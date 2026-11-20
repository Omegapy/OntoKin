#!/usr/bin/env python3
"""Independent exact-candidate C268 semantic and path-bound review probes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import inspect
import json
import os
from pathlib import Path, PurePath
import platform
import struct
import subprocess
import sys
import tempfile
import traceback
import types
from unittest.mock import patch


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def load(path, name):
    raw = path.read_bytes()
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    engineering = repo / "docs/engineering"
    reader_path = engineering / "localized-repair-c268/endpoint_reader.py"
    reader = load(reader_path, "review_final_historical")
    comparator = load(engineering / "localized-repair-c267/hinge_compare.py", "review_final_comparator")
    source_reader = load(engineering / "localized-repair-c265/source_hinges.py", "review_final_source")
    artifact_reader = load(engineering / "localized-repair-c261/hinge_glb.py", "review_final_artifact")
    contract = json.loads((engineering / "localized-repair-c260/INPUTS.json").read_text())
    corpus = json.loads((engineering / "localized-repair-c253/corpus.json").read_text())
    frozen = {Path(row["path"]).name: row for row in contract["files"]}
    original = {name: (repo / frozen[name]["path"]).read_bytes()
                for name in ("before.main.ok", "after.main.ok", "hinges.ok", "before.glb", "after.glb")}
    checked_paths = [reader_path, engineering / "localized-repair-c268/test_endpoint_reader.py",
                     engineering / "localized-repair-c268/endpoint_control_fixtures.py",
                     engineering / "localized-repair-c268/evidence/run_checks.py",
                     engineering / "localized-repair-c260/CONTRACT.md",
                     engineering / "localized-repair-c260/CONTROL-PLAN.md",
                     engineering / "localized-repair-c260/INPUTS.json",
                     engineering / "localized-repair-c253/corpus.json"]
    checked_paths += [engineering / item[0] for item in reader.DEPENDENCIES.values()]
    checked_paths += [repo / frozen[name]["path"] for name in original]
    before = {str(path.relative_to(repo)): identity(path.read_bytes()) for path in checked_paths}
    report = {"schema": "ontokin.c268.independent-final-review-probes/1",
              "reviewer": "/root/review_c268_final",
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
              "source_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip(),
              "command": [sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
              "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
              "effective_uid": os.geteuid(), "probe": identity(Path(__file__).read_bytes()),
              "checked_inputs": before, "cases": [], "observations": [],
              "limitations": ["Finite declaration and admission evidence only",
                              "No source evaluation, export, native application, physics, accepted revision or model trial",
                              "Path object preprocessing observation is not a timing benchmark"]}

    def case(name, function):
        row = {"name": name}
        try:
            row.update(passed=True, details=function())
        except Exception as exc:
            row.update(passed=False, exception=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
        report["cases"].append(row)
        print(json.dumps({"name": name, "passed": row["passed"]}), flush=True)

    def sources(endpoint):
        return {"main.ok": original[endpoint + ".main.ok"], "hinges.ok": original["hinges.ok"]}

    # Expectations are written from the supplied .ok declarations and C260.
    # No observer, product code, expected-record helper or producer sidecar supplies them.
    expected = {}
    for root, keys in (("first", ("lower", "middle", "upper")),
                       ("second", ("bottom", "lower", "middle", "upper", "top"))):
        for key in keys:
            owner = ["keyed-rack", "demo", root, "fingers", key]
            path = root + '.fingers["' + key + '"]'
            expected[path + ".flex"] = (owner, path)
    definition = ["package", "example.hinges", "hinges", "definitions", "finger", "flex"]
    limit = float(Fraction(45) * Fraction.from_float(float.fromhex("0x1.921fb54442d18p+1")) / 180)

    def semantics(result, axis, historical):
        assert result["historicalInputsBound"] is historical
        assert (result["hingeCount"], result["siteCount"], result["objectCount"]) == (8, 16, 18)
        records = {row["path"]: row for row in result["records"]}
        assert len(records) == len(result["records"]) == 8 and records.keys() == expected.keys()
        assert {tuple(row["definitionId"]) for row in records.values()} == {tuple(definition)}
        for joint_path, (owner, owner_path) in expected.items():
            record = records[joint_path]
            assert record["id"] == owner + ["flex"]
            assert record["definitionId"] == definition
            source = record["source"]
            assert source["axis"] == axis and source["axisFrame"] == "parent-site"
            assert source["limits"] == [-limit, limit] and source["initial"] == 0
            for role, site_id, path, site_def in (
                ("parent", owner + ["pivot"], owner_path + ".pivot",
                 ["package", "example.hinges", "hinges", "definitions", "finger", "pivot"]),
                ("child", owner + ["blade", "base"], owner_path + ".blade.base",
                 ["package", "example.hinges", "hinges", "definitions", "blade", "base"])):
                endpoint = record["endpoints"][role]
                site = endpoint["source"]
                assert site["id"] == site_id and site["definitionId"] == site_def and site["path"] == path
                assert site["interface"] == "hinged.part" and site["sizeM"] == 0
                assert site["compatibilityAuthority"] == "source-only" and site["poseEvaluated"] is False
                assert endpoint["artifactPath"] == path
                assert not {"artifactDefinitionId", "artifactSpan", "artifactPose"}.intersection(endpoint)
        for flag in ("sitePosesEvaluated", "sourceValidityQualified", "acceptedRevisionQualified",
                     "completeC255Semantic", "executionAllowed", "directSiteTableObserved", "jointDefinitionOrSpanObserved"):
            assert result[flag] is False
        assert result["realTrialSuccess"] is None

    def pin_review():
        for name, raw in original.items():
            assert identity(raw) == {key: frozen[name][key] for key in ("bytes", "sha256")}
        for key, row in contract["c253MatchingPins"].items():
            assert corpus["files"][key] == row
        for endpoint, entries in reader.PINS.items():
            names = contract["historicalAdmission"][endpoint]
            assert [Path(entry[1]).name for entry in entries] == names
            for logical, path, size, digest in entries:
                row = frozen[Path(path).name]
                assert (path, size, digest) == (row["path"], row["bytes"], row["sha256"])
        return {"all_five_bytes_match_C260": True, "all_C253_matching_pins_equal": True,
                "runtime_literal_pins_equal_frozen_contract": True}

    case("historical_pin_authority", pin_review)
    for endpoint in ("before", "after"):
        def positive(endpoint=endpoint):
            value = reader.read_bound_endpoint(repo, endpoint)
            semantics(value, [0, 0, 1], True)
            assert value["sourceHashes"] == {name: identity(raw)["sha256"] for name, raw in sources(endpoint).items()}
            assert value["artifactSha256"] == identity(original[endpoint + ".glb"])["sha256"]
            return {"endpoint": endpoint, "hinges": 8, "shared_joint_definitions": 1, "sites": 16,
                    "source_derived_expectations_verified": True, "physical_and_execution_nonclaims_retained": True}
        case("independent_original_semantics_" + endpoint, positive)

    changed_sources = dict(sources("before"))
    changed_sources["hinges.ok"] = changed_sources["hinges.ok"].replace(b"axis = vec3(0, 0, 1);", b"axis = vec3(1, 0, 0);")
    assert changed_sources["hinges.ok"] != original["hinges.ok"]
    old_leaf, new_leaf = identity(original["hinges.ok"])["sha256"], identity(changed_sources["hinges.ok"])["sha256"]
    changed_sources["main.ok"] = changed_sources["main.ok"].replace(old_leaf.encode(), new_leaf.encode())
    raw = original["before.glb"]
    json_length = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + json_length])
    manifest = doc["extras"]["ontokin"]["program"]["manifest"]
    old_revision = doc["extras"]["ontokin"]["program"]["revision"]
    for unit in manifest["units"]:
        unit["source_revision"] = "sha256:" + identity(changed_sources[unit["filename"]])["sha256"]
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    new_revision = "sha256:" + identity(b"ontokin.bundle/0.1\0" + canonical)["sha256"]
    changed_glb = raw
    for filename, before_raw in sources("before").items():
        changed_glb = changed_glb.replace(identity(before_raw)["sha256"].encode(), identity(changed_sources[filename])["sha256"].encode())
    changed_glb = changed_glb.replace(old_revision.encode(), new_revision.encode())
    assert changed_glb.count(b'"axis":[0.0,0.0,1.0]') == 8
    changed_glb = changed_glb.replace(b'"axis":[0.0,0.0,1.0]', b'"axis":[1.0,0.0,0.0]')
    assert len(changed_glb) == len(raw)
    for name, data in {"main.ok": changed_sources["main.ok"], "hinges.ok": changed_sources["hinges.ok"], "paired-axis.glb": changed_glb}.items():
        (output / name).write_bytes(data)

    def raw_paired():
        source = source_reader.observe_source_hinges(changed_sources)
        artifact = artifact_reader.observe_glb_hinges(changed_glb)
        compared = comparator.compare_hinges(changed_sources, changed_glb)
        assert source["historicalInputsBound"] is artifact["historicalInputsBound"] is False
        assert len(source["records"]) == len(artifact["records"]) == 8
        assert all(row["axis"] == [1, 0, 0] for row in source["records"])
        assert all(row["claims"]["axis"] == [1, 0, 0] for row in artifact["records"])
        semantics(compared, [1, 0, 0], False)
        return {"changed_axis": [1, 0, 0], "all_three_raw_interfaces_preserved": True,
                "sources": {name: identity(data) for name, data in changed_sources.items()}, "artifact": identity(changed_glb)}
    case("independent_paired_raw_change", raw_paired)

    def changed_historical():
        outcomes = []
        with tempfile.TemporaryDirectory(dir=output, prefix="inputs-") as temporary:
            destination = Path(temporary) / "docs/engineering/semantic-export-c210/evidence/proof"
            destination.mkdir(parents=True)
            selected = {"before.main.ok": changed_sources["main.ok"], "hinges.ok": changed_sources["hinges.ok"], "before.glb": changed_glb}
            for filename, content in selected.items():
                (destination / filename).write_bytes(content)
            for name, pointer in (("before.main.ok", "/historicalAdmission/main.ok"),
                                  ("hinges.ok", "/historicalAdmission/hinges.ok"),
                                  ("before.glb", "/historicalAdmission/artifact")):
                with patch.object(reader, "_compare_captured", side_effect=AssertionError("admission failure reached comparator")):
                    try:
                        reader.read_bound_endpoint(temporary, "before")
                    except reader.Fault as exc:
                        assert (exc.code, exc.reason, exc.pointer) == ("HISTORICAL_BINDING", "HASH", pointer)
                        assert not hasattr(exc, "records")
                        outcomes.append({"changed_file": name, "code": exc.code, "reason": exc.reason, "pointer": exc.pointer})
                    else:
                        raise AssertionError("supported changed bytes acquired historical authority")
                (destination / name).write_bytes(original[name])
        return {"isolated_each_admission_stage": outcomes}
    case("paired_change_is_never_historical", changed_historical)

    def original_fix_delta():
        previous = (engineering / "localized-repair-c268/evidence/implementation/endpoint-length-fix/endpoint_reader.py.before.txt").read_bytes()
        old = b"if type(endpoint) is not str or endpoint not in PINS:"
        new = b"if type(endpoint) is not str or len(endpoint) not in (5, 6) or endpoint not in PINS:"
        assert previous.count(old) == 1 and previous.replace(old, new) == reader_path.read_bytes()
        return {"previous": identity(previous), "current": identity(reader_path.read_bytes()), "sole_reader_delta_is_guard": True}
    case("mandatory_finding_fix_is_exact", original_fix_delta)

    def string_root_early_cap():
        with patch.object(reader.os, "open", side_effect=AssertionError("oversize root accessed filesystem")):
            for value in ("x" * 1000001, "\ud800" + "x" * 1000000):
                try:
                    reader.read_bound_endpoint(value, "before")
                except reader.Fault as exc:
                    assert (exc.code, exc.reason) == ("RESOURCE_LIMIT", "PATH_LIMIT")
                else:
                    raise AssertionError("oversize string root admitted")
        return {"one_million_character_roots_refused_before_scan_or_file_open": True}
    case("built_in_string_root_bound", string_root_early_cap)

    # Record a real remaining preprocessing limitation separately from contract acceptance.
    # Native pathlib objects may be lazy: str(Path(...)) renders before C268's text cap.
    parsed_lengths = []
    native_parse = PurePath._parse_path.__func__
    def inspect_parse(cls, value):
        parsed_lengths.append(len(value))
        return native_parse(cls, value)
    native_root = Path("x/" * 100000 + "x")
    with patch.object(PurePath, "_parse_path", classmethod(inspect_parse)), \
         patch.object(reader.os, "open", side_effect=AssertionError("oversize Path accessed filesystem")):
        try:
            reader.read_bound_endpoint(native_root, "before")
        except reader.Fault as exc:
            path_outcome = {"code": exc.code, "reason": exc.reason}
        else:
            raise AssertionError("oversize Path admitted")
    report["observations"].append({"id": "PATH-PREPROCESSING", "native_path_parsed_character_lengths": parsed_lengths,
                                   "final_refusal": path_outcome,
                                   "stdlib_str_source": inspect.getsource(PurePath.__str__),
                                   "meaning": "Native Path conversion precedes the wrapper text cap; string roots receive the cap before scanning. No file admission bypass observed."})
    after = {str(path.relative_to(repo)): identity(path.read_bytes()) for path in checked_paths}
    report["inputs_unchanged"] = before == after
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["passed"] = report["inputs_unchanged"] and all(row["passed"] for row in report["cases"])
    (output / "RESULTS.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "cases": len(report["cases"]), "inputs_unchanged": report["inputs_unchanged"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
