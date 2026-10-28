"""Independent exact examples and cancellation checks for pure pose reuse."""
from fractions import Fraction as F
import math
import unittest
from dataclasses import replace
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import PRODUCT_ERROR, ZERO, PoseValue, ReachPoseOps, RotationValue


class ReachPoseReuseTests(unittest.TestCase):
    def test_zero_rate_domain_checks_precede_warm_composition_reuse(self):
        for parent_position in (ZERO, (F(1), F(2), F(3))):
            for owner in ("parent", "local"):
                for field in ("exact_velocity", "exact_omega"):
                    for invalid in ((False, False, False), (F(0), F(0))):
                        with self.subTest(position=parent_position, owner=owner,
                                          field=field, invalid=invalid):
                            ops = ReachPoseOps(ReachExecutionWork())
                            parent, local = ops.make(parent_position), ops.make((4, 5, 6))
                            ops.compose(parent, local)
                            if owner == "parent":
                                parent = replace(parent, **{field: invalid})
                            else:
                                local = replace(local, **{field: invalid})
                            with self.assertRaises(ReachAdmissionError):
                                ops.compose(parent, local)

    def test_equal_zero_rate_values_need_no_identity_alias_to_prove_stationarity(self):
        ops = ReachPoseOps(ReachExecutionWork())
        first, second = ops.make((1, 2, 3)), ops.make((4, 5, 6))
        zeros = lambda: tuple(F(0) for _ in range(3))
        first = replace(first, exact_velocity=zeros(), exact_omega=zeros())
        second = replace(second, exact_velocity=zeros(), exact_omega=zeros())
        self.assertIsNot(first.exact_velocity, ZERO)
        with patch.object(ops, "cross", side_effect=AssertionError("recomputed proved zero rates")):
            result = ops.compose(first, second)
        self.assertEqual(result.exact_position, (F(5), F(7), F(9)))
        self.assertEqual(result.exact_velocity, ZERO)
        self.assertEqual(result.exact_omega, ZERO)
        moving = replace(first, exact_omega=(F(0), F(0), F(2)))
        self.assertEqual(ops.compose(moving, second).exact_velocity, (F(-10), F(8), F(0)))

    def test_reused_spin_axis_preserves_complete_plan_operands_and_guards(self):
        warm = ReachPoseOps(ReachExecutionWork())
        plan = warm.spin_plan((1, 2, 3), F(10))
        warm.spin_rotation((1, 2, 3), F(1, 7), phase_plan=plan)
        for elapsed in (F(2, 7), F(-3, 7)):
            cold = ReachPoseOps(ReachExecutionWork())
            expected = cold.spin_rotation((1, 2, 3), elapsed, phase_plan=plan)
            actual = warm.spin_rotation((1, 2, 3), elapsed, phase_plan=plan)
            self.assertEqual(actual, expected)
        with self.assertRaises(ReachAdmissionError):
            warm.spin_rotation((1, 2, 4), F(1, 7), phase_plan=plan)
        with self.assertRaises(ReachAdmissionError):
            warm.spin_rotation((1, 2, 3), F(11), phase_plan=plan)
        marker = RuntimeError("cancel warm source spin")
        with patch.object(warm.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                warm.spin_rotation((1, 2, 3), F(1, 7), phase_plan=plan)
        self.assertIs(caught.exception, marker)
        self.assertIs(warm.work.callback_error, marker)

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
        with patch.object(ops, "_multiply_uncached", side_effect=AssertionError("recomputed identical components")):
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
            # A one-axis factor entry retains its last vector result. Vary
            # the actual quaternion too so this still forces distinct keys
            # past the unchanged two-entry capacity.
            varying = RotationValue((F(1), F(0), F(i, 16), F(0)))
            ops.rotate(varying, (F(i), F(2), F(3)))
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

    def test_zero_local_derivatives_preserve_independent_spatial_formulas_and_grid(self):
        def grid(values):
            return tuple(F(round(value * (1 << 96)), 1 << 96) for value in values)
        def rotate(q, vector):
            w, x, y, z = q
            d = sum(value * value for value in q)
            rows = ((d - 2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
                    (2*(x*y+w*z), d - 2*(x*x+z*z), 2*(y*z-w*x)),
                    (2*(x*z-w*y), 2*(y*z+w*x), d - 2*(x*x+y*y)))
            return grid(tuple(sum(a*b for a, b in zip(row, vector)) / d for row in rows))
        def cross(a, b):
            return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
        rotations = ((F(1), F(0), F(0), F(0)), (F(1, 3), F(-2, 7), F(1, 11), F(3, 13)))
        rates = ((F(1, 3), F(3, 1 << 97), F(-1, 1 << 1074)),
                 (F(0), F(-3, 1 << 97), F(2, 7)))
        for q in rotations:
            for position in (ZERO, (F(1, 3), F(-2, 5), F(7, 11))):
                for parent_omega in (rates[1], ZERO):
                    for local_velocity, local_omega in ((ZERO, ZERO), (ZERO, rates[0]), (rates[1], ZERO)):
                        with self.subTest(q=q, position=position, local_velocity=local_velocity, local_omega=local_omega, parent_omega=parent_omega):
                            ops = ReachPoseOps(ReachExecutionWork())
                            parent = PoseValue((F(2), F(3), F(4)), RotationValue(q, F(1, 1024)),
                                               rates[0], parent_omega, F(1, 4096), ops)
                            local = PoseValue(position, RotationValue((F(1), F(0), F(1), F(0)), F(1, 2048)),
                                              local_velocity, local_omega, F(1, 8192), ops)
                            offset = rotate(q, position)
                            inherited = cross(parent.exact_omega, offset)
                            rotated_linear, rotated_angular = rotate(q, local_velocity), rotate(q, local_omega)
                            expected_linear = grid(tuple(a+b+c for a, b, c in
                                                         zip(parent.exact_velocity, inherited, rotated_linear)))
                            expected_angular = grid(tuple(a+b for a, b in zip(parent.exact_omega, rotated_angular)))
                            result = ops.compose(parent, local)
                            self.assertEqual(result.exact_position, grid(tuple(a+b for a, b in zip(parent.exact_position, offset))))
                            self.assertEqual(result.exact_velocity, expected_linear)
                            self.assertEqual(result.exact_omega, expected_angular)
                            self.assertEqual(result.position_error_m, F(3, 8192)
                                             + sum(map(abs, position)) * F(1, 1024) + F(1, 1 << 95))
                            self.assertEqual(result.rotation.error_rad, F(3, 2048) + PRODUCT_ERROR)
                            self.assertEqual(ops.work.counts.get("composition_derivative_zero_check"), 1)

    def test_zero_local_derivative_shortcuts_keep_dimension_domain_and_width_guards(self):
        for field in ("velocity", "omega"):
            for malformed in ((F(1), F(2)), (True, 0, 0), (F(1 << 512), F(0), F(0))):
                with self.subTest(field=field, malformed=malformed):
                    ops = ReachPoseOps(ReachExecutionWork(max_operand_bits=512))
                    valid = ops.identity()
                    parent = PoseValue(valid.exact_position, valid.rotation,
                                       malformed if field == "velocity" else (F(1, 3), F(0), F(0)),
                                       malformed if field == "omega" else (F(1, 7), F(0), F(0)), F(0), ops)
                    with self.assertRaises(ReachAdmissionError):
                        ops.compose(parent, valid)
                    self.assertFalse(any("relative_composition" in key for key in ops.work._cache))

    def test_zero_local_derivative_cancellation_precedes_relative_result_publication(self):
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        parent = ops.make(velocity=(F(1, 3), 0, 0), omega=(0, F(3, 1 << 97), 0))
        local = ops.identity()
        marker = RuntimeError("cancel reduced spatial derivatives")
        def check():
            if work.counts.get("composition_derivative_zero_check", 0):
                raise marker
        work.external_check = check
        with self.assertRaises(RuntimeError) as raised:
            ops.compose(parent, local)
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertFalse(any("relative_composition" in key for key in work._cache))
        self.assertEqual(work.counts.get("composition_derivative_zero_check"), 1)

    def test_mixed_zero_components_preserve_exact_sums_and_final_grid_ties(self):
        pairs = (
            ((F(0), F(1, 3), F(3, 1 << 97)), (F(2, 7), F(0), F(-1, 1 << 97))),
            ((F(-5, 11), F(0), F(1, 1 << 1075)), (F(5, 11), F(3, 1 << 97), F(0))),
            ((F(0), F(-3, 1 << 97), F(7, 13)), (F(-1, 1 << 1075), F(0), F(0))),
        )
        for a, b in pairs:
            with self.subTest(a=a, b=b):
                ops = ReachPoseOps(ReachExecutionWork())
                expected = tuple(x + y for x, y in zip(a, b))
                with patch.object(ops, "_op", wraps=ops._op) as arithmetic:
                    actual = ops.add(a, b)
                self.assertEqual(actual, expected)
                self.assertEqual(ops._rounded_vector(actual),
                                 tuple(F(round(value * (1 << 96)), 1 << 96) for value in expected))
                self.assertEqual(arithmetic.call_count, sum(bool(x) and bool(y) for x, y in zip(a, b)))
                self.assertTrue(all(call.args[0] and call.args[1] and call.args[2] == "add"
                                    for call in arithmetic.call_args_list))
                self.assertEqual(ops.work.counts["pose_add_zero_check"], 1)

    def test_mixed_zero_components_keep_public_vector_guards_and_cancellation(self):
        for malformed in ((F(1), F(0)), (F(0), True, F(0)), (F(0), F(1 << 512), F(0))):
            with self.subTest(malformed=malformed):
                ops = ReachPoseOps(ReachExecutionWork(max_operand_bits=512))
                with self.assertRaises(ReachAdmissionError):
                    ops.add((F(1), F(0), F(0)), malformed)
                self.assertNotIn("pose_add_zero_check", ops.work.counts)
        work = ReachExecutionWork()
        ops = ReachPoseOps(work)
        marker = RuntimeError("cancel before mixed zero identity decision")
        def check():
            if work.counts.get("pose_vector_domain", 0) == 2:
                raise marker
        work.external_check = check
        with self.assertRaises(RuntimeError) as raised:
            ops.add((F(1), F(0), F(0)), (F(0), F(2), F(0)))
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertNotIn("pose_add_zero_check", work.counts)

    def test_warm_composition_zero_errors_keep_each_callers_exact_bound(self):
        ops = ReachPoseOps(ReachExecutionWork())
        rotation = RotationValue((F(1), F(0), F(0), F(0)), F(1, 1024))
        local_position = (F(2), F(-3), F(4))
        for parent_error, local_error in ((F(0), F(0)), (F(1, 7), F(0)),
                                           (F(0), F(1, 11)), (F(1, 7), F(1, 11))):
            with self.subTest(parent_error=parent_error, local_error=local_error):
                parent = PoseValue((F(5), F(6), F(7)), rotation, ZERO, ZERO, parent_error, ops)
                local = PoseValue(local_position, RotationValue((F(1), F(0), F(0), F(0))),
                                  ZERO, ZERO, local_error, ops)
                warm = ops.compose(parent, local)
                translated = PoseValue((F(50), F(60), F(70)), rotation, ZERO, ZERO, parent_error, ops)
                with patch.object(ops, "_op", wraps=ops._op) as arithmetic:
                    result = ops.compose(translated, local)
                expected = parent_error + local_error + F(9, 1024) + F(1, 1 << 95)
                self.assertEqual(warm.position_error_m, expected)
                self.assertEqual(result.position_error_m, expected)
                self.assertEqual(result.exact_position, (F(52), F(57), F(74)))
                self.assertEqual(result.exact_velocity, ZERO)
                self.assertEqual(result.exact_omega, ZERO)
                self.assertEqual(arithmetic.call_count, 4 + int(bool(parent_error) and bool(local_error)))
                self.assertEqual(arithmetic.call_args_list[-1].args,
                                 (parent_error + local_error, F(9, 1024) + F(1, 1 << 95), "add"))

    def test_warm_zero_error_composition_keeps_width_guard_and_final_cancellation(self):
        work = ReachExecutionWork(max_operand_bits=512)
        ops = ReachPoseOps(work)
        parent, local = ops.make((1, 2, 3)), ops.make((2, 0, 0))
        ops.compose(parent, local)
        for parent_error, local_error in ((F(1 << 512), F(0)), (F(0), F(1 << 512))):
            with self.subTest(parent_error=parent_error, local_error=local_error):
                changed_parent = PoseValue(parent.exact_position, parent.rotation, ZERO, ZERO, parent_error, ops)
                changed_local = PoseValue(local.exact_position, local.rotation, ZERO, ZERO, local_error, ops)
                with self.assertRaises(ReachAdmissionError) as raised:
                    ops.compose(changed_parent, changed_local)
                self.assertEqual(raised.exception.details["budget"], "numeric_operand_bits")
        grids = work.counts["pose_grid_check"]
        marker = RuntimeError("cancel final caller-specific offset allowance")
        def check():
            if work.counts.get("pose_grid_check", 0) > grids:
                raise marker
        work.external_check = check
        with self.assertRaises(RuntimeError) as raised:
            ops.compose(parent, local)
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
