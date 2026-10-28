"""Actual Agent results against the frozen adopted schemas, with offline refs."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest

from reach_agent_support import DATA, ReachAgentFixture, exact_patch, source_case

HAS_SCHEMA = all(importlib.util.find_spec(name) for name in ("jsonschema", "referencing"))


@unittest.skipUnless(HAS_SCHEMA, "Pinned verification-only jsonschema/referencing packages are required")
class ReachAgentSchemaVerificationTests(ReachAgentFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from referencing.exceptions import NoSuchResource
        def deny(uri):
            raise NoSuchResource(ref=uri)
        manifest = json.loads((DATA / "schema-drafts/schema-drafts-manifest.json").read_text())
        documents = {}
        for group, base in (("members", DATA / "schema-drafts"), ("inherited_inputs", DATA)):
            for row in manifest[group]:
                path = base / row["path"]
                raw = path.read_bytes()
                self.assertEqual("sha256:" + hashlib.sha256(raw).hexdigest(), row["sha256"])
                schema = json.loads(raw)
                documents[schema["$id"]] = schema
        registry = Registry(retrieve=deny).with_resources(
            (uri, Resource.from_contents(schema)) for uri, schema in documents.items())
        self.validators = {}
        for name in ("agent-request", "agent-response", "reach-projection"):
            schema = json.loads((DATA / "schema-drafts" / (name + ".schema.json")).read_text())
            Draft202012Validator.check_schema(schema)
            self.validators[name] = Draft202012Validator(schema, registry=registry)

    def valid(self, name, value):
        errors = sorted(self.validators[name].iter_errors(value), key=lambda error: str(list(error.path)))
        self.assertEqual([{"path": list(error.path), "message": error.message} for error in errors], [])

    def test_actual_created_sampled_failed_and_historical_receipts_match_frozen_schemas(self):
        program, created = self.create("P10")
        self.valid("agent-response", created)
        self.valid("reach-projection", created["result"]["initial_state"]["reaches"]["reach"])
        evaluated = self.evaluate(program)
        self.valid("agent-response", evaluated)
        self.valid("reach-projection", evaluated["result"]["run_state"]["last_valid_state"]["reaches"]["reach"])
        inspected = self.success(self.actions(program, run=evaluated["run_id"], time="1"))
        self.valid("agent-response", inspected)
        self.valid("reach-projection", self.projection(inspected))
        candidate = source_case("N06")
        failed_request = self.request("edit", expected_program_revision=program.program_revision,
            patches=[exact_patch(program, candidate, ["planar-reach-fixture", "demo", "rig"])], requested_level="evaluated")
        failed = self.error(self.service.handle(failed_request), "OKL-E-REACH")
        self.valid("agent-request", failed_request)
        self.valid("agent-response", failed)
        unsampled = self.success(self.actions(candidate))
        self.valid("agent-response", unsampled)
        self.valid("reach-projection", self.projection(unsampled))
        accepted = self.success(self.service.handle({**failed_request, "request_id": "accept-identical", "requested_level": "constructed"}))
        self.valid("agent-response", accepted)
        historical = self.success(self.actions(candidate, run=failed["run_id"], time="0", side="before"))
        self.valid("agent-response", historical)
        self.valid("reach-projection", self.projection(historical))
        self.assertFalse(self.projection(historical)["candidate_only"])
        self.assertTrue(self.service.get_run("reach", failed["run_id"])["candidate_only"])
        status = self.success(self.send("status", target_request_id=failed_request["request_id"]))
        self.valid("agent-response", status)
        self.assertEqual(status["result"]["target"], failed)
        for request, response in self.exchanges:
            self.valid("agent-request", request)
            self.valid("agent-response", response)

    def test_frozen_schema_rejects_fabricated_outcomes_and_missing_context(self):
        program, created = self.create(level="evaluated")
        valid = self.projection(self.success(self.actions(program, run=created["run_id"], time="1")))
        self.valid("reach-projection", valid)
        for mutation in ("failed_goal", "missing_run", "missing_rates", "missing_context"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(valid)
                state = changed["current"]["value"]
                if mutation == "failed_goal":
                    state["goal_outcome"] = "failed"
                elif mutation == "missing_run":
                    state["observation"]["run_id"] = None
                elif mutation == "missing_rates":
                    state.pop("action_joint_rates_rad_per_s")
                else:
                    changed.pop("accepted_program_revision")
                self.assertTrue(list(self.validators["reach-projection"].iter_errors(changed)))


if __name__ == "__main__":
    unittest.main()
