#!/usr/bin/env python3
"""Prepare OntoKin's local development environment from its committed specification.

The tool resolves the checkout or worktree and the specified interpreter, selects the
committed lock that is valid for this platform, creates the checkout's own environment
only when it is absent, and installs only missing or mismatched packages from that
lock with hash enforcement. A healthy environment is left as it is. An incompatible
one is reported and is rebuilt only with --rebuild. Node dependencies and Chromium are
prepared only for the visual-verification profile. --preview changes nothing.

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
STATE_DIRECTORY = "build/local-environment"  # Ignored by Git; holds the setup lock and the reports of changing runs.
READY, UNMET, REFUSED, BUSY = 0, 1, 2, 3
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


@contextmanager
def exclusive(root: Path):
    """Hold the checkout's setup lock; a second run fails at once and a crash releases it."""
    if fcntl is None:
        raise Refusal("This platform offers no file lock, so concurrent setup runs cannot be excluded.")
    directory = root / STATE_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "bootstrap.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise Busy("Another setup run is changing this checkout's environment. Nothing was changed.") from error
        yield


def users_of(root: Path, directory: Path, run=doctor.execute, which=shutil.which):
    """Process identifiers that use a directory, or None when that cannot be established.

    Open files and absolute command lines are read for every process. A command line that names
    the directory relatively counts only when that process works in this checkout.
    """
    if not which("lsof"):
        return None
    listed = run(["lsof", "-w", "-t", "+D", str(directory)], timeout=300)
    shown = run(["ps", "-axo", "pid=,command="], timeout=30)
    if listed["error"] is not None or shown["code"] != 0:
        return None
    users = {int(line) for line in listed["out"].split() if line.isdigit()}
    relative = re.compile(r"(?:^|\s)(?:\./)?" + re.escape(directory.relative_to(root).as_posix()) + "/")
    for line in shown["out"].splitlines():
        number, _, command = line.strip().partition(" ")
        if not number.isdigit() or int(number) in users:
            continue
        if str(directory) + os.sep in command:
            users.add(int(number))
        elif relative.search(command):
            place = run(["lsof", "-a", "-d", "cwd", "-p", number, "-Fn"], timeout=30)
            places = [entry[1:] for entry in place["out"].splitlines() if entry.startswith("n")]
            if not places or os.path.realpath(places[0]) == os.path.realpath(str(root)):
                users.add(int(number))
    return sorted(users)


def require_unused(root: Path, directory: Path, run, which) -> None:
    users = users_of(root, directory, run, which)
    if users is None:
        raise Refusal(f"Whether a process uses {directory.name} cannot be established here, so it is not replaced.")
    if users:
        raise Refusal(f"{directory.name} is in use by process {', '.join(map(str, users))}, so it is not replaced.")


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


def install_interpreter(spec: dict, key, log: list, run, which) -> None:
    """Use the machine's existing installation mechanism, only on an explicit request."""
    command = spec["interpreter"].get("distributions", {}).get(key, {}).get("install")
    if not command or not which(command[0]):
        raise Refusal("The machine's existing installation mechanism for the interpreter is not available.")
    perform(log, "install-interpreter", command, run, timeout=3600)


def perform(log: list, name: str, argv, run, *, cwd=None, timeout=1800, env=None) -> dict:
    """Run one setup action and keep what it did, whether it succeeded or not."""
    started, clock = utc_now(), time.monotonic()
    result = run(argv, cwd=cwd, timeout=timeout, env=doctor.clean_environment() if env is None else env)
    log.append({"action": name, "argv": result["argv"], "started_at": started, "seconds": round(time.monotonic() - clock, 2),
                "code": result["code"], "output_tail": (result["out"] + result["err"])[-2000:], "error": result["error"]})
    if result["code"] != 0:
        raise ActionFailed(f"{name} failed: {doctor.failure_text(result)}")
    return result


