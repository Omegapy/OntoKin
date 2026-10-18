"""Bake evaluator-owned world poses for the bounded ``ontokin.glb/0.1`` adapter.

Ownership is metadata, not a second transform hierarchy. Every exported object
is a scene root, including parts and released bodies. Source event times retain
their exact decimal spelling in metadata; glTF animation times are binary32.
"""

from __future__ import annotations

import math
import hashlib
import json
import struct
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Iterable, Iterator

from . import __version__
from .diagnostics import OntoKinError
from .evaluator import MAX_OUTPUT_RECORDS, MAX_SAMPLES, evaluate, exact_time, preflight, time_text
from .geometry import (SPHERE_RINGS, SPHERE_SEGMENTS, Mesh, assembly_marker,
                       box_mesh, joint_marker, sphere_mesh)
from .model import SceneModel, Vec
from .json_limits import JSONLimitError
from .values import bounded_data


TARGET_CONTRACT = "ontokin.glb/0.1"
CONSTRUCTION_TARGET = "ontokin.glb/0.2"
MAX_KEYFRAMES = 10000
MAX_BAKED_POSES = 250000
MAX_VALIDATION_POSES = 1000000
MAX_MESH_VERTICES = 250000
MAX_GLB_BYTES = 64 * 1024 * 1024
MAX_FPS = 10000
MAX_ANGULAR_STEP = math.pi / 4


def export_error(export_code: str, message: str, model: SceneModel | None = None,
                 *, kind: str = "numeric", details: dict[str, Any] | None = None) -> None:
    """Use the existing diagnostic transport, with adapter-specific details."""
    code, phase, category = {
        "numeric": ("OKL-E-NUMERIC", "evaluation", "numerical_failure"),
        "unsupported": ("OKL-E-CAPABILITY-UNSUPPORTED", "support", "unsupported"),
        "resource": ("OKL-E-RESOURCE", "support", "resource_limit"),
        "options": ("OKL-E-SAMPLE", "inspection", "invalid"),
    }[kind]
    raise OntoKinError(code, message, model.span if model else None, phase=phase,
                       category=category, blocks=["delivered"],
                       details={"target_contract": CONSTRUCTION_TARGET if model is not None and model.profile == "construction-0.1" else TARGET_CONTRACT,
                                "export_code": export_code, **(details or {})},
                       repair=("Use supported visual geometry and the explicitly matching model/delivery profile." if kind == "unsupported" else
                               "Use a smaller scene or export interval, or a lower requested sampling rate." if kind == "resource" else
                               "Supply finite positive export settings and an end time within the scene horizon." if kind == "options" else
                               "Increase sampling for interpolation error; reduce magnitudes or the interval for binary32 precision limits. Review any changed tolerance explicitly."))


def float32(value: float, model: SceneModel | None = None, *, context: str = "value") -> float:
    try:
        result = struct.unpack("<f", struct.pack("<f", value))[0]
    except (OverflowError, struct.error, ValueError) as exc:
        export_error("OKE-E-FLOAT32", f"The exported {context} exceeds finite binary32.", model,
                     details={"context": context, "value": str(value)})
    if not math.isfinite(result):
        export_error("OKE-E-FLOAT32", f"The exported {context} is not finite binary32.", model)
    return 0.0 if result == 0 else result


def rotation_error(a: Iterable[float], b: Iterable[float]) -> float:
    """Orientation angle, stable near zero and invariant to quaternion sign."""
    a, b = tuple(a), tuple(b)
    na, nb = math.hypot(*a), math.hypot(*b)
    if not na or not nb or not math.isfinite(na + nb):
        return math.inf
    a, b = tuple(v / na for v in a), tuple(v / nb for v in b)
    if sum(x * y for x, y in zip(a, b)) < 0:
        b = tuple(-v for v in b)
    return 4 * math.atan2(math.hypot(*(x - y for x, y in zip(a, b))),
                          math.hypot(*(x + y for x, y in zip(a, b))))


