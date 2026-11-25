#!/usr/bin/env python3
"""Diagnose OntoKin's local development environment without changing it.

The tool reads the tracked specification tools/local-environment.json and reports
the checkout, Python, packages, specification, visual tools, storage, workflow and
the readiness of each profile. It installs, updates, fetches, publishes and repairs
nothing, and it writes a file only when --output names a new one. Remote state is
read only with --online. It uses the standard library alone, so it can diagnose an
interpreter or environment that has none of the verification packages.

A ready profile states that its tools are present. It is not task completion,
native experiment acceptance or product qualification.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # Diagnosis leaves no __pycache__ behind.

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import tempfile

try:
    import fcntl
except ImportError:  # Not on this platform.
    fcntl = None

ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = "tools/local-environment.json"
SPECIFICATION_SCHEMA = "ontokin.local-environment/1"
REPORT_SCHEMA = "ontokin.local-doctor/1"
STATES = ("ready", "missing", "mismatch", "unsupported", "not_checked")
DEFAULT_PROFILE = "python-verification"
LFS_MINIMUM = (3, 8, 1)
UNTRACKED_LIMIT = 50
INSTALL_TOOLS = {"pip"}
ENVIRONMENT_CHECKS = ("interpreter", "isolation", "packages", "imports", "pip-check", "native-reader")
NATIVE_NOTICE = ("Native and historical experiments keep their own contracts. This tool does not launch, "
                 "prepare or accept one, and a ready profile is not native qualification.")

# Runs inside the diagnosed interpreter, isolated and without writing bytecode. The package version is
# the one importlib.metadata resolves; a second metadata directory of the same package is a duplicate.
PROBE = r"""
import importlib, importlib.util, json, os, platform, re, sys, sysconfig
from importlib import metadata
from urllib.parse import unquote, urlsplit
place = lambda value: os.path.realpath(value) if value else None
try:
    source = importlib.util.find_spec("ontokin")
    source = place(source.origin) if source else None
except BaseException as error:
    source = type(error).__name__ + ": " + str(error)[:200]
imports = {}
for name in json.loads(sys.argv[1]):
    try:
        imports[name] = {"ok": True, "file": place(getattr(importlib.import_module(name), "__file__", None))}
    except BaseException as error:
        imports[name] = {"ok": False, "file": None, "error": (type(error).__name__ + ": " + str(error))[:300]}
packages, places, duplicates, editable, seen = {}, {}, {}, {}, {}
for distribution in metadata.distributions():
    name, folder = distribution.metadata["Name"], str(getattr(distribution, "_path", ""))
    if not name or os.path.basename(folder).startswith("~"):
        continue
    key = re.sub(r"[-_.]+", "-", name).lower()
    if key in seen:
        duplicates.setdefault(seen[key], [packages[seen[key]]]).append(distribution.version)
        continue
    seen[key] = name
    packages[name], places[name] = metadata.version(name), place(folder)
    try:
        direct = json.loads(distribution.read_text("direct_url.json") or "{}")
        if direct.get("dir_info", {}).get("editable"):
            editable[name] = place(unquote(urlsplit(direct["url"]).path))
    except Exception as error:
        editable[name] = type(error).__name__
print(json.dumps({
    "implementation": platform.python_implementation(), "version": platform.python_version(),
    "build": list(platform.python_build()), "compiler": platform.python_compiler(),
    "executable": sys.executable, "base_executable": getattr(sys, "_base_executable", None),
    "prefix": sys.prefix, "base_prefix": sys.base_prefix, "base_prefix_real": os.path.realpath(sys.base_prefix),
    "system": platform.system(), "machine": platform.machine(), "os_version": platform.mac_ver()[0] or platform.release(),
    "platform_tag": sysconfig.get_platform(), "sys_path": [place(entry) for entry in sys.path if entry],
    "site_packages": place(sysconfig.get_path("purelib")), "packages": packages, "places": places,
    "duplicates": duplicates, "editable": editable, "source_package": source, "imports": imports}))
"""


class SpecificationError(ValueError):
    """The tracked specification cannot be used as written."""


def execute(argv, cwd=None, timeout=60, env=None, keep=()) -> dict:
    """Run one command without a shell and return what happened; never raise for its result."""
    argv = [str(part) for part in argv]
    try:
        done = subprocess.run(argv, cwd=None if cwd is None else str(cwd), env=env, timeout=timeout, pass_fds=keep,
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (OSError, subprocess.SubprocessError) as error:
        return {"argv": argv, "code": None, "out": "", "err": "", "error": f"{type(error).__name__}: {error}"}
    return {"argv": argv, "code": done.returncode, "out": done.stdout.decode("utf-8", "replace"),
            "err": done.stderr.decode("utf-8", "replace"), "error": None}


def failure_text(result: dict) -> str:
    text = result["error"] or result["err"].strip() or result["out"].strip() or f"exit status {result['code']}"
    return text.splitlines()[-1][:300]


def clean_environment() -> dict:
    """The caller's environment without Python, pip and Git redirection, and with no lazy object fetch."""
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("GIT_", "PYTHON", "PIP_")) and key not in {"VIRTUAL_ENV", "__PYVENV_LAUNCHER__"}}
    environment.update(PYTHONDONTWRITEBYTECODE="1", PIP_DISABLE_PIP_VERSION_CHECK="1",
                       GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1")
    return environment


def inside(path, *directories) -> bool:
    """Whether a resolved path is one of the directories or lies below one."""
    return any(path == directory or path.startswith(directory.rstrip(os.sep) + os.sep) for directory in directories if directory)


def same_place(first: str, second: str) -> bool:
    """Whether two paths name one place, also where the file system ignores letter case."""
    if os.path.realpath(first) == os.path.realpath(second):
        return True
    try:
        return os.path.samefile(first, second)
    except OSError:
        return False


def canonical(path) -> Path:
    """The resolved path, in the letter case that the file system itself records where it can tell."""
    resolved = Path(path).resolve()
    try:
        descriptor = os.open(str(resolved), os.O_RDONLY)
    except OSError:
        return resolved
    try:
        return Path(os.fsdecode(fcntl.fcntl(descriptor, fcntl.F_GETPATH, bytes(1024)).rstrip(b"\0")))
    except (AttributeError, OSError):
        return resolved
    finally:
        os.close(descriptor)


def host_machine(run=execute) -> str:
    """The machine's architecture, also when this tool itself runs translated under Rosetta."""
    machine = platform.machine()
    if (platform.system(), machine) == ("Darwin", "x86_64") and run(["sysctl", "-in", "sysctl.proc_translated"], timeout=10)["out"].strip() == "1":
        return "arm64"
    return machine


def git(root: Path, *arguments, run=execute, timeout=60) -> dict:
    return run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
               timeout=timeout, env=clean_environment())


def digest(path: Path):
    if not path.is_file():
        return None
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return "sha256:" + value.hexdigest()


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


# --- Specification ---------------------------------------------------------

