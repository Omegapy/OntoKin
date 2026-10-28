"""Independently audit retained regression receipts; never import or run OntoKin.

All discovered focused runs and local-core summaries are audited.  A failed
product run is acceptable evidence only with --allow-failures; that switch
never permits missing execution, skips, changed inputs, or invalid receipts.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def unprefix(value):
    return value.removeprefix("sha256:")


def read(path):
    require(path.is_file() and not path.is_symlink(), f"Missing regular file: {path}")
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), f"Changed while reading: {path}")
    return raw


def json_read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key {key}: {path}")
            result[key] = value
        return result
    return json.loads(read(path), object_pairs_hook=pairs)


def member(root, name):
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts, f"Unsafe member: {name}")
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()), f"Escaping member: {name}")
    return path


def identity(root, item):
    raw = read(member(root, item["path"]))
    require(len(raw) == item["bytes"] and digest(raw) == unprefix(item["sha256"]),
            f"Wrong bytes/hash: {root / item['path']}")


def inventory(data):
    rows = data["files"]
    paths = [row["path"] for row in rows]
    require(rows and len(paths) == len(set(paths)), "Empty or duplicate input inventory")
    for row in rows:
        require(isinstance(row["bytes"], int) and row["bytes"] >= 0 and
                re.fullmatch(r"[0-9a-f]{64}", unprefix(row["sha256"])), "Invalid input identity")
        require(not Path(row["path"]).is_absolute() and ".." not in Path(row["path"]).parts,
                "Invalid input path")
    if "file_count" in data:
        require(data["file_count"] == len(rows), "Wrong input inventory count")
    if "sha256" in data:
        encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        require(digest(encoded) == unprefix(data["sha256"]), "Wrong input inventory aggregate hash")
    return {row["path"]: (row["bytes"], row["sha256"]) for row in rows}


def parse_log(raw):
    """Read actual method starts and terminal outcomes, including description lines."""
    text = raw.decode("utf-8")
    starts, events = [], defaultdict(list)
    current = None
    for line in text.splitlines():
        if re.fullmatch(r"Ran \d+ tests? in [0-9.]+s", line):
            break
        match = re.match(r"^test\S+ \(([^)]+)\)(.*)$", line)
        if match:
            current = match.group(1)
            starts.append(current)
        status = re.search(r"(?:\.\.\.\s+|^)(ok|FAIL|ERROR|skipped(?: .*)?|expected failure|unexpected success)\s*$", line)
        if current is not None and status:
            value = status.group(1)
            events[current].append("skipped" if value.startswith("skipped") else value)
    require(starts and len(starts) == len(set(starts)), "Missing or duplicate raw test starts")
    require(set(events) == set(starts), "Raw log has incomplete method outcomes")
    footers = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", text, re.M)
    endings = re.findall(r"^(OK|FAILED)(?: \(([^\n]*)\))?$", text, re.M)
    require(len(footers) == len(endings) == 1, "Missing or ambiguous completion footer")
    require(int(footers[0][0]) == len(starts), "Footer count differs from actual starts")
    terminal = re.search(r"^(OK|FAILED)(?: \(([^\n]*)\))?\s*\Z", text, re.M)
    require(terminal is not None, "Log lacks a terminal result")
    counts = Counter(value for values in events.values() for value in values)
    require(not (counts["skipped"] or counts["expected failure"] or counts["unexpected success"]),
            "Skipped, expected-failure, or unexpected-success execution is not accepted")
    footer_counts = {key.strip(): int(value) for key, value in re.findall(r"([a-z ]+)=(\d+)", endings[0][1])}
    require(footer_counts.get("failures", 0) == counts["FAIL"] and
            footer_counts.get("errors", 0) == counts["ERROR"], "Footer failure/error count differs from raw outcomes")
    require(not any(footer_counts.get(key, 0) for key in ("skipped", "expected failures", "unexpected successes")),
            "Unacceptable footer outcome")
    failed = bool(counts["FAIL"] or counts["ERROR"])
    require((endings[0][0] == "FAILED") == failed, "Footer result disagrees with outcomes")
    for values in events.values():
        require(values == ["ok"] or ("ok" not in values and set(values) <= {"FAIL", "ERROR"}),
                "Duplicated or inconsistent method completion")
    return {"ids": starts, "events": dict(events), "tests": len(starts),
            "passed": sum(values == ["ok"] for values in events.values()),
            "failures": counts["FAIL"], "errors": counts["ERROR"], "failed": failed,
            "elapsed_seconds": float(footers[0][1])}


def command(root, name, expected_exit):
    path = root / "commands" / (name + ".json")
    receipt = json_read(path)
    for stream in ("stdout", "stderr"):
        identity(path.parent, receipt[stream])
    require(receipt["exit_status"] == expected_exit, f"Wrong actual command exit: {name}")
    require(receipt.get("timed_out") is False, f"Timed out or missing timeout receipt: {name}")
    require(receipt.get("log_paths_stable") is True, f"Unstable or unverified log paths: {name}")
    require(receipt.get("started_at") and receipt.get("finished_at"), f"Incomplete command: {name}")
    if "opened_log_inodes" in receipt:
        require(receipt["opened_log_inodes"] == receipt["closed_log_inodes"], "Log inode changed")
    if receipt.get("schema_version") == "ontokin.serial-command/0.2":
        opened, closed = receipt["log_open_identities"], receipt["log_close_identities"]
        require(set(opened) == set(closed) == {"stdout", "stderr"} and opened == closed,
                "Command log device/inode identities changed")
        require(all(isinstance(value, list) and len(value) == 2 and
                    all(isinstance(number, int) and number >= 0 for number in value)
                    for value in opened.values()), "Invalid command log identity")
    return receipt


def focused(root, directory):
    report = json_read(directory / "report.json")
    if not (directory / "tests.json").exists():
        return preflight_failure(root, directory, report)
    tests = json_read(directory / "tests.json")
    before = json_read(directory / "inputs-before.json")
    after = json_read(directory / "inputs-after.json")
    require(before == after and report["inputs_stable"] is True, "Focused inputs changed")
    inventory(before)
    require(before["git"]["status"] == "", "Focused source was not clean")
    require(report["source_commit"] == before["git"]["commit"] and
            report["source_tree"] == before["git"]["tree"], "Focused source identity mismatch")
    require(digest(read(directory / "executed-driver.py")) == report["driver_sha256"], "Focused driver mismatch")
    raw = read(directory / "tests.log")
    require(digest(raw) == report["test_log_sha256"] and report["test_log_complete"] is True,
            "Focused raw-log identity mismatch")
    actual = parse_log(raw)
    require(tests["started"] == actual["ids"], "Structured/raw starts differ")
    require(tests["expected_failures"] == tests["unexpected_successes"] == 0, "Unexpected test outcomes")
    rows = tests["results"]
    grouped = defaultdict(list)
    labels = {"passed": "ok", "failed": "FAIL", "error": "ERROR", "skipped": "skipped"}
    for row in rows:
        require(row["status"] in labels, "Unknown result status")
        grouped[row["test_id"]].append(labels[row["status"]])
        if row["status"] in ("failed", "error"):
            require(bool(row.get("traceback")), "Missing complete failure traceback")
    require(dict(grouped) == actual["events"], "Structured/raw outcomes differ")
    for key, expected in (("test_count", actual["tests"]), ("passed_count", actual["passed"]),
                          ("failures", actual["failures"]), ("errors", actual["errors"]), ("skips", 0)):
        require(report[key] == expected, f"Wrong reported {key}")
    require(report["status"] == ("failed" if actual["failed"] else "passed"), "Focused status mismatch")
    receipt = command(root, directory.name, int(actual["failed"]))
    require(receipt["command"][1:] == report["command"][1:], "Focused argv mismatch")
    return {"kind": "focused", "name": directory.name, "source_commit": report["source_commit"],
            "source_tree": report["source_tree"], "tests": actual["tests"], "passed": actual["passed"],
            "failures": actual["failures"], "errors": actual["errors"], "failed": actual["failed"],
            "test_ids": actual["ids"], "log_sha256": digest(raw)}


def preflight_failure(root, directory, report):
    """Retain the verified driver's clean-check refusal before test collection."""
    require(report["schema_version"] == "ontokin.native-field-development-tests/0.1" and
            report["status"] == "failed", "Unexecuted report is not an explicit failure")
    require(report["failure"] == {"type": "ValueError", "message":
            "Execute artifact evidence from a clean committed checkout"},
            "Unrecognized unexecuted failure; inspect separately")
    require("before=snapshot();write_json" in report["traceback"] and
            "in snapshot" in report["traceback"] and report["failure"]["message"] in report["traceback"],
            "Preflight failure lacks its complete snapshot traceback")
    for filename in ("tests.json", "tests.log", "inputs-before.json", "inputs-after.json"):
        require(not (directory / filename).exists(), "Preflight failure has contradictory execution files")
    require(not any(key in report for key in ("test_count", "passed_count", "source_commit", "source_tree")),
            "Preflight refusal cannot claim test counts or verified source identity")
    known_driver = "612741c6614583895c70a4d1e9f7a4c271bd9a2415ab364b8f4d8e13dd6c74f7"
    require(digest(read(directory / "executed-driver.py")) == report["driver_sha256"] == known_driver,
            "Preflight control ordering requires the reviewed driver bytes")
    receipt = command(root, directory.name, 1)
    require(receipt["command"][1:] == report["command"][1:] and
            receipt["working_directory"] == report["working_directory"], "Preflight command mismatch")
    require(report.get("started_at") and report.get("finished_at"), "Incomplete preflight report")
    return {"kind": "preflight_not_executed", "name": directory.name,
            "source_commit": None, "source_tree": None, "tests_executed": False,
            "tests": 0, "passed": 0, "failures": 0, "errors": 0, "failed": True,
            "test_ids": [], "failure": report["failure"], "traceback": report["traceback"],
            "limitation": "Setup refused before input snapshot and test collection; no test or product pass is claimed."}


