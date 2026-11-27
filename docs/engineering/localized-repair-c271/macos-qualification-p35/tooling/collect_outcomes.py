#!/usr/bin/env python3
"""Unittest outcome collector for gate MH of C271-P35.

Two commands; each writes into one absent output directory:

  cohort    Runs the complete module tests.test_static_tray_readback_v01, both classes, as
            "python -B -m unittest -v tests.test_static_tray_readback_v01" runs it from the root,
            so that setUpClass and tearDownClass see all three CPU cases (P07 section 6).
  controls  Runs, separately, named methods of MI's frozen control module
            tests.test_current_host_readback_controls_v02 (for example MC37's method).

This process is the unit process. It uses unittest's own loader and TextTestRunner (verbosity 2,
the "default" warnings filter that unittest.main sets) with a result class that only records, so no
test, fixture or project object is substituted. One audit hook records every process-creation event
and refuses none. For each test the record holds the raw test ID, its outcome (pass, fail, error,
skip, expected failure, unexpected success; not_run or interrupted when unittest never finished it),
the traceback texts and the timing; class-level and module-level setup and teardown errors are kept
with unittest's own descriptions. No ID is normalized, except through P07 section 6's one declared
prefix alias, tests.test_static_tray_readback_v01. to test_static_tray_readback_v01., joined by the
source file, class, method and body identity.

Before any test runs, the collector refuses a process that the 0.2.0 provider would refuse or that
differs from the frozen unit environment: the interpreter flags, the exact environment, and in a
cohort the selection's HOST launcher, build, version and process image (W5-PROVIDER section 3).

Launch from the root, under the frozen environment, with the HOST launcher and -B only (a start
without -B refuses, N-09); the tool runs from its committed place inside the root, whose own
__main__ is the one root module it admits (TR-01):

  env -i <frozen environment> <worktree>/.venv/bin/python -B collect_outcomes.py cohort \
      --root <worktree> --environment ENV.json --environment-sha256 H --module-sha256 H --output-dir OUT
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import stat
import sys
import time

SCHEMA = "ontokin.c271.p35-unittest-outcomes/2"
JOURNAL_SCHEMA = "ontokin.c271.p35-unittest-outcome-event/1"
ENVIRONMENT_SCHEMA = "ontokin.c271.p35-unit-environment/1"
COHORT_MODULE = "tests.test_static_tray_readback_v01"
COHORT_FILE = "tests/test_static_tray_readback_v01.py"
# P07 section 6: the only declared alias between the package and the default-discovery prefix.
PACKAGE_PREFIX = "tests.test_static_tray_readback_v01."
DISCOVERY_PREFIX = "test_static_tray_readback_v01."
CONTROL_MODULE = "tests.test_current_host_readback_controls_v02"
CONTROL_FILE = "tests/test_current_host_readback_controls_v02.py"
# P07 section 6's table: the seven original methods, after the prefix.
REQUIRED_METHODS = (
    "ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries",
    "ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries",
    "ReadbackCPUControls.test_three_rejects_changed_synthetic_reference",
    "ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked",
    "ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup",
    "ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm",
    "ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending")
CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
CONFIG_SCHEMA = "ontokin.current-host-readback-config/0.2.0"
HOST_SCHEMA = "ontokin.current-host-readback-host/0.2.0"
CF_NAME = "__CF_USER_TEXT_ENCODING"
# tools/check_local.py UNIT_REMOVED_ENVIRONMENT: never present in a qualifying run's unit process.
UNIT_REMOVED_NAMES = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONBREAKPOINT",
                      "PYTHONUSERBASE", "PYTHONPYCACHEPREFIX", "LD_PRELOAD", "LD_LIBRARY_PATH", "NODE_OPTIONS",
                      "NODE_PATH", "__PYVENV_LAUNCHER__", "PYTHONEXECUTABLE")
UNIT_REMOVED_PREFIXES = ("DYLD_",)
# Set by the driver for a qualifying run's unit process (W4-DRIVER section 2).
UNIT_REQUIRED_VALUES = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
# tools/check_local.py git_environment(root): the only GIT_* names a qualifying unit process can hold (TR-09).
DRIVER_GIT_VALUES = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
                     "GIT_ATTR_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1",
                     "GIT_NO_LAZY_FETCH": "1"}
DRIVER_GIT_CEILING = "GIT_CEILING_DIRECTORIES"
METHODS_SCHEMA = "ontokin.current-host-readback-methods/0.2.0"
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                            "os.system", "os.startfile"))
# ctypes lookups of libc's process-creation functions; a call through them raises no audit event of its own.
CTYPES_PROCESS_SYMBOLS = frozenset(("fork", "vfork", "posix_spawn", "posix_spawnp", "execve", "execv", "execvp",
                                    "execvpe", "execl", "execlp", "execle", "system", "popen"))
TEXT_LIMIT = 1024 * 1024
EXIT_ALL_PASSED, EXIT_OTHER_OUTCOMES, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3


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

    def identity(info):
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_mode
    if identity(before) != identity(after) or identity(after) != identity(named) or total != before.st_size:
        raise Refusal(rule, "The input changed while it was read", path=path)
    data = b"".join(chunks)
    return data, {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": total, "mode": mode_text(before.st_mode)}


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


def create_output_directory(path):
    """Create one absent private output directory in an existing canonical directory."""
    canonical_path(path, rule="OUTPUT")
    canonical_path(os.path.dirname(path), kind="dir", rule="OUTPUT")
    try:
        os.mkdir(path, 0o700)
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

    Its blind spots: _posixsubprocess.fork_exec (which multiprocessing's spawn and forkserver start
    methods call) raises no audit event, and a call through ctypes raises none either. A ctypes
    lookup of libc's fork, exec, posix_spawn or system functions is recorded (and refused when
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


def loaded_project_files(root):
    rows = []
    for name, module in sorted(tuple(sys.modules.items())):
        path = getattr(module, "__file__", None)
        if type(path) is not str:
            continue
        real = os.path.realpath(path)
        if not real.startswith(root + "/"):
            continue
        row = {"module": name, "path": real[len(root) + 1:]}
        try:
            with open(real, "rb") as stream:
                row["sha256"] = hashlib.sha256(stream.read()).hexdigest()
        except OSError as exc:
            row["read_error"] = str(exc)
        cached = getattr(module, "__cached__", None)
        row["bytecode_present"] = bool(type(cached) is str and os.path.lexists(cached))
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# The durable journal: one JSON line per event, each line fsynced
# ---------------------------------------------------------------------------

class Journal:
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_APPEND
                          | getattr(os, "O_CLOEXEC", 0), 0o644)
        fsync_directory(os.path.dirname(path))
        self.lines, self.failure = 0, None

    def append(self, row):
        if self.fd is None:
            return
        try:
            data = (json.dumps({"schema": JOURNAL_SCHEMA, **row}, sort_keys=True, ensure_ascii=True,
                               allow_nan=False) + "\n").encode("ascii")
            view = memoryview(data)
            while view:
                view = view[os.write(self.fd, view):]
            os.fsync(self.fd)
            self.lines += 1
        except BaseException as exc:  # a journal failure is recorded; the run's outcome becomes unknown
            self.failure = {"type": type(exc).__name__, "reason": str(exc)}
            self.close()

    def close(self):
        if self.fd is not None:
            fd, self.fd = self.fd, None
            os.close(fd)


# ---------------------------------------------------------------------------
# Preconditions: the provider's unit-process rules and the frozen unit environment
# ---------------------------------------------------------------------------

def check_flags():
    flags = sys.flags
    if not flags.dont_write_bytecode:
        raise Refusal("PYTHON", "Run with -B: the interpreter trees are inventoried as exact sets (MC32)")
    if flags.isolated or flags.no_site or flags.ignore_environment or flags.safe_path:
        raise Refusal("PYTHON", "Run with -B only, as the unit stage runs its interpreter; -I, -S, -E and -P refuse")
    return {name: getattr(flags, name) for name in FLAG_NAMES}


def load_environment(path, sha256):
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise Refusal("ENVIRONMENT", "Expected a lowercase SHA-256 digest for the frozen environment")
    raw, binding = read_regular(path, 1024 * 1024, rule="ENVIRONMENT")
    if binding["sha256"] != sha256:
        raise Refusal("ENVIRONMENT", "The frozen environment differs from its supplied SHA-256", path=path)
    value = strict_json(raw, rule="ENVIRONMENT", what="frozen environment")
    if (type(value) is not dict or set(value) != {"schema", "environment"} or value["schema"] != ENVIRONMENT_SCHEMA
            or type(value["environment"]) is not dict
            or not all(type(k) is str and type(v) is str for k, v in value["environment"].items())):
        raise Refusal("ENVIRONMENT", "The frozen environment is not a " + ENVIRONMENT_SCHEMA + " document")
    if "HOME" in value["environment"]:
        raise Refusal("ENVIRONMENT", "HOME is not part of a frozen environment")
    return value["environment"], {"path": path, **binding}


def compare_environment(observed, frozen):
    """Exactly the frozen mapping; __CF_USER_TEXT_ENCODING, which macOS adds, is admitted and recorded (S10)."""
    observed = dict(observed)
    admitted = None
    if CF_NAME not in frozen and CF_NAME in observed:
        admitted = observed.pop(CF_NAME)
    missing = sorted(set(frozen) - set(observed))
    extra = sorted(set(observed) - set(frozen))
    differing = sorted(name for name in set(frozen) & set(observed) if frozen[name] != observed[name])
    if missing or extra or differing:
        raise Refusal("ENVIRONMENT", "The process environment differs from the frozen environment "
                      "(names only; values are not reported)", missing=missing, extra=extra, differing=differing)
    return admitted


def check_unit_environment_rules(frozen, root):
    git = sorted(name for name in frozen if name.startswith("GIT_"))
    driver = dict(DRIVER_GIT_VALUES, **{DRIVER_GIT_CEILING: os.path.dirname(root)})
    if git and (git != sorted(driver) or any(frozen[name] != driver[name] for name in git)):
        raise Refusal("ENVIRONMENT", "GIT_* names in the frozen environment must be exactly the driver's own "
                      "git_environment set, with its values, or absent", names=git)
    removed = sorted(name for name in frozen if name in UNIT_REMOVED_NAMES or name.startswith(UNIT_REMOVED_PREFIXES))
    if removed:
        raise Refusal("ENVIRONMENT", "The frozen environment holds names that the driver removes from a qualifying "
                      "unit process", names=removed)
    wrong = sorted(name for name, value in UNIT_REQUIRED_VALUES.items() if frozen.get(name) != value)
    if wrong:
        raise Refusal("ENVIRONMENT", "The frozen environment lacks values that the driver sets for a qualifying "
                      "unit process", names=wrong)
    if not frozen.get(CONFIG_ENV) or not frozen.get(DIGEST_ENV):
        raise Refusal("SELECTION", "A cohort needs both selection variables in the frozen environment")


def process_image():
    """proc_pidpath of this process, the provider's process-image observation."""
    import ctypes
    try:
        function = ctypes.CDLL(LIBSYSTEM, use_errno=True).proc_pidpath
    except (OSError, AttributeError) as exc:
        raise Refusal("PYTHON", "proc_pidpath is unavailable", error=str(exc)) from exc
    function.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32)
    function.restype = ctypes.c_int
    buffer = ctypes.create_string_buffer(4096)
    length = function(os.getpid(), buffer, ctypes.sizeof(buffer))
    if length <= 0:
        raise Refusal("PYTHON", "proc_pidpath failed", errno=ctypes.get_errno())
    return os.fsdecode(buffer.raw[:length])


