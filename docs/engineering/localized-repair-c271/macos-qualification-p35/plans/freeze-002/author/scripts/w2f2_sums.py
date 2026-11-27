"""W2 freeze author: write SHA256SUMS.txt for every regular file of the freeze 002 directory (stdlib; -I -S -B).

It refuses any process creation, refuses a link or a special file, and creates SHA256SUMS.txt by exclusive creation.
Usage: w2f2_sums.py DIRECTORY
"""
import hashlib
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(PermissionError(event)) if event in PROCESS_EVENTS else None)

top = sys.argv[1]
target = os.path.join(top, "SHA256SUMS.txt")
rows, odd = [], []
for parent, directories, names in os.walk(top, followlinks=False):
    directories.sort()
    for name in sorted(names) + [d for d in directories if os.path.islink(os.path.join(parent, d))]:
        path = os.path.join(parent, name)
        rel = os.path.relpath(path, top)
        info = os.lstat(path)
        if rel == "SHA256SUMS.txt":
            continue
        if not stat.S_ISREG(info.st_mode) or "\n" in rel or "\\" in rel or name == ".DS_Store":
            odd.append(rel)
            continue
        with open(path, "rb") as stream:
            rows.append((rel, hashlib.sha256(stream.read()).hexdigest()))
if odd:
    raise SystemExit("not a plain regular file: " + json.dumps(odd))
rows.sort()
data = "".join(digest + "  " + rel + "\n" for rel, digest in rows).encode("ascii")
fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
try:
    os.write(fd, data)
    os.fsync(fd)
finally:
    os.close(fd)
print(json.dumps({"files": len(rows), "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}))
