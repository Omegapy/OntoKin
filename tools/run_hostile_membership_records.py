#!/usr/bin/env python3
"""Apply sixteen frozen non-GLB hostile classes to private evidence copies.

Original passing artifacts and all refused mutant bytes are retained. Transport
digests are recomputed for coherent request/response and SQLite mutations, so
those refusals also exercise independent semantic/source expectations. Untouched
files may share read-only hardlinks; every edited file is detached atomically.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

from keyed_membership_evidence import Freeze, canonical, inventory, jsonl_reader, jsonl_writer, read, save, sha, stamp
from keyed_membership_amendment import AgentAmendment


IDS = ("source-boolean", "source-diagnostic", "stage-trace", "callback-identity", "input-identity",
       "request-identity", "accepted-head", "source-bytes", "patch-span", "derived-dependency",
       "detached-origin", "selected-origin", "artifact-truncation", "artifact-slice", "store-run", "store-artifact")


def replace_bytes(path, raw):
    temporary = path.with_name(path.name + ".detached-tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def replace_json(path, value):
    replace_bytes(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode() + b"\n")


def mutate_records(path, predicate, mutation):
    temporary = path.with_name(path.name + ".detached-tmp")
    changed = None
    with jsonl_writer(temporary) as emit:
        for row in jsonl_reader(path):
            if changed is None and predicate(row):
                original = copy.deepcopy(row)
                mutation(row)
                if original == row:
                    raise ValueError("Hostile preparation did not change the selected record")
                changed = {"record_id": row["id"], "original_record_sha256": sha(canonical(original)), "mutated_record_sha256": sha(canonical(row))}
            emit(row)
    if changed is None:
        temporary.unlink()
        raise ValueError("Frozen hostile target record was not found")
    os.replace(temporary, path)
    return changed


def mutate_exchange(root, predicate, kind, mutation):
    transcript = read(root / "agent/transcript.json")
    row = next(item for item in transcript if predicate(item))
    before = copy.deepcopy(row[kind])
    mutation(row[kind])
    if before == row[kind]:
        raise ValueError("Hostile exchange mutation made no change")
    wire = json.dumps(row[kind], ensure_ascii=False, allow_nan=False).encode()
    replace_bytes(root / row[kind + "_file"], wire)
    row[kind + "_sha256"] = sha(wire)
    replace_json(root / f"agent/exchange-{row['sequence']:05}.json", row)
    replace_json(root / "agent/transcript.json", transcript)
    return {"sequence": row["sequence"], "workflow": row["workflow"], "step": row["step"],
            "logical_field_container": kind, "original_sha256": sha(canonical(before)), "mutated_sha256": sha(canonical(row[kind]))}


def mutate_store(root, workflow, function):
    summary = read(root / "summary.json")
    record = next(row for row in summary["stores"] if row["workflow"] == workflow)
    path = root / record["path"]
    original = path.read_bytes()
    replace_bytes(path, original)
    db = sqlite3.connect(path)
    try:
        db.execute("PRAGMA journal_mode=DELETE")
        detail = function(db)
        db.commit()
    finally:
        db.close()
    mutated = path.read_bytes()
    if mutated == original:
        raise ValueError("Hostile SQLite preparation did not change bytes")
    record.update(bytes=len(mutated), sha256=sha(mutated))
    replace_json(root / "summary.json", summary)
    return {"workflow": workflow, "path": record["path"], "original_sha256": sha(original),
            "mutated_sha256": sha(mutated), "transport_digest_rebound": True, "detail": detail}


def mutate(kind, root, freeze):
    if kind == "source-boolean":
        return mutate_records(root / "source-records.jsonl.gz", lambda row: row["id"] == "singleton-present",
                              lambda row: row["private"].__setitem__("observed", not row["private"]["observed"]))
    if kind == "source-diagnostic":
        return mutate_records(root / "source-records.jsonl.gz",
            lambda row: any(d.get("code") == "OKL-E-ID" for d in row.get("public", {}).get("result", {}).get("diagnostics", [])),
            lambda row: next(d for d in row["public"]["result"]["diagnostics"] if d["code"] == "OKL-E-ID").__setitem__("message", "Altered hostile diagnostic."))
    if kind == "stage-trace":
        return mutate_records(root / "native-records.jsonl.gz", lambda row: row.get("group") == "native-valid" and len(row.get("events", [])) >= 5,
                              lambda row: row["events"].pop(1))
    if kind == "callback-identity":
        return mutate_records(root / "native-records.jsonl.gz", lambda row: row.get("group") == "cancel",
                              lambda row: row.__setitem__("same_original_cancellation", False))
    if kind == "input-identity":
        path = root / "summary.json"; value = read(path); original = value["input_manifest_sha256"]
        value["input_manifest_sha256"] = "0" * 64
        replace_json(path, value)
        return {"field": "input_manifest_sha256", "original": original, "mutated": value["input_manifest_sha256"]}
    if kind == "derived-dependency":
        return mutate_records(root / "source-records.jsonl.gz", lambda row: row["id"] == "dependencies-false",
                              lambda row: row["private"]["provenance"]["members"].remove("probe.query"))
    if kind == "detached-origin":
        return mutate_records(root / "source-records.jsonl.gz", lambda row: row["id"] == "composition-map-absent",
                              lambda row: row["private"]["provenance"]["transforms"].clear())
    if kind == "selected-origin":
        return mutate_records(root / "source-records.jsonl.gz", lambda row: row["id"] == "composition-map",
                              lambda row: row["private"]["provenance"]["transforms"][0].__setitem__("key", "a"))
    if kind == "request-identity":
        return mutate_exchange(root, lambda row: row["workflow"] == "A01" and row["step"] == "create", "request",
                               lambda value: value.__setitem__("requested_level", "represented"))
    if kind == "patch-span":
        return mutate_exchange(root, lambda row: row["workflow"] == "A01" and row["step"] == "edit-inserted", "request",
                               lambda value: value["patches"][0].__setitem__("start_byte", value["patches"][0]["start_byte"] + 1))
    if kind == "artifact-slice":
        return mutate_exchange(root, lambda row: row["workflow"] == "A10" and row["step"] == "slice-0", "response",
                               lambda value: value["result"].__setitem__("offset", 1))
    if kind == "artifact-truncation":
        artifact = read(root / "summary.json")["agent_artifacts"][0]
        path = root / artifact["glb"]; raw = path.read_bytes()
        replace_bytes(path, raw[:-1])
        return {"path": artifact["glb"], "original_bytes": len(raw), "mutated_bytes": len(raw) - 1,
                "original_sha256": sha(raw), "mutated_sha256": sha(raw[:-1])}
    if kind == "accepted-head":
        revision = next(case["program_revision"] for case in freeze.representative["cases"] if case["id"] == "invalid-selected")
        def change(db):
            before = db.execute("SELECT accepted_revision FROM projects WHERE id='c088-a02'").fetchone()[0]
            db.execute("UPDATE projects SET accepted_revision=? WHERE id='c088-a02'", (revision,))
            return {"project": "c088-a02", "original": before, "mutated": revision}
        return mutate_store(root, "A02", change)
    if kind == "source-bytes":
        def change(db):
            project, revision, raw = db.execute("SELECT project_id,revision,raw FROM sources ORDER BY project_id,revision LIMIT 1").fetchone()
            payload = json.loads(bytes(raw)); payload["entry"]["source"] += "\n"
            db.execute("UPDATE sources SET raw=? WHERE project_id=? AND revision=?", (canonical(payload), project, revision))
            return {"project": project, "revision_unchanged": revision, "mutation": "append one newline to entry source"}
        return mutate_store(root, "A01", change)
    if kind == "store-run":
        def change(db):
            project, ident, descriptor = db.execute("SELECT project_id,id,descriptor FROM runs ORDER BY project_id,id LIMIT 1").fetchone()
            value = json.loads(descriptor); old = value["valid_until_seconds"]; value["valid_until_seconds"] = "0.5"
            db.execute("UPDATE runs SET descriptor=? WHERE project_id=? AND id=?", (canonical(value).decode(), project, ident))
            return {"project": project, "run_id": ident, "original_time": old, "mutated_time": "0.5"}
        return mutate_store(root, "A01", change)
    if kind == "store-artifact":
        def change(db):
            project, ident, data = db.execute("SELECT project_id,id,data FROM artifacts ORDER BY project_id,id LIMIT 1").fetchone()
            raw = bytearray(data); raw[-1] ^= 1
            db.execute("UPDATE artifacts SET data=? WHERE project_id=? AND id=?", (bytes(raw), project, ident))
            return {"project": project, "artifact_id_unchanged": ident, "mutation": "xor final artifact byte with 1"}
        return mutate_store(root, "A01", change)
    raise ValueError("Unhandled frozen hostile class")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--agent", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--observation-pass", type=Path, required=True)
    parser.add_argument("--agent-pass", type=Path, required=True)
    parser.add_argument("--agent-amendment", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    freeze = Freeze(args.inputs)
    amendment = AgentAmendment(freeze, args.agent_amendment) if args.agent_amendment else None
    if read(args.observation_pass)["status"] != "passed" or read(args.agent_pass)["status"] != "passed":
        raise ValueError("Original source/native and Agent evidence must pass independent readers first")
    if args.output.exists():
        raise ValueError("Hostile output must be fresh")
    args.output.mkdir(parents=True)
    original = {str(root): inventory(root) for root in (args.source, args.native, args.agent)}
    report = {"schema_version": "ontokin.c088-hostile-records/1", **freeze.lineage(), "started_utc": stamp(),
              "mutations": [], "failures": [], "reader_tools": [{"path": p.name, "sha256": sha(p.read_bytes())} for p in sorted(Path(__file__).parent.glob("*.py"))]}
    report["agent_amendment"] = None if amendment is None else amendment.lineage()
    frozen_ids = {row["id"] for row in read(freeze.root / "hostile-expected.json")["mutations"]}
    if not set(IDS) <= frozen_ids:
        raise ValueError("A hostile class was not independently frozen")
    for ident in IDS:
        group = "native" if ident in ("stage-trace", "callback-identity") else "source" if ident in (
            "source-boolean", "source-diagnostic", "input-identity", "derived-dependency", "detached-origin", "selected-origin") else "agent"
        source = getattr(args, group)
        destination = args.output / ident
        copied = destination / "mutant"
        destination.mkdir()
        shutil.copytree(source, copied, copy_function=os.link)
        before = inventory(copied)
        record = {"id": ident, "original_root": str(source), "mutant_root": str(copied), "logical_mutations": 1}
        try:
            record["mutation"] = mutate(ident, copied, freeze)
            after = inventory(copied)
            old = {row["path"]: row for row in before}; new = {row["path"]: row for row in after}
            record["changed_files"] = [{"path": path, "before": old.get(path), "after": new.get(path)} for path in sorted(set(old) | set(new)) if old.get(path) != new.get(path)]
            if not record["changed_files"]:
                raise ValueError("Prepared mutant has no changed bytes")
            tool = "verify_membership_agent.py" if group == "agent" else "verify_keyed_membership_observations.py"
            command = [sys.executable, str(Path(__file__).parent / tool), "--inputs", str(args.inputs), "--" + group, str(copied), "--output", str(destination / "reader")]
            if group == "agent": command += ["--checkout", str(args.checkout)]
            if group == "agent" and amendment is not None: command += ["--agent-amendment", str(args.agent_amendment)]
            env = os.environ.copy(); env["PYTHONDONTWRITEBYTECODE"] = "1"
            with (destination / "stdout.txt").open("xb") as stdout, (destination / "stderr.txt").open("xb") as stderr:
                process = subprocess.run(command, stdout=stdout, stderr=stderr, env=env, timeout=180)
            result = read(destination / "reader/result.json")
            failures = result.get("failures", [])
            reader_errors = [row for row in failures if row.get("check") in ("reader exception", "independent reader completed")]
            refused = process.returncode == 1 and result["status"] == "failed" and bool(failures) and not reader_errors
            record.update(command=command, exit_code=process.returncode, status="refused" if refused else "failed",
                          failure_count=len(failures), reader_errors=reader_errors,
                          result_sha256=sha((destination / "reader/result.json").read_bytes()))
            if not refused:
                report["failures"].append({"id": ident, "reason": "Mutation was not a completed semantic refusal"})
        except Exception as error:
            record.update(status="preparation_or_execution_error", error={"type": type(error).__name__, "message": str(error)})
            report["failures"].append({"id": ident, "error": record["error"]})
        report["mutations"].append(record)
        save(destination / "mutation.json", record)
        save(args.output / "summary-running.json", report)
    final = {str(root): inventory(root) for root in (args.source, args.native, args.agent)}
    if final != original:
        report["failures"].append({"reason": "Original evidence changed"})
    freeze.assert_unchanged()
    if amendment is not None:
        amendment.assert_unchanged()
    report.update(status="passed" if not report["failures"] else "failed", completed_utc=stamp(),
                  original_inventories_before=original, original_inventories_after=final,
                  original_artifacts_unchanged=original == final, inputs_unchanged=True)
    save(args.output / "result.json", report)
    print(json.dumps({"status": report["status"], "mutations": len(report["mutations"]), "failures": len(report["failures"])}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
