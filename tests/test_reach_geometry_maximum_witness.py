"""An attaining source point eliminates only identical exact L1 sums."""
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.geometry import box_mesh
from ontokin import reach_conformance as reader
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.scene import float32


def stored(points):
    return [tuple(float32(value) for value in point) for point in points]


class GeometryMaximumWitnessTests(unittest.TestCase):
    def test_box_repeated_maxima_preserve_exact_extrema_with_less_actual_arithmetic(self):
        points = box_mesh((.2, .3, .4)).positions
        actual = stored(points)
        outcomes, costs, caches = [], [], []
        for reuse in (False, True):
            work = Work()
            # Only disable the optional attaining-point predicate; all scalar
            # operations and their original full-cap guards remain unchanged.
            mode = patch.object(reader, '_bound_domain', return_value=32767) if not reuse else patch.object(
                reader, '_bound_domain', wraps=reader._bound_domain)
            with mode:
                outcomes.append(reader._vertex_extrema_uncached(points, actual, work=work))
            costs.append(work.operations)
            self.assertEqual(work.operations, sum(work.counts.values()))
            caches.append(tuple(work._cache.items()))
        self.assertEqual(outcomes[0], outcomes[1])
        # The original final norm enclosure may populate its bounded cache.
        # The attaining-point witness introduces no different entry or value.
        self.assertEqual(caches[0], caches[1])
        self.assertEqual(outcomes[1][0], sum((abs(F(v)) for v in points[0]), F(0)))
        self.assertLess(costs[1], costs[0])

    def test_changed_component_order_and_new_maxima_receive_the_original_exact_sum(self):
        points = ((.1, .2, .3), (-.1, -.2, -.3), (.3, .2, .1),
                  (.3, .2, .10000000000000002), (-.3, -.2, -.10000000000000002))
        actual = stored(points)
        result = reader._vertex_extrema_uncached(points, actual, work=Work())
        self.assertEqual(result[0], max(sum((abs(F(v)) for v in point), F(0)) for point in points))
        with patch.object(reader, '_bound_domain', return_value=32767):
            original = reader._vertex_extrema_uncached(points, actual, work=Work())
        self.assertEqual(result, original)

    def test_each_repeated_vertex_still_checks_its_actual_supplied_bytes(self):
        points = box_mesh((.2, .3, .4)).positions
        for index in (1, len(points) // 2, len(points) - 1):
            actual = stored(points)
            actual[index] = (float32(.9), *actual[index][1:])
            with self.subTest(index=index), self.assertRaises(OntoKinError) as caught:
                reader._vertex_extrema_uncached(points, actual, work=Work())
            self.assertEqual(caught.exception.diagnostic.details['export_code'], 'OKE-E-GEOMETRY')

    def test_live_narrowing_at_a_repeated_point_keeps_the_original_failure(self):
        points = ((.1, .2, .3),) * 3
        work, index = Work(), 0
        charge = work.charge
        def narrow(kind='checkpoint', amount=1):
            nonlocal index
            if kind == 'independent_geometry_point':
                index += 1
                if index == 2:
                    work.max_operand_bits = 32
            return charge(kind, amount)
        with patch.object(work, 'charge', side_effect=narrow), self.assertRaises(ReachAdmissionError) as caught:
            reader._vertex_extrema_uncached(points, stored(points), work=work)
        with self.assertRaises(ReachAdmissionError) as original:
            reader._vertex_extrema_uncached(points[1:], stored(points[1:]), work=Work(max_operand_bits=32))
        self.assertEqual(caught.exception.details, original.exception.details)
        self.assertEqual(index, 2)

    def test_cancellation_at_a_repeated_point_keeps_exception_identity_and_inputs(self):
        points = ((.1, .2, .3),) * 3
        actual = stored(points)
        work, index = Work(), 0
        marker, charge = RuntimeError('cancel repeated source vertex'), work.charge
        def interrupt(kind='checkpoint', amount=1):
            nonlocal index
            if kind == 'independent_geometry_point':
                index += 1
                if index == 2:
                    work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(work, 'charge', side_effect=interrupt), self.assertRaises(RuntimeError) as caught:
            reader._vertex_extrema_uncached(points, actual, work=work)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(actual, stored(points))
        self.assertFalse(work._cache)

    def test_nonfinite_and_nonnative_inputs_cannot_borrow_a_float_maximum(self):
        points = ((.1, .2, .3),) * 3
        rational = tuple(tuple(F(v) for v in row) for row in points)
        self.assertEqual(reader._vertex_extrema_uncached(rational, stored(points), work=Work()),
                         reader._vertex_extrema_uncached(points, stored(points), work=Work()))
        for value in (math.inf, math.nan):
            source = (points[0], (value, .2, .3))
            with self.subTest(value=value), self.assertRaises((OntoKinError, ValueError)):
                reader._vertex_extrema_uncached(source, stored(points[:2]), work=Work())


if __name__ == '__main__':
    unittest.main()
