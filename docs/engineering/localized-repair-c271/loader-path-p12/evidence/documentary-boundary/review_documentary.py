"""Read-only documentary candidate review; writes only reviewer evidence."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
REPO = ROOT.parent / "OntoKin"
HEAD = "74c9cdaeb7f92cc7d3e6957b8a92d798250b9e55"
TREE = "c449b7db33ebdeaef3dd7a91c735256ba2f32023"
BASE = "79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae"
P12 = "docs/engineering/localized-repair-c271/loader-path-p12/"

def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)

def identify(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def file_identity(path):
    return {"path": str(path), **identify(path.read_bytes())}

def load(path):
    return json.loads((REPO / path).read_bytes())

def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

checks = []
def check(name, passed, evidence):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

assert git("rev-parse", "HEAD").decode().strip() == HEAD
staged = git("diff", "--cached", "--name-only", "-z").decode().split("\0")[:-1]
index = {}
for row in git("ls-files", "--stage", "-z").decode().split("\0")[:-1]:
    meta, path = row.split("\t", 1)
    mode, blob, stage = meta.split()
    assert stage == "0"
    index[path] = (mode, blob)
tree = {}
for row in git("ls-tree", "-r", "-z", TREE).decode().split("\0")[:-1]:
    meta, path = row.split("\t", 1)
    mode, kind, blob = meta.split()
    tree[path] = (mode, blob)
check("exact_staged_tree", index == tree, {"tree": TREE, "head": HEAD, "paths": len(staged)})
rows = []
for path in staged:
    raw = git("show", ":" + path)
    working = (REPO / path).read_bytes()
    rows.append({"path": path, "mode": index[path][0], "blob": index[path][1], **identify(raw), "working_equals_staged": raw == working})
check("documentation_only_candidate", len(staged) == 64 and all(p.startswith("docs/") for p in staged), {"count": len(staged)})
check("reviewed_working_bytes_equal_staged", all(r["working_equals_staged"] for r in rows), {"rows": "REVIEWED-FILES.json"})
save("REVIEWED-FILES.json", {"head": HEAD, "tree": TREE, "files": rows})

phase = load(P12 + "PHASE.json")
blocker = load(P12 + "BLOCKER.json")
outcome = load(P12 + "PHASE-OUTCOME.json")
task = load("docs/workflow/tasks/C271/task.json")
current = load("docs/workflow/CURRENT.json")
adjudication = load(P12 + "evidence/review/ADJUDICATION.json")
phase_without_branch = {k:v for k,v in phase.items() if k != "branch"}
task_phase_without_branch = {k:v for k,v in task["session_phase"].items() if k != "branch"}
opening_phase = json.loads(git("show", HEAD + ":" + P12 + "PHASE.json"))
opening_task_phase = json.loads(git("show", HEAD + ":docs/workflow/tasks/C271/task.json"))["session_phase"]
branch_representations_unchanged = phase["branch"] == opening_phase["branch"] and task["session_phase"]["branch"] == opening_task_phase["branch"]
check("canonical_phase_and_blocker_agree", task_phase_without_branch == phase_without_branch and task["session_phase"]["branch"] == phase["branch"]["name"] and branch_representations_unchanged and phase["blocker"] == blocker == outcome["blocker"], {"blocker": blocker["id"], "branch_representation": "Opening checkpoint preserves a name/head/tree object in PHASE and the same branch name string in task.session_phase. Those representations are unchanged; all other phase fields are equal."})
check("accurate_static_N57_finding", blocker["id"] == adjudication["canonical_blocker"] and blocker["sole_context_difference"] == "variant_review.completeness" and blocker["negative_value"] == "unsupported" and blocker["positive_value"] == "synthetic_declared_complete" and "Neither context supplies an actual operational plan or actual plan digest" in blocker["finding"], {"adjudication_sha256": identify((REPO / (P12 + "evidence/review/ADJUDICATION.json")).read_bytes())["sha256"]})
check("behavior_explicitly_not_run", phase["frozen_97_controls"] == phase["existing_175_methods"] == outcome["actual_execution"]["frozen97_controls"] == outcome["actual_execution"]["existing175_methods"] == "not_run" and phase["product_tests_run"] is False and outcome["actual_execution"]["behavior_tests"] == 0 and all(x["result"] == "not_run" for x in task["checks"] if x["name"] == "P12 frozen loader-path controls and existing inspection regression"), {"controls": 97, "inherited_methods": 175})
expected_requirements = {"R01": "done", "R02": "done", "R03": "not_done", "R04": "not_done", "R05": "not_done"}
check("parent_gates_open", task["status"] == phase["parent_status"] == outcome["parent_status"] == "blocked" and {r["id"]: r["status"] for r in task["requirements"]} == expected_requirements == outcome["requirements"] == phase["parent_requirements"] and task["completion"]["merge_commit"] is None and task["completion"]["branch_disposition"] == "retained", {"requirements": expected_requirements, "plan": {r["id"]: r["status"] for r in task["plan"]}})
check("documentary_next_action_only", task["next_action"] == phase["exact_next_action"] == current["next_action"]["suggested_task"] == outcome["first_remaining_action"] and "No clarification or implementation begins in this chat." in task["next_action"] and phase["product_implementation_changes"] is False and phase["technical_phase_complete"] is False, {"next_action": task["next_action"], "future_phase_not_current": phase["post_delivery_next_action"]})

old_task = json.loads(git("show", HEAD + ":docs/workflow/tasks/C271/task.json"))
old_current = json.loads(git("show", HEAD + ":docs/workflow/CURRENT.json"))
history_keys = ["historical_checks", "prior_session_phases", "prior_phase_deliveries", "prior_blocked_reason", "completion", "authorization", "delivery"]
history_equal = {k: task[k] == old_task[k] for k in history_keys}
old_history = old_task["blocked_reason_history"]
history_equal["blocked_reason_history_prefix"] = task["blocked_reason_history"][:len(old_history)] == old_history
for field in ("latest_handoff", "previous_handoff", "latest_recovery", "older_handoffs", "previous_recovery", "older_recoveries", "historical_handoff"):
    history_equal["CURRENT." + field] = current[field] == old_current[field]
history_equal["CURRENT.boundaries_prefix"] = current["boundaries"][:len(old_current["boundaries"])] == old_current["boundaries"]
for name in ("PLAN.md", "REQUIREMENTS.md", "P12-SESSION.md"):
    path = "docs/workflow/tasks/C271/" + name
    history_equal[name + "_opening_prefix"] = (REPO / path).read_bytes().startswith(git("show", HEAD + ":" + path))
check("historical_records_preserved", all(history_equal.values()), history_equal)
check("historical_unknowns_preserved", phase["historical_unknowns"] == outcome["historical_unknowns"] == ["C270 broad-driver completion remains unknown", "Global prior-process termination remains unestablished"] and phase["current_unknown_operations"] == outcome["current_unknown_operations"] == [], {"historical_unknowns": phase["historical_unknowns"]})

protected = ["ontokin", "prototypes", "tests", "tools", ".github"]
protected_delta = git("diff", "--name-status", BASE, "--", *protected).decode()
untracked = git("ls-files", "--others", "--exclude-standard", "--", *protected).decode()
source_record_path = ROOT / "checks/SOURCE-BOUNDARY.json"
source_record = json.loads(source_record_path.read_bytes())
new_test = REPO / "tests/test_current_host_loader_path_v01.py"
p11_delta = git("diff", "--name-status", BASE, "--", "docs/engineering/localized-repair-c271/loader-path-p11").decode()
check("protected_source_and_frozen_design_unchanged", not protected_delta and not untracked and not p11_delta and not new_test.exists() and source_record["files_checked"] == len(source_record["rows"]) == 942 and all(r["passed"] for r in source_record["rows"]), {"root_record": file_identity(source_record_path), "current_source_diff": protected_delta, "current_untracked_source": untracked, "P11_diff": p11_delta, "new_test_absent": not new_test.exists()})

copy_rows = []
copy_roots = {
    "review": ROOT / "review",
    "implementation": ROOT / "implementation",
    "opening-publication": ROOT / "publication/opening",
    "opening-record-checks": ROOT / "checks/opening-records",
}
for path in staged:
    prefix = P12 + "evidence/"
    if not path.startswith(prefix):
        continue
    rest = path[len(prefix):]
    if rest == "SOURCE-BOUNDARY.json":
        original = source_record_path
    else:
        group, relative = rest.split("/", 1)
        original = copy_roots[group] / relative
    raw = (REPO / path).read_bytes()
    # Root retains opening checks under the discovered stable checks directory.
    if not original.exists() and "opening-record-checks/" in rest:
        matches = [p for p in (ROOT / "checks").glob("*/" + original.name) if p.parent.name.startswith("opening")]
        assert len(matches) == 1, (str(original), [str(p) for p in matches])
        original = matches[0]
    copy_rows.append({"canonical": path, "source": str(original), **identify(raw), "equal": raw == original.read_bytes()})
check("canonical_evidence_copies_exact", all(r["equal"] for r in copy_rows), {"count": len(copy_rows), "rows": "CANONICAL-COPY-CHECKS.json"})
save("CANONICAL-COPY-CHECKS.json", copy_rows)

check_path = ROOT / "checks/blocked-reviewed-candidate/CHECKS.json"
check_record = json.loads(check_path.read_bytes())
log_rows = []
for result in check_record["checks"]:
    for row in result["logs"]:
        raw = (check_path.parent / row["path"]).read_bytes()
        log_rows.append({"path": str(check_path.parent / row["path"]), "equal": identify(raw) == {"bytes": row["bytes"], "sha256": row["sha256"]}, **identify(raw)})
check("existing_four_documentary_checks_and_logs", check_record["passed"] and len(check_record["checks"]) == 4 and check_record["index_tree"] == TREE and all(r["result"] == "passed" and r["returncode"] == 0 for r in check_record["checks"]) and all(r["equal"] for r in log_rows), {"record": file_identity(check_path), "checks": [{"name":r["name"],"result":r["result"],"returncode":r["returncode"]} for r in check_record["checks"]], "logs": log_rows, "scope": "Root's correction-inclusive record at the exact reviewed staged tree; checks were not rerun by reviewer."})

correction_path = ROOT / "checks/DOCUMENTARY-CORRECTION.json"
correction = json.loads(correction_path.read_bytes())
task_identity = file_identity(REPO / "docs/workflow/tasks/C271/task.json")
check("stale_current_scope_finding_closed", task["remaining_h0_constraint"]["scope"] == correction["after"] and task_identity["sha256"] == correction["sha256"] == "2a66c0e692537f63e0cf760df8351a1efcfdaaf7947db8ce499b6604bf0717b8", {"record": file_identity(correction_path), "before": correction["before"], "after": correction["after"], "task": task_identity})
assert git("rev-parse", "HEAD").decode().strip() == HEAD
assert all((REPO / row["path"]).read_bytes() == git("show", ":" + row["path"]) for row in rows)

findings = [{"id": "P12-DOC-001", "severity": "mandatory_documentary_correction", "state": "closed", "field": "task.json remaining_h0_constraint.scope", "initial_tree": "4fbab57bcd2c1b5605e4375b6d741c54a2c998ae", "reviewed_corrected_tree": TREE, "finding": "An active current-state field still said P12 implements the rule after the technical stop.", "resolution": correction["after"], "evidence": file_identity(correction_path)}]
verdict = "accepted_documentary_blocked_outcome" if all(c["passed"] for c in checks) else "not_accepted"
save("AUDIT.json", {
    "schema": "ontokin.c271.p12-independent-documentary-boundary-review/1",
    "reviewer": "/root/intake_review",
    "completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "head": HEAD,
    "reviewed_staged_tree": TREE,
    "reviewed_paths": len(rows),
    "verdict": verdict,
    "findings": findings,
    "checks": checks,
    "check_groups": len(checks),
    "passed_check_groups": sum(c["passed"] for c in checks),
    "technical_blocker_still_open": "P12-N57-POLICY-BINDING-001",
    "reviewed_file_hashes": "REVIEWED-FILES.json",
    "limits": [
        "Accepts current documentary state only; no new implementation or design is approved.",
        "Publication of this corrected candidate and final ZIP/save remain future gates.",
        "Root's four correction-inclusive record checks bind this reviewed staged tree; the earlier check records remain preserved separately.",
        "No behavior tests, H0/H1, full routine, main integration or parent closure occurred in this review.",
    ],
    "review_observation_errors": [
        {"kind": "overstrict_representation_comparison", "evidence": "ATTEMPT-002-LIMITATION.json", "detail": "Second script result treated the unchanged branch-name versus branch-object representation as disagreement. Original script and machine/prose outputs remain preserved under attempt002. The corrected predicate verifies the same branch name, unchanged baseline representations and exact equality of every other phase field."},
        {"kind": "review_script_path_derivation_failure", "evidence": "ATTEMPT-001-FAILURE.json", "detail": "The first owned review script addressed a nonexistent repository directory and failed before any repository read or report write. Its exact script bytes are preserved in review_documentary-attempt001.py. The path was corrected only in the owned script."},
        {"kind": "nonexistent_inventory_path", "detail": "Initial rg inventory included docs/tasks, which does not exist. It still returned P12 paths; task inspection was corrected to docs/workflow/tasks/C271. No mutation."},
        {"kind": "display_truncation", "detail": "A combined diff/full-document display exceeded the aggregate output budget, and one selected JSON display exceeded its individual budget. All changed content needed for the decision was subsequently read in bounded calls; exact full bytes are retained by the staged-tree/file identities."},
    ],
})
report = f"""# P12 documentary boundary review

