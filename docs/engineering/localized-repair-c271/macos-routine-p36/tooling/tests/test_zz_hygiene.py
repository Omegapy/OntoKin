"""Hygiene of the MR tooling, and the start count of this test run. It runs last (by name) and starts nothing.

* No tooling file holds a machine path, an account name or the name of software installed on this
  machine. The forbidden strings are derived at run time (MH's TR-04), so that no file holds a
  literal or a fragment of them, this one included: the home directory and the account name; the
  directory above the checkout when the tooling sits at its committed place, or the local root above
  the phase directory when it does not; the interpreter's base prefix; the temporary directory. Each
  path and its ancestors are searched as text, and each component as a word, ignoring case, unless it
  is generic or public vocabulary of the project: its task and phase IDs (C271, C271-P36) and its
  worker labels (W2, W3-tooling-001), which the tooling writes as such (TR-07). So the outcome does
  not depend on where the checkout lies, and no assertion needs this host's interpreter prefix to
  have a component of its own. Python files are searched again with their string literals joined,
  since a split literal is still a literal. A failure names the file and the kind of string, never
  the string.
* Every tool imports the standard library only, never another tool and never subprocess; it refuses
  a start without -B before any other import; it writes exclusively and identifies itself.
* This test process made no process-creation event (the audit hook of w2_support counts them).
"""
import ast
import os
import pwd
import re
import sys
import tempfile
import unittest

import w2_support as S

TOOLS = ("unit_log_outcomes.py", "readback_evidence.py")
COMMITTED_PLACE = "docs/engineering/localized-repair-c271/macos-routine-p36/tooling"
GENERIC = frozenset(("volumes", "users", "library", "applications", "system", "usr", "local", ".local", "bin",
                     "sbin", "lib", "opt", "private", "var", "tmp", "etc", "share", "include", "frameworks",
                     "python.framework", "versions", "current", "resources", "contents", "macos", "site-packages",
                     "developer", "home", "folders", "python", "python3", "t", "libexec", "docs", "engineering",
                     "tooling", "tests", "workers"))
VERSION = re.compile(r"(?:python)?\d+(?:\.\d+)*", re.IGNORECASE)
PHASE = re.compile(r"c\d+-p\d+")
# The project's own task, phase and worker names, and the phase directory's own subdirectories (TR-07).
PUBLIC = re.compile(r"c\d+(?:-p\d+)?|w\d+(?:-[a-z]+(?:-\d+)?)?|workers|director", re.IGNORECASE)
JOINED = re.compile(r"""(['"])\s*\+?\s*(['"])""")


def ancestors(path, depth=2):
    parts = [part for part in path.split("/") if part]
    return ["/" + "/".join(parts[:index]) for index in range(len(parts), depth - 1, -1)]


def components(path):
    return [part for part in path.split("/") if part and part.lower() not in GENERIC and not VERSION.fullmatch(part)
            and not PUBLIC.fullmatch(part)]


def forbidden_strings(tooling=None):
    """(kind, text, as_word) for every private string of this machine, derived now, for the tooling at its path."""
    rows = []
    home = os.path.expanduser("~")
    account = pwd.getpwuid(os.getuid()).pw_name
    rows += [("home directory", path, False) for path in {home, os.path.realpath(home)}]
    rows.append(("account name", account, True))
    rows += [("part of the account name", part, True) for part in re.split(r"[^A-Za-z0-9]+", account) if len(part) >= 3]
    tooling = str(S.TOOLING) if tooling is None else tooling
    sources = {"interpreter prefix": [sys.base_prefix, os.path.realpath(sys.base_prefix)],
               "temporary directory": [os.path.realpath(tempfile.gettempdir())]}
    if tooling.endswith("/" + COMMITTED_PLACE):
        sources["checkout parent"] = [os.path.dirname(tooling[:-len(COMMITTED_PLACE) - 1])]
    else:
        parts = tooling.split("/")
        phase = next((index for index, part in enumerate(parts) if PHASE.fullmatch(part)), None)
        sources["local root"] = ["/".join(parts[:phase])] if phase else [os.path.dirname(tooling)]
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


