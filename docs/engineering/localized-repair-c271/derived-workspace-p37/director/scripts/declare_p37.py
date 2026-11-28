"""C271-P37: write the declaration and update task.json and CURRENT.json. Run as python3 -I -S -B."""
import copy, json, os, sys

WT = "<worktree>"
T = WT + "/docs/workflow/tasks/C271/task.json"
C = WT + "/docs/workflow/CURRENT.json"
D = "docs/engineering/localized-repair-c271/derived-workspace-p37/"
NOW = sys.argv[1]
OWNER = "c271-p37-08beec34eb0a"
PHASE = "C271-P37-derived-workspace-correction"
HEAD = "07d4e3c31e31054b147b586569f29cff3d945d5b"
MAIN = "51223c9b94a222f29d38eb6c33808f8e55e2bff9"
NEXT = ("C271-P37-derived-workspace-correction is declared and in progress: the correction of FZ-01, the implementation "
        "blocker that stopped gate MR at its operational freeze. An independent author decides, under P05 section 3 and MC19 "
        "of the adopted contract ontokin.current-host-readback/0.2.0, how the provider's derived source check treats tracked "
        "paths that the driver does not copy into its isolated workspace, and whether that needs an amendment; implements it "
        "in tools/check_local.py and the 0.2.0 provider with one definition of the copied set; an independent author freezes "
        "real-Git controls on a fixture tree that tracks such paths; the Director first measures the derived route's Git "
        "timing (FZ-02) at the real tree's scale, runs the focused tests, the controls and the complete ordinary routine at "
        "the candidate commit, and a fresh reviewer reviews the candidate. It does not run MR. Nothing is integrated. Then MR "
        "again at the corrected commit, with a new observation plan, HOST and freeze.")

phase_doc = {
    "schema": "ontokin.c271.p37-derived-workspace-correction/1",
    "task": "C271",
    "phase": PHASE,
    "owner": OWNER,
    "declared_at_utc": NOW,
    "status": "declared_correction_pending",
    "execution_mode": {
        "mode": "local",
        "entry_document": "https://github.com/Omegapy/OntoKin/blob/" + MAIN + "/LOCAL-START-HERE.md",
        "governing_instructions": "current main at " + MAIN + "; gate MB merged it into this branch, so the branch's instruction files are main's bytes",
    },
    "owner_direction": {
        "date": "2026-11-27 (UTC)",
        "question": "Should I start that correction phase now, or leave it for later?",
        "reply": "Start the correction",
        "how_received": "selected by the owner in this session, as the reply to the question that closed C271-P36",
        "scope_of_selection": "the correction of FZ-01 recommended by gate MR's outcome: how the driver's workspace treats tracked paths it does not copy, with tests on a tree that has such paths; MR again afterwards",
    },
    "objective": ("Correct FZ-01, gate MR's blocker, under P05 section 3 and MC19 of ontokin.current-host-readback/0.2.0: an "
                  "independent decision on how the 0.2.0 provider's derived source check treats tracked paths outside the driver's "
                  "copied set, its implementation in tools/check_local.py and prototypes/static_tray_v01/current_host_readback_v02.py "
                  "with one definition of that set, independently frozen real-Git controls, FZ-02's measurement and, if needed, its "
                  "correction, and an independent review of the candidate with the focused tests, the controls and the complete "
                  "ordinary routine as evidence."),
    "plan": D + "CORRECTION-PLAN.md",
    "starting_state": {
        "branch_head": HEAD,
        "main": MAIN,
        "remote_observation": "git ls-remote --heads origin at 2026-11-27T23:13:44Z: this branch at 07d4e3c3, main at 51223c9b, work/c271-p29-trd-record at 880933a4",
        "pull_request": "PR274 open, draft, head 07d4e3c3",
        "scope_issue": "issue273 open",
        "environment": "as MP prepared it: the doctor (run with --node at a nonexistent path, so that it starts no Node) reports core ready and python-verification not_checked by design (no pip, D-21); the .venv holds no bytecode",
        "gate_mr": "stopped at S6 by FZ-01 (docs/engineering/localized-repair-c271/macos-routine-p36/OUTCOME.json); its fixed state ended with its outcome records",
    },
    "acceptance": [
        {"id": "A1", "check": "This declaration and its plan are pushed before any phase work."},
        {"id": "A2", "check": "FZ-02 is measured at the declaration commit before the decision: the provider's exact status and untracked-file reads in a workspace that the driver's own prepare_workspace copied from the real tree, through HOST's bound Git, five times each before and after an index refresh, with every time recorded."},
        {"id": "A3", "check": "An independent author's decision record states the rule for status lines in the derived workspace, its basis in P05 section 3 and MC19, whether a versioned amendment is needed, and what FZ-02's measurement requires; the implementation keeps one definition of the copied set, keeps every other refusal, and has focused tests."},
        {"id": "A4", "check": "An independent author freezes the controls before the Director executes them: the derived route with real Git on a fixture tree that tracks paths outside the copied set, a symbolic link among them (accepted), and every unchanged refusal inside the copied set and on the original route (refused)."},
        {"id": "A5", "check": "The Director executes the focused tests, the frozen controls, MI's frozen control module unchanged and the existing modules of the changed files at the candidate commit C, with every failure retained; C is pushed and read back."},
        {"id": "A6", "check": "The complete ordinary routine of tools/check_local.py runs once at C with PATH fixed so that no Node can start, with the Python inventory read before and after; MR's reviewed comparator lists every difference from main's resolved-directory run; C's default inventory additions are listed by exact ID for MC28."},
        {"id": "A7", "check": "A fresh reviewer reviews C, the decision, the implementation, the controls and the evidence, and accepts it with no unresolved mandatory finding."},
        {"id": "A8", "check": "Records with path-portable copies; the workflow check, the documentation verifier and a whitespace check pass; pushed without force and read back; one checkpoint comment each on PR274 and issue273; PR274 stays draft; main is not written."},
    ],
    "ownership": {
        "director": OWNER,
        "director_session": "the same Claude Code session that carried out C271-P30 to P36",
        "owned": ["the C271 worktree, its index and .venv", "every update of this branch in this phase", "the working evidence directory ../OntoKin-local/c271-p37/"],
        "workers": "W1 (author of the decision and the implementation), W2 (independent control author) and W3 (independent reviewer), each with the exclusive files of the plan's section 3; no worker makes a Git write",
        "main": "not written; the integration lease is not used",
    },
    "stopping_condition": "A1 to A8 met, with the correction reviewed and its records pushed and read back; or a concrete blocker, such as a decision that needs an amendment of the contract.",
    "excluded": [
        "gate MR and R03's acceptance, R04 and R05",
        "the 0.1.0 provider and the Linux route",
        "any download or install; any change to the prepared runtime, reader tree or .venv",
        "Node, ldd and codesign starts; the --full and --force-agent profiles",
        "any write to main",
    ],
    "records": D,
}
os.makedirs(WT + "/" + D, exist_ok=True)
pp = WT + "/" + D + "PHASE.json"
fd = os.open(pp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(phase_doc, indent=2, ensure_ascii=False) + "\n")

