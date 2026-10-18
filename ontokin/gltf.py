"""Binary glTF 2.0 writing and independent decoded-animation verification.

The reader deliberately supports the bounded subset written by this adapter:
embedded geometry, flat root nodes, and one LINEAR translation/rotation clip.
It is a validation reader, not a general-purpose glTF importer.
"""

from __future__ import annotations

import bisect
import copy
import hashlib
import json
import math
import platform
import struct
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

from .diagnostics import OntoKinError
from .model import SceneModel
from .json_limits import JSONLimitError, measure_json
from .values import bounded_data
from .scene import (MAX_GLB_BYTES, MAX_VALIDATION_POSES, TARGET_CONTRACT,
                    CONSTRUCTION_TARGET, SURFACE_TARGET, IMPULSE_TARGET, NATIVE_TARGETS, PROGRAM_TARGETS, MAX_MESH_VERTICES,
                    SurfaceMesh, build_surface_mesh, geometry_metadata, surface_metadata,
                    checked_contract, program_metadata,
                    BakedScene, ExportOptions, build_scene, export_error,
                    float32, rotation_error, sampled_states, relationship_metadata,
                    _angular_speed_bound, _boundary_output_budget, impulse_profile_metadata)
from .evaluator import exact_time, preflight, time_text


@dataclass
class ExportResult:
    data: bytes
    report: dict[str, Any]
    scene: BakedScene


class _CallbackFailure(BaseException):
    """Keep caller cancellation outside malformed-input exception handlers."""

    def __init__(self, error: BaseException):
        self.error = error


def _guard_check(check):
    if check is None:
        return None

    def guarded():
        try:
            check()
        except _CallbackFailure:
            raise
        except BaseException as error:
            raise _CallbackFailure(error) from error
    return guarded


class _BufferBuilder:
    def __init__(self, check=None) -> None:
        self.binary = bytearray()
        self.views: list[dict[str, Any]] = []
        self.accessors: list[dict[str, Any]] = []
        self.max_geometry_quantization_error_m = 0.
        self.max_surface_quantization_error_m = 0.
        self.check = check

    def add(self, values: list | tuple, size: int, *, component: int = 5126,
            target: int | None = None, bounds: bool = False, geometry: bool = False,
            surface: bool = False) -> int:
        if self.check:
            self.check()
        format_ = {5126: "f", 5123: "H", 5125: "I"}[component]
        row_format = struct.Struct("<" + format_ * size)
        padding = -len(self.binary) % 4
        if len(self.binary) + padding + len(values) * row_format.size > MAX_GLB_BYTES:
            export_error("OKE-E-GLB-BUDGET", "The predicted binary buffer exceeds the GLB byte budget.", kind="resource")
        rows = [(v,) for v in values] if size == 1 else values
        quantized = []
        for number, row in enumerate(rows):
            if self.check and number % 256 == 0:
                self.check()
            quantized.append(tuple(float32(v, context="geometry" if geometry else "animation component")
                                   for v in row) if component == 5126 else tuple(row))
        if geometry:
            error = max((abs(a - b) for row, encoded in zip(rows, quantized)
                         for a, b in zip(row, encoded)), default=0.)
            self.max_geometry_quantization_error_m = max(self.max_geometry_quantization_error_m, error)
            if surface:
                self.max_surface_quantization_error_m = max(self.max_surface_quantization_error_m, error)
                if error > 1e-5:
                    export_error("OKE-E-GEOMETRY-PRECISION", "Surface local vertex quantization exceeds 0.00001 m.",
                                 details={"max_geometry_quantization_error_m": error,
                                          "surface_position_tolerance_m": 1e-5})
            if any(min(row[i] for row in quantized) == max(row[i] for row in quantized) for i in range(3)):
                export_error("OKE-E-GEOMETRY-PRECISION", "A visual solid collapses along an axis in binary32.")
        self.binary.extend(b"\0" * padding)
        start = len(self.binary)
        for number, row in enumerate(quantized):
            if self.check and number % 256 == 0:
                self.check()
            self.binary.extend(row_format.pack(*row))
        if len(self.binary) > MAX_GLB_BYTES:
            export_error("OKE-E-GLB-BUDGET", "The binary buffer exceeds the GLB byte budget.", kind="resource")
        view = {"buffer": 0, "byteOffset": start, "byteLength": len(self.binary) - start}
        if target is not None:
            view["target"] = target
        accessor = {"bufferView": len(self.views), "componentType": component,
                    "count": len(rows), "type": {1: "SCALAR", 2: "VEC2", 3: "VEC3", 4: "VEC4"}[size]}
        if bounds:
            accessor["min"] = [min(row[i] for row in quantized) for i in range(size)]
            accessor["max"] = [max(row[i] for row in quantized) for i in range(size)]
        self.views.append(view)
        self.accessors.append(accessor)
        return len(self.accessors) - 1


