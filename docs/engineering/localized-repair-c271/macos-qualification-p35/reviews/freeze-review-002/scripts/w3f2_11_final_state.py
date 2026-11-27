"""Freeze review 002, script 11: the state after the review's work, and the digests of every file reviewed.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_11_final_state.py OUTPUT.json
Reads only; starts no process; writes OUTPUT.json only.
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
OUT = P35 + "/workers/W3-freeze-002"
E = P35 + "/evidence"
WT = "<worktree>"
TOOL = WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35"
REVIEWED = [
    F2 + "/FREEZE-002.json", F2 + "/FREEZE-002-DIFFERENCES.json", F2 + "/FREEZE-AUTHOR-NOTES-002.md", F2 + "/SHA256SUMS.txt",
    F2 + "/s7/p00-freeze-001-rebound.sha256sums.txt", F2 + "/author/scripts/w2f2_selfcheck.py",
    F2 + "/author/records/selfcheck-002-001.txt",
    F1 + "/FREEZE-001.json", F1 + "/SHA256SUMS.txt", F1 + "/s7/w2f_s7_check.py", F1 + "/s7/prepare-s7-001.sh",
    F1 + "/config/cohort-config-001.json", F1 + "/env/declared.environment.json", F1 + "/env/runner.environment.json",
    R1 + "/FREEZE-REVIEW-001.md", R1 + "/FREEZE-REVIEW-001.json", R1 + "/MC11-REVIEWED-LIST-001.json",
    P35 + "/director/reviews/FREEZE-REVIEW-DISPOSITION-001.json", P35 + "/director/run/run_once_v2.sh",
    TOOL + "/MH-PLAN.md", TOOL + "/tooling/FAILURE-CAPTURE.md", TOOL + "/tooling/README.md", TOOL + "/tooling/capture_probe.py",
    TOOL + "/tooling/collect_outcomes.py", TOOL + "/tooling/control_harness.py", TOOL + "/tooling/run_direct_probe.py",
    WT + "/tests/test_static_tray_readback_v01.py", WT + "/tools/check_local.py",
    WT + "/prototypes/static_tray_v01/current_host_readback_v02.py", WT + "/prototypes/static_tray_v01/supervisor_darwin_v01.py",
    WT + "/prototypes/static_tray_v01/supervisor.py", WT + "/prototypes/static_tray_v01/current_host_observation_v02.py",
    WT + "/prototypes/static_tray_v01/format_check.py", E + "/observe-001/HOST.json",
    "/usr/bin/shasum",
    "<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12/lib/python3.12/subprocess.py",
]


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
    return buf.value.decode("ascii") if f(b"kern.bootsessionuuid", buf, ctypes.byref(size), None, 0) == 0 else None


def utc(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def verify(sums, base):
    bad, n, listed = [], 0, set()
    with open(sums, "rb") as s:
        for line in s.read().decode("utf-8").splitlines():
            if line.startswith("#"):
                continue
            digest, name = line.split("  ", 1)
            path = name if name.startswith("/") else base + "/" + name
            listed.add(name)
            n += 1
            if sha256(path) != digest:
                bad.append(name)
    present = set()
    for parent, dirs, files in os.walk(base):
        for f in files:
            present.add(os.path.relpath(os.path.join(parent, f), base))
    return {"lines": n, "failed": bad, "unlisted": sorted(present - listed - {"SHA256SUMS.txt"})}


def newest(root, exclude=()):
    best, where = 0.0, None
    for parent, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if os.path.join(parent, d) not in exclude]
        for n in dirs + names:
            m = os.lstat(os.path.join(parent, n)).st_mtime
            if m > best:
                best, where = m, os.path.join(parent, n)
    return {"utc": utc(best), "path": where}


def main():
    out = {"script": "w3f2_11_final_state.py", "at_utc": utc(time.time()), "boot": boot()}
    out["freeze_002"] = verify(F2 + "/SHA256SUMS.txt", F2)
    out["freeze_002"]["second_list"] = verify(F2 + "/s7/p00-freeze-001-rebound.sha256sums.txt", F2)["failed"]
    out["freeze_002"]["newest"] = newest(F2)
    out["freeze_001"] = verify(F1 + "/SHA256SUMS.txt", F1)
    out["freeze_001"]["newest"] = newest(F1)
    out["review_001_newest"] = newest(R1)
    info = os.lstat(E)
    out["evidence_parent"] = {"inode": info.st_ino, "mtime_utc": utc(info.st_mtime), "entries": len(os.listdir(E)),
                              "s7_paths": [n for n in os.listdir(E) if n.startswith("s7-")], "newest": newest(E)}
    found = []
    for parent, dirs, files in os.walk(WT, followlinks=False):
        dirs[:] = [d for d in dirs if os.path.join(parent, d) != WT + "/.venv"]
        for n in dirs + files:
            if n == "__pycache__" or n.endswith((".pyc", ".pyo")) or n == ".DS_Store":
                found.append(os.path.join(parent, n))
    out["worktree"] = {"bytecode_or_ds_store_outside_venv": found, "newest_outside_venv": newest(WT, (WT + "/.venv",))}
    venv_bytecode = []
    for parent, dirs, files in os.walk(WT + "/.venv", followlinks=False):
        for n in dirs + files:
            p = os.path.join(parent, n)
            if (n == "__pycache__" or n.endswith(".pyc")) and os.lstat(p).st_mtime > 1795767949:  # after 09:25:49Z
                venv_bytecode.append(p)
    out["venv_bytecode_newer_than_review_start"] = venv_bytecode
    out_bytecode = []
    for parent, dirs, files in os.walk(OUT, followlinks=False):
        for n in dirs + files:
            if n == "__pycache__" or n.endswith(".pyc") or n == ".DS_Store":
                out_bytecode.append(os.path.join(parent, n))
    out["out_bytecode_or_ds_store"] = out_bytecode
    out["reviewed_files"] = []
    for p in REVIEWED:
        st = os.lstat(p)
        out["reviewed_files"].append({"path": p, "sha256": sha256(p), "size_bytes": st.st_size,
                                      "mode": "0o%03o" % stat.S_IMODE(st.st_mode)})
    with open(OUT + "/records/02-bindings.json", "rb") as s:
        rows = json.loads(s.read())["rows"]
    out["bound_files_verified"] = [{"id": r["id"], "path": r["path"], "sha256": r["sha256"], "size_bytes": r["size_bytes"],
                                    "mode": r["mode"], "nlink": r["nlink"]} for r in rows]
    with open(sys.argv[1], "x") as s:
        json.dump(out, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps({k: out[k] for k in ("boot", "freeze_002", "freeze_001", "review_001_newest", "evidence_parent",
                                          "worktree", "venv_bytecode_newer_than_review_start", "out_bytecode_or_ds_store")},
                     sort_keys=True))


main()
