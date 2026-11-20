from pathlib import Path, PurePosixPath
import datetime, hashlib, json, os, platform, subprocess, sys, zipfile

OUT = Path("/workspace/scratch/d59e10906594/session/state-audit")
REPO = Path("/workspace/scratch/d59e10906594/OntoKin")
ARCHIVE = Path("/workspace/scratch/d59e10906594/source-handoff/OntoKin_C268_Development_Handoff_2026-11-19.zip")
MAIN = "23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb"
env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
events = []
def git(*args, require=True):
    p = subprocess.run(["git", *args], cwd=REPO, env=env, capture_output=True)
    events.append({"argv":["git",*args],"returncode":p.returncode,"stderr":p.stderr.decode(errors="replace")})
    if require and p.returncode:
        raise RuntimeError(events[-1])
    return p
def api(name):
    wrapped = json.loads((OUT / (name + ".json")).read_text())
    assert not wrapped.get("isError"), name
    return json.loads(wrapped["structuredContent"]["content"])
def digest(b):
    return hashlib.sha256(b).hexdigest()
def identity(b):
    return {"bytes": len(b), "sha256": digest(b)}
def assertion(condition, message):
    if not condition:
        raise AssertionError(message)

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
delivery = api("delivery_live")
current = api("current_live")
heads = [*api("branches_page_1"), *api("branches_page_2")]
prs = [*api("open_prs_page_1"), *api("open_prs_page_2")]
assertion(api("branches_page_2") == [], "branch pagination is not exhausted")
assertion(api("open_prs_page_2") == [], "PR pagination is not exhausted")
assertion(len(heads)==1 and heads[0]["name"]=="main" and heads[0]["commit"]["sha"]==MAIN, "unexpected branches")
assertion(not prs,"open PRs")
assertion(api("main_ref")["object"]["sha"] == api("main_ref_final")["object"]["sha"] == MAIN,"main moved during observations")
assertion(api("issue_265")["state"] == "closed" and api("issue_265")["state_reason"]=="completed","issue not complete")
pr = api("pr_266")
assertion(pr["merged"] and pr["merge_commit_sha"]=="5084dd69312e8da5a49aadd33cf83ba56db7c058","PR merge differs")
assertion(api("pr_retained_head")["object"]["sha"]==pr["head"]["sha"], "retained PR head differs")
assertion(api("merge_commit")["parents"][1]["sha"]==pr["head"]["sha"], "merge does not retain head")
assertion(api("main_commit")["parents"][0]["sha"]=="9ffdbf4aa96ab8c1895aac2c6ee31e7bbf92cf20","closure parent differs")
assertion(api("receipt_commit")["parents"][0]["sha"]==delivery["packaged_git_revision"],"receipt source differs")
assertion(current["active_task"] is None and current["next_action"]["status"]=="awaiting_user_direction","active task conflict")
assertion(api("task_live")["status"]==api("closure_live")["status"]=="done","task closure differs")
assertion(delivery["status"]=="confirmed","delivery not confirmed")
assertion(git("rev-parse","HEAD").stdout.decode().strip()==MAIN, "local head differs")
assertion(git("rev-parse","HEAD^{tree}").stdout.decode().strip()==api("main_commit")["tree"]["sha"],"local tree differs")
status = git("status","--porcelain=v1","--untracked-files=all").stdout.decode()
assertion(status == "", "working tree not clean at audit observation")
for ancestor in (pr["head"]["sha"], pr["merge_commit_sha"], "71932558224d80794f76e52adf603b6308580326", delivery["packaged_git_revision"], "9ffdbf4aa96ab8c1895aac2c6ee31e7bbf92cf20"):
    assertion(git("merge-base","--is-ancestor",ancestor,MAIN).returncode == 0,"ancestor missing: "+ancestor)
local_api = {}
for name,path in [
 ("current_live","docs/workflow/CURRENT.json"),
 ("delivery_live","docs/engineering/localized-repair-c268/DELIVERY.json"),
 ("closure_live","docs/engineering/localized-repair-c268/evidence/delivery-60da64efa55b/CLOSURE.json"),
 ("task_live","docs/workflow/tasks/C268/task.json")]:
    b=(REPO/path).read_bytes()
    response=json.loads((OUT/(name+".json")).read_text())["structuredContent"]["content"].encode()
    assertion(b==response, "live file and local bytes differ: "+path)
    local_api[path]=identity(b)

