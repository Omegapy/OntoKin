"""Execute adopted M01--M12 checks and audit identified release evidence.

The acceptance corpus and coverage mapping are expectations, never execution
results. Unittest methods execute once. Reading retained source, GLB, browser,
regression or GitHub reports does not execute those external tools. Every gate
keeps missing or contradictory evidence pending, including current C20 and CI.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import unittest

from .bundle import ProgramBundle, SourceUnit, load_bundle
from . import construction_conformance as legacy

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs/language-design/surface-v0.1"
MAPPING_SHA256 = 'sha256:64c8ae3459869a42fe0f51f05503d3a4b9f06d503d164a93d04b04d7e89e6461'
GATES = ("workflow", "destination", "browser", "regression", "ci")
SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
file_identity = legacy.file_identity
implementation_identity = legacy.implementation_identity
_json_file = legacy._json_file
_require = legacy._require
_finite = legacy._finite
_metric = legacy._metric
_vector = legacy._vector
_run_tests = legacy._run_tests


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def _identified(record: dict, root: Path) -> Path:
    _require(isinstance(record, dict) and isinstance(record.get("sha256"), str)
             and SHA.fullmatch(record["sha256"]) is not None,
             "Every evidence file needs an exact SHA-256 identity.")
    path = legacy._repository_file(record["path"], root)
    _require(file_identity(path) == record["sha256"], "Evidence file bytes changed: " + record["path"])
    return path


def _nested(path_value: str, claimed: str, root: Path) -> Path:
    return _identified({"path": path_value, "sha256": claimed}, root)


def load_manifest(directory: Path = FIXTURES) -> dict:
    mapping_path = Path(directory) / "conformance.json"
    _require(file_identity(mapping_path) == MAPPING_SHA256, "The reviewed conformance mapping bytes changed; update its versioned identity explicitly.")
    manifest = _json_file(mapping_path)
    _require(manifest.get("schema_version") == "ontokin.surface-conformance-map/0.1",
             "Unknown surface conformance mapping schema.")
    _require(manifest.get("status") == "predetermined_expectations_not_execution_results",
             "The mapping must contain predetermined expectations, not pass claims.")
    acceptance_path = _identified(manifest["acceptance_manifest"], ROOT)
    composition_path = _identified(manifest["composition_manifest"], ROOT)
    acceptance, composition = _json_file(acceptance_path), _json_file(composition_path)
    _require(acceptance.get("schema") == "ontokin.acceptance/surface-0.1",
             "The adopted surface acceptance corpus is missing.")
    for key in ("limits", "tolerance"):
        _require(manifest[key] == acceptance[key], "The coverage mapping changed adopted " + key + ".")
    _require(manifest["source_pin"] == acceptance["source_bundle"]
             and manifest["normative_contract"] == acceptance["normative_contract"],
             "The adopted source or specification identity changed.")
    _require(composition["schema_version"] == "ontokin.surface-compositions/0.1"
             and composition["acceptance_manifest_sha256"] == file_identity(acceptance_path)
             and composition["generated_part_counts"] == [1, 3, 7],
             "The predetermined composition and generated-count dependency changed.")
    expected = [f"M{i:02}" for i in range(1, 13)]
    _require([c.get("id") for c in manifest["cases"]] == expected
             and [c.get("id") for c in acceptance["cases"]] == expected,
             "Adopted M01--M12 must appear once, in order.")
    for case in manifest["cases"]:
        names = case["required_tests"]
        _require(isinstance(names, list) and names and len(names) == len(set(names))
                 and all(isinstance(n, str) and legacy._TEST_ID.fullmatch(n) for n in names),
                 "Every mapped case requires distinct concrete unittest methods.")
        _require(not set(case["external_gates"]) - set(GATES), "Unknown release evidence gate.")
    for name in ("mandatory_native_fixtures", "mandatory_workflow_checks", "mandatory_browser_fixtures"):
        values = manifest[name]
        _require(isinstance(values, list) and values and len(values) == len(set(values)),
                 "Mandatory evidence identities must be nonempty and unique.")
    _require(set(manifest["mandatory_browser_fixtures"]) <= set(manifest["mandatory_native_fixtures"]),
             "A browser fixture must identify a native source artifact.")
    return manifest


def evidence_inventory() -> list[dict]:
    """Current reproducible inputs; generated evidence directories are excluded."""
    paths = set()
    for folder in (ROOT / "ontokin", ROOT / "tests", ROOT / "tools"):
        for path in folder.rglob("*"):
            if path.is_file() and not {"__pycache__", "node_modules"}.intersection(path.parts) \
                    and path.suffix in {".py", ".mjs", ".json", ".ok", ".html"}:
                paths.add(path)
    paths.update((ROOT / ".github/workflows").glob("*.yml"))
    paths.update((ROOT / ".github/workflows").glob("*.yaml"))
    if (ROOT / "pyproject.toml").is_file():
        paths.add(ROOT / "pyproject.toml")
    design = ROOT / "docs/language-design"
    paths.update(design.glob("OK-LANG-*.md"))
    for name in ("core-v0.1", "construction-v0.1", "surface-v0.1", "agent-v0.1", "agent-v0.2", "agent-v0.3"):
        for path in (design / name).rglob("*"):
            # Validation history is independently hash-bound by the external
            # manifest, and must not make a new report invalidate its own run.
            if path.is_file() and not {"__pycache__", "evidence", "validation"}.intersection(path.parts) \
                    and path.suffix in {".py", ".ok", ".json", ".md", ".html", ".mjs"}:
                paths.add(path)
    return [{"path": path.relative_to(ROOT).as_posix(), "sha256": file_identity(path)}
            for path in sorted(paths)]


def inventory_identity(records: list[dict]) -> str:
    return digest(_canonical(records))


def discover_test_ids() -> list[str]:
    """Use actual default repository discovery, preserving loader failures."""
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern="test*.py")
    def flatten(item):
        if isinstance(item, unittest.TestSuite):
            for child in item:
                yield from flatten(child)
        else:
            yield item.id()
    names = list(flatten(suite))
    _require(not loader.errors, "Full-suite discovery has loader errors: " + repr(loader.errors))
    _require(names and len(names) == len(set(names)), "Discovery must identify unique executable tests.")
    return sorted(names)


def _execution_passes(execution: dict, names: list[str]) -> bool:
    records = execution.get("tests", [])
    return (execution.get("unique_required") == len(names)
            and execution.get("tests_run") == len(names)
            and not execution.get("loader_errors") and not execution.get("fixture_errors")
            and not execution.get("unexpected_test_records")
            and len(records) == len(names)
            and sorted(r.get("test_id", "") for r in records) == sorted(names)
            and all(r.get("status") == "passed" and not r.get("failures") for r in records)
            and execution.get("outcomes") == {"passed": len(names)})


def run_full_suite() -> dict:
    before, implementation = evidence_inventory(), implementation_identity()
    names = discover_test_ids()
    execution = _run_tests(names)
    stable = before == evidence_inventory() and implementation == implementation_identity()
    missing = sorted(set(load_manifest()["regression_required_test_ids"])-set(names))
    passed = _execution_passes(execution, names) and stable and not missing
    return {"schema_version": "ontokin.unittest-execution/0.1", "executed": True,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "implementation": implementation, "evidence_files": before,
            "evidence_inventory_sha256": inventory_identity(before), "expected_test_ids": names,
            "test_execution": execution, "evidence_stable_during_run": stable,
            "missing_frozen_regression_test_ids": missing,
            "summary": {"total": len(names), "passed": sum(r["status"] == "passed" for r in execution["tests"]),
                        "all_passed": passed}, "full_product_conformance_certified": False}


def _gate(name: str, action) -> dict:
    result = {"id": name, "status": "pending", "executed_external_tools": False, "issues": []}
    try:
        result["verified"] = action()
        result["status"] = "passed"
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, RuntimeError, OverflowError, struct.error, subprocess.SubprocessError) as error:
        result["issues"].append(str(error) or type(error).__name__)
    return result


def _source_bundle(path: Path) -> ProgramBundle:
    program = load_bundle(_json_file(path))
    for unit in program.units:
        source = legacy._repository_file(unit.filename, path.parent)
        _require(source.read_bytes() == unit.raw, "The bundle differs from retained raw source " + unit.filename)
    return program


def _expected_fixtures() -> dict:
    """Read authored scalar/source generators; no compiled or Python mesh input."""
    from tools.build_surface_demo import fixture_cases
    values = {name: {"program": program, "oracle": oracle} for name, program, oracle in fixture_cases()}
    values["studio-original"] = values.pop("studio")
    composition = _json_file(FIXTURES / "compositions/expected.json")
    library = values["studio-original"]["program"].modules[0]
    for fixture in composition["fixtures"]:
        path = FIXTURES / "compositions" / fixture["entry"]
        _require(file_identity(path) == fixture["entry_sha256"], "A fixed composition source changed.")
        program = ProgramBundle(SourceUnit("entry", fixture["entry"], path.read_bytes()), (library,))
        _require(program.program_revision == fixture["program_revision"], "A fixed composition revision changed.")
        values[fixture["id"]] = {"program": program, "oracle": fixture["oracle"]}
    previous = copy.deepcopy(values["studio-original"]["oracle"])
    rules = composition["workflow"]
    next(s for s in previous["shapes"][1]["sections"] if s["key"] == "middle")["radii_xy_m"][0] = rules["repaired_radius_x_m"]
    values["radius-repaired"] = {"oracle": copy.deepcopy(previous)}
    previous["shapes"][1]["materials"][rules["palette_region"]] = rules["palette_after"]
    values["palette-repaired"] = {"oracle": copy.deepcopy(previous)}
    previous["shapes"][1]["sections"].append(rules["inserted_section"])
    previous["shapes"][1]["sections"].sort(key=lambda s: s["station_m"])
    previous["shapes"][1]["expected"] = {"triangles": rules["inserted_triangles"], "vertices": 3 * rules["inserted_triangles"]}
    values["inserted"] = {"oracle": copy.deepcopy(previous)}
    values["reordered"] = {"oracle": copy.deepcopy(previous)}
    values["removed"] = {"oracle": copy.deepcopy(values["palette-repaired"]["oracle"])}
    return values


def _check_oracle(actual: dict, expected: dict):
    for group in ("shapes", "empty_objects"):
        observed, wanted = actual.get(group, []), expected.get(group, [])
        _require(len(observed) == len(wanted), "A source oracle has the wrong object count.")
        by_path = {s["path"]: s for s in observed}
        _require(len(by_path) == len(observed) and set(by_path) == {s["path"] for s in wanted},
                 "A source oracle changed the fixed object identities.")
        for shape in wanted:
            found = by_path[shape["path"]]
            for key in ("element_id", "sections", "materials", "facets", "caps", "local_position_m",
                        "local_rotation_wxyz", "motion"):
                if key in shape:
                    _require(found.get(key) == shape[key], "A retained oracle changed predetermined " + key + " for " + shape["path"])
            _require(found.get("physical_kind", "no_body") == shape.get("physical_kind", "no_body"),
                     "A retained oracle changed physical participation.")


def _patched_program(program: ProgramBundle, patches: list[dict]) -> ProgramBundle:
    by_id = {unit.source_id: unit for unit in program.units}
    changes = {}
    for patch in patches:
        unit = by_id[patch["source_id"]]
        _require(patch["source_revision"] == unit.revision, "A workflow patch has a stale source precondition.")
        start, end = patch["start_byte"], patch["end_byte"]
        _require(type(start) is int and type(end) is int and 0 <= start <= end <= len(unit.raw),
                 "A workflow patch has invalid byte offsets.")
        unit.raw[:start].decode("utf-8"); unit.raw[:end].decode("utf-8")
        _require(unit.raw[start:end] == patch["expected_text"].encode("utf-8"),
                 "A workflow patch did not name the exact previous bytes.")
        changes.setdefault(unit.source_id, []).append(patch)
    replaced = []
    for unit in program.units:
        raw, last_start = unit.raw, len(unit.raw) + 1
        for patch in sorted(changes.get(unit.source_id, []), key=lambda p: p["start_byte"], reverse=True):
            _require(patch["end_byte"] <= last_start, "Retained source patches overlap.")
            raw = raw[:patch["start_byte"]] + patch["replacement"].encode("utf-8") + raw[patch["end_byte"]:]
            last_start = patch["start_byte"]
        replaced.append(SourceUnit(unit.source_id, unit.filename, raw, unit.package_id, unit.version))
    return ProgramBundle(replaced[0], tuple(replaced[1:]))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _rotate(point, quaternion):
    q = _vector(quaternion, 4, "Quaternion")
    size = math.hypot(*q)
    _require(size > 0, "A scalar source rotation cannot be zero.")
    w, *axis = [v / size for v in q]
    twice = [2 * v for v in _cross(axis, point)]
    correction = _cross(axis, twice)
    return [p + w * t + c for p, t, c in zip(point, twice, correction)]


def _analytic_triangles(shape: dict) -> list[tuple]:
    """Independent scalar oracle: rings, oriented sides, alternating end caps."""
    sections = sorted(shape["sections"], key=lambda s: s["station_m"])
    n = shape["facets"]
    rings = [[[s["center_xy_m"][0] + s["radii_xy_m"][0] * math.cos(2 * math.pi * j / n),
               s["center_xy_m"][1] + s["radii_xy_m"][1] * math.sin(2 * math.pi * j / n), s["station_m"]]
              for j in range(n)] for s in sections]
    faces = []
    for i in range(len(sections) - 1):
        for j in range(n):
            a, b, c, d = rings[i][j], rings[i][(j + 1) % n], rings[i + 1][j], rings[i + 1][(j + 1) % n]
            faces.extend([(sections[i]["region"], [a, b, c]), (sections[i]["region"], [b, d, c])])
    if shape["caps"] == "flat":
        for j in range(n):
            faces.append((sections[0]["region"], [[*sections[0]["center_xy_m"], sections[0]["station_m"]], rings[0][(j + 1) % n], rings[0][j]]))
            faces.append((sections[-1]["region"], [[*sections[-1]["center_xy_m"], sections[-1]["station_m"]], rings[-1][j], rings[-1][(j + 1) % n]]))
    result = []
    for region, points in faces:
        ab = [b - a for a, b in zip(points[0], points[1])]
        ac = [c - a for a, c in zip(points[0], points[2])]
        normal = _cross(ab, ac)
        size = math.hypot(*normal)
        _require(size > 0, "A fixed oracle triangle is degenerate.")
        normal = _rotate([v / size for v in normal], shape["local_rotation_wxyz"])
        positioned = [[v + offset for v, offset in zip(_rotate(p, shape["local_rotation_wxyz"]), shape["local_position_m"])] for p in points]
        result.append((region, positioned, normal))
    return result


def _vector_error(actual, expected, tolerance, label):
    values = _vector(actual, len(expected), label)
    error = max(abs(a - b) for a, b in zip(values, expected))
    _metric(error, tolerance, label)
    return error


def _verify_workflow(record: dict, evidence_root: Path, implementation: dict, manifest: dict, context: dict) -> dict:
    path = _identified(record, evidence_root)
    report = _json_file(path)
    root = path.parent
    _require(report.get("schema_version") == "ontokin.surface-agent-workflow/0.1"
             and report.get("implementation") == implementation and report.get("status") == "passed"
             and report.get("error") is None, "The source workflow belongs to a different implementation.")
    _require(report["builder_sha256"] == file_identity(ROOT / "tools/build_surface_agent_demo.py"),
             "The workflow builder is stale.")
    _require(report["acceptance_manifest_sha256"] == manifest["acceptance_manifest"]["sha256"]
             and report["composition_manifest_sha256"] == manifest["composition_manifest"]["sha256"],
             "The workflow did not use the fixed acceptance/composition sources.")
    snapshots = {}
    for snapshot in report["snapshots"]:
        bundle_path = _nested(snapshot["bundle_file"], snapshot["bundle_sha256"], root)
        program = load_bundle(_json_file(bundle_path))
        key = (snapshot["project_id"], snapshot["program_revision"])
        _require(key not in snapshots and key[1] == program.program_revision,
                 "Workflow snapshots must identify exact, unique program revisions.")
        source_manifest = _nested(snapshot["source_manifest_file"], snapshot["source_manifest_sha256"], root)
        _require(_json_file(source_manifest) == program.manifest(), "A snapshot source manifest changed.")
        units = {u["source_id"]: u for u in snapshot["units"]}
        _require(len(units) == len(snapshot["units"]) == len(program.units), "A snapshot lost or duplicated a source unit.")
        for unit in program.units:
            item = units[unit.source_id]
            source = _nested(item["file"], item["sha256"], root)
            _require(source.read_bytes() == unit.raw and item["source_revision"] == unit.revision
                     and item["filename"] == unit.filename and item["byte_length"] == len(unit.raw)
                     and item.get("package_id") == unit.package_id and item.get("version") == unit.version,
                     "Snapshot source identity disagrees with exact retained UTF-8 bytes.")
        _require(type(snapshot["accepted_once"]) is bool, "accepted_once must be a measured Boolean.")
        snapshots[key] = (program, snapshot["accepted_once"])
    exchanges, accepted, accepted_once, pages = {}, {}, set(), {}
    previous_sequence = -1
    from .program_protocol import bind
    protocol = bind("ontokin.agent/0.3")
    from .agent_protocol import ProtocolError
    for item in report["exchanges"]:
        _require(type(item["sequence"]) is int and item["sequence"] > previous_sequence,
                 "Workflow exchange order must be explicit and strictly increasing.")
        previous_sequence = item["sequence"]
        request = _json_file(_nested(item["request_file"], item["request_sha256"], root))
        response = _json_file(_nested(item["response_file"], item["response_sha256"], root))
        try:
            protocol.validate_request(request)
        except ProtocolError as error:
            raise ValueError("A retained workflow request violates the actual Agent/0.3 contract: " + str(error)) from error
        project, operation = request["project_id"], request["operation"]
        key = (project, request["request_id"])
        _require((project, request["request_id"], operation) == (item["project_id"], item["request_id"], item["operation"]),
                 "An exchange index relabelled its actual request.")
        _require(response["schema_version"] == "ontokin.agent/0.3" and response["operation"] == operation
                 and response["project_id"] == project and response["request_id"] == request["request_id"],
                 "A retained response does not answer its exact native protocol request.")
        if key in exchanges:
            _require(exchanges[key] == (request, response), "An idempotent retry changed its request or response.")
            continue
        exchanges[key] = (request, response)
        candidate = None
        if operation == "create":
            candidate = load_bundle(request["bundle"])
        elif operation == "edit" and request["expected_program_revision"] == accepted.get(project):
            base = snapshots[(project, request["expected_program_revision"])][0]
            _require(not request.get("module_changes"), "This fixed workflow only edits occurrence source bytes.")
            candidate = _patched_program(base, request["patches"])
        if candidate is not None and response.get("program_revision") is not None:
            _require(candidate.program_revision == response["program_revision"], "The edit response names different source bytes.")
            _require(snapshots[(project, candidate.program_revision)][0].to_payload() == candidate.to_payload(),
                     "The candidate snapshot is not the exact requested source edit.")
        if response["status"] == "succeeded":
            _require(response["result"].get("implementation") == implementation,
                     "A workflow response was generated by different implementation bytes.")
            if operation in {"create", "edit"}:
                _require(request["expected_program_revision"] == accepted.get(project), "A stale request changed the accepted head.")
                accepted[project] = response["program_revision"]
                accepted_once.add((project, response["program_revision"]))
            elif operation in {"surface.mesh_page", "export", "evaluate"}:
                _require((project, request["program_revision"]) in accepted_once,
                         "A never-accepted candidate was paged, evaluated or delivered.")
        _require(response.get("accepted_program_revision") == accepted.get(project),
                 "A response changed or misreported the accepted head.")
        if operation == "surface.mesh_page" and response["status"] == "succeeded":
            page = response["result"]
            _require(page["schema_version"] == "ontokin.surface-mesh-page/0.1"
                     and page["program_revision"] == request["program_revision"]
                     and page["element_id"] == request["element_id"]
                     and page["coordinate_system"] == "carrier_local_after_placement/0.1"
                     and page["ordering"] == "native_triangle_ordinal/0.1"
                     and page["profile"] == "surface-0.1", "A mesh page lost source identity or coordinate semantics.")
            count = page["returned_triangles"]
            _require(type(count) is int and 0 <= count <= request["count"] <= 256
                     and len(page["positions_m"]) == len(page["normals"]) == 3 * count
                     and len(page["triangles"]) == len(page["region_keys"]) == len(page["source_triangle_ordinals"]) == count,
                     "Mesh pagination split triangles or exceeded its requested count.")
            _require(page["triangles"] == [[3*i, 3*i+1, 3*i+2] for i in range(count)],
                     "Page-local triangle indices are inconsistent.")
            _require(response["requested_level"] is None and response["achieved_level"] == "constructed"
                     and response["run_id"] is None, "Mesh inspection acquired a run or wrong assurance level.")
            if page["region"] is None:
                page_key = (project, request["program_revision"], tuple(page["element_id"]))
                collected = pages.setdefault(page_key, {"triangles": {}, "total": page["total_triangles"], "digest": page["geometry_sha256"]})
                _require(collected["total"] == page["total_triangles"] == page["filtered_triangles"]
                         and collected["digest"] == page["geometry_sha256"], "A mesh cursor crossed geometry identities.")
                ordinals = page["source_triangle_ordinals"]
                _require(ordinals == list(range(page["offset"], page["offset"] + count)), "An unfiltered page changed native triangle ordinals.")
                for i, ordinal in enumerate(ordinals):
                    face = (page["region_keys"][i], page["positions_m"][3*i:3*i+3], page["normals"][3*i:3*i+3])
                    previous = collected["triangles"].setdefault(ordinal, face)
                    _require(previous == face, "An immutable mesh changed across repeated pages.")
                _require(response["truncated"] is (page["offset"] + count < page["total_triangles"])
                         and bool(response["next_cursor"]) is response["truncated"], "A cursor hides incomplete mesh output.")
    _require(set(snapshots) >= accepted_once, "An accepted source snapshot was omitted.")
    for key, (_, claimed) in snapshots.items():
        _require(claimed is (key in accepted_once), "accepted_once disagrees with the actual source-edit exchanges.")
    checks = {c["id"]: c for c in report["checks"]}
    _require(len(checks) == len(report["checks"]) and set(manifest["mandatory_workflow_checks"]) <= set(checks),
             "Required actual source-workflow scenarios are missing.")
    for identity in manifest["mandatory_workflow_checks"]:
        check = checks[identity]
        _require(check["status"] == "passed" and check["evidence_request_ids"], "A mandatory workflow scenario did not execute.")
        known_ids = {key[1] for key in exchanges}
        _require(set(check["evidence_request_ids"]) <= known_ids, "A workflow check cites absent actual requests.")
    artifacts = {}
    for item in report["artifacts"]:
        fixture = item["fixture"]
        _require(fixture not in artifacts, "A workflow fixture has ambiguous delivered artifacts.")
        project, revision = item["project_id"], item["program_revision"]
        export_request, exported = exchanges[(project, item["export_request_id"])]
        _require(export_request["operation"] == "export" and export_request["program_revision"] == revision
                 and export_request["destination"] == "ontokin.glb/0.3" and exported["status"] == "succeeded"
                 and exported["program_revision"] == revision and exported["result"]["artifact_id"] == item["artifact_id"]
                 and exported["result"]["sha256"] == item["artifact_sha256"], "Artifact export provenance is inconsistent.")
        raw = bytearray()
        for request_id in item["retrieval_request_ids"]:
            request, response = exchanges[(project, request_id)]
            part = response["result"]
            chunk = base64.b64decode(part["data_base64"], validate=True)
            _require(request["operation"] == "artifact" and request["artifact_id"] == item["artifact_id"]
                     and response["status"] == "succeeded" and part["offset"] == request.get("offset", 0) == len(raw)
                     and part["next_offset"] == (None if len(raw)+len(chunk) == item["byte_length"] else len(raw)+len(chunk))
                     and part["total_bytes"] == item["byte_length"]
                     and part["sha256"] == item["artifact_sha256"] and response["program_revision"] == revision,
                     "Artifact retrieval chunks are missing, reordered or from another program.")
            raw.extend(chunk)
            _require(len(raw) <= manifest["limits"]["max_glb_bytes"], "Retained artifact exceeds the fixed byte cap.")
        _require(len(raw) == item["byte_length"] and digest(raw) == item["artifact_sha256"],
                 "Retrieved source artifact bytes differ from their claimed hash or length.")
        actual_glb = legacy._repository_file(fixture + "/scene.glb", root)
        _require(actual_glb.read_bytes() == raw, "The independently validated GLB was not the retrieved artifact.")
        artifacts[fixture] = item
    _require(set(manifest["mandatory_native_fixtures"]) <= set(artifacts), "Not every fixed native source fixture was exported and retrieved.")
    expected = _expected_fixtures()
    for fixture in manifest["mandatory_native_fixtures"]:
        item = artifacts[fixture]
        program = snapshots[(item["project_id"], item["program_revision"])][0]
        if "program" in expected[fixture]:
            _require(program.to_payload() == expected[fixture]["program"].to_payload(), "A workflow changed the fixed source fixture " + fixture)
        for shape in expected[fixture]["oracle"]["shapes"]:
            page = pages[(item["project_id"], item["program_revision"], tuple(shape["element_id"]))]
            triangles = _analytic_triangles(shape)
            _require(page["total"] == len(triangles) and set(page["triangles"]) == set(range(len(triangles))),
                     "Complete mesh-page evidence is missing for " + fixture + ":" + shape["path"])
            for ordinal, (region, points, normal) in enumerate(triangles):
                actual_region, actual_points, actual_normals = page["triangles"][ordinal]
                _require(actual_region == region, "A source page assigned the wrong material region.")
                for actual, wanted, observed_normal in zip(actual_points, points, actual_normals):
                    _vector_error(actual, wanted, 1e-10, "Native binary64 page point")
                    _vector_error(observed_normal, normal, 1e-10, "Native page flat normal")
                    _metric(abs(math.hypot(*observed_normal) - 1), 1e-12, "Native page unit normal")
    studio = artifacts["studio-original"]
    project = studio["project_id"]
    original = snapshots[(project, studio["program_revision"])][0]
    repaired = snapshots[(project, artifacts["radius-repaired"]["program_revision"])][0]
    _require(original.entry.raw.count(b"0.48[m]") == 1 and repaired.entry.raw == original.entry.raw.replace(b"0.48[m]", b"0.52[m]"),
             "The targeted radius repair changed other source bytes.")
    invalid_raw = original.entry.raw.replace(b"0.48[m]", b"0[m]")
    invalid = ProgramBundle(SourceUnit("entry", original.entry.filename, invalid_raw), original.modules)
    _require((project, invalid.program_revision) in snapshots and not snapshots[(project, invalid.program_revision)][1],
             "The rejected radius candidate was omitted or became accepted.")
    rejected = [(q, r) for (p, _), (q, r) in exchanges.items() if p == project and q["operation"] == "edit"
                and r.get("program_revision") == invalid.program_revision and r["status"] == "rejected"]
    _require(rejected and any(d["code"] == "OKL-E-SURFACE-RADIUS" and d["program_revision"] == invalid.program_revision
                             for _, response in rejected for d in response["diagnostics"]),
             "The bad source variant lacks its revision-bound radius diagnostic.")
    head_prefix = original.entry.raw.split(b'    object second @ "second"')[0]
    action_suffix = original.entry.raw.split(b'    action walk @ "walk"')[1]
    for fixture in ("radius-repaired", "palette-repaired", "inserted", "reordered", "removed"):
        item = artifacts[fixture]
        program = snapshots[(item["project_id"], item["program_revision"])][0]
        _require(item["project_id"] == project and program.modules == original.modules
                 and program.entry.raw.split(b'    object second @ "second"')[0] == head_prefix
                 and program.entry.raw.split(b'    action walk @ "walk"')[1] == action_suffix,
                 "A targeted workflow edit changed the sibling, animation or pinned library.")
    _require(artifacts["removed"]["program_revision"] == artifacts["palette-repaired"]["program_revision"],
             "Removing the inserted section did not restore the exact authored source revision.")
    context["workflow"] = {"artifacts": artifacts, "snapshots": snapshots, "exchanges": exchanges}
    return {"workflow_sha256": file_identity(path), "exchanges": len(exchanges), "snapshots": len(snapshots),
            "accepted_revisions": len(accepted_once), "retrieved_artifacts": len(artifacts),
            "complete_mesh_occurrences": len(pages), "checks": manifest["mandatory_workflow_checks"]}


def _glb(path: Path):
    raw = path.read_bytes()
    _require(28 <= len(raw) <= 67108864, "A retained native GLB exceeds the fixed byte limit.")
    magic, version, total, size, kind = struct.unpack_from("<4sIIII", raw)
    _require(magic == b"glTF" and version == 2 and total == len(raw) and kind == 0x4E4F534A
             and size <= 4194304 and size % 4 == 0, "Invalid retained GLB container.")
    document = json.loads(raw[20:20+size].decode("utf-8"),
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite GLB JSON: " + x)))
    binary_size, binary_kind = struct.unpack_from("<II", raw, 20+size)
    _require(binary_kind == 0x004E4942 and 28+size+binary_size == len(raw), "Invalid retained GLB binary chunk.")
    return document, raw[28+size:]


def _accessor(document, binary, index):
    _require(type(index) is int and 0 <= index < len(document["accessors"]), "Invalid GLB accessor index.")
    accessor = document["accessors"][index]
    _require(not accessor.get("sparse") and not accessor.get("normalized"), "Unexpected native accessor encoding.")
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    code, size = {5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}[accessor["componentType"]]
    view = document["bufferViews"][accessor["bufferView"]]
    count, stride = accessor["count"], view.get("byteStride", size*width)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    _require(type(count) is int and 0 < count <= 250000 and view["buffer"] == 0
             and stride >= size*width and accessor.get("byteOffset", 0)+(count-1)*stride+size*width <= view["byteLength"]
             and 0 <= offset and offset+(count-1)*stride+size*width <= len(binary), "Native accessor exceeds its embedded buffer.")
    values = [list(struct.unpack_from("<"+code*width, binary, offset+i*stride)) for i in range(count)]
    _require(all(math.isfinite(v) for row in values for v in row), "Native accessor contains non-finite values.")
    return [row[0] for row in values] if width == 1 else values


def _verify_geometry(document, binary, shape, record, revision, program):
    nodes = [n for n in document["nodes"] if n.get("extras", {}).get("ontokin", {}).get("path") == shape["path"]]
    _require(len(nodes) == 1, "A native source occurrence has no unique carrier.")
    node = nodes[0]
    meta = node["extras"]["ontokin"]
    _require(meta["element_id"] == shape["element_id"] and meta["program_revision"] == revision
             and meta["physical"]["kind"] == shape.get("physical_kind", "no_body"),
             "A native carrier changed source identity or physical participation.")
    units = {u.source_id: u for u in program.units}
    _require(meta["source_mapping"]["element_id"] == shape["element_id"], "An occurrence source mapping changed identity.")
    for key in ("definition", "declaration"):
        source = meta["source_mapping"][key]
        unit = units[source["source_id"]]
        _require(source["source_revision"] == unit.revision and type(source["start_byte"]) is int
                 and type(source["end_byte"]) is int and 0 <= source["start_byte"] < source["end_byte"] <= len(unit.raw),
                 "An exported source mapping escaped the actual source unit.")
        unit.raw[:source["start_byte"]].decode("utf-8"); unit.raw[:source["end_byte"]].decode("utf-8")
    triangles = _analytic_triangles(shape)
    surface = meta["surface"]
    ordered = sorted(shape["sections"], key=lambda s: s["station_m"])
    _require(surface["profile"] == "surface-0.1" and surface["facets"] == shape["facets"]
             and surface["caps"] == shape["caps"] and surface["section_keys"] == [s["key"] for s in ordered]
             and surface["stations_m"] == [s["station_m"] for s in ordered]
             and surface["triangle_count"] == len(triangles) and surface["vertex_count"] == 3*len(triangles)
             and surface["physical_participation"] == "none", "Native metadata contradicts its scalar source oracle.")
    placement = surface["local_visual_placement"]
    _require(placement["frame"] == "carrier_self_frame", "Visual placement acquired a world authority.")
    _vector_error(placement["position_m"], shape["local_position_m"], 1e-12, "Local placement")
    _vector_error(placement["orientation_wxyz"], shape["local_rotation_wxyz"], 1e-12, "Local rotation")
    primitives = document["meshes"][node["mesh"]]["primitives"]
    expected_regions = sorted({t[0] for t in triangles})
    _require(len(primitives) == len(expected_regions)
             and sorted(p["extras"]["ontokin"]["region_key"] for p in primitives) == expected_regions
             and len({p["material"] for p in primitives}) == len(primitives), "Native material regions were merged or omitted.")
    _require(record["path"] == shape["path"] and record["triangles"] == len(triangles)
             and record["vertices"] == 3*len(triangles) and record["ordered_keys"] == [s["key"] for s in ordered]
             and record["local_placement_applied_once"] is True, "The independent geometry record contradicts the artifact.")
    regions = {r["region"]: r for r in record["regions"]}
    _require(len(regions) == len(record["regions"]) and sorted(regions) == expected_regions, "A destination geometry record lost regional evidence.")
    worst_position, worst_unit = 0.0, 0.0
    for primitive in primitives:
        _require(primitive.get("mode", 4) == 4, "Native geometry must contain triangles.")
        region = primitive["extras"]["ontokin"]["region_key"]
        faces = [t for t in triangles if t[0] == region]
        positions = _accessor(document, binary, primitive["attributes"]["POSITION"])
        normals = _accessor(document, binary, primitive["attributes"]["NORMAL"])
        indices = _accessor(document, binary, primitive["indices"])
        _require(len(indices) == 3*len(faces) and len(positions) == len(normals), "The real primitive has the wrong triangle count.")
        material = document["materials"][primitive["material"]]
        pbr, wanted = material["pbrMetallicRoughness"], shape["materials"][region]
        _require(pbr["baseColorFactor"] == wanted["rgba"] and pbr["metallicFactor"] == wanted["metallic"]
                 and pbr["roughnessFactor"] == wanted["roughness"], "Actual glTF PBR properties changed.")
        _require(material["extras"]["ontokin"]["source_region_key"] == region
                 and material["extras"]["ontokin"]["element_id"] == shape["element_id"]
                 and material["extras"]["ontokin"]["program_revision"] == revision,
                 "Actual material source provenance changed.")
        actual_region = regions[region]
        _require(actual_region["triangles"] == len(faces) and actual_region["material_index"] == primitive["material"]
                 and all(actual_region[k] == wanted[k] for k in ("rgba", "metallic", "roughness")),
                 "Recorded destination materials contradict the real PBR primitive.")
        for number, (_, points, normal) in enumerate(faces):
            actual_points = []
            for index, point in zip(indices[3*number:3*number+3], points):
                _require(type(index) is int and 0 <= index < len(positions), "A real primitive index is out of bounds.")
                actual_points.append(positions[index])
                worst_position = max(worst_position, _vector_error(positions[index], point, 1e-5, "Decoded local float32 point"))
                _vector_error(normals[index], normal, 1e-6, "Decoded flat triangle normal")
                worst_unit = max(worst_unit, abs(math.hypot(*normals[index]) - 1))
            winding = _cross([b-a for a,b in zip(actual_points[0], actual_points[1])],
                             [c-a for a,c in zip(actual_points[0], actual_points[2])])
            _require(sum(a*b for a,b in zip(winding, normal)) > 0, "The actual GLB has degenerate or reversed triangle winding.")
    _metric(record["max_local_float32_error_m"], 1e-5, "Recorded local float32 tolerance")
    _metric(record["max_float32_normal_length_error"], 1e-6, "Recorded float32 unit normals")
    legacy._same_metric(record["max_local_float32_error_m"], worst_position, "Recorded point error")
    legacy._same_metric(record["max_float32_normal_length_error"], worst_unit, "Recorded normal length error")
    for identity in ("positions_sha256", "topology_sha256"):
        _require(isinstance(record[identity], str) and SHA.fullmatch(record[identity]), "A destination geometry digest is missing.")
    for key in ("closed_volume", "circle_sagitta"):
        if key in record:
            metric, bound = ("error_m3", "float32_perturbation_bound_m3") if key == "closed_volume" else ("error_m", "float32_perturbation_bound_m")
            _metric(record[key][metric], _finite(record[key][bound], bound), key)


def _multiply_quaternions(a, b):
    w,x,y,z = a; v,i,j,k = b
    return [w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j, w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v]


def _expected_pose(shape, time):
    motion = shape["motion"]
    position = [p + time*v for p,v in zip(motion["position_m"], motion["velocity_m_per_s"])]
    kind = motion["kind"]
    if kind == "affine":
        rotation = motion["rotation_wxyz"]
    elif kind == "released_uniform_gravity":
        dt = max(0.0, time-motion["release_time_s"])
        position = [p + .5*g*dt*dt for p,g in zip(position, motion["gravity_m_per_s2"])]
        rotation = motion["rotation_wxyz"]
    elif kind == "hinge_y_on_translating_z90_parent":
        parent = [math.sqrt(.5), 0, 0, math.sqrt(.5)]
        angle = motion["angle_rad_per_second"]*time/2
        rotation = _multiply_quaternions(parent, [math.cos(angle), 0, math.sin(angle), 0])
        position = [p+v for p,v in zip(position, _rotate(motion["mount_position_m"], parent))]
    else:
        raise ValueError("Unknown predetermined motion oracle: " + str(kind))
    return {"position_m": position, "orientation_wxyz": rotation}


def _verify_poses(objects, oracle, time, *, reference=None, direct_metrics=False):
    expected = {s["path"]: s for s in oracle["shapes"] + oracle.get("empty_objects", [])}
    _require(set(objects) == set(expected), "A destination sample omitted or added a source carrier.")
    for path, shape in expected.items():
        actual = objects[path]
        wanted = _expected_pose(shape, time)
        p, q = legacy._pose_error(actual, wanted, xyzw=True)
        _metric(p, .001, "Independent world position")
        _metric(q, .001, "Independent world rotation")
        metrics = actual if direct_metrics else actual["independent"]
        legacy._same_metric(metrics["position_error_m"], p, "Recorded independent position error")
        legacy._same_metric(metrics["rotation_error_rad"], q, "Recorded independent rotation error")
        if reference is not None:
            e, f = legacy._pose_error(actual, reference[path], xyzw=True)
            _metric(e, .001, "Evaluated world position")
            _metric(f, .001, "Evaluated world rotation")
            legacy._same_metric(actual["evaluator"]["position_error_m"], e, "Recorded evaluator position error")
            legacy._same_metric(actual["evaluator"]["rotation_error_rad"], f, "Recorded evaluator rotation error")
        landmarks = actual.get("landmarks", actual.get("probes", []))
        for point in landmarks:
            local = point.get("local_m")
            world = point.get("world_m")
            if local is not None and world is not None:
                wanted_world = [v+p for v,p in zip(_rotate(local, wanted["orientation_wxyz"]), wanted["position_m"])]
                error = _vector_error(world, wanted_world, .001, "World geometry landmark")
                if "error_m" in point:
                    legacy._same_metric(point["error_m"], error, "Recorded world landmark error")
    return len(expected)


def _verify_destination(native, evidence_root, implementation, manifest, context):
    build_path = _identified(native["build"], evidence_root)
    destination_path = _identified(native["destination"], evidence_root)
    build, report = _json_file(build_path), _json_file(destination_path)
    root = build_path.parent
    _require(build["schema_version"] == "ontokin.surface-native-build/0.1" and build["status"] == "built"
             and build["acceptance_manifest_sha256"] == manifest["acceptance_manifest"]["sha256"],
             "Native build did not finish from the fixed acceptance corpus.")
    _require(report["schema_version"] == "ontokin.surface-native-destination-validation/0.1"
             and report["status"] == "passed" and report["build_sha256"] == file_identity(build_path),
             "Independent native validation is absent or identifies another build.")
    _require(report["verifier_sha256"] == file_identity(ROOT / "tools/verify_surface_native.mjs")
             and report["tooling_lock_sha256"] == file_identity(ROOT / "tools/package-lock.json"),
             "Independent destination tooling identity is stale.")
    artifacts = {f["fixture"]: f for f in build["fixtures"]}
    results = {f["fixture"]: f for f in report["fixtures"]}
    _require(len(artifacts) == len(build["fixtures"]) and len(results) == len(report["fixtures"])
             and set(artifacts) == set(results) and set(manifest["mandatory_native_fixtures"]) <= set(artifacts),
             "The independent destination corpus omits or duplicates a mandatory fixture.")
    expected, verified = _expected_fixtures(), {}
    comparison_count = 0
    for fixture in manifest["mandatory_native_fixtures"]:
        entry, result = artifacts[fixture], results[fixture]
        directory = root / fixture
        bundle_path = legacy._repository_file(fixture + "/program.bundle.json", root)
        directory = bundle_path.parent
        program = _source_bundle(bundle_path)
        oracle = _json_file(directory / "oracle.json")
        _check_oracle(oracle, expected[fixture]["oracle"])
        if "program" in expected[fixture]:
            _require(program.to_payload() == expected[fixture]["program"].to_payload(), "The native fixture is not its fixed source program.")
        _require(oracle["schema_version"] == "ontokin.surface-fixture-oracle/0.1" and oracle["fixture"] == fixture
                 and oracle["acceptance_manifest_sha256"] == manifest["acceptance_manifest"]["sha256"], "A retained scalar oracle lost its frozen source identity.")
        required_files = {"bundle": "program.bundle.json", "glb": "scene.glb", "export": "scene.export.json",
                          "reference": "scene.reference.json", "oracle": "oracle.json"}
        required_files.update({"source_"+str(i): u.filename for i,u in enumerate(program.units)})
        _require(set(result["provenance"]) == set(required_files), "The destination provenance closure is incomplete.")
        for role, filename in required_files.items():
            record = result["provenance"][role]
            file = _nested(record["file"], record["sha256"], directory)
            _require(record["file"] == filename and record["byte_length"] == file.stat().st_size,
                     "Destination provenance was relabelled or changed byte length.")
        glb_path = directory / "scene.glb"
        artifact_sha = file_identity(glb_path)
        revision = program.program_revision
        _require(entry["program_revision"] == result["program_revision"] == revision
                 and entry["artifact_sha256"] == result["artifact_sha256"] == artifact_sha
                 and entry["glb_bytes"] == glb_path.stat().st_size
                 and result["status"] == "passed", "Source, artifact and independent validator identities disagree.")
        _require(result["exporter_source_code_sha256"] == implementation["source_code_sha256"].removeprefix("sha256:"),
                 "The native artifact was exported by stale implementation bytes.")
        export = _json_file(directory / "scene.export.json")
        reference = _json_file(directory / "scene.reference.json")
        _require(export["schema_version"] == "ontokin.glb-report/0.3" and export["target_contract"] == "ontokin.glb/0.3"
                 and export["validation"]["status"] == "passed" and export["source_code_sha256"] == result["exporter_source_code_sha256"]
                 and export["artifact"]["sha256"] == artifact_sha and export["artifact"]["byte_length"] == glb_path.stat().st_size
                 and export["program_revision"] == revision and export["program"]["manifest"] == program.manifest(),
                 "Native exporter report does not identify this successful artifact.")
        _require(reference["schema_version"] == "ontokin.surface-native-reference/0.1" and reference["program_revision"] == revision
                 and reference["artifact_sha256"] == artifact_sha and reference["source_manifest"] == program.manifest(),
                 "The evaluator reference describes another source artifact.")
        document, binary = _glb(glb_path)
        metadata = document["extras"]["ontokin"]
        _require(metadata["target_contract"] == "ontokin.glb/0.3" and metadata["profile"] == "surface-0.1"
                 and metadata["program"]["revision"] == revision and metadata["program"]["manifest"] == program.manifest(),
                 "Actual native GLB metadata changed source identity or destination.")
        objects = oracle["shapes"] + oracle.get("empty_objects", [])
        _require(len(document["nodes"]) == len(objects), "The actual GLB added a hidden carrier or motion authority.")
        geometry = {r["path"]: r for r in result["geometry"]}
        _require(len(geometry) == len(result["geometry"]) == len(oracle["shapes"]), "The independent report omitted native geometry.")
        for shape in oracle["shapes"]:
            _verify_geometry(document, binary, shape, geometry[shape["path"]], revision, program)
        _require(result["khronos"]["errors"] == 0 and result["khronos"]["warnings"] == 0
                 and result["khronos"]["version"], "The actual Khronos run reported errors or warnings.")
        _require(not any(m.get("severity") in (0, 1) for m in result["khronos"].get("messages", [])),
                 "Khronos messages contradict the error/warning totals.")
        samples = result["three_js"]["samples"]
        fixed_times = [float(t) for t in _json_file(FIXTURES / "compositions/expected.json")["sample_times_seconds"]]
        _require([float(s["time_seconds"]) for s in samples] == fixed_times
                 and [float(s["time_seconds"]) for s in reference["samples"]] == fixed_times,
                 "The destination did not execute every fixed animation sample time.")
        count = 0
        for sample, ref in zip(samples, reference["samples"]):
            count += _verify_poses(sample["objects"], oracle, float(sample["time_seconds"]), reference=ref["objects"])
        _require(result["three_js"]["world_pose_comparisons"] == count, "The independent pose count was inferred or inflated.")
        comparison_count += count
        verified[fixture] = {"program_revision": revision, "artifact_sha256": artifact_sha,
                             "provenance": result["provenance"], "oracle": oracle}
    context["destination"] = verified
    return {"build_sha256": file_identity(build_path), "destination_sha256": file_identity(destination_path),
            "fixtures": len(verified), "world_pose_comparisons": comparison_count,
            "khronos_errors": 0, "khronos_warnings": 0}


def _verify_browser(native, evidence_root, implementation, manifest, context):
    _require("destination" in context, "The browser gate requires verified source/destination identities first.")
    path = _identified(native["browser"], evidence_root)
    report = _json_file(path)
    _require(report["schema_version"] == "ontokin.surface-native-browser-validation/0.1" and report["status"] == "passed",
             "The identified browser run did not pass.")
    _require(report["verifier_sha256"] == file_identity(ROOT / "tools/verify_surface_viewer.mjs")
             and report["tooling_lock_sha256"] == file_identity(ROOT / "tools/package-lock.json")
             and report["harness_sha256"] == file_identity(path.parent / "surface-viewer.html"),
             "The browser harness or locked validation tooling changed.")
    _require(report.get("browser") and report.get("webgl") and report.get("environment"), "The browser report lacks actual renderer identity.")
    for key in ("page_errors", "console_errors", "failed_requests", "network_requests"):
        _require(report[key] == [], "The browser run reported " + key + ".")
    fixtures = {f["fixture"]: f for f in report["source_fixtures"]}
    _require(len(fixtures) == len(report["source_fixtures"]) and set(manifest["mandatory_browser_fixtures"]) <= set(fixtures),
             "The browser corpus omits a mandatory repaired/composed/released source fixture.")
    reviews = {r["capture_sha256"]: r for r in native["visual_reviews"]}
    _require(len(reviews) == len(native["visual_reviews"]), "Visual review identities are duplicated.")
    counts, capture_count = 0, 0
    times = [float(t) for t in _json_file(FIXTURES / "compositions/expected.json")["sample_times_seconds"]]
    for fixture in manifest["mandatory_browser_fixtures"]:
        source = fixtures[fixture]
        expected = context["destination"][fixture]
        _require(source["program_revision"] == expected["program_revision"] and source["artifact_sha256"] == expected["artifact_sha256"]
                 and source["provenance"] == expected["provenance"]
                 and source["exporter_source_code_sha256"] == implementation["source_code_sha256"].removeprefix("sha256:"),
                 "A browser fixture is disconnected from the independently validated source GLB.")
        samples = [s for s in report["samples"] if s["fixture"] == fixture]
        _require([float(s["time_seconds"]) for s in samples] == times, "The browser omitted or duplicated a fixed sample time.")
        for sample in samples:
            counts += _verify_poses(sample["objects"], expected["oracle"], float(sample["time_seconds"]), direct_metrics=True)
        captures = [c for c in report["captures"] if c["fixture"] == fixture]
        required = {(c["view"], float(c["time_seconds"])) for c in manifest["mandatory_browser_captures"]}
        _require(len(captures) == len(required) and {(c["view"], float(c["time_seconds"])) for c in captures} == required,
                 "Required front, side or animated browser captures are missing.")
        for capture in captures:
            file = _nested(capture["file"], capture["sha256"], path.parent)
            _require(file.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") and file.stat().st_size > 100,
                     "A retained browser capture is not a usable PNG.")
            _require(capture["program_revision"] == source["program_revision"] and capture["artifact_sha256"] == source["artifact_sha256"],
                     "A capture names a different source/artifact revision.")
            _verify_poses(capture["objects"], expected["oracle"], float(capture["time_seconds"]), direct_metrics=True)
            review = reviews.get(capture["sha256"], {})
            _require(review.get("status") == "reviewed"
                     and isinstance(review.get("reviewer"), str) and review["reviewer"].strip()
                     and isinstance(review.get("observation"), str) and review["observation"].strip(),
                     "A required browser capture has no identified visual review.")
            capture_count += 1
        playback = [p for p in report["playback"] if p["fixture"] == fixture]
        _require(len(playback) == 1 and playback[0]["stable_across_frames"] is True
                 and playback[0]["started_at_seconds"] == .5
                 and .5 < _finite(playback[0]["paused_at_seconds"], "Playback time") <= 2,
                 "The browser has no successful play/pause observation for this fixture.")
    _require(report["world_pose_comparisons"] == sum(len(s["objects"]) for s in report["samples"]),
             "The browser pose count contradicts its retained samples.")
    return {"browser_sha256": file_identity(path), "fixtures": len(manifest["mandatory_browser_fixtures"]),
            "world_pose_comparisons": counts, "reviewed_captures": capture_count}


def _verify_full_suite(report, implementation, inventory, manifest):
    names = discover_test_ids()
    _require(set(manifest["regression_required_test_ids"]) <= set(names),
             "Current discovery lost an inherited frozen regression test.")
    _require(report["schema_version"] == "ontokin.unittest-execution/0.1" and report["executed"] is True
             and report["implementation"] == implementation and report["evidence_stable_during_run"] is True,
             "The full regression suite is unexecuted, stale or changed during its run.")
    _require(report["evidence_files"] == inventory and report["evidence_inventory_sha256"] == inventory_identity(inventory),
             "The full-suite report does not identify current test/spec/tool bytes.")
    _require(report["expected_test_ids"] == names and _execution_passes(report["test_execution"], names),
             "The full-suite report omits, duplicates, skips or fails a current discovered test.")
    _require(report["summary"] == {"total": len(names), "passed": len(names), "all_passed": True},
             "The full-suite summary contradicts its actual execution records.")
    return len(names)


def _verify_regression(records, evidence_root, implementation, inventory, manifest):
    paths = {key: _identified(records[key], evidence_root)
             for key in ("core", "agent", "construction", "construction_external", "full_suite")}
    reports = {key: _json_file(path) for key,path in paths.items()}
    full_count = _verify_full_suite(reports["full_suite"], implementation, inventory, manifest)
    core = reports["core"]
    core_manifest_path = ROOT / "docs/language-design/core-v0.1/validation-cases.json"
    core_manifest = _json_file(core_manifest_path)
    _require(core["schema_version"] == "ontokin.conformance-report/0.1"
             and core["source_code_sha256"] == implementation["source_code_sha256"].removeprefix("sha256:")
             and core["implementation_version"] == implementation["version"]
             and core["fixture_manifest_sha256"] == file_identity(core_manifest_path).removeprefix("sha256:"),
             "Core conformance belongs to another implementation or fixture corpus.")
    from .fixtures import materialize
    core_cases = {c["id"]: c for c in core["cases"]}
    _require(len(core_cases) == len(core["cases"]) and set(core_cases) == {c["id"] for c in core_manifest["cases"]},
             "The core source conformance corpus is incomplete.")
    for case in core_manifest["cases"]:
        result = core_cases[case["id"]]
        _require(result["status"] == "passed" and result["checks"] and all(c["passed"] is True for c in result["checks"])
                 and result["source_revision"] == digest(materialize(case, core_manifest_path.parent).encode("utf-8")),
                 "A core case did not execute against its exact frozen source.")
    _require(core["summary"]["passed"] == core["summary"]["total"] == len(core_cases) and core["summary"]["failed"] == 0,
             "The core conformance summary contradicts its cases.")
    agent = reports["agent"]
    _require(agent["schema_version"] == "ontokin.agent-conformance/0.1" and agent["executed"] is True
             and agent["agent_contract"] == "ontokin.agent/0.1" and agent["implementation"] == implementation
             and agent["manifest_sha256"] == file_identity(core_manifest_path), "Agent A01--A10 evidence is stale or unexecuted.")
    from tools.run_agent_conformance import CASE_TESTS, content_identity
    agent_files = [ROOT / "tests/test_agent.py", ROOT / "tools/run_agent_conformance.py",
                   ROOT / "docs/language-design/agent-v0.1/request.schema.json",
                   ROOT / "docs/language-design/agent-v0.1/response.schema.json", core_manifest_path,
                   core_manifest_path.parent / "diagnostic.schema.json", *core_manifest_path.parent.glob("*.ok")]
    _require(agent["fixture_identity"] == content_identity(agent_files), "The agent scenario implementation or schema bytes changed.")
    agent_cases = {c["id"]: c for c in agent["cases"]}
    _require(len(agent_cases) == len(agent["cases"]) == 10 and set(agent_cases) == set(CASE_TESTS), "A01--A10 are not all present.")
    for key, method in CASE_TESTS.items():
        case = agent_cases[key]
        _require(case["passed"] is True and not case["failures"] and case["test_method"] == method and case["operations"],
                 "An agent case lacks its actual successful protocol scenario.")
    _require(agent["summary"] == {"total": 10, "passed": 10, "failed": 0}, "The A01--A10 summary changed its observed results.")
    construction = reports["construction"]
    frozen = legacy.load_manifest()
    names = sorted({name for c in frozen["cases"] for name in c["required_tests"]})
    _require(construction["schema_version"] == "ontokin.construction-conformance/0.1" and construction["executed"] is True
             and construction["implementation"] == construction["implementation_after_run"] == implementation
             and construction["evidence_stable_during_run"] is True and not construction["run_issues"]
             and construction["evidence_files"] == legacy._evidence_inventory(legacy.DEFAULT_FIXTURES)
             and construction["manifest"]["sha256"] == file_identity(legacy.DEFAULT_FIXTURES / "validation-cases.json")
             and construction["settings"] == frozen["settings"], "Current construction conformance is stale or incomplete.")
    _require(_execution_passes(construction["test_execution"], names), "Current C01--C20 required tests did not all execute and pass.")
    actual_cases = {c["id"]: c for c in construction["cases"]}
    _require(len(actual_cases) == len(construction["cases"]) == 20 and set(actual_cases) == {c["id"] for c in frozen["cases"]},
             "C01--C20 are not all present in current regression evidence.")
    for case in frozen["cases"]:
        actual = actual_cases[case["id"]]
        _require(actual["status"] == "passed" and actual["required_tests"] == case["required_tests"]
                 and actual["external_gates"] == case["external_gates"] and not actual["pending_reasons"],
                 "A current construction requirement remains pending or changed its adopted checks.")
    _require(construction["summary"]["case_gate_complete"] is True and construction["summary"]["passed"] == 20
             and construction["summary"]["pending"] == construction["summary"]["failed"] == 0,
             "Historical or pending C20 evidence cannot close current M12.")
    rack = load_bundle(_json_file(legacy.DEFAULT_FIXTURES / "01-keyed-rack/program.bundle.json"))
    external = legacy.verify_external_evidence(paths["construction_external"], implementation=implementation,
                                               expected_program=rack, root=evidence_root)
    _require(external["status"] == "passed", "Current C20 independent evidence remains pending: " + "; ".join(external["issues"]))
    _require(construction["external_evidence"]["manifest_sha256"] == file_identity(paths["construction_external"])
             and construction["external_evidence"]["status"] == "passed", "The C20 case did not use this verified external run.")
    return {"full_suite_tests": full_count, "core_cases": len(core_cases), "agent_cases": 10,
            "construction_cases": 20, "current_C20": "passed", "reports": {k: file_identity(v) for k,v in paths.items()}}


def _verify_commit_inventory(commit: str, inventory: list[dict]):
    """Bind the CI head's actual Git tree, not its self-reported digest label."""
    import subprocess
    process = subprocess.run(["git", "ls-tree", "-r", "--full-tree", "-z", commit], cwd=ROOT,
                             capture_output=True, check=False, timeout=30)
    _require(process.returncode == 0, "The identified CI commit is not locally available for an exact tree check.")
    tree = {}
    for row in process.stdout.split(b"\0"):
        if not row:
            continue
        descriptor, path = row.split(b"\t", 1)
        mode, kind, identity = descriptor.decode("ascii").split()
        if kind == "blob":
            tree[path.decode("utf-8")] = (mode, identity)
    for record in inventory:
        file = legacy._repository_file(record["path"], ROOT)
        raw = file.read_bytes()
        _require(digest(raw) == record["sha256"], "Current evidence changed during the CI identity check.")
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        _require(tree.get(record["path"]) in (("100644", blob), ("100755", blob)),
                 "CI commit tree differs from current implementation/test/spec/tool bytes: " + record["path"])


