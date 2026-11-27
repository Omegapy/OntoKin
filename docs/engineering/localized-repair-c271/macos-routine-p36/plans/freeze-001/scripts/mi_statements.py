"""W2 (freeze 001): the not-passing records of MI's retained per-module runs, as attribution statements.

Usage: python3 -I -S -B mi_statements.py OUTPUT COLLECT_RECORD...

Each COLLECT_RECORD is an output of the MR collector (unit_log_outcomes.py collect) on one of MI's per-module
logs, run as "python -B -m unittest -v tests.<module>" from the worktree root. The routine runs the same module
as a top-level module (discover -s tests), so each raw ID loses its "tests." prefix. The statement of each
not-passing test is built exactly as the comparator's record_statement builds it (unit_log_outcomes.py
lines 1188-1201), in raw form. Every text is scanned for content that names a place or a run (an absolute
path, a temporary name, the "tests." prefix, a process number); a statement with such content is marked
for review. It starts no process and writes only OUTPUT (absent).
"""
import json
import os
import re
import sys

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
output, records = sys.argv[1], sys.argv[2:]
if os.path.lexists(output):
    sys.stderr.write("refused: output exists\n")
    raise SystemExit(2)
NOT_PASSING = {"failure", "error", "unexpected_success"}
VARIABLE = [("absolute_path", re.compile(r"(?:^|[\s'\"(\[=:,])/(?:Volumes|private|var|tmp|Users|opt|Library|System)/")),
            ("temporary_name", re.compile(r"\btmp[a-z0-9_]{8}\b")),
            ("tests_prefix", re.compile(r"\btests\.test_")),
            ("pid_like", re.compile(r"\b(?:pid|PID|process)\D{0,12}\d{3,7}\b")),
            ("hex_digest", re.compile(r"\b[0-9a-f]{32,64}\b")),
            ("time_like", re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b|\b20\d\d-\d\d-\d\dT"))]


def statement(row):
    events = [event for run in row["runs"] for event in run["events"]]
    own = []
    for event in events:
        item = {"status": event["status"]}
        if event["status"] in ("FAIL", "ERROR"):
            item["reason_first_line"] = event.get("reason_first_line")
        elif event["status"] == "skipped":
            item["skip_reason"] = event.get("skip_reason")
        own.append(item)
    return {"outcome": row["outcome"], "occurrences": row["occurrences"], "events": own,
            "failing_subtests": [{"subtest": e["subtest"], "status": e["status"], "reason_first_line": e.get("reason_first_line")}
                                 for e in row.get("failing_subtests", [])],
            "skipped_subtests": [{"subtest": e["subtest"], "skip_reason": e["skip_reason"]} for e in row.get("skipped_subtests", [])]}


rows, sources = [], []
for path in records:
    record = json.load(open(path, encoding="utf-8"))
    sources.append({"record": os.path.basename(path), "log_sha256": record["input"]["log"]["sha256"],
                    "ran": record["footer"]["ran"], "by_outcome": record["counts"]["by_outcome"]})
    for row in record["tests"] + record["fixtures"]:
        if row["outcome"] not in NOT_PASSING and not (row["kind"] == "fixture" and row["outcome"] == "error"):
            continue
        raw_id = row["id"]
        routine_id = raw_id[len("tests."):] if raw_id.startswith("tests.") else raw_id
        if row["kind"] == "fixture":
            routine_id = raw_id.replace("(tests.", "(")
        item = {"mi_id": raw_id, "id": routine_id, "kind": row["kind"], "statement": statement(row) if row["kind"] == "test" else
                {"outcome": row["outcome"], "occurrences": row["occurrences"],
                 "events": [{"status": e["status"], **({"reason_first_line": e.get("reason_first_line")} if e["status"] == "ERROR" else {})}
                            for e in row["events"]], "failing_subtests": [], "skipped_subtests": []}}
        texts = [e.get("reason_first_line") or "" for e in item["statement"]["events"]]
        texts += [e["subtest"] + " " + (e.get("reason_first_line") or "") for e in item["statement"]["failing_subtests"]]
        flags = sorted({name for name, pattern in VARIABLE for text in texts if pattern.search(text)})
        item["variable_content"] = flags
        item["source_log_sha256"] = record["input"]["log"]["sha256"]
        rows.append(item)
document = {"schema": "ontokin.c271.p36-w2-freeze-mi-statements/1", "sources": sources, "not_passing": len(rows),
            "with_variable_content": sum(1 for row in rows if row["variable_content"]), "rows": rows}
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    stream.write(json.dumps(document, indent=1, sort_keys=True) + "\n")
print(json.dumps({"not_passing": len(rows), "with_variable_content": document["with_variable_content"]}))
for row in rows:
    if row["variable_content"]:
        print(row["id"], row["variable_content"])
