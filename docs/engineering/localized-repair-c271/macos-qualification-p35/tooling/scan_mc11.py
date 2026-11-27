#!/usr/bin/env python3
"""MC11 scanner for gate MH of C271-P35: a static scan for process-creation calls.

It scans the 0.2.0 probe, the module loader the probe uses (tools/three_loader.mjs) and the 24
reader files, after checking every file's bytes: the probe against a SHA-256 supplied as an
argument, the reader tree against the dependencies inventory (also bound by a supplied SHA-256),
as an exact set of files with no link and no .DS_Store. It reads files only and starts nothing.

It reports two verdicts (TR-12):

* The frozen rule's, which decides MC11: MI's mc11_rule (CONTROLS-FROZEN.json), applied exactly as
  MI's line-based scan_javascript applies it, pattern for pattern. Process-creation names
  (child_process, cluster as an identifier, worker_threads, dlopen): none may occur. Dynamic
  constructs (eval, Function and createRequire substrings; require( and import( whose argument is
  not one string literal): each hit, as its kind and stripped line, must be in the file's reviewed
  list. Static specifiers whose keyword and string share a line: equal to the file's reviewed list
  as a multiset.
* A wider scan's, for review (TR-11). Every pattern runs on the raw text and on two transformed
  views of each line that holds an escape or a "+" (JavaScript escapes \\xHH, \\uHHHH and \\u{H}
  decoded; adjacent string literals joined across "+"). Each hit has its line, column, an advisory
  lexical context (code, comment, string, template or regular expression) and a snippet:
  - process creation: child_process and worker_threads in any letter case, cluster and Worker as
    names, dlopen, process.binding, _linkedBinding, internalBinding, execve, and the internal
    binding names spawn_sync and process_wrap in any letter case;
  - process call names: spawn, spawnSync, exec, execSync, execFile, execFileSync and fork, called
    directly, through a receiver or parenthesized, with the receiver, for review
    (RegExp.prototype.exec shares the name);
  - dynamic constructs: every eval and Function substring, classified; createRequire; require( and
    import( whose argument is not one string literal; every other require that is neither a plain
    call nor a declaration (a reference, a member, or a parenthesized callee, whose literal
    argument is also listed as a specifier); __non_webpack_require__; Module._load,
    module.constructor, process.mainModule and module.require; the bracket forms ['name'] of the
    process and module names; and a vm module specifier;
  - static module specifiers of import, export, require and import(), including statements that
    span lines, each resolved within the reader tree, to a node: builtin, or marked bare.

The wider scan's "none found" holds when no process-creation hit occurs in any view. Every process
call name and dynamic construct must appear in the reviewed list given with --reviewed. That list
must have the status REVIEWED and name its reviewer; any other list refuses (TR-12). Without a list,
every hit is pending review. A scan of names cannot exclude every dynamic route; the result states
that limit (contract section 5).

Launch (a start without -B refuses, N-09):

  <worktree>/.venv/bin/python -I -S -B scan_mc11.py --probe P --probe-sha256 H \\
      --dependencies-root D --dependencies-inventory I --dependencies-inventory-sha256 H \\
      [--reviewed R --reviewed-sha256 H] --output OUT
"""
from __future__ import annotations

import argparse
import bisect
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
import posixpath
import re
import stat
import sys
import time

SCHEMA = "ontokin.c271.p35-mc11-scan/2"
REVIEWED_SCHEMA = "ontokin.c271.p35-mc11-reviewed/2"
REVIEWED_STATUS = "REVIEWED"
REVIEWED_ENTRY_KEYS = {"process_call_names", "dynamic", "specifiers", "frozen_rule", "notes"}
DEPENDENCIES_SCHEMA = "ontokin.current-host-readback-dependencies/0.2.0"
INSTALL_SCHEMA = "ontokin.current-host-readback-install/0.2.0"
LOADER = "tools/three_loader.mjs"
PROBE_KEY = "<probe>"
READER_FILES = 24
LIMIT = ("A scan of names cannot exclude every dynamic route (contract section 5). It finds names and "
         "call shapes in the bytes of the bound files; a construct that computes a module name or a "
         "property name at run time, or code that a dynamic construct evaluates, is found only as that "
         "construct, and every such hit needs an independent review. The lexical context is advisory.")
