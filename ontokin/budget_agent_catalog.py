"""Source-aware discovery for the separately selected budget Agent binding."""
from __future__ import annotations

import hashlib
import json

from .budget_protocol import SCHEMA_VERSION, DEFINITION, OPERATIONS, MAX_BUDGETS
from .execution_budget import DEFAULT_LIMITS, MAX_LIMIT, HostPolicy
from .json_limits import measure_json
from .profile_capabilities import BUDGET_PROFILE


def interface(policy=None, *, aggregate_limits=None):
    policy = HostPolicy() if policy is None else policy
    if not isinstance(policy, HostPolicy):
        raise TypeError("Discovery host policy must be supplied by the embedding host.")
    return {"status": "experimental_development", "agent_contract": SCHEMA_VERSION,
            "language_version": "0.7", "profile": BUDGET_PROFILE,
            "delivery_contract": DEFINITION.destination,
            "storage_schema": DEFINITION.store_schema,
            "defaults": dict(DEFAULT_LIMITS), "host_ceilings": policy.ceilings,
            "policy_id": policy.policy_id, "max_representable_limit": MAX_LIMIT,
            "source_fields": ["max_operations", "max_elapsed"],
            "caller_caps": list(DEFAULT_LIMITS), "fixed_budgets": {
                name: value for name, value in MAX_BUDGETS.items() if name not in DEFAULT_LIMITS},
            "operations": sorted(OPERATIONS),
            "edit_scope": {"element_id": ["sources", "<source_id>"],
                           "patches": "Exact UTF-8 byte spans inside the identified source file",
                           "identity_guard": "Complete source-derived acceptance identity map"},
            "aggregate_limits": aggregate_limits or {
                "max_running_requests": 4, "max_pending_requests": 256,
                "scope": "Trusted local service admission; independent of source grants"},
            "transport": "BudgetAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.7",
            "request_schema": "docs/language-design/agent-v0.7/request.schema.json",
            "response_schema": "docs/language-design/agent-v0.7/response.schema.json",
            "accounting": "One policy snapshot, operation counter and original deadline per request",
            "limitations": ["Experimental Agent increment; complete reach release remains open.",
                            "Only file source identities authorize this binding's byte patches.",
                            "Artifact retrieval verifies retained bytes; producer destination checks remain historical.",
                            "A cooperative deadline cannot preempt a blocking host callback.",
                            "Recorded playback does not establish live destination physics."]}


def catalog(*, policy, linked_program=None, check=None, aggregate_limits=None):
    # Start from an unchanged copy of the explicit inherited language catalog.
    # Its existing specifications remain the authority for inherited semantics.
    from .construction_catalog import catalog as inherited, _Budget, _public_interfaces
    result = inherited(profile="planar-reach-0.1", check=check)
    inherited_profiles = list(result["compatible_definition_profiles"])
    inherited_examples = {key: result[key] for key in
                          ("complete_examples", "example_bundles", "example_file_manifests")}
    def convert(value):
        if check is not None:
            check()
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, str):
            # Keep the paths of the inherited specifications and fixtures.
            if value == "planar-reach-0.1" or value.startswith("planar-reach-0.1/"):
                value = value.replace("planar-reach-0.1", BUDGET_PROFILE, 1)
            return (value.replace("ontokin.agent/0.6", SCHEMA_VERSION)
                    .replace("ontokin.glb/0.6", DEFINITION.destination)
                    .replace("planar-reach-program-agent.sqlite3", DEFINITION.store_filename))
        return value
    result = convert(result)
    result.update(schema_version="ontokin.agent-catalog/0.7", language_version="0.7",
                  profile=BUDGET_PROFILE, budget_agent_interface=interface(policy, aggregate_limits=aggregate_limits),
                  source_header='ontokin "0.7"; module Example @ "example"; profile "planar-reach-budget-0.1";',
                  compatible_definition_profiles=inherited_profiles + [BUDGET_PROFILE],
                  complete_examples=["examples/execution-budgets/larger-workload.ok"],
                  example_bundles=[], example_file_manifests=[],
                  inherited_reach_examples={"language_version": "0.6", **inherited_examples},
                  example_context="The .7 example is exact source and needs its requested host ceilings. Earlier examples retain their original bindings.",
                  adoption="docs/language-design/agent-v0.7/ADOPTION.md")
    result["limits"].pop("max_operations")
    result["limits"].pop("max_elapsed_ms")
    result["execution_defaults"] = dict(DEFAULT_LIMITS)
    for item in result["items"]:
        if check is not None:
            check()
        if item.get("kind") == "protocol":
            item.update(specification="docs/language-design/agent-v0.7/ADOPTION.md",
                        signature="BudgetAgentService(store, host_policy=HostPolicy(...))",
                        store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                        description="Explicit source-authoritative budgets with current host policy and atomic local Agent requests.",
                        domains=["Explicit source 0.7 / planar-reach-budget-0.1 entries and compatible pinned definitions",
                                 "Earlier Python and CLI defaults retain their bindings",
                                 "Only complete-file source identities authorize exact UTF-8 byte patches",
                                 "Current worker policy authorizes a fresh shared request ledger",
                                 "Saved artifacts and run descriptors grant no execution authority",
                                 "Final response checks precede atomic source, run and artifact publication"])
        elif item.get("kind") == "destination":
            item.update(specification="docs/language-design/execution-budgets-v0.1/ADOPTION-C073.md",
                        examples=["examples/execution-budgets/larger-workload.ok"],
                        domains=["Explicit source 0.7 / planar-reach-budget-0.1 and GLB/0.7",
                                 "The admitted source prefix authorizes evaluation and recorded delivery",
                                 "Construction, evaluation, encoding and independent supplied-byte checks share remaining work",
                                 "Stored animation retains complete source history and conservative motion bounds",
                                 "Recorded playback supplies no destination IK, contacts, grasp or live physics"])
    result["items"].append({"id": BUDGET_PROFILE + "/syntax/execution", "kind": "syntax",
        "name": "execution", "profile": BUDGET_PROFILE, "capability": "configurable_execution_budgets",
        "signature": "execution { max_operations = 400000; max_elapsed = 80[s]; }",
        "description": "An entry source requests finite work; the trusted host independently authorizes its ceilings.",
        "specification": "docs/language-design/agent-v0.7/ADOPTION.md"})
    if linked_program is not None:
        if linked_program.entry.ast.profile != BUDGET_PROFILE:
            raise ValueError("Budget discovery requires the admitted budget source profile.")
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
