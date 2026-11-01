"""Bounded source summaries and revision-independent native mesh page content.

The service supplies accepted-snapshot authorization and signed query cursors.
This module derives geometry only from the compiled OntoKin recipe; no derived
vertex is an editable source identity or an independent motion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import struct

from .agent_protocol import ProtocolError
from .diagnostics import OntoKinError
from .scene import MAX_MESH_VERTICES, SurfaceMesh, build_surface_mesh
from .surface import SurfaceError
from .profile_capabilities import EXTRUSION_PROFILE, EXTRUSION_PROFILES, EXECUTION_PROFILES, TEXTURE_PROFILES
from .values import bounded_data


PROFILE = "surface-0.1"
PAGE_SCHEMA = "ontokin.surface-mesh-page/0.1"
SUMMARY_SCHEMA = "ontokin.surface-summary/0.1"
COORDINATE_SYSTEM = "carrier_local_after_placement/0.1"
ORDERING = "native_triangle_ordinal/0.1"


def _surface_summary(geometry, *, check=None):
    """Describe at most 64 sections and 16 regions without allocating vertices."""
    if check is not None:
        check()
    recipe = geometry.get("surface", geometry)
    if recipe["kind"] == "pockets":
        from .pockets_inspection import pockets_summary
        return pockets_summary(geometry, check=check)
    if recipe["kind"] == "framed_loft":
        from .framed_loft_inspection import framed_loft_summary
        return framed_loft_summary(geometry, check=check)
    if recipe["kind"] == "ring_loft":
        from .ring_loft_inspection import ring_loft_summary
        return ring_loft_summary(geometry, check=check)
    if recipe["kind"] == "holes":
        from .holes_inspection import holes_summary
        return holes_summary(geometry, check=check)
    if recipe["kind"] == "extrusion":
        return extrusion_summary(geometry, check=check)
    ordered = sorted(recipe["sections"], key=lambda section: section.station_m)
    facets, caps = recipe["facets"], recipe["caps"]
    counts = {material.key: 0 for material in recipe["materials"]}
    for section in ordered[:-1]:
        if check is not None:
            check()
        counts[section.region] += 2 * facets
    if caps == "flat":
        counts[ordered[0].region] += facets
        counts[ordered[-1].region] += facets
    triangles = sum(counts.values())
    return {"schema_version": SUMMARY_SCHEMA, "profile": PROFILE,
            "section_keys": [section.key for section in ordered],
            "stations_m": [section.station_m for section in ordered],
            "palette_keys": sorted(counts), "facets": facets, "caps": caps,
            "triangle_count": triangles, "vertex_count": 3 * triangles,
            "regions": [{"key": key, "material_key": key, "triangle_count": counts[key]}
                        for key in sorted(counts) if counts[key]],
            "local_visual_placement": {
                "frame": "carrier_self_frame",
                "position_m": list(geometry.get("local_position", (0., 0., 0.))),
                "orientation_wxyz": list(geometry.get("local_rotation", (1., 0., 0., 0.)))},
            "physical_participation": "none",
            "motion_authority": "carrier_evaluated_world_pose"}



def surface_summary(geometry, *, check=None):
    result = _surface_summary(geometry, check=check)
    if geometry.get("surface", geometry).get("texture_bindings"):
        from .texture_runtime import texture_metadata
        result["texture_bindings"] = texture_metadata(geometry, check=check)
        result["texture_coordinate_system"] = "raw_unplaced_recipe_local_affine"
    return result


def extrusion_summary(geometry, *, check=None):
    """Expose ordered authored points and regional counts, never editable corners."""
    recipe = geometry.get("surface", geometry)
    vertices = sorted(recipe["vertices"], key=lambda vertex: vertex.order)
    counts = {}
    for material in recipe["materials"]:
        if check is not None:
            check()
        counts[material.key] = 0
    keys, orders, points = [], [], []
    for vertex in vertices:
        if check is not None:
            check()
        keys.append(vertex.key)
        orders.append(vertex.order)
        points.append(list(vertex.point_m))
        counts[vertex.region] += 2
    counts[recipe["bottom_region"]] += len(vertices) - 2
    counts[recipe["top_region"]] += len(vertices) - 2
    triangles = 4 * len(vertices) - 4
    return {"schema_version": "ontokin.polygon-extrusion-summary/0.1",
            "profile": EXTRUSION_PROFILE, "family": "polygon_extrusion",
            "vertex_keys": keys, "orders": orders, "points_m": points,
            "depth_m": recipe["depth_m"], "bottom_region": recipe["bottom_region"],
            "top_region": recipe["top_region"], "palette_keys": sorted(counts),
            "triangle_count": triangles, "vertex_count": 3 * triangles,
            "regions": [{"key": key, "material_key": key, "triangle_count": counts[key]}
                        for key in sorted(counts) if counts[key]],
            "local_visual_placement": {
                "frame": "carrier_self_frame",
                "position_m": list(geometry.get("local_position", (0., 0., 0.))),
                "orientation_wxyz": list(geometry.get("local_rotation", (1., 0., 0., 0.)))},
            "physical_participation": "none",
            "motion_authority": "carrier_evaluated_world_pose"}

def _mesh_digest(geometry, mesh, *, check, texture_uvs=None):
    """Implementation-scoped fingerprint, streamed with bounded work callbacks.

