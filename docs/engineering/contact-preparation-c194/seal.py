#!/usr/bin/env python3
"""Seal the independently reviewed C194 preparation before any native run."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from common import HERE, REPO, digest, require, verify_inputs, write

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--review", type=Path, required=True)
a = p.parse_args()
inputs = verify_inputs()
review = json.loads(a.review.read_text())
require(review["passed"] is True and review["input_manifest_sha256"] == inputs["input_manifest_sha256"],
        "Independent passing review must identify this exact input manifest")
require(not (HERE / "EXECUTION-LEDGER.json").exists(), "Execution already reserved; cannot change freeze")
write(HERE / "PREPARATION-REVIEW.json", review, exclusive=True)
seal = {"schema": "ontokin.c194.preparation-freeze/0.1", "approved_for_execution": True,
        "created_utc": datetime.now(timezone.utc).isoformat(), "native_builds_before_freeze": 0,
        "source_commit": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "input_manifest_sha256": inputs["input_manifest_sha256"],
        "review_sha256": digest(HERE / "PREPARATION-REVIEW.json"),
        "planned_builds": ["ok-G", "python-G", "ok-H", "python-H"],
        "maximum_builds": 4, "authors_authorized": False}
write(HERE / "FREEZE.json", seal, exclusive=True)
print(json.dumps(seal, indent=2))

