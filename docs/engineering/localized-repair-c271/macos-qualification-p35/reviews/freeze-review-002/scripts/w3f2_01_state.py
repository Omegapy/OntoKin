"""Freeze review 002, script 01: the state before the review's checks.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_01_state.py OUTPUT.json
Reads only. Starts no process (an audit hook refuses every process creation). Writes OUTPUT.json only.
"""
import ctypes
import hashlib
import json
import os
import stat
import sys
import time

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

LOCAL = "<local>"
P35 = LOCAL + "/c271-p35"
F1 = P35 + "/workers/W2-freeze-001"
F2 = P35 + "/workers/W2-freeze-002"
R1 = P35 + "/workers/W3-freeze-001"
E = P35 + "/evidence"
WT = "<worktree>"
DISP = P35 + "/director/reviews/FREEZE-REVIEW-DISPOSITION-001.json"
WRAPPER = P35 + "/director/run/run_once_v2.sh"


def sha256(path):
    h = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        while True:
            b = os.read(fd, 1 << 20)
            if not b:
                break
            h.update(b)
    finally:
        os.close(fd)
    return h.hexdigest()


def boot():
    f = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True).sysctlbyname
    f.argtypes = (ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t)
    f.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(128)
    size = ctypes.c_size_t(128)
    if f(b"kern.bootsessionuuid", buf, ctypes.byref(size), None, 0) != 0:
        return None
    return buf.value.decode("ascii")


def utc(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def parse_sums(path, base):
    rows, malformed = [], []
    with open(path, "rb") as s:
        for n, raw in enumerate(s.read().decode("utf-8").splitlines(), 1):
            if raw.startswith("#"):
                continue
            parts = raw.split("  ", 1)
            if len(parts) != 2 or len(parts[0]) != 64 or any(c not in "0123456789abcdef" for c in parts[0]):
                malformed.append([n, raw])
                continue
            name = parts[1]
            full = name if name.startswith("/") else os.path.join(base, name)
            rows.append({"line": n, "digest": parts[0], "name": name, "path": full})
    return rows, malformed


def verify_sums(path, base):
    rows, malformed = parse_sums(path, base)
    bad = []
    for r in rows:
        try:
            got = sha256(r["path"])
        except OSError as exc:
            got = "unreadable: " + str(exc)
        r["ok"] = got == r["digest"]
        if not r["ok"]:
            bad.append({"name": r["name"], "got": got, "want": r["digest"]})
    return rows, malformed, bad


def all_files(root):
    out = []
    for parent, dirs, names in os.walk(root, followlinks=False):
        for n in names:
            out.append(os.path.relpath(os.path.join(parent, n), root))
        for d in dirs:
            if os.path.islink(os.path.join(parent, d)):
                out.append(os.path.relpath(os.path.join(parent, d), root))
    return sorted(out)


def newest(root, exclude=()):
    best, where, count = 0.0, None, 0
    for parent, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if os.path.join(parent, d) not in exclude]
        for n in dirs + names:
            p = os.path.join(parent, n)
            try:
                m = os.lstat(p).st_mtime
            except OSError:
                continue
            count += 1
            if m > best:
                best, where = m, p
    return {"newest_mtime_utc": utc(best), "newest_path": where, "entries": count}


