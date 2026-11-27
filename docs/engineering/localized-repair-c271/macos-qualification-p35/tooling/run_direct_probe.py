#!/usr/bin/env python3
"""Direct-probe runner for gate MH of C271-P35: the probe syntax check, P06-H01, P06-H02 and MC36.

It makes one start per frozen row through supervisor_darwin_v01.run_process, under the row's frozen
argv, cwd (the supervisor's stage), environment, limits and label, and it keeps stdout, stderr, the
exit status, the receipt and the started record. It never passes through the provider's parent
guard (P07 section 5) and it does not interpret scientific output: it records the raw evidence, the
start count, the cleanup receipt and the boot session around the start, and it checks only the
row's frozen evidence predicates:

* the exit status, and the supervisor's own error, which must equal the row's frozen
  supervisor_error both as the raised Stop and as the receipt's error (TR-02): for an expected
  status N other than 0 exactly {code OTRAY-E-BACKEND, reason "Child exited with status N", state
  REJECTED}, and null for 0. Any other supervisor refusal (a remaining descendant, a staged-output
  violation, a deadline, the log ceiling, an interruption) therefore misses the row;
* stdout and stderr, exactly or by literal substrings that must or must not occur;
* paths that must be absent, or present, after the start; literal texts in named files, such as
  the probe's own probe.json; and JSON members of such files, equal to a value or absent. Every
  file such a predicate reads must be absent when the row's intent is written (TR-03), so no file
  that existed before the start can meet it. The probe reports a refusal raised inside its try
  block, MC36's among them, in probe.json, not on stderr.

Each row also carries its frozen input descriptors (path, SHA-256, size, mode), which bind every
file of its stage, and the exact set of its stage's entries; both are verified when the rows are
read and again immediately before the start (TR-03). The four supervisor files are bound by SHA-256
values supplied as arguments. They are loaded only after those digests are checked, and they are
compiled from the verified bytes, so no bytecode file and no other copy of the source can stand in
for them. The Node executable, the probe and the module loader are bound the same way, and are
checked again immediately before each start. The tool runs from its committed place inside the
root: its own __main__ is the one root module it admits besides the four supervisor files (TR-01).

The rows document, bound by a SHA-256 supplied outside it, admits exactly the row IDs
probe-syntax-check, P06-H01, P06-H02, MC36 and MC30-probe, each at most once and each in its own
stage, each with the contract's declared environment and one of two argv shapes:

  syntax: [NODE, (--no-addons, --max-old-space-size=256,)? --check, PROBE]
  probe:  [NODE, --no-addons, --max-old-space-size=256, --experimental-loader, LOADER, PROBE,
           --expected-config-sha256, DIGEST, --job, STAGE/job.json]

MC30-probe is admitted only if the operational freeze adds it: one probe start whose HOST input
records __CF_USER_TEXT_ENCODING as null, so that the probe's own environment binding refuses exactly
when the variable reached Node's process.env (MH-PLAN section 10, N-04). No tool can read the value
that Node's environment held: the probe does not report it, and the supervisor passes and records
only the declared environment.

No row is retried. An unknown outcome or an interruption stops every later row, and an interrupted
run's state is UNKNOWN (FAILURE-CAPTURE section 2). A row that misses its predicates stops the later
rows unless the rows document declares them independent. SIGTERM and SIGHUP are handled as SIGINT
is, so the supervisor's own cleanup ends a started child's group.

Launch (a start without -B refuses, N-09):

  env -i PATH=/usr/bin:/bin <worktree>/.venv/bin/python -I -S -B run_direct_probe.py --root <worktree> \
      --bind prototypes/__init__.py=H ... --rows ROWS --rows-sha256 H --node NODE --node-sha256 H \
      --probe PROBE --probe-sha256 H --loader LOADER --loader-sha256 H --output-dir OUT
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import posixpath
import re
import signal
import stat
import sys
import time

SCHEMA_ROWS = "ontokin.c271.p35-direct-probe-rows/2"
SCHEMA_RUN = "ontokin.c271.p35-direct-probe-run/2"
SCHEMA_ROW = "ontokin.c271.p35-direct-probe-row/2"
ROW_IDS = ("probe-syntax-check", "P06-H01", "P06-H02", "MC36", "MC30-probe")
ROW_KINDS = {"probe-syntax-check": "syntax", "P06-H01": "probe", "P06-H02": "probe", "MC36": "probe",
             "MC30-probe": "probe"}
ROW_KEYS = {"id", "argv", "stage", "label", "environment", "total_ms", "stage_ms", "inputs", "stage_entries",
            "expected"}
EXPECTED_KEYS = {"returncode", "supervisor_error", "stdout_exact", "stderr_exact", "stdout_includes",
                 "stdout_excludes", "stderr_includes", "stderr_excludes", "absent_paths", "present_paths",
                 "file_includes", "json_members"}
# The four files of the Darwin supervisor's import, in load order (W3-OBSERVER section 7).
SUPERVISOR_FILES = (
    ("prototypes", "prototypes/__init__.py", True),
    ("prototypes.static_tray_v01", "prototypes/static_tray_v01/__init__.py", True),
    ("prototypes.static_tray_v01.supervisor", "prototypes/static_tray_v01/supervisor.py", False),
    ("prototypes.static_tray_v01.supervisor_darwin_v01", "prototypes/static_tray_v01/supervisor_darwin_v01.py", False))
DARWIN_MODULE = "prototypes.static_tray_v01.supervisor_darwin_v01"
BASE_MODULE = "prototypes.static_tray_v01.supervisor"
# Contract section 7 and prototypes/static_tray_v01/format_check.py: the declared environment.
DECLARED_ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
                        "UV_THREADPOOL_SIZE": "2"}
NODE_FLAGS = ["--no-addons", "--max-old-space-size=256"]
MAX_TOTAL_MS, CLEANUP_MS = 30000, 2000
FILE_PREDICATE_BYTES = 4 * 1024 * 1024
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
SHA = re.compile(r"[0-9a-f]{64}")
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                            "os.system", "os.startfile"))
# ctypes lookups of libc's process-creation functions; a call through them raises no audit event of its own.
CTYPES_PROCESS_SYMBOLS = frozenset(("fork", "vfork", "posix_spawn", "posix_spawnp", "execve", "execv", "execvp",
                                    "execvpe", "execl", "execlp", "execle", "system", "popen"))
INTERRUPTIONS = ("KeyboardInterrupt", "SystemExit")
EXIT_ALL_MET, EXIT_UNMET, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3


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


def read_regular(path, maximum, *, rule="INPUT"):
    """The bytes and binding of a regular file, opened without following a final link; a change during the read refuses."""
    canonical_path(path, rule=rule)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise Refusal(rule, "Cannot open the input", path=path, error=str(exc)) from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise Refusal(rule, "The input is not a regular file", path=path)
        if before.st_size > maximum:
            raise Refusal(rule, "The input exceeds its byte bound", path=path, size_bytes=before.st_size,
                          maximum=maximum)
        chunks, total = [], 0
        while True:
            block = os.read(fd, min(1 << 20, maximum + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            if total > maximum:
                raise Refusal(rule, "The input grew beyond its byte bound", path=path)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    named = os.lstat(path)
    if _identity(before) != _identity(after) or _identity(after) != _identity(named) or total != before.st_size:
        raise Refusal(rule, "The input changed while it was read", path=path)
    data = b"".join(chunks)
    return data, {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": total, "mode": mode_text(before.st_mode)}


def file_binding(path, *, rule="INPUT"):
    """SHA-256, size and mode of a large regular file, streamed, opened without following a final link."""
    canonical_path(path, rule=rule)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
    except OSError as exc:
        raise Refusal(rule, "Cannot open the input", path=path, error=str(exc)) from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise Refusal(rule, "The input is not a regular file", path=path)
        digest, total = hashlib.sha256(), 0
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
            total += len(block)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    named = os.lstat(path)
    if _identity(before) != _identity(after) or _identity(after) != _identity(named) or total != before.st_size:
        raise Refusal(rule, "The input changed while it was read", path=path)
    return {"sha256": digest.hexdigest(), "size_bytes": total, "mode": mode_text(before.st_mode)}


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


def create_output_directory(path, *, private=True):
    """Create one absent output directory in an existing canonical directory."""
    canonical_path(path, rule="OUTPUT")
    canonical_path(os.path.dirname(path), kind="dir", rule="OUTPUT")
    try:
        os.mkdir(path, 0o700 if private else 0o755)
    except FileExistsError as exc:
        raise Refusal("OUTPUT", "The output directory exists; it is never reused", path=path) from exc
    fsync_directory(os.path.dirname(path))
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
            "pid": os.getpid(),
            "python": {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
                       "build_string": sys.version, "executable": sys.executable,
                       "flags": {name: getattr(sys.flags, name) for name in FLAG_NAMES}}}


def text_of(value, limit=4096):
    if isinstance(value, bytes):
        value = os.fsdecode(value)
    elif isinstance(value, os.PathLike):
        value = os.fsdecode(os.fspath(value))
    text = value if isinstance(value, str) else repr(value)
    return text if len(text) <= limit else text[:limit] + "...[%d more characters]" % (len(text) - limit)


def environment_summary(env):
    """Names and a digest only: no tool writes the values of a child's environment (TR-06)."""
    mapping = {text_of(k, 256): text_of(v, 65536) for k, v in dict(env).items()}
    raw = json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return {"names": sorted(mapping), "sha256": hashlib.sha256(raw).hexdigest()}


