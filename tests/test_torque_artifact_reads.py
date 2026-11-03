"""Actual durable .22 artifact reads retain authority and byte integrity."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from types import MethodType
import unittest
from unittest.mock import patch

from ontokin.agent_protocol import ProtocolError
from ontokin.budget_agent import BudgetAgentService
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget
from ontokin.keyed_membership_agent import KeyedMembershipAgentService
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.torque_agent import TorqueAgentService
from ontokin.torque_artifacts import _VerifiedBytes


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "docs/language-design/torque-v0.1/freeze"
POLICY = HostPolicy(max_operations=1000000, max_elapsed_ms=30000)


class Interrupted(BaseException):
    pass


class TorqueArtifactReadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = tempfile.TemporaryDirectory(prefix="c091-artifact-seed-")
        cls.program = load_texture_file_manifest(FROZEN / "workflow-agent-base.files.json")
        cls.project = "c091-byte-proof"
        with TorqueAgentService(Path(cls.seed.name), host_policy=POLICY) as service:
            create = service.handle({"schema_version": "ontokin.agent/0.22", "project_id": cls.project,
                "request_id": "seed-create", "operation": "create", "expected_program_revision": None,
                "requested_level": "constructed", "bundle": cls.program.to_payload()})
            if create["status"] != "succeeded":
                raise AssertionError(create)
            scenario = next(row for row in json.loads((FROZEN / "agent/request-workflows.json").read_bytes())["scenarios"]
                            if row["id"] == "A08")
            request = copy.deepcopy(scenario["steps"][1]["request"])
            request.update(project_id=cls.project, request_id="seed-export")
            exported = service.handle(request)
            if exported["status"] != "succeeded":
                raise AssertionError(exported)
            cls.artifact_id = exported["result"]["artifact_id"]
            with service._store.connection() as db:
                cls.retained = dict(db.execute("SELECT * FROM artifacts").fetchone())
            cls.data = bytes(cls.retained["data"])
            cls.base = service.database_path
        if hashlib.sha256(cls.data).hexdigest() != cls.artifact_id.removeprefix("artifact:"):
            raise AssertionError("Actual producer artifact identity mismatch")

    @classmethod
    def tearDownClass(cls):
        cls.seed.cleanup()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="c091-artifact-test-")
        self.root = Path(self.directory.name)
        self.db_path = self.root / self.base.name
        shutil.copyfile(self.base, self.db_path)
        self.service = TorqueAgentService(self.root, host_policy=POLICY, clock=lambda: 100.0)
        self.peers = []
        self.serial = 0

    def tearDown(self):
        for peer in self.peers:
            peer.close()
        self.service.close()
        self.assertIsNone(self.service._verified_artifact)
        self.assertIsNone(self.service._store._wal_keeper)
        for suffix in ("-wal", "-shm"):
            path = Path(str(self.db_path) + suffix)
            self.assertTrue(not path.exists() or path.stat().st_size == 0, suffix)
        with sqlite3.connect("file:" + str(self.db_path) + "?mode=ro", uri=True) as db:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.directory.cleanup()

    def request(self, operation="artifact", **fields):
        self.serial += 1
        result = {"schema_version": "ontokin.agent/0.22", "project_id": self.project,
                  "request_id": "read-%06d" % self.serial, "operation": operation}
        if operation == "artifact":
            result.update(artifact_id=self.artifact_id, offset=0, max_bytes=1)
        result.update(fields)
        return result

    def successful(self, request, *, service=None):
        response = (service or self.service).handle(request)
        self.assertEqual(response["status"], "succeeded", response)
        return response

    def codes(self, response):
        result = [item["code"] for item in response.get("diagnostics", [])]
        if response.get("protocol_error"):
            result.append(response["protocol_error"]["code"])
        return result

    def accepted_rows(self):
        with self.service._store.connection() as db:
            return {table: [tuple(row) for row in db.execute("SELECT * FROM " + table + " ORDER BY 1,2")]
                    for table in ("projects", "runs", "artifacts")}

    def traced(self, request):
        observations = []
        original = SharedExecutionBudget.tick
        def observe(ledger, node=None, amount=1):
            observations.append((ledger.stage, ledger.operations, amount))
            return original(ledger, node, amount)
        with patch.object(SharedExecutionBudget, "tick", observe):
            result = self.successful(request)
        return result, observations

    def test_original_miss_and_equal_bytes_preserve_all_charges_and_callbacks(self):
        self.service._read_artifact = MethodType(BudgetAgentService._read_artifact, self.service)
        self.service._check_task_response = MethodType(BudgetAgentService._check_task_response, self.service)
        baseline, original_trace = self.traced(self.request())
        del self.service._read_artifact
        del self.service._check_task_response
        miss, miss_trace = self.traced(self.request())
        retained = self.service._verified_artifact
        self.assertIs(type(retained), _VerifiedBytes)
        self.assertEqual(retained.data, self.data)
        hit, hit_trace = self.traced(self.request())
        self.assertIs(self.service._verified_artifact, retained)
        self.assertEqual(baseline["result"], miss["result"])
        self.assertEqual(miss["result"], hit["result"])
        self.assertEqual(original_trace, miss_trace)
        self.assertEqual(original_trace, hit_trace)
        for value in (miss, hit):
            self.assertEqual(value["execution_budget"]["consumed_operations"],
                             baseline["execution_budget"]["consumed_operations"])
        for offset in (0, 65535, len(self.data) - 1, len(self.data)):
            response = self.successful(self.request(offset=offset, max_bytes=17))
            result = response["result"]
            self.assertEqual(base64.b64decode(result["data_base64"]), self.data[offset:offset + 17])
            self.assertEqual(result["total_bytes"], len(self.data))
        beyond = self.service.handle(self.request(offset=len(self.data) + 1))
        self.assertIn("OKA-E-ARTIFACT", self.codes(beyond))

    def test_warm_proof_rereads_entire_blob_metadata_and_source(self):
        self.successful(self.request())
        cache = self.service._verified_artifact
        original_report = self.retained["report"]
        mutations = [
            ("data", self.data[:-1] + bytes([self.data[-1] ^ 1])),
            ("data", self.data[:-1]),
            ("sha256", "sha256:" + "0" * 64),
            ("report", json.dumps({**json.loads(original_report), "program_revision": "sha256:" + "0" * 64})),
            ("report", json.dumps({**json.loads(original_report), "implementation_identity": {}})),
        ]
        for field, value in mutations:
            with self.subTest(field=field, length=len(value)):
                with self.service._store.transaction() as db:
                    db.execute("UPDATE artifacts SET " + field + "=?", (value,))
                response = self.service.handle(self.request(offset=0, max_bytes=1))
                self.assertIn("OKA-E-STORE-INTEGRITY", self.codes(response))
                self.assertIs(self.service._verified_artifact, cache)
                with self.service._store.transaction() as db:
                    db.execute("UPDATE artifacts SET " + field + "=?", (self.retained[field],))
        with self.service._store.transaction() as db:
            raw = bytes(db.execute("SELECT raw FROM sources WHERE revision=?", (self.program.program_revision,)).fetchone()[0])
            altered = json.loads(raw)
            altered["entry"]["source"] += "\n"
            db.execute("UPDATE sources SET raw=? WHERE revision=?", (json.dumps(altered).encode(), self.program.program_revision))
        response = self.service.handle(self.request())
        self.assertIn("OKA-E-STORE-INTEGRITY", self.codes(response))
        with self.service._store.transaction() as db:
            db.execute("UPDATE sources SET raw=? WHERE revision=?", (raw, self.program.program_revision))

    def test_original_callback_cannot_mutate_verified_proof_to_accept_corrupt_bytes(self):
        self.successful(self.request())
        proof = self.service._verified_artifact
        changed = self.data[:-1] + bytes([self.data[-1] ^ 1])
        current, attempts = [], []
        original = SharedExecutionBudget.tick
        def observe(ledger, node=None, amount=1):
            current[:] = [ledger]
            return original(ledger, node, amount)
        def callback():
            if current[0].stage != "artifact_integrity" or attempts:
                return
            try:
                object.__setattr__(proof, "data", changed)
            except AttributeError:
                attempts.append("structurally-immutable")
            else:
                attempts.append("mutated")
        self.service._host_check = callback
        try:
            with patch.object(SharedExecutionBudget, "tick", observe):
                self.successful(self.request())
        finally:
            self.service._host_check = None
        self.assertEqual(attempts, ["structurally-immutable"])
        self.assertEqual(proof.data, self.data)
        with self.service._store.transaction() as db:
            db.execute("UPDATE artifacts SET data=?", (changed,))
        refused = self.service.handle(self.request())
        self.assertIn("OKA-E-STORE-INTEGRITY", self.codes(refused))

    def test_current_authority_is_rechecked_and_reopen_has_no_cached_grant(self):
        old_request = self.request()
        old_response = self.successful(old_request)
        self.service.host_policy = HostPolicy(max_operations=999999, max_elapsed_ms=30000)
        denied = self.service.handle(self.request())
        self.assertIn("OKL-E-RESOURCE", self.codes(denied))
        self.assertEqual(self.service.handle(old_request), old_response)
        self.service.close()
        self.service = TorqueAgentService(self.root, host_policy=POLICY)
        self.assertIsNone(self.service._verified_artifact)
        self.successful(self.request())
        self.assertIs(type(self.service._verified_artifact), _VerifiedBytes)

    def test_original_callbacks_cannot_replace_proof_from_any_request_stage(self):
        changed = self.data[:-1] + bytes([self.data[-1] ^ 1])
        for operation, stage in (("artifact", "artifact_integrity"), ("artifact", "publication"),
                                 ("discover", "publication")):
            for setter in (setattr, object.__setattr__):
                with self.subTest(operation=operation, stage=stage, setter=setter.__name__):
                    self.successful(self.request())
                    proof = self.service._verified_artifact
                    forged = type(proof)(proof.project, proof.artifact_id, changed, proof.digest)
                    attempts = []
                    def callback():
                        # This is the original host callback called directly
                        # by _BudgetCheck._poll; no ledger/callback replacement.
                        ledger = sys._getframe(1).f_locals["self"].execution_budget
                        if ledger.stage != stage or attempts:
                            return
                        try:
                            setter(self.service, "_verified_artifact", forged)
                        except AttributeError:
                            attempts.append("read-only-owner")
                        else:
                            attempts.append("forged-proof-published")
                    self.service._host_check = callback
                    try:
                        request = self.request() if operation == "artifact" else self.request("discover", profile="torque-0.1", limit=1)
                        self.successful(request)
                    finally:
                        self.service._host_check = None
                    self.assertEqual(attempts, ["read-only-owner"])
                    self.assertIs(self.service._verified_artifact, proof)
                    with self.service._store.transaction() as db:
                        db.execute("UPDATE artifacts SET data=?", (changed,))
                    try:
                        refused = self.service.handle(self.request(offset=len(changed)-1))
                        self.assertIn("OKA-E-STORE-INTEGRITY", self.codes(refused))
                    finally:
                        with self.service._store.transaction() as db:
                            db.execute("UPDATE artifacts SET data=?", (self.data,))

    def test_uncaught_cache_assignment_preserves_original_callback_exception(self):
        self.successful(self.request())
        proof = self.service._verified_artifact
        seen = []
        def callback():
            ledger = sys._getframe(1).f_locals["self"].execution_budget
            if ledger.stage != "publication" or seen:
                return
            try:
                self.service._verified_artifact = proof
            except AttributeError as error:
                seen.append(error)
                raise
        self.service._host_check = callback
        try:
            with self.assertRaises(AttributeError) as caught:
                self.service.handle(self.request())
        finally:
            self.service._host_check = None
        self.assertEqual(len(seen), 1)
        self.assertIs(caught.exception, seen[0])
        self.assertIs(self.service._verified_artifact, proof)

    def test_completed_close_cannot_be_followed_by_inflight_cache_publication(self):
        from ontokin import torque_artifacts
        entered, resume = Event(), Event()
        original = torque_artifacts._publish_verified_artifact
        observed = []
        def paused(service, proof):
            observed.append(proof)
            entered.set()
            if not resume.wait(timeout=10):
                raise AssertionError("The actual cache publisher was not resumed")
            return original(service, proof)
        request = self.request()
        with patch.object(torque_artifacts, "_publish_verified_artifact", paused):
            with ThreadPoolExecutor(max_workers=1) as workers:
                task = workers.submit(self.service.handle, request)
                try:
                    self.assertTrue(entered.wait(timeout=10), "Actual full-byte verification reaches cache publication")
                    self.service.close()
                    self.assertIsNone(self.service._verified_artifact)
                finally:
                    resume.set()
                response = task.result(timeout=10)
        self.assertEqual(len(observed), 1)
        self.assertIn(response["status"], ("cancelled", "unknown_outcome"))
        self.assertTrue(self.service._store.closed)
        self.assertIsNone(self.service._verified_artifact)
        self.service = TorqueAgentService(self.root, host_policy=POLICY)
        self.assertIsNone(self.service._verified_artifact)
        self.successful(self.request())

    def test_warm_read_retains_cap_deadline_cancel_and_original_exception(self):
        _, trace = self.traced(self.request())
        before = self.accepted_rows()
        first = next(row for row in trace if row[0] == "artifact_integrity")
        capped = self.service.handle(self.request(budgets={"max_operations": first[1] + first[2] - 1}))
        self.assertIn("OKL-E-RESOURCE", self.codes(capped))
        self.assertEqual(self.accepted_rows(), before)
        for mode in ("deadline", "cancel", "callback"):
            with self.subTest(mode=mode):
                now, seen = [100.0], []
                self.service._clock = lambda: now[0]
                sentinel = Interrupted("original host exception")
                request = self.request()
                peer = TorqueAgentService(self.root, host_policy=POLICY)
                self.peers.append(peer)
                current = []
                original = SharedExecutionBudget.tick
                def observe(ledger, node=None, amount=1):
                    current[:] = [ledger]
                    return original(ledger, node, amount)
                def host_check():
                    ledger = current[0]
                    if ledger.stage != "artifact_integrity" or seen:
                        return
                    seen.append(ledger.operations)
                    if mode == "deadline":
                        now[0] = 131.0
                    elif mode == "callback":
                        raise sentinel
                    else:
                        self.successful(self.request("cancel", target_request_id=request["request_id"]), service=peer)
                        ledger.check.__self__.last_poll = 0.0
                self.service._host_check = host_check
                try:
                    with patch.object(SharedExecutionBudget, "tick", observe):
                        if mode == "callback":
                            with self.assertRaises(Interrupted) as caught:
                                self.service.handle(request)
                            self.assertIs(caught.exception, sentinel)
                        else:
                            response = self.service.handle(request)
                            if mode == "deadline":
                                self.assertIn("OKL-E-RESOURCE", self.codes(response))
                            else:
                                self.assertEqual(response["status"], "cancelled")
                    self.assertEqual(len(seen), 1)
                finally:
                    self.service._host_check = None
                    self.service._clock = lambda: 100.0
                self.assertEqual(self.accepted_rows(), before)
                peer.close()

    def test_idle_handle_has_no_snapshot_and_services_observe_each_commit(self):
        keeper = self.service._store._wal_keeper
        self.assertFalse(keeper.in_transaction)
        self.assertEqual(keeper.execute("PRAGMA synchronous").fetchone()[0], 2)
        peer = TorqueAgentService(self.root, host_policy=POLICY)
        self.peers.append(peer)
        project = self.project + "-new"
        create = self.request("create", project_id=project, bundle=self.program.to_payload(),
                              expected_program_revision=None, requested_level="constructed")
        self.successful(create)
        self.assertEqual(peer.accepted_revision(project), self.program.program_revision)
        run = self.successful(self.request("evaluate", project_id=project,
            program_revision=self.program.program_revision, until_seconds="0.5", run_id=None), service=peer)
        self.assertEqual(self.service.get_run(project, run["run_id"])["valid_until_seconds"], "0.5")
        self.assertFalse(keeper.in_transaction)
        self.assertFalse(peer._store._wal_keeper.in_transaction)
        self.service.close()
        self.successful(self.request(), service=peer)
        self.assertFalse(peer._store._wal_keeper.in_transaction)

    def test_nested_and_concurrent_contexts_keep_separate_transactions(self):
        store = self.service._store
        with store.connection() as outer:
            self.assertIs(outer, store._wal_keeper)
            with store.connection() as nested:
                self.assertIsNot(outer, nested)
                self.assertFalse(nested.in_transaction)
            outer.execute("BEGIN IMMEDIATE")
            outer.execute("INSERT INTO projects VALUES ('uncommitted-native-check', NULL)")
            with store.connection() as nested:
                self.assertIsNone(nested.execute("SELECT id FROM projects WHERE id='uncommitted-native-check'").fetchone())
            # Returning this unfinished native transaction must roll it back,
            # exactly as the inherited fresh connection's close did.
        self.assertFalse(store._wal_keeper.in_transaction)
        with store.connection() as current:
            self.assertIsNone(current.execute("SELECT id FROM projects WHERE id='uncommitted-native-check'").fetchone())
        barrier = Barrier(2)
        requests = [self.request(offset=offset) for offset in (0, len(self.data) - 1)]
        def perform(request):
            barrier.wait(timeout=10)
            return self.service.handle(request)
        with ThreadPoolExecutor(max_workers=2) as workers:
            responses = list(workers.map(perform, requests))
        for request, response in zip(requests, responses):
            self.assertEqual(response["status"], "succeeded", response)
            offset = request["offset"]
            self.assertEqual(base64.b64decode(response["result"]["data_base64"]), self.data[offset:offset + 1])
        self.assertFalse(store._wal_keeper.in_transaction)

    def test_close_defers_borrowed_connection_release_without_losing_fence(self):
        store = self.service._store
        with store.connection() as borrowed:
            self.assertIs(borrowed, store._wal_keeper)
            self.service.close()
            self.assertIsNone(store._wal_keeper)
            self.assertFalse(borrowed.in_transaction)
            self.assertEqual(borrowed.execute("SELECT closed FROM sessions WHERE id=?", (store.owner,)).fetchone()[0], 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            borrowed.execute("SELECT 1")
        self.service = TorqueAgentService(self.root, host_policy=POLICY)
        self.successful(self.request())

    def test_real_publication_exception_rolls_back_and_close_fences_identity(self):
        project = self.project + "-uncommitted"
        request = self.request("create", project_id=project, bundle=self.program.to_payload(),
                               expected_program_revision=None, requested_level="constructed")
        original = self.service._persist_task_metadata
        original_check = self.service._check_task_response
        sentinel = Interrupted("interrupt original publication transaction")
        observed, active = [], []
        def capture(db, task):
            original(db, task)
            active[:] = [db]
        def interrupt(task):
            original_check(task)
            if not active or not active[0].in_transaction:
                return
            db = active[0]
            observed.append((db.in_transaction, self.service._store.accepted(db, project)))
            raise sentinel
        self.service._persist_task_metadata = capture
        self.service._check_task_response = interrupt
        with self.assertRaises(Interrupted) as caught:
            self.service.handle(request)
        self.assertIs(caught.exception, sentinel)
        self.assertEqual(observed, [(True, self.program.program_revision)])
        self.assertIsNone(self.service.accepted_revision(project))
        self.assertFalse(self.service._store._wal_keeper.in_transaction)
        self.service.close()
        self.service = TorqueAgentService(self.root, host_policy=POLICY)
        response = self.service.handle(request)
        self.assertEqual(response["status"], "unknown_outcome")
        self.assertIsNone(self.service.accepted_revision(project))

    def test_predecessor_store_and_schema_refusal_remain_unchanged(self):
        path = self.root / "old"
        with KeyedMembershipAgentService(path) as previous:
            self.assertFalse(hasattr(previous._store, "_wal_keeper"))
            old_path = previous.database_path
        original = old_path.read_bytes()
        wrong = self.root / "wrong"
        wrong.mkdir()
        target = wrong / "torque-program-agent.sqlite3"
        target.write_bytes(original)
        with self.assertRaises(ProtocolError) as caught:
            TorqueAgentService(wrong)
        self.assertEqual(caught.exception.code, "OKA-E-STORE-VERSION")
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(old_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
