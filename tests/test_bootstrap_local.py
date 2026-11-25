"""Controls for the local setup tool. No package is installed and no network is used."""

from contextlib import redirect_stderr, redirect_stdout
import functools
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import bootstrap_local as setup
from tools import doctor_local as doctor

try:
    from tests.test_doctor_local import BASE, LocalProject
except ModuleNotFoundError:  # Discovery that starts inside tests/.
    from test_doctor_local import BASE, LocalProject

MACOS_LOCK = "tools/native-reader-verification-macos-arm64-cp312.lock"
LINUX_LOCK = "tools/native-reader-verification-linux-cp312.lock"
FRAMEWORK = "/opt/homebrew/Cellar/python@3.12/3.12.13/Python.app/Contents/MacOS/Python"
ME, OTHER = os.getuid(), os.getuid() + 1
CHANGING = {"venv", "install", "ci"}


class SetupCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = LocalProject(Path(temporary.name))
        self.selections, self.install_code, self.created = [], 0, {}
        self.project.handlers.append(self.machine)

    def machine(self, argv):
        """Act like venv, pip, npm and the Playwright installer, inside the temporary directory only."""
        if "venv" in argv:
            target = Path(argv[-1])
            if target == self.project.venv:
                self.project.create_environment({}, **self.created)
            else:
                (target / "bin").mkdir(parents=True)
            return self.project.result(argv)
        if "pip" in argv and "install" in argv:
            if self.install_code:
                return self.project.result(argv, code=self.install_code, err="ERROR: THESE PACKAGES DO NOT MATCH THE HASHES\n")
            lines = Path(argv[argv.index("-r") + 1]).read_text(encoding="utf-8").splitlines()
            self.selections.append(lines)
            for line in lines:
                name, version = re.match(r"([^=]+)==(\S+)", line).groups()
                self.project.installed[name] = version
            return self.project.result(argv)
        if "ci" in argv:
            self.project.node_modules()
            return self.project.result(argv)
        if argv[-3:] == ["install", "chromium", "--only-shell"]:
            self.project.browser()
            return self.project.result(argv)
        return None

    def bootstrap(self, profile="python-verification", **options):
        values = {"run": self.project.run, "which": self.project.which, "system": self.project.system, "machine": self.project.machine,
                  "cache": self.project.directory / "browsers", **options}
        return setup.bootstrap(self.project.root, profile, **values)

    def session(self, system="Darwin"):
        return setup.Session(self.project.root, self.project.spec, "macos-arm64", system, self.project.run, self.project.which)

    def prepared(self, **overrides):
        """A complete environment with the record that setup writes."""
        self.project.create_environment(**overrides)
        self.assertEqual(self.bootstrap()["outcome"], "changed", "Only the record is written.")
        self.project.calls.clear()

    def changing_calls(self):
        return [call for call in self.project.calls if CHANGING & set(call) and call[0] not in {"git", "ps", "lsof"}]

    def contents(self):
        """Everything except the setup lock in the Git directory."""
        return {name: value for name, value in self.project.snapshot().items() if name not in {"checkout/.git", "checkout/.git/" + setup.LOCK_NAME}}

    def refused(self, pattern, profile="python-verification", **options):
        """A refusal leaves every file as it was and starts no changing command."""
        self.project.calls.clear()
        before = self.contents()
        with self.assertRaisesRegex(setup.Refusal, pattern):
            self.bootstrap(profile, **options)
        self.assertEqual(self.changing_calls(), [])
        self.assertTrue(self.contents() == before, "A refused run changed a file.")


class PlatformSelectionTests(SetupCase):
    def test_compatible_platform_selects_its_own_lock(self):
        report = self.bootstrap(preview=True)
        self.assertEqual(report["lock"]["path"], MACOS_LOCK)
        self.project.system, self.project.machine = "Linux", "x86_64"
        self.project.base = self.project.facts(system="Linux", machine="x86_64", base_prefix_real="/usr")
        report = self.bootstrap(preview=True)
        self.assertEqual((report["lock"]["path"], report["interpreter"]["status"]), (LINUX_LOCK, "found"))

    def test_platform_without_an_entry_is_refused_before_anything_is_installed(self):
        for system, machine in (("Darwin", "x86_64"), ("Linux", "aarch64"), ("Windows", "AMD64")):
            with self.subTest(system=system, machine=machine):
                self.refused("no entry", system=system, machine=machine)

    def test_incompatible_lock_is_refused_before_anything_is_installed(self):
        del self.project.spec["profiles"]["python-verification"]["locks"]["macos-arm64"]
        self.project.save()
        self.refused("No committed lock is valid for this platform")
        self.project.spec["profiles"]["python-verification"]["locks"]["macos-arm64"] = {"path": LINUX_LOCK, "python": "3.11"}
        self.project.save()
        self.refused("is valid for Python 3.11, not 3.12")

    def test_changed_lock_is_refused_before_anything_is_installed(self):
        lock = self.project.root / MACOS_LOCK
        original = lock.read_text(encoding="utf-8")
        for label, text in (("hash", original.replace("c647aa", "c647ab")), ("version", original.replace("attrs==26.1.0", "attrs==26.2.0")),
                            ("no hash", re.sub(r" --hash=sha256:[0-9a-f]{64}", "", original, count=1))):
            with self.subTest(change=label):
                lock.write_text(text, encoding="utf-8")
                self.refused("specification, pins and locks disagree")

    def test_linux_lock_is_never_installed_on_macos(self):
        self.bootstrap()
        linux = doctor.parse_lock((self.project.root / LINUX_LOCK).read_text(encoding="utf-8"))
        installed = "\n".join(line for lines in self.selections for line in lines)
        for name in ("rpds-py", "pillow"):
            self.assertNotIn(linux[name]["sha256"], installed)


class InterpreterTests(SetupCase):
    def test_requested_interpreter_must_match_the_specification(self):
        other = self.project.directory / "interpreters/python3.9"
        other.write_text("", encoding="utf-8")
        self.project.base = self.project.facts(version="3.9.6", base_prefix_real="/Library/Developer/CommandLineTools/Python")
        self.refused("version 3.9.6, expected 3.12.13.*Apple Command Line Tools, expected Homebrew", python=str(other))
        self.refused("does not exist", python=str(self.project.directory / "absent"))

    def test_requested_interpreter_is_checked_also_when_the_environment_is_reused(self):
        self.prepared()
        other = self.project.directory / "interpreters/python3.9"
        other.write_text("", encoding="utf-8")
        self.project.base = self.project.facts(version="3.9.6")
        self.refused("version 3.9.6, expected 3.12.13", python=str(other))
        self.project.base = self.project.facts()
        self.assertEqual(self.bootstrap(python=str(other))["outcome"], "unchanged")

    def test_other_patch_other_source_and_virtual_environments_are_not_compliant(self):
        for label, facts in (("patch", {"version": "3.12.14"}), ("uv", {"base_prefix_real": "/home/x/.local/share/uv/python/cpython-3.12.13"}),
                             ("environment", {"prefix": "/somewhere/.venv"})):
            with self.subTest(case=label):
                self.project.base = self.project.facts(**facts)
                report = self.bootstrap()
                self.assertEqual(report["outcome"], "interpreter-mismatch")
                self.assertEqual((self.changing_calls(), setup.exit_status(report), self.project.venv.exists()), ([], setup.UNMET, False))

    def test_missing_interpreter_is_told_apart_from_missing_packages(self):
        self.project.interpreter.unlink()
        self.project.which = lambda name: self.project.commands.get(name)
        report = self.bootstrap()
        self.assertEqual((report["outcome"], self.changing_calls()), ("interpreter-missing", []))
        self.assertIn("brew install python@3.12", setup.render(report))
        self.project.create_environment({})
        report = self.bootstrap()
        self.assertEqual((report["outcome"], report["interpreter"]["status"]), ("changed", "not_needed"))

    def test_interpreter_is_installed_only_on_request_and_only_when_absent(self):
        self.project.interpreter.unlink()
        present = self.project.which
        self.project.which = lambda name: None if name == "python3.12" else self.project.commands.get(name)

        def brew(argv):
            if argv[:1] == ["brew"]:
                self.project.interpreter.write_text("", encoding="utf-8")
                self.project.which = present
                return self.project.result(argv)

        self.project.handlers.insert(0, brew)
        report = self.bootstrap(install=True)
        self.assertEqual(report["actions"][0]["argv"], ["brew", "install", "python@3.12"])
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.READY))
        self.project.calls.clear()
        self.project.base = self.project.facts(version="3.12.14")
        self.project.create_environment(version="3.12.14")
        report = self.bootstrap(install=True, rebuild=True)
        self.assertEqual(report["outcome"], "interpreter-mismatch")
        self.assertFalse([call for call in self.project.calls if call[0] == "brew"])
        self.assertTrue(self.project.venv.exists())

    def test_created_environment_must_run_the_specified_interpreter(self):
        self.created = {"version": "3.12.14"}
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("failed", setup.UNMET))
        self.assertIn("created environment is not compliant: version 3.12.14, expected 3.12.13", report["failure"])
        self.assertEqual(self.selections, [])


