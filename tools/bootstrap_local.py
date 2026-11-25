#!/usr/bin/env python3
"""Prepare OntoKin's local development environment from its committed specification.

The tool resolves the checkout or worktree and the specified interpreter, selects the
committed lock that is valid for this platform, creates the checkout's own environment
only when it is absent, and installs only missing or mismatched packages from that
lock with hash enforcement. A healthy environment is left as it is. An incompatible
one is reported and is rebuilt only with --rebuild. Nothing that a process uses is
changed. Node dependencies and Chromium are prepared only for the visual-verification
profile. --preview changes nothing.

It does not replace tools/check_local.py, change project behaviour, start native
experiments or publish anything. A ready profile is not task completion, native
qualification or a release result.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # A preview leaves no __pycache__ behind.

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import doctor_local as doctor

try:
    import fcntl
except ImportError:  # No advisory file lock on this platform.
    fcntl = None

REPORT_SCHEMA = "ontokin.local-bootstrap/1"
RECORD_SCHEMA = "ontokin.local-environment-record/1"
LOCK_NAME = "ontokin-bootstrap.lock"  # In the checkout's own Git directory.
STATE_DIRECTORY = "build/local-environment"  # Ignored by Git; holds the reports of changing runs.
READY, UNMET, REFUSED, BUSY, INTERRUPTED = 0, 1, 2, 3, 130
SMOKE = (("capabilities", ["-B", "-m", "ontokin", "capabilities"]),
         ("check", ["-B", "-m", "ontokin", "check", "docs/language-design/core-v0.1/01-independent-parts.ok"]))


class Refusal(RuntimeError):
    """A precondition that stops the run before it changes anything."""


class Busy(RuntimeError):
    """Another setup run holds this checkout."""


class ActionFailed(RuntimeError):
    """A started setup action did not succeed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


class Session:
    """One setup run: where it works, how it starts commands and what it did."""

    def __init__(self, root: Path, spec: dict, key, system: str, run, which):
        self.root, self.spec, self.key, self.system, self.run, self.which = root, spec, key, system, run, which
        self.environment = root / spec["environment"]["directory"]
        self.python = self.environment / "bin" / "python"
        self.log: list = []
        self.keep: tuple = ()  # The held lock, kept open in children so that an orphaned one still excludes others.

    def perform(self, name: str, argv, *, cwd=None, timeout=1800, env=None) -> dict:
        """Run one setup action and keep what it did, whether it succeeded or not."""
        entry = {"action": name, "argv": [str(part) for part in argv], "started_at": utc_now(), "seconds": None, "code": None,
                 "output_tail": "", "error": "not finished"}
        self.log.append(entry)
        clock = time.monotonic()
        result = self.run(argv, cwd=cwd, timeout=timeout, env=doctor.clean_environment() if env is None else env, keep=self.keep)
        entry.update(seconds=round(time.monotonic() - clock, 2), code=result["code"],
                     output_tail=(result["out"] + result["err"])[-2000:], error=result["error"])
        if result["code"] != 0:
            raise ActionFailed(f"{name} failed: {doctor.failure_text(result)}")
        return result

    @contextmanager
    def exclusive(self):
        """Hold the checkout's setup lock; a second run fails at once and a crash releases it."""
        if fcntl is None:
            raise Refusal("This platform offers no file lock, so concurrent setup runs cannot be excluded.")
        located = doctor.git(self.root, "rev-parse", "--absolute-git-dir", run=self.run)
        if located["code"] != 0:
            raise Refusal("The checkout's Git directory was not found: " + doctor.failure_text(located))
        with (Path(located["out"].rstrip("\n")) / LOCK_NAME).open("a") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise Busy("Another setup run is changing this checkout's environment. Nothing was changed.") from error
            self.keep = (stream.fileno(),)
            try:
                yield
            finally:
                self.keep = ()


# --- Use of a directory ----------------------------------------------------

