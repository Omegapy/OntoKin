"""Exercise the explicit .14 protocol boundary and source repair authority."""
from __future__ import annotations

import base64
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
from ontokin.keyed_transform_agent import KeyedTransformAgentService
from ontokin.keyed_transform_protocol import KeyedTransformProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.texture_agent import TextureAgentService
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.texture_protocol import TextureProtocol


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-transform"
PROFILE, PROTOCOL, TARGET = "keyed-transform-0.1", "ontokin.agent/0.14", "ontokin.glb/0.14"
PROJECT = "keyed-transforms"


def source(name="panel-task"):
    return load_texture_file_manifest(FIXTURES / (name + ".files.json"))


def exact_patch(program, old="scale = 1[m];", new="scale = 1.5[m];"):
    offset = program.entry.raw.index(old.encode())
    return {"source_id": "entry", "source_revision": program.entry.revision,
        "element_id": ["sources", "entry"], "start_byte": offset,
        "end_byte": offset + len(old.encode()), "expected_text": old, "replacement": new}


def diagnostic_codes(response):
    result = [d["code"] for d in response.get("diagnostics", [])]
    if response.get("protocol_error"):
        result.append(response["protocol_error"]["code"])
    return result


class KeyedTransformAgentTests(unittest.TestCase):
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
        for path in (ROOT / "docs/language-design/agent-v0.14").glob("*.schema.json"):
            value = json.loads(path.read_bytes())
            Draft202012Validator.check_schema(value)
            cls.validators[path.name] = Draft202012Validator(value, registry=registry)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c081-agent-")
        self.service = KeyedTransformAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": PROJECT,
                "request_id": f"keyed-{self.serial}", "operation": operation, **fields}

    def send(self, operation, **fields):
        request = self.request(operation, **fields)
        self.validators["request.schema.json"].validate(request)
        KeyedTransformProtocol.validate_request(request)
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

    def test_discovery_is_current_and_defaults_keep_separate_bindings(self):
        discovered = self.success(self.send("discover", profile=PROFILE, limit=1000))["result"]
        interface = discovered["keyed_transform_interface"]
        self.assertEqual(interface["operations"], sorted(KeyedTransformProtocol.OPERATIONS))
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        self.assertFalse(interface["transform_provenance"]["writable"])
        self.assertEqual(next(i for i in discovered["items"] if i["name"] == "map_keyed")["kind"], "builtin")
        for item in discovered["items"]:
            if item["kind"] == "protocol":
                self.assertEqual(item["name"], PROTOCOL)
            elif item["kind"] == "destination":
                self.assertEqual(item["name"], TARGET)
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success(self.send("discover", profile=PROFILE, limit=1000))["result"]
        self.assertEqual(fresh["keyed_transform_interface"]["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(self.service.database_path.name, "keyed-transform-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.keyed-transform-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(ProtocolError):
            TextureProtocol.validate_request(self.request("discover", profile=PROFILE, limit=1))
        with AgentService(Path(self.directory.name) / "default") as default:
            rejected = default.handle(self.request("discover", profile=PROFILE, limit=1))
            self.assertEqual(rejected["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(rejected["status"], "rejected")

    def test_scalar_and_generated_provenance_are_source_bound_and_read_only(self):
        program = self.create()
        first = self.inspect(program, "first")
        transform = first["values"]["widths"]["derived_transforms"][0]
        self.assertEqual(transform["input_element_type"], "Real")
        self.assertEqual(transform["output_element_type"], "Length")
        self.assertNotIn("key", transform)
        self.assertNotIn("derived_transforms", first["values"]["scale"])
        library = next(u for u in program.units if u.source_id == transform["expression"]["source_id"])
        expression = transform["expression"]
        self.assertEqual(expression["source_revision"], library.revision)
        self.assertTrue(library.raw[expression["start_byte"]:expression["end_byte"]].startswith(b"map_keyed<Length>"))
        for entry in first["values"]["widths"]["value"]:
            derived = entry["value"]["derived_transforms"][-1]
            self.assertEqual(derived["key"], entry["key"])
            origin = derived["input_entry"]
            self.assertTrue(library.raw[origin["start_byte"]:origin["end_byte"]].startswith(json.dumps(entry["key"]).encode() + b":"))
        leaf = self.inspect(program, 'first.panels["left"]')
        derived = leaf["values"]["width"]["derived_transforms"][-1]
        self.assertEqual(derived["key"], "left")
        entry = derived["input_entry"]
        self.assertTrue(library.raw[entry["start_byte"]:entry["end_byte"]].startswith(b'"left":'))
        self.assertTrue(leaf["source"]["generated"]["input_transforms"])
        self.assertFalse(leaf["source"]["generated"]["unique_declaration_span"])
        self.assertEqual(leaf["source"]["writable_spans"], [])
        self.assertEqual(leaf["matter"]["own_mass_kg"], 0)
        self.assertEqual(leaf["matter"]["owned_aggregate_mass_kg"], 0)
        self.assertEqual(leaf["matter"]["collision"], "disabled")
        self.assertEqual(leaf["support"]["named_destination"], TARGET)
        invalid_scope = exact_patch(program)
        invalid_scope["element_id"] = leaf["element_id"]
        request = self.request("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[invalid_scope])
        response = self.service.handle(request)
        self.assertIn("OKA-E-REQUEST", diagnostic_codes(response))
        self.assertEqual(self.service.accepted_revision(PROJECT), program.program_revision)

    def test_scoped_repair_preserves_library_assets_sibling_and_stale_cursors(self):
        program = self.create()
        initial_sibling = self.inspect(program, 'sibling.panels["left"]')["values"]["width"]["value"]
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
        self.assertEqual(self.inspect(repaired, 'first.panels["left"]')["values"]["width"]["value"], 1.5)
        self.assertEqual(self.inspect(repaired, 'sibling.panels["left"]')["values"]["width"]["value"], initial_sibling)
        stale = self.send("inspect", program_revision=repaired.program_revision,
            selector={"kind": "object"}, fields=["identity"], limit=1, cursor=cursor)
        self.assertIn("OKL-E-REVISION", diagnostic_codes(stale))
        stale_edit = self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program)])
        self.assertIn("OKL-E-REVISION", diagnostic_codes(stale_edit))
        self.assertEqual(self.service.accepted_revision(PROJECT), repaired.program_revision)

    def test_detached_unknown_origin_schema_keeps_null_and_rejects_invented_authority(self):
        """Schema coverage only: authored fixture origins are all known."""
        program = self.create()
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": 'first.panels["left"]'}, fields=["values"], limit=1))
        detached = copy.deepcopy(response)
        record = detached["result"]["items"][0]["values"]["width"]["derived_transforms"][-1]
        self.assertIsInstance(record["input_entry"], dict)
        record["input_entry"] = None
        self.validators["response.schema.json"].validate(detached)
        self.assertIsInstance(response["result"]["items"][0]["values"]["width"]["derived_transforms"][-1]["input_entry"], dict)
        record["writable_span"] = {"start_byte": 0, "end_byte": 1}
        self.assertTrue(list(self.validators["response.schema.json"].iter_errors(detached)))
        del record["writable_span"]
        del record["key"]
        self.assertTrue(list(self.validators["response.schema.json"].iter_errors(detached)))

    def test_reopened_policy_reauthorizes_assets_and_source(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        program = self.create(source("panel-task-higher-budget"))
        self.service.close()
        self.service = KeyedTransformAgentService(self.directory.name)
        for operation, fields in (
            ("validate", {"requested_level": "represented"}),
            ("inspect", {"selector": {"element_id": ["assets", "label"]}, "fields": ["source"],
                         "limit": 1, "asset_slice": {"offset": 0, "max_bytes": 1}})):
            with self.subTest(operation=operation):
                response = self.send(operation, program_revision=program.program_revision, **fields)
                self.assertIn("OKL-E-RESOURCE", diagnostic_codes(response))
                self.assertEqual(self.service.accepted_revision(PROJECT), program.program_revision)

    def test_older_agent_cannot_accept_or_relabel_new_source(self):
        program = source()
        old = TextureAgentService(Path(self.directory.name) / "old")
        try:
            request = self.request("create", bundle=program.to_payload(),
                expected_program_revision=None, requested_level="represented")
            request["schema_version"] = "ontokin.agent/0.13"
            response = old.handle(request)
            self.assertIn("OKL-E-RESOURCE", diagnostic_codes(response))
            self.assertEqual(response["execution_budget"]["budget_reason"], "invalid_declaration")
            self.assertIsNone(old.accepted_revision(PROJECT))
            control = source("control-panel-task")
            request["request_id"] += "-control"
            request["bundle"] = control.to_payload()
            self.assertEqual(old.handle(request)["status"], "succeeded")
        finally:
            old.close()

    def test_cli_requires_explicit_protocol_and_preserves_default(self):
        request = self.request("discover", profile=PROFILE, limit=1000)
        path = Path(self.directory.name) / "request.json"
        path.write_text(json.dumps(request))
        output = io.StringIO()
        with redirect_stdout(output):
            status = cli_main(["agent", "--protocol", PROTOCOL, "--store", str(Path(self.directory.name) / "cli-new"),
                               "--request", str(path), "--wait"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output.getvalue())["schema_version"], PROTOCOL)
        output = io.StringIO()
        with redirect_stdout(output):
            status = cli_main(["agent", "--store", str(Path(self.directory.name) / "cli-default"),
                               "--request", str(path), "--wait"])
        self.assertEqual(status, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["schema_version"], "ontokin.agent/0.1")
        self.assertEqual(response["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
