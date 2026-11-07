#!/usr/bin/env python3
"""Independently test the A08 auditor with coherent SQLite/transcript mutations."""
import argparse
from contextlib import closing
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auditor", type=Path, required=True)
    parser.add_argument("--seed-run", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    variants = ("control", "boolean-request-max-bytes", "foreign-request-engine",
                "negative-consumed-work", "negative-elapsed", "boolean-response-offset",
                "boolean-next-offset", "integer-truncated", "float-budget-limit",
                "boolean-size-max-bytes", "oversized-transcript-line")
    rows = []
    for variant in variants:
        target = args.output / variant
        target.mkdir()
        copied = target / "input"
        shutil.copytree(args.seed_run, copied, ignore=shutil.ignore_patterns("store"))
        (copied / "store").mkdir()
        database = copied / "store/torque-program-agent.sqlite3"
        with closing(sqlite3.connect("file:" + str(args.seed_run / "store/torque-program-agent.sqlite3") + "?mode=ro", uri=True)) as src:
            with closing(sqlite3.connect(database)) as dst:
                src.backup(dst)
        with gzip.open(copied / "exchanges.jsonl.gz", "rb") as stream:
            exchanges = [json.loads(line) for line in stream]
        if len(exchanges) != 3 or exchanges[2]["request"]["max_bytes"] != 1:
            raise ValueError("Review requires an actual one-chunk, one-byte A08 prefix")
        changed = exchanges[2]
        request, response = changed["request"], changed["response"]
        if variant == "boolean-request-max-bytes":
            request["max_bytes"] = True
        elif variant == "negative-consumed-work":
            response["execution_budget"]["consumed_operations"] = -1
        elif variant == "negative-elapsed":
            response["execution_budget"]["elapsed_ms"] = -1
        elif variant == "boolean-response-offset":
            response["result"]["offset"] = False
        elif variant == "boolean-next-offset":
            response["result"]["next_offset"] = True
        elif variant == "integer-truncated":
            response["truncated"] = 1
        elif variant == "float-budget-limit":
            response["execution_budget"]["effective"]["max_operations"] = 1000000.0
        elif variant == "boolean-size-max-bytes":
            path = copied / "artifact-size.json"
            size = json.loads(path.read_bytes())
            size["max_bytes"] = True
            path.write_text(canonical(size) + "\n")
        request_text, response_text = canonical(request), canonical(response)
        request_sha = hashlib.sha256(request_text.encode()).hexdigest()
        if "request_canonical_sha256" in changed:
            changed["request_canonical_sha256"] = request_sha
        with closing(sqlite3.connect(database)) as db:
            with db:
                db.execute("UPDATE requests SET payload=?,digest=?,response=? WHERE sequence=3",
                           (request_text, request_sha, response_text))
                if variant == "foreign-request-engine":
                    db.execute("UPDATE requests SET engine='{}' WHERE sequence=3")
        with gzip.open(copied / "exchanges.jsonl.gz", "wb") as stream:
            if variant == "oversized-transcript-line":
                stream.write(b" " * (9 * 1024 * 1024) + b"\n")
            else:
                for exchange in exchanges:
                    stream.write((canonical(exchange) + "\n").encode())
        command = [sys.executable, str(args.auditor), "--run", str(copied),
                   "--output", str(target / "audit"), "--source-root", str(args.source_root), "--allow-incomplete"]
        completed = subprocess.run(command, capture_output=True, text=True)
        (target / "stdout.log").write_text(completed.stdout)
        (target / "stderr.log").write_text(completed.stderr)
        expected = 0 if variant == "control" else 1
        rows.append({"case": variant, "exit_code": completed.returncode, "expected_exit_code": expected,
                     "passed": completed.returncode == expected, "argv": command,
                     "database_sha256": hashlib.sha256(database.read_bytes()).hexdigest(),
                     "transcript_sha256": hashlib.sha256((copied / "exchanges.jsonl.gz").read_bytes()).hexdigest()})
    result = {"status": "passed" if all(row["passed"] for row in rows) else "failed",
              "scope": "Original prefix control plus independently coherent protocol/provenance/number mutations; no production imports.",
              "auditor": str(args.auditor), "auditor_sha256": hashlib.sha256(args.auditor.read_bytes()).hexdigest(),
              "seed_run": str(args.seed_run), "results": rows}
    (args.output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "cases": len(rows),
                      "failed_cases": [row["case"] for row in rows if not row["passed"]]}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
