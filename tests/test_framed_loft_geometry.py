"""Frozen framed coordinates and hostile source/delivery geometry controls."""
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import unittest

from ontokin.extrusion import PolygonVertex
from ontokin.framed_loft import (FramedPolygonSection, _Exact, placed_cap_axes,
                                 triangulate_framed_loft, validate_framed_loft_delivery)
from ontokin.holes import PolygonRing
from ontokin.model import Pose
from ontokin.ring_loft import PolygonSection, triangulate_ring_loft
from ontokin.surface import SurfaceError, SurfaceMaterial


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = json.loads((ROOT / 'examples/framed-polygon-lofts/expected.json').read_text())
CASES = {case['id']: case for case in EXPECTED['cases']}
FRAME = 'Example.part.frame'


def inputs(name='identity-hollow'):
    wanted = CASES[name]['geometry']
    sections = tuple(FramedPolygonSection(section['key'], section['order'],
        Pose(FRAME, tuple(section['origin_m']), tuple(section['orientation_wxyz'])), tuple(
            PolygonRing(ring['key'], ring['order'], ring['role'], tuple(
                PolygonVertex(vertex['key'], vertex['order'], tuple(vertex['point_m']), vertex['region'])
                for vertex in ring['vertices'])) for ring in section['rings']))
        for section in wanted['sections'])
    palette = tuple(SurfaceMaterial(key, tuple(color), wanted['metallic'], wanted['roughness'])
                    for key, color in wanted['palette'].items())
    return sections, palette, wanted


def mesh(name='identity-hollow', *, sections=None, materials=None, **kwargs):
    original, palette, wanted = inputs(name)
    return triangulate_framed_loft(original if sections is None else sections,
                                    palette if materials is None else materials,
                                    wanted.get('bottom_region', 'bottom'), wanted.get('top_region', 'top'),
                                    owner_frame=FRAME, **kwargs)


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def measurements(value):
    area, volume6, edges = [], Fraction(0), Counter()
    for start in range(0, len(value.positions), 3):
        a, b, c = (tuple(Fraction(x) for x in point) for point in value.positions[start:start + 3])
        face = cross(sub(b, a), sub(c, a))
        area.append(math.hypot(*(float(x) for x in face)) / 2)
        volume6 += dot(a, cross(b, c))
        ids = value.corner_vertex_ids[start:start + 3]
        for first, second in zip(ids, ids[1:] + ids[:1]):
            edges[first, second] += 1
    return math.fsum(area), volume6 / 6, edges


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def quantize(points):
    return tuple(tuple(f32(value) for value in point) for point in points)


def independently_place(point, offset, q):
    length = math.hypot(*q)
    w, x, y, z = (Fraction(value / length) for value in q)
    rows = ((1 - 2 * (y*y + z*z), 2 * (x*y - w*z), 2 * (x*z + w*y)),
            (2 * (x*y + w*z), 1 - 2 * (x*x + z*z), 2 * (y*z - w*x)),
            (2 * (x*z - w*y), 2 * (y*z + w*x), 1 - 2 * (x*x + y*y)))
    return tuple(float(sum(a * Fraction(b) for a, b in zip(row, point))) + shift
                 for row, shift in zip(rows, offset))