def check_selection_and_host(frozen):
    """The configuration's digest (the driver's readback_config_identity check) and the HOST launcher rules
    that the provider's _check_python applies to the unit process."""
    import platform
    path, digest = frozen[CONFIG_ENV], frozen[DIGEST_ENV]
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise Refusal("SELECTION", "The selection digest is not a lowercase SHA-256")
    raw, config_binding = read_regular(canonical_path(path, rule="SELECTION"), 1024 * 1024, rule="SELECTION")
    if config_binding["sha256"] != digest:
        raise Refusal("SELECTION", "The configuration differs from the selected digest", path=path)
    config = strict_json(raw, rule="SELECTION", what="configuration")
    if type(config) is not dict or config.get("schema") != CONFIG_SCHEMA:
        raise Refusal("SELECTION", "The selection is not a " + CONFIG_SCHEMA + " configuration")
    descriptor = config.get("host")
    if type(descriptor) is not dict or set(descriptor) != {"path", "sha256", "size_bytes", "mode"}:
        raise Refusal("SELECTION", "The configuration's HOST descriptor is malformed")
    raw, host_binding = read_regular(canonical_path(descriptor["path"], rule="HOST"), 8 * 1024 * 1024, rule="HOST")
    if host_binding != {key: descriptor[key] for key in ("sha256", "size_bytes", "mode")}:
        raise Refusal("HOST", "HOST differs from the configuration's descriptor", path=descriptor["path"])
    host = strict_json(raw, rule="HOST", what="HOST")
    python = host.get("python") if type(host) is dict and host.get("schema") == HOST_SCHEMA else None
    interpreter = python.get("interpreter") if type(python) is dict else None
    if type(interpreter) is not dict:
        raise Refusal("HOST", "HOST is not a " + HOST_SCHEMA + " document with a Python interpreter record")
    image = process_image()
    checks = {
        "executable_is_host_launcher": sys.executable == python.get("launcher"),
        "launcher_is_venv_bin_python": type(python.get("venv")) is str
        and python.get("launcher") == python["venv"] + "/bin/python",
        "implementation": interpreter.get("implementation") == sys.implementation.name,
        "version": interpreter.get("version") == platform.python_version(),
        "build_string": interpreter.get("build_string") == sys.version,
        "process_image": interpreter.get("process_image") == image}
    if not all(checks.values()):
        raise Refusal("PROVIDER-PRECONDITION", "The 0.2.0 provider would refuse this unit process (_check_python)",
                      checks=checks)
    methods = config.get("methods")
    if type(methods) is not dict or set(methods) != {"path", "sha256", "size_bytes", "mode"}:
        raise Refusal("SELECTION", "The configuration's methods descriptor is malformed")
    raw, methods_binding = read_regular(canonical_path(methods["path"], rule="SELECTION"), 1024 * 1024,
                                        rule="SELECTION")
    if methods_binding != {key: methods[key] for key in ("sha256", "size_bytes", "mode")}:
        raise Refusal("SELECTION", "The methods document differs from the configuration's descriptor")
    document = strict_json(raw, rule="SELECTION", what="methods document")
    bodies = document.get("original_bodies") if type(document) is dict and document.get("schema") == METHODS_SCHEMA \
        else None
    if type(bodies) is not dict or not all(type(k) is str and type(v) is str for k, v in bodies.items()):
        raise Refusal("SELECTION", "The methods document holds no original_bodies map")
    return {"configuration": {"path": path, **config_binding}, "host": {"path": descriptor["path"], **host_binding},
            "methods": {"path": methods["path"], **methods_binding}, "original_bodies": bodies,
            "launcher": python["launcher"], "venv": python["venv"], "process_image": image,
            "venv_is_root_venv": None, "checks": checks}


