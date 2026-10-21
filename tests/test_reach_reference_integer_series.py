"""Exact adaptive reference sums retain their first strict alternating tail."""
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork as Work
from ontokin.reach_reference import (
    MAX_CACHE, MAX_OPERAND_BITS, Interval, ReferenceError, _Arithmetic, _Uncertain, build_reference,
)
from reach_agent_support import source_case


def previous_series(arithmetic, value):
    """The original charged Fraction recurrence, including all its preflights."""
    value = arithmetic.interval(value)
    if value.magnitude > 1:
        raise _Uncertain("Reference sine reduction exceeds its proved range")
    middle = arithmetic.exact(arithmetic.exact(value.lo, value.hi, "add"), 2, "div")
    width = max(arithmetic.exact(middle, value.lo, "sub"), arithmetic.exact(value.hi, middle, "sub"))
    squared = arithmetic.exact(middle, middle, "mul")
    sine, cosine = middle, F(1)
    sine_term, cosine_term = middle, F(1)
    threshold = F(1, 1 << (arithmetic.bits + 8))
    for k in range(1, arithmetic.bits // 5 + 12):
        sine_term = -arithmetic.exact(arithmetic.exact(sine_term, squared, "mul"), (2 * k) * (2 * k + 1), "div")
        cosine_term = -arithmetic.exact(arithmetic.exact(cosine_term, squared, "mul"), (2 * k - 1) * (2 * k), "div")
        sine, cosine = arithmetic.exact(sine, sine_term, "add"), arithmetic.exact(cosine, cosine_term, "add")
        arithmetic.tick()
        tail = max(abs(sine_term), abs(cosine_term))
        if tail < threshold:
            error = arithmetic.exact(tail, width, "add")
            return (arithmetic.grid(arithmetic.exact(sine, error, "sub"), arithmetic.exact(sine, error, "add")),
                    arithmetic.grid(arithmetic.exact(cosine, error, "sub"), arithmetic.exact(cosine, error, "add")))
    raise _Uncertain("Finite reference sine series did not converge")


def direct_sums(middle, bits):
    """Separate direct powers/factorials select the first included small term."""
    threshold = F(1, 1 << (bits + 8))
    for degree in range(1, bits // 5 + 12):
        tail = middle ** (2 * degree) / math.factorial(2 * degree)
        if tail < threshold:
            sine = sum(((-1) ** k * middle ** (2 * k + 1) / math.factorial(2 * k + 1)
                        for k in range(degree + 1)), F(0))
            cosine = sum(((-1) ** k * middle ** (2 * k) / math.factorial(2 * k)
                          for k in range(degree + 1)), F(0))
            return (sine, cosine, tail), degree
    raise AssertionError("Test series did not converge")


class IndependentIntegerSeriesTests(unittest.TestCase):
    def test_cold_outputs_equal_the_original_fraction_recurrence(self):
        values = [F(-1), F(-7, 8), F(-1, 1024), F(0), F(1, 1024), F(3, 8), F(1)]
        values += [Interval(F(-3, 32), F(1, 16)), Interval(F(7, 16), F(9, 16)),
                   Interval(F(-1), F(1)), Interval(F(1, 3), F(2, 3))]
        for bits in (32, 64, 96, 128, 256):
            for value in values:
                with self.subTest(bits=bits, value=value):
                    actual = _Arithmetic(work=Work(), bits=bits)._series_sincos(value)
                    expected = previous_series(_Arithmetic(work=Work(), bits=bits), value)
                    self.assertEqual(actual, expected)

    def test_selected_sums_and_tail_equal_direct_powers_at_the_first_degree(self):
        for bits in (32, 96, 128):
            arithmetic = _Arithmetic(work=Work(), bits=bits)
            for exponent in (0, 1, 7, 32, 128):
                denominator = 1 << exponent
                numerators = {0, 1, denominator, max(1, denominator // 3), max(1, denominator - 1)}
                for numerator in sorted(numerators):
                    for sign in (-1, 1):
                        middle = F(sign * numerator, denominator)
                        with self.subTest(bits=bits, middle=middle):
                            expected, degree = direct_sums(middle, bits)
                            actual = arithmetic._series_dyadic(middle, middle * middle)
                            self.assertIsNotNone(actual)
                            self.assertEqual(actual, expected)
                            if degree > 1:
                                previous_tail = middle ** (2 * degree - 2) / math.factorial(2 * degree - 2)
                                self.assertGreaterEqual(previous_tail, F(1, 1 << (bits + 8)))

    def test_warm_coefficients_reduce_actual_work_for_distinct_exact_angles(self):
        work = Work()
        arithmetic = _Arithmetic(work=work)
        denominator = 1 << 128
        arithmetic._series_sincos(F((denominator >> 1) + 1, denominator))
        for offset in (3, 5, 7, 101):
            value = F((denominator >> 1) + offset, denominator)
            original_work = Work()
            before = work.operations
            actual = arithmetic._series_sincos(value)
            expected = previous_series(_Arithmetic(work=original_work), value)
            with self.subTest(offset=offset):
                self.assertEqual(actual, expected)
                self.assertLess(work.operations - before, original_work.operations)
        self.assertLessEqual(len(arithmetic.cache), MAX_CACHE)

    def test_non_dyadic_large_denominator_and_large_precision_keep_the_original_path(self):
        for value, bits in ((F(1, 3), 128), (F(1, 1 << 300), 128), (F(1, 2), 512)):
            with self.subTest(value=value, bits=bits):
                arithmetic = _Arithmetic(work=Work(), bits=bits)
                self.assertIsNone(arithmetic._series_dyadic(value, value * value))
                with patch.object(arithmetic, "_series_coefficients", side_effect=AssertionError("unexpected integer path")):
                    self.assertEqual(arithmetic._series_sincos(value),
                                     previous_series(_Arithmetic(work=Work(), bits=bits), value))

    def test_legacy_intermediate_failures_and_lowered_caps_cannot_use_a_warm_proof(self):
        arithmetic = _Arithmetic(work=Work())
        arithmetic._series_sincos(F(1, 2))
        tiny = F(1, 1 << 9000)
        for execute in (lambda: arithmetic._series_sincos(tiny),
                        lambda: previous_series(_Arithmetic(work=Work()), tiny)):
            with self.assertRaises(ReferenceError) as caught:
                execute()
            self.assertEqual(caught.exception.code, "resource")
        with patch("ontokin.reach_reference.MAX_OPERAND_BITS", 256):
            for execute in (lambda: arithmetic._series_sincos(F(1, 2)),
                            lambda: previous_series(_Arithmetic(work=Work()), F(1, 2))):
                with self.assertRaises(ReferenceError) as caught:
                    execute()
                self.assertEqual(caught.exception.code, "resource")
        for execute in (lambda: arithmetic._series_sincos(F(2)),
                        lambda: previous_series(_Arithmetic(work=Work()), F(2))):
            with self.assertRaises(_Uncertain):
                execute()

    def test_integer_preflights_charge_before_rejecting_an_oversized_allocation(self):
        for first, last, operation in ((1 << 20000, 1 << 20000, "mul"),
                                       (1, MAX_OPERAND_BITS, "shift")):
            work = Work()
            arithmetic = _Arithmetic(work=work)
            with self.subTest(operation=operation), self.assertRaises(ReferenceError) as caught:
                arithmetic._series_integer(first, last, operation)
            self.assertEqual(caught.exception.code, "resource")
            self.assertEqual(work.operations, 1)

    def test_callbacks_keep_identity_on_cold_and_cached_paths(self):
        marker = RuntimeError("cancel independent exact integer series")
        calls = 0

        def cancel_during_table():
            nonlocal calls
            calls += 1
            if calls == 20:
                raise marker

        arithmetic = _Arithmetic(check=cancel_during_table)
        with self.assertRaises(RuntimeError) as caught:
            arithmetic._series_sincos(F(1, 2))
        self.assertIs(caught.exception, marker)
        self.assertEqual(arithmetic.cache, {})
        arithmetic = _Arithmetic(work=Work())
        arithmetic._series_sincos(F(1, 2))
        with patch.object(arithmetic, "check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                arithmetic._series_sincos(F(1, 2))
        self.assertIs(caught.exception, marker)

    def test_coefficient_eviction_keeps_the_same_complete_result_and_cache_bound(self):
        arithmetic = _Arithmetic(work=Work())
        value = Interval(F(-7, 16), F(-5, 16))
        expected = arithmetic._series_sincos(value)
        for index in range(MAX_CACHE + 5):
            arithmetic.remember(("series-test-padding", index), (index,))
            self.assertLessEqual(len(arithmetic.cache), MAX_CACHE)
        self.assertFalse(any(key[0] == "series_coefficients" for key in arithmetic.cache))
        self.assertEqual(arithmetic._series_sincos(value), expected)
        self.assertLessEqual(len(arithmetic.cache), MAX_CACHE)

    def test_complete_source_boundary_and_pose_trees_equal_the_previous_series(self):
        for case, end, time in (("P01", F(3), F(1, 4)), ("P07", F(3), F(1, 4)),
                                ("P16", F(3), F(5, 2)), ("L02", F(2), F(3, 2))):
            results = []
            for original in (False, True):
                with patch.object(_Arithmetic, "_series_sincos", new=previous_series if original else _Arithmetic._series_sincos):
                    compiler = compile_construction(source_case(case))
                    reference = build_reference(compiler.model, end=end, work=compiler.reach_work)
                    carriers = tuple(path + ".frame" for path in reference.model.objects)
                    results.append((reference.boundary_states(),
                                    reference.recording_pose_enclosures(carriers, time), reference.sample(time)))
            with self.subTest(case=case):
                self.assertEqual(results[0], results[1])


if __name__ == "__main__":
    unittest.main()
