"""Run only the reach fixture-precondition checks, never a release audit."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest

UPSTREAM_COMMIT = "1ed885c930da4adcb590d35f400b72dac57f9f74"
RECOVERED_BLOBS = {
    "ontokin/__init__.py": "64794b329c54f450faacea01aa940d8716bfb73a",
    "ontokin/diagnostics.py": "975f12a00a9c4be464f9465e42397220543b9794",
    "ontokin/bundle.py": "5cb479266c06c8c637a4e6019514f80534a2637b",
}
INPUTS = [*RECOVERED_BLOBS, "tests/reach_fixture_support.py",
          "tests/test_reach_fixture_preconditions.py", "tests/test_reach_reference.py",
          "tests/test_reach_agent_protocol_cases.py",
          "docs/engineering/reach-fixture-repair-validation/run_focused.py"]


def identify(root):
    result = {}
    for relative in INPUTS:
        raw = (root / relative).read_bytes()
        result[relative] = {
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    before = identify(root)
    for name, expected in RECOVERED_BLOBS.items():
        if before[name]["git_blob_sha1"] != expected:
            raise SystemExit(f"Recovered production input differs from its declared upstream blob: {name}")
    for relative in INPUTS:
        ast.parse((root / relative).read_text(encoding="utf-8"), filename=relative)
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "tests"))
    started = datetime.now(timezone.utc).isoformat()
    clock = time.perf_counter()
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_reach_fixture_preconditions.py")
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    elapsed = time.perf_counter() - clock
    after = identify(root)
    from test_reach_fixture_preconditions import ReachHandoffFixtureTests
    witnesses = []
    for target in ReachHandoffFixtureTests.TARGETS:
        rows = []
        for duration in (3, 5):
            ideal = Fraction(target) / (2 * duration)
            rounded = Fraction(float(ideal))
            rows.append({"duration_s": duration, "elapsed_s": "1/2",
                         "ideal_coordinate": str(ideal), "rounded_hex": float(ideal).hex(),
                         "rounding_error": str(rounded - ideal)})
        witnesses.append({"target_hex": target.hex(), "cases": rows})
    valid = (result.wasSuccessful() and result.testsRun == 11 and not result.skipped
             and not result.expectedFailures and not result.unexpectedSuccesses and before == after)
    report = {
        "schema_version": "ontokin.reach-fixture-repair-check/0.1",
        "status": "passed" if valid else "failed", "started_utc": started,
        "duration_seconds": elapsed, "upstream_commit": UPSTREAM_COMMIT,
        "environment": {"implementation": platform.python_implementation(),
                        "python": platform.python_version(), "platform": platform.platform()},
        "argv": [sys.executable, *sys.argv], "working_directory": str(Path.cwd()),
        "source_scope": "Eight exact identified files; partial recovery, not a complete repository checkout",
        "syntax_parsed_files": len(INPUTS),
        "tests": {"run": result.testsRun, "failures": len(result.failures),
                  "errors": len(result.errors), "skipped": len(result.skipped),
                  "expected_failures": len(result.expectedFailures), "unexpected_successes": len(result.unexpectedSuccesses)},
        "inputs_before": before, "inputs_after": after, "inputs_unchanged": before == after,
        "recovered_upstream_blobs_verified": RECOVERED_BLOBS,
        "exact_rounding_witnesses": witnesses,
        "full_runtime_suite": {"status": "not_run", "reason": "Complete compiler/evaluator/service checkout is absent in this execution environment"},
        "release_acceptance": "not_established", "hosted_execution": "not_dispatched",
    }
    (output / "tests.log").write_text(log.getvalue(), encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(log.getvalue(), end="")
    print(json.dumps({"status": report["status"], "inputs_unchanged": report["inputs_unchanged"], "report": str(output / "report.json")}))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
