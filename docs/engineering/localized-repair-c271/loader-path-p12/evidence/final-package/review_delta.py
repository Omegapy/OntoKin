"""Bounded independent delta review of the corrected frozen P12 handoff."""
from pathlib import Path, PurePosixPath
import collections
import datetime
import hashlib
import json
import os
import stat
import zipfile

OUT = Path(__file__).resolve().parent
SESSION = OUT.parents[1]
WORKSPACE = SESSION.parent
OLD_DIR = WORKSPACE / "deliverables_p12/final"
NEW_DIR = WORKSPACE / "deliverables_p12/final-corrected"
NAME = "OntoKin_C271_P12_Loader_Path_Blocked_Handoff_2026-11-21"
OLD = OLD_DIR / (NAME + ".zip")
NEW = NEW_DIR / (NAME + ".zip")
OLD_HASH = "cb7fdb60de7e116c9d89ccb0aead793fef1bdfc38cdb927f8c8477a123040ea7"
NEW_HASH = "337f8fd00f91987c6a70ba91a9439a5da29bc91a81507d4a92d2d9bc17cbb323"
SOURCE = "09e04b394194b7a21dc203dd7bba2e548ca1c168"
TREE = "ae7a01657b6f545640eba2b7e30e5800dacda37f"

def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def file_identity(path):
    return {"path": str(path), **identity(path.read_bytes())}

def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def safe(name):
    return bool(name) and not PurePosixPath(name).is_absolute() and "\\" not in name and ":" not in name and all(x not in ("", ".", "..") for x in name.split("/"))

checks = []
def check(name, passed, evidence):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})
    assert passed, name

check("exact_old_and_corrected_archive_identities", identity(OLD.read_bytes()) == {"bytes":1840636,"sha256":OLD_HASH} and identity(NEW.read_bytes()) == {"bytes":2075115,"sha256":NEW_HASH}, {"old":file_identity(OLD),"corrected":file_identity(NEW)})
with zipfile.ZipFile(OLD) as z:
    old = {i.filename:z.read(i.filename) for i in z.infolist()}
with zipfile.ZipFile(NEW) as z:
    entries = z.infolist()
    names = [i.filename for i in entries]
    new = {n:z.read(n) for n in names}
    safe_zip = len(names) == len(set(names)) == 399 and z.testzip() is None and all(safe(i.filename) and stat.S_ISREG(i.external_attr >> 16) and stat.S_IMODE(i.external_attr >> 16) == 0o644 and not (i.flag_bits & 1) for i in entries)
manifest = json.loads(new["MANIFEST-SHA256.json"])
manifest_rows = [{"path":r["path"], **identity(new[r["path"]]), "passed":identity(new[r["path"]]) == {"bytes":r["bytes"],"sha256":r["sha256"]} and r["transport_mode"] == "0644"} for r in manifest["files"]]
check("safe_corrected_zip_and_full_manifest", safe_zip and len(manifest_rows) == 398 and {r["path"] for r in manifest_rows} == set(new)-{"MANIFEST-SHA256.json"} and all(r["passed"] for r in manifest_rows), {"members":399,"manifest_payloads":398,"mode":"0644","root_manifest_excluded_only":manifest["excluded"]})
save("PAYLOAD-CHECKS.json",manifest_rows)

added = sorted(set(new)-set(old))
removed = sorted(set(old)-set(new))
changed = sorted(k for k in set(old)&set(new) if old[k] != new[k])
unchanged = sorted(k for k in set(old)&set(new) if old[k] == new[k])
reported = json.loads((NEW_DIR / "COMPLETE-FILE-DIFF.json").read_bytes())
expected_changes = ["CHECKPOINT.json","HANDOFF.md","HISTORICAL-DEPENDENCIES.json","MANIFEST-SHA256.json","PACKAGE-BOUNDARY.json","RECOVERY-FILE-MAP.json","RECOVERY-STATUS.md"]
check("complete_independent_file_delta", (len(added),len(removed),len(changed),len(unchanged)) == (15,0,7,377) and changed == expected_changes and added == sorted(r["path"] for r in reported["added"]) and changed == sorted(r["path"] for r in reported["changed"]) and unchanged == sorted(reported["unchanged_paths"]), {"added":added,"removed":removed,"changed":changed,"unchanged_count":len(unchanged),"builder_diff":file_identity(NEW_DIR / "COMPLETE-FILE-DIFF.json")})
save("FILE-DELTA.json",{"old_archive":file_identity(OLD),"corrected_archive":file_identity(NEW),"added":[{"path":p,**identity(new[p])} for p in added],"changed":[{"path":p,"before":identity(old[p]),"after":identity(new[p])} for p in changed],"removed":removed,"unchanged":unchanged})

