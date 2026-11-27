#!/usr/bin/env python3
"""Unit-stage log outcomes and the baseline comparison for gate MR of C271-P36 (MR-PLAN section 5).

Two commands, one parser; each command writes one absent output file:

  collect  Reads one unit-stage log, the combined stdout and stderr of
           "python -B -m unittest discover -s tests -v" that tools/check_local.py keeps as
           <output>/logs/unit-tests.log, bound by the SHA-256 given on the command line. It
           gives one record for each raw test ID as unittest prints it (module.Class.method),
           with the outcome (passed, failure, error, skipped, expected_failure or
           unexpected_success), the first line of the reason of each failure or error, the
           skip reason, the failing and skipped subtests, and the class-level and module-level
           events that unittest reports under its own descriptions (setUpClass (module.Class),
           tearDownModule (module), ...); a failed import is the raw ID
           unittest.loader._FailedTest.<module>. The parsed counts must equal the log's own
           "Ran N tests" line and its final OK / FAILED (...) line, and every listing entry must
           belong to a status line of the progress section; otherwise the log is refused.
           With --expect ID=OUTCOME, exact IDs must have exact outcomes (for example MC23's
           methods). With --inventory and its digest, the started tests are joined with a
           runtime-discovery document of MH's discover_inventory.py (MC28's "the log against the
           same list"): every started raw ID must be in it and every ID in it must start, in
           discovery order.

  compare  Applies OK-ENG-009 section 3 item 4 to a baseline and a candidate: each log and each
           summary.json bound by SHA-256, the summary naming its log by digest. It lists the
           unchanged results per outcome, the new tests that do not pass, the tests that no
           longer fail, every different outcome, reason or subtest set, and the added and removed
           IDs; and, side by side, each step's status, report summaries, pending external cases
           and not_executed_steps, with every differing report summary listed. It classifies
           nothing as exempt. An attribution file supplied by the operational freeze states, for
           one exact ID, the test's complete not-passing record (outcome, occurrences, own events,
           failing and skipped subtests) in one declared form, raw or normalized; it matches
           only when the candidate's record equals that statement exactly, and the output lists
           what differs.

How the log is read. The tail is anchored first: the last separator line of 70 "-", then
"Ran N test(s) in S.SSSs", an empty line and the result line; text after it is kept as trailing
text. The progress section is read as unittest 3.12's TextTestResult writes it, with its
_newline state emulated: a start "<description> ... ", a status written directly after it, the
"  <subtest description> ... STATUS" lines of failing or skipped subtests, a status line that
repeats the description, and the fixture lines. Text that the tests or their children wrote
into the same file (block-buffered stdout, warnings, child output) is kept as noise, including
noise glued in front of a runner line or between a start and its status. A status that does not
directly follow its start is taken only when exactly one candidate exists among the lines up to
the next runner line (a line that is a status, or ends with one); two or more candidates refuse
the log as ambiguous, whatever their values, since a choice would be a guess.
The listing (the ERROR and FAIL entries, then the unexpected successes) must consist of exactly
the expected headers in the expected order; every header text must occur exactly as often as
expected, so the split is unique.

The reason's first line: in a listing entry's traceback text, the first line of the exception
text of the last block of the chain (blocks are separated by the two standard chain lines,
each between empty lines); the exception text starts at the first line after the frames, which
are the lines indented by two spaces after "Traceback (most recent call last):".

Launch:  python3 -I -S -B unit_log_outcomes.py collect --log LOG --log-sha256 H --output OUT
A start without -B refuses before any other import (N-09). Nothing is started; only OUT is written.
"""
import sys


def _missing_dash_b(flags=None):
    """N-09: every start of the framework interpreter carries -B; True when this one does not."""
    return not (sys.flags if flags is None else flags).dont_write_bytecode


if __name__ == "__main__" and _missing_dash_b():
    sys.stderr.write('{"schema": "ontokin.c271.p36-tool-refusal/1", "tool": "unit_log_outcomes.py", '
                     '"state": "REFUSED", "refusal": {"rule": "PYTHON", "reason": "Run with -B: every start '
                     'of the framework interpreter writes no bytecode (N-09)"}}\n')
    raise SystemExit(2)

import argparse  # noqa: E402  (after the -B check on purpose)
import ast  # noqa: E402
from collections import Counter  # noqa: E402
from datetime import datetime, timezone  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import stat  # noqa: E402
import time  # noqa: E402

SCHEMA = "ontokin.c271.p36-unit-log-outcomes/2"
COMPARISON_SCHEMA = "ontokin.c271.p36-unit-log-comparison/2"
ATTRIBUTIONS_SCHEMA = "ontokin.c271.p36-attributions/2"
DISCOVERY_SCHEMA = "ontokin.c271.p35-runtime-discovery/2"
REFUSAL_SCHEMA = "ontokin.c271.p36-tool-refusal/1"
FAILURE_SCHEMA = "ontokin.c271.p36-tool-failure/1"
SUMMARY_SCHEMA = "ontokin.local-checks/0.1"
NORMALIZATION = "ontokin.c271.p36-reason-normalization/2"
ATTRIBUTION_FORMS = ("raw", "normalized")
TOOL = "unit_log_outcomes.py"
UNIT_STEP = "unit-tests"
LOG_LIMIT = 512 * 1024 * 1024
SUMMARY_LIMIT = 64 * 1024 * 1024
ATTRIBUTIONS_LIMIT = 4 * 1024 * 1024
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
EXIT_OK, EXIT_DIFFERS, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3

SEPARATOR1, SEPARATOR2 = "=" * 70, "-" * 70
CHAIN_LINES = ("During handling of the above exception, another exception occurred:",
               "The above exception was the direct cause of the following exception:")
TRACEBACK_HEADER = "Traceback (most recent call last):"
INFO_KEYS = ("failures", "errors", "skipped", "expected failures", "unexpected successes")
OUTCOMES = ("passed", "failure", "error", "skipped", "expected_failure", "unexpected_success")
NOT_PASSING = frozenset(("failure", "error", "unexpected_success"))
FIXTURES = ("setUpClass", "tearDownClass", "setUpModule", "tearDownModule")
# unittest's loader names these tests after the module, which may be dotted (a module inside a test package).
SPECIAL_CLASSES = {"unittest.loader._FailedTest": "failed_import_or_load", "unittest.loader.ModuleSkipped": "module_skipped"}
# tempfile's own names with its default prefix: "tmp" and eight characters of tempfile's alphabet.
TEMP_NAME = re.compile(r"tmp[a-z0-9_]{8}")
# Characters that end a path in a reason's text; a run path is replaced only between them or "/".
PATH_DELIMITERS = " \t\r\n'\"`()[]{}<>,;:="

_SKIP = r"skipped (?:'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\")"
TOKEN = re.compile(r"(?:ok|FAIL|ERROR|expected failure|unexpected success|" + _SKIP + r")")
TOKEN_AT_END = re.compile(r"(?:ok|FAIL|ERROR|expected failure|unexpected success|" + _SKIP + r")$")
SUBTEST_TOKEN = re.compile(r"(?:FAIL|ERROR|" + _SKIP + r")")
REPEATED_TOKEN = re.compile(r"(?:FAIL|ERROR|" + _SKIP + r")")
FIXTURE_TOKEN = re.compile(r"(?:ERROR|" + _SKIP + r")")
DESCRIPTION = re.compile(r"(?P<method>[^\s()]+) \((?P<id>[^\s()]+)\)")
FIXTURE = re.compile(r"(?P<kind>setUpClass|tearDownClass|setUpModule|tearDownModule) \((?P<target>[^\s()]+)\) \.\.\. "
                     r"(?P<status>ERROR|" + _SKIP + r")$")
TAIL = re.compile(r"(?m)^-{70}\nRan (?P<ran>\d+) (?P<word>tests?) in (?P<seconds>\d+\.\d{3})s\n\n"
                  r"(?P<result>OK|FAILED|NO TESTS RAN)(?: \((?P<infos>[^\n]*)\))?\n")
SHA256 = re.compile(r"[0-9a-f]{64}")


# ---------------------------------------------------------------------------
# Common helpers (as in the MH tools; each tool of this directory carries its own copy)
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


def require_dash_b(flags=None):
    if _missing_dash_b(flags):
        raise Refusal("PYTHON", "Run with -B: every start of the framework interpreter writes no bytecode (N-09)")


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


