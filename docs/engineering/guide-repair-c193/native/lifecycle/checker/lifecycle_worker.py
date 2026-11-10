#!/usr/bin/env python3
"""Controlled subprocesses for the frozen lifecycle faults; never native proof."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("copy", "block", "log"))
    parser.add_argument("stage", type=Path)
    parser.add_argument("--seed", type=Path)
    args = parser.parse_args()
    if args.mode == "copy":
        for name in ("native-result.json", "scene.blend"):
            shutil.copyfile(args.seed / name, args.stage / name)
        (args.stage / "controlled-worker.json").write_text(json.dumps({
            "meaning": "Exact already-qualified native capture copied for a trusted transaction fault probe; no new native solve.",
            "seed_directory": str(args.seed), "pid": os.getpid(), "process_group": os.getpgrp()}) + "\n")
        return
    if args.mode == "log":
        # The limit is combined stdout/stderr, so neither stream alone exceeds it.
        block = b"L" * 65536
        for _ in range(40):
            os.write(1, block)
            os.write(2, block)
        return
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    child = subprocess.Popen([sys.executable, "-B", "-c",
        "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)"])
    (args.stage / "worker-pids.json").write_text(json.dumps({
        "parent": os.getpid(), "descendant": child.pid, "process_group": os.getpgrp(),
        "parent_ignores_sigterm": True, "child_requests_ignore_sigterm": True}) + "\n")
    time.sleep(60)
    (args.stage / "late-worker-result.txt").write_text("This must not be written.\n")


if __name__ == "__main__":
    main()
