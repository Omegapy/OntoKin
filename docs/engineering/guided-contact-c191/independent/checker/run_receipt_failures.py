#!/usr/bin/env python3
"""Independently check truthful commit results when auxiliary receipts fail.

These recovery probes exercise the actual transaction with a controlled copying
worker. They establish state/receipt failure behavior, not a new native solve.
They were added after source review of the recovered implementation.
"""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(directory):
    return {str(path.relative_to(directory)): digest(path)
            for path in sorted(directory.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}


def run(repo, formal, destination, revision, blender):
    destination.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import run as adapter_run
    schema = json.loads((repo / "docs/language-design/guided-contact-v0.1/output.schema.json").read_text())
    summary = json.loads((formal / "summary.json").read_text())
    assert summary["pass"] and summary["implementation_revision"] == revision
    seed = Path(next(row for row in summary["builds"] if row["case"] == "A" and row["repeat"] == 1)["artifact_directory"])
    specifications = [
        ("R01-committed-attempt-receipt", True, None, "result.json"),
        ("R02-rejected-attempt-receipt", False, "C191_E_INITIAL_OVERLAP", "result.json"),
        ("R03-orphan-candidate-receipt", False, "C191_E_PUBLICATION", "unreferenced-candidate.json"),
        ("R04-optional-output-error-receipt", True, None, "optional-result-error.json"),
    ]
    lock = {"implementation_revision": revision, "prototype_files": inventory(repo / "prototypes/guided_contact_v01"),
            "checker_sha256": digest(__file__), "formal_summary_sha256": digest(formal / "summary.json"),
            "formal_native_result_sha256": digest(seed / "native-result.json"),
            "scope": "Controlled IO faults at the actual receipt and state replacement paths; no fresh native contact claim"}
    (destination / "INPUT-LOCK.json").write_text(json.dumps(lock, indent=2) + "\n")
    records = []
    original_write = Path.write_bytes
    for name, expect_commit, expected_code, denied_name in specifications:
        directory = destination / name
        directory.mkdir()
        store = directory / "store"
        shutil.copytree(seed.parents[1], store)
        state_before = (store / "state.json").read_bytes()
        old = json.loads(state_before)
        old_artifacts = store / old["artifact_directory"]
        old_inventory = inventory(old_artifacts)
        stderr = io.StringIO()
        faults = []
        record = {"id": name, "expected_committed": expect_commit, "expected_code": expected_code, "pass": False}
        source = HERE.parent / "source-fixtures" / ("N10-initial-overlap.ok" if name.startswith("R02") else "A.ok")
        hooks = {"worker_command": lambda argv, stage: [sys.executable, "-B", str(HERE / "lifecycle_worker.py"),
                                                       "copy", str(stage), "--seed", str(seed)]}
        if name.startswith("R03"):
            def reject_pointer(temporary, target):
                faults.append("atomic_state_replace")
                raise OSError("Independent injected atomic state replacement failure")
            hooks["replace_state"] = reject_pointer
        options = {"result_path": directory / "absent-parent" / "result.json"} if name.startswith("R04") else {}
        def denied_write(path, data):
            if path.name == denied_name and path.parent.parent == store / "attempts":
                faults.append(str(path.relative_to(store)))
                raise OSError("Independent injected auxiliary receipt failure: " + denied_name)
            return original_write(path, data)
        try:
            with patch.object(Path, "write_bytes", denied_write), contextlib.redirect_stderr(stderr):
                result = adapter_run(source, store=store, blender=blender,
                    host_max_operations=1000000, host_max_elapsed_ms=80000,
                    expected_revision=old["accepted_revision"], hooks=hooks, **options)
            (directory / "returned-result.json").write_text(json.dumps(result, indent=2) + "\n")
            errors = list(Draft202012Validator(schema).iter_errors(result))
            assert not errors, "; ".join(error.message for error in errors)
            assert faults and any(item.endswith(denied_name) for item in faults), "Receipt fault did not execute"
            assert result["successful"] == result["committed"] == expect_commit, "Returned result contradicts commit state"
            state_after = (store / "state.json").read_bytes()
            assert (state_after != state_before) == expect_commit, "State-pointer change disagrees with returned commit"
            assert inventory(old_artifacts) == old_inventory, "Previous accepted artifacts changed"
            if expect_commit:
                accepted = json.loads(state_after)
                assert result["diagnostics"] == []
                assert Path(result["artifact_directory"]) == store / accepted["artifact_directory"]
                assert result["accepted_revision"] == accepted["accepted_revision"] == digest(source)
                assert Path(result["artifact_directory"]).is_dir()
                assert result["levels"]["exported"] and not result["levels"]["destination_validated"]
            else:
                diagnostic, = result["diagnostics"]
                assert diagnostic["code"] == expected_code
                assert result["accepted_revision"] == old["accepted_revision"]
                assert all(not result["levels"][level] for level in diagnostic["blocked_levels"])
            assert stderr.getvalue(), "Receipt loss was not reported to the caller"
            record["pass"] = True
            record["committed"] = result["committed"]
            record["pointer_changed"] = state_after != state_before
            record["previous_artifacts_unchanged"] = True
        except Exception as error:
            record["failure"] = type(error).__name__ + ": " + str(error)
            record["pointer_changed"] = (store / "state.json").read_bytes() != state_before
            record["previous_artifacts_unchanged"] = inventory(old_artifacts) == old_inventory
        record["injected_faults"] = faults
        record["stderr"] = stderr.getvalue()
        (directory / "review.json").write_text(json.dumps(record, indent=2) + "\n")
        records.append(record)
    unchanged = inventory(repo / "prototypes/guided_contact_v01") == lock["prototype_files"]
    return {"version": "C191-independent-receipt-failure-checks-1", "implementation_revision": revision,
            "input_lock_sha256": digest(destination / "INPUT-LOCK.json"), "snapshot_inputs_unchanged": unchanged,
            "written_after_recovered_candidate_inspection": True, "cases": records,
            "passed": sum(row["pass"] for row in records), "total": len(records),
            "pass": unchanged and all(row["pass"] for row in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--blender", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.repo.resolve(), args.formal.resolve(), args.out.resolve(), args.revision, args.blender.resolve())
    (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"pass": result["pass"], "passed": result["passed"], "total": result["total"],
                      "failures": [row for row in result["cases"] if not row["pass"]]}, indent=2))
    raise SystemExit(0 if result["pass"] else 1)