class FramedLoftGeometryTests(unittest.TestCase):
    def assertInvalid(self, suffix, sections, **kwargs):
        with self.assertRaises(SurfaceError) as caught:
            mesh(sections=sections, **kwargs)
        self.assertEqual(caught.exception.code, 'OKL-E-FRAMED-LOFT-' + suffix)

    def test_frozen_valid_source_positions_counts_and_exact_determinants(self):
        for name, case in CASES.items():
            if case['expected_outcome'] not in ('valid', 'source_valid_delivery_rejected') or 'geometry' not in case:
                continue
            with self.subTest(case=name):
                value = mesh(name)
                wanted = case['geometry']
                positions = dict(zip(value.corner_vertex_ids, value.positions))
                self.assertEqual(len(positions), wanted['authored_vertex_count'])
                for frozen in wanted['source_positions']:
                    actual = positions[tuple(frozen['identity'])]
                    self.assertEqual([x.hex() for x in actual], frozen['position_hex'])
                area, volume, edges = measurements(value)
                self.assertEqual(volume, Fraction(*(int(x) for x in wanted['volume_exact'])))
                self.assertTrue(math.isclose(area, wanted['surface_area_m2'], rel_tol=1e-12, abs_tol=1e-8))
                self.assertEqual(value.triangle_count, wanted['triangle_count'])
                self.assertEqual(len(value.positions), wanted['vertex_count'])
                self.assertEqual({region.key: len(region.indices) // 3 for region in value.regions},
                                 wanted['region_triangle_counts'])
                for (a, b), count in edges.items():
                    self.assertEqual(count, 1)
                    self.assertEqual(edges[b, a], 1)

    def test_identity_frames_reproduce_c077_geometry_exactly(self):
        sections, palette, unused = inputs()
        original = tuple(PolygonSection(s.key, s.order, s.frame.position[2], s.rings) for s in sections)
        reference = triangulate_ring_loft(original, palette, 'bottom', 'top')
        actual = mesh()
        for field in ('positions', 'normals', 'regions', 'corner_vertex_ids', 'vertex_keys'):
            self.assertEqual(getattr(actual, field), getattr(reference, field))

    def test_equal_quaternion_components_produce_an_exact_right_angle(self):
        value = mesh('bent-solid')
        positions = dict(zip(value.corner_vertex_ids, value.positions))
        self.assertEqual(positions[('s1', 'outer', 'v0')], (4., -1., 5.))
        self.assertEqual(value.cap_axes, ((Fraction(0), Fraction(0), Fraction(1)),
                                         (Fraction(1), Fraction(0), Fraction(0))))
        self.assertEqual(measurements(value)[1], 16)

    def test_reordering_all_declarations_retains_native_output(self):
        sections, palette, unused = inputs('hollow-elbow')
        reordered = tuple(replace(section, rings=tuple(
            replace(ring, vertices=tuple(reversed(ring.vertices))) for ring in reversed(section.rings)))
            for section in reversed(sections))
        self.assertEqual(mesh('hollow-elbow'), mesh('hollow-elbow', sections=reordered,
                                                  materials=tuple(reversed(palette))))

    def test_sign_equivalent_native_quaternions_retain_exact_output(self):
        sections, unused_palette, unused = inputs('hollow-elbow')
        changed = tuple(replace(s, frame=replace(s.frame, rotation=tuple(-q for q in s.frame.rotation)))
                        for s in sections)
        self.assertEqual(mesh('hollow-elbow'), mesh('hollow-elbow', sections=changed))

    def test_native_quaternion_envelope_does_not_renormalize_again(self):
        sections, unused_palette, unused = inputs()
        admitted = math.nextafter(1. + 1e-12, 1.)
        changed = tuple(replace(s, frame=replace(s.frame, rotation=(admitted, 0., 0., 0.))) for s in sections)
        self.assertEqual(mesh(), mesh(sections=changed))
        self.assertInvalid('FRAME', (replace(changed[0], frame=replace(changed[0].frame,
                                       rotation=(1. + 1e-12, 0., 0., 0.))), changed[1]))

    def test_nonplanar_rounded_caps_are_admitted_as_actual_triangles(self):
        value = mesh('rounded-nonplanar-caps')
        positions = dict(zip(value.corner_vertex_ids, value.positions))
        for key in (value.section_keys[0], value.section_keys[-1]):
            points = [tuple(Fraction(x) for x in positions[(key, 'outer', 'v' + str(i))]) for i in range(4)]
            determinant = dot(sub(points[3], points[0]), cross(sub(points[1], points[0]), sub(points[2], points[0])))
            self.assertNotEqual(determinant, 0)

    def test_exact_progression_rejects_zero_sideways_reverse_and_short_steps(self):
        lower, upper = inputs()[0]
        for origin in ((0., 0., 0.), (2., 0., 0.), (0., 0., -1.),
                       (0., 0., math.nextafter(.001, 0.))):
            with self.subTest(origin=origin):
                self.assertInvalid('PROGRESSION', (lower, replace(upper, frame=replace(upper.frame, position=origin))))
        mesh(sections=(lower, replace(upper, frame=replace(upper.frame, position=(0., 0., .001)))))
        self.assertInvalid('PROGRESSION', (replace(lower, frame=replace(lower.frame, position=(0., 0., 1.))),
            replace(upper, frame=replace(upper.frame, position=(0., 0., 1.001)))))

    def test_near_half_turn_has_no_added_angular_threshold(self):
        value = mesh('near-half-turn-admitted')
        self.assertGreater(measurements(value)[1], 0)
        lower, upper = inputs()[0]
        self.assertInvalid('PROGRESSION', (lower, replace(upper, frame=replace(upper.frame,
                                            rotation=(0., 0., 1., 0.)))))

    def test_frame_reference_and_consuming_owner_are_checked(self):
        lower, upper = inputs()[0]
        for frame in ('world', 'Other.part.frame', '', None, '.frame'):
            with self.subTest(frame=frame):
                self.assertInvalid('FRAME', (lower, replace(upper, frame=replace(upper.frame, frame=frame))))

    def test_source_frame_category_and_origin_dimensions_keep_distinct_diagnostics(self):
        from ontokin.budget_runtime import execute_framed_loft_export
        from ontokin.bundle import ProgramBundle, SourceUnit

        for name, code in (('wrong-frame-type', 'OKL-E-TYPE'),
                           ('wrong-origin-type', 'OKL-E-TYPE'),
                           ('wrong-origin-unit', 'OKL-E-UNIT')):
            with self.subTest(case=name):
                filename = CASES[name]['source']
                raw = (ROOT / 'examples/framed-polygon-lofts' / filename).read_bytes()
                source = ProgramBundle(SourceUnit('entry', filename, raw))
                result = execute_framed_loft_export(source)
                self.assertIsNone(result.data)
                self.assertEqual(result.report['diagnostics'][0]['code'], code, result.report)

    def test_native_pose_shapes_and_nonrigid_values_are_rejected(self):
        lower, upper = inputs()[0]
        frames = (None, {'scale': [1, 1, 1]}, Pose(FRAME, (0, 0), (1, 0, 0, 0)),
                  Pose(FRAME, (0, 0, 4), (1, 0, 0)), Pose(FRAME, (0, 0, 4), (0, 0, 0, 0)),
                  Pose(FRAME, (0, 0, 4), (2, 0, 0, 0)), Pose(FRAME, (0, 0, 4), (True, 0, 0, 0)),
                  Pose(FRAME, (math.inf, 0, 4)), Pose(FRAME, (0, 0, 4), (math.nan, 0, 0, 0)),
                  Pose(FRAME, (math.nextafter(100., math.inf), 0, 4)))
        for frame in frames:
            with self.subTest(frame=frame):
                self.assertInvalid('FRAME', (lower, replace(upper, frame=frame)))

    def test_section_keys_orders_counts_and_vertex_allocation_are_bounded(self):
        lower, upper = inputs()[0]
        for sections in ((), (lower,), (lower, upper) * 5):
            self.assertInvalid('SECTION', sections)
        self.assertInvalid('SECTION', (lower, replace(upper, key=lower.key)))
        for order in (True, -1, 65536, 1.5, lower.order):
            self.assertInvalid('ORDER', (lower, replace(upper, order=order)))
        with self.assertRaises(SurfaceError) as caught:
            mesh(max_vertices=95)
        self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')
        self.assertEqual(caught.exception.details, {'required': 96, 'available': 95})

    def test_correspondence_requires_authored_identity_not_nearest_point(self):
        lower, upper = inputs()[0]
        ring = upper.rings[0]
        changed = replace(ring, vertices=(replace(ring.vertices[0], key='different'),) + ring.vertices[1:])
        self.assertInvalid('CORRESPONDENCE', (lower, replace(upper, rings=(changed,) + upper.rings[1:])))
        self.assertInvalid('CORRESPONDENCE', (lower, replace(upper, rings=upper.rings[:1])))

    def test_source_rounding_collapse_is_a_topology_refusal(self):
        lower, upper = inputs('identity-solid')[0]
        points = ((0., -1.), (1e-15, -1.), (1e-15, 1.), (0., 1.))
        outline = replace(lower.rings[0], vertices=tuple(replace(v, point_m=p)
                              for v, p in zip(lower.rings[0].vertices, points)))
        changed = tuple(replace(s, rings=(outline,), frame=replace(s.frame, position=(100., 0., s.frame.position[2])))
                        for s in (lower, upper))
        self.assertInvalid('TOPOLOGY', changed)

    def test_valid_frames_do_not_authorize_a_pinched_connecting_surface(self):
        sections, unused_palette, unused = inputs('bent-solid')
        changed = (sections[0], replace(sections[1], frame=replace(sections[1].frame, position=(1., 0., 1.))))
        self.assertInvalid('TOPOLOGY', changed)

    def test_complete_mutable_pose_and_ring_leaves_are_snapshotted(self):
        sections, palette, unused = inputs('hollow-elbow')
        source = [replace(s, frame=Pose(s.frame.frame, list(s.frame.position), list(s.frame.rotation)),
                    rings=[replace(r, vertices=[replace(v, point_m=list(v.point_m)) for v in r.vertices])
                           for r in s.rings]) for s in sections]
        materials = [replace(m, rgba=list(m.rgba)) for m in palette]
        calls = 0
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 2:
                source[-1].frame.position[:] = [1000., 0., 0.]
                source[-1].frame.rotation[:] = [0., 0., 0., 0.]
                object.__setattr__(source[-1].frame, 'frame', 'foreign.frame')
                source[-1].rings[0].vertices[0].point_m[0] = 500.
                source[-1].rings.extend(source[-1].rings * 20)
                source.extend(source * 10)
                materials[0].rgba[0] = 9.
                materials.extend(materials * 10)
        self.assertEqual(mesh('hollow-elbow'), mesh('hollow-elbow', sections=source, materials=materials, check=mutate))

    def test_dynamic_section_and_pose_subclasses_are_not_admitted(self):
        class DynamicSection(FramedPolygonSection):
            pass
        class DynamicPose(Pose):
            pass
        lower, upper = inputs()[0]
        self.assertInvalid('SECTION', (DynamicSection(lower.key, lower.order, lower.frame, lower.rings), upper))
        self.assertInvalid('FRAME', (replace(lower, frame=DynamicPose(FRAME, (0., 0., 0.))), upper))

    def test_shared_work_preserves_cancellation_exception_identity(self):
        calls = 0
        def count():
            nonlocal calls
            calls += 1
        mesh('bent-solid', check=count)
        total = calls
        for limit in (2, 60, total // 2, total - 1):
            marker = RuntimeError('stop at ' + str(limit))
            calls = 0
            def cancel():
                nonlocal calls
                calls += 1
                if calls == limit:
                    raise marker
            with self.assertRaises(RuntimeError) as caught:
                mesh('bent-solid', check=cancel)
            self.assertIs(caught.exception, marker)

    def test_new_exact_operations_enforce_the_unchanged_operand_limit(self):
        work = _Exact(None)
        for operation in (lambda: work.fraction(1 << 32768),
                          lambda: work.mul(Fraction((1 << 20000) + 1), Fraction((1 << 20000) + 3))):
            with self.assertRaises(SurfaceError) as caught:
                operation()
            self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')
            self.assertEqual(caught.exception.details['budget'], 'numeric_operand_bits')
            self.assertEqual(caught.exception.details['limit'], 32768)


class FramedLoftDeliveryTests(unittest.TestCase):
    def validate(self, value, *, ids=None, positions=None, normals=None, axes=None, keys=None, check=None):
        return validate_framed_loft_delivery(value.corner_vertex_ids if ids is None else ids,
            quantize(value.positions) if positions is None else positions,
            section_keys=value.section_keys if keys is None else keys,
            cap_axes=value.cap_axes if axes is None else axes,
            normals=normals, check=check)

    def assertRejected(self, value, **kwargs):
        with self.assertRaises(SurfaceError) as caught:
            self.validate(value, **kwargs)
        self.assertEqual(caught.exception.code, 'OKL-E-FRAMED-LOFT-NUMERIC')

    def test_bent_hollow_handle_and_nonplanar_caps_survive_delivery(self):
        for name in ('bent-solid', 'hollow-elbow', 'solid-handle', 'hollow-handle',
                     'rounded-nonplanar-caps', 'near-half-turn-admitted'):
            with self.subTest(case=name):
                value = mesh(name)
                self.validate(value, normals=quantize(value.normals))

    def test_frozen_precision_cases_require_actual_geometric_refusal(self):
        for name, case in CASES.items():
            if case['expected_outcome'] != 'source_valid_delivery_rejected':
                continue
            with self.subTest(case=name):
                value, wanted = mesh(name), case['geometry']
                offset = wanted.get('local_position_m', (0., 0., 0.))
                q = wanted.get('local_orientation_wxyz', (1., 0., 0., 0.))
                positions = quantize(tuple(independently_place(p, offset, q) for p in value.positions))
                axes = placed_cap_axes(value.cap_axes, q)
                self.assertRejected(value, positions=positions, axes=axes)

    def test_general_outer_rotation_uses_inherited_arithmetic_and_exact_cap_axes(self):
        value = mesh('hollow-handle')
        q = (.8, .36, .48, 0.)
        offset = (.123, -.456, .789)
        positions = quantize(tuple(independently_place(p, offset, q) for p in value.positions))
        normals = quantize(tuple(independently_place(n, (0., 0., 0.), q) for n in value.normals))
        axes = placed_cap_axes(value.cap_axes, q)
        self.validate(value, positions=positions, normals=normals, axes=axes)

    def test_wrong_cap_axis_is_rejected_even_when_closed_mesh_is_unchanged(self):
        value = mesh('hollow-elbow')
        self.assertRejected(value, axes=(tuple(-x for x in value.cap_axes[0]), value.cap_axes[1]))
        self.assertRejected(value, axes=(value.cap_axes[0], tuple(-x for x in value.cap_axes[1])))

    def test_cap_axis_and_section_inventory_shapes_are_admitted_before_work(self):
        value = mesh()
        for axes in ((), ((0, 0, 0), (0, 0, 1)), ((True, 0, 1), (0, 0, 1)),
                     ((0, 0, math.nan), (0, 0, 1)), ((0, 1), (0, 0, 1))):
            with self.subTest(axes=axes):
                self.assertRejected(value, axes=axes)
        for keys in ((), (value.section_keys[0],) * 2, ('different', value.section_keys[-1])):
            self.assertRejected(value, keys=keys)

    def test_axis_operand_bound_precedes_unbounded_fraction_operations(self):
        value = mesh()
        with self.assertRaises(SurfaceError) as caught:
            self.validate(value, axes=((Fraction(1, 1 << 32768), 0, 1), (0, 0, 1)))
        self.assertEqual(caught.exception.code, 'OKL-E-RESOURCE')

    def test_mutable_delivery_and_axis_inputs_are_captured_before_callbacks(self):
        value = mesh('bent-solid')
        points = [list(p) for p in quantize(value.positions)]
        ids = [list(v) for v in value.corner_vertex_ids]
        axes = [list(axis) for axis in value.cap_axes]
        calls = 0
        def mutate():
            nonlocal calls
            calls += 1
            if calls == 1:
                points[0][0] = 1000.
                ids[0][0] = 'changed'
                axes[0][:] = [0, 0, -1]
        self.validate(value, ids=ids, positions=points, axes=axes, check=mutate)

    def test_mutable_outer_rotation_is_captured_before_callbacks(self):
        value = mesh('bent-solid')
        rotation = [1., 0., 0., 0.]
        axes = [list(axis) for axis in value.cap_axes]
        def mutate():
            rotation[:] = [0., 0., 0., 0.]
            axes[0][:] = [0, 0, -1]
        self.assertEqual(placed_cap_axes(axes, rotation, check=mutate), value.cap_axes)

    def test_missing_duplicate_and_reversed_faces_are_rejected(self):
        value = mesh('bent-solid')
        self.assertRejected(value, ids=value.corner_vertex_ids[:-3], positions=value.positions[:-3])
        self.assertRejected(value, ids=value.corner_vertex_ids + value.corner_vertex_ids[:3],
                            positions=value.positions + value.positions[:3])
        ids, positions = list(value.corner_vertex_ids), list(value.positions)
        ids[:3], positions[:3] = ids[:3][::-1], positions[:3][::-1]
        self.assertRejected(value, ids=ids, positions=positions)

    def test_inconsistent_identity_and_hostile_identity_leaf_are_rejected(self):
        value = mesh('bent-solid')
        points = list(value.positions)
        points[0] = tuple(x + .01 for x in points[0])
        self.assertRejected(value, positions=points)
        ids = list(value.corner_vertex_ids)
        ids[0] = ([], ids[0][1], ids[0][2])
        self.assertRejected(value, ids=ids)

    def test_delivery_cancellation_preserves_the_original_exception(self):
        value = mesh('bent-solid')
        marker = RuntimeError('delivery cancelled')
        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            if calls == 100:
                raise marker
        with self.assertRaises(RuntimeError) as caught:
            self.validate(value, check=cancel)
        self.assertIs(caught.exception, marker)


if __name__ == '__main__':
    unittest.main()
