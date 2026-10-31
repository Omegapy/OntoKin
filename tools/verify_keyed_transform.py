#!/usr/bin/env python3
"""Read supplied C081 source, inspection, control and artifact evidence independently."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.keyed_transform_reference import (DELIVERED_CASES, FREEZE_COMMIT, FREEZE_SHA256,
    ReferenceError, case_payload, check_artifact, check_inspection, codes, load_fixtures,
    loads, ordinary_path, require, sha)
from tools.keyed_transform_adversaries import build_mutations


def read_json(directory, relative):
    return loads(ordinary_path(directory, relative).read_bytes())


def verify_case(case, record, control_record, fixtures, directory):
    require(record["name"] == case["name"] and record["id"] == case["id"], "Actual source case identity differs")
    require(record["file_manifest"] == case["file_manifest"], "Actual source file manifest differs")
    envelope = read_json(directory, record["receipt"])
    receipt = envelope.get("result", envelope)
    require(record["program_revision"] == case["program_revision"] == receipt["program_revision"] == envelope["program_revision"], "Actual source immutable revision differs")
    require(record.get("host_policy", case["host_policy"]) == case["host_policy"], "Frozen source caller authority changed")
    if "source_revision" in receipt:
        entry = next(u for u in case["canonical_manifest"]["units"] if u["source_id"] == "entry")
        require(receipt["source_revision"] == entry["source_revision"], "Actual entry UTF-8 source hash differs")
    budget = envelope.get("execution_budget") or receipt.get("execution_budget") or {}
    observed = codes(receipt)
    require(record.get("diagnostic_codes", observed) == observed, "Producer diagnostic index differs from raw receipt")
    if case["expected_outcome"] == "invalid":
        require(not record["delivered"] and "glb" not in record and receipt.get("achieved_level") != "delivered", "Invalid source published an artifact")
        require(case["expected_code"] in observed, "Refused source lost its exact frozen diagnostic")
        if case["expected_code"] != "OKL-E-RESOURCE":
            require("OKL-E-RESOURCE" not in observed, "Resource exhaustion substituted for the frozen semantic refusal")
        return {"case": case["name"], "status": "passed", "outcome": "refused", "expected_code": case["expected_code"],
                "achieved_level": receipt.get("achieved_level"), "budget_stage": budget.get("stage")}
    require(receipt.get("achieved_level") in ("represented", "delivered", "executed") and
            not any(c.startswith(("OKL-E-", "OKE-E-")) for c in observed), "Valid source did not achieve its required semantics")
    require(control_record is not None and control_record["program_revision"] == case["explicit_c080_control"]["program_revision"], "Missing separately authored .13 control")
    control_envelope = read_json(directory, control_record["receipt"])
    control_receipt = control_envelope.get("result", control_envelope)
    require(control_receipt["program_revision"] == control_record["program_revision"] and not any(c.startswith(("OKL-E-", "OKE-E-")) for c in codes(control_receipt)), "Explicit control did not validate")
    inspection = check_inspection(read_json(directory, record["inspection"]), read_json(directory, control_record["inspection"]), case, fixtures)
    result = {"case": case["name"], "status": "passed", "outcome": "represented", "inspection": inspection,
              "actual_operations": budget.get("consumed_operations"), "actual_elapsed_ms": budget.get("elapsed_ms")}
    if case["expected_stage"] == "represented":
        require(not record["delivered"] and "glb" not in record, "Represented fixture was silently converted into an export gate")
        return result
    require(record["delivered"] and receipt.get("achieved_level") == "delivered", "Delivered fixture did not publish a successful named artifact")
    raw = ordinary_path(directory, record["glb"]).read_bytes()
    require(sha(raw) == record["sha256"] and len(raw) == record["bytes"], "Actual source GLB differs from retained identity")
    control = ordinary_path(directory, control_record["glb"]).read_bytes()
    require(sha(control) == control_record["sha256"] and len(control) == control_record["bytes"], "Explicit .13 control GLB differs from retained identity")
    result.update(outcome="delivered", artifact=check_artifact(raw, case, fixtures, control))
    return result


def verify(directory, fixtures):
    summary = read_json(directory, "summary.json")
    report = {"schema_version": "ontokin.c081-independent-readback/0.1", "status": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(), "frozen_input_commit": FREEZE_COMMIT,
        "frozen_manifest_sha256": FREEZE_SHA256, "actual_git": summary["git"], "producer_summary_sha256": sha((directory / "summary.json").read_bytes()),
        "cases": [], "agent_artifacts": [], "hostile_glbs": [], "failures": [], "release_acceptance": False}
    def section(label, action):
        try:
            return action()
        except Exception as error:
            report["failures"].append({"scope": label, "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc()})
            return None
    section("published_input_identity", lambda: require(summary["frozen_input_commit"] == FREEZE_COMMIT and
        summary["frozen_manifest_sha256"] == FREEZE_SHA256, "Producer used another acceptance freeze"))
    records = {r["name"]: r for r in summary["cases"]}
    controls = {r["name"]: r for r in summary["controls"]}
    section("source_inventory", lambda: require(len(summary["cases"]) == len(records) == 97 and set(records) == set(fixtures["cases"]), "Actual source corpus is incomplete"))
    section("explicit_control_inventory", lambda: require(len(summary["controls"]) == len(controls) == 50 and
        set(controls) == {c["name"] for c in fixtures["cases"].values() if c["expected_outcome"] == "valid"}, "Actual explicit-control corpus is incomplete"))
    for case in fixtures["expected"]["cases"]:
        result = section("source/"+case["name"], lambda case=case: verify_case(case, records[case["name"]], controls.get(case["name"]), fixtures, directory))
        if result is not None:
            report["cases"].append(result)
    by_revision = {c["program_revision"]: c for c in fixtures["cases"].values() if c["name"] in DELIVERED_CASES}
    for item in summary.get("agent_artifacts", []):
        def artifact(item=item):
            case = by_revision[item["program_revision"]]
            raw = ordinary_path(directory, item["glb"]).read_bytes()
            require(len(raw) == item["bytes"] and sha(raw) == item["sha256"], "Actual retrieved Agent GLB bytes differ")
            result = check_artifact(raw, case, fixtures, ordinary_path(directory, controls[case["name"]]["glb"]).read_bytes())
            result.update(project_id=item["project_id"], artifact_id=item["artifact_id"], export_request_id=item["export_request_id"], source="bounded actual Agent artifact retrieval")
            return result
        result = section("agent_artifact/"+item["glb"], artifact)
        if result is not None:
            report["agent_artifacts"].append(result)
    def hostiles():
        actual = summary.get("hostile_glbs", [])
        require(len(actual) == 12 and len({i["id"] for i in actual}) == 12, "Frozen twelve supplied-byte adversaries are incomplete")
        names = {i["case"] for i in actual}
        require(len(names) == 1, "All repeatable supplied-byte adversaries must retain their one actual baseline")
        name = next(iter(names)); case = fixtures["cases"][name]
        base = ordinary_path(directory, records[name]["glb"]).read_bytes()
        expected = {i["id"]: i for i in build_mutations(base, case)}
        positive = summary.get("supplied_glb_positive_controls", [])
        require(positive and all(p.get("status") == "observed_as_expected" for p in positive), "No successful actual supplied-byte validator control")
        for item in actual:
            wanted = expected[item["id"]]
            raw = ordinary_path(directory, item["path"]).read_bytes()
            require(raw == wanted["data"] and len(raw) == item["bytes"] and sha(raw) == item["sha256"] and item["base_sha256"] == wanted["base_sha256"],
                    "Retained mutation does not reproduce from the original actual supplied bytes")
            require(item["mutation"] == wanted["mutation"] and item["status"] == "observed_as_expected", "Actual supplied-byte mutation was not refused as specified")
            diagnostic = item.get("actual_export_code")
            require(type(diagnostic) is str and diagnostic.startswith(("OKE-E-", "OKL-E-")) and "RESOURCE" not in diagnostic,
                    "Actual validator refusal is absent or substituted resource exhaustion")
            try:
                check_artifact(raw, case, fixtures, ordinary_path(directory, controls[name]["glb"]).read_bytes())
            except (ReferenceError, KeyError, IndexError, ValueError) as error:
                report["hostile_glbs"].append({"id": item["id"], "mutation": item["mutation"], "sha256": sha(raw),
                    "actual_product_code": diagnostic, "independent_exception": type(error).__name__, "independent_reason": str(error), "status": "passed"})
            else:
                raise ReferenceError("Independent reader accepted supplied-byte mutation: "+item["mutation"])
    section("actual_supplied_byte_adversaries", hostiles)
    def workflows():
        rows = summary.get("workflows", [])
        require(len(rows) == 10 and {r["id"] for r in rows} == {r["id"] for r in fixtures["workflows"]["workflows"]} and
                all(r["status"] == "observed_as_expected" for r in rows), "Actual Agent workflow inventory failed or incomplete")
        return {"workflow_count": len(rows), "raw_independent_audit_required": "tools/verify_keyed_transform_agent_evidence.py"}
    report["workflows"] = section("workflow_inventory", workflows)
    section("producer_terminal_status", lambda: require(summary.get("status") == "produced_as_expected" and not summary.get("failures"), "Producer did not complete all frozen requested work"))
    report["status"] = "failed" if report["failures"] else "passed"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["coverage"] = {"source_cases": len(report["cases"]), "represented_sources": sum(r["outcome"] == "represented" for r in report["cases"]),
        "delivered_sources": sum(r["outcome"] == "delivered" for r in report["cases"]), "agent_artifacts": len(report["agent_artifacts"]), "hostile_glbs": len(report["hostile_glbs"])}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-transform")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new report path")
    report = verify(args.results.resolve(), load_fixtures(args.fixtures))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["coverage"], "failures": len(report["failures"])}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
