#!/usr/bin/env python3
"""Execute the published A01--A10 expectations through the durable service.

This script does not change the original design manifest or infer success from
its expected outcomes. Each reported case runs a concrete independent protocol
test against fresh persistent storage and retains the actual request/results.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from ontokin import __version__
from ontokin.fixtures import DEFAULT_FIXTURES, load_manifest
from test_agent import AgentContractTests, CASE_TESTS


def content_identity(paths):
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix()):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return "sha256:" + digest.hexdigest()


def run_cases(selected=None):
    manifest = load_manifest()
    cases = {case["id"]: case for case in manifest["agent_contract_checks"]}
    if set(cases) != set(CASE_TESTS):
        raise ValueError("The executed scenario map does not match the published agent cases.")
    selected = sorted(cases if selected is None else set(selected))
    records = []
    for case_id in selected:
        test = AgentContractTests(CASE_TESTS[case_id])
        result = unittest.TestResult()
        started = time.monotonic()
        test.run(result)
        failures = [message for _, message in result.failures + result.errors]
        if result.skipped:
            failures.extend("Case was skipped: " + reason for _, reason in result.skipped)
        if result.testsRun != 1:
            failures.append(f"Expected one executed scenario, got {result.testsRun}.")
        records.append({
            "id": case_id, "operation": cases[case_id]["operation"],
            "condition": cases[case_id]["condition"], "expected": cases[case_id]["expected"],
            "rules": cases[case_id]["rules"], "requirements": cases[case_id]["requirements"],
            "test_method": CASE_TESTS[case_id], "passed": not failures,
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "failures": failures, "operations": getattr(test, "evidence", []),
        })
    passed = sum(case["passed"] for case in records)
    source_digest = hashlib.sha256()
    for path in sorted((ROOT / "ontokin").glob("*.py")):
        source_digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    evidence_files = [ROOT / "tests/test_agent.py", Path(__file__).resolve(),
                      ROOT / "docs/language-design/agent-v0.1/request.schema.json",
                      ROOT / "docs/language-design/agent-v0.1/response.schema.json",
                      DEFAULT_FIXTURES / "validation-cases.json", DEFAULT_FIXTURES / "diagnostic.schema.json"]
    evidence_files.extend(DEFAULT_FIXTURES.glob("*.ok"))
    return {
        "schema_version": "ontokin.agent-conformance/0.1",
        "executed": True, "agent_contract": "ontokin.agent/0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "implementation": {"name": "ontokin-reference", "version": __version__,
                           "source_code_sha256": "sha256:" + source_digest.hexdigest()},
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "fixture_identity": content_identity(evidence_files),
        "manifest_sha256": "sha256:" + hashlib.sha256((DEFAULT_FIXTURES / "validation-cases.json").read_bytes()).hexdigest(),
        "scope": "Actual A01-A10 agent-operation scenarios using independent expected outcomes. Additional service, CLI, and export tests are recorded separately. This does not certify unrestricted language or product conformance.",
        "full_product_conformance_certified": False,
        "summary": {"total": len(records), "passed": passed, "failed": len(records) - passed},
        "cases": records,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write complete measured evidence to this JSON file")
    parser.add_argument("--case", action="append", choices=sorted(CASE_TESTS), help="Run only the selected case; repeatable")
    arguments = parser.parse_args(argv)
    report = run_cases(arguments.case)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(arguments.output), "summary": report["summary"]}, indent=2))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
