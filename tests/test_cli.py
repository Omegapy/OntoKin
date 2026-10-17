"""Exercise the user-facing commands with real files and JSON output."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ontokin.cli import main
from ontokin.fixtures import DEFAULT_FIXTURES, load_manifest, materialize


class CLITests(unittest.TestCase):
    def invoke(self, args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = main(args)
        return status, json.loads(output.getvalue())

    def test_module_entrypoint_and_capabilities(self):
        completed = subprocess.run([sys.executable, "-m", "ontokin", "capabilities"],
                                   capture_output=True, text=True, check=True)
        result = json.loads(completed.stdout)
        self.assertIn("evaluate", result["operations"])
        self.assertEqual(result["runtime_dependencies"], [])

    def test_four_complete_source_programs(self):
        for path in sorted(DEFAULT_FIXTURES.glob("*.ok")):
            with self.subTest(path=path.name):
                status, result = self.invoke(["check", str(path)])
                self.assertEqual(status, 0)
                self.assertEqual(result["outcome"], "valid")
                self.assertIn("timeline_preflight", result)

    def test_sample_and_requested_frame(self):
        path = str(DEFAULT_FIXTURES / "04-ownership-reuse-and-follow.ok")
        status, result = self.invoke(["evaluate", path, "--times", "0.5", "--object", "first.ball", "--frame", "first.frame"])
        self.assertEqual(status, 0)
        self.assertAlmostEqual(result["inspection"][0]["position_m"][0], -0.5)
        self.assertEqual(result["inspection"][0]["velocity_measured_in"], "world")
        self.assertTrue(result["run_id"])

    def test_invalid_source_has_revision_span_and_repair(self):
        case = next(c for c in load_manifest()["cases"] if c["id"] == "N06")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong-unit.ok"
            source = materialize(case)
            path.write_text(source, encoding="utf-8")
            status, result = self.invoke(["check", str(path)])
            self.assertEqual(status, 2)
            diagnostic = result["diagnostics"][0]
            self.assertEqual(diagnostic["code"], "OKL-E-UNIT")
            self.assertTrue(diagnostic["repair"]["summary"])
            self.assertEqual(path.read_text(), source)

    def test_unavailable_delivery_is_not_lower_level_success(self):
        path = str(DEFAULT_FIXTURES / "01-independent-parts.ok")
        status, result = self.invoke(["check", path, "--level", "delivered"])
        self.assertEqual(status, 3)
        self.assertEqual(result["outcome"], "unsupported")
        self.assertEqual(result["diagnostics"][0]["blocks"], ["delivered"])

    def test_constructed_resolves_initial_pose_without_admitting_actions(self):
        path = str(DEFAULT_FIXTURES / "02-gravity-and-release.ok")
        status, result = self.invoke(["check", path, "--level", "constructed"])
        self.assertEqual(status, 0)
        state = result["initial_state"]
        self.assertEqual(state["side"], "before")
        self.assertEqual(state["objects"]["payload"]["position_m"], [0, 2, 0])
        self.assertEqual(state["actions"]["carry"]["status"], "pending")

    def test_timeline_limit_failure_does_not_block_construction(self):
        case = next(c for c in load_manifest()["cases"] if c["id"] == "N14")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future-limit.ok"
            path.write_text(materialize(case), encoding="utf-8")
            status, result = self.invoke(["check", str(path), "--level", "constructed"])
            self.assertEqual(status, 0)
            self.assertIn("initial_state", result)
            status, result = self.invoke(["check", str(path)])
            self.assertEqual(status, 2)
            self.assertEqual(result["diagnostics"][0]["blocks"], ["evaluated", "delivered"])

    def test_invalid_utf8_is_reported_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.ok"
            path.write_bytes(b"ontokin \xff")
            status, result = self.invoke(["check", str(path)])
            self.assertEqual(status, 2)
            self.assertEqual(result["diagnostics"][0]["code"], "OKL-E-LEXICAL")

    def test_missing_file_returns_io_failure(self):
        status, result = self.invoke(["check", "/no/such/ontokin-file.ok"])
        self.assertEqual(status, 1)
        self.assertEqual(result["outcome"], "io_error")


if __name__ == "__main__":
    unittest.main()
