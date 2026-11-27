#!/usr/bin/env python3
"""Numerical-audit harness for gate MH of C271-P35 (P07 section 6).

An independent reimplementation of the probe's comparison: it imports nothing of the project, the
probe or the provider. For each of the three CPU stages of a retained cohort, it reads the retained
reference (synthetic-audit.json), the probe's report (probe.json), the GLB and the job, and
recomputes from those values:

* the expected row inventory: for every reference node, the 16 world-matrix terms; for every mesh
  node, one world-position row and one normal row per vertex and axis, then the minimum, maximum and
  size of the world bounds per axis;
* the actual world positions, from the report's retained local positions and world matrix in the
  order of Three.js r186's Vector3.applyMatrix4, and the actual bounds from those positions, so that
  the audit does not depend on the probe's vertex or bounds code (TR-15); the retained world
  vertices and bounds must equal that recomputation exactly. The matrix terms and the normals are
  the retained importer values;
* each row's difference |actual - expected|, its threshold (5e-6 m for positions, bounds and the
  translational matrix terms [0..2][3]; 1e-6 for the other matrix terms and the normals) and its
  decision (both values finite and the difference within the threshold);
* that the report's rows are exactly that inventory, with no row missing, extra or duplicated, and
  that every reported actual, expected, difference, threshold and decision equals the recomputation;
* the exact comparisons the retained values allow (names, identities, relationships, indices and
  materials), and the report's findings as a multiset;
* that Q01 and Q03 pass every row, and that the negative has exactly one failed row and exactly one
  finding, at equipment-tray/pair/left/base matrix_0_3, with a difference of 0.001 within 1e-9, on a
  GLB byte-identical to Q01's and a reference that differs from Q01's only there and in its scope.

Launch:  <worktree>/.venv/bin/python -I -S -B audit_numeric.py --cohort-root DIR --output OUT
A start without -B refuses (N-09). It starts no process and writes only its absent output file.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import stat
import sys
import time

SCHEMA = "ontokin.c271.p35-numerical-audit/2"
REPORT_SCHEMA = "ontokin.current-host-readback-result/0.2.0"
REFERENCE_SCHEMA = "ontokin.static-tray.independent-audit/0.1.0"
CONTRACT = "ontokin.current-host-readback/0.2.0"
CASES = {"Q01-positive": ("Q01", False), "Q03-positive": ("Q03", False), "Q01-changed-reference": ("Q01", True)}
POSITION_THRESHOLD, MATRIX_THRESHOLD = 5e-6, 1e-6
NEGATIVE_NODE, NEGATIVE_FIELD = "equipment-tray/pair/left/base", "matrix_0_3"
NEGATIVE_DIFFERENCE, NEGATIVE_DIFFERENCE_TOLERANCE = 0.001, 1e-9
CHANGED_SCOPE = ("Intentionally changed synthetic reference for a negative importer comparison control; "
                 "not native evidence")
HISTORICAL_ROWS, NODE_COUNT, MESH_COUNT, VERTICES_PER_MESH = 2060, 14, 12, 24
VALIDATOR_VERSION, THREE_VERSION, THREE_REVISION, NODE_VERSION = "2.0.0-dev.3.10", "0.186.1", "186", "v24.22.1"
ROW_KEYS = {"semantic_id", "field", "actual", "expected", "difference", "threshold", "passed"}
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
EXIT_PASSED, EXIT_FAILED, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3


# ---------------------------------------------------------------------------
# Common helpers (each MH tool carries its own copy; no tool imports another)
# ---------------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Refusal(Exception):
    """A precondition the tool refuses, with the rule it applies."""

    def __init__(self, rule, reason, **details):
        super().__init__(reason)
        self.rule, self.reason, self.details = rule, reason, details

    def as_dict(self):
        return {"rule": self.rule, "reason": self.reason, "details": self.details}


def require_no_bytecode():
    """N-09: every start of the framework interpreter carries -B (TR-17)."""
    if not sys.flags.dont_write_bytecode:
        raise Refusal("PYTHON", "Run with -B: every start of the qualification interpreter writes no bytecode (N-09)")


def mode_text(st_mode):
    return "0o%03o" % stat.S_IMODE(st_mode)


def canonical_path(value, *, kind=None, rule="PATH"):
    """An absolute path in normal form that is its own realpath, so no component is a symbolic link."""
    if type(value) is not str or not value.startswith("/") or "\0" in value:
        raise Refusal(rule, "Expected an absolute path", path=repr(value))
    if os.path.normpath(value) != value:
        raise Refusal(rule, "The path is not in normal form", path=value)
    if os.path.realpath(value) != value:
        raise Refusal(rule, "The path is not canonical: a component is a symbolic link", path=value)
    if kind is not None:
        try:
            info = os.lstat(value)
        except OSError as exc:
            raise Refusal(rule, "The path is absent or unreadable", path=value, error=str(exc)) from exc
        if kind == "dir" and not stat.S_ISDIR(info.st_mode):
            raise Refusal(rule, "Expected a directory", path=value)
        if kind == "file" and not stat.S_ISREG(info.st_mode):
            raise Refusal(rule, "Expected a regular file", path=value)
    return value


def read_regular(path, maximum, *, rule="INPUT"):
    """The bytes and binding of a regular file, opened without following a final link; a change during the read refuses."""
    canonical_path(path, rule=rule)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise Refusal(rule, "Cannot open the input", path=path, error=str(exc)) from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise Refusal(rule, "The input is not a regular file", path=path)
        if before.st_size > maximum:
            raise Refusal(rule, "The input exceeds its byte bound", path=path, size_bytes=before.st_size,
                          maximum=maximum)
        chunks, total = [], 0
        while True:
            block = os.read(fd, min(1 << 20, maximum + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            if total > maximum:
                raise Refusal(rule, "The input grew beyond its byte bound", path=path)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    named = os.lstat(path)

    def identity(info):
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode
    if identity(before) != identity(after) or identity(after) != identity(named) or total != before.st_size:
        raise Refusal(rule, "The input changed while it was read", path=path)
    data = b"".join(chunks)
    return data, {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": total, "mode": mode_text(before.st_mode)}


def strict_json(raw, *, rule="INPUT", what="document"):
    """JSON with duplicate members and non-finite constants refused."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Refusal(rule, "Duplicate JSON member in the " + what, member=key)
            result[key] = value
        return result

    def constant(text):
        raise Refusal(rule, "Non-finite JSON constant in the " + what, constant=text)
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except Refusal:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise Refusal(rule, "Invalid JSON in the " + what, error=str(exc)) from exc


