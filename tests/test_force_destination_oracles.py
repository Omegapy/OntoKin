"""Independent fixture mathematics and source recording, without a store or GLB."""
from fractions import Fraction
import unittest

from ontokin.construction import compile_construction
from tools.build_force_demo import fixture_bundle, record_reference
from tools.force_oracles import (ADOPTED_CASES, CASES, FROZEN_DELIVERY_CASES, HELD_OUT_CASES,
                                 boundary_times, expected_pose, oracle_for,
                                 sample_requests, seconds)


class ForceDestinationOracleTests(unittest.TestCase):
    def test_closed_form_matches_every_frozen_delivery_pose(self):
        comparisons = 0
        for name in FROZEN_DELIVERY_CASES:
            oracle = oracle_for(name)
            for expected in CASES[name]["expected_samples"]:
                with self.subTest(fixture=name, time=expected["time"], side=expected["side"]):
                    object_ = next(o for o in oracle["shapes"] if o["path"] == expected["target"])
                    position, orientation = expected_pose(object_, seconds(expected["time"]))
                    self.assertLessEqual(max(abs(a - b) for a, b in zip(position, expected["position_m"])), 1e-9)
                    error = min(max(abs(a - sign * b) for a, b in zip(orientation, expected["orientation_wxyz"]))
                                for sign in (-1, 1))
                    self.assertLessEqual(error, 1e-9)
                    comparisons += 1
        self.assertGreater(comparisons, 200)

    def test_generated_held_out_sources_compile_and_match_independent_motion(self):
        revisions = set()
        for name in HELD_OUT_CASES:
            with self.subTest(fixture=name):
                bundle = fixture_bundle(name)
                model = compile_construction(bundle, level="constructed").model
                samples = record_reference(model, oracle_for(name))
                self.assertGreaterEqual(len(samples), 20)
                self.assertEqual({s["side"] for s in samples}, {"before", "after"})
                revisions.add(bundle.program_revision)
        self.assertEqual(len(revisions), len(HELD_OUT_CASES))

    def test_source_completion_keeps_exact_sum_and_both_sides(self):
        expected = Fraction(.1) + Fraction(.2)
        self.assertNotEqual(expected, Fraction(.1 + .2))
        actual = oracle_for("P16")["specification"]["forces"][0]["end_seconds"]
        self.assertEqual(Fraction(actual), expected)
        self.assertEqual(actual, "0.3000000000000000166533453693773481063544750213623046875")
        requests = sample_requests("P16")
        self.assertEqual({r["side"] for r in requests if r["time_seconds"] == actual}, {"before", "after"})

    def test_existing_p09_erratum_is_applied_without_rewriting_original(self):
        original = CASES["P09"]["expected_samples"][0]
        adopted = ADOPTED_CASES["P09"]["expected_samples"][0]
        self.assertEqual(original["omega_world_rad_s"], [0, 0, 2])
        self.assertEqual(adopted["omega_world_rad_s"], [0, 0, 0])
        self.assertEqual(adopted["velocity_m_s"], [0, 0, 0])
        self.assertEqual(original["position_m"], adopted["position_m"])
        model = compile_construction(fixture_bundle("P09"), level="constructed").model
        self.assertGreater(len(record_reference(model, oracle_for("P09"))), 20)

    def test_prefix_keeps_future_source_but_excludes_future_sampling(self):
        oracle = oracle_for("held-out-prefix")
        self.assertIn("1e+308[N*s]", fixture_bundle("held-out-prefix").entry.text)
        self.assertEqual(oracle["specification"]["impulses"][0]["time_seconds"], "3")
        self.assertEqual(oracle["specification"]["forces"][0]["end_seconds"], "2.125")
        self.assertEqual(boundary_times("held-out-prefix"), ["0", "0.125", "1"])
        self.assertEqual(boundary_times("P21"), ["0", "1"])
        self.assertTrue(all(Fraction(s["time_seconds"]) <= 1 for s in sample_requests("held-out-prefix")))


if __name__ == "__main__":
    unittest.main()
