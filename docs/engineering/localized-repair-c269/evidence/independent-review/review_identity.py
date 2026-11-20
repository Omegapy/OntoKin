"""Independent static review of C269 reuse eligibility; never imports observer code."""
from pathlib import Path, PurePosixPath
import ast
import datetime as dt
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
BASE = "23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb"
ORIGINAL = "5084dd69312e8da5a49aadd33cf83ba56db7c058"
RECEIPT = "docs/engineering/localized-repair-c268/evidence/finalization-a3de3dd23bbf/main-integration/CHECKS.json"
ELIGIBLE = "docs/engineering/localized-repair-c269/evidence/EXECUTION-ELIGIBILITY.json"
RUNNER = "docs/engineering/localized-repair-c268/evidence/run_checks.py"
env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
started = dt.datetime.now(dt.timezone.utc).isoformat()
checks = []
def check(name, result):
    checks.append({"name":name,"passed":bool(result)})
    if not result:
        raise AssertionError(name)
def ident(b):
    return {"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
def git(*args):
    return subprocess.check_output(["git","--no-optional-locks",*args],cwd=ROOT,env=env)
def git_blobs(specs):
    specs=list(dict.fromkeys(specs))
    raw=subprocess.check_output(["git","--no-optional-locks","cat-file","--batch"],cwd=ROOT,env=env,input=("\n".join(specs)+"\n").encode())
    result={}; pos=0
    for spec in specs:
        end=raw.index(b"\n",pos); header=raw[pos:end].decode().split(); pos=end+1
        check("blob available: "+spec,len(header)==3 and header[1]=="blob")
        size=int(header[2]);result[spec]=raw[pos:pos+size];pos+=size
        check("blob framing: "+spec,raw[pos:pos+1]==b"\n");pos+=1
    check("batch exhausted",pos==len(raw))
    return result
try:
    original_bytes=git("show",BASE+":"+RECEIPT)
    original=json.loads(original_bytes)
    eligible_bytes=(ROOT/ELIGIBLE).read_bytes()
    eligible=json.loads(eligible_bytes)
    parent=PurePosixPath(RECEIPT).parent
    input_paths=[x["path"] for x in original["input_files_before"]]
    output_paths=[str(parent/x["path"]) for x in original["output_files"]]
    check("159 unique original inputs",len(input_paths)==len(set(input_paths))==159)
    check("30 unique original outputs",len(output_paths)==len(set(output_paths))==30)
    blob_specs=[r+":"+p for r in (ORIGINAL,BASE) for p in input_paths]
    blob_specs += [BASE+":"+p for p in output_paths]
    blob_specs += [ORIGINAL+":"+RUNNER,BASE+":"+RUNNER]
    blobs=git_blobs(blob_specs)
    check("original source commit",original["source_before"]["commit"]==ORIGINAL)
    check("original source before equals after",original["source_before"]==original["source_after"])
    check("original source clean",original["source_before"]["all_dirty_status"]==original["source_before"]["tracked_dirty_status"]=="")
    check("original source tree",git("rev-parse",ORIGINAL+"^{tree}").decode().strip()==original["source_before"]["tree"])
    check("original inputs before equal after",original["input_files_before"]==original["input_files_after"])
    check("original run complete",original["complete"] is True and original["passed"] is True and original["input_identity_unchanged"] is True and original["remaining_checks"]==[])
    check("eligibility execution attribution",eligible["original_execution_revision"]==ORIGINAL and eligible["audit_baseline_revision"]==BASE and eligible["new_behavioral_execution"] is False)
    check("eligibility receipt identity",eligible["receipt"]=={"path":RECEIPT,**ident(original_bytes)})
    check("eligibility exact input row inventory",[x["path"] for x in eligible["source_inputs"]]==input_paths)
    changes=[]
    for item,row in zip(original["input_files_before"],eligible["source_inputs"]):
        p=item["path"]
        old=ident(blobs[ORIGINAL+":"+p]);new=ident(blobs[BASE+":"+p])
        expected={"path":p,"execution_revision":ORIGINAL,"original":old,"audit_baseline_revision":BASE,"audit_baseline":new,"unchanged":old==new}
        check("original input receipt: "+p,old=={k:item[k] for k in ("bytes","sha256")})
        check("eligibility input row: "+p,row==expected)
        if old!=new:changes.append(expected)
    expected_delta_paths={
      "STATUS.md","docs/engineering/localized-repair-c268/README.md",
      "docs/engineering/localized-repair-c268/RESULTS.md","docs/workflow/CURRENT.json",
      "docs/workflow/knowledge.json","docs/workflow/tasks/C268/PLAN.md","docs/workflow/tasks/C268/task.json"}
    check("seven declared state/document deltas",{x["path"] for x in changes}==expected_delta_paths and len(changes)==7)
    check("eligibility exact delta rows",eligible["changed_documentation_records"]==changes)
    check("152 unchanged original inputs",sum(x["unchanged"] for x in eligible["source_inputs"])==152)
    observed_outputs=[]
    for item,path in zip(original["output_files"],output_paths):
        actual=ident(blobs[BASE+":"+path])
        check("original output receipt: "+path,actual=={k:item[k] for k in ("bytes","sha256")})
        observed_outputs.append({"path":path,**actual,"revision":BASE})
    check("eligibility exact outputs",eligible["outputs"]==observed_outputs)
    check("runner identity at execution",ident(blobs[ORIGINAL+":"+RUNNER])=={k:original["runner"][k] for k in ("bytes","sha256")})
    check("runner unchanged at baseline",blobs[ORIGINAL+":"+RUNNER]==blobs[BASE+":"+RUNNER])
    check("runner unchanged in working copy",(ROOT/RUNNER).read_bytes()==blobs[BASE+":"+RUNNER])
    check("historical environment copied exactly",eligible["historical_environment"]==original["environment"])
    test_counts=[]
    expected_eligibility_checks=[]
    for planned,run in zip(original["planned_checks"],original["checks"]):
        check("planned command: "+run["name"],planned["name"]==run["name"] and planned["command"]==run["command"] and planned["expected_methods"]==run["expected_methods"])
        check("passed strict assertions: "+run["name"],run["result"]=="passed" and run["exit_code"]==0 and run["failure"] is None and all(type(v) is bool and v for v in run["assertions"].values()))
        log=blobs[BASE+":"+str(parent/run["log"]["path"])].decode()
        check("log receipt: "+run["name"],ident(log.encode())=={k:run["log"][k] for k in ("bytes","sha256")})
        expected_eligibility_checks.append({k:run[k] for k in ("name","command","methods","result","assertions","log")})
        if run["methods"] is not None:
            command=run["command"]
            if "discover" in command:
                path=str(PurePosixPath(command[command.index("-s")+1])/command[command.index("-p")+1])
            else:
                path=command[2]
            tree=ast.parse(blobs[ORIGINAL+":"+path])
            authored={(c.name,n.name) for c in ast.walk(tree) if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith("test_")}
            matches=re.findall(r"^(test_\w+) \(([^\n]+)\) \.\.\. (.+)$",log,re.MULTILINE)
            observed=[(qual.split(".")[-2],name) for name,qual,outcome in matches]
            check("authored methods match successful log: "+run["name"],len(matches)==len(observed)==len(set(observed))==run["methods"]==run["expected_methods"] and set(observed)==authored and all(o=="ok" for _,_,o in matches))
            check("method summary: "+run["name"],re.search(r"^Ran "+str(run["methods"])+r" tests in ",log,re.MULTILINE) is not None and re.search(r"^OK$",log,re.MULTILINE) is not None)
            test_counts.append({"group":run["name"],"test_path":path,"methods":len(authored),"log_path":str(parent/run["log"]["path"]),"outcome":"all authored methods recorded as ok"})
    check("12 planned and completed groups",len(original["planned_checks"])==len(original["checks"])==original["planned_check_count"]==original["completed_check_count"]==12)
    check("nine test groups and 282 methods",len(test_counts)==9 and sum(x["methods"] for x in test_counts)==original["total_methods"]==original["expected_total_methods"]==282)
    check("eligibility exact check summaries",eligible["checks"]==expected_eligibility_checks)
    corpus=json.loads(blobs[BASE+":"+str(parent/"c253-corpus.log")])
    check("corpus 14 bindings across three tasks",corpus["passed"] is True and corpus["boundFiles"]==14 and corpus["tasks"]==3 and corpus["productStarts"]==corpus["nativeStarts"]==corpus["modelTrials"]==0)
    pins=json.loads(blobs[BASE+":docs/engineering/localized-repair-c260/INPUTS.json"])
    for p in pins["files"]:
        check("C260 declared pin: "+p["path"],ident(blobs[BASE+":"+p["path"]])=={k:p[k] for k in ("bytes","sha256")})
    current_environment={
      "python":sys.version,"platform":platform.platform(),
      "runtime_bundle_version":os.environ.get("CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION"),
      "resolved_executable":{"path":str(Path(sys.executable).resolve()),**ident(Path(sys.executable).resolve().read_bytes())},
      "dont_write_bytecode":sys.dont_write_bytecode}
    old_environment=original["environment"]
    environment_comparison={
      "python":current_environment["python"]==old_environment["python"],
      "platform":current_environment["platform"]==old_environment["platform"],
      "runtime_bundle_version":current_environment["runtime_bundle_version"]==old_environment["runtime_bundle_version"],
      "interpreter_bytes":{k:current_environment["resolved_executable"][k] for k in ("bytes","sha256")}=={k:old_environment["resolved_executable"][k] for k in ("bytes","sha256")}}
    read_paths=[
      "docs/workflow/tasks/C269/REQUIREMENTS.md","docs/workflow/tasks/C269/PLAN.md",
      "docs/engineering/localized-repair-c260/CONTRACT.md","docs/engineering/localized-repair-c260/CONTROL-PLAN.md","docs/engineering/localized-repair-c260/INPUTS.json",
      "docs/engineering/localized-repair-c269/evidence/audit_identity.py",ELIGIBLE]
    read_set={p:ident((ROOT/p).read_bytes()) for p in read_paths}
    check("eligibility file remained stable",(ROOT/ELIGIBLE).read_bytes()==eligible_bytes)
    result={
      "schema":"ontokin.c269.independent-identity-readiness/1","reviewer":"/root/state_audit",
      "started_at_utc":started,"finished_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "verdict":"eligible_as_historical_execution_evidence_for_coverage_audit",
      "final_acceptance":False,"mandatory_identity_findings":[],
      "original_execution_revision":ORIGINAL,"audit_baseline_revision":BASE,
      "supplied_scope_publication":{"commit":"5e193e831e74483bccca67ea6cf8a1b8cec47491","tree":"cb1d3758bbd500fa65fca2fce49746c886bb3535","attribution":"Director supplied; this preparation does not repeat remote publication validation"},
      "inspection_command":[sys.executable,"-B",str(Path(__file__).resolve())],
      "read_set":read_set,"historical_receipt":{"path":RECEIPT,**ident(original_bytes)},
      "source_input_count":159,"unchanged_input_count":152,"changed_documentation_records":changes,
      "output_identity_count":30,"original_groups":12,"original_methods":282,"original_bindings":14,
      "log_method_matching":test_counts,"historical_runner":{"path":RUNNER,**ident(blobs[ORIGINAL+":"+RUNNER]),"unchanged_at_baseline_and_working_copy":True},
      "historical_environment":old_environment,"current_inspection_environment":current_environment,"environment_comparison":environment_comparison,
      "new_behavioral_execution":False,"assertion_count":len(checks),"checks":checks,
      "review_limits":[
        "This accepts provenance and eligibility of already recorded execution only; it does not qualify any H group.",
        "The seven deltas are reviewed C268 documentation/state transitions; historical documentation/workflow passes do not qualify C269 documents.",
        "H-map authorship is ongoing and no immutable audit candidate was supplied.",
        "Final H-map review must inspect independent expected-value construction, actual assertions, changed-input provenance and subcase outcomes.",
        "No observer module was imported, no behavior was run, no Git index/ref/commit or remote writes occurred."],
      "final_acceptance_conditions":[
        "An immutable candidate commit/tree and changed-file manifest identify the exact audit payload.",
        "R01 binds all claimed source/control/log/ledger evidence and unchanged contract/input identities.",
        "All H01-H28 material subcases map to inspected independent assertions and exact recorded outcomes; partial, absent and contradictory evidence stays explicit.",
        "No missing material subcase is promoted by a test name, method count, broad label or inherited pass.",
        "The decision and one proposed next bounded control match the evidence; no product/contract expansion or new control implementation occurs.",
        "Fresh workflow/documentation checks and evidence-reference/hash checks identify the candidate; historical outcomes retain original execution attribution.",
        "Any mandatory final-review finding is corrected and re-reviewed; integration and saved-delivery gates remain subsequent Director actions."
      ]
    }
    (OUT/"READINESS.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("verdict","mandatory_identity_findings","source_input_count","unchanged_input_count","output_identity_count","original_groups","original_methods","original_bindings","assertion_count","environment_comparison","final_acceptance")},indent=2))
except BaseException as exc:
    fail={"schema":"ontokin.c269.independent-identity-attempt/1","started_at_utc":started,"failed_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"type":type(exc).__name__,"error":str(exc),"checks":checks,"traceback":traceback.format_exc(),"behavioral_execution":False}
    (OUT/"IDENTITY-ATTEMPT-01.json").write_text(json.dumps(fail,indent=2)+"\n")
    raise

