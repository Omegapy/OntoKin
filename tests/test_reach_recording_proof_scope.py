"""Sequential recording proofs retain useful reuse without nested cache churn."""
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import (
    _Bounds, _Cell, _aligned_reference, _key_comparisons,
    _recording_orientation_comparison, _stored_arc,
)
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_orientation_proof_reuse import comparison_inputs


def point(value):
    return _Cell(F(value), F(value))


class IndependentRecordingProofScopeTests(unittest.TestCase):
    def test_nested_arithmetic_is_identical_without_intermediate_cache_entries(self):
        queries = (
            lambda a: a.root(F(2)),
            lambda a: a.root(F(121, 49), precision=48),
            lambda a: a.norm((F(-3, 7), F(4, 11), F(0))),
            lambda a: a.normalize((0., 0., -.6, -.8)),
            lambda a: a.difference((point(0), point(1), point(2)),
                                   (_Cell(F(-1, 7), F(1, 7)), point(1), point(2))),
        )
        for query in queries:
            work, cached_work = Work(), Work()
            arithmetic = _Bounds(work, cache_intermediates=False)
            with self.subTest(query=query):
                self.assertEqual(query(arithmetic), query(_Bounds(cached_work)))
                self.assertLess(work.operations, cached_work.operations)
                self.assertEqual(work.record()["cache_entries"], 0)

    def test_orientation_and_stored_arc_proofs_still_share_complete_results(self):
        work = Work()
        arithmetic = _Bounds(work, cache_intermediates=False)
        raw = (0., 0., .6, .8)
        source = tuple(map(point, raw))
        with patch("ontokin.reach_conformance._aligned_reference", wraps=_aligned_reference) as alignment:
            first = _recording_orientation_comparison(raw, source, arithmetic)
            second = _recording_orientation_comparison(raw, source, arithmetic)
        self.assertEqual(first, second)
        self.assertEqual(alignment.call_count, 1)
        normalized, _ = first
        arc = _stored_arc(raw, raw, normalized, normalized, arithmetic)
        with patch.object(arithmetic, "difference", side_effect=AssertionError("repeated complete arc proof")):
            self.assertEqual(_stored_arc(raw, raw, normalized, normalized, arithmetic), arc)
        domains = {key[2] for key in work._cache}
        self.assertEqual(domains, {"recording_orientation_comparison", "stored_endpoint_arc"})

    def test_whole_endpoint_cache_is_unneeded_for_separate_positions(self):
        reference, geometry, tracks = comparison_inputs()
        work, previous_work = Work(), Work()
        with patch("ontokin.reach_conformance._aligned_reference", wraps=_aligned_reference) as alignment:
            actual = _key_comparisons(reference, geometry, tracks, F(0), 0,
                                      _Bounds(work, cache_intermediates=False))
        expected = _key_comparisons(reference, geometry, tracks, F(0), 0, _Bounds(previous_work))
        self.assertEqual(actual, expected)
        self.assertEqual(alignment.call_count, 1)
        self.assertEqual(actual[0]["position_error"], 0)
        self.assertEqual(actual[1]["position_error"], 1)
        self.assertLess(work.operations, previous_work.operations)
        self.assertFalse(any(key[2] == "key_pose_comparison" for key in work._cache))

    def test_complete_proofs_recheck_changed_signs_and_source_cells(self):
        work = Work()
        arithmetic = _Bounds(work, cache_intermediates=False)
        raw = (0., 0., .6, .8)
        source = tuple(map(point, raw))
        normalized, error = _recording_orientation_comparison(raw, source, arithmetic)
        changed_source = (*source[:3], _Cell(F(7, 10), F(9, 10)))
        _, changed_error = _recording_orientation_comparison(raw, changed_source, arithmetic)
        self.assertNotEqual(error, changed_error)
        _stored_arc(raw, raw, normalized, normalized, arithmetic)
        opposite = tuple(-value for value in raw)
        with self.assertRaises(OntoKinError):
            _stored_arc(raw, opposite, normalized, arithmetic.normalize(opposite), arithmetic)

    def test_small_cache_evicts_complete_proofs_without_changing_answers(self):
        work = Work(max_cache_entries=2)
        arithmetic = _Bounds(work, cache_intermediates=False)
        for value in (.25, .5, .75, .25):
            raw = (0., 0., value, 1.)
            source = tuple(map(point, raw))
            self.assertEqual(_recording_orientation_comparison(raw, source, arithmetic),
                             _recording_orientation_comparison(raw, source, _Bounds(Work())))
            self.assertLessEqual(len(work._cache), 2)
        self.assertEqual(work.max_operations, 100000)

    def test_lowered_caps_still_reject_original_root_intermediate_extent(self):
        for retain in (False, True):
            arithmetic = _Bounds(Work(max_operand_bits=128), cache_intermediates=retain)
            with self.subTest(retain=retain), self.assertRaises(ReachAdmissionError) as caught:
                arithmetic.normalize((0., 0., 0., 1.))
            self.assertEqual(caught.exception.details["consumed"], 193)

    def test_live_root_domain_is_rechecked_before_each_native_allocation(self):
        for checkpoint in ("independent_sqrt_scale", "independent_sqrt_divide", "independent_sqrt_enter",
                           "independent_sqrt_return", "independent_sqrt_exactness"):
            work = Work()
            original = work.charge
            def charge(kind="checkpoint", amount=1):
                if kind == checkpoint:
                    work.max_operand_bits = 16
                return original(kind, amount)
            with self.subTest(checkpoint=checkpoint), patch.object(work, "charge", side_effect=charge), \
                 self.assertRaises(ReachAdmissionError):
                _Bounds(work, cache_intermediates=False).root(F(2))

    def test_cancellation_preserves_original_exception_without_partial_proof(self):
        work = Work()
        arithmetic = _Bounds(work, cache_intermediates=False)
        marker = RuntimeError("cancel uncached intermediate proof")
        def cancel():
            raise marker
        work.external_check = cancel
        raw, source = (0., 0., .6, .8), tuple(map(point, (0, 0, F(3, 5), F(4, 5))))
        with self.assertRaises(RuntimeError) as caught:
            _recording_orientation_comparison(raw, source, arithmetic)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(len(work._cache), 0)


if __name__ == "__main__":
    unittest.main()
