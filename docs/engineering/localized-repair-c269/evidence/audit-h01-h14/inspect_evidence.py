#!/usr/bin/env python3
"""C269 read-only identity/structure audit. Never imports an observer or its tests."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import struct
import subprocess
import sys
import zipfile

BASE = "23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb"
RUN_REVISION = "5084dd69312e8da5a49aadd33cf83ba56db7c058"
PREFIX = "docs/engineering/"
OWN = PREFIX + "localized-repair-c269/evidence/audit-h01-h14/"
RUN = PREFIX + "localized-repair-c268/evidence/finalization-a3de3dd23bbf/main-integration/"
RAW = PREFIX + "localized-repair-c261/evidence/independent/"
SOURCE = PREFIX + "localized-repair-c265/evidence/independent-controls/run-06/"

METHODS = {
    "C265": [
        "test_h01_both_original_source_endpoints", "test_h01_complete_associations_are_independently_derived",
        "test_h01_utf8_byte_witnesses_are_exact", "test_h02_h04_initial_changes_follow_bytes",
        "test_h05_each_ordered_limit_changes_independently", "test_h06_inclusive_boundaries_and_zero_width",
        "test_h06_reversed_or_outside_limits_refuse_without_clamping", "test_h07_pi64_single_round_literals_and_ties",
        "test_h07_adjacent_binary64_is_observed_distinctly", "test_h08_six_signed_basis_axes_preserve_sign",
        "test_h09_nonbasis_and_invalid_axes_refuse", "test_h11_computed_numeric_fields_refuse",
        "test_h12_joint_name_and_key_are_separate", "test_h12_alias_root_module_and_class_changes",
        "test_h13_endpoint_names_keys_and_part_names_are_independent",
        "test_h13_missing_endpoint_name_cannot_guess_from_key", "test_h14_endpoint_order_is_preserved",
        "test_h14_same_object_endpoints_refuse"],
    "C267": [
        "test_original_before_after_exact_bytes", "test_initial_source_artifact_and_paired_changes",
        "test_each_limit_source_artifact_and_paired_changes", "test_inclusive_boundary_zero_width_and_invalid_ranges",
        "test_exact_deg_rad_negative_zero_and_adjacent_values", "test_six_signed_basis_axes_and_reversal",
        "test_unsupported_and_invalid_source_axes", "test_malformed_artifact_fields_and_strict_axis_shape",
        "test_computed_source_fields_do_not_use_baseline_values", "test_joint_name_and_key_have_separate_authority",
        "test_site_names_and_derived_keys_remain_distinct", "test_ordered_endpoint_swap_wrong_object_and_same_object"],
    "C268": [
        "test_original_before_after_with_path_and_string_roots", "test_relative_repository_root",
        "test_comparison_records_and_nonclaims_preserved", "test_supported_same_size_paired_axis_change_stays_raw_only",
        "test_supported_different_size_paired_initial_change_stays_raw_only",
        "test_artifact_only_initial_change_remains_visible_but_unbound"],
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def clean(value):
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_json_number": repr(value)}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    output = args.output.resolve()
    if output != root / OWN:
        parser.error("Outputs are restricted to the assigned C269 evidence directory")
    output.mkdir(parents=True, exist_ok=True)
    identities = {}
    checks = []

    def git(*arguments):
        env = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
        return subprocess.run(["git", *arguments], cwd=root, env=env, capture_output=True, check=False)

    def record(path):
        if path in identities:
            return (root / path).read_bytes()
        raw = (root / path).read_bytes()
        committed = git("show", BASE + ":" + path)
        equal = committed.returncode == 0 and committed.stdout == raw
        identities[path] = {"path": path, "revision": BASE, "bytes": len(raw), "sha256": digest(raw),
                            "matches_frozen_revision": equal}
        if not equal:
            raise AssertionError("Inspected audit input differs from frozen revision: " + path)
        return raw

    def doc(path):
        return json.loads(record(path))

    # Governing and scientific inputs. C269 mutable workflow records are excluded
    # from the immutable scientific input binding; they were read by the worker.
    for path in ("AGENTS.md", "GOAL.md", "ROLE.md", "docs/workflow/PROTOCOL.md",
                 "docs/workflow/HANDOFF.md", ".agents/skills/ontokin-delivery/SKILL.md",
                 PREFIX + "localized-repair-c260/CONTRACT.md", PREFIX + "localized-repair-c260/CONTROL-PLAN.md",
                 PREFIX + "localized-repair-c260/INPUTS.json", PREFIX + "localized-repair-c253/corpus.json",
                 "docs/language-design/OK-LANG-001-core-language-specification.md"):
        record(path)
    for name in ("before.main.ok", "after.main.ok", "hinges.ok", "before.glb", "after.glb"):
        record(PREFIX + "semantic-export-c210/evidence/proof/" + name)
    for stage, files in {
        257: ["ownership.py"],
        261: ["hinge_glb.py", "test_hinge_glb.py", "CONTROL-COVERAGE.md", "RESULTS.md", "README.md",
              "evidence/independent/independent_controls.py", "evidence/independent/REVIEW.md",
              "evidence/independent/SOURCE-BINDING.json", "evidence/integration/review/REVIEW.md"],
        265: ["source_hinges.py", "test_source_hinges.py", "RESULTS.md", "REVIEW.md", "INPUTS.json",
              "evidence/independent-controls/CONTROL-COVERAGE.json", "evidence/independent-controls/RUN-NOTES.md",
              "evidence/review/REVIEW.md", "evidence/review/REVIEW.json"],
        266: ["hinge_binding.py", "binding_control_fixtures.py", "test_hinge_binding.py", "CONTROL-COVERAGE.md",
              "REVIEW.md", "INPUTS.json"],
        267: ["hinge_compare.py", "test_hinge_compare.py", "comparison_control_fixtures.py", "CONTROL-COVERAGE.md",
              "REVIEW.md", "REVIEW.json", "INPUTS.json"],
        268: ["endpoint_reader.py", "test_endpoint_reader.py", "endpoint_control_fixtures.py", "CONTROL-COVERAGE.md",
              "REVIEW.md", "RESULTS.md", "INPUTS.json", "evidence/finalization-20261119/review/REVIEW.md"],
    }.items():
        for name in files:
            record(PREFIX + f"localized-repair-c{stage}/" + name)

    main_checks = doc(RUN + "CHECKS.json")
    assert main_checks["source_before"]["commit"] == main_checks["source_after"]["commit"] == RUN_REVISION
    assert main_checks["input_identity_unchanged"] and main_checks["passed"] and main_checks["complete"]
    before = {row["path"]: row for row in main_checks["input_files_before"]}
    after = {row["path"]: row for row in main_checks["input_files_after"]}
    checked_inputs = []
    later_documentation = []
    for path in sorted(identities):
        if path in before:
            expected = before[path]
            assert expected == after[path]
            if path == PREFIX + "localized-repair-c268/RESULTS.md":
                original = git("show", RUN_REVISION + ":" + path)
                assert original.returncode == 0 and len(original.stdout) == expected["bytes"]
                assert digest(original.stdout) == expected["sha256"]
                later_documentation.append({"path": path, "execution_revision": RUN_REVISION,
                    "execution_sha256": expected["sha256"], "audit_baseline_sha256": identities[path]["sha256"],
                    "interpretation": "Later C268 delivery documentation; not an implementation/test/fixture/contract change."})
                continue
            assert expected["bytes"] == identities[path]["bytes"] and expected["sha256"] == identities[path]["sha256"]
            checked_inputs.append(path)
    checks.append({"check": "retained_main_run_input_identity", "passed": True,
                   "path": RUN + "CHECKS.json", "execution_revision": RUN_REVISION,
                   "matched_input_paths": checked_inputs, "later_documentation": later_documentation})
    for row in main_checks["output_files"]:
        if row["path"].startswith(("c261-", "c265-", "c266-", "c267-", "c268-")):
            raw = record(RUN + row["path"])
            assert len(raw) == row["bytes"] and digest(raw) == row["sha256"]
    checks.append({"check": "retained_main_run_relevant_output_hashes", "passed": True})

    suite_index = {}
    raw_result = doc(RAW + "run-03/RESULTS.json")
    raw_binding = doc(RAW + "SOURCE-BINDING.json")
    assert raw_result["passed"] and raw_result["failures"] == 0
    for filename, expected in (("hinge_glb.py", raw_binding["readerSha256"]),
                               ("evidence/independent/independent_controls.py", raw_binding["controlsSha256"]),
                               ("evidence/independent/run-03/RESULTS.json", raw_binding["reportSha256"])):
        assert digest(record(PREFIX + "localized-repair-c261/" + filename)) == expected
    published = "a877b0a3b75595c66c321cf515c7138391af5ba2"
    published_reader = git("show", published + ":" + PREFIX + "localized-repair-c261/hinge_glb.py")
    assert published_reader.returncode == 0 and digest(published_reader.stdout) == raw_binding["readerSha256"]
    raw_rows = []
    for i, row in enumerate(raw_result["controls"]):
        groups = {int(m) for m in re.findall(r"H(\d+)", row["group"])}
        if groups & set(range(1, 15)):
            assert row["passed"]
            raw_rows.append({"id": f"C261-{i:03}", "result_pointer": f"/controls/{i}", **row})
    suite_index["C261"] = {
        "result_path": RAW + "run-03/RESULTS.json", "execution_revision": raw_binding["revision"],
        "revision_binding_path": RAW + "SOURCE-BINDING.json",
        "revision_status": "Historical local execution revision as recorded; that local commit is unavailable in this checkout. Reader bytes match the available published equivalent.",
        "published_equivalent_reader_revision": published,
        "command_source": RAW + "REVIEW.md", "python": raw_result["python"], "platform": raw_result["platform"],
        "input_recipe_path": RAW + "independent_controls.py",
        "input_retention": "Original artifacts retained; deterministic mutated-byte recipes and exact per-control hashes retained. No generated GLB archive is claimed.",
        "records": raw_rows}

    source_result = doc(SOURCE + "results.json")
    assert source_result["passed"] and source_result["failures"] == source_result["errors"] == source_result["skipped"] == 0
    for path, expected in source_result["inputs"].items():
        raw = record(path)
        assert len(raw) == expected["bytes"] and digest(raw) == expected["sha256"]
    for name, path in (("source_hinges.py.txt", PREFIX + "localized-repair-c265/source_hinges.py"),
                       ("test_source_hinges.py.txt", PREFIX + "localized-repair-c265/test_source_hinges.py")):
        assert record(SOURCE + name) == record(path)
    source_rows = []
    for i, row in enumerate(source_result["observations"]):
        if row["test"].split(".")[-1] in METHODS["C265"]:
            source_rows.append({"id": f"C265-{i:03}", "result_pointer": f"/observations/{i}", **row})
    check_i, check = next((i, c) for i, c in enumerate(main_checks["checks"]) if c["name"] == "c265-source_hinges")
    source_log = record(RUN + check["log"]["path"]).decode()
    for method in METHODS["C265"]:
        assert re.search(re.escape(method) + r" .*? \.\.\. ok", source_log), method
    suite_index["C265"] = {
        "result_path": SOURCE + "results.json", "execution_revision": None,
        "revision_status": "Detailed original run-06 records exact implementation/dependency/test hashes but no Git execution revision. The later clean 5084dd6 cohort executes identical bytes; these two runs are kept distinct.",
        "command": source_result["command"], "python": source_result["python"], "platform": source_result["platform"],
        "published_reexecution": {"result_path": RUN + "CHECKS.json", "result_pointer": f"/checks/{check_i}",
                                   "execution_revision": RUN_REVISION, "log_path": RUN + check["log"]["path"],
                                   "command": check["command"], "input_hash_binding": "input_files_before/input_files_after in CHECKS.json"},
        "input_recipe_path": PREFIX + "localized-repair-c265/test_source_hinges.py",
        "input_retention": "Exact original sources and implementation/test snapshots retained; run-06 stores every changed-input hash and byte count, with deterministic source-edit recipes rather than a changed-input archive.",
        "records": source_rows}

    zip_inspections = []
    archived_field_inspections = []
    for suite in ("C267", "C268"):
        directory = RUN + suite.lower() + "-controls/"
        result = doc(directory + "results.json")
        assert result["passed"] and not result["failures"] and not result["errors"] and not result["skipped"]
        assert result["inputCodeStableDuringRun"]
        for path, expected in result["implementationAndControlInputs"].items():
            raw = record(path)
            assert len(raw) == expected["bytes"] and digest(raw) == expected["sha256"]
        archive_path = directory + "inputs.zip"
        record(archive_path)
        count = 0
        with zipfile.ZipFile(root / archive_path) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                assert len(name.split("/")) == 1 and ".." not in name
                assert digest(archive.read(name)) == name.split(".")[0]
            records = []
            for i, row in enumerate(result["cases"]):
                if row["case"].split(".")[-1] not in METHODS[suite]:
                    continue
                records.append({"id": f"{suite}-{i:03}", "result_pointer": f"/cases/{i}", **row})
                def inspect(value):
                    nonlocal count
                    if isinstance(value, dict):
                        if isinstance(value.get("snapshot"), str) and value["snapshot"].startswith("inputs.zip!"):
                            name = value["snapshot"].split("!", 1)[1]
                            raw = archive.read(name)
                            assert len(raw) == value["bytes"] and digest(raw) == value["sha256"]
                            count += 1
                        for child in value.values():
                            inspect(child)
                    elif isinstance(value, list):
                        for child in value:
                            inspect(child)
                inspect(row)
                # Read retained GLB JSON and actual source field text; no observer runs.
                if suite == "C267" and row["artifact"].get("snapshot"):
                    raw = archive.read(row["artifact"]["snapshot"].split("!", 1)[1])
                    n = struct.unpack_from("<I", raw, 12)[0]
                    payload = json.loads(raw[20:20+n])
                    leaf_meta = row["sources"].get("hinges.ok", {})
                    leaf = archive.read(leaf_meta["snapshot"].split("!", 1)[1]) if "snapshot" in leaf_meta else b""
                    excerpts = {field: re.findall(rb"\b" + field.encode() + rb"\s*=\s*([^;]+);", leaf)
                                for field in ("parent", "child", "axis", "limits", "initial")}
                    archived_field_inspections.append({"record_id": f"{suite}-{i:03}", "artifact_sha256": digest(raw),
                        "source_hinge_fields_text": {key: [value.decode() for value in values] for key, values in excerpts.items()},
                        "first_artifact_joint": clean(payload["extras"]["ontokin"]["joints"][0])})
            zip_inspections.append({"archive_path": archive_path, "passed": True,
                "all_member_hashes_match_names": True, "member_count": len(archive.namelist()),
                "selected_call_input_witnesses_verified": count})
        suite_index[suite] = {"result_path": directory + "results.json", "execution_revision": RUN_REVISION,
            "revision_binding_path": RUN + "CHECKS.json", "revision_binding_pointer": "/source_before/commit",
            "command": result["command"], "python": result["python"], "platform": result["platform"],
            "input_archive_path": archive_path, "records": records}

    # Bind each method and helper to exact source locations without importing code.
    methods = {}
    for stage, filename in ((265, "test_source_hinges.py"), (267, "test_hinge_compare.py"),
                            (268, "test_endpoint_reader.py"), (267, "comparison_control_fixtures.py"),
                            (268, "endpoint_control_fixtures.py"), (266, "binding_control_fixtures.py")):
        path = PREFIX + f"localized-repair-c{stage}/" + filename
        tree = ast.parse(record(path))
        methods[path] = {node.name: {"start_line": node.lineno, "end_line": node.end_lineno}
                         for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

    result = {"schema": "ontokin.c269.h01-h14.readonly-evidence-inspection/0.1", "passed": True,
              "audit_input_revision": BASE, "worker": "/root/audit_h01_h14",
              "executed_command": sys.argv, "python": sys.version, "platform": platform.platform(),
              "checks": checks, "zip_inspections": zip_inspections,
              "archived_field_inspections": archived_field_inspections,
              "new_behavioral_executions": 0, "new_controls": 0,
              "unknown_operations": [], "limitations": [
                  "This audit reads hashes, source text, retained result JSON and retained GLB JSON; it executes no observer, compiler, exporter, native application or model trial.",
                  "C261 local run revision is retained from its original receipt, not manufactured from a later published revision.",
                  "C265 detailed call ledger and later revision-bound discovery result remain different historical executions."]}
    products = {"INPUT-IDENTITIES.json": {"schema": "ontokin.c269.audit-input-identities/0.1", "audit_input_revision": BASE,
                  "files": [identities[k] for k in sorted(identities)]},
                "EVIDENCE-INDEX.json": {"schema": "ontokin.c269.h01-h14.execution-index/0.1", "audit_input_revision": BASE,
                  "suites": suite_index, "method_locations": methods},
                "INSPECTION.json": result}
    for filename, data in products.items():
        (output / filename).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "input_files": len(identities),
                      "selected_execution_records": {k: len(v["records"]) for k,v in suite_index.items()},
                      "zip_inspections": zip_inspections, "new_behavioral_executions": 0}, indent=2))


if __name__ == "__main__":
    main()
