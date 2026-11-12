#!/usr/bin/env python3
"""CPU-only proposed Blender corner adapter; no destination process or acceptance."""

from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path
import re
import struct
from typing import Any


_source_path = Path(__file__).resolve().parent.parent / "source-normals-c214" / "prototype.py"
_spec = importlib.util.spec_from_file_location("_c215_source_authority", _source_path)
assert _spec is not None and _spec.loader is not None
source = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(source)

ProfileError = source.ProfileError
canonical_bytes, digest, load_json = source.canonical_bytes, source.digest, source.load_json
require = source.require

PROFILE = "c210-blender-corner-adapter-c215/0.1"
LOCK_SCHEMA = "ontokin.receiving-input-lock/0.1"
OBSERVATIONS_SCHEMA = "ontokin.blender-corner-observations/0.1"
REPORT_SCHEMA = "ontokin.blender-corner-loss-report/0.1"
NATIVE_FRAME = "blender-object-local-right-handed-z-up"
EXECUTED_C211 = "66f1940c4c99f52dfdea835445cdc380498815f7"
HELD_C211 = "cdae8b582a37e37f76f142f07039ba74cedc08ad"
ARTIFACT_KEYS = {"receiver_source", "importer_source", "build_record", "import_settings", "scene"}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _fields(value: Any, fields: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == fields, "Unexpected " + label + " fields")


def _text(value: Any, label: str) -> None:
    require(isinstance(value, str) and bool(value.strip()), label + " must be nonempty text")


def _index(value: Any, label: str) -> None:
    require(type(value) is int and value >= 0, label + " must be a non-bool nonnegative integer")


def _vector(value: Any, nonzero: bool = False) -> tuple[tuple[float, float, float] | None, str | None]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return None, "expected-three-components"
    if any(type(item) not in (int, float) for item in value):
        return None, "non-numeric-or-bool-component"
    try:
        result = tuple(float(item) for item in value)
    except (OverflowError, ValueError):
        return None, "component-outside-finite-float64"
    if not all(math.isfinite(item) for item in result):
        return None, "nonfinite-component"
    if nonzero and not any(result):
        return None, "zero-vector"
    return result, None


def to_source_frame(vector: tuple | list) -> tuple[float, float, float]:
    """Inverse proper rotation, for object-local positions and normal directions."""
    return vector[0], vector[2], -vector[1]


def _position_index(source_triangles: list, reverse: bool = False) -> dict:
    result: dict[tuple, list] = {}
    for triangle_index, triangle in enumerate(source_triangles):
        require(isinstance(triangle, (list, tuple)) and len(triangle) == 3, "Expected source position triangle")
        vectors = [_vector(position) for position in triangle]
        require(all(reason is None for _, reason in vectors), "Invalid source position")
        positions = [vector for vector, _ in vectors]
        for start in range(3):
            permutation = tuple((start + (-corner if reverse else corner)) % 3 for corner in range(3))
            key = tuple(positions[corner] for corner in permutation)
            result.setdefault(key, []).append((triangle_index, permutation))
    return result


def position_candidates(source_triangles: list, native_positions: list, reverse: bool = False) -> list:
    """Return geometric candidates only; this helper cannot issue source or native authority."""
    require(type(reverse) is bool, "Reverse flag must be boolean")
    require(isinstance(native_positions, (list, tuple)) and len(native_positions) == 3, "Expected native position triangle")
    vectors = [_vector(position) for position in native_positions]
    require(all(reason is None for _, reason in vectors), "Invalid native position")
    key = tuple(to_source_frame(vector) for vector, _ in vectors)
    return _position_index(source_triangles, reverse).get(key, [])


