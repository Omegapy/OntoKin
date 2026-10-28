"""Completed residual scalars keep exact inputs, limits and source histories."""
from contextlib import nullcontext
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin import reach_kinematics as kinematics
from ontokin import reach_runtime
from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_export import reach_prefix_plan
from ontokin.reach_numeric import (
    MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork,
    exact, float_bits, rational, sqrt_rational_binary64,
)


def previous_residual(actual, target, *, work):
    """Retain the preceding complete scalar algorithm as a cost/domain oracle."""
    if len(actual) != 3 or len(target) != 3:
        raise ReachAdmissionError("reach_domain", "A residual requires two three-dimensional positions.")
    while True:
        cap = work.max_operand_bits
        operands = tuple((rational(a, work), rational(b, work)) for a, b in zip(actual, target))
        if work.max_operand_bits != cap:
            continue
        key = (kinematics.METHOD, "measured_residual_squared", cap, operands)
        result = work.lookup(key)
        if work.max_operand_bits != cap:
            continue
        if result is None:
            result = F(0)
            for a, b in operands:
                delta = exact(a, b, "sub", work)
                result = exact(result, exact(delta, delta, "mul", work), "add", work)
            if work.max_operand_bits != cap:
                continue
            work.remember(key, result)
        work.charge("residual_result_guard")
        work.guard(result)
        if work.max_operand_bits == cap:
            return result


def formula(actual, target):
    return sum(((F(a) - F(b)) ** 2 for a, b in zip(actual, target)), F(0))


