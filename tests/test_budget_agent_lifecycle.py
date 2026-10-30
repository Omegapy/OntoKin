"""Actual C074 protocol work, current authority and durable rollback boundaries."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from ontokin.budget_agent import BudgetAgentService
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.execution_budget import HostPolicy
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "ontokin.agent/0.7"
PROFILE = "planar-reach-budget-0.1"
TARGET = "ontokin.glb/0.7"
POLICY = HostPolicy(400000, 80000, "c074-test-host")
CAPS = {"max_operations": 100000, "max_elapsed_ms": 30000}
TEXT = '''ontokin "0.7";
module BudgetAgent @ "budget-agent";
profile "planar-reach-budget-0.1";
execution { max_operations = 200000; max_elapsed = 60[s]; }
// A café label supplies an actual multibyte patch boundary
class Carrier @ "carrier-class" {
    geometry = box(vec3(1[m], 2[m], 3[m]));
    physical = no_body();
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object carrier @ "carrier": Carrier {}
    action travel @ "travel" = move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    at 0[s] sequence { start travel; }
}
'''
DEFAULT_TEXT = TEXT.replace("execution { max_operations = 200000; max_elapsed = 60[s]; }\n", "")
OPTIONS = {"fps": 2, "end": "0.5", "helpers": False}


def source(text=TEXT):
    return ProgramBundle(SourceUnit("entry", "budget-agent.ok", text.encode("utf-8")))


def exact_patch(program, old, new):
    unit = program.entry
    start = unit.raw.index(old.encode("utf-8"))
    return {"source_id": "entry", "source_revision": unit.revision,
            "element_id": ["sources", "entry"], "start_byte": start,
            "end_byte": start + len(old.encode("utf-8")),
            "expected_text": old, "replacement": new}


class BudgetAgentLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-budget-agent-")
        self.service = BudgetAgentService(self.temporary.name, host_policy=POLICY)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.temporary.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "budget-agent",
                "request_id": f"budget-{self.serial}", "operation": operation, **fields}

    def send(self, operation, **fields):
        return self.service.handle(self.request(operation, **fields))

    def success(self, response):
        self.assertEqual(response["schema_version"], PROTOCOL, response)
        self.assertEqual(response["status"], "succeeded", response)
        self.assertIsNone(response["protocol_error"], response)
        return response

    def error(self, response, code=None):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        if code is not None:
            codes = [item["code"] for item in response.get("diagnostics", [])]
            if response.get("protocol_error") is not None:
                codes.append(response["protocol_error"]["code"])
            self.assertIn(code, codes, response)
        return response

    def create(self, program=None, *, level="constructed", **fields):
        program = source() if program is None else program
        response = self.success(self.send("create", bundle=program.to_payload(),
            expected_program_revision=None, requested_level=level, **fields))
        self.assertEqual(response["accepted_program_revision"], program.program_revision)
        return program, response

    def evaluate(self, program, until="0.25", run_id=None, **fields):
        return self.success(self.send("evaluate", program_revision=program.program_revision,
            run_id=run_id, until_seconds=until, **fields))

    def export(self, program, **fields):
        return self.success(self.send("export", program_revision=program.program_revision,
            destination=TARGET, options=OPTIONS, **fields))

    def retained(self, project="budget-agent"):
        with self.service._store.connection() as db:
            return {"accepted": self.service._store.accepted(db, project),
                    "runs": [tuple(row) for row in db.execute(
                        "SELECT id,source_revision,descriptor,version FROM runs WHERE project_id=? ORDER BY id", (project,))],
                    "artifacts": [tuple(row) for row in db.execute(
                        "SELECT id,source_revision,data,report,sha256 FROM artifacts WHERE project_id=? ORDER BY id", (project,))]}

    def test_EB15_candidate_header_changes_revision_and_effective_request(self):
        program, _ = self.create()
        candidate = source(TEXT.replace("200000", "300000").replace("60[s]", "75[s]"))
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, "200000", "300000"),
                                                      exact_patch(program, "60[s]", "75[s]")]))
        self.assertNotEqual(candidate.program_revision, program.program_revision)
        self.assertEqual(response["program_revision"], candidate.program_revision)
        self.assertEqual(response["accepted_program_revision"], candidate.program_revision)
        receipt = response["execution_budget"]
        self.assertEqual(receipt["source_request"], {"max_operations": 300000, "max_elapsed_ms": 75000})
        self.assertEqual(receipt["effective"], receipt["source_request"])
        self.assertEqual(receipt["entry_revision"], candidate.entry.revision)

    def test_EB15_unauthorized_candidate_preserves_source_run_and_artifact(self):
        program, _ = self.create()
        self.evaluate(program)
        self.export(program)
        before = self.retained()
        response = self.error(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="delivered", destination=TARGET, options=OPTIONS,
            patches=[exact_patch(program, "200000", "400001")]), "OKL-E-RESOURCE")
        self.assertEqual(response["execution_budget"]["budget_reason"], "host_ceiling_exceeded")
        self.assertEqual(self.retained(), before)
        self.assertNotEqual(response["achieved_level"], "delivered")

    def test_EB15_candidate_construction_exhaustion_keeps_prior_acceptance(self):
        program, _ = self.create()
        before = self.retained()
        response = self.error(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, "200000", "200")]), "OKL-E-RESOURCE")
        self.assertEqual(response["execution_budget"]["budget_reason"], "operation_budget_exhausted")
        self.assertEqual(self.retained(), before)

    def test_EB15_lowering_source_budget_repairs_under_lower_current_host(self):
        program, _ = self.create()
        self.service.host_policy = HostPolicy()
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, "200000", "100000"),
                                                      exact_patch(program, "60[s]", "30[s]")]))
        candidate = source(TEXT.replace("200000", "100000").replace("60[s]", "30[s]"))
        self.assertEqual(response["accepted_program_revision"], candidate.program_revision)
        self.assertEqual(response["execution_budget"]["effective"], CAPS)

    def test_EB15_nominal_occurrence_identity_cannot_change_silently(self):
        program, _ = self.create()
        before = self.retained()
        response = self.error(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, '"carrier-class"', '"other-class"')]), "OKL-E-ID")
        self.assertEqual(response["accepted_program_revision"], program.program_revision)
        self.assertEqual(self.retained(), before)

    def test_EB15_exact_utf8_preconditions_and_source_scope_are_atomic(self):
        program, _ = self.create()
        good = exact_patch(program, "1[m], 2[m], 3[m]", "2[m], 2[m], 3[m]")
        split = program.entry.raw.index("é".encode("utf-8")) + 1
        bad_patches = [
            {**good, "expected_text": "wrong"},
            {**good, "source_revision": "sha256:" + "0" * 64},
            {**good, "start_byte": split, "end_byte": split, "expected_text": "", "replacement": "x"},
            {**good, "element_id": ["budget-agent", "demo", "carrier"]},
        ]
        before = self.retained()
        for bad in bad_patches:
            with self.subTest(patch=bad):
                self.error(self.send("edit", expected_program_revision=program.program_revision,
                    requested_level="constructed", patches=[bad]))
                self.assertEqual(self.retained(), before)
        self.error(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[good, good]))
        self.assertEqual(self.retained(), before)

    def test_EB15_failed_new_project_retains_no_accepted_revision(self):
        program = source(TEXT.replace("200000", "400001"))
        response = self.error(self.send("create", bundle=program.to_payload(), expected_program_revision=None,
            requested_level="constructed"), "OKL-E-RESOURCE")
        self.assertIsNone(response["accepted_program_revision"])
        self.assertEqual(self.retained(), {"accepted": None, "runs": [], "artifacts": []})

    def test_EB16_saved_program_requires_current_policy_or_explicit_caps(self):
        program, _ = self.create()
        self.service.host_policy = HostPolicy()
        failure = self.error(self.send("validate", program_revision=program.program_revision,
            requested_level="constructed"), "OKL-E-RESOURCE")
        self.assertEqual(failure["execution_budget"]["budget_reason"], "host_ceiling_exceeded")
        reduced = self.success(self.send("validate", program_revision=program.program_revision,
            requested_level="constructed", budgets=CAPS))
        self.assertEqual(reduced["execution_budget"]["effective"], CAPS)
        self.assertEqual(reduced["execution_budget"]["source_request"],
                         {"max_operations": 200000, "max_elapsed_ms": 60000})

    def test_EB16_saved_run_reauthorizes_and_preserves_failed_advancement(self):
        program, _ = self.create()
        prior = self.evaluate(program)
        before = self.retained()
        self.service.host_policy = HostPolicy()
        self.error(self.send("evaluate", program_revision=program.program_revision, run_id=prior["run_id"],
            until_seconds="0.5"), "OKL-E-RESOURCE")
        self.assertEqual(self.retained(), before)
        advanced = self.evaluate(program, "0.5", prior["run_id"], budgets=CAPS)
        self.assertEqual(advanced["run_id"], prior["run_id"])
        self.assertEqual(advanced["result"]["run_state"]["valid_until_seconds"], "0.5")

    def test_EB16_artifact_retrieval_uses_its_source_and_current_host(self):
        program, _ = self.create()
        exported = self.export(program)
        artifact_id = exported["result"]["artifact_id"]
        self.service.host_policy = HostPolicy()
        failure = self.error(self.send("artifact", artifact_id=artifact_id, max_bytes=64), "OKL-E-RESOURCE")
        self.assertEqual(failure["execution_budget"]["budget_reason"], "host_ceiling_exceeded")
        retrieved = self.success(self.send("artifact", artifact_id=artifact_id, max_bytes=64, budgets=CAPS))
        self.assertEqual(retrieved["program_revision"], program.program_revision)
        self.assertEqual(retrieved["execution_budget"]["effective"], CAPS)
        self.assertEqual(base64.b64decode(retrieved["result"]["data_base64"])[:4], b"glTF")
        self.assertEqual(retrieved["result"]["sha256"], exported["result"]["sha256"])

    def test_EB16_new_inspection_and_reset_reauthorize_saved_source(self):
        program, _ = self.create()
        self.service.host_policy = HostPolicy()
        fields = {"program_revision": program.program_revision, "selector": {},
                  "fields": ["identity"], "limit": 20}
        self.error(self.send("inspect", **fields), "OKL-E-RESOURCE")
        self.success(self.send("inspect", **fields, budgets=CAPS))
        self.error(self.send("reset", program_revision=program.program_revision), "OKL-E-RESOURCE")
        self.success(self.send("reset", program_revision=program.program_revision, budgets=CAPS))

    def test_EB18_queued_work_uses_policy_when_worker_admits(self):
        program = source()
        request = self.request("create", bundle=program.to_payload(), expected_program_revision=None,
                               requested_level="constructed")
        self.assertEqual(self.service.submit(request)["status"], "queued")
        self.service.host_policy = HostPolicy()
        response = self.error(self.service.handle(request), "OKL-E-RESOURCE")
        self.assertEqual(response["execution_budget"]["host_ceilings"], CAPS)
        self.assertIsNone(self.service.accepted_revision("budget-agent"))

    def test_EB18_pending_limit_preserves_retries_and_control_requests(self):
        self.service.max_pending_requests = 1
        first = self.request("create", bundle=source().to_payload(), expected_program_revision=None,
                             requested_level="constructed")
        queued = self.service.submit(first)
        self.assertEqual(queued["status"], "queued")
        self.assertEqual(self.service.submit(copy.deepcopy(first)), queued)
        self.error(self.service.submit(self.request("create", bundle=source().to_payload(),
            expected_program_revision=None, requested_level="constructed", project_id="other")), "OKA-E-RESOURCE")
        status = self.success(self.send("status", target_request_id=first["request_id"]))
        self.assertEqual(status["result"]["target_status"], "queued")
        self.success(self.send("cancel", target_request_id=first["request_id"]))
        self.assertEqual(self.service.handle(first)["status"], "cancelled")
        self.create()

    def test_EB18_running_limit_leaves_second_request_queued(self):
        self.service.max_running_requests = 1
        first = self.request("create", bundle=source().to_payload(), expected_program_revision=None,
                             requested_level="constructed", project_id="one")
        second = self.request("create", bundle=source().to_payload(), expected_program_revision=None,
                              requested_level="constructed", project_id="two")
        for request in (first, second):
            self.assertEqual(self.service.submit(request)["status"], "queued")
        ready, release = threading.Event(), threading.Event()
        execute, errors = self.service._execute, []

        def pause_first(task, check):
            if task.request["request_id"] == first["request_id"]:
                ready.set()
                if not release.wait(10):
                    raise TimeoutError("The test did not release its first worker")
            return execute(task, check)

        def worker():
            try:
                self.assertTrue(self.service.work_next())
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=worker, daemon=True)
        with patch.object(self.service, "_execute", side_effect=pause_first):
            try:
                thread.start()
                self.assertTrue(ready.wait(10))
                self.assertFalse(self.service.work_next())
                self.assertEqual(self.service.submit(second)["status"], "queued")
            finally:
                release.set()
                thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.success(self.service.handle(first))
        self.success(self.service.handle(second))

    def test_EB18_concurrent_workers_keep_distinct_ledgers_and_policy_snapshots(self):
        high = self.request("create", bundle=source().to_payload(), expected_program_revision=None,
                            requested_level="constructed", project_id="high")
        low = self.request("create", bundle=source(DEFAULT_TEXT).to_payload(), expected_program_revision=None,
                           requested_level="constructed", project_id="low")
        for request in (high, low):
            self.assertEqual(self.service.submit(request)["status"], "queued")
        ready = {high["request_id"]: threading.Event(), low["request_id"]: threading.Event()}
        release = threading.Event()
        observed, errors = {}, []
        original = self.service._execute

        def execute(task, check):
            observed[task.request["request_id"]] = check.execution_budget
            ready[task.request["request_id"]].set()
            if not release.wait(10):
                raise TimeoutError("The test did not release admitted requests")
            return original(task, check)

        def worker():
            try:
                self.assertTrue(self.service.work_next())
            except BaseException as error:
                errors.append(error)

        threads = []
        with patch.object(self.service, "_execute", side_effect=execute):
            try:
                first = threading.Thread(target=worker, daemon=True); threads.append(first); first.start()
                self.assertTrue(ready[high["request_id"]].wait(10))
                self.service.host_policy = HostPolicy()
                second = threading.Thread(target=worker, daemon=True); threads.append(second); second.start()
                self.assertTrue(ready[low["request_id"]].wait(10))
            finally:
                release.set()
                for thread in threads:
                    thread.join(10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        first_result = self.success(self.service.handle(high))
        second_result = self.success(self.service.handle(low))
        self.assertIsNot(observed[high["request_id"]], observed[low["request_id"]])
        self.assertEqual(first_result["execution_budget"]["host_ceilings"], POLICY.ceilings)
        self.assertEqual(second_result["execution_budget"]["host_ceilings"], CAPS)
        self.assertEqual(first_result["execution_budget"]["effective"]["max_operations"], 200000)
        self.assertEqual(second_result["execution_budget"]["effective"]["max_operations"], 100000)

    def test_EB18_cancel_after_actual_computation_prevents_all_new_effects(self):
        program = source()
        request = self.request("create", bundle=program.to_payload(), expected_program_revision=None,
            requested_level="delivered", destination=TARGET, options=OPTIONS)
        execute = self.service._execute
        prepared = []

        def cancel_completed(task, check):
            execute(task, check)
            prepared.append(task.artifact is not None)
            self.success(self.send("cancel", target_request_id=request["request_id"]))

        with patch.object(self.service, "_execute", side_effect=cancel_completed):
            response = self.service.handle(request)
        self.assertEqual(prepared, [True])
        self.assertEqual(response["status"], "cancelled", response)
        self.assertEqual(self.retained(), {"accepted": None, "runs": [], "artifacts": []})
        self.assertEqual(self.service.handle(request), response)

    def test_EB18_cancelled_extension_preserves_original_run_bytes(self):
        program, _ = self.create()
        prior = self.evaluate(program)
        before = self.retained()
        request = self.request("evaluate", program_revision=program.program_revision,
                               run_id=prior["run_id"], until_seconds="0.5")
        finish = self.service._finish

        def cancel_before_transaction(task):
            self.success(self.send("cancel", target_request_id=request["request_id"]))
            return finish(task)

        with patch.object(self.service, "_finish", side_effect=cancel_before_transaction):
            response = self.service.handle(request)
        self.assertEqual(response["status"], "cancelled", response)
        self.assertEqual(self.retained(), before)

    def test_EB24_same_payload_returns_original_receipt_after_policy_change(self):
        program = source()
        request = self.request("create", bundle=program.to_payload(), expected_program_revision=None,
                               requested_level="constructed")
        original = self.success(self.service.handle(request))
        before = self.retained()
        self.service.host_policy = HostPolicy()
        with patch.object(self.service, "_execute", side_effect=AssertionError("An identical retry executed")):
            self.assertEqual(self.service.handle(copy.deepcopy(request)), original)
        self.assertEqual(self.retained(), before)
        self.assertEqual(original["execution_budget"]["host_ceilings"], POLICY.ceilings)

    def test_EB24_changed_budget_under_used_request_id_conflicts(self):
        program, _ = self.create()
        request = self.request("validate", program_revision=program.program_revision,
                               requested_level="constructed", budgets=CAPS)
        original = self.success(self.service.handle(request))
        changed = {**request, "budgets": {**CAPS, "max_operations": 99999}}
        self.error(self.service.handle(changed), "OKL-E-REQUEST-ID")
        self.assertEqual(self.service.handle(request), original)

    def test_EB24_retry_after_reopening_retains_old_receipt_without_reauthorization(self):
        program = source()
        request = self.request("create", bundle=program.to_payload(), expected_program_revision=None,
                               requested_level="constructed")
        original = self.success(self.service.handle(request))
        self.service.close()
        self.service = BudgetAgentService(self.temporary.name, host_policy=HostPolicy())
        self.assertEqual(self.service.handle(request), original)
        self.error(self.send("validate", program_revision=program.program_revision,
                            requested_level="constructed"), "OKL-E-RESOURCE")

    def test_EB24_expired_result_is_not_reexecuted(self):
        program = source()
        request = self.request("create", bundle=program.to_payload(), expected_program_revision=None,
                               requested_level="constructed")
        self.success(self.service.handle(request))
        before = self.retained()
        self.assertTrue(self.service.expire_result(request["project_id"], request["request_id"]))
        response = self.service.handle(request)
        self.assertEqual(response["status"], "unknown_outcome", response)
        self.assertEqual(self.retained(), before)

    def test_EB24_work_failure_is_not_automatically_retried(self):
        program = source()
        request = self.request("create", bundle=program.to_payload(), expected_program_revision=None,
                               requested_level="constructed", budgets={"max_operations": 1})
        original = self.service._execute
        with patch.object(self.service, "_execute", wraps=original) as work:
            failed = self.error(self.service.handle(request), "OKL-E-RESOURCE")
            count = work.call_count
            self.assertLessEqual(count, 1)
            self.assertEqual(self.service.handle(request), failed)
            self.assertEqual(work.call_count, count)
        self.assertIsNone(self.service.accepted_revision("budget-agent"))

    def test_EB29_discovery_reports_authority_and_preserves_legacy_registry(self):
        response = self.success(self.send("discover", profile=PROFILE, limit=100))
        rendered = json.dumps(response["result"])
        self.assertIn(PROTOCOL, rendered)
        self.assertIn(PROFILE, rendered)
        self.assertIn(TARGET, rendered)
        self.assertIn("100000", rendered)
        self.assertIn("400000", rendered)
        self.assertIn("80000", rendered)
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)

    def test_EB29_complete_discover_create_inspect_evaluate_export_retrieve_status_cycle(self):
        self.success(self.send("discover", profile=PROFILE, limit=100))
        program, _ = self.create()
        inspected = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"kind": "object"}, fields=["identity", "source", "geometry"], limit=20))
        self.assertEqual(len(inspected["result"]["items"]), 1)
        evaluated = self.evaluate(program, "0.5")
        self.assertEqual(evaluated["result"]["run_state"]["valid_until_seconds"], "0.5")
        request = self.request("export", program_revision=program.program_revision, destination=TARGET, options=OPTIONS)
        exported = self.success(self.service.handle(request))
        self.assertEqual(exported["achieved_level"], "delivered")
        self.assertEqual(exported["result"]["report"]["validation"]["status"], "passed")
        artifact_id = exported["result"]["artifact_id"]
        chunks, offset = [], 0
        while True:
            retrieved = self.success(self.send("artifact", artifact_id=artifact_id, offset=offset, max_bytes=4096))
            chunks.append(base64.b64decode(retrieved["result"]["data_base64"]))
            offset = retrieved["result"]["next_offset"]
            if offset is None:
                break
        data = b"".join(chunks)
        self.assertEqual(len(data), exported["result"]["total_bytes"])
        self.assertEqual("sha256:" + hashlib.sha256(data).hexdigest(), exported["result"]["sha256"])
        status = self.success(self.send("status", target_request_id=request["request_id"]))
        self.assertEqual(status["result"]["target"], exported)

    def test_EB29_requested_delivery_without_target_cannot_return_lower_level_success(self):
        program, _ = self.create()
        response = self.error(self.send("validate", program_revision=program.program_revision,
                                      requested_level="delivered"), "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertNotEqual(response["achieved_level"], "delivered")
        self.assertEqual(len(self.retained()["artifacts"]), 0)

    def test_EB29_execution_fields_cannot_grant_host_authority(self):
        program = source()
        for fields in ({"host_policy": {"max_operations": 999999}},
                       {"policy_id": "grant-all"}, {"execution_budget": {"effective": CAPS}},
                       {"budgets": {"max_operations": True}},
                       {"budgets": {"max_operations": 0}},
                       {"budgets": {"max_operations": 1 << 53}},
                       {"budgets": {"max_value_entries": 100001}}):
            with self.subTest(fields=fields):
                response = self.error(self.send("create", bundle=program.to_payload(), expected_program_revision=None,
                                               requested_level="constructed", **fields))
                self.assertIsNone(response["accepted_program_revision"])
        self.service.host_policy = HostPolicy()
        self.error(self.send("create", bundle=program.to_payload(), expected_program_revision=None,
            requested_level="constructed", budgets={"max_operations": 200000, "max_elapsed_ms": 60000}), "OKL-E-RESOURCE")

    def test_EB29_large_host_does_not_raise_omitted_source_defaults(self):
        _, response = self.create(source(DEFAULT_TEXT))
        self.assertEqual(response["execution_budget"]["source_request"], CAPS)
        self.assertEqual(response["execution_budget"]["effective"], CAPS)
        self.assertEqual(response["execution_budget"]["host_ceilings"], POLICY.ceilings)

    def test_EB29_success_receipt_keeps_original_clock_and_complete_identity(self):
        program, response = self.create()
        receipt = response["execution_budget"]
        self.assertEqual(receipt["program_revision"], program.program_revision)
        self.assertEqual(receipt["entry_revision"], program.entry.revision)
        self.assertEqual(receipt["request_id"], response["request_id"])
        self.assertEqual(receipt["implementation"], self.service.implementation)
        self.assertFalse(receipt["provisional"])
        self.assertGreater(receipt["consumed_operations"], 0)
        self.assertGreaterEqual(receipt["elapsed_ms"], 0)
        self.assertAlmostEqual(receipt["deadline_monotonic_seconds"] - receipt["started_monotonic_seconds"], 60.0)

    def test_EB29_small_output_budget_returns_failure_without_acceptance(self):
        program = source()
        response = self.error(self.send("create", bundle=program.to_payload(), expected_program_revision=None,
            requested_level="constructed", budgets={"max_value_entries": 1}))
        self.assertIsNone(response["accepted_program_revision"])
        self.assertIsNotNone(response.get("execution_budget"), response)
        self.assertEqual(self.retained(), {"accepted": None, "runs": [], "artifacts": []})

    def test_EB29_final_transaction_work_exhaustion_rolls_back_all_tentative_effects(self):
        program = source()
        guard, calls, prepared = self.service._check_task_response, [], []

        def exhaust_final_check(task):
            calls.append(task.response["status"])
            if len(calls) == 2:
                prepared.append((task.accept, task.run is not None, task.artifact is not None))
                ledger = task.execution_check.execution_budget
                ledger.operations = ledger.limits["max_operations"]
            return guard(task)

        with patch.object(self.service, "_check_task_response", side_effect=exhaust_final_check):
            response = self.error(self.send("create", bundle=program.to_payload(), expected_program_revision=None,
                requested_level="delivered", destination=TARGET, options=OPTIONS), "OKL-E-RESOURCE")
        self.assertEqual(prepared, [(True, True, True)])
        self.assertEqual(response["execution_budget"]["budget_reason"], "operation_budget_exhausted")
        self.assertEqual(self.retained(), {"accepted": None, "runs": [], "artifacts": []})
        with self.service._store.connection() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM acceptance_identities").fetchone()[0], 0)

    def test_EB29_final_transaction_deadline_uses_original_clock_and_rolls_back(self):
        self.service.close()
        clock = [10.0]
        self.service = BudgetAgentService(self.temporary.name, host_policy=POLICY, clock=lambda: clock[0])
        guard, calls = self.service._check_task_response, []

        def expire_final_check(task):
            calls.append(task.response["status"])
            if len(calls) == 2:
                clock[0] = 70.001
            return guard(task)

        with patch.object(self.service, "_check_task_response", side_effect=expire_final_check):
            response = self.error(self.send("create", bundle=source().to_payload(), expected_program_revision=None,
                requested_level="constructed"), "OKL-E-RESOURCE")
        receipt = response["execution_budget"]
        self.assertEqual(receipt["started_monotonic_seconds"], 10.0)
        self.assertEqual(receipt["deadline_monotonic_seconds"], 70.0)
        self.assertEqual(receipt["budget_reason"], "execution_deadline_exceeded")
        self.assertEqual(self.retained(), {"accepted": None, "runs": [], "artifacts": []})

    def test_EB29_trusted_callback_exception_identity_survives_durable_cancellation(self):
        from ontokin.diagnostics import OntoKinError
        from ontokin.json_limits import JSONLimitError
        for number, marker in enumerate((RuntimeError("stop"), OntoKinError("OKL-E-TYPE", "stop"),
                                        JSONLimitError("caller", 1, 2))):
            self.service.close()

            def cancel():
                raise marker

            self.service = BudgetAgentService(Path(self.temporary.name) / str(number), host_policy=POLICY, check=cancel)
            request = self.request("create", bundle=source().to_payload(), expected_program_revision=None,
                                   requested_level="constructed")
            with self.subTest(error=type(marker).__name__), self.assertRaises(type(marker)) as caught:
                self.service.handle(request)
            self.assertIs(caught.exception, marker)
            self.assertEqual(self.service.handle(request)["status"], "cancelled")
            self.assertEqual(self.retained(), {"accepted": None, "runs": [], "artifacts": []})

    def test_EB29_frozen_c073_source_mesh_pages_remain_bounded_and_revision_bound(self):
        directory = ROOT / "examples/execution-budgets"
        freeze = json.loads((directory / "acceptance-freeze.json").read_text())
        raw = (directory / "larger-workload.ok").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), freeze["files"]["larger-workload.ok"]["sha256"])
        expected = (directory / "larger-workload.expected.json").read_bytes()
        self.assertEqual(hashlib.sha256(expected).hexdigest(), freeze["files"]["larger-workload.expected.json"]["sha256"])
        program = ProgramBundle(SourceUnit("entry", "larger-workload.ok", raw))
        self.create(program)
        response = self.success(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=["force-workshop", "workshop", "vessel-1"], count=2))
        self.assertEqual(response["result"]["program_revision"], program.program_revision)
        self.assertEqual(response["result"]["returned_triangles"], 2)
        self.assertEqual(len(response["result"]["triangles"]), 2)
        self.assertTrue(response["truncated"])
        self.assertIsNotNone(response["next_cursor"])

    def test_EB29_cli_selects_only_explicit_budget_protocol(self):
        request = self.request("create", bundle=source(DEFAULT_TEXT).to_payload(), expected_program_revision=None,
                               requested_level="constructed")
        with tempfile.TemporaryDirectory() as directory:
            execution = subprocess.run([sys.executable, "-m", "ontokin", "agent", "--store", directory,
                "--wait", "--protocol", PROTOCOL], input=b'{"broken":\n' + json.dumps(request).encode() + b'\n',
                capture_output=True, cwd=ROOT, timeout=30)
        self.assertEqual(execution.returncode, 0, execution.stderr)
        self.assertEqual(execution.stderr, b"")
        responses = [json.loads(line) for line in execution.stdout.splitlines()]
        self.assertEqual(responses[0]["schema_version"], PROTOCOL)
        self.assertEqual(responses[0]["protocol_error"]["code"], "OKA-E-JSON")
        self.success(responses[1])


if __name__ == "__main__":
    unittest.main()