def construction_result(root, data, source_rows):
    """Audit the stock runner's actual named-method records and adopted case map."""
    manifest_path = "docs/language-design/construction-v0.1/validation-cases.json"
    frozen_path = root / "inputs" / "construction-validation-cases.json"
    frozen_raw = read(frozen_path)
    frozen = json_read(frozen_path)
    require((len(frozen_raw), "sha256:" + digest(frozen_raw)) == source_rows[manifest_path],
            "Retained construction manifest differs from executed source inputs")
    require(data["schema_version"] == "ontokin.construction-conformance/0.1" and data["executed"] is True and
            data["evidence_stable_during_run"] is True and not data["run_issues"] and
            data["implementation"] == data["implementation_after_run"], "Incomplete or unstable construction execution")
    require(data["manifest"]["path"] == manifest_path and
            unprefix(data["manifest"]["sha256"]) == digest(frozen_raw) and data["settings"] == frozen["settings"] and
            data["settings"]["max_operations"] == 100000 and data["settings"]["max_elapsed_ms"] == 30000,
            "Construction authority or protected settings changed")
    evidence_paths = [item["path"] for item in data["evidence_files"]]
    require(len(evidence_paths) == len(set(evidence_paths)) and evidence_paths,
            "Duplicate or missing construction input identities")
    for item in data["evidence_files"]:
        require(unprefix(item["sha256"]) == unprefix(source_rows[item["path"]][1]),
                f"Construction evidence input differs: {item['path']}")
    cases = frozen["cases"]
    require([case["id"] for case in cases] == [f"C{i:02}" for i in range(1, 21)], "Incomplete adopted case map")
    required = sorted({name for case in cases for name in case["required_tests"]})
    execution = data["test_execution"]
    rows = execution["tests"]
    ids = [row["test_id"] for row in rows]
    require(ids == required and len(ids) == len(set(ids)) == execution["tests_run"] ==
            execution["unique_required"] == 128, "Construction methods are missing, duplicated, or unexecuted")
    require(not any(execution[key] for key in ("loader_errors", "fixture_errors", "unexpected_test_records")),
            "Construction loader or fixture failure")
    for row in rows:
        require(row["status"] in ("passed", "failed", "error") and
                isinstance(row["elapsed_seconds"], (int, float)) and 0 <= row["elapsed_seconds"] < float("inf"),
                "Construction skip, incomplete, or unexpected outcome")
        require((not row["failures"]) if row["status"] == "passed" else
                bool(row["failures"]) and all(isinstance(value, str) and value for value in row["failures"]),
                "Construction failure traceback missing or inconsistent")
    counts = Counter(row["status"] for row in rows)
    require(execution["outcomes"] == dict(counts), "Construction method summary mismatch")
    by_id = {row["test_id"]: row for row in rows}
    require([case["id"] for case in data["cases"]] == [case["id"] for case in cases], "Construction case membership mismatch")
    for expected, actual in zip(cases, data["cases"]):
        require(actual["required_tests"] == expected["required_tests"], "Construction case test mapping changed")
        outcomes = Counter(by_id[name]["status"] for name in expected["required_tests"])
        pending = list(expected.get("unbound_requirements", []))
        if expected["external_gates"] and data["external_evidence"]["status"] != "passed":
            pending.append("The identified independent visual-delivery gate is pending.")
        status = "failed" if outcomes["failed"] or outcomes["error"] else "pending" if pending else "passed"
        require(actual["status"] == status and actual["test_outcomes"] == dict(outcomes) and
                actual["pending_reasons"] == pending, "Construction case outcome is inconsistent")
    case_counts = Counter(case["status"] for case in data["cases"])
    require(data["summary"] == {"total": 20, "passed": case_counts["passed"], "failed": case_counts["failed"],
            "pending": case_counts["pending"], "all_adopted_cases_selected": True,
            "case_gate_complete": case_counts["passed"] == 20}, "Construction case summary mismatch")
    return {"tests": len(ids), "passed": counts["passed"], "failures": counts["failed"], "errors": counts["error"],
            "test_ids": ids, "case_summary": data["summary"],
            "failed_test_records": [row for row in rows if row["status"] != "passed"]}


