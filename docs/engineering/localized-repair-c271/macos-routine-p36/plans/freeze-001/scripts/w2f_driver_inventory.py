"""W2 (freeze 001): the driver's own source inventory of the worktree, and its difference from main's baseline run.

Usage: <worktree>/.venv/bin/python -I -S -B w2f_driver_inventory.py WORKTREE MAIN_SOURCE_BEFORE OUTPUT

It loads tools/check_local.py of commit B from WORKTREE and calls its inventory() on WORKTREE: the value that R1's
and R2's summaries record as source_inventory (inventory_sha256, file_count), when nothing changes. It then
lists, by top-level directory, the paths whose identity differs from main's source-before.json (the resolved-
directory baseline run of 8e847c15), and the paths on one side only. An audit hook refuses every process
creation and every open() for writing other than OUTPUT. It writes only OUTPUT (absent).
"""
import sys

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
import json
import os
from collections import Counter
from pathlib import Path

worktree, main_before, output = sys.argv[1:4]
if os.path.lexists(output):
    raise SystemExit("refused: output exists")
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
events = []


def hook(event, args):
    if event in {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}:
        events.append(event)
        raise PermissionError(event)
    if event == "open" and len(args) >= 3 and not isinstance(args[0], int):
        flags, mode = args[2], args[1]
        if ((isinstance(flags, int) and flags & WRITE_FLAGS) or (isinstance(mode, str) and any(c in mode for c in "wax+"))) \
                and os.fspath(args[0]) != output:
            events.append("open-for-write " + str(args[0]))
            raise PermissionError("writes nothing but its output")


sys.addaudithook(hook)
sys.path.insert(0, worktree)
from tools import check_local  # noqa: E402

current = check_local.inventory(Path(worktree))
main = json.load(open(main_before, encoding="utf-8"))
a = {row["path"]: (row["sha256"], row["bytes"]) for row in main["files"]}
b = {row["path"]: (row["sha256"], row["bytes"]) for row in current["files"]}
changed = sorted(p for p in a.keys() & b.keys() if a[p] != b[p])
only_main = sorted(a.keys() - b.keys())
only_b = sorted(b.keys() - a.keys())
top = lambda paths: dict(sorted(Counter(p.split("/")[0] if "/" in p else "<root file>" for p in paths).items()))
document = {"schema": "ontokin.c271.p36-w2-freeze-driver-inventory/1",
            "worktree_inventory": {"inventory_sha256": current["sha256"], "file_count": current["file_count"]},
            "main_8e847c15_inventory": {"inventory_sha256": main["sha256"], "file_count": main["file_count"]},
            "changed": {"count": len(changed), "by_top": top(changed), "paths": changed},
            "only_in_main": {"count": len(only_main), "by_top": top(only_main), "paths": only_main},
            "only_in_b": {"count": len(only_b), "by_top": top(only_b), "paths": only_b},
            "audit_events": events}
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    stream.write(json.dumps(document, indent=1, sort_keys=True) + "\n")
print(json.dumps({key: (value if not isinstance(value, dict) or "paths" not in value else
                        {"count": value["count"], "by_top": value["by_top"]}) for key, value in document.items()}, indent=1))
