"""HOST review 001, script 03: the source binding, read from files without any Git process.

It recomputes the source inventory of W3-OBSERVER section 2 (the observer's four trees, sixteen
roles and three optional files, taken from its AST), compares its canonical bytes with the frozen
inventory, reads HEAD from the worktree's Git files exactly as HOST records it, inflates commit
B's loose object and checks its name and tree, and parses the worktree's index: its trailing
checksum, the cached root tree of its TREE extension, and the blob identity and mode of every
source-inventory file against its index entry.
Usage: python3 -I -S -B w3h_03_source.py --host H --plan P --out OUT [--label PATH=LABEL ...]
"""
import argparse
import hashlib
import os
import posixpath
import re
import stat
import struct
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()


def source_inventory(root, K):
    found, problems = set(), []
    for tree in K["SOURCE_TREES"]:
        base = root + "/" + tree
        stack = [""]
        while stack:
            rel = stack.pop()
            directory = base + "/" + rel if rel else base
            for name in sorted(os.listdir(directory)):
                r = rel + "/" + name if rel else name
                path = base + "/" + r
                info = os.lstat(path)
                if name in (".DS_Store", "__pycache__") or not name.isprintable():
                    problems.append("refused name: " + tree + "/" + r)
                if stat.S_ISLNK(info.st_mode):
                    problems.append("link: " + tree + "/" + r)
                elif stat.S_ISDIR(info.st_mode):
                    stack.append(r)
                elif stat.S_ISREG(info.st_mode):
                    if r.endswith((".pyc", ".pyo")):
                        problems.append("bytecode: " + tree + "/" + r)
                    found.add(tree + "/" + r)
                else:
                    problems.append("special: " + tree + "/" + r)
    for rel in K["SOURCE_FILES"]:
        path = root + "/" + rel
        if C.has_linked_component(path) is not None or not os.path.isfile(path) or os.path.islink(path):
            problems.append("role missing or linked: " + rel)
        found.add(rel)
    for rel in K["SOURCE_OPTIONAL"]:
        if os.path.lexists(root + "/" + rel):
            found.add(rel)
    files, nlinks = {}, []
    for rel in sorted(found):
        _, facts, _ = C.read_bytes(root + "/" + rel, keep=False)
        files[rel] = C.binding(facts)
        if facts["nlink"] != 1:
            nlinks.append(rel)
    return {"schema": K["SOURCE_SCHEMA"], "files": files}, problems, nlinks


def git_head(root):
    files = {}

    def read(path):
        raw, facts, _ = C.read_bytes(path)
        files[path] = C.binding(facts)
        return raw
    dotgit = root + "/.git"
    text = read(dotgit).decode("utf-8").strip()
    gitdir = text[len("gitdir: "):] if text.startswith("gitdir: ") else None
    if gitdir and not gitdir.startswith("/"):
        gitdir = posixpath.normpath(root + "/" + gitdir)
    common = gitdir
    if os.path.lexists(gitdir + "/commondir"):
        rel = read(gitdir + "/commondir").decode("utf-8").strip()
        common = rel if rel.startswith("/") else posixpath.normpath(gitdir + "/" + rel)
    head = read(gitdir + "/HEAD").decode("ascii").strip()
    ref, commit = None, None
    if head.startswith("ref: "):
        ref = head[5:]
        for base in (gitdir, common):
            if os.path.lexists(base + "/" + ref):
                commit = read(base + "/" + ref).decode("ascii").strip()
                break
    else:
        commit = head
    return {"gitdir": gitdir, "common_dir": common, "ref": ref, "commit": commit,
            "files": {p: files[p] for p in sorted(files)}}


def loose_object(common, name):
    path = common + "/objects/" + name[:2] + "/" + name[2:]
    if not os.path.lexists(path):
        return None
    raw = zlib.decompress(C.read_bytes(path)[0])
    return raw