def local_step(root, directory):
    report = json_read(directory / "report.json")
    require(report["schema_version"] == "ontokin.local-step-development/0.1", "Unknown local-step schema")
    before, after = (json_read(directory / name) for name in ("inputs-before.json", "inputs-after.json"))
    require(before == after and report["inputs_stable"] is True, "Diagnostic step inputs changed")
    source_rows = inventory(before)
    git_before, git_after = report["git_before"], report["git_after"]
    require(git_before == git_after and git_before["available"] and not git_before["tracked_worktree_status"] and
            not git_before["untracked_source_files"] and report["source_commit"] == git_before["local_head"] and
            report["source_tree"] == git_before["local_tree"], "Diagnostic step source identity mismatch")
    require(report["driver_sha256"] == digest(read(root / "drivers" / "run_local_step.py")) and
            report["stock_driver_sha256"] == unprefix(source_rows["tools/check_local.py"][1]), "Diagnostic driver mismatch")
    require(report["complete_default_driver_pass_claimed"] is False and report["release_acceptance"] is False,
            "Diagnostic retry cannot replace complete default validation")
    step = report["step"]
    require(step["id"] == "construction" and step["cwd"] == report["source_root"] and
            step["status"] in ("passed", "failed") and step["returncode"] in (0, 1) and "reason" not in step,
            "Incomplete diagnostic stock step")
    require(step["argv"][1:6] == ["-m", "tools.verify_construction_ci", "--external-evidence",
            "docs/engineering/construction-validation/external-gate.json", "--output"] and len(step["argv"]) == 7,
            "Diagnostic did not run the complete stock construction command")
    identity(directory, {"path": step["log"], **step["log_identity"]})
    require(len(step["reports"]) == 1 and step["reports"][0]["path"] == "reports/construction.json",
            "Missing complete construction report")
    identity(directory, step["reports"][0])
    actual = construction_result(root, json_read(directory / "reports" / "construction.json"), source_rows)
    failed = step["returncode"] != 0
    require(report["status"] == step["status"] == ("failed" if failed else "passed"), "Diagnostic step status mismatch")
    if not failed:
        require(actual["passed"] == 128 and actual["case_summary"]["failed"] == 0, "Passing step contains test failures")
    else:
        require("Traceback" in read(member(directory, step["log"])).decode("utf-8"), "Failed step lacks raw traceback")
    receipt = command(root, directory.name, int(failed))
    require(receipt["command"][1:] == report["command"][1:] and receipt["working_directory"] == report["source_root"],
            "Diagnostic command receipt mismatch")
    return {"kind": "local_step", "name": directory.name, "source_commit": report["source_commit"],
            "source_tree": report["source_tree"], "failed": failed, **actual,
            "complete_default_driver_pass_claimed": False}


