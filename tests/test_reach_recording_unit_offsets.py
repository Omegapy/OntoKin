"""Sparse unit offsets omit exact native identities, preserving all actual bits."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
import math
import struct
import unittest
from unittest.mock import patch

from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recording_captured_chain import begin, chain
from test_reach_recording_captured_graph import bits


def native(*, sharing=False, cap=32768):
    return fast.Binary64RecordingOps(ReachPoseOps(ReachExecutionWork(max_operand_bits=cap)),
                                     share_arithmetic=sharing)


def offset_bits(value):
    return struct.pack("!ddd", *value[0]), value[1]


def ordinary_offset(ops, rotation, position, zeros):
    """The preceding complete ordered kernel, including its existing LRU."""
    key = None
    if ops.share_arithmetic:
        key = (fast.METHOD, "native_offset", ops.work.max_operand_bits,
               ops._rotation_bits(rotation), struct.pack("<ddd???", *position, *zeros))
        old = ops.work.lookup(key)
        ops._require_domain()
        if old is not None:
            return old
    op = ops._native
    w, z = rotation.w, rotation.z
    x, y, zz = position
    c = op(op(w, w, "mul"), op(z, z, "mul"), "sub")
    s = op(op(w, z, "mul"), 2.0, "mul")
    cross_zero = rotation.zero_w or rotation.zero_z
    if zeros[1]:
        offset = (op(c, x, "mul"), op(s, x, "mul"), zz)
        offset_zeros = (zeros[0], zeros[0] or cross_zero, zeros[2])
    elif zeros[0]:
        ops.work.charge("recording_float_sign")
        ops._require_domain()
        offset = (op(-s, y, "mul"), op(c, y, "mul"), zz)
        offset_zeros = (zeros[1] or cross_zero, zeros[1], zeros[2])
    else:
        offset = (op(op(c, x, "mul"), op(s, y, "mul"), "sub"),
                  op(op(s, x, "mul"), op(c, y, "mul"), "add"), zz)
        offset_zeros = (False, False, zeros[2])
    result = offset, offset_zeros
    if key is not None:
        ops.work.remember(key, result)
        ops._require_domain()
    return result


class ReachRecordingUnitOffsetTests(unittest.TestCase):
    def test_unit_axes_preserve_signed_zero_subnormal_bits_and_every_mask(self):
        tiny = float.fromhex("0x0.0000000000001p-1022")
        rotations = (
            fast._FloatRotation(0.75, -0.5, False, False),
            fast._FloatRotation(1.0, 0.0, False, True),
            fast._FloatRotation(1.0, -0.0, False, False),
            fast._FloatRotation(0.0, 1.0, True, False),
            fast._FloatRotation(-0.0, 1.0, False, False),
            fast._FloatRotation(1.0, tiny, False, False),
            fast._FloatRotation(1.0, -tiny, False, False),
            fast._FloatRotation(tiny, -tiny, False, False),
        )
        for rotation in rotations:
            for zero in (0.0, -0.0):
                for z in (0.0, -0.0, tiny, -tiny):
                    for z_mask in (False, True):
                        for position, masks in (((1.0, zero, z), (False, True, z_mask)),
                                                ((zero, 1.0, z), (True, False, z_mask))):
                            with self.subTest(rotation=rotation, position=position, masks=masks):
                                current, original = native(), native()
                                actual = current._rotated_offset(rotation, position, masks)
                                expected = ordinary_offset(original, rotation, position, masks)
                                self.assertEqual(offset_bits(actual), offset_bits(expected))
                                self.assertEqual(original.work.operations - current.work.operations, 2)
                                self.assertEqual(original.work.counts["recording_float_mul"]
                                                 - current.work.counts["recording_float_mul"], 2)
                                self.assertEqual(original.work.counts.get("recording_float_sign", 0),
                                                 current.work.counts.get("recording_float_sign", 0))

    def test_nonunit_and_nonsparse_offsets_keep_the_original_arithmetic(self):
        rotation = fast._FloatRotation(0.75, -0.5, False, False)
        tiny = float.fromhex("0x0.0000000000001p-1022")
        cases = [((x, 0.0, 0.0), (False, True, True))
                 for x in (-1.0, 0.0, -0.0, tiny, -tiny, math.nextafter(1.0, 0.0), math.nextafter(1.0, 2.0))]
        cases += [((0.0, -1.0, 0.0), (True, False, True)),
                  ((1.0, 0.5, 0.0), (False, False, True)),
                  ((0.5, 1.0, 0.0), (False, False, True))]
        for position, masks in cases:
            with self.subTest(position=position):
                current, original = native(), native()
                self.assertEqual(offset_bits(current._rotated_offset(rotation, position, masks)),
                                 offset_bits(ordinary_offset(original, rotation, position, masks)))
                self.assertEqual(current.work.counts, original.work.counts)

    def test_foreign_unit_operands_and_nonfloat_coefficients_keep_original_calls(self):
        class ForeignFloat(float):
            pass
        for operand in (1, True, F(1), ForeignFloat(1.0)):
            for position, masks in (((operand, 0.0, 0.0), (False, True, True)),
                                    ((0.0, operand, 0.0), (True, False, True))):
                with self.subTest(operand_type=type(operand), masks=masks):
                    rotation = fast._FloatRotation(0.75, -0.5, False, False)
                    current, original = native(), native()
                    self.assertEqual(offset_bits(current._rotated_offset(rotation, position, masks)),
                                     offset_bits(ordinary_offset(original, rotation, position, masks)))
                    self.assertEqual(current.work.counts, original.work.counts)
        # A private direct-helper misuse can produce an integer c. Preserve
        # its old float multiplication conversion rather than returning an int.
        current, original = native(), native()
        rotation = fast._FloatRotation(1, 0, False, True)
        actual = current._rotated_offset(rotation, (1.0, 0.0, 0.0), (False, True, True))
        expected = ordinary_offset(original, rotation, (1.0, 0.0, 0.0), (False, True, True))
        self.assertEqual(tuple(type(v) for v in actual[0]), tuple(type(v) for v in expected[0]))
        self.assertEqual(offset_bits(actual), offset_bits(expected))
        self.assertEqual(current.work.counts, original.work.counts)

    def test_nonfinite_inputs_retain_original_rejection_and_attempted_work(self):
        for rotation, position in (
                (fast._FloatRotation(math.inf, 0.5, False, False), (1.0, 0.0, 0.0)),
                (fast._FloatRotation(0.75, math.nan, False, False), (1.0, 0.0, 0.0)),
                (fast._FloatRotation(0.75, 0.5, False, False), (math.inf, 0.0, 0.0)),
                (fast._FloatRotation(0.75, 0.5, False, False), (math.nan, 0.0, 0.0))):
            histories = []
            for method in (ordinary_offset, fast.Binary64RecordingOps._rotated_offset):
                ops = native()
                with self.assertRaises(fast._UnsupportedPlanar):
                    method(ops, rotation, position, (False, True, True))
                histories.append(ops.work.counts)
            self.assertEqual(*histories)

    def test_narrowed_domain_rejects_before_any_unit_identity_can_return(self):
        rotation = fast._FloatRotation(0.75, -0.5, False, False)
        histories = []
        for method in (ordinary_offset, fast.Binary64RecordingOps._rotated_offset):
            ops = native(cap=128)
            with self.assertRaises(fast._UnsupportedPlanar):
                method(ops, rotation, (1.0, 0.0, 0.0), (False, True, True))
            histories.append(ops.work.counts)
            self.assertFalse(ops.work._cache)
        self.assertEqual(*histories)

    def test_coefficient_and_y_sign_callbacks_keep_caps_and_exception_identity(self):
        rotation = fast._FloatRotation(0.75, -0.5, False, False)
        for position, masks, stop in (((1.0, 0.0, 0.0), (False, True, True), 5),
                                     ((0.0, 1.0, 0.0), (True, False, True), 6)):
            for narrow in (False, True):
                with self.subTest(masks=masks, narrow=narrow):
                    ops, calls = native(), []
                    marker = RuntimeError("cancel original coefficient/sign callback")
                    def check():
                        calls.append(True)
                        if len(calls) == stop:
                            if narrow:
                                ops.work.max_operand_bits = 128
                            else:
                                raise marker
                    ops.work.external_check = check
                    with self.assertRaises(fast._UnsupportedPlanar if narrow else RuntimeError) as caught:
                        ops._rotated_offset(rotation, position, masks)
                    self.assertEqual(len(calls), stop)
                    self.assertFalse(ops.work._cache)
                    if not narrow:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(ops.work.callback_error, marker)

    def test_existing_cache_reuse_keeps_complete_bits_and_live_cap_callbacks(self):
        rotation = fast._FloatRotation(1.0, -0.0, False, False)
        position, masks = (1.0, -0.0, 0.0), (False, True, True)
        for narrow in (False, True):
            ops = native(sharing=True)
            original = native(sharing=True)
            self.assertEqual(offset_bits(ops._rotated_offset(rotation, position, masks)),
                             offset_bits(ordinary_offset(original, rotation, position, masks)))
            key = next(k for k in ops.work._cache if k[1] == "native_offset")
            before, charged = tuple(ops.work._cache.items()), ops.work.charge
            marker = RuntimeError("cancel completed unit-offset cache promotion")
            def charge(kind="checkpoint", amount=1):
                if kind == "cache_promote":
                    def check():
                        if narrow:
                            ops.work.max_operand_bits = 128
                        else:
                            raise marker
                    ops.work.external_check = check
                return charged(kind, amount)
            with patch.object(ops.work, "charge", side_effect=charge):
                with self.assertRaises(fast._UnsupportedPlanar if narrow else RuntimeError) as caught:
                    ops._rotated_offset(rotation, position, masks)
            if narrow:
                self.assertNotIn(key, ops.work._cache)
            else:
                self.assertIs(caught.exception, marker)
                self.assertEqual(tuple(ops.work._cache.items()), before)

    def test_actual_p16_phase_keeps_all_frame_bits_enclosures_and_source_state(self):
        outcomes = []
        times = tuple(F(index, 8) for index in range(1, 16))
        native_offset = fast.Binary64RecordingOps._rotated_offset
        for folded in (False, True):
            fixture = chain("P16", F(0), F(2))
            sim = fixture[0]
            source = deepcopy(sim.state)
            started = sim.work.operations
            counts = dict(sim.work.counts)
            multiplies = sim.work.counts.get("recording_float_mul", 0)
            mode = nullcontext() if folded else patch.object(fast.Binary64RecordingOps,
                                                             "_rotated_offset", ordinary_offset)
            # The later forward-translation proof pins _rotated_offset, so the
            # old kernel alone would also lose unrelated domain-entry savings.
            # Hold that optional path off in both arms; keep the native offset
            # method itself untouched in the folded arm.
            with patch.object(fast.Binary64RecordingOps, "recording_forward_translation",
                              return_value=None) as forward, mode:
                phase = begin(fixture, times)
                self.assertIsNotNone(phase)
                self.assertIs(phase.phase.ops._rotated_offset.__func__,
                              native_offset if folded else ordinary_offset)
                values = [bits(phase.sample(time)) for time in times]
                phase.finish()
            self.assertGreater(forward.call_count, 0)
            self.assertEqual(sim.state, source)
            self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
            self.assertLessEqual(len(sim.work._cache), 256)
            other_counts = {kind: count - counts.get(kind, 0)
                for kind, count in sim.work.counts.items()
                if kind != "recording_float_mul" and count != counts.get(kind, 0)}
            outcomes.append((values, sim.work.operations - started,
                             sim.work.counts.get("recording_float_mul", 0) - multiplies,
                             other_counts, forward.call_count))
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertGreater(outcomes[0][1] - outcomes[1][1], 0)
        self.assertEqual(outcomes[0][1] - outcomes[1][1], outcomes[0][2] - outcomes[1][2])
        self.assertEqual(outcomes[0][3:], outcomes[1][3:])

    def test_actual_p16_prefix_keeps_complete_delivered_glb_bytes(self):
        outputs = []
        for folded in (False, True):
            built = compile_construction(source_case("P16"), level="constructed")
            mode = nullcontext() if folded else patch.object(fast.Binary64RecordingOps,
                                                             "_rotated_offset", ordinary_offset)
            with mode:
                result = export_glb(built.model, options=ExportOptions(end=F(1, 4), fps=1, helpers=False),
                                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertLessEqual(built.budget.operations, 100000)
            outputs.append(result.data)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
