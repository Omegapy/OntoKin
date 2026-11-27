#!/usr/bin/env python3
"""Runtime-discovery collector for gate MH of C271-P35 (contract control MC28).

Two commands, each writing one absent output file:

  discover  List the default unittest inventory exactly as the unit stage of the root's
            tools/check_local.py discovers it, without running any test. The unit stage's argv,
            and the interpreter flag that build_plan's add() puts after the interpreter, are read
            from that file by parsing it; the argv must be "-m unittest discover -s tests -v" and
            the flag "-B". The discovery then runs in this process as "python -B -m unittest
            discover" would run it from the root: the root is the working directory and
            sys.path[0], and unittest's own loader discovers. The process environment must be
            exactly a frozen one. Importing the test modules is the only code that runs. Every
            attempt to create a process during discovery is refused and recorded.

  compare   Compare a discovered inventory with the baseline inventory plus the approved
            additions, exactly: the IDs that are missing and the IDs that are extra. Counts and
            duplicates are recomputed from the IDs of both documents.

Launch, from a clean worktree, with the qualification interpreter and -B (N-09; a start without -B
refuses):

  env -i <frozen environment> <worktree>/.venv/bin/python -B discover_inventory.py discover \
      --root ROOT --environment ENV --environment-sha256 H --output OUT
  <worktree>/.venv/bin/python -I -S -B discover_inventory.py compare --current C --current-sha256 H \
      --baseline B --baseline-sha256 H --additions A --additions-sha256 H --output OUT

The tool starts no process and never starts Git: the baseline is discovered from an exported
copy of the baseline commit's tree, given as --root. It uses the standard library only. It runs
from its committed place inside the root: its own __main__ is the one root module it admits.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import stat
import sys
import time

SCHEMA_DISCOVERY = "ontokin.c271.p35-runtime-discovery/2"
SCHEMA_COMPARISON = "ontokin.c271.p35-runtime-discovery-comparison/2"
ENVIRONMENT_SCHEMA = "ontokin.c271.p35-unit-environment/1"
ADDITIONS_SCHEMA = "ontokin.c271.p33-inventory-additions/1"
# The unit stage of tools/check_local.py: add("unit-tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"]).
UNIT_STAGE_ID = "unit-tests"
UNIT_STAGE_ARGS = ["-m", "unittest", "discover", "-s", "tests", "-v"]
CF_NAME = "__CF_USER_TEXT_ENCODING"
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                            "os.system", "os.startfile"))
# ctypes lookups of libc's process-creation functions; a call through them raises no audit event of its own.
CTYPES_PROCESS_SYMBOLS = frozenset(("fork", "vfork", "posix_spawn", "posix_spawnp", "execve", "execv", "execvp",
                                    "execvpe", "execl", "execlp", "execle", "system", "popen"))
MAX_DOCUMENT = 64 * 1024 * 1024
EXIT_COMPLETE, EXIT_FINDINGS, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3


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
            "pid": os.getpid(),
            "python": {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
                       "build_string": sys.version, "executable": sys.executable,
                       "flags": {name: getattr(sys.flags, name) for name in FLAG_NAMES}}}


def own_main_admission(root):
    """TR-01: this running tool's own __main__, when its file lies under the root: the one root module admitted."""
    main = sys.modules.get("__main__")
    path = getattr(main, "__file__", None)
    own = os.path.realpath(__file__)
    if type(path) is str and os.path.realpath(path) == own and own.startswith(root + "/"):
        return {"module": "__main__", "path": own, "admitted": True,
                "reason": "the running tool itself, identified by realpath equality with its own file"}
    return None


def preloaded_root_modules(root):
    """Every loaded module whose file lies under the root, except this tool's own __main__."""
    own = os.path.realpath(__file__)
    rows = []
    for name, module in sorted(tuple(sys.modules.items())):
        path = getattr(module, "__file__", None)
        if type(path) is not str or not os.path.realpath(path).startswith(root + "/"):
            continue
        if name == "__main__" and os.path.realpath(path) == own:
            continue
        rows.append(name)
    return rows


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


