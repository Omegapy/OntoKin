"""Explicit .17 interface, authority and detached source-provenance boundaries."""
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
from ontokin.keyed_filter_protocol import KeyedFilterProtocol
from ontokin.keyed_merge_agent import KeyedMergeAgentService
from ontokin.keyed_merge_protocol import KeyedMergeProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.texture_bundle import load_texture_file_manifest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-merge"
PROFILE, PROTOCOL, TARGET = "keyed-merge-0.1", "ontokin.agent/0.17", "ontokin.glb/0.17"


class KeyedMergeInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c084-interface-")
        self.service = KeyedMergeAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "merge-interface",
            "request_id": f"request-{self.serial}", "operation": operation, **fields}

    def success(self, operation, **fields):
        response = self.service.handle(self.request(operation, **fields))
        self.assertEqual(response["status"], "succeeded", response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        return response

    def test_explicit_binding_discovery_and_older_defaults(self):
        result = self.success("discover", profile=PROFILE, limit=1000)["result"]
        interface = result["keyed_merge_interface"]
        self.assertEqual(interface["operations"], sorted(KeyedMergeProtocol.OPERATIONS))
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        self.assertFalse(interface["merge_provenance"]["writable"])
        for name in ("map_keyed", "reduce_keyed", "filter_keyed", "merge_keyed"):
            self.assertEqual(next(i for i in result["items"] if i["name"] == name)["kind"], "builtin")
        self.assertEqual(interface["source_expressions"]["merge_keyed"]["cancellation_stages"],
                         ["keyed_merge_collision", "keyed_merge_iteration"])
        self.assertEqual(self.service.database_path.name, "keyed-merge-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.keyed-merge-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(ProtocolError):
            KeyedFilterProtocol.validate_request(self.request("discover", profile=PROFILE, limit=1))
        with AgentService(Path(self.directory.name) / "default") as default:
            response = default.handle(self.request("discover", profile=PROFILE, limit=1))
            self.assertEqual(response["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(response["status"], "rejected")

    def test_discovery_is_detached_and_reads_current_host_authority(self):
        first = self.success("discover", profile=PROFILE, limit=1000)["result"]
        first["keyed_merge_interface"]["source_expressions"]["merge_keyed"]["leaf_families"].clear()
        first["keyed_merge_interface"]["merge_provenance"]["input_sides"].append("invented")
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success("discover", profile=PROFILE, limit=1000)["result"]["keyed_merge_interface"]
        self.assertEqual(fresh["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(len(fresh["source_expressions"]["merge_keyed"]["leaf_families"]), 24)
        self.assertEqual(fresh["merge_provenance"]["input_sides"], ["both", "left", "right"])

    def test_closed_schema_and_detached_merge_provenance(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        resources = {}
        for path in (ROOT / "docs/language-design").rglob("*.schema.json"):
            value = json.loads(path.read_bytes())
            if "$id" in value:
                resources[value["$id"]] = Resource.from_contents(value)
        schema = json.loads((ROOT / "docs/language-design/agent-v0.17/response.schema.json").read_bytes())
        validator = Draft202012Validator(schema, registry=Registry().with_resources(resources.items()))
        program = load_texture_file_manifest(FIXTURES / "panel-task-repaired.files.json")
        self.success("create", bundle=program.to_payload(), expected_program_revision=None, requested_level="constructed")
        fields = dict(program_revision=program.program_revision, selector={"path": "first"}, fields=["values"], limit=1)
        response = self.success("inspect", **fields)
        validator.validate(response)
        record = response["result"]["items"][0]["values"]["widths"]["derived_merges"][-1]
        self.assertEqual(set(record), {"expression", "left", "right", "element_type", "input_side"})
        self.assertEqual(record["input_side"], "both")
        for location in ("expression", "left", "right"):
            self.assertEqual(set(record[location]), {"source_id", "source_revision", "filename", "start_byte", "end_byte"})
        original = copy.deepcopy(response)
        record["input_side"] = "invented"
        self.assertTrue(list(validator.iter_errors(response)))
        record.clear()
        self.assertEqual(self.success("inspect", **fields)["result"], original["result"])
        invented = copy.deepcopy(original)
        invented["result"]["items"][0]["values"]["widths"]["derived_merges"][-1]["editable_key"] = "invented"
        self.assertTrue(list(validator.iter_errors(invented)))

    def test_cli_selects_explicit_protocol_and_target_without_default_migration(self):
        request = self.request("discover", profile=PROFILE, limit=1000)
        request_file = Path(self.directory.name) / "request.json"
        request_file.write_text(json.dumps(request))
        stream = io.StringIO()
        with redirect_stdout(stream):
            status = cli_main(["agent", "--protocol", PROTOCOL, "--store", str(Path(self.directory.name) / "cli"),
                               "--request", str(request_file)])
        self.assertEqual(status, 0, stream.getvalue())
        self.assertEqual(json.loads(stream.getvalue())["schema_version"], PROTOCOL)
        output = Path(self.directory.name) / "model.glb"
        stream = io.StringIO()
        with redirect_stdout(stream):
            status = cli_main(["export", "--bundle", str(FIXTURES / "panel-identity.files.json"),
                "--target", TARGET, "--output", str(output), "--fps", "4", "--end", "1"])
        self.assertEqual(status, 0, stream.getvalue())
        self.assertTrue(output.read_bytes().startswith(b"glTF"))


if __name__ == "__main__":
    unittest.main()