def load_specification(root: Path) -> dict:
    path = root / SPECIFICATION
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise SpecificationError(f"Cannot read {SPECIFICATION}: {error}") from error
    if not isinstance(spec, dict) or spec.get("schema") != SPECIFICATION_SCHEMA:
        raise SpecificationError(f"{SPECIFICATION}: expected schema {SPECIFICATION_SCHEMA}")
    try:
        profiles = spec["profiles"]
        interpreter = spec["interpreter"]
        if not re.fullmatch(r"\d+\.\d+\.\d+", interpreter["version"]) or not interpreter["implementation"]:
            raise SpecificationError(f"{SPECIFICATION}: the interpreter needs an implementation and an exact patch version")
        directory = spec["environment"]["directory"]
        if not re.fullmatch(r"\.?[A-Za-z0-9_-]+", directory):
            raise SpecificationError(f"{SPECIFICATION}: the environment directory must be one plain name")
        for key, entry in spec["platforms"].items():
            entry["system"], entry["machine"]
        for name, profile in profiles.items():
            if profile["kind"] not in {"environment", "on-demand", "external", "unconfigured"}:
                raise SpecificationError(f"{SPECIFICATION}: profile {name} has an unknown kind")
            profile_chain(spec, name)
            if not profile["readiness_checks"]:
                raise SpecificationError(f"{SPECIFICATION}: profile {name} names no readiness check")
    except (KeyError, TypeError, AttributeError) as error:
        raise SpecificationError(f"{SPECIFICATION}: incomplete specification: {error!r}") from error
    return spec


def profile_chain(spec: dict, name: str) -> list:
    """The profile and the profiles it extends, base first."""
    chain, current = [], name
    while current is not None:
        if current not in spec["profiles"] or current in chain:
            raise SpecificationError(f"{SPECIFICATION}: profile {name} extends an unknown or cyclic profile {current}")
        chain.append(current)
        current = spec["profiles"][current].get("extends")
    return chain[::-1]


def platform_key(spec: dict, system: str, machine: str):
    for key, entry in spec["platforms"].items():
        if (entry["system"], entry["machine"]) == (system, machine):
            return key
    return None


def parse_pins(text: str) -> dict:
    pins = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)"
                             r"(?: --hash=sha256:([0-9a-f]{64}))?", line)
        if match is None:
            raise SpecificationError(f"Expected an exact NAME==VERSION pin: {line}")
        name = normalize(match[1])
        if name in pins:
            raise SpecificationError(f"Repeated pin: {match[1]}")
        pins[name] = {"name": match[1], "version": match[2], "sha256": match[3], "line": line}
    if not pins:
        raise SpecificationError("The pin file names no package")
    return pins


def parse_lock(text: str) -> dict:
    pins = parse_pins(text)
    unhashed = [pin["name"] for pin in pins.values() if pin["sha256"] is None]
    if unhashed:
        raise SpecificationError("Every lock entry needs a SHA-256 hash: " + ", ".join(unhashed))
    return pins


def select_lock(spec: dict, profile: str, key, series: str) -> dict:
    """Choose the committed lock for this platform; an incompatible lock is never selected."""
    locks = {}
    for name in profile_chain(spec, profile):
        locks.update(spec["profiles"][name].get("locks", {}))
    if not locks:
        return {"state": "ready", "required": False, "path": None, "detail": "The profile installs no locked package."}
    entry = locks.get(key) if key is not None else None
    if entry is None:
        return {"state": "unsupported", "required": True, "path": None,
                "detail": f"No committed lock is valid for this platform; available: {', '.join(sorted(locks))}."}
    if entry["python"] != series:
        return {"state": "unsupported", "required": True, "path": entry["path"],
                "detail": f"{entry['path']} is valid for Python {entry['python']}, not {series}."}
    return {"state": "ready", "required": True, "path": entry["path"], "provenance": entry.get("provenance"),
            "detail": f"{entry['path']} is valid for this platform and Python {series}."}


def packages_of(spec: dict, profile: str) -> list:
    return [package for name in profile_chain(spec, profile) for package in spec["profiles"][name].get("packages", [])]


def lock_problems(root: Path, relative: str, provenance, expected: dict) -> list:
    """Differences between one committed lock, its provenance and the adopted pins."""
    path = root / relative
    if not path.is_file():
        return [f"{relative}: missing"]
    try:
        pins = parse_lock(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SpecificationError) as error:
        return [f"{relative}: {error}"]
    problems = []
    if {name: pin["version"] for name, pin in pins.items()} != expected:
        problems.append(f"{relative}: its versions differ from the adopted pins")
    if provenance:
        try:
            record = json.loads((root / provenance).read_text(encoding="utf-8"))
            if "sha256:" + record["lock"]["sha256"] != digest(path):
                problems.append(f"{provenance}: names a different lock digest")
            recorded = {normalize(wheel["name"]): (wheel["version"], wheel["sha256"]) for wheel in record["wheels"]}
            if recorded != {name: (pin["version"], pin["sha256"]) for name, pin in pins.items()}:
                problems.append(f"{provenance}: its wheels differ from the lock entries")
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
            problems.append(f"{provenance}: unreadable provenance ({type(error).__name__})")
    return problems


def profile_problems(root: Path, spec: dict, name: str) -> list:
    """Disagreements among one profile, its pin files, its locks and its npm manifest."""
    profile, problems, sources = spec["profiles"][name], [], {}
    packages = profile.get("packages", [])
    expected = {normalize(package["name"]): package["version"] for package in packages}
    for package in packages:
        source = package["pin"]
        try:
            if source not in sources:
                sources[source] = parse_pins((root / source).read_text(encoding="utf-8"))
            pin = sources[source].get(normalize(package["name"]))
            if pin is None or pin["version"] != package["version"]:
                problems.append(f"{name}: {package['name']} {package['version']} differs from {source}")
        except (OSError, UnicodeError, SpecificationError) as error:
            problems.append(f"{source}: {error}")
    for entry in profile.get("locks", {}).values():
        problems.extend(lock_problems(root, entry["path"], entry.get("provenance"), expected))
    if "npm_manifest" in profile:
        try:
            manifest = json.loads((root / profile["npm_manifest"]).read_text(encoding="utf-8"))
            if manifest.get("devDependencies") != profile["npm_dependencies"]:
                problems.append(f"{name}: npm dependencies differ from {profile['npm_manifest']}")
        except (OSError, UnicodeError, ValueError, AttributeError) as error:
            problems.append(f"{profile['npm_manifest']}: {error}")
    return sorted(set(problems))


def specification_problems(root: Path, spec: dict) -> list:
    return sorted({problem for name in spec["profiles"] for problem in profile_problems(root, spec, name)})


def specification_section(root: Path, spec: dict, profile: str, key, series: str) -> dict:
    paths = {SPECIFICATION, "pyproject.toml"}
    for entry in spec["profiles"].values():
        paths.update(package["pin"] for package in entry.get("packages", []))
        for lock in entry.get("locks", {}).values():
            paths.add(lock["path"])
            if lock.get("provenance"):
                paths.add(lock["provenance"])
        paths.update(entry[name] for name in ("npm_manifest", "npm_lock", "preflight") if name in entry)
    return {"selected_profile": profile, "interpreter": spec["interpreter"]["version"],
            "environment_directory": spec["environment"]["directory"], "platform": key,
            "selected_lock": select_lock(spec, profile, key, series),
            "digests": {path: digest(root / path) for path in sorted(paths)},
            "problems": specification_problems(root, spec)}


# --- Python and packages ---------------------------------------------------

def distribution_of(facts: dict) -> dict:
    """Name the installation an interpreter comes from, from its resolved base location."""
    real = facts.get("base_prefix_real") or facts.get("base_prefix") or ""
    cellar = re.search(r"/Cellar/([^/]+)/", real)
    if cellar:
        return {"name": "Homebrew", "formula": cellar[1]}
    for marker, name in (("/uv/python/", "uv-managed"), ("/.pyenv/versions/", "pyenv"), ("conda", "Conda"),
                         ("/CommandLineTools/", "Apple Command Line Tools"), ("/Xcode.app/", "Apple Xcode"),
                         ("/Library/Frameworks/Python.framework", "python.org")):
        if marker in real:
            return {"name": name, "formula": None}
    return {"name": "system" if real == "/usr" or real.startswith("/usr/") else "unknown", "formula": None}


