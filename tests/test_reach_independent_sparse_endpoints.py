"""Exact zero components omit arithmetic while all live domains stay checked."""
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def cells(values):
    return tuple(reader._Cell(F(value), F(value)) for value in values)


def original_magnitude(position, arithmetic):
    return arithmetic.total(abs(arithmetic.value(value)) for value in position)


class IndependentSparseEndpointTests(unittest.TestCase):
    def test_finite_position_magnitudes_equal_exact_sum_with_less_sparse_work(self):
        largest = float.fromhex("0x1.fffffffffffffp+1023")
        smallest = math.ldexp(1., -1074)
        for position in ((0., -0., 0.), (0., -3., 0.), (1., -2., 0.),
                         (1., -2., 3.), (smallest, -largest, 0.),
                         (largest, -largest, largest), (0, -(1 << 1023), 0)):
            work, baseline = Work(), Work()
            arithmetic, original = reader._Bounds(work), reader._Bounds(baseline)
            with self.subTest(position=position):
                result = reader._recording_position_magnitude(position, arithmetic)
                self.assertEqual(result, sum((abs(F(value)) for value in position), F(0)))
                self.assertEqual(result, original_magnitude(position, original))
                if any(value == 0 for value in position):
                    self.assertLess(work.operations, baseline.operations)
                else:
                    self.assertLessEqual(work.operations, baseline.operations)
                self.assertEqual(work.max_operations, 100000)
                self.assertFalse(work._cache)

    def test_endpoint_l1_omits_zero_decodes_but_preserves_interval_width(self):
        epsilon = F(1, 1 << 80)
        expected = (reader._Cell(-epsilon, epsilon), reader._Cell(F(2), F(2) + epsilon),
                    reader._Cell(F(-3) - epsilon, F(-3)))
        arithmetic = reader._Bounds(Work())
        with patch.object(arithmetic, "value", wraps=arithmetic.value) as decode:
            bound = reader._optional_endpoint_l1((0., 2., -3.), expected, arithmetic)
        self.assertEqual(bound, 3 * epsilon)
        self.assertEqual([call.args[0] for call in decode.call_args_list], [2., -3.])
        for zero in (0., -0., 0, F(0)):
            with self.subTest(zero_type=type(zero)), \
                    patch.object(arithmetic, "value", side_effect=AssertionError("exact zero decoded")):
                self.assertEqual(reader._optional_endpoint_l1((zero,) * 3, cells((0, 0, 0)), arithmetic), 0)

    def test_zero_shortcuts_still_reject_invalid_supplied_values_and_source_cells(self):
        for position in ((False, 0., 0.), (float("nan"), 0., 0.), (float("inf"), 0., 0.)):
            with self.subTest(position=position):
                with self.assertRaises(OntoKinError):
                    reader._recording_position_magnitude(position, reader._Bounds(Work()))
                with self.assertRaises(OntoKinError):
                    reader._optional_endpoint_l1(position, cells((0, 0, 0)), reader._Bounds(Work()))
        for expected in ((reader._Cell(F(1), F(0)), *cells((0, 0))),
                         cells((1 << 32768, 0, 0))):
            with self.subTest(expected=expected), self.assertRaises((OntoKinError, ReachAdmissionError)):
                reader._optional_endpoint_l1((0.,) * 3, expected, reader._Bounds(Work()))

    def test_large_integer_and_narrow_cap_keep_original_addition_preflights(self):
        for position, cap in (((1 << 32766, 0, 0), 32768), ((0.,) * 3, 1),
                              ((float(1 << 63), 0., 0.), 64)):
            errors = []
            for calculate in (original_magnitude, reader._recording_position_magnitude):
                arithmetic = reader._Bounds(Work(max_operand_bits=cap))
                with self.subTest(position=position, cap=cap, calculate=calculate.__name__), \
                        self.assertRaises(ReachAdmissionError) as caught:
                    calculate(position, arithmetic)
                errors.append(caught.exception.details)
            self.assertEqual(errors[0], errors[1])

    def test_live_cap_changes_reestablish_the_original_fold(self):
        for checkpoint, position, cap in (
                ("independent_position_magnitude", (0.,) * 3, 1),
                ("independent_bound_decode", (float(1 << 63), 0., 0.), 64)):
            original = reader._Bounds(Work(max_operand_bits=cap))
            with self.assertRaises(ReachAdmissionError) as expected:
                original_magnitude(position, original)
            work = Work()
            charge = work.charge
            def narrow(kind="checkpoint", amount=1):
                if kind == checkpoint:
                    work.max_operand_bits = cap
                return charge(kind, amount)
            with self.subTest(checkpoint=checkpoint), patch.object(work, "charge", narrow), \
                    self.assertRaises(ReachAdmissionError) as actual:
                reader._recording_position_magnitude(position, reader._Bounds(work))
            self.assertEqual(actual.exception.details, expected.exception.details)

    def test_cancellation_is_polled_before_zero_results_without_cache_mutation(self):
        for checkpoint in ("independent_position_magnitude", "independent_sufficient_endpoint_domain",
                           "independent_interval_vector_domain"):
            work = Work()
            marker = RuntimeError("cancel sparse endpoint " + checkpoint)
            charge = work.charge
            def cancel(kind="checkpoint", amount=1):
                if kind == checkpoint:
                    work.external_check = lambda: (_ for _ in ()).throw(marker)
                return charge(kind, amount)
            with self.subTest(checkpoint=checkpoint), patch.object(work, "charge", cancel), \
                    self.assertRaises(RuntimeError) as caught:
                arithmetic = reader._Bounds(work)
                if checkpoint == "independent_position_magnitude":
                    reader._recording_position_magnitude((0.,) * 3, arithmetic)
                else:
                    reader._optional_endpoint_l1((0.,) * 3, cells((0, 0, 0)), arithmetic)
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertFalse(work._cache)


if __name__ == "__main__":
    unittest.main()
