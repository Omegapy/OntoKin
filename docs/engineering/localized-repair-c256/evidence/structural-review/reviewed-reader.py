#!/usr/bin/env python3
"""Finite C210 GLB measurements; no semantic oracle, rebuild or trial runner."""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys

SCHEMA = "ontokin.c256.glb-measurement/0.1"
TIMES = (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
ROTATION_RESIDUAL = 1e-6
MAX_BYTES = 4 * 1024 * 1024
PROOF = "docs/engineering/semantic-export-c210/evidence/proof"
LIBRARY_HASH = "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"
ENDPOINTS = {
    "before": {
        "glb": "d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534",
        "source": "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123",
        "program": "sha256:8f9d976568e2a9fa39573e3fb90f616529097241a098b21d4eb22eabe4b7032f",
    },
    "after": {
        "glb": "05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8",
        "source": "443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a",
        "program": "sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082",
    },
}
LIMITS = [
    "Geometry and seven sampled rigid transforms only; no complete C255 observation",
    "Ownership, follows, hinges, actions, physical values and semantic parameters unqualified",
    "No accepted revision, rebuild, invalid-edit atomicity, native execution or trial evidence",
    "One public C210 family; no all-time motion or comparative advantage claim",
    "Finite profile validation, not a general glTF validator or normal/material fidelity check",
]


class Fault(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


def require(condition, code, detail):
    if not condition:
        raise Fault(code, detail)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, where, minimum=0, maximum=None):
    require(type(value) is int and value >= minimum, "INTEGER", where)
    require(maximum is None or value <= maximum, "LIMIT", where)
    return value


def number(value, where):
    require(type(value) in (int, float), "NUMBER", where)
    require(math.isfinite(value), "NONFINITE", where)
    return value


def vector(value, size, where):
    require(type(value) is list and len(value) == size, "VECTOR", where)
    return [number(x, where) for x in value]


def text(value, where):
    require(type(value) is str and 0 < len(value) <= 1024
            and all(ord(c) >= 32 for c in value), "TEXT", where)
    return value


def identity(value, where):
    require(type(value) is list and 1 <= len(value) <= 16, "IDENTITY", where)
    return [text(x, where) for x in value]


def table(value, where, maximum=256):
    require(type(value) is list and 0 < len(value) <= maximum, "TABLE", where)
    require(all(type(x) is dict for x in value), "TABLE", where)
    return value


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON_DUPLICATE", key)
        result[key] = value
    return result


def json_bytes(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(Fault("NONFINITE", x)))


def no_extensions(value):
    if type(value) is dict:
        require(not value.get("extensions"), "UNSUPPORTED", "extensions")
        for child in value.values():
            no_extensions(child)
    elif type(value) is list:
        for child in value:
            no_extensions(child)


def unit_quaternion(raw, where):
    q = vector(raw, 4, where)
    norm = math.sqrt(sum(x * x for x in q))
    require(norm > 0 and abs(norm - 1) <= ROTATION_RESIDUAL, "ROTATION_NORM", where)
    return [x / norm for x in q], norm


def interpolate_rotation(left, right, alpha):
    a, _ = unit_quaternion(left, "rotation left")
    b, _ = unit_quaternion(right, "rotation right")
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b = [-x for x in b]
        dot = -dot
    dot = min(1.0, max(0.0, dot))
    if 1.0 - dot <= 1e-12:
        q = [(1 - alpha) * x + alpha * y for x, y in zip(a, b)]
    else:
        angle = math.acos(dot)
        denominator = math.sin(angle)
        l = math.sin((1 - alpha) * angle) / denominator
        r = math.sin(alpha * angle) / denominator
        q = [l * x + r * y for x, y in zip(a, b)]
    norm = math.sqrt(sum(x * x for x in q))
    return [x / norm for x in q]


def matrix_from_trs(position, xyzw):
    x, y, z, w = xyzw
    return [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w), position[0],
            2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w), position[1],
            2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y), position[2],
            0, 0, 0, 1]


