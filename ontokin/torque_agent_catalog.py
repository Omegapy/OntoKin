"""Explicit finite torque discovery with inherited declaring-unit semantics."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_membership_agent_catalog import _declarative_template as membership_template
from .keyed_membership_agent_catalog import interface as membership_interface
from .profile_capabilities import TORQUE_PROFILE
from .torque_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION


ADOPTION = "docs/language-design/torque-v0.1/ADOPTION.md"
EXAMPLES = ["docs/language-design/torque-v0.1/freeze/p01-spin-up.files.json",
            "docs/language-design/torque-v0.1/freeze/p03-braking-reversal.files.json",
            "docs/language-design/torque-v0.1/freeze/p14-offset-reversal.files.json"]
STAGES = ("torque_source", "torque_boundary_scan", "torque_completion",
          "torque_activation", "torque_impulse_axis", "torque_aggregate_begin",
          "torque_aggregate_term", "torque_aggregate_publish", "torque_reference_origin",
          "torque_rotation_anchor", "torque_segment", "torque_segment_vertex",
          "torque_projection", "torque_boundary_commit")


def torque_interface():
    return {
        "schema_version": "ontokin.torque-interface/0.1", "source_version": "0.22",
        "profile": TORQUE_PROFILE, "agent_protocol": SCHEMA_VERSION,
        "target_contract": DEFINITION.destination,
        "statement": "torque <target> @ <stable_key> about <world_x|world_y|world_z> using <Torque> for <Time>;",
        "axes": ["world_x", "world_y", "world_z"], "rotation_phase_limit_rad": 1048576,
        "status": "experimental",
        "mechanics": "free homogeneous own sphere; external world-axis couple; signed scalar; sticky axis; fixed rigid massless marker delivery",
        "work_stages": list(STAGES),
        "authority": "current host ceilings and reducing caller caps; original shared deadline and cancellation callback",
        "unsupported": ["arbitrary_axis", "compound_inertia", "nonspherical_body", "reaction_motor",
                        "contacts", "affected_articulated_delivery", "live_engine_physics"]}


def interface(policy=None, *, aggregate_limits=None):
    result = membership_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.22", profile=TORQUE_PROFILE,
        delivery_contract=DEFINITION.destination, storage_schema=DEFINITION.store_schema,
        store_filename=DEFINITION.store_filename,
        transport="TorqueAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.22",
        request_schema="docs/language-design/agent-v0.22/request.schema.json",
        response_schema="docs/language-design/agent-v0.22/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.22 --output MODEL.glb",
        adoption=ADOPTION)
    concat = result["source_expressions"]["string_concat"]
    concat["declaring_versions"].append("0.22")
    concat["declaring_profiles"].append(TORQUE_PROFILE)
    concat["inherited_in_declaring_profile"] = TORQUE_PROFILE
    concat["cache_behavior"] = "No folding or value-cache bypass of executed String addition; inherited immutable member reads keep their meanings"
    membership = result["source_expressions"]["has_key"]
    membership.update(declaring_versions=["0.21", "0.22"],
        declaring_profiles=["keyed-membership-0.1", TORQUE_PROFILE],
        inherited_in_declaring_profile=TORQUE_PROFILE,
        declaring_boundary="Bare has_key is reserved in declaring .21 and .22 units; older imported lexical contexts retain their rules")
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(membership_template())
    result.update(schema_version="ontokin.agent-catalog/0.22", language_version="0.22",
        profile=TORQUE_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.22"; module Example @ "example"; profile "torque-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], TORQUE_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        example_context="Explicit .22 torque examples; inherited examples retain their original source bindings.")
    result["limits"]["max_request_bytes"] = MAX_REQUEST_BYTES
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=TORQUE_PROFILE, specification=ADOPTION,
                signature="TorqueAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Source-owned finite torque, immutable source repair and bounded recorded delivery.",
                domains=["Explicit source/Agent/GLB .22; bundle/files .2 and all twelve operations retain their transport shapes",
                    "Torque changes only through an accepted source revision and an ordered event sequence",
                    "Current host ceilings and reducing caller caps govern the original shared ledger",
                    "Saved requests, accepted source, reopened stores and artifacts grant no fresh authority",
                    "Sticky axis, exact clocks, whole-boundary rollback and complete interval histories remain inspectable"])
        elif item["kind"] == "destination":
            item.update(profile=TORQUE_PROFILE, specification=ADOPTION, name=DEFINITION.destination,
                capability=DEFINITION.destination, signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded finite torque with source-bound states, acceleration-aware error proof and exact immutable image bytes.",
                domains=["Explicit controlled .22 destination; the .6-only wrapper remains distinct",
                    "Free own spheres with fixed rigid massless markers; affected articulated paths are refused",
                    "Exact boundaries, complete source/state identity and independent supplied-byte validation",
                    "No live destination physics, general rigid dynamics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.22 requires ontokin.bundle/0.2."
        elif item["name"] == "has_key":
            item.update(profile=TORQUE_PROFILE)
            item["domains"][0] = "Ordinary call in a declaring .21 or .22 unit; both arguments evaluate eagerly left to right"
        elif item["name"] == "String + String":
            item.update(profile=TORQUE_PROFILE)
            item["domains"][0] = "Declaring source .20, .21 or .22; earlier imported expressions retain their original meaning"
    for kind, name, signature, description, capability in (
        ("event", "torque", torque_interface()["statement"],
         "Apply one signed finite Cartesian world-axis external couple through authoritative source.", "source_torque_intervals"),
        ("projection", "state.torques", 'inspect(..., fields=["state"]) -> state.torques',
         "Complete interval histories, sticky axis, split rotation anchor, scalar acceleration and rational error bounds.", "bounded_torque_state")):
        result["items"].append(_entry(kind, name, signature, description, capability=capability,
            profile=TORQUE_PROFILE, specification=ADOPTION, examples=EXAMPLES,
            domains=["Explicit experimental .22 binding only", "Source/program closure and original repair spans remain authoritative",
                     "Exact clocks and complete bounded histories; no truncated successful projection"]))
    result.pop("revision", None)
    result.pop("program_context", None)
    measure_json(result)
    return json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


_DECLARATIVE_JSON = _declarative_template()


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    from .construction_catalog import _Budget, _public_interfaces
    budget = _Budget(check)
    budget.step()
    result = json.loads(_DECLARATIVE_JSON)
    budget.charge(result)
    current = interface(policy, aggregate_limits=aggregate_limits)
    budget.charge(current)
    result["keyed_membership_interface"] = current
    result["torque_interface"] = torque_interface()
    budget.charge(result["torque_interface"])
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != TORQUE_PROFILE:
            raise ValueError("Torque discovery requires the admitted .22 source profile.")
        result["program_context"] = {"program_revision": linked_program.bundle.program_revision,
            "state": "linked declarations; no evaluated output claimed",
            "source_manifest": linked_program.bundle.manifest()}
        budget.charge(result["program_context"])
        for entry, node in _public_interfaces(linked_program, budget, source_profiles=True):
            budget.charge(entry, node)
            result["items"].append(entry)
    measure_json(result, check=check)
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    result["revision"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    return result
