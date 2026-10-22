"""Fixed-size sampling reuse retains exact outputs and live proof domains."""
from contextlib import ExitStack
from dataclasses import replace
from fractions import Fraction as F
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_kinematics import recording_pair, sample_pair
from ontokin.reach_numeric import (ReachAdmissionError, ReachExecutionWork, exact,
                                  float_bits, sqrt_rational_binary64)
from ontokin.reach_pose import (BITS, METHOD, ReachPoseOps, RotationValue,
                               _IntegerAxisFactors)
from ontokin.scene import ExportOptions


DATA=Path(__file__).resolve().parents[1]/"docs/language-design/planar-reach-v0.1"


def separate_projection(self,rotation):
    """Pre-consolidation normalization, with its original scalar work charges."""
    if rotation.frozen_projection is not None:
        self.work.charge("frozen_quaternion_projection")
        return rotation.frozen_projection
    self.work.charge("quaternion_projection_operand_guard")
    self.work.guard(*rotation.components)
    key=(METHOD,"unit_projection",rotation.components)
    cached=self.work.lookup(key)
    if cached is not None:
        return cached
    self.work.charge("quaternion_projection_support")
    squares=tuple(exact(value,value,"mul",self.work) if value else F(0)
                  for value in rotation.components)
    nonzero=tuple(value for value in squares if value)
    if not nonzero:
        raise ZeroDivisionError("Exact zero divisor")
    denominator=nonzero[0]
    for value in nonzero[1:]:
        denominator=exact(denominator,value,"add",self.work)
    result=[]
    for value,square in zip(rotation.components,squares):
        if not value:
            self.work.charge("known_zero_quaternion_projection")
            result.append(0.0)
        else:
            ratio=exact(square,denominator,"div",self.work)
            component=sqrt_rational_binary64(ratio,work=self.work)
            self.work.charge("quaternion_projection_sign")
            result.append(-component if value<0 and component else component)
    result=tuple(result)
    self.work.remember(key,result)
    return result


def previous_recording_helpers():
    context=ExitStack()
    context.enter_context(patch.object(ReachPoseOps,"_recording_vector",ReachPoseOps._vector))
    context.enter_context(patch.object(ReachPoseOps,"recording_affine",ReachPoseOps.affine))
    context.enter_context(patch.object(ReachPoseOps,"_compose_recording_relative",
                                      ReachPoseOps.compose_recording))
    context.enter_context(patch.object(ReachPoseOps,"_unit_projection_in_domain",separate_projection))
    context.enter_context(patch("ontokin.reach_runtime.recording_pair",sample_pair))
    return context


