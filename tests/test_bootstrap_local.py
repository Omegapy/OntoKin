"""Controls for the local setup tool. No package is installed and no network is used."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import shutil
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
        for flag in ("--require-hashes", "--only-binary=:all:", "--no-deps", "--isolated"):
            self.assertIn(flag, install)
        self.assertNotIn("--no-index", install)
        self.assertEqual(install[0], str(self.project.venv / "bin/python"))
        pins = doctor.parse_lock((self.project.root / MACOS_LOCK).read_text(encoding="utf-8"))
        self.assertEqual(sorted(self.selections[0]), sorted(pin["line"] for pin in pins.values()))
        self.assertEqual([item["passed"] for item in report["smoke"]], [True, True])
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

    def test_missing_record_of_a_healthy_environment_is_written_once(self):
        self.project.create_environment()
        report = self.bootstrap()
        self.assertEqual(([action["action"] for action in report["planned"]], report["outcome"], self.changing_calls()), (["record-environment"], "changed", []))
        self.assertEqual(json.loads((self.project.venv / "ontokin-environment.json").read_text(encoding="utf-8"))["packages"]["Pillow"], "13.0.0")
        self.assertEqual(self.bootstrap()["outcome"], "unchanged")

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
                                 ("path entry", {"sys_path": ["/another/worktree"]})):
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

        def repaired_by_a_new_environment(argv):
            if "venv" in argv:
                self.project.pip_conflict, self.project.broken_imports = None, {}

        self.project.handlers.insert(0, repaired_by_a_new_environment)
        for label, damage in (("conflict", conflict), ("import", broken), ("pip", without_pip)):
            with self.subTest(case=label):
                self.project.create_environment()
                damage()
                self.refused("incompatible and was not changed.*--rebuild")
                report = self.bootstrap(rebuild=True)
                self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.READY), report.get("failure"))

    def test_rebuild_is_explicit_and_replaces_an_unused_environment(self):
        self.project.create_environment(version="3.12.14")
        (self.project.venv / "old").write_text("old", encoding="utf-8")
        report = self.bootstrap(rebuild=True)
        self.assertEqual([action["action"] for action in report["actions"]],
                         ["set-aside-environment", "create-environment", "install-packages", "delete-replaced-environment"])
        self.assertFalse((self.project.venv / "old").exists())
        self.assertEqual(list((self.project.root / setup.STATE_DIRECTORY).glob("replaced-*")), [])
        self.assertEqual((setup.exit_status(report), self.project.git("status", "--porcelain")), (setup.READY, ""))

    def test_healthy_environment_is_not_rebuilt_even_on_request(self):
        self.project.create_environment()
        self.project.record()
        report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], self.changing_calls()), ("unchanged", []))

    def test_replaced_environment_survives_a_failed_rebuild(self):
        self.project.create_environment(version="3.12.14")
        (self.project.venv / "old").write_text("old", encoding="utf-8")
        self.install_code = 1
        report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("failed", setup.UNMET))
        self.assertTrue((Path(report["set_aside"]) / "old").is_file())
        self.assertIn(report["set_aside"], setup.render(report))

    def test_remnant_of_a_replaced_environment_is_reported(self):
        self.project.create_environment(version="3.12.14")
        real = shutil.rmtree

        def busy(place, *arguments, **options):
            if "replaced-" in str(place):
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
        self.refused("not an environment directory of this checkout", rebuild=True)
        self.assertTrue((shared / "bin/python").exists())
        self.project.venv.unlink()
        self.project.venv.mkdir()
        (self.project.venv / "notes.txt").write_text("mine", encoding="utf-8")
        self.refused("not an environment directory of this checkout", rebuild=True)

    def test_failing_smoke_check_prevents_success(self):
        self.project.smoke_code = 1
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.UNMET))
        self.assertIn("smoke check", report["selected"]["next_action"])


class FailureTests(SetupCase):
    def test_failed_installation_is_kept_as_a_failure_and_can_be_resumed(self):
        self.install_code = 1
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("failed", setup.UNMET))
        self.assertIn("DO NOT MATCH THE HASHES", report["failure"])
        kept = json.loads(Path(report["run_report"]).read_text(encoding="utf-8"))
        self.assertEqual([(action["action"], action["code"]) for action in kept["actions"]], [("create-environment", 0), ("install-packages", 1)])
        self.assertFalse((self.project.venv / "ontokin-environment.json").exists())
        self.install_code = 0
        report = self.bootstrap()
        self.assertEqual([action["action"] for action in report["actions"]], ["install-packages"])

    def test_interruption_is_recorded_and_passed_on(self):
        def interrupt(argv):
            if "pip" in argv and "install" in argv:
                raise KeyboardInterrupt

        self.project.handlers.insert(0, interrupt)
        with self.assertRaises(KeyboardInterrupt):
            self.bootstrap()
        kept = json.loads(next((self.project.root / setup.STATE_DIRECTORY).glob("run-*.json")).read_text(encoding="utf-8"))
        self.assertEqual((kept["outcome"], kept["actions"][-1]["action"], kept["actions"][-1]["error"]), ("failed", "install-packages", "not finished"))
        self.assertIn("Interrupted", kept["failure"])
        self.project.handlers.pop(0)
        self.assertEqual(setup.exit_status(self.bootstrap()), setup.READY)

    def test_refusal_after_a_change_is_a_reported_failure(self):
        self.project.create_environment(version="3.12.14")
        with patch.object(setup, "create_environment", side_effect=setup.Refusal("stopped")):
            report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], report["failure"], report["actions"][0]["action"]), ("failed", "stopped", "set-aside-environment"))

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

        def finished_meanwhile(session):
            self.project.create_environment()
            self.project.record()
            return real(session)

        with patch.object(setup.Session, "exclusive", finished_meanwhile):
            report = self.bootstrap()
        self.assertEqual((report["outcome"], report["planned"], self.changing_calls()), ("unchanged", [], []))

    def test_platform_without_a_file_lock_is_refused(self):
        with patch.object(setup, "fcntl", None):
            self.refused("no file lock")


class UseTests(SetupCase):
    def users(self, directory=None, system="Darwin"):
        return setup.users_of(self.session(system), directory or self.project.venv)

    def test_every_way_of_starting_from_the_environment_counts(self):
        venv, root = self.project.venv, self.project.root
        self.project.places = str(root)
        self.project.launch = {"79": f"{FRAMEWORK} -m unittest PATH=/usr/bin:/bin __PYVENV_LAUNCHER__={venv}/bin/python",
                               "85": f"python -m unittest HOME=/h PATH={venv}/bin:/usr/bin TERM=x", "86": f"python -m unittest PATH=/usr/bin VIRTUAL_ENV={venv} TERM=x",
                               **{number: "python PATH=/usr/bin" for number in ("78", "80", "83", "84")}}
        (venv / "bin").mkdir(parents=True)
        (venv / "bin/python").write_text("", encoding="utf-8")
        cases = {"absolute": f"  77 {ME} {venv}/bin/python -m unittest\n", "relative": f"  78 {ME} .venv/bin/python -m unittest\n",
                 "script": f"  80 {ME} python3 ./.venv/bin/pip list\n", "framework": f"  79 {ME} {FRAMEWORK} -m unittest\n",
                 "path": f"  85 {ME} python -m unittest\n", "activated": f"  86 {ME} python -m unittest\n", "unreadable": f"  87 {ME} python -m unittest\n",
                 "other user": f"  89 {OTHER} {venv}/bin/python -m unittest\n", "named script": f"  83 {ME} python3 {venv}/bin/pip list\n",
                 "tool": f"  82 {ME} .venv/bin/tool --serve\n"}
        for label, listing in cases.items():
            with self.subTest(start=label):
                self.project.listing = listing
                self.assertEqual(self.users(), [int(listing.split()[0])])
        self.project.places = ""
        for label in ("relative", "script", "tool"):
            with self.subTest(start=label, place="unknown"):
                self.project.listing = cases[label]
                self.assertEqual(self.users(), [int(cases[label].split()[0])], "A start that cannot be excluded counts.")
        self.project.listing, self.project.users = "  1 0 /sbin/launchd\n", "4242\n"
        self.assertEqual(self.users(), [4242], "An open file counts.")

    def test_environment_variables_are_read_in_the_linux_form_too(self):
        venv = self.project.venv
        self.project.launch = {"85": f"HOME=/h\0VIRTUAL_ENV={venv}\0PATH=/usr/bin\0", "86": "HOME=/h\0VIRTUAL_ENV=/another/.venv\0PATH=/usr/bin\0"}
        self.project.places = "/another"
        self.project.listing = f"  85 {ME} python -m unittest\n  86 {ME} python -m unittest\n"
        self.assertEqual(self.users(system="Linux"), [85])
        self.assertTrue([call for call in self.project.calls if call[:2] == ["cat", "/proc/85/environ"]])
        self.assertFalse([call for call in self.project.calls if "-Eww" in call])

    def test_unrelated_processes_do_not_count(self):
        root = self.project.root
        self.project.places = "/another/checkout"
        self.project.launch = {"83": f"{FRAMEWORK} PATH=/usr/bin __PYVENV_LAUNCHER__=/another/checkout/.venv/bin/python", "85": "python PATH=/usr/bin VIRTUAL_ENV=/another/.venv"}
        self.project.listing = (f"  81 {ME} /bin/zsh -c cd {root} && .venv/bin/python -m unittest\n  82 {ME} .venv/bin/python -m unittest\n"
                                f"  83 {ME} {FRAMEWORK} -m unittest\n  84 {ME} less {root}/README.md\n  85 {ME} python -m unittest\n  88 {ME} node server.js\n  1 0 /sbin/launchd\n")
        self.assertEqual(self.users(), [])
        self.project.places, self.project.launch = "", {}
        self.project.listing = (f"  557 {OTHER} /System/Library/CoreServices/Software Update.app/Contents/Resources/softwareupdated\n"
                                f"  558 {ME} /Applications/Some App.app/Contents/MacOS/helper.app/run --flag\n  559 {OTHER} python -m unittest\n"
                                f"  560 {OTHER} node validator.mjs\n")
        self.assertEqual(self.users(), [], "Programs with a space in their path and other users' interpreters are not users of this environment.")

    def test_node_processes_of_the_checkout_count_for_its_dependencies(self):
        directory = self.project.root / "tools/node_modules"
        directory.mkdir(parents=True)
        for label, place, listing, expected in (
                ("working here", str(self.project.root), f"  90 {ME} node tools/validator.mjs\n", [90]), ("unknown place", "", f"  91 {ME} node validator.mjs\n", [91]),
                ("named here", "/elsewhere", f"  92 {ME} node {self.project.root}/tools/validator.mjs\n", [92]), ("elsewhere", "/elsewhere", f"  93 {ME} node server.js\n", [])):
            with self.subTest(case=label):
                self.project.places, self.project.listing = place, listing
                self.assertEqual(self.users(directory), expected)
        workspace = self.project.directory / "workspace/tools"
        workspace.mkdir(parents=True)
        (workspace / "node_modules").symlink_to(directory, target_is_directory=True)
        self.project.places, self.project.listing = str(workspace.parent), f"  94 {ME} node tools/validator.mjs\n"
        self.assertEqual(self.users(directory), [94], "The driver's isolated workspace links to these dependencies.")

    def test_use_that_cannot_be_established_is_not_taken_as_unused(self):
        for label, change in (("lsof absent", lambda: self.project.commands.pop("lsof")), ("lsof error", lambda: setattr(self.project, "lsof_code", 2)),
                              ("lsof message", lambda: setattr(self.project, "lsof_error", "lsof: status error\n")), ("ps error", lambda: setattr(self.project, "ps_code", 1)),
                              ("ps silent", lambda: setattr(self.project, "listing", ""))):
            with self.subTest(case=label):
                self.project.commands["lsof"], self.project.lsof_code, self.project.lsof_error = "/usr/sbin/lsof", None, ""
                self.project.ps_code, self.project.listing = 0, "  1 0 /sbin/launchd\n"
                self.assertEqual(self.users(), [])
                change()
                self.assertIsNone(self.users())
                self.project.create_environment(version="3.12.14")
                self.refused("cannot be established", rebuild=True)

    def test_used_environment_is_neither_rebuilt_nor_filled(self):
        self.project.listing = f"  77 {ME} {self.project.venv}/bin/python -m unittest\n"
        self.project.create_environment(version="3.12.14")
        self.refused("in use by process 77", rebuild=True)
        self.refused("in use by process 77", rebuild=True, preview=True)
        self.project.create_environment({**self.project.pins, "jsonschema": "4.25.0"})
        self.refused("in use by process 77")
        self.project.create_environment()
        self.project.record()
        self.assertEqual(self.bootstrap()["outcome"], "unchanged", "A healthy environment may be in use.")


class PreviewTests(SetupCase):
    def test_preview_changes_nothing(self):
        self.project.node()
        for prepare, profiles in ((lambda: None, ("core", "python-verification", "visual-verification")), (self.project.create_environment, ("python-verification",))):
            prepare()
            for profile in profiles:
                with self.subTest(profile=profile):
                    before = self.project.snapshot()
                    report = self.bootstrap(profile, preview=True)
                    self.assertEqual((report["outcome"], report["changed"], report["actions"]), ("previewed", False, []))
                    self.assertEqual(self.changing_calls(), [])
                    self.assertTrue(self.project.snapshot() == before, "A preview changed a file.")

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
        used = self.project.environments[self.project.calls.index(npm)]
        self.assertFalse([name for name in used if name.lower().startswith(("npm_", "node_"))], "Caller settings cannot change what npm installs.")
        self.assertTrue(used["PATH"].startswith(str(Path(npm[0]).parent) + os.pathsep))

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
        report = self.bootstrap("visual-verification", repair_node=True)
        self.assertEqual([action["action"] for action in report["actions"]], ["install-node-dependencies", "install-chromium"])

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
        self.project.node_version = "v25.9.0\n"
        self.refused("target is Node.js 22", "visual-verification")


class OtherProfileTests(SetupCase):
    def test_package_smoke_gets_two_clean_environments_outside_the_checkout(self):
        work = self.project.directory / "smoke"
        self.refused("needs --work-dir", "package-smoke")
        self.refused("new and outside the checkout", "package-smoke", work=self.project.root / "build/smoke")
        report = self.bootstrap("package-smoke", work=work)
        self.assertEqual([call[-1] for call in self.changing_calls()], [str(work / "build-env"), str(work / "install-env")])
        self.assertEqual((report["selected"]["state"], setup.exit_status(report)), ("not_checked", setup.READY))
        self.assertFalse(self.project.venv.exists())
        self.refused("new and outside the checkout", "package-smoke", work=work)

    @unittest.skipIf(os.geteuid() == 0, "Root may write anywhere.")
    def test_unwritable_places_are_refused_before_anything_changes(self):
        closed = self.project.directory / "closed"
        closed.mkdir(mode=0o500)
        self.addCleanup(closed.chmod, 0o700)
        self.refused("cannot be created", "package-smoke", work=closed / "smoke")

    def test_native_and_container_profiles_are_refused(self):
        for profile in ("historical-native", "linux-container"):
            with self.subTest(profile=profile):
                self.refused("does not prepare", profile)
        self.refused("Unknown profile", "everything")

    def test_root_must_be_the_top_of_a_checkout(self):
        (self.project.root / ".git").rename(self.project.directory / "moved")
        with self.assertRaisesRegex(setup.Refusal, "top of a Git checkout"):
            self.bootstrap()

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
        places = [(existing, "must be new")] + ([] if os.geteuid() == 0 else [(closed / "report.json", "cannot be created")])
        for place, message in places:
            with self.subTest(place=place.name), patch.object(setup, "bootstrap") as started:
                code, _, errors = self.call("--report", str(place))
                started.assert_not_called()
                self.assertEqual(code, setup.REFUSED)
                self.assertIn(message, errors)
        self.assertEqual(existing.read_text(encoding="utf-8"), "kept")

    def test_exit_statuses(self):
        for error, code in ((setup.Refusal("no"), setup.REFUSED), (doctor.SpecificationError("no"), setup.REFUSED), (setup.Busy("busy"), setup.BUSY),
                            (KeyboardInterrupt(), setup.INTERRUPTED)):
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


if __name__ == "__main__":
    unittest.main()
