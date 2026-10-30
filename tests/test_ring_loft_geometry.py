"""Frozen analytic lofts, exact surface controls and hostile supplied geometry."""
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import unittest

from ontokin.extrusion import PolygonVertex
from ontokin.holes import PolygonRing, triangulate_holes
from ontokin.holes_delivery import _allowed_intersection
from ontokin.ring_loft import PolygonSection, triangulate_ring_loft, _unit_normal
from ontokin.ring_loft_delivery import validate_ring_loft_delivery
from ontokin.surface import SurfaceError, SurfaceMaterial


ROOT = Path(__file__).resolve().parents[1]
CASES = {case['id']: case for case in json.loads(
    (ROOT / 'examples/polygon-lofts/expected.json').read_text())['cases']}
PALETTE = (SurfaceMaterial('bottom', (.3, .35, .4, 1.), .1, .65),
           SurfaceMaterial('inner', (.15, .65, .3, 1.), .1, .65),
           SurfaceMaterial('outer', (.7, .3, .1, 1.), .1, .65),
           SurfaceMaterial('top', (.1, .5, .8, 1.), .1, .65))


def ring(points, *, key='outer', order=10, role='outer', region='outer'):
    return PolygonRing(key, order, role, tuple(
        PolygonVertex('v' + str(i), 10 * i, tuple(point), region)
        for i, point in enumerate(points)))


def basic_sections():
    rings = (ring(((-2., -2.), (2., -2.), (2., 2.), (-2., 2.))),
             ring(((-1., 1.), (1., 1.), (1., -1.), (-1., -1.)),
                  key='opening', order=20, role='hole', region='inner'))
    return (PolygonSection('lower', 10, 0., rings), PolygonSection('upper', 20, 3., rings))


def mesh(sections=None, *, materials=PALETTE, bottom='bottom', top='top', **kwargs):
    return triangulate_ring_loft(basic_sections() if sections is None else sections,
                                 materials, bottom, top, **kwargs)


def frozen_inputs(name):
    wanted = CASES[name]['geometry']
    sections = tuple(PolygonSection(section['key'], section['order'], section['station_m'], tuple(
        PolygonRing(r['key'], r['order'], r['role'], tuple(
            PolygonVertex(v['key'], v['order'], tuple(v['point_m']), v['region'])
            for v in r['vertices'])) for r in section['rings'])) for section in wanted['sections'])
    palette = tuple(SurfaceMaterial(key, tuple(color), wanted['metallic'], wanted['roughness'])
                    for key, color in wanted['palette'].items())
    return sections, palette, wanted


def frozen_mesh(name):
    sections, palette, wanted = frozen_inputs(name)
    return mesh(sections, materials=palette), wanted


def subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def totals(value):
    area, volume6, edges = 0., Fraction(0), Counter()
    for start in range(0, len(value.positions), 3):
        a, b, c = (tuple(Fraction(x) for x in point) for point in value.positions[start:start + 3])
        face = cross(subtract(b, a), subtract(c, a))
        area += math.hypot(*(float(x) for x in face)) / 2
        volume6 += dot(a, cross(b, c))
        ids = value.corner_vertex_ids[start:start + 3]
        for first, second in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            edges[first, second] += 1
    return area, volume6 / 6, edges


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def quantize(values, transform=lambda value: value):
    return tuple(tuple(f32(x) for x in transform(value)) for value in values)


def rotate(point, q):
    w, x, y, z = q
    first = cross((x, y, z), point)
    second = cross((x, y, z), first)
    return tuple(point[i] + 2 * (w * first[i] + second[i]) for i in range(3))


