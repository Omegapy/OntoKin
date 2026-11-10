#!/usr/bin/env python3
"""Exercise frozen C191 failures through the real API, supervisor and commit point.

The accepted baseline is a byte-preserving copy of a qualified formal A store.
Controlled copying workers feed its exact native capture into the actual result,
mapping and publication paths. They are explicitly not new native qualification.
Cancellation/deadline workers create a descendant in the actual supervised group.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import struct
import sys
import threading
import time
import traceback

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "source-fixtures"
FROZEN = HERE.parent / "frozen/lifecycle-fixtures.json"


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def inventory(root):
    return {str(path.relative_to(root)): {"sha256": digest(path), "bytes": path.stat().st_size}
        for path in sorted(root.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def source_span(source, anchor):
    data = source.read_bytes()
    if anchor in ("backend", "output"):
        match = re.search(rb"^" + anchor.encode() + rb"\s+(\"[^\"]+\")", data, re.M)
        start, end = match.span(1)
    elif anchor == "header":
        match = re.search(rb"^ontokin\b[^;]*;", data)
        start, end = match.span()
    else:
        match = re.search(rb"\bexecution\s*\{[^}]*\}", data)
        start, end = match.span()
    def point(position):
        before = data[:position].decode("utf8")
        return before.count("\n") + 1, len(before.rsplit("\n", 1)[-1]) + 1
    line, column = point(start)
    end_line, end_column = point(end)
    return {"path": source.name, "source_sha256": digest(source), "start_byte": start, "end_byte": end,
        "start_line": line, "start_column": column, "end_line": end_line, "end_column": end_column}


def mutate_float(path, *, axis=0, time_value=False, increment=.001):
    data = bytearray(path.read_bytes())
    length, kind = struct.unpack_from("<II", data, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(data[20:20 + length])
    bin_length, bin_kind = struct.unpack_from("<II", data, 20 + length)
    assert bin_kind == 0x004E4942 and bin_length > 0
    animation = doc["animations"][0]
    channel = next(row for row in animation["channels"]
        if row["target"]["path"] == "translation" and doc["nodes"][row["target"]["node"]]["name"] == "left_carriage")
    sampler = animation["samplers"][channel["sampler"]]
    accessor = doc["accessors"][sampler["input" if time_value else "output"]]
    view = doc["bufferViews"][accessor["bufferView"]]
    assert accessor["componentType"] == 5126 and accessor["count"] == 481
    width = 1 if time_value else 3
    offset = 28 + length + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    offset += 100 * view.get("byteStride", width * 4) + axis * 4
    before = struct.unpack_from("<f", data, offset)[0]
    struct.pack_into("<f", data, offset, before + increment)
    path.write_bytes(data)
    return {"file": path.name, "frame": 100, "axis": axis, "time": time_value,
        "before": before, "after": struct.unpack_from("<f", data, offset)[0], "byte_offset": offset}


def mutate_native(stage, mutation):
    path = stage / "native-result.json"
    raw = path.read_bytes()
    obj = json.loads(raw)
    objects = obj["configuration"]["objects"]
    if mutation == "duplicate-key":
        path.write_bytes(b'{"source_sha256":' + json.dumps(obj["source_sha256"]).encode() + b"," + raw[1:])
        return
    if mutation == "unknown":
        obj["undeclared_result_field"] = True
    elif mutation in ("nan", "infinity"):
        obj["samples"][100]["matrices_blender_m"]["left_carriage"][0][3] = math.nan if mutation == "nan" else math.inf
    elif mutation == "missing-sample":
        obj["samples"].pop(100)
    elif mutation == "duplicate-frame":
        obj["samples"][100]["frame"] = 99
    elif mutation == "wrong-time":
        obj["samples"][100]["time_s"] += .0001
    elif mutation == "body-tag":
        objects["left_shoe"]["properties"]["body_id"] = "body.right"
    elif mutation == "collider-tag":
        objects["left_shoe"]["properties"]["collider_id"] = "contact.right_shoe"
    elif mutation == "parent":
        objects["left_shoe"]["parent"] = "right_carriage"
    elif mutation == "shape":
        objects["left_shoe"]["rigid_body"]["collision_shape"] = "SPHERE"
    elif mutation == "guide":
        objects["_left_generic"]["constraint"]["use_limit_lin_x"] = True
    elif mutation == "motor":
        objects["_left_motor"]["constraint"]["motor_lin_target_velocity"] = -.15
    elif mutation == "substeps":
        obj["configuration"]["world"]["substeps_per_frame"] = 11
    elif mutation == "object-count":
        objects["undeclared_object"] = objects["left_shoe"]
    elif mutation == "native-steps":
        obj["nominal_scheduled_substeps"] = 4801
    elif mutation == "nonaffine":
        obj["samples"][100]["matrices_blender_m"]["left_carriage"][3] = [0, 0, 1, 1]
    elif mutation == "attachment":
        record = obj["samples"][100]
        record["matrices_blender_m"]["left_shoe"][0][3] += .00015
        for bound in record["bounds_gltf_mm"]["left_shoe"]:
            bound[0] += .15
    else:
        raise ValueError(mutation)
    path.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=True) + "\n")


def process_group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def run(repo, destination, revision, blender, formal):
    destination.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.api import run as adapter_run
    source_manifest = json.loads((FIXTURES / "manifest.json").read_text())
    sources = {row["id"]: row for row in source_manifest["fixtures"]}
    frozen = json.loads(FROZEN.read_text())
    tests = {row["id"][:3]: row for row in frozen["failure_tests"]}
    contract = repo / "docs/language-design/guided-contact-v0.1"
    schema = json.loads((contract / "output.schema.json").read_text())
    diagnostics = {row["code"]: row for row in json.loads((contract / "diagnostics.json").read_text())["codes"]}
    formal_summary = json.loads((formal / "summary.json").read_text())
    assert formal_summary["pass"] and formal_summary["implementation_revision"] == revision
    a = next(row for row in formal_summary["builds"] if row["case"] == "A" and row["repeat"] == 1)
    seed = Path(a["artifact_directory"])
    original_store = seed.parents[1]
    accepted_store = destination / "accepted-store"
    shutil.copytree(original_store, accepted_store)
    old_state = (accepted_store / "state.json").read_bytes()
    accepted = json.loads(old_state)
    accepted_dir = accepted_store / accepted["artifact_directory"]
    accepted_inventory = inventory(accepted_dir)
    assert accepted_inventory == inventory(seed)
    short_source = destination / "running-deadline-2s.ok"
    original = (FIXTURES / "A.ok").read_bytes()
    assert original.count(b"max_elapsed = 80[s]") == 1
    short_source.write_bytes(original.replace(b"max_elapsed = 80[s]", b"max_elapsed = 2[s]"))
    lock = {"version": "C191-independent-lifecycle-lock-1", "implementation_revision": revision,
        "prototype_files": inventory(repo / "prototypes/guided_contact_v01"), "contract_files": inventory(contract),
        "checker_files": {name: {"sha256": digest(HERE / name), "bytes": (HERE / name).stat().st_size}
            for name in ("run_lifecycle.py", "lifecycle_worker.py")},
        "frozen_lifecycle_sha256": digest(FROZEN), "source_manifest_sha256": digest(FIXTURES / "manifest.json"),
        "formal_summary_sha256": digest(formal / "summary.json"), "formal_input_lock_sha256": digest(formal / "INPUT-LOCK.json"),
        "blender_sha256": digest(blender), "seed_native_sha256": digest(seed / "native-result.json"),
        "accepted_state_sha256": hashlib.sha256(old_state).hexdigest(), "accepted_artifacts": accepted_inventory,
        "running_deadline_source_sha256": digest(short_source),
        "fault_worker_role": "Controlled test workers exercise actual supervision/validation/commit paths; these are not fresh native-solve proofs."}
    save(destination / "INPUT-LOCK.json", lock)
    specifications = [
        ("T01-invalid-edit-rollback", "T01", "N10-initial-overlap", None),
        ("T02-cancel-after-start", "T02", "A", "cancel"),
        ("T03-deadline-running-worker", "T03", "deadline", "block"),
        ("T04-operation-exhaustion", "T04", "N15-operation-exhaustion", None),
        ("T05-source-deadline", "T05", "N16-deadline-exhaustion", None),
        ("T06-unknown-native-field", "T06", "A", "unknown"),
        ("T07-duplicate-native-key", "T07", "A", "duplicate-key"),
        ("T08-nonfinite-NaN", "T08", "A", "nan"),
        ("T08-nonfinite-Infinity", "T08", "A", "infinity"),
        ("T09-missing-sample", "T09", "A", "missing-sample"),
        ("T09-duplicate-frame", "T09", "A", "duplicate-frame"),
        ("T09-wrong-time", "T09", "A", "wrong-time"),
        *[("T10-" + mutation, "T10", "A", mutation) for mutation in
            ("body-tag", "collider-tag", "parent", "shape", "guide", "motor", "substeps", "object-count", "native-steps")],
        ("T11-nonaffine-native", "T11", "A", "nonaffine"),
        ("T12-native-byte-cap", "T12", "A", "native-size"),
        ("T13-log-byte-cap", "T13", "A", "log"),
        ("T14-output-byte-cap", "T14", "A", "output-size"),
        ("T15-atomic-publication-failure", "T15", "A", "publication"),
        ("T16-stale-revision", "T16", "A", "stale"),
        ("T17-disallowed-X-map", "T17", "A", "map-x"),
        ("T18-disallowed-time-map", "T18", "A", "map-time"),
        ("T19-mapping-bound", "T19", "A", "map-bound"),
        ("S01-native-attachment-0p15mm", "T10", "A", "attachment"),
        *[(name, None, name, None) for name in ("N12-missing-backend", "N20-host-ceiling", "N36-mismatched-backend")],
    ]
    save(destination / "TEST-PLAN.json", [{"id": name, "frozen_test": test, "source": source, "mutation": mutation}
        for name, test, source, mutation in specifications])
    records = []
    for name, test_id, source_id, mutation in specifications:
        directory = destination / name
        directory.mkdir()
        source = short_source if source_id == "deadline" else FIXTURES / sources[source_id]["file"]
        fixture = sources.get(source_id)
        specification = tests[test_id] if test_id else fixture
        expected_code = specification["expected_code"]
        phase = specification.get("phase", specification.get("expected_phase"))
        blocked = specification.get("blocked_levels", specification.get("expected_blocked_levels"))
        anchor = ("backend" if expected_code in ("C191_E_NATIVE_RESULT", "C191_E_BACKEND_MISSING", "C191_E_BACKEND_MISMATCH")
            else "output" if expected_code in ("C191_E_MAPPING", "C191_E_PUBLICATION")
            else "header" if expected_code == "C191_E_STALE_REVISION" else "execution")
        expected_span = fixture["expected_span"] if fixture and "expected_span" in fixture else source_span(source, anchor)
        record = {"id": name, "frozen_test": test_id, "source_sha256": digest(source), "expected_code": expected_code,
            "expected_phase": phase, "expected_span": expected_span, "mutation": mutation, "pass": False}
        hooks = {}
        events = {}
        cancel_token = directory / "cancel.request"
        threads = []
        worker_mode = "block" if mutation in ("cancel", "block") else "log" if mutation == "log" else "copy"
        if mutation not in (None, "stale"):
            def worker_command(argv, stage):
                events["stage"] = str(stage)
                return [sys.executable, "-B", str(HERE / "lifecycle_worker.py"), worker_mode, str(stage), "--seed", str(seed)]
            hooks["worker_command"] = worker_command
            def worker_started(process, stage):
                events["worker_pid"] = process.pid
                events["worker_started_monotonic"] = time.monotonic()
                if mutation == "cancel":
                    def request_cancel():
                        end = time.monotonic() + 1.0
                        while not (stage / "worker-pids.json").exists() and time.monotonic() < end:
                            time.sleep(.01)
                        time.sleep(.05)
                        events["cancellation_requested_monotonic"] = time.monotonic()
                        cancel_token.write_text("Independent reviewer cancellation request.\n")
                    thread = threading.Thread(target=request_cancel, daemon=True)
                    threads.append(thread)
                    thread.start()
            hooks["worker_started"] = worker_started
        if mutation not in (None, "cancel", "block", "log", "stale", "output-size", "publication", "map-x", "map-time", "map-bound"):
            def before_native(stage):
                if mutation == "native-size":
                    with (stage / "native-result.json").open("r+b") as stream:
                        stream.truncate(16777217)
                else:
                    mutate_native(stage, mutation)
                events["mutated_native_sha256"] = digest(stage / "native-result.json")
            hooks["before_native_validation"] = before_native
        if mutation in ("map-x", "map-time"):
            def before_mapping(stage):
                events["glb_mutation"] = mutate_float(stage / "final.glb", time_value=mutation == "map-time",
                    increment=.0001 if mutation == "map-time" else .001)
            hooks["before_mapping_validation"] = before_mapping
        if mutation == "map-bound":
            def before_projection(stage):
                events["glb_mutation"] = mutate_float(stage / "raw.glb", axis=1, increment=.001)
            hooks["before_projection"] = before_projection
        if mutation == "output-size":
            def before_publication(stage):
                with (stage / "exceeds-staged-byte-cap.bin").open("wb") as stream:
                    stream.truncate(67108865)
            hooks["before_publication_validation"] = before_publication
        if mutation == "publication":
            def replace_state(temporary, state_path):
                events["publication_replacement_reached"] = True
                candidate = json.loads(temporary.read_text())
                events["unaccepted_candidate"] = str(accepted_store / candidate["artifact_directory"])
                assert Path(events["unaccepted_candidate"]).is_dir()
                raise OSError("Independent injected failure at the sole atomic state replacement")
            hooks["replace_state"] = replace_state
        runtime = blender
        if source_id == "N12-missing-backend":
            runtime = directory / "absent-blender"
            assert not runtime.exists()
        elif source_id == "N36-mismatched-backend":
            runtime = Path("/bin/true")
            assert digest(runtime) != lock["blender_sha256"]
        ceiling = fixture.get("host_ceilings", {}) if fixture else {}
        began = time.monotonic()
        try:
            result = adapter_run(source, store=accepted_store, blender=runtime,
                host_max_operations=ceiling.get("operations", 1000000), host_max_elapsed_ms=ceiling.get("elapsed_ms", 80000),
                expected_revision="0" * 64 if mutation == "stale" else accepted["accepted_revision"],
                cancel_file=cancel_token if mutation == "cancel" else None, hooks=hooks)
            events["return_monotonic"] = time.monotonic()
            save(directory / "result.json", result)
            errors = list(Draft202012Validator(schema).iter_errors(result))
            assert not errors, "; ".join(error.message for error in errors)
            assert not result["successful"] and not result["committed"], "Rejected attempt committed"
            assert result["accepted_revision"] == result["previous_revision"] == accepted["accepted_revision"]
            assert result["source_sha256"] == digest(source)
            diagnostic, = result["diagnostics"]
            assert diagnostic["code"] == expected_code, f"Expected {expected_code}, received {diagnostic['code']}: {diagnostic['message']}"
            assert diagnostic["phase"] == phase and diagnostic["blocked_levels"] == blocked
            assert diagnostic["span"] == expected_span, "Wrong exact runtime source span"
            assert all(not result["levels"][level] for level in blocked), "A blocked level remains true"
            assert not result["levels"]["destination_validated"]
            attempt = accepted_store / "attempts" / result["attempt_id"]
            assert (attempt / "result.json").is_file(), "Failed attempt receipt missing"
            record["attempt_directory"] = str(attempt)
            stage = attempt / "failed-stage"
            if "worker_pid" in events:
                command = json.loads((stage / "native-command.json").read_text()) if stage.is_dir() else json.loads((Path(events["unaccepted_candidate"]) / "native-command.json").read_text())
                assert command["pid"] == events["worker_pid"]
                assert not process_group_exists(command["process_group"]), "Native process group remains alive"
                assert not Path(f"/proc/{command['pid']}").exists(), "Native parent remains unreaped"
                assert command["poll_ms"] <= 50 and command["terminate_grace_ms"] <= 500
                record["supervised_process_group"] = command["process_group"]
                if mutation in ("cancel", "block"):
                    pids = json.loads((stage / "worker-pids.json").read_text())
                    assert not Path(f"/proc/{pids['descendant']}").exists(), "Native descendant remains unreaped"
                    assert not (stage / "late-worker-result.txt").exists()
                    record["descendant_reaped"] = True
                if mutation == "cancel":
                    measured = (events["return_monotonic"] - events["cancellation_requested_monotonic"]) * 1000
                    assert measured <= 2000, f"Cancellation completion {measured} ms exceeds frozen 2000 ms"
                    assert 0 <= result["cost"]["cancellation_completion_ms"] <= 2000
                    record["request_to_API_return_ms"] = measured
                    record["reported_cancellation_completion_ms"] = result["cost"]["cancellation_completion_ms"]
                if mutation == "block":
                    # 2 s source deadline plus the frozen complete-stop allowance.
                    assert (events["return_monotonic"] - began) * 1000 <= 4000
                    record["running_worker_deadline_ms"] = 2000
                if mutation == "log":
                    stored = (stage / "native.stdout.txt").stat().st_size + (stage / "native.stderr.txt").stat().st_size
                    assert stored <= 4194304 and result["cost"]["native_log_bytes"] > 4194304
                    record["retained_combined_log_bytes"] = stored
            elif mutation not in (None, "stale"):
                raise AssertionError("Test did not reach the intended supervised worker boundary")
            if mutation == "native-size":
                assert result["cost"]["native_result_bytes"] == 16777217
            if mutation == "output-size":
                assert result["cost"]["staged_output_bytes"] > 67108864
            if mutation == "publication":
                assert events.get("publication_replacement_reached")
                orphan = json.loads((attempt / "unreferenced-candidate.json").read_text())
                assert not orphan["accepted"] and orphan["directory"] == events["unaccepted_candidate"]
                assert Path(orphan["directory"]) != accepted_dir
                record["unaccepted_candidate_directory"] = orphan["directory"]
            if test_id == "T04":
                assert result["cost"]["operations_consumed"] > 1
            assert (accepted_store / "state.json").read_bytes() == old_state, "Accepted pointer bytes changed"
            assert inventory(accepted_dir) == accepted_inventory, "Previously accepted artifact bytes changed"
            record["previous_state_and_artifacts_unchanged"] = True
            record["cost"] = result["cost"]
            record["pass"] = True
        except Exception as error:
            record["failure"] = str(error)
            (directory / "exception.txt").write_text(traceback.format_exc())
        finally:
            for thread in threads:
                thread.join(timeout=2)
            if "worker_pid" in events and process_group_exists(events["worker_pid"]):
                # A failed supervisor must not contaminate later probes.
                os.killpg(events["worker_pid"], signal.SIGKILL)
                record["harness_emergency_kill"] = True
            record["elapsed_ms"] = (time.monotonic() - began) * 1000
            save(directory / "events.json", events)
            save(directory / "review.json", record)
        records.append(record)
        save(destination / "progress.json", {"cases": records, "passed": sum(row["pass"] for row in records)})
        print(json.dumps({"id": name, "pass": record["pass"], "failure": record.get("failure")}), flush=True)
    unchanged = inventory(repo / "prototypes/guided_contact_v01") == lock["prototype_files"] and inventory(contract) == lock["contract_files"]
    covered = {row["frozen_test"] for row in records if row["pass"] and row["frozen_test"]}
    return {"version": "C191-independent-lifecycle-report-1", "implementation_revision": revision,
        "input_lock_sha256": digest(destination / "INPUT-LOCK.json"), "snapshot_inputs_unchanged": unchanged,
        "accepted_baseline_formal_artifacts": str(seed), "accepted_store_copy": str(accepted_store),
        "cases": records, "passed": sum(row["pass"] for row in records), "total": len(records),
        "frozen_failure_methods_covered": sorted(covered), "frozen_failure_method_count": len(covered),
        "all_prior_accepted_bytes_unchanged": (accepted_store / "state.json").read_bytes() == old_state and inventory(accepted_dir) == accepted_inventory,
        "pass": all(row["pass"] for row in records) and covered == set(tests) and unchanged}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--formal", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.repo.resolve(), args.out.resolve(), args.revision, args.blender.resolve(), args.formal.resolve())
    save(args.out / "summary.json", report)
    print(json.dumps({"pass": report["pass"], "passed": report["passed"], "total": report["total"]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)
