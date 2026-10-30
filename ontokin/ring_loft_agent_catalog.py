"""Discover matched polygon sections and their explicit triangular surface."""
from __future__ import annotations

import hashlib
import json

from .holes_agent_catalog import catalog as holes_catalog
from .holes_agent_catalog import interface as holes_interface
from .json_limits import measure_json
from .profile_capabilities import RING_LOFT_PROFILE
from .ring_loft_protocol import SCHEMA_VERSION, DEFINITION


ADOPTION = "docs/language-design/polygon-loft-v0.1/ADOPTION.md"
EXAMPLE = "examples/polygon-lofts/hollow-frustum.ok"


def interface(policy=None, *, aggregate_limits=None):
    result = holes_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.10",
        profile=RING_LOFT_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema,
        transport="RingLoftAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.10",
        request_schema="docs/language-design/agent-v0.10/request.schema.json",
        response_schema="docs/language-design/agent-v0.10/response.schema.json",
        adoption=ADOPTION,
        single_source_command="export SOURCE.ok --target ontokin.glb/0.10 --output MODEL.glb",
        source_constructors=["surface_material", "loft_section", "loft", "planar_point", "polygon_vertex",
            "polygon_ring", "polygon_section", "extrude", "extrude_rings", "loft_rings", "placed"],
        ring_loft_limits={"min_sections": 2, "max_sections": 8,
            "min_rings_per_section": 1, "max_rings_per_section": 9,
            "min_holes_per_section": 0, "max_holes_per_section": 8,
            "min_vertices_per_ring": 3, "max_vertices_per_section": 64,
            "max_total_vertices": 256, "min_order": 0, "max_order": 65535,
            "min_station_m": 0, "max_station_m": 100, "min_station_gap_m": 0.001,
            "station_gap_rule": "exact difference of canonical binary64 stations",
            "max_coordinate_abs_m": 100, "max_palette_keys": 16,
            "max_triangles": 540, "max_corners": 1620},
        surface_rule="fixed-diagonal-triangles",
        correspondence="Exact matching ring keys, roles and orders and per-ring vertex keys and orders",
        strip_material_ownership="Lower section's outgoing-edge region; terminal regions emit no strip",
        polygon_exclusions=["crossed_or_pinched_or_overlapping_surfaces", "nested_holes",
            "automatic_matching_or_resampling", "ring_creation_or_removal", "blind_cavities",
            "branching_ducts", "arbitrary_bevel_offsets", "arbitrary_boolean_operations",
            "implicit_mass_or_inertia_or_collision", "live_destination_physics"])
    return result


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    from .construction_catalog import _Budget, _entry, _public_interfaces
    result = holes_catalog(policy=policy, check=check, aggregate_limits=aggregate_limits)
    compatible = result["compatible_definition_profiles"] + [RING_LOFT_PROFILE]
    inherited_examples = result["complete_examples"]

    def transport(value):
        if check is not None:
            check()
        if isinstance(value, dict):
            return {key: transport(item) for key, item in value.items()}
        if isinstance(value, list):
            return [transport(item) for item in value]
        if isinstance(value, str):
            # Protocol selectors change; inherited source profiles and their
            # geometry summary schemas keep their independently adopted meaning.
            return (value.replace("ontokin.agent/0.9", SCHEMA_VERSION)
                .replace("ontokin.glb/0.9", DEFINITION.destination)
                .replace("HolesAgentService", "RingLoftAgentService")
                .replace("holes-program-agent.sqlite3", DEFINITION.store_filename)
                .replace("ontokin.holes-program-agent-store/0.1", DEFINITION.store_schema))
        return value

    result = transport(result)
    result.pop("polygon_holes_interface", None)
    result.update(schema_version="ontokin.agent-catalog/0.10", language_version="0.10",
        profile=RING_LOFT_PROFILE,
        polygon_loft_interface=interface(policy, aggregate_limits=aggregate_limits),
        source_header='ontokin "0.10"; module Example @ "example"; profile "polygon-loft-0.1";',
        compatible_definition_profiles=compatible, complete_examples=[EXAMPLE],
        inherited_ring_examples={"language_version": "0.9", "paths": inherited_examples},
        example_context="The .10 loft example is complete source. Earlier examples retain their declared bindings.",
        adoption=ADOPTION)
    result["limits"].update(min_polygon_sections=2, max_polygon_sections=8,
        max_ring_loft_vertices_per_section=64, max_ring_loft_total_vertices=256,
        max_ring_loft_triangles=540, max_ring_loft_corners=1620)
    for item in result["items"]:
        if check is not None:
            check()
        item["profile"] = RING_LOFT_PROFILE
        if item["kind"] == "protocol":
            item.update(specification=ADOPTION,
                domains=["Explicit source 0.10 / polygon-loft-0.1 and a separate Agent/0.10 store",
                    "Current host authority and one cumulative counter and original deadline per request",
                    "Exact file source edits, immutable revisions and failed-edit rollback",
                    "All twelve inherited operations; derived triangle indices are inspection data"],
                description="Matched polygon sections, scoped repair and recorded delivery under source-requested budgets.")
        elif item["kind"] == "destination":
            item.update(specification=ADOPTION, examples=[EXAMPLE],
                domains=["Explicit source 0.10 and recorded GLB/0.10",
                    "Actual fixed-diagonal strips, independent endpoint caps and regional PBR primitives",
                    "Source and supplied binary32 surfaces must preserve shared topology without collapse or intersections",
                    "Recorded carrier motion; no Unreal Engine import or live destination physics claim"])
        elif item["name"] == "Geometry" and item["kind"] == "type":
            item.update(description="Immutable primitives, elliptical lofts, polygon extrusions and matched polygon ring lofts.",
                        specification=ADOPTION)
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["element_types"].append("PolygonSection")
            item["domains"].append("Source .10 adds immutable PolygonSection values containing typed keyed PolygonRing values")
        elif item["name"] == "placed":
            item.update(specification=ADOPTION,
                description="Apply one rigid local visual transform to one unplaced native surface.",
                domains=["Source .10 also accepts a matched polygon ring loft; primitives and nested placement reject",
                         "Pose references the carrier's self.frame; no scale, shear or added motion authority"])
        elif item["name"] == "geometry.surface":
            item.update(specification=ADOPTION,
                description="Bounded authored section, ring, vertex, placement and material summary.",
                summary_contracts=["ontokin.surface-summary/0.1", "ontokin.polygon-extrusion-summary/0.1",
                    "ontokin.polygon-holes-summary/0.1", "ontokin.polygon-loft-summary/0.1"],
                domains=["Inherited summaries retain their original schema and profile meanings",
                    "Ring loft summaries expose ordered sections and matched ring/vertex identities",
                    "Fixed-diagonal triangles define the surface; exact linearly interpolated polygon slices are not promised",
                    "Derived corners and triangles require bounded revision-bound mesh-page inspection"])
        elif item["name"] == "surface.mesh_page":
            item.update(specification=ADOPTION,
                domains=["Agent/0.10 pages identify polygon-loft-0.1, including inherited native geometry",
                    "Revision, occurrence, region, geometry, implementation and protocol bind every cursor",
                    "At most 256 triangles per page; derived indices are read-only inspection identities"])

    domains = ["2..8 ordered sections, 3..64 vertices per section and at most 256 vertices in total",
        "Exactly matched ring keys, roles and orders and per-ring vertex keys and orders",
        "One counterclockwise outer ring and zero through eight clockwise holes in each section",
        "Stations in [0,100]m increase by an exact binary64-rational gap of at least 0.001m",
        "Coordinates in [-100,100]m; palette has 1..16 keys; all terminal regions are validated",
        "The lower outgoing-edge region owns each fixed-diagonal strip pair; endpoints alone carry caps",
        "Complete source and delivered surfaces reject crossings, pinches, touching and folded overlaps",
        "Visual geometry adds no physical matter, collision or motion authority"]
    for kind, name, signature, description in [
        ("type", "PolygonSection", "PolygonSection",
         "An immutable order, station and keyed ring collection with a stable enclosing section key."),
        ("builtin", "polygon_section",
         "polygon_section(order: Int, station: Length, rings: Keyed<PolygonRing>) -> PolygonSection",
         "Author one section with exact ring and vertex correspondence to every other section."),
        ("builtin", "loft_rings",
         "loft_rings(sections: Keyed<PolygonSection>, palette: Keyed<SurfaceMaterial>, bottom_region: String, top_region: String) -> Geometry",
         "Construct a closed triangular surface between matched polygon sections."),
    ]:
        if check is not None:
            check()
        result["items"].append(_entry(kind, name, signature, description,
            capability="source_polygon_lofts", profile=RING_LOFT_PROFILE,
            specification=ADOPTION, domains=domains, examples=[EXAMPLE]))
    result["items"].append(_entry("capability", "source_polygon_lofts", "source_polygon_lofts",
        "Editable tapered housings, chamfered profiles and hollow ducts from reusable matched sections.",
        capability="source_polygon_lofts", profile=RING_LOFT_PROFILE, specification=ADOPTION))
    if linked_program is not None:
        if linked_program.entry.ast.profile != RING_LOFT_PROFILE:
            raise ValueError("Ring loft discovery requires the admitted polygon-loft source profile.")
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