class EnvironmentTests(SetupCase):
    def test_absent_environment_is_created_and_filled_from_the_lock(self):
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.READY), report.get("failure"))
        create, install = self.changing_calls()
        self.assertEqual(create, [str(self.project.interpreter), "-I", "-m", "venv", str(self.project.venv)])
        self.assertEqual(install[:-1], [str(self.project.venv / "bin/python"), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "install", "--no-input",
                                        "--no-deps", "--only-binary=:all:", "--require-hashes", "-r"])
        pins = doctor.parse_lock((self.project.root / MACOS_LOCK).read_text(encoding="utf-8"))
        self.assertEqual(sorted(self.selections[0]), sorted(pin["line"] for pin in pins.values()))
        self.assertEqual([item["passed"] for item in report["smoke"]], [True, True])
        self.assertEqual({place for call, place in zip(self.project.calls, self.project.directories) if "ontokin" in call}, {self.project.root}, "Source checks run in the checkout.")
        self.assertEqual(self.project.git("status", "--porcelain"), "")

    def test_environment_record_says_what_was_installed_from_which_inputs(self):
        self.bootstrap()
        record = json.loads((self.project.venv / "ontokin-environment.json").read_text(encoding="utf-8"))
        self.assertEqual((record["schema"], record["profile"], record["interpreter"]["version"]), (setup.RECORD_SCHEMA, "python-verification", "3.12.13"))
        self.assertEqual(record["interpreter"]["distribution"]["name"], "Homebrew")
        self.assertEqual(record["lock"]["path"], MACOS_LOCK)
        self.assertEqual(record["digests"][MACOS_LOCK], doctor.digest(self.project.root / MACOS_LOCK))
        self.assertEqual(record["packages"]["Pillow"], "13.0.0")
        self.assertEqual(record["installation_tools"], {"pip": "26.0"})
        self.assertEqual([action["action"] for action in record["actions"]], ["create-environment", "install-packages"])

    def test_second_run_changes_nothing(self):
        self.bootstrap()
        before = self.project.snapshot()
        self.project.calls.clear()
        report = self.bootstrap()
        self.assertEqual((report["outcome"], report["planned"], report["changed"], setup.exit_status(report)), ("unchanged", [], False, setup.READY))
        self.assertEqual(self.changing_calls(), [])
        self.assertTrue(self.project.snapshot() == before, "A repeat run changed a file.")

    def recorded(self):
        return json.loads((self.project.venv / "ontokin-environment.json").read_text(encoding="utf-8"))

    def test_missing_record_of_a_healthy_environment_is_written_once(self):
        self.project.create_environment()
        report = self.bootstrap()
        self.assertEqual(([action["action"] for action in report["planned"]], report["outcome"], self.changing_calls()), (["record-environment"], "changed", []))
        self.assertEqual(self.recorded()["packages"]["Pillow"], "13.0.0")
        self.assertEqual(json.loads(Path(report["run_report"]).read_text(encoding="utf-8"))["outcome"], "changed")
        self.assertEqual(self.bootstrap()["outcome"], "unchanged")

    def test_record_that_no_longer_describes_the_environment_is_written_again(self):
        self.prepared()
        record = self.project.venv / "ontokin-environment.json"
        kept = self.recorded()
        for label, change, text in (("packages", lambda value: value["packages"].pop("Pillow"), "packages differs"), ("interpreter", lambda value: value["interpreter"].update(version="3.12.12"), "interpreter differs"),
                                    ("lock", lambda value: value["digests"].update({MACOS_LOCK: "sha256:0"}), "the lock differs"), ("tools", lambda value: value.update(installation_tools={}), "installation_tools differs"),
                                    ("platform", lambda value: value["platform"].update(os_version="26.0"), "platform differs")):
            with self.subTest(case=label):
                value = json.loads(json.dumps(kept))
                change(value)
                record.write_text(json.dumps(value), encoding="utf-8")
                report = self.bootstrap()
                self.assertEqual((report["outcome"], self.changing_calls()), ("changed", []))
                self.assertIn(text, report["planned"][0]["detail"])
                self.assertEqual({key: value for key, value in self.recorded().items() if key not in {"updated_at", "actions"}},
                                 {key: value for key, value in kept.items() if key not in {"updated_at", "actions"}})
        for text in ("{", "[]", json.dumps({"profile": ["a"], "digests": "x", "actions": "y", "packages": 3})):
            record.write_text(text, encoding="utf-8")
            self.assertEqual([action["action"] for action in self.bootstrap()["planned"]], ["record-environment"], text)
            self.assertEqual(self.bootstrap()["outcome"], "unchanged")
        self.assertEqual(self.bootstrap("core")["outcome"], "unchanged")
        record.unlink()
        self.bootstrap("core")
        self.assertEqual(self.recorded()["profile"], "core")
        self.bootstrap()
        record.write_text(json.dumps({**self.recorded(), "profile": "python-verification", "packages": {}}), encoding="utf-8")
        self.bootstrap("core")
        self.assertEqual(self.recorded()["profile"], "python-verification", "A smaller profile does not hide what was prepared.")

    def test_only_missing_and_mismatched_packages_are_installed(self):
        packages = {**self.project.pins, "jsonschema": "4.25.0"}
        del packages["Pillow"]
        self.project.create_environment(packages)
        report = self.bootstrap()
        self.assertEqual([re.match(r"[^=]+", line)[0] for line in self.selections[0]], ["jsonschema", "Pillow"])
        self.assertEqual(report["planned"][0]["packages"][0]["replaces"], "4.25.0")
        self.assertEqual([call for call in self.changing_calls() if "venv" in call], [])
        self.assertEqual(setup.exit_status(report), setup.READY)

    def test_core_creates_an_environment_and_installs_nothing(self):
        report = self.bootstrap("core")
        self.assertEqual([action["action"] for action in report["actions"]], ["create-environment"])
        self.assertEqual((report["selected"]["state"], report["observed"]["readiness"]["python-verification"]["state"]), ("ready", "missing"))

    def test_offline_installation_uses_only_the_given_wheels(self):
        wheels = self.project.directory / "wheels"
        self.bootstrap(wheels=[wheels])
        install = self.changing_calls()[-1]
        self.assertEqual(install[install.index("--no-index") + 1:][:2], ["--find-links", str(wheels)])
        self.assertIn("--require-hashes", install)

    def test_incompatible_environment_is_reported_and_kept(self):
        for label, arguments in (("patch", {"version": "3.12.14"}), ("copied", {"command": "python3.12 -m venv /elsewhere/.venv"}),
                                 ("system packages", {"system_site": "true"}), ("broken", {"version": "broken"}), ("no pip", {"packages": {}, "pip": None}),
                                 ("path entry", {"sys_path": ["/another/worktree"]}), ("unrecorded place", {"command": "unrecorded"}),
                                 ("duplicate", {"duplicates": {"attrs": ["26.1.0", "25.3.0"]}})):
            with self.subTest(case=label):
                self.project.create_environment(**arguments)
                self.refused("incompatible and was not changed.*--rebuild")

    def test_state_that_installing_cannot_repair_needs_an_explicit_rebuild(self):
        def conflict():
            self.project.pip_conflict = "referencing requires attrs, which is not installed.\n"

        def broken():
            self.project.broken_imports = {"rpds": "ImportError: incompatible architecture"}

        def without_pip():
            del self.project.installed["pip"]

        def broken_pip_and_a_missing_package():
            self.project.pip_error = "ModuleNotFoundError: No module named 'pip._internal'\n"
            del self.project.installed["attrs"]

        def repaired_by_a_new_environment(argv):
            if "venv" in argv:
                self.project.pip_conflict, self.project.pip_error, self.project.broken_imports = None, None, {}

        self.project.handlers.insert(0, repaired_by_a_new_environment)
        for label, damage in (("conflict", conflict), ("import", broken), ("pip", without_pip), ("broken pip", broken_pip_and_a_missing_package)):
            with self.subTest(case=label):
                self.project.create_environment()
                damage()
                self.refused("incompatible and was not changed.*--rebuild")
                report = self.bootstrap(rebuild=True)
                self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.READY), report.get("failure"))

    def test_rebuild_is_explicit_and_replaces_an_unused_environment(self):
        for label, arguments in (("incompatible", {"version": "3.12.14"}), ("incomplete", {"packages": {**self.project.pins, "attrs": "25.0.0"}})):
            with self.subTest(case=label):
                self.project.create_environment(**arguments)
                (self.project.venv / "old").write_text("old", encoding="utf-8")
                report = self.bootstrap(rebuild=True)
                self.assertEqual([action["action"] for action in report["actions"]],
                                 ["set-aside-environment", "create-environment", "install-packages", "delete-replaced-environment"])
                self.assertFalse((self.project.venv / "old").exists())
                self.assertEqual(list((self.project.root / setup.STATE_DIRECTORY).glob(".replaced-*")), [])
                self.assertEqual((setup.exit_status(report), self.project.git("status", "--porcelain")), (setup.READY, ""))

    def test_healthy_environment_is_not_rebuilt_even_on_request(self):
        self.prepared()
        report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], self.changing_calls()), ("unchanged", []))

    def test_replaced_environment_survives_a_failed_rebuild(self):
        self.project.create_environment(version="3.12.14")
        (self.project.venv / "old").write_text("old", encoding="utf-8")
        self.install_code = 1
        report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("failed", setup.UNMET))
        self.assertTrue((Path(report["set_aside"]) / "old").is_file())
        self.assertTrue(Path(report["set_aside"]).name.startswith("."), "The documentation verifier skips names with a dot.")
        self.assertIn(report["set_aside"], setup.render(report))

    def test_remnant_of_a_replaced_environment_is_reported(self):
        self.project.create_environment(version="3.12.14")
        real = shutil.rmtree

        def busy(place, *arguments, **options):
            if ".replaced-" in str(place):
                options["onerror"](os.unlink, str(place), (OSError, OSError("busy"), None))
            else:
                real(place, *arguments, **options)

        with patch.object(setup.shutil, "rmtree", busy):
            report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], report["actions"][-1]["code"], setup.exit_status(report)), ("changed", 1, setup.READY))
        self.assertIn("left behind", setup.render(report))

    def test_failed_move_leaves_the_environment_in_place(self):
        self.project.create_environment(version="3.12.14")
        with patch.object(Path, "rename", side_effect=PermissionError("not permitted")):
            report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], self.project.venv.is_dir(), self.changing_calls()), ("failed", True, []))
        self.assertIn("PermissionError", report["failure"])
        self.assertTrue(Path(report["run_report"]).is_file())

    def test_symbolic_link_and_unrelated_directory_are_never_replaced(self):
        shared = self.project.directory / "shared"
        self.project.create_environment()
        self.project.venv.rename(shared)
        self.project.venv.symlink_to(shared, target_is_directory=True)
        for options in ({"rebuild": True}, {}):
            self.refused("not an environment directory of this checkout, so it is not replaced. Move it away by hand", **options)
        self.assertTrue((shared / "bin/python").exists())
        self.project.venv.unlink()
        self.project.venv.mkdir()
        (self.project.venv / "notes.txt").write_text("mine", encoding="utf-8")
        for options in ({"rebuild": True}, {"rebuild": True, "preview": True}, {}):
            self.refused("not an environment directory of this checkout, so it is not replaced. Move it away by hand", **options)

    def test_failing_smoke_check_prevents_success(self):
        self.project.smoke_code = 1
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.UNMET))
        self.assertIn("smoke check", report["selected"]["next_action"])


