"""Sequential placements share admission without changing interval arithmetic."""
from contextlib import nullcontext
from dataclasses import replace
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
from test_reach_reference_source_batch import normalized_cursors
from test_reach_reference_world_recording import reference_case


def poses(*, axis=0, scale=F(1), position=None, orientation=None):
    zero = tuple(point(0) for _ in range(3))
    unit = (point(1), *zero)
    first, second, _, _ = dense_values()
    orientation = orientation or (first, point(0), point(0), second)
    position = position or (point(0), point(1), point(0))
    offset = [point(0) for _ in range(3)]
    offset[axis] = point(scale)
    return (PoseEnclosure(position, orientation, zero, zero),
            PoseEnclosure(tuple(offset), unit, zero, zero))


def ordinary():
    return patch.object(_PoseArithmetic, "_recording_native_composition", return_value=None)


class IndependentNativeCompositionTests(unittest.TestCase):
    def test_signed_axis_offsets_keep_every_original_cell(self):
        positive = dense_values()[0]
        values = (positive, Interval(-positive.hi, -positive.lo),
                  Interval(F(-1, 8), F(3, 16)), point(0), point(2))
        positions = ((point(0), point(1), point(0)),
                     (dense_values()[2], dense_values()[3], point(0)),
                     tuple(point(0) for _ in range(3)))
        for w, z, axis, scale, position in product(values, values, (0, 1), (F(1), F(-1), F(3, 4)), positions):
            parent, local = poses(axis=axis, scale=scale, position=position,
                                  orientation=(w, point(0), point(0), z))
            actual, expected = arithmetic(), arithmetic()
            with ordinary():
                before = expected._recording_sequential_compose(parent, local, recording=True)
            with self.subTest(w=w, z=z, axis=axis, scale=scale, position=position):
                self.assertEqual(actual._recording_sequential_compose(parent, local, recording=True), before)
                self.assertLessEqual(actual.a.work.operations, expected.a.work.operations)
                self.assertEqual(actual.a.work.operations, sum(actual.a.work.counts.values()))

    def test_two_ordinary_moving_offsets_measure_the_per_key_saving(self):
        parents = (poses(), poses(position=(dense_values()[2], dense_values()[3], point(0))))
        totals = []
        for enabled in (False, True):
            spent = 0
            for parent, local in parents:
                ops = arithmetic()
                with nullcontext() if enabled else ordinary():
                    result = ops._recording_sequential_compose(parent, local, recording=True)
                spent += ops.a.work.operations
                self.assertIs(result.orientation, parent.orientation)
                if enabled:
                    self.assertEqual(ops.a.cache, {})
            totals.append(spent)
        self.assertLess(totals[1], totals[0])
        print(f"Two independent moving offsets: ordinary={totals[0]}, native={totals[1]}, saved={totals[0] - totals[1]}")

    def test_ordinary_axis_rotation_keeps_its_original_lookup_and_publication(self):
        parent, local = poses()
        ops = arithmetic()
        first = ops._recording_rotate(parent.orientation, local.position)
        key = ops._key("recording_axis_rotation", parent.orientation, local.position)
        self.assertIs(ops.a.cache[key], first)
        start = ops.a.work.operations
        second = ops._recording_rotate(parent.orientation, local.position)
        self.assertIs(first, second)
        self.assertEqual(ops.a.work.operations - start, 2)

    def test_unsupported_shapes_precisions_caps_and_nonidentity_locals_are_ordinary(self):
        parent, local = poses()
        cases = [(128, 32767, parent, local), (64, 32768, parent, local),
                 (256, 32768, parent, local),
                 (128, 32768, parent, replace(local, orientation=parent.orientation)),
                 (128, 32768, parent, replace(local, position=(point(1), point(1), point(0)))),
                 (128, 32768, parent, replace(local, position=(point(1), point(0), point(1)))),
                 (128, 32768, replace(parent, position=(point(F(1, 3)), *parent.position[1:])), local),
                 (128, 32768, replace(parent, velocity=(point(1), *parent.velocity[1:])), local),
                 (128, 32768, replace(parent, position=list(parent.position)), local)]
        for bits, cap, first, last in cases:
            outcomes = []
            for enabled in (False, True):
                ops = arithmetic(bits=bits, cap=cap)
                with nullcontext() if enabled else ordinary():
                    try:
                        result = ops._recording_sequential_compose(first, last, recording=True)
                    except Exception as error:
                        result = (type(error), str(error))
                outcomes.append((result, ops.a.work.operations, ops.a.cache))
            with self.subTest(bits=bits, cap=cap, first=first, last=last):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_nonrecording_composition_never_enters_the_new_admission(self):
        parent, local = poses()
        ops = arithmetic()
        with patch.object(ops, "_recording_native_composition", side_effect=AssertionError("recording only")):
            value = ops._recording_sequential_compose(parent, local)
        self.assertEqual(value, arithmetic().compose(parent, local))

    def test_every_remaining_callback_preserves_cancellation_exception_identity(self):
        parent, local = poses(position=(dense_values()[2], dense_values()[3], point(0)))
        baseline = arithmetic()
        baseline._recording_sequential_compose(parent, local, recording=True)
        for fail_at in range(1, baseline.a.work.operations + 1):
            for marker in (RuntimeError("cancel native independent composition"),
                           ReferenceError("resource", "caller owns this refusal")):
                ops, calls = arithmetic(), 0
                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        ops.a.work.max_operand_bits = 64
                        raise marker
                ops.a.work.external_check = cancel
                with self.subTest(fail_at=fail_at, marker=type(marker)), self.assertRaises(type(marker)) as caught:
                    ops._recording_sequential_compose(parent, local, recording=True)
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.a.work.callback_error, marker)
                self.assertEqual(ops.a.cache, {})

    def test_each_cap_change_discards_the_native_proof_on_the_same_work(self):
        parent, local = poses(position=(dense_values()[2], dense_values()[3], point(0)))
        baseline = arithmetic()
        baseline._recording_sequential_compose(parent, local, recording=True)
        for fail_at in range(1, baseline.a.work.operations + 1):
            ops, calls = arithmetic(), 0
            owner = ops.a.work
            def narrow():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    owner.max_operand_bits = 32767
            owner.external_check = narrow
            actual = ops._recording_sequential_compose(parent, local, recording=True)
            expected = arithmetic(cap=32767)._recording_sequential_compose(parent, local, recording=True)
            with self.subTest(fail_at=fail_at):
                self.assertEqual(actual, expected)
                self.assertIs(ops.a.work, owner)
                self.assertEqual(owner.operations, calls)
                self.assertEqual(owner.max_operand_bits, 32767)
        ops = arithmetic()
        ops.a.work.external_check = lambda: setattr(ops.a.work, "max_operand_bits", 64)
        with self.assertRaises(ReferenceError) as caught:
            ops._recording_sequential_compose(parent, local, recording=True)
        self.assertEqual(caught.exception.code, "resource")

    def test_a_later_callback_cannot_restore_an_invalidated_native_domain(self):
        parent, local = poses()
        ops, calls, admitted = arithmetic(), 0, []
        original = ops._recording_native_composition
        def narrow_then_restore():
            nonlocal calls
            calls += 1
            if calls == 3:
                ops.a.work.max_operand_bits = 32767
            elif calls == 4:
                ops.a.work.max_operand_bits = 32768
        def observe(*args):
            result = original(*args)
            admitted.append(result)
            return result
        ops.a.work.external_check = narrow_then_restore
        with patch.object(ops, "_recording_native_composition", side_effect=observe):
            actual = ops._recording_sequential_compose(parent, local, recording=True)
        with ordinary():
            expected = arithmetic()._recording_sequential_compose(parent, local, recording=True)
        self.assertEqual(actual, expected)
        self.assertEqual(admitted, [None])
        self.assertEqual(ops.a.work.max_operand_bits, 32768)

    def test_operand_and_wrapper_mutation_cannot_borrow_an_earlier_receipt(self):
        for kind in ("position", "orientation", "velocity", "cell", "fraction"):
            parent, local = poses()
            ops, calls = arithmetic(), 0
            def mutate():
                nonlocal calls
                calls += 1
                if calls != 2:
                    return
                if kind in ("position", "velocity"):
                    object.__setattr__(local, kind, (point(1), point(1), point(0)))
                elif kind == "orientation":
                    object.__setattr__(local, "orientation", (point(0), point(0), point(1), point(0)))
                elif kind == "cell":
                    object.__setattr__(parent.position[1], "hi", F(2))
                else:
                    object.__setattr__(parent.position[1].lo, "_numerator", 2)
            ops.a.work.external_check = mutate
            with self.subTest(kind=kind), self.assertRaises(ReferenceError) as caught:
                ops._recording_sequential_compose(parent, local, recording=True)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(ops.a.cache, {})

    def test_replaced_arithmetic_work_or_callback_owner_cannot_authorize_a_result(self):
        for kind in ("arithmetic", "work", "check", "external"):
            parent, local = poses()
            ops, calls = arithmetic(), 0
            owner = ops.a
            def mutate():
                nonlocal calls
                calls += 1
                if calls != 2:
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
                ops._recording_sequential_compose(parent, local, recording=True)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(owner.cache, {})

    def test_reentrant_compositions_have_separate_receipts_and_exact_results(self):
        parent, local = poses()
        other_parent, other_local = poses(axis=1, scale=F(-1))
        ops, nested, calls = arithmetic(), [], 0
        def reenter():
            nonlocal calls
            calls += 1
            if calls == 3:
                nested.append(ops._recording_sequential_compose(other_parent, other_local, recording=True))
        ops.a.work.external_check = reenter
        actual = ops._recording_sequential_compose(parent, local, recording=True)
        with ordinary():
            expected = arithmetic()._recording_sequential_compose(parent, local, recording=True)
            other = arithmetic()._recording_sequential_compose(other_parent, other_local, recording=True)
        self.assertEqual(actual, expected)
        self.assertEqual(nested, [other])
        self.assertEqual(ops.a.cache, {})

    def test_actual_source_cells_cursors_eviction_and_reseeding_stay_identical(self):
        for case in ("P09", "L03"):
            outcomes = []
            for enabled in (False, True):
                reference, _ = reference_case(case, F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                observations = []
                with nullcontext() if enabled else ordinary():
                    with reference.recording_source_batch(context):
                        for index in range(68):
                            if case == "L03" and index == 32:
                                for item in range(MAX_CACHE):
                                    reference.a.remember(("native-placement-evict", item), F(item))
                            value = reference.recording_pose_enclosures(carriers, F(index, 256),
                                                                         recording_context=context)
                            cursors = normalized_cursors(reference)
                            observations.append((value, cursors))
                            if case == "P09" and index == 65 or case == "L03" and index == 32:
                                self.assertTrue(cursors)
                                self.assertTrue(all(value[-1] == 0 for value in cursors.values()))
                            self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
                outcomes.append(observations)
            with self.subTest(case=case):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_persistent_source_mutation_still_fails_the_complete_batch(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        joint = next(value for value in reference.model.joints.values() if value.kind == "hinge")
        original_axis = joint.axis
        actual, armed, changed = reference.p._recording_native_composition, False, []
        check = reference.a.work.external_check
        def observe(*args):
            nonlocal armed
            armed = True
            try:
                return actual(*args)
            finally:
                armed = False
        def mutate():
            if check is not None:
                check()
            if armed and not changed:
                joint.axis = (1.0, 0.0, 0.0)
                changed.append(True)
        reference.a.work.external_check = mutate
        try:
            with self.assertRaises(ReferenceError) as caught:
                with reference.recording_source_batch(context):
                    reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                    with patch.object(reference.p, "_recording_native_composition", side_effect=observe):
                        reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
            self.assertEqual(caught.exception.code, "identity")
            self.assertTrue(changed)
        finally:
            joint.axis = original_axis

    def test_original_source_prefix_bytes_and_validation_are_unchanged(self):
        savings = []
        for case in ("P09", "P11", "L03"):
            results = []
            for enabled in (False, True):
                compiler = compile_construction(source_case(case))
                with nullcontext() if enabled else ordinary():
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                results.append((result.data, result.report["validation"], compiler.budget.operations))
            with self.subTest(case=case):
                self.assertEqual(results[0][:2], results[1][:2])
                self.assertLessEqual(results[1][2], results[0][2])
            savings.append(results[0][2] - results[1][2])
            print(f"{case} native composition prefix: ordinary={results[0][2]}, native={results[1][2]}")
        self.assertGreater(sum(savings), 0)


if __name__ == "__main__":
    unittest.main()
