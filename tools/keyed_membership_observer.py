"""Passive Python-call/stage observation; no runtime function is replaced."""
from __future__ import annotations

import sys

from keyed_membership_evidence import MEMBERSHIP_STAGES, STAGES, node_location, sha


class ExecutionObserver:
    """Observe existing helper calls and the original embedding callback.

    This observer does not assign counters, limits, clocks, metadata or result
    values. It runs inside the same request's existing callback and records the
    counter before the real tick increments it. Python profiling observes the
    unmodified helper code object through any imported function alias.
    """
    def __init__(self, ledger, functions):
        self.ledger = ledger
        self.functions = {fn.__code__: name for name, fn in functions.items()}
        self.calls = []
        self.events = []
        self.active = {}
        self.previous = None

    def __enter__(self):
        self.previous = sys.getprofile()
        if self.previous is not None:
            raise RuntimeError("An existing profiler cannot be silently replaced by the observer.")
        sys.setprofile(self.profile)
        return self

    def __exit__(self, typ, value, tb):
        sys.setprofile(self.previous)

    def checkpoint(self):
        stage = self.ledger.stage
        if stage in STAGES:
            self.events.append([STAGES.index(stage), self.ledger.operations])

    def profile(self, frame, event, arg):
        name = self.functions.get(frame.f_code)
        if name is None:
            return
        if event == "call":
            local = frame.f_locals
            if local.get("ledger") is not self.ledger:
                return
            row = {"helper": name, "node": node_location(local.get("node")),
                   "operations_before": self.ledger.operations,
                   "string_bytes_before": self.ledger.string_concat_bytes,
                   "event_start": len(self.events), "result": None}
            if name == "has_key":
                collection, query = local.get("collection"), local.get("query")
                # Source execution admits these immutable native payloads before
                # the helper. Malformed-native tests use a separate recorder.
                entries = getattr(collection, "entries", None)
                row["input_keys"] = [key for key, leaf in entries] if type(entries) is tuple else None
                row["query"] = query if type(query) is str and len(query) <= 64 else None
                row["query_chars"] = len(query) if type(query) is str else None
                row["query_sha256"] = sha(query.encode()) if type(query) is str else None
            elif name == "concat_strings":
                for side in ("left", "right"):
                    operand = local.get(side)
                    row[side + "_utf8_bytes"] = len(operand.encode()) if type(operand) is str else None
                    row[side + "_sha256"] = sha(operand.encode()) if type(operand) is str else None
            self.active[id(frame)] = row
            self.calls.append(row)
        elif event == "return" and id(frame) in self.active:
            row = self.active.pop(id(frame))
            row.update(operations_after=self.ledger.operations,
                       string_bytes_after=self.ledger.string_concat_bytes,
                       event_end=len(self.events))
            if type(arg) is bool:
                row["result"] = arg
            elif type(arg) is str:
                row["result"] = {"utf8_bytes": len(arg.encode()), "sha256": sha(arg.encode())}
            row["returned_normally_typed"] = type(arg) is (bool if name == "has_key" else str)

    def report(self):
        return {"schema_version": "ontokin.c088-passive-execution-observation/1",
                "stage_codes": list(STAGES), "events": self.events,
                "calls": self.calls, "unterminated_profile_frames": len(self.active),
                "ledger_identity": id(self.ledger), "original_started": self.ledger.started,
                "final_operations": self.ledger.operations,
                "final_string_concat_bytes": self.ledger.string_concat_bytes,
                "intervention": "Passive Python call/return profiling and recording inside the original embedding callback; no helper, clock, counter, limit, input or output replacement."}
