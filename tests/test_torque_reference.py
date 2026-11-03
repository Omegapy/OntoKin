"""Independent finite-torque reconstruction and alpha-sensitive byte proofs."""
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.reach_reference import build_reference, _Arithmetic, ReferenceError
from ontokin.torque_reference import TorqueReference, TorqueErrorRequirement
from ontokin import torque_conformance as tc
from ontokin.diagnostics import OntoKinError

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "docs/language-design/torque-v0.1/freeze"


def reference(events, *, end=F(3), omega=0, inertia=1, orientation=None):
    bundle = load_texture_file_manifest(FROZEN / "control-spin-up.files.json")
    ledger = SharedExecutionBudget()
    admit_entry_budget(bundle.entry, ledger, profile="keyed-membership-0.1")
    compiler = compile_construction(bundle, execution_budget=ledger)
    model = compiler.model
    model.profile = "torque-0.1"
    model.objects["ball"].omega = (0.0, 0.0, float(omega))
    model.objects["ball"].physical["inertia"] = float(inertia)
    if orientation is not None:
        model.objects["ball"].placement = replace_pose(model.objects["ball"].placement, orientation)
    model.events = []
    for time, rows in events:
        statements = []
        for index, (key, scalar, duration, axis) in enumerate(rows):
            location = {"source_id": "entry", "source_revision": bundle.entry.revision,
                        "start_byte": 0, "end_byte": 1}
            payload = SimpleNamespace(key=key, axis=axis, torque_n_m=float(scalar), duration=F(duration),
                sequence_index=index, source=location, operand_source=location, duration_source=location)
            statements.append(SimpleNamespace(kind="torque", target="ball", torque=payload, span=model.span))
        model.events.append(SimpleNamespace(time=F(time), events=statements))
    # These are separately authored mathematical model-unit tests. They do
    # not substitute for the frozen literal-source acceptance cohort.
    return build_reference(model, end=end, mode="recording", work=compiler.reach_work)


def replace_pose(pose, orientation):
    from dataclasses import replace
    return replace(pose, rotation=orientation)


