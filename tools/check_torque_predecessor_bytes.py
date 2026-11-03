#!/usr/bin/env python3
"""Compare unchanged .21 programs to the exact frozen predecessor observations."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.budget_runtime import execute_keyed_membership_export
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.scene import ExportOptions
from ontokin.texture_bundle import load_texture_file_manifest


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    frozen = ROOT / "docs/language-design/torque-v0.1/freeze"
    archive = frozen / "predecessor/new-control-artifacts01.zip"
    inputs = json.loads((frozen / "physics-cases.json").read_bytes())["cases"]
    report = {"schema_version": "ontokin.c091-predecessor-byte-comparison/1",
        "started": datetime.now(timezone.utc).isoformat(), "command": sys.argv,
        "implementation_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "interpreter": sys.version, "baseline_archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "scope": "All31 original .21 common-clock state streams and export outcomes, including27 whole-GLB byte pairs and4 preserved refusals.",
        "original_batch_status": "failed", "original_failures_reclassified": False,
        "host_policy": HostPolicy().ceilings, "cases": []}
    with zipfile.ZipFile(archive) as baseline:
        original = json.loads(baseline.read("RESULT.json"))
        assert original["status"] == "failed" and len(original["cases"]) == 31
        for case in inputs:
            before = next(row for row in original["cases"] if row["id"] == case["id"])
            directory = args.output / case["id"]
            directory.mkdir()
            row = {"id": case["id"], "original_export_status": before["status"], "status": "failed"}
            start = time.monotonic()
            try:
                bundle = load_texture_file_manifest(frozen / case["predecessor_control"]["file_manifest"])
                assert bundle.program_revision == case["predecessor_control"]["identity"]["program_revision"]
                row["state_streams"] = []
                for side in ("before", "after"):
                    ledger = SharedExecutionBudget(policy=HostPolicy())
                    admit_entry_budget(bundle.entry, ledger, profile="keyed-membership-0.1")
                    compiler = compile_construction(bundle, level="constructed", execution_budget=ledger)
                    state = evaluate(compiler.model, times=before["sample_times_seconds"], side=side, work=compiler.reach_work)
                    actual = encoded(state)
                    expected = baseline.read("cases/" + case["id"] + "/" + side + "-states.json")
                    (directory / (side + "-states.json")).write_bytes(actual)
                    (directory / (side + "-budget.json")).write_bytes(encoded(ledger.report(status="passed")))
                    row["state_streams"].append({"side": side, "complete_bytes_equal": actual == expected,
                        "bytes": len(actual), "sha256": hashlib.sha256(actual).hexdigest()})
                    assert actual == expected, "Changed original " + side + " state stream"
                result = execute_keyed_membership_export(bundle, policy=HostPolicy(),
                    options=ExportOptions(fps=4, end=before["sample_times_seconds"][-1], helpers=False))
                (directory / "export-report.json").write_bytes(encoded(result.report))
                row["export_has_bytes"] = result.data is not None
                assert row["export_has_bytes"] == before["export_has_bytes"]
                if result.data is not None:
                    expected = baseline.read("cases/" + case["id"] + "/original.glb")
                    (directory / "original.glb").write_bytes(result.data)
                    row["complete_glb_bytes_equal"] = result.data == expected
                    row["artifact"] = {"bytes": len(result.data), "sha256": hashlib.sha256(result.data).hexdigest()}
                    assert row["complete_glb_bytes_equal"], "Changed original whole GLB"
                else:
                    expected = json.loads(baseline.read("cases/" + case["id"] + "/export-report.json"))
                    assert result.report.get("diagnostics") == expected.get("diagnostics"), "Changed original refusal"
                    assert result.report.get("error") == expected.get("error"), "Changed original resource envelope"
                    row["original_refusal_equal"] = True
                row["status"] = "passed"
            except BaseException as error:
                row["error"] = f"{type(error).__name__}: {error}"
                row["traceback"] = traceback.format_exc()
            row["elapsed_seconds"] = time.monotonic() - start
            report["cases"].append(row)
            report["status"] = "passed" if all(item["status"] == "passed" for item in report["cases"]) else "failed"
            (args.output / "summary.json").write_bytes(encoded(report))
            print(json.dumps({key: row[key] for key in ("id", "status", "elapsed_seconds")}), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
