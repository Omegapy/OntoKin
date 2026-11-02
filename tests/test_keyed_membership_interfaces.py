"""Explicit .21 interfaces, frozen source answers and inherited closed lineage.

These focused binding checks supplement the separately authored C088 acceptance
packet. The frozen packet supplies source bytes, revisions and Boolean answers;
no expected answer is obtained from a candidate execution.
"""
from __future__ import annotations

import copy
import hashlib
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
from ontokin.keyed_membership_agent import KeyedMembershipAgentService
from ontokin.keyed_membership_protocol import KeyedMembershipProtocol
from ontokin.program_agent import ProgramAgentService
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.string_concat_agent import StringConcatAgentService
from ontokin.string_concat_protocol import StringConcatProtocol
from ontokin.syntax02 import parse_source_unit
from ontokin.texture_bundle import load_texture_file_manifest


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "docs/language-design/keyed-membership-v0.1/freeze"
PROFILE, PROTOCOL, TARGET = "keyed-membership-0.1", "ontokin.agent/0.21", "ontokin.glb/0.21"
CHECKPOINTS = ["keyed_membership_admission", "keyed_membership_input",
               "keyed_membership_query", "keyed_membership_scan",
               "keyed_membership_publication"]
CONCAT_CHECKPOINTS = ["string_concat_admission", "string_concat_scan",
                      "string_concat_allocation", "string_concat_publication"]


def frozen_case(name):
    document = json.loads((FROZEN / "source-expected.json").read_bytes())
    return next(case for case in document["cases"] if case["id"] == name)