class Hygiene(unittest.TestCase):
    def test_no_machine_path_account_name_or_installed_software_name_in_any_tooling_file(self):
        strings = forbidden_strings()
        self.assertTrue(any(kind == "account name" for kind, _, _ in strings))
        checked = 0
        for path in sorted(S.TOOLING.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            views = [text] + (literal_views(text) if path.suffix == ".py" else [])
            checked += 1
            for index, (kind, item, word) in enumerate(strings):
                with self.subTest(file=str(path.relative_to(S.TOOLING)), kind="%s %d" % (kind, index)):
                    self.assertFalse(any(found(view, item, word) for view in views),
                                     "a derived private string occurs in this file")
        self.assertGreaterEqual(checked, 7)

    def test_tr07_the_projects_own_names_are_public_wherever_the_checkout_lies(self):
        parent = "/root-a/local-b/c271-p36/workers/W3-tooling-001"
        strings = forbidden_strings(parent + "/clone/" + COMMITTED_PLACE)
        words = {text for kind, text, word in strings if word and kind.startswith("checkout parent")}
        self.assertEqual(words, {"root-a", "local-b"})
        strings = forbidden_strings("/root-a/local-b/c271-p36/workers/W2/tooling")
        words = {text for kind, text, word in strings if word and kind.startswith("local root")}
        self.assertEqual(words, {"root-a", "local-b"})
        for name in ("C271", "c271-p36", "C271-P36", "W2", "w3-tooling-001", "workers", "director"):
            with self.subTest(name=name):
                self.assertEqual(components("/x/" + name), ["x"])

    def test_the_derivation_finds_a_split_literal(self):
        account = pwd.getpwuid(os.getuid()).pw_name
        for split in (repr(account[:2]) + " " + repr(account[2:]), repr(account[:2]) + " + " + repr(account[2:]),
                      "NAME = ''.join((" + repr(account[:2]) + ", " + repr(account[2:]) + "))\n"):
            with self.subTest(form=split.replace(account[:2], "<first>").replace(account[2:], "<rest>")):
                self.assertFalse(found(split, account, True))
                self.assertTrue(any(found(view, account, True) for view in literal_views(split)))

    def test_tools_import_the_standard_library_only_never_another_tool_or_subprocess(self):
        allowed = set(sys.stdlib_module_names)
        for name in TOOLS:
            tree = ast.parse((S.TOOLING / name).read_bytes())
            modules = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.level, 0, name)
                    modules.add(node.module.split(".")[0])
            with self.subTest(tool=name):
                self.assertEqual(sorted(modules - allowed), [])
                self.assertNotIn("subprocess", modules)
                self.assertFalse(modules & {tool[:-3] for tool in TOOLS})

    def test_every_tool_refuses_without_dash_b_first_writes_exclusively_and_identifies_itself(self):
        for name in TOOLS:
            text = (S.TOOLING / name).read_text(encoding="utf-8")
            with self.subTest(tool=name):
                self.assertTrue(text.startswith("#!/usr/bin/env python3\n"))
                guard = text.index('if __name__ == "__main__" and _missing_dash_b():')
                self.assertEqual([line for line in text[:guard].splitlines() if line.startswith(("import ", "from "))],
                                 ["import sys"])
                for needle in ("os.O_EXCL", "os.fsync", "def tool_record", "def invocation_record",
                               ".dont_write_bytecode", '"loaded_project_files": []'):
                    self.assertIn(needle, text)

    def test_zz_this_run_started_no_process(self):
        print("\nW2-TOOLING-TEST-STARTS process-creation events in this test process: %d" % len(S.STARTS),
              file=sys.stderr)
        self.assertEqual(S.STARTS, [])


if __name__ == "__main__":
    unittest.main()
