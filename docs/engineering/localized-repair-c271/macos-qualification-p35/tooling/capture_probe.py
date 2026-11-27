#!/usr/bin/env python3
"""Failure-capture probe for gate MH of C271-P35: FC-P3, FC-P6 and FC-K5 of FAILURE-CAPTURE.md.

Three commands; each writes one absent output file, reads kern.bootsessionuuid before and after,
starts no process (every process creation is refused) and imports nothing of the project.

  probe    FC-P3. For each --pair INTENT STARTED, the process that STARTED records under /process
           (the runner's started-<n>.json, the observer's and the provider's started.json all hold
           the supervisor's record there; INTENT is the record written before that start: the
           runner's or the observer's intent.json, the provider's preflight.json). It probes the
           recorded PID with kill(P, 0) and the recorded group with killpg(G, 0), and records the
           errno names. Only ESRCH establishes absence (FC-P4). For a present PID it reads the
           kernel's own facts: proc_pidinfo PROC_PIDTBSDINFO (the start time, the group, the
           parent, the user and the command name), proc_pidpath (the image), and the members of the
           recorded group (proc_listpgrppids). The recorded process's identity is established only
           when all of these hold (TR-05):
             - its kernel start time lies inside the window from INTENT's modification time to
               STARTED's, both read from the files, compared in microseconds;
             - its image, from proc_pidpath, equals the recorded argv[0];
             - its process group equals the recorded group, which equals the recorded PID.
           Otherwise a present process is "present, identity not established", and its outcome
           stays unknown.

  stop     FC-P6, for one pair. It probes as above. Only when the identity is established does it
           send SIGTERM to the recorded group; it then probes the group every 50 ms. If the group
           stays present, without a break, for 2,000 ms, it establishes the identity again and only
           then sends SIGKILL, and probes for 2,000 ms more. Every send and every probe is recorded.
           When the identity is not established, at the start or before SIGKILL, it sends nothing
           and records "present, identity not established". Ending a process never changes an
           attempt's outcome.

  listing  FC-K5. For each --path, absent, or present with its type, size, mode and SHA-256 (a
           link's target instead, never followed); for each --dir, every entry below it, links
           never followed: relative path, type, size and mode, the SHA-256 of each regular file
           and the target of each link. This process computes every digest of the listing.

The limit of FC-P5 is stated in every probe record: a descendant that moved to another process
group or session is not found by the group probe.

Launch (a start without -B refuses, N-09):

  <worktree>/.venv/bin/python -I -S -B capture_probe.py probe --pair INTENT STARTED ... --output OUT
  <worktree>/.venv/bin/python -I -S -B capture_probe.py stop --pair INTENT STARTED --output OUT
  <worktree>/.venv/bin/python -I -S -B capture_probe.py listing [--dir D ...] [--path P ...] --output OUT
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import errno as errno_module
import hashlib
import json
import os
import signal
import stat
import sys
import time

SCHEMA = "ontokin.c271.p35-capture-probe/1"
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
PROC_PIDTBSDINFO = 3
MAXCOMLEN = 16
GRACE_MS, POLL_MS = 2000, 50
LIMIT_FC_P5 = ("FC-P5: a descendant that moved to another process group or session is not found by the group "
               "probe; the contract claims no enforcement against descendants, and MC11's static scan is its "
               "only evidence.")
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                            "os.system", "os.startfile"))
CTYPES_PROCESS_SYMBOLS = frozenset(("fork", "vfork", "posix_spawn", "posix_spawnp", "execve", "execv", "execvp",
                                    "execvpe", "execl", "execlp", "execle", "system", "popen"))
EXIT_DONE, EXIT_REFUSED, EXIT_UNKNOWN = 0, 2, 3


# ---------------------------------------------------------------------------
# Common helpers (each MH tool carries its own copy; no tool imports another)
# ---------------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class Refusal(Exception):
    """A precondition the tool refuses, with the rule it applies."""

    def __init__(self, rule, reason, **details):
        super().__init__(reason)
        self.rule, self.reason, self.details = rule, reason, details

    def as_dict(self):
        return {"rule": self.rule, "reason": self.reason, "details": self.details}


def require_no_bytecode():
    """N-09: every start of the framework interpreter carries -B."""
    if not sys.flags.dont_write_bytecode:
        raise Refusal("PYTHON", "Run with -B: every start of the qualification interpreter writes no bytecode (N-09)")


def mode_text(st_mode):
    return "0o%03o" % stat.S_IMODE(st_mode)


def canonical_path(value, *, kind=None, rule="PATH"):
    """An absolute path in normal form that is its own realpath, so no component is a symbolic link."""
    if type(value) is not str or not value.startswith("/") or "\0" in value:
        raise Refusal(rule, "Expected an absolute path", path=repr(value))
    if os.path.normpath(value) != value:
        raise Refusal(rule, "The path is not in normal form", path=value)
    if os.path.realpath(value) != value:
        raise Refusal(rule, "The path is not canonical: a component is a symbolic link", path=value)
    if kind is not None:
        try:
            info = os.lstat(value)
        except OSError as exc:
            raise Refusal(rule, "The path is absent or unreadable", path=value, error=str(exc)) from exc
        if kind == "dir" and not stat.S_ISDIR(info.st_mode):
            raise Refusal(rule, "Expected a directory", path=value)
        if kind == "file" and not stat.S_ISREG(info.st_mode):
            raise Refusal(rule, "Expected a regular file", path=value)
    return value


def _identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode


def read_file(path, maximum=None, *, rule="INPUT"):
    """A regular file opened without following a final link: (bytes or None, binding, mtime_ns).

    With maximum None the file is only hashed, streamed; a change during the read refuses.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise Refusal(rule, "Cannot open the file", path=path, error=str(exc)) from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise Refusal(rule, "Not a regular file", path=path)
        if maximum is not None and before.st_size > maximum:
            raise Refusal(rule, "The file exceeds its byte bound", path=path, size_bytes=before.st_size)
        digest, chunks, total = hashlib.sha256(), [], 0
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
            total += len(block)
            if maximum is not None:
                chunks.append(block)
                if total > maximum:
                    raise Refusal(rule, "The file grew beyond its byte bound", path=path)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    named = os.lstat(path)
    if _identity(before) != _identity(after) or _identity(after) != _identity(named) or total != before.st_size:
        raise Refusal(rule, "The file changed while it was read", path=path)
    binding = {"sha256": digest.hexdigest(), "size_bytes": total, "mode": mode_text(before.st_mode)}
    return (b"".join(chunks) if maximum is not None else None), binding, before.st_mtime_ns