class KeyedMembershipInterfaceTests(unittest.TestCase):
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
        for name in ("request", "response", "diagnostic"):
            schema = json.loads((ROOT / f"docs/language-design/agent-v0.21/{name}.schema.json").read_bytes())
            Draft202012Validator.check_schema(schema)
            cls.validators[name] = Draft202012Validator(schema, registry=registry)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c088-interface-")
        self.service = KeyedMembershipAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation="discover", **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "membership-interface",
                "request_id": f"request-{self.serial}", "operation": operation,
                **({"profile": PROFILE, "limit": 1000} if operation == "discover" else {}),
                **fields}

    def send(self, operation="discover", **fields):
        request = self.request(operation, **fields)
        self.validators["request"].validate(request)
        KeyedMembershipProtocol.validate_request(request)
        response = self.service.handle(request)
        self.validators["response"].validate(response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        return response

    def success(self, operation="discover", **fields):
        response = self.send(operation, **fields)
        self.assertEqual(response["status"], "succeeded", response)
        return response

    def frozen_program(self, name):
        case = frozen_case(name)
        program = load_texture_file_manifest(FROZEN / case["files"])
        self.assertEqual(hashlib.sha256(program.entry.raw).hexdigest(), case["source_sha256"])
        self.assertEqual(program.program_revision, case["program_revision"])
        return case, program

    def test_discovery_advertises_membership_and_inherited_string_authority(self):
        result = self.success()["result"]
        interface = result["keyed_membership_interface"]
        self.assertEqual(interface["operations"], sorted(KeyedMembershipProtocol.OPERATIONS))
        self.assertEqual(KeyedMembershipProtocol.OPERATIONS, StringConcatProtocol.OPERATIONS)
        self.assertEqual(len(interface["operations"]), 12)
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["host_ceilings"], self.service.host_policy.ceilings)
        self.assertEqual(interface["delivery_contract"], TARGET)
        self.assertEqual(interface["source_schema"], "ontokin.bundle/0.2")
        self.assertEqual(interface["file_transport_schema"], "ontokin.files/0.2")
        membership = interface["source_expressions"]["has_key"]
        self.assertEqual(membership["signature"], "has_key(Keyed<T>, String) -> Bool")
        self.assertEqual(membership["declaring_version"], "0.21")
        self.assertEqual(membership["declaring_profile"], PROFILE)
        self.assertEqual(membership["stable_key_pattern"], "[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
        self.assertEqual(membership["max_entries"], 256)
        self.assertEqual(membership["max_key_characters"], 64)
        self.assertEqual(membership["empty_operations"], 3)
        self.assertEqual(membership["first_of_256_operations"], 260)
        self.assertEqual(membership["maximum_operations"], 515)
        self.assertEqual(membership["cancellation_stages"], CHECKPOINTS)
        self.assertEqual(membership["stage_operations"], dict(zip(CHECKPOINTS, (1, "n", 1, "k", 1))))
        concat = interface["source_expressions"]["string_concat"]
        self.assertEqual(concat["declaring_versions"], ["0.20", "0.21"])
        self.assertEqual(concat["declaring_profiles"], ["string-concat-0.1", PROFILE])
        self.assertEqual(concat["diagnostic_profile"], "string-concat-0.1")
        self.assertEqual(concat["max_result_utf8_bytes"], 65536)
        self.assertEqual(concat["max_total_utf8_bytes"], 4194304)
        self.assertEqual(concat["cancellation_stages"], CONCAT_CHECKPOINTS)
        self.assertTrue(interface["source_expressions"]["rekey_keyed"]["string_concatenation"])
        self.assertEqual(next(item for item in result["items"] if item["name"] == "has_key")["kind"], "builtin")
        for item in result["items"]:
            if item["kind"] == "protocol":
                self.assertEqual(item["name"], PROTOCOL)
            elif item["kind"] == "destination":
                self.assertEqual(item["name"], TARGET)

    def test_discovery_is_detached_and_recomputes_current_host_policy(self):
        first = self.success()["result"]
        old_revision = first["revision"]
        interface = first["keyed_membership_interface"]
        interface["source_expressions"]["has_key"]["cancellation_stages"].clear()
        interface["source_expressions"]["string_concat"]["cancellation_stages"].clear()
        interface["rekey_provenance"]["writable"] = True
        self.service.host_policy = HostPolicy(200000, 80000)
        fresh = self.success()["result"]
        current = fresh["keyed_membership_interface"]
        self.assertEqual(current["host_ceilings"], self.service.host_policy.ceilings)
        self.assertNotEqual(fresh["revision"], old_revision)
        self.assertEqual(current["source_expressions"]["has_key"]["cancellation_stages"], CHECKPOINTS)
        self.assertEqual(current["source_expressions"]["string_concat"]["cancellation_stages"], CONCAT_CHECKPOINTS)
        self.assertFalse(current["rekey_provenance"]["writable"])
        with StringConcatAgentService(self.directory.name) as predecessor:
            response = predecessor.handle({**self.request(), "schema_version": "ontokin.agent/0.20",
                                           "profile": "string-concat-0.1"})
            self.assertEqual(response["status"], "succeeded", response)
            self.assertNotIn("keyed_membership_interface", response["result"])
            old = response["result"]["string_concat_interface"]
            self.assertNotIn("has_key", old["source_expressions"])
            self.assertEqual(old["source_expressions"]["string_concat"]["declaring_version"], "0.20")
            self.assertNotIn("declaring_versions", old["source_expressions"]["string_concat"])
            self.assertEqual(current["source_expressions"]["rekey_keyed"], old["source_expressions"]["rekey_keyed"])
            self.assertNotEqual(predecessor.database_path, self.service.database_path)

    def test_store_reopens_its_own_contract_and_preserves_old_defaults(self):
        expected_revision = self.success()["result"]["revision"]
        self.assertEqual(self.service.database_path.name, "keyed-membership-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.keyed-membership-program-agent-store/0.1")
        self.service.close()
        self.service = KeyedMembershipAgentService(self.directory.name)
        self.assertEqual(self.success()["result"]["revision"], expected_revision)
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)
        with ProgramAgentService(Path(self.directory.name) / "program-default") as default:
            self.assertEqual(default._protocol.SCHEMA_VERSION, "ontokin.agent/0.2")
        with AgentService(Path(self.directory.name) / "core-default") as default:
            response = default.handle(self.request())
            self.assertEqual(response["schema_version"], "ontokin.agent/0.1")
            self.assertEqual(response["status"], "rejected")

    def test_request_shapes_refuse_cross_contract_and_invented_membership_fields(self):
        good = self.request()
        KeyedMembershipProtocol.validate_request(good)
        self.validators["request"].validate(good)
        with self.assertRaises(ProtocolError):
            StringConcatProtocol.validate_request(good)
        inspect = self.request("inspect", program_revision="sha256:" + "0" * 64,
                               selector={"kind": "source"}, fields=["source"], limit=1)
        KeyedMembershipProtocol.validate_request(inspect)
        self.validators["request"].validate(inspect)
        invalid = [
            {**good, "schema_version": "ontokin.agent/0.20"},
            {**good, "membership_query": "alpha"},
            {**inspect, "source_slice": {"offset": 0, "max_bytes": 128}},
        ]
        for request in invalid:
            with self.subTest(request=request):
                self.assertTrue(list(self.validators["request"].iter_errors(request)))
                with self.assertRaises(ProtocolError):
                    KeyedMembershipProtocol.validate_request(request)

    def test_schemas_preserve_all_inherited_operation_and_provenance_shapes(self):
        replacements = {"ontokin.agent/0.20": PROTOCOL, "ontokin.glb/0.20": TARGET,
                        "string-concat-0.1": PROFILE}

        def binding_scalars(value):
            if isinstance(value, dict):
                return {key: binding_scalars(child) for key, child in value.items()}
            if isinstance(value, list):
                return [binding_scalars(child) for child in value]
            return replacements.get(value, value) if isinstance(value, str) else value

        for name in ("request", "response", "diagnostic"):
            with self.subTest(schema=name):
                old = json.loads((ROOT / f"docs/language-design/agent-v0.20/{name}.schema.json").read_bytes())
                expected = binding_scalars(old)
                expected["$id"] = old["$id"].replace("0.20", "0.21")
                expected["title"] = f"OntoKin Keyed membership Agent/0.21 {name}"
                if name == "response":
                    expected["description"] = old["description"].replace("Agent/0.20", "Agent/0.21")
                self.assertEqual(self.validators[name].schema, expected)
        self.assertFalse(any("membership" in name for name in self.validators["response"].schema["$defs"]))

    def test_true_and_false_inspection_keep_exact_closed_detached_filter_records(self):
        for name in ("composition-filter-keep", "composition-filter-drop"):
            with self.subTest(case=name):
                case, program = self.frozen_program(name)
                self.success("create", project_id=name, bundle=program.to_payload(),
                             expected_program_revision=None, requested_level="constructed")
                fields = {"project_id": name, "program_revision": program.program_revision,
                          "selector": {"path": "probe"}, "fields": ["values", "support"], "limit": 1}
                response = self.success("inspect", **fields)
                item = response["result"]["items"][0]
                self.assertEqual(item["support"]["named_destination"], TARGET)
                value = item["values"]["observed"]
                self.assertEqual(value["type"], "Bool")
                self.assertIs(value["value"], case["expected"]["observed"])

                def location(raw):
                    start = program.entry.raw.index(raw)
                    return {"source_id": "entry", "source_revision": "sha256:" + case["source_sha256"],
                            "filename": "main.ok", "start_byte": start, "end_byte": start + len(raw)}

                expected = {"expression": location(b'filter_keyed<Length>(keyed<Length>{"a":1[m],"b":2[m]},(k,v)->v>1[m])'),
                            "input": location(b'keyed<Length>{"a":1[m],"b":2[m]}'),
                            "predicate": location(b"v>1[m]"), "element_type": "Length"}
                self.assertEqual(value["derived_filters"], [expected])
                self.assertEqual({key for key in value if key.startswith("derived_")}, {"derived_filters"})
                original_value = copy.deepcopy(value)
                for mutation in ({"key": "b"}, {"membership_query": "a"}, {"writable": True}):
                    broken = copy.deepcopy(response)
                    broken["result"]["items"][0]["values"]["observed"]["derived_filters"][0].update(mutation)
                    self.assertTrue(list(self.validators["response"].iter_errors(broken)))
                value["derived_filters"].clear()
                fresh = self.success("inspect", **fields)
                self.assertEqual(fresh["result"]["items"][0]["values"]["observed"], original_value)
                self.service.close()
                self.service = KeyedMembershipAgentService(self.directory.name)
                reopened = self.success("inspect", **fields)
                self.assertEqual(reopened["result"]["items"][0]["values"]["observed"], original_value)

    def test_inherited_rekey_schema_retains_closed_old_to_new_constraints(self):
        from jsonschema import Draft202012Validator
        schema = self.validators["response"].schema
        validator = Draft202012Validator({"$schema": schema["$schema"], "$defs": schema["$defs"],
                                          "$ref": "#/$defs/derived_rekey"})
        expected = json.loads((ROOT / "examples/keyed-rekey/expected.json").read_bytes())
        singleton = next(case for case in expected["cases"] if case["name"] == "singleton")["expected"]
        aggregate = singleton["root_aggregate_rekey_record"]
        selected = singleton["root_selected_rekey_records"]["ns.a"]
        validator.validate(aggregate)
        validator.validate(selected)
        for mutation in ({**aggregate, "old_key": "a"}, {**selected, "new_key": None},
                         {**selected, "editable_key": "a"}):
            self.assertTrue(list(validator.iter_errors(mutation)))
        broken = copy.deepcopy(selected)
        broken["input_entry"]["writable"] = True
        self.assertTrue(list(validator.iter_errors(broken)))

    def test_explicit_parser_and_cli_do_not_replace_earlier_defaults(self):
        case, program = self.frozen_program("empty")
        ast = parse_source_unit(program.entry)
        self.assertEqual((ast.version, ast.profile), ("0.21", PROFILE))
        old = load_texture_file_manifest(FROZEN / case["controls"]["literal"])
        old_ast = parse_source_unit(old.entry)
        self.assertEqual((old_ast.version, old_ast.profile), ("0.20", "string-concat-0.1"))
        request_file = Path(self.directory.name) / "request.json"
        request_file.write_text(json.dumps(self.request()), encoding="utf-8")
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = cli_main(["agent", "--protocol", PROTOCOL, "--store",
                             str(Path(self.directory.name) / "cli"), "--request", str(request_file)])
        self.assertEqual(code, 0, stream.getvalue())
        response = json.loads(stream.getvalue())
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.validators["response"].validate(response)
        with patch("ontokin.agent_cli.run", return_value=0) as run:
            self.assertEqual(cli_main(["agent", "--store", self.directory.name]), 0)
        self.assertEqual(run.call_args.args[0].protocol, "ontokin.agent/0.1")
        with patch("ontokin.cli._program_export", return_value=0) as export:
            self.assertEqual(cli_main(["export", "--bundle", "unread.files.json",
                                       "--output", "unwritten.glb"]), 0)
        self.assertEqual(export.call_args.args[0].target, "ontokin.glb/0.1")

    def test_small_actual_cli_export_has_explicit_identity_and_closed_reader(self):
        from ontokin import texture_gltf
        from ontokin.budget_runtime import execute_keyed_membership_export
        from ontokin.diagnostics import OntoKinError
        case, program = self.frozen_program("empty")
        with self.assertRaises(TypeError):
            execute_keyed_membership_export(program, profile="string-concat-0.1")
        output = Path(self.directory.name) / "membership.glb"
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = cli_main(["export", "--bundle", str(FROZEN / case["files"]),
                             "--target", TARGET, "--output", str(output), "--fps", "1", "--end", "1"])
        self.assertEqual(code, 0, stream.getvalue())
        data = output.read_bytes()
        self.assertEqual(data[:4], b"glTF")
        json_length, chunk_type = struct.unpack_from("<I4s", data, 12)
        self.assertEqual(chunk_type, b"JSON")
        document = json.loads(data[20:20 + json_length])
        metadata = document["extras"]["ontokin"]
        self.assertEqual(metadata["target_contract"], TARGET)
        self.assertEqual(metadata["schema_version"], "0.21")
        self.assertEqual(metadata["profile"], PROFILE)
        self.assertEqual(metadata["source"]["entry_revision"], "sha256:" + case["source_sha256"])
        token = texture_gltf._ACTIVE_TARGET.set(TARGET)
        try:
            texture_gltf.validate_texture_shapes(document)
            broken = copy.deepcopy(document)
            broken["asset"]["extras"] = {"invented": True}
            with self.assertRaises(OntoKinError):
                texture_gltf.validate_texture_shapes(broken)
            broken = copy.deepcopy(document)
            broken["extras"]["ontokin"]["membership_authority"] = True
            with self.assertRaises(OntoKinError):
                texture_gltf.validate_texture_shapes(broken)
        finally:
            texture_gltf._ACTIVE_TARGET.reset(token)


if __name__ == "__main__":
    unittest.main()
