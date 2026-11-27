"""W2 freeze author: bindings of files and directories, with the on-disk spelling of every component.

Run with <worktree>/.venv/bin/python -I -S -B. Standard library only. It reads; it starts nothing
(an audit hook refuses process creation) and writes only the --output file, which must be absent.

Usage: w2f_bind.py --output OUT PATH [PATH ...]
"""
import hashlib
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse_process(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("w2f_bind starts no process: " + event)


def spelling(path):
    """Each component as the directory lists it (TR-3-03): exact, or the listed spelling."""
    rows = []
    current = "/"
    for part in [p for p in path.split("/") if p]:
        try:
            names = os.listdir(current)
        except OSError as exc:
            rows.append({"component": part, "state": "unlistable", "error": str(exc)})
            return {"exact": False, "components": rows}
        if part in names:
            rows.append({"component": part, "state": "exact"})
        else:
            other = [n for n in names if n.lower() == part.lower()]
            rows.append({"component": part, "state": "differs", "listed": other})
            return {"exact": False, "components": rows}
        current = os.path.join(current, part)
    return {"exact": True, "components": len(rows)}


def binding(path):
    row = {"path": path}
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        row["state"] = "absent"
        parent = os.path.dirname(path)
        row["parent_spelling"] = spelling(parent) if os.path.isdir(parent) else {"exact": False, "parent": "absent"}
        return row
    row["state"] = "present"
    row["realpath_equal"] = os.path.realpath(path) == path and os.path.normpath(path) == path
    row["spelling"] = spelling(path)
    row["mode"] = "0o%03o" % stat.S_IMODE(info.st_mode)
    row["nlink"] = info.st_nlink
    row["mtime_ns"] = info.st_mtime_ns
    row["device"], row["inode"] = info.st_dev, info.st_ino
    if stat.S_ISLNK(info.st_mode):
        row["kind"], row["target"] = "symlink", os.readlink(path)
    elif stat.S_ISDIR(info.st_mode):
        row["kind"] = "directory"
        row["entries"] = sorted(os.listdir(path))[:400]
        row["entry_count"] = len(os.listdir(path))
    elif stat.S_ISREG(info.st_mode):
        row["kind"] = "file"
        digest = hashlib.sha256()
        with open(path, "rb") as stream:
            while True:
                block = stream.read(1 << 20)
                if not block:
                    break
                digest.update(block)
        row["sha256"] = digest.hexdigest()
        row["size_bytes"] = info.st_size
    else:
        row["kind"] = "special"
    return row


def main():
    sys.addaudithook(refuse_process)
    args = sys.argv[1:]
    if len(args) < 3 or args[0] != "--output":
        raise SystemExit("usage: w2f_bind.py --output OUT PATH [PATH ...]")
    output, paths = args[1], args[2:]
    if os.path.lexists(output):
        raise SystemExit("output exists: " + output)
    rows = [binding(path) for path in paths]
    data = (json.dumps({"schema": "w2f-bindings/1", "rows": rows}, indent=1, sort_keys=True) + "\n").encode("ascii")
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    for row in rows:
        short = {k: row.get(k) for k in ("path", "state", "kind", "sha256", "size_bytes", "mode", "nlink")}
        short["spelling_exact"] = (row.get("spelling") or {}).get("exact")
        short["realpath_equal"] = row.get("realpath_equal")
        print(json.dumps(short, sort_keys=True))


main()