def strict_json(raw, *, rule="INPUT", what="document"):
    """JSON with duplicate members and non-finite constants refused."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Refusal(rule, "Duplicate JSON member in the " + what, member=key)
            result[key] = value
        return result

    def constant(text):
        raise Refusal(rule, "Non-finite JSON constant in the " + what, constant=text)
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except Refusal:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise Refusal(rule, "Invalid JSON in the " + what, error=str(exc)) from exc


def json_text(value):
    return (json.dumps(value, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def prepare_output_file(path):
    """An absent output path in an existing canonical directory; an existing path is never replaced."""
    canonical_path(path, rule="OUTPUT")
    canonical_path(os.path.dirname(path), kind="dir", rule="OUTPUT")
    if os.path.lexists(path):
        raise Refusal("OUTPUT", "The output path exists; it is never replaced", path=path)
    return path


def write_new(path, data):
    """Exclusive creation of one absent file, fsynced together with its directory."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0), 0o644)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)
    fsync_directory(os.path.dirname(path))
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def tool_record():
    path = os.path.realpath(__file__)
    with open(path, "rb") as stream:
        data = stream.read()
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "mode": mode_text(os.stat(path).st_mode)}


def invocation_record():
    return {"argv": list(sys.argv), "orig_argv": list(getattr(sys, "orig_argv", [])), "cwd": os.getcwd(),
            "pid": os.getpid(), "process_group": os.getpgrp(),
            "python": {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
                       "build_string": sys.version, "executable": sys.executable,
                       "flags": {name: getattr(sys.flags, name) for name in FLAG_NAMES}}}


