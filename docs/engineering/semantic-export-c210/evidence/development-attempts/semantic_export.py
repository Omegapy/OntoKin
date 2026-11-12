"""Explicit, experimental semantic sidecars for existing construction GLBs.

This is a checked projection of the existing compiler model, not another IR.
The caller supplies a trusted accepted revision; acceptance itself is proved by
the Agent workflow, not by a string or a self-asserted manifest field.
"""
from __future__ import annotations

import hashlib
import json
import struct
from typing import Any, Callable

from .bundle import ProgramBundle, load_bundle
from .construction import compile_construction
from .evaluator import time_text
from .gltf import read_glb, validate_export
from .json_limits import measure_json
from .scene import CONSTRUCTION_TARGET, program_metadata
from .values import bounded_data


SCHEMA = "ontokin.semantic-export/0.1"
PROFILE = "construction-primitives/0.1"
MAX_MANIFEST_BYTES = 4 * 1024 * 1024


class SemanticExportError(ValueError):
    """A failed semantic binding or an explicitly unsupported requirement."""

    def __init__(self, code: str, message: str, **details: Any):
        super().__init__(message)
        self.code, self.details = code, details

    def to_dict(self) -> dict:
        return {"schema_version": SCHEMA, "status": "rejected", "code": self.code,
                "message": str(self), "details": self.details}


def canonical_bytes(value: Any) -> bytes:
    """The sidecar comparison rule: compact UTF-8 JSON, sorted object keys."""
    measure_json(value, max_bytes=MAX_MANIFEST_BYTES)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


_FEATURES = (
    ("source_closure", "preserved", "Exact source hashes, package versions and compiler import closure; retain the separate .ok bytes."),
    ("stable_identities", "preserved", "Existing nominal definition and stable occurrence identities, including generated keys."),
    ("dimensions_units_frames", "preserved", "Normalized SI dimensions, authored/default placements, site frames and typed resolved values."),
    ("ownership", "preserved", "Ownership is a semantic relation; it does not create GLB transform parenting."),
    ("following", "preserved", "Declared rigid following is metadata; its evaluated world motion is baked separately."),
    ("hinge_constraints", "preserved", "Endpoints, axes, initial angles and limits are metadata, not destination constraints."),
    ("physical_declarations", "preserved", "This finite profile preserves explicit no_body, prescribed motion, disabled collision and gravity declarations."),
    ("materials", "preserved", "Source linear RGBA and actual GLB PBR values are retained; metallic=0 and roughness=0.7 are exporter defaults."),
    ("primitive_geometry", "approximated", "Boxes use triangulated faces; spheres use the existing finite tessellation and binary32 vertices."),
    ("world_motion", "baked", "Evaluated world poses use the existing sampled GLB translation/rotation tracks; no live controller is delivered."),
    ("numeric_precision", "approximated", "Source binary64 quantities and exact times are retained in metadata; GLB geometry/animation use binary32."),
    ("action_execution", "unsupported", "Action/event descriptions are retained, but GLB cannot execute OntoKin methods, actions or source edits."),
    ("live_physics", "unsupported", "No destination rigid-body simulation, collision response or live joint constraint is implemented."),
    ("source_reconstruction", "unsupported", "The sidecar is not a substitute for original source text, reusable definitions and pinned dependencies."),
)


def _requirements(required_features) -> list[str]:
    if (type(required_features) not in (tuple, list)
            or any(type(x) is not str for x in required_features)
            or len(required_features) != len(set(required_features))):
        raise SemanticExportError("OKS-E-REQUIREMENTS", "Required features must be a unique list of feature IDs.")
    known = {name: (status, reason) for name, status, reason in _FEATURES}
    for name in required_features:
        if name not in known or known[name][0] == "unsupported":
            status, reason = known.get(name, ("unsupported", "This contract does not define the requested feature."))
            raise SemanticExportError("OKS-E-UNSUPPORTED", "A required feature is unsupported.",
                                      feature=name, treatment=status, reason=reason)
    return sorted(required_features)


