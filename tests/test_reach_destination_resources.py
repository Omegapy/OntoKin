"""Resource and interruption checks for the identified recording arithmetic.

These tests use a small external work protocol so the writer cannot obtain a
fresh allowance while executing a nested helper. The retained IK oracle is not
imported, and these probes do not execute source, Agent or export workflows.
"""
from fractions import Fraction
import math
import struct
import unittest
from unittest.mock import patch

from ontokin import reach_export as recording


class ResourceExhausted(Exception):
    pass


class ProbeWork:
    def __init__(self, *, bits=32768, operations=100000, callback=None):
        self.max_bits = bits
        self.max_operations = operations
        self.operations = 0
        self.events = []
        self.callback = callback

    def charge(self, kind="recording_arithmetic"):
        if self.callback is not None:
            self.callback()
        if self.operations >= self.max_operations:
            raise ResourceExhausted("operations")
        self.operations += 1
        self.events.append(kind)

    def guard_bits(self, bits):
        if bits > self.max_bits:
            raise ResourceExhausted("bits")

    def guard(self, *values):
        for value in values:
            if isinstance(value, Fraction):
                self.guard_bits(max(value.numerator.bit_length(), value.denominator.bit_length()))
            else:
                self.guard_bits(value.bit_length())


class ReachDestinationResourceTests(unittest.TestCase):
    def test_exact_product_is_rejected_before_fraction_allocation(self):
        left = Fraction(1 << 20000)
        right = Fraction((1 << 20000) + 1)
        with patch.object(Fraction, "__mul__", side_effect=AssertionError("product allocated")) as operation:
            with self.assertRaises(ResourceExhausted):
                recording._exact(left, right, "mul", ProbeWork())
        operation.assert_not_called()

    def test_exact_sum_is_rejected_before_cross_products(self):
        left = Fraction(1, (1 << 20000) + 1)
        right = Fraction(1, (1 << 20000) + 3)
        with patch.object(Fraction, "__add__", side_effect=AssertionError("sum allocated")) as operation:
            with self.assertRaises(ResourceExhausted):
                recording._exact(left, right, "add", ProbeWork())
        operation.assert_not_called()

    def test_sqrt_rejects_growth_before_shift_and_integer_root(self):
        value = Fraction(1 << 32700)
        with patch.object(recording.math, "isqrt", side_effect=AssertionError("root allocated")) as operation:
            with self.assertRaises(ResourceExhausted):
                recording.sqrt_upper(value, work=ProbeWork())
        operation.assert_not_called()

    def test_clock_round_rejects_growth_before_divmod(self):
        value = Fraction(1, 1 << 32767)
        with patch("builtins.divmod", side_effect=AssertionError("quotient allocated")) as operation:
            with self.assertRaises(ResourceExhausted):
                recording.direct_binary32(value, work=ProbeWork())
        operation.assert_not_called()

    def test_integer_root_checks_cancellation_before_return(self):
        cancelled = False
        interruption = RuntimeError("original request cancellation")
        original = math.isqrt

        def check():
            if cancelled:
                raise interruption

        def root(value):
            nonlocal cancelled
            answer = original(value)
            cancelled = True
            return answer

        with patch.object(recording.math, "isqrt", side_effect=root):
            with self.assertRaises(RuntimeError) as caught:
                recording.sqrt_upper(Fraction(2), work=ProbeWork(callback=check))
        self.assertIs(caught.exception, interruption)

    def test_fixed_vector_dimension_stops_an_unbounded_iterator(self):
        observed = []

        def values():
            for index in range(6):
                observed.append(index)
                if index == 5:
                    raise AssertionError("the fixed dimension was not enforced")
                yield 1

        with self.assertRaisesRegex(ValueError, "fixed dimension"):
            recording.norm_upper(values(), work=ProbeWork())
        self.assertEqual(observed, [0, 1, 2, 3, 4])

    def test_complete_bounds_reject_angular_square_before_allocation(self):
        bound = recording.MotionBound(Fraction(1), Fraction(1), Fraction(1 << 17000))
        original = Fraction.__mul__
        observed = []

        def multiply(left, right):
            size = max(left.numerator.bit_length(), right.numerator.bit_length())
            observed.append(size)
            if size > 17000:
                raise AssertionError("an oversized angular product was allocated")
            return original(left, right)

        with patch.object(Fraction, "__mul__", multiply):
            with self.assertRaises(ResourceExhausted):
                recording.complete_interval_bounds(width=1, bound=bound, enclosing=bound,
                    radius=1, vertex_error=0, endpoint_position_error=0,
                    endpoint_quaternion_error=0, stored_arc=0, time_shift=0,
                    source_position_error=0, source_rotation_error=0,
                    destination_position_error=0, destination_rotation_error=0,
                    work=ProbeWork())
        self.assertTrue(observed)
        self.assertLess(max(observed), 17000)

    def test_negative_normalization_underflow_is_canonical_positive_zero(self):
        answer = recording.normalized_component(-Fraction(1, 1 << 1075), 1, work=ProbeWork())
        self.assertEqual(struct.pack(">d", answer), bytes(8))

    def test_supplied_work_is_shared_without_nested_fresh_allowances(self):
        work = ProbeWork(operations=4)
        with patch.object(recording, "_LocalArithmeticWork", side_effect=AssertionError("fresh allowance")):
            self.assertEqual(recording.direct_binary32(0, work=work), (0.0, "00000000"))
            self.assertEqual(recording.direct_binary32(0, work=work), (0.0, "00000000"))
            with self.assertRaises(ResourceExhausted):
                recording.direct_binary32(0, work=work)
        self.assertEqual(work.operations, 4)

    def test_nested_normalization_and_bounds_charge_the_supplied_work(self):
        work = ProbeWork()
        with patch.object(recording, "_LocalArithmeticWork", side_effect=AssertionError("fresh allowance")):
            arc = recording.quaternion_arc_upper((0, 0, 0, 1), (0, 0, 0, 1), work=work)
            recording.destination_numeric_bounds(arc, 1, 1, 0, work=work)
        self.assertGreater(work.operations, 40)
        self.assertIn("recording_exact_mul", work.events)
        self.assertIn("recording_integer_sqrt_return", work.events)

    def test_decimal_serialization_does_not_depend_on_global_digit_limit(self):
        value = Fraction(10**5000 + 1)
        work = ProbeWork()
        result = recording.rational_record(value, work=work)
        self.assertEqual(result, {"numerator": "1" + "0" * 4999 + "1", "denominator": "1"})
        self.assertGreater(work.events.count("recording_decimal_chunk"), 500)

    def test_decimal_serialization_preserves_callback_exception(self):
        interruption = LookupError("cancel decimal conversion")
        calls = 0

        def check():
            nonlocal calls
            calls += 1
            if calls == 4:
                raise interruption

        with self.assertRaises(LookupError) as caught:
            recording.rational_record(Fraction(10**100), work=ProbeWork(callback=check))
        self.assertIs(caught.exception, interruption)


if __name__ == "__main__":
    unittest.main()
