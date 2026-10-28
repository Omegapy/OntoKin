"""Retain an actual isolated reach cohort run, including failed attempts."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time


COHORT = (
    "test_reach_numeric.py", "test_reach_kinematics.py", "test_reach_pose.py",
    "test_reach_export_arithmetic.py", "test_reach_source.py", "test_reach_evaluator.py",
    "test_reach_agent_protocol.py", "test_reach_agent.py", "test_reach_agent_cli.py",
    "test_reach_agent_protocol_cases.py", "test_reach_agent_transactions.py",
    "test_reach_agent_verification.py", "test_reach_phase.py",
    "test_reach_reference.py", "test_reach_conformance.py", "test_reach_destination_resources.py",
    "test_reach_accounting.py", "test_reach_recording_sampler.py", "test_reach_observation.py",
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pattern", action="append", dest="patterns")
    args = parser.parse_args()
    root = args.repository.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    def git(*parts):
        return subprocess.check_output(["git", "-C", str(root), *parts]).decode().strip()

    def inputs():
        names = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0")
        return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names if name}

    def write(name, value):
        (output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

    before = inputs()
    write("inputs-before.json", before)
    report = {
        "schema_version": "ontokin.reach-focused-execution/0.1",
        "started_at": utc(), "repository": str(root),
        "source_commit": git("rev-parse", "HEAD"), "source_tree": git("rev-parse", "HEAD^{tree}"),
        "git_status_before": git("status", "--porcelain"),
        "environment": {"executable": sys.executable, "python": platform.python_version(),
                        "implementation": platform.python_implementation(), "platform": platform.platform()},
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "stages": [], "input_count": len(before),
        "excluded_pending_cohorts": {"test_reach_agent_delivery.py": "Independent reader and Agent delivery binding incomplete."},
        "scope": "Selected actual runtime preparation; not full source/native/browser/compatibility/release acceptance.",
    }
    write("report.json", report)
    for pattern in args.patterns or COHORT:
        if pattern not in COHORT:
            raise ValueError("Only the identified focused cohort is supported")
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"]
        stage = {"pattern": pattern, "command": command, "started_at": utc()}
        print(json.dumps({"event": "stage_started", **stage}), flush=True)
        log_path = output / (pattern + ".log")
        start = time.monotonic()
        with log_path.open("wb") as log:
            try:
                result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=300, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                stage["returncode"] = result.returncode
            except subprocess.TimeoutExpired:
                stage["returncode"] = None
                stage["timeout_seconds"] = 300
                log.write(b"\nFOCUSED RUNNER: stage timed out after 300 seconds.\n")
        raw = log_path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        runs = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", text, flags=re.MULTILINE)
        stage.update({"ended_at": utc(), "elapsed_seconds": time.monotonic() - start,
                      "log": log_path.name, "log_sha256": hashlib.sha256(raw).hexdigest(),
                      "tests_run": int(runs[-1][0]) if runs else None,
                      "status": "passed" if stage["returncode"] == 0 and runs and
                      not re.search(r"\bskipped[= ]", text) else "failed"})
        after = inputs()
        stage["input_changes"] = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        stage["git_identity_unchanged"] = git("rev-parse", "HEAD") == report["source_commit"]
        if stage["input_changes"] or not stage["git_identity_unchanged"]:
            stage["status"] = "invalid_input_drift"
        report["stages"].append(stage)
        write("report.json", report)
        print(json.dumps({"event": "stage_finished", **stage}), flush=True)
        if stage["status"] == "invalid_input_drift":
            break
    after = inputs()
    write("inputs-after.json", after)
    report.update({"ended_at": utc(), "git_status_after": git("status", "--porcelain"),
                   "input_hashes_unchanged": before == after,
                   "tests_run": sum(stage["tests_run"] or 0 for stage in report["stages"]),
                   "status": "passed" if all(stage["status"] == "passed" for stage in report["stages"]) else "failed"})
    write("report.json", report)
    (output / "run_reach21_focused.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({"event": "completed", "status": report["status"], "tests_run": report["tests_run"],
                      "report": str(output / "report.json"), "stable_inputs": before == after}), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
