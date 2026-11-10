#!/usr/bin/env python3
"""Common C193 command recorder; retains failures and never overwrites a run."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--repo", type=Path, required=True)
p.add_argument("--route", choices=("ok", "python"), required=True)
p.add_argument("--source", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--blender", type=Path, required=True)
a = p.parse_args()
for name in ("repo", "source", "out", "blender"):
    setattr(a, name, getattr(a, name).resolve())
a.out.mkdir(parents=True, exist_ok=False)
source = a.source.read_bytes()
(a.out / ("submitted-source" + a.source.suffix)).write_bytes(source)
if a.route == "ok":
    command = [sys.executable, "-B", "-m", "prototypes.guided_contact_v02", "run", str(a.source),
               "--store", str(a.out / "store"), "--blender", str(a.blender),
               "--host-max-operations", "1000000", "--host-max-elapsed-ms", "80000"]
else:
    command = [sys.executable, "-B", str(Path(__file__).parent / "direct_runner.py"),
               "--repo", str(a.repo), "--design", str(a.source), "--out", str(a.out / "artifact"),
               "--blender", str(a.blender)]
record = {"route": a.route, "source": str(a.source), "source_sha256": hashlib.sha256(source).hexdigest(),
          "argv": command, "cwd": str(a.repo), "started_unix_s": time.time(), "successful": False}
(a.out / "command.json").write_text(json.dumps(record, indent=2) + "\n")
with (a.out / "stdout.txt").open("wb") as stdout, (a.out / "stderr.txt").open("wb") as stderr:
    try:
        done = subprocess.run(command, cwd=a.repo, stdout=stdout, stderr=stderr, timeout=100)
        record["returncode"] = done.returncode
    except subprocess.TimeoutExpired:
        record["returncode"] = None
        record["error"] = "Outer 100-second process deadline"
record["finished_unix_s"] = time.time()
record["elapsed_s"] = record["finished_unix_s"] - record["started_unix_s"]
try:
    result = json.loads((a.out / "stdout.txt").read_text())
    record.update(successful=record["returncode"] == 0 and result["successful"],
                  artifact_directory=result.get("artifact_directory"), cost=result.get("cost"))
except Exception as error:
    record["parse_error"] = str(error)
record["source_unchanged_during_build"] = a.source.read_bytes() == source
record["successful"] = record["successful"] and record["source_unchanged_during_build"]
(a.out / "command.json").write_text(json.dumps(record, indent=2) + "\n")
(a.out / "delivery.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, sort_keys=True))
raise SystemExit(0 if record["successful"] else 1)
