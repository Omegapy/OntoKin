#!/usr/bin/env python3
"""Run the recorded observer regression groups unchanged and record their outcomes.

The twelve groups and their command forms are those recorded in
docs/engineering/localized-repair-c270/correction/finalization-20261120/ACTUAL-MAIN-CHECKS.json.
`--with-c272` adds this scope's own test group. Output goes to a new directory
outside the checkout; the committed summary holds no machine-specific path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
RECORDED = {"c255-oracle": 31, "c256-reader": 29, "c257-ownership": 23, "c258-follows": 28,
            "c261-hinge_glb": 28, "c265-source_hinges": 49, "c266-binding": 34,
            "c267-comparison": 25, "c268-endpoint": 35}


def groups(evidence: Path, with_c272: bool) -> list[tuple[str, list[str]]]:
    unit = lambda d, p: ["-m", "unittest", "discover", "-s", f"docs/engineering/{d}", "-p", p, "-v"]
    rows = [
        ("c253-corpus", ["docs/engineering/localized-repair-c253/verify_manifest.py"]),
        ("c255-oracle", unit("localized-repair-c255", "test_oracle.py")),
        ("c256-reader", unit("localized-repair-c256", "test_reader.py")),
        ("c257-ownership", unit("localized-repair-c257", "test_ownership.py")),
        ("c258-follows", unit("localized-repair-c258", "test_follows.py")),
        ("c261-hinge_glb", unit("localized-repair-c261", "test_hinge_glb.py")),
        ("c265-source_hinges", unit("localized-repair-c265", "test_source_hinges.py")),
        ("c266-binding", ["docs/engineering/localized-repair-c266/test_hinge_binding.py", "--evidence-dir", str(evidence / "c266-controls")]),
        ("c267-comparison", ["docs/engineering/localized-repair-c267/test_hinge_compare.py", "--evidence-dir", str(evidence / "c267-controls")]),
        ("c268-endpoint", ["docs/engineering/localized-repair-c268/test_endpoint_reader.py", "--evidence-dir", str(evidence / "c268-controls")]),
        ("workflow", ["tools/chat_workflow.py", "check", "--json"]),
        ("documentation", ["docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"]),
    ]
    if with_c272:
        rows.append(("c272-qualification", unit("localized-repair-c272", "test_*.py")))
    return rows


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="new or empty directory outside the checkout")
    parser.add_argument("--with-c272", action="store_true", help="add this scope's own test group")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.is_relative_to(ROOT):
        parser.error("the output directory must lie outside the checkout")
    if out.exists() and any(out.iterdir()):
        parser.error("the output directory must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir()
    env = dict(os.environ)
    env["TMPDIR"] = str(Path(env.get("TMPDIR", "/tmp")).resolve())
    status_before = git("status", "--porcelain")
    record = {"schema": "ontokin.c272.observer-regression/1",
              "revision": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
              "clean_before": status_before == "",
              "executor": {"interpreter": platform.python_version(), "implementation": platform.python_implementation(),
                           "system": platform.system(), "release": platform.mac_ver()[0] or platform.release(),
                           "machine": platform.machine(), "executable": "checkout .venv/bin/python" if ".venv" in sys.executable else "other"},
              "temporary_directory": "resolved", "groups": []}
    for name, argv in groups(out / "evidence", args.with_c272):
        command = [sys.executable, "-B", *argv]
        started = time.monotonic()
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=env)
        seconds = round(time.monotonic() - started, 2)
        log = run.stdout + "\n--- stderr ---\n" + run.stderr
        (out / "logs" / f"{name}.log").write_text(log)
        found = re.findall(r"^Ran (\d+) tests? in", log, re.M)
        methods = int(found[-1]) if found else None
        summary = re.findall(r"^(OK.*|FAILED \(.*\))$", log, re.M)
        portable = [("python" if i == 0 else a) for i, a in enumerate(command)]
        portable = [a if not a.startswith(str(out)) else "OUTPUT_DIR" + a[len(str(out)):] for a in portable]
        record["groups"].append({"name": name, "command": portable, "exit_code": run.returncode,
                                 "result": "passed" if run.returncode == 0 else "failed",
                                 "methods": methods, "recorded_methods": RECORDED.get(name),
                                 "method_count_matches": None if name not in RECORDED else methods == RECORDED[name],
                                 "unittest_summary": summary[-1] if summary else None, "seconds": seconds,
                                 "log_sha256": hashlib.sha256(log.encode()).hexdigest()})
    record["clean_after"] = git("status", "--porcelain") == ""
    record["result"] = "passed" if all(g["result"] == "passed" for g in record["groups"]) else "failed"
    record["methods_total"] = sum(g["methods"] or 0 for g in record["groups"])
    (out / "RESULTS.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("revision", "result", "methods_total", "clean_before", "clean_after")}))
    for g in record["groups"]:
        print(f"{g['name']:22} {g['result']:7} methods={g['methods']} recorded={g['recorded_methods']} {g['seconds']}s")
    return 0 if record["result"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
