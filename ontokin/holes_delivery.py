"""Exact intersection checks for placed, supplied polygon-hole mesh positions.

The caller supplies final decoded positions and the source corner identities.
This check does not assume that binary32 conversion leaves a cap coplanar.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction

from .surface import SurfaceError, _number


MAX_BOUNDARY_VERTICES = 64
MAX_CORNERS = 12 * MAX_BOUNDARY_VERTICES + 12 * 8 - 12


def _failure(message, **details):
    raise SurfaceError('OKL-E-HOLES-NUMERIC', message, details=details)


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _turn(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, point):
    return (_turn(a, b, point) == 0 and
            min(a[0], b[0]) <= point[0] <= max(a[0], b[0]) and
            min(a[1], b[1]) <= point[1] <= max(a[1], b[1]))


def _section(points, distances, tick):
    """Intersect a noncoplanar triangle with a plane using exact coordinates."""
    result = set()
    for i, a in enumerate(points):
        tick()
        j = (i + 1) % 3
        da, db = distances[i], distances[j]
        if da == 0:
            result.add(a)
        if da * db < 0:
            b = points[j]
            result.add(tuple((da * b[k] - db * a[k]) / (da - db) for k in range(3)))
    return tuple(result)


def _clip(first, second, tick):
    """Return the exact closed intersection of two projected triangles."""
    if _turn(*second) < 0:
        second = (second[0], second[2], second[1])
    polygon = list(first)
    for i, a in enumerate(second):
        tick()
        if not polygon:
            break
        b, output = second[(i + 1) % 3], []
        previous = polygon[-1]
        previous_side = _turn(a, b, previous)
        for current in polygon:
            tick()
            current_side = _turn(a, b, current)
            if (current_side >= 0) != (previous_side >= 0):
                fraction = previous_side / (previous_side - current_side)
                point = tuple(previous[k] + fraction * (current[k] - previous[k]) for k in range(2))
                if not output or output[-1] != point:
                    output.append(point)
            if current_side >= 0 and (not output or output[-1] != current):
                output.append(current)
            previous, previous_side = current, current_side
        if len(output) > 1 and output[-1] == output[0]:
            output.pop()
        polygon = output
    return polygon


def _one_side(distances):
    return all(value > 0 for value in distances) or all(value < 0 for value in distances)


def _allowed_intersection(first, second, shared_points, tick):
    """Return whether two triangles meet only at their source-shared simplex."""
    a, normal_a, bounds_a = first
    b, normal_b, bounds_b = second
    if any(bounds_a[1][axis] < bounds_b[0][axis] or
           bounds_b[1][axis] < bounds_a[0][axis] for axis in range(3)):
        return True
    da = tuple(_dot(normal_b, _sub(point, b[0])) for point in a)
    db = tuple(_dot(normal_a, _sub(point, a[0])) for point in b)
    if _one_side(da) or _one_side(db):
        return True
    line = _cross(normal_a, normal_b)
    if any(line):
        cut_a, cut_b = _section(a, da, tick), _section(b, db, tick)
        if not cut_a or not cut_b:
            return True
        axis = max(range(3), key=lambda index: abs(line[index]))
        low = max(min(point[axis] for point in cut_a), min(point[axis] for point in cut_b))
        high = min(max(point[axis] for point in cut_a), max(point[axis] for point in cut_b))
        if low > high:
            return True
        if len(shared_points) == 1:
            return low == high == shared_points[0][axis]
        if len(shared_points) == 2:
            return (low == min(point[axis] for point in shared_points) and
                    high == max(point[axis] for point in shared_points))
        return False
    if any(db):
        return True
    axis = max(range(3), key=lambda index: abs(normal_a[index]))
    def project(point):
        return tuple(value for index, value in enumerate(point) if index != axis)
    intersection = _clip(tuple(map(project, a)), tuple(map(project, b)), tick)
    if not intersection:
        return True
    shared = tuple(map(project, shared_points))
    for point in intersection:
        tick()
        if len(shared) == 1 and point == shared[0]:
            continue
        if len(shared) == 2 and _on_segment(shared[0], shared[1], point):
            continue
        return False
    return True


def validate_holes_delivery(corner_vertex_ids, delivered_positions, *, check=None):
    """Reject collapsed or self-intersecting supplied meshes after placement.

    Repeated corners refer to the same source vertex by identity. Different
    source vertices must remain different, even if their coordinates are close.
    The existing destination reader separately validates outward normals,
    exact source-quantized positions, regions and geometric error bounds.
    """
    def tick():
        if check is not None:
            check()

    tick()
    if type(corner_vertex_ids) not in (list, tuple) or type(delivered_positions) not in (list, tuple):
        _failure('Delivered corner identities and positions must be bounded sequences.')
    ids = tuple(corner_vertex_ids[:MAX_CORNERS + 1])
    raw = tuple(delivered_positions[:MAX_CORNERS + 1])
    if not 24 <= len(ids) <= MAX_CORNERS or len(ids) % 3 or len(raw) != len(ids):
        _failure('Delivered corner counts must match the bounded ring mesh.')
    positions = []
    for point in raw:
        if type(point) not in (list, tuple):
            _failure('Delivered positions must have three finite coordinates.')
        point = tuple(point[:4])
        if len(point) != 3:
            _failure('Delivered positions must have three finite coordinates.')
        positions.append(tuple(_number(value, 'OKL-E-HOLES-NUMERIC', 'delivered coordinate') for value in point))
    positions = tuple(positions)
    vertices, geometric_ids = {}, {}
    for identity, position in zip(ids, positions):
        tick()
        if type(identity) is not int or not 0 <= identity < 2 * MAX_BOUNDARY_VERTICES:
            _failure('Delivered source vertex identities must be bounded integers.')
        point = tuple(Fraction(value) for value in position)
        if identity in vertices and vertices[identity] != point:
            _failure('Repeated source corners must retain identical delivered positions.', vertex_id=identity)
        other = geometric_ids.get(point)
        if other is not None and other != identity:
            _failure('Distinct source boundary vertices collapse after delivery.',
                     vertex_id=identity, other_vertex_id=other)
        vertices[identity] = point
        geometric_ids[point] = identity
    if set(vertices) != set(range(len(vertices))) or len(vertices) < 6 or len(vertices) % 2:
        _failure('Delivered source vertex identities must retain both complete boundary layers.')
    triangles, triangle_ids, edges = [], [], Counter()
    for start in range(0, len(ids), 3):
        tick()
        identity = ids[start:start + 3]
        if len(set(identity)) != 3:
            _failure('A delivered triangle must have three distinct source vertices.', triangle=start // 3)
        points = tuple(vertices[index] for index in identity)
        normal = _cross(_sub(points[1], points[0]), _sub(points[2], points[0]))
        if not any(normal):
            _failure('A delivered triangle must retain nonzero area.', triangle=start // 3)
        bounds = (tuple(min(point[axis] for point in points) for axis in range(3)),
                  tuple(max(point[axis] for point in points) for axis in range(3)))
        triangles.append((points, normal, bounds))
        triangle_ids.append(identity)
        for i in range(3):
            edges[identity[i], identity[(i + 1) % 3]] += 1
    for (a, b), count in edges.items():
        tick()
        if count != 1 or edges[b, a] != 1:
            _failure('Delivered triangles must retain closed, oppositely oriented edge incidence.',
                     edge=[a, b], count=count, opposite_count=edges[b, a])
    for i, first in enumerate(triangles):
        for j in range(i + 1, len(triangles)):
            tick()
            shared = set(triangle_ids[i]).intersection(triangle_ids[j])
            if len(shared) == 3:
                _failure('Distinct delivered faces cannot duplicate one source triangle.', first=i, second=j)
            shared_points = tuple(vertices[index] for index in sorted(shared))
            if not _allowed_intersection(first, triangles[j], shared_points, tick):
                _failure('Delivered faces intersect beyond their shared source boundary.', first=i, second=j)
