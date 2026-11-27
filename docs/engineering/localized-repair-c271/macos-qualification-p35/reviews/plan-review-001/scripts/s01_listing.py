"""W3 plan review 001, script s01: static listing, hashing and pretty-printing.

Standard library only. Starts nothing. Follows no link. Writes only the absent
output paths given on the command line (exclusive creation).

Usage (every path is an argument; no machine path is written here):
  python -I -S -B s01_listing.py --output OUT.json [--list DIR ...] [--top DIR ...]
         [--absent PATH ...] [--sums SUMS BASEDIR] [--pretty-dir DIR --pretty FILE ...]
"""

import argparse
import ctypes
import hashlib
import json
import os
import stat
import sys
import time


def sha256_nofollow(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError("not a regular file: %s" % path)
        h = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                break
            h.update(chunk)
            total += len(chunk)
        st2 = os.fstat(fd)
        if (st.st_size, st.st_mtime_ns, st.st_ino) != (st2.st_size, st2.st_mtime_ns, st2.st_ino):
            raise OSError("changed while read: %s" % path)
        if total != st.st_size:
            raise OSError("size mismatch: %s" % path)
        return h.hexdigest(), st
    finally:
        os.close(fd)


def entry(path, rel):
    st = os.lstat(path)
    mode = stat.S_IMODE(st.st_mode)
    rec = {"path": rel, "mode": "0o%03o" % mode, "dev": st.st_dev, "ino": st.st_ino,
           "nlink": st.st_nlink, "mtime_ns": st.st_mtime_ns}
    if stat.S_ISLNK(st.st_mode):
        rec["kind"] = "symlink"
        rec["target"] = os.readlink(path)
    elif stat.S_ISDIR(st.st_mode):
        rec["kind"] = "directory"
    elif stat.S_ISREG(st.st_mode):
        rec["kind"] = "file"
        digest, st2 = sha256_nofollow(path)
        rec["sha256"] = digest
        rec["size_bytes"] = st2.st_size
    else:
        rec["kind"] = "special"
    return rec


def walk(root):
    out = [entry(root, ".")]
    stack = [root]
    while stack:
        d = stack.pop()
        names = sorted(os.listdir(d))
        for n in names:
            p = os.path.join(d, n)
            rel = os.path.relpath(p, root)
            rec = entry(p, rel)
            out.append(rec)
            if rec["kind"] == "directory":
                stack.append(p)
    out.sort(key=lambda r: r["path"])
    return out


def top(d):
    rec = entry(d, ".")
    rec["children"] = sorted(os.listdir(d)) if rec["kind"] == "directory" else None
    return rec


def proc_chain():
    lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    lib.proc_pidpath.restype = ctypes.c_int
    lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    lib.proc_pidinfo.restype = ctypes.c_int

    class BSD(ctypes.Structure):
        _fields_ = [("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32),
                    ("pbi_xstatus", ctypes.c_uint32), ("pbi_pid", ctypes.c_uint32),
                    ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
                    ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32),
                    ("pbi_rgid", ctypes.c_uint32), ("pbi_svuid", ctypes.c_uint32),
                    ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
                    ("pbi_comm", ctypes.c_char * 16), ("pbi_name", ctypes.c_char * 32),
                    ("pbi_nfiles", ctypes.c_uint32), ("pbi_pgid", ctypes.c_uint32),
                    ("pbi_pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
                    ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32),
                    ("pbi_start_tvsec", ctypes.c_uint64), ("pbi_start_tvusec", ctypes.c_uint64)]

    chain = []
    pid = os.getpid()
    for _ in range(5):
        info = BSD()
        n = lib.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
        buf = ctypes.create_string_buffer(4096)
        r = lib.proc_pidpath(pid, buf, 4096)
        image = buf.value.decode("utf-8", "replace") if r > 0 else None
        # keep system images only; other images are reduced to their basename
        if image and not (image.startswith("/bin/") or image.startswith("/usr/") or image.startswith("/System/")):
            image = "<non-system>/" + os.path.basename(image)
        chain.append({"pid": pid, "ppid": info.pbi_ppid if n > 0 else None,
                      "comm": info.pbi_comm.decode("utf-8", "replace") if n > 0 else None,
                      "image": image})
        if n <= 0 or info.pbi_ppid in (0, 1):
            break
        pid = info.pbi_ppid
    return chain


def excl_write(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--list", action="append", default=[])
    ap.add_argument("--top", action="append", default=[])
    ap.add_argument("--absent", action="append", default=[])
    ap.add_argument("--sums", nargs=2, action="append", default=[])
    ap.add_argument("--pretty-dir")
    ap.add_argument("--pretty", action="append", default=[])
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    if a.pretty_dir:
        os.makedirs(a.pretty_dir, exist_ok=True)
    t0 = time.time()
    res = {"script": os.path.basename(__file__), "argv": sys.argv, "orig_argv": sys.orig_argv,
           "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                     "dont_write_bytecode": sys.flags.dont_write_bytecode},
           "executable": sys.executable, "version": sys.version,
           "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
           "process_chain": proc_chain()}
    res["listings"] = {d: walk(d) for d in a.list}
    res["tops"] = {d: top(d) for d in a.top}
    absent = {}
    for p in a.absent:
        try:
            os.lstat(p)
            absent[p] = "PRESENT"
        except FileNotFoundError:
            absent[p] = "absent (ENOENT)"
    res["absent_checks"] = absent
    sums = []
    for sums_file, base in a.sums:
        with open(sums_file, "rb") as f:
            lines = f.read().decode("ascii").splitlines()
        for line in lines:
            if not line.strip():
                continue
            digest, name = line.split(" ", 1)
            if name[:1] in (" ", "*"):
                name = name[1:]
            p = os.path.join(base, name)
            try:
                actual, st = sha256_nofollow(p)
                sums.append({"file": name, "listed": digest, "actual": actual, "equal": digest == actual,
                             "size_bytes": st.st_size, "mode": "0o%03o" % stat.S_IMODE(st.st_mode)})
            except OSError as e:
                sums.append({"file": name, "listed": digest, "error": str(e)})
    res["sums"] = sums
    pretty = []
    for p in a.pretty:
        with open(p, "rb") as f:
            raw = f.read()
        doc = json.loads(raw)
        canon = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        outp = os.path.join(a.pretty_dir, os.path.basename(p) + ".pretty.json")
        excl_write(outp, json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=True).encode("ascii") + b"\n")
        pretty.append({"file": p, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw),
                       "is_canonical": raw == canon, "canonical_plus_newline": raw == canon + b"\n",
                       "pretty": outp})
    res["pretty"] = pretty
    res["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    res["elapsed_s"] = round(time.time() - t0, 3)
    excl_write(a.output, json.dumps(res, indent=1, sort_keys=True).encode("utf-8") + b"\n")
    bad = [s for s in sums if not s.get("equal")]
    print(json.dumps({"output": a.output, "sums": len(sums), "sums_bad": len(bad),
                      "absent": absent, "pretty": [p["pretty"] for p in pretty],
                      "chain": res["process_chain"]}, indent=1))


if __name__ == "__main__":
    main()
