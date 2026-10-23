"""Cartesian source products preserve the original complete Hamilton result."""
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction as F
import random
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, float_bits
from ontokin.reach_pose import (BITS, PRODUCT_ERROR, ReachPoseOps, RotationValue,
                               _FractionPlanarFallback)
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


SCALE = 1 << BITS
_PLANAR_PRODUCT = ReachPoseOps._integer_planar_product


def rotation(w, value, axis, *, error=F(0), frozen=None):
    components = [F(w), F(0), F(0), F(0)]
    components[axis + 1] = F(value)
    return RotationValue(tuple(components), error, frozen)


@contextmanager
def previous_products():
    """Keep the existing Z optimization and original generic X/Y equations."""
    def product(ops, first, second, error, *, axis=2):
        return (_PLANAR_PRODUCT(ops, first, second, error)
                if axis == 2 else None)
    with patch.object(ReachPoseOps, "_integer_planar_product", product):
        yield


def outcome(ops, first, second):
    try:
        return "returned", ops.multiply(first, second)
    except ReachAdmissionError as error:
        return "failed", error.reach_code, error.details
    except (AttributeError, TypeError) as error:
        # Malformed private scalar records keep the original helper's exact
        # Python rejection, rather than acquiring a new public coercion rule.
        return "failed", type(error).__name__, str(error)


