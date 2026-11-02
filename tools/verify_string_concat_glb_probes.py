#!/usr/bin/env python3
"""Independently rebuild and refuse all75 frozen supplied C087 GLB adversaries."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.string_concat_reference import load_fixtures,input_lineage,require,sha,ordinary_path,check_artifact,ReferenceError
from tools.string_concat_adversaries import build_mutations


def verify(sources,probes,fixtures):
    summary=json.loads(ordinary_path(sources,"summary.json").read_bytes())
    production=json.loads(ordinary_path(probes,"production-observations.json").read_bytes())
    for value in (summary,production):
        require(all(value.get(k)==v for k,v in input_lineage(fixtures).items()),"Supplied-byte observations name another frozen lineage")
    require(production["source_summary_sha256"]==sha(ordinary_path(sources,"summary.json").read_bytes()),"Product probes name another source producer")
    records={r["name"]:r for r in summary["cases"]};controls={r["name"]:r for r in summary["controls"]}
    observed={(r["case"],r["id"]):r for r in production["hostile_controls"]}
    positives={r["case"]:r for r in production["positive_controls"]}
    require(len(observed)==len(production["hostile_controls"])==75 and
            set(positives)==set(fixtures["adversaries"]["source_cases"]),"Supplied-byte raw inventory differs")
    report={"schema_version":"ontokin.c087-independent-supplied-byte-audit/0.1",**input_lineage(fixtures),
        "status":"running","positive_controls":[],"hostile_controls":[],"failures":[],"release_acceptance":False}
    for name in fixtures["adversaries"]["source_cases"]:
        case=fixtures["agent_cases"][name];raw=ordinary_path(sources,records[name]["glb"]).read_bytes()
        old=ordinary_path(sources,controls[name]["glb"]).read_bytes()
        positive=positives[name]
        require(positive["sha256"]==sha(raw) and positive["bytes"]==len(raw) and positive["observation"]["accepted"] is True,
                "Actual product rejected the unchanged positive bytes")
        check_artifact(raw,case,fixtures,old)
        report["positive_controls"].append({"case":name,"sha256":sha(raw),"product_accepted":True,"independent_accepted":True})
        for expected in build_mutations(raw,case,fixtures=fixtures):
            row=observed[(name,expected["id"])];changed=ordinary_path(probes,row["path"]).read_bytes()
            require(changed==expected["data"] and all(row[k]==expected[k] for k in ("mutation","base_sha256","sha256","bytes")),
                    "Supplied hostile bytes do not implement the exact isolated frozen mutation")
            observation=row["observation"];diagnostic=observation.get("diagnostic",{})
            codes=[diagnostic.get("code",""),diagnostic.get("details",{}).get("export_code","")]
            require(observation["accepted"] is False and any(code.startswith(("OKE-E-","OKL-E-")) for code in codes) and
                    not any(code.endswith(("-RESOURCE","-BUDGET")) for code in codes),"Product probe substituted exhaustion/unrelated failure for hostile refusal")
            try:check_artifact(changed,case,fixtures,old)
            except (ReferenceError,ValueError,KeyError,TypeError,IndexError) as error:
                report["hostile_controls"].append({"case":name,"id":row["id"],"sha256":sha(changed),
                    "product_refused":True,"product_codes":codes,"independent_refused":True,
                    "independent_exception":type(error).__name__,"reason":str(error)})
            else:report["failures"].append({"case":name,"id":row["id"],"reason":"Independent reader accepted hostile bytes"})
    require(len(report["hostile_controls"])+len(report["failures"])==75,"Independent hostile inventory incomplete")
    report.update(status="failed" if report["failures"] else "passed",finished_utc=datetime.now(timezone.utc).isoformat())
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sources",type=Path,required=True);p.add_argument("--probes",type=Path,required=True)
    p.add_argument("--candidate-source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error("Fresh output report required")
    try:
        f=load_fixtures();f["basis_repository"]=f["control_basis_repository"]=a.candidate_source.resolve()
        report=verify(a.sources.resolve(),a.probes.resolve(),f)
    except Exception as error:report={"status":"failed","reason":str(error),"traceback":traceback.format_exc(),"release_acceptance":False}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"hostile_refusals":len(report.get("hostile_controls",[])),"reason":report.get("reason")}))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":raise SystemExit(main())
