"""Hand-authored meshes and hostile supplied-byte controls for C078.

No product module is imported. Exact section positions come from independently
frozen witnesses, cap partitions are written by hand, and each hostile case
alters an actual mesh, accessor, scene or animation input.
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

from tools.framed_loft_oracles import (
    Decoded, check_geometry, check_glb, section_matrix, section_point,
    placement_matrix, place_point, source_facts, _sign_cap,
)
from tools.ring_loft_oracles import check_surface_intersections, _check_face_normals

ROOT = Path(__file__).resolve().parents[1]
FROZEN = json.loads((ROOT / 'examples/framed-polygon-lofts/expected.json').read_text())
GEOMETRIES = {case['id']: case['geometry'] for case in FROZEN['cases'] if 'geometry' in case}


class Supplied:
    def __init__(self, rows):
        self.rows = rows

    def triangles(self, path):
        assert path == 'shape'
        return self.rows


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def hand_loft(wanted):
    """Write explicit caps and strips around frozen independent source points."""
    points = {tuple(item['identity']): tuple(item['position_m']) for item in wanted['source_positions']}
    sections = sorted(wanted['sections'], key=lambda section: section['order'])
    levels, ring_rows = [], []
    for section in sections:
        rings = sorted(section['rings'], key=lambda ring: ring['order'])
        rows = [sorted(ring['vertices'], key=lambda vertex: vertex['order']) for ring in rings]
        levels.append([points[section['key'], ring['key'], vertex['key']]
                       for ring, vertices in zip(rings, rows) for vertex in vertices])
        ring_rows.append(rows)
    n = len(levels[0])
    if n == 4:
        cap = [(0, 1, 2), (0, 2, 3)]
    elif n == 8 and wanted['hole_count'] == 1:
        cap = [(0, 1, 6), (0, 6, 7), (1, 2, 5), (1, 5, 6),
               (2, 3, 4), (2, 4, 5), (3, 0, 7), (3, 7, 4)]
    else:
        raise AssertionError('Hand controls use a quadrilateral or square annulus')
    offset = wanted.get('local_position_m', [0, 0, 0])
    rotation = wanted.get('local_orientation_wxyz', [1, 0, 0, 0])
    assert rotation in ([1, 0, 0, 0], [0, 1, 0, 0])

    def rotate(point):
        return tuple(point) if rotation[0] == 1 else (point[0], -point[1], -point[2])

    rows = []

    def emit(region, positions):
        a, b, c = [tuple(Fraction(value) for value in p) for p in positions]
        u, v = tuple(y-x for x, y in zip(a, b)), tuple(y-x for x, y in zip(a, c))
        face = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        length = math.hypot(*(float(value) for value in face))
        normal = tuple(f32(float(value)/length) for value in rotate(face))
        delivered = [tuple(f32(value+shift) for value, shift in zip(rotate(point), offset)) for point in positions]
        material = {'pbrMetallicRoughness': {
            'baseColorFactor': copy.deepcopy(wanted['palette'][region]),
            'metallicFactor': wanted['metallic'], 'roughnessFactor': wanted['roughness']},
            'extras': {'ontokin': {'source_region_key': region}}}
        rows.append([region, delivered, [normal]*3, material])

    for triangle in cap:
        emit('bottom', [levels[0][i] for i in reversed(triangle)])
    for triangle in cap:
        emit('top', [levels[-1][i] for i in triangle])
    for level in range(len(sections)-1):
        start = 0
        for vertices in ring_rows[level]:
            count = len(vertices)
            for i, vertex in enumerate(vertices):
                a, b = start+i, start+(i+1)%count
                emit(vertex['region'], [levels[level][a], levels[level][b], levels[level+1][a]])
                emit(vertex['region'], [levels[level][b], levels[level+1][b], levels[level+1][a]])
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
                'extras': {'ontokin': {'target_contract': 'ontokin.glb/0.11', 'profile': 'framed-polygon-loft-0.1',
                                       'schema_version': '0.11', 'program': {'revision': 'sha256:fixture'}}}}
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


class FramedLoftOracleTests(unittest.TestCase):
    def setUp(self):
        self.wanted = copy.deepcopy(GEOMETRIES['hollow-elbow'])
        self.rows = hand_loft(self.wanted)

    def reject(self, mutation, message=None):
        mutation(self.rows)
        context = self.assertRaisesRegex(AssertionError, message) if message else self.assertRaises(AssertionError)
        with context:
            check_geometry(Supplied(self.rows), 'shape', self.wanted)

    def test_hand_elbow_and_handle_match_independent_analytic_controls(self):
        for name, volume, area in (
                ('bent-solid', 16, 24+16*math.sqrt(2)),
                ('hollow-elbow', 12, 30+24*math.sqrt(2)),
                ('solid-handle', 32, 40+32*math.sqrt(2)),
                ('hollow-handle', 24, 54+48*math.sqrt(2))):
            with self.subTest(name=name):
                wanted = GEOMETRIES[name]
                result = check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)
                self.assertEqual(result['signed_volume_m3'], volume)
                self.assertAlmostEqual(result['surface_area_m2'], area)

    def test_identity_cyclic_rotation_and_equal_component_y90(self):
        for name in ('identity-solid', 'identity-hollow', 'cyclic-rigid-rotation',
                     'sign-equivalent-rotation', 'equal-component-y90',
                     'authoritative-frame-quarter-turn', 'negative-origins'):
            with self.subTest(name=name):
                wanted = GEOMETRIES[name]
                self.assertEqual(check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)['status'], 'passed')

    def test_known_outer_placement_is_applied_once(self):
        wanted = GEOMETRIES['placed-hollow-handle']
        result = check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)
        self.assertEqual(result['signed_volume_m3'], 24)

    def test_repair_preserves_predetermined_volume(self):
        wanted = GEOMETRIES['repaired-hollow-elbow']
        result = check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)
        self.assertEqual(result['signed_volume_m3'], 13.5)

    def test_minimum_diagonal_and_near_half_turn_progression(self):
        for name in ('minimum-origin-separation', 'diagonal-origin-separation', 'near-half-turn-admitted'):
            with self.subTest(name=name):
                wanted = GEOMETRIES[name]
                self.assertEqual(check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)['status'], 'passed')

    def test_rounded_nonplanar_caps_are_checked_in_three_dimensions(self):
        wanted = GEOMETRIES['rounded-nonplanar-caps']
        section = wanted['sections'][0]['key']
        points = [tuple(Fraction(value) for value in item['position_m'])
                  for item in wanted['source_positions'] if item['identity'][0] == section]
        a, b, c, d = points
        u, v, w = [[p[i]-a[i] for i in range(3)] for p in (b, c, d)]
        determinant = (u[0]*(v[1]*w[2]-v[2]*w[1]) - u[1]*(v[0]*w[2]-v[2]*w[0])
                       + u[2]*(v[0]*w[1]-v[1]*w[0]))
        self.assertNotEqual(determinant, 0)
        result = check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['cap_domains']), 2)

    def test_all_frozen_source_bits_and_progression_are_independently_recomputed(self):
        for case in FROZEN['cases']:
            if 'geometry' in case:
                with self.subTest(name=case['id']):
                    sections, points, axes, progression = source_facts(case['geometry'])
                    self.assertEqual(len(points), case['geometry']['authored_vertex_count'])
                    self.assertEqual(len(axes), len(sections))
                    self.assertEqual(len(progression), len(sections)-1)

    def test_single_round_transform_matches_frozen_nonplanar_witnesses(self):
        wanted = GEOMETRIES['rounded-nonplanar-caps']
        witnesses = {tuple(item['identity']): item for item in wanted['source_positions']}
        for section in wanted['sections']:
            for ring in section['rings']:
                for vertex in ring['vertices']:
                    point = section_point(section['origin_m'], section['orientation_wxyz'], vertex['point_m'])
                    identity = (section['key'], ring['key'], vertex['key'])
                    self.assertEqual([value.hex() for value in point], witnesses[identity]['position_hex'])

    def test_section_action_and_inherited_placement_keep_distinct_rules(self):
        q = [.8, .36, .48, 0]
        self.assertNotEqual(section_matrix(q), placement_matrix(q))
        self.assertEqual(section_point([0, 0, 0], [0.5, 0.5, 0.5, 0.5], [2, 3]), (0, 2, 3))
        self.assertEqual(place_point([2, 3, 0], [0.5, 0.5, 0.5, 0.5], [1, -1, 2]), (1, 1, 5))

    def test_quaternion_sign_invariance_does_not_renormalize_stored_leaves(self):
        q = [.8, .36, .48, 0]
        self.assertEqual(section_matrix(q), section_matrix([-value for value in q]))
        q = [0.7071067811865476, 0, 0.7071067811865476, 0]
        self.assertEqual(section_point([4, 0, 4], q, [1, 2]), (4, 2, 3))

    def test_zero_nonunit_nonfinite_or_wrong_shape_rotation_rejects(self):
        for q in ([0, 0, 0, 0], [2, 0, 0, 0], [1, 0, float('nan'), 0], [1, 0, 0], [True, 0, 0, 0]):
            with self.subTest(q=q), self.assertRaises(AssertionError):
                section_matrix(q)

    def test_mutated_frozen_source_position_cannot_be_trusted_as_oracle_output(self):
        self.wanted['source_positions'][0]['position_m'][0] += .01
        with self.assertRaisesRegex(AssertionError, 'Frozen source position'):
            check_geometry(Supplied(self.rows), 'shape', self.wanted)

    def test_mutated_frozen_position_bits_are_rejected(self):
        self.wanted['source_positions'][0]['position_hex'][0] = '0x0.0p+0'
        with self.assertRaisesRegex(AssertionError, 'Frozen source bits'):
            check_geometry(Supplied(self.rows), 'shape', self.wanted)

    def test_mutated_progression_witness_is_rejected(self):
        self.wanted['progression'][0]['previous_normal_dot_exact'] = ['99', '1']
        with self.assertRaisesRegex(AssertionError, 'progression witnesses'):
            check_geometry(Supplied(self.rows), 'shape', self.wanted)

    def test_source_frame_progression_guard_rejects_sideways_connection(self):
        wanted = copy.deepcopy(GEOMETRIES['identity-solid'])
        wanted.pop('source_positions')
        wanted.pop('progression')
        wanted['sections'][1]['origin_m'] = [4, 0, 0]
        with self.assertRaisesRegex(AssertionError, 'forward progression'):
            source_facts(wanted)

    def test_source_frame_separation_guard_has_no_epsilon(self):
        wanted = copy.deepcopy(GEOMETRIES['identity-solid'])
        wanted.pop('source_positions')
        wanted.pop('progression')
        wanted['sections'][1]['origin_m'] = [0, 0, math.nextafter(.001, 0)]
        with self.assertRaisesRegex(AssertionError, 'too close'):
            source_facts(wanted)

    def test_cap_orientation_uses_rotated_frame_axis(self):
        points = [(4, -1, 5), (4, 1, 5), (4, 1, 3)]
        _sign_cap(points, (Fraction(-1), Fraction(0), Fraction(0)), 1, 'Delivered')
        with self.assertRaisesRegex(AssertionError, 'outward frame axis'):
            _sign_cap(points, (Fraction(1), Fraction(0), Fraction(0)), 1, 'Delivered')

    def test_exact_cap_sign_rejects_zero_and_reversed_faces(self):
        for points in ([(0, 0, 0), (1, 0, 0), (1, 1, 0)], [(0, 0, 0), (1, 0, 0), (2, 0, 0)]):
            with self.assertRaises(AssertionError):
                _sign_cap(points, (Fraction(0), Fraction(0), Fraction(1)), -1, 'Source')

    def test_missing_triangle_rejects(self):
        self.reject(lambda rows: rows.pop(), 'triangle count')

    def test_duplicate_cap_with_equal_triangle_count_rejects(self):
        self.reject(lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])), 'overlap|coverage|repeat')

    def test_cap_covering_a_hole_rejects(self):
        wanted = GEOMETRIES['identity-hollow']
        rows = hand_loft(wanted)
        rows[0][1] = [(1, 1, 0), (1, -1, 0), (-1, -1, 0)]
        with self.assertRaisesRegex(AssertionError, 'hole|boundary|domain'):
            check_geometry(Supplied(rows), 'shape', wanted)

    def test_reversed_cap_with_matching_normals_still_rejects(self):
        def mutation(rows):
            rows[0][1].reverse()
            rows[0][2] = [tuple(-value for value in normal) for normal in rows[0][2]]
        self.reject(mutation, 'outward frame axis')

    def test_wrong_strip_diagonal_rejects_even_for_same_planar_quad(self):
        wanted = GEOMETRIES['identity-solid']
        rows = hand_loft(wanted)
        a0, b0, a1 = rows[4][1]
        _, b1, _ = rows[5][1]
        rows[4][1], rows[5][1] = [a0, b0, b1], [a0, b1, a1]
        with self.assertRaisesRegex(AssertionError, 'fixed diagonal'):
            check_geometry(Supplied(rows), 'shape', wanted)

    def test_reversed_strip_with_matching_normals_rejects(self):
        def mutation(rows):
            rows[-1][1].reverse()
            rows[-1][2] = [tuple(-value for value in normal) for normal in rows[-1][2]]
        self.reject(mutation, 'fixed diagonal')

    def test_wrong_strip_material_with_matching_color_rejects(self):
        def mutation(rows):
            rows[-1][0] = 'outer'
            rows[-1][3] = copy.deepcopy(next(row[3] for row in rows if row[0] == 'outer'))
        self.reject(mutation, 'outgoing edge')

    def test_wrong_cap_region_rejects(self):
        self.reject(lambda rows: rows[0].__setitem__(0, 'top'), 'cap region')

    def test_palette_values_are_checked(self):
        for field, value in (('baseColorFactor', [1, 1, 1, 1]), ('metallicFactor', .8), ('roughnessFactor', .2)):
            with self.subTest(field=field):
                rows = copy.deepcopy(self.rows)
                rows[0][3]['pbrMetallicRoughness'][field] = value
                with self.assertRaises(AssertionError):
                    check_geometry(Supplied(rows), 'shape', self.wanted)

    def test_double_sided_material_rejects(self):
        self.reject(lambda rows: rows[0][3].__setitem__('doubleSided', True), 'double-sided')

    def test_tilted_unit_normal_rejects(self):
        self.reject(lambda rows: rows[0].__setitem__(2, [(0, .6, -.8)]*3))

    def test_nonfinite_normal_rejects(self):
        self.reject(lambda rows: rows[0].__setitem__(2, [(0, 0, float('nan'))]*3))

    def test_flat_corner_normals_must_match(self):
        def mutation(rows):
            rows[0][2] = [rows[0][2][0], (1e-7, 0, -1), rows[0][2][2]]
        self.reject(mutation, 'one normal')

    def test_small_unauthored_corner_shift_rejects_exact_identity(self):
        def mutation(rows):
            point = list(rows[0][1][0])
            point[0] += 1e-8
            rows[0][1][0] = tuple(point)
        self.reject(mutation, 'source-quantized')

    def test_binary32_collapse_controls_cannot_pass_geometry(self):
        for name in ('binary32-hole-collapse', 'binary32-rotated-boundary-clearance', 'binary32-placed-clearance'):
            with self.subTest(name=name), self.assertRaises(AssertionError):
                wanted = GEOMETRIES[name]
                check_geometry(Supplied(hand_loft(wanted)), 'shape', wanted)

    def test_wrong_area_volume_or_bounds_expectation_rejects(self):
        for field in ('surface_area_m2', 'volume_m3', 'bounds_m'):
            with self.subTest(field=field):
                wanted = copy.deepcopy(self.wanted)
                if field == 'bounds_m':
                    wanted[field][0][0] -= 1
                else:
                    wanted[field] += 1
                with self.assertRaises(AssertionError):
                    check_geometry(Supplied(self.rows), 'shape', wanted)

    def artifact(self):
        document, binary = hand_document(self.rows)
        nodes = {'shape': {'geometry': self.wanted, 'origin': [0, 0, 0], 'velocity': [0, .5, 0]}}
        return document, binary, nodes

    def test_actual_hand_encoded_glb_and_motion_pass(self):
        document, binary, nodes = self.artifact()
        result = check_glb(pack_document(document, binary), nodes, 'sha256:fixture')
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['observations']), 5)

    def test_actual_motion_must_match_frozen_velocity(self):
        document, binary, nodes = self.artifact()
        nodes['shape']['velocity'][1] = .75
        with self.assertRaises(AssertionError):
            check_glb(pack_document(document, binary), nodes)

    def test_program_revision_must_match(self):
        document, binary, nodes = self.artifact()
        with self.assertRaises(AssertionError):
            check_glb(pack_document(document, binary), nodes, 'sha256:other')

    def test_active_scene_cannot_hide_a_carrier(self):
        document, binary, nodes = self.artifact()
        document['scenes'][0]['nodes'] = []
        with self.assertRaisesRegex(AssertionError, 'active scene'):
            check_glb(pack_document(document, binary), nodes)

    def test_geometry_free_carrier_cannot_hide_a_mesh(self):
        document, binary, nodes = self.artifact()
        nodes['shape']['geometry'] = None
        with self.assertRaisesRegex(AssertionError, 'geometry-free'):
            check_glb(pack_document(document, binary), nodes)

    def test_wrong_binding_rejects(self):
        for field, value in (('target_contract', 'ontokin.glb/0.10'), ('profile', 'polygon-loft-0.1'), ('schema_version', '0.10')):
            with self.subTest(field=field):
                document, binary, nodes = self.artifact()
                document['extras']['ontokin'][field] = value
                with self.assertRaises(AssertionError):
                    Decoded(pack_document(document, binary))

    def test_nonrigid_node_transforms_or_hierarchy_reject(self):
        for field, value in (('scale', [1, 2, 1]), ('matrix', [1]*16), ('children', [0])):
            with self.subTest(field=field):
                document, binary, nodes = self.artifact()
                document['nodes'][0][field] = value
                with self.assertRaises(AssertionError):
                    Decoded(pack_document(document, binary))

    def test_duplicate_motion_target_or_scale_channel_rejects(self):
        for duplicate in (True, False):
            document, binary, nodes = self.artifact()
            channel = copy.deepcopy(document['animations'][0]['channels'][0])
            if duplicate:
                document['animations'][0]['channels'].append(channel)
            else:
                channel['target']['path'] = 'scale'
                document['animations'][0]['channels'][0] = channel
            with self.assertRaises(AssertionError):
                check_glb(pack_document(document, binary), nodes)

    def test_missing_motion_channel_rejects(self):
        document, binary, nodes = self.artifact()
        document['animations'][0]['channels'].pop()
        with self.assertRaisesRegex(AssertionError, 'both rigid motion channels'):
            check_glb(pack_document(document, binary), nodes)

    def test_repeated_clock_rejects(self):
        document, binary, nodes = self.artifact()
        index = document['animations'][0]['samplers'][0]['input']
        accessor = document['accessors'][index]
        view = document['bufferViews'][accessor['bufferView']]
        altered = bytearray(binary)
        struct.pack_into('<ff', altered, view['byteOffset'], 0, 0)
        with self.assertRaisesRegex(AssertionError, 'clocks'):
            check_glb(pack_document(document, altered), nodes)

    def test_accessor_must_stay_inside_its_own_view(self):
        document, binary, nodes = self.artifact()
        index = document['meshes'][0]['primitives'][0]['attributes']['POSITION']
        accessor = document['accessors'][index]
        document['bufferViews'][accessor['bufferView']]['byteLength'] -= 4
        with self.assertRaises(AssertionError):
            check_glb(pack_document(document, binary), nodes)

    def test_flat_corner_indices_cannot_be_welded(self):
        document, binary, nodes = self.artifact()
        primitive = document['meshes'][0]['primitives'][0]
        accessor = document['accessors'][primitive['indices']]
        view = document['bufferViews'][accessor['bufferView']]
        altered = bytearray(binary)
        struct.pack_into('<I', altered, view['byteOffset']+4, 0)
        with self.assertRaisesRegex(AssertionError, 'flat corner'):
            check_glb(pack_document(document, altered), nodes)

    def test_material_primitive_order_is_not_arbitrary(self):
        document, binary, nodes = self.artifact()
        document['meshes'][0]['primitives'].reverse()
        with self.assertRaisesRegex(AssertionError, 'unique and sorted'):
            check_glb(pack_document(document, binary), nodes)

    def test_nonadjacent_crossing_and_point_contact_reject(self):
        first = [(0, 0, 0), (2, 0, 0), (0, 2, 0)]
        for second in ([(.5, .5, -1), (.5, .5, 1), (1.5, .5, 0)],
                       [(0, 0, 0), (-1, 0, 1), (0, -1, 1)]):
            with self.assertRaises(AssertionError):
                check_surface_intersections([first, second], [('a', 'b', 'c'), ('d', 'e', 'f')])

    def test_coplanar_containment_and_folded_overlap_reject(self):
        first = [(0, 0, 0), (4, 0, 0), (0, 4, 0)]
        for second, ids in (([(.5, .5, 0), (1, .5, 0), (.5, 1, 0)], ('d', 'e', 'f')),
                            ([(4, 0, 0), (0, 0, 0), (1, 1, 0)], ('b', 'a', 'd'))):
            with self.assertRaises(AssertionError):
                check_surface_intersections([first, second], [('a', 'b', 'c'), ids])

    def test_exact_shared_edge_contact_passes_without_epsilon(self):
        first = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        second = [(1, 0, 0), (0, 0, 0), (0, 0, 1)]
        result = check_surface_intersections([first, second], [('a', 'b', 'c'), ('b', 'a', 'd')])
        self.assertEqual(result['triangle_pairs'], 1)


if __name__ == '__main__':
    unittest.main()