def bound_input(path, expected, maximum, *, rule):
    """A regular file whose SHA-256 must equal the digest supplied on the command line."""
    if type(expected) is not str or SHA256.fullmatch(expected) is None:
        raise Refusal("USAGE", "Expected a lowercase SHA-256 digest for " + rule.lower(), digest=repr(expected))
    data, binding = read_regular(path, maximum, rule=rule)
    if binding["sha256"] != expected:
        raise Refusal("DIGEST", "The input differs from its supplied SHA-256", path=path, role=rule,
                      expected_sha256=expected, actual_sha256=binding["sha256"])
    return data, {"path": path, **binding}


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


def text_digest(text):
    return hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()


# ---------------------------------------------------------------------------
# The parse of one unit-stage log
# ---------------------------------------------------------------------------

class Occurrence:
    """One start of one test in the progress section, with every status event that belongs to it."""

    def __init__(self, raw_id, method, description, docline, line, order):
        self.raw_id, self.method, self.description, self.docline = raw_id, method, description, docline
        self.line, self.order = line, order
        self.events = []      # own status events, in order
        self.subtests = []    # failing or skipped subtests, in order
        self.direct = None    # the status written directly after the start, if any
        self.pending = True   # no event yet

    @property
    def full_description(self):
        return self.description + ("\n" + self.docline if self.docline else "")


def status_event(token, line):
    """A status token as an event: its status and, for a skip, the reason (the repr unittest wrote)."""
    if token.startswith("skipped "):
        try:
            reason = ast.literal_eval(token[len("skipped "):])
        except (ValueError, SyntaxError) as exc:
            raise Refusal("PARSE", "A skip reason is not a valid string literal", line=line) from exc
        return {"status": "skipped", "skip_reason": reason, "line": line}
    return {"status": token, "line": line}


def special_class(raw_id):
    """The loader's special class that names this raw ID, or None (TR-08)."""
    for name in SPECIAL_CLASSES:
        if raw_id.startswith(name + ".") and len(raw_id) > len(name) + 1:
            return name
    return None


def method_of(raw_id):
    """The method part of a raw ID: the last component, or, for the loader's special tests, the whole
    module name after their class, which is dotted for a module inside a test package (TR-08)."""
    special = special_class(raw_id)
    return raw_id[len(special) + 1:] if special else raw_id.rsplit(".", 1)[1]


def split_description(line, *, require_dots):
    """The leftmost test description in a line, as (prefix, method, raw_id, rest) or None.

    With require_dots, the description must be followed by " ... " (rest is the text after it);
    without, it must end the line (the start of a test with a docstring line). A prefix is text
    glued in front of the description (noise); the method name is the last component of the ID,
    or the module name of the loader's _FailedTest and ModuleSkipped tests.
    """
    for match in DESCRIPTION.finditer(line):
        raw_id = match.group("id")
        if "." not in raw_id:
            continue
        method = method_of(raw_id)
        written = match.group("method")
        if not method or not written.endswith(method):
            continue
        start = match.start("method") + len(written) - len(method)
        end = match.end()
        if require_dots:
            if line.startswith(" ... ", end):
                return line[:start], method, raw_id, line[end + 5:]
        elif end == len(line):
            return line[:start], method, raw_id, None
    return None


class LogParser:
    """Reads one unit-stage log exactly as the module docstring describes; refuses what it cannot read completely."""

    def __init__(self, text):
        self.text = text

    # -- tail ---------------------------------------------------------------

    def tail(self):
        matches = list(TAIL.finditer(self.text))
        if not matches:
            raise Refusal("FOOTER", "The log has no complete unittest footer (separator, Ran line, result line); "
                          "it is truncated, interrupted or not a unittest -v log")
        match = matches[-1]
        ran = int(match.group("ran"))
        if (match.group("word") == "test") != (ran == 1):
            raise Refusal("FOOTER", "The Ran line's plural does not fit its count", ran=ran)
        infos = {}
        raw_infos = match.group("infos")
        if raw_infos is not None:
            position = 0
            for item in raw_infos.split(", "):
                key, separator, value = item.partition("=")
                if (not separator or key not in INFO_KEYS or INFO_KEYS.index(key) < position
                        or key in infos or re.fullmatch(r"[1-9]\d*", value) is None):
                    raise Refusal("FOOTER", "The result line's counts are not unittest's", result=match.group(0).strip())
                position = INFO_KEYS.index(key)
                infos[key] = int(value)
        counts = {key: infos.get(key, 0) for key in INFO_KEYS}
        failed = counts["failures"] or counts["errors"] or counts["unexpected successes"]
        result = match.group("result")
        expected = "FAILED" if failed else "NO TESTS RAN" if ran == 0 and not counts["skipped"] else "OK"
        if result != expected or (result == "FAILED") != bool(failed):
            raise Refusal("FOOTER", "The result word does not fit its counts", result=result, counts=counts)
        trailing = self.text[match.end():]
        footer = {"ran": ran, "seconds": match.group("seconds"), "result": result, "counts": counts,
                  "result_line": match.group(0).split("\n")[-2],
                  "ran_line_number": self.text.count("\n", 0, match.start()) + 2,
                  "earlier_footer_patterns": len(matches) - 1,
                  "trailing_text": {"bytes": len(trailing.encode("utf-8", "surrogateescape")),
                                    "lines": trailing.count("\n") + (0 if trailing.endswith("\n") or not trailing else 1),
                                    "sha256": text_digest(trailing)}}
        return footer, self.text[:match.start()]

    # -- progress -------------------------------------------------------------

    def parse(self):
        footer, body = self.tail()
        if not body.endswith("\n"):
            raise Refusal("PARSE", "The text before the footer does not end with a line end")
        lines = body[:-1].split("\n")
        candidates = self.listing_candidates(lines, footer)
        failures = []
        for start in candidates:
            try:
                return self.parse_at(lines, start, footer)
            except Refusal as exc:
                failures.append({"listing_line": start + 1 if start < len(lines) else None, **exc.as_dict()})
        raise Refusal("PARSE", "No reading of the log is complete and consistent with its own footer",
                      attempts=failures[:8], candidates=len(candidates))

    @staticmethod
    def listing_candidates(lines, footer):
        """Line indices where the error listing can start: an empty line, then the listing (or nothing)."""
        counts = footer["counts"]
        entries = counts["failures"] + counts["errors"]
        if entries == 0 and counts["unexpected successes"] == 0:
            # printErrors writes one line end and no entry: the body's last line is empty
            return [len(lines) - 1] if lines and lines[-1] == "" else []
        first = ("ERROR: ", "FAIL: ") if entries else ("UNEXPECTED SUCCESS: ",)
        return [index for index in range(len(lines) - 2)
                if lines[index] == "" and lines[index + 1] == SEPARATOR1 and lines[index + 2].startswith(first)]

    def parse_at(self, lines, listing_start, footer):
        state = Progress(lines, listing_start)
        state.run()
        record = state.result()
        listing = Listing(lines, listing_start, state, footer).run()
        checks = consistency(record, listing, footer)
        bad = sorted(name for name, value in checks.items() if not value)
        if bad:
            raise Refusal("COUNTS", "The parsed progress does not equal the log's own footer or listing",
                          failed_checks=bad, parsed=record["counts"], footer=footer["counts"], ran=footer["ran"])
        return footer, record, listing, checks