def _encode(scene: BakedScene, *, check=None) -> tuple[bytes, float]:
    builder = _BufferBuilder(check)
    nodes, meshes, materials, samplers, channels = [], [], [], [], []
    geometry_cache, mesh_cache, material_cache = {}, {}, {}
    time_accessor = builder.add(scene.times, 1, bounds=True)
    for index, node in enumerate(scene.nodes):
        if check:
            check()
        record: dict[str, Any] = {
            "name": node.name,
            "translation": [float32(v, context="node position") for v in node.translations[0]],
            "rotation": [float32(v, context="node rotation") for v in node.rotations_xyzw[0]],
            "extras": {"ontokin": node.metadata},
        }
        if isinstance(node.mesh, SurfaceMesh):
            mesh = node.mesh
            positions = builder.add(mesh.positions, 3, target=34962, bounds=True,
                                    geometry=True, surface=True)
            normals = builder.add(mesh.normals, 3, target=34962)
            component = 5123 if len(mesh.positions) < 65536 else 5125
            primitives = []
            for region in mesh.regions:
                if check:
                    check()
                source_material = region.material
                identity = {"source_region_key": region.key,
                            "occurrence_path": node.metadata["path"],
                            "element_id": node.metadata["element_id"],
                            "program_revision": node.metadata["program_revision"]}
                material = {"name": node.name + ": " + region.key,
                            "pbrMetallicRoughness": {
                                "baseColorFactor": list(source_material.rgba),
                                "metallicFactor": source_material.metallic,
                                "roughnessFactor": source_material.roughness},
                            "extras": {"ontokin": identity}}
                if source_material.rgba[3] < 1:
                    material["alphaMode"] = "BLEND"
                material_id = len(materials)
                materials.append(material)
                indices = builder.add(region.indices, 1, component=component, target=34963)
                primitives.append({"attributes": {"POSITION": positions, "NORMAL": normals},
                                   "indices": indices, "material": material_id, "mode": 4,
                                   "extras": {"ontokin": {"region_key": region.key}}})
            record["mesh"] = len(meshes)
            meshes.append({"name": mesh.name, "primitives": primitives})
        elif node.mesh is not None:
            mesh = node.mesh
            if node.color not in material_cache:
                material_cache[node.color] = len(materials)
                material = {"name": "OntoKin material " + str(len(materials)),
                            "pbrMetallicRoughness": {"baseColorFactor": list(node.color),
                                                    "metallicFactor": 0., "roughnessFactor": .7}}
                if node.color[3] < 1:
                    material["alphaMode"] = "BLEND"
                materials.append(material)
            material_id = material_cache[node.color]
            if id(mesh) not in geometry_cache:
                positions = builder.add(mesh.positions, 3, target=34962, bounds=True, geometry=True)
                normals = builder.add(mesh.normals, 3, target=34962)
                component = 5123 if len(mesh.positions) < 65536 else 5125
                indices = builder.add(mesh.indices, 1, component=component, target=34963)
                geometry_cache[id(mesh)] = (positions, normals, indices)
            cache_key = (id(mesh), material_id)
            if cache_key not in mesh_cache:
                position, normal, indices = geometry_cache[id(mesh)]
                mesh_cache[cache_key] = len(meshes)
                meshes.append({"name": mesh.name, "primitives": [{
                    "attributes": {"POSITION": position, "NORMAL": normal},
                    "indices": indices, "material": material_id, "mode": 4}]})
            record["mesh"] = mesh_cache[cache_key]
        nodes.append(record)
        for path, values, size in (("translation", node.translations, 3),
                                   ("rotation", node.rotations_xyzw, 4)):
            output = builder.add(values, size)
            channels.append({"sampler": len(samplers), "target": {"node": index, "path": path}})
            samplers.append({"input": time_accessor, "output": output, "interpolation": "LINEAR"})
    document: dict[str, Any] = {
        "asset": {"version": "2.0", "generator": "OntoKin reference " + scene.report["exporter"]["version"]},
        "scene": 0, "scenes": [{"name": scene.scene_name, "nodes": list(range(len(nodes)))}],
        "nodes": nodes, "buffers": [{"byteLength": len(builder.binary)}],
        "bufferViews": builder.views, "accessors": builder.accessors,
        "animations": [{"name": scene.module_name + ": " + scene.scene_name,
                        "samplers": samplers, "channels": channels,
                        "extras": {"ontokin": {"target_contract": scene.contract,
                                               "exact_times_seconds": [time_text(t) for t in scene.exact_times],
                                               "boundary_times_seconds": [time_text(t) for t in scene.boundaries]}}}],
        "extras": {"ontokin": scene.metadata},
    }
    if meshes:
        document["meshes"] = meshes
        document["materials"] = materials
    if scene.contract in NATIVE_TARGETS:
        document["extras"]["ontokin"]["surface_delivery"] = {
            "local_vertex_tolerance_m": min(scene.options.position_tolerance_m, 1e-5),
            "max_vertex_quantization_error_m": builder.max_surface_quantization_error_m,
            "normal_policy": "flat_shaded_triangle_corners",
            "material_policy": "one_primitive_per_used_source_region",
            "placement_policy": "baked_once_in_carrier_local_vertices_and_normals"}
    try:
        measure_json(document, max_bytes=max(0, MAX_GLB_BYTES - len(builder.binary) - 34),
                     max_entries=MAX_GLB_BYTES, check=check)
    except JSONLimitError as error:
        export_error("OKE-E-GLB-BUDGET", "Encoded glTF JSON and binary exceed the GLB byte budget.",
                     kind="resource", details=error.details)
    chunks = []
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    for number, chunk in enumerate(encoder.iterencode(document)):
        if check and number % 256 == 0:
            check()
        chunks.append(chunk.encode("utf-8"))
    json_bytes = b"".join(chunks)
    if check:
        check()
    json_bytes += b" " * (-len(json_bytes) % 4)
    binary = bytes(builder.binary)
    binary += b"\0" * (-len(binary) % 4)
    length = 12 + 8 + len(json_bytes) + 8 + len(binary)
    if length > MAX_GLB_BYTES:
        export_error("OKE-E-GLB-BUDGET", "Geometry, animation, and metadata exceed the GLB byte budget.", kind="resource")
    data = (struct.pack("<III", 0x46546C67, 2, length) + struct.pack("<II", len(json_bytes), 0x4E4F534A)
            + json_bytes + struct.pack("<II", len(binary), 0x004E4942) + binary)
    return data, builder.max_geometry_quantization_error_m