def variable(environment: str, name: str):
    match = re.search(r"(?:^|[\0 ])" + name + r"=(.*?)(?=[\0 ][A-Za-z_][A-Za-z0-9_]*=|\0|$)", environment, re.S)
    return match[1].rstrip() if match else None


def process_environment(number: str, system: str, run):
    """The start environment of one process as text, or None when it cannot be read."""
    if system == "Linux":
        read = run(["cat", f"/proc/{number}/environ"], timeout=10)
        return read["out"] if read["code"] == 0 and read["out"] else None
    read = run(["ps", "-Eww", "-o", "command=", "-p", number], timeout=30)
    return read["out"] if read["code"] == 0 and " PATH=" in read["out"] else None


def working_directory(number: str, run):
    place = run(["lsof", "-a", "-d", "cwd", "-p", number, "-Fn"], timeout=30)
    places = [entry[1:] for entry in place["out"].splitlines() if entry.startswith("n/")]
    return places[0] if places else None


def started_from(session: Session, directory: Path, number: str, command: str) -> bool:
    """Whether a process of this user runs from a directory. One that cannot be excluded counts."""
    prefix, words = str(directory) + os.sep, command.split(None, 2)
    program, place = os.path.basename(words[0]).lower(), None
    interpreter, node = program.startswith(("python", "pypy")), program.startswith("node")
    if command.startswith(prefix) or (interpreter or node) and prefix in command:
        return True
    # The program and, for an interpreter, its script; a system program may have a space in its own path.
    named = words[:1] + (words[1:2] if interpreter or node else [])
    relative = [word for word in named if os.sep in word and not word.startswith((os.sep, "-"))]
    if relative or interpreter or node:
        place = working_directory(number, session.run)
    for word in relative:
        if place is None or os.path.normpath(os.path.join(place, word)).startswith(prefix):
            return True
    if node:
        shared = directory.relative_to(session.root)
        return (place is None or doctor.inside(place, str(session.root)) or str(session.root) in command
                or os.path.realpath(os.path.join(place, shared)) == str(directory))
    if not interpreter:
        return False
    environment = process_environment(number, session.system, session.run)
    if environment is None:
        return place is None or doctor.inside(place, str(session.root))
    launcher = variable(environment, "__PYVENV_LAUNCHER__")  # A macOS framework interpreter shows its own path instead.
    if launcher:
        return launcher.startswith(prefix)
    if os.path.normpath(variable(environment, "VIRTUAL_ENV") or "/") == str(directory):
        return True
    if os.sep not in words[0]:
        for element in (variable(environment, "PATH") or "").split(os.pathsep):
            if element and os.path.exists(os.path.join(element, words[0])):
                return (os.path.normpath(element) + os.sep).startswith(prefix)
    return False


def users_of(session: Session, directory: Path):
    """Process identifiers that use a directory, or None when that cannot be established.

    Open files and a start from the directory count for every process that shows them. Only this
    user's processes are examined further; no other user works in this user's checkout.
    """
    if not session.which("lsof"):
        return None
    listed = session.run(["lsof", "-w", "-t", "+D", str(directory)], timeout=300)
    shown = session.run(["ps", "-axo", "pid=,uid=,command="], timeout=30)
    if listed["error"] or listed["code"] not in (0, 1) or listed["err"].strip() or shown["code"] != 0 or not shown["out"].strip():
        return None
    users = {int(line) for line in listed["out"].split() if line.isdigit()}
    for line in shown["out"].splitlines():
        number, owner, command = (line.split(None, 2) + ["", "", ""])[:3]
        if number.isdigit() and int(number) not in users and command and (
                command.startswith(str(directory) + os.sep) or owner == str(os.getuid()) and started_from(session, directory, number, command)):
            users.add(int(number))
    return sorted(users)


def require_unused(session: Session, directory: Path) -> None:
    users = users_of(session, directory)
    if users is None:
        raise Refusal(f"Whether a process uses {directory.name} cannot be established here, so it is not changed.")
    if users:
        raise Refusal(f"{directory.name} is in use by process {', '.join(map(str, users))}, or that process could not be excluded, so it is not changed.")


