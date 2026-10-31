"""Independent frozen measurements and hostile native pocket construction."""
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path
import unittest

from ontokin.extrusion import PolygonVertex, triangulate_extrusion
from ontokin.pockets import (PolygonPocket, _Exact, _admit_face, _floor_details,
                             triangulate_pockets)
from ontokin.surface import SurfaceError, SurfaceMaterial


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / 'examples/polygon-pockets/expected.json').read_text())
CASES = {case['id']: case for case in EXPECTED['cases']}


def inputs(name='rectangular-pocket'):
    wanted = CASES[name]['geometry']
    def vertices(values):
        return tuple(PolygonVertex(value['key'], value['order'], tuple(value['point_m']), value['region'])
                     for value in values)
    outer = vertices(wanted['outer_vertices'])
    pockets = tuple(PolygonPocket(value['key'], value['order'], vertices(value['vertices']),
                                   value['depth_m'], value['floor_region']) for value in wanted['pockets'])
    palette = tuple(SurfaceMaterial(key, tuple(color), wanted['metallic'], wanted['roughness'])
                    for key, color in wanted['palette'].items())
    return outer, pockets, palette, wanted


def mesh(name='rectangular-pocket', *, outer=None, pockets=None, materials=None,
         height=None, bottom=None, top=None, **kwargs):
    original_outer, original_pockets, palette, wanted = inputs(name)
    return triangulate_pockets(original_outer if outer is None else outer,
                                original_pockets if pockets is None else pockets,
                                palette if materials is None else materials,
                                wanted['height_m'] if height is None else height,
                                wanted['bottom_region'] if bottom is None else bottom,
                                wanted['top_region'] if top is None else top, **kwargs)


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def measurements(value):
    area, volume6, edges = [], Fraction(0), Counter()
    for start in range(0, len(value.positions), 3):
        a, b, c = (tuple(Fraction(component) for component in point)
                   for point in value.positions[start:start + 3])
        face = cross(sub(b, a), sub(c, a))
        area.append(math.hypot(*(float(component) for component in face)) / 2)
        volume6 += dot(a, cross(b, c))
        ids = value.corner_vertex_ids[start:start + 3]
        for first, second in zip(ids, ids[1:] + ids[:1]):
            edges[first, second] += 1
    return math.fsum(area), volume6 / 6, edges