@dataclass(frozen=True)
class ExportOptions:
    fps: float = 60
    end: Any = None
    position_tolerance_m: float = .001
    rotation_tolerance_rad: float = .001
    time_tolerance_s: float = .000001
    helpers: bool = True

    def checked_end(self, model: SceneModel) -> Fraction:
        settings = {"fps": self.fps, "position_tolerance_m": self.position_tolerance_m,
                    "rotation_tolerance_rad": self.rotation_tolerance_rad,
                    "time_tolerance_s": self.time_tolerance_s}
        for name, value in settings.items():
            try:
                valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value > 0
            except OverflowError:
                valid = False
            if not valid:
                export_error("OKE-E-OPTIONS", f"{name} must be finite and positive.", model, kind="options")
        if self.fps > MAX_FPS or not isinstance(self.helpers, bool):
            export_error("OKE-E-OPTIONS", f"fps must be at most {MAX_FPS} and helpers must be Boolean.", model, kind="options")
        try:
            end = model.duration if self.end is None else exact_time(self.end)
        except OntoKinError as exc:
            export_error("OKE-E-OPTIONS", "The export end time must be a finite exact decimal timestamp.",
                         model, kind="options", details={"cause": exc.code})
        if not 0 < end <= model.duration:
            export_error("OKE-E-OPTIONS", "The export interval must end after zero and within scene.duration.",
                         model, kind="options", details={"scene_duration_seconds": time_text(model.duration)})
        return end


@dataclass
class BakedNode:
    name: str
    frame_path: str
    mesh: Mesh | None
    color: tuple[float, float, float, float]
    metadata: dict[str, Any]
    translations: list[Vec] = field(default_factory=list)
    rotations_xyzw: list[tuple[float, float, float, float]] = field(default_factory=list)


@dataclass
class BakedScene:
    module_name: str
    scene_name: str
    exact_times: list[Fraction]
    times: list[float]
    boundaries: list[Fraction]
    nodes: list[BakedNode]
    metadata: dict[str, Any]
    report: dict[str, Any]
    options: ExportOptions
    contract: str = TARGET_CONTRACT
    schema_version: str = "0.1"


def checked_contract(model: SceneModel, target_contract: str) -> str:
    expected = {TARGET_CONTRACT: "core-0.1", CONSTRUCTION_TARGET: "construction-0.1"}
    if target_contract not in expected or model.profile != expected[target_contract]:
        export_error("OKE-E-SUPPORT", "The named GLB contract must explicitly match the authored semantic profile.",
                     model, kind="unsupported", details={"target_contract": target_contract,
                                                         "profile": model.profile})
    if model.requested_capabilities or any(diagnostic.code.startswith("OKL-E-") for diagnostic in model.diagnostics):
        export_error("OKE-E-SUPPORT", "The GLB adapter requires a supported, validated model.", model, kind="unsupported")
    return "0.2" if target_contract == CONSTRUCTION_TARGET else "0.1"