# --- Planning --------------------------------------------------------------

def resolve_interpreter(spec: dict, key, requested, run=doctor.execute, which=shutil.which) -> dict:
    """Find the specified interpreter. Absent, unsuitable and compliant are different answers."""
    if requested:
        path = which(requested) or requested
        if not os.path.exists(path):
            return {"status": "missing", "path": None, "candidates": [], "detail": f"{requested} does not exist."}
        found = [doctor.candidate(spec, key, path, doctor.probe(Path(path), run=run))]
    else:
        found = doctor.find_interpreters(spec, key, run, which)
    for entry in found:
        if not entry["differences"]:
            return {"status": "found", "path": entry["path"], "candidates": found,
                    "detail": f"{entry['implementation']} {entry['version']} ({entry['distribution']['name']})."}
    if not found:
        return {"status": "missing", "path": None, "candidates": [],
                "detail": f"{spec['interpreter']['implementation']} {spec['interpreter']['version']} was not found on this machine."}
    return {"status": "mismatch", "path": None, "candidates": found,
            "detail": "; ".join(f"{entry['path']}: {', '.join(entry['differences'])}" for entry in found)}


def incompatibilities(observed: dict, rows: list) -> list:
    """Why installing packages cannot make the existing environment ready."""
    environment = observed["python"]["environment"]
    core = {item["id"]: item for item in observed["readiness"]["core"]["checks"]}
    found = [f"{name}: {core[name]['detail']}" for name in ("interpreter", "isolation") if core[name]["state"] in {"mismatch", "not_checked"}]
    if found or not doctor.usable(environment) or not rows:
        return found
    if "pip" not in {doctor.normalize(name) for name in environment["facts"]["packages"]}:
        return ["pip: pip is missing, so nothing can be installed"]
    if all(row["state"] == "ready" for row in rows):
        checks = {item["id"]: item for item in observed["readiness"]["python-verification"]["checks"]}
        return [f"{name}: {checks[name]['detail']}" for name in ("imports", "pip-check", "native-reader") if checks[name]["state"] != "ready"]
    return []


def plan_actions(session: Session, profile: str, observed: dict, rebuild: bool, repair: bool) -> dict:
    """Decide what this run would change. Planning reads only, and it refuses before any change."""
    root, spec, environment = session.root, session.spec, observed["python"]["environment"]
    series = ".".join(spec["interpreter"]["version"].split(".")[:2])
    selected = doctor.select_lock(spec, profile, session.key, series)
    if selected["state"] != "ready":
        raise Refusal("No package is installed: " + selected["detail"])
    chain = doctor.profile_chain(spec, profile)
    problems = [problem for name in chain for problem in doctor.profile_problems(root, spec, name)]
    if problems:
        raise Refusal("The specification, pins and locks disagree: " + "; ".join(problems))
    directory, actions, notes, recreate = session.environment, [], [], not environment["exists"]
    rows = doctor.package_rows(spec, profile, environment)
    reasons = [] if recreate else incompatibilities(observed, rows)
    if recreate:
        actions.append({"action": "create-environment", "detail": f"Create {directory.name} with the specified interpreter."})
    elif reasons:
        reason = "; ".join(reasons)
        if not rebuild:
            raise Refusal(f"The existing environment is incompatible and was not changed: {reason}. Review it, then use --rebuild to replace it.")
        if environment["symlink"] or not environment["configuration"]:
            raise Refusal(f"{directory.name} is not an environment directory of this checkout, so it is not replaced. Move it away by hand.")
        require_unused(session, directory)
        actions.append({"action": "rebuild-environment", "detail": f"Replace {directory.name}: {reason}."})
        recreate = True
    else:
        notes.append("The existing environment is compatible and is reused.")
    wanted = rows if recreate else [row for row in rows if row["state"] != "ready"]
    if wanted:
        if not recreate:
            require_unused(session, directory)
        actions.append({"action": "install-packages", "lock": selected["path"], "packages":
                        [{"name": row["name"], "version": row["expected"], "replaces": None if recreate else row["installed"]} for row in wanted],
                        "detail": f"Install {len(wanted)} of {len(rows)} packages from {selected['path']} with hash enforcement."})
    elif rows:
        notes.append("Every pinned package is already at its adopted version.")
    if "visual-verification" in chain:
        actions += plan_visual(session, observed["visual"], repair, notes)
    if not actions and not (environment["record"] or {}).get("readable"):
        actions.append({"action": "record-environment", "detail": "Write the missing record of the existing environment."})
    return {"lock": selected, "actions": actions, "notes": notes}