class FailureTests(SetupCase):
    def run_reports(self):
        return sorted((self.project.root / setup.STATE_DIRECTORY).glob("run-*.json"))

    def interrupted(self, when):
        """Interrupt at the first command that the condition selects; the run passes the interruption on."""
        def interrupt(argv):
            if when(argv):
                self.project.handlers.remove(interrupt)
                raise KeyboardInterrupt

        self.project.handlers.insert(0, interrupt)
        with self.assertRaises(KeyboardInterrupt) as raised:
            self.bootstrap()
        return raised.exception.setup_report

    def test_failed_installation_is_kept_as_a_failure_and_can_be_resumed(self):
        self.install_code = 1
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("failed", setup.UNMET))
        self.assertIn("DO NOT MATCH THE HASHES", report["failure"])
        self.assertIn("failure: install-packages failed", setup.render(report), "A failed run can be shown also when no environment was set aside.")
        kept = json.loads(Path(report["run_report"]).read_text(encoding="utf-8"))
        self.assertEqual([(action["action"], action["code"]) for action in kept["actions"]], [("create-environment", 0), ("install-packages", 1)])
        self.assertFalse((self.project.venv / "ontokin-environment.json").exists())
        self.install_code = 0
        report = self.bootstrap()
        self.assertEqual([action["action"] for action in report["actions"]], ["install-packages"])

    def test_failed_run_is_never_reported_as_ready(self):
        report = self.bootstrap()
        self.assertEqual(setup.exit_status(report), setup.READY)
        self.assertEqual(setup.exit_status(dict(report, outcome="failed")), setup.UNMET)

    def test_interruption_is_recorded_and_passed_on(self):
        for label, when, last in (("during an action", lambda argv: "pip" in argv and "install" in argv, ("install-packages", "not finished")),
                                  ("after the last action", lambda argv: "ontokin" in argv, ("install-packages", None))):
            with self.subTest(case=label):
                report = self.interrupted(when)
                kept = json.loads(Path(report["run_report"]).read_text(encoding="utf-8"))
                self.assertEqual((kept["outcome"], kept["actions"][-1]["action"], kept["actions"][-1]["error"]), ("failed", *last))
                self.assertIn("Interrupted", kept["failure"])
                self.assertEqual(setup.exit_status(self.bootstrap()), setup.READY)
                shutil.rmtree(self.project.venv)

    def test_interruption_before_any_change_is_reported_as_such(self):
        reports = self.run_reports()
        with self.assertRaises(KeyboardInterrupt):
            with patch.object(setup, "carry_out", side_effect=KeyboardInterrupt):
                self.bootstrap()
        self.assertEqual((self.run_reports(), self.project.venv.exists()), (reports, False))

    def test_interruption_waits_while_the_report_is_written(self):
        real, during = setup.keep_report, []

        def observed(*arguments):
            during.append(signal.getsignal(signal.SIGINT))
            return real(*arguments)

        with patch.object(setup, "keep_report", observed):
            self.bootstrap()
        self.assertEqual(during, [signal.SIG_IGN])
        self.assertIsNot(signal.getsignal(signal.SIGINT), signal.SIG_IGN)

    def test_interrupted_record_is_reported_as_a_change(self):
        self.project.create_environment()
        report = self.interrupted(lambda argv: "ontokin" in argv)
        self.assertTrue(report["changed"])
        self.assertEqual(json.loads(Path(report["run_report"]).read_text(encoding="utf-8"))["outcome"], "failed")

    def test_input_that_changes_during_the_run_is_a_failure_with_a_report(self):
        lock = self.project.root / MACOS_LOCK
        kept = lock.read_bytes()

        def edit_lock(argv):
            if "venv" in argv:
                lock.write_text("no pins here\n", encoding="utf-8")

        self.project.handlers.insert(0, edit_lock)
        self.project.create_environment(version="3.12.14")
        report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("failed", setup.UNMET))
        self.assertIn("SpecificationError", report["failure"])
        self.assertTrue(Path(report["run_report"]).is_file() and Path(report["set_aside"]).is_dir())
        self.project.handlers.pop(0)
        lock.write_bytes(kept)
        specification = self.project.root / doctor.SPECIFICATION
        shutil.rmtree(self.project.venv)
        self.project.handlers.insert(0, lambda argv: specification.write_text("{", encoding="utf-8") and None if "install" in argv and "pip" in argv else None)
        report = self.bootstrap()
        self.assertEqual((report["outcome"], Path(report["run_report"]).is_file()), ("failed", True))
        self.assertIn("SpecificationError", report["failure"])
        self.assertIn("failed", setup.render(report))

    def test_report_that_cannot_be_kept_is_refused_first_or_reported(self):
        build = self.project.root / "build"
        build.write_text("a file", encoding="utf-8")
        self.refused("The report of this run cannot be created")
        build.unlink()
        build.symlink_to(self.project.directory / "absent", target_is_directory=True)
        self.refused("The report of this run cannot be created")
        build.unlink()
        with patch.object(doctor, "write_new", side_effect=PermissionError("not permitted")):
            report = self.bootstrap()
        self.assertEqual((report["outcome"], report["run_report"], setup.exit_status(report)), ("failed", None, setup.UNMET))
        self.assertIn("could not be kept: not permitted", setup.render(report))

    def test_record_that_cannot_be_written_is_a_failure_with_a_report(self):
        with patch.object(setup, "write_record", side_effect=PermissionError("not permitted")):
            report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("failed", setup.UNMET))
        self.assertIn("PermissionError", json.loads(Path(report["run_report"]).read_text(encoding="utf-8"))["failure"])

    def test_refusal_after_a_change_is_a_reported_failure(self):
        self.project.create_environment(version="3.12.14")
        with patch.object(setup, "create_environment", side_effect=setup.Refusal("stopped")):
            report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], report["failure"], report["actions"][0]["action"]), ("failed", "stopped", "set-aside-environment"))

    def test_environment_that_is_no_directory_is_refused(self):
        self.project.venv.write_text("a file", encoding="utf-8")
        self.refused("exists and is not a directory", rebuild=True)

    def test_set_aside_moves_only_an_environment_of_this_checkout(self):
        session = self.session()
        elsewhere = self.project.directory / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "pyvenv.cfg").write_text("", encoding="utf-8")
        for label, prepare in (("link", lambda: self.project.venv.symlink_to(elsewhere, target_is_directory=True)), ("unrelated", lambda: self.project.venv.mkdir())):
            with self.subTest(case=label):
                prepare()
                with self.assertRaisesRegex(setup.Refusal, "not an environment directory of this checkout"):
                    setup.set_aside(session)
                self.project.venv.unlink() if label == "link" else self.project.venv.rmdir()

    def test_long_output_is_cut_at_a_line(self):
        self.assertEqual(setup.tail("short"), "short")
        kept = setup.tail("x" * 50 + "/private/path\n" + "a line of text\n" * 500)
        self.assertTrue(len(kept) <= 2000 and set(kept.splitlines()) == {"a line of text"})

    def test_concurrent_run_is_excluded_even_when_nothing_is_to_do(self):
        with self.session().exclusive():
            with self.assertRaises(setup.Busy):
                self.bootstrap()
            self.assertEqual((self.changing_calls(), self.project.venv.exists()), ([], False))
        self.assertEqual(self.bootstrap()["outcome"], "changed")
        with self.session().exclusive():
            with self.assertRaises(setup.Busy):
                self.bootstrap()
        self.assertEqual(self.bootstrap()["outcome"], "unchanged")

    def test_run_beside_another_one_is_told_so_whatever_it_would_see(self):
        with self.session().exclusive():
            for label, prepare in (("half made", lambda: self.project.create_environment({}, pip=None)), ("incompatible", lambda: self.project.create_environment(version="3.12.14"))):
                with self.subTest(case=label):
                    prepare()
                    with self.assertRaises(setup.Busy):
                        self.bootstrap()

    def test_lock_stays_with_the_checkout_and_its_children(self):
        self.bootstrap()
        self.assertTrue((self.project.root / ".git" / setup.LOCK_NAME).is_file())
        held = [kept for call, kept in zip(self.project.calls, self.project.kept) if CHANGING & set(call) and call[0] != "git"]
        self.assertTrue(held and all(len(kept) == 1 for kept in held), "Children that change the environment keep the lock open.")
        shutil.rmtree(self.project.root / "build")
        with self.session().exclusive():
            with self.assertRaises(setup.Busy):
                self.bootstrap()

    def test_work_finished_by_another_run_is_not_repeated(self):
        real = setup.Session.exclusive
        self.prepared()
        shutil.move(self.project.venv, self.project.directory / "kept")
        installed, self.project.installed = self.project.installed, None

        def finished_meanwhile(session):
            shutil.move(self.project.directory / "kept", self.project.venv)
            self.project.installed = installed
            return real(session)

        with patch.object(setup.Session, "exclusive", finished_meanwhile):
            report = self.bootstrap()
        self.assertEqual((report["outcome"], report["planned"], self.changing_calls()), ("unchanged", [], []))

    def test_platform_without_a_file_lock_is_refused(self):
        with patch.object(setup, "fcntl", None):
            self.refused("no file lock")

    def test_lock_that_cannot_be_opened_is_refused(self):
        (self.project.root / ".git" / setup.LOCK_NAME).mkdir()
        self.refused("The setup lock cannot be opened")


