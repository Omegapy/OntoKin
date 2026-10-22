"""A recording cursor rounds exact interval rotation only at final outputs."""
from contextlib import nullcontext
from fractions import Fraction as F
from itertools import product
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_reference import Interval, MAX_CACHE, ReferenceError, _Arithmetic, _PoseArithmetic
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def arithmetic(*, bits=128, cap=32768):
    return _PoseArithmetic(_Arithmetic(work=ReachExecutionWork(max_operand_bits=cap), bits=bits))


def point(value):
    value = F(value)
    return Interval(value, value)


def direct(ops, old_sine, old_cosine, sine, cosine, *, shared=False):
    return (ops.a.add(ops.a.mul(old_sine, cosine), ops.a.mul(old_cosine, sine)),
            ops.a.sub(ops.a.mul(old_cosine, cosine), ops.a.mul(old_sine, sine)))


def exact_expected(values, bits=128):
    old_sine, old_cosine, sine, cosine = values
    def bounds(a, b):
        products = [x * y for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
        return min(products), max(products)
    def grid(low, high):
        scale = 1 << bits
        return Interval(F((low.numerator * scale) // low.denominator, scale),
                        F(-((-high.numerator * scale) // high.denominator), scale))
    left, right = bounds(old_sine, cosine), bounds(old_cosine, sine)
    first = grid(left[0] + right[0], left[1] + right[1])
    left, right = bounds(old_cosine, cosine), bounds(old_sine, sine)
    return first, grid(left[0] - right[1], left[1] - right[0])


def dense_values():
    scale = 1 << 128
    return tuple(Interval(F(scale // denominator, scale), F(scale // denominator + 1, scale))
                 for denominator in (3, 5, 7, 11))


class IndependentFusedRecordingTests(unittest.TestCase):
    def test_all_product_sign_domains_equal_separate_exact_corner_extrema(self):
        positive = dense_values()[0]
        negative = Interval(-positive.hi, -positive.lo)
        mixed = Interval(F(-1, 1 << 128), F(2, 1 << 128))
        for values in product((positive, negative, mixed), repeat=4):
            with self.subTest(signs=tuple((value.lo >= 0, value.hi <= 0) for value in values)):
                ops, baseline = arithmetic(), arithmetic()
                actual = ops._recording_rotate_sincos(*values)
                expected = exact_expected(values)
                previous = direct(baseline, *values)
                self.assertEqual(actual, expected)
                for enclosed, old in zip(actual, previous):
                    self.assertGreaterEqual(enclosed.lo, old.lo)
                    self.assertLessEqual(enclosed.hi, old.hi)
                self.assertLess(ops.a.work.operations, baseline.a.work.operations)
                self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))
                self.assertEqual(ops.a.cache, {})

    def test_exact_points_use_each_product_once_and_stay_on_the_same_grid(self):
        values = tuple(point(value) for value in (F(1, 4), F(-3, 8), F(1, 16), F(7, 8)))
        ops, baseline = arithmetic(), arithmetic()
        self.assertEqual(ops._recording_rotate_sincos(*values), exact_expected(values))
        self.assertEqual(ops._recording_rotate_sincos(*values), direct(baseline, *values))
        self.assertLess(ops.a.work.operations // 2, baseline.a.work.operations)
        self.assertEqual(ops.a.cache, {})

    def test_other_precisions_domains_shapes_and_identity_shortcuts_are_exactly_original(self):
        values = dense_values()
        cases = [(64, 32768, values), (256, 32768, values), (128, 32767, values)]
        for replacement in (point(0), point(1), point(-1), point(F(1, 3)), F(1, 8),
                            Interval(False, False)):
            cases.append((128, 32768, (replacement, *values[1:])))
        for bits, cap, inputs in cases:
            with self.subTest(bits=bits, cap=cap, first=inputs[0]):
                ops, baseline = arithmetic(bits=bits, cap=cap), arithmetic(bits=bits, cap=cap)
                self.assertEqual(ops._recording_rotate_sincos(*inputs), direct(baseline, *inputs))
                self.assertEqual(ops.a.work.operations, baseline.a.work.operations)

    def test_large_operands_keep_the_original_guard_before_ordering_or_products(self):
        for operand in (F(1 << 33000), F(1, 1 << 33000)):
            values = (point(operand), *dense_values()[1:])
            outcomes = []
            for optimized in (False, True):
                ops = arithmetic()
                with self.subTest(optimized=optimized, denominator_bits=operand.denominator.bit_length()), \
                        self.assertRaises(ReferenceError) as caught:
                    (ops._recording_rotate_sincos(*values) if optimized else direct(ops, *values))
                outcomes.append((caught.exception.code, str(caught.exception), ops.a.work.operations))
            self.assertEqual(outcomes[0], outcomes[1])

    def test_narrowing_at_admission_products_sums_or_final_grid_replays_original(self):
        values = dense_values()
        for fail_at in (1, 3, 6, 8, 15):
            ops, calls = arithmetic(), 0
            def narrow():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    ops.a.work.max_operand_bits = 32767
            ops.a.work.external_check = narrow
            actual = ops._recording_rotate_sincos(*values)
            self.assertEqual(actual, direct(arithmetic(cap=32767), *values))
            self.assertEqual(ops.a.work.max_operand_bits, 32767)
            self.assertEqual(ops.a.cache, {})

    def test_callback_failures_keep_exact_identity_and_publish_nothing(self):
        for fail_at in (1, 4, 10, 15):
            for marker in (RuntimeError("cancel fused independent rotation"),
                           ReferenceError("resource", "caller owns this refusal")):
                ops, calls = arithmetic(), 0
                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        ops.a.work.max_operand_bits = 32767
                        raise marker
                ops.a.work.external_check = cancel
                with self.assertRaises(type(marker)) as caught:
                    ops._recording_rotate_sincos(*dense_values())
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.a.work.callback_error, marker)
                self.assertEqual(ops.a.cache, {})

    def test_full_cursor_preserves_a_direct_fallback_failure_before_a_broadening_callback(self):
        ops, context = arithmetic(), object()
        ops._recording_sincos(point(F(1, 8)), context=context, clock=F(1))
        cursor_key = ops._key("recording_sincos", context)
        before = ops.a.cache[cursor_key]
        original_rotate, original_mul = ops._recording_rotate_sincos, ops.a.mul
        armed, failures, broadened = False, [], []

        def change_domain():
            if armed:
                if failures:
                    broadened.append(True)
                    ops.a.work.max_operand_bits = 32768
                else:
                    ops.a.work.max_operand_bits = 64

        def enter_rotation(*values):
            nonlocal armed
            armed = True
            return original_rotate(*values)

        def observe_direct_mul(a, b):
            try:
                return original_mul(a, b)
            except ReferenceError as error:
                failures.append(error)
                raise

        with patch.object(ops.a.work, "external_check", side_effect=change_domain), \
                patch.object(ops, "_recording_rotate_sincos", side_effect=enter_rotation), \
                patch.object(ops.a, "mul", side_effect=observe_direct_mul):
            with self.assertRaises(ReferenceError) as caught:
                ops._recording_sincos(point(F(1, 4)), context=context, clock=F(2))
        self.assertTrue(armed)
        self.assertEqual(len(failures), 1)
        self.assertIs(caught.exception, failures[0])
        self.assertEqual(caught.exception.code, "resource")
        self.assertFalse(broadened)
        self.assertEqual(ops.a.work.max_operand_bits, 64)
        self.assertIsNone(ops.a.work.callback_error)
        self.assertEqual(ops.a.cache[cursor_key], before)

    def test_cancelled_fused_update_cannot_advance_the_existing_cursor(self):
        ops, context = arithmetic(), object()
        ops._recording_sincos(point(F(1, 8)), context=context, clock=F(1))
        key = ops._key("recording_sincos", context)
        previous = ops.a.cache[key]
        original, marker = ops._recording_rotate_sincos, RuntimeError("cancel before fused cursor update")
        def cancelled(*values):
            def cancel():
                raise marker
            ops.a.work.external_check = cancel
            return original(*values)
        with patch.object(ops, "_recording_rotate_sincos", side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                ops._recording_sincos(point(F(1, 4)), context=context, clock=F(2))
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.a.work.callback_error, marker)
        self.assertEqual(ops.a.cache[key], previous)
        self.assertLessEqual(len(ops.a.cache), MAX_CACHE)

    def test_actual_glb_bytes_and_validation_are_unchanged_with_less_recording_work(self):
        for case in ("P01", "P18"):
            outcomes = []
            for optimized in (False, True):
                compiler = compile_construction(source_case(case))
                context = (nullcontext() if optimized else
                           patch.object(_PoseArithmetic, "_recording_rotate_sincos", new=direct))
                with context:
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                self.assertLessEqual(compiler.budget.operations, 100000)
                outcomes.append((result.data, result.report["validation"], compiler.budget.operations))
            self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            self.assertLess(outcomes[1][2], outcomes[0][2])


if __name__ == "__main__":
    unittest.main()
