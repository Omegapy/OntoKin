#!/usr/bin/env python3
"""Exercise the independent A08 audit against bounded copies of real evidence."""
from __future__ import annotations

import argparse
import base64
import copy
import gzip
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import traceback

from audit_torque_artifact_loop import Audit, ROOT, canonical, digest, file_digest, read, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir()
    args.run = args.run.resolve()
    original_paths = [args.run / name for name in ("artifact-size.json", "exchanges.jsonl.gz", "retrieved.glb", "retrieved-label.png", "store/torque-program-agent.sqlite3")]
    completion = args.run / "artifact-completion.json"
    if completion.exists(): original_paths.append(completion)
    before = {str(path): {"bytes": path.stat().st_size, "sha256": file_digest(path)} for path in original_paths}
    if (args.run / "store/torque-program-agent.sqlite3").stat().st_size > 16*1024*1024:
        raise ValueError("Use an actual completed 65,536-byte loop for this bounded hostile-copy test")
    with gzip.open(args.run / "exchanges.jsonl.gz", "rb") as stream:
        raw_lines = list(stream)
    if len(raw_lines) > 1000:
        raise ValueError("The hostile-copy proof is bounded to 1,000 actual exchanges")
    records = [json.loads(line) for line in raw_lines]
    positive_output = args.output / "original-control"
    positive_output.mkdir()
    positive = Audit(argparse.Namespace(run=args.run, output=positive_output, source_root=args.source_root, allow_incomplete=False)).run()
    assert positive["complete_frozen_loop"]
    cases = ["response-only", "wrong-returned-byte-both", "offset-skipped-both", "raised-budget-both",
             "row-payload-identity-both", "noncanonical-request", "transcript-row-removed", "extra-durable-row",
             "duplicate-json-member", "missing-final-newline", "artifact-tail-corruption", "source-module-corruption",
             "unaccepted-source", "wrong-png-byte-both", "reconstructed-glb-corruption", "incomplete-prefix",
             "request-float-integer-both", "request-bool-integer-both", "boolean-transcript-index",
             "oversized-transcript-record", "wrong-request-engine", "wrong-run-implementation"]
    required_errors = {
        "response-only": "Every complete response equals its exact durable serialization",
        "wrong-returned-byte-both": "Every actual artifact range equals stored bytes",
        "offset-skipped-both": "Every frozen chunk request uses actual decoded sequential offset",
        "raised-budget-both": "Every actual request retains frozen allocation, inherited defaults and implementation",
        "row-payload-identity-both": "Every stored payload binds its original row identity",
        "noncanonical-request": "Every exact canonical request and SHA equals the durable receipt",
        "transcript-row-removed": "Actual sequential request and transcript positions",
        "extra-durable-row": "Every durable row has one complete original transcript exchange",
        "duplicate-json-member": "Duplicate JSON member: index",
        "missing-final-newline": "Bounded complete original transcript record",
        "artifact-tail-corruption": "Actual full artifact bytes and durable provenance identity",
        "source-module-corruption": "Exact frozen source and asset payload stored without normalization",
        "unaccepted-source": "Actual accepted immutable source row",
        "wrong-png-byte-both": "Every actual PNG range equals frozen original bytes",
        "reconstructed-glb-corruption": "Exact independently reconstructed retained GLB bytes",
        "incomplete-prefix": "All required chunk/EOF/PNG requests executed",
        "request-float-integer-both": "Every frozen chunk request uses actual decoded sequential offset",
        "request-bool-integer-both": "Every frozen chunk request uses actual decoded sequential offset",
        "boolean-transcript-index": "Actual sequential request and transcript positions",
        "oversized-transcript-record": "Bounded complete original transcript record",
        "wrong-request-engine": "Every durable request is bound to its actual producer implementation",
        "wrong-run-implementation": "Actual run implementation equals its producer artifact implementation",
    }
    results = []
    for name in cases:
        directory = args.output / name
        directory.mkdir()
        run = directory / "mutated-copy"
        run.mkdir()
        (run / "store").mkdir()
        for path in original_paths:
            shutil.copyfile(path, run / path.relative_to(args.run))
        materialized = copy.deepcopy(records)
        database = run / "store/torque-program-agent.sqlite3"
        def update_pair(db, index):
            row = materialized[index]
            request = canonical(row["request"])
            response = canonical(row["response"])
            db.execute("UPDATE requests SET payload=?,digest=?,response=?,state=? WHERE sequence=?",
                       (request, digest(request.encode()), response, row["response"]["status"], index+1))
            if "request_canonical_sha256" in row:
                row["request_canonical_sha256"] = digest(request.encode())
        with sqlite3.connect(database) as db:
            if name == "response-only":
                response = copy.deepcopy(materialized[2]["response"])
                response["result"]["offset"] = 17
                db.execute("UPDATE requests SET response=? WHERE sequence=3", (canonical(response),))
            elif name == "wrong-returned-byte-both":
                raw = bytearray(base64.b64decode(materialized[2]["response"]["result"]["data_base64"]))
                raw[0] ^= 1
                materialized[2]["response"]["result"]["data_base64"] = base64.b64encode(raw).decode()
                update_pair(db, 2)
            elif name == "offset-skipped-both":
                materialized[2]["request"]["offset"] = 17
                materialized[2]["response"]["result"]["offset"] = 17
                update_pair(db, 2)
            elif name == "raised-budget-both":
                materialized[2]["response"]["execution_budget"]["effective"]["max_operations"] = 2000000
                update_pair(db, 2)
            elif name == "row-payload-identity-both":
                materialized[2]["request"]["project_id"] += "-changed"
                update_pair(db, 2)
            elif name == "noncanonical-request":
                raw = " " + canonical(materialized[2]["request"])
                db.execute("UPDATE requests SET payload=?,digest=? WHERE sequence=3", (raw, digest(raw.encode())))
            elif name == "transcript-row-removed":
                del materialized[2]
            elif name == "extra-durable-row":
                db.execute("INSERT INTO requests(project_id,id,operation,digest,payload,state,engine,response,cancel_requested,owner,created,updated) SELECT project_id,id||'-extra',operation,digest,payload,state,engine,response,cancel_requested,owner,created,updated FROM requests WHERE sequence=3")
            elif name == "artifact-tail-corruption":
                raw = bytearray(db.execute("SELECT data FROM artifacts").fetchone()[0])
                raw[-1] ^= 1
                db.execute("UPDATE artifacts SET data=?", (bytes(raw),))
            elif name == "source-module-corruption":
                source = json.loads(db.execute("SELECT raw FROM sources").fetchone()[0])
                source["modules"][0]["source"] += "\n"
                db.execute("UPDATE sources SET raw=?", (canonical(source).encode(),))
            elif name == "unaccepted-source":
                db.execute("UPDATE sources SET accepted_once=0")
            elif name == "wrong-png-byte-both":
                index = next(i for i, row in enumerate(materialized) if row["request"]["operation"] == "inspect")
                raw = bytearray(base64.b64decode(materialized[index]["response"]["result"]["data_base64"]))
                raw[0] ^= 1
                materialized[index]["response"]["result"]["data_base64"] = base64.b64encode(raw).decode()
                update_pair(db, index)
            elif name == "reconstructed-glb-corruption":
                path = run / "retrieved.glb"
                raw = bytearray(path.read_bytes())
                raw[-1] ^= 1
                path.write_bytes(raw)
            elif name == "incomplete-prefix":
                materialized = materialized[:4]
                db.execute("DELETE FROM requests WHERE sequence>4")
                prefix = sum(len(base64.b64decode(row["response"]["result"]["data_base64"])) for row in materialized[2:])
                path = run / "retrieved.glb"
                path.write_bytes(path.read_bytes()[:prefix])
            elif name in ("request-float-integer-both", "request-bool-integer-both"):
                materialized[2]["request"]["offset"] = 0.0 if name == "request-float-integer-both" else False
                update_pair(db, 2)
            elif name == "boolean-transcript-index":
                materialized[0]["index"] = True
            elif name == "wrong-request-engine":
                db.execute("UPDATE requests SET engine=? WHERE sequence=3", ('{"name":"forged-implementation"}',))
            elif name == "wrong-run-implementation":
                descriptor = json.loads(db.execute("SELECT descriptor FROM runs").fetchone()[0])
                descriptor["implementation"] = {"name": "forged-implementation"}
                db.execute("UPDATE runs SET descriptor=?", (canonical(descriptor),))
        db.close()
        lines = [canonical(row).encode()+b"\n" for row in materialized]
        if name == "duplicate-json-member":
            lines[2] = b'{"index":3,'+lines[2][1:]
        elif name == "missing-final-newline":
            lines[-1] = lines[-1][:-1]
        elif name == "oversized-transcript-record":
            lines[0] = b" " * (8*1024*1024+1) + lines[0]
        with gzip.open(run / "exchanges.jsonl.gz", "wb") as stream:
            for line in lines:
                stream.write(line)
        output = directory / "audit"
        output.mkdir()
        audit = Audit(argparse.Namespace(run=run, output=output, source_root=args.source_root, allow_incomplete=False))
        try:
            audit.run()
        except (AssertionError, ValueError) as error:
            result = {"case": name, "status": "passed" if str(error) == required_errors[name] else "failed",
                      "observed": "refused", "error": str(error), "required_error": required_errors[name],
                      "checks_before_refusal": audit.checks}
            write(output / "EXPECTED-REFUSAL.json", {**result, "traceback": traceback.format_exc(),
                "mutated_database_sha256": file_digest(database), "mutated_transcript_sha256": file_digest(run / "exchanges.jsonl.gz")})
        else:
            result = {"case": name, "status": "failed", "observed": "accepted_hostile_copy"}
        results.append(result)
        print(json.dumps(result), flush=True)
    after = {str(path): {"bytes": path.stat().st_size, "sha256": file_digest(path)} for path in original_paths}
    unchanged = before == after
    passed = all(row["status"] == "passed" for row in results) and unchanged
    write(args.output / "summary.json", {"status": "passed" if passed else "failed", "positive_complete_control": positive,
        "hostile_copies": results, "originals_unchanged": unchanged, "originals": before,
        "driver_sha256": file_digest(Path(__file__)), "auditor_sha256": file_digest(Path(__file__).with_name("audit_torque_artifact_loop.py")),
        "argv": sys.argv, "scope": "One actual complete original and explicitly mutated bounded copies; each refusal is observed at its specified check, not inferred from a producer flag"})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
