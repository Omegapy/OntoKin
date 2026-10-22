"""Private carrier seeds use the exact immutable source curve they witness."""
from contextlib import ExitStack
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_phase import phase_bounds
from ontokin.reach_pose import ReachPoseOps, RotationValue
from ontokin.reach_recording_fast import (
    Binary64RecordingOps,
    captured_recording_orientation, sample_bounded_frames,
)
from test_reach_recording_sampler import simulator


PATHS = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame")


def prepared(start=F(0), end=F(2)):
    sim = simulator("P16")
    sim.advance(start, "after")
    phase = phase_bounds(sim, start, end, sim.state, recording_proof=True)
    return sim, phase


class ReachRecordingCapturedSeedTests(unittest.TestCase):
    def test_captured_seed_matches_every_private_source_rotation_through_completion(self):
        for start, end in ((F(0), F(2)), (F(2), F(3)), (F(3), F(4))):
            with self.subTest(start=start):
                sim, phase = prepared(start, end)
                proof = phase["recording_angular_proof"]
                time = start + (end - start) / 4
                _, direct = sim._resolve_kinematics(time, sim.state, selected_frames=PATHS,
                    pose_only=True, recording_only=True)
                for path in PATHS:
                    actual = captured_recording_orientation(sim.pose_ops, proof, path, time)
                    self.assertIs(type(actual), RotationValue)
                    self.assertEqual(actual, direct[path].rotation)
                    self.assertEqual(actual.frozen_projection, direct[path].rotation.frozen_projection)
                self.assertLessEqual(len(sim.work._cache), 256)

    def test_captured_seed_keeps_actual_axis_fixed_rotation_and_paused_coordinate_inputs(self):
        for change in ("axis", "child", "paused", "tween"):
            with self.subTest(change=change):
                sim = simulator("P16")
                sim.advance(F(0), "after")
                claimant = sim.state.claims[("rig.arm.shoulder", "coordinate")]
                active = sim.state.actions[claimant]
                if change == "axis":
                    joint = sim.model.joints["rig.arm.shoulder"]
                    sim.model.joints[joint.path] = replace(joint, axis=(0.0, 0.0, -1.0))
                elif change == "child":
                    site = sim.model.sites["rig.arm.upper.base"]
                    sim.model.sites["rig.arm.upper.base"] = replace(site,
                        pose=replace(site.pose, rotation=(0.0, 0.0, 0.0, 1.0)))
                elif change == "paused":
                    active.status, active.elapsed = "paused", F(1)
                else:
                    action = sim.model.actions[claimant]
                    sim.model.actions[claimant] = replace(action, kind="tween",
                        target="rig.arm.shoulder", goal=0.75)
                    active.initial, active.ideal_initial, active.solution = 0.125, F(1, 8), None
                paths = PATHS[:1] if change == "tween" else PATHS
                phase = phase_bounds(sim, F(0), F(2), sim.state,
                    selected_frames=paths, recording_proof=True)
                _, direct = sim._resolve_kinematics(F(1, 4), sim.state,
                    selected_frames=paths, pose_only=True, recording_only=True)
                for path in paths:
                    self.assertIn(path, phase["recording_angular_proof"].frames)
                    self.assertEqual(captured_recording_orientation(sim.pose_ops,
                        phase["recording_angular_proof"], path, F(1, 4)), direct[path].rotation)

    def test_seed_has_no_live_graph_position_or_recording_cursor_dependency(self):
        sim, phase = prepared()
        proof = phase["recording_angular_proof"]
        expected = captured_recording_orientation(sim.pose_ops, proof, PATHS[1], F(1, 4))
        # These live changes deliberately invalidate the old proof for a new
        # sample. They cannot change the pure seed for its captured operands.
        active = sim.state.actions[sim.state.claims[("rig.arm.shoulder", "coordinate")]]
        active.initial = (active.initial[0] + 0.25, active.initial[1])
        with ExitStack() as stack:
            for target, name in ((sim, "_resolve_kinematics"), (sim, "_coordinate"),
                                 (sim.pose_ops, "rotate"), (sim.pose_ops, "affine"),
                                 (sim.pose_ops, "recording_axis_rotation"),
                                 (sim.pose_ops, "recording_advance_orientation"),
                                 (sim.pose_ops, "recording_body_orientation")):
                stack.enter_context(patch.object(target, name,
                    side_effect=AssertionError("captured orientation needs no live graph")))
            self.assertEqual(captured_recording_orientation(sim.pose_ops, proof, PATHS[1], F(1, 4)),
                             expected)

    def test_transient_callback_source_changes_cannot_poison_exact_or_native_body_cursors(self):
        for native in (False, True):
            with self.subTest(native=native):
                outputs = []
                for mutate in (False, True):
                    sim, phase = prepared()
                    proof, context = phase["recording_angular_proof"], object()
                    moving = sim.recording_moving_frames(sim.state, PATHS)
                    active = sim.state.actions[sim.state.claims[("rig.arm.shoulder", "coordinate")]]
                    initial, prior_check = active.initial, sim.work.external_check
                    body_type = Binary64RecordingOps if native else ReachPoseOps
                    original_body, charge = body_type.recording_body_orientation, sim.work.charge
                    trigger = "recording_float_body_direct_seed" if native else "recording_body_direct_seed"
                    changed = []
                    def temporary_source():
                        if prior_check is not None:
                            prior_check()
                        if not changed:
                            active.initial = (initial[0] + 0.25, initial[1])
                            changed.append(True)
                    def charged(kind="checkpoint", amount=1):
                        if mutate and kind == trigger and not changed:
                            sim.work.external_check = temporary_source
                        return charge(kind, amount)
                    def body(ops, build, *args, **keywords):
                        def captured_seed():
                            try:
                                return build()
                            finally:
                                active.initial, sim.work.external_check = initial, prior_check
                        return original_body(ops, captured_seed, *args, **keywords)
                    frames = []
                    with patch.object(sim.work, "charge", side_effect=charged), \
                            patch.object(body_type, "recording_body_orientation", body):
                        for time in (F(1, 8), F(1, 4), F(3, 8)):
                            if native:
                                result = sample_bounded_frames(sim, time, sim.state, PATHS,
                                    context=context, moving_frames=moving, phase_bounds=phase["frames"],
                                    phase_interval=(F(0), F(2)), recording_angular_proof=proof).frames
                            else:
                                result = sim.recording_frames(time, sim.state, PATHS,
                                    moving_frames=moving, recording_context=context, recording_angular_proof=proof)
                            frames.append(result)
                    self.assertEqual(bool(changed), mutate)
                    self.assertEqual(active.initial, initial)
                    self.assertIs(sim.work.external_check, prior_check)
                    self.assertLessEqual(len(sim.work._cache), 256)
                    outputs.append(frames)
                self.assertEqual(outputs[0], outputs[1])

    def test_cold_seed_callback_cancellation_never_publishes_a_partial_body(self):
        for native in (False, True):
            with self.subTest(native=native):
                sim, phase = prepared()
                marker = RuntimeError("cancel captured carrier seed")
                charge = sim.work.charge
                def cancelled(kind="checkpoint", amount=1):
                    if kind == "recording_body_seed_decode":
                        sim.work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return charge(kind, amount)
                with patch.object(sim.work, "charge", side_effect=cancelled):
                    with self.assertRaises(RuntimeError) as caught:
                        if native:
                            sample_bounded_frames(sim, F(1, 4), sim.state, PATHS, context=object(),
                                moving_frames=sim.recording_moving_frames(sim.state, PATHS),
                                phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                                recording_angular_proof=phase["recording_angular_proof"])
                        else:
                            sim.recording_frames(F(1, 4), sim.state, PATHS,
                                recording_context=object(), recording_angular_proof=phase["recording_angular_proof"])
                self.assertIs(caught.exception, marker)
                self.assertIs(sim.work.callback_error, marker)
                self.assertFalse(any("certified_binary64_body" in key or "body" in key
                                     for key in sim.work._cache))


if __name__ == "__main__":
    unittest.main()
