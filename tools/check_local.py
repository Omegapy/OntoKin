#!/usr/bin/env python3
"""Run OntoKin's existing checks locally without installing or publishing anything.

The default profile runs the seven Python reference checks. --full also builds
and verifies the visual examples with already installed Node tools and Chromium.
Reports certify only the checks executed here, not a complete release gate.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("ontokin", "tests", "tools", "docs", "examples", "schemas", "prototypes", ".github")
ROOT_FILES = ("pyproject.toml", "README.md", "AGENTS.md", "GOAL.md", "STATUS.md", "LICENSE", ".gitignore")
IGNORED = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tox", ".cache",
           ".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", "_build"}
GENERATED_EXAMPLES = {
    "examples/visual/demo-data.js", "examples/visual/viewer.bundle.js", "examples/visual/THREE-LICENSE.txt",
    *["examples/agent/" + name for name in ("workflow.json", "repaired.ok", "rejected-candidate.ok")],
    *["examples/construction/" + name for name in ("workflow.json", "authoring.ok", "rejected-candidate.ok",
                                                  "main.ok", "hinges.ok", "program.bundle.json", "program.files.json")],
}


@dataclass(frozen=True)
class Step:
    id: str
    argv: tuple[str, ...]
    requires: tuple[str, ...] = ()
    reports: tuple[Path, ...] = ()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def file_identity(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"sha256": "sha256:" + digest.hexdigest(), "bytes": path.stat().st_size}


def ignored(name: str) -> bool:
    return name in IGNORED or name == ".env" or name.startswith(".env.") or name.endswith((".pyc", ".pyo"))


def source_files(root: Path) -> list[Path]:
    """Inventory source and preserved evidence, including all original examples."""
    paths = [root / name for name in ROOT_FILES if (root / name).is_file()]
    for name in SOURCE_DIRS:
        directory = root / name
        if directory.is_symlink():
            raise ValueError(f"Source directory is a symbolic link: {directory}")
        if not directory.is_dir():
            continue
        for parent, directories, files in os.walk(directory, followlinks=False):
            directories[:] = sorted(d for d in directories if not ignored(d))
            for child in directories:
                if (Path(parent) / child).is_symlink():
                    raise ValueError(f"Source directory is a symbolic link: {Path(parent) / child}")
            for filename in sorted(files):
                if ignored(filename):
                    continue
                path = Path(parent) / filename
                paths.append(path)
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Source file is a symbolic link: {path}")
    return sorted(paths)


def inventory(root: Path) -> dict:
    files = [{"path": p.relative_to(root).as_posix(), **file_identity(p)} for p in source_files(root)]
    return inventory_records(files)


def inventory_records(files: list[dict]) -> dict:
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {"sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(), "file_count": len(files), "files": files}


def immutable_workspace_inputs(records: dict) -> dict:
    """Only the isolated workspace may regenerate these explicitly named products."""
    def generated(name: str) -> bool:
        return name in GENERATED_EXAMPLES or (name.startswith(("examples/visual/", "examples/agent/", "examples/construction/"))
                                               and name.endswith((".glb", ".export.json", ".reference.json")))
    return inventory_records([item for item in records["files"] if not generated(item["path"])])


def git_metadata(root: Path) -> dict:
    """Read local metadata only; a parent repository is not this source checkout."""
    def read(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL,
                                       text=True, timeout=10).strip()
    try:
        if Path(read("rev-parse", "--show-toplevel")).resolve() != root.resolve():
            return {"available": False, "reason": "No Git checkout rooted at this source directory."}
        return {"available": True, "local_head": read("rev-parse", "HEAD"),
                "local_tree": read("rev-parse", "HEAD^{tree}"),
                "tracked_worktree_status": read("status", "--porcelain=v1", "--untracked-files=no"),
                "untracked_source_files": [name for name in read("ls-files", "--others", "--exclude-standard", "-z").split("\0")
                                           if name and (name.split("/")[0] in SOURCE_DIRS or name in ROOT_FILES)
                                           and not any(ignored(part) for part in name.split("/"))],
                "head_is_base_revision": True, "source_inventory_includes_untracked_files": True,
                "remote_head_verified": False}
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "reason": "Local Git metadata unavailable; use the source inventory."}


def prepare_output(root: Path, output: Path) -> None:
    if output == root or root in output.parents and output.relative_to(root).parts[0] != "build":
        raise ValueError("Keep results beneath build/ or outside the repository, away from source/evidence files.")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError(f"Output directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def prepare_workspace(root: Path, output: Path, full: bool) -> Path:
    """Retain an isolated copy so fixed-path builders cannot overwrite the checkout."""
    workspace = output / "workspace"
    workspace.mkdir()
    def exclude(directory: str, names: list[str]) -> list[str]:
        excluded = [name for name in names if ignored(name)]
        for name in names:
            if name not in excluded and (Path(directory) / name).is_symlink():
                raise ValueError(f"Cannot copy a source symbolic link: {Path(directory) / name}")
        return excluded
    for name in SOURCE_DIRS:
        if (root / name).exists():
            shutil.copytree(root / name, workspace / name, ignore=exclude)
    for name in ROOT_FILES:
        if (root / name).is_file():
            shutil.copy2(root / name, workspace / name)
    dependencies = root / "tools/node_modules"
    if full and dependencies.is_dir():
        # Verification commands only read these installed tools; they never install.
        (workspace / "tools/node_modules").symlink_to(dependencies.resolve(), target_is_directory=True)
    return workspace


NODE_PREFLIGHT = r"""
const fs = require('node:fs');
const path = require('node:path');
const expected = require('./tools/package.json').devDependencies;
if (Number(process.versions.node.split('.')[0]) < 18) throw Error('Node 18 or later is required; hosted checks use Node 22.');
for (const [name, version] of Object.entries(expected)) {
  const actual = JSON.parse(fs.readFileSync(path.join('tools/node_modules', name, 'package.json'))).version;
  if (actual !== version) throw Error(`${name}: installed ${actual}, expected ${version}; install the pinned tools separately.`);
}
fs.writeFileSync(process.argv[1], JSON.stringify({node:process.version, platform:process.platform,
  architecture:process.arch, dependencies:expected}, null, 2) + '\n');
