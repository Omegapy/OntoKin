#!/usr/bin/env python3
"""Control harness for gate MH of C271-P35: reruns for MI's findings F-01, F-03 and F-04.

Three commands; each writes one absent output file and substitutes only what it states.

  mc10        F-01. The observer's real observe_host on a frozen observation plan, with M0's real
              static bindings (the real plan, environment, platform, OS identity, source, Python
              installation, packages, runtime with its Mach-O rules, reader tree, Git binding,
              failure-capture binding and evidence ancestors). Substituted: the command boundary,
              which answers the frozen Git and Node --version output without starting a process,
              and so the host boundary is labelled mocked; and, in the observer's loaded-module
              listing, the one row of this harness's own file, which the plan binds by SHA-256
              instead. Every process creation is refused, so zero processes start.
              Launch exactly as M0 is launched: env -i <declared environment> <venv>/bin/python -I -S -B.

  mc29        F-03. The 0.2.0 provider with its real detectors: a real cohort setup through the
              facade, one attempt on Q01-positive, and the cohort accounting, with one real change
              made immediately after the provider writes the attempt's preflight.json: the
              configuration gains one byte, or the stage's synthetic.glb gains one byte.
              Substituted: supervisor_darwin_v01.run_process, by a recorder that refuses to start
              anything, so the provider labels its records mocked; and the provider's _write_new, by
              a wrapper that calls the original and then makes the change once. The provider's
              source, HOST, runtime, dependency, method, selection, job and host_state checks are its
              own. Launch as the unit process, under the frozen environment given with --environment,
              which the harness requires exactly (HOME is never part of it; TR-06):
              env -i <frozen environment> <venv>/bin/python -B.

  host-state  F-04. The provider's real host_state (kern.bootsessionuuid, sysctl.proc_translated,
              os.uname and both SystemVersion.plist copies) compared with HOST through the
              provider's own _check_state. Nothing is substituted, and every process creation is
              refused.

Every command refuses a start without -B (N-09). The audit hook records process-creation events
and ctypes lookups of libc's process functions; it does not see _posixsubprocess.fork_exec, which
multiprocessing's spawn and forkserver start methods call, nor a call made through ctypes (TR-08).
Records name a child's environment variables and a digest of their values, never the values.

It uses the standard library only and holds no machine path; every path is an argument.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import stat
import sys
import time

SCHEMA = "ontokin.c271.p35-control-harness/2"
ENVIRONMENT_SCHEMA = "ontokin.c271.p35-unit-environment/1"
OBSERVER_REL = "prototypes/static_tray_v01/current_host_observation_v02.py"
OBSERVER_MODULE = "prototypes.static_tray_v01.current_host_observation_v02"
# What the mc10 command loads, from verified bytes, in order.
MC10_FILES = (
    ("prototypes", "prototypes/__init__.py", True),
    ("prototypes.static_tray_v01", "prototypes/static_tray_v01/__init__.py", True),
    ("prototypes.static_tray_v01.supervisor", "prototypes/static_tray_v01/supervisor.py", False),
    (OBSERVER_MODULE, OBSERVER_REL, False))
DECLARED_ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
                        "UV_THREADPOOL_SIZE": "2"}
CF_NAME = "__CF_USER_TEXT_ENCODING"
CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
CONFIG_SCHEMA = "ontokin.current-host-readback-config/0.2.0"
HOST_SCHEMA = "ontokin.current-host-readback-host/0.2.0"
LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
# A process ID above the kernel's maximum (99999): the command boundary's mock receipts can never name a real process.
SYNTHETIC_PID_BASE = 999990000
STAGE_LABEL, STAGE_CASE, CHECKER_LABEL = "Q01-positive", "Q01", "synthetic-readback"
# The provider's checks that MC29 keeps as its own objects; the harness proves their identity afterwards.
DETECTORS = ("_selection", "_host_git", "_verify_source", "_verify_host", "_cross_bindings", "_verify_dependencies",
             "_verify_methods", "_verify_parent", "_job", "_check_state", "host_state", "_verified_manifest",
             "_check_python", "_check_runtime", "_check_git", "_check_inspections", "_check_host_labels")
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                            "os.system", "os.startfile"))
# ctypes lookups of libc's process-creation functions; a call through them raises no audit event of its own.
CTYPES_PROCESS_SYMBOLS = frozenset(("fork", "vfork", "posix_spawn", "posix_spawnp", "execve", "execv", "execvp",
                                    "execvpe", "execl", "execlp", "execle", "system", "popen"))
SHA = re.compile(r"[0-9a-f]{64}")
EXIT_EXPECTED, EXIT_NOT_EXPECTED, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3


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
    """N-09: every start of the framework interpreter carries -B (TR-17)."""
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
    return (json.dumps(value, sort_keys=True, indent=1, ensure_ascii=True, allow_nan=False, default=repr) + "\n"
            ).encode("ascii")


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


def write_new(path, data, mode=0o644):
    """Exclusive creation of one absent file, fsynced together with its directory."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0), mode)
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


