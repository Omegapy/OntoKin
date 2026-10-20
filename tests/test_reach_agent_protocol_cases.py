"""Execute all 42 adopted LP steps without editing their frozen templates."""
from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from ontokin.construction import ConstructionBudget
from ontokin.json_limits import measure_json
from ontokin import program_runtime
from reach_agent_support import (CASES, PROTOCOL_CASES, STEPS, ReachAgentFixture,
                                 reach_records, source_case)


class ReachProtocolCaseTests(ReachAgentFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.bindings = {}
        self.receipts = {}
        self.requests = {}

    def resolve(self, value):
        if isinstance(value, dict):
            if set(value) == {"$fixture_bundle"}:
                return source_case(value["$fixture_bundle"]).to_payload()
            if set(value) == {"$binding"}:
                return copy.deepcopy(self.bindings[value["$binding"]])
            if set(value) == {"$binding_minus_one"}:
                return self.bindings[value["$binding_minus_one"]] - 1
            return {key: self.resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self.resolve(item) for item in value]
        return value

    def step(self, identity):
        row = STEPS[identity]
        request = self.resolve(row["request_template"])
        response = self.service.handle(request)
        self.exchanges.append((request, response))
        self.requests[identity] = request
        self.receipts[identity] = copy.deepcopy(response)
        expected = row["expected"]
        self.assertEqual(response["status"], expected["status"], (identity, response))
        for name in ("accepted_program_revision", "program_revision"):
            if name in expected:
                self.assertEqual(response[name], expected[name], identity)
        for name in ("diagnostic_code", "protocol_error_code"):
            if name in expected:
                self.error(response, expected[name])
        if "reach_code" in expected:
            self.assertIn(expected["reach_code"], [d.get("details", {}).get("reach_code") for d in response["diagnostics"]], identity)
        if "category" in expected:
            self.assertIn(expected["category"], [d["category"] for d in response["diagnostics"]], identity)
        if "phase" in expected:
            self.assertIn(expected["phase"], [d["phase"] for d in response["diagnostics"]], identity)
        run = (response.get("result") or {}).get("run_state")
        for name in ("valid_until_seconds", "valid_until_side"):
            if name in expected:
                self.assertEqual(run[name], expected[name], identity)
        if "run_status" in expected:
            self.assertEqual(run["status"], expected["run_status"], identity)
        prefix = identity.split(".")[0]
        for name, expression in row["capture_bindings"].items():
            if expression == "response.run_id":
                captured = response["run_id"]
                self.assertIsNotNone(captured, identity)
            elif expression in ("complete immutable terminal response", "complete response"):
                captured = copy.deepcopy(response)
            elif expression == "actual returned source.initializer_target":
                captured = response["result"]["items"][0]["source"]["initializer_target"]
            elif expression == "logical_json_entries(complete response)":
                captured = measure_json(response)["entries"]
            else:
                self.fail("Unimplemented frozen capture expression: " + expression)
            self.bindings[prefix + "." + name] = copy.deepcopy(captured)
        return response

    def frozen_run(self, project, identity):
        return copy.deepcopy(self.service._store.read_run(project, identity))

    def test_lp01_failed_prefix_reset_all_nine_steps(self):
        self.step("LP01.01")
        failure = self.step("LP01.02")
        project, run_id = "reach-reconstruction-lp01", failure["run_id"]
        historical = self.frozen_run(project, run_id)
        before = self.step("LP01.03")
        a = self.projection(before, "reach_a")["current"]["value"]
        b = self.projection(before, "reach_b")["current"]["value"]
        self.assertEqual((a["lifecycle"], len(a["claimed_joint_ids"])), ("running", 2))
        self.assertEqual((b["lifecycle"], b["resolved_joint_targets_rad"], b["claimed_joint_ids"]), ("pending", None, []))
        for identity in ("LP01.04", "LP01.05", "LP01.06"):
            self.step(identity)
        reset = self.step("LP01.07")
        self.assertNotEqual(reset["run_id"], run_id)
        prefix = self.step("LP01.08")
        self.assertEqual(prefix["run_id"], reset["run_id"])
        current = self.step("LP01.09")
        self.assertEqual(self.projection(current, "reach_a")["current"]["value"]["lifecycle"], "running")
        self.assertEqual(self.frozen_run(project, run_id), historical)
        self.assertEqual(self.effects(project)["artifacts"], 0)
        self.assertEqual(len(self.receipts), 9)

    def test_lp02_authorized_root_repair_retry_history_all_nine_steps(self):
        before = self.step("LP02.01")
        project = "reach-reconstruction-lp02"
        old_run = self.frozen_run(project, before["run_id"])
        authority = self.step("LP02.02")["result"]["items"][0]["source"]["initializer_target"]
        self.assertTrue(authority["available"])
        self.assertEqual(authority["rendered_path"], 'arms["first"].forearm_length')
        self.step("LP02.03")
        self.step("LP02.04")
        authorized_patch = STEPS["LP02.05"]["request_template"]["patches"][0]
        self.assertEqual(authorized_patch["element_id"], authority["element_id"])
        self.assertEqual(authorized_patch["source_id"], authority["span"]["source_id"])
        self.assertEqual(authorized_patch["source_revision"], authority["span"]["source_revision"])
        self.assertLessEqual(authority["span"]["start_byte"], authorized_patch["start_byte"])
        self.assertGreaterEqual(authority["span"]["end_byte"], authorized_patch["end_byte"])
        edited = self.step("LP02.05")
        effects = self.effects(project)
        self.assertEqual(self.step("LP02.06"), edited)
        self.assertEqual(self.requests["LP02.06"], self.requests["LP02.05"])
        self.assertEqual(self.step("LP02.07")["result"]["target"], edited)
        self.assertEqual(self.effects(project), effects)
        old = self.step("LP02.08")
        new = self.step("LP02.09")
        old_records = {item["element_id"][-1]: item for item in reach_records(old)}
        new_records = {item["element_id"][-1]: item for item in reach_records(new)}
        self.assertEqual(set(old_records), set(new_records))
        same = 0
        for name, record in old_records.items():
            comparison = new_records[name]
            self.assertEqual(record["accepted_program_revision"], edited["program_revision"])
            self.assertFalse(record["candidate_only"])
            if record["chain"]["lengths_m"] == comparison["chain"]["lengths_m"]:
                same += 1
                for field in ("joint_coordinates_rad", "joint_rates_rad_per_s", "resolved_joint_targets_rad"):
                    self.assertEqual(record["current"]["value"][field], comparison["current"]["value"][field])
        self.assertEqual(same, 4)
        original, changed = source_case("P13"), source_case("P20")
        self.assertEqual(self.service.read_program(project, changed.program_revision), changed)
        for source_id in original.sources:
            if source_id != "entry":
                self.assertEqual(original.sources[source_id].raw, changed.sources[source_id].raw)
        self.assertEqual(self.frozen_run(project, before["run_id"]), old_run)
        self.assertEqual(len(self.receipts), 9)

    def test_lp03_accepted_construction_failed_admission_repair_all_five_steps(self):
        self.step("LP03.01")
        failure = self.step("LP03.02")
        project = "reach-reconstruction-lp03"
        historical = self.frozen_run(project, failure["run_id"])
        initial = self.step("LP03.03")
        state = self.projection(initial)["current"]["value"]
        self.assertEqual((state["lifecycle"], state["goal_outcome"], state["claimed_joint_ids"]), ("pending", "pending", []))
        self.assertIsNone(state["resolved_joint_targets_rad"])
        changed = self.step("LP03.04")
        old = self.projection(self.step("LP03.05"))
        self.assert_context(old, source_case("N06"), changed["program_revision"], run=failure["run_id"])
        self.assertEqual(self.frozen_run(project, failure["run_id"]), historical)
        self.assertEqual(self.service.handle(self.requests["LP03.02"]), failure)
        self.assertEqual(len(self.receipts), 5)

    def test_lp04_q03_fixed_128_actions_real_n_and_n_minus_one_all_seven_steps(self):
        self.step("LP04.01")
        evaluated = self.step("LP04.02")
        project = "reach-reconstruction-lp04"
        historical = self.frozen_run(project, evaluated["run_id"])
        measurements = {}
        real_init = ConstructionBudget.__init__
        real_data, real_json = program_runtime._Budget.data, program_runtime._Budget.json
        execute, guard = self.service._execute, self.service._check_task_response

        def measured_step(identity):
            constructors, materializations, prepared, guards = [], [], [], []
            def init(budget, *args, **kwargs):
                real_init(budget, *args, **kwargs)
                constructors.append(budget)
            def data(budget, value):
                result = real_data(budget, value)
                materializations.append(("data", measure_json(result)["entries"]))
                return result
            def json_value(budget, value):
                result = real_json(budget, value)
                materializations.append(("json", measure_json(result)["entries"]))
                return result
            def completed(task, check):
                execute(task, check)
                prepared.append(task.response["status"])
            def checked(task):
                guards.append({"status": task.response["status"], "phase": (task.response.get("progress") or {}).get("phase"),
                               "entries": measure_json(task.response)["entries"]})
                guard(task)
            with patch.object(ConstructionBudget, "__init__", init), patch.object(program_runtime._Budget, "data", data), \
                 patch.object(program_runtime._Budget, "json", json_value), patch.object(self.service, "_execute", completed), \
                 patch.object(self.service, "_check_task_response", checked):
                response = self.step(identity)
            measurements[identity] = {"constructor_counts": [budget.value_entries for budget in constructors],
                                      "materializations": materializations, "prepared": prepared, "guards": guards}
            return response

        baseline = measured_step("LP04.03")
        self.assertEqual(len(list(reach_records(baseline))), 128)
        self.assertEqual(baseline["result"]["total"], 128)
        self.assertFalse(baseline["truncated"])
        self.assertIsNone(baseline["next_cursor"])
        n = self.bindings["LP04.N"]
        exact = measured_step("LP04.04")
        self.assertEqual(measure_json(exact)["entries"], n)
        self.assertEqual(len(list(reach_records(exact))), 128)
        failure = measured_step("LP04.05")
        self.assertFalse(failure["protocol_error"]["details"]["effects_committed"])
        self.assertIsNone(failure["result"])
        self.assertIsNone(failure["run_id"])
        for identity in ("LP04.03", "LP04.04", "LP04.05"):
            measured = measurements[identity]
            self.assertEqual(measured["prepared"], ["succeeded"], measured)
            self.assertTrue(measured["constructor_counts"])
            self.assertTrue(all(0 < count < n for count in measured["constructor_counts"]))
            self.assertTrue(measured["materializations"])
            self.assertTrue(all(count < n for _, count in measured["materializations"]))
        self.assertIn({"status": "succeeded", "phase": "complete", "entries": n}, measurements["LP04.05"]["guards"])
        fields = ("program_revision", "run_id", "selector", "fields", "limit", "time")
        for identity in ("LP04.04", "LP04.05"):
            self.assertEqual({field: self.requests[identity][field] for field in fields},
                             {field: self.requests["LP04.03"][field] for field in fields})
        tiny = self.step("LP04.06")
        self.assertEqual(tiny["status"], "failed")
        codes = [diagnostic["code"] for diagnostic in tiny["diagnostics"]]
        if tiny["protocol_error"]:
            codes.append(tiny["protocol_error"]["code"])
        self.assertTrue({"OKL-E-RESOURCE", "OKA-E-RESOURCE"} & set(codes))
        self.step("LP04.07")
        self.assertEqual(self.frozen_run(project, evaluated["run_id"]), historical)
        self.assertEqual(self.effects(project), {"runs": 1, "artifacts": 0})
        self.assertEqual(len(self.receipts), 7)
        # Kept as test data for the release runner, never substituted for a
        # recorded actual exchange or used to shrink the fixed Q03 query.
        self.q03_measurements = {"complete_response_entries": n, "requests": measurements}

    def test_lp05_candidate_and_later_accepted_history_all_twelve_steps(self):
        self.step("LP05.01")
        candidate = self.step("LP05.02")
        project = "reach-reconstruction-lp05"
        candidate_id = candidate["run_id"]
        historical = self.frozen_run(project, candidate_id)
        self.assertTrue(historical[0]["candidate_only"])
        unrun = self.projection(self.step("LP05.03"))
        self.assertTrue(unrun["candidate_only"])
        self.assertEqual(unrun["current"], {"available": False, "reason": "run_required", "value": None})
        pending = self.projection(self.step("LP05.04"))
        self.assertTrue(pending["candidate_only"])
        self.assertEqual(pending["current"]["value"]["lifecycle"], "pending")
        for identity in ("LP05.05", "LP05.06", "LP05.07"):
            self.step(identity)
        accepted = self.step("LP05.08")
        now = self.projection(self.step("LP05.09"))
        self.assert_context(now, source_case("N06"), accepted["program_revision"], run=candidate_id)
        self.assertFalse(now["candidate_only"])
        self.assertEqual(self.frozen_run(project, candidate_id), historical)
        self.assertTrue(self.service.get_run(project, candidate_id)["candidate_only"])
        self.assertEqual(self.step("LP05.10")["result"]["target"], candidate)
        stale = self.step("LP05.11")
        self.assertEqual(stale["result"]["run_state"], historical[0])
        reset = self.step("LP05.12")
        self.assertNotEqual(reset["run_id"], candidate_id)
        self.assertFalse(reset["result"]["run_state"]["candidate_only"])
        self.assertEqual(self.frozen_run(project, candidate_id), historical)
        self.assertEqual(self.service.handle(self.requests["LP05.02"]), candidate)
        self.assertEqual(len(self.receipts), 12)

    def test_frozen_protocol_inventory_is_exactly_forty_two_steps(self):
        self.assertEqual([len(case["steps"]) for case in PROTOCOL_CASES], [9, 9, 5, 7, 12])
        self.assertEqual(len(STEPS), 42)


if __name__ == "__main__":
    unittest.main()
