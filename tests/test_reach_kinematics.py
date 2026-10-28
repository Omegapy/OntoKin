"""Frozen corpus bits, source arithmetic and failure ordering for production IK."""
from fractions import Fraction as F
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.reach_kinematics import (
    admit_planar, measured_residual_squared, rounded_sqrt, sample_pair,
)
from ontokin.reach_numeric import (
    DyadicContext, PI64_BITS, ReachAdmissionError, ReachExecutionWork,
    bits_float,float_bits,
)

PROPOSAL=Path(__file__).resolve().parents[1]/"docs/language-design/planar-reach-v0.1"
PI=bits_float(PI64_BITS)
LIMITS=((-PI,PI),(-PI,PI))


class ReachKinematicsTests(unittest.TestCase):
    def test_all_54_original_target_coordinates_keep_their_bits(self):
        corpus=json.loads((PROPOSAL/"acceptance.json").read_text())
        count=0
        for case in corpus["source_cases"]:
            expected=case["expected"].get("independent_solution",{})
            if "resolved_joint_targets_rad" not in expected: continue
            spec=case["specification"]
            with self.subTest(case=case["id"]):
                result=admit_planar(spec["lengths"],spec["target"],"elbow_"+spec["branch"],
                                    LIMITS,work=ReachExecutionWork())
                self.assertEqual(result.target_bits,tuple(map(float_bits,expected["resolved_joint_targets_rad"])))
                self.assertLessEqual(result.residual_squared_upper_m2,F(1,10**18))
                count+=2
        self.assertEqual(count,54)

    def test_geometric_rejections_are_exact_and_distinct(self):
        cases=(((1.,1.),(3.,0.,0.),"reach_unreachable"),
               ((2.,1.),(0.,0.,0.),"reach_unreachable"),
               ((1.,1.),(0.,0.,0.),"reach_singular"),
               ((1.,1.),(1.,0.,1e-300),"reach_frame"))
        for lengths,target,code in cases:
            with self.subTest(code=code):
                with self.assertRaises(ReachAdmissionError) as raised:
                    admit_planar(lengths,target,"elbow_positive",LIMITS,work=ReachExecutionWork())
                self.assertEqual(raised.exception.reach_code,code)

    def test_closed_limit_is_checked_before_any_residual_series(self):
        with patch.object(DyadicContext,"sincos_point",side_effect=AssertionError("residual ran before limit")):
            with self.assertRaises(ReachAdmissionError) as raised:
                admit_planar((1.,1.),(1.,1.,0.),"elbow_positive",((-PI,PI),(-PI,0.)),work=ReachExecutionWork())
        self.assertEqual(raised.exception.reach_code,"reach_limit")

    def test_cache_hit_rechecks_current_limits_and_cancellation(self):
        calls=0
        marker=RuntimeError("cancel cache hit")
        cancel=False
        def check():
            nonlocal calls
            calls+=1
            if cancel: raise marker
        work=ReachExecutionWork(check=check)
        result=admit_planar((1.,1.),(1.,1.,0.),"elbow_positive",LIMITS,work=work)
        before=work.operations
        again=admit_planar((1.,1.),(1.,1.,0.),"elbow_positive",LIMITS,work=work)
        self.assertEqual(result.target_bits,again.target_bits)
        self.assertLess(work.operations-before,200)
        with self.assertRaises(ReachAdmissionError) as raised:
            admit_planar((1.,1.),(1.,1.,0.),"elbow_positive",((-PI,PI),(-PI,0.)),work=work)
        self.assertEqual(raised.exception.reach_code,"reach_limit")
        cancel=True
        with self.assertRaises(RuntimeError) as interrupted:
            admit_planar((1.,1.),(1.,1.,0.),"elbow_positive",LIMITS,work=work)
        self.assertIs(interrupted.exception,marker)
        self.assertGreater(calls,work.operations)

    def test_lowered_shared_work_fails_without_partial_pair(self):
        with self.assertRaises(ReachAdmissionError) as raised:
            admit_planar((1.,1.),(1.,1.,0.),"elbow_positive",LIMITS,work=ReachExecutionWork(max_operations=50))
        self.assertEqual(raised.exception.reach_code,"reach_resource")

    def test_pair_uses_exact_clock_and_independent_exact_slope(self):
        duration=F(3)
        elapsed=F(1,3)
        start=(0.1,-0.3); goal=(1.7,0.9)
        result=sample_pair(start,goal,duration,elapsed,running=True,work=ReachExecutionWork())
        slopes=tuple((F(b)-F(a))/duration for a,b in zip(start,goal))
        expected=tuple(F(a)+s*elapsed for a,s in zip(start,slopes))
        self.assertEqual(result.exact_slopes,slopes)
        self.assertEqual(result.exact_coordinates,expected)
        self.assertEqual(result.coordinates_rad,tuple(map(float,expected)))
        paused=sample_pair(start,goal,duration,elapsed,running=False,work=ReachExecutionWork())
        self.assertEqual(paused.coordinates_rad,result.coordinates_rad)
        self.assertEqual(paused.rates_rad_s,(0.,0.))
        completed=sample_pair(start,goal,duration,duration,running=False,work=ReachExecutionWork())
        self.assertEqual(tuple(map(float_bits,completed.coordinates_rad)),tuple(map(float_bits,goal)))

    def test_measured_residual_uses_actual_coordinates(self):
        work=ReachExecutionWork()
        value=measured_residual_squared((1.,2.,3.),(1.,2.,2.),work=work)
        self.assertEqual(value,1)
        self.assertEqual(rounded_sqrt(value,work=work),1.)


if __name__=="__main__": unittest.main()
