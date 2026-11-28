"""W3 (C271-P37 S7): C's default inventory additions (MC28) and the test modules' members, without running a test.

1. From Git's files: every class and method of the two changed test modules at the declaration commit and
   at C, compared by their syntax trees; the new module's methods at C.
2. The discovery at C against MH's baseline discovery, MI's additions and the cumulative additions record:
   exact sets, order of the record, and the record's own counts.
Writes one JSON file with labels in place of machine paths.

Usage: python3 -I -S -B s5_inventory.py GIT_COMMON_DIR LOCAL WORKTREE OUTPUT
"""
import ast
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gitstore  # noqa: E402

C = "5a3502e22d0fa4b29fbff2c867f1aab8271c4235"
PARENT = "2f728998456c829f3cdc13bbf72d6dd805fefa36"
CHANGED = ("tests/test_local_checks.py", "tests/test_current_host_readback_provider_v02.py")
NEW = "tests/test_current_host_readback_derived_controls_v02.py"
BASELINE = "c271-p35/evidence/s7-001-discovery-baseline.json"
BASELINE_SHA256 = "8d53b1c942c79676f0e0c23fe28f343f855e59ccc706e255ee605623ca8ce4c7"
MI_ADDITIONS = "docs/engineering/localized-repair-c271/macos-implementation-p33/INVENTORY-ADDITIONS.json"
MI_ADDITIONS_SHA256 = "f710dbb55483ca428e641e81c523ee556d422660a2594675be0d790fa3a4c9da"
DISCOVERY = "c271-p37/routine/discovery-c.json"
DISCOVERY_SHA256 = "51ca04483cd60fea967575d9f8c5164b4b713282cafcbcfe59df9fcbd12fd08b"
ADDITIONS = "c271-p37/routine/INVENTORY-ADDITIONS.json"
ADDITIONS_SHA256 = "7eccdc027ab1a52cb4ed3fa5b5b5589aba22670448e5d1f41d35ea5220a45682"
FROZEN = "docs/engineering/localized-repair-c271/derived-workspace-p37/CONTROLS-FROZEN.json"
NOTE = "docs/engineering/localized-repair-c271/derived-workspace-p37/interfaces/W1-CORRECTION.md"


def members(source):
    """{"Class": dump, "Class.method": dump, "<module>.name": dump} for top-level classes, their functions and functions."""
    tree = ast.parse(source)
    rows = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            rows[node.name] = ast.dump(ast.ClassDef(name=node.name, bases=node.bases, keywords=node.keywords, body=[],
                                                    decorator_list=node.decorator_list, type_params=[]))
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    rows[node.name + "." + item.name] = ast.dump(item)
                elif isinstance(item, ast.Assign):
                    rows[node.name + ".=" + ",".join(ast.dump(t) for t in item.targets)] = ast.dump(item.value)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            rows["<module>." + node.name] = ast.dump(node)
        elif isinstance(node, ast.Assign):
            rows["<module>.=" + ",".join(ast.dump(t) for t in node.targets)] = ast.dump(node.value)
    return rows


def test_ids(module_name, source):
    tree = ast.parse(source)
    ids = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test"):
                    ids.append(module_name + "." + node.name + "." + item.name)
    return ids


def bound(path, expected):
    raw = open(path, "rb").read()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise SystemExit("input differs from its recorded digest: " + os.path.basename(path))
    return json.loads(raw)


