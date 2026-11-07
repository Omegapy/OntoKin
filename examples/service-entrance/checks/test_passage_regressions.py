"""Focused tests for the two-cart passage checker. Run this module directly."""

from pathlib import Path
from itertools import product
from fractions import Fraction
import struct
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
    def test_quarter_turn_preserves_contact_and_small_gap(self):
        # Equal binary32 Y and W components encode an exact quarter turn.
        c = 0.7071067690849304
        rotation = (0., c, 0., c)
        opposite = tuple(-value for value in rotation)
        corners = list(product((-.25, .25), (-.25, .25), (0., 1.)))
        parked = passage.exact_rotated_bounds([corners], [rotation, opposite])
        self.assertEqual(parked, [[0, -.25, -.25], [1, .25, .25]])
        moving = [[-.25, -.25, 0], [.25, .25, 1]]
        bounds = {'parked': parked, 'moving': moving}
        tracks = {('parked', 'translation'): [(0, 0, 0)] * 2,
                  ('moving', 'translation'): [(1.25, 0, 0)] * 2}
        with self.assertRaisesRegex(ValueError, 'lacks positive separation'):
            passage.parked_clearance([0, 1], tracks, bounds, 'parked', 'moving')
        gap = 2**-23
        tracks['moving', 'translation'] = [(1.25 + gap, 0, 0)] * 2
        result = passage.parked_clearance([0, 1], tracks, bounds, 'parked', 'moving')
        self.assertEqual(result['separation_lower_bound_m'], gap)

    def test_rotation_uses_the_ratio_of_the_stored_components(self):
        # For rotation about Z, an X-axis unit vector maps to (w²-z², 2wz)/(w²+z²).
        z, w = 0.6000000238418579, 0.800000011920929
        rotation = (0, 0, z, w)
        z, w = Fraction(z), Fraction(w)
        norm = w*w + z*z
        expected = [(w*w - z*z)/norm, 2*w*z/norm, 0]
        bounds = passage.exact_rotated_bounds([[(1, 0, 0)]], [rotation])
        self.assertEqual(bounds, [expected, expected])

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
    def test_mesh_reader_rejects_instance_transforms(self):
        points = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        binary = b''.join(struct.pack('<3f', *p) for p in points)
        graph = {
            'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
            'accessors': [{'bufferView': 0, 'type': 'VEC3', 'componentType': 5126, 'count': 3}],
            'bufferViews': [{'buffer': 0, 'byteLength': len(binary)}],
        }
        node = {'mesh': 0, 'extras': {'label': 'cart'}}
        self.assertEqual(passage.gate.surfaces(graph, binary, node), [points])
        node['extensions'] = {'EXT_mesh_gpu_instancing': {'attributes': {'TRANSLATION': 0}}}
        with self.assertRaisesRegex(ValueError, 'mesh instancing'):
            passage.gate.surfaces(graph, binary, node)

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
