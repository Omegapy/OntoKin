"""Bounded exact ring topology and triangulation for polygon-holes-0.1.

All authored coordinates remain canonical binary64 values. Exact predicates
select a planar graph; emitted triangles remain ordinary rigid visual data.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import cmp_to_key
import math

from .extrusion import PolygonVertex, _intersects, _on_segment, _turn
from .surface import (MAX_MESH_VERTICES, RegionTriangles, SurfaceError,
                      SurfaceMaterial, _check_materials, _key, _number)


MAX_HOLES = 8
MAX_RINGS = MAX_HOLES + 1
MAX_VERTICES = 64
MAX_ORDER = 65535
MAX_COORDINATE_ABS_M = 100.0
MIN_DEPTH_M = 0.001
MAX_DEPTH_M = 100.0


@dataclass(frozen=True)
class PolygonRing:
    key: str
    order: int
    role: str
    vertices: tuple[PolygonVertex, ...]


@dataclass(frozen=True)
class HolesMesh:
    ring_keys: tuple[str, ...]
    vertex_keys: tuple[tuple[str, str], ...]
    positions: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    regions: tuple[RegionTriangles, ...]
    depth_m: float
    corner_vertex_ids: tuple[int, ...]

    @property
    def triangle_count(self):
        return sum(len(region.indices) // 3 for region in self.regions)


def _error(suffix, message, **details):
    raise SurfaceError('OKL-E-HOLES-' + suffix, message, details=details)


def _sequence(value, minimum, maximum, suffix, message):
    if type(value) not in (list, tuple):
        _error(suffix, message)
    # The slice bounds allocation even if a caller-owned list was enlarged
    captured = tuple(value[:maximum + 1])
    if not minimum <= len(captured) <= maximum:
        _error(suffix, message)
    return captured


def _snapshot(rings, materials):
    """Copy bounded leaves before any later callback can mutate host values."""
    raw_rings = _sequence(rings, 1, MAX_RINGS, 'RING',
                          'A ring extrusion requires 1 through 9 rings.')
    copied, total = [], 0
    for ring in raw_rings:
        if type(ring) is not PolygonRing:
            _error('RING', 'Expected a PolygonRing value.')
        vertices = _sequence(ring.vertices, 3, MAX_VERTICES, 'VERTEX',
                             'Every ring requires at least three vertices, with at most 64 in total.')
        total += len(vertices)
        if total > MAX_VERTICES:
            _error('VERTEX', 'All rings together may contain at most 64 vertices.')
        leaves = []
        for vertex in vertices:
            if type(vertex) is not PolygonVertex:
                _error('VERTEX', 'Expected a PolygonVertex value.', ring=ring.key)
            point = _sequence(vertex.point_m, 2, 2, 'POINT',
                              'A planar point requires exactly two coordinates.')
            leaves.append(PolygonVertex(vertex.key, vertex.order, point, vertex.region))
        copied.append(PolygonRing(ring.key, ring.order, ring.role, tuple(leaves)))
    if type(materials) not in (list, tuple):
        raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'A ring extrusion requires 1 through 16 materials.')
    raw_materials = tuple(materials[:17])
    if not 1 <= len(raw_materials) <= 16:
        raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'A ring extrusion requires 1 through 16 materials.')
    palette = []
    for material in raw_materials:
        if type(material) is not SurfaceMaterial:
            raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'Expected a SurfaceMaterial value.')
        if type(material.rgba) not in (list, tuple):
            raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'RGBA needs exactly four channels.')
        rgba = tuple(material.rgba[:5])
        if len(rgba) != 4:
            raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'RGBA needs exactly four channels.')
        palette.append(SurfaceMaterial(material.key, rgba, material.metallic, material.roughness))
    return tuple(copied), tuple(palette), total


def _containment(point, outline, tick):
    """Return 1 inside, 0 on the boundary, or -1 outside either ring winding."""
    winding = 0
    for index, a in enumerate(outline):
        tick()
        b = outline[(index + 1) % len(outline)]
        turn = _turn(a, b, point)
        if turn == 0 and _on_segment(a, b, point):
            return 0
        if a[1] <= point[1]:
            if b[1] > point[1] and turn > 0:
                winding += 1
        elif b[1] <= point[1] and turn < 0:
            winding -= 1
    return 1 if winding else -1


def _validated_rings(rings, palette, tick):
    keys, orders, checked = set(), set(), []
    outer_count = 0
    for ring in rings:
        tick()
        key = _key(ring.key, 'OKL-E-HOLES-RING', 'ring key')
        if key in keys:
            _error('RING', 'Ring keys must be unique.', ring=key)
        keys.add(key)
        if type(ring.order) is not int or not 0 <= ring.order <= MAX_ORDER or ring.order in orders:
            _error('ORDER', 'Ring orders must be unique integers from 0 through 65535.',
                   ring=key, order=ring.order)
        orders.add(ring.order)
        if type(ring.role) is not str or ring.role not in ('outer', 'hole'):
            _error('RING', 'A ring role must be exactly outer or hole.', ring=key)
        outer_count += ring.role == 'outer'
        vertex_keys, vertex_orders, points, vertices = set(), set(), set(), []
        for vertex in ring.vertices:
            tick()
            vkey = _key(vertex.key, 'OKL-E-HOLES-VERTEX', 'vertex key')
            if vkey in vertex_keys:
                _error('VERTEX', 'Vertex keys must be unique within a ring.', ring=key, vertex=vkey)
            vertex_keys.add(vkey)
            order = vertex.order
            if type(order) is not int or not 0 <= order <= MAX_ORDER or order in vertex_orders:
                _error('ORDER', 'Vertex orders must be unique integers from 0 through 65535 within a ring.',
                       ring=key, vertex=vkey, order=order)
            vertex_orders.add(order)
            point = tuple(_number(value, 'OKL-E-HOLES-POINT', 'coordinate') for value in vertex.point_m)
            if any(abs(value) > MAX_COORDINATE_ABS_M for value in point):
                _error('POINT', 'Planar coordinates must lie within [-100,100] meters.', ring=key, vertex=vkey)
            if point in points:
                _error('TOPOLOGY', 'Ring positions must be distinct; the closing edge is implicit.',
                       ring=key, vertex=vkey)
            points.add(point)
            region = _key(vertex.region, 'OKL-E-HOLES-REGION', 'wall region')
            if region not in palette:
                _error('REGION', 'A wall region is absent from the palette.',
                       ring=key, vertex=vkey, region=region)
            vertices.append(PolygonVertex(vkey, order, point, region))
        checked.append(PolygonRing(key, ring.order, ring.role,
                                   tuple(sorted(vertices, key=lambda value: value.order))))
    if outer_count != 1:
        _error('RING', 'A ring extrusion requires exactly one outer ring.', outer_count=outer_count)
    return tuple(sorted(checked, key=lambda value: value.order))


def _topology(rings, tick):
    exact_rings, area2 = [], Fraction(0)
    for ring in rings:
        exact = []
        for vertex in ring.vertices:
            tick()
            exact.append(tuple(Fraction(value) for value in vertex.point_m))
        count, signed = len(exact), Fraction(0)
        for i, a in enumerate(exact):
            tick()
            b = exact[(i + 1) % count]
            if _turn(exact[i - 1], a, b) == 0:
                _error('TOPOLOGY', 'Adjacent ring vertices cannot be collinear.',
                       ring=ring.key, vertex=ring.vertices[i].key)
            signed += a[0] * b[1] - a[1] * b[0]
            for j in range(i + 1, count):
                tick()
                if j == i + 1 or i == 0 and j == count - 1:
                    continue
                if _intersects(a, b, exact[j], exact[(j + 1) % count]):
                    _error('TOPOLOGY', 'Nonadjacent ring edges cannot cross, touch or overlap.',
                           ring=ring.key, edge_start=ring.vertices[i].key,
                           other_edge_start=ring.vertices[j].key)
        if signed == 0:
            _error('TOPOLOGY', 'A ring must have nonzero signed area.', ring=ring.key)
        if (signed > 0) != (ring.role == 'outer'):
            _error('WINDING', 'The outer ring must be counterclockwise and holes clockwise.', ring=ring.key)
        exact_rings.append(tuple(exact))
        area2 += signed
    for first in range(len(rings)):
        for second in range(first + 1, len(rings)):
            a_ring, b_ring = exact_rings[first], exact_rings[second]
            for i, a in enumerate(a_ring):
                for j, c in enumerate(b_ring):
                    tick()
                    if _intersects(a, a_ring[(i + 1) % len(a_ring)],
                                   c, b_ring[(j + 1) % len(b_ring)]):
                        _error('TOPOLOGY', 'Different rings cannot cross, touch or overlap.',
                               ring=rings[first].key, other_ring=rings[second].key,
                               edge_start=rings[first].vertices[i].key,
                               other_edge_start=rings[second].vertices[j].key)
    outer = next(i for i, ring in enumerate(rings) if ring.role == 'outer')
    holes = tuple(i for i, ring in enumerate(rings) if ring.role == 'hole')
    for hole in holes:
        for point in exact_rings[hole]:
            tick()
            if _containment(point, exact_rings[outer], tick) != 1:
                _error('CONTAINMENT', 'Every hole must lie strictly inside the outer ring.', ring=rings[hole].key)
    for i, first in enumerate(holes):
        for second in holes[i + 1:]:
            tick()
            if (_containment(exact_rings[first][0], exact_rings[second], tick) != -1 or
                    _containment(exact_rings[second][0], exact_rings[first], tick) != -1):
                _error('CONTAINMENT', 'Holes must be mutually exterior; nested holes are not supported.',
                       ring=rings[first].key, other_ring=rings[second].key)
    if area2 <= 0:
        _error('TOPOLOGY', 'The rings must enclose positive material area.')
    return tuple(exact_rings), outer, holes, area2


def _caps(exact_rings, outer, holes, expected_area2, tick):
    points, boundary = [], []
    for ring in exact_rings:
        offset = len(points)
        points.extend(ring)
        for i in range(len(ring)):
            tick()
            boundary.append((offset + i, offset + (i + 1) % len(ring)))
    count, hole_count = len(points), len(holes)
    boundary_pairs = {tuple(sorted(edge)) for edge in boundary}
    diagonals = []
    required = count + 3 * hole_count - 3
    for first in range(count):
        if len(diagonals) == required:
            break
        for second in range(first + 1, count):
            tick()
            if len(diagonals) == required:
                break
            if (first, second) in boundary_pairs:
                continue
            a, b = points[first], points[second]
            rejected = False
            # Existing graph crossings reject a candidate before repeating
            # boundary and containment proofs that cannot make it admissible
            for i, j in diagonals:
                tick()
                if first in (i, j) or second in (i, j):
                    continue
                if _intersects(a, b, points[i], points[j]):
                    rejected = True
                    break
            if rejected:
                continue
            for index, point in enumerate(points):
                tick()
                if index not in (first, second) and _on_segment(a, b, point):
                    rejected = True
                    break
            if rejected:
                continue
            for i, j in boundary:
                tick()
                if first in (i, j) or second in (i, j):
                    continue
                if _intersects(a, b, points[i], points[j]):
                    rejected = True
                    break
            if rejected:
                continue
            midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if _containment(midpoint, exact_rings[outer], tick) != 1:
                continue
            for hole in holes:
                tick()
                if _containment(midpoint, exact_rings[hole], tick) != -1:
                    rejected = True
                    break
            if rejected:
                continue
            diagonals.append((first, second))
    if len(diagonals) != required:
        _error('TOPOLOGY', 'The ring graph could not establish its complete triangulation.')
    adjacency = [[] for _ in points]
    material = set(boundary)
    for i, j in (*boundary, *diagonals):
        tick()
        adjacency[i].append(j)
        adjacency[j].append(i)
    for i, j in diagonals:
        tick()
        material.add((i, j))
        material.add((j, i))
    for origin, neighbors in enumerate(adjacency):
        tick()
        def compare(first, second):
            tick()
            a = tuple(points[first][axis] - points[origin][axis] for axis in range(2))
            b = tuple(points[second][axis] - points[origin][axis] for axis in range(2))
            ha = 0 if a[1] > 0 or a[1] == 0 and a[0] >= 0 else 1
            hb = 0 if b[1] > 0 or b[1] == 0 and b[0] >= 0 else 1
            if ha != hb:
                return -1 if ha < hb else 1
            cross = a[0] * b[1] - a[1] * b[0]
            if cross == 0:
                _error('TOPOLOGY', 'Incident graph edges must have distinct directions.')
            return -1 if cross > 0 else 1
        neighbors.sort(key=cmp_to_key(compare))
    successors = {}
    for origin, neighbors in enumerate(adjacency):
        for index, neighbor in enumerate(neighbors):
            tick()
            successors[(neighbor, origin)] = (origin, neighbors[index - 1])
    visited, triangles, area2 = set(), [], Fraction(0)
    for start in sorted(material):
        tick()
        if start in visited:
            continue
        current, face = start, []
        while True:
            tick()
            if current not in material or current in visited:
                _error('TOPOLOGY', 'Material face traversal must cover each halfedge exactly once.')
            visited.add(current)
            face.append(current[0])
            current = successors[current]
            if current == start:
                break
            if len(face) >= 3:
                _error('TOPOLOGY', 'Every material face must be triangular.')
        if len(face) != 3 or len(set(face)) != 3:
            _error('TOPOLOGY', 'Every material face requires three distinct corners.')
        signed = _turn(*(points[index] for index in face))
        if signed <= 0:
            _error('TOPOLOGY', 'Every material cap triangle must have positive area.')
        area2 += signed
        minimum = face.index(min(face))
        triangles.append(tuple(face[minimum:] + face[:minimum]))
    if (visited != material or len(triangles) != count + 2 * hole_count - 2 or
            area2 != expected_area2):
        _error('TOPOLOGY', 'Cap coverage, area and triangle counts must match the authored rings.')
    return tuple(sorted(triangles)), tuple(boundary)


def triangulate_holes(rings, materials, depth_m, bottom_region, top_region,
                      *, max_vertices=MAX_MESH_VERTICES, check=None):
    """Build a closed extrusion from one outer ring and zero through eight holes."""
    def tick():
        if check is not None:
            check()

    tick()
    rings, materials, count = _snapshot(rings, materials)
    if type(max_vertices) is not int or not 0 <= max_vertices <= MAX_MESH_VERTICES:
        raise SurfaceError('OKL-E-RESOURCE', 'Invalid remaining vertex budget.', details={'budget': max_vertices})
    required = 12 * count + 12 * (len(rings) - 1) - 12
    if required > max_vertices:
        raise SurfaceError('OKL-E-RESOURCE', 'Ring extrusion exceeds the remaining mesh vertex budget.',
                           details={'required': required, 'available': max_vertices})
    depth = _number(depth_m, 'OKL-E-HOLES-DEPTH', 'depth')
    if not MIN_DEPTH_M <= depth <= MAX_DEPTH_M:
        _error('DEPTH', 'Extrusion depth must lie in [0.001,100] meters.', depth_m=depth)
    for material in materials:
        tick()
    palette = _check_materials(materials)
    for label, region in (('bottom', bottom_region), ('top', top_region)):
        tick()
        _key(region, 'OKL-E-HOLES-REGION', label + ' region')
        if region not in palette:
            _error('REGION', 'A cap region is absent from the palette.', cap=label, region=region)
    rings = _validated_rings(rings, palette, tick)
    exact_rings, outer, holes, area2 = _topology(rings, tick)
    caps, boundary = _caps(exact_rings, outer, holes, area2, tick)
    vertices = tuple(vertex for ring in rings for vertex in ring.vertices)
    lower, upper = [], []
    for vertex in vertices:
        tick()
        x, y = vertex.point_m
        lower.append((x, y, 0.0))
        upper.append((x, y, depth))
    source_positions = tuple(lower + upper)
    positions, normals, identities = [], [], []
    groups = {key: [] for key in palette}

    def emit(ids, normal, region):
        tick()
        a, b, c = (source_positions[index] for index in ids)
        u, v = tuple(b[i] - a[i] for i in range(3)), tuple(c[i] - a[i] for i in range(3))
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
                 u[0] * v[1] - u[1] * v[0])
        facing = sum(x * y for x, y in zip(cross, normal))
        if (not math.isfinite(facing) or facing <= 0 or
                not all(math.isfinite(value) for value in normal) or
                abs(math.hypot(*normal) - 1.0) > 1e-12):
            _error('NUMERIC', 'A nonzero outward triangle and unit normal must remain representable.')
        start = len(positions)
        positions.extend((a, b, c))
        normals.extend((normal, normal, normal))
        identities.extend(ids)
        groups[region].extend((start, start + 1, start + 2))

    for a, b, c in caps:
        emit((c, b, a), (0.0, 0.0, -1.0), bottom_region)
    for a, b, c in caps:
        emit((count + a, count + b, count + c), (0.0, 0.0, 1.0), top_region)
    for i, j in boundary:
        tick()
        dx, dy = lower[j][0] - lower[i][0], lower[j][1] - lower[i][1]
        length = math.hypot(dx, dy)
        if not math.isfinite(length) or length <= 0:
            _error('NUMERIC', 'A wall edge must have a representable nonzero length.')
        normal = (dy / length, -dx / length, 0.0)
        emit((i, j, count + i), normal, vertices[i].region)
        emit((j, count + j, count + i), normal, vertices[i].region)
    regions = []
    for key in sorted(groups):
        tick()
        if groups[key]:
            regions.append(RegionTriangles(key, palette[key], tuple(groups[key])))
    return HolesMesh(tuple(ring.key for ring in rings),
                     tuple((ring.key, vertex.key) for ring in rings for vertex in ring.vertices),
                     tuple(positions), tuple(normals), tuple(regions), depth, tuple(identities))


# Keep the public geometry boundary small while the supplied-byte checker stays separate
from .holes_delivery import validate_holes_delivery
