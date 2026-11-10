"""Finite captured-pose GLB encoding; native X/time are never synthesized."""
import contextlib
import io
import json
import math
from pathlib import Path
import struct

from .common import Failure, PARTS, canonical_bytes, sha256
from . import playback_projection as projection


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def quaternion(matrix):
    # Native Blender basis -> glTF basis, Rg = B Rb B^-1.
    r = [[matrix[0][0], matrix[0][2], -matrix[0][1]],
         [matrix[2][0], matrix[2][2], -matrix[2][1]],
         [-matrix[1][0], -matrix[1][2], matrix[1][1]]]
    trace = sum(r[i][i] for i in range(3))
    if trace > 0:
        scale = math.sqrt(trace + 1) * 2
        q = [(r[2][1] - r[1][2]) / scale, (r[0][2] - r[2][0]) / scale,
             (r[1][0] - r[0][1]) / scale, scale / 4]
    else:
        i = max(range(3), key=lambda index: r[index][index])
        j, k = (i + 1) % 3, (i + 2) % 3
        scale = math.sqrt(max(0, 1 + r[i][i] - r[j][j] - r[k][k])) * 2
        q = [0.0, 0.0, 0.0, (r[k][j] - r[j][k]) / scale]
        q[i], q[j], q[k] = scale / 4, (r[j][i] + r[i][j]) / scale, (r[k][i] + r[i][k]) / scale
    norm = math.sqrt(sum(v * v for v in q))
    return [v / norm for v in q]


def mesh_geometry(box):
    x, y, z = [value / 2000 for value in box]
    corners = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
               (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [((0, 3, 2, 1), (0, 0, -1)), ((4, 5, 6, 7), (0, 0, 1)),
             ((0, 1, 5, 4), (0, -1, 0)), ((3, 7, 6, 2), (0, 1, 0)),
             ((0, 4, 7, 3), (-1, 0, 0)), ((1, 2, 6, 5), (1, 0, 0))]
    positions, normals, indices = [], [], []
    for face, normal in faces:
        base = len(positions)
        positions.extend(corners[index] for index in face)
        normals.extend([normal] * 4)
        indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])
    return positions, normals, indices


def encode_raw(stage, native, context, budget, backend):
    source = context.canonical
    model = {"asset": {"version": "2.0", "generator": "OntoKin C191 finite captured-pose encoder",
                       "extras": {"output_binding": source["output"], "canonical_input_sha256": context.canonical_sha}},
             "scene": 0, "scenes": [{"nodes": [0, 1, 3, 4, 6]}],
             "nodes": [], "meshes": [], "materials": [], "animations": [],
             "accessors": [], "bufferViews": [], "buffers": []}
    binary = bytearray()

    def add(rows, kind, component=5126, target=None, include_bounds=True):
        width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[kind]
        values = [(value,) for value in rows] if width == 1 else rows
        if component == 5126:
            values = [[f32(value) for value in row] for row in values]
        budget.charge("encoded_scalar_values", len(values) * width)
        binary.extend(b"\x00" * (-len(binary) % 4))
        start = len(binary)
        layout = struct.Struct("<" + ("f" if component == 5126 else "H") * width)
        for row in values:
            binary.extend(layout.pack(*row))
        view = {"buffer": 0, "byteOffset": start, "byteLength": len(binary) - start}
        if target is not None:
            view["target"] = target
        model["bufferViews"].append(view)
        accessor = {"bufferView": len(model["bufferViews"]) - 1, "componentType": component,
                    "count": len(values), "type": kind}
        if include_bounds:
            accessor.update(min=[min(row[a] for row in values) for a in range(width)],
                            max=[max(row[a] for row in values) for a in range(width)])
        model["accessors"].append(accessor)
        return len(model["accessors"]) - 1

    initial = native["samples"][0]
    for index, name in enumerate(PARTS):
        positions, normals, indices = mesh_geometry(source["parts"][name]["box_mm"])
        position_index, normal_index = add(positions, "VEC3", target=34962), add(normals, "VEC3", target=34962)
        index_index = add(indices, "SCALAR", component=5123, target=34963)
        model["meshes"].append({"name": name, "primitives": [{"attributes": {"POSITION": position_index, "NORMAL": normal_index},
                                                             "indices": index_index, "material": index, "mode": 4}]})
        model["materials"].append({"name": name + "_material", "pbrMetallicRoughness": {
            "baseColorFactor": source["parts"][name]["color_linear_rgba"],
            "metallicFactor": backend["glb_material"]["metallicFactor"],
            "roughnessFactor": backend["glb_material"]["roughnessFactor"]}, "doubleSided": False})
        matrix = initial["matrices_blender_m"][name]
        translation = [matrix[0][3], matrix[2][3], -matrix[1][3]]
        if name.endswith("_shoe"):
            local = native["configuration"]["objects"][name]["location"]
            translation = [local[0], local[2], -local[1]]
        node = {"name": name, "mesh": index, "translation": translation}
        if name.endswith("_carriage"):
            node["children"] = [index + 1]
        model["nodes"].append(node)
    times = add([record["time_s"] for record in native["samples"]], "SCALAR")
    animation = {"name": "native_guided_contact", "samplers": [], "channels": []}
    for name in ("left_carriage", "right_carriage"):
        matrices = [record["matrices_blender_m"][name] for record in native["samples"]]
        translations = [[m[0][3], m[2][3], -m[1][3]] for m in matrices]
        rotations = [quaternion(matrix) for matrix in matrices]
        for i in range(1, len(rotations)):
            if sum(a * b for a, b in zip(rotations[i - 1], rotations[i])) < 0:
                rotations[i] = [-v for v in rotations[i]]
        tracks = [("translation", translations, "VEC3")]
        if any(any(abs(q[a] - [0, 0, 0, 1][a]) > 0 for a in range(4)) for q in rotations):
            tracks.append(("rotation", rotations, "VEC4"))
        for path, rows, kind in tracks:
            # Output-track bounds are optional in glTF. Omit them in raw so
            # transverse projection cannot leave stale bounds or require an
            # extra raw/final metadata edit beyond the frozen mapping contract.
            output = add(rows, kind, include_bounds=False)
            animation["samplers"].append({"input": times, "output": output, "interpolation": "LINEAR"})
            animation["channels"].append({"sampler": len(animation["samplers"]) - 1,
                                           "target": {"node": PARTS.index(name), "path": path}})
    model["animations"].append(animation)
    model["buffers"] = [{"byteLength": len(binary)}]
    (stage / "raw.glb").write_bytes(projection.encode(model, binary))