def _pose(pose) -> dict:
    return {"frame": pose.frame, "position_m": list(pose.position),
            "rotation_wxyz": list(pose.rotation)}


def _admit(model) -> None:
    problems = []
    if model.profile != "construction-0.1":
        problems.append({"feature": "source_profile", "value": model.profile})
    for path, obj in model.objects.items():
        if obj.geometry.get("kind") not in ("box", "sphere", "empty"):
            problems.append({"path": path, "feature": "geometry", "value": obj.geometry.get("kind")})
        if obj.physical != {"kind": "no_body"} or obj.motion != "prescribed" or obj.collision != "disabled":
            problems.append({"path": path, "feature": "physical_behavior",
                             "physical": obj.physical, "motion": obj.motion, "collision": obj.collision})
    for path, joint in model.joints.items():
        if joint.kind != "hinge":
            problems.append({"path": path, "feature": "joint_kind", "value": joint.kind})
    for path, action in model.actions.items():
        if action.kind not in ("move", "tween"):
            problems.append({"path": path, "feature": "action_kind", "value": action.kind})
    for block in model.events:
        for event in block.events:
            if event.kind not in ("start", "stop"):
                problems.append({"feature": "event_kind", "value": event.kind})
    if problems:
        raise SemanticExportError("OKS-E-PROFILE", "Declared source features exceed this finite semantic profile.",
                                  treatment="unsupported", features=problems)


