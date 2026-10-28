#!/usr/bin/env python3
"""Freeze and execute exactly one control/capture pair, serially."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--driver", type=Path, required=True)
parser.add_argument("--reviewed-driver-sha256", required=True)
args = parser.parse_args()
root, output, driver = args.root.resolve(), args.output.resolve(), args.driver.resolve()
assert not output.is_relative_to(root) and not driver.is_relative_to(root)
assert sha(driver) == args.reviewed_driver_sha256
output.mkdir(parents=True, exist_ok=False)
plan = {"schema": "ontokin.checkpoint036-pair-plan/0.1", "created_at": utc(),
        "root": str(root), "driver": str(driver), "driver_sha256": sha(driver),
        "orchestrator_sha256": sha(Path(__file__).resolve()),
        "source_commit": "4ca73909f861fe4bef9694787473621c1d21c140",
        "source_tree": "87c949b238055af1ce368c694e1d5683c8aeacde",
        "order": ["control", "capture"], "requests_per_mode": 1,
        "outer_timeout_seconds": 180, "product_limits_unchanged": True,
        "request": {"case": "P11", "end": "3", "fps": 1, "helpers": False},
        "no_live_instrumentation": True, "no_timing_acceptance_threshold": True,
        "no_reruns_or_exclusions_in_this_plan": True,
        "neutrality_required_before_census_interpretation": True}
write(output / "plan.json", plan)
results = []
for mode in plan["order"]:
    assert sha(driver) == plan["driver_sha256"]
    receipt_dir = output / (mode + "-command")
    receipt_dir.mkdir()
    command = [sys.executable, "-B", str(driver), "--root", str(root),
               "--output", str(output / mode), "--mode", mode]
    receipt = {"command": command, "cwd": str(root), "started_at": utc(),
               "driver_sha256": sha(driver), "timeout_seconds": plan["outer_timeout_seconds"]}
    write(receipt_dir / "start.json", receipt)
    started = time.monotonic()
    with (receipt_dir / "stdout.txt").open("xb") as stdout, (receipt_dir / "stderr.txt").open("xb") as stderr:
        process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr, start_new_session=True)
        receipt["pid"] = process.pid
        try:
            receipt["exit_code"] = process.wait(timeout=plan["outer_timeout_seconds"])
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            receipt.update(exit_code=process.returncode, timed_out=True)
    receipt.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started,
                   driver_unchanged=sha(driver) == plan["driver_sha256"],
                   streams=[{"path": name, "bytes": (receipt_dir / name).stat().st_size,
                             "sha256": sha(receipt_dir / name)} for name in ("stdout.txt", "stderr.txt")])
    write(receipt_dir / "result.json", receipt)
    results.append(receipt)
    print(json.dumps({"mode": mode, "exit_code": receipt["exit_code"],
                      "elapsed_seconds": receipt["elapsed_seconds"]}), flush=True)
    if receipt.get("timed_out") or not (output / mode / "request-result.json").is_file():
        break
write(output / "pair-command.json", {"plan_sha256": sha(output / "plan.json"), "commands": results,
                                     "finished_at": utc(), "requests_executed": len(results)})
raise SystemExit(0 if len(results) == 2 and all(x["exit_code"] == 1 for x in results) else 1)