def project(stage, budget):
    # The copied C190 proof now checks budget/cancellation during scalar decode,
    # each interval and each actual vertex evaluation.
    with contextlib.redirect_stdout(io.StringIO()):
        report = projection.map_playback(stage / "raw.glb", stage / "final.glb",
                                         stage / "post-export.json", stage / "native-transforms.json", budget)
    budget.check()
    return report


def verify_mapping(stage, native, context, budget):
    """Recheck bytes and native correspondence after any trusted fault hook."""
    try:
        raw_bytes, raw, raw_bin = projection.decode(stage / "raw.glb")
        final_bytes, final, final_bin = projection.decode(stage / "final.glb")
        if any(raw[key] != final[key] for key in ("asset", "nodes", "meshes", "materials", "scenes", "accessors", "bufferViews", "buffers")):
            raise ValueError("Projection changed a forbidden static field")
        if raw["animations"][0]["samplers"] != final["animations"][0]["samplers"]:
            raise ValueError("Projection changed animation samplers")
        names = [node["name"] for node in raw["nodes"]]
        if names != list(PARTS):
            raise ValueError("GLB stable IDs differ")
        expected_channels = [c for c in raw["animations"][0]["channels"] if c["target"]["path"] != "rotation"]
        if final["animations"][0]["channels"] != expected_channels:
            raise ValueError("Projection changed forbidden animation channels")
        allowed_offsets = set()
        expected_times = [f32(record["time_s"]) for record in native["samples"]]
        for channel in raw["animations"][0]["channels"]:
            sampler = raw["animations"][0]["samplers"][channel["sampler"]]
            if sampler["interpolation"] != "LINEAR":
                raise ValueError("Unsupported GLB interpolation")
            times, time_start, time_stride = projection.accessor(raw, raw_bin, sampler["input"])
            final_times, _, _ = projection.accessor(final, final_bin, sampler["input"])
            if [row[0] for row in times] != expected_times or final_times != times:
                raise ValueError("GLB time keys changed")
            node = names[channel["target"]["node"]]
            values, start, stride = projection.accessor(raw, raw_bin, sampler["output"])
            if channel["target"]["path"] == "translation":
                final_values, _, _ = projection.accessor(final, final_bin, sampler["output"])
                expected_x = [f32(record["matrices_blender_m"][node][0][3]) for record in native["samples"]]
                if [row[0] for row in values] != expected_x or [row[0] for row in final_values] != expected_x:
                    raise ValueError("Native carriage X sample was changed")
                for i, (before, after) in enumerate(zip(values, final_values)):
                    if after[1:] != values[0][1:]:
                        raise ValueError("Final guide projection is not constant")
                    for axis in (1, 2):
                        allowed_offsets.update(range(start + i * stride + axis * 4, start + i * stride + axis * 4 + 4))
            budget.charge("verified_animation_scalar_values", len(values) * len(values[0]) + len(times))
        if len(raw_bin) != len(final_bin) or any(a != b and i not in allowed_offsets for i, (a, b) in enumerate(zip(raw_bin, final_bin))):
            raise ValueError("Projection changed forbidden binary bytes")
        budget.charge("verified_binary_bytes", len(raw_bin))
        geometry = projection.mapping_geometry(raw, raw_bin, final, final_bin, native["samples"], budget)
        if geometry["native_sample_to_final_max_vertex_distance_mm"] > 0.2 or geometry["continuous_raw_export_to_final_full_clip_bound_mm"] > 0.2:
            raise ValueError("Native/raw to final vertex mapping exceeds 0.2 mm")
        report = json.loads((stage / "post-export.json").read_text())
        if report["raw_sha256"] != sha256(raw_bytes) or report["final_sha256"] != sha256(final_bytes):
            raise ValueError("Mapping receipt does not bind actual GLB bytes")
        return geometry
    except Failure:
        raise
    except (ValueError, KeyError, AssertionError, IndexError, struct.error, OSError, TypeError) as exc:
        raise Failure("E_MAPPING", str(exc), context.span(context.headers["output"])) from exc
