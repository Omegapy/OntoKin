"""A repeated independent orientation claim keeps complete current operands."""
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def cells(values):
    return tuple(reader._Cell(F(value), F(value)) for value in values)


RAW = (0., 0., .6, .8 + 2. ** -24)
SOURCE = cells((0, 0, F(3, 5), F(4, 5)))


class IndependentOrientationClaimTests(unittest.TestCase):
    def test_complete_repeated_claim_omits_both_completed_inequalities(self):
        work = Work()
        arithmetic = reader._Bounds(work)
        first = reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic)
        before = work.operations
        with patch.object(arithmetic, "compare", wraps=arithmetic.compare) as compare:
            second = reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic)
        self.assertEqual(first, second)
        self.assertIsNone(second[0])
        self.assertGreater(second[1], 0)
        compare.assert_not_called()
        self.assertEqual(work.operations - before, 4)
        self.assertEqual(work.max_operations, 100000)

    def test_tighter_claim_and_changed_source_or_stored_values_get_fresh_proofs(self):
        for changed in ("claim", "source", "raw", "sign"):
            work = Work()
            arithmetic = reader._Bounds(work)
            first = reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic)
            raw, source, claim = RAW, SOURCE, 1e-5
            if changed == "claim":
                claim = 0.
            elif changed == "source":
                source = (*SOURCE[:2], reader._Cell(F(1, 2), F(7, 10)), SOURCE[3])
            elif changed == "raw":
                raw = (*RAW[:3], .8 + 2. ** -23)
            else:
                raw = tuple(-value for value in RAW)
            with self.subTest(changed=changed), \
                    patch.object(arithmetic, "compare", wraps=arithmetic.compare) as compare:
                actual = reader._recording_orientation_bound(raw, source, claim, arithmetic)
            fresh = reader._recording_orientation_bound(raw, source, claim, reader._Bounds(Work()))
            self.assertEqual(actual, fresh)
            self.assertGreater(compare.call_count, 0)
            if changed == "claim":
                self.assertIsNotNone(actual[0])
            elif changed != "sign":
                self.assertNotEqual(actual, first)

    def test_native_claim_type_is_part_of_identity_and_bool_is_rejected(self):
        arithmetic = reader._Bounds(Work())
        for claim in (1, 1., F(1)):
            with self.subTest(claim_type=type(claim)), \
                    patch.object(arithmetic, "compare", wraps=arithmetic.compare) as compare:
                reader._recording_orientation_bound(RAW, SOURCE, claim, arithmetic)
            self.assertEqual(compare.call_count, 2)
        with self.assertRaises(OntoKinError):
            reader._recording_orientation_bound(RAW, SOURCE, True, arithmetic)

    def test_current_position_comparison_runs_once_on_each_successful_hit(self):
        arithmetic = reader._Bounds(Work())
        calls = []
        for _ in range(3):
            reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic,
                                                before_error=lambda: calls.append("position"))
        self.assertEqual(calls, ["position"] * 3)
        marker = RuntimeError("this sibling position failed")
        def fail():
            raise marker
        with self.assertRaises(RuntimeError) as caught:
            reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic, before_error=fail)
        self.assertIs(caught.exception, marker)

    def test_bad_current_source_or_buffer_cannot_reuse_a_completed_claim(self):
        work = Work()
        arithmetic = reader._Bounds(work)
        reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic)
        for raw, source in (((False, *RAW[1:]), SOURCE),
                ((float("nan"), *RAW[1:]), SOURCE), (RAW[:3], SOURCE),
                (RAW, SOURCE[:3]), (RAW, (reader._Cell(F(1), F(0)), *SOURCE[1:])),
                (RAW, (reader._Cell(F(1 << 32768), F(1 << 32768)), *SOURCE[1:]))):
            with self.subTest(raw=raw, source_length=len(source)), \
                    patch.object(work, "lookup", wraps=work.lookup) as lookup:
                with self.assertRaises((OntoKinError, ReachAdmissionError)):
                    reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
                lookup.assert_not_called()

    def test_warm_lookup_and_promotion_cannot_return_a_narrower_domain_proof(self):
        raw, source = (0., 0., 0., 1.), cells((0, 0, 0, 1))
        for checkpoint in ("independent_sufficient_orientation_domain", "cache_lookup", "cache_promote"):
            work = Work()
            arithmetic = reader._Bounds(work)
            reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
            original = work.charge
            def charge(kind="checkpoint", amount=1):
                value = original(kind, amount)
                if kind == checkpoint:
                    work.max_operand_bits = 128
                return value
            with self.subTest(checkpoint=checkpoint), patch.object(work, "charge", charge), \
                    self.assertRaises(ReachAdmissionError) as caught:
                reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
            self.assertEqual(caught.exception.details["limit"], 128)
            self.assertEqual(caught.exception.details["consumed"], 193)

    def test_position_callback_narrowing_keeps_original_normalization_failure(self):
        raw, source = (0., 0., 0., 1.), cells((0, 0, 0, 1))
        work = Work()
        arithmetic = reader._Bounds(work)
        reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
        def narrow():
            work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as caught:
            reader._recording_orientation_bound(raw, source, 1e-5, arithmetic, before_error=narrow)
        self.assertEqual(caught.exception.details["consumed"], 193)

    def test_cancelled_warm_lookup_preserves_original_error_and_cache(self):
        work = Work()
        arithmetic = reader._Bounds(work)
        reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic)
        saved = deepcopy(work._cache)
        marker = RuntimeError("cancel complete orientation claim")
        original = work.charge
        def charge(kind="checkpoint", amount=1):
            if kind == "cache_lookup":
                def fail():
                    raise marker
                work.external_check = fail
            return original(kind, amount)
        with patch.object(work, "charge", charge), self.assertRaises(RuntimeError) as caught:
            reader._recording_orientation_bound(RAW, SOURCE, 1e-5, arithmetic)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(work._cache, saved)

    def test_distinct_claims_share_only_the_existing_bounded_cache(self):
        work = Work(max_cache_entries=2)
        arithmetic = reader._Bounds(work)
        expected = reader._recording_orientation_bound(RAW, SOURCE, 1e-5, reader._Bounds(Work()))
        for claim in (1e-5, 2e-5, 3e-5, 1e-5):
            self.assertEqual(reader._recording_orientation_bound(RAW, SOURCE, claim, arithmetic), expected)
            self.assertLessEqual(len(work._cache), 2)
        self.assertGreater(work.counts.get("cache_evict", 0), 0)

    def test_translated_siblings_keep_exact_independent_endpoint_results(self):
        def run(reuse):
            work = Work()
            arithmetic = reader._Bounds(work, cache_intermediates=False)
            geometry = {index: {"frame": str(index)} for index in range(8)}
            tracks = {index: {"translation": [(float(index), 0., 0.)], "rotation": [RAW]}
                      for index in geometry}
            rows = {(0, index): {"max_endpoint_position_error_m": .001,
                                "max_endpoint_unit_quaternion_error": 1e-5} for index in geometry}
            reference = SimpleNamespace(recording_pose_enclosures=lambda carriers, time, side,
                recording_context=None: {frame: SimpleNamespace(position=cells((int(frame), 0, 0)),
                    orientation=(SOURCE[3], *SOURCE[:3])) for frame in carriers})
            original = arithmetic.reuse
            def selected(key, calculate):
                if not reuse and key[0] == "recording_orientation_sufficient_claim":
                    return calculate()
                return original(key, calculate)
            with patch.object(arithmetic, "reuse", selected):
                result = reader._key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic,
                                                  endpoint_rows=rows)
            return result, work.operations
        actual, cost = run(True)
        fresh, fresh_cost = run(False)
        self.assertEqual(actual, fresh)
        self.assertLess(cost, fresh_cost)
        self.assertEqual([actual[index]["magnitude"] for index in actual], list(range(8)))


if __name__ == "__main__":
    unittest.main()
