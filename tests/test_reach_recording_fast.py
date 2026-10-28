"""Stored-cell certification, finite native recording and phase fallback."""
from fractions import Fraction as F
import copy
import math
import struct
import unittest
from unittest.mock import patch
from types import SimpleNamespace as NS

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import PhaseBound
from ontokin.reach_pose import MAX_RECORDING_ROTATION_STEPS, ReachPoseOps, RotationValue, UNIT, ZERO
from ontokin.reach_recording_fast import (
    Binary64RecordingOps, RecordingRoundingAmbiguity, RecordingFloatExcess,
    certified_float32_cell, recording_float_excess, sample_certified_frames, sample_bounded_frames,
    MAX_FLOAT_ROTATION_STEPS, _FloatPose, _FloatRotation, _UnsupportedPlanar,
    _certify_pose, _rotation_cell_groups,
)
from test_reach_recording_sampler import simulator


def bits32(values):
    return b"".join(struct.pack("<f", value) for value in values)


class ReachRecordingFastTests(unittest.TestCase):
    def test_axis_projection_reuse_preserves_each_cursor_and_exact_candidate_bits(self):
        direct = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        shared = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        original = lambda axis, coordinate, structural=True: direct._project_rotation(
            direct.source_ops.axis_rotation(axis, coordinate), structural=structural)
        direct_context, shared_context = object(), object()
        coordinate = F(0)
        with patch.object(direct, "_axis_rotation", side_effect=original):
            for index in range(48):
                coordinate += F(1 + index % 2, 128)
                expected = direct.recording_axis_rotation((0, 0, 1), coordinate,
                    context=direct_context, path="hinge:joint", max_steps=10000)
                actual = shared.recording_axis_rotation((0, 0, 1), coordinate,
                    context=shared_context, path="hinge:joint", max_steps=10000)
                self.assertEqual(shared._rotation_bits(actual), direct._rotation_bits(expected))
        self.assertLess(shared.work.operations, direct.work.operations)
        self.assertEqual(shared.work.counts["recording_float_rotation_step"],
                         direct.work.counts["recording_float_rotation_step"])
        self.assertLessEqual(len(shared.work._cache), shared.work.max_cache_entries)

    def test_axis_projection_cache_preserves_structural_mode_and_live_hit_guards(self):
        for narrow in (False, True):
            with self.subTest(narrow=narrow):
                native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
                axis, coordinate = (F(0), F(0), F(1)), F(0)
                structural = native._axis_rotation(axis, coordinate)
                approximate = native._axis_rotation(axis, coordinate, structural=False)
                self.assertTrue(structural.zero_z)
                self.assertFalse(approximate.zero_z)
                marker = RuntimeError("cancel complete axis projection")
                charge = native.work.charge
                def interrupt(kind="checkpoint", amount=1):
                    if kind == "cache_promote":
                        if narrow:
                            native.work.external_check = lambda: setattr(native.work, "max_operand_bits", 128)
                        else:
                            native.work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return charge(kind, amount)
                with patch.object(native.work, "charge", side_effect=interrupt):
                    with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                        native._axis_rotation(axis, coordinate)
                if not narrow:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(native.work.callback_error, marker)

    def test_private_zero_leaf_proof_skips_only_the_known_default_projection(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        rotation = _FloatRotation(0.8, 0.6, False, False)
        with patch.object(native.source_ops, "_vector_projection",
                          side_effect=AssertionError("The fixed ZERO image is known exactly")):
            result = native.make_recording(orientation=rotation)
            self.assertEqual(result.position, (0.0, 0.0, 0.0))
            self.assertEqual(result.zeros, (True, True, True))
            with self.assertRaises(AssertionError):
                native.make_recording(position=(F(0), F(0), F(0)), orientation=rotation)
        native.work.max_operand_bits = 128
        with self.assertRaises(_UnsupportedPlanar):
            native.make_recording(position=ZERO, orientation=rotation)

    def test_bounded_samples_retain_explicit_errors_without_a_rounding_cell_claim(self):
        candidate, baseline = simulator("P09"), simulator("P09")
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.tool.frame")
        contexts = (object(), object())
        for sim in (candidate, baseline):
            sim.advance(F(0), "after")
        bounds = candidate.phase_bounds(F(0), F(2))["frames"]
        baseline.phase_bounds(F(0), F(2))
        moving = candidate.recording_moving_frames(candidate.state, paths)
        for sim, context in zip((candidate, baseline), contexts):
            sim.recording_frames(F(0), sim.state, paths, moving_frames=moving, recording_context=context)
        with patch("ontokin.reach_recording_fast.certified_float32_cell",
                   side_effect=AssertionError("A bounded endpoint makes no original-cell claim")):
            for index in range(1, 5):
                time = F(index, 137)
                result = sample_bounded_frames(candidate, time, candidate.state, paths,
                    context=contexts[0], moving_frames=moving, phase_bounds=bounds)
                expected = baseline.recording_frames(time, baseline.state, paths,
                    moving_frames=moving, recording_context=contexts[1])
                for path in paths:
                    allowance = result.excess_by_frame[path]
                    self.assertIsNone(allowance._cell_radii)
                    self.assertGreater(allowance.position_m, 0)
                    for actual, original in zip(result.frames[path].position, expected[path].position):
                        self.assertLessEqual(abs(F(actual) - F(original)), allowance.position_m)
                    actual_q, original_q = result.frames[path].orientation, expected[path].orientation
                    projective_error = min(max(abs(F(actual) - sign * F(original))
                        for actual, original in zip(actual_q, original_q)) for sign in (1, -1))
                    self.assertLessEqual(projective_error, allowance.quaternion_component)
        self.assertNotIn("recording_float_cell_domain", candidate.work.counts)
        self.assertEqual(candidate.work.max_operations, 100000)
        self.assertLessEqual(len(candidate.work._cache), 256)

    def test_native_rotation_enclosure_crosses_the_canonical_half_turn_cut(self):
        source, baseline = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        context, reference_context = object(), object()
        center = F(math.pi)
        offsets = [F(index, 2**40) for index in range(-5, 6)]
        offsets += [F(-1, 2**54), F(0), F(1, 2**54), F(-1, 2**54)]
        for offset in offsets:
            angle = center + offset
            actual = native.recording_axis_rotation((0, 0, 1), angle,
                context=context, path="hinge:joint", max_steps=10000)
            expected = baseline.recording_axis_rotation((0, 0, 1), angle,
                context=reference_context, path="hinge:joint", max_steps=10000)
            q = baseline._unit_projection(expected)
            error = min(max(abs(F(actual.w) - sign * F(q[0])),
                            abs(F(actual.z) - sign * F(q[3]))) for sign in (1, -1))
            self.assertLessEqual(error, F(1, 2**41))

    def test_broad_graph_reuses_pure_offset_arithmetic_with_each_actual_translation(self):
        direct = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))
        shared = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), share_arithmetic=True)
        rotation = _FloatRotation(0.8, 0.6, False, False)
        leaf = _FloatPose((1.0, 0.0, 0.0), _FloatRotation(1.0, 0.0, False, True),
                          (False, True, True), 0)
        for index in range(32):
            parent = _FloatPose((0.0, index / 4.0, 0.0), rotation, (True, index == 0, True), 4)
            actual = shared.compose_recording_fast(parent, leaf)
            expected = direct.compose_recording_fast(parent, leaf)
            self.assertEqual(struct.pack("<7d", *actual.position, *actual.orientation),
                             struct.pack("<7d", *expected.position, *expected.orientation))
            self.assertEqual(actual.zeros, expected.zeros)
            self.assertEqual(actual.depth, expected.depth)
        self.assertLess(shared.work.operations, direct.work.operations)
        # The first unit-X offset needs only the four coefficient products;
        # later arms reuse that completed offset with their own translation.
        self.assertEqual(shared.work.counts["recording_float_mul"], 4)
        self.assertLessEqual(len(shared.work._cache), 256)

    def test_shared_native_product_keys_preserve_operand_bits_and_structural_flags(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), share_arithmetic=True)
        b = _FloatRotation(0.8, 0.6, False, False)
        operands = (_FloatRotation(0.0, 1.0, False, False),
                    _FloatRotation(-0.0, 1.0, False, False),
                    _FloatRotation(0.0, 1.0, True, False))
        for a in operands:
            native._product(a, b)
        before = native.work.counts["recording_float_mul"]
        for a in operands:
            native._product(a, b)
        self.assertEqual(native.work.counts["recording_float_mul"], before)
        self.assertEqual(sum("native_product" in key for key in native.work._cache), 3)

    def test_native_y_offset_charges_sign_and_reuse_keeps_exact_arithmetic(self):
        native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), share_arithmetic=True)
        rotation = _FloatRotation(0.8, 0.6, False, False)
        position, zeros = (0.0, 1.0, 0.0), (True, False, True)
        first = native._rotated_offset(rotation, position, zeros)
        self.assertEqual(native.work.counts["recording_float_sign"], 1)
        self.assertEqual(native._rotated_offset(rotation, position, zeros), first)
        self.assertEqual(native.work.counts["recording_float_sign"], 1)
        self.assertLess(first[0][0], 0.0)

    def test_shared_native_cache_hit_keeps_cancellation_and_live_domain_checks(self):
        for narrow in (False, True):
            with self.subTest(narrow=narrow):
                native = Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()), share_arithmetic=True)
                a, b = _FloatRotation(0.8, 0.6, False, False), _FloatRotation(0.6, 0.8, False, False)
                native._product(a, b)
                marker = RuntimeError("cancel pure native reuse")
                charge = native.work.charge
                def interrupt(kind="checkpoint", amount=1):
                    if kind == "cache_promote":
                        if narrow:
                            native.work.external_check = lambda: setattr(native.work, "max_operand_bits", 128)
                        else:
                            native.work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return charge(kind, amount)
                with patch.object(native.work, "charge", side_effect=interrupt):
                    with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                        native._product(a, b)
                if not narrow:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(native.work.callback_error, marker)

    def test_rounding_cells_cover_power_boundaries_signed_zero_and_subnormals(self):
        work = ReachExecutionWork()
        for value in (1.0, -1.0, .75, -.75, 0.0, math.ldexp(1.0, -149)):
            with self.subTest(value=value):
                radius = F(0) if value == 0 else F(1, 2**160) if abs(value) < 1e-30 else F(1, 2**40)
                self.assertTrue(certified_float32_cell(value, radius, work=work))
                self.assertEqual(bits32((float(F(value)-radius),)), bits32((value,)))
                self.assertEqual(bits32((float(F(value)+radius),)), bits32((value,)))
        for midpoint in (1.0 + 2**-24, 1.0 - 2**-25,
                         -1.0 + 2**-25, -1.0 - 2**-24, 2**-150):
            with self.subTest(midpoint=midpoint):
                self.assertFalse(certified_float32_cell(midpoint, F(0), work=work))
        for value in (float("nan"), float("inf"), 2.0**128):
            self.assertFalse(certified_float32_cell(value, F(1, 2**40), work=work))
        self.assertFalse(certified_float32_cell(0.0, F(1, 2**160), work=work))
        self.assertFalse(certified_float32_cell(-0.0, F(0), work=work))

    def test_native_recurrence_enclosure_contains_original_private_projection(self):
        source, baseline = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        context, reference_context = object(), object()
        angles = [F(index + 1, 113) for index in range(48)]
        angles += list(reversed(angles[9:16]))
        for angle in angles:
            actual = native.recording_axis_rotation((0, 0, 1), angle,
                context=context, path="hinge:joint", max_steps=10000)
            expected = baseline.recording_axis_rotation((0, 0, 1), angle,
                context=reference_context, path="hinge:joint", max_steps=10000)
            q = baseline._unit_projection(expected)
            self.assertLessEqual(abs(F(actual.w) - F(q[0])), F(1, 2**41))
            self.assertLessEqual(abs(F(actual.z) - F(q[3])), F(1, 2**41))
        self.assertLessEqual(len(source.work._cache), 256)
        self.assertEqual(source.work.operations, sum(source.work.counts.values()))

    def test_native_cursor_reseeds_before_its_smaller_error_bound_expires(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        args = dict(context=object(), path="hinge:joint", max_steps=10000)
        angles = [F(index + 1, 113) for index in range(2 * MAX_FLOAT_ROTATION_STEPS + 3)]
        with patch.object(source, "axis_rotation", wraps=source.axis_rotation) as axis:
            for angle in angles:
                actual = native.recording_axis_rotation((0, 0, 1), angle, **args)
                cursor = next(value for key, value in source.work._cache.items()
                              if "certified_binary64_axis" in key)
                self.assertLessEqual(cursor[2], MAX_FLOAT_ROTATION_STEPS)
        seed_angles = [call.args[1] for call in axis.call_args_list if call.args[1] != F(1, 113)]
        self.assertEqual(seed_angles, [angles[MAX_FLOAT_ROTATION_STEPS], angles[2 * MAX_FLOAT_ROTATION_STEPS]])
        expected = source._unit_projection(source.axis_rotation((0, 0, 1), angles[-1]))
        self.assertLessEqual(abs(F(actual.w) - F(expected[0])), F(1, 2**41))
        self.assertLessEqual(abs(F(actual.z) - F(expected[3])), F(1, 2**41))
        self.assertEqual(MAX_FLOAT_ROTATION_STEPS, 127)
        self.assertEqual(MAX_RECORDING_ROTATION_STEPS, 10000)

    def test_native_prescribed_spin_encloses_original_across_reseed_and_clock_reversal(self):
        source, baseline = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        omega = (0, 0, F(1, 4))
        initial = source.axis_rotation((0, 0, 1), F(1, 7))
        reference_initial = baseline.axis_rotation((0, 0, 1), F(1, 7))
        plan, reference_plan = source.spin_plan(omega, F(3)), baseline.spin_plan(omega, F(3))
        context, reference_context = object(), object()
        times = [F(index + 1, 113) for index in range(MAX_FLOAT_ROTATION_STEPS + 3)]
        times += [F(3, 5), F(2, 5), F(2, 5)]
        for time in times:
            actual = native.recording_advance_orientation(initial, omega, time,
                context=context, path="prescribed:root", max_steps=10000, phase_plan=plan)
            reference = baseline.recording_advance_orientation(reference_initial, omega, time,
                context=reference_context, path="prescribed:root", max_steps=10000, phase_plan=reference_plan)
            projected = baseline._unit_projection(reference)
            self.assertLessEqual(abs(F(actual.w) - F(projected[0])), F(1, 2**41))
            self.assertLessEqual(abs(F(actual.z) - F(projected[3])), F(1, 2**41))
        self.assertLessEqual(len(source.work._cache), 256)

    def test_native_prescribed_spin_keeps_phase_checks_and_cancelled_cursor(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        omega = (0, 0, F(1, 4))
        plan = source.spin_plan(omega, F(3))
        args = dict(context=object(), path="prescribed:root", max_steps=10000, phase_plan=plan)
        for time in (F(1, 8), F(1, 4)):
            native.recording_advance_orientation(UNIT, omega, time, **args)
        key = next(key for key in source.work._cache if "certified_binary64_spin" in key)
        before = source.work._cache[key]
        with self.assertRaises(ReachAdmissionError):
            native.recording_advance_orientation(UNIT, omega, F(4), **args)
        self.assertEqual(source.work._cache[key], before)
        marker = RuntimeError("cancel native prescribed spin")
        charge = source.work.charge
        def cancelled(kind="checkpoint", amount=1):
            if kind == "recording_float_mul":
                source.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(source.work, "charge", side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                native.recording_advance_orientation(UNIT, omega, F(3, 8), **args)
        self.assertIs(caught.exception, marker)
        self.assertIs(source.work.callback_error, marker)
        self.assertEqual(source.work._cache[key], before)

    def test_cursor_cancellation_keeps_the_last_completed_coordinate(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        args = dict(context=object(), path="hinge:joint", max_steps=10000)
        for angle in (F(1, 8), F(1, 4)):
            native.recording_axis_rotation((0, 0, 1), angle, **args)
        key = next(key for key in source.work._cache if "certified_binary64_axis" in key)
        before = source.work._cache[key]
        marker = RuntimeError("cancel native multiplication")
        charge = source.work.charge
        def cancelled(kind="checkpoint", amount=1):
            if kind == "recording_float_mul":
                source.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(source.work, "charge", side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                native.recording_axis_rotation((0, 0, 1), F(3, 8), **args)
        self.assertIs(caught.exception, marker)
        self.assertIs(source.work.callback_error, marker)
        self.assertEqual(source.work._cache[key], before)

    def test_narrowed_domain_cannot_return_a_native_result(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        args = dict(context=object(), path="hinge:joint", max_steps=10000)
        native.recording_axis_rotation((0, 0, 1), F(1, 8), **args)
        source.work.max_operand_bits = 128
        with self.assertRaises(_UnsupportedPlanar):
            native.recording_axis_rotation((0, 0, 1), F(1, 4), **args)

    def test_last_projection_or_sign_callback_cannot_return_a_wide_candidate(self):
        for trigger in ("frozen_quaternion_projection", "recording_float_sign"):
            with self.subTest(trigger=trigger):
                source = ReachPoseOps(ReachExecutionWork())
                native = Binary64RecordingOps(source)
                charge = source.work.charge
                def narrow(kind="checkpoint", amount=1):
                    if kind == trigger:
                        source.work.external_check = lambda: setattr(source.work, "max_operand_bits", 128)
                    return charge(kind, amount)
                with patch.object(source.work, "charge", side_effect=narrow):
                    with self.assertRaises(_UnsupportedPlanar):
                        if trigger == "frozen_quaternion_projection":
                            native._project_rotation(RotationValue(UNIT, frozen_projection=(1.0, 0.0, 0.0, 0.0)))
                        else:
                            native._product(_FloatRotation(0.0, 1.0, True, False),
                                            _FloatRotation(0.0, 1.0, True, False))

    def test_last_rounding_cell_callback_rechecks_operand_domain(self):
        for value, trigger, occurrence in ((1.0, "recording_float_sub", 2),
                                           (0.0, "recording_float32_candidate", 1)):
            with self.subTest(value=value, trigger=trigger):
                work = ReachExecutionWork()
                charge = work.charge
                occurrences = 0
                def narrow(kind="checkpoint", amount=1):
                    nonlocal occurrences
                    if kind == trigger:
                        occurrences += 1
                        if occurrences == occurrence:
                            work.external_check = lambda: setattr(work, "max_operand_bits", 128)
                    return charge(kind, amount)
                with patch.object(work, "charge", side_effect=narrow):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        certified_float32_cell(value, 0.0, work=work)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_strict_threshold_proofs_stay_inside_exact_neighbor_midpoints(self):
        def number(bits):
            return struct.unpack("<f", struct.pack("<I", bits))[0]
        work = ReachExecutionWork()
        for magnitude in (1, 0x00800000, 0x3F400000, 0x3F800000, 0x71800000):
            for sign in (0, 1 << 31):
                bits = sign | magnitude
                stored = number(bits)
                low = number(bits + 1 if sign else bits - 1)
                high = number(bits - 1 if sign else bits + 1)
                midpoint = (stored + low) / 2
                upper_midpoint = (stored + high) / 2
                values = (stored, midpoint, math.nextafter(midpoint, -math.inf),
                          math.nextafter(midpoint, math.inf), upper_midpoint,
                          math.nextafter(upper_midpoint, -math.inf),
                          math.nextafter(upper_midpoint, math.inf))
                width = min(abs(stored - low), abs(high - stored)) / 2
                radii = (0.0, math.ldexp(1.0, -1074), math.nextafter(width, 0.0),
                         width, math.nextafter(width, math.inf))
                for value in values:
                    for radius in radii:
                        with self.subTest(bits=bits, value=value, radius=radius):
                            if not certified_float32_cell(value, radius, work=work):
                                continue
                            packed = struct.pack("<f", value)
                            encoded = struct.unpack("<I", packed)[0]
                            actual = struct.unpack("<f", packed)[0]
                            if actual == 0.0:
                                # The explicit signed-zero gate owns the
                                # half-cell's sign boundary at exact zero.
                                self.assertLess(radius, abs(value))
                                continue
                            negative = bool(encoded >> 31)
                            below = number(encoded + 1 if negative else encoded - 1)
                            above = number(encoded - 1 if negative else encoded + 1)
                            self.assertGreater(F(value) - F(radius), (F(actual) + F(below)) / 2)
                            self.assertLess(F(value) + F(radius), (F(actual) + F(above)) / 2)

    def test_constant_projection_cache_callbacks_cannot_return_a_wide_candidate(self):
        for warmed, trigger in ((False, "cache_insert"), (True, "cache_promote")):
            with self.subTest(warmed=warmed):
                source = ReachPoseOps(ReachExecutionWork())
                native = Binary64RecordingOps(source)
                pose = source.make((1, 0, 0))
                source._unit_projection(pose.rotation)
                source._vector_projection(pose.exact_position)
                if warmed:
                    native._pose(pose)
                charge = source.work.charge
                def narrow(kind="checkpoint", amount=1):
                    if kind == trigger:
                        source.work.external_check = lambda: setattr(source.work, "max_operand_bits", 128)
                    return charge(kind, amount)
                with patch.object(source.work, "charge", side_effect=narrow):
                    with self.assertRaises(_UnsupportedPlanar):
                        native._pose(pose)
                self.assertEqual(source.work._cache_operand_bits, 128)

    def test_same_graph_rotation_identity_shares_the_maximum_member_enclosure(self):
        work = ReachExecutionWork()
        rotation = _FloatRotation(.6, .8, False, False)
        other = _FloatRotation(.6, .8, False, False)
        small = RecordingFloatExcess(F(1, 2**48), F(1, 2**48), F(1, 2**44))
        large = RecordingFloatExcess(F(1, 2**47), F(1, 2**47), F(1, 2**43))
        candidates = []
        for path, value, excess in (("first", rotation, small), ("second", rotation, large),
                                    ("unshared", other, small)):
            private = _FloatPose((1.0, 2.0, 0.0), value, (False, False, True), 1)
            pose = NS(position=private.position, orientation=private.orientation)
            candidates.append((path, private, pose, excess))
        groups = _rotation_cell_groups(candidates, work)
        self.assertEqual(groups, {(id(rotation), False, False)})
        self.assertNotIn((id(other), False, False), groups)
        before = work.counts["recording_float32_candidate"]
        for _, private, pose, excess in candidates[:2]:
            self.assertTrue(_certify_pose(pose, excess, work, zeros=private.zeros,
                rotation_zeros=(False, False), rotation_certified=True))
        self.assertEqual(work.counts["recording_float32_candidate"] - before, 4)
        self.assertEqual(work.counts["recording_rotation_cell_reuse"], 2)

    def test_failed_group_enclosure_keeps_each_members_smaller_rounding_proof(self):
        work = ReachExecutionWork()
        rotation = _FloatRotation(.6, .8, False, False)
        private = _FloatPose((0.0, 0.0, 0.0), rotation, (True, True, True), 1)
        pose = NS(position=private.position, orientation=private.orientation)
        small = RecordingFloatExcess(F(0), F(1, 2**48), F(1, 2**44))
        large = RecordingFloatExcess(F(0), F(1, 1000000), F(1, 62500))
        candidates = [("small", private, pose, small), ("large", private, pose, large)]
        self.assertEqual(_rotation_cell_groups(candidates, work), set())
        self.assertTrue(_certify_pose(pose, small, work, zeros=private.zeros, rotation_zeros=(False, False)))
        self.assertFalse(_certify_pose(pose, large, work, zeros=private.zeros, rotation_zeros=(False, False)))

    def test_certified_p09_samples_preserve_stored_pose_bits(self):
        candidate, baseline = simulator("P09"), simulator("P09")
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.tool.frame")
        contexts = (object(), object())
        for sim in (candidate, baseline):
            sim.advance(F(0), "after")
        bounds = candidate.phase_bounds(F(0), F(2))["frames"]
        baseline.phase_bounds(F(0), F(2))
        moving = candidate.recording_moving_frames(candidate.state, paths)
        for sim, context in zip((candidate, baseline), contexts):
            sim.recording_frames(F(0), sim.state, paths, moving_frames=moving, recording_context=context)
        for index in range(1, 17):
            time = F(index, 137)
            result = sample_certified_frames(candidate, time, candidate.state, paths,
                context=contexts[0], moving_frames=moving, phase_bounds=bounds)
            expected = baseline.recording_frames(time, baseline.state, paths,
                moving_frames=moving, recording_context=contexts[1])
            for path in paths:
                self.assertEqual(bits32((*result.frames[path].position, *result.frames[path].orientation)),
                                 bits32((*expected[path].position, *expected[path].orientation)))
                self.assertIsInstance(result.excess_by_frame[path], RecordingFloatExcess)
                self.assertGreater(result.excess_by_frame[path].position_m, 0)
        self.assertLessEqual(len(candidate.work._cache), 256)

    def test_certified_prescribed_spin_and_follow_samples_preserve_p16_pose_bits(self):
        candidate, baseline = simulator("P16"), simulator("P16")
        paths = ("rig.frame", "rig.column.frame", "rig.arm.frame", "rig.arm.upper.frame",
                 "rig.arm.forearm.frame", "rig.tool.frame", "payload.frame")
        contexts = (object(), object())
        for sim in (candidate, baseline):
            sim.advance(F(0), "after")
        bounds = candidate.phase_bounds(F(0), F(2))["frames"]
        baseline.phase_bounds(F(0), F(2))
        moving = candidate.recording_moving_frames(candidate.state, paths)
        for sim, context in zip((candidate, baseline), contexts):
            sim.recording_frames(F(0), sim.state, paths, moving_frames=moving, recording_context=context)
        for index in range(1, 17):
            time = F(index, 137)
            result = sample_certified_frames(candidate, time, candidate.state, paths,
                context=contexts[0], moving_frames=moving, phase_bounds=bounds)
            expected = baseline.recording_frames(time, baseline.state, paths,
                moving_frames=moving, recording_context=contexts[1])
            for path in paths:
                self.assertEqual(bits32((*result.frames[path].position, *result.frames[path].orientation)),
                                 bits32((*expected[path].position, *expected[path].orientation)))
        self.assertTrue(any("certified_binary64_spin" in key for key in candidate.work._cache))
        self.assertLessEqual(len(candidate.work._cache), 256)

    def test_ambiguous_refinement_requests_whole_phase_replay(self):
        sim = simulator("P09")
        sim.advance(F(0), "after")
        paths = ("rig.arm.forearm.frame",)
        bounds = sim.phase_bounds(F(0), F(2))["frames"]
        before = copy.deepcopy(sim.state)
        with patch("ontokin.reach_recording_fast.certified_float32_cell", return_value=False):
            with self.assertRaises(RecordingRoundingAmbiguity):
                sample_certified_frames(sim, F(1, 7), sim.state, paths, context=object(),
                    moving_frames=frozenset(paths), phase_bounds=bounds)
        self.assertEqual(sim.state, before)

    def test_error_fields_are_separate_from_source_bounds(self):
        work = ReachExecutionWork()
        bound = PhaseBound(trig_count=2, product_count=8, max_position_l1_m=F(7),
                           path_offset_l1_m=F(3), position_error_m=F(1, 2**48),
                           rotation_error_rad=F(1, 2**49))
        result = recording_float_excess(bound, work=work)
        self.assertGreater(result.position_m, 2 * bound.position_error_m)
        self.assertGreater(result.quaternion_component, 2 * bound.rotation_error_rad)
        self.assertEqual(result.rotation_rad, 16 * result.quaternion_component)
        self.assertEqual(recording_float_excess(bound, work=work), result)
        self.assertEqual(bound.position_error_m, F(1, 2**48))
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.max_cache_entries, 256)

    def test_cached_enclosure_carries_its_completed_outward_component_radii(self):
        work = ReachExecutionWork()
        bound = PhaseBound(trig_count=2, product_count=8, max_position_l1_m=F(7),
                           path_offset_l1_m=F(3), position_error_m=F(1, 2**48),
                           rotation_error_rad=F(1, 2**49))
        result = recording_float_excess(bound, work=work)
        for radius, exact_radius in zip(result._cell_radii,
                                       (result.position_m, result.quaternion_component)):
            self.assertGreaterEqual(F(radius), exact_radius)
            self.assertLess(F(math.nextafter(radius, -math.inf)), exact_radius)
        before = work.counts["recording_cell_radius_domain"]
        self.assertIs(recording_float_excess(bound, work=work), result)
        pose = NS(position=(1.0, 2.0, 0.0), orientation=(.6, 0.0, 0.0, .8))
        self.assertTrue(_certify_pose(pose, result, work, zeros=(False, False, True)))
        self.assertEqual(work.counts["recording_cell_radius_domain"], before)
        self.assertFalse(any("cell_radius" in key for key in work._cache))

    def test_cancelled_second_radius_conversion_cannot_publish_partial_enclosure(self):
        work = ReachExecutionWork()
        bound = PhaseBound(trig_count=1, product_count=2)
        marker = RuntimeError("cancel second outward radius")
        charge = work.charge
        radii = 0
        def cancelled(kind="checkpoint", amount=1):
            nonlocal radii
            if kind == "recording_cell_radius_domain":
                radii += 1
                if radii == 2:
                    work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(work, "charge", side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                recording_float_excess(bound, work=work)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertFalse(any("excess" in key for key in work._cache))


    def test_source_identity_leaf_keeps_the_exact_candidate_without_projection(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        parent = native.make_recording((F(1, 3), F(-2, 7), F(0)),
            native._project_rotation(source.axis_rotation((0, 0, 1), F(1, 7))))
        for scalar in (F(1), F(3, 2)):
            with self.subTest(scalar=scalar):
                leaf = source.make(orientation=RotationValue((scalar, F(0), F(0), F(0)), F(1, 2**80)))
                projected = native._pose(leaf)
                expected = native.compose_recording_fast(parent, projected)
                with patch.object(source, "_unit_projection", side_effect=AssertionError("identity projected")):
                    with patch.object(native, "_product", side_effect=AssertionError("identity multiplied")):
                        actual = native.compose_recording_fast(parent, leaf)
                self.assertEqual(struct.pack("<7d", *actual.position, *actual.orientation),
                                 struct.pack("<7d", *expected.position, *expected.orientation))
                self.assertIs(actual.rotation, parent.rotation)
                self.assertEqual(actual.zeros, expected.zeros)
                self.assertEqual(actual.depth, parent.depth + 1)


    def test_source_identity_leaf_retains_frozen_projection_and_depth_domains(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        parent = native.make_recording()
        frozen = source.make(orientation=RotationValue(UNIT,
            frozen_projection=(1.0, 0.0, 0.0, 0.0)))
        with patch.object(source, "_unit_projection", wraps=source._unit_projection) as project:
            actual = native.compose_recording_fast(parent, frozen)
        project.assert_called_once_with(frozen.rotation)
        self.assertEqual(actual.orientation, frozen.rotation.frozen_projection)
        leaf = source.make()
        exhausted = _FloatPose(parent.position, parent.rotation, parent.zeros, 64)
        with self.assertRaises(_UnsupportedPlanar):
            native.compose_recording_fast(exhausted, leaf)
        with self.assertRaises(_UnsupportedPlanar):
            native.compose_recording_fast(parent, ReachPoseOps(ReachExecutionWork()).make())


    def test_source_identity_leaf_cancellation_and_cap_change_remain_immediate(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                source = ReachPoseOps(ReachExecutionWork())
                native = Binary64RecordingOps(source)
                parent, leaf = native.make_recording(), source.make()
                before = list(source.work._cache.items())
                marker = RuntimeError("cancel identity leaf")
                def callback():
                    if cancel:
                        raise marker
                    source.work.max_operand_bits = 128
                source.work.external_check = callback
                with self.assertRaises(RuntimeError if cancel else _UnsupportedPlanar) as caught:
                    native.compose_recording_fast(parent, leaf)
                if cancel:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(source.work.callback_error, marker)
                self.assertEqual(list(source.work._cache.items()), before)


    def test_source_identity_leaf_keeps_cold_projection_operand_width_rejection(self):
        for scalar in (F(1 << 20000), F(1, 1 << 20000)):
            with self.subTest(scalar_bits=max(scalar.numerator.bit_length(), scalar.denominator.bit_length())):
                source = ReachPoseOps(ReachExecutionWork())
                native = Binary64RecordingOps(source)
                parent = native.make_recording()
                leaf = source.make(orientation=RotationValue((scalar, F(0), F(0), F(0))))
                with self.assertRaises(ReachAdmissionError) as direct:
                    native._pose(leaf)
                with self.assertRaises(ReachAdmissionError) as composed:
                    native.compose_recording_fast(parent, leaf)
                self.assertEqual(composed.exception.details, direct.exception.details)
                self.assertEqual(composed.exception.details["budget"], "numeric_operand_bits")


    def test_frozen_projection_must_prove_its_actual_plane_and_zero_support(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        projected = native._project_rotation(RotationValue((F(.6), F(0), F(0), F(.8)),
            frozen_projection=(.6, 0.0, 0.0, .8)))
        self.assertFalse(projected.zero_z)
        product = native._product(projected, _FloatRotation(0.0, 1.0, True, False))
        self.assertEqual((product.w, product.z), (.8, -.6))
        self.assertFalse(product.zero_w)
        consistent = native._project_rotation(RotationValue(UNIT,
            frozen_projection=(1.0, 0.0, 0.0, 0.0)))
        self.assertTrue(consistent.zero_z)
        invalid = (
            RotationValue(UNIT, frozen_projection=(.6, 0.0, 0.0, .8)),
            RotationValue(UNIT, frozen_projection=(.6, .1, 0.0, .8)),
            RotationValue(UNIT, frozen_projection=(1.0, -0.0, 0.0, 0.0)),
            RotationValue(UNIT, frozen_projection=(1.0, 0.0, 0.0, -0.0)),
            RotationValue((F(2), F(0), F(0), F(0)), frozen_projection=(2.0, 0.0, 0.0, 0.0)),
            RotationValue((F(-1), F(0), F(0), F(0)), frozen_projection=(-1.0, 0.0, 0.0, 0.0)),
            RotationValue((F(0), F(0), F(0), F(-1))),
            RotationValue(UNIT, frozen_projection=(1, 0.0, 0.0, 0.0)),
            RotationValue(UNIT, frozen_projection=(float("nan"), 0.0, 0.0, 0.0)),
            RotationValue(UNIT, frozen_projection=(1.0, 0.0, 0.0)),
        )
        for rotation in invalid:
            with self.subTest(rotation=rotation):
                with self.assertRaises(_UnsupportedPlanar):
                    native._project_rotation(rotation)


    def test_frozen_materialized_anchor_keeps_its_actual_binary64_projection(self):
        source = ReachPoseOps(ReachExecutionWork())
        native = Binary64RecordingOps(source)
        original = source.make(orientation=source.axis_rotation((0, 0, 1), F(1, 7)))
        anchor = source.materialize(original)
        candidate = native._project_rotation(anchor.rotation)
        self.assertEqual(struct.pack("<4d", candidate.w, 0.0, 0.0, candidate.z),
                         struct.pack("<4d", *anchor.orientation))


    def test_frozen_projection_last_admission_callback_keeps_domain_and_cancellation(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                source = ReachPoseOps(ReachExecutionWork())
                native = Binary64RecordingOps(source)
                rotation = RotationValue(UNIT, frozen_projection=(1.0, 0.0, 0.0, 0.0))
                before = list(source.work._cache.items())
                charge = source.work.charge
                comparisons = 0
                marker = RuntimeError("cancel frozen admission")
                def guarded(kind="checkpoint", amount=1):
                    nonlocal comparisons
                    if kind == "exact_compare":
                        comparisons += 1
                        if comparisons == 5:
                            def callback():
                                if cancel:
                                    raise marker
                                source.work.max_operand_bits = 128
                            source.work.external_check = callback
                    return charge(kind, amount)
                with patch.object(source.work, "charge", side_effect=guarded):
                    with self.assertRaises(RuntimeError if cancel else _UnsupportedPlanar) as caught:
                        native._project_rotation(rotation)
                if cancel:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(source.work.callback_error, marker)
                self.assertEqual(list(source.work._cache.items()), before)


if __name__ == "__main__":
    unittest.main()