def _validate_context(payload: dict, input_lock: dict, artifacts: dict) -> tuple[dict, dict]:
    fields = {"schema_version", "profile", "sourcePayloadSha256", "sourceInputs", "receiverRevision",
              "receiverDisposition", "artifacts"}
    _fields(input_lock, fields, "input lock")
    require(input_lock["schema_version"] == LOCK_SCHEMA and input_lock["profile"] == PROFILE, "Unsupported input lock")
    require(input_lock["sourcePayloadSha256"] == digest(canonical_bytes(payload)), "Stale locked payload")
    require(canonical_bytes(input_lock["sourceInputs"]) == canonical_bytes(source.ACCEPTED_INPUTS), "Stale locked source triple")
    revision, disposition = input_lock["receiverRevision"], input_lock["receiverDisposition"]
    require(isinstance(revision, str) and HEX40.fullmatch(revision) is not None, "Invalid receiver Git revision")
    require(disposition in ("c211-executed-source", "c211-held-unexecuted-correction", "future-proposed-source", "synthetic-fixture"),
            "Unknown receiver source disposition")
    if disposition == "c211-executed-source":
        require(revision == EXECUTED_C211, "Executed C211 source revision differs")
    elif disposition == "c211-held-unexecuted-correction":
        require(revision == HELD_C211, "Held C211 source revision differs")
    else:
        require(revision not in (EXECUTED_C211, HELD_C211), "Known C211 source disposition cannot be relabeled")
    _fields(artifacts, ARTIFACT_KEYS, "artifact bytes")
    _fields(input_lock["artifacts"], ARTIFACT_KEYS, "artifact locks")
    for name in sorted(ARTIFACT_KEYS):
        data, binding = artifacts[name], input_lock["artifacts"][name]
        if name == "scene" and data is None:
            require(binding is None, "Missing scene differs from locked bytes")
            continue
        require(type(data) is bytes and bool(data), "Artifact must contain bytes: " + name)
        _fields(binding, {"bytes", "sha256"}, "artifact descriptor")
        require(type(binding["bytes"]) is int and binding["bytes"] > 0, "Artifact length must be a positive integer")
        require(binding == {"bytes": len(data), "sha256": digest(data)}, "Artifact differs from independent lock: " + name)
    build, settings = load_json(artifacts["build_record"]), load_json(artifacts["import_settings"])
    _fields(build, {"application", "version", "executableSha256", "buildHash", "importerSourceSha256"}, "build record")
    require(build["application"] == "Blender", "Unsupported application")
    require(isinstance(build["version"], list) and len(build["version"]) == 3 and
            all(type(value) is int and value >= 0 for value in build["version"]), "Invalid exact build version")
    require(isinstance(build["executableSha256"], str) and SHA256.fullmatch(build["executableSha256"]) is not None,
            "Executable digest missing or malformed")
    _text(build["buildHash"], "Build hash")
    require(build["importerSourceSha256"] == digest(artifacts["importer_source"]), "Build/importer source binding differs")
    require(isinstance(settings, dict), "Import settings must be a JSON object")
    return build, settings