FLAG_NAMES = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
              "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated",
              "dev_mode", "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
EXIT_NONE_FOUND, EXIT_FOUND_OR_UNREVIEWED, EXIT_REFUSED, EXIT_UNKNOWN = 0, 1, 2, 3
IDENT = r"[\w$]"

# The wider scan (TR-11): every pattern applies to the raw text and to every transformed view.
PROCESS_CREATION = (
    ("child_process", re.compile(r"child_process", re.IGNORECASE)),
    ("worker_threads", re.compile(r"worker_threads", re.IGNORECASE)),
    ("cluster", re.compile(r"(?<!" + IDENT + r")cluster(?!" + IDENT + r")")),
    ("Worker", re.compile(r"(?<!" + IDENT + r")Worker(?!" + IDENT + r")")),
    ("dlopen", re.compile(r"dlopen")),
    ("process.binding", re.compile(r"process\s*(?:\.|\[\s*['\"`])\s*(?:binding|_linkedBinding)(?!" + IDENT + r")")),
    ("_linkedBinding", re.compile(r"_linkedBinding")),
    ("internalBinding", re.compile(r"internalBinding")),
    ("execve", re.compile(r"(?<!" + IDENT + r")execve(?!" + IDENT + r")")),
    ("spawn_sync", re.compile(r"spawn_sync", re.IGNORECASE)),
    ("process_wrap", re.compile(r"process_wrap", re.IGNORECASE)))
CALL_NAMES = re.compile(r"(?<!" + IDENT + r")(spawn|spawnSync|exec|execSync|execFile|execFileSync|fork)"
                        r"(\s*\)\s*\(|\s*\()")
BRACKET_NAMES = ("child_process|worker_threads|cluster|dlopen|binding|_linkedBinding|internalBinding|mainModule"
                 "|constructor|_load|require|spawn|spawnSync|exec|execSync|execFile|execFileSync|fork|execve")
DYNAMIC = (
    ("eval", re.compile(r"eval")),
    ("Function", re.compile(r"Function")),
    ("createRequire", re.compile(r"createRequire")),
    ("module-loading", re.compile(r"(?<!" + IDENT + r")(?:Module\s*\.\s*_load|_load\s*\(|module\s*\.\s*constructor"
                                  r"|process\s*\.\s*mainModule|module\s*\.\s*require\s*\()")),
    ("bracket-access", re.compile(r"\[\s*(['\"`])(?:" + BRACKET_NAMES + r")\1\s*\]")),
    ("non-webpack-require", re.compile(r"__non_webpack_require__")),
    ("vm-specifier", re.compile(r"""(['"`])(?:node:)?vm\1""")))
CALLS = (("require", re.compile(r"(?<![\w$.])require\s*\(")), ("import", re.compile(r"(?<![\w$.])import\s*\(")))
REQUIRE_WORD = re.compile(r"(?<![\w$])require(?![\w$])")
DECLARATION_BEFORE = re.compile(r"(?<![\w$])(?:const|let|var|function)\s+$")
PARENTHESIZED_LITERAL = re.compile(r"""\s*\)\s*\(\s*(['"])((?:[^'"\\\n])*)\1\s*\)""")
LITERAL_ARGUMENT = re.compile(r"""\s*(['"])((?:[^'"\\\n])*)\1\s*\)""")
FROM_SPECIFIER = re.compile(r"""(?<![\w$.])from\s*(['"])([^'"\\\n]+)\1""")
BARE_IMPORT = re.compile(r"""(?<![\w$.])import\s*(['"])([^'"\\\n]+)\1""")
ESCAPE = re.compile(r"\\x([0-9A-Fa-f]{2})|\\u([0-9A-Fa-f]{4})|\\u\{([0-9A-Fa-f]{1,6})\}")
STRING = r"""'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*\""""
CONCATENATION = re.compile(r"(" + STRING + r")\s*\+\s*(" + STRING + r")")
REGEX_PRECEDING_WORDS = frozenset(("return", "typeof", "instanceof", "in", "of", "new", "delete", "void", "throw",
                                   "case", "do", "else", "yield", "await"))

