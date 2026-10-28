#!/usr/bin/env python3
"""Run one external validation command with closed source/stream receipts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def snapshot(root):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args]).decode().strip()
    state = {"commit": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
             "status": git("status", "--porcelain=v1", "--untracked-files=all")}
    assert state["status"] == "", "Validation source must be a clean committed checkout"
    rows = []
    for name in sorted(filter(None, subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0"))):
        path = root / name
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        rows.append({"path": name, "bytes": len(raw), "sha256": sha(raw),
                     "mode": "100755" if path.stat().st_mode & 0o111 else "100644"})
    return {"git": state, "files": rows, "count": len(rows), "bytes": sum(row["bytes"] for row in rows)}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--timeout", type=float, default=180)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
root, output = args.root.resolve(), args.output.resolve()
command = args.command[1:] if args.command[:1] == ["--"] else args.command
assert command and args.timeout > 0 and not output.is_relative_to(root)
output.mkdir(parents=True, exist_ok=False)
before = snapshot(root)
write(output / "inputs-before.json", before)
record = {"schema": "ontokin.checkpoint038-closed-command/0.1", "command": command,
          "cwd": str(root), "started_at": utc(), "timeout_seconds": args.timeout,
          "source_commit": before["git"]["commit"], "source_tree": before["git"]["tree"],
          "wrapper_sha256": sha(Path(__file__).read_bytes()),
          "environment": {"executable": sys.executable, "python": sys.version, "platform": platform.platform(), "executable_sha256": sha(Path(sys.executable).resolve().read_bytes())}}
record["command_files"] = [{"path": str(Path(x).resolve()), "sha256": sha(Path(x).read_bytes()), "bytes": Path(x).stat().st_size} for x in command if Path(x).is_file()]
write(output / "start.json", record)
started = time.monotonic()
with (output / "stdout.txt").open("xb") as stdout, (output / "stderr.txt").open("xb") as stderr:
    process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr, start_new_session=True)
    record["pid"] = process.pid
    try:
        record["exit_code"] = process.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        record.update(exit_code=process.returncode, timed_out=True)
record.update(finished_at=utc(), elapsed_seconds=time.monotonic() - started)
after = snapshot(root)
write(output / "inputs-after.json", after)
record["inputs_stable"] = before == after
record["streams"] = [{"path": name, "bytes": (output / name).stat().st_size,
                      "sha256": sha((output / name).read_bytes())} for name in ("stdout.txt", "stderr.txt")]
record["command_files_stable"] = all(Path(x["path"]).is_file() and sha(Path(x["path"]).read_bytes()) == x["sha256"] for x in record["command_files"])
record["status"] = "passed" if record["exit_code"] == 0 and record["inputs_stable"] and record["command_files_stable"] else "failed"
write(output / "result.json", record)
print(json.dumps({k:record[k] for k in ("status", "exit_code", "inputs_stable", "elapsed_seconds")}), flush=True)
raise SystemExit(0 if record["status"] == "passed" else 1)
