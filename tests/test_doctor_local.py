"""Controls for the non-mutating local doctor. No package is installed and no network is used."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import doctor_local as doctor

REPOSITORY = Path(__file__).resolve().parents[1]
BASE = "/opt/homebrew/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12"
AREAS = ("checkout", "python", "packages", "specification", "visual", "storage", "workflow", "remote", "readiness", "native_experiments")


class LocalProject:
    """A temporary checkout with the committed specification and a controlled machine around it."""

    FILES = ("tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock",
             "tools/native-reader-verification-macos-arm64-cp312.lock", "tools/native-reader-verification-macos-arm64-cp312.provenance.json",
             "tools/check_native_reader_setup.py", "tools/package.json", "tools/package-lock.json", "pyproject.toml")

    def __init__(self, directory: Path, name="checkout"):
        self.directory = directory.resolve()
        self.root = self.directory / name
        for file in self.FILES:
            target = self.root / file
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((REPOSITORY / file).read_bytes())
        (self.root / "ontokin").mkdir()
        (self.root / "ontokin/__init__.py").write_text("", encoding="utf-8")
        (self.root / ".gitignore").write_text(".venv/\nbuild/\nnode_modules/\n", encoding="utf-8")
        self.interpreter = self.directory / "interpreters/python3.12"
        self.interpreter.parent.mkdir()
        self.interpreter.write_text("", encoding="utf-8")
        self.spec = json.loads((REPOSITORY / doctor.SPECIFICATION).read_text(encoding="utf-8"))
        for distribution in self.spec["interpreter"]["distributions"].values():
            distribution["search"] = [str(self.interpreter.parent)]
        self.save()
        self.pins = {package["name"]: package["version"] for package in self.spec["profiles"]["python-verification"]["packages"]}
        self.system, self.machine, self.commands = "Darwin", "arm64", {"lsof": "/usr/sbin/lsof", "brew": "/opt/homebrew/bin/brew"}
        self.base = self.facts()                      # What the specified interpreter command reports.
        self.installed = None                         # What the environment reports; None means no environment.
        self.environment = {}                         # Overrides of the environment interpreter's facts.
        self.broken_imports, self.pip_conflict, self.smoke_code, self.source = {}, None, 0, None
        self.node_version, self.users, self.lsof_code, self.lsof_error, self.ps_code = "v22.11.0\n", "", None, "", 0
        self.listing, self.places, self.launch = "  1 /sbin/launchd\n", "", {}
        self.calls, self.environments, self.kept, self.handlers = [], [], [], []
        self.git("init", "--quiet", "--template=")
        self.git("add", "-A")
        self.git("commit", "--quiet", "--no-verify", "-m", "Checkout")

    def save(self):
        (self.root / doctor.SPECIFICATION).write_text(json.dumps(self.spec, indent=2), encoding="utf-8")

    def git(self, *arguments):
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        return subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-C", str(self.root), *arguments],
                              env=environment, check=True, capture_output=True, text=True).stdout.strip()

    def facts(self, **overrides):
        return {"implementation": "CPython", "version": "3.12.13", "build": ["main", "Mar  3 2026 12:39:30"], "compiler": "Clang 17.0.0",
                "executable": "python3.12", "base_executable": "python3.12", "prefix": BASE, "base_prefix": BASE, "base_prefix_real": BASE,
                "system": "Darwin", "machine": "arm64", "os_version": "26.6.2", "platform_tag": "macosx-26.0-arm64",
                "sys_path": [BASE + "/lib/python312.zip", BASE + "/lib/python3.12"], "site_packages": BASE + "/lib/python3.12/site-packages",
                "packages": {"pip": "26.0"}, "places": {}, "duplicates": {}, "imports": {}, **overrides}

    @property
    def venv(self):
        return self.root / ".venv"

    @property
    def site(self):
        return str(self.venv / "lib/python3.12/site-packages")

    def create_environment(self, packages=None, *, command=None, system_site="false", pip="26.0", **overrides):
        """Lay out an environment directory and what its interpreter would report."""
        (self.venv / "bin").mkdir(parents=True, exist_ok=True)
        (self.venv / "bin/python").write_text("", encoding="utf-8")
        (self.venv / "pyvenv.cfg").write_text(f"home = /opt/homebrew/opt/python@3.12/bin\ninclude-system-site-packages = {system_site}\n"
                                              f"version = 3.12.13\ncommand = {command or f'python3.12 -m venv {self.venv}'}\n", encoding="utf-8")
        self.installed = {**({"pip": pip} if pip else {}), **(self.pins if packages is None else packages)}
        self.environment = overrides

    def record(self):
        (self.venv / "ontokin-environment.json").write_text("{}", encoding="utf-8")

    def environment_facts(self, names):
        present = {doctor.normalize(name) for name in self.installed}
        imports = {}
        for package in self.spec["profiles"]["python-verification"]["packages"]:
            if package["import"] in names:
                error = self.broken_imports.get(package["import"])
                if error is None and doctor.normalize(package["name"]) not in present:
                    error = "ModuleNotFoundError: absent"
                imports[package["import"]] = {"ok": error is None, "file": None if error else f"{self.site}/{package['import']}.py", "error": error}
        return self.facts(**{"prefix": str(self.venv), "packages": self.installed, "imports": imports, "site_packages": self.site,
                             "sys_path": [BASE + "/lib/python3.12", self.site],
                             "places": {name: f"{self.site}/{name}.dist-info" for name in self.installed}, **self.environment})

    def result(self, argv, code=0, out="", err=""):
        return {"argv": [str(part) for part in argv], "code": code, "out": out, "err": err, "error": None}

    def run(self, argv, cwd=None, timeout=60, env=None, keep=()):
        argv = [str(part) for part in argv]
        self.calls.append(argv)
        self.environments.append(env)
        self.kept.append(keep)
        for handler in self.handlers:
            answer = handler(argv)
            if answer is not None:
                return answer
        if argv[:3] == ["git", "lfs", "version"]:
            return self.result(argv, out="git-lfs/3.7.1 (GitHub; darwin arm64)\n")
        if argv[0] == "git" or any(part.endswith("tools/chat_workflow.py") for part in argv):
            return doctor.execute(argv, cwd, timeout, env)
        if argv[0] == "lsof" and "-Fn" in argv:
            return self.result(argv, out=f"p1\nfcwd\nn{self.places}\n" if self.places else "")
        if argv[0] == "lsof":
            return self.result(argv, code=self.lsof_code if self.lsof_code is not None else 0 if self.users else 1, out=self.users, err=self.lsof_error)
        if argv[0] == "ps" and "-Eww" in argv or argv[0] == "cat":
            text = self.launch.get(argv[-1].split("/")[2] if argv[0] == "cat" else argv[-1])
            return self.result(argv, code=0 if text else 1, out=text or "")
        if argv[0] == "ps":
            return self.result(argv, code=self.ps_code, out=self.listing)
        if argv[1:] == ["--version"]:
            return self.result(argv, out=self.node_version)
        inside = argv[0] == str(self.venv / "bin/python")
        if doctor.PROBE in argv:
            facts = self.environment_facts(json.loads(argv[-1])) if inside else self.base
            return self.result(argv, code=3, err="cannot execute") if facts is None or self.environment.get("version") == "broken" and inside else \
                self.result(argv, out=json.dumps(facts))
        if "pip" in argv and argv[-1] == "check":
            return self.result(argv, code=1 if self.pip_conflict else 0, out=self.pip_conflict or "No broken requirements found.\n")
        if argv[-1].endswith("check_native_reader_setup.py"):
            ready = self.installed.get("Pillow") == "13.0.0"
            return self.result(argv, code=0 if ready else 1, out="Native-reader image decoder ready\n" if ready else "", err="" if ready else "setup failed\n")
        if argv[-1].startswith("import ontokin"):
            return self.result(argv, out=str(self.root / "ontokin/__init__.py") + "\n" if self.source is None else self.source)
        if "ontokin" in argv:
            return self.result(argv, code=self.smoke_code)
        raise AssertionError(f"Unexpected command: {argv}")

    def which(self, name):
        return str(self.interpreter) if name == "python3.12" else self.commands.get(name)

    def collect(self, profile="python-verification", online=False, **overrides):
        options = {"run": self.run, "which": self.which, "system": self.system, "machine": self.machine,
                   "cache": self.directory / "browsers", **overrides}
        return doctor.collect(self.root, profile, online, **options)

    def snapshot(self):
        """Every path with its kind, size, time and content; Git's own directory included."""
        state = {}
        for path in sorted(self.directory.rglob("*")):
            status = path.lstat()
            content = os.readlink(path) if path.is_symlink() else path.read_bytes() if path.is_file() else None
            state[path.relative_to(self.directory).as_posix()] = (status.st_mode, status.st_mtime_ns, content)
        return state

    def node_modules(self, **versions):
        """Every package of the committed lock that belongs on the controlled platform."""
        for row in doctor.npm_dependencies(self.root, self.spec["profiles"]["visual-verification"], self.system, self.machine):
            target = self.root / "tools/node_modules" / row["name"] / "package.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"name": row["name"], "version": versions.get(row["name"], row["expected"])}), encoding="utf-8")
        target = self.root / "tools/node_modules/playwright-core/browsers.json"
        target.write_text(json.dumps({"browsers": [{"name": "chromium-headless-shell", "revision": "1194"}]}), encoding="utf-8")

    def node(self):
        directory = self.directory / "node/bin"
        directory.mkdir(parents=True, exist_ok=True)
        manifest = self.directory / "node/lib/node_modules/npm"
        (manifest / "bin").mkdir(parents=True, exist_ok=True)
        (manifest / "package.json").write_text(json.dumps({"name": "npm", "version": "10.9.0"}), encoding="utf-8")
        (manifest / "bin/npm-cli.js").write_text("", encoding="utf-8")
        (directory / "node").write_text("", encoding="utf-8")
        if not (directory / "npm").exists():
            (directory / "npm").symlink_to(manifest / "bin/npm-cli.js")
        self.commands["node"] = str(directory / "node")

    def browser(self):
        marker = self.directory / "browsers/chromium_headless_shell-1194/INSTALLATION_COMPLETE"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")


class DoctorCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = LocalProject(Path(temporary.name))

    def state(self, report, profile="python-verification"):
        return report["readiness"][profile]["state"]

    def check(self, report, identifier, profile="python-verification"):
        return next(item for item in report["readiness"][profile]["checks"] if item["id"] == identifier)


class SpecificationTests(DoctorCase):
    def test_committed_specification_pins_and_locks_agree(self):
        spec = doctor.load_specification(REPOSITORY)
        self.assertEqual(doctor.specification_problems(REPOSITORY, spec), [])
        pins = {doctor.normalize(package["name"]): package["version"] for package in doctor.packages_of(spec, "python-verification")}
        self.assertEqual(pins, {"attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1", "referencing": "0.37.0",
                                "rpds-py": "2026.5.1", "typing-extensions": "4.16.0", "pillow": "13.0.0"})
        self.assertRegex(spec["interpreter"]["version"], r"^3\.12\.\d+$")
        self.assertEqual(list(spec["profiles"]), ["core", "python-verification", "visual-verification", "package-smoke", "historical-native", "linux-container"])
        text = (REPOSITORY / doctor.SPECIFICATION).read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"\b(uv|conda|poetry|pipenv)\b", text, re.I))

    def test_platform_independent_wheels_have_the_same_hash_in_both_locks(self):
        linux = doctor.parse_lock((REPOSITORY / "tools/native-reader-verification-linux-cp312.lock").read_text(encoding="utf-8"))
        macos = doctor.parse_lock((REPOSITORY / "tools/native-reader-verification-macos-arm64-cp312.lock").read_text(encoding="utf-8"))
        provenance = json.loads((REPOSITORY / "tools/native-reader-verification-macos-arm64-cp312.provenance.json").read_text(encoding="utf-8"))
        portable = {doctor.normalize(wheel["name"]) for wheel in provenance["wheels"] if wheel["platform_independent"]}
        self.assertEqual(len(portable), 5)
        self.assertEqual({name for name in linux if linux[name]["sha256"] == macos[name]["sha256"]}, portable)

    def test_lock_is_selected_only_for_its_platform_and_python_series(self):
        spec = self.project.spec
        self.assertEqual(doctor.select_lock(spec, "python-verification", "macos-arm64", "3.12")["path"], "tools/native-reader-verification-macos-arm64-cp312.lock")
        self.assertEqual(doctor.select_lock(spec, "python-verification", "linux-x86_64", "3.12")["path"], "tools/native-reader-verification-linux-cp312.lock")
        for key, series in ((None, "3.12"), ("linux-aarch64", "3.12"), ("linux-x86_64", "3.11"), ("macos-arm64", "3.13")):
            with self.subTest(platform=key, series=series):
                self.assertEqual(doctor.select_lock(spec, "python-verification", key, series)["state"], "unsupported")
        self.assertFalse(doctor.select_lock(spec, "core", None, "3.12")["required"])
        self.assertEqual(doctor.platform_key(spec, "Darwin", "arm64"), "macos-arm64")
        self.assertIsNone(doctor.platform_key(spec, "Darwin", "x86_64"))
        self.assertIsNone(doctor.platform_key(spec, "Windows", "AMD64"))

    def test_lock_text_must_be_exact_hashed_pins(self):
        hashed = "attrs==26.1.0 --hash=sha256:" + "a" * 64
        self.assertEqual(doctor.parse_lock("# note\n" + hashed)["attrs"]["version"], "26.1.0")
        for text in ("attrs==26.1.0", "attrs>=26.1.0 --hash=sha256:" + "a" * 64, "--index-url https://example.invalid\n" + hashed,
                     hashed + "\nAttrs==26.1.0 --hash=sha256:" + "b" * 64, "https://example.invalid/attrs.whl", "", hashed + " --hash=sha256:" + "b" * 64):
            with self.subTest(text=text[:40]), self.assertRaises(doctor.SpecificationError):
                doctor.parse_lock(text)

    def test_changed_lock_pin_or_provenance_is_reported_and_not_ready(self):
        self.project.create_environment()
        lock = self.project.root / "tools/native-reader-verification-macos-arm64-cp312.lock"
        original = lock.read_bytes()
        for label, data in (("hash", original.replace(b"c647aa", b"c647ab")), ("version", original.replace(b"attrs==26.1.0", b"attrs==26.1.1")),
                            ("missing entry", original.split(b"\n", 1)[0] + b"\n" + b"\n".join(original.split(b"\n")[2:])),
                            ("bytes only", original + b"# Same pins, other bytes.\n")):
            with self.subTest(change=label):
                lock.write_bytes(data)
                report = self.project.collect()
                self.assertEqual(self.check(report, "lock")["state"], "mismatch")
                self.assertEqual(self.state(report), "mismatch")
                self.assertTrue(report["specification"]["problems"])
        lock.write_bytes(original)
        provenance = self.project.root / "tools/native-reader-verification-macos-arm64-cp312.provenance.json"
        recorded = provenance.read_bytes()
        provenance.write_bytes(recorded.replace(b'"sha256": "c647aa', b'"sha256": "c647ab'))
        self.assertIn("its wheels differ", self.check(self.project.collect(), "lock")["detail"])
        provenance.unlink()
        self.assertIn("unreadable provenance", self.check(self.project.collect(), "lock")["detail"])
        provenance.write_bytes(recorded)
        self.assertEqual(self.check(self.project.collect(), "lock")["state"], "ready")
        lock.unlink()
        self.assertEqual(self.check(self.project.collect(), "lock")["state"], "missing")

    def test_disagreeing_pin_file_and_npm_manifest_are_reported(self):
        pins = self.project.root / "tools/force-agent-verification-requirements.txt"
        pins.write_text(pins.read_text(encoding="utf-8").replace("attrs==26.1.0", "attrs==26.0.0"), encoding="utf-8")
        self.assertIn("python-verification: attrs 26.1.0 differs from tools/force-agent-verification-requirements.txt",
                      doctor.specification_problems(self.project.root, self.project.spec))
        self.project.create_environment()
        self.assertEqual(self.check(self.project.collect(), "lock")["state"], "mismatch")
        manifest = self.project.root / "tools/package.json"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace("0.180.0", "0.181.0"), encoding="utf-8")
        self.assertIn("visual-verification: npm dependencies differ from tools/package.json", doctor.specification_problems(self.project.root, self.project.spec))

    def test_unusable_specifications_are_refused(self):
        path = self.project.root / doctor.SPECIFICATION
        for label, change in (("schema", lambda spec: spec.update(schema="other/1")), ("patch", lambda spec: spec["interpreter"].update(version="3.12")),
                              ("cycle", lambda spec: spec["profiles"]["core"].update(extends="visual-verification")),
                              ("kind", lambda spec: spec["profiles"]["core"].update(kind="other")),
                              ("directory", lambda spec: spec["environment"].update(directory="../outside"))):
            with self.subTest(case=label):
                spec = json.loads(json.dumps(self.project.spec))
                change(spec)
                path.write_text(json.dumps(spec), encoding="utf-8")
                with self.assertRaises(doctor.SpecificationError):
                    doctor.load_specification(self.project.root)
        path.write_text("{", encoding="utf-8")
        with self.assertRaises(doctor.SpecificationError):
            doctor.load_specification(self.project.root)