@dataclass
class DecodedGLB:
    document: dict[str, Any]
    binary: bytes
    _cache: dict[int, list[tuple]] = field(default_factory=dict, repr=False)
    _clocks: dict[int, list[float]] = field(default_factory=dict, repr=False)
    check: Callable[[], None] | None = field(default=None, repr=False)

    def clock(self, index: int) -> list[float]:
        if index not in self._clocks:
            self._clocks[index] = [row[0] for row in self.accessor(index)]
        return self._clocks[index]

    def accessor(self, index: int) -> list[tuple]:
        if index in self._cache:
            return self._cache[index]
        accessor = self.document["accessors"][index]
        view = self.document["bufferViews"][accessor["bufferView"]]
        size = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
        format_ = struct.Struct("<" + {5126: "f", 5123: "H", 5125: "I"}[accessor["componentType"]] * size)
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = view.get("byteStride", format_.size)
        result = []
        for row in range(accessor["count"]):
            if self.check and row % 256 == 0:
                self.check()
            result.append(format_.unpack_from(self.binary, offset + row * stride))
        self._cache[index] = result
        return result


def _format_error(message: str) -> None:
    export_error("OKE-E-GLB-STRUCTURE", message, kind="unsupported")


def read_glb(source: bytes | bytearray | str | Path, *, check=None) -> DecodedGLB:
    """Decode and structurally check the adapter's embedded, flat GLB subset."""
    if check:
        check()
    data = bytes(source) if isinstance(source, (bytes, bytearray)) else Path(source).read_bytes()
    if len(data) < 28 or len(data) > MAX_GLB_BYTES:
        _format_error("GLB size is outside the bounded reader contract.")
    magic, version, length = struct.unpack_from("<III", data)
    if magic != 0x46546C67 or version != 2 or length != len(data):
        _format_error("GLB header magic, version, or total length is invalid.")
    chunks, offset = [], 12
    while offset < len(data):
        if offset + 8 > len(data):
            _format_error("GLB chunk header is truncated.")
        size, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        if size % 4 or offset + size > len(data):
            _format_error("GLB chunks must be aligned and remain inside the file.")
        chunks.append((kind, data[offset:offset + size]))
        offset += size
    if [kind for kind, _ in chunks] != [0x4E4F534A, 0x004E4942]:
        _format_error("This adapter requires one JSON chunk followed by one embedded BIN chunk.")
    try:
        document = json.loads(chunks[0][1].decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        if document["asset"]["version"] != "2.0" or document.get("extensionsRequired"):
            _format_error("The adapter requires plain glTF 2.0 without required extensions.")
        binary = chunks[1][1]
        buffers = document["buffers"]
        if len(buffers) != 1 or "uri" in buffers[0] or not 0 <= len(binary) - buffers[0]["byteLength"] <= 3:
            _format_error("GLB must have one embedded buffer with at most three padding bytes.")
        for view in document["bufferViews"]:
            start, size = view.get("byteOffset", 0), view["byteLength"]
            if view["buffer"] != 0 or start < 0 or size <= 0 or start % 4 or start + size > buffers[0]["byteLength"]:
                _format_error("A buffer view is out of bounds or misaligned.")
        decoded = DecodedGLB(document, binary, check=check)
        for index, accessor in enumerate(document["accessors"]):
            if check:
                check()
            if accessor.get("sparse") or accessor.get("normalized"):
                _format_error("Sparse and normalized accessors are outside this adapter's reader subset.")
            count = accessor["count"]
            if not isinstance(count, int) or count <= 0:
                _format_error("Accessor counts must be positive integers.")
            view = document["bufferViews"][accessor["bufferView"]]
            component_size = {5126: 4, 5123: 2, 5125: 4}[accessor["componentType"]]
            size = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
            stride = view.get("byteStride", component_size * size)
            start = accessor.get("byteOffset", 0)
            if start < 0 or start % component_size or stride < size * component_size or stride % component_size or start + (count - 1) * stride + size * component_size > view["byteLength"]:
                _format_error("An accessor is out of bounds or misaligned.")
            values = decoded.accessor(index)
            if any(not math.isfinite(value) for row in values for value in row):
                _format_error("Accessors may not contain NaN or infinity.")
            for label, operation in (("min", min), ("max", max)):
                if label in accessor and accessor[label] != [operation(row[i] for row in values) for i in range(size)]:
                    _format_error("Accessor declared bounds do not match decoded buffer values.")
        nodes = document["nodes"]
        roots = document["scenes"][document.get("scene", 0)]["nodes"]
        if not nodes or sorted(roots) != list(range(len(nodes))) or any(n.get("children") or "matrix" in n for n in nodes):
            _format_error("This adapter requires every node to be a scene root with TRS transforms.")
        for node in nodes:
            translation, rotation = node.get("translation", [0., 0., 0.]), node.get("rotation", [0., 0., 0., 1.])
            if len(translation) != 3 or len(rotation) != 4 or not all(math.isfinite(v) for v in translation + rotation) or abs(math.hypot(*rotation) - 1) > 1e-5:
                _format_error("Node transforms must be finite and rotations must be unit XYZW quaternions.")
            if node.get("scale", [1., 1., 1.]) != [1., 1., 1.]:
                _format_error("This adapter stores source dimensions in geometry and does not support node scaling.")
            if "mesh" in node:
                document["meshes"][node["mesh"]]
        for mesh in document.get("meshes", []):
            if check:
                check()
            for primitive in mesh["primitives"]:
                if primitive.get("mode", 4) != 4:
                    _format_error("The adapter's geometry uses indexed triangles.")
                position_id, normal_id = primitive["attributes"]["POSITION"], primitive["attributes"]["NORMAL"]
                for index in (position_id, normal_id):
                    if document["accessors"][index]["type"] != "VEC3" or document["accessors"][index]["componentType"] != 5126:
                        _format_error("Position and normal accessors must contain binary32 VEC3 values.")
                if "min" not in document["accessors"][position_id] or "max" not in document["accessors"][position_id]:
                    _format_error("Position accessors require bounds.")
                positions, normals = decoded.accessor(position_id), decoded.accessor(normal_id)
                index_accessor = document["accessors"][primitive["indices"]]
                if index_accessor["type"] != "SCALAR" or index_accessor["componentType"] not in (5123, 5125):
                    _format_error("Triangle indices must be unsigned scalar integers.")
                indices = [row[0] for row in decoded.accessor(primitive["indices"])]
                if len(positions) != len(normals) or len(indices) % 3 or any(i < 0 or i >= len(positions) for i in indices):
                    _format_error("Primitive indices or vertex attribute counts are invalid.")
                if any(abs(math.hypot(*normal) - 1) > 1e-5 for normal in normals):
                    _format_error("Decoded vertex normals must have unit length.")
                for start in range(0, len(indices), 3):
                    if check and start % 768 == 0:
                        check()
                    a, b, c = (positions[i] for i in indices[start:start + 3])
                    u, v = tuple(y - x for x, y in zip(a, b)), tuple(y - x for x, y in zip(a, c))
                    scale = max(abs(component) for component in (*u, *v))
                    if scale == 0:
                        _format_error("Binary32 geometry contains a collapsed triangle.")
                    u, v = tuple(x / scale for x in u), tuple(x / scale for x in v)
                    cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2],
                             u[0] * v[1] - u[1] * v[0])
                    if max(abs(component) for component in cross) == 0:
                        _format_error("Binary32 geometry contains a degenerate triangle.")
                    if any(sum(n * c for n, c in zip(normals[i], cross)) <= 0
                           for i in indices[start:start + 3]):
                        _format_error("Triangle winding disagrees with its outward vertex normals.")
                document["materials"][primitive["material"]]
        for material in document.get("materials", []):
            pbr = material.get("pbrMetallicRoughness", {})
            color = pbr.get("baseColorFactor", [1., 1., 1., 1.])
            if len(color) != 4 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in color):
                _format_error("PBR base color must be a finite linear RGBA factor in [0,1].")
            if any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1
                   for value in (pbr.get("metallicFactor", 1.), pbr.get("roughnessFactor", 1.))):
                _format_error("PBR metallic and roughness factors must be finite numbers in [0,1].")
        if len(document["animations"]) != 1:
            _format_error("This adapter requires exactly one baked clip.")
        animation = document["animations"][0]
        targets = set()
        for channel in animation["channels"]:
            target = channel["target"]
            pair = (target["node"], target["path"])
            if pair in targets or target["node"] not in roots or target["path"] not in ("translation", "rotation"):
                _format_error("Animation targets must be unique root-node translation/rotation channels.")
            targets.add(pair)
            sampler = animation["samplers"][channel["sampler"]]
            incoming, outgoing = document["accessors"][sampler["input"]], document["accessors"][sampler["output"]]
            if sampler.get("interpolation", "LINEAR") != "LINEAR" or incoming["type"] != "SCALAR" or incoming["componentType"] != 5126 or "min" not in incoming or "max" not in incoming:
                _format_error("Animation input must be a bounded binary32 SCALAR with LINEAR interpolation.")
            times = [row[0] for row in decoded.accessor(sampler["input"])]
            if times[0] < 0 or any(a >= b for a, b in zip(times, times[1:])):
                _format_error("Animation input timestamps must be strictly increasing and nonnegative.")
            if outgoing["count"] != incoming["count"] or outgoing["componentType"] != 5126 or outgoing["type"] != ("VEC3" if target["path"] == "translation" else "VEC4"):
                _format_error("Animation output type/count does not match its target and input.")
            initial = tuple(nodes[target["node"]].get(target["path"], (0., 0., 0.) if target["path"] == "translation" else (0., 0., 0., 1.)))
            if initial != decoded.accessor(sampler["output"])[0]:
                _format_error("Default node transforms must equal the first decoded animation key.")
            if target["path"] == "rotation" and any(abs(math.hypot(*q) - 1) > 1e-5 for q in decoded.accessor(sampler["output"])):
                _format_error("Animation quaternion outputs must have unit length.")
        if targets != {(i, path) for i in roots for path in ("translation", "rotation")}:
            _format_error("Every exported node must have translation and rotation animation channels.")
        return decoded
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, struct.error, OverflowError, UnicodeError) as exc:
        _format_error("Malformed or unsupported data in the bounded GLB structure: " + str(exc))


