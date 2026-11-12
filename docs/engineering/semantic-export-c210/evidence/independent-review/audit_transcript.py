"""Check saved actual Agent exchanges against the independently retained bytes."""
import argparse
import hashlib
import json
from pathlib import Path

def digest(data):
    return "sha256:"+hashlib.sha256(data).hexdigest()

def run(proof_dir,output):
    proof=json.loads((proof_dir/"proof.json").read_text())
    workflow=json.loads((proof_dir/"workflow.json").read_text())
    exchanges=workflow["exchanges"];checks=[]
    def check(name,ok,**observed):
        checks.append({"name":name,"passed":bool(ok),"observed":observed})
    artifacts={}
    for phase in ("before","after"):
        data=(proof_dir/(phase+".glb")).read_bytes()
        identity=digest(data)
        artifacts["artifact:"+identity.removeprefix("sha256:")]=(data,proof[phase+"_program_revision"])
        check(phase+" proof artifact hash",proof[phase+"_artifact_sha256"]==identity)
    chunks=0
    for row in exchanges:
        request,response=row["request"],row["response_summary"]
        if request["operation"]!="artifact":
            continue
        chunks+=1
        data,revision=artifacts[request["artifact_id"]]
        result=response["result"];chunk=result["omitted_artifact_chunk"];offset=request["offset"]
        observed=data[offset:offset+chunk["bytes"]]
        check("actual artifact chunk "+str(chunks),response["status"]=="succeeded" and result["program_revision"]==revision and result["offset"]==offset and chunk["sha256"]==digest(observed) and len(observed)==chunk["bytes"],project=request["project_id"],offset=offset,bytes=chunk["bytes"])
    check("all 12 retained chunks audited",chunks==12)
    edits=[row for row in exchanges if row["request"]["operation"]=="edit"]
    invalid=[row for row in edits if row["request"]["patches"][0]["replacement"]=="0.75[kg]"]
    accepted=[row for row in edits if row["request"]["patches"][0]["replacement"]=="0.75[m]"]
    check("invalid edit has exact retry and preserved accepted revision",len(invalid)==2 and invalid[0]==invalid[1] and all(row["response_summary"]["status"]=="rejected" and row["response_summary"]["accepted_program_revision"]==proof["before_program_revision"] for row in invalid))
    check("accepted edit has exact retry and accepted after revision",len(accepted)==2 and accepted[0]==accepted[1] and all(row["response_summary"]["status"]=="succeeded" and row["response_summary"]["accepted_program_revision"]==proof["after_program_revision"] for row in accepted))
    invalid_source=(proof_dir/"rejected-candidate.ok").read_bytes()
    diagnostic=next(row for row in invalid[0]["response_summary"]["diagnostics"] if row["code"]=="OKL-E-UNIT")
    primary=diagnostic["primary"]
    check("invalid candidate diagnostic names actual rejected bytes",diagnostic["source_revision"]==digest(invalid_source) and invalid_source[primary["start_byte"]:primary["end_byte"]]==b"0.75[kg]" and primary["source_id"]=="entry")
    others=[row for row in edits if row not in invalid and row not in accepted]
    check("changed-payload request and stale-revision request reject",len(others)==2 and all(row["response_summary"]["status"]=="rejected" for row in others) and any(row["response_summary"].get("protocol_error") for row in others) and any(row["response_summary"].get("accepted_program_revision")==proof["after_program_revision"] for row in others))
    clean=[row for row in exchanges if row["request"]["project_id"]=="clean-regeneration" and row["request"]["operation"]=="create"]
    check("fresh store accepted full source at delivered level",len(clean)==1 and clean[0]["request"]["expected_program_revision"] is None and clean[0]["request"]["requested_level"]=="delivered" and clean[0]["response_summary"]["status"]=="succeeded" and clean[0]["response_summary"]["program_revision"]==proof["after_program_revision"])
    check("regeneration digest equals delivered after bytes",proof["regeneration"]["glb_sha256"]==proof["after_artifact_sha256"])
    report={"schema_version":"ontokin.c210-transcript-review/0.1","status":"passed" if all(c["passed"] for c in checks) else "failed","implementation_commit":proof["implementation_commit"],"exchanges":len(exchanges),"summary":{"checks":len(checks),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks)},"checks":checks,"inputs":{name:digest((proof_dir/name).read_bytes()) for name in ("proof.json","workflow.json","before.glb","after.glb","rejected-candidate.ok")},"limit":"Audit of retained real workflow evidence and exact bytes; service implementation tests and execution evidence remain separate."}
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"summary":report["summary"],"output":str(output)}))
    return int(report["status"]!="passed")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--proof",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();raise SystemExit(run(args.proof,args.output))

