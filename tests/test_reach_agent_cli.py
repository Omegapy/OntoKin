"""Actual explicit Agent/0.6 JSONL transport and unchanged core default."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from reach_agent_support import PROTOCOL, ROOT, source_case


class ReachAgentCLITests(unittest.TestCase):
    def invoke(self, directory, payload, *, selected=True):
        arguments = [sys.executable, "-m", "ontokin", "agent", "--store", str(directory), "--wait"]
        if selected:
            arguments.extend(("--protocol", PROTOCOL))
        process = subprocess.run(arguments, input=payload, capture_output=True, cwd=ROOT, timeout=60)
        self.assertEqual(process.stderr, b"")
        return process.returncode, [json.loads(line) for line in process.stdout.splitlines()]

    def test_malformed_json_then_actual_create_retain_selected_binding(self):
        program = source_case("P01")
        request = dict(schema_version=PROTOCOL, project_id="cli", request_id="create", operation="create",
                       bundle=program.to_payload(), expected_program_revision=None, requested_level="constructed")
        with tempfile.TemporaryDirectory() as directory:
            code, results = self.invoke(directory, b'{"broken":\n' + json.dumps(request).encode() + b"\n")
            self.assertEqual(code, 0)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["schema_version"], PROTOCOL)
            self.assertEqual(results[0]["protocol_error"]["code"], "OKA-E-JSON")
            self.assertEqual(results[1]["status"], "succeeded", results[1])
            self.assertEqual(results[1]["accepted_program_revision"], program.program_revision)
            projection = results[1]["result"]["initial_state"]["reaches"]["reach"]
            self.assertEqual(projection["context_origin"], "agent")
            self.assertEqual(projection["current"]["value"]["observation"]["context_kind"], "constructed_initial")
            self.assertTrue((Path(directory) / "planar-reach-program-agent.sqlite3").is_file())
            self.assertFalse((Path(directory) / "agent.sqlite3").exists())

    def test_default_transport_stays_agent_01(self):
        with tempfile.TemporaryDirectory() as directory:
            _, results = self.invoke(directory, b'{"broken":\n', selected=False)
            self.assertEqual(results[0]["schema_version"], "ontokin.agent/0.1")
            self.assertFalse((Path(directory) / "planar-reach-program-agent.sqlite3").exists())

    def test_corrupt_selected_store_returns_error_without_replacement(self):
        for kind in ("file", "directory"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "planar-reach-program-agent.sqlite3"
                if kind == "file":
                    path.write_bytes(b"preserve corrupt store bytes")
                else:
                    path.mkdir()
                code, results = self.invoke(directory, b"")
                self.assertNotEqual(code, 0)
                self.assertEqual(results[0]["schema_version"], PROTOCOL)
                self.assertEqual(results[0]["protocol_error"]["code"], "OKA-E-STORE")
                if kind == "file":
                    self.assertEqual(path.read_bytes(), b"preserve corrupt store bytes")
                else:
                    self.assertEqual(list(path.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
