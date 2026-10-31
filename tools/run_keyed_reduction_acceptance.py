#!/usr/bin/env python3
"""Retain actual C082 source, Agent and supplied-byte observations.

The independently frozen expectations and independent readers are separate.
This producer never turns its own success flags into release acceptance.
Run against a new evidence directory outside the checkout. Synchronization and
publication fault injection are recorded and confined to new local stores.
"""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.run_texture_acceptance import (
    Acceptance as TextureAcceptance, codes, error_record, git, inventory, save)
from tools.texture_reference import bundle_identity, canonical, digest, sha
from tools.keyed_reduction_reference import (
    FREEZE_COMMIT, FREEZE_SHA256, PROFILE, PROTOCOL, TARGET,
    case_payload, load_fixtures)


OPTIONS = {"fps": 4, "end": "1", "helpers": False}
DEFAULT_POLICY = {"max_operations": 100000, "max_elapsed_ms": 30000}
HIGH_POLICY = {"max_operations": 400000, "max_elapsed_ms": 80000}
PANEL_ID = ["panel-task", "demo", "first", "panels", "left"]


class SourceContext:
    """Fresh direct-call host context; no historical receipt grants authority."""

    def __init__(self, policy, profile, caller_caps=None):
        from ontokin.execution_budget import SharedExecutionBudget
        self.execution_budget = SharedExecutionBudget(policy=policy, caller_caps=caller_caps)
        self.profile = profile

    def __call__(self):
        self.execution_budget.tick()

    def admit(self, source):
        from ontokin.execution_budget import admit_entry_budget
        if self.execution_budget.resolved is None:
            admit_entry_budget(source.entry, self.execution_budget, profile=self.profile)
        elif self.execution_budget.admitted_entry_revision != source.entry.revision:
            raise ValueError("One source observation cannot reauthorize a different entry")