def probe(python: Path, imports=(), run=execute) -> dict:
    result = run([str(python), "-I", "-B", "-c", PROBE, json.dumps(list(imports))], timeout=60, env=clean_environment())
    if result["code"] != 0:
        return {"ok": False, "error": failure_text(result)}
    try:
        facts = json.loads(result["out"])
    except ValueError:
        return {"ok": False, "error": "The interpreter returned no readable facts."}
    facts.update(ok=True, distribution=distribution_of(facts))
    return facts


def interpreter_differences(spec: dict, key, facts: dict) -> list:
    """How one interpreter differs from the specified one; empty means compliant."""
    wanted, differences = spec["interpreter"], []
    if facts["implementation"] != wanted["implementation"]:
        differences.append(f"implementation {facts['implementation']}, expected {wanted['implementation']}")
    if facts["version"] != wanted["version"]:
        differences.append(f"version {facts['version']}, expected {wanted['version']}")
    entry = spec["platforms"].get(key) if key is not None else None
    if entry is not None and (facts["system"], facts["machine"]) != (entry["system"], entry["machine"]):
        differences.append(f"built for {facts['system']} {facts['machine']}, expected {entry['system']} {entry['machine']}")
    distribution = wanted.get("distributions", {}).get(key, {})
    if distribution.get("name") and facts["distribution"]["name"] != distribution["name"]:
        differences.append(f"distribution {facts['distribution']['name']}, expected {distribution['name']}")
    return differences


def find_interpreters(spec: dict, key, run=execute, which=shutil.which) -> list:
    """Interpreters of the specified command in the specified locations and on PATH, each probed once."""
    distribution = spec["interpreter"].get("distributions", {}).get(key, {})
    command = distribution.get("command", "python" + ".".join(spec["interpreter"]["version"].split(".")[:2]))
    paths = [str(Path(directory) / command) for directory in distribution.get("search", [])]
    found = which(command)
    if found:
        paths.append(found)
    candidates, seen = [], set()
    for path in paths:
        if not os.path.exists(path) or os.path.realpath(path) in seen:
            continue
        seen.add(os.path.realpath(path))
        candidates.append(candidate(spec, key, path, probe(Path(path), run=run)))
    return candidates


def candidate(spec: dict, key, path, facts: dict) -> dict:
    """One interpreter considered as the base of an environment."""
    differences = interpreter_differences(spec, key, facts) if facts["ok"] else [facts["error"]]
    if facts["ok"] and facts["prefix"] != facts["base_prefix"]:
        differences.append("belongs to a virtual environment")
    return {"path": str(path), "ok": facts["ok"], "version": facts.get("version"), "implementation": facts.get("implementation"),
            "distribution": facts.get("distribution"), "differences": differences}


def read_configuration(path: Path) -> dict:
    values = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.partition("=")
            if separator:
                values[name.strip().lower()] = value.strip()
    except (OSError, UnicodeError):
        return {}
    return values


def inspect_environment(root: Path, spec: dict, imports=(), run=execute) -> dict:
    """Observe the checkout's environment directory without repairing it."""
    directory = root / spec["environment"]["directory"]
    result = {"path": str(directory), "exists": directory.is_dir(), "symlink": None, "python": None, "configuration": {},
              "facts": None, "pip_check": None, "pip_error": None, "record": None}
    if directory.is_symlink():
        result.update(exists=True, symlink=os.path.realpath(str(directory)))
    if not result["exists"]:
        return result
    python = directory / "bin" / "python"
    result["configuration"] = read_configuration(directory / "pyvenv.cfg")
    if not python.exists():
        return result
    result["python"] = str(python)
    result["facts"] = probe(python, imports, run)
    if result["facts"]["ok"] and "pip" not in {normalize(name) for name in result["facts"]["packages"]}:
        result["pip_error"] = "pip is not installed"
    elif result["facts"]["ok"]:
        checked = run([str(python), "-I", "-B", "-m", "pip", "check"], timeout=120, env=clean_environment())
        if checked["error"] or checked["code"] and not checked["out"].strip():  # A conflict is reported on stdout.
            result["pip_error"] = "pip does not run: " + failure_text(checked)
        else:
            result["pip_check"] = {"code": checked["code"], "summary": failure_text(checked) if checked["code"] else checked["out"].strip()[:300]}
    record = directory / spec["environment"]["record"]
    if record.is_file():
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
            result["record"] = {"path": str(record), "sha256": digest(record), "updated_at": data.get("updated_at"),
                                "profile": data.get("profile"), "readable": True}
        except (OSError, UnicodeError, ValueError, AttributeError):
            result["record"] = {"path": str(record), "sha256": digest(record), "readable": False}
    return result


def check(identifier: str, state: str, detail: str) -> dict:
    if state not in STATES:
        raise ValueError(f"Unknown readiness state {state}")
    return {"id": identifier, "state": state, "detail": detail}


def usable(environment: dict) -> bool:
    return bool(environment["facts"] and environment["facts"]["ok"])


def core_checks(root: Path, spec: dict, key, environment: dict, checkout: dict, run=execute) -> list:
    directory = spec["environment"]["directory"]
    facts = environment["facts"]
    results = []
    if key is None:
        results.append(check("interpreter", "unsupported", "No supported platform entry matches this machine."))
    elif not environment["exists"]:
        results.append(check("interpreter", "missing", f"No environment at {directory}."))
    elif not usable(environment):
        why = facts["error"] if facts else f"{directory} holds no interpreter."
        results.append(check("interpreter", "mismatch", f"The environment interpreter does not run: {why}"))
    else:
        differences = interpreter_differences(spec, key, facts)
        created = environment["configuration"].get("version")
        if differences and created and created != facts["version"]:
            differences.append(f"the environment was created with {created}")
        results.append(check("interpreter", "mismatch" if differences else "ready",
                             "; ".join(differences) if differences else
                             f"{facts['implementation']} {facts['version']} ({facts['distribution']['name']})."))
    if not environment["exists"]:
        results.append(check("isolation", "missing", f"No environment at {directory}."))
    elif environment["symlink"]:
        results.append(check("isolation", "mismatch", f"{directory} is a symbolic link; each checkout needs its own environment."))
    elif not usable(environment):
        results.append(check("isolation", "not_checked", "The environment interpreter does not run."))
    else:
        problems, unknown = isolation_problems(root, environment)
        results.append(check("isolation", "mismatch", "; ".join(problems)) if problems else
                       check("isolation", "not_checked", unknown) if unknown else
                       check("isolation", "ready", "A real, isolated environment of this checkout."))
    if not checkout["git_available"]:
        results.append(check("git", "missing", f"Git could not be started: {checkout['problem']}"))
    elif not checkout["is_checkout"]:
        results.append(check("git", "mismatch", "The root is not the top of a Git checkout or worktree" + (f": {checkout['problem']}" if checkout["problem"] else ".")))
    elif checkout["unread"]:
        results.append(check("git", "mismatch", "Git could not read: " + "; ".join(checkout["unread"])))
    else:
        results.append(check("git", "ready", "The root is a Git checkout."))
    if not usable(environment):
        results.append(check("source-import", "not_checked", "No usable environment interpreter."))
    else:
        done = run([environment["python"], "-B", "-c", "import ontokin; print(ontokin.__file__ or '')"], cwd=root, timeout=60, env=clean_environment())
        place = os.path.realpath(done["out"].strip()) if done["code"] == 0 and done["out"].strip() else None
        expected = os.path.join(os.path.realpath(str(root)), "ontokin")
        results.append(check("source-import", "mismatch", failure_text(done)) if done["code"] != 0 else
                       check("source-import", "ready", "The source package imports from the checkout.") if place and inside(place, expected) else
                       check("source-import", "mismatch", f"ontokin is imported from {place or 'no source file'}, not from the checkout."))
    return results


