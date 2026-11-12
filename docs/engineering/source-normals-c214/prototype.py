#!/usr/bin/env python3
"""C214 isolated CPU prototype; this module does not launch a destination."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
from typing import Any


SCHEMA = "ontokin.source-normal-payload/0.1"
OBSERVATIONS_SCHEMA = "ontokin.normal-observations/0.1"
REPORT_SCHEMA = "ontokin.normal-loss-report/0.1"
FRAME = "gltf-object-local-right-handed-y-up"
PROFILE = "c210-accepted-after-source-normals-c214/0.1"
ACCEPTED_INPUTS = {
    "glb": {"bytes": 185236, "sha256": "sha256:05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8"},
    "bundle": {"bytes": 4065, "sha256": "sha256:83ca659aadd23d7ce09ebcd209c210efd69028ca6e51ebd70d69ec47f65098e4"},
    "semantic": {"bytes": 191181, "sha256": "sha256:1077eff813807c0b2058d35e2007c234b4d8c157f6dc0177f5a548924edd2c34"},
}
KEY_FIELDS = {"key", "vertex", "winding", "normal_f32le", "position_f32le"}
HEX12 = re.compile(r"[0-9a-f]{24}\Z")


class ProfileError(ValueError):
    """A refusal at the finite proposed profile boundary."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileError(message)


def canonical_bytes(value: Any) -> bytes:
    """Canonical JSON; reject NaN and infinity instead of inventing JSON values."""
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ProfileError("Value has no canonical JSON encoding") from exc


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON member: " + key)
        result[key] = value
    return result


def load_json(data: bytes) -> Any:
    def invalid_constant(value: str) -> None:
        raise ProfileError("Nonfinite JSON token: " + value)
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=invalid_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProfileError("Invalid UTF-8 JSON") from exc


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    require(type(value) is int and value >= minimum, label + " must be a non-bool integer")
    return value


def _index(items: Any, index: Any, label: str) -> Any:
    _integer(index, label)
    require(isinstance(items, list) and index < len(items), label + " is outside its array")
    return items[index]


def decode_glb(glb: bytes) -> tuple[dict, bytes]:
    """Decode only the two-chunk, embedded-buffer GLB subset used by C210."""
    require(type(glb) is bytes and len(glb) >= 28, "GLB is incomplete")
    magic, version, length = struct.unpack_from("<4sII", glb)
    require(magic == b"glTF" and version == 2 and length == len(glb), "Invalid GLB header")
    chunks = []
    cursor = 12
    while cursor < len(glb):
        require(cursor + 8 <= len(glb), "Truncated GLB chunk header")
        size, kind = struct.unpack_from("<II", glb, cursor)
        cursor += 8
        require(size % 4 == 0 and cursor + size <= len(glb), "Invalid GLB chunk size")
        chunks.append((kind, glb[cursor:cursor + size]))
        cursor += size
    require([kind for kind, _ in chunks] == [0x4E4F534A, 0x004E4942], "Unsupported GLB chunks")
    document, binary = load_json(chunks[0][1]), chunks[1][1]
    require(isinstance(document, dict), "GLB JSON must be an object")
    buffers = document.get("buffers")
    require(isinstance(buffers, list) and len(buffers) == 1, "One embedded buffer is required")
    require(isinstance(buffers[0], dict) and "uri" not in buffers[0], "External buffers are unsupported")
    length = _integer(buffers[0].get("byteLength"), "buffer length")
    require(length <= len(binary) <= length + 3, "GLB binary size differs from buffer")
    require(binary[length:] == b"\0" * (len(binary) - length), "GLB binary padding is nonzero")
    require(document.get("asset", {}).get("version") == "2.0", "Unsupported glTF version")
    require(not document.get("extensionsRequired"), "Required GLB extensions are unsupported")
    return document, binary[:length]


