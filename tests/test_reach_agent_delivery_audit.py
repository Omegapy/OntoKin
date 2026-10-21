"""Adversarial reader tests; fixtures are not actual Agent workflow evidence."""
from __future__ import annotations

import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.audit_reach_agent_delivery import (DATA, MAX_DEPTH, MAX_ENVELOPE, PROTOCOL, TARGET,
    EvidenceError, Reader, Sources, canonical, decode, descriptor, envelope_bound,
    complete_source_units, frozen_request, joined_chunks, json_entries, resolve, retained_run, safe_path, sha)


def chunk_fixture():
    """A transport-only binary fixture; it makes no valid-GLB claim."""
    raw = b"first-block\0" * 3000 + b"last"
    request = {"schema_version": PROTOCOL, "project_id": "project-a", "request_id": "export-a",
               "operation": "export", "program_revision": "sha256:" + "1" * 64,
               "destination": TARGET, "options": {"end": "0.25", "fps": 1, "helpers": False}}
    report = {"exporter": "test-reader-fixture", "source_code_sha256": "2" * 64}
    result = {"artifact_id": "artifact:" + sha(raw)[7:], "program_revision": request["program_revision"],
              "total_bytes": len(raw), "sha256": sha(raw), "report": report}
    response = {"status": "succeeded", "run_id": "run-a", "result": result}
    provenance = {"exporter": report["exporter"], "source_code_sha256": "sha256:" + report["source_code_sha256"],
                  "program_revision": request["program_revision"]}
    rows, roles = {}, []
    for index, offset in enumerate(range(0, len(raw), 32768)):
        block = raw[offset:offset + 32768]
        role = f"chunk-{index}"
        q = {"schema_version": PROTOCOL, "project_id": request["project_id"], "request_id": role,
             "operation": "artifact", "artifact_id": result["artifact_id"], "offset": offset, "max_bytes": 32768}
        r = {"status": "succeeded", "result": {"offset": offset, "total_bytes": len(raw), "sha256": sha(raw),
             "data_base64": base64.b64encode(block).decode("ascii"),
             "next_offset": offset + len(block) if offset + len(block) < len(raw) else None,
             "artifact_provenance": provenance}}
        rows[role] = (q, r)
        roles.append(role)
    closure = {"project_id": request["project_id"], "run_id": "run-a", "artifact_id": result["artifact_id"],
               "sha256": sha(raw), "bytes": len(raw), "chunk_bytes": 32768,
               "chunk_roles": roles, "provenance": provenance, "complete_contiguous_retrieval": True}
    return raw, rows, closure, request, response


class ReachAgentDeliveryAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Immutable byte parsing only: no compiler, Agent service or runtime.
        cls.sources = Sources()
        cls.probes = {row["id"]: row for row in
                      json.loads((DATA / "draft2-supplements/release-probes.json").read_text())["probes"]}

    def test_independent_entry_count_counts_repeated_occurrences_and_ignores_keys(self):
        shared = [None, {"very long key" * 30: False}]
        value = {"left": shared, "right": shared}
        self.assertEqual(json_entries(value), 9)
        with self.assertRaises(EvidenceError):
            json_entries(value, limit=8)
        cycle = []
        cycle.append(cycle)
        with self.assertRaises(EvidenceError):
            json_entries(cycle)

    def test_independent_depth_boundary_includes_containers_and_terminal_values(self):
        value = 0
        for _ in range(MAX_DEPTH):
            value = [value]
        self.assertEqual(json_entries(value), MAX_DEPTH + 1)
        with self.assertRaises(EvidenceError):
            json_entries([value])
        with self.assertRaises(EvidenceError):
            json_entries([[]], depth_limit=1)

    def test_complete_byte_limit_and_scalar_validity_are_checked_independently(self):
        self.assertEqual(envelope_bound("a" * (MAX_ENVELOPE - 2)), 1)
        with self.assertRaises(EvidenceError):
            envelope_bound("a" * (MAX_ENVELOPE - 1))
        for value in (float("inf"), (1,), {1: "bad"}, 1 << 14000):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(EvidenceError):
                json_entries(value)
        with self.assertRaises(UnicodeError):
            json_entries({"\ud800": 0})

    def test_duplicate_keys_and_nonfinite_tokens_cannot_hide_evidence_fields(self):
        for raw in (b'{"status":"failed","status":"passed"}', b'{"n":NaN}', b'{"n":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(EvidenceError):
                decode(raw)

    def test_actual_chunk_closure_is_independent_of_summary_pass_flags(self):
        raw, rows, closure, q, r = chunk_fixture()
        self.assertEqual(joined_chunks(rows, closure, q, r), raw)
        closure["complete_contiguous_retrieval"] = False
        closure["producer_checks"] = "failed"
        self.assertEqual(joined_chunks(rows, closure, q, r), raw)
        closure["complete_contiguous_retrieval"] = True
        closure["chunk_roles"] = closure["chunk_roles"][:-1]
        with self.assertRaises(EvidenceError):
            joined_chunks(rows, closure, q, r)

    def test_chunk_gap_duplicate_and_false_eof_are_rejected(self):
        for mutation in ("request-gap", "response-gap", "duplicate", "false-eof"):
            raw, rows, closure, q, r = chunk_fixture()
            first, last = closure["chunk_roles"]
            if mutation == "request-gap":
                rows[last][0]["offset"] += 1
            elif mutation == "response-gap":
                rows[last][1]["result"]["offset"] -= 1
            elif mutation == "duplicate":
                closure["chunk_roles"].append(last)
            else:
                rows[first][1]["result"]["next_offset"] = None
            with self.subTest(mutation=mutation), self.assertRaises(EvidenceError):
                joined_chunks(rows, closure, q, r)

    def test_rehashed_chunk_record_cannot_substitute_project_source_or_artifact(self):
        for mutation in ("project", "source", "artifact", "bytes"):
            raw, rows, closure, q, r = chunk_fixture()
            cq, cr = rows[closure["chunk_roles"][0]]
            if mutation == "project":
                cq["project_id"] = "project-b"
            elif mutation == "source":
                cr["result"]["artifact_provenance"] = {**cr["result"]["artifact_provenance"], "program_revision": "sha256:" + "3" * 64}
            elif mutation == "artifact":
                cq["artifact_id"] = "artifact:" + "4" * 64
            else:
                original = base64.b64decode(cr["result"]["data_base64"])
                cr["result"]["data_base64"] = base64.b64encode(b"X" + original[1:]).decode("ascii")
            # A newly computed descriptor cannot make semantic substitutions valid.
            receipt = descriptor(canonical(cr), "changed-response.json")
            self.assertTrue(receipt["sha256"].startswith("sha256:"))
            with self.subTest(mutation=mutation), self.assertRaises(EvidenceError):
                joined_chunks(rows, closure, q, r)

    def test_exact_q22_requires_original_project_expression_and_old_run(self):
        probe = self.probes["Q22-same-project-repair-and-stale-history"]
        bindings = {"LP01.failed_run": "actual-failed-run"}
        expected = resolve(probe["edit_request_template"], bindings, self.sources)
        frozen_request(expected, probe["edit_request_template"], bindings, self.sources)
        for mutation in ("new-project", "different-span", "different-sample", "different-run"):
            if mutation in ("new-project", "different-span"):
                template = probe["edit_request_template"]
                changed = copy.deepcopy(expected)
                if mutation == "new-project":
                    changed["project_id"] = "reach-delivery-q22"
                else:
                    changed["patches"][0]["start_byte"] += 1
            else:
                template = probe["mismatch_request_template"]
                changed = resolve(template, bindings, self.sources)
                if mutation == "different-sample":
                    changed["time"] = {"seconds": "0.25", "side": "after"}
                else:
                    changed["run_id"] = "a-new-failed-run"
            with self.subTest(mutation=mutation), self.assertRaises(EvidenceError):
                frozen_request(changed, template, bindings, self.sources)

    def test_q22_frozen_patch_independently_reconstructs_exact_l02_bytes(self):
        template = self.probes["Q22-same-project-repair-and-stale-history"]["edit_request_template"]
        candidate = self.sources.candidate(template)
        self.assertEqual(candidate.to_payload(), self.sources.bundles["L02"].to_payload())
        self.assertEqual(candidate.modules, self.sources.bundles["L04"].modules)
        changed = copy.deepcopy(template)
        changed["patches"][0]["expected_text"] = "invented prior bytes"
        with self.assertRaises(EvidenceError):
            self.sources.candidate(changed)

    def test_lp02_complete_source_reads_preserve_immutable_unit_identity(self):
        document = json.loads((DATA / "draft2-supplements/protocol-cases.json").read_text())
        lp02 = next(case for case in document["protocol_cases"] if case["id"] == "LP02")
        for role, case_id in (("LP02.08", "P13"), ("LP02.09", "P20")):
            step = next(item for item in lp02["steps"] if item["id"] == role)
            expected = next(item["expected"]["exact_source_unit_identities"]
                            for item in step["required_evidence_reads"]
                            if "exact_source_unit_identities" in item["expected"])
            program = self.sources.bundles[case_id]
            units = {unit.source_id: unit for unit in program.units}
            returned = [{"source_id": item["source_id"], "source_revision": item["source_revision"],
                         "filename": item["filename"], "source": units[item["source_id"]].raw.decode("utf-8")}
                        for item in expected]
            self.assertEqual(list(complete_source_units(program, returned, expected)),
                             [item["source_id"] for item in expected])
            for mutation in ("bytes", "revision", "filename", "unknown", "duplicate", "missing", "reordered"):
                changed = copy.deepcopy(returned)
                if mutation in ("bytes", "revision", "filename", "unknown"):
                    field = {"bytes": "source", "revision": "source_revision",
                             "filename": "filename", "unknown": "source_id"}[mutation]
                    changed[0][field] += "x"
                elif mutation == "duplicate":
                    changed.append(copy.deepcopy(changed[0]))
                elif mutation == "missing":
                    changed.pop()
                else:
                    changed.reverse()
                with self.subTest(case=case_id, mutation=mutation), self.assertRaises(EvidenceError):
                    complete_source_units(program, changed, expected)

    def test_snapshot_action_summary_and_complete_reach_projection_are_distinct(self):
        projection = copy.deepcopy(self.sources.cases["L04"]["samples"][0]["reaches"]["reach_a"])
        calls = []

        class ProjectionSchema:
            def check(self, name, value):
                if name == "agent-response":
                    return  # This fixture tests traversal, not envelope schemas.
                calls.append((name, copy.deepcopy(value)))
                if name != "reach-projection" or set(value) != set(projection) or value.get("kind") != "reach_planar":
                    raise EvidenceError("Not a complete source-bound reach projection")

        reader = Reader.__new__(Reader)
        reader.schemas, reader.sources, reader.projections = ProjectionSchema(), self.sources, 0
        summary = {"kind": "reach_planar", "element_id": projection["element_id"],
                   "target": projection["chain"]["shoulder"]["path"], "channel": "joint_coordinates",
                   "status": "pending", "duration_seconds": "2", "local_elapsed_seconds": "0",
                   "value_type": "AnglePair", "start_value": {"available": False, "value": None},
                   "current_value": {"available": True, "value": [0.0, 0.0]},
                   "target_value": {"available": False, "value": None, "reason": "action_has_not_started"}}
        sample = {"time_seconds": "0", "side": "before", "objects": {}, "frames": {}, "joints": {},
                  "actions": {"reach_a": summary}, "reaches": {"reach_a": projection}}
        response = {"schema_version": PROTOCOL, "result": {"initial_state": sample}}
        reader.recursive(response)
        self.assertEqual(calls, [("reach-projection", projection)])
        self.assertEqual(reader.projections, 1)
        reader.recursive({"result": {"items": [{"actions": [projection]}]}})
        self.assertEqual(reader.projections, 2)
        reader.recursive({"schema_version": PROTOCOL,
                          "result": {"run_state": {"last_valid_state": sample}}})
        reader.recursive({"schema_version": PROTOCOL, "result": {"target": response}})
        self.assertEqual(reader.projections, 4)
        for mutation in ("missing-kind", "missing-source", "summary-in-reaches", "summary-in-inspect",
                         "snapshot-shaped-decoy", "nonmap-frames"):
            changed = copy.deepcopy(response)
            state = changed["result"]["initial_state"]
            if mutation == "missing-kind":
                del state["reaches"]["reach_a"]["kind"]
            elif mutation == "missing-source":
                del state["reaches"]["reach_a"]["program_revision"]
            elif mutation == "summary-in-reaches":
                state["reaches"]["reach_a"] = summary
            elif mutation == "summary-in-inspect":
                changed = {"result": {"items": [{"actions": [summary]}]}}
            elif mutation == "snapshot-shaped-decoy":
                changed = {"schema_version": PROTOCOL, "result": {"unrelated": sample}}
            else:
                state["frames"] = []
            with self.subTest(mutation=mutation), self.assertRaises(EvidenceError):
                reader.recursive(changed)
        # Discovery may carry schema descriptions with properties called
        # actions/reaches. Those are not actual sampled projection records.
        count = len(calls)
        reader.recursive({"properties": {"actions": {"type": "object"},
            "reaches": {"additionalProperties": {"$ref": "reach-projection.schema.json"}}}})
        self.assertEqual(len(calls), count)

    def test_bindings_must_come_from_a_prior_actual_capture(self):
        with self.assertRaises(EvidenceError):
            resolve({"$binding": "LP01.failed_run"}, {}, self.sources)
        self.assertEqual(resolve({"$binding_minus_one": "LP04.N"}, {"LP04.N": 37}, self.sources), 36)
        with self.assertRaises(EvidenceError):
            resolve({"$binding_minus_one": "LP04.N"}, {"LP04.N": "37"}, self.sources)

    def test_identical_claimed_before_after_still_must_match_the_actual_retained_run(self):
        state = {"run_id": "historical", "candidate_only": True}
        record = {"before": [copy.deepcopy(state), 1], "after": [copy.deepcopy(state), 1], "unchanged": True}
        retained_run(record, state, 1)
        for final, version in (({**state, "candidate_only": False}, 1), (state, 2)):
            with self.subTest(final=final, version=version), self.assertRaises(EvidenceError):
                retained_run(record, final, version)
        record["after"][0]["candidate_only"] = False
        with self.assertRaises(EvidenceError):
            retained_run(record, state, 1)

    def test_cancelled_before_work_or_with_output_cannot_satisfy_q02(self):
        program = self.sources.bundles["P23"]
        q = {"operation": "export", "project_id": "q02", "program_revision": program.program_revision,
             "destination": TARGET, "options": {"end": "0.25", "fps": 1, "helpers": False}}
        cq = {"project_id": "q02", "bundle": program.to_payload()}
        cr = {"status": "succeeded", "accepted_program_revision": program.program_revision}
        for mutation in ("before-work", "output"):
            reader = object.__new__(Reader)
            reader.sources, reader.used = self.sources, set()
            r = {"status": "cancelled", "run_id": None, "result": None, "achieved_level": None,
                 "accepted_program_revision": program.program_revision,
                 "progress": {"cancellation_requested": True, "phase": "cancelled_before_work"}}
            if mutation == "output":
                r["result"] = {"artifact_id": "unexpected-artifact"}
                r["progress"]["phase"] = "cancelled_before_commit"
            reader.exchanges = {"Q02/create-P23": (cq, cr, {}), "Q02/export": (q, r, {})}
            with self.subTest(mutation=mutation), self.assertRaises(EvidenceError):
                reader.q02()

    def test_evidence_descriptor_and_path_cannot_escape_or_rewrite_a_member(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            raw = b'{"receipt":"first"}'
            (root / "receipt.json").write_bytes(raw)
            reader = object.__new__(Reader)
            reader.root, reader.files = root, {}
            receipt = descriptor(raw, "receipt.json")
            self.assertEqual(reader.member(receipt), {"receipt": "first"})
            (root / "receipt.json").write_bytes(b'{"receipt":"other"}')
            with self.assertRaises(EvidenceError):
                reader.member(receipt)
            for name in ("../receipt.json", "/receipt.json", "./receipt.json", "a\\receipt.json"):
                with self.subTest(name=name), self.assertRaises(EvidenceError):
                    safe_path(root, name)
            (root / "linked.json").symlink_to(root / "receipt.json")
            with self.assertRaises(EvidenceError):
                safe_path(root, "linked.json")

    def test_input_cut_default_remains_strict_and_trusted_validator_sees_full_records(self):
        actual = {"commit": "a" * 40, "tree": "b" * 40}
        recorded = {"commit": "c" * 40, "tree": "d" * 40, "status": ""}
        before = {"git": recorded, "files": [{"path": "sentinel", "sha256": "sha256:" + "e" * 64, "bytes": 9}]}
        producer = {"source_commit": recorded["commit"], "source_tree": recorded["tree"]}
        reader = object.__new__(Reader)
        reader.record = producer
        reader.read = lambda name: copy.deepcopy(before)
        with patch("tools.audit_reach_agent_delivery.source_identity", return_value=actual):
            with self.assertRaisesRegex(EvidenceError, "source cuts differ"):
                reader.input_cut()
            calls = []
            reader.input_cut_validator = lambda old, new, report: calls.append((old, new, report))
            reader.input_cut()
            self.assertEqual(calls, [(before, before, producer)])
            self.assertEqual(reader.source_cut, actual)
            reader.input_cut_validator = lambda *args: True
            with self.assertRaisesRegex(EvidenceError, "not a pass flag"):
                reader.input_cut()
            def rejected(*args):
                raise EvidenceError("Git blobs differ")
            reader.input_cut_validator = rejected
            with self.assertRaisesRegex(EvidenceError, "Git blobs differ"):
                reader.input_cut()

    def test_input_cut_injection_cannot_skip_clean_stable_producer_identity(self):
        before = {"git": {"commit": "a" * 40, "tree": "b" * 40, "status": ""}, "files": []}
        for mutation in ("dirty", "changed", "wrong-commit", "wrong-tree"):
            old, new = copy.deepcopy(before), copy.deepcopy(before)
            reader = object.__new__(Reader)
            reader.record = {"source_commit": "a" * 40, "source_tree": "b" * 40}
            if mutation == "dirty":
                old["git"]["status"] = new["git"]["status"] = " M tracked"
            elif mutation == "changed":
                new["files"] = [{"path": "new"}]
            elif mutation == "wrong-commit":
                reader.record["source_commit"] = "c" * 40
            else:
                reader.record["source_tree"] = "d" * 40
            calls = []
            reader.input_cut_validator = lambda *args: calls.append(args)
            reader.read = lambda name: old if name == "inputs-before.json" else new
            with self.subTest(mutation=mutation), self.assertRaises(EvidenceError):
                reader.input_cut()
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
