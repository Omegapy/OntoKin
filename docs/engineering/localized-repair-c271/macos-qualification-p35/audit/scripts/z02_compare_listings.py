"""W4 audit 001, z02: compare the listing taken at the start of the audit with the one taken at its end.

Usage: z02_compare_listings.py START.json END.json OUTPUT
Every root: entries added, removed or changed (kind, mode, size, nlink, SHA-256, link target, mtime).
Starts nothing (an audit hook refuses process creation).
"""
import json
import os
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)


def main():
    start, end, output = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), sys.argv[3]
    report = {"schema": "w4-audit-001.z02-listing-comparison/1", "roots": {}}
    for root in start["roots"]:
        a = {e["path"]: e for e in start["roots"][root].get("entries", [])}
        b = {e["path"]: e for e in end["roots"][root].get("entries", [])}
        changed = []
        for path in sorted(set(a) & set(b)):
            keys = ("kind", "mode", "size", "nlink", "sha256", "target", "mtime_ns")
            if any(a[path].get(k) != b[path].get(k) for k in keys):
                changed.append({"path": path, "fields": [k for k in keys if a[path].get(k) != b[path].get(k)]})
        report["roots"][root] = {"entries_start": len(a), "entries_end": len(b),
                                 "added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)), "changed": changed}
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    for root, value in report["roots"].items():
        print(root, value["entries_start"], value["entries_end"], "added", value["added"][:10], "removed",
              value["removed"][:10], "changed", value["changed"][:10])


main()
