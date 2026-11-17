#!/usr/bin/env python3
"""Read-only C257 evidence/candidate receipt verification."""
from pathlib import Path
import hashlib
import json
import re
import datetime

OUT = Path(__file__).resolve().parent
WORKSPACE = OUT.parents[1]
REPO = WORKSPACE / "OntoKin"
ROOT = REPO / "docs/engineering/localized-repair-c257"
EVIDENCE = ROOT / "evidence"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


locations = json.loads((EVIDENCE / "EVIDENCE-LOCATIONS.json").read_text())
records, issues = [], []
for row in locations["files"]:
    if "retainedPath" in row:
        path = (EVIDENCE / row["retainedPath"]).resolve()
    else:
        path = (REPO / row["repositoryPath"]).resolve()
    ok = path.is_relative_to(REPO) and path.is_file() and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"]
    records.append({**row, "resolvedRepositoryPath": path.relative_to(REPO).as_posix(), "verified": ok})
    if not ok:
        issues.append(row.get("originalPath", row.get("retainedPath")))

required = json.loads((WORKSPACE / "audit/c257-reader-review/REVIEW-RETENTION.json").read_text())["requiredFiles"]
by_original = {x["originalPath"]: x for x in locations["files"] if "originalPath" in x}
missing = []
for row in required:
    mapped = by_original.get("c257-reader-review/" + row["path"])
    if not mapped or mapped["sha256"] != row["sha256"] or mapped["bytes"] != row["bytes"]:
        missing.append(row["path"])

inputs = json.loads((ROOT / "INPUTS.json").read_text())
input_results = []
for row in inputs["inputs"] + inputs["authorities"]:
    path = REPO / row["path"]
    input_results.append({**row, "verified": path.stat().st_size == row["bytes"] and digest(path) == row["sha256"]})

checks = []
for path in sorted((EVIDENCE / "candidate-checks").glob("*.json")):
    data = json.loads(path.read_text())
    if "logSha256" not in data:
        continue
    log = path.parent / data["log"]
    script = REPO / next(x for x in data["command"] if x.endswith(".py"))
    checks.append({"name": path.stem, "commit": data["commit"], "tree": data["tree"],
                   "passed": data["passed"], "sourceUnchangedAfter": data["sourceUnchangedAfter"],
                   "logHashVerified": digest(log) == data["logSha256"],
                   "scriptHashVerified": digest(script) == data["scriptSha256"],
                   "testCountsInLog": re.findall(r"Ran (\d+) tests?", log.read_text())})

summary = json.loads((EVIDENCE / "candidate-checks/CHECKS.json").read_text())
doc = json.loads((OUT / "documentation.json").read_text())
doclog = json.loads((OUT / "documentation.log").read_text())
lines = (REPO / "STATUS.md").read_text().splitlines()
start = lines.index("## Main integration lease")
lease = lines[start:start + 17]
report = {"recordedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "evidenceLocationEntries": len(records), "evidenceLocations": records,
          "evidenceLocationFailures": issues, "requiredIndependentFiles": len(required),
          "requiredIndependentMissingOrWrong": missing, "originalInputBindings": input_results,
          "candidateCohortReceipts": checks, "cohortSummary": summary,
          "documentation": {"receipt": doc, "logVerified": digest(OUT / "documentation.log") == doc["logSha256"],
                            "scriptVerified": digest(REPO / "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py") == doc["scriptSha256"],
                            "sections": doclog["sections_verified"], "sources": doclog["sources_verified"],
                            "links": doclog["links"], "failures": doclog["failures"]},
          "leaseExcerpt": lease}
(OUT / "EVIDENCE-AND-GATES.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"evidenceMapEntries": len(records), "evidenceMapErrors": issues,
                  "requiredFiles": len(required), "requiredMissingOrWrong": missing,
                  "inputBindings": len(input_results), "allInputBindingsMatch": all(x["verified"] for x in input_results),
                  "cohort": checks, "documentation": {"sources": doclog["sources_verified"],
                      "sections": doclog["sections_verified"], "links": doclog["links"], "errors": doclog["failures"]},
                  "lease": lease}, sort_keys=True))
assert not issues and not missing and all(x["verified"] for x in input_results)
assert report["documentation"]["logVerified"] and report["documentation"]["scriptVerified"] and not doclog["failures"]
assert all(x["passed"] and x["sourceUnchangedAfter"] and x["logHashVerified"] and x["scriptHashVerified"] for x in checks)