def load_environment(path, sha256):
    """The frozen environment, bound by a SHA-256 supplied outside it; HOME is never part of one (TR-06)."""
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
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


def compare_environment(observed, frozen):
    """Exactly the frozen mapping; __CF_USER_TEXT_ENCODING, which macOS adds, is admitted and recorded (S10)."""
    observed = dict(observed)
    admitted = observed.pop(CF_NAME, None) if CF_NAME not in frozen else None
    missing = sorted(set(frozen) - set(observed))
    extra = sorted(set(observed) - set(frozen))
    differing = sorted(name for name in set(frozen) & set(observed) if frozen[name] != observed[name])
    if missing or extra or differing:
        raise Refusal("ENVIRONMENT", "The process environment differs from the frozen environment "
                      "(names only; values are not reported)", missing=missing, extra=extra, differing=differing)
    return admitted


# ---------------------------------------------------------------------------
# The unit stage's discovery arguments and interpreter flags, read from tools/check_local.py
# ---------------------------------------------------------------------------

def _flags_added_by_add(function):
    """build_plan's add(): if argv[0] == python, argv = [python, FLAGS..., *argv[1:]]; returns FLAGS."""
    for node in function.body:
        if not (isinstance(node, ast.If) and isinstance(node.test, ast.Compare) and len(node.test.ops) == 1
                and isinstance(node.test.ops[0], ast.Eq)):
            continue
        left, right = node.test.left, node.test.comparators[0]
        if not (isinstance(left, ast.Subscript) and isinstance(left.value, ast.Name) and left.value.id == "argv"
                and isinstance(left.slice, ast.Constant) and left.slice.value == 0
                and isinstance(right, ast.Name) and right.id == "python"):
            continue
        for statement in node.body:
            if (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name) and statement.targets[0].id == "argv"
                    and isinstance(statement.value, ast.List) and statement.value.elts):
                elements = statement.value.elts
                if not (isinstance(elements[0], ast.Name) and elements[0].id == "python"
                        and isinstance(elements[-1], ast.Starred)):
                    continue
                flags = elements[1:-1]
                if all(isinstance(item, ast.Constant) and type(item.value) is str for item in flags):
                    return [item.value for item in flags]
    return None


def unit_stage_arguments(root):
    """The unit stage's argv after the interpreter, and the flags build_plan adds, from tools/check_local.py."""
    path = root + "/tools/check_local.py"
    raw, binding = read_regular(path, 4 * 1024 * 1024, rule="UNIT-STAGE")
    try:
        tree = ast.parse(raw, filename=path)
    except SyntaxError as exc:
        raise Refusal("UNIT-STAGE", "tools/check_local.py does not parse", error=str(exc)) from exc
    plans = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "build_plan"]
    if len(plans) != 1:
        raise Refusal("UNIT-STAGE", "Expected exactly one build_plan function in tools/check_local.py")
    adders = [node for node in plans[0].body if isinstance(node, ast.FunctionDef) and node.name == "add"]
    flags = _flags_added_by_add(adders[0]) if len(adders) == 1 else None
    if flags is None:
        raise Refusal("UNIT-STAGE", "build_plan's add() does not show the interpreter flags it inserts")
    found = [node for node in ast.walk(plans[0])
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "add"
             and len(node.args) >= 2 and isinstance(node.args[0], ast.Constant) and node.args[0].value == UNIT_STAGE_ID]
    if len(found) != 1:
        raise Refusal("UNIT-STAGE", "Expected exactly one unit-stage declaration in build_plan", found=len(found))
    command = found[0].args[1]
    if not isinstance(command, ast.List) or not command.elts or not isinstance(command.elts[0], ast.Name) \
            or command.elts[0].id != "python":
        raise Refusal("UNIT-STAGE", "The unit-stage argv is not a literal list that starts with the interpreter")
    arguments = []
    for element in command.elts[1:]:
        if not (isinstance(element, ast.Constant) and type(element.value) is str):
            raise Refusal("UNIT-STAGE", "The unit-stage argv holds a non-literal element")
        arguments.append(element.value)
    if arguments != UNIT_STAGE_ARGS:
        raise Refusal("UNIT-STAGE", "The unit-stage argv differs from the one this collector reproduces",
                      found=arguments, expected=UNIT_STAGE_ARGS)
    if flags != ["-B"]:
        raise Refusal("UNIT-STAGE", "build_plan inserts interpreter flags other than -B", flags=flags)
    return {"check_local": {"path": path, **binding}, "argv_after_interpreter": arguments,
            "interpreter_flags_added_by_build_plan": flags, "derived_from": "build_plan.add, by its AST",
            "line": found[0].lineno}


