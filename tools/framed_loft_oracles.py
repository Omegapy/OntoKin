"""Independent supplied-byte checks for authored framed polygon lofts.

This checker imports no OntoKin product code. Section transforms are evaluated
from the frozen binary64 leaves using exact rational quaternion action. Outer
placement retains its independently reproduced older arithmetic. Authored XY
cap domains and actual three-dimensional surfaces are checked separately.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import json
import math
import struct

from tools.extrusion_oracles import Decoded as _AccessorReader
from tools.extrusion_oracles import close, cross, dot, sub
from tools.holes_oracles import _cap_domain, _overlap_area2, _turn
from tools.ring_loft_oracles import (
    _cyclic, _face_measure, _check_face_normals, _exact_signed_volume6,
    check_surface_intersections,
)


class Decoded(_AccessorReader):
    """Decode a rigid, inline GLB with the explicit C078 binding."""

    def __init__(self, data):
        assert len(data) >= 28
        assert struct.unpack_from('<III', data) == (0x46546c67, 2, len(data))
        length, kind = struct.unpack_from('<II', data, 12)
        assert kind == 0x4e4f534a and length % 4 == 0 and 20 + length + 8 <= len(data)
        self.document = json.loads(data[20:20 + length])
        start = 20 + length
        size, kind = struct.unpack_from('<II', data, start)
        assert kind == 0x004e4942 and size % 4 == 0 and start + 8 + size == len(data)
        self.binary = data[start + 8:]
        buffers = self.document['buffers']
        assert len(buffers) == 1 and buffers[0].get('uri') is None
        declared = buffers[0]['byteLength']
        assert type(declared) is int and 0 <= size - declared <= 3
        meta = self.document['extras']['ontokin']
        assert meta['target_contract'] == 'ontokin.glb/0.11'
        assert meta['profile'] == 'framed-polygon-loft-0.1'
        assert meta['schema_version'] == '0.11'
        for node in self.document.get('nodes', []):
            scale = node.get('scale', [1, 1, 1])
            assert len(scale) == 3 and all(type(v) in (int, float) for v in scale)
            assert scale == [1, 1, 1], 'Rigid carriers require identity scale'
            assert 'matrix' not in node, 'Recorded carriers use explicit rigid transforms'
            assert not node.get('children'), 'Carrier world poses cannot be inherited twice'
        for animation in self.document.get('animations', []):
            targets = set()
            for channel in animation['channels']:
                target = channel['target']
                assert target['path'] in ('translation', 'rotation'), 'Rigid motion cannot animate scale or weights'
                identity = (target['node'], target['path'])
                assert identity not in targets, 'An animation cannot duplicate a target path'
                targets.add(identity)

    def accessor(self, index):
        accessors, views = self.document['accessors'], self.document['bufferViews']
        assert type(index) is int and 0 <= index < len(accessors)
        item = accessors[index]
        assert 'sparse' not in item and not item.get('normalized', False)
        view_index = item['bufferView']
        assert type(view_index) is int and 0 <= view_index < len(views)
        view = views[view_index]
        assert view.get('buffer', 0) == 0
        fmt, width = {5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}[item['componentType']]
        components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[item['type']]
        count = item['count']
        view_start, view_size = view.get('byteOffset', 0), view['byteLength']
        offset = item.get('byteOffset', 0)
        stride = view.get('byteStride', width * components)
        assert all(type(v) is int and v >= 0 for v in (count, view_start, view_size, offset, stride))
        assert count > 0 and stride >= width * components and stride % width == 0
        assert view_start + view_size <= self.document['buffers'][0]['byteLength']
        assert offset + (count - 1) * stride + width * components <= view_size
        assert (view_start + offset) % width == 0
        rows = [struct.unpack_from('<' + fmt * components, self.binary, view_start + offset + i * stride)
                for i in range(count)]
        return [row[0] for row in rows] if components == 1 else rows

    def triangles(self, path):
        node = self.document['nodes'][self.objects()[path]]
        if 'mesh' not in node:
            return []
        mesh_index = node['mesh']
        assert type(mesh_index) is int and 0 <= mesh_index < len(self.document['meshes'])
        result = []
        position_uses, normal_uses = Counter(), Counter()
        position_sizes, normal_sizes, regions = {}, {}, []
        for primitive in self.document['meshes'][mesh_index]['primitives']:
            assert primitive.get('mode', 4) == 4
            attributes = primitive['attributes']
            p_index, n_index, i_index = attributes['POSITION'], attributes['NORMAL'], primitive['indices']
            for index in (p_index, n_index):
                item = self.document['accessors'][index]
                assert item['componentType'] == 5126 and item['type'] == 'VEC3'
            item = self.document['accessors'][i_index]
            assert item['componentType'] in (5123, 5125) and item['type'] == 'SCALAR'
            positions, normals, indices = self.accessor(p_index), self.accessor(n_index), self.accessor(i_index)
            assert len(positions) == len(normals) and len(indices) % 3 == 0
            assert all(type(i) is int and 0 <= i < len(positions) for i in indices)
            position_sizes[p_index], normal_sizes[n_index] = len(positions), len(normals)
            position_uses.update((p_index, i) for i in indices)
            normal_uses.update((n_index, i) for i in indices)
            material_index = primitive['material']
            assert type(material_index) is int and 0 <= material_index < len(self.document['materials'])
            material = self.document['materials'][material_index]
            region = material['extras']['ontokin']['source_region_key']
            regions.append(region)
            for start in range(0, len(indices), 3):
                ids = indices[start:start + 3]
                result.append((region, [positions[i] for i in ids], [normals[i] for i in ids], material))
        assert regions == sorted(set(regions)), 'Used material primitives must be unique and sorted'
        for uses, sizes in ((position_uses, position_sizes), (normal_uses, normal_sizes)):
            assert set(uses) == {(index, i) for index, size in sizes.items() for i in range(size)}, 'A flat corner accessor cannot contain unused corners'
            assert all(count == 1 for count in uses.values()), 'Each flat corner index must occur once'
        return result


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _binary64(value):
    result = float(value)
    assert math.isfinite(result), 'A transformed component must be finite'
    return 0.0 if result == 0 else result


def _native(values, count):
    assert isinstance(values, (list, tuple)) and len(values) == count
    assert all(type(value) in (int, float) and math.isfinite(value) for value in values)
    return tuple(Fraction(float(value)) for value in values)


def _matrix_vector(matrix, values):
    return tuple(sum((a * b for a, b in zip(row, values)), Fraction(0)) for row in matrix)


def section_matrix(quaternion):
    """A proper exact rotation from stored leaves, with no renormalization."""
    w, x, y, z = _native(quaternion, 4)
    denominator = w*w + x*x + y*y + z*z
    tolerance = Fraction(1e-12)
    assert (1 - tolerance)**2 <= denominator <= (1 + tolerance)**2, 'Section quaternion is outside its unit envelope'
    rows = ((w*w+x*x-y*y-z*z, 2*(x*y-w*z), 2*(x*z+w*y)),
            (2*(x*y+w*z), w*w-x*x+y*y-z*z, 2*(y*z-w*x)),
            (2*(x*z-w*y), 2*(y*z+w*x), w*w-x*x-y*y+z*z))
    return tuple(tuple(value / denominator for value in row) for row in rows)


def section_point(origin, quaternion, point):
    """Round each whole origin-plus-rotation result once to binary64."""
    offset = _native(origin, 3)
    u, v = _native(point, 2)
    rotated = _matrix_vector(section_matrix(quaternion), (u, v, Fraction(0)))
    return tuple(_binary64(a + b) for a, b in zip(offset, rotated))


def placement_matrix(quaternion):
    """Independently retain the existing outer placement's arithmetic."""
    _native(quaternion, 4)
    length = math.hypot(*quaternion)
    assert length > 0 and math.isfinite(length)
    q = tuple(float(value) / length for value in quaternion)
    if next((value for value in q if value != 0), 1.0) < 0:
        q = tuple(-value for value in q)
    w, x, y, z = (Fraction(_binary64(value)) for value in q)
    return ((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
            (2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)),
            (2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)))


