"""Fixed phase algebra retains guarded domains when exact identities collapse."""
from fractions import Fraction as F
import unittest

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import PhaseArithmetic


class PhaseArithmeticTests(unittest.TestCase):
    def test_exact_identities_preserve_values_and_admit_every_operand(self):
        arithmetic = PhaseArithmetic(ReachExecutionWork())
        for values in ((F(0),) * 8, (F(1),) * 8,
                       (F(0), F(-7, 11), F(0), F(3, 11)),
                       (F(1), F(-7, 11), F(1), F(3, 11)),
                       (F(1), F(0), F(-7, 11)),
                       (F(1),) * 9, (2, F(0), F(3))):
            with self.subTest(values=values):
                self.assertEqual(arithmetic.add(*values), sum(values, F(0)))
                expected = F(1)
                for value in values:
                    expected *= value
                self.assertEqual(arithmetic.mul(*values), expected)
        guarded = PhaseArithmetic(ReachExecutionWork(max_operand_bits=64))
        for method, values in ((guarded.add, (F(0), F(1 << 80))),
                               (guarded.mul, (F(0), F(1 << 80))),
                               (guarded.mul, (F(1), F(1, 1 << 80)))):
            with self.subTest(values=values), self.assertRaises(ReachAdmissionError):
                method(*values)

    def test_constant_result_preserves_the_original_callback(self):
        interruption = RuntimeError("cancelled before constant phase algebra")
        def check():
            raise interruption
        for method in ("add", "mul"):
            with self.subTest(method=method):
                arithmetic = PhaseArithmetic(ReachExecutionWork(check=check))
                with self.assertRaises(RuntimeError) as caught:
                    getattr(arithmetic, method)(F(0), F(1))
                self.assertIs(caught.exception, interruption)


if __name__ == "__main__":
    unittest.main()