def plan_visual(session: Session, visual: dict, repair: bool, notes: list) -> list:
    """Node dependencies and Chromium; installed identities are compared before anything is replaced."""
    states = {item["id"]: item for item in doctor.visual_checks(visual)}
    if states["node"]["state"] != "ready" or states["npm"]["state"] == "missing":
        bad = states["node"] if states["node"]["state"] != "ready" else states["npm"]
        raise Refusal(f"{bad['detail']} Node.js is not installed by this tool.")
    if visual["npm_directory_symlink"]:
        raise Refusal(f"{visual['npm_directory']} is a symbolic link, so it is never replaced. Remove the link by hand.")
    actions = []
    if states["npm-dependencies"]["state"] == "ready":
        notes.append("The npm dependencies are at their committed versions and are left as they are.")
    elif not visual["npm_directory_exists"]:
        actions.append({"action": "install-node-dependencies", "replaces": False, "detail": "Install the committed npm dependencies with npm ci."})
    elif repair:
        require_unused(session, session.root / visual["npm_directory"])
        actions.append({"action": "install-node-dependencies", "replaces": True,
                        "detail": f"Replace {visual['npm_directory']} with npm ci: {states['npm-dependencies']['detail']}"})
    else:
        raise Refusal(f"{visual['npm_directory']} exists and differs: {states['npm-dependencies']['detail']}. "
                      "npm ci would replace the directory; use --repair-node to allow that.")
    if actions or states["chromium"]["state"] != "ready":
        actions.append({"action": "install-chromium", "detail": "Install Playwright's matching Chromium headless shell."})
    return actions


# --- Actions ---------------------------------------------------------------

def install_interpreter(session: Session) -> None:
    """Use the machine's existing installation mechanism, only on an explicit request."""
    command = session.spec["interpreter"].get("distributions", {}).get(session.key, {}).get("install")
    if not command or not session.which(command[0]):
        raise Refusal("The machine's existing installation mechanism for the interpreter is not available.")
    session.perform("install-interpreter", command, timeout=3600)


def create_environment(session: Session, python: str) -> None:
    session.perform("create-environment", [python, "-I", "-m", "venv", session.environment])
    facts = doctor.probe(session.python, run=session.run)
    differences = doctor.interpreter_differences(session.spec, session.key, facts) if facts["ok"] else [facts["error"]]
    if differences:
        raise ActionFailed("The created environment is not compliant: " + "; ".join(differences))


def set_aside(session: Session) -> Path:
    """Move the old environment out of the way in one step, so that an interruption leaves no partial one behind."""
    directory = session.environment
    if directory.is_symlink() or not (directory / "pyvenv.cfg").is_file() or directory.resolve().parent != session.root:
        raise Refusal(f"{directory.name} is not an environment directory of this checkout, so it is not replaced.")
    place = session.root / STATE_DIRECTORY / f"replaced-{stamp()}"
    place.parent.mkdir(parents=True, exist_ok=True)
    entry = {"action": "set-aside-environment", "argv": None, "started_at": utc_now(), "seconds": 0, "code": None, "output_tail": "", "error": None}
    session.log.append(entry)
    directory.rename(place)
    entry["code"] = 0
    return place