# ---------------------------------------------------------------------------
# Source identity of the cohort's methods (the P07 section 6 alias join)
# ---------------------------------------------------------------------------

def body_identities(raw, path):
    """Per Class.function: the def line and the SHA-256 of the AST dump of its body, as ORIGINAL_BODIES is computed."""
    tree = ast.parse(raw, filename=path)
    rows = {}
    for group in tree.body:
        if isinstance(group, ast.ClassDef):
            for node in group.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    dump = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
                    rows[group.name + "." + node.name] = {
                        "line": node.lineno, "decorators": len(node.decorator_list),
                        "body_sha256": hashlib.sha256(dump.encode()).hexdigest()}
    return rows


def method_identity(test, module_path, bodies):
    """The loaded test method tied to its parsed source: file, class, method, first line and body digest."""
    cls = type(test)
    name = getattr(test, "_testMethodName", None)
    function = getattr(getattr(cls, name, None), "__func__", getattr(cls, name, None)) if name else None
    code = getattr(function, "__code__", None)
    key = cls.__name__ + "." + str(name)
    body = bodies.get(key)
    checks = {
        "class_module": cls.__module__ == COHORT_MODULE,
        "code_file": code is not None and os.path.realpath(code.co_filename) == module_path,
        "parsed": body is not None,
        "first_line": body is not None and code is not None and body["decorators"] == 0
        and code.co_firstlineno == body["line"]}
    return {"key": key, "checks": checks, "joined": all(checks.values()),
            "body_sha256": body["body_sha256"] if body else None}