def failure_of(exc):
    if exc is None:
        return None
    row = {"type": type(exc).__name__, "reason": text_of(str(exc), 65536)}
    for name in ("code", "category", "state"):
        if hasattr(exc, name):
            row[name] = text_of(getattr(exc, name))
    if hasattr(exc, "as_dict"):
        try:
            row["as_dict"] = json.loads(json.dumps(exc.as_dict(), default=repr))
        except BaseException:
            row["as_dict"] = "<unavailable>"
    return row


def compare_environment(observed, frozen):
    """Exactly the given mapping; __CF_USER_TEXT_ENCODING, which macOS adds, is admitted and recorded (S10)."""
    observed = dict(observed)
    admitted = observed.pop(CF_NAME, None) if CF_NAME not in frozen else None
    missing, extra = sorted(set(frozen) - set(observed)), sorted(set(observed) - set(frozen))
    differing = sorted(name for name in set(frozen) & set(observed) if frozen[name] != observed[name])
    if missing or extra or differing:
        raise Refusal("ENVIRONMENT", "The process environment is not the expected one (names only)",
                      missing=missing, extra=extra, differing=differing)
    return admitted


def load_environment(path, sha256):
    """A frozen environment document bound by a supplied SHA-256; HOME is never part of one (TR-06)."""
    if type(sha256) is not str or SHA.fullmatch(sha256) is None:
        raise Refusal("ENVIRONMENT", "Expected a lowercase SHA-256 digest for the frozen environment")
    raw, binding = read_regular(canonical_path(path, kind="file", rule="ENVIRONMENT"), 1024 * 1024, rule="ENVIRONMENT")
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


def parse_bindings(values, expected):
    bindings = {}
    for value in values or []:
        rel, sep, digest = value.partition("=")
        if not sep or SHA.fullmatch(digest) is None or rel in bindings:
            raise Refusal("BINDING", "A binding is RELATIVE_PATH=SHA256, given once per file", binding=value)
        bindings[rel] = digest
    if sorted(bindings) != sorted(expected):
        raise Refusal("BINDING", "Exactly these files must be bound", given=sorted(bindings), expected=sorted(expected))
    return bindings


def load_verified(root, files, bindings):
    """Load modules from their verified bytes, in order, as the import system names them; no bytecode is read."""
    import importlib.machinery
    import importlib.util
    already = sorted(name for name, _, _ in files if name in sys.modules)
    if already:
        raise Refusal("BINDING", "A module to be loaded is already loaded", modules=already)
    loaded = []
    for name, rel, package in files:
        path = canonical_path(root + "/" + rel, kind="file", rule="BINDING")
        raw, binding = read_regular(path, 16 * 1024 * 1024, rule="BINDING")
        if binding["sha256"] != bindings[rel]:
            raise Refusal("BINDING", "A file differs from its supplied SHA-256", path=path, observed=binding["sha256"])
        try:
            code = compile(raw, path, "exec", dont_inherit=True)
        except SyntaxError as exc:
            raise Refusal("BINDING", "A bound file does not compile", path=path, error=str(exc)) from exc
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
            raise Refusal("BINDING", "A bound file failed while it was loaded", path=path,
                          error=type(exc).__name__ + ": " + str(exc)) from exc
        loaded.append({"module": name, "path": path, **binding, "compiled_from_verified_bytes": True})
    return loaded


