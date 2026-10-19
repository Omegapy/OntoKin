"""Agent/0.4 selection, source-only requests and isolated durable envelopes."""
import copy
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.bundle import load_file_manifest
from ontokin.program_agent import ProgramAgentService
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin import program_protocol


FIXTURES = Path(__file__).resolve().parents[1] / "docs/language-design/impulse-v0.1"
PROTOCOL = "ontokin.agent/0.4"


class ImpulseAgentProtocolTests(unittest.TestCase):
    def setUp(self):
        self.binding = program_protocol.bind(PROTOCOL)
        self.program = load_file_manifest(FIXTURES / "p02-off-center-mixed-imports.files.json")

    def request(self, operation="surface.mesh_page", **fields):
        result = {"schema_version": PROTOCOL, "project_id": "impulse", "request_id": "request",
                  "operation": operation}
        if operation == "surface.mesh_page":
            result.update(program_revision=self.program.program_revision,
                          element_id=["impulse-demo", "demo", "ball"], count=1)
        if operation == "create":
            result.update(bundle=self.program.to_payload(), expected_program_revision=None,
                          requested_level="represented")
        result.update(fields)
        return result

    def test_binding_is_explicit_with_unchanged_old_defaults_and_operations(self):
        self.assertEqual(self.binding.profile, "impulse-0.1")
        self.assertEqual(self.binding.destination, "ontokin.glb/0.4")
        self.assertEqual(self.binding.OPERATIONS, program_protocol.bind("ontokin.agent/0.3").OPERATIONS)
        self.assertEqual(program_protocol.SCHEMA_VERSION, "ontokin.agent/0.2")
        self.assertEqual(program_protocol.bind().profile, "construction-0.1")
        self.assertNotIn("surface.mesh_page", program_protocol.OPERATIONS)
        self.binding.validate_request(self.request())
        for older in ("ontokin.agent/0.2", "ontokin.agent/0.3"):
            with self.subTest(older=older), self.assertRaises(ProtocolError):
                program_protocol.bind(older).validate_request(self.request())
            with self.subTest(older=older), self.assertRaises(ProtocolError):
                self.binding.validate_request(self.request(schema_version=older))
        for unknown in ("ontokin.agent/0.6", "ontokin.agent/0.1", None, [], {}):
            with self.subTest(unknown=unknown), self.assertRaises(ProtocolError):
                program_protocol.bind(unknown)

    def test_binding_lookup_and_per_instance_operation_sets_are_detached(self):
        with self.assertRaises(TypeError):
            PROGRAM_BINDINGS[PROTOCOL] = None
        with self.assertRaises(TypeError):
            PROFILE_BINDINGS["impulse-0.1"] = None
        with self.assertRaises(FrozenInstanceError):
            PROGRAM_BINDINGS[PROTOCOL].destination = "ontokin.glb/0.3"
        self.binding.OPERATIONS["surface.mesh_page"][0].add("fabricated")
        self.binding.MAX_BUDGETS["max_value_entries"] = 1
        fresh = program_protocol.bind(PROTOCOL)
        fresh.validate_request(self.request())
        self.assertEqual(fresh.MAX_BUDGETS["max_value_entries"], 100000)
        self.assertNotIn("fabricated", program_protocol.bind("ontokin.agent/0.3").OPERATIONS["surface.mesh_page"][0])

    def test_no_host_impulse_rpc_or_state_mutation_request_fields(self):
        for operation in ("impulse", "apply_impulse", "applyImpulse", "set_velocity", "set_state"):
            request = self.request(operation)
            with self.subTest(operation=operation), self.assertRaises(ProtocolError):
                self.binding.validate_request(request)
            self.assertIsNone(self.binding.envelope(request, "rejected")["operation"])
        for extra in ({"impulse_world_n_s": [0, 2, 0]}, {"impulses": []}, {"velocity": [0, 1, 0]},
                      {"entry_profile": "impulse-0.1"}):
            with self.subTest(extra=extra), self.assertRaises(ProtocolError):
                self.binding.validate_request(self.request("create", **extra))

    def test_native_destination_is_explicit_and_never_coerced(self):
        request = self.request("create", requested_level="delivered", destination="ontokin.glb/0.4",
                               options={"fps": 1, "helpers": False})
        self.binding.validate_request(request)
        for target in ("ontokin.glb/0.1", "ontokin.glb/0.2", "ontokin.glb/0.3", "ontokin.glb/0.5"):
            with self.subTest(target=target), self.assertRaises(ProtocolError):
                self.binding.validate_request({**request, "destination": target})
        with self.assertRaises(ProtocolError):
            self.binding.validate_request({**request, "requested_level": "evaluated"})
        no_destination = {k:v for k,v in request.items() if k != "destination"}
        with self.assertRaises(ProtocolError):
            self.binding.validate_request(no_destination)

    def test_inherited_page_token_bounds_and_envelope_operation_identity(self):
        for count in (1, 7, 256):
            request = self.request(count=count)
            self.binding.validate_request(request)
            for status in ("queued", "running", "succeeded", "rejected", "failed", "cancelled"):
                response = self.binding.envelope(request, status)
                self.assertEqual(response["schema_version"], PROTOCOL)
                self.assertEqual(response["operation"], "surface.mesh_page")
                self.assertEqual(response["program_revision"], self.program.program_revision)
        for count in (0, 257, 1.0, True, "1", None):
            with self.subTest(count=count), self.assertRaises(ProtocolError):
                self.binding.validate_request(self.request(count=count))
        for extra in ({"region":None}, {"entry_profile":"impulse-0.1"}, {"time":{"seconds":"1","side":"after"}},
                      {"run_id":None}, {"count":1,"budgets":{"max_value_entries":100001}}):
            with self.subTest(extra=extra), self.assertRaises(ProtocolError):
                self.binding.validate_request(self.request(**extra))

    def test_context_binds_entry_only_for_impulse_without_public_profile_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            for protocol in ("ontokin.agent/0.2", "ontokin.agent/0.3", PROTOCOL):
                with ProgramAgentService(directory, protocol=protocol) as service:
                    context = service._context_binding()
                    self.assertEqual(context["protocol"], protocol)
                    self.assertEqual(context["implementation"], service.implementation)
                    if protocol == PROTOCOL:
                        self.assertEqual(context["entry_profile"], "impulse-0.1")
                    else:
                        self.assertNotIn("entry_profile", context)

    def test_all_four_stores_keep_identical_request_ids_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            definitions = [("ontokin.agent/0.1", "agent.sqlite3", "ontokin.agent-store/0.1"),
                *[(b.protocol,b.store_filename,b.store_schema) for b in PROGRAM_BINDINGS.values()]]
            for protocol,filename,schema in definitions:
                service = AgentService(directory) if protocol.endswith("/0.1") else ProgramAgentService(directory, protocol=protocol)
                try:
                    key = "source_revision" if protocol.endswith("/0.1") else "program_revision"
                    request = {"schema_version":protocol,"project_id":"same","request_id":"same",
                               "operation":"validate",key:"sha256:"+"a"*64,"requested_level":"represented"}
                    response = service.submit(request)
                    self.assertEqual(response["status"], "queued", response)
                    self.assertEqual(response["schema_version"], protocol)
                    self.assertEqual(service._store.database_path.name, filename)
                    with service._store.connection() as db:
                        self.assertEqual(db.execute("SELECT value FROM metadata WHERE name='schema_version'").fetchone()[0],schema)
                        saved = json.loads(db.execute("SELECT payload FROM requests WHERE id='same'").fetchone()[0])
                        self.assertEqual(saved,request)
                finally:
                    service.close()
            self.assertEqual({p.name for p in Path(directory).glob('*.sqlite3')},{r[1] for r in definitions})

    def test_wrong_store_version_rejects_before_journal_or_ddl_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"impulse-program-agent.sqlite3"
            with sqlite3.connect(path) as db:
                db.executescript("CREATE TABLE metadata(name TEXT PRIMARY KEY,value TEXT NOT NULL);"
                                 "CREATE TABLE sentinel(payload BLOB);")
                db.execute("INSERT INTO metadata VALUES ('schema_version','ontokin.surface-program-agent-store/0.1')")
                db.execute("INSERT INTO sentinel VALUES (?)",(b'keep exact old contents',))
            before=path.read_bytes(); listing={p.name for p in Path(directory).iterdir()}
            with self.assertRaises(ProtocolError) as caught:
                ProgramAgentService(directory,protocol=PROTOCOL)
            self.assertEqual(caught.exception.code,"OKA-E-STORE-VERSION")
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual({p.name for p in Path(directory).iterdir()},listing)

    def test_malformed_request_fails_before_candidate_or_run_write(self):
        with tempfile.TemporaryDirectory() as directory, ProgramAgentService(directory,protocol=PROTOCOL) as service:
            request=self.request('create'); request['bundle']['entry']['source']=False
            response=service.handle(request)
            self.assertEqual(response['status'],'rejected',response)
            self.assertEqual(response['schema_version'],PROTOCOL)
            with service._store.connection() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM sources').fetchone()[0],0)
                self.assertEqual(db.execute('SELECT count(*) FROM runs').fetchone()[0],0)


if __name__ == '__main__':
    unittest.main()
