"""Broad recording batches share completed exact interval updates, not cursors."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_reference import Interval, MAX_CACHE, ReferenceError
from test_reach_reference_fused_recording import arithmetic, dense_values, direct, exact_expected, point


def proof_rows(ops):
    return {key: value for key, value in ops.a.cache.items()
            if key[:1] == ("reference_pose",) and key[3] == "recording_interval_rotation"}


def cursor_rows(ops):
    return {key: value for key, value in ops.a.cache.items()
            if key[:1] == ("reference_pose",) and key[3] == "recording_sincos"}


class IndependentSharedRecordingTests(unittest.TestCase):
    def test_repeated_exact_inputs_share_one_completed_interval_proof(self):
        ops, baseline, values = arithmetic(), arithmetic(), dense_values()
        first = ops._recording_rotate_sincos(*values, shared=True)
        before = ops.a.work.operations
        with patch.object(ops.a, "exact", wraps=ops.a.exact) as exact:
            following = ops._recording_rotate_sincos(*values, shared=True)
        self.assertIs(first, following)
        self.assertEqual(first, exact_expected(values))
        exact.assert_not_called()
        self.assertEqual(ops.a.work.operations - before, 2)
        baseline._recording_rotate_sincos(*values)
        baseline._recording_rotate_sincos(*values)
        self.assertLess(ops.a.work.operations, baseline.a.work.operations)
        self.assertEqual(len(proof_rows(ops)), 1)
        self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))

    def test_each_actual_interval_enters_the_complete_key(self):
        ops, values = arithmetic(), dense_values()
        ops._recording_rotate_sincos(*values, shared=True)
        for index in range(4):
            changed = list(values)
            cell, step = values[index], F(1, 1 << 128)
            changed[index] = Interval(cell.lo + step, cell.hi + step)
            with patch.object(ops.a, "exact", wraps=ops.a.exact) as exact:
                actual = ops._recording_rotate_sincos(*changed, shared=True)
            self.assertGreater(exact.call_count, 0)
            self.assertEqual(actual, exact_expected(changed))
        self.assertEqual(len(proof_rows(ops)), 5)

    def test_default_and_ineligible_calls_do_not_add_sharing_bookkeeping(self):
        values = dense_values()
        ops = arithmetic()
        self.assertEqual(ops._recording_rotate_sincos(*values), exact_expected(values))
        self.assertEqual(proof_rows(ops), {})
        for bits, cap, first in ((64, 32768, values[0]), (128, 32767, values[0]),
                                 (128, 32768, point(0)), (128, 32768, point(F(1, 3)))):
            shared, baseline = arithmetic(bits=bits, cap=cap), arithmetic(bits=bits, cap=cap)
            inputs = (first, *values[1:])
            self.assertEqual(shared._recording_rotate_sincos(*inputs, shared=True), direct(baseline, *inputs))
            self.assertEqual(shared.a.work.operations, baseline.a.work.operations)
            self.assertEqual(proof_rows(shared), {})

    def test_warm_proof_cannot_admit_a_larger_invalid_operand(self):
        ops, values = arithmetic(), dense_values()
        ops._recording_rotate_sincos(*values, shared=True)
        changed = (point(1 << 33000), *values[1:])
        outcomes = []
        for optimized in (False, True):
            target = ops if optimized else arithmetic()
            before = target.a.work.operations
            with patch.object(target.a, "lookup", side_effect=AssertionError("invalid operand reused")):
                with self.assertRaises(ReferenceError) as caught:
                    (target._recording_rotate_sincos(*changed, shared=True) if optimized else direct(target, *changed))
            outcomes.append((caught.exception.code, str(caught.exception), target.a.work.operations - before))
        self.assertEqual(*outcomes)

    def test_live_cap_changes_on_lookup_or_publication_keep_original_fallback(self):
        for method in ("lookup", "remember"):
            ops, values = arithmetic(), dense_values()
            original = getattr(ops.a, method)
            def narrow(*args):
                ops.a.work.max_operand_bits = 32767
                return original(*args)
            with patch.object(ops.a, method, side_effect=narrow):
                actual = ops._recording_rotate_sincos(*values, shared=True)
            self.assertEqual(actual, direct(arithmetic(cap=32767), *values))
            self.assertEqual(ops.a.work.max_operand_bits, 32767)

    def test_sharing_poll_preserves_callback_identity_and_does_not_publish_partial_proof(self):
        for fail_at in (1, 2, 3):
            for marker in (RuntimeError("cancel shared independent update"),
                           ReferenceError("resource", "caller owns cancellation")):
                ops, calls = arithmetic(), 0
                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise marker
                ops.a.work.external_check = cancel
                with self.assertRaises(type(marker)) as caught:
                    ops._recording_rotate_sincos(*dense_values(), shared=True)
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.a.work.callback_error, marker)
                self.assertEqual(proof_rows(ops), {})

    def test_equal_curves_keep_independent_clocks_contexts_and_completed_steps(self):
        ops, baseline = arithmetic(), arithmetic()
        contexts = object(), object()
        for target, shared in ((ops, True), (baseline, False)):
            for context, offset in zip(contexts, (0, 10)):
                target._recording_sincos(point(F(1, 8)), context=context, clock=F(1 + offset), shared=shared)
            for context, offset in zip(contexts, (0, 10)):
                target._recording_sincos(point(F(1, 4)), context=context, clock=F(2 + offset), shared=shared)
        rows, original = cursor_rows(ops), cursor_rows(baseline)
        self.assertEqual(rows, original)
        self.assertEqual(sorted(value[0] for value in rows.values()), [F(2), F(12)])
        self.assertEqual([value[4] for value in rows.values()], [1, 1])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(proof_rows(ops)), 1)
        self.assertLess(ops.a.work.operations, baseline.a.work.operations)
        self.assertEqual(proof_rows(baseline), {})

    def test_eviction_uses_only_the_existing_bounded_cache(self):
        ops, values = arithmetic(), dense_values()
        expected = ops._recording_rotate_sincos(*values, shared=True)
        for index in range(MAX_CACHE):
            ops.a.remember(("unrelated", index), F(index))
        self.assertEqual(proof_rows(ops), {})
        with patch.object(ops.a, "exact", wraps=ops.a.exact) as exact:
            self.assertEqual(ops._recording_rotate_sincos(*values, shared=True), expected)
        self.assertGreater(exact.call_count, 0)
        self.assertEqual(len(ops.a.cache), MAX_CACHE)
        self.assertEqual(ops.a.work.max_operations, 100000)
        self.assertEqual(ops.a.work.max_operand_bits, 32768)


if __name__ == "__main__":
    unittest.main()
