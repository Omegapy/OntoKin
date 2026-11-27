"""Check every file of HOST's source inventory against the worktree's bytes (read only).

Usage: python3 -I -S -B source_vs_inventory.py INVENTORY ROOT OUT.json
"""
import hashlib, json, os, stat, sys

inventory_path, root, destination = sys.argv[1:4]
inventory = json.load(open(inventory_path, "rb"))
bad = []
for relative, binding in inventory["files"].items():
    path = os.path.join(root, relative)
    info = os.lstat(path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    actual = {"sha256": digest, "size_bytes": info.st_size, "mode": oct(stat.S_IMODE(info.st_mode))}
    if actual != binding or info.st_nlink != 1 or not stat.S_ISREG(info.st_mode):
        bad.append({"path": relative, "actual": actual, "expected": binding, "nlink": info.st_nlink})
trees = sorted({relative.split("/")[0] + "/" + relative.split("/")[1] if relative.count("/") else relative
                for relative in inventory["files"]})
report = {"schema": inventory["schema"], "files": len(inventory["files"]), "bad": bad, "top_level_groups": trees[:40],
          "verdict": "EQUAL" if not bad else "DIFFERS"}
with open(destination, "x") as fh:
    json.dump(report, fh, indent=1)
    fh.write("\n")
print(json.dumps({k: v for k, v in report.items() if k != "top_level_groups"}, indent=1)[:1500])
print(report["top_level_groups"])
