"""Detached discovery for bounded disjoint keyed merge with collision refusal."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_merge_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION
from .keyed_filter_agent_catalog import _declarative_template as filter_template
from .keyed_filter_agent_catalog import interface as filter_interface
from .profile_capabilities import KEYED_MERGE_PROFILE


ADOPTION = "docs/language-design/keyed-merge-v0.1/ADOPTION.md"
EXAMPLES = ["examples/keyed-merge/panel-task.files.json",
            "examples/keyed-merge/panel-identity.files.json",
            "examples/keyed-merge/singleton-pair.files.json"]


def interface(policy=None, *, aggregate_limits=None):
    result = filter_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.17",
        profile=KEYED_MERGE_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="KeyedMergeAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.17",
        request_schema="docs/language-design/agent-v0.17/request.schema.json",
        response_schema="docs/language-design/agent-v0.17/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.17 --output MODEL.glb",
        adoption=ADOPTION,
        merge_provenance={"value_field": "derived_merges", "generated_input_field": "input_merges",
            "ordering": "Left inherited aggregates, right inherited aggregates, then current both; generated entries append contributing origins with exact-record deduplication",
            "locations": ["expression", "left", "right"],
            "types": ["element_type"], "input_sides": ["both", "left", "right"], "writable": False})
    result["source_expressions"]["merge_keyed"] = {
        "syntax": "merge_keyed<T>(left, right)",
        "input": "Two flat Keyed<T> values with the same exact resolved element type and no boundary conversion",
        "output": "The immutable disjoint union in canonical ASCII key order with detached typed values",
        "input_order": "Evaluate and fully admit left once, then right once",
        "collision": "Refuse the lowest shared ASCII key even when the values are equal, before disjoint-result overflow",
        "max_entries": 256,
        "static_check": "Both operands are pure, typed and access-checked left then right before dynamic work",
        "leaf_families": list(result["source_expressions"]["reduce_keyed"]["leaf_families"]),
        "cancellation_stages": ["keyed_merge_collision", "keyed_merge_iteration"],
        "authority": "No new effects or physical authority; actual dependencies and taints of both inputs survive even empty output"}
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(filter_template())
    result.update(schema_version="ontokin.agent-catalog/0.17", language_version="0.17",
        profile=KEYED_MERGE_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.17"; module Example @ "example"; profile "keyed-merge-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], KEYED_MERGE_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_filter_examples={"language_version": "0.16",
            "paths": ["examples/keyed-filter/panel-task.files.json"]},
        example_context="The .17 manifests explicitly select merge; inherited examples retain their bindings.")
    result["limits"].update(max_keyed_entries=256, max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=KEYED_MERGE_PROFILE, specification=ADOPTION,
                signature="KeyedMergeAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic source repair and bounded disjoint keyed merge under current host authority.",
                domains=["Explicit source/Agent/GLB .17; bundle/files .2 and twelve operations are unchanged",
                    "Both actual inputs retain their dependencies and taints, including empty collections",
                    "Source/member keys and exact revision preconditions remain repair authority",
                    "Accepted source, persistent stores and artifacts never grant future execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=KEYED_MERGE_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.17 with complete source and immutable image identity.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Equivalent explicit .16 controls retain complete geometry and motion streams",
                    "Source/profile/revision and detached merge provenance identify the .17 program",
                    "No live destination physics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.17 requires ontokin.bundle/0.2."
    result["items"].append(_entry("builtin", "merge_keyed",
        "merge_keyed<T>(left: Keyed<T>, right: Keyed<T>) -> Keyed<T>",
        "Combine disjoint immutable keyed inputs while refusing every shared key.",
        capability="pure_keyed_merges", profile=KEYED_MERGE_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["Each operand is evaluated and fully admitted once, left before right",
            "Each input and the result have at most 256 entries of the 24 inherited immutable leaf families",
            "The lowest shared ASCII key refuses before disjoint union overflow",
            "Collision lookup, canonical ordering, copying and provenance are bounded and cancellable",
            "Aggregate and contributing origins remain detached and read-only"]))
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
    result["keyed_merge_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != KEYED_MERGE_PROFILE:
            raise ValueError("Keyed merge discovery requires the admitted .17 source profile.")
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
