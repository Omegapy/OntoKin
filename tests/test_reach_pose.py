"""Independent enclosures and lifecycle-facing properties of source poses."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import importlib.util
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError,ReachExecutionWork,float_bits
from ontokin.reach_pose import (
    ARGUMENT_ERROR,AXIS_ERROR,EXPOSED_ROTATION_ERROR,PRODUCT_ERROR,TRIG_ERROR,
    VECTOR_ERROR,ZERO,ReachPoseOps,source_numeric_basis,uniform_source_bounds,
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
        for k in range(1,27): factorial*=k
        self.assertLess(ARGUMENT_ERROR+F(1,1<<97)+F(1,factorial),TRIG_ERROR)

    def test_horner_grid_errors_match_independent_exact_polynomial_sums(self):
        ops=ReachPoseOps(ReachExecutionWork())
        rho=F(1,1<<97)
        points=(F(-1),F(-1)+2*rho,F(-3,4),F(-1,2),-2*rho,F(0),
                2*rho,F(1,2),F(3,4),F(1)-2*rho,F(1))
        for point in points:
            with self.subTest(point=point):
                sine,cosine=ops._horner_sincos(point)
                # Independent direct powers/exact sums and Python's Fraction
                # ties-to-even rounding, without the production recurrence.
                exact_sine=sum((F((-1)**k,math.factorial(2*k+1))*point**(2*k+1)
                                for k in range(13)),F(0))
                exact_cosine=sum((F((-1)**k,math.factorial(2*k))*point**(2*k)
                                  for k in range(13)),F(0))
                self.assertEqual(sine,F(round(exact_sine*(1<<96)),1<<96))
                self.assertEqual(cosine,F(round(exact_cosine*(1<<96)),1<<96))
                self.assertLessEqual(abs(sine-exact_sine),rho)
                self.assertLessEqual(abs(cosine-exact_cosine),rho)

    def test_exact_horner_prospective_widths_stay_inside_the_proved_bound(self):
        class ObservedWork(ReachExecutionWork):
            def __init__(self):
                super().__init__(max_operand_bits=2600)
                self.largest_guard=0
            def guard_bits(self,bits):
                self.largest_guard=max(self.largest_guard,bits)
                super().guard_bits(bits)
        work=ObservedWork()
        ops=ReachPoseOps(work)
        for point in (F(1,1<<96),F(1)-F(1,1<<96),F(-1)+F(1,1<<96),F(-1),F(1)):
            with self.subTest(point=point):
                result=ops._horner_sincos(point)
                self.assertTrue(all(value.denominator <= 1<<96 for value in result))
        self.assertGreater(work.largest_guard,2000)
        self.assertLessEqual(work.largest_guard,2582)
        self.assertEqual(sum(work.counts.values()),work.operations)

    def test_exact_horner_rejects_arguments_outside_its_proved_grid(self):
        for point in (F(1,3),F(1,1<<97),F(2),F(-2),0.5):
            with self.subTest(point=point):
                work=ReachExecutionWork()
                with self.assertRaises(ReachAdmissionError) as caught:
                    ReachPoseOps(work)._horner_sincos(point)
                self.assertEqual(caught.exception.reach_code,"reach_numeric")
                self.assertNotIn("source_series_recurrence",work.counts)

    def test_exact_horner_smaller_operand_budget_still_rejects_before_publication(self):
        work=ReachExecutionWork(max_operand_bits=512)
        with self.assertRaises(ReachAdmissionError) as caught:
            ReachPoseOps(work).sincos(F(1,1<<96))
        self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")
        self.assertGreater(caught.exception.details["consumed"],512)
        self.assertFalse(any(key[1]=="sincos" for key in work._cache))

    def test_reduced_series_encloses_grid_ties_and_range_seams(self):
        oracle=independent_oracle()
        rho=F(1,1<<97)
        points={rho,3*rho,F(1)-rho,F(1),F(1)+rho}
        for quadrant in (1,2,3,4):
            midpoint=F(math.pi)*quadrant/2
            points.update((midpoint-rho,midpoint,midpoint+rho))
        points.update(-point for point in tuple(points))
        ops=ReachPoseOps(ReachExecutionWork())
        for point in sorted(points):
            with self.subTest(point=point):
                actual=ops.sincos(point)
                context=oracle.Context(192,oracle.Budget())
                expected=context.sincos_point(point)
                for value,enclosure in zip(actual,expected):
                    self.assertLessEqual(value-TRIG_ERROR,enclosure.lo)
                    self.assertGreaterEqual(value+TRIG_ERROR,enclosure.hi)

    def test_horner_recurrences_remain_interruptible_without_cached_result(self):
        marker=RuntimeError("cancel inside source Horner arithmetic")
        def check():
            if work.counts.get("source_series_recurrence",0)==5:
                raise marker
        work=ReachExecutionWork(check=check)
        ops=ReachPoseOps(work)
        with self.assertRaises(RuntimeError) as raised:
            ops.sincos(F(1,3))
        self.assertIs(raised.exception,marker)
        self.assertIs(work.callback_error,marker)
        self.assertEqual(work.counts["source_series_recurrence"],5)
        self.assertEqual(sum(work.counts.values()),work.operations)
        self.assertFalse(any(key[1]=="sincos" for key in work._cache))

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

    def test_known_zero_derivatives_preserve_pose_bits_errors_and_reduce_work(self):
        results,costs={},{}
        for canonical in (False,True):
            work=ReachExecutionWork()
            ops=ReachPoseOps(work)
            rate=ZERO if canonical else tuple(F(0) for _ in range(3))
            parent=ops.make((F(1,3),2,F(-3,7)),(1,2,-3,4),rate,rate)
            local=ops.make((F(-2,5),F(3,11),F(7,13)),(2,-1,1,3),rate,rate)
            parent=replace(parent,position_error_m=F(1,1000))
            local=replace(local,position_error_m=F(1,2000))
            before=work.operations
            result=ops.compose(parent,local)
            costs[canonical]=work.operations-before
            results[canonical]=(result.exact_position,result.rotation,
                result.exact_velocity,result.exact_omega,result.position_error_m,
                *(tuple(map(float_bits,getattr(result,field)))
                  for field in ("position","orientation","velocity","omega")))
            self.assertEqual(result.exact_velocity,(F(0),)*3)
            self.assertEqual(result.exact_omega,(F(0),)*3)
            self.assertEqual(sum(work.counts.values()),work.operations)
        self.assertEqual(results[True],results[False])
        self.assertLess(costs[True],costs[False])

    def test_complete_composition_keeps_moving_spatial_derivatives(self):
        ops=ReachPoseOps(ReachExecutionWork())
        # The parent is an exact quarter-turn about z. Its moving local frame
        # therefore has independent, directly calculable spatial derivatives.
        parent=ops.make((2,3,4),(1,0,0,1),(1,2,3),(0,0,2))
        local=ops.make((F(1,4),F(-1,2),F(3,4)),(0,1,0,0),(3,-2,1),(4,5,-1))
        result=ops.compose(parent,local)
        self.assertEqual(result.exact_position,(F(5,2),F(13,4),F(19,4)))
        self.assertEqual(result.exact_velocity,(F(5,2),F(6),F(4)))
        self.assertEqual(result.exact_omega,(F(-5),F(4),F(1)))
        self.assertEqual(result.rotation.components,(F(0),F(1,2),F(1,2),F(0)))
        self.assertEqual(result.angular_error_rad,
                         parent.angular_error_rad+local.angular_error_rad+PRODUCT_ERROR)
        self.assertEqual(result.position_error_m,
                         F(3,2)*parent.angular_error_rad+2*VECTOR_ERROR)

    def test_zero_valued_invalid_derivatives_still_fail_input_validation(self):
        for owner in ("parent","local"):
            for field in ("exact_velocity","exact_omega"):
                for malformed in ((False,False,False),(F(0),F(0))):
                    with self.subTest(owner=owner,field=field,value=malformed):
                        # A fresh work cache ensures this exercises admission
                        # of the supplied malformed pose rather than a hit.
                        ops=ReachPoseOps(ReachExecutionWork())
                        parent=ops.make((1,2,3),(1,0,0,1))
                        local=ops.make((F(1,4),F(1,2),F(3,4)))
                        if owner=="parent": parent=replace(parent,**{field:malformed})
                        else: local=replace(local,**{field:malformed})
                        with self.assertRaises(ReachAdmissionError):
                            ops.compose(parent,local)

    def test_known_zero_composition_remains_interruptible_before_publication(self):
        marker=RuntimeError("cancel zero-derivative composition")
        active=False
        def check():
            if active and work.counts.get("composition_operand_guard",0):
                raise marker
        work=ReachExecutionWork(check=check)
        ops=ReachPoseOps(work)
        parent=ops.make((1,2,3),(1,0,0,1))
        local=ops.make((F(1,4),F(1,2),F(3,4)))
        active=True
        with self.assertRaises(RuntimeError) as raised:
            ops.compose(parent,local)
        self.assertIs(raised.exception,marker)
        self.assertIs(work.callback_error,marker)
        self.assertFalse(any(key[1] in ("relative_composition","stationary_composition")
                             for key in work._cache))

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
        self.assertEqual(tuple(name for name,_ in basis.inputs),(
            "ontokin/reach_numeric.py","ontokin/reach_kinematics.py","ontokin/reach_pose.py",
            "ontokin/reach_phase.py","ontokin/reach_runtime.py",
            "docs/engineering/reach-numeric-kernel.md","docs/engineering/reach-source-kernel.md"))
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

    def test_sparse_paths_preserve_dense_exact_product_and_grid_rotation(self):
        from ontokin.reach_pose import RotationValue
        ops=ReachPoseOps(ReachExecutionWork())
        def grid(value): return F(round(value*(1<<96)),1<<96)
        def rescale(values):
            maximum=max(map(abs,values)); exponent=maximum.numerator.bit_length()-maximum.denominator.bit_length()
            power=F(1<<exponent) if exponent>=0 else F(1,1<<-exponent)
            if maximum<power: exponent-=1
            shift=-exponent-1
            factor=F(1<<shift) if shift>=0 else F(1,1<<-shift)
            result=tuple(grid(value*factor) for value in values)
            return tuple(-v for v in result) if next(v for v in result if v)<0 else result
        rotations=((F(1),F(0),F(0),F(0)),(F(3,4),F(0),F(0),F(0)),
                   (F(1,3),F(0),F(0),F(2,7)),(F(-1,3),F(2,7),F(0),F(0)),
                   (F(1,3),F(0),F(-2,7),F(0)),(F(0),F(0),F(0),F(-2,7)),
                   (F(3,5),F(2,11),F(-1,13),F(1,1<<1074)))
        for a in rotations:
            for b in rotations:
                aw,ax,ay,az=a; bw,bx,by,bz=b
                product=(aw*bw-ax*bx-ay*by-az*bz,aw*bx+ax*bw+ay*bz-az*by,
                         aw*by-ax*bz+ay*bw+az*bx,aw*bz+ax*by-ay*bx+az*bw)
                self.assertEqual(ops.multiply(RotationValue(a),RotationValue(b)).components,rescale(product))
            w,x,y,z=a; denominator=sum(v*v for v in a)
            rows=((denominator-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)),
                  (2*(x*y+w*z),denominator-2*(x*x+z*z),2*(y*z-w*x)),
                  (2*(x*z-w*y),2*(y*z+w*x),denominator-2*(x*x+y*y)))
            for vector in ((F(0),)*3,(F(1,1<<1074),F(1,3),F(-7,11)),
                           (F(1,3),F(0),F(0)),(F(0),F(-7,11),F(0)),
                           (F(0),F(0),F(1,1<<97)),(F(0),F(1,3),F(-7,11))):
                expected=tuple(grid(sum(a*b for a,b in zip(row,vector))/denominator) for row in rows)
                self.assertEqual(ops.rotate(RotationValue(a),vector),expected)

    def test_scalar_products_preserve_independent_grid_sign_error_and_projection(self):
        from ontokin.reach_pose import RotationValue
        def expected(values):
            maximum=max(map(abs,values))
            # Independent exact normalization by a bounded sequence of powers
            # of two also covers negative scales and nearest-even grid ties.
            factor=F(1)
            while maximum*factor>=1: factor/=2
            while maximum*factor<F(1,2): factor*=2
            result=tuple(F(round(value*factor*(1<<96)),1<<96) for value in values)
            return tuple(-value for value in result) if next(v for v in result if v)<0 else result
        rotations=((F(3,4),F(1,8),F(0),F(-1,4)),
                   (F(-3,4),F(1,8),F(0),F(1,4)),
                   (F(1),F(1,4),F(0),F(0)),
                   (F(1,3),F(2,7),F(-3,11),F(0)),
                   (F(1,2),F(1,1<<97),F(3,1<<97),F(-3,1<<97)),
                   (F(0),F(-1,1<<111),F(0),F(0)))
        scales=(F(1),F(-1),F(1,2),F(-1,2),F(1<<7),F(-1,1<<101),F(3,4),F(-7,3))
        for components in rotations:
            for scale in scales:
                for reverse in (False,True):
                    with self.subTest(components=components,scale=scale,reverse=reverse):
                        ops=ReachPoseOps(ReachExecutionWork())
                        rotation=RotationValue(components,F(1,1024),(1.0,0.0,0.0,0.0))
                        scalar=RotationValue((scale,F(0),F(0),F(0)),F(1,2048))
                        result=ops.multiply(scalar,rotation) if reverse else ops.multiply(rotation,scalar)
                        self.assertEqual(result.components,expected(tuple(scale*v for v in components)))
                        self.assertTrue(all(type(value) is F for value in result.components))
                        self.assertEqual(result.error_rad,F(3,2048)+PRODUCT_ERROR)
                        self.assertIsNone(result.frozen_projection)

    def test_sparse_shortcuts_retain_operand_and_vector_admission(self):
        from ontokin.reach_pose import RotationValue
        valid=RotationValue((F(3,4),F(0),F(0),F(1,4)))
        oversized=RotationValue((F(1<<512),F(0),F(0),F(0)))
        for operation in ("multiply","rotate"):
            with self.subTest(operation=operation):
                ops=ReachPoseOps(ReachExecutionWork(max_operand_bits=512))
                with self.assertRaises(ReachAdmissionError) as raised:
                    if operation=="multiply": ops.multiply(valid,oversized)
                    else: ops.rotate(oversized,(F(0),F(0),F(1)))
                self.assertEqual(raised.exception.details["budget"],"numeric_operand_bits")
                self.assertEqual(ops.work._cache,{})
        for vector in ((F(0),F(0),F(1<<512)),(True,0,0),(0,0)):
            with self.subTest(vector=vector):
                ops=ReachPoseOps(ReachExecutionWork(max_operand_bits=512))
                with self.assertRaises(ReachAdmissionError): ops.rotate(valid,vector)
                self.assertEqual(ops.work._cache,{})

    def test_sparse_shortcuts_cancel_before_successful_cache_publication(self):
        from ontokin.reach_pose import RotationValue
        for operation,checkpoint in (("multiply","quaternion_identity_canonical_check"),
                                     ("fixed-axis","rotation_sparse_check"),
                                     ("planar","rotation_sparse_check")):
            with self.subTest(operation=operation):
                work=ReachExecutionWork()
                marker=RuntimeError("cancel sparse pose arithmetic")
                def check():
                    if work.counts.get(checkpoint,0): raise marker
                work.external_check=check
                ops=ReachPoseOps(work)
                rotation=RotationValue((F(3,4),F(0),F(0),F(1,4)))
                with self.assertRaises(RuntimeError) as raised:
                    if operation=="multiply":
                        ops.multiply(rotation,RotationValue((F(1,2),F(0),F(0),F(0))))
                    else:
                        vector=(F(0),F(0),F(1,3)) if operation=="fixed-axis" else (F(1,3),F(0),F(0))
                        ops.rotate(rotation,vector)
                self.assertIs(raised.exception,marker)
                self.assertIs(work.callback_error,marker)
                self.assertEqual(work.counts.get(checkpoint),1)
                self.assertEqual(work._cache,{})

    def test_sparse_unit_projection_has_independent_exact_binary64_rounding_cells(self):
        from ontokin.reach_pose import RotationValue
        rotations=((F(1),F(0),F(0),F(0)),(F(0),F(-3),F(0),F(4)),
                   (F(1,3),F(2,7),F(0),F(0)),(F(-1),F(0),F(1),F(0)),
                   (F(1),F(0),F(0),F(1,1<<1074)),
                   (F(1),F(-3,1<<1075),F(0),F(0)),
                   (F(1,2),F(1,3),F(-1,5),F(1,7)))
        for values in rotations:
            with self.subTest(values=values):
                ops=ReachPoseOps(ReachExecutionWork())
                rotation=RotationValue(values,F(1,1024))
                actual=ops._unit_projection(rotation)
                denominator=sum(value*value for value in values)
                for source,component in zip(values,actual):
                    self.assertTrue(math.isfinite(component))
                    magnitude=abs(component)
                    ratio=source*source/denominator
                    # Square the exact neighboring-binary64 midpoints. This
                    # independently proves nearest-even sqrt rounding without
                    # a host sqrt or the production integer-sqrt algorithm.
                    lower=(F(math.nextafter(magnitude,0.0))+F(magnitude))/2 if magnitude else F(0)
                    upper=(F(magnitude)+F(math.nextafter(magnitude,math.inf)))/2
                    if float_bits(magnitude)&1:
                        self.assertGreater(ratio,lower*lower)
                        self.assertLess(ratio,upper*upper)
                    else:
                        self.assertGreaterEqual(ratio,lower*lower)
                        self.assertLessEqual(ratio,upper*upper)
                    self.assertEqual(math.copysign(1.0,component),-1.0 if source<0 and magnitude else 1.0)
                    if not source: self.assertEqual(float_bits(component),0)
                self.assertEqual(rotation.error_rad,F(1,1024))
                self.assertEqual(ops.work.counts.get("known_zero_quaternion_projection",0),
                                 sum(not value for value in values))

    def test_sparse_unit_projection_keeps_width_zero_and_materialized_guards(self):
        from ontokin.reach_pose import RotationValue
        work=ReachExecutionWork(max_operand_bits=512)
        ops=ReachPoseOps(work)
        oversized=RotationValue((F(1<<512),F(0),F(0),F(0)))
        with self.assertRaises(ReachAdmissionError) as raised: ops._unit_projection(oversized)
        self.assertEqual(raised.exception.details["budget"],"numeric_operand_bits")
        self.assertEqual(work._cache,{})
        with self.assertRaises(ZeroDivisionError): ops._unit_projection(RotationValue((F(0),)*4))
        self.assertEqual(work._cache,{})
        saved=(-0.0,0.0,0.0,1.0)
        frozen=RotationValue((F(0),F(0),F(0),F(1)),frozen_projection=saved)
        self.assertIs(ops._unit_projection(frozen),saved)
        self.assertEqual(tuple(map(float_bits,saved)),(1<<63,0,0,0x3ff0000000000000))

    def test_sparse_unit_projection_cancellation_cannot_publish_partial_components(self):
        from ontokin.reach_pose import RotationValue
        work=ReachExecutionWork()
        ops=ReachPoseOps(work)
        pose=ops.make(orientation=RotationValue((F(1,2),F(0),F(0),F(0))))
        before=tuple(work._cache.items())
        marker=RuntimeError("cancel zero quaternion component")
        def check():
            if work.counts.get("known_zero_quaternion_projection",0): raise marker
        work.external_check=check
        with self.assertRaises(RuntimeError) as raised: pose.orientation
        self.assertIs(raised.exception,marker)
        self.assertIs(work.callback_error,marker)
        self.assertEqual(work.counts.get("known_zero_quaternion_projection"),1)
        self.assertNotIn("orientation",pose._projection)
        self.assertEqual(tuple(work._cache.items()),before)

    def test_mixed_grid_vector_projects_only_components_that_change(self):
        from ontokin.reach_numeric import round_dyadic
        values=(F(0),F(1,3),F(1,8),F(3,1<<97),F(-3,1<<97),F(1,1<<96))
        expected=tuple(F(round(value*(1<<96)),1<<96) for value in values)
        ops=ReachPoseOps(ReachExecutionWork())
        with patch("ontokin.reach_pose.round_dyadic",wraps=round_dyadic) as rounding:
            actual=ops._rounded_vector(values)
        self.assertEqual(actual,expected)
        self.assertEqual([call.args[0] for call in rounding.call_args_list],
                         [values[index] for index in (1,3,4)])
        self.assertIs(actual[0],values[0])
        self.assertIs(actual[2],values[2])
        self.assertIs(actual[5],values[5])
        limited=ReachPoseOps(ReachExecutionWork(max_operand_bits=512))
        with self.assertRaises(ReachAdmissionError):
            limited._rounded_vector((F(1<<512),F(1,3),F(0)))
        self.assertEqual(limited.work.counts.get("dyadic_round",0),0)
        marker=RuntimeError("cancel mixed grid projection")
        def check(): raise marker
        with self.assertRaises(RuntimeError) as raised:
            ReachPoseOps(ReachExecutionWork(check=check))._rounded_vector(values)
        self.assertIs(raised.exception,marker)

    def test_normalized_axis_reuse_matches_independent_integer_sqrt_and_grid(self):
        def grid(value): return F(round(value*(1<<96)),1<<96)
        def normalized(axis):
            maximum=max(map(abs,axis)); scaled=tuple(value/maximum for value in axis)
            square=sum(value*value for value in scaled)
            integer=math.isqrt((square.numerator<<192)//square.denominator)
            lower=F(integer,1<<96)
            upper=lower if lower*lower==square else lower+F(1,1<<96)
            return tuple(grid(2*value/(lower+upper)) for value in scaled)
        def rescale(values):
            maximum=max(map(abs,values)); factor=F(1)
            while maximum*factor>=1: factor/=2
            while maximum*factor<F(1,2): factor*=2
            result=tuple(grid(value*factor) for value in values)
            return tuple(-value for value in result) if next(v for v in result if v)<0 else result
        axes=((F(1),F(0),F(0)),(F(0),F(-7,11),F(0)),(F(0),F(0),F(1,1<<1074)),
              (F(1,3),F(-2,7),F(5,11)),(F(1),F(1,1<<100),F(0)),(F(1),F(2),F(2)))
        for axis in axes:
            with self.subTest(axis=axis):
                ops=ReachPoseOps(ReachExecutionWork())
                expected=normalized(axis)
                actual=ops._normalized_axis(axis)
                self.assertEqual(actual,expected)
                count=ops.work.operations
                self.assertIs(ops._normalized_axis(axis),actual)
                self.assertGreater(ops.work.operations,count)
                self.assertLess(ops.work.operations-count,5)
                for angle in (F(1,3),F(-2,7)):
                    sine,cosine=ops.sincos(angle/2)
                    result=ops.axis_rotation(axis,angle)
                    self.assertEqual(result.components,rescale((cosine,*(value*sine for value in expected))))
                    self.assertEqual(result.error_rad,AXIS_ERROR+PRODUCT_ERROR)
                self.assertEqual(ops.work.counts.get("pose_unit_axis_check"),1)

    def test_normalized_axis_cache_retains_admission_bounds_and_cancellation(self):
        for axis in ((F(0),)*3,(F(1<<512),F(0),F(0)),(True,0,0),(0,1)):
            for angle in (F(0),F(1,3)):
                with self.subTest(axis=axis,angle=angle):
                    ops=ReachPoseOps(ReachExecutionWork(max_operand_bits=512))
                    with self.assertRaises(ReachAdmissionError): ops.axis_rotation(axis,angle)
                    self.assertFalse(any("normalized_axis" in key for key in ops.work._cache))
        work=ReachExecutionWork(max_cache_entries=1)
        ops=ReachPoseOps(work)
        for axis in ((1,0,0),(0,1,0),(0,0,1),(1,2,3)):
            ops._normalized_axis(axis)
            self.assertLessEqual(len(work._cache),1)
        work=ReachExecutionWork()
        marker=RuntimeError("cancel exact unit axis")
        def check():
            if work.counts.get("pose_unit_axis_check",0): raise marker
        work.external_check=check
        with self.assertRaises(RuntimeError) as raised:
            ReachPoseOps(work).axis_rotation((0,0,1),F(1,3))
        self.assertIs(raised.exception,marker)
        self.assertIs(work.callback_error,marker)
        self.assertFalse(any("normalized_axis" in key or "axis_rotation" in key for key in work._cache))

    def test_static_pose_reuse_is_bounded_and_still_checks_cancellation(self):
        marker=RuntimeError("cancel static cache hit"); cancelled=False
        def check():
            if cancelled: raise marker
        work=ReachExecutionWork(check=check,max_cache_entries=12)
        ops=ReachPoseOps(work)
        # Whole-pose entries are admitted for shared local transforms; varying
        # world translations use the separately tested relative-value cache.
        first=ops.make((0,0,0)); second=ops.make((F(1,7),0,0))
        result=ops.compose(first,second)
        before=work.operations
        again=ops.compose(first,second)
        self.assertIs(again,result)
        self.assertGreater(work.operations,before)
        self.assertLess(work.operations-before,10)
        self.assertLessEqual(len(work._cache),12)
        cancelled=True
        with self.assertRaises(RuntimeError) as raised: ops.compose(first,second)
        self.assertIs(raised.exception,marker)


if __name__=="__main__": unittest.main()
