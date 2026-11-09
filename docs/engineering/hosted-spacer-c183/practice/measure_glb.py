#!/usr/bin/env python3
"""Read the exported triangles of the public, centered glTF box fixture."""

import argparse
import collections
import json
import math
from pathlib import Path
import struct
import sys


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def at(items, index):
    require(type(index) is int and 0 <= index < len(items), "invalid glTF reference")
    return items[index]


def read_glb(path):
    data = path.read_bytes()
    require(struct.unpack_from("<4sII", data) == (b"glTF", 2, len(data)), "invalid GLB header")
    offset = 12
    chunks = []
    for expected in (b"JSON", b"BIN\x00"):
        size, kind = struct.unpack_from("<I4s", data, offset)
        offset += 8
        require(kind == expected and size % 4 == 0 and offset + size <= len(data), "invalid GLB chunk")
        chunks.append(data[offset:offset + size])
        offset += size
    require(offset == len(data), "unexpected trailing GLB chunks")
    doc = json.loads(chunks[0].decode("utf-8"))
    require(doc["asset"]["version"] == "2.0" and not doc.get("extensionsUsed")
            and not doc.get("extensionsRequired"), "expected unextended glTF 2.0")
    buffers = doc["buffers"]
    require(len(buffers) == 1 and "uri" not in buffers[0], "expected one embedded buffer")
    size = buffers[0]["byteLength"]
    require(type(size) is int and size > 0 and 0 <= len(chunks[1]) - size <= 3, "invalid buffer length")
    return doc, chunks[1][:size]


