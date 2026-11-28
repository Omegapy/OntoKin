"""W3 (C271-P37 S7): the end state of the S6 routine's isolated workspace, read without Git.

The workspace's index is read from its file and compared with C's tree; each entry is compared with
its file as Git's status would (type, executable bit, stat data, then content); every file the index
does not hold is listed, outside .git; bytecode, __pycache__ and .DS_Store anywhere are listed. Content
is read only for entries whose stat data does not match. Nothing is written except OUTPUT.

Usage: python3 -I -S -B s3_workspace_end_state.py WORKSPACE GIT_COMMON_DIR OUTPUT
"""
import json
import os
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gitstore  # noqa: E402

C = "5a3502e22d0fa4b29fbff2c867f1aab8271c4235"


def main(workspace, common, output):
    store = gitstore.Store(os.path.join(common, "objects"))
    flat = store.flatten(store.commit(C)["tree"])
    index_path = os.path.join(workspace, ".git", "index")
    version, index = gitstore.read_index(index_path)
    index_mtime = os.stat(index_path).st_mtime_ns
    result = {"schema": "w3.c271-p37.workspace-end-state/1", "workspace": "<local>/c271-p37/routine/ordinary-001/workspace",
              "index": {"version": version, "entries": len(index),
                        "entries_equal_C_tree": {p: (oct(e["mode"])[2:], e["oid"]) for p, e in index.items()}
                        == {p: (m, o) for p, (m, o) in flat.items()},
                        "stages_other_than_zero": sorted(p for p, e in index.items() if e["stage"]),
                        "flags": sorted(p for p, e in index.items()
                                        if e["assume_valid"] or e["skip_worktree"] or e["intent_to_add"]),
                        "entries_without_stat_data": sorted(p for p, e in index.items()
                                                            if e["ctime"] == (0, 0) and e["mtime"] == (0, 0)
                                                            and e["size"] == 0 and e["ino"] == 0)}}
    lines, hashed = [], 0
    for path, entry in sorted(index.items()):
        local = os.path.join(workspace, path)
        try:
            info = os.lstat(local)
        except FileNotFoundError:
            lines.append(" D " + path)
            continue
        mode = entry["mode"]
        is_link = mode >> 12 == 0o12
        if stat.S_ISLNK(info.st_mode) != is_link or (not is_link and not stat.S_ISREG(info.st_mode)):
            lines.append(" T " + path)
            continue
        if not is_link and bool(info.st_mode & 0o100) != bool(mode & 0o100):
            lines.append(" M " + path + "  (mode)")
            continue
        seconds, nanoseconds = entry["mtime"]
        same = (seconds == int(info.st_mtime_ns // 10**9) & 0xFFFFFFFF and nanoseconds in (0, info.st_mtime_ns % 10**9)
                and entry["size"] == info.st_size & 0xFFFFFFFF and entry["ino"] == info.st_ino & 0xFFFFFFFF
                and info.st_mtime_ns < index_mtime)
        if same:
            continue
        hashed += 1
        data = os.readlink(local).encode() if is_link else open(local, "rb").read()
        if gitstore.blob_id(data) != entry["oid"]:
            lines.append(" M " + path)
    result["status_lines_computed"] = lines
    result["entries_hashed_after_stat_mismatch"] = hashed
    untracked, bytecode, ds_store = [], [], []
    for parent, dirnames, filenames in os.walk(workspace):
        relative = os.path.relpath(parent, workspace)
        relative = "" if relative == "." else relative + "/"
        if relative == "":
            dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in dirnames:
            if name == "__pycache__":
                bytecode.append(relative + name + "/")
        names = list(filenames) + [d for d in dirnames if os.path.islink(os.path.join(parent, d))]
        for name in names:
            path = relative + name
            if name.endswith((".pyc", ".pyo")):
                bytecode.append(path)
            if name == ".DS_Store":
                ds_store.append(path)
            if path not in index:
                untracked.append(path)
    result["files_not_in_index"] = sorted(untracked)
    result["bytecode"] = sorted(bytecode)
    result["ds_store"] = sorted(ds_store)
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:4])
