"""Shared helpers of the MH tooling's focused tests: the standard library only, and no machine path.

The tests run with the qualification interpreter and -B (N-09), from the tooling directory:

    <worktree>/.venv/bin/python -B -m unittest discover -s tests -v

Every child is started here and counted: the interpreter (always with -B), /bin/sh and /usr/bin/true.
A tool under test may itself start /bin/sh, /usr/bin/true or a stand-in script that this interpreter
runs with -B; those starts are read from its records and counted too. No test starts Node, Git, ldd,
codesign or the observer's observe command.

The project root is MH_TOOLING_ROOT when that is set, otherwise the checkout that holds this file
(<worktree>/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/tests/).

The tools under test are those beside this directory, or those in MH_TOOLING_UNDER_TEST when that is
set: the same suite then runs against another copy, such as the rejected tooling of review 001.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

TOOLING = (Path(os.environ["MH_TOOLING_UNDER_TEST"]).resolve() if os.environ.get("MH_TOOLING_UNDER_TEST")
           else Path(__file__).resolve().parents[1])
PYTHON = sys.executable
STARTS = collections.Counter()
TOOL_STARTS = collections.Counter()
DECLARED = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
CF_NAME = "__CF_USER_TEXT_ENCODING"
ENVIRONMENT_SCHEMA = "ontokin.c271.p35-unit-environment/1"
# The committed place of the tooling inside a root (TR-01).
COMMITTED_PLACE = "docs/engineering/localized-repair-c271/macos-qualification-p35/tooling"


def project_root():
    candidates = [os.environ.get("MH_TOOLING_ROOT")]
    parents = Path(__file__).resolve().parents
    if len(parents) > 6:
        candidates.append(str(parents[6]))
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, "prototypes/static_tray_v01/supervisor_darwin_v01.py")):
            return os.path.realpath(candidate)
    raise AssertionError("Set MH_TOOLING_ROOT to the worktree root: these tests read the project's own files")


def tool_source(script):
    return (TOOLING / script).read_bytes()


def legacy(script, marker):
    """True when the tool under test is an earlier version, recognized by a schema marker in its source."""
    return marker.encode("ascii") in tool_source(script)


def resolved_temp(test):
    """A fresh resolved temporary directory, removed after the test."""
    base = os.path.realpath(tempfile.gettempdir())
    path = os.path.realpath(tempfile.mkdtemp(prefix="mh-tooling-", dir=base))
    test.addCleanup(shutil.rmtree, path, True)
    return path


def child_environment(**extra):
    environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
                   "TMPDIR": os.path.realpath(tempfile.gettempdir()) + "/", "PYTHONDONTWRITEBYTECODE": "1"}
    environment.update(extra)
    return environment


def frozen_environment(path, mapping):
    """A frozen environment document; returns its path and SHA-256."""
    written = write(path, json.dumps({"schema": ENVIRONMENT_SCHEMA, "environment": mapping}).encode())
    return written, sha256_file(written)


def tool_argv(script, args, flags, tool_path):
    if "-B" not in flags:
        raise AssertionError("Every start of the framework interpreter carries -B (MH-PLAN section 10, N-09)")
    path = str(tool_path) if tool_path is not None else str(TOOLING / script)
    return [PYTHON, *flags, path, *[str(item) for item in args]]


def run_tool(script, *args, flags=("-B",), env=None, cwd=None, timeout=600, tool_path=None):
    """Start one tool with the qualification interpreter; -B is mandatory (N-09)."""
    argv = tool_argv(script, args, flags, tool_path)
    STARTS["python -B"] += 1
    return subprocess.run(argv, env=child_environment() if env is None else env, cwd=cwd, capture_output=True,
                          timeout=timeout)


def start_tool(script, *args, flags=("-B",), env=None, cwd=None, tool_path=None):
    """Start one tool without waiting, for a test that signals it."""
    argv = tool_argv(script, args, flags, tool_path)
    STARTS["python -B"] += 1
    return subprocess.Popen(argv, env=child_environment() if env is None else env, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)


def start_child(argv, **kwargs):
    """A direct child of this test: /bin/sh, /usr/bin/true, or this interpreter with -B."""
    if argv[0] == PYTHON and "-B" not in argv[1:3]:
        raise AssertionError("Every start of the framework interpreter carries -B (N-09)")
    if argv[0] not in (PYTHON, "/bin/sh", "/usr/bin/true"):
        raise AssertionError("A test child is /bin/sh, /usr/bin/true or this interpreter with -B")
    STARTS["python -B" if argv[0] == PYTHON else argv[0]] += 1
    return subprocess.Popen(argv, **kwargs)


def count_tool_starts(kind, number):
    TOOL_STARTS[kind] += number


def in_place(root, script):
    """A copy of one tool at its committed place inside a root (TR-01)."""
    target = Path(root) / COMMITTED_PLACE / script
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TOOLING / script, target)
    return str(target)


def stand_in(path, body):
    """An executable script that this interpreter runs with -B: a stand-in for Node in the runner's tests."""
    return write(path, ("#!" + PYTHON + " -B\n" + body).encode(), 0o755)


# The reason that every tool records with its admission of its own __main__ (TR-01).
ADMISSION_REASON = "the running tool itself, identified by realpath equality with its own file"


def admission_place(script, root, tool_path=None):
    """Where the running tool lies: "inside the root" (its committed place among them) or "outside the root"."""
    own = os.path.realpath(tool_path if tool_path is not None else TOOLING / script)
    return "inside the root" if own.startswith(os.path.realpath(root) + "/") else "outside the root"


def expected_admission(script, root, tool_path=None):
    """own_main_admitted as the tool must record it for --root ROOT, in either place (TR-01, IP-01).

    Outside the root: None. Inside the root, as at the tooling's committed place in the worktree:
    exactly the running tool's own __main__, identified by its realpath, admitted.
    """
    if admission_place(script, root, tool_path) == "outside the root":
        return None
    own = os.path.realpath(tool_path if tool_path is not None else TOOLING / script)
    return {"module": "__main__", "path": own, "admitted": True, "reason": ADMISSION_REASON}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, "rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def write(path, data, mode=0o644):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    os.chmod(path, mode)
    return str(path)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def binding(path):
    info = os.stat(path)
    return {"sha256": sha256_file(path), "size_bytes": info.st_size, "mode": "0o%03o" % stat.S_IMODE(info.st_mode)}


def descriptor(path):
    return {"path": str(path), **binding(path)}


def read_json(path):
    with open(path, "rb") as stream:
        return json.loads(stream.read())


def process_image(pid=None):
    """proc_pidpath of a process (this one by default): the image every start of this interpreter has."""
    import ctypes
    function = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True).proc_pidpath
    function.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32)
    function.restype = ctypes.c_int
    buffer = ctypes.create_string_buffer(4096)
    length = function(os.getpid() if pid is None else pid, buffer, ctypes.sizeof(buffer))
    assert length > 0
    return os.fsdecode(buffer.raw[:length])


def load_module(name, path):
    """Load one file as a module by path, without putting its directory on sys.path."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class FlagsWithoutB:
    """sys.flags as a start without -B would show them, for a test of a tool's refusal in this process."""

    def __init__(self):
        self._flags = sys.flags

    def __getattr__(self, name):
        return 0 if name == "dont_write_bytecode" else getattr(self._flags, name)
