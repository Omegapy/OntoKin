"""One-shot exact clock parsing preserves independent admission and failures."""
from contextlib import nullcontext
from fractions import Fraction as F
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_reference_source_batch import prefix


def record(value):
    value = F(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def cached_axis():
    ordinary = reader.rational_clock
    def cached(value, *, work=None, cache_parse=True):
        return ordinary(value, work=work, cache_parse=True)
    return patch.object(reader, "rational_clock", cached)


def axis(work, *, cached=False, forged=False):
    exact = tuple(F(index, 64) for index in range(65))
    raw = [float(value) for value in exact]
    if forged:
        raw[17] += 2. ** -20
    authored = [record(value) for value in exact]
    retained = [{"authored_seconds": source, "stored_seconds": value,
                 "stored_binary32_bits": struct.pack(">f", value).hex(),
                 "semantic_boundary": index in (0, 64)}
                for index, (source, value) in enumerate(zip(authored, raw))]
    decoded = SimpleNamespace(document={"animations": [{"samplers": [{"input": 0}, {"input": 0}]}]},
                              clock=lambda index: tuple(raw))
    with cached_axis() if cached else nullcontext():
        return reader.verify_retained_clocks(decoded, {"retained_keys": retained}, authored,
            (F(0), F(1)), F(1), time_tolerance=F(1, 1000000), work=work)


class RetainedClockParsingTests(unittest.TestCase):
    def test_exact_values_and_all_parse_operations_match_without_numeric_cache_bookkeeping(self):
        for value in (F(0), F(7, 31), F(10**127 + 1, 3), F(1, 10**127 + 1), F(10**128 + 1, 3)):
            results = []
            for cached in (True, False):
                work = Work()
                actual = reader.rational_clock(record(value), work=work, cache_parse=cached)
                results.append((actual, work))
                self.assertEqual(actual, value)
                self.assertEqual(work.operations, sum(work.counts.values()))
                for kind, expected in (("independent_clock_integer", 2),
                                       ("independent_clock_reduction", 1),
                                       ("independent_clock_reduction_return", 1)):
                    self.assertEqual(work.counts[kind], expected)
            self.assertEqual(results[0][0], results[1][0])
            self.assertFalse(results[1][1]._cache)
            self.assertLessEqual(results[1][1].operations, results[0][1].operations)

    def test_repeated_width_default_still_reuses_its_complete_exact_parse(self):
        work = Work()
        value = record(F(7, 31))
        self.assertEqual(reader.rational_clock(value, work=work), F(7, 31))
        first = work.operations
        self.assertEqual(reader.rational_clock(dict(value), work=work), F(7, 31))
        self.assertLess(work.operations - first, first)
        self.assertEqual(work.counts["independent_clock_reduction"], 1)
        self.assertEqual(len(work._cache), 1)

    def test_one_shot_parse_does_not_read_write_promote_or_evict_existing_results(self):
        work = Work()
        for index in range(256):
            work.remember(("existing", index), F(index, 257))
        saved, counts = tuple(work._cache.items()), dict(work.counts)
        for index in range(40):
            self.assertEqual(reader.rational_clock(record(F(index, 41)), work=work, cache_parse=False), F(index, 41))
        self.assertEqual(tuple(work._cache.items()), saved)
        for kind in ("cache_lookup", "cache_insert", "cache_promote", "cache_evict"):
            self.assertEqual(work.counts.get(kind, 0), counts.get(kind, 0))
        self.assertEqual(work.max_cache_entries, 256)
        self.assertEqual(work.max_operand_bits, 32768)
        self.assertEqual(work.max_operations, 100000)

    def test_changed_supplied_strings_are_reparsed_and_do_not_inherit_a_previous_result(self):
        work, value = Work(), record(F(7, 31))
        for numerator in ("7", "8", "9"):
            value["numerator"] = numerator
            self.assertEqual(reader.rational_clock(value, work=work, cache_parse=False), F(int(numerator), 31))
        value["numerator"] = "09"
        with self.assertRaises(OntoKinError) as caught:
            reader.rational_clock(value, work=work, cache_parse=False)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CLOCK")
        self.assertFalse(work._cache)

    def test_malformed_and_unreduced_records_keep_the_original_diagnostic(self):
        cases = ({}, {"numerator": "1", "denominator": "2", "extra": 1},
                 {"numerator": "01", "denominator": "2"},
                 {"numerator": "-1", "denominator": "2"},
                 {"numerator": "2", "denominator": "4"},
                 {"numerator": "1", "denominator": "0"},
                 {"numerator": "0", "denominator": "2"},
                 {"numerator": True, "denominator": "2"},
                 {"numerator": "9" * 9866, "denominator": "1"})
        for value in cases:
            errors = []
            for cached in (True, False):
                with self.subTest(value=str(value)[:60], cached=cached), self.assertRaises(OntoKinError) as caught:
                    reader.rational_clock(value, work=Work(), cache_parse=cached)
                errors.append(caught.exception.diagnostic.details)
            self.assertEqual(errors[0], errors[1])

    def test_narrow_operand_guards_match_the_original_parse(self):
        for cap, value in ((1, F(0)), (64, F(1 << 80, 3)), (128, F(1, (1 << 130) + 1))):
            errors = []
            for cached in (True, False):
                with self.assertRaises(ReachAdmissionError) as caught:
                    reader.rational_clock(record(value), work=Work(max_operand_bits=cap), cache_parse=cached)
                errors.append((caught.exception.reach_code, caught.exception.details))
            self.assertEqual(errors[0], errors[1])

    def test_each_surviving_callback_preserves_exception_identity_without_partial_publication(self):
        for fail_at in range(1, 5):
            marker, calls = RuntimeError("one-shot parse cancellation"), 0
            def check():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    raise marker
            work = Work(check=check)
            with self.assertRaises(RuntimeError) as caught:
                reader.rational_clock(record(F(7, 31)), work=work, cache_parse=False)
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertEqual(calls, fail_at)
            self.assertFalse(work._cache)

    def test_final_result_guard_still_observes_a_cap_narrowed_by_reduction_callback(self):
        for cached in (True, False):
            work = Work()
            original = work.charge
            def narrow(kind="checkpoint", amount=1):
                result = original(kind, amount)
                if kind == "independent_clock_reduction_return":
                    work.max_operand_bits = 2
                return result
            with patch.object(work, "charge", narrow), self.assertRaises(ReachAdmissionError) as caught:
                reader.rational_clock(record(F(7, 31)), work=work, cache_parse=cached)
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
            self.assertEqual(caught.exception.details["limit"], 2)
            self.assertEqual(caught.exception.details["consumed"], 5)

    def test_narrow_then_widen_cannot_hide_the_original_integer_allocation_failure(self):
        for cached in (True, False):
            work, visited = Work(), []
            original = work.charge
            def narrow(kind="checkpoint", amount=1):
                result = original(kind, amount)
                if kind == "independent_clock_integer":
                    visited.append(kind)
                    work.max_operand_bits = 1 if len(visited) == 1 else 32768
                return result
            with patch.object(work, "charge", narrow), self.assertRaises(ReachAdmissionError) as caught:
                reader.rational_clock(record(F(7, 31)), work=work, cache_parse=cached)
            self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
            self.assertEqual(visited, ["independent_clock_integer"])

    def test_complete_axis_values_and_cache_contention_include_setup_in_the_saving(self):
        for prefill in (0, 256):
            results = []
            for cached in (True, False):
                work = Work()
                for index in range(prefill):
                    work.remember(("preexisting", index), F(index, 257))
                result = axis(work, cached=cached)
                results.append((result, work.operations, work.counts))
                self.assertLessEqual(len(work._cache), 256)
                self.assertEqual(work.operations, sum(work.counts.values()))
            self.assertEqual(results[0][0], results[1][0])
            self.assertGreater(results[0][1], results[1][1])
            self.assertEqual(results[0][2]["independent_clock_integer"], results[1][2]["independent_clock_integer"])

    def test_forged_accessor_and_consistent_labels_still_fail_the_exact_rounding_cell(self):
        results = []
        for cached in (True, False):
            with self.assertRaises(OntoKinError) as caught:
                axis(Work(), cached=cached, forged=True)
            results.append(caught.exception.diagnostic.details)
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0]["export_code"], "OKE-E-CLOCK-ROUNDING")

    def test_whole_original_prefix_bytes_and_reports_match_with_positive_total_savings(self):
        for case in ("P09", "P11", "P16", "L03"):
            outcomes = []
            for cached in (True, False):
                with cached_axis() if cached else nullcontext():
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                self.assertLessEqual(len(compiler.reach_work._cache), 256)
                self.assertEqual(compiler.reach_work.operations, sum(compiler.reach_work.counts.values()))
                outcomes.append((result.data, result.report, compiler.budget.operations))
            self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            self.assertLess(outcomes[1][2], outcomes[0][2])
            print(f"{case} whole retained-clock prefix: cached={outcomes[0][2]}, one_shot={outcomes[1][2]}")


if __name__ == "__main__":
    unittest.main()
