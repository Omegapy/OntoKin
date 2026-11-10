#!/usr/bin/env python3
"""Supplemental C191 native-result and saved-scene admission probes.

These probes were written after the recovered implementation was inspected.
They exercise existing obligations and do not replace the frozen C191 corpus.
A supervised copying worker supplies an identified earlier native solve; these
attempts establish transaction behavior, not a new native simulation result.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import sys
import time
import traceback

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
INDEPENDENT = HERE.parents[1]
CHECKER = INDEPENDENT / "checker"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inventory(directory):
    return {str(path.relative_to(directory)): {"sha256": digest(path), "bytes": path.stat().st_size}
            for path in sorted(directory.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def run(repo, seed_store, blender, destination, revision):
    destination.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    sys.path.insert(0, str(CHECKER))
    from prototypes.guided_contact_v01.api import run as adapter_run
    from run_lifecycle import source_span

    contract = repo / "docs/language-design/guided-contact-v0.1"
    schema = json.loads((contract / "output.schema.json").read_text())
    diagnostic_rules = {row["code"]: row for row in json.loads((contract / "diagnostics.json").read_text())["codes"]}
    source = INDEPENDENT / "source-fixtures/A.ok"
    original_state = json.loads((seed_store / "state.json").read_text())
    seed = seed_store / original_state["artifact_directory"]
    assert (seed / "source.ok").read_bytes() == source.read_bytes(), "Seed is not the frozen A source"
    lock = {
        "implementation_revision": revision,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "argv": sys.argv,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "prototype_files": inventory(repo / "prototypes/guided_contact_v01"),
        "contract_files": inventory(contract),
        "checker_sha256": digest(__file__),
        "source_sha256": digest(source),
        "seed_store": str(seed_store),
        "seed_native_result_sha256": digest(seed / "native-result.json"),
        "seed_scene_sha256": digest(seed / "scene.blend"),
        "seed_final_glb_sha256": digest(seed / "final.glb"),
        "blender_sha256": digest(blender),
        "written_after_candidate_source_inspection": True,
        "new_native_solve_claimed": False,
    }
    (destination / "executed-checker.py").write_bytes(Path(__file__).read_bytes())
    save(destination / "INPUT-LOCK.json", lock)
    cases = [
        ("R2-valid-copy-control", None, None),
        ("R2-mesh-reported-empty", "mesh-type", "C191_E_NATIVE_RESULT"),
        ("R2-constraint-reported-mesh", "constraint-type", "C191_E_NATIVE_RESULT"),
        ("R2-missing-saved-scene", "missing-scene", "C191_E_NATIVE_FAILURE"),
        ("R2-empty-saved-scene", "empty-scene", "C191_E_NATIVE_RESULT"),
        ("R2-non-blender-saved-scene", "bad-scene-header", "C191_E_NATIVE_RESULT"),
        ("R2-scene-header-only", "header-only", "C191_E_NATIVE_RESULT"),
        ("R2-scene-header-and-one-byte", "header-and-byte", "C191_E_NATIVE_RESULT"),
        ("R2-scene-partial-block-header", "partial-block-header", "C191_E_NATIVE_RESULT"),
        ("R2-scene-partial-block-payload", "partial-block-payload", "C191_E_NATIVE_RESULT"),
        ("R2-scene-missing-end-block", "missing-end-block", "C191_E_NATIVE_RESULT"),
        ("R2-scene-truncated-end-block", "truncated-end-block", "C191_E_NATIVE_RESULT"),
        ("R2-scene-trailing-data", "trailing-data", "C191_E_NATIVE_RESULT"),
    ]
    save(destination / "TEST-PLAN.json", [
        {"id": name, "mutation": mutation, "expected_code": code,
         "expected_commit": code is None, "prior_artifact_preservation_required": True}
        for name, mutation, code in cases])
    records = []
    for name, mutation, code in cases:
        directory = destination / name
        directory.mkdir()
        store = directory / "store"
        shutil.copytree(seed_store, store)
        before_state = (store / "state.json").read_bytes()
        accepted = json.loads(before_state)
        old_artifacts = store / accepted["artifact_directory"]
        before_inventory = inventory(old_artifacts)
        events = {}

        def worker_command(argv, stage):
            events["stage"] = str(stage)
            return [sys.executable, "-B", str(CHECKER / "lifecycle_worker.py"),
                    "copy", str(stage), "--seed", str(seed)]

        def before_native(stage):
            events["mutation_boundary_reached"] = True
            if mutation in ("mesh-type", "constraint-type"):
                native_path = stage / "native-result.json"
                value = json.loads(native_path.read_text())
                name = "left_carriage" if mutation == "mesh-type" else "_left_generic"
                value["configuration"]["objects"][name]["type"] = "EMPTY" if mutation == "mesh-type" else "MESH"
                save(native_path, value)
                events["native_result_sha256_after_mutation"] = digest(native_path)
            elif mutation == "missing-scene":
                (stage / "scene.blend").unlink()
            elif mutation == "empty-scene":
                (stage / "scene.blend").write_bytes(b"")
            elif mutation == "bad-scene-header":
                (stage / "scene.blend").write_bytes(b"Not a saved Blender scene.\n")
            elif mutation in ("header-only", "header-and-byte", "partial-block-header",
                              "partial-block-payload", "missing-end-block", "truncated-end-block", "trailing-data"):
                scene = stage / "scene.blend"
                data = scene.read_bytes()
                # Mutate actual native bytes. The pinned file uses the 64-bit
                # little-endian, uncompressed 12-byte header and 24-byte BHead.
                assert data[:12] == b"BLENDER-v405" and data[-24:-20] == b"ENDB"
                first_payload_bytes, = struct.unpack_from("<i", data, 16)
                assert first_payload_bytes > 1
                if mutation == "header-only":
                    data = data[:12]
                elif mutation == "header-and-byte":
                    data = data[:13]
                elif mutation == "partial-block-header":
                    data = data[:12 + 10]
                elif mutation == "partial-block-payload":
                    data = data[:12 + 24 + first_payload_bytes // 2]
                elif mutation == "missing-end-block":
                    data = data[:-24]
                elif mutation == "truncated-end-block":
                    data = data[:-1]
                else:
                    data += b"unexpected trailing data"
                scene.write_bytes(data)
                events["mutated_scene_bytes"] = len(data)
                events["mutated_scene_sha256"] = digest(scene)

        hooks = {"worker_command": worker_command}
        if mutation is not None:
            hooks["before_native_validation"] = before_native
        row = {"id": name, "expected_code": code, "mutation": mutation, "pass": False}
        started = time.monotonic()
        try:
            result = adapter_run(source, store=store, blender=blender,
                host_max_operations=1000000, host_max_elapsed_ms=80000,
                expected_revision=accepted["accepted_revision"], hooks=hooks)
            save(directory / "returned-result.json", result)
            errors = list(Draft202012Validator(schema).iter_errors(result))
            assert not errors, "; ".join(error.message for error in errors)
            assert result["source_sha256"] == digest(source)
            assert not result["levels"]["destination_validated"]
            assert inventory(old_artifacts) == before_inventory, "Previous accepted artifact bytes changed"
            row["prior_artifacts_unchanged"] = True
            changed = (store / "state.json").read_bytes() != before_state
            row["pointer_changed"] = changed
            if code is None:
                assert result["successful"] and result["committed"] and changed
                assert result["diagnostics"] == [] and result["levels"]["exported"]
                candidate = Path(result["artifact_directory"])
                assert (candidate / "scene.blend").read_bytes() == (seed / "scene.blend").read_bytes()
                assert digest(candidate / "final.glb") == digest(seed / "final.glb")
                command_path = candidate / "native-command.json"
            else:
                assert events.get("mutation_boundary_reached"), "Probe did not reach its intended boundary"
                assert not result["successful"] and not result["committed"], "Malformed candidate committed"
                assert not changed, "Rejected candidate changed the state pointer"
                assert result["accepted_revision"] == accepted["accepted_revision"]
                diagnostic, = result["diagnostics"]
                rule = diagnostic_rules[code]
                assert diagnostic["code"] == code, "Wrong rejection code: " + diagnostic["code"]
                assert diagnostic["phase"] == rule["phase"]
                assert diagnostic["blocked_levels"] == rule["blocked_levels"]
                assert diagnostic["span"] == source_span(source, "backend"), "Wrong exact backend source span"
                assert all(not result["levels"][level] for level in rule["blocked_levels"])
                attempt = store / "attempts" / result["attempt_id"]
                assert (attempt / "result.json").is_file(), "Rejected attempt receipt missing"
                command_path = attempt / "failed-stage/native-command.json"
                row["diagnostic"] = diagnostic
            command = json.loads(command_path.read_text())
            assert command["returncode"] == 0, "Copy worker did not succeed before admission check"
            assert not group_exists(command["process_group"])
            assert not Path(f"/proc/{command['pid']}").exists()
            row["copy_worker_reaped"] = True
            row["pass"] = True
        except Exception as error:
            row["failure"] = type(error).__name__ + ": " + str(error)
            (directory / "exception.txt").write_text(traceback.format_exc())
        row["elapsed_ms"] = (time.monotonic() - started) * 1000
        save(directory / "events.json", events)
        save(directory / "review.json", row)
        records.append(row)
        print(json.dumps({"id": name, "pass": row["pass"], "failure": row.get("failure")}), flush=True)
    unchanged = (inventory(repo / "prototypes/guided_contact_v01") == lock["prototype_files"]
                 and inventory(contract) == lock["contract_files"])
    return {"version": "C191-R2-independent-native-artifact-edges-1", "implementation_revision": revision,
            "input_lock_sha256": digest(destination / "INPUT-LOCK.json"),
            "written_after_candidate_source_inspection": True, "new_native_solve_claimed": False,
            "snapshot_inputs_unchanged": unchanged, "cases": records,
            "passed": sum(row["pass"] for row in records), "total": len(records),
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
