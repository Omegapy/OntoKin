"""Independent supplied-byte checks for the frozen polygon-hole fixtures.

The checker imports no OntoKin runtime or production triangulator. It combines
measurements of decoded positions with exact boundary and coverage checks over
independently authored fixture coordinates.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import json
import math
import struct

from tools.extrusion_oracles import Decoded as _ExtrusionDecoded
from tools.extrusion_oracles import close, cross, dot, sub


class Decoded(_ExtrusionDecoded):
    """Reuse the independent accessor reader with explicit GLB/0.9 admission."""

    def __init__(self, data):
        assert len(data) >= 28
        assert struct.unpack_from('<III', data) == (0x46546c67, 2, len(data))
        length, kind = struct.unpack_from('<II', data, 12)
        assert kind == 0x4e4f534a and 20 + length + 8 <= len(data)
        self.document = json.loads(data[20:20 + length])
        start = 20 + length
        size, kind = struct.unpack_from('<II', data, start)
        assert kind == 0x004e4942 and start + 8 + size == len(data)
        self.binary = data[start + 8:]
        assert self.document['buffers'][0].get('uri') is None
        meta = self.document['extras']['ontokin']
        assert meta['target_contract'] == 'ontokin.glb/0.9'
        assert meta['profile'] == 'polygon-holes-0.1'
        assert meta['schema_version'] == '0.9'
        for node in self.document.get('nodes', []):
            assert node.get('scale', [1, 1, 1]) == [1, 1, 1], 'Rigid carriers require identity scale'
            assert 'matrix' not in node, 'Recorded carriers use explicit rigid transforms'
        for animation in self.document.get('animations', []):
            for channel in animation['channels']:
                assert channel['target']['path'] in ('translation', 'rotation'), (
                    'Recorded rigid motion cannot animate scale or weights')


def _turn(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, p):
    return (_turn(a, b, p) == 0
            and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def _segments_meet(a, b, c, d):
    ac, ad, ca, cb = _turn(a, b, c), _turn(a, b, d), _turn(c, d, a), _turn(c, d, b)
    if 0 in (ac, ad, ca, cb):
        return any((_on_segment(a, b, c), _on_segment(a, b, d),
                    _on_segment(c, d, a), _on_segment(c, d, b)))
    return (ac > 0) != (ad > 0) and (ca > 0) != (cb > 0)


def _location(point, polygon):
    """Return -1 outside, zero on the boundary and one strictly inside."""
    winding = 0
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        if _on_segment(a, b, point):
            return 0
        if a[1] <= point[1] < b[1] and _turn(a, b, point) > 0:
            winding += 1
        elif b[1] <= point[1] < a[1] and _turn(a, b, point) < 0:
            winding -= 1
    return 1 if winding else -1


def _inside_triangle(point, triangle):
    return all(_turn(triangle[i], triangle[(i + 1) % 3], point) > 0 for i in range(3))


def _overlap_area2(left, right):
    """Exact convex clipping measures positive overlap, including containment."""
    # A shared edge or vertex has zero area and is a valid triangulation contact
    for axis in range(2):
        if max(min(p[axis] for p in left), min(p[axis] for p in right)) >= min(
                max(p[axis] for p in left), max(p[axis] for p in right)):
            return Fraction(0)
    polygon = list(left)
    for i, a in enumerate(right):
        b = right[(i + 1) % 3]
        clipped = []
        if not polygon:
            return Fraction(0)
        previous = polygon[-1]
        previous_side = _turn(a, b, previous)
        for current in polygon:
            current_side = _turn(a, b, current)
            if (previous_side >= 0) != (current_side >= 0):
                t = previous_side / (previous_side - current_side)
                clipped.append(tuple(previous[k] + t * (current[k] - previous[k])
                                     for k in range(2)))
            if current_side >= 0:
                clipped.append(current)
            previous, previous_side = current, current_side
        polygon = clipped
    if len(polygon) < 3:
        return Fraction(0)
    return abs(sum(a[0] * polygon[(i + 1) % len(polygon)][1]
                   - a[1] * polygon[(i + 1) % len(polygon)][0]
                   for i, a in enumerate(polygon)))


def _cap_domain(triangle, outer, holes, boundaries, all_points):
    """Check full triangle boundaries and interiors, beyond their centroids."""
    assert _turn(*triangle) > 0, 'A normalized cap triangle needs positive exact area'
    for i, a in enumerate(triangle):
        b = triangle[(i + 1) % 3]
        for point in all_points:
            assert point in (a, b) or not _on_segment(a, b, point), (
                'A cap edge skips an authored boundary vertex')
        authored = any((a, b) in ((c, d), (d, c)) for c, d in boundaries)
        for c, d in boundaries:
            if (a, b) in ((c, d), (d, c)):
                continue
            if _segments_meet(a, b, c, d):
                assert a in (c, d) or b in (c, d), 'A cap edge crosses an authored boundary'
        midpoint = tuple((a[k] + b[k]) / 2 for k in range(2))
        if not authored:
            assert _location(midpoint, outer) == 1, 'A cap diagonal leaves the material domain'
            assert all(_location(midpoint, hole) == -1 for hole in holes), (
                'A cap diagonal crosses a hole interior or boundary')
    centroid = tuple(sum(point[k] for point in triangle) / 3 for k in range(2))
    assert _location(centroid, outer) == 1, 'A cap triangle lies outside the outer boundary'
    assert all(_location(centroid, hole) == -1 for hole in holes), 'A cap triangle fills a hole'
    for hole in holes:
        assert not any(_inside_triangle(point, triangle) for point in hole), (
            'A cap triangle covers an authored hole vertex')
        for i, a in enumerate(hole):
            b = hole[(i + 1) % len(hole)]
            midpoint = tuple((a[k] + b[k]) / 2 for k in range(2))
            assert not _inside_triangle(midpoint, triangle), 'A cap triangle covers a hole edge'


def check_geometry(decoded, path, wanted):
    """Measure one actual mesh against independent ring, material and pose facts."""
    triangles = decoded.triangles(path)
    assert len(triangles) == wanted['triangle_count'], 'Unexpected complete triangle count'
    rings = sorted(wanted['rings'], key=lambda ring: ring['order'])
    rings = [{**ring, 'vertices': sorted(ring['vertices'], key=lambda vertex: vertex['order'])}
             for ring in rings]
    n = sum(len(ring['vertices']) for ring in rings)
    h = sum(ring['role'] == 'hole' for ring in rings)
    assert len(rings) == h + 1 and sum(ring['role'] == 'outer' for ring in rings) == 1
    assert wanted['boundary_vertex_count'] == n and wanted['hole_count'] == h
    assert wanted['triangle_count'] == 4 * n + 4 * h - 4
    assert wanted['vertex_count'] == 3 * wanted['triangle_count']
    cap_count = n + 2 * h - 2
    assert wanted['cap_triangle_count'] == cap_count
    depth = wanted['depth_m']
    offset = wanted.get('local_position_m', [0, 0, 0])
    rotation = wanted.get('local_orientation_wxyz', [1, 0, 0, 0])
    assert rotation in ([1, 0, 0, 0], [0, 1, 0, 0]), 'Frozen placements are identity or X half-turn'

    def local_vector(vector):
        return tuple(vector) if rotation[0] == 1 else (vector[0], -vector[1], -vector[2])

    def unplace(point):
        return local_vector(sub(point, offset))

    points = {}
    exact = {}
    polygons = {}
    boundaries = []
    boundary_owners = {}
    corners = {}
    for ring in rings:
        vertices = ring['vertices']
        identities = [(ring['key'], vertex['key']) for vertex in vertices]
        for identity, vertex in zip(identities, vertices):
            points[identity] = tuple(vertex['point_m'])
            exact[identity] = tuple(Fraction(float(value)) for value in vertex['point_m'])
            for level in (0, 1):
                corners[(identity, level)] = (*points[identity], depth if level else 0.0)
        polygons[ring['key']] = [exact[identity] for identity in identities]
        for i, a in enumerate(identities):
            b = identities[(i + 1) % len(identities)]
            boundaries.append((a, b))
            boundary_owners[frozenset((a, b))] = (a, b, vertices[i]['region'])
    outer = polygons[next(ring['key'] for ring in rings if ring['role'] == 'outer')]
    holes = [polygons[ring['key']] for ring in rings if ring['role'] == 'hole']
    exact_boundaries = [(exact[a], exact[b]) for a, b in boundaries]
    exact_area2 = sum(a[0] * b[1] - b[0] * a[1] for a, b in exact_boundaries)
    assert abs(float(exact_area2 / 2) - wanted['area_m2']) <= 1e-4

    mapped_positions = {}
    reverse_positions = {}
    raw_edges = Counter()
    counts = Counter()
    cap_edges = {0: Counter(), 1: Counter()}
    caps = {0: [], 1: []}
    cap_areas = {0: 0.0, 1: 0.0}
    walls = Counter()
    all_local = []
    area = volume = wall_area = 0.0

    for region, placed, normals, material in triangles:
        assert len(placed) == len(normals) == 3
        counts[region] += 1
        local = [unplace(point) for point in placed]
        all_local.extend(local)
        identities = []
        for supplied, point in zip(placed, local):
            assert len(point) == 3 and all(math.isfinite(value) for value in point)
            matches = [identity for identity, expected in corners.items()
                       if math.dist(point, expected) <= 1e-5]
            assert len(matches) == 1, 'A decoded corner must identify one authored boundary vertex and level'
            identity = matches[0]
            actual = tuple(supplied)
            assert identity not in mapped_positions or mapped_positions[identity] == actual, (
                'Repeated corners must have consistent actual decoded positions')
            assert actual not in reverse_positions or reverse_positions[actual] == identity, (
                'Distinct authored corners cannot collapse to one decoded position')
            mapped_positions[identity] = actual
            reverse_positions[actual] = identity
            identities.append(identity)
        assert len(set(identities)) == 3, 'A triangle cannot repeat an authored corner'
        face = cross(sub(placed[1], placed[0]), sub(placed[2], placed[0]))
        magnitude = math.hypot(*face)
        assert math.isfinite(magnitude) and magnitude > 0, 'A decoded triangle must have nonzero area'
        for normal in normals:
            assert len(normal) == 3 and all(math.isfinite(value) for value in normal)
            assert abs(math.hypot(*normal) - 1) <= 1e-5 and dot(face, normal) > 0
            close(normal, [value / magnitude for value in face], 1e-5)
        area += magnitude / 2
        volume += dot(local[0], cross(local[1], local[2])) / 6
        levels = {identity[1] for identity in identities}
        local_face = cross(sub(local[1], local[0]), sub(local[2], local[0]))
        if len(levels) == 1:
            level = levels.pop()
            assert region == wanted.get('top_region' if level else 'bottom_region',
                                        'top' if level else 'bottom'), 'Wrong cap material region'
            sign = 1 if level else -1
            assert sign * local_face[2] > 0, 'A cap must point out of the solid'
            for normal in normals:
                close(local_vector(normal), [0, 0, sign], 1e-5)
            xy = [identity[0] for identity in identities]
            for a, b in zip(xy, xy[1:] + xy[:1]):
                cap_edges[level][(a, b)] += 1
            triangle = tuple(exact[identity] for identity in (xy if level else list(reversed(xy))))
            _cap_domain(triangle, outer, holes, exact_boundaries, tuple(exact.values()))
            caps[level].append(triangle)
            cap_areas[level] += abs(local_face[2]) / 2
        else:
            xy = frozenset(identity[0] for identity in identities)
            assert len(xy) == 2 and xy in boundary_owners, 'A wall must follow one authored ring edge'
            a, b, owner = boundary_owners[xy]
            assert region == owner, 'The outgoing authored edge owns the wall material'
            walls[xy] += 1
            dx, dy = points[b][0] - points[a][0], points[b][1] - points[a][1]
            length = math.hypot(dx, dy)
            outward = (dy / length, -dx / length, 0.0)
            assert dot(local_face, outward) > 0, 'A wall must face away from material, including into holes'
            for normal in normals:
                close(local_vector(normal), outward, 1e-5)
            wall_area += magnitude / 2
        pbr = material['pbrMetallicRoughness']
        close(pbr['baseColorFactor'], wanted['palette'][region], 1e-6)
        close([pbr['metallicFactor'], pbr['roughnessFactor']],
              [wanted['metallic'], wanted['roughness']], 1e-6)
        for a, b in zip(placed, placed[1:] + placed[:1]):
            raw_edges[(tuple(a), tuple(b))] += 1

    assert set(mapped_positions) == set(corners), 'Every authored boundary corner must be present'
    for level in (0, 1):
        cap = caps[level]
        assert len(cap) == cap_count, 'Wrong cap triangle count'
        assert sum(_turn(*triangle) for triangle in cap) == exact_area2, 'Wrong exact cap coverage area'
        for i, triangle in enumerate(cap):
            for other in cap[i + 1:]:
                assert _overlap_area2(triangle, other) == 0, 'Cap triangle interiors overlap'
        expected_boundary = set(boundaries if level else [(b, a) for a, b in boundaries])
        observed = cap_edges[level]
        for edge in expected_boundary:
            assert observed[edge] == 1 and observed[edge[::-1]] == 0, (
                'A cap must contain each directed authored boundary exactly once')
        for edge, count in observed.items():
            assert count == 1, 'A cap edge cannot repeat'
            if edge not in expected_boundary:
                assert edge[::-1] not in expected_boundary and observed[edge[::-1]] == 1, (
                    'A cap interior edge needs exactly one opposite incidence')
        assert abs(cap_areas[level] - wanted['area_m2']) <= 1e-4, 'Wrong measured cap area'
    assert set(walls) == set(boundary_owners) and all(count == 2 for count in walls.values()), (
        'Every outer and inner boundary edge needs two wall triangles')
    assert dict(counts) == wanted['region_triangle_counts'], 'Wrong regional triangle counts'
    assert all(count == 1 and raw_edges[(b, a)] == 1 for (a, b), count in raw_edges.items()), (
        'The actual decoded mesh needs one opposite incidence for every directed edge')
    perimeter = sum(math.dist(unplace(mapped_positions[(a, 0)]), unplace(mapped_positions[(b, 0)]))
                    for a, b in boundaries)
    assert abs(perimeter - wanted['boundary_perimeter_m']) <= 1e-4, 'Wrong measured ring perimeter'
    assert abs(wall_area - wanted['boundary_perimeter_m'] * depth) <= 1e-4, 'Wrong measured wall area'
    assert abs(area - wanted['surface_area_m2']) <= 1e-4, (area, wanted['surface_area_m2'])
    assert abs(volume - wanted['volume_m3']) <= 1e-4, (volume, wanted['volume_m3'])
    bounds = [[min(point[i] for point in all_local) for i in range(3)],
              [max(point[i] for point in all_local) for i in range(3)]]
    for actual, expected in zip(bounds, wanted['bounds_m']):
        close(actual, expected)
    return {'path': path, 'status': 'passed', 'triangles': len(triangles),
            'cap_triangles_per_side': cap_count, 'rings': len(rings), 'holes': h,
            'regions': dict(counts), 'surface_area_m2': area, 'signed_volume_m3': volume,
            'cap_areas_m2': [cap_areas[0], cap_areas[1]], 'boundary_perimeter_m': perimeter,
            'oriented_edges': len(raw_edges), 'bounds_m': bounds,
            'coverage': 'exact authored boundaries, disjoint material caps and actual closed mesh'}
