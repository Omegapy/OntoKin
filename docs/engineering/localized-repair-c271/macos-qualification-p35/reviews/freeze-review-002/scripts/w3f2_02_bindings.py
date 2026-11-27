"""Freeze review 002, script 02: all 122 bindings recomputed, and compared with freeze 001's 120.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_02_bindings.py OUTPUT.json
Reads only; starts no process; writes OUTPUT.json only.
"""
import hashlib
import json
import os
import stat
import sys

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)

P35 = "<local>/c271-p35"
F1 = P35 + "/workers/W2-freeze-001/FREEZE-001.json"
F2 = P35 + "/workers/W2-freeze-002/FREEZE-002.json"
R1 = P35 + "/workers/W3-freeze-001"


def sha256(path):
    h = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        while True:
            b = os.read(fd, 1 << 20)
            if not b:
                break
            h.update(b)
    finally:
        os.close(fd)
    return h.hexdigest()


def components_on_disk(path):
    bad, current = [], "/"
    for part in [p for p in path.split("/") if p]:
        try:
            listing = os.listdir(current)
        except OSError as exc:
            bad.append([current, "unlistable: " + str(exc)])
            break
        if part not in listing:
            bad.append([current, part])
            break
        current = os.path.join(current, part)
    return bad


def check(row):
    path = row["path"]
    out = {"id": row["id"], "path": path}
    info = os.lstat(path)
    out["kind"] = "file" if stat.S_ISREG(info.st_mode) else ("symlink" if stat.S_ISLNK(info.st_mode) else "other")
    out["sha256"] = sha256(path) if out["kind"] == "file" else None
    out["size_bytes"] = info.st_size
    out["mode"] = "0o%03o" % stat.S_IMODE(info.st_mode)
    out["nlink"] = info.st_nlink
    out["canonical"] = os.path.realpath(path) == path and os.path.normpath(path) == path
    out["components_not_on_disk"] = components_on_disk(path)
    problems = []
    for key in ("kind", "sha256", "size_bytes", "mode"):
        if out[key] != row[key]:
            problems.append(key)
    if row.get("nlink_one") is not True or out["nlink"] != 1:
        problems.append("nlink")
    if not out["canonical"]:
        problems.append("canonical")
    if out["components_not_on_disk"]:
        problems.append("spelling")
    out["problems"] = problems
    return out


def main():
    with open(F1, "rb") as s:
        f1 = json.loads(s.read())
    with open(F2, "rb") as s:
        f2 = json.loads(s.read())
    b1, b2 = f1["bindings"], f2["bindings"]
    ids2 = [r["id"] for r in b2]
    paths2 = [r["path"] for r in b2]
    result = {"script": "w3f2_02_bindings.py", "count_001": len(b1), "count_002": len(b2),
              "duplicate_ids": sorted({i for i in ids2 if ids2.count(i) > 1}),
              "duplicate_paths": sorted({p for p in paths2 if paths2.count(p) > 1})}
    # The 120 of freeze 001 kept unchanged, in order, as the first 120 of freeze 002.
    by_id_1 = {r["id"]: r for r in b1}
    kept = [r for r in b2 if r["id"] in by_id_1]
    result["kept_count"] = len(kept)
    result["kept_identical_in_order"] = b2[:len(b1)] == b1
    result["kept_identical_by_id"] = all(by_id_1[r["id"]] == r for r in kept)
    result["removed"] = sorted(set(by_id_1) - set(ids2))
    result["added"] = [r for r in b2 if r["id"] not in by_id_1]
    # Every binding recomputed.
    rows = [check(r) for r in b2]
    result["rows"] = rows
    result["failed"] = [r for r in rows if r["problems"]]
    # The inputs the MC11 list's binding depends on: the probe, the dependencies inventory, the reader tree.
    def pick(prefix):
        return [{"id": r["id"], "sha256": r["sha256"], "size_bytes": r["size_bytes"]} for r in b2 if r["id"].startswith(prefix)]
    result["mc11_dependencies"] = {
        "probe": pick("source:prototypes/static_tray_v01/current_host_readback_v02.mjs"),
        "dependencies_inventory": pick("plan001:dependencies-inventory-001.json"),
        "reader_tree_count": len(pick("reader:")),
        "reader_tree_unchanged_from_001": [r for r in b2 if r["id"].startswith("reader:")] ==
                                           [r for r in b1 if r["id"].startswith("reader:")]}
    # The dependencies inventory's file list against the reader bindings.
    dep = next(r for r in b2 if r["id"] == "plan001:dependencies-inventory-001.json")
    with open(dep["path"], "rb") as s:
        inv = json.loads(s.read())
    result["dependencies_inventory_keys"] = sorted(inv)
    files = inv.get("files") or {}
    root = None
    for r in b2:
        if r["id"].startswith("reader:"):
            root = r["path"][: -len(r["id"][len("reader:"):])].rstrip("/")
            break
    mism = []
    for r in b2:
        if r["id"].startswith("reader:"):
            rel = r["id"][len("reader:"):]
            want = files.get(rel)
            if not isinstance(want, dict) or want.get("sha256", "").replace("sha256:", "") != r["sha256"] \
                    or want.get("size_bytes", want.get("size")) != r["size_bytes"]:
                mism.append({"rel": rel, "inventory": want, "binding": {"sha256": r["sha256"], "size": r["size_bytes"]}})
    result["reader_root"] = root
    result["reader_inventory_files"] = len(files) if isinstance(files, dict) else None
    result["reader_vs_inventory_mismatch"] = mism
    # The reviewed list's own record of what it was made against.
    with open(R1 + "/MC11-REVIEWED-LIST-001.json", "rb") as s:
        listed = json.loads(s.read())
    result["mc11_list"] = {"schema": listed.get("schema"), "status": listed.get("status"),
                           "top_keys": sorted(listed), "entries": len(listed.get("entries") or listed.get("files") or {})}
    with open(sys.argv[1], "x") as s:
        json.dump(result, s, indent=1, sort_keys=True)
        s.write("\n")
    print(json.dumps({"count": len(rows), "failed": len(result["failed"]), "kept_identical_in_order": result["kept_identical_in_order"],
                      "added": [r["id"] for r in result["added"]], "removed": result["removed"],
                      "dup_ids": result["duplicate_ids"], "dup_paths": result["duplicate_paths"],
                      "reader_mismatch": len(mism), "reader_inventory_files": result["reader_inventory_files"]}, sort_keys=True))


main()
