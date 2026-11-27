"""Hygiene of the MH tooling, and the start count of this test run. It runs last (by name) and starts nothing.

* No tooling file holds a machine path, the package manager's name or the account's name. The
  forbidden strings are derived at run time from this machine (TR-04), so that no file holds a
  literal or a fragment of them, this one included: the home directory and the account name; the
  parent of the worktree; the local root above the phase's directory, when the tooling lies outside
  the worktree; the interpreter's base prefix; the temporary directory. Each path and its ancestors
  are searched as text, and each of their non-generic components as a word, case-insensitively.
  Python files are searched again with their string literals joined, since a split literal is still
  a literal: literals that are adjacent or added, and runs of literals in one tuple, list, set or
  call, such as the parts that a join would put together. A failure names the file and the kind of
  string, never the string.
* Every tool imports the standard library only, never another tool, and none imports subprocess:
  the tools that start processes do so only through the project's Darwin supervisor.
* Every tool has the same exclusive-output and self-identification helpers, and refuses a start
  without -B.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path
import pwd
import re
import sys
import tempfile
import unittest

import mh_support as S

TOOLS = ("discover_inventory.py", "collect_outcomes.py", "run_direct_probe.py", "audit_numeric.py", "scan_mc11.py",
         "control_harness.py", "capture_probe.py")
# Directory names of any macOS or Python layout; none of them identifies a machine, an account or a manager.
GENERIC = frozenset(("volumes", "users", "library", "applications", "system", "usr", "local", ".local", "bin",
                     "sbin", "lib", "opt", "private", "var", "tmp", "etc", "share", "include", "frameworks",
                     "python.framework", "versions", "current", "resources", "contents", "macos", "site-packages",
                     "developer", "home", "folders", "python", "python3", "t"))
VERSION = re.compile(r"(?:python)?\d+(?:\.\d+)*", re.IGNORECASE)
PHASE = re.compile(r"c\d+-p\d+")
JOINED = re.compile(r"""(['"])\s*\+?\s*(['"])""")


def ancestors(path, depth=2):
    """The path and each ancestor with at least `depth` components."""
    parts = [part for part in path.split("/") if part]
    return ["/" + "/".join(parts[:index]) for index in range(len(parts), depth - 1, -1)]


def components(path):
    return [part for part in path.split("/") if part and part.lower() not in GENERIC and not VERSION.fullmatch(part)]


def forbidden_strings():
    """(kind, text, as_word) for every private string of this machine, derived now."""
    rows = []
    home = os.path.expanduser("~")
    account = pwd.getpwuid(os.getuid()).pw_name
    rows += [("home directory", path, False) for path in {home, os.path.realpath(home)}]
    rows.append(("account name", account, True))
    rows += [("part of the account name", part, True) for part in re.split(r"[^A-Za-z0-9]+", account) if len(part) >= 3]
    sources = {"worktree parent": [os.path.dirname(S.project_root())],
               "interpreter prefix": [sys.base_prefix, os.path.realpath(sys.base_prefix)],
               "temporary directory": [os.path.realpath(tempfile.gettempdir())]}
    tooling = str(S.TOOLING.resolve())
    parts = tooling.split("/")
    phase = next((index for index, part in enumerate(parts) if PHASE.fullmatch(part)), None)
    if not tooling.startswith(S.project_root() + "/") and phase is not None:
        sources["local root"] = ["/".join(parts[:phase])]
    for kind, paths in sources.items():
        for path in paths:
            rows += [(kind + " path", item, False) for item in ancestors(path, 3 if kind == "temporary directory" else 2)]
            if kind != "temporary directory":
                rows += [(kind + " component", item, True) for item in components(path)]
    unique, seen = [], set()
    for kind, text, word in rows:
        if text and (text.lower(), word) not in seen:
            seen.add((text.lower(), word))
            unique.append((kind, text, word))
    return unique


def literal_views(source):
    """The joined forms of a Python file's string literals: each run of literal siblings, and each sum of them."""
    views = [JOINED.sub("", source)]
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            parts = [part for part in (node.left, node.right) if isinstance(part, ast.Constant)
                     and isinstance(part.value, str)]
            views.append("".join(part.value for part in parts))
        for field in ("elts", "args", "values", "keys"):
            children = getattr(node, field, None)
            if not isinstance(children, list):
                continue
            run = []
            for child in children + [None]:
                if isinstance(child, ast.Constant) and isinstance(child.value, str):
                    run.append(child.value)
                    continue
                if len(run) > 1:
                    views.append("".join(run))
                run = []
    return views


def found(text, item, word):
    if not word:
        return item.lower() in text.lower()
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(item) + r"(?![A-Za-z0-9_])", text, re.IGNORECASE) is not None


class HygieneTests(unittest.TestCase):
    def test_no_machine_path_package_manager_or_account_name_in_any_tooling_file(self):
        strings = forbidden_strings()
        self.assertTrue(any(kind == "account name" for kind, _, _ in strings))
        for path in sorted(S.TOOLING.rglob("*")):
            if not (path.is_file() and path.suffix in (".py", ".md", ".txt", ".json")):
                continue
            text = path.read_text(encoding="utf-8")
            views = [text] + (literal_views(text) if path.suffix == ".py" else [])
            for index, (kind, item, word) in enumerate(strings):
                with self.subTest(file=str(path.relative_to(S.TOOLING)), kind="%s %d" % (kind, index)):
                    self.assertFalse(any(found(view, item, word) for view in views),
                                     "a derived private string occurs in this file")

    def test_the_derivation_finds_a_split_literal(self):
        account = pwd.getpwuid(os.getuid()).pw_name
        for split in (repr(account[:2]) + " " + repr(account[2:]), repr(account[:2]) + " + " + repr(account[2:]),
                      "NAME = ''.join((" + repr(account[:2]) + ", " + repr(account[2:]) + "))\n"):
            with self.subTest(form=split.replace(account[:2], "<first>").replace(account[2:], "<rest>")):
                self.assertFalse(found(split, account, True))
                self.assertTrue(any(found(view, account, True) for view in literal_views(split)))

    def test_tools_import_the_standard_library_only_and_never_subprocess(self):
        allowed = set(sys.stdlib_module_names)
        for name in TOOLS:
            tree = ast.parse((S.TOOLING / name).read_bytes())
            modules = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    modules.add(node.module.split(".")[0])
            project = {"prototypes"} if name == "control_harness.py" else set()
            with self.subTest(tool=name):
                self.assertEqual(sorted(modules - allowed - project), [])
                self.assertNotIn("subprocess", modules)

    def test_every_tool_writes_exclusively_identifies_itself_and_requires_dash_b(self):
        for name in TOOLS:
            text = (S.TOOLING / name).read_text(encoding="utf-8")
            with self.subTest(tool=name):
                self.assertIn("os.O_EXCL", text)
                self.assertIn("os.fsync", text)
                self.assertIn("def tool_record", text)
                self.assertIn("def invocation_record", text)
                self.assertIn("flags.dont_write_bytecode", text)
                self.assertTrue(text.startswith("#!/usr/bin/env python3\n"))

    def test_zz_report_the_starts_of_this_run(self):
        print("\nMH-TOOLING-TEST-STARTS direct children: %s; started by the tools under test: %s"
              % (dict(sorted(S.STARTS.items())), dict(sorted(S.TOOL_STARTS.items()))), file=sys.stderr)


if __name__ == "__main__":
    unittest.main()