def discovery_parameters(arguments):
    """unittest's own discovery options: start, pattern and top (unittest/main.py, _do_discovery)."""
    if arguments[:3] != ["-m", "unittest", "discover"]:
        raise Refusal("UNIT-STAGE", "The unit stage is not a unittest discovery")
    rest = list(arguments[3:])
    options = {"-s": "start", "--start-directory": "start", "-p": "pattern", "--pattern": "pattern",
               "-t": "top", "--top-level-directory": "top"}
    values = {"start": ".", "pattern": "test*.py", "top": None}
    while rest:
        item = rest.pop(0)
        if item in ("-v", "--verbose", "-q", "--quiet"):
            continue
        if item in options and rest:
            values[options[item]] = rest.pop(0)
            continue
        raise Refusal("UNIT-STAGE", "Unsupported unit-stage discovery argument", argument=item)
    return values


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------

def flatten(suite):
    import unittest
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


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


def discover(args, root, output):
    started, monotonic = utc_now(), time.monotonic()
    record = {"schema": SCHEMA_DISCOVERY, "tool": tool_record(), "invocation": invocation_record(),
              "started_at_utc": started, "root": root, "state": "UNKNOWN"}
    flags = sys.flags
    if flags.isolated or flags.no_site or flags.ignore_environment or flags.safe_path:
        raise Refusal("PYTHON", "Run without -I, -S, -E or -P, as the unit stage's interpreter runs "
                      "(python -B -m unittest)")
    frozen, environment_binding = load_environment(args.environment, args.environment_sha256)
    admitted_cf = compare_environment(os.environ, frozen)
    unit = unit_stage_arguments(root)
    parameters = discovery_parameters(unit["argv_after_interpreter"])
    record["unit_stage"] = {**unit, "discovery": parameters}
    if parameters["top"] is not None:
        raise Refusal("UNIT-STAGE", "A top-level directory option is not reproduced by this collector")
    preloaded = preloaded_root_modules(root)
    if preloaded:
        raise Refusal("PYTHON", "A module of the root is already loaded", modules=preloaded)
    record["own_main_admitted"] = own_main_admission(root)
    record["environment"] = {"frozen": environment_binding, "names": sorted(frozen),
                             "admitted_cf_user_text_encoding": admitted_cf}
    audit = ProcessAudit(block=True)
    sys.addaudithook(audit)
    # python -m from the root: the root is the working directory and sys.path[0]; the tool's own
    # directory is not on the path.
    own = os.path.dirname(os.path.realpath(__file__))
    record["sys_path_before"] = list(sys.path)
    os.chdir(root)
    sys.path[:] = [root] + [item for item in sys.path[1:] if os.path.realpath(item or ".") != own]
    record["sys_path_at_discovery"] = list(sys.path)
    import unittest
    loader = unittest.TestLoader()
    failed_type = getattr(unittest.loader, "_FailedTest", None)
    discovery_started = time.monotonic()
    try:
        suite = loader.discover(parameters["start"], parameters["pattern"], parameters["top"])
    finally:
        audit.enabled = False
    record["discovery_seconds"] = time.monotonic() - discovery_started
    record["sys_path_after_discovery"] = list(sys.path)
    identifiers, failures, foreign = [], [], Counter()
    for test in flatten(suite):
        test_id = test.id()
        if failed_type is not None and isinstance(test, failed_type):
            failures.append({"id": test_id, "name": getattr(test, "_testMethodName", None),
                             "exception": text_of(repr(getattr(test, "_exception", None)), 65536)})
            continue
        if not isinstance(test, unittest.TestCase):
            foreign[type(test).__module__ + "." + type(test).__qualname__] += 1
        identifiers.append(test_id)
    counts = Counter(identifiers)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    ordered = "\n".join(identifiers).encode("utf-8")
    unique_sorted = sorted(counts)
    record.update(
        ids_in_discovery_order=identifiers,
        count=len(identifiers), unique_count=len(unique_sorted),
        order_sha256=hashlib.sha256(ordered).hexdigest(),
        sorted_sha256=hashlib.sha256("\n".join(unique_sorted).encode("utf-8")).hexdigest(),
        duplicates=duplicates, failed_imports=failures,
        loader_errors=[text_of(item, 65536) for item in loader.errors],
        tests_that_are_not_test_cases=dict(sorted(foreign.items())),
        modules=sorted({name.split(".")[0] for name in identifiers}),
        process_events=audit.events,
        loaded_project_files=loaded_project_files(root))
    record["module_count"] = len(record["modules"])
    record["bytecode_present"] = sorted(row["path"] for row in record["loaded_project_files"] if row["bytecode_present"])
    clean = not failures and not duplicates and not audit.events and not loader.errors and not record["bytecode_present"]
    record.update(state="COMPLETE" if clean else "COMPLETE_WITH_FINDINGS", finished_at_utc=utc_now(),
                  elapsed_s=time.monotonic() - monotonic)
    write_new(output, json_text(record))
    return EXIT_COMPLETE if clean else EXIT_FINDINGS


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------