def plan_actions(root: Path, spec: dict, profile: str, key, environment: dict, visual: dict, options) -> dict:
    """Decide what this run would change. Planning reads only, and it refuses before any change."""
    series = ".".join(spec["interpreter"]["version"].split(".")[:2])
    selected = doctor.select_lock(spec, profile, key, series)
    if selected["state"] != "ready":
        raise Refusal("No package is installed: " + selected["detail"])
    chain = doctor.profile_chain(spec, profile)
    problems = [problem for name in chain for problem in doctor.profile_problems(root, spec, name)]
    if problems:
        raise Refusal("The specification, pins and locks disagree: " + "; ".join(problems))
    directory = root / spec["environment"]["directory"]
    actions, notes = [], []
    checks = {item["id"]: item for item in options["core_checks"]}
    incompatible = [checks[name] for name in ("interpreter", "isolation") if checks[name]["state"] == "mismatch"]
    recreate = False
    if not environment["exists"]:
        actions.append({"action": "create-environment", "detail": f"Create {directory.name} with the specified interpreter."})
        recreate = True
    elif incompatible:
        reason = "; ".join(f"{item['id']}: {item['detail']}" for item in incompatible)
        if not options["rebuild"]:
            raise Refusal(f"The existing environment is incompatible and was not changed: {reason}. Review it, then use --rebuild to replace it.")
        if environment["symlink"] or not environment["configuration"]:
            raise Refusal(f"{directory.name} is not an environment directory of this checkout, so it is not replaced.")
        actions.append({"action": "rebuild-environment", "detail": f"Replace {directory.name}: {reason}."})
        recreate = True
    else:
        notes.append("The existing environment is compatible and is reused.")
    rows = doctor.package_rows(spec, profile, environment if not recreate else dict(environment, exists=False, facts=None))
    wanted = [row for row in rows if row["state"] != "ready"]
    if wanted:
        actions.append({"action": "install-packages", "lock": selected["path"], "packages":
                        [{"name": row["name"], "version": row["expected"], "replaces": None if recreate else row["installed"]} for row in wanted],
                        "detail": f"Install {len(wanted)} of {len(rows)} packages from {selected['path']} with hash enforcement."})
    elif rows:
        notes.append("Every pinned package is already at its adopted version.")
    if "visual-verification" in chain:
        actions += plan_visual(visual, options["repair_node"], notes)
    return {"lock": selected, "actions": actions, "notes": notes}


def plan_visual(visual: dict, repair: bool, notes: list) -> list:
    """Node dependencies and Chromium; installed identities are compared before anything is replaced."""
    states = {item["id"]: item for item in doctor.visual_checks(visual)}
    if states["node"]["state"] != "ready" or states["npm"]["state"] == "missing":
        bad = states["node"] if states["node"]["state"] != "ready" else states["npm"]
        raise Refusal(f"{bad['detail']} Node.js is not installed by this tool.")
    actions = []
    if states["npm-dependencies"]["state"] == "ready":
        notes.append("The npm dependencies are at their committed versions and are left as they are.")
    elif not visual["npm_directory_exists"]:
        actions.append({"action": "install-node-dependencies", "replaces": False, "detail": "Install the committed npm dependencies with npm ci."})
    elif repair:
        actions.append({"action": "install-node-dependencies", "replaces": True,
                        "detail": f"Replace {visual['npm_directory']} with npm ci: {states['npm-dependencies']['detail']}"})
    else:
        raise Refusal(f"{visual['npm_directory']} exists and differs: {states['npm-dependencies']['detail']}. "
                      "npm ci would replace the directory; use --repair-node to allow that.")
    if actions or states["chromium"]["state"] != "ready":
        actions.append({"action": "install-chromium", "detail": "Install Playwright's matching Chromium headless shell."})
    return actions


def create_environment(root: Path, spec: dict, key, python: str, log: list, run) -> None:
    directory = root / spec["environment"]["directory"]
    perform(log, "create-environment", [python, "-I", "-m", "venv", directory], run)
    facts = doctor.probe(directory / "bin" / "python", run=run)
    differences = doctor.interpreter_differences(spec, key, facts) if facts["ok"] else [facts["error"]]
    if differences:
        raise ActionFailed("The created environment is not compliant: " + "; ".join(differences))


def remove_environment(root: Path, spec: dict, log: list, run, which) -> None:
    directory = root / spec["environment"]["directory"]
    if directory.is_symlink() or not (directory / "pyvenv.cfg").is_file() or directory.resolve().parent != root.resolve():
        raise Refusal(f"{directory.name} is not an environment directory of this checkout, so it is not replaced.")
    require_unused(root, directory, run, which)
    shutil.rmtree(directory)
    log.append({"action": "remove-environment", "argv": None, "started_at": utc_now(), "seconds": 0, "code": 0,
                "output_tail": "", "error": None})


def install_packages(root: Path, spec: dict, lock: str, packages: list, wheels: list, log: list, run) -> None:
    """Install only the named packages, exactly as the lock pins them."""
    pins = doctor.parse_lock((root / lock).read_text(encoding="utf-8"))
    lines = [pins[doctor.normalize(package["name"])]["line"] for package in packages]
    python = root / spec["environment"]["directory"] / "bin" / "python"
    with tempfile.TemporaryDirectory(prefix="ontokin-bootstrap-") as temporary:
        selection = Path(temporary) / "selected.lock"
        selection.write_text("\n".join(lines) + "\n", encoding="utf-8")
        source = ["--no-index"] + [part for wheel in wheels for part in ("--find-links", str(wheel))] if wheels else []
        perform(log, "install-packages", [python, "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "install", "--no-input",
                                          "--no-deps", "--only-binary=:all:", "--require-hashes", *source, "-r", selection], run)


