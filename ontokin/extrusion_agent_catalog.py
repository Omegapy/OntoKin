"""Discovery for source-authored polygons and the explicit Agent/0.8 binding."""
from __future__ import annotations

import hashlib
import json

from .budget_agent_catalog import catalog as budget_catalog, interface as budget_interface
from .extrusion_protocol import SCHEMA_VERSION, DEFINITION
from .json_limits import measure_json
from .profile_capabilities import BUDGET_PROFILE, EXTRUSION_PROFILE


ADOPTION = "docs/language-design/polygon-extrusion-v0.1/ADOPTION.md"
EXAMPLE = "examples/polygon-extrusions/concave-bracket.ok"


def interface(policy=None, *, aggregate_limits=None):
    result = budget_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.8",
        profile=EXTRUSION_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema,
        transport="ExtrusionAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.8",
        request_schema="docs/language-design/agent-v0.8/request.schema.json",
        response_schema="docs/language-design/agent-v0.8/response.schema.json",
        adoption=ADOPTION,
        single_source_command="export SOURCE.ok --target ontokin.glb/0.8 --output MODEL.glb",
        source_constructors=["planar_point", "polygon_vertex", "extrude", "placed"],
        polygon_limits={"min_vertices": 3, "max_vertices": 64,
            "min_order": 0, "max_order": 65535, "max_coordinate_abs_m": 100,
            "min_depth_m": 0.001, "max_depth_m": 100, "max_palette_keys": 16},
        polygon_exclusions=["holes", "self_intersection", "bevels",
                            "implicit_mass_or_inertia", "live_destination_physics"])
    return result


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    from .construction_catalog import _Budget, _entry, _public_interfaces
    result = budget_catalog(policy=policy, check=check, aggregate_limits=aggregate_limits)
    compatible = result["compatible_definition_profiles"] + [EXTRUSION_PROFILE]
    inherited_examples = result["complete_examples"]

    def convert(value):
        if check is not None:
            check()
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, str):
            return (value.replace(BUDGET_PROFILE, EXTRUSION_PROFILE)
                    .replace("ontokin.agent/0.7", SCHEMA_VERSION)
                    .replace("ontokin.glb/0.7", DEFINITION.destination)
                    .replace("BudgetAgentService", "ExtrusionAgentService")
                    .replace("budget-program-agent.sqlite3", DEFINITION.store_filename)
                    .replace("ontokin.budget-program-agent-store/0.1", DEFINITION.store_schema))
        return value

    result = convert(result)
    result.pop("budget_agent_interface", None)
    result.update(schema_version="ontokin.agent-catalog/0.8", language_version="0.8",
        profile=EXTRUSION_PROFILE, polygon_extrusion_interface=interface(policy, aggregate_limits=aggregate_limits),
        source_header='ontokin "0.8"; module Example @ "example"; profile "polygon-extrusion-0.1";',
        compatible_definition_profiles=compatible, complete_examples=[EXAMPLE],
        inherited_execution_budget_examples={"language_version": "0.7", "paths": inherited_examples},
        example_context="The .8 polygon example is complete source. Earlier examples retain their declared language bindings.",
        adoption=ADOPTION)
    result["limits"].update(min_polygon_vertices=3, max_polygon_vertices=64,
        min_polygon_order=0, max_polygon_order=65535, max_polygon_coordinate_abs_m=100,
        min_extrusion_depth_m=0.001, max_extrusion_depth_m=100,
        max_extrusion_triangles=252, max_extrusion_corners=756)
    for item in result["items"]:
        if check is not None:
            check()
        if item["kind"] == "protocol":
            item.update(specification=ADOPTION,
                domains=["Explicit source 0.8 / polygon-extrusion-0.1 and its separate Agent/0.8 store",
                         "Current host authority and one cumulative execution ledger per request",
                         "Exact file source scopes, immutable revisions and atomic failed-edit rollback",
                         "All twelve budget Agent operations; derived mesh corners are not writable source keys"],
                description="Authored polygon construction, inspection, repair and recorded delivery under source-requested budgets.")
        elif item["kind"] == "destination":
            item.update(specification=ADOPTION, examples=[EXAMPLE],
                domains=["Explicit source 0.8 and recorded GLB/0.8",
                         "Source-generated polygon positions, outward flat normals and actual regional PBR primitives",
                         "Binary32 collapse, wrong winding and excess geometric error reject delivery",
                         "Recorded world carrier motion; no live destination physics"])
        elif item["name"] == "Geometry" and item["kind"] == "type":
            item.update(description="Immutable primitive, native loft or source-authored polygon extrusion geometry.",
                        specification=ADOPTION)
        elif item["name"] == "Keyed" and item["kind"] == "type":
            item["element_types"] += ["PlanarPoint", "PolygonVertex"]
            item["domains"].append("PlanarPoint and PolygonVertex are immutable leaves only in source .8 declarations")
        elif item["name"] == "placed":
            item.update(specification=ADOPTION,
                description="Apply one rigid local visual transform to an unplaced native loft or polygon extrusion.",
                domains=["Source .8 permits one unplaced loft or extrusion; primitives and nested placements reject",
                         "Pose references the carrier's self.frame; no scale, shear, reflection or extra motion authority"])
        elif item["name"] == "geometry.surface":
            item.update(specification=ADOPTION,
                description="Bounded source geometry summary for an authored loft or polygon extrusion.",
                summary_contracts=["ontokin.surface-summary/0.1", "ontokin.polygon-extrusion-summary/0.1"],
                domains=["Loft summaries keep the original section semantics",
                         "Polygon summaries expose stable vertex keys, explicit orders, planar points, depth and cap regions",
                         "Derived corners and triangle buffers require bounded mesh-page inspection"])
            item.pop("summary_contract", None)
        elif item["name"] == "surface.mesh_page":
            item["specification"] = ADOPTION
            item["domains"] = [domain for domain in item["domains"]
                               if "profile remains surface-0.1" not in domain and "entry_profile=" not in domain]
            item["domains"].append("Agent/0.8 mesh pages explicitly identify polygon-extrusion-0.1, including inherited loft occurrences")

    declarations = [
        ("type", "PlanarPoint", "PlanarPoint", "An immutable pair of local XY Length coordinates."),
        ("type", "PolygonVertex", "PolygonVertex", "An immutable order, planar point and side-region value with an authored enclosing key."),
        ("builtin", "planar_point", "planar_point(x: Length, y: Length) -> PlanarPoint", "Define one planar point in canonical meters."),
        ("builtin", "polygon_vertex", "polygon_vertex(order: Int, point: PlanarPoint, side_region: String) -> PolygonVertex", "Order an authored vertex and name its outgoing edge material."),
        ("builtin", "extrude", "extrude(vertices: Keyed<PolygonVertex>, palette: Keyed<SurfaceMaterial>, depth: Length, bottom_region: String, top_region: String) -> Geometry", "Build a closed +Z extrusion from a simple counterclockwise polygon."),
    ]
    for kind, name, signature, description in declarations:
        if check is not None:
            check()
        result["items"].append(_entry(kind, name, signature, description,
            capability="source_polygon_extrusions", profile=EXTRUSION_PROFILE, specification=ADOPTION,
            domains=["3..64 ordered vertices, coordinates within [-100,100]m and depth within [0.001,100]m",
                     "Unique orders 0..65535; declaration and key order do not determine traversal",
                     "Exact geometric predicates reject crossing, touching, duplicate and collinear degeneracies",
                     "Closed caps and flat outward triangles; geometry adds no physical matter"],
            examples=[EXAMPLE]))
    result["items"].append(_entry("capability", "source_polygon_extrusions", "source_polygon_extrusions",
        "Reusable source-authored plates and concave brackets with exact source repair.",
        capability="source_polygon_extrusions", profile=EXTRUSION_PROFILE, specification=ADOPTION))
    if linked_program is not None:
        if linked_program.entry.ast.profile != EXTRUSION_PROFILE:
            raise ValueError("Polygon discovery requires the admitted polygon source profile.")
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