def accessor_bytes(document: dict, binary: bytes, index: int,
                   component_type: int, kind: str) -> list[bytes]:
    accessor = _index(document.get("accessors"), index, "accessor")
    require(isinstance(accessor, dict), "Accessor must be an object")
    require(accessor.get("componentType") == component_type and accessor.get("type") == kind,
            "Unsupported accessor component/type")
    require("sparse" not in accessor and not accessor.get("normalized", False), "Sparse/normalized accessor unsupported")
    view = _index(document.get("bufferViews"), accessor.get("bufferView"), "bufferView")
    require(isinstance(view, dict) and type(view.get("buffer")) is int and view["buffer"] == 0,
            "Accessor buffer must be zero")
    component_size = {5121: 1, 5123: 2, 5125: 4, 5126: 4}[component_type]
    width = component_size * {"SCALAR": 1, "VEC3": 3}[kind]
    view_start = _integer(view.get("byteOffset", 0), "bufferView offset")
    view_size = _integer(view.get("byteLength"), "bufferView length")
    offset = _integer(accessor.get("byteOffset", 0), "accessor offset")
    count = _integer(accessor.get("count"), "accessor count", 1)
    stride = _integer(view.get("byteStride", width), "accessor stride", width)
    require(stride % component_size == 0 and offset % component_size == 0 and
            view_start % component_size == 0, "Misaligned accessor")
    require(view_start + view_size <= len(binary), "bufferView exceeds binary data")
    require(offset + (count - 1) * stride + width <= view_size, "Accessor exceeds bufferView")
    return [binary[view_start + offset + n * stride:view_start + offset + n * stride + width]
            for n in range(count)]


def _vector(raw: bytes, label: str, nonzero: bool = True) -> tuple[float, float, float]:
    require(len(raw) == 12, label + " must contain three float32 values")
    values = struct.unpack("<3f", raw)
    require(all(math.isfinite(value) for value in values), label + " is nonfinite")
    if nonzero:
        require(any(value != 0.0 for value in values), label + " is zero")
    return values


def source_corners(document: dict, binary: bytes) -> list[dict]:
    """Decode exact source corners; equality of positions never merges identities."""
    meshes = document.get("meshes")
    require(isinstance(meshes, list) and meshes, "At least one mesh is required")
    corners = []
    for mesh_index, mesh in enumerate(meshes):
        require(isinstance(mesh, dict), "Mesh must be an object")
        primitives = mesh.get("primitives")
        require(isinstance(primitives, list) and primitives, "Mesh primitives missing")
        for primitive_index, primitive in enumerate(primitives):
            require(isinstance(primitive, dict) and primitive.get("mode", 4) == 4 and
                    type(primitive.get("mode", 4)) is int, "Only TRIANGLES is supported")
            require(not primitive.get("targets") and not primitive.get("extensions"), "Morph/compressed primitives unsupported")
            attributes = primitive.get("attributes")
            require(isinstance(attributes, dict) and {"POSITION", "NORMAL"} <= set(attributes), "Position/normal attributes required")
            positions = accessor_bytes(document, binary, attributes["POSITION"], 5126, "VEC3")
            normals = accessor_bytes(document, binary, attributes["NORMAL"], 5126, "VEC3")
            require(len(normals) == len(positions), "Normal and position counts differ")
            for raw in positions:
                _vector(raw, "Source position", nonzero=False)
            for raw in normals:
                _vector(raw, "Source normal")
            accessor = _index(document.get("accessors"), primitive.get("indices"), "indices accessor")
            component = accessor.get("componentType")
            require(type(component) is int and component in (5121, 5123, 5125), "Unsigned indices required")
            raw_indices = accessor_bytes(document, binary, primitive["indices"], component, "SCALAR")
            indices = [int.from_bytes(raw, "little") for raw in raw_indices]
            require(len(indices) % 3 == 0, "Triangle index count must be divisible by three")
            require(all(index < len(positions) for index in indices), "Vertex index out of bounds")
            for triangle, start in enumerate(range(0, len(indices), 3)):
                winding = indices[start:start + 3]
                require(len(set(winding)) == 3, "Degenerate repeated-index triangle unsupported")
                for corner, vertex in enumerate(winding):
                    corners.append({"key": [mesh_index, primitive_index, triangle, corner],
                                    "vertex": vertex, "winding": winding.copy(),
                                    "normal_f32le": normals[vertex].hex(),
                                    "position_f32le": positions[vertex].hex()})
    return corners