class ReadinessTests(DoctorCase):
    def test_absent_environment_is_missing_and_unexecuted_checks_are_not_passes(self):
        report = self.project.collect()
        self.assertEqual(self.state(report, "core"), "missing")
        self.assertEqual(self.state(report), "missing")
        self.assertEqual({row["state"] for row in report["packages"]["expected"]}, {"missing"})
        for name in ("imports", "pip-check", "native-reader"):
            self.assertEqual(self.check(report, name)["state"], "not_checked")
        self.assertIn("tools/bootstrap_local.py --profile python-verification", report["selected"]["next_action"])

    def test_complete_environment_is_ready(self):
        self.project.create_environment()
        report = self.project.collect()
        self.assertEqual(self.state(report, "core"), "ready", report["readiness"]["core"])
        self.assertEqual(self.state(report), "ready", report["readiness"]["python-verification"])
        self.assertIsNone(report["selected"]["next_action"])
        self.assertEqual(report["packages"]["additional"], {})
        self.assertEqual(report["packages"]["install_tools"], {"pip": "26.0"})

    def test_wrong_version_is_a_mismatch_and_absent_package_is_missing(self):
        self.project.create_environment({**self.project.pins, "jsonschema": "4.25.0"})
        report = self.project.collect()
        self.assertEqual((self.check(report, "packages")["state"], self.state(report)), ("mismatch", "mismatch"))
        self.assertIn("jsonschema 4.25.0, expected 4.26.0", self.check(report, "packages")["detail"])
        self.assertNotIn("--rebuild", report["selected"]["next_action"])
        packages = dict(self.project.pins)
        del packages["Pillow"]
        self.project.create_environment(packages)
        report = self.project.collect()
        self.assertEqual((self.check(report, "packages")["state"], self.check(report, "imports")["state"], self.state(report)), ("missing",) * 3)
        self.assertEqual(self.check(report, "native-reader")["state"], "missing")

    def test_package_installed_twice_is_a_mismatch(self):
        self.project.create_environment(duplicates={"attrs": ["26.1.0", "25.3.0"]})
        report = self.project.collect()
        self.assertEqual((self.check(report, "packages")["state"], self.state(report)), ("mismatch", "mismatch"))
        self.assertIn("attrs 26.1.0 and 25.3.0, expected 26.1.0", self.check(report, "packages")["detail"])

    def test_dependents_of_an_absent_package_do_not_look_like_a_conflict(self):
        packages = dict(self.project.pins)
        del packages["rpds-py"]
        self.project.create_environment(packages)
        self.project.broken_imports = {name: "ModuleNotFoundError: No module named 'rpds'" for name in ("jsonschema", "referencing")}
        self.project.pip_conflict = "referencing 0.37.0 requires rpds-py, which is not installed.\n"
        report = self.project.collect()
        self.assertEqual((self.check(report, "imports")["state"], self.check(report, "pip-check")["state"], self.state(report)), ("missing",) * 3)
        self.project.installed["attrs"] = "1.0"
        self.assertEqual(self.state(self.project.collect()), "mismatch")

    def test_one_unexecuted_check_prevents_readiness_and_names_the_rebuild(self):
        self.project.create_environment(pip=None)
        report = self.project.collect()
        self.assertEqual((self.check(report, "pip-check")["state"], self.state(report)), ("not_checked", "not_checked"))
        self.assertIn("--rebuild", report["selected"]["next_action"])

    def test_additional_packages_stay_visible(self):
        self.project.create_environment({**self.project.pins, "example": "1.0"})
        self.assertEqual(self.project.collect()["packages"]["additional"], {"example": "1.0"})

    def test_interpreter_patch_drift_and_other_distributions_are_mismatches(self):
        cases = ({"version": "3.12.14"}, {"version": "3.11.14"}, {"implementation": "PyPy"}, {"machine": "x86_64"},
                 {"base_prefix_real": "/home/someone/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none"})
        for overrides in cases:
            with self.subTest(**overrides):
                self.project.create_environment(**overrides)
                report = self.project.collect()
                self.assertEqual(self.check(report, "interpreter", "core")["state"], "mismatch")
                self.assertEqual(self.state(report), "mismatch")
                self.assertIn("--rebuild", report["selected"]["next_action"])
        self.project.create_environment(version="3.12.14")
        detail = self.check(self.project.collect(), "interpreter", "core")["detail"]
        self.assertIn("version 3.12.14, expected 3.12.13", detail)
        self.assertIn("created with 3.12.13", detail)

    def test_anything_from_another_location_breaks_isolation(self):
        site = self.project.site
        for label, arguments in (("copied", {"command": "python3.12 -m venv /elsewhere/.venv"}), ("system packages", {"system_site": "true"}),
                                 ("other prefix", {"prefix": "/elsewhere/.venv"}), ("not virtual", {"prefix": BASE}),
                                 ("path entry", {"sys_path": [BASE + "/lib/python3.12", site, "/another/worktree"]}),
                                 ("shared packages", {"sys_path": [BASE + "/lib/python3.12/site-packages", site]}),
                                 ("linked site-packages", {"site_packages": "/another/site-packages"}),
                                 ("package elsewhere", {"places": {"attrs": "/another/worktree/.venv/attrs.dist-info"}})):
            with self.subTest(case=label):
                self.project.create_environment(**arguments)
                report = self.project.collect()
                self.assertEqual(self.check(report, "isolation", "core")["state"], "mismatch")
                self.assertEqual(self.state(report), "mismatch")
                self.assertIn("--rebuild", report["selected"]["next_action"])
        self.project.create_environment(sys_path=[BASE + "/lib/python3.12", site, str(self.project.root)])
        self.assertEqual(self.check(self.project.collect(), "isolation", "core")["state"], "ready", "An editable install adds this checkout only.")

    def test_shared_environment_is_a_mismatch(self):
        self.project.create_environment()
        shutil.move(str(self.project.venv), str(self.project.directory / "shared"))
        self.project.venv.symlink_to(self.project.directory / "shared", target_is_directory=True)
        report = self.project.collect()
        self.assertEqual(self.check(report, "isolation", "core")["state"], "mismatch")
        self.assertIn("symbolic link", self.check(report, "isolation", "core")["detail"])

    def test_unrecorded_creation_place_is_not_a_pass(self):
        self.project.create_environment()
        configuration = self.project.venv / "pyvenv.cfg"
        configuration.write_text("\n".join(line for line in configuration.read_text().splitlines() if not line.startswith("command")), encoding="utf-8")
        report = self.project.collect()
        self.assertEqual((self.check(report, "isolation", "core")["state"], self.state(report, "core")), ("not_checked", "not_checked"))
        self.assertIn("--rebuild", report["selected"]["next_action"])

    def test_broken_environment_is_a_mismatch_and_later_checks_are_not_run(self):
        self.project.create_environment(version="broken")
        report = self.project.collect()
        self.assertEqual(self.check(report, "interpreter", "core")["state"], "mismatch")
        self.assertEqual({item["state"] for item in report["readiness"]["python-verification"]["checks"] if item["id"] != "lock"}, {"not_checked"})
        (self.project.venv / "bin/python").unlink()
        self.assertEqual(self.check(self.project.collect(), "interpreter", "core")["state"], "mismatch")

    def test_failing_import_conflict_or_preflight_is_a_mismatch(self):
        self.project.create_environment()
        self.project.broken_imports = {"rpds": "ImportError: incompatible architecture"}
        self.assertEqual(self.check(self.project.collect(), "imports")["state"], "mismatch")
        self.project.broken_imports = {}
        self.project.pip_conflict = "referencing 0.37.0 requires attrs, which is not installed.\n"
        report = self.project.collect()
        self.assertEqual((self.check(report, "pip-check")["state"], self.state(report)), ("mismatch", "mismatch"))
        self.assertIn("--rebuild", report["selected"]["next_action"])
        self.project.pip_conflict = None
        self.project.handlers.append(lambda argv: self.project.result(argv, code=1, err="cannot import PIL.Image\n")
                                     if argv[-1].endswith("check_native_reader_setup.py") else None)
        self.assertEqual(self.check(self.project.collect(), "native-reader")["state"], "mismatch")

    def test_import_from_outside_the_environment_is_a_mismatch(self):
        self.project.create_environment(imports={package["import"]: {"ok": True, "file": f"/another/{package['import']}.py", "error": None}
                                                 for package in self.project.spec["profiles"]["python-verification"]["packages"]})
        report = self.project.collect()
        self.assertEqual(self.check(report, "imports")["state"], "mismatch")
        self.assertIn("outside the environment", self.check(report, "imports")["detail"])

    def test_source_package_must_come_from_the_checkout(self):
        self.project.create_environment()
        for source in ("\n", "/another/checkout/ontokin/__init__.py\n", f"{self.project.site}/ontokin/__init__.py\n"):
            with self.subTest(source=source):
                self.project.source = source
                report = self.project.collect()
                self.assertEqual((self.check(report, "source-import", "core")["state"], self.state(report, "core")), ("mismatch", "mismatch"))
        self.project.handlers.append(lambda argv: self.project.result(argv, code=1, err="SyntaxError: broken\n") if argv[-1].startswith("import ontokin") else None)
        self.assertIn("SyntaxError", self.check(self.project.collect(), "source-import", "core")["detail"])

    def test_missing_git_is_missing(self):
        self.project.create_environment()
        self.project.handlers.append(lambda argv: {**self.project.result(argv), "code": None, "error": "FileNotFoundError: git"} if argv[0] == "git" else None)
        report = self.project.collect()
        self.assertEqual((self.check(report, "git", "core")["state"], report["storage"]["state"]), ("missing", "not_checked"))
        self.assertIn("Install Git", report["selected"]["next_action"])

    def test_unsupported_platform_is_unsupported(self):
        self.project.create_environment()
        for system, machine in (("Darwin", "x86_64"), ("Linux", "aarch64"), ("Windows", "AMD64")):
            with self.subTest(system=system, machine=machine):
                report = self.project.collect(system=system, machine=machine)
                self.assertEqual((self.state(report, "core"), self.state(report)), ("unsupported", "unsupported"))
                self.assertIn("No setup action applies", report["selected"]["next_action"])

    def test_profiles_outside_the_environment_are_never_ready(self):
        self.project.create_environment()
        report = self.project.collect()
        self.assertEqual(self.state(report, "package-smoke"), "not_checked")
        self.assertEqual(self.state(report, "historical-native"), "not_checked")
        self.assertEqual(self.state(report, "linux-container"), "unsupported")
        self.assertEqual(report["native_experiments"]["acceptance"], "not_checked")

    def test_every_state_is_one_of_the_five(self):
        for prepare in (lambda: None, self.project.create_environment):
            prepare()
            report = self.project.collect()
            states = [entry["state"] for entry in report["readiness"].values()]
            states += [item["state"] for entry in report["readiness"].values() for item in entry["checks"]]
            self.assertLessEqual(set(states), set(doctor.STATES))
        with self.assertRaises(ValueError):
            doctor.check("example", "passed", "not a state")

    def test_missing_interpreter_is_told_apart_from_missing_packages(self):
        self.project.interpreter.unlink()
        self.project.which = lambda name: self.project.commands.get(name)
        report = self.project.collect()
        self.assertEqual(report["python"]["available_interpreters"], [])
        self.assertIn("brew install python@3.12", report["selected"]["next_action"])
        self.project.interpreter.write_text("", encoding="utf-8")
        self.project.base = self.project.facts(version="3.12.14")
        self.assertIn("found 3.12.14 (Homebrew)", self.project.collect()["selected"]["next_action"])


