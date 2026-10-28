"""Integer interval extrema preserve every original outward cell and guard."""
from fractions import Fraction as F
import unittest

from ontokin.reach_numeric import (
    DyadicContext, Interval, PRECISIONS, ReachAdmissionError, ReachExecutionWork, _Refine,
)


def floor(value):
    return value.numerator // value.denominator


def ceil(value):
    return -((-value.numerator) // value.denominator)


class LabelledWork(ReachExecutionWork):
    def charge(self, kind="checkpoint", amount=1):
        previous = getattr(self, "kind", None)
        self.kind = kind
        try:
            return super().charge(kind, amount)
        finally:
            self.kind = previous


class ReachDyadicCornerTests(unittest.TestCase):
    def test_all_signs_points_and_zero_edges_match_all_four_exact_corners(self):
        for precision in PRECISIONS:
            work = ReachExecutionWork()
            admission = work.admission()
            context = DyadicContext(precision, admission)
            scale = context.scale
            endpoints = (-3*scale, -scale-1, -scale, -1, 0, 1, scale, scale+1, 3*scale)
            cells = [Interval(low, high) for index, low in enumerate(endpoints)
                     for high in endpoints[index:]]
            calls = 0
            for a in cells:
                for b in cells:
                    with self.subTest(precision=precision, a=a, b=b):
                        products = [F(x*y, scale) for x in (a.lo,a.hi) for y in (b.lo,b.hi)]
                        self.assertEqual(context.mul(a,b), Interval(floor(min(products)), ceil(max(products))))
                        calls += 1
                        if not b.lo <= 0 <= b.hi:
                            ratios = [F(x*scale,y) for x in (a.lo,a.hi) for y in (b.lo,b.hi)]
                            self.assertEqual(context.div(a,b), Interval(floor(min(ratios)), ceil(max(ratios))))
                            calls += 1
                squares = [F(a.lo*a.lo,scale), F(a.hi*a.hi,scale)]
                low = F(0) if a.lo <= 0 <= a.hi else min(squares)
                self.assertEqual(context.square(a), Interval(floor(low), ceil(max(squares))))
                calls += 1
            self.assertEqual(admission.interval_operations, calls)
            self.assertEqual(work.operations, sum(work.counts.values()))
            self.assertLess(work.operations, 100000)
            self.assertFalse(work._cache)

    def test_removed_corners_reduce_actual_constituents_without_removing_interval_charges(self):
        work = ReachExecutionWork()
        context = DyadicContext(96, work)
        unit = Interval(context.scale,context.scale)
        zero = Interval(0,0)
        positive, negative, crossing = Interval(1,3), Interval(-5,-2), Interval(-2,7)
        probes = (("mul",(positive,negative),4), ("mul",(unit,positive),0),
                  ("mul",(zero,negative),0), ("mul",(Interval(3,3),Interval(-2,-2)),3),
                  ("div",(crossing,negative),4), ("div",(positive,unit),0),
                  ("square",(crossing,),2), ("square",(Interval(-2,-2),),3))
        for name,args,units in probes:
            before = dict(work.counts)
            getattr(context,name)(*args)
            self.assertEqual(work.counts["interval"]-before.get("interval",0),1)
            self.assertEqual(work.counts.get("interval_constituent",0)-before.get("interval_constituent",0),units)

    def test_zero_identity_and_selected_corners_keep_the_complete_original_width_guard(self):
        for operation in ("zero_product", "identity_product", "zero_division", "selected_product", "square"):
            work = ReachExecutionWork(max_operand_bits=128)
            context = DyadicContext(96, work)
            zero, unit = Interval(0,0), Interval(context.scale,context.scale)
            wide = Interval(1 << 100, 1 << 100)
            with self.subTest(operation=operation):
                if operation == "zero_product":
                    # Input itself is too wide even though its product is zero.
                    call = lambda: context.mul(zero, Interval(1 << 200,1 << 200))
                elif operation == "identity_product":
                    call = lambda: context.mul(unit,wide)
                elif operation == "zero_division":
                    call = lambda: context.div(zero,Interval(1 << 200,1 << 200))
                elif operation == "selected_product":
                    call = lambda: context.mul(wide,wide)
                else:
                    call = lambda: context.square(wide)
                with self.assertRaises(ReachAdmissionError) as caught:
                    call()
                self.assertEqual(caught.exception.reach_code,"reach_resource")
                self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")

    def test_constituent_callbacks_cannot_narrow_the_domain_after_preflight(self):
        for operation in ("mul","div","square"):
            work = LabelledWork()
            context = DyadicContext(96,work)
            cell = Interval(context.scale,context.scale+1)
            def narrow():
                if work.kind == "interval_constituent":
                    work.max_operand_bits = 64
            work.external_check = narrow
            with self.subTest(operation=operation), self.assertRaises(ReachAdmissionError) as caught:
                getattr(context,operation)(cell,*(() if operation == "square" else (cell,)))
            self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")
            self.assertEqual(work.max_operand_bits,64)

    def test_cancellation_and_constituent_budget_failures_never_return_a_result(self):
        for stage in ("interval","interval_constituent"):
            work = LabelledWork()
            context = DyadicContext(96,work)
            marker = RuntimeError("cancel an actual interval constituent")
            def cancel():
                if work.kind == stage:
                    raise marker
            work.external_check = cancel
            with self.assertRaises(RuntimeError) as caught:
                context.mul(Interval(1,3),Interval(2,4))
            self.assertIs(caught.exception,marker)
            self.assertIs(work.callback_error,marker)
        work = ReachExecutionWork(max_operations=2)
        context = DyadicContext(96,work)
        with self.assertRaises(ReachAdmissionError) as caught:
            context.div(Interval(1,3),Interval(2,4))
        self.assertEqual(caught.exception.details,{"reach_code":"reach_resource",
            "budget":"max_operations","limit":2,"consumed":3})
        self.assertEqual(work.operations,2)

    def test_zero_denominators_and_unordered_internal_cells_keep_the_original_path(self):
        context = DyadicContext(96,ReachExecutionWork())
        for denominator in (Interval(0,0),Interval(-1,1),Interval(0,1),Interval(-1,0)):
            with self.assertRaises(_Refine):
                context.div(Interval(0,0),denominator)
        a,b = Interval(7,-2),Interval(-3,5)
        products = [x*y for x in (a.lo,a.hi) for y in (b.lo,b.hi)]
        self.assertEqual(context.mul(a,b),Interval(min(products)//context.scale,
            -((-max(products))//context.scale)))


if __name__ == "__main__":
    unittest.main()