class Progress:
    """The progress section up to the listing, read with TextTestResult's _newline state emulated.

    A test's status that does not directly follow its start is planned once, at the start: the
    candidates are the lines up to the next runner line (a start, a fixture line or a subtest line
    of this test) that are a status token (exact) or end with one (glued after noise). A subtest
    line as that boundary means there is no direct status. Exact candidates come first; candidates
    with different statuses refuse the log, since choosing one would be a guess.
    """

    def __init__(self, lines, limit):
        self.lines, self.limit = lines, limit
        self.occurrences = []
        self.fixtures = []
        self.noise_lines = []
        self.newline = True       # TextTestResult._newline
        self.current = None
        self.plan = None          # (line index, cut, token) of the pending test's direct status
        self.events = []          # every status event that unittest counts, in the order it wrote them

    # -- matching: each returns (lines used, payload) or None ------------------

    def match_start(self, index):
        line = self.lines[index]
        found = split_description(line, require_dots=True)
        if found is not None:
            prefix, method, raw_id, rest = found
            return 1, {"prefix": prefix, "method": method, "id": raw_id, "docline": None, "rest": rest}
        found = split_description(line, require_dots=False)
        if found is None or index + 1 >= self.limit:
            return None
        prefix, method, raw_id, _ = found
        second = self.lines[index + 1]
        position = second.find(" ... ")
        if position <= 0:
            return None
        last = second.rfind(" ... ")
        if last != position and TOKEN.fullmatch(second[last + 5:]):
            position = last
        docline = second[:position]
        if docline != docline.strip():
            return None
        return 2, {"prefix": prefix, "method": method, "id": raw_id, "docline": docline, "rest": second[position + 5:]}

    def match_subtest(self, index):
        current = self.current
        if current is None:
            return None
        head = "  " + current.description + " "
        line = self.lines[index]
        position = line.find(head)
        if position < 0:
            return None
        tail = line[position + len(head):]
        if current.docline is None:
            match = re.search(r" \.\.\. (" + SUBTEST_TOKEN.pattern + r")$", tail)
            if match is None:
                return None
            subdesc, token, used = tail[:match.start()], match.group(1), 1
        else:
            if index + 1 >= self.limit:
                return None
            second = self.lines[index + 1]
            lead = current.docline + " ... "
            if not second.startswith(lead) or not SUBTEST_TOKEN.fullmatch(second[len(lead):]):
                return None
            subdesc, token, used = tail, second[len(lead):], 2
        if re.fullmatch(r"(?:\[.*\](?: \(.*\))?|\(.*\))", subdesc, re.DOTALL) is None:
            return None
        return used, {"prefix": line[:position], "subtest": subdesc, "token": token}

    def match_repeated(self, index):
        current = self.current
        if current is None:
            return None
        line = self.lines[index]
        if current.docline is None:
            head = current.description + " ... "
            position = line.rfind(head)
            if position < 0 or not REPEATED_TOKEN.fullmatch(line[position + len(head):]):
                return None
            return 1, {"prefix": line[:position], "token": line[position + len(head):]}
        if not line.endswith(current.description) or index + 1 >= self.limit:
            return None
        second = self.lines[index + 1]
        lead = current.docline + " ... "
        if not second.startswith(lead) or not REPEATED_TOKEN.fullmatch(second[len(lead):]):
            return None
        return 2, {"prefix": line[:len(line) - len(current.description)], "token": second[len(lead):]}

    def match_fixture(self, index):
        line = self.lines[index]
        match = next(FIXTURE.finditer(line), None)
        if match is None:
            return None
        return 1, {"prefix": line[:match.start()], "kind": match.group("kind"), "target": match.group("target"),
                   "token": match.group("status")}

    # -- recording ---------------------------------------------------------------

    def noise(self, index, text=None):
        text = self.lines[index] if text is None else text
        if text:
            self.noise_lines.append((index + 1, text))

    def add_event(self, owner, event):
        self.events.append((owner, event))
        return event

    def direct(self, occurrence, token, line):
        event = self.add_event(("test", occurrence), status_event(token, line))
        occurrence.events.append(event)
        occurrence.direct = event["status"]
        occurrence.pending = False
        # unittest writes "expected failure" and "unexpected success" with writeln, which leaves _newline unset
        self.newline = event["status"] not in ("expected failure", "unexpected success")

    # -- the reading -----------------------------------------------------------------

    def run(self):
        index = 0
        while index < self.limit:
            index += self.step(index)

    def step(self, index):
        current = self.current
        if current is not None and current.pending and self.plan is not None and self.plan[0] == index:
            _, cut, token = self.plan
            self.plan = None
            self.noise(index, self.lines[index][:cut])
            self.direct(current, token, index + 1)
            return 1
        if current is not None and (current.pending or self.newline):
            found = self.match_subtest(index)
            if found is not None:
                used, payload = found
                self.noise(index, payload["prefix"])
                event = self.add_event(("subtest", current), dict(status_event(payload["token"], index + used),
                                                                  subtest=payload["subtest"]))
                current.subtests.append(event)
                current.pending = False
                self.plan = None
                self.newline = True
                return used
        if current is not None and self.newline:
            found = self.match_repeated(index)
            if found is not None:
                used, payload = found
                self.noise(index, payload["prefix"])
                current.events.append(self.add_event(("test", current), status_event(payload["token"], index + used)))
                return used
        if self.newline:
            found = self.match_fixture(index)
            if found is not None:
                used, payload = found
                self.noise(index, payload["prefix"])
                record = {"id": "%s (%s)" % (payload["kind"], payload["target"]), "fixture": payload["kind"],
                          "target": payload["target"], "order": len(self.fixtures)}
                record["event"] = self.add_event(("fixture", record), status_event(payload["token"], index + 1))
                self.fixtures.append(record)
                return used
        found = self.match_start(index)
        if found is not None:
            used, payload = found
            if current is not None and current.pending:
                raise Refusal("STATUS", "A test started before the previous test had any status", line=index + 1,
                              previous=current.raw_id, previous_line=current.line)
            self.noise(index, payload["prefix"])
            description = "%s (%s)" % (payload["method"], payload["id"])
            occurrence = Occurrence(payload["id"], payload["method"], description, payload["docline"], index + 1,
                                    len(self.occurrences))
            self.occurrences.append(occurrence)
            self.current = occurrence
            self.newline = False
            rest, last = payload["rest"], index + used - 1
            if TOKEN.fullmatch(rest):
                self.plan = None
                self.direct(occurrence, rest, last + 1)
                return used
            self.plan = self.plan_direct(index + used, last, rest)
            if self.plan is not None and self.plan[0] == last:
                _, cut, token = self.plan
                self.plan = None
                self.noise(last, rest[:cut])
                self.direct(occurrence, token, last + 1)
            else:
                self.noise(last, rest)
            return used
        if (current is not None and not current.pending and not self.newline
                and FIXTURE_TOKEN.fullmatch(self.lines[index])):
            raise Refusal("ATTRIBUTION", "A class-level or module-level status without a description follows an "
                          "expected failure or an unexpected success; it cannot be attributed", line=index + 1)
        self.noise(index)
        return 1

    def window(self, index):
        """(end, boundary): the lines from index up to the next runner line, and what that line is."""
        end = index
        while end < self.limit:
            if self.match_subtest(end) is not None:
                return end, "subtest"
            if self.match_fixture(end) is not None or self.match_start(end) is not None:
                return end, "runner"
            end += 1
        return end, "listing"

    def plan_direct(self, first, rest_line, rest):
        """The one candidate for a status that did not directly follow its start, or None (TR-05).

        A candidate is a line, or the text after the start's " ... ", that is a status token
        (exact) or ends with one (glued after noise). With two or more candidates in the window,
        whatever their values, the log is refused: one of them was printed, and any choice would
        be a guess, even one that keeps every count.
        """
        end, boundary = self.window(first)
        if boundary == "subtest":
            return None
        scan = ([(rest_line, rest)] if rest else []) + [(i, self.lines[i]) for i in range(first, end)]
        candidates = []
        for i, text in scan:
            if TOKEN.fullmatch(text):
                candidates.append((i, 0, text))
                continue
            match = TOKEN_AT_END.search(text)
            if match is not None and match.start() > 0:
                candidates.append((i, match.start(), text[match.start():]))
        if len(candidates) > 1:
            raise Refusal("AMBIGUOUS", "More than one status candidate follows a test's start; the status cannot "
                          "be told from printed text", test=self.current.raw_id, line=self.current.line,
                          candidate_lines=[i + 1 for i, _, _ in candidates],
                          candidate_statuses=[status_event(token, i + 1)["status"] for i, _, token in candidates])
        return candidates[0] if candidates else None

    def result(self):
        if self.current is not None and self.current.pending:
            raise Refusal("STATUS", "The last test has no status before the listing", test=self.current.raw_id,
                          line=self.current.line)
        counts = Counter(event["status"] for _, event in self.events)
        return {"occurrences": self.occurrences, "fixtures": self.fixtures, "events": self.events,
                "counts": {"tests_started": len(self.occurrences),
                           "failures": counts["FAIL"], "errors": counts["ERROR"], "skipped": counts["skipped"],
                           "expected failures": counts["expected failure"],
                           "unexpected successes": counts["unexpected success"], "ok": counts["ok"]},
                "noise_lines": self.noise_lines}


