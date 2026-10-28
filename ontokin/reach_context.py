"""Bind newly computed reach observations at the Agent publication boundary.

Only explicitly registered result slots are eligible. This module neither
opens a store nor walks arbitrary result/history trees; an old run, receipt or
retained stronger prefix must preserve its original context byte for byte.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FreshReachProjection:
    record: dict
    context_kind: str
    run_id: str | None


def _snapshot_records(snapshot):
    if isinstance(snapshot, dict) and isinstance(snapshot.get("reaches"), dict):
        yield from snapshot["reaches"].values()


def _fresh_slots(result, run):
    if not isinstance(result, dict):
        return
    for item in result.get("items", []):
        if isinstance(item, dict) and isinstance(item.get("actions"), list):
            for record in item["actions"]:
                if isinstance(record, dict) and record.get("kind") == "reach_planar":
                    yield record, "run_sample"
    for record in _snapshot_records(result.get("initial_state")):
        yield record, "constructed_initial"
    if (run is not None and result.get("run_state") is run
            and not run.get("retained_prior_prefix")):
        for record in _snapshot_records(run.get("last_valid_state")):
            yield record, "run_sample"


def register_fresh(result, *, run=None, inspection_run_id=None):
    """Capture references while the service absorbs a newly computed result."""
    bindings = []
    for record, kind in _fresh_slots(result, run):
        run_id = None if kind == "constructed_initial" else (
            run.get("run_id") if run is not None else inspection_run_id)
        bindings.append(FreshReachProjection(record, kind, run_id))
    return tuple(bindings)


def bind_fresh(bindings, *, result, run, accepted_revision, source_accepted_once):
    """Apply the current transaction's identity to live registered projections.

    A source that was accepted in this project remains non-candidate even if
    it is no longer the accepted head. That fact does not rewrite a historical
    candidate run's independent candidate_only flag or any embedded receipt.
    """
    live = {id(record) for record, _ in _fresh_slots(result, run)}
    for binding in bindings or ():
        record = binding.record
        if id(record) not in live:
            continue
        record.update(context_origin="agent", accepted_program_revision=accepted_revision,
                      candidate_only=not source_accepted_once)
        current = record.get("current")
        value = current.get("value") if isinstance(current, dict) else None
        if value is not None:
            observation = value["observation"]
            observation.update(context_kind=binding.context_kind, run_id=binding.run_id)
