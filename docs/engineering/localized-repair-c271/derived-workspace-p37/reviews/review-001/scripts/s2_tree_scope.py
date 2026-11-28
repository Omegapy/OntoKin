"""W3 (C271-P37 S7): the copied set and the 0.2.0 source set at candidate C, from Git's files.

The driver's constants and its pure predicates (ignored, copied_source_path and the generated-example
rule of immutable_workspace_inputs) are taken from C's blob of tools/check_local.py by its syntax tree and
evaluated here; the observer's source-set constants likewise from C's current_host_observation_v02.py.
No project module is imported and nothing is started. Every path of C's tree is classified.

Usage: python3 -I -S -B s2_tree_scope.py GIT_COMMON_DIR SUMMARY_JSON OUTPUT
"""
import ast
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gitstore  # noqa: E402

C = "5a3502e22d0fa4b29fbff2c867f1aab8271c4235"
DRIVER = "tools/check_local.py"
OBSERVER = "prototypes/static_tray_v01/current_host_observation_v02.py"


def blob(store, flat, path):
    return store.read(flat[path][1])[1].decode("utf-8")


def driver_namespace(source):
    tree = ast.parse(source)
    namespace = {}
    wanted_constants = {"SOURCE_DIRS", "ROOT_FILES", "IGNORED", "GENERATED_EXAMPLES"}
    wanted_functions = {"ignored", "copied_source_path"}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in wanted_constants:
            namespace[node.targets[0].id] = eval(compile(ast.Expression(node.value), DRIVER, "eval"), {}, {})
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted_functions:
            module = ast.Module(body=[node], type_ignores=[])
            exec(compile(module, DRIVER, "exec"), namespace)
        if isinstance(node, ast.FunctionDef) and node.name == "immutable_workspace_inputs":
            inner = next(item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "generated")
            exec(compile(ast.Module(body=[inner], type_ignores=[]), DRIVER, "exec"), namespace)
    return namespace


def observer_constants(source):
    tree = ast.parse(source)
    namespace = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("SOURCE_TREES", "SOURCE_OPTIONAL", "SOURCE_FILES", "MACOS_LOCK", "EXTERNAL_INPUTS"):
                namespace[name] = eval(compile(ast.Expression(node.value), OBSERVER, "eval"), {}, dict(namespace))
    return namespace


def quoted_by_git(name):
    data = name.encode("utf-8", "surrogateescape")
    return any(byte < 0x20 or byte == 0x7F or byte >= 0x80 or byte in (0x22, 0x5C, 0x20) for byte in data)


def main(common, summary_path, output):
    store = gitstore.Store(os.path.join(common, "objects"))
    commit = store.commit(C)
    flat = store.flatten(commit["tree"])
    driver = driver_namespace(blob(store, flat, DRIVER))
    observer = observer_constants(blob(store, flat, OBSERVER))
    copied = driver["copied_source_path"]
    ignored = driver["ignored"]
    generated = driver["generated"]
    inside = {path for path in flat if copied(path)}
    outside = sorted(set(flat) - inside)
    result = {"schema": "w3.c271-p37.tree-scope/1", "commit": C, "tree": commit["tree"], "tracked_entries": len(flat),
              "constants": {key: sorted(driver[key]) if isinstance(driver[key], (set, frozenset)) else list(driver[key])
                            for key in ("SOURCE_DIRS", "ROOT_FILES", "IGNORED")},
              "outside_copied_set": [{"path": path, "mode": flat[path][0], "oid": flat[path][1]} for path in outside],
              "outside_count": len(outside)}
    result["inside_not_regular_files"] = sorted(p for p in inside if flat[p][0] not in ("100644", "100755"))
    result["with_an_ignored_component"] = sorted(p for p in flat if any(ignored(part) for part in p.split("/")))
    result["names_git_quotes_in_porcelain_v1"] = sorted(p for p in flat if quoted_by_git(p))
    result["names_with_a_line_break_python_splits"] = sorted(
        p for p in flat if len((p + "x").splitlines()) != 1)
    result["names_with_arrow"] = sorted(p for p in flat if " -> " in p)
    result["names_not_nfc"] = sorted(p for p in flat if unicodedata.normalize("NFC", p) != p)
    folded = {}
    for path in flat:
        folded.setdefault(path.casefold(), []).append(path)
    result["case_fold_collisions_among_tracked_paths"] = sorted(v for v in folded.values() if len(v) > 1)
    inside_folded = {p.casefold() for p in inside}
    result["outside_paths_folding_to_an_inside_path"] = sorted(p for p in outside if p.casefold() in inside_folded)
    roots = {p.split("/")[0] for p in flat}
    result["case_variants_of_copied_roots"] = sorted(
        r for r in roots if r not in driver["SOURCE_DIRS"] and r not in driver["ROOT_FILES"]
        and any(r.casefold() == s.casefold() for s in (*driver["SOURCE_DIRS"], *driver["ROOT_FILES"])))
    result["root_files_tracked"] = {name: (flat[name][0] if name in flat else None) for name in driver["ROOT_FILES"]}
    # Rule B's other conditions for each line the workspace's status would print at C.
    rows = []
    for path in outside:
        parts = path.split("/")
        rows.append({"line": " D " + path, "generated": generated(path),
                     "components_safe": all(part not in ("", ".", "..") for part in parts),
                     "not_quoted": not quoted_by_git(path), "no_arrow": " -> " not in path,
                     "copied_source_path": copied(path), "folds_to_a_copied_file": path.casefold() in inside_folded})
    result["rule_b_at_C"] = rows
    result["rule_b_admits_every_line_at_C"] = all(
        row["components_safe"] and row["not_quoted"] and row["no_arrow"] and not row["copied_source_path"]
        and not row["folds_to_a_copied_file"] for row in rows)
    # The 0.2.0 source set at C (the observer's source_paths, read from the tree).
    trees, optional, roles = observer["SOURCE_TREES"], observer["SOURCE_OPTIONAL"], observer["SOURCE_FILES"]
    source_set = set()
    for path, (mode, _) in flat.items():
        if any(path.startswith(tree + "/") for tree in trees):
            source_set.add(path)
    source_set.update(role for role in roles if role in flat)
    source_set.update(name for name in optional if name in flat)
    result["source_set"] = {"trees": list(trees), "roles": list(roles), "optional": list(optional),
                            "files": len(source_set),
                            "roles_missing_at_C": [r for r in roles if r not in flat],
                            "outside_copied_set": sorted(p for p in source_set if not copied(p)),
                            "not_regular_files": sorted(p for p in source_set if flat[p][0] not in ("100644", "100755")),
                            "bytecode_or_ds_store": sorted(p for p in source_set if p.endswith((".pyc", ".pyo"))
                                                           or "__pycache__" in p.split("/")
                                                           or p.split("/")[-1] == ".DS_Store")}
    regular_inside = sorted(p for p in inside if flat[p][0] in ("100644", "100755"))
    result["copied_files_expected"] = len(regular_inside)
    summary = json.load(open(summary_path))
    result["routine_source_inventory_file_count"] = summary["source_inventory"]["file_count"]
    result["copied_files_equal_routine_inventory_count"] = len(regular_inside) == summary["source_inventory"]["file_count"]
    result["generated_examples_tracked"] = sorted(p for p in flat if generated(p))
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:4])