def run_visual(root: Path, spec: dict, actions: list, visual: dict, log: list, run, which) -> None:
    profile = spec["profiles"]["visual-verification"]
    selected = [action for action in actions if action["action"] in {"install-node-dependencies", "install-chromium"}]
    if not selected:
        return
    environment = doctor.clean_environment()
    environment["PATH"] = str(Path(visual["node"]["path"]).parent) + os.pathsep + environment.get("PATH", "")
    for action in selected:
        if action["action"] == "install-chromium":
            perform(log, action["action"], [visual["node"]["path"], "tools/node_modules/playwright/cli.js", "install", "chromium", "--only-shell"],
                    run, cwd=root, env=environment)
            continue
        if action["replaces"]:
            require_unused(root, root / profile["npm_directory"], run, which)
        perform(log, action["action"], [visual["npm"]["path"], "ci", "--prefix", "tools", "--ignore-scripts"], run, cwd=root, env=environment)


def smoke_checks(root: Path, spec: dict, run) -> list:
    """Small source checks through the environment's own interpreter; nothing is written."""
    python = root / spec["environment"]["directory"] / "bin" / "python"
    results = []
    for name, arguments in SMOKE:
        done = run([python, *arguments], cwd=root, timeout=120, env=doctor.clean_environment())
        results.append({"check": name, "argv": done["argv"], "code": done["code"], "passed": done["code"] == 0,
                        "detail": None if done["code"] == 0 else doctor.failure_text(done)})
    return results


def environment_record(root: Path, spec: dict, profile: str, report: dict, log: list, lock) -> dict:
    """What was installed, from which inputs and with which tools."""
    environment = report["python"]["environment"]
    facts = environment["facts"] or {}
    return {
        "schema": RECORD_SCHEMA, "updated_at": utc_now(), "profile": profile, "root": str(root), "environment": environment["path"],
        "interpreter": {name: facts.get(name) for name in ("implementation", "version", "build", "compiler", "executable", "base_executable",
                                                             "base_prefix", "base_prefix_real", "distribution")},
        "platform": {"key": report["platform"]["key"], "system": facts.get("system"), "machine": facts.get("machine"),
                     "os_version": facts.get("os_version"), "platform_tag": facts.get("platform_tag")},
        "configuration": environment["configuration"],
        "installation_tools": report["packages"]["install_tools"], "build_tools": "None: binary wheels only.",
        "packages": dict(sorted((facts.get("packages") or {}).items())),
        "lock": lock, "digests": report["specification"]["digests"],
        "node": report["visual"]["node"] if profile == "visual-verification" else None,
        "npm": report["visual"]["npm"] if profile == "visual-verification" else None,
        "npm_dependencies": report["visual"]["npm_dependencies"] if profile == "visual-verification" else None,
        "browser": report["visual"]["browser"] if profile == "visual-verification" else None,
        "source": {"head": report["checkout"].get("head"), "tracked_modifications": report["checkout"].get("tracked_modifications")},
        "actions": log}


