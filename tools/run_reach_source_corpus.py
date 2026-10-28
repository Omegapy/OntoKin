#!/usr/bin/env python3
"""Run the literal 45-case source cohort; preserve development evidence.

This does not certify source_execution or the complete finite release. Run in
the repository's exclusive executor window, with output outside the checkout.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.storage_identity import (PROFILE as STORAGE_PROFILE, SCHEMA as STORAGE_SCHEMA,
                                    StorageContext, StorageIdentityError, git as storage_git)

MAPPING = ROOT / "docs/engineering/reach-source-acceptance-validation/source-case-map.json"


def _git(*args):
    return storage_git(ROOT, *args)


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def _snapshot():
    try:
        return _storage_snapshot()
    except StorageIdentityError as error:
        raise RuntimeError(str(error)) from error


def _storage_snapshot():
    storage = StorageContext(ROOT, revision=None)
    if storage.algorithm != "sha1":
        raise RuntimeError("This source snapshot's existing Git-blob field requires SHA-1 Git objects")
    tracked = {name: (entry.mode, entry.blob) for name, entry in storage.entries.items()}
    names = set(tracked) | {p.decode() for p in _git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p}
    rows = []
    for name in sorted(names):
        binding = storage.verify_file(name)
        payload = binding["payload"]
        mode, _ = tracked.get(name, (None, None))
        row = {"path": name, "bytes": payload["bytes"], "sha256": payload["sha256"].removeprefix("sha256:"),
               "git_blob_sha1": payload["raw_git_blob"], "index_mode": mode, "tracked": name in tracked}
        if binding["kind"] == "git-lfs":
            row["storage_binding"] = binding
        rows.append(row)
    result = {"git_commit": _git("rev-parse", "HEAD").decode().strip(),
            "git_tree": _git("rev-parse", "HEAD^{tree}").decode().strip(),
            "git_status": _git("status", "--porcelain=v1", "--untracked-files=all").decode(),
            "input_count": len(rows), "inputs": rows}
    if storage.lfs_paths:
        result["storage_identity"] = {"schema_version": STORAGE_SCHEMA, "profile": STORAGE_PROFILE,
                                      "lfs_files": len(storage.lfs_paths), "network_transfers": False}
    return result


class _Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = []
        self.started = {}

    def startTest(self, test):
        self.started[test.id()] = time.monotonic()
        super().startTest(test)

    def _record(self, test, status, error=None):
        row = {"test_id": test.id(), "status": status}
        if test.id() in self.started:
            row["elapsed_seconds"] = time.monotonic() - self.started[test.id()]
        if error is not None:
            row["traceback"] = self._exc_info_to_string(error, test)
        self.results.append(row)

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "passed")

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self._record(test, "failed", error)

    def addError(self, test, error):
        super().addError(test, error)
        self._record(test, "error", error)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.results.append({"test_id": test.id(), "status": "skipped", "reason": reason})

    def addExpectedFailure(self, test, error):
        super().addExpectedFailure(test, error)
        self._record(test, "expected_failure", error)

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._record(test, "unexpected_success")

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error is not None:
            self.results.append({"test_id": test.id(), "subtest_id": subtest.id(),
                                 "status": "failed" if issubclass(error[0], test.failureException) else "error",
                                 "traceback": self._exc_info_to_string(error, test)})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New evidence directory outside this checkout")
    args = parser.parse_args(argv)
    destination = args.output.resolve()
    if destination.is_relative_to(ROOT) or destination.exists():
        parser.error("--output must be a new directory outside the checkout")
    destination.mkdir(parents=True)
    started_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    report = {"schema_version": "ontokin.reach-source-development-run/0.1",
              "status": "not_executed", "release_acceptance": False,
              "source_execution_role": "pending", "full_product_goal_completed": False,
              "remote_publication_verified": False,
              "provider": "local", "started_utc": started_utc,
              "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
              "working_directory": str(ROOT),
              "interpreter": {"path": sys.executable, "version": sys.version,
                              "implementation": platform.python_implementation()},
              "platform": platform.platform()}
    try:
        before = _snapshot()
        _write(destination / "inputs-before.json", before)
        mapping = json.loads(MAPPING.read_text())
        for name, wanted in mapping["frozen_input_hashes"].items():
            actual = "sha256:" + hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            if actual != wanted:
                raise RuntimeError("Mapped frozen input changed: " + name)
        sys.path[:0] = [str(ROOT / "tests"), str(ROOT)]
        import test_reach_source_corpus as corpus
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(corpus.ReachSourceCorpusTests)
        inventory = [test.id() for test in suite]
        expected = [row["test_id"] for row in mapping["cases"]]
        if len(inventory) != 45 or len(set(inventory)) != 45 or set(inventory) != set(expected):
            raise RuntimeError("Discovered source inventory differs from the published literal mapping")
        _write(destination / "inventory.json", {"test_count": len(inventory), "test_ids": inventory})
        with (destination / "tests.log").open("w", encoding="utf-8") as stream:
            result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=_Result).run(suite)
        _write(destination / "tests.json", {"test_count": result.testsRun, "results": result.results})
        _write(destination / "source-observations.json", {"cases": corpus.EXECUTION_RECORDS})
        after = _snapshot()
        _write(destination / "inputs-after.json", after)
        stable = before == after
        passed = result.wasSuccessful() and result.testsRun == 45 and not (
            result.skipped or result.expectedFailures or result.unexpectedSuccesses) and stable
        failed_ids = {row["test_id"] for row in result.results if row["status"] != "passed"}
        passed_ids = {row["test_id"] for row in result.results if row["status"] == "passed"}
        measurements = [row for case in corpus.EXECUTION_RECORDS for row in case["derivative_measurements"]]
        report.update(status="passed" if passed else "failed", git_commit=before["git_commit"],
                      git_tree=before["git_tree"], git_status=before["git_status"],
                      head_revision_contains_all_tested_inputs=not bool(before["git_status"]),
                      input_count=before["input_count"], inputs_stable=stable,
                      test_count=result.testsRun, passed_case_count=len(passed_ids),
                      failed_case_count=len(failed_ids & set(expected)), failures=len(result.failures), errors=len(result.errors),
                      skipped=len(result.skipped), expected_failures=len(result.expectedFailures),
                      unexpected_successes=len(result.unexpectedSuccesses),
                      world_derivative_measurement_count=len(measurements),
                      world_derivative_exact_match_count=sum(row["exact_binary64_equal"] for row in measurements),
                      pending_comparisons=["Explicit adopted acceptance bounds for derived world velocity and angular velocity"],
                      scope_limits=mapping["scope_limits"])
    except Exception as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
    report.update(ended_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started)
    report["outputs"] = [{"path": path.name, "bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                         for path in sorted(destination.iterdir()) if path.is_file()]
    _write(destination / "report.json", report)
    print(json.dumps({key: report[key] for key in ("status", "test_count", "passed_case_count", "failed_case_count", "inputs_stable", "error") if key in report}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