def isolation_problems(root: Path, environment: dict):
    """What lets another location into the environment, and what could not be established about it."""
    facts, problems, here, top = environment["facts"], [], os.path.realpath(environment["path"]), os.path.realpath(str(root))
    if facts["prefix"] == facts["base_prefix"]:
        problems.append("it is not a virtual environment")
    if not same_place(facts["prefix"], here):
        problems.append("its interpreter belongs to another location")
    if environment["configuration"].get("include-system-site-packages", "").lower() != "false":
        problems.append("system site-packages are not excluded")
    if not facts["site_packages"] or not inside(facts["site_packages"], here):
        problems.append("its site-packages directory lies elsewhere")
    # An editable install of this checkout may add the checkout itself, and nothing else.
    foreign = [entry for entry in facts["sys_path"] if entry != top and not inside(entry, here) and
               (os.path.basename(entry) in {"site-packages", "dist-packages"} or not inside(entry, facts["base_prefix_real"]))]
    if foreign:
        problems.append("its import path leaves the environment: " + ", ".join(foreign))
    strangers = sorted(name for name, place in facts["places"].items() if not place or not inside(place, here) and os.path.dirname(place) != top)
    if strangers:
        problems.append("packages are installed elsewhere: " + ", ".join(strangers))
    others = sorted(f"{name} from {place}" for name, place in facts["editable"].items() if place != top)
    if others:
        problems.append("editable installs of other locations: " + ", ".join(others))
    if facts["source_package"] and not inside(facts["source_package"], here, os.path.join(top, "ontokin")):
        problems.append(f"ontokin is imported from {facts['source_package']}")
    _, separator, created = environment["configuration"].get("command", "").partition(" -m venv ")
    if not separator:
        return problems, "Where the environment was created is not recorded."
    starts = [0] + [index + 1 for index, letter in enumerate(created) if letter == " "]
    if not any(created[start:].startswith(os.sep) and same_place(created[start:], here) for start in starts):
        problems.append("it was created for another location and then copied or moved")
    return problems, None


def rebuild_reasons(environment: dict, core: list, verification: list, rows: list) -> list:
    """Why installing packages cannot make the existing environment ready, so that only a rebuild can."""
    if not environment["exists"]:
        return []
    found = [f"{item['id']}: {item['detail']}" for item in core if item["id"] in {"interpreter", "isolation"} and item["state"] in {"mismatch", "not_checked"}]
    if found or not usable(environment) or not rows:
        return found
    if environment["pip_check"] is None:
        return [f"pip: {environment['pip_error']}, so nothing can be installed"]
    twice = [f"{row['name']} is recorded as {row['installed']}" for row in rows if row["duplicate"]]
    if twice:
        return ["packages: " + "; ".join(twice)]
    if all(row["state"] == "ready" for row in rows):
        return [f"{item['id']}: {item['detail']}" for item in verification if item["id"] in {"imports", "pip-check", "native-reader"} and item["state"] != "ready"]
    return []


def package_rows(spec: dict, profile: str, environment: dict) -> list:
    installed, duplicates, here = {}, {}, os.path.realpath(environment["path"])
    if usable(environment):
        installed = {normalize(name): version for name, version in environment["facts"]["packages"].items()}
        duplicates = {normalize(name): versions for name, versions in environment["facts"]["duplicates"].items()}
    rows = []
    for package in packages_of(spec, profile):
        name = normalize(package["name"])
        actual, twice = installed.get(name), duplicates.get(name)
        imported = environment["facts"]["imports"].get(package["import"]) if usable(environment) else None
        error = None if imported is None else imported.get("error")
        if imported and imported["ok"] and not (imported["file"] and inside(imported["file"], here)):
            error = f"imported from {imported['file'] or 'no file'}, outside the environment"
        if not usable(environment):
            state = "not_checked" if environment["exists"] else "missing"
        else:
            state = "mismatch" if twice else "missing" if actual is None else "ready" if actual == package["version"] else "mismatch"
        rows.append({"name": package["name"], "expected": package["version"], "installed": " and ".join(twice) if twice else actual, "state": state,
                     "duplicate": bool(twice), "import": package["import"], "import_ok": None if imported is None else error is None, "import_error": error})
    return rows


def verification_checks(root: Path, spec: dict, key, environment: dict, run=execute) -> list:
    profile = spec["profiles"]["python-verification"]
    series = ".".join(spec["interpreter"]["version"].split(".")[:2])
    selected = select_lock(spec, "python-verification", key, series)
    if selected["state"] != "ready":
        results = [check("lock", selected["state"], selected["detail"])]
    elif not (root / selected["path"]).is_file():
        results = [check("lock", "missing", f"{selected['path']} is not present.")]
    else:
        problems = profile_problems(root, spec, "python-verification")
        results = [check("lock", "mismatch" if problems else "ready", "; ".join(problems) if problems else selected["detail"])]
    rows = package_rows(spec, "python-verification", environment)
    if not environment["exists"]:
        absent = f"No environment at {spec['environment']['directory']}."
        return results + [check(name, "missing" if name == "packages" else "not_checked", absent)
                          for name in ("packages", "imports", "pip-check", "native-reader")]
    if not usable(environment):
        return results + [check(name, "not_checked", "The environment interpreter does not run.")
                          for name in ("packages", "imports", "pip-check", "native-reader")]
    wrong = [f"{row['name']} {row['installed']}, expected {row['expected']}" for row in rows if row["state"] == "mismatch"]
    absent = [f"{row['name']} {row['expected']}" for row in rows if row["state"] == "missing"]
    results.append(check("packages", "mismatch" if wrong else "missing" if absent else "ready",
                         "; ".join(wrong + [f"not installed: {', '.join(absent)}"] * bool(absent))
                         if wrong or absent else f"{len(rows)} packages at their adopted versions."))
    # An absent package makes its dependents fail too; that is still an absence, not a conflict.
    failed = "missing" if absent and not wrong else "mismatch"
    broken = [row for row in rows if not row["import_ok"]]
    results.append(check("imports", failed, "; ".join(f"{row['import']}: {row['import_error']}" for row in broken)) if broken else
                   check("imports", "ready", f"{len(rows)} packages import."))
    pip = environment["pip_check"]
    results.append(check("pip-check", "not_checked", environment["pip_error"] or "pip is not available in the environment.") if pip is None else
                   check("pip-check", "ready" if pip["code"] == 0 else failed, pip["summary"] or "No conflict."))
    done = run([environment["python"], "-I", "-B", str(root / profile["preflight"])], cwd=root, timeout=60, env=clean_environment())
    results.append(check("native-reader", "ready" if done["code"] == 0 else failed,
                         done["out"].strip()[:300] if done["code"] == 0 else failure_text(done)))
    return results


# --- Visual tools ----------------------------------------------------------

def npm_version(npm):
    """Read npm's own manifest; running npm would write a log."""
    if not npm:
        return None
    for parent in Path(os.path.realpath(npm)).parents:
        manifest = parent / "package.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError):
                return None
            return data.get("version") if data.get("name") == "npm" else None
    return None


