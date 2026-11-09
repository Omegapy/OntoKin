"""Check a local visual-environment registration and its single-file OntoKin layer."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from .bundle import MAX_SOURCE_BYTES
from .diagnostics import OntoKinError
from .external_gltf import EXTENSION, preflight_splat_glb
from .gltf import _preflight_accessor_layout, _preflight_scene_layout
from .json_limits import MAX_JSON_BYTES, measure_json
from .scene import MAX_GLB_BYTES


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, *names):
    require(isinstance(value, dict) and value.keys() == set(names),
            "Expected exactly these fields: " + ", ".join(names))


def _read(path, limit):
    require(path.is_file(), f"Expected a regular file: {path.name}")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, f"File exceeds its byte budget: {path.name}")
    return data


def _unique(pairs):
    obj = dict(pairs)
    require(len(obj) == len(pairs), "Duplicate JSON key")
    return obj


def _json(data):
    def invalid_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_unique, parse_constant=invalid_constant)
    except RecursionError:
        raise ValueError("Excessive JSON nesting") from None


def _resolve_asset(root, asset):
    relative = asset["path"]
    # Use the same conservative path vocabulary in local files and browser URLs.
    require(isinstance(relative, str) and re.fullmatch(r"[A-Za-z0-9._/-]{1,256}", relative)
            and all(part and not part.startswith(".") for part in relative.split("/")), "Invalid relative asset path")
    path = (root / relative).resolve(strict=True)
    require(path.is_relative_to(root) and path.is_file(), "Asset resolves outside its manifest or is not a file")
    require(isinstance(asset["sha256"], str) and re.fullmatch("[a-f0-9]{64}", asset["sha256"]),
            "Expected lowercase SHA-256 hex")
    return path


def _vector(values, n):
    require(isinstance(values, list) and len(values) == n and
            all(type(x) in (int, float) and -1e6 <= x <= 1e6 for x in values),
            f"Expected {n} finite values within ±1000000")


def _cross(a, b):
    return (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])


def _span_plane(points):
    vectors = [tuple(x - y for x, y in zip(point, points[0])) for point in points[1:]]
    longest = max(vectors, key=lambda vector: math.hypot(*vector))
    # Reject a collinear or numerically near-collinear registration in either frame.
    return max(math.hypot(*_cross(longest, vector)) for vector in vectors) > 1e-9 * sum(x*x for x in longest)


def check_registration(reg):
    _keys(reg, "kind", "worldUnit", "matrix", "anchors", "toleranceM")
    require(reg["kind"] in ("rigid", "similarity") and reg["worldUnit"] == "metre", "Unknown registration kind or unit")
    matrix = reg["matrix"]
    _vector(matrix, 16)
    require(matrix[3::4] == [0, 0, 0, 1], "Expected affine column-major transform")
    columns = [matrix[i:i+3] for i in (0, 4, 8)]
    scale = math.hypot(*columns[0])
    require(1e-6 <= scale <= 1e6 and (reg["kind"] != "rigid" or math.isclose(scale, 1, rel_tol=1e-8)),
            "Invalid registration scale")
    normalized = [[v / scale for v in c] for c in columns]
    require(all(math.isclose(math.hypot(*c), 1, rel_tol=1e-8) for c in normalized)
            and abs(sum(a*b for a, b in zip(normalized[0], normalized[1]))) <= 1e-8
            and math.dist(_cross(*normalized[:2]), normalized[2]) <= 1e-8,
            "Expected a right-handed rotation and uniform scale")
    tolerance = reg["toleranceM"]
    require(type(tolerance) in (int, float) and 0 <= tolerance <= 1, "Invalid residual tolerance in metres")
    anchors = reg["anchors"]
    require(isinstance(anchors, list) and 3 <= len(anchors) <= 64, "Expected 3 to 64 anchors")
    residuals = {}
    for anchor in anchors:
        _keys(anchor, "name", "environment", "world")
        name = anchor["name"]
        require(isinstance(name, str) and 1 <= len(name.strip()) <= 128 and name not in residuals,
                "Expected unique nonempty anchor names")
        src, dst = anchor["environment"], anchor["world"]
        _vector(src, 3)
        _vector(dst, 3)
        predicted = [sum(matrix[4*j+i]*src[j] for j in range(3)) + matrix[12+i] for i in range(3)]
        residuals[name] = math.dist(predicted, dst)
    require(all(_span_plane([a[key] for a in anchors]) for key in ("environment", "world")),
            "Registration anchors must span a plane in both frames")
    worst = max(residuals.values())
    require(worst <= tolerance, f"Maximum registration residual {worst:.9g} m exceeds tolerance")
    return {"kind": reg["kind"], "scale": scale, "anchorResidualsM": residuals,
            "maxResidualM": worst, "rmsResidualM": math.hypot(*residuals.values()) / math.sqrt(len(anchors)),
            "toleranceM": tolerance}


def _authored_layout(doc):
    """Bound the native triangle/animation subset before any renderer allocation."""
    require(doc.keys() <= {"asset", "scene", "scenes", "nodes", "buffers", "bufferViews", "accessors",
                           "animations", "extras", "meshes", "materials"}, "Expected embedded native authored scene")
    nodes = doc["nodes"]
    require(0 < len(nodes) <= 4096 and len(doc["scenes"]) == 1 and doc.get("scene", 0) == 0
            and sorted(doc["scenes"][0]["nodes"]) == list(range(len(nodes)))
            and all(node.keys() <= {"name", "translation", "rotation", "extras", "mesh"} for node in nodes),
            "Authored nodes must be unique flat scene roots")
    views, accessors = doc["bufferViews"], doc["accessors"]
    require(len(doc["meshes"]) <= 512 and len(accessors) <= 8192
            and all("sparse" not in acc and type(acc["count"]) is int and 0 < acc["count"] <= 1_000_000
                    for acc in accessors), "Authored accessor budget or dense layout violated")
    # Three copies each referenced bufferView. Overlaps can multiply a small input.
    require(sum(view["byteLength"] for view in views) <= MAX_GLB_BYTES, "Authored bufferView copy budget exceeded")
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            require(primitive.keys() <= {"attributes", "indices", "material", "mode", "extras"}
                    and primitive.get("mode", 4) == 4 and primitive["attributes"].keys() == {"POSITION", "NORMAL"},
                    "Expected dense authored triangle primitives")
    stack = [doc]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            require("extensions" not in item, "Undeclared extension in authored GLB")
            stack.extend(v for k, v in item.items() if k != "extras")
        elif isinstance(item, list):
            stack.extend(item)
    # These are the same pre-allocation checks used by the native GLB/0.22 reader.
    _preflight_accessor_layout(doc, target_contract="ontokin.glb/0.22")
    _preflight_scene_layout(doc, target_contract="ontokin.glb/0.22")
    animation = doc["animations"][0]
    channels = animation["channels"]
    require(len(channels) == len(animation["samplers"]) == 2 * len(nodes)
            and {(c["target"]["node"], c["target"]["path"]) for c in channels}
            == {(i, path) for i in range(len(nodes)) for path in ("translation", "rotation")},
            "Expected unique authored translation and rotation tracks")


def _bind_authored(glb, source_sha):
    # The independent passage checker measures the mesh after structural admission.
    require(len(glb) >= 28, "Truncated authored GLB")
    magic, version, total, size, tag = struct.unpack_from("<4sIII4s", glb)
    end = 20 + size
    require((magic, version, total, tag) == (b"glTF", 2, len(glb), b"JSON") and 0 < size <= MAX_JSON_BYTES
            and size % 4 == 0 and end + 8 <= total, "Invalid authored GLB JSON bounds")
    binary_size, tag = struct.unpack_from("<I4s", glb, end)
    require(tag == b"BIN\0" and binary_size % 4 == 0 and end + 8 + binary_size == total,
            "Invalid authored GLB embedded buffer")
    doc = _json(glb[20:end])
    measure_json(doc)
    try:
        buffers = doc["buffers"]
        require(doc["asset"]["version"] == "2.0" and not doc.get("extensionsUsed") and
                not doc.get("extensionsRequired") and len(buffers) == 1 and "uri" not in buffers[0]
                and type(buffers[0]["byteLength"]) is int and 0 <= binary_size - buffers[0]["byteLength"] <= 3
                and all("bufferView" in image and "uri" not in image for image in doc.get("images", [])),
                "Expected embedded, extension-free authored GLB")
        _authored_layout(doc)
        meta = doc["extras"]["ontokin"]
        program = meta["program"]["manifest"]
        units = program["units"]
        revision = "sha256:" + source_sha
        require(meta["target_contract"] == "ontokin.glb/0.22" and meta["source"]["entry_revision"] == revision
                and len(units) == 1 and units[0]["source_id"] == program["entry_source_id"] == "entry"
                and units[0]["source_revision"] == revision and program["assets"] == [],
                "Expected single-entry OntoKin GLB/0.22 bound to the pinned source revision")
    except OntoKinError as exc:
        raise ValueError(f"Invalid native authored GLB layout: {exc}") from exc
    except (KeyError, IndexError, TypeError, AttributeError, OverflowError):
        raise ValueError("Malformed authored GLB metadata") from None


def check_manifest(path):
    path = Path(path).resolve(strict=True)
    manifest = _json(_read(path, 65536))
    _keys(manifest, "schema", "environment", "authored", "registration", "collisionProxy")
    require(manifest["schema"] == "ontokin-composite/1", "Unknown composite manifest version")
    require(manifest["collisionProxy"] is None, "Collision proxies are outside this visual-only profile")
    env = manifest["environment"]
    _keys(env, "name", "path", "sha256", "requiredExtension", "authority", "provenance")
    require(env["authority"] == "visual-only" and env["requiredExtension"] == EXTENSION,
            "Invalid environment authority or required extension")
    require(all(isinstance(env[k], str) and env[k].strip() for k in ("name", "provenance")),
            "Environment name and provenance are required")
    registration = check_registration(manifest["registration"])
    environment = preflight_splat_glb(_resolve_asset(path.parent, env), env["sha256"])
    authored = manifest["authored"]
    _keys(authored, "source", "glb")
    for key, limit in (("source", MAX_SOURCE_BYTES), ("glb", MAX_GLB_BYTES)):
        ref = authored[key]
        _keys(ref, "path", "sha256")
        data = _read(_resolve_asset(path.parent, ref), limit)
        require(hashlib.sha256(data).hexdigest() == ref["sha256"], f"Authored {key} SHA-256 mismatch")
        if key == "glb":
            _bind_authored(data, authored["source"]["sha256"])
    return {"schema": manifest["schema"], "environment": environment, "registration": registration,
            "authored": authored, "environmentAuthority": "visual-only", "collisionProxy": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    try:
        print(json.dumps(check_manifest(parser.parse_args().manifest), indent=2, allow_nan=False))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Invalid composite manifest: {exc}\n")
