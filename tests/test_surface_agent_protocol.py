"""Explicit Agent/0.3 transport/profile boundaries and isolated durable stores."""

import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.bundle import ProgramBundle, SourceUnit, load_bundle
from ontokin.program_agent import ProgramAgentService
from ontokin import program_protocol
from tests.test_program_protocol import PAYLOAD as CONSTRUCTION_PAYLOAD
from tests.test_surface_export import single_source
from tests.test_surface_source import bundle as studio_bundle


PROTOCOL = "ontokin.agent/0.3"


class SurfaceAgentProtocolTests(unittest.TestCase):
    def setUp(self):
        self.program = studio_bundle()
        self.binding = program_protocol.bind(PROTOCOL)

    def request(self, operation="surface.mesh_page", **fields):
        request = {"schema_version": PROTOCOL, "project_id": "boundary", "request_id": "r",
                   "operation": operation}
        if operation == "surface.mesh_page":
            request.update(program_revision=self.program.program_revision,
                           element_id=["surface-studio", "studio", "first"], count=1)
        if operation == "create":
            request.update(bundle=self.program.to_payload(), expected_program_revision=None,
                           requested_level="represented")
        request.update(fields)
        return request

    def assert_code(self, response, code):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        codes = [diagnostic["code"] for diagnostic in response["diagnostics"]]
        if response["protocol_error"]:
            codes.append(response["protocol_error"]["code"])
        self.assertIn(code, codes, response)

    def test_binding_is_explicit_and_does_not_change_the_existing_default(self):
        self.assertEqual(self.binding.SCHEMA_VERSION, PROTOCOL)
        self.binding.validate_request(self.request())
        self.assertIn("surface.mesh_page", self.binding.OPERATIONS)
        previous = program_protocol.bind()
        self.assertEqual(previous.SCHEMA_VERSION, "ontokin.agent/0.2")
        self.assertEqual(program_protocol.SCHEMA_VERSION, "ontokin.agent/0.2")
        self.assertNotIn("surface.mesh_page", previous.OPERATIONS)
        self.assertNotIn("surface.mesh_page", program_protocol.OPERATIONS)
        for binding in (previous, program_protocol):
            with self.assertRaises(ProtocolError):
                binding.validate_request(self.request())
        for schema in ("ontokin.agent/0.1", "ontokin.agent/0.2", "ontokin.agent/0.4"):
            with self.subTest(schema=schema), self.assertRaises(ProtocolError):
                self.binding.validate_request(self.request(schema_version=schema))
        with self.assertRaises(ProtocolError):
            program_protocol.bind("ontokin.agent/0.5")

    def test_mesh_count_is_a_required_integer_token_in_triangle_units(self):
        for count in (1, 7, 256):
            self.binding.validate_request(self.request(count=count))
        for count in (0, -1, 257, 1.0, 256.0, True, False, None, "1", [], {}):
            with self.subTest(count=count), self.assertRaises(ProtocolError) as caught:
                self.binding.validate_request(self.request(count=count))
            self.assertEqual(caught.exception.code, "OKA-E-REQUEST")
        for name in ("program_revision", "element_id", "count"):
            missing = self.request()
            del missing[name]
            with self.subTest(missing=name), self.assertRaises(ProtocolError):
                self.binding.validate_request(missing)

    def test_mesh_operation_identity_survives_receipts_and_failure_envelopes(self):
        request = self.request()
        self.assertEqual(self.binding.envelope(request, "queued")["operation"], "surface.mesh_page")
        self.assertIsNone(self.binding.envelope({**request, "operation": "surface.future"}, "rejected")["operation"])
        with tempfile.TemporaryDirectory() as directory, ProgramAgentService(Path(directory), protocol=PROTOCOL) as service:
            create = service.handle(self.request("create", request_id="create"))
            self.assertEqual(create["status"], "succeeded", create)
            queued = service.submit(self.request(request_id="queued-page"))
            self.assertEqual(queued["status"], "queued")
            self.assertEqual(queued["operation"], "surface.mesh_page")
            cases = [({"count": 0}, "OKA-E-REQUEST"), ({"region": "absent"}, "OKL-E-SURFACE-REGION"),
                     ({"element_id": ["missing"]}, "OKL-E-REVISION")]
            for index, (fields, code) in enumerate(cases):
                with self.subTest(fields=fields):
                    response = service.handle(self.request(request_id=f"failed-{index}", **fields))
                    self.assert_code(response, code)
                    self.assertEqual(response["operation"], "surface.mesh_page")
                    self.assertEqual(response["schema_version"], PROTOCOL)
            unknown = service.handle(self.request(operation="surface.future", request_id="unknown"))
            self.assert_code(unknown, "OKA-E-REQUEST")
            self.assertIsNone(unknown["operation"])

    def test_mesh_selector_cursor_region_and_budget_fields_are_bounded(self):
        self.binding.validate_request(self.request(element_id=["segment"]*256, region="blue", cursor=None,
                                                   budgets={"max_result_items": 256}))
        invalid = [
            {"element_id": "first"}, {"element_id": []}, {"element_id": ["a"]*257},
            {"element_id": [True]}, {"element_id": [["a"]]}, {"element_id": [""]},
            {"region": ""}, {"region": "x"*65}, {"region": None}, {"region": 1},
            {"cursor": True}, {"cursor": "x"*65537},
            {"program_revision": "sha256:"+"G"*64}, {"program_revision": self.program.entry.revision.upper()},
            {"budgets": {"max_result_items": 1.0}}, {"budgets": {"max_operations": True}},
            {"budgets": {"max_value_entries": 0}}, {"budgets": {"invented": 1}},
            {"selector": {"path": "first"}}, {"run_id": None}, {"frame": "world"},
            {"time": {"seconds": "1", "side": "after"}}, {"limit": 1},
            {"source_revision": self.program.entry.revision}, {"expected_revision": None},
            {"destination": "ontokin.glb/0.3"}, {"vertex_offset": 0},
        ]
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises(ProtocolError):
                self.binding.validate_request(self.request(**fields))

    def test_named_surface_delivery_does_not_coerce_older_destinations(self):
        good = self.request("create", requested_level="delivered", destination="ontokin.glb/0.3",
                            options={"fps": 24, "helpers": False})
        self.binding.validate_request(good)
        for fields in ({"destination": "ontokin.glb/0.1"}, {"destination": "ontokin.glb/0.2"},
                       {"destination": "ontokin.glb/0.4"}, {"requested_level": "evaluated"},
                       {"options": {"fps": True}}, {"options": {"max_glb_bytes": 100}}):
            with self.subTest(fields=fields), self.assertRaises(ProtocolError):
                self.binding.validate_request({**good, **fields})
        without_destination = {name: value for name, value in good.items() if name != "destination"}
        with self.assertRaises(ProtocolError):
            self.binding.validate_request(without_destination)
        old = {**good, "schema_version": "ontokin.agent/0.2", "destination": "ontokin.glb/0.2",
               "bundle": copy.deepcopy(CONSTRUCTION_PAYLOAD)}
        program_protocol.validate_request(old)

    def test_malformed_bundle_transport_fails_before_any_candidate_snapshot(self):
        request = self.request("create")
        request["bundle"]["modules"].append(copy.deepcopy(request["bundle"]["modules"][0]))
        with tempfile.TemporaryDirectory() as directory, ProgramAgentService(Path(directory), protocol=PROTOCOL) as service:
            response = service.handle(request)
            self.assert_code(response, "OKA-E-REQUEST")
            self.assertEqual(response["schema_version"], PROTOCOL)
            self.assertIsNone(response["program_revision"])
            self.assertIsNone(service.accepted_revision("boundary"))
            with service._store.connection() as db:
                self.assertEqual(db.execute("SELECT count(*) FROM sources").fetchone()[0], 0)
        # Syntactically invalid source still has a valid complete transport hash.
        sealed = self.request("create")
        sealed["bundle"]["entry"]["source"] = "invalid native source café"
        self.binding.validate_request(sealed)
        self.assertNotEqual(load_bundle(sealed["bundle"]).program_revision, self.program.program_revision)

    def test_core_construction_and_surface_stores_remain_independent_in_one_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            with ProgramAgentService(path) as old, ProgramAgentService(path, protocol=PROTOCOL) as native, AgentService(path) as core:
                request = self.request("create")
                surface = native.handle(request)
                self.assertEqual(surface["status"], "succeeded", surface)
                self.assertIsNone(old.accepted_revision("boundary"))
                self.assertIsNone(core.accepted_revision("boundary"))
                old_request = {**request, "schema_version": "ontokin.agent/0.2", "bundle": copy.deepcopy(CONSTRUCTION_PAYLOAD)}
                construction = old.handle(old_request)
                self.assertEqual(construction["status"], "succeeded", construction)
                self.assertEqual(old.accepted_revision("boundary"), load_bundle(CONSTRUCTION_PAYLOAD).program_revision)
                self.assertEqual(native.accepted_revision("boundary"), self.program.program_revision)
                self.assertEqual(native.database_path.name, "surface-program-agent.sqlite3")
                self.assertEqual(old.database_path.name, "program-agent.sqlite3")
                self.assertEqual(core.database_path.name, "agent.sqlite3")
                self.assertEqual(native._store.schema_version, "ontokin.surface-program-agent-store/0.1")
                self.assertEqual(old._store.schema_version, "ontokin.program-agent-store/0.1")
                for service, wrong, schema in ((native, old_request, PROTOCOL), (old, request, "ontokin.agent/0.2")):
                    response = service.handle({**wrong, "request_id": "wrong-binding"})
                    self.assert_code(response, "OKA-E-REQUEST")
                    self.assertEqual(response["schema_version"], schema)
                self.assertEqual(native.handle(request), surface)
                self.assertEqual(old.handle(old_request), construction)

    def test_each_binding_rejects_the_other_entry_profile_without_accepting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            for schema, bundle, expected_profile in (("ontokin.agent/0.2", self.program.to_payload(), "construction-0.1"),
                                                       (PROTOCOL, copy.deepcopy(CONSTRUCTION_PAYLOAD), "surface-0.1")):
                with self.subTest(schema=schema), ProgramAgentService(Path(directory), protocol=schema) as service:
                    request = self.request("create", schema_version=schema, bundle=bundle)
                    response = service.handle(request)
                    self.assert_code(response, "OKL-E-CAPABILITY-UNSUPPORTED")
                    candidate = load_bundle(bundle)
                    self.assertEqual(response["program_revision"], candidate.program_revision)
                    self.assertIsNone(response["accepted_program_revision"])
                    self.assertIsNone(service.accepted_revision("boundary"))
                    diagnostic = next(item for item in response["diagnostics"] if item["code"] == "OKL-E-CAPABILITY-UNSUPPORTED")
                    self.assertEqual(diagnostic["details"]["required_profile"], expected_profile)
                    self.assertEqual(service.read_program("boundary", candidate.program_revision).to_payload(), bundle)

    def test_wrong_store_version_is_rejected_before_any_schema_or_journal_change(self):
        for version in ("ontokin.agent-store/0.1", "ontokin.program-agent-store/0.1",
                        "ontokin.surface-program-agent-store/0.2"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                database = path / "surface-program-agent.sqlite3"
                db = sqlite3.connect(database)
                try:
                    db.execute("CREATE TABLE metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
                    db.execute("INSERT INTO metadata VALUES ('schema_version', ?)", (version,))
                    db.execute("CREATE TABLE foreign_payload (retained BLOB)")
                    db.execute("INSERT INTO foreign_payload VALUES (?)", (b"unchanged source and data",))
                    db.commit()
                    tables = db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall()
                    journal = db.execute("PRAGMA journal_mode").fetchone()[0]
                finally:
                    db.close()
                original = database.read_bytes()
                with self.assertRaises(ProtocolError) as caught:
                    ProgramAgentService(path, protocol=PROTOCOL)
                self.assertEqual(caught.exception.code, "OKA-E-STORE-VERSION")
                self.assertEqual(caught.exception.details["actual"], version)
                self.assertEqual(database.read_bytes(), original)
                self.assertEqual(sorted(item.name for item in path.iterdir()), [database.name])
                db = sqlite3.connect(database)
                try:
                    self.assertEqual(db.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall(), tables)
                    self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], journal)
                    self.assertEqual(db.execute("SELECT retained FROM foreign_payload").fetchone()[0], b"unchanged source and data")
                finally:
                    db.close()

    def test_native_profile_can_import_pinned_older_components_without_surface_relabeling(self):
        library = SourceUnit("package:fixture.legacy@1.0.0", "legacy.ok", b'''ontokin "0.2";
module Legacy @ "legacy";
profile "construction-0.1";
public class Marker @ "marker" {
    geometry = sphere(0.1[m]);
    physical = no_body();
}
''', "fixture.legacy", "1.0.0")
        source = single_source(objects='object shell @ "shell": Shell {} object marker @ "marker": old.Marker {}')
        source = source.replace('profile "surface-0.1";', 'profile "surface-0.1";\n' +
                                f'import old @ "old" from "fixture.legacy" version "1.0.0" digest "{library.revision}";')
        program = ProgramBundle(SourceUnit("entry", "mixed-native.ok", source.encode("utf-8")), (library,))
        with tempfile.TemporaryDirectory() as directory, ProgramAgentService(Path(directory), protocol=PROTOCOL) as service:
            created = service.handle(self.request("create", bundle=program.to_payload(), requested_level="evaluated"))
            self.assertEqual(created["status"], "succeeded", created)
            revision = created["program_revision"]
            page = service.handle(self.request(program_revision=revision, request_id="surface-page",
                                               element_id=["native-export", "demo", "shell"]))
            self.assertEqual(page["status"], "succeeded", page)
            primitive = service.handle(self.request(program_revision=revision, request_id="primitive-page",
                                                    element_id=["native-export", "demo", "marker"]))
            self.assert_code(primitive, "OKL-E-CAPABILITY-UNSUPPORTED")
            self.assertEqual(service.read_unit("boundary", revision, library.source_id).raw, library.raw)
            request = self.request("inspect", program_revision=revision, request_id="primitive-summary",
                                   selector={"path": "marker"}, fields=["geometry", "source"], limit=1)
            inspected = service.handle(request)
            self.assertEqual(inspected["status"], "succeeded", inspected)
            item = inspected["result"]["items"][0]
            self.assertNotIn("surface", item["geometry"])
            self.assertEqual(item["source"]["definition_span"]["source_revision"], library.revision)
            self.assertEqual(item["geometry"]["description"]["kind"], "sphere")
            json.dumps(item, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
