"""Incremental recording forecasts retain exact complete history obligations."""
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import evaluator, reach_runtime
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.reach_delivery import ReachDeliveryCapture
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_runtime import (_BoundaryHistoryPreflight,
    _incoming_release_bound, boundary_history_bound)
from test_reach_phase import source


def model(case):
    return compile_construction(source(case)).model


def outcome(call):
    try:
        return ("passed", call())
    except OntoKinError as error:
        return ("failed", error.diagnostic.code, error.diagnostic.details)


class ReachHistoryPreflightTests(unittest.TestCase):
    def test_incremental_totals_and_first_failure_match_complete_forecasts(self):
        cases = (
            ("P01", (0, 2, 3)),
            ("P14", (0, F(1, 2), F(3, 2), 3, 4)),
            ("P16", (0, 2, 3, 4)),
            ("P23", (0, 2, 3)),
            ("P24", (0, F(3, 2), 2, 3)),
            ("L01", (0, F(1, 2), F(3, 2), 3, 4)),
            ("L02", (0, F(1, 2), F(3, 2), 2)),
            ("L03", (0, 2, 3, 4)),
            ("L04", (0, F(1, 4))),
        )
        for case, times in cases:
            current = model(case)
            for side in ("before", "after"):
                with self.subTest(case=case, side=side):
                    preflight = _BoundaryHistoryPreflight(current, horizon=times[-1], side=side)
                    prefix = []
                    for time in times:
                        previous = (preflight.total, preflight.last_time)
                        prefix.append(time)
                        expected = outcome(lambda: boundary_history_bound(
                            current, prefix, horizon=times[-1], side=side))
                        actual = outcome(lambda: preflight.append(time))
                        self.assertEqual(actual, expected)
                        if actual[0] == "failed":
                            self.assertEqual((preflight.total, preflight.last_time), previous)
                            break
                        self.assertEqual(preflight.total, expected[1])
                        self.assertEqual(preflight.last_time, time)

    def test_repeated_arm_preflight_does_less_work_without_changing_total(self):
        current = model("P23")
        times = (F(0), F(2), F(3))
        complete_work = ReachExecutionWork()
        for length in range(1, len(times) + 1):
            expected = boundary_history_bound(current, times[:length],
                horizon=F(3), check=complete_work.tick)
        incremental_work = ReachExecutionWork()
        preflight = _BoundaryHistoryPreflight(current, horizon=F(3), check=incremental_work.tick)
        for time in times:
            actual = preflight.append(time)
        self.assertEqual(actual, expected)
        self.assertLess(incremental_work.operations, complete_work.operations)
        self.assertEqual(incremental_work.operations, sum(incremental_work.counts.values()))
        self.assertEqual(incremental_work.max_operations, 100000)

    def test_exact_history_limit_and_one_less_retain_complete_consumed_count(self):
        current = model("P16")
        times = (F(0), F(2))
        total = boundary_history_bound(current, times, horizon=F(2))
        self.assertLessEqual(total, evaluator.MAX_OUTPUT_RECORDS)
        for limit in (total, total - 1):
            with self.subTest(limit=limit), patch.object(evaluator, "MAX_OUTPUT_RECORDS", limit):
                preflight = _BoundaryHistoryPreflight(current, horizon=F(2))
                before = preflight.append(F(0))
                expected = outcome(lambda: boundary_history_bound(current, times, horizon=F(2)))
                actual = outcome(lambda: preflight.append(F(2)))
                self.assertEqual(actual, expected)
                if limit == total:
                    self.assertEqual(actual, ("passed", total))
                else:
                    self.assertEqual(preflight.total, before)
                    self.assertEqual(preflight.last_time, F(0))
                    self.assertEqual(actual[2]["budget"], "boundary_state_records")
                    self.assertEqual(actual[2]["consumed"], total)
                    self.assertEqual(actual[2]["limit"], total - 1)

    def test_cancelled_final_accumulation_preserves_previous_complete_prefix(self):
        current = model("P01")
        armed = False
        marker = RuntimeError("cancel new history accumulation")

        def check():
            if armed:
                raise marker

        work = ReachExecutionWork(check=check)
        preflight = _BoundaryHistoryPreflight(current, horizon=F(3), check=work.tick)
        preflight.append(F(0))
        saved = preflight.total, preflight.last_time
        original = reach_runtime._boundary_history_weight

        def weight(*args, **kwargs):
            nonlocal armed
            value = original(*args, **kwargs)
            armed = True
            return value

        with patch.object(reach_runtime, "_boundary_history_weight", weight):
            with self.assertRaises(RuntimeError) as caught:
                preflight.append(F(2))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual((preflight.total, preflight.last_time), saved)
        armed = False
        self.assertEqual(preflight.append(F(2)), boundary_history_bound(current, (0, 2), horizon=F(3)))

    def test_lowered_operation_budget_cannot_publish_unchecked_accumulation(self):
        current = model("P01")
        measured = ReachExecutionWork()
        expected = _BoundaryHistoryPreflight(current, horizon=F(3), check=measured.tick).append(F(0))
        work = ReachExecutionWork(max_operations=measured.operations - 1)
        preflight = _BoundaryHistoryPreflight(current, horizon=F(3), check=work.tick)
        with self.assertRaises(ReachAdmissionError) as caught:
            preflight.append(F(0))
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual((preflight.total, preflight.last_time), (0, None))
        self.assertGreater(expected, 0)

    def test_last_callback_rechecks_live_history_limit_and_source_context(self):
        for change in ("limit", "revision", "duration", "model", "endpoint", "side"):
            with self.subTest(change=change):
                current = model("P01")
                preflight = _BoundaryHistoryPreflight(current, horizon=F(3))
                preflight.append(F(0))
                saved = preflight.total, preflight.last_time
                original = reach_runtime._boundary_history_weight
                ready = False

                def weight(*args, **kwargs):
                    nonlocal ready
                    value = original(*args, **kwargs)
                    ready = True
                    return value

                def check():
                    if ready:
                        if change == "limit":
                            evaluator.MAX_OUTPUT_RECORDS = saved[0]
                        elif change == "revision":
                            current.program_revision = "changed-source"
                        elif change == "duration":
                            current.duration += F(1)
                        elif change == "model":
                            preflight.model = SimpleNamespace(**vars(current))
                        elif change == "endpoint":
                            preflight.endpoint = F(2)
                        else:
                            preflight.side = "before"

                preflight.check = check
                with patch.object(evaluator, "MAX_OUTPUT_RECORDS", evaluator.MAX_OUTPUT_RECORDS), \
                        patch.object(reach_runtime, "_boundary_history_weight", weight):
                    error = OntoKinError if change == "limit" else ValueError
                    with self.assertRaises(error):
                        preflight.append(F(2))
                self.assertEqual((preflight.total, preflight.last_time), saved)

    def test_reentrant_callback_and_invalid_clock_preserve_previous_prefix(self):
        current = model("P01")
        preflight = _BoundaryHistoryPreflight(current, horizon=F(3))
        preflight.append(F(0))
        saved = preflight.total, preflight.last_time
        for invalid in (F(0), F(-1), F(4)):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    preflight.append(invalid)
                self.assertEqual((preflight.total, preflight.last_time), saved)
        preflight.check = lambda: preflight.append(F(1))
        with self.assertRaisesRegex(ValueError, "reentered"):
            preflight.append(F(2))
        self.assertEqual((preflight.total, preflight.last_time), saved)
        preflight.check = None
        self.assertEqual(preflight.append(F(2)), boundary_history_bound(current, (0, 2), horizon=F(3)))
        for horizon, side in ((F(-1), "after"), (F(4), "after"), (F(3), "invalid")):
            with self.assertRaises(ValueError):
                _BoundaryHistoryPreflight(current, horizon=horizon, side=side)

    def test_no_release_at_clock_does_not_construct_unused_topology(self):
        current = model("P23")
        checkpoints = []
        # Its release array is empty, but each relevant source event is still
        # visited and counted. No joint/follow graph is needed for that fact.
        with patch.object(current, "joints", None), patch.object(current, "follows", None):
            self.assertEqual(_incoming_release_bound(current, F(0), check=lambda: checkpoints.append(1)), 1)
            self.assertTrue(checkpoints)
            self.assertEqual(_incoming_release_bound(current, F(2)), 1)
        released = model("P16")
        with patch.object(released, "joints", None), patch.object(released, "follows", None):
            self.assertEqual(_incoming_release_bound(released, F(0)), 1)
        self.assertGreater(_incoming_release_bound(released, F(2)), 1)

    def test_release_graph_build_keeps_cancellation_and_complete_contributors(self):
        current = model("P16")
        expected = _incoming_release_bound(current, F(2))
        marker = RuntimeError("cancel contributor topology")
        original = current.joints

        class CancelledJoints(dict):
            def items(self):
                raise marker

        with patch.object(current, "joints", CancelledJoints(original)):
            with self.assertRaises(RuntimeError) as caught:
                _incoming_release_bound(current, F(2))
        self.assertIs(caught.exception, marker)
        self.assertEqual(_incoming_release_bound(current, F(2)), expected)

    def test_agent_capture_retains_times_only_after_successful_history_extension(self):
        current = model("P01")
        work = ReachExecutionWork()
        capture = ReachDeliveryCapture(current, F(3), work=work)
        simulator = SimpleNamespace(model=current, work=work)
        capture.before_capture(simulator, F(0), "before")
        saved = capture.history.total
        self.assertEqual(capture.times, [F(0)])
        marker = RuntimeError("cancel agent history extension")
        with patch.object(work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                capture.before_capture(simulator, F(2), "before")
        self.assertIs(caught.exception, marker)
        self.assertEqual(capture.times, [F(0)])
        self.assertEqual(capture.history.total, saved)
        capture.before_capture(simulator, F(2), "before")
        self.assertEqual(capture.times, [F(0), F(2)])
        self.assertEqual(capture.history.total, boundary_history_bound(current, capture.times, horizon=F(3)))
        with self.assertRaisesRegex(ValueError, "incomplete or failed"):
            capture.finish()


if __name__ == "__main__":
    unittest.main()
