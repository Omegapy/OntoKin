"""Detached discovery for explicit bounded pure String concatenation."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_rekey_agent_catalog import _declarative_template as rekey_template
from .keyed_rekey_agent_catalog import interface as rekey_interface
from .profile_capabilities import STRING_CONCAT_PROFILE
from .string_concat_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION


ADOPTION = "docs/language-design/string-concat-v0.1/ADOPTION.md"
EXAMPLES = ["examples/string-concat/agent/panel-task.files.json",
            "examples/string-concat/agent/panel-task-repaired.files.json",
            "examples/string-concat/empty-both.files.json"]
STAGES = ("string_concat_admission", "string_concat_scan",
          "string_concat_allocation", "string_concat_publication")


def interface(policy=None, *, aggregate_limits=None):
    result = rekey_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.20",
        profile=STRING_CONCAT_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="StringConcatAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.20",
        request_schema="docs/language-design/agent-v0.20/request.schema.json",
        response_schema="docs/language-design/agent-v0.20/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.20 --output MODEL.glb",
        adoption=ADOPTION)
    result["source_expressions"]["rekey_keyed"]["string_concatenation"] = True
    result["source_expressions"]["string_concat"] = {
        "syntax": "left + right",
        "inputs": ["String", "String"], "output": "String",
        "declaring_version": "0.20", "declaring_profile": STRING_CONCAT_PROFILE,
        "meaning": "Exact ordered Unicode scalar sequence of left followed by right; no conversion, normalization, trimming or escaping",
        "evaluation_order": "Left once, then right once; original operand failures retain identity",
        "abstract_behavior": "Unknown String after exact type checks; no scan, computed-byte reservation or dynamic String stages",
        "max_result_utf8_bytes": 65536,
        "max_total_utf8_bytes": 4194304,
        "total_scope": "Monotone logical computed-result bytes on the same complete-request SharedExecutionBudget; never refunded within a request",
        "scan_quantum_utf8_bytes": 64,
        "additional_operations": "3 + ceil(left_utf8_bytes/64) + ceil(right_utf8_bytes/64) + ceil(result_utf8_bytes/64)",
        "cancellation_stages": list(STAGES),
        "allocation": "Scalar sizing and actual shared-ledger admission precede result allocation; current authority is checked before allocation and publication",
        "empty_behavior": "Both operands are evaluated and admission, allocation and publication remain charged; zero-byte scans add no scan charge",
        "cache_behavior": "No result folding or value-cache bypass of an executed .20 plus; established immutable member reads retain inherited semantics",
        "other_operators": "All other operator/type pairs retain their complete inherited dispatch and diagnostics",
        "keys": "Ordinary Strings need not be stable keys; rekey retains its unchanged complete 1-64 ASCII-character rule and collision order",
        "authority": "Higher operation/time requests require independently current host ceilings; caller caps only reduce authority and neither changes the fixed byte caps",
        "provenance": "Retain both actual operand dependencies, taints and inherited keyed lineage; no new writable identity or lineage family",
        "lexical": "Raw UTF-8 scalar text and inherited quote/backslash/n/r/t escapes; backslash-u remains unsupported"}
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(rekey_template())
    result.update(schema_version="ontokin.agent-catalog/0.20", language_version="0.20",
        profile=STRING_CONCAT_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.20"; module Example @ "example"; profile "string-concat-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], STRING_CONCAT_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_rekey_examples={"language_version": "0.19",
            "paths": ["examples/keyed-rekey/agent/panel-task.files.json"]},
        example_context="The .20 manifests explicitly select bounded String addition; inherited examples retain their original bindings.")
    result["limits"].update(max_string_concat_result_utf8_bytes=65536,
        max_string_concat_total_utf8_bytes=4194304, max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=STRING_CONCAT_PROFILE, specification=ADOPTION,
                signature="StringConcatAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic source repair and bounded String concatenation under current host authority.",
                domains=["Explicit source/Agent/GLB .20; bundle/files .2 and twelve operation shapes remain unchanged",
                    "Only String + String in a .20 declaring unit gains the new meaning",
                    "65536 UTF-8 result bytes and 4194304 cumulative logical result bytes per complete request",
                    "Real shared-ledger scan, allocation and publication stages preserve cancellation",
                    "Computed namespaces retain exact payloads, original contributors and revision-bound source repair",
                    "Accepted source, stores and artifacts never grant future execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=STRING_CONCAT_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.20 with complete source and immutable image identity.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Equivalent explicit .19 controls retain complete geometry and motion streams",
                    "Source/profile/revision and original detached lineage identify the .20 program",
                    "No live destination physics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.20 requires ontokin.bundle/0.2."
    result["items"].append(_entry("operator", "String + String",
        "String + String -> String",
        "Concatenate the exact ordered scalar sequences under current request and UTF-8 byte bounds.",
        capability="pure_string_concatenation", profile=STRING_CONCAT_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["Declaring source .20 only; earlier imported expressions retain their original meaning",
            "Left and right evaluate once in that order, including empty operands",
            "No implicit conversion, normalization, interpolation, slicing or length overload",
            "Preallocation scalar scan: one actual ledger charge per started operand-local 64 UTF-8 bytes",
            "Per-result cap 65536 bytes; cumulative logical results cap 4194304 bytes on the same request ledger",
            "Admission, scan, allocation and publication use actual cancellation and operation/time authority",
            "All original dependencies, generated taints and earlier keyed contributor records remain exact",
            "No computed source/module/import/asset identity or expanded physical authority"]))
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
    result["string_concat_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != STRING_CONCAT_PROFILE:
            raise ValueError("String concatenation discovery requires the admitted .20 source profile.")
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