def process_image():
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


def read_selection(config_path, config_sha256):
    """The configuration by its supplied digest, and the HOST it binds; the provider's launcher rules for this process."""
    import platform
    raw, config_binding = read_regular(canonical_path(config_path, kind="file", rule="SELECTION"), 1024 * 1024,
                                       rule="SELECTION")
    if config_binding["sha256"] != config_sha256:
        raise Refusal("SELECTION", "The configuration differs from its supplied SHA-256", path=config_path)
    config = strict_json(raw, rule="SELECTION", what="configuration")
    descriptor = config.get("host") if type(config) is dict and config.get("schema") == CONFIG_SCHEMA else None
    if type(descriptor) is not dict or set(descriptor) != {"path", "sha256", "size_bytes", "mode"}:
        raise Refusal("SELECTION", "The selection is not a " + CONFIG_SCHEMA + " configuration with a HOST descriptor")
    raw, host_binding = read_regular(canonical_path(descriptor["path"], kind="file", rule="HOST"), 8 * 1024 * 1024,
                                     rule="HOST")
    if host_binding != {key: descriptor[key] for key in ("sha256", "size_bytes", "mode")}:
        raise Refusal("HOST", "HOST differs from the configuration's descriptor")
    host = strict_json(raw, rule="HOST", what="HOST")
    python = host.get("python") if type(host) is dict and host.get("schema") == HOST_SCHEMA else None
    interpreter = python.get("interpreter") if type(python) is dict else None
    if type(interpreter) is not dict:
        raise Refusal("HOST", "HOST has no Python interpreter record")
    checks = {"executable_is_host_launcher": sys.executable == python.get("launcher"),
              "launcher_is_venv_bin_python": type(python.get("venv")) is str
              and python.get("launcher") == python["venv"] + "/bin/python",
              "implementation": interpreter.get("implementation") == sys.implementation.name,
              "version": interpreter.get("version") == platform.python_version(),
              "build_string": interpreter.get("build_string") == sys.version,
              "process_image": interpreter.get("process_image") == process_image()}
    if not all(checks.values()):
        raise Refusal("PROVIDER-PRECONDITION", "The 0.2.0 provider would refuse this process (_check_python)",
                      checks=checks)
    return config, {"configuration": {"path": config_path, **config_binding},
                    "host": {"path": descriptor["path"], **host_binding}, "launcher_checks": checks}


def use_root_imports(root):
    """The root as sys.path[0] and the working directory, as the unit process imports; the tool's directory leaves."""
    own = os.path.dirname(os.path.realpath(__file__))
    os.chdir(root)
    sys.path[:] = [root] + [item for item in sys.path[1:] if os.path.realpath(item or ".") != own]
    return list(sys.path)


# ---------------------------------------------------------------------------
# mc10: real static bindings, the command boundary simulated
# ---------------------------------------------------------------------------

