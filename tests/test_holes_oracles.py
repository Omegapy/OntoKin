"""Hostile controls built from a hand-divided square plate with an opening.

No source compiler, runtime exporter or triangulator supplies the test mesh.
The eight cap triangles are four independently specified rectangular bands.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import unittest

from tools.holes_oracles import Decoded, check_geometry, _overlap_area2


FIXTURES = Path(__file__).resolve().parents[1] / 'examples/polygon-holes'
EXPECTED = json.loads((FIXTURES / 'expected.json').read_text())
SQUARE = next(case['geometry'] for case in EXPECTED['cases'] if case['id'] == 'square-hole')


class Supplied:
    def __init__(self, rows):
        self.rows = rows

    def triangles(self, path):
        assert path == 'shape'
        return self.rows


def hand_plate(wanted):
    """Divide four quadrilateral bands by hand, then attach their boundary walls."""
    outer = next(r for r in wanted['rings'] if r['role'] == 'outer')
    inner = next(r for r in wanted['rings'] if r['role'] == 'hole')
    outer_points = [tuple(v['point_m']) for v in outer['vertices']]
    inner_points = [tuple(v['point_m']) for v in inner['vertices']]
    points = outer_points + inner_points
    # Outer order is bottom-left, bottom-right, top-right, top-left
    # Inner order is top-left, top-right, bottom-right, bottom-left
    caps = [(0, 1, 6), (0, 6, 7), (1, 2, 5), (1, 5, 6),
            (2, 3, 4), (2, 4, 5), (3, 0, 7), (3, 7, 4)]
    rows = []
    depth = wanted['depth_m']
    offset = wanted.get('local_position_m', [0, 0, 0])
    q = wanted.get('local_orientation_wxyz', [1, 0, 0, 0])

    def rotate(v):
        return tuple(v) if q[0] == 1 else (v[0], -v[1], -v[2])

    def f32(v):
        return struct.unpack('<f', struct.pack('<f', v))[0]

    def emit(region, triangle, normal):
        placed = [tuple(f32(a + b) for a, b in zip(rotate(point), offset)) for point in triangle]
        normal = tuple(f32(v) for v in rotate(normal))
        material = {'pbrMetallicRoughness': {
            'baseColorFactor': copy.deepcopy(wanted['palette'][region]),
            'metallicFactor': wanted['metallic'], 'roughnessFactor': wanted['roughness']}}
        rows.append([region, placed, [normal] * 3, material])

    for triangle in caps:
        emit('bottom', [(*points[i], 0) for i in reversed(triangle)], (0, 0, -1))
    for triangle in caps:
        emit('top', [(*points[i], depth) for i in triangle], (0, 0, 1))
    for ring in [outer, inner]:
        vertices = ring['vertices']
        for i, vertex in enumerate(vertices):
            a = vertex['point_m']
            b = vertices[(i + 1) % len(vertices)]['point_m']
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            normal = (dy / length, -dx / length, 0)
            emit(vertex['region'], [(*a, 0), (*b, 0), (*a, depth)], normal)
            emit(vertex['region'], [(*b, 0), (*b, depth), (*a, depth)], normal)
    return rows


class HolesOracleTests(unittest.TestCase):
    def setUp(self):
        self.wanted = copy.deepcopy(SQUARE)
        self.rows = hand_plate(self.wanted)

    def reject(self, mutate, message=None):
        mutate(self.rows)
        context = (self.assertRaisesRegex(AssertionError, message) if message
                   else self.assertRaises(AssertionError))
        with context:
            check_geometry(Supplied(self.rows), 'shape', self.wanted)

    def test_hand_divided_square_opening_passes(self):
        result = check_geometry(Supplied(self.rows), 'shape', self.wanted)
        self.assertEqual(result['triangles'], 32)
        self.assertEqual(result['holes'], 1)
        self.assertAlmostEqual(result['signed_volume_m3'], 6)
        self.assertEqual(result['cap_areas_m2'], [12, 12])

    def test_known_rigid_placement_is_removed_once(self):
        self.wanted['local_position_m'] = [.5, -.5, .2]
        self.wanted['local_orientation_wxyz'] = [0, 1, 0, 0]
        rows = hand_plate(self.wanted)
        result = check_geometry(Supplied(rows), 'shape', self.wanted)
        self.assertEqual(result['status'], 'passed')
        self.assertAlmostEqual(result['signed_volume_m3'], 6, places=5)

    def test_missing_triangle_rejects(self):
        self.reject(lambda rows: rows.pop(), 'triangle count')

    def test_duplicate_equal_area_cap_rejects_overlap(self):
        def change(rows):
            rows[10] = copy.deepcopy(rows[8])
        self.reject(change, 'overlap')

    def test_cap_filling_part_of_hole_rejects_when_centroid_is_material(self):
        small = copy.deepcopy(self.wanted)
        inner = next(r for r in small['rings'] if r['role'] == 'hole')
        for vertex, point in zip(inner['vertices'], [(1, 2), (2, 2), (2, 1), (1, 1)]):
            vertex['point_m'] = point
        small.update(area_m2=15, volume_m3=7.5, surface_area_m2=40, boundary_perimeter_m=20)
        rows = hand_plate(small)
        # The centroid (2, 2/3) is outside the hole, while this cap cuts its interior
        rows[8][1] = [(0, 0, .5), (4, 0, .5), (2, 2, .5)]
        centroid = [sum(p[i] for p in rows[8][1]) / 3 for i in range(2)]
        self.assertLess(centroid[1], 1)
        with self.assertRaisesRegex(AssertionError, 'boundary|hole'):
            check_geometry(Supplied(rows), 'shape', small)

    def test_inner_wall_with_reversed_face_and_normals_rejects(self):
        def change(rows):
            row = next(row for row in rows if row[0] == 'inner')
            row[1][0], row[1][1] = row[1][1], row[1][0]
            row[2] = [tuple(-v for v in normal) for normal in row[2]]
        self.reject(change, 'away from material')

    def test_wall_material_must_follow_outgoing_ring_edge(self):
        def change(rows):
            row = next(row for row in rows if row[0] == 'inner')
            row[0] = 'outer'
            row[3]['pbrMetallicRoughness']['baseColorFactor'] = self.wanted['palette']['outer']
        self.reject(change, 'outgoing authored edge')

    def test_wrong_pbr_color_rejects(self):
        def change(rows):
            rows[0][3]['pbrMetallicRoughness']['baseColorFactor'] = [0, 0, 0, 1]
        self.reject(change)

    def test_wrong_pbr_roughness_rejects(self):
        def change(rows):
            rows[0][3]['pbrMetallicRoughness']['roughnessFactor'] = .2
        self.reject(change)

    def test_tilted_unit_normal_rejects(self):
        def change(rows):
            rows[8][2] = [(0, .6, .8)] * 3
        self.reject(change)

    def test_inconsistent_duplicate_corner_rejects_inside_error_tolerance(self):
        def change(rows):
            point = rows[8][1][0]
            rows[8][1][0] = (point[0] + .0000001, point[1], point[2])
        self.reject(change, 'consistent actual decoded')

    def test_non_authored_corner_rejects(self):
        self.reject(lambda rows: rows[0][1].__setitem__(0, (100, 100, 100)), 'authored boundary vertex')

    def test_reversed_cap_face_and_normals_rejects(self):
        def change(rows):
            rows[8][1].reverse()
            rows[8][2] = [(0, 0, -1)] * 3
        self.reject(change, 'cap must point out')

    def test_unclosed_wall_rejects(self):
        def change(rows):
            rows[-1] = copy.deepcopy(rows[-2])
        self.reject(change)

    def test_exact_clipping_detects_containment_without_crossing_edges(self):
        triangle = tuple((Fraction(x), Fraction(y)) for x, y in [(0, 0), (4, 0), (0, 4)])
        contained = tuple((Fraction(x), Fraction(y)) for x, y in [(1, 1), (2, 1), (1, 2)])
        self.assertEqual(_overlap_area2(triangle, contained), 1)

    def test_exact_clipping_permits_shared_edges(self):
        first = tuple((Fraction(x), Fraction(y)) for x, y in [(0, 0), (1, 0), (0, 1)])
        second = tuple((Fraction(x), Fraction(y)) for x, y in [(1, 0), (1, 1), (0, 1)])
        self.assertEqual(_overlap_area2(first, second), 0)

    def test_exact_clipping_detects_crossing_triangles_without_containment(self):
        first = tuple((Fraction(x), Fraction(y)) for x, y in [(0, 0), (4, 0), (2, 4)])
        second = tuple((Fraction(x), Fraction(y)) for x, y in [(0, 3), (2, -1), (4, 3)])
        self.assertGreater(_overlap_area2(first, second), 0)

    def test_decoder_requires_explicit_dot9_binding(self):
        def supplied(version):
            document = {'buffers': [{'byteLength': 0}], 'extras': {'ontokin': {
                'target_contract': 'ontokin.glb/' + version, 'schema_version': version,
                'profile': 'polygon-holes-0.1' if version == '0.9' else 'polygon-extrusion-0.1'}}}
            data = json.dumps(document).encode()
            data += b' ' * (-len(data) % 4)
            return (struct.pack('<III', 0x46546c67, 2, 28 + len(data))
                    + struct.pack('<II', len(data), 0x4e4f534a) + data
                    + struct.pack('<II', 0, 0x004e4942))
        self.assertEqual(Decoded(supplied('0.9')).binary, b'')
        with self.assertRaises(AssertionError):
            Decoded(supplied('0.8'))

    def rigid_document(self, **extra):
        document = {'buffers': [{'byteLength': 0}], 'extras': {'ontokin': {
            'target_contract': 'ontokin.glb/0.9', 'schema_version': '0.9',
            'profile': 'polygon-holes-0.1'}}, **extra}
        data = json.dumps(document).encode()
        data += b' ' * (-len(data) % 4)
        return (struct.pack('<III', 0x46546c67, 2, 28 + len(data))
                + struct.pack('<II', len(data), 0x4e4f534a) + data
                + struct.pack('<II', 0, 0x004e4942))

    def test_decoder_refuses_static_scale_that_local_geometry_cannot_detect(self):
        Decoded(self.rigid_document(nodes=[{'scale': [1, 1, 1]}]))
        for scale in ([2, 2, 2], [.5, 2, 1], [-1, 1, 1]):
            with self.subTest(scale=scale), self.assertRaisesRegex(AssertionError, 'identity scale'):
                Decoded(self.rigid_document(nodes=[{'scale': scale}]))
        with self.assertRaisesRegex(AssertionError, 'explicit rigid transforms'):
            Decoded(self.rigid_document(nodes=[{'matrix': [2, 0, 0, 0, 0, 2, 0, 0,
                                                          0, 0, 2, 0, 0, 0, 0, 1]}]))

    def test_decoder_refuses_animated_scale_before_pose_interpolation(self):
        for channel in ('scale', 'weights'):
            with self.subTest(channel=channel), self.assertRaisesRegex(AssertionError, 'cannot animate'):
                Decoded(self.rigid_document(animations=[{'channels': [
                    {'target': {'node': 0, 'path': channel}, 'sampler': 0}]}]))


if __name__ == '__main__':
    unittest.main()
