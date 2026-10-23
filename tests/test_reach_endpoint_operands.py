"""Current endpoint operands share exact decodes without sharing a pose proof."""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def cells(values, width=F(0)):
    return tuple(reader._Cell(F(value) - width, F(value) + width) for value in values)


@contextmanager
def repeated_operand_admission():
    original = reader._optional_endpoint_l1
    def ordinary(actual, expected, arithmetic, *, admitted_cells=False):
        return original(actual, expected, arithmetic)
    with patch.object(reader, "_PositionOperands", lambda arithmetic, position: arithmetic), \
            patch.object(reader, "_optional_endpoint_l1", ordinary):
        yield


class ReachEndpointOperandTests(unittest.TestCase):
    def test_complete_endpoint_results_equal_repeated_decodes_and_admission(self):
        def run(repeated):
            work = Work()
            arithmetic = reader._Bounds(work, cache_intermediates=False)
            geometry = {index: {"frame": str(index)} for index in range(3)}
            positions = {index: (float(index) + 1.25, -2.5, 3.75) for index in geometry}
            tracks = {index: {"translation": [positions[index]],
                              "rotation": [(0., 0., .6, .8 + 2. ** -24)]} for index in geometry}
            rows = {(0, index): {"max_endpoint_position_error_m": .001,
                                "max_endpoint_unit_quaternion_error": 1e-5} for index in geometry}
            reference = SimpleNamespace(recording_pose_enclosures=lambda carriers, time, side,
                recording_context=None: {frame: SimpleNamespace(
                    position=cells(positions[int(frame)], F(1, 1 << 80)),
                    orientation=cells((F(4, 5), 0, 0, F(3, 5)))) for frame in carriers})
            if repeated:
                with repeated_operand_admission():
                    result = reader._key_comparisons(reference, geometry, tracks, F(0), 0,
                                                    arithmetic, endpoint_rows=rows)
            else:
                result = reader._key_comparisons(reference, geometry, tracks, F(0), 0,
                                                arithmetic, endpoint_rows=rows)
            self.assertLessEqual(len(work._cache), 256)
            self.assertEqual(work.operations, sum(work.counts.values()))
            self.assertEqual(work.max_operations, 100000)
            return result, work.operations, work.counts
        result, cost, counts = run(False)
        expected, repeated_cost, repeated_counts = run(True)
        self.assertEqual(result, expected)
        self.assertGreaterEqual(repeated_cost - cost, 10)
        self.assertEqual(repeated_counts["independent_bound_decode"] - counts["independent_bound_decode"], 9)
        self.assertEqual(repeated_counts["independent_interval_vector_domain"] -
                         counts["independent_interval_vector_domain"], 1)

    def test_position_magnitude_reuses_only_completed_native_coordinate_ratios(self):
        position = (1.25, -2.5, 3.75)
        work = Work()
        arithmetic = reader._Bounds(work)
        view = reader._PositionOperands(arithmetic, position)
        error = reader._recording_position_bound(position, cells(position, F(1, 1 << 80)), .001, view)
        self.assertEqual(error, F(3, 1 << 80))
        before = work.counts.get("independent_bound_decode", 0)
        self.assertEqual(reader._recording_position_magnitude(position, view), F(15, 2))
        self.assertEqual(work.counts.get("independent_bound_decode", 0), before)
        self.assertFalse(work._cache)
        changed = (1.5, -2.5, 3.75)
        self.assertEqual(reader._recording_position_magnitude(changed, view), F(31, 4))
        self.assertEqual(work.counts["independent_bound_decode"], before + 1)
        changed_error = reader._recording_position_bound(position, cells((1., -2.5, 3.75)), .5, view)
        self.assertEqual(changed_error, F(1, 4))
        arithmetic.work = Work()
        self.assertEqual(reader._recording_position_magnitude(position, view), F(15, 2))
        self.assertEqual(arithmetic.work.counts["independent_bound_decode"], 3)

    def test_cap_narrowing_before_magnitude_replays_original_scalar_preflights(self):
        position = (float(1 << 63), 0., 0.)
        expected = reader._Bounds(Work(max_operand_bits=64))
        with self.assertRaises(ReachAdmissionError) as original_error:
            reader._recording_position_magnitude(position, expected)
        work = Work()
        view = reader._PositionOperands(reader._Bounds(work), position)
        reader._recording_position_bound(position, cells(position), .001, view)
        charge = work.charge
        def narrow(kind="checkpoint", amount=1):
            if kind == "independent_position_magnitude":
                work.max_operand_bits = 64
            return charge(kind, amount)
        with patch.object(work, "charge", narrow), self.assertRaises(ReachAdmissionError) as actual_error:
            reader._recording_position_magnitude(position, view)
        self.assertEqual(actual_error.exception.details, original_error.exception.details)

    def test_cancelled_later_magnitude_keeps_original_error_and_completed_cache(self):
        work = Work()
        view = reader._PositionOperands(reader._Bounds(work), (1.25, -2.5, 3.75))
        reader._recording_position_bound(view.position, cells(view.position), .001, view)
        saved = deepcopy(work._cache)
        marker = RuntimeError("cancel after completed coordinate decodes")
        charge = work.charge
        def cancel(kind="checkpoint", amount=1):
            if kind == "independent_position_magnitude":
                with patch.object(work, "external_check", side_effect=marker):
                    return charge(kind, amount)
            return charge(kind, amount)
        with patch.object(work, "charge", cancel), self.assertRaises(RuntimeError) as caught:
            reader._recording_position_magnitude(view.position, view)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(work._cache, saved)

    def test_admitted_cell_path_retains_complete_live_source_guards(self):
        expected = cells((1, 0, 0), F(1, 1 << 200))
        errors = []
        for admitted in (False, True):
            work = Work()
            charge = work.charge
            def narrow(kind="checkpoint", amount=1):
                if kind == "independent_bound_decode":
                    work.max_operand_bits = 128
                return charge(kind, amount)
            with self.subTest(admitted=admitted), patch.object(work, "charge", narrow), \
                    self.assertRaises(ReachAdmissionError) as caught:
                reader._optional_endpoint_l1((1., 0., 0.), expected, reader._Bounds(work),
                                             admitted_cells=admitted)
            errors.append(caught.exception.details)
        self.assertEqual(errors[0], errors[1])
        self.assertEqual(errors[0]["limit"], 128)

    def test_foreign_reversed_or_changed_cells_cannot_borrow_admission(self):
        for expected in ((reader._Cell(F(2), F(1)), *cells((0, 0))),
                         (reader._Cell(True, F(1)), *cells((0, 0))),
                         cells((1 << 32768, 0, 0))):
            outcomes = []
            for admitted in (False, True):
                with self.subTest(admitted=admitted, expected=expected), \
                        self.assertRaises((OntoKinError, ReachAdmissionError)) as caught:
                    reader._optional_endpoint_l1((1., 0., 0.), expected, reader._Bounds(Work()),
                                                 admitted_cells=admitted)
                error = caught.exception
                outcomes.append(error.details if isinstance(error, ReachAdmissionError)
                                else error.diagnostic.details)
            self.assertEqual(outcomes[0], outcomes[1])
        foreign = (SimpleNamespace(lo=F(1), hi=F(1)), *cells((0, 0)))
        self.assertEqual(reader._optional_endpoint_l1((1., 0., 0.), foreign, reader._Bounds(Work()),
                                                     admitted_cells=True), 0)

    def test_small_native_claim_implies_half_bound_without_redundant_comparison(self):
        raw, source = (0., 0., 0., 1.), cells((0, 0, 0, 1))
        for limit, count in ((0, 1), (0., 1), (1e-5, 1), (.5, 1),
                             (1, 2), (1., 2), (F(1, 2), 2), (F(0), 2)):
            arithmetic = reader._Bounds(Work())
            with self.subTest(limit=limit, kind=type(limit)), \
                    patch.object(arithmetic, "compare", wraps=arithmetic.compare) as compare:
                actual = reader._recording_orientation_bound(raw, source, limit, arithmetic)
            self.assertEqual(actual, (None, F(0)))
            self.assertEqual(compare.call_count, count)

    def test_current_position_callback_still_follows_orientation_admission(self):
        for warm in (False, True):
            work = Work()
            arithmetic = reader._Bounds(work)
            raw, source = (0., 0., .6, .8), cells((0, 0, F(3, 5), F(4, 5)))
            if warm:
                reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
            marker = RuntimeError("current position failure")
            observed = []
            def fail_position():
                observed.append("position")
                raise marker
            with self.subTest(warm=warm), self.assertRaises(RuntimeError) as caught:
                reader._recording_orientation_bound(raw, source, 1e-5, arithmetic,
                                                    before_error=fail_position)
            self.assertIs(caught.exception, marker)
            self.assertEqual(observed, ["position"])

    def test_invalid_current_stored_operands_never_use_completed_ratios(self):
        work = Work()
        view = reader._PositionOperands(reader._Bounds(work), (1., 2., 3.))
        reader._recording_position_bound(view.position, cells(view.position), .001, view)
        for bad in ((True, 2., 3.), (float("nan"), 2., 3.), (float("inf"), 2., 3.), (1., 2.)):
            with self.subTest(bad=bad), self.assertRaises(OntoKinError):
                reader._recording_position_magnitude(bad, view)
        with patch.object(work, "external_check", side_effect=RuntimeError("first checkpoint")):
            with self.assertRaisesRegex(RuntimeError, "first checkpoint"):
                reader._recording_position_magnitude(view.position, view)


if __name__ == "__main__":
    unittest.main()
