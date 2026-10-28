"""Finite recording recurrences retain source coordinates and proved errors."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import (AXIS_ERROR, PRODUCT_ERROR, MAX_RECORDING_ROTATION_STEPS,
                               UNIT, ReachPoseOps)
from test_reach_pose import independent_oracle


def planar_matrix(rotation):
    w, x, y, z = rotation.components
    assert x == y == 0
    square = w * w + z * z
    return (w * w - z * z) / square, 2 * w * z / square


class ReachRecordingRotationTests(unittest.TestCase):
    def test_exact_rounded_coordinate_differences_match_independent_enclosures(self):
        oracle = independent_oracle()
        ops = ReachPoseOps(ReachExecutionWork())
        context = object()
        # These binary64 angles have varying reduced denominators and changes
        # of direction; the delta must be exact, without binary64 rerounding.
        values = [F(float((index - 19) / 37)) for index in range(48)]
        values += list(reversed(values[13:20]))
        for index, angle in enumerate(values):
            rotation = ops.recording_axis_rotation((0, 0, 1), angle,
                context=context, path="joint", max_steps=10000)
            expected = oracle.Context(192, oracle.Budget()).sincos_point(angle)
            cosine, sine = planar_matrix(rotation)
            allowance = (index + 1) * AXIS_ERROR + (2 * index + 1) * PRODUCT_ERROR
            self.assertLessEqual(rotation.error_rad, allowance)
            for actual, interval in zip((sine, cosine), expected):
                self.assertLessEqual(actual - allowance, interval.lo)
                self.assertGreaterEqual(actual + allowance, interval.hi)
        self.assertLessEqual(len(ops.work._cache), 256)
        self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))

    def test_spin_increment_matches_ideal_and_rechecks_current_plan(self):
        oracle = independent_oracle()
        ops = ReachPoseOps(ReachExecutionWork())
        omega = (F(0), F(0), F(7, 4))
        plan = ops.spin_plan(omega, F(2))
        context = object()
        for index in range(1, 33):
            elapsed = F(index, 32)
            rotation = ops.recording_advance_orientation(UNIT, omega, elapsed,
                context=context, path="root", max_steps=10000, phase_plan=plan)
            expected = oracle.Context(192, oracle.Budget()).sincos_point(omega[2] * elapsed)
            cosine, sine = planar_matrix(rotation)
            allowance = index * AXIS_ERROR + (2 * index + 1) * PRODUCT_ERROR
            self.assertLessEqual(rotation.error_rad, allowance)
            for actual, interval in zip((sine, cosine), expected):
                self.assertLessEqual(actual - allowance, interval.lo)
                self.assertGreaterEqual(actual + allowance, interval.hi)
        for changed_omega, elapsed in ((omega, F(3)), ((0, 0, 2), F(1))):
            with self.subTest(omega=changed_omega, elapsed=elapsed), self.assertRaises(ReachAdmissionError):
                ops.recording_advance_orientation(UNIT, changed_omega, elapsed,
                    context=context, path="root", max_steps=10000, phase_plan=plan)

    def test_recurring_steps_save_actual_work_without_a_separate_cache(self):
        recurring, direct = ReachPoseOps(ReachExecutionWork()), ReachPoseOps(ReachExecutionWork())
        context = object()
        for index in range(48):
            angle = F(index, 64)
            recurring.recording_axis_rotation((0, 0, 1), angle,
                context=context, path="joint", max_steps=10000)
            direct.axis_rotation((0, 0, 1), angle)
        self.assertLess(recurring.work.operations, direct.work.operations)
        self.assertLessEqual(len(recurring.work._cache), recurring.work.max_cache_entries)
        self.assertEqual(MAX_RECORDING_ROTATION_STEPS, 10000)

    def test_finite_step_limit_new_context_axis_and_eviction_reseed_directly(self):
        ops = ReachPoseOps(ReachExecutionWork())
        context = object()
        for index in range(4):
            actual = ops.recording_axis_rotation((0, 0, 1), F(index + 1, 11),
                context=context, path="joint", max_steps=3)
        self.assertEqual(actual, ops.axis_rotation((0, 0, 1), F(4, 11)))
        for changed_context, axis in ((object(), (0, 0, 1)), (context, (0, 1, 0))):
            actual = ops.recording_axis_rotation(axis, F(5, 11),
                context=changed_context, path="joint", max_steps=3)
            self.assertEqual(actual, ops.axis_rotation(axis, F(5, 11)))
        for index in range(256):
            ops.work.remember(("test eviction", index), index)
        actual = ops.recording_axis_rotation((0, 0, 1), F(6, 11),
            context=context, path="joint", max_steps=3)
        self.assertEqual(actual, ops.axis_rotation((0, 0, 1), F(6, 11)))

    def test_invalid_domains_and_lowered_cap_cannot_use_a_warm_cursor(self):
        ops = ReachPoseOps(ReachExecutionWork())
        context = object()
        ops.recording_axis_rotation((0, 0, 1), F(1, 2), context=context, path="joint", max_steps=10000)
        for axis, angle, steps in (((0, 0, 0), F(1, 2), 10000),
                                   ((0, 0, 1), False, 10000),
                                   ((0, 0, 1), float("nan"), 10000),
                                   ((0, 0, 1), F(3, 4), 10001),
                                   ((0, 0, 1), F(3, 4), True)):
            with self.subTest(axis=axis, angle=angle, steps=steps), self.assertRaises(ReachAdmissionError):
                ops.recording_axis_rotation(axis, angle, context=context, path="joint", max_steps=steps)
        ops.work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as caught:
            ops.recording_axis_rotation((0, 0, 1), F(3, 4), context=context, path="joint", max_steps=10000)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_same_warmed_angle_rechecks_all_nested_caches_after_cap_change(self):
        ops = ReachPoseOps(ReachExecutionWork())
        context = object()
        arguments = dict(context=context, path="joint", max_steps=10000)
        ops.recording_axis_rotation((0, 0, 1), F(1, 2), **arguments)
        ops.work.max_operand_bits = 128
        outcomes = []
        for candidate in (ops, ReachPoseOps(ReachExecutionWork(max_operand_bits=128))):
            with self.assertRaises(ReachAdmissionError) as caught:
                candidate.recording_axis_rotation((0, 0, 1), F(1, 2), **arguments)
            outcomes.append((caught.exception.reach_code, caught.exception.details))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(ops.work.counts["cache_operand_scope_reset"], 1)

    def test_cancelled_operand_scope_reset_preserves_the_previous_cache(self):
        work = ReachExecutionWork()
        work.remember(("retained",), F(1, 2))
        before = tuple(work._cache.items())
        work.max_operand_bits = 128
        marker = RuntimeError("cancel operand scope reset")
        charge = work.charge
        def cancelled(kind="checkpoint", amount=1):
            if kind == "cache_operand_scope_reset":
                work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(work, "charge", side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                work.lookup(("retained",))
        self.assertIs(caught.exception, marker)
        self.assertEqual(tuple(work._cache.items()), before)
        self.assertEqual(work._cache_operand_bits, 32768)

    def test_cancellation_does_not_publish_a_partial_cursor(self):
        ops = ReachPoseOps(ReachExecutionWork())
        context = object()
        ops.recording_axis_rotation((0, 0, 1), F(1, 4), context=context, path="joint", max_steps=10000)
        key = next(key for key in ops.work._cache if "recording_rotation_cursor" in key)
        before = ops.work._cache[key]
        marker = RuntimeError("cancel recording increment")
        charge = ops.work.charge
        def cancelled(kind="checkpoint", amount=1):
            if kind == "recording_rotation_step":
                ops.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(ops.work, "charge", side_effect=cancelled):
            with self.assertRaises(RuntimeError) as caught:
                ops.recording_axis_rotation((0, 0, 1), F(1, 2), context=context, path="joint", max_steps=10000)
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.work.callback_error, marker)
        self.assertEqual(ops.work._cache[key], before)


if __name__ == "__main__":
    unittest.main()
