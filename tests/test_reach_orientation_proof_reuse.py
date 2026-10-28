"""Independent orientation reuse preserves source cells and current domains."""
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import (
    _Bounds, _Cell, _aligned_reference, _key_comparisons, _recording_orientation_comparison,
)
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork


def point(value):
    return _Cell(F(value), F(value))


def previous_comparison(quaternion, expected, arithmetic):
    normalized = arithmetic.normalize(quaternion)
    aligned = _aligned_reference(quaternion, expected, arithmetic)
    return normalized, arithmetic.difference(normalized, aligned)


def comparison_inputs():
    orientation = (point(F(1, 2)),) * 4
    poses = {"first.frame": SimpleNamespace(position=tuple(map(point, (1, 2, 3))), orientation=orientation),
             "second.frame": SimpleNamespace(position=tuple(map(point, (8, 9, 10))), orientation=orientation)}
    reference = SimpleNamespace(recording_pose_enclosures=lambda carriers, time, side, recording_context=None:
                                {frame: poses[frame] for frame in carriers})
    geometry = {0: {"frame": "first.frame"}, 1: {"frame": "second.frame"}}
    tracks = {0: {"translation": [(1., 2., 3.)], "rotation": [(.5,) * 4]},
              1: {"translation": [(9., 9., 10.)], "rotation": [(.5,) * 4]}}
    return reference, geometry, tracks


