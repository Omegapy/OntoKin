"""W3 freeze review 001, script 09: module-level (import-time) code of the test modules that names .git or .venv.

Discovery (C12, C13) imports every test module of an export, which holds no .git pointer and no .venv. This lists,
for each tests/test*.py of the worktree at C, the string constants '.git', '.venv' and 'venv' (and Path parts) that
occur in code run at import: the module body and class bodies, outside function bodies. Reads only.
"""
import ast
import os
import sys

ROOT = sys.argv[1]
hits = []
for name in sorted(os.listdir(os.path.join(ROOT, "tests"))):
    if not (name.startswith("test") and name.endswith(".py")):
        continue
    path = os.path.join(ROOT, "tests", name)
    with open(path, "rb") as f:
        tree = ast.parse(f.read(), filename=path)

    def visit(node, at_import):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                # default values and decorators run at import; bodies do not
                for d in getattr(child, "decorator_list", []):
                    visit_expr(d)
                args = getattr(child, "args", None)
                if args is not None:
                    for d in list(args.defaults) + [x for x in args.kw_defaults if x is not None]:
                        visit_expr(d)
                continue
            if isinstance(child, ast.Constant) and isinstance(child.value, str) and child.value in (".git", ".venv", "venv", ".git/HEAD"):
                hits.append((name, child.lineno, child.value))
            visit(child, at_import)

    def visit_expr(expr):
        for sub in ast.walk(expr):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value in (".git", ".venv", "venv"):
                hits.append((name, sub.lineno, sub.value + " (default or decorator)"))
    visit(tree, True)
for h in hits:
    with open(os.path.join(ROOT, "tests", h[0]), "r", encoding="utf-8", errors="replace") as f:
        line = f.read().split("\n")[h[1] - 1]
    print("%s:%d %r  %s" % (h[0], h[1], h[2], line.strip()[:160]))
print("hits", len(hits))
