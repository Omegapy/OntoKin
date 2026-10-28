"""Recording samples preserve actual p/q without publishing fictitious rates."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as Q
from functools import partial
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin import reach_export
from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_runtime import ReachSimulator
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import PoseValue, RecordedTransform, ReachPoseOps
from ontokin.gltf import export_glb
from ontokin.scene import ExportOptions


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"
SUPPLEMENT = DATA / "draft2-supplements"


def simulator(case):
    root = SUPPLEMENT if case.startswith("L") else DATA
    built = compile_construction(load_file_manifest(root / (case.lower() + ".files.json")))
    return ReachSimulator(built.model, work=built.reach_work)


class ReachRecordingSamplerTests(unittest.TestCase):
    def test_transform_composition_preserves_noncommuting_rotation_and_grid_ties(self):
        for position in ((Q(1, 3), Q(3, 1 << 97), Q(-5, 11)),
                         (Q(0), Q(-1, 1 << 1075), Q(1, 1 << 96))):
            with self.subTest(position=position):
                ops = ReachPoseOps(ReachExecutionWork())
                parent = ops.make(position, (1, 2, -3, 4), (1, 2, 3), (4, 5, 6))
                local = ops.make((Q(1, 7), Q(-2, 9), 3), (2, -3, 1, 5), (3, 2, 1), (6, 5, 4))
                parent = replace(parent, position_error_m=Q(1, 1000))
                local = replace(local, position_error_m=Q(1, 2000))
                complete = ops.compose(parent, local)
                actual = ops.compose_recording(parent, local)
                self.assertIsInstance(actual, RecordedTransform)
                self.assertEqual(actual.exact_position, complete.exact_position)
                self.assertEqual(actual.rotation, complete.rotation)
                self.assertEqual(actual.position, complete.position)
                self.assertEqual(actual.orientation, complete.orientation)
                child = ops.make((Q(3, 5), Q(2, 11), Q(-7, 13)), (3, 1, -2, 4))
                chained = ops.compose_recording(actual, child)
                expected = ops.compose(complete, child)
                self.assertEqual((chained.exact_position, chained.rotation),
                                 (expected.exact_position, expected.rotation))
                for field in ("velocity", "omega", "exact_velocity", "exact_omega", "position_error_m"):
                    self.assertFalse(hasattr(actual, field))
                with self.assertRaises(TypeError):
                    ops.compose(actual, child)
                self.assertLessEqual(len(ops.work._cache), 256)

    def test_transform_composition_keeps_operand_and_cancellation_guards(self):
        for invalid in ((False, False, False), (Q(0), Q(0)), (Q(1 << 512), Q(0), Q(0))):
            with self.subTest(invalid=invalid):
                ops = ReachPoseOps(ReachExecutionWork(max_operand_bits=512))
                parent, local = ops.identity(), ops.make((1, 2, 3))
                ops.compose_recording(parent, local)
                with self.assertRaises(ReachAdmissionError):
                    ops.compose_recording(replace(parent, exact_position=invalid), local)
        ops = ReachPoseOps(ReachExecutionWork())
        parent, local = ops.identity(), ops.make((1, 2, 3))
        marker = RuntimeError("cancel transform-only sampling")
        with patch.object(ops.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                ops.compose_recording(parent, local)
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.work.callback_error, marker)

    def test_transform_graph_cannot_enter_complete_source_cache(self):
        sim = simulator("P01")
        sim.advance(Q(0), "after")
        sim.phase_bounds(Q(0), Q(2))
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame")
        _, partial = sim._resolve_kinematics(Q(1, 3), sim.state, selected_frames=paths,
                                           pose_only=True, recording_only=True)
        self.assertTrue(all(isinstance(partial[path], RecordedTransform) for path in paths))
        _, complete = sim._kinematics(Q(1, 3), sim.state)
        self.assertTrue(all(isinstance(complete[path], PoseValue) for path in paths))
        with self.assertRaises(ValueError):
            sim._resolve_kinematics(Q(1, 3), sim.state, recording_only=True)

    def test_transform_recording_preserves_complete_glb_bytes(self):
        original = ReachSimulator._resolve_kinematics
        original_frames = ReachSimulator.recording_frames
        original_sampling = reach_export._sample_recording_nodes
        def full_pose_sampling(self, *args, **kwargs):
            kwargs["recording_only"] = False
            return original(self, *args, **kwargs)
        def direct_sampling(self, *args, **kwargs):
            # This test isolates the derivative-free transform optimization.
            # The separate incremental recording algorithm has its own error
            # proof and need not reproduce direct private quaternion bits.
            kwargs["recording_context"] = None
            kwargs["recording_angular_proof"] = None
            return original_frames(self, *args, **kwargs)
        for case, end in (("P01", Q(3)), ("L01", Q(3, 4)), ("P16", Q(1, 4))):
            outputs = []
            for transforms in (False, True):
                root = SUPPLEMENT if case.startswith("L") else DATA
                built = compile_construction(load_file_manifest(root / (case.lower() + ".files.json")))
                options = ExportOptions(end=end, fps=1, helpers=False)
                with patch.object(ReachSimulator, "recording_frames", direct_sampling), \
                        patch.object(reach_export, "_sample_recording_nodes",
                                     partial(original_sampling, allow_fast=False)):
                    if transforms:
                        result = export_glb(built.model, options=options,
                            target_contract="ontokin.glb/0.6", work=built.reach_work)
                    else:
                        with patch.object(ReachSimulator, "_resolve_kinematics", full_pose_sampling):
                            result = export_glb(built.model, options=options,
                                target_contract="ontokin.glb/0.6", work=built.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertLessEqual(built.budget.operations, 100000)
                outputs.append(result.data)
            self.assertEqual(outputs[0], outputs[1], case)

    def test_constant_track_classification_follows_complete_actual_dependencies(self):
        for case, start, end in (("P01", Q(0), Q(2)), ("P01", Q(2), Q(3)),
                                  ("P05", Q(0), Q(2)), ("L01", Q(1, 2), Q(3, 2)),
                                  ("L02", Q(1, 2), Q(3, 2)), ("P16", Q(2), Q(3))):
            with self.subTest(case=case, start=start):
                sim = simulator(case)
                sim.advance(start, "after")
                sim.phase_bounds(start, end)
                paths = ("world", *(path + ".frame" for path in sim.model.objects),
                         *(path + ".frame" for path in sim.model.sites))
                moving = sim.recording_moving_frames(sim.state, paths)
                first = sim.recording_frames(start, sim.state, paths)
                last = sim.recording_frames((start + end) / 2, sim.state, paths)
                self.assertNotIn("world", moving)
                for path in paths:
                    if path not in moving:
                        self.assertEqual(first[path], last[path], path)
                if case == "P05":
                    self.assertEqual(moving, frozenset(path for path in paths if path != "world"))
                if case == "P16":
                    self.assertIn("payload.frame", moving)
                if case == "P01" and start == 2:
                    self.assertFalse(moving)
        sim = simulator("P01")
        with self.assertRaises(ValueError):
            sim.recording_moving_frames(sim.state, ("invented.frame",))
        marker = RuntimeError("cancel recording dependency walk")
        with patch.object(sim.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                sim.recording_moving_frames(sim.state, ("world",))
        self.assertIs(caught.exception, marker)

    def test_retained_constant_tracks_equal_fresh_sampling_at_every_key(self):
        original_sampling = reach_export._sample_recording_nodes
        for case, end in (("P01", Q(3)), ("L01", Q(3, 4))):
            outputs = []
            for reuse in (False, True):
                root = SUPPLEMENT if case.startswith("L") else DATA
                built = compile_construction(load_file_manifest(root / (case.lower() + ".files.json")))
                options = ExportOptions(end=end, fps=1, helpers=False)
                # Isolate exact stationary-track reuse. The native algorithm
                # has separately certified endpoint allowances; its tests
                # cover retained and recomputed actual stored components.
                with patch.object(reach_export, "_sample_recording_nodes",
                                  partial(original_sampling, allow_fast=False)):
                    if reuse:
                        result = export_glb(built.model, options=options,
                            target_contract="ontokin.glb/0.6", work=built.reach_work)
                    else:
                        with patch.object(ReachSimulator, "recording_moving_frames",
                                          lambda self, state, paths: frozenset(paths)):
                            result = export_glb(built.model, options=options,
                                target_contract="ontokin.glb/0.6", work=built.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                outputs.append(result.data)
            self.assertEqual(outputs[0], outputs[1], case)

    def assert_same_poses(self, sim, time, paths):
        # Both paths use the same already prepared whole-phase reduction plan.
        sim._invalidate()
        recorded = sim.recording_frames(time, sim.state, paths)
        _, complete = sim._kinematics(time, sim.state)
        self.assertEqual(set(recorded), set(paths))
        for path in paths:
            self.assertEqual(recorded[path].position, complete[path].position, path)
            self.assertEqual(recorded[path].orientation, complete[path].orientation, path)
            self.assertFalse(hasattr(recorded[path], "velocity"))
            self.assertFalse(hasattr(recorded[path], "omega"))
        return complete

    def test_moving_carrier_and_reach_match_complete_pose_without_losing_rates(self):
        sim = simulator("P16")
        sim.advance(Q(0), "after")
        sim.phase_bounds(Q(0), Q(2))
        complete = self.assert_same_poses(sim, Q(1, 3),
            ("rig.frame", "rig.arm.upper.frame", "rig.arm.forearm.tip.frame", "payload.frame"))
        self.assertTrue(any(complete["payload.frame"].velocity))
        self.assertTrue(any(complete["payload.frame"].omega))

    def test_new_owner_replaces_partial_cache_inputs(self):
        sim = simulator("L02")
        sim.advance(Q(0), "after")
        sim.phase_bounds(Q(0), Q(1, 2))
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame")
        first = self.assert_same_poses(sim, Q(1, 4), paths)
        first_pose = first[paths[-1]].position
        sim.advance(Q(1, 2), "after")
        sim.phase_bounds(Q(1, 2), Q(3, 2))
        second = self.assert_same_poses(sim, Q(3, 4), paths)
        self.assertNotEqual(first_pose, second[paths[-1]].position)
        self.assertTrue(any(second[paths[-1]].omega))

    def test_released_anchor_and_dynamic_samples_preserve_canonical_pose(self):
        sim = simulator("P16")
        sim.advance(Q(2), "after")
        anchor = sim.state.dynamic["payload"].state
        anchor_pose = (anchor.position, anchor.orientation)
        sim.phase_bounds(Q(2), Q(3))
        at_anchor = sim.recording_frames(Q(2), sim.state, ["payload.frame"])["payload.frame"]
        self.assertEqual((at_anchor.position, at_anchor.orientation), anchor_pose)
        complete = self.assert_same_poses(sim, Q(9, 4), ("payload.frame",))
        self.assertTrue(any(complete["payload.frame"].velocity))
        self.assertEqual((anchor.position, anchor.orientation), anchor_pose)

    def test_pose_only_default_carriers_execute_less_actual_work(self):
        costs, poses = {}, {}
        for mode in ("complete", "recording"):
            sim = simulator("P01")
            sim.advance(Q(0), "after")
            sim.phase_bounds(Q(0), Q(2))
            paths = tuple(path + ".frame" for path in sim.model.objects)
            baseline = sim.work.operations
            if mode == "recording":
                frames = sim.recording_frames(Q(1, 3), sim.state, paths)
            else:
                _, frames = sim._kinematics(Q(1, 3), sim.state)
            poses[mode] = {path: (frames[path].position, frames[path].orientation) for path in paths}
            costs[mode] = sim.work.operations - baseline
        self.assertEqual(poses["recording"], poses["complete"])
        self.assertLess(costs["recording"], costs["complete"])


if __name__ == "__main__":
    unittest.main()
