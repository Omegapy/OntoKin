"""Bounded source polygon triangulation for the explicit extrusion profile.

Predicates use exact rational values of canonical binary64 coordinates. Mesh
corners are flat shaded visual data and carry no physical or motion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from .surface import (SurfaceError, SurfaceMaterial, RegionTriangles,
                      MAX_MESH_VERTICES, _check_materials, _key, _number)

MAX_VERTICES = 64
MAX_ORDER = 65535
MAX_COORDINATE_ABS_M = 100.0
MIN_DEPTH_M = 0.001
MAX_DEPTH_M = 100.0


@dataclass(frozen=True)
class PolygonVertex:
    key: str
    order: int
    point_m: tuple[float, float]
    region: str


@dataclass(frozen=True)
class ExtrusionMesh:
    vertex_keys: tuple[str, ...]
    positions: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    regions: tuple[RegionTriangles, ...]
    depth_m: float

    @property
    def triangle_count(self):
        return sum(len(region.indices) // 3 for region in self.regions)


def _error(suffix, message, **details):
    raise SurfaceError('OKL-E-EXTRUSION-' + suffix, message, details=details)


def _turn(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, p):
    return (_turn(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def _intersects(a, b, c, d):
    turns = _turn(a, b, c), _turn(a, b, d), _turn(c, d, a), _turn(c, d, b)
    if any(value == 0 for value in turns):
        return (_on_segment(a, b, c) or _on_segment(a, b, d)
                or _on_segment(c, d, a) or _on_segment(c, d, b))
    return (turns[0] > 0) != (turns[1] > 0) and (turns[2] > 0) != (turns[3] > 0)


def triangulate_extrusion(vertices, materials, depth_m, bottom_region, top_region,
                          *, max_vertices=MAX_MESH_VERTICES, check=None):
    """Validate an ordered simple outline and emit deterministic rigid faces."""
    def tick():
        if check is not None:
            check()

    tick()
    if type(vertices) not in (list, tuple) or not 3 <= len(vertices) <= MAX_VERTICES:
        _error('VERTEX', 'An extrusion requires 3 through 64 polygon vertices.')
    # Callbacks can mutate a host-owned list after its length was checked
    # Retain its bounded membership before any later cooperative checkpoint
    vertices = tuple(vertices)
    if type(max_vertices) is not int or not 0 <= max_vertices <= MAX_MESH_VERTICES:
        raise SurfaceError('OKL-E-RESOURCE', 'Invalid remaining vertex budget.',
                           details={'budget': max_vertices})
    required = 12 * len(vertices) - 12
    if required > max_vertices:
        raise SurfaceError('OKL-E-RESOURCE', 'Extrusion exceeds the remaining mesh vertex budget.',
                           details={'required': required, 'available': max_vertices})
    depth = _number(depth_m, 'OKL-E-EXTRUSION-DEPTH', 'depth')
    if not MIN_DEPTH_M <= depth <= MAX_DEPTH_M:
        _error('DEPTH', 'Extrusion depth must lie in [0.001,100] meters.', depth_m=depth)
    if type(materials) not in (list, tuple) or not 1 <= len(materials) <= 16:
        raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'An extrusion requires 1 through 16 materials.')
    materials = tuple(materials)
    for material in materials:
        tick()
    palette = _check_materials(materials)
    for label, region in (('bottom', bottom_region), ('top', top_region)):
        tick()
        _key(region, 'OKL-E-EXTRUSION-REGION', label + ' region')
        if region not in palette:
            _error('REGION', 'A cap region is absent from the palette.', cap=label, region=region)
    keys, orders, points, checked = set(), set(), set(), []
    for vertex in vertices:
        tick()
        if not isinstance(vertex, PolygonVertex):
            _error('VERTEX', 'Expected a PolygonVertex value.')
        key = _key(vertex.key, 'OKL-E-EXTRUSION-VERTEX', 'vertex key')
        if key in keys:
            _error('VERTEX', 'Duplicate authored polygon vertex key.', key=key)
        keys.add(key)
        order = vertex.order
        if type(order) is not int or not 0 <= order <= MAX_ORDER or order in orders:
            _error('ORDER', 'Vertex orders must be unique integers from 0 through 65535.',
                   key=key, order=order)
        orders.add(order)
        if not isinstance(vertex.point_m, (list, tuple)) or len(vertex.point_m) != 2:
            _error('POINT', 'A planar point requires exactly two coordinates.', key=key)
        point = tuple(_number(c, 'OKL-E-EXTRUSION-POINT', 'coordinate') for c in vertex.point_m)
        if any(abs(c) > MAX_COORDINATE_ABS_M for c in point):
            _error('POINT', 'Planar coordinates must lie within [-100,100] meters.', key=key)
        if point in points:
            _error('TOPOLOGY', 'Polygon positions must be distinct; the closing edge is implicit.', key=key)
        points.add(point)
        region = _key(vertex.region, 'OKL-E-EXTRUSION-REGION', 'side region')
        if region not in palette:
            _error('REGION', 'A side region is absent from the palette.', key=key, region=region)
        checked.append(PolygonVertex(key, order, point, region))
    ordered = sorted(checked, key=lambda vertex: vertex.order)
    exact = []
    for vertex in ordered:
        tick()
        exact.append(tuple(Fraction(c) for c in vertex.point_m))
    count = len(ordered)
    for i, a in enumerate(exact):
        tick()
        if _turn(exact[i-1], a, exact[(i+1) % count]) == 0:
            _error('TOPOLOGY', 'Adjacent polygon vertices cannot be collinear.', key=ordered[i].key)
        b = exact[(i+1) % count]
        for j in range(i+1, count):
            tick()
            if j == i+1 or i == 0 and j == count-1:
                continue
            if _intersects(a, b, exact[j], exact[(j+1) % count]):
                _error('TOPOLOGY', 'Nonadjacent polygon edges cannot cross, touch or overlap.',
                       edge_start=ordered[i].key, other_edge_start=ordered[j].key)
    area2 = Fraction(0)
    for i, a in enumerate(exact):
        tick()
        b = exact[(i+1) % count]
        area2 += a[0] * b[1] - a[1] * b[0]
    if area2 == 0:
        _error('TOPOLOGY', 'The polygon must have nonzero signed area.')
    if area2 < 0:
        _error('WINDING', 'The polygon must traverse counterclockwise as viewed from +Z.')
    retained = list(range(count))
    caps = []
    while len(retained) > 3:
        found = False
        for i, current in enumerate(retained):
            tick()
            previous, following = retained[i-1], retained[(i+1) % len(retained)]
            a, b, c = exact[previous], exact[current], exact[following]
            if _turn(a, b, c) <= 0:
                continue
            obstructed = False
            for candidate in retained:
                tick()
                if candidate in (previous, current, following):
                    continue
                p = exact[candidate]
                if _turn(a, b, p) >= 0 and _turn(b, c, p) >= 0 and _turn(c, a, p) >= 0:
                    obstructed = True
                    break
            if not obstructed:
                caps.append((previous, current, following))
                del retained[i]
                found = True
                break
        if not found:
            _error('TOPOLOGY', 'The simple polygon has no admissible nondegenerate ear.')
    tick()
    if _turn(*(exact[i] for i in retained)) <= 0:
        _error('TOPOLOGY', 'The final cap triangle must have positive area.')
    caps.append(tuple(retained))
    lower, upper = [], []
    for vertex in ordered:
        tick()
        x, y = vertex.point_m
        lower.append((x, y, 0.0))
        upper.append((x, y, depth))
    positions, normals = [], []
    groups = {key: [] for key in palette}

    def emit(a, b, c, normal, region):
        tick()
        u, v = tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3))
        cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        facing = sum(x*y for x,y in zip(cross, normal))
        if (not math.isfinite(facing) or facing <= 0 or
                not all(math.isfinite(value) for value in normal) or
                abs(math.hypot(*normal)-1.0) > 1e-12):
            _error('NUMERIC', 'A nonzero outward triangle and unit normal must remain representable.')
        start = len(positions)
        positions.extend((a,b,c))
        normals.extend((normal,normal,normal))
        groups[region].extend((start,start+1,start+2))

    for a,b,c in caps:
        emit(lower[c],lower[b],lower[a],(0.0,0.0,-1.0),bottom_region)
    for a,b,c in caps:
        emit(upper[a],upper[b],upper[c],(0.0,0.0,1.0),top_region)
    for i, vertex in enumerate(ordered):
        tick()
        j = (i+1) % count
        dx, dy = lower[j][0]-lower[i][0], lower[j][1]-lower[i][1]
        length = math.hypot(dx,dy)
        if not math.isfinite(length) or length <= 0:
            _error('NUMERIC', 'A side edge must have a representable nonzero length.', key=vertex.key)
        normal = (dy/length,-dx/length,0.0)
        emit(lower[i],lower[j],upper[i],normal,vertex.region)
        emit(lower[j],upper[j],upper[i],normal,vertex.region)
    regions = []
    for key in sorted(groups):
        tick()
        if groups[key]:
            regions.append(RegionTriangles(key,palette[key],tuple(groups[key])))
    return ExtrusionMesh(tuple(v.key for v in ordered), tuple(positions), tuple(normals),
                         tuple(regions), depth)