prior_audit_path = SESSION / "review/final-package/AUDIT.json"
prior_audit = json.loads(prior_audit_path.read_bytes())
source_manifest = json.loads(new["SOURCE-MANIFEST.json"])
check("reuse_exact_verified_316_git_snapshots", identity(prior_audit_path.read_bytes())["sha256"] == "4fd5942b5f93dde82acd38e8f1a61ef47dbacba43d070a877fe97aa1a89b4342" and old["SOURCE-MANIFEST.json"] == new["SOURCE-MANIFEST.json"] and len(source_manifest["snapshots"]) == 316 and all(old[r["payload_path"]] == new[r["payload_path"]] for r in source_manifest["snapshots"]) and source_manifest["source_commit"] == SOURCE and source_manifest["source_tree"] == TREE, {"prior_independent_audit":file_identity(prior_audit_path),"source":SOURCE,"tree":TREE,"reused_source_check":"All exact Git bytes/blob/modes were independently verified for the unchanged first candidate."})
old_checkpoint = json.loads(old["CHECKPOINT.json"])
checkpoint = json.loads(new["CHECKPOINT.json"])
checkpoint_delta = [k for k in set(old_checkpoint)|set(checkpoint) if old_checkpoint.get(k) != checkpoint.get(k)]
check("unchanged_phase_limits_and_checkpoint", checkpoint_delta == ["frozen_at_utc"] and checkpoint["parent_status"] == "blocked" and checkpoint["parent_complete"] is False and checkpoint["frozen_97_controls"] == checkpoint["existing_175_methods"] == "not_run" and checkpoint["product_implementation_changes"] is False and checkpoint["delivery"]["status"] == "save_pending" and "No design clarification or implementation begins in this chat." in checkpoint["exact_next_action"], {"checkpoint_only_changed_field":checkpoint_delta,"current_action":checkpoint["exact_next_action"],"future_action":checkpoint["post_delivery_next_action"]})

replacements = {
    "HANDOFF.md": (
        "The accepted corpus was privately materialized with exact bytes and declared modes. Its original unsuccessful helper attempt and corrected attempt remain recorded.",
        "The accepted corpus was privately materialized with exact bytes and declared modes. The materialization attempt completed successfully. Separate failed and overstrict documentary reviewer-script attempts and their corrected rechecks remain recorded."),
    "RECOVERY-STATUS.md": (
        "It includes the initial materialization failure, corrected materialization receipt, author question, independent adjudication, check outputs, publication intentions/readbacks, scripts and delivery observations available before freeze.",
        "It includes the successful materialization attempt and receipt, preserved documentary reviewer-script failures/limitations and corrected rechecks, author question, independent adjudication, check outputs, publication intentions/readbacks, scripts and delivery observations available before freeze."),
}
prose_rows = []
for member,(before,after) in replacements.items():
    old_text = old[member].decode()
    new_text = new[member].decode()
    prose_rows.append({"member":member,"before":before,"after":after,"exact_single_replacement":old_text.count(before) == 1 and old_text.replace(before,after) == new_text})
check("P12_PACKAGE_001_closed", all(r["exact_single_replacement"] for r in prose_rows), {"finding":"P12-PACKAGE-001","state":"closed","corrections":prose_rows,"rationale":"Correctly separates successful corpus materialization from the preserved documentary-review script failures/limitations."})

old_deps = json.loads(old["HISTORICAL-DEPENDENCIES.json"])
new_deps = json.loads(new["HISTORICAL-DEPENDENCIES.json"])
new_dep_key = "rejected_final_candidate_001"
rejected = new_deps[new_dep_key]
check("original_rejected_candidate_preserved", {k:v for k,v in new_deps.items() if k != new_dep_key} == old_deps and rejected["sha256"] == OLD_HASH and rejected["bytes"] == 1840636 and rejected["embedded"] is False and rejected["library_save"] == "not_claimed" and rejected["retained_unchanged"] is True, {"new_dependency":rejected,"limit":"Original archive durable preservation is assigned to the later separate terminal receipt; this package makes no save claim."})

