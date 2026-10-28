"""Independent source topology proves signed coaxial ideal derivatives."""
from dataclasses import fields, replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork as Work
from ontokin.reach_reference import (
    Interval, ReferenceError, ReferencePhase, ReachReference, _Arithmetic, build_reference,
)
from reach_agent_support import source_case


def reference_case(case, end=F(2)):
    compiler = compile_construction(source_case(case))
    reference = build_reference(compiler.model, end=end, work=compiler.reach_work)
    return reference, compiler


def point(value):
    return Interval(F(value), F(value))


class IndependentAxisTransportTests(unittest.TestCase):
    def reference(self, work=None):
        reference = object.__new__(ReachReference)
        reference.a = _Arithmetic(work=work or Work(), bits=8)
        return reference

    def test_exact_quaternion_patterns_preserve_and_reverse_each_cartesian_axis(self):
        for axis in range(3):
            preserving = [F(2), F(0), F(0), F(0)]
            preserving[axis + 1] = F(-3, 7)
            reversing = [F(0)] * 4
            reversing[(axis + 1) % 3 + 1] = F(5, 9)
            with self.subTest(axis=axis):
                reference = self.reference()
                self.assertEqual(reference._axis_transport(tuple(preserving), axis), 1)
                self.assertEqual(reference._axis_transport(tuple(reversing), axis), -1)
                self.assertEqual(reference._axis_transport(tuple(-value for value in preserving), axis), 1)
                self.assertEqual(reference._axis_transport(tuple(-value for value in reversing), axis), -1)

    def test_uncertain_or_oblique_quaternions_do_not_claim_an_exact_axis(self):
        reference = self.reference()
        uncertain = Interval(F(-1, 8), F(1, 8))
        for quaternion in ((1, 1, 1, 1), (0, 0, 0, 0),
                           (point(1), uncertain, point(0), point(0)),
                           (uncertain, point(0), point(0), uncertain)):
            with self.subTest(quaternion=quaternion):
                self.assertIsNone(reference._axis_transport(quaternion, 2))

    def test_live_operand_limit_precedes_zero_pattern_shortcuts(self):
        work = Work(max_operand_bits=256)
        reference = self.reference(work)
        work.external_check = lambda: setattr(work, "max_operand_bits", 64)
        with self.assertRaises(ReferenceError) as caught:
            reference._axis_transport((point(1 << 80), point(0), point(0), point(0)), 2)
        self.assertEqual(caught.exception.code, "resource")

    def test_cancelled_axis_admission_preserves_the_original_exception(self):
        work = Work()
        reference = self.reference(work)
        marker = RuntimeError("cancel independent axial transport")
        def cancel():
            raise marker
        work.external_check = cancel
        with self.assertRaises(RuntimeError) as caught:
            reference._axis_transport((1, 0, 0, 0), 2)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)


