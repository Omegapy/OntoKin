"""Independent enclosures and lifecycle-facing properties of source poses."""
import copy
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError,ReachExecutionWork,float_bits
from ontokin.reach_pose import (
    ARGUMENT_ERROR,AXIS_ERROR,EXPOSED_ROTATION_ERROR,PRODUCT_ERROR,TRIG_ERROR,
    VECTOR_ERROR,ReachPoseOps,source_numeric_basis,uniform_source_bounds,
)


def independent_oracle():
    name="ontokin_test_independent_reach_pose_oracle"
    if name not in sys.modules:
        source=Path(__file__).resolve().parents[1]/"docs/language-design/planar-reach-v0.1/interval_oracle.py"
        spec=importlib.util.spec_from_file_location(name,source)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
    return sys.modules[name]


class ReachPoseTests(unittest.TestCase):
    def test_horner_and_reduction_match_independent_enclosures(self):
        oracle=independent_oracle()
        ops=ReachPoseOps(ReachExecutionWork())
        for angle in (F(-7),F(-3),F(-1),F(-1,3),F(0),F(1,3),F(1),F(3),F(7)):
            with self.subTest(angle=angle):
                sine,cosine=ops.sincos(angle)
                context=oracle.Context(192,oracle.Budget())
                expected=context.sincos_point(angle)
                for actual,enclosure in zip((sine,cosine),expected):
                    self.assertLessEqual(actual-TRIG_ERROR,enclosure.lo)
                    self.assertGreaterEqual(actual+TRIG_ERROR,enclosure.hi)

    def test_horner_bound_is_exact_and_uniform(self):
        factorial=1
        for k in range(1,41): factorial*=k
        self.assertLess(ARGUMENT_ERROR+F(21,1<<97)+F(1,factorial),TRIG_ERROR)

    def test_projective_rotation_and_inverse_avoid_public_round_trip(self):
        ops=ReachPoseOps(ReachExecutionWork())
        first=ops.make((1,2,3),(2,1,0,0))
        second=ops.make((F(1,3),F(2,7),F(-5,11)),(1,0,1,0))
        combined=ops.compose(first,second)
        recovered=ops.relative_point(first,combined)
        for actual,expected in zip(recovered,second.exact_position):
            self.assertLess(abs(actual-expected),8*VECTOR_ERROR)
        # Reading public projections must not alter subsequent private results.
        before=combined.exact_position,combined.rotation.components
        _=first.position,first.orientation,combined.orientation
        again=ops.compose(first,second)
        self.assertEqual(before,(again.exact_position,again.rotation.components))

    def test_hinge_velocity_uses_exact_rate_before_projection(self):
        ops=ReachPoseOps(ReachExecutionWork())
        rate=F(1,3)
        hinge=ops.hinge_pose((0,0,1),F(0),rate)
        self.assertEqual(hinge.exact_omega,(F(0),F(0),rate))
        end=ops.compose(hinge,ops.make((3,0,0)))
        self.assertEqual(end.velocity,(0.,1.,0.))
        self.assertEqual(hinge.omega,(0.,0.,float(rate)))

    def test_affine_and_parabolic_keep_exact_clock_until_public_boundary(self):
        ops=ReachPoseOps(ReachExecutionWork())
        position=ops.parabolic((1,2,3),(F(1,7),0,0),(0,F(-1,3),0),F(1,5))
        self.assertEqual(position,(F(36,35),F(299,150),F(3)))
        pose=ops.make(position)
        self.assertEqual(pose.position,tuple(map(float,position)))

    def test_spin_phase_is_uniform_and_bound_to_velocity(self):
        ops=ReachPoseOps(ReachExecutionWork())
        plan=ops.spin_plan((0,0,2),10)
        self.assertLessEqual(plan.argument_error_rad,ARGUMENT_ERROR)
        oracle=independent_oracle()
        for elapsed in (F(0),F(1,7),F(1),F(3)):
            rotation=ops.spin_rotation((0,0,2),elapsed,phase_plan=plan)
            point=ops.rotate(rotation,(1,0,0))
            expected=oracle.Context(192,oracle.Budget()).sincos_point(2*elapsed)
            for actual,enclosure in ((point[0],expected[1]),(point[1],expected[0])):
                self.assertLessEqual(actual-AXIS_ERROR,enclosure.lo)
                self.assertGreaterEqual(actual+AXIS_ERROR,enclosure.hi)
        with self.assertRaises(ReachAdmissionError):
            ops.spin_rotation((0,0,2),11,phase_plan=plan)
        with self.assertRaises(ReachAdmissionError):
            ops.spin_rotation((0,0,3),1,phase_plan=plan)

    def test_finite_reduction_does_not_call_host_transcendentals(self):
        ops=ReachPoseOps(ReachExecutionWork())
        with patch("math.sin",side_effect=AssertionError("host sin")), \
             patch("math.cos",side_effect=AssertionError("host cos")), \
             patch("math.hypot",side_effect=AssertionError("host hypot")), \
             patch("math.sqrt",side_effect=AssertionError("host sqrt")):
            self.assertEqual(ops.make(orientation=ops.axis_rotation((0,0,1),1)).orientation[1],0.)
        with self.assertRaises(ReachAdmissionError) as raised:
            ops.sincos(F(1 << 2000))
        self.assertEqual(raised.exception.reach_code,"reach_numeric")

    def test_materialized_release_anchor_preserves_every_exposed_bit(self):
        ops=ReachPoseOps(ReachExecutionWork())
        pose=ops.make((F(1,7),F(2,11),0),ops.axis_rotation((1,2,3),F(7,11)),
                      (F(1,3),2,3),(0,0,F(1,7)))
        anchor=ops.materialize(pose)
        self.assertIs(copy.deepcopy(anchor),anchor)
        for name in ("position","orientation","velocity","omega"):
            self.assertEqual(tuple(map(float_bits,getattr(anchor,name))),tuple(map(float_bits,getattr(pose,name))))
        advanced=ops.make(anchor.exact_position,
            ops.advance_orientation(anchor.rotation,anchor.exact_omega,F(0)),
            anchor.exact_velocity,anchor.exact_omega)
        self.assertEqual(tuple(map(float_bits,advanced.orientation)),tuple(map(float_bits,anchor.orientation)))

    def test_uniform_bounds_charge_coordinate_and_anchor_discrepancies(self):
        work=ReachExecutionWork()
        arguments=dict(max_position_l1_m=10,path_offset_l1_m=8,trig_count=3,
            product_count=12,vector_round_count=8,coordinate_angle_error_rad=F(1,1<<51),
            anchor_position_error_m=F(1,10**20),anchor_rotation_error_rad=F(1,10**21),
            radius_m=2,work=work)
        result=uniform_source_bounds(**arguments)
        rotation=F(1,10**21)+F(1,1<<51)+3*AXIS_ERROR+12*PRODUCT_ERROR
        position=F(1,10**20)+8*rotation+8*VECTOR_ERROR+F(10,1<<53)+F(3,1<<1075)
        self.assertEqual(result["rotation_rad"],rotation+EXPOSED_ROTATION_ERROR)
        self.assertEqual(result["position_m"],position)
        self.assertEqual(result["point_m"],position+2*result["rotation_rad"])
        self.assertEqual(result["proper_rotation_defect"],0)
        arguments["anchor_position_error_m"]=F(-1)
        with self.assertRaises(ReachAdmissionError): uniform_source_bounds(**arguments)

    def test_basis_identifies_current_sources_and_derivation(self):
        work=ReachExecutionWork()
        basis=source_numeric_basis(work=work)
        self.assertEqual(len(basis.inputs),4)
        self.assertEqual(set(basis.as_dict()),{"name","version","implementation","method","derivation"})
        before=work.operations
        self.assertIs(source_numeric_basis(work=work),basis)
        self.assertGreater(work.operations,before)

    def test_pose_cancellation_propagates_without_partial_publication(self):
        marker=RuntimeError("cancel controlled pose")
        calls=0
        def check():
            nonlocal calls
            calls+=1
            if calls==60: raise marker
        ops=ReachPoseOps(ReachExecutionWork(check=check))
        with self.assertRaises(RuntimeError) as raised:
            ops.axis_rotation((1,2,3),F(1,3))
        self.assertIs(raised.exception,marker)
        self.assertEqual(calls,60)


if __name__=="__main__": unittest.main()
