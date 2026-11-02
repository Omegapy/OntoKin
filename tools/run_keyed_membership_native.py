#!/usr/bin/env python3
"""Produce actual fresh-ledger C088 native/resource/abstract observations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from keyed_membership_evidence import (
    EvidenceRun, Freeze, MEMBERSHIP_STAGES, PROFILE, error_record, jsonl_writer,
    node_location, save,
)
from keyed_membership_native_fixtures import NativeFactory


class OriginalCancellation(BaseException):
    pass


class Clock:
    def __init__(self): self.value = 0.0
    def __call__(self): return self.value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--groups", nargs="+", choices=("native", "resource", "abstract"),
                        default=("native", "resource", "abstract"))
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    freeze = Freeze(args.inputs)
    run = EvidenceRun(args.output, args.checkout, freeze, "native-observations")
    run.summary.update(groups=list(args.groups), full_cohort=set(args.groups) == {"native", "resource", "abstract"})
    sys.path.insert(0, str(args.checkout.resolve()))
    import ontokin
    if Path(ontokin.__file__).resolve().parent != args.checkout.resolve() / "ontokin":
        raise RuntimeError("Runtime import did not use the selected fixed checkout.")
    from ontokin.values import Type, Value, KeyedValue, UNKNOWN
    from ontokin.bundle import SourceUnit
    from ontokin.execution_budget import SharedExecutionBudget, HostPolicy, admit_entry_budget
    from ontokin.keyed_membership import has_key
    factory = NativeFactory(Type, Value, KeyedValue, UNKNOWN)
    entry = SourceUnit("entry", "native-ledger.ok", (freeze.root / "native-ledger.ok").read_bytes())
    header_operations = freeze.resource["native_setup"]["header_expected_operations"]
    if header_operations != 14:
        raise ValueError("Unexpected frozen header operation basis")

    def observe(case, *, ident, group, local_cap=None, interruption=None, target_step=None, mutation_case=None):
        collection, query, expected_type, traps = factory.build(case)
        clock = Clock()
        cancellation = OriginalCancellation("Original frozen C088 cancellation")
        events, mutations = [], []
        mutate = None
        if mutation_case is not None:
            mutate, mutations = factory.callback(mutation_case, collection, expected_type, traps)
        ledger = None
        def original_callback():
            stage = ledger.stage
            if stage not in MEMBERSHIP_STAGES:
                return
            ordinal = len(events) + 1
            events.append([MEMBERSHIP_STAGES.index(stage), ledger.operations])
            if mutate is not None:
                mutate(stage)
            if ordinal == target_step:
                if interruption in ("deadline", "cancel-cap-deadline", "cap-deadline"):
                    clock.value = 31.0
                if interruption in ("cancel", "cancel-cap-deadline"):
                    raise cancellation
        caps = None if local_cap is None else {"max_operations": header_operations + local_cap}
        ledger = SharedExecutionBudget(policy=HostPolicy(), caller_caps=caps,
                                       check=original_callback, clock=clock)
        original_started = ledger.started
        row = {"id": ident, "group": group, "input_id": case.get("id"),
               "local_cap": local_cap, "interruption": interruption,
               "target_step": target_step, "node": None,
               "helper": "ontokin.keyed_membership.has_key",
               "embedding_policy": {"max_operations": 100000, "max_elapsed_ms": 30000},
               "direct_operation_only": True,
               "source_request_acceptance_claim": False}
        try:
            admit_entry_budget(entry, ledger, profile=PROFILE)
            row.update(header_operations=ledger.operations, operations_before=ledger.operations,
                       stage_before=ledger.stage, string_bytes_before=ledger.string_concat_bytes,
                       admitted_entry_revision=ledger.admitted_entry_revision,
                       resolved_budget=ledger.report())
            if ledger.operations != header_operations:
                raise AssertionError("Actual original entry header differs from independently frozen 14 operations")
            value = has_key(collection, query, expected_type=expected_type, node=None, ledger=ledger)
            row.update(status="returned", result=value if type(value) is bool else None,
                       result_native_type=type(value).__name__)
        except BaseException as error:
            row.update(status="raised", error=error_record(error),
                       same_original_cancellation=(error is cancellation),
                       same_ledger_callback_error=(error is ledger.callback_error))
        row.update(events=events, stage_codes=list(MEMBERSHIP_STAGES),
                   operations_after=ledger.operations, string_bytes_after=ledger.string_concat_bytes,
                   stage_after=ledger.stage, original_started=original_started,
                   final_started=ledger.started, final_clock_seconds=clock.value,
                   execution_budget=ledger.report(status=row["status"]),
                   foreign_methods_called=traps.calls, mutations=mutations,
                   ledger_identity=id(ledger), original_callback_identity=id(original_callback))
        return row

    def add(emit, row):
        emit(row)
        run.summary["records"].append({"id": row["id"], "group": row["group"], "status": row["status"]})
        if len(run.summary["records"]) % 100 == 0:
            run.checkpoint()

    with jsonl_writer(run.output / "native-records.jsonl.gz") as emit:
        if "native" in args.groups:
            for case in freeze.native["cases"]:
                add(emit, observe(case, ident="native/" + case["id"], group="native-negative"))
            for case in freeze.native["valid_metadata_cases"]:
                add(emit, observe(case, ident="valid/" + case["id"], group="native-valid"))
            for case in freeze.native["callback_mutation_cases"]:
                add(emit, observe(case, ident="capture/" + case["id"], group="native-capture", mutation_case=case))
            for case in freeze.native["missing_context_variants"]:
                if case["id"] == "no-ledger": ledger = None
                elif case["id"] == "non-ledger": ledger = object()
                elif case["id"] == "unresolved-ledger": ledger = SharedExecutionBudget(policy=HostPolicy())
                elif case["id"] == "unadmitted-ledger":
                    ledger = SharedExecutionBudget(policy=HostPolicy())
                    ledger.promote({}, entry_revision=None)
                else: raise ValueError("Unknown frozen missing-context fixture")
                before = ledger.operations if isinstance(ledger, SharedExecutionBudget) else None
                row = {"id": "context/" + case["id"], "group": "missing-context", "input_id": case["id"],
                       "negative_only": True, "operations_before": before}
                try:
                    value = has_key(KeyedValue(()), "a", expected_type=Type("Int"), node=None, ledger=ledger)
                    row.update(status="returned", result=value if type(value) is bool else None,
                               result_native_type=type(value).__name__)
                except BaseException as error:
                    row.update(status="raised", error=error_record(error))
                row["operations_after"] = ledger.operations if isinstance(ledger, SharedExecutionBudget) else None
                add(emit, row)
        if "resource" in args.groups:
            for schedule in freeze.resource["cases"]:
                case = {"id": schedule["id"], "keys": schedule["keys"], "query": schedule["query"]}
                for cap in schedule["operation_caps"]:
                    add(emit, observe(case, ident=f"cap/{case['id']}/{cap['available']}",
                                      group="operation-cap", local_cap=cap["available"]))
                for seam in schedule["interruptions"]:
                    step = seam["before_step"]
                    for mode in ("cancel", "deadline", "cancel-cap-deadline", "cap-deadline"):
                        add(emit, observe(case, ident=f"{mode}/{case['id']}/{step}", group=mode,
                                          local_cap=step - 1 if mode in ("cancel-cap-deadline", "cap-deadline") else None,
                                          interruption=mode, target_step=step))
            add(emit, observe({"id": "invalid-query-deadline", "keys": [], "query": ""},
                              ident="precedence/expired-before-semantic-key-error", group="query-error-precedence",
                              interruption="deadline", target_step=2))
        if "abstract" in args.groups:
            from ontokin.texture_bundle import load_texture_file_manifest
            from ontokin.construction import compile_construction
            from ontokin.validator import Context
            from ontokin.syntax import Node
            carrier = load_texture_file_manifest(freeze.root / "empty.files.json")
            def calls(root):
                if isinstance(root, Node):
                    if root.kind == "call" and root.callee.kind == "name" and root.callee.name == "has_key":
                        yield root
                    for value in root.data.values():
                        yield from calls(value)
                elif isinstance(root, (list, tuple)):
                    for value in root:
                        yield from calls(value)
                elif isinstance(root, dict):
                    for value in root.values():
                        yield from calls(value)
            for case in freeze.native["unknown_abstract_cases"]:
                events = []
                ledger = None
                def original_check():
                    if ledger.stage in MEMBERSHIP_STAGES:
                        events.append([MEMBERSHIP_STAGES.index(ledger.stage), ledger.operations])
                ledger = SharedExecutionBudget(policy=HostPolicy(), check=original_check)
                admit_entry_budget(carrier.entry, ledger, profile=PROFILE)
                compiler = compile_construction(carrier, level="constructed", execution_budget=ledger)
                node = next(calls(compiler.program))
                before_events, before_operations = len(events), ledger.operations
                collection = Value(Type("Keyed", element=Type("Int")),
                                   UNKNOWN if case["collection"] == "UNKNOWN" else KeyedValue(()))
                query_type = Type(case["query_type"])
                query = Value(query_type, UNKNOWN if case["query"] == "UNKNOWN" else case["query"])
                row = {"id": "abstract/" + case["id"], "group": "abstract", "input_id": case["id"],
                       "carrier_program_revision": carrier.program_revision,
                       "carrier_operations": before_operations, "node": node_location(node)}
                try:
                    result = compiler.builtin("has_key", [collection, query], node, Context(abstract=case["abstract"]))
                    row.update(status="returned", result_type=result.type.kind, result_known=result.known,
                               result=result.value if result.known and type(result.value) is bool else None)
                except BaseException as error:
                    row.update(status="raised", error=error_record(error))
                row.update(events=events[before_events:], operations_before=before_operations,
                           operations_after=ledger.operations, execution_budget=ledger.report(status=row["status"]))
                add(emit, row)
    finished = run.finish()
    print(json.dumps({"status": run.summary["status"], "records": len(run.summary["records"]),
                      "output": str(run.output)}))
    return 0 if finished else 1


if __name__ == "__main__":
    raise SystemExit(main())
