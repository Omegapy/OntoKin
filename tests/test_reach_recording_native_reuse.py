"""Native recording reuses completed work without changing actual candidates."""
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_recording_fast as recording
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, float_bits
from ontokin.reach_pose import ReachPoseOps, UNIT
from ontokin.reach_recording_fast import (Binary64RecordingOps, RecordingRoundingAmbiguity,
                                        _UnsupportedPlanar, sample_bounded_frames)
from test_reach_recording_sampler import simulator


def native_ops():
    return Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))


def rotation_bits(value):
    return float_bits(value.w), float_bits(value.z), value.zero_w, value.zero_z


class ReachRecordingNativeReuseTests(unittest.TestCase):
    def test_fixed_vector_and_spin_proof_reuse_preserves_native_bits_and_reseeds(self):
        actual, original = native_ops(), native_ops()
        omega, axis = (0.0, 0.0, 0.25), (0.0, 0.0, 1.0)
        plans = tuple(ops.source_ops.spin_plan(omega, F(3)) for ops in (actual, original))
        contexts = object(), object()
        times = [F(index + 1, 128) for index in range(130)] + [F(3, 4), F(1, 2), F(1, 2)]
        with ExitStack() as stack:
            stack.enter_context(patch.object(original.source_ops, "_recording_vector",
                                             original.source_ops._vector))
            stack.enter_context(patch.object(original, "_reusable_spin_plan", return_value=False))
            for time in times:
                rotations = []
                for ops, plan, context in zip((actual, original), plans, contexts):
                    hinge = ops.recording_axis_rotation(axis, time, context=context,
                        path="hinge:arm", max_steps=10000)
                    root = ops.recording_advance_orientation(UNIT, omega, time,
                        context=context, path="prescribed:root", max_steps=10000, phase_plan=plan)
                    rotations.append((rotation_bits(hinge), rotation_bits(root)))
                self.assertEqual(*rotations)
        self.assertLess(actual.work.operations, original.work.operations)
        self.assertLess(actual.work.counts["binary64_decode"], original.work.counts["binary64_decode"])
        self.assertLess(actual.work.counts["spin_plan_identity"], original.work.counts["spin_plan_identity"])
        for ops in (actual, original):
            self.assertLessEqual(len(ops.work._cache), 256)
            self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))

    def test_completed_spin_identity_still_checks_each_clock_and_changed_plan(self):
        native = native_ops()
        omega = (0.0, 0.0, 0.25)
        plan = native.source_ops.spin_plan(omega, F(3))
        arguments = dict(context=object(), path="prescribed:root", max_steps=10000, phase_plan=plan)
        for time in (F(1, 8), F(1, 4)):
            native.recording_advance_orientation(UNIT, omega, time, **arguments)
        with patch.object(native.source_ops, "_checked_spin_plan",
                          side_effect=AssertionError("unchanged completed spin identity")):
            native.recording_advance_orientation(UNIT, omega, F(3, 8), **arguments)
            with self.assertRaises(ReachAdmissionError):
                native.recording_advance_orientation(UNIT, omega, F(4), **arguments)
        with self.assertRaises(ReachAdmissionError):
            native.recording_advance_orientation(UNIT, (0.0, 0.0, 0.5), F(1, 2), **arguments)
        changed = replace(plan, maximum=F(1, 2))
        with self.assertRaises(ReachAdmissionError):
            native.recording_advance_orientation(UNIT, omega, F(1, 2),
                                                **(arguments | {"phase_plan": changed}))
        with patch.object(native.source_ops, "_checked_spin_plan",
                          wraps=native.source_ops._checked_spin_plan) as checked:
            changed = replace(plan, argument_error_rad=plan.argument_error_rad * 2)
            native.recording_advance_orientation(UNIT, omega, F(1, 2),
                                                **(arguments | {"phase_plan": changed}))
        self.assertGreater(checked.call_count, 0)

    def test_spin_cursor_hit_retains_live_cap_and_cancellation_identity(self):
        for narrow in (False, True):
            with self.subTest(narrow=narrow):
                native = native_ops()
                omega = (0.0, 0.0, 0.25)
                plan = native.source_ops.spin_plan(omega, F(3))
                arguments = dict(context=object(), path="prescribed:root", max_steps=10000,
                                 phase_plan=plan)
                for time in (F(1, 8), F(1, 4)):
                    native.recording_advance_orientation(UNIT, omega, time, **arguments)
                key = next(key for key in native.work._cache if "certified_binary64_spin" in key)
                previous, lookup = native.work._cache[key], native.work.lookup
                marker = RuntimeError("cancel completed native spin identity")
                def interrupt(current):
                    if "certified_binary64_spin" in current:
                        native.work.external_check = (lambda: setattr(native.work, "max_operand_bits", 128)
                            if narrow else (_ for _ in ()).throw(marker))
                    return lookup(current)
                with patch.object(native.work, "lookup", side_effect=interrupt):
                    with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                        native.recording_advance_orientation(UNIT, omega, F(3, 8), **arguments)
                if narrow:
                    self.assertNotIn(key, native.work._cache)
                else:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(native.work.callback_error, marker)
                    self.assertIs(native.work._cache[key], previous)

    def test_reused_vector_decoding_admits_every_current_axis_and_velocity(self):
        native = native_ops()
        axis, omega = (0.0, 0.0, 1.0), (0.0, 0.0, 0.25)
        plan = native.source_ops.spin_plan(omega, F(3))
        arguments = dict(context=object(), path="hinge:arm", max_steps=10000)
        native.recording_axis_rotation(axis, F(1, 8), **arguments)
        native.recording_advance_orientation(UNIT, omega, F(1, 8), **arguments, phase_plan=plan)
        for invalid in ((False, 0.0, 1.0), (float("nan"), 0.0, 1.0),
                        (0.0, float("inf"), 1.0), (0.0, 1.0), (F(1 << 32768), F(0), F(1))):
            with self.subTest(invalid_type=type(invalid[0]).__name__):
                with self.assertRaises((ReachAdmissionError, _UnsupportedPlanar)):
                    native.recording_axis_rotation(invalid, F(1, 4), **arguments)
                with self.assertRaises((ReachAdmissionError, _UnsupportedPlanar)):
                    native.recording_advance_orientation(UNIT, invalid, F(1, 4),
                                                        **arguments, phase_plan=plan)

    def test_ballistic_law_reuses_only_identical_completed_phase_relations(self):
        native = native_ops()
        position, velocity, acceleration = (1.0, 0.0, 0.0), (0.5, 0.0, 0.0), (0.25, 0.0, 0.0)
        arguments = dict(anchor_time=F(0), phase_interval=(F(0), F(2)), scene_duration=F(4),
                         root_extent=F(10), context=object(), path="body")
        first = native._ballistic_law(position, velocity, acceleration, **arguments)
        with patch.object(recording, "_checked_compare",
                          side_effect=AssertionError("completed immutable phase ordering")):
            self.assertIs(native._ballistic_law(position, velocity, acceleration, **arguments), first)
        for changes in ({"anchor_time": F(1)}, {"phase_interval": (F(2), F(1))},
                        {"scene_duration": F(1)}, {"root_extent": F(0)}):
            with self.subTest(changes=changes), self.assertRaises(_UnsupportedPlanar):
                native._ballistic_law(position, velocity, acceleration, **(arguments | changes))
        self.assertLessEqual(len(native.work._cache), 256)

    def test_ballistic_cache_preserves_signed_zero_coefficient_bits(self):
        native = native_ops()
        velocity, acceleration = (-float.fromhex("0x0.0000000000001p-1022"), 0.0, 0.0), (0.0, 0.0, 0.0)
        arguments = dict(anchor_time=F(0), phase_interval=(F(0), F(1)), scene_duration=F(1),
                         root_extent=F(1), context=object(), path="body")
        laws = [native._ballistic_law((zero, 0.0, 0.0), velocity, acceleration, **arguments)
                for zero in (0.0, -0.0)]
        self.assertIsNot(*laws)
        values = [native._ballistic_position(law, F(1, 2**250))[0][0] for law in laws]
        self.assertEqual(tuple(float_bits(value) for value in values), (0, 1 << 63))

    def test_equal_dynamic_extent_receipt_omits_only_its_completed_comparison(self):
        samples, operations = [], []
        original = Binary64RecordingOps.recording_dynamic_pose
        def force_fresh_comparison(ops, simulator, path, time, state, **keywords):
            value = original(ops, simulator, path, time, state, **keywords)
            law = ops.dynamic_extents[path]
            ops.dynamic_extents[path] = replace(law, proved_extent=law.proved_extent + 1)
            return value
        for reuse in (False, True):
            sim = simulator("P16")
            sim.advance(F(2), "after")
            bounds = sim.phase_bounds(F(2), F(3))["frames"]
            paths, context = ("payload.frame",), object()
            moving = sim.recording_moving_frames(sim.state, paths)
            before = sim.work.operations
            with ExitStack() as stack:
                if not reuse:
                    stack.enter_context(patch.object(Binary64RecordingOps, "recording_dynamic_pose",
                                                     force_fresh_comparison))
                result = sample_bounded_frames(sim, F(9, 4), sim.state, paths, context=context,
                    moving_frames=moving, phase_bounds=bounds, phase_interval=(F(2), F(3)))
            samples.append(result)
            operations.append(sim.work.operations - before)
            self.assertEqual(sim.work.counts["recording_dynamic_path_extent"], 1)
        self.assertEqual(samples[0], samples[1])
        self.assertEqual(operations[0] - operations[1], 1)

    def test_warm_dynamic_root_cannot_authorize_a_changed_descendant_extent(self):
        sim = simulator("P16")
        sim.advance(F(2), "after")
        bounds = sim.phase_bounds(F(2), F(3))["frames"]
        paths, context = ("payload.origin.frame",), object()
        moving = sim.recording_moving_frames(sim.state, paths)
        before = deepcopy(sim.state)
        sample_bounded_frames(sim, F(9, 4), sim.state, paths, context=context,
            moving_frames=moving, phase_bounds=bounds, phase_interval=(F(2), F(3)))
        changed = bounds | {paths[0]: replace(bounds[paths[0]], max_position_l1_m=F(0))}
        with self.assertRaises(RecordingRoundingAmbiguity):
            sample_bounded_frames(sim, F(5, 2), sim.state, paths, context=context,
                moving_frames=moving, phase_bounds=changed, phase_interval=(F(2), F(3)))
        self.assertEqual(sim.state, before)
        self.assertLessEqual(len(sim.work._cache), 256)


if __name__ == "__main__":
    unittest.main()
