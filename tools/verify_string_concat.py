#!/usr/bin/env python3
"""Read C087 actual source/value/ledger/GLB evidence independently.

Expected values, source roles, diagnostics and limits come from the published
preimplementation inputs. This reader imports no OntoKin runtime module.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.string_concat_reference import (
    FREEZE_COMMIT, FREEZE_SHA256, PROFILE, TARGET, ReferenceError, require, sha,
    canonical, loads, ordinary_path, load_fixtures, input_lineage, case_payload,
    source_units, codes, walk, check_all_locations, check_location, check_private_value,
    read_private_json, check_inspection, check_artifact, delivered_by_revision,
    check_transforms, check_filters, check_reductions, check_merges, check_zips, check_rekeys,
)


def read_json(directory, name):
    return loads(ordinary_path(directory,name).read_bytes())


def require_lineage(value, fixtures):
    require(all(value.get(key)==wanted for key,wanted in input_lineage(fixtures).items()),
            "Evidence names another exact frozen input lineage")


def location_key(location):
    return tuple(location.get(key) for key in ("source_id","start_byte","end_byte"))


def public_diagnostic(expected):
    result = {key:copy.deepcopy(value) for key,value in expected.items()
              if key not in ("comparison","location","no_dynamic_concat_stage_reached")}
    result["schema_version"] = "ontokin.diagnostic/0.2"
    if isinstance(result.get("repair"),str):
        result["repair"] = {"summary":result["repair"],"patches":[]}
    for value in [result.get("primary"),*result.get("related",[])]:
        if isinstance(value,dict) and "filename" in value:
            value["file"] = value.pop("filename")
    return result


def check_diagnostic(receipt, expected):
    wanted = public_diagnostic(expected)
    require(receipt.get("diagnostics")==[wanted], "Complete frozen diagnostic fields differ")
    require(receipt.get("outcome")==wanted["category"], "Refusal outcome differs from exact diagnostic category")
    return {"code":wanted["code"],"primary":wanted.get("primary"),"details":wanted["details"],"complete_fields_equal":True}


def check_budget(budget,case):
    require(budget.get("defaults")=={"max_operations":100000,"max_elapsed_ms":30000} and
            budget.get("host_ceilings")==case["host_policy"], "Actual ledger defaults/current authority differ")
    for key,value in (budget.get("effective") or {}).items():
        require(key in case["host_policy"] and value<=case["host_policy"][key], "Actual effective ledger raises host authority")
    require(type(budget.get("consumed_operations")) is int and budget["consumed_operations"]>=0,
            "Actual charged work omitted")


def expected_ticks(left,right,reserved):
    """Scalar-width arithmetic derived from SPECIFICATION, independent of runtime."""
    ticks=[("string_concat_admission",1)]
    total=0
    for value in (left,right):
        own=0
        for char in value:
            scalar=ord(char)
            require(not 0xD800<=scalar<=0xDFFF,"Observed String contains a surrogate")
            width=1 if scalar<0x80 else 2 if scalar<0x800 else 3 if scalar<0x10000 else 4
            delta=(own+width+63)//64-(own+63)//64
            if delta:
                ticks.append(("string_concat_scan",delta))
            own+=width;total+=width
            if total>65536:
                return ticks,0,{"budget":"string_concat_result_bytes","limit":65536,"consumed":total,"profile":PROFILE}
    ticks.append(("string_concat_allocation",1+(total+63)//64))
    if reserved+total>4194304:
        return ticks,0,{"budget":"string_concat_total_bytes","limit":4194304,"consumed":reserved+total,"profile":PROFILE}
    ticks.append(("string_concat_publication",1))
    return ticks,total,None


def refused_call_count(case):
    # These counts are consequences of the frozen original source expressions:
    # one overflowing operation, canonical traversal through the first bad key,
    # two independent merge operands, or seventeen nested doubling invocations.
    name=case["name"]
    if name in {"result-N-plus-1","oversize-left-plus-empty","oversize-right-plus-empty","result-crossing-four-byte"}:return 1
    if name=="repeated-doubling-overflow":return 17
    if case["expected_code"]=="OKL-E-ID":
        if name=="merge-overlapping-namespaces-refused":return 2
        details=case["diagnostic"]["details"]
        old=details.get("old_key",details.get("duplicate_old_key"))
        operations=[row for row in case["source_operations"] if row["kind"]=="rekey_keyed"]
        require(len(operations)==1,"Unspecified canonical refused-key traversal")
        span=operations[0]["input"]
        keys=sorted(row["key"] for row in case["source_keyed_entries"] if
            row["location"]["source_id"]==span["source_id"] and
            span["start_byte"]<=row["location"]["start_byte"]<row["location"]["end_byte"]<=span["end_byte"])
        require(old in keys,"Frozen original refused key absent from literal input")
        return keys.index(old)+1
    return 0


def check_execution_trace(trace,values,case,units,budget,fixtures):
    require_lineage(trace,fixtures)
    legacy=units["entry"]["source"].lstrip().startswith('ontokin "0.19";')
    require(trace.get("schema_version")=="ontokin.c087-string-execution-observation/0.1" and
            trace.get("case")==case["name"] and trace.get("program_revision")==case["program_revision"] and
            trace.get("profile")==("keyed-rekey-0.1" if legacy else PROFILE) and
            trace.get("requested_level")=="constructed" and
            trace.get("public_api") == ("KeyedRekeyProgramRuntime.validate_revision" if legacy else
                                        "StringConcatProgramRuntime.validate_revision"), "Trace public source binding differs")
    calls=trace.get("helper_invocations"); require(isinstance(calls,list),"Missing actual helper observations")
    raw=values.get("helper_values")
    require(isinstance(raw,list) and len(raw)==len(calls) and len({r["index"] for r in raw})==len(raw),
            "Exact helper operand/result inventory differs")
    by_index={row["index"]:row for row in raw}
    originals={location_key(row["expression"]):row for row in case.get("source_operations",[]) if row["kind"]=="binary" and row["operator"]=="+"}
    operations_before=-1;reserved=0;observations=[];successful=[]
    for index,call in enumerate(calls):
        require(call["index"]==index and call["operations_before"]>=operations_before and
                call["reserved_bytes_before"]==reserved,"Helper order or cumulative request reservation differs")
        operands=by_index[index];left,right,result=operands["left"],operands["right"],operands["result"]
        require(isinstance(left,str) and isinstance(right,str),"Helper observed non-String operands")
        check_location(call["expression"],units)
        if case["name"] in fixtures["core_cases"]:
            require(location_key(call["expression"]) in originals,"Helper observed another original String expression")
        unit=units[call["expression"]["source_id"]]["source"]
        require(re.search(r'\bontokin\s+"0\.20"\s*;',unit) and re.search(r'\bprofile\s+"string-concat-0\.1"\s*;',unit),
                "New String work ran under another declaring-unit contract")
        schedule,increment,refusal=expected_ticks(left,right,reserved)
        require([(tick["stage"],tick["amount"]) for tick in call["ticks"]]==schedule,
                "Actual String stage/scan block/allocation schedule differs")
        previous=call["operations_before"]
        for tick in call["ticks"]:
            reservation=reserved+(increment if tick["stage"]=="string_concat_publication" else 0)
            require(location_key(tick["expression"])==location_key(call["expression"]) and
                    tick["operations_before"]==previous and tick["operations_after"]==previous+tick["amount"] and
                    tick["reserved_bytes_before"]==tick["reserved_bytes_after"]==reservation and
                    not tick.get("exception"),"Actual named tick does not retain exact original ledger accounting")
            previous=tick["operations_after"]
        require(previous==call["operations_after"],"Hidden or omitted work inside String helper")
        require(call["left_utf8_bytes"]==len(left.encode()) and call["right_utf8_bytes"]==len(right.encode()),
                "Claimed operand sizes differ from exact observed Strings")
        if refusal:
            require(result is None and call.get("exception",{}).get("code")=="OKL-E-RESOURCE" and
                    call["exception"].get("details")==refusal and call["result_utf8_bytes"] is None and
                    call["result_sha256"] is None,"Resource refusal differs from first over-limit scalar/request reservation")
        else:
            require(isinstance(result,str) and result==left+right and not call.get("exception") and
                    call["result_utf8_bytes"]==len(result.encode()) and call["result_sha256"]==sha(result.encode()),
                    "Actual scalar sequence/empty fast path/result digest differs")
            totals=Counter()
            for stage,amount in schedule:totals[stage.removeprefix("string_concat_")]+=amount
            successful.append({"left_utf8_bytes":len(left.encode()),"right_utf8_bytes":len(right.encode()),
                "result_utf8_bytes":len(result.encode()),**{key:totals[key] for key in ("admission","scan","allocation","publication")},
                "total":sum(totals.values()),"cumulative_result_reservation_bytes":increment})
        reserved+=increment
        require(call["reserved_bytes_after"]==reserved,"Completed helper reservation was reset or changed")
        operations_before=call["operations_after"]
        observations.append({"index":index,"expression":call["expression"],"added_operations":sum(amount for _,amount in schedule),
                             "reserved_bytes_after":reserved,"refusal":refusal})
    aggregate=case.get("aggregate_expectation")
    is_core=case["name"] in fixtures["core_cases"]
    if aggregate:
        require(len(calls)==aggregate["attempted_concatenations"] and len(successful)==aggregate["successful_concatenations"] and
                reserved==aggregate["reserved_result_utf8_bytes"],"Actual cumulative preceding work differs from frozen aggregate boundary")
    elif is_core and case["expected_outcome"]=="valid":
        require(successful==case["expected_dynamic_concat_calls"] and len(calls)==len(successful),
                "Actual execution count/operand byte charges differ from frozen selected work")
    elif is_core:
        require(len(calls)==refused_call_count(case),"Refusal skipped or repeated original dynamically selected work")
    elif case["expected_outcome"]=="valid":
        require(len(calls)==len(case["first_members_in_authored_order"])+len(case["sibling_members"]),
                "Computed Agent prefix did not execute once for each original member")
    binaries=trace.get("binary_invocations")
    require(isinstance(binaries,list),"Missing abstract/dynamic binary observation inventory")
    abstract_count=0
    for binary in binaries:
        check_location(binary["expression"],units)
        if is_core:require(location_key(binary["expression"]) in originals,"Binary trace names another original addition")
        events=binary["operand_evaluations"]
        sequence=[(e["side"],e["event"]) for e in events]
        expected_sequences=[[("left","start"),("left","end"),("right","start"),("right","end")],
                            [("left","start"),("left","exception")],
                            [("left","start"),("left","end"),("right","start"),("right","exception")]]
        require(sequence in expected_sequences,"Original operands were skipped, repeated or reordered")
        for event in events:
            check_location(event["source_location"],units)
            if is_core:
                require(location_key(event["source_location"])==location_key(originals[location_key(binary["expression"])][event["side"]]),
                        "Operand trace belongs to another original child")
        if binary["abstract"]:
            abstract_count+=1
            require(binary["reserved_bytes_before"]==binary["reserved_bytes_after"] and
                    len({event["helper_invocations_completed"] for event in events})<=1,"Abstract checking executed new String payload work")
            if binary.get("returned_type")=="String" and binary["declaring_profile"]==PROFILE:
                require(binary.get("returned_known") is False,"Abstract String addition synthesized a known payload")
    user_calls=trace.get("user_function_invocations")
    require(isinstance(user_calls,list),"Missing actual source-defined invocation observations")
    if is_core:
        require(len(user_calls)==case["actual_helper_invocation_count"],"Actual source helper call count differs from frozen selected execution")
        if case["expected_outcome"]=="valid":
            wanted={tuple(r["element_id"]) for r in case["required_actual_definition_dependencies"]}
            require({tuple(r["definition_id"]) for r in user_calls}==wanted,"Actual source helper identity differs from frozen definition closure")
    for call in user_calls:
        check_location(call["definition"],units);check_location(call["caller"],units)
    for key in ("consumed_operations","effective","host_ceilings","caller_caps"):
        require(trace["execution_budget"].get(key)==budget.get(key),"Trace uses another actual request ledger")
    return {"actual_concatenations":len(calls),"successful_concatenations":len(successful),"reserved_utf8_bytes":reserved,
            "abstract_binary_observations":abstract_count,"actual_user_function_calls":len(user_calls),"invocations":observations}


def dedup(records):
    seen=set();result=[]
    for record in records:
        key=canonical(record)
        if key not in seen:result.append(record);seen.add(key)
    return result


def selected_rekey_records(operations,key):
    selected=[];current=key
    for operation in reversed(operations):
        matches=[row for row in operation["selected_records"] if row["new_key"]==current]
        if matches:
            require(len(matches)==1,"Ambiguous frozen selected rekey contributor")
            selected.insert(0,matches[0]);current=matches[0]["old_key"]
    return selected


def check_private_provenance(provenance,case,fixtures):
    require(provenance["program_revision"]==case["program_revision"] and set(provenance["values"])=={"shape.result"},
            "Private provenance names another source/field")
    value=provenance["values"]["shape.result"]
    wanted=[{**r,"relationship":"effective_value_dependency"} for r in case["required_actual_member_dependencies"]]
    wanted+=case["required_actual_definition_dependencies"]
    require(value["dependencies"]==wanted and value["generated_dependencies"]==[],"Exact actual member/definition/taint closure differs")
    units=source_units(case_payload(fixtures,case));operations=case["independent_rekey_operations"]
    aggregates=[operation["aggregate_record"] for operation in operations]
    keyed=case["expected"]["type"].startswith("Keyed<")
    families={"rekeys":check_rekeys,"zips":check_zips,"merges":check_merges,"filters":check_filters,
              "reductions":check_reductions,"transforms":check_transforms}
    kind_family={"rekey_keyed":"rekeys","zip_keyed":"zips","merge_keyed":"merges","filter_keyed":"filters",
                 "reduce_keyed":"reductions","map_keyed":"transforms"}
    require(set(value["aggregate"])==set(families),"Private origin family inventory differs")
    for group in [value["aggregate"],*value["leaves"].values()]:
        require(set(group)==set(families),"Private leaf origin family inventory differs")
        for family,reader in families.items():
            if group[family]:
                if family in ("transforms","zips"):
                    reader(group[family],units,rekey_records=group["rekeys"])
                else:reader(group[family],units)
    for kind,family in kind_family.items():
        expected={location_key(r["expression"]) for r in case["source_operations"] if r["kind"]==kind}
        actual={location_key(r["expression"]) for r in value["aggregate"][family]}
        require(actual==expected,"Completed value lost or acquired original "+family+" expression origins")
    if keyed:
        require(value["aggregate"]["rekeys"]==aggregates,"Exact aggregate null-field rekey sequence differs")
        require(set(value["leaves"])==set(case["expected"]["keys"]),"Private surviving leaf provenance inventory differs")
        for key,leaf in value["leaves"].items():
            expected=aggregates+selected_rekey_records(operations,key)
            require(dedup(value["aggregate"]["rekeys"]+leaf["rekeys"])==expected,
                    "Exact surviving leaf original/rekeyed key/payload-entry lineage differs")
    elif case["name"]=="rekey-then-index":
        tokens=re.findall(r'\[\s*("(?:\\.|[^"\\])*")\s*\]',case["expression"]["text"])
        require(tokens,"Frozen indexed source lacks its literal selected key")
        require(value["aggregate"]["rekeys"]==aggregates+selected_rekey_records(operations,json.loads(tokens[-1])),
                "Indexed value retained another original contributor")
    elif operations:
        require(case["name"]=="rekey-then-reduce" and value["aggregate"]["rekeys"]==
                aggregates+[record for operation in operations for record in operation["selected_records"]],
                "Reduction lost original aggregate/selected rekey read order")
    else:
        require(not value["aggregate"]["rekeys"],"Ordinary String value acquired invented concat/rekey lineage")
    return {"member_dependencies":len(case["required_actual_member_dependencies"]),
            "called_definitions":len(case["required_actual_definition_dependencies"]),
            "families":{key:len(records) for key,records in value["aggregate"].items()},"surviving_leaves":len(value["leaves"])}


def check_private_record(record,case,fixtures,directory,*,control=False):
    selected=case["explicit_c086_control"] if control else case
    receipt=read_json(directory,record["private_value_receipt"])
    require_lineage(receipt,fixtures)
    require(receipt["program_revision"]==selected["program_revision"] and receipt["public_response_limit_override"] is False,
            "Full ordinary value evidence uses another source or widens a public output limit")
    raw=ordinary_path(directory,record["private_values"]).read_bytes()
    require(sha(raw)==receipt["gzip_sha256"] and len(raw)==receipt["gzip_bytes"],"Private compressed value fingerprint differs")
    actual=read_private_json(ordinary_path(directory,record["private_values"]))
    uncompressed=canonical(actual)
    require(sha(uncompressed)==receipt["raw_sha256"] and len(uncompressed)==receipt["raw_bytes"],"Complete private JSON fingerprint differs")
    check_budget(receipt["execution_budget"],case)
    if case["name"] in fixtures["agent_cases"]:
        require(set(actual["values"])=={"first.renamed","sibling.renamed"},"Agent private field inventory differs")
        for key,wanted in case["expected_keyed_values"].items():
            expected={"type":"Keyed<String>","keys":[r[0] for r in wanted["entries"]],
                "entries":[{"key":k,"value":{"type":"String","literal":v,"utf8_bytes":len(v.encode()),"codepoints":len(v),"sha256":sha(v.encode())}}
                           for k,v in wanted["entries"]]}
            check_private_value(actual["values"][key],expected,fixtures)
        return {"complete_fields":2}
    count=check_private_value(actual,selected["expected"],fixtures)
    provenance=None if control else check_private_provenance(read_json(directory,record["private_provenance"]),case,fixtures)
    return {"complete_typed_leaves":count,"provenance":provenance}


def verify_case(case,record,control_record,fixtures,directory):
    require(record["input_lineage"]==input_lineage(fixtures) and record["producer_status"]=="observed_as_expected",
            "Source record failed production or names another frozen lineage")
    for key in ("id","name","file_manifest","host_policy","program_revision"):
        require(record[key]==case[key],"Source record identity differs: "+key)
    envelope=read_json(directory,record["receipt"]);require_lineage(envelope,fixtures)
    receipt=envelope["result"];budget=envelope["execution_budget"]
    require(receipt["program_revision"]==case["program_revision"] and receipt["source_manifest"]==case["canonical_manifest"],
            "Actual source receipt has another immutable complete registry")
    check_budget(budget,case);units=source_units(case_payload(fixtures,case));check_all_locations(receipt,units)
    require(record["diagnostic_codes"]==codes(receipt),"Recorded diagnostic inventory differs from raw receipt")
    trace=check_execution_trace(read_json(directory,record["execution_trace"]),
        read_private_json(ordinary_path(directory,record["helper_values"])),case,units,budget,fixtures)
    if case["expected_outcome"]!="valid":
        require(not record.get("delivered") and "glb" not in record and receipt["outcome"]!="valid", "Refused source published an artifact")
        if case["name"] in fixtures["core_cases"]:
            diagnostic=check_diagnostic(receipt,case["diagnostic"])
        else:
            require(case["expected_code"] in codes(receipt) and
                    (case["expected_code"]=="OKL-E-RESOURCE" or "OKL-E-RESOURCE" not in codes(receipt)),
                    "Agent source refused for another reason")
            diagnostic={"code":case["expected_code"]}
        return {"case":case["name"],"status":"passed","outcome":"refused","diagnostic":diagnostic,"trace":trace}
    require(receipt["outcome"]=="valid" and receipt["achieved_level"]=="constructed", "Valid source did not reach its constructed level")
    require(control_record is not None,"Valid source lacks independently authored .19 literal control")
    private=check_private_record(record,case,fixtures,directory)
    artifact=None;inspection=None
    if case["name"] in fixtures["agent_cases"]:
        inspection=check_inspection(read_json(directory,record["inspection"]),read_json(directory,control_record["inspection"]),case,fixtures)
        raw=ordinary_path(directory,record["glb"]).read_bytes();old=ordinary_path(directory,control_record["glb"]).read_bytes()
        require(sha(raw)==record["sha256"] and len(raw)==record["bytes"] and record["delivered"],"Delivered actual bytes differ")
        artifact=check_artifact(raw,case,fixtures,old)
    return {"case":case["name"],"status":"passed","outcome":"valid","private":private,"trace":trace,"inspection":inspection,"artifact":artifact}


def verify_control(case,record,fixtures,directory):
    spec=case["explicit_c086_control"]
    require(record["producer_status"]=="observed_as_expected" and record["program_revision"]==spec["program_revision"] and
            record["file_manifest"]==spec["file_manifest"] and record["input_lineage"]==input_lineage(fixtures),"Literal control record differs")
    envelope=read_json(directory,record["receipt"]);require_lineage(envelope,fixtures);receipt=envelope["result"]
    require(receipt["program_revision"]==spec["program_revision"] and receipt["source_manifest"]==spec["canonical_manifest"] and
            receipt["outcome"]=="valid" and receipt["achieved_level"]=="constructed","Actual .19 literal control did not construct")
    check_budget(envelope["execution_budget"],case)
    return {"case":case["name"],"status":"passed","private":check_private_record(record,case,fixtures,directory,control=True)}


def verify(directory,fixtures,*,source_only=False):
    summary=read_json(directory,"summary.json");require_lineage(summary,fixtures)
    cases={r["name"]:r for r in summary["cases"]};controls={r["name"]:r for r in summary["controls"]}
    require(len(cases)==len(summary["cases"])==118 and set(cases)==set(fixtures["cases"]),"Actual source case inventory differs")
    wanted_controls={name for name,case in fixtures["cases"].items() if "explicit_c086_control" in case}
    require(len(controls)==len(summary["controls"])==85 and set(controls)==wanted_controls,"Actual control inventory differs")
    report={"schema_version":"ontokin.c087-independent-supplied-evidence/0.1","status":"running",**input_lineage(fixtures),
        "reader_git":subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip(),
        "actual_git":summary["git"],"cases":[],"controls":[],"negative_controls":[],"agent_artifacts":[],
        "failures":[],"full_product_acceptance":False,"release_acceptance":False}
    def attempt(scope,name,callback):
        try:return callback()
        except Exception as error:
            row={"scope":scope,"name":name,"status":"failed","exception":type(error).__name__,"reason":str(error),"traceback":traceback.format_exc()}
            report["failures"].append(row);return row
    for name,case in fixtures["cases"].items():
        report["cases"].append(attempt("source",name,lambda c=case:verify_case(c,cases[c["name"]],controls.get(c["name"]),fixtures,directory)))
        if name in controls:report["controls"].append(attempt("control",name,lambda c=case:verify_control(c,controls[c["name"]],fixtures,directory)))
    negatives={r["name"]:r for r in summary["predecessor_negative_controls"]}
    require(set(negatives)=={c["name"] for c in fixtures["negative_controls"]["cases"]} and len(negatives)==28,
            "Actual .19 negative control inventory differs")
    for case in fixtures["negative_controls"]["cases"]:
        def negative(case=case):
            row=negatives[case["name"]];require(row["producer_status"]=="observed_as_expected","Inherited negative producer failed")
            receipt=read_json(directory,row["receipt"]);require_lineage(receipt,fixtures)
            return {"case":case["name"],"status":"passed","diagnostic":check_diagnostic(receipt["result"],case["diagnostic"])}
        report["negative_controls"].append(attempt("negative_control",case["name"],negative))
    if not source_only:
        by_revision=delivered_by_revision(fixtures)
        require(summary["agent_artifacts"],"Missing actual complete Agent artifacts")
        for record in summary["agent_artifacts"]:
            def artifact(record=record):
                case=by_revision[record["program_revision"]];raw=ordinary_path(directory,record["glb"]).read_bytes()
                require(sha(raw)==record["sha256"] and len(raw)==record["bytes"],"Actual retrieved complete GLB fingerprint differs")
                return check_artifact(raw,case,fixtures,ordinary_path(directory,controls[case["name"]]["glb"]).read_bytes())
            report["agent_artifacts"].append(attempt("agent_artifact",record["glb"],artifact))
    report.update(status="failed" if report["failures"] else "passed",source_scope_only=source_only,
                  finished_utc=datetime.now(timezone.utc).isoformat())
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--fixtures",type=Path,default=ROOT)
    parser.add_argument("--candidate-source",type=Path,required=True)
    parser.add_argument("--source-only",action="store_true")
    args=parser.parse_args()
    if args.output.exists():parser.error("--output must name a fresh report")
    try:
        fixtures=load_fixtures(args.fixtures)
        fixtures["basis_repository"]=fixtures["control_basis_repository"]=args.candidate_source.resolve()
        report=verify(args.results.resolve(),fixtures,source_only=args.source_only)
    except Exception as error:
        report={"schema_version":"ontokin.c087-independent-supplied-evidence/0.1","status":"failed",
                "exception":type(error).__name__,"reason":str(error),"traceback":traceback.format_exc(),
                "release_acceptance":False,"full_product_acceptance":False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({key:report[key] for key in ("status","reason") if key in report}|{"failures":len(report.get("failures",[]))}))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