def describe_process_event(event, args):
    if event == "os.system":
        return {"event": event, "command": text_of(args[0])}
    if event == "ctypes.dlsym":
        return {"event": event, "symbol": text_of(args[1] if len(args) > 1 else None)}
    if event == "subprocess.Popen":
        executable, argv, cwd, env = args
    elif event in ("os.posix_spawn", "os.exec"):
        (executable, argv, env), cwd = args, None
    elif event == "os.spawn":
        (_, executable, argv, env), cwd = args, None
    else:
        return {"event": event}
    argv = [argv] if isinstance(argv, (str, bytes, os.PathLike)) else list(argv)
    return {"event": event, "executable": None if executable is None else text_of(executable),
            "argv": [text_of(item) for item in argv[:256]], "cwd": None if cwd is None else text_of(cwd),
            "environment": None if env is None else environment_summary(env)}


class ProcessAudit:
    """An audit hook that records every process-creation event; with block set, it refuses the event.

    Its blind spots (TR-08): _posixsubprocess.fork_exec, which multiprocessing's spawn and forkserver
    start methods call, raises no audit event, and a call through ctypes raises none either. A ctypes
    lookup of libc's fork, exec, posix_spawn, system or popen functions is recorded (and refused when
    blocking), but a lookup made before the hook was installed is not seen.
    """

    def __init__(self, *, block):
        self.block, self.events, self.enabled = block, [], True

    def __call__(self, event, args):
        if not self.enabled:
            return
        if event == "ctypes.dlsym":
            name = args[1] if len(args) > 1 else None
            if not (isinstance(name, str) and name in CTYPES_PROCESS_SYMBOLS):
                return
        elif event not in PROCESS_EVENTS:
            return
        try:
            row = describe_process_event(event, args)
        except BaseException as exc:  # the hook must describe, never fail, unless it blocks
            row = {"event": event, "description_error": type(exc).__name__}
        row.update(sequence=len(self.events) + 1, monotonic=time.monotonic(), utc=utc_now(), blocked=self.block)
        self.events.append(row)
        if self.block:
            raise PermissionError("Process creation is refused while the MH tool runs: " + event)


