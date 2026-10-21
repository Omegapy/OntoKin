"""Dimensioned independent checks for real reach/release/impulse histories."""
import copy
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.bundle import load_bundle
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import _Bounds, _assert_projection
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_reference import Interval, build_reference
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


FIELDS = (
    "lever_arm_world_m", "application_point_world_m", "angular_impulse_world_n_m_s",
    "linear_velocity_before_world_m_per_s", "linear_velocity_after_world_m_per_s",
    "angular_velocity_before_world_rad_per_s", "angular_velocity_after_world_rad_per_s",
)


def impulse_variant():
    payload = source_case("P16").to_payload()
    release = "release grip using incoming;"
    impulses = (
        " impulse payload using vector(world, 0[N*s], 0.2[N*s], 0[N*s]) "
        "at point(payload.frame, 0.07[m], 0.02[m], 0[m]);"
        " impulse payload using vector(world, -0.1[N*s], 0[N*s], 0[N*s]) "
        "at point(payload.frame, 0.03[m], 0[m], 0[m]);"
        " impulse payload using vector(world, 0[N*s], 0[N*s], 0[N*s]) "
        "at point(payload.frame, 0.07[m], 0.02[m], 0[m]);"
    )
    assert payload["entry"]["source"].count(release) == 1
    payload["entry"]["source"] = payload["entry"]["source"].replace(release, release + impulses)
    return load_bundle(payload)


class ReachReferenceImpulseTests(unittest.TestCase):
    def test_actual_source_impulses_fit_independent_dimensioned_histories(self):
        compiler = compile_construction(impulse_variant())
        snapshot = ReachSimulator(compiler.model, work=compiler.reach_work).advance(F(2), "after")
        unavailable = AssertionError("production expectation generator called")
        with patch("ontokin.reach_runtime.ReachSimulator", side_effect=unavailable), \
             patch("ontokin.reach_pose.ReachPoseOps", side_effect=unavailable), \
             patch("ontokin.reach_kinematics.admit_planar", side_effect=unavailable):
            reference = build_reference(compiler.model, end=F(2), work=compiler.reach_work)
            expected = reference.sample(F(2))["objects"]["payload"]["impulses"]
        actual = snapshot["objects"]["payload"]["impulses"]
        self.assertEqual(actual["applied_count"], 3)
        self.assertEqual(len(actual["last_applications"]), 3)
        _assert_projection(actual, expected, arithmetic=_Bounds(compiler.reach_work),
            allowances={}, path=("boundary_states", "impulse_states_after", "payload"))
        for recorded, enclosure in zip(actual["last_applications"], expected["last_applications"]):
            for field in FIELDS:
                for value, interval in zip(recorded[field], enclosure[field]):
                    self.assertIsInstance(interval, Interval)
                    self.assertTrue(interval.contains(value), (field, value, interval))
        self.assertEqual(actual["last_applications"][-1]["linear_velocity_before_world_m_per_s"],
                         actual["last_applications"][-1]["linear_velocity_after_world_m_per_s"])
        self.assertLessEqual(compiler.reach_work.operations, 100000)

    def test_impulse_fields_do_not_inherit_unrelated_global_tolerances(self):
        actual = {"last_applications": [{field: [1.0, 0.0, 0.0] for field in FIELDS}]}
        expected = {"last_applications": [{field: [Interval(F(1), F(1)),
            Interval(F(0), F(0)), Interval(F(0), F(0))] for field in FIELDS}]}
        # A huge ordinary pose allowance cannot authorize an extra ULP of
        # momentum, lever length or velocity outside its source enclosure.
        allowances = {name: F(1000000) for name in ("position", "rotation", "velocity", "angular_velocity")}
        for field in FIELDS:
            changed = copy.deepcopy(actual)
            changed["last_applications"][0][field][0] = math.nextafter(1.0, math.inf)
            with self.subTest(field=field), self.assertRaises(OntoKinError) as failure:
                _assert_projection(changed, expected, arithmetic=_Bounds(ReachExecutionWork()),
                                   allowances=allowances, path=("impulse_states_after", "payload"))
            self.assertEqual(failure.exception.diagnostic.details["export_code"], "OKE-E-BOUNDARY-HISTORY")


if __name__ == "__main__":
    unittest.main()
