#!/usr/bin/env python3
"""Finite CPU normal-loss comparison after fresh authority and geometry checks.

Only check_normals is a public admission API. A numerical pass never attests
native capture or authorizes a destination application.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
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
    "ontokin_c235_geometry", Path(__file__).absolute().parents[1] / "second_target_c222/check_observations.py")
c222 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(c222)
c221 = c222.c221

VERSION = "C235/0.1.0"
SCHEMA = "ontokin.c235.normal-observations/0.1"
REPORT_SCHEMA = "ontokin.c235.normal-comparison/0.1"
NORMAL_FRAME = "gltf-object-local-right-handed-y-up"
MAX_NORMAL_OBSERVATION_BYTES = 16 * 1024 * 1024
COMPONENT_LIMIT = 0.000002
_EXACT_LIMIT = Fraction(1, 500000)
_CHANNELS = ("x", "y", "z")
_STAGES = ("admission", "geometry", "structure", "comparison")


class CheckError(ValueError):
    def __init__(self, code, message, stage="normal_structure", report=None):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.report = report


def require(condition, code, message, stage="normal_structure"):
    if not condition:
        raise CheckError(code, message, stage)


def _fields(value, expected, label):
    require(type(value) is dict and set(value) == set(expected), "SCHEMA", label + ": exact fields required")


def _integer(value, label):
    require(type(value) is int and value >= 0, "INDEX", label + ": nonnegative integer required")
    return value


def _vector(value, label, stage="normal_structure"):
    require(type(value) is list and len(value) == 3, "VECTOR", label + ": three components required", stage)
    for component in value:
        try:
            valid = type(component) in (int, float) and math.isfinite(component)
        except OverflowError:
            valid = False
        require(valid, "FINITE", label + ": finite non-bool numeric components required", stage)
    require(any(component != 0 for component in value), "ZERO_NORMAL", label + ": nonzero direction required", stage)
    return value


def _read_normal_observation(path):
    supplied = os.fspath(path)
    require(type(supplied) is str and "\x00" not in supplied and ".." not in supplied.split("/"),
            "PATH", "Unsafe normal observation path", "normal_read")
    absolute = Path(os.path.abspath(supplied))
    try:
        with c221.SafeRoot(absolute.parent) as parent:
            fd = os.open(absolute.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent.fd)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode), "FILE", "Normal observation must be a regular file", "normal_read")
                require(0 < before.st_size <= MAX_NORMAL_OBSERVATION_BYTES,
                        "SIZE", "Normal observation exceeds finite size bounds", "normal_read")
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
                        "CHANGED", "Normal observation changed while reading", "normal_read")
                return raw
            finally:
                os.close(fd)
    except (OSError, c221.CheckError) as exc:
        raise CheckError("FILE", "Missing, unsafe or unreadable normal observation", "normal_read") from exc


def _read_source(package_root):
    """Recheck original bytes and decode their normals; not an admission API."""
    bindings, part_map = c221.load_authority()
    with c221.SafeRoot(package_root) as package:
        values = {}
        for index in (0, 3):
            pin = bindings["items"][index]
            values[index] = package.read(pin["packagePath"], pin["bytes"], pin["sha256"], pin["mode"])
    glb, binary = c221.decode_glb(values[0])
    payload = c221.strict_json(values[3], "C214 source normal payload")
    require(payload["sourceFrame"] == NORMAL_FRAME, "SOURCE_NORMAL", "Unexpected source normal frame", "source_normals")
    normal_arrays, normals = {}, {}
    for corner in payload["corners"]:
        key = tuple(corner["key"])
        require(len(key) == 4 and all(type(v) is int and v >= 0 for v in key) and key not in normals,
                "SOURCE_NORMAL", "Invalid or duplicate source corner", "source_normals")
        mesh, primitive, _, _ = key
        if (mesh, primitive) not in normal_arrays:
            source_primitive = glb["meshes"][mesh]["primitives"][primitive]
            meta, raw_array = c221._accessor(glb, binary, source_primitive["attributes"]["NORMAL"])
            require(meta["component_type"] == 5126 and meta["type"] == "VEC3",
                    "SOURCE_NORMAL", "Source normal accessor must be binary32 VEC3", "source_normals")
            normal_arrays[(mesh, primitive)] = raw_array
        vertex = corner["vertex"]
        require(type(vertex) is int and vertex >= 0, "SOURCE_NORMAL", "Invalid source vertex", "source_normals")
        raw_normal = normal_arrays[(mesh, primitive)][vertex * 12:vertex * 12 + 12]
        require(len(raw_normal) == 12 and raw_normal.hex() == corner["normal_f32le"],
                "SOURCE_NORMAL", "C214 normal bytes differ from source GLB", "source_normals")
        source = list(struct.unpack("<3f", raw_normal))
        _vector(source, "Source normal", "source_normals")
        normals[key] = {"vertex": vertex, "normal_f32le": raw_normal.hex(), "normal": source}
    parts = {row["glbNode"]: row for row in part_map["entries"]}
    require(len(normals) == 3024 and len(parts) == 18, "SOURCE_NORMAL", "Incomplete source normal inventory", "source_normals")
    pin = bindings["items"][3]
    return {"normals": normals, "parts": parts, "glb_sha256": bindings["items"][0]["sha256"],
            "payload": {"bytes": len(values[3]), "sha256": c221.digest(values[3]), "package_path": pin["packagePath"],
                        "source_frame": payload["sourceFrame"], "source_corners": len(normals)}}


def _validate_structure(observation, geometry, geometry_report, authority):
    """Validate the redundant raw-corner view; supplied reports are not admission."""
    _fields(observation, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256",
                          "normal_frame", "geometry_observation", "records"), "Normal observation")
    require(observation["schema"] == SCHEMA, "SCHEMA", "Unsupported normal observation schema")
    require(type(observation["declared_origin"]) is str and observation["declared_origin"] in ("synthetic", "unattested-native") and
            observation["declared_origin"] == geometry["declared_origin"], "ORIGIN", "Normal origin must match bound geometry")
    require(observation["accepted_program_revision"] == c221.ACCEPTED_REVISION and observation["glb_sha256"] == authority["glb_sha256"],
            "IDENTITY", "Normal source/artifact claim differs")
    require(observation["normal_frame"] == NORMAL_FRAME, "NORMAL_FRAME", "Only the predeclared object-local identity basis is supported")
    binding = observation["geometry_observation"]
    _fields(binding, ("bytes", "sha256", "corner_map_sha256"), "Geometry and correspondence binding")
    require(_integer(binding["bytes"], "Geometry bytes") == geometry_report["observation_bytes"] and
            binding["sha256"] == geometry_report["observation_sha256"],
            "GEOMETRY_BINDING", "Normal observations do not bind the exact checked geometry bytes")
    correspondence = geometry_report["correspondence"]
    require(binding["corner_map_sha256"] == correspondence["corner_map_sha256"],
            "CORRESPONDENCE_BINDING", "Normal observations do not bind the complete checked corner map")
    mapping = correspondence["corner_map"]
    expected = {tuple(row[:5]): row for row in mapping}
    require(len(expected) == 23400, "COUNT", "Complete unique raw corner map required")
    records = observation["records"]
    require(type(records) is list and len(records) == len(expected), "COUNT", "Exactly 23,400 corner normals required")
    surfaces = {(part["gltf_node"], surface["gltf_primitive"]): surface
                for part in geometry["parts"] for surface in part["surfaces"]}
    observed = {}
    for record in records:
        _fields(record, ("key", "normal"), "Corner normal")
        key = record["key"]
        require(type(key) is list and len(key) == 5 and all(type(v) is int and v >= 0 for v in key),
                "INDEX", "Raw corner key needs five nonnegative integers")
        key = tuple(key)
        require(key in expected and key not in observed, "CORNER_IDENTITY", "Unknown or duplicate raw corner key")
        raw = _vector(record["normal"], "Observed raw normal")
        geometry_raw = surfaces[key[:2]]["normals"][key[4]]
        require(c221.canonical(raw) == c221.canonical(geometry_raw), "RAW_NORMAL_BINDING",
                "Corner normal copy differs from bound raw geometry normal")
        observed[key] = raw
    require(set(observed) == set(expected), "CORNER_IDENTITY", "Incomplete raw corner coverage")
    rows = []
    for mapped in mapping:
        raw_key, source_key = mapped[:5], mapped[5:9]
        source = authority["normals"].get(tuple(source_key))
        planned = authority["parts"][mapped[0]]
        require(source is not None and source["vertex"] == mapped[9] and source_key[0] == planned["glbMesh"],
                "SOURCE_NORMAL", "Mapped normal source/vertex association differs", "source_normals")
        rows.append({"raw_key": raw_key, "source_key": [mapped[0], *source_key], "source_vertex": mapped[9],
                     "source_normal_f32le": source["normal_f32le"], "raw_normal": observed[tuple(raw_key)],
                     "source_normal": source["normal"]})
    return {"result": "PASS_NORMAL_STRUCTURE", "parts": 18, "corners": len(rows),
            "normal_frame": NORMAL_FRAME, "raw_geometry_consistency": "EXACT_CANONICAL_EQUALITY"}, rows


def _unit(values):
    scale = max(abs(value) for value in values)
    scaled = [value / scale for value in values]
    length = math.hypot(*scaled)
    return [value / length for value in scaled]


def _angle_degrees(actual, expected):
    a, b = _unit(actual), _unit(expected)
    cross = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    dot = sum(x * y for x, y in zip(a, b))
    return math.degrees(math.atan2(math.hypot(*cross), dot))


def _within_tolerance(actual, expected):
    return abs(Fraction(actual) - Fraction(expected)) <= _EXACT_LIMIT


def _display(value):
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def _magnitude(values):
    result = math.hypot(*values)
    return result if math.isfinite(result) else None


def _compare(rows):
    """Internal measurement seam over already associated nonzero vectors."""
    results, failures, parts = [], [], {}
    maximum = Fraction(0)
    maximum_angle = 0.0
    for row in rows:
        raw, source = row["raw_normal"], row["source_normal"]
        exact_deltas = [Fraction(a) - Fraction(b) for a, b in zip(raw, source)]
        exact_errors = [abs(value) for value in exact_deltas]
        checks = [value <= _EXACT_LIMIT for value in exact_errors]
        failed = [channel for channel, passed in zip(_CHANNELS, checks) if not passed]
        angle = _angle_degrees(raw, source)
        raw_magnitude, source_magnitude = _magnitude(raw), _magnitude(source)
        deltas, errors = [_display(v) for v in exact_deltas], [_display(v) for v in exact_errors]
        results.append({**row, "component_delta": deltas, "absolute_errors": errors, "component_pass": checks,
                        "failed_components": failed, "angular_error_degrees": angle,
                        "raw_magnitude": raw_magnitude, "source_magnitude": source_magnitude,
                        "raw_magnitude_overflow": raw_magnitude is None, "source_magnitude_overflow": source_magnitude is None,
                        "error_display_overflow": [v is None for v in errors]})
        node = row["raw_key"][0]
        if node not in parts:
            parts[node] = {"gltf_node": node, "corners": 0, "components": 0, "passing_corners": 0,
                           "exceeding_corners": 0, "exceeding_components": 0,
                           "maximum_absolute_error_exact": Fraction(0), "maximum_angular_error_degrees": 0.0}
        part = parts[node]
        part["corners"] += 1
        part["components"] += 3
        part["passing_corners"] += not failed
        part["exceeding_corners"] += bool(failed)
        part["exceeding_components"] += len(failed)
        part["maximum_absolute_error_exact"] = max(part["maximum_absolute_error_exact"], *exact_errors)
        part["maximum_angular_error_degrees"] = max(part["maximum_angular_error_degrees"], angle)
        maximum = max(maximum, *exact_errors)
        maximum_angle = max(maximum_angle, angle)
        if failed:
            failures.append({"raw_key": row["raw_key"], "source_key": row["source_key"], "failed_components": failed})
    part_rows = []
    for node in sorted(parts):
        part = parts[node]
        exact = part["maximum_absolute_error_exact"]
        part_rows.append({**part, "maximum_absolute_error": _display(exact),
                          "maximum_absolute_error_exact": str(exact), "maximum_absolute_error_display_overflow": _display(exact) is None})
    return {"result": "PASS_STRICT_NORMAL_LIMIT" if not failures else "FAIL_STRICT_NORMAL_LIMIT",
            "component_limit": COMPONENT_LIMIT, "component_limit_exact": "1/500000",
            "numeric_rule": "absolute difference of represented raw/source numbers <= exact 1/500000; no normalization or epsilon",
            "angular_limit": None, "angular_rule": "scale-first unit vectors; degrees(atan2(hypot(cross), dot)); diagnostic only",
            "corners_compared": len(rows), "numeric_components_compared": len(rows) * 3,
            "passing_corners": len(rows) - len(failures), "exceeding_corners": len(failures),
            "exceeding_components": sum(len(row["failed_components"]) for row in failures),
            "maximum_absolute_error": _display(maximum), "maximum_absolute_error_exact": str(maximum),
            "maximum_absolute_error_display_overflow": _display(maximum) is None,
            "maximum_angular_error_degrees": maximum_angle, "per_part": part_rows,
            "exceeding_corner_records": failures, "rows": results}


def _base_report():
    return {"schema": REPORT_SCHEMA, "version": VERSION, "result": "FAIL_CLOSED",
            **{stage: {"result": "NOT_RUN"} for stage in _STAGES},
            "limits": {"target_starts": 0, "native_version_starts": 0, "source_evaluations": 0, "exports": 0,
                       "imports": 0, "renders": 0, "scene_writes": 0, "native_receiving_evidence": False,
                       "native_mapping_attested": False, "target_execution_authorized": False,
                       "normal_values_compared": False, "material_values_compared": False, "poses_compared": False,
                       "meaning": "Finite CPU normal loss on untrusted observations; no native capture, receiving acceptance or execution permission"}}


def check_normals(package_root, geometry_observation_path, normal_observation_path):
    """Admit actual source and geometry bytes before the complete normal check."""
    report, stage = _base_report(), "authority_admission"
    try:
        report["admission"] = c221.check_package(package_root)
        stage = "geometry_correspondence"
        geometry_report = c222.check_observations(package_root, geometry_observation_path)
        report["admission"] = geometry_report["admission"]
        raw_geometry = c222._read_observation(geometry_observation_path)
        require(len(raw_geometry) == geometry_report["observation_bytes"] and c221.digest(raw_geometry) == geometry_report["observation_sha256"],
                "GEOMETRY_CHANGED", "Geometry bytes changed after fresh C222 checking", "geometry_correspondence")
        geometry = c221.strict_json(raw_geometry, "Bound geometry observation")
        correspondence = geometry_report["correspondence"]
        report["geometry"] = {"result": geometry_report["result"], "schema": geometry_report["schema"],
                              "observation_bytes": len(raw_geometry), "observation_sha256": c221.digest(raw_geometry),
                              "declared_origin": geometry_report["declared_origin"], "structure": geometry_report["structure"],
                              "corner_map_fields": correspondence["corner_map_fields"],
                              "corner_map_sha256": correspondence["corner_map_sha256"], "native_receiving_evidence": False}
        stage = "source_normals"
        authority = _read_source(package_root)
        report["source_payload"] = authority["payload"]
        stage = "normal_read"
        raw = _read_normal_observation(normal_observation_path)
        report["observation_bytes"], report["observation_sha256"] = len(raw), c221.digest(raw)
        stage = "normal_structure"
        observation = c221.strict_json(raw, "Normal observation")
        report["structure"], rows = _validate_structure(observation, geometry, geometry_report, authority)
        report["declared_origin"] = observation["declared_origin"]
        stage = "normal_comparison"
        report["comparison"] = _compare(rows)
        report["limits"]["normal_values_compared"] = True
        if report["comparison"]["exceeding_corners"]:
            report["result"] = "FAIL_STRICT_NORMAL_LIMIT"
            raise CheckError("NORMAL_COMPARISON", "Admissible raw normals exceed the unchanged strict component limit", stage)
        report["result"] = "PASS_CPU_NORMALS"
        return report
    except (CheckError, c221.CheckError, c222.CheckError, OSError) as exc:
        effective_stage = exc.stage if isinstance(exc, CheckError) else stage
        report["error"] = {"code": getattr(exc, "code", "IO"), "stage": effective_stage, "message": str(exc)}
        if isinstance(exc, c222.CheckError):
            report["error"]["upstream_stage"] = exc.stage
        key = {"authority_admission": "admission", "geometry_correspondence": "geometry", "source_normals": "structure",
               "normal_read": "structure", "normal_structure": "structure", "normal_comparison": "comparison"}.get(effective_stage)
        if key and report[key]["result"] == "NOT_RUN":
            report[key] = {"result": "FAIL_CLOSED"}
        raise CheckError(report["error"]["code"], str(exc), effective_stage, report) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--geometry-observations", required=True)
    parser.add_argument("--normal-observations", required=True)
    args = parser.parse_args(argv)
    try:
        report = check_normals(args.package_root, args.geometry_observations, args.normal_observations)
    except CheckError as exc:
        print(json.dumps(exc.report, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 1
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