class UseTests(SetupCase):
    def users(self, directory=None, system="Darwin"):
        return setup.users_of(self.session(system), directory or self.project.venv)

    def alone(self, number, command, **options):
        """One process beside the system's first one."""
        self.project.processes[1:] = []
        self.project.process(number, command, **options)

    def test_every_way_of_starting_from_the_environment_counts(self):
        venv, root = self.project.venv, str(self.project.root)
        (venv / "bin").mkdir(parents=True)
        (venv / "bin/python").write_text("", encoding="utf-8")
        plain = "PATH=/usr/bin:/bin"
        cases = {"absolute": (f"{venv}/bin/python -m unittest", {"program": "python3.12", "environment": plain}),
                 "relative": (".venv/bin/python -m unittest", {"program": "python3.12", "environment": plain}),
                 "script": ("python3 ./.venv/bin/pip list", {"program": "python3.12", "environment": plain}),
                 "named script": (f"python3 {venv}/bin/pip list", {"program": "python3.12", "environment": plain, "place": "/elsewhere"}),
                 "framework": (f"{FRAMEWORK} -m unittest", {"program": "Python", "environment": f"{plain} __PYVENV_LAUNCHER__={venv}/bin/python"}),
                 "empty environment": (f"{FRAMEWORK} -m unittest", {"program": "Python", "environment": f"__PYVENV_LAUNCHER__={venv}/bin/python", "place": "/elsewhere"}),
                 "path": ("python -m unittest", {"program": "python3.12", "environment": f"HOME=/h PATH={venv}/bin:/usr/bin TERM=x"}),
                 "activated": ("python -m unittest", {"program": "python3.12", "environment": f"PATH=/usr/bin VIRTUAL_ENV={venv} TERM=x"}),
                 "renamed": ("worker: idle", {"program": "python3.12", "environment": f"PATH=/usr/bin VIRTUAL_ENV={venv}"}),
                 "unreadable": ("python -m unittest", {"program": "python3.12"}),
                 "unreadable, place unknown": ("python -m unittest", {"program": "python3.12", "place": None}),
                 "tool": (".venv/bin/tool --serve", {"program": "tool"}),
                 "other user": (f"{venv}/bin/python -m unittest", {"owner": OTHER})}
        for label, (command, options) in cases.items():
            with self.subTest(start=label):
                self.alone(77, command, **{"place": root, **options})
                self.assertEqual(self.users(), ([77], None))
        for label in ("relative", "script", "tool"):
            with self.subTest(start=label, place="unknown"):
                command, options = cases[label]
                self.alone(77, command, **{**options, "place": None})
                self.assertEqual(self.users(), ([77], None), "A start that cannot be excluded counts.")
        self.project.processes[1:], self.project.users = [], "4242\n"
        self.assertEqual(self.users(), ([4242], None), "An open file counts.")
        self.project.ended = {4242}
        self.assertEqual(self.users(), ([], None), "A process that has ended uses nothing.")

    def test_environment_variables_are_read_in_the_linux_form_too(self):
        self.project.process(85, "python -m unittest", program="python3.12", place="/another", environment=f"HOME=/h VIRTUAL_ENV={self.project.venv} PATH=/usr/bin")
        self.project.process(86, "python -m unittest", program="python3.12", place="/another", environment="HOME=/h VIRTUAL_ENV=/another/.venv PATH=/usr/bin")
        self.project.process(87, "python -m unittest", program="python3.12", place="/another", environment=f"HOME=/h OLD_VIRTUAL_ENV={self.project.venv} PATH=/usr/bin")
        self.assertEqual(self.users(system="Linux"), ([85], None))
        self.assertTrue([call for call in self.project.calls if call[:2] == ["cat", "/proc/85/environ"]])
        self.assertFalse([call for call in self.project.calls if "-Eww" in call])

    def test_paths_are_listed_in_a_locale_that_shows_them(self):
        self.project.process(77, f"{FRAMEWORK} -m unittest", program="Python", environment=f"PATH=/usr/bin __PYVENV_LAUNCHER__={self.project.venv}/bin/python")
        self.users()
        listings = [(call, environment) for call, environment in zip(self.project.calls, self.project.environments) if call[0] in {"ps", "lsof"}]
        self.assertTrue([call for call, _ in listings if "-Eww" in call])
        self.assertEqual({environment["LC_ALL"] for _, environment in listings}, {"en_US.UTF-8"})
        self.assertEqual(setup.listing_environment("Linux")["LC_ALL"], "C.UTF-8")

    def test_unrelated_processes_do_not_count(self):
        root, venv = self.project.root, self.project.venv
        for number, command, options in (
                (81, f"/bin/zsh -c cd {root} && .venv/bin/python -m unittest", {"program": "zsh"}), (82, ".venv/bin/python -m unittest", {"program": "python3.12"}),
                (83, f"{FRAMEWORK} -m unittest", {"program": "Python", "environment": "PATH=/usr/bin __PYVENV_LAUNCHER__=/another/checkout/.venv/bin/python"}),
                (84, f"less {root}/README.md", {"program": "less"}), (85, "python -m unittest", {"program": "python3.12", "environment": "PATH=/usr/bin VIRTUAL_ENV=/another/.venv"}),
                (86, f"{FRAMEWORK} -m unittest", {"program": "Python", "environment": f"PATH=/usr/bin __PYVENV_LAUNCHER__={venv}2/bin/python"}),
                (87, "python -m unittest", {"program": "python3.12"}), (88, "node server.js", {"program": "node"}),
                (89, "python -m unittest", {"program": "python3.12", "owner": OTHER}), (90, "node validator.mjs", {"program": "node", "owner": OTHER, "place": None}),
                (557, "/System/Library/CoreServices/Software Update.app/Contents/Resources/softwareupdated", {"owner": OTHER, "place": None}),
                (558, "/Applications/Some App.app/Contents/MacOS/helper.app/run --flag", {"program": "run", "place": None})):
            self.project.process(number, command, **{"place": "/another/checkout", "environment": "PATH=/usr/bin" if number not in {87} else None, **options})
        self.assertEqual(self.users(), ([], None))

    def test_node_in_the_checkout_does_not_hold_the_environment(self):
        self.prepared()
        del self.project.installed["attrs"]
        self.project.process(90, "node server.js", program="node", place=str(self.project.root))
        self.assertEqual(self.bootstrap()["outcome"], "changed", "A language server is no user of .venv.")
        self.project.process(91, f"node {self.project.venv}/bin/tool.js", program="node", place="/elsewhere")
        del self.project.installed["attrs"]
        self.refused("in use by process 91")

    def test_node_processes_of_the_checkout_count_for_its_dependencies(self):
        directory, root = self.project.root / "tools/node_modules", str(self.project.root)
        directory.mkdir(parents=True)
        for label, command, options, expected in (
                ("working here", "node tools/validator.mjs", {"place": root}, [90]), ("below", "node validator.mjs", {"place": root + "/tools"}, [90]),
                ("unknown place", "node validator.mjs", {}, [90]), ("named here", f"node {root}/tools/validator.mjs", {"place": "/elsewhere"}, [90]),
                ("renamed", "npm run dev", {"place": root}, [90]), ("program in another place", "/Users/x/Library/Application Support/fnm/node tools/validator.mjs", {"place": root}, [90]),
                ("npx", "npx playwright", {"place": root, "program": "npx"}, [90]), ("elsewhere", "node server.js", {"place": "/elsewhere"}, []),
                ("python here", "python -m unittest", {"place": root, "program": "python3.12"}, []), ("shell here", "zsh", {"place": root, "program": "zsh"}, [])):
            with self.subTest(case=label):
                self.alone(90, command, **{"program": "node", **options})
                self.assertEqual(self.users(directory), (expected, None))
        workspace = self.project.directory / "workspace/tools"
        workspace.mkdir(parents=True)
        (workspace / "node_modules").symlink_to(directory, target_is_directory=True)
        script, link = self.project.root / "tools/validator.mjs", self.project.directory / "linked.mjs"
        script.write_text("", encoding="utf-8")
        link.symlink_to(script)
        beside = os.path.relpath(script, self.project.directory)
        for label, command, options in (
                ("isolated workspace", "node tools/validator.mjs", {"place": str(workspace.parent)}), ("its tools", "node validator.mjs", {"place": str(workspace)}),
                ("below its tools", "node x.mjs", {"place": str(workspace / "deep")}), ("relative script", f"node {beside}", {"place": str(self.project.directory)}),
                ("script after an option", f"node --trace-warnings {beside}", {"place": str(self.project.directory)}), ("linked script", "node linked.mjs", {"place": str(self.project.directory)}),
                ("another letter case", f"node {str(script).upper()}", {"place": "/elsewhere"}), ("NODE_PATH", "node x.mjs", {"place": "/elsewhere", "environment": f"PATH=/usr/bin NODE_PATH=/a:{workspace}/node_modules"})):
            with self.subTest(start=label):
                self.alone(94, command, **{"program": "node", **options})
                self.assertEqual(self.users(directory), ([94], None))
        self.alone(95, "node x.mjs", program="node", place="/elsewhere", environment="PATH=/usr/bin NODE_PATH=/elsewhere/node_modules")
        self.assertEqual(self.users(directory), ([], None))

    def test_use_that_cannot_be_established_is_not_taken_as_unused(self):
        self.prepared(version="3.12.13")
        for label, change, reason in (("lsof absent", lambda: self.project.commands.pop("lsof"), "lsof was not found"), ("lsof error", lambda: setattr(self.project, "lsof_code", 2), "lsof: exit status 2"),
                                      ("lsof message", lambda: setattr(self.project, "lsof_error", "lsof: status error\n"), "lsof: lsof: status error"),
                                      ("ps error", lambda: setattr(self.project, "ps_code", 1), "ps: exit status 1"), ("ps silent", lambda: self.project.processes.clear(), "ps: exit status 0"),
                                      ("ps forbidden", lambda: self.project.handlers.insert(0, lambda argv: {**self.project.result(argv), "code": None, "error": "PermissionError: ps"} if argv[0] == "ps" else None), "ps: PermissionError")):
            with self.subTest(case=label):
                kept = list(self.project.handlers)
                self.assertEqual(self.users(), ([], None))
                change()
                users, why = self.users()
                self.assertIsNone(users)
                self.assertIn(reason, why)
                self.project.create_environment(version="3.12.14")
                self.refused(re.escape(f"cannot be established here ({reason}"), rebuild=True)
                self.project.handlers[:] = kept
                self.project.commands["lsof"], self.project.lsof_code, self.project.lsof_error, self.project.ps_code = "/usr/sbin/lsof", None, "", 0
                if not self.project.processes:
                    self.project.process(1, "/sbin/launchd", owner=0)

    def test_used_environment_is_neither_rebuilt_nor_filled(self):
        self.prepared()
        self.project.process(77, f"{self.project.venv}/bin/python -m unittest", program="python3.12", place="/elsewhere")
        self.assertEqual(self.bootstrap()["outcome"], "unchanged", "A healthy environment may be in use.")
        self.project.create_environment(version="3.12.14")
        self.refused("in use by process 77", rebuild=True)
        self.refused("in use by process 77", rebuild=True, preview=True)
        self.project.create_environment({**self.project.pins, "jsonschema": "4.25.0"})
        self.refused("in use by process 77")

    def test_setup_that_runs_from_the_environment_says_so(self):
        self.project.create_environment({**self.project.pins, "jsonschema": "4.25.0"})
        self.project.process(os.getpid(), f"{self.project.venv}/bin/python tools/bootstrap_local.py", program="python3.12", place=str(self.project.root))
        self.refused("This setup tool itself runs from .venv")