def _bundle_manifest(bundle: dict) -> tuple[dict, str]:
    require(isinstance(bundle, dict) and set(bundle) == {"schema_version", "entry", "modules"}, "Unexpected bundle fields")
    require(bundle["schema_version"] == "ontokin.bundle/0.1", "Unsupported bundle schema")
    require(isinstance(bundle["modules"], list), "Bundle modules must be an array")
    units = []
    for entry, unit in [(True, bundle["entry"]), *[(False, unit) for unit in bundle["modules"]]]:
        fields = {"filename", "source"} if entry else {"package_id", "version", "filename", "source"}
        require(isinstance(unit, dict) and set(unit) == fields, "Unexpected source-unit fields")
        require(all(isinstance(value, str) and value for value in unit.values()), "Source-unit values must be nonempty strings")
        package, version = (None, None) if entry else (unit["package_id"], unit["version"])
        source_id = "entry" if entry else "package:" + package + "@" + version
        units.append({"source_id": source_id, "filename": unit["filename"], "package_id": package,
                      "version": version, "source_revision": digest(unit["source"].encode("utf-8"))})
    require(len({unit["source_id"] for unit in units}) == len(units), "Duplicate source identity")
    manifest = {"schema_version": "ontokin.bundle/0.1", "entry_source_id": "entry",
                "units": sorted(units, key=lambda unit: unit["source_id"])}
    return manifest, digest(b"ontokin.bundle/0.1\0" + canonical_bytes(manifest))


def _instance_bindings(document: dict, binary: bytes, semantic: dict) -> list[dict]:
    nodes, objects = document.get("nodes"), semantic.get("objects")
    require(isinstance(nodes, list) and isinstance(objects, list) and len(nodes) == len(objects), "Object/node coverage differs")
    instances, seen_nodes, seen_paths, seen_ids = [], set(), set(), set()
    for obj in objects:
        require(isinstance(obj, dict), "Semantic object must be an object")
        binding = obj.get("geometry_binding", {})
        node_index, mesh_index = binding.get("node"), binding.get("mesh")
        node = _index(nodes, node_index, "node")
        _integer(mesh_index, "mesh")
        require(node_index not in seen_nodes and node.get("mesh") == mesh_index, "Ambiguous node/mesh binding")
        require("skin" not in node and not node.get("weights"), "Skinned/morphed nodes unsupported")
        path, element_id = obj.get("path"), obj.get("element_id")
        require(isinstance(path, str) and path and isinstance(element_id, list) and element_id and
                all(isinstance(part, str) and part for part in element_id), "Invalid source object identity")
        require(path not in seen_paths and tuple(element_id) not in seen_ids, "Ambiguous source object identity")
        actual = node.get("extras", {}).get("ontokin", {})
        require(actual.get("path") == path and actual.get("element_id") == element_id, "Node source identity differs")
        primitives = _index(document.get("meshes"), mesh_index, "mesh")["primitives"]
        expected_primitives = binding.get("primitives")
        require(isinstance(expected_primitives, list) and len(primitives) == len(expected_primitives), "Semantic primitive coverage differs")
        for index, (primitive, declared) in enumerate(zip(primitives, expected_primitives)):
            require(type(declared.get("primitive")) is int and declared["primitive"] == index, "Semantic primitive index differs")
            for label in ("NORMAL", "POSITION", "indices"):
                accessor_index = primitive["indices"] if label == "indices" else primitive["attributes"][label]
                description = declared["indices"] if label == "indices" else declared["attributes"][label]
                actual_accessor = _index(document["accessors"], accessor_index, "bound accessor")
                for left, right in (("accessor", accessor_index), ("buffer_view", actual_accessor["bufferView"]),
                                    ("component_type", actual_accessor["componentType"]),
                                    ("count", actual_accessor["count"]), ("type", actual_accessor["type"])):
                    require(canonical_bytes(description.get(left)) == canonical_bytes(right), "Semantic accessor descriptor differs")
                data = accessor_bytes(document, binary, accessor_index, actual_accessor["componentType"], actual_accessor["type"])
                require(description.get("data_sha256") == digest(b"".join(data)), "Semantic accessor bytes differ")
        seen_nodes.add(node_index)
        seen_paths.add(path)
        seen_ids.add(tuple(element_id))
        instances.append({"node": node_index, "mesh": mesh_index, "path": path, "element_id": element_id})
    require(seen_nodes == set(range(len(nodes))), "Source nodes are missing")
    require({item["mesh"] for item in instances} == set(range(len(document["meshes"]))), "Unbound source mesh")
    return sorted(instances, key=lambda item: item["node"])


