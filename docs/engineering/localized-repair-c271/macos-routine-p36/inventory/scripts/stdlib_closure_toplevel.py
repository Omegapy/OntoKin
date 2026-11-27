"""W1 (C271-P36) module-level standard-library import closure. Reads source files only; imports nothing it scans.

Run only as: python3 -I -S -B stdlib_closure_toplevel.py STDLIB_ROOT PYC_REPORT OUTFILE LABEL=MOD[,MOD...] ...

Like stdlib_closure.py, but it follows only the imports that run when a module is imported: module-level
statements and class bodies, including try/except and with blocks, and both arms of an if statement,
except that the arms that test for Windows (sys.platform == "win32", sys.platform.startswith("win"),
os.name == "nt", _mswindows, MS_WINDOWS, _WINDOWS) are resolved as on macOS, and "if TYPE_CHECKING" bodies
are skipped. Function bodies are not followed; for each reached module the script also lists the names
imported inside its functions, so that the executed code paths can be reviewed by reading.
"""
from __future__ import annotations

import ast
import json
import os
import sys

FROZEN = {"zipimport", "abc", "codecs", "io", "_collections_abc", "_sitebuiltins", "genericpath", "ntpath",
          "posixpath", "os", "site", "stat", "importlib.util", "importlib.machinery", "runpy", "__hello__",
          "__phello__", "importlib._bootstrap", "importlib._bootstrap_external"}
WINDOWS_NAMES = {"_mswindows", "MS_WINDOWS", "_WINDOWS", "_IS_WINDOWS", "WINDOWS"}


def resolve(root, name):
    parts = name.split(".")
    base = os.path.join(root, *parts)
    if os.path.isfile(os.path.join(base, "__init__.py")):
        return os.path.join(base, "__init__.py")
    if os.path.isfile(base + ".py"):
        return base + ".py"
    return None


def windows_test(test):
    """True when the test is a Windows check; False when it is its negation; None otherwise."""
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        inner = windows_test(test.operand)
        return None if inner is None else not inner
    if isinstance(test, ast.Name):
        if test.id in WINDOWS_NAMES:
            return True
        if test.id == "TYPE_CHECKING":
            return True  # treated like a false branch
    if isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
        return True
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.comparators[0], ast.Constant):
        left = ast.unparse(test.left)
        value = test.comparators[0].value
        if left in ("sys.platform", "os.name", "_os.name") and isinstance(value, str):
            windows = value in ("win32", "nt", "cygwin")
            darwin = value == "darwin"
            if isinstance(test.ops[0], ast.Eq):
                return True if windows else (False if darwin else None)
            if isinstance(test.ops[0], ast.NotEq):
                return False if windows else (True if darwin else None)
    if isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute) and test.func.attr == "startswith":
        if ast.unparse(test.func.value) == "sys.platform" and test.args and isinstance(test.args[0], ast.Constant):
            if test.args[0].value in ("win", "win32", "cygwin"):
                return True
    return None


class Collector(ast.NodeVisitor):
    def __init__(self, package):
        self.package = package
        self.top, self.inner = [], []
        self.depth = 0

    def names(self, node):
        found = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                found += [".".join(parts[:i]) for i in range(1, len(parts) + 1)]
        else:
            if node.level:
                base = self.package.split(".") if self.package else []
                if node.level > 1:
                    base = base[:len(base) - (node.level - 1)]
                absolute = ".".join(base + ([node.module] if node.module else []))
            else:
                absolute = node.module or ""
            parts = absolute.split(".") if absolute else []
            found += [".".join(parts[:i]) for i in range(1, len(parts) + 1)]
            found += [absolute + "." + a.name if absolute else a.name for a in node.names if a.name != "*"]
        return found

    def visit_Import(self, node):
        (self.inner if self.depth else self.top).extend(self.names(node))

    visit_ImportFrom = visit_Import

    def visit_FunctionDef(self, node):
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef

    def visit_If(self, node):
        verdict = windows_test(node.test) if self.depth == 0 else None
        if verdict is True:
            for child in node.orelse:
                self.visit(child)
        elif verdict is False:
            for child in node.body:
                self.visit(child)
        else:
            self.generic_visit(node)


def analyse(path, name):
    with open(path, "rb") as stream:
        tree = ast.parse(stream.read(), filename=path)
    package = name if path.endswith("__init__.py") else name.rpartition(".")[0]
    collector = Collector(package)
    collector.visit(tree)
    return collector.top, collector.inner


def closure(root, entries):
    seen, stack, inner = {}, list(entries), {}
    while stack:
        name = stack.pop()
        if not name or name in seen:
            continue
        path = resolve(root, name)
        seen[name] = path
        if path is None:
            continue
        if "." in name:
            stack.append(name.rpartition(".")[0])
        try:
            top, nested = analyse(path, name)
        except SyntaxError:
            continue
        stack.extend(top)
        inner[name] = sorted(set(n for n in nested if resolve(root, n)))
    return {k: v for k, v in seen.items() if v}, inner


def main():
    root, pyc_report, outfile, *specs = sys.argv[1:]
    with open(pyc_report, encoding="utf-8") as stream:
        report = json.load(stream)
    missing = set(report["missing_opt0_files"])
    stale = {row["source"] for row in report["stale_opt0_files"]}
    out = {}
    for spec in specs:
        label, _, modules = spec.partition("=")
        reached, inner = closure(root, modules.split(","))
        rows = []
        for name, path in sorted(reached.items()):
            rel = os.path.relpath(path, root)
            frozen = name in FROZEN or name.startswith("__phello__")
            state = "frozen" if frozen else "missing" if rel in missing else "stale" if rel in stale else "cached"
            rows.append({"module": name, "file": rel, "state": state, "function_level_imports": inner.get(name, [])})
        out[label] = {"entries": modules.split(","), "reached": len(rows),
                      "not_cached_non_frozen": [r["module"] for r in rows if r["state"] in ("missing", "stale")],
                      "modules": rows}
    with open(outfile, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")
    for label, value in out.items():
        print(label, "module-level reached", value["reached"], "not cached:", value["not_cached_non_frozen"])


if __name__ == "__main__":
    main()