class Acceptance(TextureAcceptance):
    """Reuse only binding-neutral recording helpers from the C080 producer."""

    def __init__(self, fixtures, output):
        from ontokin.budget_runtime import execute_keyed_reduction_export, execute_keyed_transform_export
        from ontokin.execution_budget import HostPolicy
        from ontokin.keyed_reduction_agent import KeyedReductionAgentService
        from ontokin.keyed_reduction_program_runtime import KeyedReductionProgramRuntime
        from ontokin.scene import ExportOptions
        from ontokin.texture_bundle import load_texture_file_manifest
        from ontokin.keyed_transform_program_runtime import KeyedTransformProgramRuntime
        self.load_files = load_texture_file_manifest
        self.execute, self.execute_control = execute_keyed_reduction_export, execute_keyed_transform_export
        self.Runtime, self.ControlRuntime = KeyedReductionProgramRuntime, KeyedTransformProgramRuntime
        self.HostPolicy, self.ExportOptions = HostPolicy, ExportOptions
        self.Service = KeyedReductionAgentService
        self.fixtures, self.output = fixtures, output
        self.fixture_root = Path(fixtures["root"])
        self.serial, self.transcript, self.service = 0, [], None
        self.project, self.scenario = "", None
        self.summary = {"schema_version": "ontokin.c082-actual-evidence/0.1",
            "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
            "command": [sys.executable, *sys.argv], "python": sys.version,
            "platform": platform.platform(), "frozen_input_commit": FREEZE_COMMIT,
            "frozen_manifest_sha256": FREEZE_SHA256,
            "git": {"commit": git(["rev-parse", "HEAD"]),
                    "tree": git(["rev-parse", "HEAD^{tree}"]),
                    "status": git(["status", "--porcelain"])},
            "profile": PROFILE, "target_contract": TARGET, "agent_contract": PROTOCOL,
            "cases": [], "controls": [], "workflows": [], "agent_artifacts": [],
            "hostile_glbs": [], "supplied_glb_positive_controls": [],
            "additional_stores": [], "snapshots": [], "failures": [],
            "reopens": [],
            "release_acceptance": False,
            "independent_verification": "not_run_by_this_producer",
            "destination_verification": "not_run_by_this_producer"}
        self.options = ExportOptions(**OPTIONS)
        self.schema_validators = self.schemas()

    def schemas(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        paths = sorted((ROOT / "docs/language-design/agent-v0.15").glob("*.schema.json"))
        if not paths:
            raise RuntimeError("Actual Agent/0.15 schemas are required")
        resources = {}
        for path in sorted((ROOT / "docs/language-design").rglob("*.schema.json")):
            value = json.loads(path.read_bytes())
            if "$id" in value:
                resources[value["$id"]] = Resource.from_contents(value)
        registry = Registry().with_resources(resources.items())
        result, records = {}, []
        for path in paths:
            value = json.loads(path.read_bytes())
            Draft202012Validator.check_schema(value)
            result[path.name] = Draft202012Validator(value, registry=registry)
            records.append({"path": path.relative_to(ROOT).as_posix(),
                            "sha256": sha(path.read_bytes()), "id": value.get("$id")})
        save(self.output / "schema-inventory.json", {"schemas": records,
             "jsonschema_version": importlib.metadata.version("jsonschema"),
             "referencing_version": importlib.metadata.version("referencing")})
        return result

    def payload(self, name):
        return case_payload(self.fixtures, self.fixtures["cases"][name])

    def source_observation(self, source, case, prefix, *, control=False):
        # The frozen older-importer refusal is intentionally authored as .14.
        # Its actual entry binding must reach the lexical import check; forcing
        # a .15 header would observe a different refusal before that test.
        legacy = control or source.entry.raw.lstrip().startswith(b'ontokin "0.14";')
        profile = "keyed-transform-0.1" if legacy else PROFILE
        runtime = self.ControlRuntime() if legacy else self.Runtime()
        policy = self.HostPolicy(**case["host_policy"])
        context = SourceContext(policy, profile)
        result = runtime.validate_revision(source, level="represented", check=context)
        receipt = {"schema_version": "ontokin.c082-source-observation/0.1",
            "public_api": type(runtime).__name__ + ".validate_revision",
            "profile": profile, "program_revision": source.program_revision,
            "requested_level": "represented", "result": result,
            "execution_budget": context.execution_budget.report(status=result["outcome"])}
        save(self.output / (prefix + ".receipt.json"), receipt)
        return result

    def inspect_source(self, source, case, prefix, *, control=False):
        profile = "keyed-transform-0.1" if control else PROFILE
        runtime = self.ControlRuntime() if control else self.Runtime()
        context = SourceContext(self.HostPolicy(**case["host_policy"]), profile)
        probe = case.get("probe")
        selector = {"path": probe["object_path"]} if probe else {"kind": "object"}
        query = {"selector": selector, "fields": ["identity", "source", "values", "geometry", "matter"],
                 "limit": 1000}
        result = runtime.inspect_revision(source, check=context, **query)
        path = prefix + ".inspection.json"
        save(self.output / path, result)
        save(self.output / (prefix + ".inspection-receipt.json"), {
            "schema_version": "ontokin.c082-source-inspection-observation/0.1",
            "public_api": type(runtime).__name__ + ".inspect_revision",
            "profile": profile, "program_revision": source.program_revision,
            "query": query, "execution_budget": context.execution_budget.report(status=result["outcome"])})
        self.check(result["outcome"] == "valid" and result.get("items"),
                   case["name"] + " must retain actual public value inspection: " + str(codes(result)))
        return path

    def run_sources(self):
        for case in self.fixtures["expected"]["cases"]:
            record = {key: case[key] for key in ("id", "name", "source", "file_manifest",
                "expected_outcome", "expected_code", "expected_stage", "host_policy")}
            prefix = "sources/" + case["name"]
            try:
                source = self.load_files(self.fixture_root / case["file_manifest"])
                record.update(program_revision=source.program_revision, receipt=prefix + ".receipt.json",
                              delivered=False)
                self.check(source.program_revision == case["program_revision"], "Frozen source revision")
                if case["expected_stage"] == "delivered":
                    exported = self.execute(source, policy=self.HostPolicy(**case["host_policy"]), options=self.options)
                    result = exported.report
                    save(self.output / record["receipt"], result)
                    if exported.data is not None:
                        record.update(delivered=True, glb=prefix + ".glb",
                                      bytes=len(exported.data), sha256=sha(exported.data))
                        (self.output / record["glb"]).write_bytes(exported.data)
                    observed_valid = exported.data is not None
                else:
                    result = self.source_observation(source, case, prefix)
                    observed_valid = result["outcome"] == "valid"
                record["diagnostic_codes"] = codes(result)
                if case["expected_outcome"] == "valid":
                    self.check(observed_valid, case["name"] + " must achieve its frozen stage")
                    record["inspection"] = self.inspect_source(source, case, prefix)
                    record["inspection_receipt"] = prefix + ".inspection-receipt.json"
                    control_spec = case["explicit_c081_control"]
                    control = self.load_files(self.fixture_root / control_spec["file_manifest"])
                    self.check(control.program_revision == control_spec["program_revision"], "Frozen explicit .14 revision")
                    control_prefix = "controls/" + case["name"]
                    control_record = {"name": case["name"], "file_manifest": control_spec["file_manifest"],
                        "program_revision": control.program_revision, "receipt": control_prefix + ".receipt.json",
                        "host_policy": case["host_policy"]}
                    if case["expected_stage"] == "delivered":
                        exported_control = self.execute_control(control, policy=self.HostPolicy(**case["host_policy"]), options=self.options)
                        save(self.output / control_record["receipt"], exported_control.report)
                        self.check(exported_control.data is not None, case["name"] + " explicit .14 must deliver")
                        control_record.update(glb=control_prefix + ".glb", bytes=len(exported_control.data),
                                              sha256=sha(exported_control.data))
                        (self.output / control_record["glb"]).write_bytes(exported_control.data)
                        record["control"] = control_record["glb"]
                    else:
                        control_result = self.source_observation(control, case, control_prefix, control=True)
                        self.check(control_result["outcome"] == "valid", case["name"] + " explicit .14 must represent")
                    control_record["inspection"] = self.inspect_source(control, case, control_prefix, control=True)
                    control_record["inspection_receipt"] = control_prefix + ".inspection-receipt.json"
                    control_record["producer_status"] = "observed_as_expected"
                    self.summary["controls"].append(control_record)
                else:
                    self.check(not observed_valid, case["name"] + " must refuse")
                    self.check(case["expected_code"] in record["diagnostic_codes"],
                               case["name"] + " requires exact frozen diagnostic: " + str(record["diagnostic_codes"]))
                    if case["expected_code"] != "OKL-E-RESOURCE":
                        self.check("OKL-E-RESOURCE" not in record["diagnostic_codes"],
                                   "Budget exhaustion cannot substitute for a semantic refusal")
                record["producer_status"] = "observed_as_expected"
            except Exception as error:
                record.update(producer_status="failed", exception=error_record(error))
                self.summary["failures"].append({"scope": "source", "name": case["name"], "error": str(error)})
            self.summary["cases"].append(record)
            save(self.output / "summary.json", self.summary)

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": self.project,
                "request_id": f"c082-{self.serial:04}", "operation": operation, **fields}

    def create(self, name, *, level="constructed"):
        payload = self.payload(name)
        response = self.success("create", bundle=payload, expected_program_revision=None, requested_level=level)
        self.check(response["accepted_program_revision"] == self.fixtures["cases"][name]["program_revision"],
                   "Actual create must preserve the frozen source/asset revision")
        return payload

    def repair_fields(self, before, after):
        old, new = "scale = 1[m];", "scale = 1.5[m];"
        raw = before["entry"]["source"].encode()
        offset = raw.index(old.encode())
        self.check(raw.count(old.encode()) == 1, "The frozen first occurrence repair is unambiguous")
        patched = raw[:offset] + new.encode() + raw[offset + len(old.encode()):]
        self.check(patched == after["entry"]["source"].encode(), "Exact small repair produces the frozen candidate")
        self.check(before["modules"] == after["modules"] and before["assets"] == after["assets"],
                   "The frozen repair preserves pinned library and PNG bytes")
        return {"expected_program_revision": bundle_identity(before)[0], "requested_level": "constructed",
            "patches": [{"source_id": "entry", "source_revision": digest(raw),
                "element_id": ["sources", "entry"], "start_byte": offset, "end_byte": offset + len(old.encode()),
                "expected_text": old, "replacement": new}]}

    def retrieve_artifact(self, response, name):
        result, chunks, offset = response["result"], [], 0
        while offset < result["total_bytes"]:
            part = self.success("artifact", artifact_id=result["artifact_id"], offset=offset, max_bytes=65536)["result"]
            raw = base64.b64decode(part["data_base64"], validate=True)
            self.check(raw and part["offset"] == offset and part["program_revision"] == response["program_revision"],
                       "Artifact slices progress under the actual revision")
            chunks.append(raw)
            offset += len(raw)
        raw = b"".join(chunks)
        self.check(len(raw) == result["total_bytes"] and digest(raw) == result["sha256"], "Complete actual artifact hash")
        path = "agent/" + self.project + "-" + name + ".glb"
        (self.output / path).write_bytes(raw)
        self.summary["agent_artifacts"].append({"project_id": self.project, "name": name, "glb": path,
            "sha256": sha(raw), "bytes": len(raw), "program_revision": response["program_revision"],
            "artifact_id": result["artifact_id"], "export_request_id": response["request_id"]})
        return raw

    def export(self, name, payload):
        request = self.request("export", program_revision=bundle_identity(payload)[0], destination=TARGET, options=OPTIONS)
        response = self.call(request)
        self.check(response["status"] == "succeeded", "Actual .15 export must succeed: " + str(codes(response)))
        self.last_export_request = request
        self.retrieve_artifact(response, name)
        return response

    def inspect_panels(self, revision):
        return self.success("inspect", program_revision=revision, selector={"kind": "object"},
            fields=["identity", "source", "values", "geometry", "matter", "support"], limit=100)

    def evaluate(self, revision):
        return self.success("evaluate", program_revision=revision, run_id=None, until_seconds="1")

    def reopen(self, policy=None):
        previous = self.service
        directory = previous.database_path.parent
        record = {"workflow": self.scenario, "project_id": self.project,
            "store_path": previous.database_path.relative_to(self.output).as_posix(),
            "old_session_owner": previous._store.owner,
            "old_host_policy": previous.host_policy.ceilings,
            "old_implementation": previous.implementation,
            "before": self.state(), "after_exchange": len(self.transcript)}
        previous.close()
        self.service = self.Service(directory, host_policy=self.HostPolicy(**(policy or DEFAULT_POLICY)))
        record.update(new_session_owner=self.service._store.owner,
            new_host_policy=self.service.host_policy.ceilings,
            new_implementation=self.service.implementation, after=self.state())
        self.check(record["old_session_owner"] != record["new_session_owner"],
                   "Reopen must create a distinct durable service session")
        self.summary["reopens"].append(record)
        save(self.output / "agent/reopen-log.json", self.summary["reopens"])

    def run_one_workflow(self, spec):
        name, expected = spec["name"], spec["expected"]
        if name == "two-occurrence-repair":
            self.success("discover", profile=PROFILE, limit=1000)
            before = self.create(spec["base"])
            revision = bundle_identity(before)[0]
            self.success("discover", profile=PROFILE, program_revision=revision, limit=1000)
            self.success("validate", program_revision=revision, requested_level="constructed")
            self.inspect_panels(revision)
            self.success("surface.mesh_page", program_revision=revision, element_id=PANEL_ID, count=256)
            self.evaluate(revision)
            self.export("before", before)
            after = self.payload(spec["candidate"])
            self.success("edit", **self.repair_fields(before, after))
            revised = bundle_identity(after)[0]
            self.check(self.state()["accepted_program_revision"] == revised, "Repair accepts exact frozen candidate")
            self.inspect_panels(revised)
            self.success("surface.mesh_page", program_revision=revised, element_id=PANEL_ID, count=256)
            self.evaluate(revised)
            self.export("after", after)
        elif name == "invalid-candidate-rollback":
            before = self.create(spec["base"])
            state = self.state()
            response = self.refuse(expected["expected_code"], "edit",
                **self.edit_fields(before, self.payload(spec["candidate"])))
            self.success("status", target_request_id=response["request_id"])
            self.accepted_same(state, all_effects=True)
            self.inspect_panels(bundle_identity(before)[0])
            after = self.payload("panel-task-repaired")
            self.success("edit", **self.repair_fields(before, after))
            repaired_state = self.state()
            self.refuse("OKL-E-REVISION", "edit", **self.repair_fields(before, after))
            self.accepted_same(repaired_state, all_effects=True)
        elif name == "stale-surface-and-element-cursors":
            before = self.create(spec["base"])
            revision = bundle_identity(before)[0]
            queries = [("inspect", {"selector": {"kind": "object"}, "fields": ["identity", "source"], "limit": 1}),
                       ("surface.mesh_page", {"element_id": PANEL_ID, "count": 1})]
            cursors = []
            for operation, query in queries:
                response = self.success(operation, program_revision=revision, **query)
                self.check(response["next_cursor"], "Actual ordinary/mesh pagination must yield a cursor")
                cursors.append((operation, query, response["next_cursor"]))
            self.reopen()
            for operation, query, cursor in cursors:
                self.success(operation, program_revision=revision, cursor=cursor, **query)
            after = self.payload(spec["candidate"])
            self.success("edit", **self.repair_fields(before, after))
            state = self.state()
            for operation, query, cursor in cursors:
                self.refuse("OKL-E-REVISION", operation, program_revision=bundle_identity(after)[0], cursor=cursor, **query)
            self.accepted_same(state, all_effects=True)
        elif name == "reopen-and-request-identity":
            payload = self.payload(spec["base"])
            request = self.request("create", bundle=payload, expected_program_revision=None, requested_level="constructed")
            response = self.call(request)
            self.check(response["status"] == "succeeded", "Original durable create")
            self.success("validate", program_revision=bundle_identity(payload)[0], requested_level="constructed")
            exported = self.export("before-reopen", payload)
            export_request = copy.deepcopy(self.last_export_request)
            state = self.state()
            self.reopen()
            self.check(self.call(request) == response, "Exact create retry returns historical receipt")
            self.check(self.call(export_request) == exported, "Exact export retry preserves actual artifact identity")
            self.success("status", target_request_id=export_request["request_id"])
            self.retrieve_artifact(exported, "after-reopen")
            changed = copy.deepcopy(request)
            changed["requested_level"] = "represented"
            refusal = self.call(changed)
            self.check(refusal["status"] == "rejected" and "OKL-E-REQUEST-ID" in codes(refusal), "Changed retry payload must refuse")
            self.accepted_same(state, all_effects=True)
        elif name == "current-host-authority":
            self.service.host_policy = self.HostPolicy(**HIGH_POLICY)
            payload = self.create(spec["base"])
            revision = bundle_identity(payload)[0]
            self.success("validate", program_revision=revision, requested_level="constructed")
            self.inspect_panels(revision)
            self.evaluate(revision)
            exported = self.export("authorized", payload)
            state = self.state()
            self.reopen(DEFAULT_POLICY)
            calls = [
                ("validate", {"program_revision": revision, "requested_level": "constructed"}),
                ("inspect", {"program_revision": revision, "selector": {"kind": "object"}, "fields": ["identity"], "limit": 100}),
                ("surface.mesh_page", {"program_revision": revision, "element_id": PANEL_ID, "count": 1}),
                ("evaluate", {"program_revision": revision, "run_id": None, "until_seconds": "1"}),
                ("export", {"program_revision": revision, "destination": TARGET, "options": OPTIONS}),
                ("artifact", {"artifact_id": exported["result"]["artifact_id"], "offset": 0, "max_bytes": 1}),
                ("inspect", {"program_revision": revision, "selector": {"element_id": ["assets", "label"]},
                    "fields": ["source"], "limit": 1, "asset_slice": {"offset": 0, "max_bytes": 1}})]
            for operation, query in calls:
                self.refuse("OKL-E-RESOURCE", operation, **query)
                self.accepted_same(state, all_effects=True)
        elif name == "caller-caps-and-output-exhaustion":
            payload = self.create(spec["base"])
            revision = bundle_identity(payload)[0]
            exported = self.export("complete-before-caps", payload)
            state = self.state()
            self.refuse("OKL-E-RESOURCE", "validate", program_revision=revision,
                        requested_level="represented", budgets={"max_operations": 1})
            self.refuse("OKL-E-SAMPLE", "inspect", program_revision=revision,
                selector={"kind": "object"}, fields=["identity"], limit=2, budgets={"max_result_items": 1})
            self.refuse("OKL-E-RESOURCE", "inspect", program_revision=revision,
                selector={"path": "first"}, fields=["values"], limit=1, budgets={"max_value_entries": 1})
            self.refuse("OKL-E-RESOURCE", "surface.mesh_page", program_revision=revision,
                element_id=PANEL_ID, count=1, budgets={"max_operations": 1})
            self.refuse("OKL-E-RESOURCE", "export", program_revision=revision,
                destination=TARGET, options=OPTIONS, budgets={"max_operations": 1})
            self.refuse("OKL-E-RESOURCE", "artifact", artifact_id=exported["result"]["artifact_id"],
                offset=0, max_bytes=1, budgets={"max_operations": 1})
            self.refuse("OKL-E-RESOURCE", "validate", program_revision=revision,
                requested_level="represented", budgets={"max_operations": 100001})
            self.accepted_same(state, all_effects=True)
            original = self.project
            self.project += "-maximum"
            maximum = self.create(spec["secondary"], level="represented")
            maximum_state = self.state()
            self.refuse("OKL-E-RESOURCE", "inspect", program_revision=bundle_identity(maximum)[0],
                selector={"path": "shape"}, fields=["values"], limit=1, budgets={"max_value_entries": 1})
            self.accepted_same(maximum_state, all_effects=True)
            self.project = original
        elif name == "cancel-during-reduction":
            self.cancel_during_reduction(spec["base"])
        elif name == "interrupted-artifact-publication":
            self.interrupt_publication()
        elif name == "exact-attachment-slices":
            payload = self.create(spec["base"])
            revision = bundle_identity(payload)[0]
            expected_bytes = base64.b64decode(payload["assets"][0]["data_base64"], validate=True)
            actual, offset = b"", 0
            query = {"program_revision": revision, "selector": {"element_id": ["assets", "label"]},
                     "fields": ["identity", "source"], "limit": 1}
            while offset < len(expected_bytes):
                result = self.success("inspect", **query, asset_slice={"offset": offset, "max_bytes": 17})["result"]
                part = base64.b64decode(result["data_base64"], validate=True)
                self.check(part and result["program_revision"] == revision and result["sha256"] == digest(expected_bytes), "Exact asset slice identities")
                actual += part
                offset += len(part)
            eof = self.success("inspect", **query, asset_slice={"offset": offset, "max_bytes": 17})["result"]
            self.check(actual == expected_bytes and eof["data_base64"] == "" and eof["complete"]
                       and eof["next_offset"] is None, "Exact complete original PNG and empty EOF")
            self.refuse("OKA-E-REQUEST", "inspect", **query, asset_slice={"offset": offset + 1, "max_bytes": 1})
            (self.output / "agent/retrieved-label.png").write_bytes(actual)
        elif name == "reduction-and-explicit-c081-delivery":
            payload = self.create(spec["base"])
            revision = bundle_identity(payload)[0]
            self.success("validate", program_revision=revision, requested_level="constructed")
            self.inspect_panels(revision)
            self.evaluate(revision)
            self.export("identity", payload)
        else:
            raise AssertionError("No executable frozen C082 workflow: " + name)

    def cancel_during_reduction(self, name):
        payload = self.create(name, level="represented")
        state = self.state()
        request = self.request("validate", program_revision=bundle_identity(payload)[0], requested_level="represented")
        reached, release = threading.Event(), threading.Event()
        worker_errors, checkpoints = [], []
        original = self.service._make_check
        def make_check(task):
            check = original(task)
            original_poll = check.execution_budget.check
            def gated():
                if (task.request["request_id"] == request["request_id"]
                        and check.execution_budget.stage == "keyed_reduction_iteration" and not reached.is_set()):
                    checkpoints.append({"stage": check.execution_budget.stage,
                        "consumed_operations": check.execution_budget.operations,
                        "program_revision": check.program_revision, "request_id": task.request["request_id"]})
                    reached.set()
                    if not release.wait(30):
                        raise TimeoutError("Actual reduction cancellation barrier timed out")
                    check.last_poll = 0.0
                return original_poll()
            check.execution_budget.check = gated
            return check
        self.service._make_check = make_check
        worker = None
        try:
            queued = self.call(request, wait=False)
            self.check(queued["status"] == "queued", "Actual reduction validation is queued")
            def work():
                try:
                    self.service.work_next()
                except BaseException as error:
                    worker_errors.append(error_record(error))
            worker = threading.Thread(target=work, name="c082-cancel-reduction")
            worker.start()
            self.check(reached.wait(30), "Actual nonempty reduction iteration must be reached before cancellation")
            self.success("cancel", target_request_id=request["request_id"])
            release.set()
            worker.join(30)
            self.check(not worker.is_alive() and not worker_errors, "Cancelled reduction worker terminates cleanly")
            terminal = self.call(request)
            self.check(terminal["status"] == "cancelled", "Original in-progress request is cancelled")
            self.success("status", target_request_id=request["request_id"])
            self.accepted_same(state, all_effects=True)
        finally:
            release.set()
            if worker is not None:
                worker.join(30)
            self.service._make_check = original
            save(self.output / "agent/cancellation-barrier.json", {
                "actual_reduction_checkpoint_reached": reached.is_set(), "request_id": request["request_id"],
                "checkpoints": checkpoints, "worker_errors": worker_errors,
                "intervention": "Pause the actual dynamic-reduction selection charge after input/static checks, send real protocol cancel, resume the original poll."})

    def interrupt_publication(self):
        payload = self.create("panel-task")
        revision, state = bundle_identity(payload)[0], self.state()
        original, prepared = self.service._persist_task_metadata, []
        class PublicationInterruption(BaseException):
            pass
        def fail_after_prepare(db, task):
            if task.artifact is not None:
                raw, report, artifact_id = task.artifact
                prepared.append({"artifact_id": artifact_id, "bytes": len(raw), "sha256": sha(raw),
                    "request_id": task.request["request_id"], "glb": "agent/interrupted-prepared-only.glb",
                    "sqlite_transaction_active": db.in_transaction,
                    "store_path": self.service.database_path.relative_to(self.output).as_posix()})
                (self.output / "agent/interrupted-prepared-only.glb").write_bytes(raw)
                raise PublicationInterruption("Deliberate BaseException inside the actual uncommitted SQLite publication transaction")
            return original(db, task)
        request = self.request("export", program_revision=revision, destination=TARGET, options=OPTIONS)
        self.service._persist_task_metadata = fail_after_prepare
        try:
            self.call(request)
        except PublicationInterruption:
            pass
        finally:
            self.service._persist_task_metadata = original
        self.check(len(prepared) == 1, "Real GLB preparation must precede publication interruption")
        self.check(prepared[0]["sqlite_transaction_active"], "Interruption must occur inside real publication transaction")
        self.reopen()
        status = self.success("status", target_request_id=request["request_id"])
        self.check(status["result"]["target_status"] in ("unknown_outcome", "cancelled", "failed"),
                   "Interrupted publication cannot claim a successful artifact")
        self.refuse("OKA-E-ARTIFACT", "artifact", artifact_id=prepared[0]["artifact_id"], offset=0, max_bytes=1)
        self.accepted_same(state, all_effects=True)
        save(self.output / "agent/publication-interruption.json", {"prepared_only": prepared,
            "status_response": status, "before": state, "after": self.state(),
            "intervention": "Injected BaseException at real publication after verified GLB preparation in a new isolated store; reopened and queried actual durable status."})
        self.export("new-id-retry", payload)

    def backup_store(self, label):
        backup = self.output / ("agent/" + label + "-store.sqlite3")
        with self.service._store.connection() as source, sqlite3.connect(backup) as destination:
            source.backup(destination)
            snapshots = source.execute("SELECT project_id,revision,raw FROM sources ORDER BY project_id,revision").fetchall()
        for row in snapshots:
            raw = bytes(row["raw"])
            path = "agent/snapshots/" + label + "/" + row["project_id"] + "/" + row["revision"].split(":", 1)[1] + ".json"
            destination = self.output / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
            self.summary["snapshots"].append({"store": label, "project_id": row["project_id"],
                "program_revision": row["revision"], "path": path, "sha256": sha(raw), "bytes": len(raw)})
        return {"path": backup.relative_to(self.output).as_posix(),
                "sha256": sha(backup.read_bytes()), "bytes": backup.stat().st_size}

    def run_agent(self):
        self.service = self.Service(self.output / "live-store/main", host_policy=self.HostPolicy())
        for spec in self.fixtures["workflows"]["workflows"]:
            self.scenario, self.project = spec["id"], "c082-" + spec["id"].lower()
            self.service.host_policy = self.HostPolicy()
            held_service = None
            if spec["id"] == "A08":
                held_service = self.service
                self.service = self.Service(self.output / "live-store/interruption", host_policy=self.HostPolicy())
            record = {"id": spec["id"], "name": spec["name"], "project_id": self.project,
                      "first_exchange": len(self.transcript) + 1}
            try:
                self.run_one_workflow(spec)
                record["status"] = "observed_as_expected"
            except Exception as error:
                record.update(status="failed", exception=error_record(error))
                self.summary["failures"].append({"scope": "workflow", "name": spec["name"], "error": str(error)})
            record.update(last_exchange=len(self.transcript), retained_state=self.state())
            self.summary["workflows"].append(record)
            if held_service is not None:
                self.summary["additional_stores"].append({"workflow": "A08", **self.backup_store("interruption")})
                self.service.close()
                self.service = held_service
            save(self.output / "summary.json", self.summary)
        self.scenario, self.project = "operation-coverage", "c082-coverage"
        payload = self.create("panel-task")
        self.success("reset", program_revision=bundle_identity(payload)[0])
        self.summary["operation_inventory"] = sorted({r["request"]["operation"] for r in self.transcript})
        self.check(len(self.summary["operation_inventory"]) == 12, "All twelve real Agent operations are retained")
        save(self.output / "agent/transcript.json", self.transcript)
        with (self.output / "agent/transcript.jsonl").open("w", encoding="utf-8") as stream:
            for row in self.transcript:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        self.summary["store"] = self.backup_store("durable")
        self.service.close()
        self.service = None

    def run_supplied_glb_probes(self):
        from tools.keyed_reduction_adversaries import build_mutations
        from ontokin.construction import compile_construction
        from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
        from ontokin.gltf import validate_export
        from ontokin.reach_numeric import ReachExecutionWork
        directory = self.output / "hostile-glbs"
        directory.mkdir(exist_ok=True)
        def validate(raw, case):
            source = self.load_files(self.fixture_root / case["file_manifest"])
            ledger = SharedExecutionBudget(policy=self.HostPolicy(**case["host_policy"]))
            admit_entry_budget(source.entry, ledger, profile=PROFILE)
            compiler = compile_construction(source, level="evaluated", execution_budget=ledger)
            report = validate_export(raw, compiler.model, options=self.options, target_contract=TARGET,
                                     work=ReachExecutionWork(execution_budget=ledger))
            return {"report": report, "execution_budget": ledger.report(status="valid")}
        for source_record in self.summary["cases"]:
            if source_record["name"] != "panel-identity" or "glb" not in source_record:
                continue
            case = self.fixtures["cases"][source_record["name"]]
            raw = (self.output / source_record["glb"]).read_bytes()
            positive = {"case": case["name"], "sha256": sha(raw)}
            try:
                positive.update(status="observed_as_expected", validation=validate(raw, case))
            except Exception as error:
                positive.update(status="failed", exception=error_record(error))
                self.summary["failures"].append({"scope": "supplied_glb_positive", "name": case["name"], "error": str(error)})
            self.summary["supplied_glb_positive_controls"].append(positive)
            for mutation in build_mutations(raw, case):
                mutation = dict(mutation)
                data = mutation.pop("data")
                mutation["path"] = "hostile-glbs/" + case["name"] + "-" + mutation["id"] + ".glb"
                (self.output / mutation["path"]).write_bytes(data)
                try:
                    observation = validate(data, case)
                except Exception as error:
                    mutation["exception"] = error_record(error)
                    mutation["diagnostic_codes"] = codes(mutation["exception"])
                    mutation["actual_export_code"] = mutation["exception"].get("details", {}).get("export_code")
                    mutation["status"] = "observed_as_expected" if mutation["diagnostic_codes"] else "failed"
                else:
                    mutation.update(status="failed", unexpected_acceptance=True, validation=observation)
                if mutation["status"] == "failed":
                    self.summary["failures"].append({"scope": "hostile_glb", "name": mutation["id"], "error": mutation})
                self.summary["hostile_glbs"].append(mutation)
        save(directory / "production-observations.json", {
            "positive_controls": self.summary["supplied_glb_positive_controls"],
            "hostile_controls": self.summary["hostile_glbs"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-reduction")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--section", choices=("all", "sources", "agent"), default="all",
                        help="A partial diagnostic run remains labelled with its selected section")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        parser.error("--output must be a new directory outside the checkout")
    fixtures = load_fixtures(args.fixtures)
    output.mkdir(parents=True)
    for name in ("sources", "controls", "agent"):
        (output / name).mkdir()
    run = None
    try:
        run = Acceptance(fixtures, output)
        run.summary["selected_section"] = args.section
        if args.section in ("all", "sources"):
            run.run_sources()
        if args.section == "all":
            run.run_supplied_glb_probes()
        if args.section in ("all", "agent"):
            run.run_agent()
        run.summary["status"] = "failed" if run.summary["failures"] else "produced_as_expected"
    except BaseException as error:
        if run is None:
            save(output / "initialization-failure.json", error_record(error))
            raise
        run.summary["status"] = "failed"
        run.summary["failures"].append({"scope": "driver", "error": error_record(error)})
    finally:
        if run is not None:
            if run.service is not None:
                run.service.close()
            run.summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
            save(output / "summary.json", run.summary)
            save(output / "inventory.json", inventory(output))
    print(json.dumps({"status": run.summary["status"], "source_cases": len(run.summary["cases"]),
                      "failures": len(run.summary["failures"]), "output": str(output)}))
    return 0 if run.summary["status"] == "produced_as_expected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
