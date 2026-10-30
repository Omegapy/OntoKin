"""Analytic ring solids, hostile host values and supplied-mesh intersections."""
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import unittest

from ontokin.extrusion import PolygonVertex
from ontokin.holes import PolygonRing, triangulate_holes, validate_holes_delivery
from ontokin.holes_delivery import _allowed_intersection
from ontokin.surface import SurfaceError, SurfaceMaterial


ROOT = Path(__file__).resolve().parents[1]
CASES = {case['id']: case for case in json.loads(
    (ROOT / 'examples/polygon-holes/expected.json').read_text())['cases']}
OUTER = ((0., 0.), (4., 0.), (4., 4.), (0., 4.))
HOLE = ((1., 1.), (1., 3.), (3., 3.), (3., 1.))
PALETTE = (SurfaceMaterial('bottom', (.3, .35, .4, 1.), .1, .65),
           SurfaceMaterial('inner', (.15, .65, .3, 1.), .1, .65),
           SurfaceMaterial('outer', (.7, .3, .1, 1.), .1, .65),
           SurfaceMaterial('top', (.1, .5, .8, 1.), .1, .65))


def ring(points, *, key='opening', order=20, role='hole', region='inner'):
    return PolygonRing(key, order, role, tuple(
        PolygonVertex('v' + str(i), 10 * i, point, region) for i, point in enumerate(points)))


def rings():
    return (ring(OUTER, key='outer', order=10, role='outer', region='outer'), ring(HOLE))


def mesh(value=None, *, palette=PALETTE, depth=.5, bottom='bottom', top='top', **kwargs):
    return triangulate_holes(rings() if value is None else value, palette, depth, bottom, top, **kwargs)


def frozen_mesh(name):
    wanted = CASES[name]['geometry']
    value = tuple(PolygonRing(r['key'], r['order'], r['role'], tuple(
        PolygonVertex(v['key'], v['order'], tuple(v['point_m']), v['region'])
        for v in r['vertices'])) for r in wanted['rings'])
    palette = tuple(SurfaceMaterial(key, tuple(color), wanted['metallic'], wanted['roughness'])
                    for key, color in wanted['palette'].items())
    return mesh(value, palette=palette, depth=wanted['depth_m']), wanted


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def totals(value):
    area, volume, edges = 0., 0., Counter()
    for start in range(0, len(value.positions), 3):
        a, b, c = value.positions[start:start + 3]
        face = cross(subtract(b, a), subtract(c, a))
        area += math.hypot(*face) / 2
        volume += dot(a, cross(b, c)) / 6
        for first, second in ((a, b), (b, c), (c, a)):
            edges[first, second] += 1
    return area, volume, edges


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def quantize(positions, transform=lambda point: point):
    return tuple(tuple(f32(value) for value in transform(point)) for point in positions)


