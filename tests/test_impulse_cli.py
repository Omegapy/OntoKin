"""Explicit impulse CLI selection, exact source delivery and startup failures."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ontokin.bundle import load_file_manifest
from ontokin.cli import main, capabilities
from tests.test_export import DecodedGLB
from tests.test_impulse_export import FIXTURES, CASES

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "ontokin.agent/0.4"
CONTRACT = "ontokin.glb/0.4"


class ImpulseCLITests(unittest.TestCase):
    def invoke(self, args):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main([str(arg) for arg in args])
        return result, json.loads(stdout.getvalue())

    def test_explicit_bundle_export_preserves_frozen_sources_and_bound_sidecar(self):
        manifest = FIXTURES / CASES["P02"]["file_manifest"]
        bundle = load_file_manifest(manifest)
        original = {unit.source_id: unit.raw for unit in bundle.units}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "impulse.glb"
            status, report = self.invoke(["export", manifest, "--bundle", "--target", CONTRACT,
                "--output", output, "--no-helpers"])
            self.assertEqual(status, 0, report)
            self.assertEqual(report, json.loads(output.with_suffix(".export.json").read_text()))
            self.assertEqual(report["artifact"]["sha256"], "sha256:" + hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(report["program_revision"], CASES["P02"]["program_revision"])
            metadata = DecodedGLB(output.read_bytes()).document["extras"]["ontokin"]
            self.assertEqual(metadata["target_contract"], CONTRACT)
            self.assertEqual(metadata["boundary_states"][1]["impulse_states_after"]["ball"]["applied_count"], 1)
        self.assertEqual({unit.source_id: unit.raw for unit in load_file_manifest(manifest).units}, original)

    def test_failed_old_target_preserves_existing_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "prior.glb"
            sidecar = output.with_suffix(".export.json")
            output.write_bytes(b"previous-artifact")
            sidecar.write_bytes(b"previous-report")
            status, report = self.invoke(["export", FIXTURES / CASES["P02"]["file_manifest"], "--bundle",
                "--target", "ontokin.glb/0.3", "--output", output])
            self.assertNotEqual(status, 0)
            self.assertEqual(report["diagnostics"][0]["details"]["target_contract"], "ontokin.glb/0.3")
            self.assertEqual(output.read_bytes(), b"previous-artifact")
            self.assertEqual(sidecar.read_bytes(), b"previous-report")

    def test_jsonl_malformed_request_uses_selected_impulse_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run([sys.executable, "-m", "ontokin", "agent", "--store", directory,
                "--protocol", PROTOCOL], input=b'{"bad":\n', capture_output=True, cwd=ROOT, timeout=30)
            self.assertEqual(process.stderr, b"")
            response = json.loads(process.stdout)
            self.assertEqual(response["schema_version"], PROTOCOL)
            self.assertEqual(response["protocol_error"]["code"], "OKA-E-JSON")

    def test_corrupt_or_directory_store_reports_controlled_selected_protocol_error(self):
        for kind in ("corrupt", "directory"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "impulse-program-agent.sqlite3"
                if kind == "corrupt":
                    target.write_bytes(b"not SQLite; unchanged bytes")
                else:
                    target.mkdir()
                process = subprocess.run([sys.executable, "-m", "ontokin", "agent", "--store", directory,
                    "--protocol", PROTOCOL], input=b"", capture_output=True, cwd=ROOT, timeout=30)
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual(process.stderr, b"")
                response = json.loads(process.stdout)
                self.assertEqual(response["schema_version"], PROTOCOL)
                self.assertEqual(response["protocol_error"]["code"], "OKA-E-STORE")
                if kind == "corrupt":
                    self.assertEqual(target.read_bytes(), b"not SQLite; unchanged bytes")
                else:
                    self.assertEqual(list(target.iterdir()), [])

    def test_capabilities_add_impulse_without_relabeling_old_defaults(self):
        result = capabilities()
        self.assertEqual((result["language_version"], result["profile"]), ("0.1", "core-0.1"))
        self.assertEqual(result["agent_interface"]["schema_version"], "ontokin.agent/0.1")
        self.assertEqual(result["surface_interface"]["agent_contract"], "ontokin.agent/0.3")
        self.assertEqual(result["impulse_interface"]["agent_contract"], PROTOCOL)
        self.assertEqual(result["export_targets"][CONTRACT]["profile"], "impulse-0.1")


if __name__ == "__main__":
    unittest.main()