class CommandBoundary:
    """The M0/M1 command boundary, simulated: each label answers its frozen stdout; nothing starts.

    It writes the supervisor's own three files in the stage and returns the original 14-field receipt,
    with a process ID that no real process can have.
    """

    def __init__(self, base, outputs):
        self.Clock, self.Stop, self.json_bytes = base.Clock, base.Stop, base.json_bytes
        self.outputs, self.calls = outputs, []

    def run_process(self, argv, *, stage, label, clock, stage_end, env=None, on_started=None, cancel_after_ms=None):
        stage = os.path.realpath(stage)
        self.calls.append({"label": label, "argv": list(argv), "stage": stage, "utc": utc_now()})
        stdout = self.outputs[label]
        pid = SYNTHETIC_PID_BASE + len(self.calls)
        record = {"argv": argv, "cwd": stage, "environment": env, "label": label,
                  "start_monotonic": time.monotonic(), "pid": pid, "process_group": pid, "returncode": None,
                  "observed_log_bytes": 0, "retained_log_bytes": 0, "cleanup": None, "handles_closed": False,
                  "error": None}
        if on_started is not None:
            on_started(dict(record))
        write_new(stage + "/" + label + ".stdout.log", stdout, 0o666)
        write_new(stage + "/" + label + ".stderr.log", b"", 0o666)
        final = dict(record, returncode=0, observed_log_bytes=len(stdout), retained_log_bytes=len(stdout),
                     cleanup={"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 0.0},
                     handles_closed=True, end_monotonic=time.monotonic())
        write_new(stage + "/" + label + ".process.json", self.json_bytes(final), 0o666)
        return final


def attempt_listing(path):
    """Every entry of the attempt directory, links never followed (TR-13): files with their digests."""
    if os.path.islink(path) or not os.path.isdir(path):
        return None
    rows = {}
    for parent, directories, names in os.walk(path, followlinks=False):
        for name in sorted(directories + names):
            full = os.path.join(parent, name)
            rel = os.path.relpath(full, path)
            info = os.lstat(full)
            if stat.S_ISLNK(info.st_mode):
                rows[rel] = {"kind": "symlink", "target": os.readlink(full)}
            elif stat.S_ISREG(info.st_mode):
                try:
                    _, binding = read_regular(full, 64 * 1024 * 1024, rule="ATTEMPT")
                    rows[rel] = {"kind": "file", **binding}
                except Refusal as exc:
                    rows[rel] = {"kind": "file", "refusal": exc.as_dict()}
            elif not stat.S_ISDIR(info.st_mode):
                rows[rel] = {"kind": "special"}
    return rows


def mc10(args, record):
    flags = sys.flags
    if not (flags.isolated and flags.no_site and flags.dont_write_bytecode and flags.ignore_environment
            and flags.no_user_site and flags.safe_path) or "site" in sys.modules:
        raise Refusal("PYTHON", "Run as M0 runs: -I -S -B, without site")
    record["admitted_cf_user_text_encoding"] = compare_environment(os.environ, DECLARED_ENVIRONMENT)
    root = canonical_path(args.root, kind="dir", rule="ROOT")
    if SHA.fullmatch(args.plan_sha256 or "") is None:
        raise Refusal("PLAN", "Expected a lowercase SHA-256 for the plan")
    canonical_path(args.plan, kind="file", rule="PLAN")
    try:
        git_stdout, node_stdout = bytes.fromhex(args.git_stdout_hex), bytes.fromhex(args.node_stdout_hex)
    except ValueError as exc:
        raise Refusal("USAGE", "The simulated outputs are given in hexadecimal", error=str(exc)) from exc
    bindings = parse_bindings(args.bind, [rel for _, rel, _ in MC10_FILES])
    audit = ProcessAudit(block=True)
    sys.addaudithook(audit)
    loaded = load_verified(root, MC10_FILES, bindings)
    observation, base = sys.modules[OBSERVER_MODULE], sys.modules["prototypes.static_tray_v01.supervisor"]
    boundary = CommandBoundary(base, {observation.LABELS["git_version"]: git_stdout,
                                      observation.LABELS["node_version"]: node_stdout})
    own = os.path.realpath(__file__)

    class CommandBoundaryHost(observation.Host):
        """The real host readers, except the command boundary and this harness's own loaded-module row."""
        boundary = "mocked"
        excluded = []

        def supervisor(self, source_root, inventory):
            return boundary

        def loaded_modules(self):
            rows = []
            for row in observation.loaded_module_files():
                if row["name"] == "__main__" and os.path.realpath(row["file"]) == own:
                    CommandBoundaryHost.excluded.append(row)
                    continue
                rows.append(row)
            return rows
    host = CommandBoundaryHost()
    record.update(root=root, loaded_project_files=loaded,
                  substituted=["the M0/M1 command boundary (Host.supervisor returns CommandBoundary; no start)",
                               "the observer's loaded-module listing, without this harness's own __main__ row"],
                  simulated_outputs={"git_version_hex": args.git_stdout_hex, "node_version_hex": args.node_stdout_hex})
    result, error = None, None
    try:
        result = observation.observe_host(args.plan, args.plan_sha256, host=host)
    except observation.ObservationError as exc:
        error = exc
    except BaseException as exc:
        record["unexpected_failure"] = failure_of(exc)
        raise
    finally:
        audit.enabled = False
    plan = json.loads(read_regular(args.plan, 16 * 1024 * 1024)[0])
    attempt = plan.get("evidence", {}).get("attempt") if type(plan) is dict else None
    listing = attempt_listing(attempt) if type(attempt) is str else None
    outcome = error.result if error is not None else result
    record.update(
        observation_result=json.loads(json.dumps(outcome, default=repr)) if outcome is not None else None,
        observation_error=failure_of(error), boundary_calls=boundary.calls,
        excluded_loaded_module_rows=CommandBoundaryHost.excluded, attempt=attempt, attempt_files=listing,
        process_events=audit.events)
    labels = observation.LABELS
    common = {"zero_process_starts": not audit.events,
              "both_commands_reached_the_boundary": [row["label"] for row in boundary.calls]
              == [labels["git_version"], labels["node_version"]],
              "only_the_harness_row_excluded": len(CommandBoundaryHost.excluded) >= 1
              and all(row["name"] == "__main__" for row in CommandBoundaryHost.excluded),
              "labelled_mocked": type(outcome) is dict and (outcome.get("labels") or {}).get("boundary") == "mocked"}
    if args.expect == "refused-output":
        checks = dict(common, refused_with_output=error is not None and error.category == "OUTPUT",
                      no_host=type(outcome) is dict and outcome.get("host") is None,
                      not_observed=type(outcome) is dict and outcome.get("state") != "OBSERVED_UNAPPROVED",
                      not_finalized=type(outcome) is dict and outcome.get("evidence_finalized") is False,
                      no_host_or_completion_file=listing is not None and "HOST.json" not in listing
                      and "completion.json" not in listing)
    else:
        host_file = (attempt + "/HOST.json") if type(attempt) is str else None
        written = json.loads(read_regular(host_file, 8 * 1024 * 1024)[0]) if host_file and os.path.isfile(host_file) else {}
        checks = dict(common, accepted=error is None and type(result) is dict
                      and result.get("state") == "OBSERVED_UNAPPROVED",
                      host_labelled_mocked=(written.get("labels") or {}).get("boundary") == "mocked",
                      host_runtime_version=(written.get("runtime") or {}).get("version") == "v24.22.1")
    return checks


# ---------------------------------------------------------------------------
# mc29: the real detectors, one real change after preflight
# ---------------------------------------------------------------------------

class SupervisorRecorder:
    """Stands for supervisor_darwin_v01.run_process: records the call and starts nothing."""

    def __init__(self):
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "stage": str(kwargs.get("stage")), "label": kwargs.get("label"),
                           "utc": utc_now()})
        raise RuntimeError("MC29 harness: the supervisor was reached; nothing is started")


