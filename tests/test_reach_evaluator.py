"""Actual adopted source lifecycle, observations and atomic failure semantics."""
from __future__ import annotations

import copy
from fractions import Fraction as Q
import json
from pathlib import Path
import unittest

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import construct, evaluate_prefix
from ontokin.json_limits import measure_json
from ontokin.reach_projection import reach_projection, reach_record_bound
from ontokin.reach_runtime import ReachSimulator, boundary_history_bound


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"
SUPPLEMENT = DATA / "draft2-supplements"


def compiler(case):
    root = SUPPLEMENT if case.startswith("L") or case == "Q16" else DATA
    return compile_construction(load_file_manifest(root / (case.lower() + ".files.json")))


class ReachEvaluatorTests(unittest.TestCase):
    def assert_projection(self, actual, expected, trail=""):
        if isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected), trail)
            for key, value in expected.items():
                self.assert_projection(actual[key], value, trail + "." + key)
        elif isinstance(expected, list):
            self.assertEqual(len(actual), len(expected), trail)
            for index, value in enumerate(expected):
                self.assert_projection(actual[index], value, trail + f"[{index}]")
        elif isinstance(expected, float):
            self.assertAlmostEqual(actual, expected, delta=2e-12, msg=trail)
        else:
            self.assertEqual(actual, expected, trail)

    def test_frozen_lifecycle_51_sides_and_86_complete_action_states(self):
        accepted = json.loads((SUPPLEMENT / "acceptance.json").read_text())
        sides = states = 0
        for case in accepted["source_cases"]:
            with self.subTest(case=case["id"]):
                built = compiler(case["id"])
                sim = ReachSimulator(built.model, work=built.reach_work)
                for expected in case["samples"]:
                    actual = sim.advance(Q(expected["time_seconds"]), expected["side"])
                    self.assert_projection(actual["reaches"], expected["reaches"])
                    for path, target in expected["reaches"].items():
                        current = actual["reaches"][path]["current"]["value"]
                        wanted = target["current"]["value"]
                        for key in ("joint_coordinates_rad", "joint_rates_rad_per_s",
                                    "action_joint_rates_rad_per_s", "resolved_joint_targets_rad"):
                            self.assertEqual(current[key], wanted[key], f"{case['id']} {path} {key}")
                        states += 1
                    sides += 1
        self.assertEqual((sides, states), (51, 86))

    def test_failed_boundary_retains_incoming_running_owner_and_no_after(self):
        built = compiler("L04")
        sim = ReachSimulator(built.model, work=built.reach_work)
        before = sim.advance(Q(1, 2), "before")
        retained, index = copy.deepcopy(sim.state), sim.event_index
        with self.assertRaises(OntoKinError) as caught:
            sim.advance(Q(1, 2), "after")
        self.assertEqual(caught.exception.diagnostic.details["reach_code"], "reach_unreachable")
        self.assertEqual(sim.state, retained)
        self.assertEqual(sim.event_index, index)
        self.assertEqual(sim.snapshot(Q(1, 2), "before"), before)
        self.assertEqual(sim.incoming_releases_at(Q(1, 2)), [])
        self.assertEqual(set(sim.state.claims.values()), {"reach_a"})
        self.assertEqual(sim.state.actions["reach_b"].status, "pending")

    def test_short_failed_source_prefix_does_not_admit_future_boundary(self):
        built = compiler("L04")
        early = evaluate_prefix(built.model, "0.25", work=built.reach_work)
        self.assertIsNone(early["failure"])
        self.assertEqual(early["valid_until_seconds"], "0.25")
        failed = evaluate_prefix(built.model, "1", work=None)
        self.assertEqual(failed["valid_until_seconds"], "0.5")
        self.assertEqual(failed["valid_until_side"], "before")
        self.assertEqual(failed["failure"].diagnostic.details["reach_code"], "reach_unreachable")

    def test_unrun_source_and_constructed_initial_are_distinct(self):
        built = compiler("L01")
        raw = reach_projection(built.model, "reach_a")
        self.assertEqual(raw["current"], {"available": False, "reason": "run_required", "value": None})
        result = construct(built.model, work=built.reach_work)
        # The constructed projection is a real zero-before observation.
        value = result["initial_state"]["reaches"]["reach_a"]["current"]["value"]
        self.assertEqual(value["observation"], {"time_seconds": "0", "side": "before",
                                              "run_id": None, "context_kind": "constructed_initial"})
        self.assertEqual(value["goal_outcome"], "pending")
        self.assertGreater(measure_json(result["initial_state"])["entries"], 0)

    def test_q16_uses_actual_nonbinary_events_and_exact_completion(self):
        built = compiler("Q16")
        sim = ReachSimulator(built.model, work=built.reach_work)
        pause = Q(4503599807514481, 9007199254740992)
        resume = Q(6755399531127737, 4503599627370496)
        completion = Q(3) + Q(1, 2**53)
        sim.advance(pause, "after")
        after = sim.advance(resume, "after")["reaches"]["reach_a"]["current"]["value"]
        self.assertEqual(Q(after["completion_time_seconds"]), completion)
        self.assertGreater(completion, Q(3))
        self.assertEqual(sim.advance(Q(3), "after")["reaches"]["reach_a"]["current"]["value"]["lifecycle"], "running")
        self.assertEqual(sim.advance(completion, "after")["reaches"]["reach_a"]["current"]["value"]["lifecycle"], "completed")

    def test_release_uses_incoming_rates_at_natural_completion(self):
        built = compiler("P16")
        sim = ReachSimulator(built.model, work=built.reach_work)
        before = sim.advance(Q(2), "before")
        sim.advance(Q(2), "after")
        records = sim.incoming_releases_at(Q(2))
        self.assertEqual(len(records), 1)
        release = records[0]
        child = release["target"]["path"]
        self.assertEqual(release["incoming_linear_velocity_world_m_per_s"],
                         before["objects"][child]["velocity_m_per_s"])
        self.assertEqual(release["incoming_angular_velocity_world_rad_per_s"],
                         before["objects"][child]["angular_velocity_rad_per_s"])
        self.assertEqual(len(release["reach_contributors"]), 1)
        self.assertTrue(any(release["reach_contributors"][0]["joint_rates_rad_per_s"]))
        self.assertEqual(sim.state.actions["reach"].status, "completed")
        self.assertLessEqual(measure_json(before["reaches"])["entries"], reach_record_bound(built.model))
        self.assertGreater(boundary_history_bound(built.model, [Q(0), Q(2)], horizon=Q(2)), 0)

    def test_frozen_admission_failures_have_strict_reach_subcodes(self):
        for case, code in {"N01": "reach_unreachable", "N02": "reach_unreachable",
                           "N03": "reach_singular", "N06": "reach_limit",
                           "N09": "reach_claim_conflict"}.items():
            with self.subTest(case=case):
                built = compiler(case)
                prefix = evaluate_prefix(built.model, built.model.duration, work=built.reach_work)
                self.assertIsNotNone(prefix["failure"])
                self.assertEqual(prefix["failure"].diagnostic.details["reach_code"], code)


if __name__ == "__main__":
    unittest.main()
