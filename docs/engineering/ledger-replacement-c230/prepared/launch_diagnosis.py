"""One-use C230 launcher; path-qualified successor to the C229 launcher."""
from __future__ import annotations
import argparse
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
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def source_state(source, bindings):
    identity = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD", "HEAD^{tree}"],
                              capture_output=True, text=True, check=True, timeout=20).stdout.splitlines()
    status = subprocess.run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"],
                            capture_output=True, text=True, check=True, timeout=20).stdout
    hashes = {name: sha(source / name) for name in bindings}
    return {"commit": identity[0], "tree": identity[1], "status": status, "source_hashes": hashes}


def group_members(pgid):
    found = []
    for directory in Path("/proc").iterdir():
        if directory.name.isdigit():
            try:
                text = (directory / "stat").read_text()
                fields = text[text.rfind(")") + 2:].split()
                if int(fields[2]) == pgid:
                    found.append({"pid": int(directory.name), "state": fields[0]})
            except (OSError, ValueError, IndexError):
                pass
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--approval", required=True, type=Path)
    args = parser.parse_args()
    # Resolve caller paths before any worker changes its working directory.
    plan_path = args.plan.resolve(strict=True)
    approval_path = args.approval.resolve(strict=True)
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    approval = json.loads(approval_path.read_text())
    if not (approval.get("decision") == "APPROVE_FINITE_DIAGNOSIS"
            and approval.get("plan_sha256") == sha(plan_path)
            and approval.get("source_commit") == plan["source_commit"]
            and approval.get("maximum_worker_starts") == 2):
        raise RuntimeError("Missing or mismatched independent finite-plan approval")
    if [slot["mode"] for slot in plan["slots"]] != ["original-method", "observed-cases"]:
        raise RuntimeError("Finite slot inventory differs")
    # Relative paths inside the plan are relative to the resolved plan directory.
    def plan_path_value(value, *, strict):
        path = Path(value)
        return (path if path.is_absolute() else directory / path).resolve(strict=strict)
    source = plan_path_value(plan["source_directory"], strict=True)
    output = plan_path_value(plan["output_directory"], strict=False)
    if not source.is_dir() or not output.parent.is_dir():
        raise RuntimeError("Source or output parent is not an existing directory")
    if output == source or source in output.parents:
        raise RuntimeError("Diagnostic output must be outside the immutable source")
    required_scripts = {"diagnose_replacement.py", "launch_diagnosis.py"}
    if set(plan["harness_sha256"]) != required_scripts:
        raise RuntimeError("Exact reviewed launcher and worker bindings are required")
    scripts = {name: (directory / name).resolve(strict=True) for name in required_scripts}
    if Path(__file__).resolve(strict=True) != scripts["launch_diagnosis.py"]:
        raise RuntimeError("Invoked launcher differs from the reviewed launcher path")
    for filename, expected in plan["harness_sha256"].items():
        if not scripts[filename].is_file() or sha(scripts[filename]) != expected:
            raise RuntimeError("Reviewed harness bytes changed")
    harness = scripts["diagnose_replacement.py"]
    python = Path(sys.executable).resolve(strict=True)
    if (plan.get("maximum_worker_starts") != 2
            or any(slot.get("maximum_starts") != 1
                   or not 0 < slot["timeout_seconds"] <= 60 for slot in plan["slots"])):
        raise RuntimeError("Finite worker start or timeout limits differ")
    if (tuple(sys.version_info[:3]) != (3, 12, 14) or os.uname().sysname != "Linux"
            or os.uname().machine != "x86_64" or sha(python) != plan["python_sha256"]):
        raise RuntimeError("Interpreter or platform differs from the reviewed plan")
    # mkdir is the durable one-use claim. Existing outputs are never resumed or overwritten.
    output.mkdir()
    scratch = output / "tmp"
    scratch.mkdir()
    started = time.monotonic()
    report = {"schema": "ontokin.c230.finite-diagnosis-run/0.1", "plan_sha256": sha(plan_path),
              "approval_sha256": sha(approval_path), "worker_starts": [], "completed": False,
              "native_starts": 0, "aggregate_attempts": 0, "source_before": None,
              "resolved_paths": {"plan": str(plan_path), "approval": str(approval_path),
                                 "launcher": str(scripts["launch_diagnosis.py"]),
                                 "worker": str(harness), "source": str(source),
                                 "output": str(output), "python": str(python)},
              "caller_working_directory": str(Path.cwd())}
    save(output / "RUNNING.json", report)
    try:
        before = source_state(source, plan["source_sha256"])
        report["source_before"] = before
        if (before["commit"] != plan["source_commit"] or before["tree"] != plan["source_tree"]
                or before["status"] or before["source_hashes"] != plan["source_sha256"]):
            raise RuntimeError("Source identity, cleanliness or input hashes differ from plan")
        for slot in plan["slots"]:
            mode = slot["mode"]
            command = [str(python), "-IB", str(harness), mode, "--source", str(source),
                       "--output", str(output / mode), "--scratch", str(scratch / mode)]
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(scratch))
            with (output / (mode + ".stdout.log")).open("xb") as stdout, (output / (mode + ".stderr.log")).open("xb") as stderr:
                attempt = {"mode": mode, "command": command, "timeout_seconds": slot["timeout_seconds"],
                           "attempt_consumed": True, "popen_succeeded": False, "outcome": "start_attempted"}
                report["worker_starts"].append(attempt)
                save(output / "RUNNING.json", report)
                process = subprocess.Popen(command, cwd=source, env=environment, stdout=stdout, stderr=stderr,
                                           start_new_session=True)
                attempt["pid"], attempt["pgid"] = process.pid, process.pid
                attempt["popen_succeeded"] = True
                try:
                    attempt["exit_code"] = process.wait(timeout=slot["timeout_seconds"])
                    attempt["outcome"] = "exited"
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    attempt["exit_code"] = process.wait(timeout=10)
                    attempt["outcome"] = "timeout_killed"
                except BaseException:
                    attempt["outcome"] = "interrupted_killed"
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                    attempt["exit_code"] = process.wait(timeout=10)
                    raise
                finally:
                    attempt["reaped"] = process.poll() is not None
                    attempt["remaining_process_group"] = group_members(process.pid)
            save(output / "RUNNING.json", report)
            if attempt["outcome"] != "exited" or not attempt["reaped"] or attempt["remaining_process_group"]:
                raise RuntimeError("Worker did not exit with confirmed cleanup; no further start")
            result_path = output / mode / "result.json"
            if not result_path.is_file():
                raise RuntimeError("Missing complete worker result; no further start")
            result = json.loads(result_path.read_text())
            if not result.get("completed") or result.get("child_start_attempts"):
                raise RuntimeError("Incomplete worker or forbidden child attempt; no further start")
            if mode == "original-method":
                failures = [x for x in result["subtests"] if x["status"] != "passed"]
                if (result["tests_run"] != 1 or len(result["subtests"]) != 10 or result["errors"]
                        or result["skipped"] or len(result["failures"]) != len(failures)
                        or result["temporary_fixture_cleanup_observed_empty"] is not True
                        or attempt["exit_code"] not in (0, 1)
                        or any(x["status"] != "failed" or x["parameters"].get("mutation") != "replace"
                               or "LedgerError not raised" not in x.get("traceback", "") for x in failures)):
                    raise RuntimeError("Unexpected original-method outcome; diagnostic follow-up is not authorized")
            elif (attempt["exit_code"] != 0 or result.get("case_count") != 4
                  or result.get("cleanup", {}).get("retained_descriptors_closed") is not True):
                raise RuntimeError("Observed-case execution did not complete")
        report["completed"] = True
    except BaseException as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        try:
            report["source_after"] = source_state(source, plan["source_sha256"])
            report["source_unchanged"] = report["source_before"] == report["source_after"]
        except BaseException as exc:
            report["source_after_error"] = repr(exc)
            report["source_unchanged"] = False
        report["elapsed_seconds"] = time.monotonic() - started
        report["schedule_consumed"] = True
        report["worker_start_count"] = len(report["worker_starts"])
        report["metadata_git_starts_maximum"] = 4
        report["conclusion"] = "Finite observation only; original C228 failure and R02 remain unchanged"
        save(output / "RESULT.json", report)
    print(json.dumps({"completed": report["completed"], "source_unchanged": report["source_unchanged"],
                      "worker_start_count": len(report["worker_starts"]), "report": str(output / "RESULT.json")}))
    return 0 if report["completed"] and report["source_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
