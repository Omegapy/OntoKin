"""Focused tests for the two-cart passage checker. Run this module directly."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_passage as passage


def corner_clearance(offset, size=1.0):
    # Two equal boxes. At 7/25 of the interval the X and Y gaps equal offset.
    step = size * 2**-16
    moving = [(size + 7 * step + offset, size - 7 * step + offset, 0),
              (size - 18 * step + offset, size + 18 * step + offset, 0)]
    origin = (0, 0, 0)
    box = (origin, (size, size, size))
    tracks = {('parked', 'translation'): [origin, origin],
              ('moving', 'translation'): moving}
    return passage.parked_clearance([0, 1], tracks, {'parked': box, 'moving': box},
                                    'parked', 'moving')


class ParkedClearanceTests(unittest.TestCase):
    def test_corner_contact_between_keys(self):
        with self.assertRaisesRegex(ValueError, 'lacks positive separation'):
            corner_clearance(0)

    def test_corner_overlap_between_keys(self):
        with self.assertRaisesRegex(ValueError, 'lacks positive separation'):
            corner_clearance(-2**-22)

    def test_small_positive_gap_is_preserved(self):
        # Scaling by a power of two keeps the input coordinates exactly binary32.
        size = 2**-24
        gap = size * 2**-22
        result = corner_clearance(gap, size)
        self.assertEqual(result['separation_lower_bound_m'], gap)
        self.assertAlmostEqual(result['time_of_min_s'], 7 / 25)


class SiblingGeometryTests(unittest.TestCase):
    def test_mesh_comparison_preserves_local_triangles_and_multiplicity(self):
        a, b, c, d = (0, 0, 0), (2, 0, 0), (0, 1, 0), (2, 1, 0)
        compare = passage.local_triangle_counts
        expected = compare([[a, b, c, b, d, c]])
        # Primitive grouping, face order and winding do not alter these surfaces.
        self.assertEqual(expected, compare([[c, d, b], [c, b, a]]))
        # The same bounds and vertex set can describe different triangles.
        self.assertNotEqual(expected, compare([[a, b, d, a, d, c]]))
        self.assertNotEqual(expected, compare([[a, b, c, b, d, c, b, d, c]]))


if __name__ == '__main__':
    unittest.main()
