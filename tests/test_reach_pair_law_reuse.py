"""A reused reach law keeps each clock, public rate and finite domain exact."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_kinematics import PairSample, sample_pair
from ontokin.reach_numeric import (
    MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork, exact,
    bits_float, float_bits, rational, round_binary64,
)


def previous_sample(start, target, duration, elapsed, *, running, work):
    duration, elapsed = rational(duration, work), rational(elapsed, work)
    work.charge("pair_clock_domain")
    values, rates, exact_values, slopes = [], [], [], []
    for first, last in zip(start, target):
        initial, goal = rational(first, work), rational(last, work)
        slope = exact(exact(goal, initial, "sub", work), duration, "div", work)
        value = goal if elapsed == duration else exact(initial, exact(slope, elapsed, "mul", work), "add", work)
        exact_values.append(value)
        slopes.append(slope if running else F(0))
        values.append(round_binary64(value, work=work))
        rates.append(round_binary64(slope, work=work) if running else 0.0)
    return PairSample(tuple(values), tuple(rates), tuple(exact_values), tuple(slopes))


class ReachPairLawReuseTests(unittest.TestCase):
    def test_every_sample_keeps_exact_coordinates_rates_and_terminal_values(self):
        start, target, duration = (.1, -.3), (1.7, .9), F(3)
        work = ReachExecutionWork()
        for running in (True, False, True):
            for elapsed in (F(0), F(1, 3), F(3, 2), F(3)):
                with self.subTest(running=running, elapsed=elapsed):
                    actual = sample_pair(start, target, duration, elapsed, running=running, work=work)
                    expected = previous_sample(start, target, duration, elapsed,
                                               running=running, work=ReachExecutionWork())
                    self.assertEqual(actual, expected)
                    slopes = tuple((F(last) - F(first)) / duration for first, last in zip(start, target))
                    self.assertEqual(actual.exact_coordinates,
                                     tuple(F(first) + slope * elapsed for first, slope in zip(start, slopes)))
                    self.assertEqual(actual.exact_slopes, slopes if running else (F(0), F(0)))
                    repeated = sample_pair(start, target, duration, elapsed, running=running, work=work)
                    self.assertEqual(repeated, actual)
                    self.assertIsNot(repeated, actual)

    def test_warm_law_removes_repeated_slope_and_rate_work(self):
        start, target, duration = (.1, -.3), (1.7, .9), F(3)
        for running in (True, False):
            with self.subTest(running=running):
                work = ReachExecutionWork()
                sample_pair(start, target, duration, F(0), running=running, work=work)
                before = work.operations
                actual = sample_pair(start, target, duration, F(1, 3), running=running, work=work)
                used = work.operations - before
                previous_work = ReachExecutionWork()
                expected = previous_sample(start, target, duration, F(1, 3),
                                           running=running, work=previous_work)
                self.assertEqual(actual, expected)
                self.assertLess(used, previous_work.operations)
                self.assertEqual(work.max_operations, 100000)

    def test_warm_law_preserves_subnormal_and_normal_ties_to_even(self):
        cases = (
            ((0., 0.), (bits_float(1), bits_float(3)), (0, 2)),
            ((1., bits_float(float_bits(1.) + 1)),
             (bits_float(float_bits(1.) + 1), bits_float(float_bits(1.) + 2)),
             (float_bits(1.), float_bits(1.) + 2)),
        )
        for start, target, expected_bits in cases:
            with self.subTest(start=start, target=target):
                work = ReachExecutionWork()
                sample_pair(start, target, F(2), F(0), running=True, work=work)
                sample = sample_pair(start, target, F(2), F(1), running=True, work=work)
                self.assertEqual(sample, previous_sample(start, target, F(2), F(1),
                                                        running=True, work=ReachExecutionWork()))
                self.assertEqual(tuple(map(float_bits, sample.coordinates_rad)), expected_bits)

    def test_changed_law_operands_and_eviction_never_inherit_another_answer(self):
        work = ReachExecutionWork(max_cache_entries=3)
        laws = [((0., 0.), (1., 2.), F(3), True),
                ((.5, 0.), (1., 2.), F(3), True),
                ((0., 0.), (1., 3.), F(3), True),
                ((0., 0.), (1., 2.), F(4), True),
                ((0., 0.), (1., 2.), F(3), False)]
        for start, target, duration, running in (*laws, laws[0]):
            with self.subTest(start=start, target=target, duration=duration, running=running):
                actual = sample_pair(start, target, duration, F(1, 4), running=running, work=work)
                expected = previous_sample(start, target, duration, F(1, 4),
                                           running=running, work=ReachExecutionWork())
                self.assertEqual(actual, expected)
                self.assertLessEqual(len(work._cache), 3)

    def test_paused_law_does_not_round_an_unrepresentable_unused_rate(self):
        duration = F(1, 1 << 1074)
        start, target = (0., 0.), (1., -1.)
        work = ReachExecutionWork()
        for elapsed in (F(0), duration / 2, duration):
            paused = sample_pair(start, target, duration, elapsed, running=False, work=work)
            self.assertEqual(paused, previous_sample(start, target, duration, elapsed,
                                                    running=False, work=ReachExecutionWork()))
            self.assertEqual(paused.rates_rad_s, (0., 0.))
            self.assertEqual(paused.exact_slopes, (F(0), F(0)))
        with self.assertRaises(ReachAdmissionError) as caught:
            sample_pair(start, target, duration, duration, running=True, work=work)
        self.assertEqual(caught.exception.reach_code, "reach_numeric")
        self.assertEqual(sample_pair(start, target, duration, duration, running=False, work=work).coordinates_rad,
                         target)

    def test_warm_lookup_keeps_all_input_domains_and_actual_clock_checks(self):
        base = {"start_rad": (0., 0.), "target_rad": (1., 2.), "duration_s": F(3),
                "elapsed_s": F(1), "running": True}
        work = ReachExecutionWork()
        sample_pair(**base, work=work)
        changes = [
            ("start_rad", (False, 0.)), ("target_rad", (float("nan"), 2.)),
            ("start_rad", (F(1 << MAX_OPERAND_BITS), 0.)),
            ("duration_s", F(0)), ("duration_s", F(1, 1 << MAX_OPERAND_BITS)),
            ("elapsed_s", F(-1)), ("elapsed_s", F(4)), ("elapsed_s", True),
            ("running", 1), ("start_rad", (0.,)), ("target_rad", (1., 2., 3.)),
        ]
        for field, value in changes:
            with self.subTest(field=field, value_type=type(value).__name__):
                with patch.object(work, "lookup", wraps=work.lookup) as lookup:
                    with self.assertRaises(ReachAdmissionError):
                        sample_pair(**{**base, field: value}, work=work)
                    lookup.assert_not_called()

    def test_lowered_operand_cap_cannot_reuse_a_previously_admitted_law(self):
        start, target = (F(1, 1 << 64), F(0)), (F(3, 1 << 64), F(1))
        work = ReachExecutionWork()
        sample_pair(start, target, F(1), F(1), running=False, work=work)
        # Every input and final coordinate still fits. The original exact
        # subtraction's unreduced denominator preflight needs 130 bits.
        work.max_operand_bits = 125
        with self.assertRaises(ReachAdmissionError) as caught:
            sample_pair(start, target, F(1), F(1), running=False, work=work)
        self.assertEqual(caught.exception.reach_code, "reach_resource")
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["consumed"], 130)

    def test_cache_hit_preserves_cancellation_and_never_returns_a_partial_pair(self):
        marker = RuntimeError("cancel reused reach law")
        cancelled = False
        def check():
            if cancelled:
                raise marker
        work = ReachExecutionWork(check=check)
        sample_pair((0., 0.), (1., 2.), F(3), F(0), running=True, work=work)
        original = work.lookup
        def cancel_on_lookup(key):
            nonlocal cancelled
            cancelled = True
            return original(key)
        with patch.object(work, "lookup", side_effect=cancel_on_lookup):
            with self.assertRaises(RuntimeError) as caught:
                sample_pair((0., 0.), (1., 2.), F(3), F(1), running=True, work=work)
        self.assertIs(caught.exception, marker)

    def test_cold_failure_keeps_coordinate_before_rate_order_and_stores_no_partial_law(self):
        work = ReachExecutionWork()
        marker = RuntimeError("coordinate publication failed")
        with patch("ontokin.reach_kinematics.round_binary64", side_effect=marker) as rounding:
            with self.assertRaises(RuntimeError) as caught:
                sample_pair((0., 0.), (4., 6.), F(2), F(0), running=True, work=work)
        self.assertIs(caught.exception, marker)
        self.assertEqual(rounding.call_args.args, (F(0),))
        self.assertEqual(rounding.call_count, 1)
        self.assertEqual(len(work._cache), 0)


if __name__ == "__main__":
    unittest.main()
