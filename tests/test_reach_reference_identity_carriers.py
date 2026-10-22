"""An exact identity hinge needs no second independent world trajectory."""
from contextlib import nullcontext
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import MAX_CACHE, ReachReference, ReferenceError
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_world_recording import cursors, reference_case


ROOT = "rig.frame"
UPPER = "rig.arm.upper.frame"


def shoulder_source(reference):
    state = reference._state_at(F(0), "after")
    joint = reference.model.joints["rig.arm.shoulder"]
    child = reference.model.sites[joint.child]
    return state, joint, child


class IndependentIdentityCarrierTests(unittest.TestCase):
    def test_moving_parent_identity_hinge_reuses_both_enclosures_and_omits_its_cursor(self):
        reference, built = reference_case("P05", F(1, 2))
        finer, _ = reference_case("P05", F(1, 2), bits=256)
        _, joint, _ = shoulder_source(reference)
        parent = joint.parent + ".frame"
        context, visited = object(), []
        original = reference.p._recording_body_orientation
        def observe(*args, **kwargs):
            visited.append(kwargs["context"][-1])
            return original(*args, **kwargs)
        with patch.object(reference.p, "_recording_body_orientation", side_effect=observe):
            for index in range(1, 9):
                time = F(index, 32)
                actual = reference.recording_pose_enclosures((parent, UPPER), time, recording_context=context)
                expected = finer.recording_pose_enclosures((UPPER,), time)[UPPER]
                self.assertIs(actual[UPPER].position, actual[parent].position)
                self.assertIs(actual[UPPER].orientation, actual[parent].orientation)
                for name in ("position", "orientation"):
                    for cell, fine in zip(getattr(actual[UPPER], name), getattr(expected, name)):
                        self.assertLessEqual(cell.lo, fine.lo)
                        self.assertGreaterEqual(cell.hi, fine.hi)
        self.assertIn(ROOT, visited)
        self.assertNotIn(UPPER, visited)
        self.assertFalse(any(key[-1][-1] == UPPER for key in cursors(reference.p)))
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        self.assertLessEqual(built.budget.operations, 100000)

    def test_unclaimed_exact_zero_coordinate_and_positive_scalar_child_remain_identity(self):
        reference, _ = reference_case("P05", F(1, 2))
        state, joint, child = shoulder_source(reference)
        del state.claims[(joint.path, "coordinate")]
        state.ideal_coordinates[joint.path] = F(0)
        child.pose = replace(child.pose, rotation=(2., 0., 0., 0.))
        parent = joint.parent + ".frame"
        result = reference.recording_pose_enclosures((parent, UPPER), F(1, 8), recording_context=object())
        self.assertIs(result[UPPER].orientation, result[parent].orientation)
        self.assertIs(result[UPPER].position, result[parent].position)
        self.assertFalse(any(key[-1][-1] == UPPER for key in cursors(reference.p)))

    def test_negative_or_nonidentity_child_and_nonzero_coordinate_keep_their_own_proofs(self):
        for change in ("negative_child", "rotated_child", "nonzero_initial", "nonzero_target", "unclaimed"):
            reference, _ = reference_case("P05", F(1, 2))
            state, joint, child = shoulder_source(reference)
            if change == "negative_child":
                child.pose = replace(child.pose, rotation=(-1., 0., 0., 0.))
            elif change == "rotated_child":
                child.pose = replace(child.pose, rotation=(1., 0., 0., 1.))
            elif change == "unclaimed":
                del state.claims[(joint.path, "coordinate")]
                state.ideal_coordinates[joint.path] = F(1, 8)
            else:
                active = state.actions[state.claims[(joint.path, "coordinate")]]
                field = "ideal_initial" if change == "nonzero_initial" else "targets"
                values = list(getattr(active, field))
                values[0] = F(1, 8)
                setattr(active, field, tuple(values))
            original, visited = reference.p._recording_body_orientation, []
            def observe(*args, **kwargs):
                visited.append(kwargs["context"][-1])
                return original(*args, **kwargs)
            with self.subTest(change=change), \
                    patch.object(reference.p, "_recording_body_orientation", side_effect=observe):
                reference.recording_pose_enclosures((UPPER,), F(1, 8), recording_context=object())
            self.assertIn(UPPER, visited)
            self.assertTrue(any(key[-1][-1] == UPPER for key in cursors(reference.p)))

    def test_paused_nonzero_coordinate_and_nonzero_child_offset_do_not_alias(self):
        for change in ("paused", "offset"):
            reference, _ = reference_case("P05", F(1, 2))
            state, joint, child = shoulder_source(reference)
            if change == "paused":
                active = state.actions[state.claims[(joint.path, "coordinate")]]
                active.status, active.elapsed = "paused", F(1)
                active.targets = (F(1, 8), active.targets[1])
            else:
                child.pose = replace(child.pose, position=(0.125, 0., 0.))
            original, aliases = reference._recording_identity_parent, []
            def observe(parent, body):
                result = original(parent, body)
                if result is not None:
                    aliases.append(body.path)
                return result
            with self.subTest(change=change), \
                    patch.object(reference, "_recording_identity_parent", side_effect=observe):
                reference.recording_pose_enclosures((UPPER,), F(1, 8), recording_context=object())
            self.assertNotIn(UPPER, aliases)

    def test_last_receipt_callback_source_mutation_is_rejected_before_identity_return(self):
        reference, _ = reference_case("P05", F(1, 2))
        state, joint, _ = shoulder_source(reference)
        active = state.actions[state.claims[(joint.path, "coordinate")]]
        initial, original = active.ideal_initial, reference._recording_identity_parent
        changed = []
        def enter(parent, body):
            if body.path != UPPER:
                return original(parent, body)
            checks = 0
            def mutate():
                nonlocal checks
                checks += 1
                if checks == len(body.receipts):
                    active.ideal_initial = (F(1, 8), initial[1])
                    changed.append(True)
            with patch.object(reference.a.work, "external_check", side_effect=mutate):
                return original(parent, body)
        with patch.object(reference, "_recording_identity_parent", side_effect=enter), \
                self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures((UPPER,), F(1, 8), recording_context=object())
        self.assertTrue(changed)
        self.assertEqual(caught.exception.code, "identity")
        self.assertFalse(any(key[-1][-1] == UPPER for key in cursors(reference.p)))
        active.ideal_initial = initial
        recovered = reference.recording_pose_enclosures((UPPER,), F(1, 4), recording_context=object())
        self.assertIn(UPPER, recovered)

    def test_identity_receipt_cancellation_preserves_exception_and_cache_order(self):
        for fail_at in (1, -1):
            reference, _ = reference_case("P05", F(1, 2))
            marker = RuntimeError("cancel independent identity carrier")
            original, snapshots = reference._recording_identity_parent, []
            def enter(parent, body):
                if body.path != UPPER:
                    return original(parent, body)
                snapshots.append(tuple(reference.a.cache.items()))
                checks = 0
                def cancel():
                    nonlocal checks
                    checks += 1
                    if checks == (len(body.receipts) if fail_at == -1 else fail_at):
                        raise marker
                with patch.object(reference.a.work, "external_check", side_effect=cancel):
                    return original(parent, body)
            with self.subTest(fail_at=fail_at), \
                    patch.object(reference, "_recording_identity_parent", side_effect=enter), \
                    self.assertRaises(RuntimeError) as caught:
                reference.recording_pose_enclosures((UPPER,), F(1, 8), recording_context=object())
            self.assertIs(caught.exception, marker)
            self.assertIs(reference.a.work.callback_error, marker)
            self.assertEqual(tuple(reference.a.cache.items()), snapshots[-1])

    def test_narrowed_identity_admission_reenters_original_source_failure_without_retry(self):
        reference, _ = reference_case("P05", F(1, 2))
        original = reference._recording_identity_parent
        direct_failures = []
        marker = ReferenceError("resource", "original direct source rejects the narrowed operand")
        def enter(parent, body):
            if body.path != UPPER:
                return original(parent, body)
            with patch.object(reference.a.work, "external_check", side_effect=lambda: setattr(
                    reference.a.work, "max_operand_bits", 64)):
                result = original(parent, body)
            self.assertIsNone(result)
            direct_failures.append(True)
            def direct(clock):
                reference.a.work.max_operand_bits = 32768
                raise marker
            object.__setattr__(body, "direct", direct)
            return result
        with patch.object(reference, "_recording_identity_parent", side_effect=enter), \
                self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures((UPPER,), F(1, 8), recording_context=object())
        self.assertTrue(direct_failures)
        self.assertIs(caught.exception, marker)
        self.assertFalse(any(key[-1][-1] == UPPER for key in cursors(reference.p)))

    def test_source_observations_and_other_precisions_never_call_identity_carrier_reuse(self):
        for bits in (128, 256):
            reference, _ = reference_case("P05", F(1, 2), bits=bits)
            with self.subTest(bits=bits), patch.object(reference, "_recording_identity_parent",
                    side_effect=AssertionError("recording-only identity reuse")):
                reference.pose_enclosure(UPPER, F(1, 8))
                reference.recording_pose_enclosures((UPPER,), F(1, 8))
                if bits != 128:
                    reference.recording_pose_enclosures((UPPER,), F(1, 8), recording_context=object())

    def test_complete_glb_bytes_and_validation_are_identical_with_less_shared_work(self):
        outcomes = []
        for reuse in (False, True):
            built = compile_construction(source_case("P05"))
            mode = nullcontext() if reuse else patch.object(ReachReference, "_recording_identity_parent", return_value=None)
            with mode:
                result = export_glb(built.model, options=ExportOptions(end=F(1, 4), fps=24, helpers=False),
                                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertEqual(built.reach_work.max_operations, 100000)
            self.assertLessEqual(built.budget.operations, 100000)
            outcomes.append((result.data, result.report["validation"], built.budget.operations))
        self.assertEqual(outcomes[0][:2], outcomes[1][:2])
        self.assertLess(outcomes[1][2], outcomes[0][2])


if __name__ == "__main__":
    unittest.main()
