"""Explicit .20 binding discovery, closed schemas and unchanged old defaults."""
from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.cli import main as cli_main
from ontokin.execution_budget import HostPolicy
from ontokin.keyed_rekey_agent import KeyedRekeyAgentService
from ontokin.keyed_rekey_protocol import KeyedRekeyProtocol
from ontokin.program_agent import ProgramAgentService
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.string_concat_agent import StringConcatAgentService
from ontokin.string_concat_protocol import StringConcatProtocol
from ontokin.syntax02 import parse_source_unit
from ontokin.texture_bundle import load_texture_file_manifest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/string-concat"
PROFILE = "string-concat-0.1"
PROTOCOL = "ontokin.agent/0.20"
TARGET = "ontokin.glb/0.20"


def validator(name):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    resources = {}
    for path in (ROOT / "docs/language-design").rglob("*.schema.json"):
        value = json.loads(path.read_bytes())
        if "$id" in value:
            resources[value["$id"]] = Resource.from_contents(value)
    schema = json.loads((ROOT / f"docs/language-design/agent-v0.20/{name}.schema.json").read_bytes())
    return Draft202012Validator(schema, registry=Registry().with_resources(resources.items()))


class StringConcatInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c087-interface-")
        self.service = StringConcatAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation="discover", **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "concat-interface",
            "request_id": f"request-{self.serial}", "operation": operation,
            **({"profile": PROFILE, "limit": 1000} if operation == "discover" else {}), **fields}

    def discovery(self):
        request = self.request()
        validator("request").validate(request)
        response = self.service.handle(request)
        self.assertEqual(response["status"], "succeeded", response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        validator("response").validate(response)
        return response["result"]

    def test_explicit_discovery_advertises_complete_current_authority(self):
        result = self.discovery()
        interface = result["string_concat_interface"]
        self.assertEqual(interface["operations"], sorted(StringConcatProtocol.OPERATIONS))
        self.assertEqual(StringConcatProtocol.OPERATIONS, KeyedRekeyProtocol.OPERATIONS)
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(interface["delivery_contract"], TARGET)
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        operation = interface["source_expressions"]["string_concat"]
        self.assertEqual(operation["inputs"], ["String", "String"])
        self.assertEqual(operation["max_result_utf8_bytes"], 65536)
        self.assertEqual(operation["max_total_utf8_bytes"], 4194304)
        self.assertEqual(operation["scan_quantum_utf8_bytes"], 64)
        self.assertEqual(operation["cancellation_stages"], ["string_concat_admission",
            "string_concat_scan", "string_concat_allocation", "string_concat_publication"])
        self.assertTrue(interface["source_expressions"]["rekey_keyed"]["string_concatenation"])
        self.assertFalse(interface["rekey_provenance"]["writable"])
        self.assertTrue(any(item["capability"] == "pure_string_concatenation" for item in result["items"]))

    def test_detached_discovery_cannot_mutate_new_or_inherited_contracts(self):
        first = self.discovery()["string_concat_interface"]
        first["source_expressions"]["string_concat"]["cancellation_stages"].clear()
        first["source_expressions"]["rekey_keyed"]["string_concatenation"] = False
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.discovery()["string_concat_interface"]
        self.assertEqual(fresh["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(len(fresh["source_expressions"]["string_concat"]["cancellation_stages"]), 4)
        self.assertTrue(fresh["source_expressions"]["rekey_keyed"]["string_concatenation"])
        with KeyedRekeyAgentService(self.directory.name) as predecessor:
            request = {**self.request(), "schema_version": "ontokin.agent/0.19", "profile": "keyed-rekey-0.1"}
            response = predecessor.handle(request)
            self.assertEqual(response["status"], "succeeded", response)
            old = response["result"]["keyed_rekey_interface"]
            self.assertFalse(old["source_expressions"]["rekey_keyed"]["string_concatenation"])
            self.assertNotIn("string_concat", old["source_expressions"])
            self.assertEqual(fresh["source_expressions"]["zip_keyed"], old["source_expressions"]["zip_keyed"])
            self.assertNotEqual(predecessor.database_path, self.service.database_path)

    def test_store_reopens_exact_contract_without_registering_new_defaults(self):
        expected = self.discovery()
        self.assertEqual(self.service.database_path.name, "string-concat-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.string-concat-program-agent-store/0.1")
        self.service.close()
        self.service = StringConcatAgentService(self.directory.name)
        self.assertEqual(self.discovery()["revision"], expected["revision"])
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with ProgramAgentService(Path(self.directory.name) / "program-default") as default:
            self.assertEqual(default._protocol.SCHEMA_VERSION, "ontokin.agent/0.2")
        with AgentService(Path(self.directory.name) / "core-default") as default:
            response = default.handle(self.request())
            self.assertEqual(response["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(response["status"], "rejected")

    def test_request_schema_and_protocol_reject_cross_contract_and_extra_source_shape(self):
        good = self.request()
        StringConcatProtocol.validate_request(good)
        with self.assertRaises(ProtocolError):
            KeyedRekeyProtocol.validate_request(good)
        wrong = {**good, "schema_version": "ontokin.agent/0.19"}
        self.assertTrue(list(validator("request").iter_errors(wrong)))
        with self.assertRaises(ProtocolError):
            StringConcatProtocol.validate_request(wrong)
        inspect = self.request("inspect", program_revision="sha256:" + "0" * 64,
            selector={"kind": "source"}, fields=["source"], limit=1)
        StringConcatProtocol.validate_request(inspect)
        validator("request").validate(inspect)
        extra = {**inspect, "source_slice": {"offset": 0, "max_bytes": 128}}
        self.assertTrue(list(validator("request").iter_errors(extra)))
        with self.assertRaises(ProtocolError):
            StringConcatProtocol.validate_request(extra)

    def test_response_preserves_closed_rekey_lineage(self):
        from jsonschema import Draft202012Validator
        schema = validator("response").schema
        record = Draft202012Validator({"$schema": schema["$schema"], "$defs": schema["$defs"],
                                      "$ref": "#/$defs/derived_rekey"})
        expected = json.loads((ROOT / "examples/keyed-rekey/expected.json").read_bytes())
        singleton = next(case for case in expected["cases"] if case["name"] == "singleton")["expected"]
        aggregate = singleton["root_aggregate_rekey_record"]
        selected = singleton["root_selected_rekey_records"]["ns.a"]
        record.validate(aggregate)
        record.validate(selected)
        for mutation in ({**aggregate, "old_key": "a"}, {**selected, "new_key": None},
                         {**selected, "editable_key": "a"}):
            self.assertTrue(list(record.iter_errors(mutation)))
        broken = copy.deepcopy(selected)
        broken["input_entry"]["writable"] = True
        self.assertTrue(list(record.iter_errors(broken)))

    def test_parser_and_cli_select_twenty_without_changing_old_defaults(self):
        program = load_texture_file_manifest(FIXTURES / "empty-both.files.json")
        ast = parse_source_unit(program.entry)
        self.assertEqual(ast.version, "0.20")
        self.assertEqual(ast.profile, PROFILE)
        request_file = Path(self.directory.name) / "request.json"
        request_file.write_text(json.dumps(self.request()), encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = cli_main(["agent", "--protocol", PROTOCOL, "--store",
                str(Path(self.directory.name) / "cli"), "--request", str(request_file)])
        self.assertEqual(code, 0, stream.getvalue())
        self.assertEqual(json.loads(stream.getvalue())["schema_version"], PROTOCOL)
        with patch("ontokin.agent_cli.run", return_value=0) as run:
            self.assertEqual(cli_main(["agent", "--store", self.directory.name]), 0)
        self.assertEqual(run.call_args.args[0].protocol, "ontokin.agent/0.1")
        with patch("ontokin.cli._program_export", return_value=0) as export:
            self.assertEqual(cli_main(["export", "--bundle", "unread.files.json",
                "--output", "unwritten.glb"]), 0)
        self.assertEqual(export.call_args.args[0].target, "ontokin.glb/0.1")
        with patch("ontokin.cli._program_export", return_value=0) as export:
            self.assertEqual(cli_main(["export", "--bundle", "unread.files.json", "--target", TARGET,
                "--output", "unwritten.glb"]), 0)
        self.assertEqual(export.call_args.args[0].target, TARGET)


if __name__ == "__main__":
    unittest.main()
