"""Check complete pocket topology on source or actual delivered coordinates.

Logical identities and the cap axis come from the rebuilt source recipe.
Artifact metadata cannot define that expected layout or authorize geometry.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import math

from .holes_delivery import _allowed_intersection, _cross, _dot, _sub
from .reach_numeric import MAX_OPERAND_BITS
from .surface import SurfaceError, _key, _number


MAX_POCKETS = 8
MAX_VERTICES = 64
MAX_CORNERS = 756


def _failure(code, message, **details):
    raise SurfaceError(code, message, details=details)


def _sequence(value, maximum, code, label):
    if type(value) not in (list, tuple):
        _failure(code, label + ' must be a bounded sequence.')
    raw = tuple(value[:maximum + 1])
    if len(raw) > maximum:
        _failure(code, label + ' exceeds its pocket geometry bound.')
    return raw


def _snapshot(ids, positions, normals, boundary_vertex_keys, cap_axis, code):
    ids = _sequence(ids, MAX_CORNERS, code, 'Corner identities')
    positions = _sequence(positions, MAX_CORNERS, code, 'Corner positions')
    if not 24 <= len(ids) <= MAX_CORNERS or len(ids) % 3 or len(positions) != len(ids):
        _failure(code, 'Corner counts must match a complete bounded pocket mesh.')
    copied_ids, copied_positions = [], []
    for identity, position in zip(ids, positions):
        identity = _sequence(identity, 4, code, 'Logical identity')
        position = _sequence(position, 3, code, 'Corner position')
        if len(identity) != 4 or len(position) != 3:
            _failure(code, 'Each logical identity needs four components and each position three.')
        copied_ids.append(identity)
        copied_positions.append(position)
    copied_normals = None
    if normals is not None:
        raw = _sequence(normals, MAX_CORNERS, code, 'Corner normals')
        if len(raw) != len(ids):
            _failure(code, 'Normal counts must match the complete corner array.')
        copied_normals = []
        for normal in raw:
            normal = _sequence(normal, 3, code, 'Corner normal')
            if len(normal) != 3:
                _failure(code, 'Every normal needs three components.')
            copied_normals.append(normal)
        copied_normals = tuple(copied_normals)
    raw = _sequence(boundary_vertex_keys, MAX_POCKETS + 1, code, 'Source boundaries')
    if not raw:
        _failure(code, 'A pocket mesh needs its complete exterior boundary.')
    boundaries, total = [], 0
    for boundary in raw:
        boundary = _sequence(boundary, 3, code, 'Source boundary')
        if len(boundary) != 3:
            _failure(code, 'A source boundary needs its kind, key and vertex keys.')
        keys = _sequence(boundary[2], MAX_VERTICES, code, 'Boundary vertex keys')
        total += len(keys)
        if len(keys) < 3 or total > MAX_VERTICES:
            _failure(code, 'Every source boundary needs three vertices, with at most 64 in total.')
        boundaries.append((boundary[0], boundary[1], keys))
    axis = _sequence(cap_axis, 3, code, 'Source cap axis')
    if len(axis) != 3:
        _failure(code, 'The source cap axis needs three components.')
    return tuple(copied_ids), tuple(copied_positions), copied_normals, tuple(boundaries), axis


def _exact_axis(raw, code, tick):
    axis = []
    for value in raw:
        tick()
        if type(value) not in (int, float, Fraction) or type(value) is float and not math.isfinite(value):
            _failure(code, 'Source cap axes require finite native exact numeric leaves.')
        if type(value) is int and value.bit_length() > MAX_OPERAND_BITS:
            raise SurfaceError('OKL-E-RESOURCE', 'Source cap axis exceeds the unchanged operand bound.')
        if type(value) is Fraction and max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_OPERAND_BITS:
            raise SurfaceError('OKL-E-RESOURCE', 'Source cap axis exceeds the unchanged operand bound.')
        exact = Fraction(value)
        axis.append(exact)
    if not any(axis):
        _failure(code, 'The source cap axis cannot be zero.')
    return tuple(axis)


def _layout(boundaries, corner_count, code, tick):
    expected, counts, seen = set(), {}, set()
    for index, (kind, key, keys) in enumerate(boundaries):
        tick()
        if index == 0:
            if (kind, key) != ('outer', 'outer'):
                _failure(code, 'The first logical boundary must be the exterior namespace.')
        elif kind != 'pocket':
            _failure(code, 'Every later logical boundary must be a pocket namespace.')
        _key(key, code, 'boundary key')
        identity = (kind, key)
        if identity in seen:
            _failure(code, 'Source boundary identities must be unique.')
        seen.add(identity)
        vertex_keys = set()
        for vertex in keys:
            tick()
            _key(vertex, code, 'vertex key')
            if vertex in vertex_keys:
                _failure(code, 'Source vertex keys must be unique within their boundary.')
            vertex_keys.add(vertex)
            expected.add((kind, key, vertex, 'lower'))
            expected.add((kind, key, vertex, 'top'))
        counts[identity] = len(keys)
    required = 6 * len(expected) - 12
    if corner_count != required:
        _failure(code, 'The complete corner count must match all source boundary identities.',
                 required=required, actual=corner_count)
    return expected, counts


def _validate_pockets_mesh(corner_vertex_ids, positions, *, boundary_vertex_keys,
                           cap_axis, normals=None, check=None,
                           code='OKL-E-POCKETS-NUMERIC'):
    def tick():
        if check is not None:
            check()

    ids, raw_points, raw_normals, boundaries, raw_axis = _snapshot(
        corner_vertex_ids, positions, normals, boundary_vertex_keys, cap_axis, code)
    tick()
    expected, boundary_counts = _layout(boundaries, len(ids), code, tick)
    axis = _exact_axis(raw_axis, code, tick)
    vertices, geometric_ids = {}, {}
    exact_normals = [] if raw_normals is not None else None
    for index, (identity, raw) in enumerate(zip(ids, raw_points)):
        tick()
        if not all(type(value) is str for value in identity) or identity not in expected:
            _failure(code, 'A supplied corner identity is absent from the complete source layout.',
                     corner=index)
        point = tuple(Fraction(_number(value, code, 'coordinate')) for value in raw)
        if identity in vertices and vertices[identity] != point:
            _failure(code, 'Repeated logical corners must retain identical positions.',
                     vertex_id=list(identity))
        other = geometric_ids.get(point)
        if other is not None and other != identity:
            _failure(code, 'Distinct logical vertices collapse to one position.',
                     vertex_id=list(identity), other_vertex_id=list(other))
        vertices[identity] = point
        geometric_ids[point] = identity
        if raw_normals is not None:
            normal = tuple(_number(value, code, 'normal') for value in raw_normals[index])
            if abs(math.hypot(*normal) - 1.0) > 1e-5:
                _failure(code, 'Supplied corner normals must retain unit length.', corner=index)
            exact_normals.append(tuple(Fraction(value) for value in normal))
    if set(vertices) != expected:
        _failure(code, 'Supplied corners must retain the complete source vertex inventory.')
    triangles, triangle_ids, edges = [], [], Counter()
    caps, walls = Counter(), Counter()
    volume6 = Fraction(0)
    for start in range(0, len(ids), 3):
        tick()
        identity = ids[start:start + 3]
        if len(set(identity)) != 3:
            _failure(code, 'Every face needs three distinct logical source vertices.', triangle=start // 3)
        points = tuple(vertices[key] for key in identity)
        normal = _cross(_sub(points[1], points[0]), _sub(points[2], points[0]))
        if not any(normal):
            _failure(code, 'Every face must retain nonzero exact area.', triangle=start // 3)
        if exact_normals is not None:
            for supplied in exact_normals[start:start + 3]:
                tick()
                if _dot(normal, supplied) <= 0:
                    _failure(code, 'Supplied normals disagree with actual face winding.', triangle=start // 3)
        levels = {value[3] for value in identity}
        face_boundaries = {value[:2] for value in identity}
        if levels == {'top'}:
            caps['top'] += 1
            if _dot(normal, axis) <= 0:
                _failure(code, 'A top triangle must face the placed positive Z axis.', triangle=start // 3)
        elif levels == {'lower'} and len(face_boundaries) == 1:
            boundary = next(iter(face_boundaries))
            caps[boundary] += 1
            facing = _dot(normal, axis)
            if (boundary[0] == 'outer' and facing >= 0) or (boundary[0] == 'pocket' and facing <= 0):
                _failure(code, 'The exterior bottom faces down and each blind floor faces up.',
                         triangle=start // 3)
        elif levels == {'lower', 'top'} and len(face_boundaries) == 1:
            walls[next(iter(face_boundaries))] += 1
        else:
            _failure(code, 'A supplied face crosses unrelated pocket boundary domains.', triangle=start // 3)
        bounds = (tuple(min(point[component] for point in points) for component in range(3)),
                  tuple(max(point[component] for point in points) for component in range(3)))
        triangles.append((points, normal, bounds))
        triangle_ids.append(identity)
        volume6 += _dot(points[0], _cross(points[1], points[2]))
        for index in range(3):
            edges[identity[index], identity[(index + 1) % 3]] += 1
    for boundary, count in boundary_counts.items():
        tick()
        if caps[boundary] != count - 2 or walls[boundary] != 2 * count:
            _failure(code, 'Every exterior/pocket boundary must retain its complete cap and walls.',
                     boundary=list(boundary))
    top_required = sum(boundary_counts.values()) + 2 * (len(boundary_counts) - 1) - 2
    if caps['top'] != top_required:
        _failure(code, 'The perforated top must retain its complete source triangle count.')
    for (a, b), count in edges.items():
        tick()
        if count != 1 or edges[b, a] != 1:
            _failure(code, 'The mesh must retain closed oppositely directed edge incidence.',
                     edge=[list(a), list(b)], count=count, opposite_count=edges[b, a])
    if volume6 <= 0:
        _failure(code, 'The complete oriented pocket mesh must retain positive exact signed volume.')
    for first_index, first in enumerate(triangles):
        for second_index in range(first_index + 1, len(triangles)):
            tick()
            shared = set(triangle_ids[first_index]).intersection(triangle_ids[second_index])
            if len(shared) == 3:
                _failure(code, 'Distinct faces cannot duplicate one source triangle.',
                         first=first_index, second=second_index)
            shared_points = tuple(vertices[key] for key in sorted(shared))
            if not _allowed_intersection(first, triangles[second_index], shared_points, tick):
                _failure(code, 'Faces meet beyond their explicitly shared source vertex or edge.',
                         first=first_index, second=second_index)


def validate_pockets_delivery(corner_vertex_ids, positions, *, boundary_vertex_keys,
                              cap_axis, normals=None, check=None):
    """Validate actual supplied coordinates against source-owned identities."""
    _validate_pockets_mesh(corner_vertex_ids, positions,
                          boundary_vertex_keys=boundary_vertex_keys,
                          cap_axis=cap_axis, normals=normals, check=check)


def placed_pockets_axis(rotation, *, check=None):
    """Keep the scene adapter entry point beside supplied-coordinate checks."""
    from .pockets import placed_pockets_axis as source_axis
    return source_axis(rotation, check=check)
