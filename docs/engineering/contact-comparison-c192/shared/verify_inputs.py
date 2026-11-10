#!/usr/bin/env python3
"""Verify the pre-dispatch C192 files and their inherited implementation inputs."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--repo", type=Path, required=True)
a = p.parse_args()
scope = a.repo / "docs/engineering/contact-comparison-c192"
frozen = json.loads((scope / "frozen/INPUT-FREEZE.json").read_text())
failures = []
for relative, expected in frozen["files"].items():
    path = a.repo / relative
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected["sha256"]:
        failures.append(relative)
print(json.dumps({"pass": not failures, "checked": len(frozen["files"]), "failures": failures}))
raise SystemExit(bool(failures))
