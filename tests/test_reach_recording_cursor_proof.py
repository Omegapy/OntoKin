"""A bounded cursor retains one exact increment without changing its output."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps


def reference_steps(ops, axis, angles):
    result=[]
    previous=None
    for angle in angles:
        if previous is None:
            rotation=ops.axis_rotation(axis,angle)
        else:
            delta=angle-previous
            if delta:
                rotation=ops.multiply(ops.axis_rotation(axis,delta),rotation)
        previous=angle
        result.append(rotation)
    return result


class ReachRecordingCursorProofTests(unittest.TestCase):
    def test_every_private_component_and_allowance_matches_original_recurrence(self):
        angles=[F(index,64) for index in range(24)]
        angles+=angles[-1:]+list(reversed(angles[4:12]))
        angles += [F(19,31),F(3,4),F(7,8)]
        for axis in ((0,0,1),(0,1,0),(1,2,3)):
            with self.subTest(axis=axis):
                ops=ReachPoseOps(ReachExecutionWork())
                reference=ReachPoseOps(ReachExecutionWork())
                expected=reference_steps(reference,axis,angles)
                context=object()
                actual=[ops.recording_axis_rotation(axis,angle,context=context,
                    path="joint",max_steps=10000) for angle in angles]
                self.assertEqual(actual,expected)
                self.assertEqual([ops._unit_projection(q) for q in actual],
                                 [reference._unit_projection(q) for q in expected])
                self.assertLessEqual(len(ops.work._cache),256)
                self.assertEqual(ops.work.operations,sum(ops.work.counts.values()))

    def test_warm_increment_avoids_the_axis_kernel_and_global_product_cache(self):
        ops=ReachPoseOps(ReachExecutionWork())
        context=object()
        args=dict(context=context,path="joint",max_steps=10000)
        for angle in (F(0),F(1,64)):
            ops.recording_axis_rotation((0,0,1),angle,**args)
        before=tuple(key for key in ops.work._cache if "rotation_product" in key)
        with patch.object(ops,"axis_rotation",side_effect=AssertionError("redecoded increment")):
            ops.recording_axis_rotation((0,0,1),F(2,64),**args)
        after=tuple(key for key in ops.work._cache if "rotation_product" in key)
        self.assertEqual(before,after)
        self.assertEqual(ops.work.counts["recording_increment_reuse"],1)

    def test_cancelled_reuse_does_not_publish_the_next_coordinate(self):
        ops=ReachPoseOps(ReachExecutionWork())
        context=object()
        args=dict(context=context,path="joint",max_steps=10000)
        for angle in (F(0),F(1,64)):
            ops.recording_axis_rotation((0,0,1),angle,**args)
        key=next(key for key in ops.work._cache if "recording_rotation_cursor" in key)
        before=ops.work._cache[key]
        marker=RuntimeError("cancel increment reuse")
        charge=ops.work.charge
        def cancelled(kind="checkpoint",amount=1):
            if kind=="recording_increment_reuse":
                ops.work.external_check=lambda: (_ for _ in ()).throw(marker)
            return charge(kind,amount)
        with patch.object(ops.work,"charge",side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                ops.recording_axis_rotation((0,0,1),F(2,64),**args)
        self.assertIs(caught.exception,marker)
        self.assertEqual(ops.work._cache[key],before)

    def test_lowered_cap_at_increment_reuse_cannot_publish_the_wide_proof(self):
        ops=ReachPoseOps(ReachExecutionWork())
        context=object()
        args=dict(context=context,path="joint",max_steps=10000)
        for angle in (F(0),F(1,64)):
            ops.recording_axis_rotation((0,0,1),angle,**args)
        charge=ops.work.charge
        def narrowed(kind="checkpoint",amount=1):
            result=charge(kind,amount)
            if kind=="recording_increment_reuse":
                ops.work.max_operand_bits=128
            return result
        with patch.object(ops.work,"charge",side_effect=narrowed):
            with self.assertRaises(ReachAdmissionError) as caught:
                ops.recording_axis_rotation((0,0,1),F(2,64),**args)
        self.assertEqual(caught.exception.details["budget"],"numeric_operand_bits")


if __name__=="__main__":
    unittest.main()