def local_core(root, directory):
    summary = json_read(directory / "summary.json")
    if summary.get("steps") == []:
        return local_setup_failure(root, directory, summary)
    before = json_read(directory / "source-before.json")
    after = json_read(directory / "source-after.json")
    require(before == after and summary["source_unchanged"] is True and
            summary["git_revision_unchanged"] is True, "Local-core inputs changed")
    inventory(before)
    identity(directory, summary["source_inventory"])
    identities = [summary[name] for name in ("git", "workspace_git", "git_after")]
    pairs = {(item["local_head"], item["local_tree"]) for item in identities}
    require(len(pairs) == 1 and all(item["available"] and not item["tracked_worktree_status"]
            and not item["untracked_source_files"] for item in identities), "Local-core source identity mismatch")
    commit, tree = next(iter(pairs))
    collection_path = directory / "full-test-inventory.json"
    if not collection_path.is_file():
        collection_path = root / "full-test-inventory.json"
    collection = json_read(collection_path)
    require(collection["source_commit"] == commit and collection["source_tree"] == tree,
            "Collected inventory belongs to another source")
    expected = collection["test_ids"]
    require(collection["method_count"] == len(expected) == len(set(expected)), "Bad collection count")
    steps = summary["steps"]
    require([step["id"] for step in steps] == summary["planned_steps"] and not summary["not_executed_steps"],
            "Local driver did not execute its complete plan")
    require([step["id"] for step in steps] ==
            ["unit-tests", "source", "agent", "construction", "surface", "impulse", "documents"],
            "Expected the complete default core plan")
    actual = None
    construction = None
    for step in steps:
        identity(directory, {"path": step["log"], **step["log_identity"]})
        require(step["status"] in ("passed", "failed") and step["returncode"] in (0, 1), "Incomplete local step")
        require("reason" not in step, "Local step has a timeout or verification problem")
        require((step["status"] == "passed") == (step["returncode"] == 0), "Local step exit mismatch")
        for report in step["reports"]:
            identity(directory, report)
        if step["id"] == "construction":
            construction = construction_result(root, json_read(directory / "reports" / "construction.json"), inventory(before))
        if step["id"] == "unit-tests":
            actual = parse_log(read(member(directory, step["log"])))
            require(Counter(actual["ids"]) == Counter(expected), "Full suite differs from complete collection")
            execution = step["test_execution"]
            require(execution["tests_run"] == execution["executed_without_skips"] == actual["tests"] and
                    execution["skipped"] == execution["expected_failures"] == 0, "Full summary counts differ")
            require(execution["complete_regression_passed"] is (not actual["failed"]) and
                    step["returncode"] == int(actual["failed"]), "Full regression status mismatch")
    failed = any(step["status"] != "passed" for step in steps)
    require(summary["status"] == ("failed" if failed else "passed") and
            summary["exit_code"] == int(failed), "Full driver outcome mismatch")
    command(root, directory.name, int(failed))
    return {"kind": "local_core", "name": directory.name, "source_commit": commit,
            "source_tree": tree, "tests": actual["tests"], "passed": actual["passed"],
            "failures": actual["failures"], "errors": actual["errors"], "failed": failed,
            "unittest_passed": not actual["failed"], "driver_passed": not failed,
            "failed_steps": [step["id"] for step in steps if step["status"] != "passed"],
            "construction": construction,
            "test_ids": actual["ids"], "pending_external_cases": summary["pending_external_cases"]}


