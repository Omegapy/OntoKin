"""W3 plan review 001, s08: checks the two review records, scans OUT for private terms, writes SHA256SUMS.txt.

The private terms are given on the command line (--term), so that this file holds none. The scan
covers every file in OUT except SHA256SUMS.txt and outputs/plan-indented.json, the declared reading
copy of the plan with its machine paths, for which only the count of matches is reported.

python3 -I -S -B s08_report_check.py --out OUT --plan P --w2 DIR [--term TEXT ...] [--label NAME=PATH ...]
    --output OUTPUT
"""
import argparse
import hashlib
import os
import re
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3_common as common  # noqa: E402
sys.path.pop(0)

READING_COPY = "outputs/plan-indented.json"


def files_below(root):
    found, stack = [], [""]
    while stack:
        rel = stack.pop()
        for name in sorted(os.listdir(root + ("/" + rel if rel else ""))):
            sub = rel + "/" + name if rel else name
            info = os.lstat(root + "/" + sub)
            if stat.S_ISDIR(info.st_mode):
                stack.append(sub)
            elif stat.S_ISREG(info.st_mode):
                found.append(sub)
            else:
                raise SystemExit("unexpected entry " + sub)
    return sorted(found)


def main():
    common.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--w2", required=True)
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    checks = common.Checks()
    record_raw = common.read_bytes(args.out + "/PLAN-REVIEW-001.json")[0]
    record = common.strict_loads(record_raw)
    markdown = common.read_bytes(args.out + "/PLAN-REVIEW-001.md")[0].decode("utf-8")
    plan_sha = common.read_bytes(args.plan, keep=False)[1]["sha256"]
    checks.add("S-01", record["verdict"] in ("ACCEPT", "ACCEPT_WITH_NONMANDATORY_FINDINGS",
                                             "REJECT_WITH_MANDATORY_FINDINGS")
               and record["verdict"] == "ACCEPT_WITH_NONMANDATORY_FINDINGS"
               and "**ACCEPT_WITH_NONMANDATORY_FINDINGS.**" in markdown.split("## Context")[0],
               "both records state the same verdict, first in the Markdown record", record["verdict"])
    checks.add("S-02", record["plan"]["sha256"] == plan_sha and markdown.count(plan_sha) >= 2,
               "the plan digest in both records equals my hash of the plan file now", plan_sha)
    inventories = {"python": "python-inventory-001.json", "source": "source-inventory-001.json",
                   "dependencies": "dependencies-inventory-001.json"}
    equal = {key: record["recomputed_inventories"][key]["sha256"] ==
             common.read_bytes(args.w2 + "/" + name, keep=False)[1]["sha256"] for key, name in inventories.items()}
    checks.add("S-03", all(equal.values()) and all(record["recomputed_inventories"][key]["sha256"] in markdown
                                                   for key in inventories),
               "the three recomputed digests in both records equal the frozen files' digests", equal)
    findings = record["findings"]
    checks.add("S-04", [row["id"] for row in findings] == ["PR-0%d" % n for n in range(1, 7)]
               and not any(row["mandatory"] for row in findings) and record["mandatory_findings"] == []
               and all(set(row) == {"id", "mandatory", "location", "statement", "required_change"} for row in findings)
               and all("### " + row["id"] + " (nonmandatory)" in markdown for row in findings)
               and sorted(record["answers"]) == ["Q-%d" % n for n in range(1, 9)],
               "six nonmandatory findings with their five fields, in both records; answers to Q-1 to Q-8",
               [row["id"] for row in findings])
    output_rows = {}
    for rel, value in record["files"]["outputs"].items():
        if re.fullmatch(r"[0-9a-f]{64}", value):
            output_rows[rel] = value == common.read_bytes(args.out + "/" + rel, keep=False)[1]["sha256"]
    checks.add("S-05", all(output_rows.values()) and len(output_rows) == 12,
               "every output digest that the JSON record lists equals its file", output_rows)
    patterns = [re.compile(re.escape(term), re.IGNORECASE) for term in args.term]
    hits, copy_hits = {}, 0
    for rel in files_below(args.out):
        if rel == "SHA256SUMS.txt":
            continue
        text = common.read_bytes(args.out + "/" + rel)[0].decode("utf-8", "replace")
        count = sum(len(pattern.findall(text)) for pattern in patterns)
        if rel == READING_COPY:
            copy_hits = count
        elif count:
            hits[rel] = count
    checks.add("S-06", not hits and len(args.term) > 0,
               "no file in OUT holds a private term, apart from the declared reading copy of the plan",
               {"terms": len(args.term), "files_with_hits": hits, "reading_copy_hits": copy_hits})
    out = {"schema": "w3.p36.plan-review-001.s08/1", "pid": os.getpid(), "checks": checks.rows,
           "summary": checks.summary(), "refused_process_events": list(common.REFUSED_EVENTS),
           "boot": common.sysctl_text("kern.bootsessionuuid")}
    digest = common.write_output(args.output, out, labels)
    lines = []
    for rel in files_below(args.out):
        if rel != "SHA256SUMS.txt":
            lines.append(common.read_bytes(args.out + "/" + rel, keep=False)[1]["sha256"] + "  " + rel)
    sums = ("\n".join(lines) + "\n").encode("ascii")
    fd = os.open(args.out + "/SHA256SUMS.txt", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(sums)
        handle.flush()
        os.fsync(handle.fileno())
    print(str({"summary": out["summary"], "output_sha256": digest, "sums_entries": len(lines),
               "sums_sha256": hashlib.sha256(sums).hexdigest()}))


if __name__ == "__main__":
    main()
