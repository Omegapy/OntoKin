"""Saturated request-cache reuse and interruption before cache mutation."""
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.reach_kinematics import admit_planar
from ontokin.reach_numeric import (
    DyadicContext, PI64_BITS, ReachAdmissionError, ReachExecutionWork,
    bits_float, float_bits,
)


CORPUS = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1/acceptance.json"
PI = bits_float(PI64_BITS)
LIMITS = ((-PI, PI), (-PI, PI))


class ReachCacheBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus = json.loads(CORPUS.read_text())
        cls.case = next(case for case in corpus["source_cases"] if case["id"] == "P01")
        cls.expected_bits = tuple(map(float_bits,
            cls.case["expected"]["independent_solution"]["resolved_joint_targets_rad"]))

    def _admit(self, work, limits=LIMITS):
        spec = self.case["specification"]
        return admit_planar(spec["lengths"], spec["target"], "elbow_" + spec["branch"],
                            limits, work=work)

    def test_saturated_cache_retains_proof_and_revalidates_limits_and_domain(self):
        calls = 0

        def check():
            nonlocal calls
            calls += 1

        work = ReachExecutionWork(check=check)
        for index in range(work.max_cache_entries):
            work.remember(("earlier_pose", index), (index,))
        self.assertEqual(work.record()["cache_entries"], 256)
        first = self._admit(work)
        self.assertEqual(first.target_bits, self.expected_bits)
        self.assertEqual(tuple(map(float_bits, first.target_rad)), self.expected_bits)
        self.assertEqual(work.record()["cache_entries"], 256)
        before = work.operations
        with patch.object(DyadicContext, "atan_small",
                          side_effect=AssertionError("A retained IK proof was recomputed")):
            again = self._admit(work)
            self.assertIsNot(again, first)
            self.assertEqual(replace(again, work=()), replace(first, work=()))
            # The shared admission-entry unit precedes the local meter.
            self.assertEqual(dict(again.work)["operations"] + 1, work.operations - before)
            self.assertGreater(dict(again.work)["operations"], 0)
            self.assertEqual(dict(again.work)["series_terms"], 0)
            self.assertEqual(dict(again.work)["interval_operations"], 0)
            # These requests have the same mathematical cache key. Their current
            # limits/domain must still be checked before reuse grants a result.
            for limits, code in ((((-PI, PI), (-PI, 0.0)), "reach_limit"),
                                 (((-PI, PI), (-4.0, 4.0)), "reach_domain")):
                with self.subTest(code=code):
                    with self.assertRaises(ReachAdmissionError) as raised:
                        self._admit(work, limits)
                    self.assertEqual(raised.exception.reach_code, code)
        self.assertEqual(calls, work.operations)
        self.assertEqual(sum(work.counts.values()), work.operations)
        self.assertEqual(work.record()["cache_entries"], 256)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)

    def test_hot_proof_survives_interleaved_pose_entries_at_lowered_capacity(self):
        work = ReachExecutionWork(max_cache_entries=2)
        first = self._admit(work)
        work.remember(("cold_pose", 0), (0,))
        with patch.object(DyadicContext, "atan_small",
                          side_effect=AssertionError("A recently used IK proof was evicted")):
            for index in range(1, 5):
                again = self._admit(work)
                self.assertEqual(again.target_bits, self.expected_bits)
                self.assertEqual(replace(again, work=()), replace(first, work=()))
                work.remember(("cold_pose", index), (index,))
                self.assertEqual(work.record()["cache_entries"], 2)
            self.assertEqual(self._admit(work).target_bits, self.expected_bits)
        self.assertGreater(work.counts.get("cache_promote", 0), 0)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)

    def test_interrupted_bookkeeping_preserves_cache_values_and_order(self):
        for operation in ("lookup", "replace", "insert"):
            for reason in ("cancellation", "budget"):
                with self.subTest(operation=operation, reason=reason):
                    calls = 0
                    cancel_at = None
                    marker = RuntimeError("cancel cache bookkeeping")

                    def check():
                        nonlocal calls
                        calls += 1
                        if calls == cancel_at:
                            raise marker

                    work = ReachExecutionWork(check=check, max_cache_entries=2,
                        max_operations=3 if reason == "budget" else 100000)
                    work.remember(("a",), ("original",))
                    work.remember(("b",), ("retained",))
                    before = tuple(work._cache.items())
                    # The lookup/insert charge succeeds; the following promotion
                    # or eviction checkpoint must fail before any cache change.
                    if reason == "cancellation":
                        cancel_at = calls + 2
                    error_type = RuntimeError if reason == "cancellation" else ReachAdmissionError
                    with self.assertRaises(error_type) as raised:
                        if operation == "lookup":
                            work.lookup(("a",))
                        elif operation == "replace":
                            work.remember(("a",), ("replacement",))
                        else:
                            work.remember(("c",), ("new",))
                    if reason == "cancellation":
                        self.assertIs(raised.exception, marker)
                        self.assertIs(work.callback_error, marker)
                    else:
                        self.assertEqual(raised.exception.reach_code, "reach_resource")
                        self.assertEqual(raised.exception.details["budget"], "max_operations")
                    self.assertEqual(tuple(work._cache.items()), before)
                    self.assertEqual(work.record()["cache_entries"], 2)
                    self.assertEqual(work.operations, 3)
                    self.assertEqual(sum(work.counts.values()), work.operations)


if __name__ == "__main__":
    unittest.main()
