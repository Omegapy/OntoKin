"""Discover authored section frames without redefining inherited geometry."""
from __future__ import annotations

import hashlib
import json

from .framed_loft_protocol import DEFINITION, SCHEMA_VERSION
from .json_limits import measure_json
from .profile_capabilities import FRAMED_LOFT_PROFILE
from .ring_loft_agent_catalog import catalog as ring_loft_catalog
from .ring_loft_agent_catalog import interface as ring_loft_interface


ADOPTION = "docs/language-design/framed-polygon-loft-v0.1/ADOPTION.md"
EXAMPLE = "examples/framed-polygon-lofts/hollow-elbow.ok"


def interface(policy=None, *, aggregate_limits=None):
    result = ring_loft_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.11",
        profile=FRAMED_LOFT_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema,
        transport="FramedLoftAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.11",
        request_schema="docs/language-design/agent-v0.11/request.schema.json",
        response_schema="docs/language-design/agent-v0.11/response.schema.json",
        adoption=ADOPTION,
        single_source_command="export SOURCE.ok --target ontokin.glb/0.11 --output MODEL.glb",
        source_constructors=[*result["source_constructors"], "framed_polygon_section", "loft_framed_rings"],
        framed_polygon_loft_limits={"min_sections": 2, "max_sections": 8,
            "min_rings_per_section": 1, "max_rings_per_section": 9,
            "min_holes_per_section": 0, "max_holes_per_section": 8,
            "min_vertices_per_ring": 3, "max_vertices_per_section": 64,
            "max_total_vertices": 256, "min_order": 0, "max_order": 65535,
            "max_planar_coordinate_abs_m": 100, "max_origin_component_abs_m": 100,
            "max_transformed_coordinate_abs_m": 256,
            "min_origin_separation_m": 0.001,
            "origin_separation_rule": "exact squared distance of canonical binary64 origins",
            "progression_rule": "exact displacement dot each neighboring frame +Z axis is strictly positive",
            "max_palette_keys": 16, "max_triangles": 540, "max_corners": 1620},
        frame_reference="consuming_carrier_self_frame",
        section_transform_rule="exact-rational-quaternion-single-round",
        frame_interpolation="none",
        polygon_exclusions=["crossed_or_pinched_or_overlapping_surfaces", "nested_holes",
            "foreign_owner_frames", "scale_or_shear", "automatic_frame_transport",
            "inferred_tangents", "frame_interpolation", "automatic_matching_or_resampling",
            "ring_creation_or_removal", "blind_cavities", "branching_ducts",
            "arbitrary_bevel_offsets", "arbitrary_boolean_operations",
            "implicit_mass_or_inertia_or_collision", "live_destination_physics"])
    return result


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    from .construction_catalog import _Budget, _entry, _public_interfaces
    result = ring_loft_catalog(policy=policy, check=check, aggregate_limits=aggregate_limits)
    compatible = [*result["compatible_definition_profiles"], FRAMED_LOFT_PROFILE]
    inherited_examples = result["complete_examples"]
    inherited_interface = result.pop("polygon_loft_interface")

    def selectors(value):
        if check is not None:
            check()
        if isinstance(value, dict):
            return {key: selectors(item) for key, item in value.items()}
        if isinstance(value, list):
            return [selectors(item) for item in value]
        if isinstance(value, str):
            # Only operational selectors change. Inherited source declarations,
            # profiles, summary schemas, and specification versions stay intact.
            return (value.replace("ontokin.agent/0.10", SCHEMA_VERSION)
                .replace("ontokin.glb/0.10", DEFINITION.destination)
                .replace("RingLoftAgentService", "FramedLoftAgentService")
                .replace("ring-loft-program-agent.sqlite3", DEFINITION.store_filename)
                .replace("ontokin.ring-loft-program-agent-store/0.1", DEFINITION.store_schema))
        return value

    result = selectors(result)
    result.update(schema_version="ontokin.agent-catalog/0.11", language_version="0.11",
        profile=FRAMED_LOFT_PROFILE,
        framed_polygon_loft_interface=interface(policy, aggregate_limits=aggregate_limits),
        inherited_polygon_loft_interface=inherited_interface,
        source_header='ontokin "0.11"; module Example @ "example"; profile "framed-polygon-loft-0.1";',
        compatible_definition_profiles=compatible, complete_examples=[EXAMPLE],
        inherited_loft_examples={"language_version": "0.10", "paths": inherited_examples},
        example_context="The .11 framed elbow is complete source. Inherited examples retain their declared source bindings.",
        adoption=ADOPTION)
    result["limits"].update(min_framed_polygon_sections=2, max_framed_polygon_sections=8,
        max_framed_loft_vertices_per_section=64, max_framed_loft_total_vertices=256,
        max_framed_loft_triangles=540, max_framed_loft_corners=1620)
    for item in result["items"]:
        if check is not None:
            check()
        if item["kind"] == "protocol":
            item.update(profile=FRAMED_LOFT_PROFILE, specification=ADOPTION,
                domains=["Explicit source 0.11 / framed-polygon-loft-0.1 and a separate Agent/0.11 store",
                    "Current trusted host authority, one cumulative counter and the original deadline",
                    "Exact source edits, immutable revisions, failed-edit rollback and durable retries",
                    "All twelve inherited operations; derived triangles are inspection data"],
                description="Authored rigid section frames, scoped repair and recorded delivery under source-requested budgets.")
        elif item["kind"] == "destination":
            item.update(profile=FRAMED_LOFT_PROFILE, specification=ADOPTION, examples=[EXAMPLE],
                domains=["Explicit source 0.11 and recorded GLB/0.11",
                    "Exact framed vertices, prescribed strip triangles and independently triangulated endpoint domains",
                    "Actual source and binary32 positions preserve cap orientation and complete shared topology",
                    "Recorded carrier motion; Unreal import and live destination physics remain unverified"])
        elif item["name"] == "Geometry" and item["kind"] == "type":
            item.update(description="Immutable primitives and native surfaces, including station and framed polygon lofts.",
                        specification=ADOPTION)
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["element_types"].append("FramedPolygonSection")
            item["domains"].append("Source .11 adds immutable FramedPolygonSection values containing an owning Pose and keyed PolygonRing values")
        elif item["name"] == "placed":
            item.update(specification=ADOPTION,
                description="Apply one rigid local visual placement to one unplaced native surface.",
                domains=[*item["domains"],
                    "Source .11 additionally accepts framed polygon lofts; each section frame remains distinct from this outer placement"])
        elif item["name"] == "geometry.surface":
            item.update(profile=FRAMED_LOFT_PROFILE, specification=ADOPTION,
                description="Bounded authored section frames, ring identities, materials and outer visual placement.",
                summary_contracts=[*item["summary_contracts"], "ontokin.framed-polygon-loft-summary/0.1"],
                domains=[*item["domains"],
                    "Framed sections expose sorted local origins, canonical wxyz rotations and their owning frame",
                    "Framed summaries have no station range; earlier summary schemas retain their original fields",
                    "Original XY cap domains and actual rounded three-dimensional triangles have separate checks"])
        elif item["name"] == "surface.mesh_page":
            item.update(profile=FRAMED_LOFT_PROFILE, specification=ADOPTION,
                domains=["Agent/0.11 pages identify framed-polygon-loft-0.1, including inherited geometry occurrences",
                    "Revision, occurrence, region, geometry, implementation and protocol bind every cursor",
                    "At most 256 triangles per page; derived indices are read-only inspection identities"])

    domains = ["2..8 ordered sections; at most 64 vertices per section and 256 over all sections",
        "Each section Pose references the consuming carrier's self.frame at construction and consumption",
        "Origin and planar coordinates have components within [-100,100] meters",
        "Existing source rotations canonicalize once; exact quaternion-matrix division and completed-coordinate rounding follow",
        "Neighbor origins are at least 0.001 meters apart and advance along both exact frame +Z axes",
        "Matched ring and vertex keys/orders define fixed strip diagonals; no frame transport or resampling",
        "Original XY endpoint domains determine caps; rounded nonplanar cap triangles are checked in three dimensions",
        "Complete source and delivered surfaces reject collapse, crossing, pinching and nonadjacent contact",
        "Visual geometry adds no physical matter, collision shape or motion authority"]
    for kind, name, signature, description in [
        ("type", "FramedPolygonSection", "FramedPolygonSection",
         "An immutable explicit order, owning rigid Pose and keyed polygon-ring collection."),
        ("builtin", "framed_polygon_section",
         "framed_polygon_section(order: Int, frame: Pose, rings: Keyed<PolygonRing>) -> FramedPolygonSection",
         "Author a matched polygon section in an explicit rigid frame within its own carrier."),
        ("builtin", "loft_framed_rings",
         "loft_framed_rings(sections: Keyed<FramedPolygonSection>, palette: Keyed<SurfaceMaterial>, bottom_region: String, top_region: String) -> Geometry",
         "Construct a closed triangular surface through matched, explicitly framed polygon sections."),
    ]:
        if check is not None:
            check()
        result["items"].append(_entry(kind, name, signature, description,
            capability="source_framed_polygon_lofts", profile=FRAMED_LOFT_PROFILE,
            specification=ADOPTION, domains=domains, examples=[EXAMPLE]))
    result["items"].append(_entry("capability", "source_framed_polygon_lofts", "source_framed_polygon_lofts",
        "Editable bent ducts and finite handle forms with explicit authored section poses.",
        capability="source_framed_polygon_lofts", profile=FRAMED_LOFT_PROFILE, specification=ADOPTION))
    if linked_program is not None:
        if linked_program.entry.ast.profile != FRAMED_LOFT_PROFILE:
            raise ValueError("Framed loft discovery requires the admitted framed-polygon-loft source profile.")
        result["program_context"] = {"program_revision": linked_program.bundle.program_revision,
            "state": "linked declarations; no evaluated output claimed",
            "source_manifest": linked_program.bundle.manifest()}
        budget = _Budget(check)
        for entry, node in _public_interfaces(linked_program, budget, source_profiles=True):
            budget.charge(entry, node)
            result["items"].append(entry)
    result.pop("revision", None)
    measure_json(result, check=check)
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    result["revision"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    return result