class HoleGeometryTests(unittest.TestCase):
    def assertInvalid(self, suffix, value=None, **kwargs):
        with self.assertRaises(SurfaceError) as caught:
            mesh(value, **kwargs)
        self.assertEqual(caught.exception.code, 'OKL-E-HOLES-' + suffix)

    def assertClosed(self, value, area, volume, triangles):
        actual_area, actual_volume, edges = totals(value)
        self.assertAlmostEqual(actual_area, area, places=8)
        self.assertAlmostEqual(actual_volume, volume, places=8)
        self.assertEqual(value.triangle_count, triangles)
        self.assertEqual(len(value.positions), 3 * triangles)
        self.assertEqual(len(value.corner_vertex_ids), len(value.positions))
        for (a, b), count in edges.items():
            self.assertEqual(count, 1)
            self.assertEqual(edges[b, a], 1)
        for start in range(0, len(value.positions), 3):
            a, b, c = value.positions[start:start + 3]
            normal = value.normals[start]
            self.assertGreater(dot(cross(subtract(b, a), subtract(c, a)), normal), 0)
            self.assertAlmostEqual(math.hypot(*normal), 1)
            self.assertEqual(value.normals[start:start + 3], (normal,) * 3)

    def test_all_frozen_positive_solids_match_independent_analytic_totals(self):
        for name, case in CASES.items():
            if case['expected_outcome'] != 'valid':
                continue
            with self.subTest(case=name):
                value, wanted = frozen_mesh(name)
                self.assertClosed(value, wanted['surface_area_m2'], wanted['volume_m3'],
                                  wanted['triangle_count'])
                self.assertEqual({r.key: len(r.indices) // 3 for r in value.regions},
                                 wanted['region_triangle_counts'])
                self.assertEqual(len(value.vertex_keys), wanted['boundary_vertex_count'])
                self.assertEqual(len(value.ring_keys), wanted['ring_count'])

    def test_square_hole_cap_boundaries_keep_the_opening_empty(self):
        value = mesh()
        self.assertClosed(value, 36., 6., 32)
        for start in range(0, 8 * 3, 3):
            triangle = value.positions[start:start + 3]
            for point in ((2., 2.), (1.5, 1.5), (2.5, 2.5)):
                signs = []
                for a, b in zip(triangle, triangle[1:] + triangle[:1]):
                    signs.append((b[0] - a[0]) * (point[1] - a[1]) -
                                 (b[1] - a[1]) * (point[0] - a[0]))
                self.assertFalse(all(turn > 0 for turn in signs) or all(turn < 0 for turn in signs))

    def test_hole_wall_normals_face_into_the_opening(self):
        value = mesh()
        inner = next(region for region in value.regions if region.key == 'inner')
        for index in inner.indices:
            point, normal = value.positions[index], value.normals[index]
            inward = (2. - point[0], 2. - point[1], 0.)
            self.assertGreater(dot(normal, inward), 0)

    def test_ring_vertex_and_palette_reordering_retains_exact_native_output(self):
        original = rings()
        reordered = tuple(replace(r, vertices=tuple(reversed(r.vertices))) for r in reversed(original))
        self.assertEqual(mesh(original), mesh(reordered, palette=tuple(reversed(PALETTE))))

    def test_role_identifies_outer_even_when_the_hole_sorts_first(self):
        original = rings()
        value = mesh((replace(original[0], order=50), replace(original[1], order=2)))
        self.assertEqual(value.ring_keys, ('opening', 'outer'))
        self.assertClosed(value, 36., 6., 32)

    def test_vertex_keys_are_local_to_their_ring(self):
        value = mesh()
        self.assertIn(('outer', 'v0'), value.vertex_keys)
        self.assertIn(('opening', 'v0'), value.vertex_keys)
        self.assertEqual(len(set(value.vertex_keys)), 8)

    def test_gapped_orders_do_not_change_traversal_or_materials(self):
        original = rings()
        value = tuple(replace(r, order=100 * i + 5,
                              vertices=tuple(replace(v, order=100 * j + 3)
                                             for j, v in enumerate(r.vertices)))
                      for i, r in enumerate(original))
        self.assertEqual(mesh(value), mesh(original))

    def test_caps_are_canonical_and_precede_ordered_walls(self):
        value = mesh()
        top = [tuple(index - 8 for index in value.corner_vertex_ids[start:start + 3])
               for start in range(24, 48, 3)]
        self.assertEqual(top, sorted(top))
        self.assertTrue(all(triangle[0] == min(triangle) for triangle in top))
        self.assertEqual(value.normals[:24], ((0., 0., -1.),) * 24)
        self.assertEqual(value.normals[24:48], ((0., 0., 1.),) * 24)
        self.assertEqual(value.corner_vertex_ids[48:54], (0, 1, 8, 1, 9, 8))

    def test_unused_material_does_not_emit_a_primitive(self):
        value = mesh(palette=PALETTE + (SurfaceMaterial('unused', (0., 0., 0., 1.), 0., 1.),))
        self.assertEqual([region.key for region in value.regions], ['bottom', 'inner', 'outer', 'top'])

    def test_ring_roles_counts_keys_and_orders_are_strict(self):
        outer, hole = rings()
        self.assertInvalid('RING', ())
        self.assertInvalid('RING', (hole,))
        self.assertInvalid('RING', (outer, replace(hole, role='outer')))
        self.assertInvalid('RING', (outer, replace(hole, role='Hole')))
        self.assertInvalid('RING', (outer, replace(hole, key='outer')))
        self.assertInvalid('RING', (outer,) + (hole,) * 9)
        for order in (True, -1, 65536, 1.5, outer.order):
            with self.subTest(order=order):
                self.assertInvalid('ORDER', (outer, replace(hole, order=order)))

    def test_vertex_boundaries_and_invalid_host_point_types(self):
        outer, hole = rings()
        self.assertInvalid('VERTEX', (replace(outer, vertices=outer.vertices[:2]),))
        self.assertInvalid('VERTEX', (replace(outer, vertices=outer.vertices * 17),))
        for point in ((0.,), (0., 0., 0.), (True, 0.), (math.nan, 0.), (100.0001, 0.)):
            with self.subTest(point=point):
                vertex = replace(hole.vertices[0], point_m=point)
                self.assertInvalid('POINT', (outer, replace(hole, vertices=(vertex,) + hole.vertices[1:])))
        for order in (True, -1, 65536, 1.5, hole.vertices[1].order):
            with self.subTest(order=order):
                vertex = replace(hole.vertices[0], order=order)
                self.assertInvalid('ORDER', (outer, replace(hole, vertices=(vertex,) + hole.vertices[1:])))
        vertex = replace(hole.vertices[0], key=hole.vertices[1].key)
        self.assertInvalid('VERTEX', (outer, replace(hole, vertices=(vertex,) + hole.vertices[1:])))

    def test_winding_is_rejected_without_reversal(self):
        outer, hole = rings()
        self.assertInvalid('WINDING', (ring(tuple(reversed(OUTER)), key='outer', order=10,
                                          role='outer', region='outer'), hole))
        self.assertInvalid('WINDING', (outer, ring(tuple(reversed(HOLE)))))

    def test_touching_crossing_overlapping_and_nested_rings_are_rejected(self):
        outer, hole = rings()
        for points in (((0., 1.), (0., 3.), (2., 3.), (2., 1.)),
                       ((-1., 1.), (-1., 3.), (2., 3.), (2., 1.))):
            with self.subTest(points=points):
                self.assertInvalid('TOPOLOGY', (outer, ring(points)))
        outside = ring(((5., 1.), (5., 3.), (7., 3.), (7., 1.)))
        self.assertInvalid('CONTAINMENT', (outer, outside))
        nested = ring(((1.5, 1.5), (1.5, 2.5), (2.5, 2.5), (2.5, 1.5)), key='nested', order=30)
        self.assertInvalid('CONTAINMENT', (outer, hole, nested))
        overlap = ring(((2., 1.5), (2., 3.5), (3.5, 3.5), (3.5, 1.5)), key='overlap', order=30)
        self.assertInvalid('TOPOLOGY', (outer, hole, overlap))

    def test_repeated_points_collinearity_and_self_crossings_are_rejected(self):
        outer = rings()[0]
        for points in (((1., 1.), (1., 3.), (3., 3.), (1., 1.)),
                       ((1., 1.), (1., 2.), (1., 3.), (3., 3.), (3., 1.)),
                       ((1., 1.), (3., 3.), (1., 3.), (3., 1.))):
            with self.subTest(points=points):
                self.assertInvalid('TOPOLOGY', (outer, ring(points)))

    def test_depth_material_and_remaining_allocation_failures_are_explicit(self):
        for depth in (True, 0., -.5, math.nextafter(.001, 0.),
                      math.nextafter(100., math.inf), math.inf, math.nan):
            with self.subTest(depth=depth):
                self.assertInvalid('DEPTH', depth=depth)
        self.assertInvalid('REGION', bottom='missing')
        self.assertInvalid('REGION', top='missing')
        outer, hole = rings()
        bad = replace(hole.vertices[0], region='missing')
        self.assertInvalid('REGION', (outer, replace(hole, vertices=(bad,) + hole.vertices[1:])))
        with self.assertRaises(SurfaceError) as caught:
            mesh(max_vertices=95)
        self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')
        self.assertEqual(caught.exception.details, {'required': 96, 'available': 95})

    def test_exact_predicates_do_not_admit_unrepresentable_native_faces(self):
        tiny = math.ulp(0.)
        value = ring(((0., 0.), (tiny, 0.), (0., tiny)), key='outer', order=0,
                     role='outer', region='outer')
        self.assertInvalid('NUMERIC', (value,))

    def test_mutable_host_membership_points_and_materials_are_snapshotted(self):
        source = [replace(r, vertices=[replace(v, point_m=list(v.point_m)) for v in r.vertices])
                  for r in rings()]
        palette = [replace(material, rgba=list(material.rgba)) for material in PALETTE]
        calls = 0
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 2:
                source[0].vertices[0].point_m[0] = 500.
                source[0].vertices.extend(source[0].vertices * 20)
                object.__setattr__(source[1], 'role', 'outer')
                source.extend(source * 10)
                palette[0].rgba[0] = 8.
                palette.extend(palette * 10)
        self.assertEqual(mesh(source, palette=palette, check=mutate), mesh())

    def test_subclass_entries_cannot_supply_dynamic_host_fields(self):
        class DynamicRing(PolygonRing):
            pass
        outer, hole = rings()
        self.assertInvalid('RING', (DynamicRing(outer.key, outer.order, outer.role, outer.vertices), hole))

    def test_cooperative_geometry_work_preserves_cancellation_identity(self):
        marker = RuntimeError('cancel ring construction')
        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            if calls == 40:
                raise marker
        with self.assertRaises(RuntimeError) as caught:
            mesh(check=cancel)
        self.assertIs(caught.exception, marker)


class HoleDeliveryTests(unittest.TestCase):
    def assertRejected(self, value, positions=None, ids=None):
        with self.assertRaises(SurfaceError) as caught:
            validate_holes_delivery(value.corner_vertex_ids if ids is None else ids,
                                    value.positions if positions is None else positions)
        self.assertEqual(caught.exception.code, 'OKL-E-HOLES-NUMERIC')

    def test_square_multiple_concave_and_maximum_holes_survive_float32(self):
        for name in ('square-hole', 'two-holes', 'concave-outer', 'concave-hole',
                     'zero-holes', 'maximum-rings-and-vertices'):
            with self.subTest(case=name):
                value, unused = frozen_mesh(name)
                validate_holes_delivery(value.corner_vertex_ids, quantize(value.positions))

    def test_arbitrary_rotated_and_translated_float32_positions_are_checked_in_3d(self):
        value = mesh()
        ax, ay = .37, -.59
        cx, sx, cy, sy = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay)
        def transform(point):
            x, y, z = point
            y, z = cx * y - sx * z, sx * y + cx * z
            return (cy * x + sy * z + .123, y - .456, -sy * x + cy * z + .789)
        validate_holes_delivery(value.corner_vertex_ids, quantize(value.positions, transform))

    def test_all_frozen_precision_failures_are_source_valid_and_delivery_rejected(self):
        for name, case in CASES.items():
            if case['expected_outcome'] != 'source_valid_delivery_rejected':
                continue
            with self.subTest(case=name):
                value, wanted = frozen_mesh(name)
                offset = wanted.get('local_position_m', [0., 0., 0.])
                def transform(point):
                    return tuple(point[i] + offset[i] for i in range(3))
                self.assertRejected(value, quantize(value.positions, transform))

    def test_nonincident_wall_and_cap_intersections_cannot_retain_a_false_pass(self):
        value = mesh()
        shifted = tuple((x + 2.25, y + .1, z) if identity % 8 >= 4 else (x, y, z)
                        for identity, (x, y, z) in zip(value.corner_vertex_ids, value.positions))
        self.assertRejected(value, shifted)

    def test_repeated_vertex_identity_must_have_identical_coordinates(self):
        value = mesh()
        positions = list(value.positions)
        positions[0] = tuple(component + .01 for component in positions[0])
        self.assertRejected(value, positions)

    def test_distinct_vertices_cannot_merge_even_before_face_checks(self):
        value = mesh()
        replacement = next(position for identity, position in zip(value.corner_vertex_ids, value.positions)
                           if identity == 0)
        positions = tuple(replacement if identity == 4 else position
                          for identity, position in zip(value.corner_vertex_ids, value.positions))
        self.assertRejected(value, positions)

    def test_removed_reversed_or_repeated_faces_are_rejected(self):
        value = mesh()
        self.assertRejected(value, value.positions[:-3], value.corner_vertex_ids[:-3])
        ids, positions = list(value.corner_vertex_ids), list(value.positions)
        ids[:3], positions[:3] = ids[:3][::-1], positions[:3][::-1]
        self.assertRejected(value, positions, ids)
        self.assertRejected(value, value.positions + value.positions[:3],
                            value.corner_vertex_ids + value.corner_vertex_ids[:3])

    def test_delivery_snapshots_caller_owned_positions_before_later_callbacks(self):
        value = mesh()
        ids, positions = list(value.corner_vertex_ids), [list(point) for point in value.positions]
        calls = 0
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 2:
                ids[:] = []
                positions[0][:] = [math.inf]
                positions.extend(positions * 20)
        validate_holes_delivery(ids, positions, check=mutate)

    def test_delivery_callbacks_preserve_exception_identity(self):
        value = mesh()
        marker = RuntimeError('cancel supplied geometry')
        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            if calls == 40:
                raise marker
        with self.assertRaises(RuntimeError) as caught:
            validate_holes_delivery(value.corner_vertex_ids, value.positions, check=cancel)
        self.assertIs(caught.exception, marker)

    def test_invalid_delivery_shapes_identity_types_and_nonfinite_coordinates(self):
        value = mesh()
        self.assertRejected(value, (), ())
        ids = list(value.corner_vertex_ids)
        ids[0] = True
        self.assertRejected(value, ids=ids)
        positions = list(value.positions)
        positions[0] = (math.inf, 0., 0.)
        self.assertRejected(value, positions)


