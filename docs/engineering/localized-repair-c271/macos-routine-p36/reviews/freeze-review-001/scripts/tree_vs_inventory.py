"""Compare the live framework and .venv trees with HOST's frozen Python inventory (read only; my own walk).

Usage: python3 -I -S -B tree_vs_inventory.py INVENTORY OUT.json
Entries: kind file (sha256, size, mode), directory (mode), symlink (target); links are not followed.
"""
import hashlib, json, os, stat, sys

inventory_path, destination = sys.argv[1:3]
frozen = json.load(open(inventory_path, "rb"))


def walk(root):
    entries = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            full = os.path.join(parent, name)
            relative = os.path.relpath(full, root)
            info = os.lstat(full)
            if stat.S_ISLNK(info.st_mode):
                entries[relative] = {"kind": "symlink", "target": os.readlink(full)}
            elif stat.S_ISDIR(info.st_mode):
                entries[relative] = {"kind": "directory", "mode": oct(stat.S_IMODE(info.st_mode))}
            elif stat.S_ISREG(info.st_mode):
                digest = hashlib.sha256()
                with open(full, "rb") as fh:
                    for block in iter(lambda: fh.read(1 << 20), b""):
                        digest.update(block)
                entries[relative] = {"kind": "file", "mode": oct(stat.S_IMODE(info.st_mode)),
                                     "sha256": digest.hexdigest(), "size_bytes": info.st_size}
            else:
                entries[relative] = {"kind": "special"}
    return entries


report = {}
for tree in ("framework", "venv"):
    root = frozen[tree]["root"]
    expected = frozen[tree]["entries"]
    actual = walk(root)
    added = sorted(set(actual) - set(expected))
    missing = sorted(set(expected) - set(actual))
    changed = []
    for name in sorted(set(actual) & set(expected)):
        a, e = actual[name], expected[name]
        keys = [k for k in a if k in e]
        if a.get("kind") != e.get("kind") or any(a[k] != e[k] for k in keys):
            changed.append(name)
    report[tree] = {"root_label": "<framework>" if tree == "framework" else "<worktree>/.venv", "expected": len(expected),
                    "actual": len(actual), "added": added[:50], "added_count": len(added), "missing": missing[:50],
                    "missing_count": len(missing), "changed": changed[:50], "changed_count": len(changed),
                    "pyc_actual": sum(1 for n in actual if n.endswith(".pyc"))}
report["verdict"] = "EQUAL" if all(report[t]["added_count"] == report[t]["missing_count"] == report[t]["changed_count"] == 0
                                   for t in ("framework", "venv")) else "DIFFERS"
with open(destination, "x") as fh:
    json.dump(report, fh, indent=1)
    fh.write("\n")
print(json.dumps(report, indent=1))