class TorqueIndependentReferenceTests(unittest.TestCase):
    def test_impulse_before_first_torque_uses_exact_controlled_transfer_radius(self):
        cases = json.loads((FROZEN / "physics-cases.json").read_text())["cases"]
        case = next(row for row in cases if row["id"] == "p20-impulse-then-torque")
        bundle = load_texture_file_manifest(FROZEN / case["file_manifest"])
        ledger = SharedExecutionBudget()
        admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
        compiler = compile_construction(bundle, execution_budget=ledger)
        r = build_reference(compiler.model, end=F(0), mode="recording", work=compiler.reach_work)
        state = r._state_at(F(0), "after")
        value = r._torques("ball", F(0), state)
        # Source-only derivation: identity lever=(1,0,0), J=(0,5/4,0),
        # own inertia=1. The two exact output sums have zero RN discrepancy.
        rounding = lambda size: size * F(1, 1 << 53) + F(3, 1 << 1075)
        before_angle = F(1, 1 << 91) + F(1, 1 << 50)
        required = (before_angle + F(2, 1 << 96) + rounding(F(1))) * F(5, 4) + rounding(F(5, 4))
        self.assertEqual(value["angular_speed_error_bound_rad_per_s"].minimum, required)
        self.assertEqual(state.dynamic["ball"].actual.omega[2].lo, F(5, 4))
        self.assertEqual(state.dynamic["ball"].actual.omega[2].hi, F(5, 4))
        tc.verify_error_requirement({"numerator": str(required.numerator),
                           "denominator": str(required.denominator)},
                          required, tc.rc._Bounds(), ("angular_speed_error_bound_rad_per_s",))
        with self.assertRaises(OntoKinError):
            tc.verify_error_requirement({"numerator": "0", "denominator": "1"},
                required, tc.rc._Bounds(), ("angular_speed_error_bound_rad_per_s",))

    def test_acceleration_completion_and_coast(self):
        r = reference([(0, [("spin", 2, 1, "world_z")])], end=F(2))
        self.assertEqual(r.boundaries, (F(0), F(1), F(2)))
        a = r.sample(F(1), "before")["objects"]["ball"]["torques"]
        b = r.sample(F(1), "after")["objects"]["ball"]["torques"]
        self.assertTrue(a["phase_since_anchor_rad"].contains(1))
        self.assertTrue(b["phase_since_anchor_rad"].contains(0))
        self.assertEqual(a["angular_acceleration_rad_per_s2"], 2)
        self.assertEqual(b["angular_acceleration_rad_per_s2"], 0)
        self.assertEqual(b["completed_count"], 1)
        self.assertTrue(r.pose_enclosure("ball", F(2), ideal=True).omega[2].contains(2))

    def test_completion_alone_enters_split_route(self):
        r = reference([(0, [("positive", 2, 2, "world_z"), ("negative", -2, 1, "world_z")])], end=F(2))
        before = r.sample(F(1), "before")["objects"]["ball"]["torques"]
        after = r.sample(F(1), "after")["objects"]["ball"]["torques"]
        self.assertEqual(before["rotation_route"], "legacy")
        self.assertEqual(after["rotation_route"], "split")
        self.assertEqual(after["rotation_anchor_seconds"], "1")

    def test_equal_canonical_acceleration_preserves_rotation_anchor(self):
        r = reference([(0, [("first", 2, 1, "world_z")]),
                       (1, [("second", 2, 1, "world_z")])], end=F(3, 2))
        state = r.sample(F(3, 2))["objects"]["ball"]["torques"]
        self.assertEqual(state["rotation_anchor_seconds"], "0")
        self.assertTrue(state["phase_since_anchor_rad"].contains(F(9, 4)))

    def test_reversal_maxima_and_nested_offset_acceleration(self):
        r = reference([(0, [("brake", -2, 2, "world_z")])], end=F(2), omega=2)
        root = r.phases("ball", 0, 2)[0]
        marker = r.phases("ball.arm.tip.frame", 0, 2)[0]
        self.assertEqual(root.angular_speed, 2)
        self.assertEqual(root.angular_acceleration, 2)
        self.assertEqual(marker.angular_acceleration, 2)
        self.assertGreater(marker.acceleration, 0)
        self.assertGreater(marker.offset_radius, 0)

    def test_underflow_shadow_remains_exact_without_split(self):
        r = reference([(0, [("tiny", float.fromhex("0x0.0000000000001p-1022"), 2, "world_z")])],
                      end=F(1), inertia=2)
        state = r.sample(F(1))["objects"]["ball"]["torques"]
        self.assertEqual(state["rotation_route"], "legacy")
        self.assertEqual(state["angular_acceleration_rad_per_s2"], 0)
        self.assertEqual(state["angular_acceleration_reference_rad_per_s2"],
                         {"numerator": "1", "denominator": str(1 << 1075)})
        self.assertGreaterEqual(state["angular_error_bound_rad"].minimum, F(1, 1 << 1076))
        self.assertGreaterEqual(state["angular_speed_error_bound_rad_per_s"].minimum, F(1, 1 << 1075))

    def test_exact_completion_clock_not_binary64_sum(self):
        r = reference([(F(0.1), [("pulse", 1, F(0.2), "world_z")])], end=F(1))
        exact = F(0.1) + F(0.2)
        self.assertIn(exact, r.boundaries)
        self.assertNotEqual(exact, F(0.3))
        state = r.sample(F(0.3))["objects"]["ball"]["torques"]
        self.assertEqual(len(state["active"]), 1)

    def test_interior_vertex_refuses_even_equal_endpoint_phases(self):
        with self.assertRaises(ReferenceError) as caught:
            reference([(0, [("reverse", -4 * ((1 << 20) + 1), 2, "world_z")])],
                      end=F(2), omega=4 * ((1 << 20) + 1))
        self.assertEqual(caught.exception.details.get("torque_reason"), "phase_domain")

    def test_world_axis_left_product_has_noncommuting_y_sign(self):
        r = reference([(0, [("spin", 2, 1, "world_z")])], end=F(1), orientation=(0.0, 1.0, 0.0, 0.0))
        q = r.pose_enclosure("ball", F(1), ideal=True).orientation
        self.assertEqual(q[0].magnitude, 0)
        self.assertGreater(q[1].lo, 0)
        self.assertGreater(q[2].lo, 0)
        self.assertEqual(q[3].magnitude, 0)

    def test_no_production_simulator_or_pose_kernel(self):
        unavailable = AssertionError("producer was consulted")
        with patch("ontokin.reach_runtime.ReachSimulator", side_effect=unavailable), \
             patch("ontokin.reach_pose.ReachPoseOps", side_effect=unavailable):
            r = reference([(0, [("pulse", 2, 1, "world_z")])], end=F(1))
            self.assertTrue(r.pose_enclosure("ball", F(1)).omega[2].contains(2))