class ProcessAudit:
    """An audit hook that refuses and records every process-creation event and ctypes process lookup."""

    def __init__(self):
        self.events, self.enabled = [], True

    def __call__(self, event, args):
        if not self.enabled:
            return
        if event == "ctypes.dlsym":
            name = args[1] if len(args) > 1 else None
            if not (isinstance(name, str) and name in CTYPES_PROCESS_SYMBOLS):
                return
        elif event not in PROCESS_EVENTS:
            return
        self.events.append({"event": event, "utc": utc_now(), "blocked": True})
        raise PermissionError("Process creation is refused while the capture probe runs: " + event)


# ---------------------------------------------------------------------------
# The kernel's facts about a process (libproc and sysctl)
# ---------------------------------------------------------------------------

class ProcBSDInfo(ctypes.Structure):
    """struct proc_bsdinfo of <sys/proc_info.h>, 136 bytes."""
    _fields_ = [("pbi_flags", ctypes.c_uint32), ("pbi_status", ctypes.c_uint32), ("pbi_xstatus", ctypes.c_uint32),
                ("pbi_pid", ctypes.c_uint32), ("pbi_ppid", ctypes.c_uint32), ("pbi_uid", ctypes.c_uint32),
                ("pbi_gid", ctypes.c_uint32), ("pbi_ruid", ctypes.c_uint32), ("pbi_rgid", ctypes.c_uint32),
                ("pbi_svuid", ctypes.c_uint32), ("pbi_svgid", ctypes.c_uint32), ("rfu_1", ctypes.c_uint32),
                ("pbi_comm", ctypes.c_char * MAXCOMLEN), ("pbi_name", ctypes.c_char * (2 * MAXCOMLEN)),
                ("pbi_nfiles", ctypes.c_uint32), ("pbi_pgid", ctypes.c_uint32), ("pbi_pjobc", ctypes.c_uint32),
                ("e_tdev", ctypes.c_uint32), ("e_tpgid", ctypes.c_uint32), ("pbi_nice", ctypes.c_int32),
                ("pbi_start_tvsec", ctypes.c_uint64), ("pbi_start_tvusec", ctypes.c_uint64)]


class Kernel:
    """The four libSystem functions the probe uses, resolved once, before any target is probed."""

    def __init__(self):
        if ctypes.sizeof(ProcBSDInfo) != 136:
            raise Refusal("KERNEL", "struct proc_bsdinfo does not have its 136-byte layout",
                          size=ctypes.sizeof(ProcBSDInfo))
        try:
            library = ctypes.CDLL(LIBSYSTEM, use_errno=True)
            self.pidinfo, self.pidpath = library.proc_pidinfo, library.proc_pidpath
            self.pgrppids, self.sysctl = library.proc_listpgrppids, library.sysctlbyname
        except (OSError, AttributeError) as exc:
            raise Refusal("KERNEL", "libproc or sysctlbyname is unavailable", error=str(exc)) from exc
        self.pidinfo.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int)
        self.pidinfo.restype = ctypes.c_int
        self.pidpath.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32)
        self.pidpath.restype = ctypes.c_int
        self.pgrppids.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_int)
        self.pgrppids.restype = ctypes.c_int
        self.sysctl.argtypes = (ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                                ctypes.c_size_t)
        self.sysctl.restype = ctypes.c_int

    def boot_session_uuid(self):
        buffer = ctypes.create_string_buffer(128)
        size = ctypes.c_size_t(ctypes.sizeof(buffer))
        if self.sysctl(b"kern.bootsessionuuid", buffer, ctypes.byref(size), None, 0) != 0:
            return {"error": errno_name(ctypes.get_errno())}
        return buffer.value.decode("ascii", "replace")

    def bsdinfo(self, pid):
        info = ProcBSDInfo()
        ctypes.set_errno(0)
        size = self.pidinfo(pid, PROC_PIDTBSDINFO, 0, ctypes.byref(info), ctypes.sizeof(info))
        if size != ctypes.sizeof(info):
            return {"error": errno_name(ctypes.get_errno()), "returned": size}
        return {"pid": info.pbi_pid, "ppid": info.pbi_ppid, "pgid": info.pbi_pgid, "uid": info.pbi_uid,
                "status": info.pbi_status, "comm": info.pbi_comm.decode("utf-8", "replace"),
                "start_tvsec": info.pbi_start_tvsec, "start_tvusec": info.pbi_start_tvusec,
                "start_us": info.pbi_start_tvsec * 1000000 + info.pbi_start_tvusec}

    def image(self, pid):
        buffer = ctypes.create_string_buffer(4096)
        ctypes.set_errno(0)
        length = self.pidpath(pid, buffer, ctypes.sizeof(buffer))
        if length <= 0:
            return {"error": errno_name(ctypes.get_errno())}
        return os.fsdecode(buffer.raw[:length])

    def group_members(self, pgid):
        """The PIDs whose process group is pgid; the call answers the number of PIDs it wrote."""
        count = 4096
        buffer = (ctypes.c_int * count)()
        ctypes.set_errno(0)
        returned = self.pgrppids(pgid, buffer, ctypes.sizeof(buffer))
        if returned < 0:
            return {"error": errno_name(ctypes.get_errno())}
        listed = [buffer[index] for index in range(min(count, returned))]
        return sorted(pid for pid in listed if pid > 0)


