"""Retained source/request/artifact bytes from real Agent04 workflow segments."""
import base64
import json
from pathlib import Path
import tempfile
import unittest

from tools.build_impulse_agent_demo import Workflow, patch_between, source_case
from tools.impulse_oracles import ACCEPTANCE_BYTES, CASES, digest


class ImpulseWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="ontokin-impulse-workflow-")
        cls.output = Path(cls.tmp.name) / "retained"
        workflow = Workflow(cls.output)
        try:
            # One real delivered artifact, both actual repair paths, and the
            # nonstandard time/numeric cases exercise independent writer risks.
            for name in ("P01", "P02", "P03", "P06", "P09", "P10", "P12", "P15"):
                workflow.fixture(name, deliver=name == "P02")
            workflow.rejection_and_history()
            workflow.mesh_context()
            workflow.frame_projection()
        except BaseException as error:
            workflow.finish(error)
            raise
        cls.report = workflow.finish()
        cls.attempts = []
        for item in cls.report["exchanges"]:
            request = json.loads((cls.output / item["request_file"]).read_text())
            response = json.loads((cls.output / item["response_file"]).read_text())
            cls.attempts.append((item, request, response))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_partial_segment_is_honest_and_all_written_exchange_hashes_match(self):
        self.assertEqual(self.report["status"], "partial")
        self.assertEqual(self.report["acceptance_manifest_sha256"], digest(ACCEPTANCE_BYTES))
        self.assertEqual(len(self.report["fixtures"]), 8)
        self.assertEqual(len(self.report["artifacts"]), 1)
        for index, (item, request, response) in enumerate(self.attempts, 1):
            self.assertEqual(item["sequence"], index)
            self.assertEqual(item["request_sha256"], digest((self.output / item["request_file"]).read_bytes()))
            self.assertEqual(item["response_sha256"], digest((self.output / item["response_file"]).read_bytes()))
            self.assertEqual(request["schema_version"], "ontokin.agent/0.4")
            self.assertEqual(response["schema_version"], "ontokin.agent/0.4")
            self.assertEqual(request["request_id"], response["request_id"])
            self.assertNotIn(request["operation"], ("impulse", "apply_impulse", "set_state"))
        a03 = next(c for c in self.report["checks"] if c["id"] == "A03")
        self.assertEqual(a03["status"], "partial")
        self.assertIn("test_impulse_cli.ImpulseCLITests.test_corrupt_or_directory_store_reports_controlled_selected_protocol_error",
                      a03["details"]["required_test_ids"])

    def test_snapshot_bytes_and_source_authorized_repairs_match_exact_frozen_programs(self):
        by_id = {request["request_id"]: request for _, request, _ in self.attempts}
        for fixture in self.report["fixtures"]:
            expected = source_case(fixture["fixture"])
            self.assertEqual(fixture["program_revision"], expected.program_revision)
            snapshot = next(s for s in self.report["snapshots"] if s["project_id"] == fixture["project_id"]
                            and s["program_revision"] == expected.program_revision)
            self.assertTrue(snapshot["accepted_once"])
            self.assertEqual(json.loads((self.output / snapshot["bundle_file"]).read_text()), expected.to_payload())
            self.assertEqual(snapshot["bundle_sha256"], digest((self.output / snapshot["bundle_file"]).read_bytes()))
            for unit in snapshot["units"]:
                self.assertEqual((self.output / unit["file"]).read_bytes(), expected.sources[unit["source_id"]].raw)
                self.assertEqual(unit["sha256"], digest((self.output / unit["file"]).read_bytes()))
            if fixture["fixture"] in ("P09", "P10"):
                base = source_case("P08")
                self.assertEqual(by_id[fixture["create_request_id"]]["bundle"], base.to_payload())
                self.assertEqual(len(fixture["edit_request_ids"]), 1)
                request = by_id[fixture["accepted_request_id"]]
                self.assertEqual(request["operation"], "edit")
                self.assertEqual(request["expected_program_revision"], base.program_revision)
                self.assertEqual(request["patches"], [patch_between(base, expected, ["impulse-demo", "demo", "rack"])])

    def test_retry_attempts_preserve_original_receipt_and_changed_payload_rejection(self):
        a02 = next(c for c in self.report["checks"] if c["id"] == "A02")
        attempts = [a for a in self.attempts if a[1]["request_id"] == a02["details"]["retry_request_id"]]
        self.assertEqual(len(attempts), 3)
        self.assertEqual(attempts[0][1:], attempts[1][1:])
        self.assertNotEqual(attempts[0][1], attempts[2][1])
        self.assertEqual(attempts[2][2]["protocol_error"]["code"], "OKL-E-REQUEST-ID")
        candidate = next(s for s in self.report["snapshots"] if s["program_revision"] == CASES["N19"]["program_revision"])
        self.assertFalse(candidate["accepted_once"])
        rejected = attempts[0][2]
        self.assertEqual(rejected["accepted_program_revision"], CASES["P01"]["program_revision"])
        self.assertTrue(rejected["result"]["run_state"]["candidate_only"])
        self.assertEqual(rejected["result"]["run_state"]["last_valid_state"]["objects"]["ball"]["impulses"]["applied_count"], 0)

    def test_nonstandard_duration_exact_clock_and_huge_state_are_retained(self):
        p06 = next(f for f in self.report["fixtures"] if f["fixture"] == "P06")
        requests = [r for _, r, _ in self.attempts if r["request_id"] in p06["evaluate_request_ids"]]
        self.assertEqual(requests[-1]["until_seconds"], "3")
        self.assertTrue(any(r.get("time") == {"seconds": "3", "side": "after"}
                            for _, r, _ in self.attempts if r["project_id"] == p06["project_id"]))
        p15 = next(f for f in self.report["fixtures"] if f["fixture"] == "P15")
        actual_times = {(r["time"]["seconds"], r["time"]["side"]) for _, r, _ in self.attempts
                        if r["project_id"] == p15["project_id"] and r["operation"] == "inspect" and "time" in r}
        expected_times = {(s["time_seconds"], s["side"]) for s in CASES["P15"]["expected"]["samples"]}
        self.assertEqual(actual_times, expected_times)
        p12 = next(f for f in self.report["fixtures"] if f["fixture"] == "P12")
        after = next(response for _, request, response in self.attempts if request["project_id"] == p12["project_id"]
                     and request.get("time") == {"seconds": "1", "side": "after"})
        state = after["result"]["items"][0]["state"]
        self.assertEqual(state["velocity_m_per_s"], [1e308, 0., 0.])
        self.assertEqual(state["position_m"], [-1e308, 0., 0.])
        self.assertNotIn("P12", [a["fixture"] for a in self.report["artifacts"]])
        json.dumps(after, allow_nan=False)

    def test_delivered_glb_is_exactly_the_retrieved_artifact_and_has_complete_reference_sides(self):
        artifact = self.report["artifacts"][0]
        self.assertEqual(artifact["fixture"], "P02")
        data = bytearray()
        for identity in artifact["retrieval_request_ids"]:
            _, request, response = next(a for a in self.attempts if a[1]["request_id"] == identity)
            self.assertEqual(request["offset"], len(data))
            self.assertEqual(response["result"]["offset"], len(data))
            data.extend(base64.b64decode(response["result"]["data_base64"], validate=True))
        self.assertEqual(bytes(data), (self.output / "P02/scene.glb").read_bytes())
        self.assertEqual(len(data), artifact["byte_length"])
        self.assertEqual(digest(data), artifact["artifact_sha256"])
        reference = json.loads((self.output / "P02/scene.reference.json").read_text())
        self.assertEqual(reference["program_revision"], CASES["P02"]["program_revision"])
        self.assertEqual(reference["artifact_sha256"], artifact["artifact_sha256"])
        self.assertEqual(reference["implementation"], self.report["implementation"])
        for seconds in ("0", "1", "2"):
            for side in ("before", "after"):
                sample = next(s for s in reference["samples"] if (s["time_seconds"], s["side"]) == (seconds, side))
                self.assertIn("impulses", sample["objects"]["ball"])
                self.assertEqual(sample["objects"]["ball"]["program_revision"], reference["program_revision"])


if __name__ == "__main__":
    unittest.main()
