"""Landmark metrology regressions. None of the fixtures establishes real-site accuracy."""
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from ontokin.composite_manifest import check_registration
from ontokin.landmark_registration import register


FIXTURES = Path(__file__).resolve().parents[1] / "examples/splat-composite/fixtures"
ENV = FIXTURES / "registration-screen.glb"
PLAN = FIXTURES / "landmarks/synthetic-plan.json"
PICKS = FIXTURES / "landmarks/synthetic-picks.json"


class LandmarkRegistrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.plan_path = Path(temporary.name, "plan.json")
        self.picks_path = Path(temporary.name, "picks.json")
        self.plan = json.loads(PLAN.read_bytes())
        self.picks = json.loads(PICKS.read_bytes())

    def run_case(self):
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        self.picks["planSha256"] = hashlib.sha256(self.plan_path.read_bytes()).hexdigest()
        self.picks_path.write_text(json.dumps(self.picks), encoding="utf-8")
        return register(self.plan_path, self.picks_path, ENV)

    def test_control_recovers_rotation_translation_and_scale_and_checks_fourth_point(self):
        result = register(PLAN, PICKS, ENV)
        self.assertTrue(result["passesTolerance"])
        self.assertAlmostEqual(result["scale"], 2.0, places=7)
        oracle = [0, 0, -2, 0, 0, 2, 0, 0, 2, 0, 0, 0, 1, 0.5, 3, 1]
        for actual, expected in zip(result["matrixColumnMajor"], oracle):
            self.assertAlmostEqual(actual, expected, places=7)
        self.assertEqual((result["fit"]["count"], result["holdout"]["count"]), (3, 1))
        combined = check_registration(result["registration"])
        self.assertEqual(combined["maxResidualM"], result["holdout"]["maxResidualM"])

    def test_heldout_error_is_reported_but_cannot_move_fit(self):
        reference = self.run_case()
        self.picks["environment"]["floor-far-right"][1] += 0.1
        bad = self.run_case()
        self.assertEqual(reference["matrixColumnMajor"], bad["matrixColumnMajor"])
        self.assertEqual(reference["fit"], bad["fit"])
        self.assertFalse(bad["passesTolerance"])
        self.assertAlmostEqual(bad["holdout"]["maxResidualM"], 0.2, places=5)
        self.assertIsNone(bad["registration"])

    def test_rigid_keeps_unit_scale_on_mismatched_units(self):
        self.plan["kind"] = "rigid"
        self.plan["minimumAltitudeM"] = 0.1
        bad = self.run_case()
        self.assertEqual(bad["scale"], 1.0)
        self.assertFalse(bad["fit"]["passesTolerance"])
        self.assertGreater(bad["fit"]["maxResidualM"], 1.0)
        self.assertIsNone(bad["registration"])

    def test_noisy_rigid_fit_with_known_least_squares_residual(self):
        # Symmetric opposite points cancel translation error and yield a diagonal covariance.
        self.plan.update(kind="rigid", toleranceM=0.05, minimumAltitudeM=0.5)
        source = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
        self.picks["environment"] = {str(i): v for i, v in enumerate(source)}
        self.plan["landmarks"] = []
        for i, (x, y, z) in enumerate(source):
            world = [2 - y, 4 + 1.03*x, 6 + z]
            self.plan["landmarks"].append({"name": str(i), "world": world, "role": "fit"})
        report = self.run_case()
        self.assertTrue(report["passesTolerance"])
        self.assertAlmostEqual(report["fit"]["maxResidualM"], 0.03)
        self.assertAlmostEqual(report["fit"]["rmsResidualM"], 0.03 / math.sqrt(3))
        self.assertIsNone(report["holdout"]["passesTolerance"])
        self.assertIsNone(report["holdout"]["maxResidualM"])

    def test_mirror_cannot_pass_as_a_proper_rotation(self):
        for point in self.plan["landmarks"]:
            point["role"] = "fit"
            point["world"][0] *= -1
        report = self.run_case()
        self.assertFalse(report["passesTolerance"])
        self.assertIsNone(report["registration"])

    def test_rejects_stale_plan_and_wrong_asset(self):
        self.run_case()
        self.plan["toleranceM"] *= 2
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "plan SHA-256"):
            register(self.plan_path, self.picks_path, ENV)
        self.plan["environmentSha256"] = "1" * 64
        with self.assertRaisesRegex(ValueError, "GLB SHA-256"):
            self.run_case()

    def test_rejects_near_collinear_and_poorly_spaced_fit_anchors(self):
        self.plan["minimumAltitudeM"] = 1.0
        with self.assertRaisesRegex(ValueError, "minimum altitude"):
            self.run_case()
        self.picks["environment"]["screen-lower-left"] = [0, 0, 0]
        self.picks["environment"]["screen-lower-right"] = [1, 0, 0]
        self.picks["environment"]["wall-upper-right"] = [2, 1e-11, 0]
        with self.assertRaisesRegex(ValueError, "span a plane"):
            self.run_case()

    def test_cannot_validate_on_a_copy_of_a_fit_point(self):
        self.picks["environment"]["floor-far-right"] = self.picks["environment"]["screen-lower-left"]
        with self.assertRaisesRegex(ValueError, "Duplicated physical point"):
            self.run_case()

    def test_rejects_extra_unplanned_picks(self):
        self.picks["environment"]["extra"] = [0, 0, 0]
        with self.assertRaisesRegex(ValueError, "Unexpected environment picks"):
            self.run_case()

    def test_rejects_unreasonable_tolerance_or_invalid_coordinate(self):
        for tolerance in [True, 1.5, float("nan")]:
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                self.plan["toleranceM"] = tolerance
                self.run_case()
        self.plan["toleranceM"] = 0.01
        self.plan["landmarks"][0]["world"][2] = True
        with self.assertRaisesRegex(ValueError, "finite values"):
            self.run_case()