def browser_cache(directory: Path) -> Path:
    chosen = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if chosen:  # Playwright reads 0 as "inside its own package".
        return directory / "playwright-core" / ".local-browsers" if chosen == "0" else Path(chosen)
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "ms-playwright"


def locked_packages(root: Path, profile: dict, system: str, machine: str):
    """The entries of the committed npm lock that belong on this platform, or None when it is unreadable."""
    platform_names = ({"Darwin": "darwin", "Linux": "linux", "Windows": "win32"}.get(system, system.lower()),
                      {"x86_64": "x64", "AMD64": "x64", "aarch64": "arm64"}.get(machine, machine))
    entries = {}
    try:
        for place, entry in json.loads((root / profile["npm_lock"]).read_text(encoding="utf-8"))["packages"].items():
            elsewhere = entry.get("optional") and any(allowed and name not in allowed for allowed, name in
                                                      ((entry.get("os"), platform_names[0]), (entry.get("cpu"), platform_names[1])))
            if place.startswith("node_modules/") and not elsewhere:
                entries[place] = {"version": entry["version"], "integrity": entry.get("integrity")}
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return entries


def npm_dependencies(root: Path, profile: dict, system: str, machine: str) -> list:
    """Every locked package of this platform with the version installed at its place."""
    locked, directory = locked_packages(root, profile, system, machine), root / profile["npm_directory"]
    wanted = dict(profile["npm_dependencies"])
    wanted.update({"package-lock": "readable"} if locked is None else {place[len("node_modules/"):]: entry["version"] for place, entry in locked.items()})
    rows = []
    for name, expected in sorted(wanted.items()):
        place, actual = directory / name, None
        manifest = place / "package.json"
        if any(part.is_symlink() for part in (place, *place.parents) if part != directory and inside(str(part), str(directory))):
            actual = "a symbolic link"
        elif manifest.is_file():
            try:
                actual = json.loads(manifest.read_text(encoding="utf-8")).get("version") or "unreadable"
            except (OSError, UnicodeError, ValueError, AttributeError):
                actual = "unreadable"
        rows.append({"name": name, "expected": expected, "installed": actual, "direct": name in profile["npm_dependencies"]})
    return rows


def npm_record_problem(root: Path, profile: dict, system: str, machine: str):
    """Why npm's own record of the installation does not show the committed lock; manifests alone prove no installation."""
    locked = locked_packages(root, profile, system, machine)
    recorded = read_json(root / profile["npm_directory"] / ".package-lock.json").get("packages")
    if locked is None or not isinstance(recorded, dict):
        return "npm's own record of the installation is missing"
    differing = sorted(place[len("node_modules/"):] for place, entry in locked.items() if not isinstance(recorded.get(place), dict)
                       or (recorded[place].get("version"), recorded[place].get("integrity")) != (entry["version"], entry["integrity"]))
    return f"npm's own record of the installation differs for {', '.join(differing)}" if differing else None


def visual_section(root: Path, spec: dict, run=execute, which=shutil.which, node=None, cache=None, system=None, machine=None) -> dict:
    profile = spec["profiles"]["visual-verification"]
    node = node or which("node")
    npm = str(Path(node).parent / "npm") if node and (Path(node).parent / "npm").exists() else which("npm")
    version = None
    if node:
        done = run([node, "--version"], timeout=30, env=clean_environment())
        version = done["out"].strip() if done["code"] == 0 else None
    dependencies = npm_dependencies(root, profile, system or platform.system(), machine or platform.machine())
    directory = root / profile["npm_directory"]
    browser = {"state": "not_checked", "expected": None, "detail": "Playwright is not installed, so its expected browser revision is unknown."}
    manifest = directory / "playwright-core" / "browsers.json"
    if manifest.is_file():
        try:
            entries = json.loads(manifest.read_text(encoding="utf-8"))["browsers"]
            revision = next(entry["revision"] for entry in entries if entry["name"] == "chromium-headless-shell")
            place = (cache or browser_cache(directory)) / f"chromium_headless_shell-{revision}"
            present = (place / "INSTALLATION_COMPLETE").is_file()
            browser = {"state": "ready" if present else "missing", "expected": f"chromium_headless_shell-{revision}",
                       "detail": "Present in the Playwright cache." if present else "Not present in the Playwright cache."}
        except (OSError, UnicodeError, ValueError, KeyError, StopIteration, TypeError):
            browser = {"state": "not_checked", "expected": None, "detail": "The installed Playwright browser list is unreadable."}
    return {"node": {"path": node, "version": version, "target_major": profile["node_major"]},
            "npm": {"path": npm, "version": npm_version(npm)}, "npm_directory": profile["npm_directory"],
            "npm_directory_exists": directory.is_dir() or directory.is_symlink(), "npm_directory_symlink": directory.is_symlink(),
            "npm_dependencies": dependencies, "npm_record_problem": npm_record_problem(root, profile, system or platform.system(), machine or platform.machine()),
            "browser": browser}


def visual_checks(visual: dict) -> list:
    node, npm = visual["node"], visual["npm"]
    if not node["path"]:
        results = [check("node", "missing", "Node.js was not found.")]
    else:
        match = re.match(r"v(\d+)\.", node["version"] or "")
        right = bool(match) and int(match[1]) == node["target_major"]
        results = [check("node", "ready" if right else "mismatch",
                         f"Node.js {node['version'] or 'did not report a version'}; the target is Node.js {node['target_major']}.")]
    if not npm["path"]:
        results.append(check("npm", "missing", "npm was not found."))
    else:
        results.append(check("npm", "ready" if npm["version"] else "not_checked", f"npm {npm['version'] or 'version not established'}."))
    rows = visual["npm_dependencies"]
    wrong = [f"{row['name']} {row['installed']}, expected {row['expected']}" for row in rows if row["installed"] not in {None, row["expected"]}]
    absent = [f"{row['name']} {row['expected']}" for row in rows if row["installed"] is None]
    if visual["npm_directory_symlink"]:
        wrong.append(f"{visual['npm_directory']} is a symbolic link; each checkout needs its own dependencies")
    elif visual["npm_directory_exists"] and not absent and not wrong and visual["npm_record_problem"]:
        wrong.append(visual["npm_record_problem"])
    results.append(check("npm-dependencies", "mismatch" if wrong else "missing" if absent else "ready",
                         "; ".join(wrong + [f"not installed: {', '.join(absent)}"] * bool(absent))
                         if wrong or absent else f"All {len(rows)} packages of the committed lock for this platform are at their versions."))
    results.append(check("chromium", visual["browser"]["state"], visual["browser"]["detail"]))
    return results


# --- Checkout, storage, workflow and remote --------------------------------

