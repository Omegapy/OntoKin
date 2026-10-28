"""Completed exact seeds retain source arithmetic and bounded cache admission."""
from contextlib import ExitStack, nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
from types import MappingProxyType
import unittest
from unittest.mock import patch

from ontokin import reach_kinematics, reach_recording_fast
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import RecordingAngularProof, phase_bounds
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_fast import captured_recording_orientation
from test_reach_recording_graph_sharing import frozen, records
from test_reach_recording_sampler import simulator


SEED_NAMESPACE = "recording_captured_direct_seed_v1"


def proof_for(prefix="arm", *, offset=0.0, change=None):
    root, site, joint = records(prefix, offset)
    if change is not None:
        root, site, joint = change(root, site, joint)
    frame = prefix + ".upper.frame"
    proof = RecordingAngularProof(F(0), F(2), "seed-test",
        MappingProxyType({"rig.frame": root, prefix + ".mount.frame": site, frame: joint}))
    return proof, frame


def change_joint(index, value):
    def change(root, site, joint):
        witness = list(joint.witness)
        witness[index] = value(witness[index])
        return root, site, replace(joint, witness=tuple(witness))
    return change


def change_law(index, value):
    def apply(law):
        result = list(law)
        result[index] = value(result[index])
        return tuple(result)
    return change_joint(9, apply)


def without_seed_reuse():
    return patch.object(reach_recording_fast, "_captured_recording_seed_key", return_value=None)