def write_record(root: Path, spec: dict, record: dict) -> Path:
    path = root / spec["environment"]["directory"] / spec["environment"]["record"]
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def prepare_package_smoke(python: str, work: Path, log: list, run) -> list:
    """Two separate clean environments in a new directory; the wheel steps stay explicit."""
    work.mkdir(parents=True)
    for name in ("build-env", "install-env"):
        perform(log, f"create-{name}", [python, "-I", "-m", "venv", work / name], run)
    return [str(work / name) for name in ("build-env", "install-env")]


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

    report = {"schema": REPORT_SCHEMA, "started_at": utc_now(), "root": str(root), "profile": profile, "preview": preview,
              "platform": {"key": key, "system": system, "machine": machine}, "actions": [], "planned": [], "notes": [],
              "changed": False, "smoke": [], "outcome": None}

    def prepare():
        """Observe, plan and resolve the interpreter; every refusal happens here, before any change."""
        observed = doctor.collect(root, profile, run=run, which=which, system=system, machine=machine, node=node, cache=cache)
        if kind == "environment":
            options = {"rebuild": rebuild, "repair_node": repair_node, "core_checks": observed["readiness"]["core"]["checks"]}
            plan = plan_actions(root, spec, profile, key, observed["python"]["environment"], observed["visual"], options)
        else:
            plan = {"lock": None, "notes": [], "actions": [{"action": "create-smoke-environments",
                                                             "detail": f"Create two clean environments in {work}."}]}
        creates = any(action["action"] in {"create-environment", "rebuild-environment", "create-smoke-environments"} for action in plan["actions"])
        interpreter = resolve_interpreter(spec, key, python, run, which) if creates or python else \
            {"status": "not_needed", "path": None, "candidates": [], "detail": "The existing environment is reused."}
        if python and interpreter["status"] != "found":
            raise Refusal(f"The requested interpreter is not compliant: {interpreter['detail']}")
        report.update(planned=plan["actions"], notes=plan["notes"], lock=plan["lock"], interpreter=interpreter,
                      observed=observed, selected=observed["selected"])
        return creates

    creates = prepare()
    if preview:
        if creates and report["interpreter"]["status"] != "found":
            report["notes"].append(f"interpreter {report['interpreter']['status']}: {report['interpreter']['detail']}")
        return dict(report, outcome="previewed")
    if not report["planned"]:
        return finish(report, root, spec, run, "unchanged")
    with exclusive(root):
        creates = prepare()  # Another run may have finished between the first observation and the lock.
        try:
            carry_out(report, root, spec, key, creates, python, install, wheels, work, run, which)
        except Refusal as error:
            if not report["actions"]:
                raise
            report["failure"] = str(error)
        except ActionFailed as error:
            report["failure"] = str(error)
        report["changed"] = bool(report["actions"])
        if report["changed"]:
            report["observed"] = doctor.collect(root, profile, run=run, which=which, system=system, machine=machine, node=node, cache=cache)
            report["selected"] = report["observed"]["selected"]
            if kind == "environment" and "failure" not in report and doctor.usable(report["observed"]["python"]["environment"]):
                report["environment_record"] = str(write_record(root, spec, environment_record(
                    root, spec, profile, report["observed"], report["actions"], report["lock"])))
        if report["outcome"] is None:
            finish(report, root, spec, run, "failed" if "failure" in report else "changed" if report["changed"] else "unchanged")
        if report["changed"]:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            report["run_report"] = str(root / STATE_DIRECTORY / f"run-{stamp}.json")
            doctor.write_new(Path(report["run_report"]), json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return report


def carry_out(report: dict, root: Path, spec: dict, key, creates: bool, python, install: bool, wheels, work, run, which) -> None:
    """Perform the planned actions in order. The caller holds the checkout's setup lock."""
    log, names = report["actions"], {action["action"] for action in report["planned"]}
    if creates and report["interpreter"]["status"] == "missing" and install:
        install_interpreter(spec, key, log, run, which)
        report["interpreter"] = resolve_interpreter(spec, key, python, run, which)
    if creates and report["interpreter"]["status"] != "found":
        report["outcome"] = "interpreter-" + report["interpreter"]["status"]
        return
    if "create-smoke-environments" in names:
        report["smoke_environments"] = prepare_package_smoke(report["interpreter"]["path"], work, log, run)
    if "rebuild-environment" in names:
        remove_environment(root, spec, log, run, which)
    if names & {"create-environment", "rebuild-environment"}:
        create_environment(root, spec, key, report["interpreter"]["path"], log, run)
    for action in report["planned"]:
        if action["action"] == "install-packages":
            install_packages(root, spec, action["lock"], action["packages"], list(wheels), log, run)
    run_visual(root, spec, report["planned"], report["observed"]["visual"], log, run, which)


def finish(report: dict, root: Path, spec: dict, run, outcome: str) -> dict:
    """Run the smoke checks that the reached state allows and settle the outcome."""
    observed = report["observed"]
    if spec["profiles"][report["profile"]]["kind"] == "environment" and observed["readiness"]["core"]["state"] == "ready":
        report["smoke"] = smoke_checks(root, spec, run)
    report["outcome"] = outcome
    if any(not item["passed"] for item in report["smoke"]):
        report["selected"] = dict(observed["selected"], next_action="Inspect the smoke check that did not pass before using this environment.")
    return report


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
    lines += [f"  done: {item['action']} (status {item['code']}, {item['seconds']} s)" for item in report["actions"]]
    lines += [f"  smoke: {item['check']} {'passed' if item['passed'] else 'did not pass: ' + str(item['detail'])}" for item in report["smoke"]]
    if report.get("failure"):
        lines.append(f"  failure: {report['failure']}")
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
    if args.report and args.report.exists():
        print(f"The report file must be new: {args.report}", file=sys.stderr)
        return REFUSED
    try:
        report = bootstrap(args.root, args.profile, preview=args.preview, python=args.python, rebuild=args.rebuild,
                           repair_node=args.repair_node, wheels=[path.resolve() for path in args.find_links], work=args.work_dir,
                           install=args.install_interpreter, node=args.node)
    except (Refusal, doctor.SpecificationError) as error:
        print(f"Setup refused: {error}", file=sys.stderr)
        return REFUSED
    except Busy as error:
        print(str(error), file=sys.stderr)
        return BUSY
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