def main():
    out = {"script": "w3f2_01_state.py", "started_utc": utc(time.time()), "boot": boot()}
    # Freeze 002: its SHA256SUMS.txt, every line verified, none unlisted.
    rows, malformed, bad = verify_sums(F2 + "/SHA256SUMS.txt", F2)
    listed = sorted(r["name"] for r in rows)
    present = [p for p in all_files(F2) if p != "SHA256SUMS.txt"]
    out["freeze_002"] = {
        "sums_sha256": sha256(F2 + "/SHA256SUMS.txt"), "lines": len(rows), "malformed": malformed,
        "failed": bad, "unlisted": sorted(set(present) - set(listed)), "listed_missing": sorted(set(listed) - set(present)),
        "FREEZE-002.json": {"sha256": sha256(F2 + "/FREEZE-002.json"), "size_bytes": os.lstat(F2 + "/FREEZE-002.json").st_size},
        "differences_sha256": sha256(F2 + "/FREEZE-002-DIFFERENCES.json"),
        "notes_sha256": sha256(F2 + "/FREEZE-AUTHOR-NOTES-002.md"),
        "second_list_sha256": sha256(F2 + "/s7/p00-freeze-001-rebound.sha256sums.txt"),
        "newest": newest(F2)}
    # Freeze 001: its 85 files, and nothing newer than its SHA256SUMS.txt.
    rows1, malformed1, bad1 = verify_sums(F1 + "/SHA256SUMS.txt", F1)
    present1 = [p for p in all_files(F1) if p != "SHA256SUMS.txt"]
    sums_mtime = os.lstat(F1 + "/SHA256SUMS.txt").st_mtime
    newer = []
    for parent, dirs, names in os.walk(F1, followlinks=False):
        for n in dirs + names:
            p = os.path.join(parent, n)
            if os.lstat(p).st_mtime > sums_mtime:
                newer.append(p)
    out["freeze_001"] = {
        "sums_sha256": sha256(F1 + "/SHA256SUMS.txt"), "lines": len(rows1), "malformed": malformed1, "failed": bad1,
        "unlisted": sorted(set(present1) - set(r["name"] for r in rows1)),
        "FREEZE-001.json": {"sha256": sha256(F1 + "/FREEZE-001.json"), "size_bytes": os.lstat(F1 + "/FREEZE-001.json").st_size},
        "sums_mtime_utc": utc(sums_mtime), "newer_than_sums": newer, "newest": newest(F1)}
    # Review 001's records and the disposition.
    out["review_001"] = {name: {"sha256": sha256(R1 + "/" + name), "size_bytes": os.lstat(R1 + "/" + name).st_size,
                                "mode": "0o%03o" % stat.S_IMODE(os.lstat(R1 + "/" + name).st_mode),
                                "nlink": os.lstat(R1 + "/" + name).st_nlink}
                         for name in ("FREEZE-REVIEW-001.md", "FREEZE-REVIEW-001.json", "MC11-REVIEWED-LIST-001.json")}
    out["review_001"]["newest"] = newest(R1)
    out["disposition"] = {"sha256": sha256(DISP), "size_bytes": os.lstat(DISP).st_size}
    out["wrapper"] = {"sha256": sha256(WRAPPER), "size_bytes": os.lstat(WRAPPER).st_size,
                      "mode": "0o%03o" % stat.S_IMODE(os.lstat(WRAPPER).st_mode)}
    # The evidence parent.
    info = os.lstat(E)
    names = sorted(os.listdir(E))
    out["evidence_parent"] = {"inode": info.st_ino, "device": info.st_dev, "mode": "0o%03o" % stat.S_IMODE(info.st_mode),
                              "mtime_utc": utc(info.st_mtime), "entries": len(names),
                              "s7_paths": [n for n in names if n.startswith("s7-")], "newest": newest(E)}
    # The worktree: no bytecode, __pycache__ or .DS_Store outside .venv; its newest entry.
    found = []
    for parent, dirs, files in os.walk(WT, followlinks=False):
        dirs[:] = [d for d in dirs if os.path.join(parent, d) != WT + "/.venv"]
        for n in dirs + files:
            if n == "__pycache__" or n.endswith((".pyc", ".pyo")) or n == ".DS_Store":
                found.append(os.path.join(parent, n))
    out["worktree"] = {"bytecode_or_ds_store": found, "newest_outside_venv": newest(WT, exclude=(WT + "/.venv",))}
    out["finished_utc"] = utc(time.time())
    with open(sys.argv[1], "x") as s:
        json.dump(out, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps({"F2_lines": len(rows), "F2_failed": len(bad), "F2_unlisted": out["freeze_002"]["unlisted"],
                      "F1_lines": len(rows1), "F1_failed": len(bad1), "F1_newer": len(newer), "boot": out["boot"],
                      "freeze_sha256": out["freeze_002"]["FREEZE-002.json"]}, sort_keys=True))


main()