# ---------------------------------------------------------------------------
# The recording result
# ---------------------------------------------------------------------------

def flatten(suite):
    import unittest
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def make_recorder(journal):
    import unittest

    class Recorder(unittest.TextTestResult):
        """unittest's TextTestResult; each method records, then calls the original unchanged."""

        instances = []

        def __init__(self, stream, descriptions, verbosity, *, durations=None):
            super().__init__(stream, descriptions, verbosity, durations=durations)
            self.mh_events = []
            Recorder.instances.append(self)

        def _mh(self, kind, test, **fields):
            try:
                identifier = test.id()
            except BaseException as exc:
                identifier = "<id unavailable: %s>" % type(exc).__name__
            row = {"sequence": len(self.mh_events) + 1, "kind": kind, "test": identifier,
                   "class_level": not isinstance(test, unittest.TestCase),
                   "monotonic": time.monotonic(), "utc": utc_now(), **fields}
            self.mh_events.append(row)
            journal.append(row)

        def _trace(self, err, test):
            try:
                return text_of(self._exc_info_to_string(err, test), TEXT_LIMIT)
            except BaseException as exc:
                return "<traceback unavailable: %s>" % type(exc).__name__

        def startTestRun(self):
            self._mh_run = time.monotonic()
            journal.append({"kind": "start_run", "monotonic": self._mh_run, "utc": utc_now()})
            super().startTestRun()

        def stopTestRun(self):
            super().stopTestRun()
            journal.append({"kind": "stop_run", "monotonic": time.monotonic(), "utc": utc_now()})

        def startTest(self, test):
            self._mh("start", test, perf_counter=time.perf_counter())
            super().startTest(test)

        def stopTest(self, test):
            super().stopTest(test)
            self._mh("stop", test, perf_counter=time.perf_counter())

        def addSuccess(self, test):
            self._mh("pass", test)
            super().addSuccess(test)

        def addFailure(self, test, err):
            self._mh("failure", test, exception_type=getattr(err[0], "__name__", None), traceback=self._trace(err, test))
            super().addFailure(test, err)

        def addError(self, test, err):
            self._mh("error", test, exception_type=getattr(err[0], "__name__", None), traceback=self._trace(err, test))
            super().addError(test, err)

        def addSkip(self, test, reason):
            parent = getattr(test, "test_case", None)
            if isinstance(test, unittest.case._SubTest) and parent is not None:
                # TR-09: a skip raised inside a subTest arrives under the subtest; it is the parent's event.
                self._mh("subtest_skip", parent, subtest=text_of(str(test), TEXT_LIMIT),
                         reason=text_of(reason, TEXT_LIMIT))
            else:
                self._mh("skip", test, reason=text_of(reason, TEXT_LIMIT))
            super().addSkip(test, reason)

        def addExpectedFailure(self, test, err):
            self._mh("expected_failure", test, exception_type=getattr(err[0], "__name__", None),
                     traceback=self._trace(err, test))
            super().addExpectedFailure(test, err)

        def addUnexpectedSuccess(self, test):
            self._mh("unexpected_success", test)
            super().addUnexpectedSuccess(test)

        def addSubTest(self, test, subtest, err):
            if err is None:
                self._mh("subtest_pass", test, subtest=text_of(str(subtest), TEXT_LIMIT))
            else:
                kind = "subtest_failure" if issubclass(err[0], test.failureException) else "subtest_error"
                self._mh(kind, test, subtest=text_of(str(subtest), TEXT_LIMIT),
                         exception_type=getattr(err[0], "__name__", None), traceback=self._trace(err, subtest))
            super().addSubTest(test, subtest, err)

        def addDuration(self, test, elapsed):
            self._mh("duration", test, elapsed_s=elapsed)
            parent = getattr(super(), "addDuration", None)
            if parent is not None:
                parent(test, elapsed)

    return Recorder


