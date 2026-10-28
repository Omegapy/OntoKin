"""A literal native child zero needs no numerical vector cache entry."""
from dataclasses import replace
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_fast import Binary64RecordingOps
from test_reach_recording_captured_seed import PATHS, prepared


class ReachRecordingChildOriginTests(unittest.TestCase):
    def test_only_complete_immutable_binary64_zeros_use_direct_admission(self):
        ops = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), body_cursors=True)
        for value in ((0.0, 0.0, 0.0), (-0.0, 0.0, -0.0)):
            self.assertIs(ops.recording_zero_child_origin(value), True)
            self.assertEqual(ops.source_ops._vector(value), (F(0), F(0), F(0)))
        for value in ((0, 0, 0), (F(0), F(0), F(0)), [0.0, 0.0, 0.0],
                      (0.0, 0.0), (False, 0.0, 0.0),
                      (math.ldexp(1.0, -1074), 0.0, 0.0),
                      (float("nan"), 0.0, 0.0), (float("inf"), 0.0, 0.0)):
            with self.subTest(value=value):
                self.assertIsNone(ops.recording_zero_child_origin(value))
        ops.work.max_operand_bits = 128
        self.assertIsNone(ops.recording_zero_child_origin((0.0, 0.0, 0.0)))

    def test_current_origin_guard_keeps_cancellation_cap_changes_and_operation_limit(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                work = ReachExecutionWork()
                ops = Binary64RecordingOps(ReachPoseOps(work), body_cursors=True)
                marker = RuntimeError("cancel child-origin admission")
                def callback():
                    if cancel:
                        raise marker
                    work.max_operand_bits = 128
                work.external_check = callback
                if cancel:
                    with self.assertRaises(RuntimeError) as caught:
                        ops.recording_zero_child_origin((0.0, 0.0, 0.0))
                    self.assertIs(caught.exception, marker)
                    self.assertIs(work.callback_error, marker)
                else:
                    self.assertIs(ops.recording_zero_child_origin((0.0, 0.0, 0.0)), False)
                self.assertFalse(work._cache)
        ops = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork(max_operations=1)), body_cursors=True)
        self.assertTrue(ops.recording_zero_child_origin((0.0, 0.0, 0.0)))
        with self.assertRaises(ReachAdmissionError) as caught:
            ops.recording_zero_child_origin((0.0, 0.0, 0.0))
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["consumed"], 2)

    def test_actual_native_zero_child_avoids_decoding_with_identical_graph_output(self):
        outputs, costs, decodes = [], [], []
        for direct in (False, True):
            sim, phase = prepared()
            site = sim.model.sites["rig.arm.upper.base"]
            position = tuple([0.0, 0.0, 0.0])
            sim.model.sites[site.path] = replace(site, pose=replace(site.pose, position=position))
            native = Binary64RecordingOps(sim.pose_ops, body_cursors=True)
            vector, context, observed = native._recording_vector, object(), []
            def decode(values, length=3):
                if values is position:
                    observed.append(values)
                return vector(values, length)
            frames, before = [], sim.work.operations
            with patch.object(native, "_recording_vector", side_effect=decode), \
                    patch.object(native, "recording_zero_child_origin",
                        wraps=native.recording_zero_child_origin if direct else lambda value: None):
                for time in (F(1, 8), F(1, 4), F(3, 8)):
                    _, result = sim._resolve_kinematics(time, sim.state, selected_frames=PATHS[:1],
                        pose_only=True, recording_only=True, recording_context=context,
                        recording_pose_ops=native, recording_angular_proof=phase["recording_angular_proof"])
                    frames.append((result[PATHS[0]].position, result[PATHS[0]].orientation))
            outputs.append(frames)
            costs.append(sim.work.operations - before)
            decodes.append(len(observed))
            self.assertLessEqual(len(sim.work._cache), 256)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(decodes, [3, 0])
        self.assertLess(costs[1], costs[0])


if __name__ == "__main__":
    unittest.main()
