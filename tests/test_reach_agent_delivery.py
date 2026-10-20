"""Actual delivery obligations; success requires the integrated GLB/0.6 adapter.

These tests deliberately do not skip or replace delivery with a stub while the
adapter is unavailable. Run this cohort after the root adapter is integrated;
an earlier failed run is preparation evidence, never release acceptance.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import unittest
from unittest.mock import patch

from ontokin import gltf, program_runtime
from ontokin.json_limits import measure_json
from test_export import DecodedGLB
from reach_agent_support import TARGET, ReachAgentFixture, exact_patch, source_case


class ReachAgentDeliveryTests(ReachAgentFixture, unittest.TestCase):
    def retrieve(self, delivered):
        result = delivered["result"]
        chunks, offset = [], 0
        while offset < result["total_bytes"]:
            response = self.success(self.send("artifact", artifact_id=result["artifact_id"], offset=offset, max_bytes=32768))
            chunk = response["result"]
            self.assertEqual(chunk["offset"], offset)
            self.assertEqual(chunk["sha256"], result["sha256"])
            self.assertEqual(chunk["artifact_provenance"]["program_revision"], result["program_revision"])
            raw = base64.b64decode(chunk["data_base64"], validate=True)
            self.assertTrue(raw)
            chunks.append(raw)
            offset += len(raw)
            self.assertEqual(chunk["next_offset"], offset if offset < result["total_bytes"] else None)
        data = b"".join(chunks)
        self.assertEqual(len(data), result["total_bytes"])
        self.assertEqual("sha256:" + hashlib.sha256(data).hexdigest(), result["sha256"])
        return data, DecodedGLB(data)

    def test_actual_export_retrieval_context_and_exact_retry(self):
        program, _ = self.create()
        request = self.request("export", program_revision=program.program_revision, destination=TARGET,
                               options={"end": "0.25", "fps": 2, "helpers": False})
        response = self.success(self.service.handle(request))
        self.assertEqual(response["achieved_level"], "delivered")
        self.assertEqual(response["result"]["destination"], TARGET)
        self.assertEqual(response["result"]["report"]["program_revision"], program.program_revision)
        self.assertEqual(response["result"]["run_state"]["valid_until_seconds"], "0.25")
        self.assert_context(response["result"]["run_state"]["last_valid_state"]["reaches"]["reach"],
                            program, program.program_revision, run=response["run_id"])
        self.assertEqual(self.service.get_run("reach", response["run_id"]), response["result"]["run_state"])
        self.assertEqual(self.service.handle(request), response)
        self.assertEqual(self.effects(), {"runs": 1, "artifacts": 1})
        data, decoded = self.retrieve(response)
        metadata = decoded.document["extras"]["ontokin"]
        self.assertEqual(metadata["target_contract"], TARGET)
        self.assertEqual(metadata["program"]["revision"], program.program_revision)
        self.assertTrue(metadata["boundary_states"])
        for boundary in metadata["boundary_states"]:
            for side in ("before", "after"):
                for record in boundary["reach_states_" + side].values():
                    self.assertEqual(record["context_origin"], "source_recording")
                    self.assertIsNone(record["accepted_program_revision"])
                    self.assertIsNone(record["candidate_only"])
                    self.assertIsNone(record["current"]["value"]["observation"]["run_id"])
        self.error(self.send("artifact", artifact_id=response["result"]["artifact_id"], offset=len(data) + 1), "OKA-E-ARTIFACT")
        self.error(self.send("artifact", project_id="foreign", artifact_id=response["result"]["artifact_id"]), "OKA-E-ARTIFACT")
        changed = {**request, "options": {**request["options"], "end": "0.125"}}
        self.assertEqual(self.service.handle(changed)["status"], "rejected")
        self.assertEqual(self.effects(), {"runs": 1, "artifacts": 1})

    def test_l04_extra_recovery_export_is_fresh_run_with_unchanged_source(self):
        program, _ = self.create("L04")
        failed = self.error(self.send("evaluate", program_revision=program.program_revision,
                                     run_id=None, until_seconds="2"), "OKL-E-REACH")
        historical = copy.deepcopy(self.service.get_run("reach", failed["run_id"]))
        reset = self.success(self.send("reset", program_revision=program.program_revision))
        fresh = self.evaluate(program, "0.25", reset["run_id"])
        prior_prefix = copy.deepcopy(self.service.get_run("reach", fresh["run_id"]))
        delivered = self.success(self.send("export", program_revision=program.program_revision, destination=TARGET,
                                          options={"end": "0.25", "fps": 2, "helpers": False}))
        self.assertNotIn(delivered["run_id"], (failed["run_id"], fresh["run_id"]))
        self.assertEqual(delivered["result"]["run_state"]["valid_until_seconds"], "0.25")
        self.assertEqual(delivered["result"]["report"]["sampling"]["end_seconds"], "0.25")
        self.assertEqual(self.service.get_run("reach", failed["run_id"]), historical)
        self.assertEqual(self.service.get_run("reach", fresh["run_id"]), prior_prefix)
        self.assertEqual(self.service.read_program("reach", program.program_revision), program)
        self.assertEqual(self.service.accepted_revision("reach"), program.program_revision)
        self.retrieve(delivered)

    def test_create_validate_export_authorize_only_requested_l04_prefix(self):
        program = source_case("L04")
        options = {"end": "0.25", "fps": 2, "helpers": False}
        for operation in ("create", "validate", "export"):
            project = "prefix-" + operation
            if operation != "create":
                self.success(self.send("create", project_id=project, bundle=program.to_payload(),
                    expected_program_revision=None, requested_level="constructed"))
            fields = ({"bundle": program.to_payload(), "expected_program_revision": None, "requested_level": "delivered"}
                      if operation == "create" else {"program_revision": program.program_revision})
            if operation == "validate":
                fields["requested_level"] = "delivered"
            response = self.success(self.send(operation, project_id=project, destination=TARGET, options=options, **fields))
            self.assertEqual(response["achieved_level"], "delivered")
            self.assertEqual(response["result"]["run_state"]["valid_until_seconds"], "0.25")
            self.assertEqual(response["result"]["report"]["sampling"]["end_seconds"], "0.25")
            self.assertEqual(self.effects(project), {"runs": 1, "artifacts": 1})
            self.error(self.actions(program, project_id=project, run=response["run_id"], time="0.5"), "OKL-E-SAMPLE")

    def test_delivery_shares_one_compiler_and_numerical_work_context(self):
        program, _ = self.create()
        compiled, exported = [], []
        compile_ = program_runtime._compile
        export = gltf.export_glb
        def compile_once(*args, **kwargs):
            compiler = compile_(*args, **kwargs)
            compiled.append(compiler)
            return compiler
        def export_same(model, *args, **kwargs):
            exported.append((model, kwargs.get("work")))
            return export(model, *args, **kwargs)
        with patch.object(program_runtime, "_compile", side_effect=compile_once), patch.object(gltf, "export_glb", side_effect=export_same):
            self.success(self.send("export", program_revision=program.program_revision, destination=TARGET,
                                   options={"end": "0.25", "helpers": False}))
        self.assertEqual(len(compiled), 1)
        self.assertEqual(len(exported), 1)
        self.assertIs(exported[0][0], compiled[0].model)
        self.assertIs(exported[0][1], compiled[0].reach_work)
        self.assertIsNotNone(exported[0][1])

    def test_generic_delivery_and_full_failed_horizon_never_claim_artifact(self):
        program, _ = self.create("L04")
        generic = self.error(self.send("validate", program_revision=program.program_revision,
                                       requested_level="delivered"), "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertNotEqual(generic["achieved_level"], "delivered")
        failed = self.error(self.send("export", program_revision=program.program_revision,
                                      destination=TARGET), "OKL-E-REACH")
        self.assertEqual(failed["diagnostics"][-1]["details"]["reach_code"], "reach_unreachable")
        self.assertEqual(self.effects()["artifacts"], 0)
        self.assertEqual(self.service.accepted_revision("reach"), program.program_revision)

    def test_q08_p17_short_prefix_and_exact_later_failure(self):
        program, _ = self.create("P17")
        delivered = self.success(self.send("export", program_revision=program.program_revision, destination=TARGET,
                                          options={"end": "2", "fps": 2, "helpers": False}))
        artifact = delivered["result"]["artifact_id"]
        before = self.effects()
        failed = self.error(self.send("export", program_revision=program.program_revision, destination=TARGET,
                                      options={"end": "4", "fps": 2, "helpers": False}), "OKL-E-REACH")
        self.assertNotEqual(failed["achieved_level"], "delivered")
        self.assertEqual(failed["diagnostics"][-1]["details"]["reach_code"], "reach_unreachable")
        run = failed["result"]["run_state"]
        self.assertEqual((run["valid_until_seconds"], run["valid_until_side"]), ("3", "before"))
        self.assertEqual(self.effects()["artifacts"], before["artifacts"])
        retained = self.success(self.send("artifact", artifact_id=artifact, max_bytes=64))
        self.assertEqual(retained["result"]["sha256"], delivered["result"]["sha256"])

    def test_cancel_after_actual_delivery_rolls_back_artifact_and_candidate(self):
        old, _ = self.create("L04")
        new = source_case("L02")
        request = self.request("edit", expected_program_revision=old.program_revision,
            patches=[exact_patch(old, new, ["planar-reach-lifecycle", "demo", "reach-b"])], requested_level="delivered",
            destination=TARGET, options={"end": "0.25", "fps": 2, "helpers": False})
        execute = self.service._execute
        prepared = []
        def cancel_after_delivery(task, check):
            execute(task, check)
            prepared.append((task.accept, task.run is not None, task.artifact is not None))
            self.success(self.send("cancel", target_request_id=request["request_id"]))
        with patch.object(self.service, "_execute", side_effect=cancel_after_delivery):
            response = self.service.handle(request)
        self.assertEqual(prepared, [(True, True, True)])
        self.assertEqual(response["status"], "cancelled")
        self.assertEqual(response["accepted_program_revision"], old.program_revision)
        self.assertIsNone(response["result"])
        self.assertEqual(self.effects(), {"runs": 0, "artifacts": 0})

    def test_final_delivery_envelope_guard_rolls_back_run_and_artifact(self):
        program, _ = self.create("P24")
        options = {"end": "0.25", "fps": 2, "helpers": False}
        baseline = self.success(self.send("export", program_revision=program.program_revision,
                                           destination=TARGET, options=options))
        n = measure_json(baseline)["entries"]
        self.success(self.send("create", project_id="limited", bundle=program.to_payload(),
                               expected_program_revision=None, requested_level="constructed"))
        execute = self.service._execute
        prepared = []
        def observe(task, check):
            execute(task, check)
            prepared.append((task.run is not None, task.artifact is not None))
        with patch.object(self.service, "_execute", side_effect=observe):
            response = self.error(self.send("export", project_id="limited", program_revision=program.program_revision,
                destination=TARGET, options=options, budgets={"max_value_entries": n - 1}), "OKA-E-RESOURCE")
        self.assertEqual(prepared, [(True, True)])
        self.assertFalse(response["protocol_error"]["details"]["effects_committed"])
        self.assertIsNone(response["run_id"])
        self.assertIsNone(response["result"])
        self.assertEqual(self.effects("limited"), {"runs": 0, "artifacts": 0})
        exact = self.success(self.send("export", project_id="limited", program_revision=program.program_revision,
            destination=TARGET, options=options, budgets={"max_value_entries": n}))
        self.assertEqual(measure_json(exact)["entries"], n)
        self.assertEqual(self.effects("limited"), {"runs": 1, "artifacts": 1})


if __name__ == "__main__":
    unittest.main()
