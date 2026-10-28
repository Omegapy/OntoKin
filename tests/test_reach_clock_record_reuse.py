"""Repeated interval clocks retain exact digits and live request guards."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_export import _interval_clock_record, rational_record
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork


class ReachIntervalClockReuseTests(unittest.TestCase):
    def test_actual_digits_and_fresh_rows_with_less_repeated_conversion(self):
        for value in (F(0), F(1, 288), F(3, 1 << 30), F(10**120 + 7, 10**119 + 3)):
            work = ReachExecutionWork()
            expected = rational_record(value, work=ReachExecutionWork())
            first = _interval_clock_record(value, work=work)
            first["numerator"] = "changed output row"
            before = work.operations
            with patch("ontokin.reach_export.rational_record", side_effect=AssertionError("digits already complete")):
                actual = _interval_clock_record(value, work=work)
            repeated = work.operations - before
            ordinary = ReachExecutionWork()
            self.assertEqual(rational_record(value, work=ordinary), expected)
            self.assertEqual(actual, expected)
            self.assertIsNot(first, actual)
            self.assertLess(repeated, ordinary.operations)
            self.assertLessEqual(len(work._cache), 256)

    def test_original_invalid_operands_and_sign_are_checked_before_reuse(self):
        for value in (True, "1", float("inf"), float("nan"), F(-1)):
            observed = []
            for operation in (rational_record, _interval_clock_record):
                work = ReachExecutionWork()
                with self.assertRaises(ValueError) as caught:
                    operation(value, work=work)
                observed.append((str(caught.exception), work.operations))
                self.assertFalse(work._cache)
            self.assertEqual(observed[0], observed[1])

    def test_warm_input_guard_still_refuses_a_narrower_live_domain(self):
        value = F(1 << 200, 3)
        work = ReachExecutionWork()
        _interval_clock_record(value, work=work)
        work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as caught:
            _interval_clock_record(value, work=work)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["limit"], 128)

    def test_lookup_and_publication_callbacks_keep_exact_failure_identity(self):
        for warm in (False, True):
            work, value = ReachExecutionWork(), F(1, 17)
            if warm:
                _interval_clock_record(value, work=work)
            previous = tuple(work._cache.items())
            marker = RuntimeError("cancel interval clock conversion")
            original = work.charge
            event = "cache_promote" if warm else "cache_insert"
            def cancel(kind="checkpoint", amount=1):
                if kind == event:
                    work.external_check = lambda: (_ for _ in ()).throw(marker)
                return original(kind, amount)
            with patch.object(work, "charge", side_effect=cancel):
                with self.assertRaises(RuntimeError) as caught:
                    _interval_clock_record(value, work=work)
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertEqual(tuple(work._cache.items()), previous)

    def test_callback_domain_change_rechecks_before_return_or_publication(self):
        for warm in (False, True):
            work, value = ReachExecutionWork(), F(1 << 200, 3)
            if warm:
                _interval_clock_record(value, work=work)
            original = work.charge
            event = "cache_promote" if warm else "cache_insert"
            def narrow(kind="checkpoint", amount=1):
                if kind == event:
                    work.external_check = lambda: setattr(work, "max_operand_bits", 128)
                return original(kind, amount)
            with patch.object(work, "charge", side_effect=narrow):
                with self.assertRaises(ReachAdmissionError) as caught:
                    _interval_clock_record(value, work=work)
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
            self.assertFalse(work._cache)


if __name__ == "__main__":
    unittest.main()