def place_point(point, quaternion, origin):
    rotated = _matrix_vector(placement_matrix(quaternion), _native(point, 3))
    _native(origin, 3)
    return tuple(_binary64(_binary64(value) + float(shift)) for value, shift in zip(rotated, origin))


def _sign_cap(points, axis, sign, label):
    exact = tuple(tuple(Fraction(value) for value in p) for p in points)
    normal = cross(sub(exact[1], exact[0]), sub(exact[2], exact[0]))
    assert sign * dot(normal, axis) > 0, label + ' cap must face its authored outward frame axis'


def _ordered_sections(wanted):
    sections = sorted(wanted['sections'], key=lambda section: section['order'])
    sections = [{**section, 'rings': [
        {**ring, 'vertices': sorted(ring['vertices'], key=lambda vertex: vertex['order'])}
        for ring in sorted(section['rings'], key=lambda ring: ring['order'])]}
        for section in sections]
    assert 2 <= len(sections) <= 8
    assert len({s['key'] for s in sections}) == len(sections)
    assert len({s['order'] for s in sections}) == len(sections)
    assert all(type(s['order']) is int and 0 <= s['order'] <= 65535 for s in sections)
    return sections


def source_facts(wanted):
    """Recompute source points and progression independently of frozen witnesses."""
    sections = _ordered_sections(wanted)
    points, axes, matrices, origins = {}, {}, {}, {}
    for section in sections:
        key = section['key']
        origins[key] = _native(section['origin_m'], 3)
        assert all(abs(value) <= 100 for value in origins[key])
        matrices[key] = section_matrix(section['orientation_wxyz'])
        axes[key] = tuple(row[2] for row in matrices[key])
        for ring in section['rings']:
            for vertex in ring['vertices']:
                uv = _native(vertex['point_m'], 2)
                assert all(abs(value) <= 100 for value in uv)
                transformed = _matrix_vector(matrices[key], (*uv, Fraction(0)))
                point = tuple(_binary64(a + b) for a, b in zip(origins[key], transformed))
                assert all(abs(value) <= 256 for value in point)
                identity = (key, ring['key'], vertex['key'])
                assert identity not in points, 'A source identity cannot repeat'
                points[identity] = point
    assert len(set(points.values())) == len(points), 'Distinct source identities collapse before delivery'
    if 'source_positions' in wanted:
        witnesses = {tuple(item['identity']): item for item in wanted['source_positions']}
        assert len(witnesses) == len(wanted['source_positions']) and set(witnesses) == set(points)
        for identity, point in points.items():
            assert list(point) == witnesses[identity]['position_m'], 'Frozen source position differs'
            assert [value.hex() for value in point] == witnesses[identity]['position_hex'], 'Frozen source bits differ'
    progression = []
    for previous, following in zip(sections, sections[1:]):
        a, b = previous['key'], following['key']
        displacement = sub(origins[b], origins[a])
        distance2 = dot(displacement, displacement)
        first, second = dot(displacement, axes[a]), dot(displacement, axes[b])
        assert distance2 >= Fraction(.001)**2, 'Adjacent origins are too close'
        assert first > 0 and second > 0, 'Adjacent frames violate forward progression'
        progression.append({'from': a, 'to': b,
                            'squared_distance_exact': [str(distance2.numerator), str(distance2.denominator)],
                            'previous_normal_dot_exact': [str(first.numerator), str(first.denominator)],
                            'next_normal_dot_exact': [str(second.numerator), str(second.denominator)]})
    if 'progression' in wanted:
        assert progression == wanted['progression'], 'Frozen progression witnesses differ'
    return sections, points, axes, progression


