#!/usr/bin/env python3
"""Read-only audit of frozen C268 controls and candidate evidence."""
from pathlib import Path, PurePosixPath
import hashlib, json, zipfile, collections, subprocess, sys

repo = Path("/workspace/scratch/c7dae94da130/validate-candidate")
author = repo / "docs/engineering/localized-repair-c268/evidence/control-author"
cohort = Path("/workspace/scratch/c7dae94da130/evidence/candidate")
out = Path("/workspace/scratch/c7dae94da130/OntoKin/docs/engineering/localized-repair-c268/evidence/review/EVIDENCE-AUDIT.json")
def ident(raw): return {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def same(raw, row): return ident(raw) == {k:row[k] for k in ("bytes","sha256")}
def walk(value):
    if isinstance(value,dict):
        yield value
        for v in value.values(): yield from walk(v)
    elif isinstance(value,list):
        for v in value: yield from walk(v)
def audit_controls(folder):
    v=json.loads((folder/"results.json").read_text())
    inp = v["implementationAndControlInputs"]
    current_bad=[p for p,t in inp.items() if not same((repo/p).read_bytes(),t)]
    snapshots=[]
    for p in (folder/"checked-code").iterdir():
        source="docs/engineering/localized-repair-c268/"+p.name
        snapshots.append({"path":p.name,"matches_recorded":same(p.read_bytes(),inp[source])})
    counts=collections.Counter(x.get("outcome") for x in v["cases"])
    api=collections.Counter(x.get("api") for x in v["cases"])
    mismatches=[]
    expected={"admitted":"admitted","accepted":"raw_success","typed_refusal":"typed_refusal"}
    for i,x in enumerate(v["cases"]):
        if expected.get(x["expected"]) != x.get("outcome"): mismatches.append({"case_index":i,"expected":x["expected"],"observed":x.get("outcome")})
    witnesses=collections.Counter()
    failures=[]
    with zipfile.ZipFile(folder/"inputs.zip") as z:
        names=z.namelist()
        zip_status={"identity":ident((folder/"inputs.zip").read_bytes()),"members":len(names),"crc_failure":z.testzip(),
                    "unique_names":len(names)==len(set(names)),
                    "safe_paths":all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts and "\\" not in n for n in names),
                    "content_names_match":all(Path(n).stem==hashlib.sha256(z.read(n)).hexdigest() for n in names)}
        for t in walk(v["cases"]):
            if not {"bytes","sha256"} <= set(t): continue
            if "snapshot" in t:
                witnesses["archived"]+=1
                name=t["snapshot"].split("inputs.zip!",1)[1]
                if not same(z.read(name),t):failures.append({"kind":"archived","name":name})
            elif "frozenReference" in t:
                witnesses["frozen"]+=1
                if not same((repo/t["frozenReference"]).read_bytes(),t):failures.append({"kind":"frozen","name":t["frozenReference"]})
            elif t.get("recipe","").startswith("sparse file consisting entirely of zero bytes"):
                witnesses["sparse_recipe"]+=1
                h=hashlib.sha256();left=t["bytes"]
                while left:
                    n=min(left,65536);h.update(bytes(n));left-=n
                if h.hexdigest()!=t["sha256"]:failures.append({"kind":"sparse_recipe"})
            else:
                witnesses["code_or_other_identity"]+=1
                if not any(t["bytes"]==row["bytes"] and t["sha256"]==row["sha256"] for row in inp.values()):
                    failures.append({"kind":"unresolved_identity","identity":t})
    current_identity_ok=not current_bad
    return {"folder":str(folder),"results_identity":ident((folder/"results.json").read_bytes()),
            "methods":v["testMethods"],"passed":v["passed"],"failures":len(v["failures"]),"errors":len(v["errors"]),"skips":len(v["skipped"]),
            "implementation_and_control_input_count":len(inp),"input_code_stable":v["inputCodeStableDuringRun"],
            "current_input_differences":current_bad,"snapshots":snapshots,
            "api_calls":len(v["cases"]),"outcomes":dict(counts),"apis":dict(api),
            "count_fields_match":v["apiCalls"]==len(v["cases"]) and v["historicalCalls"]==api["historical-reader"]
                 and v["rawCalls"]==len(v["cases"])-api["historical-reader"]
                 and v["admittedCalls"]==counts["admitted"] and v["rawSuccessfulCalls"]==counts["raw_success"]
                 and v["typedRefusals"]==counts["typed_refusal"],
            "expected_outcome_mismatches":mismatches,"witnesses":dict(witnesses),"witness_failures":failures,"archive":zip_status,
            "permission_notes":v["notes"],"error_types":dict(collections.Counter(x["traceback"].strip().splitlines()[-1] for x in v["errors"])),
            "reader_identity":inp["docs/engineering/localized-repair-c268/endpoint_reader.py"]}

