#!/usr/bin/env python3
"""Run the declared C266 cohort against an identified, stable Git checkout."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def file_identity(path, root=None):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(root)) if root else str(path),
            "bytes": len(raw), "sha256": digest(raw)}


def inputs(repo):
    selected = set()
    for component in (253, 255, 256, 257, 258, 260, 261, 265, 266):
        folder = repo / f"docs/engineering/localized-repair-c{component}"
        selected.update(p for p in folder.iterdir()
                        if p.is_file() and p.suffix in {".py", ".json", ".md"})
    corpus = json.loads((repo / "docs/engineering/localized-repair-c253/corpus.json").read_text())
    selected.update(repo / row["path"] for row in corpus["files"].values())
    required = (
        "tools/chat_workflow.py", "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py",
        "AGENTS.md", "GOAL.md", "ROLE.md", "STATUS.md", "CHATGPT-START-HERE.md",
        "docs/language-design/OK-LANG-001-core-language-specification.md",
        "docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md",
        "docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md",
        "docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md",
        "docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md",
    )
    selected.update(repo / name for name in required)
    selected.update((repo / "docs/workflow").glob("*.json"))
    selected.update((repo / "docs/workflow").glob("*.md"))
    selected.update((repo / "docs/workflow/tasks/C266").glob("*.json"))
    selected.update((repo / "docs/workflow/tasks/C266").glob("*.md"))
    selected.update((repo / ".agents/skills").glob("*/SKILL.md"))
    return [file_identity(p, repo) for p in sorted(selected)]


def source_state(repo):
    return {"commit": git(repo, "rev-parse", "HEAD"),
            "tree": git(repo, "rev-parse", "HEAD^{tree}"),
            "tracked_dirty_status": git(repo, "status", "--porcelain", "--untracked-files=no"),
            "all_dirty_status": git(repo, "status", "--porcelain"),
            "shallow_checkout": git(repo, "rev-parse", "--is-shallow-repository") == "true"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    py = sys.executable
    checks = [{"name": "c253-corpus", "expected_methods": None,
               "command": [py, "-B", "docs/engineering/localized-repair-c253/verify_manifest.py"]}]
    suites = [(255, "oracle", 31), (256, "reader", 29), (257, "ownership", 23),
              (258, "follows", 28), (261, "hinge_glb", 28), (265, "source_hinges", 49)]
    for number, name, count in suites:
        checks.append({"name": f"c{number}-{name}", "expected_methods": count,
                       "command": [py, "-B", "-m", "unittest", "discover", "-s",
                                   f"docs/engineering/localized-repair-c{number}", "-p",
                                   f"test_{name}.py", "-v"]})
    checks.extend([
        {"name": "c266-binding", "expected_methods": 34,
         "command": [py, "-B", "docs/engineering/localized-repair-c266/test_hinge_binding.py",
                     "--evidence-dir", str(out / "c266-controls")]},
        {"name": "workflow", "expected_methods": None,
         "command": [py, "-B", "tools/chat_workflow.py", "check", "--json"]},
        {"name": "documentation", "expected_methods": None,
         "command": [py, "-B", "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"]},
    ])
    start_state, before = source_state(repo), inputs(repo)
    binary = Path(sys.executable).resolve()
    report = {
        "schema": "ontokin.c266.identified-checks/0.1", "phase": args.phase,
        "started_at": now(), "source_before": start_state,
        "provider": "assistant hosted Linux workspace; not owner computer or GitHub Actions",
        "environment": {"python": sys.version, "version_info": list(sys.version_info),
                        "implementation": platform.python_implementation(),
                        "cache_tag": sys.implementation.cache_tag,
                        "executable": sys.executable, "resolved_executable": file_identity(binary),
                        "platform": platform.platform(), "uname": list(platform.uname()),
                        "python_build": list(platform.python_build()), "python_compiler": platform.python_compiler(),
                        "runtime_bundle_version": os.environ.get("CODEX_PRIMARY_RUNTIME_BUNDLE_VERSION"),
                        "environment_overrides": {"PYTHONDONTWRITEBYTECODE": "1"}},
        "runner": file_identity(Path(__file__).resolve()),
        "input_files_before": before, "planned_checks": checks,
        "planned_check_count": len(checks), "expected_total_methods": 222,
        "checks": [], "completed_check_count": 0, "complete": False, "passed": False,
        "remaining_checks": [c["name"] for c in checks],
        "not_run": ["full product aggregate", "source conformance/export", "native/visual/model trials",
                    "other Python compatibility", "hosted workflows"],
        "limits": ["C266 input binding only; no complete C260 H group or hinge comparison",
                   "Historical failures unchanged; this cohort is not a full product release",
                   "Tracked Git tree and explicit inputs bind verification; untracked evidence is disclosed"],
    }
    def save():
        (out / "CHECKS.json").write_text(json.dumps(report, indent=2) + "\n")
    save()
    if start_state["tracked_dirty_status"]:
        report["setup_failure"] = "Tracked source was dirty before execution"
        save()
        return 1
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for check in checks:
        started, clock = now(), time.monotonic()
        output = b""
        code, failure = None, None
        try:
            result = subprocess.run(check["command"], cwd=repo, env=environment,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=args.timeout)
            output, code = result.stdout, result.returncode
        except subprocess.TimeoutExpired as error:
            output = error.stdout or b""
            failure = f"Timeout after {args.timeout} seconds"
        except (OSError, subprocess.SubprocessError) as error:
            failure = f"{type(error).__name__}: {error}"
        log = out / (check["name"] + ".log")
        log.write_bytes(output)
        text = output.decode("utf-8", errors="replace")
        matches = re.findall(r"(?m)^Ran (\d+) tests? in ", text)
        methods = int(matches[-1]) if matches else None
        assertions = {"exit_zero": code == 0}
        details = {}
        if check["expected_methods"] is not None:
            assertions["expected_method_count"] = methods == check["expected_methods"]
            assertions["zero_failures_errors_skips_expected_failures"] = bool(re.search(r"(?m)^OK\r?$", text))
        try:
            if check["name"] == "c253-corpus":
                details = json.loads(text)
                assertions["corpus_identity"] = details.get("passed") is True and details.get("boundFiles") == 14 and details.get("tasks") == 3
            elif check["name"] == "workflow":
                details = json.loads(text)
                assertions["workflow_structure"] = details.get("passed") is True and details.get("errors") == []
            elif check["name"] == "documentation":
                details = json.loads(text)
                assertions["preservation_and_links"] = details.get("status") == "passed" and details.get("failures") == []
            elif check["name"] == "c266-binding":
                controls = json.loads((out / "c266-controls/results.json").read_text())
                details = {key: controls[key] for key in ("passed", "testMethods", "apiCalls", "boundCalls", "typedRefusals", "failures", "errors", "skipped")}
                assertions["retained_controls_zero_failures_errors_skips"] = controls["passed"] is True and controls["failures"] == [] and controls["errors"] == [] and controls["skipped"] == []
                assertions["complete_expected_calls"] = (controls["apiCalls"], controls["boundCalls"], controls["typedRefusals"]) == (748, 28, 720)
                details["results_identity"] = file_identity(out / "c266-controls/results.json", out)
        except (OSError, ValueError, KeyError, TypeError) as error:
            failure = f"Result validation: {type(error).__name__}: {error}"
        current = source_state(repo)
        assertions["same_source_commit_tree"] = (current["commit"], current["tree"]) == (start_state["commit"], start_state["tree"])
        assertions["tracked_source_remains_clean"] = current["tracked_dirty_status"] == ""
        status = "passed" if failure is None and all(assertions.values()) else "failed"
        item = {**check, "started_at": started, "finished_at": now(),
                "seconds": round(time.monotonic() - clock, 6), "result": status,
                "exit_code": code, "methods": methods, "failure": failure,
                "assertions": assertions, "details": details,
                "log": file_identity(log, out)}
        report["checks"].append(item)
        report["completed_check_count"] = len(report["checks"])
        report["remaining_checks"] = [c["name"] for c in checks[len(report["checks"]):]]
        save()
        print(json.dumps({"check": check["name"], "result": status, "methods": methods, "seconds": item["seconds"], "failure": failure}), flush=True)
    report["finished_at"] = now()
    report["source_after"] = source_state(repo)
    report["input_files_after"] = inputs(repo)
    report["input_identity_unchanged"] = report["input_files_after"] == before
    report["complete"] = len(report["checks"]) == len(checks)
    report["total_methods"] = sum(c["methods"] or 0 for c in report["checks"])
    report["passed"] = (report["complete"] and report["input_identity_unchanged"]
                        and report["total_methods"] == report["expected_total_methods"]
                        and all(c["result"] == "passed" for c in report["checks"]))
    report["output_files"] = [file_identity(p, out) for p in sorted(out.rglob("*"))
                              if p.is_file() and p.name != "CHECKS.json"]
    save()
    print(json.dumps({"passed": report["passed"], "complete": report["complete"],
                      "checks": report["completed_check_count"], "methods": report["total_methods"],
                      "input_identity_unchanged": report["input_identity_unchanged"],
                      "report": str(out / "CHECKS.json")}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
