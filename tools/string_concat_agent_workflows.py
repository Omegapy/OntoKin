#!/usr/bin/env python3
"""Actual C087 Agent lifecycle workflows, isolated from independent readers.

Derived from the retained C085 lifecycle recorder. These methods invoke the
actual versioned service and preserve requests, responses and SQLite snapshots.
All finite expected sources were independently frozen before implementation.
Synchronization and publication faults act only on fresh local test stores.
"""
from __future__ import annotations

import base64
import copy
import json
import sqlite3
import threading
import time

from tools.run_texture_acceptance import codes, error_record, save
from tools.texture_reference import bundle_identity, digest, sha
from tools.string_concat_reference import PROFILE, PROTOCOL, TARGET

OPTIONS = {"fps": 4, "end": "1", "helpers": False}
DEFAULT_POLICY = {"max_operations": 100000, "max_elapsed_ms": 30000}
HIGH_POLICY = {"max_operations": 400000, "max_elapsed_ms": 80000}
PANEL_ID = ["panel-task", "demo", "sibling", "panels", "back.right"]


class StringConcatAgentWorkflows:
    """Mixin over the common recorder; supplies all ten frozen actual workflows."""

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": self.project,
                "request_id": f"c087-{self.serial:04}", "operation": operation, **fields}

    def create(self, name, *, level="constructed"):
        payload = self.payload(name)
        response = self.success("create", bundle=payload, expected_program_revision=None, requested_level=level)
        self.check(response["accepted_program_revision"] == self.fixtures["cases"][name]["program_revision"],
                   "Actual create must preserve the frozen source/asset revision")
        return payload

    def repair_fields(self, before, after):
        before_revision, after_revision = bundle_identity(before)[0], bundle_identity(after)[0]
        candidates = [edit for edit in self.fixtures["agent_expected"]["source_edits"]
            if edit["patches"] and edit["patches"][0]["before_revision"] == before_revision
            and edit["patches"][0]["after_revision"] == after_revision]
        self.check(len(candidates) == 1, "Exactly one frozen source transition must match")
        raw = before["entry"]["source"].encode()
        patches = []
        for item in candidates[0]["patches"]:
            patch = {key: item[key] for key in ("source_id", "source_revision", "start_byte", "end_byte", "expected_text", "replacement")}
            patch["element_id"] = ["sources", "entry"]
            self.check(raw[patch["start_byte"]:patch["end_byte"]] == patch["expected_text"].encode(), "Exact frozen original UTF-8 patch precondition")
            patches.append(patch)
        patched = raw
        for patch in reversed(patches):
            patched = patched[:patch["start_byte"]] + patch["replacement"].encode() + patched[patch["end_byte"]:]
        self.check(patched == after["entry"]["source"].encode(), "Frozen exact source transition")
        self.check(before["modules"] == after["modules"] and before["assets"] == after["assets"], "Pinned library and PNG unchanged")
        return {"expected_program_revision": before_revision, "requested_level": "constructed", "patches": patches}

    def retrieve_artifact(self, response, name):
        result, chunks, offset = response["result"], [], 0
        first_exchange = len(self.transcript) + 1
        while offset < result["total_bytes"]:
            part = self.success("artifact", artifact_id=result["artifact_id"], offset=offset, max_bytes=65536)["result"]
            raw = base64.b64decode(part["data_base64"], validate=True)
            self.check(raw and part["offset"] == offset and part["program_revision"] == response["program_revision"],
                       "Artifact slices progress under the actual revision")
            chunks.append(raw)
            offset += len(raw)
        raw = b"".join(chunks)
        self.check(len(raw) == result["total_bytes"] and digest(raw) == result["sha256"], "Complete actual artifact hash")
        eof = self.success("artifact", artifact_id=result["artifact_id"], offset=offset, max_bytes=1)["result"]
        self.check(eof["data_base64"] == "" and eof["next_offset"] is None
                   and eof["offset"] == len(raw) and eof["total_bytes"] == len(raw)
                   and eof["sha256"] == digest(raw), "Exact empty artifact EOF preserves the complete-byte identity")
        self.refuse("OKA-E-ARTIFACT", "artifact", artifact_id=result["artifact_id"],
                    offset=offset + 1, max_bytes=1)
        path = "agent/" + self.project + "-" + name + ".glb"
        (self.output / path).write_bytes(raw)
        self.summary["agent_artifacts"].append({"project_id": self.project, "name": name, "glb": path,
            "sha256": sha(raw), "bytes": len(raw), "program_revision": response["program_revision"],
            "artifact_id": result["artifact_id"], "export_request_id": response["request_id"],
            "retrieval_first_exchange": first_exchange, "retrieval_last_exchange": len(self.transcript)})
        return raw

    def export(self, name, payload):
        request = self.request("export", program_revision=bundle_identity(payload)[0], destination=TARGET, options=OPTIONS)
        response = self.call(request)
        self.check(response["status"] == "succeeded", "Actual .20 export must succeed: " + str(codes(response)))
        self.last_export_request = request
        self.retrieve_artifact(response, name)
        return response

    def inspect_panels(self, revision):
        response = self.success("inspect", program_revision=revision, selector={"kind": "object"},
            fields=["identity", "source", "values", "geometry", "matter", "support"], limit=100)
        for owner in ("first", "sibling"):
            self.success("inspect", program_revision=revision,
                selector={"kind": "object", "element_id": ["panel-task", "demo", owner]},
                fields=["values"], limit=1)
        return response

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
        if name == "two-occurrence-computed-namespace-repair":
            # These identities are selected only from the published fixture,
            # before observing any candidate service response.
            before_keys = set(expected["before_generated_keys"]["first"])
            after_keys = set(expected["surviving_generated_keys"]["first"])
            removed, added = sorted(before_keys - after_keys), sorted(after_keys - before_keys)
            self.check(len(removed) == len(added) == 2,
                       "The frozen repair removes and adds exactly two first-occurrence keys")
            original_panel = [*expected["repair_occurrence"], "panels", removed[0]]
            renamed_panel = [*expected["repair_occurrence"], "panels", added[0]]
            self.success("discover", profile=PROFILE, limit=1000)
            before = self.create(spec["base"])
            revision = bundle_identity(before)[0]
            self.success("discover", profile=PROFILE, program_revision=revision, limit=1000)
            self.success("validate", program_revision=revision, requested_level="constructed")
            self.inspect_panels(revision)
            self.success("surface.mesh_page", program_revision=revision, element_id=PANEL_ID, count=256)
            self.success("surface.mesh_page", program_revision=revision, element_id=original_panel, count=256)
            old_run = self.evaluate(revision)
            old_export = self.export("before", before)
            old_bytes = (self.output / self.summary["agent_artifacts"][-1]["glb"]).read_bytes()
            after = self.payload(spec["candidate"])
            self.success("edit", **self.repair_fields(before, after))
            revised = bundle_identity(after)[0]
            self.check(self.state()["accepted_program_revision"] == revised, "Repair accepts exact frozen candidate")
            self.inspect_panels(revised)
            self.success("surface.mesh_page", program_revision=revised, element_id=PANEL_ID, count=256)
            self.success("surface.mesh_page", program_revision=revised, element_id=renamed_panel, count=256)
            added_run = self.evaluate(revised)
            added_export = self.export("after", after)
            added_bytes = (self.output / self.summary["agent_artifacts"][-1]["glb"]).read_bytes()
            # Retain real old-revision queries after accepting the new head.
            # A prior run or artifact must not silently inherit new membership.
            pinned = self.success("inspect", program_revision=revision,
                run_id=old_run["run_id"], selector={"kind": "object"},
                fields=["identity", "source", "values", "state"], limit=100,
                time={"seconds": "1", "side": "after"})
            self.check(pinned["program_revision"] == revision and
                       pinned["run_id"] == old_run["run_id"],
                       "Old run inspection retains its original revision and run identity")
            retrieved = self.retrieve_artifact(old_export, "before-after-repair")
            self.check(retrieved == old_bytes, "Old artifact membership bytes remain unchanged after repair")
            removed = self.payload(expected["restore_again"]["candidate"])
            self.success("edit", **self.repair_fields(after, removed))
            removed_revision = bundle_identity(removed)[0]
            self.inspect_panels(removed_revision)
            self.success("surface.mesh_page", program_revision=removed_revision, element_id=PANEL_ID, count=256)
            self.success("surface.mesh_page", program_revision=removed_revision, element_id=original_panel, count=256)
            self.evaluate(removed_revision)
            self.export("restored", removed)
            added_pinned = self.success("inspect", program_revision=revised,
                run_id=added_run["run_id"], selector={"kind": "object"},
                fields=["identity", "source", "values", "state"], limit=100,
                time={"seconds": "1", "side": "after"})
            self.check(added_pinned["program_revision"] == revised and added_pinned["run_id"] == added_run["run_id"],
                       "Repaired membership remains pinned to their original revision and run after restoration")
            self.check(self.retrieve_artifact(added_export, "after-after-restoration") == added_bytes,
                       "Repaired-revision artifact remains byte-exact after restoration")
        elif name == "invalid-computed-prefix-candidate-rollback":
            before = self.create(spec["base"])
            state = self.state()
            response = self.refuse(expected["expected_code"], "edit",
                **self.edit_fields(before, self.payload(spec["candidate"])))
            self.check(any(d.get("code") == expected["expected_code"] and
                           d.get("details") == expected["diagnostic_details"]
                           for d in response.get("diagnostics", [])),
                       "Invalid computed-key refusal retains the frozen original-order collision details")
            self.success("status", target_request_id=response["request_id"])
            self.accepted_same(state, all_effects=True)
            self.inspect_panels(bundle_identity(before)[0])
            invalid = expected["invalid_geometry_candidate"]
            invalid_case = self.fixtures["cases"][invalid["name"]]
            invalid_fields = self.edit_fields(before, self.payload(invalid["name"]))
            if invalid_case["expected_code"] is None:
                # The frozen workflow requires the inherited geometry refusal
                # without prescribing a new exact diagnostic code.
                collision_response = self.call(self.request("edit", **invalid_fields))
                actual_codes = codes(collision_response)
                self.check(collision_response["status"] in ("failed", "rejected") and
                           actual_codes and "OKL-E-RESOURCE" not in actual_codes,
                           "Invalid-width candidate must produce an actual inherited refusal, not resource substitution")
            else:
                collision_response = self.refuse(invalid_case["expected_code"], "edit", **invalid_fields)
            self.success("status", target_request_id=collision_response["request_id"])
            self.accepted_same(state, all_effects=True)
            after = self.payload("panel-task-repaired")
            self.success("edit", **self.repair_fields(before, after))
            repaired_state = self.state()
            self.refuse("OKL-E-REVISION", "edit", **self.repair_fields(before, after))
            self.accepted_same(repaired_state, all_effects=True)
        elif name == "stale-surface-and-element-cursors":
            before = self.create(spec["base"])
            revision = bundle_identity(before)[0]
            queries = [("inspect", {"selector": {"kind": "object"}, "fields": ["identity", "source"], "limit": 1}),
                       ("inspect", {"selector": {"kind": "source"}, "fields": ["identity", "source"], "limit": 1}),
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
            old_run = self.evaluate(bundle_identity(payload)[0])
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
            reset = self.success("reset", program_revision=bundle_identity(payload)[0])
            reset_state = reset["result"]["run_state"]["last_valid_state"]
            self.check(reset_state["time_seconds"] == "0" and reset_state["side"] == "before",
                       "Actual reset returns the original modeled time and boundary side")
            fresh_run = self.evaluate(bundle_identity(payload)[0])
            self.check(len({old_run["run_id"], reset["run_id"], fresh_run["run_id"]}) == 3,
                       "Reset and subsequent fresh evaluation preserve distinct immutable run identities")
            pinned = self.success("inspect", program_revision=bundle_identity(payload)[0],
                run_id=old_run["run_id"], selector={"kind": "object"},
                fields=["identity", "state"], limit=100, time={"seconds": "1", "side": "after"})
            self.check(pinned["run_id"] == old_run["run_id"] and
                       pinned["program_revision"] == bundle_identity(payload)[0],
                       "The pre-reset run remains inspectable under its original revision")
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
            json_limit = self.refuse("OKL-E-RESOURCE", "inspect", program_revision=revision,
                selector={"element_id": ["assets", "label"]}, fields=["identity", "source"], limit=1,
                asset_slice={"offset": 0, "max_bytes": 1}, budgets={"max_value_entries": 1})
            self.check(any(d.get("details", {}).get("budget") == "logical_json_entries" and
                           d["details"].get("limit") == 1 and d["details"].get("consumed", 0) > 1
                           for d in json_limit.get("diagnostics", [])),
                       "The supported JSON-entry cap must fail actual asset response materialization")
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
        elif name == "cancel-at-four-real-concatenation-stages":
            self.create(spec["base"], level="represented")
            self.cancellation_barriers = []
            for stage in expected["required_actual_stages"]:
                self.cancel_during_concat(spec["base"], stage)
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
            self.read_source_pages(payload)
        elif name == "computed-namespace-and-explicit-c086-delivery":
            payload = self.create(spec["base"])
            revision = bundle_identity(payload)[0]
            self.success("validate", program_revision=revision, requested_level="constructed")
            self.inspect_panels(revision)
            self.evaluate(revision)
            self.export("identity", payload)
        elif name == "variable-input-membership-and-order":
            base = self.create(spec["base"])
            current = base
            for variant in spec["source_states"]:
                if bundle_identity(current)[0] != bundle_identity(base)[0]:
                    self.success("edit", **self.edit_fields(current, base))
                candidate = self.payload(variant)
                self.success("edit", **self.repair_fields(base, candidate))
                revision = bundle_identity(candidate)[0]
                self.success("validate", program_revision=revision, requested_level="constructed")
                self.inspect_panels(revision)
                self.evaluate(revision)
                self.export(variant, candidate)
                current = candidate
        else:
            raise AssertionError("No executable frozen C087 workflow: " + name)

    def read_source_pages(self, payload):
        """Exercise inherited item pagination, without inventing a byte-slice API."""
        revision = bundle_identity(payload)[0]
        units = {"entry": payload["entry"], **{
            "package:" + unit["package_id"] + "@" + unit["version"]: unit
            for unit in payload["modules"]}}
        cursor, offset, seen, records = None, 0, set(), []
        directory = self.output / "agent/retrieved-sources"
        directory.mkdir()
        while True:
            query = {"program_revision": revision, "selector": {"kind": "source"},
                     "fields": ["identity", "source"], "limit": 1}
            if cursor is not None:
                query["cursor"] = cursor
            response = self.success("inspect", **query)
            result = response["result"]
            self.check(response["program_revision"] == revision and result["offset"] == offset
                       and result["total"] == len(units) and len(result["items"]) == 1,
                       "Actual complete-source page is bounded and tied to this revision")
            source_units = result["source_units"]
            self.check(len(source_units) == 1, "A source-item page contains exactly its selected original unit")
            unit = source_units[0]
            source_id = unit["source_id"]
            self.check(source_id in units and source_id not in seen,
                       "Complete-source pages neither skip to an unknown unit nor repeat a unit")
            raw = units[source_id]["source"].encode("utf-8")
            self.check(unit == {"source_id": source_id, "filename": units[source_id]["filename"],
                               "source_revision": digest(raw), "source": units[source_id]["source"]},
                       "Exact original UTF-8 source bytes, filename and revision are retained")
            self.check(result["items"][0]["element_id"] == ["sources", source_id],
                       "Source-item identity matches the complete unit it returns")
            filename = f"unit-{offset:02}.ok"
            (directory / filename).write_bytes(raw)
            records.append({"source_id": source_id, "filename": unit["filename"],
                "source_revision": unit["source_revision"], "program_revision": revision,
                "offset": offset, "bytes": len(raw), "sha256": sha(raw),
                "path": "agent/retrieved-sources/" + filename,
                "request_id": response["request_id"]})
            seen.add(source_id)
            offset += 1
            cursor = response["next_cursor"]
            self.check(result["next_offset"] == (offset if offset < len(units) else None)
                       and result["truncated"] == (offset < len(units))
                       and bool(cursor) == (offset < len(units)),
                       "Actual source page terminates exactly at the complete unit inventory")
            if cursor is None:
                break
        self.check(seen == set(units), "Entry and all pinned source libraries were retrieved exactly")
        save(self.output / "agent/retrieved-sources.json", records)

    def cancel_during_concat(self, name, stage):
        payload = self.payload(name)
        state = self.state()
        request = self.request("validate", program_revision=bundle_identity(payload)[0], requested_level="represented")
        reached, release = threading.Event(), threading.Event()
        worker_errors, checkpoints, ledger_observations = [], [], []
        actual_ledgers, original_callback_errors = [], []
        original = self.service._make_check
        def make_check(task):
            check = original(task)
            original_poll = check.execution_budget.check
            if task.request["request_id"] == request["request_id"]:
                actual_ledgers.append(check.execution_budget)
            def gated():
                # Observe the existing cumulative ledger; this wrapper neither
                # changes a charge nor substitutes a synthetic checkpoint.
                if (task.request["request_id"] == request["request_id"] and
                        (check.execution_budget.stage or "").startswith("string_concat_")):
                    ledger_observations.append({"stage": check.execution_budget.stage,
                        "consumed_operations": check.execution_budget.operations,
                        "program_revision": check.program_revision,
                        "request_id": task.request["request_id"]})
                if (task.request["request_id"] == request["request_id"]
                        and check.execution_budget.stage == stage and not reached.is_set()):
                    checkpoints.append({"stage": check.execution_budget.stage,
                        "consumed_operations": check.execution_budget.operations,
                        "program_revision": check.program_revision, "request_id": task.request["request_id"]})
                    reached.set()
                    if not release.wait(30):
                        raise TimeoutError("Actual rekey cancellation barrier timed out")
                    time.sleep(.006)
                try:
                    return original_poll()
                except BaseException as error:
                    if task.request["request_id"] == request["request_id"]:
                        original_callback_errors.append(error)
                    raise
            check.execution_budget.check = gated
            return check
        self.service._make_check = make_check
        worker = None
        try:
            queued = self.call(request, wait=False)
            self.check(queued["status"] == "queued", "Actual rekey validation is queued")
            def work():
                try:
                    self.service.work_next()
                except BaseException as error:
                    worker_errors.append(error_record(error))
            worker = threading.Thread(target=work, name="c087-cancel-rekey")
            worker.start()
            self.check(reached.wait(30), "Actual nonempty rekey checkpoint must be reached before cancellation")
            self.success("cancel", target_request_id=request["request_id"])
            release.set()
            worker.join(30)
            self.check(not worker.is_alive() and not worker_errors, "Cancelled rekey worker terminates cleanly")
            terminal = self.call(request)
            self.check(terminal["status"] == "cancelled", "Original in-progress request is cancelled")
            self.success("status", target_request_id=request["request_id"])
            self.accepted_same(state, all_effects=True)
            self.check(original_callback_errors and any(ledger.callback_error is error for ledger in actual_ledgers for error in original_callback_errors),
                       "Actual original poll exception remains the ledger callback error")
        finally:
            release.set()
            if worker is not None:
                worker.join(30)
            self.service._make_check = original
            self.cancellation_barriers.append({
                "actual_concat_checkpoint_reached": reached.is_set(), "stage": stage,
                "request_id": request["request_id"], "checkpoints": checkpoints,
                "ledger_observations": ledger_observations, "worker_errors": worker_errors,
                "original_callback_exception_ids": [id(error) for error in original_callback_errors],
                "ledger_callback_error_ids": [None if ledger.callback_error is None else id(ledger.callback_error) for ledger in actual_ledgers],
                "original_callback_exception_identity_preserved": bool(original_callback_errors) and any(ledger.callback_error is error for ledger in actual_ledgers for error in original_callback_errors),
                "intervention": "Pause an actual dynamic rekey charge after its single input is admitted, send real protocol cancel, wait over the ordinary five-millisecond polling interval without changing its timestamp, then resume that original poll; execution-budget clocks, limits and charges are unchanged."})
            save(self.output / "agent/cancellation-barriers.json", self.cancellation_barriers)

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
            self.scenario, self.project = spec["id"], "c087-" + spec["id"].lower()
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
        self.summary["operation_inventory"] = sorted({r["request"]["operation"] for r in self.transcript})
        self.check(self.summary["operation_inventory"] == sorted(self.fixtures["workflows"]["required_operations"]),
                   "The exact twelve frozen real Agent operations are retained")
        save(self.output / "agent/transcript.json", self.transcript)
        with (self.output / "agent/transcript.jsonl").open("w", encoding="utf-8") as stream:
            for row in self.transcript:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
        self.summary["store"] = self.backup_store("durable")
        self.service.close()
        self.service = None

