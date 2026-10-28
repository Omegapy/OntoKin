"""Integer planar arithmetic preserves the existing exact grid and domains."""
from contextlib import ExitStack
from dataclasses import replace
from fractions import Fraction as F
from functools import partial
import random
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin import reach_export
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import (BITS, METHOD, PRODUCT_ERROR, ZERO, ReachPoseOps,
    RotationValue, _FractionPlanarFallback, _IntegerAxisFactors)
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


SCALE = 1 << BITS


def rotation(w, z, axis=2, *, error=F(0), frozen=None):
    values = [F(w), F(0), F(0), F(0)]
    values[axis + 1] = F(z)
    return RotationValue(tuple(values), error, frozen)


def ordinary(ops):
    context = ExitStack()
    context.enter_context(patch.object(ops, "_integer_planar_product", return_value=None))
    context.enter_context(patch.object(ops, "_integer_axis_rotate", return_value=None))
    return context


class ReachIntegerPlanarTests(unittest.TestCase):
    def test_hamilton_products_match_original_components_errors_and_signs(self):
        generator = random.Random(202610212045)
        pairs = [(F(0), F(1)), (F(1), F(1)), (F(-1), F(1)),
                 (F(1, 2), F(-1, 4)), (F(1, SCALE), F(1, 2)),
                 (F(SCALE - 1, SCALE), F(3, SCALE))]
        for bits in (1, 8, 52, 95, 96):
            pairs.extend((F(generator.randrange(-(1 << bits), (1 << bits) + 1), 1 << bits),
                          F(generator.randrange(1, (1 << bits) + 1), 1 << bits))
                         for _ in range(8))
        for first, second in zip(pairs, reversed(pairs)):
            for sign in (-1, 1):
                a = rotation(*first, error=F(1, 1 << 70), frozen=(1., 0., 0., 0.))
                b = rotation(sign * second[0], sign * second[1], error=F(1, 1 << 75))
                actual = ReachPoseOps(ReachExecutionWork())
                baseline = ReachPoseOps(ReachExecutionWork())
                with self.subTest(first=first, second=second, sign=sign):
                    with ordinary(baseline):
                        expected = baseline.multiply(a, b)
                    result = actual.multiply(a, b)
                    self.assertEqual(result, expected)
                    self.assertEqual(result.error_rad, a.error_rad + b.error_rad + PRODUCT_ERROR)
                    self.assertIsNone(result.frozen_projection)
                    self.assertGreater(actual.work.counts.get("planar_integer_mul", 0), 0)

    def test_product_halfway_rounding_keeps_even_parity_after_canonical_sign(self):
        b = rotation(F(1, 2), F(1, 2))
        for difference, upper, lower in ((3, 2, -1), (5, 3, -2)):
            a = rotation(F((1 << 95) + upper, SCALE), F((1 << 95) + lower, SCALE))
            for sign in (-1, 1):
                signed = rotation(sign * a.components[0], sign * a.components[3])
                actual = ReachPoseOps(ReachExecutionWork()).multiply(signed, b)
                baseline = ReachPoseOps(ReachExecutionWork())
                with ordinary(baseline):
                    expected = baseline.multiply(signed, b)
                with self.subTest(difference=difference, sign=sign):
                    self.assertEqual(actual, expected)
                    self.assertEqual(actual.components[0], F(2, SCALE))
                    self.assertGreater(actual.components[3], 0)

    def test_all_axes_sparse_and_dense_vectors_match_fraction_projection(self):
        generator = random.Random(202610212046)
        vectors = [(F(1), F(0), F(0)), (F(0), F(-3), F(0)),
                   (F(0), F(0), F(7, 8)), (F(2), F(-3), F(5)),
                   (F((1 << 256) - 1, SCALE), F(-3, SCALE), F(5, 8))]
        vectors.extend(tuple(F(generator.randrange(-SCALE, SCALE), SCALE) for _ in range(3))
                       for _ in range(12))
        pairs = ((F(3, 4), F(1, 8)), (F(-3, 4), F(1, 8)),
                 (F(0), F(-1)), (F(SCALE - 3, SCALE), F(17, SCALE)))
        for axis in range(3):
            for w, z in pairs:
                actual, baseline = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
                q = rotation(w, z, axis)
                for vector in vectors:
                    with self.subTest(axis=axis, pair=(w, z), vector=vector):
                        with ordinary(baseline):
                            expected = baseline.rotate(q, vector)
                        result = actual.rotate(q, vector)
                        self.assertEqual(result, expected)
                        self.assertEqual(result[axis], vector[axis])
                self.assertLessEqual(len(actual.work._cache), 256)

    def test_unsupported_grid_scale_and_vector_width_use_original_arithmetic(self):
        for q, vector in ((rotation(F(1, 3), F(2, 3)), (F(1), F(0), F(0))),
                          (rotation(F(1, 2), F(1, 1 << 97)), (F(1), F(0), F(0))),
                          (rotation(F(3), F(2)), (F(1), F(0), F(0))),
                          (rotation(F(3, 4), F(1, 8)), (F(1, 3), F(1), F(0))),
                          (rotation(F(3, 4), F(1, 8)), (F(1, 1 << 97), F(1), F(0))),
                          (rotation(F(3, 4), F(1, 8)), (F(1 << 256), F(1), F(0)))):
            actual, baseline = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
            with ordinary(baseline):
                expected_rotation = baseline.multiply(q, rotation(F(3, 4), F(1, 4)))
                expected_vector = baseline.rotate(q, vector)
            with self.subTest(q=q, vector=vector):
                self.assertEqual(actual.multiply(q, rotation(F(3, 4), F(1, 4))), expected_rotation)
                self.assertEqual(actual.rotate(q, vector), expected_vector)

    def test_factor_representation_replaces_the_existing_single_cache_entry(self):
        work = ReachExecutionWork(max_cache_entries=7)
        ops = ReachPoseOps(work)
        q = rotation(F(SCALE - 1, SCALE), F(3, SCALE))
        key = (METHOD, "axis_rotation_factors", q.components, work.max_operand_bits)
        ops.rotate(q, (F(1), F(0), F(0)))
        self.assertIs(type(work._cache[key]), _IntegerAxisFactors)
        # The original rational representation replaces the tagged form for
        # an off-grid vector; a later grid vector reuses that rational entry.
        baseline = ReachPoseOps(ReachExecutionWork())
        for vector in ((F(1, 3), F(0), F(0)), (F(2), F(0), F(0))):
            with ordinary(baseline):
                expected = baseline.rotate(q, vector)
            self.assertEqual(ops.rotate(q, vector), expected)
            self.assertIs(type(work._cache[key]), tuple)
            self.assertEqual(sum(k[1] == "axis_rotation_factors" for k in work._cache), 1)
        for index in range(20):
            ops.rotate(rotation(F(3, 4), F(index + 1, 64)), (F(1), F(0), F(0)))
        self.assertLessEqual(len(work._cache), work.max_cache_entries)
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_integer_products_and_rotations_reduce_charged_work(self):
        costs = []
        for enabled in (False, True):
            ops = ReachPoseOps(ReachExecutionWork())
            with ExitStack() as stack:
                if not enabled:
                    stack.enter_context(ordinary(ops))
                for index in range(24):
                    q = rotation(F((1 << 95) + 2 * index + 1, SCALE),
                                 F((1 << 94) + 2 * index + 3, SCALE))
                    r = rotation(F((1 << 95) + 2 * index + 5, SCALE),
                                 F((1 << 93) + 2 * index + 7, SCALE))
                    ops.multiply(q, r)
                    ops.rotate(q, (F(1), F(0), F(0)))
                    ops.rotate(q, (F(2), F(0), F(0)))
                costs.append(ops.work.operations)
            self.assertLessEqual(len(ops.work._cache), 256)
            self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))
        self.assertLess(costs[1], costs[0])

    def test_lower_caps_retain_original_values_and_precise_rejections(self):
        q = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE))
        r = rotation(F(3, 4), F(1, 8))
        for cap in (64, 96, 128, 192, 256, 512, 1024, 4096):
            for method, arguments in (("multiply", (q, r)), ("rotate", (q, (F(1), F(2), F(3))))):
                outcomes = []
                for enabled in (False, True):
                    ops = ReachPoseOps(ReachExecutionWork(max_operand_bits=cap))
                    try:
                        with ExitStack() as stack:
                            if not enabled:
                                stack.enter_context(ordinary(ops))
                            outcomes.append(("returned", getattr(ops, method)(*arguments)))
                    except ReachAdmissionError as error:
                        outcomes.append(("failed", error.reach_code, error.details))
                with self.subTest(cap=cap, method=method):
                    self.assertEqual(outcomes[0], outcomes[1])

    def test_warm_cap_narrowing_rejects_the_original_intermediate_width(self):
        q = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE))
        for method, arguments in (("multiply", (q, q)), ("rotate", (q, (F(1), F(0), F(0))))):
            ops = ReachPoseOps(ReachExecutionWork())
            getattr(ops, method)(*arguments)
            ops.work.max_operand_bits = 128
            with self.subTest(method=method), self.assertRaises(ReachAdmissionError) as caught:
                getattr(ops, method)(*arguments)
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_callback_cap_changes_at_arithmetic_lookup_and_insert_restart_safely(self):
        q = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE))
        for method, arguments in (("multiply", (q, q)), ("rotate", (q, (F(1), F(0), F(0))))):
            for checkpoint in ("planar_integer_mul", "planar_integer_round", "cache_insert", "cache_promote"):
                ops = ReachPoseOps(ReachExecutionWork())
                if checkpoint == "cache_promote":
                    getattr(ops, method)(*arguments)
                charge = ops.work.charge
                def narrowing(kind="checkpoint", amount=1):
                    if kind == checkpoint:
                        ops.work.external_check = lambda: setattr(ops.work, "max_operand_bits", 128)
                    return charge(kind, amount)
                with self.subTest(method=method, checkpoint=checkpoint), \
                        patch.object(ops.work, "charge", side_effect=narrowing):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        getattr(ops, method)(*arguments)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                self.assertLessEqual(len(ops.work._cache), 256)

    def test_raw_rotation_normalization_restarts_from_original_operands_after_cap_change(self):
        raw = (F(3 << 200), F(0), F(0), F(1 << 200))
        for method, arguments in (("multiply", (raw, rotation(F(3, 4), F(1, 8)))),
                                  ("rotate", (raw, (F(1), F(0), F(0))))):
            ops = ReachPoseOps(ReachExecutionWork())
            # The normalized result is small enough for cap128, but the raw
            # input is not. A changed cap cannot hide that original domain.
            canonical = ops._rotation(raw)
            self.assertLessEqual(max(max(value.numerator.bit_length(), value.denominator.bit_length())
                                     for value in canonical.components), 128)
            charge = ops.work.charge
            def narrowing(kind="checkpoint", amount=1):
                if kind == "cache_promote":
                    ops.work.external_check = lambda: setattr(ops.work, "max_operand_bits", 128)
                return charge(kind, amount)
            with self.subTest(method=method), patch.object(ops.work, "charge", side_effect=narrowing):
                with self.assertRaises(ReachAdmissionError) as caught:
                    getattr(ops, method)(*arguments)
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
            self.assertEqual(caught.exception.details["limit"], 128)
            self.assertGreater(caught.exception.details["consumed"], 200)

    def test_narrowed_publication_cannot_reuse_broad_normalization_or_general_rows(self):
        raw = (F((1 << 119) + 1, (1 << 120) + 1),) * 4
        cases = (("multiply", (raw, rotation(F(1), F(0)))),
                 ("rotate", (raw, (F(1), F(0), F(0)))),
                 ("rotate", (RotationValue((F(1, 1 << 64),) * 4),
                             (F(1), F(0), F(0)))))
        for method, arguments in cases:
            baseline = ReachPoseOps(ReachExecutionWork(max_operand_bits=128))
            with ordinary(baseline), self.assertRaises(ReachAdmissionError) as expected:
                getattr(baseline, method)(*arguments)
            ops = ReachPoseOps(ReachExecutionWork())
            charge = ops.work.charge
            def narrowing(kind="checkpoint", amount=1):
                if kind == "cache_insert":
                    ops.work.external_check = lambda: setattr(ops.work, "max_operand_bits", 128)
                return charge(kind, amount)
            with self.subTest(method=method, argument_type=type(arguments[0]).__name__), \
                    patch.object(ops.work, "charge", side_effect=narrowing):
                with self.assertRaises(ReachAdmissionError) as caught:
                    getattr(ops, method)(*arguments)
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
            self.assertEqual(caught.exception.details["limit"], 128)
            self.assertEqual(caught.exception.details, expected.exception.details)

    def test_cancellation_preserves_the_actual_callback_exception_and_cache(self):
        q = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE))
        for marker in (RuntimeError("cancel integer planar product"),
                       _FractionPlanarFallback("external exception with the internal type")):
            for method, arguments in (("multiply", (q, q)), ("rotate", (q, (F(1), F(0), F(0))))):
                ops = ReachPoseOps(ReachExecutionWork())
                before = dict(ops.work._cache)
                charge = ops.work.charge
                def cancelled(kind="checkpoint", amount=1):
                    if kind == "planar_integer_mul":
                        ops.work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return charge(kind, amount)
                with patch.object(ops.work, "charge", side_effect=cancelled):
                    with self.assertRaises(type(marker)) as caught:
                        getattr(ops, method)(*arguments)
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.work.callback_error, marker)
                self.assertEqual(dict(ops.work._cache), before)

    def test_warm_results_keep_current_vector_domains_and_rotation_allowances(self):
        ops = ReachPoseOps(ReachExecutionWork())
        q = rotation(F(3, 4), F(1, 8), error=F(1, 1 << 70))
        first = ops.multiply(q, q)
        changed = replace(q, error_rad=F(1, 1 << 65))
        second = ops.multiply(changed, q)
        self.assertEqual(first.components, second.components)
        self.assertEqual(second.error_rad - first.error_rad, changed.error_rad - q.error_rad)
        ops.rotate(q, (F(1), F(0), F(0)))
        for invalid in ((True, 0, 0), (float("inf"), 0, 0), (F(1), F(0)),
                        (F(1 << 32768), F(0), F(0))):
            with self.subTest(invalid_type=type(invalid[0]).__name__), self.assertRaises(ReachAdmissionError):
                ops.rotate(q, invalid)
        self.assertEqual(ops.rotate(q, ZERO), ZERO)

    def test_actual_recurrence_recording_remains_byte_identical(self):
        outputs = []
        original_sampling = reach_export._sample_recording_nodes
        for enabled in (False, True):
            with ExitStack() as stack:
                # Compare the exact recurrence with and without its integer
                # factorization; the native algorithm has separate bounds.
                stack.enter_context(patch.object(reach_export, "_sample_recording_nodes",
                    partial(original_sampling, allow_fast=False)))
                if not enabled:
                    stack.enter_context(patch.object(ReachPoseOps, "_integer_planar_product", return_value=None))
                    stack.enter_context(patch.object(ReachPoseOps, "_integer_axis_rotate", return_value=None))
                compiler = compile_construction(source_case("P01"))
                result = export_glb(compiler.model,
                    options=ExportOptions(end=F(1, 4), fps=12, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertGreater(compiler.reach_work.counts.get("recording_rotation_step", 0), 0)
            self.assertLessEqual(compiler.budget.operations, 100000)
            outputs.append(result.data)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
