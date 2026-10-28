"""Exact constant affine coordinates retain source projection and operand gates."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_reference import MAX_OPERAND_BITS, ReferenceError, _Uncertain
from test_reach_reference_coordinate_law import example, previous_coordinate


class IndependentConstantCoordinateTests(unittest.TestCase):
    def test_constant_tweens_and_reach_laws_equal_original_actual_and_ideal_samples(self):
        for value in (F(0), F(1, 7), F(-3, 11), F(1, 1 << 1075)):
            for paired in (False, True):
                for status in ("running", "paused", "completed"):
                    for ideal in (False, True):
                        reference, state, _, active = example(initial=value, target=value,
                                                               paired=paired, status=status)
                        direct, direct_state, _, direct_active = example(initial=value, target=value,
                                                                         paired=paired, status=status)
                        active.elapsed = direct_active.elapsed = F(1, 7)
                        active.since = direct_active.since = F(1, 11)
                        for joint in (("shoulder", "elbow") if paired else ("shoulder",)):
                            for time in (F(1, 11), F(1, 3), F(2)):
                                with self.subTest(value=value, paired=paired, status=status, ideal=ideal,
                                                  joint=joint, time=time):
                                    before = reference.a.work.operations
                                    used_before = direct.a.work.operations
                                    with patch.object(reference.a, "lookup", side_effect=AssertionError("constant law lookup")):
                                        result = reference._coordinate(joint, time, state, ideal=ideal)
                                    expected = previous_coordinate(direct, joint, time, direct_state, ideal=ideal)
                                    self.assertEqual(result, expected)
                                    self.assertLess(reference.a.work.operations - before,
                                                    direct.a.work.operations - used_before)
                                    self.assertFalse(any(key[0] == "coordinate_affine_law" for key in reference.a.cache))

    def test_original_zero_duration_and_intermediate_operand_gates_remain(self):
        for duration, elapsed, limit, error in (
                (F(0), F(0), MAX_OPERAND_BITS, _Uncertain),
                (F(1 << 63), F(0), 64, ReferenceError),
                (F(1), F(1, 1 << 127), 128, ReferenceError),
                (F(1), F(1 << MAX_OPERAND_BITS), MAX_OPERAND_BITS, ReferenceError)):
            for ideal in (False, True):
                reference, state, _, active = example(initial=F(0), target=F(0), duration=duration, status="paused")
                direct, direct_state, _, direct_active = example(initial=F(0), target=F(0), duration=duration,
                                                                 status="paused")
                active.elapsed = direct_active.elapsed = elapsed
                reference.a.work.max_operand_bits = direct.a.work.max_operand_bits = limit
                with self.subTest(duration=duration, elapsed=elapsed, limit=limit, ideal=ideal):
                    with self.assertRaises(error) as actual:
                        reference._coordinate("shoulder", F(0), state, ideal=ideal)
                    with self.assertRaises(error) as expected:
                        previous_coordinate(direct, "shoulder", F(0), direct_state, ideal=ideal)
                    self.assertEqual(str(actual.exception), str(expected.exception))
                    self.assertEqual(getattr(actual.exception, "code", None), getattr(expected.exception, "code", None))

    def test_actual_projection_overflow_and_cancellation_publish_no_law(self):
        reference, state, _, _ = example(initial=F(1 << 1024), target=F(1 << 1024))
        with self.assertRaises(ReferenceError):
            reference._coordinate("shoulder", F(0), state)
        self.assertFalse(reference.a.cache)
        reference, state, _, _ = example(initial=F(1, 3), target=F(1, 3))
        marker = RuntimeError("cancel constant independent coordinate")
        with patch.object(reference.a.work, "external_check", side_effect=marker), \
                self.assertRaises(RuntimeError) as caught:
            reference._coordinate("shoulder", F(0), state)
        self.assertIs(caught.exception, marker)
        self.assertIs(reference.a.work.callback_error, marker)
        self.assertFalse(reference.a.cache)

    def test_body_recipe_constant_sample_omits_elapsed_arithmetic_on_its_sufficient_domain(self):
        reference, state, action, active = example(initial=F(1, 7), target=F(1, 7))
        action.target = "shoulder"
        active.elapsed, active.since = F(2, 5), F(1, 11)
        rate, direct, receipt = reference._recording_coordinate_recipe("shoulder", state)
        self.assertEqual(rate, 0)
        self.assertIsNotNone(receipt)
        for clock in (F(0), F(1, 3), F(2)):
            with self.subTest(clock=clock), patch.object(reference.a, "exact", side_effect=AssertionError("constant recipe arithmetic")):
                self.assertEqual(direct(clock), F(1, 7))

    def test_body_recipe_narrow_cap_and_cancellation_keep_original_failure(self):
        reference, state, action, active = example(initial=F(1, 7), target=F(1, 7))
        action.target = "shoulder"
        active.since = F(1, 1 << 80)
        _, direct, _ = reference._recording_coordinate_recipe("shoulder", state)
        reference.a.work.max_operand_bits = 128
        with self.assertRaises(ReferenceError) as caught:
            direct(F(1, 1 << 80))
        self.assertEqual(caught.exception.code, "resource")
        reference.a.work.max_operand_bits = MAX_OPERAND_BITS
        marker = RuntimeError("cancel constant independent body recipe")
        with patch.object(reference.a.work, "external_check", side_effect=marker), \
                self.assertRaises(RuntimeError) as caught:
            direct(F(1, 4))
        self.assertIs(caught.exception, marker)
        self.assertIs(reference.a.work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
