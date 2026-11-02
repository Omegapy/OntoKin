"""Detached discovery for explicit bounded immutable keyed membership."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_membership_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION
from .profile_capabilities import KEYED_MEMBERSHIP_PROFILE, STRING_CONCAT_PROFILE
from .string_concat_agent_catalog import _declarative_template as concat_template
from .string_concat_agent_catalog import interface as concat_interface


ADOPTION = "docs/language-design/keyed-membership-v0.1/ADOPTION.md"
EXAMPLES = ["examples/keyed-membership/agent/base.files.json",
            "examples/keyed-membership/agent/inserted.files.json",
            "examples/keyed-membership/empty.files.json"]
STAGES = ("keyed_membership_admission", "keyed_membership_input",
          "keyed_membership_query", "keyed_membership_scan",
          "keyed_membership_publication")


def interface(policy=None, *, aggregate_limits=None):
    result = concat_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.21",
        profile=KEYED_MEMBERSHIP_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="KeyedMembershipAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.21",
        request_schema="docs/language-design/agent-v0.21/request.schema.json",
        response_schema="docs/language-design/agent-v0.21/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.21 --output MODEL.glb",
        adoption=ADOPTION)
    result["source_expressions"]["string_concat"].update(
        declaring_versions=["0.20", "0.21"],
        declaring_profiles=[STRING_CONCAT_PROFILE, KEYED_MEMBERSHIP_PROFILE],
        inherited_in_declaring_profile=KEYED_MEMBERSHIP_PROFILE,
        diagnostic_profile=STRING_CONCAT_PROFILE,
        cache_behavior="No folding or value-cache bypass of an executed .20/.21 plus; established immutable member reads retain inherited semantics")
    result["source_expressions"]["has_key"] = {
        "syntax": "has_key(collection, query)",
        "signature": "has_key(Keyed<T>, String) -> Bool",
        "declaring_version": "0.21", "declaring_profile": KEYED_MEMBERSHIP_PROFILE,
        "inputs": ["Admitted immutable keyed leaf collection or existing generated Keyed<Ref<C>> view", "String"],
        "output": "Bool",
        "meaning": "True if the exact stable query key occurs in the fully admitted canonical collection; false for valid absence",
        "declaring_boundary": "Bare has_key is reserved only in a .21 declaring unit; older functions, locals and aliases retain meaning and qualified older helpers remain available",
        "evaluation_order": "Callee then both arguments eagerly left to right; arity, collection family and exact String query type precede abstract return",
        "abstract_behavior": "Well-typed abstract or unknown input yields unknown Bool without dynamic stages, payload admission or literal query-domain checking",
        "stable_key_pattern": "[A-Za-z0-9][A-Za-z0-9._-]{0,63}",
        "invalid_query": "Explicit stable-key refusal, never false",
        "max_entries": 256, "max_key_characters": 64,
        "admission": "Validate the complete immutable tuple, canonical keys, exact leaf wrappers and bounded resolved metadata before validating the query or scanning",
        "scan": "Canonical keys only; stop at the first exact match, otherwise scan all entries; never evaluate or compare payloads, sort, build a set or copy the collection",
        "additional_operations": "n + k + 3; n is full input length and k is comparisons through the first match or n for absence",
        "empty_operations": 3, "maximum_operations": 515,
        "first_of_256_operations": 260,
        "cancellation_stages": list(STAGES),
        "stage_operations": {STAGES[0]: 1, STAGES[1]: "n", STAGES[2]: 1,
                             STAGES[3]: "k", STAGES[4]: 1},
        "authority": "The original admitted SharedExecutionBudget, deadline, current host ceilings, caller reductions and callback govern every stage; no fallback authority or new allowance",
        "cache_behavior": "No constant or parameter result folding for actual invocations; inherited immutable binding reuse remains unchanged",
        "provenance": "True and false retain actual collection/query dependencies, generated taints and all inherited detached contributors; no new public lineage family or selected-leaf fiction",
        "generated_views": "Read-only membership retains existing access and CON-007 generated-shape restrictions; Ref is not a new authored annotation or mutable reference constructor",
        "string_quota": "Membership consumes no computed String bytes; inherited String operations retain their own fixed result and cumulative caps",
        "lookup": "A guarded lookup can select a fallback; ordinary unguarded absence retains its existing name error"}
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(concat_template())
    result.update(schema_version="ontokin.agent-catalog/0.21", language_version="0.21",
        profile=KEYED_MEMBERSHIP_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.21"; module Example @ "example"; profile "keyed-membership-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], KEYED_MEMBERSHIP_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_string_concat_examples={"language_version": "0.20",
            "paths": ["examples/string-concat/agent/panel-task.files.json"]},
        example_context="The .21 examples explicitly select membership for sparse overrides; inherited examples retain their original bindings.")
    result["limits"].update(max_keyed_membership_entries=256,
        max_keyed_membership_key_characters=64, max_keyed_membership_operations=515,
        max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=KEYED_MEMBERSHIP_PROFILE, specification=ADOPTION,
                signature="KeyedMembershipAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic sparse source repair and bounded immutable membership under current host authority.",
                domains=["Explicit source/Agent/GLB .21; bundle/files .2 and twelve operation shapes remain unchanged",
                    "Declaring .21 reserves has_key and inherits bounded .20 String addition",
                    "Complete canonical input admission precedes query validation and key-only scan",
                    "Five actual shared-ledger stages preserve cancellation and current authority",
                    "Actual dependencies, generated restrictions and inherited detached contributors remain exact",
                    "Accepted source, stores and artifacts never grant future execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=KEYED_MEMBERSHIP_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.21 with complete source and immutable image identity.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Equivalent explicit .20 controls retain complete geometry and motion streams",
                    "Source/profile/revision and original detached lineage identify the .21 program",
                    "No live destination physics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.21 requires ontokin.bundle/0.2."
        elif item["name"] == "String + String":
            item.update(profile=KEYED_MEMBERSHIP_PROFILE, specification=ADOPTION)
            item["domains"][0] = "Declaring source .20 or .21; earlier imported expressions retain their original meaning"
    result["items"].append(_entry("builtin", "has_key", "has_key(Keyed<T>, String) -> Bool",
        "Test an exact stable key in an admitted immutable collection without recomputing payloads.",
        capability="bounded_keyed_membership", profile=KEYED_MEMBERSHIP_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["Ordinary call in a .21 declaring unit; both arguments evaluate eagerly left to right",
            "At most 256 canonical entries; stable keys are 1-64 ASCII characters with an initial letter or digit",
            "Existing authored leaf families and read-only generated Ref views retain type/access/shape rules",
            "Complete input admission, query validation, canonical scan and publication use the original ledger",
            "Successful dynamic cost n+k+3; empty costs 3 and maximum costs 515; fixed original deadline and callback",
            "Well-typed abstract/unknown calls return unknown Bool without dynamic stages",
            "Both outcomes retain actual dependencies, generated taints and all existing contributor records",
            "No payload comparison, collection copy, new lineage family, mutable container or physical authority"]))
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
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != KEYED_MEMBERSHIP_PROFILE:
            raise ValueError("Keyed membership discovery requires the admitted .21 source profile.")
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
