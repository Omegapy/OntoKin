#!/usr/bin/env python3
"""Finite CPU world-pose comparison against freshly admitted original samples.

Only check_poses is a public admission API. CPU results cannot attest native
capture, authorize a target process or complete the second-target proof.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
from functools import lru_cache
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import sys


sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location(
    "ontokin_c236_authority", Path(__file__).absolute().parents[1] / "second_target_c221/check_bindings.py")
c221 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(c221)

VERSION = "C236/0.1.0"
SCHEMA = "ontokin.c236.pose-observations/0.1"
REPORT_SCHEMA = "ontokin.c236.pose-comparison/0.1"
MAX_OBSERVATION_BYTES = 1024 * 1024
TIMES = ("0", "0.25", "0.5", "0.75", "1", "1.5", "2")
COORDINATE_SYSTEM = {"position_unit": "m", "time_unit": "s",
                     "basis": "gltf-rh-y-up-identity", "quaternion_order": "wxyz",
                     "matrix_layout": "row-major-4x4"}
_POSITION_LIMIT = Fraction(1, 1000)
_TIME_LIMIT = Fraction(1, 1000000)
_MATRIX_LIMIT = Fraction(1, 1048576)
_COS_ARGUMENT_SQUARED = Fraction(1, 4000000)
_COS_TERMS = 256
_STAGES = ("admission", "source", "structure", "comparison")
_AXES = ("x", "y", "z")


class CheckError(ValueError):
    def __init__(self, code, message, stage="pose_structure", report=None):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.report = report


def require(condition, code, message, stage="pose_structure"):
    if not condition:
        raise CheckError(code, message, stage)


def _fields(value, expected, label, stage="pose_structure"):
    require(type(value) is dict and set(value) == set(expected),
            "SCHEMA", label + ": exact fields required", stage)


def _number(value, label, stage="pose_structure"):
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    require(valid, "FINITE", label + ": finite non-bool number required", stage)
    return value


def _vector(value, length, label, stage="pose_structure"):
    require(type(value) is list and len(value) == length,
            "VECTOR", label + ": unexpected component count", stage)
    for component in value:
        _number(component, label, stage)
    return value


def _integer(value, label):
    require(type(value) is int and value >= 0, "INDEX", label + ": nonnegative integer required")
    return value


def _display(value):
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if math.isfinite(result) else None


def _read_observation(path):
    supplied = os.fspath(path)
    require(type(supplied) is str and "\x00" not in supplied and "\\" not in supplied and
            ".." not in supplied.split("/"), "PATH", "Unsafe pose observation path", "pose_read")
    absolute = Path(os.path.abspath(supplied))
    try:
        with c221.SafeRoot(absolute.parent) as parent:
            fd = os.open(absolute.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent.fd)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode), "FILE", "Pose observation must be regular", "pose_read")
                require(0 < before.st_size <= MAX_OBSERVATION_BYTES, "SIZE",
                        "Pose observation exceeds finite size bounds", "pose_read")
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
                        "CHANGED", "Pose observation changed while reading", "pose_read")
                return raw
            finally:
                os.close(fd)
    except (OSError, c221.CheckError) as exc:
        raise CheckError("FILE", "Missing, unsafe or unreadable pose observation", "pose_read") from exc


def _rotation_matrix(q):
    """Exact homogeneous quaternion rotation; no floating normalization."""
    w, x, y, z = map(Fraction, q)
    n = w*w + x*x + y*y + z*z
    return [(w*w + x*x - y*y - z*z)/n, 2*(x*y - w*z)/n, 2*(x*z + w*y)/n,
            2*(x*y + w*z)/n, (w*w - x*x + y*y - z*z)/n, 2*(y*z - w*x)/n,
            2*(x*z - w*y)/n, 2*(y*z + w*x)/n, (w*w - x*x - y*y + z*z)/n]


def _unit_source_matrix(translation, rotation):
    r = _rotation_matrix(rotation)
    return [float(r[0]), float(r[1]), float(r[2]), translation[0],
            float(r[3]), float(r[4]), float(r[5]), translation[1],
            float(r[6]), float(r[7]), float(r[8]), translation[2], 0, 0, 0, 1]


def _read_source(package_root):
    """Reread original bytes; this internal seam is not an admission API."""
    bindings, part_map = c221.load_authority()
    pins = {item["packagePath"]: item for item in bindings["items"]}
    raw = {}
    with c221.SafeRoot(package_root) as package:
        for path in (c221.INPUT_PATHS[0], c221.INPUT_PATHS[4]):
            pin = pins[path]
            raw[path] = package.read(path, pin["bytes"], pin["sha256"], pin["mode"])
    glb, _ = c221.decode_glb(raw[c221.INPUT_PATHS[0]])
    reference = c221.strict_json(raw[c221.INPUT_PATHS[4]], "Original source reference")
    require(reference["schema_version"] == "ontokin.viewer-reference/0.2",
            "SOURCE_REFERENCE", "Unexpected original reference schema", "source_reference")
    expected_tolerances = {"position_m": 0.001, "rotation_rad": 0.001, "time_seconds": 0.000001}
    for key, value in expected_tolerances.items():
        require(c221.canonical(reference["tolerances"][key]) == c221.canonical(value),
                "SOURCE_REFERENCE", "Original pose tolerance differs", "source_reference")
    parts = {row["glbNode"]: row for row in part_map["entries"]}
    require(len(parts) == 18 and len(glb["nodes"]) == 18,
            "SOURCE_REFERENCE", "Expected 18 original flat source nodes", "source_reference")
    for number, node in enumerate(glb["nodes"]):
        require(number in parts and not node.get("children") and "matrix" not in node and
                node.get("scale", [1, 1, 1]) == [1, 1, 1],
                "SOURCE_SCALE", "Source does not establish this unit world-scale profile", "source_reference")
    for animation in glb.get("animations", []):
        for channel in animation["channels"]:
            require(channel["target"]["path"] in ("translation", "rotation"),
                    "SOURCE_SCALE", "Unexpected source animation transform channel", "source_reference")
    samples = reference["samples"]
    require(type(samples) is list and len(samples) == len(TIMES) and
            [sample["time_seconds"] for sample in samples] == list(TIMES),
            "SOURCE_REFERENCE", "Original reference-time inventory differs", "source_reference")
    paths = {part["sourcePath"] for part in parts.values()}
    source_rows = {}
    for sample in samples:
        _fields(sample, ("time_seconds", "objects"), "Source sample", "source_reference")
        require(type(sample["objects"]) is dict and set(sample["objects"]) == paths,
                "SOURCE_REFERENCE", "Incomplete original source sample", "source_reference")
        for node, part in parts.items():
            value = sample["objects"][part["sourcePath"]]
            _fields(value, ("position_m", "orientation_wxyz"), "Source pose", "source_reference")
            _vector(value["position_m"], 3, "Source position", "source_reference")
            q = _vector(value["orientation_wxyz"], 4, "Source quaternion", "source_reference")
            require(any(v != 0 for v in q), "SOURCE_REFERENCE", "Zero source quaternion", "source_reference")
            source_rows[(node, sample["time_seconds"])] = value
    mapping = [[node, part["glbMesh"], part["sourcePath"], part["elementId"], part["definitionId"], time]
               for node, part in sorted(parts.items()) for time in TIMES]
    pin = pins[c221.INPUT_PATHS[4]]
    return {"parts": parts, "rows": source_rows, "identity_map": mapping,
            "glb_sha256": pins[c221.INPUT_PATHS[0]]["sha256"],
            "reference_pin": {k: pin[k] for k in ("packagePath", "bytes", "sha256", "mode")},
            "glb_pin": {k: pins[c221.INPUT_PATHS[0]][k] for k in ("packagePath", "bytes", "sha256", "mode")}}


def _matrix_consistency(sample):
    m, t, q, scale = (sample[k] for k in ("world_matrix", "translation_m", "rotation_wxyz", "scale"))
    require(m[12:] == [0, 0, 0, 1], "MATRIX_AFFINE", "Exact affine final row required")
    require([m[3], m[7], m[11]] == t, "MATRIX_TRANSLATION", "Matrix and translation must report the same origin")
    a, b, c, d, e, f, g, h, i = [Fraction(m[row*4 + col]) for row in range(3) for col in range(3)]
    determinant = a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g)
    require(determinant > 0, "MATRIX_DETERMINANT", "Positive nonsingular matrix determinant required")
    r = _rotation_matrix(q)
    residuals = [Fraction(m[row*4 + col])/Fraction(scale[col]) - r[row*3 + col]
                 for row in range(3) for col in range(3)]
    maximum = max(map(abs, residuals))
    require(maximum <= _MATRIX_LIMIT, "MATRIX_CONSISTENCY",
            "Matrix/quaternion/scale residual exceeds predeclared structural envelope")
    return {"result": "PASS_MATRIX_CONSISTENCY", "dimensionless_limit_exact": str(_MATRIX_LIMIT),
            "signed_residuals_exact": [str(v) for v in residuals],
            "absolute_residuals_exact": [str(abs(v)) for v in residuals],
            "signed_residuals": [_display(v) for v in residuals],
            "maximum_absolute_residual_exact": str(maximum),
            "maximum_absolute_residual": _display(maximum),
            "raw_determinant_exact": str(determinant), "exact_origin_equality": True}


def _validate_structure(observation, source):
    _fields(observation, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256",
                          "coordinate_system", "parts"), "Pose observation")
    require(observation["schema"] == SCHEMA, "SCHEMA", "Unsupported pose observation schema")
    require(type(observation["declared_origin"]) is str and observation["declared_origin"] in
            ("synthetic", "unattested-native"), "ORIGIN", "Unsupported untrusted origin label")
    require(observation["accepted_program_revision"] == c221.ACCEPTED_REVISION and
            observation["glb_sha256"] == source["glb_sha256"], "IDENTITY", "Pose source/artifact claim differs")
    require(c221.canonical(observation["coordinate_system"]) == c221.canonical(COORDINATE_SYSTEM),
            "COORDINATES", "Only the predeclared world identity basis and encodings are supported")
    parts = observation["parts"]
    require(type(parts) is list and len(parts) == 18, "COUNT", "Exactly 18 observed parts required")
    seen_nodes, native_ids, rows = set(), set(), {}
    for part in parts:
        _fields(part, ("gltf_node", "gltf_mesh", "element_id", "definition_id", "source_path",
                       "native_node_id", "samples"), "Pose part")
        node = _integer(part["gltf_node"], "glTF node")
        mesh = _integer(part["gltf_mesh"], "glTF mesh")
        require(node in source["parts"] and node not in seen_nodes, "IDENTITY", "Unknown or duplicate source node")
        seen_nodes.add(node)
        expected = source["parts"][node]
        for actual, value in ((mesh, expected["glbMesh"]), (part["element_id"], expected["elementId"]),
                              (part["definition_id"], expected["definitionId"]), (part["source_path"], expected["sourcePath"])):
            require(c221.canonical(actual) == c221.canonical(value), "IDENTITY", "Part source identity differs")
        native = part["native_node_id"]
        require(type(native) is str and 0 < len(native) <= 4096 and "\x00" not in native and native not in native_ids,
                "NATIVE_LABEL", "Unique bounded nonempty native label required")
        native_ids.add(native)
        samples = part["samples"]
        require(type(samples) is list and len(samples) == len(TIMES), "COUNT", "Exactly seven samples per part required")
        seen_times = set()
        for sample in samples:
            _fields(sample, ("reference_time_seconds", "observed_time_seconds", "translation_m",
                             "rotation_wxyz", "scale", "world_matrix"), "Pose sample")
            time = sample["reference_time_seconds"]
            require(type(time) is str and time in TIMES and time not in seen_times,
                    "TIME_IDENTITY", "Unknown, mistyped or duplicate reference-time slot")
            seen_times.add(time)
            _number(sample["observed_time_seconds"], "Observed time")
            _vector(sample["translation_m"], 3, "Raw translation")
            q = _vector(sample["rotation_wxyz"], 4, "Raw quaternion")
            require(any(v != 0 for v in q), "ZERO_QUATERNION", "Nonzero raw quaternion required")
            scale = _vector(sample["scale"], 3, "Raw scale")
            require(all(v > 0 for v in scale), "SCALE_DOMAIN", "Strictly positive raw scales required")
            _vector(sample["world_matrix"], 16, "Raw world matrix")
            matrix = _matrix_consistency(sample)
            rows[(node, time)] = {"gltf_node": node, "gltf_mesh": mesh, "source_path": expected["sourcePath"],
                                 "element_id": expected["elementId"], "definition_id": expected["definitionId"],
                                 "native_node_id": native, "sample": sample, "source": source["rows"][(node, time)],
                                 "matrix_consistency": matrix}
        require(seen_times == set(TIMES), "TIME_IDENTITY", "Incomplete reference-time set")
    require(seen_nodes == set(source["parts"]) and len(rows) == 126, "COUNT", "Incomplete object/time inventory")
    ordered = [rows[(node, time)] for node in sorted(seen_nodes) for time in TIMES]
    return {"result": "PASS_POSE_STRUCTURE", "parts": 18, "sample_times": list(TIMES), "object_time_pairs": 126,
            "native_labels_attested": False, "matrix_consistency_limit_exact": str(_MATRIX_LIMIT)}, ordered


@lru_cache(maxsize=_COS_TERMS + 1)
def _cosine_bounds(n):
    """Alternating exact-rational bounds for cos(1/2000), cached by depth."""
    if n == 0:
        return Fraction(1), Fraction(1), Fraction(0), Fraction(1)
    term, total, lower, upper = _cosine_bounds(n - 1)
    term *= -_COS_ARGUMENT_SQUARED / ((2*n - 1)*(2*n))
    total += term
    if n % 2:
        lower = total
    else:
        upper = total
    return term, total, lower, upper


def _orientation_gate(raw, source):
    a, b = list(map(Fraction, raw)), list(map(Fraction, source))
    dot = sum(x*y for x, y in zip(a, b))
    ratio = dot*dot / (sum(x*x for x in a)*sum(x*x for x in b))
    for n in range(_COS_TERMS + 1):
        _, _, lower, upper = _cosine_bounds(n)
        if ratio >= upper*upper:
            return True, ratio, n
        if ratio <= lower*lower:
            return False, ratio, n
    raise CheckError("NUMERIC_RESOLUTION", "Angular gate unresolved within 256 rational Taylor terms", "pose_comparison")


def _unit_quaternion(q):
    largest = max(map(abs, q))
    scaled = [v/largest for v in q]
    length = math.hypot(*scaled)
    return [v/length for v in scaled]


def _angle_display(raw, source, exact_ratio):
    if exact_ratio == 1:
        return 0.0
    if exact_ratio == 0:
        return math.pi
    aw, ax, ay, az = _unit_quaternion(raw)
    bw, bx, by, bz = _unit_quaternion(source)
    w = aw*bw + ax*bx + ay*by + az*bz
    x = -aw*bx + ax*bw - ay*bz + az*by
    y = -aw*by + ax*bz + ay*bw - az*bx
    z = -aw*bz - ax*by + ay*bx + az*bw
    return 2*math.atan2(math.hypot(x, y, z), abs(w))


def _summary(rows):
    position = max(Fraction(v) for row in rows for v in row["position_absolute_errors_exact"])
    time = max(Fraction(row["time_absolute_error_exact"]) for row in rows)
    return {"object_time_pairs": len(rows), "position_components": 3*len(rows), "scale_components": 3*len(rows),
            "passing_original_poses": sum(row["original_pose_pass"] for row in rows),
            "failing_original_poses": sum(not row["original_pose_pass"] for row in rows),
            "passing_scale_profiles": sum(row["unit_scale_profile_pass"] for row in rows),
            "failing_scale_profiles": sum(not row["unit_scale_profile_pass"] for row in rows),
            "position_exceeding_components": sum(not ok for row in rows for ok in row["position_component_pass"]),
            "scale_differing_components": sum(not ok for row in rows for ok in row["unit_scale_component_pass"]),
            "maximum_position_error_exact": str(position), "maximum_position_error_m": _display(position),
            "maximum_time_error_exact": str(time), "maximum_time_error_seconds": _display(time),
            "maximum_orientation_error_rad": max(row["orientation_error_rad"] for row in rows),
            "minimum_orientation_dot_ratio_squared_exact": str(min(Fraction(row["orientation_dot_ratio_squared_exact"]) for row in rows)),
            "position_display_overflow": _display(position) is None,
            "time_display_overflow": _display(time) is None}


def _compare(structured_rows):
    rows, losses = [], []
    for item in structured_rows:
        sample, source = item["sample"], item["source"]
        position_delta = [Fraction(a)-Fraction(b) for a, b in zip(sample["translation_m"], source["position_m"])]
        position_errors = list(map(abs, position_delta))
        position_pass = [v <= _POSITION_LIMIT for v in position_errors]
        time_delta = Fraction(sample["observed_time_seconds"])-Fraction(sample["reference_time_seconds"])
        time_pass = abs(time_delta) <= _TIME_LIMIT
        orientation_pass, ratio, terms = _orientation_gate(sample["rotation_wxyz"], source["orientation_wxyz"])
        scale_delta = [Fraction(v)-1 for v in sample["scale"]]
        scale_pass = [v == 0 for v in scale_delta]
        original_pose_pass = all(position_pass) and time_pass and orientation_pass
        profile_pass = all(scale_pass)
        gates = [name for name, ok in (("position", all(position_pass)), ("orientation", orientation_pass),
                                       ("time", time_pass), ("unit_scale_profile", profile_pass)) if not ok]
        identity = {k: item[k] for k in ("gltf_node", "gltf_mesh", "source_path", "element_id", "definition_id", "native_node_id")}
        row = {**identity, "reference_time_seconds": sample["reference_time_seconds"],
               "observed_time_seconds": sample["observed_time_seconds"],
               "raw_translation_m": sample["translation_m"], "raw_rotation_wxyz": sample["rotation_wxyz"],
               "raw_scale": sample["scale"], "raw_world_matrix": sample["world_matrix"],
               "source_position_m": source["position_m"], "source_orientation_wxyz": source["orientation_wxyz"],
               "derived_source_scale": [1, 1, 1],
               "derived_source_world_matrix": _unit_source_matrix(source["position_m"], source["orientation_wxyz"]),
               "matrix_consistency": item["matrix_consistency"],
               "position_deltas_exact": [str(v) for v in position_delta],
               "position_absolute_errors_exact": [str(v) for v in position_errors],
               "position_absolute_errors_m": [_display(v) for v in position_errors],
               "position_display_overflow": [_display(v) is None for v in position_errors],
               "position_component_pass": position_pass,
               "failed_position_components": [_AXES[i] for i, ok in enumerate(position_pass) if not ok],
               "time_delta_exact": str(time_delta), "time_absolute_error_exact": str(abs(time_delta)),
               "time_absolute_error_seconds": _display(abs(time_delta)), "time_display_overflow": _display(abs(time_delta)) is None,
               "time_pass": time_pass, "orientation_pass": orientation_pass,
               "orientation_dot_ratio_squared_exact": str(ratio), "orientation_decision_terms": terms,
               "orientation_error_rad": _angle_display(sample["rotation_wxyz"], source["orientation_wxyz"], ratio),
               "unit_scale_deltas_exact": [str(v) for v in scale_delta],
               "unit_scale_component_pass": scale_pass,
               "failed_scale_components": [_AXES[i] for i, ok in enumerate(scale_pass) if not ok],
               "original_pose_pass": original_pose_pass, "unit_scale_profile_pass": profile_pass,
               "failed_gates": gates}
        rows.append(row)
        if gates:
            losses.append({**identity, "reference_time_seconds": sample["reference_time_seconds"], "failed_gates": gates,
                           "failed_position_components": row["failed_position_components"],
                           "failed_scale_components": row["failed_scale_components"]})
    original_pass = all(row["original_pose_pass"] for row in rows)
    scale_pass = all(row["unit_scale_profile_pass"] for row in rows)
    result = "FAIL_POSE_LIMIT" if not original_pass else ("FAIL_SCALE_PROFILE" if not scale_pass else "PASS_CPU_POSES")
    return {"result": result, "original_pose_result": "PASS_POSE_LIMITS" if original_pass else "FAIL_POSE_LIMITS",
            "scale_profile_result": "PASS_UNIT_SCALE_PROFILE" if scale_pass else "FAIL_UNIT_SCALE_PROFILE",
            "position_metric": "maximum absolute XYZ component difference",
            "position_limit_exact": "1/1000", "orientation_limit_radians_exact": "1/1000",
            "time_limit_seconds_exact": "1/1000000",
            "angular_gate": "exact dot-squared/norm-product ratio versus rational bounds on cos(1/2000)^2",
            "scale_profile_rule": "separate exact unit-scale condition; not an original C220 pose tolerance",
            "summary": _summary(rows),
            "per_part": [{"gltf_node": node, **_summary([r for r in rows if r["gltf_node"] == node])}
                         for node in sorted({r["gltf_node"] for r in rows})],
            "per_time": [{"reference_time_seconds": time, **_summary([r for r in rows if r["reference_time_seconds"] == time])}
                         for time in TIMES],
            "losses": losses, "rows": rows}


def _base_report():
    return {"schema": REPORT_SCHEMA, "version": VERSION, "result": "FAIL_CLOSED",
            **{stage: {"result": "NOT_RUN"} for stage in _STAGES},
            "limits": {"target_starts": 0, "native_version_starts": 0, "source_evaluations": 0, "exports": 0,
                       "imports": 0, "renders": 0, "scene_writes": 0, "aggregate_starts": 0,
                       "native_receiving_evidence": False, "native_mapping_attested": False,
                       "target_execution_authorized": False, "poses_compared": False,
                       "material_values_compared": False, "normal_values_compared": False,
                       "R07_complete": False, "release_acceptance": False,
                       "meaning": "Finite CPU pose limits and separate scale profile on untrusted observations; no native capture or execution authority"}}


def check_poses(package_root, observation_path):
    """Freshly admit original source bytes and compare every declared pose."""
    report, stage = _base_report(), "authority_admission"
    try:
        report["admission"] = c221.check_package(package_root)
        stage = "source_reference"
        source = _read_source(package_root)
        report["source"] = {"result": "PASS_SOURCE_REFERENCE", "accepted_program_revision": c221.ACCEPTED_REVISION,
                            "reference": source["reference_pin"], "glb": source["glb_pin"],
                            "parts": 18, "sample_times": list(TIMES), "object_time_pairs": 126,
                            "identity_map_fields": ["gltf_node", "gltf_mesh", "source_path", "element_id", "definition_id", "reference_time_seconds"],
                            "identity_map": source["identity_map"],
                            "identity_map_sha256": c221.digest(c221.canonical(source["identity_map"])),
                            "unit_world_scale_derived_from_glb": True,
                            "source_supplies_world_matrices": False, "source_supplies_scale_samples": False}
        stage = "pose_read"
        raw = _read_observation(observation_path)
        report["observation_bytes"], report["observation_sha256"] = len(raw), c221.digest(raw)
        stage = "pose_structure"
        observation = c221.strict_json(raw, "Pose observation")
        report["structure"], rows = _validate_structure(observation, source)
        report["declared_origin"] = observation["declared_origin"]
        stage = "pose_comparison"
        report["comparison"] = _compare(rows)
        report["limits"]["poses_compared"] = True
        report["result"] = report["comparison"]["result"]
        if report["result"] != "PASS_CPU_POSES":
            code = "POSE_COMPARISON" if report["result"] == "FAIL_POSE_LIMIT" else "SCALE_PROFILE"
            raise CheckError(code, "Complete admissible observations fail the identified pose or scale gates", stage)
        return report
    except (CheckError, c221.CheckError, OSError, KeyError, TypeError, IndexError,
            AttributeError, OverflowError, RecursionError, ZeroDivisionError) as exc:
        effective_stage = exc.stage if isinstance(exc, CheckError) else stage
        code = getattr(exc, "code", "IO" if isinstance(exc, OSError) else "SHAPE")
        report["error"] = {"code": code, "stage": effective_stage, "message": str(exc)}
        key = {"authority_admission": "admission", "source_reference": "source",
               "pose_read": "structure", "pose_structure": "structure", "pose_comparison": "comparison"}[effective_stage]
        if report[key]["result"] == "NOT_RUN":
            report[key] = {"result": "FAIL_CLOSED", "error": report["error"]}
        raise CheckError(code, str(exc), effective_stage, report) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--pose-observations", required=True)
    args = parser.parse_args(argv)
    try:
        report = check_poses(args.package_root, args.pose_observations)
    except CheckError as exc:
        print(json.dumps(exc.report, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 1
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

