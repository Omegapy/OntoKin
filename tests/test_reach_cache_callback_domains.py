"""Cache bookkeeping callbacks cannot reuse proofs from an earlier domain."""
from fractions import Fraction as F
import unittest

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps


class ReachCacheCallbackDomainTests(unittest.TestCase):
    def test_lookup_promotion_rechecks_the_domain_after_its_callback(self):
        work = ReachExecutionWork()
        proof = F(1 << 255)
        work.remember(("proof",), proof)
        calls = 0

        def narrow_on_promotion():
            nonlocal calls
            calls += 1
            if calls == 2:
                work.max_operand_bits = 128

        work.external_check = narrow_on_promotion
        self.assertIsNone(work.lookup(("proof",)))
        self.assertEqual(work._cache, {})
        self.assertEqual(work._cache_operand_bits, 128)
        self.assertEqual(calls, 3)
        self.assertEqual(work.counts["cache_operand_scope_reset"], 1)

    def test_warm_axis_proof_has_the_same_narrow_domain_failure_as_cold_arithmetic(self):
        ops = ReachPoseOps(ReachExecutionWork())
        ops.axis_rotation((0, 0, 1), F(1, 2))
        # The public operand decodes precede the warm axis proof lookup. The
        # first cache promotion belongs to that proof, not a nested series.
        prior_promotions = ops.work.counts.get("cache_promote", 0)

        def narrow_during_promotion():
            # charge invokes its callback before recording the current kind.
            if ops.work.counts.get("cache_lookup", 0) > lookups:
                ops.work.max_operand_bits = 128

        lookups = ops.work.counts.get("cache_lookup", 0)
        ops.work.external_check = narrow_during_promotion
        outcomes = []
        for candidate in (ops, ReachPoseOps(ReachExecutionWork(max_operand_bits=128))):
            with self.assertRaises(ReachAdmissionError) as caught:
                candidate.axis_rotation((0, 0, 1), F(1, 2))
            outcomes.append((caught.exception.reach_code, caught.exception.details))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertGreater(ops.work.counts["cache_promote"], prior_promotions)
        self.assertEqual(ops.work.counts["cache_operand_scope_reset"], 1)

    def test_insert_replace_and_evict_discard_a_candidate_when_the_callback_narrows(self):
        for operation in ("insert", "replace", "evict"):
            with self.subTest(operation=operation):
                work = ReachExecutionWork(max_cache_entries=2)
                work.remember(("first",), F(1 << 255))
                if operation != "insert":
                    work.remember(("second",), F(2))
                target = ("first",) if operation == "replace" else ("new",)
                calls = 0
                narrow_at = 1 if operation == "insert" else 2

                def narrow():
                    nonlocal calls
                    calls += 1
                    if calls == narrow_at:
                        work.max_operand_bits = 128

                work.external_check = narrow
                # Completed old-domain results may return to their caller;
                # this optional publication itself must not raise or retain it.
                self.assertIsNone(work.remember(target, F(1 << 255)))
                self.assertEqual(work._cache, {})
                self.assertEqual(work._cache_operand_bits, 128)
                self.assertEqual(calls, narrow_at + 1)
                work.external_check = None
                work.remember(target, F(1, 2))
                self.assertEqual(work.lookup(target), F(1, 2))
                self.assertEqual(work.record()["cache_entries"], 1)

    def test_reset_uses_the_domain_after_its_own_callback(self):
        work = ReachExecutionWork()
        work.remember(("proof",), F(1 << 255))
        work.max_operand_bits = 128
        calls = 0

        def narrow_again():
            nonlocal calls
            calls += 1
            if calls == 2:
                work.max_operand_bits = 64

        work.external_check = narrow_again
        self.assertIsNone(work.lookup(("proof",)))
        self.assertEqual(work._cache, {})
        self.assertEqual(work._cache_operand_bits, 64)
        self.assertEqual(calls, 2)

    def test_cancelled_post_callback_reset_preserves_all_previous_values_and_order(self):
        for operation in ("lookup", "replace", "evict"):
            with self.subTest(operation=operation):
                work = ReachExecutionWork(max_cache_entries=2)
                work.remember(("first",), F(1 << 255))
                work.remember(("second",), F(2))
                before = tuple(work._cache.items())
                marker = RuntimeError("cancel cache domain reset")
                calls = 0

                def cancel_reset():
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        work.max_operand_bits = 128
                    if calls == 3:
                        raise marker

                work.external_check = cancel_reset
                with self.assertRaises(RuntimeError) as caught:
                    if operation == "lookup":
                        work.lookup(("first",))
                    else:
                        target = ("first",) if operation == "replace" else ("new",)
                        work.remember(target, F(3))
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(tuple(work._cache.items()), before)
                self.assertEqual(work._cache_operand_bits, 32768)
                work.external_check = None
                self.assertIsNone(work.lookup(("first",)))
                self.assertEqual(work._cache, {})
                self.assertEqual(work._cache_operand_bits, 128)

    def test_budget_failure_before_post_callback_reset_preserves_the_cache(self):
        work = ReachExecutionWork(max_operations=4, max_cache_entries=2)
        work.remember(("first",), F(1 << 255))
        work.remember(("second",), F(2))
        before = tuple(work._cache.items())
        calls = 0

        def narrow_on_promotion():
            nonlocal calls
            calls += 1
            if calls == 2:
                work.max_operand_bits = 128

        work.external_check = narrow_on_promotion
        with self.assertRaises(ReachAdmissionError) as caught:
            work.lookup(("first",))
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["consumed"], 5)
        self.assertEqual(tuple(work._cache.items()), before)
        self.assertEqual(work._cache_operand_bits, 32768)
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_unchanged_domain_keeps_existing_charges_capacity_and_lru_order(self):
        work = ReachExecutionWork(max_cache_entries=2)
        work.remember(("first",), F(1))
        work.remember(("second",), F(2))
        self.assertEqual(work.lookup(("first",)), F(1))
        work.remember(("first",), F(3))
        work.remember(("third",), F(4))
        self.assertEqual(tuple(work._cache), (("first",), ("third",)))
        self.assertEqual(work._cache[("first",)], F(3))
        self.assertEqual(work.counts, {"cache_insert": 4, "cache_lookup": 1,
                                      "cache_promote": 2, "cache_evict": 1})
        self.assertEqual(work.operations, 8)
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_reentrant_promotion_callback_can_reset_the_domain_before_outer_lookup_resumes(self):
        work = ReachExecutionWork()
        work.remember(("proof",), F(1 << 255))
        calls = 0

        def nested_lookup():
            nonlocal calls
            calls += 1
            if calls == 2:
                work.max_operand_bits = 128
                self.assertIsNone(work.lookup(("absent",)))
                work.remember(("proof",), F(1, 2))

        work.external_check = nested_lookup
        self.assertIsNone(work.lookup(("proof",)))
        self.assertEqual(work._cache_operand_bits, 128)
        self.assertEqual(tuple(work._cache.items()), ((("proof",), F(1, 2)),))
        work.external_check = None
        self.assertEqual(work.lookup(("proof",)), F(1, 2))

    def test_reentrant_promotion_callback_can_evict_the_lookup_key(self):
        work = ReachExecutionWork(max_cache_entries=1)
        work.remember(("first",), F(1))
        calls = 0

        def nested_insert():
            nonlocal calls
            calls += 1
            if calls == 2:
                work.remember(("second",), F(2))

        work.external_check = nested_insert
        self.assertIsNone(work.lookup(("first",)))
        self.assertEqual(tuple(work._cache.items()), ((("second",), F(2)),))

    def test_reentrant_insert_replace_and_evict_preserve_nested_mutations_and_capacity(self):
        for operation in ("insert", "replace", "evict"):
            with self.subTest(operation=operation):
                work = ReachExecutionWork(max_cache_entries=2)
                work.remember(("first",), F(1))
                work.remember(("second",), F(2))
                calls = 0
                reenter_at = 1 if operation == "insert" else 2
                expected = None

                def mutate_inside_callback():
                    nonlocal calls, expected
                    calls += 1
                    if calls == reenter_at:
                        if operation == "insert":
                            work.remember(("third",), F(99))
                        elif operation == "replace":
                            work.remember(("third",), F(3))
                        else:
                            self.assertEqual(work.lookup(("first",)), F(1))
                        expected = tuple(work._cache.items())

                work.external_check = mutate_inside_callback
                target = ("first",) if operation == "replace" else ("third",)
                work.remember(target, F(100))
                self.assertIsNotNone(expected)
                self.assertEqual(tuple(work._cache.items()), expected)
                self.assertLessEqual(len(work._cache), 2)
                self.assertEqual(work.operations, sum(work.counts.values()))

    def test_reentrant_remember_preserves_a_nested_proof_in_the_new_domain(self):
        work = ReachExecutionWork(max_cache_entries=2)
        work.remember(("first",), F(1 << 255))
        work.remember(("second",), F(2))
        calls = 0

        def replace_in_narrow_domain():
            nonlocal calls
            calls += 1
            if calls == 2:
                work.max_operand_bits = 128
                self.assertIsNone(work.lookup(("absent",)))
                work.remember(("first",), F(1, 2))

        work.external_check = replace_in_narrow_domain
        work.remember(("first",), F(1 << 256))
        self.assertEqual(work._cache_operand_bits, 128)
        self.assertEqual(tuple(work._cache.items()), ((("first",), F(1, 2)),))

    def test_reentrant_scope_reset_keeps_entries_already_rebuilt_in_the_current_domain(self):
        work = ReachExecutionWork()
        work.remember(("old",), F(1 << 255))
        work.max_operand_bits = 128
        calls = 0

        def populate_during_reset():
            nonlocal calls
            calls += 1
            if calls == 2:
                self.assertIsNone(work.lookup(("absent",)))
                work.remember(("fresh",), F(1, 2))

        work.external_check = populate_during_reset
        self.assertIsNone(work.lookup(("old",)))
        self.assertEqual(work._cache_operand_bits, 128)
        self.assertEqual(tuple(work._cache.items()), ((("fresh",), F(1, 2)),))


if __name__ == "__main__":
    unittest.main()
