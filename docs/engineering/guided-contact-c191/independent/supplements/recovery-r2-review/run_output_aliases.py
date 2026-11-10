#!/usr/bin/env python3
"""Post-inspection C191 output-path preservation probes through public APIs.

Every store and input is copied into a fresh probe directory. No shared frozen
source or accepted seed is exposed to a deliberately unsafe output path.
"""
import argparse
import contextlib
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import traceback

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
INDEPENDENT = HERE.parents[1]
CHECKER = INDEPENDENT / "checker"
sys.path.insert(0, str(CHECKER))
from run_lifecycle import digest, inventory, source_span


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def alias(path, target, kind):
    if kind == "direct":
        return target
    if kind == "symlink":
        path.symlink_to(target)
    elif kind == "hardlink":
        os.link(target, path)
    else:
        raise ValueError(kind)
    return path


def run(repo, seed_store, blender, destination, revision):
    destination.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import run as adapter_run, validate_source
    contract = repo / "docs/language-design/guided-contact-v0.1"
    schema = json.loads((contract / "output.schema.json").read_text())
    rules = {row["code"]: row for row in json.loads((contract / "diagnostics.json").read_text())["codes"]}
    sources = INDEPENDENT / "source-fixtures"
    source_manifest = json.loads((sources / "manifest.json").read_text())
    invalid = next(row for row in source_manifest["fixtures"] if row["id"] == "N10-initial-overlap")
    seed_state = json.loads((seed_store / "state.json").read_text())
    seed = seed_store / seed_state["artifact_directory"]
    lock = {"implementation_revision": revision, "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "argv": sys.argv, "python": platform.python_version(), "checker_sha256": digest(__file__),
        "prototype_files": inventory(repo / "prototypes/guided_contact_v01"),
        "contract_files": inventory(contract), "seed_native_sha256": digest(seed / "native-result.json"),
        "seed_scene_sha256": digest(seed / "scene.blend"), "blender_sha256": digest(blender),
        "written_after_candidate_source_inspection": True, "new_native_solve_claimed": False}
    save(destination / "INPUT-LOCK.json", lock)
    (destination / "executed-checker.py").write_bytes(Path(__file__).read_bytes())
    records = []

    run_cases = [(target + "-" + kind + "-" + status, target, kind, status)
                 for target in ("state", "artifact", "source")
                 for kind in ("direct", "symlink") for status in ("valid", "invalid")]
    run_cases += [("state-outside-hardlink-valid", "state", "hardlink", "valid"),
                  ("artifact-outside-hardlink-valid", "artifact", "hardlink", "valid"),
                  ("source-hardlink-valid", "source", "hardlink", "valid"),
                  ("external-receipt-valid", "external", "direct", "valid"),
                  ("late-state-symlink-valid", "late-state", "symlink", "valid"),
                  ("reopen-input-alias-valid", "reopen", "direct", "valid")]
    for name, target_kind, alias_kind, status in run_cases:
        directory = destination / ("run-" + name)
        directory.mkdir()
        store = directory / "store"
        shutil.copytree(seed_store, store)
        before_state = (store / "state.json").read_bytes()
        old = json.loads(before_state)
        old_artifacts = store / old["artifact_directory"]
        before_artifacts = inventory(old_artifacts)
        source = directory / ("A.ok" if status == "valid" else invalid["file"])
        shutil.copyfile(sources / source.name, source)
        before_source = source.read_bytes()
        reopen = directory / "input-scene.blend" if target_kind == "reopen" else None
        if reopen:
            shutil.copyfile(seed / "scene.blend", reopen)
        targets = {"state": store / "state.json", "artifact": old_artifacts / "final.glb", "source": source,
                   "external": directory / "outside-result.json", "late-state": directory / "late-result.json",
                   "reopen": reopen}
        target = targets[target_kind]
        result_path = target if target_kind in ("external", "late-state") else alias(directory / "result-alias.json", target, alias_kind)
        allowed_hardlink = alias_kind == "hardlink" and target_kind in ("state", "artifact")
        expected_commit = status == "valid" and (target_kind in ("external", "late-state") or allowed_hardlink)
        expected_code = None if expected_commit else invalid["expected_code"] if status == "invalid" else "C191_E_PUBLICATION"
        events = {}
        stderr = io.StringIO()

        def worker_command(argv, stage):
            events["worker_started"] = True
            return [sys.executable, "-B", str(CHECKER / "lifecycle_worker.py"), "copy", str(stage), "--seed", str(seed)]

        hooks = {"worker_command": worker_command}
        if target_kind == "late-state":
            def replace_state(temporary, state_path):
                os.replace(temporary, state_path)
                result_path.symlink_to(state_path)
                events["late_alias_created_after_state_replace"] = True
            hooks["replace_state"] = replace_state
        row = {"id": "run-" + name, "expected_commit": expected_commit, "expected_code": expected_code, "pass": False}
        try:
            with contextlib.redirect_stderr(stderr):
                result = adapter_run(source, store=store, blender=blender,
                    host_max_operations=1000000, host_max_elapsed_ms=80000,
                    expected_revision=old["accepted_revision"], result_path=result_path, reopen=reopen, hooks=hooks)
            save(directory / "returned-result.json", result)
            assert not list(Draft202012Validator(schema).iter_errors(result)), "Output schema violation"
            assert source.read_bytes() == before_source, "Input source was overwritten"
            assert inventory(old_artifacts) == before_artifacts, "Previous accepted artifact bytes changed"
            if reopen:
                assert digest(reopen) == digest(seed / "scene.blend"), "Reopen input was overwritten"
            assert result["successful"] == result["committed"] == expected_commit, "Wrong transaction outcome"
            assert not result["levels"]["destination_validated"]
            state_after = (store / "state.json").read_bytes()
            if expected_commit:
                accepted = json.loads(state_after)
                assert state_after != before_state and accepted["schema"] == "ontokin.c191.store/0.1"
                assert accepted["accepted_revision"] == digest(source)
                assert Path(result["artifact_directory"]) == store / accepted["artifact_directory"]
                assert result["diagnostics"] == [] and events.get("worker_started")
                if target_kind == "late-state":
                    assert events.get("late_alias_created_after_state_replace") and stderr.getvalue()
                else:
                    assert json.loads(result_path.read_text()) == result, "Legal external receipt differs from returned result"
            else:
                assert state_after == before_state, "Rejected transaction changed accepted pointer bytes"
                assert not events.get("worker_started"), "Protected preexisting alias reached native worker"
                diagnostic, = result["diagnostics"]
                rule = rules[expected_code]
                assert diagnostic["code"] == expected_code and diagnostic["phase"] == rule["phase"]
                assert diagnostic["blocked_levels"] == rule["blocked_levels"]
                expected_span = invalid["expected_span"] if status == "invalid" else source_span(source, "output")
                assert diagnostic["span"] == expected_span, "Original source or publication span changed"
                assert all(not result["levels"][level] for level in rule["blocked_levels"])
                assert stderr.getvalue(), "Unsafe optional receipt suppression was not reported"
            row.update(pass_=True, prior_artifact_bytes_unchanged=True, input_source_unchanged=True)
            row["pass"] = row.pop("pass_")
        except Exception as error:
            row["failure"] = type(error).__name__ + ": " + str(error)
            (directory / "exception.txt").write_text(traceback.format_exc())
        row["events"] = events
        row["stderr"] = stderr.getvalue()
        save(directory / "review.json", row)
        records.append(row)
        print(json.dumps({"id": row["id"], "pass": row["pass"], "failure": row.get("failure")}), flush=True)

    validate_cases = [(output + "-source-" + kind, output, kind)
                      for output in ("canonical", "result") for kind in ("direct", "symlink", "hardlink")]
    validate_cases += [("canonical-result-same-path", "same-path", "direct"), ("separate-external-outputs", "external", "direct")]
    for name, output_kind, alias_kind in validate_cases:
        directory = destination / ("validate-" + name)
        directory.mkdir()
        source = directory / "A.ok"
        shutil.copyfile(sources / "A.ok", source)
        before_source = source.read_bytes()
        options = {}
        sentinel = None
        if output_kind in ("canonical", "result"):
            target = alias(directory / "output-alias.json", source, alias_kind)
            options["canonical_out" if output_kind == "canonical" else "result_path"] = target
        elif output_kind == "same-path":
            sentinel = directory / "canonical-and-result.json"
            sentinel.write_bytes(b"Earlier unrelated output bytes\n")
            options.update(canonical_out=sentinel, result_path=sentinel)
        else:
            options.update(canonical_out=directory / "canonical.json", result_path=directory / "result.json")
        stderr = io.StringIO()
        row = {"id": "validate-" + name, "expected_success": output_kind == "external", "pass": False}
        try:
            with contextlib.redirect_stderr(stderr):
                result = validate_source(source, host_max_operations=1000000, host_max_elapsed_ms=80000, **options)
            save(directory / "returned-result.json", result)
            assert not list(Draft202012Validator(schema).iter_errors(result)), "Output schema violation"
            assert source.read_bytes() == before_source, "Read-only validation overwrote its source"
            assert not result["committed"] and result["successful"] == row["expected_success"]
            if row["expected_success"]:
                assert result["diagnostics"] == []
                assert (directory / "canonical.json").read_bytes() == (sources / "A-canonical.json").read_bytes()
                assert json.loads((directory / "result.json").read_text()) == result
            else:
                diagnostic, = result["diagnostics"]
                assert diagnostic["code"] == "C191_E_IO" and diagnostic["phase"] == rules["C191_E_IO"]["phase"]
                assert diagnostic["span"] == source_span(source, "header")
                assert diagnostic["blocked_levels"] == rules["C191_E_IO"]["blocked_levels"]
                assert all(not result["levels"][level] for level in diagnostic["blocked_levels"])
                if sentinel:
                    assert sentinel.read_bytes() == b"Earlier unrelated output bytes\n", "Colliding output path was overwritten"
            row["pass"] = True
        except Exception as error:
            row["failure"] = type(error).__name__ + ": " + str(error)
            (directory / "exception.txt").write_text(traceback.format_exc())
        row["stderr"] = stderr.getvalue()
        save(directory / "review.json", row)
        records.append(row)
        print(json.dumps({"id": row["id"], "pass": row["pass"], "failure": row.get("failure")}), flush=True)
    unchanged = (inventory(repo / "prototypes/guided_contact_v01") == lock["prototype_files"] and
                 inventory(contract) == lock["contract_files"])
    return {"version": "C191-R2-independent-output-aliases-1", "implementation_revision": revision,
            "input_lock_sha256": digest(destination / "INPUT-LOCK.json"), "snapshot_inputs_unchanged": unchanged,
            "written_after_candidate_source_inspection": True, "new_native_solve_claimed": False,
            "cases": records, "passed": sum(row["pass"] for row in records), "total": len(records),
            "pass": unchanged and all(row["pass"] for row in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--seed-store", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    result = run(args.repo.resolve(), args.seed_store.resolve(), args.blender.resolve(), args.out.resolve(), args.revision)
    save(args.out / "summary.json", result)
    print(json.dumps({"pass": result["pass"], "passed": result["passed"], "total": result["total"]}, indent=2))
    raise SystemExit(0 if result["pass"] else 1)
