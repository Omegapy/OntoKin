"""Bounded matched polygon sections with authoritative triangular strips."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

from .holes import PolygonRing, _snapshot as _snapshot_rings, _validated_rings, _topology, _caps
from .holes_delivery import _cross, _dot, _sub
from .ring_loft_delivery import _validate_ring_loft_mesh, validate_ring_loft_delivery
from .surface import MAX_MESH_VERTICES, RegionTriangles, SurfaceError, _check_materials, _key, _number


MAX_SECTIONS = 8
MAX_AUTHORED_VERTICES = 256
MAX_ORDER = 65535
MIN_STATION_GAP_M = 0.001
MAX_STATION_M = 100.0
_MIN_GAP_EXACT = Fraction(MIN_STATION_GAP_M)


@dataclass(frozen=True)
class PolygonSection:
    key: str
    order: int
    station_m: float
    rings: tuple[PolygonRing, ...]


@dataclass(frozen=True)
class RingLoftMesh:
    section_keys: tuple[str, ...]
    ring_keys: tuple[str, ...]
    vertex_keys: tuple[tuple[str, str, str], ...]
    positions: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    regions: tuple[RegionTriangles, ...]
    corner_vertex_ids: tuple[tuple[str, str, str], ...]

    @property
    def triangle_count(self):
        return sum(len(region.indices) // 3 for region in self.regions)


def _error(suffix, message, **details):
    raise SurfaceError('OKL-E-RING-LOFT-' + suffix, message, details=details)


def _snapshot(sections, materials):
    if type(sections) not in (list, tuple):
        _error('SECTION', 'A polygon ring loft requires a bounded section sequence.')
    raw = tuple(sections[:MAX_SECTIONS + 1])
    if not 2 <= len(raw) <= MAX_SECTIONS:
        _error('SECTION', 'A polygon ring loft requires 2 through 8 sections.')
    copied, palette, total = [], None, 0
    for section in raw:
        if type(section) is not PolygonSection:
            _error('SECTION', 'Expected a PolygonSection value.')
        rings, frozen_palette, count = _snapshot_rings(section.rings,
                                                       materials if palette is None else palette)
        if palette is None:
            palette = frozen_palette
        total += count
        if total > MAX_AUTHORED_VERTICES:
            _error('SECTION', 'All sections together may contain at most 256 authored vertices.')
        copied.append(PolygonSection(section.key, section.order, section.station_m, rings))
    return tuple(copied), palette


def _checked_sections(sections, palette, tick):
    keys, orders, checked = set(), set(), []
    for section in sections:
        tick()
        key = _key(section.key, 'OKL-E-RING-LOFT-SECTION', 'section key')
        if key in keys:
            _error('SECTION', 'Section keys must be unique.', section=key)
        keys.add(key)
        order = section.order
        if type(order) is not int or not 0 <= order <= MAX_ORDER or order in orders:
            _error('ORDER', 'Section orders must be unique integers from 0 through 65535.',
                   section=key, order=order)
        orders.add(order)
        station = _number(section.station_m, 'OKL-E-RING-LOFT-STATION', 'station')
        if not 0 <= station <= MAX_STATION_M:
            _error('STATION', 'Section stations must lie within [0,100] meters.',
                   section=key, station_m=station)
        rings = _validated_rings(section.rings, palette, tick)
        checked.append(PolygonSection(key, order, station, rings))
    checked.sort(key=lambda section: section.order)
    for lower, upper in zip(checked, checked[1:]):
        tick()
        gap = Fraction(upper.station_m) - Fraction(lower.station_m)
        if gap < _MIN_GAP_EXACT:
            _error('STATION', 'Ordered stations must advance by at least canonical binary64 0.001 meters.',
                   lower=lower.key, upper=upper.key, separation_m=float(gap))
    signature = None
    for section in checked:
        tick()
        rings = []
        for ring in section.rings:
            tick()
            vertices = []
            for vertex in ring.vertices:
                tick()
                vertices.append((vertex.key, vertex.order))
            rings.append((ring.key, ring.order, ring.role, tuple(vertices)))
        current = tuple(rings)
        if signature is None:
            signature = current
        elif current != signature:
            _error('CORRESPONDENCE', 'Sections must retain identical ring and vertex keys, roles and orders.',
                   section=section.key, reference_section=checked[0].key)
    return tuple(checked)


def _unit_normal(points):
    """Normalize the exact cross without rounded subtraction or cancellation."""
    exact = tuple(tuple(Fraction(value) for value in point) for point in points)
    cross = _cross(_sub(exact[1], exact[0]), _sub(exact[2], exact[0]))
    scale = max(map(abs, cross))
    if not scale:
        _error('TOPOLOGY', 'Every triangle must have nonzero exact area.')
    scaled = tuple(float(component / scale) for component in cross)
    length = math.hypot(*scaled)
    normal = tuple(component / length for component in scaled)
    if (not all(math.isfinite(value) for value in normal)
            or abs(math.hypot(*normal) - 1.0) > 1e-12
            or _dot(cross, tuple(Fraction(value) for value in normal)) <= 0):
        _error('NUMERIC', 'A finite outward unit normal must remain representable.')
    return normal


def triangulate_ring_loft(sections, materials, bottom_region, top_region,
                          *, max_vertices=MAX_MESH_VERTICES, check=None):
    """Construct and exactly admit one closed matched-topology polygon loft."""
    def tick():
        if check is not None:
            check()

    tick()
    sections, materials = _snapshot(sections, materials)
    if type(max_vertices) is not int or not 0 <= max_vertices <= MAX_MESH_VERTICES:
        raise SurfaceError('OKL-E-RESOURCE', 'Invalid remaining vertex budget.',
                           details={'budget': max_vertices})
    for material in materials:
        tick()
    palette = _check_materials(materials)
    for cap, region in (('bottom', bottom_region), ('top', top_region)):
        tick()
        _key(region, 'OKL-E-RING-LOFT-REGION', cap + ' region')
        if region not in palette:
            _error('REGION', 'A cap region is absent from the palette.', cap=cap, region=region)
    sections = _checked_sections(sections, palette, tick)
    count = sum(len(ring.vertices) for ring in sections[0].rings)
    holes = len(sections[0].rings) - 1
    required = 3 * (2 * len(sections) * count + 4 * holes - 4)
    if required > max_vertices:
        raise SurfaceError('OKL-E-RESOURCE', 'Ring loft exceeds the remaining mesh vertex budget.',
                           details={'required': required, 'available': max_vertices})
    topologies = []
    for section in sections:
        tick()
        topologies.append(_topology(section.rings, tick))
    bottom_caps, boundary = _caps(*topologies[0], tick)
    top_caps, unused_boundary = _caps(*topologies[-1], tick)
    source_positions, vertex_keys, source_regions = [], [], []
    for section in sections:
        tick()
        for ring in section.rings:
            tick()
            for vertex in ring.vertices:
                tick()
                source_positions.append((*vertex.point_m, section.station_m))
                vertex_keys.append((section.key, ring.key, vertex.key))
                source_regions.append(vertex.region)
    positions, normals, identities = [], [], []
    groups = {key: [] for key in palette}

    def emit(indices, region):
        tick()
        points = tuple(source_positions[index] for index in indices)
        normal = _unit_normal(points)
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
    for section in range(len(sections) - 1):
        tick()
        lower, upper = section * count, (section + 1) * count
        for a, b in boundary:
            tick()
            region = source_regions[lower + a]
            emit((lower + a, lower + b, upper + a), region)
            emit((lower + b, upper + b, upper + a), region)
    _validate_ring_loft_mesh(tuple(identities), tuple(positions), normals=tuple(normals),
                             check=check, code='OKL-E-RING-LOFT-TOPOLOGY')
    regions = []
    for key in sorted(groups):
        tick()
        if groups[key]:
            regions.append(RegionTriangles(key, palette[key], tuple(groups[key])))
    return RingLoftMesh(tuple(section.key for section in sections),
                        tuple(ring.key for ring in sections[0].rings), tuple(vertex_keys),
                        tuple(positions), tuple(normals), tuple(regions), tuple(identities))
