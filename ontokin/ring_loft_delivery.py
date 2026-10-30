"""Exact source-identity and supplied-position checks for polygon ring lofts.

Positions may be source binary64 coordinates or the actual placed binary32
coordinates. No planarity assumption is made about rounded endpoint caps.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
import math

from .holes_delivery import _allowed_intersection, _cross, _dot, _sub
from .surface import SurfaceError, _key, _number


MAX_SECTIONS = 8
MAX_SECTION_VERTICES = 64
MAX_AUTHORED_VERTICES = 256
MAX_RINGS = 9
MAX_CORNERS = 1620


def _failure(code, message, **details):
    raise SurfaceError(code, message, details=details)


def _sequence(value, maximum, code, label):
    if type(value) not in (list, tuple):
        _failure(code, label + ' must be a bounded sequence.')
    captured = tuple(value[:maximum + 1])
    if len(captured) > maximum:
        _failure(code, label + ' exceeds the ring loft bound.')
    return captured


def _snapshot(corner_vertex_ids, positions, normals, code):
    """Capture every host-owned leaf before subsequent work callbacks."""
    ids = _sequence(corner_vertex_ids, MAX_CORNERS, code, 'Corner identities')
    points = _sequence(positions, MAX_CORNERS, code, 'Corner positions')
    if not 24 <= len(ids) <= MAX_CORNERS or len(ids) % 3 or len(points) != len(ids):
        _failure(code, 'Corner identities and positions must match a complete bounded ring loft.')
    copied_ids, copied_points = [], []
    for identity, point in zip(ids, points):
        identity = _sequence(identity, 3, code, 'Source vertex identity')
        point = _sequence(point, 3, code, 'Corner position')
        if len(identity) != 3 or len(point) != 3:
            _failure(code, 'Source identities and positions each require exactly three components.')
        copied_ids.append(identity)
        copied_points.append(point)
    copied_normals = None
    if normals is not None:
        raw_normals = _sequence(normals, MAX_CORNERS, code, 'Corner normals')
        if len(raw_normals) != len(ids):
            _failure(code, 'Supplied normal counts must match the complete corner array.')
        captured = []
        for normal in raw_normals:
            normal = _sequence(normal, 3, code, 'Corner normal')
            if len(normal) != 3:
                _failure(code, 'Every supplied normal requires three components.')
            captured.append(normal)
        copied_normals = tuple(captured)
    return tuple(copied_ids), tuple(copied_points), copied_normals


def _matched_identity_layout(vertices, corner_count, code, tick):
    """Verify finite complete layers without trusting artifact metadata."""
    sections = {}
    for section, ring, vertex in vertices:
        tick()
        sections.setdefault(section, {}).setdefault(ring, set()).add(vertex)
    if not 2 <= len(sections) <= MAX_SECTIONS or not 6 <= len(vertices) <= MAX_AUTHORED_VERTICES:
        _failure(code, 'Source identities must retain 2 through 8 complete matched sections.')
    first = next(iter(sections.values()))
    count = sum(len(value) for value in first.values())
    if not 1 <= len(first) <= MAX_RINGS or not 3 <= count <= MAX_SECTION_VERTICES:
        _failure(code, 'Every section must retain its bounded rings and vertices.')
    for rings in sections.values():
        tick()
        if rings != first or any(len(value) < 3 for value in rings.values()):
            _failure(code, 'All delivered sections must retain the same complete ring/vertex identities.')
    required = 3 * (2 * len(sections) * count + 4 * (len(first) - 1) - 4)
    if corner_count != required:
        _failure(code, 'The supplied corner count must match its complete matched-section topology.',
                 required=required, actual=corner_count)


def _validate_ring_loft_mesh(corner_vertex_ids, positions, *, normals=None,
                             check=None, code='OKL-E-RING-LOFT-NUMERIC'):
    def tick():
        if check is not None:
            check()

    tick()
    ids, raw_points, raw_normals = _snapshot(corner_vertex_ids, positions, normals, code)
    vertices, geometric_ids = {}, {}
    exact_normals = [] if raw_normals is not None else None
    for index, (identity, raw) in enumerate(zip(ids, raw_points)):
        tick()
        for component, label in zip(identity, ('section key', 'ring key', 'vertex key')):
            _key(component, code, label)
        point = tuple(Fraction(_number(value, code, 'coordinate')) for value in raw)
        if identity in vertices and vertices[identity] != point:
            _failure(code, 'Repeated source corners must retain identical positions.',
                     vertex_id=list(identity))
        other = geometric_ids.get(point)
        if other is not None and other != identity:
            _failure(code, 'Distinct source vertices cannot collapse to one position.',
                     vertex_id=list(identity), other_vertex_id=list(other))
        vertices[identity] = point
        geometric_ids[point] = identity
        if raw_normals is not None:
            normal = tuple(_number(value, code, 'normal') for value in raw_normals[index])
            if abs(math.hypot(*normal) - 1.0) > 1e-5:
                _failure(code, 'Supplied corner normals must have finite unit length.', corner=index)
            exact_normals.append(tuple(Fraction(value) for value in normal))
    _matched_identity_layout(vertices, len(ids), code, tick)
    triangles, triangle_ids, edges = [], [], Counter()
    volume6 = Fraction(0)
    for start in range(0, len(ids), 3):
        tick()
        identity = ids[start:start + 3]
        if len(set(identity)) != 3:
            _failure(code, 'Every triangle needs three distinct source vertices.', triangle=start // 3)
        points = tuple(vertices[key] for key in identity)
        normal = _cross(_sub(points[1], points[0]), _sub(points[2], points[0]))
        if not any(normal):
            _failure(code, 'Every triangle must retain nonzero exact area.', triangle=start // 3)
        if exact_normals is not None:
            for supplied in exact_normals[start:start + 3]:
                tick()
                if _dot(normal, supplied) <= 0:
                    _failure(code, 'Supplied normals must agree with exact face winding.',
                             triangle=start // 3)
        bounds = (tuple(min(point[axis] for point in points) for axis in range(3)),
                  tuple(max(point[axis] for point in points) for axis in range(3)))
        triangles.append((points, normal, bounds))
        triangle_ids.append(identity)
        volume6 += _dot(points[0], _cross(points[1], points[2]))
        for i in range(3):
            edges[identity[i], identity[(i + 1) % 3]] += 1
    for (a, b), count in edges.items():
        tick()
        if count != 1 or edges[b, a] != 1:
            _failure(code, 'The mesh must have closed, oppositely oriented edge incidence.',
                     edge=[list(a), list(b)], count=count, opposite_count=edges[b, a])
    if volume6 <= 0:
        _failure(code, 'The closed oriented mesh must retain positive exact signed volume.')
    for i, first in enumerate(triangles):
        for j in range(i + 1, len(triangles)):
            tick()
            shared = set(triangle_ids[i]).intersection(triangle_ids[j])
            if len(shared) == 3:
                _failure(code, 'Distinct faces cannot duplicate one source triangle.', first=i, second=j)
            shared_points = tuple(vertices[key] for key in sorted(shared))
            if not _allowed_intersection(first, triangles[j], shared_points, tick):
                _failure(code, 'Faces intersect beyond their explicitly shared source boundary.',
                         first=i, second=j)


def validate_ring_loft_delivery(corner_vertex_ids, delivered_positions, *, normals=None, check=None):
    """Check the actual supplied positions and optional decoded flat normals.

    Source identities come from the independently rebuilt recipe, never from
    artifact metadata. The caller separately binds source-quantized positions,
    normal values, regional membership, placement and recorded motion.
    """
    _validate_ring_loft_mesh(corner_vertex_ids, delivered_positions,
                             normals=normals, check=check)
