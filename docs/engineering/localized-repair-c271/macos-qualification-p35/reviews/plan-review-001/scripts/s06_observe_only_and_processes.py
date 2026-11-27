"""W3 plan review 001, script s06: the observe-only loaded-module check, and the absence of my processes.

1. observe_host checks the loaded modules again after it imports the Darwin supervisor; static
   never makes that check. This script imports the supervisor as load_darwin_supervisor does
   (the bound root on sys.path for the import only), then applies the observer's rule with its
   own code: every loaded module file is a file of the frozen Python inventory's framework tree
   (with any existing bytecode also inventoried) or a source-inventory file without bytecode.
   The import runs only module-level definitions (both package files are docstrings) and starts
   nothing (audit hook); -B writes no bytecode, and the script checks that no __pycache__ appeared.
2. bin/node: a standalone C string v24.22.1 (static read only).
3. Every process on the host is listed through libproc; the PIDs of my earlier starts are probed
   with kill(pid, 0) and, if present, identified by start time and image (FAILURE-CAPTURE FC-P1:
   never by name alone).

Usage:
  python -I -S -B s06_observe_only_and_processes.py --worktree WT --python-inventory P --source-inventory S
      --node NODE --earlier-pids PID,... --output OUT.json
"""
import argparse
import ctypes
import errno
import json
import os
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
SUPERVISOR = "prototypes.static_tray_v01.supervisor_darwin_v01"
SUPERVISOR_FILES = {"prototypes": "prototypes/__init__.py",
                    "prototypes.static_tray_v01": "prototypes/static_tray_v01/__init__.py",
                    "prototypes.static_tray_v01.supervisor": "prototypes/static_tray_v01/supervisor.py",
                    SUPERVISOR: "prototypes/static_tray_v01/supervisor_darwin_v01.py"}


class BSD(ctypes.Structure):
    _fields_ = [("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32), ("pbi_xstatus", ctypes.c_uint32),
                ("pbi_pid", ctypes.c_uint32), ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
                ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32), ("pbi_rgid", ctypes.c_uint32),
                ("pbi_svuid", ctypes.c_uint32), ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
                ("pbi_comm", ctypes.c_char * 16), ("pbi_name", ctypes.c_char * 32), ("pbi_nfiles", ctypes.c_uint32),
                ("pbi_pgid", ctypes.c_uint32), ("pbi_pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
                ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32), ("pbi_start_tvsec", ctypes.c_uint64),
                ("pbi_start_tvusec", ctypes.c_uint64)]


def lib():
    handle = ctypes.CDLL(LIBSYSTEM, use_errno=True)
    handle.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
    handle.proc_listallpids.restype = ctypes.c_int
    handle.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    handle.proc_pidinfo.restype = ctypes.c_int
    handle.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    handle.proc_pidpath.restype = ctypes.c_int
    return handle


def proc(handle, pid):
    info = BSD()
    n = handle.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info))
    buf = ctypes.create_string_buffer(4096)
    r = handle.proc_pidpath(pid, buf, 4096)
    if n <= 0:
        return None
    return {"pid": pid, "ppid": info.pbi_ppid, "pgid": info.pbi_pgid, "comm": info.pbi_comm.decode("utf-8", "replace"),
            "image": buf.value.decode("utf-8", "replace") if r > 0 else None,
            "start": info.pbi_start_tvsec + info.pbi_start_tvusec / 1e6}


def all_processes(handle):
    count = handle.proc_listallpids(None, 0)
    buf = (ctypes.c_int * (count + 256))()
    count = handle.proc_listallpids(buf, ctypes.sizeof(buf))
    rows = []
    for pid in list(buf)[:count]:
        if pid > 0:
            row = proc(handle, pid)
            if row:
                rows.append(row)
    return rows


def probe(pid):
    try:
        os.kill(pid, 0)
        return "present"
    except ProcessLookupError:
        return "ESRCH"
    except PermissionError:
        return "EPERM"


