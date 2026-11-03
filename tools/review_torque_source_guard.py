#!/usr/bin/env python3
"""Replay the native source-projection bookkeeping witness on explicit bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.source))
    from ontokin.agent import implementation_identity
    from ontokin.construction import compile_construction
    from ontokin.diagnostics import OntoKinError
    from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
    from ontokin.program_diagnostics import diagnostic_dict
    from ontokin.texture_bundle import load_texture_file_manifest
    from ontokin.torque_source import source_intervals

    results = []
    for mutate in (False, True):
        bundle = load_texture_file_manifest(args.freeze / "p04-overlap.files.json")
        armed = False
        visits = []
        def callback():
            if not armed or ledger.stage != "torque_projection":
                return
            visits.append([ledger.operations, work.operations, dict(work.counts)])
            if mutate and len(visits) == 4:
                work.operations = 0
                work.counts.clear()
        ledger = SharedExecutionBudget(check=callback)
        admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
        compiler = compile_construction(bundle, execution_budget=ledger)
        work = compiler.reach_work
        before = [ledger.operations, work.operations, dict(work.counts)]
        hook, observer, stage = ledger._torque_context_guard, work._source_after_charge, ledger.stage
        armed = True
        rows, error = None, None
        try:
            rows = source_intervals(compiler, "ball", compiler.budget)
        except OntoKinError as caught:
            error = diagnostic_dict(caught.diagnostic, bundle)
        accepted = rows is not None
        result = {
            "case": "native-counter-reset" if mutate else "control",
            "program_revision": bundle.program_revision,
            "before": before, "visits": visits,
            "after": [ledger.operations, work.operations, dict(work.counts)],
            "accepted": accepted, "records": rows, "error": error,
            "original_callback_retained": ledger.check is callback,
            "original_hook_restored": ledger._torque_context_guard is hook,
            "original_observer_restored": work._source_after_charge is observer,
            "original_stage_restored": ledger.stage == stage,
        }
        result["passed"] = (
            all(result[key] for key in ("original_callback_retained", "original_hook_restored",
                                       "original_observer_restored", "original_stage_restored"))
            and ((not mutate and accepted and len(rows) == 2 and len(visits) == 5
                  and ledger.operations == before[0] + 5 and work.operations == before[1] + 2)
                 or (mutate and not accepted and len(visits) == 4 and error is not None
                     and error["code"] == "OKL-E-RESOURCE"
                     and error["details"]["budget_reason"] == "execution_context_required")))
        results.append(result)
    report = {
        "schema_version": "ontokin.c091-source-counter-review/1",
        "source_commit": subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip(),
        "implementation_identity": implementation_identity(),
        "source_hashes": {str(path.relative_to(args.source)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted((args.source / "ontokin").glob("*.py"))},
        "status": "passed" if all(result["passed"] for result in results) else "failed",
        "results": results,
    }
    (args.output / "result.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(results), "source_commit": report["source_commit"]}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