class Listing:
    """The ERROR and FAIL entries, then the unexpected successes: exactly the expected headers, in order."""

    def __init__(self, lines, start, progress, footer):
        self.lines, self.start, self.progress, self.footer = lines, start, progress, footer

    def expected(self):
        errors, failures, unexpected = [], [], []
        for owner, event in self.progress.events:
            kind, subject = owner
            if kind == "test":
                description = subject.full_description
            elif kind == "subtest":
                description = subject.description + " " + event["subtest"] + (
                    "\n" + subject.docline if subject.docline else "")
            else:
                description = subject["id"]
            if event["status"] == "ERROR":
                errors.append((event, description))
            elif event["status"] == "FAIL":
                failures.append((event, description))
            elif event["status"] == "unexpected success":
                unexpected.append(description)
        headers = [("ERROR", event, description) for event, description in errors] + \
                  [("FAIL", event, description) for event, description in failures]
        return headers, unexpected

    def run(self):
        headers, unexpected = self.expected()
        text = "\n".join(self.lines[self.start + 1:]) + "\n" if self.start + 1 < len(self.lines) else ""
        if not headers and not unexpected:
            if text:
                raise Refusal("LISTING", "Text follows the end of the progress section, but the footer expects no entry")
            return {"entries": 0, "unexpected_successes": 0}
        block = ""
        if unexpected:
            block = SEPARATOR1 + "\n" + "".join("UNEXPECTED SUCCESS: " + description + "\n" for description in unexpected)
            if not text.endswith(block):
                raise Refusal("LISTING", "The unexpected-success block does not list the unexpected successes")
            text = text[:len(text) - len(block)]
        strings = [SEPARATOR1 + "\n" + flavour + ": " + description + "\n" + SEPARATOR2 + "\n"
                   for flavour, _, description in headers]
        occurrences = []
        for header in set(strings):
            position = text.find(header)
            while position >= 0:
                if position == 0 or text[position - 1] == "\n":
                    occurrences.append((position, header))
                position = text.find(header, position + 1)
        occurrences.sort()
        if [header for _, header in occurrences] != strings or (strings and occurrences[0][0] != 0):
            raise Refusal("LISTING", "The listing's headers are not exactly the expected headers in order; "
                          "the split would not be unique", expected=len(strings), found=len(occurrences))
        if not strings and text:
            raise Refusal("LISTING", "Text precedes the unexpected-success block")
        blank_after_every_entry = True
        for number, ((position, header), (flavour, event, _)) in enumerate(zip(occurrences, headers)):
            end = occurrences[number + 1][0] if number + 1 < len(occurrences) else len(text)
            segment = text[position + len(header):end]
            if not segment.endswith("\n"):
                raise Refusal("LISTING", "A listing entry does not end with the line end that unittest writes",
                              entry=number + 1)
            blank_after_every_entry = blank_after_every_entry and segment.endswith("\n\n")
            event.update(reason_analysis(segment[:-1]))
            event["listing_entry"] = number + 1
        return {"entries": len(strings), "unexpected_successes": len(unexpected),
                "every_entry_ends_with_an_empty_line": blank_after_every_entry}


def reason_analysis(reason):
    """The first line of the reason (see the module docstring), each block's first line, and the text's digest."""
    lines = reason.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    blocks, index = [], 0
    while index < len(lines):
        if lines[index] == TRACEBACK_HEADER:
            index += 1
            while index < len(lines) and lines[index].startswith("  "):
                index += 1
        start = index
        end = len(lines)
        for probe in range(start, len(lines) - 2):
            if lines[probe] == "" and lines[probe + 1] in CHAIN_LINES and lines[probe + 2] == "":
                end = probe
                break
        blocks.append(lines[start:end])
        index = end + 3 if end < len(lines) else len(lines)
    first_lines = [block[0] if block else None for block in blocks]
    first = first_lines[-1] if first_lines else None
    if first is None:
        remaining = [line for line in lines if line.strip()]
        first = remaining[-1] if remaining else None
    return {"reason_first_line": first, "chain_first_lines": first_lines, "reason_lines": len(lines),
            "reason_sha256": text_digest(reason)}


def consistency(record, listing, footer):
    counts, expected = record["counts"], footer["counts"]
    return {"tests_started_equal_ran": counts["tests_started"] == footer["ran"],
            "failures_equal_footer": counts["failures"] == expected["failures"],
            "errors_equal_footer": counts["errors"] == expected["errors"],
            "skipped_equal_footer": counts["skipped"] == expected["skipped"],
            "expected_failures_equal_footer": counts["expected failures"] == expected["expected failures"],
            "unexpected_successes_equal_footer": counts["unexpected successes"] == expected["unexpected successes"],
            "listing_entries_equal_failures_and_errors": listing["entries"] == expected["failures"] + expected["errors"],
            "every_test_has_a_status": all(not occurrence.pending for occurrence in record["occurrences"])}


def driver_text(raw):
    """The log's text as tools/check_local.py reads it: Path.read_text(encoding="utf-8", errors="replace"),
    which decodes with universal newlines, so a carriage return becomes a line end (TR-11)."""
    return io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", errors="replace", newline=None).read()


def driver_reading(raw):
    """What tools/check_local.py's execute_step reads from this log's bytes (its regular expressions, unchanged)."""
    text = driver_text(raw)
    executions = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", text, re.MULTILINE)
    endings = re.findall(r"^(?:OK|FAILED)(?: \(([^\n]*)\))?$", text, re.MULTILINE)
    counts = {name.strip(): value for name, value in re.findall(r"([a-z ]+)=(\d+)", endings[-1])} if endings else {}
    skipped, expected_failures = int(counts.get("skipped", 0)), int(counts.get("expected failures", 0))
    count = int(executions[-1][0]) if executions else 0
    return {"tests_run": count, "skipped": skipped, "expected_failures": expected_failures,
            "executed_without_skips": max(0, count - skipped)}


# ---------------------------------------------------------------------------
# Records per raw ID
# ---------------------------------------------------------------------------

def outcome_of(events, subtests):
    statuses = [event["status"] for event in events] + [event["status"] for event in subtests]
    if "ERROR" in statuses:
        return "error"
    if "FAIL" in statuses:
        return "failure"
    if "unexpected success" in statuses:
        return "unexpected_success"
    if "expected failure" in statuses:
        return "expected_failure"
    if "skipped" in statuses:
        return "skipped"
    if statuses and all(status == "ok" for status in statuses):
        return "passed"
    return "unknown"


def public_event(event):
    return {key: event[key] for key in ("status", "skip_reason", "subtest", "line", "reason_first_line",
                                       "chain_first_lines", "reason_lines", "reason_sha256", "listing_entry")
            if key in event}


def test_records(occurrences):
    grouped = {}
    for occurrence in occurrences:
        grouped.setdefault(occurrence.raw_id, []).append(occurrence)
    records = []
    for raw_id, items in sorted(grouped.items(), key=lambda pair: pair[1][0].order):
        special = special_class(raw_id)
        runs = []
        for item in items:
            runs.append({"line": item.line, "order": item.order,
                         "outcome": outcome_of(item.events, item.subtests),
                         "events": [public_event(event) for event in item.events],
                         "subtests": [public_event(event) for event in item.subtests]})
        combined = [event for item in items for event in item.events]
        combined_subtests = [event for item in items for event in item.subtests]
        record = {"id": raw_id, "kind": "test", "description": items[0].description, "docline": items[0].docline,
                  "special": SPECIAL_CLASSES.get(special), "occurrences": len(items),
                  "outcome": outcome_of(combined, combined_subtests), "line": items[0].line, "order": items[0].order,
                  "runs": runs}
        record["reasons"] = [event["reason_first_line"] for event in combined + combined_subtests
                             if event["status"] in ("FAIL", "ERROR")]
        record["skip_reasons"] = [event["skip_reason"] for event in combined + combined_subtests
                                  if event["status"] == "skipped"]
        record["failing_subtests"] = [{"subtest": event["subtest"], "status": event["status"],
                                       "reason_first_line": event.get("reason_first_line")}
                                      for event in combined_subtests if event["status"] in ("FAIL", "ERROR")]
        record["skipped_subtests"] = [{"subtest": event["subtest"], "skip_reason": event["skip_reason"]}
                                      for event in combined_subtests if event["status"] == "skipped"]
        records.append(record)
    return records


def fixture_records(fixtures):
    grouped = {}
    for fixture in fixtures:
        grouped.setdefault(fixture["id"], []).append(fixture)
    records = []
    for raw_id, items in sorted(grouped.items(), key=lambda pair: pair[1][0]["order"]):
        events = [item["event"] for item in items]
        outcome = "error" if any(event["status"] == "ERROR" for event in events) else "skipped"
        records.append({"id": raw_id, "kind": "fixture", "fixture": items[0]["fixture"], "target": items[0]["target"],
                        "occurrences": len(items), "outcome": outcome, "line": events[0]["line"],
                        "events": [public_event(event) for event in events],
                        "reasons": [event["reason_first_line"] for event in events if event["status"] == "ERROR"],
                        "skip_reasons": [event["skip_reason"] for event in events if event["status"] == "skipped"],
                        "failing_subtests": [], "skipped_subtests": []})
    return records