doc = json.load(open(T, encoding="utf-8"))
assert doc["owner"] == "c271-p36-14f7f8b219db", doc["owner"]
for key in ("p37_prior_current_fields", "p37_derived_workspace_correction", "p37_fields_index"):
    assert key not in doc, key
doc["p37_prior_current_fields"] = {
    "recorded_at_utc": NOW,
    "purpose": "The current values that the C271-P37 declaration replaced, kept unchanged as P36's closing state.",
    "owner": doc["owner"], "next_action": doc["next_action"], "session_phase": copy.deepcopy(doc["session_phase"])}
doc["owner"] = OWNER
doc["next_action"] = NEXT
doc["session_phase"] = {
    "schema": "ontokin.c271.p37-derived-workspace-correction/1", "task": "C271", "phase": PHASE, "owner": OWNER,
    "declared_at_utc": NOW, "execution_mode": "local", "observed_main": MAIN, "starting_branch_head": HEAD,
    "branch": "work/c271-missing-import-digest-control", "worktree": "../OntoKin-worktrees/c271",
    "pull_request": 274, "scope_issue": 273, "record": D + "PHASE.json", "plan": D + "CORRECTION-PLAN.md",
    "session_checkpoint": "docs/workflow/tasks/C271/P37-SESSION.md", "status": "declared_correction_pending"}
doc["p37_derived_workspace_correction"] = {
    "phase": PHASE, "owner": OWNER, "record": D + "PHASE.json", "plan": D + "CORRECTION-PLAN.md",
    "session_checkpoint": "docs/workflow/tasks/C271/P37-SESSION.md", "declared_at_utc": NOW,
    "status": "declared_correction_pending",
    "owner_direction": [phase_doc["owner_direction"]],
    "blocker_corrected": "FZ-01 of gate MR (docs/engineering/localized-repair-c271/macos-routine-p36/reviews/FREEZE-REVIEW-DISPOSITION-001.json)",
    "downloads": "none needed and none approved",
    "parent_complete": False}
index = copy.deepcopy(doc["p36_fields_index"])
index["recorded_at_utc"] = NOW
index["purpose"] = ("Extends p36_fields_index, which stays unchanged: p37_derived_workspace_correction joins the current-state "
                    "fields of task.json, and p36_macos_routine becomes history.")
fields = index["current_state_fields"]["task.json"]
fields[fields.index("p36_macos_routine")] = "p37_derived_workspace_correction"
index["now_history"] = {"task.json": ["p36_macos_routine", "p36_prior_current_fields", "p36_fields_index", "p37_prior_current_fields"]}
doc["p37_fields_index"] = index
open(T, "w", encoding="utf-8").write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

cur = json.load(open(C, encoding="utf-8"))
cur["snapshot_date"] = NOW
cur["next_action"] = {"status": "ready", "summary": NEXT, "suggested_task": "C271",
                      "sources": ["docs/workflow/tasks/C271/task.json", "docs/workflow/tasks/C271/P37-SESSION.md", D + "PHASE.json"]}
cur["checkpoint"]["session"] = "docs/workflow/tasks/C271/P37-SESSION.md"
b = cur["boundaries"]
old = ("gate MR (R03) stopped at stage S6 in C271-P36, before any routine run, with an implementation blocker (FZ-01: the "
       "provider's derived source check refuses the driver's workspace, which lacks seven tracked .claude/ entries);")
hits = [i for i, v in enumerate(b) if old in v]
assert len(hits) == 1, hits
b[hits[0]] = b[hits[0]].replace(old, old[:-1] + ", and its correction is declared as C271-P37 and in progress;")
open(C, "w", encoding="utf-8").write(json.dumps(cur, indent=2, ensure_ascii=False) + "\n")
print("ok", NOW)
