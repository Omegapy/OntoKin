"""Source-built impulse physics, exact boundaries, and complete output bounds."""

from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import (MAX_OUTPUT_RECORDS, MAX_SAMPLES, _Simulator, _records_per_sample,
                               construct, evaluate, evaluate_prefix, inspect_in_frame,
                               preflight, time_text)
from ontokin.json_limits import measure_json
from ontokin.program_diagnostics import diagnostic_dict


ROOT = Path(__file__).resolve().parents[1] / "docs/language-design/impulse-v0.1"
ACCEPTANCE = json.loads((ROOT / "acceptance.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in ACCEPTANCE["source_cases"]}


def program(case_id):
    return load_file_manifest(ROOT / CASES[case_id]["file_manifest"])


def compiled(case_id):
    return compile_construction(program(case_id)).model


def changed_entry(bundle, text):
    return ProgramBundle(replace(bundle.entry, raw=text.encode("utf-8")), bundle.modules)


def coexisting_history_model():
    """Two authored target groups coexist; a later smaller group replaces one."""
    bundle = program("P08")
    first, second = [item["expected_text"] for item in CASES["P08"]["source_impulse_statements"]]
    prefix = bundle.entry.text[:bundle.entry.text.index("    at 1[s] sequence {")]
    text = (prefix + "    at 1[s] sequence {\n" + first + "\n" + first + "\n    }\n"
            + "    at 1.5[s] sequence {\n" + second + "\n    }\n"
            + "    at 2[s] sequence {\n" + first + "\n    }\n}\n")
    return compile_construction(changed_entry(bundle, text)).model


class ImpulseEvaluatorTests(unittest.TestCase):
    def assert_rotation(self, actual, expected):
        # Chord distance avoids the acos(dot) rounding floor near equal unit
        # quaternions. The two quaternion signs denote the same rotation.
        actual = [value / math.hypot(*actual) for value in actual]
        expected = [value / math.hypot(*expected) for value in expected]
        if sum(a * b for a, b in zip(actual, expected)) < 0:
            expected = [-value for value in expected]
        chord = math.hypot(*(a - b for a, b in zip(actual, expected)))
        angle = 4 * math.asin(min(1, chord / 2))
        self.assertLessEqual(angle, ACCEPTANCE["tolerance"]["orientation_geodesic_rad"])

    def assert_projection(self, actual, expected, path="", *, exact_numbers=False):
        if isinstance(expected, dict):
            for key, value in expected.items():
                if key == "sequence_indices":
                    self.assertEqual([record["sequence_index"] for record in actual["last_applications"]], value)
                else:
                    self.assertIn(key, actual, path)
                    self.assert_projection(actual[key], value, path + "." + key, exact_numbers=exact_numbers)
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected), path)
            if path.endswith("orientation_wxyz"):
                self.assert_rotation(actual, expected)
            else:
                for a, b in zip(actual, expected):
                    self.assert_projection(a, b, path, exact_numbers=exact_numbers)
        elif type(expected) in (int, float) and not exact_numbers:
            self.assertTrue(math.isfinite(actual), path)
            self.assertAlmostEqual(actual, expected, delta=1e-9, msg=path)
        else:
            self.assertEqual(actual, expected, path)

    def test_frozen_positive_state_samples(self):
        for case_id, case in CASES.items():
            if case["kind"] != "positive":
                continue
            with self.subTest(case=case_id):
                model = compiled(case_id)
                expected = case["expected"]["samples"]
                actual = evaluate(model, expected)["samples"]
                for sample, oracle in zip(actual, expected):
                    self.assert_projection(sample, oracle, exact_numbers=case_id == "P12")
                    for record in sample["objects"].values():
                        self.assertIs(type(record["impulses"]["applied_count"]), int)
                        for application in record["impulses"]["last_applications"]:
                            json.dumps(application, allow_nan=False)
                            self.assertEqual(measure_json(application)["entries"],
                                             45 + len(application["target_element_id"]))

    def test_center_momentum_and_energy(self):
        for case_id in ("P01", "P02"):
            with self.subTest(case=case_id):
                model = compiled(case_id)
                state = evaluate(model, ["1"])["samples"][0]["objects"]["ball"]
                obj = model.objects["ball"]
                energy = (obj.mass * sum(value * value for value in state["velocity_m_per_s"]) / 2
                          + obj.inertia * sum(value * value for value in state["angular_velocity_rad_per_s"]) / 2)
                self.assertAlmostEqual(energy, CASES[case_id]["expected"]["kinetic_energy_after_j"], delta=1e-12)
        record = state["impulses"]["last_applications"][0]
        self.assert_projection(record, CASES["P02"]["expected"]["first_application"])

    def test_rotated_off_center_world_momentum(self):
        model = compiled("P03")
        at_boundary, later = evaluate(model, ["1", "2"])["samples"]
        ball = at_boundary["objects"]["ball"]
        self.assert_projection(ball["impulses"]["last_applications"][0],
                               CASES["P03"]["expected"]["first_application"])
        self.assert_projection(ball["angular_velocity_rad_per_s"], [5, 0, 0])
        # Rx(5) * Ry(pi/2), independently expanded in (w,x,y,z) order.
        half = math.sqrt(0.5)
        self.assert_rotation(later["objects"]["ball"]["orientation_wxyz"],
                             [math.cos(2.5) * half, math.sin(2.5) * half,
                              math.cos(2.5) * half, math.sin(2.5) * half])

    def test_completion_release_preserves_incoming_derivatives_before_impulse(self):
        model = compiled("P04")
        before, after = evaluate(model, [{"time": "1", "side": "before"}, "1"])["samples"]
        incoming, outgoing = before["objects"]["ball"], after["objects"]["ball"]
        self.assertEqual(incoming["position_m"], outgoing["position_m"])
        self.assertEqual(incoming["orientation_wxyz"], outgoing["orientation_wxyz"])
        record = outgoing["impulses"]["last_applications"][0]
        self.assertEqual(record["sequence_index"], 1)
        self.assertEqual(record["linear_velocity_before_world_m_per_s"], incoming["velocity_m_per_s"])
        self.assertEqual(record["angular_velocity_before_world_rad_per_s"], incoming["angular_velocity_rad_per_s"])
        self.assert_projection(record["linear_velocity_after_world_m_per_s"], [1, 2, 0])
        self.assert_projection(record["angular_velocity_after_world_rad_per_s"], [0, 0, 7])
        self.assertEqual(after["objects"]["carrier"]["velocity_m_per_s"], [0, 0, 0])
        self.assertEqual(after["objects"]["carrier"]["angular_velocity_rad_per_s"], [0, 0, 0])
        self.assertEqual(outgoing["pose_authority"],
                         {"kind": "free_sphere", "since_seconds": "1", "trajectory_anchor_seconds": "1"})
        self.assertEqual(after["joints"]["hold"]["status"], "inactive")

    def test_zero_impulse_preserves_original_trajectory_exactly(self):
        bundle = program("P05")
        statement = CASES["P05"]["source_impulse_statements"][0]["expected_text"]
        control = compile_construction(changed_entry(bundle, bundle.entry.text.replace(statement, ""))).model
        model = compile_construction(bundle).model
        times = ["0", "0.9", {"time": "1", "side": "before"}, "1", "1.2345678901234567", "2"]
        actual, expected = evaluate(model, times)["samples"], evaluate(control, times)["samples"]
        for sample, reference in zip(actual, expected):
            ball, other = sample["objects"]["ball"], reference["objects"]["ball"]
            for field in ("position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s", "pose_authority"):
                self.assertEqual(ball[field], other[field], field)
        self.assertEqual(actual[-1]["objects"]["ball"]["impulses"]["applied_count"], 1)
        self.assertEqual(actual[-1]["objects"]["ball"]["pose_authority"]["trajectory_anchor_seconds"], "0")

    def test_repeated_impulses_retain_all_latest_boundary_records(self):
        model = compiled("P06")
        before, first, unrelated, before_next, next_ = evaluate(
            model, [{"time": "1", "side": "before"}, "1", "1.5", {"time": "2", "side": "before"}, "2"])["samples"]
        projection = lambda sample: sample["objects"]["ball"]["impulses"]
        self.assertEqual(projection(before)["applied_count"], 0)
        self.assertEqual(projection(first)["applied_count"], 2)
        self.assertEqual(projection(first), projection(unrelated))
        self.assertEqual(projection(first), projection(before_next))
        for record, expected in zip(projection(first)["last_applications"], CASES["P06"]["expected"]["boundary_1_records"]):
            self.assert_projection(record, expected)
        self.assertEqual(projection(next_)["applied_count"], 3)
        self.assertEqual(projection(next_)["last_application_time_seconds"], "2")
        self.assertEqual([r["sequence_index"] for r in projection(next_)["last_applications"]], [0])
        self.assertEqual(next_["objects"]["ball"]["pose_authority"],
                         {"kind": "free_sphere", "since_seconds": "0", "trajectory_anchor_seconds": "2"})

    def test_numeric_failures_are_source_local_at_actual_boundary(self):
        for case_id in ("N15", "N16", "N17", "N18"):
            with self.subTest(case=case_id):
                bundle, model = program(case_id), compiled(case_id)
                with self.assertRaises(OntoKinError) as raised:
                    evaluate(model, ["2"])
                error = raised.exception
                self.assertEqual(error.code, "OKL-E-NUMERIC")
                self.assertEqual(error.diagnostic.category, "numerical_failure")
                self.assertEqual(error.diagnostic.time, Fraction(1))
                self.assertEqual(error.diagnostic.side, "after")
                self.assertEqual(error.diagnostic.details["sequence_index"], 0)
                self.assertEqual(error.diagnostic.element_id, ["impulse-demo", "demo", "ball"])
                expected = CASES[case_id]["source_impulse_statements"][0]["source_location"]
                actual = diagnostic_dict(error.diagnostic, bundle)
                self.assertEqual({key: actual["primary"][key] for key in expected}, expected)
                self.assertIn("IMP-002", error.diagnostic.rule_ids)
                json.dumps(actual, allow_nan=False)

    def test_finite_quotient_overflow_can_cancel_before_rounding(self):
        model = compiled("P12")
        impulse = model.events[0].events[0].impulse.impulse_world_n_s[0]
        self.assertGreater(Fraction(impulse) / Fraction(model.objects["ball"].mass),
                           Fraction(sys.float_info.max))
        boundary, end = evaluate(model, ["1", "2"])["samples"]
        self.assertEqual(boundary["objects"]["ball"]["position_m"], [-1e308, 0, 0])
        self.assertEqual(boundary["objects"]["ball"]["velocity_m_per_s"], [1e308, 0, 0])
        self.assertEqual(end["objects"]["ball"]["position_m"], [0, 0, 0])

    def test_every_frozen_atomic_failure_retains_before_state(self):
        for case_id, case in CASES.items():
            if case["kind"] != "negative" or case["expected"]["phase_group"] != "event_admission":
                continue
            with self.subTest(case=case_id):
                model = compiled(case_id)
                expected = case["expected"]
                incoming = evaluate_prefix(model, expected["event_time_seconds"], side="before")
                failed = evaluate_prefix(model, model.duration)
                self.assertEqual(failed["failure"].code, expected["diagnostic_code"])
                self.assertEqual(failed["last_valid_state"], incoming["last_valid_state"])
                self.assertEqual(failed["valid_until_side"], "before")
                self.assertEqual(failed["valid_until_seconds"], expected["event_time_seconds"])
                self.assertEqual(failed["failure"].diagnostic.details["sequence_index"], expected["sequence_index"])
                if case_id == "N24":
                    state = failed["last_valid_state"]
                    self.assertEqual(state["joints"]["hold"]["status"], "active")
                    self.assertEqual(state["objects"]["ball"]["motion"], "prescribed")
                    self.assertEqual(state["objects"]["ball"]["impulses"]["applied_count"], 0)

    def test_time_zero_and_duration_keep_before_after_semantics(self):
        for case_id, boundary in (("P13", "0"), ("P14", "2")):
            with self.subTest(case=case_id):
                model = compiled(case_id)
                initial = construct(model)["initial_state"]["objects"]["ball"]
                self.assertEqual(initial["impulses"],
                                 {"applied_count": 0, "last_application_time_seconds": None, "last_applications": []})
                before, after = evaluate(model, [{"time": boundary, "side": "before"}, boundary])["samples"]
                self.assertEqual(before["objects"]["ball"]["impulses"]["applied_count"], 0)
                self.assertEqual(after["objects"]["ball"]["impulses"]["applied_count"], 1)
                self.assertEqual(after["objects"]["ball"]["impulses"]["last_application_time_seconds"], boundary)

    def test_binary64_clock_is_not_protocol_decimal(self):
        model = compiled("P15")
        boundary = CASES["P15"]["expected"]["canonical_boundary_seconds"]
        self.assertEqual(time_text(model.events[0].time), boundary)
        decimal, before, after = evaluate(model, ["0.1", {"time": boundary, "side": "before"}, boundary])["samples"]
        for sample in (decimal, before):
            self.assertEqual(sample["objects"]["ball"]["impulses"]["applied_count"], 0)
        self.assertEqual(after["objects"]["ball"]["impulses"]["applied_count"], 1)
        self.assertEqual(after["objects"]["ball"]["impulses"]["last_application_time_seconds"], boundary)

    def test_frame_inspection_preserves_explicit_record_coordinates(self):
        sample = evaluate(compiled("P03"), ["1.5"])["samples"][0]
        world = copy.deepcopy(sample["objects"]["ball"]["impulses"])
        # The inherited helper returns a kinematic patch, which inspection
        # overlays on the complete object projection.
        relative = copy.deepcopy(sample["objects"]["ball"])
        relative.update(inspect_in_frame(sample, "ball", "ball.frame"))
        self.assertEqual(relative["impulses"], world)
        self.assertEqual(sample["objects"]["ball"]["impulses"], world)
        self.assert_projection(relative["position_m"], [0, 0, 0])
        self.assert_rotation(relative["orientation_wxyz"], [1, 0, 0, 0])

    def test_history_records_do_not_alias_other_samples(self):
        model = compiled("P06")
        first, second = evaluate(model, ["1", "1.5"])["samples"]
        retained = copy.deepcopy(second["objects"]["ball"]["impulses"])
        changed = first["objects"]["ball"]["impulses"]["last_applications"][0]
        changed["impulse_world_n_s"][1] = 999
        changed["source_location"]["source_revision"] = "changed"
        self.assertEqual(second["objects"]["ball"]["impulses"], retained)
        self.assertEqual(evaluate(model, ["1.5"])["samples"][0]["objects"]["ball"]["impulses"], retained)
        self.assertEqual(model.events[0].events[0].impulse.source,
                         CASES["P06"]["source_impulse_statements"][0]["source_location"])

    def test_complete_history_weight_retains_each_objects_latest_group(self):
        model = coexisting_history_model()
        first, second = 'rack.props["first"]', 'rack.props["second"]'
        base = 2 * len(model.objects) + len(model.sites) + len(model.joints) + len(model.actions) + 1
        empty = 4 * len(model.objects)
        first_weight = 45 + len(model.objects[first].element_id)
        second_weight = 45 + len(model.objects[second].element_id)
        self.assertEqual(_records_per_sample(model, constructing=True), base + empty)
        self.assertEqual(_records_per_sample(model), base + empty + 2 * first_weight + second_weight)
        samples = evaluate(model, ["1", "1.5", "2"])["samples"]
        lengths = [[len(sample["objects"][path]["impulses"]["last_applications"])
                    for path in (first, second)] for sample in samples]
        self.assertEqual(lengths, [[2, 0], [2, 1], [1, 1]])
        for sample in samples:
            actual = sum(measure_json(obj["impulses"])["entries"] for obj in sample["objects"].values())
            self.assertLessEqual(base + actual, _records_per_sample(model))

    def test_sparse_and_dense_samples_obey_complete_history_weight(self):
        model = coexisting_history_model()
        bound = _records_per_sample(model)
        count = min(MAX_SAMPLES, MAX_OUTPUT_RECORDS // bound)
        self.assertLess(count, MAX_SAMPLES)
        dense = evaluate(model, ["1.5"] * count)["samples"]
        self.assertEqual(len(dense), count)
        self.assertEqual(len(dense[-1]["objects"]['rack.props["first"]']["impulses"]["last_applications"]), 2)
        self.assertEqual(len(evaluate(model, ["1", "1.5", "2"])["samples"]), 3)
        with patch("ontokin.evaluator._Simulator", side_effect=AssertionError("allocated before budget admission")):
            with self.assertRaises(OntoKinError) as raised:
                evaluate(model, ["1.5"] * (count + 1))
        self.assertEqual(raised.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(raised.exception.diagnostic.details["records_per_sample"], bound)

    def test_one_sample_overflow_fails_before_history_allocation(self):
        model = coexisting_history_model()
        bound = _records_per_sample(model)
        with patch("ontokin.evaluator.MAX_OUTPUT_RECORDS", bound):
            self.assertEqual(len(evaluate(model, ["1.5"])["samples"]), 1)
        with patch("ontokin.evaluator.MAX_OUTPUT_RECORDS", bound - 1):
            # The constructed before-t0 state exposes only empty projections.
            initial = construct(model)["initial_state"]
            self.assertTrue(all(not obj["impulses"]["last_applications"] for obj in initial["objects"].values()))
            with patch("ontokin.evaluator._Simulator", side_effect=AssertionError("allocated before budget admission")):
                for call in (lambda: evaluate(model, ["1.5"]), lambda: evaluate(model, []),
                             lambda: preflight(model), lambda: evaluate_prefix(model, "1.5")):
                    with self.assertRaises(OntoKinError) as raised:
                        call()
                    self.assertEqual(raised.exception.code, "OKL-E-RESOURCE")
                    self.assertEqual(raised.exception.diagnostic.rule_ids, ["IMP-004"])

    def test_cancellation_during_complete_history_bound(self):
        model = coexisting_history_model()
        entered = False
        cancellation = RuntimeError("cancel inside authored event history")

        class ObservedEvents(list):
            def __iter__(self):
                nonlocal entered
                entered = True
                return super().__iter__()

        model.events[0].events = ObservedEvents(model.events[0].events)

        def check():
            if entered:
                raise cancellation

        with patch("ontokin.evaluator._Simulator", side_effect=AssertionError("allocated despite cancelled bound")):
            with self.assertRaises(RuntimeError) as raised:
                preflight(model, check=check)
        self.assertIs(raised.exception, cancellation)
        self.assertGreater(_records_per_sample(model), _records_per_sample(model, constructing=True))

    def test_cancellation_during_staged_impulse_does_not_commit(self):
        model = compiled("P02")
        simulator = _Simulator(model)
        before = simulator.advance(Fraction(1), "before")
        entered = False
        cancellation = OntoKinError("OKL-E-RESOURCE", "caller cancelled staged impulse", details={"caller": True})
        original = _Simulator._dynamic_kinematics

        def dynamic(sim, path, time, state):
            nonlocal entered
            result = original(sim, path, time, state)
            if state is not sim.state:
                entered = True
            return result

        def check():
            if entered:
                raise cancellation

        simulator.check = check
        with patch.object(_Simulator, "_dynamic_kinematics", dynamic):
            with self.assertRaises(OntoKinError) as raised:
                simulator.advance(Fraction(1))
        self.assertIs(raised.exception, cancellation)
        simulator.check = None
        self.assertEqual(simulator.snapshot(Fraction(1), "before"), before)
        after = simulator.advance(Fraction(1))
        self.assert_projection(after, CASES["P02"]["expected"]["samples"][1])
        self.assertEqual(cancellation.diagnostic.details, {"caller": True})

    def test_cancellation_during_history_projection_keeps_complete_state(self):
        model = compiled("P06")
        simulator = _Simulator(model)
        expected = simulator.advance(Fraction(1))
        entered = False
        cancellation = RuntimeError("cancel during complete record projection")

        class ObservedRecords(list):
            def __iter__(self):
                nonlocal entered
                entered = True
                return super().__iter__()

        history = simulator.state.impulses["ball"]
        history.last_applications = ObservedRecords(history.last_applications)

        def check():
            if entered:
                raise cancellation

        simulator.check = check
        with self.assertRaises(RuntimeError) as raised:
            simulator.snapshot(Fraction(1), "after")
        self.assertIs(raised.exception, cancellation)
        simulator.check = None
        self.assertEqual(simulator.snapshot(Fraction(1), "after"), expected)
        self.assertEqual(history.applied_count, 2)
        self.assertEqual(len(history.last_applications), 2)

    def test_old_profiles_keep_snapshot_and_assumption_shapes(self):
        old_root = ROOT.parent / "surface-v0.1"
        model = compile_construction(load_file_manifest(old_root / "program.files.json")).model
        result = evaluate(model, ["0"])
        self.assertEqual(result["physical_assumptions"]["external_torque"], "absent")
        self.assertNotIn("impulses", result["physical_assumptions"])
        for obj in result["samples"][0]["objects"].values():
            self.assertNotIn("impulses", obj)
            self.assertNotIn("trajectory_anchor_seconds", obj["pose_authority"])
        self.assertEqual(_records_per_sample(model), 2 * len(model.objects) + len(model.sites)
                         + len(model.joints) + len(model.actions) + 1)

    def test_new_profile_discloses_instantaneous_physical_influences(self):
        assumptions = evaluate(compiled("P02"), ["1"])["physical_assumptions"]
        self.assertEqual(assumptions["external_torque"], "authored_instantaneous_angular_impulses_only")
        self.assertEqual(assumptions["continuous_external_forces"], "uniform_gravity_only")
        self.assertEqual(assumptions["continuous_external_torque"], "absent")
        self.assertEqual(assumptions["contact_response"], "unavailable")


if __name__ == "__main__":
    unittest.main()
