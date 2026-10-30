"""Independent hand-built meshes and hostile supplied-byte controls for C077.

The product compiler, exporter, triangulator and intersection predicate are
never imported. Cap partitions are written by hand for these small controls.
"""
from __future__ import annotations

from collections import defaultdict
import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import struct
import unittest

from tools.ring_loft_oracles import Decoded, check_geometry, check_glb, check_surface_intersections
from tools.ring_loft_oracles import _check_face_normals, _exact_signed_volume6


ROOT = Path(__file__).resolve().parents[1]
FROZEN = json.loads((ROOT / 'examples/polygon-lofts/expected.json').read_text())
GEOMETRIES = {case['id']: case['geometry'] for case in FROZEN['cases'] if 'geometry' in case}


class Supplied:
    def __init__(self, rows):
        self.rows = rows

    def triangles(self, path):
        assert path == 'shape'
        return self.rows


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def hand_loft(wanted, cap_override=None):
    """Attach explicit square/annular cap partitions to prescribed strips."""
    sections = sorted(wanted['sections'], key=lambda section: section['order'])
    levels, ring_rows = [], []
    for section in sections:
        rings = sorted(section['rings'], key=lambda ring: ring['order'])
        vertices = [sorted(ring['vertices'], key=lambda vertex: vertex['order']) for ring in rings]
        levels.append([(*vertex['point_m'], section['station_m']) for row in vertices for vertex in row])
        ring_rows.append(vertices)
    n = len(levels[0])
    if n == 4:
        bottom = top = [(0, 1, 2), (0, 2, 3)]
        if wanted.get('cap_diagonal_control'):
            top = [(0, 1, 3), (1, 2, 3)]
    elif n == 8 and wanted['hole_count'] == 1:
        bottom = top = [(0, 1, 6), (0, 6, 7), (1, 2, 5), (1, 5, 6),
                        (2, 3, 4), (2, 4, 5), (3, 0, 7), (3, 7, 4)]
    else:
        raise AssertionError('This hand-built control only supplies four-sided boundaries')
    if cap_override:
        bottom, top = cap_override
    offset = wanted.get('local_position_m', [0, 0, 0])
    rotation = wanted.get('local_orientation_wxyz', [1, 0, 0, 0])
    assert rotation in ([1, 0, 0, 0], [0, 1, 0, 0])

    def rotate(point):
        return tuple(point) if rotation[0] == 1 else (point[0], -point[1], -point[2])

    rows = []

    def emit(region, points):
        a, b, c = points
        u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        face = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        length = math.hypot(*face)
        normal = tuple(f32(value / length) for value in rotate(face))
        positions = [tuple(f32(value + shift) for value, shift in zip(rotate(point), offset)) for point in points]
        pbr = {'baseColorFactor': copy.deepcopy(wanted['palette'][region]),
               'metallicFactor': wanted['metallic'], 'roughnessFactor': wanted['roughness']}
        material = {'pbrMetallicRoughness': pbr, 'extras': {'ontokin': {'source_region_key': region}}}
        rows.append([region, positions, [normal] * 3, material])

    for triangle in bottom:
        emit('bottom', [levels[0][i] for i in reversed(triangle)])
    for triangle in top:
        emit('top', [levels[-1][i] for i in triangle])
    for level in range(len(sections) - 1):
        start = 0
        for vertices in ring_rows[level]:
            count = len(vertices)
            for i, vertex in enumerate(vertices):
                a, b = start + i, start + (i + 1) % count
                emit(vertex['region'], [levels[level][a], levels[level][b], levels[level + 1][a]])
                emit(vertex['region'], [levels[level][b], levels[level + 1][b], levels[level + 1][a]])
            start += count
    return rows


def pack_document(document, binary=b''):
    payload = json.dumps(document, separators=(',', ':')).encode()
    payload += b' ' * (-len(payload) % 4)
    binary += b'\x00' * (-len(binary) % 4)
    return (struct.pack('<III', 0x46546c67, 2, 28 + len(payload) + len(binary))
            + struct.pack('<II', len(payload), 0x4e4f534a) + payload
            + struct.pack('<II', len(binary), 0x004e4942) + binary)


