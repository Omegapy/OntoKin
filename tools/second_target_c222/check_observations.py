#!/usr/bin/env python3
"""Finite CPU observation-schema and exact corner-correspondence checker.

Only check_observations is the public admission API. Internal geometry and
validation seams do not admit replacement authority or attest native provenance.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import struct
import sys


sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location(
    "ontokin_c221_bindings", Path(__file__).absolute().parents[1] / "second_target_c221/check_bindings.py")
c221 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(c221)

VERSION = "C222/0.1.0"
SCHEMA = "ontokin.c222.geometry-observations/0.1"
REPORT_SCHEMA = "ontokin.c222.corner-correspondence/0.1"
MAX_OBSERVATION_BYTES = 16 * 1024 * 1024
COORDINATE_SYSTEM = {"position_unit": "m", "basis": "gltf-rh-y-up-identity",
                     "winding": "godot-clockwise-reverse-once"}
MAP_FIELDS = ["gltf_node", "gltf_primitive", "raw_triangle", "raw_corner", "raw_vertex",
              "source_mesh", "source_primitive", "source_triangle", "source_corner", "source_vertex"]


class CheckError(ValueError):
    def __init__(self, code, message, stage="structure"):
        super().__init__(message)
        self.code = code
        self.stage = stage


def require(condition, code, message, stage="structure"):
    if not condition:
        raise CheckError(code, message, stage)


def fields(value, expected, label):
    require(type(value) is dict and set(value) == set(expected), "SCHEMA", label + ": exact fields required")


def integer(value, label):
    require(type(value) is int and value >= 0, "INDEX", label + ": nonnegative integer required")
    return value


def text_value(value, label):
    require(type(value) is str and 0 < len(value) <= 4096 and "\x00" not in value,
            "TEXT", label + ": bounded nonempty text required")
    return value


def vector(value, label):
    require(type(value) is list and len(value) == 3, "VECTOR", label + ": three components required")
    result = []
    for component in value:
        try:
            valid = type(component) in (int, float) and math.isfinite(component)
        except OverflowError:
            valid = False
        require(valid, "FINITE", label + ": finite numeric components required")
        # No float32 conversion, rounding, scaling or tolerance is applied.
        result.append(0.0 if component == 0 else component)
    return tuple(result)


def _read_observation(path):
    supplied = os.fspath(path)
    require(type(supplied) is str and "\x00" not in supplied and
            ".." not in supplied.split("/"), "PATH", "Unsafe observation path", "observation_read")
    absolute = Path(os.path.abspath(supplied))
    try:
        with c221.SafeRoot(absolute.parent) as parent:
            fd = os.open(absolute.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent.fd)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode), "FILE", "Observation must be a regular file", "observation_read")
                require(0 < before.st_size <= MAX_OBSERVATION_BYTES, "SIZE", "Observation exceeds finite size bounds", "observation_read")
                chunks, remaining = [], before.st_size + 1
                while remaining:
                    chunk = os.read(fd, min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                raw = b"".join(chunks)
                after = os.fstat(fd)
                keys = ("st_dev", "st_ino", "st_size", "st_mode", "st_mtime_ns", "st_ctime_ns")
                require(len(raw) == before.st_size and all(getattr(before, k) == getattr(after, k) for k in keys),
                        "CHANGED", "Observation changed while reading", "observation_read")
                return raw
            finally:
                os.close(fd)
    except (OSError, c221.CheckError) as exc:
        raise CheckError("FILE", "Missing, unsafe or unreadable observation", "observation_read") from exc


def _source_geometry(glb, binary, part_map, payload):
    """Internal decoded-geometry seam; it establishes no immutable admission."""
    payload_rows = {}
    for row in payload["corners"]:
        key = row["key"]
        require(type(key) is list and len(key) == 4 and all(type(v) is int and v >= 0 for v in key),
                "AUTHORITY_GEOMETRY", "Invalid C214 corner key", "authority_geometry")
        key = tuple(key)
        require(key not in payload_rows, "AUTHORITY_GEOMETRY", "Duplicate C214 corner key", "authority_geometry")
        payload_rows[key] = row
    meshes, expected_keys, parts = {}, set(), {}
    for planned in part_map["entries"]:
        node, mesh = planned["glbNode"], planned["glbMesh"]
        surfaces = {}
        for primitive_row in planned["primitives"]:
            primitive = primitive_row["primitive"]
            cache_key = (mesh, primitive)
            if cache_key not in meshes:
                prim = glb["meshes"][mesh]["primitives"][primitive]
                pmeta, pbytes = c221._accessor(glb, binary, prim["attributes"]["POSITION"])
                imeta, ibytes = c221._accessor(glb, binary, prim["indices"])
                require(pmeta["component_type"] == 5126 and pmeta["type"] == "VEC3" and
                        imeta["component_type"] == 5123 and imeta["type"] == "SCALAR",
                        "AUTHORITY_GEOMETRY", "Unexpected finite source accessor format", "authority_geometry")
                positions = [vector(list(v), "Source position") for v in struct.iter_unpack("<3f", pbytes)]
                indices = [v[0] for v in struct.iter_unpack("<H", ibytes)]
                require(len(indices) % 3 == 0, "AUTHORITY_GEOMETRY", "Incomplete source triangle", "authority_geometry")
                triangles = []
                for offset in range(0, len(indices), 3):
                    verts = indices[offset:offset + 3]
                    triangle = offset // 3
                    keys = []
                    for corner, vertex in enumerate(verts):
                        key = (mesh, primitive, triangle, corner)
                        require(vertex < len(positions) and key in payload_rows, "AUTHORITY_GEOMETRY",
                                "Source corner missing or out of bounds", "authority_geometry")
                        record = payload_rows[key]
                        require(type(record["vertex"]) is int and record["vertex"] == vertex and
                                c221.canonical(record["winding"]) == c221.canonical(verts) and
                                record["position_f32le"] == pbytes[vertex * 12:vertex * 12 + 12].hex(),
                                "AUTHORITY_GEOMETRY", "C214 corner/GLB position disagreement", "authority_geometry")
                        expected_keys.add(key)
                        keys.append(key)
                    triangles.append({"index": triangle, "vertices": verts,
                                      "positions": [positions[v] for v in verts], "keys": keys})
                meshes[cache_key] = triangles
            surfaces[primitive] = {"material": primitive_row["material"], "triangles": meshes[cache_key]}
        parts[node] = {"planned": planned, "surfaces": surfaces}
    require(set(payload_rows) == expected_keys, "AUTHORITY_GEOMETRY", "Unexpected C214 corner inventory", "authority_geometry")
    require(len(parts) == 18 and len(expected_keys) == 3024, "AUTHORITY_GEOMETRY", "Unexpected source geometry inventory", "authority_geometry")
    return parts


def _load_authority(package_root):
    """Re-admit every public invocation; no caller-supplied pass report is trusted."""
    try:
        report = c221.check_package(package_root)
        bindings, part_map = c221.load_authority()
        needed = {}
        with c221.SafeRoot(package_root) as package:
            for index in (0, 3):
                pin = bindings["items"][index]
                needed[index] = package.read(pin["packagePath"], pin["bytes"], pin["sha256"], pin["mode"])
        glb, binary = c221.decode_glb(needed[0])
        payload = c221.strict_json(needed[3], "C214 payload")
        parts = _source_geometry(glb, binary, part_map, payload)
        return {"admission": report, "parts": parts, "glb_sha256": bindings["items"][0]["sha256"]}
    except c221.CheckError as exc:
        raise CheckError(exc.code, str(exc), "authority_admission") from exc


def _cyclic_key(positions):
    return min(tuple(positions[i:] + positions[:i]) for i in range(3))


def _match_surface(source_triangles, surface):
    """Internal exact-position seam; normals and names are never read here.

    Returns raw-triangle/raw-corner/raw-vertex plus C214 key/source-vertex rows.
    Source triangles supplied directly to this seam are NOT admitted authority.
    """
    positions = [vector(v, "Observed position") for v in surface["positions"]]
    indices = surface["indices"]
    by_positions = {}
    for source in source_triangles:
        source_positions = [vector(list(v), "Source position") for v in source["positions"]]
        key = _cyclic_key(source_positions)
        by_positions.setdefault(key, []).append((source, source_positions))
    used, rows = set(), []
    for offset in range(0, len(indices), 3):
        raw_indices = indices[offset:offset + 3]
        # C220 fixes this reversal before any observation, then permits cycles.
        comparison_positions = [positions[raw_indices[c]] for c in (0, 2, 1)]
        candidates = by_positions.get(_cyclic_key(comparison_positions), [])
        require(candidates, "MISSING_CORRESPONDENCE", "Observed triangle has no exact source position match", "correspondence")
        require(len(candidates) == 1, "AMBIGUOUS_CORRESPONDENCE", "Multiple source triangles share the position key", "correspondence")
        source, source_positions = candidates[0]
        rotations = [i for i in range(3) if comparison_positions == source_positions[i:] + source_positions[:i]]
        require(len(rotations) == 1, "AMBIGUOUS_CORRESPONDENCE", "Corner rotation is not unique", "correspondence")
        triangle = source["index"]
        require(triangle not in used, "DUPLICATE_CORRESPONDENCE", "Source triangle matched more than once", "correspondence")
        used.add(triangle)
        rotation = rotations[0]
        for comparison_corner, raw_corner in enumerate((0, 2, 1)):
            source_corner = (comparison_corner + rotation) % 3
            rows.append([offset // 3, raw_corner, raw_indices[raw_corner],
                         *source["keys"][source_corner], source["vertices"][source_corner]])
    require(len(used) == len(source_triangles), "MISSING_CORRESPONDENCE", "Source triangles remain unmatched", "correspondence")
    return sorted(rows, key=lambda row: (row[0], row[1]))


def validate_observations(observation, authority):
    """Internal structural/correspondence seam, NOT an authority-admission API."""
    fields(observation, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256",
                         "coordinate_system", "parts"), "Observation")
    require(observation["schema"] == SCHEMA, "SCHEMA", "Unsupported observation schema")
    require(observation["declared_origin"] in ("synthetic", "unattested-native"), "SCHEMA", "Unsupported declared origin")
    require(observation["accepted_program_revision"] == c221.ACCEPTED_REVISION and
            observation["glb_sha256"] == authority["glb_sha256"], "IDENTITY", "Observation source/artifact claim differs")
    require(c221.canonical(observation["coordinate_system"]) == c221.canonical(COORDINATE_SYSTEM),
            "COORDINATES", "Only declared metre/identity-basis/reverse-once winding is supported")
    parts = observation["parts"]
    require(type(parts) is list and len(parts) == 18, "COUNT", "Exactly 18 part observations required")
    nodes, native_ids, checked_surfaces, labels = set(), set(), [], []
    vertex_count, triangle_count = 0, 0
    for part in parts:
        fields(part, ("gltf_node", "gltf_mesh", "element_id", "source_path", "native_node_id",
                      "display_name", "surfaces"), "Part")
        node, mesh = integer(part["gltf_node"], "glTF node"), integer(part["gltf_mesh"], "glTF mesh")
        require(node in authority["parts"] and node not in nodes, "IDENTITY", "Unexpected or duplicate glTF node")
        nodes.add(node)
        expected = authority["parts"][node]
        planned = expected["planned"]
        require(mesh == planned["glbMesh"] and part["source_path"] == planned["sourcePath"] and
                c221.canonical(part["element_id"]) == c221.canonical(planned["elementId"]),
                "IDENTITY", "Part source identity does not agree with node/mesh")
        native_id = text_value(part["native_node_id"], "Native node label")
        require(native_id not in native_ids, "IDENTITY", "Duplicate native node label")
        native_ids.add(native_id)
        require(type(part["display_name"]) is str and len(part["display_name"]) <= 4096,
                "TEXT", "Display name must be bounded text")
        labels.append({"gltf_node": node, "native_node_id": native_id, "display_name": part["display_name"]})
        surfaces = part["surfaces"]
        require(type(surfaces) is list and len(surfaces) == len(expected["surfaces"]),
                "COUNT", "Complete primitive surface inventory required")
        primitives = set()
        for surface in surfaces:
            fields(surface, ("gltf_primitive", "material_index", "positions", "normals", "indices"), "Surface")
            primitive = integer(surface["gltf_primitive"], "glTF primitive")
            material = integer(surface["material_index"], "Material index")
            require(primitive in expected["surfaces"] and primitive not in primitives,
                    "IDENTITY", "Unexpected or duplicate primitive")
            primitives.add(primitive)
            source = expected["surfaces"][primitive]
            require(material == source["material"], "MATERIAL_BINDING", "Declared primitive material index differs")
            expected_corners = len(source["triangles"]) * 3
            positions, normals, indices = surface["positions"], surface["normals"], surface["indices"]
            require(type(positions) is list and 0 < len(positions) <= expected_corners,
                    "COUNT", "Observed vertex count is outside finite surface bounds")
            require(type(normals) is list and len(normals) == len(positions), "COUNT", "Complete normal array required")
            for values in positions:
                vector(values, "Observed position")
            for values in normals:
                vector(values, "Observed normal")
            require(type(indices) is list and len(indices) == expected_corners, "COUNT", "Complete triangle-index array required")
            for index in indices:
                require(integer(index, "Raw vertex index") < len(positions), "INDEX", "Raw vertex index out of range")
            require(set(indices) == set(range(len(positions))), "EXTRA_GEOMETRY", "Unreferenced observed vertex")
            vertex_count += len(positions)
            triangle_count += len(indices) // 3
            checked_surfaces.append((node, primitive, source["triangles"], surface))
    require(nodes == set(authority["parts"]), "IDENTITY", "Incomplete source-part inventory")
    require(triangle_count == 7800, "COUNT", "Unexpected complete triangle inventory")
    mapping = []
    for node, primitive, source_triangles, surface in sorted(checked_surfaces):
        mapping.extend([[node, primitive, *row] for row in _match_surface(source_triangles, surface)])
    require(len(mapping) == 23400, "COUNT", "Incomplete corner inventory", "correspondence")
    return {"structure": {"result": "PASS_OBSERVATION_STRUCTURE", "parts": len(nodes),
                          "surfaces": len(checked_surfaces), "vertices": vertex_count,
                          "triangles": triangle_count, "corners": len(mapping)},
            "correspondence": {"result": "PASS_EXACT_CORNER_CORRESPONDENCE",
                               "corner_map_fields": MAP_FIELDS, "corner_map": mapping,
                               "corner_map_sha256": c221.digest(c221.canonical(mapping))},
            "untrusted_observation_labels": sorted(labels, key=lambda row: row["gltf_node"])}


def check_observations(package_root, observation_path):
    authority = _load_authority(package_root)
    raw = _read_observation(observation_path)
    try:
        observation = c221.strict_json(raw, "Observation")
        result = validate_observations(observation, authority)
    except c221.CheckError as exc:
        raise CheckError(exc.code, str(exc), "observation_schema") from exc
    return {"schema": REPORT_SCHEMA, "version": VERSION, "result": "PASS_CPU_CORRESPONDENCE",
            "admission": authority["admission"], "observation_bytes": len(raw),
            "observation_sha256": c221.digest(raw), "declared_origin": observation["declared_origin"],
            **result, "limits": {"target_starts": 0, "source_evaluations": 0, "exports": 0,
                                 "imports": 0, "renders": 0, "scene_writes": 0,
                                 "native_receiving_evidence": False, "native_mapping_attested": False,
                                 "normal_values_compared": False, "material_values_compared": False,
                                 "poses_compared": False, "target_execution_authorized": False,
                                 "meaning": "Exact CPU correspondence of untrusted observations; no native acceptance or provenance"}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--observations", required=True)
    args = parser.parse_args(argv)
    try:
        result = check_observations(args.package_root, args.observations)
    except (CheckError, c221.CheckError, OSError) as exc:
        result = {"schema": REPORT_SCHEMA, "version": VERSION, "result": "FAIL_CLOSED",
                  "error": {"code": getattr(exc, "code", "IO"), "stage": getattr(exc, "stage", "io"),
                            "message": str(exc)}, "target_execution_authorized": False}
        print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
