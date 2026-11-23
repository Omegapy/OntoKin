"""Read-only audit of supplied C271 state; writes only the adjacent audit result."""
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
inputs = {}

def raw(path):
    p = ROOT / path
    data = p.read_bytes()
    inputs[path] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return data

def read(path):
    return json.loads(raw(path))

def payload(path, key=None):
    data = read(path)["structuredContent"]
    return data[key] if key else json.loads(data["content"])

checks = []
def check(name, condition, details=None):
    checks.append({"name": name, "passed": bool(condition), "details": details})

for name in ["AGENTS.md", "GOAL.md", "ROLE.md", "CHATGPT-START-HERE.md",
             "STATUS.md", "docs/workflow/PROTOCOL.md", "docs/workflow/HANDOFF.md",
             "docs/workflow/EPHEMERAL-HOST.md"]:
    raw("governing-main/" + name)
for name in ["ontokin-session", "ontokin-delivery", "ontokin-learning"]:
    raw(f"governing-main/.agents/skills/{name}/SKILL.md")
for name in ["REQUIREMENTS.md", "PLAN.md"]:
    raw(f"branch-snapshot/docs/workflow/tasks/C271/{name}")
task = read("branch-snapshot/docs/workflow/tasks/C271/task.json")
current = read("branch-snapshot/docs/workflow/CURRENT.json")
early = read("incoming/p28-early/CHECKPOINT.json")
for name in ["HANDOFF.md", "NEXT-TASK.md", "RECOVERY-STATUS.md"]:
    raw("incoming/p28-early/" + name)
branch = payload("records/live/ref.json")["object"]["sha"]
main = payload("records/live/mainref.json")["object"]["sha"]
branches = payload("records/live/branches.json")
issue = payload("records/live/issue.json", "issue")
pulls = payload("records/live/pulls.json")
pr = next(p for p in pulls if p["number"] == 274)
ic = payload("records/live/issueComments.json", "comments")
pc = payload("records/live/prComments.json", "comments")
by_id = {c["id"]: c for c in ic + pc}
p27_body = by_id[7110046284]["body"]
p28_body = by_id[7111339840]["body"]

check("live branch and main identities", branch == "360c80062e769230199602326fa8de25660df714" and main == "e43cc6c5777874101a40559e4058ad6826b07e51")
check("branch list agrees", {p["name"]: p["commit"]["sha"] for p in branches}.get("work/c271-missing-import-digest-control") == branch)
check("PR is open draft and unmerged", pr["state"] == "open" and pr["draft"] and pr["merged_at"] is None and pr["head"]["sha"] == branch)
check("scope issue remains open", issue["state"] == "open")
check("all five supplied scope comments counted", issue.get("comments") == len(ic) == 5)
check("P27 terminal pair exact", p27_body == by_id[7110052122]["body"])
check("P28 start pair exact", p28_body == by_id[7111340439]["body"])
check("P28 owner recorded", "c271-p28-4b91a1fab6b4" in p28_body)
check("C271 requirement states unchanged", {x["id"]: x["status"] for x in task["requirements"]} == {"R01":"done","R02":"done","R03":"not_done","R04":"not_done","R05":"not_done"})
check("parent task and plan remain incomplete", task["status"] == "blocked" and {p["id"]:p["status"] for p in task["plan"]} == {"P01":"done", "P02":"in_progress"})
check("current pointer remains C271", current["active_task"] == current["latest_task"] == "C271")
check("P28 package is startup snapshot", early["status"] == "startup_early_save_pending" and early["phase_complete"] is False and early["source_commit"] == branch)
check("P28 early checkpoint explicitly precedes control execution", "has not edited product code or executed controls" in (ROOT / "incoming/p28-early/HANDOFF.md").read_text())
check("P28 no main lease at start", early["main_lease_held"] is False and "No main lease" in p28_body)

p27zip = "incoming/OntoKin_C271_P27_Required_Image_Design_Handoff_2026-11-23.zip"
p28zip = "incoming/OntoKin_C271_P28_Required_Images_Early_Recovery_2026-11-23.zip"
receipt_path = "incoming/p28-early/predecessor/OntoKin_C271_P27_Delivery_Receipt_2026-11-23.json"
for p in [p27zip, p28zip]:
    raw(p)
receipt = read(receipt_path)
check("P27 ZIP exact terminal identity", inputs[p27zip] == {"bytes":7397736,"sha256":"d9fdae71a39f343b1fa14a6eb358f780428a1d05af66e85bd9e4c191abe82a77"} and inputs[p27zip]["sha256"] in p27_body)
check("P27 external receipt exact terminal identity", inputs[receipt_path] == {"bytes":2872533,"sha256":"614a765b48e90efd1de9b3f5ae102bdf838c834fa8ebcdbc0581baef676c8783"} and inputs[receipt_path]["sha256"] in p27_body)
check("P27 receipt source A/B bind branch", receipt["source_a"]["commit"] == "105ac7c5f247fc1a01c1073266763f16e6587757" and receipt["receipt_b"]["commit"] == branch)
check("P28 early ZIP exact start-marker identity", inputs[p28zip] == {"bytes":8480098,"sha256":"520b24277f2f4a28b5ed96122a477b2438a60905c1a1ae80de39d448426cb15e"} and inputs[p28zip]["sha256"] in p28_body)
check("P27 declarative controls remain unrun at predecessor boundary", receipt["control_obligations"] == {"count":116,"execution":"NOT_RUN","fixture_bytes_frozen":False})

