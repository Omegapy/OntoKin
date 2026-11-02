#!/usr/bin/env python3
"""Preserve and refuse three schema-valid partial Agent inspection corruptions."""
from __future__ import annotations
import argparse,copy,json
from pathlib import Path
import sys,traceback
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.string_concat_reference import load_fixtures,case_payload,source_units,sha,require,ReferenceError
from tools.verify_string_concat_agent_evidence import check_partial_panel_values,schema_validators

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--results",type=Path,required=True)
    p.add_argument("--fixtures",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error("Fresh output directory required")
    a.output.mkdir(parents=True);f=load_fixtures(a.fixtures);case=f["agent_cases"]["panel-task"]
    rows=json.loads((a.results/"agent/transcript.json").read_bytes());identity=["panel-task","demo","first"]
    partial=next(r for r in rows if r["workflow"]=="A01" and r["request"]["operation"]=="inspect" and
        r["request"].get("selector")=={"kind":"object","element_id":identity} and
        r["request"].get("program_revision")==case["program_revision"])
    full=next(r for r in rows if r["workflow"]=="A01" and r["request"]["operation"]=="inspect" and
        r["request"].get("selector")=={"kind":"object"} and r["request"].get("program_revision")==case["program_revision"])
    units=source_units(case_payload(f,case));full_items=full["response"]["result"]["items"]
    mutations=[]
    for name in ("wrong-keyed-and-leaf-types","removed-rekey-lineage","missing-selected-total"):
        response=copy.deepcopy(partial["response"]);values=response["result"]["items"][0]["values"]
        if name=="wrong-keyed-and-leaf-types":
            values["renamed"]["type"]="Keyed<Bool>"
            for entry in values["renamed"]["value"]:entry["value"]["type"]="Bool"
        elif name=="removed-rekey-lineage":
            def remove(value):
                if isinstance(value,dict):
                    value.pop("derived_rekeys",None)
                    for child in value.values():remove(child)
                elif isinstance(value,list):
                    for child in value:remove(child)
            remove(values)
        else:del values["selected_total"]
        raw=json.dumps(response,ensure_ascii=False,allow_nan=False).encode()
        path=name+".response.json";(a.output/path).write_bytes(raw)
        mutations.append({"name":name,"path":path,"sha256":sha(raw),"bytes":len(raw),"expected":"refused"})
    # All negative byte streams and expected refusals exist before any check.
    (a.output/"EXPECTED-REJECTIONS.json").write_text(json.dumps({"source_exchange":partial["sequence"],
        "frozen_program_revision":case["program_revision"],"mutations":mutations},indent=2)+"\n")
    check_partial_panel_values(partial["response"]["result"]["items"],full_items,identity,case,f,units)
    validators=schema_validators(f["repository"]);results=[]
    for record in mutations:
        response=json.loads((a.output/record["path"]).read_bytes())
        require(not list(validators["response.schema.json"].iter_errors(response)),"Negative regression must remain schema-valid")
        try:check_partial_panel_values(response["result"]["items"],full_items,identity,case,f,units)
        except ReferenceError as error:results.append({**record,"status":"passed","schema_valid":True,"rejection":str(error)})
        else:results.append({**record,"status":"failed","reason":"Corrupted partial projection accepted"})
    report={"status":"passed" if all(r["status"]=="passed" for r in results) else "failed",
        "positive_original_accepted":True,"regressions":results,"runtime_changed":False,"frozen_inputs_changed":False}
    (a.output/"RESULT.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({"status":report["status"],"regressions":len(results)}))
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":raise SystemExit(main())
