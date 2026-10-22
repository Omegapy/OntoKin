"""Actual endpoint conversions share only identical independent operands."""
from fractions import Fraction as F
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin import reach_export as export
from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.scene import ExportOptions


def original_endpoint(position, quaternion, model, *, work):
    """The preceding scalar implementation, retained as a differential control."""
    work.charge("recording_endpoint_domain")
    if (len(position) != 3 or len(quaternion) != 4 or
            any(type(v) is not float or not math.isfinite(v) for v in (*position, *quaternion))):
        raise ValueError("Invalid endpoint")
    work.guard_bits(1075)
    def calculate():
        stored_p = export._stored_vector(position, model)
        stored_q = export._stored_vector(quaternion, model)
        if not any(stored_q):
            export._fail("OKE-E-QUATERNION", "Zero quaternion", model=model)
        ep = export._sum((export._rational(abs(a-b), work) for a,b in zip(position,stored_p)),work)
        large = max(abs(v) for v in quaternion) >= .5
        if not large:
            q = export._vector(quaternion, work, size=4)
            large = export._sum((export._exact(v,v,"mul",work) for v in q),work) >= F(1,4)
        if large:
            eq = export._exact(F(4),export._sum((export._rational(abs(a-b),work)
                for a,b in zip(quaternion,stored_q)),work),"mul",work)
        else:
            eq = export.norm_upper((export._exact(export._rational(a,work),export._rational(b,work),"sub",work)
                for a,b in zip(export.normalized_quaternion(q,work=work),
                               export.normalized_quaternion(stored_q,work=work))),work=work)
        eq = export._exact(eq,2*export.NORMALIZATION_ERROR,"add",work)
        magnitude = export._sum((export._rational(abs(v),work) for v in stored_p),work)
        return ep,eq,magnitude
    return export._reuse(work,("endpoint_rounding",position,quaternion),calculate)


class ReachEndpointReuseTests(unittest.TestCase):
    def test_exact_bounds_equal_previous_scalar_sequence(self):
        positions = ((0.,-0.,0.),(.1,-1.-2.**-24,2.**40),
                     (math.ulp(0.),-3*2.**-150,2.**-149),(.125,.25,.5))
        rotations = ((0.,0.,0.,1.),(.6,.8,0.,0.),(.5,-.5,.5,-.5),
                     (.3,-.3,.3,-.3),(.1,0.,0.,0.))
        for position in positions:
            for rotation in rotations:
                with self.subTest(position=position,rotation=rotation):
                    expected=original_endpoint(position,rotation,None,work=ReachExecutionWork())
                    actual=export._endpoint_rounding(position,rotation,None,work=ReachExecutionWork())
                    self.assertEqual(actual,expected)

    def test_translated_endpoints_reuse_rotation_but_preserve_distinct_errors(self):
        work=ReachExecutionWork();old_work=ReachExecutionWork()
        for index in range(32):
            position=(index+.1,0.,0.);rotation=(.6,.8,0.,0.)
            expected=original_endpoint(position,rotation,None,work=old_work)
            self.assertEqual(export._endpoint_rounding(position,rotation,None,work=work),expected)
        self.assertLess(work.operations,old_work.operations)
        self.assertEqual(sum(work.counts.values()),work.operations)
        self.assertLessEqual(len(work._cache),256)

    def test_sparse_sum_matches_exact_binary64_values(self):
        for values in ((0.,0.,0.),(math.ulp(0.),2.**-149,0.),(.1,.2,.3,.4)):
            self.assertEqual(export._endpoint_l1(values,work=ReachExecutionWork()),sum(map(F,values),F(0)))
        for invalid in ((False,0.,0.),(-1.,0.,0.),(math.inf,0.,0.),(0.,0.)):
            with self.assertRaises(ValueError):
                export._endpoint_l1(invalid,work=ReachExecutionWork())

    def test_warm_hit_rechecks_domain_and_callback_narrowing(self):
        position=(.1,0.,0.);rotation=(.6,.8,0.,0.)
        for narrow_during_lookup in (False,True):
            work=ReachExecutionWork()
            export._endpoint_rounding(position,rotation,None,work=work)
            if narrow_during_lookup:
                calls=0
                def narrow():
                    nonlocal calls
                    calls+=1
                    if calls==2:work.max_operand_bits=512
                work.external_check=narrow
            else:work.max_operand_bits=512
            with self.assertRaises(ReachAdmissionError):
                export._endpoint_rounding(position,rotation,None,work=work)

    def test_cancellation_at_each_first_call_charge_publishes_no_outer_result(self):
        position=(.1,0.,0.);rotation=(.6,.8,0.,0.)
        work=ReachExecutionWork();export._endpoint_rounding(position,rotation,None,work=work)
        for stop in range(1,work.operations+1):
            marker=RuntimeError("cancel endpoint");calls=0
            def cancel():
                nonlocal calls
                calls+=1
                if calls==stop:raise marker
            current=ReachExecutionWork(check=cancel)
            with self.assertRaises(RuntimeError) as caught:
                export._endpoint_rounding(position,rotation,None,work=current)
            self.assertIs(caught.exception,marker)
            self.assertFalse(any(key[1]=="endpoint_rounding" for key in current._cache))

    def test_lowered_operation_budget_still_stops_at_exact_limit(self):
        work=ReachExecutionWork(max_operations=3)
        with self.assertRaises(ReachAdmissionError) as caught:
            export._endpoint_rounding((.1,0.,0.),(.6,.8,0.,0.),None,work=work)
        self.assertEqual(caught.exception.details["consumed"],4)
        self.assertEqual(work.operations,3)

    def test_complete_p01_glb_bytes_equal_previous_endpoint_algorithm(self):
        root=Path(__file__).resolve().parents[1]
        def build():
            compiler=compile_construction(load_file_manifest(root/"docs/language-design/planar-reach-v0.1/p01.files.json"),level="constructed")
            result=export_glb(compiler.model,options=ExportOptions(end=F(3),fps=1,helpers=False),
                              target_contract="ontokin.glb/0.6",work=compiler.reach_work)
            return result,compiler.budget.operations
        current,current_cost=build()
        with patch.object(export,"_endpoint_rounding",new=original_endpoint):
            previous,previous_cost=build()
        self.assertEqual(current.data,previous.data)
        self.assertEqual(current.report["validation"],previous.report["validation"])
        self.assertLess(current_cost,previous_cost)


if __name__=="__main__":unittest.main()