class PocketsGeometryTests(unittest.TestCase):
    def assertInvalid(self, suffix, **kwargs):
        with self.assertRaises(SurfaceError) as caught:
            mesh(**kwargs)
        self.assertEqual(caught.exception.code, 'OKL-E-POCKETS-' + suffix)

    def test_all_frozen_source_valid_positions_counts_and_measures(self):
        for name, case in CASES.items():
            if case['expected_outcome'] not in ('valid', 'source_valid_delivery_rejected'):
                continue
            with self.subTest(case=name):
                wanted = case['geometry']
                value = mesh(name)
                actual = dict(zip(value.corner_vertex_ids, value.positions))
                self.assertEqual(len(actual), wanted['logical_vertex_count'])
                self.assertEqual(set(actual), {tuple(row['identity']) for row in wanted['source_positions']})
                for row in wanted['source_positions']:
                    self.assertEqual(actual[tuple(row['identity'])], tuple(row['position_m']))
                area, volume, edges = measurements(value)
                self.assertEqual(volume, Fraction(*(int(part) for part in wanted['volume_exact'])))
                self.assertTrue(math.isclose(area, wanted['surface_area_m2'], rel_tol=1e-12, abs_tol=1e-9))
                self.assertEqual(value.triangle_count, wanted['triangle_count'])
                self.assertEqual(len(value.positions), wanted['vertex_count'])
                self.assertEqual({region.key: len(region.indices)//3 for region in value.regions},
                                 wanted['region_triangle_counts'])
                for (first, second), count in edges.items():
                    self.assertEqual(count, 1)
                    self.assertEqual(edges[second, first], 1)

    def test_zero_pockets_retain_unchanged_extrusion_streams(self):
        for name in ('zero-pockets', 'zero-pockets-concave', 'minimum-body-height',
                     'maximum-vertices-zero-pockets'):
            with self.subTest(case=name):
                outer, pockets, palette, wanted = inputs(name)
                reference = triangulate_extrusion(outer, palette, wanted['height_m'],
                                                   wanted['bottom_region'], wanted['top_region'])
                value = mesh(name)
                self.assertFalse(pockets)
                for field in ('positions', 'normals', 'regions'):
                    self.assertEqual(getattr(value, field), getattr(reference, field))

    def test_signed_zero_zero_pocket_streams_are_not_reinterpreted(self):
        outer, unused, palette, wanted = inputs('zero-pockets')
        outer = tuple(replace(vertex, point_m=tuple(-0.0 if value == 0 else value for value in vertex.point_m))
                      for vertex in outer)
        original = triangulate_extrusion(outer, palette, wanted['height_m'], 'bottom', 'top')
        value = mesh('zero-pockets', outer=outer)
        self.assertEqual([[part.hex() for part in point] for point in value.positions],
                         [[part.hex() for part in point] for point in original.positions])

    def test_rectangular_control_has_upward_floor_and_downward_bottom(self):
        value = mesh()
        counts = Counter()
        for start in range(0, len(value.positions), 3):
            ids = value.corner_vertex_ids[start:start+3]
            if {identity[3] for identity in ids} == {'lower'}:
                kind = ids[0][0]
                self.assertTrue(all(identity[0] == kind for identity in ids))
                expected = (0.0, 0.0, -1.0 if kind == 'outer' else 1.0)
                self.assertEqual(value.normals[start:start+3], (expected,)*3)
                counts[kind] += 1
        self.assertEqual(counts, {'outer': 2, 'pocket': 2})

    def test_vertex_and_pocket_declaration_reordering_preserves_streams(self):
        outer, pockets, palette, unused = inputs('unequal-depths')
        reordered = tuple(replace(pocket, vertices=tuple(reversed(pocket.vertices)))
                          for pocket in reversed(pockets))
        before = mesh('unequal-depths')
        after = mesh('unequal-depths', outer=tuple(reversed(outer)), pockets=reordered,
                     materials=tuple(reversed(palette)))
        self.assertEqual(before, after)

    def test_outer_named_pocket_keeps_distinct_identity_namespace(self):
        value = mesh('pocket-key-outer')
        ids = set(value.corner_vertex_ids)
        self.assertTrue(any(identity[:2] == ('outer', 'outer') for identity in ids))
        self.assertTrue(any(identity[:2] == ('pocket', 'outer') for identity in ids))
        self.assertEqual(len(ids), 16)

    def test_exact_base_threshold_precedes_rounding(self):
        unused, floor, base, effective = _floor_details(0.002, 0.001)
        self.assertEqual(base, Fraction(0.001))
        self.assertEqual(floor, 0.001)
        self.assertEqual(effective, Fraction(0.001))
        with self.assertRaises(SurfaceError) as caught:
            _floor_details(math.nextafter(0.002, 0.0), 0.001)
        self.assertEqual(caught.exception.code, 'OKL-E-POCKETS-BASE')
        _floor_details(math.nextafter(0.002, math.inf), 0.001)

    def test_frozen_rounded_floor_retains_authored_and_effective_depth_fields(self):
        unused, pockets, unused_palette, wanted = inputs('rounded-floor')
        pocket, frozen = pockets[0], wanted['pockets'][0]
        depth, floor, base, effective = _floor_details(wanted['height_m'], pocket.depth_m)
        self.assertEqual(depth, frozen['depth_m'])
        self.assertEqual(floor, frozen['floor_m'])
        self.assertEqual(base, Fraction(int(frozen['exact_remaining_base_m']['numerator']),
                                       int(frozen['exact_remaining_base_m']['denominator'])))
        self.assertEqual(effective, Fraction(int(frozen['effective_depth_m']['numerator']),
                                            int(frozen['effective_depth_m']['denominator'])))
        self.assertEqual(base, Fraction(wanted['height_m']) - Fraction(depth))
        self.assertEqual(effective, Fraction(wanted['height_m']) - Fraction(floor))

    def test_separate_native_floor_rounding_witness_has_distinct_effective_depth(self):
        # This additional native control is not a modification of the frozen
        # rounded-floor source, whose canonical .3/.1 subtraction is exact
        depth, floor, base, effective = _floor_details(1.0, 0.1)
        self.assertEqual(base, Fraction(1.0) - Fraction(0.1))
        self.assertEqual(floor, float(base))
        self.assertEqual(effective, Fraction(1.0) - Fraction(floor))
        self.assertNotEqual(effective, Fraction(depth))

    def test_new_face_admission_uses_exact_stored_coordinate_orientation(self):
        a, b, c = (2.**-80, 0., 0.), (1., 3., 0.), (15., 45., 0.)
        _admit_face(a, b, c, (0., 0., -1.))
        with self.assertRaises(SurfaceError) as caught:
            _admit_face(a, b, c, (0., 0., 1.))
        self.assertEqual(caught.exception.code, 'OKL-E-POCKETS-NUMERIC')
        with self.assertRaises(SurfaceError):
            _admit_face((0.,0.,0.), b, c, (0.,0.,1.))

    def test_depth_and_height_native_domains(self):
        unused, pockets, unused_palette, unused_wanted = inputs()
        for value in (0, -1, 0.0001, 100.01, math.nan, math.inf, True, '2'):
            with self.subTest(height=value):
                self.assertInvalid('HEIGHT', height=value)
        for value in (0, -1, 0.0001, 2, 3, 100.01, math.nan, math.inf, True, '1'):
            with self.subTest(depth=value):
                self.assertInvalid('DEPTH', pockets=(replace(pockets[0], depth_m=value),))

    def test_remaining_base_refusal_is_distinct_from_penetration(self):
        unused, pockets, unused_palette, unused_wanted = inputs()
        self.assertInvalid('BASE', height=0.002,
                           pockets=(replace(pockets[0], depth_m=math.nextafter(0.001, math.inf)),))
        self.assertInvalid('DEPTH', height=0.002, pockets=(replace(pockets[0], depth_m=0.002),))

    def test_pocket_and_vertex_native_count_bounds(self):
        outer, pockets, unused_palette, unused_wanted = inputs()
        for value in ([], outer[:2]):
            self.assertInvalid('VERTEX', outer=value)
        self.assertInvalid('VERTEX', pockets=(replace(pockets[0], vertices=pockets[0].vertices[:2]),))
        self.assertInvalid('POCKET', pockets=[pockets[0]]*9)
        self.assertInvalid('POCKET', pockets=[object()])
        self.assertInvalid('VERTEX', outer=[outer[0]]*65)

    def test_aggregate_boundary_count_is_not_per_pocket(self):
        unused, pockets, unused_palette, unused_wanted = inputs('maximum-pockets-and-vertices')
        extra = replace(pockets[0].vertices[0], key='extra', order=65535, point_m=(0.123, 0.456))
        changed = (replace(pockets[0], vertices=(*pockets[0].vertices, extra)), *pockets[1:])
        self.assertInvalid('VERTEX', name='maximum-pockets-and-vertices', pockets=changed)

    def test_native_order_key_and_coordinate_domains(self):
        outer, pockets, unused_palette, unused_wanted = inputs()
        for value in (-1, 65536, True, 1.5):
            self.assertInvalid('ORDER', pockets=(replace(pockets[0], order=value),))
            self.assertInvalid('ORDER', outer=(replace(outer[0], order=value), *outer[1:]))
        self.assertInvalid('POCKET', pockets=(replace(pockets[0], key='bad key'),))
        self.assertInvalid('VERTEX', outer=(replace(outer[0], key='bad key'), *outer[1:]))
        for point in ((101, 0), (math.nan, 0), (True, 0), (0,), [0, 0, 0]):
            self.assertInvalid('POINT', outer=(replace(outer[0], point_m=point), *outer[1:]))

    def test_duplicate_native_keys_and_orders_refuse(self):
        outer, pockets, unused_palette, unused_wanted = inputs()
        self.assertInvalid('POCKET', pockets=(pockets[0], replace(pockets[0], order=30)))
        self.assertInvalid('ORDER', pockets=(pockets[0], replace(pockets[0], key='different')))
        self.assertInvalid('VERTEX', outer=(outer[0], replace(outer[1], key=outer[0].key), *outer[2:]))
        self.assertInvalid('ORDER', outer=(outer[0], replace(outer[1], order=outer[0].order), *outer[2:]))

    def test_wrong_boundary_winding_is_not_repaired(self):
        outer, pockets, unused_palette, unused_wanted = inputs()
        reverse_outer = tuple(replace(vertex, order=index) for index, vertex in enumerate(reversed(outer)))
        self.assertInvalid('WINDING', outer=reverse_outer)
        reverse_pocket = tuple(replace(vertex, order=index)
                               for index, vertex in enumerate(reversed(pockets[0].vertices)))
        self.assertInvalid('WINDING', pockets=(replace(pockets[0], vertices=reverse_pocket),))

    def test_touching_outside_and_nested_pockets_refuse(self):
        unused, pockets, unused_palette, unused_wanted = inputs()
        def shifted(dx, dy):
            return tuple(replace(vertex, point_m=(vertex.point_m[0]+dx, vertex.point_m[1]+dy))
                          for vertex in pockets[0].vertices)
        self.assertInvalid('TOPOLOGY', pockets=(replace(pockets[0], vertices=shifted(-1, 0)),))
        self.assertInvalid('CONTAINMENT', pockets=(replace(pockets[0], vertices=shifted(10, 0)),))
        nested = tuple(replace(vertex, point_m=(1.5+(vertex.point_m[0]-1)*0.5,
                                                 1.25+(vertex.point_m[1]-1)*0.5))
                       for vertex in pockets[0].vertices)
        self.assertInvalid('CONTAINMENT', pockets=(pockets[0],
                           replace(pockets[0], key='nested', order=30, vertices=nested)))

    def test_duplicate_and_collinear_points_refuse(self):
        outer, pockets, unused_palette, unused_wanted = inputs()
        self.assertInvalid('TOPOLOGY', outer=(outer[0], replace(outer[1], point_m=outer[0].point_m), *outer[2:]))
        extra = replace(outer[0], key='middle', order=5, point_m=(2, 0))
        self.assertInvalid('TOPOLOGY', outer=(outer[0], extra, *outer[1:]))

    def test_all_cap_and_wall_regions_must_resolve(self):
        outer, pockets, unused_palette, unused_wanted = inputs()
        self.assertInvalid('REGION', bottom='absent')
        self.assertInvalid('REGION', top='absent')
        self.assertInvalid('REGION', outer=(replace(outer[0], region='absent'), *outer[1:]))
        self.assertInvalid('REGION', pockets=(replace(pockets[0], floor_region='absent'),))
        vertices = (replace(pockets[0].vertices[0], region='absent'), *pockets[0].vertices[1:])
        self.assertInvalid('REGION', pockets=(replace(pockets[0], vertices=vertices),))
        self.assertInvalid('REGION', name='zero-pockets', top='absent')

    def test_palette_and_aggregate_mesh_budget_keep_inherited_codes(self):
        unused, unused_pockets, palette, unused_wanted = inputs()
        for value in ([], [palette[0]]*17):
            with self.assertRaises(SurfaceError) as caught:
                mesh(materials=value)
            self.assertEqual(caught.exception.code, 'OKL-E-SURFACE-MATERIAL')
        for limit in (83, -1, 250001, True):
            with self.assertRaises(SurfaceError) as caught:
                mesh(max_vertices=limit)
            self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')
        self.assertEqual(len(mesh(max_vertices=84).positions), 84)

    def test_complete_native_snapshot_precedes_mutating_callbacks(self):
        original = mesh()
        outer, pockets, palette, unused = inputs()
        outer = [replace(vertex, point_m=list(vertex.point_m)) for vertex in outer]
        inner = [replace(vertex, point_m=list(vertex.point_m)) for vertex in pockets[0].vertices]
        pockets = [replace(pockets[0], vertices=inner)]
        palette = [replace(material, rgba=list(material.rgba)) for material in palette]
        called = 0
        def mutate():
            nonlocal called
            called += 1
            if called == 1:
                outer[0].point_m[:] = [math.nan, math.nan]
                inner[0].point_m.clear()
                palette[0].rgba.clear()
                outer.clear()
                pockets.clear()
                palette.clear()
        actual = mesh(outer=outer, pockets=pockets, materials=palette, check=mutate)
        self.assertEqual(actual, original)
        self.assertGreater(called, 1)

    def test_callback_failure_identity_survives_inherited_error_mapping(self):
        for target in (1, 120, 240):
            with self.subTest(checkpoint=target):
                sentinel = SurfaceError('OKL-E-HOLES-TOPOLOGY', 'caller-owned sentinel')
                calls = 0
                def stop():
                    nonlocal calls
                    calls += 1
                    if calls == target:
                        raise sentinel
                with self.assertRaises(SurfaceError) as caught:
                    mesh(check=stop)
                self.assertIs(caught.exception, sentinel)
                self.assertEqual(calls, target)

    def test_base_exception_cancellation_identity_survives(self):
        sentinel = KeyboardInterrupt('caller cancellation')
        def stop():
            raise sentinel
        with self.assertRaises(KeyboardInterrupt) as caught:
            mesh(check=stop)
        self.assertIs(caught.exception, sentinel)

    def test_exact_operand_guard_precedes_oversized_arithmetic(self):
        exact = _Exact(None)
        for operation in (lambda: exact.fraction(1 << 32769),
                          lambda: exact.sub(Fraction(1 << 32760), Fraction(1, 1 << 20)),
                          lambda: exact.less(Fraction(1 << 32760), Fraction(1, 1 << 20))):
            with self.assertRaises(SurfaceError) as caught:
                operation()
            self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')

    def test_floor_arithmetic_charges_operations_without_reset(self):
        calls = []
        _floor_details(2, 0.5, check=lambda: calls.append(1))
        first = len(calls)
        self.assertGreater(first, 5)
        _floor_details(2, 0.5, check=lambda: calls.append(1))
        self.assertEqual(len(calls), 2*first)

    def test_summary_preserves_frozen_floor_and_material_counts(self):
        from ontokin.pockets_inspection import pockets_summary
        for name in ('rounded-floor', 'zero-pockets', 'unequal-depths', 'maximum-pockets-and-vertices'):
            with self.subTest(case=name):
                outer, pockets, palette, wanted = inputs(name)
                recipe = {'kind':'pockets', 'outer_vertices':outer, 'pockets':pockets,
                          'materials':palette, 'height_m':wanted['height_m'],
                          'bottom_region':wanted['bottom_region'], 'top_region':wanted['top_region']}
                summary = pockets_summary(recipe)
                for field in ('pocket_count','authored_vertex_count','logical_vertex_count',
                              'bottom_triangle_count','top_triangle_count','floor_triangle_count',
                              'wall_triangle_count','triangle_count','vertex_count'):
                    self.assertEqual(summary[field], wanted[field])
                self.assertEqual({region['key']: region['triangle_count'] for region in summary['regions']},
                                 wanted['region_triangle_counts'])
                for actual, frozen in zip(summary['pockets'], sorted(wanted['pockets'], key=lambda value:value['order'])):
                    for field in ('key','order','depth_m','floor_m','remaining_base_m',
                                  'exact_remaining_base_m','effective_depth_m','floor_region'):
                        self.assertEqual(actual[field], frozen[field])


if __name__ == '__main__':
    unittest.main()
