"""W4 audit 001, z03: is any process of this audit still alive?

Usage: z03_process_check.py OUTPUT
Enumerates every process through libproc (proc_listallpids, proc_pidinfo PROC_PIDTBSDINFO, proc_pidpath)
and reads each argv of the same user through sysctl KERN_PROCARGS2. It reports every process, other than
itself, whose argv names this audit's directory or scripts, the bound checker, the numerical audit tool, the
observer, the bound Node, or the bound Git. A name listing is context only (FAILURE-CAPTURE FC-P1): this is
the auditor's own check of its own synchronous starts, not evidence about MH's starts.
Starts nothing (an audit hook refuses process creation); writes OUTPUT by exclusive creation.
"""
import ctypes
import json
import os
import struct
import sys


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)
libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
PROC_PIDTBSDINFO = 3
MARKERS = ("W4-audit-001", "w2f_s7_check.py", "audit_numeric.py", "current_host_observation_v02.py",
           "node-v24.22.1-darwin-arm64/bin/node", "CommandLineTools/usr/bin/git")


class BSDInfo(ctypes.Structure):
    _fields_ = [("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32), ("pbi_xstatus", ctypes.c_uint32),
                ("pbi_pid", ctypes.c_uint32), ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
                ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32), ("pbi_rgid", ctypes.c_uint32),
                ("pbi_svuid", ctypes.c_uint32), ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
                ("pbi_comm", ctypes.c_char * 16), ("pbi_name", ctypes.c_char * 32), ("pbi_nfiles", ctypes.c_uint32),
                ("pbi_pgid", ctypes.c_uint32), ("pbi_pjobc", ctypes.c_uint32), ("e_tdev", ctypes.c_uint32),
                ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32), ("pbi_start_tvsec", ctypes.c_uint64),
                ("pbi_start_tvusec", ctypes.c_uint64)]


def argv_of(pid):
    mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2
    size = ctypes.c_size_t(1 << 20)
    buffer = ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib, 3, buffer, ctypes.byref(size), None, ctypes.c_size_t(0)) != 0:
        return None
    raw = buffer.raw[:size.value]
    argc = struct.unpack_from("<i", raw, 0)[0]
    rest = raw[4:]
    exec_end = rest.index(b"\0")
    position = exec_end
    while position < len(rest) and rest[position] == 0:
        position += 1
    args = []
    for _ in range(argc):
        end = rest.index(b"\0", position)
        args.append(rest[position:end].decode("utf-8", "replace"))
        position = end + 1
    return args


def main():
    output = sys.argv[1]
    count = libc.proc_listallpids(None, 0)
    pids = (ctypes.c_int * (count + 64))()
    count = libc.proc_listallpids(pids, ctypes.sizeof(pids))
    me, uid = os.getpid(), os.getuid()
    infos = {}
    for pid in list(pids)[:count]:
        if pid <= 0:
            continue
        info = BSDInfo()
        if libc.proc_pidinfo(pid, PROC_PIDTBSDINFO, ctypes.c_uint64(0), ctypes.byref(info), ctypes.sizeof(info)) == ctypes.sizeof(info):
            infos[pid] = info
    # The check's own ancestors (the shell-tool call that runs it, and above) are alive by construction.
    ancestors, current = [], me
    while current in infos and infos[current].pbi_ppid not in (0, current):
        current = infos[current].pbi_ppid
        ancestors.append(current)
    rows, matches, ancestor_matches = 0, [], []
    for pid, info in infos.items():
        if pid == me:
            continue
        rows += 1
        if info.pbi_uid != uid:
            continue
        args = argv_of(pid) or []
        text = " ".join(args)
        if any(marker in text for marker in MARKERS):
            row = {"pid": pid, "ppid": info.pbi_ppid, "pgid": info.pbi_pgid, "comm": info.pbi_comm.decode(),
                   "argv_markers": [m for m in MARKERS if m in text]}
            (ancestor_matches if pid in ancestors else matches).append(row)
    report = {"schema": "w4-audit-001.z03-process-check/1", "processes_seen": rows, "self_pid": me,
              "ancestor_pids": ancestors[:4], "ancestors_matching_markers": ancestor_matches,
              "matching_processes": matches, "none_alive": not matches}
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps(report))


main()
