"""Bounded cache publication never exposes a partially admitted cursor group."""
import unittest

from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork


def identity(work):
    return tuple((key, id(value)) for key, value in work._cache.items()), work._cache_generation


def prepared():
    work = ReachExecutionWork(max_cache_entries=3)
    for key in ("a", "b", "c"):
        work.remember((key,), object())
    entries = ((("b",), object()), (("d",), object()), (("b",), object()))
    return work, entries


class ReachRecordingBatchPublicationTests(unittest.TestCase):
    def test_batch_has_identical_final_lru_values_and_per_mutation_charges(self):
        for seed in ((), ("a",), ("a", "b", "c")):
            actual, expected = (ReachExecutionWork(max_cache_entries=3) for _ in range(2))
            for key in seed:
                value = object()
                actual.remember((key,), value)
                expected.remember((key,), value)
            entries = ((("b",), object()), (("d",), object()), (("b",), object()))
            self.assertIs(actual.remember_batch(entries, admission=lambda: True), True)
            for key, value in entries:
                expected.remember(key, value)
            self.assertEqual(identity(actual), identity(expected))
            for kind in ("cache_insert", "cache_promote", "cache_evict"):
                self.assertEqual(actual.counts.get(kind, 0), expected.counts.get(kind, 0))
            self.assertEqual(actual.operations, expected.operations + 1)
            self.assertLessEqual(len(actual._cache), 3)

    def test_admission_follows_every_callback_and_precedes_all_mutations(self):
        work, entries = prepared()
        before, events = identity(work), []
        def check():
            events.append("callback")
            self.assertEqual(identity(work), before)
        def admission():
            events.append("admission")
            self.assertEqual(identity(work), before)
            # Publication after this receipt performs no additional callback.
            work.external_check = lambda: self.fail("callback after complete admission")
            return True
        work.external_check = check
        self.assertIs(work.remember_batch(entries, admission=admission), True)
        self.assertEqual(events, ["callback"] * 7 + ["admission"])
        self.assertEqual(tuple(work._cache), (("c",), ("d",), ("b",)))
        self.assertIs(work._cache[("b",)], entries[-1][1])
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_refused_or_failed_admission_preserves_complete_previous_state(self):
        for failure in (None, RuntimeError("reject all staged values")):
            work, entries = prepared()
            before = identity(work)
            def admission():
                if failure is not None:
                    raise failure
                return False
            if failure is None:
                self.assertIs(work.remember_batch(entries, admission=admission), False)
            else:
                with self.assertRaises(RuntimeError) as caught:
                    work.remember_batch(entries, admission=admission)
                self.assertIs(caught.exception, failure)
            self.assertEqual(identity(work), before)

    def test_cancellation_at_every_batch_callback_preserves_order_and_exception(self):
        for checkpoint in range(7):
            with self.subTest(checkpoint=checkpoint):
                work, entries = prepared()
                before, calls = identity(work), []
                marker = RuntimeError("cancel the complete pending publication")
                def check():
                    calls.append(True)
                    if len(calls) == checkpoint + 1:
                        work.max_operand_bits = 128
                        raise marker
                work.external_check = check
                with self.assertRaises(RuntimeError) as caught:
                    work.remember_batch(entries, admission=lambda: self.fail("admission after cancellation"))
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(identity(work), before)

    def test_cap_changes_and_restore_during_scope_reset_never_publish_a_prefix(self):
        for checkpoint in range(7):
            for restore in (False, True):
                with self.subTest(checkpoint=checkpoint, restore=restore):
                    work, entries = prepared()
                    before, calls = identity(work), []
                    def check():
                        calls.append(True)
                        if len(calls) == checkpoint + 1:
                            work.max_operand_bits = 128
                        elif restore and len(calls) == checkpoint + 2:
                            work.max_operand_bits = 32768
                    work.external_check = check
                    self.assertIs(work.remember_batch(entries,
                        admission=lambda: self.fail("a changed domain reached admission")), False)
                    if restore:
                        self.assertEqual(identity(work), before)
                        self.assertEqual(work.max_operand_bits, 32768)
                    else:
                        self.assertFalse(work._cache)
                    self.assertFalse(any(value is entries[0][1] or value is entries[1][1]
                                         or value is entries[2][1] for value in work._cache.values()))

    def test_cache_capacity_changes_decline_without_eviction_or_admission(self):
        for checkpoint in range(7):
            with self.subTest(checkpoint=checkpoint):
                work, entries = prepared()
                before, calls = identity(work), []
                def check():
                    calls.append(True)
                    if len(calls) == checkpoint + 1:
                        work.max_cache_entries = 2
                work.external_check = check
                self.assertIs(work.remember_batch(entries,
                    admission=lambda: self.fail("a changed cache limit reached admission")), False)
                self.assertEqual(identity(work), before)

    def test_reentrant_callback_writes_survive_without_any_outer_prefix(self):
        for checkpoint in range(7):
            with self.subTest(checkpoint=checkpoint):
                work, entries = prepared()
                calls, completed = [], []
                inner = object()
                def check():
                    calls.append(True)
                    if len(calls) == checkpoint + 1:
                        work.external_check = None
                        work.remember(("b",), inner)
                        completed.append(identity(work))
                        work.external_check = check
                work.external_check = check
                self.assertIs(work.remember_batch(entries,
                    admission=lambda: self.fail("a reentrant cache mutation reached admission")), False)
                self.assertEqual(identity(work), completed[0])
                self.assertIs(work._cache[("b",)], inner)
                self.assertNotIn(("d",), work._cache)

    def test_reentrant_transaction_keeps_its_own_complete_group(self):
        work, entries = prepared()
        nested, captured = ((("inner",), object()), (("b",), object())), []
        def check():
            work.external_check = None
            self.assertTrue(work.remember_batch(nested, admission=lambda: True))
            captured.append(identity(work))
        work.external_check = check
        self.assertFalse(work.remember_batch(entries, admission=lambda: True))
        self.assertEqual(identity(work), captured[0])
        self.assertIs(work._cache[("b",)], nested[1][1])
        self.assertNotIn(("d",), work._cache)

    def test_reentrant_or_cap_changing_admission_cannot_overwrite_completed_work(self):
        for change in ("cache", "cap", "capacity"):
            with self.subTest(change=change):
                work, entries = prepared()
                before, inside = identity(work), []
                def admission():
                    if change == "cache":
                        work.remember(("inner",), object())
                    elif change == "cap":
                        work.max_operand_bits = 128
                    else:
                        work.max_cache_entries = 2
                    inside.append(identity(work))
                    return True
                self.assertFalse(work.remember_batch(entries, admission=admission))
                self.assertEqual(identity(work), inside[0])
                if change != "cache":
                    self.assertEqual(identity(work), before)

    def test_batch_size_and_shape_admission_retain_the_fixed_cache_bound(self):
        work, entries = prepared()
        before = identity(work)
        for value in (list(entries), entries + entries, ((["bad"], object()),), (("bad",),)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                work.remember_batch(value, admission=lambda: True)
            self.assertEqual(identity(work), before)
        with self.assertRaises(ValueError):
            work.remember_batch(entries, admission=None)
        self.assertEqual(work.max_cache_entries, 3)
        self.assertEqual(work.max_operations, 100000)

    def test_empty_batch_still_admits_current_source_and_checks_cancellation(self):
        work = ReachExecutionWork()
        calls = []
        self.assertTrue(work.remember_batch((), admission=lambda: calls.append("source") or True))
        self.assertEqual(calls, ["source"])
        self.assertFalse(work._cache)
        marker = RuntimeError("cancel empty source receipt")
        work.external_check = lambda: (_ for _ in ()).throw(marker)
        with self.assertRaises(RuntimeError) as caught:
            work.remember_batch((), admission=lambda: self.fail("cancelled empty receipt"))
        self.assertIs(caught.exception, marker)

    def test_budget_exhaustion_keeps_the_original_failure_and_no_partial_group(self):
        work = ReachExecutionWork(max_operations=2)
        old = object()
        work.remember(("old",), old)
        before = identity(work)
        with self.assertRaises(ReachAdmissionError) as caught:
            work.remember_batch(((("new",), object()),), admission=lambda: True)
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], 2)
        self.assertEqual(identity(work), before)


if __name__ == "__main__":
    unittest.main()