class _GLB:
    def __init__(self, raw):
        require(type(raw) is bytes and 28 <= len(raw) <= MAX_BYTES, "GLB_SIZE", "raw bytes")
        magic, version, length = struct.unpack_from("<III", raw)
        require(magic == 0x46546C67 and version == 2 and length == len(raw),
                "GLB_HEADER", "magic, version and total byte length")
        chunks, offset = [], 12
        while offset < len(raw):
            require(offset + 8 <= len(raw), "GLB_CHUNK", "truncated header")
            size, kind = struct.unpack_from("<II", raw, offset)
            require(size % 4 == 0 and offset + 8 + size <= len(raw),
                    "GLB_CHUNK", "alignment and range")
            chunks.append((kind, offset + 8, size))
            offset += 8 + size
        require(len(chunks) == 2 and [x[0] for x in chunks] == [0x4E4F534A, 0x004E4942],
                "GLB_CHUNKS", "exact JSON then BIN profile")
        _, start, count = chunks[0]
        require(count <= 2 * 1024 * 1024, "LIMIT", "JSON chunk")
        self.document = json_bytes(raw[start:start + count])
        require(type(self.document) is dict, "JSON_ROOT", "object required")
        self.raw = raw
        self.binary_offset, self.binary_size = chunks[1][1:]
        self.json_offset, self.json_size = start, count
        self.sha256 = digest(raw)
        self._accessors = {}
        self._profile()

    def _profile(self):
        d = self.document
        require(d.get("asset", {}).get("version") == "2.0", "GLTF_VERSION", "2.0 required")
        require(not d.get("extensionsUsed") and not d.get("extensionsRequired"),
                "UNSUPPORTED", "extensions")
        no_extensions(d)
        require(not any(d.get(k) for k in ("skins", "cameras", "images", "textures")),
                "UNSUPPORTED", "skins, cameras, images or textures")
        buffers = table(d["buffers"], "buffers", 1)
        require(set(buffers[0]) == {"byteLength"}, "BUFFER", "one embedded buffer")
        self.buffer_size = integer(buffers[0]["byteLength"], "buffer byteLength", 1, MAX_BYTES)
        require(0 <= self.binary_size - self.buffer_size <= 3, "BUFFER", "BIN length and padding")
        self.views = table(d["bufferViews"], "bufferViews", 256)
        self.accessors = table(d["accessors"], "accessors", 256)
        self.nodes = table(d["nodes"], "nodes", 18)
        require(len(self.nodes) == 18, "PROFILE", "eighteen object nodes")
        scenes = table(d["scenes"], "scenes", 1)
        require(integer(d.get("scene", 0), "scene") == 0, "SCENE", "single scene")
        roots = scenes[0]["nodes"]
        require(type(roots) is list and all(type(x) is int for x in roots)
                and sorted(roots) == list(range(18)), "SCENE_ROOTS", "every node exactly once")
        self.meshes = table(d["meshes"], "meshes", 18)
        self.animation = table(d["animations"], "animations", 1)[0]
        self.meta = d["extras"]["ontokin"]
        require(self.meta.get("target_contract") == "ontokin.glb/0.2"
                and self.meta.get("transform_policy") == "all_nodes_are_roots_with_baked_world_poses",
                "PROFILE", "bound baked-world profile labels")
        require(self.meta.get("coordinates") == {"handedness": "right", "up": "+Y",
                "length_unit": "m", "time_unit": "s"}, "COORDINATES", "metre/Y-up profile")
        self.program = text(self.meta["program"]["revision"], "program revision")
        require(re.fullmatch(r"sha256:[0-9a-f]{64}", self.program), "PROGRAM", "SHA-256 identity")
        for i, view in enumerate(self.views):
            require(integer(view.get("buffer"), f"bufferViews[{i}].buffer") == 0,
                    "BUFFER", "embedded buffer index")
            start = integer(view.get("byteOffset", 0), f"bufferViews[{i}].byteOffset")
            size = integer(view.get("byteLength"), f"bufferViews[{i}].byteLength", 1)
            require(start + size <= self.buffer_size, "BUFFER_VIEW_RANGE", str(i))
            if "byteStride" in view:
                stride = integer(view["byteStride"], "byteStride", 4, 252)
                require(stride % 4 == 0, "ACCESSOR_STRIDE", str(i))
        self._tracks()

    def accessor(self, index, components, shape, role):
        index = integer(index, "accessor index", 0, len(self.accessors)-1)
        key = (index, tuple(components), shape, role)
        if key in self._accessors:
            return self._accessors[key]
        a = self.accessors[index]
        require("sparse" not in a and a.get("normalized", False) is False,
                "UNSUPPORTED", "sparse or normalized accessor")
        require(type(a.get("componentType")) is int and a["componentType"] in components
                and a.get("type") == shape, "ACCESSOR_TYPE", f"accessors[{index}] {role}")
        view_index = integer(a.get("bufferView"), "bufferView", 0, len(self.views)-1)
        v = self.views[view_index]
        local_offset = integer(a.get("byteOffset", 0), "accessor byteOffset")
        widths = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}
        formats = {5126: ("f", 4), 5123: ("H", 2), 5125: ("I", 4)}
        code, component_size = formats[a["componentType"]]
        width = widths[shape]
        size = width * component_size
        count = integer(a.get("count"), "accessor count", 1, 100000)
        stride = v.get("byteStride", size)
        require(role == "vertex" or "byteStride" not in v,
                "ACCESSOR_STRIDE", "only vertex attributes may have stride")
        require(type(stride) is int and stride >= size and stride % component_size == 0,
                "ACCESSOR_STRIDE", str(index))
        buffer_offset = v.get("byteOffset", 0) + local_offset
        require(local_offset % component_size == 0 and buffer_offset % component_size == 0,
                "ACCESSOR_ALIGNMENT", str(index))
        require(role != "vertex" or buffer_offset % 4 == 0,
                "ACCESSOR_ALIGNMENT", "vertex data requires four-byte alignment")
        require(local_offset + (count-1) * stride + size <= v["byteLength"],
                "ACCESSOR_RANGE", str(index))
        fmt = "<" + code * width
        absolute = self.binary_offset + buffer_offset
        values, raw_elements = [], []
        for row in range(count):
            offset = absolute + row * stride
            item = list(struct.unpack_from(fmt, self.raw, offset))
            if code == "f":
                require(all(math.isfinite(x) for x in item), "NONFINITE", f"accessor {index} row {row}")
            values.append(item)
            raw_elements.append(self.raw[offset:offset+size])
        origin = {"accessor": index, "bufferView": view_index, "buffer": 0,
                  "componentType": a["componentType"], "type": shape, "count": count,
                  "bufferByteOffset": buffer_offset, "glbByteOffset": absolute,
                  "elementBytes": size, "byteStride": stride,
                  "elementBytesSha256": digest(b"".join(raw_elements))}
        self._accessors[key] = values, origin
        return values, origin

    def _tracks(self):
        channels = table(self.animation["channels"], "channels", 36)
        samplers = table(self.animation["samplers"], "samplers", 36)
        require(len(channels) == 36, "CHANNEL_COUNT", "translation and rotation for eighteen nodes")
        self.tracks = {}
        for channel_index, channel in enumerate(channels):
            target = channel["target"]
            require(type(target) is dict and set(target) == {"node", "path"}, "CHANNEL_TARGET", str(channel_index))
            node = integer(target["node"], "target node", 0, 17)
            path = target["path"]
            require(path in ("translation", "rotation"), "UNSUPPORTED", "animation target")
            require((node, path) not in self.tracks, "DUPLICATE_CHANNEL", f"node {node} {path}")
            sampler_index = integer(channel["sampler"], "sampler", 0, len(samplers)-1)
            sampler = samplers[sampler_index]
            require(sampler.get("interpolation", "LINEAR") == "LINEAR", "UNSUPPORTED", "interpolation")
            times, time_origin = self.accessor(sampler["input"], (5126,), "SCALAR", "time")
            values, value_origin = self.accessor(sampler["output"], (5126,), "VEC3" if path == "translation" else "VEC4", "animation")
            times = [x[0] for x in times]
            require(len(times) == len(values) and 2 <= len(times) <= 4096,
                    "ANIMATION_COUNT", str(channel_index))
            require(times[0] >= 0 and all(a < b for a, b in zip(times, times[1:])),
                    "ANIMATION_TIME", "finite strictly increasing times")
            require(times[0] <= TIMES[0] and times[-1] >= TIMES[-1],
                    "ANIMATION_COVERAGE", "all seven requested times must be covered")
            if path == "rotation":
                for q in values:
                    unit_quaternion(q, f"channel {channel_index}")
            self.tracks[node, path] = {"times": times, "values": values,
                "channel": channel_index, "sampler": sampler_index,
                "input": time_origin, "output": value_origin}
        require(set(self.tracks) == {(i, p) for i in range(18) for p in ("translation", "rotation")},
                "CHANNEL_COVERAGE", "all node translations and rotations")

    def sample(self, node, path, seconds):
        track = self.tracks[node, path]
        times, values = track["times"], track["values"]
        right = bisect.bisect_left(times, seconds)
        if right < len(times) and times[right] == seconds:
            left = right
            alpha = 0.0
        else:
            require(0 < right < len(times), "ANIMATION_COVERAGE", str(seconds))
            left = right - 1
            alpha = (seconds-times[left]) / (times[right]-times[left])
        if path == "rotation":
            value = interpolate_rotation(values[left], values[right], alpha)
        else:
            value = [(1-alpha)*x + alpha*y for x, y in zip(values[left], values[right])]
        origin = {k: track[k] for k in ("channel", "sampler", "input", "output")}
        origin.update({"animation": 0, "interpolation": "LINEAR", "path": path,
                       "sampleIndices": [left, right], "storedTimes_s": [times[left], times[right]],
                       "alpha": alpha, "rawSamples": [values[left], values[right]]})
        if path == "rotation":
            origin["rawNorms"] = [unit_quaternion(values[i], "sample")[1] for i in (left, right)]
            origin["operation"] = "unit-residual admission, shortest-path SLERP, normalization"
        else:
            origin["operation"] = "component linear interpolation"
        return value, origin

    def measure(self, artifact_name):
        text(artifact_name, "artifact name")
        require("/" not in artifact_name and "\\" not in artifact_name,
                "ARTIFACT_NAME", "one file basename")
        result = {"schema": SCHEMA, "authority": "untrusted-artifact-labels",
                  "historicalArtifactBound": False, "sourceAssociationVerified": False,
                  "semanticQualified": False, "completeC255Observation": False,
                  "realTrialSuccess": None, "executionAllowed": False,
                  "artifact": {"name": artifact_name, "bytes": len(self.raw), "sha256": self.sha256},
                  "programRevision": self.program, "sampleTimes_s": list(TIMES),
                  "geometry": [], "poses": [], "identities": [],
                  "measurementOrigins": {"geometry": [], "poses": []}, "limits": LIMITS.copy()}
        identities, paths = set(), set()
        for node_index, node in enumerate(self.nodes):
            require(not any(k in node for k in ("children", "matrix", "skin", "weights", "camera")),
                    "UNSUPPORTED", "hierarchy, matrix, skin, morph or camera node")
            vector(node.get("translation", [0, 0, 0]), 3, "node translation")
            unit_quaternion(node.get("rotation", [0, 0, 0, 1]), "node rotation")
            require(vector(node.get("scale", [1, 1, 1]), 3, "node scale") == [1, 1, 1],
                    "RIGID_SCALE", str(node_index))
            metadata = node["extras"]["ontokin"]
            require(metadata.get("kind") == "object" and metadata.get("pose_frame") == "world",
                    "IDENTITY", "object/world metadata required")
            oid = identity(metadata["element_id"], "node identity")
            path = text(metadata["path"], "node path")
            definition = identity(metadata["source_mapping"]["definition_id"], "definition identity")
            require(tuple(oid) not in identities and path not in paths, "DUPLICATE_IDENTITY", path)
            require(node.get("name") == path and metadata["source_mapping"].get("path") == path
                    and metadata["source_mapping"].get("element_id") == oid,
                    "IDENTITY_JOIN", path)
            require(metadata.get("program_revision") == self.program, "PROGRAM_JOIN", path)
            identities.add(tuple(oid)); paths.add(path)
            result["identities"].append({"id": oid, "path": path, "definitionId": definition,
                "node": node_index, "location": f"/nodes/{node_index}/extras/ontokin"})
            mesh_index = integer(node["mesh"], "node mesh", 0, len(self.meshes)-1)
            mesh = self.meshes[mesh_index]
            require("weights" not in mesh, "UNSUPPORTED", "mesh weights")
            primitive = table(mesh["primitives"], "primitives", 1)[0]
            require(primitive.get("mode", 4) == 4 and type(primitive.get("mode", 4)) is int
                    and "targets" not in primitive, "UNSUPPORTED", "triangle primitive required")
            attributes = primitive["attributes"]
            require(type(attributes) is dict and set(attributes) == {"POSITION", "NORMAL"},
                    "UNSUPPORTED", "POSITION/NORMAL vertex profile")
            vertices, position_origin = self.accessor(attributes["POSITION"], (5126,), "VEC3", "vertex")
            normals, _ = self.accessor(attributes["NORMAL"], (5126,), "VEC3", "vertex")
            require(len(normals) == len(vertices), "ATTRIBUTE_COUNT", str(mesh_index))
            indices, index_origin = self.accessor(primitive["indices"], (5123, 5125), "SCALAR", "index")
            flat_indices = [x[0] for x in indices]
            restart = 2**(16 if index_origin["componentType"] == 5123 else 32)-1
            require(len(flat_indices) % 3 == 0 and all(x < len(vertices) and x != restart for x in flat_indices),
                    "TRIANGLE_INDEX", str(mesh_index))
            location = (f"/nodes/{node_index}/mesh -> /meshes/{mesh_index}/primitives/0; "
                        f"POSITION accessor {position_origin['accessor']} @ GLB byte {position_origin['glbByteOffset']}; "
                        f"indices accessor {index_origin['accessor']} @ GLB byte {index_origin['glbByteOffset']}")
            origin = {"artifact": artifact_name, "sha256": self.sha256,
                      "location": location, "programRevision": self.program}
            result["geometry"].append({"id": oid, "vertices_m": vertices,
                "triangles": [flat_indices[i:i+3] for i in range(0, len(flat_indices), 3)], "origin": origin})
            result["measurementOrigins"]["geometry"].append({"id": oid, "node": node_index,
                "mesh": mesh_index, "primitive": 0, "position": position_origin, "indices": index_origin,
                "operation": "decode local POSITION and triangle-index bytes; no metadata dimensions"})
            for seconds in TIMES:
                position, po = self.sample(node_index, "translation", seconds)
                rotation, ro = self.sample(node_index, "rotation", seconds)
                pose_origin = {"artifact": artifact_name, "sha256": self.sha256,
                    "programRevision": self.program,
                    "location": (f"/nodes/{node_index}; /animations/0/channels/{po['channel']},"
                                 f"{ro['channel']}; input accessors {po['input']['accessor']},{ro['input']['accessor']}; "
                                 f"output accessors {po['output']['accessor']},{ro['output']['accessor']}; "
                                 f"samples {po['sampleIndices']},{ro['sampleIndices']}; t={seconds}")}
                result["poses"].append({"id": oid, "time_s": seconds, "side": "after",
                    "position_m": position, "rotation_wxyz": [rotation[3], *rotation[:3]],
                    "scale": [1, 1, 1], "matrix": matrix_from_trs(position, rotation), "origin": pose_origin})
                result["measurementOrigins"]["poses"].append({"id": oid, "time_s": seconds,
                    "node": node_index, "translation": po, "rotation": ro,
                    "matrixOperation": "row-major T*R from sampled channels; root local equals world",
                    "scaleOrigin": f"/nodes/{node_index}/scale" if "scale" in node else "glTF default [1,1,1]"})
        return result


