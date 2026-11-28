"""Exercise local-check failure reporting and isolation with real child processes."""
from contextlib import nullcontext, redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
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

    def execute(self, steps, *, timeout=10, force_agent=False):
        # These synthetic repositories exercise the generic driver, not readback.
        # Bind the new provider seam explicitly while retaining real test children.
        selection = self.directory / "mocked-readback-selection.json"
        binding = None
        if any(step.id == "unit-tests" for step in steps):
            selection.write_text('{"scope": "mocked driver-test preparation boundary"}\n')
            binding = {"config_path": str(selection),
                       "config_sha256": checks.file_identity(selection)["sha256"].removeprefix("sha256:")}
        preparation = (patch.object(checks, "prepare_readback_selection", return_value=binding)
                       if binding else nullcontext())
        derivation = (patch.object(checks, "bind_readback_workspace", return_value=binding)
                      if binding else nullcontext())
        with patch.object(checks, "build_plan", return_value=steps), preparation, derivation, redirect_stdout(io.StringIO()):
            code = checks.run(self.root, self.output, False, timeout, force_agent=force_agent)
        return code, json.loads((self.output / "summary.json").read_text(encoding="utf-8"))

    def command(self, name, program, *, requires=(), reports=()):
        return checks.Step(name, (sys.executable, "-c", program), requires, reports)

    def initialize_git(self, root, paths=(".",)):
        checks.git_read(root, "init", "--quiet", "--template=")
        checks.git_read(root, "add", "--", *paths)
        checks.git_read(root, "-c", "user.name=Local check fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--quiet", "-m", "Source fixture")
        return checks.git_metadata(root)

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

    def test_external_workspace_retains_real_git_revision_and_copied_changes_with_own_index(self):
        original = self.initialize_git(self.root)
        checks.git_read(self.root, "config", "remote.origin.url", "https://example.invalid/source-only")
        checks.git_read(self.root, "config", "credential.helper", "source-only-helper")
        changed = self.root / "ontokin/__init__.py"
        changed.write_text("VALUE = 2\n", encoding="utf-8")
        checks.git_read(self.root, "add", "ontokin/__init__.py")
        changed.write_text("VALUE = 3\n", encoding="utf-8")
        (self.root / "docs/untracked.txt").write_text("new source evidence\n", encoding="utf-8")
        source_index = self.root / ".git/index"
        before = (source_index.read_bytes(), source_index.stat().st_mtime_ns)
        code, summary = self.execute([self.command("git-provenance", "import subprocess; subprocess.run(['git', 'rev-parse', 'HEAD'], check=True)")])
        workspace = self.output / "workspace"
        self.assertEqual(code, 0)
        for name in ("git", "workspace_git", "git_after"):
            self.assertEqual(summary[name]["local_head"], original["local_head"])
            self.assertEqual(summary[name]["local_tree"], original["local_tree"])
        self.assertEqual(summary["workspace_git"]["index_basis"], "source_commit_tree")
        self.assertIn(" M ontokin/__init__.py", checks.git_read(workspace, "status", "--porcelain"))
        self.assertIn("docs/untracked.txt", summary["workspace_git"]["untracked_source_files"])
        self.assertEqual((workspace / "ontokin/__init__.py").read_bytes(), changed.read_bytes())
        self.assertEqual((workspace / "docs/untracked.txt").read_text(), "new source evidence\n")
        self.assertEqual((source_index.read_bytes(), source_index.stat().st_mtime_ns), before)
        self.assertFalse(source_index.samefile(workspace / ".git/index"))
        self.assertFalse((workspace / ".git/objects/info/alternates").exists())
        self.assertNotIn("source-only", (workspace / ".git/config").read_text())
        self.assertEqual(checks.git_read(workspace, "rev-parse", "--show-toplevel"), str(workspace))
        self.assertTrue(summary["git_revision_unchanged"])

    def test_no_git_source_cannot_inherit_an_unrelated_parent_revision(self):
        (self.directory / "parent.txt").write_text("unrelated repository\n", encoding="utf-8")
        self.initialize_git(self.directory, ("parent.txt",))
        step = self.command("no-parent-git", "import subprocess; result=subprocess.run(['git','rev-parse','HEAD'], capture_output=True); assert result.returncode != 0")
        code, summary = self.execute([step])
        self.assertEqual(code, 0)
        self.assertFalse(summary["git"]["available"])
        self.assertFalse(summary["workspace_git"]["available"])
        self.assertNotIn("local_head", summary["workspace_git"])
        self.assertFalse((self.output / "workspace/.git").exists())

    def test_future_lfs_attributes_without_payloads_need_no_lfs_client(self):
        attributes = self.root / ".gitattributes"
        attributes.write_text("docs/engineering/lfs-archives/**/*.zip filter=lfs diff=lfs merge=lfs -text\n")
        self.initialize_git(self.root)
        with patch("tools.storage_identity.shutil.which", return_value=None):
            code, summary = self.execute([])
        self.assertEqual(code, 0, summary)
        self.assertEqual((self.output / "workspace/.gitattributes").read_bytes(), attributes.read_bytes())
        self.assertEqual(summary["workspace_storage"]["lfs_files"], [])
        self.assertNotIn("client", summary["workspace_storage"])
        self.assertEqual(summary["workspace_git"]["tracked_worktree_status"], "")
        self.assertTrue(summary["source_unchanged"])

    def test_workspace_git_copy_failure_is_explicit_and_does_not_start_checks(self):
        self.initialize_git(self.root)
        read = checks.git_read
        def fail_local_fetch(root, *args, **kwargs):
            if root == self.output / "workspace" and "fetch" in args:
                raise subprocess.CalledProcessError(128, ["git", "fetch"], stderr="missing local object")
            return read(root, *args, **kwargs)
        with patch.object(checks, "git_read", side_effect=fail_local_fetch):
            code, summary = self.execute([self.command("unexpected", "raise RuntimeError('must not run')")])
        self.assertEqual(code, 1)
        self.assertEqual(summary["steps"], [])
        self.assertIn("Cannot retain exact source Git metadata", summary["error"])

    def test_source_head_movement_invalidates_unchanged_file_bytes(self):
        original = self.initialize_git(self.root)
        step = checks.Step("advance-head", ("git", "-C", str(self.root), "-c", "user.name=Local check fixture",
            "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "--allow-empty", "-m", "Concurrent head movement"))
        code, summary = self.execute([step])
        self.assertEqual(code, 1)
        self.assertEqual(summary["steps"][0]["status"], "passed")
        self.assertEqual(summary["git_after"]["local_tree"], original["local_tree"])
        self.assertNotEqual(summary["git_after"]["local_head"], original["local_head"])
        self.assertFalse(summary["git_revision_unchanged"])
        self.assertFalse(summary["source_unchanged"])

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

    def test_packaging_sources_and_license_notices_survive_workspace_isolation(self):
        paths = ("packaging/installed/ontokin/__init__.py", "LICENSE", "LICENSE-CODE", "LICENSE-DOCS")
        for name in paths:
            source = self.root / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(name + "\n", encoding="utf-8")
        self.initialize_git(self.root)
        code, summary = self.execute([])
        self.assertEqual(code, 0, summary)
        recorded = {item["path"] for item in checks.inventory(self.root)["files"]}
        self.assertTrue(set(paths) <= recorded, set(paths) - recorded)
        self.assertEqual(summary["workspace_git"]["tracked_worktree_status"], "")
        for name in paths:
            self.assertEqual((self.output / "workspace" / name).read_bytes(), (self.root / name).read_bytes())

    def test_declared_validation_input_roots_survive_inventory_and_copy(self):
        directories = ("ontokin", "tests", "tools", "docs", "examples", "schemas", "prototypes",
                       "packaging", ".github", "fixtures", ".agents", "TRDs")
        paths = [name + "/input.bin" for name in directories]
        paths += ["pyproject.toml", "README.md", "AGENTS.md", "GOAL.md", "STATUS.md", "CHATGPT-START-HERE.md", "ROLE.md",
                  "LOCAL-START-HERE.md", "CLAUDE.md", "LICENSE", "LICENSE-CODE", "LICENSE-DOCS", "LICENSING.md", "NOTICE",
                  ".gitignore", ".gitattributes", ".lfsconfig"]
        for name in paths:
            source = self.root / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"# input for " + name.encode("utf-8") + b"\n")
        self.initialize_git(self.root)
        code, summary = self.execute([])
        self.assertEqual(code, 0, summary)
        before = json.loads((self.output / "source-before.json").read_text())
        recorded = {item["path"] for item in before["files"]}
        self.assertTrue(set(paths) <= recorded, set(paths) - recorded)
        self.assertEqual(checks.inventory(self.output / "workspace"), before)
        self.assertEqual(summary["workspace_git"]["tracked_worktree_status"], "")
        for name in paths:
            self.assertEqual((self.output / "workspace" / name).read_bytes(), (self.root / name).read_bytes())

    def test_workflow_instruction_targets_survive_workspace_isolation(self):
        paths = ("CHATGPT-START-HERE.md", "ROLE.md",
                 ".agents/skills/ontokin-session/SKILL.md",
                 ".agents/skills/ontokin-delivery/SKILL.md",
                 ".agents/skills/ontokin-learning/SKILL.md")
        for name in paths:
            source = self.root / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"# Required workflow instruction: " + name.encode("utf-8") + b"\n")
        original = self.initialize_git(self.root)
        excluded = (".agents/.env", ".agents/.env.local", ".agents/.cache/session.tmp",
                    ".agents/node_modules/package/index.js", ".agents/.venv/installed.py",
                    ".agents/__pycache__/module.pyc", "temporary-worker/notes.txt")
        for name in excluded:
            source = self.root / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"Unrelated local fixture; must stay outside the copied inputs.\n")
        source_index = self.root / ".git/index"
        before_index = (source_index.read_bytes(), source_index.stat().st_mtime_ns)
        code, summary = self.execute([])
        self.assertEqual(code, 0, summary)
        workspace = self.output / "workspace"
        before = json.loads((self.output / "source-before.json").read_text())
        recorded = {item["path"] for item in before["files"]}
        self.assertTrue(set(paths) <= recorded, set(paths) - recorded)
        self.assertEqual(checks.inventory(workspace), before)
        for name in paths:
            self.assertEqual((workspace / name).read_bytes(), (self.root / name).read_bytes())
        for name in excluded:
            self.assertNotIn(name, recorded)
            self.assertFalse((workspace / name).exists(), name)
        self.assertEqual(summary["workspace_git"]["tracked_worktree_status"], "")
        for name in ("git", "workspace_git", "git_after"):
            self.assertEqual(summary[name]["local_head"], original["local_head"])
            self.assertEqual(summary[name]["local_tree"], original["local_tree"])
        self.assertFalse(source_index.samefile(workspace / ".git/index"))
        checks.git_read(workspace, "update-index", "--assume-unchanged", "ROLE.md")
        self.assertNotEqual((workspace / ".git/index").read_bytes(), before_index[0])
        self.assertEqual((source_index.read_bytes(), source_index.stat().st_mtime_ns), before_index)
        self.assertEqual(checks.git_read(workspace, "rev-parse", "HEAD"), original["local_head"])
        self.assertTrue(summary["source_unchanged"])

    def test_instruction_files_and_adopted_requirements_reach_the_isolated_workspace(self):
        paths = ("CHATGPT-START-HERE.md", "LOCAL-START-HERE.md", "CLAUDE.md", "ROLE.md", "LICENSING.md", "NOTICE", "TRDs/INDEX.md",
                 "TRDs/trd_example.md", ".agents/skills/ontokin-session/SKILL.md", ".agents/skills/to-trd/scripts/trd.py",
                 "tools/local-environment.json", "tools/example.lock")
        excluded = (".agents/.env", ".agents/.venv/installed.py", ".agents/skills/to-trd/__pycache__/trd.pyc", ".claude/settings.local.json",
                    "Implementation_Plans/INDEX.md", "notes.txt")
        for name in (*paths, *excluded):
            source = self.root / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"Content of " + name.encode("utf-8") + b"\n")
        self.initialize_git(self.root, paths)
        code, summary = self.execute([])
        self.assertEqual(code, 0, summary)
        workspace = self.output / "workspace"
        before = json.loads((self.output / "source-before.json").read_text())
        recorded = {item["path"] for item in before["files"]}
        self.assertTrue(set(paths) <= recorded, set(paths) - recorded)
        self.assertEqual(checks.inventory(workspace), before)
        for name in paths:
            self.assertEqual((workspace / name).read_bytes(), (self.root / name).read_bytes())
        for name in excluded:
            self.assertNotIn(name, recorded)
            self.assertFalse((workspace / name).exists(), name)

    def test_declared_instruction_inputs_exist_in_this_repository(self):
        optional = {".lfsconfig"}
        self.assertEqual([name for name in checks.ROOT_FILES if name not in optional and not (checks.ROOT / name).is_file()], [])
        for name in (".agents", "TRDs"):
            self.assertIn(name, checks.SOURCE_DIRS)
            self.assertTrue((checks.ROOT / name).is_dir())

    def test_top_level_fixture_can_be_read_by_isolated_child(self):
        fixture = self.root / "fixtures/static_tray_v01/native/Q01/ontokin/source.json"
        fixture.parent.mkdir(parents=True)
        fixture.write_text('{"case": "Q01", "source": "main.ok"}\n', encoding="utf-8")
        program = ("import json; from pathlib import Path; "
                   "data=json.loads(Path('fixtures/static_tray_v01/native/Q01/ontokin/source.json').read_text()); "
                   "assert data == {'case': 'Q01', 'source': 'main.ok'}")
        code, summary = self.execute([self.command("read-top-level-fixture", program)])
        self.assertEqual(code, 0, summary)
        self.assertTrue(summary["source_unchanged"])
        recorded = {item["path"] for item in json.loads((self.output / "source-before.json").read_text())["files"]}
        self.assertIn(fixture.relative_to(self.root).as_posix(), recorded)

    def test_fixture_mutation_invalidates_source_or_workspace_stability(self):
        name = "fixtures/static_tray_v01/input.json"
        fixture = self.root / name
        fixture.parent.mkdir(parents=True)
        for location in ("source", "workspace"):
            with self.subTest(location=location):
                fixture.write_text('{"original": true}\n', encoding="utf-8")
                self.output = self.directory / ("evidence-" + location)
                target = fixture if location == "source" else self.output / "workspace" / name
                code, summary = self.execute([self.command("mutate-fixture",
                    f"from pathlib import Path; Path({str(target)!r}).write_text('changed fixture')")])
                self.assertEqual(code, 1, summary)
                self.assertEqual(summary["steps"][0]["status"], "passed")
                self.assertFalse(summary["source_unchanged"])
                self.assertIn("changed", summary["error"])

    def test_fixture_symlink_is_rejected_by_existing_source_guard(self):
        external = self.directory / "external.json"
        external.write_text('{"external": true}\n', encoding="utf-8")
        fixtures = self.root / "fixtures"
        fixtures.mkdir()
        try:
            (fixtures / "linked.json").symlink_to(external)
        except OSError as error:
            self.skipTest(f"Symbolic links are unavailable: {error}")
        code, summary = self.execute([])
        self.assertEqual(code, 1, summary)
        self.assertIn("symbolic link", summary["error"])
        self.assertEqual(external.read_text(), '{"external": true}\n')

    def test_parent_only_no_bytecode_flag_does_not_protect_child_imports(self):
        environment = dict(os.environ)
        for name in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX"):
            environment.pop(name, None)
        program = ("import subprocess,sys; assert sys.dont_write_bytecode; "
                   "subprocess.run([sys.executable,'-c','import ontokin'],check=True)")
        subprocess.run([sys.executable, "-B", "-c", program], cwd=self.root, env=environment,
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertTrue(list((self.root / "ontokin/__pycache__").glob("*.pyc")))

    def test_planned_python_commands_explicitly_disable_bytecode(self):
        for full, force_agent in ((False, False), (True, False), (False, True), (True, True)):
            with self.subTest(full=full, force_agent=force_agent):
                steps = checks.build_plan(self.root, self.output, full, "selected-python", force_agent=force_agent)
                python_steps = [step for step in steps if step.argv[0] == "selected-python"]
                self.assertTrue(python_steps)
                self.assertTrue(all(step.argv[1] == "-B" for step in python_steps), python_steps)

    def test_planned_bytecode_flag_works_when_python_environment_is_ignored(self):
        (self.root / "tests/test_bytecode.py").write_text(
            "import sys,unittest\nimport ontokin\nclass Bytecode(unittest.TestCase):\n"
            "    def test_disabled(self): self.assertTrue(sys.dont_write_bytecode)\n", encoding="utf-8")
        selected = next(step for step in checks.build_plan(self.root, self.output, False) if step.id == "unit-tests")
        step = checks.Step(selected.id, (selected.argv[0], "-E", *selected.argv[1:]))
        code, summary = self.execute([step])
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["steps"][0]["test_execution"]["tests_run"], 1)
        self.assertFalse(list((self.output / "workspace").rglob("*.pyc")))

    def test_step_environment_prevents_child_and_grandchild_bytecode(self):
        child = "import sys,ontokin; assert sys.dont_write_bytecode"
        program = ("import subprocess,sys,ontokin; assert sys.dont_write_bytecode; "
                   f"subprocess.run([sys.executable,'-c',{child!r}],check=True)")
        with patch.dict(os.environ, {"PYTHONDONTWRITEBYTECODE": ""}):
            code, summary = self.execute([self.command("nested-python", program)])
        self.assertEqual(code, 0, summary)
        self.assertFalse(list((self.output / "workspace").rglob("*.pyc")))
        self.assertTrue(summary["source_unchanged"])

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

    def test_force_agent_preflight_reports_missing_and_mismatched_pins(self):
        requirements = self.root / "tools/force-agent-verification-requirements.txt"
        requirements.write_text("# verification only\njsonschema==4.26.0\n", encoding="utf-8")
        for installed in (None, "0.0.0"):
            with self.subTest(installed=installed):
                report = self.output / f"preflight-{installed}.json"
                error = checks.metadata.PackageNotFoundError("jsonschema") if installed is None else None
                captured = io.StringIO()
                with patch.object(checks.metadata, "version", return_value=installed, side_effect=error), redirect_stderr(captured):
                    code = checks.force_agent_preflight(requirements, report)
                result = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual(code, 1)
                self.assertEqual(result["status"], "failed")
                self.assertEqual(result["dependencies"], [{"name": "jsonschema", "expected": "4.26.0", "installed": installed}])
                self.assertEqual(result["requirements_identity"], checks.file_identity(requirements))
                self.assertIn("expected 4.26.0", captured.getvalue())

    def test_force_agent_preflight_failure_blocks_its_tests_builder_and_audit(self):
        (self.root / "tools/check_local.py").write_bytes(Path(checks.__file__).read_bytes())
        (self.root / "tools/storage_identity.py").write_bytes(
            Path(checks.__file__).with_name("storage_identity.py").read_bytes())
        (self.root / "tools/force-agent-verification-requirements.txt").write_text(
            "ontokin-local-checks-unavailable-test-package==0.0.0\n", encoding="utf-8")
        marker = self.directory / "force-command-was-run"
        for script in ("build_force_agent_demo.py", "verify_force_agent_workflow.py"):
            (self.root / "tools" / script).write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n", encoding="utf-8")
        steps = [s for s in checks.build_plan(self.root, self.output, False, force_agent=True)
                 if s.id.startswith("force-agent-")]
        code, summary = self.execute(steps, force_agent=True)
        self.assertEqual(code, 1)
        self.assertEqual([s["status"] for s in summary["steps"]], ["failed", "blocked", "blocked", "blocked"])
        self.assertEqual(summary["selected_roles"], ["core", "force-agent"])
        self.assertFalse(marker.exists())
        self.assertEqual(summary["not_executed_steps"], ["force-agent-tests", "force-agent-build", "force-agent-audit"])
        preflight = json.loads((self.output / "reports/force-agent-tools.json").read_text())
        self.assertIsNone(preflight["dependencies"][0]["installed"])
        self.assertEqual(summary["steps"][0]["reports"][0]["outcomes"]["status"], "failed")

    def test_force_agent_cohort_enforces_execution_without_skips_or_expected_failures(self):
        cases = {
            "skipped": "import unittest\nclass Probe(unittest.TestCase):\n"
                       "    @unittest.skip('missing verifier')\n    def test_probe(self): pass\n",
            "expected_failure": "import unittest\nclass Probe(unittest.TestCase):\n"
                                "    @unittest.expectedFailure\n    def test_probe(self): self.fail('expected')\n",
            "empty": "# No selected test cases.\n",
            "passed": "import unittest\nclass Probe(unittest.TestCase):\n    def test_probe(self): pass\n",
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self.output = self.directory / ("evidence-" + name)
                (self.root / "tests/test_force_agent_probe.py").write_text(source, encoding="utf-8")
                selected = next(s for s in checks.build_plan(self.root, self.output, False, force_agent=True)
                                if s.id == "force-agent-tests")
                marker = self.directory / ("built-" + name)
                steps = [checks.Step(selected.id, selected.argv),
                         self.command("force-agent-build", f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
                                      requires=(selected.id,))]
                code, summary = self.execute(steps, force_agent=True)
                passed = name == "passed"
                self.assertEqual(code, 0 if passed else 1)
                execution = summary["steps"][0]["test_execution"]
                self.assertEqual(execution["tests_run"], 0 if name == "empty" else 1)
                self.assertEqual(execution["complete_cohort_passed"], passed)
                self.assertNotIn("complete_regression_passed", execution)
                self.assertEqual(summary["steps"][1]["status"], "passed" if passed else "blocked")
                self.assertEqual(marker.exists(), passed)

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

    def test_force_agent_plan_is_explicit_and_combines_with_existing_full_role(self):
        original = checks.build_plan(self.root, self.output, False, "selected-python")
        self.assertEqual([s.id for s in original], ["unit-tests", "source", "agent", "construction", "surface", "impulse", "documents"])
        self.assertTrue(all(s.argv[0] == "selected-python" for s in original))
        output = io.StringIO()
        with patch.object(checks, "ROOT", self.root), patch.object(checks, "run") as execute, redirect_stdout(output):
            code = checks.main(["--list", "--full", "--force-agent", "--output-dir", str(self.output)])
        self.assertEqual(code, 0)
        execute.assert_not_called()
        self.assertFalse(self.output.exists())
        plan = json.loads(output.getvalue())
        self.assertEqual(plan["profile"], "full")
        self.assertEqual(plan["selected_roles"], ["core", "visual", "force-agent"])
        steps = {s["id"]: s for s in plan["steps"]}
        self.assertIn("impulse-agent-browser", steps)
        self.assertEqual(steps["force-agent-tests"]["requires"], ["force-agent-tools"])
        self.assertEqual(steps["force-agent-build"]["requires"], ["force-agent-tests"])
        self.assertEqual(steps["force-agent-audit"]["requires"], ["force-agent-build", "force-agent-tools"])
        self.assertIn(str(self.output / "artifacts/force-agent-workflow"), steps["force-agent-build"]["argv"])
        self.assertFalse(any("install" in s["argv"] or "ci" in s["argv"] for s in plan["steps"]))


class CopiedSetAndWorkspaceIndexTests(unittest.TestCase):
    """C271-P37 DECISION-001 in the driver (author W1): the copied set's one definition, and the workspace
    index's stat data (FZ-02). Starts real Git in temporary fixture repositories, through the PATH Git
    resolved once; the repositories track two paths outside the copied set, a symbolic link among them."""

    UNCOPIED = (".claude/.gitignore", ".claude/skills/alpha")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(os.path.realpath(temporary.name))
        self.root = self.directory / "source"
        isolated = patch.object(checks, "_GIT_STATE", None)
        isolated.start()
        self.addCleanup(isolated.stop)
        self.outputs = 0

    def fresh_output(self):
        self.outputs += 1
        output = self.directory / ("evidence-%d" % self.outputs)
        output.mkdir()
        return output

    def write(self, name, data, *, old=None):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if old is not None:
            os.utime(path, (old, old))
        return path

    def repository(self):
        """A committed source whose files carry old modification times, so that no index entry is racy."""
        old = time.time() - 120
        for name in ("ontokin/__init__.py", "tests/test_fixture.py", "docs/a.md", "docs/b.md", "docs/c.md", "docs/d.md",
                     "docs/e.md", ".agents/skills/alpha/SKILL.md", "README.md", ".claude/.gitignore"):
            self.write(name, b"fixture bytes of " + name.encode() + b"\n", old=old)
        (self.root / ".claude/skills").mkdir(parents=True)
        (self.root / ".claude/skills/alpha").symlink_to("../../.agents/skills/alpha")
        checks.git_read(self.root, "init", "--quiet", "--template=")
        checks.git_read(self.root, "add", "-A")
        checks.git_read(self.root, "-c", "user.name=Local check fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "--quiet", "-m", "Copied-set fixture")
        return checks.git_metadata(self.root)

    def tracked(self, root):
        return [name for name in checks.git_read(root, "ls-files", "-z").split("\0") if name]

    def unstat(self, root):
        """Entries whose stat data does not match, without any content check (diff-files never refreshes)."""
        return [name for name in checks.git_read(root, "diff-files", "--name-only", "-z").split("\0") if name]

    def test_copied_source_path_is_the_scope_of_the_copy_and_of_the_inventory(self):
        """Starts no process."""
        inside = ("ontokin/__init__.py", "tests/test_fixture.py", "tools/fixture.py", "docs/notes/a.md", ".agents/skills/a/SKILL.md",
                  "TRDs/INDEX.md", ".github/workflows/check.yml", "README.md", "pyproject.toml", ".gitignore", "LICENSE")
        outside = (".claude/.gitignore", ".claude/skills/alpha/SKILL.md", "outside/notes.txt", "Makefile", "tools/build/out.py",
                   "docs/_build/page.html", "tests/__pycache__/fixture.cpython-312.pyc", "ontokin/.env", "ontokin/.env.local",
                   "tools/node_modules/package/index.js", "examples/stale.pyc", "TRDs/dist/archive.txt")
        for name in (*inside, *outside):
            self.write(name, b"scope fixture\n")
        self.assertEqual([name for name in inside if not checks.copied_source_path(name)], [])
        self.assertEqual([name for name in outside if checks.copied_source_path(name)], [])
        recorded = {item["path"] for item in checks.inventory(self.root)["files"]}
        self.assertEqual(recorded, set(inside))
        workspace = checks.prepare_workspace(self.root, self.fresh_output(), False,
                                             source_git={"available": False, "reason": "no Git in this fixture"})
        copied = {path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()}
        self.assertEqual(copied, set(inside))
        for name, expected in (("tests", True), ("README.md", True), ("docs/README.md", True), ("Tests/x.py", False),
                               ("readme.md", False), ("tools/Build/x.py", True), (".claude", False)):
            with self.subTest(name=name):
                self.assertIs(checks.copied_source_path(name), expected)

    def test_untracked_source_record_lists_exactly_the_copied_set_names(self):
        """The summary's untracked_source_files is the same definition as before, now named once."""
        self.repository()
        untracked = (".agents/new.md", ".claude/new.txt", "Makefile", "README-new.txt", "docs/new.md", "outside/new.txt",
                     "tools/build/new.py", "tools/new.py")
        for name in untracked:
            self.write(name, b"untracked fixture\n")
        metadata = checks.git_metadata(self.root)
        self.assertEqual(metadata["untracked_source_files"], [".agents/new.md", "docs/new.md", "tools/new.py"])
        self.assertEqual(metadata["untracked_source_files"], [name for name in sorted(untracked) if checks.copied_source_path(name)])

    def test_workspace_index_records_stat_data_once_and_status_reports_the_same_lines(self):
        """FZ-02: one update-index -q --refresh in the workspace; afterwards only the uncopied paths lack stat
        data, while the entries, the status lines and the summary's workspace_git values stay as without it."""
        original = self.repository()
        reads, real = [], checks.git_read

        def recording(root, *args, **kwargs):
            reads.append((root, args, kwargs.get("timeout")))
            return real(root, *args, **kwargs)
        with patch.object(checks, "git_read", side_effect=recording):
            workspace = checks.prepare_workspace(self.root, self.fresh_output(), False, source_git=original)
        refreshes = [read for read in reads if "update-index" in read[1]]
        self.assertEqual(refreshes, [(workspace, ("update-index", "-q", "--refresh"), 120)])
        self.assertEqual(reads[-1], refreshes[0], "the refresh is the preparation's last Git start")
        self.assertEqual(self.unstat(workspace), list(self.UNCOPIED))
        with patch.object(checks, "refresh_workspace_index") as disabled:
            unrefreshed = checks.prepare_workspace(self.root, self.fresh_output(), False, source_git=original)
        disabled.assert_called_once_with(unrefreshed)
        self.assertEqual(set(self.unstat(unrefreshed)), set(self.tracked(self.root)))
        self.assertEqual(checks.git_read(workspace, "ls-files", "--stage", "-z"),
                         checks.git_read(unrefreshed, "ls-files", "--stage", "-z"))
        refreshed, plain = checks.git_metadata(workspace), checks.git_metadata(unrefreshed)
        self.assertEqual(refreshed, plain)
        self.assertEqual(refreshed["tracked_worktree_status"], "\n".join(" D " + name for name in self.UNCOPIED))
        self.assertEqual((refreshed["local_head"], refreshed["local_tree"]), (original["local_head"], original["local_tree"]))

    def test_refreshed_index_still_reports_every_change_of_a_copied_file(self):
        """The refresh records stat data only for unchanged copies; later changes, a same-size change with the old
        modification time among them, and a change copied from the source all stay visible."""
        original = self.repository()
        (self.root / "docs/e.md").write_bytes(b"changed in the source before the copy\n")
        workspace = checks.prepare_workspace(self.root, self.fresh_output(), False, source_git=original)
        self.assertIn(" M docs/e.md", checks.git_metadata(workspace)["tracked_worktree_status"].splitlines())
        (workspace / "docs/a.md").write_bytes(b"appended\n" * 3)
        before = (workspace / "docs/b.md").stat()
        # A later second than the copy's change time, for a Git that compares whole seconds of ctime.
        time.sleep(1.1)
        (workspace / "docs/b.md").write_bytes(b"x" * before.st_size)
        os.utime(workspace / "docs/b.md", ns=(before.st_atime_ns, before.st_mtime_ns))
        (workspace / "docs/c.md").unlink()
        (workspace / "docs/d.md").unlink()
        (workspace / "docs/d.md").symlink_to("a.md")
        self.assertEqual(checks.git_metadata(workspace)["tracked_worktree_status"].splitlines(),
                         [" D .claude/.gitignore", " D .claude/skills/alpha", " M docs/a.md", " M docs/b.md", " D docs/c.md",
                          " T docs/d.md", " M docs/e.md"])

    def test_failed_index_refresh_fails_the_run_before_any_step(self):
        self.repository()
        output, real = self.directory / "evidence-refresh-failure", checks.git_read

        def fail_refresh(root, *args, **kwargs):
            if root == output / "workspace" and "update-index" in args:
                raise subprocess.CalledProcessError(128, ["git", "update-index"], stderr="index.lock exists")
            return real(root, *args, **kwargs)
        step = checks.Step("unexpected", (sys.executable, "-c", "raise RuntimeError('must not run')"))
        with patch.object(checks, "git_read", side_effect=fail_refresh), patch.object(checks, "build_plan", return_value=[step]), \
                redirect_stdout(io.StringIO()):
            code = checks.run(self.root, output, False, 30)
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 1)
        self.assertEqual(summary["steps"], [])
        self.assertIn("Cannot record the isolated workspace's index stat data", summary["error"])
        self.assertEqual(summary["not_executed_steps"], ["unexpected"])

    def test_ordinary_run_records_the_uncopied_tracked_paths_with_unchanged_fields(self):
        """An ordinary run of a source that tracks paths outside the copied set: the outcome and workspace_git
        carry the fields and values that main's baseline summaries record for its seven .claude/ entries."""
        original = self.repository()
        output = self.directory / "evidence-ordinary"
        with patch.object(checks, "build_plan", return_value=[]), redirect_stdout(io.StringIO()):
            code = checks.run(self.root, output, False, 30)
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["readback_selection"], {"status": "absent", "run_kind": "ordinary"})
        self.assertTrue(summary["source_unchanged"])
        workspace_git = summary["workspace_git"]
        self.assertEqual(set(workspace_git), {"available", "local_head", "local_tree", "tracked_worktree_status",
                                              "untracked_source_files", "head_is_base_revision",
                                              "source_inventory_includes_untracked_files", "remote_head_verified",
                                              "index_basis", "copied_worktree_changes_preserved", "source_staging_preserved"})
        self.assertEqual(workspace_git["tracked_worktree_status"], " D .claude/.gitignore\n D .claude/skills/alpha")
        self.assertEqual(workspace_git["untracked_source_files"], [])
        self.assertEqual((workspace_git["local_head"], workspace_git["local_tree"]), (original["local_head"], original["local_tree"]))
        self.assertEqual((workspace_git["index_basis"], workspace_git["copied_worktree_changes_preserved"],
                          workspace_git["source_staging_preserved"]), ("source_commit_tree", True, False))
        self.assertEqual(summary["git"]["tracked_worktree_status"], "")


if __name__ == "__main__":
    unittest.main()
