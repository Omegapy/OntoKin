"""Exact identity children reuse their freshly admitted constant parent pose."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_reference import ReferenceError
from test_reach_reference_identity_carriers import shoulder_source
from test_reach_reference_world_recording import cursors, reference_case


UPPER = "rig.arm.upper.frame"


class IndependentConstantParentTests(unittest.TestCase):
    def test_identity_hinge_reuses_constant_parent_without_a_second_local_pose(self):
        reference, compiler = reference_case("P01", F(1, 2))
        finer, _ = reference_case("P01", F(1, 2), bits=256)
        _, joint, _ = shoulder_source(reference)
        parent = joint.parent + ".frame"
        context = object()
        for time in (F(1, 8), F(1, 4), F(3, 8)):
            with patch.object(reference.p, "hinge", side_effect=AssertionError("duplicate zero local hinge")):
                actual = reference.recording_pose_enclosures((parent, UPPER), time, recording_context=context)
            expected = finer.recording_pose_enclosures((UPPER,), time)[UPPER]
            self.assertIs(actual[UPPER].position, actual[parent].position)
            self.assertIs(actual[UPPER].orientation, actual[parent].orientation)
            self.assertEqual(actual[UPPER], expected)
        self.assertFalse(any(key[-1][-1] == UPPER for key in cursors(reference.p)))
        self.assertLessEqual(compiler.budget.operations, 100000)

    def test_nonzero_constant_child_retains_its_own_local_source_equation(self):
        reference, _ = reference_case("P01", F(1, 2))
        state, joint, _ = shoulder_source(reference)
        active = state.actions[state.claims[(joint.path, "coordinate")]]
        active.ideal_initial = (F(1, 8), active.ideal_initial[1])
        active.targets = (F(1, 8), active.targets[1])
        with patch.object(reference.p, "hinge", wraps=reference.p.hinge) as hinge:
            reference.recording_pose_enclosures((UPPER,), F(1, 4), recording_context=object())
        self.assertTrue(any(call.args[1] == F(1, 8) for call in hinge.call_args_list))

    def test_constant_identity_final_receipt_rechecks_source_mutation(self):
        reference, _ = reference_case("P01", F(1, 2))
        state, joint, _ = shoulder_source(reference)
        active = state.actions[state.claims[(joint.path, "coordinate")]]
        original = reference._recording_identity_parent
        entered = []
        def intercept(parent, body):
            if body.path != UPPER:
                return original(parent, body)
            entered.append(True)
            checks = 0
            def mutate():
                nonlocal checks
                checks += 1
                if checks == len(body.receipts):
                    active.ideal_initial = (F(1, 8), active.ideal_initial[1])
            with patch.object(reference.a.work, "external_check", side_effect=mutate):
                return original(parent, body)
        with patch.object(reference, "_recording_identity_parent", side_effect=intercept), \
                self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures((UPPER,), F(1, 4), recording_context=object())
        self.assertTrue(entered)
        self.assertEqual(caught.exception.code, "identity")

    def test_constant_identity_cancellation_keeps_original_error_and_cache_order(self):
        reference, _ = reference_case("P01", F(1, 2))
        original = reference._recording_identity_parent
        marker = RuntimeError("cancel constant parent identity proof")
        entries = []
        def intercept(parent, body):
            if body.path != UPPER:
                return original(parent, body)
            entries.append(tuple(reference.a.cache.items()))
            with patch.object(reference.a.work, "external_check", side_effect=marker):
                return original(parent, body)
        with patch.object(reference, "_recording_identity_parent", side_effect=intercept), \
                self.assertRaises(RuntimeError) as caught:
            reference.recording_pose_enclosures((UPPER,), F(1, 4), recording_context=object())
        self.assertIs(caught.exception, marker)
        self.assertIs(reference.a.work.callback_error, marker)
        self.assertEqual(tuple(reference.a.cache.items()), entries[-1])


if __name__ == "__main__":
    unittest.main()