checks=json.loads((cohort/"CHECKS.json").read_text())
before=checks["input_files_before"]
input_bad=[r["path"] for r in before if not same((repo/r["path"]).read_bytes(),r)]
output_bad=[r["path"] for r in checks["output_files"] if not same((cohort/r["path"]).read_bytes(),r)]
historical_glbs=[r for r in before if r["path"].endswith(("/before.glb","/after.glb"))]
record={"schema":"ontokin.c268.review-evidence-audit/1","reviewer":"/root/state_audit",
        "candidate":"734789521f82248d39b623c33aae9d3284ab4bce",
        "candidate_tree":"23aa5e900cede54b9ff2ff7b14cbfb2e440547d0",
        "author_runs":{name:audit_controls(author/name) for name in ("run-01","run-02","run-03")},
        "candidate_controls":audit_controls(cohort/"c268-controls"),
        "cohort":{"receipt_identity":ident((cohort/"CHECKS.json").read_bytes()),
                  "source_before":checks["source_before"],"source_after":checks["source_after"],
                  "passed":checks["passed"],"complete":checks["complete"],
                  "groups":checks["completed_check_count"],"methods":checks["total_methods"],
                  "all_groups_pass":all(c["result"]=="passed" and c["exit_code"]==0 and all(c["assertions"].values()) for c in checks["checks"]),
                  "input_count":len(before),"input_identity_failures":input_bad,
                  "before_after_inventory_equal":before==checks["input_files_after"],
                  "output_count":len(checks["output_files"]),"output_identity_failures":output_bad,
                  "both_historical_glbs_explicitly_bound":len(historical_glbs)==2,
                  "historical_glbs":historical_glbs,"runner":checks["runner"],"environment":checks["environment"],
                  "not_run":checks["not_run"]}}
record["passed_current_evidence_audit"]=(
    not input_bad and not output_bad and len(historical_glbs)==2
    and record["cohort"]["all_groups_pass"] and checks["passed"] and checks["complete"]
    and checks["total_methods"]==281 and checks["completed_check_count"]==12
    and all(not record[k]["current_input_differences"] and not record[k]["witness_failures"]
            and not record[k]["expected_outcome_mismatches"] and record[k]["count_fields_match"]
            for k in ("candidate_controls",))
    and not record["author_runs"]["run-03"]["current_input_differences"]
    and not record["author_runs"]["run-03"]["witness_failures"]
    and not record["author_runs"]["run-03"]["expected_outcome_mismatches"])
out.write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({"passed":record["passed_current_evidence_audit"],"cohort":{k:record["cohort"][k] for k in
    ("groups","methods","input_count","input_identity_failures","output_count","output_identity_failures","both_historical_glbs_explicitly_bound")},
    "controls":{n:{"calls":v["api_calls"],"outcomes":v["outcomes"],"witnesses":v["witnesses"],"witness_failures":v["witness_failures"],
                   "changed_current_inputs":v["current_input_differences"],"error_types":v["error_types"]} for n,v in record["author_runs"].items()},
    "candidate_control_witnesses":record["candidate_controls"]["witnesses"],"output":str(out)},indent=2))

