"""Driver selection rule (S8), unit environment and Git binding (S9), without host qualification.

C271-P33, decision D-18: W4 wrote these tests in tests/test_current_host_readback_driver.py. That file
stays byte-identical, because P29's frozen controls authenticate it as an inherited companion. This
module holds W4's tests unchanged: its S8 versions of two tests of that file, which keep their names
in a class of the same name, and its new classes.
"""
from contextlib import ExitStack, redirect_stdout
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import check_local as checks
from tools import storage_identity as storage

FACADE = "prototypes.static_tray_v01.current_host_readback_v01"
ORDINARY_REASON = "No approved current-host readback selection: ordinary run, not a qualification"
UNIT_DISCOVERY = (sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v")
# A synthetic unit module for an ordinary run; the test prefixes NAMES, OBSERVED and REASON.
ORDINARY_PROBE = '''
import json, os, unittest
from pathlib import Path


class SelectionProbe(unittest.TestCase):
    def test_unit_process_receives_no_selection(self):
        Path(OBSERVED).write_text(json.dumps({name: os.environ.get(name) for name in NAMES}))
        for name in NAMES:
            self.assertNotIn(name, os.environ)


class ReadbackSetupStandIn(unittest.TestCase):
    """Stands in for ReadbackCPUControls, whose setUpClass refuses an ordinary run."""

    @classmethod
    def setUpClass(cls):
        raise RuntimeError(REASON)

    def test_q01(self):
        pass

    def test_q03(self):
        pass

    def test_changed_reference(self):
        pass
'''


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

    def test_missing_explicit_selection_cannot_use_ambient_approval(self):
        # S8: without the explicit pair the run is ordinary and proceeds; an ambient pair
        # never reaches its unit process. Starts one real synthetic Python unittest child.
        observed = self.root.parent / "unit-selection.json"
        program = ("import json,os,unittest\nfrom pathlib import Path\nclass Ambient(unittest.TestCase):\n"
                   " def test_no_selection(self):\n"
                   f"  names = ({checks.READBACK_CONFIG_ENV!r}, {checks.READBACK_DIGEST_ENV!r})\n"
                   f"  Path({str(observed)!r}).write_text(json.dumps([os.environ.get(name) for name in names]))\n"
                   "unittest.main()\n")
        step = checks.Step("unit-tests", (sys.executable, "-B", "-c", program))
        with patch.dict(os.environ, {checks.READBACK_CONFIG_ENV: str(self.config),
                                     checks.READBACK_DIGEST_ENV: self.expected}), \
                patch.object(checks, "build_plan", return_value=[step]), \
                patch.object(checks, "prepare_readback_selection") as prepare, \
                patch.object(checks, "git_metadata", return_value={"available": False, "scope": "mocked metadata leaf"}), \
                patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                redirect_stdout(io.StringIO()):
            result = checks.run(self.root, self.output, False, 30)
        report = json.loads((self.output / "summary.json").read_text())
        prepare.assert_not_called()
        self.assertEqual(result, 0, report)
        self.assertEqual(report["readback_selection"], {"status": "absent", "run_kind": "ordinary"})
        self.assertEqual(json.loads(observed.read_text()), [None, None])
        self.assertEqual(report["steps"][0]["environment_overrides"], {"PYTHONDONTWRITEBYTECODE": "1"})

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
                # S8: only the caller's explicit pair makes a qualifying run that prepares a selection.
                code = checks.run(self.root, output, False, 5, readback_config=self.config,
                                  readback_config_sha256=self.expected)
            child.assert_not_called()
            report = json.loads((output / "summary.json").read_text())
            self.assertEqual(code, 1)
            self.assertEqual(report["not_executed_steps"], ["unit-tests"])
            self.assertFalse(report["steps"][0]["process_started"])
            if fail_after:
                self.assertIn("controlled post-run inventory failure", report["error"])


class DriverFixture(unittest.TestCase):
    """Canonical temporary paths, an isolated process Git state and synthetic Git stand-ins."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="readback-driver-s8-s9-")
        self.addCleanup(temporary.cleanup)
        # The canonical spelling keeps synthetic executables bindable whatever form TMPDIR has.
        self.base = Path(os.path.realpath(temporary.name))
        self.root = self.base / "source"
        self.root.mkdir()
        self.output = self.base / "evidence"
        self.config = self.base / "selection.json"
        self.config.write_bytes(b'{"scope":"transport fixture, not a qualified host"}\n')
        self.expected = hashlib.sha256(self.config.read_bytes()).hexdigest()
        self.events = self.base / "events.log"
        isolated = patch.object(checks, "_GIT_STATE", None)
        isolated.start()
        self.addCleanup(isolated.stop)

    def stand_in(self, directory, label, *, status=128, stdout=None):
        """A synthetic Git stand-in, a /bin/sh script that logs its path and arguments, then exits."""
        path = self.base / directory / "git"
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["#!/bin/sh", f'printf "%s\\n" "{label} $0 $*" >> {shlex.quote(str(self.events))}']
        if stdout is not None:
            lines.append(f'printf "%s\\n" {shlex.quote(stdout)}')
        lines.append(f"exit {status}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        path.chmod(0o755)
        return str(path), hashlib.sha256(path.read_bytes()).hexdigest()

    def event(self, label):
        with self.events.open("a", encoding="utf-8") as stream:
            stream.write(label + "\n")

    def logged(self):
        return self.events.read_text(encoding="utf-8").splitlines() if self.events.exists() else []

    def summary(self, output=None):
        return json.loads(((output or self.output) / "summary.json").read_text(encoding="utf-8"))

    def with_path(self, *executables):
        """PATH with the stand-ins' directories first, in order."""
        directories = [os.path.dirname(path) for path in executables]
        return patch.dict(os.environ, {"PATH": os.pathsep.join([*directories, os.environ.get("PATH", "")])})

    def qualifying_run(self, binding, *, plan=()):
        """A qualifying run whose facade, provider validation and workspace derivation are mocked."""
        def facade(config, expected):
            self.event("facade")
            return binding
        def validate(config, expected, root):
            self.event("validate")
            return {"evidence_root": str(self.base)}
        derived = {"config_path": str(self.config), "config_sha256": self.expected}
        with patch(FACADE + ".git_binding_from_selection", create=True, side_effect=facade) as read, \
                patch(FACADE + ".validate_selection", side_effect=validate), \
                patch.object(checks, "bind_readback_workspace", return_value=derived), \
                patch.object(checks, "build_plan", return_value=list(plan)), \
                patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                redirect_stdout(io.StringIO()):
            code = checks.run(self.root, self.output, False, 30, readback_config=self.config,
                              readback_config_sha256=self.expected)
        read.assert_called_once_with(self.config, self.expected)
        return code, self.summary()


class SelectionRuleTests(DriverFixture):
    """S8: ordinary, partial and qualifying runs, and the qualifying run's Git binding order."""

    def test_ordinary_run_proceeds_and_the_readback_setup_error_stays_visible(self):
        """MC22. Starts real children: one synthetic unittest discovery, two trivial Python stages
        and the driver's read-only Git metadata reads of temporary directories with no repository."""
        observed = self.base / "unit-selection.json"
        names = (checks.READBACK_CONFIG_ENV, checks.READBACK_DIGEST_ENV)
        (self.root / "tests").mkdir()
        (self.root / "tests/test_ordinary_probe.py").write_text(
            f"NAMES, OBSERVED, REASON = {(names, str(observed), ORDINARY_REASON)!r}\n" + ORDINARY_PROBE, encoding="utf-8")
        plan = [checks.Step("unit-tests", UNIT_DISCOVERY),
                checks.Step("source", (sys.executable, "-B", "-c", "print('a later stage ran')")),
                checks.Step("documents", (sys.executable, "-B", "-c", "print('another stage ran')"))]
        with patch.dict(os.environ, {checks.READBACK_CONFIG_ENV: str(self.config), checks.READBACK_DIGEST_ENV: self.expected}), \
                patch.object(checks, "build_plan", return_value=plan), \
                patch.object(checks, "prepare_readback_selection") as prepare, \
                patch(FACADE + ".git_binding_from_selection", create=True) as facade, \
                patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                redirect_stdout(io.StringIO()):
            code = checks.run(self.root, self.output, False, 60)
        summary = self.summary()
        prepare.assert_not_called()
        facade.assert_not_called()
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["readback_selection"], {"status": "absent", "run_kind": "ordinary"})
        self.assertEqual([step["status"] for step in summary["steps"]], ["failed", "passed", "passed"])
        self.assertEqual(summary["not_executed_steps"], [])
        unit = summary["steps"][0]
        self.assertEqual(unit["test_execution"]["tests_run"], 1)
        self.assertEqual(unit["test_execution"]["skipped"], 0)
        self.assertFalse(unit["test_execution"]["complete_regression_passed"])
        log = (self.output / unit["log"]).read_text(encoding="utf-8")
        self.assertIn("ERROR: setUpClass", log)
        self.assertIn(ORDINARY_REASON, log)
        self.assertIn("FAILED (errors=1)", log)
        self.assertEqual(json.loads(observed.read_text()), dict.fromkeys(names))
        self.assertEqual(unit["environment_overrides"], {"PYTHONDONTWRITEBYTECODE": "1"})
        self.assertNotIn("removed_injection_environment_names", unit)
        self.assertEqual((summary["git_binding"]["bound"], summary["git_binding"]["source"]), (False, "PATH"))

    def refused(self, config, digest, *, facade=None, validate=None):
        """One failed preparation; Git metadata, the workspace copy and every child start are mocked."""
        with patch(FACADE + ".git_binding_from_selection", create=True, return_value=facade) as read, \
                patch(FACADE + ".validate_selection", side_effect=validate) as validated, \
                patch.object(checks, "git_metadata") as metadata, \
                patch.object(checks, "prepare_workspace") as copy, \
                patch.object(checks.subprocess, "Popen") as child, \
                patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                redirect_stdout(io.StringIO()):
            code = checks.run(self.root, self.output, False, 5, readback_config=config, readback_config_sha256=digest)
        summary = self.summary()
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["steps"], [])
        self.assertIn("preparation_or_execution_error", summary["readback_selection"])
        self.assertIsNone(summary["git"])
        self.assertNotIn("git_binding", summary)
        self.assertIsNone(checks._GIT_STATE)
        metadata.assert_not_called()
        copy.assert_not_called()
        child.assert_not_called()
        return summary, read, validated

    def test_qualifying_preparation_refuses_missing_partial_malformed_mismatched_and_unapproved_selections(self):
        """MC21 and the partial rule. Starts no process."""
        link = self.base / "linked-selection.json"
        link.symlink_to(self.config)
        cases = {
            "missing": (self.base / "absent-selection.json", self.expected, "No such file"),
            "partial, digest only": (None, self.expected, "EXPECTED_DIGEST"),
            "partial, path only": (self.config, None, "EXPECTED_DIGEST"),
            "malformed, relative path": (Path("selection.json"), self.expected, "absolute configuration path"),
            "malformed, uppercase digest": (self.config, self.expected.upper(), "lowercase SHA-256 digest"),
            "malformed, prefixed digest": (self.config, "sha256:" + self.expected, "lowercase SHA-256 digest"),
            "malformed, short digest": (self.config, self.expected[:-1], "lowercase SHA-256 digest"),
            "malformed, linked configuration": (link, self.expected, "symbolic link"),
            "mismatched": (self.config, "0" * 64, "differs from the independently supplied expected digest"),
        }
        for index, (name, (config, digest, reason)) in enumerate(cases.items()):
            with self.subTest(case=name):
                self.output = self.base / f"evidence-{index}"
                summary, read, validated = self.refused(config, digest)
                self.assertIn(reason, summary["error"])
                if config is None or digest is None:
                    self.assertNotIn("run_kind", summary["readback_selection"])
                else:
                    self.assertEqual(summary["readback_selection"]["run_kind"], "qualifying")
                read.assert_not_called()
                validated.assert_not_called()
        with self.subTest(case="unapproved, refused by the provider"):
            self.output = self.base / "evidence-unapproved"
            summary, read, validated = self.refused(
                self.config, self.expected, validate=RuntimeError("synthetic refusal of an unapproved selection"))
            self.assertIn("synthetic refusal of an unapproved selection", summary["error"])
            read.assert_called_once_with(self.config, self.expected)
            validated.assert_called_once()

    def test_qualifying_run_binds_git_before_its_first_git_start(self):
        """S9 order. Starts only the bound /bin/sh Git stand-in, three times, for metadata reads."""
        bound, digest = self.stand_in("bound", "bound-git")
        path_git, _ = self.stand_in("path", "path-git")
        with self.with_path(path_git):
            code, summary = self.qualifying_run({"path": bound, "sha256": digest})
        self.assertEqual(code, 0, summary)
        events = self.logged()
        self.assertEqual(events[:2], ["facade", "validate"])
        self.assertEqual(len(events[2:]), 3, events)
        self.assertTrue(all(line.startswith(f"bound-git {bound} -c core.fsmonitor=false -C ") for line in events[2:]), events)
        self.assertEqual(summary["git_binding"], {"path": bound, "sha256": digest, "bound": True, "source": "selection"})
        self.assertEqual(summary["readback_selection"]["run_kind"], "qualifying")
        self.assertEqual(summary["readback_selection"]["status"], "workspace_bound")
        self.assertFalse(summary["git"]["available"])

    def test_qualifying_0_1_0_selection_keeps_the_path_git_resolved_once(self):
        """Starts only the PATH /bin/sh Git stand-in, three times, for metadata reads."""
        path_git, path_digest = self.stand_in("path", "path-git")
        with self.with_path(path_git):
            code, summary = self.qualifying_run(None)
        self.assertEqual(code, 0, summary)
        events = self.logged()
        self.assertEqual(events[:2], ["facade", "validate"])
        self.assertEqual(len(events[2:]), 3, events)
        self.assertTrue(all(line.startswith(f"path-git {path_git} -c core.fsmonitor=false -C ") for line in events[2:]), events)
        self.assertEqual(summary["git_binding"], {"path": path_git, "sha256": path_digest, "bound": False, "source": "PATH"})

    def test_qualifying_run_fails_closed_before_any_git_start_when_git_cannot_be_bound(self):
        """Starts no process: Git metadata, the workspace copy and every child start are mocked."""
        bound, digest = self.stand_in("bound", "bound-git")
        provider = importlib.import_module(FACADE)
        cases = {
            "facade absent, as before W5": ("absent", "cannot import name 'git_binding_from_selection'"),
            "facade refusal": (RuntimeError("synthetic HOST refusal"), "synthetic HOST refusal"),
            "binding without its digest": ({"path": bound}, "exactly path and sha256"),
            "binding with an extra member": ({"path": bound, "sha256": digest, "size_bytes": 1}, "exactly path and sha256"),
            "binding that is not an object": ([bound, digest], "exactly path and sha256"),
            "binding of the dispatcher": ({"path": checks.GIT_DISPATCHER, "sha256": digest}, "dispatcher"),
            "binding with another digest": ({"path": bound, "sha256": "0" * 64}, "approved SHA-256"),
        }
        for index, (name, (facade, reason)) in enumerate(cases.items()):
            with self.subTest(case=name), ExitStack() as stack:
                self.output = self.base / f"evidence-{index}"
                if facade == "absent":
                    stack.enter_context(patch.dict(provider.__dict__))
                    provider.__dict__.pop("git_binding_from_selection", None)
                else:
                    effect = {"side_effect": facade} if isinstance(facade, BaseException) else {"return_value": facade}
                    stack.enter_context(patch.object(provider, "git_binding_from_selection", create=True, **effect))
                validated = stack.enter_context(patch.object(provider, "validate_selection"))
                metadata = stack.enter_context(patch.object(checks, "git_metadata"))
                copy = stack.enter_context(patch.object(checks, "prepare_workspace"))
                child = stack.enter_context(patch.object(checks.subprocess, "Popen"))
                stack.enter_context(patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"))
                stack.enter_context(redirect_stdout(io.StringIO()))
                code = checks.run(self.root, self.output, False, 5, readback_config=self.config,
                                  readback_config_sha256=self.expected)
                summary = self.summary()
                self.assertEqual(code, 1)
                self.assertEqual(summary["status"], "failed")
                self.assertIn(reason, summary["error"])
                self.assertEqual(summary["steps"], [])
                self.assertIsNone(summary["git"])
                self.assertIsNone(checks._GIT_STATE)
                for mock in (validated, metadata, copy, child):
                    mock.assert_not_called()
        self.assertEqual(self.logged(), [])


class UnitEnvironmentTests(DriverFixture):
    """S9: the removal list of a qualifying run's unit process, and its unchanged scope."""

    def test_removal_list_is_the_existing_names_every_dyld_name_and_two_launcher_names(self):
        """Starts no process."""
        existing = ["PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONBREAKPOINT",
                    "PYTHONUSERBASE", "PYTHONPYCACHEPREFIX", "LD_PRELOAD", "LD_LIBRARY_PATH", "NODE_OPTIONS", "NODE_PATH"]
        environment = {name: "control" for name in reversed(existing)}
        environment.update({"PYTHONEXECUTABLE": "control", "__PYVENV_LAUNCHER__": "control", "DYLD_LIBRARY_PATH": "control",
                            "DYLD_INSERT_LIBRARIES": "", "DYLD_": "control", "DYLD_ONTOKIN_CONTROL": "control",
                            "PATH": "kept", "LANG": "kept", "DYLDNOT": "kept", "dyld_lowercase": "kept",
                            "PYTHONNOUSERSITE": "kept", "NODE_ENV": "kept"})
        self.assertEqual(checks.unit_environment_removals(environment),
                         existing + ["DYLD_", "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH", "DYLD_ONTOKIN_CONTROL",
                                     "__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE"])
        self.assertEqual(checks.unit_environment_removals({"PATH": "kept"}), [])

    def test_each_new_removal_name_is_stripped_from_the_qualifying_unit_process(self):
        """MC07, the driver part. Starts one real synthetic Python unittest child. The mapping the driver
        passes is checked too, because CPython itself consumes __PYVENV_LAUNCHER__ at startup."""
        self.output.mkdir()
        empty = self.base / "empty-directory"
        empty.mkdir()
        controls = {"DYLD_INSERT_LIBRARIES": "", "DYLD_LIBRARY_PATH": str(empty), "DYLD_FRAMEWORK_PATH": str(empty),
                    "DYLD_ONTOKIN_SYNTHETIC_CONTROL": "1", "__PYVENV_LAUNCHER__": str(self.base / "absent-launcher"),
                    "PYTHONEXECUTABLE": str(self.base / "absent-interpreter"), "NODE_PATH": str(empty)}
        observed = self.base / "unit-environment.json"
        program = ("import json,os,unittest\nfrom pathlib import Path\nclass Environment(unittest.TestCase):\n"
                   " def test_removed(self):\n"
                   f"  seen = sorted(name for name in os.environ if name.startswith('DYLD_') or name in {sorted(controls)!r})\n"
                   f"  selection = [os.environ.get(name) for name in "
                   f"({checks.READBACK_CONFIG_ENV!r}, {checks.READBACK_DIGEST_ENV!r})]\n"
                   f"  Path({str(observed)!r}).write_text(json.dumps({{'seen': seen, 'selection': selection}}))\n"
                   "  self.assertEqual(seen, [])\n"
                   "unittest.main()\n")
        passed, real = [], subprocess.Popen
        def spy(argv, *args, **kwargs):
            passed.append(dict(kwargs["env"]))
            return real(argv, *args, **kwargs)
        selection = {"config_path": str(self.config), "config_sha256": self.expected}
        with patch.dict(os.environ):
            for name in [name for name in os.environ if checks.unit_environment_removals({name: ""})]:
                del os.environ[name]
            os.environ.update(controls)
            with patch.object(checks.subprocess, "Popen", side_effect=spy):
                result = checks.execute_step(checks.Step("unit-tests", (sys.executable, "-B", "-c", program)),
                                             self.root, self.output, {}, 30, readback_selection=selection)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(len(passed), 1)
        self.assertEqual([name for name in controls if name in passed[0]], [])
        self.assertEqual(result["removed_injection_environment_names"],
                         ["NODE_PATH", "DYLD_FRAMEWORK_PATH", "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH",
                          "DYLD_ONTOKIN_SYNTHETIC_CONTROL", "__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE"])
        self.assertEqual(json.loads(observed.read_text()), {"seen": [], "selection": [str(self.config), self.expected]})

    def test_removal_list_keeps_its_present_scope(self):
        """Starts no process: the child start is mocked to capture the mapping the driver passes.
        Only the unit step of a run that passes a selection applies the list, as before S9."""
        self.output.mkdir()
        selection = {"config_path": str(self.config), "config_sha256": self.expected}
        cases = (("qualifying unit step", "unit-tests", selection, True),
                 ("ordinary unit step", "unit-tests", None, False),
                 ("another step with a selection", "source", selection, False))
        for name, step, chosen, applied in cases:
            with self.subTest(case=name), \
                    patch.dict(os.environ, {"DYLD_ONTOKIN_SCOPE_CONTROL": "1", "PYTHONEXECUTABLE": "/absent/control"}), \
                    patch.object(checks.subprocess, "Popen") as child:
                child.return_value.pid, child.return_value.returncode = 4242, 0
                child.return_value.wait.return_value = 0
                result = checks.execute_step(checks.Step(step, (sys.executable, "-c", "pass")), self.root,
                                             self.output / name.replace(" ", "-"), {}, 5, readback_selection=chosen)
                environment = child.call_args.kwargs["env"]
                self.assertEqual("DYLD_ONTOKIN_SCOPE_CONTROL" in environment, not applied)
                self.assertEqual("PYTHONEXECUTABLE" in environment, not applied)
                self.assertEqual("removed_injection_environment_names" in result, applied)
                self.assertEqual(checks.READBACK_CONFIG_ENV in environment, applied)


class DriverGitBindingTests(DriverFixture):
    """S9: bind_git refusals, the re-check at every start, and the unbound PATH resolution."""

    def test_bound_absolute_git_is_what_every_driver_git_start_runs(self):
        """Starts the bound /bin/sh Git stand-in once; the PATH stand-in must stay unused."""
        bound, digest = self.stand_in("bound", "bound-git", status=0, stdout="synthetic toplevel")
        path_git, _ = self.stand_in("path", "path-git", status=0, stdout="unbound")
        with self.with_path(path_git):
            self.assertEqual(checks.bind_git(bound, digest),
                             {"path": bound, "sha256": digest, "bound": True, "source": "selection"})
            self.assertEqual(checks.git_executable(), bound)
            self.assertEqual(checks.git_read(self.root, "rev-parse", "--show-toplevel"), "synthetic toplevel")
            # The same binding again changes nothing.
            self.assertEqual(checks.bind_git(Path(bound), digest)["path"], bound)
        self.assertEqual(self.logged(), [f"bound-git {bound} -c core.fsmonitor=false -C {self.root} rev-parse --show-toplevel"])

    def test_bind_refuses_relative_noncanonical_linked_nonregular_dispatcher_and_mismatched_paths(self):
        """Starts no process."""
        bound, digest = self.stand_in("bound", "bound-git")
        alias = self.base / "alias"
        alias.symlink_to(self.base / "bound", target_is_directory=True)
        link = self.base / "linked-git"
        link.symlink_to(bound)
        fifo = self.base / "fifo-git"
        os.mkfifo(fifo)
        self.assertEqual(checks.GIT_DISPATCHER, "/usr/bin/git")
        base = str(self.base)
        cases = [
            ("relative name", "git", digest, "absolute path"),
            ("relative path", "bound/git", digest, "absolute path"),
            ("not a path", 42, digest, "absolute path"),
            ("noncanonical, parent segment", base + "/bound/../bound/git", digest, "not canonical"),
            ("noncanonical, current segment", base + "/bound/./git", digest, "not canonical"),
            ("noncanonical, doubled separator", base + "/bound//git", digest, "not canonical"),
            ("noncanonical, linked ancestor", str(alias / "git"), digest, "not canonical"),
            ("symbolic link", str(link), digest, "symbolic link"),
            ("not regular, directory", str(self.base / "bound"), digest, "not a regular file"),
            ("not regular, FIFO", str(fifo), digest, "not a regular file"),
            ("missing", base + "/absent/git", digest, "Cannot read"),
            ("dispatcher path", checks.GIT_DISPATCHER, digest, "dispatcher"),
            ("mismatched digest", bound, "0" * 64, "approved SHA-256"),
            ("malformed digest, uppercase", bound, digest.upper(), "lowercase SHA-256"),
            ("malformed digest, prefixed", bound, "sha256:" + digest, "lowercase SHA-256"),
            ("malformed digest, not text", bound, None, "lowercase SHA-256"),
        ]
        for name, path, sha256, reason in cases:
            with self.subTest(case=name):
                with self.assertRaisesRegex(checks.GitBindingError, reason):
                    checks.bind_git(path, sha256)
                self.assertIsNone(checks._GIT_STATE)
        dispatcher = Path(checks.GIT_DISPATCHER)
        if dispatcher.is_file():
            with self.subTest(case="dispatcher path with its own digest"):
                actual = hashlib.sha256(dispatcher.read_bytes()).hexdigest()
                with self.assertRaisesRegex(checks.GitBindingError, "dispatcher"):
                    checks.bind_git(str(dispatcher), actual)
                self.assertIsNone(checks._GIT_STATE)

    def test_bind_refuses_the_dispatcher_file_under_another_name_and_a_copy_of_its_bytes(self):
        """Starts no process. A synthetic file stands in for the dispatcher."""
        dispatcher = self.base / "system" / "git"
        dispatcher.parent.mkdir()
        dispatcher.write_bytes(b"#!/bin/sh\nexit 0\n")
        dispatcher.chmod(0o755)
        digest = hashlib.sha256(dispatcher.read_bytes()).hexdigest()
        hard_link = self.base / "hard-link" / "git"
        hard_link.parent.mkdir()
        os.link(dispatcher, hard_link)
        copy = self.base / "copy" / "git"
        copy.parent.mkdir()
        shutil.copyfile(dispatcher, copy)
        copy.chmod(0o755)
        with patch.object(checks, "GIT_DISPATCHER", str(dispatcher)):
            for name, path, reason in (("its own path", dispatcher, "macOS dispatcher"),
                                       ("a hard link", hard_link, "dispatcher's file"),
                                       ("a copy of its bytes", copy, "dispatcher's bytes")):
                with self.subTest(case=name):
                    with self.assertRaisesRegex(checks.GitBindingError, reason):
                        checks.bind_git(str(path), digest)
                    self.assertIsNone(checks._GIT_STATE)

    def test_bound_git_is_checked_again_at_every_start_and_never_falls_back_to_path(self):
        """Starts the bound /bin/sh Git stand-in once, before it changes."""
        bound, digest = self.stand_in("bound", "bound-git", status=0, stdout="clean")
        other, _ = self.stand_in("other", "other-git", status=0, stdout="other")
        checks.bind_git(bound, digest)
        self.assertEqual(checks.git_read(self.root, "status"), "clean")
        with open(bound, "a", encoding="utf-8") as stream:
            stream.write("# changed after binding\n")
        with self.assertRaisesRegex(checks.GitBindingError, "no longer matches"):
            checks.git_executable()
        with self.assertRaisesRegex(checks.GitBindingError, "no longer matches"):
            checks.git_metadata(self.root)
        os.remove(bound)
        os.symlink(other, bound)
        with self.assertRaisesRegex(checks.GitBindingError, "symbolic link"):
            checks.git_read(self.root, "status")
        os.remove(bound)
        with self.assertRaisesRegex(checks.GitBindingError, "Cannot read"):
            checks.git_executable()
        self.assertEqual((checks._GIT_STATE["path"], checks._GIT_STATE["bound"]), (bound, True))
        self.assertEqual(len(self.logged()), 1)

    def test_a_second_binding_to_another_executable_is_refused(self):
        """Starts no process."""
        first, first_digest = self.stand_in("first", "first-git")
        second, second_digest = self.stand_in("second", "second-git")
        checks.bind_git(first, first_digest)
        with self.assertRaisesRegex(checks.GitBindingError, "already bound"):
            checks.bind_git(second, second_digest)
        self.assertEqual(checks.git_executable(), first)

    def test_unbound_git_is_resolved_once_on_path_to_an_absolute_path(self):
        """Starts no process."""
        first, first_digest = self.stand_in("first", "first-git")
        second, _ = self.stand_in("second", "second-git")
        with self.with_path(first, second):
            self.assertEqual(checks.git_executable(), first)
            self.assertEqual(checks._git_binding_record(),
                             {"path": first, "sha256": first_digest, "bound": False, "source": "PATH"})
        with self.with_path(second):
            self.assertEqual(checks.git_executable(), first)
        relative, _ = self.stand_in("relative-home/bin", "relative-git")
        working = os.getcwd()
        with patch.object(checks, "_GIT_STATE", None), patch.dict(os.environ, {"PATH": "bin"}):
            os.chdir(self.base / "relative-home")
            try:
                self.assertEqual(checks.git_executable(), relative)
            finally:
                os.chdir(working)

    def test_unbound_git_absent_from_path_leaves_git_metadata_unavailable(self):
        """Starts no process."""
        empty = self.base / "empty-bin"
        empty.mkdir()
        with patch.dict(os.environ, {"PATH": str(empty)}):
            self.assertEqual(checks.git_metadata(self.root)["available"], False)
            record = checks._git_binding_record()
        self.assertEqual((record["path"], record["sha256"], record["bound"], record["source"]), (None, None, False, "PATH"))
        self.assertIn("No git executable was found on PATH", record["reason"])
        self.assertIsNone(checks._GIT_STATE)


class QualifyingUnitDecisionTests(DriverFixture):
    """MC23 in part: the driver's decision on synthetic unit results of a qualifying run."""

    HEAD = "import unittest\n\n\nclass Cohort(unittest.TestCase):\n"
    CASES = {
        "passed": HEAD + "    def test_q01(self):\n        pass\n\n    def test_q03(self):\n        pass\n",
        "skipped method": HEAD + "    def test_q01(self):\n        pass\n\n    @unittest.skip('synthetic skip')\n"
                                 "    def test_q03(self):\n        pass\n",
        "skipped class": HEAD + "    @classmethod\n    def setUpClass(cls):\n"
                                "        raise unittest.SkipTest('synthetic class skip')\n\n"
                                "    def test_q01(self):\n        pass\n",
        "error": HEAD + "    def test_q01(self):\n        raise RuntimeError('synthetic error')\n",
        "failure": HEAD + "    def test_q01(self):\n        self.fail('synthetic failure')\n",
        "class setup error": HEAD + "    @classmethod\n    def setUpClass(cls):\n"
                                    "        raise RuntimeError('synthetic setup refusal')\n\n"
                                    "    def test_q01(self):\n        pass\n",
        "class teardown error": HEAD + "    @classmethod\n    def tearDownClass(cls):\n"
                                       "        raise RuntimeError('Completed cohort is missing or has extra checker attempts')\n"
                                       "\n    def test_q01(self):\n        pass\n",
        "expected failure": HEAD + "    @unittest.expectedFailure\n    def test_q01(self):\n        self.fail('synthetic')\n",
        "unexpected success": HEAD + "    @unittest.expectedFailure\n    def test_q01(self):\n        pass\n",
        "no test": "import unittest\n",
    }

    def test_any_skip_error_failure_or_expected_failure_fails_the_qualifying_unit_stage(self):
        """Starts one real synthetic Python unittest discovery per case, each in a fresh workspace.
        The teardown error stands in for the provider's report of a missing checker attempt."""
        selection = {"config_path": str(self.config), "config_sha256": self.expected}
        for index, (name, source) in enumerate(self.CASES.items()):
            with self.subTest(case=name):
                workspace, output = self.base / f"workspace-{index}", self.base / f"evidence-{index}"
                (workspace / "tests").mkdir(parents=True)
                output.mkdir()
                (workspace / "tests/test_cohort.py").write_text(source, encoding="utf-8")
                result = checks.execute_step(checks.Step("unit-tests", UNIT_DISCOVERY), workspace, output, {}, 60,
                                             readback_selection=selection)
                passed = name == "passed"
                self.assertTrue(result["process_started"])
                self.assertIn(checks.READBACK_CONFIG_ENV, result["environment_overrides"])
                self.assertEqual(result["status"], "passed" if passed else "failed", result)
                self.assertEqual(result["test_execution"]["complete_regression_passed"], passed)

    def test_qualifying_run_with_an_expected_failure_in_its_unit_stage_fails(self):
        """Starts one real synthetic Python unittest discovery and the driver's read-only Git metadata
        reads of temporary directories with no repository; selection preparation is mocked."""
        (self.root / "tests").mkdir()
        (self.root / "tests/test_cohort.py").write_text(self.CASES["expected failure"], encoding="utf-8")
        selection = {"config_path": str(self.config), "config_sha256": self.expected}
        with patch.object(checks, "prepare_readback_selection", return_value=selection), \
                patch.object(checks, "bind_readback_workspace", return_value=selection), \
                patch.object(checks, "build_plan", return_value=[checks.Step("unit-tests", UNIT_DISCOVERY)]), \
                patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                redirect_stdout(io.StringIO()):
            code = checks.run(self.root, self.output, False, 60, readback_config=self.config,
                              readback_config_sha256=self.expected)
        summary = self.summary()
        self.assertEqual(code, 1)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["readback_selection"]["run_kind"], "qualifying")
        unit = summary["steps"][0]
        self.assertEqual((unit["status"], unit["returncode"]), ("failed", 0))
        self.assertEqual(unit["test_execution"]["expected_failures"], 1)
        self.assertFalse(unit["test_execution"]["complete_regression_passed"])