def _verify_ci(record, evidence_root, implementation, inventory):
    path = _identified(record, evidence_root)
    ci = _json_file(path)
    _require(ci["schema_version"] == "ontokin.surface-ci/0.1" and ci["implementation"] == implementation
             and ci["evidence_inventory_sha256"] == inventory_identity(inventory), "CI evidence identifies different implementation or test inputs.")
    commit = ci["implementation_commit"]
    _require(isinstance(commit, str) and COMMIT.fullmatch(commit), "CI needs an exact full Git commit identity.")
    run = ci["workflow_run"]
    _require(type(run["id"]) is int and run["id"] > 0 and run["head_sha"] == commit
             and run["status"] == "completed" and run["conclusion"] == "success"
             and run["html_url"] == f'https://github.com/Omegapy/OntoKin/actions/runs/{run["id"]}',
             "CI did not complete successfully on the identified OntoKin commit.")
    jobs = ci["jobs"]
    _require(isinstance(jobs, list) and len({j["id"] for j in jobs}) == len(jobs), "CI job identities are ambiguous.")
    versions, visual = set(), 0
    for job in jobs:
        _require(type(job["id"]) is int and job["id"] > 0 and job["run_id"] == run["id"]
                 and isinstance(job["name"], str) and job["name"].strip()
                 and job["status"] == "completed" and job["conclusion"] == "success", "A required CI job did not pass on the same run.")
        if job["role"] == "python":
            _require(job["python_version"] in {"3.11", "3.12", "3.13"}
                     and job["python_version"] not in versions, "CI Python jobs are missing, duplicated or relabelled.")
            versions.add(job["python_version"])
        elif job["role"] == "visual":
            _require(job["python_version"] is None, "The visual CI job has contradictory role metadata.")
            visual += 1
        else:
            raise ValueError("Unknown required CI job role.")
    _require(versions == {"3.11", "3.12", "3.13"} and visual == 1, "All three supported Python jobs and the visual job are mandatory.")
    _verify_commit_inventory(commit, inventory)
    return {"ci_sha256": file_identity(path), "implementation_commit": commit,
            "workflow_run_id": run["id"], "python_versions": sorted(versions), "visual_jobs": visual}