def hand_document(rows):
    """Encode actual independent position/normal/index/animation accessors."""
    document = {'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
                'nodes': [{'mesh': 0, 'translation': [0, 0, 0], 'rotation': [0, 0, 0, 1],
                           'extras': {'ontokin': {'kind': 'object', 'path': 'shape'}}}],
                'meshes': [{'primitives': []}], 'materials': [], 'accessors': [], 'bufferViews': [],
                'buffers': [{'byteLength': 0}],
                'extras': {'ontokin': {'target_contract': 'ontokin.glb/0.10', 'profile': 'polygon-loft-0.1',
                                       'schema_version': '0.10', 'program': {'revision': 'sha256:fixture'}}}}
    binary = bytearray()

    def accessor(values, kind, component=5126):
        while len(binary) % 4:
            binary.append(0)
        start = len(binary)
        components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[kind]
        fmt = 'I' if component == 5125 else 'f'
        for row in values:
            binary.extend(struct.pack('<' + fmt * components, *([row] if components == 1 else row)))
        view = len(document['bufferViews'])
        document['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(binary) - start})
        index = len(document['accessors'])
        document['accessors'].append({'bufferView': view, 'componentType': component, 'count': len(values), 'type': kind})
        return index

    groups = defaultdict(list)
    for row in rows:
        groups[row[0]].append(row)
    for region in sorted(groups):
        group = groups[region]
        positions = [point for row in group for point in row[1]]
        normals = [normal for row in group for normal in row[2]]
        material = len(document['materials'])
        document['materials'].append(copy.deepcopy(group[0][3]))
        primitive = {'attributes': {'POSITION': accessor(positions, 'VEC3'), 'NORMAL': accessor(normals, 'VEC3')},
                     'indices': accessor(list(range(len(positions))), 'SCALAR', 5125), 'material': material, 'mode': 4}
        document['meshes'][0]['primitives'].append(primitive)
    times = accessor([0, 1], 'SCALAR')
    translations = accessor([[0, 0, 0], [0, .5, 0]], 'VEC3')
    rotations = accessor([[0, 0, 0, 1], [0, 0, 0, 1]], 'VEC4')
    document['animations'] = [{'samplers': [{'input': times, 'output': translations, 'interpolation': 'LINEAR'},
                                           {'input': times, 'output': rotations, 'interpolation': 'LINEAR'}],
                               'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}},
                                            {'sampler': 1, 'target': {'node': 0, 'path': 'rotation'}}]}]
    document['buffers'][0]['byteLength'] = len(binary)
    return document, bytes(binary)