class PreviewTests(SetupCase):
    def test_preview_changes_nothing(self):
        self.project.node()
        for prepare, profiles in ((lambda: None, ("core", "python-verification", "visual-verification")), (self.prepared, ("python-verification",))):
            prepare()
            for profile in profiles:
                with self.subTest(profile=profile):
                    before = self.project.snapshot()
                    report = self.bootstrap(profile, preview=True)
                    self.assertEqual((report["outcome"], report["changed"], report["actions"]), ("previewed", False, []))
                    self.assertEqual(self.changing_calls(), [])
                    self.assertTrue(self.project.snapshot() == before, "A preview changed a file.")

    def test_preview_beside_a_running_setup_says_so(self):
        self.project.create_environment({}, pip=None)
        with self.session().exclusive():
            with self.assertRaises(setup.Busy):
                self.bootstrap(preview=True)
        self.assertFalse((self.project.root / "build").exists())

    def test_preview_names_the_packages_and_an_unavailable_interpreter(self):
        self.project.base = self.project.facts(version="3.12.14")
        text = setup.render(self.bootstrap(preview=True))
        for package, version in self.project.pins.items():
            self.assertIn(f"{package}=={version}", text)
        self.assertIn("interpreter mismatch", text)


class VisualProfileTests(SetupCase):
    def test_other_profiles_never_touch_node(self):
        self.project.node()
        self.bootstrap()
        self.bootstrap("core")
        commands = [call for call in self.project.calls if Path(call[0]).name in {"npm", "node"}]
        self.assertTrue(all(call[1:] == ["--version"] for call in commands), commands)
        self.assertFalse((self.project.root / "tools/node_modules").exists())

    def test_selected_profile_installs_dependencies_then_the_browser_separately(self):
        self.project.node()
        with patch.dict(os.environ, {"NODE_ENV": "production", "npm_config_omit": "dev", "NPM_CONFIG_REGISTRY": "https://example.invalid"}):
            report = self.bootstrap("visual-verification")
        self.assertEqual([action["action"] for action in report["actions"]], ["create-environment", "install-packages", "install-node-dependencies", "install-chromium"])
        npm, browser = [action["argv"] for action in report["actions"][2:]]
        self.assertEqual(npm[1:], ["ci", "--prefix", "tools", "--ignore-scripts"])
        self.assertEqual(browser[1:], ["tools/node_modules/playwright/cli.js", "install", "chromium", "--only-shell"])
        self.assertNotIn("--with-deps", json.dumps(report["actions"]))
        self.assertEqual(setup.exit_status(report), setup.READY)
        for command in (npm, browser):
            used = self.project.environments[self.project.calls.index(command)]
            self.assertFalse([name for name in used if name.lower().startswith(("npm_", "node_"))], "Caller settings cannot change what is installed.")
            self.assertTrue(used["PATH"].startswith(str(Path(npm[0]).parent) + os.pathsep))
        record = json.loads((self.project.venv / "ontokin-environment.json").read_text(encoding="utf-8"))
        self.assertEqual((record["profile"], record["node"]["version"], record["npm"]["version"], record["browser"]["expected"]),
                         ("visual-verification", "v22.11.0", "10.9.0", "chromium_headless_shell-1194"))
        self.assertIn({"name": "three", "expected": "0.180.0", "installed": "0.180.0", "direct": True}, record["npm_dependencies"])

    def test_record_keeps_what_was_done_and_what_the_visual_profile_prepared(self):
        self.project.node()
        self.bootstrap("visual-verification")
        record = self.project.venv / "ontokin-environment.json"
        first = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual([action["action"] for action in first["actions"]], ["create-environment", "install-packages", "install-node-dependencies", "install-chromium"])
        self.project.node_version = "v25.9.0\n"
        self.assertEqual(self.bootstrap()["outcome"], "unchanged", "Another Node.js is no matter of this profile.")
        record.write_text(json.dumps({**first, "packages": {}}), encoding="utf-8")
        self.assertEqual(self.bootstrap()["outcome"], "changed")
        again = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual((again["profile"], again["node"], again["browser"], again["actions"]), ("visual-verification", first["node"], first["browser"], first["actions"]))
        del self.project.installed["attrs"]
        self.bootstrap()
        self.assertEqual([action["action"] for action in json.loads(record.read_text(encoding="utf-8"))["actions"]],
                         [action["action"] for action in first["actions"]] + ["install-packages"])

    def test_tools_prepared_by_hand_are_recorded(self):
        self.project.node()
        self.bootstrap()
        record = self.project.venv / "ontokin-environment.json"
        self.assertEqual({json.loads(record.read_text(encoding="utf-8"))[name] for name in ("node", "npm", "npm_dependencies", "browser")}, {None})
        self.project.node_modules()
        self.project.browser()
        report = self.bootstrap("visual-verification")
        self.assertEqual(([action["action"] for action in report["planned"]], report["outcome"]), (["record-environment"], "changed"))
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["browser"]["state"], "ready")
        self.assertEqual(self.bootstrap("visual-verification")["outcome"], "unchanged")

    def test_healthy_dependencies_are_compared_and_kept(self):
        self.project.node()
        self.bootstrap("visual-verification")
        before = self.project.snapshot()
        self.project.calls.clear()
        report = self.bootstrap("visual-verification")
        self.assertEqual((report["outcome"], self.changing_calls()), ("unchanged", []))
        self.assertTrue(self.project.snapshot() == before, "A repeat run changed a file.")

    def test_differing_dependencies_are_replaced_only_on_request_and_only_when_unused(self):
        self.project.node()
        self.project.create_environment()
        self.project.node_modules(three="0.179.0")
        self.refused("--repair-node", "visual-verification")
        self.project.users = "991\n"
        self.refused("node_modules is in use by process 991", "visual-verification", repair_node=True)
        self.project.users = ""
        self.project.browser()
        report = self.bootstrap("visual-verification", repair_node=True)
        self.assertEqual([action["action"] for action in report["actions"]], ["install-node-dependencies", "install-chromium"], "The browser follows the dependencies that were just installed.")

    def test_refused_dependencies_stop_the_run_before_the_environment_changes(self):
        self.project.node()
        self.project.node_modules(three="0.179.0")
        self.refused("--repair-node", "visual-verification")
        self.assertFalse(self.project.venv.exists())

    def test_linked_dependencies_are_never_replaced(self):
        self.project.node()
        self.project.create_environment()
        self.project.node_modules(three="0.179.0")
        directory, shared = self.project.root / "tools/node_modules", self.project.directory / "shared-modules"
        directory.rename(shared)
        directory.symlink_to(shared, target_is_directory=True)
        for repair in (False, True):
            self.refused("symbolic link, so it is never replaced", "visual-verification", repair_node=repair)
        self.assertTrue((shared / "three/package.json").is_file())

    def test_wrong_or_absent_node_is_refused_and_never_installed(self):
        self.refused("Node.js was not found", "visual-verification")
        self.project.node()
        (Path(self.project.commands["node"]).parent / "npm").unlink()
        self.refused("npm was not found", "visual-verification")
        self.project.node()
        self.project.node_version = "v25.9.0\n"
        self.refused("target is Node.js 22", "visual-verification")


