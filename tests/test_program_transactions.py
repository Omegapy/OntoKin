"""Actual bundle computation at durable program-agent transaction boundaries.

The gates below only order real work. Both competing edits parse and evaluate
their complete dependency bundles before either transaction may accept them.
Subprocess checks exercise persisted receipts and proven-dead worker fencing.
"""

from __future__ import annotations

from contextlib import contextmanager
import copy
import itertools
import json
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch as instrument

from ontokin.agent_protocol import ProtocolError
from ontokin.bundle import load_bundle
from ontokin.program_agent import ProgramAgentService


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/language-design/construction-v0.1/01-keyed-rack/program.bundle.json"
PROJECT = "program-transactions"
SELECTED = 'first.fingers["middle"]'


class _FinishGate(ProgramAgentService):
    """Wait immediately before committing a real completed program operation."""

    def __init__(self, path):
        self.ready = threading.Event()
        self.release = threading.Event()
        self.prepared = None
        self.errors = []
        super().__init__(path)

    def _finish(self, task):
        self.prepared = {"response": copy.deepcopy(task.response), "run": copy.deepcopy(task.run),
                         "accept": task.accept,
                         "program": None if task.source is None else task.source.to_payload()}
        self.ready.set()
        if not self.release.wait(10):
            raise TimeoutError("The test did not release the prepared program transaction")
        super()._finish(task)

    def do_work(self):
        try:
            if not self.work_next():
                raise AssertionError("The worker could not claim the queued program operation")
        except BaseException as error:
            self.errors.append(error)
            self.ready.set()


class _LateTermination(ProgramAgentService):
    """Exhaust one request budget only after the real extension was computed."""

    def __init__(self, path, budget):
        self.budget = budget
        self.prepared = None
        super().__init__(path)

    def _execute(self, task, check):
        super()._execute(task, check)
        self.prepared = copy.deepcopy(task.run)
        if self.budget == "max_operations":
            check.operations = check.limits["max_operations"]
        else:
            check.started = time.monotonic() - check.limits["max_elapsed_ms"] / 1000 - 1


class _OversizedControl(ProgramAgentService):
    """Add a size probe after the actual cancellation SQL changes were made."""

    def _control(self, db, request):
        response = super()._control(db, request)
        response["result"]["oversized_fixture"] = "x" * (4 * 1024 * 1024)
        return response


class ProgramTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-program-transactions-")
        self.path = Path(self.temporary.name) / "state"
        self.service = ProgramAgentService(self.path)
        self.serial = itertools.count(1)
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.original = load_bundle(self.payload)

    def tearDown(self):
        self.service.close()
        self.temporary.cleanup()

    def request(self, operation, **fields):
        return {"schema_version": "ontokin.agent/0.2", "project_id": PROJECT,
                "request_id": f"program-transaction-{next(self.serial)}", "operation": operation, **fields}

    def assert_success(self, response):
        self.assertEqual(response["schema_version"], "ontokin.agent/0.2", response)
        self.assertEqual(response["status"], "succeeded", response)
        self.assertIsNone(response["protocol_error"], response)

    def assert_code(self, response, code):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        codes = [diagnostic["code"] for diagnostic in response["diagnostics"]]
        if response["protocol_error"]:
            codes.append(response["protocol_error"]["code"])
        self.assertIn(code, codes, response)

    def reopen(self):
        self.service.close()
        self.service = ProgramAgentService(self.path)

    def create(self, level="represented"):
        request = self.request("create", bundle=self.payload, expected_program_revision=None, requested_level=level)
        response = self.service.handle(request)
        self.assert_success(response)
        self.assertEqual(response["program_revision"], self.original.program_revision)
        return request, response

    def source_patch(self, program, source_id, old, new, element_id=None):
        source = program.sources[source_id]
        start = source.raw.index(old.encode("utf-8"))
        return {"source_id": source_id, "source_revision": source.revision,
                "element_id": element_id or ["sources", source_id], "start_byte": start,
                "end_byte": start + len(old.encode("utf-8")), "expected_text": old, "replacement": new}

    def candidate(self, radius, *, program=None):
        """A real two-file edit changes a component and its exact import pin."""
        program = program or self.original
        module = program.to_payload()["modules"][0]
        previous = program.modules[0]
        old_expression = "sphere(0.06[m])"
        self.assertEqual(module["source"].count(old_expression), 1)
        module["source"] = module["source"].replace(old_expression, f"sphere({radius}[m])")
        candidate_payload = program.to_payload()
        candidate_payload["modules"] = [module]
        provisional = load_bundle(candidate_payload)
        new_revision = provisional.modules[0].revision
        candidate_payload["entry"]["source"] = program.entry.text.replace(previous.revision, new_revision)
        expected = load_bundle(candidate_payload)
        request = self.request("edit", expected_program_revision=program.program_revision,
            requested_level="evaluated",
            patches=[self.source_patch(program, "entry", previous.revision, new_revision)],
            module_changes=[{"operation": "replace", "source_id": previous.source_id,
                             "source_revision": previous.revision, "module": module}])
        return request, expected

    @contextmanager
    def prepared(self, requests):
        workers = [_FinishGate(self.path) for _ in requests]
        threads = []
        try:
            for request in requests:
                self.assertEqual(self.service.submit(request)["status"], "queued")
            for worker in workers:
                thread = threading.Thread(target=worker.do_work, daemon=True)
                threads.append(thread)
                thread.start()
                self.assertTrue(worker.ready.wait(10), "Program work did not reach its commit boundary")
                self.assertEqual(worker.errors, [])
                self.assertIsNotNone(worker.prepared)
                self.assertEqual(worker.prepared["response"]["status"], "succeeded", worker.prepared)
            yield workers, threads
        finally:
            for worker in workers:
                worker.release.set()
            for thread in threads:
                thread.join(10)
            for worker in workers:
                worker.close()

    def release(self, worker, thread):
        worker.release.set()
        thread.join(10)
        self.assertFalse(thread.is_alive(), "The released program worker did not finish")
        self.assertEqual(worker.errors, [])

    @contextmanager
    def prepared_process(self):
        code = '''import json, sys
from pathlib import Path
from ontokin.program_agent import ProgramAgentService
service = ProgramAgentService(Path(sys.argv[1]))
execute = service._execute
def pause(task, check):
    execute(task, check)
    assert task.response['status'] == 'succeeded', task.response
    assert task.run['valid_until_seconds'] == '2', task.run
    print(json.dumps({'prepared': True, 'program_revision': task.source.program_revision,
                      'run_id': task.run['run_id']}), flush=True)
    sys.stdin.readline()
service._execute = pause
try:
    assert service.work_next(), 'No queued work to prepare'
finally:
    service.close()
'''
        process = subprocess.Popen([sys.executable, "-c", code, str(self.path)], cwd=ROOT,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, bufsize=1)
        try:
            self.assertTrue(select.select([process.stdout], [], [], 10)[0], "The process did not prepare actual work")
            line = process.stdout.readline()
            self.assertTrue(line, "The process exited before preparing work")
            prepared = json.loads(line)
            self.assertTrue(prepared["prepared"])
            yield process, prepared
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    def test_competing_complete_bundles_commit_one_head_and_retain_loser_evidence(self):
        _, created = self.create()
        requests, candidates = zip(self.candidate("0.07"), self.candidate("0.08"))
        with self.prepared(requests) as (workers, threads):
            self.assertEqual(self.service.accepted_revision(PROJECT), created["program_revision"])
            for worker, expected, radius in zip(workers, candidates, (.07, .08)):
                self.assertTrue(worker.prepared["accept"])
                self.assertEqual(worker.prepared["program"], expected.to_payload())
                state = worker.prepared["run"]
                self.assertEqual(state["program_revision"], expected.program_revision)
                self.assertEqual(state["valid_until_seconds"], "2")
                self.assertEqual(state["last_valid_state"]["objects"][SELECTED]["geometry"]["radius"], radius)
                self.assertEqual(state["last_valid_state"]["objects"]["first"]["position_m"], [-1, .4, 0])
            self.release(workers[0], threads[0])
            winner = self.service.handle(requests[0])
            self.assert_success(winner)
            self.release(workers[1], threads[1])
            loser = self.service.handle(requests[1])
        self.assert_code(loser, "OKL-E-REVISION")
        self.assertEqual(winner["program_revision"], candidates[0].program_revision)
        self.assertEqual(loser["program_revision"], candidates[1].program_revision)
        self.assertEqual(loser["accepted_program_revision"], winner["program_revision"])
        self.assertEqual(self.service.accepted_revision(PROJECT), winner["program_revision"])
        for candidate in candidates:
            retained = self.service.read_program(PROJECT, candidate.program_revision)
            self.assertEqual(retained.to_payload(), candidate.to_payload())
            self.assertIn(retained.modules[0].revision, retained.entry.text)
        run = self.service.get_run(PROJECT, loser["run_id"])
        self.assertEqual(run, loser["result"]["run_state"])
        self.assertTrue(run["candidate_only"])
        self.assertEqual(run["program_revision"], candidates[1].program_revision)
        ordinary = self.service.handle(self.request("evaluate", program_revision=candidates[1].program_revision,
                                                    run_id=None, until_seconds="0"))
        self.assert_code(ordinary, "OKL-E-REVISION")

    def test_competing_run_extensions_report_the_actual_committed_program_prefix(self):
        _, created = self.create()
        revision = created["program_revision"]
        reset = self.service.handle(self.request("reset", program_revision=revision))
        self.assert_success(reset)
        run_id = reset["run_id"]
        original = self.service.get_run(PROJECT, run_id)
        requests = [self.request("evaluate", program_revision=revision, run_id=run_id, until_seconds=until)
                    for until in ("0.5", "1")]
        with self.prepared(requests) as (workers, threads):
            self.assertEqual(self.service.get_run(PROJECT, run_id), original)
            self.assertEqual([worker.prepared["run"]["valid_until_seconds"] for worker in workers], ["0.5", "1"])
            self.release(workers[0], threads[0])
            winner = self.service.handle(requests[0])
            self.assert_success(winner)
            self.release(workers[1], threads[1])
            loser = self.service.handle(requests[1])
        self.assert_code(loser, "OKL-E-SAMPLE")
        retained = self.service.get_run(PROJECT, run_id)
        self.assertEqual(retained["program_revision"], revision)
        self.assertEqual(retained["valid_until_seconds"], "0.5")
        self.assertEqual(retained["last_valid_state"]["objects"]["first"]["position_m"], [-1, .1, 0])
        self.assertEqual(loser["result"]["run_state"], retained)
        self.assertEqual(winner["result"]["run_state"], retained)
        self.assertFalse(loser["result"]["run_advance_committed"])
        self.assertIsNone(loser["achieved_level"])

    def test_request_termination_cannot_commit_a_computed_program_run_extension(self):
        _, created = self.create()
        revision = created["program_revision"]
        reset = self.service.handle(self.request("reset", program_revision=revision))
        self.assert_success(reset)
        run_id = reset["run_id"]
        original = self.service.get_run(PROJECT, run_id)
        for budget in ("max_operations", "max_elapsed_ms"):
            with self.subTest(budget=budget), _LateTermination(self.path, budget) as worker:
                request = self.request("evaluate", program_revision=revision, run_id=run_id, until_seconds="1")
                self.assertEqual(self.service.submit(request)["status"], "queued")
                self.assertTrue(worker.work_next())
                self.assertEqual(worker.prepared["valid_until_seconds"], "1")
                self.assertEqual(worker.prepared["last_valid_state"]["objects"]["first"]["position_m"], [-1, .2, 0])
                response = self.service.handle(request)
            self.assert_code(response, "OKL-E-RESOURCE")
            self.assertEqual(response["diagnostics"][-1]["details"]["budget"], budget)
            self.assertTrue(response["diagnostics"][-1]["details"]["request_terminated"])
            self.assertEqual(response["result"]["run_state"], original)
            self.assertEqual(self.service.get_run(PROJECT, run_id), original)
            self.assertEqual(self.service.accepted_revision(PROJECT), revision)

    def test_cancellation_after_complete_bundle_computation_prevents_acceptance(self):
        _, created = self.create()
        request, candidate = self.candidate("0.07")
        with self.prepared([request]) as (workers, threads):
            worker = workers[0]
            self.assertEqual(worker.prepared["program"], candidate.to_payload())
            self.assertTrue(worker.prepared["accept"])
            cancelled = self.service.handle(self.request("cancel", target_request_id=request["request_id"]))
            self.assert_success(cancelled)
            self.assertEqual(cancelled["result"]["disposition"], "cancellation_requested")
            self.release(worker, threads[0])
        terminal = self.service.handle(request)
        self.assertEqual(terminal["status"], "cancelled")
        self.assertEqual(terminal["program_revision"], candidate.program_revision)
        self.assertEqual(terminal["accepted_program_revision"], created["program_revision"])
        self.assertIsNone(terminal["run_id"])
        self.assertIsNone(terminal["result"])
        self.assertEqual(self.service.read_program(PROJECT, candidate.program_revision).to_payload(), candidate.to_payload())
        self.assertEqual(self.service.accepted_revision(PROJECT), created["program_revision"])
        with self.assertRaises(ProtocolError):
            self.service.get_run(PROJECT, worker.prepared["run"]["run_id"])
        ordinary = self.service.handle(self.request("evaluate", program_revision=candidate.program_revision,
                                                    run_id=None, until_seconds="0"))
        self.assert_code(ordinary, "OKL-E-REVISION")

    def test_oversized_control_response_rolls_back_real_pending_cancellation(self):
        self.create()
        request, candidate = self.candidate("0.07")
        with self.prepared([request]) as (workers, threads):
            with _OversizedControl(self.path) as controller:
                cancel_request = self.request("cancel", target_request_id=request["request_id"])
                rejected = controller.handle(cancel_request)
                self.assert_code(rejected, "OKA-E-RESOURCE")
                self.assertFalse(rejected["protocol_error"]["details"]["effects_committed"])
                self.assertEqual(controller.handle(cancel_request), rejected)
            status = self.service.handle(self.request("status", target_request_id=request["request_id"]))
            self.assertEqual(status["result"]["target_status"], "running")
            self.assertFalse(status["result"]["target"]["progress"]["cancellation_requested"])
            self.release(workers[0], threads[0])
        result = self.service.handle(request)
        self.assert_success(result)
        self.assertEqual(self.service.accepted_revision(PROJECT), candidate.program_revision)

    def test_persisted_queued_bundle_resumes_in_a_new_python_process(self):
        request = self.request("create", bundle=self.payload, expected_program_revision=None, requested_level="evaluated")
        receipt = self.service.submit(request)
        self.assertEqual(receipt["status"], "queued")
        self.service.close()
        code = '''import json, sys
from pathlib import Path
from ontokin.program_agent import ProgramAgentService
request = json.load(sys.stdin)
with ProgramAgentService(Path(sys.argv[1])) as service:
    print(json.dumps(service.handle(request)))
'''
        process = subprocess.run([sys.executable, "-c", code, str(self.path)], cwd=ROOT,
                                 input=json.dumps(request), text=True, capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        response = json.loads(process.stdout)
        self.assert_success(response)
        self.assertEqual(response["program_revision"], self.original.program_revision)
        self.reopen()
        self.assertEqual(self.service.handle(request), response)
        self.assertEqual(self.service.read_program(PROJECT, response["program_revision"]).to_payload(), self.payload)
        self.assertFalse(self.service.work_next())

    def test_proven_dead_worker_is_fenced_but_a_live_worker_is_not_stolen(self):
        _, created = self.create("evaluated")
        initial_run = self.service.get_run(PROJECT, created["run_id"])
        request, candidate = self.candidate("0.07")
        self.assertEqual(self.service.submit(request)["status"], "queued")
        with self.prepared_process() as (process, prepared):
            self.assertEqual(prepared["program_revision"], candidate.program_revision)
            with ProgramAgentService(self.path) as peer:
                status = peer.handle(self.request("status", target_request_id=request["request_id"]))
                self.assertEqual(status["result"]["target_status"], "running")
                self.assertFalse(peer.work_next(), "A live process retains its exclusive request ownership")
                self.assertEqual(peer.accepted_revision(PROJECT), created["program_revision"])
            process.kill()
            process.wait(timeout=5)
        self.reopen()
        status = self.service.handle(self.request("status", target_request_id=request["request_id"]))
        self.assertEqual(status["result"]["target_status"], "unknown_outcome")
        self.assertEqual(self.service.handle(request)["status"], "unknown_outcome")
        self.assertFalse(self.service.work_next())
        self.assertEqual(self.service.get_run(PROJECT, created["run_id"]), initial_run)
        self.assertEqual(self.service.accepted_revision(PROJECT), created["program_revision"])
        self.assertEqual(self.service.read_program(PROJECT, candidate.program_revision).to_payload(), candidate.to_payload())
        with self.assertRaises(ProtocolError):
            self.service.get_run(PROJECT, prepared["run_id"])
        changed = {**request, "requested_level": "represented"}
        self.assert_code(self.service.handle(changed), "OKL-E-REQUEST-ID")
        deliberate = {**request, "request_id": f"reconciled-{next(self.serial)}"}
        accepted = self.service.handle(deliberate)
        self.assert_success(accepted)
        self.assertEqual(self.service.accepted_revision(PROJECT), candidate.program_revision)

    def test_exact_retry_and_expired_identity_never_replay_program_effects(self):
        request, original = self.create("evaluated")
        initial_run = self.service.get_run(PROJECT, original["run_id"])
        edit_request, candidate = self.candidate("0.07")
        edited = self.service.handle(edit_request)
        self.assert_success(edited)
        self.reopen()
        # Canonical JSON ignores object field order, but preserves the complete
        # operation payload and the original terminal response context.
        reordered = {key: request[key] for key in reversed(request)}
        self.assertEqual(self.service.handle(reordered), original)
        self.assertEqual(self.service.accepted_revision(PROJECT), candidate.program_revision)
        cancelled = self.service.handle(self.request("cancel", target_request_id=edit_request["request_id"]))
        self.assert_success(cancelled)
        self.assertEqual(cancelled["result"]["disposition"], "already_completed")
        self.assertEqual(cancelled["result"]["target"], edited)
        self.assertTrue(self.service.expire_result(PROJECT, request["request_id"]))
        self.reopen()
        tombstone = self.service.handle(request)
        self.assertEqual(tombstone["status"], "unknown_outcome")
        self.assertEqual(tombstone["program_revision"], original["program_revision"])
        self.assertEqual(tombstone["accepted_program_revision"], candidate.program_revision)
        self.assertFalse(tombstone["protocol_error"]["details"]["replay_permitted"])
        self.assertFalse(self.service.work_next())
        self.assertEqual(self.service.get_run(PROJECT, original["run_id"]), initial_run)
        self.assertEqual(self.service.read_program(PROJECT, original["program_revision"]).to_payload(), self.payload)
        self.assert_code(self.service.handle({**request, "requested_level": "represented"}), "OKL-E-REQUEST-ID")

    def test_changed_engine_preserves_program_evidence_but_fences_old_work(self):
        create_request, created = self.create("evaluated")
        revision = created["program_revision"]
        run = self.service.get_run(PROJECT, created["run_id"])
        queued = self.request("reset", program_revision=revision)
        self.assertEqual(self.service.submit(queued)["status"], "queued")
        alternate = copy.deepcopy(self.service.implementation)
        alternate["source_code_sha256"] = "sha256:" + "0" * 64
        self.assertNotEqual(alternate, self.service.implementation)
        # Only engine identity differs; all parsing/evaluation/store code stays real.
        with instrument("ontokin.agent.implementation_identity", return_value=alternate):
            peer = ProgramAgentService(self.path)
        try:
            self.assertTrue(peer.work_next())
            self.assert_code(peer.handle(queued), "OKA-E-ENGINE")
            self.assertEqual(peer.handle(create_request), created)
            self.assertEqual(peer.get_run(PROJECT, created["run_id"]), run)
            blocked = peer.handle(self.request("evaluate", program_revision=revision,
                                               run_id=created["run_id"], until_seconds="2"))
            self.assert_code(blocked, "OKL-E-SAMPLE")
            self.assertEqual(peer.read_program(PROJECT, revision).to_payload(), self.payload)
            fresh = peer.handle(self.request("reset", program_revision=revision))
            self.assert_success(fresh)
            self.assertEqual(fresh["result"]["run_state"]["implementation"], alternate)
            self.assertEqual(fresh["result"]["run_state"]["program_revision"], revision)
        finally:
            peer.close()


if __name__ == "__main__":
    unittest.main()