def _accessor(decoded, index: int) -> dict:
    accessor = decoded.document["accessors"][index]
    view = decoded.document["bufferViews"][accessor["bufferView"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    width *= struct.calcsize({5126: "f", 5123: "H", 5125: "I"}[accessor["componentType"]])
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", width)
    digest = hashlib.sha256()
    for row in range(accessor["count"]):
        digest.update(decoded.binary[offset + row * stride:offset + row * stride + width])
    return {"accessor": index, "buffer_view": accessor["bufferView"],
            "component_type": accessor["componentType"], "type": accessor["type"],
            "count": accessor["count"], "data_sha256": "sha256:" + digest.hexdigest()}


def _content(record: dict) -> dict:
    return {key: value for key, value in record.items() if key not in ("accessor", "buffer_view")}


def _geometry_binding(decoded, node_index: int) -> dict:
    node = decoded.document["nodes"][node_index]
    result = {"node": node_index, "mesh": node.get("mesh"), "primitives": []}
    contents = []
    if "mesh" in node:
        for index, primitive in enumerate(decoded.document["meshes"][node["mesh"]]["primitives"]):
            attributes = {name: _accessor(decoded, value) for name, value in sorted(primitive["attributes"].items())}
            indices = _accessor(decoded, primitive["indices"])
            material = decoded.document["materials"][primitive["material"]]
            material_values = {key: value for key, value in material.items() if key not in ("name", "extras")}
            result["primitives"].append({"primitive": index, "attributes": attributes, "indices": indices,
                                         "material": primitive["material"], "material_values": material_values})
            contents.append({"mode": primitive.get("mode", 4),
                             "attributes": {key: _content(value) for key, value in attributes.items()},
                             "indices": _content(indices), "material_values": material_values})
    result["content_sha256"] = _digest(canonical_bytes(contents))
    return result


def _motion_binding(decoded, node_index: int) -> dict:
    animation = decoded.document["animations"][0]
    records, contents = [], []
    for index, channel in enumerate(animation["channels"]):
        if channel["target"]["node"] != node_index:
            continue
        sampler = animation["samplers"][channel["sampler"]]
        record = {"channel": index, "sampler": channel["sampler"], "path": channel["target"]["path"],
                  "input": _accessor(decoded, sampler["input"]), "output": _accessor(decoded, sampler["output"]),
                  "interpolation": sampler["interpolation"]}
        records.append(record)
        contents.append({"path": record["path"], "input": _content(record["input"]),
                         "output": _content(record["output"]), "interpolation": record["interpolation"]})
    node = decoded.document["nodes"][node_index]
    initial = {"translation": node["translation"], "rotation_xyzw": node["rotation"]}
    return {"animation": 0, "channels": records, "initial_world_pose": initial,
            "content_sha256": _digest(canonical_bytes({"initial": initial, "channels": contents}))}


def build_semantic_manifest(bundle: ProgramBundle | dict, glb: bytes, *, accepted_program_revision: str,
                            required_features=(), check: Callable[[], None] | None = None) -> dict:
    """Bind exact source and actual GLB bytes under one explicit finite profile.

    No source, accepted pointer, GLB or store is modified. The caller must obtain
    accepted_program_revision from trusted application state. This function
    checks identity and source/artifact consistency, not acceptance authority.
    """
    required = _requirements(required_features)
    sealed = load_bundle(bundle.to_payload() if isinstance(bundle, ProgramBundle) else bundle)
    if sealed.program_revision != accepted_program_revision:
        raise SemanticExportError("OKS-E-REVISION", "Supplied source is not the expected accepted revision.",
                                  expected=accepted_program_revision, actual=sealed.program_revision)
    if type(glb) is not bytes:
        raise SemanticExportError("OKS-E-ARTIFACT", "GLB input must be exact immutable bytes.")
    compiler = compile_construction(sealed, level="evaluated", check=check)
    model = compiler.model
    _admit(model)
    validation = validate_export(glb, model, target_contract=CONSTRUCTION_TARGET, check=check)
    decoded = read_glb(glb, target_contract=CONSTRUCTION_TARGET, check=check)
    metadata = decoded.document["extras"]["ontokin"]
    delivered_times = decoded.document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]
    if delivered_times[0] != "0" or delivered_times[-1] != time_text(model.duration):
        raise SemanticExportError("OKS-E-PROFILE", "This finite sidecar profile requires the full declared source interval.",
                                  feature="partial_interval", treatment="unsupported",
                                  delivered_start_seconds=delivered_times[0], delivered_end_seconds=delivered_times[-1],
                                  declared_end_seconds=time_text(model.duration))
    if any(node.get("extras", {}).get("ontokin", {}).get("kind") != "object" for node in decoded.document["nodes"]):
        raise SemanticExportError("OKS-E-PROFILE", "This finite sidecar profile requires GLB export with helpers=false.",
                                  feature="visual_helpers", treatment="unsupported")
    program = program_metadata(model, check=check)
    if metadata["program"] != program:
        raise SemanticExportError("OKS-E-PROVENANCE", "Actual GLB program provenance differs from the compiled source.")
    node_indices = {node["extras"]["ontokin"]["path"]: index
                    for index, node in enumerate(decoded.document["nodes"])}
    objects = []
    for path, obj in sorted(model.objects.items()):
        if check:
            check()
        mapping = model.occurrence_provenance[path]
        objects.append({"path": path, "element_id": list(obj.element_id), "definition_id": mapping["definition_id"],
                        "class_id": obj.class_name, "name": obj.name, "role": obj.role,
                        "owner": {"path": obj.owner, "element_id": list(model.objects[obj.owner].element_id)} if obj.owner else None,
                        "placement": {"authored": obj.placement_authored, **_pose(obj.placement)},
                        "geometry": obj.geometry, "appearance_linear_rgba": list(obj.appearance),
                        "properties": bounded_data(dict(obj.properties), check=check),
                        "physical": obj.physical, "collision": obj.collision,
                        "motion": {"declared": obj.motion, "initial_velocity_m_per_s": list(obj.velocity),
                                   "initial_omega_rad_per_s": list(obj.omega)},
                        "provenance": mapping,
                        "geometry_binding": _geometry_binding(decoded, node_indices[path]),
                        "motion_binding": _motion_binding(decoded, node_indices[path])})
    sites = [{"path": site.path, "element_id": list(site.element_id), "owner": site.owner,
              "pose": _pose(site.pose), "interface": site.interface, "size_m": site.size,
              "source_location": compiler.location(site.span)} for _, site in sorted(model.sites.items())]
    joints = [{"path": joint.path, "element_id": list(joint.element_id), "kind": joint.kind,
               "parent_site": joint.parent, "child_site": joint.child,
               "axis_in_parent_site": list(joint.axis), "limits_rad": list(joint.limits),
               "initial_rad": joint.initial, "source_location": compiler.location(joint.span)}
              for _, joint in sorted(model.joints.items())]
    follows = [{"path": follow.path, "element_id": list(follow.element_id), "parent_frame": follow.parent,
                "child_object": follow.child, "offset": _pose(follow.offset),
                "source_location": compiler.location(follow.span)} for _, follow in sorted(model.follows.items())]
    actions = [{"path": action.path, "element_id": list(action.element_id), "kind": action.kind,
                "target": action.target, "duration_seconds": time_text(action.duration),
                "velocity_m_per_s": list(action.vector) if action.vector is not None else None,
                "hinge_goal_rad": action.goal, "source_location": compiler.location(action.span)}
               for _, action in sorted(model.actions.items())]
    events = [{"time_seconds": time_text(block.time),
               "events": [{"kind": event.kind, "target": event.target,
                           "source_location": compiler.location(event.span)} for event in block.events]}
              for block in model.events]
    manifest = {"schema_version": SCHEMA, "profile": PROFILE, "status": "experimental",
                "binding": {"accepted_program_revision": sealed.program_revision,
                            "acceptance_authority": "caller; verify retained Agent acceptance evidence separately",
                            "source_manifest": sealed.manifest(), "source_provenance": program["sources"],
                            "artifact": {"target_contract": CONSTRUCTION_TARGET, "sha256": _digest(glb), "bytes": len(glb)}},
                "coordinates": {"handedness": "right", "up": "+Y", "length": "m", "time": "s",
                                "angle": "rad", "mass": "kg", "source_rotation_order": "WXYZ",
                                "glb_rotation_order": "XYZW", "geometry_frame": "object-local",
                                "glb_transform_policy": "all_nodes_are_roots_with_baked_world_poses"},
                "scene": {"module": model.module_name, "name": model.scene_name,
                          "duration_seconds": time_text(model.duration), "gravity_m_per_s2": list(model.gravity),
                          "delivered_interval_seconds": [delivered_times[0], delivered_times[-1]],
                          "motion_authority": "OntoKin reference evaluator; destination receives baked playback only"},
                "objects": objects, "sites": sites, "joints": joints, "follows": follows,
                "actions": actions, "events": events, "collections": program["collections"],
                "required_features": required,
                "features": [{"feature": name, "treatment": status, "reason": reason, "required": name in required}
                             for name, status, reason in _FEATURES],
                "comparison_rule": "Exact GLB bytes; sidecar compact UTF-8 JSON with sorted keys and unchanged array order; no timestamps or request IDs.",
                "validation": {"source_to_artifact": validation["status"], "destination_execution": False}}
    return json.loads(canonical_bytes(manifest))


def verify_semantic_manifest(manifest: dict, bundle: ProgramBundle | dict, glb: bytes, *,
                             accepted_program_revision: str, required_features=None,
                             check: Callable[[], None] | None = None) -> dict:
    """Recompute all semantic values and references from the actual bound inputs.

    Pass required_features when the consumer has its own requirements. Omitting
    it validates the manifest's declared requirement list, not an external policy.
    """
    actual = canonical_bytes(manifest)
    if type(manifest) is not dict or manifest.get("schema_version") != SCHEMA:
        raise SemanticExportError("OKS-E-SCHEMA", "Unknown semantic export schema.")
    requirements = manifest.get("required_features") if required_features is None else required_features
    expected = build_semantic_manifest(bundle, glb, accepted_program_revision=accepted_program_revision,
                                       required_features=requirements, check=check)
    if actual != canonical_bytes(expected):
        raise SemanticExportError("OKS-E-MISMATCH", "Semantic values, requirements or geometry references differ from the bound source and actual GLB.")
    return {"status": "passed", "schema_version": SCHEMA, "program_revision": accepted_program_revision,
            "artifact_sha256": _digest(glb), "manifest_sha256": _digest(actual),
            "objects": len(expected["objects"]), "sites": len(expected["sites"]),
            "joints": len(expected["joints"]), "follows": len(expected["follows"]),
            "destination_execution": False}
