"""Independent reference checks; actual execution requires the shared window."""
from __future__ import annotations

import copy
from fractions import Fraction as F
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.bundle import load_bundle
from ontokin.construction import compile_construction
from ontokin.reach_reference import (
    Interval, ReferenceError, _Arithmetic, _canonical_targets, build_reference,
)
from reach_agent_support import CASES, source_case


class Counter:
    def __init__(self):
        self.operations = 0

    def tick(self):
        self.operations += 1
        if self.operations > 100000:
            raise RuntimeError("Shared reference work exhausted")


def compile_case(name):
    return compile_construction(source_case(name))


class ReachReferenceTests(unittest.TestCase):
    def assert_encloses(self, interval, value, allowance=F(1, 10**12)):
        self.assertIsInstance(interval, Interval)
        self.assertLessEqual(interval.lo - allowance, F(value))
        self.assertGreaterEqual(interval.hi + allowance, F(value))

    def assert_record(self, expected, actual, trail=""):
        if isinstance(actual, Interval):
            self.assertIsInstance(expected, (int, float), trail)
            self.assert_encloses(actual, expected)
        elif isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected), trail)
            for key in expected:
                self.assert_record(expected[key], actual[key], trail + "." + key)
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected), trail)
            for index, value in enumerate(expected):
                self.assert_record(value, actual[index], trail + f"[{index}]")
        else:
            self.assertEqual(actual, expected, trail)

    def test_independent_exact_signed_quadrants_and_canonical_half_turns(self):
        work = Counter()
        ar = _Arithmetic(work=work)
        cases = (((1, 1, 0), "elbow_positive", (0.0, math.pi / 2)),
                 ((1, 1, 0), "elbow_negative", (math.pi / 2, -math.pi / 2)),
                 ((-1, 1, 0), "elbow_positive", (math.pi / 2, math.pi / 2)),
                 ((-1, 1, 0), "elbow_negative", (-math.pi, -math.pi / 2)),
                 ((-1, -1, 0), "elbow_positive", (-math.pi, math.pi / 2)),
                 ((1, -1, 0), "elbow_negative", (0.0, -math.pi / 2)),
                 ((-2, 0, 0), "elbow_positive", (-math.pi, 0.0)))
        for target, branch, expected in cases:
            with self.subTest(target=target, branch=branch):
                payload = SimpleNamespace(lengths_m=(1.0, 1.0), target_m=target,
                    branch=branch, limits_rad=((-math.pi, math.pi), (-math.pi, math.pi)))
                self.assertEqual(_canonical_targets(payload, ar), expected)
        self.assertGreater(work.operations, 0)
        self.assertLessEqual(work.operations, 100000)

    def test_shared_work_is_required_and_cancellation_identity_survives(self):
        with self.assertRaises(ValueError):
            _Arithmetic()
        interruption = RuntimeError("cancel at actual independent arithmetic")
        count = 0
        def check():
            nonlocal count
            count += 1
            if count == 20:
                raise interruption
        with self.assertRaises(RuntimeError) as caught:
            _Arithmetic(check=check).pi()
        self.assertIs(caught.exception, interruption)
        self.assertEqual(count, 20)

    def test_source_reference_uses_no_production_solver_or_simulator(self):
        compiler = compile_case("P01")
        before = compiler.reach_work.operations
        failure = AssertionError("Production expectation generator was called")
        with patch("ontokin.reach_runtime.ReachSimulator", side_effect=failure), \
             patch("ontokin.reach_kinematics.admit_planar", side_effect=failure), \
             patch("ontokin.reach_pose.ReachPoseOps", side_effect=failure):
            reference = build_reference(compiler.model, end=3, work=compiler.reach_work)
            sample = reference.sample(F(3, 2))
        self.assertEqual(reference.boundaries, (F(0), F(2), F(3)))
        current = sample["reaches"]["reach"]["current"]["value"]
        self.assertEqual(current["resolved_joint_targets_rad"], [0.0, math.pi / 2])
        self.assertEqual(current["joint_coordinates_rad"], [0.0, float(F(math.pi / 2) * F(3, 4))])
        self.assertEqual(current["action_joint_rates_rad_per_s"], [0.0, math.pi / 4])
        self.assertGreater(compiler.reach_work.operations, before)
        model_action = compiler.model.actions["reach"]
        compiler.model.actions.clear()
        self.assertEqual(reference.sample(F(3, 2))["reaches"]["reach"]["element_id"], list(model_action.element_id))
        geometry = reference.geometry_expectations
        geometry[0]["geometry"].clear()
        self.assertTrue(reference.geometry_expectations[0]["geometry"])

    def test_complete_independent_stopped_history_and_new_physical_owner(self):
        compiler = compile_case("L02")
        reference = build_reference(compiler.model, end=2, work=compiler.reach_work)
        wanted = CASES["L02"][1]["samples"]
        for row in wanted:
            if F(row["time_seconds"]) not in {F(1, 2), F(1), F(3, 2)}:
                continue
            sample = reference.sample(F(row["time_seconds"]), row["side"])
            self.assert_record(row["reaches"], sample["reaches"])
        current = reference.sample(1)["reaches"]["reach_a"]["current"]["value"]
        self.assertEqual(current["goal_outcome"], "interrupted")
        self.assertEqual(current["action_joint_rates_rad_per_s"], [0.0, 0.0])
        self.assertNotEqual(current["joint_rates_rad_per_s"], [0.0, 0.0])
        self.assertEqual(current["terminal_result"]["time_seconds"], "0.5")

    def test_short_prefix_never_admits_the_future_failed_handoff(self):
        compiler = compile_case("L04")
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        self.assertEqual(reference.boundaries, (F(0), F(1, 4)))
        self.assertEqual(reference.sample(F(1, 4))["reaches"]["reach_b"]["current"]["value"]["lifecycle"], "pending")
        other = compile_case("L04")
        with self.assertRaises(ReferenceError) as caught:
            build_reference(other.model, end=F(1, 2), work=other.reach_work)
        self.assertEqual(caught.exception.code, "source_admission")

    def test_saved_incoming_release_and_force_history_match_frozen_source(self):
        compiler = compile_case("P16")
        reference = build_reference(compiler.model, end=4, work=compiler.reach_work)
        expected = CASES["P16"][1]["expected"]["release"]
        boundaries = reference.boundary_states()
        release = next(row for row in boundaries if row["source_seconds"] == "2")
        self.assertEqual(len(release["incoming_releases"]), 1)
        incoming = release["incoming_releases"][0]
        contributor = incoming["reach_contributors"][0]
        self.assertTrue(all(contributor["joint_rates_rad_per_s"]))
        self.assertEqual(contributor["joint_rates_rad_per_s"], expected["incoming_state"]["joint_rates_rad_per_s"])
        self.assertEqual(release["reach_states_before"]["reach"]["current"]["value"]["lifecycle"], "running")
        self.assertEqual(release["reach_states_after"]["reach"]["current"]["value"]["lifecycle"], "completed")
        for time in (3, 4):
            payload = reference.sample(time)["objects"]["payload"]
            for interval, value in zip(payload["position_m"], expected[f"position_at_{time}_seconds_m"]):
                self.assert_encloses(interval, value)
            for interval, value in zip(payload["velocity_m_per_s"], expected[f"velocity_at_{time}_seconds_m_per_s"]):
                self.assert_encloses(interval, value)
            self.assertEqual(payload["forces"]["started_count"], 1)
            self.assertEqual(payload["forces"]["completed_count"], 1)
        self.assertLessEqual(reference._history_weight, 100000)
        self.assertEqual(set(release), {"source_seconds", "incoming_releases", *(
            name + "_" + side for name in ("joint_states", "action_states", "pose_authorities", "impulse_states", "force_states", "reach_states")
            for side in ("before", "after"))})

    def test_continuous_ideal_start_survives_stop_and_replacement(self):
        # At t=0.5, duration 3 divides these targets by 6 exactly in binary64.
        # Duration 5 instead gives a genuine /10 rounding discrepancy on both
        # coordinates. Only this derived variant changes, not frozen L02.
        payload = source_case("L02").to_payload()
        old = "point(rig.arm.reach_frame, 0[m], 1[m], 0[m]), 2[s], elbow_positive)"
        new = "point(rig.arm.reach_frame, 0[m], 1[m], 0[m]), 5[s], elbow_positive)"
        self.assertEqual(payload["entry"]["source"].count(old), 1)
        payload["entry"]["source"] = payload["entry"]["source"].replace(old, new)
        compiler = compile_construction(load_bundle(payload))
        reference = build_reference(compiler.model, end=2, work=compiler.reach_work)
        started = reference.sample(0)["reaches"]["reach_a"]["current"]["value"]
        ideal_stops = [F(target) / 10 for target in started["resolved_joint_targets_rad"]]
        self.assertEqual(len(ideal_stops), 2)
        self.assertTrue(all(F(float(value)) != value for value in ideal_stops))
        action = compiler.model.actions["reach_b"]
        phases = reference.phases(action.reach.tip + ".frame", F(1, 2), F(3, 2))
        self.assertEqual(len(phases), 1)
        self.assertTrue(any(coordinate.initial != coordinate.ideal_initial for coordinate in phases[0].coordinates))
        for coordinate in phases[0].coordinates:
            self.assertEqual(coordinate.slope, (coordinate.target - coordinate.ideal_initial) / coordinate.duration)
            self.assertEqual(coordinate.actual_slope, (coordinate.target - coordinate.initial) / coordinate.duration)
        self.assertGreater(phases[0].coordinate_angle_error, 0)
        self.assertGreater(phases[0].source_numeric_position_error, 0)

    def test_nonbinary_completion_and_phase_overlap_keep_exact_clocks(self):
        from ontokin.bundle import load_file_manifest
        from reach_agent_support import SUPPLEMENT
        compiler = compile_construction(load_file_manifest(SUPPLEMENT / "q16.files.json"))
        reference = build_reference(compiler.model, end=compiler.model.duration, work=compiler.reach_work)
        completion = F(3) + F(1, 1 << 53)
        self.assertIn(completion, reference.boundaries)
        action = next(action for action in compiler.model.actions.values() if action.kind == "reach_planar")
        frames = reference.phases(action.reach.tip + ".frame", 3, completion)
        self.assertTrue(frames)
        self.assertTrue(all(frame.start < frame.end <= completion for frame in frames))
        self.assertGreater(max(frame.angular_speed for frame in frames), 0)
        self.assertEqual(reference.sample(completion, "before")["reaches"][action.path]["current"]["value"]["lifecycle"], "running")
        self.assertEqual(reference.sample(completion, "after")["reaches"][action.path]["current"]["value"]["lifecycle"], "completed")
        before = reference.point_phase(action.reach.tip, completion, "before")
        after = reference.point_phase(action.reach.tip, completion, "after")
        self.assertEqual((before.start, before.end, after.start, after.end), (completion,) * 4)
        self.assertTrue(any(coordinate.slope for coordinate in before.coordinates))
        self.assertTrue(all(coordinate.slope == 0 for coordinate in after.coordinates))
        self.assertIs(reference.point_phase(action.reach.tip, completion), after)
        self.assertEqual(reference.phases(action.reach.tip, completion, completion), ())


if __name__ == "__main__":
    unittest.main()
