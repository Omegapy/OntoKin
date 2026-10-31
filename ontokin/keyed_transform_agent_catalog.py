"""Bounded discovery for the explicit key-preserving source expression."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_transform_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION
from .profile_capabilities import KEYED_TRANSFORM_PROFILE
from .texture_agent_catalog import _declarative_template as texture_template
from .texture_agent_catalog import interface as texture_interface


ADOPTION = "docs/language-design/keyed-transform-v0.1/ADOPTION.md"
EXAMPLES = ["examples/keyed-transform/panel-task.files.json",
            "examples/keyed-transform/panel-identity.files.json",
            "examples/keyed-transform/singleton-length.files.json"]


def interface(policy=None, *, aggregate_limits=None):
    result = texture_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.14",
        profile=KEYED_TRANSFORM_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="KeyedTransformAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.14",
        request_schema="docs/language-design/agent-v0.14/request.schema.json",
        response_schema="docs/language-design/agent-v0.14/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.14 --output MODEL.glb",
        adoption=ADOPTION,
        source_expressions={"map_keyed": {
            "syntax": "map_keyed<Out>(input, (key, value) -> body)",
            "input": "One already represented flat Keyed<T>, evaluated once",
            "output": "Keyed<Out> with identical keys and cardinality in canonical ASCII order",
            "max_entries": 256,
            "body": "Pure, typed and access-checked even for empty input; exact output type and units",
            "authority": "Read-only derived values; source/member spans remain repair authority"}},
        transform_provenance={
            "value_field": "derived_transforms", "generated_input_field": "input_transforms",
            "ordering": "Input transforms followed by the current transform; nested selected values retain their own keys",
            "locations": ["expression", "body", "input"],
            "types": ["input_element_type", "output_element_type"],
            "indexed_leaf": "Original stable key and actual input_entry location, or null when unknown",
            "writable": False})
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(texture_template())
    result.update(schema_version="ontokin.agent-catalog/0.14", language_version="0.14",
        profile=KEYED_TRANSFORM_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.14"; module Example @ "example"; profile "keyed-transform-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], KEYED_TRANSFORM_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_texture_examples={"language_version": "0.13",
            "paths": ["examples/textured-surfaces/rgb-panel.files.json",
                      "examples/textured-surfaces/marked-tray.files.json"]},
        example_context="The .14 manifests select map_keyed explicitly; inherited examples keep their original bindings.")
    result["limits"].update(max_keyed_entries=256, max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=KEYED_TRANSFORM_PROFILE, specification=ADOPTION,
                signature="KeyedTransformAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Scoped source repairs and immutable asset edits under the current host policy.",
                domains=["Explicit source/Agent/GLB .14 with unchanged bundle/files .2",
                    "All twelve operations; previous protocol defaults remain unchanged",
                    "Source transformations preserve original keys and read-only provenance",
                    "Durable retry identity; accepted source and artifacts never grant execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=KEYED_TRANSFORM_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.14 for the explicit .14 source profile.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Identity transforms preserve complete BIN streams against explicit .13 controls",
                    "Source/program and transform provenance bind the selected .14 program",
                    "No new physical authority; live destination physics and Unreal import remain unverified"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.14 requires ontokin.bundle/0.2."
    result["items"].append(_entry("builtin", "map_keyed",
        "map_keyed<Out>(input: Keyed<T>, (key: String, value: T) -> body: Out) -> Keyed<Out>",
        "Transform every existing keyed value without changing its stable key.",
        capability="key_preserving_transforms", profile=KEYED_TRANSFORM_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["Contextual source expression, not a first-class or higher-order callable",
            "Flat admitted element types, exact output units, at most 256 entries",
            "The complete body is checked for empty inputs without fabricated values",
            "One input evaluation and canonical key order; nested transforms share the current request ledger",
            "No filtering, rekeying, reduction, mutation or new geometric/physical authority"]))
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
    result["keyed_transform_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != KEYED_TRANSFORM_PROFILE:
            raise ValueError("Keyed transform discovery requires the admitted .14 source profile.")
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