def own_main_admission(root):
    """TR-01: this running tool's own __main__, when its file lies under the root: the one root module admitted."""
    main = sys.modules.get("__main__")
    path = getattr(main, "__file__", None)
    own = os.path.realpath(__file__)
    if type(path) is str and os.path.realpath(path) == own and own.startswith(root + "/"):
        return {"module": "__main__", "path": own, "admitted": True,
                "reason": "the running tool itself, identified by realpath equality with its own file"}
    return None


_SYSCTL = []


def boot_session_uuid():
    """kern.bootsessionuuid through sysctlbyname (TR-10); None if it cannot be read.

    The first call resolves the function before any row's start, so no lookup happens between starts.
    """
    import ctypes
    if not _SYSCTL:
        try:
            function = ctypes.CDLL(LIBSYSTEM, use_errno=True).sysctlbyname
        except (OSError, AttributeError):
            return None
        function.argtypes = (ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                             ctypes.c_size_t)
        function.restype = ctypes.c_int
        _SYSCTL.append(function)
    buffer = ctypes.create_string_buffer(128)
    size = ctypes.c_size_t(ctypes.sizeof(buffer))
    if _SYSCTL[0](b"kern.bootsessionuuid", buffer, ctypes.byref(size), None, 0) != 0:
        return None
    return buffer.value.decode("ascii", "replace") or None


# ---------------------------------------------------------------------------
# The supervisor, compiled from verified bytes
# ---------------------------------------------------------------------------

def parse_bindings(values):
    bindings = {}
    for value in values or []:
        rel, sep, digest = value.partition("=")
        if not sep or SHA.fullmatch(digest) is None or rel in bindings:
            raise Refusal("SUPERVISOR", "A binding is RELATIVE_PATH=SHA256, given once per file", binding=value)
        bindings[rel] = digest
    expected = sorted(rel for _, rel, _ in SUPERVISOR_FILES)
    if sorted(bindings) != expected:
        raise Refusal("SUPERVISOR", "Exactly the four supervisor files must be bound", given=sorted(bindings),
                      expected=expected)
    return bindings


def load_supervisor(root, bindings):
    """Load the four files from their verified bytes, in order, as the import system would name them."""
    import importlib.machinery
    import importlib.util
    already = sorted(name for name, _, _ in SUPERVISOR_FILES if name in sys.modules)
    if already:
        raise Refusal("SUPERVISOR", "A supervisor module is already loaded", modules=already)
    loaded = []
    for name, rel, package in SUPERVISOR_FILES:
        path = canonical_path(root + "/" + rel, kind="file", rule="SUPERVISOR")
        raw, binding = read_regular(path, 4 * 1024 * 1024, rule="SUPERVISOR")
        if binding["sha256"] != bindings[rel]:
            raise Refusal("SUPERVISOR", "A supervisor file differs from its supplied SHA-256", path=path,
                          observed=binding["sha256"])
        try:
            code = compile(raw, path, "exec", dont_inherit=True)
        except SyntaxError as exc:
            raise Refusal("SUPERVISOR", "A supervisor file does not compile", path=path, error=str(exc)) from exc
        spec = importlib.machinery.ModuleSpec(name, None, origin=path, is_package=package)
        if package:
            spec.submodule_search_locations = [os.path.dirname(path)]
        module = importlib.util.module_from_spec(spec)
        module.__file__, module.__cached__ = path, None
        sys.modules[name] = module
        parent, _, child = name.rpartition(".")
        if parent:
            setattr(sys.modules[parent], child, module)
        try:
            exec(code, module.__dict__)
        except BaseException as exc:
            sys.modules.pop(name, None)
            raise Refusal("SUPERVISOR", "A supervisor file failed while it was loaded", path=path,
                          error=type(exc).__name__ + ": " + str(exc)) from exc
        loaded.append({"module": name, "path": path, **binding, "compiled_from_verified_bytes": True})
    darwin, base = sys.modules[DARWIN_MODULE], sys.modules[BASE_MODULE]
    run_process = getattr(darwin, "run_process", None)
    checks = {
        "run_process_from_bound_file": getattr(getattr(run_process, "__code__", None), "co_filename", None)
        == root + "/" + SUPERVISOR_FILES[3][1],
        "clock_is_the_original": getattr(darwin, "Clock", None) is getattr(base, "Clock", None) is not None,
        "stop_is_the_original": getattr(darwin, "Stop", None) is getattr(base, "Stop", None) is not None,
        "json_bytes_is_the_original": getattr(darwin, "json_bytes", None) is getattr(base, "json_bytes", None)
        is not None}
    own = os.path.realpath(__file__)
    supervisor_names = {name for name, _, _ in SUPERVISOR_FILES}
    others = sorted(module_name for module_name, module in sys.modules.items()
                    if type(getattr(module, "__file__", None)) is str
                    and os.path.realpath(module.__file__).startswith(root + "/")
                    and module_name not in supervisor_names
                    and not (module_name == "__main__" and os.path.realpath(module.__file__) == own))
    if not all(checks.values()) or others:
        raise Refusal("SUPERVISOR", "The loaded supervisor is not exactly the bound files", checks=checks,
                      other_project_modules=others)
    return darwin, base, loaded, checks


# ---------------------------------------------------------------------------
# Rows: their shape, their frozen inputs and stage, and their predicates
# ---------------------------------------------------------------------------

