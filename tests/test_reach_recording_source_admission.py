"""A completed carrier value is published only for its still-current source."""
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps, RotationValue
from ontokin.reach_recording_fast import Binary64RecordingOps
from test_reach_recording_body_cursor import arguments
from test_reach_recording_captured_seed import PATHS, prepared


def cache_identity(work):
    return tuple((key, id(value)) for key, value in work._cache.items())


def body_key(key):
    return "body" in key or "certified_binary64_body" in key


class ReachRecordingSourceAdmissionTests(unittest.TestCase):
    def test_cache_admission_follows_all_callbacks_and_precedes_every_mutation(self):
        for final in ("cache_insert", "cache_promote", "cache_evict"):
            for refusal in (False, RuntimeError("reject this completed receipt")):
                with self.subTest(final=final, exception=bool(refusal)):
                    work = ReachExecutionWork(max_cache_entries=2)
                    old = object()
                    if final != "cache_insert":
                        work.remember(("old",), old)
                    if final == "cache_evict":
                        work.remember(("other",), object())
                    key = ("old",) if final == "cache_promote" else ("new",)
                    before, generation = cache_identity(work), work._cache_generation
                    events, charge = [], work.charge
                    def charged(kind="checkpoint", amount=1):
                        events.append(kind)
                        return charge(kind, amount)
                    def admission():
                        events.append("admission")
                        self.assertEqual(cache_identity(work), before)
                        self.assertEqual(work._cache_generation, generation)
                        if refusal:
                            raise refusal
                        return False
                    with patch.object(work, "charge", side_effect=charged):
                        if refusal:
                            with self.assertRaises(RuntimeError) as caught:
                                work.remember(key, object(), admission=admission)
                            self.assertIs(caught.exception, refusal)
                        else:
                            self.assertIs(work.remember(key, object(), admission=admission), False)
                    self.assertEqual(events[-2:], [final, "admission"])
                    self.assertEqual(cache_identity(work), before)
                    self.assertEqual(work._cache_generation, generation)

    def test_successful_admission_is_the_last_check_before_publication(self):
        work = ReachExecutionWork(max_cache_entries=1)
        old, new = object(), object()
        self.assertIsNone(work.remember(("old",), old))
        events = []
        work.external_check = lambda: events.append("callback")
        def admission():
            events.append("admission")
            self.assertIs(work._cache[("old",)], old)
            return True
        self.assertIs(work.remember(("new",), new, admission=admission), True)
        self.assertEqual(events, ["callback", "callback", "admission"])
        self.assertEqual(tuple(work._cache), (("new",),))
        self.assertIs(work._cache[("new",)], new)

    def test_reentrant_or_changed_cap_admission_cannot_overwrite_completed_work(self):
        for change in ("generation", "cap"):
            with self.subTest(change=change):
                work = ReachExecutionWork(max_cache_entries=2)
                old, inner = object(), object()
                work.remember(("old",), old)
                def admission():
                    if change == "generation":
                        work.remember(("inner",), inner)
                    else:
                        work.max_operand_bits = 128
                    return True
                self.assertIs(work.remember(("pending",), object(), admission=admission), False)
                self.assertIs(work._cache[("old",)], old)
                self.assertNotIn(("pending",), work._cache)
                if change == "generation":
                    self.assertIs(work._cache[("inner",)], inner)
                else:
                    self.assertEqual(tuple(work._cache), (("old",),))

    def test_original_seed_and_admission_failures_keep_identity_across_cap_changes(self):
        for native in (False, True):
            for origin in ("seed", "admission"):
                with self.subTest(native=native, origin=origin):
                    source = ReachPoseOps(ReachExecutionWork())
                    ops = Binary64RecordingOps(source, body_cursors=True) if native else source
                    failures, calls = [], []
                    unit = RotationValue((F(1), F(0), F(0), F(0)))
                    def original_failure():
                        calls.append(origin)
                        if len(calls) > 1:
                            source.work.max_operand_bits = MAX_OPERAND_BITS
                            return
                        source.work.max_operand_bits = 128
                        try:
                            # This is the original exact source refusal, not
                            # a synthetic cursor guard with the same code.
                            source.axis_rotation((0, 0, 1), F(1, 4))
                        except ReachAdmissionError as error:
                            failures.append(error)
                            raise
                        self.fail("the ordinary source kernel must reject this cap")
                    def seed():
                        if origin == "seed":
                            original_failure()
                        return unit
                    def admission():
                        if origin == "admission":
                            original_failure()
                        return True
                    with self.assertRaises(ReachAdmissionError) as caught:
                        ops.recording_body_orientation(seed, None, F(0), F(0),
                            source_admission=admission, source_records=1, **arguments())
                    self.assertEqual(calls, [origin])
                    self.assertEqual(len(failures), 1)
                    self.assertIs(caught.exception, failures[0])
                    self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                    self.assertFalse(any(body_key(key) for key in source.work._cache))

    def test_exact_cursor_rejects_malformed_callbacks_before_invoking_them(self):
        for seed, admission, records in (
                (1, None, 0), (lambda: None, 1, 1),
                (lambda: None, None, 1), (lambda: None, lambda: True, True),
                (lambda: None, lambda: True, -1)):
            with self.subTest(seed=seed, admission=admission, records=records):
                ops = ReachPoseOps(ReachExecutionWork())
                with self.assertRaises(ReachAdmissionError) as caught:
                    ops.recording_body_orientation(seed, None, F(0), F(0),
                        source_admission=admission, source_records=records, **arguments())
                self.assertEqual(caught.exception.reach_code, "reach_domain")

    def test_persistent_source_changes_at_final_cache_callbacks_preserve_old_cursor_and_order(self):
        for native in (False, True):
            for final in ("cache_insert", "cache_promote", "cache_evict"):
                with self.subTest(native=native, final=final):
                    self._persistent_change(native, final, replace_state=False)

    def test_replacing_the_root_state_at_publication_invalidates_identical_source_values(self):
        for native in (False, True):
            with self.subTest(native=native):
                self._persistent_change(native, "cache_insert", replace_state=True)

    def _persistent_change(self, native, final, *, replace_state):
        sim, phase = prepared()
        work, context = sim.work, object()
        state = sim.state
        active = state.actions[state.claims[("rig.arm.shoulder", "coordinate")]]
        initial = active.initial
        ops = Binary64RecordingOps(sim.pose_ops, body_cursors=True) if native else None
        def sample(time):
            return sim._resolve_kinematics(time, state, selected_frames=PATHS[:1],
                pose_only=True, recording_only=True, recording_context=context,
                recording_pose_ops=ops, recording_angular_proof=phase["recording_angular_proof"])
        if final == "cache_promote":
            sample(F(1, 8))
        remember, charge, prior_check = work.remember, work.charge, work.external_check
        saved, changed = [], []
        def publish(key, value, *, admission=None):
            if not body_key(key):
                return remember(key, value, admission=admission)
            self.assertFalse(saved)
            self.assertIsNotNone(admission)
            if final == "cache_promote":
                self.assertIn(key, work._cache)
            else:
                self.assertNotIn(key, work._cache)
            if final == "cache_evict":
                for index in range(work.max_cache_entries - len(work._cache)):
                    remember(("admission eviction filler", index), object())
                self.assertEqual(len(work._cache), work.max_cache_entries)
            saved.append((cache_identity(work), work._cache_generation))
            def mutate():
                if prior_check is not None:
                    prior_check()
                if not changed:
                    if replace_state:
                        sim.state = deepcopy(state)
                    else:
                        active.initial = (initial[0] + 0.25, initial[1])
                    changed.append(final)
            def charged(kind="checkpoint", amount=1):
                if kind == final:
                    work.external_check = mutate
                return charge(kind, amount)
            def final_admission():
                # Earlier ancestor checks cannot be invalidated by a later
                # callback inside this final whole-chain comparison.
                with patch.object(work, "charge", side_effect=AssertionError("callback after final admission")):
                    return admission()
            try:
                with patch.object(work, "charge", side_effect=charged):
                    return remember(key, value, admission=final_admission)
            finally:
                work.external_check = prior_check
        try:
            with patch.object(work, "remember", side_effect=publish):
                with self.assertRaises(ReachAdmissionError) as caught:
                    sample(F(1, 4))
            self.assertEqual(caught.exception.reach_code, "reach_domain")
            self.assertEqual(changed, [final])
            self.assertEqual(len(saved), 1)
            self.assertEqual(cache_identity(work), saved[0][0])
            self.assertEqual(work._cache_generation, saved[0][1])
            self.assertLessEqual(len(work._cache), 256)
        finally:
            active.initial, sim.state, work.external_check = initial, state, prior_check


if __name__ == "__main__":
    unittest.main()
