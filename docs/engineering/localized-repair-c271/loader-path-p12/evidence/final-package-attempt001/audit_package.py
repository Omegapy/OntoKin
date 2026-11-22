"""Independently verify one frozen package and its original-mode recovery."""
from pathlib import Path, PurePosixPath
import collections
import datetime
import hashlib
import json
import os
import stat
import subprocess
import sys
import zipfile

OUT = Path(__file__).resolve().parent
SESSION = OUT.parents[1]
WORKSPACE = SESSION.parent
REPO = WORKSPACE / "OntoKin"
PACKAGE_DIR = WORKSPACE / "deliverables_p12/final"
NAME = "OntoKin_C271_P12_Loader_Path_Blocked_Handoff_2026-11-21"
ARCHIVE = PACKAGE_DIR / (NAME + ".zip")
EXPECTED_HASH = "cb7fdb60de7e116c9d89ccb0aead793fef1bdfc38cdb927f8c8477a123040ea7"
SOURCE = "09e04b394194b7a21dc203dd7bba2e548ca1c168"
TREE = "ae7a01657b6f545640eba2b7e30e5800dacda37f"
EARLY = WORKSPACE / "deliverables_p12/early/OntoKin_C271_P12_Loader_Path_Early_Recovery_2026-11-21.zip"
P12 = "repository/docs/engineering/localized-repair-c271/loader-path-p12/"
checks = []

