"""Native root translation keeps the exact source equation and exposure bits."""
from copy import deepcopy
from fractions import Fraction as F
import math
import struct
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_recording_fast import (
    Binary64RecordingOps, _ExactAffinePosition, _FloatRotation, _UnsupportedPlanar,
    sample_bounded_frames,
)
from test_reach_recording_captured_seed import PATHS, prepared


IDENTITY = _FloatRotation(1.0, 0.0, False, True)


def packed(position):
    return struct.pack("<ddd", *position)


def native_ops(**limits):
    return Binary64RecordingOps(ReachPoseOps(ReachExecutionWork(**limits)))


class ReachRecordingExactAffinePositionTests(unittest.TestCase):
    def test_exact_values_and_exposure_bits_cover_rationals_ties_and_subnormal_zeros(self):
        cases = (
            ((F(1, 3), F(-2, 7), F(0)), (F(2, 5), F(0), F(-3, 2)), F(7, 11)),
            ((0.0, -0.0, math.ldexp(1.0, -1074)), (0.5, -0.0, 0.0), F(1, 3)),
            ((F(1), F(-1), F(0)), (F(-2), F(2), F(0)), F(1, 2)),
            ((0, 0, 0), (F(1, 2**1075), F(-1, 2**1075), F(3, 2**1075)), F(1)),
            ((F(0), F(0), F(0)), (F(1, 2**2047), F(-1, 2**2047), F(0)), F(1, 2**2047)),
            ((F(1, 7), F(2, 9), F(-3, 11)), (F(0), F(0), F(0)), F(-5, 3)),
            ((1.0, 2.0, -3.0), (0.25, -0.5, 1.0), F(0)),
            ((1.0, 2.0, -3.0), (0.25, -0.5, 1.0), F(1)),
        )
        for initial, rate, elapsed in cases:
            with self.subTest(initial=initial, rate=rate, elapsed=elapsed):
                native, reference = native_ops(), native_ops()
                actual = native.recording_affine(initial, rate, elapsed)
                expected = reference.source_ops.recording_affine(initial, rate, elapsed)
                self.assertIs(type(actual), _ExactAffinePosition)
                self.assertEqual(actual.values, expected)
                a = native.make_recording(actual, IDENTITY)
                b = reference.make_recording(expected, IDENTITY)
                self.assertEqual(packed(a.position), packed(b.position))
                self.assertEqual(a.zeros, b.zeros)
                self.assertEqual(a.rotation, b.rotation)
                self.assertEqual(native.work.operations, sum(native.work.counts.values()))

    def test_large_mutable_and_nonfraction_clock_inputs_keep_the_ordinary_exact_path(self):
        for initial, rate, elapsed in (
                ([0.0, -0.0, 0.0], (0.5, 0.0, 0.0), F(1, 3)),
                ((F(1, 2**4096), F(0), F(0)), (0, 0, 0), F(1, 3)),
                ((0, 0, 0), (1, 0, 0), F(1, 2**4096)),
                ((0, 0, 0), (0.5, 0, 0), 0.25)):
            with self.subTest(initial=initial, elapsed=elapsed):
                native, reference = native_ops(), native_ops()
                with patch.object(native.source_ops, "recording_affine",
                                  wraps=native.source_ops.recording_affine) as fallback:
                    actual = native.recording_affine(initial, rate, elapsed)
                self.assertEqual(fallback.call_count, 1)
                expected = reference.source_ops.recording_affine(initial, rate, elapsed)
                self.assertIs(type(actual), tuple)
                self.assertEqual(actual, expected)
                self.assertEqual(packed(native.make_recording(actual, IDENTITY).position),
                                 packed(reference.make_recording(expected, IDENTITY).position))

    def test_invalid_inputs_and_projection_overflow_keep_original_failures(self):
        for initial, rate, elapsed in (
                ((False, 0, 0), (1, 0, 0), F(1, 3)),
                ((float("nan"), 0, 0), (1, 0, 0), F(1, 3)),
                ((0, 0), (1, 0, 0), F(1, 3)),
                ((0, 0, 0), (1, 0, 0), True),
                ((F(2**1024), F(0), F(0)), (0, 0, 0), F(1))):
            with self.subTest(initial=initial, elapsed=elapsed):
                errors = []
                for optimized in (False, True):
                    native = native_ops()
                    with self.assertRaises(ReachAdmissionError) as caught:
                        exact = (native.recording_affine(initial, rate, elapsed) if optimized else
                                 native.source_ops.recording_affine(initial, rate, elapsed))
                        native.make_recording(exact, IDENTITY)
                    errors.append((caught.exception.reach_code, caught.exception.details,
                                   str(caught.exception)))
                self.assertEqual(errors[0], errors[1])
        native = native_ops()
        for malformed in ((F(0), F(0)), (False, F(0), F(0)), [F(0), F(0), F(0)]):
            with self.subTest(malformed=malformed), self.assertRaises(_UnsupportedPlanar):
                native.make_recording(_ExactAffinePosition(malformed), IDENTITY)

    def test_repeated_keys_remove_actual_work_without_retaining_sample_positions(self):
        native, reference = native_ops(), native_ops()
        initial, rate = (0.0, 0.0, 0.0), (0.5, 0.0, 0.0)
        for index in range(1, 41):
            time = F(index, 41)
            actual = native.make_recording(native.recording_affine(initial, rate, time), IDENTITY)
            expected = reference.make_recording(
                reference.source_ops.recording_affine(initial, rate, time), IDENTITY)
            self.assertEqual(packed(actual.position), packed(expected.position))
        self.assertLess(native.work.operations, reference.work.operations)
        self.assertEqual(sum("exact_affine_source_vectors" in key for key in native.work._cache), 1)
        self.assertFalse(any("vector_projection" in key for key in native.work._cache))
        self.assertLessEqual(len(native.work._cache), 256)
        self.assertEqual(native.work.operations, sum(native.work.counts.values()))

    def test_current_operand_types_values_and_eviction_scope_the_shared_law_cache(self):
        native = native_ops(max_cache_entries=3)
        initial, rate = (0.0, 0.0, 0.0), (0.5, 0.0, 0.0)
        first = native.recording_affine(initial, rate, F(1, 3))
        variants = (
            ((0, 0, 0), rate), ((-0.0, 0.0, 0.0), rate),
            ((1.0, 0.0, 0.0), rate), (initial, (0.25, 0.0, 0.0)),
        )
        keys = set(native.work._cache)
        for new_initial, new_rate in variants:
            result = native.recording_affine(new_initial, new_rate, F(1, 3))
            expected = tuple(F(a) + F(b)/3 for a, b in zip(new_initial, new_rate))
            self.assertEqual(result.values, expected)
            keys.update(native.work._cache)
            self.assertLessEqual(len(native.work._cache), 3)
        self.assertEqual(len(keys), 5)
        self.assertGreater(native.work.counts.get("cache_evict", 0), 0)
        self.assertEqual(native.recording_affine(initial, rate, F(1, 3)), first)

    def test_live_cap_changes_and_cancellation_cannot_publish_a_partial_projection(self):
        initial, rate = (0.0, 0.0, 0.0), (0.5, 0.0, 0.0)
        for checkpoint in ("cache_lookup", "cache_promote", "cache_insert",
                           "pose_scale_identity_check", "recording_affine_position_guard", "binary64_round"):
            for cancel in (False, True):
                with self.subTest(checkpoint=checkpoint, cancel=cancel):
                    native = native_ops()
                    if checkpoint == "cache_promote":
                        native.recording_affine(initial, rate, F(1, 4))
                    marker, seen, charge = RuntimeError("cancel exact root projection"), [], native.work.charge
                    def interrupt():
                        if cancel:
                            raise marker
                        native.work.max_operand_bits = 128
                    def charged(kind="checkpoint", amount=1):
                        if kind == checkpoint and not seen:
                            seen.append(kind)
                            native.work.external_check = interrupt
                        return charge(kind, amount)
                    with patch.object(native.work, "charge", side_effect=charged):
                        with self.assertRaises(RuntimeError if cancel else _UnsupportedPlanar) as caught:
                            value = native.recording_affine(initial, rate, F(1, 3))
                            native.make_recording(value, IDENTITY)
                    self.assertEqual(seen, [checkpoint])
                    if cancel:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(native.work.callback_error, marker)
                    self.assertFalse(any("vector_projection" in key for key in native.work._cache))
                    self.assertLessEqual(len(native.work._cache), 256)

    def test_original_exact_arithmetic_failure_identity_is_not_retried(self):
        native = native_ops()
        marker = ReachAdmissionError("reach_resource", "original affine multiplication",
                                     budget="numeric_operand_bits", limit=128, consumed=129)
        calls = []
        def refuse(*args):
            calls.append(args)
            native.work.max_operand_bits = 128
            raise marker
        with patch.object(native.source_ops, "_op", side_effect=refuse):
            with self.assertRaises(ReachAdmissionError) as caught:
                native.recording_affine((0.0, 0.0, 0.0), (0.5, 0.0, 0.0), F(1, 3))
        self.assertIs(caught.exception, marker)
        self.assertEqual(len(calls), 1)

    def test_actual_moving_source_samples_preserve_frames_and_source_state(self):
        outputs = []
        ordinary = ReachPoseOps.recording_affine
        for optimized in (False, True):
            sim, phase = prepared()
            state = deepcopy(sim.state)
            context = object()
            frames = []
            def original(ops, initial, rate, elapsed):
                return ordinary(ops, initial, rate, elapsed)
            with patch.object(Binary64RecordingOps, "recording_affine",
                              Binary64RecordingOps.recording_affine if optimized else original):
                for time in (F(1, 8), F(1, 4), F(3, 8), F(1, 2)):
                    sample = sample_bounded_frames(sim, time, sim.state, PATHS, context=context,
                        moving_frames=sim.recording_moving_frames(sim.state, PATHS),
                        phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                        recording_angular_proof=phase["recording_angular_proof"])
                    frames.append(sample.frames)
            self.assertEqual(sim.state, state)
            outputs.append(frames)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
