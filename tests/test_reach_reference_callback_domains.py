"""A callback cannot admit wider interval operands through an exact shortcut."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_reference import Interval, ReferenceError, _Arithmetic, _PoseArithmetic


class Work:
    def __init__(self):
        self.max_operand_bits = 256
        self.operations = 0
        self.callback = None

    def tick(self):
        self.operations += 1
        if self.callback is not None:
            self.callback()


def point(value):
    return Interval(F(value), F(value))


class ReachReferenceCallbackDomainTests(unittest.TestCase):
    def setUp(self):
        self.work = Work()
        self.a = _Arithmetic(work=self.work, bits=8)
        self.p = _PoseArithmetic(self.a)
        self.zero, self.one = point(0), point(1)
        self.wide = point(1 << 80)
        self.zero_vector = (self.zero,) * 3
        self.wide_vector = (self.wide, self.zero, self.zero)
        self.unit = (self.one, self.zero, self.zero, self.zero)

    def lower(self):
        self.work.max_operand_bits = 64

    def resource(self, query):
        self.work.max_operand_bits = 256
        self.work.callback = self.lower
        with self.assertRaises(ReferenceError) as caught:
            query()
        self.assertEqual(caught.exception.code, "resource")

    def test_scalar_zero_and_identity_shortcuts_recheck_after_the_callback(self):
        queries = (
            lambda: self.a.add(self.zero, self.wide),
            lambda: self.a.add(self.wide, self.zero),
            lambda: self.a.mul(self.zero, self.wide),
            lambda: self.a.mul(self.one, self.wide),
            lambda: self.a.mul(self.wide, self.one),
            lambda: self.a.div(self.wide, self.one),
            lambda: self.a.div(self.zero, self.wide),
        )
        for index, query in enumerate(queries):
            with self.subTest(index=index):
                self.resource(query)

    def test_vector_zero_and_identity_shortcuts_recheck_after_the_callback(self):
        queries = (
            lambda: self.p.add(self.zero_vector, self.wide_vector),
            lambda: self.p.add(self.wide_vector, self.zero_vector),
            lambda: self.p.scale(self.wide_vector, self.one),
            lambda: self.p.scale(self.zero_vector, self.wide),
            lambda: self.p.cross(self.zero_vector, self.wide_vector),
            lambda: self.p.cross(self.wide_vector, self.zero_vector),
            lambda: self.p.rotate(self.unit, self.wide_vector),
        )
        for index, query in enumerate(queries):
            with self.subTest(index=index):
                self.resource(query)

    def test_scalar_quaternion_normalization_rechecks_after_cache_lookup(self):
        self.resource(lambda: self.p.quaternion((self.wide, self.zero, self.zero, self.zero)))

    def test_radical_rechecks_the_endpoint_denominator_before_allocating(self):
        tiny = point(F(1, 1 << 80))
        with patch("ontokin.reach_reference.math.isqrt", side_effect=AssertionError("allocated radical")):
            self.resource(lambda: self.a.sqrt(tiny))

    def test_public_rounding_rechecks_both_endpoints_after_the_callback(self):
        self.resource(lambda: self.a.round64(self.wide))
        self.resource(lambda: self.a.round64(point(F(1, 1 << 80))))

    def test_integer_series_unpack_rechecks_before_the_native_division(self):
        self.work.max_operand_bits = 32768
        original = self.a._series_integer
        def narrow_at_unpack(first, last, operation):
            if operation == "divmod":
                self.work.callback = lambda: setattr(self.work, "max_operand_bits", 16)
            return original(first, last, operation)
        with patch.object(self.a, "_series_integer", side_effect=narrow_at_unpack), \
             patch("ontokin.reach_reference.divmod", create=True, side_effect=AssertionError("allocated unpack")):
            with self.assertRaises(ReferenceError) as caught:
                self.a._series_dyadic(F(1, 2), F(1, 4))
        self.assertEqual(caught.exception.code, "resource")

    def test_quadrant_rounding_rechecks_before_its_native_fraction_product(self):
        def narrow_at_quadrant():
            # Lookup, input midpoint, pi midpoint, quotient, then quadrant.
            if self.work.operations == 5:
                self.lower()
        self.work.callback = narrow_at_quadrant
        with patch.object(self.a, "pi", return_value=point(3)), \
             patch.object(F, "__mul__", side_effect=AssertionError("allocated quadrant product")):
            with self.assertRaises(ReferenceError) as caught:
                self.a.sincos(point(F(1, 1 << 80)))
        self.assertEqual(caught.exception.code, "resource")

    def test_valid_shortcuts_keep_exact_results_under_the_new_domain(self):
        vector = (point(3), point(-4), point(5))
        self.work.callback = self.lower
        self.assertEqual(self.a.add(self.zero, point(7)), point(7))
        self.assertEqual(self.a.mul(self.one, point(7)), point(7))
        self.assertEqual(self.a.div(point(7), self.one), point(7))
        self.assertEqual(self.p.add(self.zero_vector, vector), vector)
        self.assertEqual(self.p.scale(vector, self.one), vector)
        self.assertEqual(self.p.cross(vector, self.zero_vector), self.zero_vector)
        self.assertEqual(self.p.rotate(self.unit, vector), vector)
        self.assertEqual(self.p.quaternion((point(3), self.zero, self.zero, self.zero)), self.unit)
        self.assertEqual(self.a.round64(point(F(1, 2))), .5)

    def test_callback_cancellation_precedes_post_callback_domain_checks(self):
        marker = RuntimeError("cancel before the narrower independent domain")
        def cancel():
            self.lower()
            raise marker
        for query in (lambda: self.a.add(self.zero, self.wide),
                      lambda: self.p.rotate(self.unit, self.wide_vector),
                      lambda: self.a.sqrt(point(F(1, 1 << 80)))):
            self.work.max_operand_bits = 256
            self.work.callback = cancel
            with self.assertRaises(RuntimeError) as caught:
                query()
            self.assertIs(caught.exception, marker)


if __name__ == "__main__":
    unittest.main()
