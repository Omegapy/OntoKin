"""W3 plan review 001, script s07: identify processes that share the bound images, statically.

For every process whose image lies in the bound Python framework, or whose command name or
image names node or git: its image (labelled), start time, parent and process group, through
libproc. For a framework-interpreter process not started by this review, its argument vector
through sysctl KERN_PROCARGS2 (same user), with paths labelled, and the NAMES of its environment
variables only (values are never recorded), plus whether PYTHONDONTWRITEBYTECODE is set.
Starts nothing (audit hook); writes only its absent output.

Usage:
  python -I -S -B s07_foreign_processes.py --framework F --node NODE --git GIT --home-label-prefix H --output OUT.json
"""
import argparse
import ctypes
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


class BSD(ctypes.Structure):
    _fields_ = [("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32), ("pbi_xstatus", ctypes.c_uint32),
                ("pbi_pid", ctypes.c_uint32), ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
                ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32), ("pbi_rgid", ctypes.c_uint32),
                ("pbi_svuid", ctypes.c_uint32), ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
                ("pbi_comm", ctypes.c_char * 16), ("pbi_name", ctypes.c_char * 32), ("pbi_nfiles", ctypes.c_uint32),
                ("pbi_pgid", ctypes.c_uint32), ("pbi_pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
                ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32), ("pbi_start_tvsec", ctypes.c_uint64),
                ("pbi_start_tvusec", ctypes.c_uint64)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--framework", required=True)
    ap.add_argument("--node", required=True)
    ap.add_argument("--git", required=True)
    ap.add_argument("--home-label-prefix", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    lib = ctypes.CDLL(LIBSYSTEM, use_errno=True)
    lib.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.proc_listallpids.restype = ctypes.c_int
    lib.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    lib.proc_pidinfo.restype = ctypes.c_int
    lib.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    lib.proc_pidpath.restype = ctypes.c_int
    lib.sysctl.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_uint, ctypes.c_void_p,
                           ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
    lib.sysctl.restype = ctypes.c_int
    home = a.home_label_prefix

    def labelled(text):
        if text is None:
            return None
        for prefix, name in ((a.framework, "<framework>"), (home, "<home>")):
            text = text.replace(prefix, name)
        return text

    count = lib.proc_listallpids(None, 0)
    buf = (ctypes.c_int * (count + 256))()
    count = lib.proc_listallpids(buf, ctypes.sizeof(buf))
    rows = []
    for pid in list(buf)[:count]:
        if pid <= 0 or pid == os.getpid():
            continue
        info = BSD()
        if lib.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info)) <= 0:
            continue
        path = ctypes.create_string_buffer(4096)
        image = path.value.decode("utf-8", "replace") if lib.proc_pidpath(pid, path, 4096) > 0 else None
        comm = info.pbi_comm.decode("utf-8", "replace")
        interesting = (image or "").startswith(a.framework + "/") or comm in ("node", "git") or image in (a.node, a.git)
        if not interesting:
            continue
        row = {"pid": pid, "ppid": info.pbi_ppid, "pgid": info.pbi_pgid, "uid_is_mine": info.pbi_uid == os.getuid(),
               "comm": comm, "image_is_prepared_node": image == a.node, "image_is_bound_git": image == a.git,
               "image_in_framework": (image or "").startswith(a.framework + "/"),
               "image": labelled(image) if (image or "").startswith((a.framework, "/usr/", "/bin/", "/System/",
                                                                     "/Library/")) else "<other>/" + os.path.basename(image or ""),
               "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(info.pbi_start_tvsec))}
        if row["image_in_framework"]:
            mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2
            size = ctypes.c_size_t(0)
            if lib.sysctl(mib, 3, None, ctypes.byref(size), None, 0) == 0 and size.value:
                raw = ctypes.create_string_buffer(size.value)
                if lib.sysctl(mib, 3, raw, ctypes.byref(size), None, 0) == 0:
                    data = raw.raw[:size.value]
                    argc = struct.unpack_from("<i", data, 0)[0]
                    pos = 4
                    end = data.index(b"\0", pos)
                    exec_path = data[pos:end].decode("utf-8", "replace")
                    pos = end
                    while pos < len(data) and data[pos] == 0:
                        pos += 1
                    strings = data[pos:].split(b"\0")
                    argv = [s.decode("utf-8", "replace") for s in strings[:argc]]
                    env = [s.decode("utf-8", "replace") for s in strings[argc:] if s]
                    names = sorted({e.split("=", 1)[0] for e in env if "=" in e})
                    row["exec_path"] = labelled(exec_path)
                    row["argv"] = [labelled(x) for x in argv]
                    row["environment_names"] = names
                    row["PYTHONDONTWRITEBYTECODE"] = next((e.split("=", 1)[1] for e in env
                                                           if e.startswith("PYTHONDONTWRITEBYTECODE=")), None)
                    row["dash_B_in_argv"] = "-B" in argv[1:] or any(x.startswith("-") and not x.startswith("--")
                                                                     and "B" in x[1:] for x in argv[1:3])
            else:
                row["procargs"] = "unreadable (errno %d)" % ctypes.get_errno()
        rows.append(row)
    out = {"script": os.path.basename(__file__), "pid": os.getpid(), "ppid": os.getppid(), "rows": rows,
           "prepared_node_running": any(r["image_is_prepared_node"] for r in rows),
           "bound_git_running": any(r["image_is_bound_git"] for r in rows),
           "foreign_framework_processes": [r for r in rows if r["image_in_framework"]],
           "process_events": EVENTS}
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({"prepared_node_running": out["prepared_node_running"],
                      "bound_git_running": out["bound_git_running"],
                      "node_images": sorted({r["image"] for r in rows if r["comm"] == "node"}),
                      "foreign_framework_processes": out["foreign_framework_processes"],
                      "process_events": EVENTS}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