def verify_external_evidence(path: Path | None, *, implementation=None, inventory=None,
                             manifest=None, evidence_root: Path = ROOT) -> dict:
    implementation = implementation or implementation_identity()
    inventory = evidence_inventory() if inventory is None else inventory
    manifest = load_manifest() if manifest is None else manifest
    result = {"schema_version": "ontokin.surface-evidence-audit/0.1", "executed_external_tools": False,
              "manifest": None if path is None else str(path), "gates": [],
              "basis": "Retained-file, source, binary, numerical and CI-tree checks; no external tools were rerun."}
    if path is None:
        result["gates"] = [{"id": name, "status": "pending", "executed_external_tools": False,
                             "issues": ["No identified surface release evidence manifest was supplied."]} for name in GATES]
        return result
    try:
        evidence = _json_file(Path(path))
        _require(evidence["schema_version"] == "ontokin.surface-release-evidence/0.1"
                 and evidence["implementation"] == implementation, "The release evidence uses another schema or implementation.")
        result["manifest_sha256"] = file_identity(Path(path))
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["gates"] = [{"id": name, "status": "pending", "executed_external_tools": False,
                             "issues": [str(error)]} for name in GATES]
        return result
    root, context = Path(evidence_root), {}
    actions = {
        "workflow": lambda: _verify_workflow(evidence["workflow"], root, implementation, manifest, context),
        "destination": lambda: _verify_destination(evidence["native"], root, implementation, manifest, context),
        "browser": lambda: _verify_browser(evidence["native"], root, implementation, manifest, context),
        "regression": lambda: _verify_regression(evidence["legacy"], root, implementation, inventory, manifest),
        "ci": lambda: _verify_ci(evidence["ci"], root, implementation, inventory),
    }
    result["gates"] = [_gate(name, actions[name]) for name in GATES]
    return result