def read_bound(path, sha256, what):
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise Refusal("DIGEST", "Expected a lowercase SHA-256 digest for the " + what)
    raw, binding = read_regular(path, MAX_DOCUMENT, rule="INPUT")
    if binding["sha256"] != sha256:
        raise Refusal("DIGEST", "The " + what + " differs from its supplied SHA-256", path=path,
                      observed=binding["sha256"])
    return strict_json(raw, what=what), {"path": path, **binding}


def discovery_summary(value, what):
    """The document's own fields, and its counts and duplicates recomputed from its IDs (TR-07)."""
    if type(value) is not dict or value.get("schema") != SCHEMA_DISCOVERY:
        raise Refusal("SCHEMA", "The " + what + " is not a " + SCHEMA_DISCOVERY + " document")
    ids = value.get("ids_in_discovery_order")
    if type(ids) is not list or not all(type(item) is str for item in ids):
        raise Refusal("SCHEMA", "The " + what + " has no list of discovered IDs")
    counts = Counter(ids)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    summary = {"root": value.get("root"), "state": value.get("state"), "count": len(ids), "unique_count": len(counts),
               "duplicates_recomputed": duplicates, "duplicates_recorded": value.get("duplicates"),
               "count_recorded": value.get("count"),
               "failed_imports": len(value.get("failed_imports") or []),
               "loader_errors": len(value.get("loader_errors") or []),
               "process_events": len(value.get("process_events") or []),
               "bytecode_present": len(value.get("bytecode_present") or []),
               "check_local": (value.get("unit_stage") or {}).get("check_local"),
               "tool": value.get("tool")}
    summary["consistent"] = (summary["count_recorded"] == len(ids) and summary["duplicates_recorded"] == duplicates)
    summary["clean"] = (summary["state"] == "COMPLETE" and not duplicates and summary["failed_imports"] == 0
                        and summary["loader_errors"] == 0 and summary["process_events"] == 0
                        and summary["bytecode_present"] == 0 and summary["consistent"])
    return summary, set(ids)


