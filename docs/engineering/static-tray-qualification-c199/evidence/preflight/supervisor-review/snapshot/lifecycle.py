"""Eight assigned subprocess controls, explicitly separate from native evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

from .store import promote, read_state, revision, seal_candidate, verify_candidate
from .supervisor import Clock, Stop, json_bytes, run_process, sha256_file


def snapshot(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): {"sha256": sha256_file(p),
            "size_bytes": p.stat().st_size, "mode": p.stat().st_mode & 0o777}
            for p in sorted(root.rglob("*")) if p.is_file() and not p.name.startswith(".")}


def control(case, destination):
    if case not in {"L%02d" % number for number in range(1, 9)}:
        raise ValueError("Unknown assigned lifecycle control")
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=False)
    store = root / "store"
    old = store / "objects" / "accepted-old"
    old.mkdir(parents=True)
    (old / "source.ok").write_bytes(b"sealed predecessor source")
    (old / "final.glb").write_bytes(b"sealed predecessor artifact - lifecycle seam only")
    for path in old.iterdir():
        path.chmod(0o444)
    old.chmod(0o555)
    predecessor = {"revision": "old", "candidate": "objects/accepted-old"}
    (store / "state.json").write_bytes(json_bytes(predecessor))
    before = snapshot(store)
    stage = root / "child-stage"
    stage.mkdir()
    built = root / "constructed-candidate"
    built.mkdir()
    (built / "source.txt").write_bytes(b"fixed prevalidated construction seam")
    (built / "final.glb").write_bytes(b"not native geometry; lifecycle fixture only")
    clock = Clock(total_ms=30000)
    phase = "receiving" if case in {"L01", "L08"} else "construction"
    result = {"schema": "ontokin.static-tray.lifecycle-control/0.1.0", "case": case,
              "tested_phase": phase, "direct_child_starts": 0, "grandchild_starts": 0,
              "native_starts": 0, "receiver_native_starts": 0,
              "other_stage": "sealed prevalidated in-process fixture seam",
              "before": before, "built_pending_pointer_unchanged": False}
    if phase == "receiving":
        candidate, closure = seal_candidate(built, store, "candidate-"+case)
        verify_candidate(candidate)
        result["built_pending_pointer_unchanged"] = read_state(store) == predecessor
    deadline = clock.end if case not in {"L03", "L05"} else clock.started + 0.3
    process_record = None
    def started(record):
        result["direct_child_starts"] += 1
    try:
        process_record = run_process([sys.executable, "-IB", str(Path(__file__).with_name("lifecycle_stub.py")), case],
            stage=stage, label=phase, clock=clock, stage_end=deadline,
            on_started=started, cancel_after_ms=150 if case == "L04" else None)
        if case == "L07":
            try:
                json.loads((stage / "stub-result.json").read_bytes())
            except (ValueError, OSError):
                raise Stop("OTRAY-E-DELIVERY", "Independent stage rejects malformed controlled output")
            raise AssertionError("Malformed control unexpectedly decoded")
        receipt = json.loads((stage / "stub-result.json").read_bytes())
        if receipt != {"passed": True}:
            raise Stop("OTRAY-E-DELIVERY", "Controlled receiving output rejected")
        new_state = {"revision": "new", "candidate": "objects/candidate-"+case,
                     "closure_sha256": closure}
        verify_candidate(candidate)
        if case == "L08":
            stale_store = root / "stale-store"
            shutil.copytree(store, stale_store)
            (stale_store / "state.json").write_bytes(json_bytes({"revision": "other"}))
            stale_before = snapshot(stale_store)
            try:
                promote(stale_store, expected="old", state=new_state, clock=clock,
                        cleanup_records=[process_record])
            except Stop as exc:
                result["stale_rejected"] = exc.code == "OTRAY-E-STALE"
                result["stale_preserved"] = snapshot(stale_store) == stale_before
            unknown_store = root / "unknown-store"
            shutil.copytree(store, unknown_store)
            try:
                promote(unknown_store, expected="old", state=new_state, clock=clock,
                        cleanup_records=[process_record], lost_reply=True)
            except Stop as exc:
                result["unknown_observed"] = exc.state == "UNKNOWN"
                result["unknown_reconciled_without_child_or_write_retry"] = read_state(unknown_store) == new_state
            result["state"] = "REJECTED_STALE_AND_RECONCILED_UNKNOWN"
        else:
            result["promotion"] = promote(store, expected="old", state=new_state,
                clock=clock, cleanup_records=[process_record])
            result["state"] = "ACCEPTED"
    except Stop as exc:
        process_record = getattr(exc, "process_record", process_record)
        result["state"], result["error"] = exc.state, exc.as_dict()
    if (stage / "grandchild.json").exists():
        result["grandchild_starts"] = 1
        result["grandchild"] = json.loads((stage / "grandchild.json").read_bytes())
    after = snapshot(store)
    result["after"] = after
    result["prior_immutable_bytes_preserved"] = all(after.get(k) == v for k,v in before.items() if k != "state.json")
    result["accepted_pointer_preserved"] = read_state(store) == predecessor
    result["process"] = process_record
    result["elapsed_ms"] = clock.elapsed_ms()
    cleanup = bool(process_record and process_record["handles_closed"] and process_record["cleanup"]["passed"])
    expectations = {
        "L01": result["state"] == "ACCEPTED" and result["built_pending_pointer_unchanged"],
        "L02": result["state"] == "REJECTED" and (stage / "partial.bin").exists(),
        "L03": result["state"] == "TIMEOUT",
        "L04": result["state"] == "CANCELLED" and process_record is not None and process_record.get("cancellation_completion_ms", 100000) <= 2000,
        "L05": result["state"] == "TIMEOUT" and result["grandchild_starts"] == 1,
        "L06": result["state"] == "REJECTED" and result.get("error", {}).get("code") == "OTRAY-E-RESOURCE",
        "L07": result["state"] == "REJECTED" and result.get("error", {}).get("code") == "OTRAY-E-DELIVERY",
        "L08": all(result.get(key) for key in ["stale_rejected", "stale_preserved", "unknown_observed", "unknown_reconciled_without_child_or_write_retry"])}
    result["passed"] = (expectations[case] and cleanup and result["direct_child_starts"] == 1
        and result["prior_immutable_bytes_preserved"]
        and (case == "L01" or result["accepted_pointer_preserved"]))
    (root / "RESULT.json").write_bytes(json_bytes(result))
    return result


def controls(destination):
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=False)
    results = [control("L%02d" % number, root / ("L%02d" % number)) for number in range(1, 9)]
    report = {"schema": "ontokin.static-tray.lifecycle-suite/0.1.0",
        "passed": all(row["passed"] for row in results),
        "direct_child_starts": sum(row["direct_child_starts"] for row in results),
        "grandchild_starts": sum(row["grandchild_starts"] for row in results),
        "native_starts": 0, "scope": "Controlled subprocess mechanics; no observed Blender cancellation claim",
        "results": [{key:row[key] for key in ["case", "passed", "state", "elapsed_ms"]} for row in results]}
    (root / "RESULTS.json").write_bytes(json_bytes(report))
    return report