def build_report(payload: dict, observations: dict, glb: bytes, bundle: bytes, semantic: bytes,
                 *, input_lock: dict, artifacts: dict) -> dict:
    """Map a locked recorded envelope; even a native label remains unverified evidence."""
    validation = source.validate_payload(payload, glb, bundle, semantic)
    build, settings = _validate_context(payload, input_lock, artifacts)
    fields = {"schema_version", "profile", "kind", "inputLockSha256", "sourcePayloadSha256", "frame", "phase", "producer", "objects"}
    _fields(observations, fields, "observations")
    require(observations["schema_version"] == OBSERVATIONS_SCHEMA and observations["profile"] == PROFILE, "Unsupported observation profile")
    require(observations["inputLockSha256"] == digest(canonical_bytes(input_lock)), "Observation input lock differs")
    require(observations["sourcePayloadSha256"] == validation["payloadSha256"], "Observation source payload differs")
    require(observations["frame"] == NATIVE_FRAME, "Unsupported native normal/position frame")
    require(observations["kind"] in ("synthetic-cpu", "native-unverified"), "Unsupported observation kind")
    if observations["kind"] == "synthetic-cpu":
        require(observations["phase"] == "synthetic", "Synthetic observation phase differs")
    else:
        require(observations["phase"] in ("import", "reopen"), "Native observation phase missing")
        require(type(artifacts["scene"]) is bytes and bool(artifacts["scene"]), "Native-unverified input requires exact observed scene bytes")
        require(input_lock["receiverDisposition"] not in ("c211-held-unexecuted-correction", "synthetic-fixture"),
                "Held/unexecuted correction or synthetic receiver cannot supply a native label")
    _text(observations["producer"], "Observation producer")
    require(isinstance(observations["objects"], list), "Observed objects must be an array")

    instances = {item["node"]: item for item in payload["instances"]}
    triangle_corners: dict[tuple, list] = {}
    for corner in payload["corners"]:
        triangle_corners.setdefault(tuple(corner["key"][:3]), []).append(corner)
    mesh_tables = {}
    for mesh in {instance["mesh"] for instance in instances.values()}:
        keys = [key for key in triangle_corners if key[0] == mesh]
        triangles = [[struct.unpack("<3f", bytes.fromhex(corner["position_f32le"]))
                      for corner in triangle_corners[key]] for key in keys]
        mesh_tables[mesh] = (keys, _position_index(triangles), _position_index(triangles, True))
    expected = {}
    for instance in payload["instances"]:
        for corner in payload["corners"]:
            if corner["key"][0] == instance["mesh"]:
                expected[(instance["node"], *corner["key"])] = corner
    claims: dict[tuple, list] = {}
    diagnostics, seen_objects, seen_nodes = [], set(), set()
    native_triangle_count = 0
    for obj in observations["objects"]:
        _fields(obj, {"nativeObject", "nativeMesh", "sourceNode", "sourceMesh", "sourcePath", "elementId", "triangles"}, "native object")
        _text(obj["nativeObject"], "Native object identity")
        _text(obj["nativeMesh"], "Native mesh identity")
        _index(obj["sourceNode"], "Source node")
        _index(obj["sourceMesh"], "Source mesh")
        require(obj["sourceNode"] in instances, "Unknown source node")
        instance = instances[obj["sourceNode"]]
        require(obj["sourceMesh"] == instance["mesh"] and obj["sourcePath"] == instance["path"] and
                canonical_bytes(obj["elementId"]) == canonical_bytes(instance["element_id"]), "Native object/source instance identity differs")
        require(obj["nativeObject"] not in seen_objects and obj["sourceNode"] not in seen_nodes, "Duplicate or ambiguous native object binding")
        seen_objects.add(obj["nativeObject"])
        seen_nodes.add(obj["sourceNode"])
        require(isinstance(obj["triangles"], list), "Native triangles must be an array")
        source_keys, forward_index, reverse_index = mesh_tables[instance["mesh"]]
        seen_triangles, seen_loops = set(), set()
        for triangle in obj["triangles"]:
            _fields(triangle, {"nativeTriangle", "loops", "positions", "normals"}, "native triangle")
            _index(triangle["nativeTriangle"], "Native triangle")
            require(triangle["nativeTriangle"] not in seen_triangles, "Duplicate native triangle identifier")
            seen_triangles.add(triangle["nativeTriangle"])
            loops = triangle["loops"]
            require(isinstance(loops, list) and len(loops) == 3 and all(type(value) is int and value >= 0 for value in loops), "Invalid native loop identifiers")
            require(len(set(loops)) == 3 and not seen_loops.intersection(loops), "Duplicate native loop identifier in triangulated object")
            seen_loops.update(loops)
            require(isinstance(triangle["positions"], list) and len(triangle["positions"]) == 3, "Native position triangle needs three corners")
            require(isinstance(triangle["normals"], list) and len(triangle["normals"]) == 3, "Native normal triangle needs three corners")
            native_triangle_count += 1
            identity = {"nativeObject": obj["nativeObject"], "nativeMesh": obj["nativeMesh"], "nativeTriangle": triangle["nativeTriangle"]}
            vectors = [_vector(position) for position in triangle["positions"]]
            bad_position = next((reason for _, reason in vectors if reason is not None), None)
            if bad_position:
                diagnostics.append({**identity, "status": "invalid", "reason": "invalid-position:" + bad_position, "candidateSourceTriangles": []})
                continue
            position_key = tuple(to_source_frame(vector) for vector, _ in vectors)
            candidates = forward_index.get(position_key, [])
            mapping_status, reason = "observed", None
            if not candidates:
                candidates = reverse_index.get(position_key, [])
                mapping_status, reason = "invalid", "reversed-winding" if candidates else "unmatched-position-triangle"
            if len(candidates) > 1:
                mapping_status, reason = "ambiguous", "multiple-source-triangle-mappings"
            if mapping_status != "observed":
                diagnostics.append({**identity, "status": mapping_status, "reason": reason,
                                    "candidateSourceTriangles": [[instance["node"], *source_keys[index]] for index, _ in candidates]})
            for source_index, permutation in candidates:
                source_triangle_key = source_keys[source_index]
                for native_corner, source_corner in enumerate(permutation):
                    key = (instance["node"], *source_triangle_key, source_corner)
                    claim = {**identity, "nativeLoop": loops[native_corner], "nativeCorner": native_corner,
                             "mappingStatus": mapping_status, "reason": reason, "normal": triangle["normals"][native_corner]}
                    claims.setdefault(key, []).append(claim)

    duplicate_claims = {}
    for key, matches in claims.items():
        if len(matches) <= 1:
            continue
        for match in matches:
            native_key = (match["nativeObject"], match["nativeTriangle"])
            item = duplicate_claims.setdefault(native_key, {field: match[field] for field in ("nativeObject", "nativeMesh", "nativeTriangle")})
            item.setdefault("candidateSourceTriangles", set()).add(key[:4])
    for native_key, item in duplicate_claims.items():
        previous = [entry for entry in diagnostics if (entry["nativeObject"], entry["nativeTriangle"]) == native_key]
        diagnostics = [entry for entry in diagnostics if (entry["nativeObject"], entry["nativeTriangle"]) != native_key]
        diagnostics.append({**item, "status": "ambiguous", "reason": "multiple-native-claims",
                            "priorReasons": [entry["reason"] for entry in previous],
                            "candidateSourceTriangles": [list(key) for key in sorted(item["candidateSourceTriangles"])]})
    counts = {"expected": len(expected), "observed": 0, "missing": 0, "ambiguous": 0, "invalid": 0}
    rows, maximum_component, maximum_angle = [], None, None
    for key, corner in expected.items():
        row = {"key": list(key), "sourceVertex": corner["vertex"], "sourceWinding": corner["winding"],
               "sourceNormalF32le": corner["normal_f32le"]}
        matches = claims.get(key, [])
        native_fields = ("nativeObject", "nativeMesh", "nativeTriangle", "nativeLoop", "nativeCorner")
        if not matches:
            row.update(status="missing", reason="no-matched-native-corner")
        elif len(matches) > 1 or any(match["mappingStatus"] == "ambiguous" for match in matches):
            row.update(status="ambiguous", reason="multiple-native-claims" if len(matches) > 1 else "multiple-source-triangle-mappings",
                       nativeClaims=[{field: match[field] for field in native_fields} for match in matches])
        else:
            match = matches[0]
            row.update({field: match[field] for field in native_fields})
            if match["mappingStatus"] == "invalid":
                row.update(status="invalid", reason=match["reason"])
            else:
                vector, invalid = _vector(match["normal"], nonzero=True)
                if invalid:
                    row.update(status="invalid", reason=invalid)
                else:
                    converted = to_source_frame(vector)
                    original = struct.unpack("<3f", bytes.fromhex(corner["normal_f32le"]))
                    delta = [a - b for a, b in zip(converted, original)]
                    component = max(abs(value) for value in delta)
                    a, b = source._unit(original), source._unit(converted)
                    cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
                    angle = math.degrees(math.atan2(math.hypot(*cross), sum(x * y for x, y in zip(a, b))))
                    require(math.isfinite(component) and math.isfinite(angle), "Nonfinite loss measurement")
                    row.update(status="observed", sourceNormal=list(original), observedNormal=list(converted), nativeNormal=list(vector),
                               componentDelta=delta, maximumComponentDifference=component, angularDifferenceDegrees=angle)
                    maximum_component = component if maximum_component is None else max(maximum_component, component)
                    maximum_angle = angle if maximum_angle is None else max(maximum_angle, angle)
        counts[row["status"]] += 1
        rows.append(row)
    try:
        observation_digest, canonicalizable = digest(canonical_bytes(observations)), True
    except ProfileError:
        observation_digest, canonicalizable = None, False
    return {"schema_version": REPORT_SCHEMA, "profile": PROFILE, "sourcePayloadSha256": validation["payloadSha256"],
            "inputLockSha256": digest(canonical_bytes(input_lock)), "sourceInputs": input_lock["sourceInputs"],
            "receiverRevision": input_lock["receiverRevision"], "receiverDisposition": input_lock["receiverDisposition"],
            "artifactBindings": input_lock["artifacts"], "buildRecord": build, "importSettings": settings,
            "sceneBound": artifacts["scene"] is not None, "observationKind": observations["kind"], "phase": observations["phase"],
            "producer": observations["producer"], "sourceFrame": source.FRAME, "nativeFrame": NATIVE_FRAME,
            "observationsSha256": observation_digest, "observationsCanonicalJson": canonicalizable,
            "mappingPolicy": "exact-object-local-position-triangles-cyclic-winding-no-normal-disambiguation",
            "sourceAuthority": "EXACT_SOURCE_PAYLOAD", "provenanceAuthenticated": False,
            "receiverExecutionVerified": False, "nativeFidelityEstablished": False, "receivingEvidence": False,
            "acceptanceTolerance": None, "shadingAcceptance": "NOT_EVALUATED",
            "summary": {**counts, "nativeObjects": len(observations["objects"]), "nativeTriangles": native_triangle_count,
                        "nativeInvalidTriangles": sum(item["status"] == "invalid" for item in diagnostics),
                        "nativeAmbiguousTriangles": sum(item["status"] == "ambiguous" for item in diagnostics),
                        "maximumComponentDifference": maximum_component, "maximumAngularDifferenceDegrees": maximum_angle},
            "nativeDiagnostics": diagnostics, "corners": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("payload", "observations", "glb", "bundle", "semantic", "input-lock", "receiver-source", "importer-source", "build-record", "import-settings", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--scene", type=Path)
    args = parser.parse_args()
    artifacts = {"receiver_source": args.receiver_source.read_bytes(), "importer_source": args.importer_source.read_bytes(), "build_record": args.build_record.read_bytes(),
                 "import_settings": args.import_settings.read_bytes(), "scene": args.scene.read_bytes() if args.scene else None}
    report = build_report(load_json(args.payload.read_bytes()), load_json(args.observations.read_bytes()), args.glb.read_bytes(),
                          args.bundle.read_bytes(), args.semantic.read_bytes(), input_lock=load_json(args.input_lock.read_bytes()), artifacts=artifacts)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(report) + b"\n")


if __name__ == "__main__":
    main()
