"""Explicit .19 interfaces, closed lineage and unchanged earlier bindings."""
from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.cli import main as cli_main
from ontokin.execution_budget import HostPolicy
from ontokin.keyed_rekey_agent import KeyedRekeyAgentService
from ontokin.keyed_rekey_protocol import KeyedRekeyProtocol
from ontokin.keyed_zip_agent import KeyedZipAgentService
from ontokin.keyed_zip_protocol import KeyedZipProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.texture_bundle import load_texture_file_manifest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-rekey"
AGENT_FIXTURES = FIXTURES / "agent"
PROFILE, PROTOCOL, TARGET = "keyed-rekey-0.1", "ontokin.agent/0.19", "ontokin.glb/0.19"
CHECKPOINTS = ["keyed_rekey_iteration", "keyed_rekey_key_validation",
               "keyed_rekey_collision", "keyed_rekey_publication"]
RECORD_FIELDS = {"expression", "input", "body", "element_type", "old_key", "new_key", "input_entry"}
LOCATION_FIELDS = {"source_id", "source_revision", "filename", "start_byte", "end_byte"}


def frozen_case(name):
    data = json.loads((FIXTURES / "expected.json").read_bytes())
    return next(case for case in data["cases"] if case["name"] == name)


def response_validator():
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    resources = {}
    for path in (ROOT / "docs/language-design").rglob("*.schema.json"):
        value = json.loads(path.read_bytes())
        if "$id" in value:
            resources[value["$id"]] = Resource.from_contents(value)
    schema = json.loads((ROOT / "docs/language-design/agent-v0.19/response.schema.json").read_bytes())
    return Draft202012Validator(schema, registry=Registry().with_resources(resources.items()))


class KeyedRekeyInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c086-interface-")
        self.service = KeyedRekeyAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "rekey-interface",
            "request_id": f"request-{self.serial}", "operation": operation, **fields}

    def success(self, operation, **fields):
        response = self.service.handle(self.request(operation, **fields))
        self.assertEqual(response["status"], "succeeded", response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        return response

    def create(self, manifest):
        program = load_texture_file_manifest(manifest)
        self.success("create", bundle=program.to_payload(), expected_program_revision=None,
                     requested_level="constructed")
        return program

    def inspect_result(self, program):
        response = self.success("inspect", program_revision=program.program_revision,
            selector={"path": "shape"}, fields=["values"], limit=1)
        return response, response["result"]["items"][0]["values"]["result"]

    def test_explicit_discovery_preserves_predecessor_and_defaults(self):
        result = self.success("discover", profile=PROFILE, limit=1000)["result"]
        interface = result["keyed_rekey_interface"]
        self.assertEqual(interface["operations"], sorted(KeyedRekeyProtocol.OPERATIONS))
        self.assertEqual(KeyedRekeyProtocol.OPERATIONS, KeyedZipProtocol.OPERATIONS)
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        self.assertFalse(interface["rekey_provenance"]["writable"])
        self.assertEqual(set(interface["rekey_provenance"]["fields"]), RECORD_FIELDS)
        operation = interface["source_expressions"]["rekey_keyed"]
        self.assertEqual(operation["cancellation_stages"], CHECKPOINTS)
        self.assertEqual(operation["max_entries"], 256)
        self.assertEqual(operation["key_domain"], {"pattern": "[A-Za-z0-9][A-Za-z0-9._-]{0,63}",
            "full_match": True, "min_ascii_characters": 1, "max_ascii_characters": 64,
            "case_sensitive": True, "normalization": False})
        self.assertFalse(operation["string_concatenation"])
        for name in ("map_keyed", "reduce_keyed", "filter_keyed", "merge_keyed", "zip_keyed", "rekey_keyed"):
            self.assertEqual(next(item for item in result["items"] if item["name"] == name)["kind"], "builtin")
        self.assertEqual(self.service.database_path.name, "keyed-rekey-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.keyed-rekey-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with self.assertRaises(ProtocolError):
            KeyedZipProtocol.validate_request(self.request("discover", profile=PROFILE, limit=1))
        with AgentService(Path(self.directory.name) / "default") as default:
            response = default.handle(self.request("discover", profile=PROFILE, limit=1))
            self.assertEqual(response["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(response["status"], "rejected")
        with KeyedZipAgentService(Path(self.directory.name) / "predecessor") as predecessor:
            response = predecessor.handle({"schema_version": "ontokin.agent/0.18", "project_id": "old",
                "request_id": "discover", "operation": "discover", "profile": "keyed-zip-0.1", "limit": 1000})
            self.assertEqual(response["status"], "succeeded", response)
            self.assertNotIn("keyed_rekey_interface", response["result"])
            self.assertNotIn("rekey_keyed", response["result"]["keyed_zip_interface"]["source_expressions"])
            self.assertEqual(interface["source_expressions"]["zip_keyed"],
                             response["result"]["keyed_zip_interface"]["source_expressions"]["zip_keyed"])

    def test_discovery_is_detached_and_reads_current_host_authority(self):
        first = self.success("discover", profile=PROFILE, limit=1000)["result"]
        first["keyed_rekey_interface"]["source_expressions"]["rekey_keyed"]["leaf_families"].clear()
        first["keyed_rekey_interface"]["rekey_provenance"]["aggregate"]["new_key"] = "invented"
        first["keyed_rekey_interface"]["source_expressions"]["zip_keyed"]["cancellation_stages"].clear()
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success("discover", profile=PROFILE, limit=1000)["result"]["keyed_rekey_interface"]
        self.assertEqual(fresh["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(len(fresh["source_expressions"]["rekey_keyed"]["leaf_families"]), 24)
        self.assertEqual(fresh["rekey_provenance"]["aggregate"],
                         {"old_key": None, "new_key": None, "input_entry": None})
        self.assertEqual(fresh["source_expressions"]["zip_keyed"]["cancellation_stages"],
                         ["keyed_zip_keyset", "keyed_zip_iteration"])

    def test_source_reads_keep_the_existing_request_shape(self):
        request = self.request("inspect", program_revision="sha256:" + "0" * 64,
            selector={"kind": "source"}, fields=["source"], limit=1)
        KeyedRekeyProtocol.validate_request(request)
        request["source_slice"] = {"offset": 0, "max_bytes": 128}
        with self.assertRaises(ProtocolError):
            KeyedRekeyProtocol.validate_request(request)

    def test_frozen_singleton_lineage_is_exact_and_detached(self):
        program = self.create(FIXTURES / "singleton.files.json")
        response, value = self.inspect_result(program)
        expected = frozen_case("singleton")["expected"]
        validator = response_validator()
        validator.validate(response)
        aggregate = value["derived_rekeys"]
        selected = value["value"][0]["value"]["derived_rekeys"]
        self.assertEqual(aggregate, [expected["root_aggregate_rekey_record"]])
        self.assertEqual(selected, [expected["root_aggregate_rekey_record"],
                                   expected["root_selected_rekey_records"]["ns.a"]])
        self.assertEqual(value["value"][0]["key"], "ns.a")
        self.assertEqual(value["value"][0]["value"]["value"], 7)
        for record in selected:
            self.assertEqual(set(record), RECORD_FIELDS)
            for field in ("expression", "input", "body"):
                self.assertEqual(set(record[field]), LOCATION_FIELDS)
        original = copy.deepcopy(response)
        aggregate[0]["input_entry"] = selected[-1]["input_entry"]
        self.assertTrue(list(validator.iter_errors(response)))
        aggregate.clear()
        fresh, unused = self.inspect_result(program)
        self.assertEqual(fresh["result"], original["result"])
        invented = copy.deepcopy(original)
        invented["result"]["items"][0]["values"]["result"]["derived_rekeys"][0]["editable_key"] = "invented"
        self.assertTrue(list(validator.iter_errors(invented)))

    def test_nested_projection_keeps_both_frozen_old_to_new_steps(self):
        program = self.create(FIXTURES / "nested-rekey.files.json")
        response, value = self.inspect_result(program)
        expected = frozen_case("nested-rekey")["expected"]
        response_validator().validate(response)
        self.assertEqual(value["derived_rekeys"], expected["exact_aggregate_rekey_records"])
        self.assertEqual(value["value"][0]["key"], "c")
        selected = value["value"][0]["value"]["derived_rekeys"]
        self.assertEqual(selected, expected["exact_public_selected_rekey_records"]["c"])
        self.assertEqual([(row["old_key"], row["new_key"]) for row in selected],
                         [(None, None), (None, None), ("a", "b"), ("b", "c")])

    def test_rekey_keeps_inherited_zip_contributor_keys(self):
        program = self.create(FIXTURES / "zip-prepares-input.files.json")
        response, value = self.inspect_result(program)
        response_validator().validate(response)
        selected = value["value"][0]["value"]
        self.assertEqual(value["value"][0]["key"], "ns.a")
        self.assertEqual(selected["value"], 5)
        self.assertEqual([row["key"] for row in value["derived_zips"]], [None])
        self.assertEqual([row["key"] for row in selected["derived_zips"]], [None, "a"])
        expected = frozen_case("zip-prepares-input")["expected"]
        self.assertEqual(selected["derived_rekeys"][-1], expected["root_selected_rekey_records"]["ns.a"])

    def test_generated_source_uses_new_identity_and_original_payload_entry(self):
        program = self.create(AGENT_FIXTURES / "panel-task-repaired.files.json")
        response = self.success("inspect", program_revision=program.program_revision,
            selector={"path": 'first.panels["front.left"]'}, fields=["identity", "source"], limit=1)
        response_validator().validate(response)
        item = response["result"]["items"][0]
        self.assertEqual(item["element_id"], ["panel-task", "demo", "first", "panels", "front.left"])
        generated = item["source"]["generated"]
        current = generated["input_rekeys"][-1]
        self.assertEqual((current["old_key"], current["new_key"]), ("left", "front.left"))
        loc = current["input_entry"]
        # The inherited generated span uses file; rekey lineage uses filename.
        self.assertEqual(generated["input_entry_span"], {
            "source_id": loc["source_id"], "source_revision": loc["source_revision"],
            "file": loc["filename"], "start_byte": loc["start_byte"], "end_byte": loc["end_byte"]})
        self.assertEqual(loc["source_id"], "package:fixture.rekey-catalog@1.0.0")
        catalog_source = next(unit for unit in program.units if unit.source_id == loc["source_id"])
        self.assertEqual(catalog_source.raw[loc["start_byte"]:loc["end_byte"]], b'"left":"left"')
        self.assertTrue(any(row["key"] == "left" for row in generated["input_zips"]))
        self.assertFalse(any(row["key"] == "front.left" for row in generated["input_zips"]))

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
            status = cli_main(["export", "--bundle", str(AGENT_FIXTURES / "panel-task-repaired.files.json"),
                "--target", TARGET, "--output", str(output), "--fps", "4", "--end", "1"])
        self.assertEqual(status, 0, stream.getvalue())
        data = output.read_bytes()
        self.assertTrue(data.startswith(b"glTF"))
        json_length, chunk_type = struct.unpack_from("<I4s", data, 12)
        self.assertEqual(chunk_type, b"JSON")
        document = json.loads(data[20:20 + json_length])
        self.assertEqual(document["extras"]["ontokin"]["target_contract"], TARGET)
        self.assertEqual(document["extras"]["ontokin"]["schema_version"], "0.19")
        # Exercise the inherited strict shape validator with actual .19 output.
        # Unknown extras must not become permitted on the new target.
        from ontokin import texture_gltf
        from ontokin.diagnostics import OntoKinError
        token = texture_gltf._ACTIVE_TARGET.set(TARGET)
        try:
            texture_gltf.validate_texture_shapes(document)
            document["asset"]["extras"] = {"invented": True}
            with self.assertRaises(OntoKinError):
                texture_gltf.validate_texture_shapes(document)
        finally:
            texture_gltf._ACTIVE_TARGET.reset(token)

    def test_surface_page_preserves_texture_uv_stream_and_new_identity(self):
        from ontokin import program_surface
        program = self.create(AGENT_FIXTURES / "panel-task-repaired.files.json")
        element_id = ["panel-task", "demo", "first", "panels", "front.left"]
        with patch.object(program_surface, "_mesh_digest", wraps=program_surface._mesh_digest) as digest:
            response = self.success("surface.mesh_page", program_revision=program.program_revision,
                                    element_id=element_id, count=256)
        page = response["result"]
        response_validator().validate(response)
        self.assertIsNone(response["next_cursor"])
        self.assertEqual(page["profile"], PROFILE)
        self.assertEqual(page["element_id"], element_id)
        self.assertEqual(page["texture_coordinate_system"], "raw_unplaced_recipe_local_affine")
        self.assertEqual(set(page["texture_bindings"]), {"top"})
        binding = page["texture_bindings"]["top"]
        self.assertEqual(binding["asset_id"], "label")
        self.assertEqual(binding["sha256"], program.assets[0].sha256)
        self.assertEqual(binding["source_id"], "package:fixture.rekey-panels@1.0.0")
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
                self.assertEqual(uv, [0.5 * position[0], 1 - 0.5 * position[1]])
                top_corners.add(tuple(uv))
            else:
                self.assertIsNone(uv)
        self.assertEqual(top_corners, {(0, 1), (0.5, 1), (0.5, 0), (0, 0)})
        digest.assert_called_once()
        self.assertEqual(set(digest.call_args.kwargs["texture_uvs"]), {"top"})
        geometry, mesh = digest.call_args.args
        without_uv_stream = program_surface._mesh_digest(geometry, mesh, check=lambda: None)
        self.assertNotEqual(page["geometry_sha256"], without_uv_stream)


class KeyedRekeySchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from jsonschema import Draft202012Validator
        cls.schema = json.loads((ROOT / "docs/language-design/agent-v0.19/response.schema.json").read_bytes())
        cls.record_validator = Draft202012Validator({"$schema": cls.schema["$schema"],
            "$defs": cls.schema["$defs"], "$ref": "#/$defs/derived_rekey"})

    def test_rekey_records_close_fields_locations_and_nullable_roles(self):
        expected = frozen_case("singleton")["expected"]
        aggregate = expected["root_aggregate_rekey_record"]
        selected = expected["root_selected_rekey_records"]["ns.a"]
        for valid in (aggregate, selected, {**selected, "input_entry": None}):
            self.record_validator.validate(valid)
        corruptions = [
            {**aggregate, "old_key": "a"}, {**aggregate, "new_key": "ns.a"},
            {**aggregate, "input_entry": selected["input_entry"]},
            {**selected, "old_key": None}, {**selected, "new_key": None},
            {**selected, "editable_key": "a"},
            {**selected, "input": {**selected["input"], "authority": "invented"}},
        ]
        for candidate in corruptions:
            with self.subTest(candidate=candidate):
                self.assertTrue(list(self.record_validator.iter_errors(candidate)))
        for name in RECORD_FIELDS:
            candidate = {key: value for key, value in selected.items() if key != name}
            with self.subTest(missing=name):
                self.assertTrue(list(self.record_validator.iter_errors(candidate)))

    def test_rekey_key_schema_rejects_trailing_characters_and_boundaries(self):
        selected = frozen_case("singleton")["expected"]["root_selected_rekey_records"]["ns.a"]
        for key in ("0", "a", "A._-9", "a" * 64):
            self.record_validator.validate({**selected, "old_key": key, "new_key": key})
        for key in ("", "_a", ".a", "-a", "a" * 65, "a/b", "a b", "é", "a\n", "a\r", "a\x00"):
            for field in ("old_key", "new_key"):
                with self.subTest(key=key, field=field):
                    self.assertTrue(list(self.record_validator.iter_errors({**selected, field: key})))

    def test_request_shapes_and_inherited_provenance_definitions_are_unchanged(self):
        old_dir = ROOT / "docs/language-design/agent-v0.18"
        new_dir = ROOT / "docs/language-design/agent-v0.19"
        previous = json.loads((old_dir / "request.schema.json").read_bytes())
        current = json.loads((new_dir / "request.schema.json").read_bytes())
        normalized = json.loads(json.dumps(current).replace("0.19", "0.18")
            .replace("keyed-rekey-0.1", "keyed-zip-0.1")
            .replace("keyed renaming Agent", "keyed pair Agent"))
        self.assertEqual(normalized, previous)
        previous = json.loads((old_dir / "response.schema.json").read_bytes())
        for name in ("stable_key", "transform_source_location", "derived_transform", "derived_transforms",
                     "derived_reduction", "derived_reductions", "derived_filter", "derived_filters",
                     "derived_merge", "derived_merges", "derived_zip", "derived_zips"):
            self.assertEqual(self.schema["$defs"][name], previous["$defs"][name], name)


if __name__ == "__main__":
    unittest.main()
