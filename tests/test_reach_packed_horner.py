"""Exact integer lanes retain the original source Taylor polynomial bits."""
from fractions import Fraction as F
import random
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import BITS, ReachPoseOps


def ordinary(value, work=None):
    ops = ReachPoseOps(work or ReachExecutionWork())
    with patch.object(ops, '_packed_horner_sincos', return_value=None):
        return ops._horner_sincos(value)


class ReachPackedHornerTests(unittest.TestCase):
    def test_original_polynomial_and_final_grid_match_exactly(self):
        generator = random.Random(20261021)
        values = [F(0), F(1), F(-1), F(1, 2), F(-1, 2),
                  F(1, 1 << BITS), F(-1, 1 << BITS),
                  F((1 << BITS) - 1, 1 << BITS),
                  F(1 - (1 << BITS), 1 << BITS)]
        for bits in (1, 2, 8, 24, 52, 53, 72, 95, 96):
            values.extend(F(generator.randrange(-(1 << bits), (1 << bits) + 1), 1 << bits)
                          for _ in range(12))
        for value in values:
            with self.subTest(value=value):
                actual = ReachPoseOps(ReachExecutionWork())._horner_sincos(value)
                self.assertEqual(actual, ordinary(value))

    def test_repeated_layout_reduces_real_arithmetic_and_remains_bounded(self):
        packed, original = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
        first, second = F(123456789, 1 << 30), F(234567891, 1 << 30)
        packed._horner_sincos(first)
        with patch.object(original, '_packed_horner_sincos', return_value=None):
            original._horner_sincos(first)
        before = packed.work.operations, original.work.operations
        actual = packed._horner_sincos(second)
        with patch.object(original, '_packed_horner_sincos', return_value=None):
            expected = original._horner_sincos(second)
        self.assertEqual(actual, expected)
        self.assertLess(packed.work.operations - before[0], original.work.operations - before[1])
        self.assertLessEqual(len(packed.work._cache), 256)
        self.assertEqual(packed.work.operations, sum(packed.work.counts.values()))

    def test_lower_operand_limits_retain_the_original_rejection_or_result(self):
        for cap in (128, 192, 256, 512, 1024, 2048, 4096):
            for value in (F(1), F(-1, 2), F(5, 8), F(127, 256), F(123456789, 1 << 52)):
                outcomes = []
                for reuse in (False, True):
                    work = ReachExecutionWork(max_operand_bits=cap)
                    ops = ReachPoseOps(work)
                    try:
                        if reuse:
                            result = ops._horner_sincos(value)
                        else:
                            with patch.object(ops, '_packed_horner_sincos', return_value=None):
                                result = ops._horner_sincos(value)
                        outcomes.append(('returned', result))
                    except ReachAdmissionError as error:
                        outcomes.append(('failed', error.reach_code, error.details))
                with self.subTest(cap=cap, value=value):
                    self.assertEqual(outcomes[0], outcomes[1])

    def test_different_reduced_denominators_share_one_admitted_grid_layout(self):
        ops = ReachPoseOps(ReachExecutionWork())
        values = (F(1, 2), F(5, 16), F(123456789, 1 << 52),
                  F((1 << BITS) - 1, 1 << BITS), F(-1), F(0))
        coefficient_cost = None
        for value in values:
            self.assertEqual(ops._horner_sincos(value), ordinary(value))
            actual_cost = ops.work.counts['source_horner_integer_coefficient']
            if coefficient_cost is None:
                coefficient_cost = actual_cost
            else:
                self.assertEqual(actual_cost, coefficient_cost)
        self.assertLessEqual(len(ops.work._cache), ops.work.max_cache_entries)

    def test_warm_layout_does_not_admit_changed_domain_or_hide_cancellation(self):
        ops = ReachPoseOps(ReachExecutionWork())
        ops._horner_sincos(F(5, 8))
        for value in (False, .625, F(1, 3), F(1, 1 << (BITS + 1)), F(9, 8)):
            with self.subTest(value=value), self.assertRaises(ReachAdmissionError):
                ops._horner_sincos(value)
        marker = RuntimeError('cancel packed Horner recurrence')
        charge = ops.work.charge

        def cancelled(kind='checkpoint', amount=1):
            if kind == 'source_horner_integer_product':
                ops.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)

        with patch.object(ops.work, 'charge', side_effect=cancelled):
            with self.assertRaises(RuntimeError) as raised:
                ops._horner_sincos(F(7, 8))
        self.assertIs(raised.exception, marker)
        self.assertIs(ops.work.callback_error, marker)


if __name__ == '__main__':
    unittest.main()