class OtherProfileTests(SetupCase):
    def test_package_smoke_gets_two_clean_environments_outside_the_checkout(self):
        work = self.project.directory / "smoke"
        self.refused("needs --work-dir", "package-smoke")
        self.refused("new and outside the checkout", "package-smoke", work=self.project.root / "build/smoke")
        other_case = self.project.directory / "CHECKOUT"
        if other_case.exists():  # The file system ignores letter case.
            self.refused("new and outside the checkout", "package-smoke", work=other_case / "smoke")
        link = self.project.directory / "link"
        link.symlink_to(self.project.root, target_is_directory=True)
        self.refused("new and outside the checkout", "package-smoke", work=link / "smoke")
        report = self.bootstrap("package-smoke", work=work)
        self.assertEqual([call[-1] for call in self.changing_calls()], [str(work / "build-env"), str(work / "install-env")])
        self.assertEqual((report["selected"]["state"], setup.exit_status(report)), ("not_checked", setup.READY))
        self.assertFalse(self.project.venv.exists())
        self.refused("new and outside the checkout", "package-smoke", work=work)

    def test_unwritable_places_are_refused_before_anything_changes(self):
        occupied, closed = self.project.directory / "occupied", self.project.directory / "closed"
        occupied.write_text("a file", encoding="utf-8")
        closed.mkdir(mode=0o500)
        self.addCleanup(closed.chmod, 0o700)
        for place in (occupied, closed) if os.geteuid() else (occupied,):  # Root may write anywhere.
            with self.subTest(place=place.name):
                self.refused("cannot be created", "package-smoke", work=place / "smoke")

    def test_native_and_container_profiles_are_refused(self):
        for profile in ("historical-native", "linux-container"):
            with self.subTest(profile=profile):
                self.refused("does not prepare", profile)
        self.refused("Unknown profile", "everything")

    def test_root_must_be_the_top_of_a_checkout(self):
        (self.project.root / ".git").rename(self.project.directory / "moved")
        with self.assertRaisesRegex(setup.Refusal, "top of a Git checkout"):
            self.bootstrap()

    def test_git_that_does_not_answer_is_named_as_the_cause(self):
        for label, change, message in (("absent", {"code": None, "error": "FileNotFoundError: git"}, "Git could not be started: FileNotFoundError: git"),
                                       ("refusing", {"code": 128, "err": "fatal: detected dubious ownership in repository\n"}, "top of a Git checkout or worktree: fatal: detected dubious ownership")):
            with self.subTest(case=label):
                self.project.handlers.insert(0, lambda argv, change=change: {**self.project.result(argv), **change} if argv[0] == "git" else None)
                self.refused(message)
                self.project.handlers.pop(0)

    def test_setup_never_publishes_or_changes_source(self):
        head = self.project.git("rev-parse", "HEAD")
        self.project.node()
        self.bootstrap("visual-verification")
        subcommands = {"add", "commit", "push", "fetch", "pull", "checkout", "switch", "reset", "merge", "rebase", "clean", "tag", "update-ref"}
        self.assertFalse([call for call in self.project.calls if call[0] == "git" and subcommands & set(call)])
        self.assertFalse([call for call in self.project.calls if "stash" in call and call[-1] != "list"])
        self.assertEqual((self.project.git("rev-parse", "HEAD"), self.project.git("status", "--porcelain")), (head, ""))
        self.assertFalse([call for call in self.project.calls if "check_local.py" in " ".join(call)])


