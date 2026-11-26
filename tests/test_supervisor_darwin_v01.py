"""Development tests of the Darwin supervisor variant (S4, as amended); standard library only.

Contract ``ontokin.current-host-readback/0.2.0``, profile ``darwin-arm64-v1``, section 5, as
amended by P33-AMENDMENT-001 (design revision 4), and section 4.1 of the C271-P33
implementation plan as that amendment supersedes it.  These are development tests written with
the implementation.  They are not the frozen controls, which an independent author freezes.

Process starts: every started process is a Python process; no Node, ldd or codesign process
starts.  Children start as ``sys.executable -I -S -B -c <fixed code>``; ``-B`` keeps them from
writing bytecode into the interpreter installation.  In MC39 (a) the child forks Python
descendants of its own.  Each test's docstring says what it starts.  The simulated cases (MC17,
MC39 (b)) say so in their names.  After each test, a guard applies the amended rule, EPERM
means present: every tracked process group must answer ESRCH.  The tests that start real
children need the darwin-arm64-v1 executor; on another host they fail visibly, never as a skip.
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
import select
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
STDIN_WAITER = "import sys; sys.stdin.read()"
# MC39 (a): the child forks a descendant, which forks its own child and moves itself into its own
# process group.  That child exits at once and is never reaped, so it stays in the owned group.
ESCAPING = (
    "import os, sys, time\n"
    "read_end, write_end = os.pipe()\n"
    "if os.fork() == 0:\n"
    "    os.close(read_end)\n"
    "    null = os.open(os.devnull, os.O_RDWR)\n"
    "    for fd in (0, 1, 2):\n"
    "        os.dup2(null, fd)\n"
    "    os.close(null)\n"
    "    child = os.fork()\n"
    "    if child == 0:\n"
    "        os._exit(0)\n"
    "    os.setpgid(0, 0)\n"
    "    os.write(write_end, ('%d %d\\n' % (os.getpid(), child)).encode())\n"
    "    os.close(write_end)\n"
    "    time.sleep(15)\n"
    "    os._exit(0)\n"
    "os.close(write_end)\n"
    "sys.stdout.write(os.read(read_end, 64).decode())\n")
IMPORTED = ("Clock", "Stop", "LIMITS", "inventory", "json_bytes", "_reap")
REIMPLEMENTED = ("group_exists", "terminate_group", "run_process")
# The original receipt: the initial record of run_process plus "end_monotonic", which is always
# added; an observed cancellation adds "cancellation_completion_ms".
RECEIPT_KEYS = frozenset({"argv", "cwd", "environment", "label", "start_monotonic", "pid",
                          "process_group", "returncode", "observed_log_bytes", "retained_log_bytes",
                          "cleanup", "handles_closed", "error", "end_monotonic"})
CLEANUP_KEYS = frozenset({"passed", "elapsed_ms", "process_group_absent", "reaped"})
PREFIX = "Cannot establish the Darwin arm64 native precondition: "
CEILING = "Owned process group cleanup exceeded stage or transaction ceiling"
ORIGINAL_PRECONDITION = (
    "    libc = ctypes.CDLL(None, use_errno=True)\n",
    "    if libc.prctl(36, 1, 0, 0, 0) != 0:\n",
    '        raise Stop("OTRAY-E-BACKEND", "Cannot establish Linux descendant reaping")\n')
DARWIN_PRECONDITION = (
    "    unmet = darwin_precondition()\n",
    "    if unmet is not None:\n",
    '        raise Stop("OTRAY-E-BACKEND", "Cannot establish the Darwin arm64 native precondition: " + unmet)\n')
# The five change sites of P33-AMENDMENT-001 section 3.2, as exact line edits of the original
# function sources: (function, site, the line right before the edit, original lines, new lines).
SITES = (
    ("run_process", 1, '        raise ValueError("A private stage and explicit argv are required")\n',
     ORIGINAL_PRECONDITION, DARWIN_PRECONDITION),
    ("group_exists", 2, "        return True\n",
     (), ("    except PermissionError:\n", "        return True\n")),
    ("terminate_group", 3, "        os.killpg(process.pid, signal.SIGTERM)\n",
     ("    except ProcessLookupError:\n",), ("    except (ProcessLookupError, PermissionError):\n",)),
    ("terminate_group", 4, "            os.killpg(process.pid, signal.SIGKILL)\n",
     ("        except ProcessLookupError:\n",), ("        except (ProcessLookupError, PermissionError):\n",)),
    ("terminate_group", 5, "        os.killpg(process.pid, signal.SIGKILL)\n",
     ("    except ProcessLookupError:\n",), ("    except (ProcessLookupError, PermissionError):\n",)),
)
SYSCTLBYNAME = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p,
                                ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t)


def _tokens(source):
    return [[tokenize.tok_name[token.type], token.string, list(token.start), list(token.end)]
            for token in tokenize.generate_tokens(io.StringIO(source).readline)]


def _apply_sites(name, lines):
    """The original lines of ``name`` with its sites applied, and the rows each site occupies."""
    edits = []
    for function, number, anchor, old, new in SITES:
        if function != name:
            continue
        found = [index for index, line in enumerate(lines) if line == anchor]
        if len(found) != 1:
            raise AssertionError("The anchor of site %d does not occur exactly once" % number)
        start = found[0] + 1
        if tuple(lines[start:start + len(old)]) != old:
            raise AssertionError("The original text of site %d differs" % number)
        edits.append((start, number, old, new))
    amended, rows, shift = list(lines), {}, 0
    for start, number, old, new in sorted(edits):
        at = start + shift
        amended[at:at + len(old)] = list(new)
        rows[number] = {"original": (start + 1, start + len(old)), "darwin": (at + 1, at + len(new)),
                        "shift": len(new) - len(old)}
        shift += len(new) - len(old)
    return amended, rows


def _partition(tokens, ranges):
    """Unchanged tokens and one token list per site, by the rows that each site occupies."""
    unchanged, sites = [], {number: [] for number in ranges}
    for token in tokens:
        first, last = token[2][0], token[3][0]
        owner = [number for number, (low, high) in ranges.items() if low <= first and last <= high]
        if owner:
            sites[owner[0]].append(token)
        elif any(not (last < low or first > high) for low, high in ranges.values()):
            raise AssertionError("A token crosses a change-site boundary")
        else:
            unchanged.append(token)
    return unchanged, sites


def token_comparison():
    """MC14 development comparison of the three re-implemented functions, token by token.

    Compared: every token that ``tokenize.generate_tokens`` yields for ``inspect.getsource`` of
    ``run_process``, ``group_exists`` and ``terminate_group`` in both modules, by token type,
    string, start and end.  Comments, docstrings and the NL, NEWLINE, INDENT and DEDENT tokens
    are compared like every other token.  Ignored: nothing.  Tokens outside the five sites of
    ``SITES`` must be equal, with rows after an inserted site mapped back by its line count; the
    Darwin source must equal the original with exactly those five edits applied.
    """
    functions, sites, differences, source_diff = {}, [], {}, {}
    for name in REIMPLEMENTED:
        original_source = inspect.getsource(getattr(supervisor, name))
        darwin_source = inspect.getsource(getattr(darwin, name))
        amended, rows = _apply_sites(name, original_source.splitlines(keepends=True))
        original_tokens, darwin_tokens = _tokens(original_source), _tokens(darwin_source)
        original_unchanged, original_sites = _partition(
            original_tokens, {number: value["original"] for number, value in rows.items()})
        darwin_unchanged, darwin_sites = _partition(
            darwin_tokens, {number: value["darwin"] for number, value in rows.items()})

        def original_row(row):
            return row - sum(value["shift"] for value in rows.values() if value["darwin"][1] < row)

        mapped = [[kind, text, [original_row(start[0]), start[1]], [original_row(end[0]), end[1]]]
                  for kind, text, start, end in darwin_unchanged]
        matcher = difflib.SequenceMatcher(None, [tuple(token[:2]) for token in original_tokens],
                                          [tuple(token[:2]) for token in darwin_tokens], autojunk=False)
        differences[name] = [{"tag": tag, "original": original_tokens[i1:i2], "darwin": darwin_tokens[j1:j2]}
                             for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]
        functions[name] = {
            "original": {"function": "prototypes.static_tray_v01.supervisor." + name,
                         "source_sha256": hashlib.sha256(original_source.encode("utf-8")).hexdigest(),
                         "token_count": len(original_tokens)},
            "darwin": {"function": darwin.__name__ + "." + name,
                       "source_sha256": hashlib.sha256(darwin_source.encode("utf-8")).hexdigest(),
                       "token_count": len(darwin_tokens)},
            "unchanged_token_count": len(original_unchanged),
            "unchanged_tokens_equal": mapped == original_unchanged,
            "source_equals_original_with_sites_applied": darwin_source == "".join(amended),
            "difflib_nonequal_opcodes": len(differences[name])}
        for number, value in sorted(rows.items()):
            before, after = original_sites[number], darwin_sites[number]
            sites.append({"site": number, "function": name,
                          "original_rows": list(value["original"]), "darwin_rows": list(value["darwin"]),
                          "original_tokens": before, "darwin_tokens": after,
                          "differs": [token[:2] for token in before] != [token[:2] for token in after],
                          "adds_PermissionError": (not any(token[1] == "PermissionError" for token in before)
                                                   and any(token[1] == "PermissionError" for token in after))})
        source_diff[name] = list(difflib.unified_diff(original_source.splitlines(keepends=True),
                                                      darwin_source.splitlines(keepends=True),
                                                      "supervisor." + name, "supervisor_darwin_v01." + name))
    sites.sort(key=lambda site: site["site"])
    return {
        "kind": "MC14 development token comparison of three functions; not a frozen control",
        "rule": "P33-AMENDMENT-001 section 3.2: exactly five change sites, four of them EPERM handlings; "
                "nothing else differs, docstrings and comments included",
        "compared": "every token of tokenize.generate_tokens over inspect.getsource of each function, by type, "
                    "string, start and end; comments, docstrings and NL, NEWLINE, INDENT and DEDENT included",
        "ignored": "nothing",
        "functions": functions,
        "sites": sites,
        "change_site_count": len(sites),
        "eperm_handling_sites": [site["site"] for site in sites if site["adds_PermissionError"]],
        "difflib_differences": differences,
        "source_diff": source_diff,
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


def _absent_within(group, seconds):
    """True once ``killpg(group, 0)`` answers ESRCH; success and EPERM mean present (amended rule)."""
    deadline = time.monotonic() + seconds
    while True:
        if _killpg_errno(group) == errno.ESRCH:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


def _gone(pid, seconds=2.0):
    """True once ``kill(pid, 0)`` answers ESRCH; success and EPERM mean present (amended rule)."""
    deadline = time.monotonic() + seconds
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


class GuardedCase(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="darwin-supervisor-")
        self.addCleanup(temporary.cleanup)
        self.stage = Path(temporary.name) / "stage"
        self.stage.mkdir()
        self.starts, self.groups = [], []
        self.addCleanup(self.no_group_left)

    def started(self, record):
        self.starts.append(record)
        self.groups.append(record["process_group"])

    def no_group_left(self):
        """Guard after each test, with the amended rule (EPERM means present): every tracked group
        must answer ESRCH within 2 s.  One that does not is sent SIGKILL and reported."""
        left = []
        for group in self.groups:
            if _absent_within(group, 2.0):
                continue
            left.append((group, _killpg_errno(group)))
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(group, signal.SIGKILL)
            _absent_within(group, 2.0)
        if left:
            self.fail("Tracked process groups did not answer ESRCH; the guard sent SIGKILL: %r" % left)

    def assert_cleanup(self, record):
        cleanup = record["cleanup"]
        self.assertEqual(set(cleanup), CLEANUP_KEYS)
        self.assertIs(cleanup["passed"], True)
        self.assertIs(cleanup["process_group_absent"], True)
        self.assertIs(cleanup["reaped"], True)
        self.assertEqual(darwin.LIMITS["cleanup_ms"], 2000)
        self.assertLessEqual(cleanup["elapsed_ms"], darwin.LIMITS["cleanup_ms"])
        self.assertIs(record["handles_closed"], True)
        self.assertEqual(_killpg_errno(record["process_group"]), errno.ESRCH)

    def assert_ceiling_stop(self, error):
        self.assertEqual(error.as_dict(), {"code": "OTRAY-E-BACKEND", "reason": CEILING, "state": "REJECTED"})
        record = error.process_record
        self.assertEqual(set(record), RECEIPT_KEYS)
        self.assertEqual(record["cleanup"], {"passed": False, "reason": CEILING})
        self.assertEqual(record["error"], error.as_dict())
        self.assertIs(record["handles_closed"], True)
        self.assertGreaterEqual(record["end_monotonic"] - record["start_monotonic"],
                                darwin.LIMITS["cleanup_ms"] / 1000)
        self.assertEqual((self.stage / (record["label"] + ".process.json")).read_bytes(), darwin.json_bytes(record))
        return record


class DarwinSupervisorSource(unittest.TestCase):
    """Development checks of the variant's source, imports and signatures; they start nothing."""

    def test_mc14_development_token_comparison_shows_exactly_the_five_change_sites(self):
        """Starts nothing: tokenizes inspect.getsource of run_process, group_exists and terminate_group
        in both modules and compares them."""
        result = token_comparison()
        self.assertEqual(result["ignored"], "nothing")
        self.assertEqual(sorted(result["functions"]), ["group_exists", "run_process", "terminate_group"])
        for name, value in result["functions"].items():
            self.assertTrue(value["unchanged_tokens_equal"], name)
            self.assertTrue(value["source_equals_original_with_sites_applied"], name)
        self.assertEqual(result["change_site_count"], 5)
        self.assertEqual([(site["site"], site["function"], site["original_rows"], site["darwin_rows"])
                          for site in result["sites"]],
                         [(1, "run_process", [7, 9], [7, 9]), (2, "group_exists", [5, 4], [5, 6]),
                          (3, "terminate_group", [6, 6], [6, 6]), (4, "terminate_group", [19, 19], [19, 19]),
                          (5, "terminate_group", [35, 35], [35, 35])])
        self.assertTrue(all(site["differs"] for site in result["sites"]))
        self.assertEqual(result["eperm_handling_sites"], [2, 3, 4, 5])

    def test_imported_names_and_signatures(self):
        """Starts nothing: the six imported names are the original objects; the three re-implemented
        functions are this module's own, with the original signatures."""
        for name in IMPORTED:
            self.assertIs(getattr(darwin, name), getattr(supervisor, name), name)
        for name in REIMPLEMENTED:
            function = getattr(darwin, name)
            self.assertIsNot(function, getattr(supervisor, name), name)
            self.assertEqual(function.__module__, darwin.__name__, name)
            self.assertEqual(inspect.signature(function), inspect.signature(getattr(supervisor, name)), name)

    def test_body_globals_bind_to_the_original_objects_or_the_reimplementations(self):
        """Starts nothing: each global that the three functions load is the original object, except
        group_exists and terminate_group, which resolve to this module's re-implementations."""
        expected = {"run_process": ({"ctypes"}, {"darwin_precondition"}),
                    "group_exists": (set(), {"PermissionError"}),
                    "terminate_group": (set(), {"PermissionError"})}
        for name, (removed, added) in expected.items():
            original, variant = _global_loads(getattr(supervisor, name)), _global_loads(getattr(darwin, name))
            self.assertEqual(original - variant, removed, name)
            self.assertEqual(variant - original, added, name)
            for symbol in sorted(original & variant):
                if symbol in REIMPLEMENTED:
                    self.assertIs(_resolve(darwin, symbol), getattr(darwin, symbol), (name, symbol))
                    self.assertIsNot(_resolve(darwin, symbol), _resolve(supervisor, symbol), (name, symbol))
                else:
                    self.assertIs(_resolve(darwin, symbol), _resolve(supervisor, symbol), (name, symbol))
        self.assertIs(_resolve(darwin, "PermissionError"), builtins.PermissionError)
        self.assertIs(_resolve(darwin, "darwin_precondition"), darwin.darwin_precondition)


