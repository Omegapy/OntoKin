"""One static traversal can reuse an identical complete source rotation."""
from contextlib import contextmanager, nullcontext
from dataclasses import replace
from fractions import Fraction as F
import struct
from types import MappingProxyType
import unittest
from unittest.mock import patch

from ontokin import reach_runtime as runtime
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_phase import phase_bounds
from ontokin.reach_pose import ReachPoseOps, RotationValue
from test_reach_recording_sampler import simulator


def prepared(*, count=3, case="P23", start=F(2), end=F(3), change=None):
    sim = simulator(case)
    sim.advance(start, "after")
    if case == "P23" and count is not None:
        names = ("first", *(f"part-{index:02}" for index in range(1, count)))
        paths = ("rig.frame", *(f'rig.arms["{name}"].{part}.frame'
                  for name in names for part in ("upper", "forearm")))
    else:
        paths = tuple(path + ".frame" for path in sim.model.objects)
    if change is not None:
        change(sim)
    proof = phase_bounds(sim, start, end, sim.state,
                         selected_frames=paths, recording_proof=True)
    return sim, paths, proof["recording_angular_proof"], object()


def sample(fixture, time=F(2), *, recording=True, incremental=True):
    sim, paths, proof, context = fixture
    _, frames = sim._resolve_kinematics(time, sim.state, selected_frames=paths,
        pose_only=True, recording_only=recording,
        recording_moving_frames=frozenset(),
        recording_context=context if recording and incremental else None,
        recording_angular_proof=proof if recording and incremental else None)
    return {path: frames[path] for path in paths}


def values(frames):
    # Keep private cells, error and frozen semantics as well as public bits.
    return tuple((path, pose.exact_position, pose.rotation.components,
                  pose.rotation.error_rad, pose.rotation.frozen_projection,
                  struct.pack("<7d", *pose.position, *pose.orientation))
                 for path, pose in frames.items())


@contextmanager
def callbacks(work, callback):
    """Observe the existing charge name through the actual caller callback."""
    original_charge, original_check, active = work.charge, work.external_check, [None]
    def checked():
        if original_check is not None:
            original_check()
        callback(active[0])
    def charged(kind="checkpoint", amount=1):
        active[0] = kind
        return original_charge(kind, amount)
    work.external_check = checked
    try:
        with patch.object(work, "charge", side_effect=charged):
            yield
    finally:
        work.external_check = original_check


def representative(work):
    return next(value[1] for key, value in work._cache.items()
                if len(key) > 4 and key[1:3] == ("recording_rotation_cursor", "body")
                and key[4] == 'carrier:rig.arms["first"].upper')


