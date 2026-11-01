"""Detached discovery for bounded, strict Boolean keyed filtering."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_filter_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION
from .keyed_reduction_agent_catalog import _declarative_template as reduction_template
from .keyed_reduction_agent_catalog import interface as reduction_interface
from .profile_capabilities import KEYED_FILTER_PROFILE


ADOPTION = "docs/language-design/keyed-filter-v0.1/ADOPTION.md"
EXAMPLES = ["examples/keyed-filter/panel-task.files.json",
            "examples/keyed-filter/panel-identity.files.json",
            "examples/keyed-filter/singleton-keep.files.json"]


def interface(policy=None, *, aggregate_limits=None):
    result = reduction_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.16",
        profile=KEYED_FILTER_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="KeyedFilterAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.16",
        request_schema="docs/language-design/agent-v0.16/request.schema.json",
        response_schema="docs/language-design/agent-v0.16/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.16 --output MODEL.glb",
        adoption=ADOPTION,
        filter_provenance={"value_field": "derived_filters", "generated_input_field": "input_filters",
            "ordering": "Unique actual input and selected-predicate derivations before the current filter",
            "locations": ["expression", "input", "predicate"],
            "types": ["element_type"], "writable": False})
    result["source_expressions"]["filter_keyed"] = {
        "syntax": "filter_keyed<T>(input, (key, value) -> predicate)",
        "input": "One admitted flat Keyed<T> with the exact resolved element type and no boundary conversion",
        "output": "An immutable subset retaining each original key and typed value",
        "predicate": "Strict Bool, executed once per entry in canonical ASCII key order",
        "max_entries": 256,
        "static_check": "Pure, typed and access-checked even when empty; enclosing local payloads are masked",
        "leaf_families": list(result["source_expressions"]["reduce_keyed"]["leaf_families"]),
        "cancellation_stage": "keyed_filter_iteration",
        "authority": "No new effects or physical authority; every actual read and taint survives dropped entries"}
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(reduction_template())
    result.update(schema_version="ontokin.agent-catalog/0.16", language_version="0.16",
        profile=KEYED_FILTER_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.16"; module Example @ "example"; profile "keyed-filter-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], KEYED_FILTER_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_reduction_examples={"language_version": "0.15",
            "paths": ["examples/keyed-reduction/panel-task.files.json"]},
        example_context="The .16 manifests explicitly select filtering; inherited examples retain their bindings.")
    result["limits"].update(max_keyed_entries=256, max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=KEYED_FILTER_PROFILE, specification=ADOPTION,
                signature="KeyedFilterAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic source repair and bounded keyed filtering under current host authority.",
                domains=["Explicit source/Agent/GLB .16; bundle/files .2 and twelve operations are unchanged",
                    "Every actual input and predicate dependency survives dropped entries and empty output",
                    "Source/member keys and exact revision preconditions remain repair authority",
                    "Accepted source, persistent stores and artifacts never grant future execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=KEYED_FILTER_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.16 with complete source and immutable image identity.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Equivalent explicit .15 controls retain complete geometry and motion streams",
                    "Source/profile/revision and detached filter provenance identify the .16 program",
                    "No live destination physics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.16 requires ontokin.bundle/0.2."
    result["items"].append(_entry("builtin", "filter_keyed",
        "filter_keyed<T>(input: Keyed<T>, (key: String, value: T) -> predicate: Bool) -> Keyed<T>",
        "Select an immutable keyed subset without changing surviving keys or typed values.",
        capability="pure_keyed_filters", profile=KEYED_FILTER_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["Input is evaluated and admitted once before predicate traversal",
            "At most 256 entries of the 24 inherited immutable leaf families",
            "The predicate is checked statically even when empty and executes once per actual entry",
            "Traversal, bindings, predicate work, copies and provenance remain bounded and cancellable",
            "Actual dropped-entry reads and taints remain; derivations are detached and read-only"]))
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
    result["keyed_filter_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != KEYED_FILTER_PROFILE:
            raise ValueError("Keyed filter discovery requires the admitted .16 source profile.")
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
