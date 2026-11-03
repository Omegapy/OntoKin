#!/usr/bin/env python3
"""Exercise frozen resource stages in the actual durable Torque Agent service.

The original host callback observes the real native shared-ledger stack frame.
It supplies no helper result and replaces no clock, ledger, tick or callback.
"""
from __future__ import annotations

import argparse
import copy
import inspect
import json
from pathlib import Path
import sys
import time
import traceback

from run_torque_agent_workflows import FrozenAgentRun, ROOT, digest, effective_table, read, write
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget


def retained(service):
    result = {}
    with service._store.connection() as db:
        for table, columns, order in (
            ("projects", "id,accepted_revision", "id"),
            ("sources", "project_id,revision,filename,raw,accepted_once", "project_id,revision"),
            ("runs", "project_id,id,source_revision,descriptor,version", "project_id,id"),
            ("artifacts", "project_id,id,source_revision,data,report,sha256", "project_id,id"),
        ):
            result[table] = [[{"blob_bytes": len(value), "blob_sha256": digest(value)}
                              if isinstance(value, bytes) else value for value in row]
                             for row in db.execute("SELECT " + columns + " FROM " + table + " ORDER BY " + order)]
    return result


def callsite(stage):
    """Observe the concrete native structural charge and occurrence identity."""
    frame = inspect.currentframe().f_back
    result = {"kind": None, "path": None, "unlatched_empty": False, "previous_stage": None}
    try:
        while frame is not None:
            local = frame.f_locals
            if frame.f_code.co_name == "charge" and result["kind"] is None:
                result["kind"] = local.get("kind")
            if frame.f_code.co_name in ("_stage", "torque_stage", "check_torque_structure", "source_intervals"):
                if "previous" in local and result["previous_stage"] is None:
                    result["previous_stage"] = local["previous"]
            if frame.f_code.co_name == "torque_projection":
                result["path"] = local.get("path")
                history = local.get("history")
                result["unlatched_empty"] = (history is not None and history.axis is None
                                               and not history.active and not history.last_changes)
            if frame.f_code.co_name == "_reference_origin":
                result["path"] = local.get("path")
                result["time"] = str(local.get("time"))
            frame = frame.f_back
    finally:
        del frame
    if stage == "torque_source" and result["kind"] is None:
        result["kind"] = stage
    return result


