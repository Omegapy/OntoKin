"""Actual-source helpers for Agent/0.6 tests; frozen expectations stay external."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from ontokin.bundle import load_file_manifest
from ontokin.program_agent import ProgramAgentService

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/language-design/planar-reach-v0.1"
SUPPLEMENT = DATA / "draft2-supplements"
PROTOCOL = "ontokin.agent/0.6"
PROFILE = "planar-reach-0.1"
TARGET = "ontokin.glb/0.6"
CASES = {case["id"]: (DATA, case) for case in json.loads((DATA / "acceptance.json").read_text())["source_cases"]}
CASES.update({case["id"]: (SUPPLEMENT, case) for case in json.loads((SUPPLEMENT / "acceptance.json").read_text())["source_cases"]})
PROTOCOL_CASES = json.loads((SUPPLEMENT / "protocol-cases.json").read_text())["protocol_cases"]
STEPS = {step["id"]: step for case in PROTOCOL_CASES for step in case["steps"]}


def source_case(name):
    directory, case = CASES[name]
    program = load_file_manifest(directory / case["file_manifest"])
    assert program.program_revision == case["program_revision"], name
    return program


def exact_patch(before, after, element_id):
    """Smallest single UTF-8-safe source difference, bound to supplied authority."""
    left, right = before.entry.raw, after.entry.raw
    start = 0
    while start < min(len(left), len(right)) and left[start] == right[start]:
        start += 1
    while start and (left[start:start + 1] and left[start] & 0xC0 == 0x80):
        start -= 1
    old_end, new_end = len(left), len(right)
    while old_end > start and new_end > start and left[old_end - 1] == right[new_end - 1]:
        old_end -= 1
        new_end -= 1
    while old_end < len(left) and left[old_end] & 0xC0 == 0x80:
        old_end += 1
        new_end += 1
    return {"source_id": "entry", "source_revision": before.entry.revision,
            "element_id": list(element_id), "start_byte": start, "end_byte": old_end,
            "expected_text": left[start:old_end].decode(), "replacement": right[start:new_end].decode()}


class ReachAgentFixture:
    """Mixin with no test methods, so importing it does not duplicate a cohort."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = ProgramAgentService(self.tmp.name, protocol=PROTOCOL)
        self.number = 0
        self.exchanges = []

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def request(self, operation, **fields):
        self.number += 1
        return {"schema_version": PROTOCOL, "project_id": "reach", "request_id": str(self.number),
                "operation": operation, **fields}

    def send(self, operation, **fields):
        request = self.request(operation, **fields)
        response = self.service.handle(request)
        self.exchanges.append((request, response))
        return response

    def success(self, response):
        self.assertEqual(response["status"], "succeeded", response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.assertIsNone(response["protocol_error"], response)
        return response

    def error(self, response, code):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        codes = [diagnostic["code"] for diagnostic in response["diagnostics"]]
        if response.get("protocol_error"):
            codes.append(response["protocol_error"]["code"])
        self.assertIn(code, codes, response)
        return response

    def create(self, name="P01", level="constructed"):
        program = source_case(name)
        response = self.success(self.send("create", bundle=program.to_payload(),
                                         expected_program_revision=None, requested_level=level))
        self.assertEqual(response["accepted_program_revision"], program.program_revision)
        return program, response

    def evaluate(self, program, until="3", run=None):
        return self.success(self.send("evaluate", program_revision=program.program_revision,
                                      run_id=run, until_seconds=until))

    def actions(self, program, *, run=None, time=None, side="after", selector=None, **kwargs):
        context = {} if run is None else {"run_id": run}
        if time is not None:
            context["time"] = {"seconds": time, "side": side}
        return self.send("inspect", program_revision=program.program_revision,
                         selector={"kind": "action"} if selector is None else selector,
                         fields=["actions"], limit=128, **context, **kwargs)

    def effects(self, project="reach"):
        with self.service._store.connection() as db:
            return {name: db.execute("SELECT count(*) FROM " + name + " WHERE project_id=?", (project,)).fetchone()[0]
                    for name in ("runs", "artifacts")}

    def projection(self, response, path="reach"):
        items = response["result"]["items"]
        matching = [item for item in items if item["path"] == path]
        self.assertEqual(len(matching), 1, response)
        records = matching[0]["actions"]
        self.assertEqual(len(records), 1, response)
        return records[0]

    def assert_context(self, record, program, accepted, *, candidate=False, run=None, kind="run_sample"):
        self.assertEqual(record["program_revision"], program.program_revision)
        self.assertEqual(record["accepted_program_revision"], accepted)
        self.assertEqual(record["candidate_only"], candidate)
        self.assertEqual(record["context_origin"], "agent")
        if record["current"]["available"]:
            observation = record["current"]["value"]["observation"]
            self.assertEqual(observation["run_id"], run)
            self.assertEqual(observation["context_kind"], kind)


def reach_records(response):
    for item in response["result"].get("items", []):
        if isinstance(item.get("actions"), list):
            yield from (record for record in item["actions"] if record.get("kind") == "reach_planar")
