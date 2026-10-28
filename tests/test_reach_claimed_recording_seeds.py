"""Equal cold source seeds preserve each claimed body's own cursor history."""
from contextlib import nullcontext
from dataclasses import replace
from fractions import Fraction as F
from types import MappingProxyType
import unittest
from unittest.mock import patch

from ontokin import reach_runtime as runtime
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_pose import ReachPoseOps, RotationValue
from test_reach_static_recording_rotations import (
    callbacks, prepared as static_prepared, representative, sample, values,
)


def prepared(*, start=F(0), end=F(2), **changes):
    return static_prepared(start=start, end=end, **changes)


def sharing(enabled):
    return nullcontext() if enabled else patch.object(
        runtime, "_share_claimed_recording_seeds", return_value=False)


def body_cursors(work):
    return {key[4]: value for key, value in work._cache.items()
            if len(key) > 4 and key[1:3] == ("recording_rotation_cursor", "body")}


class ClaimedRecordingSeedTests(unittest.TestCase):
    def assert_accounted(self, work):
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.max_cache_entries, 256)
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertLessEqual(len(work._cache), work.max_cache_entries)

    def test_original_p23_initial_graph_keeps_exact_values_and_every_body_cursor(self):
        outcomes = []
        for enabled in (False, True):
            fixture = prepared(count=None)
            sim = fixture[0]
            before, counts = sim.work.operations, dict(sim.work.counts)
            with sharing(enabled):
                actual = values(sample(fixture, F(0)))
            delta = {key: value - counts.get(key, 0) for key, value in sim.work.counts.items()}
            outcomes.append((actual, sim.work.operations - before, delta))
            self.assert_accounted(sim.work)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])
        for kind in ("recording_body_phase_guard", "recording_body_direct_seed"):
            self.assertEqual(outcomes[0][2].get(kind, 0), outcomes[1][2].get(kind, 0))
        self.assertGreater(outcomes[1][2].get("recording_claimed_shared_seed", 0), 0)
        self.assertLess(outcomes[1][2].get("recording_body_seed_domain", 0),
                        outcomes[0][2].get("recording_body_seed_domain", 0))
        self.assertEqual(outcomes[1][2].get("recording_static_body_shared_orientation", 0), 0)
        print(f"P23 initial exact graph: ordinary={outcomes[0][1]}, shared={outcomes[1][1]}, "
              f"saved={outcomes[0][1] - outcomes[1][1]}; "
              f"body cursors={outcomes[1][2].get('recording_body_direct_seed', 0)}; "
              f"decoded seeds={outcomes[0][2].get('recording_body_seed_domain', 0)}"
              f"->{outcomes[1][2].get('recording_body_seed_domain', 0)}")

    def test_nonzero_cold_clock_preserves_private_errors_frozen_bits_and_fresh_wrappers(self):
        def change(sim):
            sim.state.positions["rig"] = (0.125, -0.0, -0.25)
            sim.state.root_rotation_values["rig"] = RotationValue(
                (F(1), F(0), F(0), F(0)), F(1, 1 << 90), (1.0, -0.0, 0.0, -0.0))
        outcomes = []
        for enabled in (False, True):
            fixture = prepared(change=change)
            with sharing(enabled):
                frames = sample(fixture, F(1, 8))
                outcomes.append(values(frames))
            if enabled:
                first = frames['rig.arms["first"].forearm.frame'].rotation
                second = frames['rig.arms["part-01"].forearm.frame'].rotation
                self.assertEqual(first, second)
                self.assertIsNot(first, second)
                for left, right in zip((*first.components, first.error_rad),
                                       (*second.components, second.error_rad)):
                    self.assertIsNot(left, right)
                self.assertGreater(fixture[0].work.counts.get("recording_claimed_shared_seed", 0), 0)
            self.assert_accounted(fixture[0].work)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_warm_repeated_and_out_of_order_clocks_keep_each_original_cursor(self):
        outcomes = []
        for enabled in (False, True):
            fixture = prepared()
            sim, captured = fixture[0], []
            with sharing(enabled):
                for clock in (F(0), F(1, 8), F(1, 4), F(1, 4), F(3, 16)):
                    captured.append((values(sample(fixture, clock)), body_cursors(sim.work)))
            outcomes.append(captured)
            cursors = body_cursors(sim.work)
            self.assertEqual(len(cursors), 6)
            self.assertTrue(all(value[2] == 5 for value in cursors.values()))
            self.assertEqual(sim.work.counts.get("recording_body_direct_seed", 0), 6)
            self.assert_accounted(sim.work)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_warm_representative_cannot_supply_another_bodys_cold_seed(self):
        outcomes = []
        for enabled in (False, True):
            fixture = prepared()
            sim, paths, proof, context = fixture
            with sharing(enabled):
                sample((sim, paths[:3], proof, context), F(1, 8))
                actual = values(sample(fixture, F(1, 4)))
            outcomes.append((actual, body_cursors(sim.work)))
            self.assertEqual(body_cursors(sim.work)['carrier:rig.arms["first"].forearm'][2], 2)
            self.assertEqual(body_cursors(sim.work)['carrier:rig.arms["part-01"].forearm'][2], 1)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_different_duration_and_elapsed_laws_remain_distinct(self):
        for changed in ("duration", "elapsed"):
            def change(sim):
                path = 'rig.arms["part-01"].shoulder'
                claimant = sim.state.claims[(path, "coordinate")]
                if changed == "duration":
                    action = sim.model.actions[claimant]
                    sim.model.actions[claimant] = replace(action, duration=F(4))
                else:
                    sim.state.actions[claimant].elapsed = F(1, 8)
            outcomes = []
            for enabled in (False, True):
                fixture = prepared(change=change, end=F(1))
                with sharing(enabled):
                    frames = sample(fixture, F(1, 2))
                    outcomes.append(values(frames))
                self.assertNotEqual(frames['rig.arms["first"].forearm.frame'].rotation,
                                    frames['rig.arms["part-01"].forearm.frame'].rotation)
            with self.subTest(changed=changed):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_small_graph_root_claim_dynamic_and_foreign_dispatch_decline(self):
        sim = prepared()[0]
        self.assertTrue(runtime._share_claimed_recording_seeds(sim.state, sim.pose_ops))
        original_claims, original_dynamic = sim.state.claims, sim.state.dynamic
        variants = (dict(tuple(original_claims.items())[:15]),
                    {**original_claims, ("rig", "orientation"): "turn"},
                    {**original_claims, ("rig", "translation"): "travel"},
                    {**original_claims, ("rig", "coordinate"): 1})
        for claims in variants:
            sim.state.claims = claims
            self.assertFalse(runtime._share_claimed_recording_seeds(sim.state, sim.pose_ops))
        sim.state.claims = original_claims
        sim.state.dynamic = {"rig": object()}
        self.assertFalse(runtime._share_claimed_recording_seeds(sim.state, sim.pose_ops))
        sim.state.dynamic = original_dynamic
        class OtherOps(ReachPoseOps):
            pass
        self.assertFalse(runtime._share_claimed_recording_seeds(sim.state, OtherOps(sim.work)))
        with patch.object(sim.pose_ops, "recording_body_orientation", wraps=sim.pose_ops.recording_body_orientation):
            self.assertFalse(runtime._share_claimed_recording_seeds(sim.state, sim.pose_ops))
        native, reads = ReachPoseOps.recording_body_orientation, []
        class Descriptor:
            def __get__(self, instance, owner):
                reads.append(instance)
                return native
        with patch.object(ReachPoseOps, "recording_body_orientation", new=Descriptor()):
            self.assertFalse(runtime._share_claimed_recording_seeds(sim.state, sim.pose_ops))
        self.assertEqual(reads, [])

    def test_strict_full_source_and_lowered_cap_keep_the_original_work(self):
        for setting in ("source", "strict", "cap"):
            outcomes = []
            for enabled in (False, True):
                fixture = prepared()
                sim = fixture[0]
                if setting == "cap":
                    sim.work.max_operand_bits = 32767
                before = sim.work.operations
                with sharing(enabled):
                    actual = values(sample(fixture, F(0), recording=setting != "source",
                                           incremental=setting == "cap"))
                outcomes.append((actual, sim.work.operations - before))
                self.assertEqual(sim.work.counts.get("recording_claimed_shared_seed", 0), 0)
            with self.subTest(setting=setting):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_narrowed_then_restored_domain_does_not_revive_shared_seeds(self):
        expected_fixture = prepared()
        with sharing(False):
            expected = values(sample(expected_fixture, F(0)))
        fixture, changed = prepared(), []
        sim = fixture[0]
        def mutate(kind):
            if kind == "recording_claimed_shared_seed" and not changed:
                sim.work.max_operand_bits = 32767
                changed.append("narrowed")
            elif changed == ["narrowed"]:
                sim.work.max_operand_bits = 32768
                changed.append("restored")
        with callbacks(sim.work, mutate):
            actual = values(sample(fixture, F(0)))
        self.assertEqual(actual, expected)
        self.assertEqual(changed, ["narrowed", "restored"])
        self.assertEqual(sim.work.counts.get("recording_claimed_shared_seed", 0), 1)

    def test_changed_representative_is_rejected_before_restoration(self):
        expected_fixture = prepared()
        with sharing(False):
            expected = values(sample(expected_fixture, F(0)))
        fixture, changed, saved = prepared(), [], []
        sim = fixture[0]
        def mutate(kind):
            if kind == "recording_claimed_shared_seed" and not changed:
                rotation = representative(sim.work)
                saved.append((rotation, rotation.error_rad))
                object.__setattr__(rotation, "error_rad", F(1, 2))
                changed.append("mutated")
            elif changed == ["mutated"]:
                object.__setattr__(saved[0][0], "error_rad", saved[0][1])
                changed.append("restored")
        with callbacks(sim.work, mutate):
            actual = values(sample(fixture, F(0)))
        self.assertEqual(actual, expected)
        self.assertEqual(changed, ["mutated", "restored"])
        self.assertEqual(sim.work.counts.get("recording_claimed_shared_seed", 0), 1)

    def test_late_origin_callback_rechecks_the_borrowed_seed(self):
        expected_fixture = prepared()
        with sharing(False):
            expected = values(sample(expected_fixture, F(0)))
        fixture, stages, saved = prepared(), [], []
        sim = fixture[0]
        def mutate(kind):
            if kind == "recording_claimed_shared_seed" and not stages:
                stages.append("borrowed")
            elif kind == "pose_grid_check" and stages == ["borrowed"]:
                rotation = representative(sim.work)
                saved.append((rotation, rotation.frozen_projection))
                object.__setattr__(rotation, "frozen_projection", (0.0, 0.0, 0.0, 1.0))
                stages.append("mutated")
            elif kind == "recording_body_phase_guard" and stages == ["borrowed", "mutated"]:
                object.__setattr__(saved[0][0], "frozen_projection", saved[0][1])
                stages.append("restored")
        with callbacks(sim.work, mutate):
            actual = values(sample(fixture, F(0)))
        self.assertEqual(stages, ["borrowed", "mutated", "restored"])
        self.assertEqual(actual, expected)
        self.assertEqual(sim.work.counts.get("recording_claimed_shared_seed", 0), 1)

    def test_changed_target_source_cannot_publish_a_body_cursor(self):
        fixture, changed = prepared(), []
        sim = fixture[0]
        path = 'rig.arms["part-01"].shoulder'
        active = sim.state.actions[sim.state.claims[(path, "coordinate")]]
        def mutate(kind):
            if kind == "recording_claimed_shared_seed" and not changed:
                changed.append(True)
                active.initial = (0.25, active.initial[1])
        with callbacks(sim.work, mutate), self.assertRaises(ReachAdmissionError) as caught:
            sample(fixture, F(0))
        self.assertTrue(changed)
        self.assertEqual(caught.exception.reach_code, "reach_domain")
        self.assertIn('carrier:rig.arms["first"].upper', body_cursors(sim.work))
        self.assertNotIn('carrier:rig.arms["part-01"].upper', body_cursors(sim.work))

    def test_origin_callback_cannot_return_a_mutated_borrowed_target(self):
        for field in ("components", "error_rad", "frozen_projection"):
            fixture, stages = prepared(), []
            sim = fixture[0]
            def mutate(kind):
                if kind == "recording_claimed_shared_seed" and not stages:
                    stages.append("borrowed")
                elif kind == "pose_grid_check" and stages == ["borrowed"]:
                    target = body_cursors(sim.work)['carrier:rig.arms["part-01"].upper'][1]
                    replacement = {"components": (F(0), F(0), F(0), F(1)),
                                   "error_rad": F(1, 2),
                                   "frozen_projection": (0.0, 0.0, 0.0, 1.0)}[field]
                    object.__setattr__(target, field, replacement)
                    stages.append("mutated")
            with self.subTest(field=field), callbacks(sim.work, mutate):
                with self.assertRaises(ReachAdmissionError) as caught:
                    sample(fixture, F(0))
            self.assertEqual(stages, ["borrowed", "mutated"])
            self.assertEqual(caught.exception.reach_code, "reach_domain")
            self.assertIn("borrowed carrier seed changed", str(caught.exception))

    def test_ordinary_lazy_projection_does_not_change_the_borrowed_target_receipt(self):
        fixture, stages = prepared(), []
        sim = fixture[0]
        expected = values(sample(prepared(), F(0)))
        def expose(kind):
            if kind == "recording_claimed_shared_seed" and not stages:
                stages.append("borrowed")
            elif kind == "pose_grid_check" and stages == ["borrowed"]:
                stages.append("exposed")
                target = body_cursors(sim.work)['carrier:rig.arms["part-01"].upper'][1]
                before = target.frozen_projection
                sim.pose_ops._unit_projection(target)
                self.assertIs(target.frozen_projection, before)
        with callbacks(sim.work, expose):
            actual = values(sample(fixture, F(0)))
        self.assertEqual(stages, ["borrowed", "exposed"])
        self.assertEqual(actual, expected)

    def test_changed_phase_clock_and_proof_record_identity_decline(self):
        for changed_field in ("clock", "record"):
            expected_fixture = prepared()
            with sharing(False):
                expected = values(sample(expected_fixture, F(0)))
            fixture, changed = prepared(), []
            sim, paths, proof, context = fixture
            backing = dict(proof.frames)
            proof = replace(proof, frames=MappingProxyType(backing))
            fixture = sim, paths, proof, context
            numerator = proof.end.numerator
            def mutate(kind):
                if kind == "recording_claimed_shared_seed" and not changed:
                    if changed_field == "clock":
                        object.__setattr__(proof.end, "_numerator", numerator + 1)
                    else:
                        key = 'rig.arms["part-01"].upper.frame'
                        backing[key] = replace(backing[key])
                    changed.append("mutated")
                elif changed_field == "clock" and changed == ["mutated"]:
                    object.__setattr__(proof.end, "_numerator", numerator)
                    changed.append("restored")
            try:
                with callbacks(sim.work, mutate):
                    actual = values(sample(fixture, F(0)))
            finally:
                object.__setattr__(proof.end, "_numerator", numerator)
            with self.subTest(changed_field=changed_field):
                self.assertEqual(actual, expected)
                self.assertTrue(changed)
                self.assertEqual(sim.work.counts.get("recording_claimed_shared_seed", 0), 1)

    def test_bool_aliased_elapsed_clock_keeps_the_original_decoder_failure(self):
        failures = []
        for enabled in (False, True):
            sim, paths, proof, context = prepared()
            backing = dict(proof.frames)
            key = 'rig.arms["first"].upper.frame'
            record = backing[key]
            witness = list(record.witness)
            law = list(witness[9])
            self.assertEqual(law[11], ("rational", 0, 1))
            law[11] = ("rational", False, 1)
            witness[9] = tuple(law)
            backing[key] = replace(record, witness=tuple(witness))
            fixture = sim, paths, replace(proof, frames=MappingProxyType(backing)), context
            with sharing(enabled), self.assertRaises(ReachAdmissionError) as caught:
                sample(fixture, F(0))
            failures.append((caught.exception.reach_code, str(caught.exception), caught.exception.details))
        self.assertEqual(failures[0], failures[1])

    def test_transient_live_proof_cannot_change_the_first_detached_seed(self):
        expected = values(sample(prepared(), F(0)))
        outcomes = []
        for enabled in (False, True):
            sim, paths, proof, context = prepared()
            backing = dict(proof.frames)
            fixture = sim, paths, replace(proof, frames=MappingProxyType(backing)), context
            key = 'rig.arms["first"].upper.frame'
            saved, changed = backing[key], []
            witness = list(saved.witness)
            law = list(witness[9])
            law[8] = ("tuple", (("rational", 1, 4), law[8][1][1]))
            witness[9] = tuple(law)
            def mutate(kind):
                if kind == "recording_body_seed_domain" and not changed:
                    backing[key] = replace(saved, witness=tuple(witness))
                    changed.append("mutated")
                elif kind == "recording_body_seed_decode" and changed == ["mutated"]:
                    backing[key] = saved
                    changed.append("restored")
            with sharing(enabled), callbacks(sim.work, mutate):
                outcomes.append(values(sample(fixture, F(0))))
            self.assertEqual(changed, ["mutated", "restored"])
        self.assertNotEqual(outcomes[0], expected)
        self.assertEqual(outcomes[1], expected)

    def test_cancellation_and_reentry_keep_callback_identity_and_local_index(self):
        fixture = prepared()
        sim, marker = fixture[0], RuntimeError("cancel the actual claimed seed")
        def cancel(kind):
            if kind == "recording_claimed_shared_seed":
                raise marker
        with callbacks(sim.work, cancel), self.assertRaises(RuntimeError) as caught:
            sample(fixture, F(0))
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        fixture, entered, inner = prepared(), [], []
        sim, paths, proof, _ = fixture
        expected = values(sample(prepared(), F(0)))
        def reenter(kind):
            if kind == "recording_claimed_shared_seed" and not entered:
                entered.append(True)
                inner.append(values(sample((sim, paths, proof, object()), F(0))))
        with callbacks(sim.work, reenter):
            actual = values(sample(fixture, F(0)))
        self.assertEqual(actual, expected)
        self.assertEqual(inner, [expected])
        self.assert_accounted(sim.work)


if __name__ == "__main__":
    unittest.main()
