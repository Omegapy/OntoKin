"""Exercise local-check failure reporting and isolation with real child processes."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import check_local as checks


class LocalChecksTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / "source"
        for name in ("ontokin", "tools", "tests", "docs", "examples/visual"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        (self.root / "ontokin/__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "examples/visual/demo-data.js").write_text("historical bytes\n", encoding="utf-8")
        self.output = self.directory / "evidence"

    def execute(self, steps, *, timeout=10):
        with patch.object(checks, "build_plan", return_value=steps), redirect_stdout(io.StringIO()):
            code = checks.run(self.root, self.output, False, timeout)
        return code, json.loads((self.output / "summary.json").read_text(encoding="utf-8"))

    def command(self, name, program, *, requires=(), reports=()):
        return checks.Step(name, (sys.executable, "-c", program), requires, reports)

    def test_failed_builder_blocks_stale_artifact_validation(self):
        marker = self.directory / "checker-was-run"
        steps = [
            self.command("build", "import sys; print('build failure evidence'); sys.exit(7)"),
            self.command("check", f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
                         requires=("build",)),
            self.command("independent", "print('independent check ran')"),
        ]
        code, summary = self.execute(steps)
        self.assertEqual(code, 1)
        self.assertEqual([s["status"] for s in summary["steps"]], ["failed", "blocked", "passed"])
        self.assertEqual(summary["steps"][0]["returncode"], 7)
        self.assertFalse(marker.exists())
        self.assertIn("build failure evidence", (self.output / "logs/build.log").read_text())
        self.assertIn("build", (self.output / "logs/check.log").read_text())
        self.assertFalse(summary["release_certified"])

    def test_fixed_path_build_only_changes_isolated_copy(self):
        original = self.root / "examples/visual/demo-data.js"
        code, summary = self.execute([self.command(
            "build", "from pathlib import Path; Path('examples/visual/demo-data.js').write_text('fresh output')")])
        self.assertEqual(code, 0)
        self.assertEqual(original.read_text(), "historical bytes\n")
        self.assertEqual((self.output / "workspace/examples/visual/demo-data.js").read_text(), "fresh output")
        self.assertTrue(summary["source_unchanged"])
        self.assertTrue((self.output / "source-before.json").is_file())
        self.assertEqual(summary["source_inventory"]["inventory_sha256"], checks.inventory(self.root)["sha256"])
        self.assertEqual(summary["source_inventory"]["sha256"], checks.file_identity(self.output / "source-before.json")["sha256"])

    def test_pending_report_remains_pending_after_successful_command(self):
        report = self.output / "reports/cases.json"
        evidence = {"summary": {"passed": 19, "pending": 1}, "full_gate_complete": False,
                    "cases": [{"id": "C20", "status": "pending", "pending_reasons": ["External evidence required"]}]}
        raw = json.dumps(evidence)
        step = self.command("conformance", f"from pathlib import Path; Path({str(report)!r}).write_text({raw!r})",
                            reports=(report,))
        code, summary = self.execute([step])
        self.assertEqual(code, 0)
        self.assertEqual(report.read_text(), raw)
        self.assertEqual(summary["pending_external_cases"][0]["id"], "C20")
        recorded = summary["steps"][0]["reports"][0]
        self.assertEqual(recorded["sha256"], checks.file_identity(report)["sha256"])
        self.assertFalse(recorded["outcomes"]["full_gate_complete"])
        self.assertFalse(summary["remote_checks_executed"])
        self.assertFalse(summary["full_product_conformance_certified"])

    def test_missing_executable_is_failure_and_has_durable_report(self):
        step = checks.Step("missing-tool", (str(self.directory / "nonexistent-executable"),))
        code, summary = self.execute([step])
        self.assertEqual(code, 1)
        self.assertEqual(summary["steps"][0]["status"], "unavailable")
        self.assertIsNone(summary["steps"][0]["returncode"])
        self.assertTrue((self.output / "logs/missing-tool.log").read_text())

    def test_success_exit_cannot_hide_missing_or_invalid_report(self):
        missing = self.output / "reports/missing.json"
        invalid = self.output / "reports/invalid.json"
        steps = [self.command("missing", "pass", reports=(missing,)),
                 self.command("invalid", f"from pathlib import Path; Path({str(invalid)!r}).write_text('broken JSON')",
                              reports=(invalid,))]
        code, summary = self.execute(steps)
        self.assertEqual(code, 1)
        self.assertEqual([s["status"] for s in summary["steps"]], ["failed", "failed"])
        self.assertTrue(all(s["returncode"] == 0 for s in summary["steps"]))

    def test_source_change_invalidates_otherwise_successful_run(self):
        target = self.root / "ontokin/__init__.py"
        step = self.command("change", f"from pathlib import Path; Path({str(target)!r}).write_text('VALUE = 2\\n')")
        code, summary = self.execute([step])
        self.assertEqual(code, 1)
        self.assertEqual(summary["steps"][0]["status"], "passed")
        self.assertFalse(summary["source_unchanged"])
        self.assertIn("changed", summary["error"])

    def test_original_generated_inputs_and_new_json_sources_are_inventoried(self):
        manifest = self.root / "examples/visual/scene.files.json"
        manifest.write_text('{"entry": "scene.ok"}', encoding="utf-8")
        files = {item["path"] for item in checks.inventory(self.root)["files"]}
        self.assertIn("examples/visual/scene.files.json", files)
        self.assertIn("examples/visual/demo-data.js", files)
        target = self.root / "examples/visual/demo-data.js"
        code, summary = self.execute([self.command("change-original-render-input",
            f"from pathlib import Path; Path({str(target)!r}).write_text('changed original')")])
        self.assertEqual(code, 1)
        self.assertFalse(summary["source_unchanged"])

    def test_skipped_unittest_is_visible_and_cannot_pass_complete_regression(self):
        (self.root / "tests/test_optional.py").write_text(
            "import unittest\nclass Optional(unittest.TestCase):\n"
            "    @unittest.skip('missing optional validator')\n    def test_optional(self): pass\n", encoding="utf-8")
        step = checks.Step("unit-tests", (sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"))
        code, summary = self.execute([step])
        self.assertEqual(code, 1)
        execution = summary["steps"][0]["test_execution"]
        self.assertEqual(execution["tests_run"], 1)
        self.assertEqual(execution["skipped"], 1)
        self.assertEqual(execution["executed_without_skips"], 0)
        self.assertFalse(execution["complete_regression_passed"])

    def test_timeout_stops_child_and_retains_failure(self):
        marker = self.directory / "late-write"
        step = self.command("timeout", f"import time; from pathlib import Path; time.sleep(2); Path({str(marker)!r}).write_text('late')")
        code, summary = self.execute([step], timeout=0.05)
        self.assertEqual(code, 1)
        self.assertEqual(summary["steps"][0]["status"], "failed")
        self.assertIn("Exceeded", summary["steps"][0]["reason"])
        self.assertFalse(marker.exists())

    def test_output_cannot_replace_existing_evidence_or_enter_source(self):
        self.output.mkdir()
        preserved = self.output / "summary.json"
        preserved.write_text("previous evidence", encoding="utf-8")
        with self.assertRaises(ValueError):
            checks.prepare_output(self.root, self.output)
        with self.assertRaises(ValueError):
            checks.prepare_output(self.root, self.root / "docs/new-evidence")
        self.assertEqual(preserved.read_text(), "previous evidence")

    def test_snapshot_rejects_source_links_outside_the_checkout(self):
        external = self.directory / "external.py"
        external.write_text("external source", encoding="utf-8")
        link = self.root / "ontokin/external.py"
        try:
            link.symlink_to(external)
        except OSError as error:
            self.skipTest(f"Symbolic links are unavailable: {error}")
        code, summary = self.execute([])
        self.assertEqual(code, 1)
        self.assertIn("symbolic link", summary["error"])
        self.assertEqual(external.read_text(), "external source")

    def test_dry_run_writes_nothing_and_does_not_start_checks(self):
        output = io.StringIO()
        with patch.object(checks, "ROOT", self.root), patch.object(checks, "run") as execute, redirect_stdout(output):
            code = checks.main(["--dry-run", "--full", "--output-dir", str(self.output)])
        self.assertEqual(code, 0)
        execute.assert_not_called()
        self.assertFalse(self.output.exists())
        plan = json.loads(output.getvalue())
        self.assertEqual(plan["profile"], "full")
        ids = {s["id"] for s in plan["steps"]}
        self.assertTrue({"unit-tests", "source", "agent", "construction", "surface", "impulse", "documents"} <= ids)
        self.assertIn("impulse-agent-browser", ids)
        self.assertFalse(any("install" in s["argv"] or "ci" in s["argv"] for s in plan["steps"]))


if __name__ == "__main__":
    unittest.main()
