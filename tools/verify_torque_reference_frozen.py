"""Execute the separately frozen scalar/history expectations on the reader.

This checks the independent reference against the frozen analytic inputs. It
does not run the producer and cannot certify a runtime, artifact or release.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.construction import compile_construction
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.reach_reference import Interval, build_reference


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("A fresh evidence output is required")
    frozen = ROOT / "docs/language-design/torque-v0.1/freeze"
    source_cases = json.loads((frozen / "physics-cases.json").read_text())["cases"]
    expectations = {row["case"]: row for row in json.loads((frozen / "state-expectations.json").read_text())["cases"]}
    rows, checks = [], 0
    def compare(actual, expected, path=()):
        nonlocal checks
        checks += 1
        if isinstance(actual, Interval):
            assert type(expected) in (int, float) and actual.contains(expected), (path, actual, expected)
        elif type(expected) is dict:
            assert type(actual) is dict and actual.keys() == expected.keys(), path
            for key in expected:
                compare(actual[key], expected[key], (*path, key))
        elif type(expected) is list:
            assert type(actual) is list and len(actual) == len(expected), path
            for index, value in enumerate(expected):
                compare(actual[index], value, (*path, index))
        else:
            assert actual == expected, (path, actual, expected)
    for case in source_cases:
        row = {"id": case["id"], "status": "running"}
        try:
            bundle = load_texture_file_manifest(frozen / case["file_manifest"])
            assert bundle.program_revision == case["identity"]["program_revision"]
            ledger = SharedExecutionBudget()
            admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
            compiler = compile_construction(bundle, execution_budget=ledger)
            reference = build_reference(compiler.model, end=F(case["horizon"]), mode="observation", work=compiler.reach_work)
            target = case["torques"][0]["target"]
            observed = []
            for observation in expectations[case["id"]]["observations"]:
                time, side = F(observation["time_fraction"]), observation["side"]
                actual = reference._torques(target, time, reference._state_at(time, side))
                for name, expected in observation["exact_fields"].items():
                    compare(actual[name], expected, (case["id"], observation["time_fraction"], side, name))
                observed.append({"time": str(time), "side": side, "status": "passed"})
            row.update(status="passed", observations=observed, operations=ledger.operations,
                       program_revision=bundle.program_revision)
        except Exception as error:
            row.update(status="failed", error_type=type(error).__name__, error=str(error),
                       traceback=traceback.format_exc())
        rows.append(row)
    result = {"schema_version": "ontokin.c091-independent-frozen-reference/1",
              "status": "passed" if all(row["status"] == "passed" for row in rows) else "failed",
              "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "checks": checks, "cases": rows,
              "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "input_hashes": {name: hashlib.sha256((frozen / name).read_bytes()).hexdigest()
                               for name in ("physics-cases.json", "state-expectations.json")},
              "scope": "Independent reference versus frozen analytic scalar/history expectations; no producer execution or artifact acceptance"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks": checks,
                      "passed": sum(row["status"] == "passed" for row in rows), "total": len(rows)}))
    return int(result["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
