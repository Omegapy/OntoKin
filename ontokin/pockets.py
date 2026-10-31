"""Finite prismatic bodies with independently authored blind pocket floors.

Exact planar predicates and one-round floor coordinates define the source
surface. The resulting triangles are visual geometry, without physical or
motion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from .extrusion import PolygonVertex, _turn, triangulate_extrusion
from .holes import PolygonRing, _topology, _caps
from .reach_numeric import MAX_OPERAND_BITS
from .surface import (MAX_MESH_VERTICES, RegionTriangles, SurfaceError,
                      SurfaceMaterial, _check_materials, _key, _number)


MAX_POCKETS = 8
MAX_VERTICES = 64
MAX_ORDER = 65535
MAX_COORDINATE_ABS_M = 100.0
MIN_HEIGHT_M = MIN_DEPTH_M = MIN_BASE_M = 0.001
MAX_HEIGHT_M = MAX_DEPTH_M = 100.0
MAX_TRIANGLES = 252
MAX_CORNERS = 756
_MIN_BASE = Fraction(MIN_BASE_M)
_CAP_AXIS = (Fraction(0), Fraction(0), Fraction(1))


@dataclass(frozen=True)
class PolygonPocket:
    key: str
    order: int
    vertices: tuple[PolygonVertex, ...]
    depth_m: float
    floor_region: str


@dataclass(frozen=True)
class PocketsMesh:
    positions: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    regions: tuple[RegionTriangles, ...]
    height_m: float
    corner_vertex_ids: tuple[tuple[str, str, str, str], ...]
    boundary_vertex_keys: tuple[tuple[str, str, tuple[str, ...]], ...]
    cap_axis: tuple[Fraction, Fraction, Fraction]

    @property
    def triangle_count(self):
        return sum(len(region.indices) // 3 for region in self.regions)


def _error(suffix, message, **details):
    raise SurfaceError('OKL-E-POCKETS-' + suffix, message, details=details)


def _resource(bits):
    raise SurfaceError('OKL-E-RESOURCE', 'Pocket geometry exceeded the unchanged exact operand bound.',
                       details={'budget': 'numeric_operand_bits', 'limit': MAX_OPERAND_BITS,
                                'consumed': bits})


def _bits(value):
    return max(value.numerator.bit_length(), value.denominator.bit_length())


class _Exact:
    """Charge and guard new floor and placement arithmetic without a cache."""
    def __init__(self, check):
        self.check = check

    def tick(self):
        if self.check is not None:
            self.check()

    def guard(self, value):
        bits = _bits(value)
        if bits > MAX_OPERAND_BITS:
            _resource(bits)
        return value

    def fraction(self, value):
        self.tick()
        if type(value) is int and value.bit_length() > MAX_OPERAND_BITS:
            _resource(value.bit_length())
        if type(value) is Fraction:
            self.guard(value)
        return self.guard(Fraction(value))

    def operation(self, a, b, kind):
        self.tick()
        a, b = self.guard(Fraction(a)), self.guard(Fraction(b))
        an, ad = a.numerator.bit_length(), a.denominator.bit_length()
        bn, bd = b.numerator.bit_length(), b.denominator.bit_length()
        if kind in ('add', 'sub'):
            prospective = max(max(an + bd, bn + ad) + 1, ad + bd)
        else:
            prospective = max(an + bn, ad + bd)
        if prospective > MAX_OPERAND_BITS:
            _resource(prospective)
        if kind == 'add':
            result = a + b
        elif kind == 'sub':
            result = a - b
        else:
            result = a * b
        return self.guard(result)

    def add(self, a, b):
        return self.operation(a, b, 'add')

    def sub(self, a, b):
        return self.operation(a, b, 'sub')

    def mul(self, a, b):
        return self.operation(a, b, 'mul')

    def less(self, a, b):
        self.tick()
        a, b = self.guard(Fraction(a)), self.guard(Fraction(b))
        prospective = max(a.numerator.bit_length() + b.denominator.bit_length(),
                          b.numerator.bit_length() + a.denominator.bit_length())
        if prospective > MAX_OPERAND_BITS:
            _resource(prospective)
        return a < b

    def rounded(self, value):
        self.tick()
        self.guard(value)
        try:
            result = float(value)
        except (OverflowError, ValueError):
            _error('NUMERIC', 'The pocket floor must remain a finite binary64 coordinate.')
        if not math.isfinite(result):
            _error('NUMERIC', 'The pocket floor must remain a finite binary64 coordinate.')
        return 0.0 if result == 0 else result


class _CallbackFailure(BaseException):
    def __init__(self, original):
        self.original = original


def _tick_callback(check):
    def tick():
        if check is not None:
            try:
                check()
            except BaseException as error:
                raise _CallbackFailure(error) from error
    return tick


def _reuse(function, *args, **kwargs):
    """Keep inherited algorithms while giving new geometry its own failures."""
    try:
        return function(*args, **kwargs)
    except SurfaceError as error:
        for prefix in ('OKL-E-HOLES-', 'OKL-E-EXTRUSION-'):
            if error.code.startswith(prefix):
                raise SurfaceError('OKL-E-POCKETS-' + error.code[len(prefix):],
                                   str(error), details=error.details) from error
        raise


def _sequence(value, minimum, maximum, suffix, label):
    if type(value) not in (list, tuple):
        _error(suffix, label + ' must be a bounded sequence.')
    captured = tuple(value[:maximum + 1])
    if not minimum <= len(captured) <= maximum:
        _error(suffix, label + ' is outside its declared count bound.')
    return captured


def _snapshot_vertices(vertices):
    raw = _sequence(vertices, 3, MAX_VERTICES, 'VERTEX', 'Boundary vertices')
    captured = []
    for vertex in raw:
        if type(vertex) is not PolygonVertex:
            _error('VERTEX', 'Expected a PolygonVertex value.')
        point = _sequence(vertex.point_m, 2, 2, 'POINT', 'Planar point')
        captured.append(PolygonVertex(vertex.key, vertex.order, point, vertex.region))
    return tuple(captured)


def _snapshot(outer_vertices, pockets, materials):
    """Copy every bounded host-owned leaf before calling cooperative work."""
    outer = _snapshot_vertices(outer_vertices)
    raw = _sequence(pockets, 0, MAX_POCKETS, 'POCKET', 'Pockets')
    captured, total = [], len(outer)
    for pocket in raw:
        if type(pocket) is not PolygonPocket:
            _error('POCKET', 'Expected a PolygonPocket value.')
        vertices = _snapshot_vertices(pocket.vertices)
        total += len(vertices)
        if total > MAX_VERTICES:
            _error('VERTEX', 'All exterior and pocket boundaries together permit at most 64 vertices.')
        captured.append(PolygonPocket(pocket.key, pocket.order, vertices,
                                       pocket.depth_m, pocket.floor_region))
    if type(materials) not in (list, tuple):
        raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'A pocket body requires 1 through 16 materials.')
    raw_materials = tuple(materials[:17])
    if not 1 <= len(raw_materials) <= 16:
        raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'A pocket body requires 1 through 16 materials.')
    palette = []
    for material in raw_materials:
        if type(material) is not SurfaceMaterial or type(material.rgba) not in (list, tuple):
            raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'Expected a bounded SurfaceMaterial value.')
        rgba = tuple(material.rgba[:5])
        if len(rgba) != 4:
            raise SurfaceError('OKL-E-SURFACE-MATERIAL', 'RGBA needs exactly four channels.')
        palette.append(SurfaceMaterial(material.key, rgba, material.metallic, material.roughness))
    return outer, tuple(captured), tuple(palette), total


def _native_number(value, suffix, label):
    if type(value) is int and value.bit_length() > MAX_OPERAND_BITS:
        _resource(value.bit_length())
    return _number(value, 'OKL-E-POCKETS-' + suffix, label)


def _floor_details(height_m, depth_m, *, check=None, pocket=None):
    arithmetic = _Exact(check)
    arithmetic.tick()
    height = _native_number(height_m, 'HEIGHT', 'height')
    if not MIN_HEIGHT_M <= height <= MAX_HEIGHT_M:
        _error('HEIGHT', 'Body height must lie in [0.001,100] meters.', height_m=height)
    arithmetic.tick()
    depth = _native_number(depth_m, 'DEPTH', 'pocket depth')
    if not MIN_DEPTH_M <= depth <= MAX_DEPTH_M or depth >= height:
        _error('DEPTH', 'Pocket depth must lie in [0.001,100] meters and stop above the bottom.',
               pocket=pocket, depth_m=depth, height_m=height)
    exact_height, exact_depth = arithmetic.fraction(height), arithmetic.fraction(depth)
    base = arithmetic.sub(exact_height, exact_depth)
    if arithmetic.less(base, _MIN_BASE):
        _error('BASE', 'The exact remaining base must be at least canonical binary64 0.001 meter.',
               pocket=pocket, depth_m=depth, height_m=height)
    floor = arithmetic.rounded(base)
    arithmetic.tick()
    if not 0 < floor < height:
        _error('NUMERIC', 'The rounded pocket floor must remain strictly between bottom and top.',
               pocket=pocket)
    effective = arithmetic.sub(exact_height, arithmetic.fraction(floor))
    return depth, floor, base, effective


def _validated_vertices(vertices, palette, tick, *, kind, boundary):
    keys, orders, points, captured = set(), set(), set(), []
    for vertex in vertices:
        tick()
        key = _key(vertex.key, 'OKL-E-POCKETS-VERTEX', 'vertex key')
        if key in keys:
            _error('VERTEX', 'Vertex keys must be unique within their boundary.',
                   boundary_kind=kind, boundary=boundary, vertex=key)
        keys.add(key)
        order = vertex.order
        if type(order) is not int or not 0 <= order <= MAX_ORDER or order in orders:
            _error('ORDER', 'Vertex orders must be unique integers in [0,65535] within a boundary.',
                   boundary_kind=kind, boundary=boundary, vertex=key, order=order)
        orders.add(order)
        point = tuple(_native_number(value, 'POINT', 'coordinate') for value in vertex.point_m)
        if any(abs(value) > MAX_COORDINATE_ABS_M for value in point):
            _error('POINT', 'Planar coordinates must lie within [-100,100] meters.',
                   boundary_kind=kind, boundary=boundary, vertex=key)
        if point in points:
            _error('TOPOLOGY', 'Boundary points must be distinct; the closing edge is implicit.',
                   boundary_kind=kind, boundary=boundary, vertex=key)
        points.add(point)
        region = _key(vertex.region, 'OKL-E-POCKETS-REGION', 'wall region')
        if region not in palette:
            _error('REGION', 'A wall region is absent from the palette.',
                   boundary_kind=kind, boundary=boundary, vertex=key, region=region)
        captured.append(PolygonVertex(key, order, point, region))
    return tuple(sorted(captured, key=lambda vertex: vertex.order))


def _ear_caps(exact, tick):
    """Use the unchanged .8 first-admissible-ear order on a validated outline."""
    retained = list(range(len(exact)))
    caps = []
    while len(retained) > 3:
        found = False
        for index, current in enumerate(retained):
            tick()
            previous, following = retained[index - 1], retained[(index + 1) % len(retained)]
            a, b, c = exact[previous], exact[current], exact[following]
            if _turn(a, b, c) <= 0:
                continue
            obstructed = False
            for candidate in retained:
                tick()
                if candidate in (previous, current, following):
                    continue
                point = exact[candidate]
                if (_turn(a, b, point) >= 0 and _turn(b, c, point) >= 0
                        and _turn(c, a, point) >= 0):
                    obstructed = True
                    break
            if not obstructed:
                caps.append((previous, current, following))
                del retained[index]
                found = True
                break
        if not found:
            _error('TOPOLOGY', 'The boundary has no admissible nondegenerate ear.')
    tick()
    if _turn(*(exact[index] for index in retained)) <= 0:
        _error('TOPOLOGY', 'The final cap triangle must have positive area.')
    caps.append(tuple(retained))
    return tuple(caps)


def _admit_face(a, b, c, normal, *, check=None):
    """Use exact stored coordinates before any destination quantization."""
    arithmetic = _Exact(check)
    arithmetic.tick()
    if (not all(math.isfinite(value) for value in normal)
            or abs(math.hypot(*normal) - 1.0) > 1e-12):
        _error('NUMERIC', 'Every emitted triangle must retain a finite outward unit normal.')
    exact = tuple(tuple(arithmetic.fraction(value) for value in point) for point in (a, b, c))
    u = tuple(arithmetic.sub(exact[1][axis], exact[0][axis]) for axis in range(3))
    v = tuple(arithmetic.sub(exact[2][axis], exact[0][axis]) for axis in range(3))
    cross = tuple(arithmetic.sub(arithmetic.mul(u[i], v[j]), arithmetic.mul(u[j], v[i]))
                  for i, j in ((1, 2), (2, 0), (0, 1)))
    facing = Fraction(0)
    for component, direction in zip(cross, normal):
        facing = arithmetic.add(facing, arithmetic.mul(component, arithmetic.fraction(direction)))
    if not arithmetic.less(0, facing):
        _error('NUMERIC', 'Every emitted triangle must retain a nonzero exact outward face.')


def _triangulate(outer_vertices, pockets, materials, height_m, bottom_region, top_region,
                 *, max_vertices, check):
    outer, raw_pockets, materials, count = _snapshot(outer_vertices, pockets, materials)
    tick = _tick_callback(check)
    for unused in range(4 * count + 4 * len(raw_pockets) + 6 * len(materials)):
        tick()
    if type(max_vertices) is not int or not 0 <= max_vertices <= MAX_MESH_VERTICES:
        raise SurfaceError('OKL-E-RESOURCE', 'Invalid remaining mesh vertex budget.',
                           details={'budget': max_vertices})
    required = 12 * count - 12
    if required > max_vertices:
        raise SurfaceError('OKL-E-RESOURCE', 'Pocket geometry exceeds the remaining mesh vertex budget.',
                           details={'required': required, 'available': max_vertices})
    height = _native_number(height_m, 'HEIGHT', 'height')
    if not MIN_HEIGHT_M <= height <= MAX_HEIGHT_M:
        _error('HEIGHT', 'Body height must lie in [0.001,100] meters.', height_m=height)
    palette = _check_materials(materials)
    for label, region in (('bottom', bottom_region), ('top', top_region)):
        tick()
        _key(region, 'OKL-E-POCKETS-REGION', label + ' region')
        if region not in palette:
            _error('REGION', 'A cap region is absent from the palette.', cap=label, region=region)
    outer = _validated_vertices(outer, palette, tick, kind='outer', boundary='outer')
    checked, keys, orders, floors = [], set(), set(), {}
    for pocket in raw_pockets:
        tick()
        key = _key(pocket.key, 'OKL-E-POCKETS-POCKET', 'pocket key')
        if key in keys:
            _error('POCKET', 'Pocket keys must be unique.', pocket=key)
        keys.add(key)
        if type(pocket.order) is not int or not 0 <= pocket.order <= MAX_ORDER or pocket.order in orders:
            _error('ORDER', 'Pocket orders must be unique integers in [0,65535].',
                   pocket=key, order=pocket.order)
        orders.add(pocket.order)
        vertices = _validated_vertices(pocket.vertices, palette, tick, kind='pocket', boundary=key)
        depth, floor, unused_base, unused_effective = _floor_details(
            height, pocket.depth_m, check=tick, pocket=key)
        region = _key(pocket.floor_region, 'OKL-E-POCKETS-REGION', 'floor region')
        if region not in palette:
            _error('REGION', 'A pocket floor region is absent from the palette.', pocket=key, region=region)
        checked.append(PolygonPocket(key, pocket.order, vertices, depth, region))
        floors[key] = floor
    pockets = tuple(sorted(checked, key=lambda pocket: pocket.order))
    rings = (PolygonRing('outer', 0, 'outer', outer),) + tuple(
        PolygonRing(pocket.key, index + 1, 'hole', pocket.vertices)
        for index, pocket in enumerate(pockets))
    exact_rings, exterior_index, hole_indices, top_area2 = _reuse(_topology, rings, tick)
    boundary_keys = (('outer', 'outer', tuple(vertex.key for vertex in outer)),) + tuple(
        ('pocket', pocket.key, tuple(vertex.key for vertex in pocket.vertices)) for pocket in pockets)
    source_positions, source_ids = [], []
    lower_ids, upper_ids = [], []
    for kind, boundary, vertices, lower in (
            ('outer', 'outer', outer, 0.0),
            *(('pocket', pocket.key, pocket.vertices, floors[pocket.key]) for pocket in pockets)):
        for vertex in vertices:
            tick()
            x, y = vertex.point_m
            lower_ids.append(len(source_positions))
            source_positions.append((x, y, lower))
            source_ids.append((kind, boundary, vertex.key, 'lower'))
            upper_ids.append(len(source_positions))
            source_positions.append((x, y, height))
            source_ids.append((kind, boundary, vertex.key, 'top'))
    if not pockets:
        old = _reuse(triangulate_extrusion, outer, materials, height, bottom_region, top_region,
                     max_vertices=max_vertices, check=tick)
        by_position = dict(zip(source_positions, source_ids))
        identities = []
        for position in old.positions:
            tick()
            identities.append(by_position[position])
        positions, normals, regions = old.positions, old.normals, old.regions
    else:
        positions, normals, identities = [], [], []
        groups = {key: [] for key in palette}

        def emit(indices, normal, region):
            tick()
            a, b, c = (source_positions[index] for index in indices)
            _admit_face(a, b, c, normal, check=tick)
            start = len(positions)
            positions.extend((a, b, c))
            normals.extend((normal, normal, normal))
            identities.extend(source_ids[index] for index in indices)
            groups[region].extend((start, start + 1, start + 2))

        for a, b, c in _ear_caps(exact_rings[0], tick):
            emit((lower_ids[c], lower_ids[b], lower_ids[a]), (0.0, 0.0, -1.0), bottom_region)
        caps, boundary = _reuse(_caps, exact_rings, exterior_index, hole_indices, top_area2, tick)
        for a, b, c in caps:
            emit((upper_ids[a], upper_ids[b], upper_ids[c]), (0.0, 0.0, 1.0), top_region)
        vertices = tuple(vertex for ring in rings for vertex in ring.vertices)
        for a, b in boundary:
            tick()
            first, second = vertices[a].point_m, vertices[b].point_m
            dx, dy = second[0] - first[0], second[1] - first[1]
            length = math.hypot(dx, dy)
            if not math.isfinite(length) or length <= 0:
                _error('NUMERIC', 'Every wall edge must retain a representable nonzero length.')
            normal = (dy / length, -dx / length, 0.0)
            emit((lower_ids[a], lower_ids[b], upper_ids[a]), normal, vertices[a].region)
            emit((lower_ids[b], upper_ids[b], upper_ids[a]), normal, vertices[a].region)
        offset = len(outer)
        for index, pocket in enumerate(pockets):
            tick()
            order = (0, *range(len(pocket.vertices) - 1, 0, -1))
            exact = tuple(exact_rings[index + 1][vertex] for vertex in order)
            for triangle in _ear_caps(exact, tick):
                ids = tuple(lower_ids[offset + order[vertex]] for vertex in triangle)
                emit(ids, (0.0, 0.0, 1.0), pocket.floor_region)
            offset += len(pocket.vertices)
        regions = []
        for key in sorted(groups):
            tick()
            if groups[key]:
                regions.append(RegionTriangles(key, palette[key], tuple(groups[key])))
    from .pockets_delivery import _validate_pockets_mesh
    result = PocketsMesh(tuple(positions), tuple(normals), tuple(regions), height,
                          tuple(identities), boundary_keys, _CAP_AXIS)
    _validate_pockets_mesh(result.corner_vertex_ids, result.positions,
                          boundary_vertex_keys=result.boundary_vertex_keys,
                          cap_axis=result.cap_axis, normals=result.normals, check=tick,
                          code='OKL-E-POCKETS-TOPOLOGY')
    return result


def triangulate_pockets(outer_vertices, pockets, materials, height_m, bottom_region, top_region,
                        *, max_vertices=MAX_MESH_VERTICES, check=None):
    """Build a complete, bounded closed surface with retained blind floors."""
    try:
        return _triangulate(outer_vertices, pockets, materials, height_m, bottom_region, top_region,
                            max_vertices=max_vertices, check=check)
    except _CallbackFailure as failure:
        raise failure.original


def placed_pockets_axis(rotation, *, check=None):
    """Return exact inherited outer-placement action on local +Z."""
    from .evaluator import _NumericFault, _unit_quaternion
    raw = _sequence(rotation, 4, 4, 'NUMERIC', 'Outer placement rotation')
    raw = tuple(_native_number(value, 'NUMERIC', 'rotation component') for value in raw)
    arithmetic = _Exact(check)
    arithmetic.tick()
    try:
        normalized = _unit_quaternion(raw)
    except _NumericFault as error:
        raise SurfaceError('OKL-E-POCKETS-NUMERIC', str(error)) from error
    w, x, y, z = (arithmetic.fraction(value) for value in normalized)
    add, sub, mul = arithmetic.add, arithmetic.sub, arithmetic.mul
    return (mul(2, add(mul(x, z), mul(w, y))),
            mul(2, sub(mul(y, z), mul(w, x))),
            sub(1, mul(2, add(mul(x, x), mul(y, y)))))


from .pockets_delivery import validate_pockets_delivery