def collect_log(raw):
    """The complete reading of one log's bytes; raises Refusal when it cannot be read completely."""
    text = raw.decode("utf-8", "surrogateescape")
    try:
        raw.decode("utf-8")
        valid = True
    except UnicodeDecodeError:
        valid = False
    footer, record, listing, checks = LogParser(text).parse()
    tests = test_records(record["occurrences"])
    fixtures = fixture_records(record["fixtures"])
    by_outcome = Counter(row["outcome"] for row in tests)
    noise_text = "\n".join(text for _, text in record["noise_lines"])
    reading = driver_reading(raw)
    reading["equals_footer"] = (reading["tests_run"] == footer["ran"] and reading["skipped"] == footer["counts"]["skipped"]
                                and reading["expected_failures"] == footer["counts"]["expected failures"])
    return {
        "text": {"utf8_valid": valid, "lines": text.count("\n") + (0 if text.endswith("\n") else 1),
                 "carriage_returns": text.count("\r"), "nul_characters": text.count("\0")},
        "footer": footer, "driver_reading": reading,
        "listing": listing, "checks": checks,
        "counts": dict(record["counts"], distinct_test_ids=len(tests), fixture_ids=len(fixtures),
                       duplicate_test_ids=sum(1 for row in tests if row["occurrences"] > 1),
                       by_outcome={name: by_outcome.get(name, 0) for name in OUTCOMES + ("unknown",)},
                       not_passing_test_ids=sum(1 for row in tests if row["outcome"] in NOT_PASSING),
                       not_passing_fixture_ids=sum(1 for row in fixtures if row["outcome"] == "error")),
        "noise": {"lines": len(record["noise_lines"]), "line_numbers": [number for number, _ in record["noise_lines"]],
                  "sha256": text_digest(noise_text)},
        "tests": tests, "fixtures": fixtures}


def expectation_results(expectations, records):
    """--expect rows for exact IDs (TR-02), for example MC23's methods and the absence of fixture records.

    ID=OUTCOME     the ID's record exists, has that outcome and occurs exactly once;
    ID=OUTCOME*N   the same, occurring exactly N times;
    ID=missing     no test or fixture record has that ID.
    """
    by_id = {row["id"]: row for row in records}
    rows = []
    for item in expectations:
        raw_id, separator, spec = item.rpartition("=")
        outcome, star, count = spec.partition("*")
        valid = bool(separator and raw_id) and (
            (spec == "missing") or (outcome in OUTCOMES and (not star or re.fullmatch(r"[1-9]\d*", count) is not None)))
        if not valid:
            raise Refusal("USAGE", "An expectation is ID=OUTCOME, ID=OUTCOME*N or ID=missing, with OUTCOME one of "
                          + ", ".join(OUTCOMES), expectation=item)
        row = by_id.get(raw_id)
        observed = row["outcome"] if row else "missing"
        occurrences = row["occurrences"] if row else 0
        if spec == "missing":
            expected_occurrences, met = 0, row is None
        else:
            expected_occurrences = int(count) if star else 1
            met = row is not None and observed == outcome and occurrences == expected_occurrences
        rows.append({"id": raw_id, "expected": "missing" if spec == "missing" else outcome,
                     "expected_occurrences": expected_occurrences, "observed": observed,
                     "occurrences": occurrences, "met": met})
    return rows


def inventory_join(path, expected, result):
    """The log's started tests against a runtime-discovery document of MH's collector (MC28's second half).

    The discovery IDs are recomputed from ids_in_discovery_order, never taken from the document's
    own counts (MH's TR-07). The run starts tests in discovery order, so for a complete run the
    sequence of starts equals that list exactly; every difference is listed.
    """
    raw, binding = bound_input(path, expected, LOG_LIMIT, rule="INVENTORY")
    document = strict_json(raw, rule="INVENTORY", what="discovery document")
    ids = document.get("ids_in_discovery_order") if type(document) is dict else None
    if (type(document) is not dict or document.get("schema") != DISCOVERY_SCHEMA or document.get("state") != "COMPLETE"
            or type(ids) is not list or not all(type(item) is str for item in ids)):
        raise Refusal("INVENTORY", "The inventory is not a complete " + DISCOVERY_SCHEMA + " document")
    sequence = [raw_id for _, raw_id in sorted((run["order"], row["id"]) for row in result["tests"] for run in row["runs"])]
    counts = Counter(ids)
    started = Counter(sequence)
    return {"input": binding, "ids": len(ids), "unique_ids": len(counts),
            "recomputed_duplicates": sorted(item for item, number in counts.items() if number > 1),
            "started": len(sequence),
            "started_not_in_inventory": sorted(set(started) - set(counts)),
            "inventory_not_started": sorted(set(counts) - set(started)),
            "started_a_different_number_of_times": sorted(item for item in set(counts) & set(started)
                                                          if counts[item] != started[item]),
            "sequence_equal": sequence == ids,
            "matches": sequence == ids}


def run_collect(args):
    started, monotonic = utc_now(), time.monotonic()
    raw, binding = bound_input(args.log, args.log_sha256, LOG_LIMIT, rule="LOG")
    result = collect_log(raw)
    expectations = expectation_results(args.expect or [], result["tests"] + result["fixtures"])
    if bool(args.inventory) != bool(args.inventory_sha256):
        raise Refusal("USAGE", "--inventory and --inventory-sha256 go together")
    inventory = inventory_join(args.inventory, args.inventory_sha256, result) if args.inventory else None
    record = {"schema": SCHEMA, "tool": tool_record(), "invocation": invocation_record(), "started_at_utc": started,
              "state": "PARSED", "input": {"log": binding, "expected_sha256": args.log_sha256},
              "loaded_project_files": [], **result, "expectations": expectations,
              "expectations_met": all(row["met"] for row in expectations), "inventory": inventory,
              "limits": ["Outcomes are read from the text unittest wrote. Printed text that leaves more than one status "
                         "candidate after a start refuses the log. A status token that a test writes unbuffered "
                         "immediately after its own start is read as its status, and is caught only when it changes a "
                         "count or a listing entry.",
                         "The first line of a reason is a reading of the traceback text, as the module docstring defines it."]}
    record.update(finished_at_utc=utc_now(), elapsed_s=time.monotonic() - monotonic)
    write_new(args.output, json_text(record))
    inventory_matches = inventory is None or inventory["matches"]
    sys.stderr.write("UNIT-LOG-OUTCOMES " + json.dumps({"ran": result["footer"]["ran"],
                                                        "by_outcome": result["counts"]["by_outcome"],
                                                        "fixtures": len(result["fixtures"]),
                                                        "expectations_met": record["expectations_met"],
                                                        "inventory_matches": inventory_matches},
                                                       sort_keys=True) + "\n")
    return EXIT_OK if record["expectations_met"] and inventory_matches else EXIT_DIFFERS


# ---------------------------------------------------------------------------
# The comparison (OK-ENG-009 section 3 item 4)
# ---------------------------------------------------------------------------

def load_summary(path, expected):
    raw, binding = bound_input(path, expected, SUMMARY_LIMIT, rule="SUMMARY")
    summary = strict_json(raw, rule="SUMMARY", what="summary")
    if type(summary) is not dict or summary.get("schema_version") != SUMMARY_SCHEMA:
        raise Refusal("SUMMARY", "The summary is not a " + SUMMARY_SCHEMA + " document", path=path)
    steps = summary.get("steps")
    if type(steps) is not list or not all(type(step) is dict and type(step.get("id")) is str for step in steps):
        raise Refusal("SUMMARY", "The summary's steps are malformed", path=path)
    if len({step["id"] for step in steps}) != len(steps):
        raise Refusal("SUMMARY", "The summary repeats a step", path=path)
    return summary, binding


def unit_step(summary):
    for step in summary["steps"]:
        if step["id"] == UNIT_STEP:
            return step
    return None


