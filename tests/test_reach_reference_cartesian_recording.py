"""Independent Cartesian recording rotations retain Hamilton containment."""
from contextlib import contextmanager, nullcontext
from fractions import Fraction as F
from itertools import product
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import Interval, MAX_CACHE, PoseEnclosure, ReferenceError, _PoseArithmetic
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_fused_recording import arithmetic, dense_values, point


def quaternion(axis, w=None, s=None):
    first, second, _, _ = dense_values()
    values = [first if w is None else w, point(0), point(0), point(0)]
    values[axis + 1] = second if s is None else s
    return tuple(values)


def vector(values=(F(-3, 16), F(1, 4), F(7, 32))):
    return tuple(value if isinstance(value, Interval) else point(value) for value in values)


def poses(q=None, offset=None, position=None):
    zero = vector((0, 0, 0))
    return (PoseEnclosure(vector((0, 2, 0)) if position is None else position,
                          quaternion(1) if q is None else q, zero, zero),
            PoseEnclosure(vector() if offset is None else offset,
                          (point(1), *zero), zero, zero))


def hamilton(left, right):
    w, x, y, z = left
    a, b, c, d = right
    return (w*a - x*b - y*c - z*d,
            w*b + x*a + y*d - z*c,
            w*c - x*d + y*a + z*b,
            w*d + x*c - y*b + z*a)


def rotated(q, offset):
    return hamilton(hamilton(q, (F(0), *offset)), (q[0], *(-value for value in q[1:])))[1:]


def samples(cell):
    return (cell.lo,) if cell.lo == cell.hi else (cell.lo, (cell.lo + cell.hi) / 2, cell.hi)


@contextmanager
def preceding_recording():
    """Reconstruct the preceding cbb native-composition admission domain."""
    original = _PoseArithmetic._recording_native_composition

    def previous(self, parent, local):
        q, offset = parent.orientation, local.position
        if (not self._zero((q[1], q[2], offset[2]))
                or not (self._zero((offset[0],)) or self._zero((offset[1],)))):
            return None
        return original(self, parent, local)

    with patch.object(_PoseArithmetic, "_recording_cartesian_rotate", return_value=None), \
            patch.object(_PoseArithmetic, "_recording_native_composition", new=previous):
        yield