def local_setup_failure(root, directory, summary):
    """Bind a specific refused workspace copy; it supplies no executed tests."""
    require(summary["schema_version"] == "ontokin.local-checks/0.1" and
            summary["status"] == "failed" and summary["exit_code"] == 1 and
            summary["steps"] == [] and summary.get("error") ==
            "Source changed while the isolated workspace was copied.",
            "Unrecognized local setup failure; inspect separately")
    require("planned_steps" not in summary and not (directory / "logs").exists() and
            not (directory / "reports").exists(), "Setup refusal contains execution evidence")
    before = json_read(directory / "source-before.json")
    copied = json_read(directory / "workspace-after-setup-failure.json")
    source_rows, copied_rows = inventory(before), inventory(copied)
    identity(directory, summary["source_inventory"])
    missing = sorted(set(source_rows) - set(copied_rows))
    extra = sorted(set(copied_rows) - set(source_rows))
    changed = sorted(name for name in set(source_rows) & set(copied_rows)
                     if source_rows[name] != copied_rows[name])
    require(not missing and not changed and len(extra) == 1,
            "Refused copy does not retain identical inputs plus one extra file")
    comparison = json_read(root / "review" / (directory.name + "-setup-comparison.json"))
    require(comparison["source_before_count"] == comparison["source_current_count"] == len(source_rows) and
            comparison["workspace_count"] == len(copied_rows) and
            comparison["source_changed"] == {"missing": [], "extra": [], "changed": []} and
            comparison["workspace_diff"] == {"missing": missing, "extra": extra, "changed": changed},
            "Post-failure comparison does not agree with retained inventories")
    source_git, copied_git = summary["git"], summary["workspace_git"]
    require(source_git["available"] and copied_git["available"] and
            source_git["local_head"] == copied_git["local_head"] and
            source_git["local_tree"] == copied_git["local_tree"] and
            source_git["tracked_worktree_status"] == copied_git["tracked_worktree_status"] == "" and
            source_git["untracked_source_files"] == [] and copied_git["untracked_source_files"] == extra,
            "Refused-copy Git metadata does not identify the observed extra file")
    receipt = command(root, directory.name, 1)
    require(receipt["working_directory"] == summary["source_root"] and
            "tools/check_local.py" in receipt["command"], "Refused-copy command mismatch")
    require(summary.get("started_at") and summary.get("finished_at"), "Incomplete setup-failure summary")
    return {"kind": "preflight_not_executed", "name": directory.name,
            "source_commit": source_git["local_head"], "source_tree": source_git["local_tree"],
            "tests_executed": False, "tests": 0, "passed": 0, "failures": 0,
            "errors": 0, "failed": True, "test_ids": [], "failure": summary["error"],
            "source_file_count": len(source_rows), "workspace_file_count": len(copied_rows),
            "workspace_diff": {"missing": missing, "extra": extra, "changed": changed},
            "source_inventory_sha256": before["sha256"], "workspace_inventory_sha256": copied["sha256"],
            "limitation": "Local driver refused before planning or running tests. Copied original input bytes agree; the extra workspace file and the post-failure source-comparison receipt are retained separately."}


