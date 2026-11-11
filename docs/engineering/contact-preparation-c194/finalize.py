#!/usr/bin/env python3
"""Join unchanged automated results with actual visual review; runs no native work."""
import argparse
import json
from pathlib import Path
from common import digest, require, verify_freeze, write

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--results", type=Path, required=True)
p.add_argument("--visual-review", type=Path, required=True)
a = p.parse_args()
freeze = verify_freeze()
out = a.results.resolve().parent
results = json.loads(a.results.read_text())
ledger = json.loads((out / "EXECUTION-LEDGER.json").read_text())
require(ledger["results_sha256"] == digest(a.results), "Executed result differs from closing ledger")
require(results["frozen_inputs"]["freeze_sha256"] == freeze["freeze_sha256"], "Execution freeze differs")
visual = json.loads(a.visual_review.read_text())
reviewed = {row["path"]: row for row in visual["panels"]}
actual = {str(path.relative_to(out / "receiving")): path for path in (out / "receiving/renders").rglob("*.png")}
require(len(actual) == len(reviewed) == 12 and set(actual) == set(reviewed), "Review must cover all twelve original render panels")
for name, path in actual.items():
    require(path.stat().st_size == reviewed[name]["bytes"] and digest(path) == reviewed[name]["sha256"],
            "Visual review panel identity differs: " + name)
passed = results["automated_gates_passed"] and visual["pass"] is True
report = {"schema": "ontokin.c194.final-qualification/0.1",
          "passed": passed, "qualified_for_author_dispatch": passed,
          "targets_mm": [365, 375], "coordinator_setup_only": True, "author_trials": 0,
          "results_sha256": digest(a.results), "freeze_sha256": freeze["freeze_sha256"],
          "visual_review_sha256": digest(a.visual_review), "panels_reviewed": 12,
          "decision": "Both targets qualify; freeze the public protocol before author dispatch" if passed else
                      "STOP before author dispatch; preserve failure and propose separately reviewed next action"}
write(out / "QUALIFICATION.json", report, exclusive=True)
print(json.dumps(report, indent=2))
raise SystemExit(0 if passed else 1)

