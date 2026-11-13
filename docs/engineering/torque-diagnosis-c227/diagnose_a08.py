#!/usr/bin/env python3
"""Run the reviewed C227 two-slot diagnostic without changing product behavior."""
from __future__ import annotations

import argparse
import cProfile
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import pstats
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
SCHEMA = "ontokin.c227.a08-diagnostic/0.1"
TEST = "tests/test_torque_artifact_reads.py"
FROZEN = "docs/language-design/torque-v0.1/freeze"
PROTECTED = ("ontokin", TEST, FROZEN)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


def cpu_context():
    result = {"cpuCount": os.cpu_count(), "loadAverage": list(os.getloadavg()),
              "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None}
    for name in ("cpu.max", "cpu.stat"):
        path = Path("/sys/fs/cgroup") / name
        try:
            result[name] = path.read_text()
        except OSError as exc:
            result[name] = {"unavailable": type(exc).__name__, "message": str(exc)}
    return result


def git(repo, *args, binary=False):
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.hooksPath=" + os.devnull,
         "-c", "core.fsmonitor=false", *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    return result.stdout if binary else result.stdout.decode().strip()


def tree_records(repo, revision):
    raw = git(repo, "ls-tree", "-rz", revision, "--", *PROTECTED, binary=True)
    records = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        header, path = entry.split(b"\t", 1)
        mode, kind, oid = header.decode().split()
        require(kind == "blob" and mode in {"100644", "100755"},
                "Protected input is not a regular file")
        records.append({"path": path.decode(), "mode": mode, "gitBlob": oid})
    return records


def snapshot(repo, plan):
    require(not git(repo, "status", "--porcelain", "--untracked-files=all"),
            "Source checkout must be completely clean")
    require(not any((repo / "ontokin").rglob("*.pyc")),
            "Existing product bytecode is not an admitted input")
    require(not any((repo / "tests").glob("__pycache__/test_torque_artifact_reads*.pyc")),
            "Existing setup-test bytecode is not an admitted input")
    records = tree_records(repo, "HEAD")
    require(records == tree_records(repo, plan["sourceBaseline"]),
            "Protected code/test/fixture tree differs from reviewed baseline")
    for row in records:
        path = repo / row["path"]
        require(path.is_file() and not path.is_symlink(), "Protected file missing or linked")
        data = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        require(blob == row["gitBlob"], "Worktree bytes differ: " + row["path"])
        row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    package = hashlib.sha256()
    for path in sorted((repo / "ontokin").glob("*.py")):
        package.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    require("sha256:" + package.hexdigest() == plan["implementationDigest"],
            "Implementation digest differs from reconciled current identity")
    for relative, expected in plan["requiredFiles"].items():
        require(digest(repo / relative) == expected, "Required file hash differs: " + relative)
    return {"commit": git(repo, "rev-parse", "HEAD"),
            "tree": git(repo, "rev-parse", "HEAD^{tree}"),
            "implementationDigest": "sha256:" + package.hexdigest(),
            "protectedInputs": records, "worktreeClean": True}


def admission(repo, plan_path, approval_path, identity_path):
    plan, approval = json.loads(plan_path.read_text()), json.loads(approval_path.read_text())
    require(plan["schema"] == SCHEMA, "Unknown diagnostic plan")
    require(plan["modes"] == ["baseline", "cprofile"], "Exactly two ordered slots are allowed")
    require(plan["processTimeoutSeconds"] == 90, "Unexpected process ceiling")
    require(plan["productLimits"] == {"max_operations": 1000000, "max_elapsed_ms": 30000},
            "Frozen product limits must remain unchanged")
    require(approval.get("approved") is True and approval.get("implementationReconciled") is True,
            "Independent approval and implementation reconciliation are required")
    require(approval["planSha256"] == digest(plan_path), "Plan differs from independent approval")
    require(approval["harnessSha256"] == digest(__file__), "Harness differs from independent approval")
    require(approval["identityReviewSha256"] == digest(identity_path),
            "Implementation review differs from approval")
    current = snapshot(repo, plan)
    require(current["commit"] == approval["sourceCommit"] and current["tree"] == approval["sourceTree"],
            "Source identity differs from independently approved execution source")
    return plan, approval, current


def inventory_files(root):
    return [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
             "sha256": digest(path)} for path in sorted(root.rglob("*")) if path.is_file()]