**Accepted after one documentary correction.** Reviewed HEAD `{HEAD}` and exact staged tree `{TREE}`: 64 documentation paths, with working bytes equal to staged bytes. `REVIEWED-FILES.json` records every path, Git blob, mode, byte count and SHA256.

The canonical phase, blocker and task agree that `P12-N57-POLICY-BINDING-001` stopped implementation. N57's required refusal has no specified production binding for its sole synthetic label difference. The record distinguishes identical synthetic digest observations from an actual operational plan digest. No new admission design, input substitution or oracle revision is adopted.

The 97 controls and 175 inherited methods remain **not run**. C271 is blocked; R01/R02 remain done, R03–R05 not done, and P02 in progress. The retained branch and absence of a merge are unchanged. The current next action is documentary publication, verified saved partial handoff and separate receipt, then stop. Clarification is expressly deferred to a fresh phase.

Finding `P12-DOC-001` is closed: root corrected the stale current-state sentence that said P12 implements the rule. The correction now states that P12 stopped before implementation. The corrected task SHA256 is `{task_identity['sha256']}`; original intent remains preserved in the historical phase scope.

All {len(copy_rows)} staged canonical evidence copies match their original session files. The 942-file source-preservation record is intact; current read-only Git comparisons show no protected-source or P11-design changes and no new focused test. Historical task/CURRENT records and prior document prefixes are preserved. Root's four correction-inclusive documentary checks and all eight logs verify exactly against this staged tree; earlier check records remain preserved. Two reviewer calculation issues are preserved: an initial wrong directory, and an overstrict comparison of pre-existing branch object/string representations. The corrected review verifies matching branch names, unchanged representations and every other phase field exactly; no product test failed.

No mandatory documentary finding remains. This review accepts the corrected blocked-outcome records only. Conditional publication/readback and final package/save still require their own evidence; no implementation acceptance, host qualification, integration or parent completion is claimed.
"""
with (OUT / "REPORT.md").open("x", encoding="utf-8") as handle:
    handle.write(report)
print(json.dumps({"verdict": verdict, "check_groups": len(checks), "passed": sum(c["passed"] for c in checks), "canonical_copies": len(copy_rows), "artifacts": [file_identity(OUT / name) for name in ("AUDIT.json", "REPORT.md", "REVIEWED-FILES.json", "CANONICAL-COPY-CHECKS.json")]}, indent=2))