def canonical_job_bytes(value):
    """prototypes.static_tray_v01.supervisor.json_bytes, as check_case writes job.json."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def mc29(args, record):
    from pathlib import Path
    from unittest import mock
    if not sys.flags.dont_write_bytecode or sys.flags.isolated or sys.flags.no_site or sys.flags.safe_path:
        raise Refusal("PYTHON", "Run as the unit process runs: -B only")
    root = canonical_path(args.root, kind="dir", rule="ROOT")
    for name, value in (("--config-sha256", args.config_sha256), ("--glb-sha256", args.glb_sha256),
                        ("--audit-sha256", args.audit_sha256)):
        if SHA.fullmatch(value or "") is None:
            raise Refusal("USAGE", name + " must be a lowercase SHA-256")
    frozen, environment_binding = load_environment(args.environment, args.environment_sha256)
    admitted = compare_environment(os.environ, frozen)
    if frozen.get(CONFIG_ENV) != args.config or frozen.get(DIGEST_ENV) != args.config_sha256:
        raise Refusal("SELECTION", "The frozen selection must be the configuration and digest given as arguments")
    config, selection = read_selection(args.config, args.config_sha256)
    glb, glb_binding = read_regular(canonical_path(args.glb, kind="file", rule="INPUT"), 8 * 1024 * 1024)
    audit_bytes, audit_binding = read_regular(canonical_path(args.audit, kind="file", rule="INPUT"), 4 * 1024 * 1024)
    if glb_binding["sha256"] != args.glb_sha256 or audit_binding["sha256"] != args.audit_sha256:
        raise Refusal("INPUT", "A stage input differs from its supplied SHA-256")
    record.update(root=root, selection=selection, stage_inputs={"glb": {"path": args.glb, **glb_binding},
                                                                "audit": {"path": args.audit, **audit_binding}},
                  environment={"frozen": environment_binding, "names": sorted(frozen),
                               "admitted_cf_user_text_encoding": admitted}, change=args.change)
    audit = ProcessAudit(block=False)
    sys.addaudithook(audit)
    record["sys_path_at_import"] = use_root_imports(root)
    import prototypes.static_tray_v01.current_host_readback_v01 as facade
    import prototypes.static_tray_v01.current_host_readback_v02 as provider
    import prototypes.static_tray_v01.supervisor as base
    import prototypes.static_tray_v01.supervisor_darwin_v01 as darwin
    import types

    def providers_own(name):
        """A plain function of the provider's own file, under its own name: never a stand-in."""
        value = getattr(provider, name, None)
        code = getattr(value, "__code__", None)
        return (type(value) is types.FunctionType and code is not None and value.__qualname__ == name
                and value.__module__ == provider.__name__
                and os.path.realpath(code.co_filename) == os.path.realpath(provider.__file__))
    record["detectors_own_before"] = {name: providers_own(name) for name in DETECTORS}
    record["boundary_before"] = provider._boundary()
    recorder = SupervisorRecorder()
    real_write = provider._write_new
    changes = []
    stage = {"path": None}

    def apply_change():
        if args.change == "configuration":
            with open(args.config, "ab") as stream:
                stream.write(b" ")
                stream.flush()
                os.fsync(stream.fileno())
        else:
            with open(stage["path"] + "/synthetic.glb", "ab") as stream:
                stream.write(b"\0")
                stream.flush()
                os.fsync(stream.fileno())
        changes.append({"change": args.change, "utc": utc_now()})

    def after_preflight(path, value):
        written = real_write(path, value)
        target = Path(path)
        if not changes and stage["path"] is not None and target.name == "preflight.json" \
                and target.parent.name == STAGE_LABEL:
            apply_change()
        return written

    class Cohort:
        """Stands for the readback CPU class: the facade's class seams take a class object."""
    errors = (facade.CurrentHostBindingError, provider.CurrentHostBindingError)
    setup_error = attempt_error = finish_error = None
    started, ledger = [], None
    try:
        with mock.patch.object(darwin, "run_process", recorder), mock.patch.object(provider, "_write_new", after_preflight):
            record["boundary_during"] = provider._boundary()
            try:
                facade.setup_cpu_cohort(Cohort)
            except BaseException as exc:
                setup_error = exc
            if setup_error is None:
                stage["path"] = str(Path(Cohort.root) / STAGE_LABEL)
                os.mkdir(stage["path"])
                write_new(stage["path"] + "/synthetic.glb", glb)
                write_new(stage["path"] + "/synthetic-audit.json", audit_bytes)
                job = {"slot": "CPU-" + STAGE_LABEL, "case": STAGE_CASE, "manifest": str(Cohort.manifest_path),
                       "supplemental_manifest_sha256": Cohort.manifest_hash,
                       "input_lock_sha256": "CPU-ONLY-SYNTHETIC-NOT-NATIVE",
                       "artifact": stage["path"] + "/synthetic.glb", "artifact_sha256": glb_binding["sha256"],
                       "audit": stage["path"] + "/synthetic-audit.json", "audit_sha256": audit_binding["sha256"],
                       "result": stage["path"] + "/probe.json"}
                write_new(stage["path"] + "/job.json", canonical_job_bytes(job))
                argv = Cohort.manifest["slots"][0]["argv"][:-1] + [stage["path"] + "/job.json"]
                clock = base.Clock(total_ms=30000)
                try:
                    facade.guarded_run_process(argv, stage=Path(stage["path"]), label=CHECKER_LABEL, clock=clock,
                                               stage_end=clock.started + 28, env=Cohort.manifest["environment"],
                                               on_started=started.append)
                except BaseException as exc:
                    attempt_error = exc
                ledger_path = Path(Cohort.root) / "provider-ledgers" / STAGE_LABEL / "result.json"
                if ledger_path.is_file():
                    ledger = json.loads(ledger_path.read_bytes())
                try:
                    facade.finish_cpu_cohort(Cohort)
                except BaseException as exc:
                    finish_error = exc
    finally:
        audit.enabled = False
    identity = {name: providers_own(name) and record["detectors_own_before"][name] for name in DETECTORS}
    node = (config.get("runtime") or {}).get("executable")
    node_events = [row for row in audit.events if row.get("executable") == node
                   or (row.get("argv") or [None])[0] == node]
    record.update(
        setup_error=failure_of(setup_error), attempt_error=failure_of(attempt_error), finish_error=failure_of(finish_error),
        refusal_record=json.loads(json.dumps(getattr(attempt_error, "refusal_record", None), default=repr)),
        ledger=ledger, supervisor_calls=recorder.calls, on_started_calls=len(started), changes=changes,
        detectors_are_the_providers_own=identity, boundary_after=provider._boundary(),
        retained_evidence=str(getattr(Cohort, "retained_evidence", None)), cohort_root=str(getattr(Cohort, "root", None)),
        substituted=["supervisor_darwin_v01.run_process (a recorder that starts nothing)",
                     "current_host_readback_v02._write_new (the original, then the change once after preflight.json)"],
        process_events=audit.events, node_process_events=node_events,
        git_process_events=len(audit.events) - len(node_events), loaded_project_files=loaded_project_files(root))
    refusal = getattr(attempt_error, "refusal_record", None) or {}
    checks = {"setup_passed": setup_error is None,
              "change_applied_once": len(changes) == 1,
              "attempt_refused_by_the_provider": isinstance(attempt_error, errors),
              "zero_supervisor_calls": not recorder.calls, "zero_on_started_calls": not started,
              "zero_node_process_events": not node_events,
              "refusal_counts_zero_starts": refusal.get("actual_checker_starts") == 0,
              "ledger_zero_starts_not_completed": type(ledger) is dict and ledger.get("actual_checker_starts") == 0
              and ledger.get("state") != "COMPLETED",
              "ledger_labelled_mocked": type(ledger) is dict and (ledger.get("labels") or {}).get("boundary") == "mocked",
              "accounting_refused": isinstance(finish_error, errors),
              "detectors_are_the_providers_own": all(identity.values())}
    if args.expect_code is not None:
        checks["refusal_code"] = getattr(attempt_error, "code", None) == args.expect_code
    return checks


