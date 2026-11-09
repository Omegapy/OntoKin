"""Structural preflight for the experimental, read-only splat environment.

The input profile uses one embedded buffer and uncompressed, unindexed POINTS
primitives in one static scene. Splat attribute formats follow Khronos'
KHR_gaussian_splatting ellipse kernel. This checks metadata and byte ranges;
it does not decode sample values, certify visual fidelity, or measure geometry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct

from .json_limits import MAX_JSON_BYTES, measure_json

EXTENSION = "KHR_gaussian_splatting"
MAX_BYTES = 64 * 1024 * 1024
MAX_SPLATS = 1_000_000
_SUPPORTED = {EXTENSION, "KHR_materials_unlit"}
_WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
_COMPONENT_BYTES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5126: 4}
_FLOAT = {(5126, False)}
_UNORM = {(5121, True), (5123, True)}
_FORMATS = {
    "POSITION": ("VEC3", _FLOAT),
    EXTENSION + ":ROTATION": ("VEC4", _FLOAT | {(5120, True), (5122, True)}),
    EXTENSION + ":SCALE": ("VEC3", _FLOAT | _UNORM | {(5121, False), (5123, False)}),
    EXTENSION + ":OPACITY": ("SCALAR", _FLOAT | _UNORM),
}
_SH = [
    {f"{EXTENSION}:SH_DEGREE_{degree}_COEF_{i}" for i in range(2 * degree + 1)}
    for degree in range(4)
]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _object(value, label):
    _require(isinstance(value, dict), f"Expected object for {label}")
    return value


def _array(value, label):
    _require(isinstance(value, list), f"Expected array for {label}")
    return value


def _integer(value, label, minimum=0):
    _require(type(value) is int and value >= minimum, f"Invalid {label}")
    return value


def _reference(value, items, label):
    i = _integer(value, label)
    _require(i < len(items), f"Out-of-range {label}")
    return i


def _offline_object(pairs):
    result = dict(pairs)
    _require(len(result) == len(pairs), "Duplicate key in GLB JSON")
    _require("uri" not in result, "Offline profile forbids URI resources")
    if "extensions" in result:
        _require(_object(result["extensions"], "extensions").keys() <= _SUPPORTED,
                 "Unsupported glTF extension")
    return result


def _container(data):
    _require(len(data) >= 28, "Truncated GLB")
    magic, version, total, size, tag = struct.unpack_from("<4sIII4s", data)
    _require((magic, version, total) == (b"glTF", 2, len(data)), "Invalid GLB header")
    end = 20 + size
    _require(tag == b"JSON" and 0 < size <= MAX_JSON_BYTES and size % 4 == 0
             and end + 8 <= total, "Invalid GLB JSON chunk bounds")
    bin_size, bin_tag = struct.unpack_from("<I4s", data, end)
    _require(bin_tag == b"BIN\0" and bin_size % 4 == 0 and end + 8 + bin_size == total,
             "Invalid GLB BIN chunk bounds")
    try:
        doc = json.loads(data[20:end].decode("utf-8"), object_pairs_hook=_offline_object)
    except RecursionError as exc:
        raise ValueError("GLB JSON nesting exceeds limit") from exc
    measure_json(doc)
    doc = _object(doc, "GLB JSON")
    asset = _object(doc.get("asset"), "asset")
    _require(asset.get("version") == "2.0" and asset.get("minVersion", "2.0") == "2.0",
             "Expected glTF 2.0 asset")
    buffers = _array(doc.get("buffers"), "buffers")
    _require(len(buffers) == 1, "Expected one embedded buffer")
    declared = _integer(_object(buffers[0], "buffer").get("byteLength"), "buffer length", 1)
    padding = bin_size - declared
    _require(0 <= padding <= 3 and (not padding or data[-padding:] == bytes(padding)),
             "Invalid embedded buffer length or padding")
    return doc, declared


def _storage(doc, buffer_size, byte_budget):
    views = _array(doc.get("bufferViews"), "bufferViews")
    view_bytes = 0
    for view in views:
        _object(view, "bufferView")
        _require(_integer(view.get("buffer"), "buffer index") == 0, "Unknown buffer")
        offset = _integer(view.get("byteOffset", 0), "bufferView byteOffset")
        length = _integer(view.get("byteLength"), "bufferView byteLength", 1)
        _require(offset + length <= buffer_size, "bufferView exceeds embedded buffer")
        # GLTFLoader slices a new backing buffer for each declared view.
        view_bytes += length
        _require(view_bytes <= byte_budget, "Aggregate bufferView bytes exceed budget")
        if "byteStride" in view:
            stride = _integer(view["byteStride"], "byteStride", 4)
            _require(stride <= 252 and stride % 4 == 0, "Invalid vertex stride")

    accessors = _array(doc.get("accessors"), "accessors")
    accessor_bytes = 0
    for acc in accessors:
        _object(acc, "accessor")
        _require("sparse" not in acc, "Sparse accessors are outside the first profile")
        view = views[_reference(acc.get("bufferView"), views, "accessor bufferView")]
        part = _integer(acc.get("componentType"), "componentType")
        shape = acc.get("type")
        _require(part in _COMPONENT_BYTES and isinstance(shape, str) and shape in _WIDTH,
                 "Unsupported accessor type or componentType")
        norm = acc.get("normalized", False)
        _require(type(norm) is bool and not (norm and part == 5126), "Invalid normalized flag")
        count = _integer(acc.get("count"), "accessor count", 1)
        offset = _integer(acc.get("byteOffset", 0), "accessor byteOffset")
        element = _WIDTH[shape] * _COMPONENT_BYTES[part]
        accessor_bytes += count * element
        _require(accessor_bytes <= byte_budget, "Aggregate accessor bytes exceed budget")
        stride = view.get("byteStride", element)
        start = view.get("byteOffset", 0) + offset
        _require(offset % 4 == 0 and start % _COMPONENT_BYTES[part] == 0
                 and stride >= element and (count == 1 or stride % 4 == 0),
                 "Invalid vertex alignment or stride")
        _require(offset + stride * (count - 1) + element <= view["byteLength"],
                 "Accessor exceeds its bufferView")
    return accessors


def _primitive(prim, accessors):
    _object(prim, "primitive")
    _require(type(prim.get("mode")) is int and prim["mode"] == 0, "Expected POINTS mode")
    _require("indices" not in prim and "targets" not in prim,
             "Indexed or morphed primitives are outside the first profile")
    cfg = _object(_object(prim.get("extensions"), "primitive extensions").get(EXTENSION),
                  "splat extension")
    _require(cfg.get("kernel") == "ellipse" and cfg.get("colorSpace") in
             ("srgb_rec709_display", "lin_rec709_display"), "Unsupported splat kernel/colorSpace")
    _require(cfg.get("projection", "perspective") == "perspective"
             and cfg.get("sortingMethod", "cameraDistance") == "cameraDistance",
             "Unsupported projection or sortingMethod")
    attrs = _object(prim.get("attributes"), "attributes")
    formats = _FORMATS.copy()
    highest = max((i for i, coeffs in enumerate(_SH) if coeffs.intersection(attrs)), default=0)
    for degree in range(highest + 1):
        formats.update({name: ("VEC3", _FLOAT) for name in _SH[degree]})
    _require(formats.keys() <= attrs.keys(), "Missing required attribute or incomplete SH degree")
    counts = set()
    attribute_bytes = 0
    for name, index in attrs.items():
        acc = accessors[_reference(index, accessors, f"{name} accessor")]
        counts.add(acc["count"])
        attribute_bytes += acc["count"] * _WIDTH[acc["type"]] * _COMPONENT_BYTES[acc["componentType"]]
        if name == "POSITION":
            bounds = (acc.get("min"), acc.get("max"))
            _require(all(isinstance(row, list) and len(row) == 3
                         and all(type(v) in (int, float) for v in row) for row in bounds)
                     and all(lo <= hi for lo, hi in zip(*bounds)), "Invalid POSITION bounds")
        if name in formats:
            shape, allowed = formats[name]
            _require(acc["type"] == shape and
                     (acc["componentType"], acc.get("normalized", False)) in allowed,
                     f"Invalid {name} accessor format")
        else:
            _require(not name.startswith(EXTENSION + ":"), "Unknown splat attribute")
    _require(len(counts) == 1, "Attribute counts disagree")
    return counts.pop(), attribute_bytes


def _scene_count(doc, mesh_counts):
    scenes = _array(doc.get("scenes"), "scenes")
    _require(len(scenes) == 1 and _integer(doc.get("scene", 0), "scene") == 0,
             "Expected a single scene")
    nodes = _array(doc.get("nodes"), "nodes")
    roots = _array(_object(scenes[0], "scene").get("nodes"), "scene nodes")
    stack = list(roots)
    seen = set()
    count = 0
    while stack:
        i = _reference(stack.pop(), nodes, "node index")
        _require(i not in seen, "Cyclic or multiply referenced scene node")
        seen.add(i)
        node = _object(nodes[i], "node")
        if "mesh" in node:
            count += mesh_counts[_reference(node["mesh"], mesh_counts, "mesh index")]
        stack.extend(_array(node.get("children", []), "children"))
    _require(count > 0, "Scene contains no splats")
    return count


def preflight_splat_glb(path: str | Path, expected_sha256: str, *,
                        max_bytes: int = MAX_BYTES, max_splats: int = MAX_SPLATS) -> dict:
    """Read and hash one local GLB. Return structural counts or raise ValueError."""
    _require(isinstance(expected_sha256, str) and
             re.fullmatch(r"[A-Fa-f0-9]{64}", expected_sha256), "Invalid expected SHA-256")
    _integer(max_bytes, "byte budget", 1)
    _integer(max_splats, "splat budget", 1)
    with Path(path).open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        _require(size <= max_bytes, "GLB exceeds byte budget")
        data = stream.read(size + 1)
    _require(len(data) == size, "GLB size changed during read")
    digest = hashlib.sha256(data).hexdigest()
    _require(digest == expected_sha256.lower(), "GLB SHA-256 mismatch")
    doc, buffer_size = _container(data)
    used = _array(doc.get("extensionsUsed"), "extensionsUsed")
    required = _array(doc.get("extensionsRequired", []), "extensionsRequired")
    _require(all(isinstance(s, str) for s in used + required), "Invalid extension list")
    _require(len(used) == len(set(used)) and len(required) == len(set(required)),
             "Duplicate extension declaration")
    _require(EXTENSION in used and set(required) <= set(used) <= _SUPPORTED,
             "Unsupported or undeclared extension")
    _require(not any(k in doc for k in ("images", "textures", "animations", "skins")),
             "Expected a static, texture-free splat environment")
    accessors = _storage(doc, buffer_size, max_bytes)
    mesh_counts = []
    primitives = 0
    attribute_bytes = 0
    for mesh in _array(doc.get("meshes"), "meshes"):
        parts = _array(_object(mesh, "mesh").get("primitives"), "primitives")
        _require(parts, "Mesh has no primitives")
        count = 0
        for primitive in parts:
            points, size_bytes = _primitive(primitive, accessors)
            count += points
            # Count every binding even when multiple primitives alias one accessor.
            attribute_bytes += size_bytes
            _require(attribute_bytes <= max_bytes, "Aggregate primitive attribute bytes exceed budget")
        mesh_counts.append(count)
        primitives += len(parts)
    stored = sum(mesh_counts)
    rendered = _scene_count(doc, mesh_counts)
    _require(max(stored, rendered) <= max_splats, "GLB exceeds splat budget")
    return {"sha256": digest, "bytes": size, "splat_count": stored,
            "scene_splat_count": rendered, "splat_primitives": primitives,
            "extensionsUsed": used, "extensionsRequired": required}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    try:
        result = preflight_splat_glb(args.glb, args.sha256)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Preflight failed: {error}\n")
    print(json.dumps(result, indent=2))
