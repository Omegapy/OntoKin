"""One finite, nonretrying native schedule plus actual delivered GLB controls."""
from __future__ import annotations

from pathlib import Path
import time

from .canonical import ROOT
from .lock import independent_modules, read_json, verify_lock
from .store import verify_candidate
from .supervisor import Clock, Stop, sha256_file
from .transaction import _prior_result, alarm_until, run_transaction, write_new


def required_delivered_controls(lock, after_slot):
    return [row for row in lock["delivered_controls"] if row["after_slot"] == after_slot]


def delivered_control(lock, lock_hash, row):
    """Mutate only fresh copies; actual rejected geometry is retained verbatim."""
    clock = Clock(total_ms=30000)
    destination = Path(row["directory"])
    result = {"schema": "ontokin.static-tray.delivered-control-result/0.1.0", "case": row["case"],
              "variant": row["variant"], "input_lock_sha256": lock_hash, "passed": False, "native_starts": 0,
              "expected": row["expected"], "source_slot": row["after_slot"], "started_monotonic": clock.started}
    created = False
    try:
        with alarm_until(clock, clock.end):
            destination.mkdir(parents=True, exist_ok=False)
            created = True
            write_new(destination / "reserved.json", result)
            _, candidate, before = _prior_result(lock, row["after_slot"])
            artifact = candidate / "final.glb"
            baseline = read_json(candidate / "independent-audit.json")
            modules = independent_modules(lock)
            control = next(x for x in read_json(ROOT / "docs/engineering/static-tray-mapping-c198/CONTROLS.json")["controls"] if x["id"] == row["case"])
            changed = destination / "changed.glb"
            receipt = modules["corrupt"].corrupt(row["case"], artifact, changed, row["variant"])
            clock.check()
            write_new(destination / "corruption.json", receipt)
            audit = modules["reader"].audit(changed, row["expected"], baseline, lock["independent_reader"]["delivery_rules"])
            write_new(destination / "audit.json", audit)
            classes = sorted({finding["classification"] for finding in audit["findings"]})
            required = control.get("required_findings", [control["expected_diagnostic_class"]] if "expected_diagnostic_class" in control else [])
            preserved = verify_candidate(candidate) == before and receipt["input_sha256"] == sha256_file(artifact)
            result.update(required_findings=required, observed_findings=classes, audit_passed=audit["passed"],
                          actual_input_sha256=sha256_file(artifact), actual_output_sha256=sha256_file(changed),
                          original_closure_preserved=preserved, corruption_receipt=receipt)
            if row["case"] == "D08":
                equal = artifact.read_bytes() == changed.read_bytes()
                measured_equal = all(audit[k] == baseline[k] for k in ("nodes", "measurements", "right_closure"))
                result.update(exact_bytes_equal=equal, measured_equal=measured_equal,
                              regeneration_equality_passed=equal)
                result["passed"] = preserved and audit["passed"] and measured_equal and equal == (row["variant"] == "copy")
            else:
                result["passed"] = preserved and not audit["passed"] and set(required) <= set(classes) and "STRUCTURE" not in classes
            clock.check()
            if not result["passed"]:
                raise Stop("OTRAY-E-DELIVERY", "Actual delivered corruption has an unexpected classification or changed its retained source")
    except BaseException as exc:
        result["passed"] = False
        result["error"] = exc.as_dict() if isinstance(exc, Stop) else {"code": "OTRAY-E-DELIVERY", "reason": type(exc).__name__ + ": " + str(exc)}
    result["elapsed_ms"] = clock.elapsed_ms()
    result["finished_monotonic"] = time.monotonic()
    if created:
        write_new(destination / "result.json", result)
    return result


def verify_delivered_predecessors(lock, slot, lock_hash=None):
    """The individual run interface cannot skip an earlier failed reader control."""
    ordinal = int(slot[1:])
    for row in lock.get("delivered_controls", []):
        if int(row["after_slot"][1:]) >= ordinal:
            continue
        result = read_json(Path(row["directory"]) / "result.json")
        if result.get("passed") is not True or result.get("case") != row["case"] or result.get("variant") != row["variant"]:
            raise Stop("OTRAY-E-DELIVERY", "An assigned earlier delivered control is incomplete or failed")
        if lock_hash is not None and result.get("input_lock_sha256") != lock_hash:
            raise Stop("OTRAY-E-BINDING", "Delivered control belongs to a different input lock")
    if "external_readback" in lock:
        from .format_check import verify_predecessors
        verify_predecessors(lock, lock_hash, slot)


