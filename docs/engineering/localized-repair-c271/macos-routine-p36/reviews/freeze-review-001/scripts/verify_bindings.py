"""Independent read-only check of FREEZE-001.json's bindings, host facts, trees, ancestors and absent paths.

Usage: python3 -I -S -B verify_bindings.py FREEZE OUT.json
Reads files only; starts no process; writes only OUT.json (exclusive creation).
"""
import hashlib, json, os, stat, sys

freeze_path, destination = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import labeller
label = labeller(freeze_path)
freeze = json.load(open(freeze_path, "rb"))


def identity(path):
    info = os.lstat(path)
    row = {"exists": True, "is_link": stat.S_ISLNK(info.st_mode), "is_file": stat.S_ISREG(info.st_mode),
           "is_dir": stat.S_ISDIR(info.st_mode), "mode": oct(stat.S_IMODE(info.st_mode)), "nlink": info.st_nlink,
           "size_bytes": info.st_size, "device": info.st_dev, "inode": info.st_ino}
    if row["is_file"]:
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                digest.update(block)
        row["sha256"] = digest.hexdigest()
    return row


def safe(path):
    try:
        return identity(path)
    except FileNotFoundError:
        return {"exists": False}


results = {"bindings": [], "host_facts": [], "trees": [], "ancestors": [], "absent": {}, "evidence_listing": None}
bad = []
for row in freeze["bindings"]:
    actual = safe(row["path"])
    ok = (actual.get("exists") and actual.get("is_file") and not actual.get("is_link")
          and actual.get("sha256") == row["sha256"] and actual.get("size_bytes") == row["size_bytes"]
          and actual.get("mode") == row["mode"] and (not row.get("nlink_one") or actual.get("nlink") == 1))
    results["bindings"].append({"id": row["id"], "ok": bool(ok), "nlink": actual.get("nlink")})
    if not ok:
        bad.append(("binding", row["id"], actual))
for row in freeze["host_facts"]:
    actual = safe(row["path"])
    ok = (actual.get("is_file") and actual.get("sha256") == row["sha256"] and actual.get("size_bytes") == row["size_bytes"]
          and actual.get("mode") == row["mode"] and (not row.get("nlink_one") or actual.get("nlink") == 1))
    results["host_facts"].append({"id": row["id"], "ok": bool(ok)})
    if not ok:
        bad.append(("host_fact", row["id"], actual))
home = freeze["places"]["<home>"]
for name in (".config/git/config", ".config/git/attributes"):
    results["absent"][home + "/" + name] = not os.path.lexists(os.path.join(home, name))
for tree in freeze["trees"]:
    root = tree["root"]
    if not os.path.lexists(root):
        results["trees"].append({"root": root, "exists": False})
        continue
    found = []
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            if name == ".DS_Store" or (tree["bytecode"] and (name == "__pycache__" or name.endswith((".pyc", ".pyo")))):
                found.append(os.path.join(parent, name))
    results["trees"].append({"root": root, "exists": True, "bytecode_checked": tree["bytecode"],
                             "found": found[:20], "found_count": len(found)})
    if found:
        bad.append(("tree", root, found[:5]))
for row in freeze["evidence"]["ancestors"]:
    info = os.lstat(row["path"])
    ok = (info.st_dev == row["device"] and info.st_ino == row["inode"] and oct(stat.S_IMODE(info.st_mode)) == row["mode"]
          and not stat.S_ISLNK(info.st_mode))
    results["ancestors"].append({"path": row["path"], "ok": ok})
    if not ok:
        bad.append(("ancestor", row["path"], {"dev": info.st_dev, "ino": info.st_ino}))
absent = freeze["absent_paths"]["before_preparation"]
present = [path for path in absent if os.path.lexists(path)]
results["absent"]["before_preparation_count"] = len(absent)
results["absent"]["before_preparation_present"] = present
if present:
    bad.append(("absent", "present", present))
evidence = freeze["evidence"]["parent"]
results["evidence_listing"] = sorted(os.listdir(evidence))
tmp = freeze["places"]["<tmp:resolved>"]
results["devices_now"] = {"evidence": os.lstat(evidence).st_dev, "temporary_resolved": os.lstat(tmp).st_dev,
                          "temporary_default_is_link_path": os.path.realpath(freeze["places"]["<tmp:default>"]) + "/" == tmp}
results["umask_note"] = "not read here (a process attribute of the Director's shell)"
results["bad"] = bad
results["verdict"] = "MET" if not bad else "NOT_MET"
with open(destination, "x") as fh:
    fh.write(label(json.dumps(results, indent=1, default=str)))
    fh.write("\n")
print(label(json.dumps({"verdict": results["verdict"], "bindings": len(results["bindings"]),
                  "bindings_ok": sum(r["ok"] for r in results["bindings"]), "host_facts_ok": [r["ok"] for r in results["host_facts"]],
                  "trees": [(t["root"][-40:], t.get("exists"), t.get("found_count")) for t in results["trees"]],
                  "ancestors_ok": all(r["ok"] for r in results["ancestors"]), "absent": {k: v for k, v in results["absent"].items() if k != "before_preparation_present"},
                  "absent_present": present, "evidence": results["evidence_listing"], "devices_now": results["devices_now"], "bad": bad[:5]}, indent=1, default=str)))