def values(doc, blob, index, shape, components):
    acc = at(doc["accessors"], index)
    scalar = acc["componentType"]
    require(acc["type"] == shape and scalar in components and not acc.get("normalized")
            and "sparse" not in acc, "unsupported accessor type")
    layout = struct.Struct("<" + {5121: "B", 5123: "H", 5125: "I", 5126: "f"}[scalar]
                           * {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[shape])
    view = at(doc["bufferViews"], acc["bufferView"])
    start, length = view.get("byteOffset", 0), view["byteLength"]
    offset, stride, count = acc.get("byteOffset", 0), view.get("byteStride", layout.size), acc["count"]
    require(view["buffer"] == 0 and all(type(x) is int for x in (start, length, offset, stride, count))
            and min(start, offset) >= 0 and stride >= layout.size and count > 0
            and offset + (count - 1) * stride + layout.size <= length
            and start + length <= len(blob), "accessor extends beyond its buffer view")
    return [layout.unpack_from(blob, start + offset + i * stride) for i in range(count)]


DEFAULT = {"translation": (0, 0, 0), "rotation": (0, 0, 0, 1), "scale": (1, 1, 1)}
IDENTITY = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def vector(value, size):
    require(len(value) == size and all(type(x) in (int, float) and math.isfinite(x) for x in value),
            "invalid transform")
    return tuple(value)


def node_matrix(node):
    if "matrix" in node:
        matrix = vector(node["matrix"], 16)
        require(not any(k in node for k in DEFAULT) and matrix[3::4] == (0, 0, 0, 1),
                "expected one affine matrix")
        return matrix
    tx, ty, tz = vector(node.get("translation", DEFAULT["translation"]), 3)
    sx, sy, sz = vector(node.get("scale", DEFAULT["scale"]), 3)
    x, y, z, w = vector(node.get("rotation", DEFAULT["rotation"]), 4)
    require(abs(math.hypot(x, y, z, w) - 1) <= 1e-6, "invalid rotation quaternion")
    # Column-major T * R * S, the order specified for glTF nodes.
    return ((1-2*(y*y+z*z))*sx, 2*(x*y+z*w)*sx, 2*(x*z-y*w)*sx, 0,
            2*(x*y-z*w)*sy, (1-2*(x*x+z*z))*sy, 2*(y*z+x*w)*sy, 0,
            2*(x*z+y*w)*sz, 2*(y*z-x*w)*sz, (1-2*(x*x+y*y))*sz, 0,
            tx, ty, tz, 1)


def multiply(left, right):
    return tuple(sum(left[4*k+r] * right[4*c+k] for k in range(4))
                 for c in range(4) for r in range(4))


def check_static_tracks(doc, blob, visited):
    # Some recorders write constant pose keys even for a stationary box.
    for animation in doc.get("animations", []):
        for channel in animation["channels"]:
            target = channel["target"]
            if target["node"] not in visited:
                continue
            node = at(doc["nodes"], target["node"])
            path = target["path"]
            sampler = at(animation["samplers"], channel["sampler"])
            require(path in DEFAULT and "matrix" not in node
                    and sampler.get("interpolation", "LINEAR") in ("STEP", "LINEAR"),
                    "unsupported animation on the practice object")
            expected = node.get(path, DEFAULT[path])
            shape = "VEC4" if path == "rotation" else "VEC3"
            keys = values(doc, blob, sampler["output"], shape, (5126,))
            times = [t for (t,) in values(doc, blob, sampler["input"], "SCALAR", (5126,))]
            require(len(times) == len(keys) and all(math.isfinite(t) and t >= 0 for t in times)
                    and all(a < b for a, b in zip(times, times[1:])), "invalid animation key times")
            for key in keys:
                signs = (1, -1) if path == "rotation" else (1,)
                require(any(all(abs(a - sign*b) <= 1e-7 for a, b in zip(key, expected))
                            for sign in signs), "practice box has a changing pose")


def check_box(points, low, high):
    # Map each world-space vertex to a corner. Each rectangular face must have
    # two distinct triangles whose shared edge is a diagonal of that face.
    faces = collections.defaultdict(list)
    epsilon = 1e-7  # metres
    require(all(b - a > 2 * epsilon for a, b in zip(low, high)), "degenerate box")
    for i in range(0, len(points), 3):
        corners = []
        for p in points[i:i+3]:
            corner = tuple(int(abs(x-b) < abs(x-a)) for x, a, b in zip(p, low, high))
            require(all(abs(x - (high[k] if corner[k] else low[k])) <= epsilon
                        for k, x in enumerate(p)), "mesh contains a non-corner vertex")
            corners.append(corner)
        flat = [(axis, corners[0][axis]) for axis in range(3)
                if len({p[axis] for p in corners}) == 1]
        require(len(set(corners)) == 3 and len(flat) == 1, "triangle is not on one box face")
        faces[flat[0]].append(set(corners))
    require(len(faces) == 6 and all(len(pair) == 2 for pair in faces.values()),
            "expected two triangles per box face")
    for a, b in faces.values():
        shared = a & b
        require(len(shared) == 2, "duplicate or disconnected face triangles")
        start, end = shared
        require(sum(x != y for x, y in zip(start, end)) == 2, "face triangles overlap")


def measure(path):
    doc, blob = read_glb(path)
    roots = at(doc["scenes"], doc["scene"])["nodes"]
    stack = [(index, IDENTITY) for index in roots]
    visited = set()
    points = []
    meshes = primitives = 0
    while stack:
        index, parent = stack.pop()
        node = at(doc["nodes"], index)
        require(index not in visited and "skin" not in node and "weights" not in node,
                "cyclic, shared, or deformed scene node")
        visited.add(index)
        world = multiply(parent, node_matrix(node))
        stack.extend((child, world) for child in node.get("children", []))
        if "mesh" not in node:
            continue
        meshes += 1
        require(meshes == 1, "expected exactly one active mesh instance")
        mesh = at(doc["meshes"], node["mesh"])
        for prim in mesh["primitives"]:
            primitives += 1
            require(prim.get("mode", 4) == 4 and not prim.get("targets")
                    and "indices" in prim and "weights" not in mesh, "expected indexed static triangles")
            positions = values(doc, blob, prim["attributes"]["POSITION"], "VEC3", (5126,))
            indices = values(doc, blob, prim["indices"], "SCALAR", (5121, 5123, 5125))
            require(len(indices) % 3 == 0, "incomplete triangle")
            for (vertex,) in indices:
                point = (*at(positions, vertex), 1)
                xyz = tuple(sum(world[4*c+r] * point[c] for c in range(4)) for r in range(3))
                require(all(map(math.isfinite, xyz)), "nonfinite world vertex")
                points.append(xyz)
    require(len(points) == 36, "expected a twelve-triangle box")
    check_static_tracks(doc, blob, visited)
    low = tuple(map(min, zip(*points)))
    high = tuple(map(max, zip(*points)))
    check_box(points, low, high)
    return {"mesh_count": meshes, "primitive_count": primitives, "triangle_count": len(points)//3,
            "dimensions_mm": [1000*(b-a) for a, b in zip(low, high)],
            "center_mm": [500*(b+a) for a, b in zip(low, high)],
            "world_min_mm": [1000*a for a in low], "world_max_mm": [1000*b for b in high]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expect-mm", nargs=3, type=float, required=True, metavar=("X", "Y", "Z"))
    args = parser.parse_args()
    if not all(math.isfinite(x) and x > 0 for x in args.expect_mm):
        parser.error("expected dimensions must be positive and finite")
    try:
        result = measure(args.file)
    except (OSError, ValueError, KeyError, TypeError, struct.error, OverflowError) as exc:
        print(json.dumps({"pass": False, "error": str(exc)}))
        return 1
    result["expected_mm"] = args.expect_mm
    result["tolerance_mm"] = 0.05
    result["pass"] = (all(abs(actual - expected) <= 0.05
                          for actual, expected in zip(result["dimensions_mm"], args.expect_mm))
                      and all(abs(x) <= 0.05 for x in result["center_mm"]))
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