class IndependentCartesianRecordingTests(unittest.TestCase):
    def test_signed_cartesian_boxes_enclose_independent_point_hamilton_products(self):
        positive = dense_values()[0]
        negative = Interval(-positive.hi, -positive.lo)
        crossing = Interval(F(-1, 8), F(3, 16))
        offsets = (vector(), vector((Interval(F(-1, 4), F(3, 8)), F(-1, 2), F(1, 8))),
                   vector((0, F(3, 4), 0)), vector((1, 0, 0)))
        for axis, w, s, offset in product(range(3), (positive, negative, crossing),
                                         (positive, negative, crossing), offsets):
            ops = arithmetic()
            q = quaternion(axis, w, s)
            actual = ops._recording_rotate(q, offset)
            with self.subTest(axis=axis, w=w, s=s, offset=offset):
                for values in product(*(samples(cell) for cell in (*q, *offset))):
                    expected = rotated(values[:4], values[4:])
                    self.assertTrue(all(cell.contains(value) for cell, value in zip(actual, expected)))
                self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))
                self.assertLessEqual(len(ops.a.cache), MAX_CACHE)

    def test_proper_cyclic_signs_and_nonunit_axial_scale_are_explicit(self):
        # q=(1,e_axis) is deliberately nonunit. Its axial factor is two;
        # the positive perpendicular basis vector rotates to twice the next.
        for axis in range(3):
            q = quaternion(axis, point(1), point(1))
            first, second = (axis + 1) % 3, (axis + 2) % 3
            for coordinate, output, sign in ((first, second, 1), (second, first, -1), (axis, axis, 1)):
                offset, expected = [F(0)] * 3, [F(0)] * 3
                offset[coordinate], expected[output] = F(1), F(2 * sign)
                with self.subTest(axis=axis, coordinate=coordinate):
                    actual = arithmetic()._recording_rotate(q, vector(offset))
                    self.assertEqual(actual, vector(expected))
        q = quaternion(1, point(F(3, 4)), point(F(-1, 8)))
        actual = arithmetic()._recording_rotate(q, vector((0, F(1, 4), 0)))
        self.assertEqual(actual[1], point(F(37, 256)))
        self.assertNotEqual(actual[1], point(F(1, 4)))

    def test_original_taylor_seeds_contain_finer_independent_hamilton_cells(self):
        for axis, angle, offset in product(range(3), (F(1, 8), F(-3, 16), F(7, 32)),
                                           (vector(), vector((0, F(1, 4), 0)), vector((1, 0, 0)))):
            coarse, fine = arithmetic(), arithmetic(bits=256)
            sine, cosine = coarse.a.sincos(angle)
            fine_sine, fine_cosine = fine.a.sincos(angle)
            q, fine_q = quaternion(axis, cosine, sine), quaternion(axis, fine_cosine, fine_sine)
            actual = coarse._recording_rotate(q, offset)
            expected = fine.rotate(fine_q, offset)
            with self.subTest(axis=axis, angle=angle, offset=offset):
                for cell, finer in zip(actual, expected):
                    self.assertLessEqual(cell.lo, finer.lo)
                    self.assertGreaterEqual(cell.hi, finer.hi)

    def test_preceding_z_single_offsets_keep_their_cells_order_and_counts(self):
        q = quaternion(2)
        for axis, expected_count in ((0, 15), (1, 16)):
            offset = [point(0)] * 3
            offset[axis] = point(1)
            ops = arithmetic()
            with patch.object(ops, "_recording_cartesian_rotate", side_effect=AssertionError("old path changed")):
                actual = ops._recording_rotate(q, tuple(offset))
            before = arithmetic()
            with preceding_recording():
                expected = before._recording_rotate(q, tuple(offset))
            self.assertEqual(actual, expected)
            self.assertEqual(ops.a.work.operations, expected_count)
            self.assertEqual(ops.a.work.counts, before.a.work.counts)

    def test_cartesian_cache_keys_bind_axis_and_complete_offsets_and_remain_bounded(self):
        ops, offset = arithmetic(), vector()
        values = [ops._recording_rotate(quaternion(axis), offset) for axis in range(3)]
        self.assertEqual(len(set(values)), 3)
        for axis, expected in enumerate(values):
            before = ops.a.work.operations
            self.assertIs(ops._recording_rotate(quaternion(axis), offset), expected)
            self.assertEqual(ops.a.work.operations - before, 2)
        changed = ops._recording_rotate(quaternion(1), vector((F(-3, 16), F(1, 4), F(-7, 32))))
        self.assertNotEqual(changed, values[1])
        key = ops._key("recording_cartesian_rotation", quaternion(1), offset)
        for index in range(MAX_CACHE):
            ops.a.remember(("evict-cartesian-recording", index), F(index))
        self.assertNotIn(key, ops.a.cache)
        self.assertEqual(ops._recording_rotate(quaternion(1), offset), values[1])
        self.assertEqual(len(ops.a.cache), MAX_CACHE)
        ops.a.work.max_operand_bits = 127
        with self.assertRaises(ReferenceError) as caught:
            ops._recording_rotate(quaternion(1), offset)
        self.assertEqual(caught.exception.code, "resource")

    def test_mixed_foreign_nondyadic_and_narrow_domains_keep_the_original_path(self):
        q, offset = quaternion(1), vector()
        cases = [(128, 32767, q, offset), (64, 32768, q, offset), (256, 32768, q, offset),
                 (128, 32768, (q[0], point(F(1, 4)), q[2], q[3]), offset),
                 (128, 32768, quaternion(1, point(F(1, 3))), offset),
                 (128, 32768, q, vector((F(1, 3), F(1, 4), F(1, 8)))),
                 (128, 32768, list(q), offset), (128, 32768, q, list(offset)),
                 (128, 32768, q, vector((0, 0, 0))),
                 (128, 32768, quaternion(1, point(1), point(0)), offset)]
        for bits, cap, rotation, position in cases:
            ops, before = arithmetic(bits=bits, cap=cap), arithmetic(bits=bits, cap=cap)
            with self.subTest(bits=bits, cap=cap, rotation=rotation, position=position):
                self.assertEqual(ops._recording_rotate(rotation, position), before.rotate(rotation, position))
                self.assertEqual(ops.a.work.operations, before.a.work.operations)
                self.assertEqual(ops.a.cache, before.a.cache)

    def test_every_cartesian_callback_preserves_cancellation_exception_identity(self):
        q, offset = quaternion(1), vector()
        baseline = arithmetic()
        baseline._recording_rotate(q, offset)
        for fail_at in range(1, baseline.a.work.operations + 1):
            for marker in (RuntimeError("cancel Cartesian enclosure"),
                           ReferenceError("resource", "the caller owns this refusal")):
                ops, calls = arithmetic(), 0
                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        ops.a.work.max_operand_bits = 64
                        raise marker
                ops.a.work.external_check = cancel
                with self.subTest(fail_at=fail_at, marker=type(marker)), self.assertRaises(type(marker)) as caught:
                    ops._recording_rotate(q, offset)
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.a.work.callback_error, marker)
                self.assertEqual(ops.a.cache, {})

    def test_each_live_cap_change_replays_the_original_on_the_same_work(self):
        q, offset = quaternion(1), vector()
        baseline = arithmetic()
        baseline._recording_rotate(q, offset)
        for fail_at in range(1, baseline.a.work.operations + 1):
            ops, calls = arithmetic(), 0
            owner = ops.a.work
            def narrow():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    owner.max_operand_bits = 32767
            owner.external_check = narrow
            with patch.object(ops, "rotate", wraps=ops.rotate) as direct:
                actual = ops._recording_rotate(q, offset)
            with self.subTest(fail_at=fail_at):
                direct.assert_called_once_with(q, offset)
                self.assertEqual(actual, arithmetic(cap=32767).rotate(q, offset))
                self.assertIs(ops.a.work, owner)
                self.assertEqual(owner.operations, calls)
                self.assertFalse(any(len(key) > 3 and key[3] == "recording_cartesian_rotation"
                                     for key in ops.a.cache))

    def test_a_later_callback_cannot_restore_a_discarded_cartesian_domain(self):
        ops, q, offset, calls = arithmetic(), quaternion(1), vector(), 0
        def narrow_restore():
            nonlocal calls
            calls += 1
            if calls == 3:
                ops.a.work.max_operand_bits = 32767
            elif calls == 4:
                ops.a.work.max_operand_bits = 32768
        ops.a.work.external_check = narrow_restore
        with patch.object(ops, "rotate", wraps=ops.rotate) as direct:
            actual = ops._recording_rotate(q, offset)
        direct.assert_called_once_with(q, offset)
        self.assertEqual(actual, arithmetic().rotate(q, offset))
        self.assertFalse(any(key[3] == "recording_cartesian_rotation" for key in ops.a.cache))

    def test_wrapper_and_fraction_mutations_are_checked_at_each_callback(self):
        baseline = arithmetic()
        baseline._recording_rotate(quaternion(1), vector())
        for fail_at, kind in product((1, 2, 3, 7, baseline.a.work.operations),
                                     ("quaternion", "offset", "fraction")):
            ops, q, offset, calls = arithmetic(), quaternion(1), vector(), 0
            def mutate():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    if kind == "quaternion":
                        object.__setattr__(q[0], "hi", F(1, 2))
                    elif kind == "offset":
                        object.__setattr__(offset[0], "lo", F(-1, 2))
                    else:
                        object.__setattr__(offset[1].lo, "_numerator", 3)
            ops.a.work.external_check = mutate
            with self.subTest(fail_at=fail_at, kind=kind), self.assertRaises(ReferenceError) as caught:
                ops._recording_rotate(q, offset)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(ops.a.cache, {})

    def test_transient_operand_mutation_is_rejected_before_a_restoring_callback(self):
        ops, q, offset, calls = arithmetic(), quaternion(1), vector(), 0
        original = offset[0].lo
        def mutate_restore():
            nonlocal calls
            calls += 1
            if calls == 3:
                object.__setattr__(offset[0], "lo", F(-1, 2))
            elif calls == 4:
                object.__setattr__(offset[0], "lo", original)
        ops.a.work.external_check = mutate_restore
        with self.assertRaises(ReferenceError) as caught:
            ops._recording_rotate(q, offset)
        self.assertEqual(caught.exception.code, "identity")
        self.assertEqual(calls, 3)
        self.assertEqual(ops.a.cache, {})

    def test_replaced_native_record_classes_are_rejected_before_foreign_attribute_reads(self):
        calls = []

        class ForeignCell(Interval):
            def __getattribute__(self, name):
                calls.append(name)
                return object.__getattribute__(self, name)

        class ForeignPose(PoseEnclosure):
            def __getattribute__(self, name):
                calls.append(name)
                return object.__getattribute__(self, name)

        for kind in ("cell", "pose"):
            ops, seen = arithmetic(), []
            parent, local = poses()
            def mutate():
                if seen:
                    return
                seen.append(True)
                target, replacement = ((parent.orientation[0], ForeignCell) if kind == "cell" else
                                       (parent, ForeignPose))
                object.__setattr__(target, "__class__", replacement)
            ops.a.work.external_check = mutate
            with self.subTest(kind=kind), self.assertRaises(ReferenceError) as caught:
                if kind == "cell":
                    ops._recording_rotate(parent.orientation, local.position)
                else:
                    # The outer composition admission precedes its receipt;
                    # install the mutation only once the native helper starts.
                    ops.a.work.external_check = None
                    original = ops._recording_native_composition
                    def native(*args):
                        ops.a.work.external_check = mutate
                        return original(*args)
                    with patch.object(ops, "_recording_native_composition", side_effect=native):
                        ops._recording_sequential_compose(parent, local, recording=True)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(calls, [])
            self.assertEqual(ops.a.cache, {})

    def test_arithmetic_work_and_callback_owner_replacement_cannot_authorize_output(self):
        for kind in ("arithmetic", "work", "check", "external"):
            ops, calls = arithmetic(), 0
            owner = ops.a
            def mutate():
                nonlocal calls
                calls += 1
                if calls != 3:
                    return
                if kind == "arithmetic":
                    ops.a = arithmetic().a
                elif kind == "work":
                    owner.work = arithmetic().a.work
                elif kind == "check":
                    owner.check = lambda: None
                else:
                    owner.work.external_check = lambda: None
            owner.work.external_check = mutate
            with self.subTest(kind=kind), self.assertRaises(ReferenceError) as caught:
                ops._recording_rotate(quaternion(1), vector())
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(owner.cache, {})

    def test_reentrant_axis_rotations_have_separate_receipts_and_lru_keys(self):
        ops, calls, nested = arithmetic(), 0, []
        q, offset = quaternion(1), vector()
        other_q, other_offset = quaternion(0), vector((F(1, 8), F(-1, 4), F(3, 16)))
        def reenter():
            nonlocal calls
            calls += 1
            if calls == 3:
                nested.append(ops._recording_rotate(other_q, other_offset))
        ops.a.work.external_check = reenter
        actual = ops._recording_rotate(q, offset)
        self.assertEqual(actual, arithmetic()._recording_rotate(q, offset))
        self.assertEqual(nested, [arithmetic()._recording_rotate(other_q, other_offset)])
        self.assertEqual(len(ops.a.cache), 2)
        self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))

    def test_translated_native_composition_preserves_exact_nonunit_hamilton_result(self):
        for axis in range(3):
            parent, local = poses(quaternion(axis, point(F(3, 4)), point(F(-1, 8))),
                                  position=vector((F(5, 4), F(-7, 8), F(3, 16))))
            ops = arithmetic()
            actual = ops._recording_sequential_compose(parent, local, recording=True)
            expected = arithmetic().compose(parent, local)
            with self.subTest(axis=axis):
                self.assertEqual(actual, expected)
                self.assertIs(actual.orientation, parent.orientation)
                self.assertIs(actual.velocity, parent.velocity)
                self.assertIs(actual.omega, parent.omega)
                self.assertEqual(ops.a.cache, {})

    def test_cartesian_composition_binds_the_complete_parent_and_local_pose(self):
        for kind in ("parent_position", "parent_velocity", "local_orientation", "local_omega"):
            parent, local = poses()
            ops, calls = arithmetic(), 0
            def mutate():
                nonlocal calls
                calls += 1
                if calls != 2:
                    return
                if kind == "parent_position":
                    object.__setattr__(parent, "position", vector((1, 2, 3)))
                elif kind == "parent_velocity":
                    object.__setattr__(parent, "velocity", vector((1, 0, 0)))
                elif kind == "local_orientation":
                    object.__setattr__(local, "orientation", quaternion(0))
                else:
                    object.__setattr__(local, "omega", vector((1, 0, 0)))
            ops.a.work.external_check = mutate
            with self.subTest(kind=kind), self.assertRaises(ReferenceError) as caught:
                ops._recording_sequential_compose(parent, local, recording=True)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(ops.a.cache, {})

    def test_the_p11_head_and_three_eye_offset_pattern_has_a_measured_cost(self):
        seed = arithmetic()
        sine, cosine = seed.a.sincos(F(1, 8))
        q = quaternion(1, cosine, sine)
        # Exact source binary64 operands, including the inverse head origin.
        offsets = ((0.0, 0.25, 0.0), (-0.1, 0.05, 0.23),
                   (0.1, 0.05, 0.23), (0.0, 0.16, 0.2))
        outcomes = []
        for enabled in (False, True):
            ops, values, costs = arithmetic(), [], []
            with nullcontext() if enabled else preceding_recording():
                for offset in offsets:
                    parent, local = poses(q, vector(offset))
                    before = ops.a.work.operations
                    values.append(ops._recording_sequential_compose(parent, local, recording=True))
                    costs.append(ops.a.work.operations - before)
            outcomes.append((values, costs, ops.a.work.operations))
        self.assertLess(outcomes[1][2], outcomes[0][2])
        for before, after in zip(outcomes[0][0], outcomes[1][0]):
            self.assertEqual(before.orientation, after.orientation)
            for old, new in zip(before.position, after.position):
                self.assertGreaterEqual(new.lo, old.lo)
                self.assertLessEqual(new.hi, old.hi)
        print(f"P11 independent offset pattern: previous={outcomes[0][1]} ({outcomes[0][2]}), "
              f"Cartesian={outcomes[1][1]} ({outcomes[1][2]}), saved={outcomes[0][2] - outcomes[1][2]}")

    def test_generic_composition_never_uses_the_recording_cartesian_formula(self):
        parent, local = poses()
        ops = arithmetic()
        with patch.object(ops, "_recording_cartesian_rotate", side_effect=AssertionError("ordinary source read")):
            actual = ops.compose(parent, local)
        self.assertEqual(actual, arithmetic().compose(parent, local))

    def test_original_fallback_failure_is_not_retried_after_later_broadening(self):
        ops, calls, failures, broadened = arithmetic(), 0, [], []
        q, offset, original = quaternion(1), vector(), ops.rotate
        def narrow():
            nonlocal calls
            calls += 1
            if failures:
                broadened.append(True)
                ops.a.work.max_operand_bits = 32768
            elif calls == 3:
                ops.a.work.max_operand_bits = 64
        def observe(*args):
            try:
                return original(*args)
            except ReferenceError as error:
                failures.append(error)
                raise
        ops.a.work.external_check = narrow
        with patch.object(ops, "rotate", side_effect=observe), self.assertRaises(ReferenceError) as caught:
            ops._recording_rotate(q, offset)
        self.assertEqual(len(failures), 1)
        self.assertIs(caught.exception, failures[0])
        self.assertFalse(broadened)

    def test_original_source_prefix_bytes_and_independent_validation_are_preserved(self):
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for enabled in (False, True):
                compiler = compile_construction(source_case(case))
                with nullcontext() if enabled else preceding_recording():
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                outcomes.append((result.data, result.report["validation"], compiler.budget.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLessEqual(outcomes[1][2], outcomes[0][2])
            print(f"{case} Cartesian independent prefix: previous={outcomes[0][2]}, candidate={outcomes[1][2]}")


if __name__ == "__main__":
    unittest.main()
