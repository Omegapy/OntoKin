#!/usr/bin/env python3
"""Read supplied C084 source, inspection, control and artifact evidence independently."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.keyed_merge_reference import (DELIVERED_CASES, FREEZE_COMMIT, FREEZE_SHA256,
    ReferenceError, case_payload, check_artifact, check_inspection, codes, delivered_by_revision, load_fixtures,
    loads, ordinary_path, require, sha, diagnostic_anchor, source_units, check_all_locations,
    canonical_probe_type, same_location, PROFILE)
from tools.keyed_merge_adversaries import build_mutations

def requires_execution_trace(case):
    expected = case.get("expected") or {}
    return case["expected_outcome"] == "valid" and all(field in expected for field in (
        "left_input_evaluations", "right_input_evaluations", "collision_key_order", "materialization_key_order"))


def read_json(directory, relative):
    return loads(ordinary_path(directory, relative).read_bytes())


def check_execution_trace(trace, case, units, budget):
    """Read observed input/admission calls and genuine stage/key checkpoints."""
    require(trace.get("schema_version") == "ontokin.c084-merge-execution-observation/0.1" and
            trace.get("case") == case["name"] and trace.get("program_revision") == case["program_revision"] and
            trace.get("profile") == PROFILE and trace.get("requested_level") == "represented" and
            trace.get("public_api") == "KeyedMergeProgramRuntime.validate_revision", "Execution trace is not bound to the exact public source case")
    invocations = trace.get("invocations", [])
    require(len(invocations) == 1, "Frozen trace fixture must have one actual dynamic merge invocation")
    current, expected = invocations[0], case["expected"]
    origin = case["source_merge_records"][0]
    for part in ("expression", "left", "right"):
        same_location(current[part], origin[part], units)
    require(current["self_path"] == case["probe"]["object_path"] and
            current["left_input_evaluations"] == expected["left_input_evaluations"] == 1 and
            current["right_input_evaluations"] == expected["right_input_evaluations"] == 1 and
            current["dynamic_input_order"] == expected["dynamic_input_order"] == ["left", "right"],
            "Actual operand evaluation was skipped/repeated or reversed")
    require(current["left_input_admissions"] == current["right_input_admissions"] == 1 and
            current["admission_order"] == ["left", "right"], "Actual operand admission was skipped/repeated or reversed")
    require(current["input_events"] == ["evaluate_left", "admit_left", "evaluate_right", "admit_right"],
            "Actual left admission did not complete before right evaluation")
    right, output = expected["collision_key_order"], expected["materialization_key_order"]
    left = sorted(set(output) - set(right))
    require(current["left_keys"] == left and current["right_keys"] == right and current["output_keys"] == output == case["probe"]["keys"],
            "Actual merge inputs/output differ from independent disjoint-union membership")
    require(current["collision_keys"] == right and current["materialization_keys"] == output,
            "Actual collision traversal or detached materialization is not canonical ASCII order")
    for name in ("left_type", "right_type", "output_type"):
        require(canonical_probe_type(current[name]) == canonical_probe_type(case["probe"]["type"]),
                "Observed merge widened/changed exact input/output type")
    for name in ("left_map_visits", "right_map_visits"):
        if name in expected:
            require(current.get(name) == expected[name], "Operand map visit order/count differs")
    before, after = current["operations_before"], current["operations_after"]
    values_before, values_after = current["value_entries_before"], current["value_entries_after"]
    require(type(before) is type(after) is int and 0 <= before < after and
            type(values_before) is type(values_after) is int and 0 <= values_before < values_after,
            "Actual merge lacks one monotone current work/value ledger")
    checkpoints = current["checkpoints"]
    expected_visits = [("keyed_merge_collision", key) for key in right] + [("keyed_merge_iteration", key) for key in output]
    require([(item["stage"], item["key"]) for item in checkpoints] == expected_visits,
            "Actual checkpoints were skipped, invented, reordered or not tied to canonical keys")
    previous_operations, previous_values = before, values_before
    for item in checkpoints:
        require(type(item["consumed_operations"]) is type(item["value_entries"]) is int and
                previous_operations < item["consumed_operations"] <= after and
                previous_values <= item["value_entries"] <= values_after,
                "Actual collision/materialization checkpoint escaped or reset the shared ledger")
        previous_operations, previous_values = item["consumed_operations"], item["value_entries"]
    if origin["element_type"] == "PolygonRing":
        materialized = [item for item in checkpoints if item["stage"] == "keyed_merge_iteration"]
        require(len(materialized) == 2 and materialized[1]["value_entries"] - materialized[0]["value_entries"] > 4 and
                values_after - materialized[-1]["value_entries"] > 4,
                "Compound detached copy/materialization lost its inherited logical-copy charges")
    observed = trace["execution_budget"]
    require(observed["consumed_operations"] == budget["consumed_operations"] >= after and
            observed["host_ceilings"] == case["host_policy"] and observed["effective"] == budget["effective"],
            "Observed expression ledger is not the retained complete request ledger")
    return {"left_input_evaluations": 1, "right_input_evaluations": 1, "input_admissions": 2,
            "collision_lookups": len(right), "materialized_entries": len(output),
            "actual_checkpoint_count": len(checkpoints), "logical_value_entries": values_after - values_before,
            "observed_operations": after - before}

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
    require(receipt.get("outcome") == case["expected_protocol_outcome"],
            "Actual protocol outcome differs from the separately frozen exact category")
    source_locations = check_all_locations(receipt, source_units(case_payload(fixtures, case)))
    require(record.get("diagnostic_codes", observed) == observed, "Producer diagnostic index differs from raw receipt")
    if case["expected_outcome"] == "invalid":
        require(not record["delivered"] and "glb" not in record and receipt.get("achieved_level") != "delivered", "Invalid source published an artifact")
        require(case["expected_code"] in observed, "Refused source lost its exact frozen diagnostic")
        if case["expected_code"] != "OKL-E-RESOURCE":
            require("OKL-E-RESOURCE" not in observed, "Resource exhaustion substituted for the frozen semantic refusal")
        anchor = diagnostic_anchor(receipt, case, source_units(case_payload(fixtures, case)))
        return {"case": case["name"], "status": "passed", "outcome": "refused", "expected_code": case["expected_code"],
                "achieved_level": receipt.get("achieved_level"), "budget_stage": budget.get("stage"),
                "source_locations": source_locations, "checked_primary_anchor": anchor}
    require(receipt.get("achieved_level") in ("represented", "delivered", "executed") and
            not any(c.startswith(("OKL-E-", "OKE-E-")) for c in observed), "Valid source did not achieve its required semantics")
    require(control_record is not None and control_record["program_revision"] == case["explicit_c083_control"]["program_revision"], "Missing separately authored .16 control")
    control_envelope = read_json(directory, control_record["receipt"])
    control_receipt = control_envelope.get("result", control_envelope)
    require(control_receipt.get("outcome") == "valid" and control_receipt["program_revision"] == control_record["program_revision"] and not any(c.startswith(("OKL-E-", "OKE-E-")) for c in codes(control_receipt)), "Explicit control did not validate")
    inspection = check_inspection(read_json(directory, record["inspection"]), read_json(directory, control_record["inspection"]), case, fixtures)
    result = {"case": case["name"], "status": "passed", "outcome": "represented", "inspection": inspection,
              "actual_operations": budget.get("consumed_operations"), "actual_elapsed_ms": budget.get("elapsed_ms")}
    if requires_execution_trace(case):
        result["execution_trace"] = check_execution_trace(read_json(directory, record["execution_trace"]), case,
            source_units(case_payload(fixtures, case)), budget)
    if case["expected_stage"] == "represented":
        require(not record["delivered"] and "glb" not in record, "Represented fixture was silently converted into an export gate")
        return result
    require(record["delivered"] and receipt.get("achieved_level") == "delivered", "Delivered fixture did not publish a successful named artifact")
    raw = ordinary_path(directory, record["glb"]).read_bytes()
    require(sha(raw) == record["sha256"] and len(raw) == record["bytes"], "Actual source GLB differs from retained identity")
    control = ordinary_path(directory, control_record["glb"]).read_bytes()
    require(sha(control) == control_record["sha256"] and len(control) == control_record["bytes"], "Explicit .16 control GLB differs from retained identity")
    result.update(outcome="delivered", artifact=check_artifact(raw, case, fixtures, control))
    return result


def verify(directory, fixtures):
    summary = read_json(directory, "summary.json")
    report = {"schema_version": "ontokin.c084-independent-readback/0.1", "status": "running",
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
    section("source_inventory", lambda: require(len(summary["cases"]) == len(records) == len(fixtures["cases"]) and set(records) == set(fixtures["cases"]), "Actual source corpus is incomplete"))
    section("explicit_control_inventory", lambda: require(len(summary["controls"]) == len(controls) == sum(case["expected_outcome"] == "valid" for case in fixtures["cases"].values()) and
        set(controls) == {c["name"] for c in fixtures["cases"].values() if c["expected_outcome"] == "valid"}, "Actual explicit-control corpus is incomplete"))
    for case in fixtures["expected"]["cases"]:
        result = section("source/"+case["name"], lambda case=case: verify_case(case, records[case["name"]], controls.get(case["name"]), fixtures, directory))
        if result is not None:
            report["cases"].append(result)
    by_revision = delivered_by_revision(fixtures)
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
        contract = loads(ordinary_path(fixtures["root"], "supplied-byte-adversaries.json").read_bytes())
        names = set(contract["source_cases"])
        pairs = {(name, rule["id"]) for name in names for rule in contract["requirements"]}
        require(len(actual) == len(pairs) == 57 and {(i["case"], i["id"]) for i in actual} == pairs,
                "Frozen nineteen supplied-byte adversaries for three source baselines are incomplete")
        bases = {name: ordinary_path(directory, records[name]["glb"]).read_bytes() for name in names}
        expected = {(name, item["id"]): item for name in names for item in build_mutations(bases[name], fixtures["cases"][name])}
        require(all(item["mutation"] == next(rule["mutation"] for rule in contract["requirements"] if rule["id"] == item["id"])
                    for item in expected.values()), "Mutation labels differ from frozen requirements")
        positive = summary.get("supplied_glb_positive_controls", [])
        require(len(positive) == 3 and {p["case"] for p in positive} == names and
                all(p.get("status") == "observed_as_expected" and p["sha256"] == sha(bases[p["case"]]) and p.get("validation") for p in positive),
                "Actual supplied-byte positive controls are absent or bound to other bytes")
        retained = read_json(directory, "hostile-glbs/production-observations.json")
        require(retained["positive_controls"] == positive and retained["hostile_controls"] == actual,
                "Supplied-byte raw observation inventories disagree")
        for item in actual:
            name, case = item["case"], fixtures["cases"][item["case"]]
            wanted = expected[(name, item["id"])]
            raw = ordinary_path(directory, item["path"]).read_bytes()
            require(raw == wanted["data"] and len(raw) == item["bytes"] and sha(raw) == item["sha256"] and item["base_sha256"] == wanted["base_sha256"],
                    "Retained mutation does not reproduce from the original actual supplied bytes")
            require(item["mutation"] == wanted["mutation"] and item["status"] == "observed_as_expected", "Actual supplied-byte mutation was not refused as specified")
            diagnostic = item.get("actual_export_code")
            require(type(diagnostic) is str and diagnostic.startswith(("OKE-E-", "OKL-E-")) and "RESOURCE" not in diagnostic,
                    "Actual validator refusal is absent or substituted resource exhaustion")
            require(diagnostic == item.get("exception", {}).get("details", {}).get("export_code") and
                    item.get("diagnostic_codes") == codes(item.get("exception")) and item["diagnostic_codes"] and
                    not any("RESOURCE" in code for code in item["diagnostic_codes"]), "Hostile refusal does not match its retained raw product exception")
            try:
                check_artifact(raw, case, fixtures, ordinary_path(directory, controls[name]["glb"]).read_bytes())
            except (ReferenceError, KeyError, IndexError, ValueError) as error:
                report["hostile_glbs"].append({"id": item["id"], "case": name, "mutation": item["mutation"], "sha256": sha(raw),
                    "actual_product_code": diagnostic, "independent_exception": type(error).__name__, "independent_reason": str(error), "status": "passed"})
            else:
                raise ReferenceError("Independent reader accepted supplied-byte mutation: "+item["mutation"])
    section("actual_supplied_byte_adversaries", hostiles)
    def workflows():
        rows = summary.get("workflows", [])
        require(len(rows) == 10 and {r["id"] for r in rows} == {r["id"] for r in fixtures["workflows"]["workflows"]} and
                all(r["status"] == "observed_as_expected" for r in rows), "Actual Agent workflow inventory failed or incomplete")
        return {"workflow_count": len(rows), "raw_independent_audit_required": "tools/verify_keyed_merge_agent_evidence.py"}
    report["workflows"] = section("workflow_inventory", workflows)
    section("producer_terminal_status", lambda: require(summary.get("status") == "produced_as_expected" and not summary.get("failures"), "Producer did not complete all frozen requested work"))
    report["status"] = "failed" if report["failures"] else "passed"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["coverage"] = {"source_cases": len(report["cases"]), "represented_sources": sum(r["outcome"] == "represented" for r in report["cases"]),
        "delivered_sources": sum(r["outcome"] == "delivered" for r in report["cases"]),
        "unique_delivered_bundles": len(by_revision),
        "agent_artifacts": len(report["agent_artifacts"]),
        "unique_agent_glbs": len({r["sha256"] for r in report["agent_artifacts"]}),
        "hostile_glbs": len(report["hostile_glbs"])}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-merge")
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
