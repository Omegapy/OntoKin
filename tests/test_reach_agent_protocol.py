"""Strict Agent/0.6 selection, wire limits and isolated inherited stores."""
import copy
from pathlib import Path
import tempfile
import unittest

from ontokin.agent import AgentService
from ontokin.agent_protocol import ProtocolError
from ontokin.construction_catalog import catalog
from ontokin.program_agent import ProgramAgentService
from ontokin.program_bindings import PROGRAM_BINDINGS
from ontokin.program_protocol import bind
from reach_agent_support import PROFILE, PROTOCOL, TARGET


class ReachAgentProtocolTests(unittest.TestCase):
    def request(self, operation="inspect", **fields):
        return dict(schema_version=PROTOCOL, project_id="p", request_id="r", operation=operation, **fields)

    def test_exact_twelve_operations_and_unchanged_defaults(self):
        protocol = bind(PROTOCOL)
        self.assertEqual(set(protocol.OPERATIONS), {"discover", "create", "edit", "validate", "inspect", "evaluate",
                                                  "reset", "status", "cancel", "export", "artifact", "surface.mesh_page"})
        self.assertEqual(protocol.profile, PROFILE)
        self.assertEqual(protocol.destination, TARGET)
        self.assertEqual(bind().SCHEMA_VERSION, "ontokin.agent/0.2")
        for operation in ("reach", "reach_planar", "set_goal", "set_coordinates", "set_velocity", "apply_force"):
            with self.subTest(operation=operation), self.assertRaises(ProtocolError):
                protocol.validate_request(self.request(operation))

    def test_explicit_binding_cannot_be_switched_by_a_request(self):
        for version in ("0.1", "0.2", "0.3", "0.4", "0.5"):
            request = self.request("status", target_request_id="old")
            request["schema_version"] = "ontokin.agent/" + version
            with self.subTest(version=version), self.assertRaises(ProtocolError):
                bind(PROTOCOL).validate_request(request)

    def test_reach_clock_limit_does_not_change_older_options(self):
        request = self.request("export", program_revision="sha256:" + "a" * 64,
                               destination=TARGET, options={"time_tolerance_s": 1e-6})
        bind(PROTOCOL).validate_request(request)
        for value in (1.000001e-6, 0, True, float("nan"), float("inf"), "0.000001"):
            with self.subTest(value=value), self.assertRaises(ProtocolError):
                bind(PROTOCOL).validate_request({**request, "options": {"time_tolerance_s": value}})
        older = {**request, "schema_version": "ontokin.agent/0.5", "destination": "ontokin.glb/0.5",
                 "options": {"time_tolerance_s": .01}}
        bind("ontokin.agent/0.5").validate_request(older)

    def test_inspection_has_one_entry_budget_and_integer_wire_fields(self):
        request = self.request(program_revision="sha256:" + "a" * 64, selector={"kind": "action"},
                               fields=["actions"], limit=128, budgets={"max_value_entries": 100000})
        bind(PROTOCOL).validate_request(request)
        for changed in ({"limit": 128.0}, {"limit": True}, {"max_bytes": 1000}, {"max_response_bytes": 1000},
                        {"budgets": {"max_value_entries": 100001}}, {"budgets": {"max_value_entries": 1.0}}):
            with self.subTest(changed=changed), self.assertRaises(ProtocolError):
                bind(PROTOCOL).validate_request({**request, **changed})

    def test_six_stores_coexist_with_identical_project_and_request_ids(self):
        definitions = [("ontokin.agent/0.1", "agent.sqlite3"),
                       *[(binding.protocol, binding.store_filename) for binding in PROGRAM_BINDINGS.values()]]
        self.assertEqual(len(definitions), 6)
        with tempfile.TemporaryDirectory() as directory:
            for protocol, filename in definitions:
                service = AgentService(directory) if protocol.endswith("/0.1") else ProgramAgentService(directory, protocol=protocol)
                with service:
                    revision_key = "source_revision" if protocol.endswith("/0.1") else "program_revision"
                    response = service.submit(dict(schema_version=protocol, project_id="same", request_id="same",
                        operation="validate", requested_level="represented", **{revision_key: "sha256:" + "a" * 64}))
                    self.assertEqual(response["status"], "queued")
                    self.assertEqual(service.database_path.name, filename)
            self.assertEqual({path.name for path in Path(directory).glob("*.sqlite3")}, {name for _, name in definitions})

    def test_additive_catalog_preserves_old_catalogs_and_names_real_source_examples(self):
        before = {profile: catalog(profile=profile) for profile in ("construction-0.1", "surface-0.1", "impulse-0.1", "force-0.1")}
        reach = catalog(profile=PROFILE)
        self.assertEqual(reach["agent_contract"], PROTOCOL)
        self.assertFalse(reach["full_product_conformance_certified"])
        names = {item["name"]: item for item in reach["items"]}
        self.assertEqual(names["reach_planar"]["kind"], "function")
        self.assertEqual(names["ReachBranch"]["kind"], "type")
        self.assertEqual(names[PROTOCOL]["store_filename"], "planar-reach-program-agent.sqlite3")
        self.assertEqual(names[PROTOCOL]["store_schema"], "ontokin.planar-reach-program-agent-store/0.1")
        self.assertEqual(len({item["id"] for item in reach["items"]}), len(reach["items"]))
        self.assertEqual(names["external_forces_and_actuators"]["availability"], "unsupported")
        root = Path(__file__).resolve().parents[1]
        for filename in reach["complete_examples"] + reach["example_file_manifests"]:
            self.assertTrue((root / filename).is_file(), filename)
        for profile, previous in before.items():
            self.assertEqual(catalog(profile=profile), previous)
        altered = copy.deepcopy(reach)
        altered["items"][0]["description"] = "caller mutation"
        self.assertEqual(catalog(profile=PROFILE), reach)


if __name__ == "__main__":
    unittest.main()
