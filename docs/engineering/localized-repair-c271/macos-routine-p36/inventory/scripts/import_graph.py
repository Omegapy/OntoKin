"""W1 (C271-P36) static import graph. Reads source files only; imports nothing it scans.

Run only as: python3 -I -S -B import_graph.py WORKTREE OUTFILE

Module search roots model the unit process of `python -B -m unittest discover -s tests`, started in the
isolated workspace: sys.path[0] = <workspace>/tests (inserted by discovery), then <workspace> (from -m).
A module name resolves to the first of tests/<name>.py, <root>/<pkg path>.py, <root>/<pkg path>/__init__.py,
or a namespace directory. Every import statement anywhere in a file (module level or inside a function)
counts as a possible import. Relative imports resolve against the file's package.
Output: per entry file, the repository files in its static closure and the external top-level modules.
"""
from __future__ import annotations

import ast
import json
import os
import sys

WORKTREE = None


def module_file(name, roots):
    key = (name, tuple(roots))
    if key not in _RESOLVED:
        _RESOLVED[key] = _module_file(name, roots)
    return _RESOLVED[key]


def _module_file(name, roots):
    parts = name.split(".")
    # Regular modules and packages on any root win over namespace portions (PEP 420).
    for root in roots:
        base = os.path.join(root, *parts)
        if os.path.isfile(os.path.join(base, "__init__.py")):
            return os.path.join(base, "__init__.py")
        if os.path.isfile(base + ".py"):
            return base + ".py"
    for root in roots:
        base = os.path.join(root, *parts)
        if os.path.isdir(base):
            return base + os.sep  # namespace package directory
    return None


def package_of(path, roots):
    rel = None
    for root in roots:
        if path.startswith(root + os.sep):
            rel = os.path.relpath(path, root)
            break
    if rel is None:
        return None
    parts = rel[:-3].split(os.sep)
    if parts[-1] == "__init__":
        return ".".join(parts[:-1])
    return ".".join(parts[:-1])


_IMPORTS = {}
_RESOLVED = {}


def imports_of(path):
    if path in _IMPORTS:
        return _IMPORTS[path]
    _IMPORTS[path] = _imports_of(path)
    return _IMPORTS[path]


def _imports_of(path):
    with open(path, "rb") as stream:
        tree = ast.parse(stream.read(), filename=path)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((0, alias.name, None, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            found.append((node.level, node.module or "", [a.name for a in node.names], node.lineno))
    return found


def closure(entry, roots, stdlib_names):
    seen_files, external, edges, unresolved = set(), set(), [], set()
    stack = [entry]
    while stack:
        path = stack.pop()
        if path in seen_files or path.endswith(os.sep):
            continue
        seen_files.add(path)
        try:
            found = imports_of(path)
        except SyntaxError:
            continue
        for level, module, names, line in found:
            targets = []
            if level:
                package = package_of(path, roots) or ""
                base_parts = package.split(".") if package else []
                if level > 1:
                    base_parts = base_parts[:len(base_parts) - (level - 1)]
                absolute = ".".join(base_parts + ([module] if module else []))
            else:
                absolute = module
            if names is None:
                # import a.b.c imports a, a.b and a.b.c
                parts = absolute.split(".")
                targets = [".".join(parts[:i]) for i in range(1, len(parts) + 1)]
            else:
                parts = absolute.split(".") if absolute else []
                targets = [".".join(parts[:i]) for i in range(1, len(parts) + 1)]
                targets += [(absolute + "." + n) if absolute else n for n in names if n != "*"]
            for target in targets:
                if not target:
                    continue
                file = module_file(target, roots)
                if file is None:
                    top = target.split(".")[0]
                    if names is not None and target != absolute and module_file(absolute, roots):
                        continue  # attribute import from a repository module
                    if module_file(top, roots) is None:
                        external.add(top)
                    else:
                        unresolved.add(target)
                    continue
                edges.append((os.path.relpath(path, WORKTREE), line, target, os.path.relpath(file, WORKTREE)))
                if not file.endswith(os.sep):
                    stack.append(file)
                else:
                    init = os.path.join(file, "__init__.py")
                    if os.path.isfile(init):
                        stack.append(init)
    return seen_files, external, edges, unresolved


def main():
    global WORKTREE
    WORKTREE, outfile = sys.argv[1:3]
    tests = os.path.join(WORKTREE, "tests")
    roots = [tests, WORKTREE]
    stdlib_names = set(sys.stdlib_module_names)
    entries = sorted(os.path.join(tests, n) for n in os.listdir(tests)
                     if n.startswith("test") and n.endswith(".py") and os.path.isfile(os.path.join(tests, n)))
    step_entries = {
        "source": os.path.join(WORKTREE, "ontokin", "__main__.py"),
        "agent": os.path.join(WORKTREE, "tools", "run_agent_conformance.py"),
        "construction": os.path.join(WORKTREE, "tools", "verify_construction_ci.py"),
        "surface": os.path.join(WORKTREE, "tools", "run_surface_conformance.py"),
        "impulse": os.path.join(WORKTREE, "tools", "run_impulse_conformance.py"),
        "documents": os.path.join(WORKTREE, "docs", "maintenance", "reorganization-2026-10-17", "verify_reorganization.py"),
        "driver": os.path.join(WORKTREE, "tools", "check_local.py"),
    }
    out = {"roots_model": ["<workspace>/tests", "<workspace>"], "tests": {}, "steps": {}}
    for entry in entries:
        files, external, edges, unresolved = closure(entry, roots, stdlib_names)
        out["tests"][os.path.relpath(entry, WORKTREE)] = {
            "repo_files": sorted(os.path.relpath(f, WORKTREE) for f in files),
            "external": sorted(external),
            "external_nonstdlib": sorted(e for e in external if e not in stdlib_names),
            "unresolved": sorted(unresolved)}
    for step, entry in step_entries.items():
        script_dir = os.path.dirname(entry)
        step_roots = [script_dir, WORKTREE] if step not in {"source", "construction"} else [WORKTREE]
        files, external, edges, unresolved = closure(entry, step_roots, stdlib_names)
        out["steps"][step] = {"entry": os.path.relpath(entry, WORKTREE),
                              "repo_files": sorted(os.path.relpath(f, WORKTREE) for f in files),
                              "external": sorted(external),
                              "external_nonstdlib": sorted(e for e in external if e not in stdlib_names),
                              "unresolved": sorted(unresolved)}
    with open(outfile, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")
    allfiles = set()
    for v in out["tests"].values():
        allfiles.update(v["repo_files"])
    print(json.dumps({"tests": len(out["tests"]), "union_repo_files": len(allfiles),
                      "steps": {k: len(v["repo_files"]) for k, v in out["steps"].items()},
                      "external_nonstdlib_union": sorted({e for v in out["tests"].values() for e in v["external_nonstdlib"]})},
                     indent=1))


if __name__ == "__main__":
    main()
