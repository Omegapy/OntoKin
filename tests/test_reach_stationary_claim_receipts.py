"""Completed stationary comparisons retain only their actual admitted limits."""
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


EPSILON = F(1, 1 << 40)


def inputs():
    position = (reader._Cell(-EPSILON, EPSILON),) * 3
    orientation = (reader._Cell(F(1, 2) - EPSILON, F(1, 2) + EPSILON),) * 4
    pose = SimpleNamespace(position=position, orientation=orientation)
    reference = SimpleNamespace(
        recording_pose_enclosures=lambda carriers, time, side, recording_context=None: {"frame": pose},
        recording_stationary_frames=lambda carriers, first, last, side: frozenset(carriers))
    geometry = {0: {"frame": "frame"}}
    tracks = {0: {"translation": [(0.,) * 3] * 4, "rotation": [(.5,) * 4] * 4}}
    rows = {(index, 0): {"max_endpoint_position_error_m": 1e-5,
                         "max_endpoint_unit_quaternion_error": 1e-5} for index in range(3)}
    return reference, geometry, tracks, rows


class StationaryClaimReceiptTests(unittest.TestCase):
    def setUp(self):
        self.reference, self.geometry, self.tracks, self.rows = inputs()
        self.arithmetic = reader._Bounds(Work(), cache_intermediates=False)

    def compare(self, index, previous=None):
        return reader._key_comparisons(self.reference, self.geometry, self.tracks, F(index), index,
            self.arithmetic, previous=previous, previous_time=F(index - 1) if previous else None,
            endpoint_rows=self.rows)

    def ready(self):
        first = self.compare(0)
        self.assertNotIn("_endpoint_limit_receipt", first[0])
        second = self.compare(1, first)
        self.assertEqual(second[0]["_endpoint_limit_receipt"], (1e-5, 1e-5))
        self.assertNotIn("_endpoint_limit_receipt", first[0])
        return second

    def test_equal_actual_limits_omit_only_completed_comparisons(self):
        previous = self.ready()
        before = self.arithmetic.work.operations
        with patch.object(self.arithmetic, "compare", side_effect=AssertionError("repeated threshold product")), \
             patch.object(self.arithmetic.work, "lookup", side_effect=AssertionError("additional cache")), \
             patch.object(self.reference, "recording_stationary_frames",
                          wraps=self.reference.recording_stationary_frames) as stationary:
            actual = self.compare(2, previous)
        reused_cost = self.arithmetic.work.operations - before
        stationary.assert_called_once()
        unreceipted = deepcopy(previous)
        del unreceipted[0]["_endpoint_limit_receipt"]
        before = self.arithmetic.work.operations
        expected = self.compare(2, unreceipted)
        self.assertEqual(actual, expected)
        self.assertLess(reused_cost, self.arithmetic.work.operations - before)
        self.assertEqual(self.arithmetic.work.max_operations, 100000)
        self.assertLessEqual(len(self.arithmetic.work._cache), 256)

    def test_a_tighter_adjacent_claim_recomputes_the_original_exact_norms(self):
        previous = self.ready()
        self.rows[2, 0] = {"max_endpoint_position_error_m": float(2 * EPSILON),
                           "max_endpoint_unit_quaternion_error": float(2 * EPSILON)}
        actual = self.compare(2, previous)
        self.assertLess(actual[0]["position_error"], previous[0]["position_error"])
        self.assertLess(actual[0]["quaternion_error"], previous[0]["quaternion_error"])
        self.assertIsNotNone(actual[0]["normalized"])
        self.assertNotIn("_endpoint_limit_receipt", actual[0])
        self.assertEqual(previous[0]["_endpoint_limit_receipt"], (1e-5, 1e-5))

    def test_equal_numeric_limits_of_different_types_need_fresh_comparisons(self):
        for record in self.rows.values():
            record.update(max_endpoint_position_error_m=1., max_endpoint_unit_quaternion_error=1.)
        first = self.compare(0)
        previous = self.compare(1, first)
        for record in self.rows.values():
            record.update(max_endpoint_position_error_m=1, max_endpoint_unit_quaternion_error=1)
        with patch.object(self.arithmetic, "compare", wraps=self.arithmetic.compare) as compare:
            actual = self.compare(2, previous)
        self.assertEqual(compare.call_count, 2)
        self.assertEqual(tuple(map(type, actual[0]["_endpoint_limit_receipt"])), (int, int))
        self.assertEqual(tuple(map(type, previous[0]["_endpoint_limit_receipt"])), (float, float))

    def test_every_adjacent_claim_is_admitted_before_receipt_reuse(self):
        previous = self.ready()
        for invalid in (False, float("nan"), -1., 1 << 32768):
            self.rows[2, 0]["max_endpoint_position_error_m"] = invalid
            with self.subTest(invalid_type=type(invalid).__name__), \
                 patch.object(self.arithmetic.work, "lookup", side_effect=AssertionError("invalid claim reused")), \
                 self.assertRaises((OntoKinError, ReachAdmissionError)):
                self.compare(2, previous)

    def test_changed_actual_operand_does_not_inherit_the_stationary_receipt(self):
        previous = self.ready()
        self.tracks[0]["rotation"][2] = (-.5,) * 4
        actual = self.compare(2, previous)
        self.assertNotIn("_endpoint_limit_receipt", actual[0])
        self.assertEqual(actual[0]["_quaternion_operand"], (-.5,) * 4)
        self.assertEqual(previous[0]["_quaternion_operand"], (.5,) * 4)

    def test_live_narrowing_cannot_return_an_old_threshold_receipt(self):
        previous = self.ready()
        saved = deepcopy(previous)
        charge = self.arithmetic.work.charge
        def narrow(kind="checkpoint", amount=1):
            if kind == "independent_stationary_key_comparison":
                self.arithmetic.work.max_operand_bits = 128
            return charge(kind, amount)
        with patch.object(self.arithmetic.work, "charge", narrow), self.assertRaises(ReachAdmissionError) as caught:
            self.compare(2, previous)
        self.assertEqual(caught.exception.details["consumed"], 193)
        self.assertEqual(previous, saved)

    def test_cancelled_admission_or_receipt_use_keeps_the_original_exception(self):
        previous = self.ready()
        saved = deepcopy(previous)
        for checkpoint in ("independent_endpoint_claims", "independent_stationary_key_comparison"):
            marker = RuntimeError("cancel stationary receipt " + checkpoint)
            charge = self.arithmetic.work.charge
            def cancel(kind="checkpoint", amount=1):
                if kind == checkpoint:
                    self.arithmetic.work.external_check = lambda: (_ for _ in ()).throw(marker)
                return charge(kind, amount)
            with self.subTest(checkpoint=checkpoint), patch.object(self.arithmetic.work, "charge", cancel), \
                    self.assertRaises(RuntimeError) as caught:
                self.compare(2, previous)
            self.assertIs(caught.exception, marker)
            self.assertIs(self.arithmetic.work.callback_error, marker)
            self.assertEqual(previous, saved)
            self.arithmetic.work.external_check = None

    def test_interruption_of_second_comparison_cannot_publish_a_partial_receipt(self):
        previous = self.compare(0)
        saved, calls = deepcopy(previous), []
        marker = RuntimeError("cancel second threshold comparison")
        compare = self.arithmetic.compare
        def interrupt(first, last):
            calls.append((first, last))
            if len(calls) == 2:
                self.arithmetic.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return compare(first, last)
        with patch.object(self.arithmetic, "compare", interrupt), self.assertRaises(RuntimeError) as caught:
            self.compare(1, previous)
        self.assertEqual(calls, [(previous[0]["position_error"], 1e-5),
                                 (previous[0]["quaternion_error"], 1e-5)])
        self.assertIs(caught.exception, marker)
        self.assertIs(self.arithmetic.work.callback_error, marker)
        self.assertEqual(previous, saved)
        self.assertNotIn("_endpoint_limit_receipt", previous[0])


if __name__ == "__main__":
    unittest.main()