def run_qualification(lock_path, *, progress=None):
    """Run each locked transaction once and stop on the first unexpected result."""
    preflight = Clock(total_ms=30000)
    with alarm_until(preflight, preflight.end):
        lock, lock_hash = verify_lock(lock_path, runtime=True, check=preflight.check)
    schedule = Path(lock["schedule_root"])
    if schedule.exists():
        raise Stop("OTRAY-E-RESOURCE", "Qualification requires the locked new schedule; a prior schedule cannot be restarted")
    result = {"schema": "ontokin.static-tray.qualification/0.1.0", "input_lock_sha256": lock_hash,
              "implementation": lock["implementation"], "native_slots_maximum": 12,
              "read_only_preflight_elapsed_ms": preflight.elapsed_ms(),
              "transactions": [], "delivered_controls": [], "native_starts": 0, "receiving_starts": 0,
              "external_readbacks": [], "read_only_checker_starts": 0,
              "measured_gates_passed": False, "qualified": False, "visual_review": "PENDING_ACTUAL_ARTIFACT_REVIEW",
              "scope": "Finite C199 geometry qualification; tray admission, timed authors and inherited regression are separate"}
    stopped = False
    for row in lock["slots"]:
        if stopped:
            break
        transaction = run_transaction(lock_path, row["slot"], route=row["route"], source=row["source_manifest"],
                                      store=row["store"], result_path=row["result"])
        result["transactions"].append({key: transaction.get(key) for key in ("slot", "case", "route", "state", "native_starts", "receiving_starts", "elapsed_ms", "error")})
        result["native_starts"] += transaction["native_starts"]
        result["receiving_starts"] += transaction["receiving_starts"]
        if progress:
            progress(result["transactions"][-1])
        if transaction["state"] != "ACCEPTED" or transaction.get("elapsed_ms", float("inf")) > 65000:
            stopped = True
            result["stopped_at"] = {"kind": "transaction", "slot": row["slot"]}
            break
        from .format_check import run_check
        readback = run_check(lock, lock_hash, row["slot"])
        result["external_readbacks"].append({key: readback.get(key) for key in ("slot", "passed", "state", "checker_starts", "validator", "three", "elapsed_ms", "error")})
        result["read_only_checker_starts"] += readback["checker_starts"]
        if progress:
            progress(result["external_readbacks"][-1])
        if not readback["passed"] or readback.get("elapsed_ms", float("inf")) > 30000:
            stopped = True
            result["stopped_at"] = {"kind": "external_readback", "slot": row["slot"]}
            break
        for control in required_delivered_controls(lock, row["slot"]):
            observation = delivered_control(lock, lock_hash, control)
            result["delivered_controls"].append({key: observation.get(key) for key in ("case", "variant", "passed", "required_findings", "observed_findings", "elapsed_ms", "error")})
            if progress:
                progress(result["delivered_controls"][-1])
            if not observation["passed"]:
                stopped = True
                result["stopped_at"] = {"kind": "delivered_control", "case": control["case"], "variant": control["variant"]}
                break
    result["measured_gates_passed"] = (not stopped and len(result["transactions"]) == 12
        and result["native_starts"] == 12 and result["receiving_starts"] == 12
        and len(result["external_readbacks"]) == 12 and result["read_only_checker_starts"] == 12
        and all(r["passed"] for r in result["external_readbacks"])
        and len(result["delivered_controls"]) == 9 and all(r["passed"] for r in result["delivered_controls"]))
    result["status"] = "MEASURED_GATES_PASSED_VISUAL_REVIEW_PENDING" if result["measured_gates_passed"] else "STOPPED_AFTER_FIRST_UNEXPECTED_RESULT"
    write_new(schedule / "qualification-result.json", result)
    return result
