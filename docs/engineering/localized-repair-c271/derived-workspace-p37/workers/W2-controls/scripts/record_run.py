"""Append one test run's record to RUNS.jsonl (W2, C271-P37 S4). Run as python3 -I -S -B; reads the log, writes JSONL.

Arguments: evidence directory, label, module list (space-separated), start UTC, end UTC, exit status.
The command is recorded with labels for the account values and the resolved temporary directory.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

evidence, label, modules, started, ended, status = sys.argv[1:7]
log = Path(evidence) / "runs" / (label + ".log")
text = log.read_text(encoding="utf-8", errors="replace")
ran = re.findall(r"^Ran \d+ tests? in [0-9.]+s$", text, re.M)
verdict = re.findall(r"^(OK.*|FAILED.*)$", text, re.M)
record = {
    "label": label,
    "command": ("/usr/bin/env -i HOME=<home> LOGNAME=<logname> USER=<user> PATH=/usr/bin:/bin TMPDIR=<resolved tmp>/ "
                ".venv/bin/python -B -m unittest " + modules + " -v"),
    "cwd": "<worktree>",
    "started_at_utc": started,
    "ended_at_utc": ended,
    "exit": int(status),
    "result": " ".join(ran[-1:] + verdict[-1:]),
    "log": "runs/" + log.name,
    "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
}
with open(Path(evidence) / "runs" / "RUNS.jsonl", "a", encoding="utf-8") as stream:
    stream.write(json.dumps(record, ensure_ascii=True) + "\n")
print(json.dumps(record, ensure_ascii=True))
