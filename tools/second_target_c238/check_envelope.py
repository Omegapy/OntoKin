#!/usr/bin/env python3
"""Admit one finite set of exact observation bytes without component validation."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys

sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location(
    "ontokin_c238_authority", Path(__file__).absolute().parents[1] / "second_target_c221/check_bindings.py")
c221 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(c221)

VERSION = "C238/0.1.0"
SCHEMA = "ontokin.c238.observation-envelope/0.1"
REPORT_SCHEMA = "ontokin.c238.envelope-admission/0.1"
MAP_SCHEMA = "ontokin.c238.declared-corner-map/0.1"
MIB = 1024 * 1024
ROLE_SPECS = {
    "geometry": ("ontokin.c222.geometry-observations/0.1", 16 * MIB),
    "materials": ("ontokin.c234.material-observations/0.1", 256 * 1024),
    "normals": ("ontokin.c235.normal-observations/0.1", 16 * MIB),
    "poses": ("ontokin.c236.pose-observations/0.1", MIB),
    "semantics": ("ontokin.second-target.c237.observations/0.1", 4 * MIB),
    "corner_map": (MAP_SCHEMA, 4 * MIB),
}
SOURCE_FIELDS = ("gltf_node", "gltf_mesh", "element_id", "definition_id", "source_path")
PART_FIELDS = (*SOURCE_FIELDS, "native_node_id")
MAP_FIELDS = ["gltf_node", "gltf_primitive", "raw_triangle", "raw_corner", "raw_vertex",
              "source_mesh", "source_primitive", "source_triangle", "source_corner", "source_vertex"]
TIMES = ("0", "0.25", "0.5", "0.75", "1", "1.5", "2")
GEOMETRY_COORDINATES = {"position_unit": "m", "basis": "gltf-rh-y-up-identity",
                        "winding": "godot-clockwise-reverse-once"}
POSE_COORDINATES = {"position_unit": "m", "time_unit": "s", "basis": "gltf-rh-y-up-identity",
                   "quaternion_order": "wxyz", "matrix_layout": "row-major-4x4"}
NORMAL_FRAME = "gltf-object-local-right-handed-y-up"
DESCRIPTIVE = ("imported_native", "independently_derived", "observer_copied", "retained_external")
COPIED = ("observer_copied", "retained_external")
FEATURE_RULES = {
    "source_closure": (("retained_external",), "retained_source"),
    "stable_identities": (DESCRIPTIVE, "descriptive_metadata"),
    "dimensions_units_frames": (DESCRIPTIVE, "descriptive_metadata"),
    "ownership": (COPIED, "descriptive_metadata"),
    "following": (COPIED, "descriptive_metadata"),
    "hinge_constraints": (COPIED, "descriptive_metadata"),
    "physical_declarations": (COPIED, "descriptive_metadata"),
    "materials": (DESCRIPTIVE, "descriptive_metadata"),
    "primitive_geometry": (DESCRIPTIVE, "approximated_representation"),
    "world_motion": (DESCRIPTIVE, "baked_playback"),
    "numeric_precision": (DESCRIPTIVE, "approximated_representation"),
    "action_execution": (("unsupported",), "unsupported"),
    "live_physics": (("unsupported",), "unsupported"),
    "source_reconstruction": (("unsupported",), "unsupported"),
}
RETAINED_KINDS = ("program_bundle", "glb", "semantic_sidecar", "source_normal_payload")
STAGES = ("authority", "source", "envelope", "members", "identities", "geometry",
          "corner_map", "materials", "normals", "poses", "semantics", "snapshot")
STAT_FIELDS = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")


class CheckError(ValueError):
    def __init__(self, code, message, report=None):
        super().__init__(message)
        self.code = code
        self.report = report


def _require(condition, code, message):
    if not condition:
        raise CheckError(code, message)


def _fields(value, fields, label):
    _require(type(value) is dict and set(value) == set(fields), "SCHEMA", label + ": exact fields required")


def _integer(value, label, minimum=0):
    _require(type(value) is int and value >= minimum, "INDEX", label + ": integer required")
    return value


def _text(value, label, maximum=4096, empty=False):
    _require(type(value) is str and "\x00" not in value, "TEXT", label + ": text without NUL required")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise CheckError("JSON", label + ": invalid Unicode") from exc
    _require((empty or size > 0) and size <= maximum, "TEXT", label + ": text exceeds bounds")
    return value


def _number(value, label):
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    _require(valid, "FINITE", label + ": finite non-Boolean number required")
    return value


def _vector(value, count, label):
    _require(type(value) is list and len(value) == count, "VECTOR", label + ": wrong component count")
    for item in value:
        _number(item, label)
    return value


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _equal(actual, expected, code, label):
    _require(_canonical(actual) == _canonical(expected), code, label + ": differs")


def _json(raw, label, max_values=1000000):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "JSON", label + ": duplicate key")
            result[key] = value
        return result

    def nonfinite(_):
        raise CheckError("JSON", label + ": nonfinite token")

    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
        pending, count = [(result, 0)], 0
        while pending:
            value, depth = pending.pop()
            count += 1
            _require(count <= max_values and depth <= 64, "JSON_BOUNDS", label + ": JSON value/depth limit")
            if type(value) is dict:
                for key, child in value.items():
                    _require(len(key.encode("utf-8")) <= MIB, "JSON_BOUNDS", label + ": oversized key")
                    pending.append((child, depth + 1))
            elif type(value) is list:
                pending.extend((child, depth + 1) for child in value)
            elif type(value) is str:
                _require(len(value.encode("utf-8")) <= MIB, "JSON_BOUNDS", label + ": oversized string")
            elif type(value) is float:
                _require(math.isfinite(value), "JSON", label + ": nonfinite number")
        return result
    except (UnicodeError, ValueError, RecursionError) as exc:
        if isinstance(exc, CheckError):
            raise
        raise CheckError("JSON", label + ": malformed bounded UTF-8 JSON") from exc


def _stat_key(value):
    return tuple(getattr(value, name) for name in STAT_FIELDS)


class _Snapshot:
    """Hold inspected descriptors and check all names again at transaction end."""

    def __init__(self, envelope_path):
        self.entries = []
        self.root = None
        supplied = os.fspath(envelope_path)
        _require(type(supplied) is str and supplied and "\\" not in supplied and "\x00" not in supplied,
                 "PATH", "Invalid envelope path")
        parts = supplied.split("/")
        _require(all(part not in ("", ".", "..") for part in (parts[1:] if supplied.startswith("/") else parts)),
                 "PATH", "Empty, dot or traversal path component")
        absolute = Path(os.path.abspath(supplied))
        self.envelope_name = absolute.name
        self.root = c221.SafeRoot(absolute.parent)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for entry in self.entries:
            os.close(entry["fd"])
        if self.root is not None:
            self.root.__exit__()

    def read(self, name, ceiling, expected=None, role="envelope"):
        fd = None
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.root.fd)
            before = os.fstat(fd)
            _require(stat.S_ISREG(before.st_mode), "FILE", role + ": regular file required")
            _require(0 < before.st_size <= ceiling, "SIZE", role + ": file exceeds byte limit")
            if expected is not None:
                _require(before.st_size == expected["bytes"], "MEMBER_BINDING", role + ": declared length differs")
            _require(all((before.st_dev, before.st_ino) != entry["identity"] for entry in self.entries),
                     "ALIAS", role + ": file aliases another admitted input")
            entry = {"fd": fd, "name": name, "before": _stat_key(before),
                     "identity": (before.st_dev, before.st_ino), "role": role}
            self.entries.append(entry)
            fd = None
            chunks, remaining = [], min(before.st_size + 1, ceiling + 1)
            while remaining:
                chunk = os.read(entry["fd"], min(1024 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            _require(entry["before"] == _stat_key(os.fstat(entry["fd"])), "CHANGED", role + ": changed during read")
            _require(len(raw) == before.st_size, "CHANGED", role + ": short or growing read")
            binding = {"bytes": len(raw), "sha256": _digest(raw)}
            if expected is not None:
                _require(binding["sha256"] == expected["sha256"], "MEMBER_BINDING", role + ": declared digest differs")
            return raw, binding
        except FileNotFoundError as exc:
            raise CheckError("MISSING_MEMBER", role + ": file is absent") from exc
        except OSError as exc:
            raise CheckError("FILE", role + ": unsafe or unreadable file") from exc
        finally:
            if fd is not None:
                os.close(fd)

    def finish(self):
        for entry in self.entries:
            try:
                descriptor = os.fstat(entry["fd"])
                named = os.stat(entry["name"], dir_fd=self.root.fd, follow_symlinks=False)
            except OSError as exc:
                raise CheckError("CHANGED", entry["role"] + ": final name/descriptor unavailable") from exc
            _require(entry["before"] == _stat_key(descriptor) == _stat_key(named),
                     "CHANGED", entry["role"] + ": descriptor or directory entry changed")
        return {"result": "PASS_INSPECTED_SNAPSHOT", "files": len(self.entries),
                "distinct_inodes": len(self.entries), "post_return_immutability": False}


def _source(package_root):
    bindings, part_map = c221.load_authority()
    pins = {row["packagePath"]: row for row in bindings["items"]}
    values = {}
    with c221.SafeRoot(package_root) as root:
        for index in (0, 2, 3):
            path = c221.INPUT_PATHS[index]
            pin = pins[path]
            values[index] = root.read(path, pin["bytes"], pin["sha256"], pin["mode"])
    glb, binary = c221.decode_glb(values[0])
    payload = c221.strict_json(values[3], "Pinned C214 payload")
    semantic = c221.strict_json(values[2], "Pinned semantics")
    parts = {}
    for row in part_map["entries"]:
        node = row["glbNode"]
        parts[node] = dict(zip(SOURCE_FIELDS, (node, row["glbMesh"], row["elementId"],
                                              row["definitionId"], row["sourcePath"])))
    corners = {}
    for row in payload["corners"]:
        key = tuple(row["key"])
        _require(len(key) == 4 and key not in corners, "SOURCE", "Pinned source corner inventory differs")
        corners[key] = row["vertex"]
    surfaces = {}
    for node, part in parts.items():
        mesh = part["gltf_mesh"]
        for primitive, raw in enumerate(glb["meshes"][mesh]["primitives"]):
            meta, data = c221._accessor(glb, binary, raw["indices"])
            _require(meta["component_type"] == 5123 and meta["type"] == "SCALAR",
                     "SOURCE", "Unexpected source index representation")
            indices = [item[0] for item in struct.iter_unpack("<H", data)]
            _require(len(indices) % 3 == 0, "SOURCE", "Incomplete source triangles")
            for offset, vertex in enumerate(indices):
                key = (mesh, primitive, offset // 3, offset % 3)
                _require(corners.get(key) == vertex, "SOURCE", "Pinned C214 corner/vertex differs from GLB")
            surfaces[(node, primitive)] = {"material": raw["material"], "corners": len(indices),
                                          "source_mesh": mesh, "source_vertices": indices}
    _require(len(parts) == 18 and len(corners) == 3024 and sum(r["corners"] for r in surfaces.values()) == 23400,
             "SOURCE", "Finite source inventory differs")
    return {"parts": parts, "surfaces": surfaces, "corners": corners, "semantic": semantic,
            "glb_sha256": pins[c221.INPUT_PATHS[0]]["sha256"],
            "pins": [pins[c221.INPUT_PATHS[index]] for index in (0, 2, 3)]}


def _keyed(rows, key, expected, label):
    _require(type(rows) is list and len(rows) == len(expected), "COUNT", label + ": incomplete inventory")
    result = {}
    for row in rows:
        _require(type(row) is dict and key in row, "SCHEMA", label + ": missing identity field")
        value = row[key]
        _require(type(value) in (int, str), "IDENTITY", label + ": invalid identity type")
        _require(value in expected and value not in result, "IDENTITY", label + ": duplicate or unknown identity")
        result[value] = row
    _require(set(result) == set(expected), "IDENTITY", label + ": incomplete identity set")
    return result


def _envelope(value, source, envelope_name):
    _fields(value, ("schema", "capture", "authority", "parts", "members"), "Envelope")
    _require(value["schema"] == SCHEMA, "SCHEMA", "Unsupported envelope schema")
    _fields(value["capture"], ("kind", "label"), "Capture")
    _require(value["capture"]["kind"] in ("synthetic", "unattested-native"), "PROVENANCE", "Unknown capture kind")
    _text(value["capture"]["label"], "Capture label", 256)
    _fields(value["authority"], ("accepted_program_revision", "glb_sha256"), "Authority declaration")
    _equal(value["authority"], {"accepted_program_revision": c221.ACCEPTED_REVISION,
                               "glb_sha256": source["glb_sha256"]}, "IDENTITY", "Envelope authority")
    parts = _keyed(value["parts"], "gltf_node", source["parts"], "Envelope parts")
    labels = set()
    for node, part in parts.items():
        _fields(part, PART_FIELDS, "Envelope part")
        _integer(part["gltf_node"], "Node")
        _integer(part["gltf_mesh"], "Mesh")
        _equal({name: part[name] for name in SOURCE_FIELDS}, source["parts"][node], "IDENTITY", "Full part mapping")
        label = _text(part["native_node_id"], "Native label")
        _require(label not in labels, "IDENTITY", "Duplicate native label")
        labels.add(label)
    members = _keyed(value["members"], "role", ROLE_SPECS, "Members")
    paths, total = {envelope_name}, 0
    for role, member in members.items():
        _fields(member, ("role", "path", "schema", "bytes", "sha256"), "Member descriptor")
        schema, ceiling = ROLE_SPECS[role]
        _require(member["schema"] == schema, "SCHEMA", role + ": unsupported declared schema")
        path = member["path"]
        _require(type(path) is str and NAME.fullmatch(path) is not None and path not in paths,
                 "PATH", role + ": unsafe or duplicate member path")
        paths.add(path)
        size = _integer(member["bytes"], "Member length", 1)
        _require(size <= ceiling, "SIZE", role + ": declared length exceeds limit")
        _require(type(member["sha256"]) is str and HEX.fullmatch(member["sha256"]) is not None,
                 "MEMBER_BINDING", role + ": malformed SHA-256")
        total += size
    return parts, members, total


def _common(value, fields, role, envelope, source):
    _fields(value, fields, role)
    _require(value["schema"] == ROLE_SPECS[role][0], "SCHEMA", role + ": unsupported raw schema")
    _equal(value["accepted_program_revision"], c221.ACCEPTED_REVISION, "IDENTITY", role + ": source revision")
    _equal(value["glb_sha256"], source["glb_sha256"], "IDENTITY", role + ": source artifact")
    _equal(value["declared_origin"], envelope["capture"]["kind"], "PROVENANCE", role + ": mixed declared origin")


def _part_projection(rows, role, parts, fields, definitions=False, semantic=False):
    key = "sourceNode" if semantic else "gltf_node"
    result = _keyed(rows, key, parts, role + " parts")
    report = []
    renames = dict(zip(SOURCE_FIELDS, ("sourceNode", "sourceMesh", "elementId", "definitionId", "sourcePath"))) if semantic else {}
    selected = SOURCE_FIELDS if definitions or semantic else tuple(name for name in SOURCE_FIELDS if name != "definition_id")
    for node in sorted(result):
        row, expected = result[node], parts[node]
        _fields(row, fields, role + " part")
        for name in selected:
            _equal(row[renames.get(name, name)], expected[name], "IDENTITY", role + ": " + name)
        native_field = "destinationLabel" if semantic else "native_node_id"
        _equal(row[native_field], expected["native_node_id"], "IDENTITY", role + ": native label")
        report.append({"gltf_node": node, "declared_fields": {name: row[renames.get(name, name)] for name in selected},
                       "authority_derived_fields": {} if "definition_id" in selected else {"definition_id": expected["definition_id"]},
                       "native_node_id": row[native_field], "native_mapping_attested": False})
    return result, report


def _geometry(value, parts, source, envelope):
    _common(value, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256", "coordinate_system", "parts"),
            "geometry", envelope, source)
    _equal(value["coordinate_system"], GEOMETRY_COORDINATES, "SCHEMA", "Geometry coordinates")
    by_node, projection = _part_projection(value["parts"], "geometry", parts,
        ("gltf_node", "gltf_mesh", "element_id", "source_path", "native_node_id", "display_name", "surfaces"))
    surfaces, raw_keys, vertices = {}, set(), 0
    for node, part in by_node.items():
        _require(type(part["display_name"]) is str and len(part["display_name"]) <= 4096,
                 "TEXT", "Display name must retain the C222 character-count domain")
        expected = {primitive for n, primitive in source["surfaces"] if n == node}
        rows = _keyed(part["surfaces"], "gltf_primitive", expected, "Geometry surfaces")
        for primitive, row in rows.items():
            _fields(row, ("gltf_primitive", "material_index", "positions", "normals", "indices"), "Geometry surface")
            _integer(row["gltf_primitive"], "Primitive")
            planned = source["surfaces"][(node, primitive)]
            _equal(row["material_index"], planned["material"], "IDENTITY", "Geometry material")
            positions, normals, indices = row["positions"], row["normals"], row["indices"]
            _require(type(positions) is list and 0 < len(positions) <= planned["corners"], "COUNT", "Geometry vertex inventory")
            _require(type(normals) is list and len(normals) == len(positions), "COUNT", "Geometry normal inventory")
            for vector in positions + normals:
                _vector(vector, 3, "Geometry vector")
            _require(type(indices) is list and len(indices) == planned["corners"], "COUNT", "Geometry corner inventory")
            for offset, vertex in enumerate(indices):
                _require(_integer(vertex, "Raw vertex") < len(positions), "INDEX", "Raw vertex out of bounds")
                raw_keys.add((node, primitive, offset // 3, offset % 3, vertex))
            _require(set(indices) == set(range(len(positions))), "COUNT", "Unreferenced geometry vertex")
            vertices += len(positions)
            surfaces[(node, primitive)] = row
    _require(len(raw_keys) == 23400, "COUNT", "Incomplete raw corner inventory")
    return surfaces, raw_keys, {"parts": 18, "surfaces": len(surfaces), "vertices": vertices,
                                "triangles": 7800, "corners": 23400, "part_projections": projection}


def _dependency(value, expected, label, extra=None):
    fields = ("bytes", "sha256") if extra is None else ("bytes", "sha256", "corner_map_sha256")
    _fields(value, fields, label)
    _integer(value["bytes"], label + " length", 1)
    target = dict(expected)
    if extra is not None:
        target["corner_map_sha256"] = extra
    _equal(value, target, "DEPENDENCY", label)
    return {"declared": value, "inspected": target, "equal": True}


def _corner_map(value, parts, source, envelope, bindings, surfaces, raw_keys):
    _common(value, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256",
                    "geometry_observation", "corner_map_fields", "corner_map"), "corner_map", envelope, source)
    dependency = _dependency(value["geometry_observation"], bindings["geometry"], "Corner-map geometry")
    _equal(value["corner_map_fields"], MAP_FIELDS, "SCHEMA", "Corner-map fields")
    rows = value["corner_map"]
    _require(type(rows) is list and len(rows) == 23400, "COUNT", "Complete declared map required")
    seen_raw, seen_source, previous, triangles = set(), set(), None, {}
    for row in rows:
        _require(type(row) is list and len(row) == 10, "SCHEMA", "Ten fields per map row required")
        for integer in row:
            _integer(integer, "Map field")
        raw, source_key = tuple(row[:5]), tuple(row[5:9])
        _require(raw in raw_keys and raw not in seen_raw and (previous is None or previous < raw),
                 "CORNER_IDENTITY", "Unknown, duplicated or unsorted raw map corner")
        previous = raw
        seen_raw.add(raw)
        node, primitive, triangle, corner, _ = raw
        _require(source_key[0] == parts[node]["gltf_mesh"] and source_key[1] == primitive and
                 source["corners"].get(source_key) == row[9],
                 "CORNER_IDENTITY", "Declared source corner/vertex does not match admitted inventory")
        source_instance = (node, *source_key)
        _require(source_instance not in seen_source, "CORNER_IDENTITY", "Repeated per-part source corner")
        seen_source.add(source_instance)
        triangles.setdefault((node, primitive, triangle), {})[corner] = (row[7], row[8])
    expected_source = {(node, mesh, primitive, triangle, corner)
                       for node, part in parts.items()
                       for mesh, primitive, triangle, corner in source["corners"]
                       if mesh == part["gltf_mesh"]}
    _require(seen_raw == raw_keys and seen_source == expected_source, "CORNER_IDENTITY", "Incomplete map coverage")
    for corners in triangles.values():
        _require(set(corners) == {0, 1, 2} and len({r[0] for r in corners.values()}) == 1,
                 "WINDING", "Raw triangle spans incompatible source triangles")
        start = corners[0][1]
        _require(corners[2][1] == (start + 1) % 3 and corners[1][1] == (start + 2) % 3,
                 "WINDING", "Declared winding is not reverse-once with a cycle")
    return {"parts": 18, "corners": len(rows), "triangles": len(triangles), "corner_map_fields": MAP_FIELDS,
            "corner_map": rows, "corner_map_sha256": _digest(_canonical(rows)),
            "geometric_correspondence": "NOT_RUN", "producer_declaration_attested": False}, dependency


def _materials(value, parts, source, envelope, bindings):
    _common(value, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256",
                    "geometry_observation", "parts"), "materials", envelope, source)
    dependency = _dependency(value["geometry_observation"], bindings["geometry"], "Material geometry")
    by_node, projection = _part_projection(value["parts"], "materials", parts,
        ("gltf_node", "gltf_mesh", "element_id", "source_path", "native_node_id", "surfaces"))
    resources, associations = {}, []
    for node, part in by_node.items():
        expected = {primitive for n, primitive in source["surfaces"] if n == node}
        rows = _keyed(part["surfaces"], "gltf_primitive", expected, "Material surfaces")
        for primitive, row in rows.items():
            _fields(row, ("gltf_primitive", "material_index", "native_material_id", "raw"), "Material surface")
            _integer(row["gltf_primitive"], "Primitive")
            material = source["surfaces"][(node, primitive)]["material"]
            _equal(row["material_index"], material, "IDENTITY", "Material association")
            resource = row["native_material_id"]
            _require(type(resource) is str and 0 < len(resource) <= 4096 and "\x00" not in resource,
                     "TEXT", "Material label must retain the C234 character-count domain")
            raw = row["raw"]
            _fields(raw, ("albedo_storage", "albedo_rgb", "alpha", "metallic", "roughness",
                          "cull_mode", "transparency_mode"), "Raw material")
            _require(raw["albedo_storage"] == "srgb-rgb-linear-alpha", "SCHEMA", "Unsupported color storage")
            rgb = _vector(raw["albedo_rgb"], 3, "Albedo")
            for number in [*rgb, raw["alpha"], raw["metallic"], raw["roughness"]]:
                _require(0 <= _number(number, "Material parameter") <= 1, "PARAMETER", "Parameter outside unit interval")
            _require(raw["cull_mode"] in ("back", "front", "disabled") and
                     raw["transparency_mode"] in ("disabled", "alpha", "alpha-scissor"), "SCHEMA", "Unknown material mode")
            association = (material, _canonical(raw))
            _require(resource not in resources or resources[resource] == association,
                     "RESOURCE_BINDING", "One resource has contradictory declarations")
            resources[resource] = association
            associations.append({"gltf_node": node, "gltf_primitive": primitive,
                                 "material_index": material, "native_material_id": resource, "raw": raw})
    return {"parts": 18, "surface_associations": len(associations), "source_materials": 2,
            "part_projections": projection, "associations": sorted(associations, key=lambda r: (r["gltf_node"], r["gltf_primitive"]))}, dependency


def _normals(value, source, envelope, bindings, surfaces, raw_keys, mapping):
    _common(value, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256", "normal_frame",
                    "geometry_observation", "records"), "normals", envelope, source)
    _require(value["normal_frame"] == NORMAL_FRAME, "SCHEMA", "Unsupported normal frame")
    dependency = _dependency(value["geometry_observation"], bindings["geometry"],
                             "Normal geometry/map", mapping["corner_map_sha256"])
    rows = value["records"]
    _require(type(rows) is list and len(rows) == 23400, "COUNT", "Complete normal records required")
    seen = set()
    for row in rows:
        _fields(row, ("key", "normal"), "Normal record")
        key = row["key"]
        _require(type(key) is list and len(key) == 5, "SCHEMA", "Five normal key fields required")
        for value in key:
            _integer(value, "Normal key")
        key = tuple(key)
        _require(key in raw_keys and key not in seen, "CORNER_IDENTITY", "Unknown or duplicate normal corner")
        seen.add(key)
        normal = _vector(row["normal"], 3, "Raw normal")
        _require(any(v != 0 for v in normal), "VECTOR", "Nonzero normal required")
        _equal(normal, surfaces[key[:2]]["normals"][key[4]], "RAW_NORMAL_BINDING", "Copied normal")
    _require(seen == raw_keys, "CORNER_IDENTITY", "Incomplete normal corner coverage")
    return {"parts": 18, "corners": len(rows), "raw_geometry_consistency": "EXACT_TYPED_CANONICAL_EQUALITY"}, dependency


def _poses(value, parts, source, envelope):
    _common(value, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256",
                    "coordinate_system", "parts"), "poses", envelope, source)
    _equal(value["coordinate_system"], POSE_COORDINATES, "SCHEMA", "Pose coordinates")
    by_node, projection = _part_projection(value["parts"], "poses", parts,
        ("gltf_node", "gltf_mesh", "element_id", "definition_id", "source_path", "native_node_id", "samples"), definitions=True)
    slots = []
    for node, part in by_node.items():
        samples = _keyed(part["samples"], "reference_time_seconds", TIMES, "Pose slots")
        for time, sample in samples.items():
            _fields(sample, ("reference_time_seconds", "observed_time_seconds", "translation_m",
                             "rotation_wxyz", "scale", "world_matrix"), "Pose sample")
            _number(sample["observed_time_seconds"], "Observed time")
            _vector(sample["translation_m"], 3, "Translation")
            quaternion = _vector(sample["rotation_wxyz"], 4, "Quaternion")
            _require(any(v != 0 for v in quaternion), "VECTOR", "Zero quaternion")
            scales = _vector(sample["scale"], 3, "Scale")
            _require(all(v > 0 for v in scales), "VECTOR", "Nonpositive scale")
            _vector(sample["world_matrix"], 16, "World matrix")
            slots.append({"gltf_node": node, "reference_time_seconds": time})
    return {"parts": 18, "samples": len(slots), "sample_times": list(TIMES), "part_projections": projection,
            "slots": sorted(slots, key=lambda r: (r["gltf_node"], TIMES.index(r["reference_time_seconds"]))),
            "matrix_consistency": "NOT_RUN"}


def _same_shape(expected, actual, label):
    _require(type(actual) is type(expected), "SCHEMA", label + ": JSON type differs")
    if type(expected) is dict:
        _fields(actual, expected, label)
        for key in expected:
            _same_shape(expected[key], actual[key], label + "/" + key)
    elif type(expected) is list:
        _require(len(actual) == len(expected), "COUNT", label + ": list length differs")
        for index, (a, b) in enumerate(zip(expected, actual)):
            _same_shape(a, b, label + "/" + str(index))


def _semantics(value, parts, source, envelope):
    _fields(value, ("schema", "producer", "programRevision", "parts", "semantics", "features", "retainedFiles", "capabilities"),
            "Semantics")
    _require(value["schema"] == ROLE_SPECS["semantics"][0], "SCHEMA", "Unsupported semantic schema")
    _equal(value["programRevision"], c221.ACCEPTED_REVISION, "IDENTITY", "Semantic source revision")
    _fields(value["producer"], ("kind", "name"), "Semantic producer")
    expected_kind = "synthetic" if envelope["capture"]["kind"] == "synthetic" else "declared_destination"
    _equal(value["producer"]["kind"], expected_kind, "PROVENANCE", "Semantic producer origin")
    _require(type(value["producer"]["name"]) is str and bool(value["producer"]["name"]),
             "TEXT", "Semantic producer must retain the C237 nonempty-string domain")
    _, projection = _part_projection(value["parts"], "semantics", parts,
        ("sourceNode", "sourceMesh", "elementId", "definitionId", "sourcePath", "destinationLabel"), semantic=True)
    original = source["semantic"]
    _same_shape(original, value["semantics"], "/semantics")
    features = {row["feature"]: row for row in original["features"]}
    by_feature = _keyed(value["features"], "feature", features, "Semantic features")
    feature_rows = []
    for name, row in by_feature.items():
        _fields(row, ("feature", "treatment", "reason", "required", "provenance", "capability"), "Feature")
        _same_shape(features[name], {key: row[key] for key in features[name]}, "/features/" + name)
        origins, capability = FEATURE_RULES[name]
        _require(row["provenance"] in origins and row["capability"] == capability,
                 "PROVENANCE", "Unsupported feature provenance/capability")
        _require(features[name]["treatment"] != "unsupported" or row["treatment"] == "unsupported",
                 "PROVENANCE", "Unsupported feature cannot be upgraded")
        feature_rows.append(row)
    expected = {"liveFollowing": False, "liveHinges": False, "actionExecution": False,
                "livePhysics": False, "sourceReconstruction": False, "rigidBodyCount": 0,
                "controllerCount": 0, "representedBodyMassKg": 0.0,
                "motionAuthority": original["scene"]["motion_authority"]}
    _equal(value["capabilities"], expected, "PROVENANCE", "No-body capability profile")
    retained = _keyed(value["retainedFiles"], "kind", RETAINED_KINDS, "Retained files")
    decoded = []
    for kind, row in retained.items():
        _fields(row, ("kind", "base64"), "Retained file")
        _require(type(row["base64"]) is str, "ENCODING", "Retained payload must be base64 text")
        try:
            raw = base64.b64decode(row["base64"].encode("ascii"), validate=True)
        except (UnicodeError, ValueError, binascii.Error) as exc:
            raise CheckError("ENCODING", "Noncanonical retained base64") from exc
        _require(base64.b64encode(raw).decode("ascii") == row["base64"], "ENCODING", "Noncanonical retained base64")
        decoded.append({"kind": kind, "bytes": len(raw), "sha256": _digest(raw), "source_equality": "NOT_RUN"})
    return {"parts": 18, "features": len(feature_rows), "retained_files": len(decoded), "part_projections": projection,
            "producer": value["producer"], "feature_declarations": sorted(feature_rows, key=lambda r: r["feature"]),
            "capability_declarations": value["capabilities"], "decoded_retained_bindings": sorted(decoded, key=lambda r: r["kind"]),
            "semantic_equality": "NOT_RUN", "source_unit_inspection": "NOT_RUN"}


def _base_report():
    return {"schema": REPORT_SCHEMA, "version": VERSION, "result": "FAIL_CLOSED",
            "stages": {stage: "NOT_RUN" for stage in STAGES},
            "component_results": {name: "NOT_RUN" for name in ("C222", "C234", "C235", "C236", "C237")},
            "limits": {"geometric_correspondence": "NOT_RUN", "matrix_consistency": "NOT_RUN",
                       "semantic_equality": "NOT_RUN", "original_byte_retention": "NOT_RUN",
                       "native_receiving_evidence": False, "native_mapping_attested": False,
                       "source_execution": False, "native_execution": False, "aggregate_execution": False,
                       "target_execution_authorized": False, "full_r07_acceptance": False,
                       "target_starts": 0, "native_version_starts": 0, "source_evaluations": 0, "exports": 0,
                       "imports": 0, "renders": 0, "scene_writes": 0,
                       "meaning": "Exact byte and declared-identity/dependency admission only; component validators are NOT_RUN"}}


def check_envelope(package_root, envelope_path):
    """Public path: fresh authority, actual members, complete declared bindings."""
    report, stage = _base_report(), "authority"
    try:
        report["authority"] = c221.check_package(package_root)
        report["stages"][stage] = "PASS"
        stage = "source"
        source = _source(package_root)
        report["source_inventory"] = {"parts": 18, "source_corners": 3024,
                                      "instance_corners": 23400, "reread_pins": source["pins"]}
        report["stages"][stage] = "PASS"
        stage = "envelope"
        with _Snapshot(envelope_path) as snapshot:
            raw, report["envelope_binding"] = snapshot.read(snapshot.envelope_name, 64 * 1024)
            envelope = _json(raw, "Envelope", 10000)
            parts, descriptors, total = _envelope(envelope, source, snapshot.envelope_name)
            _require(total + len(raw) <= 42 * MIB, "SIZE", "Combined observation byte limit")
            report["capture_declaration"] = {**envelope["capture"], "attested": False}
            report["stages"][stage] = "PASS"
            stage = "members"
            values, bindings, member_rows = {}, {}, []
            report["members"] = member_rows
            for role, (schema, ceiling) in ROLE_SPECS.items():
                descriptor = descriptors[role]
                member_raw, binding = snapshot.read(descriptor["path"], ceiling, descriptor, role)
                row = {"role": role, "path": descriptor["path"], "schema": schema,
                       "declared_binding": {key: descriptor[key] for key in ("bytes", "sha256")},
                       "inspected_binding": binding, "equal": True, "schema_admission": "NOT_RUN",
                       "component_result": "NOT_RUN"}
                member_rows.append(row)
                values[role] = _json(member_raw, role, 100000 if role == "semantics" else 1000000)
                _require(type(values[role]) is dict and values[role].get("schema") == schema,
                         "SCHEMA", role + ": incompatible raw schema")
                row["schema_admission"] = "PASS_SCHEMA_ID_ONLY"
                bindings[role] = binding
            report["stages"][stage] = "PASS"
            stage = "identities"
            report["parts"] = [parts[node] for node in sorted(parts)]
            report["identity_stage_meaning"] = "Envelope full source identities only; member identity projections are checked in their separate stages"
            report["declared_origins"] = {role: (value["producer"] if role == "semantics" else value.get("declared_origin"))
                                          for role, value in values.items()}
            report["stages"][stage] = "PASS"
            stage = "geometry"
            surfaces, raw_keys, report["geometry_projection"] = _geometry(values["geometry"], parts, source, envelope)
            report["stages"][stage] = "PASS"
            stage = "corner_map"
            report["corner_map_projection"], map_dependency = _corner_map(
                values["corner_map"], parts, source, envelope, bindings, surfaces, raw_keys)
            report["stages"][stage] = "PASS"
            stage = "materials"
            report["material_projection"], material_dependency = _materials(values["materials"], parts, source, envelope, bindings)
            report["stages"][stage] = "PASS"
            stage = "normals"
            report["normal_projection"], normal_dependency = _normals(
                values["normals"], source, envelope, bindings, surfaces, raw_keys, report["corner_map_projection"])
            report["stages"][stage] = "PASS"
            stage = "poses"
            report["pose_projection"] = _poses(values["poses"], parts, source, envelope)
            report["stages"][stage] = "PASS"
            stage = "semantics"
            report["semantic_projection"] = _semantics(values["semantics"], parts, source, envelope)
            report["stages"][stage] = "PASS"
            report["dependencies"] = {"corner_map_geometry": map_dependency, "material_geometry": material_dependency,
                                      "normal_geometry_and_map": normal_dependency}
            stage = "snapshot"
            report["snapshot"] = snapshot.finish()
            report["stages"][stage] = "PASS"
        report["result"] = "PASS_CPU_ENVELOPE_ADMISSION"
        return report
    except (CheckError, c221.CheckError, OSError, TypeError, ValueError, KeyError, OverflowError, RecursionError) as exc:
        report["stages"][stage] = "FAIL_CLOSED"
        report["error"] = {"stage": stage, "code": getattr(exc, "code", "SHAPE"), "message": str(exc)}
        raise CheckError(report["error"]["code"], str(exc), report) from exc


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise CheckError("ARGUMENT", message)


def main(argv=None):
    parser = _ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--envelope", required=True)
    try:
        args = parser.parse_args(argv)
        result = check_envelope(args.package_root, args.envelope)
        code = 0
    except CheckError as exc:
        result = exc.report or _base_report()
        if exc.report is None:
            result["error"] = {"stage": "arguments", "code": exc.code, "message": str(exc)}
        code = 2 if exc.code == "ARGUMENT" else 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

