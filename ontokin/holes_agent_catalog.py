"""Discover editable outer and inner rings through explicit Agent/0.9."""
from __future__ import annotations

import hashlib
import json

from .extrusion_agent_catalog import catalog as extrusion_catalog
from .extrusion_agent_catalog import interface as extrusion_interface
from .holes_protocol import SCHEMA_VERSION, DEFINITION
from .json_limits import measure_json
from .profile_capabilities import EXTRUSION_PROFILE, HOLES_PROFILE


ADOPTION = "docs/language-design/polygon-holes-v0.1/ADOPTION.md"
EXAMPLE = "examples/polygon-holes/square-hole.ok"


def interface(policy=None, *, aggregate_limits=None):
    result = extrusion_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.9",
        profile=HOLES_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema,
        transport="HolesAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.9",
        request_schema="docs/language-design/agent-v0.9/request.schema.json",
        response_schema="docs/language-design/agent-v0.9/response.schema.json",
        adoption=ADOPTION,
        single_source_command="export SOURCE.ok --target ontokin.glb/0.9 --output MODEL.glb",
        source_constructors=["planar_point", "polygon_vertex", "polygon_ring", "extrude", "extrude_rings", "placed"],
        hole_limits={"min_rings": 1, "max_rings": 9, "min_holes": 0, "max_holes": 8,
            "min_vertices_per_ring": 3, "max_total_vertices": 64,
            "min_order": 0, "max_order": 65535, "max_coordinate_abs_m": 100,
            "min_depth_m": 0.001, "max_depth_m": 100, "max_palette_keys": 16,
            "max_triangles": 284, "max_corners": 852},
        polygon_exclusions=["self_intersection", "touching_rings", "nested_holes",
            "bevels", "arbitrary_boolean_operations", "implicit_mass_or_inertia",
            "live_destination_physics"])
    return result


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    from .construction_catalog import _Budget, _entry, _public_interfaces
    result = extrusion_catalog(policy=policy, check=check, aggregate_limits=aggregate_limits)
    compatible = result["compatible_definition_profiles"] + [HOLES_PROFILE]
    inherited_examples = result["complete_examples"]

    def convert(value):
        if check is not None:
            check()
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, str):
            return (value.replace(EXTRUSION_PROFILE, HOLES_PROFILE)
                    .replace("ontokin.agent/0.8", SCHEMA_VERSION)
                    .replace("ontokin.glb/0.8", DEFINITION.destination)
                    .replace("ExtrusionAgentService", "HolesAgentService")
                    .replace("extrusion-program-agent.sqlite3", DEFINITION.store_filename)
                    .replace("ontokin.extrusion-program-agent-store/0.1", DEFINITION.store_schema))
        return value

    result = convert(result)
    result.pop("polygon_extrusion_interface", None)
    result.update(schema_version="ontokin.agent-catalog/0.9", language_version="0.9",
        profile=HOLES_PROFILE, polygon_holes_interface=interface(policy, aggregate_limits=aggregate_limits),
        source_header='ontokin "0.9"; module Example @ "example"; profile "polygon-holes-0.1";',
        compatible_definition_profiles=compatible, complete_examples=[EXAMPLE],
        inherited_polygon_examples={"language_version": "0.8", "paths": inherited_examples},
        example_context="The .9 ring example is complete source. Earlier examples retain their declared bindings.",
        adoption=ADOPTION)
    result["limits"].update(min_polygon_rings=1, max_polygon_rings=9, max_polygon_holes=8,
        max_ring_extrusion_vertices=64, max_ring_extrusion_triangles=284,
        max_ring_extrusion_corners=852)
    for item in result["items"]:
        if check is not None:
            check()
        if item["kind"] == "protocol":
            item.update(specification=ADOPTION,
                domains=["Explicit source 0.9 / polygon-holes-0.1 and a separate Agent/0.9 store",
                         "Current host authority and one cumulative execution ledger per request",
                         "Exact file source scopes, immutable revisions and failed-edit rollback",
                         "All twelve inherited operations; derived mesh corners are inspection data"],
                description="Authored outer and inner rings, scoped repair and recorded delivery under source-requested budgets.")
        elif item["kind"] == "destination":
            item.update(specification=ADOPTION, examples=[EXAMPLE],
                domains=["Explicit source 0.9 and recorded GLB/0.9",
                         "Source-generated caps, outer walls, hole walls and regional PBR primitives",
                         "Binary32 collapse, touching openings, invalid cap coverage and excess error reject delivery",
                         "Recorded carrier motion; no live destination physics or Unreal Engine import claim"])
        elif item["name"] == "Geometry" and item["kind"] == "type":
            item.update(description="Immutable primitive, native loft, simple extrusion or ring extrusion geometry.",
                        specification=ADOPTION)
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["element_types"].append("PolygonRing")
            item["domains"] = [domain for domain in item["domains"]
                               if "PlanarPoint and PolygonVertex" not in domain]
            item["domains"].append("Source .9 adds immutable PolygonRing elements containing typed keyed PolygonVertex values")
        elif item["name"] == "placed":
            item.update(specification=ADOPTION,
                description="Apply one rigid local visual transform to an unplaced loft, simple extrusion or ring extrusion.",
                domains=["Source .9 accepts one native unplaced geometry; primitives and nested placements reject",
                         "Pose references the carrier's self.frame; no scale, shear or added motion authority"])
        elif item["name"] == "geometry.surface":
            item.update(specification=ADOPTION,
                description="Bounded source summary for a loft, simple extrusion or authored outer/inner rings.",
                summary_contracts=["ontokin.surface-summary/0.1", "ontokin.polygon-extrusion-summary/0.1",
                                   "ontokin.polygon-holes-summary/0.1"],
                domains=["Earlier loft and simple-extrusion summaries retain their schema meanings",
                         "Ring summaries expose stable ring and vertex keys, explicit orders, roles, points and outgoing materials",
                         "Derived corners and triangles require bounded revision-bound mesh-page inspection"])
        elif item["name"] == "surface.mesh_page":
            item["specification"] = ADOPTION
            item["domains"] = ["Agent/0.9 mesh pages identify polygon-holes-0.1, including inherited geometry occurrences",
                               "Revision, element, geometry, filter and cursor bindings remain mandatory",
                               "Derived triangle and corner indices are read-only inspection identities"]

    for kind, name, signature, description in [
        ("type", "PolygonRing", "PolygonRing", "An immutable role, order and keyed vertex sequence with an authored enclosing ring key."),
        ("builtin", "polygon_ring", "polygon_ring(order: Int, role: String, vertices: Keyed<PolygonVertex>) -> PolygonRing", "Define an outer or hole ring; vertex keys are scoped by that ring."),
        ("builtin", "extrude_rings", "extrude_rings(rings: Keyed<PolygonRing>, palette: Keyed<SurfaceMaterial>, depth: Length, bottom_region: String, top_region: String) -> Geometry", "Construct a closed extrusion with zero through eight source-authored openings."),
    ]:
        if check is not None:
            check()
        result["items"].append(_entry(kind, name, signature, description,
            capability="source_polygon_holes", profile=HOLES_PROFILE, specification=ADOPTION,
            domains=["Exactly one counterclockwise outer ring; zero through eight clockwise hole rings",
                     "At least three vertices per ring and at most 64 vertices across all rings",
                     "Role is outer or hole; unique explicit ring orders and per-ring vertex orders lie in 0..65535",
                     "Holes lie strictly inside the outer ring; crossings, touches, overlap and nesting reject",
                     "Coordinates within [-100,100]m; depth within [0.001,100]m; palette has 1..16 keys",
                     "Deterministic bounded exact triangulation; geometry adds no physical matter"],
            examples=[EXAMPLE]))
    result["items"].append(_entry("capability", "source_polygon_holes", "source_polygon_holes",
        "Editable openings, slotted brackets and hollow housing cross-sections from reusable source.",
        capability="source_polygon_holes", profile=HOLES_PROFILE, specification=ADOPTION))
    if linked_program is not None:
        if linked_program.entry.ast.profile != HOLES_PROFILE:
            raise ValueError("Hole discovery requires the admitted polygon-holes source profile.")
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