def certificate():
    row = {name: 0.0 for name in tc.NUMERIC_KEYS}
    row.update(left_key_index=0, right_key_index=1, carrier={"path": "ball", "element_id": ["ball"]},
               source_phase_indices=[0], h_authored_seconds={"numerator": "1", "denominator": "100"},
               h_stored_seconds={"numerator": "1", "denominator": "100"})
    row.update(angular_speed_bound_rad_per_s=2.0, angular_acceleration_bound_rad_per_s2=2.0,
        enclosing_angular_speed_bound_rad_per_s=2.0, enclosing_angular_acceleration_bound_rad_per_s2=2.0,
        carrier_acceleration_bound_m_per_s2=6.0, enclosing_carrier_acceleration_bound_m_per_s2=6.0,
        enclosing_carrier_speed_bound_m_per_s=3.0, landmark_radius_m=1.0,
        stored_quaternion_arc_upper_rad=0.02, unit_quaternion_difference_bound=0.00008,
        ideal_rotation_bound_rad=0.00016, ideal_position_bound_m=0.00008,
        total_rotation_bound_rad=0.0004, carrier_position_bound_m=0.0001,
        total_position_bound_m=0.0006)
    return row


class TorqueIndependentCertificateTests(unittest.TestCase):
    def test_group_key_keeps_both_acceleration_claims_and_exact_maxima(self):
        options = SimpleNamespace(position_tolerance_m=0.1, rotation_tolerance_rad=0.1)
        batch = tc._TorqueCertificateBatch(tc.rc._Bounds(), options)
        first = certificate()
        first.update(destination_numeric_position_bound_m=1e-8,
                     destination_numeric_rotation_bound_rad=0.0005,
                     total_rotation_bound_rad=0.001,
                     total_position_bound_m=0.002)
        minima = {"angular_acceleration_bound_rad_per_s2": F(2)}
        batch.add(first, F(1, 100), F(1, 100), minima, F(0))
        batch.add(first, F(1, 200), F(1, 200), minima, F(0))
        self.assertEqual(len(batch.groups), 1)
        self.assertEqual(next(iter(batch.groups.values()))["width"], F(1, 100))
        second = dict(first, enclosing_angular_acceleration_bound_rad_per_s2=3.0)
        batch.add(second, F(1, 100), F(1, 100), minima, F(0))
        self.assertEqual(len(batch.groups), 2)
        second = dict(first, angular_acceleration_bound_rad_per_s2=0.0)
        batch.add(second, F(1, 100), F(1, 100), minima, F(0))
        self.assertEqual(len(batch.groups), 3)
        with self.assertRaises(OntoKinError) as caught:
            batch.flush()
        self.assertEqual(caught.exception.diagnostic.details.get("quantity"),
                         "angular_acceleration_bound_rad_per_s2")

    def test_torque_canonical_history_has_no_pose_or_second_rounding_allowance(self):
        from ontokin.reach_reference import Interval
        for field in ("phase_since_anchor_rad", "signed_angular_speed_rad_per_s"):
            path = ("boundary_states", 0, "torque_states_after", "ball", field)
            expected = Interval(F(1), F(1))
            tc.rc._assert_projection(1.0, expected, arithmetic=tc.rc._Bounds(),
                allowances={}, path=path)
            with self.assertRaises(OntoKinError):
                tc.rc._assert_projection(1.0000000000000002, expected,
                    arithmetic=tc.rc._Bounds(), allowances={}, path=path)

    def test_control_and_acceleration_quaternion_term(self):
        row = certificate()
        tc.check_complete_inequalities(row, position_tolerance=0.1, rotation_tolerance=0.1)
        row["unit_quaternion_difference_bound"] = 0.00007
        with self.assertRaises(OntoKinError):
            tc.check_complete_inequalities(row, position_tolerance=0.1, rotation_tolerance=0.1)

    def test_nonzero_acceleration_invalidates_zero_speed_quarter_shortcut(self):
        row = certificate()
        row["angular_speed_bound_rad_per_s"] = 0.0
        row["enclosing_angular_speed_bound_rad_per_s"] = 0.0
        row["angular_acceleration_bound_rad_per_s2"] = 1000000.0
        with self.assertRaises(OntoKinError):
            tc.check_complete_inequalities(row, position_tolerance=0.1, rotation_tolerance=0.1)

    def test_missing_or_extra_acceleration_field_refused(self):
        for name in tc.ACCELERATION_FIELDS:
            row = certificate()
            del row[name]
            with self.assertRaises(OntoKinError):
                tc.check_complete_inequalities(row, position_tolerance=0.1, rotation_tolerance=0.1)
        row = certificate()
        row["extra"] = 0
        with self.assertRaises(OntoKinError):
            tc.check_complete_inequalities(row, position_tolerance=0.1, rotation_tolerance=0.1)

    def test_error_rational_requires_reduction_and_minimum(self):
        a = tc.rc._Bounds()
        tc.verify_error_requirement({"numerator": "1", "denominator": "8"}, F(1, 8), a, ())
        for value in ({"numerator": "2", "denominator": "16"},
                      {"numerator": "0", "denominator": "1"},
                      {"numerator": "01", "denominator": "8"}):
            with self.assertRaises(OntoKinError):
                tc.verify_error_requirement(value, F(1, 8), a, ())


if __name__ == "__main__":
    unittest.main()
