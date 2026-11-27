"""W3 plan review 001, s06: the modules that observe's loaded-module check will see, read statically.

observe_host runs check_loaded_modules after load_darwin_supervisor: every loaded module file must
be a file of the frozen framework inventory (with any existing bytecode inventoried too) or a file
of the source inventory without bytecode. This script imports no project code. It parses the
observer and the four supervisor files with ast, lists the imports that run before that check
(module level, and the observer's function-level imports on the path to it), locates each
standard-library module in the frozen framework inventory, and checks that no repository bytecode
exists for the project modules on that path.

python3 -I -S -B s06_imports_static.py --worktree W --inventory PYINV --source-inventory SRCINV
    [--label NAME=PATH ...] --output OUT
"""
import argparse
import ast
import os
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3_common as common  # noqa: E402
sys.path.pop(0)

FILES = {"__main__": "prototypes/static_tray_v01/current_host_observation_v02.py",
         "prototypes": "prototypes/__init__.py",
         "prototypes.static_tray_v01": "prototypes/static_tray_v01/__init__.py",
         "prototypes.static_tray_v01.supervisor": "prototypes/static_tray_v01/supervisor.py",
         "prototypes.static_tray_v01.supervisor_darwin_v01": "prototypes/static_tray_v01/supervisor_darwin_v01.py"}
OBSERVER_FUNCTIONS = ("_libsystem", "_plist_identity", "load_darwin_supervisor")


def imports(tree, functions=()):
    names = set()

    def visit(body, top):
        for node in body:
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module)
            elif isinstance(node, (ast.If, ast.Try)) and top:
                visit(node.body, top)
                visit(getattr(node, "orelse", []), top)
                for handler in getattr(node, "handlers", []):
                    visit(handler.body, top)
            elif isinstance(node, ast.FunctionDef) and node.name in functions:
                visit(node.body, False)
    visit(tree.body, True)
    return names


def main():
    common.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--source-inventory", required=True)
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    inventory = common.strict_loads(common.read_bytes(args.inventory)[0])
    source = common.strict_loads(common.read_bytes(args.source_inventory)[0])
    entries = inventory["framework"]["entries"]
    checks = common.Checks()
    found = {}
    for module, rel in FILES.items():
        tree = ast.parse(common.read_bytes(args.worktree + "/" + rel)[0].decode("utf-8"))
        found[module] = sorted(imports(tree, OBSERVER_FUNCTIONS if module == "__main__" else ()))
    top_names = sorted({name.split(".")[0] for names in found.values() for name in names} - {"prototypes"}
                       - {"__future__"})
    located = {}
    for name in top_names:
        candidates = ["lib/python3.12/" + name + ".py", "lib/python3.12/" + name + "/__init__.py",
                      "lib/python3.12/lib-dynload/" + name + ".cpython-312-darwin.so"]
        where = [rel for rel in candidates if entries.get(rel, {}).get("kind") == "file"]
        cached = None
        if where and where[0].endswith(".py"):
            directory, base = os.path.split(where[0])
            stem = base[:-3]
            cached = directory + "/__pycache__/" + stem + ".cpython-312.pyc"
            cached = {"path": cached, "inventoried": entries.get(cached, {}).get("kind") == "file",
                      "exists": os.path.lexists(inventory["framework"]["root"] + "/" + cached)}
        located[name] = {"framework_file": where[0] if where else None,
                         "builtin": name in sys.builtin_module_names, "bytecode": cached}
    unlocated = [name for name, row in located.items() if row["framework_file"] is None and not row["builtin"]]
    bytecode_unbound = [name for name, row in located.items() if row["bytecode"] and row["bytecode"]["exists"]
                        and not row["bytecode"]["inventoried"]]
    checks.add("I-01", not unlocated and not bytecode_unbound,
               "every standard-library module on the path to the check is a frozen framework file or built in, and "
               "any bytecode of it that exists is inventoried",
               {"modules": top_names, "unlocated": unlocated, "bytecode_unbound": bytecode_unbound})
    project = sorted({name for names in found.values() for name in names if name.startswith("prototypes")})
    checks.add("I-02", all(rel in source["files"] for rel in FILES.values())
               and set(project) <= set(FILES) - {"__main__"},
               "the only project modules on that path are the four supervisor files, all in the source inventory",
               {"project_imports": project})
    pycache = []
    stack = [args.worktree + "/prototypes"]
    while stack:
        directory = stack.pop()
        for name in os.listdir(directory):
            path = directory + "/" + name
            info = os.lstat(path)
            if name == "__pycache__" or name.endswith((".pyc", ".pyo")):
                pycache.append(path)
            if stat.S_ISDIR(info.st_mode):
                stack.append(path)
    checks.add("I-03", not pycache, "no bytecode file or __pycache__ directory exists anywhere under prototypes/",
               {"found": pycache})
    out = {"schema": "w3.p36.plan-review-001.s06/1", "pid": os.getpid(), "imports": found, "located": located,
           "checks": checks.rows, "summary": checks.summary(), "refused_process_events": list(common.REFUSED_EVENTS),
           "boot": common.sysctl_text("kern.bootsessionuuid")}
    digest = common.write_output(args.output, out, labels)
    print(labels(str({"summary": out["summary"], "modules": len(top_names), "output_sha256": digest})))


if __name__ == "__main__":
    main()