class CommandLineTests(SetupCase):
    def call(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = setup.main(["--root", str(self.project.root), *arguments])
        return code, output.getvalue(), errors.getvalue()

    def test_report_place_is_checked_first(self):
        existing = self.project.directory / "report.json"
        existing.write_text("kept", encoding="utf-8")
        closed = self.project.directory / "closed"
        closed.mkdir(mode=0o500)
        self.addCleanup(closed.chmod, 0o700)
        places = [(existing, "must be new"), (existing / "report.json", "cannot be created")] + ([(closed / "report.json", "cannot be created")] if os.geteuid() else [])
        for place, message in places:
            with self.subTest(place=place.name), patch.object(setup, "bootstrap") as started:
                code, _, errors = self.call("--report", str(place))
                started.assert_not_called()
                self.assertEqual(code, setup.REFUSED)
                self.assertIn(message, errors)
        self.assertEqual(existing.read_text(encoding="utf-8"), "kept")

    def test_exit_statuses(self):
        for error, code in ((setup.Refusal("no"), setup.REFUSED), (doctor.SpecificationError("no"), setup.REFUSED), (setup.Busy("busy"), setup.BUSY),
                            (PermissionError("no"), setup.REFUSED), (KeyboardInterrupt(), setup.INTERRUPTED)):
            with self.subTest(error=type(error).__name__), patch.object(setup, "bootstrap", side_effect=error):
                self.assertEqual(self.call()[0], code)

    def test_report_is_written_and_can_be_made_portable(self):
        report = self.bootstrap(preview=True)
        target = self.project.directory / "reports/setup.json"
        with patch.object(setup, "bootstrap", return_value=report):
            code, output, _ = self.call("--preview", "--portable-paths", "--report", str(target))
        self.assertEqual(code, setup.READY)
        self.assertIn("would do: create-environment", output)
        text = target.read_text(encoding="utf-8")
        self.assertEqual(json.loads(text)["outcome"], "previewed")
        self.assertNotIn(str(self.project.root), text)

    def test_options_reach_the_setup(self):
        with patch.object(setup, "bootstrap", side_effect=setup.Refusal("stop")) as started:
            self.call("--profile", "core", "--python", "/x/python", "--rebuild", "--repair-node", "--install-interpreter", "--preview")
        self.assertEqual(started.call_args.args, (self.project.root, "core"))
        options = started.call_args.kwargs
        self.assertEqual({name: options[name] for name in ("preview", "python", "rebuild", "repair_node", "install")},
                         {"preview": True, "python": "/x/python", "rebuild": True, "repair_node": True, "install": True})

    def run_setup(self, *arguments):
        """The real command line and the real setup, on the controlled machine."""
        real = functools.partial(setup.bootstrap, run=self.project.run, which=self.project.which, system="Darwin", machine="arm64", cache=self.project.directory / "browsers")
        with patch.object(setup, "bootstrap", real):
            return self.call(*arguments)

    def test_command_line_carries_out_and_shows_every_outcome(self):
        code, output, _ = self.run_setup("--preview")
        self.assertEqual((code, output.splitlines()[0]), (setup.READY, "OntoKin local setup: profile python-verification, previewed"))
        self.install_code = 1
        code, output, _ = self.run_setup()
        self.assertEqual((code, output.splitlines()[0]), (setup.UNMET, "OntoKin local setup: profile python-verification, failed"))
        self.assertIn("failure: install-packages failed: ERROR: THESE PACKAGES DO NOT MATCH THE HASHES", output)
        self.install_code = 0
        code, output, _ = self.run_setup()
        self.assertEqual((code, output.splitlines()[0]), (setup.READY, "OntoKin local setup: profile python-verification, changed"))
        code, output, _ = self.run_setup()
        self.assertEqual((code, output.splitlines()[0]), (setup.READY, "OntoKin local setup: profile python-verification, unchanged"))
        self.assertIn("no change needed", output)
        self.project.create_environment(version="3.12.14")
        code, _, errors = self.run_setup()
        self.assertEqual(code, setup.REFUSED)
        self.assertIn("--rebuild", errors)
        with self.session().exclusive():
            self.assertEqual(self.run_setup()[0], setup.BUSY)
        self.project.base = self.project.facts(version="3.12.14")
        code, output, _ = self.run_setup("--rebuild")
        self.assertEqual(code, setup.UNMET)
        self.assertIn("interpreter-mismatch", output)
        code, output, _ = self.run_setup("--json")
        self.assertEqual((code, output), (setup.REFUSED, ""))

    def test_command_line_reports_an_interruption(self):
        def interrupt(argv):
            if "pip" in argv and "install" in argv:
                raise KeyboardInterrupt

        self.project.handlers.insert(0, interrupt)
        code, _, errors = self.run_setup()
        self.assertEqual(code, setup.INTERRUPTED)
        self.assertRegex(errors, r"The report of this run is .*/run-\w+\.json\.")
        with patch.object(setup, "bootstrap", side_effect=KeyboardInterrupt):
            self.assertIn("Nothing was changed.", self.call()[2])

    def test_portable_report_names_no_place_that_was_passed(self):
        wheels, report = self.project.directory.parent / "ontokin-test-wheels", self.project.directory / "out/report.json"
        self.project.node()
        node, python = Path(self.project.commands["node"]), self.project.interpreter
        code, _, errors = self.run_setup("--portable-paths", "--find-links", str(wheels), "--node", str(node), "--python", str(python), "--report", str(report))
        self.assertEqual(code, setup.READY, errors)
        text = report.read_text(encoding="utf-8")
        for place in (wheels, node.parent, python, self.project.root):
            self.assertNotIn(str(place), text)
        for label in ('"<find-links>"', '"<node>"', '"<node-directory>/npm"', '"<python>"'):
            self.assertIn(label, text)
        work, report = self.project.directory.parent / "ontokin-test-work" / self.project.directory.name, self.project.directory / "out/second.json"
        self.addCleanup(shutil.rmtree, work.parent, True)
        code, output, errors = self.run_setup("--profile", "package-smoke", "--work-dir", str(work), "--portable-paths", "--report", str(report))
        self.assertEqual(code, setup.READY, errors)
        for text in (output, report.read_text(encoding="utf-8")):
            self.assertNotIn(str(work), text)
        self.assertIn("<work-dir>/build-env", report.read_text(encoding="utf-8"))
        self.assertIn("<report>", self.portable_paths_of({"report": report}))

    @staticmethod
    def portable_paths_of(options):
        return {label for _, label in setup.option_labels(**options)}


class RealSetupTests(unittest.TestCase):
    """The unmodified tool creates, keeps and repeats a real environment without any package or network."""

    def test_real_core_environment_from_the_command_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = LocalProject(Path(temporary), "check out")
            project.spec["interpreter"].update(implementation=platform.python_implementation(), version=platform.python_version(), distributions={})
            project.spec["platforms"] = {"this": {"system": platform.system(), "machine": doctor.host_machine()}}
            project.save()
            (project.root / "ontokin/__main__.py").write_text("", encoding="utf-8")
            base = getattr(sys, "_base_executable", None) or sys.executable
            command = [sys.executable, "-I", "-B", str(doctor.ROOT / "tools/bootstrap_local.py"), "--root", str(project.root), "--profile", "core"]

            def run(*arguments):
                return subprocess.run([*command, *arguments], capture_output=True, text=True, timeout=300, stdin=subprocess.DEVNULL)

            first = run("--python", base)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn("done: create-environment", first.stdout)
            record = json.loads((project.venv / "ontokin-environment.json").read_text(encoding="utf-8"))
            self.assertEqual((record["profile"], record["interpreter"]["version"], list(record["packages"])), ("core", platform.python_version(), ["pip"]))
            before = project.snapshot()
            second = run()
            self.assertEqual((second.returncode, second.stdout.splitlines()[0]), (0, "OntoKin local setup: profile core, unchanged"), second.stdout + second.stderr)
            self.assertTrue(project.snapshot() == before, "A repeat run changed a file.")
            self.assertEqual(len(list((project.root / setup.STATE_DIRECTORY).glob("run-*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
