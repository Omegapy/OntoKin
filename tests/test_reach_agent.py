"""Actual source, run and repair workflows through the explicit reach service."""
import copy
import unittest

from ontokin.bundle import load_bundle
from reach_agent_support import (CASES, PROTOCOL, PROFILE, ReachAgentFixture,
                                 exact_patch, reach_records, source_case)


class ReachAgentTests(ReachAgentFixture, unittest.TestCase):
    def test_construction_unrun_and_reset_have_distinct_observation_contexts(self):
        program, created = self.create()
        self.assertIsNone(created["run_id"])
        initial = created["result"]["initial_state"]["reaches"]["reach"]
        self.assert_context(initial, program, program.program_revision, kind="constructed_initial")
        state = initial["current"]["value"]
        self.assertEqual(state["observation"]["time_seconds"], "0")
        self.assertEqual(state["observation"]["side"], "before")
        self.assertEqual(state["lifecycle"], "pending")
        self.assertEqual(state["goal_outcome"], "pending")
        for name in ("resolved_joint_targets_rad", "start_coordinates_rad", "start_time_seconds",
                     "elapsed_seconds", "completion_time_seconds", "current_residual_m", "terminal_result"):
            self.assertIsNone(state[name], name)
        unsampled = self.success(self.actions(program))
        projection = self.projection(unsampled)
        self.assert_context(projection, program, program.program_revision)
        self.assertEqual(projection["current"], {"available": False, "reason": "run_required", "value": None})
        self.assertEqual(self.effects(), {"runs": 0, "artifacts": 0})
        reset = self.success(self.send("reset", program_revision=program.program_revision))
        run = reset["result"]["run_state"]
        self.assert_context(run["last_valid_state"]["reaches"]["reach"], program,
                            program.program_revision, run=reset["run_id"])
        self.assertEqual(self.service.get_run("reach", reset["run_id"]), run)
        self.assertEqual(run["valid_until_seconds"], "0")
        self.assertEqual(run["valid_until_side"], "before")

    def test_before_after_complete_projection_and_persisted_run_agree(self):
        program, created = self.create(level="evaluated")
        run_id = created["run_id"]
        run = created["result"]["run_state"]
        self.assertEqual(self.service.get_run("reach", run_id), run)
        stored = copy.deepcopy(run)
        for time, side, lifecycle, outcome in (("0", "before", "pending", "pending"),
                ("0", "after", "running", "active"), ("1", "after", "running", "active"),
                ("2", "before", "running", "active"), ("2", "after", "completed", "satisfied")):
            with self.subTest(time=time, side=side):
                response = self.success(self.actions(program, run=run_id, time=time, side=side))
                record = self.projection(response)
                self.assert_context(record, program, program.program_revision, run=run_id)
                self.assertEqual(record["kind"], "reach_planar")
                self.assertEqual(record["channel"], "joint_coordinates")
                self.assertEqual(record["element_id"], ["planar-reach-fixture", "demo", "reach"])
                self.assertEqual(record["source_location"]["source_revision"], program.entry.revision)
                state = record["current"]["value"]
                self.assertEqual(state["observation"], {"time_seconds": time, "side": side,
                    "run_id": run_id, "context_kind": "run_sample"})
                self.assertEqual((state["lifecycle"], state["goal_outcome"]), (lifecycle, outcome))
                self.assertEqual(len(state["claimed_joint_ids"]), 2 if lifecycle == "running" else 0)
                if lifecycle == "completed":
                    self.assertEqual(state["terminal_result"]["outcome"], "satisfied")
                    self.assertLessEqual(state["terminal_result"]["position_residual_m"], 1e-9)
                    self.assertEqual(state["action_joint_rates_rad_per_s"], [0, 0])
        self.assertEqual(self.service.get_run("reach", run_id), stored)

    def test_object_actions_include_both_joint_endpoint_owners(self):
        program, _ = self.create()
        for path in ("rig.arm", "rig.arm.upper", "rig.arm.forearm"):
            response = self.success(self.actions(program, selector={"path": path}))
            self.assertEqual(len(list(reach_records(response))), 1, path)
        unrelated = self.success(self.actions(program, selector={"path": "rig.column"}))
        self.assertEqual(list(reach_records(unrelated)), [])

    def test_named_alias_has_independent_pending_state_and_shared_description_identity(self):
        original = source_case("P01")
        payload = original.to_payload()
        marker = "    at 0[s] sequence { start reach; }"
        self.assertEqual(payload["entry"]["source"].count(marker), 1)
        payload["entry"]["source"] = payload["entry"]["source"].replace(
            marker, '    action alias @ "alias" = reach;\n' + marker)
        program = load_bundle(payload)
        created = self.success(self.send("create", bundle=program.to_payload(), expected_program_revision=None,
                                         requested_level="evaluated"))
        response = self.success(self.actions(program, run=created["run_id"], time="1"))
        owner, alias = self.projection(response, "reach"), self.projection(response, "alias")
        self.assertNotEqual(owner["element_id"], alias["element_id"])
        self.assertEqual(owner["description_identity"], alias["description_identity"])
        self.assertEqual(owner["source_location"], alias["source_location"])
        current, pending = owner["current"]["value"], alias["current"]["value"]
        self.assertEqual((current["lifecycle"], pending["lifecycle"]), ("running", "pending"))
        self.assertEqual(pending["claimed_joint_ids"], [])
        self.assertIsNone(pending["resolved_joint_targets_rad"])
        self.assertEqual(pending["action_joint_rates_rad_per_s"], [0, 0])
        self.assertEqual(pending["joint_rates_rad_per_s"], current["joint_rates_rad_per_s"])

    def test_failed_handoff_exposes_incoming_state_and_preserves_it_after_reset(self):
        program, _ = self.create("L04")
        failed = self.error(self.send("evaluate", program_revision=program.program_revision,
                                     run_id=None, until_seconds="2"), "OKL-E-REACH")
        self.assertEqual(failed["status"], "rejected")
        self.assertEqual(failed["diagnostics"][-1]["details"]["reach_code"], "reach_unreachable")
        old_run = copy.deepcopy(self.service.get_run("reach", failed["run_id"]))
        self.assertEqual((old_run["valid_until_seconds"], old_run["valid_until_side"]), ("0.5", "before"))
        before = self.success(self.actions(program, run=failed["run_id"], time="0.5", side="before"))
        first = self.projection(before, "reach_a")["current"]["value"]
        second = self.projection(before, "reach_b")["current"]["value"]
        self.assertEqual((first["lifecycle"], first["goal_outcome"]), ("running", "active"))
        self.assertEqual(len(first["claimed_joint_ids"]), 2)
        self.assertEqual((second["lifecycle"], second["goal_outcome"]), ("pending", "pending"))
        self.assertIsNone(second["resolved_joint_targets_rad"])
        self.assertEqual(second["claimed_joint_ids"], [])
        self.error(self.actions(program, run=failed["run_id"], time="0.5"), "OKL-E-SAMPLE")
        reset = self.success(self.send("reset", program_revision=program.program_revision))
        self.assertNotEqual(reset["run_id"], failed["run_id"])
        prefix = self.evaluate(program, "0.25", reset["run_id"])
        self.assertEqual(prefix["run_id"], reset["run_id"])
        self.assertEqual(self.service.get_run("reach", failed["run_id"]), old_run)
        self.assertEqual(self.service.read_program("reach", program.program_revision), program)

    def test_same_project_action_edit_l04_to_l02_rejects_stale_run(self):
        old, _ = self.create("L04")
        failed = self.error(self.send("evaluate", program_revision=old.program_revision,
                                     run_id=None, until_seconds="2"), "OKL-E-REACH")
        retained = copy.deepcopy(self.service.get_run("reach", failed["run_id"]))
        scope = self.success(self.send("inspect", program_revision=old.program_revision,
            selector={"path": "reach_b"}, fields=["identity", "source", "actions"], limit=1))
        item = scope["result"]["items"][0]
        new = source_case("L02")
        patch = exact_patch(old, new, item["element_id"])
        self.assertTrue(any(span["source_id"] == patch["source_id"]
            and span["start_byte"] <= patch["start_byte"] <= patch["end_byte"] <= span["end_byte"]
            for span in item["source"]["writable_spans"]))
        self.assertEqual(item["element_id"], ["planar-reach-lifecycle", "demo", "reach-b"])
        request = self.request("edit", expected_program_revision=old.program_revision,
                               patches=[patch], requested_level="evaluated")
        edited = self.success(self.service.handle(request))
        self.assertEqual(edited["program_revision"], new.program_revision)
        self.assertEqual(edited["accepted_program_revision"], new.program_revision)
        self.assertEqual(self.service.read_program("reach", new.program_revision), new)
        self.assertEqual({k: unit.raw for k, unit in old.sources.items() if k != "entry"},
                         {k: unit.raw for k, unit in new.sources.items() if k != "entry"})
        self.error(self.actions(new, run=failed["run_id"], time="0.25"), "OKL-E-SAMPLE")
        self.assertEqual(self.service.get_run("reach", failed["run_id"]), retained)
        self.assertEqual(self.service.handle(request), edited)
        self.assertEqual(self.success(self.send("status", target_request_id=request["request_id"]))["result"]["target"], edited)

    def test_paused_and_terminal_projections_retain_complete_independent_history(self):
        for name in ("L01", "L02", "L03"):
            with self.subTest(name=name):
                program = source_case(name)
                project = name.lower()
                created = self.success(self.send("create", project_id=project, bundle=program.to_payload(),
                    expected_program_revision=None, requested_level="evaluated"))
                for expected in CASES[name][1]["samples"]:
                    record = next(iter(expected["reaches"].values()))
                    observation = record["current"]["value"]["observation"]
                    response = self.success(self.actions(program, project_id=project, run=created["run_id"],
                        time=observation["time_seconds"], side=observation["side"]))
                    for path, reference in expected["reaches"].items():
                        actual = self.projection(response, path)
                        self.assert_context(actual, program, program.program_revision, run=created["run_id"])
                        state, wanted = actual["current"]["value"], reference["current"]["value"]
                        for field in ("lifecycle", "goal_outcome", "resolved_joint_targets_rad", "start_coordinates_rad",
                                      "start_time_seconds", "elapsed_seconds", "completion_time_seconds",
                                      "joint_coordinates_rad", "joint_rates_rad_per_s", "action_joint_rates_rad_per_s",
                                      "claimed_joint_ids"):
                            self.assertEqual(state[field], wanted[field], (name, path, observation, field))
                        terminal = state["terminal_result"]
                        if wanted["terminal_result"] is None:
                            self.assertIsNone(terminal)
                        else:
                            for field in ("outcome", "time_seconds", "joint_coordinates_rad"):
                                self.assertEqual(terminal[field], wanted["terminal_result"][field])
                            self.assertLessEqual(abs(terminal["position_residual_m"] - wanted["terminal_result"]["position_residual_m"]), 1e-9)

    def test_discovery_and_mesh_page_preserve_profile_source_and_cursor_context(self):
        program, _ = self.create()
        discovered = self.success(self.send("discover", profile=PROFILE, limit=1000,
                                           program_revision=program.program_revision))
        self.assertEqual(discovered["result"]["program_context"]["program_revision"], program.program_revision)
        self.assertEqual(discovered["result"]["agent_contract"], PROTOCOL)
        ids = ["planar-reach-fixture", "demo", "rig", "arm", "upper"]
        page = self.success(self.send("surface.mesh_page", program_revision=program.program_revision,
                                      element_id=ids, count=1))
        self.assertIsNotNone(page["next_cursor"])
        self.success(self.send("surface.mesh_page", program_revision=program.program_revision,
                               element_id=ids, count=1, cursor=page["next_cursor"]))
        self.error(self.send("surface.mesh_page", program_revision=program.program_revision,
                              element_id=ids, count=1, region="trim", cursor=page["next_cursor"]), "OKL-E-REVISION")
        other = self.request("create", project_id="other", bundle=program.to_payload(),
                             expected_program_revision=None, requested_level="constructed")
        self.success(self.service.handle(other))
        self.error(self.send("surface.mesh_page", project_id="other", program_revision=program.program_revision,
                              element_id=ids, count=1, cursor=page["next_cursor"]), "OKL-E-REVISION")


if __name__ == "__main__":
    unittest.main()
