"""Intrinsic exact coefficients keep the live scalar arithmetic admissions."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_conformance import _Bounds, _complete_inequality_values
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_conformance import algebra_record


def evaluate(work):
    record = algebra_record()
    quantities = {name: F(value) for name, value in record.items()
                  if not name.startswith("h_")}
    return _complete_inequality_values(F(1, 128), F(1, 128), quantities,
                                       F(.001), F(.001), _Bounds(work), None)


class CertificateCoefficientTests(unittest.TestCase):
    def test_exact_claims_need_no_repeated_intrinsic_value_decoding(self):
        work = Work()
        with patch.object(_Bounds, "value", side_effect=AssertionError("decoded an intrinsic coefficient")):
            actual = evaluate(work)
        record = algebra_record()
        self.assertEqual(actual, {"position_bound_m": F(record["total_position_bound_m"]),
                                  "rotation_bound_rad": F(record["total_rotation_bound_rad"])})
        self.assertGreater(work.counts["independent_exact_div"], 0)
        self.assertGreater(work.counts["independent_exact_mul"], 0)
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertEqual(work.record()["cache_entries"], 0)

    def test_intrinsic_coefficient_is_guarded_after_live_narrowing_before_division(self):
        work = Work()
        quantities = {name: F(value) for name, value in algebra_record().items()
                      if not name.startswith("h_")}
        calls = 0
        def narrow():
            nonlocal calls
            calls += 1
            work.max_operand_bits = 2 if calls == 1 else 32768
        work.external_check = narrow
        with patch.object(F, "__truediv__", side_effect=AssertionError("allocated forbidden division")):
            with self.assertRaises(ReachAdmissionError) as caught:
                _complete_inequality_values(F(1), F(1),
                    quantities, F(1), F(1), _Bounds(work), None)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["consumed"], 3)
        self.assertEqual(calls, 1)

    def test_every_remaining_arithmetic_callback_preserves_cancellation_identity(self):
        baseline = Work()
        evaluate(baseline)
        for fail_at in range(1, baseline.operations + 1):
            work, calls = Work(), 0
            marker = RuntimeError("cancel complete certificate arithmetic")
            def cancel():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    raise marker
            work.external_check = cancel
            with self.subTest(callback=fail_at), self.assertRaises(RuntimeError) as caught:
                evaluate(work)
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertEqual(work.record()["cache_entries"], 0)


if __name__ == "__main__":
    unittest.main()
