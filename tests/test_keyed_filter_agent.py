"""Actual .16 authoring boundaries, membership repair and detached inspection."""
from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.cli import main as cli_main
from ontokin.execution_budget import HostPolicy
from ontokin.keyed_filter_agent import KeyedFilterAgentService
from ontokin.keyed_filter_protocol import KeyedFilterProtocol
from ontokin.keyed_reduction_agent import KeyedReductionAgentService
from ontokin.keyed_reduction_protocol import KeyedReductionProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.texture_bundle import load_texture_file_manifest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-filter"
PROFILE, PROTOCOL, TARGET = "keyed-filter-0.1", "ontokin.agent/0.16", "ontokin.glb/0.16"
PROJECT = "keyed-filters"


def source(name="panel-task"):
    return load_texture_file_manifest(FIXTURES / (name + ".files.json"))


def exact_patch(program, old="minimum_width = 0[m];", new="minimum_width = 1.5[m];"):
    offset = program.entry.raw.index(old.encode())
    return {"source_id": "entry", "source_revision": program.entry.revision,
        "element_id": ["sources", "entry"], "start_byte": offset,
        "end_byte": offset + len(old.encode()), "expected_text": old, "replacement": new}


def diagnostic_codes(response):
    result = [d["code"] for d in response.get("diagnostics", [])]
    if response.get("protocol_error"):
        result.append(response["protocol_error"]["code"])
    return result


class KeyedFilterAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        resources = {}
        for path in (ROOT / "docs/language-design").rglob("*.schema.json"):
            value = json.loads(path.read_bytes())
            if "$id" in value:
                resources[value["$id"]] = Resource.from_contents(value)
        registry = Registry().with_resources(resources.items())
        cls.validators = {}
        for path in (ROOT / "docs/language-design/agent-v0.16").glob("*.schema.json"):
            value = json.loads(path.read_bytes())
            Draft202012Validator.check_schema(value)
            cls.validators[path.name] = Draft202012Validator(value, registry=registry)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c083-agent-")
        self.service = KeyedFilterAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": PROJECT,
                "request_id": f"filter-{self.serial}", "operation": operation, **fields}

    def send(self, operation, **fields):
        request = self.request(operation, **fields)
        self.validators["request.schema.json"].validate(request)
        KeyedFilterProtocol.validate_request(request)
        response = self.service.handle(request)
        self.validators["response.schema.json"].validate(response)
        return response

    def success(self, response):
        self.assertEqual(response["status"], "succeeded", response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        return response

    def create(self, program=None):
        program = source() if program is None else program
        self.success(self.send("create", bundle=program.to_payload(),
            expected_program_revision=None, requested_level="constructed"))
        return program

    def inspect(self, program, path):
        return self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": path}, fields=["identity", "source", "values", "matter", "support"],
            limit=1))["result"]["items"][0]

    def test_discovery_current_authority_and_older_defaults(self):
        discovered = self.success(self.send("discover", profile=PROFILE, limit=1000))["result"]
        interface = discovered["keyed_filter_interface"]
        self.assertEqual(interface["operations"], sorted(KeyedFilterProtocol.OPERATIONS))
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        self.assertFalse(interface["filter_provenance"]["writable"])
        for name in ("map_keyed", "reduce_keyed", "filter_keyed"):
            self.assertEqual(next(i for i in discovered["items"] if i["name"] == name)["kind"], "builtin")
        for item in discovered["items"]:
            if item["kind"] == "protocol":
                self.assertEqual(item["name"], PROTOCOL)
            elif item["kind"] == "destination":
                self.assertEqual(item["name"], TARGET)
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success(self.send("discover", profile=PROFILE, limit=1000))["result"]
        self.assertEqual(fresh["keyed_filter_interface"]["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(self.service.database_path.name, "keyed-filter-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.keyed-filter-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(ProtocolError):
            KeyedReductionProtocol.validate_request(self.request("discover", profile=PROFILE, limit=1))
        with AgentService(Path(self.directory.name) / "default") as default:
            response = default.handle(self.request("discover", profile=PROFILE, limit=1))
            self.assertEqual(response["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(response["status"], "rejected")

    def test_aggregate_survivor_and_generated_origins_are_detached_source_locations(self):
        program = self.create()
        first = self.inspect(program, "first")
        widths = first["values"]["widths"]
        record = widths["derived_filters"][-1]
        self.assertEqual(set(record), {"expression", "input", "predicate", "element_type"})
        self.assertEqual(record["element_type"], "Length")
        library = next(u for u in program.units if u.source_id == record["expression"]["source_id"])
        for field in ("expression", "input", "predicate"):
            span = record[field]
            self.assertEqual(span["source_revision"], library.revision)
            self.assertGreater(span["end_byte"], span["start_byte"])
        span = record["expression"]
        self.assertTrue(library.raw[span["start_byte"]:span["end_byte"]].startswith(b"filter_keyed<Length>"))
        self.assertNotIn("derived_filters", first["values"]["candidates"])
        self.assertNotIn("derived_filters", first["values"]["minimum_width"])
        self.assertTrue(first["values"]["selected_total"]["derived_filters"])
        self.assertTrue(first["values"]["selected_total"]["derived_reductions"])
        for entry in widths["value"]:
            self.assertTrue(entry["value"]["derived_filters"])
            self.assertTrue(entry["value"]["derived_transforms"])
        child = self.inspect(program, 'first.panels["left"]')
        self.assertEqual(child["values"]["width"]["value"], 1.0)
        self.assertTrue(child["values"]["width"]["derived_filters"])
        self.assertTrue(child["source"]["generated"]["input_filters"])
        self.assertTrue(child["source"]["generated"]["input_transforms"])
        self.assertEqual(child["source"]["writable_spans"], [])
        self.assertEqual(child["support"]["named_destination"], TARGET)
        record["predicate"]["start_byte"] = -1
        fresh = self.inspect(program, "first")["values"]["widths"]["derived_filters"][-1]
        self.assertGreaterEqual(fresh["predicate"]["start_byte"], 0)

    def test_membership_repair_keeps_sibling_library_assets_and_rejects_stale_cursor(self):
        program = self.create()
        original_sibling = self.inspect(program, 'sibling.panels["left"]')["values"]["width"]["value"]
        page = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"kind": "object"}, fields=["identity"], limit=1))
        cursor = page["next_cursor"]
        self.assertIsNotNone(cursor)
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program)]))
        repaired = source("panel-task-repaired")
        self.assertEqual(response["accepted_program_revision"], repaired.program_revision)
        retained = self.service.read_program(PROJECT, repaired.program_revision)
        self.assertEqual(retained.to_payload()["modules"], program.to_payload()["modules"])
        self.assertEqual(retained.to_payload()["assets"], program.to_payload()["assets"])
        first = self.inspect(repaired, "first")
        self.assertEqual([entry["key"] for entry in first["values"]["widths"]["value"]], ["right"])
        self.assertEqual(first["values"]["selected_total"]["value"], 2.0)
        self.assertEqual(self.inspect(repaired, 'first.panels["right"]')["values"]["width"]["value"], 2.0)
        self.assertEqual(self.inspect(repaired, 'sibling.panels["left"]')["values"]["width"]["value"], original_sibling)
        stale = self.send("inspect", program_revision=repaired.program_revision,
            selector={"kind": "object"}, fields=["identity"], limit=1, cursor=cursor)
        self.assertIn("OKL-E-REVISION", diagnostic_codes(stale))
        stale_edit = self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program)])
        self.assertIn("OKL-E-REVISION", diagnostic_codes(stale_edit))
        self.assertEqual(self.service.accepted_revision(PROJECT), repaired.program_revision)
        self.assertEqual(len(self.inspect(program, "first")["values"]["widths"]["value"]), 2)

    def test_schema_rejects_invented_filter_keys_and_missing_predicate(self):
        program = self.create()
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "first"}, fields=["values"], limit=1))
        detached = copy.deepcopy(response)
        record = detached["result"]["items"][0]["values"]["widths"]["derived_filters"][-1]
        record["key"] = "invented-filter-identity"
        self.assertTrue(list(self.validators["response.schema.json"].iter_errors(detached)))
        del record["key"]
        del record["predicate"]
        self.assertTrue(list(self.validators["response.schema.json"].iter_errors(detached)))

    def test_reopen_requires_current_host_authority(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        program = self.create(source("panel-task-higher-budget"))
        self.service.close()
        self.service = KeyedFilterAgentService(self.directory.name)
        for operation, fields in (
            ("validate", {"requested_level": "represented"}),
            ("inspect", {"selector": {"element_id": ["assets", "label"]}, "fields": ["source"],
                         "limit": 1, "asset_slice": {"offset": 0, "max_bytes": 1}})):
            with self.subTest(operation=operation):
                response = self.send(operation, program_revision=program.program_revision, **fields)
                self.assertIn("OKL-E-RESOURCE", diagnostic_codes(response))
                self.assertEqual(self.service.accepted_revision(PROJECT), program.program_revision)

    def test_predecessor_agent_refuses_new_source_and_keeps_own_controls(self):
        with KeyedReductionAgentService(Path(self.directory.name) / "older") as old:
            request = self.request("create", bundle=source().to_payload(),
                expected_program_revision=None, requested_level="represented")
            request["schema_version"] = "ontokin.agent/0.15"
            response = old.handle(request)
            self.assertIn("OKL-E-RESOURCE", diagnostic_codes(response))
            self.assertEqual(response["execution_budget"]["budget_reason"], "invalid_declaration")
            self.assertIsNone(old.accepted_revision(PROJECT))
            request["request_id"] += "-control"
            request["bundle"] = source("control-panel-task").to_payload()
            self.assertEqual(old.handle(request)["status"], "succeeded")

    def test_cli_explicit_protocol_forwards_host_ceilings_and_keeps_default(self):
        request = self.request("discover", profile=PROFILE, limit=1000)
        path = Path(self.directory.name) / "request.json"
        path.write_text(json.dumps(request))
        output = io.StringIO()
        with redirect_stdout(output):
            status = cli_main(["agent", "--protocol", PROTOCOL, "--store", str(Path(self.directory.name) / "cli-new"),
                               "--request", str(path), "--wait"], host_policy=HostPolicy(400000, 80000))
        self.assertEqual(status, 0)
        response = json.loads(output.getvalue())
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.assertEqual(response["result"]["keyed_filter_interface"]["host_ceilings"],
                         {"max_operations": 400000, "max_elapsed_ms": 80000})
        output = io.StringIO()
        with redirect_stdout(output):
            status = cli_main(["agent", "--store", str(Path(self.directory.name) / "cli-default"),
                               "--request", str(path), "--wait"])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(output.getvalue())["schema_version"], "ontokin.agent/0.1")


if __name__ == "__main__":
    unittest.main()