def build_payload(glb: bytes, bundle: bytes, semantic: bytes) -> dict:
    """Build this finite accepted C210 payload, never accept an arbitrary new source."""
    inputs = {"glb": glb, "bundle": bundle, "semantic": semantic}
    for name, data in inputs.items():
        require(type(data) is bytes, "Input must be bytes: " + name)
        require({"bytes": len(data), "sha256": digest(data)} == ACCEPTED_INPUTS[name], "Stale or unaccepted input: " + name)
    document, binary = decode_glb(glb)
    sidecar, program = load_json(semantic), load_json(bundle)
    manifest, revision = _bundle_manifest(program)
    require(sidecar.get("schema_version") == "ontokin.semantic-export/0.1", "Unsupported semantic schema")
    binding = sidecar.get("binding", {})
    require(binding.get("source_manifest") == manifest and binding.get("accepted_program_revision") == revision,
            "Semantic source revision differs from exact source bytes")
    require(binding.get("artifact") == {**ACCEPTED_INPUTS["glb"], "target_contract": "ontokin.glb/0.2"},
            "Semantic artifact binding differs")
    provenance = document.get("extras", {}).get("ontokin", {}).get("program", {})
    require(provenance.get("manifest") == manifest and provenance.get("revision") == revision,
            "GLB source provenance differs")
    coordinates = sidecar.get("coordinates", {})
    require(coordinates.get("geometry_frame") == "object-local" and coordinates.get("handedness") == "right"
            and coordinates.get("up") == "+Y", "Unsupported source coordinate frame")
    return {"schema_version": SCHEMA, "profile": PROFILE, "status": "proposed-experimental",
            "sourceFrame": FRAME, "encoding": "three-ieee754-binary32-little-endian-hex",
            "binding": {"inputs": json.loads(canonical_bytes(ACCEPTED_INPUTS)),
                        "accepted_program_revision": revision,
                        "acceptance_authority": "retained C210 acceptance evidence; this prototype grants none"},
            "instances": _instance_bindings(document, binary, sidecar),
            "corners": source_corners(document, binary)}


def validate_payload(payload: dict, glb: bytes, bundle: bytes, semantic: bytes) -> dict:
    """Validate exact canonical source mapping, including array order and signed zero."""
    require(isinstance(payload, dict), "Payload must be an object")
    expected = build_payload(glb, bundle, semantic)
    encoded = canonical_bytes(payload)
    require(encoded == canonical_bytes(expected), "Payload differs from authoritative source mapping")
    return {"status": "EXACT_SOURCE_PAYLOAD", "payloadSha256": digest(encoded),
            "sourceCorners": len(expected["corners"]), "instances": len(expected["instances"]),
            "nativeFidelityEstablished": False, "receivingEvidence": False}


def _unit(values: tuple | list) -> tuple[float, float, float]:
    scale = max(abs(value) for value in values)
    scaled = tuple(value / scale for value in values)
    length = math.hypot(*scaled)
    return tuple(value / length for value in scaled)


def _observation_vector(value: Any) -> tuple[tuple[float, float, float] | None, str | None]:
    if not isinstance(value, list) or len(value) != 3:
        return None, "expected-three-components"
    if any(type(item) not in (int, float) for item in value):
        return None, "non-numeric-or-bool-component"
    try:
        vector = tuple(float(item) for item in value)
    except (OverflowError, ValueError):
        return None, "component-outside-finite-float64"
    if not all(math.isfinite(item) for item in vector):
        return None, "nonfinite-component"
    if not any(item != 0.0 for item in vector):
        return None, "zero-vector"
    return vector, None


