"""Exact affine recording interiors keep source state and bounded exposure."""
from dataclasses import replace
from fractions import Fraction as F
from types import SimpleNamespace as NS
import copy
import struct
import unittest
from unittest.mock import patch

from ontokin.model import Pose
from ontokin.reach_kinematics import sample_pair
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import joint_phase
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_fast import (
    Binary64RecordingOps, MAX_FLOAT_ROTATION_STEPS, RecordingRoundingAmbiguity,
    _AffineCoordinate, _FloatPose, _UnsupportedPlanar, sample_bounded_frames,
)
from test_reach_recording_sampler import simulator


def affine_fixture(work, *, initial=F(1, 7), target=F(4, 5), duration=F(2)):
    runtime = NS(initial=initial, ideal_initial=initial + F(1, 2**40),
                 elapsed=F(0), running_since=F(0), status="running")
    runtime.elapsed_at = lambda time: runtime.elapsed + (
        time - runtime.running_since if runtime.status == "running" else F(0))
    action = NS(kind="hinge", goal=target, duration=duration)
    state = NS(claims={("joint", "coordinate"): "action"},
               actions={"action": runtime}, coordinates={"joint": initial})
    sim = NS(work=work, model=NS(actions={"action": action}))
    return sim, state, runtime, action


def projective_error(actual, expected):
    return min(max(abs(F(a) - sign * F(b)) for a, b in zip(actual, expected))
               for sign in (1, -1))


