"""Detached discovery for bounded pure keyed renaming."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_rekey_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION
from .keyed_zip_agent_catalog import _declarative_template as zip_template
from .keyed_zip_agent_catalog import interface as zip_interface
from .profile_capabilities import KEYED_REKEY_PROFILE


ADOPTION = "docs/language-design/keyed-rekey-v0.1/ADOPTION.md"
EXAMPLES = ["examples/keyed-rekey/agent/panel-task.files.json",
            "examples/keyed-rekey/agent/panel-task-repaired.files.json",
            "examples/keyed-rekey/singleton.files.json"]


def interface(policy=None, *, aggregate_limits=None):
    result = zip_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.19",
        profile=KEYED_REKEY_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="KeyedRekeyAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.19",
        request_schema="docs/language-design/agent-v0.19/request.schema.json",
        response_schema="docs/language-design/agent-v0.19/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.19 --output MODEL.glb",
        adoption=ADOPTION,
        rekey_provenance={"value_field": "derived_rekeys", "generated_input_field": "input_rekeys",
            "fields": ["expression", "input", "body", "element_type", "old_key", "new_key", "input_entry"],
            "ordering": "Normalized input and selected callback aggregates in old-key traversal order, then current aggregate; selected output adds matching original leaf, actual callback and current old-to-new records with exact-record deduplication",
            "locations": ["expression", "input", "body"],
            "types": ["element_type"],
            "contributor_fields": ["old_key", "new_key", "input_entry"],
            "aggregate": {"old_key": None, "new_key": None, "input_entry": None},
            "entry_origin": "Retained original payload entry mapped under the new key; not a literal declaration of the computed key",
            "inherited_keys": "Map, reduction, filter, merge and zip records retain their original keys and contributor meanings",
            "writable": False})
    result["source_expressions"]["rekey_keyed"] = {
        "syntax": "rekey_keyed<T>(input, (old_key, value) -> new_key)",
        "input": "Exact resolved Keyed<T> of admitted immutable leaves; no boundary widening",
        "body": "Exactly String; binders are read-only String old_key and T value in the body only",
        "output": "Detached Keyed<T> preserves every original payload and cardinality under its computed new key",
        "input_order": "Evaluate and fully admit the complete input once before any callback",
        "body_order": "Exactly once per original key in canonical ASCII old-key order",
        "key_domain": {"pattern": "[A-Za-z0-9][A-Za-z0-9._-]{0,63}",
            "full_match": True, "min_ascii_characters": 1, "max_ascii_characters": 64,
            "case_sensitive": True, "normalization": False},
        "collision_policy": "Refuse the first duplicate computed key immediately in old-key traversal order; no later callbacks or overwrite",
        "output_order": "Precharge sorting, then publish in canonical ASCII new-key order",
        "max_entries": 256,
        "static_check": "Unknown typed binders and masked enclosing locals are checked before dynamic input evaluation, including empty input; all boundaries are exact",
        "leaf_families": list(result["source_expressions"]["reduce_keyed"]["leaf_families"]),
        "cancellation_stages": ["keyed_rekey_iteration", "keyed_rekey_key_validation",
            "keyed_rekey_collision", "keyed_rekey_publication"],
        "empty_behavior": "No callback or per-entry checkpoint; one final publication checkpoint after static and input admission",
        "occurrence_identity": "Generated IDs and paths use the new key; a changed key removes the old identity and introduces the new one",
        "authority": "Complete input and actual callback reads retain dependencies and taints, including empty or ignored payloads; no new effects or physical authority",
        "string_concatenation": False}
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(zip_template())
    result.update(schema_version="ontokin.agent-catalog/0.19", language_version="0.19",
        profile=KEYED_REKEY_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.19"; module Example @ "example"; profile "keyed-rekey-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], KEYED_REKEY_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_zip_examples={"language_version": "0.18",
            "paths": ["examples/keyed-zip/panel-task.files.json"]},
        example_context="The .19 manifests explicitly select bounded keyed renaming; inherited examples retain their bindings.")
    result["limits"].update(max_keyed_entries=256, max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=KEYED_REKEY_PROFILE, specification=ADOPTION,
                signature="KeyedRekeyAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic source repair and bounded pure keyed renaming under current host authority.",
                domains=["Explicit source/Agent/GLB .19; bundle/files .2 and twelve operation shapes remain unchanged",
                    "Complete input admission precedes every dynamic callback and result copy",
                    "Canonical old-key callbacks stop at the first collision; complete output sorts by new keys",
                    "Changed generated keys change occurrence identities while original payloads remain exact",
                    "Source/member keys and exact revision preconditions remain repair authority",
                    "Accepted source, stores and artifacts never grant future execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=KEYED_REKEY_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.19 with complete source and immutable image identity.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Equivalent explicit .18 controls retain complete geometry and motion streams",
                    "Source/profile/revision and detached old-to-new provenance identify the .19 program",
                    "No live destination physics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.19 requires ontokin.bundle/0.2."
    result["items"].append(_entry("builtin", "rekey_keyed",
        "rekey_keyed<T>(input: Keyed<T>, (old_key: String, value: T) -> String) -> Keyed<T>",
        "Compute one unique stable key per immutable input entry while preserving its exact original payload.",
        capability="pure_keyed_renaming", profile=KEYED_REKEY_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["One complete input evaluation and admission precedes all callbacks",
            "Input and result have at most 256 entries of the 24 inherited immutable leaf families",
            "Computed keys are 1 through 64 ASCII characters: first alphanumeric, then alphanumeric, period, underscore or hyphen",
            "One unknown-payload statically checked pure String body runs once per canonical old key",
            "The first computed-key collision fails immediately without later callbacks or partial publication",
            "New keys determine final ordering and generated identity; payload values and original contributor keys remain exact",
            "Iteration, key validation, collision lookup, copying, sorting and final provenance remain bounded and cancellable",
            "Aggregate reads and original payload entry locations remain detached and read-only"]))
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
    result["keyed_rekey_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != KEYED_REKEY_PROFILE:
            raise ValueError("Keyed renaming discovery requires the admitted .19 source profile.")
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
