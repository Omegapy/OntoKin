"""Detached discovery for bounded exact-key pair transformations."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_zip_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION
from .keyed_merge_agent_catalog import _declarative_template as merge_template
from .keyed_merge_agent_catalog import interface as merge_interface
from .profile_capabilities import KEYED_ZIP_PROFILE


ADOPTION = "docs/language-design/keyed-zip-v0.1/ADOPTION.md"
EXAMPLES = ["examples/keyed-zip/panel-task.files.json",
            "examples/keyed-zip/panel-identity.files.json",
            "examples/keyed-zip/singleton-add.files.json"]


def interface(policy=None, *, aggregate_limits=None):
    result = merge_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.18",
        profile=KEYED_ZIP_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="KeyedZipAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.18",
        request_schema="docs/language-design/agent-v0.18/request.schema.json",
        response_schema="docs/language-design/agent-v0.18/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.18 --output MODEL.glb",
        adoption=ADOPTION,
        zip_provenance={"value_field": "derived_zips", "generated_input_field": "input_zips",
            "ordering": "Normalized left, right and selected body aggregates, then current aggregate; selected output adds actual left/right/body contributors and current pair with exact-record deduplication",
            "locations": ["expression", "left", "right", "body"],
            "types": ["left_element_type", "right_element_type", "output_element_type"],
            "contributor_fields": ["key", "left_entry", "right_entry"],
            "aggregate": {"key": None, "left_entry": None, "right_entry": None},
            "entry_origin": "Original quoted-key-through-value entry span; primary key declaration follows the left input",
            "writable": False})
    result["source_expressions"]["zip_keyed"] = {
        "syntax": "zip_keyed<T, U, V>(left, right, (key, left_value, right_value) -> body)",
        "input": "Exact resolved Keyed<T> and Keyed<U> immutable inputs; no boundary widening",
        "output": "Exact body V yields detached Keyed<V> with the same complete stable keys",
        "input_order": "Evaluate and fully admit left once, then right once, before complete key-set agreement",
        "key_agreement": "Refuse the lowest ASCII symmetric-difference key and its missing side before any body or output copy",
        "body_order": "Exactly once per agreed key in canonical ASCII order",
        "max_entries": 256,
        "static_check": "Unknown typed key/left/right body binders are checked even for empty inputs; all boundaries are exact",
        "leaf_families": list(result["source_expressions"]["reduce_keyed"]["leaf_families"]),
        "cancellation_stages": ["keyed_zip_keyset", "keyed_zip_iteration"],
        "authority": "Both inputs retain actual dependencies and taints even when empty or ignored; no new effects or physical authority"}
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(merge_template())
    result.update(schema_version="ontokin.agent-catalog/0.18", language_version="0.18",
        profile=KEYED_ZIP_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.18"; module Example @ "example"; profile "keyed-zip-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], KEYED_ZIP_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_merge_examples={"language_version": "0.17",
            "paths": ["examples/keyed-merge/panel-task.files.json"]},
        example_context="The .18 manifests explicitly select exact-key pairing; inherited examples retain their bindings.")
    result["limits"].update(max_keyed_entries=256, max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=KEYED_ZIP_PROFILE, specification=ADOPTION,
                signature="KeyedZipAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic source repair and pure exact-key pairing under current host authority.",
                domains=["Explicit source/Agent/GLB .18; bundle/files .2 and twelve operation shapes remain unchanged",
                    "Complete key-set agreement precedes every dynamic body and result copy",
                    "Both actual inputs retain dependencies and taints even when empty or ignored by the body",
                    "Source/member keys and exact revision preconditions remain repair authority",
                    "Accepted source, stores and artifacts never grant future execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=KEYED_ZIP_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.18 with complete source and immutable image identity.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Equivalent explicit .17 controls retain complete geometry and motion streams",
                    "Source/profile/revision and detached paired provenance identify the .18 program",
                    "No live destination physics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.18 requires ontokin.bundle/0.2."
    result["items"].append(_entry("builtin", "zip_keyed",
        "zip_keyed<T, U, V>(left: Keyed<T>, right: Keyed<U>, (key: String, left_value: T, right_value: U) -> V) -> Keyed<V>",
        "Transform corresponding immutable keyed values after exact complete key-set agreement.",
        capability="pure_keyed_pairs", profile=KEYED_ZIP_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["Each input is evaluated and fully admitted once, left before right",
            "Each input and the result have at most 256 entries of the 24 inherited immutable leaf families",
            "The lowest ASCII symmetric-difference key identifies its missing input side",
            "One unknown-payload statically checked pure body runs once per agreed canonical key",
            "Key-set checks, pair bindings, bodies, copying and provenance are bounded and cancellable",
            "Aggregate reads and both original paired contributors remain detached and read-only"]))
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
    result["keyed_zip_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != KEYED_ZIP_PROFILE:
            raise ValueError("Keyed pair discovery requires the admitted .18 source profile.")
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
