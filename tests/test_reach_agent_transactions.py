"""Actual commit fencing, immutable history and complete response rollback."""
import copy
import unittest
from unittest.mock import patch

from ontokin.json_limits import measure_json
from reach_agent_support import ReachAgentFixture, exact_patch, source_case


class ReachAgentTransactionTests(ReachAgentFixture, unittest.TestCase):
    def test_cancel_after_computation_prevents_acceptance_and_run(self):
        program = source_case("P01")
        request = self.request("create", bundle=program.to_payload(), expected_program_revision=None,
                               requested_level="evaluated")
        original = self.service._execute
        prepared = []
        def execute(task, check):
            original(task, check)
            prepared.append((task.accept, task.run is not None))
            self.success(self.send("cancel", target_request_id=request["request_id"]))
        with patch.object(self.service, "_execute", side_effect=execute):
            response = self.service.handle(request)
        self.assertEqual(prepared, [(True, True)])
        self.assertEqual(response["status"], "cancelled")
        self.assertIsNone(response["run_id"])
        self.assertIsNone(response["result"])
        self.assertIsNone(self.service.accepted_revision("reach"))
        self.assertEqual(self.effects(), {"runs": 0, "artifacts": 0})
        self.assertEqual(self.service.handle(request), response)

    def test_cancel_tentative_extension_preserves_stored_run_and_context(self):
        program, _ = self.create()
        prior = self.evaluate(program, "0.5")
        historical = copy.deepcopy(self.service._store.read_run("reach", prior["run_id"]))
        request = self.request("evaluate", program_revision=program.program_revision,
                               run_id=prior["run_id"], until_seconds="2")
        original = self.service._finish
        def finish(task):
            if task.request["request_id"] == request["request_id"]:
                self.success(self.send("cancel", target_request_id=request["request_id"]))
            return original(task)
        with patch.object(self.service, "_finish", side_effect=finish):
            response = self.service.handle(request)
        self.assertEqual(response["status"], "cancelled")
        self.assertEqual(self.service._store.read_run("reach", prior["run_id"]), historical)
        self.assertEqual(self.service.accepted_revision("reach"), program.program_revision)

    def test_competing_acceptance_binds_isolated_candidate_to_real_winning_head(self):
        original, _ = self.create("P01")
        candidate, winner = source_case("P02"), source_case("P03")
        scene = ["planar-reach-fixture", "demo"]
        request = self.request("edit", expected_program_revision=original.program_revision,
            patches=[exact_patch(original, candidate, scene)], requested_level="evaluated")
        finish = self.service._finish
        competing = []
        def publish_competitor(task):
            if task.request["request_id"] == request["request_id"]:
                competing.append(self.success(self.send("edit", expected_program_revision=original.program_revision,
                    patches=[exact_patch(original, winner, scene)], requested_level="constructed")))
            return finish(task)
        with patch.object(self.service, "_finish", side_effect=publish_competitor):
            response = self.error(self.service.handle(request), "OKL-E-REVISION")
        self.assertEqual(len(competing), 1)
        self.assertEqual(response["accepted_program_revision"], winner.program_revision)
        self.assertEqual(response["program_revision"], candidate.program_revision)
        run = response["result"]["run_state"]
        self.assertTrue(run["candidate_only"])
        self.assertEqual(self.service.get_run("reach", response["run_id"]), run)
        for record in run["last_valid_state"]["reaches"].values():
            self.assert_context(record, candidate, winner.program_revision, candidate=True, run=response["run_id"])
        self.assertEqual(self.service.accepted_revision("reach"), winner.program_revision)

    def test_competing_run_advance_returns_unchanged_winning_descriptor(self):
        program, _ = self.create()
        prior = self.evaluate(program, "0.5")
        request = self.request("evaluate", program_revision=program.program_revision,
                               run_id=prior["run_id"], until_seconds="1.5")
        finish = self.service._finish
        competing = []
        def publish_competitor(task):
            if task.request["request_id"] == request["request_id"]:
                competing.append(self.evaluate(program, "1", prior["run_id"]))
            return finish(task)
        with patch.object(self.service, "_finish", side_effect=publish_competitor):
            response = self.error(self.service.handle(request), "OKL-E-SAMPLE")
        self.assertEqual(len(competing), 1)
        expected = competing[0]["result"]["run_state"]
        self.assertFalse(response["result"]["run_advance_committed"])
        self.assertEqual(response["result"]["run_state"], expected)
        self.assertEqual(self.service.get_run("reach", prior["run_id"]), expected)
        self.assertEqual(expected["valid_until_seconds"], "1")

    def test_complete_response_guard_rolls_back_acceptance_and_serialized_run(self):
        program, baseline = self.create("P24", level="evaluated")
        n = measure_json(baseline)["entries"]
        request = self.request("create", project_id="limited", bundle=program.to_payload(),
            expected_program_revision=None, requested_level="evaluated", budgets={"max_value_entries": n - 1})
        original = self.service._execute
        prepared = []
        def execute(task, check):
            original(task, check)
            prepared.append((task.accept, task.run is not None))
        with patch.object(self.service, "_execute", side_effect=execute):
            failure = self.error(self.service.handle(request), "OKA-E-RESOURCE")
        self.assertEqual(prepared, [(True, True)])
        self.assertFalse(failure["protocol_error"]["details"]["effects_committed"])
        self.assertIsNone(failure["accepted_program_revision"])
        self.assertIsNone(failure["run_id"])
        self.assertIsNone(failure["result"])
        self.assertEqual(self.effects("limited"), {"runs": 0, "artifacts": 0})
        self.assertFalse(self.service._store.source_accepted_once("limited", program.program_revision))
        exact = self.success(self.service.handle({**request, "request_id": "exact", "budgets": {"max_value_entries": n}}))
        self.assertEqual(measure_json(exact)["entries"], n)
        self.assertEqual(self.service.get_run("limited", exact["run_id"]), exact["result"]["run_state"])
        self.assertTrue(self.service._store.source_accepted_once("limited", program.program_revision))

    def test_request_work_failure_preserves_prior_source_and_run(self):
        program, _ = self.create()
        prior = self.evaluate(program, "0.5")
        historical = copy.deepcopy(self.service._store.read_run("reach", prior["run_id"]))
        response = self.error(self.send("evaluate", program_revision=program.program_revision,
            run_id=prior["run_id"], until_seconds="3", budgets={"max_operations": 1}), "OKL-E-RESOURCE")
        self.assertEqual(response["status"], "failed")
        self.assertEqual(self.service._store.read_run("reach", prior["run_id"]), historical)
        self.assertEqual(self.effects(), {"runs": 1, "artifacts": 0})
        self.assertEqual(self.service.accepted_revision("reach"), program.program_revision)


if __name__ == "__main__":
    unittest.main()
