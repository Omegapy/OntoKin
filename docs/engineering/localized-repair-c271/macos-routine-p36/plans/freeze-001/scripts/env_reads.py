"""W2 (freeze 001, C271-P36): the environment variable names that the routine's code reads, by reading.

Usage: python3 -I -S -B env_reads.py ROOT OUTPUT

An AST scan of every .py file under ROOT/tests, ROOT/tools, ROOT/ontokin, ROOT/prototypes and the documents
verifier. It records each read of a variable by name: os.environ.get/pop/setdefault(X), os.environ[X],
X in os.environ, os.getenv(X), and the same forms on any expression whose text ends with "environ"
(a copied mapping, for example). X is a string constant, or a module-level name bound to one. It also
records every file that copies the whole environment (dict(os.environ), os.environ.copy(), {**os.environ})
and every unresolved read (a computed name). It starts no process and writes only OUTPUT (absent).
"""
import ast
import json
import os
import sys

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
root, output = sys.argv[1], sys.argv[2]
if os.path.lexists(output):
    sys.stderr.write("refused: output exists\n")
    raise SystemExit(2)
trees = ["tests", "tools", "ontokin", "prototypes", "docs/maintenance/reorganization-2026-10-17"]


def text_of(node):
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def constants(module):
    names = {}
    for node in module.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names[target.id] = node.value.value
    return names


reads, copies, unresolved = {}, {}, []
files = 0
for tree in trees:
    base = os.path.join(root, tree)
    for directory, subdirs, names in os.walk(base):
        subdirs[:] = sorted(d for d in subdirs if d not in ("__pycache__", "node_modules", ".git"))
        for name in sorted(names):
            if not name.endswith(".py"):
                continue
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root)
            try:
                module = ast.parse(open(path, "rb").read())
            except SyntaxError:
                continue
            files += 1
            table = constants(module)

            def resolve(node):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    return node.value
                if isinstance(node, ast.Name) and node.id in table:
                    return table[node.id]
                if isinstance(node, ast.Attribute) and node.attr in table:
                    return table[node.attr]
                return None

            def note(name, node, form):
                reads.setdefault(name, []).append({"file": relative, "line": node.lineno, "form": form})

            for node in ast.walk(module):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Attribute) and func.attr in ("get", "pop", "setdefault") \
                            and text_of(func.value).endswith("environ") and node.args:
                        value = resolve(node.args[0])
                        if value is None:
                            unresolved.append({"file": relative, "line": node.lineno, "text": text_of(node)[:160]})
                        else:
                            note(value, node, "environ." + func.attr)
                    if text_of(func) in ("os.getenv", "getenv") and node.args:
                        value = resolve(node.args[0])
                        if value is None:
                            unresolved.append({"file": relative, "line": node.lineno, "text": text_of(node)[:160]})
                        else:
                            note(value, node, "os.getenv")
                    if text_of(func) in ("dict", "os.environ.copy") or (isinstance(func, ast.Attribute)
                                                                          and func.attr == "copy"
                                                                          and text_of(func.value).endswith("environ")):
                        if text_of(func) == "dict" and not (node.args and text_of(node.args[0]).endswith("environ")):
                            continue
                        copies.setdefault(relative, []).append(node.lineno)
                if isinstance(node, ast.Subscript) and text_of(node.value).endswith("environ"):
                    value = resolve(node.slice)
                    if value is None:
                        unresolved.append({"file": relative, "line": node.lineno, "text": text_of(node)[:160]})
                    else:
                        note(value, node, "environ[]" if isinstance(node.ctx, ast.Load) else "environ[] write")
                if isinstance(node, ast.Compare) and any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops) \
                        and any(text_of(c).endswith("environ") for c in node.comparators):
                    value = resolve(node.left)
                    if value is not None:
                        note(value, node, "in environ")
                if isinstance(node, ast.Dict) and any(key is None and text_of(value).endswith("environ")
                                                      for key, value in zip(node.keys, node.values)):
                    copies.setdefault(relative, []).append(node.lineno)

summary = {name: sorted({row["file"] for row in rows}) for name, rows in sorted(reads.items())}
document = {"schema": "ontokin.c271.p36-w2-freeze-env-reads/1", "root_label": "<worktree>", "trees": trees,
            "python_files": files, "names": summary, "reads": reads, "whole_environment_copies": copies,
            "unresolved_reads": unresolved}
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    stream.write(json.dumps(document, indent=1, sort_keys=True) + "\n")
print(json.dumps({"files": files, "names": len(summary), "copies": len(copies), "unresolved": len(unresolved)}))
