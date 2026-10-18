"""Real semantic work at the agent service's transaction boundaries.

Event gates order commits after both workers finish actual parsing, validation,
and evaluation. No test replaces successful semantic work with a canned result.
The deadline probes alter only the work clock/counter after real computation.
"""

from __future__ import annotations

from contextlib import contextmanager
import copy
import itertools
from pathlib import Path
import tempfile
import threading
import time
import unittest

from ontokin.agent import AgentService


PROJECT = "transaction-tests"
SOURCE = '''ontokin "0.1";
module Transactions @ "transactions";
profile "core-0.1";
class Ball @ "ball" {
    public param radius @ "radius": Length = 0.2[m];
    geometry = sphere(self.radius);
}
class Cube @ "cube" {
    public param radius @ "radius": Length = 0.2[m];
    geometry = box(vec3(self.radius, self.radius, self.radius));
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], -9.81[m/s^2], 0[m/s^2]);
    object first @ "first": Ball {
        placement = pose(world, vec3(0[m], 2[m], 0[m]), quat(1, 0, 0, 0));
    }
    action travel @ "travel" = move(first, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    at 0[s] sequence { start travel; }
}
'''
FIRST_ID = ["transactions", "demo", "first"]
BALL_ID = ["transactions", "definitions", "ball"]
RADIUS_ID = BALL_ID + ["radius"]


def patch(source: str, old: str, new: str, ids: list[str]) -> dict:
    start = source.encode("utf-8").index(old.encode("utf-8"))
    return {"element_id": ids, "start_byte": start, "end_byte": start + len(old.encode("utf-8")),
            "expected_text": old, "replacement": new}


class _FinishGate(AgentService):
    """Run the real service up to its transaction, then await an explicit gate."""

    def __init__(self, path):
        self.ready = threading.Event()
        self.release = threading.Event()
        self.prepared = None
        self.worker_errors = []
        super().__init__(path)

    def _finish(self, task):
        self.prepared = {"response": copy.deepcopy(task.response), "run": copy.deepcopy(task.run),
                         "accept": task.accept, "source": None if task.source is None else task.source.text}
        self.ready.set()
        if not self.release.wait(10):
            raise TimeoutError("Test commit gate was not released")
        super()._finish(task)

    def do_work(self):
        try:
            if not self.work_next():
                raise AssertionError("The synchronized worker did not claim queued work")
        except BaseException as error:
            self.worker_errors.append(error)
            self.ready.set()


class _LateTermination(AgentService):
    """Exhaust the actual request check after a real computed run is prepared."""

    def __init__(self, path, budget_name):
        self.budget_name = budget_name
        self.prepared = None
        super().__init__(path)

    def _execute(self, task, check):
        super()._execute(task, check)
        self.prepared = copy.deepcopy(task.run)
        if self.budget_name == "max_operations":
            check.operations = check.limits["max_operations"]
        else:
            check.started = time.monotonic() - check.limits["max_elapsed_ms"] / 1000 - 1
        # work_next's real final check performs the termination.


class _EarlyTermination(AgentService):
    """A real budget failure before an unknown run can be looked up."""

    def _execute(self, task, check):
        check.operations = check.limits["max_operations"]
        check()
        super()._execute(task, check)  # Unreachable if the budget check works.


class AgentTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-agent-transactions-")
        self.path = Path(self.temporary.name) / "state"
        self.service = AgentService(self.path)
        self.serial = itertools.count(1)

    def tearDown(self):
        self.service.close()
        self.temporary.cleanup()

    def request(self, operation, **fields):
        return {"schema_version": "ontokin.agent/0.1", "project_id": PROJECT,
                "request_id": f"transaction-{next(self.serial)}", "operation": operation, **fields}

    def assert_success(self, response):
        self.assertEqual(response["status"], "succeeded", response)
        self.assertIsNone(response["protocol_error"], response)

    def assert_code(self, response, code):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        codes = [diagnostic["code"] for diagnostic in response["diagnostics"]]
        if response["protocol_error"]:
            codes.append(response["protocol_error"]["code"])
        self.assertIn(code, codes, response)

    def create(self):
        response = self.service.handle(self.request("create", filename="scene.ok", source=SOURCE,
                                                     expected_revision=None, requested_level="represented"))
        self.assert_success(response)
        return response["source_revision"]

    def reset(self, revision):
        response = self.service.handle(self.request("reset", source_revision=revision))
        self.assert_success(response)
        return response["run_id"]

    @contextmanager
    def prepared_pair(self, requests):
        workers = [_FinishGate(self.path), _FinishGate(self.path)]
        threads = []
        try:
            for request in requests:
                self.assertEqual(self.service.submit(request)["status"], "queued")
            # Assign the ordered requests deterministically; neither may commit
            # until the caller releases it after both real results are ready.
            for worker in workers:
                thread = threading.Thread(target=worker.do_work, daemon=True)
                threads.append(thread)
                thread.start()
                self.assertTrue(worker.ready.wait(10), "Worker did not reach the real commit boundary")
                self.assertEqual(worker.worker_errors, [])
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
        self.assertFalse(thread.is_alive(), "Worker did not complete its released transaction")
        self.assertEqual(worker.worker_errors, [])

    def test_two_prepared_candidates_commit_one_head_and_retain_loser_evidence(self):
        revision = self.create()
        requests = [self.request("edit", expected_revision=revision,
                                 patches=[patch(SOURCE, "0.2[m]", radius, RADIUS_ID)],
                                 requested_level="evaluated") for radius in ("0.3[m]", "0.4[m]")]
        with self.prepared_pair(requests) as (workers, threads):
            self.assertEqual(self.service.accepted_revision(PROJECT), revision)
            for worker in workers:
                self.assertTrue(worker.prepared["accept"])
                run = worker.prepared["run"]
                self.assertEqual(run["valid_until_seconds"], "2")
                self.assertEqual(run["last_valid_state"]["objects"]["first"]["position_m"], [2, 2, 0])
            self.release(workers[0], threads[0])
            winner = self.service.handle(requests[0])
            self.assert_success(winner)
            self.release(workers[1], threads[1])
            loser = self.service.handle(requests[1])
        self.assert_code(loser, "OKL-E-REVISION")
        self.assertEqual(self.service.accepted_revision(PROJECT), winner["source_revision"])
        self.assertEqual(loser["accepted_revision"], winner["source_revision"])
        self.assertNotEqual(loser["source_revision"], winner["source_revision"])
        self.assertIn("source not accepted", loser["result"]["acceptance"])
        retained = self.service.get_run(PROJECT, loser["run_id"])
        self.assertEqual(retained, loser["result"]["run_state"])
        self.assertTrue(retained["candidate_only"])
        self.assertEqual(retained["source_revision"], loser["source_revision"])
        self.assertEqual(retained["last_valid_state"]["objects"]["first"]["geometry"]["radius"], .4)
        self.assertIn("radius @ \"radius\": Length = 0.4[m]", self.service.read_source(PROJECT, loser["source_revision"]).text)

    def test_two_prepared_run_extensions_return_the_actual_committed_interval(self):
        revision = self.create()
        run_id = self.reset(revision)
        original = self.service.get_run(PROJECT, run_id)
        requests = [self.request("evaluate", source_revision=revision, run_id=run_id,
                                 until_seconds=until) for until in ("0.5", "1")]
        with self.prepared_pair(requests) as (workers, threads):
            self.assertEqual(self.service.get_run(PROJECT, run_id), original)
            self.assertEqual([worker.prepared["run"]["valid_until_seconds"] for worker in workers], ["0.5", "1"])
            self.release(workers[0], threads[0])
            winner = self.service.handle(requests[0])
            self.assert_success(winner)
            self.release(workers[1], threads[1])
            loser = self.service.handle(requests[1])
        self.assert_code(loser, "OKL-E-SAMPLE")
        retained = self.service.get_run(PROJECT, run_id)
        self.assertEqual(retained["valid_until_seconds"], "0.5")
        self.assertEqual(retained["last_valid_state"]["objects"]["first"]["position_m"], [.5, 2, 0])
        self.assertEqual(loser["run_id"], run_id)
        self.assertIsNone(loser["achieved_level"])
        self.assertFalse(loser["result"]["run_advance_committed"])
        self.assertEqual(loser["result"]["run_state"], retained)
        self.assertEqual(winner["result"]["run_state"], retained)

    def test_late_deadline_or_operation_budget_cannot_commit_computed_advancement(self):
        revision = self.create()
        run_id = self.reset(revision)
        original = self.service.get_run(PROJECT, run_id)
        for budget_name in ("max_operations", "max_elapsed_ms"):
            with self.subTest(budget=budget_name), _LateTermination(self.path, budget_name) as worker:
                request = self.request("evaluate", source_revision=revision, run_id=run_id, until_seconds="1")
                self.assertEqual(self.service.submit(request)["status"], "queued")
                self.assertTrue(worker.work_next())
                self.assertEqual(worker.prepared["valid_until_seconds"], "1")
                self.assertEqual(worker.prepared["last_valid_state"]["objects"]["first"]["position_m"], [1, 2, 0])
                result = self.service.handle(request)
            self.assert_code(result, "OKL-E-RESOURCE")
            self.assertEqual(result["diagnostics"][-1]["details"]["budget"], budget_name)
            self.assertTrue(result["diagnostics"][-1]["details"]["request_terminated"])
            self.assertEqual(self.service.get_run(PROJECT, run_id), original)
            self.assertEqual(result["result"]["run_state"], original)
            self.assertEqual(self.service.accepted_revision(PROJECT), revision)

    def test_early_resource_error_does_not_look_up_an_unresolved_run_unsafely(self):
        revision = self.create()
        request = self.request("evaluate", source_revision=revision, run_id="run:absent", until_seconds="1")
        self.assertEqual(self.service.submit(request)["status"], "queued")
        with _EarlyTermination(self.path) as worker:
            self.assertTrue(worker.work_next())
            # submit reads the retained result without attempting new work.
            result = self.service.submit(request)
            self.assert_code(result, "OKL-E-RESOURCE")
            self.assertIsNone(result["run_id"])
            self.assertIsNone(result["result"]["run_state"])
        self.assertEqual(self.service.accepted_revision(PROJECT), revision)

    def test_identical_candidate_bytes_have_one_canonical_filename(self):
        invalid = SOURCE.replace("Length = 0.2[m]", "Length = 1[kg]", 1)
        responses = []
        for filename in ("first-name.ok", "second-name.ok"):
            response = self.service.handle(self.request("create", filename=filename, source=invalid,
                                                       expected_revision=None, requested_level="represented"))
            self.assert_code(response, "OKL-E-UNIT")
            responses.append(response)
        self.assertEqual(responses[0]["source_revision"], responses[1]["source_revision"])
        source = self.service.read_source(PROJECT, responses[0]["source_revision"])
        self.assertEqual(source.filename, "first-name.ok")
        self.assertEqual(source.text, invalid)
        for response in responses:
            for diagnostic in response["diagnostics"]:
                self.assertEqual(diagnostic["primary"]["file"], source.filename)
                self.assertEqual(diagnostic["source_revision"], source.revision)
        inspected = self.service.handle(self.request("inspect", source_revision=source.revision,
                                                      selector={}, fields=["source"], limit=100))
        self.assert_success(inspected)
        self.assertEqual(inspected["result"]["filename"], source.filename)
        self.assertEqual(inspected["result"]["source_text"], source.text)

    def test_nominal_replacement_requires_new_key_but_lexical_rename_preserves_identity(self):
        revision = self.create()
        replaced = self.service.handle(self.request("edit", expected_revision=revision,
            patches=[patch(SOURCE, 'object first @ "first": Ball', 'object first @ "first": Cube', FIRST_ID)],
            requested_level="evaluated"))
        self.assert_code(replaced, "OKL-E-ID")
        self.assertEqual(self.service.accepted_revision(PROJECT), revision)
        self.assertIn('object first @ "first": Cube', self.service.read_source(PROJECT, replaced["source_revision"]).text)
        renamed = self.service.handle(self.request("edit", expected_revision=revision,
            patches=[patch(SOURCE, "class Ball @", "class Orb @", BALL_ID),
                     patch(SOURCE, 'object first @ "first": Ball', 'object first @ "first": Orb', FIRST_ID)],
            requested_level="evaluated"))
        self.assert_success(renamed)
        inspected = self.service.handle(self.request("inspect", source_revision=renamed["source_revision"],
            selector={"element_id": FIRST_ID}, fields=["identity"], limit=1))
        self.assert_success(inspected)
        identity = inspected["result"]["items"][0]["identity"]
        self.assertEqual(identity["definition_id"], BALL_ID)
        self.assertEqual(identity["element_id"], FIRST_ID)
        self.assertEqual(identity["class_name"], "Orb")
        self.assertEqual(renamed["result"]["run_state"]["last_valid_state"]["objects"]["first"]["position_m"], [2, 2, 0])


if __name__ == "__main__":
    unittest.main()
