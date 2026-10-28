"""A fresh zero bound needs no numerical cache or floating conversion."""
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_export as export
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork


class ReachZeroBoundProjectionTests(unittest.TestCase):
    def test_exact_zero_is_canonical_and_does_not_displace_request_proofs(self):
        work = ReachExecutionWork(max_cache_entries=1)
        work.remember(("retained-proof",), F(7, 9))
        before = tuple(work._cache.items())
        start = work.operations
        with patch.object(work, "lookup", side_effect=AssertionError("unneeded zero lookup")), \
                patch.object(work, "remember", side_effect=AssertionError("unneeded zero insertion")):
            for value in (0, F(0), 0.0, -0.0):
                result = export.upper_binary64(value, work=work)
                self.assertEqual(result, 0.0)
                self.assertEqual(math.copysign(1.0, result), 1.0)
        self.assertEqual(tuple(work._cache.items()), before)
        self.assertEqual(work.operations - start, 4)

    def test_current_inputs_and_narrowed_domains_retain_original_admission(self):
        for value in (False, True, None, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                export.upper_binary64(value, work=ReachExecutionWork())
        for during in (False, True):
            work = ReachExecutionWork(max_operand_bits=32768 if during else 32)
            if during:
                work.external_check = lambda: setattr(work, "max_operand_bits", 32)
            with self.subTest(during=during), self.assertRaises(ReachAdmissionError) as caught:
                export.upper_binary64(F(0), work=work)
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_cancellation_precedes_zero_and_preserves_original_exception(self):
        marker = RuntimeError("cancel zero-bound admission")
        def cancel():
            raise marker
        work = ReachExecutionWork(check=cancel)
        with self.assertRaises(RuntimeError) as caught:
            export.upper_binary64(F(0), work=work)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(work.operations, 0)

    def test_near_zero_nonzero_bounds_still_round_outward(self):
        for value in (F(1, 2**1074), F(1, 2**1075), F(1, 10**200), F(1, 3)):
            with self.subTest(value=value):
                work = ReachExecutionWork()
                result = export.upper_binary64(value, work=work)
                self.assertGreater(result, 0.0)
                self.assertGreaterEqual(F(result), value)
                if F(result) > value:
                    self.assertLess(F(math.nextafter(result, -math.inf)), value)
        with self.assertRaises(ValueError):
            export.upper_binary64(F(-1, 2**1075), work=ReachExecutionWork())


if __name__ == "__main__":
    unittest.main()
