"""Run the adopted C01-C20 checks and verify identified external evidence.

The fixture manifest contains requirements, never measured pass statuses. Every
selected unittest is run once even when several cases require it. Independent
viewer/format evidence is an explicit retained-evidence gate; reading a report
does not rerun Blender, a browser, or an external glTF validator.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import platform
import re
import struct
import sys
import time
import unittest

from . import __version__
from .bundle import load_bundle


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = ROOT / "docs/language-design/construction-v0.1"
_TEST_ID = re.compile(r"test_[A-Za-z0-9_]+\.[A-Za-z_][A-Za-z0-9_]*\.test_[A-Za-z0-9_]+\Z")
_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ROLES = {"source_bundle", "workflow", "artifact", "reference", "external_results", "viewer_results", "capture"}


def _json_file(path: Path):
    if path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("A conformance JSON input exceeds 4 MiB.")
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate JSON member: " + key)
            value[key] = item
        return value
    def nonfinite(value):
        raise ValueError("Non-finite JSON token: " + value)
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)


def file_identity(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def implementation_identity() -> dict:
    """Read the package bytes now; do not reuse a previously loaded engine pin."""
    digest = hashlib.sha256()
    for path in sorted((ROOT / "ontokin").glob("*.py")):
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return {"name": "ontokin-reference", "version": __version__,
            "source_code_sha256": "sha256:" + digest.hexdigest()}


def _relative(path: Path, root: Path = ROOT) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _repository_file(value: str, root: Path = ROOT) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("An evidence path must be a nonempty relative POSIX path.")
    parts = value.split("/")
    if PurePosixPath(value).is_absolute() or any(part in ("", ".", "..") for part in parts):
        raise ValueError("An evidence path cannot escape or use ambiguous path segments.")
    path = (root / value).resolve(strict=True)
    path.relative_to(root.resolve())
    if not path.is_file():
        raise ValueError("An evidence path must resolve to a regular file.")
    return path


def load_manifest(directory: Path = DEFAULT_FIXTURES) -> dict:
    manifest = _json_file(Path(directory) / "validation-cases.json")
    if manifest.get("schema_version") != "ontokin.construction-validation-cases/0.1":
        raise ValueError("Unknown construction fixture manifest schema.")
    if manifest.get("status") != "predetermined_expectations_not_execution_results":
        raise ValueError("The construction manifest must contain predetermined expectations.")
    cases = manifest.get("cases", [])
    if [case.get("id") for case in cases] != [f"C{i:02}" for i in range(1, 21)]:
        raise ValueError("The manifest must list adopted C01-C20 once, in order.")
    for case in cases:
        tests = case.get("required_tests")
        if not isinstance(tests, list) or not tests or len(tests) != len(set(tests)):
            raise ValueError("Each case requires distinct, nonempty executable test IDs.")
        if any(not isinstance(name, str) or _TEST_ID.fullmatch(name) is None for name in tests):
            raise ValueError("A required test ID must identify one concrete unittest method.")
        if set(case.get("external_gates", [])) - {"identified_visual_delivery"}:
            raise ValueError("Unknown external construction gate.")
    return manifest


def _fixture_records(manifest: dict, directory: Path) -> list[dict]:
    records = []
    for fixture in manifest["fixture_sources"]:
        bundle_path = directory / fixture["bundle"]
        program = load_bundle(_json_file(bundle_path))
        expectation_path = directory / fixture["expected"]
        expected = _json_file(expectation_path)
        if program.program_revision != fixture["program_revision"] or expected["program_revision"] != program.program_revision:
            raise ValueError("A fixture program no longer matches its predetermined revision.")
        records.append({"id": fixture["id"], "case_ids": fixture["case_ids"],
                        "bundle": _relative(bundle_path), "bundle_sha256": file_identity(bundle_path),
                        "editable_manifest": _relative(directory / fixture["editable_manifest"]),
                        "expected": _relative(expectation_path), "expected_sha256": file_identity(expectation_path),
                        "expectation_basis": "Predetermined source and oracle; measured test results are recorded separately.",
                        "program_revision": program.program_revision, "source_manifest": program.manifest()})
    return records


def _evidence_inventory(directory: Path) -> list[dict]:
    # Include helper fixtures and all test source files, since a selected test
    # can import another test module or use an ordinary reference assembly.
    paths = [path for path in directory.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
    paths += [path for path in (ROOT / "tests").rglob("*")
              if path.is_file() and "__pycache__" not in path.parts and path.suffix in {".py", ".ok", ".json"}]
    paths += [ROOT / "docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md"]
    paths += [path for path in (ROOT / "docs/language-design/core-v0.1").iterdir()
              if path.is_file() and path.suffix in {".ok", ".json"}]
    paths += [path for path in (ROOT / "tools").iterdir()
              if path.is_file() and path.suffix in {".py", ".mjs", ".json"}]
    return [{"path": _relative(path), "sha256": file_identity(path)}
            for path in sorted(set(paths), key=lambda item: _relative(item))]


class _MeasuredResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.records: dict[str, dict] = {}
        self.fixture_errors: list[dict] = []
        self._started = {}

    def startTest(self, test):
        super().startTest(test)
        name = test.id()
        self.records[name] = {"test_id": name, "status": "running", "elapsed_seconds": None, "failures": []}
        self._started[name] = time.monotonic()

    def stopTest(self, test):
        name = test.id()
        self.records[name]["elapsed_seconds"] = round(time.monotonic() - self._started[name], 6)
        super().stopTest(test)

    def _problem(self, test, status, message):
        record = self.records.get(test.id())
        if record is None:
            self.fixture_errors.append({"test_id": test.id(), "status": status, "failure": message})
        else:
            record["status"] = status
            record["failures"].append(message)

    def addSuccess(self, test):
        super().addSuccess(test)
        if self.records[test.id()]["status"] == "running":
            self.records[test.id()]["status"] = "passed"

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._problem(test, "failed", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._problem(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        parent = getattr(test, "test_case", test)
        self._problem(parent, "skipped", "Skipped: " + reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._problem(test, "expected_failure", self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._problem(test, "unexpected_success", "An expected-failure test unexpectedly succeeded; acceptance needs review.")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            status = "failed" if issubclass(err[0], test.failureException) else "error"
            self._problem(test, status, subtest.id() + "\n" + self._exc_info_to_string(err, test))


def _run_tests(names: list[str]) -> dict:
    # Bare module IDs match unittest discovery and the existing module manifest.
    # Test classes retain normal setUpClass/tearDownClass behavior in one suite.
    added = []
    for path in (str(ROOT), str(ROOT / "tests")):
        if path not in sys.path:
            sys.path.insert(0, path)
            added.append(path)
    try:
        loader = unittest.TestLoader()
        suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in names)
        result = _MeasuredResult()
        started = time.monotonic()
        suite.run(result)
        elapsed = round(time.monotonic() - started, 6)
    finally:
        for path in added:
            sys.path.remove(path)
    records = []
    for name in names:
        records.append(result.records.pop(name, {"test_id": name, "status": "not_run",
                                                 "elapsed_seconds": None,
                                                 "failures": ["The named unittest did not execute; inspect loader/fixture errors."]}))
    counts = Counter(record["status"] for record in records)
    return {"unique_required": len(names), "tests_run": result.testsRun,
            "elapsed_seconds": elapsed, "outcomes": dict(sorted(counts.items())),
            "loader_errors": loader.errors, "fixture_errors": result.fixture_errors,
            "unexpected_test_records": list(result.records.values()), "tests": records,
            "counting_basis": "Executed unittest methods; no assertion count is inferred."}


def _glb_identity(path: Path) -> dict:
    with path.open("rb") as stream:
        header = stream.read(20)
        if len(header) != 20:
            raise ValueError("The identified artifact is not a complete GLB header.")
        magic, version, total, chunk_length, chunk_type = struct.unpack("<4sIIII", header)
        if magic != b"glTF" or version != 2 or total != path.stat().st_size or chunk_type != 0x4E4F534A:
            raise ValueError("The identified artifact has an invalid GLB identity container.")
        if chunk_length > 4 * 1024 * 1024 or chunk_length > total - 20:
            raise ValueError("The GLB metadata exceeds the bounded identity reader.")
        document = json.loads(stream.read(chunk_length).decode("utf-8"))
    return document["extras"]["ontokin"]


def _require(condition: bool, message: str):
    if not condition:
        raise ValueError(message)


def _finite(value, label: str) -> float:
    _require(type(value) in (int, float) and -1e300 <= value <= 1e300,
             label + " must be a finite number.")
    return float(value)


def _metric(value, maximum: float, label: str) -> float:
    result = _finite(value, label)
    _require(0 <= result <= maximum, label + " exceeds its declared tolerance.")
    return result


def _same_metric(recorded, observed: float, label: str):
    value = _finite(recorded, label)
    _require(math.isclose(value, observed, rel_tol=1e-6, abs_tol=1e-12),
             label + " disagrees with its retained observations.")


def _vector(value, count: int, label: str) -> list[float]:
    _require(isinstance(value, list) and len(value) == count, label + " has the wrong component count.")
    return [_finite(item, label) for item in value]


def _pose_error(actual: dict, expected: dict, *, xyzw: bool) -> tuple[float, float]:
    position = _vector(actual["position_m"], 3, "Position")
    target = _vector(expected["position_m"], 3, "Expected position")
    rotation = _vector(actual["orientation_xyzw" if xyzw else "orientation_wxyz"], 4, "Rotation")
    if xyzw:
        rotation = [rotation[3], *rotation[:3]]
    wanted = _vector(expected["orientation_wxyz"], 4, "Expected rotation")
    norms = math.hypot(*rotation), math.hypot(*wanted)
    _require(all(norm > 0 for norm in norms), "A retained rotation cannot be the zero quaternion.")
    a = [value / norms[0] for value in rotation]
    b = [value / norms[1] for value in wanted]
    minus = math.hypot(*(left - right for left, right in zip(a, b)))
    plus = math.hypot(*(left + right for left, right in zip(a, b)))
    return max(abs(left - right) for left, right in zip(position, target)), 4 * math.atan2(min(minus, plus), max(minus, plus))


def _sample_map(samples: list, *, time_key: str) -> dict:
    _require(isinstance(samples, list) and len(samples) == 7, "The frozen Rack needs seven distinct sample times.")
    result = {}
    for sample in samples:
        seconds = float(sample[time_key])
        _require(math.isfinite(seconds) and seconds not in result, "A retained sample time is invalid or repeated.")
        result[seconds] = sample
    return result


def _check_tolerances(value: dict) -> dict:
    limits = {"position_m": .001, "rotation_rad": .001, "time_seconds": .000001}
    for name, maximum in limits.items():
        _require(isinstance(value, dict), "Retained tolerances must be an object.")
        actual = _metric(value[name], maximum, "Tolerance " + name)
        _require(actual > 0, "A retained tolerance must be positive.")
    return {name: float(value[name]) for name in limits}


def _crosscheck_external_reports(roles: dict, checks: dict, implementation: dict, expected_program,
                                artifact_sha: str, root: Path) -> dict:
    """Cross-check recorded observations; do not rerun any external tool."""
    workflow, reference, external, viewer = (_json_file(roles[name][0]) for name in
                                            ("workflow", "reference", "external_results", "viewer_results"))
    revision, manifest = expected_program.program_revision, expected_program.manifest()
    for record, schema, revision_key in (
            (workflow, "ontokin.program-agent-workflow/0.1", "accepted_program_revision"),
            (reference, "ontokin.viewer-reference/0.2", "program_revision"),
            (viewer, "ontokin.visual-validation/0.2", "program_revision")):
        _require(record.get("schema_version") == schema, "A retained workflow/reference/viewer schema is unsupported.")
        _require(record.get(revision_key) == revision and record.get("source_manifest") == manifest
                 and record.get("artifact_sha256") == artifact_sha,
                 "A retained workflow/reference/viewer report identifies different program or artifact bytes.")
    _require(workflow.get("status") == "passed" and workflow.get("implementation") == implementation,
             "The actual workflow report failed or identifies a different implementation.")
    workflow_checks = workflow["checks"]
    _require(isinstance(workflow_checks, list) and workflow_checks
             and all(item.get("passed") is True for item in workflow_checks)
             and len(workflow_checks) == checks["workflow"]["checks"],
             "The actual workflow checks contradict the gate summary.")
    operations = workflow["operations"]
    _require(isinstance(operations, list) and operations
             and type(workflow["operation_count"]) is int
             and len(operations) == workflow["operation_count"] == checks["workflow"]["operations"],
             "The actual workflow operation count contradicts the gate summary.")
    operation_names, request_ids, rejected_edits, exports, chunks = set(), set(), [], [], []
    for operation in operations:
        request, response = operation["request"], operation["response"]
        _require(request["schema_version"] == response["schema_version"] == "ontokin.agent/0.2"
                 and all(request[name] == response[name] for name in ("operation", "request_id", "project_id")),
                 "A workflow response does not identify its actual request.")
        _require(request["request_id"] not in request_ids, "The workflow repeats a request identity.")
        request_ids.add(request["request_id"])
        name = request["operation"]
        operation_names.add(name)
        if response["status"] == "rejected":
            _require(name == "edit" and any(item["code"] == "OKL-E-UNIT" for item in response["diagnostics"]),
                     "The workflow contains an unaccounted rejected operation.")
            rejected_edits.append(response)
        else:
            _require(response["status"] == "succeeded", "A retained workflow operation did not succeed.")
        if name == "export":
            exports.append(response["result"])
        elif name == "artifact":
            chunks.append(response["result"])
    _require({"discover", "create", "inspect", "edit", "evaluate", "export", "artifact"} <= operation_names
             and len(rejected_edits) == 1 and len(exports) == 1 and chunks,
             "The retained workflow omits its authoring, rejected candidate, evaluation, or delivery path.")
    rejected = rejected_edits[0]
    _require(rejected["accepted_program_revision"] == workflow["initial_program_revision"]
             and rejected["program_revision"] == workflow["rejected_program_revision"]
             and len({revision, workflow["initial_program_revision"], workflow["rejected_program_revision"]}) == 3,
             "The rejected candidate did not preserve the original accepted program.")
    exported = exports[0]
    export_report = exported["report"]
    _require(exported["program_revision"] == revision and exported["source_manifest"] == manifest
             and exported["implementation"] == implementation and exported["sha256"] == artifact_sha
             and exported["destination"] == "ontokin.glb/0.2" and exported["achieved_level"] == "delivered"
             and exported["outcome"] == "valid" and exported["total_bytes"] == roles["artifact"][0].stat().st_size,
             "The workflow export result identifies different delivery bytes or an unsuccessful level.")
    _require(export_report["schema_version"] == "ontokin.glb-report/0.2"
             and export_report["target_contract"] == "ontokin.glb/0.2"
             and export_report["program_revision"] == revision and export_report["program"]["manifest"] == manifest
             and export_report["validation"]["status"] == "passed"
             and export_report["artifact"]["sha256"] == artifact_sha
             and "sha256:" + export_report["source_code_sha256"] == implementation["source_code_sha256"],
             "The actual export report is failed or disagrees with the implementation/program/artifact.")
    digest, offset = hashlib.sha256(), 0
    for index, chunk in enumerate(chunks):
        _require(chunk["program_revision"] == revision and chunk["sha256"] == artifact_sha
                 and chunk["artifact_id"] == exported["artifact_id"] and type(chunk["offset"]) is int
                 and chunk["offset"] == offset and chunk["total_bytes"] == exported["total_bytes"]
                 and chunk["mime_type"] == "model/gltf-binary", "A retrieved artifact chunk has inconsistent context.")
        data = base64.b64decode(chunk["data_base64"], validate=True)
        _require(0 < len(data) <= 65536, "A retained demonstration artifact chunk exceeds its requested bound.")
        digest.update(data)
        offset += len(data)
        _require(chunk["next_offset"] == (None if index == len(chunks) - 1 else offset),
                 "The retrieved artifact offsets are incomplete or discontinuous.")
    _require(offset == exported["total_bytes"] and "sha256:" + digest.hexdigest() == artifact_sha,
             "The actual workflow's retrieved chunks do not reproduce the artifact hash.")

    tolerances = _check_tolerances(reference["tolerances"])
    _require(_check_tolerances(export_report["tolerances"]) == tolerances,
             "The reference and export report use different tolerances.")
    oracle_identity = reference["independent_oracle"]
    oracle_path = _repository_file(oracle_identity["path"], root)
    _require(oracle_identity["path"] == "docs/language-design/construction-v0.1/01-keyed-rack/expected.json"
             and oracle_identity["sha256"] == file_identity(oracle_path)
             == file_identity(DEFAULT_FIXTURES / "01-keyed-rack/expected.json"),
             "The reference does not identify the predetermined independent Rack oracle.")
    oracle = _json_file(oracle_path)
    _require(oracle["program_revision"] == revision and reference["geometry"] == oracle["objects"]
             and len(oracle["objects"]) == 18, "The reference geometry differs from the independent oracle.")
    expected_samples = _sample_map(oracle["samples"], time_key="seconds")
    for sample in expected_samples.values():
        sample["objects"] = {item["path"]: {"position_m": item["position_m"],
                                          "orientation_wxyz": item["rotation_wxyz"]} for item in sample["objects"]}
    reference_samples = _sample_map(reference["samples"], time_key="time_seconds")
    _require(set(reference_samples) == set(expected_samples), "The reference omits an independent sample time.")
    maxima = [0., 0.]
    for seconds, sample in reference_samples.items():
        wanted = expected_samples[seconds]["objects"]
        _require(set(sample["objects"]) == set(wanted) and len(wanted) == 18,
                 "The reference omits or duplicates an object occurrence.")
        for name, pose in sample["objects"].items():
            errors = _pose_error(pose, wanted[name], xyzw=False)
            _require(max(errors) <= 1e-9, "An inspected reference pose differs from the independent formula oracle.")
            maxima = [max(left, right) for left, right in zip(maxima, errors)]
    _require(type(oracle_identity["pose_comparisons"]) is int and oracle_identity["pose_comparisons"] == 126,
             "The independent reference comparison count is not 126.")
    for name, observed in zip(("max_position_error_m", "max_rotation_error_rad"), maxima):
        _same_metric(oracle_identity[name], observed, "Reference " + name)

    _require(external.get("schema_version") == "ontokin.external-validation/0.1",
             "The retained independent format/Three.js schema is unsupported.")
    matching = [item for item in external["files"] if "sha256:" + item["sha256"] == artifact_sha]
    _require(len(matching) == 1, "The independent report must identify this exact artifact once.")
    loaded = matching[0]
    _require(loaded["program_revision"] == revision and loaded["source_manifest"] == manifest,
             "The independent loader report identifies a different program/source map.")
    validator = loaded["validator"]
    _require(all(type(validator[name]) is int and validator[name] == 0 for name in ("errors", "warnings"))
             and not any(item.get("severity") in (0, 1) for item in validator["messages"]),
             "The actual Khronos report contains errors or warnings.")
    geometry = loaded["geometry"]
    _require(isinstance(geometry, list) and len(geometry) == checks["geometry"]["objects"] == 18
             and {item["path"] for item in geometry} == {item["path"] for item in oracle["objects"]},
             "Independent geometry records do not cover all 18 occurrences.")
    expected_geometry = {item["path"]: item["geometry"] for item in oracle["objects"]}
    for item in geometry:
        expected = expected_geometry[item["path"]]
        sizes = expected["size_m"] if expected["kind"] == "box" else [2 * expected["radius_m"]] * 3
        actual = _vector(item["decoded_full_size_m"], 3, "Decoded geometry size")
        error = max(abs(left - right) for left, right in zip(actual, sizes))
        _require(item["status"] == "passed" and item["kind"] == expected["kind"]
                 and item["expected_full_size_m"] == sizes and error <= tolerances["position_m"],
                 "The independent mesh dimensions contradict their passed geometry summary.")
        _same_metric(item["max_dimension_error_m"], error, "Geometry dimension error")
    three = loaded["three_js"]
    comparison = three["comparison"]
    _require(three["loaded"] is True and comparison["status"] == "passed" and comparison["failures"] == []
             and _check_tolerances(comparison["tolerances"]) == tolerances,
             "The actual Three.js comparison is unavailable, failed, or uses different tolerances.")

    _require(viewer["status"] == "passed" and viewer["agent_implementation"] == implementation
             and "sha256:" + viewer["exporter_source_code_sha256"] == implementation["source_code_sha256"]
             and viewer["exporter"] == export_report["exporter"] and _check_tolerances(viewer["tolerances"]) == tolerances,
             "The actual browser report failed or identifies different engine/tolerance settings.")
    _require(isinstance(viewer["checks"], list) and len(viewer["checks"]) == checks["viewer"]["checks"]
             and all(isinstance(item, str) and item.strip() for item in viewer["checks"])
             and all(viewer[name] == [] for name in ("page_errors", "console_errors", "network_requests", "failed_requests"))
             and not viewer.get("failure"), "The actual browser checks or error records contradict the summary.")
    pose_results = {}
    for label, samples, count in (("Three.js", three["samples"], comparison["object_pose_comparisons"]),
                                  ("viewer", viewer["samples"], viewer["pose_comparisons"])):
        decoded = _sample_map(samples, time_key="time_seconds")
        _require(set(decoded) == set(reference_samples), label + " omits an independent sample time.")
        maxima, total = [0., 0.], 0
        for seconds, sample in decoded.items():
            wanted = reference_samples[seconds]["objects"]
            _require(set(sample["objects"]) == set(wanted), label + " omits an object occurrence.")
            if label == "viewer":
                _require(abs(_finite(sample["displayed_time_seconds"], "Browser time") - seconds) <= tolerances["time_seconds"],
                         "The browser displayed a different time from the requested sample.")
            for name, pose in sample["objects"].items():
                errors = _pose_error(pose, wanted[name], xyzw=True)
                _require(errors[0] <= tolerances["position_m"] and errors[1] <= tolerances["rotation_rad"],
                         label + " retained poses violate their declared tolerance.")
                maxima = [max(left, right) for left, right in zip(maxima, errors)]
                total += 1
                if label == "viewer":
                    _require(pose["expected_position_m"] == wanted[name]["position_m"]
                             and pose["expected_orientation_wxyz"] == wanted[name]["orientation_wxyz"],
                             "The browser used different expected poses from the retained reference.")
                    oracle_errors = _pose_error(pose, expected_samples[seconds]["objects"][name], xyzw=True)
                    for key, observed in zip(("position_error_m", "rotation_error_rad", "oracle_position_error_m", "oracle_rotation_error_rad"),
                                             (*errors, *oracle_errors)):
                        _same_metric(pose[key], observed, "Browser " + key)
        summary = checks["motion" if label == "Three.js" else "viewer"]
        _require(type(count) is int and count == total == summary["pose_comparisons"] == 126,
                 label + " pose comparison count contradicts its actual retained samples.")
        pose_results[label] = {"samples": len(decoded), "pose_comparisons": total,
                               "max_position_error_m": maxima[0], "max_rotation_error_rad": maxima[1]}
        if label == "Three.js":
            _require(type(comparison["sample_count"]) is int and comparison["sample_count"] == len(decoded),
                     "The Three.js sample count contradicts its retained samples.")
            for key, observed in zip(("max_position_error_m", "max_rotation_error_rad"), maxima):
                _same_metric(comparison[key], observed, "Three.js " + key)
                _same_metric(summary[key], observed, "Gate motion " + key)

    capture = [item for item in viewer["captures"] if item.get("sha256") == roles["capture"][1]]
    _require(len(capture) == 1 and capture[0]["file"] == roles["capture"][0].name
             and capture[0]["program_revision"] == revision and capture[0]["artifact_sha256"] == artifact_sha,
             "The browser report does not identify the reviewed capture and its exact program/artifact.")
    provenance = viewer["provenance"]
    aliases = {"source_bundle": "source_bundle", "glb": "artifact", "reference": "reference", "workflow": "workflow"}
    required = set(aliases) | {"entry_source", "library_source", "export_report", "oracle", "viewer_html", "viewer_bundle",
                               "viewer_builtin_data", "verifier", "tooling_lock"}
    _require(isinstance(provenance, dict) and required <= set(provenance), "The browser provenance omits source or rendering inputs.")
    provenance_files = {}
    for name, record in provenance.items():
        file = _repository_file(record["path"], root)
        _require(type(record["byte_length"]) is int and file.stat().st_size == record["byte_length"]
                 and file_identity(file) == record["sha256"], "The browser's retained " + name + " bytes changed.")
        if name in aliases:
            _require(file == roles[aliases[name]][0], "The browser used different " + name + " provenance.")
        provenance_files[name] = file
    _require(provenance_files["oracle"] == oracle_path
             and _json_file(provenance_files["export_report"]) == export_report
             and provenance_files["entry_source"].read_bytes() == expected_program.entry.raw
             and len(expected_program.modules) == 1
             and provenance_files["library_source"].read_bytes() == expected_program.modules[0].raw,
             "The browser source/export provenance disagrees with the frozen program or workflow.")
    return {"workflow_checks": len(workflow_checks), "workflow_operations": len(operations),
            "retrieved_artifact_bytes": offset, "reference_poses": 126, "geometry_objects": len(geometry),
            "validator_errors": validator["errors"], "validator_warnings": validator["warnings"],
            "pose_observations": pose_results, "browser_input_files": len(provenance_files),
            "basis": "Cross-checked identities, statuses, counts, declared tolerances and arithmetic of retained reports; no external tools re-executed."}


def verify_external_evidence(path: Path | None, *, implementation: dict, expected_program,
                             root: Path = ROOT) -> dict:
    """Verify retained evidence identities without claiming external tool execution."""
    result = {"id": "identified_visual_delivery", "status": "pending", "executed_external_tools": False,
              "basis": "Identity/provenance verification of a retained external run; this function does not execute those tools.",
              "manifest": None if path is None else str(Path(path)), "issues": [], "verified_provenance": []}
    issues = result["issues"]
    if path is None:
        issues.append("No identified external evidence manifest was supplied.")
        return result
    try:
        path = Path(path)
        evidence = _json_file(path)
        result["manifest_sha256"] = file_identity(path)
        if evidence.get("schema_version") != "ontokin.construction-external-gate/0.1":
            issues.append("The external evidence schema is unsupported.")
        if evidence.get("implementation") != implementation:
            issues.append("The external run does not match the current implementation identity.")
        if evidence.get("program_revision") != expected_program.program_revision:
            issues.append("The external run does not identify the frozen Rack program.")
        if evidence.get("source_manifest") != expected_program.manifest():
            issues.append("The external source map differs from the frozen Rack's exact source manifest.")
        artifact_sha = evidence.get("artifact_sha256")
        if not isinstance(artifact_sha, str) or _SHA.fullmatch(artifact_sha) is None:
            issues.append("The external artifact identity is not an exact SHA-256 digest.")
        records = evidence.get("provenance")
        if not isinstance(records, list):
            raise ValueError("External provenance must be an array of identified files.")
        roles = {}
        for record in records:
            role = record.get("role")
            if role not in _ROLES or role in roles:
                raise ValueError("External provenance roles must be recognized and unique.")
            claimed = record.get("sha256")
            if not isinstance(claimed, str) or _SHA.fullmatch(claimed) is None:
                raise ValueError("External provenance requires exact SHA-256 digests.")
            file = _repository_file(record["path"], root)
            actual = file_identity(file)
            roles[role] = (file, actual)
            result["verified_provenance"].append({"role": role, "path": _relative(file, root),
                                                   "claimed_sha256": claimed, "actual_sha256": actual,
                                                   "matches": actual == claimed})
            if actual != claimed:
                issues.append("The retained " + role + " file hash does not match the external manifest.")
        if set(roles) != _ROLES:
            issues.append("Required external provenance is missing: " + ", ".join(sorted(_ROLES - set(roles))))
        if "artifact" in roles:
            if roles["artifact"][1] != artifact_sha:
                issues.append("The retained artifact bytes do not match artifact_sha256.")
            metadata = _glb_identity(roles["artifact"][0])
            if metadata.get("target_contract") != "ontokin.glb/0.2" or metadata.get("profile") != "construction-0.1":
                issues.append("The actual GLB does not retain the authored construction profile and destination contract.")
            program = metadata.get("program", {})
            if program.get("revision") != expected_program.program_revision or program.get("manifest") != expected_program.manifest():
                issues.append("The actual GLB does not retain the frozen whole-program identity and source map.")
        if "source_bundle" in roles:
            source = load_bundle(_json_file(roles["source_bundle"][0]))
            if source.program_revision != expected_program.program_revision or source.manifest() != expected_program.manifest():
                issues.append("The retained source bundle differs from the frozen program.")
        checks = evidence.get("checks", {})
        if set(checks) != {"workflow", "format", "geometry", "motion", "viewer"}:
            issues.append("The external gate needs exactly the workflow, format, geometry, motion, and viewer checks.")
        for name in ("workflow", "format", "geometry", "motion", "viewer"):
            if not isinstance(checks.get(name), dict) or checks[name].get("status") != "passed":
                issues.append("The retained " + name + " check has not passed.")
        def integer(name, key, minimum=None, exact=None):
            value = checks.get(name, {}).get(key)
            if type(value) is not int or (minimum is not None and value < minimum) or (exact is not None and value != exact):
                issues.append(f"The retained {name}.{key} count does not meet the required evidence boundary.")
        integer("workflow", "checks", minimum=1)
        integer("workflow", "operations", minimum=1)
        integer("format", "errors", exact=0)
        integer("format", "warnings", exact=0)
        integer("geometry", "objects", exact=18)
        integer("motion", "pose_comparisons", minimum=126)
        integer("viewer", "checks", minimum=1)
        integer("viewer", "pose_comparisons", minimum=126)
        for key in ("max_position_error_m", "max_rotation_error_rad"):
            value = checks.get("motion", {}).get(key)
            if type(value) not in (int, float) or not 0 <= value <= .001 or not math.isfinite(value):
                issues.append("The retained motion." + key + " exceeds its finite tolerance or is unavailable.")
        viewer = checks.get("viewer", {})
        review = viewer.get("visual_review", {})
        if (review.get("status") != "reviewed"
                or not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip()
                or not isinstance(review.get("observation"), str) or not review["observation"].strip()):
            issues.append("No identified human/agent visual review of the actual capture was recorded.")
        if "capture" in roles and viewer.get("capture_sha256") != roles["capture"][1]:
            issues.append("The visual review capture identity differs from the retained capture bytes.")
        result["recorded_checks"] = checks
        result["artifact_sha256"] = artifact_sha
        result["program_revision"] = evidence.get("program_revision")
        if not issues:
            result["crosschecked_reports"] = _crosscheck_external_reports(
                roles, checks, implementation, expected_program, artifact_sha, root)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError, OverflowError) as error:
        issues.append(f"External evidence could not be verified: {type(error).__name__}: {error}")
    if not issues:
        result["status"] = "passed"
    return result


def run_conformance(*, case_ids=None, external_evidence: Path | None = None) -> dict:
    """Run selected adopted cases; a full C gate needs all twenty and external evidence."""
    manifest = load_manifest()
    selected = {case["id"] for case in manifest["cases"]} if case_ids is None else set(case_ids)
    if not selected or selected - {case["id"] for case in manifest["cases"]}:
        raise ValueError("Select one or more adopted construction case IDs C01-C20.")
    cases = [case for case in manifest["cases"] if case["id"] in selected]
    required = sorted({name for case in cases for name in case["required_tests"]})
    implementation = implementation_identity()
    inventory = _evidence_inventory(DEFAULT_FIXTURES)
    fixtures = _fixture_records(manifest, DEFAULT_FIXTURES)
    execution = _run_tests(required)
    records = {record["test_id"]: record for record in execution["tests"]}
    frozen = load_bundle(_json_file(DEFAULT_FIXTURES / "01-keyed-rack/program.bundle.json"))
    external = verify_external_evidence(external_evidence, implementation=implementation, expected_program=frozen)
    after = implementation_identity()
    stable = after == implementation and _evidence_inventory(DEFAULT_FIXTURES) == inventory
    run_issues = []
    if not stable:
        run_issues.append("Implementation, test, fixture, or contract bytes changed during this run; rerun after freezing them.")
    if execution["loader_errors"] or execution["fixture_errors"] or execution["unexpected_test_records"]:
        run_issues.append("The unittest loader or class/module fixtures reported errors or unexpected execution identities.")
    if execution["tests_run"] != len(required):
        run_issues.append("The number of executed unittest methods differs from the deduplicated required set.")
    module_manifest = _json_file(DEFAULT_FIXTURES / manifest["module_subset"])
    module_cases = {case["case_id"]: case for case in module_manifest["cases"]}
    results = []
    failed_states = {"failed", "error", "unexpected_success", "expected_failure"}
    for case in cases:
        selected_tests = [records[name] for name in case["required_tests"]]
        pending = list(case.get("unbound_requirements", []))
        if any(record["status"] not in failed_states | {"passed"} for record in selected_tests):
            pending.append("At least one required test was skipped or did not execute.")
        if case["external_gates"] and external["status"] != "passed":
            pending.append("The identified independent visual-delivery gate is pending.")
        pending += run_issues
        status = ("failed" if any(record["status"] in failed_states for record in selected_tests)
                  else "pending" if pending else "passed")
        subset = module_cases.get(case["module_subset_case"])
        results.append({"id": case["id"], "title": case["title"], "requirements": case["requirements"],
                        "expected": case["expected"], "status": status,
                        "required_tests": case["required_tests"],
                        "test_outcomes": dict(sorted(Counter(record["status"] for record in selected_tests).items())),
                        "module_scenario_expectations": [] if subset is None else subset["scenarios"],
                        "external_gates": case["external_gates"], "pending_reasons": pending})
    counts = Counter(case["status"] for case in results)
    complete = len(results) == 20 and counts["passed"] == 20 and not run_issues
    return {"schema_version": "ontokin.construction-conformance/0.1", "executed": True,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(), "implementation": implementation,
            "implementation_after_run": after, "evidence_stable_during_run": stable,
            "environment": {"python": platform.python_version(), "python_implementation": platform.python_implementation(),
                            "platform": platform.platform()},
            "language_version": manifest["language_version"], "profile": manifest["profile"],
            "agent_contract": manifest["agent_contract"], "delivery_contract": manifest["delivery_contract"],
            "manifest": {"path": _relative(DEFAULT_FIXTURES / "validation-cases.json"),
                         "sha256": file_identity(DEFAULT_FIXTURES / "validation-cases.json"),
                         "expectation_status": manifest["status"]},
            "module_manifest": {"path": _relative(DEFAULT_FIXTURES / manifest["module_subset"]),
                                "sha256": file_identity(DEFAULT_FIXTURES / manifest["module_subset"])},
            "settings": manifest["settings"], "fixtures": fixtures, "evidence_files": inventory,
            "scope": "Selected C01-C20 requirements measured through distinct real unittest methods and identified retained external evidence. This report does not certify the whole Python suite, remote CI, every legacy external destination, or the full product.",
            "full_product_conformance_certified": False,
            "summary": {"total": len(results), "passed": counts["passed"], "failed": counts["failed"],
                        "pending": counts["pending"], "all_adopted_cases_selected": len(results) == 20,
                        "case_gate_complete": complete},
            "cases": results, "test_execution": execution, "external_evidence": external,
            "run_issues": run_issues, "additional_release_gates": manifest["additional_release_gates"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write the measured report as JSON")
    parser.add_argument("--case", action="append", choices=[f"C{i:02}" for i in range(1, 21)], help="Select an adopted case; repeatable")
    parser.add_argument("--external-evidence", type=Path, help="Verify a retained external-gate manifest for C20")
    args = parser.parse_args(argv)
    report = run_conformance(case_ids=args.case, external_evidence=args.external_evidence)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(args.output), "summary": report["summary"],
                          "unique_tests": report["test_execution"]["unique_required"]}, indent=2))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    # Pending acceptance is distinct from a measured failed expectation.
    return 1 if report["summary"]["failed"] or report["run_issues"] else 2 if report["summary"]["pending"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