class ReachSamplingFactorReuseTests(unittest.TestCase):
    def test_all_axes_share_exact_squares_without_changing_rounding_cells(self):
        scale=1<<BITS
        pairs=((F(3,4),F(1,8)),(F(-3,4),F(1,8)),(F(0),F(-1)),
               (F(scale-3,scale),F(17,scale)))
        vectors=((F(1),F(2),F(3)),(F(2),F(0),F(0)),(F(1,3),F(-2,7),F(5)))
        for axis in range(3):
            for w,z in pairs:
                components=[F(0)]*4
                components[0],components[axis+1]=w,z
                q=RotationValue(tuple(components))
                actual=ReachPoseOps(ReachExecutionWork())
                reference=ReachPoseOps(ReachExecutionWork())
                for vector in vectors:
                    with self.subTest(axis=axis,pair=(w,z),vector=vector):
                        with patch.object(reference,"_integer_axis_rotate",return_value=None):
                            expected=reference.rotate(q,vector)
                        self.assertEqual(actual.rotate(q,vector),expected)
                        projection=actual._unit_projection(q)
                        self.assertEqual(projection,separate_projection(reference,q))
                        denominator=sum(value*value for value in q.components)
                        for source,component in zip(q.components,projection):
                            magnitude=abs(component)
                            ratio=source*source/denominator
                            lower=((F(math.nextafter(magnitude,0.0))+F(magnitude))/2
                                   if magnitude else F(0))
                            upper=(F(magnitude)+F(math.nextafter(magnitude,math.inf)))/2
                            self.assertLessEqual(lower*lower,ratio)
                            self.assertLessEqual(ratio,upper*upper)
                            if float_bits(magnitude)&1:
                                self.assertLess(lower*lower,ratio)
                                self.assertLess(ratio,upper*upper)

    def test_one_factor_entry_retains_one_vector_and_projection_within_capacity(self):
        work=ReachExecutionWork(max_cache_entries=3)
        ops=ReachPoseOps(work)
        q=RotationValue((F(3,4),F(0),F(0),F(1,8)))
        vector=(F(1),F(0),F(0))
        result=ops.rotate(q,vector)
        before=work.counts.get("exact_mul",0)
        projection=ops._unit_projection(q)
        self.assertEqual(work.counts.get("exact_mul",0),before)
        key=(METHOD,"axis_rotation_factors",q.components,work.max_operand_bits)
        self.assertIs(type(work._cache[key]),_IntegerAxisFactors)
        self.assertEqual(work._cache[key].result,result)
        self.assertEqual(work._cache[key].projection,projection)
        self.assertFalse(any("rotated_vector" in k or "unit_projection" in k for k in work._cache))
        with patch.object(ops,"_integer_axis_rotate",side_effect=AssertionError("repeated vector")), \
             patch("ontokin.reach_pose.sqrt_rational_binary64",side_effect=AssertionError("repeated norm")):
            self.assertEqual(ops.rotate(replace(q,error_rad=F(1,100)),vector),result)
            self.assertEqual(ops._unit_projection(q),projection)
        for index in range(12):
            current=RotationValue((F(3,4),F(0),F(0),F(index+1,32)))
            ops.rotate(current,vector)
            ops._unit_projection(current)
            self.assertLessEqual(len(work._cache),3)
        self.assertEqual(ops.rotate(q,vector),result)
        self.assertEqual(ops._unit_projection(q),projection)
        self.assertEqual(work.operations,sum(work.counts.values()))

    def test_factor_projection_restarts_original_preflights_after_cap_change(self):
        q=RotationValue((F((1<<95)+1,1<<96),F(0),F(0),F((1<<94)+3,1<<96)))
        cold=ReachPoseOps(ReachExecutionWork(max_operand_bits=128))
        with self.assertRaises(ReachAdmissionError) as expected:
            separate_projection(cold,q)
        for checkpoint in ("cache_promote","exact_div","cache_insert"):
            ops=ReachPoseOps(ReachExecutionWork())
            ops.rotate(q,(F(1),F(0),F(0)))
            charge=ops.work.charge
            def narrow(kind="checkpoint",amount=1):
                if kind==checkpoint:
                    ops.work.external_check=lambda:setattr(ops.work,"max_operand_bits",128)
                return charge(kind,amount)
            with self.subTest(checkpoint=checkpoint),patch.object(ops.work,"charge",side_effect=narrow):
                with self.assertRaises(ReachAdmissionError) as actual:
                    ops._unit_projection(q)
            self.assertEqual(actual.exception.details,expected.exception.details)

    def test_cancelled_factor_projection_keeps_its_previous_complete_record(self):
        ops=ReachPoseOps(ReachExecutionWork())
        q=RotationValue((F(3,4),F(0),F(0),F(1,8)))
        ops.rotate(q,(F(1),F(0),F(0)))
        before=dict(ops.work._cache)
        marker=RuntimeError("cancel shared normalization")
        charge=ops.work.charge
        def cancel(kind="checkpoint",amount=1):
            if kind=="sqrt_midpoint":
                ops.work.external_check=lambda:(_ for _ in ()).throw(marker)
            return charge(kind,amount)
        with patch.object(ops.work,"charge",side_effect=cancel),self.assertRaises(RuntimeError) as raised:
            ops._unit_projection(q)
        self.assertIs(raised.exception,marker)
        self.assertEqual(dict(ops.work._cache),before)

    def test_warm_pose_projection_rechecks_caps_and_replaced_exact_operands(self):
        q=RotationValue((F((1<<95)+1,1<<96),F(0),F(0),F((1<<94)+3,1<<96)))
        for during_lookup in (False,True):
            ops=ReachPoseOps(ReachExecutionWork())
            pose=ops.make_recording((F(1),F(2),F(3)),q)
            pose.orientation
            old=dict(pose._projection)
            if during_lookup:
                ops.work.external_check=lambda:setattr(ops.work,"max_operand_bits",128)
            else:
                ops.work.max_operand_bits=128
            with self.subTest(during_lookup=during_lookup),self.assertRaises(ReachAdmissionError):
                pose.orientation
            self.assertEqual(pose._projection,old)
        ops=ReachPoseOps(ReachExecutionWork())
        original=ops.make_recording((F(1),F(2),F(3)))
        self.assertEqual(original.position,(1.,2.,3.))
        modified=replace(original,exact_position=(F(4),F(5),F(6)))
        self.assertEqual(modified.position,(4.,5.,6.))
        self.assertEqual(original.position,(1.,2.,3.))
        self.assertLessEqual(len(original._projection_domains),2)

    def test_relative_composition_keeps_private_bits_errors_and_cache_guards(self):
        for local_position in ((F(0),)*3,(F(1,3),F(3,1<<97),F(-5,11))):
            ops=ReachPoseOps(ReachExecutionWork())
            parent=ops.make_recording((F(1),F(2),F(3)),(2,1,0,0))
            local=ops.make_recording(local_position,(3,0,-2,1))
            expected=ops.compose_recording(parent,local)
            ops.work._cache.clear()
            actual=ops.compose_recording_fast(parent,local)
            self.assertEqual((actual.exact_position,actual.rotation),(expected.exact_position,expected.rotation))
            self.assertEqual((actual.position,actual.orientation),(expected.position,expected.orientation))
            self.assertFalse(any("rotation_product" in key for key in ops.work._cache))
            with patch.object(ops,"_multiply_uncached",side_effect=AssertionError("repeated product")):
                repeated=ops.compose_recording_fast(parent,local)
            self.assertEqual(repeated,actual)
            malformed=replace(local,exact_position=(False,False,False))
            with self.assertRaises(ReachAdmissionError):
                ops.compose_recording_fast(parent,malformed)

    def test_recording_vectors_keep_current_domains_and_avoid_repeated_decode(self):
        ops=ReachPoseOps(ReachExecutionWork(max_cache_entries=2))
        values=(1.,2.,3.)
        self.assertEqual(ops._recording_vector(values),ops._vector(values))
        before=ops.work.operations
        self.assertEqual(ops._recording_vector(values),(F(1),F(2),F(3)))
        warm=ops.work.operations-before
        before=ops.work.operations
        ops._vector(values)
        self.assertLess(warm,ops.work.operations-before)
        for invalid in (False,float("nan"),float("inf"),F(1<<32768)):
            with self.subTest(invalid_type=type(invalid).__name__):
                with patch.object(ops.work,"lookup",wraps=ops.work.lookup) as lookup:
                    with self.assertRaises(ReachAdmissionError):
                        ops._recording_vector((invalid,2.,3.))
                    lookup.assert_not_called()
        ops.work.max_operand_bits=32
        with self.assertRaises(ReachAdmissionError) as raised:
            ops._recording_vector(values)
        self.assertEqual(raised.exception.details["consumed"],53)

    def test_recording_pair_keeps_every_coordinate_slope_and_rate(self):
        for start,target,duration in (((3.,0.),(-2.5,1.5),F(2)),
                ((F(1,3),F(-2,7)),(F(5,11),F(4,13)),F(3,2))):
            for running in (False,True):
                work=ReachExecutionWork(max_cache_entries=3)
                reference=ReachExecutionWork()
                for portion in (F(0),F(1,8),F(1,3),F(1,2),F(1),F(1,3)):
                    with self.subTest(start=start,running=running,portion=portion):
                        expected=sample_pair(start,target,duration,portion*duration,running=running,work=reference)
                        actual=recording_pair(start,target,duration,portion*duration,running=running,work=work)
                        self.assertEqual(actual,expected)
                        self.assertLessEqual(len(work._cache),3)
                before=work.operations
                recording_pair(start,target,duration,duration/2,running=running,work=work)
                warm=work.operations-before
                before=reference.operations
                sample_pair(start,target,duration,duration/2,running=running,work=reference)
                self.assertLess(warm,reference.operations-before)

    def test_recording_pair_cap_changes_and_invalid_inputs_do_not_reuse_old_proofs(self):
        start=(F(1,1<<100),F(0)); target=(F(3,1<<100),F(1))
        for during_lookup in (False,True):
            work=ReachExecutionWork()
            recording_pair(start,target,F(2),F(1),running=True,work=work)
            if during_lookup:
                lookup=work.lookup
                def narrowed(key):
                    result=lookup(key)
                    work.max_operand_bits=128
                    return result
                context=patch.object(work,"lookup",side_effect=narrowed)
            else:
                work.max_operand_bits=128
                context=ExitStack()
            with context,self.assertRaises(ReachAdmissionError) as actual:
                recording_pair(start,target,F(2),F(1),running=True,work=work)
            with self.assertRaises(ReachAdmissionError) as expected:
                sample_pair(start,target,F(2),F(1),running=True,
                            work=ReachExecutionWork(max_operand_bits=128))
            self.assertEqual(actual.exception.details,expected.exception.details)
        for invalid in (False,float("nan"),float("inf")):
            work=ReachExecutionWork()
            recording_pair((0.,0.),(1.,1.),F(2),F(1),running=True,work=work)
            with patch.object(work,"lookup",wraps=work.lookup) as lookup:
                with self.assertRaises(ReachAdmissionError):
                    recording_pair((invalid,0.),(1.,1.),F(2),F(1),running=True,work=work)
                lookup.assert_not_called()

    def test_cancelled_pair_law_cannot_publish_a_partial_clock(self):
        work=ReachExecutionWork()
        args=((0.,0.),(1.,1.),F(2),F(1))
        recording_pair(*args,running=True,work=work)
        before=dict(work._cache)
        marker=RuntimeError("cancel pair projection")
        charge=work.charge
        def cancel(kind="checkpoint",amount=1):
            if kind=="binary64_round":
                work.external_check=lambda:(_ for _ in ()).throw(marker)
            return charge(kind,amount)
        with patch.object(work,"charge",side_effect=cancel),self.assertRaises(RuntimeError) as raised:
            recording_pair(*args,running=True,work=work)
        self.assertIs(raised.exception,marker)
        self.assertEqual(dict(work._cache),before)

    def test_complete_passing_glbs_match_separate_recording_arithmetic(self):
        for case,end in (("P01",F(3)),("P09",F(1,4)),("P16",F(1,4))):
            outputs=[]
            for fused in (False,True):
                built=compile_construction(load_file_manifest(DATA/(case.lower()+".files.json")))
                with ExitStack() as context:
                    if not fused:
                        context.enter_context(previous_recording_helpers())
                    result=export_glb(built.model,options=ExportOptions(end=end,fps=1,helpers=False),
                        target_contract="ontokin.glb/0.6",work=built.reach_work)
                self.assertEqual(result.report["validation"]["status"],"passed")
                self.assertLessEqual(built.budget.operations,100000)
                outputs.append(result.data)
            self.assertEqual(outputs[0],outputs[1],case)


if __name__=="__main__":
    unittest.main()