def checkout_section(root: Path, run=execute) -> dict:
    section = {"root": str(root), "git_available": False, "is_checkout": False, "problem": None, "unread": []}
    top = git(root, "rev-parse", "--show-toplevel", run=run)
    section["git_available"] = top["error"] is None
    if top["code"] != 0:
        return dict(section, problem=failure_text(top))
    if not same_place(top["out"].rstrip("\n"), str(root)):
        return section

    def value(*arguments):
        result = git(root, *arguments, run=run)
        return result["out"].strip() if result["code"] == 0 else None

    def lines(*arguments):
        """The output lines, or None when Git could not answer; an unread state is never an empty one."""
        result = git(root, *arguments, run=run)
        if result["code"] != 0:
            section["unread"].append(f"{arguments[0]} ({failure_text(result)})")
            return None
        return [line for line in result["out"].split("\0" if "-z" in arguments else "\n") if line]

    directory, common = value("rev-parse", "--absolute-git-dir"), value("rev-parse", "--path-format=absolute", "--git-common-dir")
    untracked = lines("ls-files", "--others", "--exclude-standard", "-z")
    modified = lines("status", "--porcelain=v1", "--untracked-files=no")
    stashes = lines("stash", "list")
    listed = lines("worktree", "list", "--porcelain")
    heads = [line[len("HEAD "):] for line in listed or [] if line.startswith("HEAD ") and not set(line[len("HEAD "):]) <= {"0"}]
    unpublished = lines("rev-list", "--branches", *heads, "--not", "--remotes")
    upstream = value("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    counts = (value("rev-list", "--left-right", "--count", "HEAD...@{upstream}") or "").split() if upstream else []
    section.update({
        "is_checkout": True, "linked_worktree": directory != common,
        "branch": value("symbolic-ref", "--quiet", "--short", "HEAD"), "head": value("rev-parse", "HEAD"),
        "tree": value("rev-parse", "HEAD^{tree}"), "tracked_modifications": modified,
        "untracked_count": None if untracked is None else len(untracked), "untracked": None if untracked is None else untracked[:UNTRACKED_LIMIT],
        "stashes": None if stashes is None else len(stashes), "origin_repository": repository_name(value("config", "--get", "remote.origin.url") or ""),
        "upstream": upstream, "ahead_of_tracking_ref": int(counts[0]) if len(counts) == 2 else None,
        "behind_tracking_ref": int(counts[1]) if len(counts) == 2 else None,
        "tracking_refs": dict(line.split(" ", 1)[::-1] for line in lines("for-each-ref", "--format=%(objectname) %(refname:short)", "refs/remotes/origin") or []
                              if not line.endswith("/HEAD") and not line.endswith(" origin")),
        "unpublished_commits": None if unpublished is None else len(unpublished),
        "worktrees": [line[len("worktree "):] for line in listed or [] if line.startswith("worktree ")],
        "note": "Local observation only. A tracking ref is the last fetched state, not the live remote."})
    return section


def repository_name(url: str):
    """OWNER/NAME of a hosted remote; a local path names no repository."""
    match = re.fullmatch(r"(?:(?!file:)[A-Za-z][A-Za-z0-9+.-]*://[^/\s]+/|[^/:\s]+:(?!//))([^/:\s]+/[^/:\s]+?)(?:\.git)?/?", url)
    return match[1] if match else None


def lfs_version(run=execute):
    done = run(["git", "lfs", "version"], timeout=30, env=clean_environment())
    match = re.search(r"git-lfs/(\d+)\.(\d+)\.(\d+)", done["out"]) if done["code"] == 0 else None
    return tuple(map(int, match.groups())) if match else None


def storage_section(root: Path, checkout: dict, run=execute) -> dict:
    version = lfs_version(run)
    section = {"client_version": ".".join(map(str, version)) if version else None,
               "required_version_when_lfs_files_exist": ".".join(map(str, LFS_MINIMUM)), "lfs_files": [], "applicable": False,
               "state": "not_checked", "detail": "The root is not a Git checkout."}
    if not checkout["is_checkout"]:
        return section
    listed = git(root, "ls-files", "-z", run=run)
    if listed["code"] != 0:
        return dict(section, detail=failure_text(listed))
    try:
        done = subprocess.run(["git", "--no-optional-locks", "-C", str(root), "check-attr", "--stdin", "-z", "filter"],
                              input=listed["out"].encode("utf-8", "surrogateescape"), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=120, env=clean_environment(), check=True)
    except (OSError, subprocess.SubprocessError) as error:
        return dict(section, detail=f"{type(error).__name__}: {error}")
    fields = done.stdout.decode("utf-8", "replace").split("\0")
    selected = sorted(fields[index] for index in range(0, len(fields) - 2, 3) if fields[index + 2] == "lfs")
    if not selected:
        return dict(section, state="ready", detail="No tracked file is selected for Git LFS, so no LFS client is required.")
    unhydrated = []
    for name in selected:
        try:
            with (root / name).open("rb") as stream:
                if stream.read(43).startswith(b"version https://git-lfs.github.com/spec/v1"):
                    unhydrated.append(name)
        except OSError:
            unhydrated.append(name)
    section.update(applicable=True, lfs_files=selected, unhydrated=unhydrated)
    if version is None:
        return dict(section, state="missing", detail="LFS-selected files exist and no Git LFS client was found.")
    if version < LFS_MINIMUM:
        return dict(section, state="mismatch", detail=f"LFS-selected files exist and the client is {section['client_version']}.")
    return dict(section, state="missing" if unhydrated else "ready",
                detail=f"{len(unhydrated)} of {len(selected)} selected files are not hydrated.")


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, UnicodeError, ValueError):
        return {}


def workflow_section(root: Path, run=execute) -> dict:
    registry = read_json(root / "docs/workflow/registry.json")
    current = read_json(root / str(registry.get("current", "docs/workflow/CURRENT.json")))
    modes = registry.get("modes")
    entries = {name: entry.get("entrypoint") if isinstance(entry, dict) else None for name, entry in modes.items()} \
        if isinstance(modes, dict) else {"registered": registry.get("entrypoint")}
    task = current.get("active_task") or current.get("latest_task")
    folder = f"{registry.get('task_root', 'docs/workflow/tasks')}/{task}"
    checkpoint = current.get("checkpoint", {}).get("session") if isinstance(current.get("checkpoint"), dict) else None
    if checkpoint is None and task and (root / folder / "SESSION.md").is_file():
        checkpoint = folder + "/SESSION.md"
    section = {"entry_points": entries, "active_task": current.get("active_task"), "latest_task": current.get("latest_task"),
               "selected_task": task, "selected_task_status": read_json(root / folder / "task.json").get("status") if task else None,
               "next_action_status": current.get("next_action", {}).get("status") if isinstance(current.get("next_action"), dict) else None,
               "latest_checkpoint": checkpoint, "structure_check": {"state": "not_checked", "detail": "tools/chat_workflow.py is not present."}}
    tool = root / "tools/chat_workflow.py"
    if tool.is_file():
        done = run([sys.executable, "-I", "-B", str(tool), "--root", str(root), "check", "--json"], timeout=120, env=clean_environment())
        try:
            report = json.loads(done["out"])
            section["structure_check"] = {"state": "ready" if report["passed"] else "mismatch", "detail":
                                          f"{report['tasks_checked']} tasks checked." if report["passed"] else "; ".join(report["errors"])[:1000]}
        except (ValueError, KeyError, TypeError):
            section["structure_check"] = {"state": "not_checked", "detail": failure_text(done)}
    return section


def remote_section(root: Path, checkout: dict, online: bool, run=execute) -> dict:
    if not online:
        return {"state": "not_checked", "detail": "Offline by default. Use --online to read the remote heads."}
    if not checkout["is_checkout"]:
        return {"state": "not_checked", "detail": "The root is not a Git checkout."}
    done = git(root, "ls-remote", "--heads", "origin", run=run, timeout=60)
    if done["code"] != 0:
        return {"state": "not_checked", "detail": "The remote could not be read: " + failure_text(done)}
    heads = {line.split("\t")[1][len("refs/heads/"):]: line.split("\t")[0] for line in done["out"].splitlines() if "\trefs/heads/" in line}
    tracked = {name[len("origin/"):]: sha for name, sha in checkout["tracking_refs"].items()}
    return {"state": "ready", "detail": "Read with git ls-remote; nothing was fetched.", "heads": heads,
            "stale_tracking_refs": sorted(name for name in set(heads) | set(tracked) if heads.get(name) != tracked.get(name)),
            "branch_head_published": heads.get(checkout["branch"]) == checkout["head"] if checkout["branch"] else None}