def _public(call):
    try:
        return call()
    except Fault:
        raise
    except (KeyError, IndexError, TypeError, AttributeError, UnicodeError, json.JSONDecodeError,
            struct.error, OverflowError, RecursionError) as exc:
        raise Fault("STRUCTURE", type(exc).__name__) from exc


def measure_glb(raw, artifact_name="artifact.glb"):
    """Read arbitrary bytes in this finite profile; metadata labels remain untrusted."""
    return _public(lambda: _GLB(raw).measure(artifact_name))


def _key(source, pattern):
    matches = list(re.finditer(pattern, source))
    require(len(matches) == 1, "SOURCE_KEY", pattern.decode())
    match = matches[0]
    return match.group(1).decode(), {"startByte": match.start(1), "endByteExclusive": match.end(1)}


def _block_span(source, prefix):
    start = source.find(prefix)
    require(start >= 0 and source.find(prefix, start+1) < 0, "SOURCE_SPAN", prefix.decode())
    opening = source.find(b"{", start)
    depth, quoted, escaped = 0, False, False
    for position in range(opening, len(source)):
        ch = source[position]
        if quoted:
            if escaped:
                escaped = False
            elif ch == 92:
                escaped = True
            elif ch == 34:
                quoted = False
        elif ch == 34:
            quoted = True
        elif ch == 123:
            depth += 1
        elif ch == 125:
            depth -= 1
            if depth == 0:
                return start, position+1
    raise Fault("SOURCE_SPAN", "unclosed block")