Domain, canonical recipe summary/palette, binary64 placed corner attributes,
and source-region index streams cover all geometry and PBR inputs. This is an
opaque cursor binding, not a replacement for the canonical program revision.
"""
    recipe = geometry.get("surface", geometry)
    summary = surface_summary(geometry, check=check)
    metadata = {"summary": summary, "coordinate_system": COORDINATE_SYSTEM,
                "ordering": ORDERING,
                "palette": bounded_data(sorted(recipe["materials"], key=lambda item: item.key), check=check)}
    digest = hashlib.sha256(b"ontokin.surface-mesh/0.1\0")
    digest.update(json.dumps(metadata, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\0")
    corner = struct.Struct("<6d")
    for index, (position, normal) in enumerate(zip(mesh.positions, mesh.normals)):
        if index % 256 == 0:
            check()
        digest.update(corner.pack(*position, *normal))
    for region in mesh.regions:
        check()
        digest.update(region.key.encode("ascii") + b"\0")
        digest.update(struct.pack("<I", len(region.indices)))
        for start in range(0, len(region.indices), 256):
            check()
            values = region.indices[start:start + 256]
            digest.update(struct.pack("<" + "I" * len(values), *values))
    if texture_uvs:
        digest.update(b"\0ontokin.texture-uv/0.1\0")
        for key in sorted(texture_uvs):
            check()
            digest.update(key.encode("ascii") + b"\0")
            for index, uv in enumerate(texture_uvs[key]):
                if index % 64 == 0:
                    check()
                digest.update(struct.pack("<2d", *uv))
    return "sha256:" + digest.hexdigest()


@dataclass
class SurfacePageContext:
    program_revision: str
    element_id: list[str]
    path: str
    region: str | None
    mesh: SurfaceMesh
    geometry_sha256: str
    ordinals: list[int]
    region_keys: list[str]
    budget: object
    profile: str = PROFILE
    texture_uvs: dict | None = None
    texture_bindings: dict | None = None

    def binding(self):
        return {"program_revision": self.program_revision, "element_id": self.element_id,
                "profile": self.profile, "region": self.region,
                "geometry_sha256": self.geometry_sha256,
                "ordering": ORDERING, "coordinate_system": COORDINATE_SYSTEM}

    def page(self, offset, count):
        if type(offset) is not int or not 0 <= offset <= len(self.ordinals):
            raise ProtocolError("OKL-E-REVISION", "The cursor offset is outside this immutable surface query.")
        if type(count) is not int or not 1 <= count <= 256:
            raise ProtocolError("OKA-E-REQUEST", "Surface page count must be an integer from 1 through 256.")
        if count > self.budget.limits["max_result_items"]:
            raise OntoKinError("OKL-E-RESOURCE", "Surface page count exceeds its result-item budget.",
                               category="resource_limit", phase="inspection",
                               details={"count": count, "max_result_items": self.budget.limits["max_result_items"]})
        selected = self.ordinals[offset:offset + count]
        positions, normals, triangles, regions = [], [], [], []
        for ordinal in selected:
            self.budget.tick()
            source_index, page_index = ordinal * 3, len(positions)
            positions.extend(self.mesh.positions[source_index:source_index + 3])
            normals.extend(self.mesh.normals[source_index:source_index + 3])
            triangles.append((page_index, page_index + 1, page_index + 2))
            regions.append(self.region_keys[ordinal])
        result = {"schema_version": PAGE_SCHEMA, **self.binding(), "path": self.path,
                  "total_triangles": self.mesh.triangle_count, "filtered_triangles": len(self.ordinals),
                  "offset": offset, "returned_triangles": len(selected),
                  "positions_m": positions, "normals": normals, "triangles": triangles,
                  "source_triangle_ordinals": selected, "region_keys": regions}
        if self.texture_bindings is not None:
            result["texture_bindings"] = self.texture_bindings
            result["texture_coordinate_system"] = "raw_unplaced_recipe_local_affine"
            result["texcoords_0"] = []
            for ordinal in selected:
                self.budget.tick()
                key = self.region_keys[ordinal]
                uv = self.texture_uvs.get(key) if self.texture_uvs else None
                result["texcoords_0"].extend(uv[ordinal * 3:ordinal * 3 + 3] if uv else [None, None, None])
        result = self.budget.data(result)
        end = offset + len(selected)
        return result, end if end < len(self.ordinals) else None


def prepare_surface_page(program, element_id, *, region=None, count=256, budgets=None, check=None, profile=PROFILE):
    """Compile a bounded native occurrence and prepare stable-order page state."""
    from .program_runtime import _request_budget, _Interrupt, _compile, _support
    try:
        from .program_bindings import PROFILE_BINDINGS
        if (not isinstance(profile, str) or profile not in EXECUTION_PROFILES and
                (profile not in PROFILE_BINDINGS or not PROFILE_BINDINGS[profile].native_surfaces)):
            raise ProtocolError("OKA-E-REQUEST", "This program profile does not supply native mesh inspection.")
        budget = _request_budget(budgets, check, profile)
        if count > budget.limits["max_result_items"]:
            raise OntoKinError("OKL-E-RESOURCE", "Surface page count exceeds its result-item budget.",
                               category="resource_limit", phase="inspection",
                               details={"count": count, "max_result_items": budget.limits["max_result_items"]})
        compiler = _compile(program, budget)
        _support(compiler)
        obj = next((obj for obj in compiler.model.objects.values() if list(obj.element_id) == element_id), None)
        if obj is None:
            raise ProtocolError("OKL-E-REVISION", "The occurrence identity does not name an object in this program.",
                                element_id=element_id, program_revision=program.program_revision)
        def error(code, message, **details):
            raise OntoKinError(code, message, obj.span, phase="inspection", blocks=[],
                               category="unsupported" if code == "OKL-E-CAPABILITY-UNSUPPORTED" else
                               "resource_limit" if code == "OKL-E-RESOURCE" else "invalid",
                               element_id=list(obj.element_id), details={"object_path": obj.path, **details})
        if obj.geometry["kind"] not in ("loft", "extrusion", "placed", "holes", "ring_loft", "framed_loft", "pockets"):
            error("OKL-E-CAPABILITY-UNSUPPORTED", "Surface mesh pages require supported native exterior geometry.",
                  geometry_kind=obj.geometry["kind"])
        recipe = obj.geometry.get("surface", obj.geometry)
        palette = {material.key for material in recipe["materials"]}
        if region is not None and region not in palette:
            error("OKL-E-SURFACE-REGION", "The region is absent from this occurrence's authored palette.",
                  region=region, palette_keys=sorted(palette))
        try:
            mesh = build_surface_mesh(obj.geometry, max_vertices=MAX_MESH_VERTICES, check=budget.tick)
        except SurfaceError as exc:
            error(exc.code, str(exc), **exc.details)
        texture_uvs = texture_bindings = None
        if profile in TEXTURE_PROFILES:
            from .texture_runtime import texture_coordinates, texture_metadata
            texture_bindings = texture_metadata(obj.geometry, check=budget.tick)
            raw_mesh = compiler.surface_meshes[obj.path]["mesh"]
            texture_uvs = texture_coordinates(obj.geometry, raw_mesh,
                charge=lambda n: budget.execution_budget.tick(amount=n), check=budget.tick)
        fingerprint = _mesh_digest(obj.geometry, mesh, check=budget.tick, texture_uvs=texture_uvs)
        keys = [""] * mesh.triangle_count
        for group in mesh.regions:
            for start in range(0, len(group.indices), 3):
                if start % 768 == 0:
                    budget.tick()
                keys[group.indices[start] // 3] = group.key
        selected = []
        for ordinal, key in enumerate(keys):
            if ordinal % 256 == 0:
                budget.tick()
            if region is None or key == region:
                selected.append(ordinal)
        return SurfacePageContext(program.program_revision, list(obj.element_id), obj.path,
                                  region, mesh, fingerprint, selected, keys, budget,
                                  profile if profile in EXTRUSION_PROFILES else PROFILE,
                                  texture_uvs=texture_uvs, texture_bindings=texture_bindings)
    except _Interrupt as exc:
        raise exc.error