old_map = json.loads(old["RECOVERY-FILE-MAP.json"])
new_map = json.loads(new["RECOVERY-FILE-MAP.json"])
old_rows = {r["relative_path"]:r for r in old_map["files"]}
new_rows = {r["relative_path"]:r for r in new_map["files"]}
identity_keys = ["original_path","relative_path","bytes","sha256","source_mode"]
old_identity_preserved = all(k in new_rows and all(v[f] == new_rows[k][f] for f in identity_keys) for k,v in old_rows.items())
changed_old_rows = [k for k,v in old_rows.items() if new_rows[k] != v]
expected_alias_relocations = ["session_p12/packaging/final-documents/HANDOFF.md","session_p12/packaging/final-documents/RECOVERY-STATUS.md"]
alias_relocations = []
for k in changed_old_rows:
    prior = old_rows[k]
    current = new_rows[k]
    alias_relocations.append({"path":k,"old_payload":prior["payload_path"],"new_payload":current["payload_path"],"old_bytes_preserved":old[prior["payload_path"]] == new[current["payload_path"]],"source_mode":current["source_mode"]})
check("all_802_old_recovery_identities_preserved", len(old_rows)==802 and old_identity_preserved and sorted(changed_old_rows)==expected_alias_relocations and all(r["old_bytes_preserved"] for r in alias_relocations), {"identity_fields":identity_keys,"exact_whole_rows_unchanged":800,"alias_relocations":alias_relocations,"reuse":"The first audit restored and verified all 802 original byte/mode identities. Only these two aliases move to preserved draft copies; their payloads are checked above."})

new_paths = sorted(set(new_rows)-set(old_rows))
check("bounded_23_new_recovery_rows", len(new_rows)==825 and len(new_map["files"])==825 and len(new_paths)==23 and new_map["base_revision"]==SOURCE, {"new_paths":new_paths,"all_recovery_paths":825})
new_rows_verified = []
for path in new_paths:
    row = new_rows[path]
    assert safe(path) and "payload_path" in row and safe(row["payload_path"])
    raw = new[row["payload_path"]]
    original = Path(row["original_path"])
    new_rows_verified.append({**row,"payload_identity_matches":identity(raw)=={"bytes":row["bytes"],"sha256":row["sha256"]},"original_file_matches":original.read_bytes()==raw and stat.S_IMODE(original.stat().st_mode)==int(row["source_mode"],8)})
check("all_new_payload_and_source_identities", all(r["payload_identity_matches"] and r["original_file_matches"] for r in new_rows_verified), {"count":23,"modes":dict(collections.Counter(r["source_mode"] for r in new_rows_verified))})

private = OUT / "new-and-relocated-private"
private.mkdir(mode=0o700)
os.chmod(private,0o700)
restored_rows = []
for relative in sorted(new_paths + changed_old_rows):
    row = new_rows[relative]
    raw = new[row["payload_path"]]
    path = private.joinpath(*PurePosixPath(relative).parts)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    with path.open("xb") as handle:
        handle.write(raw)
    path.chmod(int(row["source_mode"],8))
    st = path.lstat()
    restored_rows.append({"relative_path":relative,**identity(path.read_bytes()),"mode":format(stat.S_IMODE(st.st_mode),"04o"),"passed":stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==int(row["source_mode"],8) and path.read_bytes()==raw})
check("private_new_and_relocated_recovery", len(restored_rows)==25 and all(r["passed"] for r in restored_rows) and stat.S_IMODE(private.stat().st_mode)==0o700 and old["RESTORE-RECOVERY.py"]==new["RESTORE-RECOVERY.py"], {"new_files":23,"relocated_old_drafts":2,"private_root_mode":"0700","helper_unchanged":True,"old_full_restoration_repeated":False,"payloads_executed":False,"original_paths_written":False})
save("RECOVERY-DELTA.json",{"original_identity_fields":identity_keys,"all_802_preserved":old_identity_preserved,"whole_rows_equal":800,"alias_relocations":alias_relocations,"new_rows":new_rows_verified,"private_restoration":restored_rows})

prompts = []
for suffix,member in (("Continue","PROMPT-1-CONTINUE.md"),("Recover","PROMPT-2-RECOVER.md")):
    path = NEW_DIR / (NAME + "_" + suffix + ".md")
    prompts.append({**file_identity(path),"member":member,"unchanged_and_exact":path.read_bytes()==new[member]==old[member]})
check("prompts_and_next_action_unchanged", all(r["unchanged_and_exact"] for r in prompts) and all(old[k]==new[k] for k in ("README-START-HERE.md","NEXT-TASK.md")), {"prompts":prompts,"future_design_only_limits":"Reused unchanged independently reviewed prompts, README and NEXT-TASK."})