def bound_file(path, sha256, what, *, executable=False):
    canonical_path(path, kind="file", rule="BINDING")
    if type(sha256) is not str or SHA.fullmatch(sha256) is None:
        raise Refusal("BINDING", "Expected a lowercase SHA-256 for the " + what)
    binding = file_binding(path, rule="BINDING")
    if binding["sha256"] != sha256:
        raise Refusal("BINDING", "The " + what + " differs from its supplied SHA-256", path=path,
                      observed=binding["sha256"])
    if executable and not os.stat(path).st_mode & stat.S_IXUSR:
        raise Refusal("BINDING", "The " + what + " is not executable", path=path)
    return {"path": path, **binding}


def expected_supervisor_error(returncode):
    """TR-02: the one supervisor error a row can expect, implied by its exit status."""
    if returncode == 0:
        return None
    return {"code": "OTRAY-E-BACKEND", "reason": "Child exited with status " + str(returncode), "state": "REJECTED"}


def stage_entries(stage):
    """Every entry under the stage, links never followed: {path, kind[, target]}, sorted by path."""
    rows, pending = [], [""]
    try:
        while pending:
            relative = pending.pop()
            directory = stage + ("/" + relative if relative else "")
            with os.scandir(directory) as iterator:
                names = sorted(entry.name for entry in iterator)
            for name in names:
                rel = relative + "/" + name if relative else name
                info = os.lstat(stage + "/" + rel)
                if stat.S_ISLNK(info.st_mode):
                    rows.append({"path": rel, "kind": "symlink", "target": os.readlink(stage + "/" + rel)})
                elif stat.S_ISDIR(info.st_mode):
                    rows.append({"path": rel, "kind": "directory"})
                    pending.append(rel)
                elif stat.S_ISREG(info.st_mode):
                    rows.append({"path": rel, "kind": "file"})
                else:
                    rows.append({"path": rel, "kind": "special"})
    except OSError as exc:
        raise Refusal("ROW-STAGE", "The stage cannot be listed", stage=stage, error=str(exc)) from exc
    return sorted(rows, key=lambda row: row["path"])


def predicate_targets(expected):
    return sorted(set(expected["present_paths"]) | set(expected["file_includes"]) | set(expected["json_members"]))


def supervisor_outputs(row):
    return [row["stage"] + "/" + row["label"] + suffix for suffix in (".stdout.log", ".stderr.log", ".process.json")]


def check_frozen_state(row):
    """TR-03: the row's frozen inputs, its stage's exact entries and its absent targets, as they are now."""
    inputs = []
    for item in row["inputs"]:
        actual = file_binding(item["path"], rule="ROW-INPUT")
        if actual != {key: item[key] for key in ("sha256", "size_bytes", "mode")}:
            raise Refusal("ROW-INPUT", "A frozen input of the row differs", id=row["id"], path=item["path"],
                          observed=actual)
        inputs.append({"path": item["path"], **actual})
    observed = stage_entries(row["stage"])
    frozen = sorted(row["stage_entries"], key=lambda entry: entry["path"])
    if observed != frozen:
        frozen_map = {entry["path"]: entry for entry in frozen}
        observed_map = {entry["path"]: entry for entry in observed}
        raise Refusal("ROW-STAGE", "The stage's entries are not exactly the frozen set", id=row["id"],
                      missing=sorted(set(frozen_map) - set(observed_map)),
                      extra=sorted(set(observed_map) - set(frozen_map)),
                      changed=sorted(name for name in set(frozen_map) & set(observed_map)
                                     if frozen_map[name] != observed_map[name]))
    targets = predicate_targets(row["expected"])
    present = [path for path in targets + supervisor_outputs(row) if os.path.lexists(path)]
    if present:
        raise Refusal("ROW-TARGET", "A file that a predicate or the supervisor writes exists before the start",
                      id=row["id"], paths=present)
    return {"inputs": inputs, "stage_entries": observed, "targets_absent_at_intent": targets,
            "supervisor_outputs_absent_at_intent": supervisor_outputs(row)}


def string_list(value):
    return type(value) is list and all(type(item) is str and item for item in value)


def validate_expected(ident, expected):
    if type(expected) is not dict or set(expected) != EXPECTED_KEYS:
        raise Refusal("ROWS", "The expected predicates are malformed", id=ident, expected=sorted(EXPECTED_KEYS))
    if type(expected["returncode"]) is not int:
        raise Refusal("ROWS", "The expected exit status is not an integer", id=ident)
    if expected["supervisor_error"] != expected_supervisor_error(expected["returncode"]):
        raise Refusal("ROWS", "The expected supervisor error must be the one its exit status implies (TR-02)",
                      id=ident, expected=expected_supervisor_error(expected["returncode"]))
    for key in ("stdout_exact", "stderr_exact"):
        if expected[key] is not None and type(expected[key]) is not str:
            raise Refusal("ROWS", "An exact stream predicate is a string or null", id=ident, key=key)
    for key in ("stdout_includes", "stdout_excludes", "stderr_includes", "stderr_excludes"):
        if not string_list(expected[key]):
            raise Refusal("ROWS", "A stream predicate is a list of non-empty strings", id=ident, key=key)
    for key in ("absent_paths", "present_paths"):
        if type(expected[key]) is not list:
            raise Refusal("ROWS", "A path predicate is a list", id=ident, key=key)
        for path in expected[key]:
            canonical_path(path, rule="ROWS")
    if type(expected["file_includes"]) is not dict or not all(string_list(items) and items
                                                               for items in expected["file_includes"].values()):
        raise Refusal("ROWS", "file_includes maps a path to a list of literal texts", id=ident)
    members = expected["json_members"]
    if type(members) is not dict:
        raise Refusal("ROWS", "json_members maps a path to a list of member predicates", id=ident)
    for path, items in members.items():
        if type(items) is not list or not items:
            raise Refusal("ROWS", "json_members maps a path to a non-empty list", id=ident, path=path)
        for item in items:
            ok = (type(item) is dict and type(item.get("pointer")) is str
                  and (item["pointer"] == "" or item["pointer"].startswith("/"))
                  and (set(item) == {"pointer", "equals"}
                       or (set(item) == {"pointer", "absent"} and item["absent"] is True)))
            if not ok:
                raise Refusal("ROWS", "A member predicate is {pointer, equals} or {pointer, absent: true}", id=ident,
                              path=path)
    for path in list(expected["file_includes"]) + list(members):
        canonical_path(path, rule="ROWS")