class DarwinPrecondition(GuardedCase):
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


class DarwinGroupProbe(GuardedCase):
    """MC37 and MC38 development cases, with a real child started directly with subprocess.Popen."""

    def start_waiter(self):
        """One child in a new session; it blocks reading stdin and exits 0 when stdin closes."""
        process = subprocess.Popen(CHILD + [STDIN_WAITER], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, env=ENVIRONMENT, start_new_session=True)
        self.groups.append(process.pid)
        self.addCleanup(self.reap, process)
        return process

    @staticmethod
    def reap(process):
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)

    def exit_unreaped(self, process):
        """Closes stdin and waits for kqueue's NOTE_EXIT for the child, which leaves it unreaped."""
        queue = select.kqueue()
        try:
            queue.control([select.kevent(process.pid, filter=select.KQ_FILTER_PROC,
                                         flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                                         fflags=select.KQ_NOTE_EXIT)], 0)
            process.stdin.close()
            events = queue.control(None, 1, 5.0)
        finally:
            queue.close()
        self.assertEqual([(event.ident, event.filter, bool(event.fflags & select.KQ_NOTE_EXIT)) for event in events],
                         [(process.pid, select.KQ_FILTER_PROC, True)])
        self.assertIsNone(process.returncode)
        self.assertEqual(_killpg_errno(process.pid), errno.EPERM,
                         "The unreaped group did not answer EPERM, so this case does not tell the rules apart")

    def test_mc37_development_group_exists_counts_an_exited_unreaped_child_as_present(self):
        """Starts one child directly with subprocess.Popen in a new session; it exits when stdin closes,
        and kqueue NOTE_EXIT establishes the exit without reaping it."""
        process = self.start_waiter()
        self.assertIs(darwin.group_exists(process.pid), True)
        self.exit_unreaped(process)
        self.assertIs(darwin.group_exists(process.pid), True)
        self.assertEqual(process.wait(timeout=5), 0)
        self.assertEqual(_killpg_errno(process.pid), errno.ESRCH)
        self.assertIs(darwin.group_exists(process.pid), False)

    def test_mc38_development_terminate_group_on_an_exited_unreaped_child(self):
        """Starts one child directly with subprocess.Popen in a new session, as in MC37; once NOTE_EXIT
        establishes its exit, terminate_group runs on its group.  os.killpg is wrapped only to record
        each call's outcome; every call goes to the real function."""
        process = self.start_waiter()
        self.exit_unreaped(process)
        real, calls = os.killpg, []

        def recorded(group, sig):
            try:
                real(group, sig)
            except OSError as error:
                calls.append((sig, error.errno))
                raise
            calls.append((sig, 0))

        clock = darwin.Clock(total_ms=20000)
        with patch.object(os, "killpg", recorded):
            receipt = darwin.terminate_group(process, clock)
        self.assertEqual(set(receipt), CLEANUP_KEYS)
        self.assertEqual((receipt["passed"], receipt["process_group_absent"], receipt["reaped"]), (True, True, True))
        self.assertLessEqual(receipt["elapsed_ms"], darwin.LIMITS["cleanup_ms"])
        self.assertEqual(calls[0], (signal.SIGTERM, errno.EPERM))
        self.assertEqual(calls[1:], [(0, errno.ESRCH)] * (len(calls) - 1))
        self.assertEqual(process.returncode, 0)
        self.assertEqual(_killpg_errno(process.pid), errno.ESRCH)