class IndependentAxialDerivativeTests(unittest.TestCase):
    def test_p09_uses_signed_coordinate_rates_before_taking_the_angular_norm(self):
        reference, _ = reference_case("P09")
        state = reference._state_at(F(0), "after")
        action = reference.model.actions["reach"].reach
        shoulder = reference._joint_path(action.shoulder, F(0), F(2), state).slope
        elbow = reference._joint_path(action.elbow, F(0), F(2), state).slope
        self.assertLess(shoulder, 0)
        self.assertGreater(elbow, 0)
        forearm = reference._phase("rig.arm.forearm.frame", F(0), F(2), state)
        tool = reference._phase("rig.tool.frame", F(0), F(2), state)
        self.assertEqual(forearm.angular_speed, abs(shoulder + elbow))
        self.assertEqual(tool.angular_speed, forearm.angular_speed)
        self.assertLess(forearm.angular_speed, abs(shoulder) + abs(elbow))
        # Unit source links give |p'| <= |q1'| + |q1'+q2'| and
        # |p''| <= q1'^2 + (q1'+q2')^2 for the ideal tool origin.
        self.assertEqual(tool.speed, abs(shoulder) + abs(shoulder + elbow))
        self.assertEqual(tool.acceleration, shoulder * shoulder + (shoulder + elbow) ** 2)

    def test_refinement_preserves_every_generic_numeric_anchor_and_source_field(self):
        unchanged = tuple(field.name for field in fields(ReferencePhase)
                          if field.name not in {"speed", "acceleration", "angular_speed"})
        for case, time, end in (("P09", F(0), F(2)), ("P07", F(0), F(2)),
                                ("L02", F(1), F(3, 2)), ("P16", F(0), F(1))):
            reference, _ = reference_case(case, max(F(2), end))
            state = reference._state_at(time, "after")
            for carrier in ("rig.frame", "rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.tool.frame"):
                with self.subTest(case=case, carrier=carrier):
                    current = reference._phase(carrier, time, end, state)
                    with patch.object(reference, "_axial_derivatives", return_value=None):
                        generic = reference._phase(carrier, time, end, state)
                    self.assertEqual(tuple(getattr(current, name) for name in unchanged),
                                     tuple(getattr(generic, name) for name in unchanged))
                    for name in ("speed", "acceleration", "angular_speed"):
                        self.assertLessEqual(getattr(current, name), getattr(generic, name))

    def test_fresh_root_spin_combines_with_hinges_but_released_dynamic_root_is_generic(self):
        reference, _ = reference_case("P16", F(3))
        state = reference._state_at(F(0), "after")
        action = reference.model.actions["reach"].reach
        shoulder = reference._joint_path(action.shoulder, F(0), F(1), state).slope
        elbow = reference._joint_path(action.elbow, F(0), F(1), state).slope
        phase = reference._phase("rig.arm.forearm.frame", F(0), F(1), state)
        self.assertEqual(phase.angular_speed, abs(F(1, 4) + shoulder + elbow))
        dynamic = reference._state_at(F(2), "after")
        self.assertIsNone(reference._axial_derivatives("payload.frame", F(2), F(3), dynamic))
        current = reference._phase("payload.frame", F(2), F(3), dynamic)
        with patch.object(reference, "_axial_derivatives", return_value=None):
            self.assertEqual(current, reference._phase("payload.frame", F(2), F(3), dynamic))

    def test_noncoaxial_and_nonunit_source_axes_keep_the_generic_derivative_basis(self):
        for axis in ((0., 1., 0.), (0., 0., .5)):
            reference, _ = reference_case("P09")
            state = reference._state_at(F(0), "after")
            elbow = reference.model.actions["reach"].reach.elbow
            reference.model.joints[elbow].axis = axis
            reference._basis_cache.clear()
            with self.subTest(axis=axis):
                self.assertIsNone(reference._axial_derivatives("rig.arm.forearm.frame", F(0), F(1), state))
                current = reference._phase("rig.arm.forearm.frame", F(0), F(1), state)
                with patch.object(reference, "_axial_derivatives", return_value=None):
                    self.assertEqual(current, reference._phase("rig.arm.forearm.frame", F(0), F(1), state))

    def test_child_attachment_axis_reversal_changes_the_signed_body_rate(self):
        reference, _ = reference_case("P09")
        state = reference._state_at(F(0), "after")
        carrier = "rig.arm.forearm.frame"
        before = reference._axial_derivatives(carrier, F(0), F(1), state)
        elbow = reference.model.joints[reference.model.actions["reach"].reach.elbow]
        site = reference.model.sites[elbow.child]
        site.pose = replace(site.pose, rotation=(0., 1., 0., 0.))
        after = reference._axial_derivatives(carrier, F(0), F(1), state)
        self.assertEqual(after.axis, before.axis)
        self.assertEqual(after.rate, -before.rate)
        self.assertEqual((after.speed, after.acceleration), (before.speed, before.acceleration))

    def test_changed_lifecycle_and_root_anchor_evidence_are_read_again(self):
        reference, _ = reference_case("P09")
        state = reference._state_at(F(0), "after")
        carrier = "rig.arm.forearm.frame"
        first = reference._axial_derivatives(carrier, F(0), F(1), state)
        state.actions["reach"].status = "paused"
        paused = reference._axial_derivatives(carrier, F(0), F(1), state)
        self.assertNotEqual(first.rate, 0)
        self.assertEqual(paused.rate, 0)
        state.actions["reach"].status = "running"
        self.assertEqual(reference._axial_derivatives(carrier, F(0), F(1), state).rate, first.rate)
        reference, _ = reference_case("P16", F(1))
        state = reference._state_at(F(0), "after")
        self.assertIsNotNone(reference._axial_derivatives("rig.frame", F(0), F(1), state))
        state.actions["turn"].rotation_error = F(1, 1 << 80)
        self.assertIsNone(reference._axial_derivatives("rig.frame", F(0), F(1), state))

    def test_independent_derivative_proof_does_not_call_production_pose_or_phase_helpers(self):
        reference, _ = reference_case("P09")
        state = reference._state_at(F(0), "after")
        unavailable = AssertionError("production derivative oracle called")
        with patch("ontokin.reach_phase.phase_bounds", side_effect=unavailable), \
             patch("ontokin.reach_runtime.ReachSimulator", side_effect=unavailable), \
             patch("ontokin.reach_pose.ReachPoseOps", side_effect=unavailable):
            self.assertIsNotNone(reference._axial_derivatives("rig.tool.frame", F(0), F(1), state))


if __name__ == "__main__":
    unittest.main()
