#!/usr/bin/env python3
"""Run the complete affected engineering-observer cohort for C270 evidence."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--phase", required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    def git(*items):
        return subprocess.check_output(["git", *items], cwd=repo, text=True).strip()
    def identity(path):
        raw = path.read_bytes()
        return {"path": str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path),
                "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    def inventory():
        paths = set()
        for component in (253, 257, 260, 261, 265, 266, 267, 270):
            folder = repo / f"docs/engineering/localized-repair-c{component}"
            paths.update(p for p in folder.glob("*.py"))
        paths.update((repo / "docs/engineering/localized-repair-c270/control").glob("*"))
        binding = json.loads((repo / "docs/engineering/localized-repair-c260/INPUTS.json").read_text())
        paths.update(repo / row["path"] for row in binding["files"])
        paths.update(repo / p for p in ("tools/chat_workflow.py", "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"))
        return [identity(p) for p in sorted(paths) if p.is_file()]
    before = inventory()
    report = {"schema": "ontokin.c270.affected-regressions/1", "phase": args.phase,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_revision": git("rev-parse", "HEAD"), "source_tree": git("rev-parse", "HEAD^{tree}"),
              "tracked_dirty_status": git("status", "--porcelain", "--untracked-files=no"),
              "environment": {"python": sys.version, "platform": platform.platform(),
                              "executable": identity(Path(sys.executable).resolve()), "PYTHONDONTWRITEBYTECODE": "1"},
              "inputs": before, "checks": [], "expected_methods": 108,
              "limits": ["Complete affected C265/C266/C267 engineering controls only",
                         "C270 new H16 result is separate and cannot be overridden by regression passes",
                         "Full product aggregate, check_local driver, source conformance, native/visual/model and other interpreter checks not run; no product implementation changed"]}
    def save():
        (out / "CHECKS.json").write_text(json.dumps(report, indent=2) + "\n")
    save()
    if report["tracked_dirty_status"]:
        report["setup_failure"] = "Tracked source dirty"
        save()
        return 2
    commands = [("fixture", ["docs/engineering/localized-repair-c270/control/build_control.py", "--check"], None),
                ("corpus", ["docs/engineering/localized-repair-c253/verify_manifest.py"], None)]
    for number, name, count in ((265, "source_hinges", 49), (266, "hinge_binding", 34), (267, "hinge_compare", 25)):
        commands.append((f"c{number}", [f"docs/engineering/localized-repair-c{number}/test_{name}.py", "--evidence-dir", str(out / f"c{number}-controls")], count))
    commands += [("workflow", ["tools/chat_workflow.py", "check", "--json"], None),
                 ("documentation", ["docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"], None)]
    report["planned_commands"] = [{"name": name, "command": [sys.executable, "-B", *cmd], "expected_methods": count} for name, cmd, count in commands]
    save()
    for name, command, count in commands:
        cmd = [sys.executable, "-B", *command]
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(cmd, cwd=repo, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        log = out / (name + ".log")
        log.write_bytes(result.stdout)
        text = result.stdout.decode("utf-8", errors="replace")
        matches = re.findall(r"(?m)^Ran (\d+) tests? in ", text)
        methods = int(matches[-1]) if matches else None
        checks = {"exit_zero": result.returncode == 0}
        if count is not None:
            checks["complete_methods"] = methods == count
            checks["zero_failure_error_skip"] = bool(re.search(r"(?m)^OK\r?$", text))
        if name == "corpus":
            values = json.loads(text)
            checks["fourteen_original_bindings"] = values.get("passed") is True and values.get("boundFiles") == 14
        checks["same_clean_source"] = git("rev-parse", "HEAD") == report["source_revision"] and not git("status", "--porcelain", "--untracked-files=no")
        item = {"name": name, "command": cmd, "started_at_utc": started,
                "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                "exit_code": result.returncode, "methods": methods, "assertions": checks,
                "passed": all(checks.values()), "log": identity(log)}
        report["checks"].append(item)
        save()
        print(json.dumps({"check": name, "passed": item["passed"], "methods": methods}), flush=True)
    report["input_identity_unchanged"] = before == inventory()
    report["total_methods"] = sum(row["methods"] or 0 for row in report["checks"])
    report["passed"] = all(row["passed"] for row in report["checks"]) and report["total_methods"] == 108 and report["input_identity_unchanged"]
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    save()
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
