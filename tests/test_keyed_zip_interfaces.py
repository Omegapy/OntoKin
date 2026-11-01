"""Explicit .18 discovery, inspection and unchanged earlier interface boundaries."""
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
from ontokin.keyed_merge_agent import KeyedMergeAgentService
from ontokin.keyed_merge_protocol import KeyedMergeProtocol
from ontokin.keyed_zip_agent import KeyedZipAgentService
from ontokin.keyed_zip_protocol import KeyedZipProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.texture_bundle import load_texture_file_manifest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-zip"
PROFILE, PROTOCOL, TARGET = "keyed-zip-0.1", "ontokin.agent/0.18", "ontokin.glb/0.18"


class KeyedZipInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c085-interface-")
        self.service = KeyedZipAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "zip-interface",
            "request_id": f"request-{self.serial}", "operation": operation, **fields}

    def success(self, operation, **fields):
        response = self.service.handle(self.request(operation, **fields))
        self.assertEqual(response["status"], "succeeded", response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        return response

    def test_explicit_discovery_preserves_predecessor_and_defaults(self):
        result = self.success("discover", profile=PROFILE, limit=1000)["result"]
        interface = result["keyed_zip_interface"]
        self.assertEqual(interface["operations"], sorted(KeyedZipProtocol.OPERATIONS))
        self.assertEqual(KeyedZipProtocol.OPERATIONS, KeyedMergeProtocol.OPERATIONS)
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        self.assertFalse(interface["zip_provenance"]["writable"])
        for name in ("map_keyed", "reduce_keyed", "filter_keyed", "merge_keyed", "zip_keyed"):
            self.assertEqual(next(i for i in result["items"] if i["name"] == name)["kind"], "builtin")
        self.assertEqual(interface["source_expressions"]["zip_keyed"]["cancellation_stages"],
                         ["keyed_zip_keyset", "keyed_zip_iteration"])
        self.assertEqual(self.service.database_path.name, "keyed-zip-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.keyed-zip-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(ProtocolError):
            KeyedMergeProtocol.validate_request(self.request("discover", profile=PROFILE, limit=1))
        with AgentService(Path(self.directory.name) / "default") as default:
            response = default.handle(self.request("discover", profile=PROFILE, limit=1))
            self.assertEqual(response["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(response["status"], "rejected")
        with KeyedMergeAgentService(Path(self.directory.name) / "predecessor") as predecessor:
            response = predecessor.handle({"schema_version": "ontokin.agent/0.17", "project_id": "old",
                "request_id": "discover", "operation": "discover", "profile": "keyed-merge-0.1", "limit": 1000})
            self.assertEqual(response["status"], "succeeded", response)
            self.assertNotIn("keyed_zip_interface", response["result"])
            self.assertNotIn("zip_keyed", response["result"]["keyed_merge_interface"]["source_expressions"])

    def test_discovery_is_detached_and_uses_current_host_authority(self):
        first = self.success("discover", profile=PROFILE, limit=1000)["result"]
        first["keyed_zip_interface"]["source_expressions"]["zip_keyed"]["leaf_families"].clear()
        first["keyed_zip_interface"]["zip_provenance"]["aggregate"]["key"] = "invented"
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success("discover", profile=PROFILE, limit=1000)["result"]["keyed_zip_interface"]
        self.assertEqual(fresh["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(len(fresh["source_expressions"]["zip_keyed"]["leaf_families"]), 24)
        self.assertEqual(fresh["zip_provenance"]["aggregate"],
                         {"key": None, "left_entry": None, "right_entry": None})

    def test_source_reads_keep_existing_request_shape(self):
        request = self.request("inspect", program_revision="sha256:" + "0" * 64,
            selector={"kind": "source"}, fields=["source"], limit=1)
        KeyedZipProtocol.validate_request(request)
        request["source_slice"] = {"offset": 0, "max_bytes": 128}
        with self.assertRaises(ProtocolError):
            KeyedZipProtocol.validate_request(request)

    def test_closed_schema_and_detached_aggregate_and_pair_origins(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        resources = {}
        for path in (ROOT / "docs/language-design").rglob("*.schema.json"):
            value = json.loads(path.read_bytes())
            if "$id" in value:
                resources[value["$id"]] = Resource.from_contents(value)
        schema = json.loads((ROOT / "docs/language-design/agent-v0.18/response.schema.json").read_bytes())
        validator = Draft202012Validator(schema, registry=Registry().with_resources(resources.items()))
        program = load_texture_file_manifest(FIXTURES / "nested-generated-pairs.files.json")
        self.success("create", bundle=program.to_payload(), expected_program_revision=None, requested_level="constructed")
        fields = dict(program_revision=program.program_revision, selector={"path": "rig"}, fields=["values"], limit=1)
        response = self.success("inspect", **fields)
        validator.validate(response)
        result = response["result"]["items"][0]["values"]["result"]
        aggregate = result["derived_zips"]
        selected = result["value"][0]["value"]["derived_zips"]
        self.assertEqual([record["key"] for record in aggregate], [None, None])
        self.assertEqual([record["key"] for record in selected], [None, None, "a", "a"])
        self.assertEqual(selected[-1]["left_entry"], selected[-2]["left_entry"])
        self.assertNotEqual(selected[-1]["right_entry"], selected[-2]["right_entry"])
        generated = self.success("inspect", program_revision=program.program_revision,
            selector={"path": 'rig.leaves["a"]'}, fields=["identity", "source"], limit=1)
        validator.validate(generated)
        self.assertEqual(generated["result"]["items"][0]["source"]["generated"]["input_zips"], selected)
        for record in selected:
            self.assertEqual(set(record), {"expression", "left", "right", "body", "left_element_type",
                "right_element_type", "output_element_type", "key", "left_entry", "right_entry"})
            for location in ("expression", "left", "right", "body"):
                self.assertEqual(set(record[location]),
                    {"source_id", "source_revision", "filename", "start_byte", "end_byte"})
        original = copy.deepcopy(response)
        aggregate[0]["left_entry"] = selected[-1]["left_entry"]
        self.assertTrue(list(validator.iter_errors(response)))
        aggregate.clear()
        self.assertEqual(self.success("inspect", **fields)["result"], original["result"])
        invented = copy.deepcopy(original)
        invented["result"]["items"][0]["values"]["result"]["derived_zips"][0]["editable_key"] = "invented"
        self.assertTrue(list(validator.iter_errors(invented)))

    def test_cli_selects_explicit_protocol_and_target(self):
        request_file = Path(self.directory.name) / "request.json"
        request_file.write_text(json.dumps(self.request("discover", profile=PROFILE, limit=1000)))
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

    def test_surface_page_preserves_texture_uvs_and_fingerprint(self):
        from ontokin import program_surface

        program = load_texture_file_manifest(FIXTURES / "panel-task.files.json")
        self.success("create", bundle=program.to_payload(), expected_program_revision=None,
                     requested_level="constructed")
        element_id = ["panel-task", "demo", "first", "panels", "left"]
        with patch.object(program_surface, "_mesh_digest", wraps=program_surface._mesh_digest) as digest:
            response = self.success("surface.mesh_page", program_revision=program.program_revision,
                                    element_id=element_id, count=256)
        page = response["result"]
        self.assertIsNone(response["next_cursor"])
        self.assertEqual(page["profile"], PROFILE)
        self.assertEqual(page["element_id"], element_id)
        self.assertEqual(page["texture_coordinate_system"], "raw_unplaced_recipe_local_affine")
        self.assertEqual(set(page["texture_bindings"]), {"top"})
        binding = page["texture_bindings"]["top"]
        self.assertEqual(binding["asset_id"], "label")
        self.assertEqual(binding["sha256"], program.assets[0].sha256)
        self.assertEqual(binding["source_id"], "package:fixture.pair-panels@1.0.0")
        self.assertEqual(binding["origin_m"], [0, 0, 0])
        self.assertEqual(binding["u_per_m"], [0.5, 0, 0])
        self.assertEqual(binding["v_per_m"], [0, -0.5, 0])
        self.assertEqual(binding["offset"], [0, 1])
        self.assertEqual(page["returned_triangles"], 12)
        self.assertEqual(len(page["positions_m"]), 36)
        self.assertEqual(len(page["texcoords_0"]), 36)
        top_corners = set()
        for corner, (position, uv) in enumerate(zip(page["positions_m"], page["texcoords_0"])):
            if page["region_keys"][corner // 3] == "top":
                expected = [0.5 * position[0], 1 - 0.5 * position[1]]
                self.assertEqual(uv, expected)
                top_corners.add(tuple(uv))
            else:
                self.assertIsNone(uv)
        self.assertEqual(top_corners, {(0, 1), (0.5, 1), (0.5, 0), (0, 0)})
        # Guard the exact omitted .18 preparation path: actual computed UVs
        # must reach the fingerprint, including its explicit binary64 stream.
        digest.assert_called_once()
        self.assertEqual(set(digest.call_args.kwargs["texture_uvs"]), {"top"})
        geometry, mesh = digest.call_args.args
        without_uv_stream = program_surface._mesh_digest(geometry, mesh, check=lambda: None)
        self.assertNotEqual(page["geometry_sha256"], without_uv_stream)


if __name__ == "__main__":
    unittest.main()