def label(path, worktree, framework):
    if path and path.startswith(framework + "/"):
        return "<framework>/" + path[len(framework) + 1:]
    if path and path.startswith(worktree + "/"):
        return "<worktree>/" + path[len(worktree) + 1:]
    return "<other>/" + os.path.basename(path or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--python-inventory", required=True)
    ap.add_argument("--source-inventory", required=True)
    ap.add_argument("--node", required=True)
    ap.add_argument("--earlier-pids", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    t0 = time.time()
    wt = a.worktree
    out = {"script": os.path.basename(__file__), "argv": sys.argv, "pid": os.getpid(), "ppid": os.getppid()}
    with open(a.python_inventory, "rb") as f:
        inventory = json.loads(f.read())
    with open(a.source_inventory, "rb") as f:
        source = json.loads(f.read())
    framework = inventory["framework"]["root"]
    fw_entries = inventory["framework"]["entries"]
    caches_before = {d: os.path.lexists(wt + "/" + d + "/__pycache__") for d in ("prototypes",
                                                                                   "prototypes/static_tray_v01")}
    before_import = set(sys.modules)

    # 1. The import as load_darwin_supervisor makes it, then the loaded-module rule.
    import importlib
    sys.path.insert(0, wt)
    try:
        module = importlib.import_module(SUPERVISOR)
    finally:
        sys.path.remove(wt)
    rows, problems = [], []
    for name, mod in sorted(tuple(sys.modules.items())):
        path = getattr(mod, "__file__", None)
        if type(path) is not str or name == "__main__":
            continue
        cached = getattr(mod, "__cached__", None)
        real = os.path.realpath(path)
        row = {"name": name, "file": label(real, wt, framework), "new_with_import": name not in before_import}
        if real.startswith(framework + "/"):
            rel = real[len(framework) + 1:]
            row["tree"] = "framework"
            row["inventoried"] = fw_entries.get(rel, {}).get("kind") == "file"
            if type(cached) is str and os.path.lexists(cached):
                crel = os.path.realpath(cached)[len(framework) + 1:]
                row["bytecode_inventoried"] = fw_entries.get(crel, {}).get("kind") == "file"
                if not row["bytecode_inventoried"]:
                    problems.append(row)
            if not row["inventoried"]:
                problems.append(row)
        elif real.startswith(wt + "/"):
            rel = real[len(wt) + 1:]
            row["tree"] = "source"
            row["in_source_inventory"] = rel in source["files"]
            row["bytecode_exists"] = type(cached) is str and os.path.lexists(cached)
            if not row["in_source_inventory"] or row["bytecode_exists"]:
                problems.append(row)
        else:
            row["tree"] = "outside"
            problems.append(row)
        rows.append(row)
    code_file = os.path.realpath(module.run_process.__code__.co_filename)
    out["supervisor_import"] = {
        "modules_with_files": len(rows), "new_with_import": sorted(r["name"] for r in rows if r["new_with_import"]),
        "problems": problems, "rule_holds": not problems,
        "run_process_from_bound_file": code_file == wt + "/" + SUPERVISOR_FILES[SUPERVISOR],
        "clock_and_stop": callable(getattr(module, "Clock", None)) and isinstance(getattr(module, "Stop", None), type),
        "supervisor_files_in_source_inventory": all(rel in source["files"] for rel in SUPERVISOR_FILES.values()),
        "pycache_before": caches_before,
        "pycache_after": {d: os.path.lexists(wt + "/" + d + "/__pycache__") for d in caches_before}}

    # 2. Node's standalone version text.
    with open(a.node, "rb") as f:
        data = f.read()
    at = data.find(b"\0v24.22.1\0")
    out["node_version_c_string"] = {"found": at >= 0, "offset": at + 1 if at >= 0 else None}
    del data

    # 3. Processes.
    handle = lib()
    me = proc(handle, os.getpid())
    shell = proc(handle, os.getppid())
    harness = proc(handle, shell["ppid"]) if shell else None
    every = all_processes(handle)
    children = [r for r in every if harness and r["ppid"] == harness["pid"]]
    out["processes"] = {
        "me": {"pid": me["pid"], "comm": me["comm"], "image": label(me["image"], wt, framework)},
        "my_shell": {"pid": shell["pid"], "comm": shell["comm"], "image": shell["image"]},
        "harness": {"pid": harness["pid"], "comm": harness["comm"]} if harness else None,
        "harness_children": [{"pid": r["pid"], "comm": r["comm"],
                              "image": r["image"] if (r["image"] or "").startswith(("/bin/", "/usr/")) else
                              "<other>/" + os.path.basename(r["image"] or "")} for r in children],
        "framework_python_processes": [{"pid": r["pid"], "ppid": r["ppid"]} for r in every
                                       if (r["image"] or "").startswith(framework + "/")],
        "node_processes": [{"pid": r["pid"], "ppid": r["ppid"]} for r in every
                           if r["image"] == a.node or r["comm"] == "node"],
        "git_processes": [{"pid": r["pid"], "ppid": r["ppid"], "image": r["image"]} for r in every
                          if (r["image"] or "").endswith("/git") or r["comm"] == "git"],
        "listed": len(every)}
    earlier = []
    for pid in (int(p) for p in a.earlier_pids.split(",") if p):
        state = probe(pid)
        row = {"pid": pid, "kill0": state}
        if state != "ESRCH":
            now = proc(handle, pid)
            row["now"] = {"comm": now["comm"], "ppid": now["ppid"],
                          "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now["start"]))} if now else None
        earlier.append(row)
    out["earlier_pids"] = earlier
    out["process_events"] = EVENTS
    out["elapsed_s"] = round(time.time() - t0, 3)
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({"rule_holds": out["supervisor_import"]["rule_holds"],
                      "run_process_from_bound_file": out["supervisor_import"]["run_process_from_bound_file"],
                      "pycache_after": out["supervisor_import"]["pycache_after"],
                      "node_version_c_string": out["node_version_c_string"],
                      "harness_children": out["processes"]["harness_children"],
                      "framework_python_processes": out["processes"]["framework_python_processes"],
                      "node_processes": out["processes"]["node_processes"],
                      "git_processes": out["processes"]["git_processes"],
                      "earlier_pids": earlier, "process_events": EVENTS}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