class RingLoftOracleTests(unittest.TestCase):
    def setUp(self):
        self.wanted = copy.deepcopy(GEOMETRIES['hollow-frustum'])
        self.rows = hand_loft(self.wanted)

    def reject(self, mutate, message=None):
        mutate(self.rows)
        context = self.assertRaisesRegex(AssertionError, message) if message else self.assertRaises(AssertionError)
        with context:
            check_geometry(Supplied(self.rows), 'shape', self.wanted)

    def test_hand_divided_hollow_frustum_matches_analytic_volume(self):
        result = check_geometry(Supplied(self.rows), 'shape', self.wanted)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['signed_volume_m3'], 21)
        self.assertEqual(result['cap_areas_m2'], [12, 3])
        self.assertEqual(result['intersections']['triangle_pairs'], 496)

    def test_solid_constant_frustum_chamfer_and_minimum_gap_controls(self):
        for name in ('constant-solid', 'solid-frustum', 'three-section-chamfer', 'minimum-station-gap', 'nonzero-start-station'):
            with self.subTest(name=name):
                wanted = GEOMETRIES[name]
                self.assertEqual(check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)['status'], 'passed')

    def test_authoritative_quarter_turn_is_a_rectangular_box(self):
        wanted = GEOMETRIES['authoritative-quarter-turn']
        report = check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)
        self.assertEqual(report['signed_volume_m3'], 4)
        self.assertEqual(report['surface_area_m2'], 16)

    def test_changed_concavity_uses_distinct_endpoint_cap_diagonals(self):
        wanted = GEOMETRIES['changing-concave-cap-diagonal']
        report = check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)
        self.assertEqual(report['signed_volume_m3'], 21.5)

    def test_reusing_lower_cap_on_changed_upper_domain_rejects(self):
        wanted = GEOMETRIES['changing-concave-cap-diagonal']
        rows = hand_loft(wanted, ([(0, 1, 2), (0, 2, 3)], [(0, 1, 2), (0, 2, 3)]))
        with self.assertRaises(AssertionError):
            check_geometry(Supplied(rows), 'shape', wanted)

    def test_known_rigid_local_placement_is_applied_once(self):
        wanted = GEOMETRIES['placed-hollow-frustum']
        self.assertEqual(check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)['status'], 'passed')

    def test_lower_station_materials_and_terminal_nonparticipation(self):
        for name in ('mixed-strip-materials', 'terminal-regions-no-strip'):
            with self.subTest(name=name):
                wanted = GEOMETRIES[name]
                self.assertEqual(check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)['status'], 'passed')

    def test_repaired_upper_hole_has_predetermined_volume(self):
        wanted = FROZEN['assembly']['repaired_first']
        self.assertEqual(check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)['signed_volume_m3'], wanted['volume_m3'])

    def test_missing_triangle_rejects(self):
        self.reject(lambda rows: rows.pop(), 'triangle count')

    def test_duplicated_cap_rejects_even_with_equal_triangle_count(self):
        self.reject(lambda rows: rows.__setitem__(10, copy.deepcopy(rows[8])), 'overlap|coverage')

    def test_cap_covering_hole_rejects(self):
        def change(rows):
            rows[8][1] = [(-1, -1, 3), (1, -1, 3), (.5, .5, 3)]
        self.reject(change, 'boundary|hole|domain')

    def test_reversed_strip_and_matching_normals_still_reject(self):
        def change(rows):
            row = rows[-1]
            row[1].reverse()
            row[2] = [tuple(-v for v in normal) for normal in row[2]]
        self.reject(change, 'fixed diagonal')

    def test_wrong_strip_material_cannot_hide_behind_correct_pbr(self):
        def change(rows):
            row = next(row for row in rows if row[0] == 'inner')
            row[0] = 'outer'
            row[3]['pbrMetallicRoughness']['baseColorFactor'] = self.wanted['palette']['outer']
        self.reject(change, 'lower outgoing edge')

    def test_wrong_cap_material_rejects(self):
        self.reject(lambda rows: rows[0].__setitem__(0, 'top'), 'cap region')

    def test_pbr_color_metallic_and_roughness_must_match(self):
        for field, value in [('baseColorFactor', [0, 0, 0, 1]), ('metallicFactor', .8), ('roughnessFactor', .2)]:
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                rows[0][3]['pbrMetallicRoughness'][field] = value
                with self.assertRaises(AssertionError):
                    check_geometry(Supplied(rows), 'shape', self.wanted)

    def test_double_sided_material_cannot_mask_orientation(self):
        self.reject(lambda rows: rows[0][3].update(doubleSided=True), 'double-sided')

    def test_tilted_unit_normal_rejects(self):
        self.reject(lambda rows: rows[0].__setitem__(2, [(0, .6, -.8)] * 3))

    def test_nonfinite_normal_rejects(self):
        self.reject(lambda rows: rows[0].__setitem__(2, [(math.nan, 0, -1)] * 3))

    def test_exact_thin_face_accepts_correct_normal_despite_rounded_zero_cross(self):
        epsilon = 2.0 ** -80
        points = [(epsilon, 0, 0), (1, 3, 0), (15, 45, 0)]
        # Ordinary subtraction erases epsilon, but the exact cross is -42*epsilon
        self.assertEqual((1 - epsilon) * 45 - 3 * (15 - epsilon), 0)
        length = _check_face_normals(points, [(0, 0, -1)] * 3, source_points=points)
        self.assertEqual(length, 42 * epsilon)

    def test_exact_thin_face_rejects_inward_supplied_normal(self):
        points = [(2.0 ** -80, 0, 0), (1, 3, 0), (15, 45, 0)]
        with self.assertRaisesRegex(AssertionError, 'exact outward'):
            _check_face_normals(points, [(0, 0, 1)] * 3, source_points=points)

    def test_exact_source_normal_survives_rigid_half_turn(self):
        points = [(2.0 ** -80, 0, 0), (1, 3, 0), (15, 45, 0)]
        rotate = lambda point: (point[0], -point[1], -point[2])
        length = _check_face_normals(list(map(rotate, points)), [(0, 0, 1)] * 3,
                                     source_points=points, rotate=rotate)
        self.assertEqual(length, 42 * 2.0 ** -80)

    def test_exact_volume_uses_delivered_positions_before_inverse_translation(self):
        epsilon = f32(2.0 ** -80)
        o, x, y, z = (0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, epsilon)
        # An outward tetrahedron has volume epsilon / 6. Subtracting a unit
        # offset in floating point would first flatten all four z coordinates.
        triangles = [(o, y, x), (o, x, z), (o, z, y), (x, y, z)]
        self.assertEqual(_exact_signed_volume6(triangles), Fraction(1, 2 ** 80))
        rounded_local = [[(p[0], p[1], p[2] - 1.0) for p in face] for face in triangles]
        self.assertEqual(_exact_signed_volume6(rounded_local), 0)

    def test_small_duplicate_corner_change_rejects_exact_position_identity(self):
        def change(rows):
            x, y, z = rows[0][1][0]
            rows[0][1][0] = (x + 1e-7, y, z)
        self.reject(change, 'source-quantized')

    def test_wholly_unauthored_corner_rejects(self):
        self.reject(lambda rows: rows[0][1].__setitem__(0, (99, 99, 99)), 'source-quantized')

    def test_precision_collapsed_hole_rejects_before_identity_matching(self):
        wanted = GEOMETRIES['binary32-hole-collapse']
        with self.assertRaisesRegex(AssertionError, 'collapse'):
            check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)

    def test_incorrect_measurement_expectation_rejects(self):
        for field in ('volume_m3', 'surface_area_m2'):
            wanted = copy.deepcopy(self.wanted)
            wanted[field] += 1
            with self.subTest(field=field), self.assertRaises(AssertionError):
                check_geometry(Supplied(self.rows), 'shape', wanted)

    def test_complete_binary_artifact_and_recorded_pose_pass(self):
        document, binary = hand_document(self.rows)
        nodes = {'shape': {'geometry': self.wanted, 'origin': [0, 0, 0], 'velocity': [0, .5, 0]}}
        result = check_glb(pack_document(document, binary), nodes, 'sha256:fixture')
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['observations']), 5)

    def test_recorded_motion_must_match_expected_origin_and_speed(self):
        document, binary = hand_document(self.rows)
        nodes = {'shape': {'geometry': self.wanted, 'origin': [0, 0, 0], 'velocity': [0, 1, 0]}}
        with self.assertRaises(AssertionError):
            check_glb(pack_document(document, binary), nodes)

    def test_program_revision_must_match(self):
        document, binary = hand_document(self.rows)
        with self.assertRaises(AssertionError):
            check_glb(pack_document(document, binary), {'shape': {'geometry': self.wanted, 'origin': [0, 0, 0], 'velocity': [0, .5, 0]}}, 'sha256:wrong')

    def test_hidden_carrier_outside_selected_scene_rejects(self):
        document, binary = hand_document(self.rows)
        document['scenes'][0]['nodes'] = []
        with self.assertRaisesRegex(AssertionError, 'active scene'):
            check_glb(pack_document(document, binary), {'shape': {'geometry': self.wanted, 'origin': [0, 0, 0], 'velocity': [0, .5, 0]}})

    def test_geometry_free_parent_cannot_carry_hidden_mesh(self):
        document, binary = hand_document(self.rows)
        with self.assertRaisesRegex(AssertionError, 'geometry-free'):
            check_glb(pack_document(document, binary), {'shape': {'geometry': None, 'origin': [0, 0, 0], 'velocity': [0, .5, 0]}})

    def test_decoder_requires_explicit_dot10_binding(self):
        document, binary = hand_document(self.rows)
        document['extras']['ontokin']['target_contract'] = 'ontokin.glb/0.9'
        with self.assertRaises(AssertionError):
            Decoded(pack_document(document, binary))

    def test_decoder_rejects_nonrigid_scale_matrix_and_child_hierarchy(self):
        for change in ({'scale': [2, 2, 2]}, {'matrix': [1] * 16}, {'children': [0]}):
            document, binary = hand_document(self.rows)
            document['nodes'][0].update(change)
            with self.subTest(change=change), self.assertRaises(AssertionError):
                Decoded(pack_document(document, binary))

    def test_decoder_rejects_scale_animation_and_duplicate_target(self):
        for duplicate in (False, True):
            document, binary = hand_document(self.rows)
            if duplicate:
                document['animations'][0]['channels'].append(copy.deepcopy(document['animations'][0]['channels'][0]))
            else:
                document['animations'][0]['channels'][0]['target']['path'] = 'scale'
            with self.subTest(duplicate=duplicate), self.assertRaises(AssertionError):
                Decoded(pack_document(document, binary))

    def test_accessor_cannot_read_past_its_view_into_other_valid_bytes(self):
        document, binary = hand_document(self.rows)
        document['bufferViews'][0]['byteLength'] -= 4
        decoded = Decoded(pack_document(document, binary))
        with self.assertRaises(AssertionError):
            decoded.triangles('shape')