# MI's frozen mc11_rule (CONTROLS-FROZEN.json), with the patterns of its implementation, scan_javascript in
# tests/test_current_host_readback_controls_v02.py, copied pattern for pattern (TR-12).
FROZEN_PROCESS_CREATION = (("child_process", re.compile(r"child_process")),
                           ("cluster", re.compile(r"(?<![\w$])cluster(?![\w$])")),
                           ("worker_threads", re.compile(r"worker_threads")),
                           ("process.dlopen", re.compile(r"dlopen")))
FROZEN_DYNAMIC = (("eval", re.compile(r"eval")), ("Function", re.compile(r"Function")),
                  ("createRequire", re.compile(r"createRequire")))
FROZEN_CALLS = (("require-call", re.compile(r"(?<![\w$.])require\s*\(")),
                ("import-call", re.compile(r"(?<![\w$.])import\s*\(")))
FROZEN_LITERAL_ARGUMENT = re.compile(r"""\s*(['"])([^'"\\]*)\1\s*\)""")
FROZEN_STATIC_SPECIFIER = re.compile(
    r"""^\s*(?:import|export)\b[^'";]*?\bfrom\s*(['"])([^'"]+)\1|^\s*import\s*(['"])([^'"]+)\3""")


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


# ---------------------------------------------------------------------------
# An advisory lexical map: comments, strings, templates and regular expressions
# ---------------------------------------------------------------------------

def _skip_string(text, i):
    quote, j, n = text[i], i + 1, len(text)
    while j < n:
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == quote or ch == "\n":
            return j + 1
        j += 1
    return n


def _skip_comment(text, i):
    if text.startswith("//", i):
        end = text.find("\n", i)
        return len(text) if end < 0 else end
    end = text.find("*/", i + 2)
    return len(text) if end < 0 else end + 2


def _skip_template(text, i, depth=0):
    j, n = i + 1, len(text)
    while j < n:
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == "`":
            return j + 1
        if ch == "$" and text.startswith("${", j):
            j = _skip_substitution(text, j + 2, depth + 1)
            continue
        j += 1
    return n


def _skip_substitution(text, j, depth):
    n, braces = len(text), 1
    if depth > 64:
        return n
    while j < n:
        ch = text[j]
        if ch in "'\"":
            j = _skip_string(text, j)
            continue
        if ch == "`":
            j = _skip_template(text, j, depth)
            continue
        if text.startswith("//", j) or text.startswith("/*", j):
            j = _skip_comment(text, j)
            continue
        if ch == "{":
            braces += 1
        elif ch == "}":
            braces -= 1
            if braces == 0:
                return j + 1
        j += 1
    return n


def lexical_ranges(text):
    """Sorted (start, end, kind) ranges; everything outside them is code. Heuristic, and advisory only."""
    ranges, i, n, previous = [], 0, len(text), None
    while i < n:
        ch = text[i]
        if text.startswith("//", i) or text.startswith("/*", i):
            j = _skip_comment(text, i)
            ranges.append((i, j, "comment"))
            i = j
            continue
        if ch in "'\"":
            j = _skip_string(text, i)
            ranges.append((i, j, "string"))
            i, previous = j, "value"
            continue
        if ch == "`":
            j = _skip_template(text, i)
            ranges.append((i, j, "template"))
            i, previous = j, "value"
            continue
        if ch == "/" and previous in (None, "operator", "keyword"):
            j, in_class = i + 1, False
            while j < n and text[j] != "\n":
                c = text[j]
                if c == "\\":
                    j += 2
                    continue
                if in_class:
                    in_class = c != "]"
                elif c == "[":
                    in_class = True
                elif c == "/":
                    break
                j += 1
            if j < n and text[j] == "/":
                j += 1
                while j < n and (text[j].isalnum() or text[j] in "$_"):
                    j += 1
                ranges.append((i, j, "regex"))
                i, previous = j, "value"
                continue
        if ch.isspace():
            i += 1
            continue
        if ch.isalnum() or ch in "$_":
            j = i
            while j < n and (text[j].isalnum() or text[j] in "$_"):
                j += 1
            previous = "keyword" if text[i:j] in REGEX_PRECEDING_WORDS else "value"
            i = j
            continue
        previous = "value" if ch in ")]}" else "operator"
        i += 1
    return ranges