class DriverStorageGitTests(DriverFixture):
    """S9 for the Git starts of tools/storage_identity.py that the driver's run reaches."""

    def setUp(self):
        super().setUp()
        # Resolved before any PATH change, so that no wrapper can start itself.
        self.git = shutil.which("git")
        self.assertTrue(self.git and os.path.isabs(self.git), "These tests need Git on PATH")

    def wrapper(self, directory, label):
        """A /bin/sh wrapper that logs each start, then runs the Git that PATH named at setup."""
        path = self.base / directory / "git"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'#!/bin/sh\nprintf "%s\\n" "{label} $*" >> {shlex.quote(str(self.events))}\n'
                        f'exec {shlex.quote(self.git)} "$@"\n', encoding="utf-8")
        path.chmod(0o755)
        return str(path), hashlib.sha256(path.read_bytes()).hexdigest()

    def repository(self):
        """A committed throwaway source with committed attributes, made with the Git that PATH names."""
        (self.root / "ontokin").mkdir()
        (self.root / "ontokin/__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / ".gitattributes").write_text("*.py text\n", encoding="utf-8")
        for arguments in (("init", "--quiet", "--template="), ("add", "--", "."),
                          ("-c", "user.name=Driver storage fixture", "-c", "user.email=fixture@example.invalid",
                           "commit", "--quiet", "-m", "Driver storage fixture")):
            subprocess.run([self.git, "-C", str(self.root), *arguments], env=checks.git_environment(self.root),
                           check=True, capture_output=True)

    @staticmethod
    def storage_starts(lines):
        """storage_identity's command lines carry its hook and attribute overrides; the driver's do not."""
        return [line for line in lines if "-c core.hooksPath=" in line]

    def test_driver_storage_git_starts_use_the_bound_executable(self):
        """Starts two /bin/sh wrappers, which exec the Git that PATH named at setup, and that Git, in
        throwaway repositories. The facade, the provider's validation and the workspace derivation are mocked."""
        self.repository()
        bound, digest = self.wrapper("bound", "bound-git")
        path_git, _ = self.wrapper("path", "path-git")
        with self.with_path(path_git), \
                patch.object(checks, "prepare_offline_workspace", wraps=storage.prepare_offline_workspace) as prepared:
            code, summary = self.qualifying_run({"path": bound, "sha256": digest})
        self.assertEqual(code, 0, summary)
        self.assertIs(prepared.call_args.kwargs["git_executable"], checks.git_executable)
        events = self.logged()
        self.assertEqual(events[:2], ["facade", "validate"])
        self.assertEqual([line for line in events[2:] if not line.startswith("bound-git ")], [])
        for command in ("rev-parse --show-object-format", "ls-tree -r -z", "init --quiet --template=",
                        "cat-file -s", "check-attr -z --stdin filter"):
            self.assertTrue(any(command in line for line in self.storage_starts(events)), (command, events))
        self.assertTrue(summary["git"]["available"])
        self.assertEqual(summary["workspace_storage"]["lfs_files"], [])

    def test_each_driver_storage_git_start_checks_the_binding_again(self):
        """Starts the bound /bin/sh wrapper, which execs the Git that PATH named at setup, and that Git,
        in a throwaway repository; after the wrapper changes, nothing starts."""
        self.repository()
        bound, digest = self.wrapper("bound", "bound-git")
        checks.bind_git(bound, digest)
        checked = []
        def driver_git():
            checked.append(checks.git_executable())
            return checked[-1]
        self.assertEqual(storage.prepare_offline_workspace(self.root, git_executable=driver_git)["lfs_files"], [])
        starts = self.logged()
        self.assertTrue(starts)
        self.assertEqual(len(checked), len(starts))
        self.assertEqual([line for line in starts if not line.startswith("bound-git ")], [])
        with open(bound, "a", encoding="utf-8") as stream:
            stream.write("# changed after binding\n")
        with self.assertRaisesRegex(checks.GitBindingError, "no longer matches"):
            storage.prepare_offline_workspace(self.root, git_executable=checks.git_executable)
        self.assertEqual(len(self.logged()), len(starts))

    def test_ordinary_run_storage_git_starts_use_the_path_git_resolved_once(self):
        """Starts the PATH /bin/sh wrapper, which execs the Git that PATH named at setup, and that Git, in
        throwaway repositories. Every start names the wrapper by its absolute path, never git by name."""
        self.repository()
        path_git, digest = self.wrapper("path", "path-git")
        commands, run = [], subprocess.run
        def record(command, *args, **kwargs):
            commands.append(list(command))
            return run(command, *args, **kwargs)
        with self.with_path(path_git), patch.object(checks.subprocess, "run", side_effect=record), \
                patch.object(checks, "build_plan", return_value=[]), \
                patch.object(checks.platform, "platform", return_value="mocked platform metadata leaf"), \
                redirect_stdout(io.StringIO()):
            code = checks.run(self.root, self.output, False, 30)
        summary = self.summary()
        self.assertEqual(code, 0, summary)
        self.assertEqual(summary["readback_selection"], {"status": "absent", "run_kind": "ordinary"})
        self.assertEqual(summary["git_binding"], {"path": path_git, "sha256": digest, "bound": False, "source": "PATH"})
        self.assertTrue(self.storage_starts(self.logged()))
        self.assertTrue(commands)
        self.assertEqual([command[0] for command in commands if command[0] != path_git], [])


if __name__ == "__main__":
    unittest.main()
