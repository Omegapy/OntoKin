#!/usr/bin/env python3
"""Read supplied C085 source, inspection, control and artifact evidence independently."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.keyed_zip_reference import (DELIVERED_CASES, FREEZE_COMMIT, FREEZE_SHA256,
    ReferenceError, case_payload, check_artifact, check_inspection, codes, delivered_by_revision, load_fixtures,
    loads, ordinary_path, require, sha, diagnostic_anchor, source_units, check_all_locations,
    canonical_probe_type, same_location, merge_location, _location_identity, PROFILE, check_zips, enriched_zip_records)
from tools.keyed_zip_adversaries import build_mutations

def requires_execution_trace(case):
    return bool(set(case.get("expected",{})) & {"left_input_evaluations","body_evaluations","body_key_order_before_failure","left_dynamic_divisions",
                                               "stored_leaf_zips_exact","paired_entry_zip_records_exact"})


def input_lineage(fixtures):
    return {"frozen_input_commit":FREEZE_COMMIT,"frozen_manifest_sha256":FREEZE_SHA256,
            "amendments":fixtures["amendments"],"original_expected_sha256":fixtures["original_expected_sha256"],
            "effective_expected_sha256":fixtures["effective_expected_sha256"]}


def read_json(directory, relative):
    return loads(ordinary_path(directory, relative).read_bytes())


def check_execution_trace(trace, case, units, budget):
    """Read actual unknown-body checks, admissions, canonical checkpoints and body visits."""
    require(trace.get("schema_version")=="ontokin.c085-zip-execution-observation/0.1" and
            trace.get("case")==case["name"] and trace.get("program_revision")==case["program_revision"]and
            trace.get("profile")==PROFILE and trace.get("requested_level")=="represented"and
            trace.get("public_api")=="KeyedZipProgramRuntime.validate_revision","Trace is not the exact public source invocation")
    expected=case.get("expected")or{};invocations=trace.get("invocations",[])
    if "left_input_evaluations"in expected:
        require(len(invocations)==1,"Frozen once/order fixture requires one dynamic zip invocation")
    origins={_location_identity(r["expression"]):r for r in case.get("source_zip_records",[])}
    checked=[]
    for current in invocations:
        origin=origins.get(_location_identity(current["expression"]))
        require(origin is not None,"Observed zip names another original expression")
        for part in ("expression","left","right","body"):
            merge_location(current[part],origin[part],units)
        if case.get("probe")and "left_input_evaluations"in expected:
            require(current["self_path"]==case["probe"]["object_path"],"Observed zip belongs to another instance")
        for name in ("left_input_evaluations","right_input_evaluations","dynamic_input_order","left_map_visits","right_map_visits",
                     "left_dynamic_divisions","right_dynamic_divisions"):
            if name in expected:
                require(current[name]==expected[name],"Frozen actual evaluation count/order differs: "+name)
        for side in ("left","right"):
            require(current[side+"_input_evaluations"]in(0,1)and current[side+"_input_admissions"]in(0,1),"Input repeated during one invocation")
            if side+"_type"in current:
                require(canonical_probe_type(current[side+"_type"])==canonical_probe_type("Keyed<"+origin[side+"_element_type"]+">"),
                        "Zip input boundary widened or changed")
        event_prefix=["evaluate_left","admit_left","evaluate_right","admit_right"]
        require(current["input_events"]==event_prefix[:len(current["input_events"])],"Right evaluation started before complete left admission")
        successful="output_keys"in current
        require(current["admission_order"]==[x for x in("left","right")if current[x+"_input_admissions"]],"Admission order differs")
        if successful:
            require(current["left_input_admissions"]==current["right_input_admissions"]==1 and current["input_events"]==event_prefix,
                    "Successful zip skipped one complete input admission")
            require(current["left_keys"]==current["right_keys"]==current["output_keys"],"Zip changed complete equal input/output key sets")
            require(canonical_probe_type(current["output_type"])==canonical_probe_type("Keyed<"+origin["output_element_type"]+">"),"Zip output boundary widened")
        left,right=current.get("left_keys"),current.get("right_keys")
        wanted_keyset=[]
        if left is not None and right is not None:
            require(left==sorted(set(left))and right==sorted(set(right)),"Admitted input key order/uniqueness differs")
            for key in sorted(set(left)|set(right)):
                wanted_keyset.append(key)
                if (key in left)!=(key in right):break
            require(current["keyset_keys"]==wanted_keyset,"Complete canonical union key checks were skipped/reordered")
        if left!=right:
            require(not current["iteration_keys"]and not current["body_keys"]and not successful,
                    "Mismatched or failed input reached a body/materialized result")
        for key,name in (("keyset_check_order","keyset_keys"),("body_key_order","body_keys"),("body_key_order_before_failure","body_keys")):
            if key in expected:require(current[name]==expected[key],"Frozen canonical traversal differs: "+key)
        if successful:
            require(current["iteration_keys"]==current["body_keys"]==current["output_keys"],"Body was skipped/repeated/reordered")
        visits=[("keyed_zip_keyset",key)for key in current["keyset_keys"]]+[("keyed_zip_iteration",key)for key in current["iteration_keys"]]
        checkpoints=current["checkpoints"]
        require([(v["stage"],v["key"])for v in checkpoints]==visits,"Real current-ledger checkpoint sequence differs")
        timeline=[{"event":event}for event in current["input_events"]]+[{"event":"keyed_zip_keyset","key":key}for key in current["keyset_keys"]]
        for index,key in enumerate(current["iteration_keys"]):
            timeline.append({"event":"keyed_zip_iteration","key":key})
            if index<len(current["body_keys"]):timeline.append({"event":"body","key":current["body_keys"][index]})
        require(current["timeline"]==timeline,"A body/result iteration preceded complete key-set agreement")
        abstract=current["abstract_body_checks"]
        # Dynamic operand failure may occur during the earlier unknown body
        # check only if its inherited source type itself refuses. Every valid
        # dynamic invocation retains its own original unknown-payload check.
        if successful:
            require(abstract,"Dynamic invocation reused global checking instead of its own unknown body")
        if abstract:
            require(abstract[0]["body_evaluations_started"]==0 and
                    all(not v["known"]for v in abstract[0]["locals"].values()),
                    "Invocation's own unknown-body check began with a concrete capture")
        for observation in abstract:
            incoming,effective=observation["locals"],observation["effective_locals"]
            require(isinstance(effective,dict)and set(effective)==set(incoming)and
                    all(not value["known"]and value["type"]==incoming[name]["type"] for name,value in effective.items()),
                    "Static body received a captured concrete payload")
            require(observation["mask_observed"] or effective==incoming,
                    "Reader invented a normalization without observing the real masking call")
        before,after=current["operations_before"],current["operations_after"]
        values_before,values_after=current["value_entries_before"],current["value_entries_after"]
        require(type(before)is type(after)is int and 0<=before<after and type(values_before)is type(values_after)is int and
                0<=values_before<=values_after,"Zip reset or escaped the cumulative work/value ledger")
        prior,prior_values=before,values_before
        for checkpoint in checkpoints:
            require(type(checkpoint["consumed_operations"])is type(checkpoint["value_entries"])is int and
                    prior<checkpoint["consumed_operations"]<=after and prior_values<=checkpoint["value_entries"]<=values_after,
                    "Actual checkpoint did not monotonically charge one current ledger")
            prior,prior_values=checkpoint["consumed_operations"],checkpoint["value_entries"]
        if successful and origin["output_element_type"]=="PolygonRing"and current["iteration_keys"]:
            iteration=[v for v in checkpoints if v["stage"]=="keyed_zip_iteration"][-1]
            require(values_after-iteration["value_entries"]>4,"Compound paired output lost logical copy charges")
        if successful:
            snapshot=current["snapshot_ledger"]
            require(snapshot["operations_before"]==snapshot["operations_after"]==after and
                    snapshot["value_entries_before"]==snapshot["value_entries_after"]==values_after,
                    "Observational provenance snapshot changed the request ledger")
            aggregate=current["aggregate_zip_records"];stored=current["stored_leaf_zip_records"]
            check_zips(aggregate,units,aggregate=True)
            require(set(stored)==set(current["output_keys"]),"Private leaf observation omitted or invented an entry")
            for key,records in stored.items():
                check_zips(records,units)
                require(records[-1]["key"]==key and _location_identity(records[-1]["expression"])==_location_identity(current["expression"]),
                        "Private zip leaf lost its current actual pair")
        checked.append({"body_evaluations":len(current["body_keys"]),"keyset_checks":len(current["keyset_keys"]),
                        "checkpoint_count":len(checkpoints),"operations":after-before,"value_entries":values_after-values_before})
    if "body_evaluations"in expected:
        require(sum(len(v["body_keys"])for v in invocations)==expected["body_evaluations"],"Frozen dynamic body count differs")
    private=expected.get("stored_leaf_zips_exact")
    if private is None and "paired_entry_zip_records_exact"in expected:
        private={key:[record]for key,record in expected["paired_entry_zip_records_exact"].items()}
    if private and all(records for records in private.values()):
        owners={_location_identity(records[-1]["expression"])for records in private.values()}
        require(len(owners)==1,"Frozen private leaf expectation names different current zip expressions")
        candidates=[current for current in invocations if _location_identity(current["expression"])in owners and "output_keys"in current]
        require(candidates,"Exact private leaf fixture lacks an observed output of its original zip")
        for current in candidates:
            require(set(current["stored_leaf_zip_records"])==set(private),"Private leaf key inventory differs")
            for key,records in private.items():
                check_zips(current["stored_leaf_zip_records"][key],units,expected=records,exact=True)
            if "aggregate_zip_records_exact"in expected:
                check_zips(current["aggregate_zip_records"],units,expected=expected["aggregate_zip_records_exact"],exact=True,aggregate=True)
    observed=trace["execution_budget"]
    require(observed["consumed_operations"]==budget["consumed_operations"]and observed["host_ceilings"]==case["host_policy"]and
            observed["effective"]==budget["effective"]and all(v["operations_after"]<=observed["consumed_operations"]for v in invocations),
            "Expression observations are not part of the actual complete request ledger")
    return {"invocations":checked,"count":len(checked),"body_evaluations":sum(v["body_evaluations"]for v in checked)}


def verify_case(case, record, control_record, fixtures, directory):
    require(record.get("input_lineage") == input_lineage(fixtures), "Source record lacks exact frozen/amended input lineage")
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
        trace_result = None
        if requires_execution_trace(case):
            trace = read_json(directory, record["execution_trace"])
            require(all(trace.get(k)==v for k,v in input_lineage(fixtures).items()), "Trace input lineage differs")
            trace_result = check_execution_trace(trace, case, source_units(case_payload(fixtures, case)), budget)
        return {"case": case["name"], "status": "passed", "outcome": "refused", "expected_code": case["expected_code"],
                "achieved_level": receipt.get("achieved_level"), "budget_stage": budget.get("stage"),
                "source_locations": source_locations, "checked_primary_anchor": anchor, "execution_trace": trace_result}
    require(receipt.get("achieved_level") in ("represented", "delivered", "executed") and
            not any(c.startswith(("OKL-E-", "OKE-E-")) for c in observed), "Valid source did not achieve its required semantics")
    require(control_record is not None and control_record["program_revision"] == case["explicit_c084_control"]["program_revision"], "Missing separately authored .17 control")
    require(control_record.get("input_lineage")==input_lineage(fixtures), "Control observation lineage differs")
    control_envelope = read_json(directory, control_record["receipt"])
    control_receipt = control_envelope.get("result", control_envelope)
    require(control_receipt.get("outcome") == "valid" and control_receipt["program_revision"] == control_record["program_revision"] and not any(c.startswith(("OKL-E-", "OKE-E-")) for c in codes(control_receipt)), "Explicit control did not validate")
    inspection = check_inspection(read_json(directory, record["inspection"]), read_json(directory, control_record["inspection"]), case, fixtures)
    result = {"case": case["name"], "status": "passed", "outcome": "represented", "inspection": inspection,
              "actual_operations": budget.get("consumed_operations"), "actual_elapsed_ms": budget.get("elapsed_ms")}
    if requires_execution_trace(case):
        trace=read_json(directory,record["execution_trace"])
        require(all(trace.get(k)==v for k,v in input_lineage(fixtures).items()),"Trace input lineage differs")
        result["execution_trace"] = check_execution_trace(trace, case, source_units(case_payload(fixtures, case)), budget)
    if case["expected_stage"] == "represented":
        require(not record["delivered"] and "glb" not in record, "Represented fixture was silently converted into an export gate")
        return result
    require(record["delivered"] and receipt.get("achieved_level") == "delivered", "Delivered fixture did not publish a successful named artifact")
    raw = ordinary_path(directory, record["glb"]).read_bytes()
    require(sha(raw) == record["sha256"] and len(raw) == record["bytes"], "Actual source GLB differs from retained identity")
    control = ordinary_path(directory, control_record["glb"]).read_bytes()
    require(sha(control) == control_record["sha256"] and len(control) == control_record["bytes"], "Explicit .17 control GLB differs from retained identity")
    result.update(outcome="delivered", artifact=check_artifact(raw, case, fixtures, control))
    return result


def verify(directory, fixtures):
    summary = read_json(directory, "summary.json")
    report = {"schema_version": "ontokin.c085-independent-readback/0.1", "status": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(), **input_lineage(fixtures), "frozen_input_commit": FREEZE_COMMIT,
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
    section("published_amendment_identity", lambda: require(all(summary.get(k)==v for k,v in input_lineage(fixtures).items()), "Producer input amendment/effective expectation identity differs"))
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
        require(len(actual) == len(pairs) == 72 and {(i["case"], i["id"]) for i in actual} == pairs,
                "Frozen twenty-four supplied-byte adversaries for three source baselines are incomplete")
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
        return {"workflow_count": len(rows), "raw_independent_audit_required": "tools/verify_keyed_zip_agent_evidence.py"}
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
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-zip")
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
