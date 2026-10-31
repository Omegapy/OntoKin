"""Discover editable blind pockets and retain earlier geometry meanings."""
from __future__ import annotations

import hashlib
import json

from .framed_loft_agent_catalog import catalog as framed_catalog
from .framed_loft_agent_catalog import interface as framed_interface
from .json_limits import measure_json
from .pockets_protocol import DEFINITION, SCHEMA_VERSION
from .profile_capabilities import POCKETS_PROFILE


ADOPTION = "docs/language-design/polygon-pockets-v0.1/ADOPTION.md"
EXAMPLE = "examples/polygon-pockets/rectangular-pocket.ok"


def interface(policy=None, *, aggregate_limits=None):
    result = framed_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.12",
        profile=POCKETS_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema,
        transport="PocketsAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.12",
        request_schema="docs/language-design/agent-v0.12/request.schema.json",
        response_schema="docs/language-design/agent-v0.12/response.schema.json",
        adoption=ADOPTION,
        single_source_command="export SOURCE.ok --target ontokin.glb/0.12 --output MODEL.glb",
        source_constructors=[*result["source_constructors"], "polygon_pocket", "extrude_pockets"],
        polygon_pockets_limits={"min_pockets": 0, "max_pockets": 8,
            "min_vertices_per_boundary": 3, "max_total_vertices": 64,
            "min_order": 0, "max_order": 65535,
            "max_planar_coordinate_abs_m": 100,
            "min_height_m": 0.001, "max_height_m": 100,
            "min_depth_m": 0.001, "max_depth_m": 100,
            "min_exact_remaining_base_m": 0.001,
            "max_palette_keys": 16, "max_logical_vertices": 128,
            "max_triangles": 252, "max_corners": 756},
        surface_rule="deterministic-prismatic-pocket-boundary",
        pocket_floor_rule="exact-rational-subtract-single-binary64-round",
        pocket_depth_meaning="authored_depth_distinct_from_rounded_floor_effective_depth",
        zero_pocket_equivalence="unchanged-simple-extrusion-local-streams",
        pocket_winding={"outer": "counterclockwise", "pockets": "clockwise"},
        pocket_identity=["boundary_kind", "boundary_key", "vertex_key", "level"],
        polygon_exclusions=["touching_or_intersecting_boundaries", "nested_pockets",
            "penetrating_depths", "insufficient_remaining_base", "branching_cavities",
            "arbitrary_boolean_operations", "bevels", "deformation",
            "implicit_mass_or_inertia_or_collision", "live_destination_physics"])
    return result