def check_geometry(decoded, path, wanted):
    """Check actual corners against framed source identities and closed surfaces."""
    triangles = decoded.triangles(path)
    assert len(triangles) == wanted['triangle_count'], 'Unexpected complete triangle count'
    sections, source, axes, progression = source_facts(wanted)
    n = sum(len(ring['vertices']) for ring in sections[0]['rings'])
    h = sum(ring['role'] == 'hole' for ring in sections[0]['rings'])
    cap_count = n + 2*h - 2
    assert sum(ring['role'] == 'outer' for ring in sections[0]['rings']) == 1
    assert wanted['section_count'] == len(sections) and wanted['vertices_per_section'] == n
    assert wanted['authored_vertex_count'] == len(source) == len(sections)*n
    assert wanted['ring_count'] == h+1 and wanted['hole_count'] == h
    assert wanted['cap_triangle_count'] == cap_count
    assert wanted['strip_triangle_count'] == 2*(len(sections)-1)*n
    assert wanted['triangle_count'] == 2*len(sections)*n+4*h-4
    assert wanted['vertex_count'] == 3*wanted['triangle_count']
    assert wanted['surface_rule'] == 'fixed-diagonal-triangles'
    assert wanted['section_transform_rule'] == 'exact-rational-quaternion-single-round'
    offset = wanted.get('local_position_m', [0, 0, 0])
    rotation = wanted.get('local_orientation_wxyz', [1, 0, 0, 0])
    outer_matrix = placement_matrix(rotation)

    def rotate(vector):
        return tuple(_binary64(value) for value in _matrix_vector(outer_matrix, _native(vector, 3)))

    placed_source = {identity: place_point(point, rotation, offset) for identity, point in source.items()}
    quantized = {identity: tuple(_f32(value) for value in point) for identity, point in placed_source.items()}
    inverse = {point: identity for identity, point in quantized.items()}
    assert len(inverse) == len(source), 'Distinct source identities collapse in binary32 delivery'
    for identity, point in quantized.items():
        close(point, placed_source[identity], 1e-5)
    placed_axes = {key: _matrix_vector(outer_matrix, axis) for key, axis in axes.items()}

    domains = {}
    for section in sections:
        polygons, boundaries, coordinates = {}, [], {}
        for ring in section['rings']:
            identities = []
            for vertex in ring['vertices']:
                identity = (ring['key'], vertex['key'])
                coordinates[identity] = _native(vertex['point_m'], 2)
                identities.append(identity)
            polygons[ring['key']] = [coordinates[identity] for identity in identities]
            boundaries.extend(zip(identities, identities[1:]+identities[:1]))
        exterior = next(ring['key'] for ring in section['rings'] if ring['role'] == 'outer')
        outer = polygons[exterior]
        holes = [polygons[ring['key']] for ring in section['rings'] if ring['role'] == 'hole']
        exact_boundaries = [(coordinates[a], coordinates[b]) for a, b in boundaries]
        area2 = sum(a[0]*b[1]-a[1]*b[0] for a, b in exact_boundaries)
        domains[section['key']] = (outer, holes, boundaries, exact_boundaries, coordinates, area2)

    expected_strips = {}
    for lower, upper in zip(sections, sections[1:]):
        assert len(lower['rings']) == len(upper['rings'])
        for low, high in zip(lower['rings'], upper['rings']):
            assert (low['key'], low['role'], low['order']) == (high['key'], high['role'], high['order'])
            assert [(v['key'], v['order']) for v in low['vertices']] == [(v['key'], v['order']) for v in high['vertices']]
            for i, vertex in enumerate(low['vertices']):
                next_vertex = low['vertices'][(i+1) % len(low['vertices'])]
                a0 = (lower['key'], low['key'], vertex['key'])
                b0 = (lower['key'], low['key'], next_vertex['key'])
                a1 = (upper['key'], high['key'], vertex['key'])
                b1 = (upper['key'], high['key'], next_vertex['key'])
                for triple in ((a0, b0, a1), (b0, b1, a1)):
                    expected_strips[_cyclic(triple)] = vertex['region']

    seen, strips, regions, edges = set(), Counter(), Counter(), Counter()
    caps = {sections[0]['key']: [], sections[-1]['key']: []}
    cap_edges = {key: Counter() for key in caps}
    cap_measures = {key: [] for key in caps}
    source_caps = {key: [] for key in caps}
    actual_triangles, source_triangles, actual_ids, surface_areas, source_areas = [], [], [], [], []
    for region, positions, normals, material in triangles:
        assert len(positions) == len(normals) == 3
        positions = [tuple(point) for point in positions]
        ids = []
        for point in positions:
            assert len(point) == 3 and all(math.isfinite(value) for value in point)
            assert point in inverse, 'A supplied corner must equal its source-quantized authored position'
            ids.append(inverse[point])
            seen.add(inverse[point])
        assert len(set(ids)) == 3, 'A face requires three distinct source identities'
        source_points = [source[identity] for identity in ids]
        source_length = _face_measure(source_points)[1]
        actual_length = _check_face_normals(positions, normals, source_points=source_points, rotate=rotate)
        assert normals[0] == normals[1] == normals[2], 'A flat triangle must retain one normal'
        source_areas.append(source_length/2)
        surface_areas.append(actual_length/2)
        levels = {identity[0] for identity in ids}
        if len(levels) == 1:
            key = next(iter(levels))
            assert key in caps, 'Only endpoint sections may emit caps'
            is_top = key == sections[-1]['key']
            sign = 1 if is_top else -1
            assert region == wanted.get('top_region' if is_top else 'bottom_region', 'top' if is_top else 'bottom'), 'Wrong endpoint cap region'
            _sign_cap(source_points, axes[key], sign, 'Source')
            _sign_cap(positions, placed_axes[key], sign, 'Delivered')
            planar_ids = [(identity[1], identity[2]) for identity in ids]
            for a, b in zip(planar_ids, planar_ids[1:]+planar_ids[:1]):
                cap_edges[key][a, b] += 1
            outer, holes, boundaries, exact_boundaries, coordinates, area2 = domains[key]
            oriented = planar_ids if is_top else list(reversed(planar_ids))
            triangle = tuple(coordinates[identity] for identity in oriented)
            _cap_domain(triangle, outer, holes, exact_boundaries, tuple(coordinates.values()))
            caps[key].append(triangle)
            cap_measures[key].append(actual_length/2)
            source_caps[key].append(source_length/2)
        else:
            triple = _cyclic(ids)
            assert triple in expected_strips, 'A strip must use the exact fixed diagonal and outward winding'
            assert region == expected_strips[triple], 'The lower outgoing edge owns both strip materials'
            strips[triple] += 1
        pbr = material['pbrMetallicRoughness']
        assert region in wanted['palette']
        close(pbr['baseColorFactor'], wanted['palette'][region], 1e-6)
        close([pbr['metallicFactor'], pbr['roughnessFactor']], [wanted['metallic'], wanted['roughness']], 1e-6)
        assert not material.get('doubleSided', False), 'Outward surfaces cannot use double-sided rendering'
        regions[region] += 1
        actual_triangles.append(positions)
        source_triangles.append(source_points)
        actual_ids.append(tuple(ids))
        for a, b in zip(ids, ids[1:]+ids[:1]):
            edges[a, b] += 1

    assert seen == set(source), 'Every authored identity must occur in the delivered mesh'
    assert set(strips) == set(expected_strips) and all(value == 1 for value in strips.values()), 'Every prescribed strip must occur once'
    cap_results = []
    for key, triangles_on_cap in caps.items():
        outer, holes, boundaries, exact_boundaries, coordinates, area2 = domains[key]
        assert len(triangles_on_cap) == cap_count, 'Wrong endpoint cap triangle count'
        assert sum(_turn(*triangle) for triangle in triangles_on_cap) == area2, 'Cap coverage area differs from authored domain'
        for i, triangle in enumerate(triangles_on_cap):
            for other in triangles_on_cap[i+1:]:
                assert _overlap_area2(triangle, other) == 0, 'Endpoint cap triangle interiors overlap'
        expected_boundary = set(boundaries if key == sections[-1]['key'] else [(b, a) for a, b in boundaries])
        observed = cap_edges[key]
        for edge in expected_boundary:
            assert observed[edge] == 1 and observed[edge[::-1]] == 0, 'Cap boundaries need one authored directed incidence'
        for edge, count in observed.items():
            assert count == 1, 'A cap cannot repeat a directed edge'
            if edge not in expected_boundary:
                assert edge[::-1] not in expected_boundary and observed[edge[::-1]] == 1, 'Cap interior edges need opposite incidence'
        # Actual areas are measured in three dimensions. Authored XY coverage
        # is exact, but rounded transformed triangles need not share a plane.
        cap_results.append({'section': key, 'authored_xy_area_m2': float(area2/2),
                            'source_area_m2': math.fsum(source_caps[key]),
                            'delivered_area_m2': math.fsum(cap_measures[key])})
    assert dict(sorted(regions.items())) == wanted['region_triangle_counts'], 'Regional triangle counts differ'
    assert all(count == 1 and edges[b, a] == 1 for (a, b), count in edges.items()), 'Mesh must be closed with opposite directed incidence'
    source_volume6 = _exact_signed_volume6(source_triangles)
    actual_volume6 = _exact_signed_volume6(actual_triangles)
    assert source_volume6 > 0, 'Source surface needs positive exact signed volume'
    assert actual_volume6 > 0, 'Delivered surface needs positive exact signed volume'
    source_contacts = check_surface_intersections(source_triangles, actual_ids)
    actual_contacts = check_surface_intersections(actual_triangles, actual_ids)
    area_value, volume_value = math.fsum(surface_areas), float(actual_volume6/6)
    assert abs(math.fsum(source_areas)-wanted['surface_area_m2']) <= 1e-4, 'Source surface area differs'
    assert abs(float(source_volume6/6)-wanted['volume_m3']) <= 1e-4, 'Source signed volume differs'
    assert abs(area_value-wanted['surface_area_m2']) <= 1e-4, ('Actual triangle surface area differs', area_value, wanted['surface_area_m2'])
    assert abs(volume_value-wanted['volume_m3']) <= 1e-4, ('Actual signed volume differs', volume_value, wanted['volume_m3'])
    bounds = [[min(point[i] for point in source.values()) for i in range(3)],
              [max(point[i] for point in source.values()) for i in range(3)]]
    for actual, expected in zip(bounds, wanted['bounds_m']):
        close(actual, expected, 1e-5)
    return {'status': 'passed', 'path': path, 'sections': len(sections), 'rings': h+1, 'holes': h,
            'authored_vertices': len(source), 'triangles': len(triangles), 'cap_triangles_per_end': cap_count,
            'strip_triangles': len(expected_strips), 'flat_corners': 3*len(triangles),
            'regions': dict(regions), 'surface_area_m2': area_value, 'signed_volume_m3': volume_value,
            'source_signed_volume_m3': float(source_volume6/6), 'cap_areas_m2': [c['delivered_area_m2'] for c in cap_results],
            'cap_domains': cap_results, 'bounds_m': bounds, 'oriented_edges': len(edges),
            'intersections': actual_contacts, 'source_intersections': source_contacts,
            'progression': progression, 'coverage': 'independent rational frames, authored XY cap domains and actual complete 3D surfaces'}


