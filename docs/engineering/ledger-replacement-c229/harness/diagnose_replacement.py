"""Finite C229 observation harness; it never modifies product source."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
import unittest

METHOD = "test_corrupt_replaced_aliased_or_missing_files_poison_live_capability"
CHILD_START_EVENTS = {"subprocess.Popen", "os.fork", "os.forkpty", "os.posix_spawn", "os.system", "os.exec"}
START_ATTEMPTS = []


def forbid_child(event, args):
    if event in CHILD_START_EVENTS:
        START_ATTEMPTS.append({"event": event, "arguments": repr(args)[:1000]})
        raise RuntimeError("C229 worker child-process start is forbidden")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stat_value(info):
    return {key: getattr(info, key) for key in (
        "st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid",
        "st_size", "st_atime_ns", "st_mtime_ns", "st_ctime_ns")}


def state(path):
    try:
        return {"exists": True, **stat_value(path.lstat())}
    except FileNotFoundError:
        return {"exists": False}


def descriptor_inventory():
    rows = []
    for entry in sorted(Path("/proc/self/fd").iterdir(), key=lambda p: int(p.name)):
        try:
            info = os.fstat(int(entry.name))
            rows.append({"fd": int(entry.name), "target": os.readlink(entry), **stat_value(info)})
        except OSError as exc:
            rows.append({"fd": int(entry.name), "observation_error": type(exc).__name__, "errno": exc.errno})
    return rows


def exception_chain(exc):
    rows, seen = [], set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        rows.append({"type": type(exc).__name__, "message": str(exc),
                     "code": getattr(exc, "code", None), "consumed": getattr(exc, "consumed", None)})
        exc = exc.__cause__ if exc.__cause__ is not None else exc.__context__
    return rows


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


class CapturedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subtests = []

    def addSubTest(self, test, subtest, err):
        row = {"test": test.id(), "parameters": dict(subtest.params),
               "status": "passed" if err is None else "failed" if issubclass(err[0], test.failureException) else "error"}
        if err:
            row["traceback"] = "".join(traceback.format_exception(*err))
        self.subtests.append(row)
        super().addSubTest(test, subtest, err)


def original_method(source, output):
    spec = importlib.util.spec_from_file_location(
        "test_static_tray_admission_c201_ledger",
        source / "tests/test_static_tray_admission_c201_ledger.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    suite = unittest.TestSuite([module.LedgerControls(METHOD)])
    result = unittest.TextTestRunner(verbosity=2, resultclass=CapturedResult).run(suite)
    report = {"schema": "ontokin.c229.original-method-observation/0.1",
              "completed": True, "method": METHOD, "tests_run": result.testsRun,
              "successful": result.wasSuccessful(), "subtests": result.subtests,
              "failures": [{"test": str(test), "traceback": text} for test, text in result.failures],
              "errors": [{"test": str(test), "traceback": text} for test, text in result.errors],
              "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
              "child_start_attempts": START_ATTEMPTS,
              "source_method_modified": False, "instrumented_file_operations": False,
              "live_file_bytes_or_inodes_observed": False,
              "temporary_fixture_cleanup": "Original unittest cleanups executed by TestCase.run",
              "temporary_fixture_cleanup_observed_empty": not any(Path(os.environ["TMPDIR"]).iterdir())}
    write_json(output / "result.json", report)
    return 0 if result.wasSuccessful() else 1


def observed_cases(source, output, scratch):
    from prototypes.static_tray_admission_c201.ledger import Ledger, MARKER, JOURNAL
    from prototypes.static_tray_admission_c201.schedule import LedgerError, SLOTS, expected_schedule
    row = SLOTS[0]
    cases = [("marker-no-held-fd", MARKER, False), ("journal-no-held-fd", JOURNAL, False),
             ("marker-held-fd-control", MARKER, True), ("journal-held-fd-control", JOURNAL, True)]
    results, retained = [], []
    # A pre-opened event file preserves exact original bytes before destructive mutation.
    # Appends do not allocate another file inode between unlink and recreation.
    event_path = output / "observations.jsonl"
    event_stream = event_path.open("x")
    def record(event, payload):
        event_stream.write(json.dumps({"event": event, "payload": payload}, sort_keys=True) + "\n")
        event_stream.flush()
        os.fsync(event_stream.fileno())
    for case_id, name, hold in cases:
        case_root = scratch / case_id
        case_root.mkdir()
        authority, destination = case_root / "authority", case_root / "output"
        authority.mkdir(mode=0o700)
        destination.mkdir()
        ledger = Ledger.begin(authority, destination, expected_schedule())
        path = authority / name
        original_files = {n: (authority / n).read_bytes() for n in (MARKER, JOURNAL)}
        original = original_files[name]
        initial = state(path)
        held_fd = None
        evidence = {"case": case_id, "name": name, "retained_descriptor_intervention": hold,
                    "authority": str(authority), "output": str(destination),
                    "invocation_id": ledger.snapshot()["invocation_id"],
                    "before_path": initial,
                    "stored_identity": {"marker": list(ledger._marker_identity), "journal": list(ledger._journal_identity)},
                    "original_content_sha256": digest(original), "original_content_bytes": len(original),
                    "before_snapshot": ledger.snapshot(), "observation_started_ns": time.monotonic_ns()}
        record("before-mutation", {"observation": evidence,
                                   "files_hex": {n: data.hex() for n, data in original_files.items()}})
        try:
            if hold:
                held_fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                evidence["held_fd"] = held_fd
                evidence["held_fd_before_unlink"] = stat_value(os.fstat(held_fd))
            descriptors = descriptor_inventory()
            evidence["descriptors_before_unlink"] = descriptors
            evidence["matching_descriptors_before_unlink"] = [x["fd"] for x in descriptors
                if (x.get("st_dev"), x.get("st_ino")) == (initial["st_dev"], initial["st_ino"])]
            if (not hold and evidence["matching_descriptors_before_unlink"]) or (
                    hold and evidence["matching_descriptors_before_unlink"] != [held_fd]):
                raise RuntimeError("Unexpected retained original-file descriptor; stop without replacement")
            path.unlink()
            evidence["unlink_returned"] = True
            evidence["after_unlink_path"] = state(path)
            if evidence["after_unlink_path"]["exists"]:
                raise RuntimeError("Unlink did not leave the selected path absent")
            if hold:
                evidence["held_fd_after_unlink"] = stat_value(os.fstat(held_fd))
            bytes_written = path.write_bytes(original)
            evidence["rewrite_returned_bytes"] = bytes_written
            evidence["after_recreation_path"] = state(path)
            recreated_files = {n: (authority / n).read_bytes() for n in (MARKER, JOURNAL)}
            evidence["recreated_content_sha256"] = digest(recreated_files[name])
            evidence["recreated_content_identical"] = recreated_files[name] == original
            evidence["device_inode_reused"] = (initial["st_dev"], initial["st_ino"]) == (
                evidence["after_recreation_path"]["st_dev"], evidence["after_recreation_path"]["st_ino"])
            if hold:
                evidence["held_fd_after_recreation"] = stat_value(os.fstat(held_fd))
            evidence["descriptors_before_reserve"] = descriptor_inventory()
            record("after-recreation", {"observation": evidence,
                                        "files_hex": {n: data.hex() for n, data in recreated_files.items()}})
            try:
                receipt = ledger.reserve(row.name, row.route, "construction", references=row.references())
                evidence["first_reserve"] = {"outcome": "returned", "receipt": dict(vars(receipt))}
            except LedgerError as exc:
                evidence["first_reserve"] = {"outcome": "LedgerError", "exception_chain": exception_chain(exc)}
            evidence["after_first_reserve_snapshot"] = ledger.snapshot()
            after_first = {n: (authority / n).read_bytes() for n in (MARKER, JOURNAL)}
            record("after-first-reserve", {"observation": evidence,
                                          "files_hex": {n: data.hex() for n, data in after_first.items()}})
            if evidence["first_reserve"]["outcome"] == "LedgerError":
                try:
                    retry = ledger.reserve(row.name, row.route, "construction", references=row.references())
                    evidence["poison_check"] = {"outcome": "returned", "receipt": dict(vars(retry))}
                except LedgerError as exc:
                    evidence["poison_check"] = {"outcome": "LedgerError", "exception_chain": exception_chain(exc)}
            else:
                evidence["poison_check"] = {"outcome": "not_run", "reason": "No initial rejection; another reservation would test stage order instead"}
            evidence["after_poison_check_snapshot"] = ledger.snapshot()
            after_poison = {n: (authority / n).read_bytes() for n in (MARKER, JOURNAL)}
            evidence["final_path"] = state(path)
            if hold:
                evidence["held_fd_before_close"] = stat_value(os.fstat(held_fd))
            retained.append((case_id, {"original": original_files, "recreated": recreated_files,
                                      "after-first-reserve": after_first, "after-poison-check": after_poison}))
        finally:
            if held_fd is not None:
                os.close(held_fd)
                try:
                    os.fstat(held_fd)
                    evidence["held_fd_closed"] = False
                except OSError:
                    evidence["held_fd_closed"] = True
            else:
                evidence["held_fd_closed"] = None
            evidence["observation_finished_ns"] = time.monotonic_ns()
            results.append(evidence)
            record("case-finally", evidence)
    event_stream.close()
    # Delay supplementary evidence-file allocation until all four mutations and reservations finish.
    artifact_records = []
    for case_id, stages in retained:
        for stage, files in stages.items():
            directory = output / "retained-bytes" / case_id / stage
            directory.mkdir(parents=True)
            for name, data in files.items():
                path = directory / name
                path.write_bytes(data)
                artifact_records.append({"path": str(path.relative_to(output)), "bytes": len(data), "sha256": digest(data)})
    report = {"schema": "ontokin.c229.replacement-observations/0.1", "completed": True,
              "case_count": len(results), "cases": results, "retained_bytes": artifact_records,
              "child_start_attempts": START_ATTEMPTS,
              "cleanup": {"retained_descriptors_closed": all(x["held_fd_closed"] is not False for x in results),
                          "authority_fixtures_retained_as_evidence": True},
              "instrumentation_limit": "Extra lstat/fstat/read/proc observations and fsynced event recording alter timing. Original bytes are retained before mutation; no event write occurs between unlink and recreation. Held-FD cases intentionally keep the old unlinked object alive. No historical allocator sequence is reconstructed."}
    write_json(output / "result.json", report)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("original-method", "observed-cases"))
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir()
    args.scratch.mkdir()
    os.environ["TMPDIR"] = str(args.scratch)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.source))
    sys.addaudithook(forbid_child)
    write_json(args.output / "environment.json", {
        "pid": os.getpid(), "pgid": os.getpgrp(), "python": sys.version,
        "executable": sys.executable, "uname": dict(zip(("sysname", "nodename", "release", "version", "machine"), os.uname())),
        "machine": os.uname().machine, "cwd": str(Path.cwd()), "TMPDIR": str(args.scratch),
        "scratch_stat": stat_value(args.scratch.stat()),
        "mountinfo": Path("/proc/self/mountinfo").read_text(),
        "bytecode_writes_disabled": sys.dont_write_bytecode,
        "max_child_starts": 0, "mode": args.mode})
    try:
        if args.mode == "original-method":
            return original_method(args.source, args.output)
        return observed_cases(args.source, args.output, args.scratch)
    except BaseException as exc:
        write_json(args.output / "worker-error.json", {
            "completed": False, "exception_chain": exception_chain(exc), "traceback": traceback.format_exc(),
            "child_start_attempts": START_ATTEMPTS})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
