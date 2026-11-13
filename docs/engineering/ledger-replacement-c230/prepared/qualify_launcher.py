"""Exercise the real launcher with harmless workers and a tiny Git fixture only."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

STANDIN = r'''import argparse, json, os, sys, time
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("mode")
for field in ("source", "output", "scratch"):
    p.add_argument("--" + field, required=True)
a = p.parse_args()
out = Path(a.output)
out.mkdir()
Path(a.scratch).mkdir()
(out / "stand-in-environment.json").write_text(json.dumps({"cwd": str(Path.cwd()), "script": str(Path(__file__).resolve()), "argv": sys.argv, "source": a.source, "output": a.output, "scratch": a.scratch, "product_imports": 0}))
if BEHAVIOR == "timeout":
    time.sleep(5)
if BEHAVIOR == "missing-result":
    raise SystemExit(0)
if BEHAVIOR == "malformed-result":
    (out / "result.json").write_text("invalid JSON")
    raise SystemExit(0)
result = {"completed": True, "child_start_attempts": []}
if a.mode == "original-method":
    result.update(tests_run=1, subtests=[{"status": "passed", "parameters": {"name": name, "mutation": mutation}} for name in ("marker", "journal") for mutation in ("corrupt", "replace", "symlink", "hardlink", "missing")], errors=[], skipped=[], failures=[], temporary_fixture_cleanup_observed_empty=True)
else:
    result.update(case_count=4, cleanup={"retained_descriptors_closed": True})
if BEHAVIOR == "forbidden-child-report":
    result["child_start_attempts"] = [{"event": "synthetic forbidden attempt; no child was started"}]
if BEHAVIOR == "unexpected-original-failure":
    result["subtests"][0].update(status="failed", traceback="synthetic failure")
    result["failures"] = ["synthetic failure"]
(out / "result.json").write_text(json.dumps(result))
raise SystemExit(3 if BEHAVIOR == "unexpected-exit" else 0)
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def command(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=30, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", required=True, type=Path)
    parser.add_argument("--baseline-launcher", required=True, type=Path)
    args = parser.parse_args()
    root = args.report_dir.resolve()
    root.mkdir()
    launcher = Path(__file__).resolve().with_name("launch_diagnosis.py")
    baseline = args.baseline_launcher.resolve(strict=True)
    source = root / "inert-source"
    source.mkdir()
    (source / "PINNED.txt").write_text("Harmless fixture; no product code.\n")
    for cmd in (["git", "init", "--quiet", str(source)],
                ["git", "-C", str(source), "add", "PINNED.txt"],
                ["git", "-C", str(source), "-c", "user.name=C230 inert control", "-c", "user.email=inert@example.invalid", "commit", "--quiet", "-m", "Harmless source fixture"]):
        result = command(cmd)
        if result.returncode:
            raise RuntimeError(result.stderr)
    identity = command(["git", "-C", str(source), "rev-parse", "HEAD", "HEAD^{tree}"]).stdout.splitlines()
    python = Path(sys.executable).resolve()
    rows = []

    def case(name, *, behavior="normal", relative=False, plan_relative=False,
             failure=None, baseline_control=False, repeat=False):
        directory = root / name
        directory.mkdir()
        prepared = directory / "prepared"
        prepared.mkdir()
        caller = directory / "unrelated-caller"
        caller.mkdir()
        shutil.copy2(baseline if baseline_control else launcher, prepared / "launch_diagnosis.py")
        worker = prepared / "diagnose_replacement.py"
        worker.write_text("BEHAVIOR = " + repr(behavior) + "\n" + STANDIN)
        output = directory / "run"
        plan_path = prepared / "RUN-PLAN.json"
        approval_path = directory / "APPROVAL.json"
        plan = {"source_directory": str(source), "output_directory": str(output),
                "source_commit": identity[0], "source_tree": identity[1],
                "source_sha256": {"PINNED.txt": sha(source / "PINNED.txt")},
                "harness_sha256": {n: sha(prepared / n) for n in ("launch_diagnosis.py", "diagnose_replacement.py")},
                "python_sha256": sha(python), "maximum_worker_starts": 2,
                "slots": [{"mode": mode, "maximum_starts": 1,
                           "timeout_seconds": 0.2 if behavior == "timeout" else 5}
                          for mode in ("original-method", "observed-cases")]}
        if plan_relative:
            plan["source_directory"] = os.path.relpath(source, prepared)
            plan["output_directory"] = os.path.relpath(output, prepared)
        if failure == "source-commit":
            plan["source_commit"] = "0" * 40
        elif failure == "source-hash":
            plan["source_sha256"]["PINNED.txt"] = "0" * 64
        elif failure == "missing-source-input":
            plan["source_sha256"] = {"missing.txt": "0" * 64}
        elif failure == "output-within-source":
            plan["output_directory"] = str(source / "forbidden-output")
        elif failure == "finite-start-count":
            plan["maximum_worker_starts"] = 3
        elif failure == "finite-timeout":
            plan["slots"][0]["timeout_seconds"] = 61
        elif failure == "missing-binding":
            del plan["harness_sha256"]["diagnose_replacement.py"]
        write_json(plan_path, plan)
        approval = {"decision": "APPROVE_FINITE_DIAGNOSIS", "plan_sha256": sha(plan_path),
                    "source_commit": plan["source_commit"], "maximum_worker_starts": 2}
        if failure == "approval-hash":
            approval["plan_sha256"] = "0" * 64
        write_json(approval_path, approval)
        if failure == "worker-hash":
            worker.write_text(worker.read_text() + "\n# Deliberate control drift\n")
        elif failure == "missing-worker":
            worker.unlink()
        elif failure == "missing-plan":
            plan_path.unlink()
        elif failure == "missing-approval":
            approval_path.unlink()
        launch_path = prepared / "launch_diagnosis.py"
        if failure == "launcher-location":
            launch_path = directory / "unreviewed-location.py"
            shutil.copy2(launcher, launch_path)
        invocation = [str(python), "-IB", str(launch_path), "--plan",
                      os.path.relpath(plan_path, caller) if relative else str(plan_path),
                      "--approval", os.path.relpath(approval_path, caller) if relative else str(approval_path)]
        observed = command(invocation, cwd=caller)
        (directory / "launcher.stdout.log").write_text(observed.stdout)
        (directory / "launcher.stderr.log").write_text(observed.stderr)
        write_json(directory / "invocation.json", {"command": invocation, "cwd": str(caller), "returncode": observed.returncode})
        report_path = output / "RESULT.json"
        report = json.loads(report_path.read_text()) if report_path.exists() else None
        row = {"case": name, "passed": False, "returncode": observed.returncode,
               "result_exists": report is not None, "worker_start_count": report.get("worker_start_count", 0) if report else 0,
               "product_imports": 0, "diagnostic_cases_executed": 0}
        try:
            postclaim_failure = failure in ("source-commit", "source-hash", "missing-source-input")
            if failure and not postclaim_failure:
                assert observed.returncode != 0 and report is None and not output.exists()
                assert not (source / "forbidden-output").exists()
            elif postclaim_failure:
                assert observed.returncode == 1 and report["schedule_consumed"] and not report["completed"]
                assert report["worker_start_count"] == 0
            elif baseline_control or behavior != "normal":
                assert observed.returncode == 1 and report["schedule_consumed"] and not report["completed"]
                assert report["worker_start_count"] == 1
                start = report["worker_starts"][0]
                assert start["reaped"] is True and start["remaining_process_group"] == []
                assert not (output / "observed-cases").exists()
                if baseline_control:
                    assert start["exit_code"] == 2 and not (output / "original-method").exists()
                if behavior == "timeout":
                    assert start["outcome"] == "timeout_killed"
            else:
                assert observed.returncode == 0 and report["completed"] and report["source_unchanged"]
                assert report["schedule_consumed"] and report["worker_start_count"] == 2
                assert Path(report["resolved_paths"]["worker"]) == worker.resolve()
                for start in report["worker_starts"]:
                    assert start["popen_succeeded"] and start["reaped"] and not start["remaining_process_group"]
                    assert Path(start["command"][2]).is_absolute()
                    evidence = json.loads((output / start["mode"] / "stand-in-environment.json").read_text())
                    assert evidence["cwd"] == str(source)
                    assert evidence["script"] == str(worker.resolve())
                    assert evidence["product_imports"] == 0
                    assert all(Path(evidence[key]).is_absolute() for key in ("source", "output", "scratch"))
                if repeat:
                    old_bytes = report_path.read_bytes()
                    again = command(invocation, cwd=caller)
                    (directory / "repeat.stdout.log").write_text(again.stdout)
                    (directory / "repeat.stderr.log").write_text(again.stderr)
                    assert again.returncode != 0 and report_path.read_bytes() == old_bytes
                    assert len(list(output.glob("*/stand-in-environment.json"))) == 2
                    row["repeat_refused_without_new_worker"] = True
            row["passed"] = True
        except BaseException:
            row["assertion_failure"] = traceback.format_exc()
        rows.append(row)

    case("old-launcher-relative-path-counterexample", relative=True, baseline_control=True)
    case("relative-plan-and-approval", relative=True)
    case("absolute-plan-unrelated-caller")
    case("relative-plan-embedded-source-output", relative=True, plan_relative=True)
    case("one-use-output-refusal", repeat=True)
    for failure in ("missing-plan", "missing-approval", "missing-worker", "worker-hash", "approval-hash",
                    "launcher-location", "source-commit", "source-hash", "missing-source-input",
                    "output-within-source", "finite-start-count", "finite-timeout", "missing-binding"):
        case("reject-" + failure, failure=failure)
    for behavior in ("missing-result", "malformed-result", "forbidden-child-report", "timeout",
                     "unexpected-original-failure", "unexpected-exit"):
        case("stop-" + behavior, behavior=behavior)
    report = {"schema": "ontokin.c230.inert-launcher-qualification/0.1",
              "launcher_sha256": sha(launcher), "baseline_launcher_sha256": sha(baseline),
              "qualification_script_sha256": sha(Path(__file__)),
              "environment": {"python": sys.version, "executable": str(python), "platform": list(os.uname())},
              "controls": len(rows), "passed": all(row["passed"] for row in rows),
              "passed_controls": sum(row["passed"] for row in rows), "cases": rows,
              "product_imports": 0, "product_methods_executed": 0, "actual_replacement_cases": 0,
              "meaning": "Launcher qualification with harmless stand-in result shapes only; no ledger or product execution."}
    write_json(root / "QUALIFICATION.json", report)
    print(json.dumps({"passed": report["passed"], "controls": len(rows), "passed_controls": report["passed_controls"], "report": str(root / "QUALIFICATION.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