class Normalizer:
    """Declared replacement of one run's own paths in reasons and subtest names (NORMALIZATION, version 2).

    Only paths that belong to the run itself are replaced, longest first, and only as whole path
    components: a path matches where the text before it is its start or a delimiter, and the text
    after it is its end, "/" or a delimiter (PATH_DELIMITERS); so a sibling name that merely starts
    with the path's last component is never replaced (TR-06).
    * from its summary: the driver's interpreter (environment.python_executable) by <python>, the
      workspace (the unit step's cwd) by <workspace>, the output directory (the workspace's parent)
      by <output> and the source root by <source>;
    * from the command line: each temporary directory of the run, as given by <tmp>, as resolved by
      <tmp:resolved>, and, when the given form is a resolved /private/... path, its alias without
      /private by <tmp:alias>. The component directly below it becomes * only when it has
      tempfile's own name shape, "tmp" and eight characters of [a-z0-9_]; any other name stays, so
      two different directories never compare as equal. Every masked name is recorded.
    Nothing else changes; the raw texts stay in the records beside the normalized ones.
    """

    def __init__(self, summary, tmpdirs):
        step = unit_step(summary) or {}
        workspace = step.get("cwd") if type(step.get("cwd")) is str else None
        environment = summary.get("environment") if type(summary.get("environment")) is dict else {}
        pairs = []
        if type(environment.get("python_executable")) is str:
            pairs.append((environment["python_executable"], "<python>"))
        if workspace:
            pairs.append((workspace, "<workspace>"))
            pairs.append((os.path.dirname(workspace), "<output>"))
        source = summary.get("source_root")
        if type(source) is str and source:
            pairs.append((source, "<source>"))
        paths = sorted({(path.rstrip("/"), label) for path, label in pairs if path and path.rstrip("/")},
                       key=lambda pair: (-len(pair[0]), pair[1]))
        delimiters = re.escape(PATH_DELIMITERS)
        self.left = r"(?:(?<=[%s])|^)" % delimiters
        self.right = r"(?=[/%s]|$)" % delimiters
        self.paths = [(re.compile(self.left + re.escape(path) + self.right), label) for path, label in paths]
        forms = {}
        for given in tmpdirs or []:
            given = given.rstrip("/")
            if not given.startswith("/"):
                raise Refusal("USAGE", "A temporary directory is an absolute path", path=given)
            forms.setdefault(given, "<tmp>")
            resolved = os.path.realpath(given)
            if resolved != given:
                forms.setdefault(resolved, "<tmp:resolved>")
            if given.startswith("/private/") and os.path.realpath(given[len("/private"):]) == given:
                forms.setdefault(given[len("/private"):], "<tmp:alias>")
        tmp = sorted(forms.items(), key=lambda pair: (-len(pair[0]), pair[1]))
        component = r"(?:/(?P<component>[^/%s]+))?" % delimiters
        self.tmp = [(re.compile(self.left + re.escape(path) + component + self.right), label) for path, label in tmp]
        self.declared = {"version": NORMALIZATION, "path_labels": [label for _, label in paths],
                         "temporary_directory_labels": [label for _, label in tmp],
                         "temporary_directories_given": len(tmpdirs or []),
                         "temporary_name_mask": TEMP_NAME.pattern, "delimiters": PATH_DELIMITERS}

    def apply(self, text):
        """(normalized text, masked temporary names) of one text; None stays None."""
        if text is None:
            return None, []
        masked = []
        for pattern, label in self.paths:
            text = pattern.sub(label, text)
        for pattern, label in self.tmp:
            def replace(match, label=label):
                name = match.group("component")
                if name is None:
                    return label
                if TEMP_NAME.fullmatch(name):
                    masked.append(name)
                    return label + "/*"
                return label + "/" + name
            text = pattern.sub(replace, text)
        return text, masked

    def __call__(self, text):
        return self.apply(text)[0]

    def masked(self, texts):
        """The temporary names that the mask replaced in these texts, in order, each once."""
        names = []
        for text in texts:
            for name in self.apply(text)[1]:
                if name not in names:
                    names.append(name)
        return names


def comparable(row, normalize):
    """The parts of a record that item 4 compares: outcome, normalized reasons, skip reasons and subtests.

    Subtest descriptions are compared after the same declared normalization as reasons, since a
    subtest's parameters can name a run's own temporary path.
    """
    events = []
    for run in (row["runs"] if "runs" in row else [{"events": row["events"]}]):
        for event in run["events"]:
            events.append((event["status"], normalize(event.get("reason_first_line")), event.get("skip_reason")))
    subtests = sorted((normalize(event["subtest"]), event["status"], normalize(event.get("reason_first_line")))
                      for event in row.get("failing_subtests", []))
    skipped = sorted((normalize(event["subtest"]), event["skip_reason"]) for event in row.get("skipped_subtests", []))
    return {"outcome": row["outcome"], "occurrences": row["occurrences"], "events": events,
            "failing_subtests": subtests, "skipped_subtests": skipped,
            "subtest_set": sorted({(name, status) for name, status, _ in subtests} | {(name, "skipped") for name, _ in skipped}),
            "reasons": sorted({reason for _, reason, _ in events if reason is not None} |
                              {reason for _, _, reason in subtests if reason is not None}),
            "skip_reasons": sorted({reason for _, _, reason in events if reason is not None} |
                                   {reason for _, reason in skipped})}


def brief(row, normalize):
    if row is None:
        return None
    view = comparable(row, normalize)
    texts = [reason for reason in row.get("reasons", []) if reason is not None] + \
        [event["subtest"] for event in row.get("failing_subtests", []) + row.get("skipped_subtests", [])]
    return {"outcome": row["outcome"], "occurrences": row["occurrences"], "reasons": view["reasons"],
            "raw_reasons": sorted({reason for reason in row.get("reasons", []) if reason is not None}),
            "skip_reasons": view["skip_reasons"], "failing_subtests": len(view["failing_subtests"]),
            "skipped_subtests": len(view["skipped_subtests"]), "masked_temporary_names": normalize.masked(texts)}


STATEMENT_KEYS = ("outcome", "occurrences", "events", "failing_subtests", "skipped_subtests")
STATUSES = ("ok", "FAIL", "ERROR", "skipped", "expected failure", "unexpected success")


def event_statement(event, normalize):
    """One own event as an attribution states it: its status, and its first line or skip reason."""
    row = {"status": event["status"]}
    if event["status"] in ("FAIL", "ERROR"):
        row["reason_first_line"] = normalize(event.get("reason_first_line"))
    elif event["status"] == "skipped":
        row["skip_reason"] = event.get("skip_reason")
    return row


def record_statement(row, normalize):
    """A record's complete statement (TR-01): outcome, occurrences, own events in the order unittest wrote
    them, failing subtests (status and first line) and skipped subtests (skip reason), in their order.
    Reasons and subtest names are given in one form: raw (normalize is the identity) or normalized."""
    if row is None:
        return None
    events = [event for run in (row["runs"] if "runs" in row else [{"events": row["events"]}]) for event in run["events"]]
    return {"outcome": row["outcome"], "occurrences": row["occurrences"],
            "events": [event_statement(event, normalize) for event in events],
            "failing_subtests": [{"subtest": normalize(event["subtest"]), "status": event["status"],
                                  "reason_first_line": normalize(event.get("reason_first_line"))}
                                 for event in row.get("failing_subtests", [])],
            "skipped_subtests": [{"subtest": normalize(event["subtest"]), "skip_reason": event["skip_reason"]}
                                 for event in row.get("skipped_subtests", [])]}


def statement_differences(expected, observed):
    """Every place where an observed statement differs from the attributed one, field by field and item by item."""
    if observed is None:
        return [{"field": "id", "expected": "present", "observed": "missing"}]
    rows = []
    for key in ("outcome", "occurrences"):
        if expected[key] != observed[key]:
            rows.append({"field": key, "expected": expected[key], "observed": observed[key]})
    for key in ("events", "failing_subtests", "skipped_subtests"):
        left, right = expected[key], observed[key]
        for index in range(max(len(left), len(right))):
            first = left[index] if index < len(left) else None
            second = right[index] if index < len(right) else None
            if first != second:
                rows.append({"field": "%s[%d]" % (key, index), "expected": first, "observed": second})
    return rows


