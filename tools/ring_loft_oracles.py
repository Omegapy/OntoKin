"""Independent checks of supplied GLB/0.10 bytes and frozen ring-loft facts.

No OntoKin runtime or production geometry routine is imported. Cap coverage
uses the earlier independent planar checker. Three-dimensional intersections
use exact edge/triangle witnesses and closed segment clipping, independently
of the production plane-section algorithm.
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


class Decoded(_AccessorReader):
    """Decode a rigid, inline GLB with the explicit C077 binding."""

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
        assert meta['target_contract'] == 'ontokin.glb/0.10'
        assert meta['profile'] == 'polygon-loft-0.1'
        assert meta['schema_version'] == '0.10'
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
            material_index = primitive['material']
            assert type(material_index) is int and 0 <= material_index < len(self.document['materials'])
            material = self.document['materials'][material_index]
            region = material['extras']['ontokin']['source_region_key']
            for start in range(0, len(indices), 3):
                ids = indices[start:start + 3]
                result.append((region, [positions[i] for i in ids], [normals[i] for i in ids], material))
        return result


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _cyclic(triangle):
    """Retain winding while ignoring a harmless cyclic corner rotation."""
    triple = tuple(triangle)
    return min(triple, triple[1:] + triple[:1], triple[2:] + triple[:2])


def _face_measure(points):
    """Retain the exact face sign before normalizing its bounded ratios."""
    exact = tuple(tuple(Fraction(value) for value in point) for point in points)
    face = cross(sub(exact[1], exact[0]), sub(exact[2], exact[0]))
    maximum = max(abs(value) for value in face)
    assert maximum > 0, 'Actual delivered face area must be nonzero exactly'
    ratios = tuple(float(value / maximum) for value in face)
    ratio_length = math.sqrt(math.fsum(value * value for value in ratios))
    unit = tuple(value / ratio_length for value in ratios)
    length = float(maximum) * ratio_length
    assert math.isfinite(length) and length > 0, 'Actual face measure must remain representable'
    return face, length, unit


def _check_face_normals(points, normals, *, source_points=None, rotate=None):
    """Check actual/source normals without a rounded cross or dot sign."""
    face, length, unit = _face_measure(points)
    if source_points is None:
        source_points = points
    source_unit = _face_measure(source_points)[2]
    if rotate is not None:
        source_unit = rotate(source_unit)
    for normal in normals:
        assert len(normal) == 3 and all(math.isfinite(value) for value in normal)
        assert abs(math.hypot(*normal) - 1) <= 1e-5
        assert dot(face, tuple(Fraction(value) for value in normal)) > 0, 'Actual normals must follow exact outward face winding'
        close(normal, unit, 1e-5)
        close(normal, source_unit, 1e-5)
    return length


def _exact_signed_volume6(triangles):
    """Use the supplied positions before any rounded inverse placement."""
    result = Fraction(0)
    for triangle in triangles:
        a, b, c = (tuple(Fraction(value) for value in point) for point in triangle)
        result += dot(a, cross(b, c))
    return result


def _in_triangle(point, triangle, normal):
    return all(dot(normal, cross(sub(triangle[(i + 1) % 3], triangle[i]),
                                 sub(point, triangle[i]))) >= 0 for i in range(3))


def _coplanar_segment_hits(a, b, triangle, normal):
    """Clip one coplanar segment against three closed exact half-planes."""
    remove = max(range(3), key=lambda i: abs(normal[i]))
    project = lambda point: tuple(point[i] for i in range(3) if i != remove)
    projected = tuple(map(project, triangle))
    if _turn(*projected) < 0:
        projected = tuple(reversed(projected))
    pa, pb = project(a), project(b)
    lo, hi = Fraction(0), Fraction(1)
    for i, first in enumerate(projected):
        second = projected[(i + 1) % 3]
        sa, sb = _turn(first, second, pa), _turn(first, second, pb)
        if sa < 0 and sb < 0:
            return ()
        if sa < 0 <= sb:
            lo = max(lo, -sa / (sb - sa))
        elif sb < 0 <= sa:
            hi = min(hi, sa / (sa - sb))
        if lo > hi:
            return ()
    return tuple(tuple(a[i] + t * (b[i] - a[i]) for i in range(3)) for t in (lo, hi))


def _edge_hits_triangle(a, b, triangle, normal):
    da, db = dot(normal, sub(a, triangle[0])), dot(normal, sub(b, triangle[0]))
    if da == db == 0:
        return _coplanar_segment_hits(a, b, triangle, normal)
    if da * db > 0 or da == db:
        return ()
    fraction = da / (da - db)
    if not 0 <= fraction <= 1:
        return ()
    point = tuple(a[i] + fraction * (b[i] - a[i]) for i in range(3))
    return (point,) if _in_triangle(point, triangle, normal) else ()


def _on_shared(point, shared):
    if len(shared) == 1:
        return point == shared[0]
    if len(shared) == 2:
        a, b = shared
        return (not any(cross(sub(b, a), sub(point, a))) and
                all(min(a[i], b[i]) <= point[i] <= max(a[i], b[i]) for i in range(3)))
    return False


def _contact_allowed(first, second, shared):
    """All vertices of the convex contact must belong to the shared simplex.

    Intersection vertices arise where an edge meets the other triangle. For a
    coplanar overlap, closed segment clipping also finds contained endpoints.
    Their convex hull is the whole intersection, so checking these witnesses
    is sufficient. No tolerance admits a nonshared touch.
    """
    a, na, ba = first
    b, nb, bb = second
    if any(ba[1][i] < bb[0][i] or bb[1][i] < ba[0][i] for i in range(3)):
        return True
    distances_a = [dot(nb, sub(point, b[0])) for point in a]
    distances_b = [dot(na, sub(point, a[0])) for point in b]
    if any(all(v > 0 for v in values) or all(v < 0 for v in values)
           for values in (distances_a, distances_b)):
        return True
    for edges, other, normal in ((a, b, nb), (b, a, na)):
        for i, start in enumerate(edges):
            for point in _edge_hits_triangle(start, edges[(i + 1) % 3], other, normal):
                if not _on_shared(point, shared):
                    return False
    return True


def check_surface_intersections(triangle_positions, triangle_ids):
    """Check actual 3D triangles against explicitly shared source identities."""
    assert len(triangle_positions) == len(triangle_ids)
    prepared, vertices = [], {}
    for positions, ids in zip(triangle_positions, triangle_ids):
        assert len(positions) == len(ids) == 3 and len(set(ids)) == 3
        points = tuple(tuple(Fraction(value) for value in point) for point in positions)
        for identity, point in zip(ids, points):
            assert identity not in vertices or vertices[identity] == point, 'An identity must have one actual position'
            vertices[identity] = point
        normal = cross(sub(points[1], points[0]), sub(points[2], points[0]))
        assert any(normal), 'A supplied triangle must have nonzero exact area'
        bounds = (tuple(min(p[i] for p in points) for i in range(3)),
                  tuple(max(p[i] for p in points) for i in range(3)))
        prepared.append((points, normal, bounds))
    pairs = 0
    for i, first in enumerate(prepared):
        for j in range(i + 1, len(prepared)):
            pairs += 1
            identities = set(triangle_ids[i]) & set(triangle_ids[j])
            assert len(identities) < 3, 'Duplicate supplied faces are not a surface'
            shared = tuple(vertices[key] for key in sorted(identities))
            assert _contact_allowed(first, prepared[j], shared), (
                'Nonadjacent surface intersection or contact beyond a shared simplex', i, j)
    return {'triangle_pairs': pairs, 'status': 'passed',
            'method': 'exact edge-triangle witnesses and closed coplanar segment clipping'}


def check_geometry(decoded, path, wanted):
    """Validate actual decoded mesh data against one frozen authored loft."""
    triangles = decoded.triangles(path)
    assert len(triangles) == wanted['triangle_count'], 'Unexpected complete triangle count'
    sections = sorted(wanted['sections'], key=lambda s: s['order'])
    sections = [{**s, 'rings': [{**r, 'vertices': sorted(r['vertices'], key=lambda v: v['order'])}
                               for r in sorted(s['rings'], key=lambda r: r['order'])]} for s in sections]
    n = sum(len(r['vertices']) for r in sections[0]['rings'])
    h = sum(r['role'] == 'hole' for r in sections[0]['rings'])
    cap_count = n + 2 * h - 2
    assert wanted['section_count'] == len(sections) and wanted['vertices_per_section'] == n
    assert wanted['authored_vertex_count'] == len(sections) * n and wanted['hole_count'] == h
    assert wanted['ring_count'] == h + 1 and wanted['cap_triangle_count'] == cap_count
    assert wanted['strip_triangle_count'] == 2 * (len(sections) - 1) * n
    assert wanted['triangle_count'] == 2 * len(sections) * n + 4 * h - 4
    assert wanted['vertex_count'] == 3 * wanted['triangle_count']
    assert wanted.get('surface_rule') == 'fixed-diagonal-triangles'
    offset = wanted.get('local_position_m', [0, 0, 0])
    exact_offset = tuple(Fraction(value) for value in offset)
    rotation = wanted.get('local_orientation_wxyz', [1, 0, 0, 0])
    assert rotation in ([1, 0, 0, 0], [0, 1, 0, 0]), 'Frozen placements use identity or an X half-turn'

    def rotate(point):
        return tuple(point) if rotation[0] == 1 else (point[0], -point[1], -point[2])

    def unplace(point):
        return rotate(sub(point, offset))

    source, quantized, inverse = {}, {}, {}
    section_indices, rings_by_section, domains = {}, {}, {}
    for index, section in enumerate(sections):
        key = section['key']
        section_indices[key] = index
        rings_by_section[key] = section['rings']
        polygons, boundaries, coordinates = {}, [], {}
        for ring in section['rings']:
            ring_key = ring['key']
            polygon, identities = [], []
            for vertex in ring['vertices']:
                vertex_key = vertex['key']
                identity = (key, ring_key, vertex_key)
                local = (*vertex['point_m'], section['station_m'])
                source[identity] = local
                placed = tuple(_f32(value + shift) for value, shift in zip(rotate(local), offset))
                assert placed not in inverse, 'Distinct source identities collapse in binary32 delivery'
                quantized[identity] = placed
                inverse[placed] = identity
                xy = tuple(Fraction(float(value)) for value in vertex['point_m'])
                planar_id = (ring_key, vertex_key)
                coordinates[planar_id] = xy
                polygon.append(xy)
                identities.append(planar_id)
            polygons[ring_key] = polygon
            boundaries.extend(zip(identities, identities[1:] + identities[:1]))
        outer_key = next(r['key'] for r in section['rings'] if r['role'] == 'outer')
        outer = polygons[outer_key]
        holes = [polygons[r['key']] for r in section['rings'] if r['role'] == 'hole']
        exact_boundaries = [(coordinates[a], coordinates[b]) for a, b in boundaries]
        area2 = sum(a[0] * b[1] - a[1] * b[0] for a, b in exact_boundaries)
        domains[key] = (outer, holes, boundaries, exact_boundaries, coordinates, area2)

    expected_strips = {}
    for lower, upper in zip(sections, sections[1:]):
        for low_ring, high_ring in zip(lower['rings'], upper['rings']):
            assert (low_ring['key'], low_ring['role'], low_ring['order']) == (high_ring['key'], high_ring['role'], high_ring['order'])
            assert [(v['key'], v['order']) for v in low_ring['vertices']] == [(v['key'], v['order']) for v in high_ring['vertices']]
            for i, vertex in enumerate(low_ring['vertices']):
                following = low_ring['vertices'][(i + 1) % len(low_ring['vertices'])]
                a0 = (lower['key'], low_ring['key'], vertex['key'])
                b0 = (lower['key'], low_ring['key'], following['key'])
                a1 = (upper['key'], high_ring['key'], vertex['key'])
                b1 = (upper['key'], high_ring['key'], following['key'])
                for triple in ((a0, b0, a1), (b0, b1, a1)):
                    expected_strips[_cyclic(triple)] = vertex['region']

    seen, strips, regions = set(), Counter(), Counter()
    cap_edges = {sections[0]['key']: Counter(), sections[-1]['key']: Counter()}
    caps = {key: [] for key in cap_edges}
    cap_measured_areas = {key: 0.0 for key in cap_edges}
    all_local, actual_triangles, actual_ids, directed_edges = [], [], [], Counter()
    surface_areas = []
    for region, positions, normals, material in triangles:
        assert len(positions) == len(normals) == 3
        positions = [tuple(point) for point in positions]
        ids, local = [], []
        for point in positions:
            assert len(point) == 3 and all(math.isfinite(value) for value in point)
            assert point in inverse, 'A supplied corner must equal its source-quantized authored position'
            identity = inverse[point]
            ids.append(identity)
            seen.add(identity)
            recovered = unplace(point)
            close(recovered, source[identity], 1e-5)
            local.append(recovered)
        assert len(set(ids)) == 3, 'A face requires three distinct source identities'
        length = _check_face_normals(positions, normals, source_points=[source[identity] for identity in ids], rotate=rotate)
        surface_areas.append(length / 2)
        exact_positions = [tuple(Fraction(value) for value in point) for point in positions]
        exact_local = [rotate(sub(point, exact_offset)) for point in exact_positions]
        levels = {identity[0] for identity in ids}
        if len(levels) == 1:
            key = next(iter(levels))
            assert key in caps, 'Only endpoint sections may emit caps'
            is_top = key == sections[-1]['key']
            assert region == wanted.get('top_region' if is_top else 'bottom_region', 'top' if is_top else 'bottom'), 'Wrong endpoint cap region'
            local_face = cross(sub(exact_local[1], exact_local[0]), sub(exact_local[2], exact_local[0]))
            sign = 1 if is_top else -1
            assert sign * local_face[2] > 0, 'End caps must have outward winding'
            planar_ids = [(identity[1], identity[2]) for identity in ids]
            for a, b in zip(planar_ids, planar_ids[1:] + planar_ids[:1]):
                cap_edges[key][a, b] += 1
            outer, holes, boundaries, exact_boundaries, coordinates, area2 = domains[key]
            oriented = planar_ids if is_top else list(reversed(planar_ids))
            triangle = tuple(coordinates[identity] for identity in oriented)
            _cap_domain(triangle, outer, holes, exact_boundaries, tuple(coordinates.values()))
            caps[key].append(triangle)
            cap_measured_areas[key] += float(abs(local_face[2]) / 2)
        else:
            triple = _cyclic(ids)
            assert triple in expected_strips, 'A strip must use the exact fixed diagonal and outward winding'
            assert region == expected_strips[triple], 'The lower outgoing edge owns both strip materials'
            strips[triple] += 1
        pbr = material['pbrMetallicRoughness']
        assert region in wanted['palette'], 'An actual region must name the source palette'
        close(pbr['baseColorFactor'], wanted['palette'][region], 1e-6)
        close([pbr['metallicFactor'], pbr['roughnessFactor']], [wanted['metallic'], wanted['roughness']], 1e-6)
        assert not material.get('doubleSided', False), 'Outward surfaces cannot be hidden by double-sided rendering'
        regions[region] += 1
        all_local.extend(local)
        actual_triangles.append(positions)
        actual_ids.append(tuple(ids))
        for a, b in zip(ids, ids[1:] + ids[:1]):
            directed_edges[a, b] += 1

    assert seen == set(source), 'Every authored section vertex must occur in the delivered mesh'
    assert set(strips) == set(expected_strips) and all(count == 1 for count in strips.values()), 'Every specified strip triangle must occur once'
    cap_results = []
    for key, triangles_on_cap in caps.items():
        outer, holes, boundaries, exact_boundaries, coordinates, area2 = domains[key]
        assert len(triangles_on_cap) == cap_count, 'Wrong endpoint cap triangle count'
        assert sum(_turn(*triangle) for triangle in triangles_on_cap) == area2, 'Cap coverage area differs from authored domain'
        for i, triangle in enumerate(triangles_on_cap):
            for other in triangles_on_cap[i + 1:]:
                assert _overlap_area2(triangle, other) == 0, 'Endpoint cap triangle interiors overlap'
        expected_boundary = set(boundaries if key == sections[-1]['key'] else [(b, a) for a, b in boundaries])
        observed = cap_edges[key]
        for edge in expected_boundary:
            assert observed[edge] == 1 and observed[edge[::-1]] == 0, 'Each cap boundary needs one authored directed incidence'
        interior = set()
        for edge, count in observed.items():
            assert count == 1, 'A cap cannot repeat a directed edge'
            if edge not in expected_boundary:
                assert edge[::-1] not in expected_boundary and observed[edge[::-1]] == 1, 'Cap internal edges require opposite incidence'
                interior.add(frozenset(edge))
        control = wanted.get('cap_diagonal_control')
        if control:
            diagonal = control['top' if key == sections[-1]['key'] else 'bottom']
            assert interior == {frozenset((control['ring_key'], vertex) for vertex in diagonal)}, 'Endpoint-specific cap diagonal was not preserved'
        assert abs(cap_measured_areas[key] - float(area2 / 2)) <= 1e-4, 'Measured endpoint cap area differs'
        cap_results.append(cap_measured_areas[key])
    assert dict(sorted(regions.items())) == wanted['region_triangle_counts'], 'Regional triangle counts differ'
    assert all(count == 1 and directed_edges[b, a] == 1 for (a, b), count in directed_edges.items()), 'Delivered mesh must be closed with opposite directed incidence'
    volume6 = _exact_signed_volume6(actual_triangles)
    assert volume6 > 0, 'The closed delivered surface needs positive exact signed volume'
    intersections = check_surface_intersections(actual_triangles, actual_ids)
    area_value, volume_value = math.fsum(surface_areas), float(volume6 / 6)
    assert abs(area_value - wanted['surface_area_m2']) <= 1e-4, ('Actual triangle surface area differs', area_value, wanted['surface_area_m2'])
    assert abs(volume_value - wanted['volume_m3']) <= 1e-4, ('Actual signed volume differs', volume_value, wanted['volume_m3'])
    bounds = [[min(point[i] for point in all_local) for i in range(3)], [max(point[i] for point in all_local) for i in range(3)]]
    for actual, expected in zip(bounds, wanted['bounds_m']):
        close(actual, expected)
    return {'path': path, 'status': 'passed', 'sections': len(sections), 'rings': h + 1, 'holes': h,
            'authored_vertices': len(source), 'triangles': len(triangles), 'cap_triangles_per_end': cap_count,
            'strip_triangles': len(strips), 'regions': dict(regions), 'surface_area_m2': area_value,
            'signed_volume_m3': volume_value, 'cap_areas_m2': cap_results, 'bounds_m': bounds,
            'oriented_edges': len(directed_edges), 'intersections': intersections,
            'coverage': 'source-quantized identities, independent endpoint domains, exact strips and complete 3D contacts'}


def check_glb(data, nodes, program_revision=None, sample_times=(0, .25, .5, .75, 1)):
    """Check one complete artifact with frozen geometry, origins and velocities."""
    decoded = Decoded(data)
    assert set(decoded.objects()) == set(nodes), 'Delivered carrier inventory differs'
    scenes = decoded.document['scenes']
    scene_index = decoded.document.get('scene', 0)
    assert type(scene_index) is int and 0 <= scene_index < len(scenes)
    roots = scenes[scene_index]['nodes']
    assert len(roots) == len(decoded.document['nodes']) and set(roots) == set(range(len(roots))), 'The active scene must expose every independently posed carrier once'
    assert len(decoded.document.get('animations', [])) == 1, 'Recorded delivery requires one identified clip'
    if program_revision is not None:
        assert decoded.document['extras']['ontokin']['program']['revision'] == program_revision
    geometry_results, observations = [], []
    for path, wanted in nodes.items():
        if wanted['geometry'] is not None:
            geometry_results.append(check_geometry(decoded, path, wanted['geometry']))
        else:
            assert not decoded.triangles(path), 'A geometry-free parent cannot add an unclaimed mesh'
        for time in sample_times:
            pose = decoded.pose(path, time)
            expected = [origin + time * speed for origin, speed in zip(wanted['origin'], wanted['velocity'])]
            close(pose['translation'], expected, .001)
            close(pose['rotation'], wanted.get('rotation_xyzw', [0, 0, 0, 1]), .001)
            observations.append({'path': path, 'time_seconds': time, 'translation': list(pose['translation']),
                                 'rotation': list(pose['rotation'])})
    return {'status': 'passed', 'geometry': geometry_results, 'observations': observations,
            'target_contract': 'ontokin.glb/0.10', 'program_revision': program_revision}