def main(common, local, worktree, output):
    store = gitstore.Store(os.path.join(common, "objects"))
    at_c = store.flatten(store.commit(C)["tree"])
    at_parent = store.flatten(store.commit(PARENT)["tree"])
    out = {"schema": "w3.c271-p37.inventory/1", "modules": {}}
    added_by_ast = []
    for path in CHANGED:
        before = members(store.read(at_parent[path][1])[1].decode("utf-8"))
        after = members(store.read(at_c[path][1])[1].decode("utf-8"))
        module = os.path.basename(path)[:-3]
        new_tests = sorted(set(test_ids(module, store.read(at_c[path][1])[1].decode()))
                           - set(test_ids(module, store.read(at_parent[path][1])[1].decode())))
        added_by_ast += new_tests
        out["modules"][path] = {
            "members_before": len(before), "members_after": len(after),
            "removed_members": sorted(set(before) - set(after)),
            "changed_members": sorted(name for name in set(before) & set(after) if before[name] != after[name]),
            "added_members": sorted(set(after) - set(before)),
            "tests_before": len(test_ids(module, store.read(at_parent[path][1])[1].decode())),
            "tests_after": len(test_ids(module, store.read(at_c[path][1])[1].decode())),
            "added_test_ids": new_tests}
    new_source = store.read(at_c[NEW][1])[1].decode("utf-8")
    new_ids = test_ids(os.path.basename(NEW)[:-3], new_source)
    out["modules"][NEW] = {"in_parent": NEW in at_parent, "tests": len(new_ids)}
    frozen = json.load(open(os.path.join(worktree, FROZEN)))
    out["frozen_ids_equal_module_methods"] = sorted(frozen["test_module"]["default_discovery_ids"]) == sorted(new_ids)
    out["frozen_controls_equal_methods"] = sorted("test_current_host_readback_derived_controls_v02." + c["method"]
                                                  for c in frozen["controls"]) == sorted(new_ids)
    note = open(os.path.join(worktree, NOTE), encoding="utf-8").read()
    note_ids = re.findall(r"^- `(test_[a-z0-9_]+\.[A-Za-z]+\.test_[A-Za-z0-9_]+)`", note, re.M)
    out["note_ids"] = len(note_ids)
    out["note_ids_equal_ast_additions"] = sorted(note_ids) == sorted(added_by_ast)
    p37 = sorted(added_by_ast + new_ids)
    out["p37_additions"] = len(p37)

    baseline = bound(os.path.join(local, BASELINE), BASELINE_SHA256)
    mi = bound(os.path.join(worktree, MI_ADDITIONS), MI_ADDITIONS_SHA256)
    discovery = bound(os.path.join(local, DISCOVERY), DISCOVERY_SHA256)
    record = bound(os.path.join(local, ADDITIONS), ADDITIONS_SHA256)
    base_ids = baseline["ids_in_discovery_order"]
    ids = discovery["ids_in_discovery_order"]
    out["discovery"] = {"state": discovery["state"], "count": len(ids), "unique": len(set(ids)),
                        "failed_imports": discovery["failed_imports"], "loader_errors": discovery["loader_errors"],
                        "bytecode_present": discovery["bytecode_present"], "process_events": discovery["process_events"],
                        "baseline_count": len(base_ids), "baseline_unique": len(set(base_ids)),
                        "mi_added": len(mi["added"]), "mi_removed": len(mi["removed"])}
    expected = set(base_ids) | set(mi["added"]) | set(p37)
    out["discovery"]["equals_baseline_plus_mi_plus_p37"] = set(ids) == expected
    out["discovery"]["missing"] = sorted(expected - set(ids))
    out["discovery"]["extra"] = sorted(set(ids) - expected)
    out["discovery"]["overlaps"] = {"mi_in_baseline": sorted(set(mi["added"]) & set(base_ids)),
                                    "p37_in_baseline_or_mi": sorted(set(p37) & (set(base_ids) | set(mi["added"])))}
    out["record"] = {"base_count": record["base_count"], "candidate_count": record["candidate_count"],
                     "added_count": record["added_count"], "removed": record["removed"],
                     "added_is_mi_then_p37": record["added"][:len(mi["added"])] == mi["added"]
                     and sorted(record["added"][len(mi["added"]):]) == p37,
                     "p37_in_discovery_order": record["added"][len(mi["added"]):] == [i for i in ids if i in set(p37)],
                     "counts_consistent": record["candidate_count"] == len(ids)
                     and record["base_count"] == len(base_ids) and record["added_count"] == len(record["added"]),
                     "added_by_module": record["added_by_module"]}
    by_module = {}
    for item in record["added"]:
        by_module[item.split(".")[0]] = by_module.get(item.split(".")[0], 0) + 1
    out["record"]["added_by_module_recomputed_equal"] = by_module == record["added_by_module"]
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:5])