def check_glb(data, nodes, program_revision=None, sample_times=(0, .25, .5, .75, 1)):
    """Validate supplied bytes, full carrier membership and recorded motion."""
    decoded = Decoded(data)
    assert set(decoded.objects()) == set(nodes), 'Delivered carrier inventory differs'
    scenes = decoded.document['scenes']
    scene_index = decoded.document.get('scene', 0)
    assert type(scene_index) is int and 0 <= scene_index < len(scenes)
    roots = scenes[scene_index]['nodes']
    assert all(type(index) is int for index in roots)
    assert len(roots) == len(decoded.document['nodes']) and set(roots) == set(range(len(roots))), 'The active scene must expose every carrier once'
    animations = decoded.document.get('animations', [])
    assert len(animations) == 1, 'Recorded delivery requires one identified clip'
    channels = animations[0]['channels']
    assert {(c['target']['node'], c['target']['path']) for c in channels} == {
        (i, channel) for i in range(len(roots)) for channel in ('translation', 'rotation')}, 'Each recorded carrier needs both rigid motion channels'
    for channel in channels:
        index = channel['sampler']
        assert type(index) is int and 0 <= index < len(animations[0]['samplers'])
        sampler = animations[0]['samplers'][index]
        assert sampler.get('interpolation', 'LINEAR') == 'LINEAR'
        times = decoded.accessor(sampler['input'])
        rows = decoded.accessor(sampler['output'])
        assert len(times) == len(rows) >= 2
        assert all(type(time) in (int, float) and math.isfinite(time) for time in times)
        assert all(a < b for a, b in zip(times, times[1:])), 'Recorded clocks must increase strictly'
        assert times[0] == min(sample_times) and times[-1] == max(sample_times), 'Recorded clip horizon differs'
        size = 3 if channel['target']['path'] == 'translation' else 4
        assert all(len(row) == size and all(math.isfinite(value) for value in row) for row in rows)
        if size == 4:
            assert all(abs(math.hypot(*row)-1) <= 1e-5 for row in rows)
    if program_revision is not None:
        assert decoded.document['extras']['ontokin']['program']['revision'] == program_revision
    geometry, observations = [], []
    for path, wanted in nodes.items():
        if wanted['geometry'] is not None:
            geometry.append(check_geometry(decoded, path, wanted['geometry']))
        else:
            assert not decoded.triangles(path), 'A geometry-free parent cannot add an unclaimed mesh'
        for time in sample_times:
            pose = decoded.pose(path, time)
            expected = [origin+time*speed for origin, speed in zip(wanted['origin'], wanted['velocity'])]
            close(pose['translation'], expected, .001)
            close(pose['rotation'], wanted.get('rotation_xyzw', [0, 0, 0, 1]), .001)
            observations.append({'path': path, 'time_seconds': time, 'translation': list(pose['translation']),
                                 'rotation': list(pose['rotation'])})
    return {'status': 'passed', 'geometry': geometry, 'observations': observations,
            'target_contract': 'ontokin.glb/0.11', 'program_revision': program_revision}