class ReachResidualOperandTests(unittest.TestCase):
    def test_repeated_native_operands_keep_exact_squares_and_remove_six_decodes(self):
        samples = (((0.1, -2.0, 3.0), (0.3, 4.0, -5.0)),
                   ((-0.0, 0.0, 0.0), (0.0, -0.0, 0.0)),
                   ((float.fromhex("0x1p-1074"), 0.0, 1.0), (0.0, 0.0, 1.0)),
                   ((float.fromhex("0x1.fffffffffffffp+1023"), 1.0, 0.0), (1.0, 1.0, 0.0)))
        for actual, target in samples:
            with self.subTest(actual=actual):
                work = ReachExecutionWork()
                self.assertEqual(kinematics.measured_residual_squared(actual, target, work=work),
                                 formula(actual, target))
                decoded = work.counts["exact_decode"], work.counts["binary64_decode"]
                before = work.operations
                self.assertEqual(kinematics.measured_residual_squared(actual, target, work=work),
                                 formula(actual, target))
                self.assertEqual(decoded, (work.counts["exact_decode"], work.counts["binary64_decode"]))
                old = ReachExecutionWork()
                previous_residual(actual, target, work=old)
                old_before = old.operations
                previous_residual(actual, target, work=old)
                self.assertLess(work.operations - before, old.operations - old_before)
                self.assertEqual(work.operations, sum(work.counts.values()))
                self.assertEqual(work.max_operations, 100000)
                self.assertEqual(len(work._cache), 1)

    def test_every_native_operand_and_signed_zero_enters_the_complete_key(self):
        actual, target = (0.0, 1.0, 2.0), (3.0, 4.0, 5.0)
        work = ReachExecutionWork()
        variants = [(actual, target), ((-0.0, *actual[1:]), target)]
        for vector in range(2):
            for index in range(3):
                values = [actual, target]
                changed = list(values[vector])
                changed[index] += 0.25
                values[vector] = tuple(changed)
                variants.append(tuple(values))
        for a, b in variants:
            self.assertEqual(kinematics.measured_residual_squared(a, b, work=work), formula(a, b))
        self.assertEqual(len(work._cache), len(variants))
        keys = [key[-1] for key in work._cache]
        self.assertNotEqual(keys[0], keys[1])

    def test_mutable_mixed_and_narrow_calls_keep_original_arithmetic_and_counts(self):
        cases = [([0.1, 2.0, 3.0], (0.3, 2.0, 4.0), MAX_OPERAND_BITS),
                 ((0.1, F(3, 7), -2.0), (0.3, F(5, 11), 0.0), MAX_OPERAND_BITS),
                 ((1, 2, 3), (1, 2, 2), MAX_OPERAND_BITS),
                 ((1.0, 2.0, 3.0), (1.0, 2.0, 2.0), 2048)]
        for actual, target, cap in cases:
            with self.subTest(types=tuple(map(type, actual)), cap=cap):
                current = ReachExecutionWork(max_operand_bits=cap)
                original = ReachExecutionWork(max_operand_bits=cap)
                for _ in range(2):
                    self.assertEqual(kinematics.measured_residual_squared(actual, target, work=current),
                                     previous_residual(actual, target, work=original))
                self.assertEqual(current.counts, original.counts)
                self.assertEqual(tuple(current._cache.items()), tuple(original._cache.items()))

    def test_invalid_current_inputs_fail_before_any_cache_lookup(self):
        work = ReachExecutionWork()
        kinematics.measured_residual_squared((0.0,) * 3, (0.0,) * 3, work=work)
        for invalid in (False, float("nan"), float("inf"), F(1 << MAX_OPERAND_BITS)):
            for index in range(6):
                values = [0.0] * 6
                values[index] = invalid
                with self.subTest(type=type(invalid).__name__, index=index), \
                     patch.object(work, "lookup", wraps=work.lookup) as lookup:
                    with self.assertRaises(ReachAdmissionError):
                        kinematics.measured_residual_squared(tuple(values[:3]), tuple(values[3:]), work=work)
                    lookup.assert_not_called()

    def test_native_warm_hit_and_cold_publication_recheck_callback_narrowed_caps(self):
        actual, target = (1.0, 2.0, 3.0), (4.0, 5.0, 6.0)
        for stage in ("residual_operand_domain", "cache_lookup", "cache_promote",
                      "cache_insert", "residual_result_guard"):
            with self.subTest(stage=stage):
                work = ReachExecutionWork()
                if stage != "cache_insert":
                    kinematics.measured_residual_squared(actual, target, work=work)
                original = work.charge
                narrowed = False
                def charge(kind="checkpoint", amount=1):
                    nonlocal narrowed
                    result = original(kind, amount)
                    if kind == stage and not narrowed:
                        narrowed = True
                        work.max_operand_bits = 1
                    return result
                with patch.object(work, "charge", charge):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        kinematics.measured_residual_squared(actual, target, work=work)
                self.assertTrue(narrowed)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                if stage == "cache_insert":
                    self.assertFalse(any("measured_residual_native_v1" in key for key in work._cache))

    def test_new_admission_cannot_hide_decode_failure_by_later_cap_restoration(self):
        work = ReachExecutionWork()
        original = work.charge
        narrowed = restored = False
        def charge(kind="checkpoint", amount=1):
            nonlocal narrowed, restored
            if narrowed:
                restored = True
                work.max_operand_bits = MAX_OPERAND_BITS
            result = original(kind, amount)
            if kind == "residual_operand_domain":
                narrowed = True
                work.max_operand_bits = 1
            return result
        with patch.object(work, "charge", charge):
            with self.assertRaises(ReachAdmissionError):
                kinematics.measured_residual_squared((1.0,) * 3, (0.0,) * 3, work=work)
        self.assertTrue(narrowed)
        self.assertFalse(restored)
        self.assertFalse(work._cache)

    def test_cancellation_preserves_exception_identity_and_complete_prior_cache(self):
        for stage in ("residual_operand_domain", "cache_lookup", "cache_promote", "cache_insert"):
            with self.subTest(stage=stage):
                work = ReachExecutionWork()
                actual, target = (1.0, 2.0, 3.0), (4.0, 5.0, 6.0)
                if stage == "cache_promote":
                    kinematics.measured_residual_squared(actual, target, work=work)
                else:
                    work.remember(("unrelated",), F(7))
                before = tuple(work._cache.items())
                original = work.charge
                marker = RuntimeError("cancel completed residual reuse")
                def charge(kind="checkpoint", amount=1):
                    if kind == stage:
                        work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return original(kind, amount)
                with patch.object(work, "charge", charge):
                    with self.assertRaises(RuntimeError) as caught:
                        kinematics.measured_residual_squared(actual, target, work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(tuple(work._cache.items()), before)

    def test_reentrant_publication_keeps_nested_cache_work_without_partial_outer_result(self):
        work = ReachExecutionWork()
        original = work.charge
        nested = False
        def charge(kind="checkpoint", amount=1):
            nonlocal nested
            result = original(kind, amount)
            if kind == "cache_insert" and not nested:
                nested = True
                work.remember(("nested",), F(19))
            return result
        with patch.object(work, "charge", charge):
            result = kinematics.measured_residual_squared((1.0, 2.0, 3.0), (4.0, 5.0, 6.0), work=work)
        self.assertEqual(result, 27)
        self.assertEqual(tuple(work._cache.items()), ((("nested",), F(19)),))

    def test_eviction_keeps_bounded_complete_scalars_and_exact_reconstruction(self):
        work = ReachExecutionWork(max_cache_entries=2)
        for scalar in (1.0, 2.0, 3.0, 4.0, 1.0):
            actual, target = (scalar, 1.0, 2.0), (0.0, 3.0, 4.0)
            self.assertEqual(kinematics.measured_residual_squared(actual, target, work=work), formula(actual, target))
            self.assertLessEqual(len(work._cache), 2)
        self.assertGreater(work.counts["cache_evict"], 0)


class ReachRoundedResidualTests(unittest.TestCase):
    def test_complete_positive_scalars_keep_original_rounding_bits_with_less_work(self):
        halfway = F((1 << 53) + 1, 1 << 53)
        values = (F(1), F(2), F(3, 7), F(1, 1 << 1000), F((1 << 1000) - 1),
                  halfway * halfway, (halfway + F(1, 1 << 100)) ** 2)
        for value in values:
            with self.subTest(value_bits=(value.numerator.bit_length(), value.denominator.bit_length())):
                work = ReachExecutionWork()
                expected = sqrt_rational_binary64(value, work=ReachExecutionWork())
                self.assertEqual(float_bits(kinematics.rounded_sqrt(value, work=work)), float_bits(expected))
                before = work.operations
                sqrt_count = work.counts["integer_sqrt"]
                self.assertEqual(float_bits(kinematics.rounded_sqrt(value, work=work)), float_bits(expected))
                self.assertEqual(work.counts["integer_sqrt"], sqrt_count)
                direct = ReachExecutionWork()
                sqrt_rational_binary64(value, work=direct)
                self.assertLess(work.operations - before, direct.operations)
                self.assertEqual(len(work._cache), 1)

    def test_zero_negative_unusual_and_narrow_values_keep_original_paths(self):
        for value, cap in ((F(0), MAX_OPERAND_BITS), (F(-1), MAX_OPERAND_BITS),
                           (1, MAX_OPERAND_BITS), (F(1, 1 << 1100), MAX_OPERAND_BITS),
                           (F(2), 2048), (F(1 << 32768), MAX_OPERAND_BITS)):
            with self.subTest(value_type=type(value).__name__, cap=cap):
                outcomes, counts = [], []
                for method in (kinematics.rounded_sqrt, sqrt_rational_binary64):
                    work = ReachExecutionWork(max_operand_bits=cap)
                    try:
                        result = method(value, work=work)
                        outcomes.append(("returned", float_bits(result)))
                    except (ReachAdmissionError, ValueError) as error:
                        outcomes.append((type(error), str(error), getattr(error, "details", None)))
                    counts.append(work.counts)
                    self.assertFalse(work._cache)
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(counts[0], counts[1])

    def test_narrowed_hit_keeps_original_sqrt_prospective_failure(self):
        value = F(2)
        for stage in ("sqrt_result_domain", "cache_lookup", "cache_promote", "cache_insert"):
            with self.subTest(stage=stage):
                work = ReachExecutionWork()
                if stage != "cache_insert":
                    kinematics.rounded_sqrt(value, work=work)
                original = work.charge
                narrowed = False
                def charge(kind="checkpoint", amount=1):
                    nonlocal narrowed
                    result = original(kind, amount)
                    if kind == stage and not narrowed:
                        narrowed = True
                        work.max_operand_bits = 100
                    return result
                with patch.object(work, "charge", charge):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        kinematics.rounded_sqrt(value, work=work)
                expected = ReachExecutionWork(max_operand_bits=100)
                with self.assertRaises(ReachAdmissionError) as baseline:
                    sqrt_rational_binary64(value, work=expected)
                self.assertEqual(caught.exception.details, baseline.exception.details)

    def test_sqrt_admission_cannot_hide_failure_by_later_cap_restoration(self):
        work = ReachExecutionWork()
        original = work.charge
        narrowed = restored = False

        def charge(kind="checkpoint", amount=1):
            nonlocal narrowed, restored
            if narrowed:
                restored = True
                work.max_operand_bits = MAX_OPERAND_BITS
            result = original(kind, amount)
            if kind == "sqrt_result_domain":
                narrowed = True
                work.max_operand_bits = 100
            return result

        with patch.object(work, "charge", charge), self.assertRaises(ReachAdmissionError) as caught:
            kinematics.rounded_sqrt(F(2), work=work)
        expected = ReachExecutionWork(max_operand_bits=100)
        with self.assertRaises(ReachAdmissionError) as baseline:
            sqrt_rational_binary64(F(2), work=expected)
        self.assertEqual(caught.exception.details, baseline.exception.details)
        self.assertTrue(narrowed)
        self.assertFalse(restored)
        self.assertFalse(work._cache)

    def test_original_sqrt_error_is_not_retried_after_the_cap_changes(self):
        work = ReachExecutionWork()
        marker = ReachAdmissionError("reach_resource", "original square-root failure")

        def failed(value, *, work):
            work.max_operand_bits = 100
            raise marker

        with patch.object(kinematics, "sqrt_rational_binary64", side_effect=failed) as direct, \
                self.assertRaises(ReachAdmissionError) as caught:
            kinematics.rounded_sqrt(F(2), work=work)
        self.assertIs(caught.exception, marker)
        self.assertEqual(direct.call_count, 1)
        self.assertFalse(work._cache)

    def test_cancelled_sqrt_publication_and_warm_lookup_keep_original_exception(self):
        for stage in ("sqrt_result_domain", "cache_lookup", "cache_promote", "cache_insert"):
            with self.subTest(stage=stage):
                work = ReachExecutionWork()
                if stage == "cache_promote":
                    kinematics.rounded_sqrt(F(2), work=work)
                before = tuple(work._cache.items())
                marker = RuntimeError("cancel residual square root")
                original = work.charge
                def charge(kind="checkpoint", amount=1):
                    if kind == stage:
                        work.external_check = lambda: (_ for _ in ()).throw(marker)
                    return original(kind, amount)
                with patch.object(work, "charge", charge):
                    with self.assertRaises(RuntimeError) as caught:
                        kinematics.rounded_sqrt(F(2), work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(tuple(work._cache.items()), before)

    def test_sqrt_reentrant_admission_cannot_overwrite_newer_cache_generation(self):
        work = ReachExecutionWork(max_cache_entries=2)
        original = work.charge
        nested = False
        def charge(kind="checkpoint", amount=1):
            nonlocal nested
            result = original(kind, amount)
            if kind == "cache_insert" and not nested:
                nested = True
                work.remember(("nested_sqrt",), F(23))
            return result
        with patch.object(work, "charge", charge):
            result = kinematics.rounded_sqrt(F(2), work=work)
        self.assertEqual(float_bits(result), float_bits(sqrt_rational_binary64(F(2), work=ReachExecutionWork())))
        self.assertEqual(tuple(work._cache.items()), ((("nested_sqrt",), F(23)),))

    def test_all_p23_prefix_histories_and_phase_bounds_match_original_scalars(self):
        root = Path(__file__).resolve().parents[1]
        manifest = root / "docs/language-design/planar-reach-v0.1/p23.files.json"
        results, costs = [], []
        for previous in (False, True):
            built = compile_construction(load_file_manifest(manifest), level="constructed")
            before = built.budget.operations
            residual_patch = (patch.object(reach_runtime, "measured_residual_squared", previous_residual)
                              if previous else nullcontext())
            sqrt_patch = (patch.object(reach_runtime, "rounded_sqrt", sqrt_rational_binary64)
                          if previous else nullcontext())
            with residual_patch, sqrt_patch:
                plan = reach_prefix_plan(built.model, F(3), work=built.reach_work)
            results.append((plan.boundaries, plan.boundary_records,
                            tuple((phase.start, phase.end, phase.carriers, phase.source) for phase in plan.phases)))
            costs.append(built.budget.operations - before)
            self.assertLessEqual(built.budget.operations, 100000)
            self.assertLessEqual(len(built.reach_work._cache), 256)
        self.assertEqual(results[0], results[1])
        self.assertLess(costs[0], costs[1])


if __name__ == "__main__":
    unittest.main()
