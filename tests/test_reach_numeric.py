"""Independent arithmetic boundaries for the adopted production reach kernel."""
import math
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import (
    DyadicContext, ReachAdmissionError, ReachExecutionWork, SIGN, bits_float,
    float_bits, exact, round_binary64, sqrt_rational_binary64,
)


class ReachNumericTests(unittest.TestCase):
    def test_binary64_halfway_parity_and_subnormal_zero(self):
        work=ReachExecutionWork()
        for value,expected in ((F(1)+F(1,1<<53),1.0),
                               (F(1)+F(3,1<<53),math.nextafter(math.nextafter(1.0,2.0),2.0)),
                               (F(1,1<<1075),0.0),(-F(1,1<<1075),0.0),
                               (F(3,1<<1075),bits_float(2))):
            with self.subTest(value=value):
                self.assertEqual(float_bits(round_binary64(value,work=work)),float_bits(expected))

    def test_binary64_binade_edges_and_overflow(self):
        work=ReachExecutionWork()
        for value in (math.nextafter(2.0,0.0),2.0,math.nextafter(2.0,3.0),
                      bits_float(0x000FFFFFFFFFFFFF),bits_float(0x0010000000000000)):
            self.assertEqual(round_binary64(F(value),work=work),value)
            self.assertEqual(round_binary64(-F(value),work=work),-value)
        with self.assertRaises(ReachAdmissionError) as raised:
            round_binary64(F(1<<1024)-F(1<<970),work=work)
        self.assertEqual(raised.exception.reach_code,"reach_numeric")

    def test_exact_sqrt_rounding_and_midpoint_ties(self):
        work=ReachExecutionWork()
        for bits in (0,1,2,0x0010000000000000,0x3FF0000000000000,0x3FF0000000000001):
            value=bits_float(bits)
            self.assertEqual(float_bits(sqrt_rational_binary64(F(value)**2,work=work)),bits)
        low,high=F(1),F(math.nextafter(1.0,2.0))
        midpoint=(low+high)/2
        self.assertEqual(sqrt_rational_binary64(midpoint**2,work=work),1.0)
        epsilon=F(1,1<<160)
        self.assertEqual(sqrt_rational_binary64(midpoint**2+epsilon,work=work),float(high))

    def test_outward_integer_intervals_enclose_exact_arithmetic(self):
        context=DyadicContext(96,ReachExecutionWork())
        for a,b in ((F(1,3),F(2,7)),(-F(7,5),F(11,13)),(-F(1,2),-F(9,11))):
            for operation,expected in (("add",a+b),("sub",a-b),("mul",a*b),("div",a/b)):
                lo,hi=context.bounds(getattr(context,operation)(context.point(a),context.point(b)))
                self.assertLessEqual(lo,expected); self.assertGreaterEqual(hi,expected)
        lo,hi=context.bounds(context.sqrt_point(F(2)))
        self.assertLessEqual(lo*lo,2); self.assertGreaterEqual(hi*hi,2)

    def test_precharge_rejects_huge_product_before_multiplication(self):
        large=F(1<<20000)
        with patch.object(F,"__mul__",side_effect=AssertionError("unadmitted product executed")):
            with self.assertRaises(ReachAdmissionError) as raised:
                exact(large,large,"mul",ReachExecutionWork())
        self.assertEqual(raised.exception.reach_code,"reach_resource")
        self.assertEqual(raised.exception.details["budget"],"numeric_operand_bits")

    def test_shared_callback_charges_every_unit_without_bulk_bypass(self):
        seen=[]
        work=ReachExecutionWork(check=lambda:seen.append(1))
        work.charge("precharge",17)
        self.assertEqual(len(seen),17)
        self.assertEqual(work.operations,17)

    def test_guard_rejects_negative_integer_without_absolute_value_allocation(self):
        class OversizedInteger(int):
            def __abs__(self):
                raise AssertionError("oversized absolute value was allocated")
        value=OversizedInteger(-(1 << 40000))
        with self.assertRaises(ReachAdmissionError) as raised:
            ReachExecutionWork().guard(value)
        self.assertEqual(raised.exception.reach_code,"reach_resource")
        self.assertEqual(raised.exception.details["budget"],"numeric_operand_bits")

    def test_cancellation_preserves_original_exception_before_and_after_isqrt(self):
        import ontokin.reach_numeric as numeric
        marker=RuntimeError("caller cancellation")
        entered=False
        original=numeric.isqrt
        def sqrt(value):
            nonlocal entered
            result=original(value); entered=True
            return result
        def check():
            if entered: raise marker
        with patch.object(numeric,"isqrt",side_effect=sqrt):
            with self.assertRaises(RuntimeError) as raised:
                sqrt_rational_binary64(F(2),work=ReachExecutionWork(check=check))
        self.assertIs(raised.exception,marker)

    def test_admission_counters_never_reset_between_contexts(self):
        work=ReachExecutionWork(max_operations=100)
        admission=work.admission()
        for p in (96,192):
            DyadicContext(p,admission).point(F(1,3))
            admission.term()
        self.assertEqual(admission.interval_operations,2)
        self.assertEqual(admission.series_terms,2)
        self.assertGreater(work.operations,2)


if __name__=="__main__": unittest.main()
