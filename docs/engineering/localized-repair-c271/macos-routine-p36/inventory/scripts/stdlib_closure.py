"""W1 (C271-P36) static standard-library import closure. Reads source files only; imports nothing it scans.

Run only as: python3 -I -S -B stdlib_closure.py STDLIB_ROOT PYC_REPORT OUTFILE LABEL=MODULE[,MODULE...] ...

For each label, it walks every import statement (module level and inside functions, so an
over-approximation) of the named modules and of every standard-library module they reach, resolving
names to files under STDLIB_ROOT (site-packages excluded). Frozen modules of CPython 3.12 are marked, since
they are never loaded from source or cached bytecode at the default -X frozen_modules=on. The result
lists, per label, the reached files and those whose opt-level '' cached bytecode the PYC_REPORT (from
pyc_presence.py) records as missing or stale.
"""
from __future__ import annotations

import ast
import json
import os
import sys

FROZEN = {"zipimport", "abc", "codecs", "io", "_collections_abc", "_sitebuiltins", "genericpath", "ntpath",
          "posixpath", "os", "site", "stat", "importlib.util", "importlib.machinery", "runpy", "__hello__",
          "__phello__", "importlib._bootstrap", "importlib._bootstrap_external"}


def resolve(root, name):
    parts = name.split(".")
    base = os.path.join(root, *parts)
    if os.path.isfile(os.path.join(base, "__init__.py")):
        return os.path.join(base, "__init__.py")
    if os.path.isfile(base + ".py"):
        return base + ".py"
    return None


def module_name(root, path):
    rel = os.path.relpath(path, root)[:-3].split(os.sep)
    if rel[-1] == "__init__":
        rel = rel[:-1]
    return ".".join(rel)


def imports(path, name):
    with open(path, "rb") as stream:
        tree = ast.parse(stream.read(), filename=path)
    package = name if path.endswith("__init__.py") else name.rpartition(".")[0]
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                found += [".".join(parts[:i]) for i in range(1, len(parts) + 1)]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".") if package else []
                if node.level > 1:
                    base = base[:len(base) - (node.level - 1)]
                absolute = ".".join(base + ([node.module] if node.module else []))
            else:
                absolute = node.module or ""
            parts = absolute.split(".") if absolute else []
            found += [".".join(parts[:i]) for i in range(1, len(parts) + 1)]
            found += [absolute + "." + a.name if absolute else a.name for a in node.names if a.name != "*"]
    return found


def closure(root, entries):
    seen, stack, unresolved = {}, list(entries), set()
    while stack:
        name = stack.pop()
        if name in seen or not name:
            continue
        path = resolve(root, name)
        if path is None:
            unresolved.add(name)
            seen[name] = None
            continue
        seen[name] = path
        # Importing a.b imports a first.
        if "." in name:
            stack.append(name.rpartition(".")[0])
        try:
            stack.extend(imports(path, name))
        except SyntaxError:
            pass
    return {k: v for k, v in seen.items() if v}, unresolved


def main():
    root, pyc_report, outfile, *specs = sys.argv[1:]
    with open(pyc_report, encoding="utf-8") as stream:
        report = json.load(stream)
    missing = set(report["missing_opt0_files"])
    stale = {row["source"] for row in report["stale_opt0_files"]}
    out = {}
    for spec in specs:
        label, _, modules = spec.partition("=")
        reached, unresolved = closure(root, modules.split(","))
        rows = []
        for name, path in sorted(reached.items()):
            rel = os.path.relpath(path, root)
            frozen = name in FROZEN or name.startswith("__phello__")
            state = "frozen" if frozen else "missing" if rel in missing else "stale" if rel in stale else "cached"
            rows.append({"module": name, "file": rel, "state": state})
        out[label] = {"entries": modules.split(","), "reached": len(rows),
                      "not_cached_non_frozen": [r for r in rows if r["state"] in ("missing", "stale")],
                      "unresolved_names_sample": sorted(unresolved)[:400], "modules": rows}
    with open(outfile, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")
    for label, value in out.items():
        print(label, "reached", value["reached"], "not cached:", [r["module"] for r in value["not_cached_non_frozen"]])


if __name__ == "__main__":
    main()