def validate_inputs_and_stage(row):
    ident, stage = row["id"], row["stage"]
    if type(row["inputs"]) is not list:
        raise Refusal("ROWS", "inputs is a list of descriptors", id=ident)
    paths = set()
    for item in row["inputs"]:
        if (type(item) is not dict or set(item) != {"path", "sha256", "size_bytes", "mode"}
                or type(item["sha256"]) is not str or SHA.fullmatch(item["sha256"]) is None
                or type(item["size_bytes"]) is not int or type(item["mode"]) is not str
                or re.fullmatch(r"0o[0-7]{3,4}", item["mode"]) is None or item["path"] in paths):
            raise Refusal("ROWS", "An input descriptor is malformed or repeated", id=ident)
        canonical_path(item["path"], kind="file", rule="ROWS")
        paths.add(item["path"])
    if type(row["stage_entries"]) is not list:
        raise Refusal("ROWS", "stage_entries is a list", id=ident)
    names = set()
    for entry in row["stage_entries"]:
        rel = entry.get("path") if type(entry) is dict else None
        if (type(entry) is not dict or set(entry) != {"path", "kind"} or entry["kind"] not in ("file", "directory")
                or type(rel) is not str or not rel or rel.startswith("/") or posixpath.normpath(rel) != rel
                or ".." in rel.split("/") or rel in names):
            raise Refusal("ROWS", "A stage entry is {path, kind} with kind file or directory, given once", id=ident,
                          entry=entry)
        names.add(rel)
        if entry["kind"] == "file" and stage + "/" + rel not in paths:
            raise Refusal("ROWS", "A file of the stage is not one of the row's frozen inputs", id=ident, path=rel)


def validate_rows(document, *, node, probe, loader):
    if type(document) is not dict or set(document) != {"schema", "rows_independent", "rows"} \
            or document["schema"] != SCHEMA_ROWS or type(document["rows_independent"]) is not bool \
            or type(document["rows"]) is not list or not document["rows"]:
        raise Refusal("ROWS", "The rows document is not a " + SCHEMA_ROWS + " document with rows")
    seen, stages, rows = set(), set(), []
    for index, row in enumerate(document["rows"]):
        if type(row) is not dict or set(row) != ROW_KEYS:
            raise Refusal("ROWS", "Row %d has missing or unknown members" % index, expected=sorted(ROW_KEYS))
        ident = row["id"]
        if ident not in ROW_IDS or ident in seen:
            raise Refusal("ROWS", "Row IDs are probe-syntax-check, P06-H01, P06-H02, MC36 and MC30-probe, each at "
                          "most once", id=ident)
        seen.add(ident)
        argv, stage = row["argv"], row["stage"]
        if type(argv) is not list or not all(type(item) is str and item and "\0" not in item for item in argv):
            raise Refusal("ROWS", "The argv is not a list of non-empty strings", id=ident)
        canonical_path(stage, kind="dir", rule="ROWS")
        if stage in stages:
            raise Refusal("ROWS", "Two rows share a stage (TR-10)", id=ident, stage=stage)
        stages.add(stage)
        if ROW_KINDS[ident] == "syntax":
            shape = argv in ([node, "--check", probe], [node, *NODE_FLAGS, "--check", probe])
        else:
            shape = (len(argv) == 10 and argv[:6] == [node, *NODE_FLAGS, "--experimental-loader", loader, probe]
                     and argv[6] == "--expected-config-sha256" and SHA.fullmatch(argv[7]) is not None
                     and argv[8] == "--job" and argv[9] == stage + "/job.json")
        if not shape:
            raise Refusal("ROWS", "The argv is not the admitted shape of its row", id=ident, argv=argv)
        if type(row["label"]) is not str or LABEL.fullmatch(row["label"]) is None:
            raise Refusal("ROWS", "The label is not a plain file-name stem", id=ident)
        if row["environment"] != DECLARED_ENVIRONMENT:
            raise Refusal("ROWS", "The environment is not exactly the contract's declared environment", id=ident)
        total, work = row["total_ms"], row["stage_ms"]
        if not (type(total) is int and type(work) is int and 0 < total <= MAX_TOTAL_MS
                and 0 < work <= total - CLEANUP_MS):
            raise Refusal("ROWS", "Limits need 0 < stage_ms <= total_ms - 2000 and total_ms <= 30000", id=ident)
        validate_inputs_and_stage(row)
        validate_expected(ident, row["expected"])
        check_frozen_state(row)
        rows.append(row)
    return rows


def json_equal(first, second):
    """JSON equality: booleans are not numbers, numbers compare by value."""
    if type(first) is bool or type(second) is bool:
        return type(first) is type(second) and first == second
    if type(first) in (int, float) and type(second) in (int, float):
        return float(first) == float(second)
    if isinstance(first, list) and isinstance(second, list):
        return len(first) == len(second) and all(json_equal(a, b) for a, b in zip(first, second))
    if isinstance(first, dict) and isinstance(second, dict):
        return set(first) == set(second) and all(json_equal(first[key], second[key]) for key in first)
    return type(first) is type(second) and first == second


def json_pointer(document, pointer):
    """(found, value) for an RFC 6901 pointer."""
    current = document
    if pointer == "":
        return True, current
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                return False, None
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token[0] == "0") or int(token) >= len(current):
                return False, None
            current = current[int(token)]
        else:
            return False, None
    return True, current


# ---------------------------------------------------------------------------
# One start
# ---------------------------------------------------------------------------