class Locator:
    def __init__(self, text):
        self.text = text
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.ranges = lexical_ranges(text)
        self.range_starts = [row[0] for row in self.ranges]

    def line_column(self, offset):
        line = bisect.bisect_right(self.starts, offset) - 1
        return line + 1, offset - self.starts[line] + 1

    def context(self, offset):
        index = bisect.bisect_right(self.range_starts, offset) - 1
        if index >= 0 and self.ranges[index][0] <= offset < self.ranges[index][1]:
            return self.ranges[index][2]
        return "code"

    def snippet(self, start, end, width=60):
        line = bisect.bisect_right(self.starts, start) - 1
        line_end = self.text.find("\n", start)
        line_end = len(self.text) if line_end < 0 else line_end
        left = max(self.starts[line], start - width)
        right = min(line_end, end + width)
        return ("..." if left > self.starts[line] else "") + self.text[left:right] + ("..." if right < line_end else "")


def hit(locator, kind, start, end, **fields):
    line, column = locator.line_column(start)
    return {"pattern": kind, "line": line, "column": column, "context": locator.context(start),
            "text": locator.text[start:end], "snippet": locator.snippet(start, end), **fields}


# ---------------------------------------------------------------------------
# The scan of one file
# ---------------------------------------------------------------------------

def decode_escapes(line):
    def replace(match):
        value = match.group(1) or match.group(2) or match.group(3)
        try:
            return chr(int(value, 16))
        except ValueError:
            return match.group(0)
    return ESCAPE.sub(replace, line)


def join_concatenations(line):
    def replace(match):
        first, second = match.group(1), match.group(2)
        return first[0] + first[1:-1] + second[1:-1] + first[0]
    previous = None
    while previous != line:
        previous, line = line, CONCATENATION.sub(replace, line)
    return line


def function_class(text, start):
    before, after = text[max(0, start - 16):start], text[start + len("Function"):start + len("Function") + 16]
    word = re.search(IDENT + r"$", before) is None and re.match(IDENT, after) is None
    if not word:
        return "identifier-substring"
    if re.search(r"(?<!" + IDENT + r")new\s+$", before) or (re.match(r"\s*\(", after) and not before.endswith(".")):
        return "constructor-call"
    return "word"


def require_references(text):
    """Every require that is neither a plain call nor a declaration: (start, end, literal, literal_end)."""
    rows, plain = [], CALLS[0][1]
    for match in REQUIRE_WORD.finditer(text):
        start = match.start()
        if plain.match(text, start) or DECLARATION_BEFORE.search(text, max(0, start - 24), start):
            continue
        literal = PARENTHESIZED_LITERAL.match(text, match.end())
        rows.append((start, match.end(), literal.group(2) if literal else None, literal.end() if literal else None))
    return rows


def view_counts(view):
    """How often each pattern of the wider scan occurs in one view of a line."""
    counts = Counter()
    for name, pattern in PROCESS_CREATION:
        counts[("process_creation", name)] += sum(1 for _ in pattern.finditer(view))
    for match in CALL_NAMES.finditer(view):
        counts[("process_call_names", match.group(1))] += 1
    for name, pattern in DYNAMIC:
        counts[("dynamic", name)] += sum(1 for _ in pattern.finditer(view))
    for name, pattern in CALLS:
        for match in pattern.finditer(view):
            literal = LITERAL_ARGUMENT.match(view, match.end())
            counts[("dynamic", name + ("-literal" if literal is not None else "-computed"))] += 1
    counts[("dynamic", "require-reference")] += len(require_references(view))
    return counts


