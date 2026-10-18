"""Native source workflows through real Agent/0.3 CLI processes and JSONL.

The frozen Studio bundle remains authoritative. Process boundaries exercise
durable receipts, source identities, mesh cursors and exact artifact retrieval.
"""

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_export import DecodedGLB
from tests.test_surface_source import bundle as studio_bundle


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "ontokin.agent/0.3"
DESTINATION = "ontokin.glb/0.3"
FIRST = ["surface-studio", "studio", "first"]


class SurfaceAgentCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-surface-cli-")
        self.directory = Path(self.temporary.name)
        self.store = self.directory / "state"
        self.program = studio_bundle()
        self.serial = 0

    def tearDown(self):
        self.temporary.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "cli-native",
                "request_id": f"request-{self.serial}", "operation": operation, **fields}

    def create_request(self):
        return self.request("create", bundle=self.program.to_payload(),
                            expected_program_revision=None, requested_level="constructed")

    def command(self, protocol=PROTOCOL):
        command = [sys.executable, "-m", "ontokin", "agent", "--store", str(self.store)]
        return command + (["--protocol", protocol] if protocol is not None else [])

    def run_request(self, submitted, *, wait=True, protocol=PROTOCOL):
        path = self.directory / f"{submitted['request_id']}.json"
        path.write_text(json.dumps(submitted, ensure_ascii=False), encoding="utf-8")
        command = self.command(protocol) + ["--request", str(path)] + (["--wait"] if wait else [])
        process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(process.stderr, b"", process.stderr)
        response = json.loads(process.stdout)
        self.assertEqual(response["schema_version"], protocol or "ontokin.agent/0.1")
        return response, process.returncode

    def assert_success(self, response):
        self.assertEqual(response["status"], "succeeded", response)
        self.assertIsNone(response["protocol_error"], response)
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.assertNotIn("source_revision", response)
        self.assertNotIn("accepted_revision", response)

    def test_source_create_mesh_evaluate_export_and_artifact_across_processes(self):
        created, status = self.run_request(self.create_request())
        self.assertEqual(status, 0)
        self.assert_success(created)
        revision = self.program.program_revision
        self.assertEqual(created["program_revision"], revision)
        self.assertEqual(created["accepted_program_revision"], revision)

        page, status = self.run_request(self.request("surface.mesh_page",
            program_revision=revision, element_id=FIRST, count=2))
        self.assertEqual(status, 0)
        self.assert_success(page)
        self.assertEqual(page["operation"], "surface.mesh_page")
        self.assertEqual(page["result"]["source_triangle_ordinals"], [0, 1])
        self.assertEqual(len(page["result"]["positions_m"]), 6)
        self.assertIsNotNone(page["next_cursor"])
        next_page, status = self.run_request(self.request("surface.mesh_page",
            program_revision=revision, element_id=FIRST, count=256, cursor=page["next_cursor"]))
        self.assertEqual(status, 0)
        self.assert_success(next_page)
        self.assertEqual(next_page["result"]["offset"], 2)
        self.assertIsNone(next_page["next_cursor"])
        self.assertEqual(page["result"]["geometry_sha256"], next_page["result"]["geometry_sha256"])

        evaluated, status = self.run_request(self.request("evaluate", program_revision=revision,
                                                          run_id=None, until_seconds="0.25"))
        self.assertEqual(status, 0)
        self.assert_success(evaluated)
        self.assertTrue(evaluated["run_id"])
        exported, status = self.run_request(self.request("export", program_revision=revision,
            destination=DESTINATION, options={"end": "0.25", "fps": 8, "helpers": False}))
        self.assertEqual(status, 0)
        self.assert_success(exported)
        self.assertEqual(exported["result"]["destination"], DESTINATION)
        fetched, status = self.run_request(self.request("artifact",
            artifact_id=exported["result"]["artifact_id"], offset=0, max_bytes=65536))
        self.assertEqual(status, 0)
        self.assert_success(fetched)
        self.assertEqual(fetched["program_revision"], revision)
        self.assertEqual(fetched["accepted_program_revision"], revision)
        self.assertIsNone(fetched["result"]["next_offset"])
        data = base64.b64decode(fetched["result"]["data_base64"], validate=True)
        self.assertEqual("sha256:" + hashlib.sha256(data).hexdigest(), exported["result"]["sha256"])
        decoded = DecodedGLB(data)
        metadata = decoded.document["extras"]["ontokin"]
        self.assertEqual(metadata["target_contract"], DESTINATION)
        self.assertEqual(metadata["program"]["revision"], revision)
        self.assertEqual(decoded.node_pose("first", .25)["translation"], (-2, .125, 0))
        self.assertEqual(len(decoded.document["meshes"]), 2)

    def test_queued_request_reopens_and_exact_retry_preserves_terminal_result(self):
        submitted = self.create_request()
        receipt, status = self.run_request(submitted, wait=False)
        self.assertEqual(status, 0)
        self.assertEqual(receipt["status"], "queued")
        completed, status = self.run_request(submitted)
        self.assertEqual(status, 0)
        self.assert_success(completed)
        replay, status = self.run_request(dict(reversed(list(submitted.items()))))
        self.assertEqual(status, 0)
        self.assertEqual(replay, completed)
        changed, status = self.run_request({**submitted, "requested_level": "represented"})
        self.assertEqual(status, 1)
        self.assertEqual(changed["status"], "rejected")
        self.assertIsNotNone(changed["protocol_error"])
        replay, _ = self.run_request(submitted)
        self.assertEqual(replay, completed)

    def test_invalid_json_and_utf8_do_not_end_the_selected_jsonl_stream(self):
        submitted = self.create_request()
        lines = [b'{"request_id":"one","request_id":"two"}', b'"\xff"',
                 json.dumps(submitted).encode("utf-8")]
        process = subprocess.run(self.command() + ["--wait"], cwd=ROOT,
                                 input=b"\n".join(lines) + b"\n", capture_output=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, b"")
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(responses), 3)
        for rejected in responses[:2]:
            self.assertEqual(rejected["schema_version"], PROTOCOL)
            self.assertEqual(rejected["status"], "rejected")
            self.assertEqual(rejected["protocol_error"]["code"], "OKA-E-JSON")
            self.assertIsNone(rejected["operation"])
            self.assertIsNone(rejected["program_revision"])
        self.assert_success(responses[2])
        self.assertEqual(responses[2]["request_id"], submitted["request_id"])

    def test_background_jsonl_drains_after_eof_without_unsolicited_responses(self):
        submitted = self.create_request()
        process = subprocess.run(self.command(), cwd=ROOT,
            input=(json.dumps(submitted) + "\n").encode("utf-8"), capture_output=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        lines = process.stdout.splitlines()
        self.assertEqual(len(lines), 1, process.stdout)
        receipt = json.loads(lines[0])
        self.assertEqual(receipt["schema_version"], PROTOCOL)
        self.assertEqual(receipt["status"], "queued")
        status, exit_status = self.run_request(self.request("status", target_request_id=submitted["request_id"]))
        self.assertEqual(exit_status, 0)
        self.assert_success(status)
        terminal = status["result"]["target"]
        self.assert_success(terminal)
        self.assertEqual(terminal["program_revision"], self.program.program_revision)
        repeated, _ = self.run_request(submitted)
        self.assertEqual(repeated, terminal)

    def test_default_and_construction_cli_do_not_select_a_surface_store_from_json(self):
        submitted = self.create_request()
        for protocol, filename in ((None, "agent.sqlite3"), ("ontokin.agent/0.2", "program-agent.sqlite3")):
            with self.subTest(protocol=protocol):
                response, status = self.run_request(submitted, protocol=protocol)
                self.assertEqual(status, 1)
                self.assertEqual(response["status"], "rejected")
                self.assertEqual(response["protocol_error"]["code"], "OKA-E-REQUEST")
                self.assertTrue((self.store / filename).is_file())
                self.assertFalse((self.store / "surface-program-agent.sqlite3").exists())
        native, status = self.run_request(submitted)
        self.assertEqual(status, 0)
        self.assert_success(native)
        self.assertTrue((self.store / "surface-program-agent.sqlite3").is_file())

    def test_startup_and_request_file_errors_keep_the_selected_protocol(self):
        missing = self.directory / "absent-request.json"
        process = subprocess.run(self.command() + ["--request", str(missing), "--wait"],
                                 cwd=ROOT, capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 1)
        response = json.loads(process.stdout)
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.assertEqual(response["protocol_error"]["code"], "OKA-E-IO")
        self.assertNotIn("source_revision", response)
        blocked = self.directory / "store-is-a-file"
        blocked.write_bytes(b"preserve this file")
        self.store = blocked
        process = subprocess.run(self.command(), cwd=ROOT, input=b"", capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 1)
        response = json.loads(process.stdout)
        self.assertEqual(response["schema_version"], PROTOCOL)
        self.assertEqual(response["protocol_error"]["code"], "OKA-E-STORE")
        self.assertEqual(blocked.read_bytes(), b"preserve this file")

    def test_discovery_is_executable_and_rejects_wrong_delivery_without_losing_source(self):
        request = self.request("discover", profile="surface-0.1", limit=20,
                               filter={"name": "loft"}, bundle=self.program.to_payload())
        discovered, status = self.run_request(request)
        self.assertEqual(status, 0)
        self.assert_success(discovered)
        self.assertEqual(discovered["result"]["schema_version"], "ontokin.agent-catalog/0.3")
        self.assertEqual(discovered["program_revision"], self.program.program_revision)
        self.assertTrue(discovered["result"]["items"])
        created, _ = self.run_request(self.create_request())
        self.assert_success(created)
        rejected, status = self.run_request(self.request("export", program_revision=self.program.program_revision,
                                                          destination="ontokin.glb/0.2"))
        self.assertEqual(status, 1)
        self.assertEqual(rejected["protocol_error"]["code"], "OKA-E-REQUEST")
        page, status = self.run_request(self.request("surface.mesh_page", program_revision=self.program.program_revision,
                                                      element_id=FIRST, count=1))
        self.assertEqual(status, 0)
        self.assert_success(page)
        self.assertEqual(page["accepted_program_revision"], self.program.program_revision)

    def test_corrupt_or_directory_database_returns_json_without_modifying_existing_data(self):
        for condition in ("corrupt-bytes", "database-is-directory"):
            with self.subTest(condition=condition):
                self.store = self.directory / condition
                self.store.mkdir()
                database = self.store / "surface-program-agent.sqlite3"
                original = b"Preserve these bytes: this is not an SQLite database.\n"
                if condition == "corrupt-bytes":
                    database.write_bytes(original)
                else:
                    database.mkdir()
                process = subprocess.run(self.command() + ["--wait"], cwd=ROOT,
                                         input=b"", capture_output=True, timeout=20)
                self.assertEqual(process.returncode, 1)
                self.assertEqual(process.stderr, b"")
                self.assertEqual(len(process.stdout.splitlines()), 1)
                response = json.loads(process.stdout)
                self.assertEqual(response["schema_version"], PROTOCOL)
                self.assertEqual(response["status"], "rejected")
                self.assertEqual(response["protocol_error"]["code"], "OKA-E-STORE")
                self.assertIsNone(response["accepted_program_revision"])
                if condition == "corrupt-bytes":
                    self.assertEqual(database.read_bytes(), original)
                else:
                    self.assertTrue(database.is_dir())
                    self.assertEqual(list(database.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