def run_conformance(*, case_ids=None, external_evidence: Path | None = None, evidence_root: Path = ROOT) -> dict:
    manifest = load_manifest()
    all_ids = {c["id"] for c in manifest["cases"]}
    selected = all_ids if case_ids is None else set(case_ids)
    _require(selected and selected <= all_ids, "Select one or more adopted surface cases M01--M12.")
    cases = [c for c in manifest["cases"] if c["id"] in selected]
    names = sorted({n for c in cases for n in c["required_tests"]})
    before, implementation = evidence_inventory(), implementation_identity()
    execution = _run_tests(names)
    external = verify_external_evidence(external_evidence, implementation=implementation, inventory=before,
                                        manifest=manifest, evidence_root=evidence_root)
    after = implementation_identity()
    stable = before == evidence_inventory() and implementation == after
    issues = []
    if not stable:
        issues.append("Implementation, tests, tools or predetermined fixtures changed during execution.")
    if execution["loader_errors"] or execution["fixture_errors"] or execution["unexpected_test_records"]:
        issues.append("The unittest loader, fixtures or execution identities reported errors.")
    if execution["tests_run"] != len(names):
        issues.append("Some required unittest methods did not execute exactly once.")
    outcomes = {r["test_id"]: r for r in execution["tests"]}
    gates = {g["id"]: g for g in external["gates"]}
    results = []
    failures = {"failed", "error", "unexpected_success", "expected_failure"}
    for case in cases:
        records = [outcomes[n] for n in case["required_tests"]]
        pending = list(issues)
        if any(r["status"] not in failures | {"passed"} for r in records):
            pending.append("A required test was skipped or did not execute.")
        for gate in case["external_gates"]:
            if gates[gate]["status"] != "passed":
                pending.append(gate + ": " + "; ".join(gates[gate]["issues"]))
        status = "failed" if any(r["status"] in failures for r in records) else "pending" if pending else "passed"
        results.append({**case, "status": status, "test_outcomes": dict(Counter(r["status"] for r in records)),
                        "pending_reasons": pending})
    counts = Counter(c["status"] for c in results)
    complete = selected == all_ids and counts["passed"] == 12 and not issues
    return {"schema_version": "ontokin.surface-conformance/0.1", "executed": True,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(), "implementation": implementation,
            "implementation_after_run": after, "evidence_stable_during_run": stable,
            "profile": manifest["profile"], "language_version": manifest["language_version"],
            "agent_contract": manifest["agent_contract"], "export_contract": manifest["export_contract"],
            "manifest": {"path": "docs/language-design/surface-v0.1/conformance.json", "sha256": file_identity(FIXTURES / "conformance.json")},
            "acceptance_manifest": manifest["acceptance_manifest"], "composition_manifest": manifest["composition_manifest"],
            "limits": manifest["limits"], "tolerance": manifest["tolerance"],
            "evidence_files": before, "evidence_inventory_sha256": inventory_identity(before),
            "summary": {"total": len(results), "passed": counts["passed"], "failed": counts["failed"], "pending": counts["pending"],
                        "all_adopted_cases_selected": selected == all_ids, "full_gate_complete": complete},
            "unselected_case_ids": sorted(all_ids-selected), "cases": results, "test_execution": execution,
            "external_evidence": external, "run_issues": issues,
            "scope": "The bounded adopted M01--M12 surface milestone; complete language requirements remain governed by GOAL.md.",
            "full_product_conformance_certified": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write the complete measured JSON report")
    parser.add_argument("--case", action="append", choices=[f"M{i:02}" for i in range(1, 13)])
    parser.add_argument("--external-evidence", type=Path, help="Read identified retained surface release evidence")
    parser.add_argument("--evidence-root", type=Path, default=ROOT, help="Root for every relative evidence path")
    parser.add_argument("--full-suite-only", action="store_true", help="Execute all discovered tests and emit exact regression evidence")
    parser.add_argument("--allow-pending", action="store_true", help="Allow a CI pre-attestation run to exit 0 while preserving pending gates in its report")
    args = parser.parse_args(argv)
    if args.full_suite_only and (args.case or args.external_evidence or args.allow_pending):
        parser.error("--full-suite-only cannot be combined with case selection, external evidence or --allow-pending")
    report = run_full_suite() if args.full_suite_only else run_conformance(
        case_ids=args.case, external_evidence=args.external_evidence, evidence_root=args.evidence_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
        print(json.dumps({"output": str(args.output), "summary": report["summary"]}, indent=2))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    if args.full_suite_only:
        return 0 if report["summary"]["all_passed"] else 1
    if report["summary"]["failed"] or report["run_issues"]:
        return 1
    return 2 if report["summary"]["pending"] and not args.allow_pending else 0


if __name__ == "__main__":
    raise SystemExit(main())
