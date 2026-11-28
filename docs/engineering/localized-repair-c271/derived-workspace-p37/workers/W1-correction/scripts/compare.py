"""Read-only: compare W1's changed files with their base bytes and list the added test IDs.

Usage: python3 -I -S -B compare.py <base root> <worktree root> <evidence directory>
The base root is a byte-identical copy of the declaration commit's tree (its digests are checked).
Writes CHANGES.diff and COMPARISON.json into the evidence directory; starts nothing.
"""
import ast
import difflib
import hashlib
import json
import sys
from pathlib import Path

FILES = {
    "tools/check_local.py": "4c55033d51bdd33700f6d8a847b3ed44e6b4f7f6489bf11b5f497279a5a4cb70",
    "prototypes/static_tray_v01/current_host_readback_v02.py": "d34ea2f98cf77188750b7819f0b5418d4811d0bfcd8612fdd71be58210f59071",
    "tests/test_local_checks.py": "ce58b59ef72364266ee2919c48f2f9c12eefc946e65afd79f07dc42ab8aad9d5",
    "tests/test_current_host_readback_provider_v02.py": "b51748b650b9465454dc2b62ce3a0da0de8f048f3a0998e146ce77dc58ffc7bb",
}
UNCHANGED = {
    "tests/test_current_host_readback_driver_v02.py": "de29bc205c528fcd58cafbe1da5b8ad79c96abb2ab77d0abad9aab72403bf464",
    "tests/test_current_host_readback_controls_v02.py": "3b8c91b7767c2db0ac3dd5c7dd48d035eb6dd602dc8c01e08bb0e49ac21bd618",
    "prototypes/static_tray_v01/current_host_readback_v01.py": "cb3f0c7f247331c79171a9e1ac71141d93205392ff426382046cfa61999d1126",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(source):
    """{Class.method: dump} for every function in every top-level class, and {name: dump} for top-level functions."""
    tree = ast.parse(source)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            found[node.name] = ("class", [ast.dump(base) for base in node.bases])
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[node.name + "." + item.name] = ("function", ast.dump(item, include_attributes=False))
                elif isinstance(item, ast.Assign):
                    found[node.name + "." + ast.unparse(item.targets[0])] = ("assign", ast.dump(item, include_attributes=False))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = ("function", ast.dump(node, include_attributes=False))
        elif isinstance(node, ast.Assign):
            found[ast.unparse(node.targets[0])] = ("assign", ast.dump(node, include_attributes=False))
    return found


def main():
    base, worktree, evidence = (Path(item) for item in sys.argv[1:4])
    report = {"base_digests_checked": {}, "current": {}, "unchanged_files": {}, "members": {}, "added_test_ids": []}
    diff = []
    for name, expected in FILES.items():
        before = base / name
        assert digest(before) == expected, name
        report["base_digests_checked"][name] = expected
        after = worktree / name
        report["current"][name] = {"sha256": digest(after), "bytes": after.stat().st_size}
        diff.extend(difflib.unified_diff(before.read_text().splitlines(True), after.read_text().splitlines(True),
                                         "a/" + name, "b/" + name))
        old, new = members(before.read_text()), members(after.read_text())
        report["members"][name] = {
            "removed": sorted(set(old) - set(new)),
            "changed": sorted(key for key in set(old) & set(new) if old[key] != new[key]),
            "added": sorted(set(new) - set(old))}
        if name.startswith("tests/"):
            module = Path(name).stem
            for key in sorted(set(new) - set(old)):
                parts = key.split(".")
                if len(parts) == 2 and parts[1].startswith("test_"):
                    report["added_test_ids"].append(module + "." + key)
    for name, expected in UNCHANGED.items():
        report["unchanged_files"][name] = digest(worktree / name) == expected
    (evidence / "CHANGES.diff").write_text("".join(diff))
    (evidence / "COMPARISON.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"current": report["current"], "members": report["members"],
                      "unchanged_files": report["unchanged_files"], "added": len(report["added_test_ids"])}, indent=1))


if __name__ == "__main__":
    main()