# --- Readiness -------------------------------------------------------------

def combine(states) -> str:
    states = list(states)
    for state in ("unsupported", "mismatch", "missing", "not_checked"):
        if state in states:
            return state
    return "ready" if states else "not_checked"


def next_action(root: Path, spec: dict, key, profile: str, failing: dict, interpreters: list, environment: dict, checkout: dict,
                visual: dict, rebuild: bool, node=None) -> str:
    """The first exact setup action that an unmet check needs."""
    version, identifier = spec["interpreter"]["version"], failing["id"]
    distribution = spec["interpreter"].get("distributions", {}).get(key, {})
    if failing["state"] == "unsupported":
        return "No setup action applies on this machine: " + failing["detail"]
    place = "" if os.path.realpath(str(root)) == str(ROOT) else f"In {root}: "
    # Visual setup refuses without Node.js, so the environment itself is prepared with its own profile.
    target = DEFAULT_PROFILE if identifier in ENVIRONMENT_CHECKS and profile == "visual-verification" else profile
    setup = f"{distribution.get('command', 'python3')} tools/bootstrap_local.py --profile {target}"
    if target == "visual-verification" and node:
        setup += f" --node {shlex.quote(str(node))}"
    if identifier in ENVIRONMENT_CHECKS:
        compliant = [entry for entry in interpreters if entry["ok"] and not entry["differences"]]
        if identifier == "interpreter" and not compliant:
            if interpreters:
                return (f"The specified interpreter {version} was not found; found "
                        + ", ".join(f"{entry['version']} ({(entry['distribution'] or {}).get('name')})" for entry in interpreters)
                        + ". Provide the exact interpreter or adopt another patch through a reviewed specification change.")
            install = distribution.get("install")
            return ("Install the interpreter with the machine's existing mechanism: " + " ".join(install) if install else
                    f"Provide {spec['interpreter']['implementation']} {version} with the machine's existing mechanism.")
        if environment["symlink"] or environment["exists"] and not environment["configuration"]:
            return f"{place}Move {spec['environment']['directory']} away by hand, because it is not an environment of this checkout, then run: {setup}"
        if rebuild:
            return f"{place}Review the incompatible environment, then rebuild it explicitly: {setup} --rebuild"
        return f"{place}Run: {setup}"
    if identifier == "git":
        if not checkout["git_available"]:
            return f"Install Git or repair its installation: {checkout['problem']}"
        if checkout["unread"]:
            return "Repair the checkout before any setup. Git could not read: " + "; ".join(checkout["unread"])
        return "Run from the top of a Git checkout or worktree" + (f". Git reports: {checkout['problem']}" if checkout["problem"] else ".")
    if identifier == "npm-dependencies" and visual["npm_directory_symlink"]:
        return f"{place}Remove the link {visual['npm_directory']} by hand, then run: {setup}"
    if identifier == "npm-dependencies" and visual["npm_directory_exists"]:
        return f"{place}Review the difference, then allow npm ci to replace {visual['npm_directory']}: {setup} --repair-node"
    return {
        "source-import": "Run from a complete checkout and inspect the reported import error.",
        "lock": "Restore the committed lock and its provenance, or adopt a reviewed change.",
        "node": f"Install Node.js {spec['profiles']['visual-verification']['node_major']} and pass it with --node if it is not first on PATH.",
        "npm": "Install the npm that belongs to the selected Node.js.",
        "npm-dependencies": f"{place}Run: {setup}", "chromium": f"{place}Run: {setup}",
    }.get(identifier, "Inspect the reported detail: " + failing["detail"])


def readiness_section(root: Path, spec: dict, key, environment: dict, checkout: dict, visual: dict, interpreters: list, run=execute, node=None) -> dict:
    results = {"core": core_checks(root, spec, key, environment, checkout, run),
               "python-verification": verification_checks(root, spec, key, environment, run),
               "visual-verification": visual_checks(visual)}
    section = {}
    for name, profile in spec["profiles"].items():
        rebuild = bool(rebuild_reasons(environment, results["core"], results["python-verification"], package_rows(spec, name, environment)))
        kind, requires = profile["kind"], {}
        if kind == "environment":
            own = results[name]
            requires = {part: section[part]["state"] for part in profile_chain(spec, name)[:-1]}
            state = combine([item["state"] for item in own] + list(requires.values()))
        else:
            state = "unsupported" if kind == "unconfigured" else "not_checked"
            own = [check(item, state, text) for item, text in profile["readiness_checks"].items()]
        # Base profiles come first, so a missing or wrong interpreter is the first action.
        unmet = [item for part in [*requires, name] for item in (section[part]["checks"] if part in section else own) if item["state"] != "ready"]
        first = next((item for item in unmet if item["state"] != "not_checked" or item["id"] == "pip-check" and usable(environment)), unmet[0] if unmet else None)
        section[name] = {"state": state, "kind": kind, "purpose": profile["purpose"], "requires": requires, "checks": own,
                         "next_action": None if state == "ready" else profile["purpose"] if kind != "environment" else
                         next_action(root, spec, key, name, first, interpreters, environment, checkout, visual, rebuild, node)}
    return section


def collect(root: Path, profile: str = DEFAULT_PROFILE, online: bool = False, *, run=execute, which=shutil.which,
            system=None, machine=None, node=None, cache=None) -> dict:
    """Build the complete report. Every parameter after * exists so that tests can control the observations."""
    root = canonical(root)
    spec = load_specification(root)
    if profile not in spec["profiles"]:
        raise SpecificationError(f"Unknown profile {profile}; known: {', '.join(spec['profiles'])}")
    system, machine = system or platform.system(), machine or host_machine(run)
    key = platform_key(spec, system, machine)
    series = ".".join(spec["interpreter"]["version"].split(".")[:2])
    checkout = checkout_section(root, run)
    imports = [package["import"] for package in packages_of(spec, DEFAULT_PROFILE)]
    environment = inspect_environment(root, spec, imports, run)
    interpreters = find_interpreters(spec, key, run, which)
    visual = visual_section(root, spec, run, which, node, cache, system, machine)
    readiness = readiness_section(root, spec, key, environment, checkout, visual, interpreters, run, node)
    known = {normalize(package["name"]) for package in packages_of(spec, DEFAULT_PROFILE)} | INSTALL_TOOLS
    installed = environment["facts"]["packages"] if usable(environment) else {}
    return {
        "schema": REPORT_SCHEMA, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "diagnosed_by": {"executable": sys.executable, "version": platform.python_version(),
                         "tool_sha256": digest(Path(__file__).resolve())},
        "platform": {"key": key, "system": system, "machine": machine,
                     "os_version": platform.mac_ver()[0] or platform.release()},
        "checkout": checkout,
        "python": {"specified": spec["interpreter"]["version"], "environment": environment, "available_interpreters": interpreters},
        "packages": {"expected": package_rows(spec, DEFAULT_PROFILE, environment), "pip_check": environment["pip_check"],
                     "duplicates": environment["facts"]["duplicates"] if usable(environment) else {},
                     "additional": {name: version for name, version in sorted(installed.items()) if normalize(name) not in known},
                     "install_tools": {name: version for name, version in sorted(installed.items()) if normalize(name) in INSTALL_TOOLS}},
        "specification": specification_section(root, spec, profile, key, series),
        "visual": visual, "storage": storage_section(root, checkout, run), "workflow": workflow_section(root, run),
        "remote": remote_section(root, checkout, online, run),
        "readiness": readiness, "native_experiments": {"acceptance": "not_checked", "statement": NATIVE_NOTICE},
        "selected": {"profile": profile, "state": readiness[profile]["state"], "next_action": readiness[profile]["next_action"]}}


