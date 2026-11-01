#!/usr/bin/env python3
"""Independently read supplied C086 source, control, trace and delivery evidence."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.keyed_rekey_reference import (
    AMENDMENTS, FREEZE_COMMIT, FREEZE_SHA256, PROFILE, TARGET, ReferenceError, require, sha,
    canonical, loads, ordinary_path, load_fixtures, input_lineage, case_payload,
    source_units, codes, walk, check_all_locations, diagnostic_anchor,
    check_inspection, check_artifact, delivered_by_revision, check_rekeys,
    canonical_probe_type, exact_location, _location_identity,
)

from tools.keyed_rekey_source_reference import result_rekey_expression


def read_json(directory, name):
    return loads(ordinary_path(directory, name).read_bytes())


def require_lineage(value, fixtures):
    require(all(value.get(key) == expected for key, expected in input_lineage(fixtures).items()),
            "Observed evidence lacks exact frozen/adopted input lineage")


def check_execution_trace(trace, case, units, budget, fixtures):
    require_lineage(trace, fixtures)
    require(trace.get("schema_version") == "ontokin.c086-rekey-execution-observation/0.1" and
            trace.get("case") == case["name"] and trace.get("program_revision") == case["program_revision"] and
            trace.get("profile") == PROFILE and trace.get("requested_level") == "represented" and
            trace.get("public_api") == "KeyedRekeyProgramRuntime.validate_revision",
            "Trace does not name the exact actual public source invocation")
    invocations = trace.get("invocations")
    require(isinstance(invocations, list), "Trace omitted its actual dynamic invocations")
    origins = {_location_identity(record["expression"]): record for record in case["source_rekey_records"]}
    binders = {_location_identity(record["expression"]): record for record in case["source_rekey_binders"]}
    expected = case.get("expected") or {}
    checkpoints_total, bodies_total, checked = 0, 0, []
    root_expression = result_rekey_expression(case, units)
    root_invocations = []
    for current in invocations:
        identity = _location_identity(current["expression"])
        origin = origins.get(identity)
        require(origin is not None, "Trace names another original rekey expression")
        for name in ("expression", "input", "body"):
            exact_location(current[name], origin[name], units)
        if root_expression and identity == _location_identity(root_expression):
            root_invocations.append(current)
        evaluations, admissions = current["input_evaluations"], current["input_admissions"]
        require(type(evaluations) is type(admissions) is int and evaluations in (0, 1) and admissions in (0, 1) and admissions <= evaluations,
                "One invocation repeated or skipped its complete input boundary")
        inputs = current.get("input_keys")
        if inputs is not None:
            require(inputs == sorted(set(inputs)) and len(inputs) <= 256,
                    "Admitted input keys/cardinality differ from immutable canonical input")
            require(canonical_probe_type(current["input_type"]) == "Keyed<" + canonical_probe_type(origin["element_type"]) + ">",
                    "Input boundary changed the exact canonical payload type")
        success = "output_keys" in current
        if success:
            require(evaluations == admissions == 1 and inputs is not None and
                    current["output_keys"] == sorted(set(current["output_keys"])) and
                    len(current["output_keys"]) == len(inputs) and
                    canonical_probe_type(current["output_type"]) == "Keyed<" + canonical_probe_type(origin["element_type"]) + ">",
                    "Successful invocation changed key cardinality or exact payload type")
        checks = current["abstract_body_checks"]
        require(isinstance(checks, list) and isinstance(current["timeline"], list), "Malformed abstract-check timeline")
        counters = {"input_evaluations_started": 0, "input_admissions_completed": 0, "body_evaluations_started": 0}
        increments = {"evaluate_input": "input_evaluations_started", "admit_input": "input_admissions_completed",
                      "body": "body_evaluations_started"}
        check_index, preinput_checks = 0, 0
        for event in current["timeline"]:
            if event["event"] != "abstract_body":
                if event["event"] in increments:
                    counters[increments[event["event"]]] += 1
                continue
            require(event == {"event": "abstract_body"} and check_index < len(checks),
                    "Abstract observation lacks its matching timeline event")
            check = checks[check_index]; check_index += 1
            require(all(type(check.get(name)) is int and check[name] == count for name, count in counters.items()),
                    "Abstract observation counters do not match its exact dynamic timeline position")
            if not any(counters.values()):
                preinput_checks += 1
            else:
                require(counters["input_evaluations_started"] == counters["input_admissions_completed"] == 1 and
                        counters["body_evaluations_started"] > 0,
                        "Later abstract callback check lies outside an admitted dynamic body")
            incoming, effective = check.get("locals"), check.get("effective_locals")
            require(isinstance(incoming, dict) and isinstance(effective, dict) and set(incoming) == set(effective) and
                    all(value.get("known") is False and set(value) == {"type", "known"} and
                        value["type"] == incoming[name].get("type") for name, value in effective.items()) and
                    (not any(value.get("known") is True for value in incoming.values()) or check.get("mask_observed") is True),
                    "Unknown-payload check retained or dropped an enclosing local/type or omitted actual masking")
            declaration = binders[identity]
            for name, wanted_type in zip(declaration["names"], declaration["types"]):
                require(name in effective and effective[name] == {"type": canonical_probe_type(wanted_type), "known": False},
                        "Callback binder did not retain exact readonly String/payload types")
        require(check_index == len(checks) and counters["input_evaluations_started"] == evaluations and
                counters["input_admissions_completed"] == admissions and
                counters["body_evaluations_started"] == len(current["body_keys"]),
                "Abstract/dynamic trace counts differ from their complete recorded timeline")
        if evaluations or success:
            require(preinput_checks > 0, "Dynamic input started without its preinput unknown-payload callback check")
        body_keys = current["body_keys"]
        require(isinstance(body_keys, list) and len(body_keys) == len(set(body_keys)),
                "One input callback was repeated")
        if inputs is not None:
            require(body_keys == inputs[:len(body_keys)] and (not success or body_keys == inputs),
                    "Callbacks skipped/reordered original canonical input keys")
        else:
            require(not body_keys and not admissions, "Body ran before complete input admission")
        dynamic = [event for event in current["timeline"] if event["event"] != "abstract_body"]
        wanted = []
        if evaluations:
            wanted.append({"event": "evaluate_input"})
        if admissions:
            wanted.append({"event": "admit_input"})
            for key in inputs:
                wanted.extend([{"event": "keyed_rekey_iteration", "key": key}, {"event": "body", "key": key},
                    {"event": "keyed_rekey_key_validation", "key": key}, {"event": "keyed_rekey_collision", "key": key}])
            wanted.append({"event": "keyed_rekey_publication", "key": None})
        require(dynamic == wanted[:len(dynamic)] and (not success or dynamic == wanted),
                "Actual input/body/key-validation/collision/publication timeline differs")
        checkpoints = current["checkpoints"]
        require([{"event": item["stage"], "key": item["key"]} for item in checkpoints] ==
                [event for event in dynamic if event["event"].startswith("keyed_rekey_")],
                "Trace timeline is not bound to actual current-ledger checkpoints")
        operations = [current["operations_before"], *[item["consumed_operations"] for item in checkpoints], current["operations_after"]]
        entries = [current["value_entries_before"], *[item["value_entries"] for item in checkpoints], current["value_entries_after"]]
        require(all(type(value) is int and value >= 0 for value in operations + entries) and operations == sorted(operations) and entries == sorted(entries),
                "Observed work/value counters decreased or are malformed")
        require(current["operations_after"] <= budget["consumed_operations"], "Expression work lies outside the actual shared request ledger")
        if success:
            snapshot = current["snapshot_ledger"]
            require(snapshot["operations_before"] == snapshot["operations_after"] and
                    snapshot["value_entries_before"] == snapshot["value_entries_after"],
                    "Private observation changed charged product work")
            check_rekeys(current["aggregate_rekey_records"], units, aggregate=True)
            require(set(current["stored_leaf_rekey_records"]) == set(current["output_keys"]), "Private leaf origin inventory differs")
            for records in current["stored_leaf_rekey_records"].values():
                check_rekeys(records, units)
        checkpoints_total += len(checkpoints); bodies_total += len(body_keys)
        checked.append({"expression": current["expression"], "body_keys": body_keys, "input_evaluations": evaluations,
                        "input_admissions": admissions, "checkpoint_count": len(checkpoints), "completed": success})
    if "input_dynamic_evaluations" in expected:
        require(len(root_invocations) == 1 and root_invocations[0]["input_evaluations"] == expected["input_dynamic_evaluations"],
                "Frozen once-only input observation differs")
    if "body_key_order" in expected:
        actual_order = [key for current in root_invocations for key in current["body_keys"]]
        require(actual_order == expected["body_key_order"], "Frozen callback order until first refusal differs")
    if "body_evaluations" in expected:
        require(sum(len(current["body_keys"]) for current in root_invocations) == expected["body_evaluations"],
                "Frozen callback evaluation count differs")
    if "checkpoint_counts" in expected:
        actual = Counter(item["stage"] for current in root_invocations for item in current["checkpoints"])
        require({key: actual[key] for key in expected["checkpoint_counts"]} == expected["checkpoint_counts"] and
                set(actual) <= set(expected["checkpoint_counts"]), "Frozen actual checkpoint counts differ")
    if "exact_stored_rekey_records" in expected:
        require(len(root_invocations) == 1 and root_invocations[0].get("stored_leaf_rekey_records") == expected["exact_stored_rekey_records"],
                "Exact private stored leaf lineage differs from independently authored order")
    observed = trace.get("execution_budget", {})
    require(observed.get("consumed_operations") == budget.get("consumed_operations") and
            observed.get("effective") == budget.get("effective") and observed.get("host_ceilings") == budget.get("host_ceilings"),
            "Trace belongs to another request ledger or authority")
    return {"invocations": checked, "count": len(checked), "body_evaluations": bodies_total, "checkpoints": checkpoints_total}


def check_budget(budget, case):
    require(budget.get("defaults") == {"max_operations": 100000, "max_elapsed_ms": 30000} and
            budget.get("host_ceilings") == case["host_policy"], "Source request changed ordinary defaults or independent host ceiling")
    effective = budget.get("effective")
    if effective:
        for key in ("max_operations", "max_elapsed_ms"):
            require(effective[key] <= case["host_policy"][key], "Source request exceeded current host authority")
    require(type(budget.get("consumed_operations")) is int and budget["consumed_operations"] >= 0,
            "Source receipt omitted actual charged work")


def check_source_manifest(receipt, expected_manifest, declared_png_ids=None):
    """Bind the actual full registry even when callbacks/collections are empty."""
    manifest = receipt.get("source_manifest")
    require(manifest == expected_manifest, "Actual source receipt changed its complete immutable unit/asset registry")
    png_ids = [asset["asset_id"] for asset in manifest["assets"] if asset["media_type"] == "image/png"]
    if declared_png_ids is not None:
        require(png_ids == declared_png_ids, "Actual declared PNG registry differs from the independent frozen expectation")
    return png_ids


def verify_case(case, record, control_record, fixtures, directory):
    require(record.get("input_lineage") == input_lineage(fixtures), "Source record names another input lineage")
    require(record["name"] == case["name"] and record["id"] == case["id"] and
            record["file_manifest"] == case["file_manifest"] and record["host_policy"] == case["host_policy"],
            "Actual source case/authority identity differs")
    envelope = read_json(directory, record["receipt"])
    receipt = envelope.get("result", envelope)
    require(record["program_revision"] == case["program_revision"] == receipt["program_revision"],
            "Actual source receipt names another immutable bundle")
    units = source_units(case_payload(fixtures, case))
    png_ids = check_source_manifest(receipt, case["canonical_manifest"],
                                    (case.get("expected") or {}).get("expected_declared_png_ids"))
    locations = check_all_locations(receipt, units)
    observed = codes(receipt)
    require(record["diagnostic_codes"] == observed and receipt.get("outcome") == case["expected_protocol_outcome"],
            "Actual source diagnostic/protocol outcome differs")
    budget = envelope.get("execution_budget") or receipt.get("execution_budget") or {}
    check_budget(budget, case)
    trace_report = None
    is_core = case["name"] in fixtures["core_cases"]
    legacy = units["entry"]["source"].lstrip().startswith('ontokin "0.18";')
    if is_core and not legacy:
        trace = read_json(directory, record["execution_trace"])
        trace_report = check_execution_trace(trace, case, units, budget, fixtures)
    if case["expected_outcome"] == "invalid":
        require(not record.get("delivered") and "glb" not in record and receipt.get("achieved_level") != "delivered",
                "Refused source published an artifact")
        if case["expected_code"] is not None:
            require(case["expected_code"] in observed, "Source refusal lost its exact frozen diagnostic code")
        else:
            require(any(code.startswith(("OKL-E-", "OKE-E-")) for code in observed), "Source refusal lacks inherited diagnostic")
        if case["expected_code"] != "OKL-E-RESOURCE":
            require("OKL-E-RESOURCE" not in observed, "Resource exhaustion substituted for frozen semantic refusal")
        anchor = diagnostic_anchor(receipt, case, units) if case["expected_code"] else None
        return {"case": case["name"], "status": "passed", "outcome": "refused", "expected_code": case["expected_code"],
                "source_locations": locations, "diagnostic": anchor, "execution_trace": trace_report,
                "declared_png_ids": png_ids}
    require(control_record is not None and control_record["input_lineage"] == input_lineage(fixtures) and
            control_record["program_revision"] == case["explicit_c085_control"]["program_revision"],
            "Missing separately authored explicit .18 control")
    previous_envelope = read_json(directory, control_record["receipt"])
    previous = previous_envelope.get("result", previous_envelope)
    check_source_manifest(previous, case["explicit_c085_control"]["canonical_manifest"],
                          (case.get("expected") or {}).get("expected_declared_png_ids"))
    require(previous.get("outcome") == "valid" and previous["program_revision"] == control_record["program_revision"] and
            not any(code.startswith(("OKL-E-", "OKE-E-")) for code in observed + codes(previous)), "Valid source/control did not complete")
    inspection = check_inspection(read_json(directory, record["inspection"]), read_json(directory, control_record["inspection"]), case, fixtures)
    result = {"case": case["name"], "status": "passed", "outcome": "represented", "inspection": inspection,
              "execution_trace": trace_report, "actual_operations": budget["consumed_operations"], "declared_png_ids": png_ids}
    if case["expected_stage"] == "delivered":
        require(record.get("delivered") and receipt.get("achieved_level") == "delivered", "Delivery did not publish its required bytes")
        raw = ordinary_path(directory, record["glb"]).read_bytes(); control = ordinary_path(directory, control_record["glb"]).read_bytes()
        require(len(raw) == record["bytes"] and sha(raw) == record["sha256"] and
                len(control) == control_record["bytes"] and sha(control) == control_record["sha256"], "Retained source/control GLB identity differs")
        result.update(outcome="delivered", artifact=check_artifact(raw, case, fixtures, control))
    else:
        require(receipt.get("achieved_level") in ("represented", "constructed", "executed") and not record.get("delivered") and "glb" not in record,
                "Core represented source changed its required stage")
    return result


def verify(directory, fixtures, *, scope="all"):
    summary = read_json(directory, "summary.json")
    report = {"schema_version": "ontokin.c086-independent-source-delivery-readback/0.1", "status": "running", "scope": scope,
        "started_utc": datetime.now(timezone.utc).isoformat(), **input_lineage(fixtures),
        "actual_git": summary["git"], "producer_summary_sha256": sha((directory / "summary.json").read_bytes()),
        "cases": [], "agent_artifacts": [], "hostile_glbs": [], "failures": [], "release_acceptance": False,
        "full_product_acceptance": False}
    def section(name, action):
        try:
            return action()
        except Exception as error:
            report["failures"].append({"scope": name, "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc()})
            return None
    section("frozen_input_lineage", lambda: require_lineage(summary, fixtures))
    records = {row["name"]: row for row in summary["cases"]}
    controls = {row["name"]: row for row in summary["controls"]}
    section("complete_source_inventory", lambda: require(len(summary["cases"]) == len(records) == 184 and set(records) == set(fixtures["cases"]),
            "Complete 177-core/seven-Agent source inventory missing or duplicated"))
    valid = {case["name"] for case in fixtures["cases"].values() if case["expected_outcome"] == "valid"}
    section("complete_literal_control_inventory", lambda: require(len(summary["controls"]) == len(controls) == 122 and set(controls) == valid,
            "Complete 118-core/four-Agent literal control inventory missing or duplicated"))
    for case in fixtures["cases"].values():
        result = section("source/" + case["name"], lambda case=case: verify_case(case, records[case["name"]], controls.get(case["name"]), fixtures, directory))
        if result is not None:
            report["cases"].append(result)
    if scope == "all":
        by_revision = delivered_by_revision(fixtures)
        for item in summary.get("agent_artifacts", []):
            def check(item=item):
                case = by_revision[item["program_revision"]]
                raw = ordinary_path(directory, item["glb"]).read_bytes()
                require(len(raw) == item["bytes"] and sha(raw) == item["sha256"], "Retrieved Agent artifact identity differs")
                result = check_artifact(raw, case, fixtures, ordinary_path(directory, controls[case["name"]]["glb"]).read_bytes())
                return {**result, "project_id": item["project_id"], "artifact_id": item["artifact_id"], "export_request_id": item["export_request_id"]}
            result = section("agent_artifact/" + item["glb"], check)
            if result is not None:
                report["agent_artifacts"].append(result)
        def hostiles():
            from tools.keyed_rekey_adversaries import build_mutations
            specification = fixtures["adversaries"]; names = set(specification["source_cases"])
            pairs = {(name, rule["id"]) for name in names for rule in specification["requirements"]
                     if name in rule.get("applicable_source_cases", specification["source_cases"])}
            actual = summary.get("hostile_glbs", [])
            require(len(pairs) == len(actual) == 68 and {(item["case"], item["id"]) for item in actual} == pairs,
                    "The exact 22+24+22 applicable supplied-byte inventory is incomplete")
            bases = {name: ordinary_path(directory, records[name]["glb"]).read_bytes() for name in names}
            mutations = {(name, item["id"]): item for name in names for item in
                         build_mutations(bases[name], fixtures["cases"][name], specification=specification)}
            positive = summary.get("supplied_glb_positive_controls", [])
            require(len(positive) == 3 and {item["case"] for item in positive} == names and all(
                    item.get("status") == "observed_as_expected" and item["sha256"] == sha(bases[item["case"]]) and item.get("validation") for item in positive),
                    "Product positive controls are missing or name other bytes")
            retained = read_json(directory, "hostile-glbs/production-observations.json")
            require(retained["positive_controls"] == positive and retained["hostile_controls"] == actual,
                    "Supplied-byte raw observation inventories disagree")
            for item in actual:
                name, case = item["case"], fixtures["cases"][item["case"]]; expected = mutations[(name, item["id"])]
                raw = ordinary_path(directory, item["path"]).read_bytes()
                require(raw != bases[name] and raw == expected["data"] and len(raw) == item["bytes"] and sha(raw) == item["sha256"] and
                        item["base_sha256"] == expected["base_sha256"] and item["mutation"] == expected["mutation"],
                        "Actual supplied-byte mutation is not the prescribed isolated changed bytes")
                diagnostic = item.get("actual_export_code")
                require(item.get("status") == "observed_as_expected" and type(diagnostic) is str and diagnostic.startswith(("OKL-E-", "OKE-E-")) and
                        "RESOURCE" not in diagnostic and "BUDGET" not in diagnostic and
                        diagnostic == item.get("exception", {}).get("details", {}).get("export_code") and
                        item.get("diagnostic_codes") == codes(item.get("exception")) and not any("RESOURCE" in code for code in item["diagnostic_codes"]),
                        "Product refusal is absent or substituted by resource exhaustion")
                try:
                    check_artifact(raw, case, fixtures, ordinary_path(directory, controls[name]["glb"]).read_bytes())
                except ReferenceError as error:
                    report["hostile_glbs"].append({"case": name, "id": item["id"], "sha256": sha(raw),
                        "actual_product_code": diagnostic, "independent_refusal": str(error), "status": "passed"})
                else:
                    raise ReferenceError("Independent reader accepted isolated supplied-byte mutation " + name + "/" + item["id"])
        section("supplied_byte_adversaries", hostiles)
        section("workflow_inventory", lambda: require(len(summary.get("workflows", [])) == 10 and
            {item["id"] for item in summary["workflows"]} == {f"A{i:02}" for i in range(1, 11)} and
            all(item.get("status") == "observed_as_expected" for item in summary["workflows"]), "Complete actual Agent workflow inventory is absent"))
    section("producer_terminal_status", lambda: require(summary.get("status") == "produced_as_expected" and not summary.get("failures"),
            "Producer retained a failed or incomplete invocation"))
    report["status"] = "failed" if report["failures"] else "passed"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["coverage"] = {"source_cases": len(report["cases"]), "core_cases": sum(row["case"] in fixtures["core_cases"] for row in report["cases"]),
        "represented_sources": sum(row["outcome"] == "represented" for row in report["cases"]),
        "delivered_sources": sum(row["outcome"] == "delivered" for row in report["cases"]),
        "refused_sources": sum(row["outcome"] == "refused" for row in report["cases"]),
        "agent_artifacts": len(report["agent_artifacts"]), "hostile_glbs": len(report["hostile_glbs"])}
    report["remaining_independent_gates"] = ["Raw Agent lifecycle/SQLite audit", "Pinned native destination readers and direct capture review", "Broader retained complete validation and integration"]
    if scope == "sources":
        report["remaining_independent_gates"].insert(0, "Actual Agent artifact and all68 supplied-byte checks")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-rekey")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scope", choices=("sources", "all"), default="all")
    parser.add_argument("--input-amendment", choices=tuple(row["id"] for row in AMENDMENTS),
                        default=AMENDMENTS[-1]["id"], help="Explicit adopted lineage; historical choice rereads retained evidence only")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must name a new report file")
    try:
        report = verify(args.results.resolve(), load_fixtures(args.fixtures, through_amendment=args.input_amendment), scope=args.scope)
    except Exception as error:
        report = {"schema_version": "ontokin.c086-independent-source-delivery-readback/0.1", "status": "failed",
                  "scope": args.scope, "exception": type(error).__name__, "reason": str(error),
                  "traceback": traceback.format_exc(), "release_acceptance": False, "full_product_acceptance": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "scope": args.scope, **report.get("coverage", {}),
                      "failures": len(report.get("failures", [])), "reason": report.get("reason")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
