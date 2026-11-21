"""Driver selection refusals and isolated transport, without host qualification."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import check_local as checks


class CurrentHostDriverBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="readback-driver-control-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "source"
        self.root.mkdir()
        self.output = self.root.parent / "evidence"
        self.config = self.root.parent / "selection.json"
        self.original = b'{"scope":"transport fixture, not a qualified host"}\n'
        self.config.write_bytes(self.original)
        self.expected = hashlib.sha256(self.original).hexdigest()

    def run_refusal(self, **selection):
        # Isolate metadata subprocesses from the checker-start counter.
        with patch.object(checks, "prepare_workspace") as copy, \
                patch.object(checks, "git_metadata", return_value={"available": False, "scope": "mocked metadata leaf"}), \
                patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                patch.object(checks.subprocess, "Popen") as child, redirect_stdout(io.StringIO()):
            result = checks.run(self.root, self.output, False, 5, **selection)
        copy.assert_not_called()
        child.assert_not_called()
        report = json.loads((self.output / "summary.json").read_text())
        self.assertEqual(result, 1)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["steps"], [])
        self.assertEqual(report["not_executed_steps"],
                         ["unit-tests", "source", "agent", "construction", "surface", "impulse", "documents"])
        return report

    def test_missing_explicit_selection_cannot_use_ambient_approval(self):
        with patch.dict(os.environ, {checks.READBACK_CONFIG_ENV: str(self.config),
                                     checks.READBACK_DIGEST_ENV: self.expected}):
            report = self.run_refusal()
        self.assertIn("requires --readback-config", report["error"])

    def test_missing_expected_digest_is_a_preparation_failure(self):
        report = self.run_refusal(readback_config=self.config)
        self.assertIn("independently reviewed execution plan", report["readback_selection"]["approval_source"])
        self.assertIn("EXPECTED_DIGEST", report["error"])

    def test_coherently_changed_file_cannot_choose_its_own_expected_digest(self):
        self.config.write_bytes(b'{"scope":"changed but still valid JSON"}\n')
        report = self.run_refusal(readback_config=self.config, readback_config_sha256=self.expected)
        self.assertIn("differs from the independently supplied expected digest", report["error"])
        self.assertEqual(report["readback_selection"]["expected_config_sha256"], self.expected)
        self.assertEqual(report["readback_selection"]["observed_identity"],
                         {"sha256": "sha256:" + hashlib.sha256(self.config.read_bytes()).hexdigest(),
                          "bytes": self.config.stat().st_size})

    def test_relative_configuration_and_malformed_digest_are_rejected(self):
        report = self.run_refusal(readback_config=Path("relative.json"), readback_config_sha256="not-a-digest")
        self.assertIn("absolute configuration path", report["error"])

    def test_list_does_not_read_configuration_or_prepare_runtime(self):
        output = io.StringIO()
        with patch.object(checks, "ROOT", self.root), patch.object(checks, "run") as run, \
                patch.object(checks, "readback_config_identity") as read, \
                patch.object(checks.subprocess, "Popen") as child, redirect_stdout(output):
            result = checks.main(["--list", "--readback-config", "/absent/config.json",
                                  "--readback-config-sha256", "not-a-digest", "--output-dir", str(self.output)])
        self.assertEqual(result, 0)
        run.assert_not_called()
        read.assert_not_called()
        child.assert_not_called()
        self.assertFalse(self.output.exists())
        self.assertEqual(json.loads(output.getvalue())["steps"][0]["argv"][-6:],
                         ["-m", "unittest", "discover", "-s", "tests", "-v"])

    def test_changed_copied_inventory_is_rejected_before_provider_derivation(self):
        with self.assertRaisesRegex(ValueError, "differs from the original checkout"):
            checks.bind_readback_workspace({}, root=self.root, workspace=self.root.parent / "copy",
                                           output=self.output, source_before={"files": ["original"]},
                                           workspace_inventory={"files": ["changed"]})

    def test_configuration_symlink_and_oversize_are_refused(self):
        link = self.root.parent / "linked.json"
        link.symlink_to(self.config)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            checks.readback_config_identity(link)
        self.config.write_bytes(b"x" * 1048577)
        with self.assertRaisesRegex(ValueError, "at most 1 MiB"):
            checks.readback_config_identity(self.config)

    def test_changed_selection_before_unit_launch_starts_no_child(self):
        self.output.mkdir()
        self.config.write_bytes(b"changed after derivation")
        selection = {"config_path": str(self.config), "config_sha256": self.expected}
        with patch.object(checks.subprocess, "Popen") as child:
            result = checks.execute_step(checks.Step("unit-tests", (sys.executable, "-c", "pass")),
                                         self.root, self.output, {}, 5, readback_selection=selection)
        child.assert_not_called()
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["returncode"])
        self.assertFalse(result["process_started"])
        self.assertIsNone(result["process_pid"])
        self.assertIn("changed before the unit process", result["reason"])

    def test_failed_prelaunch_is_recorded_unexecuted_even_if_later_inventory_fails(self):
        # Only failure accounting is under test. Selection/derivation and Git
        # metadata are explicit fixtures; actual source copy and guard execute.
        selection = {"config_path": str(self.config), "config_sha256": self.expected}
        self.config.write_bytes(b"changed after fixture derivation")
        original_inventory = checks.inventory
        for fail_after in (False, True):
            output = self.output.parent / ("evidence-inventory-failure" if fail_after else "evidence-no-start")
            source_reads = 0
            def inventory(path):
                nonlocal source_reads
                if path == self.root:
                    source_reads += 1
                    if fail_after and source_reads == 2:
                        raise OSError("controlled post-run inventory failure")
                return original_inventory(path)
            with self.subTest(fail_after=fail_after), \
                    patch.object(checks, "build_plan", return_value=[checks.Step("unit-tests", (sys.executable, "-c", "pass"))]), \
                    patch.object(checks, "prepare_readback_selection", return_value=selection), \
                    patch.object(checks, "bind_readback_workspace", return_value=selection), \
                    patch.object(checks, "git_metadata", return_value={"available": False, "scope": "mocked metadata leaf"}), \
                    patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                    patch.object(checks, "inventory", side_effect=inventory), \
                    patch.object(checks.subprocess, "Popen") as child, redirect_stdout(io.StringIO()):
                code = checks.run(self.root, output, False, 5)
            child.assert_not_called()
            report = json.loads((output / "summary.json").read_text())
            self.assertEqual(code, 1)
            self.assertEqual(report["not_executed_steps"], ["unit-tests"])
            self.assertFalse(report["steps"][0]["process_started"])
            if fail_after:
                self.assertIn("controlled post-run inventory failure", report["error"])

    def test_explicit_pair_reaches_real_python_child_without_ambient_override(self):
        # Only configuration transport is real here; this file is not a host lock.
        self.output.mkdir()
        selection = {"config_path": str(self.config), "config_sha256": self.expected}
        program = ("import os,unittest\nclass Transport(unittest.TestCase):\n"
                   " def test_pair(self):\n"
                   f"  self.assertEqual(os.environ[{checks.READBACK_CONFIG_ENV!r}], {str(self.config)!r})\n"
                   f"  self.assertEqual(os.environ[{checks.READBACK_DIGEST_ENV!r}], {self.expected!r})\n"
                   "  self.assertNotIn('NODE_OPTIONS', os.environ)\n"
                   "  self.assertNotIn('PYTHONPATH', os.environ)\n"
                   "  self.assertEqual(os.environ['PYTHONNOUSERSITE'], '1')\n"
                   "unittest.main()\n")
        with patch.dict(os.environ, {checks.READBACK_CONFIG_ENV: "/wrong/original-checkout.json",
                                     checks.READBACK_DIGEST_ENV: "0" * 64,
                                     "NODE_OPTIONS": "--unapproved-control-option",
                                     "PYTHONPATH": "/unapproved/control/path"}):
            result = checks.execute_step(checks.Step("unit-tests", (sys.executable, "-B", "-c", program)),
                                         self.root, self.output, {}, 5, readback_selection=selection)
        self.assertEqual(result["status"], "passed", result)
        self.assertTrue(result["process_started"])
        self.assertGreater(result["process_pid"], 0)
        self.assertEqual(result["test_execution"]["tests_run"], 1)
        self.assertEqual(result["environment_overrides"][checks.READBACK_CONFIG_ENV], str(self.config))
        self.assertEqual(result["environment_overrides"][checks.READBACK_DIGEST_ENV], self.expected)


if __name__ == "__main__":
    unittest.main()