def _source_identities(sources):
    entry, library = sources["main.ok"], sources["hinges.ok"]
    mk, module_at = _key(entry, rb'module KeyedRack @ "([^"]+)";')
    sk, scene_at = _key(entry, rb'scene Demo @ "([^"]+)"')
    rk, rack_at = _key(entry, rb'public class Rack @ "([^"]+)"')
    fk, collection_at = _key(entry, rb'public parts fingers @ "([^"]+)"')
    lk, library_at = _key(library, rb'module Hinges @ "([^"]+)";')
    finger_key, finger_at = _key(library, rb'public class Finger @ "([^"]+)"')
    blade_key, blade_at = _key(library, rb'private part blade @ "([^"]+)"')
    blade_class, blade_class_at = _key(library, rb'private class Blade @ "([^"]+)"')
    definition_ids = {"rack": ["entry", mk, "definitions", rk],
        "finger": ["package", "example.hinges", lk, "definitions", finger_key],
        "blade": ["package", "example.hinges", lk, "definitions", blade_class]}
    first_start, first_end = _block_span(library, b"public fn three_mounts")
    second_start, second_end = _block_span(entry, b"mounts = keyed<Vec3<Length>>")
    mounts = {}
    for root, raw, start, end in (("first", library, first_start, first_end),
                                  ("second", entry, second_start, second_end)):
        keys = list(re.finditer(rb'"([^"]+)"\s*:\s*vec3\(', raw[start:end]))
        mounts[root] = [(m.group(1).decode(), start+m.start(1), start+m.end(1)) for m in keys]
        require(len(mounts[root]) == (3 if root == "first" else 5), "SOURCE_KEY", "mount inventory")
    result = {}
    def span(filename, prefix):
        start, end = _block_span(sources[filename], prefix)
        return {"source_id": "entry" if filename == "main.ok" else "package:example.hinges@1.0.0",
                "source_revision": "sha256:"+digest(sources[filename]), "filename": filename,
                "start_byte": start, "end_byte": end}
    definitions = {"rack": span("main.ok", b"public class Rack"),
        "finger": span("hinges.ok", b"public class Finger"),
        "blade": span("hinges.ok", b"private class Blade")}
    for root in ("first", "second"):
        root_key, root_at = _key(entry, rb'object '+root.encode()+rb' @ "([^"]+)"')
        root_id = [mk, sk, root_key]
        root_steps = [{"kind": "member", "value": root}]
        common = [{"file": "main.ok", **x} for x in (module_at, scene_at, root_at)]
        result[root] = {"id": root_id, "definitionId": definition_ids["rack"], "root": root,
            "owner": None, "steps": root_steps, "declaration": span("main.ok", b"object "+root.encode()),
            "definition": definitions["rack"], "declarationDefinitionId": None,
            "generatedAncestor": None, "keyOrigins": common}
        for key, begin, end in mounts[root]:
            path = root+'.fingers["'+key+'"]'
            oid = root_id+[fk, key]
            steps = root_steps+[{"kind": "member", "value": "fingers"}, {"kind": "key", "value": key}]
            key_origins = common+[{"file": "main.ok", **collection_at},
                {"file": "hinges.ok" if root == "first" else "main.ok",
                 "startByte": begin, "endByteExclusive": end}]
            result[path] = {"id": oid, "definitionId": definition_ids["finger"], "root": root,
                "owner": root, "steps": steps, "declaration": span("main.ok", b"public parts fingers"),
                "definition": definitions["finger"], "declarationDefinitionId": definition_ids["rack"]+[fk],
                "generatedAncestor": path, "keyOrigins": key_origins}
            result[path+".blade"] = {"id": oid+[blade_key], "definitionId": definition_ids["blade"],
                "root": root, "owner": path, "steps": steps+[{"kind": "member", "value": "blade"}],
                "declaration": span("hinges.ok", b"private part blade"), "definition": definitions["blade"],
                "declarationDefinitionId": definition_ids["finger"]+[blade_key],
                "generatedAncestor": path, "keyOrigins": key_origins+[{"file": "hinges.ok", **blade_at}]}
    return result