class StaticRecordingRotationTests(unittest.TestCase):
    def assert_accounted(self, work):
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertLessEqual(len(work._cache), work.max_cache_entries)

    def test_original_p23_complete_static_graph_preserves_exact_values_with_less_work(self):
        outcomes = []
        for enabled in (False, True):
            fixture = prepared(count=None)
            sim = fixture[0]
            before, counts = sim.work.operations, dict(sim.work.counts)
            with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                actual = values(sample(fixture))
            delta = {key: value - counts.get(key, 0) for key, value in sim.work.counts.items()}
            outcomes.append((actual, sim.work.operations - before, delta))
            self.assert_accounted(sim.work)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])
        self.assertGreater(outcomes[1][2].get("recording_static_body_shared_orientation", 0), 0)
        self.assertLess(outcomes[1][2].get("recording_body_direct_seed", 0),
                        outcomes[0][2].get("recording_body_direct_seed", 0))
        print(f"P23 static complete graph: ordinary={outcomes[0][1]}, shared={outcomes[1][1]}, "
              f"saved={outcomes[0][1] - outcomes[1][1]}; "
              f"direct seeds={outcomes[0][2].get('recording_body_direct_seed', 0)}"
              f"->{outcomes[1][2].get('recording_body_direct_seed', 0)}")

    def test_repeated_clocks_keep_exact_rotations_and_fresh_wrappers(self):
        outcomes = []
        for enabled in (False, True):
            fixture = prepared()
            with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                frames = [sample(fixture, time) for time in (F(2), F(3), F(5, 2))]
                outcomes.append([values(value) for value in frames])
            if enabled:
                first = frames[0]['rig.arms["first"].upper.frame'].rotation
                second = frames[0]['rig.arms["part-01"].upper.frame'].rotation
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                for left, right in zip((*first.components, first.error_rad),
                                       (*second.components, second.error_rad)):
                    self.assertIsNot(left, right)
            self.assert_accounted(fixture[0].work)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_frozen_root_projection_and_distinct_signed_origins_preserve_every_field(self):
        def change(sim):
            sim.state.positions["rig"] = (0.125, -0.0, -0.25)
            sim.state.root_rotation_values["rig"] = RotationValue((F(1), F(0), F(0), F(0)),
                F(1, 1 << 90), (1.0, -0.0, 0.0, -0.0))
        outcomes = []
        for enabled in (False, True):
            fixture = prepared(change=change)
            with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                frames = sample(fixture)
                outcomes.append(values(frames))
            origins = {frame.exact_position for frame in frames.values()}
            self.assertGreater(len(origins), 2)
            self.assert_accounted(fixture[0].work)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_changed_coordinate_child_rotation_and_parent_placement_enter_the_recipe(self):
        def change(sim):
            stem = 'rig.arms["part-01"]'
            sim.state.coordinates[stem + ".shoulder"] = F(1, 4)
            elbow = sim.model.joints[stem + ".elbow"]
            child = sim.model.sites[elbow.child]
            child.pose = replace(child.pose, rotation=(0.0, 0.0, 0.0, 1.0))
            parent = sim.model.sites[elbow.parent]
            parent.pose = replace(parent.pose, position=(1.25, 0.0, 0.0))
        outcomes = []
        for enabled in (False, True):
            fixture = prepared(change=change)
            with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                frames = sample(fixture)
                outcomes.append(values(frames))
            self.assertNotEqual(frames['rig.arms["first"].upper.frame'].rotation,
                                frames['rig.arms["part-01"].upper.frame'].rotation)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_moving_and_dynamic_states_keep_the_original_graph(self):
        for case, start, end in (("P23", F(0), F(2)), ("P16", F(2), F(3))):
            outcomes = []
            for enabled in (False, True):
                fixture = prepared(case=case, start=start, end=end)
                sim = fixture[0]
                self.assertFalse(runtime._share_static_recording_rotations(sim.state, sim.pose_ops))
                before = sim.work.operations
                with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                    outcomes.append((values(sample(fixture, (start + end) / 2)), sim.work.operations - before))
                self.assertEqual(sim.work.counts.get("recording_static_body_shared_orientation", 0), 0)
            with self.subTest(case=case):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_full_source_and_strict_recording_paths_do_not_enter_the_static_index(self):
        for recording in (False, True):
            outcomes = []
            for enabled in (False, True):
                fixture = prepared()
                before = fixture[0].work.operations
                with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                    frames = sample(fixture, recording=recording, incremental=False)
                    outcomes.append((values(frames), fixture[0].work.operations - before))
                self.assertEqual(fixture[0].work.counts.get("recording_static_witness_block", 0), 0)
            self.assertEqual(outcomes[0], outcomes[1])

    def test_custom_dispatch_and_foreign_owners_decline_static_sharing(self):
        sim = prepared()[0]
        self.assertTrue(runtime._share_static_recording_rotations(sim.state, sim.pose_ops))
        class OtherOps(ReachPoseOps):
            pass
        self.assertFalse(runtime._share_static_recording_rotations(sim.state, OtherOps(sim.work)))
        original = ReachPoseOps.recording_body_orientation
        def replacement(self, *args, **kwargs):
            return original(self, *args, **kwargs)
        with patch.object(ReachPoseOps, "recording_body_orientation", new=replacement):
            self.assertFalse(runtime._share_static_recording_rotations(sim.state, sim.pose_ops))
        with patch.object(sim.pose_ops, "recording_body_orientation", wraps=sim.pose_ops.recording_body_orientation):
            self.assertFalse(runtime._share_static_recording_rotations(sim.state, sim.pose_ops))

    def test_lowered_entry_domain_keeps_the_original_calculation(self):
        outcomes = []
        for enabled in (False, True):
            fixture = prepared()
            fixture[0].work.max_operand_bits = 32767
            before = fixture[0].work.operations
            with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                outcomes.append((values(sample(fixture)), fixture[0].work.operations - before))
            self.assertEqual(fixture[0].work.counts.get("recording_static_body_shared_orientation", 0), 0)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_descriptors_cannot_claim_native_dispatch_or_execute_admission(self):
        sim, reads = prepared()[0], []
        native = ReachPoseOps.recording_body_orientation
        class Descriptor:
            def __get__(self, instance, owner):
                reads.append(instance)
                return native if instance is None else lambda *args, **kwargs: None
        with patch.object(ReachPoseOps, "recording_body_orientation", new=Descriptor()):
            self.assertFalse(runtime._share_static_recording_rotations(sim.state, sim.pose_ops))
        with patch.object(ReachPoseOps, "work", new=Descriptor(), create=True):
            self.assertFalse(runtime._share_static_recording_rotations(sim.state, sim.pose_ops))
        self.assertEqual(reads, [])
        self.assertTrue(runtime._share_static_recording_rotations(sim.state, sim.pose_ops))

    def test_a_narrowed_then_restored_callback_domain_cannot_revive_sharing(self):
        expected_fixture = prepared()
        with patch.object(runtime, "_share_static_recording_rotations", return_value=False):
            expected = values(sample(expected_fixture))
        fixture, changed = prepared(), []
        sim = fixture[0]
        def mutate(kind):
            if kind == "recording_static_body_shared_orientation" and not changed:
                changed.append("narrowed")
                sim.work.max_operand_bits = 32767
            elif changed == ["narrowed"]:
                changed.append("restored")
                sim.work.max_operand_bits = 32768
        with callbacks(sim.work, mutate):
            actual = values(sample(fixture))
        self.assertEqual(changed, ["narrowed", "restored"])
        self.assertEqual(actual, expected)
        self.assertEqual(sim.work.counts.get("recording_static_body_shared_orientation", 0), 1)
        self.assert_accounted(sim.work)

    def test_changed_representative_is_discarded_before_a_restoring_callback(self):
        expected_fixture = prepared()
        with patch.object(runtime, "_share_static_recording_rotations", return_value=False):
            expected = values(sample(expected_fixture))
        fixture, changed, saved = prepared(), [], []
        sim = fixture[0]
        def mutate(kind):
            if kind == "recording_static_body_shared_orientation" and not changed:
                rotation = representative(sim.work)
                saved.append((rotation, rotation.error_rad))
                object.__setattr__(rotation, "error_rad", F(1, 2))
                changed.append("mutated")
            elif changed == ["mutated"]:
                object.__setattr__(saved[0][0], "error_rad", saved[0][1])
                changed.append("restored")
        with callbacks(sim.work, mutate):
            actual = values(sample(fixture))
        self.assertEqual(changed, ["mutated", "restored"])
        self.assertEqual(actual, expected)
        self.assertEqual(sim.work.counts.get("recording_static_body_shared_orientation", 0), 1)

    def test_a_mutated_phase_clock_cannot_change_a_structural_dictionary_key(self):
        expected_fixture = prepared()
        with patch.object(runtime, "_share_static_recording_rotations", return_value=False):
            expected = values(sample(expected_fixture))
        fixture, changed = prepared(), []
        sim, _, proof, _ = fixture
        numerator = proof.start.numerator
        def mutate(kind):
            if kind == "recording_static_body_shared_orientation" and not changed:
                object.__setattr__(proof.start, "_numerator", numerator + 1)
                changed.append("mutated")
            elif changed == ["mutated"]:
                object.__setattr__(proof.start, "_numerator", numerator)
                changed.append("restored")
        try:
            with callbacks(sim.work, mutate):
                actual = values(sample(fixture))
        finally:
            object.__setattr__(proof.start, "_numerator", numerator)
        self.assertEqual(changed, ["mutated", "restored"])
        self.assertEqual(actual, expected)
        self.assertEqual(sim.work.counts.get("recording_static_body_shared_orientation", 0), 1)

    def test_later_origin_callback_cannot_publish_a_changed_representative(self):
        expected_fixture = prepared()
        with patch.object(runtime, "_share_static_recording_rotations", return_value=False):
            expected = values(sample(expected_fixture))
        fixture, stage, saved = prepared(), [], []
        sim = fixture[0]
        def mutate(kind):
            if kind == "recording_static_body_shared_orientation" and not stage:
                stage.append("borrowed")
            elif kind == "pose_grid_check" and stage == ["borrowed"]:
                rotation = representative(sim.work)
                saved.append((rotation, rotation.frozen_projection))
                object.__setattr__(rotation, "frozen_projection", (0.0, 0.0, 0.0, 1.0))
                stage.append("mutated")
            elif kind == "recording_body_phase_guard" and len(stage) == 2:
                object.__setattr__(saved[0][0], "frozen_projection", saved[0][1])
                stage.append("restored")
        with callbacks(sim.work, mutate):
            actual = values(sample(fixture))
        self.assertEqual(stage, ["borrowed", "mutated", "restored"])
        self.assertEqual(actual, expected)
        self.assertEqual(sim.work.counts.get("recording_static_body_shared_orientation", 0), 1)

    def test_changed_proof_record_identity_declines_the_structural_index(self):
        fixture = prepared()
        sim, paths, proof, context = fixture
        backing = dict(proof.frames)
        fixture = (sim, paths, replace(proof, frames=MappingProxyType(backing)), context)
        changed = []
        def mutate(kind):
            if kind == "recording_static_body_shared_orientation" and not changed:
                changed.append(True)
                key = 'rig.arms["part-01"].upper.frame'
                backing[key] = replace(backing[key])
        with callbacks(sim.work, mutate):
            actual = values(sample(fixture))
        baseline = prepared()
        with patch.object(runtime, "_share_static_recording_rotations", return_value=False):
            expected = values(sample(baseline))
        self.assertTrue(changed)
        self.assertEqual(actual, expected)
        self.assertEqual(sim.work.counts.get("recording_static_body_shared_orientation", 0), 1)

    def test_bool_aliased_frozen_scalar_retains_the_original_decoder_refusal(self):
        def change(sim):
            sim.state.coordinates['rig.arms["first"].shoulder'] = F(0)
        failures = []
        for enabled in (False, True):
            sim, paths, proof, context = prepared(change=change)
            backing = dict(proof.frames)
            key = 'rig.arms["first"].upper.frame'
            record = backing[key]
            witness = list(record.witness)
            self.assertEqual(witness[10], ("rational", 0, 1))
            witness[10] = ("rational", False, 1)
            backing[key] = replace(record, witness=tuple(witness))
            fixture = sim, paths, replace(proof, frames=MappingProxyType(backing)), context
            with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                with self.assertRaises(ReachAdmissionError) as caught:
                    sample(fixture)
            failures.append((caught.exception.reach_code, str(caught.exception), caught.exception.details))
        self.assertEqual(failures[0], failures[1])

    def test_transient_live_proof_mutation_cannot_contaminate_the_detached_seed(self):
        expected = values(sample(prepared()))
        outcomes = []
        for enabled in (False, True):
            fixture = prepared()
            sim, paths, proof, context = fixture
            backing = dict(proof.frames)
            fixture = (sim, paths, replace(proof, frames=MappingProxyType(backing)), context)
            key = 'rig.arms["first"].upper.frame'
            saved, changed = backing[key], []
            witness = list(saved.witness)
            witness[10] = ("rational", 1, 4)
            def mutate(kind):
                if kind == "recording_body_seed_domain" and not changed:
                    backing[key] = replace(saved, witness=tuple(witness))
                    changed.append("mutated")
                elif kind == "recording_body_seed_decode" and changed == ["mutated"]:
                    backing[key] = saved
                    changed.append("restored")
            with nullcontext() if enabled else patch.object(runtime, "_share_static_recording_rotations", return_value=False):
                with callbacks(sim.work, mutate):
                    outcomes.append(values(sample(fixture)))
            self.assertEqual(changed, ["mutated", "restored"])
        # The negative control demonstrates the exact old live-read window;
        # the detached source copy must preserve the clean actual graph.
        self.assertNotEqual(outcomes[0], expected)
        self.assertEqual(outcomes[1], expected)

    def test_cancellation_at_the_shared_guard_keeps_the_original_exception(self):
        fixture = prepared()
        sim, marker = fixture[0], RuntimeError("cancel the actual static recording")
        def cancel(kind):
            if kind == "recording_static_body_shared_orientation":
                raise marker
        with callbacks(sim.work, cancel), self.assertRaises(RuntimeError) as caught:
            sample(fixture)
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)

    def test_reentrant_request_keeps_the_current_graph_representative_local(self):
        expected_fixture = prepared()
        expected = values(sample(expected_fixture))
        fixture, entered, inner = prepared(), [], []
        sim, paths, proof, _ = fixture
        def reenter(kind):
            if kind == "recording_static_body_shared_orientation" and not entered:
                entered.append(True)
                inner.append(values(sample((sim, paths, proof, object()))))
        with callbacks(sim.work, reenter):
            actual = values(sample(fixture))
        self.assertTrue(entered)
        self.assertEqual(actual, expected)
        self.assertEqual(inner, [expected])
        self.assert_accounted(sim.work)


if __name__ == "__main__":
    unittest.main()