class ReachRecordingExactSeedReuseTests(unittest.TestCase):
    def test_equivalent_named_translated_chains_share_the_complete_private_seed(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        expected = captured_recording_orientation(ops, proof, frame, F(1, 4))
        other, other_frame = proof_for("other", offset=7.75)
        with patch.object(reach_recording_fast, "_captured_recording_orientation_direct",
                          side_effect=AssertionError("recomputed identical exact seed")):
            actual = captured_recording_orientation(ops, other, other_frame, F(1, 4))
        self.assertEqual(actual, expected)
        self.assertEqual(actual.frozen_projection, expected.frozen_projection)
        self.assertLessEqual(len(work._cache), 256)

    def test_every_changed_orientation_operand_and_clock_uses_its_own_calculation(self):
        changes = (
            change_joint(5, lambda _: frozen((0.0, 0.0, -1.0))),
            change_joint(8, lambda old: (old[0], frozen((0.0, 0.0, 0.0, 1.0)))),
            change_joint(1, lambda _: "arm.elbow"),
            change_law(3, lambda _: frozen(F(3))),
            change_law(7, lambda _: frozen("paused")),
            change_law(8, lambda _: frozen((0.125, 0.0))),
            change_law(10, lambda _: frozen((0.375, 0.75))),
            change_law(11, lambda _: frozen(F(1, 8))),
            change_law(12, lambda _: frozen(F(1, 8))),
        )
        direct = reach_recording_fast._captured_recording_orientation_direct
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                ops = ReachPoseOps(ReachExecutionWork())
                proof, frame = proof_for()
                captured_recording_orientation(ops, proof, frame, F(1, 4))
                changed, changed_frame = proof_for(change=change)
                with patch.object(reach_recording_fast, "_captured_recording_orientation_direct",
                                  wraps=direct) as called:
                    actual = captured_recording_orientation(ops, changed, changed_frame, F(1, 4))
                self.assertEqual(called.call_count, 1)
                with without_seed_reuse(), patch.object(reach_kinematics, "recording_pair",
                                                       reach_kinematics.sample_pair):
                    expected = captured_recording_orientation(
                        ReachPoseOps(ReachExecutionWork()), changed, changed_frame, F(1, 4))
                self.assertEqual(actual, expected)
        ops = ReachPoseOps(ReachExecutionWork())
        proof, frame = proof_for()
        first = captured_recording_orientation(ops, proof, frame, F(1, 4))
        with patch.object(reach_recording_fast, "_captured_recording_orientation_direct",
                          wraps=direct) as called:
            second = captured_recording_orientation(ops, proof, frame, F(1, 2))
        self.assertEqual(called.call_count, 1)
        self.assertNotEqual(first.components, second.components)

    def test_noncommuting_root_and_child_rotations_keep_order_and_frozen_projection(self):
        def changed(root, site, joint):
            root_witness = list(root.witness)
            root_witness[5] = frozen((0.0, 1.0, 0.0, 0.0))
            joint_witness = list(joint.witness)
            child = joint_witness[8]
            joint_witness[8] = (child[0], frozen((0.0, 0.0, 1.0, 0.0)))
            return replace(root, witness=tuple(root_witness)), site, replace(joint, witness=tuple(joint_witness))
        proof, frame = proof_for(change=changed)
        results = []
        for cache in (False, True):
            ops = ReachPoseOps(ReachExecutionWork())
            with nullcontext() if cache else without_seed_reuse():
                for _ in range(2):
                    value = captured_recording_orientation(ops, proof, frame, F(1, 4))
                results.append(value)
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0].frozen_projection, results[1].frozen_projection)

    def test_malformed_frozen_numeric_types_cannot_alias_a_warm_valid_recipe(self):
        for invalid in (1.0, True, F(1)):
            with self.subTest(type=type(invalid).__name__):
                ops = ReachPoseOps(ReachExecutionWork())
                proof, frame = proof_for()
                captured_recording_orientation(ops, proof, frame, F(1, 4))
                changed, changed_frame = proof_for(change=change_law(
                    3, lambda old: (old[0], old[1], invalid)))
                with self.assertRaises(ReachAdmissionError) as caught:
                    captured_recording_orientation(ops, changed, changed_frame, F(1, 4))
                self.assertEqual(caught.exception.reach_code, "reach_domain")

    def test_root_spin_keeps_its_separately_admitted_phase_plan_dependency(self):
        def spin(root, site, joint):
            witness = list(root.witness)
            witness[8] = (
                frozen("rig.spin"), frozen("spin"), frozen("rig"), frozen(F(2)),
                frozen((0.0, 0.0, 0.25)), frozen(None), frozen(None), frozen("running"),
                frozen((1.0, 0.0, 0.0, 0.0)), frozen(None), frozen(None),
                frozen(F(0)), frozen(F(0)), frozen(F(0)), frozen(None))
            return replace(root, witness=tuple(witness)), site, joint
        proof, frame = proof_for(change=spin)
        ops = ReachPoseOps(ReachExecutionWork())
        direct = reach_recording_fast._captured_recording_orientation_direct
        with patch.object(reach_recording_fast, "_captured_recording_orientation_direct",
                          wraps=direct) as called:
            first = captured_recording_orientation(ops, proof, frame, F(1, 4))
            second = captured_recording_orientation(ops, proof, frame, F(1, 4))
        self.assertEqual(first, second)
        self.assertEqual(called.call_count, 2)
        self.assertFalse(any(key[0] == SEED_NAMESPACE for key in ops.work._cache))

    def test_narrow_cap_does_not_admit_a_seed_computed_in_the_full_domain(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        captured_recording_orientation(ops, proof, frame, F(1, 4))
        work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as caught:
            captured_recording_orientation(ops, proof, frame, F(1, 4))
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["limit"], 128)

    def test_cap_change_during_warm_promotion_restarts_original_narrow_admission(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        captured_recording_orientation(ops, proof, frame, F(1, 4))
        original, changed = work.charge, []
        def charge(kind="checkpoint", amount=1):
            if kind == "cache_promote" and not changed:
                changed.append(True)
                work.external_check = lambda: setattr(work, "max_operand_bits", 128)
            return original(kind, amount)
        with patch.object(work, "charge", side_effect=charge):
            with self.assertRaises(ReachAdmissionError) as caught:
                captured_recording_orientation(ops, proof, frame, F(1, 4))
        self.assertEqual(changed, [True])
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertFalse(any(key[0] == SEED_NAMESPACE for key in work._cache))

    def test_cap_change_at_seed_publication_cannot_return_the_old_wide_result(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        remember, changed = work.remember, []
        def publish(key, value, **keywords):
            if key[0] == SEED_NAMESPACE and not changed:
                changed.append(True)
                work.external_check = lambda: setattr(work, "max_operand_bits", 128)
            return remember(key, value, **keywords)
        with patch.object(work, "remember", side_effect=publish):
            with self.assertRaises(ReachAdmissionError) as caught:
                captured_recording_orientation(ops, proof, frame, F(1, 4))
        self.assertEqual(changed, [True])
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertFalse(any(key[0] == SEED_NAMESPACE for key in work._cache))

    def test_warm_promotion_cancellation_preserves_original_error_and_cache_order(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        captured_recording_orientation(ops, proof, frame, F(1, 4))
        before, original = tuple(work._cache.items()), work.charge
        marker = RuntimeError("cancel exact seed promotion")
        def charge(kind="checkpoint", amount=1):
            if kind == "cache_promote":
                work.external_check = lambda: (_ for _ in ()).throw(marker)
            return original(kind, amount)
        with patch.object(work, "charge", side_effect=charge):
            with self.assertRaises(RuntimeError) as caught:
                captured_recording_orientation(ops, proof, frame, F(1, 4))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(tuple(work._cache.items()), before)

    def test_cancelled_seed_publication_cannot_change_existing_cache_members(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        remember, before = work.remember, []
        marker = RuntimeError("cancel completed exact seed publication")
        def publish(key, value, **keywords):
            if key[0] == SEED_NAMESPACE:
                before.append(tuple(work._cache.items()))
                work.external_check = lambda: (_ for _ in ()).throw(marker)
            return remember(key, value, **keywords)
        with patch.object(work, "remember", side_effect=publish):
            with self.assertRaises(RuntimeError) as caught:
                captured_recording_orientation(ops, proof, frame, F(1, 4))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(len(before), 1)
        self.assertEqual(tuple(work._cache.items()), before[0])
        self.assertFalse(any(key[0] == SEED_NAMESPACE for key in work._cache))

    def test_original_callback_resource_error_is_never_replaced_by_a_retry(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        marker = ReachAdmissionError("reach_resource", "original callback",
                                     budget="numeric_operand_bits", limit=128, consumed=129)
        original = work.charge
        def fail():
            work.max_operand_bits = 128
            raise marker
        def charge(kind="checkpoint", amount=1):
            if kind == "recording_body_seed_decode":
                work.external_check = fail
            return original(kind, amount)
        with patch.object(work, "charge", side_effect=charge):
            with self.assertRaises(ReachAdmissionError) as caught:
                captured_recording_orientation(ops, proof, frame, F(1, 4))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)

    def test_eviction_remains_inside_the_existing_request_cache(self):
        work = ReachExecutionWork(max_cache_entries=4)
        ops = ReachPoseOps(work)
        proof, frame = proof_for()
        for number in range(1, 9):
            captured_recording_orientation(ops, proof, frame, F(number, 16))
            self.assertLessEqual(len(work._cache), 4)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.max_operand_bits, MAX_OPERAND_BITS)

    def test_actual_p23_boundary_seeds_keep_private_values_and_reduce_charged_work(self):
        results = []
        names = ("first", "part-01", "part-02", "part-03")
        paths = tuple(f'rig.arms["{name}"].{part}.frame'
                      for name in names for part in ("upper", "forearm"))
        for cache in (False, True):
            sim = simulator("P23")
            sim.advance(F(0), "after")
            phase = phase_bounds(sim, F(0), F(2), sim.state,
                                 selected_frames=paths, recording_proof=True)
            before_state, before_ops = deepcopy(sim.state), sim.work.operations
            with ExitStack() as stack:
                if not cache:
                    stack.enter_context(without_seed_reuse())
                    stack.enter_context(patch.object(reach_kinematics, "recording_pair",
                                                      reach_kinematics.sample_pair))
                values = tuple(captured_recording_orientation(sim.pose_ops,
                    phase["recording_angular_proof"], path, F(0)) for path in paths)
            results.append((values, sim.work.operations - before_ops))
            self.assertEqual(sim.state, before_state)
            self.assertLessEqual(len(sim.work._cache), 256)
            self.assertLessEqual(sim.work.operations, 100000)
        self.assertEqual(results[0][0], results[1][0])
        self.assertLess(results[1][1], results[0][1])


if __name__ == "__main__":
    unittest.main()