def _associate(raw, sources, artifact_name):
    require(type(sources) is dict and set(sources) == {"main.ok", "hinges.ok"}
            and all(type(x) is bytes for x in sources.values()), "SOURCE_CLOSURE", "exact source byte map")
    entry_hash = digest(sources["main.ok"])
    endpoint = next((name for name, pins in ENDPOINTS.items() if pins["source"] == entry_hash), None)
    require(endpoint is not None and digest(sources["hinges.ok"]) == LIBRARY_HASH,
            "SOURCE_BINDING", "two frozen entry variants and exact dependency only")
    parsed = _GLB(raw)
    result = parsed.measure(artifact_name)
    expected_program = ENDPOINTS[endpoint]["program"]
    require(parsed.program == expected_program, "PROGRAM_BINDING", "exact source closure identity")
    program = parsed.meta["program"]
    manifest = program["manifest"]
    require(manifest.get("schema_version") == "ontokin.bundle/0.1" and manifest.get("entry_source_id") == "entry",
            "SOURCE_MANIFEST", "bundle identity")
    expected_units = [
        {"source_id": "entry", "package_id": None, "version": None,
         "filename": "main.ok", "source_revision": "sha256:"+entry_hash},
        {"source_id": "package:example.hinges@1.0.0", "package_id": "example.hinges", "version": "1.0.0",
         "filename": "hinges.ok", "source_revision": "sha256:"+LIBRARY_HASH}]
    require(manifest.get("units") == expected_units, "SOURCE_MANIFEST", "complete exact closure")
    require(parsed.meta["source"].get("entry_revision") == "sha256:"+entry_hash
            and parsed.meta["source"].get("entry_source_id") == "entry", "SOURCE_MANIFEST", "entry source")
    require(set(program["sources"]) == {x["source_id"] for x in expected_units}, "SOURCE_MANIFEST", "source inventory")
    for unit in expected_units:
        actual = program["sources"][unit["source_id"]]
        require(all(actual.get(k) == v for k, v in unit.items()), "SOURCE_MANIFEST", unit["filename"])
    expected = _source_identities(sources)
    require(set(program["occurrences"]) == set(expected), "IDENTITY_COVERAGE", "all source occurrences")
    require({row["path"] for row in result["identities"]} == set(expected), "IDENTITY_COVERAGE", "all node paths")
    joins = []
    for row in result["identities"]:
        path = row["path"]
        record = expected[path]
        metadata = parsed.nodes[row["node"]]["extras"]["ontokin"]
        mapping = metadata["source_mapping"]
        require(row["id"] == record["id"] and row["definitionId"] == record["definitionId"],
                "IDENTITY_BINDING", path)
        require(program["occurrences"][path] == mapping, "IDENTITY_JOIN", "occurrence/node source mapping")
        fields = {"owner_path": record["owner"], "root_path": record["root"], "path_steps": record["steps"],
                  "declaration": record["declaration"], "definition": record["definition"],
                  "declaration_definition_id": record["declarationDefinitionId"],
                  "generated_ancestor": record["generatedAncestor"], "class_id": "/".join(record["definitionId"])}
        require(all(mapping.get(k) == v for k, v in fields.items()), "SOURCE_MAPPING", path)
        require(metadata.get("class_name") == fields["class_id"], "DEFINITION_BINDING", path)
        if len(record["id"]) == 5:
            generated = mapping.get("generated")
            require(type(generated) is dict and generated.get("key") == record["id"][-1]
                    and generated.get("collection_id") == record["id"][:-1]
                    and generated.get("collection_path") == record["root"]+".fingers",
                    "GENERATED_IDENTITY", path)
        else:
            require(mapping.get("generated") is None, "GENERATED_IDENTITY", path)
        joins.append({"id": row["id"], "path": path, "definitionId": row["definitionId"],
            "node": row["node"], "sourceKeyOrigins": record["keyOrigins"],
            "declaration": record["declaration"], "definition": record["definition"],
            "artifactIdentityLocation": row["location"],
            "qualification": "fixed-source occurrence/definition association only"})
    result.update({"authority": "frozen-source-association", "sourceAssociationVerified": True,
                   "sourceEndpoint": endpoint, "sourceHashes": {k: digest(v) for k, v in sources.items()},
                   "identityJoins": joins})
    return result


