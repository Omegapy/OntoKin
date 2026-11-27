"""W4 audit 001, a00: a no-follow listing of directory trees with SHA-256 of regular files.

Usage: a00_listing.py OUTPUT.json ROOT [ROOT ...]
Every entry: relative path, kind (file, directory, link, other), size, mode, nlink, mtime_ns,
and for a regular file its SHA-256; for a link its target. Links are never followed.
The output file is created exclusively and must not exist. Starts nothing.
"""
import hashlib
import json
import os
import stat
import sys


def file_sha256(path):
    digest = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
    finally:
        os.close(fd)
    return digest.hexdigest()


def entry(path, rel):
    st = os.lstat(path)
    record = {
        "path": rel,
        "mode": oct(stat.S_IMODE(st.st_mode)),
        "size": st.st_size,
        "nlink": st.st_nlink,
        "mtime_ns": st.st_mtime_ns,
        "uid": st.st_uid,
    }
    if stat.S_ISLNK(st.st_mode):
        record["kind"] = "link"
        record["target"] = os.readlink(path)
    elif stat.S_ISDIR(st.st_mode):
        record["kind"] = "directory"
    elif stat.S_ISREG(st.st_mode):
        record["kind"] = "file"
        record["sha256"] = file_sha256(path)
    else:
        record["kind"] = "other"
    return record


def walk(root):
    records = [entry(root, ".")]
    if records[0]["kind"] != "directory":
        return records
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            names = sorted(os.listdir(current))
        except OSError as error:
            records.append({"path": os.path.relpath(current, root), "error": repr(error)})
            continue
        for name in names:
            path = os.path.join(current, name)
            rel = os.path.relpath(path, root)
            record = entry(path, rel)
            records.append(record)
            if record["kind"] == "directory":
                stack.append(path)
    records.sort(key=lambda item: item["path"])
    return records


def main():
    output = sys.argv[1]
    roots = sys.argv[2:]
    result = {"schema": "w4-audit-001.listing/1", "roots": {}}
    for root in roots:
        if not os.path.lexists(root):
            result["roots"][root] = {"exists": False}
            continue
        result["roots"][root] = {"exists": True, "entries": walk(root)}
    data = json.dumps(result, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    for root, info in result["roots"].items():
        if not info["exists"]:
            print(root, "ABSENT")
            continue
        kinds = {}
        for item in info["entries"]:
            kinds[item.get("kind", "error")] = kinds.get(item.get("kind", "error"), 0) + 1
        print(root, kinds)


main()
