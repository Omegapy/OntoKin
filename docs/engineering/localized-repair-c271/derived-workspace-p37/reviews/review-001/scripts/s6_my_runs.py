"""W3 (C271-P37 S7): the reviewer's three module runs, read with MR's collector and compared with S5's runs.

Usage: python3 -I -S -B s6_my_runs.py WORKTREE LOCAL TMPDIR_RESOLVED OUTPUT
"""
import hashlib
import importlib.util
import json
import os
import sys

TOOL = "docs/engineering/localized-repair-c271/macos-routine-p36/tooling/unit_log_outcomes.py"
TOOL_SHA256 = "0b5269402005584ffa8c0fe4510a1f1d728f7922414a0d38cf841851e29cc75b"
RUNS = {"tests.test_current_host_readback_derived_controls_v02": "derived-controls",
        "tests.test_local_checks": "local-checks",
        "tests.test_current_host_readback_provider_v02": "provider-v02"}


def main(worktree, local, tmpdir, output):
    path = os.path.join(worktree, TOOL)
    if hashlib.sha256(open(path, "rb").read()).hexdigest() != TOOL_SHA256:
        raise SystemExit("MR's collector differs from its reviewed bytes")
    spec = importlib.util.spec_from_file_location("unit_log_outcomes_w3", path)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    normalize = tool.Normalizer({"steps": []}, [tmpdir])
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = {"schema": "w3.c271-p37.reviewer-runs/1", "command": "/usr/bin/env -i HOME=<home> LOGNAME=<logname> "
           "USER=<user> PATH=/usr/bin:/bin TMPDIR=<resolved tmp>/ .venv/bin/python -B -m unittest <module> -v",
           "cwd": "<worktree>", "runs": []}
    for module, stem in RUNS.items():
        log = os.path.join(here, "runs", stem + ".log")
        raw = open(log, "rb").read()
        mine = tool.collect_log(raw)
        s5 = tool.collect_log(open(os.path.join(local, "c271-p37/checks/s5-001", module + ".txt"), "rb").read())
        unchanged, lists = tool.compare_records(s5["tests"] + s5["fixtures"], mine["tests"] + mine["fixtures"],
                                                normalize, normalize)
        out["runs"].append({
            "module": module, "log": "runs/" + stem + ".log", "log_sha256": hashlib.sha256(raw).hexdigest(),
            "started_at_utc": open(os.path.join(here, "runs", stem + ".start.txt")).read().strip(),
            "ended_at_utc": open(os.path.join(here, "runs", stem + ".end.txt")).read().strip(),
            "exit": int(open(os.path.join(here, "runs", stem + ".exit.txt")).read()),
            "footer": mine["footer"]["result_line"], "ran": mine["footer"]["ran"],
            "by_outcome": {k: v for k, v in mine["counts"]["by_outcome"].items() if v},
            "fixtures": mine["fixtures"], "checks": mine["checks"],
            "against_s5": {"unchanged": {k: v for k, v in unchanged.items() if v},
                           "differences": {k: [e["id"] for e in v] for k, v in lists.items() if v}}})
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:5])
