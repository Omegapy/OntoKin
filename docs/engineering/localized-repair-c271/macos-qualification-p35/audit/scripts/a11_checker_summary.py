"""W4 audit 001, a11: summary of the bound checker's 78 runs (6 --audit, 72 expect) in outputs/checker/.

Usage: a11_checker_summary.py CHECKER_DIR OUTPUT
Starts nothing (an audit hook refuses process creation).
"""
import json
import os
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)


def main():
    directory, output = sys.argv[1], sys.argv[2]
    codes = {}
    for line in open(os.path.join(directory, "exit-codes.txt")):
        cid, mode, code = line.split()
        codes[(cid, mode)] = int(code)
    rows = []
    for (cid, mode), code in codes.items():
        record = json.load(open(os.path.join(directory, "%s.%s.json" % (cid, mode))))
        rows.append({"command": cid, "mode": mode, "exit": code, "state": record["state"],
                     "predicate_set": record.get("predicate_set"),
                     "predicates": len(record["checks"].get("predicates", [])), "failed": len(record["failed"]),
                     "failed_items": [f["item"].get("rule") for f in record["failed"]][:10],
                     "flags": record["python_flags"]})
    summary = {"schema": "w4-audit-001.a11-checker-summary/1", "runs": len(rows),
               "audit_runs": [r for r in rows if r["mode"] == "audit"],
               "expect_not_met": [r for r in rows if r["mode"] == "expect" and (r["state"] != "MET" or r["exit"] != 0)],
               "expect_met": sum(1 for r in rows if r["mode"] == "expect" and r["state"] == "MET" and r["exit"] == 0),
               "expect_predicates_total": sum(r["predicates"] for r in rows if r["mode"] == "expect"),
               "rows": rows}
    data = json.dumps(summary, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print("runs", len(rows))
    for r in summary["audit_runs"]:
        print("audit", r["command"], r["exit"], r["state"], r["predicate_set"], r["predicates"], r["failed"], r["flags"])
    print("expect met", summary["expect_met"], "of", sum(1 for r in rows if r["mode"] == "expect"),
          "predicates", summary["expect_predicates_total"])
    for r in summary["expect_not_met"]:
        print("NOT MET", r["command"], r["exit"], r["state"], r["failed"], json.dumps(r["failed_items"])[:2000])


main()
