"""Verify current construction tests and retain historical external evidence honestly.

The C20 destination evidence is immutable and tied to the original package hash.
A source change cannot inherit that identity. Fresh current-format/browser checks
run in the independent GitHub Actions visual job; this guard does not claim C20
passed for a modified implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ontokin.bundle import load_bundle
from ontokin.construction_conformance import (
    DEFAULT_FIXTURES, run_conformance, verify_external_evidence,
)

IDENTITY_MISMATCH = "The external run does not match the current implementation identity."


def assess(current: dict, historic: dict, original_implementation: dict) -> dict:
    """Reject any test failure, evidence corruption, or unaccounted-for pending case."""
    cases = {item["id"]: item for item in current["cases"]}
    if len(cases) != 20 or current["summary"]["total"] != 20:
        raise ValueError("All twenty construction cases must execute.")
    if current["run_issues"] or current["summary"]["failed"]:
        raise ValueError("The current construction run failed a requirement or its consistency checks.")
    if historic["status"] != "passed" or historic["issues"]:
        raise ValueError("The original, commit-pinned external evidence no longer verifies.")
    if current["implementation"] == original_implementation:
        if any(case["status"] != "passed" for case in cases.values()):
            raise ValueError("The original implementation must pass every adopted C case.")
        return {"current_gate": "passed", "historical_external_gate": "passed",
                "fresh_destination_verification": "separate_required_ci_job"}
    for number in range(1, 20):
        if cases[f"C{number:02}"]["status"] != "passed":
            raise ValueError(f"Current C{number:02} did not pass.")
    c20 = cases["C20"]
    if (c20["status"] != "pending"
            or c20["pending_reasons"] != ["The identified independent visual-delivery gate is pending."]):
        raise ValueError("Only C20's original-build external identity may remain pending.")
    if current["external_evidence"]["issues"] != [IDENTITY_MISMATCH]:
        raise ValueError("The retained destination evidence has unexpected mismatches.")
    if current["summary"]["passed"] != 19 or current["summary"]["pending"] != 1:
        raise ValueError("The current construction acceptance summary is inconsistent.")
    return {"current_gate": "C01-C19 passed; C20 pending a matching destination evidence run",
            "historical_external_gate": "passed",
            "fresh_destination_verification": "separate_required_ci_job"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.external_evidence.read_text(encoding="utf-8"))
    original = manifest["implementation"]
    frozen = load_bundle(json.loads(
        (DEFAULT_FIXTURES / "01-keyed-rack/program.bundle.json").read_text(encoding="utf-8")))
    current = run_conformance(external_evidence=args.external_evidence)
    historic = verify_external_evidence(args.external_evidence,
                                        implementation=original, expected_program=frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    result = assess(current, historic, original)
    print(json.dumps({"output": str(args.output), "summary": current["summary"],
                      "evidence_status": result, "unique_tests": current["test_execution"]["unique_required"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