def scan_text(text, kind):
    locator = Locator(text)
    result = {"process_creation": [], "process_call_names": [], "dynamic": [], "specifiers": []}
    for name, pattern in PROCESS_CREATION:
        for match in pattern.finditer(text):
            result["process_creation"].append(hit(locator, name, match.start(), match.end(), view="raw"))
    for match in CALL_NAMES.finditer(text):
        start = match.start()
        receiver = text[max(0, start - 40):start]
        result["process_call_names"].append(hit(locator, match.group(1), start, match.end(),
                                                method_call=receiver.rstrip().endswith("."),
                                                parenthesized=match.group(2).strip().startswith(")"),
                                                receiver=receiver.splitlines()[-1] if receiver.strip() else ""))
    for name, pattern in DYNAMIC:
        for match in pattern.finditer(text):
            fields = {}
            if name == "Function":
                fields["classification"] = function_class(text, match.start())
            elif name == "eval":
                before, after = text[max(0, match.start() - 1):match.start()], text[match.end():match.end() + 1]
                fields["classification"] = "identifier-substring" if (re.match(IDENT, before or " ") or
                                                                       re.match(IDENT, after or " ")) else "word"
            result["dynamic"].append(hit(locator, name, match.start(), match.end(), **fields))
    for name, pattern in CALLS:
        for match in pattern.finditer(text):
            literal = LITERAL_ARGUMENT.match(text, match.end())
            if literal is not None:
                result["specifiers"].append(dict(hit(locator, name + "-literal", match.start(), literal.end()),
                                                 specifier=literal.group(2)))
            else:
                result["dynamic"].append(hit(locator, name + "-computed", match.start(), match.end()))
    for start, end, literal, literal_end in require_references(text):
        result["dynamic"].append(hit(locator, "require-reference", start, end))
        if literal is not None:
            result["specifiers"].append(dict(hit(locator, "require-parenthesized", start, literal_end),
                                             specifier=literal))
    for name, pattern in (("from", FROM_SPECIFIER), ("import-statement", BARE_IMPORT)):
        for match in pattern.finditer(text):
            result["specifiers"].append(dict(hit(locator, name, match.start(), match.end()), specifier=match.group(2)))
    # Every pattern on the transformed views of each line with an escape or a "+": a hit is reported when a
    # view shows a pattern more often than the view before it (raw, then decoded, then joined).
    for number, start in enumerate(locator.starts, 1):
        end = text.find("\n", start)
        line = text[start:len(text) if end < 0 else end]
        if "\\" not in line and "+" not in line:
            continue
        decoded = decode_escapes(line)
        for view, before, transformed in (("decoded", line, decoded), ("joined", decoded, join_concatenations(decoded))):
            if transformed == before:
                continue
            added = view_counts(transformed) - view_counts(before)
            # A require literal that only a transformed view shows was computed in the source: a dynamic hit.
            for (category, name), count in sorted(added.items()):
                result[category].append({"pattern": name, "line": number, "column": None, "view": view,
                                         "added": count, "context": "transformed line", "text": transformed[:400],
                                         "snippet": line[:400]})
    for key in result:
        result[key].sort(key=lambda row: (row["line"], row["column"] or 0, row["pattern"]))
    result["lines"] = len(locator.starts)
    return result


def frozen_rule_scan(text):
    """MI's mc11_rule, line by line, exactly as MI's scan_javascript applies it."""
    found = {"process_creation": [], "dynamic": [], "static_specifiers": []}
    for line in text.splitlines():
        stripped = line.strip()
        for kind, pattern in FROZEN_PROCESS_CREATION:
            found["process_creation"] += [[kind, stripped] for _ in pattern.finditer(line)]
        for kind, pattern in FROZEN_DYNAMIC:
            found["dynamic"] += [[kind, stripped] for _ in pattern.finditer(line)]
        for kind, pattern in FROZEN_CALLS:
            for match in pattern.finditer(line):
                literal = FROZEN_LITERAL_ARGUMENT.match(line, match.end())
                if literal is not None:
                    found["static_specifiers"].append(literal.group(2))
                else:
                    found["dynamic"].append([kind, stripped])
        static = FROZEN_STATIC_SPECIFIER.match(line)
        if static is not None:
            found["static_specifiers"].append(static.group(2) or static.group(4))
    return found


def frozen_verdict(found, entry):
    """The frozen rule's expectations for one file, against that file's reviewed entry."""
    rule = entry.get("frozen_rule") if type(entry) is dict else None
    verdict = {"process_creation_none": not found["process_creation"], "reviewed_entry": type(rule) is dict}
    if type(rule) is not dict:
        verdict.update(unreviewed_dynamic=found["dynamic"], reviewed_but_absent=[], specifiers_equal_review=None,
                       passed=False)
        return verdict
    actual, reviewed = Counter(tuple(item) for item in found["dynamic"]), Counter(tuple(item) for item in rule["dynamic"])
    verdict.update(unreviewed_dynamic=sorted(list(item) for item in (actual - reviewed).elements()),
                   reviewed_but_absent=sorted(list(item) for item in (reviewed - actual).elements()),
                   specifiers_equal_review=sorted(found["static_specifiers"]) == sorted(rule["static_specifiers"]))
    verdict["passed"] = (verdict["process_creation_none"] and not verdict["unreviewed_dynamic"]
                         and verdict["specifiers_equal_review"])
    return verdict


