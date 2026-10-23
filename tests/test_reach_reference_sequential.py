"""Sequential independent poses keep their exact cells and bounded guards."""
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
from test_reach_reference_world_recording import reference_case


ZERO = (point(0),) * 3
UNIT = (point(1), *ZERO)


def poses():
    first, second, third, fourth = dense_values()
    return (PoseEnclosure((point(3), point(-2), point(0)),
                          (first, point(0), point(0), second), ZERO, ZERO),
            PoseEnclosure((point(1), point(0), point(0)),
                          (third, point(0), point(0), fourth), ZERO, ZERO))


def ordinary(ops, parent, local, *, recording=False):
    return ops.compose(parent, local, recording=recording)


class IndependentSequentialPoseTests(unittest.TestCase):
    def test_scalar_z_products_keep_exact_original_interval_cells_for_all_signs(self):
        positive = dense_values()[0]
        values = (positive, Interval(-positive.hi, -positive.lo),
                  Interval(F(-1, 8), F(3, 16)), point(0), point(1), point(-1))
        for w, z, other_w, other_z in product(values, repeat=4):
            left, right = (w, point(0), point(0), z), (other_w, point(0), point(0), other_z)
            actual, expected = arithmetic(), arithmetic()
            result = actual._recording_sequential_multiply(left, right)
            self.assertEqual(result, expected.multiply(left, right))
            self.assertLessEqual(actual.a.work.operations, expected.a.work.operations)
            self.assertEqual(actual.a.cache, {})
            self.assertEqual(actual.a.work.operations, sum(actual.a.work.counts.values()))

    def test_position_only_compositions_keep_original_fields_and_skip_one_use_entries(self):
        parent, local = poses()
        identity = PoseEnclosure(ZERO, UNIT, ZERO, ZERO)
        for recording, first, second in product((False, True), (parent, identity), (local, identity)):
            with self.subTest(recording=recording, first=first, second=second):
                actual, expected = arithmetic(), arithmetic()
                result = actual._recording_sequential_compose(first, second, recording=recording)
                self.assertEqual(result, expected.compose(first, second, recording=recording))
                self.assertLessEqual(actual.a.work.operations, expected.a.work.operations)
                self.assertFalse(any(key[:1] == ("reference_pose",) and
                                     key[3] in ("multiply", "compose", "recording_compose")
                                     for key in actual.a.cache))
                self.assertLessEqual(len(actual.a.cache), MAX_CACHE)

    def test_nonunit_products_preserve_scale_and_reuse_only_an_exact_zero(self):
        left = tuple(map(point, (2, 0, 0, 3)))
        right = tuple(map(point, (-4, 0, 0, 5)))
        ops = arithmetic()
        result = ops._recording_sequential_multiply(left, right)
        self.assertEqual(result, tuple(map(point, (-23, 0, 0, -2))))
        self.assertIs(result[1], left[1])
        self.assertIs(result[2], left[1])

    def test_nonzero_derivatives_other_shapes_and_narrow_domains_keep_original_path(self):
        parent, local = poses()
        cases = [(128, 32767, parent, local), (64, 32768, parent, local),
                 (256, 32768, parent, local)]
        for changed in (replace(parent, velocity=(point(1), *ZERO[1:])),
                        replace(parent, omega=(point(1), *ZERO[1:])),
                        replace(parent, position=list(parent.position)),
                        replace(parent, position=(Interval(False, False), *ZERO[1:])),
                        replace(parent, position=(point(1 << 300), *ZERO[1:]))):
            cases.append((128, 32768, changed, local))
        for bits, cap, first, second in cases:
            with self.subTest(bits=bits, cap=cap, first=first):
                actual, expected = arithmetic(bits=bits, cap=cap), arithmetic(bits=bits, cap=cap)
                outcomes = []
                for function in (actual._recording_sequential_compose, expected.compose):
                    try:
                        outcomes.append(function(first, second, recording=True))
                    except Exception as error:
                        outcomes.append((type(error), str(error)))
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(actual.a.work.operations, expected.a.work.operations)

    def test_unsupported_hamilton_inputs_preserve_original_cells_and_failure_location(self):
        parent, local = poses()
        inputs = ((list(parent.orientation), local.orientation),
                  ((parent.orientation[0], point(1), *parent.orientation[2:]), local.orientation),
                  ((point(1 << 33000), *parent.orientation[1:]), local.orientation),
                  ((point(F(1, 1 << 33000)), *parent.orientation[1:]), local.orientation))
        for left, right in inputs:
            results = []
            for optimized in (False, True):
                ops = arithmetic()
                try:
                    value = (ops._recording_sequential_multiply(left, right) if optimized else
                             ops.multiply(left, right))
                except Exception as error:
                    value = (type(error), str(error))
                results.append((value, ops.a.work.operations))
            self.assertEqual(results[0], results[1])

    def test_each_multiply_callback_can_cancel_without_new_cache_or_masked_error(self):
        parent, local = poses()
        baseline = arithmetic()
        baseline._recording_sequential_multiply(parent.orientation, local.orientation)
        for fail_at in range(1, baseline.a.work.operations + 1):
            for marker in (RuntimeError("stop sequential product"), ReferenceError("resource", "caller stop")):
                with self.subTest(fail_at=fail_at, marker=marker):
                    ops, calls = arithmetic(), 0
                    def cancel():
                        nonlocal calls
                        calls += 1
                        if calls == fail_at:
                            ops.a.work.max_operand_bits = 64
                            raise marker
                    ops.a.work.external_check = cancel
                    with self.assertRaises(type(marker)) as caught:
                        ops._recording_sequential_multiply(parent.orientation, local.orientation)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(ops.a.work.callback_error, marker)
                    self.assertEqual(ops.a.cache, {})

    def test_changed_multiply_cap_replays_original_cells_and_respects_too_small_domains(self):
        parent, local = poses()
        baseline = arithmetic()
        baseline._recording_sequential_multiply(parent.orientation, local.orientation)
        for fail_at in range(1, baseline.a.work.operations + 1):
            with self.subTest(fail_at=fail_at):
                ops, calls = arithmetic(), 0
                def narrow():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        ops.a.work.max_operand_bits = 32767
                ops.a.work.external_check = narrow
                result = ops._recording_sequential_multiply(parent.orientation, local.orientation)
                self.assertEqual(result, arithmetic(cap=32767).multiply(parent.orientation, local.orientation))
                self.assertEqual(ops.a.work.max_operand_bits, 32767)
        ops = arithmetic()
        ops.a.work.external_check = lambda: setattr(ops.a.work, "max_operand_bits", 64)
        with self.assertRaises(ReferenceError) as caught:
            ops._recording_sequential_multiply(parent.orientation, local.orientation)
        self.assertEqual(caught.exception.code, "resource")

    def test_each_compose_callback_can_cancel_without_publishing_a_partial_pose(self):
        parent, local = poses()
        baseline = arithmetic()
        baseline._recording_sequential_compose(parent, local, recording=True)
        for fail_at in range(1, baseline.a.work.operations + 1):
            ops, calls = arithmetic(), 0
            marker = RuntimeError("stop sequential composition")
            def cancel():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    raise marker
            ops.a.work.external_check = cancel
            with self.subTest(fail_at=fail_at), self.assertRaises(RuntimeError) as caught:
                ops._recording_sequential_compose(parent, local, recording=True)
            self.assertIs(caught.exception, marker)
            self.assertFalse(any(key[:1] == ("reference_pose",) and key[3] == "recording_compose"
                                 for key in ops.a.cache))

    def test_reentry_keeps_both_completed_arithmetic_results_independent(self):
        parent, local = poses()
        ops, nested, armed = arithmetic(), [], True
        def reenter():
            nonlocal armed
            if armed:
                armed = False
                nested.append(ops._recording_sequential_compose(local, parent, recording=True))
        ops.a.work.external_check = reenter
        result = ops._recording_sequential_compose(parent, local, recording=True)
        self.assertEqual(result, arithmetic().compose(parent, local, recording=True))
        self.assertEqual(nested, [arithmetic().compose(local, parent, recording=True)])

    def test_context_free_samples_never_use_sequential_composition(self):
        reference, _ = reference_case("P01", F(1, 4))
        with patch.object(reference.p, "_recording_sequential_compose", side_effect=AssertionError("recording only")):
            reference.recording_pose_enclosures(("rig.arm.forearm",), F(1, 8))
            reference.boundary_states()

    def test_source_recording_cells_match_at_cold_and_advanced_clocks(self):
        for case in ("P01", "P09", "P11", "L03"):
            results = []
            for optimized in (False, True):
                reference, _ = reference_case(case, F(1, 4))
                carriers, context = tuple(reference.model.objects), object()
                selected = nullcontext() if optimized else patch.object(
                    _PoseArithmetic, "_recording_sequential_compose", new=ordinary)
                with selected:
                    results.append([reference.recording_pose_enclosures(carriers, clock, recording_context=context)
                                    for clock in (F(1, 16), F(1, 8), F(3, 16), F(1, 4))])
            with self.subTest(case=case):
                self.assertEqual(results[0], results[1])

    def test_actual_prefix_glb_bytes_and_validation_match_with_less_work(self):
        savings = []
        for case in ("P01", "P09", "P11", "L03"):
            results = []
            for optimized in (False, True):
                compiler = compile_construction(source_case(case))
                selected = nullcontext() if optimized else patch.object(
                    _PoseArithmetic, "_recording_sequential_compose", new=ordinary)
                with selected:
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
            print(f"{case} prefix: ordinary={results[0][2]}, sequential={results[1][2]}")
        self.assertGreater(sum(savings), 0)

    def test_broad_graph_keeps_its_existing_shared_cache_policy(self):
        reference, _ = reference_case("P11", F(1, 4))
        carriers, context = tuple(reference.model.objects), object()
        self.assertGreater(len(carriers), 16)
        with patch.object(reference.p, "_recording_sequential_compose", side_effect=AssertionError("small graphs only")):
            for clock in (F(1, 8), F(1, 4)):
                reference.recording_pose_enclosures(carriers, clock, recording_context=context)


if __name__ == "__main__":
    unittest.main()
