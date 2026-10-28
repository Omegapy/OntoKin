"""A disabled optional source cache still polls before doing pose work."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_runtime import ReachSimulator


class ReachPoseSlotBudgetTests(unittest.TestCase):
    def test_oversized_graph_bypass_preserves_interruption_before_build(self):
        for reason in ("cancellation", "budget"):
            with self.subTest(reason=reason):
                cancelled = False
                marker = RuntimeError("cancel uncached source pose")
                def check():
                    if cancelled:
                        raise marker
                work = ReachExecutionWork(check=check, max_cache_entries=1,
                                          max_operations=1 if reason == "budget" else 100000)
                work.remember(("already_retained",), ("unchanged",))
                before = tuple(work._cache.items())
                simulator = object.__new__(ReachSimulator)
                simulator.work = work
                simulator.model = SimpleNamespace(objects={"first": None, "second": None}, sites={})
                build = Mock(side_effect=AssertionError("built after interruption"))
                cancelled = reason == "cancellation"
                with self.assertRaises(RuntimeError if cancelled else ReachAdmissionError) as caught:
                    simulator._pose_slot("first", ("distinct_inputs",), build)
                if cancelled:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(work.callback_error, marker)
                else:
                    self.assertEqual(caught.exception.details["budget"], "max_operations")
                build.assert_not_called()
                self.assertEqual(tuple(work._cache.items()), before)
                self.assertEqual(work.operations, 1)


if __name__ == "__main__":
    unittest.main()