"""
BROWSER_PREFLIGHT = r"""
const fs = require('node:fs');
const {chromium} = require('./tools/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle',
    '--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try { fs.writeFileSync(process.argv[1], JSON.stringify({browser:browser.version(),
    platform:process.platform, architecture:process.arch}, null, 2) + '\n'); }
  finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
"""


def build_plan(workspace: Path, output: Path, full: bool, python: str = sys.executable) -> list[Step]:
    reports, artifacts = output / "reports", output / "artifacts"
    steps: list[Step] = []
    node = shutil.which("node") or "node"
    def add(id: str, argv: list, requires: tuple[str, ...] = (), report: Path | None = None) -> None:
        steps.append(Step(id, tuple(map(str, argv)), requires, (report,) if report else ()))
    add("unit-tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"])
    for id, command in (
        ("source", ["-m", "ontokin", "conformance"]),
        ("agent", ["tools/run_agent_conformance.py"]),
        ("construction", ["-m", "tools.verify_construction_ci", "--external-evidence",
                          "docs/engineering/construction-validation/external-gate.json"]),
        ("surface", ["tools/run_surface_conformance.py", "--allow-pending"]),
        ("impulse", ["tools/run_impulse_conformance.py", "--allow-pending"]),
    ):
        report = reports / f"{id}.json"
        add(id, [python, *command, "--output", report], report=report)
    add("documents", [python, "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"])
    if not full:
        return steps
    for id, script in (("node-tools", NODE_PREFLIGHT), ("browser-ready", BROWSER_PREFLIGHT)):
        report = reports / f"{id}.json"
        add(id, [node, "-e", script, report], ("node-tools",) if id == "browser-ready" else (), report)
    prototype = artifacts / "surface-prototype"
    add("prototype-build", [python, "-m", "tools.build_surface_prototype", "--output-dir", prototype])
    report = reports / "surface-prototype.json"
    add("prototype-format", [node, "tools/verify_surface_prototype.mjs", prototype / "offset-taper.glb", "--output", report],
        ("prototype-build", "node-tools"), report)
    for id, builder, checker in (
        ("surface-native", "build_surface_demo.py", "verify_surface_native.mjs"),
        ("surface-agent", "build_surface_agent_demo.py", "verify_surface_native.mjs"),
        ("impulse-agent", "build_impulse_agent_demo.py", "verify_impulse_native.mjs"),
    ):
        directory, report = artifacts / id, reports / f"{id}-destination.json"
        add(id + "-build", [python, "tools/" + builder, "--output-dir", directory])
        add(id + "-format", [node, "tools/" + checker, "--demo-dir", directory, "--output", report],
            (id + "-build", "node-tools"), report)
    add("viewer-build", [node, "tools/build_viewer.mjs"], ("node-tools",))
    add("visual-build", [python, "tools/build_visual_demos.py", "--include-conformance"])
    for id, builder in (("visual", None), ("agent-demo", "build_agent_demo.py"),
                        ("construction-demo", "build_construction_demo.py")):
        directory = {"visual": "visual", "agent-demo": "agent", "construction-demo": "construction"}[id]
        if builder:
            add(id + "-build", [python, "tools/" + builder])
        report = reports / f"{id}-destination.json"
        add(id + "-format", [node, "tools/verify_gltf.mjs", "examples/" + directory, "--output", report],
            (id + "-build", "node-tools"), report)
    for id, checker in (("visual", "verify_viewer.mjs"), ("agent-demo", "verify_agent_viewer.mjs"),
                        ("construction-demo", "verify_construction_viewer.mjs")):
        directory = artifacts / f"{id}-browser"
        add(id + "-browser", [node, "tools/" + checker, "--output-dir", directory],
            (id + "-format", "viewer-build", "visual-build", "browser-ready"), directory / "viewer-results.json")
    for id, checker, fixtures in (
        ("surface-native", "verify_surface_viewer.mjs", ()),
        ("surface-agent", "verify_surface_viewer.mjs", ("palette-repaired", "composition-ordinary", "composition-generated", "rotated-release")),
        ("impulse-agent", "verify_impulse_viewer.mjs", ()),
    ):
        argv = [node, "tools/" + checker, "--demo-dir", artifacts / id,
                "--output-dir", artifacts / (id + "-browser")]
        for fixture in fixtures:
            argv.extend(["--fixture", fixture])
        report_name = "browser-validation.json" if id == "impulse-agent" else "browser-results.json"
        add(id + "-browser", argv, (id + "-format", "browser-ready"), artifacts / (id + "-browser") / report_name)
    return steps


def stop_process(process: subprocess.Popen) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=5)
    except ProcessLookupError:
        pass
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def execute_step(step: Step, workspace: Path, output: Path, previous: dict, timeout: float) -> dict:
    log_path = output / "logs" / (step.id + ".log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"id": step.id, "argv": list(step.argv), "cwd": str(workspace), "requires": list(step.requires),
              "started_at": utc_now(), "log": log_path.relative_to(output).as_posix(), "returncode": None}
    started = time.monotonic()
    with log_path.open("x", encoding="utf-8") as log:
        blocked = [name for name in step.requires if previous.get(name, {}).get("status") != "passed"]
        if blocked:
            record.update(status="blocked", reason="Prerequisite checks did not pass: " + ", ".join(blocked))
            log.write(record["reason"] + "\n")
        else:
            try:
                process = subprocess.Popen(step.argv, cwd=workspace, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=os.name == "posix")
                try:
                    record["returncode"] = process.wait(timeout=timeout)
                    record["status"] = "passed" if process.returncode == 0 else "failed"
                except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
                    stop_process(process)
                    record.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                                  reason="Interrupted" if isinstance(error, KeyboardInterrupt) else f"Exceeded {timeout:g} seconds",
                                  returncode=process.returncode)
            except OSError as error:
                record.update(status="unavailable", reason=str(error))
                log.write(str(error) + "\n")
    if step.id == "unit-tests":
        raw = log_path.read_text(encoding="utf-8", errors="replace")
        executions = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", raw, re.MULTILINE)
        endings = re.findall(r"^(?:OK|FAILED)(?: \(([^\n]*)\))?$", raw, re.MULTILINE)
        counts = dict(re.findall(r"([a-z ]+)=(\d+)", endings[-1])) if endings else {}
        skipped, expected_failures = int(counts.get("skipped", 0)), int(counts.get("expected failures", 0))
        count = int(executions[-1][0]) if executions else 0
        record["test_execution"] = {"tests_run": count, "skipped": skipped, "expected_failures": expected_failures,
                                    "executed_without_skips": max(0, count - skipped),
                                    "complete_regression_passed": bool(count and not skipped and not expected_failures
                                                                       and record["status"] == "passed")}
        if record["status"] == "passed" and not record["test_execution"]["complete_regression_passed"]:
            record.update(status="failed", reason="The complete unittest suite did not execute and pass without skips or expected failures.")
    record["reports"] = []
    for path in step.reports:
        if not path.is_file():
            if record["status"] == "passed":
                record.update(status="failed", reason=f"Expected report was not produced: {path}")
            continue
        item = {"path": path.relative_to(output).as_posix(), **file_identity(path)}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Report must be a JSON object")
            item["outcomes"] = {key: data[key] for key in ("summary", "full_gate_complete", "implementation") if key in data}
            item["pending_cases"] = [{"id": case.get("id"), "reasons": case.get("pending_reasons", [])}
                                     for case in data.get("cases", []) if case.get("status") == "pending"]
        except (OSError, ValueError, TypeError, AttributeError) as error:
            item["read_error"] = str(error)
            if record["status"] == "passed":
                record.update(status="failed", reason=f"Cannot read expected report: {path}")
        record["reports"].append(item)
    record.update(finished_at=utc_now(), duration_seconds=round(time.monotonic() - started, 3), log_identity=file_identity(log_path))
    return record


def run(root: Path, output: Path, full: bool, timeout: float) -> int:
    prepare_output(root, output)
    summary = {"schema_version": "ontokin.local-checks/0.1", "profile": "full" if full else "core",
               "started_at": utc_now(), "status": "running", "source_root": str(root),
               "environment": {"python": sys.version, "python_executable": sys.executable,
                               "platform": platform.platform(), "architecture": platform.machine()},
               "git": git_metadata(root), "steps": [], "release_certified": False,
               "full_product_conformance_certified": False, "remote_checks_executed": False,
               "limits": ["This run checks one installed Python version; it is not the three-version matrix.",
                          "Pending external conformance attestations remain pending, including after full visual checks.",
                          "Generated captures require actual visual review; this runner does not supply that review."]}
    summary_path, started = output / "summary.json", time.monotonic()
    write_json(summary_path, summary)
    exit_code = 1
    try:
        before = inventory(root)
        write_json(output / "source-before.json", before)
        summary["source_inventory"] = {"path": "source-before.json", **file_identity(output / "source-before.json"),
                                       "inventory_sha256": before["sha256"], "file_count": before["file_count"],
                                       "includes_untracked_source_files": True}
        summary["workspace_generated_exclusions"] = {"files": sorted(GENERATED_EXAMPLES),
            "patterns": ["examples/{visual,agent,construction}/*.{glb,export.json,reference.json}"],
            "scope": "Only the isolated workspace comparison; all original checkout example bytes are preserved and checked."}
        workspace = prepare_workspace(root, output, full)
        if inventory(workspace) != before:
            raise ValueError("Source changed while the isolated workspace was copied.")
        (output / "reports").mkdir()
        (output / "artifacts").mkdir()
        previous = {}
        for step in build_plan(workspace, output, full):
            print(f"[{step.id}] running", flush=True)
            record = execute_step(step, workspace, output, previous, timeout)
            previous[step.id] = record
            summary["steps"].append(record)
            write_json(summary_path, summary)
            print(f"[{step.id}] {record['status']} ({record['duration_seconds']:.1f}s)", flush=True)
            if record["status"] == "interrupted":
                exit_code = 130
                break
        after = inventory(root)
        write_json(output / "source-after.json", after)
        summary["source_unchanged"] = after == before and immutable_workspace_inputs(inventory(workspace)) == immutable_workspace_inputs(before)
        summary["pending_external_cases"] = [dict(step=step["id"], report=report["path"], **case)
                                              for step in summary["steps"] for report in step["reports"]
                                              for case in report.get("pending_cases", [])]
        if not summary["source_unchanged"]:
            raise ValueError("Source or verification inputs changed during this run.")
        if exit_code != 130:
            exit_code = 0 if all(step["status"] == "passed" for step in summary["steps"]) else 1
        summary["status"] = "passed" if exit_code == 0 else "interrupted" if exit_code == 130 else "failed"
    except KeyboardInterrupt:
        summary.update(status="interrupted", error="Interrupted before checks completed.")
        exit_code = 130
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        summary.update(status="failed", error=str(error))
    finally:
        summary.update(finished_at=utc_now(), duration_seconds=round(time.monotonic() - started, 3), exit_code=exit_code)
        write_json(summary_path, summary)
        print(f"Local checks {summary['status']}. Evidence: {summary_path}", flush=True)
        if summary.get("pending_external_cases"):
            print("External release attestations remain pending; see summary.json.", flush=True)
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Also execute visual checks with already installed Node tools and Chromium")
    parser.add_argument("--output-dir", type=Path, help="New/empty evidence directory; default: build/local-checks/<unique-run>")
    parser.add_argument("--list", "--dry-run", dest="list_only", action="store_true", help="Print commands without running checks or writing files")
    parser.add_argument("--timeout", type=float, default=900, help="Maximum seconds per command (default: 900)")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or later is required.")
    if not args.timeout > 0 or not args.timeout < float("inf"):
        parser.error("--timeout must be a finite positive number.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = (args.output_dir or ROOT / "build/local-checks" / stamp).resolve()
    if args.list_only:
        print(json.dumps({"profile": "full" if args.full else "core", "output_dir": str(output),
                          "steps": [{"id": s.id, "argv": list(s.argv), "requires": list(s.requires)}
                                    for s in build_plan(output / "workspace", output, args.full)]}, indent=2))
        return 0
    try:
        return run(ROOT, output, args.full, args.timeout)
    except (OSError, ValueError) as error:
        print(f"Cannot start local checks: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
