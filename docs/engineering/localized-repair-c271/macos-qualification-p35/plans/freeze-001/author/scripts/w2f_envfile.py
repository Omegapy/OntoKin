"""W2 freeze author: write one frozen environment document (ontokin.c271.p35-unit-environment/1).

Run with <worktree>/.venv/bin/python -I -S -B. Usage: w2f_envfile.py OUTPUT NAME=VALUE [NAME=VALUE ...]
Canonical JSON (sorted keys, compact separators, ASCII, no final newline), created exclusively; HOME refused.
"""
import hashlib
import json
import os
import sys

output, pairs = sys.argv[1], sys.argv[2:]
environment = {}
for pair in pairs:
    name, sep, value = pair.partition("=")
    if not sep or not name or name in environment or name == "HOME":
        raise SystemExit("bad pair: " + pair)
    environment[name] = value
document = {"schema": "ontokin.c271.p35-unit-environment/1", "environment": environment}
data = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
try:
    os.write(fd, data)
    os.fsync(fd)
finally:
    os.close(fd)
print(json.dumps({"path": output, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
                  "names": sorted(environment)}, sort_keys=True))
