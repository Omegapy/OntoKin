"""Development tests of the Darwin supervisor variant (S4); standard library only.

Contract ``ontokin.current-host-readback/0.2.0``, profile ``darwin-arm64-v1``, section 5, and
section 4.1 of the C271-P33 implementation plan.  These are development tests written with the
implementation.  They are not the frozen controls, which an independent author freezes later.

Process starts: every child is a non-Node Python process started as
``sys.executable -I -S -B -c <fixed code>``; ``-B`` keeps the children from writing bytecode
into the interpreter installation.  No Node, ldd or codesign process starts.  Each test's
docstring says what it starts.  The MC17 cases are simulated at the platform, machine or sysctl
boundary, with ``subprocess.Popen`` patched, and are labelled simulated.  One observation test
records what this host's ``killpg(pgid, 0)`` reports while a group's only member has exited
but is not yet reaped; it observes the host and is not a control.  The tests that start real
children need the darwin-arm64-v1 executor; on another host the Darwin precondition refuses
them visibly, never as a skip.
"""
from __future__ import annotations

import builtins
import contextlib
import ctypes
import difflib
import dis
import errno
import hashlib
import inspect
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import tokenize
import types
import unittest
from unittest.mock import Mock, patch

from prototypes.static_tray_v01 import supervisor
from prototypes.static_tray_v01 import supervisor_darwin_v01 as darwin


CHILD = [sys.executable, "-I", "-S", "-B", "-c"]
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
SLEEPER = "import time; time.sleep(15)"
IMPORTED = ("Clock", "Stop", "LIMITS", "inventory", "group_exists", "terminate_group", "json_bytes")
# The original receipt: the initial record of run_process plus "end_monotonic", which is always
# added; an observed cancellation adds "cancellation_completion_ms".
RECEIPT_KEYS = frozenset({"argv", "cwd", "environment", "label", "start_monotonic", "pid",
                          "process_group", "returncode", "observed_log_bytes", "retained_log_bytes",
                          "cleanup", "handles_closed", "error", "end_monotonic"})
CLEANUP_KEYS = frozenset({"passed", "elapsed_ms", "process_group_absent", "reaped"})
PREFIX = "Cannot establish the Darwin arm64 native precondition: "
ORIGINAL_PRECONDITION = (
    "    libc = ctypes.CDLL(None, use_errno=True)\n",
    "    if libc.prctl(36, 1, 0, 0, 0) != 0:\n",
    '        raise Stop("OTRAY-E-BACKEND", "Cannot establish Linux descendant reaping")\n')
DARWIN_PRECONDITION = (
    "    unmet = darwin_precondition()\n",
    "    if unmet is not None:\n",
    '        raise Stop("OTRAY-E-BACKEND", "Cannot establish the Darwin arm64 native precondition: " + unmet)\n')
SYSCTLBYNAME = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p,
                                ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t)


def _tokens(function):
    source = inspect.getsource(function)
    rows = [[tokenize.tok_name[token.type], token.string, list(token.start), list(token.end)]
            for token in tokenize.generate_tokens(io.StringIO(source).readline)]
    return source, rows


def _precondition_rows(source, block):
    lines = source.splitlines(keepends=True)
    found = [index for index in range(len(lines)) if tuple(lines[index:index + len(block)]) == block]
    if len(found) != 1:
        raise AssertionError("The precondition block does not occur exactly once")
    return found[0] + 1, found[0] + len(block)