def ident(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def file_ident(path):
    return {"path": str(path), **ident(path.read_bytes())}

def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def check(name, condition, evidence):
    checks.append({"name": name, "passed": bool(condition), "evidence": evidence})
    if not condition:
        raise AssertionError(name)

def safe(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and "\\" not in name and ":" not in name and all(x not in ("", ".", "..") for x in name.split("/"))

raw_zip = ARCHIVE.read_bytes()
check("exact_frozen_archive", ident(raw_zip) == {"bytes": 1840636, "sha256": EXPECTED_HASH}, file_ident(ARCHIVE))
with zipfile.ZipFile(ARCHIVE) as z:
    entries = z.infolist()
    names = [i.filename for i in entries]
    data = {n: z.read(n) for n in names}
    check("safe_zip_inventory_crc", len(entries) == len(set(names)) == 384 and all(safe(i.filename) and stat.S_ISREG(i.external_attr >> 16) and stat.S_IMODE(i.external_attr >> 16) == 0o644 and not (i.flag_bits & 1) for i in entries) and z.testzip() is None, {"members": len(entries), "uncompressed_bytes": sum(i.file_size for i in entries), "transport_mode": "0644", "member_kind": "regular"})
manifest = json.loads(data["MANIFEST-SHA256.json"])
manifest_rows = []
for row in manifest["files"]:
    manifest_rows.append({"path": row["path"], **ident(data[row["path"]]), "passed": ident(data[row["path"]]) == {"bytes": row["bytes"], "sha256": row["sha256"]} and row["transport_mode"] == "0644"})
check("exact_manifest_and_payloads", manifest["excluded"] == ["MANIFEST-SHA256.json"] and len(manifest_rows) == 383 and len({r["path"] for r in manifest_rows}) == 383 and {r["path"] for r in manifest_rows} == set(names) - {"MANIFEST-SHA256.json"} and all(r["passed"] for r in manifest_rows), {"manifest_entries": 383, "excluded_manifest_self": 1})
save("PAYLOAD-CHECKS.json", manifest_rows)

required_roots = ["README-START-HERE.md", "CHECKPOINT.json", "HANDOFF.md", "NEXT-TASK.md", "RECOVERY-STATUS.md", "PROMPT-1-CONTINUE.md", "PROMPT-2-RECOVER.md", "SOURCE-MANIFEST.json", "HISTORICAL-DEPENDENCIES.json", "RECOVERY-FILE-MAP.json", "RESTORE-RECOVERY.py", "PACKAGE-BOUNDARY.json", "MANIFEST-SHA256.json"]
required_repository = ["AGENTS.md", "CHATGPT-START-HERE.md", "GOAL.md", "ROLE.md", "STATUS.md", "docs/README.md", "docs/workflow/CURRENT.json", "docs/workflow/PROTOCOL.md", "docs/workflow/HANDOFF.md", "docs/workflow/registry.json", ".agents/skills/ontokin-session/SKILL.md", ".agents/skills/ontokin-delivery/SKILL.md", ".agents/skills/ontokin-learning/SKILL.md", "docs/workflow/tasks/C271/task.json", "docs/workflow/tasks/C271/PLAN.md", "docs/workflow/tasks/C271/REQUIREMENTS.md", "docs/workflow/tasks/C271/P12-SESSION.md", "docs/workflow/tasks/C271/LEARNING-P12.md"]
check("required_handoff_roots_and_governing_snapshots", all(n in data for n in required_roots) and all("repository/" + n in data for n in required_repository), {"root_files": required_roots, "repository_files": required_repository})
sources = json.loads(data["SOURCE-MANIFEST.json"])
tree_rows = {}
for line in subprocess.check_output(["git", "ls-tree", "-r", "-z", SOURCE], cwd=REPO).decode().split("\0")[:-1]:
    meta, path = line.split("\t", 1)
    mode, kind, blob = meta.split()
    tree_rows[path] = (mode, blob)
source_rows = []
for row in sources["snapshots"]:
    raw = data[row["payload_path"]]
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    passed = row["revision"] == SOURCE and row["tree"] == TREE and ident(raw) == {"bytes": row["bytes"], "sha256": row["sha256"]} and blob == row["git_blob_sha1"] and tree_rows[row["repository_path"]] == (row["git_mode"], blob)
    source_rows.append({**row, "passed": passed})
actual_tree = subprocess.check_output(["git", "rev-parse", SOURCE + "^{tree}"], cwd=REPO).decode().strip()
check("all_git_snapshot_bytes_and_modes", actual_tree == TREE and sources["source_commit"] == SOURCE and sources["source_tree"] == TREE and len(source_rows) == 316 and all(r["passed"] for r in source_rows), {"source": SOURCE, "tree": TREE, "snapshots": len(source_rows)})
save("SOURCE-CHECKS.json", source_rows)

checkpoint = json.loads(data["CHECKPOINT.json"])
boundary = json.loads(data["PACKAGE-BOUNDARY.json"])
task = json.loads(data["repository/docs/workflow/tasks/C271/task.json"])
phase = json.loads(data[P12 + "PHASE.json"])
outcome = json.loads(data[P12 + "PHASE-OUTCOME.json"])
adjudication = json.loads(data[P12 + "evidence/review/ADJUDICATION.json"])
current = json.loads(data["repository/docs/workflow/CURRENT.json"])
check("source_and_blocked_parent_consistent", checkpoint["source_commit"] == boundary["source_commit"] == SOURCE and checkpoint["source_tree"] == boundary["source_tree"] == TREE and checkpoint["parent_status"] == task["status"] == phase["parent_status"] == outcome["parent_status"] == "blocked" and checkpoint["parent_complete"] is False and checkpoint["session_handoff_is_parent_completion"] is False and checkpoint["blocker"]["id"] == adjudication["canonical_blocker"] == "P12-N57-POLICY-BINDING-001", {"parent_requirements": checkpoint["parent_requirements"], "blocker": adjudication["canonical_blocker"]})
check("unrun_and_no_implementation_limits", checkpoint["product_implementation_changes"] is False and checkpoint["product_tests_run"] is False and checkpoint["frozen_97_controls"] == checkpoint["existing_175_methods"] == "not_run" and checkpoint["technical_phase_complete"] is False and checkpoint["main_lease_held"] is False and checkpoint["integration_allowed"] is False, {"frozen_controls": "97 not_run", "existing_methods": "175 not_run", "known_unrun": checkpoint["known_unrun"]})
check("save_pending_and_future_phase_boundaries", checkpoint["delivery"]["status"] == "save_pending" and boundary["save_pending"] is True and "No design clarification or implementation begins in this chat." in checkpoint["exact_next_action"] and "In a fresh bounded phase" in checkpoint["post_delivery_next_action"] and all(b"No clarification was adopted by P12." in data[n] and b"Do not start a second phase in the same conversation." in data[n] for n in ("PROMPT-1-CONTINUE.md", "PROMPT-2-RECOVER.md")), {"current_next_action": checkpoint["exact_next_action"], "post_delivery_next_action": checkpoint["post_delivery_next_action"], "save": "external matching receipt required"})
prompt_rows = []
for suffix, member in (("Continue", "PROMPT-1-CONTINUE.md"), ("Recover", "PROMPT-2-RECOVER.md")):
    path = PACKAGE_DIR / (NAME + "_" + suffix + ".md")
    prompt_rows.append({**file_ident(path), "member": member, "matches": path.read_bytes() == data[member]})
check("matching_external_prompts", all(r["matches"] for r in prompt_rows), prompt_rows)

dependencies = json.loads(data["HISTORICAL-DEPENDENCIES.json"])
early_ident = ident(EARLY.read_bytes())
check("exact_previously_accepted_early_dependency", early_ident == {"bytes": 793843, "sha256": "9adb6a6f8f937253fc4dd76f412346f9767606aa45e3555e2fa81811a5b584d7"} and all(dependencies["p12_early_archive"][k] == early_ident[k] for k in early_ident), {"early_archive": file_ident(EARLY), "independent_early_review": dependencies["p12_early_archive"]["independent_review"]})
check("prior_dependency_identities_retained", dependencies["p11_archive"]["sha256"] == "4eddd353047fb8d6aa316544c8b54d655eb53a1613f9c522bbed0edc1ab1249e" and dependencies["p11_terminal_receipt"]["sha256"] == "55d46239b1950b032a7fa9496b37e49a638b0d8162497b74be9aa29b9c208fd8" and dependencies["c262"]["sha256"] == "b8af544f730a4d1f741d47b56eb3fcf76147ed392a9ebb020f3d966f2f305c90" and not dependencies["p11_archive"]["embedded"] and not dependencies["p11_terminal_receipt"]["embedded"], {"prior_intake_reused": True, "historical_archive_restoration": "not_repeated", "limits": dependencies["limits"]})

recovery = json.loads(data["RECOVERY-FILE-MAP.json"])
recovery_rows = []
with zipfile.ZipFile(EARLY) as ez:
    for row in recovery["files"]:
        assert safe(row["relative_path"])
        if "payload_path" in row:
            raw = data[row["payload_path"]]
            origin = "payload"
        else:
            ref = row["external_source"]
            assert ref["dependency"] == "p12_early_archive" and safe(ref["archive_member"])
            assert ref["archive_bytes"] == early_ident["bytes"] and ref["archive_sha256"] == early_ident["sha256"]
            raw = ez.read(ref["archive_member"])
            origin = "external_archive"
        recovery_rows.append({"relative_path": row["relative_path"], "original_path": row["original_path"], "source": origin, "source_mode": row["source_mode"], **ident(raw), "passed": ident(raw) == {"bytes": row["bytes"], "sha256": row["sha256"]} and int(row["source_mode"], 8) in (0o600, 0o644)})
check("all_recovery_bindings", recovery["base_revision"] == SOURCE and len(recovery_rows) == len({r["relative_path"] for r in recovery_rows}) == 802 and all(r["passed"] for r in recovery_rows), {"rows": 802, "source_counts": dict(collections.Counter(r["source"] for r in recovery_rows)), "mode_counts": dict(collections.Counter(r["source_mode"] for r in recovery_rows)), "external_dependency": "exact confirmed early ZIP"})

extracted = OUT / "fresh-package"
extracted.mkdir(mode=0o700)
for name, raw in data.items():
    path = extracted.joinpath(*PurePosixPath(name).parts)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("xb") as handle:
        handle.write(raw)
    path.chmod(0o644)
restored = OUT / "private-original-modes"
command = [sys.executable, str(extracted / "RESTORE-RECOVERY.py"), str(extracted), str(restored), "--external-archive", "p12_early_archive=" + str(EARLY), "--restore-original-modes"]
with (OUT / "RESTORATION.stdout.json").open("xb") as stdout, (OUT / "RESTORATION.stderr.txt").open("xb") as stderr:
    result = subprocess.run(command, stdout=stdout, stderr=stderr, check=False)
assert result.returncode == 0, "recovery helper failed; exact stdout/stderr retained"
restoration = json.loads((OUT / "RESTORATION.stdout.json").read_bytes())
for row in recovery_rows:
    path = restored / row["relative_path"]
    st = path.lstat()
    row["restored_passed"] = stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and stat.S_IMODE(st.st_mode) == int(row["source_mode"], 8) and ident(path.read_bytes()) == {"bytes": row["bytes"], "sha256": row["sha256"]}
check("actual_private_original_mode_restoration", stat.S_IMODE(restored.stat().st_mode) == 0o700 and len(restoration["files"]) == 802 and all(r["restored_passed"] for r in recovery_rows) and restoration["executed_payloads"] is False and restoration["original_paths_written"] is False and restoration["verified_external_archives"] == ["p12_early_archive"], {"command": command, "returncode": result.returncode, "private_root_mode": "0700", "files": 802, "stdout": file_ident(OUT / "RESTORATION.stdout.json"), "stderr": file_ident(OUT / "RESTORATION.stderr.txt"), "helper": {"member": "RESTORE-RECOVERY.py", **ident(data["RESTORE-RECOVERY.py"])}})
save("RECOVERY-CHECKS.json", recovery_rows)

author = json.loads(data[P12 + "evidence/implementation/AUTHOR-RESULT.json"])
findings = [{
    "id": "P12-PACKAGE-001",
    "severity": "mandatory_factual_correction",
    "status": "open",
    "members": ["HANDOFF.md", "RECOVERY-STATUS.md"],
    "observed": ["HANDOFF attributes an original unsuccessful helper attempt and corrected attempt to corpus materialization.", "RECOVERY-STATUS says the inventory includes an initial materialization failure and corrected receipt."],
    "contradictory_evidence": {"author_failed_materialization_attempts": author["failed_materialization_attempts"], "author_materialization_passed": author["materialization"]["passed"], "reviewer_corpus_materialization": "passed once; its complete receipt is retained", "actual_reviewer_failures": "documentary review script path derivation and an overstrict branch-representation comparison"},
    "required_resolution": "Correct these two package prose descriptions to name the actual documentary review attempts, or provide exact evidence for a distinct materialization failure. Preserve this frozen attempt and its review; no technical/source change is required.",
}]
audit = {
    "schema": "ontokin.c271.p12-independent-final-package-audit/1",
    "reviewer": "/root/intake_review",
    "completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "archive": file_ident(ARCHIVE),
    "source_commit": SOURCE,
    "source_tree": TREE,
    "verdict": "structural_and_recovery_checks_passed_narrative_correction_required",
    "checks": checks,
    "groups_passed": len(checks),
    "findings": findings,
    "prompts": prompt_rows,
    "counts": {"zip_members":384,"manifest_payloads":383,"git_snapshots":316,"recovery_paths":802,"payload_bindings":732,"external_archive_bindings":70,"original_mode_0600":268,"original_mode_0644":534},
    "save_and_readback": "not_reviewed_pending_external_receipt",
    "limits": ["Final ZIP and early ZIP only were restored for this bounded online recovery inventory.", "No recursive historical/offline restoration or complete Git backup is claimed.", "Only the reviewed recovery helper executed; no restored payload or product module ran.", "The 97 controls and 175 inherited methods remain not_run; parent C271 remains blocked.", "Postfreeze package review/save/publication observations belong in a separate matching receipt."],
    "review_observation_errors": [{"kind":"display_output_truncation","detail":"A broad rg inventory included builder restoration trees, and an aggregate dependency display exceeded output limits. Neither changed files. Required current package content was inspected in bounded calls; full inventories were parsed and all bytes/hash/modes checked by the retained script."}],
}
save("AUDIT.json", audit)
report = f"""# Independent final package review — first frozen attempt

**Structural and recovery checks pass; two factual prose statements need correction before acceptance.** The exact ZIP is 1,840,636 bytes, SHA256 `{EXPECTED_HASH}`, source `{SOURCE}`, tree `{TREE}`. All {len(checks)} required technical package check groups passed.

Verified 384 safe regular ZIP members, 383 manifest payloads and all 316 Git snapshot bytes, blobs and recorded modes. Required startup instructions, active records and three selected skills are included. Both external prompts match their ZIP members. The package preserves the N57 blocker, 97/175 not-run status, open parent gates, delivery-only current action and a later fresh design clarification phase.

All 802 recovery mappings resolve exactly: 732 to included payload bytes, 70 to the already accepted early ZIP. A fresh independent private restoration verified every file's bytes and original mode: 268 files at `0600`, 534 at `0644`, under a `0700` root. No original path was written and no payload was executed. No full historical/offline restoration is claimed.

`P12-PACKAGE-001` remains open. `HANDOFF.md` describes an unsuccessful corpus-materialization helper attempt; `RECOVERY-STATUS.md` calls it an initial materialization failure. The author records no failed materialization attempts, and the reviewer corpus materialization passed. The preserved reviewer failures were documentary review script issues. Correct those two descriptions or supply exact contrary evidence. Preserve this frozen attempt and audit.

Final save/readback remains a separate external gate. No product tests, host qualification, integration or parent completion are claimed. Detailed payload, Git-source and original-mode restoration checks are retained beside this report.
"""
with (OUT / "REPORT.md").open("x", encoding="utf-8") as handle:
    handle.write(report)
print(json.dumps({"verdict":audit["verdict"],"groups_passed":len(checks),"counts":audit["counts"],"artifacts":[file_ident(OUT / n) for n in ("AUDIT.json","REPORT.md","PAYLOAD-CHECKS.json","SOURCE-CHECKS.json","RECOVERY-CHECKS.json")]},indent=2))