def read_output(path, limit=4 * 1024 * 1024):
    if not os.path.lexists(path):
        return None, {"path": path, "state": "absent"}
    try:
        raw, binding = read_regular(path, limit, rule="OUTPUT")
    except Refusal as exc:
        return None, {"path": path, "state": "unreadable", "refusal": exc.as_dict()}
    return raw, {"path": path, "state": "present", **binding}


def evaluate(expected, *, failure, receipt_error, stdout, stderr, returncode):
    """Each frozen predicate, after the start; every file it reads was absent at intent."""
    supervisor = failure.as_dict() if failure is not None else None
    stdout_text = stdout.decode("utf-8", "replace") if stdout is not None else None
    stderr_text = stderr.decode("utf-8", "replace") if stderr is not None else None
    predicates = {
        "returncode": returncode == expected["returncode"] and type(returncode) is int,
        "supervisor_error_raised": supervisor == expected["supervisor_error"],
        "supervisor_error_in_receipt": receipt_error == expected["supervisor_error"],
        "stdout_exact": None if expected["stdout_exact"] is None else stdout_text == expected["stdout_exact"],
        "stderr_exact": None if expected["stderr_exact"] is None else stderr_text == expected["stderr_exact"],
        "stdout_includes": {item: stdout is not None and item.encode("utf-8") in stdout
                            for item in expected["stdout_includes"]},
        "stdout_excludes": {item: stdout is not None and item.encode("utf-8") not in stdout
                            for item in expected["stdout_excludes"]},
        "stderr_includes": {item: stderr is not None and item.encode("utf-8") in stderr
                            for item in expected["stderr_includes"]},
        "stderr_excludes": {item: stderr is not None and item.encode("utf-8") not in stderr
                            for item in expected["stderr_excludes"]},
        "absent_paths": {path: not os.path.lexists(path) for path in expected["absent_paths"]},
        "present_paths": {}, "file_includes": {}, "json_members": {}}
    for path in expected["present_paths"]:
        _, binding = read_output(path)
        predicates["present_paths"][path] = binding
    for path, items in expected["file_includes"].items():
        raw, binding = read_output(path, FILE_PREDICATE_BYTES)
        predicates["file_includes"][path] = {"file": binding,
                                             "includes": {item: raw is not None and item.encode("utf-8") in raw
                                                          for item in items}}
    for path, items in expected["json_members"].items():
        raw, binding = read_output(path, FILE_PREDICATE_BYTES)
        document, parsed = None, False
        if raw is not None:
            try:
                document, parsed = strict_json(raw, what="predicate file"), True
            except Refusal:
                pass
        results = []
        for item in items:
            found, value = json_pointer(document, item["pointer"]) if parsed else (False, None)
            if "absent" in item:
                results.append({"pointer": item["pointer"], "absent": True, "met": parsed and not found})
            else:
                results.append({"pointer": item["pointer"], "equals": item["equals"], "found": found,
                                "met": parsed and found and json_equal(value, item["equals"])})
        predicates["json_members"][path] = {"file": binding, "parsed": parsed, "members": results}
    met = (predicates["returncode"] and predicates["supervisor_error_raised"]
           and predicates["supervisor_error_in_receipt"]
           and predicates["stdout_exact"] is not False and predicates["stderr_exact"] is not False
           and all(predicates["stdout_includes"].values()) and all(predicates["stdout_excludes"].values())
           and all(predicates["stderr_includes"].values()) and all(predicates["stderr_excludes"].values())
           and all(predicates["absent_paths"].values())
           and all(binding.get("state") == "present" for binding in predicates["present_paths"].values())
           and all(all(row["includes"].values()) for row in predicates["file_includes"].values())
           and all(all(member["met"] for member in row["members"]) for row in predicates["json_members"].values()))
    return predicates, bool(met)