class RingLoftIntersectionOracleTests(unittest.TestCase):
    def check(self, first, second, ids=((0, 1, 2), (3, 4, 5))):
        return check_surface_intersections([first, second], ids)

    def test_nonshared_cross_plane_intersection_rejects(self):
        with self.assertRaisesRegex(AssertionError, 'intersection'):
            self.check([(0, 0, 0), (2, 0, 0), (0, 2, 0)], [(-1, 1, -1), (3, 1, -1), (1, 1, 1)])

    def test_nonshared_touch_at_a_single_point_rejects(self):
        with self.assertRaisesRegex(AssertionError, 'intersection'):
            self.check([(0, 0, 0), (2, 0, 0), (0, 2, 0)], [(0, 0, 0), (-1, 0, 0), (0, -1, 0)])

    def test_shared_vertex_only_contact_passes(self):
        result = self.check([(0, 0, 0), (2, 0, 0), (0, 2, 0)], [(0, 0, 0), (-1, 0, 0), (0, -1, 0)], ((0, 1, 2), (0, 3, 4)))
        self.assertEqual(result['status'], 'passed')

    def test_coplanar_shared_edge_passes(self):
        self.check([(0, 0, 0), (2, 0, 0), (0, 2, 0)], [(2, 0, 0), (2, 2, 0), (0, 2, 0)], ((0, 1, 2), (1, 3, 2)))

    def test_noncoplanar_shared_edge_passes(self):
        self.check([(0, 0, 0), (2, 0, 0), (0, 2, 0)], [(0, 0, 0), (2, 0, 0), (0, 0, 2)], ((0, 1, 2), (0, 1, 3)))

    def test_coplanar_containment_without_crossing_edges_rejects(self):
        with self.assertRaisesRegex(AssertionError, 'intersection'):
            self.check([(0, 0, 0), (4, 0, 0), (0, 4, 0)], [(1, 1, 0), (2, 1, 0), (1, 2, 0)])

    def test_shared_edge_does_not_permit_folded_overlap(self):
        with self.assertRaisesRegex(AssertionError, 'intersection'):
            self.check([(0, 0, 0), (4, 0, 0), (0, 4, 0)], [(0, 0, 0), (4, 0, 0), (1, 1, 0)], ((0, 1, 2), (0, 1, 3)))

    def test_parallel_separated_triangles_pass_without_epsilon(self):
        self.check([(0, 0, 0), (2, 0, 0), (0, 2, 0)], [(0, 0, 1e-12), (2, 0, 1e-12), (0, 2, 1e-12)])

    def test_degenerate_triangle_rejects(self):
        with self.assertRaisesRegex(AssertionError, 'nonzero exact area'):
            self.check([(0, 0, 0), (1, 0, 0), (2, 0, 0)], [(0, 1, 0), (1, 1, 0), (0, 2, 0)])

    def test_duplicate_faces_reject(self):
        with self.assertRaisesRegex(AssertionError, 'Duplicate'):
            self.check([(0, 0, 0), (2, 0, 0), (0, 2, 0)], [(2, 0, 0), (0, 2, 0), (0, 0, 0)], ((0, 1, 2), (1, 2, 0)))


if __name__ == '__main__':
    unittest.main()
