"""Sparse independent Hamilton products preserve the original interval cells."""
from contextlib import nullcontext
from fractions import Fraction as F
from itertools import product
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import Interval, MAX_CACHE, ReferenceError, _Arithmetic, _PoseArithmetic
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_fused_recording import arithmetic, dense_values, point
from test_reach_reference_world_recording import reference_case


def representative(axis, scalar, component):
    values = [scalar, point(0), point(0), point(0)]
    values[axis] = component
    return tuple(values)


def operands(axis):
    a, b, c, d = dense_values()
    return representative(axis, a, b), representative(axis, c, d)


def ordinary():
    # The full preexisting Hamilton expression remains the test oracle.
    return patch.object(_PoseArithmetic, "_sparse_cartesian_multiply", return_value=None)


class IndependentSparseCartesianTests(unittest.TestCase):
    def test_all_product_signs_keep_exact_original_cells_and_cache_keys(self):
        positive = dense_values()[0]
        values = (positive, Interval(-positive.hi, -positive.lo), Interval(F(-1, 8), F(3, 16)))
        for axis in (1, 2):
            for a, b, c, d in product(values, repeat=4):
                left, right = representative(axis, a, b), representative(axis, c, d)
                actual, expected = arithmetic(), arithmetic()
                with ordinary():
                    before = expected.multiply(left, right)
                result = actual.multiply(left, right)
                with self.subTest(axis=axis, values=(a, b, c, d)):
                    self.assertEqual(result, before)
                    self.assertEqual(actual.a.cache, expected.a.cache)
                    self.assertLess(actual.a.work.operations, expected.a.work.operations)
                    self.assertEqual(actual.a.work.operations, sum(actual.a.work.counts.values()))

    def test_points_zero_identity_and_nonunit_axis_rotation_keep_original_scale(self):
        for axis in (1, 2):
            for values in ((2, 3, -4, 5), (0, 2, 3, 0), (1, 0, -1, 2),
                           (F(1, 3), F(-2, 7), F(3, 11), F(5, 13))):
                a, b, c, d = map(point, values)
                left, right = representative(axis, a, b), representative(axis, c, d)
                with ordinary():
                    expected = arithmetic().multiply(left, right)
                self.assertEqual(arithmetic().multiply(left, right), expected)
            raw = representative(axis, point(2), point(3))
            vector = [point(0)] * 3
            vector[axis - 1] = point(5)
            expected = [point(0)] * 3
            expected[axis - 1] = point(65)  # (2**2 + 3**2) * 5, with no unit substitution.
            self.assertEqual(arithmetic().rotate(raw, tuple(vector)), tuple(expected))

    def test_other_precisions_shapes_axes_and_domains_use_the_complete_expression(self):
        left, right = operands(2)
        uncertain = Interval(F(-1, 1 << 128), F(1, 1 << 128))
        cases = [(64, 32768, left, right), (256, 32768, left, right),
                 (128, 32767, left, right), (128, 32768, list(left), right),
                 (128, 32768, (left[0], uncertain, left[2], left[3]), right),
                 (128, 32768, (left[0], point(1), left[2], left[3]), right),
                 (128, 32768, (left[0], Interval(False, False), left[2], left[3]), right),
                 (128, 32768, representative(2, point(1 << 300), left[2]), right),
                 (128, 32768, *operands(3))]
        for bits, cap, first, second in cases:
            actual, expected = arithmetic(bits=bits, cap=cap), arithmetic(bits=bits, cap=cap)
            with ordinary():
                result = expected.multiply(first, second)
            with self.subTest(bits=bits, cap=cap, first=first):
                self.assertEqual(actual.multiply(first, second), result)
                self.assertEqual(actual.a.work.operations, expected.a.work.operations)
                self.assertEqual(actual.a.cache, expected.a.cache)

    def test_callback_only_arithmetic_keeps_its_original_path(self):
        counts = [0, 0]
        outcomes = []
        for index in (0, 1):
            def tick():
                counts[index] += 1
            ops = _PoseArithmetic(_Arithmetic(check=tick))
            with ordinary() if index == 0 else nullcontext():
                outcomes.append(ops.multiply(*operands(1)))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(counts[0], counts[1])

    def test_large_operand_and_intermediate_failures_keep_the_original_location(self):
        for huge in (F(1 << 33000), F(1, 1 << 33000), F(1 << 32760), F(1, 1 << 32760)):
            left = representative(1, point(huge), point(3))
            right = representative(1, point(huge), point(-4))
            outcomes = []
            for optimized in (False, True):
                ops = arithmetic()
                with nullcontext() if optimized else ordinary():
                    with self.assertRaises(ReferenceError) as caught:
                        ops.multiply(left, right)
                outcomes.append((caught.exception.code, str(caught.exception), ops.a.work.operations))
            self.assertEqual(outcomes[0], outcomes[1])

    def test_every_remaining_callback_keeps_cancellation_identity_and_no_partial_entry(self):
        for axis in (1, 2):
            left, right = operands(axis)
            baseline = arithmetic()
            baseline.multiply(left, right)
            for fail_at in range(1, baseline.a.work.operations + 1):
                for marker in (RuntimeError("cancel sparse Hamilton product"),
                               ReferenceError("resource", "caller owns this refusal")):
                    ops, calls = arithmetic(), 0
                    def cancel():
                        nonlocal calls
                        calls += 1
                        if calls == fail_at:
                            ops.a.work.max_operand_bits = 64
                            raise marker
                    ops.a.work.external_check = cancel
                    with self.subTest(axis=axis, fail_at=fail_at, marker=type(marker)), \
                            self.assertRaises(type(marker)) as caught:
                        ops.multiply(left, right)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(ops.a.work.callback_error, marker)
                    self.assertEqual(ops.a.cache, {})

    def test_every_cap_change_replays_complete_hamilton_on_the_same_work(self):
        for axis in (1, 2):
            left, right = operands(axis)
            baseline = arithmetic()
            baseline.multiply(left, right)
            with ordinary():
                expected = arithmetic(cap=32767).multiply(left, right)
            for fail_at in range(1, baseline.a.work.operations + 1):
                ops, calls = arithmetic(), 0
                def narrow():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        ops.a.work.max_operand_bits = 32767
                ops.a.work.external_check = narrow
                with patch.object(ops.a, "total", wraps=ops.a.total) as totals:
                    result = ops.multiply(left, right)
                with self.subTest(axis=axis, fail_at=fail_at):
                    self.assertEqual(result, expected)
                    self.assertEqual(ops.a.work.max_operand_bits, 32767)
                    self.assertGreaterEqual(totals.call_count, 4)
                    self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))

    def test_each_too_small_live_cap_is_rejected_before_publication(self):
        for axis in (1, 2):
            baseline = arithmetic()
            baseline.multiply(*operands(axis))
            for fail_at in range(1, baseline.a.work.operations + 1):
                ops, calls = arithmetic(), 0
                def narrow():
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        ops.a.work.max_operand_bits = 64
                ops.a.work.external_check = narrow
                with self.subTest(axis=axis, fail_at=fail_at), self.assertRaises(ReferenceError) as caught:
                    ops.multiply(*operands(axis))
                self.assertEqual(caught.exception.code, "resource")
                self.assertEqual(ops.a.cache, {})

    def test_original_arithmetic_failure_is_not_retried_after_later_broadening(self):
        ops, calls, raised, broadened = arithmetic(), 0, [], []
        original = ops.a.mul
        def change_cap():
            nonlocal calls
            calls += 1
            if calls == 3:
                ops.a.work.max_operand_bits = 64
            elif calls > 3:
                broadened.append(True)
                ops.a.work.max_operand_bits = 32768
        def observe(*args):
            try:
                return original(*args)
            except ReferenceError as error:
                raised.append(error)
                raise
        ops.a.work.external_check = change_cap
        with patch.object(ops.a, "mul", side_effect=observe), self.assertRaises(ReferenceError) as caught:
            ops.multiply(*operands(2))
        self.assertEqual(len(raised), 1)
        self.assertIs(caught.exception, raised[0])
        self.assertEqual(broadened, [])
        self.assertEqual(ops.a.cache, {})

    def test_cache_hits_eviction_and_reentrant_completed_products_remain_bounded(self):
        for axis in (1, 2):
            ops = arithmetic()
            left, right = operands(axis)
            result = ops.multiply(left, right)
            cold = ops.a.work.operations
            before = ops.a.work.operations
            self.assertIs(ops.multiply(left, right), result)
            self.assertEqual(ops.a.work.operations - before, 2)
            for index in range(MAX_CACHE):
                ops.a.remember(("sparse-product-eviction", index), F(index))
            before = ops.a.work.operations
            self.assertEqual(ops.multiply(left, right), result)
            self.assertEqual(ops.a.work.operations - before, cold)
            self.assertEqual(len(ops.a.cache), MAX_CACHE)
            ops, calls, nested = arithmetic(), 0, []
            def reenter():
                nonlocal calls
                calls += 1
                if calls == cold:
                    nested.append(ops.multiply(*operands(3 - axis)))
            ops.a.work.external_check = reenter
            self.assertEqual(ops.multiply(left, right), result)
            with ordinary():
                self.assertEqual(nested, [arithmetic().multiply(*operands(3 - axis))])
            self.assertEqual(len(ops.a.cache), 2)

    def test_character_nonzero_head_compositions_keep_exact_cold_and_advanced_cells(self):
        outcomes = []
        for optimized in (False, True):
            with nullcontext() if optimized else ordinary():
                reference, _ = reference_case("P11", F(1, 4))
                context, carriers = object(), tuple(reference.model.objects)
                before = reference.a.work.operations
                with reference.recording_source_batch(context):
                    values = [reference.recording_pose_enclosures(
                        carriers, clock, recording_context=context)
                        for clock in (F(1, 16), F(1, 8), F(3, 16), F(1, 4))]
                outcomes.append((values, reference.a.work.operations - before))
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])
        print(f"P11 four independent pose maps: full={outcomes[0][1]}, sparse={outcomes[1][1]}")

    def test_actual_character_prefix_bytes_reports_and_observed_product_costs(self):
        outcomes = []
        original_multiply = _PoseArithmetic.multiply
        original_sparse = _PoseArithmetic._sparse_cartesian_multiply
        for optimized in (False, True):
            counts = {"calls": 0, "operations": 0, "sparse_misses": 0}
            def observe(ops, left, right):
                before = ops.a.work.operations
                result = original_multiply(ops, left, right)
                counts["calls"] += 1
                counts["operations"] += ops.a.work.operations - before
                return result
            def select(ops, left, right, key):
                result = original_sparse(ops, left, right, key) if optimized else None
                if result is not None:
                    counts["sparse_misses"] += 1
                return result
            compiler = compile_construction(source_case("P11"))
            with patch.object(_PoseArithmetic, "multiply", observe), \
                    patch.object(_PoseArithmetic, "_sparse_cartesian_multiply", select):
                result = export_glb(compiler.model,
                    options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertEqual(compiler.reach_work.max_operations, 100000)
            outcomes.append((result.data, result.report["validation"], compiler.budget.operations, counts))
        self.assertEqual(outcomes[0][:2], outcomes[1][:2])
        self.assertGreater(outcomes[1][3]["sparse_misses"], 0)
        self.assertEqual(outcomes[0][3]["calls"], outcomes[1][3]["calls"])
        saving = outcomes[0][2] - outcomes[1][2]
        self.assertGreater(saving, 0)
        self.assertEqual(saving, outcomes[0][3]["operations"] - outcomes[1][3]["operations"])
        print(f"P11 actual prefix full={outcomes[0][2]} {outcomes[0][3]}, "
              f"sparse={outcomes[1][2]} {outcomes[1][3]}")


if __name__ == "__main__":
    unittest.main()