def _slerp(a: tuple, b: tuple, amount: float) -> tuple:
    a = tuple(value / math.hypot(*a) for value in a)
    b = tuple(value / math.hypot(*b) for value in b)
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b, dot = tuple(-value for value in b), -dot
    dot = min(1., max(-1., dot))
    if dot > .9999995:
        result = tuple(x + amount * (y - x) for x, y in zip(a, b))
    else:
        angle = math.acos(dot)
        denominator = math.sin(angle)
        result = tuple((math.sin((1 - amount) * angle) * x + math.sin(amount * angle) * y) / denominator
                       for x, y in zip(a, b))
    norm = math.hypot(*result)
    return tuple(value / norm for value in result)


def sample_animation(decoded: DecodedGLB, time_seconds: float | Fraction) -> dict[int, dict[str, tuple]]:
    """Sample decoded binary32 channels using LINEAR translation and SLERP."""
    time = float(time_seconds)
    if not math.isfinite(time):
        _format_error("Animation sample time must be finite.")
    animation = decoded.document["animations"][0]
    states: dict[int, dict[str, tuple]] = {i: {} for i in range(len(decoded.document["nodes"]))}
    for channel in animation["channels"]:
        if decoded.check:
            decoded.check()
        target = channel["target"]
        sampler = animation["samplers"][channel["sampler"]]
        times = decoded.clock(sampler["input"])
        values = decoded.accessor(sampler["output"])
        upper = bisect.bisect_right(times, time)
        if upper == 0:
            value = values[0]
        elif upper == len(times):
            value = values[-1]
        else:
            amount = (time - times[upper - 1]) / (times[upper] - times[upper - 1])
            value = (_slerp(values[upper - 1], values[upper], amount) if target["path"] == "rotation" else
                     tuple(a + amount * (b - a) for a, b in zip(values[upper - 1], values[upper])))
        if target["path"] == "rotation":
            value = tuple(component / math.hypot(*value) for component in value)
        states[target["node"]][target["path"]] = value
    return states