class ReachRecordingAffineTests(unittest.TestCase):
    def test_exact_affine_path_is_inside_the_existing_ideal_source_allowance(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
        sim, state, runtime, action = affine_fixture(native.work)
        bound = joint_phase(sim, "joint", F(0), F(2), state)
        omitted_rounding_is_nonzero = False
        for elapsed in (F(0), F(1, 11), F(1, 3), F(7, 5), F(2)):
            coordinate = native.recording_coordinate(sim, "joint", elapsed, state)
            value = coordinate.law.initial + coordinate.law.slope * coordinate.elapsed
            ideal = runtime.ideal_initial + (action.goal - runtime.ideal_initial) * elapsed / action.duration
            exposed = sample_pair((runtime.initial, F(0)), (action.goal, F(0)),
                action.duration, elapsed, running=True, work=ReachExecutionWork())
            self.assertEqual(value, exposed.exact_coordinates[0])
            self.assertLessEqual(abs(value - ideal), bound.coordinate_error)
            self.assertLessEqual(abs(F(exposed.coordinates_rad[0]) - ideal), bound.coordinate_error)
            omitted_rounding_is_nonzero |= value != F(exposed.coordinates_rad[0])
        self.assertTrue(omitted_rounding_is_nonzero)

    def test_affine_recurrence_encloses_direct_kernel_across_reseed_and_clock_reversal(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
        reference = ReachPoseOps(ReachExecutionWork())
        sim, state, _, _ = affine_fixture(native.work, duration=F(3))
        times = [F(index, 137) for index in range(1, MAX_FLOAT_ROTATION_STEPS + 4)]
        times += [F(1, 3), F(2, 7), F(2, 7), F(9, 5)]
        args = dict(context=object(), path="hinge:joint", max_steps=10000)
        for elapsed in times:
            coordinate = native.recording_coordinate(sim, "joint", elapsed, state)
            actual = native.recording_axis_rotation((0, 0, 1), coordinate, **args)
            value = coordinate.law.initial + coordinate.law.slope * coordinate.elapsed
            expected = reference._unit_projection(reference.axis_rotation((0, 0, 1), value))
            self.assertLessEqual(projective_error((actual.w, 0, 0, actual.z), expected), F(1, 2**41))
            cursor = next(value for key, value in native.work._cache.items()
                          if "bounded_affine_axis" in key)
            self.assertLessEqual(cursor[2], MAX_FLOAT_ROTATION_STEPS)
        self.assertLess(native.work.operations, reference.work.operations)
        self.assertEqual(native.work.operations, sum(native.work.counts.values()))
        self.assertLessEqual(len(native.work._cache), 256)

    def test_current_clock_pause_resume_and_new_owner_rebuild_the_actual_law(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
        sim, state, runtime, action = affine_fixture(native.work)
        first = native.recording_coordinate(sim, "joint", F(1, 2), state)
        runtime.status, runtime.elapsed = "paused", F(1, 2)
        paused = native.recording_coordinate(sim, "joint", F(9), state)
        self.assertEqual(paused.elapsed, first.elapsed)
        self.assertFalse(paused.running)
        runtime.status, runtime.running_since = "running", F(3, 2)
        resumed = native.recording_coordinate(sim, "joint", F(2), state)
        self.assertEqual(resumed.elapsed, F(1))
        self.assertTrue(resumed.running)
        state.claims[("joint", "coordinate")] = "new_owner"
        state.actions["new_owner"] = NS(initial=F(-1, 3), elapsed=F(0),
            running_since=F(2), status="running")
        sim.model.actions["new_owner"] = NS(kind="hinge", goal=F(1, 2), duration=F(1))
        replacement = native.recording_coordinate(sim, "joint", F(9, 4), state)
        self.assertEqual((replacement.law.initial, replacement.law.target, replacement.elapsed),
                         (F(-1, 3), F(1, 2), F(1, 4)))
        self.assertNotEqual(replacement.law, resumed.law)
        self.assertEqual((runtime.initial, action.goal), (F(1, 7), F(4, 5)))

    def test_cursor_identity_retains_each_law_axis_phase_path_and_running_state(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
        law = native._affine_law(F(1, 7), F(4, 5), F(2), running=True)
        first = _AffineCoordinate(law, F(1, 3), True)
        context = object()
        variants = [((0, 0, 1), first, context, "hinge:joint"),
                    ((0, 0, -1), first, context, "hinge:joint"),
                    ((0, 0, 1), first, object(), "hinge:joint"),
                    ((0, 0, 1), first, context, "hinge:other"),
                    ((0, 0, 1), replace(first, running=False), context, "hinge:joint")]
        for initial, target, duration in ((F(1, 5), F(4, 5), F(2)),
                                          (F(1, 7), F(3, 5), F(2)),
                                          (F(1, 7), F(4, 5), F(3))):
            other = native._affine_law(initial, target, duration, running=True)
            variants.append(((0, 0, 1), replace(first, law=other), context, "hinge:joint"))
        for axis, coordinate, phase, path in variants:
            native.recording_axis_rotation(axis, coordinate, context=phase, path=path, max_steps=10000)
        cursors = [value for key, value in native.work._cache.items() if "bounded_affine_axis" in key]
        self.assertEqual(len(cursors), len(variants))
        self.assertTrue(all(cursor[2] == 1 for cursor in cursors))

    def test_actual_clock_and_duration_are_checked_before_native_rotation(self):
        for time in (F(-1), F(3)):
            native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
            sim, state, _, _ = affine_fixture(native.work)
            with self.assertRaises(ReachAdmissionError) as caught:
                native.recording_coordinate(sim, "joint", time, state)
            self.assertEqual(caught.exception.reach_code, "reach_numeric")
            self.assertNotIn("recording_float_mul", native.work.counts)
        for duration in (F(0), F(-1)):
            native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
            sim, state, _, _ = affine_fixture(native.work, duration=duration)
            with self.assertRaises(ReachAdmissionError):
                native.recording_coordinate(sim, "joint", F(0), state)
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
        sim, state, runtime, _ = affine_fixture(native.work)
        runtime.running_since = F(1 << 1200)
        with self.assertRaises(_UnsupportedPlanar):
            native.recording_coordinate(sim, "joint", F(1 << 1200), state)
        self.assertNotIn("recording_float_mul", native.work.counts)
        self.assertEqual(native.work.max_operand_bits, 32768)

    def test_running_rate_finiteness_is_preserved_without_rounding_an_unused_paused_rate(self):
        duration = F(1, 1 << 1023)
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
        paused = native._affine_law(F(0), F(4), duration, running=False)
        self.assertEqual(paused.slope, F(1 << 1025))
        sample_pair((F(0), F(0)), (F(4), F(0)), duration, F(0),
                    running=False, work=ReachExecutionWork())
        with self.assertRaises(ReachAdmissionError) as candidate:
            native._affine_law(F(0), F(4), duration, running=True)
        with self.assertRaises(ReachAdmissionError) as ordinary:
            sample_pair((F(0), F(0)), (F(4), F(0)), duration, F(0),
                        running=True, work=ReachExecutionWork())
        self.assertEqual(candidate.exception.reach_code, ordinary.exception.reach_code)

    def test_leaf_projection_reuse_keeps_exact_bits_inverse_identity_and_fresh_parents(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        reference = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        pose = Pose(position=(0.25, -0.125, 0.0), rotation=(3.0, 0.0, 0.0, 4.0))
        def build(value, *, inverse=False):
            return (native.source_ops.inverse_pose(value) if inverse else native.source_ops.constant_pose(value))
        with patch.object(native, "_pose", wraps=native._pose) as projected:
            for inverse in (False, True):
                actual = native.recording_constant_pose(pose, inverse=inverse, build=build)
                expected = reference._pose(reference.source_ops.inverse_pose(pose) if inverse else
                                           reference.source_ops.constant_pose(pose))
                self.assertEqual(struct.pack("<7d", *actual.position, *actual.orientation),
                                 struct.pack("<7d", *expected.position, *expected.orientation))
                self.assertIs(native.recording_constant_pose(pose, inverse=inverse, build=build), actual)
            self.assertEqual(projected.call_count, 2)
        leaf = native.recording_constant_pose(pose, build=build)
        for position in ((F(0), F(0), F(0)), (F(2), F(-3), F(1))):
            parent = native.make_recording(position)
            actual = native.compose_recording_fast(parent, leaf)
            self.assertIsInstance(actual, _FloatPose)
            self.assertEqual(actual.position, tuple(float(a) + b for a, b in zip(position, leaf.position)))
        changed = native.recording_constant_pose(replace(pose, position=(0.5, -0.125, 0.0)), build=build)
        self.assertNotEqual(changed.position, leaf.position)

    def test_law_leaf_and_cursor_hits_recheck_callbacks_and_the_live_domain(self):
        for kind in ("law", "leaf", "cursor"):
            for narrow in (False, True):
                with self.subTest(kind=kind, narrow=narrow):
                    native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
                    law = native._affine_law(F(0), F(1), F(2), running=True)
                    coordinate = _AffineCoordinate(law, F(1, 3), True)
                    args = dict(context=object(), path="hinge:joint", max_steps=10000)
                    # A nonidentity rotation exercises the retained leaf cache;
                    # direct identity leaves have their own checkpoint tests.
                    pose = Pose(position=(0.25, 0.0, 0.0), rotation=(1.0, 0.0, 0.0, 0.25))
                    build = lambda value, inverse=False: native.source_ops.constant_pose(value)
                    native.recording_constant_pose(pose, build=build)
                    native.recording_axis_rotation((0, 0, 1), coordinate, **args)
                    marker = RuntimeError("cancel affine recording reuse")
                    charge = native.work.charge
                    def interrupt(event="checkpoint", amount=1):
                        if event == "cache_promote":
                            native.work.external_check = (lambda: setattr(native.work, "max_operand_bits", 128)
                                if narrow else (_ for _ in ()).throw(marker))
                        return charge(event, amount)
                    with patch.object(native.work, "charge", side_effect=interrupt):
                        with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                            if kind == "law":
                                native._affine_law(F(0), F(1), F(2), running=True)
                            elif kind == "leaf":
                                native.recording_constant_pose(pose, build=build)
                            else:
                                native.recording_axis_rotation((0, 0, 1), coordinate, **args)
                    if not narrow:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(native.work.callback_error, marker)

    def test_cancelled_affine_cursor_publication_keeps_the_previous_completed_cursor(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), affine_coordinates=True)
        law = native._affine_law(F(0), F(1), F(2), running=True)
        coordinate = _AffineCoordinate(law, F(1, 3), True)
        args = dict(context=object(), path="hinge:joint", max_steps=10000)
        native.recording_axis_rotation((0, 0, 1), coordinate, **args)
        key, previous = next((key, value) for key, value in native.work._cache.items()
                             if "bounded_affine_axis" in key)
        marker = RuntimeError("cancel affine cursor publication")
        remember = native.work.remember
        def interrupted(candidate_key, value):
            if candidate_key == key:
                native.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return remember(candidate_key, value)
        with patch.object(native.work, "remember", side_effect=interrupted):
            with self.assertRaises(RuntimeError) as caught:
                native.recording_axis_rotation((0, 0, 1), replace(coordinate, elapsed=F(2, 3)), **args)
        self.assertIs(caught.exception, marker)
        self.assertIs(native.work.callback_error, marker)
        self.assertIs(native.work._cache[key], previous)

    def test_real_pause_resume_and_ownership_samples_enclose_source_without_mutating_it(self):
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame")
        cases = (("L01", ((F(0), F(1, 2)), (F(1, 2), F(3, 2)), (F(3, 2), F(3)))),
                 ("L02", ((F(0), F(1, 2)), (F(1, 2), F(3, 2)))))
        for case, phases in cases:
            candidate, baseline = simulator(case), simulator(case)
            for start, end in phases:
                with self.subTest(case=case, start=start):
                    for sim in (candidate, baseline):
                        sim.advance(start, "after")
                    bounds = candidate.phase_bounds(start, end)["frames"]
                    baseline.phase_bounds(start, end)
                    moving = candidate.recording_moving_frames(candidate.state, paths)
                    contexts = (object(), object())
                    for sim, context in zip((candidate, baseline), contexts):
                        sim.recording_frames(start, sim.state, paths,
                            moving_frames=moving, recording_context=context)
                    before = copy.deepcopy(candidate.state)
                    time = (start + end) / 2
                    with patch.object(candidate, "_coordinate", side_effect=AssertionError(
                            "A bounded hinge interior uses its exact affine law")):
                        actual = sample_bounded_frames(candidate, time, candidate.state, paths,
                            context=contexts[0], moving_frames=moving, phase_bounds=bounds)
                    expected = baseline.recording_frames(time, baseline.state, paths,
                        moving_frames=moving, recording_context=contexts[1])
                    self.assertEqual(candidate.state, before)
                    for path in paths:
                        allowance = actual.excess_by_frame[path]
                        self.assertLessEqual(max(abs(F(a) - F(b)) for a, b in zip(
                            actual.frames[path].position, expected[path].position)), allowance.position_m)
                        self.assertLessEqual(projective_error(actual.frames[path].orientation,
                            expected[path].orientation), allowance.quaternion_component)
                    for joint in ("rig.arm.shoulder", "rig.arm.elbow"):
                        self.assertEqual(candidate._coordinate(joint, time, candidate.state),
                                         baseline._coordinate(joint, time, baseline.state))
            self.assertLessEqual(candidate.work.operations, 100000)

    def test_wide_clock_requests_whole_phase_fallback_with_work_retained(self):
        sim = simulator("P01")
        sim.advance(F(0), "after")
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame")
        bounds = sim.phase_bounds(F(0), F(2))["frames"]
        moving = sim.recording_moving_frames(sim.state, paths)
        before = sim.work.operations
        with self.assertRaises(RecordingRoundingAmbiguity):
            sample_bounded_frames(sim, F(1, 1 << 1200), sim.state, paths,
                context=object(), moving_frames=moving, phase_bounds=bounds)
        self.assertGreater(sim.work.operations, before)
        self.assertEqual(sim.work.max_operand_bits, 32768)
        self.assertEqual(sim.work.max_operations, 100000)


if __name__ == "__main__":
    unittest.main()