def final_checkpoint(root, results):
    """Bind every checkpoint attempt; keep final unittest and driver claims separate."""
    commit = "99d683741d5eea20910c319463871dec8cd9afce"
    tree = "8d75db307b98c56e587021e900d7c254926be348"
    late = ["unit-offsets", "axis-recording", "child-origins",
            "sequential", "sparse-cartesian", "source-cartesian"]
    declared = {
        "original-candidate-plan": [
            "endpoint-cancellation-001", "endpoint-bytes-001", "pending-output-001",
            "phase-operands-001", "stale-anchor-001", "original-affected-modules-001"],
        "late-reproduction-plan": [f"late-{name}-{role}-001"
                                   for name in late for role in ("candidate", "baseline")],
        "baseline-retry-plan": [f"late-{name}-baseline-002" for name in late],
        "final-focused-plan": [*(f"corrected-{name}-001" for name in late), "combined-modules-001"],
        "full-local-plan": ["local-core-001"],
        "full-local-retry-plan": ["local-core-002"],
        "construction-retry-plan": ["program-artifact-retry-001", "construction-retry-001"],
    }
    if (root / "full-local-final-plan.json").exists():
        declared["full-local-final-plan"] = ["local-core-003"]
    attempt_count = 35 + int("full-local-final-plan" in declared)
    require({p.stem for p in root.glob("*-plan.json")} == set(declared),
            "The declared command plans are not present exactly")
    require({p.name for p in root.glob("*-plan-outcomes.json")} ==
            {name + "-outcomes.json" for name in declared},
            "The declared plan outcome inventories are not present exactly")
    names = [name for group in declared.values() for name in group]
    require(len(names) == len(set(names)) == attempt_count, "Wrong checkpoint command membership")
    command_files = list((root / "commands").glob("*.json"))
    completed = {p.stem for p in command_files if not p.name.endswith(".started.json")}
    started = {p.name.removesuffix(".started.json") for p in command_files
               if p.name.endswith(".started.json")}
    require(completed == started == set(names), "Missing or undeclared command receipts")
    require(len(results) == attempt_count and {item["name"] for item in results} == set(names),
            "Audited reports do not cover every declared attempt")
    serial_hash = digest(read(root / "drivers" / "run_serial.py"))
    for plan_name, expected_names in declared.items():
        plan = json_read(root / (plan_name + ".json"))
        outcomes = json_read(root / (plan_name + "-outcomes.json"))
        require([item["name"] for item in plan] == expected_names and
                [item["name"] for item in outcomes] == expected_names,
                f"Plan/outcome membership or ordering differs: {plan_name}")
        for entry, outcome in zip(plan, outcomes):
            name = entry["name"]
            receipt = json_read(root / "commands" / (name + ".json"))
            opening = json_read(root / "commands" / (name + ".started.json"))
            require(all(receipt.get(key) == value for key, value in opening.items()),
                    f"Initial and final command metadata differ: {name}")
            require(receipt["command"] == entry["command"] and
                    receipt["working_directory"] == entry["cwd"] and
                    receipt["timeout_seconds"] == entry.get("timeout", 900) and
                    receipt["driver_sha256"] == serial_hash,
                    f"Command differs from its declared plan or driver: {name}")
            require(outcome == {"name": name, "exit_status": receipt["exit_status"],
                    "timed_out": receipt["timed_out"], "log_paths_stable": receipt["log_paths_stable"],
                    "expected_exit_for_plan": entry.get("expected_exit", 0)},
                    f"Outcome differs from actual receipt: {name}")
            # Historical mismatches between intended and actual exit remain failures.
    by_name = {item["name"]: item for item in results}
    complete_driver_names = ["local-core-002"] + declared.get("full-local-final-plan", [])
    final_names = declared["final-focused-plan"] + complete_driver_names
    for name in final_names:
        item = by_name[name]
        require(item["kind"] in ("focused", "local_core") and
                item["source_commit"] == commit and item["source_tree"] == tree,
                f"Final run did not execute on the required cut: {name}")
        if name.startswith("corrected-"):
            require(item["tests"] == 1, f"Expected one complete corrected method: {name}")
    require(by_name["combined-modules-001"]["kind"] == "focused" and
            by_name["local-core-002"]["kind"] == "local_core", "Missing mandatory final executions")
    for name in declared["construction-retry-plan"]:
        require(by_name[name]["source_commit"] == commit and by_name[name]["source_tree"] == tree,
                f"Diagnostic retry belongs to another cut: {name}")
    require(by_name["program-artifact-retry-001"]["kind"] == "focused" and
            by_name["program-artifact-retry-001"]["tests"] == 1 and
            by_name["construction-retry-001"]["kind"] == "local_step",
            "Diagnostic retries must remain separate complete method/step executions")
    protocol_path = root / "review" / "construction-followup-protocol.json"
    protocol_sha = "0243c134ac7cb9754974dbf24f05dea50dfe79c5bae5d78268bcb50f7d99c8b8"
    require(digest(read(protocol_path)) == protocol_sha, "Predeclared follow-up protocol changed")
    protocol = json_read(protocol_path)
    require(protocol["source_commit"] == commit and protocol["source_tree"] == tree and
            by_name["program-artifact-retry-001"]["test_ids"] == [protocol["failed_method"]],
            "Diagnostic retry does not match the predeclared failing method")
    both_retries_passed = all(not by_name[name]["failed"] for name in declared["construction-retry-plan"])
    require("full-local-final-plan" not in declared or both_retries_passed,
            "Additional full run violated its predeclared prerequisite")
    for name in declared["construction-retry-plan"]:
        receipt = json_read(root / "commands" / (name + ".json"))
        require(datetime.fromisoformat(receipt["started_at"]) >= datetime.fromisoformat(protocol["declared_at"]),
                "Diagnostic retry preceded its declared protocol")
    if "full-local-final-plan" in declared:
        entry, = json_read(root / "full-local-final-plan.json")
        require(entry["timeout"] == 3600 and entry["command"][1:4] ==
                ["tools/check_local.py", "--timeout", "2400"], "Additional default-driver allowance changed")
        receipt = json_read(root / "commands" / "local-core-003.json")
        for name in declared["construction-retry-plan"]:
            prior = json_read(root / "commands" / (name + ".json"))
            require(datetime.fromisoformat(receipt["started_at"]) >= datetime.fromisoformat(prior["finished_at"]),
                    "Additional full run began before its prerequisite completed")

    collection = json_read(root / "full-test-inventory.json")
    inputs = json_read(root / "collection-inputs.json")
    require(collection["source_commit"] == inputs["git"]["commit"] == commit and
            collection["source_tree"] == inputs["git"]["tree"] == tree and
            inputs["git"]["status"] == "" and collection["inputs_stable"] is True and
            collection["product_tests_executed"] is False, "Collection provenance mismatch")
    require(collection["driver_sha256"] == digest(read(root / "drivers" / "collect_inventory.py")),
            "Collection driver hash mismatch")
    collected_inputs = inventory(inputs)
    bound_paths = [root / "execution" / "combined-modules-001" / name
                   for name in ("inputs-before.json", "inputs-after.json")]
    bound_paths += [root / name / filename for name in complete_driver_names
                    for filename in ("source-before.json", "source-after.json")]
    bound_paths += [root / "local-step" / "construction-retry-001" / filename
                    for filename in ("inputs-before.json", "inputs-after.json")]
    bound_paths += [root / "execution" / "program-artifact-retry-001" / filename
                    for filename in ("inputs-before.json", "inputs-after.json")]
    for path in bound_paths:
        require(inventory(json_read(path)) == collected_inputs,
                f"Collection and final execution input bytes differ: {path}")
    ids = collection["test_ids"]
    require(collection["method_count"] == len(ids) == len(set(ids)) == 3064,
            "Wrong complete final collection")
    groups = {
        "focused115": ["test_reach_certificate_native_fields", "test_reach_certificate_term_reuse",
                       "test_reach_certificate_zero_quarter"],
        "related194": ["test_reach_certificate_native_fields", "test_reach_certificate_term_reuse",
                       "test_reach_certificate_zero_quarter", "test_reach_certificate_thresholds",
                       "test_reach_conformance", "test_reach_certificate_coefficients",
                       "test_reach_certificate_single_pass", "test_reach_independent_sparse_totals",
                       "test_reach_recurring_endpoint_claims"],
        "original_affected63": ["test_reach_endpoint_traversal", "test_reach_pending_output",
                               "test_reach_phase_reuse", "test_reach_endpoint_reuse",
                               "test_reach_endpoint_reduction", "test_reach_phase", "test_reach_transfer_bounds"],
        "later_affected68": ["test_reach_recording_unit_offsets", "test_reach_reference_axis_recording",
                            "test_reach_reference_child_origins", "test_reach_reference_sequential",
                            "test_reach_reference_sparse_cartesian", "test_reach_source_cartesian_products"],
    }
    require(set(collection["cohorts"]) == set(groups), "Unexpected cohort declarations")
    selected = {}
    for (name, modules), count in zip(groups.items(), (115, 194, 63, 68)):
        chosen = [test_id for test_id in ids if test_id.split(".")[0] in modules]
        require(len(chosen) == count and collection["cohorts"][name] ==
                {"modules": modules, "count": count, "test_ids": chosen}, f"Wrong cohort: {name}")
        selected[name] = chosen
    require(set(selected["focused115"]) <= set(selected["related194"]), "Focused/related overlap mismatch")
    union = selected["related194"] + selected["original_affected63"] + selected["later_affected68"]
    require(len(union) == len(set(union)) == 325 and collection["combined325"] == union and
            Counter(by_name["combined-modules-001"]["test_ids"]) == Counter(union) and
            all(Counter(by_name[name]["test_ids"]) == Counter(ids) for name in complete_driver_names),
            "Final complete executions differ from the required exact method selections")

    baseline = json_read(root / "review" / "baseline-preflight-recovery.json")
    require(Path(baseline["preserved_path"]).name == "baseline-untracked-preserved-001.bin",
            "Unexpected baseline recovery descriptor")
    baseline_member = {"path": "recovery/baseline-untracked-preserved-001.bin",
                       "bytes": baseline["bytes"], "sha256": baseline["sha256"]}
    identity(root, baseline_member)
    local_extra = json_read(root / "review" / "local-core-001-extra-file.json")
    require(local_extra["path"] == "recovery/local-core-001-extra-temporary.bin" and
            local_extra["failed_setup_only"] is True and local_extra["product_tests_executed"] is False,
            "Unexpected local setup recovery descriptor")
    identity(root, local_extra)
    refused = by_name["local-core-001"]
    require(refused["kind"] == "preflight_not_executed", "First local attempt was not a setup refusal")
    extra_path = refused["workspace_diff"]["extra"][0]
    copied = inventory(json_read(root / "local-core-001" / "workspace-after-setup-failure.json"))
    require(copied[extra_path][0] == local_extra["bytes"] and
            unprefix(copied[extra_path][1]) == unprefix(local_extra["sha256"]) and
            local_extra["original_path"].endswith("/" + extra_path), "Preserved temporary bytes mismatch")
    focused_passed = all(not by_name[name]["failed"] for name in declared["final-focused-plan"])
    core = by_name["local-core-002"]
    original_construction = core["construction"]
    require(core["driver_passed"] is False and core["unittest_passed"] is True and core["failed_steps"] == ["construction"] and
            original_construction["tests"] == 128 and original_construction["passed"] == 127 and
            original_construction["failures"] == 1 and original_construction["errors"] == 0 and
            [row["test_id"] for row in original_construction["failed_test_records"]] == [protocol["failed_method"]],
            "Original default-driver failure was relabeled or changed")
    original_trace = "\n".join(original_construction["failed_test_records"][0]["failures"])
    require(all(str(value) in original_trace for value in protocol["diagnostic"].values()),
            "Predeclared resource refusal differs from the retained raw traceback")
    latest = by_name[complete_driver_names[-1]]
    return {"source_commit": commit, "source_tree": tree, "declared_plans": list(declared),
            "command_count": attempt_count, "focused_attempt_count": 32, "local_attempt_count": 1 + len(complete_driver_names),
            "local_step_attempt_count": 1, "final_run_names": final_names,
            "combined_method_count": 325, "full_method_count": 3064,
            "final_focused_passed": focused_passed, "full_unittest_passed": core["unittest_passed"],
            "fixture_regression_passed": focused_passed and core["unittest_passed"],
            "original_complete_driver_passed": core["driver_passed"],
            "original_complete_driver_failed_steps": core["failed_steps"],
            "latest_default_driver_name": latest["name"], "latest_default_driver_passed": latest["driver_passed"],
            "default_driver_runs": [{"name": name, "driver_passed": by_name[name]["driver_passed"],
                                     "unittest_passed": by_name[name]["unittest_passed"],
                                     "failed_steps": by_name[name]["failed_steps"]} for name in complete_driver_names],
            "diagnostic_retries": [{"name": name, "passed": not by_name[name]["failed"]}
                                   for name in declared["construction-retry-plan"]],
            "followup_protocol_sha256": protocol_sha,
            "conditional_full_run_pending": both_retries_passed and "full-local-final-plan" not in declared,
            "retry_does_not_relabel_default_driver": True,
            "historical_failures_retained": [item["name"] for item in results if item["failed"]],
            "recovery_members": [baseline_member, {key: local_extra[key] for key in ("path", "bytes", "sha256")}],
            "release_acceptance": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-failures", action="store_true")
    args = parser.parse_args()
    root = args.evidence.resolve()
    require(not args.output.exists(), "Audit output must be a new file")
    selected = [("focused", p.parent) for p in sorted((root / "execution").glob("*/report.json"))]
    selected += [("local_core", p.parent) for p in sorted(root.glob("local-core-*/summary.json"))]
    selected += [("local_step", p.parent) for p in sorted((root / "local-step").glob("*/report.json"))]
    results, problems = [], []
    for kind, directory in selected:
        try:
            results.append({"focused": focused, "local_core": local_core, "local_step": local_step}[kind](root, directory))
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            problems.append({"kind": kind, "directory": str(directory), "error": str(error)})
    if not selected:
        problems.append({"error": "No executions discovered"})
    checkpoint = None
    try:
        checkpoint = final_checkpoint(root, results)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        problems.append({"kind": "final_checkpoint", "error": str(error)})
    failed = [item["name"] for item in results if item["failed"]]
    not_executed = [item["name"] for item in results if item["kind"] == "preflight_not_executed"]
    product_failed = [item["name"] for item in results if item["failed"] and
                      item["kind"] != "preflight_not_executed"]
    evidence_valid = not problems
    accepted = evidence_valid and (args.allow_failures or not failed)
    report = {"schema_version": "ontokin.regression-evidence-audit/0.4",
              "created_at": datetime.now(timezone.utc).isoformat(),
              "auditor_sha256": digest(read(Path(__file__))), "evidence_root": str(root),
              "allow_failures": args.allow_failures, "status": "passed" if accepted else "failed",
              "evidence_integrity_passed": evidence_valid, "product_test_pass_claimed": evidence_valid and not failed,
              "release_acceptance": False, "selected_run_count": len(selected),
              "failed_attempts": failed, "failed_product_runs": product_failed,
              "preflight_not_executed": not_executed, "problems": problems, "runs": results,
              "final_checkpoint": checkpoint,
              "scope": "All discovered focused executions and complete default local-core runs; no product execution by auditor."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "evidence_integrity_passed": evidence_valid,
                      "runs": len(results), "failed_product_runs": product_failed,
                      "preflight_not_executed": not_executed, "problems": problems}))
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
