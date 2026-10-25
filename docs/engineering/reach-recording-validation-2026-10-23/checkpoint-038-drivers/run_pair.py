#!/usr/bin/env python3
"""Freeze and execute exactly one original P16 control/capture pair, serially."""
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
import traceback


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


def error_record(error):
    return {"type": type(error).__name__, "message": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--driver", type=Path, required=True)
    parser.add_argument("--reviewed-driver-sha256", required=True)
    parser.add_argument("--reviewed-runner-sha256", required=True)
    args = parser.parse_args()
    root, output, driver = args.root.resolve(), args.output.resolve(), args.driver.resolve()
    if (output.is_relative_to(root) or driver.is_relative_to(root)
            or Path(__file__).resolve().is_relative_to(root)):
        raise ValueError("Drivers and receipts must be outside execution checkout")
    if sha(driver) != args.reviewed_driver_sha256 or sha(Path(__file__).resolve()) != args.reviewed_runner_sha256:
        raise ValueError("Reviewed driver/runner hashes differ")
    output.mkdir(parents=True, exist_ok=False)
    plan = {"schema": "ontokin.checkpoint038-pair-plan/0.1", "created_at": utc(),
        "root": str(root), "driver": str(driver), "driver_sha256": sha(driver),
        "orchestrator_sha256": sha(Path(__file__).resolve()),
        "source_commit": "4ca73909f861fe4bef9694787473621c1d21c140",
        "source_tree": "87c949b238055af1ce368c694e1d5683c8aeacde",
        "expected_program_revision": "sha256:0487f3f410944484f0a6aad7bef37e1a59a1d13464b19af85661251c430388f7",
        "manifest_sha256": "0d218a8b1245766fa3e4892ec5ccafd275ee92fd4195b3b852d5daaefa9e4070",
        "environment": {"executable": sys.executable, "python": sys.version,
                        "executable_sha256": sha(Path(sys.executable).resolve())},
        "order": ["control", "capture"], "requests_per_mode": 1,
        "outer_timeout_seconds": 180, "product_limits_unchanged": True,
        "request": {"case": "P16", "end": "4", "fps": 1, "fps_native_type": "int", "helpers": False,
                    "position_tolerance_m": .001, "rotation_tolerance_rad": .001, "time_tolerance_s": .000001},
        "limits": {"shared_operations": 100000, "elapsed_ms": 30000, "operand_bits": 32768,
                   "existing_numerical_cache_entries": 256, "separate_category_metadata_limit": 512},
        "no_live_instrumentation": True, "no_timing_acceptance_threshold": True,
        "no_reruns_or_exclusions_in_this_plan": True,
        "neutrality_required_before_census_interpretation": True}
    write(output / "plan.json", plan)
    results, outer_error = [], None
    try:
        for mode in plan["order"]:
            if sha(driver) != plan["driver_sha256"] or sha(Path(__file__).resolve()) != plan["orchestrator_sha256"]:
                raise ValueError("A frozen driver changed before request execution")
            receipt_dir = output / (mode + "-command")
            receipt_dir.mkdir()
            command = [sys.executable, "-B", str(driver), "--root", str(root),
                       "--output", str(output / mode), "--mode", mode]
            receipt = {"command": command, "cwd": str(root), "started_at": utc(),
                       "driver_sha256": sha(driver), "timeout_seconds": plan["outer_timeout_seconds"],
                       "started_process": False}
            write(receipt_dir / "start.json", receipt)
            started, process = time.monotonic(), None
            try:
                with (receipt_dir / "stdout.txt").open("xb") as stdout, (receipt_dir / "stderr.txt").open("xb") as stderr:
                    process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr, start_new_session=True)
                    receipt.update(pid=process.pid, started_process=True)
                    try:
                        receipt["exit_code"] = process.wait(timeout=plan["outer_timeout_seconds"])
                    except subprocess.TimeoutExpired:
                        receipt["timed_out"] = True
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        receipt["exit_code"] = process.returncode
            except BaseException as command_error:
                receipt["command_error"] = error_record(command_error)
                if process is not None and process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    receipt["exit_code"] = process.returncode
            finally:
                receipt.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started,
                    driver_unchanged=sha(driver) == plan["driver_sha256"],
                    streams=[{"path": name, "bytes": (receipt_dir / name).stat().st_size,
                              "sha256": sha(receipt_dir / name)} for name in ("stdout.txt", "stderr.txt")
                             if (receipt_dir / name).is_file()])
                write(receipt_dir / "result.json", receipt)
                results.append(receipt)
            print(json.dumps({"mode": mode, "exit_code": receipt.get("exit_code"),
                              "elapsed_seconds": receipt["elapsed_seconds"]}), flush=True)
            if receipt.get("timed_out") or receipt.get("command_error") or receipt.get("exit_code") != 1:
                break
            path = output / mode / "request-result.json"
            if not path.is_file():
                break
            child = json.loads(path.read_text())
            if (not child.get("request_executed") or child.get("status") != "failed"
                    or not child.get("inputs_stable") or child.get("metadata_status") != "captured"
                    or not child.get("observation_preserved_counters_and_caches")):
                break
    except BaseException as error:
        outer_error = error_record(error)
        (output / "pair-error.txt").write_text("".join(traceback.format_exception(error)))
    finally:
        closed = {"plan_sha256": sha(output / "plan.json"), "commands": results,
                  "finished_at": utc(), "processes_started": sum(x["started_process"] for x in results),
                  "commands_closed": len(results), "outer_error": outer_error,
                  "orchestrator_unchanged": sha(Path(__file__).resolve()) == plan["orchestrator_sha256"],
                  "neutrality_status": "not_interpreted_by_runner"}
        write(output / "pair-command.json", closed)
    return 0 if outer_error is None and len(results) == 2 and all(x.get("exit_code") == 1 for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