def _declarative_template():
    """Materialize source-owned documentation once, without request state.

    As with construction_catalog's static profile definitions, this template
    contains only versioned language metadata. The old operational interfaces
    are removed; no policy, aggregate service limits, linked source, evaluation
    result, accepted revision or execution receipt survives in the template.
    """
    from .construction_catalog import _entry
    result = framed_catalog(policy=None)
    compatible = [*result["compatible_definition_profiles"], POCKETS_PROFILE]
    inherited_examples = result["complete_examples"]
    inherited_interface = result.pop("framed_polygon_loft_interface")
    inherited_ring_interface = result.pop("inherited_polygon_loft_interface")
    # The current interface already carries the inherited constructors and
    # limits. Retain links to previous bindings without publishing their entire
    # repeated operation, policy, budget and transport descriptions again.
    reference_fields = ("language_version", "profile", "agent_contract",
        "delivery_contract", "request_schema", "response_schema", "adoption")
    inherited_interfaces = []
    for previous in (inherited_ring_interface, inherited_interface):
        reference = {}
        for key in reference_fields:
            reference[key] = previous[key]
        inherited_interfaces.append(reference)

    def selectors(value):
        if isinstance(value, dict):
            return {key: selectors(item) for key, item in value.items()}
        if isinstance(value, list):
            return [selectors(item) for item in value]
        if isinstance(value, str):
            # Change operational selectors without rewriting older declarations
            return (value.replace("ontokin.agent/0.11", SCHEMA_VERSION)
                .replace("ontokin.glb/0.11", DEFINITION.destination)
                .replace("FramedLoftAgentService", "PocketsAgentService")
                .replace("framed-loft-program-agent.sqlite3", DEFINITION.store_filename)
                .replace("ontokin.framed-loft-program-agent-store/0.1", DEFINITION.store_schema))
        return value

    # Only transport records change their operational selectors. Source
    # declarations and examples need no recursive copy or replacement pass.
    result.update(schema_version="ontokin.agent-catalog/0.12", language_version="0.12",
        profile=POCKETS_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination],
        inherited_geometry_interfaces=inherited_interfaces,
        source_header='ontokin "0.12"; module Example @ "example"; profile "polygon-pockets-0.1";',
        compatible_definition_profiles=compatible, complete_examples=[EXAMPLE],
        inherited_framed_loft_examples={"language_version": "0.11", "paths": inherited_examples},
        example_context="The .12 pocket example is complete source. Inherited examples retain their declared source bindings.",
        adoption=ADOPTION)
    result["limits"].update(max_polygon_pockets=8, max_pockets_total_vertices=64,
        max_pockets_logical_vertices=128, max_pockets_triangles=252, max_pockets_corners=756)
    for index, item in enumerate(result["items"]):
        if (item["kind"] in ("protocol", "destination")
                or item["name"] == "persistent_agent_editing_service"):
            item = selectors(item)
            result["items"][index] = item
        if item["kind"] == "protocol":
            item.update(profile=POCKETS_PROFILE, specification=ADOPTION,
                domains=["Explicit source 0.12 / polygon-pockets-0.1 and a separate Agent/0.12 store",
                    "Current trusted host authority, one cumulative counter and the original deadline",
                    "Exact source edits, immutable accepted revisions, rollback and durable retries",
                    "All twelve inherited operations; derived triangles are inspection data"],
                description="Blind polygon pockets, exact floor arithmetic, scoped depth repair and recorded delivery.")
        elif item["kind"] == "destination":
            item.update(profile=POCKETS_PROFILE, specification=ADOPTION, examples=[EXAMPLE],
                domains=["Explicit source 0.12 and recorded GLB/0.12",
                    "Perforated top, closed exterior bottom and explicit positive-depth pocket floors",
                    "Actual binary32 positions preserve identities, complete topology and cap orientation",
                    "Recorded carrier motion; Unreal import and live destination physics remain unverified"])
        elif item["name"] == "Geometry" and item["kind"] == "type":
            item.update(description="Immutable primitives and native surfaces, including blind polygon pockets.",
                        specification=ADOPTION)
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["element_types"].append("PolygonPocket")
            item["domains"].append("Source .12 adds immutable PolygonPocket values with keyed vertices, authored depth and a floor region")
        elif item["name"] == "placed":
            item.update(specification=ADOPTION,
                description="Apply one rigid local visual placement to one unplaced native surface.",
                domains=[*item["domains"],
                    "Source .12 additionally accepts pocket bodies with the same one-time carrier-frame placement"])
        elif item["name"] == "geometry.surface":
            item.update(profile=POCKETS_PROFILE, specification=ADOPTION,
                description="Bounded keyed pocket boundaries, exact depth arithmetic, material domains and visual placement.",
                summary_contracts=[*item["summary_contracts"], "ontokin.polygon-pockets-summary/0.1"],
                domains=[*item["domains"],
                    "Pocket summaries distinguish authored depth, exact remaining base, rounded floor and effective geometric depth",
                    "Pocket summaries retain sorted outer/pocket vertices and separate bottom, top, floor and wall counts",
                    "Earlier geometry families retain their original summary fields and meanings"])
        elif item["name"] == "surface.mesh_page":
            item.update(profile=POCKETS_PROFILE, specification=ADOPTION,
                domains=["Agent/0.12 pages identify polygon-pockets-0.1, including inherited geometry occurrences",
                    "Revision, occurrence, region, geometry, implementation and protocol bind every cursor",
                    "At most 256 triangles per page; derived indices are read-only inspection identities"])

    domains = ["Zero through eight keyed pockets; at least three vertices per boundary and at most 64 overall",
        "Counterclockwise exterior and clockwise pocket boundaries are strictly disjoint and nonnested",
        "Canonical binary64 XY components lie within [-100,100] meters; height and depths are in [0.001,100] meters",
        "Exact height-minus-depth must leave at least canonical binary64 0.001 meter of base",
        "Each completed exact base is rounded once; actual geometry uses that floor and its resulting effective depth",
        "Pocket order and vertex order determine emission; declaration order and key spelling do not",
        "Outgoing vertex regions own wall faces; every pocket names its own floor material",
        "Zero-pocket local position, normal and material-index streams match the earlier simple extrusion",
        "Complete source and delivered surfaces reject collapse, crossing, pinching and forbidden contact",
        "Visual geometry adds no physical matter, collision shape or motion authority"]
    for kind, name, signature, description in [
        ("type", "PolygonPocket", "PolygonPocket",
         "An immutable explicit order, clockwise keyed boundary, authored depth and floor material region."),
        ("builtin", "polygon_pocket",
         "polygon_pocket(order: Int, vertices: Keyed<PolygonVertex>, depth: Length, floor_region: String) -> PolygonPocket",
         "Author one blind recess boundary and the depth of its interior floor."),
        ("builtin", "extrude_pockets",
         "extrude_pockets(outer_vertices: Keyed<PolygonVertex>, pockets: Keyed<PolygonPocket>, palette: Keyed<SurfaceMaterial>, height: Length, bottom_region: String, top_region: String) -> Geometry",
         "Construct one closed body with separately authored blind pockets and positive remaining base."),
    ]:
        result["items"].append(_entry(kind, name, signature, description,
            capability="source_polygon_pockets", profile=POCKETS_PROFILE,
            specification=ADOPTION, domains=domains, examples=[EXAMPLE]))
    result["items"].append(_entry("capability", "source_polygon_pockets", "source_polygon_pockets",
        "Editable recessed trays, panels and housings with explicit interior floors.",
        capability="source_polygon_pockets", profile=POCKETS_PROFILE, specification=ADOPTION))
    result.pop("revision", None)
    result.pop("program_context", None)
    measure_json(result)
    return json.dumps(result, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


# Immutable source-derived JSON text, never a retained discovery result.
_DECLARATIVE_JSON = _declarative_template()


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    from .construction_catalog import _Budget, _public_interfaces
    budget = _Budget(check)
    budget.step()
    # Parse a fresh bounded copy, then charge every actual materialized entry.
    # The final JSON walk and both publication guards remain unchanged.
    result = json.loads(_DECLARATIVE_JSON)
    budget.charge(result)
    current_interface = interface(policy, aggregate_limits=aggregate_limits)
    budget.charge(current_interface)
    result["polygon_pockets_interface"] = current_interface
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != POCKETS_PROFILE:
            raise ValueError("Pocket discovery requires the admitted polygon-pockets source profile.")
        result["program_context"] = {"program_revision": linked_program.bundle.program_revision,
            "state": "linked declarations; no evaluated output claimed",
            "source_manifest": linked_program.bundle.manifest()}
        budget.charge(result["program_context"])
        for entry, node in _public_interfaces(linked_program, budget, source_profiles=True):
            budget.charge(entry, node)
            result["items"].append(entry)
    result.pop("revision", None)
    measure_json(result, check=check)
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    result["revision"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    return result
