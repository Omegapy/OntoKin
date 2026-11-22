"""Bounded independent receipt and canonical-record review; no repository writes."""
from pathlib import Path
import base64
import datetime
import hashlib
import json
import stat
import subprocess
import zipfile

OUT=Path(__file__).resolve().parent
SESSION=OUT.parents[1]
WORKSPACE=SESSION.parent
REPO=WORKSPACE/"OntoKin"
P12="docs/engineering/localized-repair-c271/loader-path-p12/"
HEAD="09e04b394194b7a21dc203dd7bba2e548ca1c168"
TREE="f88f110291b2fc77b94603455aefe32a7daa266a"
SOURCE_TREE="ae7a01657b6f545640eba2b7e30e5800dacda37f"

def identity(raw):
    return {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def file_identity(path):
    return {"path":str(path),**identity(path.read_bytes())}

def git(*args):
    return subprocess.check_output(["git",*args],cwd=REPO)

def load(path):
    return json.loads(path.read_bytes())

def save(name,value):
    with (OUT/name).open("x",encoding="utf-8") as h:
        h.write(json.dumps(value,indent=2,ensure_ascii=False)+"\n")

checks=[]
def check(name,passed,evidence):
    checks.append({"name":name,"passed":bool(passed),"evidence":evidence})
    assert passed,name

staged=git("diff","--cached","--name-only","-z").decode().split("\0")[:-1]
index={}
for row in git("ls-files","--stage","-z").decode().split("\0")[:-1]:
    meta,path=row.split("\t",1);mode,blob,stage=meta.split();assert stage=="0";index[path]=(mode,blob)
tree={}
for row in git("ls-tree","-r","-z",TREE).decode().split("\0")[:-1]:
    meta,path=row.split("\t",1);mode,kind,blob=meta.split();tree[path]=(mode,blob)
file_rows=[]
for path in staged:
    raw=git("show",":"+path)
    file_rows.append({"path":path,"mode":index[path][0],"blob":index[path][1],**identity(raw),"working_equals_staged":raw==(REPO/path).read_bytes()})
check("exact_documentary_candidate",git("rev-parse","HEAD").decode().strip()==HEAD and index==tree and len(staged)==34 and all(p.startswith("docs/") for p in staged) and all(r["working_equals_staged"] for r in file_rows),{"head":HEAD,"staged_tree":TREE,"paths":len(staged)})
save("REVIEWED-FILES.json",{"head":HEAD,"tree":TREE,"files":file_rows})

readback_path=SESSION/"delivery/FINAL-SAVED-READBACK.json"
readback=load(readback_path)
upload=load(SESSION/"delivery/final-upload.json")
transfers=load(SESSION/"delivery/final-readback-metadata.json")
folder=load(SESSION/"delivery/FINAL-FOLDER-METADATA.json")
upload_by_id={r["file_id"]:r for r in upload["results"]}
transfer_by_id={r["file_id"]:r for r in transfers["transfers"]}
folder_by_id={r["file_id"]:r for r in folder["items"]}
files=[]
for row in readback["files"]:
    local=Path(row["local_path"]);downloaded=Path(row["readback_path"])
    raw=local.read_bytes();actual=downloaded.read_bytes()
    u=upload_by_id[row["file_id"]];t=transfer_by_id[row["file_id"]];f=folder_by_id[row["file_id"]]
    same_identity=all(u[k]==t[k]==row[k] for k in ("file_id","library_file_id","file_name","current_version_number")) and f["library_file_id"]==row["library_file_id"] and f["name"]==row["file_name"] and int(f["version_id"])==row["version"]==0 and f["size_bytes"]==t["size_bytes"]==row["bytes"] and t["workspace_path"]==str(downloaded) and u["status"]==row["status"]=="succeeded"
    files.append({"file_name":row["file_name"],"file_id":row["file_id"],"library_file_id":row["library_file_id"],"version":row["version"],**identity(raw),"downloaded_identity":identity(actual),"bytes_equal":raw==actual,"record_identity_equal":identity(raw)=={"bytes":row["bytes"],"sha256":row["sha256"]},"service_metadata_equal":same_identity})
check("three_saved_files_exact_readback_and_service_identity",readback["all_saved_bytes_equal"] and len(files)==3 and all(r["bytes_equal"] and r["record_identity_equal"] and r["service_metadata_equal"] for r in files) and not transfers["unavailable_items"],{"files":files,"folder_id":folder["directory_id"],"evidence":[file_identity(SESSION/"delivery"/n) for n in ("FINAL-SAVED-READBACK.json","final-upload.json","final-readback-metadata.json","FINAL-FOLDER-METADATA.json")]})
archive=readback["files"][0]
with zipfile.ZipFile(archive["readback_path"]) as z:
    prompt_matches=[Path(r["readback_path"]).read_bytes()==z.read(r["matches_archive_member"]) for r in readback["files"][1:]]
    zip_checkpoint=json.loads(z.read("CHECKPOINT.json"))
check("accepted_zip_and_matching_saved_prompts",archive["sha256"]=="337f8fd00f91987c6a70ba91a9439a5da29bc91a81507d4a92d2d9bc17cbb323" and archive["bytes"]==2075115 and all(prompt_matches) and readback["source_commit"]==zip_checkpoint["source_commit"]==HEAD and readback["source_tree"]==zip_checkpoint["source_tree"]==SOURCE_TREE,{"archive_sha256":archive["sha256"],"source":HEAD,"tree":SOURCE_TREE,"prompt_members_equal":prompt_matches})

receipt_path=REPO/(P12+"P12-DELIVERY.json")
receipt=load(receipt_path);delivery=receipt["delivery"]
phase=load(REPO/(P12+"PHASE.json"));outcome=load(REPO/(P12+"PHASE-OUTCOME.json"));task=load(REPO/"docs/workflow/tasks/C271/task.json");current=load(REPO/"docs/workflow/CURRENT.json")
check("canonical_saved_core_bindings_agree",delivery["archive"]==readback["files"][0] and delivery["matching_prompts"]==readback["files"][1:] and delivery==phase["delivery"]==task["delivery"]==task["session_phase"]["delivery"] and all(current["latest_handoff"][k]==delivery["archive"][k] for k in delivery["archive"]) and current["latest_handoff"]["matching_prompts"]==delivery["matching_prompts"] and delivery["source_revision"]==HEAD and delivery["source_tree"]==SOURCE_TREE,{"receipt":file_identity(receipt_path),"source_revision":delivery["source_revision"],"source_tree":delivery["source_tree"]})
check("terminal_confirmation_remains_pending",delivery["core_saved_and_readback_verified"] is True and delivery["status"]=="delivery_confirmation_pending" and delivery["terminal_receipt_status"]=="not_yet_saved_at_this_source_snapshot" and delivery["phase_complete"] is False and delivery["technical_phase_complete"] is False and outcome["terminal_confirmation_pending_at_source_time"] is True and "that save remains pending at this source snapshot" in (REPO/(P12+"README.md")).read_text(),{"core":"saved_and_exactly_read_back","terminal_receipt":delivery["terminal_receipt_filename"],"terminal_state":delivery["terminal_receipt_status"],"phase_status":phase["status"]})
check("blocked_parent_unrun_behavior_and_delivery_only_action",receipt["parent_status"]==task["status"]==phase["parent_status"]=="blocked" and receipt["parent_complete"] is False and receipt["source_changes"] is False and receipt["product_tests_run"] is False and receipt["frozen_controls_97"]==receipt["existing_methods_175"]=="not_run" and {r["id"]:r["status"] for r in task["requirements"]}=={"R01":"done","R02":"done","R03":"not_done","R04":"not_done","R05":"not_done"} and receipt["next_action"]==phase["exact_next_action"]==task["next_action"]==current["next_action"]["suggested_task"] and "then stop this chat" in receipt["next_action"],{"blocker":receipt["blocker"],"next_action":receipt["next_action"],"full_routine":receipt["required_full_routine"]})

old_task=json.loads(git("show",HEAD+":docs/workflow/tasks/C271/task.json"))
old_current=json.loads(git("show",HEAD+":docs/workflow/CURRENT.json"))
history={k:task[k]==old_task[k] for k in ("historical_checks","prior_session_phases","prior_blocked_reason","blocked_reason_history","remaining_h0_constraint","authorization")}
history["prior_deliveries_retained"]=all(v in task["prior_phase_deliveries"] for v in old_task["prior_phase_deliveries"])
history["previous_handoff_preserves_old_latest"]=current["previous_handoff"]==old_current["latest_handoff"]
history["older_handoffs_preserve_old_previous"]=old_current["previous_handoff"] in current["older_handoffs"]
history["older_handoffs_prefix"]=current["older_handoffs"][:len(old_current["older_handoffs"])]==old_current["older_handoffs"]
for k in ("latest_recovery","previous_recovery","older_recoveries","historical_handoff","boundaries"):
    history["CURRENT."+k]=current[k]==old_current[k]
for name in ("PLAN.md","REQUIREMENTS.md","P12-SESSION.md"):
    path="docs/workflow/tasks/C271/"+name;history[name+"_prefix"]=(REPO/path).read_bytes().startswith(git("show",HEAD+":"+path))
check("history_and_unknowns_preserved",all(history.values()) and phase["historical_unknowns"]==old_task["session_phase"]["historical_unknowns"],history)

envelope_path=REPO/(P12+"evidence/final-package-attempt001/RESTORATION.stdout.transport.json")
envelope=load(envelope_path)
decoded=base64.b64decode(envelope["data"],validate=True)
original_path=WORKSPACE/envelope["original_session_path"]
raw_original=original_path.read_bytes()
check("lossless_raw_evidence_transport",envelope["schema"]=="ontokin.raw-evidence-transport/1" and envelope["encoding"]=="base64" and decoded==raw_original and identity(decoded)=={"bytes":envelope["original_bytes"],"sha256":envelope["original_sha256"]} and envelope["original_sha256"]=="74fdbe2110a8eaf5062f230598bf8f6e40fe5e6507a09f4a65da3f5e4ce5db43" and stat.S_IMODE(original_path.stat().st_mode)==int(envelope["original_mode"],8) and decoded.endswith(b"\n\n"),{"envelope":file_identity(envelope_path),"raw_original":file_identity(original_path),"original_mode":envelope["original_mode"],"trailing_blank_line_preserved":True})

failed_check_path=SESSION/"checks/delivery-candidate/CHECKS.json"
failed_check=load(failed_check_path)
recheck_path=SESSION/"checks/delivery-transport-recheck/CHECK.json"
recheck=load(recheck_path)
logs=[]
for result in failed_check["checks"]:
    for log in result["logs"]:
        raw=(failed_check_path.parent/log["path"]).read_bytes()
        logs.append({"path":str(failed_check_path.parent/log["path"]),"matches":identity(raw)=={"bytes":log["bytes"],"sha256":log["sha256"]}})
failed=[r for r in failed_check["checks"] if r["returncode"]!=0]
check("failed_whitespace_and_affected_recheck_honest",len(failed)==1 and failed[0]["name"]=="staged-whitespace" and failed[0]["returncode"]==2 and failed_check["passed"] is False and all(r["matches"] for r in logs) and recheck["passed"] is True and recheck["returncode"]==0 and recheck["raw_sha256"]==envelope["original_sha256"],{"failed_record":file_identity(failed_check_path),"failed_index_tree":failed_check["index_tree"],"passed_affected_recheck":file_identity(recheck_path),"recheck_tree":recheck["index_tree"],"reviewed_tree":TREE,"limit":"Recheck predates the single README future/pending wording correction. Required checks at the exact published terminal checkpoint remain a later root gate; no final-tree four-pass result is fabricated."})

copies=[]
for path in staged:
    mappings=[(P12+"evidence/final-package/",SESSION/"review/final-package-corrected"),(P12+"evidence/final-package-attempt001/",SESSION/"review/final-package"),(P12+"evidence/published-blocked-record-checks/",SESSION/"checks/published-blocked-source")]
    if path.endswith("RESTORATION.stdout.transport.json") or path.endswith("TRANSPORT.md"):
        continue
    for prefix,source in mappings:
        if path.startswith(prefix):
            original=source/path[len(prefix):]
            copies.append({"canonical":path,"original":str(original),"equal":(REPO/path).read_bytes()==original.read_bytes()})
            break
check("canonical_review_and_prior_check_copies_exact",len(copies)==22 and all(r["equal"] for r in copies) and identity((REPO/(P12+"evidence/final-package/AUDIT.json")).read_bytes())["sha256"]==receipt["independent_package_review"]["sha256"]=="e1422d1a0087ff0cc967e7220b626077e819b990933bb45e8d647458d2e51cdd",{"copies":copies,"transport_exception":"Raw restoration stdout is losslessly represented and checked separately above."})

save("AUDIT.json",{"schema":"ontokin.c271.p12-independent-delivery-record-review/1","reviewer":"/root/intake_review","completed_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"head":HEAD,"reviewed_staged_tree":TREE,"verdict":"accepted_core_saved_terminal_confirmation_pending","checks":checks,"groups_passed":len(checks),"files":files,"findings":[{"id":"P12-DELIVERY-DOC-001","state":"closed","finding":"README terminal-receipt wording could imply an already completed future save.","resolution":"README now says the separate terminal receipt will confirm later publication/delivery and explicitly remains pending at this snapshot."}],"remaining_gates":["Publish and read back the terminal documentary checkpoint; run required record checks at that exact source.","Build and save the separate terminal receipt with exact source/delta and all declared unique late evidence, including the rejected first ZIP; verify saved bytes and publish the matching terminal confirmation.","Stop this phase with C271 blocked; no second technical phase."],"limits":["This is a receipt/canonical-document delta review, not a repeat technical/package audit.","The current reviewed tree follows the successful affected whitespace recheck by one README wording correction; later published-source checks are not claimed here.","No product or host execution, integration or parent completion is inferred from the three successful file saves."],"pending_writes":[]})
report=f"""# P12 saved-core receipt review

**Accepted: core files saved; separate terminal confirmation remains pending.** Reviewed HEAD `{HEAD}` and exact staged tree `{TREE}` (34 documentary paths). All {len(checks)} bounded review groups passed.

The accepted ZIP and both prompts match their saved readbacks byte-for-byte. Upload results, returned download metadata, folder entries and canonical records agree on all three file IDs, Library IDs, names, version 0 and sizes. ZIP identity remains 2,075,115 bytes / SHA256 `337f8fd00f91987c6a70ba91a9439a5da29bc91a81507d4a92d2d9bc17cbb323`. Both saved prompts equal their ZIP members; source is `{HEAD}` / `{SOURCE_TREE}`.

`P12-DELIVERY.json`, PHASE, task delivery and CURRENT bind the same saved core. They do not mark the technical phase or parent complete. The terminal receipt explicitly remains unsaved at this source snapshot. The README ambiguity was corrected to future/pending wording. C271 remains blocked; R03–R05 remain unmet; the 97 controls and 175 methods remain not run. Historical records and displaced handoff pointers are preserved.

The failed staged-whitespace check is retained unchanged. Its exact raw restoration output, including the extra final blank line, is preserved in the session and a verified base64 envelope: 244,884 bytes, SHA256 `74fdbe2110a8eaf5062f230598bf8f6e40fe5e6507a09f4a65da3f5e4ce5db43`, mode `0644`. The affected recheck passed; its tree predates only the README wording correction. Exact published-source checks remain a later gate and are not falsely reported as completed here.

Publish the reviewed documentary checkpoint, verify required checks there, then save/read back the separate terminal receipt with the rejected archive and unique late evidence. Stop afterward. No mandatory receipt-record finding remains; no product work or broader audit is required by this review.
"""
with (OUT/"REPORT.md").open("x",encoding="utf-8") as h:h.write(report)
print(json.dumps({"verdict":"accepted_core_saved_terminal_confirmation_pending","groups_passed":len(checks),"artifacts":[file_identity(OUT/n) for n in ("AUDIT.json","REPORT.md","REVIEWED-FILES.json")]},indent=2))