class ReachSourceCartesianProductTests(unittest.TestCase):
    def test_signed_x_y_products_match_every_exact_component_and_allowance(self):
        generator = random.Random(202610231603)
        pairs = [(F(0), F(1)), (F(1), F(1)), (F(-1), F(1)),
                 (F(1, 2), F(-1, 4)), (F(1, SCALE), F(1, 2)),
                 (F(SCALE - 1, SCALE), F(3, SCALE))]
        for bits in (1, 8, 52, 95, 96):
            pairs.extend((F(generator.randrange(-(1 << bits), (1 << bits) + 1), 1 << bits),
                          F(generator.randrange(1, (1 << bits) + 1), 1 << bits))
                         for _ in range(8))
        for axis in (0, 1):
            for first, second in zip(pairs, reversed(pairs)):
                for sign in (-1, 1):
                    a = rotation(*first, axis, error=F(1, 1 << 70), frozen=(1., 0., 0., 0.))
                    b = rotation(sign * second[0], sign * second[1], axis, error=F(1, 1 << 75))
                    actual, control = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
                    with self.subTest(axis=axis, first=first, second=second, sign=sign):
                        with previous_products():
                            expected = control.multiply(a, b)
                        result = actual.multiply(a, b)
                        self.assertEqual(result, expected)
                        self.assertEqual(result.error_rad, a.error_rad + b.error_rad + PRODUCT_ERROR)
                        self.assertIsNone(result.frozen_projection)
                        self.assertEqual(tuple(map(float_bits, actual._unit_projection(result))),
                                         tuple(map(float_bits, control._unit_projection(expected))))
                        self.assertGreater(actual.work.counts.get("planar_integer_mul", 0), 0)
                        self.assertEqual(actual.work.counts.get("quaternion_signed_terms", 0), 0)

    def test_halfway_even_rounding_and_projective_sign_match_generic_equations(self):
        for axis in (0, 1):
            b = rotation(F(1, 2), F(1, 2), axis)
            for upper, lower in ((2, -1), (3, -2)):
                for sign in (-1, 1):
                    a = rotation(sign * F((1 << 95) + upper, SCALE),
                                 sign * F((1 << 95) + lower, SCALE), axis)
                    actual, control = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
                    with previous_products():
                        expected = control.multiply(a, b)
                    with self.subTest(axis=axis, upper=upper, sign=sign):
                        result = actual.multiply(a, b)
                        self.assertEqual(result, expected)
                        self.assertEqual(result.components[0], F(2, SCALE))
                        self.assertGreater(result.components[axis + 1], 0)

    def test_scalar_zero_and_signed_identity_operands_keep_original_behavior(self):
        for axis in (0, 1):
            q = rotation(F(3, 4), F(1, 8), axis)
            for scalar in (F(0), F(1), F(-1), F(1, 2), F(-1, 8), F(1, 3)):
                identity = rotation(scalar, F(0), axis)
                for a, b in ((q, identity), (identity, q)):
                    actual, control = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
                    with previous_products():
                        expected = outcome(control, a, b)
                    with self.subTest(axis=axis, scalar=scalar, left=a is identity):
                        self.assertEqual(outcome(actual, a, b), expected)

    def test_foreign_zeros_nonplanar_support_and_wide_inputs_keep_generic_path(self):
        class ForeignFraction(F):
            pass

        for axis in (0, 1):
            q = rotation(F(3, 4), F(1, 8), axis)
            zero_index = 2 if axis == 0 else 1
            foreign = list(q.components)
            foreign[zero_index] = ForeignFraction(0)
            uncertain = list(q.components)
            uncertain[zero_index] = F(1, 1 << 160)
            invalid = list(q.components)
            invalid[zero_index] = False
            specimens = (rotation(F(1, 3), F(2, 3), axis),
                         rotation(F(1, 2), F(1, 1 << 97), axis),
                         rotation(F(3), F(2), axis),
                         rotation(F(3, 4), F(1, 8), 1 - axis),
                         RotationValue(tuple(foreign)), RotationValue(tuple(uncertain)),
                         RotationValue(tuple(invalid)))
            for first in specimens:
                actual, control = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
                with previous_products():
                    expected = outcome(control, first, q)
                with self.subTest(axis=axis, first=first):
                    self.assertEqual(outcome(actual, first, q), expected)
                    self.assertEqual(actual.work.counts.get("planar_integer_mul", 0), 0)

    def test_lower_caps_keep_original_results_and_first_width_rejections(self):
        for axis in (0, 1):
            a = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE), axis)
            b = rotation(F(3, 4), F(1, 8), axis)
            for cap in (64, 96, 128, 192, 256, 512, 1024, 4096):
                actual = ReachPoseOps(ReachExecutionWork(max_operand_bits=cap))
                control = ReachPoseOps(ReachExecutionWork(max_operand_bits=cap))
                with previous_products():
                    expected = outcome(control, a, b)
                with self.subTest(axis=axis, cap=cap):
                    self.assertEqual(outcome(actual, a, b), expected)
                    self.assertEqual(actual.work.counts.get("planar_integer_domain", 0), 0)

    def test_warm_allowance_changes_eviction_and_narrowing_keep_live_inputs(self):
        for axis in (0, 1):
            ops = ReachPoseOps(ReachExecutionWork(max_cache_entries=3))
            q = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE), axis,
                         error=F(1, 1 << 70))
            first = ops.multiply(q, q)
            changed = replace(q, error_rad=F(1, 1 << 65))
            second = ops.multiply(changed, q)
            self.assertEqual(first.components, second.components)
            self.assertEqual(second.error_rad - first.error_rad, changed.error_rad - q.error_rad)
            for index in range(8):
                ops.multiply(q, rotation(F(3, 4), F(index + 1, 64), axis))
            self.assertLessEqual(len(ops.work._cache), 3)
            self.assertEqual(ops.multiply(q, q), first)
            ops.work.max_operand_bits = 128
            control = ReachPoseOps(ReachExecutionWork(max_operand_bits=128))
            with previous_products():
                expected = outcome(control, q, q)
            self.assertEqual(outcome(ops, q, q), expected)
            self.assertEqual(expected[0], "failed")

    def test_callback_narrowing_during_integer_work_and_publication_keeps_rejection(self):
        stages = ("planar_integer_domain", "planar_integer_mul", "planar_integer_round",
                  "planar_integer_sign", "cache_insert", "cache_promote")
        for axis in (0, 1):
            q = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE), axis)
            control = ReachPoseOps(ReachExecutionWork(max_operand_bits=128))
            with previous_products():
                expected = outcome(control, q, q)
            for stage in stages:
                ops = ReachPoseOps(ReachExecutionWork())
                if stage == "cache_promote":
                    ops.multiply(q, q)
                original = ops.work.charge
                changed = []
                def narrow(kind="checkpoint", amount=1):
                    result = original(kind, amount)
                    if kind == stage and not changed:
                        ops.work.max_operand_bits = 128
                        changed.append(True)
                    return result
                with self.subTest(axis=axis, stage=stage), patch.object(ops.work, "charge", narrow):
                    self.assertEqual(outcome(ops, q, q), expected)
                self.assertEqual(changed, [True])

    def test_external_cancellation_identity_and_empty_product_cache_are_preserved(self):
        for axis in (0, 1):
            q = rotation(F((1 << 95) + 1, SCALE), F((1 << 94) + 3, SCALE), axis)
            for stage in ("planar_integer_mul", "planar_integer_round", "planar_integer_sign"):
                for marker in (RuntimeError("cancel Cartesian source product"),
                               _FractionPlanarFallback("external fallback type")):
                    ops = ReachPoseOps(ReachExecutionWork())
                    original = ops.work.charge
                    def cancel(kind="checkpoint", amount=1):
                        if kind == stage:
                            ops.work.external_check = lambda: (_ for _ in ()).throw(marker)
                        return original(kind, amount)
                    with self.subTest(axis=axis, stage=stage, marker=type(marker)), \
                            patch.object(ops.work, "charge", cancel):
                        with self.assertRaises(type(marker)) as caught:
                            ops.multiply(q, q)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(ops.work.callback_error, marker)
                    self.assertEqual(dict(ops.work._cache), {})

    def test_replaced_private_rotation_cannot_change_the_captured_generic_operands(self):
        for axis in (0, 1):
            outcomes = []
            for enabled in (False, True):
                ops = ReachPoseOps(ReachExecutionWork())
                a = rotation(F(3, 4), F(1, 8), axis)
                b = rotation(F(1, 2), F(-1, 4), axis)
                original = ops.work.charge
                changed = []
                def replace_after_read(kind="checkpoint", amount=1):
                    result = original(kind, amount)
                    if kind == "quaternion_sparse_check" and not changed:
                        object.__setattr__(a, "components", rotation(F(1, 4), F(3, 4), axis).components)
                        changed.append(True)
                    return result
                with patch.object(ops.work, "charge", replace_after_read):
                    if enabled:
                        outcomes.append(ops._multiply_uncached(a, b))
                    else:
                        with previous_products():
                            outcomes.append(ops._multiply_uncached(a, b))
                self.assertEqual(changed, [True])
            self.assertEqual(outcomes[0], outcomes[1])

    def test_signed_axis_cursor_every_component_projection_and_allowance_match(self):
        angles = [F(index, 64) for index in range(24)]
        angles += angles[-1:] + list(reversed(angles[4:12])) + [F(19, 31), F(3, 4)]
        for axis in (0, 1):
            for sign in (-1, 1):
                vector = tuple(sign if index == axis else 0 for index in range(3))
                outputs, costs = [], []
                for enabled in (False, True):
                    ops, context = ReachPoseOps(ReachExecutionWork()), object()
                    def sample():
                        return [ops.recording_axis_rotation(vector, angle, context=context,
                            path="head", max_steps=128) for angle in angles]
                    if enabled:
                        values = sample()
                    else:
                        with previous_products():
                            values = sample()
                    outputs.append((values, tuple(tuple(map(float_bits, ops._unit_projection(q))) for q in values)))
                    costs.append(ops.work.operations)
                    self.assertLessEqual(len(ops.work._cache), 256)
                    self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))
                self.assertEqual(outputs[0], outputs[1])
                self.assertLess(costs[1], costs[0])

    def test_cancelled_x_y_cursor_step_keeps_the_last_complete_rotation(self):
        for axis in (0, 1):
            ops, context = ReachPoseOps(ReachExecutionWork()), object()
            vector = tuple(int(index == axis) for index in range(3))
            args = dict(context=context, path="head", max_steps=128)
            for angle in (F(0), F(1, 64)):
                ops.recording_axis_rotation(vector, angle, **args)
            key = next(key for key in ops.work._cache if "recording_rotation_cursor" in key)
            before = ops.work._cache[key]
            original = ops.work.charge
            marker = RuntimeError("cancel next Cartesian cursor")
            def cancel(kind="checkpoint", amount=1):
                if kind == "planar_integer_mul":
                    ops.work.external_check = lambda: (_ for _ in ()).throw(marker)
                return original(kind, amount)
            with patch.object(ops.work, "charge", cancel), self.assertRaises(RuntimeError) as caught:
                ops.recording_axis_rotation(vector, F(2, 64), **args)
            self.assertIs(caught.exception, marker)
            self.assertIs(ops.work.callback_error, marker)
            self.assertIs(ops.work._cache[key], before)

    def test_actual_p11_prefix_glb_is_identical_with_less_source_product_work(self):
        results = []
        for enabled in (False, True):
            compiler = compile_construction(source_case("P11"))
            def build():
                return export_glb(compiler.model,
                    options=ExportOptions(end=F(1, 4), fps=1, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            if enabled:
                artifact = build()
            else:
                with previous_products():
                    artifact = build()
            self.assertEqual(artifact.report["validation"]["status"], "passed")
            self.assertEqual(compiler.reach_work.max_operations, 100000)
            self.assertEqual(compiler.reach_work.max_operand_bits, 32768)
            self.assertEqual(compiler.reach_work.max_cache_entries, 256)
            self.assertLessEqual(len(compiler.reach_work._cache), 256)
            results.append((artifact.data, compiler.budget.operations,
                            compiler.reach_work.counts.get("quaternion_signed_terms", 0)))
        self.assertEqual(results[0][0], results[1][0])
        self.assertLess(results[1][1], results[0][1])
        self.assertLess(results[1][2], results[0][2])


if __name__ == "__main__":
    unittest.main()
