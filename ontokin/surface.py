"""Deterministic, bounded native loft meshing used by the surface-0.1 compiler.

The source compiler supplies validated OntoKin values and preserves provenance. Output is visual data:
it adds no physical mass, collision surface, attachment or motion authority.

All units at this boundary are canonical SI meters and linear color factors.
Flat-shaded triangle corners are intentionally duplicated. Consequently the
closed variant is geometrically watertight by position, but not an indexed
welded manifold. The region index lists refer to these duplicated vertices.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Sequence

Vec3 = tuple[float, float, float]
RGBA = tuple[float, float, float, float]

MAX_SECTIONS = 64
MAX_MATERIALS = 16
MIN_RADIUS_M = 0.001
MAX_RADIUS_M = 100.0
MIN_STATION_GAP_M = 0.001
_MIN_STATION_GAP_EXACT = Fraction(1, 1000)
MAX_COORDINATE_ABS_M = 100.0
MAX_MESH_VERTICES = 250_000
_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z", re.ASCII)


class SurfaceError(ValueError):
    """Typed failure that a later source compiler can attach to a source span."""

    def __init__(self, code: str, message: str, *, details: dict | None = None):
        self.code = code
        self.details = details or {}
        super().__init__(message)


@dataclass(frozen=True)
class LoftSection:
    key: str
    station_m: float
    center_m: Vec3
    radius_x_m: float
    radius_y_m: float
    region: str


@dataclass(frozen=True)
class SurfaceMaterial:
    key: str
    rgba: RGBA
    metallic: float
    roughness: float


@dataclass(frozen=True)
class RegionTriangles:
    key: str
    material: SurfaceMaterial
    indices: tuple[int, ...]


@dataclass(frozen=True)
class LoftMesh:
    """Rigid local-space geometry; region indices point to shared arrays."""

    section_keys: tuple[str, ...]
    positions: tuple[Vec3, ...]
    normals: tuple[Vec3, ...]
    regions: tuple[RegionTriangles, ...]
    facets: int
    caps: str

    @property
    def triangle_count(self) -> int:
        return sum(len(region.indices) // 3 for region in self.regions)


def _error(code: str, description: str, **details: object) -> None:
    raise SurfaceError(code, description, details=details)


def _number(value: object, code: str, field: str) -> float:
    if type(value) not in (int, float):
        _error(code, f"{field} must be a finite number.", field=field)
    try:
        n = float(value)
    except (OverflowError, ValueError):
        _error(code, f"{field} must be a finite number.", field=field)
    if not math.isfinite(n):
        _error(code, f"{field} must be a finite number.", field=field)
    return n


def _key(value: object, code: str, field: str) -> str:
    if type(value) is not str:
        _error(code, f"{field} must be a valid stable key.", field=field,
               value_type=type(value).__name__)
    if _KEY.fullmatch(value) is None:
        _error(code, f"{field} must be a valid stable key.", field=field, value=value[:128])
    return value


def _check_sections(sections: Sequence[LoftSection]) -> list[LoftSection]:
    if not 2 <= len(sections) <= MAX_SECTIONS:
        _error("OKL-E-SURFACE-SECTION", "A loft requires 2 through 64 sections.",
               count=len(sections), minimum=2, maximum=MAX_SECTIONS)
    seen: set[str] = set()
    checked: list[LoftSection] = []
    for section in sections:
        if not isinstance(section, LoftSection):
            _error("OKL-E-SURFACE-SECTION", "Expected a LoftSection value.")
        key = _key(section.key, "OKL-E-SURFACE-SECTION", "section key")
        if key in seen:
            _error("OKL-E-SURFACE-SECTION", "Duplicate authored section key.", key=key)
        seen.add(key)
        station = _number(section.station_m, "OKL-E-SURFACE-STATION", "station")
        if abs(station) > MAX_COORDINATE_ABS_M:
            _error("OKL-E-SURFACE-STATION", "Station is outside the local bound.", key=key,
                   station_m=station)
        center = section.center_m
        if not isinstance(center, (list, tuple)) or len(center) != 3:
            _error("OKL-E-SURFACE-CENTER", "Center must have exactly three coordinates.", key=key)
        xyz = tuple(_number(c, "OKL-E-SURFACE-CENTER", "center") for c in center)
        if any(abs(c) > MAX_COORDINATE_ABS_M for c in xyz) or xyz[2] != 0.0:
            _error("OKL-E-SURFACE-CENTER", "Center must be in XY, within 100 meters.", key=key)
        radii: list[float] = []
        for label, raw in (("radius_x_m", section.radius_x_m), ("radius_y_m", section.radius_y_m)):
            radius = _number(raw, "OKL-E-SURFACE-RADIUS", label)
            if not MIN_RADIUS_M <= radius <= MAX_RADIUS_M:
                _error("OKL-E-SURFACE-RADIUS", "Radius is outside [0.001, 100] meters.",
                       key=key, field=label, value=radius)
            radii.append(radius)
        region = _key(section.region, "OKL-E-SURFACE-REGION", "region")
        # Do not retain caller-owned center lists or reread unchecked numbers.
        checked.append(LoftSection(key, station, xyz, radii[0], radii[1], region))
    ordered = sorted(checked, key=lambda item: item.station_m)
    for lower, upper in zip(ordered, ordered[1:]):
        # C1 compares exact canonical values with only coordinate-ULP allowance.
        difference = Fraction.from_float(upper.station_m) - Fraction.from_float(lower.station_m)
        allowance = (Fraction.from_float(math.ulp(lower.station_m))
                     + Fraction.from_float(math.ulp(upper.station_m))) / 2
        if difference <= 0 or difference + allowance < _MIN_STATION_GAP_EXACT:
            _error("OKL-E-SURFACE-STATION", "Stations must advance by at least 0.001 m within C1 representation bounds.",
                   lower=lower.key, upper=upper.key, separation_m=float(difference),
                   representation_allowance_m=float(allowance))
    return ordered


def _check_materials(materials: Sequence[SurfaceMaterial]) -> dict[str, SurfaceMaterial]:
    if not 1 <= len(materials) <= MAX_MATERIALS:
        _error("OKL-E-SURFACE-MATERIAL", "A loft requires 1 through 16 materials.",
               count=len(materials), minimum=1, maximum=MAX_MATERIALS)
    resolved: dict[str, SurfaceMaterial] = {}
    for material in materials:
        if not isinstance(material, SurfaceMaterial):
            _error("OKL-E-SURFACE-MATERIAL", "Expected a SurfaceMaterial value.")
        key = _key(material.key, "OKL-E-SURFACE-MATERIAL", "material key")
        if key in resolved:
            _error("OKL-E-SURFACE-MATERIAL", "Duplicate authored material key.", key=key)
        if not isinstance(material.rgba, (tuple, list)) or len(material.rgba) != 4:
            _error("OKL-E-SURFACE-MATERIAL", "RGBA needs exactly four channels.", key=key)
        channels: list[float] = []
        for c in material.rgba:
            n = _number(c, "OKL-E-SURFACE-MATERIAL", "rgba")
            if not 0.0 <= n <= 1.0:
                _error("OKL-E-SURFACE-MATERIAL", "RGBA must be in [0,1].", key=key)
            channels.append(n)
        factors: list[float] = []
        for field in ("metallic", "roughness"):
            n = _number(getattr(material, field), "OKL-E-SURFACE-MATERIAL", field)
            if not 0.0 <= n <= 1.0:
                _error("OKL-E-SURFACE-MATERIAL", "PBR factors must be in [0,1].", key=key,
                       field=field)
            factors.append(n)
        resolved[key] = SurfaceMaterial(key, tuple(channels), factors[0], factors[1])
    return resolved


def triangulate_loft(
    sections: Sequence[LoftSection],
    materials: Sequence[SurfaceMaterial],
    facets: int,
    caps: str,
    *,
    max_vertices: int = MAX_MESH_VERTICES,
    check: Callable[[], None] | None = None,
) -> LoftMesh:
    """Return independently indexed PBR triangle groups for one visual loft.

    Source identity comes from section/material keys. The generated vertex
    offsets are not stable under topology changes. A later compiler accounts
    aggregate meshes separately; max_vertices is this call's remaining budget.
    """
    if type(facets) is not int or not 8 <= facets <= 64 or facets % 4:
        _error("OKL-E-SURFACE-FACETS", "Facets must be divisible by four, from 8 through 64.",
               value=facets)
    if type(caps) is not str or caps not in ("flat", "none"):
        _error("OKL-E-SURFACE-CAPS", 'Only "flat" and "none" caps are supported.')
    if type(max_vertices) is not int or not 0 <= max_vertices <= MAX_MESH_VERTICES:
        _error("OKL-E-RESOURCE", "Invalid remaining vertex budget.", budget=max_vertices)
    if not isinstance(sections, (list, tuple)):
        _error("OKL-E-SURFACE-SECTION", "A bounded section sequence is required.")
    if not isinstance(materials, (list, tuple)):
        _error("OKL-E-SURFACE-MATERIAL", "A bounded palette sequence is required.")
    ordered = _check_sections(sections)
    palette = _check_materials(materials)
    for section in ordered:
        if section.region not in palette:
            _error("OKL-E-SURFACE-REGION", "Section region has no matching palette entry.",
                   section_key=section.key, region=section.region)
    triangles = 2 * (len(ordered) - 1) * facets
    if caps == "flat":
        triangles += 2 * facets
    expected_vertices = triangles * 3
    if expected_vertices > max_vertices:
        _error("OKL-E-RESOURCE", "Surface exceeds the remaining mesh vertex budget.",
               required=expected_vertices, available=max_vertices)
    if check is not None:
        check()

    angles = [(math.cos(2.0 * math.pi * j / facets),
               math.sin(2.0 * math.pi * j / facets)) for j in range(facets)]
    rings: list[tuple[Vec3, ...]] = []
    for s in ordered:
        if check is not None:
            check()
        rings.append(tuple((s.center_m[0] + s.radius_x_m * u,
                            s.center_m[1] + s.radius_y_m * v,
                            s.station_m) for u, v in angles))
    vertices: list[Vec3] = []
    normals: list[Vec3] = []
    region_indices: dict[str, list[int]] = {name: [] for name in sorted(palette)}

    def triangle(p: Vec3, q: Vec3, r: Vec3, region: str) -> None:
        ux, uy, uz = (q[i] - p[i] for i in range(3))
        vx, vy, vz = (r[i] - p[i] for i in range(3))
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        magnitude = math.sqrt(nx * nx + ny * ny + nz * nz)
        if not math.isfinite(magnitude) or magnitude == 0.0:
            _error("OKL-E-SURFACE-NUMERIC", "Triangulation produced a degenerate face.")
        unit = (nx / magnitude, ny / magnitude, nz / magnitude)
        first = len(vertices)
        vertices.extend((p, q, r))
        normals.extend((unit, unit, unit))
        region_indices[region].extend((first, first + 1, first + 2))

    for i in range(len(ordered) - 1):
        lower, upper = rings[i], rings[i + 1]
        region = ordered[i].region
        for j in range(facets):
            if check is not None:
                check()
            next_j = (j + 1) % facets
            triangle(lower[j], lower[next_j], upper[j], region)
            triangle(lower[next_j], upper[next_j], upper[j], region)
    if caps == "flat":
        for i in (0, len(ordered) - 1):
            region = ordered[i].region
            s = ordered[i]
            center: Vec3 = (s.center_m[0], s.center_m[1], s.station_m)
            ring = rings[i]
            lower_cap = i == 0
            for j in range(facets):
                if check is not None:
                    check()
                next_j = (j + 1) % facets
                if lower_cap:
                    triangle(center, ring[next_j], ring[j], region)
                else:
                    triangle(center, ring[j], ring[next_j], region)

    if len(vertices) != expected_vertices or len(vertices) != len(normals):
        _error("OKL-E-SURFACE-NUMERIC", "Triangulation count mismatch.")
    grouped: list[RegionTriangles] = []
    for name in sorted(palette):
        if check is not None:
            check()
        if region_indices[name]:
            grouped.append(RegionTriangles(name, palette[name], tuple(region_indices[name])))
    result = LoftMesh(tuple(s.key for s in ordered), tuple(vertices), tuple(normals),
                      tuple(grouped), facets, caps)
    if check is not None:
        check()
    return result