def errno_name(number):
    if not number:
        return "success"
    return errno_module.errorcode.get(number, "E%d" % number)


def signal_probe(function, ident, number=0):
    """kill(P, sig) or killpg(G, sig): the errno name, or success."""
    try:
        function(ident, number)
    except OSError as exc:
        return errno_name(exc.errno)
    return "success"


# ---------------------------------------------------------------------------
# One recorded start: its records, its probes and its identity
# ---------------------------------------------------------------------------

def read_pair(intent, started):
    """The two records of one start and the recorded identity; a malformed pair is reported, not refused."""
    pair = {"intent": {"path": intent}, "started": {"path": started}}
    try:
        for key, path in (("intent", intent), ("started", started)):
            canonical_path(path, kind="file", rule="RECORD")
        _, intent_binding, intent_mtime = read_file(intent, rule="RECORD")
        raw, started_binding, started_mtime = read_file(started, 16 * 1024 * 1024, rule="RECORD")
        pair["intent"].update(intent_binding, mtime_ns=intent_mtime)
        pair["started"].update(started_binding, mtime_ns=started_mtime)
        document = strict_json(raw, rule="RECORD", what="started record")
        process = document.get("process") if type(document) is dict else None
        pid = process.get("pid") if type(process) is dict else None
        group = process.get("process_group") if type(process) is dict else None
        argv = process.get("argv") if type(process) is dict else None
        if not (type(pid) is int and pid > 1 and group == pid and type(argv) is list and argv
                and all(type(item) is str for item in argv)):
            raise Refusal("RECORD", "The started record holds no supervisor record with pid, process_group equal to "
                          "it, and argv under /process")
        if pid in (os.getpid(), os.getppid()) or pid == os.getpgrp():
            raise Refusal("RECORD", "The recorded process is this probe, its parent or its group")
        pair["recorded"] = {"pid": pid, "process_group": group, "argv0": argv[0]}
    except Refusal as exc:
        pair["refusal"] = exc.as_dict()
    return pair


