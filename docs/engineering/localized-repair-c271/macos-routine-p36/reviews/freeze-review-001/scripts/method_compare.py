"""Compare named test methods' AST between two copies of a test file (read only).

Usage: python3 -I -S -B method_compare.py FILE_A FILE_B CLASS.METHOD [...]
"""
import ast, hashlib, sys


def bodies(path):
    tree = ast.parse(open(path, "rb").read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[node.name + "." + item.name] = hashlib.sha256(ast.dump(item, include_attributes=False).encode()).hexdigest()
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
    return out


a, b = bodies(sys.argv[1]), bodies(sys.argv[2])
for name in sys.argv[3:]:
    print(name, "equal" if a.get(name) == b.get(name) and a.get(name) else "DIFFERS", a.get(name, "absent")[:12], b.get(name, "absent")[:12])
changed = sorted(n for n in a.keys() & b.keys() if a[n] != b[n])
print("all changed functions:", changed)
print("only in A:", sorted(a.keys() - b.keys()))
print("only in B:", sorted(b.keys() - a.keys()))
