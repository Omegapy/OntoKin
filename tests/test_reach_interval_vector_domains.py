"""Batched interval admission keeps the complete supplied-byte proof exact."""
from contextlib import nullcontext
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb
from ontokin.reach_conformance import _Bounds, _Cell, _recording_orientation_comparison
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_reference import Interval
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def scalar_cells(arithmetic, values):
    return tuple(arithmetic.cell(value) for value in values)


def point(value, kind=_Cell):
    return kind(F(value), F(value))


class IndependentIntervalVectorDomainTests(unittest.TestCase):
    def test_local_reference_and_mixed_vectors_match_scalar_admission(self):
        for size in (3, 4):
            for types in ((_Cell,) * size, (Interval,) * size,
                          tuple(_Cell if index % 2 else Interval for index in range(size))):
                values = tuple(kind(F(index - 2, 7), F(index + 1, 5))
                               for index, kind in enumerate(types))
                with self.subTest(size=size, types=types):
                    work, scalar_work = ReachExecutionWork(), ReachExecutionWork()
                    actual = _Bounds(work).cells(values)
                    expected = scalar_cells(_Bounds(scalar_work), values)
                    self.assertEqual(actual, expected)
                    self.assertTrue(all(type(value) is _Cell for value in actual))
                    self.assertEqual(work.operations, 1)
                    self.assertEqual(scalar_work.operations, size)
                    self.assertEqual(work.counts, {"independent_interval_vector_domain": 1})
                    self.assertEqual(work.record()["cache_entries"], 0)

    def test_other_shapes_and_untrusted_cell_types_keep_scalar_decoding(self):
        values = (SimpleNamespace(lo=F(0), hi=F(1)),
                  SimpleNamespace(lo=-.5, hi=1), F(2))
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        with patch.object(arithmetic, "cell", wraps=arithmetic.cell) as cell:
            self.assertEqual(arithmetic.cells(values),
                             scalar_cells(_Bounds(ReachExecutionWork()), values))
        self.assertEqual(cell.call_count, 3)
        self.assertNotIn("independent_interval_vector_domain", work.counts)
        with patch.object(arithmetic, "cell", wraps=arithmetic.cell) as cell:
            self.assertEqual(arithmetic.cells((point(0), point(1))), (point(0), point(1)))
        self.assertEqual(cell.call_count, 2)

    def test_difference_and_orientation_results_are_identical_to_scalar_path(self):
        cases = [((point(0), point(1), point(2)),
                  (Interval(F(-1, 7), F(1, 7)), point(1), point(2))),
                 ((point(F(-3, 5)), point(F(4, 5)), point(0)),
                  (point(0), point(0), point(0)))]
        for first, last in cases:
            with self.subTest(first=first, last=last):
                work, scalar_work = ReachExecutionWork(), ReachExecutionWork()
                actual = _Bounds(work).difference(first, last)
                with patch.object(_Bounds, "cells", scalar_cells):
                    expected = _Bounds(scalar_work).difference(first, last)
                self.assertEqual(actual, expected)
                self.assertLess(work.operations, scalar_work.operations)
        raw = (0., 0., -.6, -.8)
        source = tuple(Interval(F(value), F(value)) for value in raw)
        work, scalar_work = ReachExecutionWork(), ReachExecutionWork()
        actual = _recording_orientation_comparison(raw, source, _Bounds(work))
        with patch.object(_Bounds, "cells", scalar_cells):
            expected = _recording_orientation_comparison(raw, source, _Bounds(scalar_work))
        self.assertEqual(actual, expected)
        self.assertLess(work.operations, scalar_work.operations)

    def test_malformed_and_oversized_components_keep_left_to_right_error_order(self):
        huge, reversed_cell = point(F(1 << 80)), _Cell(F(1), F(0))
        cases = ((huge, reversed_cell, point(0)),
                 (reversed_cell, huge, point(0)),
                 (_Cell(F(1, 1 << 40), F(1 << 30)), reversed_cell, point(0)),
                 (_Cell(False, F(1)), huge, point(0)))
        for values in cases:
            outcomes = []
            for scalar in (False, True):
                arithmetic = _Bounds(ReachExecutionWork(max_operand_bits=64))
                context = patch.object(_Bounds, "cells", scalar_cells) if scalar else nullcontext()
                with self.subTest(values=values, scalar=scalar), context:
                    try:
                        arithmetic.cells(values)
                    except ReachAdmissionError as error:
                        outcomes.append((type(error), error.details))
                    except OntoKinError as error:
                        outcomes.append((type(error), error.diagnostic.details))
                    else:
                        self.fail("invalid interval vector was admitted")
            self.assertEqual(outcomes[0], outcomes[1])

    def test_changed_warm_operand_and_shape_are_rechecked_before_cache_lookup(self):
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        vector = (point(0), point(1), point(2))
        arithmetic.difference(vector, vector)
        for changed in ((point(0), _Cell(F(2), F(1)), point(2)),
                        (point(0), point(F(1 << 32768)), point(2)),
                        (point(0), _Cell(False, F(1)), point(2)),
                        vector[:2]):
            with self.subTest(changed=changed), patch.object(work, "lookup", wraps=work.lookup) as lookup:
                with self.assertRaises((OntoKinError, ReachAdmissionError)):
                    arithmetic.difference(changed, vector)
                lookup.assert_not_called()

    def test_callback_narrowing_checks_every_component_and_comparison_extent(self):
        for changed in (point(F(1 << 80)), _Cell(F(1, 1 << 40), F(1 << 30))):
            for position in range(4):
                work = ReachExecutionWork()
                values = [point(0)] * 4
                values[position] = changed
                def narrow():
                    work.max_operand_bits = 64
                work.external_check = narrow
                with self.subTest(position=position, changed=changed), self.assertRaises(ReachAdmissionError) as caught:
                    _Bounds(work).cells(values)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                self.assertEqual(caught.exception.details["limit"], 64)
                self.assertEqual(work.operations, 1)
        work = ReachExecutionWork()
        work.external_check = lambda: setattr(work, "max_operand_bits", 64)
        self.assertEqual(_Bounds(work).cells((point(0), point(1), point(2))),
                         (point(0), point(1), point(2)))

    def test_cancelled_vector_admission_preserves_original_exception_and_cache(self):
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        vector = (point(0), point(1), point(2))
        arithmetic.difference(vector, vector)
        before = tuple(work._cache.items())
        marker = RuntimeError("cancel complete independent vector admission")
        with patch.object(work, "external_check", side_effect=marker), \
             patch.object(work, "lookup", wraps=work.lookup) as lookup:
            with self.assertRaises(RuntimeError) as caught:
                arithmetic.difference(vector, vector)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(tuple(work._cache.items()), before)
        lookup.assert_not_called()

    def test_repeated_vectors_keep_the_existing_bounded_cache_and_narrow_cap(self):
        work = ReachExecutionWork(max_cache_entries=3)
        arithmetic = _Bounds(work)
        for index in range(10):
            first = (point(index), point(0), point(0))
            last = (point(0), point(0), point(0))
            self.assertEqual(arithmetic.difference(first, last), F(index))
            self.assertLessEqual(work.record()["cache_entries"], 3)
        # The current domain is checked before a cached comparison can be used.
        first = (point(F(1 << 80)), point(0), point(0))
        self.assertEqual(arithmetic.difference(first, first), 0)
        work.max_operand_bits = 64
        with self.assertRaises(ReachAdmissionError):
            arithmetic.difference(first, first)
        self.assertEqual(work.max_operations, 100000)

    def test_actual_source_glb_bytes_and_validation_match_scalar_admission(self):
        results = []
        for scalar in (False, True):
            built = compile_construction(source_case("P01"))
            context = patch.object(_Bounds, "cells", scalar_cells) if scalar else nullcontext()
            with context:
                result = export_glb(built.model,
                    options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertEqual(built.reach_work.max_operations, 100000)
            self.assertLessEqual(built.budget.operations, 100000)
            results.append((result, built.budget.operations))
        self.assertEqual(results[0][0].data, results[1][0].data)
        self.assertEqual(results[0][0].report["validation"], results[1][0].report["validation"])
        self.assertLess(results[0][1], results[1][1])


if __name__ == "__main__":
    unittest.main()
