"""Evidence-recorder integrity; these stubs do not establish Agent delivery."""
import base64
import copy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from tools.build_reach_agent_delivery import (
    CHUNK_BYTES, MAX_BYTES, PROTOCOL, RELEASE_PROBES_FILE, Recorder,
)
from tools.reach_delivery_inventory import AGENT_CASES, ROOT, checked_member, decode, read_bounded, sha


class ReachAgentProducerTests(unittest.TestCase):
    def transport(self, raw, *, change=None):
        recorder = Recorder.__new__(Recorder)
        exported = {"run_id": "run-actual", "result": {
            "artifact_id": "artifact-actual", "total_bytes": len(raw), "sha256": sha(raw),
            "program_revision": "sha256:program", "report": {
                "exporter": "test-evidence-stub", "source_code_sha256": "source",
                "program_revision": "sha256:program"}}}
        requests = []
        def send(role, project, operation, **fields):
            requests.append((role, project, operation, fields))
            offset = fields["offset"]
            part = raw[offset:offset + fields["max_bytes"]]
            result = {
                "offset": offset, "total_bytes": len(raw), "sha256": sha(raw),
                "data_base64": base64.b64encode(part).decode(),
                "next_offset": offset + len(part) if offset + len(part) < len(raw) else None,
                "artifact_provenance": {"exporter": "test-evidence-stub",
                    "source_code_sha256": "sha256:source", "program_revision": "sha256:program"}}
            if change is not None:
                change(result)
            return {"result": result}
        recorder.send = send
        return recorder, exported, requests

    def test_complete_artifact_uses_only_contiguous_returned_chunk_bytes(self):
        raw = b"\x00\xffindependent transport bytes" * (CHUNK_BYTES // 20 + 1)
        recorder, exported, requests = self.transport(raw)
        result, evidence = recorder.retrieve("case/chunk", "project", exported)
        self.assertEqual(result, raw)
        self.assertEqual(evidence["sha256"], sha(raw))
        self.assertEqual(evidence["bytes"], len(raw))
        self.assertEqual([row[3]["offset"] for row in requests], list(range(0, len(raw), CHUNK_BYTES)))
        self.assertTrue(evidence["complete_contiguous_retrieval"])
        self.assertEqual(evidence["run_id"], "run-actual")
        self.assertEqual(evidence["artifact_id"], "artifact-actual")

    def test_conflicting_chunk_identity_offset_and_empty_data_are_rejected(self):
        def provenance(result):
            result["artifact_provenance"]["program_revision"] = "sha256:another-source"
        changes = (
            lambda result: result.update(offset=1),
            lambda result: result.update(total_bytes=result["total_bytes"] + 1),
            lambda result: result.update(sha256="sha256:another-artifact"),
            lambda result: result.update(next_offset=0),
            lambda result: result.update(data_base64=""),
            provenance,
        )
        for change in changes:
            with self.subTest(change=change):
                recorder, exported, _ = self.transport(b"actual bytes", change=change)
                with self.assertRaises(ValueError):
                    recorder.retrieve("case/chunk", "project", exported)
        recorder, exported, _ = self.transport(b"actual bytes")
        exported["result"]["total_bytes"] = MAX_BYTES + 1
        with self.assertRaises(ValueError):
            recorder.retrieve("case/chunk", "project", exported)

    def test_reassembled_hash_is_independent_of_claimed_chunk_hash(self):
        recorder, exported, _ = self.transport(b"actual bytes")
        original = recorder.send
        def lying(role, project, operation, **fields):
            reply = original(role, project, operation, **fields)
            reply["result"]["data_base64"] = base64.b64encode(b"forged bytes").decode()
            return reply
        recorder.send = lying
        with self.assertRaises(ValueError):
            recorder.retrieve("case/chunk", "project", exported)

    def test_nested_status_dispatch_reserves_distinct_immutable_trace_files(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = Recorder.__new__(Recorder)
            recorder.output = Path(directory)
            recorder.report = {}
            recorder.trace, recorder.requests, recorder.responses = [], {}, {}
            recorder.serial = 0
            def response():
                return {"schema_version": PROTOCOL, "status": "succeeded", "protocol_error": None, "diagnostics": []}
            class Stub:
                def handle(self, request):
                    if request["operation"] == "export":
                        recorder.send("nested/status", "project", "status", target_request_id=request["request_id"])
                    return response()
            recorder.service = Stub()
            request = recorder.request("project", "export", program_revision="sha256:program")
            unchanged = copy.deepcopy(request)
            recorder.exchange("outer/export", request)
            self.assertEqual(request, unchanged)
            self.assertEqual([row["sequence"] for row in recorder.trace], [1, 2])
            self.assertEqual([row["role"] for row in recorder.trace], ["outer/export", "nested/status"])
            names = []
            for row in recorder.trace:
                for name in ("request", "response"):
                    path = checked_member(directory, row[name])
                    names.append(path.name)
                    value = decode(read_bounded(path))
                    self.assertEqual(value, recorder.requests[row["role"]] if name == "request" else response())
            self.assertEqual(len(names), len(set(names)))

    def test_q22_preserves_exact_frozen_patch_and_lp01_failed_run_control_requests(self):
        probes = {row["id"]: row for row in decode(read_bounded(ROOT / RELEASE_PROBES_FILE))["probes"]}
        probe = probes["Q22-same-project-repair-and-stale-history"]
        template = probe["edit_request_template"]
        change = template["patches"][0]
        project = template["project_id"]
        old_revision, new_revision = template["expected_program_revision"], probe["expected_edit"]["accepted_program_revision"]
        prefix, suffix = b"x" * change["start_byte"], b"; untouched source\n"
        old_entry = SimpleNamespace(raw=prefix + change["expected_text"].encode() + suffix,
                                    revision=change["source_revision"])
        new_entry = SimpleNamespace(raw=prefix + change["replacement"].encode() + suffix)
        library = SimpleNamespace(raw=b"exact unchanged library")
        old = SimpleNamespace(entry=old_entry, program_revision=old_revision,
                              sources={"entry": old_entry, "library": library})
        new = SimpleNamespace(entry=new_entry, program_revision=new_revision,
                              sources={"entry": new_entry, "library": library})
        original_record = {"kind": "reach_planar", "element_id": change["element_id"],
                           "program_revision": old_revision, "accepted_program_revision": old_revision,
                           "run_id": "lp01-failed", "current": {"available": True, "value": {"lifecycle": "pending"}},
                           "history": [{"time_seconds": "0.5", "side": "before"}]}
        original = {"result": {"items": [{"actions": [original_record]}]}}
        control = copy.deepcopy(original)
        control.update(program_revision=old_revision, accepted_program_revision=new_revision, run_id="lp01-failed")
        control["result"]["items"][0]["actions"][0]["accepted_program_revision"] = new_revision
        edited = {"program_revision": new_revision, "accepted_program_revision": new_revision,
                  "run_id": "q22-new", "result": {"run_state": {"status": "ready"}}}
        effects = {"runs": 3, "artifacts": 1, "accepted_program_revision": old_revision}
        retained = [{"run_id": "lp01-failed", "status": "failed"}, {"unchanged": True}]
        recorder = Recorder.__new__(Recorder)
        recorder.serial = 0
        recorder.release_probes, recorder.bindings = probes, {"LP01.failed_run": "lp01-failed"}
        recorder.contexts = {"L04": {"project": project, "program": old, "failed_run": "lp01-failed",
                                     "failed_snapshot": retained, "prior_run": "lp01-reset-prefix",
                                     "protocol_roles": [f"LP01.{number:02d}" for number in range(1, 10)]}}
        recorder.responses = {"LP01.03": original}
        recorder.bundle = lambda case_id: new if case_id == "L02" else self.fail("unexpected case")
        recorder.service = SimpleNamespace(accepted_revision=lambda requested: effects["accepted_program_revision"])
        recorder.effects = lambda requested: copy.deepcopy(effects)
        recorder.retain_source = lambda label, requested, program: {"program_revision": program.program_revision}
        retained_checks, exchanges = [], []
        def retain(label, requested, run_id, before):
            retained_checks.append((label, requested, run_id, before))
            return {"path": "retained.json"}
        recorder.require_retained = retain
        def exchange(role, request, **expected):
            exchanges.append((role, copy.deepcopy(request), expected))
            if role == "Q22/authority":
                return {"result": {"items": [{"element_id": change["element_id"], "source": {"writable_spans": [
                    {"source_id": "entry", "start_byte": 0, "end_byte": len(old_entry.raw)}]}}]}}
            if role == "Q22.01":
                effects.update(runs=4, accepted_program_revision=new_revision)
                return copy.deepcopy(edited)
            if role == "Q22.02":
                return {"diagnostics": [{"category": "stale"}]}
            if role == "Q22.03":
                return copy.deepcopy(control)
            if role == "Q22/retry":
                return copy.deepcopy(edited)
            if role == "Q22/status":
                return {"result": {"target": copy.deepcopy(edited)}}
            self.fail("Unexpected additional Q22 source mutation or evaluation: " + role)
        recorder.exchange = exchange
        result = recorder.run_q22()
        by_role = {role: request for role, request, _ in exchanges}
        self.assertEqual(by_role["Q22.01"], template)
        for role, key in (("Q22.02", "mismatch_request_template"), ("Q22.03", "historical_control_request_template")):
            expected = copy.deepcopy(probe[key])
            expected["run_id"] = "lp01-failed"
            self.assertEqual(by_role[role], expected)
        self.assertTrue(all(request["project_id"] == project for _, request, _ in exchanges))
        self.assertEqual([request["operation"] for _, request, _ in exchanges].count("edit"), 2)
        self.assertNotIn("create", [request["operation"] for _, request, _ in exchanges])
        self.assertNotIn("evaluate", [request["operation"] for _, request, _ in exchanges])
        self.assertEqual(result["old_run_id"], "lp01-failed")
        self.assertEqual(recorder.contexts["L02"]["project"], project)
        self.assertIn("Q22.03", recorder.contexts["L02"]["protocol_roles"])
        self.assertEqual(retained_checks, [("Q22-old-failure", project, "lp01-failed", retained)])

    def test_recovery_retrieval_precedes_q22_edit_without_duplicate_l04_delivery(self):
        recorder = Recorder.__new__(Recorder)
        recorder.report = {"workflow_roles": [], "deliveries": []}
        recorder.steps = {str(number): {} for number in range(42)}
        recorder.responses = {identity: {} for identity in recorder.steps}
        recorder.bindings, recorder.trace = {}, []
        recorder.send = lambda *args, **kwargs: {}
        recorder.write = lambda *args, **kwargs: {"path": "stub.json"}
        events = []
        for role in ("lp01", "lp02", "lp03", "lp04", "lp05", "q22", "delivery_failures", "q02"):
            setattr(recorder, "run_" + role, lambda: None)
        def run_role(name, function):
            events.append(name)
            function()
            recorder.report["workflow_roles"].append({"role": name, "status": "passed"})
        def deliver(case_id, fps):
            events.append("delivery/" + case_id)
            recorder.report["deliveries"].append({"case_id": case_id, "status": "passed"})
        recorder.run_role, recorder.deliver = run_role, deliver
        recorder.run(AGENT_CASES, 1)
        self.assertLess(events.index("LP01"), events.index("delivery/L04"))
        self.assertLess(events.index("delivery/L04"), events.index("Q22"))
        self.assertLess(events.index("Q22"), events.index("delivery/L02"))
        self.assertEqual(events.count("delivery/L04"), 1)
        self.assertEqual({row["case_id"] for row in recorder.report["deliveries"]}, set(AGENT_CASES))


if __name__ == "__main__":
    unittest.main()
