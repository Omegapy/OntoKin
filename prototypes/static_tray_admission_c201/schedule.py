"""Exact public C201 schedule, independent of the consumed C200 coordinator."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


PROTOCOL_SHA256 = "f1bd2895cc448f5a1ecb6495814c261dfeba8fecab8ea266e274a35475386064"
SCHEDULE_ID = "C201-Q01-A01-A04-v0.1.0"
ORDER = ("A01", "D01", "D03", "A02", "A03", "A04")


class LedgerError(ValueError):
    """A closed gate, with an inspectable reason and consumed-state flag."""

    def __init__(self, code, message, *, consumed=False):
        super().__init__(message)
        self.code = code
        self.consumed = consumed


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False, ensure_ascii=True).encode("ascii")
    except (TypeError, ValueError, RecursionError) as exc:
        raise LedgerError("SCHEDULE", "Expected bounded canonical JSON data") from exc


@dataclass(frozen=True)
class Slot:
    name: str
    route: str
    kind: str
    source_closure: str
    accepted_source_reference: str | None
    completed_predecessor: str | None
    equality_references: tuple[str, ...]
    required_controls: tuple[str, ...] = ()

    def references(self):
        return {"accepted_source_reference": self.accepted_source_reference,
                "completed_predecessor": self.completed_predecessor,
                "equality_references": list(self.equality_references),
                "required_completed_controls": list(self.required_controls)}


SLOTS = (
    Slot("A01", "ontokin", "baseline", "ontokin", None, None, ()),
    Slot("A02", "direct-python", "baseline", "direct-python", None, "A01",
         ("A01",), ("D01", "D03")),
    Slot("A03", "ontokin", "clean-regeneration",
         "A01 retained accepted source/dependencies", "A01", "A02", ("A01",)),
    Slot("A04", "direct-python", "clean-regeneration",
         "A02 retained accepted source/dependencies", "A02", "A03", ("A02", "A03")),
)


def expected_schedule():
    """Return a fresh exact copy; caller mutations cannot change the contract."""
    rows = []
    for slot in SLOTS:
        row = {"slot": slot.name, "route": slot.route, "kind": slot.kind,
               "case": "Q01", "source_closure": slot.source_closure,
               "accepted_source_reference": slot.accepted_source_reference,
               "completed_predecessor": slot.completed_predecessor,
               "equality_references": list(slot.equality_references),
               "maximum_native_starts": 1, "maximum_receiving_starts": 1,
               "maximum_actual_delivery_node_starts": 1}
        if slot.required_controls:
            row["required_completed_controls"] = list(slot.required_controls)
        rows.append(row)
    return {
        "schedule_id": SCHEDULE_ID, "one_use_invocation_required": True,
        "current_executable_invocation": None, "order": list(ORDER),
        "native_slot_order": [s.name for s in SLOTS], "slots": rows,
        "ceilings": {"native_starts": 4, "receiving_starts": 4,
                     "actual_delivery_node_starts": 4, "renders_per_receiving_job": 1,
                     "timed_authors": 0, "simulations": 0, "automatic_retries": 0,
                     "extra_renders": 0, "extra_receiver_jobs": 0, "lifecycle_cohorts": 0,
                     "deliberate_blender_cancellation_experiments": 0,
                     "synthetic_node_preparation_cohorts": 0},
        "consumption_rule": "Every attempted child start consumes its assigned stage allowance, including failure, timeout, cancellation and unknown outcome. A ceiling is not permission to continue after an unexpected result.",
        "receiving_then_node": "Receiving measurements and cleanup precede conditional promotion; actual-delivery Node checking then gates the next slot. Node failure stops the schedule and does not turn a technically accepted transaction into family admission.",
    }


SCHEDULE_SHA256 = hashlib.sha256(canonical(expected_schedule())).hexdigest()


def exact(value, expected):
    """Compare JSON shape and values without Python's bool/int equivalence."""
    if type(value) is not type(expected):
        return False
    if type(expected) is dict:
        return (value.keys() == expected.keys()
                and all(exact(value[key], item) for key, item in expected.items()))
    if type(expected) is list:
        return len(value) == len(expected) and all(exact(a, b) for a, b in zip(value, expected))
    return value == expected


def validate_schedule(value):
    """Reject any difference, including bool/int confusion or an old N-slot plan."""
    if not exact(value, expected_schedule()):
        raise LedgerError("SCHEDULE", "Only the exact approved A01-A04 schedule is admitted")
    return SCHEDULE_SHA256


def read_protocol(path):
    """Bind the unchanged preparation document, not a future executable lock."""
    path = Path(path)
    with path.open("rb") as stream:
        data = stream.read(262145)
    if len(data) > 262144 or hashlib.sha256(data).hexdigest() != PROTOCOL_SHA256:
        raise LedgerError("PROTOCOL", "The approved C201 preparation bytes differ")
    value = json.loads(data)
    validate_schedule(value["schedule"])
    return value["schedule"]