def _validate_surface(decoded: DecodedGLB, node: dict, obj, model: SceneModel,
                      *, remaining_vertices: int, check=None) -> tuple[float, int]:
    """Compare actual regional buffers and PBR assignments with the source recipe."""
    expected = build_surface_mesh(obj.geometry, max_vertices=remaining_vertices, check=check)
    if node["extras"]["ontokin"].get("surface") != surface_metadata(obj.geometry, expected, check=check):
        _format_error("Surface metadata must preserve authored section ordering, regions and local placement.")
    primitives = decoded.document["meshes"][node["mesh"]]["primitives"]
    if len(primitives) != len(expected.regions):
        _format_error("A native surface needs exactly one primitive per used source region in one logical mesh.")
    materials, attribute_pairs = set(), set()
    max_error = 0.
    for primitive, region in zip(primitives, expected.regions):
        if check:
            check()
        if primitive.get("extras", {}).get("ontokin") != {"region_key": region.key}:
            _format_error("Surface primitive identity must match its authored region key.")
        position_id, normal_id = primitive["attributes"]["POSITION"], primitive["attributes"]["NORMAL"]
        pair = (position_id, normal_id)
        if pair not in attribute_pairs:
            attribute_pairs.add(pair)
            positions, normals = decoded.accessor(position_id), decoded.accessor(normal_id)
            if len(positions) != len(expected.positions) or len(normals) != len(expected.normals):
                _format_error("Surface corner counts must match its authored section/facet/cap topology.")
            for number, (position, normal, source_position, source_normal) in enumerate(
                    zip(positions, normals, expected.positions, expected.normals)):
                if check and number % 256 == 0:
                    check()
                max_error = max(max_error, *(abs(a - b) for a, b in zip(position, source_position)))
                if (position != tuple(float32(v) for v in source_position) or
                        normal != tuple(float32(v) for v in source_normal)):
                    _format_error("Surface positions and normals must match the source geometry and single local placement.")
        indices = tuple(row[0] for row in decoded.accessor(primitive["indices"]))
        if indices != region.indices:
            _format_error("Surface triangle winding and regional membership must match the source topology.")
        material_id = primitive["material"]
        if material_id in materials:
            _format_error("Distinct surface region keys require distinct source material identities.")
        materials.add(material_id)
        material = decoded.document["materials"][material_id]
        source = region.material
        if (material.get("pbrMetallicRoughness") != {
                "baseColorFactor": list(source.rgba), "metallicFactor": source.metallic,
                "roughnessFactor": source.roughness} or
                material.get("alphaMode", "OPAQUE") != ("BLEND" if source.rgba[3] < 1 else "OPAQUE")):
            _format_error("Surface PBR factors and transparency must match the authored regional material.")
        identity = {"source_region_key": region.key, "occurrence_path": obj.path,
                    "element_id": list(obj.element_id), "program_revision": model.program_revision}
        if material.get("extras", {}).get("ontokin") != identity:
            _format_error("Surface material provenance must identify its exact program, occurrence and source region.")
    if len(attribute_pairs) != 1:
        _format_error("Surface primitives must share the logical mesh's positions and normals.")
    return max_error, len(expected.positions)


