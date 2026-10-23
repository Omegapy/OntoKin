"""Independent recording offsets retain exact containment and live limits."""
from contextlib import nullcontext
from fractions import Fraction as F
from itertools import product
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import Interval, MAX_CACHE, ReferenceError, _PoseArithmetic
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_fused_recording import arithmetic, dense_values, point
from test_reach_reference_world_recording import reference_case


def quaternion(w=None, z=None):
    values = dense_values()
    return (values[0] if w is None else w, point(0), point(0), values[1] if z is None else z)


def offset(axis=0, scale=None):
    values = [point(0)] * 3
    values[axis] = point(1) if scale is None else scale
    return tuple(values)


def samples(cell):
    return tuple(cell.lo + (cell.hi - cell.lo) * F(i, 4) for i in range(5))


class IndependentRecordingAxisTests(unittest.TestCase):
    def test_point_hamilton_rotations_are_enclosed_for_every_sign_and_offset_axis(self):
        positive = dense_values()[0]
        negative = Interval(-positive.hi, -positive.lo)
        crossing = Interval(F(-1, 8), F(3, 16))
        for w, z, axis, scale in product((positive, negative, crossing),
                                        (positive, negative, crossing), (0, 1),
                                        (point(1), point(F(-3, 2)), Interval(F(-1, 2), F(3, 4)))):
            with self.subTest(w=w, z=z, axis=axis, scale=scale):
                ops, baseline = arithmetic(), arithmetic()
                q, vector = quaternion(w, z), offset(axis, scale)
                actual = ops._recording_rotate(q, vector)
                previous = baseline.rotate(q, vector)
                for cell, old in zip(actual, previous):
                    self.assertGreaterEqual(cell.lo, old.lo)
                    self.assertLessEqual(cell.hi, old.hi)
                # Independently evaluate point Hamilton rotation throughout
                # each input box, including interior zero-crossing points.
                for a, b, length in product(samples(w), samples(z), samples(scale)):
                    expected = (((a * a - b * b) * length, 2 * a * b * length, F(0)) if not axis else
                                (-2 * a * b * length, (a * a - b * b) * length, F(0)))
                    for cell, value in zip(actual, expected):
                        self.assertTrue(cell.contains(value))
                self.assertLess(ops.a.work.operations, baseline.a.work.operations)
                self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))
                self.assertLessEqual(len(ops.a.cache), MAX_CACHE)

    def test_exact_nonunit_scalar_z_rotations_preserve_scale(self):
        for q, vector in product((quaternion(point(F(3, 4)), point(F(-1, 8))),
                                  quaternion(point(2), point(3))),
                                 (offset(), offset(1, point(F(5, 4))))):
            ops, baseline = arithmetic(), arithmetic()
            self.assertEqual(ops._recording_rotate(q, vector), baseline.rotate(q, vector))
            self.assertLess(ops.a.work.operations, baseline.a.work.operations)

    def test_generic_pose_arithmetic_keeps_its_original_interval_cells(self):
        ops = arithmetic()
        parent = ops.make(position=(0, 0, 0), orientation=quaternion(), normalized=True)
        local = ops.make(position=(1, 0, 0))
        with patch.object(ops, "_recording_rotate", side_effect=AssertionError("context-free call")):
            expected = ops.compose(parent, local)
        recording = ops.compose(parent, local, recording=True)
        for cell, old in zip(recording.position, expected.position):
            self.assertGreaterEqual(cell.lo, old.lo)
            self.assertLessEqual(cell.hi, old.hi)
        self.assertEqual(recording.orientation, expected.orientation)
        self.assertEqual(recording.velocity, expected.velocity)
        self.assertEqual(recording.omega, expected.omega)

    def test_unsupported_shapes_and_domains_execute_exactly_the_original_path(self):
        q, vector = quaternion(), offset()
        cases = [(128, 32767, q, vector), (64, 32768, q, vector), (256, 32768, q, vector),
                 (128, 32768, tuple(point(x) for x in (1, 0, 0, 0)), vector),
                 (128, 32768, q, offset(2)), (128, 32768, q, tuple(point(0) for _ in range(3))),
                 (128, 32768, (q[0], point(F(1, 4)), q[2], q[3]), vector),
                 (128, 32768, q, (point(1), point(1), point(0))),
                 (128, 32768, quaternion(point(F(1, 3))), vector),
                 (128, 32768, list(q), vector), (128, 32768, q, list(vector)),
                 (128, 32768, quaternion(Interval(False, False)), vector)]
        for bits, cap, rotation, position in cases:
            with self.subTest(bits=bits, cap=cap, rotation=rotation, position=position):
                ops, baseline = arithmetic(bits=bits, cap=cap), arithmetic(bits=bits, cap=cap)
                self.assertEqual(ops._recording_rotate(rotation, position), baseline.rotate(rotation, position))
                self.assertEqual(ops.a.work.operations, baseline.a.work.operations)

    def test_huge_operands_keep_original_error_identity_and_charge_location(self):
        for large in (F(1 << 33000), F(1, 1 << 33000)):
            outcomes = []
            for optimized in (False, True):
                ops = arithmetic()
                with self.assertRaises(ReferenceError) as caught:
                    (ops._recording_rotate if optimized else ops.rotate)(quaternion(point(large)), offset())
                outcomes.append((caught.exception.code, str(caught.exception), ops.a.work.operations))
            self.assertEqual(outcomes[0], outcomes[1])

    def test_narrowing_at_each_callback_replays_original_without_publishing_a_wide_result(self):
        q, vector = quaternion(), offset()
        count = arithmetic()
        count._recording_rotate(q, vector)
        for fail_at in range(1, count.a.work.operations + 1):
            with self.subTest(fail_at=fail_at):
                ops, calls = arithmetic(), 0
                def narrow():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        ops.a.work.max_operand_bits = 32767
                ops.a.work.external_check = narrow
                with patch.object(ops, "rotate", wraps=ops.rotate) as direct:
                    actual = ops._recording_rotate(q, vector)
                direct.assert_called_once_with(q, vector)
                self.assertEqual(actual, arithmetic(cap=32767).rotate(q, vector))
                self.assertFalse(any(key[3] == "recording_axis_rotation" for key in ops.a.cache))

    def test_callback_cancellation_preserves_the_original_error_and_no_partial_result(self):
        q, vector = quaternion(), offset()
        count = arithmetic()
        count._recording_rotate(q, vector)
        for fail_at in range(1, count.a.work.operations + 1):
            for marker in (RuntimeError("cancel independent axis rotation"),
                           ReferenceError("resource", "caller refusal")):
                with self.subTest(fail_at=fail_at, marker=marker):
                    ops, calls = arithmetic(), 0
                    def cancel():
                        nonlocal calls
                        calls += 1
                        if calls == fail_at:
                            ops.a.work.max_operand_bits = 32767
                            raise marker
                    ops.a.work.external_check = cancel
                    with self.assertRaises(type(marker)) as caught:
                        ops._recording_rotate(q, vector)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(ops.a.work.callback_error, marker)
                    self.assertEqual(ops.a.cache, {})

    def test_complete_cache_key_and_narrow_warm_hit_cannot_bypass_operand_admission(self):
        ops, q, vector = arithmetic(), quaternion(), offset()
        expected = ops._recording_rotate(q, vector)
        first = ops.a.work.operations
        self.assertEqual(ops._recording_rotate(q, vector), expected)
        self.assertLess(ops.a.work.operations - first, first)
        for changed_q, changed_vector in ((quaternion(z=point(F(1, 8))), vector),
                                          (q, offset(1)), (q, offset(scale=point(2)))):
            actual = ops._recording_rotate(changed_q, changed_vector)
            self.assertNotEqual(actual, expected)
        ops.a.work.max_operand_bits = 127
        with self.assertRaises(ReferenceError) as caught:
            ops._recording_rotate(q, vector)
        self.assertEqual(caught.exception.code, "resource")

    def test_original_fallback_failure_is_not_retried_after_a_broadening_callback(self):
        ops, q, vector = arithmetic(), quaternion(), offset()
        failures, calls, broadened = [], 0, []
        rotate = ops.rotate
        def changed():
            nonlocal calls
            calls += 1
            if failures:
                broadened.append(True)
                ops.a.work.max_operand_bits = 32768
            elif calls >= 3:
                ops.a.work.max_operand_bits = 64
        def observe(*values):
            try:
                return rotate(*values)
            except ReferenceError as error:
                failures.append(error)
                raise
        ops.a.work.external_check = changed
        with patch.object(ops, "rotate", side_effect=observe):
            with self.assertRaises(ReferenceError) as caught:
                ops._recording_rotate(q, vector)
        self.assertEqual(len(failures), 1)
        self.assertIs(caught.exception, failures[0])
        self.assertFalse(broadened)
        self.assertEqual(ops.a.cache, {})

    def test_actual_glb_and_independent_validation_match_with_less_work(self):
        for case in ("P01", "P18"):
            outcomes = []
            for optimized in (False, True):
                compiler = compile_construction(source_case(case))
                context = (nullcontext() if optimized else
                           patch.object(_PoseArithmetic, "_recording_rotate", new=_PoseArithmetic.rotate))
                with context:
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                outcomes.append((result.data, result.report["validation"], compiler.budget.operations))
            self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            self.assertLess(outcomes[1][2], outcomes[0][2])

    def test_only_an_advanced_source_lineage_uses_recording_composition_cells(self):
        reference, _ = reference_case("P09", F(1))
        carriers, context = ("rig.arm.forearm.frame",), object()
        with patch.object(reference.p, "_recording_rotate", wraps=reference.p._recording_rotate) as rotate:
            reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
            rotate.assert_not_called()
            reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
            self.assertGreater(rotate.call_count, 0)
            rotate.reset_mock()
            actual = reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=object())
            rotate.assert_not_called()
        state = reference._state_at(F(1, 4), "after")
        expected = reference._pose_map(F(1, 4), state, ideal=True, pose_only=True,
                                       selected=carriers, recording_seed=True)
        self.assertEqual(actual[carriers[0]].position, expected[carriers[0]].position)
        self.assertEqual(actual[carriers[0]].orientation, expected[carriers[0]].orientation)


if __name__ == "__main__":
    unittest.main()
