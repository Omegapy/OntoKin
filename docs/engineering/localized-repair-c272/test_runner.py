"""Focused tests of the C272 runner (TASK-011 to TASK-015); they drive the real Agent/0.2 service."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runner  # noqa: E402

V1_ACCEPTED = "443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a"
V2_ACCEPTED = "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123"
HINGES = "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"
PROGRAM_065 = "sha256:8f9d976568e2a9fa39573e3fb90f616529097241a098b21d4eb22eabe4b7032f"
PROGRAM_075 = "sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082"


def lines(case_dir: Path) -> list[dict]:
    return runner.read_lines(case_dir / "record" / "exchanges.jsonl")


class RunnerCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="c272-runner-")).resolve()
        cls.out = cls.tmp / "run"
        cls.results = {r["caseId"]: r for r in runner.run_all(cls.out)}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def case(self, case_id):
        base = self.out / "cases" / case_id
        return base, json.loads((base / "record" / "accepted-state.json").read_text())

    def test_every_case_completes_from_its_own_new_store(self):
        stores = set()
        for case_id in runner.CASES:
            self.assertEqual(self.results[case_id]["status"], "completed", self.results[case_id].get("error"))
            base, _ = self.case(case_id)
            self.assertTrue((base / "store").is_dir())
            stores.add(base / "store")
            first = [x for x in lines(base) if x["kind"] == "request"][0]["request"]
            self.assertEqual(first["operation"], "create")
            self.assertEqual(first["schema_version"], "ontokin.agent/0.2")
        self.assertEqual(len(stores), 3)

    def test_start_identities_match_the_corpus_and_precede_the_edit(self):
        for case_id, program, entry in (("V1", PROGRAM_065, V2_ACCEPTED), ("V2", PROGRAM_075, V1_ACCEPTED),
                                        ("N1", PROGRAM_065, V2_ACCEPTED)):
            base, state = self.case(case_id)
            self.assertEqual(state["starting_accepted_revision"], program)
            self.assertEqual(state["hashes"]["start.source"], {"main.ok": entry, "hinges.ok": HINGES})
            log = lines(base)
            labels = [x["label"] for x in log if x["kind"] == "request"]
            self.assertLess(labels.index("export-baseline"), labels.index("edit"))
            self.assertEqual(set(state["hashes"]["start.artifacts"]), {"scene.glb", "scene.semantic.json"})

    def test_valid_edits_change_only_the_selected_literal(self):
        for case_id, accepted, new in (("V1", V1_ACCEPTED, PROGRAM_075), ("V2", V2_ACCEPTED, PROGRAM_065)):
            base, state = self.case(case_id)
            self.assertEqual(state["new_accepted_revision"], new)
            self.assertEqual(state["hashes"]["retained.source"], {"main.ok": accepted, "hinges.ok": HINGES})
            start = (base / "record/files/start/main.ok").read_bytes()
            final = (base / "record/files/retained/main.ok").read_bytes()
            changed = [i for i, (a, b) in enumerate(zip(start, final)) if a != b]
            self.assertEqual(len(start), len(final))
            self.assertTrue(changed and all(1044 <= i < 1051 for i in changed))
            self.assertEqual((base / "record/files/start/hinges.ok").read_bytes(),
                             (base / "record/files/retained/hinges.ok").read_bytes())
            self.assertIn(b'digest "sha256:' + HINGES.encode(), final)

    def test_n1_is_refused_by_the_service_and_preserves_every_byte(self):
        base, state = self.case("N1")
        edit = [x for x in lines(base) if x["kind"] == "response" and x["label"] == "edit"][0]["response"]
        self.assertEqual(edit["status"], "rejected")
        unit = [d for d in edit["diagnostics"] if d["code"] == "OKL-E-UNIT"]
        self.assertEqual(unit[0]["details"], {"expected": "Length", "actual": "Mass"})
        self.assertTrue(state["diagnostic_translation"]["translated"])
        self.assertIsNone(state["new_accepted_revision"])
        self.assertEqual(state["accepted_revisions_observed_after_each_request"], [PROGRAM_065])
        self.assertEqual(state["hashes"]["start.source"], state["hashes"]["retained.source"])
        self.assertEqual(state["hashes"]["start.artifacts"], state["hashes"]["retained.artifacts"])
        labels = [x["label"] for x in lines(base) if x["kind"] == "request"]
        self.assertIn("artifact-after-rejection", labels)
        recorded = json.loads((runner.ROOT / "docs/engineering/semantic-export-c210/evidence/proof/invalid-edit.json").read_text())
        self.assertEqual(unit[0]["message"], recorded["diagnostics"][0]["message"])
        self.assertEqual(edit["program_revision"], recorded["program_revision"])

    def test_retry_and_stale_cases_are_executed_with_actual_responses(self):
        for case_id in ("V1", "V2"):
            cases = {c["case"]: c for c in self.results[case_id]["protocol_cases"]}
            self.assertTrue(cases["identical retry"]["equal_to_first_response"])
            self.assertEqual(cases["changed-payload retry"]["protocol_error"]["code"], "OKL-E-REQUEST-ID")
            self.assertEqual(cases["stale-revision edit"]["status"], "rejected")
            self.assertIn("OKL-E-REVISION", cases["stale-revision edit"]["diagnostic_codes"])
        n1 = {c["case"]: c for c in self.results["N1"]["protocol_cases"]}
        self.assertEqual(n1["identical retry"]["status"], "rejected")
        self.assertTrue(n1["identical retry"]["equal_to_first_response"])

    def test_the_record_is_outside_the_store_and_the_client_directory(self):
        for case_id in runner.CASES:
            base, state = self.case(case_id)
            record, client, store = base / "record", base / "client", base / "store"
            for a, b in ((record, client), (record, store), (client, store)):
                self.assertFalse(a.is_relative_to(b) or b.is_relative_to(a))
            self.assertEqual(state["model"], runner.NOT_APPLICABLE)
            responses = [x for x in lines(base) if x["kind"] == "response"]
            self.assertTrue(all("data_base64" not in json.dumps(x) for x in responses))


class RunnerFailures(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="c272-runner-fail-")).resolve()

    def tearDown(self):
        for path in self.tmp.rglob("*"):
            if path.is_dir():
                path.chmod(stat.S_IRWXU)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_one_altered_input_byte_stops_the_run_before_the_service(self):
        def read(path):
            raw = (runner.ROOT / path).read_bytes()
            return raw[:100] + bytes([raw[100] ^ 1]) + raw[101:] if path.endswith("before.main.ok") else raw
        def refuse(_store):
            raise AssertionError("the service must not be called")
        outcome = runner.run_case("V1", self.tmp / "run", service_factory=refuse, read=read)
        self.assertEqual(outcome["status"], "input_mismatch")
        kinds = [x["kind"] for x in lines(self.tmp / "run/cases/V1")]
        self.assertEqual(kinds, ["case-start", "case-end"])

    def test_a_store_that_cannot_be_written_keeps_the_record(self):
        from ontokin.program_agent import ProgramAgentService
        locked = self.tmp / "locked"
        locked.mkdir()
        locked.chmod(stat.S_IRUSR | stat.S_IXUSR)
        outcome = runner.run_case("N1", self.tmp / "run",
                                  service_factory=lambda _store: ProgramAgentService(locked / "store", protocol=runner.PROTOCOL))
        self.assertEqual(outcome["status"], "crash")
        record = self.tmp / "run/cases/N1/record"
        self.assertTrue((record / "outcome.json").is_file())
        self.assertEqual([x["kind"] for x in lines(self.tmp / "run/cases/N1")][-1], "case-end")


if __name__ == "__main__":
    unittest.main()
