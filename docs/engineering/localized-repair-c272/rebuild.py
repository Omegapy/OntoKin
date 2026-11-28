"""C272 clean rebuild (TASK-019, REQ-018, DEC-007): the package-smoke procedure applied to delivered source.

The harness side imports no product module. It builds a wheel from the exact revision
with `git archive`, installs only that wheel into a clean environment outside every
checkout, and then runs the declared rebuild entry in new, empty workspaces. Each
workspace holds only the delivered `main.ok`, `hinges.ok` and `rebuild_entry.py`. The
rebuilt bytes are compared exactly with the delivered ones; no field is exempted.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
ENTRY = Path(__file__).resolve().parent / "rebuild_entry.py"
DECLARED = ["hinges.ok", "main.ok"]
ARTIFACTS = ["scene.glb", "scene.semantic.json"]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def run(command, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in command], capture_output=True, text=True, check=True, **kwargs)


def checkouts() -> list[Path]:
    """Every checkout of this repository: the main checkout and all its worktrees."""
    listing = run(["git", "worktree", "list", "--porcelain"], cwd=ROOT).stdout
    return [Path(line[len("worktree "):]).resolve() for line in listing.splitlines() if line.startswith("worktree ")]


def inside_checkout(path: Path) -> bool:
    """True when PATH lies inside any checkout of this repository."""
    path = Path(path).resolve()
    return any(path == root or path.is_relative_to(root) for root in checkouts())


def prepare(work: Path, revision: str) -> dict:
    """Create the clean build and install environments and the wheel of REVISION."""
    if work.exists():
        raise SystemExit("the rebuild work directory must be new; the setup tool creates it")
    if inside_checkout(work.resolve().parent):
        raise SystemExit("the rebuild work directory must lie outside every checkout")
    python = shutil.which("python3.12") or sys.executable
    bootstrap = run([python, ROOT / "tools/bootstrap_local.py", "--profile", "package-smoke", "--work-dir", work], cwd=ROOT)
    (work / "logs").mkdir()
    (work / "logs/bootstrap.log").write_text(bootstrap.stdout + bootstrap.stderr)
    for name in ("source", "dist", "home", "workspaces"):
        (work / name).mkdir()
    archive = subprocess.run(["git", "archive", "--format=tar", revision], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(work / "source")], input=archive, check=True)
    epoch = run(["git", "show", "-s", "--format=%ct", revision], cwd=ROOT).stdout.strip()
    build, install = work / "build-env/bin/python", work / "install-env/bin/python"
    pip = ["-I", "-m", "pip", "--isolated", "--disable-pip-version-check"]
    steps = [[build, *pip, "install", "--only-binary=:all:", "--no-input", "setuptools>=77"],
             [build, *pip, "wheel", "--no-build-isolation", "--no-deps", "--no-input", "--no-cache-dir",
              "--wheel-dir", work / "dist", work / "source"]]
    env = {**os.environ, "SOURCE_DATE_EPOCH": epoch}
    for index, step in enumerate(steps):
        result = run(step, cwd=work, env=env)
        (work / f"logs/build-{index}.log").write_text(result.stdout + result.stderr)
    wheels = sorted((work / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected one wheel, found {len(wheels)}")
    result = run([install, *pip, "install", "--no-index", "--no-deps", "--no-input", wheels[0]], cwd=work)
    (work / "logs/install.log").write_text(result.stdout + result.stderr)
    versions = lambda py: json.loads(run([py, "-I", "-c", "import json, importlib.metadata as m; print(json.dumps({d.metadata['Name']: d.version for d in m.distributions()}))"]).stdout)
    tree = run(["git", "rev-parse", f"{revision}^{{tree}}"], cwd=ROOT).stdout.strip()
    return {"revision": revision, "tree": tree, "source_date_epoch": int(epoch),
            "wheel": {"filename": wheels[0].name, "bytes": wheels[0].stat().st_size, "sha256": sha256(wheels[0].read_bytes())},
            "build_environment": versions(build), "install_environment": versions(install),
            "interpreter": run([install, "-I", "-c", "import platform; print(platform.python_version())"]).stdout.strip(),
            "install_python": str(install)}


def rebuild_case(work: Path, prepared: dict, label: str, source_files: dict, undeclared: dict | None = None) -> dict:
    """Rebuild one delivered source closure in a new, empty workspace.

    UNDECLARED, used only by an evaluator control, places extra files in the workspace.
    """
    workspace = work / "workspaces" / label
    workspace.mkdir()
    empty_before = not any(workspace.iterdir())
    for name in DECLARED:
        (workspace / name).write_bytes(source_files[name])
    (workspace / ENTRY.name).write_bytes(ENTRY.read_bytes())
    for name, raw in (undeclared or {}).items():
        (workspace / name).write_bytes(raw)
    listing = [{"name": p.name, "bytes": p.stat().st_size, "sha256": sha256(p.read_bytes())}
               for p in sorted(workspace.iterdir())]
    command = [prepared["install_python"], "-I", "-B", ENTRY.name]
    env = {"HOME": str(work / "home"), "PATH": "/usr/bin:/bin"}
    process = subprocess.run(command, cwd=workspace, env=env, capture_output=True, text=True)
    record = {"label": label, "workspace_empty_before_inputs": empty_before, "listing_before_run": listing,
              "invocation": {"argv": ["<install-env>/bin/python", "-I", "-B", ENTRY.name],
                             "cwd": "<workspace>", "environment": {"HOME": "<work>/home", "PATH": "/usr/bin:/bin"}},
              "exit_code": process.returncode, "stderr_tail": process.stderr[-2000:]}
    if process.returncode != 0:
        return {**record, "status": "failed"}
    report = json.loads((workspace / "out/rebuild-report.json").read_text())
    install_root = (work / "install-env").resolve()
    locations = [Path(p) for p in report["ontokin_modules_loaded"]]
    record.update({
        "status": "completed",
        "artifacts": {name: (workspace / "out" / name).read_bytes() for name in ARTIFACTS},
        "sources_used": {name: (workspace / name).read_bytes() for name in DECLARED},
        "program_revision": report["program_revision"], "implementation": report["implementation"],
        "python": report["python"], "isolated_flag": report["flags"]["isolated"],
        "import_locations": {"ontokin_package": "<install-env>/" + str(Path(report["ontokin_package"]).relative_to(install_root)),
                             "modules": len(locations),
                             "all_in_install_env": all(p.is_relative_to(install_root) for p in locations),
                             "any_in_a_checkout": any(inside_checkout(p) for p in locations)},
        "sys_path_inside_checkout": any(inside_checkout(Path(p)) for p in report["sys_path"] if p),
    })
    record["clean"] = (empty_before and [x["name"] for x in listing] == sorted(DECLARED + [ENTRY.name])
                       and record["isolated_flag"] == 1 and record["import_locations"]["all_in_install_env"]
                       and not record["import_locations"]["any_in_a_checkout"] and not record["sys_path_inside_checkout"])
    return record


def compare(delivered: dict, rebuilt: dict) -> dict:
    return {name: {"delivered_sha256": sha256(delivered[name]), "rebuilt_sha256": sha256(rebuilt[name]),
                   "byte_identical": delivered[name] == rebuilt[name]} for name in ARTIFACTS}
