"""W3 plan review 001: helpers shared by my scripts (standard library only, no project import).

Each script imports this file from its own directory, which it puts on sys.path for that one
import only (under -B no bytecode is written). Nothing here holds a machine path; every path comes
from the command line. Outputs replace the real places
with labels given as --label NAME=PATH arguments.
"""
import hashlib
import json
import os
import re
import stat
import sys

PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork",
                            "os.forkpty", "os.spawn", "os.startfile"))
PROCESS_SYMBOLS = frozenset(("fork", "vfork", "execve", "execv", "execvp", "execvpe", "execl", "execlp",
                             "execle", "posix_spawn", "posix_spawnp", "system", "popen"))
REFUSED_EVENTS = []


def _audit(event, args):
    if event in PROCESS_EVENTS:
        REFUSED_EVENTS.append(event)
        raise RuntimeError("W3 refuses process creation: " + event)
    if event == "ctypes.dlsym":
        name = args[1] if len(args) > 1 else None
        if isinstance(name, str) and name in PROCESS_SYMBOLS:
            REFUSED_EVENTS.append(event + ":" + name)
            raise RuntimeError("W3 refuses a ctypes process symbol: " + name)


def start():
    """Refuse to run without -I -S -B, then install the process-creation audit hook."""
    flags = sys.flags
    if not (flags.isolated and flags.no_site and flags.dont_write_bytecode and flags.ignore_environment):
        raise SystemExit("W3 scripts run only as python3 -I -S -B")
    sys.addaudithook(_audit)


def mode_text(info):
    return "0o%03o" % stat.S_IMODE(info.st_mode)


def identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns)


def read_bytes(path, keep=True, prefix=0):
    """One descriptor, no final link followed; refuses a change of identity during the read.

    Returns (data or None, binding {sha256, size_bytes, mode}, head bytes, lstat result).
    """
    named = os.lstat(path)
    if stat.S_ISLNK(named.st_mode):
        raise ValueError("is a symbolic link: " + path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("not a regular file: " + path)
        digest, chunks, head, total = hashlib.sha256(), [], b"", 0
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
            total += len(block)
            if keep:
                chunks.append(block)
            if len(head) < prefix:
                head += block[:prefix - len(head)]
        after = os.fstat(fd)
    finally:
        os.close(fd)
    again = os.lstat(path)
    if not (identity(before) == identity(after) == identity(again)) or total != before.st_size:
        raise ValueError("changed while read: " + path)
    binding = {"sha256": digest.hexdigest(), "size_bytes": total, "mode": mode_text(before)}
    return (b"".join(chunks) if keep else None), binding, head, before


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def strict_loads(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON member: " + key)
            result[key] = value
        return result

    def constant(text):
        raise ValueError("non-finite JSON constant: " + text)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


class Labels:
    """Replace each real place by its label in output text, longest place first, at a path boundary."""

    def __init__(self, pairs):
        self.pairs = sorted(pairs, key=lambda item: -len(item[1]))
        self.patterns = [(re.compile(re.escape(path) + r"(?=$|[/\"\s:,\]})'])"), label)
                         for label, path in self.pairs]

    def __call__(self, text):
        for pattern, label in self.patterns:
            text = pattern.sub(label, text)
        return text


def parse_labels(values):
    pairs = []
    for value in values or []:
        label, _, path = value.partition("=")
        if not label.startswith("<") or not path.startswith("/"):
            raise SystemExit("bad --label " + value)
        pairs.append((label, path))
    return Labels(pairs)


def write_output(path, value, labels):
    """Exclusive creation of an absent output, with every real place replaced by its label."""
    text = labels(json.dumps(value, indent=1, sort_keys=True, ensure_ascii=True)) + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    return hashlib.sha256(text.encode("ascii")).hexdigest()


class Checks:
    """A list of named checks, each passed or failed, with an observed value."""

    def __init__(self):
        self.rows = []

    def add(self, check_id, passed, statement, observed=None):
        self.rows.append({"id": check_id, "passed": bool(passed), "statement": statement,
                          "observed": observed})
        return bool(passed)

    def summary(self):
        failed = [row["id"] for row in self.rows if not row["passed"]]
        return {"total": len(self.rows), "passed": len(self.rows) - len(failed), "failed": failed}


def _sysctl_reader():
    """sysctlbyname from libSystem through ctypes (no process start); returns read(name) -> bytes."""
    import ctypes
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    function = libc.sysctlbyname
    function.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                         ctypes.c_size_t]
    function.restype = ctypes.c_int

    def read(name):
        size = ctypes.c_size_t(0)
        if function(name, None, ctypes.byref(size), None, 0) != 0:
            raise OSError(ctypes.get_errno(), "sysctl size")
        buffer = ctypes.create_string_buffer(size.value)
        if function(name, buffer, ctypes.byref(size), None, 0) != 0:
            raise OSError(ctypes.get_errno(), "sysctl read")
        return buffer.raw[:size.value]
    return read


def sysctl_text(name):
    raw = _sysctl_reader()(name.encode("ascii"))
    return raw.rstrip(b"\0").decode("ascii")


def sysctl_int(name):
    raw = _sysctl_reader()(name.encode("ascii"))
    return int.from_bytes(raw, "little", signed=True)


def load(path):
    """Load another of my scripts by its path (no sys.path change; -B writes no bytecode)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("w3_" + os.path.basename(path)[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