def program_metadata(model: SceneModel) -> dict[str, Any]:
    """Check the construction model's sealed source-map identity before export.

    The compiler supplies validated source hashes and locations. The exporter
    receives the model, not source text, and does not invent a dependency hash
    or claim to reconstruct omitted files from GLB metadata.
    """
    try:
        manifest = bounded_data(model.source_manifest)
        if not isinstance(manifest, dict) or manifest.get("schema_version") != "ontokin.bundle/0.1" or manifest.get("entry_source_id") != "entry":
            raise ValueError("Missing canonical source manifest.")
        canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
        revision = "sha256:" + hashlib.sha256(b"ontokin.bundle/0.1\0" + canonical).hexdigest()
        if model.program_revision != revision:
            raise ValueError("Program revision differs from its canonical manifest.")
        units = manifest["units"]
        source_ids = [unit["source_id"] for unit in units]
        if source_ids != sorted(set(source_ids)) or set(source_ids) != set(model.source_provenance) or "entry" not in source_ids:
            raise ValueError("Source mapping differs from the manifest closure.")
        for unit in units:
            source = model.source_provenance[unit["source_id"]]
            if any(source.get(key) != value for key, value in unit.items()):
                raise ValueError("Source mapping hash/name/pin differs from the manifest.")
        if set(model.occurrence_provenance) != set(model.objects):
            raise ValueError("Occurrence source mapping is incomplete.")
        for path, obj in model.objects.items():
            record = model.occurrence_provenance[path]
            if (record.get("path") != path or record.get("element_id") != list(obj.element_id)
                    or record.get("owner_path") != obj.owner or record.get("class_id") != obj.class_name):
                raise ValueError("Occurrence mapping differs from actual object identities.")
            for location in (record.get("declaration"), record.get("definition")):
                if location is not None:
                    source = model.source_provenance[location["source_id"]]
                    if location["source_revision"] != source["source_revision"] or location["filename"] != source["filename"] or not 0 <= location["start_byte"] <= location["end_byte"]:
                        raise ValueError("Occurrence source location differs from its source identity.")
        raw = {"revision": revision, "entry_source_id": "entry", "manifest": manifest,
               "sources": model.source_provenance, "occurrences": model.occurrence_provenance,
               "collections": model.collection_provenance,
               "provenance": "Validated compiler source map; exact source text is not embedded."}
        return bounded_data(raw)
    except JSONLimitError as error:
        export_error("OKE-E-METADATA-BUDGET", "Program provenance exceeds the bounded materialization budget.",
                     model, kind="resource", details=error.details)
    except (KeyError, TypeError, ValueError) as error:
        export_error("OKE-E-PROVENANCE", "Construction delivery requires the complete, matching source-bundle provenance.",
                     model, kind="unsupported", details={"cause": str(error)})


