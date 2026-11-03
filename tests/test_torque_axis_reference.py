"""Canonical zero-axis admission is separate from numerical uncertainty."""
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.reach_reference import build_reference, ReferenceError
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.torque_reference import TorqueReference


FROZEN = Path(__file__).resolve().parents[1] / "docs/language-design/torque-v0.1/freeze"


def source(name="p01-spin-up", *, append="", substitute=None, transform=None):
    bundle = load_texture_file_manifest(FROZEN / (name + ".files.json"))
    text = bundle.entry.text
    if substitute is not None:
        before, after = substitute
        assert text.count(before) == 1
        text = text.replace(before, after)
    if append:
        head, tail = text.rsplit("}", 1)
        text = head + append + "}" + tail
    if transform is not None:
        text = transform(text)
    bundle = replace(bundle, entry=replace(bundle.entry, raw=text.encode()))
    ledger = SharedExecutionBudget()
    admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
    compiler = compile_construction(bundle, execution_budget=ledger)
    return compiler.model, compiler.reach_work


def independent(name="p01-spin-up", *, end=F(3), **kwargs):
    model, work = source(name, **kwargs)
    return build_reference(model, end=end, mode="recording", work=work)


class TorqueAxisReferenceTests(unittest.TestCase):
    def test_zero_impulse_on_split_body_keeps_current_angular_anchor_and_speed(self):
        reference = independent(end=F(1), append='''
    at 1[s] sequence {
        impulse ball using vector(world, 0[N*s], 0[N*s], 0[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);
    }
''')
        state = reference.sample(F(1))["objects"]["ball"]["torques"]
        self.assertEqual(state["rotation_anchor_seconds"], "0")
        self.assertTrue(state["signed_angular_speed_rad_per_s"].contains(2))
        self.assertTrue(state["phase_since_anchor_rad"].contains(1))

    def test_nonzero_central_impulse_keeps_split_anchor_and_transports_errors(self):
        reference = independent(end=F(3, 2), append='''
    at 1[s] sequence {
        impulse ball using vector(world, 1[N*s], 0[N*s], 0[N*s]) at point(ball.frame, 0[m], 0[m], 0[m]);
    }
''')
        before = reference._state_at(F(1), "before").torques["ball"]
        after = reference._state_at(F(1), "after").torques["ball"]
        self.assertEqual(after.rotation.time, F(0))
        self.assertEqual(after.support, before.support)
        self.assertEqual(after.reference.time, F(1))
        old_theta, old_speed = reference._shadow_bounds(before, F(1))
        self.assertGreater(after.reference.theta_error, old_theta)
        self.assertGreater(after.reference.speed_error, old_speed)
        later = reference.sample(F(3, 2))["objects"]["ball"]["torques"]
        self.assertEqual(later["rotation_anchor_seconds"], "0")
        self.assertTrue(later["signed_angular_speed_rad_per_s"].contains(3))
        self.assertTrue(later["phase_since_anchor_rad"].contains(F(9, 4)))

    def test_parallel_nonzero_impulse_preserves_existing_split_anchor(self):
        reference = independent(end=F(3, 2), append='''
    at 1[s] sequence {
        impulse ball using vector(world, 0[N*s], 0[N*s], 1[N*s]) at point(ball.frame, 0[m], 0[m], 2[m]);
    }
''')
        state = reference.sample(F(3, 2))["objects"]["ball"]["torques"]
        self.assertEqual(state["rotation_anchor_seconds"], "0")
        self.assertTrue(state["signed_angular_speed_rad_per_s"].contains(3))

    def test_exact_permutation_cancellation_transports_released_hinge_axis(self):
        def transformed(text):
            text = text.replace('object carrier @ "carrier": Carrier {}', '''object carrier @ "carrier": Carrier {
        placement = pose(world, vec3(0[m], 0[m], 0[m]), quat(0.5, 0.5, 0.5, 0.5));
    }
    object arm @ "arm": Carrier {}
    joint swivel @ "swivel": hinge {
        parent = carrier.tip; child = arm.tip;
        axis = vec3(1, 0, 0); limits = range(-2[rad], 2[rad]); initial = 0[rad];
    }''')
            text = text.replace('parent = carrier.tip; child = ball.origin;', 'parent = arm.tip; child = ball.origin;')
            text = text.replace('move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s])',
                                'tween(swivel, 0.5[rad], 1[s])')
            return text.replace('about world_z', 'about world_y')
        reference = independent("p28-release-then-torque", end=F(1), transform=transformed)
        support = reference._state_at(F(1), "after").torques["ball"].support
        self.assertEqual(support.exact_omega, (F(0),F(1,2),F(0)))
        self.assertEqual(support.omega, (False,True,False))

    def test_parallel_nonzero_cross_product_has_exact_cancellation_fallback(self):
        original = 'torque ball @ "drive" about world_z using 2[N*m] for 2[s];'
        def transformed(text):
            text = text.replace('quat(1, 0, 0, 0)', 'quat(0.5, 0.5, 0.5, 0.5)', 1)
            return text.replace(original, original + '''
        impulse ball using vector(world, 3[N*s], 1[N*s], 2[N*s]) at point(ball.frame, 1[m], 2[m], 3[m]);''')
        reference = independent(end=F(0), transform=transformed)
        support = reference._state_at(F(0), "after").torques["ball"].support
        self.assertEqual(support.exact_omega, (F(0),)*3)
        self.assertEqual(reference.sample(F(0))["objects"]["ball"]["impulses"]["applied_count"], 1)

    def test_release_keeps_orthogonal_uncertainty_and_separate_exact_zero_witness(self):
        reference = independent("p28-release-then-torque", end=F(1))
        state = reference._state_at(F(1), "after")
        self.assertEqual(state.torques["ball"].support.omega, (False, False, True))
        self.assertGreater(state.dynamic["ball"].omega_error, 0)
        for cell in state.dynamic["ball"].actual.omega[:2]:
            self.assertLess(cell.lo, 0)
            self.assertGreater(cell.hi, 0)
        self.assertGreater(state.torques["ball"].reference.speed_error, 0)

    def test_late_axis_preserving_impulse_on_released_split_body_is_proved(self):
        reference = independent("p28-release-then-torque", end=F(3, 2), append='''
    at 1.5[s] sequence {
        impulse ball using vector(world, 0[N*s], 1[N*s], 0[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);
    }
''')
        state = reference._state_at(F(3, 2), "after")
        self.assertEqual(state.torques["ball"].support.omega, (False, False, True))
        self.assertGreater(state.dynamic["ball"].omega_error, 0)

    def test_tiny_off_axis_impulse_cannot_hide_inside_interval_uncertainty(self):
        text = '''
    at 1[s] sequence {
        impulse ball using vector(world, 0[N*s], 0[N*s], 0.000000000000000000000000000001[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);
    }
'''
        seen = []
        def old_consistency_only(reference, vector, axis, reason, support):
            index = {"world_x": 0, "world_y": 1, "world_z": 2}[axis]
            if reason == "impulse_axis":
                seen.append(tuple(vector))
                self.assertTrue(all(cell.contains(0) for i, cell in enumerate(vector) if i != index))
            return vector[index]
        # Retain a concrete witness of why the old contains-zero predicate
        # cannot serve as an exact canonical domain proof.
        with patch.object(TorqueReference, "_axis_check", old_consistency_only):
            independent(end=F(1), append=text)
        self.assertEqual(len(seen), 1)
        with self.assertRaises(ReferenceError) as caught:
            independent(end=F(1), append=text)
        self.assertEqual(caught.exception.details["torque_reason"], "impulse_axis")

    def test_tiny_off_axis_incoming_release_requires_its_own_exact_witness(self):
        substitution = ('move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s])',
                        'spin(carrier, vector(world, 0.000000000000000000000001[rad/s], 0[rad/s], 0[rad/s]), 1[s])')
        with self.assertRaises(ReferenceError) as caught:
            independent("p28-release-then-torque", end=F(1), substitute=substitution)
        self.assertEqual(caught.exception.details["torque_reason"], "incoming_axis")

    def test_inherited_rate_grid_underflow_is_an_exact_canonical_zero(self):
        substitution = ('move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s])',
                        'spin(carrier, vector(world, 0.000000000000000000000000000001[rad/s], 0[rad/s], 0[rad/s]), 1[s])')
        reference = independent("p28-release-then-torque", end=F(1), substitute=substitution)
        support = reference._state_at(F(1), "after").torques["ball"].support
        self.assertEqual(support.exact_omega, (F(0),)*3)

    def test_two_cancelling_impulses_cannot_hide_invalid_intermediate_axis(self):
        text = '''
    at 1[s] sequence {
        impulse ball using vector(world, 0[N*s], 0[N*s], 0.000000000000000000000000000001[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);
        impulse ball using vector(world, 0[N*s], 0[N*s], -0.000000000000000000000000000001[N*s]) at point(ball.frame, 1[m], 0[m], 0[m]);
    }
'''
        with self.assertRaises(ReferenceError) as caught:
            independent(end=F(1), append=text)
        self.assertEqual(caught.exception.details["torque_reason"], "impulse_axis")


if __name__ == "__main__":
    unittest.main()
