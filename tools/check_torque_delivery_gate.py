#!/usr/bin/env python3
"""Verify actual required frozen exports without relabeling extra probes."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    table_path = ROOT / "docs/language-design/torque-v0.1/freeze/delivery-cases.json"
    table = json.loads(table_path.read_bytes())
    summary_path = args.execution / "summary.json"
    summary = json.loads(summary_path.read_bytes())
    required = {(case["id"], variant) for case in table["cases"]
                for variant in ["original", "repeat"] + (["helpers"] if case["helpers_true_repeat"] else [])}
    rows = {(row["case"], row["variant"]): row for row in summary["results"]}
    if len(rows) != len(summary["results"]) or not required <= rows.keys():
        raise ValueError("The actual run has duplicate or missing required executions.")
    checks = []
    for key in sorted(required):
        folder = args.execution / key[0] / key[1]
        result_path = folder / "result.json"
        result = json.loads(result_path.read_bytes())
        artifact = result.get("artifact")
        passed = result["status"] == "passed" and artifact is not None
        if artifact:
            raw = (folder / artifact["path"]).read_bytes()
            passed = passed and len(raw) == artifact["bytes"] and hashlib.sha256(raw).hexdigest() == artifact["sha256"]
        if key[1] == "repeat":
            passed = (passed and result.get("complete_glb_bytes_equal") is True
                      and (folder / "scene.glb").read_bytes()
                      == (args.execution / key[0] / "original/scene.glb").read_bytes())
        checks.append({"case": key[0], "variant": key[1], "status": "passed" if passed else "failed",
                       "actual_result_sha256": sha(result_path), "artifact": artifact})
    output = {
        "schema_version": "ontokin.c091-frozen-delivery-gate/1",
        "status": "passed" if all(row["status"] == "passed" for row in checks) else "failed",
        "source_commit": summary["implementation_commit"],
        "frozen_table_sha256": sha(table_path),
        "raw_execution_summary_sha256": sha(summary_path),
        "raw_execution_status_unchanged": summary["status"],
        "raw_execution_count": len(rows), "required_execution_count": len(required),
        "required_checks": checks,
        "additional_executions": [row for key, row in rows.items() if key not in required],
        "scope": "Actual exports, unchanged fixed allocations and exact repeated bytes only. Independent native/dense, hostile-byte, Agent, visual and inherited checks have separate receipts.",
        "extra_probe_policy": "Only original frozen helpers_true_repeat flags select required helpers. Every additional probe and its raw failed or passed result remain unchanged.",
    }
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k: v for k, v in output.items() if k not in {"required_checks", "additional_executions"}}))
    return 0 if output["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