class ExactTriangleIntersectionTests(unittest.TestCase):
    @staticmethod
    def triangle(points):
        points = tuple(tuple(Fraction(value) for value in point) for point in points)
        normal = cross(subtract(points[1], points[0]), subtract(points[2], points[0]))
        bounds = (tuple(min(point[i] for point in points) for i in range(3)),
                  tuple(max(point[i] for point in points) for i in range(3)))
        return points, normal, bounds

    def allowed(self, first, second, shared=()):
        return _allowed_intersection(self.triangle(first), self.triangle(second),
                                     tuple(tuple(Fraction(value) for value in point) for point in shared),
                                     lambda: None)

    def test_coplanar_disjoint_and_shared_edge_are_allowed(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        self.assertTrue(self.allowed(a, ((3, 0, 0), (5, 0, 0), (3, 2, 0))))
        b = ((2, 0, 0), (2, 2, 0), (0, 2, 0))
        self.assertTrue(self.allowed(a, b, ((2, 0, 0), (0, 2, 0))))

    def test_coplanar_overlap_is_rejected_despite_a_shared_vertex(self):
        a = ((0, 0, 0), (3, 0, 0), (0, 3, 0))
        b = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        self.assertFalse(self.allowed(a, b, ((0, 0, 0),)))

    def test_touching_without_source_identity_is_rejected(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        b = ((2, 0, 0), (3, 0, 0), (2, -1, 0))
        self.assertFalse(self.allowed(a, b))
        self.assertTrue(self.allowed(a, b, ((2, 0, 0),)))

    def test_nonplanar_crossing_and_false_shared_vertex_are_rejected(self):
        a = ((0, 0, 0), (3, 0, 0), (0, 3, 0))
        b = ((1, 1, -1), (1, 1, 1), (2, 1, 0))
        self.assertFalse(self.allowed(a, b))
        c = ((0, 0, 0), (1, 1, 1), (2, 2, -1))
        self.assertFalse(self.allowed(a, c, ((0, 0, 0),)))

    def test_nonplanar_shared_edge_and_parallel_planes_are_allowed(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        b = ((0, 0, 0), (2, 0, 0), (0, 0, 2))
        self.assertTrue(self.allowed(a, b, ((0, 0, 0), (2, 0, 0))))
        self.assertTrue(self.allowed(a, ((0, 0, 1), (2, 0, 1), (0, 2, 1))))


if __name__ == '__main__':
    unittest.main()
