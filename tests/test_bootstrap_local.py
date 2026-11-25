"""Controls for the local setup tool. No package is installed and no network is used."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import re
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
CHANGING = {"venv", "install", "ci"}


class SetupCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = LocalProject(Path(temporary.name))
        self.selections, self.install_code = [], 0
        self.project.handlers.append(self.machine)

    def machine(self, argv):
        """Act like venv, pip, npm and the Playwright installer, inside the temporary directory only."""
        if "venv" in argv:
            target = Path(argv[-1])
            if target == self.project.venv:
                self.project.create_environment({})
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
            marker = self.project.directory / "browsers/chromium_headless_shell-1194/INSTALLATION_COMPLETE"
            marker.parent.mkdir(parents=True)
            marker.write_text("", encoding="utf-8")
            return self.project.result(argv)
        return None

    def bootstrap(self, profile="python-verification", **options):
        values = {"run": self.project.run, "which": self.project.which, "system": self.project.system, "machine": self.project.machine,
                  "cache": self.project.directory / "browsers", **options}
        return setup.bootstrap(self.project.root, profile, **values)

    def changing_calls(self):
        return [call for call in self.project.calls if CHANGING & set(call) and call[0] != "git"]

    def contents(self):
        """Everything except the ignored directory that holds the setup lock."""
        return {name: value for name, value in self.project.snapshot().items() if name != "checkout" and not re.match(r"checkout/build(/|$)", name)}

    def refused(self, pattern, profile="python-verification", **options):
        """A refusal leaves every file as it was and starts no changing command."""
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


class EnvironmentTests(SetupCase):
    def test_absent_environment_is_created_and_filled_from_the_lock(self):
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.READY))
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
                                 ("system packages", {"system_site": "true"}), ("broken", {"version": "broken"})):
            with self.subTest(case=label):
                self.project.create_environment(**arguments)
                self.refused("incompatible and was not changed.*--rebuild")

    def test_rebuild_is_explicit_and_replaces_an_unused_environment(self):
        self.project.create_environment(version="3.12.14")
        (self.project.venv / "old").write_text("old", encoding="utf-8")
        report = self.bootstrap(rebuild=True)
        self.assertEqual([action["action"] for action in report["actions"]], ["remove-environment", "create-environment", "install-packages"])
        self.assertFalse((self.project.venv / "old").exists())
        self.assertEqual(setup.exit_status(report), setup.READY)

    def test_healthy_environment_is_not_rebuilt_even_on_request(self):
        self.project.create_environment()
        report = self.bootstrap(rebuild=True)
        self.assertEqual((report["outcome"], self.changing_calls()), ("unchanged", []))

    def test_used_environment_is_never_replaced(self):
        self.project.create_environment(version="3.12.14")
        framework = "/opt/homebrew/Cellar/python@3.12/3.12.13/Python.app/Contents/MacOS/Python"
        cases = {"open file": ("4242\n", "", "4242"), "absolute start": ("", f"  77 {self.project.venv}/bin/python -m unittest\n", "77"),
                 "relative start": ("", "  78 .venv/bin/python -m unittest\n", "78"), "script of it": ("", "  80 python3 ./.venv/bin/pip list\n", "80"),
                 "framework start": ("", f"  79 {framework} -m unittest\n", "79")}
        self.project.places = str(self.project.root)
        self.project.launch = f"{framework} -m unittest __PYVENV_LAUNCHER__={self.project.venv}/bin/python"
        for label, (users, listing, number) in cases.items():
            with self.subTest(case=label):
                self.project.users, self.project.listing = users, listing
                self.refused(f"in use by process {number}", rebuild=True)

    def test_unrelated_processes_do_not_count_as_users(self):
        self.project.create_environment(version="3.12.14")
        self.project.places, self.project.launch = "/another/checkout", "Python -m unittest __PYVENV_LAUNCHER__=/another/checkout/.venv/bin/python"
        self.project.listing = (f"  81 /bin/zsh -c cd {self.project.root} && .venv/bin/python -m unittest\n  82 .venv/bin/python -m unittest\n"
                                f"  83 /opt/Python.app/Contents/MacOS/Python -m unittest\n  84 less {self.project.root}/README.md\n")
        self.assertEqual(setup.users_of(self.project.root, self.project.venv, "Darwin", self.project.run, self.project.which), [])
        self.project.calls.clear()
        setup.users_of(self.project.root, self.project.venv, "Linux", self.project.run, self.project.which)
        self.assertFalse([call for call in self.project.calls if "-Eww" in call], "Launch variables are read only on macOS.")

    def test_environment_is_kept_when_its_use_cannot_be_established(self):
        self.project.create_environment(version="3.12.14")
        del self.project.commands["lsof"]
        self.refused("cannot be established", rebuild=True)

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

    def test_failed_installation_is_kept_as_a_failure(self):
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

    def test_failing_smoke_check_prevents_success(self):
        self.project.smoke_code = 1
        report = self.bootstrap()
        self.assertEqual((report["outcome"], setup.exit_status(report)), ("changed", setup.UNMET))
        self.assertIn("smoke check", report["selected"]["next_action"])

    def test_concurrent_run_is_excluded(self):
        with setup.exclusive(self.project.root):
            with self.assertRaises(setup.Busy):
                self.bootstrap()
            self.assertEqual((self.changing_calls(), self.project.venv.exists()), ([], False))
        self.assertEqual(self.bootstrap()["outcome"], "changed")

    def test_work_finished_by_another_run_is_not_repeated(self):
        real = setup.exclusive

        def finished_meanwhile(root):
            self.project.create_environment()
            return real(root)

        with patch.object(setup, "exclusive", finished_meanwhile):
            report = self.bootstrap()
        self.assertEqual((report["outcome"], report["planned"], self.changing_calls()), ("unchanged", [], []))

    def test_platform_without_a_file_lock_is_refused(self):
        with patch.object(setup, "fcntl", None):
            self.refused("no file lock")


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
        report = self.bootstrap("visual-verification")
        self.assertEqual([action["action"] for action in report["actions"]], ["create-environment", "install-packages", "install-node-dependencies", "install-chromium"])
        npm, browser = [action["argv"] for action in report["actions"][2:]]
        self.assertEqual(npm[1:], ["ci", "--prefix", "tools", "--ignore-scripts"])
        self.assertEqual(browser[1:], ["tools/node_modules/playwright/cli.js", "install", "chromium", "--only-shell"])
        self.assertNotIn("--with-deps", json.dumps(report["actions"]))
        self.assertEqual(setup.exit_status(report), setup.READY)

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
        self.project.calls.clear()
        self.refused("new and outside the checkout", "package-smoke", work=work)

    def test_native_and_container_profiles_are_refused(self):
        for profile in ("historical-native", "linux-container"):
            with self.subTest(profile=profile):
                self.refused("does not prepare", profile)
        self.refused("Unknown profile", "everything")

    def test_root_must_be_the_top_of_a_checkout(self):
        with self.assertRaisesRegex(setup.Refusal, "top of a Git checkout"):
            (self.project.root / ".git").rename(self.project.directory / "moved")
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

    def test_report_must_be_new(self):
        existing = self.project.directory / "report.json"
        existing.write_text("kept", encoding="utf-8")
        with patch.object(setup, "bootstrap") as started:
            code, _, errors = self.call("--report", str(existing))
        started.assert_not_called()
        self.assertEqual((code, existing.read_text(encoding="utf-8")), (setup.REFUSED, "kept"))
        self.assertIn("must be new", errors)

    def test_exit_statuses(self):
        for error, code in ((setup.Refusal("no"), setup.REFUSED), (doctor.SpecificationError("no"), setup.REFUSED), (setup.Busy("busy"), setup.BUSY)):
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
