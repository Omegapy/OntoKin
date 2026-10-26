#!/usr/bin/env python3
"""Append exact C047 validation records; preserve the independently reviewed core."""
import datetime
import hashlib
import json
import pathlib
import re
import shutil
import subprocess

BASE = pathlib.Path(__file__).resolve().parents[1]
ROOT = BASE / "OntoKin"
OUT = pathlib.Path(__file__).resolve().parent
REL = pathlib.Path("docs/engineering/reach-recording-validation-2026-10-23")
DEST = ROOT / REL / "checkpoint-047-validation"
CORE = "7d2c118f5cc5ca141f2092b68d02b23fd933b571"
TREE = "219ceb20170a5dc3393bc9e7383b374193ce6c02"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def read(path):
    return json.loads(path.read_text())

def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()

def binding(path, name):
    data = path.read_bytes()
    return {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "sha": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(), "mode": "100755" if path.stat().st_mode & 0o111 else "100644", "type": "blob"}

def main():
    started = now()
    window = read(OUT / "window.json")
    assert datetime.datetime.fromisoformat(window["active_after"]) <= datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat(window["expires_at"])
    assert git("rev-parse", "HEAD") == CORE and git("rev-parse", "HEAD^{tree}") == TREE
    assert git("status", "--porcelain") == ""
    assert not DEST.exists()
    root_result = read(BASE / "c047-validation/result.json")
    review = read(BASE / "c047-final-review/result.json")
    closure = read(BASE / "c047-final-review/window-closure.json")
    assert root_result["status"] == review["status"] == "passed"
    assert root_result["checks_passed"] == 53 and review["checks_passed"] == review["checks_total"] == 62
    assert root_result["source_commit"] == review["core_commit"] == closure["core_commit"] == CORE
    assert root_result["inputs_stable"] and review["inputs_stable"] and review["findings"] == []
    assert datetime.datetime.fromisoformat(closure["closed_utc"]) < datetime.datetime.fromisoformat(window["active_after"])
    assert hashlib.sha256((BASE / "c047-final-review/result.json").read_bytes()).hexdigest() == "47fe5dbc786797a2b6918bba566baeca4ebae6d8ec354d79664e6710bd29862d"
    copies = []
    groups = [(BASE / "c047-validation", "published-core"), (BASE / "c047-publication", "publication"), (BASE / "c047-final-review", "independent-review"), (OUT, "finalization")]
    finalization_names = {"window.json", "preflight.json", "finalize_appendix.py", "verify_remote_final.py", "preparation-disclosure.json"}
    for source, group in groups:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            if source == OUT and str(relative) not in finalization_names:
                continue
            if path.name == "checkpoint-047-evidence.zip":
                continue
            assert ".private." not in path.name and path.suffix.lower() not in (".md", ".html", ".htm")
            assert not path.is_symlink()
            target = DEST / group / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            assert not target.exists()
            shutil.copy2(path, target)
            assert target.read_bytes() == path.read_bytes()
            row = binding(target, str(target.relative_to(ROOT)))
            row["original_path"] = str(path.relative_to(BASE))
            copies.append(row)
    remote = read(BASE / "c047-publication/core-remote-tree.json")
    assert remote["sha"] == TREE and remote["truncated"] is False
    core = [x for x in remote["tree"] if x["type"] == "blob"]
    assert len(core) == 2596
    for row in core:
        actual = binding(ROOT / row["path"], row["path"])
        assert (actual["sha"], actual["bytes"], actual["mode"]) == (row["sha"], row["size"], row["mode"])
    patterns = [rb"gh[pousr]_[A-Za-z0-9]{30,}", rb"github_pat_[A-Za-z0-9_]{30,}", rb"AKIA[0-9A-Z]{16}", rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    matches = []
    for row in copies:
        data = (ROOT / row["path"]).read_bytes()
        for i, pattern in enumerate(patterns):
            if re.search(pattern, data):
                matches.append({"path": row["path"], "pattern_index": i})
    assert not matches
    completed_checks = now()
    assert datetime.datetime.fromisoformat(completed_checks) < datetime.datetime.fromisoformat(window["expires_at"])
    summary = {
        "schema": "ontokin.checkpoint047-validation-appendix/0.1",
        "status": "passed for the named diagnostic and metadata scope; product remains failed",
        "core_commit": CORE, "core_tree": TREE,
        "original_pair_source_commit": "48b5d381a0f86d9706a109b78e2ce52eb0d287f0",
        "original_pair_source_tree": "33ac0caa77528432d18132a1e606d1e4fbd7ab80",
        "appendix_started_at": started, "appendix_copy_and_source_checks_finished_at": completed_checks,
        "window": window,
        "published_core_validation": {"path": "checkpoint-047-validation/published-core/result.json", "sha256": hashlib.sha256((BASE / "c047-validation/result.json").read_bytes()).hexdigest(), "checks_passed": 53, "files": 2596, "bytes": 524662681, "inputs_stable": True, "documentation_exit": 0, "documentation": {"sources": 29, "sections": 233, "documents": 208, "local_links": 1671, "anchors": 92, "failures": 0}},
        "independent_published_core_review": {"path": "checkpoint-047-validation/independent-review/result.json", "sha256": closure["result"]["sha256"], "review_path": "checkpoint-047-validation/independent-review/review.txt", "review_sha256": closure["review"]["sha256"], "checks_passed": 62, "checks_total": 62, "input_files": 3048, "input_bytes": 711675411, "inputs_stable": True, "findings": [], "prior_roles": review["prior_role_disclosure"], "unsuccessful_attempts_preserved": review["failed_final_audit_attempts"], "scope": "Independent audit covers the exact published core; the later containing appendix is checked by root, not claimed independently audited."},
        "original_pair": {"stock_exit": 1, "capture_exit": 1, "shared_operations_each": 100001, "reach_operations_each": 95767, "work_categories": 288, "key_calls": 154, "snapshots": 311, "snapshot_bytes": 122526082, "independent_evidence_assertions": 61593, "assertions_are_runtime_tests": False, "audit_first_failed_clock_formula_attempt_preserved": True, "stock_request_seconds": 2.175590550999914, "captured_request_seconds": 5.610394618997816, "elapsed_neutrality": False, "benchmark": False, "glb_accepted": False},
        "current_lifetime": {"checks_passed": 27, "input_files": 325, "interval": "key 0 entry through key 153 exception snapshot before outer cleanup", "reader_entries_initial": 112, "reader_entries_final": 165, "capacity": 256, "capacity_eviction_in_interval": False, "initial_coefficient_keys": 7, "new_completed_coefficient_keys": 5, "failed_key": ["series_coefficients", 32768, 129, 14], "failed_key_previously_completed_and_retained_in_interval": False, "proof": "Current native source control flow plus captured data, not boundary occupancy alone or an internal mutation event trace.", "excluded": ["setup before key 0", "outer cleanup", "unexecuted failed tail", "arbitrary hostile or reentrant requests", "exact hit counts and intra-key event order"]},
        "core_archive": {"parts": 18, "bytes": 15483218, "members": 414, "member_bytes": 167310502, "exact_member_crc_mode_size_hash_and_bytes_passed": True, "archive_reexecuted_in_finalization": False},
        "appendix_preservation": {"core_files_unchanged": 2596, "existing_markdown_html_unchanged": True, "new_markdown_html_files": 0, "documentation_rerun_needed": False, "all_copies_byte_identical": True, "copied_files": len(copies), "copied_bytes": sum(x["bytes"] for x in copies), "credential_scan": {"defined_patterns": 4, "matches": [], "universal_secret_absence_claim": False}, "excluded_duplicate_archive": "Already published as the 18 unchanged core parts.", "manifest_excludes_its_containing_summary": True},
        "open_status": {"original28_passed": 24, "original28_total": 28, "unresolved_cases": ["P11", "P16", "P23", "L03"], "C035": "held including prior adverse timing", "runtime_change": False, "runtime_candidate_selected": False, "release_acceptance": False, "main_integration": False, "full_goal_complete": False},
        "next_step": "C048 source and retained-data feasibility review of general exact coefficient construction on genuine misses, with complete charge and storage accounting and independent numerical/authority/cost review before implementation.",
        "final_identity_rule": "The final containing commit/tree and draft PR are established by immutable remote byte readback, expected-core nonforce ref update and final Issue #26 closure. No self-containing final commit hash is fabricated here.",
        "copied_members": copies,
    }
    summary_path = ROOT / REL / "checkpoint-047-validation.json"
    write(summary_path, summary)
    new_files = copies + [binding(summary_path, str(summary_path.relative_to(ROOT)))]
    git("add", "--", str(REL / "checkpoint-047-validation"), str(REL / "checkpoint-047-validation.json"))
    staged = git("diff", "--cached", "--name-status").splitlines()
    assert {x.split("\t", 1)[1] for x in staged} == {x["path"] for x in new_files}
    assert all(x.startswith("A\t") for x in staged)
    whitespace = subprocess.run(["git", "diff", "--cached", "--check"], cwd=ROOT, capture_output=True)
    (OUT / "appendix-whitespace.stdout").write_bytes(whitespace.stdout)
    (OUT / "appendix-whitespace.stderr").write_bytes(whitespace.stderr)
    assert whitespace.returncode == 0
    finished = now()
    assert datetime.datetime.fromisoformat(finished) < datetime.datetime.fromisoformat(window["expires_at"])
    plan = {"parent": CORE, "base_tree": TREE, "tree": git("write-tree"), "branch": git("symbolic-ref", "--short", "HEAD"), "created_at": finished, "all_core_files_preserved": True, "files": [{k: v for k, v in x.items() if k != "original_path"} for x in sorted(new_files, key=lambda x: x["path"])]}
    write(OUT / "final-plan.json", plan)
    receipt = {"schema": "ontokin.c047-appendix-preparation/0.1", "status": "passed", "started_at": started, "finished_at": finished, "core_commit": CORE, "core_tree": TREE, "target_tree": plan["tree"], "added_files": len(new_files), "added_bytes": sum(x["bytes"] for x in new_files), "all_core_files_preserved": True, "new_markdown_html_files": 0, "copies_byte_identical": True, "whitespace_exit": whitespace.returncode, "product_execution": False}
    write(OUT / "appendix-preparation-receipt.json", receipt)
    print(json.dumps(receipt))

if __name__ == "__main__":
    main()