def associate_glb(raw, source_files, artifact_name="artifact.glb"):
    """Join measurements to the two frozen source variants; no historical GLB admission."""
    return _public(lambda: _associate(raw, source_files, artifact_name))


def read_bound_endpoint(repo, endpoint):
    """Read only the exact original C210 endpoint and its exact source closure."""
    def run():
        require(endpoint in ENDPOINTS, "ENDPOINT", "before or after")
        root = Path(repo).resolve()
        def read(name, sha):
            path = root / PROOF / name
            require(path.is_file() and not path.is_symlink()
                    and path.resolve().is_relative_to(root), "INPUT_PATH", name)
            raw = path.read_bytes()
            require(digest(raw) == sha, "HISTORICAL_BINDING", name)
            return raw
        pins = ENDPOINTS[endpoint]
        raw = read(endpoint+".glb", pins["glb"])
        sources = {"main.ok": read(endpoint+".main.ok", pins["source"]),
                   "hinges.ok": read("hinges.ok", LIBRARY_HASH)}
        result = _associate(raw, sources, endpoint+".glb")
        result.update({"authority": "exact-historical-C210-endpoint", "historicalArtifactBound": True,
                       "endpoint": endpoint, "sourcePaths": {"main.ok": PROOF+"/"+endpoint+".main.ok",
                       "hinges.ok": PROOF+"/hinges.ok"}, "artifactPath": PROOF+"/"+endpoint+".glb"})
        return result
    return _public(run)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--endpoint", choices=tuple(ENDPOINTS), required=True)
    args = parser.parse_args()
    try:
        result = read_bound_endpoint(args.repo, args.endpoint)
    except (Fault, OSError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "REFUSED", "code": getattr(exc, "code", "IO"),
                          "detail": str(exc), "realTrialSuccess": None, "executionAllowed": False}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
