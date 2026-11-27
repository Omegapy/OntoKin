"""W1 (C271-P36): list calls made by top-level statements of each test module (import-time code). Reads only.

Run only as: python3 -I -S -B module_level_calls.py WORKTREE OUTFILE
Calls inside def bodies are excluded; calls in class bodies (also import-time) are included.
"""
import ast, json, os, sys

def calls_in(node, out, inside_def=False):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            # decorators and defaults run at import time
            for d in getattr(child, 'decorator_list', []):
                calls_in(d, out)
            args = getattr(child, 'args', None)
            if args is not None:
                for default in list(args.defaults) + [d for d in args.kw_defaults if d is not None]:
                    calls_in(default, out)
            continue
        if isinstance(child, ast.Call):
            out.append((child.lineno, ast.unparse(child.func)[:80]))
        calls_in(child, out)

worktree, outfile = sys.argv[1:3]
tests = os.path.join(worktree, 'tests')
result = {}
for name in sorted(os.listdir(tests)):
    if not (name.endswith('.py') and os.path.isfile(os.path.join(tests, name))):
        continue
    with open(os.path.join(tests, name), 'rb') as stream:
        tree = ast.parse(stream.read())
    out = []
    calls_in(tree, out)
    result[name] = sorted(set(out))
with open(outfile, 'x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=1)
names = {}
for module, calls in result.items():
    for line, func in calls:
        names.setdefault(func, []).append(module)
for func in sorted(names):
    print('%-60s %3d %s' % (func, len(names[func]), names[func][:3]))