def outcome_of(events):
    kinds = [row["kind"] for row in events]
    if "start" not in kinds:
        return "not_run"
    for kind, outcome in (("error", "error"), ("subtest_error", "error"), ("failure", "fail"),
                          ("subtest_failure", "fail"), ("unexpected_success", "unexpected_success"),
                          ("expected_failure", "expected_failure"), ("skip", "skip"), ("subtest_skip", "skip"),
                          ("pass", "pass")):
        if kind in kinds:
            return outcome
    return "interrupted" if "stop" not in kinds else "unknown"


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

def run(args):
    started, monotonic = utc_now(), time.monotonic()
    root = canonical_path(args.root, kind="dir", rule="ROOT")
    output = create_output_directory(args.output_dir)
    record = {"schema": SCHEMA, "mode": args.command, "tool": tool_record(), "invocation": invocation_record(),
              "started_at_utc": started, "root": root, "state": "UNKNOWN"}
    try:
        flags = check_flags()
        frozen, environment_binding = load_environment(args.environment, args.environment_sha256)
        if args.command == "cohort":
            names, target_file = [COHORT_MODULE], COHORT_FILE
            check_unit_environment_rules(frozen, root)
        else:
            names, target_file = list(args.test), CONTROL_FILE
            for name in names:
                if re.fullmatch(re.escape(CONTROL_MODULE) + r"\.[A-Za-z_][A-Za-z0-9_]*\.test[A-Za-z0-9_]*", name) is None:
                    raise Refusal("TARGET", "A control is named as " + CONTROL_MODULE + ".<Class>.<test method>",
                                  name=name)
            if len(set(names)) != len(names):
                raise Refusal("TARGET", "A control is named twice")
            if CONFIG_ENV in frozen or DIGEST_ENV in frozen:
                raise Refusal("SELECTION", "A control rerun runs without a readback selection")
        cf_value = compare_environment(os.environ, frozen)
        module_path = canonical_path(root + "/" + target_file, kind="file", rule="TARGET")
        module_raw, module_binding = read_regular(module_path, 16 * 1024 * 1024, rule="TARGET")
        if module_binding["sha256"] != args.module_sha256:
            raise Refusal("TARGET", "The target module differs from its supplied SHA-256", path=module_path)
        selection = check_selection_and_host(frozen) if args.command == "cohort" else None
        if selection is not None:
            selection["venv_is_root_venv"] = selection["venv"] == root + "/.venv"
        own = os.path.realpath(__file__)
        preloaded = sorted(name for name, module in sys.modules.items()
                           if type(getattr(module, "__file__", None)) is str
                           and os.path.realpath(module.__file__).startswith(root + "/")
                           and not (name == "__main__" and os.path.realpath(module.__file__) == own))
        if preloaded:
            raise Refusal("PYTHON", "A module of the root is already loaded", modules=preloaded)
        main_file = getattr(sys.modules.get("__main__"), "__file__", None)
        record["own_main_admitted"] = ({"module": "__main__", "path": own, "admitted": True,
                                        "reason": "the running tool itself, identified by realpath equality with "
                                                  "its own file"}
                                       if own.startswith(root + "/") and type(main_file) is str
                                       and os.path.realpath(main_file) == own else None)
    except Refusal as exc:
        record.update(state="REFUSED", refusal=exc.as_dict(), finished_at_utc=utc_now(),
                      elapsed_s=time.monotonic() - monotonic)
        write_new(output + "/outcomes.json", json_text(record))
        sys.stderr.write("MH-OUTCOMES " + json.dumps({"state": "REFUSED", "refusal": exc.as_dict()}, sort_keys=True) + "\n")
        return EXIT_REFUSED
    record.update(flags=flags, environment={"frozen": environment_binding, "names": sorted(frozen),
                                            "admitted_cf_user_text_encoding": cf_value},
                  targets=names, module={"path": module_path, **module_binding}, selection=selection)
    bodies = body_identities(module_raw, module_path) if args.command == "cohort" else None
    journal = Journal(output + "/journal.jsonl")
    audit = ProcessAudit(block=False)
    sys.addaudithook(audit)
    own = os.path.dirname(os.path.realpath(__file__))
    record["sys_path_before"] = list(sys.path)
    os.chdir(root)
    # python -m unittest from the root: the root is the working directory and sys.path[0]; the tool's
    # own directory leaves the path.
    sys.path[:] = [root] + [item for item in sys.path[1:] if os.path.realpath(item or ".") != own]
    record["sys_path_at_load"] = list(sys.path)
    import unittest
    loader = unittest.TestLoader()
    recorder = make_recorder(journal)
    interrupted = None
    planned, result = [], None
    try:
        suite = loader.loadTestsFromNames(names)
        planned = list(flatten(suite))
        record["loader_errors"] = [text_of(item, TEXT_LIMIT) for item in loader.errors]
        journal.append({"kind": "planned", "tests": [test.id() for test in planned], "utc": utc_now()})
        runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2,
                                         warnings=None if sys.warnoptions else "default", resultclass=recorder)
        result = runner.run(suite)
    except BaseException as exc:  # KeyboardInterrupt, or a failure of the loader or runner itself
        interrupted = {"type": type(exc).__name__, "reason": text_of(str(exc), TEXT_LIMIT)}
        journal.append({"kind": "interrupted", "error": interrupted, "utc": utc_now()})
    finally:
        audit.enabled = False
    # The recording result exists even when the runner never returned (an interruption).
    events = [row for instance in recorder.instances for row in instance.mh_events]
    if len(recorder.instances) > 1:
        interrupted = interrupted or {"type": "RecorderError", "reason": "More than one result object was made"}
    by_test = {}
    for row in events:
        by_test.setdefault(row["test"], []).append(row)
    tests = []
    failed_type = getattr(unittest.loader, "_FailedTest", None)
    for test in planned:
        raw = test.id()
        rows = [row for row in by_test.get(raw, []) if not row["class_level"]]
        starts = [row for row in rows if row["kind"] == "start"]
        stops = [row for row in rows if row["kind"] == "stop"]
        outcome = outcome_of(rows)
        if interrupted is not None and outcome == "unknown":
            outcome = "interrupted"  # unittest stopped the test without an outcome because the run was interrupted
        entry = {"raw_id": raw, "outcome": outcome,
                 "import_failure": bool(failed_type is not None and isinstance(test, failed_type)),
                 "events": [{key: value for key, value in row.items() if key != "test"} for row in rows
                            if row["kind"] not in ("start", "stop", "duration")],
                 "started_at_utc": starts[0]["utc"] if starts else None,
                 "stopped_at_utc": stops[-1]["utc"] if stops else None,
                 "elapsed_s": (stops[-1]["perf_counter"] - starts[0]["perf_counter"]) if starts and stops else None,
                 "duration_s": next((row["elapsed_s"] for row in rows if row["kind"] == "duration"), None),
                 "alias_id": None}
        if args.command == "cohort" and isinstance(test, unittest.TestCase) and raw.startswith(PACKAGE_PREFIX):
            identity = method_identity(test, module_path, bodies)
            entry["identity"] = identity
            if identity["joined"]:
                entry["alias_id"] = DISCOVERY_PREFIX + raw[len(PACKAGE_PREFIX):]
        tests.append(entry)
    class_level = [{key: value for key, value in row.items()} for row in events if row["class_level"]]
    planned_ids = {test.id() for test in planned}
    unplanned = [dict(row) for row in events if not row["class_level"] and row["test"] not in planned_ids]
    after_raw, after_binding = read_regular(module_path, 16 * 1024 * 1024, rule="TARGET")
    record.update(tests=tests, class_level_events=class_level, unplanned_events=unplanned, interrupted=interrupted,
                  process_events=audit.events, journal={"path": output + "/journal.jsonl", "lines": journal.lines,
                                                        "failure": journal.failure},
                  module_after={"path": module_path, **after_binding},
                  module_unchanged=after_binding == module_binding,
                  loaded_project_files=loaded_project_files(root))
    if bodies is not None:
        record["source_bodies"] = bodies
        frozen_bodies = selection["original_bodies"]
        record["original_bodies"] = {
            name: {"frozen": digest, "source": (bodies.get(name) or {}).get("body_sha256"),
                   "equal": (bodies.get(name) or {}).get("body_sha256") == digest}
            for name, digest in sorted(frozen_bodies.items())}
        aliases = {row["alias_id"]: row for row in tests if row["alias_id"]}
        record["required_methods"] = [
            {"id": DISCOVERY_PREFIX + name, "outcome": aliases[DISCOVERY_PREFIX + name]["outcome"]
             if DISCOVERY_PREFIX + name in aliases else "missing"} for name in REQUIRED_METHODS]
    counted = result if result is not None else (recorder.instances[0] if recorder.instances else None)
    if counted is not None:
        record["unittest"] = {"runner_returned": result is not None, "tests_run": counted.testsRun,
                              "failures": len(counted.failures), "errors": len(counted.errors),
                              "skipped": len(counted.skipped), "expected_failures": len(counted.expectedFailures),
                              "unexpected_successes": len(counted.unexpectedSuccesses),
                              "was_successful": counted.wasSuccessful(),
                              "exit_status_of_unittest_main": 5 if counted.testsRun == 0 and not counted.skipped
                              else 0 if counted.wasSuccessful() else 1}
    counts = {}
    for row in tests:
        counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
    record["outcome_counts"] = dict(sorted(counts.items()))
    bytecode = sorted(row["path"] for row in record["loaded_project_files"] if row["bytecode_present"])
    record["bytecode_present"] = bytecode
    complete = interrupted is None and result is not None and journal.failure is None and record["module_unchanged"]
    all_passed = (complete and tests and all(row["outcome"] == "pass" for row in tests) and not class_level
                  and not unplanned and not record.get("loader_errors") and not bytecode
                  and all(row["equal"] for row in record.get("original_bodies", {}).values())
                  and all(row["outcome"] == "pass" for row in record.get("required_methods", [])))
    record.update(state=("ALL_PASSED" if all_passed else "COMPLETED_WITH_OTHER_OUTCOMES") if complete else "UNKNOWN",
                  finished_at_utc=utc_now(), elapsed_s=time.monotonic() - monotonic)
    journal.close()
    write_new(output + "/outcomes.json", json_text(record))
    sys.stderr.write("MH-OUTCOMES " + json.dumps({"state": record["state"], "outcome_counts": record["outcome_counts"],
                                                  "class_level_events": len(class_level),
                                                  "process_events": len(audit.events)}, sort_keys=True) + "\n")
    if not complete:
        return EXIT_UNKNOWN
    return EXIT_ALL_PASSED if all_passed else EXIT_OTHER_OUTCOMES


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def main(argv=None):
    parser = _Parser(prog="collect_outcomes.py", allow_abbrev=False, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("cohort", "controls"):
        sub = commands.add_parser(name)
        sub.add_argument("--root", required=True)
        sub.add_argument("--environment", required=True)
        sub.add_argument("--environment-sha256", required=True)
        sub.add_argument("--module-sha256", required=True)
        sub.add_argument("--output-dir", required=True)
        if name == "controls":
            sub.add_argument("--test", action="append", required=True)
    try:
        args = parser.parse_args(argv)
        if re.fullmatch(r"[0-9a-f]{64}", args.module_sha256) is None:
            raise Refusal("USAGE", "--module-sha256 must be a lowercase SHA-256")
        return run(args)
    except Refusal as exc:
        sys.stderr.write(json.dumps({"schema": "ontokin.c271.p35-tool-refusal/1", "tool": "collect_outcomes.py",
                                     "state": "REFUSED", "refusal": exc.as_dict()}, sort_keys=True) + "\n")
        return EXIT_REFUSED
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        sys.stderr.write(json.dumps({"schema": "ontokin.c271.p35-tool-failure/1", "tool": "collect_outcomes.py",
                                     "state": "UNKNOWN", "error": {"type": type(exc).__name__, "reason": str(exc)}},
                                    sort_keys=True) + "\n")
        return EXIT_UNKNOWN


if __name__ == "__main__":
    raise SystemExit(main())