class DarwinSupervisorChildren(GuardedCase):
    """Development cases with real Python children through the Darwin run_process."""

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
        self.assertEqual(_killpg_errno(record["pid"]), errno.ESRCH)

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
        self.assertTrue(_gone(grandchild), "The grandchild did not answer ESRCH after the group cleanup")

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

    def test_mc39a_development_lasting_eperm_from_an_escaped_descendant_fails_at_the_ceiling(self):
        """Starts one child through run_process.  The child forks a descendant, which forks its own child,
        moves itself into its own process group and never reaps that child; the child exits at once and
        stays unreaped in the owned group.  The descendant sleeps for at most 15 s; the test's own
        teardown kills it, and launchd then reaps both."""
        log, escaped = self.stage / "escaping.stdout.log", {}

        def read_pids():
            if "descendant" not in escaped:
                escaped["descendant"], escaped["child"] = (int(value) for value in log.read_bytes().split())
                self.groups.append(escaped["descendant"])

        def teardown():
            """The control's own teardown: SIGKILL to the escaped descendant's own group, once."""
            if escaped.get("removed"):
                return
            with contextlib.suppress(OSError, ValueError):
                read_pids()
            if "descendant" in escaped:
                escaped["removed"] = True
                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.killpg(escaped["descendant"], signal.SIGKILL)

        self.addCleanup(teardown)
        clock = darwin.Clock(total_ms=20000)
        with patch.object(subprocess, "Popen", wraps=subprocess.Popen) as popen, \
                self.assertRaises(darwin.Stop) as caught:
            darwin.run_process(CHILD + [ESCAPING], stage=self.stage, label="escaping", clock=clock,
                               stage_end=clock.end, env=ENVIRONMENT, on_started=self.started)
        read_pids()
        record = self.assert_ceiling_stop(caught.exception)
        self.assertEqual(record["returncode"], 0)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(len(self.starts), 1)
        group = record["process_group"]
        self.assertEqual(_killpg_errno(group), errno.EPERM)
        os.kill(escaped["descendant"], 0)
        teardown()
        self.assertTrue(_gone(escaped["descendant"]), "The escaped descendant did not answer ESRCH")
        self.assertTrue(_gone(escaped["child"]), "Its unreaped child did not answer ESRCH")
        self.assertTrue(_absent_within(group, 2.0))
        self.assertTrue(_absent_within(escaped["descendant"], 2.0))

    def test_mc39b_simulated_lasting_eperm_probe_fails_at_the_ceiling(self):
        """Starts one child through run_process, which sleeps for at most 15 s; a 300 ms stage deadline
        ends it.  Simulated: os.killpg(pid, 0) fails with PermissionError at the os.killpg boundary,
        while every real signal passes through to the real function."""
        real, calls = os.killpg, []

        def probe_refused(group, sig):
            calls.append(sig)
            if sig == 0:
                raise PermissionError(errno.EPERM, "simulated refusal of killpg(pgid, 0)")
            return real(group, sig)

        clock = darwin.Clock(total_ms=20000)
        stage_end = clock.started + 0.3
        with patch.object(subprocess, "Popen", wraps=subprocess.Popen) as popen, \
                patch.object(os, "killpg", probe_refused), self.assertRaises(darwin.Stop) as caught:
            darwin.run_process(CHILD + [SLEEPER], stage=self.stage, label="refused-probe", clock=clock,
                               stage_end=stage_end, env=ENVIRONMENT, on_started=self.started)
        record = self.assert_ceiling_stop(caught.exception)
        self.assertEqual(record["returncode"], -signal.SIGTERM)
        self.assertEqual([sig for sig in calls if sig], [signal.SIGTERM, signal.SIGKILL, signal.SIGKILL])
        self.assertGreater(calls.count(0), 0)
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(len(self.starts), 1)
        self.assertEqual(_killpg_errno(record["process_group"]), errno.ESRCH)


if __name__ == "__main__":
    unittest.main()