def _validate_export(data: bytes, model: SceneModel, *, options: ExportOptions | None = None,
                     target_contract: str = TARGET_CONTRACT, check=None) -> dict[str, Any]:
    """Compare decoded bytes with fresh evaluator samples, without baked poses.

    Checks cover source key times, stored key times, three interior points per
    interval, and both sides of exact semantic boundaries. This is measured
    finite evidence, not a proof of continuous-error bounds for every program.
    """
    version = checked_contract(model, target_contract)
    if check:
        check()
    program = program_metadata(model, check=check) if target_contract in PROGRAM_TARGETS else None
    decoded = read_glb(data, check=check)
    animation = decoded.document["animations"][0]
    try:
        authored = [exact_time(t) for t in animation["extras"]["ontokin"]["exact_times_seconds"]]
    except (KeyError, TypeError, OntoKinError) as exc:
        _format_error("The clip must retain exact source sampling timestamps.")
    if not authored:
        _format_error("The clip must contain exact source timestamps.")
    options = options or ExportOptions(end=authored[-1], helpers=any(
        node.get("extras", {}).get("ontokin", {}).get("kind") == "visual_helper" for node in decoded.document["nodes"]))
    end = options.checked_end(model)
    boundaries = sorted({Fraction(0), end} | {exact_time(t) for t in preflight(model, check=check)["boundary_times_seconds"] if exact_time(t) <= end})
    if target_contract == IMPULSE_TARGET:
        _boundary_output_budget(model, len(boundaries), target_contract=target_contract, check=check)
    sampler = animation["samplers"][0]
    times = [row[0] for row in decoded.accessor(sampler["input"])]
    if len(authored) != len(times) or authored[0] != 0 or authored[-1] != end or any(a >= b for a, b in zip(authored, authored[1:])) or not set(boundaries).issubset(authored):
        _format_error("Exported source times must retain the complete interval and every exact semantic boundary.")
    if any([row[0] for row in decoded.accessor(s["input"])] != times for s in animation["samplers"]):
        _format_error("This adapter requires a common sampling clock for all channels.")
    speed = _angular_speed_bound(model, check=check)
    if not math.isfinite(speed) or any(max(float(b - a), last - first) * speed >= math.pi / 2
        for a, b, first, last in zip(authored, authored[1:], times, times[1:])):
        export_error("OKE-E-ROTATION-ALIAS", "Decoded key spacing cannot preserve the source's bounded rotation path.", model)
    if animation["extras"]["ontokin"].get("boundary_times_seconds") != [time_text(t) for t in boundaries]:
        _format_error("Animation metadata must retain the exact semantic boundary list.")
    if animation["extras"]["ontokin"].get("target_contract") != target_contract:
        _format_error("Animation metadata must retain the explicitly requested delivery contract.")
    def plain(value: Any) -> Any:
        return json.loads(json.dumps(value, allow_nan=False))
    metadata = decoded.document.get("extras", {}).get("ontokin", {})
    if any(metadata.get(key) != expected for key, expected in (
        ("target_contract", target_contract), ("schema_version", version), ("module", model.module_name), ("scene", model.scene_name),
        ("profile", model.profile), ("gravity_m_per_s2", list(model.gravity)),
        ("transform_policy", "all_nodes_are_roots_with_baked_world_poses"))):
        _format_error("Scene metadata must match the supplied semantic model and export contract.")
    if program is not None:
        if metadata.get("program") != program:
            _format_error("GLB bundle/source/occurrence provenance must match the complete supplied program.")
        source = metadata.get("source", {})
        if (source.get("entry_source_id") != "entry" or
                source.get("entry_revision") != program["sources"]["entry"]["source_revision"] or
                source.get("editable_source_of_truth") != "pinned .ok source bundle"):
            _format_error("GLB entry source identity must remain separate from the program revision.")
    if target_contract == IMPULSE_TARGET and metadata.get("impulse_profile") != impulse_profile_metadata():
        _format_error("Impulse delivery metadata must disclose the source physical model and recorded playback.")
    for key, expected in relationship_metadata(model).items():
        if metadata.get(key) != plain(expected):
            _format_error("Declared joint/follow metadata must match the supplied semantic model.")
    records = metadata.get("boundary_states", [])
    if not isinstance(records, list) or [record.get("source_seconds") for record in records] != [time_text(t) for t in boundaries]:
        _format_error("Boundary-state metadata must retain every exact semantic boundary in order.")
    boundary_records = {record["source_seconds"]: record for record in records}
    probes = set(authored) | {Fraction(t) for t in times if 0 <= Fraction(t) <= end}
    for first, last in zip(times, times[1:]):
        probes.update(point for fraction in (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4))
                      if 0 <= (point := Fraction(first) + fraction * (Fraction(last) - Fraction(first))) <= end)
    requests = [{"time_seconds": time, "side": side} for time in sorted(probes | set(boundaries))
                for side in (("before", "after") if time in boundaries else ("after",))]
    nodes = decoded.document["nodes"]
    if len(requests) * len(nodes) > MAX_VALIDATION_POSES:
        export_error("OKE-E-VALIDATION-BUDGET", "Independent validation exceeds the pose comparison budget.", model,
                     kind="resource", details={"max_validation_poses": MAX_VALIDATION_POSES})
    paths, frames, actual_helpers = set(), {}, set()
    max_geometry_error = max_surface_error = 0.
    remaining_vertices = MAX_MESH_VERTICES
    properties = (bounded_data({path: dict(obj.properties) for path, obj in model.objects.items()}, check=check)
                  if program is not None else None)
    for index, node in enumerate(nodes):
        if check:
            check()
        metadata = node.get("extras", {}).get("ontokin", {})
        if metadata.get("kind") == "object":
            path = metadata.get("path")
            if path in paths or path not in model.objects or metadata.get("element_id") != list(model.objects[path].element_id) or metadata.get("owner") != model.objects[path].owner:
                _format_error("Exported object identities and ownership must match the supplied semantic model.")
            paths.add(path)
            frames[index] = path + ".frame"
            obj = model.objects[path]
            for key, expected in (("class_name", obj.class_name), ("geometry", geometry_metadata(obj.geometry, check=check)
                                  if target_contract in NATIVE_TARGETS else obj.geometry),
                                  ("physical", obj.physical), ("collision", obj.collision),
                                  ("authored_motion", obj.motion), ("appearance_linear_rgba", obj.appearance),
                                  ("role", obj.role), ("pose_frame", "world"),
                                  ("properties", properties[path] if properties is not None else
                                   {name: value.to_data() for name, value in obj.properties.items()})):
                if metadata.get(key) != plain(expected):
                    _format_error("Object metadata must preserve the supplied model's geometry, physical description, and resolved properties.")
            if program is not None and (metadata.get("program_revision") != model.program_revision or
                                        metadata.get("source_mapping") != model.occurrence_provenance[path]):
                _format_error("Each exported object must retain its matching generated/ordinary source mapping.")
            if obj.geometry["kind"] == "empty":
                if "mesh" in node:
                    _format_error("An empty source object cannot acquire untagged helper geometry.")
            elif obj.geometry["kind"] in ("loft", "placed") and target_contract in NATIVE_TARGETS:
                if "mesh" not in node:
                    _format_error("A native surface must have an actual mesh.")
                error, vertex_count = _validate_surface(decoded, node, obj, model,
                    remaining_vertices=remaining_vertices, check=check)
                max_geometry_error = max(max_geometry_error, error)
                max_surface_error = max(max_surface_error, error)
                remaining_vertices -= vertex_count
            else:
                if "mesh" not in node:
                    _format_error("A source visual solid must have a mesh.")
                primitives = decoded.document["meshes"][node["mesh"]]["primitives"]
                if len(primitives) != 1:
                    _format_error("A source visual solid must use the adapter's single material primitive.")
                primitive = primitives[0]
                positions = decoded.accessor(primitive["attributes"]["POSITION"])
                if target_contract in NATIVE_TARGETS:
                    remaining_vertices -= len(positions)
                extents = ([obj.geometry["radius"]] * 3 if obj.geometry["kind"] == "sphere" else
                           [component / 2 for component in obj.geometry["size"]])
                for axis, extent in enumerate(extents):
                    max_geometry_error = max(max_geometry_error, abs(min(p[axis] for p in positions) + extent),
                                             abs(max(p[axis] for p in positions) - extent))
                if obj.geometry["kind"] == "sphere":
                    max_geometry_error = max(max_geometry_error,
                        max(abs(math.hypot(*p) - obj.geometry["radius"]) for p in positions))
                else:
                    max_geometry_error = max(max_geometry_error,
                        max(abs(abs(component) - extent) for p in positions for component, extent in zip(p, extents)))
                material = decoded.document["materials"][primitive["material"]]
                pbr = material.get("pbrMetallicRoughness", {})
                if pbr.get("baseColorFactor") != list(obj.appearance) or pbr.get("metallicFactor") != 0 or pbr.get("roughnessFactor") != .7 or material.get("alphaMode", "OPAQUE") != ("BLEND" if obj.appearance[3] < 1 else "OPAQUE"):
                    _format_error("Exported material factors must preserve the source linear RGBA and adapter material defaults.")
        elif metadata.get("kind") == "visual_helper" and metadata.get("physical_participation") == "none":
            frames[index] = metadata["frame_path"]
            identity = (metadata.get("helper_kind"), tuple(metadata.get("related_element_id", ())))
            if identity in actual_helpers:
                _format_error("Visual helper identities cannot be duplicated.")
            actual_helpers.add(identity)
            if target_contract in NATIVE_TARGETS and "mesh" in node:
                primitive = decoded.document["meshes"][node["mesh"]]["primitives"][0]
                remaining_vertices -= len(decoded.accessor(primitive["attributes"]["POSITION"]))
        else:
            _format_error("Every node must identify its OntoKin occurrence or explicit visual-helper role.")
        if target_contract in NATIVE_TARGETS and remaining_vertices < 0:
            export_error("OKE-E-MESH-BUDGET", "Decoded surface occurrences exceed the aggregate mesh budget.",
                         model, kind="resource")
    if paths != set(model.objects):
        _format_error("All semantic object occurrences must appear exactly once in the exported scene.")
    expected_helpers = ({("assembly_origin", tuple(obj.element_id)) for obj in model.objects.values() if obj.geometry["kind"] == "empty"}
                        | {("joint_parent_site", tuple(j.element_id)) for j in model.joints.values()}) if options.helpers else set()
    if actual_helpers != expected_helpers:
        _format_error("Visual helper nodes must match the requested option and declared source objects/joints.")
    max_position = max_rotation = 0.
    worst_position = worst_rotation = None
    failures = []
    for request, reference in zip(requests, sampled_states(model, requests, check=check)):
        if check:
            check()
        if reference["side"] == "after" and reference["time_seconds"] in boundary_records:
            record = boundary_records[reference["time_seconds"]]
            expected = {"joint_states_after": reference["joints"], "action_states_after": reference["actions"],
                        "pose_authorities_after": {path: obj["pose_authority"] for path, obj in reference["objects"].items()}}
            if target_contract == IMPULSE_TARGET:
                expected["impulse_states_after"] = {path: obj["impulses"] for path, obj in reference["objects"].items()}
            if any(record.get(key) != plain(value) for key, value in expected.items()):
                _format_error("Stored boundary lifecycle/pose-authority metadata must match fresh semantic evaluation.")
        actual = sample_animation(decoded, request["time_seconds"])
        for index, state in actual.items():
            if frames[index] not in reference["frames"]:
                _format_error("An exported helper references an unavailable semantic frame.")
            expected = reference["frames"][frames[index]]
            position_error = max(abs(a - b) for a, b in zip(state["translation"], expected["position_m"]))
            q = expected["orientation_wxyz"]
            angle_error = rotation_error(state["rotation"], (q[1], q[2], q[3], q[0]))
            where = {"node": nodes[index]["name"], "time_seconds": reference["time_seconds"], "side": reference["side"]}
            if position_error > max_position:
                max_position, worst_position = position_error, where
            if angle_error > max_rotation:
                max_rotation, worst_rotation = angle_error, where
            if position_error > options.position_tolerance_m or angle_error > options.rotation_tolerance_rad:
                if len(failures) < 20:
                    failures.append({**where, "position_error_m": position_error, "rotation_error_rad": angle_error})
    time_error = max(abs(float(Fraction(t) - exact)) for t, exact in zip(times, authored))
    surface_tolerance = min(options.position_tolerance_m, 1e-5)
    if target_contract in NATIVE_TARGETS:
        delivery = decoded.document["extras"]["ontokin"].get("surface_delivery")
        expected_delivery = {"local_vertex_tolerance_m": surface_tolerance,
            "max_vertex_quantization_error_m": max_surface_error,
            "normal_policy": "flat_shaded_triangle_corners",
            "material_policy": "one_primitive_per_used_source_region",
            "placement_policy": "baked_once_in_carrier_local_vertices_and_normals"}
        if delivery != expected_delivery:
            _format_error("Surface conversion metadata must identify the actual decoded loss and delivery policy.")
    passed = (max_position <= options.position_tolerance_m and max_rotation <= options.rotation_tolerance_rad
              and time_error <= options.time_tolerance_s and max_geometry_error <= options.position_tolerance_m
              and max_surface_error <= surface_tolerance)
    return {"status": "passed" if passed else "failed", "structure": "passed_bounded_glb_reader",
            "method": "Decode serialized JSON/BIN accessors; LINEAR translation and shortest-path SLERP; compare fresh semantic evaluation.",
            "position_metric": "maximum absolute XYZ component error in metres",
            "rotation_metric": "orientation angle in radians, invariant to quaternion sign",
            "probe_policy": "source/stored keys, quarter/mid/three-quarter interval times, before/after exact boundaries",
            "sample_count": len(requests), "node_pose_comparisons": len(requests) * len(nodes),
            "max_position_error_m": max_position, "max_rotation_error_rad": max_rotation,
            "max_time_error_seconds": time_error, "worst_position": worst_position, "worst_rotation": worst_rotation,
            "max_geometry_dimension_error_m": max_geometry_error,
            **({"max_surface_vertex_error_m": max_surface_error,
                "surface_vertex_tolerance_m": surface_tolerance,
                "surface_geometry_materials_and_provenance": "passed_source_comparison"}
               if target_contract in NATIVE_TARGETS else {}),
            "failures": failures, "failure_details_truncated": len(failures) == 20,
            "scope": "Finite numerical evidence for this artifact and interval; no all-time error proof, rendering-quality proof, or destination import certification."}


