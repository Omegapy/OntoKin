"""Recording identity elision preserves proper transforms and error bounds."""
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import (PRODUCT_ERROR, UNIT, ZERO, RecordedTransform,
                               ReachPoseOps, RotationValue)


def matrix(q):
    w,x,y,z=q
    n=w*w+x*x+y*y+z*z
    return (((w*w+x*x-y*y-z*z)/n,2*(x*y-w*z)/n,2*(x*z+w*y)/n),
            (2*(x*y+w*z)/n,(w*w-x*x+y*y-z*z)/n,2*(y*z-w*x)/n),
            (2*(x*z-w*y)/n,2*(y*z+w*x)/n,(w*w-x*x-y*y+z*z)/n))


class ReachRecordingIdentityTests(unittest.TestCase):
    def test_identity_elision_keeps_the_exact_projective_rotation_and_both_errors(self):
        ops=ReachPoseOps(ReachExecutionWork())
        moving=ops.make((F(1,3),F(-2,7),F(3,1<<97)),(1,2,-3,4))
        moving=replace(moving,rotation=replace(moving.rotation,error_rad=F(1,1<<60)))
        for scalar in (F(1),F(-3),F(1,1<<100)):
            for identity_first in (False,True):
                with self.subTest(scalar=scalar,identity_first=identity_first):
                    identity=ops.identity()
                    identity=replace(identity,rotation=RotationValue((scalar,F(0),F(0),F(0)),F(1,1<<65)))
                    parent,local=(identity,moving) if identity_first else (moving,identity)
                    actual=ops.compose_recording_fast(parent,local)
                    expected=ops.compose_recording(parent,local)
                    self.assertEqual(matrix(actual.rotation.components),matrix(moving.rotation.components))
                    self.assertEqual(actual.exact_position,expected.exact_position)
                    self.assertEqual(actual.rotation.error_rad,parent.rotation.error_rad+local.rotation.error_rad)
                    self.assertLessEqual(actual.rotation.error_rad,expected.rotation.error_rad)
                    self.assertIsInstance(actual,RecordedTransform)
                    self.assertFalse(hasattr(actual,"velocity"))

    def test_nonidentity_path_keeps_the_original_noncommuting_product_and_grid(self):
        ops=ReachPoseOps(ReachExecutionWork())
        parent=ops.make((F(1,3),F(-2,7),F(3,1<<97)),(1,2,-3,4))
        local=ops.make((F(-1,5),F(7,9),F(-5,1<<97)),(2,-3,1,5))
        expected=ops.compose_recording(parent,local)
        actual=ops.compose_recording_fast(parent,local)
        self.assertEqual((actual.exact_position,actual.rotation),(expected.exact_position,expected.rotation))

    def test_zero_local_translation_keeps_the_original_halfway_position_projection(self):
        ops=ReachPoseOps(ReachExecutionWork())
        for position in ((F(3,1<<97),F(-5,1<<97),F(1,1<<1075)),
                         (F(1,3),F(-2,7),F(5,11))):
            parent=ops.make(position,(1,2,3,4))
            local=ops.identity()
            actual=ops.compose_recording_fast(parent,local)
            expected=ops.compose_recording(parent,local)
            self.assertEqual(actual.exact_position,expected.exact_position)

    def test_unchanged_materialized_projection_is_retained_with_combined_allowance(self):
        ops=ReachPoseOps(ReachExecutionWork())
        moving=ops.materialize(ops.make((1,2,3),(1,2,3,4)))
        identity=replace(ops.identity(),rotation=RotationValue(UNIT,F(1,1<<60)))
        for parent,local in ((moving,identity),(identity,moving)):
            actual=ops.compose_recording_fast(parent,local)
            self.assertEqual(actual.orientation,moving.orientation)
            self.assertEqual(actual.rotation.frozen_projection,moving.rotation.frozen_projection)
            self.assertEqual(actual.rotation.error_rad,moving.rotation.error_rad+identity.rotation.error_rad)

    def test_operand_domains_low_caps_and_cancellation_remain_checked(self):
        ops=ReachPoseOps(ReachExecutionWork())
        parent,local=ops.make((1,2,3),(1,2,3,4)),ops.identity()
        for invalid in ((False,False,False),(F(0),F(0)),(F(1<<32768),F(0),F(0))):
            with self.subTest(invalid_type=type(invalid[0]).__name__),self.assertRaises(ReachAdmissionError):
                ops.compose_recording_fast(replace(parent,exact_position=invalid),local)
        with self.assertRaises(ReachAdmissionError):
            ops.compose_recording_fast(replace(parent,rotation=RotationValue((F(0),)*4)),local)
        ops.work.max_operand_bits=128
        wide=replace(parent,exact_position=(F(1<<128),F(0),F(0)))
        with self.assertRaises(ReachAdmissionError):
            ops.compose_recording_fast(wide,local)
        marker=RuntimeError("cancel identity recording")
        with patch.object(ops.work,"external_check",side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                ops.compose_recording_fast(parent,local)
        self.assertIs(caught.exception,marker)

    def test_identity_chain_uses_less_work_without_a_new_cache(self):
        counts=[]
        for fast in (False,True):
            ops=ReachPoseOps(ReachExecutionWork())
            parent=ops.make((1,2,3),(1,2,3,4))
            local=ops.make((F(1,3),0,0))
            before=ops.work.operations
            for _ in range(12):
                parent=(ops.compose_recording_fast if fast else ops.compose_recording)(parent,local)
            counts.append(ops.work.operations-before)
            self.assertLessEqual(len(ops.work._cache),256)
            self.assertEqual(ops.work.operations,sum(ops.work.counts.values()))
        self.assertLess(counts[1],counts[0])

    def test_callback_cap_narrowing_cannot_publish_an_earlier_broad_domain(self):
        for checkpoint in ("recording_identity_composition","pose_grid_check"):
            with self.subTest(checkpoint=checkpoint):
                ops=ReachPoseOps(ReachExecutionWork())
                parent=replace(ops.identity(),rotation=RotationValue((F(1),F(1,1<<500),F(0),F(0))))
                local=ops.identity()
                original=ops.work.charge
                def charge(kind="checkpoint",amount=1):
                    if kind==checkpoint:
                        ops.work.external_check=lambda:setattr(ops.work,"max_operand_bits",128)
                    return original(kind,amount)
                with patch.object(ops.work,"charge",side_effect=charge):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        ops.compose_recording_fast(parent,local)
                self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")


if __name__=="__main__":
    unittest.main()