def resolve(specifier, rel, files):
    if specifier.startswith("node:"):
        return "node-builtin"
    if specifier.startswith(("./", "../")) and rel is not None:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(rel), specifier))
        return "reader-file:" + target if target in files else "unresolved:" + target
    return "bare"


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def read_bound(path, sha256, what, maximum):
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise Refusal("DIGEST", "Expected a lowercase SHA-256 for the " + what)
    raw, binding = read_regular(canonical_path(path, kind="file", rule="INPUT"), maximum)
    if binding["sha256"] != sha256:
        raise Refusal("DIGEST", "The " + what + " differs from its supplied SHA-256", path=path,
                      observed=binding["sha256"])
    return raw, {"path": path, **binding}


def inventory_files(document):
    if type(document) is not dict:
        raise Refusal("INVENTORY", "The dependencies inventory is not an object")
    schema = document.get("schema")
    if schema == INSTALL_SCHEMA and document.get("purpose") != "retained-dependencies":
        raise Refusal("INVENTORY", "An install plan serves only with purpose retained-dependencies")
    if schema not in (DEPENDENCIES_SCHEMA, INSTALL_SCHEMA):
        raise Refusal("INVENTORY", "The inventory is neither " + DEPENDENCIES_SCHEMA + " nor " + INSTALL_SCHEMA)
    files = document.get("files")
    if type(files) is not dict or len(files) != READER_FILES:
        raise Refusal("INVENTORY", "The inventory does not list exactly 24 reader files")
    for rel, binding in files.items():
        if (type(rel) is not str or rel.startswith("/") or posixpath.normpath(rel) != rel or ".." in rel.split("/")
                or type(binding) is not dict or set(binding) != {"sha256", "size_bytes", "mode"}):
            raise Refusal("INVENTORY", "A reader-file entry is malformed", file=rel)
    if LOADER not in files:
        raise Refusal("INVENTORY", "The module loader " + LOADER + " is not among the reader files")
    return schema, files


def tree_files(root):
    found, refused = [], []
    for parent, directories, names in os.walk(root, followlinks=False):
        for name in directories + names:
            path = os.path.join(parent, name)
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                refused.append(os.path.relpath(path, root))
            elif name == ".DS_Store":
                refused.append(os.path.relpath(path, root))
            elif stat.S_ISREG(info.st_mode):
                found.append(os.path.relpath(path, root))
    return sorted(found), sorted(refused)


def load_reviewed(path, sha256):
    """A reviewed list: its status must be REVIEWED and it must name its reviewer (TR-12)."""
    raw, binding = read_bound(path, sha256, "reviewed list", 16 * 1024 * 1024)
    document = strict_json(raw, what="reviewed list")
    if type(document) is not dict or document.get("schema") != REVIEWED_SCHEMA or type(document.get("files")) is not dict:
        raise Refusal("REVIEWED", "The reviewed list is not a " + REVIEWED_SCHEMA + " document")
    if document.get("status") != REVIEWED_STATUS:
        raise Refusal("REVIEWED", "The reviewed list's status is not REVIEWED; an unreviewed list cannot decide MC11",
                      status=document.get("status"))
    reviewer = document.get("reviewer")
    if type(reviewer) is not str or not reviewer.strip():
        raise Refusal("REVIEWED", "The reviewed list does not name its reviewer")

    def keys(items, shape):
        return type(items) is list and all(type(item) is list and len(item) == len(shape)
                                           and all(check(value) for check, value in zip(shape, item)) for item in items)
    text = lambda value: type(value) is str  # noqa: E731
    line = lambda value: type(value) is int and value > 0  # noqa: E731
    column = lambda value: value is None or (type(value) is int and value > 0)  # noqa: E731
    for key, entry in document["files"].items():
        rule = entry.get("frozen_rule") if type(entry) is dict else None
        if (type(entry) is not dict or not set(entry) <= REVIEWED_ENTRY_KEYS
                or not keys(entry.get("process_call_names", []), (text, line, column))
                or not keys(entry.get("dynamic", []), (text, line, column))
                or not (type(entry.get("specifiers", [])) is list and all(map(text, entry.get("specifiers", []))))
                or not (rule is None or (type(rule) is dict and set(rule) == {"dynamic", "static_specifiers"}
                                         and keys(rule["dynamic"], (text, text))
                                         and type(rule["static_specifiers"]) is list
                                         and all(map(text, rule["static_specifiers"]))))):
            raise Refusal("REVIEWED", "A reviewed entry is malformed", file=key)
    return document["files"], dict(binding, status=document["status"], reviewer=reviewer)


