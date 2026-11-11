"""The finite two-stage static-tray transaction and reserved native ledger.

No native retry exists. A single monotonic clock starts before input verification.
An accepted pointer is changed only after independent construction/receiving
checks and verified process cleanup, under an expected-predecessor comparison.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import time

from .canonical import ROOT, json_bytes, strict_json
from .errors import PROFILE, TrayError
from .lock import independent_modules, read_json, verify_lock
from .receive_check import compare
from .sources import _bounded_source_file, lower_source
from .store import append_event, promote, read_state, revision, seal_candidate, verify_candidate
from .supervisor import Clock, LIMITS, Stop, inventory, run_process, sha256_file

TERMINAL = {"ACCEPTED", "REJECTED", "TIMEOUT", "CANCELLED", "UNKNOWN"}


def write_new(path, value, *, binary=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if binary else json_bytes(value)
    if len(data) > LIMITS["result_bytes"] and not binary:
        raise Stop("OTRAY-E-RESOURCE", "Structured result exceeds the frozen allowance")
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def read_ledger(root):
    path = Path(root) / "attempts.jsonl"
    if not path.exists():
        return []
    if path.is_symlink() or path.stat().st_size > LIMITS["result_bytes"]:
        raise Stop("OTRAY-E-BINDING", "Unsafe or oversized attempt ledger")
    rows = [strict_json(line) for line in path.read_bytes().splitlines() if line.strip()]
    if any(not isinstance(row, dict) or "slot" not in row or "state" not in row for row in rows):
        raise Stop("OTRAY-E-BINDING", "Malformed attempt record")
    return rows


def check_order(lock, row, lock_hash=None):
    schedule = Path(lock["schedule_root"])
    if (schedule / "finalization-stop.json").exists():
        raise Stop("OTRAY-E-BINDING", "A finalization failure requires explicit read-only reconciliation")
    records = read_ledger(lock["schedule_root"])
    states = {}
    for event in records:
        if event["slot"] not in {s["slot"] for s in lock["slots"]} or event["state"] not in TERMINAL | {"RESERVED", "STARTED", "BUILT_PENDING_RECEIVING", "RECEIVING"}:
            raise Stop("OTRAY-E-BINDING", "Attempt ledger contains an unassigned slot or state")
        states[event["slot"]] = event["state"]
    ordinal = [x["slot"] for x in lock["slots"]].index(row["slot"])
    earlier = {x["slot"] for x in lock["slots"][:ordinal]}
    if set(states) != earlier or any(states[x] != "ACCEPTED" for x in earlier):
        raise Stop("OTRAY-E-RESOURCE", "Assigned order is not ready, already attempted, or stopped after a failure")
    latest_stores = {}
    for previous in lock["slots"][:ordinal]:
        if (schedule / (previous["slot"] + ".finalization-pending.json")).exists():
            raise Stop("OTRAY-E-BINDING", "A prior result/terminal finalization remains pending")
        prior, candidate, _ = _prior_result(lock, previous["slot"])
        terminal = next(event for event in reversed(records) if event["slot"] == previous["slot"])
        if (prior.get("schema") != "ontokin.static-tray.transaction/0.1.0"
                or prior.get("input_lock_sha256") != lock_hash
                or prior.get("implementation") != lock["implementation"]
                or any(prior.get(key) != previous[key] for key in ("route","case","candidate_revision","source_identity"))
                or candidate != Path(previous["store"]) / "objects" / previous["slot"]
                or terminal.get("input_lock_sha256") != lock_hash
                or terminal.get("result_sha256") != sha256_file(previous["result"])):
            raise Stop("OTRAY-E-BINDING", "Prior durable result differs from its locked slot or terminal receipt")
        receiving = Path(previous["store"]) / "objects" / (previous["slot"] + "-receiving")
        if prior.get("receiving_candidate") != str(receiving):
            raise Stop("OTRAY-E-BINDING", "Prior receiving closure path differs")
        verify_candidate(receiving)
        if sha256_file(receiving / "closure.json") != prior.get("receiving_closure_sha256"):
            raise Stop("OTRAY-E-BINDING", "Prior receiving closure identity changed")
        expected = {"revision":previous["candidate_revision"], "candidate":"objects/"+previous["slot"],
                    "closure_sha256":prior["closure_sha256"],
                    "receiving_candidate":"objects/"+previous["slot"]+"-receiving",
                    "receiving_closure_sha256":prior["receiving_closure_sha256"],
                    "input_lock_sha256":lock_hash,"source_identity":previous["source_identity"],
                    "canonical_sha256":previous["canonical_sha256"]}
        if prior.get("promotion") != {"promoted":True,"state":expected}:
            raise Stop("OTRAY-E-BINDING", "Prior promotion result is incomplete or uncertain")
        latest_stores[previous["store"]] = expected
    for store, expected in latest_stores.items():
        if read_state(store) != expected:
            raise Stop("OTRAY-E-BINDING", "Latest prior accepted pointer requires reconciliation")
    from .qualification import verify_delivered_predecessors
    verify_delivered_predecessors(lock, row["slot"], lock_hash)


@contextmanager
def alarm_until(clock, end):
    """Interrupt in-process compiler/reader work as well as polling children."""
    old_handler = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    if old_timer[0] > 0:
        raise Stop("OTRAY-E-BINDING", "An ambient alarm conflicts with the single transaction deadline")
    def expired(signum, frame):
        raise Stop("OTRAY-E-RESOURCE", "In-process stage deadline elapsed", "TIMEOUT")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.000001, min(end, clock.end) - time.monotonic()))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


@contextmanager
def supervised_process_clock():
    """Leave child polling and mandatory cleanup to the qualified supervisor.

    Restore only the unspent part of the same absolute host alarm. An expired
    alarm stays off while the supervisor returns its process/cleanup receipt;
    the immediately following explicit clock check rejects that result.
    """
    remaining, interval = signal.setitimer(signal.ITIMER_REAL, 0)
    started = time.monotonic()
    try:
        yield
    finally:
        unspent = remaining - (time.monotonic() - started)
        if remaining > 0 and unspent > 0:
            signal.setitimer(signal.ITIMER_REAL, unspent, interval)


def _prior_result(lock, slot):
    row = next(r for r in lock["slots"] if r["slot"] == slot)
    try:
        result = read_json(row["result"])
    except (Stop, OSError, ValueError) as exc:
        raise Stop("OTRAY-E-BINDING", "A required durable prior result is unavailable") from exc
    if result.get("state") != "ACCEPTED" or result.get("slot") != slot:
        raise Stop("OTRAY-E-BINDING", "A required prior accepted result is unavailable")
    candidate = Path(result["candidate"])
    manifest = verify_candidate(candidate)
    if sha256_file(candidate / "closure.json") != result["closure_sha256"]:
        raise Stop("OTRAY-E-BINDING", "Prior candidate closure identity changed")
    return result, candidate, manifest


def source_preservation(lock, row, lowered):
    if row["case"] not in {"Q04", "Q05"}:
        return None
    baseline_slot = "N01" if row["route"] == "ontokin" else "N02"
    _, old, _ = _prior_result(lock, baseline_slot)
    prior = read_json(old / "canonical-input.json")
    if prior["trays"][1] != lowered.record["trays"][1]:
        raise Stop("OTRAY-E-BINDING", "Unrelated right canonical source changed")
    helper, entry = ("tray.ok", "main.ok") if row["route"] == "ontokin" else ("tray.py", "main.py")
    if (old / "source" / helper).read_bytes() != lowered.files[helper]:
        raise Stop("OTRAY-E-BINDING", "Shared reusable definition changed in a scoped edit")
    marker = b" object right" if row["route"] == "ontokin" else b"right = "
    before, after = (old / "source" / entry).read_bytes(), lowered.files[entry]
    if before.count(marker) != 1 or after.count(marker) != 1 or before.split(marker)[1] != after.split(marker)[1]:
        raise Stop("OTRAY-E-BINDING", "Unrelated right source bytes changed")
    return {"baseline_slot": baseline_slot, "right_canonical_equal": True,
            "helper_bytes_equal": True, "right_source_suffix_equal": True}


def equality_checks(lock, row, stage, audit, *, check=lambda: None):
    checks = []
    slot_number = int(row["slot"][1:])
    references = []
    if slot_number % 2 == 0:
        references.append(("paired-route", "N%02d" % (slot_number - 1)))
    if row["purpose"] == "clean-regeneration":
        references.append(("clean-regeneration", "N01" if row["route"] == "ontokin" else "N02"))
    for purpose, target in references:
        check()
        _, prior, _ = _prior_result(lock, target)
        files = {}
        for name in ("canonical-input.json", "raw.glb", "final.glb"):
            current, old = sha256_file(Path(stage) / name), sha256_file(prior / name)
            if current != old or (Path(stage) / name).read_bytes() != (prior / name).read_bytes():
                raise Stop("OTRAY-E-REGENERATION", purpose + " exact bytes differ: " + name)
            files[name] = current
        checks.append({"purpose": purpose, "reference_slot": target, "exact_files": files})
    return checks


def _sealed_reuse(lock, row, check):
    if row["case"] != "Q05":
        return []
    selected = ("N01", "N09") if row["route"] == "ontokin" else ("N02", "N10")
    results = []
    for slot in selected:
        check()
        _, candidate, before = _prior_result(lock, slot)
        lowered = lower_source(row["route"], candidate / "source/source.json", PROFILE, check=check)
        if lowered.canonical_bytes != (candidate / "canonical-input.json").read_bytes():
            raise Stop("OTRAY-E-REGENERATION", "Retained selector no longer compiles to its accepted record")
        if verify_candidate(candidate) != before:
            raise Stop("OTRAY-E-BINDING", "Retained selector closure changed during source-only reuse check")
        results.append({"slot": slot, "canonical_bytes_equal": True, "retained_closure_unchanged": True, "native_starts": 0})
    return results


def _environment(row, schedule):
    environment = row["environment"]
    directory_names = ("HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "TMPDIR", "BLENDER_USER_CONFIG", "BLENDER_USER_SCRIPTS")
    for key in directory_names:
        path = Path(environment[key])
        if not path.resolve().is_relative_to(schedule.resolve()):
            raise Stop("OTRAY-E-BINDING", "Runtime environment path escapes the schedule")
        path.mkdir(parents=True, exist_ok=False)
    return environment


def read_locked_manifest(row):
    data, _ = _bounded_source_file(Path(row["source_manifest"]), 32768, code="RESOURCE")
    if len(data) != row["source_manifest_size_bytes"] or hashlib.sha256(data).hexdigest() != row["source_manifest_sha256"]:
        raise Stop("OTRAY-E-BINDING", "Retained source manifest bytes differ from the locked size/hash")
    return data


def run_transaction(lock_path, slot, *, route=None, source=None, store=None, result_path=None,
                    cancel_file=None):
    clock = Clock(cancel_file=cancel_file)
    construction_end = clock.started + LIMITS["construction_ms"] / 1000
    row, lock, lock_hash, stage = None, None, None, None
    reserved = False
    started_count = 0
    receiver_count = 0
    record = {"schema": "ontokin.static-tray.transaction/0.1.0", "slot": slot,
              "state": "REJECTED", "native_starts": 0, "receiving_starts": 0,
              "requested_limits": dict(LIMITS), "effective_limits": dict(LIMITS),
              "transaction_start_monotonic": clock.started, "attempt_events": [], "processes": []}
    guard = None
    ledger_path = None
    def event(state, **details):
        value = {"slot": slot, "state": state, "route": row["route"], "case": row["case"],
                 "input_lock_sha256": lock_hash, "monotonic": time.monotonic(),
                 "native_starts": started_count, "receiving_starts": receiver_count, **details}
        append_event(ledger_path, value, clock=clock)
        record["attempt_events"].append(value)
    try:
        with alarm_until(clock, construction_end):
            lock, lock_hash = verify_lock(lock_path, check=lambda: clock.check(construction_end), runtime=True)
            matches = [r for r in lock["slots"] if r["slot"] == slot]
            if len(matches) != 1:
                raise Stop("OTRAY-E-RESOURCE", "Unknown assigned native slot")
            row = matches[0]
            for requested, key in ((route, "route"), (source, "source_manifest"), (store, "store"), (result_path, "result")):
                if requested is not None and str(requested) != row[key]:
                    raise Stop("OTRAY-E-BINDING", "Requested command differs from locked " + key)
            record.update(route=row["route"], case=row["case"], purpose=row["purpose"], input_lock_sha256=lock_hash,
                          implementation=lock["implementation"], source_identity=row["source_identity"],
                          expected_predecessor=row["expected_predecessor"], candidate_revision=row["candidate_revision"],
                          command=row["command"], host=lock["host"]["python"], platform=lock["host"]["platform"],
                          reader_files=lock["independent_reader"]["files"])
            schedule = Path(lock["schedule_root"])
            schedule.mkdir(parents=True, exist_ok=True)
            schedule_guard = schedule / ".schedule-guard"
            if schedule_guard.is_symlink():
                raise Stop("OTRAY-E-BINDING", "Schedule guard is a symlink")
            guard = schedule_guard.open("a+b")
            try:
                fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise Stop("OTRAY-E-RESOURCE", "Another qualification transaction holds this schedule") from exc
            check_order(lock, row, lock_hash)
            ledger_path = schedule / "attempts.jsonl"
            event("RESERVED", expected_predecessor=row["expected_predecessor"], requested_limits=dict(LIMITS), effective_limits=dict(LIMITS))
            reserved = True
            store_path = Path(row["store"])
            store_path.mkdir(parents=True, exist_ok=True)
            if revision(read_state(store_path)) != row["expected_predecessor"]:
                raise Stop("OTRAY-E-STALE", "Accepted predecessor differs before native work")
            before_state = read_state(store_path)
            record["previous_state"] = before_state
            manifest_path = Path(row["source_manifest"])
            manifest_bytes = read_locked_manifest(row)
            lowered = lower_source(row["route"], manifest_path, PROFILE, check=lambda: clock.check(construction_end))
            if lowered.provenance["candidate_identity"] != row["source_identity"] or hashlib.sha256(lowered.canonical_bytes).hexdigest() != row["canonical_sha256"]:
                raise Stop("OTRAY-E-BINDING", "Actual source or canonical record differs from frozen input")
            for name, raw in lowered.files.items():
                if {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)} != row["source_files"][name]:
                    raise Stop("OTRAY-E-BINDING", "Actual source bytes differ from lock")
            if set(lowered.files) != set(row["source_files"]):
                raise Stop("OTRAY-E-BINDING", "Actual source inventory differs from lock")
            record["source_preservation"] = source_preservation(lock, row, lowered)
            record["retained_selector_checks"] = _sealed_reuse(lock, row, lambda: clock.check(construction_end))
            stage = Path(row["stage"])
            stage.mkdir(parents=True, exist_ok=False)
            source_dir = stage / "source"
            source_dir.mkdir()
            for name, raw in lowered.files.items(): write_new(source_dir / name, raw, binary=True)
            write_new(source_dir / "source.json", manifest_bytes, binary=True)
            write_new(stage / "canonical-input.json", lowered.canonical_bytes, binary=True)
            write_new(stage / "source-provenance.json", {**lowered.provenance, "implementation": lock["implementation"], "input_lock_sha256": lock_hash})
            settings = ROOT / "prototypes/static_tray_v01/export-settings.json"
            job = {"output_directory": str(stage), "record_path": str(stage / "canonical-input.json"),
                   "record_sha256": row["canonical_sha256"], "settings_path": str(settings), "settings_sha256": sha256_file(settings)}
            write_new(stage / "job.json", job)
            environment = _environment(row, schedule)
            def native_started(process):
                nonlocal started_count
                started_count += 1
                record["native_starts"] = started_count
                event("STARTED", process_group=process["process_group"], start_monotonic=process["start_monotonic"],
                      source_identity=row["source_identity"], canonical_sha256=row["canonical_sha256"])
            with supervised_process_clock():
                process = run_process(row["native_argv"], stage=stage, label="construction", clock=clock,
                                      stage_end=construction_end, env=environment, on_started=native_started)
            record["processes"].append(process)
            clock.check(construction_end)
            inventory(stage, clock=clock, stage_end=construction_end)
            native_result = read_json(stage / "native-result.json")
            if native_result.get("passed") is not True or native_result.get("record_sha256") != row["canonical_sha256"]:
                raise Stop("OTRAY-E-BINDING", "Native result does not bind the actual canonical input")
            for name in ("raw.glb", "final.glb", "scene.blend"):
                binding = native_result["artifacts"][name]
                if sha256_file(stage / name) != binding["sha256"] or (stage / name).stat().st_size != binding["size_bytes"]:
                    raise Stop("OTRAY-E-BINDING", "Actual native artifact differs from its receipt")
            record["artifacts"] = native_result["artifacts"]
            if (stage / "raw.glb").read_bytes() != (stage / "final.glb").read_bytes():
                raise Stop("OTRAY-E-BINDING", "Final GLB must be the unmodified raw GLB bytes")
            modules = independent_modules(lock)
            baseline = None
            if row["case"] in {"Q04", "Q05"}:
                _, prior, _ = _prior_result(lock, "N01" if row["route"] == "ontokin" else "N02")
                baseline = read_json(prior / "independent-audit.json")
            audit = modules["reader"].audit(stage / "final.glb", row["case"], baseline,
                                              lock["independent_reader"]["delivery_rules"])
            clock.check(construction_end)
            write_new(stage / "independent-audit.json", audit)
            if not audit["passed"]:
                raise Stop("OTRAY-E-DELIVERY", "Independent actual-GLB geometry/identity check failed")
            record["equality_checks"] = equality_checks(lock, row, stage, audit, check=lambda: clock.check(construction_end))
            write_new(stage / "equality-checks.json", record["equality_checks"])
            candidate, closure = seal_candidate(stage, store_path, slot)
            record.update(candidate=str(candidate), closure_sha256=closure)
            verify_candidate(candidate)
            clock.check(construction_end)
            if read_state(store_path) != before_state:
                raise Stop("OTRAY-E-STALE", "Accepted pointer changed before receiving")
            event("BUILT_PENDING_RECEIVING", candidate=str(candidate), closure_sha256=closure, accepted_pointer_unchanged=True)
            record["built_pending_receiving_pointer_unchanged"] = True
        receiver_end = clock.stage(LIMITS["receiving_ms"])
        with alarm_until(clock, receiver_end):
            receiving = Path(row["receiver_stage"])
            receiving.mkdir(parents=True, exist_ok=False)
            settings = ROOT / "prototypes/static_tray_v01/import-settings.json"
            inputs = {name: sha256_file(candidate / name) for name in ("scene.blend", "final.glb")}
            job = {"output_directory": str(receiving), "candidate": str(candidate), "input_sha256": inputs,
                   "settings_path": str(settings), "settings_sha256": sha256_file(settings),
                   "expected_world_bounds": modules["expected"].expected_bounds(row["case"])}
            write_new(receiving / "job.json", job)
            def receiver_started(process):
                nonlocal receiver_count
                receiver_count += 1
                record["receiving_starts"] = receiver_count
                event("RECEIVING", process_group=process["process_group"], start_monotonic=process["start_monotonic"])
            with supervised_process_clock():
                process = run_process(row["receiver_argv"], stage=receiving, label="receiving", clock=clock,
                                      stage_end=receiver_end, env=environment, on_started=receiver_started)
            record["processes"].append(process)
            clock.check(receiver_end)
            observations = read_json(receiving / "observations.json")
            if observations.get("input_sha256") != inputs:
                raise Stop("OTRAY-E-BINDING", "Receiver observations do not bind the candidate bytes")
            check = compare(observations, audit)
            write_new(receiving / "receiving-check.json", check)
            if not check["passed"]:
                raise Stop("OTRAY-E-DELIVERY", "Native-scene/GLB receiving measurements differ")
            inventory(receiving, clock=clock, stage_end=receiver_end)
            verify_candidate(candidate)
            # The receiver closure and its hashes are charged to receiving too.
            receiving_closure, receiving_hash = seal_candidate(receiving, store_path, slot + "-receiving")
            verify_candidate(receiving_closure)
            clock.check(receiver_end)
        record.update(receiving_candidate=str(receiving_closure), receiving_closure_sha256=receiving_hash,
                      receiving_check=check, render=str(receiving_closure / "review.png"))
        state = {"revision": row["candidate_revision"], "candidate": "objects/" + slot,
                 "closure_sha256": closure, "receiving_candidate": "objects/" + slot + "-receiving",
                 "receiving_closure_sha256": receiving_hash, "input_lock_sha256": lock_hash,
                 "source_identity": row["source_identity"], "canonical_sha256": row["canonical_sha256"]}
        record["promotion"] = promote(store_path, expected=row["expected_predecessor"], state=state,
                                      clock=clock, cleanup_records=record["processes"])
        record["state"] = "ACCEPTED"
    except BaseException as exc:
        if isinstance(exc, Stop):
            failure = exc
        elif isinstance(exc, TrayError):
            failure = Stop(exc.code, str(exc), "REJECTED")
            record["source_diagnostic"] = exc.to_dict()
        else:
            failure = Stop("OTRAY-E-BACKEND", type(exc).__name__ + ": " + str(exc), "UNKNOWN" if record.get("promotion") else "REJECTED")
        record["state"] = failure.state
        if record.get("promotion", {}).get("promoted"):
            failure = Stop("OTRAY-E-BINDING", "Post-promotion result is uncertain: " + str(exc), "UNKNOWN")
            record["state"] = "UNKNOWN"
        record["error"] = failure.as_dict()
        if hasattr(exc, "intended_state"):
            record["intended_state_after_unknown"] = exc.intended_state
            record["promotion_readback"] = getattr(exc, "observed_state", None)
        if hasattr(exc, "process_record"):
            record["processes"].append(exc.process_record)
        if row is not None:
            try:
                record["observed_state_after_failure"] = read_state(row["store"])
            except BaseException as read_error:
                record["state_readback_error"] = str(read_error)
        if reserved:
            try:
                event(record["state"], error=record["error"], observed_state=record.get("observed_state_after_failure"))
            except BaseException as ledger_error:
                record["terminal_ledger_write_error"] = str(ledger_error)
                record["state"] = "UNKNOWN"
    finally:
        # This immutable result describes the measured work before persistence.
        # The return value separately reports actual time after finalization.
        record["elapsed_before_finalization_ms"] = clock.elapsed_ms()
        record["native_starts"] = started_count
        record["receiving_starts"] = receiver_count
        target = Path(row["result"]) if row is not None else (Path(result_path) if result_path else None)
        pending = Path(lock["schedule_root"]) / (slot + ".finalization-pending.json") if lock else None
        if target is not None:
            try:
                if record["state"] == "ACCEPTED":
                    with alarm_until(clock, clock.end):
                        clock.check()
                        write_new(pending, {"slot":slot,"input_lock_sha256":lock_hash,"reason":"Success finalization not yet complete"})
                        write_new(target, record)
                        clock.check()
                        event("ACCEPTED", candidate=record["candidate"], closure_sha256=record["closure_sha256"],
                              receiving_candidate=record["receiving_candidate"], receiving_closure_sha256=record["receiving_closure_sha256"],
                              accepted_revision=row["candidate_revision"], cleanup_passed=True,
                              result_sha256=sha256_file(target), elapsed_before_terminal_ms=clock.elapsed_ms())
                        clock.check()
                        pending.unlink()
                        directory = os.open(pending.parent, os.O_RDONLY | os.O_DIRECTORY)
                        try:
                            os.fsync(directory)
                        finally:
                            os.close(directory)
                        clock.check()
                else:
                    # Failure retention does not restart a transaction or child.
                    write_new(target, record)
            except BaseException as write_error:
                record["result_write_error"] = str(write_error)
                record["state"] = "UNKNOWN"
                if pending is not None:
                    try:
                        if not pending.exists():
                            write_new(pending, {"slot":slot,"input_lock_sha256":lock_hash,"reason":"Finalization outcome requires explicit reconciliation"})
                        stop_path = pending.parent / "finalization-stop.json"
                        if not stop_path.exists():
                            write_new(stop_path, {"slot":slot,"input_lock_sha256":lock_hash,"reason":str(write_error)})
                    except BaseException as marker_error:
                        record["finalization_marker_error"] = str(marker_error)
                if reserved:
                    try:
                        event("UNKNOWN", reason="Final result/terminal persistence requires read-only reconciliation",
                              result_write_error=str(write_error))
                    except BaseException as ledger_error:
                        record["finalization_ledger_write_error"] = str(ledger_error)
        if guard is not None:
            guard.close()
        record["elapsed_ms"] = clock.elapsed_ms()
        record["transaction_end_monotonic"] = time.monotonic()
    return record
