"""Exact dyadic identities keep cells, complete guards and callback boundaries."""
from contextlib import ExitStack
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_kinematics import admit_planar
from ontokin.reach_numeric import (
    DyadicContext, Interval, MAX_OPERAND_BITS, PRECISIONS,
    ReachAdmissionError, ReachExecutionWork, _Refine,
)
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def ordinary_point(context, value):
    """The preceding kernel, including its full prospective shift guard."""
    value = F(value)
    context._op(value, width=value.numerator.bit_length()+context.p+1, units=3)
    n, d = value.numerator << context.p, value.denominator
    return Interval(n//d, -((-n)//d))


def ordinary_div(context, a, b):
    """The preceding canonical and fallback kernels, in their original order."""
    width = max(abs(a.lo).bit_length(), abs(a.hi).bit_length())+context.p+1
    if context._canonical_cells(a, b) and not b.lo <= 0 <= b.hi:
        if a.lo == a.hi == 0 or b.lo == b.hi == context.scale:
            context._op(a.lo,a.hi,b.lo,b.hi,width=width,units=0)
            return a
        if b.lo > 0:
            pairs = (((a.lo,b.hi),(a.hi,b.lo)) if a.lo >= 0 else
                     ((a.lo,b.lo),(a.hi,b.hi)) if a.hi <= 0 else
                     ((a.lo,b.lo),(a.hi,b.lo)))
        else:
            pairs = (((a.hi,b.hi),(a.lo,b.lo)) if a.lo >= 0 else
                     ((a.hi,b.lo),(a.lo,b.hi)) if a.hi <= 0 else
                     ((a.hi,b.hi),(a.lo,b.hi)))
        context._op(a.lo,a.hi,b.lo,b.hi,width=width,units=4)
        (x,y),(z,w) = pairs
        return Interval((x*context.scale)//y, -((-(z*context.scale))//w))
    context._op(a.lo,a.hi,b.lo,b.hi,width=width,units=8)
    if b.lo <= 0 <= b.hi:
        raise _Refine("Interval denominator contains zero")
    lower, upper = [], []
    for x in (a.lo,a.hi):
        for y in (b.lo,b.hi):
            n, d = x*context.scale, y
            if d < 0:
                n, d = -n, -d
            lower.append(n//d)
            upper.append(-((-n)//d))
    return Interval(min(lower), max(upper))


class LabelledWork(ReachExecutionWork):
    def charge(self, kind="checkpoint", amount=1):
        previous = getattr(self, "kind", None)
        self.kind = kind
        try:
            return super().charge(kind, amount)
        finally:
            self.kind = previous


def outcome(call):
    try:
        return "value", call()
    except (ReachAdmissionError, _Refine, ZeroDivisionError) as error:
        return type(error), str(error), getattr(error, "details", None)


def ordinary_mode(enabled):
    stack = ExitStack()
    if enabled:
        stack.enter_context(patch.object(DyadicContext, "point", ordinary_point))
        stack.enter_context(patch.object(DyadicContext, "div", ordinary_div))
    return stack


class ReachDyadicIdentityTests(unittest.TestCase):
    def test_exact_points_match_preceding_cells_at_every_fixed_precision(self):
        for precision in PRECISIONS:
            values = [F(sign*odd, 1 << exponent)
                      for exponent in (0, 1, precision-1, precision)
                      for odd in (1, 3, 17) for sign in (-1, 1)]
            values += [0, 0.0, -0.0, 1.5, -1.5, 1.0/3.0]
            if precision >= 1074:
                tiny = float.fromhex("0x0.0000000000001p-1022")
                values += [tiny,-tiny]
            for value in values:
                with self.subTest(precision=precision, value=value):
                    current, preceding = ReachExecutionWork(), ReachExecutionWork()
                    actual = DyadicContext(precision, current).point(value)
                    expected = ordinary_point(DyadicContext(precision, preceding), value)
                    self.assertEqual(actual, expected)
                    self.assertEqual(actual.lo, actual.hi)
                    self.assertEqual(current.counts, {"interval": 1, "interval_constituent": 1})
                    self.assertEqual(preceding.operations-current.operations, 2)
                    self.assertFalse(current._cache)

    def test_inexact_and_foreign_points_keep_original_cells_and_charges(self):
        class ForeignInt(int):
            pass
        class ForeignFraction(F):
            pass
        for precision in PRECISIONS:
            values = [F(1,3), F(-7,9), F(1,1 << (precision+1)),
                      True, "1/2", ForeignInt(1), ForeignFraction(1,2)]
            if precision < 1074:
                values.append(float.fromhex("0x0.0000000000001p-1022"))
            for value in values:
                with self.subTest(precision=precision, value_type=type(value)):
                    current, preceding = ReachExecutionWork(), ReachExecutionWork()
                    self.assertEqual(DyadicContext(precision,current).point(value),
                                     ordinary_point(DyadicContext(precision,preceding),value))
                    self.assertEqual(current.counts, preceding.counts)

    def test_integer_divisors_match_every_sign_and_precision(self):
        for precision in PRECISIONS:
            scale = 1 << precision
            numerators = (Interval(2,19), Interval(-19,-2), Interval(-11,23),
                          Interval(17,17), Interval(-17,-17))
            for multiplier in (-7,-3,-2,-1,2,3,7):
                denominator = Interval(multiplier*scale, multiplier*scale)
                for numerator in numerators:
                    with self.subTest(precision=precision, a=numerator, multiplier=multiplier):
                        current, preceding = ReachExecutionWork(), ReachExecutionWork()
                        actual = DyadicContext(precision,current).div(numerator,denominator)
                        expected = ordinary_div(DyadicContext(precision,preceding),numerator,denominator)
                        self.assertEqual(actual, expected)
                        self.assertEqual(current.counts, {"interval":1,"interval_constituent":3})
                        self.assertEqual(preceding.operations-current.operations, 1)

    def test_tiny_signed_cells_keep_exact_outward_endpoints_without_quotients(self):
        for precision in PRECISIONS:
            scale = 1 << precision
            for multiplier in (2,3,7,10001):
                denominator = Interval(multiplier*scale, multiplier*scale)
                for numerator in (Interval(0,1), Interval(-1,0)):
                    current, preceding = ReachExecutionWork(), ReachExecutionWork()
                    actual = DyadicContext(precision,current).div(numerator,denominator)
                    self.assertEqual(actual, ordinary_div(DyadicContext(precision,preceding),
                                                          numerator,denominator))
                    self.assertEqual(actual, numerator)
                    self.assertIsNot(actual, numerator)
                    self.assertEqual(current.counts, {"interval":1})
                    self.assertEqual(preceding.operations-current.operations, 4)
            # Negative divisors change the sign; they use the general reduction.
            for numerator, expected in ((Interval(0,1),Interval(-1,0)),
                                         (Interval(-1,0),Interval(0,1))):
                work = ReachExecutionWork()
                self.assertEqual(DyadicContext(precision,work).div(numerator,Interval(-3*scale,-3*scale)),
                                 expected)
                self.assertEqual(work.counts["interval_constituent"], 3)

    def test_division_fallbacks_preserve_original_cells_failures_and_work(self):
        class ForeignInt(int):
            pass
        class ForeignInterval(Interval):
            pass
        scale = 1 << 96
        probes = ((Interval(-3,7),Interval(scale+1,scale+1)),
                  (Interval(-3,7),Interval(2*scale,3*scale)),
                  (Interval(0,1),Interval(scale+1,scale+1)),
                  (Interval(-1,0),Interval(2*scale,3*scale)),
                  (Interval(0,0),Interval(0,0)),
                  (Interval(2,3),Interval(-1,1)),
                  (Interval(7,-3),Interval(2*scale,2*scale)),
                  (ForeignInterval(-3,7),Interval(2*scale,2*scale)),
                  (Interval(ForeignInt(-3),7),Interval(2*scale,2*scale)))
        for numerator, denominator in probes:
            current, preceding = ReachExecutionWork(), ReachExecutionWork()
            self.assertEqual(outcome(lambda: DyadicContext(96,current).div(numerator,denominator)),
                             outcome(lambda: ordinary_div(DyadicContext(96,preceding),numerator,denominator)))
            self.assertEqual(current.counts, preceding.counts)

    def test_narrowed_and_foreign_domains_retain_original_work(self):
        class ForeignContext(DyadicContext):
            pass
        for context_type, cap in ((DyadicContext,128),(DyadicContext,2048),
                                  (DyadicContext,float(MAX_OPERAND_BITS)),
                                  (ForeignContext,MAX_OPERAND_BITS)):
            for operation in ("point","div","tiny"):
                histories = []
                for ordinary in (True,False):
                    work = ReachExecutionWork(max_operand_bits=cap if type(cap) is int else MAX_OPERAND_BITS)
                    work.max_operand_bits = cap
                    context = context_type(96,work)
                    if operation == "point":
                        result = (ordinary_point if ordinary else DyadicContext.point)(context,F(3,8))
                    else:
                        numerator = Interval(0,1) if operation == "tiny" else Interval(-3,7)
                        result = (ordinary_div if ordinary else DyadicContext.div)(
                            context,numerator,Interval(3*context.scale,3*context.scale))
                    histories.append((result,work.counts))
                self.assertEqual(*histories)

    def test_original_prospective_width_rejects_even_when_reduced_result_fits(self):
        for operation in ("point","div"):
            histories = []
            for ordinary in (True,False):
                work = ReachExecutionWork(max_operand_bits=97 if operation == "point" else 128)
                context = DyadicContext(96,work)
                if operation == "point":
                    call = lambda: (ordinary_point if ordinary else DyadicContext.point)(context,F(1,1 << 96))
                else:
                    call = lambda: (ordinary_div if ordinary else DyadicContext.div)(
                        context,Interval(1 << 80,1 << 80),Interval(2*context.scale,2*context.scale))
                result = outcome(call)
                self.assertIs(result[0], ReachAdmissionError)
                self.assertEqual(result[2]["budget"], "numeric_operand_bits")
                histories.append((result,work.counts))
            self.assertEqual(*histories)

    def test_callback_cap_changes_restore_complete_original_charges_and_rejections(self):
        for operation in ("point","div","tiny"):
            events = (("interval",1),("interval_constituent",1))
            if operation == "div":
                events += (("interval_constituent",2),("interval_constituent",3))
            if operation == "tiny":
                events = (("interval",1),)
            for event, occurrence in events:
                for cap in (64,128):
                    histories = []
                    for ordinary in (True,False):
                        work = LabelledWork()
                        context = DyadicContext(96,work)
                        calls = 0
                        def check():
                            nonlocal calls
                            if work.kind == event:
                                calls += 1
                                if calls == occurrence:
                                    work.max_operand_bits = cap
                        work.external_check = check
                        if operation == "point":
                            call = lambda: (ordinary_point if ordinary else DyadicContext.point)(context,F(3,8))
                        else:
                            a = Interval(0,1) if operation == "tiny" else Interval(-3,7)
                            b = Interval(3*context.scale,3*context.scale)
                            call = lambda: (ordinary_div if ordinary else DyadicContext.div)(context,a,b)
                        histories.append((outcome(call),dict(work.counts)))
                    with self.subTest(operation=operation,event=event,occurrence=occurrence,cap=cap):
                        self.assertEqual(*histories)

    def test_point_callback_precision_falls_back_and_copied_values_stay_isolated(self):
        for changed in ("precision","numerator","denominator"):
            histories = []
            for ordinary in (True,False):
                work = LabelledWork()
                context = DyadicContext(96,work)
                value = F(3,8)
                def check():
                    if work.kind == "interval_constituent":
                        if changed == "precision":
                            context.p = 97
                        else:
                            object.__setattr__(value,"_"+changed,5)
                work.external_check = check
                result = (ordinary_point if ordinary else DyadicContext.point)(context,value)
                histories.append((result,dict(work.counts)))
            self.assertEqual(histories[0][0],histories[1][0])
            if changed == "precision":
                self.assertEqual(histories[0][1],histories[1][1])
            else:
                # Both kernels first copy the caller's native Fraction. A
                # callback mutation of that caller object does not change the
                # admitted private value and needs no fallback calculation.
                self.assertEqual(histories[0][0],Interval(3 << 93,3 << 93))
                self.assertEqual(histories[0][1]["interval_constituent"],3)
                self.assertEqual(histories[1][1]["interval_constituent"],1)

    def test_division_callbacks_keep_original_scale_and_precaptured_cells(self):
        for changed in ("scale","precision","numerator_cells","denominator_cells"):
            for tiny in (False,True):
                histories = []
                for ordinary in (True,False):
                    work = LabelledWork()
                    context = DyadicContext(96,work)
                    a = Interval(0,1) if tiny else Interval(-3,7)
                    b = Interval(3*context.scale,3*context.scale)
                    def check():
                        if work.kind == "interval":
                            if changed == "scale":
                                context.scale = (1 << 96)+1
                            elif changed == "precision":
                                context.p = 97
                            elif changed == "numerator_cells":
                                object.__setattr__(a,"hi",19)
                            else:
                                object.__setattr__(b,"lo",context.scale)
                    work.external_check = check
                    result = (ordinary_div if ordinary else DyadicContext.div)(context,a,b)
                    histories.append((result,dict(work.counts)))
                self.assertEqual(histories[0][0],histories[1][0])
                if changed in ("scale","precision"):
                    self.assertEqual(histories[0][1],histories[1][1])

    def test_retained_callbacks_preserve_cancellation_identity_and_attempted_work(self):
        for operation, stages in (("point",(("interval",1),("interval_constituent",1))),
                                  ("div",(("interval",1),("interval_constituent",1),
                                          ("interval_constituent",2),("interval_constituent",3))),
                                  ("tiny",(("interval",1),))):
            for event, occurrence in stages:
                histories = []
                for ordinary in (True,False):
                    work = LabelledWork()
                    context = DyadicContext(96,work)
                    marker = RuntimeError("cancel retained dyadic arithmetic")
                    calls = 0
                    def check():
                        nonlocal calls
                        if work.kind == event:
                            calls += 1
                            if calls == occurrence:
                                raise marker
                    work.external_check = check
                    with self.assertRaises(RuntimeError) as caught:
                        if operation == "point":
                            (ordinary_point if ordinary else DyadicContext.point)(context,F(3,8))
                        else:
                            a = Interval(0,1) if operation == "tiny" else Interval(-3,7)
                            (ordinary_div if ordinary else DyadicContext.div)(
                                context,a,Interval(3*context.scale,3*context.scale))
                    self.assertIs(caught.exception,marker)
                    self.assertIs(work.callback_error,marker)
                    histories.append(dict(work.counts))
                self.assertEqual(*histories)

    def test_admission_fallback_cancellation_keeps_one_original_counter_batch(self):
        for operation, stop in (("point",2),("point",3),("div",4)):
            histories = []
            for ordinary in (True,False):
                work = LabelledWork()
                admission = work.admission()
                context = DyadicContext(96,admission)
                marker = RuntimeError("cancel restored ordinary constituent")
                calls = 0
                def check():
                    nonlocal calls
                    if work.kind == "interval_constituent":
                        calls += 1
                        if calls == 1:
                            work.max_operand_bits = 128
                        if calls == stop:
                            raise marker
                work.external_check = check
                with self.assertRaises(RuntimeError) as caught:
                    if operation == "point":
                        (ordinary_point if ordinary else DyadicContext.point)(context,F(3,8))
                    else:
                        (ordinary_div if ordinary else DyadicContext.div)(
                            context,Interval(-3,7),Interval(3*context.scale,3*context.scale))
                self.assertIs(caught.exception,marker)
                self.assertEqual(admission.exact_operations,0)
                histories.append((dict(work.counts),admission.record()))
            self.assertEqual(*histories)

    def test_admission_parent_change_keeps_the_original_bound_charge_owner(self):
        for operation in ("point","div"):
            histories = []
            for ordinary in (True,False):
                work, replacement = LabelledWork(), ReachExecutionWork()
                admission = work.admission()
                context = DyadicContext(96,admission)
                def check():
                    if work.kind == "interval_constituent":
                        admission.parent = replacement
                work.external_check = check
                if operation == "point":
                    result = (ordinary_point if ordinary else DyadicContext.point)(context,F(3,8))
                else:
                    result = (ordinary_div if ordinary else DyadicContext.div)(
                        context,Interval(-3,7),Interval(3*context.scale,3*context.scale))
                histories.append((result,dict(work.counts),dict(replacement.counts),
                                  admission.exact_operations,admission.interval_operations))
            self.assertEqual(*histories)

    def test_actual_work_limits_and_logical_interval_counters_are_preserved(self):
        for operation, limit in (("point",1),("div",3)):
            work = ReachExecutionWork(max_operations=limit)
            context = DyadicContext(96,work)
            with self.assertRaises(ReachAdmissionError) as caught:
                if operation == "point":
                    context.point(F(3,8))
                else:
                    context.div(Interval(-3,7),Interval(3*context.scale,3*context.scale))
            self.assertEqual(caught.exception.details,{"reach_code":"reach_resource",
                "budget":"max_operations","limit":limit,"consumed":limit+1})
            self.assertEqual(work.operations,limit)
        work = ReachExecutionWork()
        admission = work.admission()
        for precision in PRECISIONS:
            context = DyadicContext(precision,admission)
            context.point(F(3,8))
            context.div(Interval(-3,7),Interval(3*context.scale,3*context.scale))
            context.div(Interval(0,1),Interval(3*context.scale,3*context.scale))
        self.assertEqual(admission.interval_operations,3*len(PRECISIONS))
        self.assertEqual(admission.exact_operations,4*len(PRECISIONS))
        self.assertEqual(admission.series_terms,0)
        self.assertEqual(work.operations,sum(work.counts.values()))
        self.assertFalse(work._cache)

    def test_actual_p16_and_p23_admissions_keep_bits_enclosures_and_residual_proofs(self):
        for case in ("P16","P23"):
            built = compile_construction(source_case(case),level="constructed")
            payload = next(action.reach for action in built.model.actions.values() if action.reach is not None)
            histories = []
            for ordinary in (True,False):
                work = ReachExecutionWork()
                with ordinary_mode(ordinary):
                    result = admit_planar(payload.lengths_m,payload.target_m,payload.branch,
                                          payload.limits_rad,work=work)
                histories.append((result,work))
            before, after = histories
            self.assertEqual(replace(before[0],work=()),replace(after[0],work=()))
            self.assertEqual({k:v for k,v in before[1].counts.items() if k != "interval_constituent"},
                             {k:v for k,v in after[1].counts.items() if k != "interval_constituent"})
            saved = before[1].counts["interval_constituent"]-after[1].counts["interval_constituent"]
            self.assertGreater(saved,0)
            self.assertEqual(before[1].operations-after[1].operations,saved)
            self.assertLessEqual(len(after[1]._cache),256)

    def test_actual_p16_prefix_keeps_complete_delivered_glb_bytes(self):
        outputs = []
        for ordinary in (True,False):
            built = compile_construction(source_case("P16"),level="constructed")
            with ordinary_mode(ordinary):
                result = export_glb(built.model,options=ExportOptions(end=F(1,4),fps=1,helpers=False),
                                    target_contract="ontokin.glb/0.6",work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"],"passed")
            self.assertLessEqual(built.budget.operations,100000)
            outputs.append(result.data)
        self.assertEqual(*outputs)


if __name__ == "__main__":
    unittest.main()
