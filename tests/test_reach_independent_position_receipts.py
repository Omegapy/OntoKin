"""Changing rotations cannot invalidate an unchanged independent position proof."""
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import (
    _Bounds, _Cell, _key_comparisons, _previous_position_comparison,
)
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def point(value):
    return _Cell(F(value), F(value))


def inputs():
    positions = [tuple(map(point, (1, 2, 3))), tuple(map(point, (1, 2, 3)))]
    orientations = [tuple(map(point, (1, 0, 0, 0))), tuple(map(point, (F(4, 5), 0, 0, F(3, 5))))]
    def poses(carriers, time, side, recording_context=None):
        return {carrier: SimpleNamespace(position=positions[int(time)], orientation=orientations[int(time)])
                for carrier in carriers}
    reference = SimpleNamespace(recording_pose_enclosures=poses,
                                recording_stationary_frames=lambda *args, **kwargs: frozenset())
    geometry = {0: {"frame": "carrier.frame"}}
    tracks = {0: {"translation": [(1., 2., 3.), (1., 2., 3.)],
                  "rotation": [(0., 0., 0., 1.), (0., 0., .6, .8)]}}
    rows = {(0, 0): {"max_endpoint_position_error_m": .001,
                     "max_endpoint_unit_quaternion_error": .001}}
    return reference, geometry, tracks, positions, rows


class IndependentPositionReceiptTests(unittest.TestCase):
    def run_keys(self, *, reuse=True, limits=True):
        reference, geometry, tracks, _, rows = inputs()
        work = Work()
        arithmetic = _Bounds(work, cache_intermediates=False)
        prior = _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic,
                                 endpoint_rows=rows if limits else None)
        before = work.operations
        context = (patch("ontokin.reach_conformance._previous_position_comparison", return_value=None)
                   if not reuse else patch("ontokin.reach_conformance._previous_position_comparison",
                                            wraps=_previous_position_comparison))
        with context:
            result = _key_comparisons(reference, geometry, tracks, F(1), 1, arithmetic,
                previous=prior, previous_time=F(0), endpoint_rows=rows if limits else None)
        return result, work.operations - before, work

    def test_changed_orientation_reuses_exact_position_error_and_magnitude(self):
        for limits in (True, False):
            with self.subTest(limits=limits):
                reused, cost, work = self.run_keys(limits=limits)
                fresh, direct_cost, _ = self.run_keys(reuse=False, limits=limits)
                self.assertEqual(reused, fresh)
                self.assertEqual(reused[0]["position_error"], 0)
                self.assertEqual(reused[0]["magnitude"], 6)
                self.assertLess(cost, direct_cost)
                self.assertLessEqual(work.record()["cache_entries"], 256)
                self.assertEqual(work.max_operations, 100000)

    def test_current_buffer_source_cells_and_claim_are_part_of_position_identity(self):
        for change in ("buffer", "source", "claim", "claim_type"):
            reference, geometry, tracks, positions, rows = inputs()
            arithmetic = _Bounds(Work(), cache_intermediates=False)
            prior = _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic, endpoint_rows=rows)
            if change == "buffer":
                tracks[0]["translation"][1] = (1.0001, 2., 3.)
            elif change == "source":
                positions[1] = (point(F(10001, 10000)), point(2), point(3))
            elif change == "claim":
                rows[0, 0]["max_endpoint_position_error_m"] = .0001
            else:
                rows[0, 0]["max_endpoint_position_error_m"] = 0
            actual = []
            def inspect(*args):
                value = _previous_position_comparison(*args)
                actual.append(value)
                return value
            with self.subTest(change=change), \
                    patch("ontokin.reach_conformance._previous_position_comparison", side_effect=inspect):
                result = _key_comparisons(reference, geometry, tracks, F(1), 1, arithmetic,
                    previous=prior, previous_time=F(0), endpoint_rows=rows)
            self.assertTrue(actual)
            self.assertTrue(all(value is None for value in actual))
            if change in ("buffer", "source"):
                self.assertGreater(result[0]["position_error"], 0)

    def test_receipt_never_hides_invalid_current_components_or_source_intervals(self):
        reference, geometry, tracks, positions, rows = inputs()
        arithmetic = _Bounds(Work(), cache_intermediates=False)
        prior = _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic, endpoint_rows=rows)
        for value in ((True, 2., 3.), (float("nan"), 2., 3.), (1., 2.)):
            tracks[0]["translation"][1] = value
            with self.subTest(value=value), self.assertRaises(OntoKinError):
                _key_comparisons(reference, geometry, tracks, F(1), 1, arithmetic,
                    previous=prior, previous_time=F(0), endpoint_rows=rows)
        tracks[0]["translation"][1] = (1., 2., 3.)
        for cells in ((_Cell(F(2), F(1)), point(2), point(3)),
                      (_Cell(True, F(1)), point(2), point(3)),
                      (point(1), point(2))):
            positions[1] = cells
            with self.subTest(cells=cells), self.assertRaises((OntoKinError, TypeError, ValueError)):
                _key_comparisons(reference, geometry, tracks, F(1), 1, arithmetic,
                    previous=prior, previous_time=F(0), endpoint_rows=rows)

    def test_changed_cap_and_original_callback_are_checked_before_receipt_return(self):
        reference, geometry, tracks, positions, rows = inputs()
        work = Work()
        arithmetic = _Bounds(work, cache_intermediates=False)
        prior = _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic, endpoint_rows=rows)[0]
        work.max_operand_bits = 128
        self.assertIsNone(_previous_position_comparison(prior, (1., 2., 3.), positions[1], .001, arithmetic))
        work.max_operand_bits = 32768
        saved = deepcopy(prior)
        marker = RuntimeError("cancel before independent position receipt")
        original = work.charge
        def charge(kind="checkpoint", amount=1):
            if kind == "independent_position_key_reuse":
                with patch.object(work, "external_check", side_effect=marker):
                    return original(kind, amount)
            return original(kind, amount)
        with patch.object(work, "charge", side_effect=charge), self.assertRaises(RuntimeError) as caught:
            _previous_position_comparison(prior, (1., 2., 3.), positions[1], .001, arithmetic)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(prior, saved)

    def test_cap_narrowed_inside_reuse_abandons_the_old_proof(self):
        reference, geometry, tracks, positions, rows = inputs()
        work = Work()
        arithmetic = _Bounds(work, cache_intermediates=False)
        prior = _key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic, endpoint_rows=rows)[0]
        original = work.charge
        def charge(kind="checkpoint", amount=1):
            value = original(kind, amount)
            if kind == "independent_position_key_reuse":
                work.max_operand_bits = 128
            return value
        with patch.object(work, "charge", side_effect=charge):
            self.assertIsNone(_previous_position_comparison(prior, (1., 2., 3.), positions[1], .001, arithmetic))


if __name__ == "__main__":
    unittest.main()