def build_loss_report(payload: dict, observations: dict, glb: bytes, bundle: bytes, semantic: bytes) -> dict:
    """Report synthetic observations only; no pass threshold or native claim exists."""
    validation = validate_payload(payload, glb, bundle, semantic)
    fields = {"schema_version", "sourcePayloadSha256", "sourceFrame", "kind", "producer", "records"}
    require(isinstance(observations, dict) and set(observations) == fields, "Unexpected observation envelope")
    require(observations["schema_version"] == OBSERVATIONS_SCHEMA, "Unsupported observation schema")
    require(observations["sourcePayloadSha256"] == validation["payloadSha256"], "Stale source payload observation binding")
    require(observations["sourceFrame"] == FRAME, "Observation coordinate frame differs; conversion is not implemented")
    require(observations["kind"] == "synthetic-cpu", "Only explicitly synthetic CPU observations are implemented")
    require(isinstance(observations["producer"], str) and observations["producer"].strip(), "Observation producer missing")
    require(isinstance(observations["records"], list), "Observation records must be an array")
    by_mesh: dict[int, list] = {}
    for corner in payload["corners"]:
        by_mesh.setdefault(corner["key"][0], []).append(corner)
    expected = {}
    for instance in payload["instances"]:
        for corner in by_mesh[instance["mesh"]]:
            expected[(instance["node"], *corner["key"])] = corner
    observed = {}
    for record in observations["records"]:
        require(isinstance(record, dict) and set(record) == {"key", "normal"}, "Unexpected observation record")
        key = record["key"]
        require(isinstance(key, list) and len(key) == 5 and all(type(v) is int and v >= 0 for v in key),
                "Observation key must contain five non-bool nonnegative integers")
        key = tuple(key)
        require(key in expected, "Unknown or ambiguous observation corner")
        require(key not in observed, "Duplicate observation corner")
        observed[key] = record["normal"]
    rows, counts = [], {"expected": len(expected), "observed": 0, "missing": 0, "invalid": 0}
    maximum_component, maximum_angle = None, None
    for key, corner in expected.items():
        row = {"key": list(key)}
        if key not in observed:
            row["status"] = "missing"
            counts["missing"] += 1
        else:
            vector, reason = _observation_vector(observed[key])
            if reason:
                row.update({"status": "invalid", "reason": reason})
                counts["invalid"] += 1
            else:
                source = struct.unpack("<3f", bytes.fromhex(corner["normal_f32le"]))
                component_delta = [value - original for value, original in zip(vector, source)]
                component = max(abs(value) for value in component_delta)
                a, b = _unit(source), _unit(vector)
                cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
                angle = math.degrees(math.atan2(math.hypot(*cross), sum(x * y for x, y in zip(a, b))))
                require(math.isfinite(component) and math.isfinite(angle), "Nonfinite measurement cannot be a successful observation")
                row.update({"status": "observed", "sourceNormal": list(source), "observedNormal": list(vector),
                            "componentDelta": component_delta, "maximumComponentDifference": component,
                            "angularDifferenceDegrees": angle})
                maximum_component = component if maximum_component is None else max(maximum_component, component)
                maximum_angle = angle if maximum_angle is None else max(maximum_angle, angle)
                counts["observed"] += 1
        rows.append(row)
    try:
        observations_digest, canonicalizable = digest(canonical_bytes(observations)), True
    except ProfileError:
        observations_digest, canonicalizable = None, False
    return {"schema_version": REPORT_SCHEMA, "profile": PROFILE, "sourcePayloadSha256": validation["payloadSha256"],
            "sourceFrame": FRAME, "observationKind": "synthetic-cpu", "producer": observations["producer"],
            "observationsSha256": observations_digest, "observationsCanonicalJson": canonicalizable,
            "sourceAuthority": "EXACT_SOURCE_PAYLOAD", "nativeFidelityEstablished": False,
            "receivingEvidence": False, "acceptanceTolerance": None, "shadingAcceptance": "NOT_EVALUATED",
            "summary": {**counts, "maximumComponentDifference": maximum_component, "maximumAngularDifferenceDegrees": maximum_angle},
            "corners": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("build", "validate", "report"))
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--semantic", type=Path, required=True)
    parser.add_argument("--payload", type=Path)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = (args.glb.read_bytes(), args.bundle.read_bytes(), args.semantic.read_bytes())
    if args.operation == "build":
        result = build_payload(*sources)
    else:
        require(args.payload is not None, "--payload is required")
        payload = load_json(args.payload.read_bytes())
        if args.operation == "validate":
            result = validate_payload(payload, *sources)
        else:
            require(args.observations is not None, "--observations is required")
            result = build_loss_report(payload, load_json(args.observations.read_bytes()), *sources)
    output = canonical_bytes(result) + b"\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(output)


if __name__ == "__main__":
    main()