def run_row(row, *, darwin, base, audit, output, inputs):
    directory = create_output_directory(output + "/" + row["id"])
    boot_before = boot_session_uuid()
    write_new(directory + "/intent.json", json_text({"schema": SCHEMA_ROW, "state": "INTENT", "row": row,
                                                     "boot_session_uuid": boot_before, "utc": utc_now(),
                                                     "retry": False}))
    outcome = {"schema": SCHEMA_ROW, "id": row["id"], "row": row, "state": "UNKNOWN", "started_records": [],
               "started_record_failures": [], "supervisor_failure": None, "process": None,
               "boot_before": boot_before, "started_at_utc": utc_now(), "interrupted": False}
    try:
        # TR-03: the frozen inputs, the stage's exact entries and the absent targets, just before the start.
        verified = check_frozen_state(row)
        verified["bound"] = {key: bound_file(path, sha256, key, executable=executable)
                             for key, (path, sha256, executable) in inputs.items()}
    except Refusal as exc:
        outcome.update(state="REFUSED_BEFORE_START", refusal=exc.as_dict(), start_count_state="PROVEN_ZERO",
                       actual_starts=0, observed_starts_lower_bound=0, expectation_met=False,
                       finished_at_utc=utc_now())
        write_new(directory + "/outcome.json", json_text(outcome))
        return outcome
    outcome["verified_before_start"] = verified
    callbacks = []

    def on_started(record):
        callbacks.append(record)
        outcome["started_records"].append(record)
        # The start is made durable at once; a failed write is recorded and raised, and the supervisor
        # then ends the child through its own cleanup, so no start runs without its record.
        try:
            write_new(directory + "/started-%d.json" % len(callbacks),
                      json_text({"schema": SCHEMA_ROW, "state": "STARTED", "process": record, "utc": utc_now()}))
        except BaseException as exc:
            outcome["started_record_failures"].append({"type": type(exc).__name__, "reason": str(exc)})
            raise
    first_event = len(audit.events)
    clock = base.Clock(total_ms=row["total_ms"])
    stage_end = clock.started + row["stage_ms"] / 1000
    process, failure, unexpected = None, None, None
    try:
        process = darwin.run_process(list(row["argv"]), stage=row["stage"], label=row["label"], clock=clock,
                                     stage_end=stage_end, env=dict(row["environment"]), on_started=on_started,
                                     cancel_after_ms=None)
    except base.Stop as exc:
        failure, process = exc, getattr(exc, "process_record", None)
    except BaseException as exc:  # anything outside the supervisor's Stop interface is unknown after a start
        unexpected = exc
        process = getattr(exc, "process_record", None)
    boot_after = boot_session_uuid()
    events = audit.events[first_event:]
    interrupted = (unexpected is not None and isinstance(unexpected, (KeyboardInterrupt, SystemExit))) or (
        failure is not None and str(failure.reason).startswith(INTERRUPTIONS))
    outcome.update(process_events=events, process=process, boot_after=boot_after, interrupted=interrupted,
                   supervisor_failure=failure.as_dict() if failure is not None else None,
                   unexpected_failure=None if unexpected is None else {"type": type(unexpected).__name__,
                                                                       "reason": str(unexpected)})
    stdout, outcome["stdout"] = read_output(row["stage"] + "/" + row["label"] + ".stdout.log")
    stderr, outcome["stderr"] = read_output(row["stage"] + "/" + row["label"] + ".stderr.log")
    receipt_raw, outcome["receipt_file"] = read_output(row["stage"] + "/" + row["label"] + ".process.json")
    for key, raw in (("stdout", stdout), ("stderr", stderr)):
        if raw is not None:
            outcome[key]["text"] = text_of(raw.decode("utf-8", "backslashreplace"), 65536)
    receipt_error = "<no receipt>"
    if receipt_raw is not None:
        try:
            receipt = strict_json(receipt_raw, what="receipt")
            receipt_error = receipt.get("error") if type(receipt) is dict else "<not an object>"
        except Refusal:
            receipt_error = "<unparsed receipt>"
    pid = process.get("pid") if type(process) is dict else None
    if not events and not callbacks and pid is None and unexpected is None:
        count_state, actual = "PROVEN_ZERO", 0
    elif (len(events) == 1 and events[0].get("event") == "subprocess.Popen" and len(callbacks) == 1
          and type(pid) is int and pid > 0 and callbacks[0].get("pid") == pid and process.get("process_group") == pid
          and unexpected is None):
        count_state, actual = "OBSERVED_ONE", 1
    else:
        count_state, actual = "UNKNOWN", None
    outcome.update(start_count_state=count_state, actual_starts=actual,
                   observed_starts_lower_bound=max(len(events), len(callbacks)))
    receipt_matches = (receipt_raw is not None and type(process) is dict
                       and receipt_raw == base.json_bytes(process))
    cleanup = process.get("cleanup") if type(process) is dict else None
    cleanup_complete = (type(cleanup) is dict and cleanup.get("passed") is True
                        and cleanup.get("process_group_absent") is True and cleanup.get("reaped") is True
                        and process.get("handles_closed") is True)
    boot_unchanged = boot_before is not None and boot_before == boot_after
    outcome.update(receipt_file_matches_record=receipt_matches, receipt_error=receipt_error,
                   cleanup_complete=cleanup_complete, boot_unchanged=boot_unchanged)
    if count_state == "PROVEN_ZERO":
        state = "REFUSED_BEFORE_START"
    elif (count_state == "OBSERVED_ONE" and receipt_matches and cleanup_complete
          and not outcome["started_record_failures"]):
        state = "COMPLETED"
    else:
        state = "UNKNOWN"
    predicates, met = evaluate(row["expected"], failure=failure, receipt_error=receipt_error, stdout=stdout,
                               stderr=stderr, returncode=process.get("returncode") if type(process) is dict else None)
    outcome.update(state=state, predicates=predicates,
                   expectation_met=state == "COMPLETED" and met and boot_unchanged and not interrupted,
                   finished_at_utc=utc_now(),
                   clock={"requested_ms": row["total_ms"], "stage_ms": row["stage_ms"],
                          "elapsed_ms": clock.elapsed_ms()})
    write_new(directory + "/outcome.json", json_text(outcome))
    if isinstance(unexpected, (KeyboardInterrupt, SystemExit)):
        raise unexpected
    return outcome


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def run(args):
    started, monotonic = utc_now(), time.monotonic()
    root = canonical_path(args.root, kind="dir", rule="ROOT")
    output = create_output_directory(args.output_dir)
    record = {"schema": SCHEMA_RUN, "tool": tool_record(), "invocation": invocation_record(), "started_at_utc": started,
              "root": root, "state": "UNKNOWN", "rows": [], "loaded_project_files": []}
    try:
        require_no_bytecode()
        bindings = parse_bindings(args.bind)
        node = bound_file(args.node, args.node_sha256, "Node executable", executable=True)
        probe = bound_file(args.probe, args.probe_sha256, "probe")
        loader = bound_file(args.loader, args.loader_sha256, "module loader")
        if type(args.rows_sha256) is not str or SHA.fullmatch(args.rows_sha256) is None:
            raise Refusal("ROWS", "Expected a lowercase SHA-256 for the rows document")
        raw, rows_binding = read_regular(canonical_path(args.rows, kind="file", rule="ROWS"), 1024 * 1024, rule="ROWS")
        if rows_binding["sha256"] != args.rows_sha256:
            raise Refusal("ROWS", "The rows document differs from its supplied SHA-256", observed=rows_binding["sha256"])
        document = strict_json(raw, rule="ROWS", what="rows document")
        rows = validate_rows(document, node=node["path"], probe=probe["path"], loader=loader["path"])
        darwin, base, loaded, checks = load_supervisor(root, bindings)
    except Refusal as exc:
        record.update(state="REFUSED", refusal=exc.as_dict(), finished_at_utc=utc_now(),
                      elapsed_s=time.monotonic() - monotonic)
        write_new(output + "/run.json", json_text(record))
        sys.stderr.write("MH-DIRECT-PROBE " + json.dumps({"state": "REFUSED", "refusal": exc.as_dict()},
                                                         sort_keys=True) + "\n")
        return EXIT_REFUSED
    record.update(inputs={"rows": {"path": args.rows, **rows_binding}, "node": node, "probe": probe, "loader": loader},
                  rows_independent=document["rows_independent"], loaded_project_files=loaded, supervisor_checks=checks,
                  own_main_admitted=own_main_admission(root),
                  darwin_precondition_before_rows=darwin.darwin_precondition(),
                  boot_session_uuid_before_rows=boot_session_uuid(),
                  signals_handled_as_interruption=["SIGINT", "SIGTERM", "SIGHUP"])
    audit = ProcessAudit(block=False)
    sys.addaudithook(audit)
    inputs = {"node": (node["path"], node["sha256"], True), "probe": (probe["path"], probe["sha256"], False),
              "loader": (loader["path"], loader["sha256"], False)}
    stopped, loop_failure = None, None
    try:
        for row in rows:
            if stopped is not None:
                record["rows"].append({"id": row["id"], "state": "NOT_RUN", "reason": stopped})
                continue
            events_before = len(audit.events)
            try:
                outcome = run_row(row, darwin=darwin, base=base, audit=audit, output=output, inputs=inputs)
            except BaseException as exc:  # an interruption or a tool failure: nothing else runs
                failure = {"type": type(exc).__name__, "reason": str(exc)}
                if len(audit.events) == events_before:
                    record["rows"].append({"id": row["id"], "state": "FAILED_BEFORE_START", "failure": failure,
                                           "start_count_state": "PROVEN_ZERO", "actual_starts": 0,
                                           "observed_starts_lower_bound": 0, "expectation_met": False})
                    stopped = "the tool failed or was interrupted before an earlier row's start"
                else:
                    record["rows"].append({"id": row["id"], "state": "UNKNOWN", "failure": failure,
                                           "start_count_state": "UNKNOWN", "actual_starts": None,
                                           "observed_starts_lower_bound": len(audit.events) - events_before,
                                           "expectation_met": False})
                    stopped = "an earlier row's outcome is unknown"
                continue
            record["rows"].append({key: outcome.get(key) for key in (
                "id", "state", "start_count_state", "actual_starts", "observed_starts_lower_bound", "expectation_met",
                "interrupted")})
            if outcome["state"] == "UNKNOWN":
                stopped = "an earlier row's outcome is unknown"
            elif outcome.get("interrupted"):
                stopped = "the run was interrupted during an earlier row"
            elif not outcome["expectation_met"] and not document["rows_independent"]:
                stopped = "an earlier row did not meet its frozen predicates"
    except BaseException as exc:  # an interruption between rows
        loop_failure = {"type": type(exc).__name__, "reason": str(exc)}
    audit.enabled = False
    states = [row["state"] for row in record["rows"]]
    exact = [row.get("actual_starts") for row in record["rows"] if row["state"] != "NOT_RUN"]
    record.update(
        node_starts={"exact": None if any(value is None for value in exact) or loop_failure else sum(exact),
                     "observed_lower_bound": sum(row.get("observed_starts_lower_bound") or 0 for row in record["rows"])},
        process_events=audit.events, stopped_reason=stopped, loop_failure=loop_failure,
        boot_session_uuid_after_rows=boot_session_uuid(), finished_at_utc=utc_now(),
        elapsed_s=time.monotonic() - monotonic)
    record["interrupted"] = loop_failure is not None or any(row.get("interrupted") for row in record["rows"])
    # FAILURE-CAPTURE section 2: an interrupted command's outcome is unknown, even with a complete receipt.
    if "UNKNOWN" in states or record["interrupted"]:
        record["state"], code = "UNKNOWN", EXIT_UNKNOWN
    elif all(row.get("expectation_met") for row in record["rows"]) and len(record["rows"]) == len(rows):
        record["state"], code = "ALL_ROWS_MET", EXIT_ALL_MET
    else:
        record["state"], code = "ROWS_UNMET", EXIT_UNMET
    write_new(output + "/run.json", json_text(record))
    sys.stderr.write("MH-DIRECT-PROBE " + json.dumps({"state": record["state"], "rows": record["rows"]},
                                                     sort_keys=True) + "\n")
    return code


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def main(argv=None):
    for number in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, signal.default_int_handler)
    parser = _Parser(prog="run_direct_probe.py", allow_abbrev=False, description=__doc__.splitlines()[0])
    parser.add_argument("--root", required=True)
    parser.add_argument("--bind", action="append", required=True)
    for name in ("rows", "node", "probe", "loader"):
        parser.add_argument("--" + name, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--output-dir", required=True)
    try:
        require_no_bytecode()
        return run(parser.parse_args(argv))
    except Refusal as exc:
        sys.stderr.write(json.dumps({"schema": "ontokin.c271.p35-tool-refusal/1", "tool": "run_direct_probe.py",
                                     "state": "REFUSED", "refusal": exc.as_dict()}, sort_keys=True) + "\n")
        return EXIT_REFUSED
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        sys.stderr.write(json.dumps({"schema": "ontokin.c271.p35-tool-failure/1", "tool": "run_direct_probe.py",
                                     "state": "UNKNOWN", "error": {"type": type(exc).__name__, "reason": str(exc)}},
                                    sort_keys=True) + "\n")
        return EXIT_UNKNOWN


if __name__ == "__main__":
    raise SystemExit(main())
