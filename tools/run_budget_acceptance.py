#!/usr/bin/env python3
"""Execute both frozen C073 attempts and preserve each exact result."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.budget_runtime import execute_budgeted_export
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.execution_budget import HostPolicy
from ontokin.scene import ExportOptions


def digest(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixture = ROOT / "examples/execution-budgets"
    freeze = json.loads((fixture / "acceptance-freeze.json").read_text())
    for name, expected_hash in freeze["files"].items():
        if digest(fixture / name) != expected_hash:
            raise ValueError("Frozen acceptance input changed: " + name)
    raw = (fixture / "larger-workload.ok").read_bytes()
    expected = json.loads((fixture / "larger-workload.expected.json").read_text())
    source = ProgramBundle(SourceUnit("entry", "larger-workload.ok", raw))
    options = ExportOptions(**expected["options"])
    inputs = {"case_id": freeze["case_id"], "frozen_inputs": freeze["files"],
              "freeze": digest(fixture / "acceptance-freeze.json"),
              "program_revision": source.program_revision,
              "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "git_tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True).strip(),
              "tracked_status": subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True),
              "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
              "started_utc": datetime.now(timezone.utc).isoformat()}
    save(output / "inputs.json", inputs)
    results = []
    for attempt in freeze["attempts"]:
        result = execute_budgeted_export(source, policy=HostPolicy(**attempt["policy"]),
                                         caller_caps=attempt["caller_caps"], options=options)
        save(output / (attempt["name"] + ".receipt.json"), result.report)
        if result.data is not None:
            (output / (attempt["name"] + ".glb")).write_bytes(result.data)
        reason = (result.report.get("execution_budget") or {}).get("budget_reason")
        correct = ((result.data is None and reason == "operation_budget_exhausted")
                   if attempt["name"] == "default-control" else
                   (result.data is not None and result.report["validation"]["status"] == "passed"))
        results.append({"attempt": attempt["name"], "expected": attempt["expected"],
                        "passed": correct, "outcome": result.report["outcome"],
                        "budget_reason": reason, "execution_budget": result.report.get("execution_budget"),
                        "artifact": result.report.get("artifact")})
        # Retain both attempts even when the first contradicts its expectation.
        save(output / "summary.json", {"status": "running", "attempts": results})
    summary = {"schema_version": "ontokin.execution-budget-acceptance/0.1",
               "case_id": freeze["case_id"], "status": "passed" if all(r["passed"] for r in results) else "failed",
               "attempts": results, "original28_gate_changed": False,
               "finished_utc": datetime.now(timezone.utc).isoformat()}
    save(output / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "output": str(output),
                      "attempts": [{"name": r["attempt"], "passed": r["passed"],
                        "operations": r["execution_budget"]["consumed_operations"],
                        "reason": r["budget_reason"]} for r in results]}))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