saved_agent_bindings = {}
for p in ["incoming/p27/SOURCE-MANIFEST.json", "incoming/p28-early/SOURCE-MANIFEST.json"]:
    rows = read(p)
    saved_agent_bindings[p] = [r for r in rows if r["git_path"].endswith("AGENTS.md")]
repo = ROOT / "repository"
commands = []
def git(*args):
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    commands.append({"command":["git",*args],"exit_code":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout
head = git("rev-parse", "HEAD").strip()
tree_paths = git("ls-tree", "-r", "--name-only", branch).splitlines()
agent_paths = [p for p in tree_paths if p == "AGENTS.md" or p.endswith("/AGENTS.md")]
check("current-host checkout matches observed branch", head == branch)
check("complete exact branch tree contains no nested AGENTS", agent_paths == ["AGENTS.md"])
raw("repository/AGENTS.md")
raw("repository/docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md")
source_path = "prototypes/static_tray_v01/current_host_inspection_v01.py"
source_bytes = subprocess.check_output(["git", "show", branch + ":" + source_path], cwd=repo)
early_source = raw("incoming/p28-early/repository/" + source_path)
check("P28 early inspector is unchanged P27 branch source", source_bytes == early_source)

result = {
  "schema":"ontokin.c271.p28-recovery-state-audit/1",
  "observed_at_utc":datetime.now(timezone.utc).isoformat(),
  "reviewer":"/root/state_audit",
  "scope":"Independent state/recovery policy review; no external writes or product execution",
  "passed":all(c["passed"] for c in checks),
  "checks":checks,
  "inputs":inputs,
  "state":{
    "branch":branch,"main":main,"parent_status":"blocked","P27":"complete_partial_delivery_resolved_by_exact_terminal_pair_and_saved_identities",
    "P28":"active_interrupted_phase; later_candidate_and_publication_objects_not_recovered_by_this_audit",
    "P28_recorded_owner":"c271-p28-4b91a1fab6b4","P28_release_observed":False,
    "main_lease":"released in governing STATUS; no P28 lease claimed",
    "first_unmet_recovery_gate":"Recover and authenticate exact later P28 candidate, frozen control inputs, test/review evidence and publication intent, or retain one concrete missing-artifact blocker and deliver that recovery state.",
    "documentary_checkpoint":"permissible only with explicit recovery ownership, fresh observed-head conditional nonforce publication, exact preserved baseline and candidate readback; does not accept P28 implementation",
    "unknown_immutable_upload_outcome":"retain as unknown; absent branch advancement does not establish that no unreferenced Git objects were created",
    "reported_597_tests_and_docs29_1652_6361":"unverified prior-chat report; no evidence reuse accepted"
  },
  "historical_state_inventory":{
    "task_top_level_keys":list(task),
    "historical_phases":len(task["prior_session_phases"]),
    "historical_deliveries":len(task["prior_phase_deliveries"]),
    "task_check_rows":len(task["checks"]),
    "prior_reconciliations":len(task["phase_reconciliations"]),
    "current_top_level_keys":list(current),
    "all_task_and_current_JSON_bytes_parsed":True,
    "all_historical_test_claims_reexecuted_or_independently_verified":False
  },
  "nested_instructions":{"exact_branch_tree":agent_paths,"saved_manifest_bindings":saved_agent_bindings},
  "read_commands":[c for c in commands if c["command"][1] != "ls-tree"],
  "inspection_incidents":[{"operation":"git ls-tree with :(glob) pathspec","result":"read-only invocation failed: pathspec magic not supported; corrected complete-tree listing and filename filter succeeded","source_or_remote_mutation":False}],
  "limits":[
    "Raw live observations were supplied by the Director; this worker made no GitHub or Library requests.",
    "Only current workspace paths were inspected. Historical absolute paths in records were not followed.",
    "No later P28 candidate hash, complete tree/commit identity, test log, independent acceptance artifact or write receipt was recovered by this worker.",
    "The unavailable branch-tree API response is a transport failure, not evidence of absence. Exact local Git-tree inspection supplies only the observed branch inventory.",
    "This audits recovery policy/state; it does not approve an as-yet-unseen documentary publication candidate or handoff archive."
  ]
}
(OUT / "AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"passed":result["passed"],"checks":len(checks),"failures":[x for x in checks if not x["passed"]],"inputs":len(inputs)}))
