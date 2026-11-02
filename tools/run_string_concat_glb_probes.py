#!/usr/bin/env python3
"""Record actual product decisions for frozen C087 supplied-byte mutations.

This producer makes no independent acceptance decision. A separate reader
rebuilds every mutation from its frozen meaning and checks all raw bytes.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-source",type=Path,required=True)
    parser.add_argument("--sources",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();candidate=args.candidate_source.resolve();output=args.output.resolve()
    if output.exists():parser.error("Output must be a fresh directory")
    sys.path.insert(0,str(ROOT));sys.path.insert(0,str(candidate))
    from tools.string_concat_reference import load_fixtures,input_lineage,sha,PROFILE,TARGET
    from tools.string_concat_adversaries import build_mutations
    import ontokin
    from ontokin.texture_bundle import load_texture_file_manifest
    from ontokin.execution_budget import SharedExecutionBudget,HostPolicy,admit_entry_budget
    from ontokin.construction import compile_construction
    from ontokin.gltf import validate_export
    from ontokin.reach_numeric import ReachExecutionWork
    from ontokin.scene import ExportOptions
    assert Path(ontokin.__file__).resolve().parent==candidate/"ontokin"
    fixtures=load_fixtures(candidate)
    summary=json.loads((args.sources/"summary.json").read_text())
    records={row["name"]:row for row in summary["cases"]}
    git=lambda *words:subprocess.check_output(["git","-C",str(candidate),*words],text=True).strip()
    report={"schema_version":"ontokin.c087-actual-supplied-byte-observations/0.1","status":"running",
        **input_lineage(fixtures),"started_utc":datetime.now(timezone.utc).isoformat(),
        "candidate_git":{"commit":git("rev-parse","HEAD"),"tree":git("rev-parse","HEAD^{tree}"),"status":git("status","--porcelain")},
        "source_summary_sha256":sha((args.sources/"summary.json").read_bytes()),
        "producer_sha256":sha(Path(__file__).read_bytes()),"positive_controls":[],"hostile_controls":[],
        "failures":[],"independent_acceptance":"separate reader required","release_acceptance":False}
    output.mkdir();(output/"mutations").mkdir()
    def save():
        (output/"production-observations.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    def validate(raw,case):
        source=load_texture_file_manifest(fixtures["agent_root"]/case["file_manifest"])
        ledger=SharedExecutionBudget(policy=HostPolicy(**case["host_policy"]))
        admit_entry_budget(source.entry,ledger,profile=PROFILE)
        compiler=compile_construction(source,level="evaluated",execution_budget=ledger)
        try:
            result=validate_export(raw,compiler.model,options=ExportOptions(fps=4,end="1",helpers=False),
                                   target_contract=TARGET,work=ReachExecutionWork(execution_budget=ledger))
            return {"accepted":True,"report":result,"execution_budget":ledger.report(status="valid")}
        except Exception as error:
            record={"accepted":False,"exception_type":type(error).__name__,"message":str(error),
                    "traceback":traceback.format_exc(),"execution_budget":ledger.report(status="refused")}
            diagnostic=getattr(error,"diagnostic",None)
            if diagnostic is not None:
                record["diagnostic"]={"code":diagnostic.code,"category":diagnostic.category,"phase":diagnostic.phase,
                    "message":diagnostic.message,"details":diagnostic.details}
            return record
    try:
        for name in fixtures["adversaries"]["source_cases"]:
            case=fixtures["agent_cases"][name];record=records[name]
            raw=(args.sources/record["glb"]).read_bytes()
            assert sha(raw)==record["sha256"] and len(raw)==record["bytes"]
            positive={"case":name,"sha256":sha(raw),"bytes":len(raw),"observation":validate(raw,case)}
            report["positive_controls"].append(positive)
            if not positive["observation"]["accepted"]:report["failures"].append({"scope":"positive","case":name})
            for mutation in build_mutations(raw,case,fixtures=fixtures):
                changed=mutation.pop("data");mutation["path"]="mutations/"+name+"-"+mutation["id"]+".glb"
                (output/mutation["path"]).write_bytes(changed)
                mutation["observation"]=validate(changed,case)
                if mutation["observation"]["accepted"]:report["failures"].append({"scope":"hostile","case":name,"id":mutation["id"],"reason":"unexpected acceptance"})
                report["hostile_controls"].append(mutation);save()
            print(json.dumps({"case":name,"completed":len(report["hostile_controls"])}),flush=True)
        report["status"]="failed" if report["failures"] else "observed_as_expected"
    except Exception as error:
        report["status"]="failed";report["failures"].append({"reason":str(error),"traceback":traceback.format_exc()})
    report["finished_utc"]=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps({"status":report["status"],"positive":len(report["positive_controls"]),"hostile":len(report["hostile_controls"])}))
    return 0 if report["status"]=="observed_as_expected" else 1


if __name__=="__main__":raise SystemExit(main())