def run_variant(args, case, directory, variant, control=None):
    class HostSentinel(BaseException):
        pass
    sentinel = HostSentinel("original admitted callback at " + case["stage"])
    armed = {"value": False, "fired": False, "observing": False, "now": 1000.0}
    def host_check():
        if armed["observing"]:
            frame = inspect.currentframe().f_back
            try:
                while frame is not None and frame.f_code is not SharedExecutionBudget.tick.__code__:
                    frame = frame.f_back
                if frame is None:
                    raise AssertionError("The original host callback has no actual native ledger tick")
                ledger, amount = frame.f_locals["self"], frame.f_locals["amount"]
                observe_tick(ledger, amount)
            finally:
                del frame
        if armed["value"] and variant == "original-callback-exception":
            raise sentinel
    def clock():
        return armed["now"]
    run = FrozenAgentRun(args, directory, args.output.name+"-"+case["id"]+"-"+variant,
        policy=HostPolicy(**case["host_policy"]), host_check=host_check, clock=clock)
    trace, ledgers, original_checks, selected = [], [], [], None
    result = {"case": case["id"], "stage": case["stage"], "variant": variant, "status": "running"}
    def observe_tick(ledger, amount):
        nonlocal selected
        if not ledgers:
            ledgers.append(ledger)
            original_checks.append(ledger.check)
        run.check(ledger is ledgers[0], "All task work retains one actual ledger")
        run.check(ledger.check is original_checks[0], "The admitted callback object is never replaced")
        if ledger.stage == case["stage"]:
            site = callsite(ledger.stage)
            row = {"operation_before": ledger.operations, "amount": amount, "ledger_id": id(ledger),
                   "callback_id": id(ledger.check), "started": ledger.started,
                   "deadline": ledger.started + ledger.limits["max_elapsed_ms"]/1000,
                   "effective": ledger.limits, **site}
            trace.append(row)
            eligible = site["kind"] == case["stage"] and amount > 0
            if case["id"].startswith("R13"):
                eligible = eligible and site["unlatched_empty"] and site["path"] == "ball.label"
            if case["id"].endswith("reference-change"):
                eligible = eligible and site.get("time") == "1"
            if eligible and not armed["fired"]:
                armed["fired"] = True
                selected = copy.deepcopy(row)
                if variant == "cancel":
                    run.exchange(run.resolve(case["cancel_request"]), key=case["id"]+".cancel",
                                 expected_status="succeeded")
                    # The service's unchanged callback polls its durable row at
                    # most every5ms. Allow that real polling interval to pass.
                    time.sleep(0.006)
                elif variant == "deadline":
                    armed["now"] = ledger.started + ledger.limits["max_elapsed_ms"]/1000 + 0.001
                elif variant == "original-callback-exception":
                    armed["value"] = True
    try:
        run.steps(case["id"], [case["setup"]])
        run.steps(case["id"], case.get("additional_setup", []))
        before = retained(run.service)
        write(directory / "before.json", before)
        request = run.resolve(case["task_request"])
        if variant == "operation-cap":
            request["budgets"] = {**request.get("budgets", {}),
                                  "max_operations": control["selected"]["operation_before"]}
        run.exchange(request, key=case["id"]+".queue", expected_status="queued", wait=False)
        caught = None
        armed["observing"] = True
        try:
            run.service.work_next()
        except BaseException as error:
            caught = error
        finally:
            armed["observing"] = False
        armed["value"] = False
        if variant == "original-callback-exception":
            run.check(caught is sentinel, "The exact original callback exception crosses all private helpers")
            result["same_exception_identity"] = caught is sentinel
        elif caught is not None:
            raise caught
        if variant == "control":
            status, code = "succeeded", None
        elif variant in ("cancel", "original-callback-exception"):
            status, code = "cancelled", None
        else:
            status, code = "failed", "OKL-E-RESOURCE"
        response = run.exchange(request, key=case["id"]+".terminal", expected_status=status,
                                expected_code=code, wait=False)
        run.check(selected is not None, "The selected real structural stage was reached")
        terminal = response
        if case["id"] == "R13" and variant == "control":
            expected_paths = {item["path"] for item in response["result"]["items"]}
            observed_paths = {row["path"] for row in trace if row["kind"] == case["stage"]}
            run.check(observed_paths == expected_paths, "Every carrier and empty massless object header is actually charged")
            run.check(selected["path"] == "ball.label" and selected["unlatched_empty"],
                      "Selected fault barrier is an actual empty massless marker header")
        status_response = run.exchange(run.resolve(case["status_request"]), key=case["id"]+".status",
                                       expected_status="succeeded")
        run.check(status_response["result"]["target"] == terminal, "Status reconciles exact retained target outcome")
        after = retained(run.service)
        write(directory / "after.json", after)
        if variant != "control":
            run.check(before == after, "Failed task leaves every accepted source/run/artifact row unchanged")
            run.check(ledgers[0].stage != case["stage"], "Stage owner restored after fault unwinds")
            run.check(response["execution_budget"]["started_monotonic_seconds"] == selected["started"],
                      "Failure retains original monotonic start")
            run.check(response["execution_budget"]["deadline_monotonic_seconds"] == selected["deadline"],
                      "Failure retains original admitted deadline")
        if variant == "operation-cap":
            run.check(selected["operation_before"] == control["selected"]["operation_before"],
                      "Reduced cap expires at independently observed original structural tick")
            failed_tick = selected["operation_before"] + selected["amount"]
            details = next(d["details"] for d in response["diagnostics"]
                           if d["code"] == "OKL-E-RESOURCE")
            run.check(details["consumed"] == failed_tick and details["stage"] == case["stage"],
                      "Original diagnostic identifies exact failing structural tick")
            run.check(response["execution_budget"]["consumed_operations"] == ledgers[0].operations
                      and ledgers[0].operations >= failed_tick,
                      "Every subsequent inherited request check retains the same consumed-work prefix")
        result.update(status="passed", selected=selected, stage_visits=len(trace),
                      final_stage=ledgers[0].stage, actual_ledger_id=id(ledgers[0]),
                      actual_callback_id=id(original_checks[0]), execution_budget=response.get("execution_budget"))
    except BaseException as error:
        result.update(status="failed", error=type(error).__name__+": "+str(error), traceback=traceback.format_exc(),
                      selected=selected, stage_visits=len(trace))
    finally:
        write(directory / "stage-trace.json", trace)
        try:
            run.finish()
        except BaseException as error:
            result.update(status="failed", closing_error=repr(error), closing_traceback=traceback.format_exc())
        result.update(checks=run.checks, exchanges=run.exchanges)
        write(directory / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--schema-root", type=Path, default=ROOT)
    parser.add_argument("--cases", nargs="+")
    args = parser.parse_args()
    args.output = args.output.absolute()
    args.output.mkdir()
    table = effective_table(args.source_root,
        "docs/language-design/torque-v0.1/freeze/agent/resource-cases.json", "c091-projection-run-prerequisite")
    cases = [case for case in table["cases"] if not args.cases or case["id"] in args.cases]
    if not args.cases or "R10" in args.cases:
        original = next(case for case in table["cases"] if case["id"] == "R10")
        domain = next(case for case in read(args.source_root /
            "docs/language-design/torque-v0.1/freeze/evaluation-domain-cases.json")["cases"]
            if case["id"] == "domain04-reference-only-change")
        repeated = copy.deepcopy(original)
        repeated.update(id="R10-reference-change", fixture=domain["id"])
        repeated["setup"]["request"]["bundle"] = {"$bundle_file": domain["file_manifest"]}
        repeated["task_request"].update(program_revision=domain["identity"]["program_revision"],
                                        until_seconds=domain["reference_origin_changes_at"])
        repeated["derivation"] = "Explicit R10 special requirement: domain04 at its frozen reference-origin change clock"
        cases.append(repeated)
    results = []
    for case in cases:
        parent = args.output / case["id"]
        parent.mkdir()
        control = run_variant(args, case, parent / "control", "control")
        results.append(control)
        print(json.dumps({k: control[k] for k in ("case", "variant", "status", "stage_visits")}), flush=True)
        if control["status"] != "passed":
            continue
        for variant in case["fault_variants"]:
            result = run_variant(args, case, parent / variant, variant, control)
            results.append(result)
            print(json.dumps({k: result[k] for k in ("case", "variant", "status", "stage_visits")}), flush=True)
    passed = all(result["status"] == "passed" for result in results)
    write(args.output / "summary.json", {"status": "passed" if passed else "failed", "results": results,
        "frozen_resource_sha256": digest((args.source_root / "docs/language-design/torque-v0.1/freeze/agent/resource-cases.json").read_bytes()),
        "complete_torque_release": False})
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