def path_labels(root: Path, worktrees=(), others=()) -> list:
    """This machine's paths and the labels that stand for them, longest path first."""
    labels = {tempfile.gettempdir(): "<tmp>", str(Path.home()): "<home>", str(root.parent): "<parent>"}
    labels.update((str(path), label) for path, label in others if os.path.isabs(str(path)))
    for number, worktree in enumerate(worktrees):
        labels.setdefault(str(Path(worktree).parent), "<worktree-parent>" if number else "<clone-parent>")
        labels[worktree] = f"<worktree-{number}>" if number else "<main-checkout>"
    labels[str(root)] = "<root>"
    for path, label in list(labels.items()):
        labels.setdefault(os.path.realpath(path), label)
    return sorted(((path, label) for path, label in labels.items() if len(path) > 1), key=lambda item: -len(item[0]))


def portable(value, labels: list):
    """Replace this machine's paths by labels so that a report can be published."""
    if isinstance(value, dict):
        return {portable(key, labels): portable(item, labels) for key, item in value.items()}
    if isinstance(value, list):
        return [portable(item, labels) for item in value]
    if isinstance(value, str):
        for path, label in labels:
            value = value.replace(path, label)
        if len(value) >= 200:  # A text that was cut short may end inside a path.
            ends = [size for path, _ in labels for size in range(5, len(path)) if value.endswith(path[:size])]
            value = value[:-max(ends)] + "<cut>" if ends else value
    return value


def count(value) -> str:
    return "unread" if value is None else str(len(value) if isinstance(value, list) else value)


def render(report: dict) -> str:
    checkout, python, lines = report["checkout"], report["python"], []
    environment = python["environment"]
    facts = environment["facts"] or {}
    lines.append(f"OntoKin local doctor: profile {report['selected']['profile']} is {report['selected']['state']}")
    lines.append("")
    lines.append("Readiness by profile")
    for name, entry in report["readiness"].items():
        lines.append(f"  {name:<22}{entry['state']}")
        if entry["kind"] == "environment":
            lines += [f"    - requires {part}: {state}" for part, state in entry["requires"].items() if state != "ready"]
            lines += [f"    - {item['id']}: {item['state']}: {item['detail']}" for item in entry["checks"] if item["state"] != "ready"]
    lines += ["", "Checkout", f"  root      {checkout['root']}"]
    if checkout["is_checkout"]:
        lines += [f"  branch    {checkout['branch'] or 'detached'}{' (linked worktree)' if checkout['linked_worktree'] else ''}",
                  f"  head      {checkout['head']}", f"  tree      {checkout['tree']}",
                  f"  changes   {count(checkout['tracked_modifications'])} tracked modifications, {count(checkout['untracked_count'])} untracked files, "
                  f"{count(checkout['stashes'])} stashes, {count(checkout['unpublished_commits'])} commits not in a tracking ref"]
        lines += [f"    not read: {item}" for item in checkout["unread"]]
        lines += [f"    {line}" for line in (checkout["tracked_modifications"] or [])[:20]]
        lines += [f"    ?? {line}" for line in (checkout["untracked"] or [])[:20]]
    else:
        lines.append("  not the top of a Git checkout" + (f": {checkout['problem']}" if checkout["problem"] else ""))
    lines += ["", "Python", f"  specified    {python['specified']}", f"  environment  {environment['path']}"]
    if facts.get("ok"):
        lines.append(f"  running      {facts['implementation']} {facts['version']} ({facts['distribution']['name']}), {facts['platform_tag']}")
    else:
        lines.append(f"  running      {'absent' if not environment['exists'] else facts.get('error', 'no interpreter')}")
    lines += [f"  available    {entry['version'] or 'unreadable'} ({(entry['distribution'] or {}).get('name')}) at {entry['path']}: "
              f"{'compliant' if not entry['differences'] else '; '.join(entry['differences'])}" for entry in python["available_interpreters"]]
    lines += ["", "Packages"]
    lines += [f"  {row['name']:<28}{row['expected']:<12}{row['installed'] or '-':<12}{row['state']}" for row in report["packages"]["expected"]]
    if report["packages"]["additional"]:
        lines.append("  additional: " + ", ".join(f"{name} {version}" for name, version in report["packages"]["additional"].items()))
    pip = report["packages"]["pip_check"]
    lines.append(f"  pip check: {'not checked' if pip is None else pip['summary']}")
    specification = report["specification"]
    lines += ["", "Specification", f"  lock      {specification['selected_lock']['detail']}"]
    lines += [f"  problem   {problem}" for problem in specification["problems"]]
    lines += [f"  {value or 'absent':<72}{path}" for path, value in specification["digests"].items()]
    visual = report["visual"]
    lines += ["", "Visual tools", f"  Node.js   {visual['node']['version'] or 'not found'} (target {visual['node']['target_major']}), npm {visual['npm']['version'] or 'not found'}"]
    lines += [f"  {row['name']:<16}{row['expected']:<16}{row['installed'] or '-'}" for row in visual["npm_dependencies"] if row["direct"]]
    lines.append(f"  browser   {visual['browser']['detail']}")
    lines += ["", "Storage", f"  {report['storage']['detail']} Git LFS client: {report['storage']['client_version'] or 'not found'}."]
    workflow = report["workflow"]
    lines += ["", "Workflow", "  entry     " + ", ".join(f"{name}: {path}" for name, path in workflow["entry_points"].items()),
              f"  task      {workflow['selected_task']} ({workflow['selected_task_status']}); checkpoint {workflow['latest_checkpoint'] or 'none'}",
              f"  structure {workflow['structure_check']['state']}: {workflow['structure_check']['detail']}"]
    lines += ["", "Remote", f"  {report['remote']['detail']}"]
    lines += [f"  {sha}  {name}" for name, sha in report["remote"].get("heads", {}).items()]
    lines += ["", "Native experiments", f"  acceptance {report['native_experiments']['acceptance']}. {NATIVE_NOTICE}"]
    if report["selected"]["next_action"]:
        lines += ["", "Next setup action", f"  {report['selected']['next_action']}"]
    return "\n".join(lines)


def write_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository checkout or worktree to diagnose")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="profile that decides the exit status; every profile is reported")
    parser.add_argument("--json", action="store_true", help="print the JSON report instead of the summary")
    parser.add_argument("--output", type=Path, help="also write the JSON report to this new file")
    parser.add_argument("--portable-paths", action="store_true", help="replace this machine's paths by labels in the report")
    parser.add_argument("--online", action="store_true", help="also read the remote heads with git ls-remote; nothing is fetched")
    parser.add_argument("--node", help="Node.js executable to diagnose instead of the first on PATH")
    args = parser.parse_args(argv)
    try:
        report = collect(args.root, args.profile, args.online, node=args.node)
        if args.portable_paths:
            report = portable(report, path_labels(canonical(args.root), report["checkout"].get("worktrees", ()), [(args.node, "<node>")] if args.node else ()))
        text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            write_new(args.output, text)
    except (SpecificationError, OSError) as error:
        print(f"The doctor could not run: {error}", file=sys.stderr)
        return 2
    print(text if args.json else render(report), end="" if args.json else "\n")
    return 0 if report["selected"]["state"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