def valid_statement(row):
    def text(value):
        return value is None or type(value) is str

    events, failing, skipped = row.get("events"), row.get("failing_subtests"), row.get("skipped_subtests")
    if row.get("outcome") not in OUTCOMES or type(row.get("occurrences")) is not int or row["occurrences"] < 1:
        return False
    if not all(type(value) is list for value in (events, failing, skipped)):
        return False
    for event in events:
        status = event.get("status") if type(event) is dict else None
        keys = {"status"} | ({"reason_first_line"} if status in ("FAIL", "ERROR") else
                             {"skip_reason"} if status == "skipped" else set())
        if status not in STATUSES or set(event) != keys or not all(text(event[key]) for key in keys - {"status"}):
            return False
    for event in failing:
        if (type(event) is not dict or set(event) != {"subtest", "status", "reason_first_line"}
                or event["status"] not in ("FAIL", "ERROR") or type(event["subtest"]) is not str
                or not text(event["reason_first_line"])):
            return False
    return all(type(event) is dict and set(event) == {"subtest", "skip_reason"} and type(event["subtest"]) is str
               and text(event["skip_reason"]) for event in skipped)


def load_attributions(path, expected):
    """The freeze's attribution file (ATTRIBUTIONS_SCHEMA): one complete statement per exact ID (TR-01)."""
    raw, binding = bound_input(path, expected, ATTRIBUTIONS_LIMIT, rule="ATTRIBUTIONS")
    document = strict_json(raw, rule="ATTRIBUTIONS", what="attribution file")
    rows = document.get("attributions") if type(document) is dict else None
    if (type(document) is not dict or set(document) != {"schema", "attributions"}
            or document.get("schema") != ATTRIBUTIONS_SCHEMA or type(rows) is not list):
        raise Refusal("ATTRIBUTIONS", "The attribution file is not a " + ATTRIBUTIONS_SCHEMA + " document "
                      "{schema, attributions}")
    seen = set()
    required = {"id", "form", *STATEMENT_KEYS}
    for row in rows:
        if (type(row) is not dict or not required <= set(row) or not set(row) <= required | {"source", "note"}
                or type(row["id"]) is not str or row["form"] not in ATTRIBUTION_FORMS or not valid_statement(row)):
            raise Refusal("ATTRIBUTIONS", "An attribution is {id, form (raw or normalized), outcome, occurrences, "
                          "events, failing_subtests, skipped_subtests[, source, note]}, each part complete",
                          id=row.get("id") if type(row) is dict else None)
        if row["id"] in seen:
            raise Refusal("ATTRIBUTIONS", "An ID is attributed twice", id=row["id"])
        seen.add(row["id"])
    return rows, binding


def step_views(summary):
    rows = {}
    for step in summary["steps"]:
        rows[step["id"]] = {"status": step.get("status"), "returncode": step.get("returncode"),
                            "process_started": step.get("process_started"), "test_execution": step.get("test_execution"),
                            "reports": [{"path": report.get("path"), "outcomes": report.get("outcomes"),
                                         "pending_cases": report.get("pending_cases"),
                                         "read_error": report.get("read_error")}
                                        for report in step.get("reports", []) if type(report) is dict]}
    return rows


def pending_view(summary):
    rows = summary.get("pending_external_cases") or []
    return sorted(json.dumps(row, sort_keys=True) for row in rows if type(row) is dict)


def summary_comparison(baseline, candidate):
    left, right = step_views(baseline), step_views(candidate)
    steps = []
    for name in list(dict.fromkeys([step["id"] for step in baseline["steps"]] + [step["id"] for step in candidate["steps"]])):
        a, b = left.get(name), right.get(name)
        reports_a = [(row["path"], row["outcomes"]) for row in a["reports"]] if a else None
        reports_b = [(row["path"], row["outcomes"]) for row in b["reports"]] if b else None
        steps.append({"id": name, "baseline_status": a["status"] if a else "absent",
                      "candidate_status": b["status"] if b else "absent",
                      "status_equal": bool(a and b and a["status"] == b["status"]),
                      "baseline_reports": a["reports"] if a else None, "candidate_reports": b["reports"] if b else None,
                      "report_outcomes_equal": reports_a == reports_b,
                      "baseline_test_execution": a["test_execution"] if a else None,
                      "candidate_test_execution": b["test_execution"] if b else None})
    pending_a, pending_b = pending_view(baseline), pending_view(candidate)
    # TR-03: every report whose summarized outcomes differ, or that one side lacks, by step and report path.
    reports_different = []
    for name in [row["id"] for row in steps]:
        a = {report["path"]: report["outcomes"] for report in (left.get(name) or {"reports": []})["reports"]}
        b = {report["path"]: report["outcomes"] for report in (right.get(name) or {"reports": []})["reports"]}
        for path in list(dict.fromkeys(list(a) + list(b))):
            if path not in a or path not in b or a[path] != b[path]:
                reports_different.append({"step": name, "report": path, "baseline_outcomes": a.get(path),
                                          "candidate_outcomes": b.get(path),
                                          "present": {"baseline": path in a, "candidate": path in b}})

    def side(summary):
        selection = summary.get("readback_selection") if type(summary.get("readback_selection")) is dict else {}
        git = summary.get("git") if type(summary.get("git")) is dict else {}
        inventory = summary.get("source_inventory") if type(summary.get("source_inventory")) is dict else {}
        return {"status": summary.get("status"), "exit_code": summary.get("exit_code"), "profile": summary.get("profile"),
                "selected_roles": summary.get("selected_roles"), "planned_steps": summary.get("planned_steps"),
                "not_executed_steps": summary.get("not_executed_steps"),
                "readback_selection": {"status": selection.get("status"), "run_kind": selection.get("run_kind")},
                "environment": summary.get("environment"), "local_head": git.get("local_head"),
                "local_tree": git.get("local_tree"), "source_inventory_sha256": inventory.get("inventory_sha256"),
                "source_file_count": inventory.get("file_count"), "source_unchanged": summary.get("source_unchanged"),
                "pending_external_cases": len(summary.get("pending_external_cases") or [])}
    return {"steps": steps,
            "steps_equal": [row["id"] for row in steps if row["status_equal"]],
            "steps_different": [[row["id"], row["baseline_status"], row["candidate_status"]] for row in steps
                                if not row["status_equal"]],
            "reports_different": reports_different,
            "pending_external_cases": {"baseline": [json.loads(row) for row in pending_a],
                                       "candidate": [json.loads(row) for row in pending_b],
                                       "equal": pending_a == pending_b,
                                       "only_baseline": [json.loads(row) for row in sorted(set(pending_a) - set(pending_b))],
                                       "only_candidate": [json.loads(row) for row in sorted(set(pending_b) - set(pending_a))]},
            "not_executed_steps": {"baseline": baseline.get("not_executed_steps"),
                                   "candidate": candidate.get("not_executed_steps"),
                                   "equal": baseline.get("not_executed_steps") == candidate.get("not_executed_steps")},
            "runs": {"baseline": side(baseline), "candidate": side(candidate)}}


def compare_records(baseline_rows, candidate_rows, normalize_baseline, normalize_candidate):
    left = {row["id"]: row for row in baseline_rows}
    right = {row["id"]: row for row in candidate_rows}
    unchanged = Counter()
    lists = {name: [] for name in ("unchanged_not_passing", "unchanged_skipped", "unchanged_expected_failures",
                                   "new_not_passing", "no_longer_failing", "different_outcome", "different_reason",
                                   "different_subtests", "different_skip_reason", "different_occurrences",
                                   "added_ids", "removed_ids")}
    for raw_id in list(dict.fromkeys(list(left) + list(right))):
        a, b = left.get(raw_id), right.get(raw_id)
        entry = {"id": raw_id, "kind": (a or b)["kind"], "baseline": brief(a, normalize_baseline),
                 "candidate": brief(b, normalize_candidate)}
        if a is None:
            lists["added_ids"].append(entry)
            if b["outcome"] in NOT_PASSING:
                lists["new_not_passing"].append(entry)
            continue
        if b is None:
            lists["removed_ids"].append(entry)
            if a["outcome"] in NOT_PASSING:
                lists["no_longer_failing"].append(entry)
            continue
        va, vb = comparable(a, normalize_baseline), comparable(b, normalize_candidate)
        if a["outcome"] != b["outcome"]:
            if b["outcome"] in NOT_PASSING and a["outcome"] == "passed":
                lists["new_not_passing"].append(entry)
            elif a["outcome"] in NOT_PASSING and b["outcome"] == "passed":
                lists["no_longer_failing"].append(entry)
            else:
                lists["different_outcome"].append(entry)
                # TR-04: skipped or an expected failure in the baseline, and not passing now, is also new.
                if b["outcome"] in NOT_PASSING and a["outcome"] not in NOT_PASSING:
                    lists["new_not_passing"].append(entry)
            continue
        changed = False
        if va["reasons"] != vb["reasons"] or [e[:2] for e in va["events"]] != [e[:2] for e in vb["events"]]:
            lists["different_reason"].append(entry)
            changed = True
        if va["subtest_set"] != vb["subtest_set"]:
            lists["different_subtests"].append(entry)
            changed = True
        elif va["failing_subtests"] != vb["failing_subtests"] and not changed:
            lists["different_reason"].append(entry)
            changed = True
        if va["skip_reasons"] != vb["skip_reasons"]:
            lists["different_skip_reason"].append(entry)
            changed = True
        if a["occurrences"] != b["occurrences"]:
            lists["different_occurrences"].append(entry)
            changed = True
        if not changed:
            unchanged[a["outcome"]] += 1
            if a["outcome"] in NOT_PASSING:
                lists["unchanged_not_passing"].append(entry)
            elif a["outcome"] == "skipped":
                lists["unchanged_skipped"].append(entry)
            elif a["outcome"] == "expected_failure":
                lists["unchanged_expected_failures"].append(entry)
    return {name: unchanged.get(name, 0) for name in OUTCOMES}, lists