archive_bytes = ARCHIVE.read_bytes()
observed_archive = {"file":str(ARCHIVE),**identity(archive_bytes)}
assertion(observed_archive["bytes"]==delivery["archive"]["bytes"]==current["latest_handoff"]["bytes"],"archive size differs")
assertion(observed_archive["sha256"]==delivery["archive"]["sha256"]==current["latest_handoff"]["sha256"],"archive digest differs")
with zipfile.ZipFile(ARCHIVE) as z:
    names=z.namelist()
    assertion(len(names)==len(set(names)),"duplicate ZIP path")
    for n in names:
        p=PurePosixPath(n)
        assertion(not p.is_absolute() and ".." not in p.parts and "\\" not in n, "unsafe ZIP path: "+n)
        assertion(not z.getinfo(n).is_dir(),"unexpected directory payload")
    assertion(z.testzip() is None,"CRC error")
    manifest=json.loads(z.read("MANIFEST-SHA256.json"))
    assertion(set(names)==set(manifest["files"])|{"MANIFEST-SHA256.json"},"manifest inventory mismatch")
    for n,wanted in manifest["files"].items():
        assertion(identity(z.read(n))==wanted,"payload identity differs: "+n)
    snapshots=json.loads(z.read("SNAPSHOT-SOURCES.json"))
    for s in snapshots:
        b=z.read(s["package_path"])
        assertion(identity(b)=={"bytes":s["bytes"],"sha256":s["sha256"]},"snapshot identity differs")
        source=git("cat-file","blob",s["source_revision"]+":"+s["repository_path"]).stdout
        assertion(source==b,"snapshot differs from Git: "+s["repository_path"])
        listing=git("ls-tree",s["source_revision"],"--",s["repository_path"]).stdout.decode()
        mode,kind,blob_and_path=listing.split(" ",2)
        blob=blob_and_path.split("\t",1)[0]
        assertion(mode==s["git_mode"] and blob==s["git_blob"],"snapshot mode/blob differs")
    checkpoint=json.loads(z.read("CHECKPOINT.json"))
    recovery=z.read("RECOVERY-STATUS.md").decode()
    assertion(checkpoint["source_snapshot_revision"]==delivery["packaged_git_revision"],"freeze identity differs")
    assertion(checkpoint["source_snapshot_tree"]==delivery["packaged_git_tree"]==api("frozen_snapshot")["tree"]["sha"],"freeze tree differs")
    assertion(checkpoint["publication_reconciliation"]["same_tree_publication"]==delivery["same_tree_publication"],"publication mapping differs")
    assertion(api("recovered_publication")["tree"]["sha"]=="5fa6a2a2be560255413a692704ec175f4901d4c5","public recovery tree differs")
    (OUT/"frozen-CHECKPOINT.json").write_text(json.dumps(checkpoint,indent=2)+"\n")
    (OUT/"frozen-RECOVERY-STATUS.md").write_text(recovery)
    archive_checks={"CRC":"passed","unique_safe_relative_paths":"passed","exact_inventory":"passed","manifest_payloads_checked":len(manifest["files"]),"source_snapshots_compared_with_Git":len(snapshots),"fresh_extraction":"not performed; every ZIP payload verified directly in memory","zip_entries":len(names)}

governing=["AGENTS.md","GOAL.md","ROLE.md","docs/workflow/PROTOCOL.md","docs/workflow/HANDOFF.md",".agents/skills/ontokin-session/SKILL.md"]
reads={p:identity((REPO/p).read_bytes()) for p in governing}
workflow_paths=[".github/workflows/force-agent.yml",".github/workflows/reference.yml"]
workflow_read={p:identity((REPO/p).read_bytes()) for p in workflow_paths}
for p in workflow_paths:
    text=(REPO/p).read_text()
    assertion("workflow_dispatch:" in text and "default: false" in text and "inputs.enable_hosted_ci == true" in text,"hosted CI opt-in differs")
