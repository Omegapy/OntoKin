#!/usr/bin/env python3
"""Verify C053 source/document identities and claims; never import OntoKin."""
from pathlib import Path
import hashlib, json, sys

ROOT=Path(__file__).resolve().parents[4]
EV=ROOT/"docs/engineering/reach-recording-validation-2026-10-23"
HERE=Path(__file__).resolve().parent
PARENT="853c01589af790bc83bf52ed70b18dc87673873b"
PREFIX=EV.relative_to(ROOT).as_posix()+"/"
errors=[]
checks=[]
def check(name,ok,detail=None):
    checks.append({"name":name,"passed":bool(ok),"detail":detail})
    if not ok: errors.append(name)
def obj(p): return json.loads(p.read_text())
def fileinfo(p):
    b=p.read_bytes()
    return {"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),
            "git_blob":hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()}
def matches(record):
    p=ROOT/record["path"]
    if not p.is_file():return False
    f=fileinfo(p)
    return f["sha256"]==record["sha256"] and f["bytes"]==record["bytes"]

inventory=obj(HERE/"recovered-inputs.json")
base=inventory["files"]+obj(HERE/"documentation-recovery.json")["files"]
bad=[]
for x in base:
    p=ROOT/x["path"]
    if not p.is_file():bad.append(x["path"]);continue
    f=fileinfo(p)
    expected=x.get("git_blob_sha",x.get("git_blob",x.get("sha")))
    if f["bytes"]!=x["bytes"] or f["sha256"]!=x["sha256"] or (expected and f["git_blob"]!=expected):bad.append(x["path"])
check("949 reviewed inputs and five recovered documentation dependencies unchanged",len(base)==954 and not bad,bad)
basepaths={x["path"] for x in base}
newpaths=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in basepaths]
unexpected=[x for x in newpaths if not (x.startswith(PREFIX+"checkpoint-053") or x==PREFIX+"HANDOFF-053.md")]
check("only owned C053 additions",not unexpected,unexpected)
held=obj(HERE/"held-runtime-binding.json")
check("all65 runtime modules match fresh held C035",held["files"]==65 and held["same_paths"] and not held["differences"])
attached=obj(HERE/"attachment-audit.json")
check("five uploaded C052 files match published copies",len(attached["files"])==5 and attached["all_match"])
schedule=obj(EV/"checkpoint-053-schedule.json")
ledger=obj(EV/"checkpoint-053-cost-ledger.json")
nextscope=obj(EV/"checkpoint-053-next-scope.json")
check("source identity and S1 linkage",schedule["source_commit"]==PARENT and ledger["source_commit"]==PARENT and ledger["schedule"]==schedule["id"])
g=ledger["gross"]
check("source cost arithmetic, not a numerical runtime replay",sum(x[1] for x in ledger["cold_pi_components"])==165 and g["difference"]==165-1 and g["one_convergent_publication_before_other_work"]==164-1 and ledger["scan_bound"]["full256_ceiling"]==163-256 and ledger["checkpoint_replay"]["ceiling_before_other"]==-1)
check("no measured whole-request saving or implementation selected",all(ledger["whole_request"][x] is None for x in ["H","Q","A_nonpublication","Delta_remaining","complete_net","recording_pass_prediction"]) and "NO-GO" in ledger["outcome"] and "no implementation" in ledger["outcome"])
check("next scope preserves source-only boundary",nextscope["next_checkpoint"]=="C054" and nextscope["release"]["full_product_goal_completed"] is False and "no implementation" in nextscope["status"] and any("No numerical execution" in x for x in nextscope["exclusions"]))
review_errors=[]
for role in ("authority","cost","evidence"):
    p=EV/"checkpoint-053-reviews"/role/"final-draft-review.json"
    if not p.is_file():review_errors.append(role+":missing");continue
    d=obj(p); records=d.get("final_draft_bindings",d.get("files",[]))
    if len(records)!=5 or not all(matches(x) for x in records):review_errors.append(role+":binding")
    for k in ("unresolved_findings","blocking_findings","corrections_required","open_findings"):
        if d.get(k):review_errors.append(role+":"+k)
check("three independent final audits bind five current core files",not review_errors,review_errors)
json_bad=[]
for p in EV.rglob("*.json"):
    rel=p.relative_to(ROOT).as_posix()
    if rel in basepaths:continue
    try:obj(p)
    except (ValueError,UnicodeError) as e:json_bad.append({"path":rel,"error":str(e)})
check("all existing new JSON files parse",not json_bad,json_bad)
original_checker=ROOT/"docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"
check("unchanged documentation checker",fileinfo(original_checker)["git_blob"]=="25e4c5a224cbe15bbeba9a7e35301de4368d3de7")
result={"schema":"ontokin.checkpoint053-metadata-result/0.1","source_parent_commit":PARENT,
        "status":"passed" if not errors else "failed","grouped_checks":len(checks),
        "checks":checks,"failures":errors,"recovered_base_files":len(base),
        "new_files_at_check":len(newpaths),"runtime_imports":0,"runtime_tests":0,
        "numerical_replays":0,"qualification":"Metadata and source-document consistency only, not runtime behavior or publication."}
print(json.dumps(result,indent=2))
raise SystemExit(bool(errors))