def json_text(value):
    return (json.dumps(value, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def prepare_output_file(path):
    """An absent output path in an existing canonical directory; an existing path is never replaced."""
    canonical_path(path, rule="OUTPUT")
    canonical_path(os.path.dirname(path), kind="dir", rule="OUTPUT")
    if os.path.lexists(path):
        raise Refusal("OUTPUT", "The output path exists; it is never replaced", path=path)
    return path


def write_new(path, data):
    """Exclusive creation of one absent file, fsynced together with its directory."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0), 0o644)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)
    fsync_directory(os.path.dirname(path))
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def tool_record():
    path = os.path.realpath(__file__)
    with open(path, "rb") as stream:
        data = stream.read()
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "mode": mode_text(os.stat(path).st_mode)}


def invocation_record():
    return {"argv": list(sys.argv), "orig_argv": list(getattr(sys, "orig_argv", [])), "cwd": os.getcwd(),
            "pid": os.getpid(),
            "python": {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
                       "build_string": sys.version, "executable": sys.executable,
                       "flags": {name: getattr(sys.flags, name) for name in FLAG_NAMES}}}


# ---------------------------------------------------------------------------
# JavaScript value semantics that the comparison depends on
# ---------------------------------------------------------------------------

def is_number(value):
    return type(value) in (int, float)


def number(value):
    """A JSON number as a double; anything else (null for NaN, a string, a boolean, a missing value) is None."""
    return float(value) if is_number(value) else None


def finite(value):
    return value is not None and math.isfinite(value)


def recorded(value):
    """A number as the record can hold it: a non-finite double (JSON's 1e999) is written as text."""
    return value if value is None or math.isfinite(value) else repr(value)


def js_truthy(value):
    return not (value is None or value is False or value == "" or (is_number(value) and (value == 0 or value != value)))


def js_equal(first, second):
    """stable(first) === stable(second) for JSON values: numbers by value, -0 equal to 0, booleans not numbers."""
    if type(first) is bool or type(second) is bool:
        return type(first) is type(second) and first == second
    if is_number(first) and is_number(second):
        return float(first) == float(second)
    if first is None or second is None:
        return first is None and second is None
    if isinstance(first, str) or isinstance(second, str):
        return type(first) is type(second) and first == second
    if isinstance(first, list) and isinstance(second, list):
        return len(first) == len(second) and all(js_equal(a, b) for a, b in zip(first, second))
    if isinstance(first, dict) and isinstance(second, dict):
        return set(first) == set(second) and all(js_equal(first[key], second[key]) for key in first)
    return False


def normalized(value):
    """A comparable form of a JSON value: every number a double, -0 as 0."""
    if type(value) is bool or value is None or isinstance(value, str):
        return value
    if is_number(value):
        value = float(value)
        return 0.0 if value == 0 else value
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    return repr(value)


def finding_key(row):
    return json.dumps(normalized(row), sort_keys=True, allow_nan=True)


def js_sorted(values):
    return sorted(values, key=lambda item: "null" if item is None else str(item))


def element(container, *path):
    """container[path...] when every step exists; None (JavaScript's undefined) otherwise."""
    for step in path:
        if isinstance(step, int):
            if not isinstance(container, list) or not 0 <= step < len(container):
                return None
        elif not isinstance(container, dict) or step not in container:
            return None
        container = container[step]
    return container


# ---------------------------------------------------------------------------
# The recomputation
# ---------------------------------------------------------------------------

def threshold_for(field):
    """The thresholds of P07 section 6: positions and translational matrix terms 5e-6 m, the rest 1e-6."""
    if field.startswith("matrix_"):
        _, i, j = field.split("_")
        return POSITION_THRESHOLD if int(j) == 3 and int(i) < 3 else MATRIX_THRESHOLD
    if field.startswith(("world_vertex_", "world_min_", "world_max_", "world_size_")):
        return POSITION_THRESHOLD
    if field.startswith("normal_"):
        return MATRIX_THRESHOLD
    raise ValueError("unknown row field " + field)


def bound_values(vertices, axis):
    values = [number(element(vertex, axis)) for vertex in vertices] if isinstance(vertices, list) else []
    if not values or any(value is None for value in values):
        return None, None
    return min(values), max(values)


def expected_inventory(reference):
    """The rows in the probe's order, each with its expected value from the reference."""
    rows = []
    nodes = reference["nodes"]
    for ident in sorted(nodes):
        node = nodes[ident]
        for i in range(4):
            for j in range(4):
                rows.append((ident, "matrix_%d_%d" % (i, j), number(element(node, "world_matrix", i, j))))
        vertices = node.get("world_vertices")
        if not js_truthy(vertices):
            continue
        for i in range(len(vertices) if isinstance(vertices, list) else 0):
            for axis in range(3):
                rows.append((ident, "world_vertex_%d_%d" % (i, axis), number(element(vertices, i, axis))))
                rows.append((ident, "normal_%d_%d" % (i, axis), number(element(node, "normals", i, axis))))
        for axis in range(3):
            low, high = bound_values(vertices, axis)
            rows.append((ident, "world_min_%d" % axis, low))
            rows.append((ident, "world_max_%d" % axis, high))
            rows.append((ident, "world_size_%d" % axis, None if low is None else high - low))
    return rows


def apply_matrix4(point, matrix):
    """Three.js r186 Vector3.applyMatrix4 for a row-major matrix M[i][j], the probe's matrixRows(matrixWorld).

    With e = matrixWorld.elements, which is column-major (e[4 * j + i] = M[i][j]), Three.js computes
    w = 1 / (e[3] x + e[7] y + e[11] z + e[15]) and x' = (e[0] x + e[4] y + e[8] z + e[12]) w, and so
    on for y' and z', each sum from left to right in doubles. Python's float arithmetic in the same
    order gives the same doubles. None when an input is not a finite number or the result is not.
    """
    if not isinstance(point, list) or len(point) != 3 or not all(is_number(value) for value in point):
        return None
    if not isinstance(matrix, list) or len(matrix) != 4 or not all(isinstance(row, list) and len(row) == 4
                                                                    for row in matrix):
        return None
    x, y, z = (float(value) for value in point)
    m = [[number(value) for value in row] for row in matrix]
    if not all(finite(value) for row in m for value in row) or not all(math.isfinite(v) for v in (x, y, z)):
        return None
    denominator = m[3][0] * x + m[3][1] * y + m[3][2] * z + m[3][3]
    if denominator == 0:
        return None
    w = 1 / denominator
    result = [(m[i][0] * x + m[i][1] * y + m[i][2] * z + m[i][3]) * w for i in range(3)]
    return result if all(math.isfinite(value) for value in result) else None


def recompute_geometry(retained, reference):
    """Every mesh node's world vertices and bounds, from its retained positions and world matrix (TR-15)."""
    geometry = {}
    for ident in sorted(reference["nodes"]):
        if not js_truthy(element(reference["nodes"][ident], "world_vertices")):
            continue
        data = retained.get(ident) if isinstance(retained, dict) else None
        positions, matrix = element(data, "positions"), element(data, "world_matrix")
        vertices = [apply_matrix4(point, matrix) for point in positions] if isinstance(positions, list) else None
        bounds = None
        if vertices and all(vertex is not None for vertex in vertices):
            bounds = [[min(vertex[axis] for vertex in vertices) for axis in range(3)],
                      [max(vertex[axis] for vertex in vertices) for axis in range(3)]]
        geometry[ident] = {"vertices": vertices, "bounds": bounds}
    return geometry


def geometry_consistency(retained, geometry):
    """The retained world vertices and bounds against the recomputation, number for number."""
    rows = {}
    for ident, recomputed in geometry.items():
        data = retained.get(ident) if isinstance(retained, dict) else None
        pairs, comparable = [], True
        for kept, mine in ((element(data, "world_vertices"), recomputed["vertices"]),
                           (element(data, "world_bounds"), recomputed["bounds"])):
            if not (isinstance(kept, list) and isinstance(mine, list) and len(kept) == len(mine) and mine
                    and all(isinstance(a, list) and isinstance(b, list) and len(a) == len(b) == 3
                            for a, b in zip(kept, mine))):
                pairs.append(None)
                comparable = False
                continue
            pairs.append([(number(a[axis]), b[axis]) for a, b in zip(kept, mine) for axis in range(3)])
        deviations = [abs(a - b) for values in pairs if values for a, b in values if a is not None and b is not None]
        rows[ident] = {
            "vertices_equal": pairs[0] is not None and all(same_number(a, b) for a, b in pairs[0]),
            "bounds_equal": pairs[1] is not None and all(same_number(a, b) for a, b in pairs[1]),
            "comparable": comparable, "max_absolute_deviation": recorded(max(deviations)) if deviations else None}
    return rows


def actual_value(retained, geometry, ident, field):
    """The matrix terms and normals as retained; the world positions and bounds as recomputed (TR-15)."""
    node = retained.get(ident) if isinstance(retained, dict) else None
    parts = field.split("_")
    if field.startswith("matrix_"):
        return number(element(node, "world_matrix", int(parts[1]), int(parts[2])))
    if field.startswith("normal_"):
        return number(element(node, "normals", int(parts[1]), int(parts[2])))
    recomputed = geometry.get(ident) or {}
    if field.startswith("world_vertex_"):
        return number(element(recomputed.get("vertices"), int(parts[2]), int(parts[3])))
    axis = int(parts[2])
    bounds = recomputed.get("bounds")
    low, high = number(element(bounds, 0, axis)), number(element(bounds, 1, axis))
    if field.startswith("world_min_"):
        return low
    if field.startswith("world_max_"):
        return high
    return None if low is None or high is None else high - low


def decide(actual, expected, threshold):
    difference = abs(actual - expected) if actual is not None and expected is not None else None
    if difference is not None and not math.isfinite(difference):
        difference = None
    return difference, finite(actual) and finite(expected) and difference is not None and difference <= threshold


def same_number(first, second):
    if first is None or second is None:
        return first is None and second is None
    return first == second


def exact_findings(reference, three):
    """The exact comparisons that the retained report values allow, as the probe makes them."""
    findings, limits = [], []
    nodes, retained = reference["nodes"], three.get("nodes") if isinstance(three.get("nodes"), dict) else {}

    def exact(ident, field, actual, expected):
        if not js_equal(actual, expected):
            findings.append({"semantic_id": ident, "field": field, "actual": actual, "expected": expected})
    imported = three.get("node_count")
    if imported == len(retained) and set(retained) == set(nodes):
        pass  # the imported identity inventory equals the reference's: no node_identity_inventory finding
    elif set(retained) <= set(nodes):
        limits.append("node_identity_inventory: the imported nodes are not all retained, so the probe's actual "
                      "inventory cannot be rebuilt; only the finding's presence is compared")
        findings.append({"semantic_id": "", "field": "node_identity_inventory", "actual": "<not retained>",
                         "expected": sorted(nodes)})
    exact("", "node_count", imported, NODE_COUNT)
    meshes = 0
    for ident in sorted(set(retained) & set(nodes)):
        node, data = nodes[ident], retained[ident]
        if not isinstance(data, dict) or not isinstance(node, dict):
            limits.append("node " + ident + ": malformed retained or reference record")
            continue
        extras = node.get("extras") if isinstance(node.get("extras"), dict) else {}
        exact(ident, "original_name", data.get("original_name"), ident)
        exact(ident, "semantic_role_relationships", data.get("extras"), node.get("extras"))
        exact(ident, "children", data.get("children"), js_sorted(node.get("children") or []))
        owner = extras.get("owner_id")
        expected_parent = None if extras.get("role") == "tray-root" else (
            "/".join(str(part) for part in owner) if isinstance(owner, list) else "<undefined owner>")
        exact(ident, "parent", data.get("parent"), expected_parent)
        if not js_truthy(node.get("world_vertices")):
            limits.append("empty_root of " + ident + ": whether Three.js made it a mesh is not retained")
            continue
        meshes += 1
        positions = data.get("positions")
        exact(ident, "vertex_count", len(positions) if isinstance(positions, list) else None,
              len(node["world_vertices"]))
        exact(ident, "actual_triangle_indices", data.get("indices"), node.get("indices"))
        exact(ident, "material", data.get("material"), node.get("material"))
    exact("", "mesh_count", three.get("mesh_count"), MESH_COUNT)
    return findings, limits, meshes


def reference_structure(reference):
    nodes = reference.get("nodes")
    if not isinstance(nodes, dict):
        return {"nodes_object": False}
    meshes = {ident: node for ident, node in nodes.items()
              if isinstance(node, dict) and js_truthy(node.get("world_vertices"))}
    return {"nodes_object": True, "node_count": len(nodes), "mesh_count": len(meshes),
            "matrices_4x4": all(isinstance(element(node, "world_matrix"), list) and len(node["world_matrix"]) == 4
                                and all(isinstance(row, list) and len(row) == 4 and all(is_number(v) for v in row)
                                        for row in node["world_matrix"]) for node in nodes.values()),
            "vertices_per_mesh": sorted({len(node["world_vertices"]) for node in meshes.values()
                                         if isinstance(node["world_vertices"], list)}),
            "normals_match_vertices": all(isinstance(node.get("normals"), list)
                                          and len(node["normals"]) == len(node["world_vertices"])
                                          for node in meshes.values())}


def audit_case(label, directory):
    case, negative = CASES[label]
    reference_raw, reference_binding = read_regular(directory + "/synthetic-audit.json", 4 * 1024 * 1024)
    report_raw, report_binding = read_regular(directory + "/probe.json", 4 * 1024 * 1024)
    glb_raw, glb_binding = read_regular(directory + "/synthetic.glb", 8 * 1024 * 1024)
    job_raw, job_binding = read_regular(directory + "/job.json", 32 * 1024)
    reference = strict_json(reference_raw, what="reference")
    report = strict_json(report_raw, what="report")
    job = strict_json(job_raw, what="job")
    result = {"label": label, "case": case, "negative": negative,
              "inputs": {"reference": {"path": directory + "/synthetic-audit.json", **reference_binding},
                         "report": {"path": directory + "/probe.json", **report_binding},
                         "glb": {"path": directory + "/synthetic.glb", **glb_binding},
                         "job": {"path": directory + "/job.json", **job_binding}}}
    checks = {}
    if not isinstance(reference, dict) or not isinstance(reference.get("nodes"), dict):
        raise Refusal("REFERENCE", "The reference has no node table", label=label)
    if not isinstance(report, dict) or not isinstance(report.get("three"), dict):
        checks["report_has_three"] = False
        result.update(checks=checks, passed=False)
        return result, reference, glb_binding
    three = report["three"]
    khronos = report.get("khronos") if isinstance(report.get("khronos"), dict) else {}
    issues = element(khronos, "report", "issues") or {}
    structure = reference_structure(reference)
    result["reference_structure"] = structure
    checks.update({
        "reference_schema": reference.get("schema") == REFERENCE_SCHEMA,
        "reference_case": reference.get("case") == case,
        "reference_passed": reference.get("passed") is True,
        "reference_binds_glb": reference.get("artifact_sha256") == glb_binding["sha256"],
        "reference_14_nodes_12_meshes": structure.get("node_count") == NODE_COUNT
        and structure.get("mesh_count") == MESH_COUNT,
        "reference_24_vertices_per_mesh": structure.get("vertices_per_mesh") == [VERTICES_PER_MESH],
        "reference_matrices_and_normals": bool(structure.get("matrices_4x4") and structure.get("normals_match_vertices")),
        "report_schema": report.get("schema") == REPORT_SCHEMA and report.get("contract") == CONTRACT
        and report.get("design_revision") == 4 and report.get("amendments") == ["P33-AMENDMENT-001"],
        "report_case_and_slot": report.get("case") == case and report.get("slot") == "CPU-" + label,
        "report_input_lock": report.get("input_lock_sha256") == "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
        "report_binds_glb": report.get("artifact_sha256") == glb_binding["sha256"] == job.get("artifact_sha256"),
        "report_binds_reference": report.get("audit_sha256") == reference_binding["sha256"] == job.get("audit_sha256"),
        "report_binds_manifest": report.get("supplemental_manifest_sha256") == job.get("supplemental_manifest_sha256"),
        "report_node_version": report.get("node") == NODE_VERSION,
        "report_no_native_start_or_export": report.get("native_starts") == 0 and report.get("exports") == 0,
        "report_without_error": "error" not in report,
        "validator_version": khronos.get("version") == VALIDATOR_VERSION,
        "validator_zero_errors_warnings_untruncated": khronos.get("passed") is True
        and issues.get("numErrors") == 0 and issues.get("numWarnings") == 0 and issues.get("truncated") is False,
        "three_version": three.get("version") == THREE_VERSION and three.get("revision") == THREE_REVISION,
        "three_counts": three.get("node_count") == NODE_COUNT and three.get("mesh_count") == MESH_COUNT
        and three.get("animations") == 0,
        "three_tolerances": three.get("position_tolerance_m") == POSITION_THRESHOLD
        and three.get("matrix_tolerance") == MATRIX_THRESHOLD,
        "input_preserved": report.get("input_preserved") is True})
    retained = three.get("nodes") if isinstance(three.get("nodes"), dict) else {}
    geometry = recompute_geometry(retained, reference)
    consistency = geometry_consistency(retained, geometry)
    inventory = expected_inventory(reference)
    expected_keys = [(ident, field) for ident, field, _ in inventory]
    measurements = three.get("measurements") if isinstance(three.get("measurements"), list) else []
    malformed = [index for index, row in enumerate(measurements)
                 if not isinstance(row, dict) or set(row) != ROW_KEYS
                 or not isinstance(row.get("semantic_id"), str) or not isinstance(row.get("field"), str)]
    reported = Counter((row["semantic_id"], row["field"]) for row in measurements if isinstance(row, dict)
                       and isinstance(row.get("semantic_id"), str) and isinstance(row.get("field"), str))
    report_rows = {}
    for row in measurements:
        if isinstance(row, dict) and isinstance(row.get("semantic_id"), str) and isinstance(row.get("field"), str):
            report_rows.setdefault((row["semantic_id"], row["field"]), row)
    duplicates = sorted("%s %s" % key for key, count in reported.items() if count > 1)
    missing = sorted("%s %s" % key for key in set(expected_keys) - set(reported))
    extra = sorted("%s %s" % key for key in set(reported) - set(expected_keys))
    table, mismatches, failed = [], [], []
    for ident, field, expected in inventory:
        threshold = threshold_for(field)
        actual = actual_value(retained, geometry, ident, field)
        difference, passed = decide(actual, expected, threshold)
        entry = {"semantic_id": ident, "field": field, "threshold": threshold, "expected": recorded(expected),
                 "actual": recorded(actual), "difference": recorded(difference), "passed": passed}
        row = report_rows.get((ident, field))
        if row is None:
            entry["report"] = "missing"
        else:
            matches = {"actual": same_number(number(row.get("actual")), actual) and not isinstance(row.get("actual"), bool),
                       "expected": same_number(number(row.get("expected")), expected),
                       "difference": same_number(number(row.get("difference")), difference),
                       "threshold": type(row.get("threshold")) in (int, float) and row.get("threshold") == threshold,
                       "passed": row.get("passed") is passed}
            entry["report"] = "matches" if all(matches.values()) else "differs"
            if not all(matches.values()):
                entry["report_values"] = {key: row.get(key) for key in ("actual", "expected", "difference",
                                                                         "threshold", "passed")}
                mismatches.append("%s %s: %s" % (ident, field, ", ".join(k for k, v in matches.items() if not v)))
        if not passed:
            failed.append(entry)
        table.append(entry)
    order = [(row.get("semantic_id"), row.get("field")) for row in measurements if isinstance(row, dict)]
    near = [{"semantic_id": row["semantic_id"], "field": row["field"], "actual": row["actual"],
             "expected": row["expected"], "difference": row["difference"], "threshold": row["threshold"]}
            for row in failed]
    exact, limits, mesh_rows = exact_findings(reference, three)
    recomputed = Counter(finding_key(row) for row in near + exact)
    findings = three.get("findings") if isinstance(three.get("findings"), list) else None
    reported_findings = Counter(finding_key(row) for row in findings or [])
    checks.update({
        "rows_well_formed": not malformed and isinstance(three.get("measurements"), list),
        "rows_complete": not missing, "rows_without_extra": not extra, "rows_without_duplicates": not duplicates,
        "rows_match_recomputation": not mismatches,
        "retained_world_vertices_equal_recomputation": bool(consistency)
        and all(row["vertices_equal"] for row in consistency.values()),
        "retained_world_bounds_equal_recomputation": bool(consistency)
        and all(row["bounds_equal"] for row in consistency.values()),
        "row_order_is_the_probe_order": order == expected_keys,
        "row_count_is_historical_2060": len(expected_keys) == HISTORICAL_ROWS,
        "findings_equal_recomputation": findings is not None and recomputed == reported_findings,
        "three_passed_consistent": three.get("passed") is (not (near + exact)),
        "exact_comparisons_pass": not exact})
    if negative:
        target = [row for row in failed if (row["semantic_id"], row["field"]) == (NEGATIVE_NODE, NEGATIVE_FIELD)]
        checks.update({
            "negative_exactly_one_failed_row": len(failed) == 1 and len(target) == 1,
            "negative_threshold_5e-6": bool(target) and target[0]["threshold"] == POSITION_THRESHOLD,
            "negative_difference_about_0.001": bool(target) and target[0]["difference"] is not None
            and abs(target[0]["difference"] - NEGATIVE_DIFFERENCE) <= NEGATIVE_DIFFERENCE_TOLERANCE,
            "negative_exactly_one_finding": findings is not None and len(findings) == 1
            and bool(target) and reported_findings == Counter([finding_key(near[0])]) if near else False,
            "negative_report_failed": report.get("passed") is False and three.get("passed") is False
            and khronos.get("passed") is True})
        if target:
            result["negative_row"] = dict(target[0], difference_minus_0_001=target[0]["difference"] - NEGATIVE_DIFFERENCE
                                          if target[0]["difference"] is not None else None)
    else:
        checks.update({
            "positive_every_row_passes": not failed,
            "positive_no_finding": findings == [],
            "positive_report_passed": report.get("passed") is True and three.get("passed") is True})
    result.update(
        counts={"expected_rows": len(expected_keys), "reported_rows": len(measurements),
                "failed_rows": len(failed), "missing": len(missing), "extra": len(extra), "duplicates": len(duplicates),
                "mismatches": len(mismatches), "malformed": len(malformed), "mesh_nodes_compared": mesh_rows,
                "reported_findings": None if findings is None else len(findings),
                "recomputed_findings": len(near) + len(exact)},
        missing=missing, extra=extra, duplicates=duplicates, mismatches=mismatches, malformed_rows=malformed,
        failed_rows=failed, recomputed_exact_findings=exact, limits=limits, checks=checks,
        geometry_recomputation=consistency,
        passed=all(checks.values()), rows=table)
    return result, reference, glb_binding


def negative_fixture(positive_reference, negative_reference, positive_glb, negative_glb):
    """The negative's GLB is Q01's, byte for byte; its reference differs only at the one term and the scope."""
    same_glb = positive_glb["sha256"] == negative_glb["sha256"] and positive_glb["size_bytes"] == negative_glb["size_bytes"]
    positive_value = element(positive_reference, "nodes", NEGATIVE_NODE, "world_matrix", 0, 3)
    negative_value = element(negative_reference, "nodes", NEGATIVE_NODE, "world_matrix", 0, 3)
    changed = is_number(positive_value) and is_number(negative_value) and \
        float(negative_value) == float(positive_value) + 0.001
    rest_equal = False
    if isinstance(positive_reference, dict) and isinstance(negative_reference, dict) and changed:
        first, second = json.loads(json.dumps(positive_reference)), json.loads(json.dumps(negative_reference))
        first["nodes"][NEGATIVE_NODE]["world_matrix"][0][3] = None
        second["nodes"][NEGATIVE_NODE]["world_matrix"][0][3] = None
        first.pop("scope", None)
        second_scope = second.pop("scope", None)
        rest_equal = js_equal(first, second) and second_scope == CHANGED_SCOPE
    return {"glb_byte_identical": same_glb, "term_increased_by_0.001": changed,
            "otherwise_identical_with_the_changed_scope": rest_equal,
            "positive_value": positive_value, "negative_value": negative_value,
            "passed": bool(same_glb and changed and rest_equal)}


def run(args):
    started, monotonic = utc_now(), time.monotonic()
    root = canonical_path(args.cohort_root, kind="dir", rule="INPUT")
    labels = args.case or list(CASES)
    if len(set(labels)) != len(labels) or not set(labels) <= set(CASES):
        raise Refusal("USAGE", "Cases are Q01-positive, Q03-positive and Q01-changed-reference, each once")
    results, references, glbs = {}, {}, {}
    for label in labels:
        directory = canonical_path(root + "/" + label, kind="dir", rule="INPUT")
        results[label], references[label], glbs[label] = audit_case(label, directory)
    record = {"schema": SCHEMA, "tool": tool_record(), "invocation": invocation_record(), "started_at_utc": started,
              "cohort_root": root, "cases": results, "loaded_project_files": [],
              "thresholds": {"position_m": POSITION_THRESHOLD, "matrix_and_normal": MATRIX_THRESHOLD},
              "world_positions": "recomputed from the retained local positions and world matrix in the order of "
                                 "Three.js r186 Vector3.applyMatrix4; the bounds from the recomputed positions (TR-15)",
              "negative_rule": {"semantic_id": NEGATIVE_NODE, "field": NEGATIVE_FIELD,
                                "difference": NEGATIVE_DIFFERENCE, "tolerance": NEGATIVE_DIFFERENCE_TOLERANCE}}
    if "Q01-positive" in results and "Q01-changed-reference" in results:
        record["negative_fixture"] = negative_fixture(references["Q01-positive"], references["Q01-changed-reference"],
                                                      glbs["Q01-positive"], glbs["Q01-changed-reference"])
    passed = all(row["passed"] for row in results.values()) and record.get("negative_fixture", {}).get("passed", True) \
        and set(labels) == set(CASES)
    record.update(all_three_cases=set(labels) == set(CASES), passed=passed, finished_at_utc=utc_now(),
                  elapsed_s=time.monotonic() - monotonic)
    write_new(args.output, json_text(record))
    sys.stderr.write("MH-NUMERICAL-AUDIT " + json.dumps({"passed": passed, "cases": {
        label: {"passed": row["passed"], "failed_checks": sorted(k for k, v in row.get("checks", {}).items() if not v)}
        for label, row in results.items()}}, sort_keys=True) + "\n")
    return EXIT_PASSED if passed else EXIT_FAILED


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def main(argv=None):
    parser = _Parser(prog="audit_numeric.py", allow_abbrev=False, description=__doc__.splitlines()[0])
    parser.add_argument("--cohort-root", required=True)
    parser.add_argument("--case", action="append")
    parser.add_argument("--output", required=True)
    output = None
    try:
        args = parser.parse_args(argv)
        output = prepare_output_file(args.output)
        require_no_bytecode()
        return run(args)
    except Refusal as exc:
        return report_end(output, {"schema": "ontokin.c271.p35-tool-refusal/1", "tool": "audit_numeric.py",
                                   "state": "REFUSED", "refusal": exc.as_dict()}, EXIT_REFUSED)
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        return report_end(output, {"schema": "ontokin.c271.p35-tool-failure/1", "tool": "audit_numeric.py",
                                   "state": "UNKNOWN", "error": {"type": type(exc).__name__, "reason": str(exc)}},
                          EXIT_UNKNOWN)


def report_end(output, document, code):
    """A refusal or failure goes to stderr, and to the output path while that path is still absent."""
    document.update(finished_at_utc=utc_now(), invocation=invocation_record())
    sys.stderr.write(json.dumps(document, sort_keys=True) + "\n")
    if output is not None and not os.path.lexists(output):
        try:
            write_new(output, json_text(document))
        except OSError:
            pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
