"""A complete independent angular increment can share a cursor cache slot."""
from contextlib import nullcontext
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import MAX_CACHE, ReferenceError, _PoseArithmetic
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_world_recording import arithmetic, cursors, point, quaternion_at, reference_case


def sample(ops, context, clock, *, axis=2, rate=F(1), witness=("independent curve",),
           direct=None, **kwargs):
    direct = direct or (lambda: quaternion_at(ops, axis, rate, clock))
    return ops._recording_body_orientation(direct, axis=axis, rate=rate, witness=witness,
                                           context=context, clock=clock, **kwargs)


def warmed():
    ops, context = arithmetic(), object()
    sample(ops, context, F(0))
    sample(ops, context, F(1, 8))
    return ops, context


class IndependentRepeatedIncrementTests(unittest.TestCase):
    def test_every_axis_and_signed_rate_keeps_the_original_outward_cells(self):
        for axis, rate in ((0, F(7, 5)), (1, F(-9, 7)), (2, F(11, 8))):
            actual_ops, previous_ops = arithmetic(), arithmetic()
            actual_context, previous_context = object(), object()
            # Cross the existing 64-advance reseed and then change the step.
            clocks = [F(index, 128) for index in range(68)]
            clocks.extend((F(69, 128), F(71, 128), F(73, 128)))
            for clock in clocks:
                actual = sample(actual_ops, actual_context, clock, axis=axis, rate=rate)
                with patch.object(previous_ops, "_recording_repeated_increment", return_value=None):
                    previous = sample(previous_ops, previous_context, clock, axis=axis, rate=rate)
                with self.subTest(axis=axis, rate=rate, clock=clock):
                    self.assertEqual(actual, previous)
                    self.assertLessEqual(len(actual_ops.a.cache), MAX_CACHE)
            self.assertLess(actual_ops.a.work.operations, previous_ops.a.work.operations)
            self.assertEqual(actual_ops.a.work.operations, sum(actual_ops.a.work.counts.values()))
            self.assertEqual(actual_ops.a.work.max_operations, 100000)

    def test_a_repeated_step_omits_the_completed_transcendental_lookup(self):
        ops, context = warmed()
        key = ops._key("recording_body_orientation", context)
        receipt = ops.a.cache[key][-2]
        before = ops.a.work.operations
        with patch.object(ops.a, "sincos", side_effect=AssertionError("completed independent increment")):
            actual = sample(ops, context, F(1, 4))
        self.assertIs(ops.a.cache[key][-2], receipt)
        previous_ops, previous_context = warmed()
        previous_before = previous_ops.a.work.operations
        with patch.object(previous_ops, "_recording_repeated_increment", return_value=None):
            previous = sample(previous_ops, previous_context, F(1, 4))
        self.assertEqual(actual, previous)
        self.assertEqual((previous_ops.a.work.operations - previous_before) -
                         (ops.a.work.operations - before), 4)

    def test_different_elapsed_values_execute_and_retain_their_own_exact_increment(self):
        ops, context = warmed()
        key = ops._key("recording_body_orientation", context)
        before = ops.a.cache[key][-2]
        with patch.object(ops.a, "sincos", wraps=ops.a.sincos) as sincos:
            sample(ops, context, F(3, 8))
        sincos.assert_called_once()
        self.assertNotEqual(ops.a.cache[key][-2], before)
        self.assertEqual(ops.a.cache[key][-2][1], F(1, 4))
        with patch.object(ops.a, "sincos", side_effect=AssertionError("new step was retained")):
            sample(ops, context, F(5, 8))

    def test_changed_context_rate_axis_witness_or_clock_reseeds_without_a_step_receipt(self):
        for changed in ("context", "rate", "axis", "witness", "rewind", "same_clock", "large_step"):
            ops, context = warmed()
            kwargs, clock = {}, F(1, 4)
            if changed == "context":
                context = object()
            elif changed == "rate":
                kwargs["rate"] = F(2)
            elif changed == "axis":
                kwargs["axis"] = 0
            elif changed == "witness":
                kwargs["witness"] = ("a new independently admitted source curve",)
            elif changed == "rewind":
                clock = F(1, 16)
            elif changed == "same_clock":
                clock = F(1, 8)
            else:
                clock = F(1)
            direct_value, calls = tuple(map(point, (0, 0, 0, 1))), []
            def direct():
                calls.append(True)
                return direct_value
            with self.subTest(changed=changed):
                self.assertIs(sample(ops, context, clock, direct=direct, **kwargs), direct_value)
                self.assertEqual(calls, [True])
                value = ops.a.cache[ops._key("recording_body_orientation", context)]
                self.assertIsNone(value[-2])
                self.assertEqual(value[-1], 0)

    def test_native_typed_complete_operands_are_required_for_reuse(self):
        ops, context = warmed()
        receipt = ops.a.cache[ops._key("recording_body_orientation", context)][-2]
        expected = ops._recording_repeated_increment(receipt, F(1), F(1, 8))
        self.assertIsNotNone(expected)
        for candidate, rate, elapsed in ((receipt, F(-1), F(1, 8)),
                                          (receipt, F(1), F(1, 4)),
                                          (receipt, 1., F(1, 8)),
                                          (receipt, F(1), 0.125),
                                          (list(receipt), F(1), F(1, 8)),
                                          (receipt[:-1], F(1), F(1, 8)),
                                          ((1., *receipt[1:]), F(1), F(1, 8))):
            with self.subTest(rate=rate, elapsed=elapsed, receipt=type(candidate).__name__):
                self.assertIsNone(ops._recording_repeated_increment(candidate, rate, elapsed))
        ops.a.work.max_operand_bits = 32767
        self.assertIsNone(ops._recording_repeated_increment(receipt, F(1), F(1, 8)))

    def test_narrowing_at_every_warm_callback_uses_the_current_direct_domain(self):
        count_ops, count_context = warmed()
        start = count_ops.a.work.operations
        sample(count_ops, count_context, F(1, 4))
        callbacks = count_ops.a.work.operations - start
        for fail_at in range(1, callbacks + 1):
            ops, context = warmed()
            key = ops._key("recording_body_orientation", context)
            before, calls, direct_calls = ops.a.cache[key], 0, []
            fresh = tuple(map(point, (0, 0, 0, 1)))
            def narrow():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    ops.a.work.max_operand_bits = 32767
            def direct():
                direct_calls.append(ops.a.operand_limit)
                return fresh
            with self.subTest(fail_at=fail_at), patch.object(ops.a.work, "external_check", side_effect=narrow):
                self.assertIs(sample(ops, context, F(1, 4), direct=direct), fresh)
            self.assertEqual(direct_calls, [32767])
            self.assertEqual(ops.a.cache.get(key, before), before)

    def test_cancellation_at_every_warm_callback_keeps_the_existing_cursor(self):
        count_ops, count_context = warmed()
        start = count_ops.a.work.operations
        sample(count_ops, count_context, F(1, 4))
        callbacks = count_ops.a.work.operations - start
        for fail_at in range(1, callbacks + 1):
            for marker in (RuntimeError("cancel repeated independent step"),
                           ReferenceError("resource", "caller owns this refusal")):
                ops, context = warmed()
                key = ops._key("recording_body_orientation", context)
                before, calls = ops.a.cache[key], 0
                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise marker
                with self.subTest(fail_at=fail_at, error=type(marker).__name__), \
                        patch.object(ops.a.work, "external_check", side_effect=cancel), \
                        self.assertRaises(type(marker)) as caught:
                    sample(ops, context, F(1, 4))
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.a.work.callback_error, marker)
                self.assertEqual(ops.a.cache[key], before)

    def test_a_repeated_increment_keeps_the_original_interval_failure_identity(self):
        ops, context = warmed()
        key = ops._key("recording_body_orientation", context)
        before = ops.a.cache[key]
        rotate, multiply = ops._recording_rotate_sincos, ops.a.mul
        armed, failures, broadened = False, [], []
        def change_domain():
            if armed:
                if failures:
                    broadened.append(True)
                    ops.a.work.max_operand_bits = 32768
                else:
                    ops.a.work.max_operand_bits = 64
        def enter_rotation(*values, **kwargs):
            nonlocal armed
            armed = True
            return rotate(*values, **kwargs)
        def observe_original(a, b):
            try:
                return multiply(a, b)
            except ReferenceError as error:
                failures.append(error)
                raise
        with patch.object(ops.a.work, "external_check", side_effect=change_domain), \
                patch.object(ops, "_recording_rotate_sincos", side_effect=enter_rotation), \
                patch.object(ops.a, "mul", side_effect=observe_original), self.assertRaises(ReferenceError) as caught:
            sample(ops, context, F(1, 4))
        self.assertEqual(len(failures), 1)
        self.assertIs(caught.exception, failures[0])
        self.assertFalse(broadened)
        self.assertEqual(ops.a.cache[key], before)

    def test_fresh_source_admission_still_rejects_before_cursor_publication(self):
        ops, context = warmed()
        key = ops._key("recording_body_orientation", context)
        before, admissions = ops.a.cache[key], []
        marker = ReferenceError("identity", "independent source changed during its repeated step")
        def reject():
            admissions.append(True)
            raise marker
        with self.assertRaises(ReferenceError) as caught:
            sample(ops, context, F(1, 4), source_admission=reject, source_records=3)
        self.assertIs(caught.exception, marker)
        self.assertEqual(admissions, [True])
        self.assertEqual(ops.a.cache[key], before)

    def test_source_mutation_at_a_warm_step_publication_cannot_change_its_witness(self):
        reference, _ = reference_case("P09", F(1))
        context, carrier = object(), "rig.arm.forearm.frame"
        for clock in (F(1, 8), F(1, 4)):
            reference.recording_pose_enclosures((carrier,), clock, recording_context=context)
        key = next(key for key in cursors(reference.p) if key[-1][-1] == carrier)
        previous = reference.a.cache[key]
        self.assertIsNotNone(previous[-2])
        joint = reference.model.joints[reference.model.actions["reach"].reach.elbow]
        original_axis, changed, remember = joint.axis, [], reference.a.remember
        def mutate():
            changed.append(True)
            joint.axis = (0., 0., -1.)
            reference.a.work.external_check = None
        def publish(candidate, value, **kwargs):
            if candidate == key:
                reference.a.work.external_check = mutate
            return remember(candidate, value, **kwargs)
        try:
            with patch.object(reference.a, "remember", side_effect=publish), \
                    self.assertRaises(ReferenceError) as caught:
                reference.recording_pose_enclosures((carrier,), F(3, 8), recording_context=context)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(changed, [True])
            self.assertEqual(reference.a.cache[key], previous)
        finally:
            joint.axis = original_axis
            reference.a.work.external_check = None

    def test_eviction_discards_the_receipt_with_its_existing_bounded_cursor_slot(self):
        ops, context = warmed()
        self.assertEqual(len(cursors(ops)), 1)
        for index in range(MAX_CACHE + 1):
            ops.a.remember(("unrelated immutable result", index), F(index))
        self.assertEqual(len(ops.a.cache), MAX_CACHE)
        self.assertFalse(cursors(ops))
        with patch.object(ops, "_recording_repeated_increment", side_effect=AssertionError("evicted step")):
            sample(ops, context, F(1, 4))
        entry = ops.a.cache[ops._key("recording_body_orientation", context)]
        self.assertIsNone(entry[-2])
        self.assertEqual(entry[-1], 0)
        self.assertEqual(len(ops.a.cache), MAX_CACHE)

    def test_actual_glb_bytes_and_independent_validation_remain_identical(self):
        for case in ("P05", "P09"):
            outcomes = []
            for optimized in (False, True):
                compiler = compile_construction(source_case(case))
                manager = (nullcontext() if optimized else
                           patch.object(_PoseArithmetic, "_recording_repeated_increment", return_value=None))
                with manager:
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 2), fps=8, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                outcomes.append((result.data, result.report["validation"], compiler.budget.operations))
            self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            self.assertLess(outcomes[1][2], outcomes[0][2])


if __name__ == "__main__":
    unittest.main()
