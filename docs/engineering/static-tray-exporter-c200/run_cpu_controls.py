"""Run identified C200 CPU controls without silently skipping current dependencies.

The focused cohort starts no subprocess. The synthetic cohort starts exactly
three bounded read-only Node checkers when it succeeds, plus the unchanged
Node version and ldd inspections. Neither cohort starts Blender or a lifecycle
stub. Original test modules are read unchanged.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def binding(path):
    path = Path(path)
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size}


def flattened(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flattened(item)
        else:
            yield item


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.started_ids = []
        self.passed_ids = []

    def startTest(self, test):
        self.started_ids.append(test.id())
        super().startTest(test)

    def addSuccess(self, test):
        self.passed_ids.append(test.id())
        super().addSuccess(test)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", choices=("focused", "synthetic", "compiler"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pinned-exporter", type=Path)
    parser.add_argument("--dependencies-root", type=Path)
    parser.add_argument("--host-inventory", type=Path)
    parser.add_argument("--node", type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    loader = unittest.TestLoader()
    suites = []
    sources = [Path(__file__).resolve()]
    if args.cohort == "focused":
        names = ["tests.test_static_tray_source_v01", "tests.test_static_tray_source_resources_v01",
                 "tests.test_static_tray_reader_v01", "tests.test_static_tray_receiving_v01",
                 "tests.test_static_tray_transaction_v01", "tests.test_static_tray_finalization_v01",
                 "tests.test_static_tray_exporter_c200"]
        for name in names:
            module = importlib.import_module(name)
            sources.append(Path(module.__file__))
            suites.append(loader.loadTestsFromModule(module))
        readback = importlib.import_module("tests.test_static_tray_readback_v01")
        sources.append(Path(readback.__file__))
        suites.append(loader.loadTestsFromTestCase(readback.ReadbackCoordinatorSeams))
        if args.pinned_exporter is None:
            parser.error("Focused controls require the exact pinned exporter source")
        exporter_tests = importlib.import_module("tests.test_static_tray_exporter_c200")
        suites.append(exporter_tests.pinned_source_suite(args.pinned_exporter.resolve()))
        sources.append(args.pinned_exporter.resolve())
        sources.append(args.pinned_exporter.resolve().parent / "io/com/debug.py")
    elif args.cohort == "synthetic":
        if any(value is None for value in (args.dependencies_root, args.host_inventory, args.node)):
            parser.error("Synthetic controls require current dependencies, host inventory and Node")
        module = importlib.import_module("tests.test_static_tray_readback_v01")
        sources.extend([Path(module.__file__), ROOT / "tests/test_static_tray_reader_v01.py"])
        module.DEPS = args.dependencies_root.resolve()
        module.HOST = args.host_inventory.resolve()
        module.NODE = args.node.resolve()
        available = module.NODE.is_file() and module.DEPS.is_dir() and module.HOST.is_file()
        if not available:
            raise ValueError("The identified current dependencies are unavailable; no skip is permitted")
        # Reevaluate only the original environment-availability condition after
        # supplying the recovered paths. No assertion or test body changes.
        module.ReadbackCPUControls.__unittest_skip__ = not available
        module.ReadbackCPUControls.__unittest_skip_why__ = ""
        os.environ["STATIC_TRAY_READBACK_CPU_OUTPUT"] = str(out / "actual-node-controls")
        suites.append(loader.loadTestsFromTestCase(module.ReadbackCPUControls))
        sources.extend([module.HOST, module.DEPS / "tools/three_loader.mjs"])
    else:
        for name in ("tests.test_construction", "tests.test_construction_catalog", "tests.test_construction_conformance"):
            module = importlib.import_module(name)
            sources.append(Path(module.__file__))
            suites.append(loader.loadTestsFromModule(module))
    unique = {}
    discovered = []
    for test in flattened(unittest.TestSuite(suites)):
        discovered.append(test.id())
        unique.setdefault(test.id(), test)
    if args.cohort == "synthetic" and len(unique) != 3:
        raise ValueError("The separately authorized synthetic cohort must contain exactly three methods")
    source_rows = [binding(path) for path in sorted(set(sources))]
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    tree = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).splitlines()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    initial = {"schema": "ontokin.c200.cpu-controls/0.1", "cohort": args.cohort, "started_at_utc": started,
               "implementation_commit": commit, "implementation_tree": tree, "worktree_status": dirty,
               "command": [sys.executable, *sys.orig_argv[1:]], "python_version": platform.python_version(),
               "platform": platform.platform(), "sources": source_rows, "discovered_ids": discovered,
               "unique_planned_ids": list(unique), "duplicate_discovery_count": len(discovered) - len(unique),
               "native_starts": 0, "receiving_starts": 0, "lifecycle_starts": 0,
               "scope": "CPU compatibility and independent-reader preparation; no native qualification"}
    (out / "INPUTS.json").write_text(json.dumps(initial, indent=2, sort_keys=True) + "\n")
    with (out / "tests.log").open("w") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, failfast=True,
                                        resultclass=RecordedResult).run(unittest.TestSuite(unique.values()))
    if [binding(path) for path in sorted(set(sources))] != source_rows:
        raise RuntimeError("Control inputs changed during execution")
    passed = result.wasSuccessful() and not result.skipped and result.testsRun == len(unique)
    receipt = {**initial, "finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "status": "PASS" if passed else "FAIL", "tests_run": result.testsRun,
               "passed_ids": result.passed_ids, "started_ids": result.started_ids,
               "errors": [{"id": test.id(), "traceback": text} for test, text in result.errors],
               "failures": [{"id": test.id(), "traceback": text} for test, text in result.failures],
               "skipped": [{"id": test.id(), "reason": reason} for test, reason in result.skipped],
               "log": binding(out / "tests.log")}
    if args.cohort == "synthetic":
        processes = sorted((out / "actual-node-controls").glob("*/synthetic-readback.process.json"))
        receipt["read_only_node_process_receipts"] = [binding(path) for path in processes]
        receipt["read_only_node_starts"] = len(processes)
        receipt["dependency_inspections"] = ["Node --version", "ldd Node executable"]
        if passed and len(processes) != 3:
            receipt["status"] = "FAIL"
            receipt["count_error"] = "Expected three actual read-only process receipts"
            passed = False
    (out / "RESULTS.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "cohort": args.cohort, "tests_run": result.testsRun,
                      "skipped": len(result.skipped), "result": str(out / "RESULTS.json")}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
