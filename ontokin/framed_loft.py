"""Bounded polygon lofts with explicitly authored rigid section frames.

Each section transform is an exact rational quaternion action followed by one
binary64 rounding per complete coordinate. The emitted triangles, including
slightly nonplanar rounded caps, define the admitted visual surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from .holes import PolygonRing, _snapshot as _snapshot_rings, _validated_rings, _topology, _caps
from .model import Pose
from .reach_numeric import MAX_OPERAND_BITS
from .ring_loft import RingLoftMesh, _unit_normal
from .ring_loft_delivery import _snapshot as _snapshot_delivery, _validate_ring_loft_mesh
from .surface import MAX_MESH_VERTICES, RegionTriangles, SurfaceError, _check_materials, _key, _number


MAX_SECTIONS = 8
MAX_AUTHORED_VERTICES = 256
MAX_ORDER = 65535
MAX_ORIGIN_M = 100.0
MAX_TRANSFORMED_M = 256.0
MIN_ORIGIN_GAP_M = 0.001
_MIN_GAP_SQUARED = Fraction(MIN_ORIGIN_GAP_M) ** 2
_QUATERNION_TOLERANCE = Fraction(1e-12)
_QUATERNION_LOWER = (1 - _QUATERNION_TOLERANCE) ** 2
_QUATERNION_UPPER = (1 + _QUATERNION_TOLERANCE) ** 2


@dataclass(frozen=True)
class FramedPolygonSection:
    key: str
    order: int
    frame: Pose
    rings: tuple[PolygonRing, ...]


@dataclass(frozen=True)
class FramedLoftMesh(RingLoftMesh):
    cap_axes: tuple[tuple[Fraction, Fraction, Fraction], tuple[Fraction, Fraction, Fraction]]


def _error(suffix, message, **details):
    raise SurfaceError('OKL-E-FRAMED-LOFT-' + suffix, message, details=details)


def _resource(bits):
    raise SurfaceError('OKL-E-RESOURCE', 'Framed geometry exceeded the unchanged exact operand bound.',
                       details={'budget': 'numeric_operand_bits', 'limit': MAX_OPERAND_BITS,
                                'consumed': bits})


def _bits(value):
    return max(value.numerator.bit_length(), value.denominator.bit_length())


class _Exact:
    """Precharge and bound each new exact transform operation without a cache."""
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
        return self.guard(Fraction(value))

    def operation(self, a, b, kind):
        self.tick()
        a, b = self.guard(Fraction(a)), self.guard(Fraction(b))
        an, ad = a.numerator.bit_length(), a.denominator.bit_length()
        bn, bd = b.numerator.bit_length(), b.denominator.bit_length()
        if kind in ('add', 'sub'):
            prospective = max(an + bd, bn + ad) + 1
            prospective = max(prospective, ad + bd)
        elif kind == 'mul':
            prospective = max(an + bn, ad + bd)
        else:
            if not b:
                _error('NUMERIC', 'A rigid section transform requires a nonzero denominator.')
            prospective = max(an + bd, ad + bn)
        if prospective > MAX_OPERAND_BITS:
            _resource(prospective)
        if kind == 'add':
            result = a + b
        elif kind == 'sub':
            result = a - b
        elif kind == 'mul':
            result = a * b
        else:
            result = a / b
        return self.guard(result)

    def add(self, a, b):
        return self.operation(a, b, 'add')

    def sub(self, a, b):
        return self.operation(a, b, 'sub')

    def mul(self, a, b):
        return self.operation(a, b, 'mul')

    def div(self, a, b):
        return self.operation(a, b, 'div')

    def dot(self, a, b):
        result = Fraction(0)
        for x, y in zip(a, b):
            self.tick()
            result = self.add(result, self.mul(x, y))
        return result

    def cross(self, a, b):
        result = []
        for i, j in ((1, 2), (2, 0), (0, 1)):
            self.tick()
            result.append(self.sub(self.mul(a[i], b[j]), self.mul(a[j], b[i])))
        return tuple(result)


def _sequence(value, count, suffix, label):
    if type(value) not in (list, tuple):
        _error(suffix, label + ' must be a bounded sequence.')
    captured = tuple(value[:count + 1])
    if len(captured) != count:
        _error(suffix, label + f' requires exactly {count} components.')
    return captured


def _snapshot(sections, materials):
    """Copy every bounded host-owned leaf before later work callbacks."""
    if type(sections) not in (list, tuple):
        _error('SECTION', 'A framed loft requires a bounded section sequence.')
    raw = tuple(sections[:MAX_SECTIONS + 1])
    if not 2 <= len(raw) <= MAX_SECTIONS:
        _error('SECTION', 'A framed loft requires 2 through 8 sections.')
    result, palette, total, copied_work = [], None, 0, 0
    for section in raw:
        if type(section) is not FramedPolygonSection:
            _error('SECTION', 'Expected a FramedPolygonSection value.')
        frame = section.frame
        if type(frame) is not Pose:
            _error('FRAME', 'A framed section requires a native rigid Pose.')
        position = _sequence(frame.position, 3, 'FRAME', 'Frame origin')
        rotation = _sequence(frame.rotation, 4, 'FRAME', 'Frame rotation')
        rings, frozen_palette, count = _snapshot_rings(section.rings,
                                                       materials if palette is None else palette)
        if palette is None:
            palette = frozen_palette
        total += count
        if total > MAX_AUTHORED_VERTICES:
            _error('SECTION', 'All framed sections together permit at most 256 authored vertices.')
        result.append(FramedPolygonSection(section.key, section.order,
                                            Pose(frame.frame, position, rotation), rings))
        copied_work += 9 + len(rings) + count * 3
    copied_work += len(palette) * 5
    return tuple(result), palette, copied_work


def _canonical_number(value, label, *, suffix='FRAME'):
    if type(value) is int and value.bit_length() > MAX_OPERAND_BITS:
        _resource(value.bit_length())
    value = _number(value, 'OKL-E-FRAMED-LOFT-' + suffix, label)
    return 0.0 if value == 0 else value


def _rotation_matrix(rotation, arithmetic, *, section=None):
    q = tuple(arithmetic.fraction(value) for value in rotation)
    squares = tuple(arithmetic.mul(value, value) for value in q)
    denominator = Fraction(0)
    for value in squares:
        arithmetic.tick()
        denominator = arithmetic.add(denominator, value)
    if not _QUATERNION_LOWER <= denominator <= _QUATERNION_UPPER:
        _error('FRAME', 'Section quaternion norm must remain within the inherited 1e-12 envelope.',
               section=section)
    w, x, y, z = q
    ww, xx, yy, zz = squares
    add, sub, mul = arithmetic.add, arithmetic.sub, arithmetic.mul
    rows = (
        (sub(sub(add(ww, xx), yy), zz), mul(2, sub(mul(x, y), mul(w, z))),
         mul(2, add(mul(x, z), mul(w, y)))),
        (mul(2, add(mul(x, y), mul(w, z))), sub(sub(add(ww, yy), xx), zz),
         mul(2, sub(mul(y, z), mul(w, x)))),
        (mul(2, sub(mul(x, z), mul(w, y))), mul(2, add(mul(y, z), mul(w, x))),
         sub(sub(add(ww, zz), xx), yy)),
    )
    result = []
    for row in rows:
        arithmetic.tick()
        result.append(tuple(arithmetic.div(value, denominator) for value in row))
    return tuple(result)


def _checked_sections(sections, palette, arithmetic, owner_frame):
    keys, orders, checked = set(), set(), []
    if owner_frame is not None and (type(owner_frame) is not str or not owner_frame.endswith('.frame')):
        _error('FRAME', 'The consuming geometry must name its carrier frame.')
    expected_frame = owner_frame
    for section in sections:
        arithmetic.tick()
        key = _key(section.key, 'OKL-E-FRAMED-LOFT-SECTION', 'section key')
        if key in keys:
            _error('SECTION', 'Section keys must be unique.', section=key)
        keys.add(key)
        order = section.order
        if type(order) is not int or not 0 <= order <= MAX_ORDER or order in orders:
            _error('ORDER', 'Section orders must be unique integers in [0,65535].', section=key)
        orders.add(order)
        frame = section.frame
        if (type(frame.frame) is not str or not frame.frame.endswith('.frame')
                or len(frame.frame) > 4096 or frame.frame == '.frame'):
            _error('FRAME', 'A section must reference its owning carrier frame.', section=key)
        if expected_frame is None:
            expected_frame = frame.frame
        if frame.frame != expected_frame:
            _error('FRAME', 'A section cannot acquire a different carrier frame.', section=key,
                   frame=frame.frame, owner_frame=expected_frame)
        origin = []
        for value in frame.position:
            arithmetic.tick()
            number = _canonical_number(value, 'frame origin')
            if abs(number) > MAX_ORIGIN_M:
                _error('FRAME', 'Frame origin components must lie in [-100,100] meters.', section=key)
            origin.append(number)
        rotation = []
        for value in frame.rotation:
            arithmetic.tick()
            rotation.append(_canonical_number(value, 'frame rotation'))
        if next((value for value in rotation if value), 1.0) < 0:
            rotation = [0.0 if value == 0 else -value for value in rotation]
        rings = _validated_rings(section.rings, palette, arithmetic.tick)
        checked.append(FramedPolygonSection(key, order,
                                            Pose(frame.frame, tuple(origin), tuple(rotation)), rings))
    checked.sort(key=lambda section: section.order)
    matrices = tuple(_rotation_matrix(section.frame.rotation, arithmetic, section=section.key)
                     for section in checked)
    for index, (lower, upper) in enumerate(zip(checked, checked[1:])):
        arithmetic.tick()
        delta = tuple(arithmetic.sub(arithmetic.fraction(b), arithmetic.fraction(a))
                      for a, b in zip(lower.frame.position, upper.frame.position))
        before = tuple(row[2] for row in matrices[index])
        after = tuple(row[2] for row in matrices[index + 1])
        if (arithmetic.dot(delta, delta) < _MIN_GAP_SQUARED
                or arithmetic.dot(delta, before) <= 0 or arithmetic.dot(delta, after) <= 0):
            _error('PROGRESSION', 'Adjacent section origins must be separated and advance along both +Z axes.',
                   lower=lower.key, upper=upper.key)
    signature = None
    for section in checked:
        arithmetic.tick()
        rings = []
        for ring in section.rings:
            arithmetic.tick()
            vertices = []
            for vertex in ring.vertices:
                arithmetic.tick()
                vertices.append((vertex.key, vertex.order))
            rings.append((ring.key, ring.order, ring.role, tuple(vertices)))
        current = tuple(rings)
        if signature is None:
            signature = current
        elif current != signature:
            _error('CORRESPONDENCE', 'Sections must retain identical ring and vertex keys, roles and orders.',
                   section=section.key, reference_section=checked[0].key)
    return tuple(checked), matrices


def _transform(point, origin, matrix, arithmetic):
    u, v = (arithmetic.fraction(value) for value in point)
    result = []
    for row, offset in zip(matrix, origin):
        arithmetic.tick()
        exact = arithmetic.add(arithmetic.fraction(offset),
                               arithmetic.add(arithmetic.mul(row[0], u), arithmetic.mul(row[1], v)))
        number = float(exact)
        if not math.isfinite(number) or abs(number) > MAX_TRANSFORMED_M:
            _error('NUMERIC', 'Transformed source coordinates must remain within [-256,256] meters.')
        result.append(0.0 if number == 0 else number)
    return tuple(result)


def _cap_signs(ids, positions, section_keys, axes, arithmetic, code):
    endpoints = {section_keys[0]: (axes[0], -1), section_keys[-1]: (axes[1], 1)}
    counts = {key: 0 for key in endpoints}
    for start in range(0, len(ids), 3):
        arithmetic.tick()
        layers = {identity[0] for identity in ids[start:start + 3]}
        if len(layers) != 1:
            continue
        key = next(iter(layers))
        if key not in endpoints:
            raise SurfaceError(code, 'Only the first and last authored sections may carry caps.')
        axis, sign = endpoints[key]
        points = tuple(tuple(arithmetic.fraction(value) for value in point)
                       for point in positions[start:start + 3])
        a = tuple(arithmetic.sub(x, y) for x, y in zip(points[1], points[0]))
        b = tuple(arithmetic.sub(x, y) for x, y in zip(points[2], points[0]))
        dot = arithmetic.dot(arithmetic.cross(a, b), axis)
        if (dot >= 0 if sign < 0 else dot <= 0):
            raise SurfaceError(code, 'An endpoint cap must retain its authored outward orientation.',
                               details={'section': key, 'triangle': start // 3})
        counts[key] += 1
    if not all(counts.values()):
        raise SurfaceError(code, 'Both endpoint cap domains must remain present.')


def triangulate_framed_loft(sections, materials, bottom_region, top_region,
                             *, max_vertices=MAX_MESH_VERTICES, owner_frame=None, check=None):
    """Build and admit the actual finite source triangles without frame inference."""
    arithmetic = _Exact(check)
    arithmetic.tick()
    sections, materials, copied_work = _snapshot(sections, materials)
    for unused in range(copied_work):
        arithmetic.tick()
    if type(max_vertices) is not int or not 0 <= max_vertices <= MAX_MESH_VERTICES:
        raise SurfaceError('OKL-E-RESOURCE', 'Invalid remaining vertex budget.',
                           details={'budget': max_vertices})
    for material in materials:
        arithmetic.tick()
    palette = _check_materials(materials)
    for cap, region in (('bottom', bottom_region), ('top', top_region)):
        arithmetic.tick()
        _key(region, 'OKL-E-FRAMED-LOFT-REGION', cap + ' region')
        if region not in palette:
            _error('REGION', 'A cap region is absent from the palette.', cap=cap, region=region)
    sections, matrices = _checked_sections(sections, palette, arithmetic, owner_frame)
    count = sum(len(ring.vertices) for ring in sections[0].rings)
    holes = len(sections[0].rings) - 1
    required = 3 * (2 * len(sections) * count + 4 * holes - 4)
    if required > max_vertices:
        raise SurfaceError('OKL-E-RESOURCE', 'Framed loft exceeds the remaining mesh vertex budget.',
                           details={'required': required, 'available': max_vertices})
    topologies = []
    for section in sections:
        arithmetic.tick()
        topologies.append(_topology(section.rings, arithmetic.tick))
    bottom_caps, boundary = _caps(*topologies[0], arithmetic.tick)
    top_caps, unused_boundary = _caps(*topologies[-1], arithmetic.tick)
    source_positions, vertex_keys, source_regions = [], [], []
    for section, matrix in zip(sections, matrices):
        arithmetic.tick()
        for ring in section.rings:
            arithmetic.tick()
            for vertex in ring.vertices:
                arithmetic.tick()
                source_positions.append(_transform(vertex.point_m, section.frame.position, matrix, arithmetic))
                vertex_keys.append((section.key, ring.key, vertex.key))
                source_regions.append(vertex.region)
    positions, normals, identities = [], [], []
    groups = {key: [] for key in palette}

    def emit(indices, region):
        arithmetic.tick()
        points = tuple(source_positions[index] for index in indices)
        try:
            normal = _unit_normal(points)
        except SurfaceError as error:
            if error.code.startswith('OKL-E-RING-LOFT-'):
                raise SurfaceError(error.code.replace('RING-LOFT', 'FRAMED-LOFT'), str(error),
                                   details=error.details) from error
            raise
        start = len(positions)
        positions.extend(points)
        normals.extend((normal, normal, normal))
        identities.extend(vertex_keys[index] for index in indices)
        groups[region].extend((start, start + 1, start + 2))

    for a, b, c in bottom_caps:
        emit((c, b, a), bottom_region)
    last = (len(sections) - 1) * count
    for a, b, c in top_caps:
        emit((last + a, last + b, last + c), top_region)
    for index in range(len(sections) - 1):
        arithmetic.tick()
        lower, upper = index * count, (index + 1) * count
        for a, b in boundary:
            arithmetic.tick()
            region = source_regions[lower + a]
            emit((lower + a, lower + b, upper + a), region)
            emit((lower + b, upper + b, upper + a), region)
    ids, points, unit_normals = tuple(identities), tuple(positions), tuple(normals)
    section_keys = tuple(section.key for section in sections)
    axes = (tuple(row[2] for row in matrices[0]), tuple(row[2] for row in matrices[-1]))
    _validate_ring_loft_mesh(ids, points, normals=unit_normals, check=check,
                             code='OKL-E-FRAMED-LOFT-TOPOLOGY')
    _cap_signs(ids, points, section_keys, axes, arithmetic, 'OKL-E-FRAMED-LOFT-TOPOLOGY')
    regions = []
    for key in sorted(groups):
        arithmetic.tick()
        if groups[key]:
            regions.append(RegionTriangles(key, palette[key], tuple(groups[key])))
    return FramedLoftMesh(section_keys, tuple(ring.key for ring in sections[0].rings),
                          tuple(vertex_keys), points, unit_normals, tuple(regions), ids, axes)


def _snapshot_axes(cap_axes, code):
    raw = _sequence(cap_axes, 2, 'NUMERIC', 'Endpoint cap axes')
    result = []
    for axis in raw:
        axis = _sequence(axis, 3, 'NUMERIC', 'Endpoint cap axis')
        copied = []
        for value in axis:
            if type(value) not in (int, float, Fraction):
                raise SurfaceError(code, 'Cap axes require exact native numeric leaves.')
            if type(value) is float and not math.isfinite(value):
                raise SurfaceError(code, 'Cap axes must remain finite.')
            if type(value) is int and value.bit_length() > MAX_OPERAND_BITS:
                _resource(value.bit_length())
            exact = Fraction(value)
            if _bits(exact) > MAX_OPERAND_BITS:
                _resource(_bits(exact))
            copied.append(exact)
        if not any(copied):
            raise SurfaceError(code, 'A cap axis cannot be zero.')
        result.append(tuple(copied))
    return tuple(result)


def placed_cap_axes(cap_axes, rotation, *, check=None):
    """Apply the inherited outer-placement matrix without rounding the axes."""
    from .evaluator import _NumericFault, _unit_quaternion
    axes = _snapshot_axes(cap_axes, 'OKL-E-FRAMED-LOFT-NUMERIC')
    raw = _sequence(rotation, 4, 'NUMERIC', 'Outer placement rotation')
    raw = tuple(_canonical_number(value, 'outer placement rotation', suffix='NUMERIC') for value in raw)
    arithmetic = _Exact(check)
    arithmetic.tick()
    if not any(raw):
        _error('NUMERIC', 'Outer placement requires a nonzero rotation.')
    try:
        normalized = _unit_quaternion(raw)
    except _NumericFault as error:
        raise SurfaceError('OKL-E-FRAMED-LOFT-NUMERIC', str(error)) from error
    w, x, y, z = (arithmetic.fraction(value) for value in normalized)
    add, sub, mul = arithmetic.add, arithmetic.sub, arithmetic.mul
    rows = (
        (sub(1, mul(2, add(mul(y, y), mul(z, z)))), mul(2, sub(mul(x, y), mul(w, z))),
         mul(2, add(mul(x, z), mul(w, y)))),
        (mul(2, add(mul(x, y), mul(w, z))), sub(1, mul(2, add(mul(x, x), mul(z, z)))),
         mul(2, sub(mul(y, z), mul(w, x)))),
        (mul(2, sub(mul(x, z), mul(w, y))), mul(2, add(mul(y, z), mul(w, x))),
         sub(1, mul(2, add(mul(x, x), mul(y, y))))),
    )
    return tuple(tuple(arithmetic.dot(row, axis) for row in rows) for axis in axes)


def validate_framed_loft_delivery(corner_vertex_ids, delivered_positions, *, section_keys,
                                   cap_axes, normals=None, check=None):
    """Validate supplied positions with independent source identities and cap axes."""
    code = 'OKL-E-FRAMED-LOFT-NUMERIC'
    if type(section_keys) not in (list, tuple):
        raise SurfaceError(code, 'A delivered framed loft needs bounded source section keys.')
    keys = tuple(section_keys[:MAX_SECTIONS + 1])
    if not 2 <= len(keys) <= MAX_SECTIONS:
        raise SurfaceError(code, 'A delivered framed loft needs 2 through 8 source sections.')
    for key in keys:
        _key(key, code, 'source section key')
    if len(set(keys)) != len(keys):
        raise SurfaceError(code, 'Source section keys must remain distinct.')
    axes = _snapshot_axes(cap_axes, code)
    ids, points, captured_normals = _snapshot_delivery(corner_vertex_ids, delivered_positions, normals, code)
    arithmetic = _Exact(check)
    arithmetic.tick()
    _validate_ring_loft_mesh(ids, points, normals=captured_normals, check=check, code=code)
    if {identity[0] for identity in ids} != set(keys):
        raise SurfaceError(code, 'The complete supplied section inventory must match the source.')
    _cap_signs(ids, points, keys, axes, arithmetic, code)