# ---------------------------------------------------------------------------
# host-state: the provider's real host_state against HOST
# ---------------------------------------------------------------------------

def host_state(args, record):
    if not sys.flags.dont_write_bytecode:
        raise Refusal("PYTHON", "Run with -B")
    root = canonical_path(args.root, kind="dir", rule="ROOT")
    if SHA.fullmatch(args.host_sha256 or "") is None:
        raise Refusal("USAGE", "--host-sha256 must be a lowercase SHA-256")
    raw, binding = read_regular(canonical_path(args.host, kind="file", rule="HOST"), 8 * 1024 * 1024, rule="HOST")
    if binding["sha256"] != args.host_sha256:
        raise Refusal("HOST", "HOST differs from its supplied SHA-256")
    host = strict_json(raw, rule="HOST", what="HOST")
    if type(host) is not dict or host.get("schema") != HOST_SCHEMA:
        raise Refusal("HOST", "Not a " + HOST_SCHEMA + " document")
    audit = ProcessAudit(block=True)
    sys.addaudithook(audit)
    record.update(root=root, host={"path": args.host, **binding}, sys_path_at_import=use_root_imports(root))
    import prototypes.static_tray_v01.current_host_readback_v02 as provider
    before = provider._boundary()
    state, refusal, boot = None, None, None
    try:
        state = provider.host_state()
        boot = provider._check_state({"platform": host["platform"], "os": host["os"]}, state,
                                     "the MH host_state control")
    except provider.CurrentHostBindingError as exc:
        refusal = exc
    finally:
        audit.enabled = False
    record.update(boundary_before=before, boundary_after=provider._boundary(),
                  observed_state=json.loads(json.dumps(state, default=repr)) if state is not None else None,
                  host_platform=host.get("platform"), host_os=host.get("os"), boot_record=boot,
                  refusal=failure_of(refusal), substituted=[], process_events=audit.events,
                  loaded_project_files=loaded_project_files(root))
    return {"boundary_real": before == "real" and record["boundary_after"] == "real",
            "state_equals_host": refusal is None and boot is not None, "zero_process_starts": not audit.events}


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def main(argv=None):
    parser = _Parser(prog="control_harness.py", allow_abbrev=False, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    sub = commands.add_parser("mc10")
    sub.add_argument("--root", required=True)
    sub.add_argument("--plan", required=True)
    sub.add_argument("--plan-sha256", required=True)
    sub.add_argument("--bind", action="append", required=True)
    sub.add_argument("--git-stdout-hex", required=True)
    sub.add_argument("--node-stdout-hex", required=True)
    sub.add_argument("--expect", required=True, choices=("refused-output", "accepted"))
    sub.add_argument("--output", required=True)
    sub = commands.add_parser("mc29")
    sub.add_argument("--root", required=True)
    for name in ("config", "glb", "audit"):
        sub.add_argument("--" + name, required=True)
        sub.add_argument("--" + name + "-sha256", required=True)
    sub.add_argument("--environment", required=True)
    sub.add_argument("--environment-sha256", required=True)
    sub.add_argument("--change", required=True, choices=("configuration", "job-input"))
    sub.add_argument("--expect-code")
    sub.add_argument("--output", required=True)
    sub = commands.add_parser("host-state")
    sub.add_argument("--root", required=True)
    sub.add_argument("--host", required=True)
    sub.add_argument("--host-sha256", required=True)
    sub.add_argument("--output", required=True)
    output, record, started = None, None, time.monotonic()
    try:
        args = parser.parse_args(argv)
        output = prepare_output_file(args.output)
        record = {"schema": SCHEMA, "command": args.command, "tool": tool_record(), "invocation": invocation_record(),
                  "started_at_utc": utc_now(), "state": "UNKNOWN", "loaded_project_files": []}
        require_no_bytecode()
        checks = {"mc10": mc10, "mc29": mc29, "host-state": host_state}[args.command](args, record)
        met = all(checks.values())
        record.update(checks=checks, expectation_met=met, state="EXPECTED" if met else "NOT_EXPECTED",
                      finished_at_utc=utc_now(), elapsed_s=time.monotonic() - started)
        write_new(output, json_text(record))
        sys.stderr.write("MH-CONTROL " + json.dumps({"command": args.command, "state": record["state"],
                                                     "failed_checks": sorted(k for k, v in checks.items() if not v)},
                                                    sort_keys=True) + "\n")
        return EXIT_EXPECTED if met else EXIT_NOT_EXPECTED
    except Refusal as exc:
        document = dict(record or {"schema": "ontokin.c271.p35-tool-refusal/1", "tool": "control_harness.py"},
                        state="REFUSED", refusal=exc.as_dict())
        return report_end(output, document, EXIT_REFUSED)
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        document = dict(record or {"schema": "ontokin.c271.p35-tool-failure/1", "tool": "control_harness.py"},
                        state="UNKNOWN", error=failure_of(exc))
        return report_end(output, document, EXIT_UNKNOWN)


def report_end(output, document, code):
    """A refusal or failure goes to stderr, and to the output path while that path is still absent."""
    document.update(finished_at_utc=utc_now())
    text = json_text(document)
    sys.stderr.write("MH-CONTROL " + json.dumps({"state": document.get("state"), "refusal": document.get("refusal"),
                                                 "error": document.get("error")}, sort_keys=True, default=repr) + "\n")
    if output is not None and not os.path.lexists(output):
        try:
            write_new(output, text)
        except OSError:
            pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
