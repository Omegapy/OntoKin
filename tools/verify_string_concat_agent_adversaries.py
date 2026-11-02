#!/usr/bin/env python3
"""Exercise the two frozen hostile Agent dependency streams coherently.

These are adversarial evidence copies, never purported product observations.
Every transcript, individual exchange, raw response and durable SQLite reply is
updated together. Unchanged files remain byte-identical to the actual execution.
The retained overlay plus the exact basis manifest recovers each complete copy.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.string_concat_reference import canonical, input_lineage, load_fixtures, require, sha, ReferenceError
from tools.verify_string_concat_agent_evidence import audit, schema_validators

REFUSAL = "Complete selected typed values/original lineage differ from independently validated full inspection"


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def replace(path, raw):
    """Replace one copied hard link without modifying its original inode."""
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    temporary = path.with_name(path.name + ".c087-mutant-new")
    with temporary.open("xb") as stream:
        stream.write(raw)
    temporary.chmod(mode)
    os.replace(temporary, path)


def inventory(root):
    result = []
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "Adversary basis must contain ordinary files")
        if path.is_file():
            raw = path.read_bytes()
            result.append({"path": path.relative_to(root).as_posix(), "bytes": len(raw),
                           "sha256": sha(raw), "mode": oct(stat.S_IMODE(path.stat().st_mode))})
    return result


def prepare(basis, destination, overlay, identifier, fixtures, before):
    # Source evidence is immutable. SQLite files are always private copies even
    # though ordinary unchanged artifacts may use hard links. A live WAL is not
    # a portable standalone backup and must never enter this adversary basis.
    summary_before = json.loads((basis / "summary.json").read_bytes())
    for store in [summary_before["store"], *summary_before.get("additional_stores", [])]:
        database = basis / store["path"]
        require(not Path(str(database) + "-wal").exists() and not Path(str(database) + "-shm").exists(),
                "Adversary basis requires closed standalone SQLite backups without auxiliaries")
    def copy_file(source, target):
        return shutil.copy2(source, target) if ".sqlite3" in Path(source).name else os.link(source, target)
    shutil.copytree(basis, destination, copy_function=copy_file)
    rows = json.loads((destination / "agent/transcript.json").read_bytes())
    base = fixtures["agent_cases"]["panel-task"]["program_revision"]
    revision = base if identifier == "AE01" else fixtures["agent_cases"]["panel-task-repaired"]["program_revision"]
    identity = ["panel-task", "demo", "first"]
    selected = [row for row in rows if row["workflow"] == "A01" and row["request"]["operation"] == "inspect"
                and row["request"].get("selector") == {"kind": "object", "element_id": identity}
                and row["request"].get("program_revision") == revision]
    require(selected, "Frozen hostile stream has no actual selected inspection")
    row = selected[0]
    dependencies = row["response"]["result"]["items"][0]["values"]["renamed"]["dependencies"]
    old = copy.deepcopy(dependencies)
    matched = [item for item in dependencies if item.get("relationship") == "effective_value_dependency"
               and item.get("element_id") == identity + ["prefix"] and item.get("path") == "first.prefix"]
    require(len(matched) == 1 and matched[0]["program_revision"] == revision,
            "Actual stream lacks the exact independently frozen prefix dependency")
    if identifier == "AE01":
        dependencies.remove(matched[0])
    else:
        require(revision != base, "Stale-revision mutant requires the accepted prefix repair")
        matched[0]["program_revision"] = base
    request_id = row["request"]["request_id"]
    require(sum(candidate["request"]["request_id"] == request_id for candidate in rows) == 1,
            "Selected mutation must use a non-retried actual request")
    raw = encoded(row["response"])
    replace(destination / row["response_file"], raw)
    row["response_sha256"] = sha(raw)
    replace(destination / f"agent/exchange-{row['sequence']:04}.json", encoded(row))
    replace(destination / "agent/transcript.json", encoded(rows))
    replace(destination / "agent/transcript.jsonl", b"".join(canonical(item) + b"\n" for item in rows))
    summary = json.loads((destination / "summary.json").read_bytes())
    database = destination / summary["store"]["path"]
    replace(database, database.read_bytes())
    connection = sqlite3.connect(database)
    try:
        require(connection.execute("UPDATE requests SET response=? WHERE project_id=? AND id=?",
                    (canonical(row["response"]).decode(), row["request"]["project_id"], request_id)).rowcount == 1,
                "Adversary must replace exactly one matching durable reply")
        connection.commit()
        require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)],
                "Adversarial SQLite remains structurally valid")
    finally:
        connection.close()
    database_raw = database.read_bytes()
    summary["store"].update(bytes=len(database_raw), sha256=sha(database_raw))
    replace(destination / "summary.json", encoded(summary))
    original_inventory = json.loads((destination / "inventory.json").read_bytes())
    for item in original_inventory:
        raw = (destination / item["path"]).read_bytes()
        item.update(bytes=len(raw), sha256=sha(raw))
    replace(destination / "inventory.json", encoded(original_inventory))
    after = inventory(destination)
    before_by_path = {item["path"]: item for item in before}
    require(set(before_by_path) == {item["path"] for item in after}, "Mutation changed file membership")
    changed = [item for item in after if item != before_by_path[item["path"]]]
    wanted = {row["response_file"], f"agent/exchange-{row['sequence']:04}.json", "agent/transcript.json",
              "agent/transcript.jsonl", summary["store"]["path"], "summary.json", "inventory.json"}
    require({item["path"] for item in changed} == wanted, "Mutation affected an unprescribed evidence file")
    for item in changed:
        target = overlay / "changed-files" / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(destination / item["path"], target)
        target.chmod(int(item["mode"], 8))
    manifest = {"id": identifier, "classification": "intentionally corrupted evidence, not a product observation",
        "source_exchange": row["sequence"], "project_id": row["request"]["project_id"], "request_id": request_id,
        "program_revision": revision, "old_dependencies": old, "mutated_dependencies": dependencies,
        "basis": str(basis), "actual_mutant_workspace": str(destination), "changed_files": changed,
        "expected": "refused", "expected_semantic_refusal": REFUSAL,
        "recovery": "Verify BASIS-MANIFEST.json against the original execution; copy that complete tree, then replace only these seven paths with changed-files bytes and modes."}
    (overlay / "MUTATION.json").write_bytes(encoded(manifest))
    return manifest, row["response"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mutation-workspaces", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists() and not args.mutation_workspaces.exists(), "Fresh output and mutation workspaces required")
    args.output.mkdir(parents=True); args.mutation_workspaces.mkdir(parents=True)
    basis = args.results.resolve(); fixtures = load_fixtures(args.fixtures)
    requirements = fixtures["agent_adversaries"]
    require([item["id"] for item in requirements["requirements"]] == ["AE01", "AE02"], "Wrong frozen Agent hostile inventory")
    before = inventory(basis)
    (args.output / "BASIS-MANIFEST.json").write_bytes(encoded(before))
    prepared = []
    for item in requirements["requirements"]:
        overlay = args.output / item["id"]; overlay.mkdir()
        prepared.append(prepare(basis, args.mutation_workspaces / item["id"], overlay, item["id"], fixtures, before))
    # Both complete coherent mutations and expected refusals precede every audit.
    (args.output / "EXPECTED-REFUSALS.json").write_bytes(encoded({"requirements": requirements,
        "mutations": [item[0] for item in prepared], "basis_manifest_sha256": sha(encoded(before))}))
    positive = audit(basis, fixtures)
    (args.output / "POSITIVE-BASELINE-AUDIT.json").write_bytes(encoded(positive))
    validators = schema_validators(fixtures["repository"])
    results = []
    for manifest, response in prepared:
        require(not list(validators["response.schema.json"].iter_errors(response)), "Hostile response must remain schema-valid")
        try:
            audit(Path(manifest["actual_mutant_workspace"]), fixtures)
        except ReferenceError as error:
            result = {"id": manifest["id"], "status": "passed" if str(error) == REFUSAL else "failed",
                      "schema_valid": True, "rejection": str(error), "traceback": traceback.format_exc()}
        else:
            result = {"id": manifest["id"], "status": "failed", "reason": "Hostile dependency stream accepted"}
        results.append(result)
        (args.output / manifest["id"] / "AUDIT.json").write_bytes(encoded(result))
    require(inventory(basis) == before, "Original actual evidence changed during adversarial checks")
    report = {"schema_version": "ontokin.c087-independent-agent-adversaries/0.1", **input_lineage(fixtures),
        "status": "passed" if all(item["status"] == "passed" for item in results) else "failed",
        "reader_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "positive_original_accepted": positive["status"] == "passed", "original_evidence_unchanged": True,
        "mutations": results, "expected_isolated_refusals": 2, "actual_refusals": sum(item["status"] == "passed" for item in results),
        "source_runtime_or_frozen_inputs_changed": False, "release_acceptance": False}
    (args.output / "RESULT.json").write_bytes(encoded(report))
    print(json.dumps({"status": report["status"], "refusals": report["actual_refusals"]}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