ci={}
for prefix in ("main","merge"):
    runs,checks,states=api(prefix+"_runs"),api(prefix+"_checks"),api(prefix+"_status")
    assertion(runs["total_count"]==len(runs["workflow_runs"])==0,"unexpected hosted runs")
    assertion(checks["total_count"]==len(checks["check_runs"])==0,"unexpected check runs")
    assertion(states["total_count"]==len(states["statuses"])==0,"unexpected status checks")
    ci[prefix]={"workflow_runs":0,"check_runs":0,"status_contexts":0,"combined_status":states["state"],"interpretation":"API pending with no status contexts; no executed CI pass or failure asserted"}
report={
 "verdict":"reconciled; no identified C268 gate or known unpublished work requires replay",
 "reviewer":"/root/state_audit","role":"independent investigator","observed_main":MAIN,"observed_tree":api("main_commit")["tree"]["sha"],
 "started_at_utc":started,"completed_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "scope":"C269 startup reconciliation only; no implementation, contract change, integration or remote mutation",
 "command":[sys.executable,"-B",str(OUT/"audit_state.py")],
 "environment":{"python":sys.version,"implementation":platform.python_implementation(),"platform":platform.platform(),"interpreter":sys.executable,"model_settings":"inherited; no override or independently observed numeric settings claimed"},
 "governing_read_set":reads,"live_file_byte_matches":local_api,
 "pagination":{"branches":{"per_page":100,"pages_read":[1,2],"counts":[len(api("branches_page_1")),len(api("branches_page_2"))],"complete":True},"open_prs":{"per_page":100,"pages_read":[1,2],"counts":[len(api("open_prs_page_1")),len(api("open_prs_page_2"))],"complete":True}},
 "branches":heads,"open_prs":prs,"local_working_tree_status_at_observation":status,
 "scope_issue":{"number":265,"state":"closed","state_reason":"completed","closed_at":api("issue_265")["closed_at"]},
 "pr":{"number":266,"merged":pr["merged"],"merge":pr["merge_commit_sha"],"retained_head":pr["head"]["sha"],"source_branch":pr["head"]["ref"],"source_branch_absent":True,"head_is_second_merge_parent":True,"head_and_merge_ancestors_of_observed_main":True},
 "closure":{"receipt_commit":"9ffdbf4aa96ab8c1895aac2c6ee31e7bbf92cf20","closure_commit":MAIN,"frozen_source":delivery["packaged_git_revision"],"task":"done","lease":"available in observed STATUS; no acquisition attempted"},
 "archive":observed_archive,"archive_checks":archive_checks,"ci":ci,"read_workflow_files":workflow_read,
 "unpublished_work":{"known_recovery_commit":"ecce5f18fd4693e254bc6c797cd8b3f0a74d32a1","public_same_tree_mapping":"71932558224d80794f76e52adf603b6308580326","public_tree":"5fa6a2a2be560255413a692704ec175f4901d4c5","frozen_remaining_operations":checkpoint["remaining_operations"],"observation":"Supplied frozen package and current public closure report prior work reconciled; exact supplied archive identity matches live receipt, public mapped tree exists, clean checkout and no active branch/PR were observed.","limit":"No claim that GitHub or the supplied archive can disprove unknown external work. The original unpublished commit's tree-equivalence proof is retained historical evidence; this audit verifies the public mapped tree and package bytes, without reimporting the original bundle."},
 "not_run":["product cohorts","full C260 H-group qualification","native or model trials","hosted workflows","Library save/reopen","repository-wide Actions setting inquiry","fresh ZIP extraction"],
 "inspection_failure":{"attempted_path":"docs/engineering/localized-repair-c268/RECOVERY-STATUS.md","outcome":"absent (expected package-root file); inspected exact RECOVERY-STATUS.md from supplied ZIP instead"},
 "next_action":"Director may select the user-authorized bounded C260 H01-H28 coverage audit, declare acceptance/ownership and confirm early recovery before substantive phase work. Stop after verified final handoff; no implementation or product qualification is authorized by this audit.",
 "git_commands":events
}
(OUT/"AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:report[k] for k in ("verdict","observed_main","archive","archive_checks","pagination","ci")},indent=2))

