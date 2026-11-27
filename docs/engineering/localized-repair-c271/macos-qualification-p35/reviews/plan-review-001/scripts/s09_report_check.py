"""W3 plan review 001, script s09: check the written review record, then the last process check.

Parses PLAN-REVIEW-001.json (duplicate members refuse), checks that its plan digest, the
Markdown's and the plan file's own SHA-256 agree, that the verdict and the findings are as
stated, and scans both reports and my scripts for machine paths, the user's name and the given
forbidden strings. The home directory and the account name are derived at run time, never
written here. Records the SHA-256 of both reports, of s08's output and of this script.
Starts nothing (audit hook); writes only its absent output.

Usage:
  python -I -S -B s09_report_check.py --out-dir OUT --plan PLAN --forbid TEXT ... --earlier-pids P,... --output OUT.json
"""
import argparse
import ctypes
import hashlib
import json
import os
import pwd
import struct
import sys

REFUSED = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty")
EVENTS = []


def _hook(event, args):
    if event in REFUSED:
        EVENTS.append(event)
        raise RuntimeError("process creation refused: " + event)


sys.addaudithook(_hook)
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"


def read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        chunks = []
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            chunks.append(block)
        return b"".join(chunks)
    finally:
        os.close(fd)


def strict(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("duplicate member " + k)
            out[k] = v
        return out
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--forbid", action="append", default=[])
    ap.add_argument("--earlier-pids", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    out_dir = a.out_dir
    md_raw = read(out_dir + "/PLAN-REVIEW-001.md")
    js_raw = read(out_dir + "/PLAN-REVIEW-001.json")
    plan_sha = hashlib.sha256(read(a.plan)).hexdigest()
    result = {"script": os.path.basename(__file__), "pid": os.getpid(), "ppid": os.getppid(),
              "script_sha256": hashlib.sha256(read(os.path.realpath(__file__))).hexdigest()}
    try:
        doc = strict(js_raw)
        result["json_parses"] = True
    except ValueError as exc:
        doc = None
        result["json_parses"] = False
        result["json_error"] = str(exc)
    if doc is not None:
        result["json_checks"] = {
            "plan_sha256_equals_file": doc.get("plan_sha256") == plan_sha,
            "subject_plan_sha256_equals_file": doc.get("subject", {}).get("plan", {}).get("sha256") == plan_sha,
            "verdict": doc.get("verdict"),
            "mandatory_findings_empty": doc.get("mandatory_findings") == [],
            "finding_ids": [f.get("id") for f in doc.get("findings", [])],
            "all_nonmandatory": all(f.get("severity") == "nonmandatory" for f in doc.get("findings", [])),
            "files_reviewed": len(doc.get("files_reviewed", {})),
            "starts": {k: doc.get("conduct", {}).get("starts", {}).get(k) for k in ("shells", "python")}}
    md = md_raw.decode("utf-8")
    result["markdown_checks"] = {"plan_sha256_present": plan_sha in md,
                                 "verdict_present": "**ACCEPT_WITH_NONMANDATORY_FINDINGS.**" in md,
                                 "trailing_spaces_lines": sum(1 for line in md.splitlines() if line.endswith(" ")),
                                 "tab_characters": md.count("\t")}
    home = os.path.realpath(os.path.expanduser("~"))
    account = pwd.getpwuid(os.getuid())
    forbidden = sorted({home, account.pw_name, account.pw_dir} | set(a.forbid))
    hits = {}
    targets = {"PLAN-REVIEW-001.md": md_raw, "PLAN-REVIEW-001.json": js_raw}
    for name in sorted(os.listdir(out_dir + "/scripts")):
        if name.endswith(".py"):
            targets["scripts/" + name] = read(out_dir + "/scripts/" + name)
    for label, raw in targets.items():
        text = raw.decode("utf-8", "replace")
        found = {}
        for index, term in enumerate(forbidden):
            if term and term.lower() in text.lower():
                lines = [n + 1 for n, line in enumerate(text.splitlines()) if term.lower() in line.lower()]
                found["term-%d" % index] = lines[:20]
        hits[label] = found
    result["forbidden_terms_count"] = len(forbidden)
    result["forbidden_hits"] = hits
    result["clean"] = not any(hits.values())
    result["digests"] = {"PLAN-REVIEW-001.md": hashlib.sha256(md_raw).hexdigest(),
                         "PLAN-REVIEW-001.json": hashlib.sha256(js_raw).hexdigest(),
                         "outputs/s08-final-recheck.json":
                             hashlib.sha256(read(out_dir + "/outputs/s08-final-recheck.json")).hexdigest()}
    lib = ctypes.CDLL(LIBSYSTEM, use_errno=True)
    lib.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.proc_listallpids.restype = ctypes.c_int
    lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    lib.proc_pidinfo.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(136)

    def ppid_of(pid):
        return struct.unpack_from("<I", buf.raw, 16)[0] if lib.proc_pidinfo(pid, 3, 0, buf, 136) > 0 else None
    shell = os.getppid()
    harness = ppid_of(shell)
    count = lib.proc_listallpids(None, 0)
    pids = (ctypes.c_int * (count + 256))()
    count = lib.proc_listallpids(pids, ctypes.sizeof(pids))
    children = [p for p in list(pids)[:count] if p > 0 and ppid_of(p) == harness]
    earlier = {}
    for pid in (int(p) for p in a.earlier_pids.split(",") if p):
        try:
            os.kill(pid, 0)
            earlier[str(pid)] = "present"
        except ProcessLookupError:
            earlier[str(pid)] = "ESRCH"
        except PermissionError:
            earlier[str(pid)] = "EPERM"
    result["processes"] = {"harness_pid": harness, "harness_children": children,
                           "only_my_shell": children == [shell], "earlier": earlier,
                           "earlier_all_absent": all(v == "ESRCH" for v in earlier.values())}
    result["process_events"] = EVENTS
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(result, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({k: result.get(k) for k in ("json_parses", "json_error", "json_checks", "markdown_checks", "clean",
                                                 "forbidden_hits", "digests", "processes", "script_sha256",
                                                 "process_events", "pid", "ppid")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
