"""HOST review 001, script 07: the final recheck, and the digest of every file reviewed.

It rehashes HOST and every file of the attempt and of the evidence parent against the descriptors
the run's own records give, reads the boot again, reads the cryptex's dyld shared cache header
and /usr/lib/dyld against N34-M's values (HOST records neither: N-03), probes my own recorded
PIDs with signal 0, and lists the SHA-256, size and mode of every reviewed file (labelled).
Usage: python3 -I -S -B w3h_07_final.py --plan P --outputs DIR --out OUT --files PATH ... [--label ...]
"""
import argparse
import ctypes
import glob
import os
import stat
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()

CACHE = "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e"


def boot_uuid():
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    fn = libc.sysctlbyname
    fn.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                   ctypes.c_size_t]
    size = ctypes.c_size_t(64)
    buf = ctypes.create_string_buffer(64)
    if fn(b"kern.bootsessionuuid", buf, ctypes.byref(size), None, 0) != 0:
        return None
    return buf.raw[:size.value].rstrip(b"\0").decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    for name in ("--plan", "--outputs", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--files", nargs="+", default=[])
    ap.add_argument("--label", action="append", default=[])
    args = ap.parse_args()
    lab = C.Labeler([tuple(item.split("=", 1)) for item in args.label])
    ck = C.Checks()
    started = time.time()
    plan = C.strict_loads(C.read_bytes(args.plan)[0])
    outs, parent = plan["evidence"]["outputs"], plan["evidence"]["parent"]
    host_path = outs["host"]
    _, hf, _ = C.read_bytes(host_path, keep=False)
    ck.add("F01", C.binding(hf) == {"sha256": "858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666",
                                    "size_bytes": 18420, "mode": "0o600"} and hf["nlink"] == 1,
           "HOST is unchanged at the end of the review", sha256=hf["sha256"])
    # every attempt file against the descriptors the run's records give
    result = C.strict_loads(C.read_bytes(outs["result"])[0])
    completion = C.strict_loads(C.read_bytes(outs["completion"])[0])
    host = C.strict_loads(C.read_bytes(host_path)[0])
    want = {}
    for desc in [result["host"], result["reserved"], result["preflight"], completion["result"],
                 host["inspections"]["git_version"], host["inspections"]["node_version"]] + result["attempts"]:
        want[desc["path"]] = C.binding(desc)
    for cid in ("git_version", "node_version"):
        post = C.strict_loads(C.read_bytes(outs[cid]["postflight"])[0])
        want[post["start"]["path"]] = C.binding(post["start"])
        for desc in post["artifacts"].values():
            want[desc["path"]] = C.binding(desc)
    stdout_desc = C.strict_loads(C.read_bytes(parent + "/observe-001.observe.stdout.txt")[0])["completion"]
    want[stdout_desc["path"]] = C.binding(stdout_desc)
    bad = [lab.text(p) for p, b in want.items() if C.binding(C.read_bytes(p, keep=False)[1]) != b]
    listing = sorted(os.path.relpath(os.path.join(d, n), plan["evidence"]["attempt"])
                     for d, ds, fs in os.walk(plan["evidence"]["attempt"]) for n in ds + fs)
    ck.add("F02", not bad and len(want) == 17 and len(listing) == 21,
           "17 attempt files equal the descriptors that result.json, completion.json, HOST, the postflights and "
           "observe's stdout give them; the attempt still holds 2 subdirectories and 19 files",
           described=len(want), entries=len(listing), differing=bad)
    rows = {}
    for name in ("observe-001.static", "observe-001.observe"):
        rec = C.strict_loads(C.read_bytes(parent + "/" + name + ".command.json")[0])
        for key in ("stdout", "stderr"):
            f = C.read_bytes(rec["streams"][key]["path"], keep=False)[1]
            rows[name + "." + key] = f["sha256"] == rec["streams"][key]["sha256"]
    ck.add("F03", all(rows.values()) and len(os.listdir(parent)) == 9,
           "the capture streams still equal their command records, and the evidence parent still holds 9 entries",
           rows=rows)
    ck.add("F04", boot_uuid() == plan["platform"]["boot_session_uuid"], "the boot is still the plan's")
    raw, cache, _ = C.read_bytes(CACHE)
    uuid = raw[0x58:0x68].hex().upper()
    uuid = "-".join((uuid[:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:]))
    _, dyld, _ = C.read_bytes("/usr/lib/dyld", keep=False)
    ck.add("F05", cache["sha256"] == "7a024959c8c14d46e2964f975f2256b3f9efc2da950a31067d26ac7ac16498d4"
           and cache["size_bytes"] == 573440 and raw[:15] == b"dyld_v1  arm64e" and uuid ==
           "F2E86C53-6052-388B-BA71-5A0C9B569413" and dyld["sha256"] ==
           "373fce2b3689c2113d5341a6bba735e9f970401ba64896c0a6379680192f1cdf",
           "N-03: the cryptex's main shared-cache file and /usr/lib/dyld are N34-M's (HOST records neither)",
           cache_uuid=uuid)
    mine = {}
    for path in sorted(glob.glob(os.path.join(args.outputs, "*.json"))):
        try:
            value = C.strict_loads(C.read_bytes(path)[0])
        except Exception:
            continue
        pid = value.get("process", {}).get("pid") if isinstance(value, dict) else None
        if isinstance(pid, int):
            try:
                os.kill(pid, 0)
                state = "present"
            except ProcessLookupError:
                state = "ESRCH"
            except PermissionError:
                state = "EPERM"
            mine[os.path.basename(path)] = {"pid": pid, "now": state}
    ck.add("F06", all(v["now"] == "ESRCH" for v in mine.values()) and len(mine) >= 10,
           "none of my own recorded script processes remains", processes=mine)
    files = []
    for path in args.files:
        info = os.lstat(path)
        if stat.S_ISREG(info.st_mode):
            facts = C.read_bytes(path, keep=False)[1]
            files.append({"path": lab.text(path), **C.binding(facts)})
        else:
            files.append({"path": lab.text(path), "kind": "not a regular file"})
    out = {"script": "w3h_07_final.py", "process": C.process_identity(), "started_epoch": started,
           "ended_epoch": time.time(), "checks": ck.rows, "summary": ck.summary(), "reviewed_files": files,
           "audit_events": C.EVENTS}
    print(C.write_new(args.out, lab.deep(out)), ck.summary(), len(files))


if __name__ == "__main__":
    main()
