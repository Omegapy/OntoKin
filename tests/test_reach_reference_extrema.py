"""Independent interval extrema keep the original enclosure and finite domain."""
from contextlib import ExitStack
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork as Work
from ontokin.reach_reference import (
    MAX_OPERAND_BITS, Interval, ReferenceError, _Arithmetic, _Uncertain, build_reference,
)
from reach_agent_support import source_case


def grid(low, high, bits=128):
    scale = 1 << bits
    return Interval(F(math.floor(low * scale), scale), F(math.ceil(high * scale), scale))


def previous_add(arithmetic, a, b):
    a, b = arithmetic.interval(a), arithmetic.interval(b)
    arithmetic.tick()
    if a.lo == a.hi == 0:
        return b
    if b.lo == b.hi == 0:
        return a
    return arithmetic.grid(arithmetic.exact(a.lo, b.lo, "add"), arithmetic.exact(a.hi, b.hi, "add"))


def previous_mul(arithmetic, a, b):
    a, b = arithmetic.interval(a), arithmetic.interval(b)
    arithmetic.tick()
    if a.lo == a.hi == 0 or b.lo == b.hi == 0:
        return Interval(F(0), F(0))
    if a.lo == a.hi == 1:
        return b
    if b.lo == b.hi == 1:
        return a
    if a.lo == a.hi and b.lo == b.hi:
        value = arithmetic.exact(a.lo, b.lo, "mul")
        return arithmetic.grid(value, value)
    values = [arithmetic.exact(x, y, "mul") for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
    return arithmetic.grid(min(values), max(values))


def previous_div(arithmetic, a, b):
    a, b = arithmetic.interval(a), arithmetic.interval(b)
    if b.lo <= 0 <= b.hi:
        raise _Uncertain("Reference interval divisor contains zero")
    arithmetic.tick()
    if a.lo == a.hi == 0:
        return a
    if b.lo == b.hi == 1:
        return a
    if a.lo == a.hi and b.lo == b.hi:
        value = arithmetic.exact(a.lo, b.lo, "div")
        return arithmetic.grid(value, value)
    values = [arithmetic.exact(x, y, "div") for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
    return arithmetic.grid(min(values), max(values))


def previous_sqrt(arithmetic, value):
    value = arithmetic.interval(value)
    if value.lo < 0:
        raise _Uncertain("Reference radical is not certified nonnegative")
    result = []
    for endpoint in (value.lo, value.hi):
        arithmetic.tick()
        if abs(endpoint.numerator).bit_length() + 2 * arithmetic.bits > MAX_OPERAND_BITS:
            raise ReferenceError("resource", "Reference radical operand limit exceeded")
        scaled = (endpoint.numerator << (2 * arithmetic.bits)) // endpoint.denominator
        root = math.isqrt(scaled)
        low = F(root, arithmetic.scale)
        high = low if arithmetic.exact(low, low, "mul") == endpoint else F(root + 1, arithmetic.scale)
        result.append((low, high))
    return Interval(result[0][0], result[1][1])


def previous_atan(arithmetic, value):
    value = arithmetic.interval(value)
    low, high = arithmetic._atan_point(value.lo), arithmetic._atan_point(value.hi)
    return Interval(low.lo, high.hi)


PREVIOUS = {"add": previous_add, "mul": previous_mul, "div": previous_div,
            "sqrt": previous_sqrt, "atan": previous_atan}


class IndependentIntervalExtremaTests(unittest.TestCase):
    def test_every_sign_quadrant_and_point_matches_all_four_exact_corners(self):
        pairs = [(-3, -1), (-3, 0), (-3, 2), (0, 4), (1, 3),
                 (F(-3, 7), F(2, 5))]
        intervals = [Interval(F(low), F(high)) for low, high in pairs]
        intervals += [Interval(value, value) for value in map(F, (-2, 0, 1, 2, F(2, 7)))]
        for operation in ("add", "mul", "div"):
            for first in intervals:
                for last in intervals:
                    with self.subTest(operation=operation, first=first, last=last):
                        arithmetic = _Arithmetic(work=Work(), bits=32)
                        original = _Arithmetic(work=Work(), bits=32)
                        if operation == "div" and last.lo <= 0 <= last.hi:
                            with self.assertRaises(_Uncertain):
                                arithmetic.div(first, last)
                            continue
                        actual = getattr(arithmetic, operation)(first, last)
                        self.assertEqual(actual, PREVIOUS[operation](original, first, last))
                        if operation == "mul" and not any(
                                value.lo == value.hi and value.lo in (0, 1) for value in (first, last)):
                            corners = [x * y for x in (first.lo, first.hi) for y in (last.lo, last.hi)]
                            self.assertEqual(actual, grid(min(corners), max(corners), 32))
                        elif operation == "div" and first.lo != first.hi and last.lo != last.hi:
                            corners = [x / y for x in (first.lo, first.hi) for y in (last.lo, last.hi)]
                            self.assertEqual(actual, grid(min(corners), max(corners), 32))

    def test_monotone_extrema_omit_only_unneeded_scalar_operations(self):
        first, last = Interval(F(2, 7), F(3, 5)), Interval(F(7, 11), F(9, 10))
        for operation in ("mul", "div"):
            fresh_work, original_work = Work(), Work()
            arithmetic, original = _Arithmetic(work=fresh_work), _Arithmetic(work=original_work)
            self.assertEqual(getattr(arithmetic, operation)(first, last),
                             PREVIOUS[operation](original, first, last))
            self.assertEqual(original_work.operations - fresh_work.operations, 2)
        for operation, operand in (("sqrt", F(2)), ("atan", F(1, 3))):
            fresh_work, original_work = Work(), Work()
            arithmetic, original = _Arithmetic(work=fresh_work), _Arithmetic(work=original_work)
            self.assertEqual(getattr(arithmetic, operation)(operand), PREVIOUS[operation](original, operand))
            self.assertLess(fresh_work.operations, original_work.operations)

    def test_convertible_endpoint_types_keep_previous_supported_arithmetic(self):
        for first, last in ((Interval(.25, .75), Interval(2, 3)),
                            (Interval(-3, -1), Interval(-.75, -.25))):
            for operation in ("add", "mul", "div"):
                with self.subTest(operation=operation, first=first, last=last):
                    actual = getattr(_Arithmetic(work=Work()), operation)(first, last)
                    expected = PREVIOUS[operation](_Arithmetic(work=Work()), first, last)
                    self.assertEqual(actual, expected)

    def test_point_reuse_does_not_change_irrational_or_interval_enclosures(self):
        for operation, values in (
            ("sqrt", (F(0), F(1), F(2), F(1, 7), Interval(F(1, 3), F(2, 3)))),
            ("atan", (F(0), F(-1, 3), F(1), F(3), Interval(F(-1, 3), F(2, 5)))),
        ):
            for value in values:
                with self.subTest(operation=operation, value=value):
                    actual = getattr(_Arithmetic(work=Work()), operation)(value)
                    expected = PREVIOUS[operation](_Arithmetic(work=Work()), value)
                    self.assertEqual(actual, expected)

    def test_omitted_corner_keeps_original_intermediate_operand_limit(self):
        tiny = F(1, 1 << 20000)
        cases = (
            ("mul", Interval(tiny, F(1, 2)), Interval(F(1, 3), 1 + tiny)),
            ("div", Interval(F(1, 3), F(1, 2) + tiny), Interval(F(1, 2), 1 + tiny)),
        )
        for operation, first, last in cases:
            with self.subTest(operation=operation):
                for method in (lambda a: getattr(a, operation)(first, last),
                               lambda a: PREVIOUS[operation](a, first, last)):
                    with self.assertRaises(ReferenceError) as caught:
                        method(_Arithmetic(work=Work()))
                    self.assertEqual(caught.exception.code, "resource")

    def test_new_paths_preserve_the_callers_cancellation_exception(self):
        marker = RuntimeError("cancel independent interval arithmetic")
        for operation, values in (
            ("add", (Interval(F(2), F(2)), Interval(F(3), F(3)))),
            ("mul", (Interval(F(2), F(3)), Interval(F(4), F(5)))),
            ("div", (Interval(F(-3), F(-2)), Interval(F(4), F(5)))),
            ("sqrt", (Interval(F(2), F(2)),)),
            ("atan", (Interval(F(1, 3), F(1, 3)),)),
        ):
            arithmetic = _Arithmetic(check=lambda: None)
            with self.subTest(operation=operation), patch.object(arithmetic, "check", side_effect=marker):
                with self.assertRaises(RuntimeError) as caught:
                    getattr(arithmetic, operation)(*values)
                self.assertIs(caught.exception, marker)

    def test_source_boundary_histories_and_recording_poses_remain_exactly_equal(self):
        for case, end, time in (("P07", F(3), F(1, 4)), ("P19", F(3), F(1, 4)),
                                ("P16", F(3), F(5, 2)), ("L02", F(2), F(3, 2))):
            results, operations = [], []
            for previous in (False, True):
                with ExitStack() as stack:
                    if previous:
                        for name, method in PREVIOUS.items():
                            stack.enter_context(patch.object(_Arithmetic, name, new=method))
                    compiler = compile_construction(source_case(case))
                    reference = build_reference(compiler.model, end=end, work=compiler.reach_work)
                    carriers = tuple(path + ".frame" for path in reference.model.objects)
                    results.append((reference.boundary_states(),
                                    reference.recording_pose_enclosures(carriers, time),
                                    reference.sample(time)))
                    operations.append(compiler.budget.operations)
            with self.subTest(case=case):
                self.assertEqual(results[0], results[1])
                self.assertLess(operations[0], operations[1])


if __name__ == "__main__":
    unittest.main()