def validate_export(data: bytes, model: SceneModel, *, options: ExportOptions | None = None,
                    target_contract: str = TARGET_CONTRACT, check=None) -> dict[str, Any]:
    """Return measured byte-validation results, or a structured malformed-data error."""
    try:
        return _validate_export(data, model, options=options, target_contract=target_contract,
                                check=_guard_check(check))
    except _CallbackFailure as failure:
        raise failure.error
    except OntoKinError as error:
        error.diagnostic.details["target_contract"] = target_contract
        raise
    except JSONLimitError as error:
        export_error("OKE-E-METADATA-BUDGET", "Supplied program values exceed bounded validation materialization.",
                     model, kind="resource", details=error.details)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        export_error("OKE-E-GLB-STRUCTURE", "Malformed source mapping or validation data in the bounded GLB contract: " + str(exc),
                     model, kind="unsupported", details={"target_contract": target_contract})


def _export_glb(model: SceneModel, *, options: ExportOptions | None = None,
                source_uri: str | None = None, source_sha256: str | None = None,
                target_contract: str = TARGET_CONTRACT, check=None) -> ExportResult:
    """Produce verified GLB bytes and their report without writing any files."""
    scene = build_scene(model, options=options, source_uri=source_uri, source_sha256=source_sha256,
                        target_contract=target_contract, check=check)
    data, geometry_error = _encode(scene, check=check)
    if geometry_error > scene.options.position_tolerance_m:
        export_error("OKE-E-GEOMETRY-PRECISION", "Mesh vertex binary32 quantization exceeds the position tolerance.", model,
                     details={"max_geometry_quantization_error_m": geometry_error,
                              "position_tolerance_m": scene.options.position_tolerance_m})
    validation = _validate_export(data, model, options=scene.options, target_contract=target_contract, check=check)
    if validation["status"] != "passed":
        export_error("OKE-E-ANIMATION-PRECISION", "Decoded GLB animation exceeds the requested numerical tolerance.", model,
                     details={"validation": validation, "tolerances": scene.report["tolerances"]})
    report = copy.deepcopy(scene.report)
    report["outcome"] = "valid"
    report["geometry"]["max_vertex_quantization_error_m"] = geometry_error
    report["validation"] = validation
    report["artifact"] = {"media_type": "model/gltf-binary", "gltf_version": "2.0", "byte_length": len(data),
                          "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}
    report["destination_validation"] = {"status": "not_performed_by_exporter",
                                       "note": "A named external viewer or Blender import requires separate recorded evidence."}
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).resolve().parent.glob("*.py")):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    report["source_code_sha256"] = digest.hexdigest()
    report["environment"] = {"python": platform.python_version(),
                             "python_implementation": platform.python_implementation(),
                             "operating_system": platform.system()}
    scene.report = report
    if check:
        check()
    return ExportResult(data, report, scene)


def export_glb(model: SceneModel, *, options: ExportOptions | None = None,
               source_uri: str | None = None, source_sha256: str | None = None,
               target_contract: str = TARGET_CONTRACT, check=None) -> ExportResult:
    """Produce verified bytes with an explicit profile and cooperative cancellation."""
    try:
        return _export_glb(model, options=options, source_uri=source_uri, source_sha256=source_sha256,
                           target_contract=target_contract, check=_guard_check(check))
    except _CallbackFailure as failure:
        raise failure.error
    except OntoKinError as error:
        error.diagnostic.details["target_contract"] = target_contract
        raise