def token_comparison():
    """MC14 development comparison of the two ``run_process`` functions, token by token.

    Compared: every token that ``tokenize.generate_tokens`` yields for ``inspect.getsource`` of
    each function, by token type, string, start and end.  Comments and the NL, NEWLINE, INDENT
    and DEDENT tokens are compared like every other token.  Ignored: nothing.  The precondition
    block is the three lines of ``ORIGINAL_PRECONDITION`` and of ``DARWIN_PRECONDITION``.
    """
    sides = {}
    for side, function, block in (("original", supervisor.run_process, ORIGINAL_PRECONDITION),
                                  ("darwin", darwin.run_process, DARWIN_PRECONDITION)):
        source, tokens = _tokens(function)
        first, last = _precondition_rows(source, block)
        parts = {"before": [], "precondition": [], "after": []}
        for token in tokens:
            start, end = token[2][0], token[3][0]
            if end < first:
                parts["before"].append(token)
            elif start > last:
                parts["after"].append(token)
            elif first <= start and end <= last:
                parts["precondition"].append(token)
            else:
                raise AssertionError("A token crosses the precondition block boundary")
        sides[side] = {"function": function.__module__ + "." + function.__qualname__,
                       "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                       "source": source, "tokens": tokens, "rows": (first, last), "parts": parts}
    original, variant = sides["original"], sides["darwin"]
    matcher = difflib.SequenceMatcher(None, [tuple(token[:2]) for token in original["tokens"]],
                                      [tuple(token[:2]) for token in variant["tokens"]], autojunk=False)
    differences, outside = [], 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        row = {"tag": tag, "original": original["tokens"][i1:i2], "darwin": variant["tokens"][j1:j2]}
        for side in ("original", "darwin"):
            first, last = sides[side]["rows"]
            outside += sum(1 for token in row[side] if not (first <= token[2][0] and token[3][0] <= last))
        differences.append(row)
    return {
        "kind": "MC14 development token comparison; not a frozen control",
        "compared": "every token of tokenize.generate_tokens over inspect.getsource of each run_process, "
                    "by type, string, start and end, comments and NL, NEWLINE, INDENT and DEDENT included",
        "ignored": "nothing",
        "functions": {side: {"function": value["function"], "source_sha256": value["source_sha256"],
                             "token_count": len(value["tokens"]), "precondition_rows": list(value["rows"]),
                             "precondition_token_count": len(value["parts"]["precondition"])}
                      for side, value in sides.items()},
        "before_precondition_equal": original["parts"]["before"] == variant["parts"]["before"],
        "after_precondition_equal": original["parts"]["after"] == variant["parts"]["after"],
        "precondition_equal": original["parts"]["precondition"] == variant["parts"]["precondition"],
        "differences": differences,
        "differing_tokens_outside_precondition": outside,
        "source_diff": list(difflib.unified_diff(original["source"].splitlines(keepends=True),
                                                 variant["source"].splitlines(keepends=True),
                                                 "supervisor.run_process", "supervisor_darwin_v01.run_process")),
    }


def simulated_libsystem(value=0, *, status=0, size=None, calls=None):
    """Simulated libSystem: its ``sysctlbyname`` is a C-callable stand-in, not the kernel's."""
    def sysctlbyname(name, oldp, oldlenp, newp, newlen):
        if calls is not None:
            calls.append((name, newp, newlen))
        if status:
            return status
        ctypes.c_int.from_address(oldp).value = value
        oldlenp[0] = ctypes.sizeof(ctypes.c_int) if size is None else size
        return 0
    return types.SimpleNamespace(sysctlbyname=SYSCTLBYNAME(sysctlbyname))


@contextlib.contextmanager
def simulated_host(*, platform="darwin", machine="arm64", library=None, load_error=None):
    """Simulated boundary: ``sys.platform``, ``os.uname()`` and the libSystem loader are patched."""
    uname = os.uname_result(("Darwin", "simulated", "simulated", "simulated", machine))
    if load_error is not None:
        loader = patch.object(darwin, "_libsystem", side_effect=load_error)
    else:
        loader = patch.object(darwin, "_libsystem",
                              return_value=simulated_libsystem() if library is None else library)
    with patch.object(sys, "platform", platform), patch.object(os, "uname", return_value=uname), loader as load:
        yield load


def _global_loads(function):
    return {instruction.argval for instruction in dis.get_instructions(function)
            if instruction.opname == "LOAD_GLOBAL"}


def _resolve(module, name):
    namespace = vars(module)
    return namespace[name] if name in namespace else vars(builtins)[name]


def _killpg_errno(group):
    try:
        os.killpg(group, 0)
    except OSError as error:
        return error.errno
    return 0


def _gone(pid, seconds=2.0):
    """True once ``kill(pid, 0)`` fails with ESRCH or EPERM (no live process of ours), polled for at most ``seconds``."""
    deadline = time.monotonic() + seconds
    while True:
        try:
            os.kill(pid, 0)
        except (ProcessLookupError, PermissionError):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


class StageCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="darwin-supervisor-")
        self.addCleanup(temporary.cleanup)
        self.stage = Path(temporary.name) / "stage"
        self.stage.mkdir()
        self.starts = []
        self.addCleanup(self.no_group_left)

    def started(self, record):
        self.starts.append(record)

    def no_group_left(self):
        """Guard after each test: a started group that is still present is killed, then reported."""
        left = []
        for record in self.starts:
            group = record["process_group"]
            try:
                os.killpg(group, 0)
            except (ProcessLookupError, PermissionError):
                continue
            left.append(group)
            with contextlib.suppress(ProcessLookupError):
                os.killpg(group, signal.SIGKILL)
        if left:
            self.fail("Started process groups were still present; the test guard killed them: %r" % left)

    def assert_cleanup(self, record):
        cleanup = record["cleanup"]
        self.assertEqual(set(cleanup), CLEANUP_KEYS)
        self.assertIs(cleanup["passed"], True)
        self.assertIs(cleanup["process_group_absent"], True)
        self.assertIs(cleanup["reaped"], True)
        self.assertEqual(darwin.LIMITS["cleanup_ms"], 2000)
        self.assertLessEqual(cleanup["elapsed_ms"], darwin.LIMITS["cleanup_ms"])
        self.assertIs(record["handles_closed"], True)
        self.assertFalse(darwin.group_exists(record["process_group"]))


