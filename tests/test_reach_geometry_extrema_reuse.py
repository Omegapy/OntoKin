"""Actual accessor checks remain mandatory when pure mesh extrema are reused."""
import math
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import _vertex_extrema, _vertex_extrema_uncached
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.scene import float32


def inputs(offset=0.):
    points = tuple((float(index % 17) / 100 + offset, -.1, -0.) for index in range(385))
    return points, [tuple(float32(value) for value in row) for row in points]


class VertexExtremaReuseTests(unittest.TestCase):
    def test_warm_reuse_is_exact_and_checks_all_actual_blocks(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        expected = _vertex_extrema_uncached(points, stored, work=ReachExecutionWork())
        self.assertEqual(_vertex_extrema(points, stored, work=work), expected)
        before = work.operations
        with patch("ontokin.reach_conformance._vertex_extrema_uncached",
                   side_effect=AssertionError("Repeated pure geometry arithmetic")):
            self.assertEqual(_vertex_extrema(points, list(stored), work=work), expected)
        self.assertEqual(work.counts["independent_geometry_reuse_block"], 4)
        self.assertLess(work.operations - before, len(points) // 8)
        self.assertLessEqual(work.record()["cache_entries"], 256)

    def test_every_mutated_block_and_last_vertex_is_rejected(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        _vertex_extrema(points, stored, work=work)
        for index in (0, 127, 128, 255, 256, 383, 384):
            changed = list(stored)
            changed[index] = (.9, *changed[index][1:])
            with self.subTest(index=index), self.assertRaises(OntoKinError) as raised:
                _vertex_extrema(points, changed, work=work)
            self.assertEqual(raised.exception.diagnostic.details["export_code"], "OKE-E-GEOMETRY")

    def test_signed_zero_keeps_existing_float_equality(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        expected = _vertex_extrema(points, stored, work=work)
        alternate = [(x, y, -0.) for x, y, z in stored]
        self.assertEqual(_vertex_extrema(points, alternate, work=work), expected)

    def test_malformed_or_nonfinite_actual_rows_never_reuse_the_proof(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        _vertex_extrema(points, stored, work=work)
        for row in ((0.,), (0., -.1, math.nan), (0., -.1, math.inf)):
            changed = list(stored)
            changed[-1] = row
            with self.subTest(row=row), self.assertRaises(OntoKinError):
                _vertex_extrema(points, changed, work=work)

    def test_distinct_source_identity_reproves_and_mutable_sources_use_scalar_path(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        expected = _vertex_extrema(points, stored, work=work)
        clone = tuple(list(points))
        self.assertIsNot(clone, points)
        with patch("ontokin.reach_conformance._vertex_extrema_uncached",
                   wraps=_vertex_extrema_uncached) as scalar:
            self.assertEqual(_vertex_extrema(clone, stored, work=work), expected)
            self.assertEqual(scalar.call_count, 1)
            self.assertEqual(_vertex_extrema(list(points), stored, work=work), expected)
            self.assertEqual(scalar.call_count, 2)

    def test_small_and_nonnative_inputs_retain_exact_fallback(self):
        from fractions import Fraction
        points, stored = inputs()
        rational = tuple(tuple(Fraction(value) for value in row) for row in points)
        for source, actual in ((points[:3], stored[:3]), (rational, stored)):
            with self.subTest(size=len(source)):
                self.assertEqual(_vertex_extrema(source, actual, work=ReachExecutionWork()),
                                 _vertex_extrema_uncached(source, actual, work=ReachExecutionWork()))

    def test_narrow_domain_reestablishes_original_intermediate_guards(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        _vertex_extrema(points, stored, work=work)
        work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as warm:
            _vertex_extrema(points, stored, work=work)
        with self.assertRaises(ReachAdmissionError) as cold:
            _vertex_extrema_uncached(points, stored, work=ReachExecutionWork(max_operand_bits=128))
        self.assertEqual(warm.exception.details, cold.exception.details)

    def test_callback_cap_changes_at_lookup_block_and_publication_reprove(self):
        points, stored = inputs()
        for trigger, warm in (("cache_lookup", True), ("cache_promote", True),
                              ("independent_geometry_reuse_block", True),
                              ("independent_geometry_proof_block", False), ("cache_insert", False)):
            work = ReachExecutionWork()
            if warm:
                _vertex_extrema(points, stored, work=work)
            original = work.charge
            fired = False

            def charge(kind="checkpoint", amount=1):
                nonlocal fired
                if kind == trigger and not fired:
                    fired = True
                    work.max_operand_bits = 128
                return original(kind, amount)

            work.charge = charge
            with self.subTest(trigger=trigger), self.assertRaises(ReachAdmissionError):
                _vertex_extrema(points, stored, work=work)
            self.assertTrue(fired)

    def test_original_callback_exception_survives_warm_reuse(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        _vertex_extrema(points, stored, work=work)
        marker = RuntimeError("cancel before reused geometry")
        work.external_check = lambda: (_ for _ in ()).throw(marker)
        before = tuple(work._cache.items())
        with self.assertRaises(RuntimeError) as raised:
            _vertex_extrema(points, stored, work=work)
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(tuple(work._cache.items()), before)

    def test_operand_cap_change_in_geometry_cache_publication_reproves(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        original = work.remember
        fired = False

        def remember(key, value):
            nonlocal fired
            if key[0] == "reach_independent_vertex_extrema_v1":
                fired = True
                work.max_operand_bits = 128
            return original(key, value)

        work.remember = remember
        with self.assertRaises(ReachAdmissionError):
            _vertex_extrema(points, stored, work=work)
        self.assertTrue(fired)

    def test_cold_callback_mutation_cannot_publish_unchecked_vertices(self):
        points, stored = inputs()
        work = ReachExecutionWork()
        original = work.charge

        def charge(kind="checkpoint", amount=1):
            if kind == "independent_geometry_proof_block":
                stored[-1] = (.9, 0., 0.)
            return original(kind, amount)

        work.charge = charge
        with self.assertRaises(OntoKinError):
            _vertex_extrema(points, stored, work=work)
        self.assertFalse(any(key[0] == "reach_independent_vertex_extrema_v1" for key in work._cache))

    def test_existing_lru_eviction_recomputes_without_a_second_table(self):
        work = ReachExecutionWork(max_cache_entries=3)
        points, stored = inputs()
        expected = _vertex_extrema(points, stored, work=work)
        for offset in (.1, .2, .3, .4):
            other, actual = inputs(offset)
            _vertex_extrema(other, actual, work=work)
            self.assertLessEqual(work.record()["cache_entries"], 3)
        with patch("ontokin.reach_conformance._vertex_extrema_uncached",
                   wraps=_vertex_extrema_uncached) as scalar:
            self.assertEqual(_vertex_extrema(points, stored, work=work), expected)
            self.assertEqual(scalar.call_count, 1)


if __name__ == "__main__":
    unittest.main()