builder = json.loads((NEW_DIR / "PACKAGE-VERIFICATION.json").read_bytes())
builder_restore = json.loads((NEW_DIR / "RESTORATION.stdout.json").read_bytes())
builder_restored = {r["path"]:r for r in builder_restore["files"]}
check("builder_full_restoration_evidence_agrees", builder["archive"]["sha256"]==NEW_HASH and builder["status"]=="passed" and builder["checks"]["private_original_mode_restoration"]=="passed" and len(builder_restored)==825 and all(builder_restored[k]["sha256"]==v["sha256"] and builder_restored[k]["bytes"]==v["bytes"] and int(builder_restored[k]["restored_mode"],8)==int(v["source_mode"],8) for k,v in new_rows.items()), {"builder_record":file_identity(NEW_DIR / "PACKAGE-VERIFICATION.json"),"restoration_stdout":file_identity(NEW_DIR / "RESTORATION.stdout.json"),"qualification":"Builder evidence inspected; independent current review restored 23 new plus two relocated entries and reused the exact unchanged prior 802-file proof."})

audit={
    "schema":"ontokin.c271.p12-independent-corrected-package-delta-review/1",
    "reviewer":"/root/intake_review",
    "completed_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "archive":file_identity(NEW),
    "previous_archive":file_identity(OLD),
    "source_commit":SOURCE,"source_tree":TREE,
    "verdict":"accepted_corrected_partial_handoff_save_pending",
    "finding":{"id":"P12-PACKAGE-001","state":"closed","resolution":"Only the two inaccurate active descriptions were corrected; successful materialization and actual documentary-review issues are now distinguished. Original archive and erroneous drafts remain preserved history."},
    "checks":checks,"groups_passed":len(checks),
    "counts":{"members":399,"manifest_payloads":398,"git_snapshots":316,"recovery_paths":825,"old_recovery_identities_preserved":802,"old_rows_entirely_equal":800,"old_draft_alias_relocations":2,"new_recovery_paths":23,"private_delta_restored":25,"added_payloads":15,"removed_payloads":0,"changed_payloads":7,"unchanged_payloads":377},
    "prompts":prompts,
    "limitations":["Current review is bounded to exact delta/new evidence and reuses the prior independently verified source and full restoration proof.","The final ZIP/prompts have no reviewed save/readback receipt yet; those remain external observations.","The rejected first ZIP is retained locally with exact identity and is assigned to the terminal receipt for durable preservation; no embedded original archive or successful save is claimed here.","No product execution, H0/H1, full routine, main integration, second phase or parent closure is authorized or observed."],
    "pending_writes":[],
}
save("AUDIT.json",audit)
report=f"""# Corrected P12 package: independent delta review

**Accepted for final save and exact readback.** Finding `P12-PACKAGE-001` is closed. The two active prose statements now correctly distinguish successful corpus materialization from preserved documentary-review script failures/limitations. Original erroneous drafts and the rejected archive remain identifiable preserved history.

Reviewed ZIP: 2,075,115 bytes, SHA256 `{NEW_HASH}`. Source remains `{SOURCE}`, tree `{TREE}`. All {len(checks)} delta-review groups passed.

Independently verified the complete 399-member safe ZIP inventory and 398 manifest payload hashes. Compared against the prior reviewed archive: 15 added payloads, none removed, seven changed and 377 unchanged. Only two active narrative documents changed; the other changes are checkpoint/manifests/recovery metadata. All 316 Git snapshots, both prompts, README, NEXT-TASK, source manifest and restoration helper remain byte-identical.

All 802 original recovery path/byte/hash/mode identities remain exact. Of those mapping records, 800 are entirely unchanged; two aliases now point to preserved copies of the original erroneous drafts. The 23 added records match their actual source bytes and modes. A fresh independent private copy verified all 23 new records plus the two relocated drafts under a `0700` root. The prior independent full 802-file restoration proof was reused; builder evidence also records a complete 825-file restoration.

Parent C271 remains blocked, the 97 controls and 175 methods remain unrun, and the source-time action remains final delivery followed by stopping. The later fresh phase is design clarification only. Final ZIP/prompt save, exact readback and the terminal receipt remain external gates. The terminal receipt must preserve the rejected first ZIP as declared. No further package correction or product work is required by this review.
"""
with (OUT / "REPORT.md").open("x",encoding="utf-8") as handle:
    handle.write(report)
print(json.dumps({"verdict":audit["verdict"],"groups_passed":len(checks),"artifacts":[file_identity(OUT / n) for n in ("AUDIT.json","REPORT.md","FILE-DELTA.json","RECOVERY-DELTA.json")]},indent=2))