def compare(args, output):
    started, monotonic = utc_now(), time.monotonic()
    current, current_binding = read_bound(args.current, args.current_sha256, "current inventory")
    baseline, baseline_binding = read_bound(args.baseline, args.baseline_sha256, "baseline inventory")
    additions, additions_binding = read_bound(args.additions, args.additions_sha256, "approved additions")
    current_summary, current_ids = discovery_summary(current, "current inventory")
    baseline_summary, baseline_ids = discovery_summary(baseline, "baseline inventory")
    if type(additions) is not dict or additions.get("schema") != ADDITIONS_SCHEMA:
        raise Refusal("SCHEMA", "The approved additions are not a " + ADDITIONS_SCHEMA + " document")
    added, removed = additions.get("added"), additions.get("removed")
    if not (type(added) is list and all(type(item) is str for item in added)
            and type(removed) is list and all(type(item) is str for item in removed)):
        raise Refusal("SCHEMA", "The approved additions need string lists 'added' and 'removed'")
    added_set, removed_set = set(added), set(removed)
    expected = (baseline_ids | added_set) - removed_set
    missing, extra = sorted(expected - current_ids), sorted(current_ids - expected)
    by_module = Counter(item.split(".")[0] for item in added)
    declared = {
        "base_count": additions.get("base_count"), "candidate_count": additions.get("candidate_count"),
        "added_count": additions.get("added_count"), "removed_count": additions.get("removed_count"),
        "added_by_module": additions.get("added_by_module"), "base_commit": additions.get("base_commit"),
        "candidate_commit": additions.get("candidate_commit")}
    consistency = {
        "added_unique": len(added_set) == len(added),
        "added_count_matches": declared["added_count"] == len(added),
        "removed_count_matches": declared["removed_count"] == len(removed),
        "added_by_module_matches": declared["added_by_module"] == dict(by_module),
        "baseline_count_matches_base_count": declared["base_count"] == len(baseline_ids),
        "candidate_count_matches": declared["candidate_count"] == len(baseline_ids) + len(added_set) - len(removed_set),
        "additions_not_in_baseline": not (added_set & baseline_ids),
        "removals_in_baseline": removed_set <= baseline_ids}
    inputs_clean = {"current_clean": current_summary["clean"], "baseline_clean": baseline_summary["clean"]}
    exact = not missing and not extra and all(consistency.values()) and all(inputs_clean.values())
    record = {"schema": SCHEMA_COMPARISON, "tool": tool_record(), "invocation": invocation_record(),
              "started_at_utc": started,
              "inputs": {"current": current_binding, "baseline": baseline_binding, "additions": additions_binding},
              "current": current_summary, "baseline": baseline_summary, "additions_declared": declared,
              "additions": {"added": len(added), "removed": len(removed), "by_module": dict(sorted(by_module.items()))},
              "expected_count": len(expected), "current_count": len(current_ids),
              "missing": missing, "extra": extra,
              "additions_already_in_baseline": sorted(added_set & baseline_ids),
              "removals_not_in_baseline": sorted(removed_set - baseline_ids),
              "consistency": consistency, "inputs_clean": inputs_clean, "exact_match": exact,
              "finished_at_utc": utc_now(), "elapsed_s": time.monotonic() - monotonic,
              "loaded_project_files": []}
    write_new(output, json_text(record))
    return EXIT_COMPLETE if exact else EXIT_FINDINGS


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def main(argv=None):
    parser = _Parser(prog="discover_inventory.py", allow_abbrev=False, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    sub = commands.add_parser("discover")
    sub.add_argument("--root", required=True)
    sub.add_argument("--environment", required=True)
    sub.add_argument("--environment-sha256", required=True)
    sub.add_argument("--output", required=True)
    sub = commands.add_parser("compare")
    for name in ("current", "baseline", "additions"):
        sub.add_argument("--" + name, required=True)
        sub.add_argument("--" + name + "-sha256", required=True)
    sub.add_argument("--output", required=True)
    output = None
    try:
        args = parser.parse_args(argv)
        output = prepare_output_file(args.output)
        require_no_bytecode()
        if args.command == "discover":
            return discover(args, canonical_path(args.root, kind="dir", rule="ROOT"), output)
        return compare(args, output)
    except Refusal as exc:
        return report_end(output, {"schema": "ontokin.c271.p35-tool-refusal/1", "tool": "discover_inventory.py",
                                   "state": "REFUSED", "refusal": exc.as_dict()}, EXIT_REFUSED)
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        return report_end(output, {"schema": "ontokin.c271.p35-tool-failure/1", "tool": "discover_inventory.py",
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
