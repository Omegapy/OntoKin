"""Continuous source proof inputs, including rounded event-anchor transfer."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as Q
from pathlib import Path
import unittest

from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_runtime import ReachSimulator


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"
SUPPLEMENT = DATA / "draft2-supplements"


def source(case):
    root = SUPPLEMENT if case.startswith("L") else DATA
    return load_file_manifest(root / (case.lower() + ".files.json"))


def changed(bundle, old, new):
    if bundle.entry.text.count(old) != 1:
        raise AssertionError("A test-only edit must replace one exact source occurrence.")
    return ProgramBundle(replace(bundle.entry, raw=bundle.entry.text.replace(old, new).encode()), bundle.modules)


def simulator(bundle):
    built = compile_construction(bundle)
    return ReachSimulator(built.model, work=built.reach_work)


class ReachPhaseTests(unittest.TestCase):
    def test_moving_phase_has_exact_slopes_and_nonzero_derivative_bounds(self):
        sim = simulator(source("L01"))
        sim.advance(Q(0), "after")
        phase = sim.phase_bounds(Q(0), Q(1, 2))
        payload = sim.model.actions["reach_a"].reach
        target = sim.state.actions["reach_a"].solution.target_rad
        for path, goal in zip((payload.shoulder, payload.elbow), target):
            joint = phase["joints"][path]
            self.assertEqual(joint.actual_slope, Q(goal) / 2)
            self.assertEqual(joint.ideal_slope, Q(goal) / 2)
            self.assertEqual(joint.actual_start, joint.ideal_start)
            self.assertEqual(joint.actual_end, joint.ideal_end)
            self.assertGreater(joint.coordinate_error, 0)
        tip = phase["frames"][payload.tip + ".frame"]
        self.assertGreater(tip.carrier_speed_upper_m_per_s, 0)
        self.assertGreater(tip.carrier_acceleration_upper_m_per_s2, 0)
        self.assertGreaterEqual(tip.angular_speed_upper_rad_per_s, sum(abs(Q(x) / 2) for x in target))
        self.assertGreater(tip.position_error_m, 0)
        self.assertGreater(tip.rotation_error_rad, tip.coordinate_angle_error_rad)
        self.assertGreaterEqual(tip.trig_count, 2)
        with self.assertRaisesRegex(ValueError, "authored boundary"):
            sim.phase_bounds(Q(0), Q(1))

    def test_nonbinary_handoff_retains_continuous_ideal_start_and_corrects_slope(self):
        bundle = changed(source("L02"), "at 0.5[s] sequence", "at 0.3[s] sequence")
        sim = simulator(bundle)
        handoff = Q(0.3)
        sim.advance(handoff, "after")
        old = sim.state.actions["reach_a"]
        new = sim.state.actions["reach_b"]
        payload = sim.model.actions["reach_b"].reach
        ideal_initial = tuple(Q(goal) * handoff / 2 for goal in old.solution.target_rad)
        self.assertEqual(new.ideal_initial, ideal_initial)
        self.assertEqual(new.initial, tuple(float(value) for value in ideal_initial))
        self.assertTrue(any(Q(actual) != ideal for actual, ideal in zip(new.initial, ideal_initial)))
        phase = sim.phase_bounds(handoff, handoff + 1)
        for index, path in enumerate((payload.shoulder, payload.elbow)):
            joint = phase["joints"][path]
            target = Q(new.solution.target_rad[index])
            self.assertEqual(joint.actual_start, Q(new.initial[index]))
            self.assertEqual(joint.ideal_start, ideal_initial[index])
            self.assertEqual(joint.actual_end, target)
            self.assertEqual(joint.ideal_end, target)
            self.assertEqual(joint.actual_slope - joint.ideal_slope,
                             ideal_initial[index] - Q(new.initial[index]))
            self.assertGreaterEqual(joint.coordinate_error,
                                    abs(Q(new.initial[index]) - ideal_initial[index]))

    def test_release_keeps_incoming_state_and_propagates_nonzero_anchor_error(self):
        sim = simulator(source("P16"))
        before = sim.advance(Q(2), "before")
        sim.advance(Q(2), "after")
        anchor = sim.state.dynamic["payload"]
        error = sim.state.dynamic_errors["payload"]
        self.assertEqual(anchor.state.velocity, tuple(before["objects"]["payload"]["velocity_m_per_s"]))
        self.assertEqual(anchor.state.omega, tuple(before["objects"]["payload"]["angular_velocity_rad_per_s"]))
        self.assertGreater(error.position_m, 0)
        self.assertGreater(error.rotation_rad, 0)
        self.assertGreater(error.velocity_m_per_s, 0)
        self.assertGreater(error.angular_velocity_rad_per_s, 0)
        self.assertEqual(sim.state.dynamic_error_times["payload"], Q(2))
        phase = sim.phase_bounds(Q(2), Q(3))["objects"]["payload"]
        self.assertGreaterEqual(phase.anchor_position_error_m,
                                error.position_m + error.velocity_m_per_s)
        self.assertGreaterEqual(phase.anchor_rotation_error_rad,
                                error.rotation_rad + error.angular_velocity_rad_per_s)
        self.assertGreater(phase.carrier_acceleration_upper_m_per_s2, 0)
        self.assertGreaterEqual(phase.velocity_error_m_per_s, error.velocity_m_per_s)

    def test_equal_force_replacement_keeps_actual_anchor_and_updates_proof_clock(self):
        bundle = changed(source("P16"),
            'force payload @ "released-push" using vector(world, 1[N], 0[N], 0[N]) for 1[s]; }',
            'force payload @ "released-push" using vector(world, 1[N], 0[N], 0[N]) for 0.5[s]; }\n'
            '    at 2.5[s] sequence { force payload @ "replacement-push" '
            'using vector(world, 1[N], 0[N], 0[N]) for 0.5[s]; }')
        sim = simulator(bundle)
        sim.advance(Q(2), "after")
        anchor_time = sim.state.dynamic["payload"].time
        incoming_error = sim.state.dynamic_errors["payload"]
        before = sim.advance(Q(5, 2), "before")["objects"]["payload"]
        after = sim.advance(Q(5, 2), "after")["objects"]["payload"]
        self.assertEqual(sim.state.dynamic["payload"].time, anchor_time)
        self.assertEqual(sim.state.dynamic_error_times["payload"], Q(5, 2))
        for field in ("position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s"):
            self.assertEqual(before[field], after[field])
        self.assertGreaterEqual(sim.state.dynamic_errors["payload"].position_m,
                                incoming_error.position_m)
        phase = sim.phase_bounds(Q(5, 2), Q(3))["objects"]["payload"]
        self.assertGreaterEqual(phase.position_error_m, sim.state.dynamic_errors["payload"].position_m)


if __name__ == "__main__":
    unittest.main()
