#!/usr/bin/env python3
"""Retain all frozen source projections and their complete original callback traces."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.source))
    from ontokin.construction import compile_construction
    from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
    from ontokin.texture_bundle import load_texture_file_manifest
    from ontokin.torque_source import source_intervals
    results = []
    for case in json.loads((args.freeze / "state-expectations.json").read_bytes())["cases"]:
        trace, armed = [], False
        def callback():
            if armed:
                trace.append([ledger.stage, ledger.operations])
        bundle = load_texture_file_manifest(args.freeze / (case["case"] + ".files.json"))
        ledger = SharedExecutionBudget(check=callback)
        admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
        compiler = compile_construction(bundle, execution_budget=ledger)
        armed = True
        before = ledger.operations
        previous_hook = ledger._torque_context_guard
        previous_observer = compiler.reach_work._source_after_charge
        rows = source_intervals(compiler, case["target_path"], compiler.budget)
        result = {"case": case["case"], "records": rows, "trace": trace,
                  "consumed_delta": ledger.operations - before,
                  "original_callback_retained": ledger.check is callback,
                  "original_hook_restored": ledger._torque_context_guard is previous_hook,
                  "original_observer_restored": compiler.reach_work._source_after_charge is previous_observer}
        if not all(result[key] for key in ("original_callback_retained", "original_hook_restored", "original_observer_restored")):
            raise AssertionError(case["case"])
        (args.output / (case["case"] + ".json")).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        results.append({"case": case["case"], "sha256": hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()})
    report = {"status": "passed", "cases": len(results), "results": results,
              "source_hashes": {str(path.relative_to(args.source)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted((args.source / "ontokin").glob("*.py"))}}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "passed", "cases": len(results)}))


if __name__ == "__main__":
    main()
