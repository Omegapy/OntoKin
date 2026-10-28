"""Translated recording reuse preserves each actual source transform."""
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import RecordedTransform, ReachPoseOps, RotationValue, ZERO


class ReachRecordingRelativeTests(unittest.TestCase):
    def test_translated_operands_keep_exact_grid_and_projection(self):
        ops = ReachPoseOps(ReachExecutionWork())
        parent = ops.make((F(1, 3), F(1, 1 << 97), 7), (1, 2, -3, 4))
        local = ops.make((F(2, 7), F(-3, 11), 1), (2, -1, 3, 4))
        expected = ops.compose(parent, local)
        actual = ops.compose_recording(parent, local)
        self.assertEqual((actual.exact_position, actual.rotation),
                         (expected.exact_position, expected.rotation))
        translated = replace(parent, exact_position=(F(5, 3), F(3, 1 << 97), F(-2)))
        expected = ops.compose(translated, local)
        before = ops.work.operations
        with (patch.object(ops, 'rotate', side_effect=AssertionError('repeated relative rotation')),
              patch.object(ops, 'multiply', side_effect=AssertionError('repeated quaternion product'))):
            actual = ops.compose_recording(translated, local)
        self.assertEqual((actual.exact_position, actual.rotation),
                         (expected.exact_position, expected.rotation))
        self.assertEqual((actual.position, actual.orientation), (expected.position, expected.orientation))
        self.assertGreater(ops.work.operations, before)
        self.assertLessEqual(len(ops.work._cache), ops.work.max_cache_entries)

    def test_rotation_allowance_and_local_inputs_are_part_of_identity(self):
        ops = ReachPoseOps(ReachExecutionWork())
        parent, local = ops.make((1, 2, 3), (1, 0, 0, 1)), ops.make((2, 0, 0))
        ops.compose_recording(parent, local)
        for changed_parent, changed_local in (
                (replace(parent, rotation=replace(parent.rotation, error_rad=F(1, 1000))), local),
                (parent, replace(local, rotation=replace(local.rotation, error_rad=F(1, 2000)))),
                (parent, replace(local, exact_position=(F(3), F(0), F(0))))):
            expected = ops.compose(changed_parent, changed_local)
            actual = ops.compose_recording(changed_parent, changed_local)
            self.assertEqual((actual.exact_position, actual.rotation),
                             (expected.exact_position, expected.rotation))

    def test_warm_reuse_keeps_operand_guards_and_original_cancellation(self):
        ops = ReachPoseOps(ReachExecutionWork())
        parent, local = ops.make((1, 2, 3)), ops.make((2, 0, 0))
        ops.compose_recording(parent, local)
        for field, invalid in (
                ('exact_position', (False, False, False)),
                ('exact_position', (F(1 << 32768), F(0), F(0))),
                ('rotation', RotationValue((F(1 << 32768), F(0), F(0), F(0)))),
                ('rotation', replace(parent.rotation, error_rad=F(1 << 32768)))):
            with self.subTest(field=field):
                with self.assertRaises(ReachAdmissionError):
                    ops.compose_recording(replace(parent, **{field: invalid}), local)
        marker = RuntimeError('cancel warm relative recording')
        with patch.object(ops.work, 'external_check', side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                ops.compose_recording(parent, local)
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.work.callback_error, marker)

    def test_recording_constructors_preserve_transform_and_omit_rates(self):
        ops = ReachPoseOps(ReachExecutionWork())
        full = ops.make((F(1, 3), -2, 4), (1, 2, 3, 4))
        sample = ops.make_recording((F(1, 3), -2, 4), (1, 2, 3, 4))
        self.assertIsInstance(sample, RecordedTransform)
        self.assertEqual((sample.exact_position, sample.rotation), (full.exact_position, full.rotation))
        for axis in ((0, 0, 1), (1, 2, -3)):
            for angle in (0, F(1, 3), F(-7, 3)):
                full = ops.hinge_pose(axis, angle, F(0))
                sample = ops.hinge_recording(axis, angle)
                self.assertEqual((sample.exact_position, sample.rotation), (ZERO, full.rotation))
                self.assertEqual(sample.orientation, full.orientation)
                self.assertFalse(hasattr(sample, 'exact_omega'))
        with self.assertRaises(ReachAdmissionError):
            ops.make_recording((True, 0, 0))
        with self.assertRaises(ReachAdmissionError):
            ops.hinge_recording((0, 0, 0), F(1))


if __name__ == '__main__':
    unittest.main()