def sampled_states(model: SceneModel, requests: list[Any]) -> Iterator[dict[str, Any]]:
    """Bound each public evaluator request without weakening its own budgets."""
    records = 2 * len(model.objects) + len(model.sites) + len(model.joints) + len(model.actions) + 1
    batch_size = max(1, min(MAX_SAMPLES, MAX_OUTPUT_RECORDS // records))
    for start in range(0, len(requests), batch_size):
        yield from evaluate(model, requests[start:start + batch_size])["samples"]


def _angular_speed_bound(model: SceneModel) -> float:
    # A chain's instantaneous world angular speed is bounded by the sum of
    # root and local speeds. Sum across the whole scene deliberately overbounds
    # simultaneous chains, arbitrary axes, pauses, and the inherited release.
    speeds = [math.hypot(*obj.omega) for obj in model.objects.values()]
    for action in model.actions.values():
        if action.kind == "spin":
            speeds.append(math.hypot(*action.vector))
        elif action.kind == "tween" and model.joints[action.target].kind == "hinge":
            limits = model.joints[action.target].limits
            try:
                speeds.append(float((Fraction(limits[1]) - Fraction(limits[0])) / action.duration))
            except OverflowError:
                speeds.append(math.inf)
    return sum(speeds)


def _timeline(model: SceneModel, options: ExportOptions, end: Fraction,
              boundary_strings: list[str]) -> tuple[list[Fraction], list[float], list[Fraction], float, int]:
    boundaries = sorted({Fraction(0), end} | {exact_time(t) for t in boundary_strings if exact_time(t) <= end})
    speed = _angular_speed_bound(model)
    rate = max(float(options.fps), speed / MAX_ANGULAR_STEP)
    if not math.isfinite(rate) or not math.isfinite(float(end) * rate) or float(end) * rate + 2 > MAX_KEYFRAMES:
        export_error("OKE-E-KEYFRAME-BUDGET", "The interval and angular motion exceed the export keyframe budget.",
                     model, kind="resource", details={"max_keyframes": MAX_KEYFRAMES})
    required: dict[float, Fraction] = {}
    for boundary in boundaries:
        encoded = float32(float(boundary), model, context="boundary time")
        if encoded in required and required[encoded] != boundary:
            export_error("OKE-E-TIMES-COLLAPSED", "Distinct semantic boundaries collapse to the same binary32 key time.",
                         model, details={"source_seconds": [time_text(required[encoded]), time_text(boundary)],
                                         "export_seconds": encoded})
        required[encoded] = boundary
    keys = dict(required)
    removed = 0
    for index in range(1, math.ceil(float(end) * rate)):
        exact = Fraction.from_float(index / rate)
        if exact >= end:
            continue
        encoded = float32(float(exact), model, context="sample time")
        if encoded in keys:
            removed += int(keys[encoded] != exact)
        else:
            keys[encoded] = exact
    times = sorted(keys)
    exact_times = [keys[t] for t in times]
    if len(times) > MAX_KEYFRAMES:
        export_error("OKE-E-KEYFRAME-BUDGET", "Boundary insertion exceeds the export keyframe budget.", model,
                     kind="resource", details={"max_keyframes": MAX_KEYFRAMES})
    errors = [abs(float(Fraction(encoded) - exact)) for exact, encoded in zip(exact_times, times)]
    if max(errors, default=0) > options.time_tolerance_s:
        export_error("OKE-E-TIME-PRECISION", "Binary32 key times exceed the requested timing tolerance.", model,
                     details={"max_time_error_seconds": max(errors), "tolerance_seconds": options.time_tolerance_s})
    # Float rounding and removal of a colliding grid key must not defeat the
    # no-alias bound. A factor of two leaves strict separation from pi.
    if speed and any(float(b - a) * speed >= math.pi / 2 for a, b in zip(exact_times, exact_times[1:])):
        export_error("OKE-E-ROTATION-ALIAS", "Binary32 time spacing cannot preserve the rotation path.", model)
    return exact_times, times, boundaries, speed, removed


def _nodes(model: SceneModel, options: ExportOptions) -> list[BakedNode]:
    nodes: list[BakedNode] = []
    meshes: dict[tuple, Mesh] = {}
    vertex_count = 0
    def charge(mesh: Mesh) -> None:
        nonlocal vertex_count
        vertex_count += len(mesh.positions)
        if vertex_count > MAX_MESH_VERTICES:
            export_error("OKE-E-GEOMETRY-BUDGET", "Mesh generation exceeds the vertex budget.", model,
                         kind="resource", details={"max_mesh_vertices": MAX_MESH_VERTICES})
    def mesh_for(geometry: dict[str, Any]) -> Mesh | None:
        kind = geometry.get("kind")
        if kind == "empty":
            return None
        if kind not in ("sphere", "box"):
            export_error("OKE-E-GEOMETRY", f"Unsupported export geometry: {kind}.", model, kind="unsupported")
        key = (kind, geometry["radius"] if kind == "sphere" else tuple(geometry["size"]))
        if key not in meshes:
            meshes[key] = sphere_mesh(key[1]) if kind == "sphere" else box_mesh(key[1])
            charge(meshes[key])
        return meshes[key]
    properties = None
    if model.profile == "construction-0.1":
        try:
            properties = bounded_data({path: dict(obj.properties) for path, obj in model.objects.items()})
        except JSONLimitError as error:
            export_error("OKE-E-METADATA-BUDGET", "Resolved property materialization exceeds the construction output budget.",
                         model, kind="resource", details=error.details)
    for path, obj in model.objects.items():
        metadata = {"kind": "object", "path": path, "element_id": list(obj.element_id),
                    "owner": obj.owner, "class_name": obj.class_name,
                    "geometry": obj.geometry, "physical": obj.physical,
                    "collision": obj.collision, "authored_motion": obj.motion,
                    "appearance_linear_rgba": list(obj.appearance), "pose_frame": "world",
                    "role": obj.role, "properties": properties[path] if properties is not None else
                    {name: value.to_data() for name, value in obj.properties.items()}}
        if model.profile == "construction-0.1":
            metadata["source_mapping"] = model.occurrence_provenance[path]
            metadata["program_revision"] = model.program_revision
        nodes.append(BakedNode(path, path + ".frame", mesh_for(obj.geometry), obj.appearance, metadata))
    if options.helpers:
        marker = None
        for path, obj in model.objects.items():
            if obj.geometry["kind"] == "empty":
                if marker is None:
                    marker = assembly_marker()
                    charge(marker)
                nodes.append(BakedNode("[visual helper] " + path + " origin", path + ".frame", marker,
                                       (.1, .7, .8, 1.),
                                       {"kind": "visual_helper", "helper_kind": "assembly_origin",
                                        "physical_participation": "none", "related_element_id": list(obj.element_id),
                                        "object_path": path, "frame_path": path + ".frame"}))
        joint_meshes = {}
        for path, joint in model.joints.items():
            if joint.axis not in joint_meshes:
                joint_meshes[joint.axis] = joint_marker(joint.axis)
                charge(joint_meshes[joint.axis])
            nodes.append(BakedNode("[visual helper] " + path + " parent site", joint.parent + ".frame",
                                   joint_meshes[joint.axis], (.9, .65, .08, 1.),
                                   {"kind": "visual_helper", "helper_kind": "joint_parent_site",
                                    "physical_participation": "none", "related_element_id": list(joint.element_id),
                                    "joint_path": path, "frame_path": joint.parent + ".frame",
                                    "meaning": "Parent site marker remains after release; it does not indicate an active constraint."}))
    return nodes


def relationship_metadata(model: SceneModel) -> dict[str, Any]:
    """Record declared relationships without translating them into glTF joints."""
    return {
        "joints": [{"path": j.path, "element_id": list(j.element_id), "kind": j.kind,
                    "parent_site": j.parent, "child_site": j.child, "axis": j.axis,
                    "limits": j.limits, "initial": j.initial} for j in model.joints.values()],
        "follows": [{"path": f.path, "element_id": list(f.element_id), "parent_frame": f.parent,
                     "child_object": f.child, "offset_position_m": f.offset.position,
                     "offset_rotation_wxyz": f.offset.rotation} for f in model.follows.values()],
    }


def build_scene(model: SceneModel, *, options: ExportOptions | None = None,
                source_uri: str | None = None, source_sha256: str | None = None,
                target_contract: str = TARGET_CONTRACT) -> BakedScene:
    """Build a renderer-neutral baked scene; ``export_glb`` also verifies bytes."""
    version = checked_contract(model, target_contract)
    program = program_metadata(model) if target_contract == CONSTRUCTION_TARGET else None
    if program is not None and source_sha256 is not None and source_sha256 != program["sources"]["entry"]["source_revision"]:
        export_error("OKE-E-PROVENANCE", "An optional entry source hash must match the sealed entry file, not the program revision.",
                     model, kind="unsupported")
    options = options or ExportOptions()
    end = options.checked_end(model)
    timeline = preflight(model)
    exact_times, times, boundaries, speed, removed = _timeline(
        model, options, end, timeline["boundary_times_seconds"])
    retained_boundary_records = len(boundaries) * (len(model.objects) + len(model.joints) + len(model.actions))
    if retained_boundary_records > MAX_OUTPUT_RECORDS:
        export_error("OKE-E-BOUNDARY-BUDGET", "Retained boundary metadata exceeds the state-record budget.",
                     model, kind="resource", details={"max_boundary_state_records": MAX_OUTPUT_RECORDS})
    planned_nodes = len(model.objects) + (sum(obj.geometry.get("kind") == "empty" for obj in model.objects.values())
                                          + len(model.joints) if options.helpers else 0)
    if len(exact_times) * planned_nodes > MAX_BAKED_POSES:
        export_error("OKE-E-POSE-BUDGET", "The baked node samples exceed the export pose budget.", model,
                     kind="resource", details={"max_baked_poses": MAX_BAKED_POSES})
    nodes = _nodes(model, options)
    if not nodes:
        export_error("OKE-E-EMPTY-SCENE", "The GLB adapter requires at least one object occurrence.", model, kind="unsupported")
    for sample in sampled_states(model, exact_times):
        for node in nodes:
            frame = sample["frames"][node.frame_path]
            node.translations.append(tuple(frame["position_m"]))
            w, x, y, z = frame["orientation_wxyz"]
            quaternion = (x, y, z, w)
            if node.rotations_xyzw and sum(a * b for a, b in zip(node.rotations_xyzw[-1], quaternion)) < 0:
                quaternion = tuple(-value for value in quaternion)
            node.rotations_xyzw.append(quaternion)
    requests = [{"time_seconds": t, "side": side} for t in boundaries for side in ("before", "after")]
    boundary_states = sampled_states(model, requests)
    max_jump_p = max_jump_r = 0.
    boundary_records = []
    for boundary in boundaries:
        before, after = next(boundary_states), next(boundary_states)
        for node in nodes:
            first, last = before["frames"][node.frame_path], after["frames"][node.frame_path]
            max_jump_p = max(max_jump_p, max(abs(a - b) for a, b in zip(first["position_m"], last["position_m"])))
            max_jump_r = max(max_jump_r, rotation_error(first["orientation_wxyz"], last["orientation_wxyz"]))
        boundary_records.append({"source_seconds": time_text(boundary),
                                 "joint_states_after": after["joints"], "action_states_after": after["actions"],
                                 "pose_authorities_after": {path: record["pose_authority"] for path, record in after["objects"].items()}})
    if max_jump_p > options.position_tolerance_m or max_jump_r > options.rotation_tolerance_rad:
        export_error("OKE-E-DISCONTINUOUS-POSE", "A boundary pose jump cannot be represented by continuous LINEAR tracks.",
                     model, kind="unsupported", details={"max_position_jump_m": max_jump_p,
                                                        "max_rotation_jump_rad": max_jump_r})
    source = {"uri": source_uri, "revision": source_sha256, "editable_source_of_truth": ".ok",
              "provenance": "caller_supplied; exporter receives a validated model, not source bytes" if source_sha256 else
                            "unavailable; caller did not supply source identity"}
    if program is not None:
        source = {"uri": source_uri, "uri_kind": "caller_supplied_bundle_locator",
                  "entry_source_id": "entry", "entry_revision": program["sources"]["entry"]["source_revision"],
                  "editable_source_of_truth": "pinned .ok source bundle",
                  "provenance": "Compiler supplied exact source identities; source text is not embedded."}
    relationships = relationship_metadata(model)
    metadata = {"target_contract": target_contract, "schema_version": version, "source": source,
                "module": model.module_name, "scene": model.scene_name, "profile": model.profile,
                "coordinates": {"handedness": "right", "up": "+Y", "length_unit": "m", "time_unit": "s"},
                "transform_policy": "all_nodes_are_roots_with_baked_world_poses", **relationships,
                "boundary_states": boundary_records, "gravity_m_per_s2": list(model.gravity),
                "motion_authority": "OntoKin semantic evaluator; playback contains no live solver"}
    report = {
        "schema_version": "ontokin.glb-report/" + version, "target_contract": target_contract,
        "outcome": "baked_pending_binary_validation",
        "exporter": {"name": "OntoKin reference GLB exporter", "version": __version__},
        "source": source, "scene": {"module": model.module_name, "name": model.scene_name,
                                   "profile": model.profile, "declared_duration_seconds": time_text(model.duration)},
        "sampling": {"requested_fps": options.fps, "start_seconds": "0", "end_seconds": time_text(end),
                     "keyframe_count": len(times), "angular_speed_bound_rad_per_s": speed,
                     "max_angular_step_rad": MAX_ANGULAR_STEP,
                     "max_key_interval_seconds": max((b - a for a, b in zip(times, times[1:])), default=0.),
                     "boundary_times_seconds": [time_text(t) for t in boundaries],
                     "boundary_time_mapping": [{"source_seconds": time_text(t), "export_seconds": float32(float(t)),
                                                "error_seconds": abs(float(Fraction(float32(float(t))) - t))} for t in boundaries],
                     "max_time_quantization_error_seconds": max(abs(float(Fraction(t) - exact)) for t, exact in zip(times, exact_times)),
                     "redundant_grid_keys_removed": removed,
                     "max_boundary_position_jump_m": max_jump_p, "max_boundary_rotation_jump_rad": max_jump_r},
        "tolerances": {"position_m": options.position_tolerance_m, "rotation_rad": options.rotation_tolerance_rad,
                       "time_seconds": options.time_tolerance_s,
                       "scope": "visual animation adapter; does not relax core evaluator conformance tolerances"},
        "representation": {"coordinates": metadata["coordinates"], "hierarchy": metadata["transform_policy"],
                           "translation_interpolation": "LINEAR", "rotation_interpolation": "shortest-path SLERP",
                           "stored_components": "IEEE 754 binary32", "quaternion_order": "XYZW"},
        "geometry": {"object_nodes": len(model.objects), "authored_mesh_nodes": sum(n.mesh is not None for n in nodes if n.metadata["kind"] == "object"),
                     "helper_nodes": sum(n.metadata["kind"] == "visual_helper" for n in nodes),
                     "sphere_longitude_segments": SPHERE_SEGMENTS, "sphere_latitude_bands": SPHERE_RINGS,
                     "sphere_triangles": 2 * SPHERE_SEGMENTS * (SPHERE_RINGS - 1),
                     "sphere_approximation": "Inscribed triangle surface with radial vertex normals; curved surface is tessellated, not exact.",
                     "box_dimensions": "full XYZ lengths in metres", "appearance": "linear RGBA; metallic=0, roughness=0.7"},
        "retention": {
            "preserved_metadata": ["source URI/revision", "stable occurrence IDs", "ownership", "geometry/physical descriptions",
                                   "resolved parameters", "joint/follow declarations", "boundary lifecycle and pose authority"],
            "baked": ["world translations", "world orientations", "prescribed joint/follow motion", "released sphere trajectories"],
            "not_executable_in_glb": ["source classes/methods", "action commands", "joint constraints", "mass/inertia/gravity", "release transactions"],
            "losses": ["Binary64 transforms and exact timestamps are quantized to binary32.",
                       "Analytical continuous motion becomes sampled LINEAR/SLERP animation.",
                       "Sphere surfaces are triangulated; no exact curved-surface retention is claimed.",
                       "Source syntax, class/callable definitions, source spans, site definitions, and source action/event arguments are not embedded for program reconstruction; retain the .ok source.",
                       "Velocities and accelerations are not native animation channels.",
                       "Blender/game-engine re-export may discard OntoKin extras; .ok remains authoritative."],
            "helpers": "Explicit visual aids with no physical participation; joint markers label parent sites even after release." if options.helpers else "disabled",
            "outside_interval_omitted": end < model.duration,
        },
        "budgets": {"max_keyframes": MAX_KEYFRAMES, "max_baked_poses": MAX_BAKED_POSES,
                    "max_validation_poses": MAX_VALIDATION_POSES, "max_mesh_vertices": MAX_MESH_VERTICES,
                    "max_glb_bytes": MAX_GLB_BYTES, "max_boundary_state_records": MAX_OUTPUT_RECORDS},
    }
    if program is not None:
        metadata["program"] = program
        report["program_revision"] = model.program_revision
        report["program"] = program
        report["retention"]["preserved_metadata"].extend([
            "complete program revision and exact pinned source manifest", "per-source identities and original byte spans",
            "nominal definition identities", "generated collection membership and occurrence source mappings"])
        report["retention"]["not_executable_in_glb"].extend([
            "pinned module resolution", "keyed generator recipes", "initializer precedence and parameter dependencies"])
        losses = report["retention"]["losses"]
        losses[3] = ("Source text, comments, full type declarations, library/generator recipes, parameter dependency expressions, "
                     "site definitions, and action/event source arguments cannot be reconstructed from GLB; retain the full pinned .ok source bundle.")
        losses[-1] = "External re-export may discard source/program/occurrence extras; the pinned .ok source bundle remains authoritative."
    return BakedScene(model.module_name, model.scene_name, exact_times, times, boundaries, nodes, metadata, report,
                      options, contract=target_contract, schema_version=version)