def inspect_store(seed, slot):
    """Keep untouched store bytes and query a separate read-only inspection copy."""
    if not seed or not seed.is_dir():
        return {"available": False}
    raw = slot / "store-raw"
    shutil.copytree(seed, raw)
    inventory = inventory_files(raw)
    work = slot / "store-inspection"
    shutil.copytree(raw, work)
    result = {"available": True, "rawInventory": inventory, "databases": []}
    for path in sorted(work.rglob("*.sqlite3")):
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            item = {"path": str(path.relative_to(work)),
                    "integrityCheck": [row[0] for row in db.execute("PRAGMA integrity_check")],
                    "tableCounts": {name: db.execute('SELECT COUNT(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0]
                                    for name in sorted(tables)}, "projects": [], "requests": [],
                    "runs": [], "artifacts": [], "sources": []}
            if "projects" in tables:
                item["projects"] = [dict(row) for row in db.execute("SELECT * FROM projects ORDER BY id")]
            if "requests" in tables:
                for row in db.execute("SELECT sequence,id,operation,state,payload,response FROM requests ORDER BY sequence"):
                    record = dict(row)
                    for key in ("payload", "response"):
                        if record[key] is not None:
                            record[key] = json.loads(record[key])
                    item["requests"].append(record)
            if "runs" in tables:
                for row in db.execute("SELECT project_id,id,source_revision,descriptor,version FROM runs ORDER BY project_id,id"):
                    record = dict(row)
                    record["descriptor"] = json.loads(record["descriptor"])
                    item["runs"].append(record)
            if "artifacts" in tables:
                for row in db.execute("SELECT project_id,id,source_revision,data,report,sha256 FROM artifacts ORDER BY project_id,id"):
                    record = dict(row)
                    data = bytes(record.pop("data"))
                    record.update(bytes=len(data), observedSha256=hashlib.sha256(data).hexdigest(),
                                  report=json.loads(record["report"]))
                    record["artifactIdMatchesBytes"] = record["id"] == "artifact:" + record["observedSha256"]
                    record["storedSha256MatchesBytes"] = record["sha256"].removeprefix("sha256:") == record["observedSha256"]
                    item["artifacts"].append(record)
            if "sources" in tables:
                for row in db.execute("SELECT project_id,revision,filename,raw,accepted_once FROM sources ORDER BY project_id,revision"):
                    record = dict(row)
                    data = bytes(record.pop("raw"))
                    record.update(bytes=len(data), rawSha256=hashlib.sha256(data).hexdigest())
                    item["sources"].append(record)
            result["databases"].append(item)
    result["rawBytesUnchangedAfterInspection"] = inventory_files(raw) == inventory
    shutil.rmtree(work)
    return result


def profile_reports(profile, slot):
    path = slot / "setup.prof"
    profile.dump_stats(path)
    statistics = pstats.Stats(str(path))
    rows = []
    for (filename, line, name), (primitive, total, own, cumulative, callers) in statistics.stats.items():
        rows.append({"filename": filename, "line": line, "function": name,
                     "primitiveCalls": primitive, "totalCalls": total,
                     "selfSeconds": own, "cumulativeSeconds": cumulative,
                     "callers": [{"filename": caller[0], "line": caller[1], "function": caller[2], "costs": costs}
                                 for caller, costs in sorted(callers.items())]})
    rows.sort(key=lambda row: (-row["cumulativeSeconds"], row["filename"], row["line"]))
    write_json(slot / "profile-functions.json", {"schema": SCHEMA, "instrumented": True,
        "notBaselineTiming": True, "totalCalls": statistics.total_calls,
        "primitiveCalls": statistics.prim_calls, "totalProfileSeconds": statistics.total_tt,
        "functions": rows})
    with (slot / "profile-top.txt").open("w") as stream:
        stats = pstats.Stats(str(path), stream=stream)
        stats.sort_stats("cumulative").print_stats(60)
        stats.sort_stats("tottime").print_stats(60)


def child(args):
    repo, slot = args.repository.resolve(), args.output.resolve()
    plan, approval, before = admission(repo, args.plan.resolve(), args.approval.resolve(), args.identity_review.resolve())
    require(args.child_mode in plan["modes"], "Unknown child slot")
    require((slot / "CONSUMED.json").is_file(), "Supervisor must consume slot before start")
    consumed = json.loads((slot / "CONSUMED.json").read_text())
    slot_number = plan["modes"].index(args.child_mode) + 1
    expected = {"slot": slot_number, "mode": args.child_mode,
                "expectedParentPid": os.getppid(), "sourceCommit": before["commit"],
                "sourceTree": before["tree"], "harnessSha256": digest(__file__),
                "planSha256": digest(args.plan), "approvalSha256": digest(args.approval),
                "identityReviewSha256": digest(args.identity_review), "setupInvocationsAllowed": 1,
                "replayAllowed": False}
    require(all(consumed.get(key) == value for key, value in expected.items()),
            "Consumed slot does not match supervisor, mode, source or approved input hashes")
    require(slot.name == str(slot_number) + "-" + args.child_mode, "Output slot identity differs")
    require(os.getpgrp() == os.getpid(), "Child must have its own supervisor-created process group")
    with (slot / "STARTED.json").open("x") as stream:
        json.dump({**expected, "startedAtUtc": utc(), "pid": os.getpid()}, stream, indent=2)
    sys.path.insert(0, str(repo))
    spec = importlib.util.spec_from_file_location("c227_original_torque_artifact_reads", repo / TEST)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cls = module.TorqueArtifactReadTests
    require(module.POLICY.max_operations == 1000000 and module.POLICY.max_elapsed_ms == 30000,
            "Original test policy differs")
    result = {"schema": SCHEMA, "mode": args.child_mode, "startedAtUtc": utc(),
              "source": {key: before[key] for key in ("commit", "tree", "implementationDigest")},
              "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
              "pid": os.getpid(), "parentPid": os.getppid(), "processGroup": os.getpgrp(),
              "clock": "unmodified product default real monotonic clock",
              "productLimits": plan["productLimits"], "setupOutcome": "unknown",
              "testMethodsExecuted": 0, "instrumented": args.child_mode == "cprofile",
              "cpuContextBeforeSetup": cpu_context()}
    profile = cProfile.Profile() if args.child_mode == "cprofile" else None
    start, cpu = time.monotonic(), time.process_time()
    try:
        try:
            if profile is not None:
                profile.enable()
            cls.setUpClass()
        finally:
            if profile is not None:
                profile.disable()
            ended, cpu_ended = time.monotonic(), time.process_time()
        result["setupOutcome"] = "succeeded"
    except BaseException as exc:
        result["setupOutcome"] = "assertion" if isinstance(exc, AssertionError) else "unexpected_exception"
        result["exceptionType"] = type(exc).__name__
        result["exceptionMessage"] = str(exc)
        result["traceback"] = traceback.format_exc()
        if isinstance(exc, AssertionError) and len(exc.args) == 1 and isinstance(exc.args[0], dict):
            result["response"] = exc.args[0]
    finally:
        result["setupWallSeconds"] = ended - start
        result["setupCpuSeconds"] = cpu_ended - cpu
        result["cpuContextAfterSetup"] = cpu_context()
        write_json(slot / "SETUP-RESULT.json", result)
    seed = Path(cls.seed.name) if hasattr(cls, "seed") else None
    try:
        result["store"] = inspect_store(seed, slot)
    except BaseException as exc:
        result["storeInspectionError"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        try:
            if hasattr(cls, "seed"):
                cls.tearDownClass()
            result["originalClassCleanup"] = seed is None or not seed.exists()
        except BaseException as exc:
            result["originalClassCleanup"] = False
            result["cleanupError"] = repr(exc)
    if profile is not None:
        try:
            profile_reports(profile, slot)
        except BaseException as exc:
            result["profileReportError"] = {"type": type(exc).__name__, "message": str(exc),
                                            "traceback": traceback.format_exc()}
    after = snapshot(repo, plan)
    result["sourceAndInputsUnchanged"] = before == after
    result["semanticExportModuleImported"] = "ontokin.semantic_export" in sys.modules
    result["finishedAtUtc"] = utc()
    write_json(slot / "SETUP-RESULT.json", result)
    return 0 if result["setupOutcome"] == "succeeded" else 1 if result["setupOutcome"] == "assertion" else 2


def group_present(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def signal_group(pgid, signum):
    try:
        os.killpg(pgid, signum)
        return {"signal": signum, "sent": True}
    except ProcessLookupError:
        return {"signal": signum, "sent": False, "alreadyAbsent": True}


def supervise(args):
    repo = args.repository.resolve()
    output = args.output.absolute()
    require(not output.is_symlink() and not output.resolve().is_relative_to(repo),
            "Evidence output must be outside source and must not be a symlink")
    plan_path, approval_path, identity_path = args.plan.resolve(), args.approval.resolve(), args.identity_review.resolve()
    plan, approval, before = admission(repo, plan_path, approval_path, identity_path)
    require(not output.exists(), "Output directory already exists; no replay or automatic retry")
    output.mkdir(parents=True)
    write_json(output / "INPUTS.json", before)
    for path, name in [(plan_path, "REVIEWED-PLAN.json"), (approval_path, "APPROVAL.json"),
                       (identity_path, "IDENTITY-REVIEW.txt")]:
        shutil.copyfile(path, output / name)
    report = {"schema": SCHEMA, "startedAtUtc": utc(), "slots": [],
              "aggregateRun": False, "repairPerformed": False, "nativeStarts": 0,
              "scriptSha256": digest(__file__), "planSha256": digest(plan_path),
              "approvalSha256": digest(approval_path), "identityReviewSha256": digest(identity_path),
              "plannedChildStarts": 2, "plannedSetupInvocations": 2,
              "productTestMethods": 0, "stopReason": None}
    for index, mode in enumerate(plan["modes"], 1):
        require(snapshot(repo, plan) == before, "Source changed between slots")
        slot = output / (str(index) + "-" + mode)
        slot.mkdir()
        temporary = slot / "temporary"
        temporary.mkdir()
        consumed = {"slot": index, "mode": mode, "consumedAtUtc": utc(),
                    "replayAllowed": False, "setupInvocationsAllowed": 1,
                    "expectedParentPid": os.getpid(), "sourceCommit": before["commit"],
                    "sourceTree": before["tree"], "harnessSha256": digest(__file__),
                    "planSha256": digest(plan_path), "approvalSha256": digest(approval_path),
                    "identityReviewSha256": digest(identity_path),
                    "originalSetupOperations": ["seed-create", "seed-export"]}
        with (slot / "CONSUMED.json").open("x") as stream:
            json.dump(consumed, stream, indent=2)
        command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
            "--child-mode", mode, "--repository", str(repo), "--output", str(slot),
            "--plan", str(plan_path), "--approval", str(approval_path), "--identity-review", str(identity_path)]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
                           TMPDIR=str(temporary), TEMP=str(temporary), TMP=str(temporary))
        started = time.monotonic()
        receipt = {"slot": index, "mode": mode, "command": command, "cwd": str(slot),
                   "startedAtUtc": utc(), "timeoutSeconds": 90, "timedOut": False,
                   "envOverrides": {name: environment[name] for name in
                                    ("PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "TMPDIR", "TEMP", "TMP")}}
        process = None
        receipt["signals"] = []
        try:
            with (slot / "stdout.log").open("wb") as stdout, (slot / "stderr.log").open("wb") as stderr:
                process = subprocess.Popen(command, cwd=slot, env=environment, stdout=stdout,
                                           stderr=stderr, start_new_session=True)
                receipt.update(pid=process.pid, processGroup=process.pid)
                try:
                    process.wait(timeout=90)
                except subprocess.TimeoutExpired:
                    receipt["timedOut"] = True
                    receipt["signals"].append(signal_group(process.pid, signal.SIGTERM))
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        receipt["signals"].append(signal_group(process.pid, signal.SIGKILL))
                        process.wait(timeout=5)
        except BaseException as exc:
            receipt["supervisorError"] = {"type": type(exc).__name__, "message": str(exc),
                                           "traceback": traceback.format_exc()}
        finally:
            if process is not None and group_present(process.pid):
                receipt["residualGroupTerminated"] = True
                receipt["signals"].append(signal_group(process.pid, signal.SIGKILL))
                if process.poll() is None:
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        receipt["remainingProcessWaitExpired"] = True
            receipt.update(exitCode=process.returncode if process is not None else None,
                           durationSeconds=time.monotonic() - started,
                           finishedAtUtc=utc(), processGroupAbsent=process is not None and not group_present(process.pid))
        write_json(slot / "PROCESS.json", receipt)
        report["slots"].append(receipt)
        result_path = slot / "SETUP-RESULT.json"
        result = json.loads(result_path.read_text()) if result_path.exists() else None
        store = result.get("store", {}) if result else {}
        valid_store = (store.get("available") is True and store.get("rawBytesUnchangedAfterInspection") is True
            and len(store.get("databases", [])) == 1
            and all(db.get("integrityCheck") == ["ok"] for db in store.get("databases", []))
            and all(artifact.get("artifactIdMatchesBytes") and artifact.get("storedSha256MatchesBytes")
                    for db in store.get("databases", []) for artifact in db.get("artifacts", [])))
        valid_result = result is not None and result.get("sourceAndInputsUnchanged") is True and result.get("originalClassCleanup") is True and valid_store and not result.get("profileReportError")
        expected_outcome = result is not None and (result.get("setupOutcome") == "succeeded" or (
            result.get("setupOutcome") == "assertion" and result.get("response", {}).get("request_id") == "seed-export"
            and result.get("response", {}).get("program_revision") == plan["programRevision"]
            and result.get("response", {}).get("execution_budget", {}).get("effective") == plan["productLimits"]
            and result.get("response", {}).get("execution_budget", {}).get("host_ceilings") == plan["productLimits"]
            and result.get("response", {}).get("execution_budget", {}).get("budget_reason") == "execution_deadline_exceeded"))
        expected_exit = 0 if result and result.get("setupOutcome") == "succeeded" else 1
        if (receipt["timedOut"] or not receipt["processGroupAbsent"] or receipt.get("residualGroupTerminated")
                or receipt.get("supervisorError") or receipt["exitCode"] != expected_exit
                or not valid_result or not expected_outcome):
            report["stopReason"] = "Incomplete evidence, unexpected outcome, timeout, residue, cleanup failure, or input change; no later slot or retry"
            write_json(output / "RUN-SUMMARY.json", report)
            break
        write_json(output / "RUN-SUMMARY.json", report)
    report["finishedAtUtc"] = utc()
    report["sourceAndInputsUnchanged"] = snapshot(repo, plan) == before
    report["consumedSlots"] = len(report["slots"])
    report["remainingSlots"] = [mode for mode in plan["modes"] if mode not in [row["mode"] for row in report["slots"]]]
    report["scopeComplete"] = len(report["slots"]) == 2 and report["stopReason"] is None
    report["interpretation"] = "Diagnostic execution accounting only; no regression gate is passed by these two setup calls"
    write_json(output / "RUN-SUMMARY.json", report)
    write_json(output / "EVIDENCE-SHA256.json", {"files": inventory_files(output)})
    print(json.dumps({key: report[key] for key in ("scopeComplete", "consumedSlots", "stopReason", "sourceAndInputsUnchanged")}))
    return 0 if report["scopeComplete"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--identity-review", type=Path, required=True)
    parser.add_argument("--child-mode", choices=["baseline", "cprofile"])
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.preflight_only:
        _, _, source = admission(args.repository.resolve(), args.plan.resolve(), args.approval.resolve(), args.identity_review.resolve())
        print(json.dumps({"preflightPassed": True, "productStarts": 0, "sourceCommit": source["commit"], "sourceTree": source["tree"]}))
        return 0
    return child(args) if args.child_mode else supervise(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc),
                          "instruction": "Preserve any partial output; do not replay consumed slots"}), file=sys.stderr)
        raise SystemExit(2)
