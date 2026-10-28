"""Native dynamic interiors retain exact source anchors and explicit error."""
from dataclasses import replace
from fractions import Fraction as F
import copy
import math
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_fast import (
    Binary64RecordingOps, RecordingRoundingAmbiguity, _UnsupportedPlanar,
    recording_float_excess, sample_bounded_frames, sample_certified_frames,
)
from test_reach_recording_affine import projective_error
from test_reach_recording_sampler import simulator


def extent(position, velocity, acceleration, horizon):
    """Independent exact polynomial magnitude for the numerical oracle."""
    return (sum(abs(F(v)) for v in position)
            + horizon * sum(abs(F(v)) for v in velocity)
            + horizon * horizon * sum(abs(F(v)) for v in acceleration) / 2)


def law(native, position, velocity, acceleration, horizon, *, context=None, path="body"):
    return native._ballistic_law(position, velocity, acceleration, anchor_time=F(0),
        phase_interval=(F(0), horizon), root_extent=extent(position, velocity, acceleration, horizon),
        context=object() if context is None else context, path=path)


class ReachRecordingDynamicTests(unittest.TestCase):
    def test_native_horner_encloses_exact_polynomial_with_rounded_time_and_underflow(self):
        tiny = math.ldexp(1.0, -1074)
        cases = (
            ((0.25, -0.125, 0.0), (0.5, -0.75, 0.0), (0.1, 0.2, 0.0), F(2),
             (F(0), F(1, 3), F(1, 7), F(2))),
            ((0.0, tiny, 0.0), (tiny, -tiny, 0.0), (tiny, tiny, 0.0), F(1),
             (F(1, 2**250), F(1, 3), F(1))),
            ((1.0, -1.0, 0.0), (float(2**249), -float(2**249), 0.0),
             (-float(2**250), float(2**250), 0.0), F(2), (F(1, 3), F(1), F(2))),
            ((1.0, 0.0, 0.0), (math.ldexp(1.0, -250), 0.0, 0.0),
             (math.ldexp(1.0, -500), 0.0, 0.0), F(2**250), (F(2**250),)),
        )
        rounded_clock = False
        for position, velocity, acceleration, horizon, times in cases:
            native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
            proved = law(native, position, velocity, acceleration, horizon)
            self.assertEqual(proved.extent, extent(position, velocity, acceleration, horizon))
            for elapsed in times:
                with self.subTest(position=position, elapsed=elapsed):
                    actual, zeros = native._ballistic_position(proved, elapsed)
                    expected = tuple(F(p) + F(v) * elapsed + F(a) * elapsed * elapsed / 2
                                     for p, v, a in zip(position, velocity, acceleration))
                    error = sum(abs(F(a) - b) for a, b in zip(actual, expected))
                    self.assertLessEqual(error, F(1, 2**47) * (proved.extent + 1))
                    self.assertEqual(zeros, tuple(not p and not v and not a
                        for p, v, a in zip(position, velocity, acceleration)))
                    rounded_clock |= F(float(elapsed)) != elapsed
            self.assertEqual(native.work.operations, sum(native.work.counts.values()))
            self.assertLessEqual(native.work.operations, 100000)
            self.assertEqual(native.work.max_operand_bits, 32768)
        self.assertTrue(rounded_clock)

    def test_bounded_actual_operands_keep_every_native_intermediate_below_2_to_752(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        vector = (float(2**250),) * 3
        proved = law(native, vector, vector, vector, F(2**250))
        seen = []
        original = native._native
        def observe(*args):
            value = original(*args)
            seen.append(value)
            return value
        # This law is finite but its final position exceeds the narrower
        # composition domain. It must request fallback, not overflow first.
        with patch.object(native, "_native", side_effect=observe):
            with self.assertRaises(_UnsupportedPlanar):
                native._ballistic_position(proved, F(2**250))
        self.assertTrue(seen)
        self.assertTrue(all(math.isfinite(v) and abs(F(v)) < 2**752 for v in seen))
        self.assertGreater(max(abs(F(v)) for v in seen), 2**500)

    def test_law_and_clock_guards_reject_unproved_domains_before_native_arithmetic(self):
        zero = (0.0, 0.0, 0.0)
        for invalid in (False, 0, F(0), float("inf"), float("nan"), float(2**251)):
            native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
            with self.assertRaises(_UnsupportedPlanar):
                native._ballistic_law((invalid, 0.0, 0.0), zero, zero,
                    anchor_time=F(0), phase_interval=(F(0), F(1)), root_extent=F(2**252),
                    context=object(), path="body")
            self.assertNotIn("recording_float_mul", native.work.counts)
        for invalid in (F(-1), F(2), F(1, 2**251), F(1, 2**1200)):
            native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
            proved = law(native, zero, zero, zero, F(1))
            with self.assertRaises(_UnsupportedPlanar):
                native._ballistic_position(proved, invalid)
            self.assertNotIn("recording_float_mul", native.work.counts)
        for anchor, phase in ((F(-1), (F(0), F(1))), (F(1), (F(0), F(1))),
                              (F(0), (F(1), F(0))), (F(0), (F(0), F(2**251)))):
            native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
            with self.assertRaises(_UnsupportedPlanar):
                native._ballistic_law(zero, zero, zero, anchor_time=anchor,
                    phase_interval=phase, root_extent=F(0), context=object(), path="body")
            self.assertNotIn("recording_float_mul", native.work.counts)

    def test_completed_law_is_bound_to_actual_coefficients_anchor_phase_and_context(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        position, velocity, acceleration = (1.0, 0.0, 0.0), (0.5, 0.0, 0.0), (0.25, 0.0, 0.0)
        arguments = dict(anchor_time=F(0), phase_interval=(F(0), F(2)),
                         root_extent=F(10), context=object(), path="body")
        first = native._ballistic_law(position, velocity, acceleration, **arguments)
        with patch.object(native.source_ops, "_vector", side_effect=AssertionError("completed immutable law")):
            self.assertIs(native._ballistic_law(position, velocity, acceleration, **arguments), first)
        for changes in ({"anchor_time": F(1), "phase_interval": (F(1), F(2))},
                        {"phase_interval": (F(0), F(3))}, {"context": object()}, {"path": "other"}):
            current = native._ballistic_law(position, velocity, acceleration, **(arguments | changes))
            self.assertIsNot(current, first)
        changed = native._ballistic_law(position, velocity, (0.0, 0.0, 0.0), **arguments)
        self.assertNotEqual(changed.extent, first.extent)
        with self.assertRaises(_UnsupportedPlanar):
            native._ballistic_law(position, velocity, acceleration, **(arguments | {"root_extent": F(0)}))
        self.assertLessEqual(len(native.work._cache), 256)

    def test_law_hits_recheck_callback_identity_and_live_operand_cap(self):
        zero = (0.0, 0.0, 0.0)
        for narrow in (False, True):
            native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
            context = object()
            law(native, zero, zero, zero, F(1), context=context)
            marker = RuntimeError("cancel dynamic law reuse")
            charge = native.work.charge
            def interrupt(event="checkpoint", amount=1):
                if event == "cache_promote":
                    native.work.external_check = (lambda: setattr(native.work, "max_operand_bits", 128)
                        if narrow else (_ for _ in ()).throw(marker))
                return charge(event, amount)
            with patch.object(native.work, "charge", side_effect=interrupt):
                with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                    law(native, zero, zero, zero, F(1), context=context)
            if not narrow:
                self.assertIs(caught.exception, marker)
                self.assertIs(native.work.callback_error, marker)

    def test_cancelled_law_publication_preserves_previous_completed_proof(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        zero = (0.0, 0.0, 0.0)
        old_context, new_context = object(), object()
        previous = law(native, zero, zero, zero, F(1), context=old_context)
        old_key = next(key for key, value in native.work._cache.items() if value is previous)
        marker = RuntimeError("cancel dynamic law publication")
        remember = native.work.remember
        def interrupt(key, value):
            if "ballistic_law" in key:
                native.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return remember(key, value)
        with patch.object(native.work, "remember", side_effect=interrupt):
            with self.assertRaises(RuntimeError) as caught:
                law(native, zero, zero, zero, F(1), context=new_context)
        self.assertIs(caught.exception, marker)
        self.assertIs(native.work.callback_error, marker)
        self.assertIs(native.work._cache[old_key], previous)
        self.assertFalse(any("ballistic_law" in key and new_context in key for key in native.work._cache))

    def test_actual_release_and_force_phases_enclose_source_without_changing_state_or_rates(self):
        paths = ("payload.frame", "payload.origin.frame", "rig.arm.forearm.frame")
        for start, end in ((F(0), F(2)), (F(2), F(3)), (F(3), F(4))):
            candidate, baseline = simulator("P16"), simulator("P16")
            for sim in (candidate, baseline):
                sim.advance(start, "after")
            bounds = candidate.phase_bounds(start, end)["frames"]
            baseline.phase_bounds(start, end)
            moving = candidate.recording_moving_frames(candidate.state, paths)
            contexts = (object(), object())
            for sim, context in zip((candidate, baseline), contexts):
                sim.recording_frames(start, sim.state, paths, moving_frames=moving, recording_context=context)
            before = copy.deepcopy(candidate.state)
            for time in (start + (end - start) / 7, start + 3 * (end - start) / 4):
                with self.subTest(start=start, time=time):
                    with patch.object(candidate, "_dynamic_kinematics", side_effect=AssertionError(
                            "The supported dynamic interior must use its bounded native law")):
                        actual = sample_bounded_frames(candidate, time, candidate.state, paths,
                            context=contexts[0], moving_frames=moving, phase_bounds=bounds,
                            phase_interval=(start, end))
                    expected = baseline.recording_frames(time, baseline.state, paths,
                        moving_frames=moving, recording_context=contexts[1])
                    for path in paths:
                        allowance = actual.excess_by_frame[path]
                        self.assertLessEqual(sum(abs(F(a) - F(b)) for a, b in zip(
                            actual.frames[path].position, expected[path].position)), allowance.position_m)
                        self.assertLessEqual(projective_error(actual.frames[path].orientation,
                            expected[path].orientation), allowance.quaternion_component)
                        ordinary = recording_float_excess(bounds[path], work=candidate.work,
                                                          include_cell_radii=False)
                        added = (F(1, 2**47) * (bounds[path].max_position_l1_m
                                 + bounds[path].path_offset_l1_m + 1)
                                 if start >= 2 and path.startswith("payload.") else F(0))
                        self.assertEqual(allowance.position_m - ordinary.position_m, added)
                        self.assertEqual(allowance.quaternion_component, ordinary.quaternion_component)
                    self.assertEqual(candidate.state, before)
                    if start >= 2:
                        original = candidate._dynamic_kinematics("payload", time, candidate.state)
                        reference = baseline._dynamic_kinematics("payload", time, baseline.state)
                        for field in ("position", "orientation", "velocity", "omega"):
                            self.assertEqual(getattr(original, field), getattr(reference, field))
            self.assertEqual(candidate.state, before)
            self.assertLessEqual(candidate.work.operations, 100000)

    def test_dynamic_paths_without_a_phase_or_in_strict_diagnostic_stay_ordinary(self):
        for sampler, interval in ((sample_bounded_frames, None),
                                   (sample_certified_frames, (F(2), F(3)))):
            sim = simulator("P16")
            sim.advance(F(2), "after")
            bounds = sim.phase_bounds(F(2), F(3))["frames"]
            paths = ("payload.frame", "payload.origin.frame")
            moving = sim.recording_moving_frames(sim.state, paths)
            with patch.object(Binary64RecordingOps, "recording_dynamic_pose", side_effect=AssertionError(
                    "This mode retains the ordinary complete dynamic path")):
                result = sampler(sim, F(9, 4), sim.state, paths, context=object(),
                    moving_frames=moving, phase_bounds=bounds, phase_interval=interval)
            self.assertTrue(all(value.position_m == value.quaternion_component == 0
                                for value in result.excess_by_frame.values()))

    def test_actual_phase_and_descendant_extent_guards_request_complete_fallback(self):
        for mode in ("early", "late", "outside_scene", "tiny", "extent"):
            sim = simulator("P16")
            sim.advance(F(2), "after")
            paths = ("payload.origin.frame",)
            bounds = sim.phase_bounds(F(2), F(3))["frames"]
            moving = sim.recording_moving_frames(sim.state, paths)
            time, interval = F(9, 4), (F(2), F(3))
            if mode == "early":
                time = F(1)
            elif mode == "late":
                time = F(13, 4)
            elif mode == "outside_scene":
                interval = (F(2), F(5))
            elif mode == "tiny":
                time = F(2) + F(1, 2**251)
            else:
                bounds = bounds | {paths[0]: replace(bounds[paths[0]], max_position_l1_m=F(0))}
            before = sim.work.operations
            with self.assertRaises(RecordingRoundingAmbiguity):
                sample_bounded_frames(sim, time, sim.state, paths, context=object(),
                    moving_frames=moving, phase_bounds=bounds, phase_interval=interval)
            self.assertGreater(sim.work.operations, before)
            self.assertEqual(sim.work.max_operations, 100000)
            self.assertEqual(sim.work.max_operand_bits, 32768)


if __name__ == "__main__":
    unittest.main()