class DarwinSupervisorSource(unittest.TestCase):
    """Development checks of the variant's source, imports and signature; they start nothing."""

    def test_mc14_development_token_comparison_differs_only_in_the_precondition(self):
        """Starts nothing: tokenizes inspect.getsource of both run_process functions and compares them."""
        result = token_comparison()
        for side in ("original", "darwin"):
            self.assertEqual(result["functions"][side]["precondition_rows"], [7, 9])
        self.assertTrue(result["before_precondition_equal"])
        self.assertTrue(result["after_precondition_equal"])
        self.assertFalse(result["precondition_equal"])
        self.assertTrue(result["differences"])
        self.assertEqual(result["differing_tokens_outside_precondition"], 0)

    def test_imported_names_and_signature_are_the_original(self):
        """Starts nothing: the seven imported names are the original objects; the signature is equal."""
        for name in IMPORTED:
            self.assertIs(getattr(darwin, name), getattr(supervisor, name), name)
        self.assertEqual(inspect.signature(darwin.run_process), inspect.signature(supervisor.run_process))

    def test_body_globals_bind_to_the_original_objects(self):
        """Starts nothing: every global the body loads, except the precondition's, is the original object."""
        original, variant = _global_loads(supervisor.run_process), _global_loads(darwin.run_process)
        self.assertEqual(original - variant, {"ctypes"})
        self.assertEqual(variant - original, {"darwin_precondition"})
        for name in sorted(original & variant):
            self.assertIs(_resolve(darwin, name), _resolve(supervisor, name), name)


class DarwinPrecondition(StageCase):
    """The real precondition on this host, and the MC17 development cases, which are simulated."""

    def assert_refused_before_start(self, reason, **host):
        clock = darwin.Clock(total_ms=20000)
        on_started = Mock()
        with patch.object(subprocess, "Popen", side_effect=AssertionError("simulated refusal reached Popen")) as popen, \
                simulated_host(**host) as load, self.assertRaises(darwin.Stop) as caught:
            darwin.run_process(CHILD + ["raise SystemExit(0)"], stage=self.stage, label="refused", clock=clock,
                               stage_end=clock.end, env=ENVIRONMENT, on_started=on_started)
        popen.assert_not_called()
        on_started.assert_not_called()
        self.assertEqual(caught.exception.as_dict(),
                         {"code": "OTRAY-E-BACKEND", "reason": PREFIX + reason, "state": "REJECTED"})
        self.assertFalse(hasattr(caught.exception, "process_record"))
        self.assertEqual(list(self.stage.iterdir()), [])
        return load

    def test_real_precondition_holds_on_this_host(self):
        """Starts nothing: reads this process's real sys.platform, machine and sysctl.proc_translated."""
        self.assertEqual(sys.platform, "darwin")
        self.assertEqual(os.uname().machine, "arm64")
        self.assertEqual(darwin.proc_translated(), 0)
        self.assertIsNone(darwin.darwin_precondition())

    def test_simulated_native_boundary_is_admitted(self):
        """Starts nothing (simulated): the simulated native boundary passes, so each MC17 case fails on one condition."""
        calls = []
        with simulated_host(library=simulated_libsystem(0, calls=calls)):
            self.assertEqual(darwin.proc_translated(), 0)
            self.assertIsNone(darwin.darwin_precondition())
        self.assertEqual(calls, [(b"sysctl.proc_translated", None, 0)] * 2)

    def test_mc17_simulated_non_darwin_platform_stops_before_any_start(self):
        """Starts nothing (simulated): sys.platform is linux; Popen is patched and never called."""
        load = self.assert_refused_before_start("sys.platform is not darwin", platform="linux")
        load.assert_not_called()

    def test_mc17_simulated_machine_other_than_arm64_stops_before_any_start(self):
        """Starts nothing (simulated): os.uname().machine is x86_64; Popen is patched and never called."""
        load = self.assert_refused_before_start("os.uname().machine is not arm64", machine="x86_64")
        load.assert_not_called()

    def test_mc17_simulated_translated_process_stops_before_any_start(self):
        """Starts nothing (simulated): sysctlbyname reports sysctl.proc_translated 1; Popen is never called."""
        calls = []
        load = self.assert_refused_before_start("sysctl.proc_translated is not 0",
                                                library=simulated_libsystem(1, calls=calls))
        load.assert_called_once_with()
        self.assertEqual(calls, [(b"sysctl.proc_translated", None, 0)])

    def test_mc17_simulated_unreadable_sysctl_fails_closed_before_any_start(self):
        """Starts nothing (simulated): sysctl.proc_translated is unreadable in four ways; Popen is never called."""
        cases = {"sysctlbyname returns -1": {"library": simulated_libsystem(status=-1)},
                 "value shorter than an int": {"library": simulated_libsystem(0, size=2)},
                 "libSystem cannot be loaded": {"load_error": OSError("simulated dlopen failure")},
                 "no sysctlbyname symbol": {"library": types.SimpleNamespace()}}
        for name, host in cases.items():
            with self.subTest(name):
                self.assert_refused_before_start("sysctl.proc_translated is unreadable", **host)