class RealEnvironmentTests(unittest.TestCase):
    """The real probe against a real environment, in a checkout whose path has a space."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = LocalProject(Path(temporary.name), "check out")
        spec, self.system, self.machine = self.project.spec, platform.system(), platform.machine()
        spec["interpreter"].update(implementation=platform.python_implementation(), version=platform.python_version(), distributions={})
        spec["platforms"] = {"this": {"system": self.system, "machine": self.machine}}
        self.project.save()
        subprocess.run([sys.executable, "-I", "-m", "venv", "--without-pip", str(self.project.venv)], check=True, capture_output=True, timeout=120)
        self.site = next((self.project.venv / "lib").glob("python3.*")) / "site-packages"

    def report(self):
        return doctor.collect(self.project.root, "core", run=doctor.execute, which=lambda name: None, system=self.system, machine=self.machine)

    def core(self):
        report = self.report()
        return report["readiness"]["core"]["state"], {item["id"]: item for item in report["readiness"]["core"]["checks"]}

    def metadata(self, folder, name, version):
        (self.site / folder).mkdir()
        (self.site / folder / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n", encoding="utf-8")

    def test_real_environment_is_ready_and_diagnosis_leaves_it_alone(self):
        before = self.project.snapshot()
        state, checks = self.core()
        self.assertEqual(state, "ready", checks)
        self.assertTrue(self.project.snapshot() == before, "Diagnosis changed a file.")

    def test_real_copy_path_entry_and_linked_packages_break_isolation(self):
        (self.site / "other.pth").write_text(str(self.project.directory) + "\n", encoding="utf-8")
        state, checks = self.core()
        self.assertEqual((state, checks["isolation"]["state"]), ("mismatch", "mismatch"), checks)
        (self.site / "other.pth").unlink()
        self.site.rename(self.project.directory / "moved-packages")
        self.site.symlink_to(self.project.directory / "moved-packages", target_is_directory=True)
        self.assertEqual(self.core()[1]["isolation"]["state"], "mismatch")
        other = self.project.directory / "second"
        shutil.copytree(self.project.root, other, symlinks=True)
        report = doctor.collect(other, "core", run=doctor.execute, which=lambda name: None, system=self.system, machine=self.machine)
        self.assertIn("copied or moved", next(item["detail"] for item in report["readiness"]["core"]["checks"] if item["id"] == "isolation"))

    def test_real_metadata_is_read_as_the_interpreter_reads_it(self):
        self.metadata("attrs-26.1.0.dist-info", "attrs", "26.1.0")
        self.metadata("~ttrs-25.3.0.dist-info", "attrs", "25.3.0")
        report = self.report()
        row = next(row for row in report["packages"]["expected"] if row["name"] == "attrs")
        self.assertEqual((row["installed"], row["state"], report["packages"]["duplicates"]), ("26.1.0", "ready", {}), "A pip remnant is not a package.")
        self.metadata("attrs-25.3.0.dist-info", "attrs", "25.3.0")
        row = next(row for row in self.report()["packages"]["expected"] if row["name"] == "attrs")
        self.assertEqual(row["state"], "mismatch")
        self.assertEqual(set(row["installed"].split(" and ")), {"26.1.0", "25.3.0"})

    def test_real_source_import_needs_the_checkout_source(self):
        (self.project.root / "ontokin/__init__.py").unlink()
        self.assertEqual(self.core()[1]["source-import"]["state"], "mismatch", "An empty directory is no source package.")
        shutil.rmtree(self.project.root / "ontokin")
        (self.site / "ontokin").mkdir()
        (self.site / "ontokin/__init__.py").write_text("", encoding="utf-8")
        self.assertIn("not from the checkout", self.core()[1]["source-import"]["detail"])


class VisualTests(DoctorCase):
    def visual(self, **overrides):
        return {item["id"]: item["state"] for item in self.project.collect(**overrides)["readiness"]["visual-verification"]["checks"]}

    def test_absent_and_wrong_node_are_different(self):
        self.assertEqual((self.visual()["node"], self.visual()["npm"]), ("missing", "missing"))
        self.project.node()
        self.assertEqual((self.visual()["node"], self.visual()["npm"]), ("ready", "ready"))
        for version in ("v25.9.0\n", "v2.2.0\n", "unreadable\n", ""):
            with self.subTest(version=version):
                self.project.node_version = version
                self.assertEqual(self.visual()["node"], "mismatch")
        self.assertFalse([call for call in self.project.calls if Path(call[0]).name == "npm"], "npm is never run")
        (self.project.directory / "node/lib/node_modules/npm/package.json").write_text('{"name": "other"}', encoding="utf-8")
        self.assertEqual(self.visual()["npm"], "not_checked")

    def test_every_locked_package_of_the_platform_counts(self):
        self.project.node()
        states = self.visual()
        self.assertEqual((states["npm"], states["npm-dependencies"], states["chromium"]), ("ready", "missing", "not_checked"))
        self.project.node_modules()
        self.assertEqual(self.visual()["npm-dependencies"], "ready")
        rows = {row["name"] for row in self.project.collect()["visual"]["npm_dependencies"]}
        self.assertLessEqual({"@esbuild/darwin-arm64", "playwright-core", "esbuild", "three"}, rows)
        self.assertNotIn("@esbuild/linux-x64", rows)
        for name, version in (("playwright-core", "1.40.0"), ("three", "0.179.0"), ("@esbuild/darwin-arm64", "0.25.9")):
            with self.subTest(package=name):
                self.project.node_modules(**{name: version})
                self.assertEqual(self.visual()["npm-dependencies"], "mismatch")
                self.project.node_modules()
        shutil.rmtree(self.project.root / "tools/node_modules/@esbuild")
        self.assertEqual(self.visual()["npm-dependencies"], "missing")
        (self.project.root / "tools/package-lock.json").write_text("{", encoding="utf-8")
        self.assertNotEqual(self.visual()["npm-dependencies"], "ready")

    def test_shared_dependency_directory_is_a_mismatch(self):
        self.project.node()
        self.project.node_modules()
        directory = self.project.root / "tools/node_modules"
        directory.rename(self.project.directory / "shared-modules")
        directory.symlink_to(self.project.directory / "shared-modules", target_is_directory=True)
        self.assertEqual(self.visual()["npm-dependencies"], "mismatch")

    def test_browser_state_follows_the_installed_playwright(self):
        self.project.node()
        self.project.node_modules()
        self.assertEqual(self.visual()["chromium"], "missing")
        self.project.browser()
        self.assertEqual(self.visual()["chromium"], "ready")
        (self.project.root / "tools/node_modules/playwright-core/browsers.json").write_text('{"browsers": []}', encoding="utf-8")
        self.assertEqual(self.visual()["chromium"], "not_checked")

    def test_profile_is_ready_only_with_its_base_profiles(self):
        self.project.node()
        self.project.node_modules()
        self.project.browser()
        self.assertEqual(self.state(self.project.collect(), "visual-verification"), "missing")
        self.project.create_environment()
        self.assertEqual(self.state(self.project.collect(), "visual-verification"), "ready")


class SectionTests(DoctorCase):
    def test_checkout_distinguishes_local_head_tracking_ref_and_live_remote(self):
        head = self.project.git("rev-parse", "HEAD")
        (self.project.root / "untracked.txt").write_text("new", encoding="utf-8")
        (self.project.root / "pyproject.toml").write_text("changed", encoding="utf-8")
        self.project.git("remote", "add", "origin", "git@example.invalid:Omegapy/OntoKin.git")
        report = self.project.collect()
        checkout = report["checkout"]
        self.assertEqual((checkout["head"], checkout["is_checkout"], checkout["linked_worktree"]), (head, True, False))
        self.assertEqual(checkout["tree"], self.project.git("rev-parse", "HEAD^{tree}"))
        self.assertEqual(checkout["tracked_modifications"], [" M pyproject.toml"])
        self.assertEqual((checkout["untracked"], checkout["untracked_count"], checkout["stashes"]), (["untracked.txt"], 1, 0))
        self.assertEqual(checkout["origin_repository"], "Omegapy/OntoKin")
        self.assertNotIn("git@", json.dumps(report))
        self.assertEqual(report["remote"]["state"], "not_checked")
        self.assertFalse([call for call in self.project.calls if "ls-remote" in call])
        self.project.handlers.append(lambda argv: self.project.result(argv, out=f"{'1' * 40}\trefs/heads/main\n") if "ls-remote" in argv else None)
        remote = self.project.collect(online=True)["remote"]
        self.assertEqual((remote["state"], remote["heads"], remote["stale_tracking_refs"]), ("ready", {"main": "1" * 40}, ["main"]))
        self.project.handlers[-1] = lambda argv: self.project.result(argv, code=128, err="Could not read from remote repository.\n") if "ls-remote" in argv else None
        self.assertEqual(self.project.collect(online=True)["remote"]["state"], "not_checked")
        forbidden = {"fetch", "pull", "push", "commit", "checkout", "install", "ci", "update", "add"}
        self.assertFalse([call for call in self.project.calls if forbidden & set(call)])

    def test_unpublished_commits_of_every_head_and_stashes_are_counted(self):
        self.assertEqual(self.project.collect()["checkout"]["unpublished_commits"], 1)
        self.project.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.assertEqual(self.project.collect()["checkout"]["unpublished_commits"], 0)
        self.project.git("checkout", "--quiet", "--detach")
        self.project.git("commit", "--quiet", "--allow-empty", "--no-verify", "-m", "On no branch")
        self.assertEqual(self.project.collect()["checkout"]["unpublished_commits"], 1)
        self.project.git("checkout", "--quiet", "-")
        other = self.project.directory / "linked"
        self.project.git("worktree", "add", "--quiet", "--detach", str(other))
        subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@example.invalid", "-C", str(other), "commit", "--quiet", "--allow-empty", "--no-verify", "-m", "Elsewhere"], check=True)
        self.assertEqual(self.project.collect()["checkout"]["unpublished_commits"], 1)
        (self.project.root / "pyproject.toml").write_text("changed", encoding="utf-8")
        self.project.git("stash", "push", "--quiet")
        self.assertEqual(self.project.collect()["checkout"]["stashes"], 1)

    def test_unreadable_state_is_never_reported_as_clean(self):
        self.project.create_environment()
        (self.project.root / ".git/index").write_bytes(b"not an index")
        report = self.project.collect()
        self.assertEqual(self.check(report, "git", "core")["state"], "mismatch")
        self.assertIsNone(report["checkout"]["tracked_modifications"])
        self.assertIsNone(report["checkout"]["untracked_count"])
        self.assertIn("not read: status", doctor.render(report))
        self.assertIn("unread tracked modifications", doctor.render(report))

    def test_linked_worktree_is_reported(self):
        other = self.project.directory / "linked"
        self.project.git("worktree", "add", "--quiet", "-b", "second", str(other))
        checkout = doctor.checkout_section(other)
        self.assertEqual((checkout["branch"], checkout["linked_worktree"], len(checkout["worktrees"])), ("second", True, 2))

    def test_root_outside_a_checkout_is_a_mismatch(self):
        shutil.rmtree(self.project.root / ".git")
        self.project.create_environment()
        report = self.project.collect()
        self.assertEqual(self.check(report, "git", "core")["state"], "mismatch")
        self.assertEqual(report["storage"]["state"], "not_checked")

    def test_commands_run_without_redirection_or_lazy_fetching(self):
        injected = {"GIT_DIR": "/elsewhere", "PYTHONPATH": "/elsewhere", "PIP_INDEX_URL": "https://example.invalid", "VIRTUAL_ENV": "/elsewhere", "KEPT": "yes"}
        with patch.dict(os.environ, injected):
            environment = doctor.clean_environment()
            self.project.collect()
        self.assertEqual((environment["GIT_NO_LAZY_FETCH"], environment["PYTHONDONTWRITEBYTECODE"], environment["KEPT"]), ("1", "1", "yes"))
        for used in self.project.environments:
            self.assertFalse({"GIT_DIR", "PYTHONPATH", "PIP_INDEX_URL", "VIRTUAL_ENV"} & set(used or environment))

    def test_storage_needs_a_client_only_when_files_are_selected(self):
        report = self.project.collect()
        self.assertEqual((report["storage"]["state"], report["storage"]["applicable"], report["storage"]["client_version"]), ("ready", False, "3.7.1"))
        (self.project.root / ".gitattributes").write_text("*.zip filter=lfs\n", encoding="utf-8")
        (self.project.root / "a.zip").write_text("version https://git-lfs.github.com/spec/v1\noid sha256:" + "0" * 64 + "\nsize 1\n", encoding="utf-8")
        self.project.git("-c", "filter.lfs.required=false", "-c", "filter.lfs.clean=cat", "add", ".gitattributes", "a.zip")
        storage = self.project.collect()["storage"]
        self.assertEqual((storage["state"], storage["lfs_files"], storage["unhydrated"]), ("mismatch", ["a.zip"], ["a.zip"]))
        self.project.handlers.append(lambda argv: self.project.result(argv, out="git-lfs/3.8.1 (GitHub)\n") if argv[:2] == ["git", "lfs"] else None)
        self.assertEqual(self.project.collect()["storage"]["state"], "missing")
        (self.project.root / "a.zip").write_bytes(b"PK hydrated")
        self.assertEqual(self.project.collect()["storage"]["state"], "ready")
        self.project.handlers[-1] = lambda argv: self.project.result(argv, code=1, err="git: 'lfs' is not a git command") if argv[:2] == ["git", "lfs"] else None
        self.assertEqual(self.project.collect()["storage"]["state"], "missing")

    def test_workflow_reads_single_and_mode_specific_entry_points(self):
        folder = self.project.root / "docs/workflow/tasks/T1"
        folder.mkdir(parents=True)
        (folder / "task.json").write_text(json.dumps({"status": "in_progress"}), encoding="utf-8")
        (folder / "SESSION.md").write_text("# Session\n", encoding="utf-8")
        registry, current = self.project.root / "docs/workflow/registry.json", self.project.root / "docs/workflow/CURRENT.json"
        current.write_text(json.dumps({"active_task": "T1", "latest_task": "T1", "next_action": {"status": "ready"}}), encoding="utf-8")
        registry.write_text(json.dumps({"entrypoint": "CHATGPT-START-HERE.md", "task_root": "docs/workflow/tasks", "current": "docs/workflow/CURRENT.json"}), encoding="utf-8")
        workflow = self.project.collect()["workflow"]
        self.assertEqual(workflow["entry_points"], {"registered": "CHATGPT-START-HERE.md"})
        self.assertEqual((workflow["selected_task"], workflow["selected_task_status"], workflow["latest_checkpoint"]),
                         ("T1", "in_progress", "docs/workflow/tasks/T1/SESSION.md"))
        self.assertEqual(workflow["structure_check"]["state"], "not_checked")
        registry.write_text(json.dumps({"modes": {"local": {"entrypoint": "LOCAL-START-HERE.md"}, "browser": {"entrypoint": "CHATGPT-START-HERE.md"}, "odd": "text"}}), encoding="utf-8")
        current.write_text(json.dumps({"active_task": None, "latest_task": "T1", "checkpoint": {"session": "elsewhere.md"}}), encoding="utf-8")
        workflow = self.project.collect()["workflow"]
        self.assertEqual(workflow["entry_points"], {"local": "LOCAL-START-HERE.md", "browser": "CHATGPT-START-HERE.md", "odd": None})
        self.assertEqual(workflow["latest_checkpoint"], "elsewhere.md")

    def test_structure_check_result_is_reported_as_it_is(self):
        tool = self.project.root / "tools/chat_workflow.py"
        for output, state in (({"passed": True, "tasks_checked": 3, "errors": []}, "ready"), ({"passed": False, "tasks_checked": 1, "errors": ["broken pointer"]}, "mismatch"), (None, "not_checked")):
            with self.subTest(state=state):
                tool.write_text(f"print({json.dumps(output)!r})\n" if output else "raise SystemExit('no report')\n", encoding="utf-8")
                self.assertEqual(self.project.collect()["workflow"]["structure_check"]["state"], state)


class ReportTests(DoctorCase):
    def test_diagnosis_changes_nothing(self):
        for prepare in (lambda: None, self.project.create_environment):
            prepare()
            before = self.project.snapshot()
            self.project.collect()
            self.assertTrue(self.project.snapshot() == before, "Diagnosis changed a file.")

    def test_human_and_json_output_cover_every_area(self):
        self.project.create_environment()
        report = self.project.collect()
        self.assertLessEqual(set(AREAS), set(report))
        text = doctor.render(report)
        for heading in ("Readiness by profile", "Checkout", "Python", "Packages", "Specification", "Visual tools", "Storage", "Workflow", "Remote", "Native experiments"):
            self.assertIn("\n" + heading + "\n", text)
        for name in report["readiness"]:
            self.assertIn(name, text)
        json.dumps(report, allow_nan=False)

    def test_portable_report_names_no_machine_path(self):
        self.project.create_environment()
        other = self.project.directory / "linked"
        self.project.git("worktree", "add", "--quiet", "-b", "second", str(other))
        report = self.project.collect()
        report["note"] = os.path.join(tempfile.gettempdir(), "unrelated")
        text = json.dumps(doctor.portable(report, doctor.path_labels(self.project.root, report["checkout"]["worktrees"])))
        self.assertNotIn(str(self.project.directory), text)
        self.assertNotIn(tempfile.gettempdir(), text)
        self.assertNotIn(str(Path.home()) + "/", text)
        self.assertIn("<root>/.venv", text)

    def test_command_line_runs_without_site_packages_and_writes_only_a_new_report(self):
        report = self.project.directory / "reports/doctor.json"
        command = [sys.executable, "-I", "-S", "-B", str(REPOSITORY / "tools/doctor_local.py"), "--root", str(self.project.root)]
        before = self.project.snapshot()
        done = subprocess.run([*command, "--json"], capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertIn(json.loads(done.stdout)["selected"]["state"], {"missing", "unsupported"})
        self.assertTrue(self.project.snapshot() == before, "Diagnosis changed a file.")
        done = subprocess.run([*command, "--output", str(report)], capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertTrue(report.is_file())
        kept = report.read_bytes()
        done = subprocess.run([*command, "--output", str(report)], capture_output=True, text=True, timeout=120)
        self.assertEqual((done.returncode, report.read_bytes()), (2, kept))

    def test_exit_status_follows_the_selected_profile(self):
        self.project.create_environment()
        ready, output = self.project.collect(), io.StringIO()
        with patch.object(doctor, "collect", return_value=ready), redirect_stdout(output):
            self.assertEqual(doctor.main(["--root", str(self.project.root), "--portable-paths", "--json"]), 0)
        self.assertNotIn(str(self.project.root), output.getvalue())
        with patch.object(doctor, "collect", return_value=self.project.collect("visual-verification")), redirect_stdout(io.StringIO()):
            self.assertEqual(doctor.main(["--profile", "visual-verification"]), 1)

    def test_command_line_reports_an_unusable_specification_or_profile(self):
        errors = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(errors):
            self.assertEqual(doctor.main(["--root", str(self.project.root), "--profile", "everything"]), 2)
            (self.project.root / doctor.SPECIFICATION).unlink()
            self.assertEqual(doctor.main(["--root", str(self.project.root)]), 2)
        self.assertEqual(errors.getvalue().count("The doctor could not run"), 2)


if __name__ == "__main__":
    unittest.main()