def attribution_results(rows, candidate_rows, normalize):
    """Each attribution against the candidate's record of that exact ID: equal statements, or what differs (TR-01).

    The statement of the candidate's record is built in the attribution's own declared form: raw
    texts, or the candidate's declared normalization. Only exact equality of the whole statement
    matches; nothing is matched by containment.
    """
    by_id = {row["id"]: row for row in candidate_rows}
    results = []
    for row in rows:
        form = normalize if row["form"] == "normalized" else (lambda text: text)
        expected = {key: row[key] for key in STATEMENT_KEYS}
        observed = record_statement(by_id.get(row["id"]), form)
        differences = statement_differences(expected, observed)
        results.append({"id": row["id"], "source": row.get("source"), "form": row["form"], "expected": expected,
                        "observed": observed, "observed_outcome": observed["outcome"] if observed else "missing",
                        "matches": not differences, "differences": differences})
    return results


def run_compare(args):
    started, monotonic = utc_now(), time.monotonic()
    sides = {}
    for name in ("baseline", "candidate"):
        summary, summary_binding = load_summary(getattr(args, name + "_summary"), getattr(args, name + "_summary_sha256"))
        raw, log_binding = bound_input(getattr(args, name + "_log"), getattr(args, name + "_log_sha256"), LOG_LIMIT,
                                       rule="LOG")
        step = unit_step(summary)
        if step is None:
            raise Refusal("SUMMARY", "The %s summary has no %s step" % (name, UNIT_STEP))
        named = (step.get("log_identity") or {}).get("sha256")
        if named != "sha256:" + log_binding["sha256"]:
            raise Refusal("BINDING", "The %s summary names another unit log" % name, named=named,
                          given="sha256:" + log_binding["sha256"])
        result = collect_log(raw)
        reading = result["driver_reading"]
        recorded = step.get("test_execution") or {}
        sides[name] = {"summary": summary, "summary_binding": summary_binding, "log_binding": log_binding,
                       "result": result, "normalize": Normalizer(summary, getattr(args, name + "_tmpdir")),
                       "driver_reading_matches_summary": all(recorded.get(key) == reading[key] for key in
                                                             ("tests_run", "skipped", "expected_failures",
                                                              "executed_without_skips"))}
    attributions, attribution_binding = (load_attributions(args.attributions, args.attributions_sha256)
                                         if args.attributions else ([], None))
    baseline, candidate = sides["baseline"], sides["candidate"]
    rows_a = baseline["result"]["tests"] + baseline["result"]["fixtures"]
    rows_b = candidate["result"]["tests"] + candidate["result"]["fixtures"]
    unchanged, lists = compare_records(rows_a, rows_b, baseline["normalize"], candidate["normalize"])
    attributed = attribution_results(attributions, rows_b, candidate["normalize"])
    by_attribution = {row["id"]: row for row in attributed}
    for entries in lists.values():
        for entry in entries:
            if entry["id"] in by_attribution:
                entry["attribution"] = {"matches": by_attribution[entry["id"]]["matches"],
                                        "source": by_attribution[entry["id"]]["source"]}
    differences = sum(len(lists[name]) for name in ("new_not_passing", "no_longer_failing", "different_outcome",
                                                    "different_reason", "different_subtests", "different_skip_reason",
                                                    "different_occurrences", "added_ids", "removed_ids"))
    summaries = summary_comparison(baseline["summary"], candidate["summary"])
    record = {"schema": COMPARISON_SCHEMA, "tool": tool_record(), "invocation": invocation_record(),
              "started_at_utc": started, "state": "COMPARED", "loaded_project_files": [],
              "inputs": {name: {"summary": sides[name]["summary_binding"], "log": sides[name]["log_binding"]}
                         for name in sides},
              "attributions_input": attribution_binding,
              "normalization": {name: sides[name]["normalize"].declared for name in sides},
              "logs": {name: {"footer": sides[name]["result"]["footer"], "counts": sides[name]["result"]["counts"],
                              "checks": sides[name]["result"]["checks"],
                              "driver_reading": sides[name]["result"]["driver_reading"],
                              "driver_reading_matches_summary": sides[name]["driver_reading_matches_summary"],
                              "noise_lines": sides[name]["result"]["noise"]["lines"]} for name in sides},
              "tests": {"baseline": baseline["result"]["footer"]["ran"], "candidate": candidate["result"]["footer"]["ran"]},
              "unchanged": unchanged,
              "counts": {name: len(entries) for name, entries in lists.items()},
              **lists,
              "attributions": attributed,
              "exempt": [],
              "summaries": summaries,
              "identical_item_4_lists": differences == 0,
              "rule": "Nothing is classified as exempt here. An attribution only says whether the candidate's complete "
                      "record of that exact ID equals the statement that the freeze gives, in its declared form."}
    record.update(finished_at_utc=utc_now(), elapsed_s=time.monotonic() - monotonic)
    write_new(args.output, json_text(record))
    sys.stderr.write("UNIT-LOG-COMPARISON " + json.dumps({"unchanged": unchanged, "counts": record["counts"],
                                                          "steps_different": summaries["steps_different"],
                                                          "reports_different": len(summaries["reports_different"])},
                                                         sort_keys=True) + "\n")
    same = (differences == 0 and not summaries["steps_different"] and not summaries["reports_different"]
            and summaries["pending_external_cases"]["equal"] and summaries["not_executed_steps"]["equal"])
    return EXIT_OK if same else EXIT_DIFFERS


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def build_parser():
    parser = _Parser(prog=TOOL, allow_abbrev=False, description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    collect = commands.add_parser("collect", allow_abbrev=False)
    collect.add_argument("--log", required=True)
    collect.add_argument("--log-sha256", required=True)
    collect.add_argument("--expect", action="append", metavar="ID=OUTCOME[*N]|ID=missing")
    collect.add_argument("--inventory")
    collect.add_argument("--inventory-sha256")
    collect.add_argument("--output", required=True)
    compare = commands.add_parser("compare", allow_abbrev=False)
    for name in ("baseline", "candidate"):
        compare.add_argument("--%s-log" % name, required=True)
        compare.add_argument("--%s-log-sha256" % name, required=True)
        compare.add_argument("--%s-summary" % name, required=True)
        compare.add_argument("--%s-summary-sha256" % name, required=True)
        compare.add_argument("--%s-tmpdir" % name, action="append", metavar="DIRECTORY")
    compare.add_argument("--attributions")
    compare.add_argument("--attributions-sha256")
    compare.add_argument("--output", required=True)
    return parser


def main(argv=None):
    output = None
    try:
        args = build_parser().parse_args(argv)
        output = prepare_output_file(args.output)
        require_dash_b()
        if args.command == "collect":
            return run_collect(args)
        if bool(args.attributions) != bool(args.attributions_sha256):
            raise Refusal("USAGE", "--attributions and --attributions-sha256 go together")
        return run_compare(args)
    except Refusal as exc:
        return report_end(output, {"schema": REFUSAL_SCHEMA, "tool": TOOL, "state": "REFUSED",
                                   "refusal": exc.as_dict()}, EXIT_REFUSED)
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        return report_end(output, {"schema": FAILURE_SCHEMA, "tool": TOOL, "state": "UNKNOWN",
                                   "error": {"type": type(exc).__name__, "reason": str(exc)}}, EXIT_UNKNOWN)


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