def probe_target(kernel, pair):
    """FC-P3 for one recorded start; the state and, when present, whether its identity is established."""
    result = {"pair": pair, "limit": LIMIT_FC_P5, "utc": utc_now()}
    if "refusal" in pair:
        result.update(state="unknown", reason="the records cannot name the process: " + pair["refusal"]["reason"])
        return result
    pid, group = pair["recorded"]["pid"], pair["recorded"]["process_group"]
    result.update(kill=signal_probe(os.kill, pid), killpg=signal_probe(os.killpg, group))
    answers = {result["kill"], result["killpg"]}
    if not answers <= {"ESRCH", "EPERM", "success"}:
        result.update(state="unknown", reason="a probe gave an answer other than ESRCH, EPERM or success (FC-P4)")
        return result
    if result["killpg"] == "ESRCH":
        # The recorded process led its own session and group, which it cannot leave: no group, no process.
        result.update(state="absent", reason="ESRCH for the recorded group" + (
            "; the PID itself is held by another process" if result["kill"] != "ESRCH" else ""))
        return result
    result["group_members"] = kernel.group_members(group)
    if result["kill"] == "ESRCH":
        result.update(state="present, identity not established",
                      reason="the recorded group has members, but the recorded process is absent")
        return result
    result.update(bsdinfo=kernel.bsdinfo(pid), image=kernel.image(pid))
    info, image = result["bsdinfo"], result["image"]
    low = pair["intent"]["mtime_ns"] // 1000
    high = -(-pair["started"]["mtime_ns"] // 1000)
    identity = {
        "window_us": [low, high],
        "start_within_window": "error" not in info and low <= info["start_us"] <= high,
        "image_equals_argv0": type(image) is str and image == pair["recorded"]["argv0"],
        "group_equals_recorded": "error" not in info and info["pgid"] == group and info["pid"] == pid}
    identity["established"] = all(identity[key] for key in ("start_within_window", "image_equals_argv0",
                                                             "group_equals_recorded"))
    result["identity"] = identity
    result["state"] = "present, identity established" if identity["established"] else \
        "present, identity not established"
    return result


def stop_target(kernel, pair):
    """FC-P6 for one recorded start: signals only to an established identity, each send and probe recorded."""
    first = probe_target(kernel, pair)
    record = {"probe": first, "sends": [], "probes": [], "state": first["state"]}
    if first["state"] != "present, identity established":
        record["result"] = "no signal sent: " + first["state"]
        return record
    group = pair["recorded"]["process_group"]

    def send(number):
        record["sends"].append({"signal": signal.Signals(number).name, "group": group, "utc": utc_now(),
                                "monotonic": time.monotonic(), "answer": signal_probe(os.killpg, group, number)})

    def watch(phase):
        deadline = time.monotonic() + GRACE_MS / 1000
        while True:
            answer = signal_probe(os.killpg, group)
            record["probes"].append({"phase": phase, "utc": utc_now(), "monotonic": time.monotonic(),
                                     "killpg": answer})
            if answer == "ESRCH":
                return True
            if answer not in ("EPERM", "success") or time.monotonic() >= deadline:
                return False
            time.sleep(POLL_MS / 1000)
    send(signal.SIGTERM)
    if watch("after SIGTERM"):
        record.update(state="absent", result="absent after SIGTERM")
        return record
    if record["probes"][-1]["killpg"] not in ("EPERM", "success"):
        record.update(state="unknown", result="a probe after SIGTERM gave an answer other than ESRCH, EPERM or "
                      "success; nothing more was sent")
        return record
    again = probe_target(kernel, pair)
    record["probe_before_sigkill"] = again
    if again["state"] == "absent":
        record.update(state="absent", result="absent after SIGTERM, at the identity check before SIGKILL")
        return record
    if again["state"] != "present, identity established":
        record.update(state=again["state"], result="SIGKILL not sent: " + again["state"])
        return record
    send(signal.SIGKILL)
    if watch("after SIGKILL"):
        record.update(state="absent", result="absent after SIGKILL")
    else:
        record.update(state="present after SIGKILL", result="the group is still present after SIGKILL")
    return record


# ---------------------------------------------------------------------------
# FC-K5: the readback listing
# ---------------------------------------------------------------------------

def entry_record(path):
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return {"state": "absent"}
    except OSError as exc:
        return {"state": "unreadable", "error": errno_name(exc.errno)}
    row = {"state": "present", "mode": mode_text(info.st_mode), "size_bytes": info.st_size}
    if stat.S_ISLNK(info.st_mode):
        row.update(kind="symlink", target=os.readlink(path))
    elif stat.S_ISDIR(info.st_mode):
        row["kind"] = "directory"
    elif stat.S_ISREG(info.st_mode):
        row["kind"] = "file"
        try:
            row["sha256"] = read_file(path, rule="LISTING")[1]["sha256"]
        except Refusal as exc:
            row["refusal"] = exc.as_dict()
    else:
        row["kind"] = "special"
    return row


def directory_listing(root):
    top = entry_record(root)
    if top.get("kind") != "directory":
        return {"root": top, "entries": None}
    entries = {}
    for parent, directories, names in os.walk(root, followlinks=False):
        for name in sorted(directories + names):
            full = os.path.join(parent, name)
            entries[os.path.relpath(full, root)] = entry_record(full)
    return {"root": top, "entries": entries}


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def main(argv=None):
    parser = _Parser(prog="capture_probe.py", allow_abbrev=False, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    sub = commands.add_parser("probe")
    sub.add_argument("--pair", nargs=2, action="append", required=True, metavar=("INTENT", "STARTED"))
    sub.add_argument("--output", required=True)
    sub = commands.add_parser("stop")
    sub.add_argument("--pair", nargs=2, required=True, metavar=("INTENT", "STARTED"))
    sub.add_argument("--output", required=True)
    sub = commands.add_parser("listing")
    sub.add_argument("--dir", action="append", default=[])
    sub.add_argument("--path", action="append", default=[])
    sub.add_argument("--output", required=True)
    output, started = None, time.monotonic()
    audit = ProcessAudit()
    try:
        args = parser.parse_args(argv)
        output = prepare_output_file(args.output)
        require_no_bytecode()
        kernel = Kernel()
        sys.addaudithook(audit)
        record = {"schema": SCHEMA, "command": args.command, "tool": tool_record(), "invocation": invocation_record(),
                  "started_at_utc": utc_now(), "boot_before": kernel.boot_session_uuid(), "loaded_project_files": []}
        if args.command == "probe":
            record["targets"] = [probe_target(kernel, read_pair(*pair)) for pair in args.pair]
        elif args.command == "stop":
            record["stop"] = stop_target(kernel, read_pair(*args.pair))
        else:
            if not args.dir and not args.path:
                raise Refusal("USAGE", "listing needs at least one --dir or --path")
            for path in args.dir:
                canonical_path(path, rule="LISTING")
            for path in args.path:
                # A planned output may itself be a link, which is listed as one: only its parent must be canonical.
                if type(path) is not str or not path.startswith("/") or os.path.normpath(path) != path:
                    raise Refusal("LISTING", "Expected an absolute path in normal form", path=repr(path))
                canonical_path(os.path.dirname(path), rule="LISTING")
            record.update(paths={path: entry_record(path) for path in args.path},
                          directories={path: directory_listing(path) for path in args.dir},
                          digests_computed_by="this capture_probe.py listing process")
        audit.enabled = False
        record.update(boot_after=kernel.boot_session_uuid(), process_events=audit.events, finished_at_utc=utc_now(),
                      elapsed_s=time.monotonic() - started)
        write_new(output, json_text(record))
        summary = {"command": args.command}
        if args.command == "probe":
            summary["states"] = [target["state"] for target in record["targets"]]
        elif args.command == "stop":
            summary.update(state=record["stop"]["state"], sends=[row["signal"] for row in record["stop"]["sends"]])
        sys.stderr.write("MH-CAPTURE " + json.dumps(summary, sort_keys=True) + "\n")
        return EXIT_DONE
    except Refusal as exc:
        return report_end(output, {"schema": "ontokin.c271.p35-tool-refusal/1", "tool": "capture_probe.py",
                                   "state": "REFUSED", "refusal": exc.as_dict()}, EXIT_REFUSED)
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        return report_end(output, {"schema": "ontokin.c271.p35-tool-failure/1", "tool": "capture_probe.py",
                                   "state": "UNKNOWN", "error": {"type": type(exc).__name__, "reason": str(exc)}},
                          EXIT_UNKNOWN)


def report_end(output, document, code):
    """A refusal or failure goes to stderr, and to the output path while that path is still absent."""
    document.update(finished_at_utc=utc_now(), invocation=invocation_record())
    sys.stderr.write(json.dumps(document, sort_keys=True) + "\n")
    if output is not None and not os.path.lexists(output):
        try:
            write_new(output, json_text(document))
        except OSError:
            pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