def parse_index(raw):
    sig, version, count = struct.unpack_from(">4sII", raw, 0)
    if sig != b"DIRC" or version not in (2, 3):
        raise ValueError("unsupported index")
    offset, entries = 12, {}
    stages = 0
    for _ in range(count):
        start = offset
        mode = struct.unpack_from(">I", raw, start + 24)[0]
        sha = raw[start + 40:start + 60].hex()
        flags = struct.unpack_from(">H", raw, start + 60)[0]
        stage = (flags >> 12) & 3
        extended = flags & 0x4000
        offset = start + 62
        if extended and version == 3:
            offset += 2
        end = raw.index(b"\0", offset)
        path = raw[offset:end].decode("utf-8")
        entry_len = end - start + 1
        offset = start + ((entry_len + 7) // 8) * 8 if version in (2, 3) else end + 1
        if stage:
            stages += 1
        entries[path] = {"mode": "%o" % mode, "sha1": sha, "stage": stage}
    body_end = len(raw) - 20
    extensions, tree_root = {}, None
    while offset < body_end:
        ext, size = struct.unpack_from(">4sI", raw, offset)
        data = raw[offset + 8:offset + 8 + size]
        extensions[ext.decode("ascii", "replace")] = size
        if ext == b"TREE":
            nul = data.index(b"\0")
            path = data[:nul]
            line_end = data.index(b"\n", nul)
            entry_count, subtrees = data[nul + 1:line_end].decode("ascii").split(" ")
            tree_root = {"path": path.decode("utf-8"), "entry_count": int(entry_count), "subtrees": int(subtrees),
                         "sha1": data[line_end + 1:line_end + 21].hex() if int(entry_count) >= 0 else None}
        offset += 8 + size
    checksum_ok = hashlib.sha1(raw[:body_end]).digest() == raw[body_end:]
    return {"version": version, "count": count, "entries": entries, "stages": stages, "extensions": extensions,
            "tree_root": tree_root, "checksum_ok": checksum_ok}


def blob_id(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for name in ("--host", "--plan", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--label", action="append", default=[])
    ap.add_argument("--tag", default="run1")
    args = ap.parse_args()
    lab = C.Labeler([tuple(item.split("=", 1)) for item in args.label])
    ck = C.Checks()
    started = time.time()
    host = C.strict_loads(C.read_bytes(args.host)[0])
    plan = C.strict_loads(C.read_bytes(args.plan)[0])
    root = plan["source"]["root"]
    obs_raw = C.read_bytes(plan["observer"]["path"])[0]
    K = C.observer_constants(obs_raw.decode("utf-8"))
    ck.add("S00", all(k in K for k in ("SOURCE_TREES", "SOURCE_FILES", "SOURCE_OPTIONAL", "SOURCE_SCHEMA")),
           "the observer's source-set constants evaluate from its AST", trees=list(K.get("SOURCE_TREES", ())),
           roles=len(K.get("SOURCE_FILES", ())), optional=list(K.get("SOURCE_OPTIONAL", ())))
    doc, problems, nlinks = source_inventory(root, K)
    mine = C.canonical(doc)
    frozen_raw, frozen_facts, _ = C.read_bytes(plan["source"]["inventory"]["path"])
    ck.add("S01", mine == frozen_raw and frozen_facts["sha256"] == plan["source"]["inventory"]["sha256"] ==
           "95abd300edbb9930e67c569b726015964ab98f4ed0ede389da122bbb3f145c4c",
           "my recomputed source inventory is byte-identical to the frozen one that the plan and HOST bind",
           recomputed_sha256=C.sha256(mine), files=len(doc["files"]),
           file_bytes=sum(b["size_bytes"] for b in doc["files"].values()))
    ck.add("S02", not problems and not nlinks, "no link, .DS_Store, __pycache__, bytecode, special file or multi-link "
           "file in the source set", problems=problems[:20], multilink=nlinks[:20])
    head = git_head(root)
    ck.add("S03", head == host["source"]["head"], "HEAD read from the Git files equals /source/head (gitdir, common "
           "directory, ref, commit and the four files' bindings)", ref=head["ref"], commit=head["commit"])
    ck.add("S04", head["commit"] == plan["source"]["commit"] == host["source"]["commit"] ==
           "4ca781429c5411c67c0965bc69306b42c6cc74ad", "HEAD is commit B")
    obj = loose_object(head["common_dir"], head["commit"])
    tree_line, parents, header_ok, name_ok = None, [], False, False
    if obj is not None:
        nul = obj.index(b"\0")
        header_ok = obj[:nul] == b"commit %d" % (len(obj) - nul - 1)
        name_ok = hashlib.sha1(obj).hexdigest() == head["commit"]
        body = obj[nul + 1:].decode("utf-8", "replace").split("\n\n", 1)[0].splitlines()
        tree_line = next((line[5:] for line in body if line.startswith("tree ")), None)
        parents = [line[7:] for line in body if line.startswith("parent ")]
    ck.add("S05", obj is not None and header_ok and name_ok and tree_line == plan["source"]["tree"] ==
           host["source"]["tree"] == "0935162c72fd9d804681e920da6f6d6e9066ff28",
           "commit B's loose object: its name recomputes, and it names the planned tree", parents=parents)
    index_path = head["gitdir"] + "/index"
    idx_raw, idx_facts, _ = C.read_bytes(index_path)
    idx = parse_index(idx_raw)
    tr = idx["tree_root"]
    ck.add("S06", idx["checksum_ok"] and idx["stages"] == 0 and tr is not None and tr["path"] == "" and
           tr["entry_count"] == idx["count"] and tr["sha1"] == plan["source"]["tree"],
           "the index's checksum is valid, it has no conflict stage, and its TREE extension caches the whole index "
           "as the planned tree", version=idx["version"], entries=idx["count"], extensions=idx["extensions"],
           tree_root=tr, index_sha256=idx_facts["sha256"])
    mismatched, untracked, mode_diff = [], [], []
    for rel, b in sorted(doc["files"].items()):
        entry = idx["entries"].get(rel)
        raw = C.read_bytes(root + "/" + rel)[0]
        if entry is None:
            untracked.append(rel)
            continue
        if blob_id(raw) != entry["sha1"]:
            mismatched.append(rel)
        executable = int(b["mode"], 8) & 0o100 != 0
        if entry["mode"] != ("100755" if executable else "100644"):
            mode_diff.append(rel)
    ck.add("S07", not mismatched and not untracked and not mode_diff,
           "every source-inventory file is tracked, and its bytes and executable bit equal its index entry, so the "
           "source set equals tree B's blobs", untracked=untracked[:20], mismatched=mismatched[:20],
           mode_differs=mode_diff[:20])
    blobs = {rel: idx["entries"][rel]["sha1"] for rel in (
        "prototypes/static_tray_v01/current_host_observation_v02.py",
        "prototypes/static_tray_v01/supervisor_darwin_v01.py", "prototypes/static_tray_v01/supervisor.py",
        "tools/native-reader-verification-macos-arm64-cp312.lock")}
    ck.add("S08", blobs["prototypes/static_tray_v01/current_host_observation_v02.py"] ==
           "e59d62922075e90b6cc3478f6bf3268fa7ab9926" and blobs["prototypes/static_tray_v01/supervisor_darwin_v01.py"]
           == "4765dd892785e7d3b41619a4463fd94822444b1c" and blobs["prototypes/static_tray_v01/supervisor.py"] ==
           "b02086915dcf28e2e915d7e3d2b66d253688d331",
           "the observer's and both supervisors' blobs are the ones the plan review read at B", blobs=blobs)
    sup = K.get("SUPERVISOR_FILES", {})
    ck.add("S09", isinstance(sup, dict) and all(rel in doc["files"] for rel in sup.values()),
           "the four supervisor-import files are in the source inventory", files=sorted(sup.values()) if
           isinstance(sup, dict) else None)
    pyc = []
    for tree in ("prototypes",):
        for dirpath, dirnames, filenames in os.walk(root + "/" + tree):
            pyc += [n for n in dirnames if n == "__pycache__"] + [n for n in filenames if n.endswith(".pyc")]
    ck.add("S10", not pyc, "no __pycache__ directory or bytecode anywhere under <worktree>/prototypes")
    result = {"script": "w3h_03_source.py", "tag": args.tag, "process": C.process_identity(),
              "started_epoch": started, "ended_epoch": time.time(), "checks": ck.rows, "summary": ck.summary(),
              "audit_events": C.EVENTS}
    print(C.write_new(args.out, lab.deep(result)), ck.summary())


if __name__ == "__main__":
    main()
