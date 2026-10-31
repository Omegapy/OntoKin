"""Detached discovery for the explicit sequential keyed reduction."""
from __future__ import annotations

import hashlib
import json

from .json_limits import measure_json
from .keyed_reduction_protocol import DEFINITION, MAX_REQUEST_BYTES, SCHEMA_VERSION
from .keyed_transform_agent_catalog import _declarative_template as transform_template
from .keyed_transform_agent_catalog import interface as transform_interface
from .profile_capabilities import KEYED_REDUCTION_PROFILE


ADOPTION = "docs/language-design/keyed-reduction-v0.1/ADOPTION.md"
EXAMPLES = ["examples/keyed-reduction/panel-task.files.json",
            "examples/keyed-reduction/panel-identity.files.json",
            "examples/keyed-reduction/singleton-length.files.json"]


def interface(policy=None, *, aggregate_limits=None):
    result = transform_interface(policy, aggregate_limits=aggregate_limits)
    result.update(agent_contract=SCHEMA_VERSION, language_version="0.15",
        profile=KEYED_REDUCTION_PROFILE, delivery_contract=DEFINITION.destination,
        storage_schema=DEFINITION.store_schema, store_filename=DEFINITION.store_filename,
        transport="KeyedReductionAgentService(store, host_policy=...) or agent --protocol ontokin.agent/0.15",
        request_schema="docs/language-design/agent-v0.15/request.schema.json",
        response_schema="docs/language-design/agent-v0.15/response.schema.json",
        file_manifest_command="export --bundle PROGRAM.files.json --target ontokin.glb/0.15 --output MODEL.glb",
        adoption=ADOPTION,
        reduction_provenance={"value_field": "derived_reductions", "generated_input_field": "input_reductions",
            "ordering": "Unique actual input, seed and selected-body derivations before the current reduction",
            "locations": ["expression", "input", "seed", "body"],
            "types": ["input_element_type", "accumulator_type"], "writable": False})
    result["source_expressions"]["reduce_keyed"] = {
        "syntax": "reduce_keyed<Acc>(input, seed, (accumulator, key, value) -> body)",
        "input": "One admitted flat Keyed<T>; input admission completes before the seed is evaluated",
        "seed": "One explicitly typed starting accumulator evaluated once",
        "output": "One Acc, computed as a sequential left fold in canonical ASCII key order",
        "max_entries": 256,
        "body": "Pure, typed and access-checked even when empty; unknown typed locals retain frame metadata",
        "leaf_families": ["Int", "Real", "Bool", "String", "Quantity", "Vec3", "Vector3", "Range",
            "FrameRef", "Point3", "Rotation", "Pose", "Color", "LoftSection", "SurfaceMaterial",
            "PlanarPoint", "PolygonVertex", "PolygonRing", "PolygonSection", "FramedPolygonSection",
            "PolygonPocket", "TextureImage", "PlanarUV", "TextureBinding"],
        "authority": "No new effects or physical authority; every actual dependency and taint remains"}
    return result


def _declarative_template():
    from .construction_catalog import _entry
    result = json.loads(transform_template())
    result.update(schema_version="ontokin.agent-catalog/0.15", language_version="0.15",
        profile=KEYED_REDUCTION_PROFILE, agent_contract=SCHEMA_VERSION,
        delivery_targets=[DEFINITION.destination], adoption=ADOPTION,
        source_header='ontokin "0.15"; module Example @ "example"; profile "keyed-reduction-0.1";',
        compatible_definition_profiles=[*result["compatible_definition_profiles"], KEYED_REDUCTION_PROFILE],
        complete_examples=EXAMPLES, example_file_manifests=EXAMPLES, example_bundles=[],
        inherited_transform_examples={"language_version": "0.14",
            "paths": ["examples/keyed-transform/panel-task.files.json"]},
        example_context="The .15 manifests explicitly select reduction; inherited examples retain their original bindings.")
    result["limits"].update(max_keyed_entries=256, max_request_bytes=MAX_REQUEST_BYTES)
    for item in result["items"]:
        if item["kind"] == "protocol" or item["name"] == "persistent_agent_editing_service":
            if item["kind"] == "protocol":
                item["name"] = SCHEMA_VERSION
                item["capability"] = SCHEMA_VERSION
            item.update(profile=KEYED_REDUCTION_PROFILE, specification=ADOPTION,
                signature="KeyedReductionAgentService(store, host_policy=HostPolicy(...))",
                store_filename=DEFINITION.store_filename, store_schema=DEFINITION.store_schema,
                description="Atomic source repair and bounded sequential reductions under current host authority.",
                domains=["Explicit source/Agent/GLB .15; bundle/files .2 and twelve operations are unchanged",
                    "Accumulators retain all actual input, seed and body dependencies, including overwritten values",
                    "Source/member keys and exact revision preconditions remain repair authority",
                    "Accepted source, persistent stores and artifacts never grant future execution authority"])
        elif item["kind"] == "destination":
            item.update(profile=KEYED_REDUCTION_PROFILE, specification=ADOPTION,
                name=DEFINITION.destination, capability=DEFINITION.destination,
                signature=DEFINITION.destination, examples=EXAMPLES,
                description="Recorded GLB/0.15 with complete source and immutable image identity.",
                domains=["Inherited geometry, PBR, UV, PNG, sampler and recorded motion representation",
                    "Equivalent explicit .14 controls retain complete geometry and motion streams",
                    "Source/profile/revision and detached derivation metadata identify the .15 program",
                    "No live destination physics or Unreal import claim"])
        elif item["kind"] == "format" and item["name"] == "ontokin.bundle/0.1":
            item["description"] = "Unchanged legacy transport; Agent/0.15 requires ontokin.bundle/0.2."
    result["items"].append(_entry("builtin", "reduce_keyed",
        "reduce_keyed<Acc>(input: Keyed<T>, seed: Acc, (accumulator: Acc, key: String, value: T) -> body: Acc) -> Acc",
        "Combine an immutable keyed collection using an explicit typed seed and sequential ASCII order.",
        capability="pure_keyed_reductions", profile=KEYED_REDUCTION_PROFILE,
        specification=ADOPTION, examples=EXAMPLES,
        domains=["Input and seed are evaluated once, in that order; input admission precedes seed evaluation",
            "At most 256 entries of the 24 inherited immutable leaf families",
            "Static body checks run even when empty; an empty input returns a detached seed",
            "Every intermediate result and copy is checked and charged; no reassociation or reduction cache",
            "All actual reads survive later overwrites; derivations are detached and read-only"]))
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
    result["keyed_reduction_interface"] = current
    result["program_context"] = None
    if linked_program is not None:
        if linked_program.entry.ast.profile != KEYED_REDUCTION_PROFILE:
            raise ValueError("Keyed reduction discovery requires the admitted .15 source profile.")
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
