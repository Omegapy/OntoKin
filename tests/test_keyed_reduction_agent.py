"""Exercise the explicit .15 protocol boundary and source repair authority."""
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
from ontokin.keyed_reduction_agent import KeyedReductionAgentService
from ontokin.keyed_reduction_protocol import KeyedReductionProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.keyed_transform_agent import KeyedTransformAgentService
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.keyed_transform_protocol import KeyedTransformProtocol


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-reduction"
PROFILE, PROTOCOL, TARGET = "keyed-reduction-0.1", "ontokin.agent/0.15", "ontokin.glb/0.15"
PROJECT = "keyed-reductions"


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


class KeyedReductionAgentTests(unittest.TestCase):
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
        for path in (ROOT / "docs/language-design/agent-v0.15").glob("*.schema.json"):
            value = json.loads(path.read_bytes())
            Draft202012Validator.check_schema(value)
            cls.validators[path.name] = Draft202012Validator(value, registry=registry)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c082-agent-")
        self.service = KeyedReductionAgentService(self.directory.name)
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
        KeyedReductionProtocol.validate_request(request)
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
        interface = discovered["keyed_reduction_interface"]
        self.assertEqual(interface["operations"], sorted(KeyedReductionProtocol.OPERATIONS))
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        self.assertFalse(interface["reduction_provenance"]["writable"])
        self.assertEqual(next(i for i in discovered["items"] if i["name"] == "map_keyed")["kind"], "builtin")
        for item in discovered["items"]:
            if item["kind"] == "protocol":
                self.assertEqual(item["name"], PROTOCOL)
            elif item["kind"] == "destination":
                self.assertEqual(item["name"], TARGET)
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success(self.send("discover", profile=PROFILE, limit=1000))["result"]
        self.assertEqual(fresh["keyed_reduction_interface"]["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(self.service.database_path.name, "keyed-reduction-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.keyed-reduction-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(ProtocolError):
            KeyedTransformProtocol.validate_request(self.request("discover", profile=PROFILE, limit=1))
        with AgentService(Path(self.directory.name) / "default") as default:
            rejected = default.handle(self.request("discover", profile=PROFILE, limit=1))
            self.assertEqual(rejected["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(rejected["status"], "rejected")

    def test_aggregate_and_generated_provenance_are_source_bound_and_detached(self):
        program = self.create()
        first = self.inspect(program, "first")
        aggregate = first["values"]["aggregate"]
        self.assertEqual(aggregate["value"], 1.0)
        reduction = aggregate["derived_reductions"][-1]
        self.assertEqual(reduction["input_element_type"], "Length")
        self.assertEqual(reduction["accumulator_type"], "Length")
        self.assertEqual(set(reduction), {"expression", "input", "seed", "body", "input_element_type", "accumulator_type"})
        library = next(u for u in program.units if u.source_id == reduction["expression"]["source_id"])
        for field in ("expression", "input", "seed", "body"):
            location = reduction[field]
            self.assertEqual(location["source_revision"], library.revision)
            self.assertGreater(location["end_byte"], location["start_byte"])
        location = reduction["expression"]
        self.assertTrue(library.raw[location["start_byte"]:location["end_byte"]].startswith(b"reduce_keyed<Length>"))
        self.assertTrue(aggregate["derived_transforms"])
        self.assertNotIn("derived_reductions", first["values"]["scale"])
        leaf = self.inspect(program, 'first.panels["left"]')
        self.assertEqual(leaf["values"]["width"]["value"], 1.0)
        self.assertTrue(leaf["values"]["width"]["derived_reductions"])
        self.assertTrue(leaf["source"]["generated"]["input_reductions"])
        self.assertTrue(leaf["source"]["generated"]["input_transforms"])
        self.assertEqual(leaf["source"]["writable_spans"], [])
        self.assertEqual(leaf["support"]["named_destination"], TARGET)
        reduction["expression"]["start_byte"] = -1
        self.assertGreaterEqual(self.inspect(program, "first")["values"]["aggregate"]["derived_reductions"][-1]["expression"]["start_byte"], 0)

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

    def test_reduction_schema_rejects_invented_editable_keys_and_missing_seed(self):
        program = self.create()
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "first"}, fields=["values"], limit=1))
        detached = copy.deepcopy(response)
        record = detached["result"]["items"][0]["values"]["aggregate"]["derived_reductions"][-1]
        record["key"] = "invented-iteration-key"
        self.assertTrue(list(self.validators["response.schema.json"].iter_errors(detached)))
        del record["key"]
        del record["seed"]
        self.assertTrue(list(self.validators["response.schema.json"].iter_errors(detached)))

    def test_reopened_policy_reauthorizes_assets_and_source(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        program = self.create(source("panel-task-higher-budget"))
        self.service.close()
        self.service = KeyedReductionAgentService(self.directory.name)
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
        old = KeyedTransformAgentService(Path(self.directory.name) / "old")
        try:
            request = self.request("create", bundle=program.to_payload(),
                expected_program_revision=None, requested_level="represented")
            request["schema_version"] = "ontokin.agent/0.14"
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
                               "--request", str(path), "--wait"], host_policy=HostPolicy(400000, 80000))
        self.assertEqual(status, 0)
        response = json.loads(output.getvalue())
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.assertEqual(response["result"]["keyed_reduction_interface"]["host_ceilings"],
                         {"max_operations": 400000, "max_elapsed_ms": 80000})
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