def discard(session: Session, place: Path) -> None:
    """Delete what was set aside. A remnant stays in the ignored state directory and is reported."""
    left = []
    shutil.rmtree(place, onerror=lambda function, path, error: left.append(f"{path}: {error[1]}"))
    session.log.append({"action": "delete-replaced-environment", "argv": None, "started_at": utc_now(), "seconds": 0,
                        "code": 1 if left else 0, "output_tail": "\n".join(left[:5]), "error": f"left behind: {place}" if left else None})


def install_packages(session: Session, lock: str, packages: list, wheels: list) -> None:
    """Install only the named packages, exactly as the lock pins them."""
    pins = doctor.parse_lock((session.root / lock).read_text(encoding="utf-8"))
    lines = [pins[doctor.normalize(package["name"])]["line"] for package in packages]
    with tempfile.TemporaryDirectory(prefix="ontokin-bootstrap-") as temporary:
        selection = Path(temporary) / "selected.lock"
        selection.write_text("\n".join(lines) + "\n", encoding="utf-8")
        source = ["--no-index"] + [part for wheel in wheels for part in ("--find-links", str(wheel))] if wheels else []
        session.perform("install-packages", [session.python, "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "install", "--no-input",
                                             "--no-deps", "--only-binary=:all:", "--require-hashes", *source, "-r", selection])


def run_visual(session: Session, actions: list, visual: dict) -> None:
    selected = [action for action in actions if action["action"] in {"install-node-dependencies", "install-chromium"}]
    if not selected:
        return
    environment = {key: value for key, value in doctor.clean_environment().items()
                   if not key.lower().startswith("npm_") and not key.startswith("NODE_")}
    environment["PATH"] = str(Path(visual["node"]["path"]).parent) + os.pathsep + environment.get("PATH", "")
    for action in selected:
        if action["action"] == "install-chromium":
            session.perform(action["action"], [visual["node"]["path"], "tools/node_modules/playwright/cli.js", "install", "chromium", "--only-shell"],
                            cwd=session.root, env=environment)
        else:
            session.perform(action["action"], [visual["npm"]["path"], "ci", "--prefix", "tools", "--ignore-scripts"], cwd=session.root, env=environment)


def prepare_package_smoke(session: Session, python: str, work: Path) -> list:
    """Two separate clean environments in a new directory; the wheel steps stay explicit."""
    work.mkdir(parents=True)
    for name in ("build-env", "install-env"):
        session.perform(f"create-{name}", [python, "-I", "-m", "venv", work / name])
    return [str(work / name) for name in ("build-env", "install-env")]


def smoke_checks(session: Session) -> list:
    """Small source checks through the environment's own interpreter; nothing is written."""
    results = []
    for name, arguments in SMOKE:
        done = session.run([session.python, *arguments], cwd=session.root, timeout=120, env=doctor.clean_environment())
        results.append({"check": name, "argv": done["argv"], "code": done["code"], "passed": done["code"] == 0,
                        "detail": None if done["code"] == 0 else doctor.failure_text(done)})
    return results


def environment_record(session: Session, profile: str, report: dict, lock) -> dict:
    """What was installed, from which inputs and with which tools."""
    environment = report["python"]["environment"]
    facts, visual = environment["facts"] or {}, profile == "visual-verification"
    return {
        "schema": RECORD_SCHEMA, "updated_at": utc_now(), "profile": profile, "root": str(session.root), "environment": environment["path"],
        "interpreter": {name: facts.get(name) for name in ("implementation", "version", "build", "compiler", "executable", "base_executable",
                                                             "base_prefix", "base_prefix_real", "distribution")},
        "platform": {"key": report["platform"]["key"], "system": facts.get("system"), "machine": facts.get("machine"),
                     "os_version": facts.get("os_version"), "platform_tag": facts.get("platform_tag")},
        "configuration": environment["configuration"],
        "installation_tools": report["packages"]["install_tools"], "build_tools": "None: binary wheels only.",
        "packages": dict(sorted((facts.get("packages") or {}).items())),
        "lock": lock, "digests": report["specification"]["digests"],
        "node": report["visual"]["node"] if visual else None, "npm": report["visual"]["npm"] if visual else None,
        "npm_dependencies": report["visual"]["npm_dependencies"] if visual else None, "browser": report["visual"]["browser"] if visual else None,
        "source": {"head": report["checkout"].get("head"), "tracked_modifications": report["checkout"].get("tracked_modifications")},
        "actions": session.log}


