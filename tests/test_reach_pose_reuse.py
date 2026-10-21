"""Independent exact examples and cancellation checks for pure pose reuse."""
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import PRODUCT_ERROR, PoseValue, ReachPoseOps, RotationValue


class ReachPoseReuseTests(unittest.TestCase):
    def test_translated_moving_assemblies_reuse_rates_but_keep_distinct_positions(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        local = ops.make((2, 0, 0), (1, 0, 0, 1), (0, 1, 0), (0, 0, 2))
        parent = ops.make((5, 6, 7), velocity=(1, 0, 0), omega=(0, 0, 3))
        first = ops.compose(parent, local)
        self.assertEqual(first.exact_position, (F(7), F(6), F(7)))
        self.assertEqual(first.exact_velocity, (F(1), F(7), F(0)))
        self.assertEqual(first.exact_omega, (F(0), F(0), F(5)))
        translated = ops.make((50, 60, 70), velocity=(1, 0, 0), omega=(0, 0, 3))
        before = work.operations
        with patch.object(ops, "cross", side_effect=AssertionError("recomputed shared derivatives")):
            second = ops.compose(translated, local)
        self.assertIsNot(first, second)
        self.assertIsNot(first._projection, second._projection)
        self.assertEqual(second.exact_position, (F(52), F(60), F(70)))
        self.assertEqual(second.exact_velocity, first.exact_velocity)
        self.assertEqual(second.exact_omega, first.exact_omega)
        self.assertEqual(second.rotation, first.rotation)
        self.assertEqual(second.position_error_m, first.position_error_m)
        self.assertGreater(work.operations, before)
        changed_rate = ops.make((50, 60, 70), velocity=(2, 0, 0), omega=(0, 0, 3))
        self.assertEqual(ops.compose(changed_rate, local).exact_velocity, (F(2), F(7), F(0)))
        changed_local = ops.make((3, 0, 0), (1, 0, 0, 1), (0, 1, 0), (0, 0, 2))
        self.assertEqual(ops.compose(translated, changed_local).exact_velocity, (F(1), F(10), F(0)))

    def test_relative_composition_cache_keeps_error_and_position_guards(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        parent = ops.make(velocity=(1, 0, 0))
        local = ops.make((2, 0, 0))
        first = ops.compose(parent, local)
        changed = PoseValue(parent.exact_position, parent.rotation, parent.exact_velocity,
                            parent.exact_omega, F(1, 1024), ops)
        with patch.object(ops, "cross", side_effect=AssertionError("recomputed shared derivatives")):
            second = ops.compose(changed, local)
        self.assertEqual(second.position_error_m - first.position_error_m, F(1, 1024))
        oversized = PoseValue((F(1 << 32768), F(0), F(0)), parent.rotation,
                              parent.exact_velocity, parent.exact_omega, parent.position_error_m, ops)
        with self.assertRaises(ReachAdmissionError) as raised:
            ops.compose(oversized, local)
        self.assertEqual(raised.exception.details["budget"], "numeric_operand_bits")

    def test_stationary_translations_reuse_arithmetic_with_distinct_local_errors(self):
        ops = ReachPoseOps(ReachExecutionWork())
        first_parent = ops.make((1, 2, 3))
        second_parent = ops.make((4, 5, 6))
        local = ops.make((2, 0, 0))
        first = ops.compose(first_parent, local)
        changed_local = PoseValue(local.exact_position, local.rotation, local.exact_velocity,
                                 local.exact_omega, F(1, 2048), ops)
        with patch.object(ops, "cross", side_effect=AssertionError("recomputed stationary derivatives")):
            second = ops.compose(second_parent, changed_local)
        self.assertEqual(first.exact_position, (F(3), F(2), F(3)))
        self.assertEqual(second.exact_position, (F(6), F(5), F(6)))
        self.assertEqual(second.position_error_m - first.position_error_m, F(1, 2048))

    def test_composition_parent_position_keeps_numeric_domain_validation(self):
        ops = ReachPoseOps(ReachExecutionWork())
        base = ops.identity()
        local = ops.make((2, 0, 0))
        def parent(position):
            return PoseValue(position, base.rotation, base.exact_velocity,
                             base.exact_omega, base.position_error_m, ops)
        actual = ops.compose(parent((1.5, 2, -3)), local)
        self.assertEqual(actual.exact_position, (F(7, 2), F(2), F(-3)))
        self.assertTrue(all(type(value) is F for value in actual.exact_position))
        for position, code in (((True, 0, 0), "reach_domain"),
                               ((float("inf"), 0, 0), "reach_domain"),
                               ((1, 2), "reach_numeric")):
            with self.subTest(position=position):
                with self.assertRaises(ReachAdmissionError) as raised:
                    ops.compose(parent(position), local)
                self.assertEqual(raised.exception.reach_code, code)

    def test_relative_cache_rounds_each_parent_position_at_its_own_grid_tie(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        local = ops.make()
        first = ops.make((F(1, 1 << 97), 0, 0), velocity=(1, 0, 0))
        second = ops.make((F(3, 1 << 97), 0, 0), velocity=(1, 0, 0))
        self.assertEqual(ops.compose(first, local).exact_position, (F(0), F(0), F(0)))
        with patch.object(ops, "cross", side_effect=AssertionError("recomputed shared derivatives")):
            actual = ops.compose(second, local)
        self.assertEqual(actual.exact_position, (F(1, 1 << 95), F(0), F(0)))

    def test_hinge_reuse_preserves_exact_axis_slope_and_current_projection_owner(self):
        work = ReachExecutionWork()
        first_ops = ReachPoseOps(work)
        first = first_ops.hinge_pose((0, 0, 1), F(0), F(3, 2))
        self.assertEqual(first.exact_omega, (F(0), F(0), F(3, 2)))
        self.assertEqual(first.orientation, (1.0, 0.0, 0.0, 0.0))
        second_ops = ReachPoseOps(work)
        with patch.object(second_ops, "axis_rotation", side_effect=AssertionError("recomputed hinge pose")):
            again = second_ops.hinge_pose((F(0), F(0), F(1)), F(0), F(3, 2))
        self.assertEqual(again.exact_omega, first.exact_omega)
        self.assertEqual(again.rotation, first.rotation)
        self.assertIs(again._ops, second_ops)
        self.assertIsNot(again._projection, first._projection)
        self.assertEqual(second_ops.hinge_pose((0, 0, 1), 0, 0).exact_omega, (F(0),) * 3)
        self.assertEqual(second_ops.hinge_pose((0, 1, 0), 0, 2).exact_omega, (F(0), F(2), F(0)))
        with self.assertRaises(ReachAdmissionError):
            second_ops.hinge_pose((0, 0, 0), 0, 2)

    def test_relative_cache_reuses_only_the_offset_angle_error_term(self):
        ops = ReachPoseOps(ReachExecutionWork())
        parent = ops.make(orientation=RotationValue((F(1), F(0), F(0), F(0)), F(1, 8)),
                          velocity=(1, 0, 0))
        local = ops.make((2, -3, 4))
        first = ops.compose(parent, local)
        different = PoseValue((F(9), F(8), F(7)), parent.rotation,
                              parent.exact_velocity, parent.exact_omega, F(1, 16), ops)
        local_error = PoseValue(local.exact_position, local.rotation, local.exact_velocity,
                                local.exact_omega, F(1, 32), ops)
        with patch.object(ops, "_l1", side_effect=AssertionError("recomputed shared offset bound")):
            actual = ops.compose(different, local_error)
        self.assertEqual(actual.position_error_m - first.position_error_m, F(3, 32))
        self.assertEqual(first.position_error_m, F(9, 8) + F(1, 1 << 95))
        self.assertEqual(actual.exact_position, (F(11), F(5), F(11)))

    def test_vector_projection_reuses_exact_values_across_distinct_fields(self):
        ops = ReachPoseOps(ReachExecutionWork())
        values = (F(1, 3), -F(1, 10), F(3, 2))
        first = ops.make(position=values)
        expected = (float.fromhex("0x1.5555555555555p-2"),
                    -float.fromhex("0x1.999999999999ap-4"), 1.5)
        self.assertEqual(first.position, expected)
        second = ops.make(position=(9, 8, 7), velocity=values, omega=values)
        with patch("ontokin.reach_pose.round_binary64", side_effect=AssertionError("recomputed projection")):
            self.assertEqual(second.velocity, expected)
            self.assertEqual(second.omega, expected)
        self.assertIsNot(first._projection, second._projection)
        self.assertEqual(second.position, (9.0, 8.0, 7.0))

    def test_vector_projection_preserves_subnormal_ties_and_saved_public_bits(self):
        ops = ReachPoseOps(ReachExecutionWork())
        values = (F(1, 1 << 1075), F(3, 1 << 1075), -F(3, 1 << 1075))
        pose = ops.make(position=values)
        self.assertEqual(pose.position, (0.0, float.fromhex("0x0.0000000000002p-1022"),
                                        -float.fromhex("0x0.0000000000002p-1022")))
        saved = (-0.0, 0.0, -0.0)
        base = ops.make()
        materialized = PoseValue(base.exact_position, base.rotation, base.exact_velocity,
                                 base.exact_omega, base.position_error_m, ops, {"position": saved})
        self.assertIs(materialized.position, saved)
        self.assertEqual(tuple(math.copysign(1, value) for value in materialized.position), (-1, 1, -1))

    def test_vector_projection_failure_does_not_create_a_successful_cache_entry(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        overflow = ops.make(position=(F(1 << 1024), 0, 0))
        before = tuple(work._cache.items())
        for _ in range(2):
            with self.assertRaises(ReachAdmissionError) as raised:
                overflow.position
            self.assertEqual(raised.exception.reach_code, "reach_numeric")
            self.assertNotIn("position", overflow._projection)
            self.assertEqual(tuple(work._cache.items()), before)
        oversized = PoseValue((F(1 << 32768), F(0), F(0)), overflow.rotation,
                              overflow.exact_velocity, overflow.exact_omega, F(0), ops)
        with self.assertRaises(ReachAdmissionError) as raised:
            oversized.position
        self.assertEqual(raised.exception.details["budget"], "numeric_operand_bits")

    def test_literal_zero_projection_cancellation_does_not_publish(self):
        for field_name in ("position", "velocity", "omega"):
            with self.subTest(field=field_name):
                work = ReachExecutionWork()
                ops = ReachPoseOps(work)
                pose = ops.identity()
                before = tuple(work._cache.items())
                marker = RuntimeError("cancel before publishing literal zero")
                def cancel_after_lookup():
                    if work.counts.get("pose_projection_lookup", 0):
                        raise marker
                work.external_check = cancel_after_lookup
                with self.assertRaises(RuntimeError) as raised:
                    getattr(pose, field_name)
                self.assertIs(raised.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertNotIn(field_name, pose._projection)
                self.assertEqual(tuple(work._cache.items()), before)
                self.assertEqual(work.counts.get("pose_projection_lookup"), 1)
                self.assertNotIn("known_zero_vector_projection", work.counts)

    def test_product_reuse_preserves_noncommuting_order_and_error_allowances(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        a = RotationValue((F(1), F(1), F(0), F(0)), F(1, 1024))
        b = RotationValue((F(1), F(0), F(1), F(0)), F(1, 2048))
        product = ops.multiply(a, b)
        self.assertEqual(product.components, (F(1, 2),) * 4)
        self.assertEqual(product.error_rad, F(3, 2048) + PRODUCT_ERROR)
        self.assertIsNone(product.frozen_projection)
        before = work.operations
        with patch.object(ops, "_multiply_uncached", side_effect=AssertionError("recomputed product")):
            # Saved public projections are not mathematical product operands.
            frozen = RotationValue(a.components, a.error_rad, (0.0, 1.0, 0.0, 0.0))
            repeated = ops.multiply(frozen, b)
        self.assertEqual(repeated, product)
        self.assertGreater(work.operations, before)
        reverse = ops.multiply(b, a)
        self.assertEqual(reverse.components, (F(1, 2), F(1, 2), F(1, 2), F(-1, 2)))
        changed_error = ops.multiply(RotationValue(a.components, F(1, 512)), b)
        self.assertEqual(changed_error.components, product.components)
        self.assertEqual(changed_error.error_rad, F(5, 2048) + PRODUCT_ERROR)

    def test_rotated_vector_reuse_preserves_exact_inputs_and_own_error_accounting(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        quarter_turn = RotationValue((F(1), F(0), F(0), F(1)))
        vector = (F(2), F(3), F(4))
        expected = (F(-3), F(2), F(4))
        self.assertEqual(ops.rotate(quarter_turn, vector), expected)
        before = work.operations
        with patch.object(ops, "_rounded_vector", side_effect=AssertionError("recomputed vector")):
            changed_allowance = RotationValue(quarter_turn.components, F(1, 16), (1.0, 0.0, 0.0, 0.0))
            self.assertEqual(ops.rotate(changed_allowance, vector), expected)
        self.assertGreater(work.operations, before)
        self.assertEqual(ops.rotate(quarter_turn, (F(5), F(3), F(4))), (F(-3), F(5), F(4)))
        opposite = RotationValue((F(1), F(0), F(0), F(-1)))
        self.assertEqual(ops.rotate(opposite, vector), (F(3), F(-2), F(4)))
        # Pure rotation reuse cannot share pose error bounds between callers.
        child = ops.make(position=vector)
        one = ops.compose(ops.make(orientation=quarter_turn), child)
        two = ops.compose(ops.make(orientation=changed_allowance), child)
        self.assertEqual(one.exact_position, two.exact_position)
        self.assertEqual(two.position_error_m - one.position_error_m, F(9, 16))

    def test_eviction_retains_results_and_fixed_cache_capacity(self):
        work = ReachExecutionWork(max_cache_entries=2)
        ops = ReachPoseOps(work)
        a = RotationValue((F(1), F(1), F(0), F(0)))
        b = RotationValue((F(1), F(0), F(1), F(0)))
        first = ops.multiply(a, b)
        for i in range(1, 10):
            ops.rotate(b, (F(i), F(2), F(3)))
            self.assertLessEqual(work.record()["cache_entries"], 2)
        self.assertEqual(ops.multiply(a, b), first)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)
        self.assertEqual(sum(work.counts.values()), work.operations)

    def test_cached_product_and_vector_still_check_cancellation_without_mutation(self):
        for operation in ("product", "vector", "composition", "projection", "hinge"):
            with self.subTest(operation=operation):
                cancelled = False
                marker = RuntimeError("cancel pure pose lookup")
                def check():
                    if cancelled:
                        raise marker
                work = ReachExecutionWork(check=check)
                ops = ReachPoseOps(work)
                a = RotationValue((F(1), F(1), F(0), F(0)))
                b = RotationValue((F(1), F(0), F(1), F(0)))
                if operation == "product":
                    call = lambda: ops.multiply(a, b)
                elif operation == "vector":
                    call = lambda: ops.rotate(a, (F(2), F(3), F(4)))
                elif operation == "projection":
                    values = (F(1, 3), F(2, 7), F(5, 11))
                    pose = ops.make(position=values)
                    pose.position
                    call = lambda: ops._vector_projection(values)
                elif operation == "hinge":
                    call = lambda: ops.hinge_pose((0, 0, 1), F(1, 3), F(2, 7))
                else:
                    parent = ops.make(velocity=(1, 0, 0))
                    local = ops.make((2, 0, 0))
                    call = lambda: ops.compose(parent, local)
                call()
                before = tuple(work._cache.items())
                cancelled = True
                with self.assertRaises(RuntimeError) as raised:
                    call()
                self.assertIs(raised.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(tuple(work._cache.items()), before)


if __name__ == "__main__":
    unittest.main()
