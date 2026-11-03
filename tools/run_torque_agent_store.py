#!/usr/bin/env python3
"""Observe separate real .21/.22 stores, cancellation and late publication caps."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import traceback

from run_torque_agent_workflows import FrozenAgentRun, ROOT, digest, file_digest, read, write
from run_torque_agent_resources import retained
from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.agent_store import dumps
from ontokin.keyed_membership_agent import KeyedMembershipAgentService
from ontokin.keyed_membership_protocol import KeyedMembershipProtocol
from ontokin.program_agent import ProgramAgentService
from ontokin.texture_bundle import load_texture_file_manifest, load_texture_bundle
from ontokin.torque_agent import TorqueAgentService


def execute(args):
    run = FrozenAgentRun(args, args.output / "A10", args.output.name+"-A10")
    result = {"status": "running", "scenario": "A10"}
    old = None
    try:
        old = KeyedMembershipAgentService(run.directory / "store")
        original21 = load_texture_file_manifest(run.frozen / "control-spin-up.files.json")
        program22 = load_texture_file_manifest(run.frozen / "p01-spin-up.files.json")
        project = run.namespace+"-same-project"
        from jsonschema import Draft202012Validator
        validators21 = {name: Draft202012Validator(read(args.schema_root /
            ("docs/language-design/agent-v0.21/"+name+".schema.json")), registry=run.registry)
            for name in ("request", "response")}
        def send21(operation, ident, **fields):
            request = {"schema_version": "ontokin.agent/0.21", "project_id": project,
                       "request_id": ident, "operation": operation, **fields}
            clean, raw = KeyedMembershipProtocol.canonical_request(request)
            validators21["request"].validate(clean)
            response = old.handle(clean)
            validators21["response"].validate(response)
            run.exchanges += 1
            run.log.write(dumps({"index": run.exchanges, "key": "A10.predecessor."+ident,
                "request": clean, "request_canonical_sha256": digest(raw.encode()), "response": response})+"\n")
            run.log.flush()
            run.check(response["status"] == "succeeded", "Real predecessor operation "+operation)
            return response
        send21("create", "same-create", bundle=original21.to_payload(), expected_program_revision=None,
               requested_level="constructed")
        created22 = run.exchange({"schema_version": "ontokin.agent/0.22", "project_id": project,
            "request_id": "same-create", "operation": "create", "bundle": program22.to_payload(),
            "expected_program_revision": None, "requested_level": "constructed"}, expected_status="succeeded")
        evaluated21 = send21("evaluate", "same-evaluate", program_revision=original21.program_revision,
                            until_seconds="1", run_id=None)
        evaluated22 = run.exchange({"schema_version": "ontokin.agent/0.22", "project_id": project,
            "request_id": "same-evaluate", "operation": "evaluate", "program_revision": program22.program_revision,
            "until_seconds": "1", "run_id": None}, expected_status="succeeded")
        run.check(old.database_path != run.service.database_path, "Equal project/request names use separate actual files")
        run.check(old.accepted_revision(project) == original21.program_revision, "Predecessor accepted source identity")
        run.check(run.service.accepted_revision(project) == program22.program_revision, "Torque accepted source identity")
        old_path = old.database_path
        old.close()
        old = None
        old_hash = file_digest(old_path)
        with sqlite3.connect("file:"+str(old_path)+"?mode=ro", uri=True) as db:
            metadata = dict(db.execute("SELECT name,value FROM metadata"))
            run.check(metadata["schema_version"] == "ontokin.keyed-membership-program-agent-store/0.1",
                      "Read-only predecessor schema identity")
            for revision, raw in db.execute("SELECT revision,raw FROM sources"):
                bundle = load_texture_bundle(json.loads(raw))
                run.check(bundle.program_revision == revision and bundle.to_payload() == original21.to_payload(),
                          "Read-only predecessor exact source and PNG closure")
            for payload, hashed, response in db.execute("SELECT payload,digest,response FROM requests"):
                run.check(digest(payload.encode()) == hashed and json.loads(response)["schema_version"] == "ontokin.agent/0.21",
                          "Predecessor durable request/protocol receipt")
        write(run.directory / "predecessor-observation.json", {"path": old_path.name, "sha256": old_hash,
            "bytes": old_path.stat().st_size, "schema_version": metadata["schema_version"],
            "actual_run_id": evaluated21["run_id"], "program_revision": original21.program_revision})
        wrong = run.directory / "mismatched-store"
        wrong.mkdir()
        wrong_path = wrong / "torque-program-agent.sqlite3"
        shutil.copyfile(old_path, wrong_path)
        try:
            TorqueAgentService(wrong)
        except ProtocolError as error:
            run.check(error.code == "OKA-E-STORE-VERSION", "Explicit .22 refuses a retained .21 schema")
            write(run.directory / "mismatched-store-refusal.json", error.to_dict())
        else:
            raise AssertionError("Mismatched actual store schema was accepted")
        run.check(file_digest(wrong_path) == old_hash and file_digest(old_path) == old_hash,
                  "Failed explicit store selection changes neither old data nor copied wrong store")
        old = KeyedMembershipAgentService(run.directory / "store")
        send21("inspect", "reopened", program_revision=original21.program_revision,
            run_id=evaluated21["run_id"], selector={"kind": "object"}, fields=["state"], limit=100,
            time={"seconds": "1", "side": "after"})
        run.close()
        run.open()
        run.exchange({"schema_version": "ontokin.agent/0.22", "project_id": project,
            "request_id": "reopened", "operation": "inspect", "program_revision": program22.program_revision,
            "run_id": evaluated22["run_id"], "selector": {"kind": "object"}, "fields": ["state"], "limit": 100,
            "time": {"seconds": "1", "side": "after"}}, expected_status="succeeded")
        # Actual queued cancellation before acceptance retains no accepted
        # source; after acceptance it cannot advance the previously saved run.
        for accepted in (False, True):
            prefix = "after-acceptance" if accepted else "before-acceptance"
            request = {"schema_version": "ontokin.agent/0.22", "project_id": project if accepted else project+"-never-accepted",
                       "request_id": prefix, "operation": "evaluate" if accepted else "create"}
            if accepted:
                request.update(program_revision=program22.program_revision, run_id=evaluated22["run_id"], until_seconds="2")
            else:
                request.update(bundle=program22.to_payload(), expected_program_revision=None, requested_level="constructed")
            before = retained(run.service)
            run.exchange(request, expected_status="queued", wait=False)
            run.exchange({"schema_version": "ontokin.agent/0.22", "project_id": request["project_id"],
                "request_id": prefix+"-cancel", "operation": "cancel", "target_request_id": prefix}, expected_status="succeeded")
            run.exchange(request, expected_status="cancelled", wait=False)
            after = retained(run.service)
            if not accepted:
                run.check(run.service.accepted_revision(request["project_id"]) is None, "Cancelled create has no accepted source")
                after["projects"] = [row for row in after["projects"] if row[0] != request["project_id"]]
            run.check(before == after, "Queued cancellation preserves every already accepted state row")
        with ProgramAgentService(run.directory / "program-default") as default:
            run.check(default._protocol.SCHEMA_VERSION == "ontokin.agent/0.2", "Earlier program default remains .2")
        with AgentService(run.directory / "core-default") as default:
            run.check(default._protocol.SCHEMA_VERSION == "ontokin.agent/0.1", "Earlier core default remains .1")
        # The completed artifact is staged by the real export before the
        # caller's whole-response value cap prevents publication.
        table = read(run.frozen / "agent/request-workflows.json")
        workflow = next(row for row in table["scenarios"] if row["id"] == "A08")
        run.steps("A08", workflow["steps"])
        from ontokin.json_limits import measure_json
        control_entries = measure_json(run.responses["A08.export"])["entries"]
        export_request = {**run.requests["A08.export"], "request_id": run.namespace+"-staged-response-limit",
                          "budgets": {"max_value_entries": control_entries-1}}
        before = retained(run.service)
        observed = []
        original = run.service._check_task_response
        def observe(task):
            if task.request["request_id"] == export_request["request_id"] and task.artifact is not None:
                observed.append({"bytes": len(task.artifact[0]), "sha256": digest(task.artifact[0]),
                                 "artifact_id": task.artifact[2], "response_status": task.response["status"]})
            return original(task)
        run.service._check_task_response = observe
        try:
            response = run.exchange(export_request, expected_status="failed", expected_code="OKL-E-RESOURCE")
        finally:
            run.service._check_task_response = original
        write(run.directory / "staged-response-limit.json", {"observed_real_artifacts": observed,
            "successful_control_value_entries": control_entries, "caller_max_value_entries": control_entries-1,
            "response": response, "before": before, "after": retained(run.service)})
        run.check(bool(observed), "Actual prepared artifact existed before the real final response cap")
        run.check(retained(run.service) == before, "Late response cap publishes no new artifact/run/source effects")
        result["status"] = "passed"
    except BaseException as error:
        result.update(status="failed", error=type(error).__name__+": "+str(error), traceback=traceback.format_exc())
    finally:
        if old is not None:
            old.close()
        try:
            run.finish()
        except BaseException as error:
            result.update(status="failed", closing_error=repr(error), closing_traceback=traceback.format_exc())
        result.update(checks=run.checks, exchanges=run.exchanges)
        write(args.output / "summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--schema-root", type=Path, default=ROOT)
    args = parser.parse_args()
    args.output = args.output.absolute()
    args.output.mkdir()
    result = execute(args)
    print(json.dumps({k: value for k, value in result.items() if "traceback" not in k}), flush=True)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