def reviewed_key(row):
    return [row["pattern"], row["line"], row["column"]]


def compare_reviewed(scan, reviewed):
    entry = reviewed if type(reviewed) is dict else {}
    rows = {}
    for key in ("process_call_names", "dynamic"):
        actual = sorted(reviewed_key(row) for row in scan[key])
        expected = sorted(list(item) for item in entry.get(key, []))
        rows[key] = {"unreviewed": [item for item in actual if item not in expected],
                     "reviewed_but_absent": [item for item in expected if item not in actual]}
    specifiers = sorted(row["specifier"] for row in scan["specifiers"])
    rows["specifiers"] = {"equal": specifiers == sorted(entry.get("specifiers", [])) if type(reviewed) is dict else False,
                          "found": specifiers}
    rows["matches"] = (type(reviewed) is dict and rows["specifiers"]["equal"]
                       and not any(rows[key]["unreviewed"] or rows[key]["reviewed_but_absent"]
                                   for key in ("process_call_names", "dynamic")))
    return rows


def run(args, output):
    started, monotonic = utc_now(), time.monotonic()
    probe_raw, probe_binding = read_bound(args.probe, args.probe_sha256, "probe", 4 * 1024 * 1024)
    root = canonical_path(args.dependencies_root, kind="dir", rule="INPUT")
    inventory_raw, inventory_binding = read_bound(args.dependencies_inventory, args.dependencies_inventory_sha256,
                                                  "dependencies inventory", 4 * 1024 * 1024)
    schema, files = inventory_files(strict_json(inventory_raw, what="dependencies inventory"))
    found, refused = tree_files(root)
    if refused or found != sorted(files):
        raise Refusal("TREE", "The reader tree is not exactly the inventory's 24 regular files",
                      missing=sorted(set(files) - set(found)), extra=sorted(set(found) - set(files)), refused=refused)
    reviewed, reviewed_binding = (load_reviewed(args.reviewed, args.reviewed_sha256) if args.reviewed
                                  else (None, None))
    scans, total = {}, {"process_creation": 0, "process_call_names": 0, "dynamic": 0, "specifiers": 0}
    targets = [(PROBE_KEY, args.probe, probe_raw, probe_binding, None)]
    for rel in sorted(files):
        raw, binding = read_regular(root + "/" + rel, 16 * 1024 * 1024)
        if binding != {key: files[rel][key] for key in ("sha256", "size_bytes", "mode")}:
            raise Refusal("TREE", "A reader file differs from the inventory", file=rel, observed=binding)
        targets.append((rel, root + "/" + rel, raw, binding, rel))
    for key, path, raw, binding, rel in targets:
        text = raw.decode("utf-8", "surrogateescape")
        extension = posixpath.splitext(path)[1].lower()
        scan = scan_text(text, extension)
        for row in scan["specifiers"]:
            row["resolution"] = resolve(row["specifier"], rel, files)
        role = "probe" if key == PROBE_KEY else "module loader" if rel == LOADER else "reader file"
        frozen = frozen_rule_scan(text)
        entry = {"path": path, "role": role, "kind": "javascript" if extension in (".js", ".mjs", ".cjs") else
                 "json" if extension == ".json" else "text", **binding, **scan,
                 "frozen_rule": {"found": frozen,
                                 "verdict": frozen_verdict(frozen, reviewed.get(key) if reviewed is not None else None)}}
        if reviewed is not None:
            entry["review"] = compare_reviewed(scan, reviewed.get(key))
        scans[key] = entry
        for name in total:
            total[name] += len(scan[name])
    unresolved = sorted({row["resolution"] for entry in scans.values() for row in entry["specifiers"]
                         if row["resolution"].startswith("unresolved:")})
    none_found = total["process_creation"] == 0
    reviewed_ok = reviewed is not None and all(entry["review"]["matches"] for entry in scans.values()) and \
        set(reviewed) <= set(scans)
    frozen = {"source": "CONTROLS-FROZEN.json mc11_rule, applied as MI's scan_javascript applies it",
              "decides_mc11": True,
              "process_creation_none": all(entry["frozen_rule"]["verdict"]["process_creation_none"]
                                           for entry in scans.values()),
              "dynamic_hits": sum(len(entry["frozen_rule"]["found"]["dynamic"]) for entry in scans.values()),
              "unreviewed_dynamic_hits": sum(len(entry["frozen_rule"]["verdict"]["unreviewed_dynamic"])
                                             for entry in scans.values()),
              "specifiers_equal_review": reviewed is not None and all(
                  entry["frozen_rule"]["verdict"]["specifiers_equal_review"] for entry in scans.values())}
    frozen["passed"] = (reviewed is not None and set(reviewed) <= set(scans)
                        and all(entry["frozen_rule"]["verdict"]["passed"] for entry in scans.values()))
    record = {"schema": SCHEMA, "tool": tool_record(), "invocation": invocation_record(), "started_at_utc": started,
              "inputs": {"probe": probe_binding, "dependencies_root": root, "dependencies_inventory":
                         dict(inventory_binding, schema=schema), "reviewed": reviewed_binding},
              "files": scans, "totals": total, "unresolved_relative_specifiers": unresolved,
              "frozen_rule": frozen,
              "wider_scan": {"none_found": none_found, "reviewed_list_matches": reviewed_ok if reviewed is not None
                             else None, "unresolved_relative_specifiers": len(unresolved)},
              "none_found": none_found, "reviewed_list_given": reviewed is not None,
              "reviewed_list_matches": reviewed_ok if reviewed is not None else None,
              "reviewed_keys_not_scanned": sorted(set(reviewed) - set(scans)) if reviewed is not None else [],
              "limit": LIMIT, "loaded_project_files": [], "finished_at_utc": utc_now(),
              "elapsed_s": time.monotonic() - monotonic}
    write_new(output, json_text(record))
    sys.stderr.write("MH-MC11 " + json.dumps({"frozen_rule_passed": frozen["passed"], "none_found": none_found,
                                             "totals": total, "reviewed_list_matches": record["reviewed_list_matches"]},
                                            sort_keys=True) + "\n")
    passed = frozen["passed"] and none_found and reviewed_ok and not unresolved
    return EXIT_NONE_FOUND if passed else EXIT_FOUND_OR_UNREVIEWED


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("USAGE", "Invalid arguments: " + message)


def main(argv=None):
    parser = _Parser(prog="scan_mc11.py", allow_abbrev=False, description=__doc__.splitlines()[0])
    for name in ("probe", "dependencies-inventory"):
        parser.add_argument("--" + name, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--dependencies-root", required=True)
    parser.add_argument("--reviewed")
    parser.add_argument("--reviewed-sha256")
    parser.add_argument("--output", required=True)
    output = None
    try:
        args = parser.parse_args(argv)
        if (args.reviewed is None) != (args.reviewed_sha256 is None):
            raise Refusal("USAGE", "--reviewed and --reviewed-sha256 go together")
        output = prepare_output_file(args.output)
        require_no_bytecode()
        return run(args, output)
    except Refusal as exc:
        return report_end(output, {"schema": "ontokin.c271.p35-tool-refusal/1", "tool": "scan_mc11.py",
                                   "state": "REFUSED", "refusal": exc.as_dict()}, EXIT_REFUSED)
    except BaseException as exc:  # an unexpected failure is reported as unknown, never as a result
        return report_end(output, {"schema": "ontokin.c271.p35-tool-failure/1", "tool": "scan_mc11.py",
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
