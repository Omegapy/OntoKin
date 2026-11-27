"""W3 plan review 001, script s08: final recheck before the review record is written.

Rechecks, at the end of the review: the plan's bytes and digest; this boot; the empty evidence
parent and the absent attempt and capture paths; W2's SHA256SUMS.txt and the absence of any
other file in W2's directory; MP's prepared files; the source inventory and the Python inventory,
recomputed by the functions of my scripts s04 and s03 (loaded by path; under -B no bytecode is
written); HEAD; capture_probe.py against the tooling's digest list. Then the SHA-256 of my own
scripts and earlier outputs, and the final process check. Starts nothing (audit hook).

Usage:
  python -I -S -B s08_final_recheck.py --worktree WT --local LOCAL --out-dir OUT --earlier-pids P,... --output OUT.json
"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import struct
import sys
import time

REFUSED = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty")
EVENTS = []


def _hook(event, args):
    if event in REFUSED:
        EVENTS.append(event)
        raise RuntimeError("process creation refused: " + event)


sys.addaudithook(_hook)
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
PLAN_SHA256 = "b8cd6449aba958373f68715158402ed2e0e233e08213f3521bbc3d80cfe4c152"
BOOT = "C90010BA-4DA9-475D-BBAB-CF1A9C40175A"
PYTHON_INVENTORY = "c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633"
SOURCE_INVENTORY = "95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c"
COMMIT = "0eb9a5517f4e19705178a2c59b8d8d33fb87867a"
MP = {"c271-p34/plans/node-install-plan.json": "1fee042d5e3c809a89d4975df40f69d7a27e88abf9ba58d8cf91ca16795c5ff1",
      "c271-p34/plans/reader-install-plan.json": "ff5a95da6d349e0bd6ea1d2c79fc02757de48ac9cbb89dc59737b67c6d7a71c8",
      "c271-p34/receipts/node-install-result.json": "65caf77a967898ef2d63a3f0595f6f754fde1e7fad9a61f938a084b6717d4729",
      "c271-p34/receipts/reader-install-result.json": "03222a857c7a5a186f1bb30c205d10360882962a7a181d6b3659da47a0ac3fb2",
      "c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz":
          "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7",
      "c271-macos/node-v24.22.1-darwin-arm64/bin/node": "6f32069480ec14d52b6d7b1f3c7124cfbbc46203abf5ddf5c65b127435f3f329",
      "c271-macos/node-v24.22.1-darwin-arm64/NODE-SOURCE.json":
          "e928a8ec87a6fcd8f21d7bef3e080392e0bdaad3acbf2e767997dae5ead9ea2c"}
MP_MODES = {"c271-p34/plans/node-install-plan.json": "0o644", "c271-p34/plans/reader-install-plan.json": "0o644",
            "c271-p34/receipts/node-install-result.json": "0o600",
            "c271-p34/receipts/reader-install-result.json": "0o600",
            "c271-p34/downloads/node/node-v24.22.1-darwin-arm64.tar.gz": "0o444",
            "c271-macos/node-v24.22.1-darwin-arm64/bin/node": "0o755",
            "c271-macos/node-v24.22.1-darwin-arm64/NODE-SOURCE.json": "0o644"}


def sha(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        h = hashlib.sha256()
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            h.update(block)
        info = os.fstat(fd)
        return h.hexdigest(), info.st_size, "0o%03o" % (info.st_mode & 0o7777)
    finally:
        os.close(fd)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def boot():
    lib = ctypes.CDLL(LIBSYSTEM, use_errno=True)
    f = lib.sysctlbyname
    f.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
    f.restype = ctypes.c_int
    size = ctypes.c_size_t(64)
    buf = ctypes.create_string_buffer(64)
    assert f(b"kern.bootsessionuuid", buf, ctypes.byref(size), None, 0) == 0
    return buf.raw[:size.value].split(b"\0", 1)[0].decode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--local", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--earlier-pids", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    t0 = time.time()
    wt, local = a.worktree, a.local
    w2 = local + "/c271-p35/workers/W2-plan-001"
    parent = local + "/c271-p35/evidence"
    checks = {}
    checks["plan_digest"] = sha(w2 + "/observation-plan-001.json")[0] == PLAN_SHA256
    checks["boot"] = boot() == BOOT
    checks["evidence_parent_empty"] = os.listdir(parent) == []
    checks["attempt_and_capture_paths_absent"] = not any(os.path.lexists(parent + "/" + n) for n in (
        "observe-001", "observe-001.observe.stdout.txt", "observe-001.observe.stderr.txt",
        "observe-001.observe.exit.txt"))
    listed = {}
    with open(w2 + "/SHA256SUMS.txt", "rb") as f:
        for line in f.read().decode("ascii").splitlines():
            if line.strip():
                digest, name = line.split("  ", 1)
                listed[name] = digest
    present = []
    for root, dirs, files in os.walk(w2):
        for n in files:
            present.append(os.path.relpath(os.path.join(root, n), w2))
    checks["w2_sums_valid"] = all(sha(w2 + "/" + n)[0] == d for n, d in listed.items())
    checks["w2_no_other_file"] = sorted(present) == sorted(list(listed) + ["SHA256SUMS.txt"])
    checks["w2_sums_entries"] = len(listed)
    checks["mp_unchanged_with_modes"] = all(sha(local + "/" + r)[0] == d and sha(local + "/" + r)[2] == MP_MODES[r]
                                            for r, d in MP.items())
    s03 = load(a.out_dir + "/scripts/s03_python_inventory.py", "w3_s03")
    s04 = load(a.out_dir + "/scripts/s04_source_and_git.py", "w3_s04")
    venv = wt + "/.venv"
    framework = "/".join(os.path.realpath(venv + "/bin/python").split("/")[:-2])
    images, problems = {}, []
    fw = s03.walk(framework, "framework", images, problems)
    ve = s03.walk(venv, "venv", images, problems)
    sel, sel_checks = s03.selection(venv, framework, fw, ve)
    clo, passes = s03.closure(images, framework, venv, {"framework": fw, "venv": ve}, sel["process_image"])
    doc = {"schema": s03.SCHEMA, "framework": {"root": framework, "entries": fw}, "venv": {"root": venv, "entries": ve},
           "selection": sel, "closure": clo}
    checks["python_inventory_digest"] = hashlib.sha256(s03.canonical(doc)).hexdigest()
    checks["python_inventory_equals_frozen"] = checks["python_inventory_digest"] == PYTHON_INVENTORY
    checks["python_rule_problems"] = len(s03.RULE_PROBLEMS) + len(problems)
    src, links, src_problems = s04.source_inventory(wt)
    checks["source_inventory_digest"] = hashlib.sha256(s04.canonical(src)).hexdigest()
    checks["source_inventory_equals_frozen"] = checks["source_inventory_digest"] == SOURCE_INVENTORY
    checks["source_problems"] = len(src_problems) + sum(1 for n in links.values() if n != 1)
    gitdir = open(wt + "/.git").read().strip()[len("gitdir: "):]
    head = open(gitdir + "/HEAD").read().strip()
    common = os.path.realpath(gitdir + "/" + open(gitdir + "/commondir").read().strip())
    checks["head_is_C"] = open(common + "/" + head[5:]).read().strip() == COMMIT
    tooling = wt + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling"
    sums = {}
    with open(wt + "/docs/engineering/localized-repair-c271/macos-qualification-p35/authoring/TOOLING-SHA256SUMS.txt") as f:
        for line in f:
            if line.strip():
                d, n = line.rstrip("\n").split("  ", 1)
                sums[n] = d
    checks["capture_probe_equals_tooling_sums"] = sha(tooling + "/capture_probe.py")[0] == sums.get("capture_probe.py")
    checks["failure_capture_equals_tooling_sums"] = sha(tooling + "/FAILURE-CAPTURE.md")[0] == sums.get(
        "FAILURE-CAPTURE.md")
    mine = {}
    for sub in ("scripts", "outputs", "outputs/pretty"):
        directory = a.out_dir + "/" + sub
        for n in sorted(os.listdir(directory)):
            p = directory + "/" + n
            if os.path.isfile(p) and not os.path.islink(p):
                d, size, mode = sha(p)
                mine[sub + "/" + n] = {"sha256": d, "size_bytes": size, "mode": mode}
    lib = ctypes.CDLL(LIBSYSTEM, use_errno=True)
    lib.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.proc_listallpids.restype = ctypes.c_int
    lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    lib.proc_pidinfo.restype = ctypes.c_int
    lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    lib.proc_pidpath.restype = ctypes.c_int
    raw = ctypes.create_string_buffer(136)

    def ppid_of(pid):
        if lib.proc_pidinfo(pid, 3, 0, raw, 136) <= 0:
            return None
        return struct.unpack_from("<I", raw.raw, 16)[0]
    shell = os.getppid()
    harness = ppid_of(shell)
    count = lib.proc_listallpids(None, 0)
    pids = (ctypes.c_int * (count + 256))()
    count = lib.proc_listallpids(pids, ctypes.sizeof(pids))
    children, bound_images = [], []
    node = local + "/c271-macos/node-v24.22.1-darwin-arm64/bin/node"
    for pid in list(pids)[:count]:
        if pid <= 0:
            continue
        if ppid_of(pid) == harness:
            children.append(pid)
        path = ctypes.create_string_buffer(4096)
        if lib.proc_pidpath(pid, path, 4096) > 0 and path.value.decode("utf-8", "replace") in (
                node, "/Library/Developer/CommandLineTools/usr/bin/git"):
            bound_images.append(pid)
    earlier = {}
    for pid in (int(p) for p in a.earlier_pids.split(",") if p):
        try:
            os.kill(pid, 0)
            earlier[pid] = "present"
        except ProcessLookupError:
            earlier[pid] = "ESRCH"
        except PermissionError:
            earlier[pid] = "EPERM"
    out = {"script": os.path.basename(__file__), "pid": os.getpid(), "ppid": shell, "harness_pid": harness,
           "checks": checks, "selection_checks": sel_checks, "closure_passes": passes,
           "harness_children": children, "harness_children_are_only_my_shell": children == [shell],
           "bound_images_running": bound_images, "earlier_pids": earlier,
           "earlier_all_absent": all(v == "ESRCH" for v in earlier.values()),
           "my_files": mine, "process_events": EVENTS, "elapsed_s": round(time.time() - t0, 3),
           "finished_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({k: out[k] for k in ("checks", "harness_children_are_only_my_shell", "bound_images_running",
                                          "earlier_all_absent", "process_events", "elapsed_s", "pid", "ppid")},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
