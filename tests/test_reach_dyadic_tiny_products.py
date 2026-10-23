"""Exact fixed cells omit integer work without changing a series schedule."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import (
    AdmissionWork, DyadicContext, Interval, PRECISIONS,
    ReachAdmissionError, ReachExecutionWork,
)


def original_product(context, a, b):
    """Independent full-corner directed result, without optimized branches."""
    values = [F(x*y, context.scale) for x in (a.lo,a.hi) for y in (b.lo,b.hi)]
    lo,hi = min(values),max(values)
    return Interval(lo.numerator//lo.denominator,-((-hi.numerator)//hi.denominator))


class ReachDyadicTinyProductTests(unittest.TestCase):
    def test_exact_four_corner_cells_for_all_precisions_and_support_edges(self):
        for precision in PRECISIONS:
            context=DyadicContext(precision,ReachExecutionWork())
            s=context.scale
            factors=(Interval(0,1),Interval(1,1),Interval(0,s//4),
                     Interval(s//3,s//2),Interval(s-1,s),Interval(s,s),
                     Interval(0,0),Interval(-1,1),Interval(-s,0),
                     Interval(0,s+1),Interval(2,1))
            for tiny in (Interval(0,1),Interval(-1,0)):
                for factor in factors:
                    for a,b in ((tiny,factor),(factor,tiny)):
                        with self.subTest(precision=precision,a=a,b=b):
                            self.assertEqual(context.mul(a,b),original_product(context,a,b))

    def test_only_actual_integer_constituents_are_omitted(self):
        work=ReachExecutionWork(); admission=work.admission()
        context=DyadicContext(96,admission)
        for tiny in (Interval(0,1),Interval(-1,0)):
            before=dict(work.counts)
            self.assertEqual(context.mul(tiny,Interval(1,context.scale//4)),tiny)
            self.assertEqual(work.counts['interval']-before.get('interval',0),1)
            self.assertEqual(work.counts.get('interval_constituent',0)-before.get('interval_constituent',0),0)
        self.assertEqual(admission.interval_operations,2)
        self.assertEqual(work.operations,sum(work.counts.values()))
        self.assertFalse(work._cache)

    def test_complete_original_operand_and_width_guards_survive(self):
        for cap,factor in ((64,Interval(0,1<<96)),(97,Interval(1,1<<96)),
                           (96,Interval(1,1<<95))):
            context=DyadicContext(96,ReachExecutionWork(max_operand_bits=cap))
            with self.subTest(cap=cap),self.assertRaises(ReachAdmissionError) as raised:
                context.mul(Interval(0,1),factor)
            self.assertEqual(raised.exception.details['budget'],'numeric_operand_bits')

    def test_callback_narrowing_and_cancellation_are_not_hidden(self):
        work=ReachExecutionWork(); context=DyadicContext(96,work)
        def narrow(): work.max_operand_bits=64
        work.external_check=narrow
        with self.assertRaises(ReachAdmissionError) as raised:
            context.mul(Interval(-1,0),Interval(1,context.scale//4))
        self.assertEqual(raised.exception.details['budget'],'numeric_operand_bits')
        marker=RuntimeError('cancel exact tiny product')
        def cancel(): raise marker
        work=ReachExecutionWork(check=cancel); context=DyadicContext(96,work)
        with self.assertRaises(RuntimeError) as raised:
            context.mul(Interval(0,1),Interval(1,context.scale//4))
        self.assertIs(raised.exception,marker)
        self.assertIs(work.callback_error,marker)

    def test_callback_replaced_cells_or_scale_retain_ordinary_result(self):
        for mutation in ('factor','tiny','scale'):
            work=ReachExecutionWork(); context=DyadicContext(96,work)
            tiny,factor=Interval(0,1),Interval(1,context.scale//4)
            captured_tiny,captured_factor=Interval(tiny.lo,tiny.hi),Interval(factor.lo,factor.hi)
            changed=False
            def change():
                nonlocal changed
                if changed: return
                changed=True
                if mutation=='factor': object.__setattr__(factor,'hi',context.scale*2)
                elif mutation=='tiny': object.__setattr__(tiny,'hi',3)
                else: context.scale//=4
            work.external_check=change
            with self.subTest(mutation=mutation):
                result=context.mul(tiny,factor)
                self.assertEqual(result,original_product(context,captured_tiny,captured_factor))
                self.assertIsNot(result,tiny)

    def test_foreign_cells_do_not_borrow_the_fixed_cell_proof(self):
        class Foreign(Interval): pass
        class Integer(int): pass
        context=DyadicContext(96,ReachExecutionWork())
        for a,b in ((Foreign(0,1),Interval(1,3)),
                    (Interval(Integer(0),Integer(1)),Interval(1,3))):
            before=context.work.counts.get('interval_constituent',0)
            self.assertEqual(context.mul(a,b),original_product(context,a,b))
            self.assertEqual(context.work.counts['interval_constituent']-before,8)

    def test_actual_atan_cells_degrees_and_remainder_equal_full_corner_control(self):
        # The previous production monotone-corner path has the same integer
        # cells as the independently expanded four-corner expression below.
        for value in (F(1,239),F(1,5),-F(1,5),F(1,2),F(1,1<<200)):
            work=ReachExecutionWork(); admission=work.admission()
            context=DyadicContext(96,admission)
            actual=context.atan_small(value)
            expected_terms=(96+5)//2
            self.assertEqual(admission.series_terms,expected_terms)
            original=DyadicContext(96,ReachExecutionWork().admission())
            with patch.object(original,'mul',side_effect=lambda a,b:original_product(original,a,b)):
                expected=original.atan_small(value)
            with self.subTest(value=value): self.assertEqual(actual,expected)
            self.assertEqual(original.work.series_terms,expected_terms)


if __name__=='__main__': unittest.main()