class DarwinGroupProbeObservation(unittest.TestCase):
    """Development observation of this host, not a control: killpg(pgid, 0) on an exited, unreaped member."""

    def test_observation_killpg_reports_eperm_while_the_group_holds_only_an_unreaped_child(self):
        """Starts one child directly with subprocess.Popen in a new session; it blocks reading stdin,
        exits when stdin closes, and is reaped only after the observation."""
        process = subprocess.Popen(CHILD + ["import sys; sys.stdin.read()"], stdin=subprocess.PIPE,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   env=ENVIRONMENT, start_new_session=True)
        try:
            live = _killpg_errno(process.pid)
            process.stdin.close()
            exited, deadline = live, time.monotonic() + 5
            while exited == 0 and time.monotonic() < deadline:
                time.sleep(0.005)
                exited = _killpg_errno(process.pid)
            unreaped = [_killpg_errno(process.pid) for _ in range(3)]
            with self.assertRaises(PermissionError):
                darwin.group_exists(process.pid)
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
        reaped = _killpg_errno(process.pid)
        self.assertEqual((live, exited, unreaped, reaped), (0, errno.EPERM, [errno.EPERM] * 3, errno.ESRCH))
        self.assertFalse(darwin.group_exists(process.pid))


class DarwinSupervisorChildren(StageCase):
    """Development cases with real non-Node Python children through the Darwin run_process."""

    def test_positive_child_exits_zero_with_the_original_receipt(self):
        """Starts one child, which writes one line to stdout and one to stderr and exits 0."""
        argv = CHILD + ["import sys; sys.stdout.write('positive-out\\n'); sys.stderr.write('positive-err\\n')"]
        clock = darwin.Clock(total_ms=20000)
        record = darwin.run_process(argv, stage=self.stage, label="positive", clock=clock,
                                    stage_end=clock.end, env=ENVIRONMENT, on_started=self.started)
        self.assertEqual(set(record), RECEIPT_KEYS)
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(self.starts[0]["pid"], record["pid"])
        self.assertEqual(record["process_group"], record["pid"])
        self.assertEqual((record["argv"], record["cwd"], record["environment"], record["label"]),
                         (argv, str(self.stage.resolve()), ENVIRONMENT, "positive"))
        self.assertEqual(record["returncode"], 0)
        self.assertIsNone(record["error"])
        self.assertEqual(record["cleanup"],
                         {"passed": True, "process_group_absent": True, "reaped": True, "elapsed_ms": 0})
        self.assertIs(record["handles_closed"], True)
        self.assertEqual((self.stage / "positive.stdout.log").read_bytes(), b"positive-out\n")
        self.assertEqual((self.stage / "positive.stderr.log").read_bytes(), b"positive-err\n")
        self.assertEqual((record["observed_log_bytes"], record["retained_log_bytes"]), (26, 26))
        self.assertEqual((self.stage / "positive.process.json").read_bytes(), darwin.json_bytes(record))
        self.assertEqual(sorted(path.name for path in self.stage.iterdir()),
                         ["positive.process.json", "positive.stderr.log", "positive.stdout.log"])
        self.assertLessEqual(record["start_monotonic"], record["end_monotonic"])
        self.assertFalse(darwin.group_exists(record["pid"]))

    def test_mc12_development_descendant_left_in_the_group_is_refused_and_terminated(self):
        """Starts one child, which starts one grandchild in its own process group (no setsid; standard
        streams on /dev/null), prints the grandchild's pid and exits 0 while the grandchild sleeps
        for at most 15 s."""
        code = ("import subprocess, sys; "
                "grandchild = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', 'import time; time.sleep(15)'], "
                "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                "print(grandchild.pid, flush=True)")
        clock = darwin.Clock(total_ms=20000)
        with self.assertRaises(darwin.Stop) as caught:
            darwin.run_process(CHILD + [code], stage=self.stage, label="descendant", clock=clock,
                               stage_end=clock.end, env=ENVIRONMENT, on_started=self.started)
        error = caught.exception
        self.assertEqual(error.as_dict(), {"code": "OTRAY-E-BACKEND", "state": "REJECTED",
                                           "reason": "Child exited while an owned descendant remained"})
        record = error.process_record
        self.assertEqual(set(record), RECEIPT_KEYS)
        self.assertEqual(record["error"], error.as_dict())
        self.assertEqual(record["returncode"], 0)
        self.assertEqual(len(self.starts), 1)
        self.assert_cleanup(record)
        stdout = (self.stage / "descendant.stdout.log").read_bytes()
        self.assertEqual((self.stage / "descendant.stderr.log").read_bytes(), b"")
        self.assertEqual(record["observed_log_bytes"], len(stdout))
        grandchild = int(stdout)
        self.assertNotEqual(grandchild, record["pid"])
        self.assertTrue(_gone(grandchild), "The grandchild is still present after the group cleanup")

    def test_mc13_development_timeout_cleanup(self):
        """Starts one child, which sleeps for at most 15 s; a 300 ms stage deadline ends it, with no retry."""
        clock = darwin.Clock(total_ms=20000)
        stage_end = clock.started + 0.3
        with patch.object(subprocess, "Popen", wraps=subprocess.Popen) as popen, \
                self.assertRaises(darwin.Stop) as caught:
            darwin.run_process(CHILD + [SLEEPER], stage=self.stage, label="timeout", clock=clock,
                               stage_end=stage_end, env=ENVIRONMENT, on_started=self.started)
        error = caught.exception
        self.assertEqual(error.as_dict(), {"code": "OTRAY-E-RESOURCE", "state": "TIMEOUT",
                                           "reason": "Monotonic stage or transaction deadline"})
        record = error.process_record
        self.assertEqual(set(record), RECEIPT_KEYS)
        self.assertEqual(record["error"], error.as_dict())
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(record["returncode"], -signal.SIGTERM)
        self.assert_cleanup(record)
        self.assertGreaterEqual(record["end_monotonic"], stage_end)
        self.assertIsNone(clock.cancel_observed)

    def test_mc13_development_cancellation_cleanup(self):
        """Starts one child, which sleeps for at most 15 s; cancel_after_ms=150 cancels it, with no retry."""
        clock = darwin.Clock(total_ms=20000)
        with patch.object(subprocess, "Popen", wraps=subprocess.Popen) as popen, \
                self.assertRaises(darwin.Stop) as caught:
            darwin.run_process(CHILD + [SLEEPER], stage=self.stage, label="cancellation", clock=clock,
                               stage_end=clock.end, env=ENVIRONMENT, on_started=self.started,
                               cancel_after_ms=150)
        error = caught.exception
        self.assertEqual(error.as_dict(), {"code": "OTRAY-E-CANCELLED", "state": "CANCELLED",
                                           "reason": "Controlled cancellation after child start"})
        record = error.process_record
        self.assertEqual(set(record), RECEIPT_KEYS | {"cancellation_completion_ms"})
        self.assertEqual(record["error"], error.as_dict())
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(record["returncode"], -signal.SIGTERM)
        self.assert_cleanup(record)
        self.assertLessEqual(record["cancellation_completion_ms"], darwin.LIMITS["cleanup_ms"])
        self.assertGreaterEqual((clock.cancel_observed - record["start_monotonic"]) * 1000, 150)


if __name__ == "__main__":
    unittest.main()