class RingLoftGeometryTests(unittest.TestCase):
    def assertInvalid(self, suffix, sections=None, **kwargs):
        with self.assertRaises(SurfaceError) as caught:
            mesh(sections, **kwargs)
        self.assertEqual(caught.exception.code, 'OKL-E-RING-LOFT-' + suffix)

    def test_all_frozen_source_valid_meshes_match_independent_exact_volumes(self):
        for name, case in CASES.items():
            if case['expected_outcome'] not in ('valid', 'source_valid_delivery_rejected'):
                continue
            with self.subTest(case=name):
                value, wanted = frozen_mesh(name)
                area, volume, edges = totals(value)
                self.assertEqual(volume, Fraction(*(int(x) for x in wanted['volume_exact'])))
                self.assertTrue(math.isclose(area, wanted['surface_area_m2'], rel_tol=1e-12, abs_tol=1e-8))
                self.assertEqual(value.triangle_count, wanted['triangle_count'])
                self.assertEqual(len(value.positions), wanted['vertex_count'])
                self.assertEqual(len(value.vertex_keys), wanted['authored_vertex_count'])
                self.assertEqual(len(value.section_keys), wanted['section_count'])
                self.assertEqual(len(value.ring_keys), wanted['ring_count'])
                self.assertEqual({region.key: len(region.indices) // 3 for region in value.regions},
                                 wanted['region_triangle_counts'])
                for (a, b), count in edges.items():
                    self.assertEqual(count, 1)
                    self.assertEqual(edges[b, a], 1)
                for start in range(0, len(value.positions), 3):
                    a, b, c = (tuple(Fraction(x) for x in point)
                               for point in value.positions[start:start + 3])
                    normal = value.normals[start]
                    self.assertGreater(dot(cross(subtract(b, a), subtract(c, a)),
                                           tuple(Fraction(x) for x in normal)), 0)
                    self.assertAlmostEqual(math.hypot(*normal), 1.)
                    self.assertEqual(value.normals[start:start + 3], (normal,) * 3)

    def test_constant_sections_reproduce_existing_hole_extrusion(self):
        sections = basic_sections()
        value = mesh(sections)
        reference = triangulate_holes(sections[0].rings, PALETTE, 3., 'bottom', 'top')
        self.assertEqual(value.positions, reference.positions)
        self.assertEqual(value.normals, reference.normals)
        self.assertEqual(value.regions, reference.regions)

    def test_reordering_all_declarations_retains_exact_native_output(self):
        source = basic_sections()
        reordered = tuple(replace(section, rings=tuple(
            replace(r, vertices=tuple(reversed(r.vertices))) for r in reversed(section.rings)))
            for section in reversed(source))
        self.assertEqual(mesh(source), mesh(reordered, materials=tuple(reversed(PALETTE))))

    def test_source_identities_include_section_ring_and_vertex(self):
        value = mesh()
        self.assertIn(('lower', 'outer', 'v0'), value.vertex_keys)
        self.assertIn(('upper', 'outer', 'v0'), value.vertex_keys)
        self.assertIn(('lower', 'opening', 'v0'), value.vertex_keys)
        self.assertEqual(set(value.corner_vertex_ids), set(value.vertex_keys))

    def test_endpoint_caps_use_independent_valid_diagonals(self):
        value, wanted = frozen_mesh('changing-concave-cap-diagonal')
        for region in value.regions:
            if region.key not in ('bottom', 'top'):
                continue
            edges = Counter()
            for start in range(0, len(region.indices), 3):
                ids = [value.corner_vertex_ids[index][2] for index in region.indices[start:start + 3]]
                for a, b in zip(ids, ids[1:] + ids[:1]):
                    edges[frozenset((a, b))] += 1
            internal = {edge for edge, count in edges.items() if count == 2}
            self.assertEqual(internal, {frozenset(wanted['cap_diagonal_control'][region.key])})

    def test_quarter_turn_authority_accepts_box_and_rejects_opposite_pinch(self):
        value, unused = frozen_mesh('authoritative-quarter-turn')
        area, volume, unused_edges = totals(value)
        self.assertEqual(volume, 4)
        self.assertEqual(area, 16)
        low = ring(((-1., -1.), (1., -1.), (1., 1.), (-1., 1.)))
        high = replace(low, vertices=tuple(replace(vertex, point_m=(vertex.point_m[1], -vertex.point_m[0]))
                                           for vertex in low.vertices))
        self.assertInvalid('TOPOLOGY', (PolygonSection('lower', 0, 0., (low,)),
                                        PolygonSection('upper', 1, 1., (high,))))

    def test_holes_cannot_exchange_positions_through_one_another(self):
        outside = ring(((-4., -4.), (4., -4.), (4., 4.), (-4., 4.)))
        left = ring(((-2.5, .5), (-1.5, .5), (-1.5, -.5), (-2.5, -.5)),
                    key='left', order=20, role='hole', region='inner')
        right = ring(((1.5, .5), (2.5, .5), (2.5, -.5), (1.5, -.5)),
                     key='right', order=30, role='hole', region='inner')
        top_left = replace(left, vertices=tuple(replace(v, point_m=r.point_m)
                                               for v, r in zip(left.vertices, right.vertices)))
        top_right = replace(right, vertices=tuple(replace(v, point_m=l.point_m)
                                                 for v, l in zip(right.vertices, left.vertices)))
        self.assertInvalid('TOPOLOGY', (PolygonSection('lower', 0, 0., (outside, left, right)),
                                        PolygonSection('upper', 1, 2., (outside, top_left, top_right))))

    def test_correspondence_changes_are_not_automatically_aligned(self):
        lower, upper = basic_sections()
        outer, hole = upper.rings
        changes = (replace(outer, key='changed'), replace(outer, order=12),
                   replace(outer, vertices=tuple(replace(v, key='changed') if i == 0 else v
                                                for i, v in enumerate(outer.vertices))),
                   replace(outer, vertices=tuple(replace(v, order=1) if i == 0 else v
                                                for i, v in enumerate(outer.vertices))),
                   replace(outer, vertices=outer.vertices[:3]))
        for changed in changes:
            with self.subTest(changed=changed):
                self.assertInvalid('CORRESPONDENCE', (lower, replace(upper, rings=(changed, hole))))
        self.assertInvalid('CORRESPONDENCE', (lower, replace(upper, rings=(outer,))))
        swapped_roles = (replace(outer, role='hole'), replace(hole, role='outer'))
        self.assertInvalid('CORRESPONDENCE', (lower, replace(upper, rings=swapped_roles)))

    def test_station_boundary_is_exact_canonical_binary64_difference(self):
        lower, upper = basic_sections()
        mesh((lower, replace(upper, station_m=.001)))
        for station in (True, -.1, 0., math.nextafter(.001, 0.),
                        math.nextafter(100., math.inf), math.nan, math.inf):
            with self.subTest(station=station):
                self.assertInvalid('STATION', (lower, replace(upper, station_m=station)))
        self.assertInvalid('STATION', (replace(lower, station_m=1.), replace(upper, station_m=1.001)))

    def test_section_orders_and_keys_are_bounded_and_unique(self):
        lower, upper = basic_sections()
        for order in (True, -1, 65536, 1.5, lower.order):
            with self.subTest(order=order):
                self.assertInvalid('ORDER', (lower, replace(upper, order=order)))
        self.assertInvalid('SECTION', (lower, replace(upper, key=lower.key)))

    def test_section_and_total_vertex_counts_fail_before_unbounded_work(self):
        source = basic_sections()
        for value in ((), source[:1], source * 5):
            self.assertInvalid('SECTION', value)
        outline = ring(tuple((math.cos(i * math.tau / 36), math.sin(i * math.tau / 36))
                             for i in range(36)))
        self.assertInvalid('SECTION', tuple(PolygonSection('s' + str(i), i, float(i), (outline,))
                                             for i in range(8)))

    def test_inherited_ring_winding_and_terminal_region_diagnostics_remain(self):
        lower, upper = basic_sections()
        wrong = replace(lower.rings[0], vertices=tuple(
            replace(v, point_m=lower.rings[0].vertices[-1 - i].point_m)
            for i, v in enumerate(lower.rings[0].vertices)))
        with self.assertRaises(SurfaceError) as caught:
            mesh((replace(lower, rings=(wrong, lower.rings[1])), upper))
        self.assertEqual(caught.exception.code, 'OKL-E-HOLES-WINDING')
        bad_vertex = replace(upper.rings[0].vertices[0], region='missing')
        bad_ring = replace(upper.rings[0], vertices=(bad_vertex,) + upper.rings[0].vertices[1:])
        with self.assertRaises(SurfaceError) as caught:
            mesh((lower, replace(upper, rings=(bad_ring, upper.rings[1]))))
        self.assertEqual(caught.exception.code, 'OKL-E-HOLES-REGION')

    def test_cap_material_and_remaining_allocation_failures_are_explicit(self):
        self.assertInvalid('REGION', bottom='missing')
        self.assertInvalid('REGION', top='missing')
        with self.assertRaises(SurfaceError) as caught:
            mesh(max_vertices=95)
        self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')
        self.assertEqual(caught.exception.details, {'required': 96, 'available': 95})
        for maximum in (True, -1, 250001, 1.5):
            with self.assertRaises(SurfaceError) as caught:
                mesh(max_vertices=maximum)
            self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')

    def test_all_later_sections_and_material_leaves_are_snapshotted_together(self):
        expected = mesh()
        source = [replace(section, rings=[replace(r, vertices=[replace(v, point_m=list(v.point_m))
                                                               for v in r.vertices])
                                                 for r in section.rings])
                  for section in basic_sections()]
        palette = [replace(material, rgba=list(material.rgba)) for material in PALETTE]
        calls = 0
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 2:
                source[-1].rings[0].vertices[0].point_m[0] = 500.
                source[-1].rings[0].vertices.extend(source[-1].rings[0].vertices * 20)
                object.__setattr__(source[-1], 'station_m', 0.)
                source.extend(source * 10)
                palette[0].rgba[0] = 9.
                palette.extend(palette * 10)
        self.assertEqual(mesh(source, materials=palette, check=mutate), expected)

    def test_dynamic_section_subclasses_are_not_admitted(self):
        class DynamicSection(PolygonSection):
            pass
        lower, upper = basic_sections()
        self.assertInvalid('SECTION', (DynamicSection(lower.key, lower.order, lower.station_m, lower.rings), upper))

    def test_geometry_work_checks_preserve_the_exact_cancellation_exception(self):
        total = 0
        def count():
            nonlocal total
            total += 1
        mesh(check=count)
        for limit in (2, 40, total // 2, total - 1):
            marker = RuntimeError('cancel ring loft at ' + str(limit))
            calls = 0
            def cancel():
                nonlocal calls
                calls += 1
                if calls == limit:
                    raise marker
            with self.assertRaises(RuntimeError) as caught:
                mesh(check=cancel)
            self.assertIs(caught.exception, marker)

    def test_exact_cross_normal_retains_tiny_orientation_lost_by_float_subtraction(self):
        points = ((2. ** -80, 0., 0.), (1., 3., 0.), (15., 45., 0.))
        self.assertEqual(_unit_normal(points), (0., 0., -1.))
        a, b, c = points
        u, v = subtract(b, a), subtract(c, a)
        scale = max(abs(value) for value in (*u, *v))
        rounded = cross(tuple(value / scale for value in u), tuple(value / scale for value in v))
        self.assertGreater(rounded[2], 0.)
        exact = tuple(tuple(Fraction(value) for value in point) for point in points)
        self.assertLess(cross(subtract(exact[1], exact[0]), subtract(exact[2], exact[0]))[2], 0)


class RingLoftDeliveryTests(unittest.TestCase):
    def assertRejected(self, value, *, positions=None, ids=None, normals=None):
        with self.assertRaises(SurfaceError) as caught:
            validate_ring_loft_delivery(value.corner_vertex_ids if ids is None else ids,
                                        value.positions if positions is None else positions,
                                        normals=normals)
        self.assertEqual(caught.exception.code, 'OKL-E-RING-LOFT-NUMERIC')

    def test_solid_hollow_concave_chamfer_and_maximum_meshes_survive_binary32(self):
        for name in ('solid-frustum', 'hollow-frustum', 'concave-outer', 'concave-hole',
                     'three-section-chamfer', 'authoritative-quarter-turn',
                     'maximum-sections-and-total', 'maximum-vertices-and-total'):
            with self.subTest(case=name):
                value, unused = frozen_mesh(name)
                validate_ring_loft_delivery(value.corner_vertex_ids, quantize(value.positions),
                                            normals=quantize(value.normals))

    def test_rotated_quantized_caps_need_not_remain_coplanar(self):
        value = mesh()
        q = (math.cos(.37), math.sin(.37) / math.sqrt(3),
             math.sin(.37) / math.sqrt(3), math.sin(.37) / math.sqrt(3))
        def transform(point):
            rotated = rotate(point, q)
            return tuple(rotated[i] + (.123, -.456, .789)[i] for i in range(3))
        validate_ring_loft_delivery(value.corner_vertex_ids, quantize(value.positions, transform),
                                    normals=quantize(value.normals, lambda normal: rotate(normal, q)))

    def test_frozen_precision_cases_fail_on_actual_quantized_positions(self):
        for name, case in CASES.items():
            if case['expected_outcome'] != 'source_valid_delivery_rejected':
                continue
            with self.subTest(case=name):
                value, wanted = frozen_mesh(name)
                offset = wanted.get('local_position_m', (0., 0., 0.))
                q = wanted.get('local_orientation_wxyz', (1., 0., 0., 0.))
                def transform(point):
                    rotated = rotate(point, q)
                    return tuple(rotated[i] + offset[i] for i in range(3))
                self.assertRejected(value, positions=quantize(value.positions, transform))

    def test_nonincident_hole_surfaces_cannot_cross_the_outer_surface(self):
        value = mesh()
        shifted = tuple((x + 2.5, y, z) if identity[1] == 'opening' else (x, y, z)
                        for identity, (x, y, z) in zip(value.corner_vertex_ids, value.positions))
        self.assertRejected(value, positions=shifted)

    def test_repeated_source_id_must_keep_identical_positions(self):
        value = mesh()
        positions = list(value.positions)
        positions[0] = tuple(component + .01 for component in positions[0])
        self.assertRejected(value, positions=positions)

    def test_distinct_source_ids_cannot_be_welded_by_delivery(self):
        value = mesh()
        first, second = value.vertex_keys[:2]
        target = next(point for key, point in zip(value.corner_vertex_ids, value.positions) if key == first)
        positions = tuple(target if key == second else point
                          for key, point in zip(value.corner_vertex_ids, value.positions))
        self.assertRejected(value, positions=positions)

    def test_missing_reversed_or_duplicated_faces_are_rejected(self):
        value = mesh()
        self.assertRejected(value, ids=value.corner_vertex_ids[:-3], positions=value.positions[:-3])
        ids, positions = list(value.corner_vertex_ids), list(value.positions)
        ids[:3], positions[:3] = ids[:3][::-1], positions[:3][::-1]
        self.assertRejected(value, ids=ids, positions=positions)
        self.assertRejected(value, ids=value.corner_vertex_ids + value.corner_vertex_ids[:3],
                            positions=value.positions + value.positions[:3])

    def test_global_winding_reversal_has_negative_volume(self):
        value = mesh()
        ids, positions = [], []
        for start in range(0, len(value.positions), 3):
            ids.extend(reversed(value.corner_vertex_ids[start:start + 3]))
            positions.extend(reversed(value.positions[start:start + 3]))
        self.assertRejected(value, ids=ids, positions=positions)

    def test_malformed_identity_position_and_normal_sequences_are_rejected(self):
        value = mesh()
        self.assertRejected(value, ids=(), positions=())
        for identity in (True, ('lower', 'outer'), ('lower', 'outer', True), ('lower', 'outer', 'x' * 65)):
            ids = list(value.corner_vertex_ids)
            ids[0] = identity
            self.assertRejected(value, ids=ids)
        for point in ((1., 2.), (math.inf, 0., 0.), (True, 0., 0.)):
            positions = list(value.positions)
            positions[0] = point
            self.assertRejected(value, positions=positions)
        self.assertRejected(value, normals=value.normals[:-1])
        for normal in ((0., 0., 0.), (math.nan, 0., 1.), (0., 0., 2.), (0., 0.)):
            normals = list(value.normals)
            normals[0] = normal
            self.assertRejected(value, normals=normals)

    def test_optional_normals_must_face_outward_at_every_flat_corner(self):
        value = mesh()
        normals = list(value.normals)
        normals[0] = tuple(-component for component in normals[0])
        self.assertRejected(value, normals=normals)

    def test_exact_normal_guard_rejects_the_scaled_float_wrong_sign_witness(self):
        a, b, c = (2. ** -80, 0.), (1., 3.), (15., 45.)
        outline = ring((a, c, b))
        value = mesh((PolygonSection('lower', 0, 0., (outline,)),
                      PolygonSection('upper', 1, 1., (outline,))))
        ids, positions, normals = list(value.corner_vertex_ids), list(value.positions), list(value.normals)
        wanted_ids = [('lower', 'outer', 'v0'), ('lower', 'outer', 'v2'), ('lower', 'outer', 'v1')]
        mapping = dict(zip(value.corner_vertex_ids, value.positions))
        ids[:3] = wanted_ids
        positions[:3] = [mapping[key] for key in wanted_ids]
        normals[:3] = [(0., 0., 1.)] * 3
        self.assertRejected(value, ids=ids, positions=positions, normals=normals)

    def test_normal_and_identity_leaves_are_snapshotted_before_later_callbacks(self):
        value = mesh()
        ids = [list(key) for key in value.corner_vertex_ids]
        positions, normals = [list(point) for point in value.positions], [list(normal) for normal in value.normals]
        calls = 0
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 2:
                ids[0][:] = ['bad']
                ids.clear()
                positions[0][:] = [math.inf]
                positions.extend(positions * 20)
                normals[0][:] = [math.nan]
                normals.clear()
        validate_ring_loft_delivery(ids, positions, normals=normals, check=mutate)

    def test_delivery_work_checks_retain_callback_exception_identity(self):
        value = mesh()
        for limit in (2, 40, 200):
            marker = RuntimeError('cancel supplied loft')
            calls = 0
            def cancel():
                nonlocal calls
                calls += 1
                if calls == limit:
                    raise marker
            with self.assertRaises(RuntimeError) as caught:
                validate_ring_loft_delivery(value.corner_vertex_ids, value.positions,
                                            normals=value.normals, check=cancel)
            self.assertIs(caught.exception, marker)


class RingLoftTriangleIntersectionTests(unittest.TestCase):
    @staticmethod
    def triangle(points):
        points = tuple(tuple(Fraction(value) for value in point) for point in points)
        normal = cross(subtract(points[1], points[0]), subtract(points[2], points[0]))
        bounds = (tuple(min(point[axis] for point in points) for axis in range(3)),
                  tuple(max(point[axis] for point in points) for axis in range(3)))
        return points, normal, bounds

    def allowed(self, a, b, shared=()):
        return _allowed_intersection(self.triangle(a), self.triangle(b),
                                     tuple(tuple(Fraction(x) for x in point) for point in shared), lambda: None)

    def test_shared_coplanar_edge_is_valid_only_without_folded_overlap(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        edge = ((0, 0, 0), (2, 0, 0))
        self.assertTrue(self.allowed(a, ((2, 0, 0), (0, 0, 0), (0, -2, 0)), edge))
        self.assertFalse(self.allowed(a, ((2, 0, 0), (0, 0, 0), (1, 1, 0)), edge))

    def test_shared_vertex_does_not_permit_an_extra_intersection_segment(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        self.assertTrue(self.allowed(a, ((0, 0, 0), (-1, 0, 1), (0, -1, 1)), ((0, 0, 0),)))
        self.assertFalse(self.allowed(a, ((0, 0, 0), (2, 1, -1), (2, 1, 1)), ((0, 0, 0),)))

    def test_unshared_vertex_on_another_triangle_edge_is_a_touch(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        self.assertFalse(self.allowed(a, ((1, 0, 0), (1, -1, 1), (1, 1, 1))))

    def test_tiny_nonzero_plane_separation_is_not_rounded_to_coplanarity(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        epsilon = 2. ** -80
        self.assertFalse(self.allowed(a, ((.5, -1, -epsilon), (.5, 2, -epsilon), (.5, .5, epsilon))))
        self.assertTrue(self.allowed(a, ((0, 0, epsilon), (2, 0, epsilon), (0, 2, epsilon))))

    def test_overlapping_boxes_do_not_imply_coplanar_triangle_overlap(self):
        a = ((0, 0, 0), (2, 0, 0), (0, 2, 0))
        self.assertTrue(self.allowed(a, ((2, 2, 0), (3, 2, 0), (2, 3, 0))))


if __name__ == '__main__':
    unittest.main()
