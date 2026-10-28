#!/usr/bin/env python3
"""Measure the complete current regression inventory for reach development.

This actual execution supplies a compatibility component. The separate release
audit must establish all three interpreters, literal mappings and other roles.
"""
import argparse
import contextlib
import importlib.metadata
from pathlib import Path
import platform
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.reach_delivery_inventory import (ROOT, descriptor, finish_inputs,
    fresh_output, require, snapshot, utc, write_json)


def run(output):
    output = fresh_output(output)
    report = {"schema_version": "ontokin.reach-regression-execution/0.1",
        "status": "running", "executed": False, "provider": "local",
        "started_at": utc(), "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        "working_directory": str(ROOT), "release_acceptance": False,
        "full_product_goal_completed": False, "environment": {
            "python": platform.python_version(), "python_implementation": platform.python_implementation(),
            "executable": sys.executable, "platform": platform.platform(),
            "executable_file": descriptor(Path(sys.executable).resolve())}}
    before = None
    started = time.monotonic()
    with (output / "execution.log").open("x", encoding="utf-8") as stream:
        try:
            before = snapshot()
            write_json(output / "inputs-before.json", before)
            report.update(source_commit=before["git"]["commit"], source_tree=before["git"]["tree"])
            from ontokin.force_conformance import verification_pins
            pins = verification_pins()
            actual = {name: importlib.metadata.version(name) for name in pins}
            report["environment"]["verification_packages"] = actual
            require(actual == pins, "The complete six-package verification closure must match its pins")
            from ontokin import construction_conformance, surface_conformance
            names = surface_conformance.discover_test_ids()
            require(names and len(names) == len(set(names)), "The complete test inventory must be nonempty and unique")
            write_json(output / "test-inventory.json", {"test_ids": names})
            report["executed"] = True
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                execution = construction_conformance._run_tests(names)
            write_json(output / "test-results.json", execution)
            passed = surface_conformance._execution_passes(execution, names)
            report.update(status="passed" if passed else "failed", test_count=len(names),
                passed_count=sum(row["status"] == "passed" for row in execution["tests"]),
                outcomes=execution["outcomes"],
                nonpassing_test_ids=[row["test_id"] for row in execution["tests"] if row["status"] != "passed"],
                loader_errors=execution["loader_errors"], fixture_errors=execution["fixture_errors"],
                unexpected_test_records=execution["unexpected_test_records"])
        except Exception as error:
            report.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                          traceback=traceback.format_exc())
            traceback.print_exc(file=stream)
    finish_inputs(output, before, report)
    report.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started)
    report["members"] = [descriptor(path, relative_to=output) for path in sorted(output.iterdir()) if path.is_file()]
    write_json(output / "report.json", report)
    print({key: report.get(key) for key in ("status", "test_count", "passed_count", "outcomes", "inputs_stable", "failure")}, flush=True)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    return 0 if run(args.output_dir)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