class IndependentOrientationProofReuseTests(unittest.TestCase):
    def test_exact_normalization_errors_match_old_independent_comparison(self):
        for quaternion in ((0., 0., 0., 2.), (0., 0., -.6, -.8), (.5, -.5, .5, -.5)):
            for expected in (tuple(map(point, quaternion)), (_Cell(F(-1), F(1)),) * 4,
                             tuple(point(-F(value)) for value in quaternion)):
                with self.subTest(quaternion=quaternion, expected=expected):
                    work = ReachExecutionWork()
                    arithmetic = _Bounds(work)
                    expected_result = previous_comparison(quaternion, expected, _Bounds(ReachExecutionWork()))
                    self.assertEqual(_recording_orientation_comparison(quaternion, expected, arithmetic), expected_result)
                    before = work.operations
                    self.assertEqual(_recording_orientation_comparison(quaternion, expected, arithmetic), expected_result)
                    cached_cost = work.operations - before
                    previous_work = ReachExecutionWork()
                    previous = _Bounds(previous_work)
                    previous_comparison(quaternion, expected, previous)
                    before = previous_work.operations
                    previous_comparison(quaternion, expected, previous)
                    self.assertLess(cached_cost, previous_work.operations - before)

    def test_translated_carriers_share_orientation_but_keep_position_comparisons(self):
        reference, geometry, tracks = comparison_inputs()
        arithmetic = _Bounds(ReachExecutionWork())
        with patch("ontokin.reach_conformance._aligned_reference", wraps=_aligned_reference) as alignment:
            result = _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic)
        self.assertEqual(alignment.call_count, 1)
        self.assertEqual(result[0]["quaternion_error"], result[1]["quaternion_error"])
        self.assertEqual(result[0]["normalized"], result[1]["normalized"])
        self.assertEqual(result[0]["position_error"], 0)
        self.assertEqual(result[1]["position_error"], 1)
        self.assertNotEqual(result[0]["magnitude"], result[1]["magnitude"])

    def test_cold_position_failure_precedes_quaternion_difference_and_no_proof_is_remembered(self):
        reference, geometry, tracks = comparison_inputs()
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        marker = RuntimeError("position difference failed first")
        quaternion_marker = RuntimeError("orientation difference ran first")
        def fail(first, last):
            raise marker if len(first) == 3 else quaternion_marker
        with patch.object(arithmetic, "normalize", wraps=arithmetic.normalize) as normalize, \
             patch("ontokin.reach_conformance._aligned_reference", wraps=_aligned_reference) as alignment, \
             patch.object(arithmetic, "difference", side_effect=fail) as difference:
            with self.assertRaises(RuntimeError) as caught:
                _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic)
        self.assertIs(caught.exception, marker)
        self.assertEqual(normalize.call_count, 1)
        self.assertEqual(alignment.call_count, 1)
        self.assertEqual(difference.call_count, 1)
        self.assertFalse(any("recording_orientation_comparison" in key for key in work._cache))

    def test_changed_source_cells_and_stored_signs_have_distinct_proofs(self):
        arithmetic = _Bounds(ReachExecutionWork())
        raw = (0., 0., .6, .8)
        source = tuple(map(point, raw))
        for quaternion, expected in ((raw, source), (tuple(-value for value in raw), source),
                                     (raw, (*source[:3], _Cell(F(7, 10), F(9, 10))))):
            with self.subTest(quaternion=quaternion, expected=expected):
                with patch("ontokin.reach_conformance._aligned_reference", wraps=_aligned_reference) as alignment:
                    actual = _recording_orientation_comparison(quaternion, expected, arithmetic)
                self.assertEqual(alignment.call_count, 1)
                self.assertEqual(actual, previous_comparison(quaternion, expected, _Bounds(ReachExecutionWork())))

    def test_warm_reuse_rejects_all_invalid_raw_and_source_operands_before_lookup(self):
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        raw, expected = (0., 0., 0., 1.), tuple(map(point, (0, 0, 0, 1)))
        _recording_orientation_comparison(raw, expected, arithmetic)
        invalid = [((False, *raw[1:]), expected), ((float("nan"), *raw[1:]), expected),
                   ((1 << MAX_OPERAND_BITS, *raw[1:]), expected), (raw[:3], expected),
                   (raw, (False, *expected[1:])), (raw, (_Cell(F(1), F(0)), *expected[1:])),
                   (raw, (point(F(1 << MAX_OPERAND_BITS)), *expected[1:])), (raw, expected[:3])]
        for quaternion, source in invalid:
            with self.subTest(quaternion_types=tuple(type(value).__name__ for value in quaternion)):
                with patch.object(work, "lookup", wraps=work.lookup) as lookup:
                    with self.assertRaises((OntoKinError, ReachAdmissionError)):
                        _recording_orientation_comparison(quaternion, source, arithmetic)
                    lookup.assert_not_called()

    def test_narrower_cap_rechecks_nested_proof_intermediates_and_outer_pose_cache(self):
        raw, source = (0., 0., 0., 1.), tuple(map(point, (0, 0, 0, 1)))
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        _recording_orientation_comparison(raw, source, arithmetic)
        work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as caught:
            _recording_orientation_comparison(raw, source, arithmetic)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["consumed"], 193)
        reference, geometry, tracks = comparison_inputs()
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic)
        work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError):
            _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic)

    def test_cache_hit_keeps_original_callback_exception(self):
        armed = False
        marker = RuntimeError("cancel independent orientation proof")
        def check():
            if armed:
                raise marker
        work = ReachExecutionWork(check=check)
        arithmetic = _Bounds(work)
        raw, source = (0., 0., 0., 1.), tuple(map(point, (0, 0, 0, 1)))
        _recording_orientation_comparison(raw, source, arithmetic)
        original = work.lookup
        def cancel(key):
            nonlocal armed
            armed = True
            return original(key)
        with patch.object(work, "lookup", side_effect=cancel):
            with self.assertRaises(RuntimeError) as caught:
                _recording_orientation_comparison(raw, source, arithmetic)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)

    def test_eviction_retains_the_existing_cache_limit_and_exact_results(self):
        work = ReachExecutionWork(max_cache_entries=3)
        arithmetic = _Bounds(work)
        for value in (F(1, 4), F(1, 3), F(1, 2), F(1, 4)):
            raw = (0., 0., float(value), 1.)
            source = tuple(map(point, raw))
            self.assertEqual(_recording_orientation_comparison(raw, source, arithmetic),
                             previous_comparison(raw, source, _Bounds(ReachExecutionWork())))
            self.assertLessEqual(len(work._cache), 3)
        self.assertEqual(work.max_operations, 100000)


if __name__ == "__main__":
    unittest.main()