def write_record(session: Session, record: dict) -> Path:
    path = session.environment / session.spec["environment"]["record"]
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


# --- One run ---------------------------------------------------------------

def require_writable(path: Path, what: str) -> None:
    """The nearest existing directory above a new path must accept it."""
    place = path.parent
    while not place.exists() and place != place.parent:
        place = place.parent
    if not place.is_dir() or not os.access(place, os.W_OK | os.X_OK):
        raise Refusal(f"{what} cannot be created in {place}. Nothing was changed.")


def bootstrap(root: Path, profile: str, *, preview=False, python=None, rebuild=False, repair_node=False, wheels=(), work=None,
              install=False, node=None, run=doctor.execute, which=shutil.which, system=None, machine=None, cache=None) -> dict:
    """Prepare one profile and report what happened. Parameters from run on exist for controlled tests."""
    root = Path(root).resolve()
    spec = doctor.load_specification(root)
    if profile not in spec["profiles"]:
        raise Refusal(f"Unknown profile {profile}; known: {', '.join(spec['profiles'])}")
    kind = spec["profiles"][profile]["kind"]
    system, machine = system or platform.system(), machine or platform.machine()
    key = doctor.platform_key(spec, system, machine)
    if kind in {"external", "unconfigured"}:
        raise Refusal(f"General setup does not prepare {profile}. {spec['profiles'][profile]['purpose']}")
    if key is None:
        raise Refusal(f"This platform ({system} {machine}) has no entry in {doctor.SPECIFICATION}. Nothing was changed.")
    if not doctor.checkout_section(root, run)["is_checkout"]:
        raise Refusal("The root is not the top of a Git checkout or worktree. Nothing was changed.")
    if kind == "on-demand":
        if work is None:
            raise Refusal(f"{profile} needs --work-dir with a new directory outside the checkout.")
        work = Path(work).resolve()
        if work == root or root in work.parents or work.exists():
            raise Refusal(f"The {profile} working directory must be new and outside the checkout.")
        require_writable(work, "The working directory")

    session = Session(root, spec, key, system, run, which)
    report = {"schema": REPORT_SCHEMA, "started_at": utc_now(), "root": str(root), "profile": profile, "preview": preview,
              "platform": {"key": key, "system": system, "machine": machine}, "actions": session.log, "planned": [], "notes": [],
              "changed": False, "smoke": [], "outcome": None}

    def observe():
        report["observed"] = doctor.collect(root, profile, run=run, which=which, system=system, machine=machine, node=node, cache=cache)
        report["selected"] = report["observed"]["selected"]

    def prepare() -> bool:
        """Observe, plan and resolve the interpreter; every refusal happens here, before any change."""
        observe()
        plan = plan_actions(session, profile, report["observed"], rebuild, repair_node) if kind == "environment" else \
            {"lock": None, "notes": [], "actions": [{"action": "create-smoke-environments", "detail": f"Create two clean environments in {work}."}]}
        creates = any(action["action"] in {"create-environment", "rebuild-environment", "create-smoke-environments"} for action in plan["actions"])
        interpreter = resolve_interpreter(spec, key, python, run, which) if creates or python else \
            {"status": "not_needed", "path": None, "candidates": [], "detail": "The existing environment is reused."}
        if python and interpreter["status"] != "found":
            raise Refusal(f"The requested interpreter is not compliant: {interpreter['detail']}")
        report.update(planned=plan["actions"], notes=plan["notes"], lock=plan["lock"], interpreter=interpreter)
        return creates

    if preview:
        if prepare() and report["interpreter"]["status"] != "found":
            report["notes"].append(f"interpreter {report['interpreter']['status']}: {report['interpreter']['detail']}")
        return dict(report, outcome="previewed")
    prepare()  # Refuse as early as possible, and again under the lock.
    interruption = None
    with session.exclusive():
        creates = prepare()
        try:
            carry_out(session, report, creates, python, install, wheels, work)
        except (Refusal, ActionFailed, OSError) as error:
            if isinstance(error, Refusal) and not session.log:
                raise
            report["failure"] = str(error) if not isinstance(error, OSError) else f"{type(error).__name__}: {error}"
        except KeyboardInterrupt as error:
            interruption, report["failure"] = error, "Interrupted. Run the doctor before the next setup run."
        report["changed"] = bool(session.log)
        if report["changed"] or any(action["action"] == "record-environment" for action in report["planned"]):
            observe()
            if kind == "environment" and "failure" not in report and doctor.usable(report["observed"]["python"]["environment"]):
                report["environment_record"] = str(write_record(session, environment_record(session, profile, report["observed"], report["lock"])))
                report["changed"] = True
        if report["outcome"] is None:
            finish(session, report, "failed" if "failure" in report else "changed" if report["changed"] else "unchanged")
        if session.log:
            report["run_report"] = str(root / STATE_DIRECTORY / f"run-{stamp()}.json")
            doctor.write_new(Path(report["run_report"]), json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if interruption is not None:
        raise interruption
    return report


def carry_out(session: Session, report: dict, creates: bool, python, install: bool, wheels, work) -> None:
    """Perform the planned actions in order. The caller holds the checkout's setup lock."""
    names = {action["action"] for action in report["planned"]}
    if creates and report["interpreter"]["status"] == "missing" and install:
        install_interpreter(session)
        report["interpreter"] = resolve_interpreter(session.spec, session.key, python, session.run, session.which)
    if creates and report["interpreter"]["status"] != "found":
        report["outcome"] = "interpreter-" + report["interpreter"]["status"]
        return
    if "create-smoke-environments" in names:
        report["smoke_environments"] = prepare_package_smoke(session, report["interpreter"]["path"], work)
    if "rebuild-environment" in names:
        report["set_aside"] = str(set_aside(session))
    if names & {"create-environment", "rebuild-environment"}:
        create_environment(session, report["interpreter"]["path"])
    for action in report["planned"]:
        if action["action"] == "install-packages":
            install_packages(session, action["lock"], action["packages"], list(wheels))
    if "set_aside" in report:  # Only after its successor is complete.
        discard(session, Path(report["set_aside"]))
    run_visual(session, report["planned"], report["observed"]["visual"])


def finish(session: Session, report: dict, outcome: str) -> None:
    """Run the smoke checks that the reached state allows and settle the outcome."""
    observed = report["observed"]
    if session.spec["profiles"][report["profile"]]["kind"] == "environment" and observed["readiness"]["core"]["state"] == "ready":
        report["smoke"] = smoke_checks(session)
    report["outcome"] = outcome
    if any(not item["passed"] for item in report["smoke"]):
        report["selected"] = dict(observed["selected"], next_action="Inspect the smoke check that did not pass before using this environment.")


def exit_status(report: dict) -> int:
    if report["outcome"] == "previewed" or report.get("smoke_environments"):
        return READY
    passed = all(item["passed"] for item in report["smoke"])
    return READY if report["outcome"] in {"changed", "unchanged"} and report["selected"]["state"] == "ready" and passed else UNMET


def render(report: dict) -> str:
    lines = [f"OntoKin local setup: profile {report['profile']}, {report['outcome']}", f"  root {report['root']}"]
    for action in report["planned"]:
        lines.append(f"  {'would do' if report['preview'] else 'planned'}: {action['action']}: {action['detail']}")
        lines += [f"    {package['name']}=={package['version']}" + (f" (replaces {package['replaces']})" if package["replaces"] else "")
                  for package in action.get("packages", [])]
    if not report["planned"]:
        lines.append("  no change needed")
    lines += [f"  note: {note}" for note in report["notes"]]
    lines += [f"  done: {item['action']} (status {item['code']}, {item['seconds']} s)" + (f"; {item['error']}" if item["error"] else "") for item in report["actions"]]
    lines += [f"  smoke: {item['check']} {'passed' if item['passed'] else 'did not pass: ' + str(item['detail'])}" for item in report["smoke"]]
    if report.get("failure"):
        lines.append(f"  failure: {report['failure']}")
        lines += [f"  the replaced environment was kept in {report['set_aside']}"] * ("set_aside" in report and os.path.isdir(report["set_aside"]))
    if report["outcome"].startswith("interpreter-"):
        lines.append(f"  {report['outcome']}: {report['interpreter']['detail']}")
    lines.append("Readiness by profile")
    lines += [f"  {name:<22}{entry['state']}" for name, entry in report["observed"]["readiness"].items()]
    if report["selected"]["next_action"]:
        lines += ["Next setup action", f"  {report['selected']['next_action']}"]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository checkout or worktree to prepare")
    parser.add_argument("--profile", default=doctor.DEFAULT_PROFILE, help="core, python-verification, visual-verification or package-smoke")
    parser.add_argument("--python", help="explicit interpreter; it must still match the specification")
    parser.add_argument("--preview", action="store_true", help="show what would change and change nothing")
    parser.add_argument("--rebuild", action="store_true", help="allow replacing an incompatible environment that no process uses")
    parser.add_argument("--repair-node", action="store_true", help="allow npm ci to replace a differing tools/node_modules that no process uses")
    parser.add_argument("--install-interpreter", action="store_true", help="if the interpreter is absent, install it with the machine's existing mechanism")
    parser.add_argument("--find-links", type=Path, action="append", default=[], metavar="DIR", help="install offline from this directory of locked wheels")
    parser.add_argument("--work-dir", type=Path, help="new directory outside the checkout for the package-smoke environments")
    parser.add_argument("--node", help="Node.js executable for the visual-verification profile")
    parser.add_argument("--report", type=Path, help="also write the JSON report to this new file")
    parser.add_argument("--json", action="store_true", help="print the JSON report instead of the summary")
    parser.add_argument("--portable-paths", action="store_true", help="replace this machine's paths by labels in the report")
    args = parser.parse_args(argv)
    try:
        if args.report and (args.report.exists() or args.report.is_symlink()):
            raise Refusal(f"The report file must be new: {args.report}")
        if args.report:
            require_writable(args.report, "The report")
        report = bootstrap(args.root, args.profile, preview=args.preview, python=args.python, rebuild=args.rebuild,
                           repair_node=args.repair_node, wheels=[path.resolve() for path in args.find_links], work=args.work_dir,
                           install=args.install_interpreter, node=args.node)
    except (Refusal, doctor.SpecificationError) as error:
        print(f"Setup refused: {error}", file=sys.stderr)
        return REFUSED
    except Busy as error:
        print(str(error), file=sys.stderr)
        return BUSY
    except KeyboardInterrupt:
        print(f"Setup was interrupted. The report of this run is in {STATE_DIRECTORY}.", file=sys.stderr)
        return INTERRUPTED
    status = exit_status(report)
    if args.portable_paths:
        report = doctor.portable(report, doctor.path_labels(Path(args.root).resolve(), report["observed"]["checkout"].get("worktrees", ())))
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        doctor.write_new(args.report, text)
    print(text if args.json else render(report), end="" if args.json else "\n")
    return status


if __name__ == "__main__":
    sys.exit(main())
