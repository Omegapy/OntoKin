"""W3 plan review 001, script s04: the source inventory, and commit C, its tree and the index, without Git.

Standard library only; starts nothing (audit hook); no Git is run. Loose objects are inflated
with zlib. Packed objects are found through the pack's version-2 index (fan-out table, sorted
names, 32-bit offsets with the 64-bit overflow table) and read from the pack by their type and
size header; OFS_DELTA and REF_DELTA objects are rebuilt by applying the delta's copy and insert
instructions to their base. Every object name is recomputed as SHA-1 of "<type> <size>\\0" plus its
bytes. The worktree's files are hashed as Git blobs (symbolic links by their target bytes). The
index (version 2) is parsed with its checksum and extensions.

The source inventory's set is the observer's schema (SOURCE_TREES, SOURCE_FILES and
SOURCE_OPTIONAL, written here as literals from the observer's source, W3-OBSERVER Q9).

Usage:
  python -I -S -B s04_source_and_git.py --worktree WT --commit C --tree T --source-inventory S --output OUT.json
"""
import argparse
import hashlib
import json
import mmap
import os
import posixpath
import stat
import struct
import sys
import time
import zlib

REFUSED = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty")
EVENTS = []


def _hook(event, args):
    if event in REFUSED:
        EVENTS.append(event)
        raise RuntimeError("process creation refused: " + event)


sys.addaudithook(_hook)

SOURCE_SCHEMA = "ontokin.current-host-readback-source/0.2.0"
SOURCE_TREES = ("ontokin", "tests", "prototypes/static_tray_v01", "tools/static_tray_reader_v01")
SOURCE_OPTIONAL = ("prototypes/__init__.py", "tools/__init__.py", "tests/__init__.py")
SOURCE_FILES = (
    "tools/check_local.py", "tools/prepare_current_host_readback.py", "tools/storage_identity.py",
    "tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock",
    "tools/native-reader-verification-macos-arm64-cp312.lock", "pyproject.toml",
    "docs/engineering/static-tray-mapping-c198/CONTROLS.json",
    "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json",
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md",
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json",
    "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json",
    "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip",
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md",
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json",
    "docs/engineering/localized-repair-c271/macos-contract-design-p31/ADOPTION.json")
ADOPTION_001 = "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"
TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}


def mode_text(info):
    return "0o%03o" % stat.S_IMODE(info.st_mode)


def read_all(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        chunks = []
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            chunks.append(block)
        return b"".join(chunks)
    finally:
        os.close(fd)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


# ----------------------------------------------------------------------------- source inventory

def source_inventory(root):
    found, problems = set(), []
    for tree in SOURCE_TREES:
        pending = [""]
        while pending:
            rel_dir = pending.pop()
            directory = root + "/" + tree + ("/" + rel_dir if rel_dir else "")
            for name in sorted(os.listdir(directory)):
                rel = rel_dir + "/" + name if rel_dir else name
                path = directory + "/" + name
                info = os.lstat(path)
                if name == ".DS_Store":
                    problems.append({"path": tree + "/" + rel, "problem": ".DS_Store"})
                if name == "__pycache__":
                    problems.append({"path": tree + "/" + rel, "problem": "__pycache__"})
                if stat.S_ISLNK(info.st_mode):
                    problems.append({"path": tree + "/" + rel, "problem": "symlink"})
                elif stat.S_ISDIR(info.st_mode):
                    pending.append(rel)
                elif stat.S_ISREG(info.st_mode):
                    if name.endswith((".pyc", ".pyo")):
                        problems.append({"path": tree + "/" + rel, "problem": "bytecode"})
                    found.add(tree + "/" + rel)
                else:
                    problems.append({"path": tree + "/" + rel, "problem": "special"})
    for rel in SOURCE_FILES:
        info = os.lstat(root + "/" + rel)
        if not stat.S_ISREG(info.st_mode):
            problems.append({"path": rel, "problem": "role is not a regular file"})
        found.add(rel)
    found.update(rel for rel in SOURCE_OPTIONAL if os.path.lexists(root + "/" + rel))
    files, links = {}, {}
    for rel in sorted(found):
        raw = read_all(root + "/" + rel)
        info = os.lstat(root + "/" + rel)
        files[rel] = {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw), "mode": mode_text(info)}
        links[rel] = info.st_nlink
    return {"schema": SOURCE_SCHEMA, "files": files}, links, problems


# ----------------------------------------------------------------------------- Git object store

class Store:
    def __init__(self, objects):
        self.objects = objects
        self.packs = []
        self.reads = {"loose": 0, "pack": 0}
        self.cache = {}
        pack_dir = objects + "/pack"
        for name in sorted(os.listdir(pack_dir)) if os.path.isdir(pack_dir) else []:
            if name.endswith(".idx"):
                self.packs.append(self._open_pack(pack_dir + "/" + name))

    def _open_pack(self, idx_path):
        raw = read_all(idx_path)
        assert raw[:4] == b"\xfftOc" and struct.unpack(">I", raw[4:8])[0] == 2, idx_path
        fanout = struct.unpack(">256I", raw[8:8 + 1024])
        count = fanout[255]
        names_at = 8 + 1024
        crc_at = names_at + 20 * count
        off_at = crc_at + 4 * count
        big_at = off_at + 4 * count
        assert hashlib.sha1(raw[:-20]).digest() == raw[-20:], "idx checksum " + idx_path
        offsets = {}
        for i in range(count):
            oid = raw[names_at + 20 * i:names_at + 20 * i + 20].hex()
            off = struct.unpack(">I", raw[off_at + 4 * i:off_at + 4 * i + 4])[0]
            if off & 0x80000000:
                j = off & 0x7FFFFFFF
                off = struct.unpack(">Q", raw[big_at + 8 * j:big_at + 8 * j + 8])[0]
            offsets[oid] = off
        pack_path = idx_path[:-4] + ".pack"
        fd = os.open(pack_path, os.O_RDONLY | os.O_NOFOLLOW)
        data = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        os.close(fd)
        assert data[:4] == b"PACK" and struct.unpack(">I", data[8:12])[0] == count, pack_path
        return {"idx": idx_path, "pack": pack_path, "count": count, "offsets": offsets, "data": data}

    @staticmethod
    def _inflate(data, pos):
        d = zlib.decompressobj()
        out, step = [], 65536
        while not d.eof:
            chunk = data[pos:pos + step]
            if not chunk:
                raise ValueError("truncated zlib stream")
            out.append(d.decompress(chunk))
            pos += step
        out.append(d.flush())
        return b"".join(out)

    def _packed(self, pack, offset):
        key = (pack["pack"], offset)
        if key in self.cache:
            return self.cache[key]
        data = pack["data"]
        pos = offset
        byte = data[pos]
        kind, size, shift = (byte >> 4) & 7, byte & 15, 4
        while byte & 0x80:
            pos += 1
            byte = data[pos]
            size |= (byte & 0x7F) << shift
            shift += 7
        pos += 1
        if kind == 6:
            byte = data[pos]
            pos += 1
            back = byte & 0x7F
            while byte & 0x80:
                byte = data[pos]
                pos += 1
                back = ((back + 1) << 7) | (byte & 0x7F)
            base_kind, base = self._packed(pack, offset - back)
            delta = self._inflate(data, pos)
            assert len(delta) == size
            result = (base_kind, apply_delta(base, delta))
        elif kind == 7:
            base_oid = bytes(data[pos:pos + 20]).hex()
            pos += 20
            base_kind, base = self.read(base_oid)
            delta = self._inflate(data, pos)
            assert len(delta) == size
            result = (base_kind, apply_delta(base, delta))
        else:
            body = self._inflate(data, pos)
            assert len(body) == size, "size header"
            result = (TYPES[kind], body)
        self.cache[key] = result
        return result

    def read(self, oid):
        loose = self.objects + "/" + oid[:2] + "/" + oid[2:]
        if os.path.lexists(loose):
            raw = zlib.decompress(read_all(loose))
            header, _, body = raw.partition(b"\0")
            kind, length = header.decode("ascii").split(" ")
            assert int(length) == len(body)
            self.reads["loose"] += 1
            storage = "loose"
        else:
            for pack in self.packs:
                if oid in pack["offsets"]:
                    kind, body = self._packed(pack, pack["offsets"][oid])
                    self.reads["pack"] += 1
                    storage = "pack"
                    break
            else:
                raise KeyError("object not found: " + oid)
        recomputed = hashlib.sha1(kind.encode("ascii") + b" " + str(len(body)).encode("ascii") + b"\0" + body).hexdigest()
        assert recomputed == oid, ("object name does not recompute", oid, recomputed)
        return kind, body


def apply_delta(base, delta):
    pos = 0

    def varint():
        nonlocal pos
        result = shift = 0
        while True:
            b = delta[pos]
            pos += 1
            result |= (b & 0x7F) << shift
            shift += 7
            if not b & 0x80:
                return result
    source_size, target_size = varint(), varint()
    assert source_size == len(base), "delta base size"
    out = bytearray()
    while pos < len(delta):
        op = delta[pos]
        pos += 1
        if op & 0x80:
            offset = size = 0
            for i in range(4):
                if op & (1 << i):
                    offset |= delta[pos] << (8 * i)
                    pos += 1
            for i in range(3):
                if op & (1 << (4 + i)):
                    size |= delta[pos] << (8 * i)
                    pos += 1
            out += base[offset:offset + (size or 0x10000)]
        elif op:
            out += delta[pos:pos + op]
            pos += op
        else:
            raise ValueError("delta opcode 0")
    assert len(out) == target_size, "delta target size"
    return bytes(out)


def parse_tree(body):
    entries, pos = [], 0
    while pos < len(body):
        space = body.index(b" ", pos)
        nul = body.index(b"\0", space)
        mode = body[pos:space].decode("ascii")
        name = body[space + 1:nul].decode("utf-8")
        oid = body[nul + 1:nul + 21].hex()
        entries.append((mode, name, oid))
        pos = nul + 21
    return entries


def walk_git_tree(store, oid, prefix, out, trees):
    kind, body = store.read(oid)
    assert kind == "tree", (oid, kind)
    trees[prefix] = oid
    for mode, name, child in parse_tree(body):
        path = prefix + "/" + name if prefix else name
        if mode in ("40000", "040000"):
            walk_git_tree(store, child, path, out, trees)
        else:
            out[path] = (mode, child)


def blob_oid(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def walk_worktree(root):
    files, dirs, special, ds, bytecode, multi = {}, [], [], [], [], []
    pending = [""]
    while pending:
        rel_dir = pending.pop()
        directory = root + "/" + rel_dir if rel_dir else root
        names = sorted(os.listdir(directory))
        for name in names:
            rel = rel_dir + "/" + name if rel_dir else name
            if rel in (".git", ".venv"):
                continue
            path = root + "/" + rel
            info = os.lstat(path)
            if name == ".DS_Store":
                ds.append(rel)
            if name.endswith((".pyc", ".pyo")) or name == "__pycache__":
                bytecode.append(rel)
            if stat.S_ISLNK(info.st_mode):
                files[rel] = ("120000", blob_oid(os.fsencode(os.readlink(path))), None)
            elif stat.S_ISDIR(info.st_mode):
                dirs.append(rel)
                pending.append(rel)
            elif stat.S_ISREG(info.st_mode):
                data = read_all(path)
                mode = "100755" if info.st_mode & stat.S_IXUSR else "100644"
                files[rel] = (mode, blob_oid(data), len(data))
                if info.st_nlink != 1:
                    multi.append(rel)
            else:
                special.append(rel)
    return files, dirs, special, ds, bytecode, multi


def parse_index(raw):
    assert hashlib.sha1(raw[:-20]).digest() == raw[-20:], "index checksum"
    assert raw[:4] == b"DIRC"
    version, count = struct.unpack(">II", raw[4:12])
    assert version in (2, 3), version
    pos, entries, flagged, conflicts = 12, {}, [], []
    for _ in range(count):
        start = pos
        fields = struct.unpack(">10I", raw[pos:pos + 40])
        oid = raw[pos + 40:pos + 60].hex()
        flags = struct.unpack(">H", raw[pos + 60:pos + 62])[0]
        pos += 62
        extended = 0
        if flags & 0x4000:
            extended = struct.unpack(">H", raw[pos:pos + 2])[0]
            pos += 2
        nul = raw.index(b"\0", pos)
        name = raw[pos:nul].decode("utf-8")
        pos = nul
        length = pos - start
        pad = 8 - (length % 8)
        pos += pad
        stage_bits = (flags >> 12) & 3
        mode = fields[6]
        mode_text_git = "%o" % mode
        if stage_bits:
            conflicts.append(name)
        if flags & 0x8000 or extended:
            flagged.append({"path": name, "assume_valid": bool(flags & 0x8000), "extended": extended})
        entries[name] = (mode_text_git, oid, fields[9])
    extensions, tree_root = [], None
    while pos < len(raw) - 20:
        signature = raw[pos:pos + 4].decode("ascii", "replace")
        size = struct.unpack(">I", raw[pos + 4:pos + 8])[0]
        data = raw[pos + 8:pos + 8 + size]
        extensions.append({"signature": signature, "size_bytes": size})
        if signature == "TREE":
            nul = data.index(b"\0")
            line_end = data.index(b"\n", nul)
            count_text, sub_text = data[nul + 1:line_end].decode("ascii").split(" ")
            tree_root = {"path": data[:nul].decode("ascii"), "entry_count": int(count_text),
                         "subtrees": int(sub_text),
                         "tree": data[line_end + 1:line_end + 21].hex() if int(count_text) >= 0 else None}
        pos += 8 + size
    assert pos == len(raw) - 20
    return {"version": version, "count": count, "entries": entries, "flagged": flagged, "conflicts": conflicts,
            "extensions": extensions, "tree_root": tree_root}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--source-inventory", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    t0 = time.time()
    wt = a.worktree
    out = {"script": os.path.basename(__file__), "argv": sys.argv, "pid": os.getpid(), "ppid": os.getppid()}

    # Source inventory
    mine, links, problems = source_inventory(wt)
    mine_raw = canonical(mine)
    frozen_raw = read_all(a.source_inventory)
    frozen = json.loads(frozen_raw)
    out["source_inventory"] = {
        "digest_mine": hashlib.sha256(mine_raw).hexdigest(), "digest_frozen": hashlib.sha256(frozen_raw).hexdigest(),
        "bytes_identical": mine_raw == frozen_raw, "files": len(mine["files"]),
        "bytes": sum(r["size_bytes"] for r in mine["files"].values()),
        "set_equal": set(mine["files"]) == set(frozen["files"]),
        "bindings_equal": mine["files"] == frozen["files"],
        "multi_link_files": sorted(r for r, n in links.items() if n != 1), "problems": problems,
        "adoption_001_in_set": ADOPTION_001 in mine["files"],
        "entry_point_binding": mine["files"].get("prototypes/static_tray_v01/current_host_observation_v02.py"),
        "supervisor_files_present": all(r in mine["files"] for r in (
            "prototypes/__init__.py", "prototypes/static_tray_v01/__init__.py", "prototypes/static_tray_v01/supervisor.py",
            "prototypes/static_tray_v01/supervisor_darwin_v01.py"))}

    # HEAD from the Git files
    dotgit = read_all(wt + "/.git").decode("utf-8").strip()
    assert dotgit.startswith("gitdir: ")
    gitdir = dotgit[len("gitdir: "):]
    commondir_text = read_all(gitdir + "/commondir").decode("utf-8").strip()
    common = os.path.realpath(posixpath.normpath(gitdir + "/" + commondir_text))
    head = read_all(gitdir + "/HEAD").decode("ascii").strip()
    ref = head[5:] if head.startswith("ref: ") else None
    sources = {"worktree_gitdir": None, "common_dir": None, "packed_refs": None}
    if ref:
        if os.path.lexists(gitdir + "/" + ref):
            sources["worktree_gitdir"] = read_all(gitdir + "/" + ref).decode("ascii").strip()
        if os.path.lexists(common + "/" + ref):
            sources["common_dir"] = read_all(common + "/" + ref).decode("ascii").strip()
        if os.path.lexists(common + "/packed-refs"):
            for line in read_all(common + "/packed-refs").decode("utf-8").splitlines():
                parts = line.split(" ")
                if len(parts) == 2 and parts[1] == ref:
                    sources["packed_refs"] = parts[0]
    resolved = sources["worktree_gitdir"] or sources["common_dir"] or sources["packed_refs"]
    backlink = read_all(gitdir + "/gitdir").decode("utf-8").strip() if os.path.lexists(gitdir + "/gitdir") else None
    out["head"] = {"dotgit_names_gitdir": dotgit, "commondir": commondir_text, "common_dir": common, "head": head,
                   "ref": ref, "ref_sources": sources, "commit": resolved, "equals_C": resolved == a.commit,
                   "gitdir_backlink": backlink, "backlink_is_worktree_dotgit": backlink == wt + "/.git",
                   "alternates": os.path.lexists(common + "/objects/info/alternates")}

    # Commit C and its tree
    store = Store(common + "/objects")
    kind, body = store.read(a.commit)
    lines = body.decode("utf-8").split("\n")
    header = {}
    for line in lines:
        if not line:
            break
        key, _, value = line.partition(" ")
        header.setdefault(key, []).append(value)
    message = body.decode("utf-8").split("\n\n", 1)[1] if b"\n\n" in body else ""
    committer = header.get("committer", [""])[0].rsplit(" ", 2)
    out["commit"] = {"oid": a.commit, "kind": kind, "storage": "loose" if os.path.lexists(
        common + "/objects/" + a.commit[:2] + "/" + a.commit[2:]) else "pack", "name_recomputed": True,
        "tree": header.get("tree"), "parents": header.get("parent"), "signed": "gpgsig" in header,
        "committer_epoch": int(committer[1]) if len(committer) == 3 else None,
        "committer_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(committer[1]))) if len(committer) == 3
        else None, "subject": message.split("\n", 1)[0],
        "tree_equals_director_tree": header.get("tree") == [a.tree]}
    tree_map, trees = {}, {}
    walk_git_tree(store, header["tree"][0], "", tree_map, trees)
    by_mode = {}
    for mode, _ in tree_map.values():
        by_mode[mode] = by_mode.get(mode, 0) + 1
    out["tree"] = {"oid": header["tree"][0], "entries": len(tree_map), "trees": len(trees), "by_mode": by_mode,
                   "subtrees": {k: trees.get(k) for k in (
                       "ontokin", "tests", "prototypes", "prototypes/static_tray_v01", "tools",
                       "tools/static_tray_reader_v01", "docs/engineering/localized-repair-c271/macos-implementation-p33",
                       "docs/engineering/localized-repair-c271/macos-qualification-p35",
                       "docs/engineering/localized-repair-c271/macos-qualification-p35/tooling")},
                   "store": {"packs": [{"idx": p["idx"], "objects": p["count"]} for p in store.packs],
                             "reads": store.reads}}

    # Worktree against the tree
    files, dirs, special, ds, bytecode, multi = walk_worktree(wt)
    missing = sorted(set(tree_map) - set(files))
    extra = sorted(set(files) - set(tree_map))
    changed = sorted(p for p in set(files) & set(tree_map) if files[p][1] != tree_map[p][1])
    mode_differs = sorted(p for p in set(files) & set(tree_map) if files[p][0] != tree_map[p][0])
    tracked_dirs = {posixpath.dirname(p) for p in tree_map}
    tracked_dirs = {"/".join(p.split("/")[:i]) for p in tracked_dirs for i in range(1, len(p.split("/")) + 1)}
    out["worktree"] = {"files": sum(1 for v in files.values() if v[0] != "120000"),
                       "symlinks": sum(1 for v in files.values() if v[0] == "120000"), "directories": len(dirs),
                       "missing": missing[:50], "extra": extra[:50], "changed": changed[:50],
                       "mode_differs": mode_differs[:50], "special": special, "ds_store": ds, "bytecode": bytecode,
                       "multi_link_files": multi[:50],
                       "directories_without_tracked_content": sorted(set(dirs) - tracked_dirs)[:50],
                       "equals_tree": not (missing or extra or changed or mode_differs)}

    # Index against the tree
    index = parse_index(read_all(gitdir + "/index"))
    imap = index["entries"]
    out["index"] = {"path": gitdir + "/index", "version": index["version"], "entries": index["count"],
                    "checksum_ok": True, "extensions": index["extensions"], "cache_tree_root": index["tree_root"],
                    "cache_tree_root_equals_tree": (index["tree_root"] or {}).get("tree") == header["tree"][0],
                    "conflicts": index["conflicts"], "flagged": index["flagged"],
                    "missing": sorted(set(tree_map) - set(imap))[:50], "extra": sorted(set(imap) - set(tree_map))[:50],
                    "differs": sorted(p for p in set(imap) & set(tree_map)
                                      if (imap[p][0], imap[p][1]) != tree_map[p])[:50],
                    "cached_size_differs": sorted(p for p in set(imap) & set(files) if files[p][2] is not None
                                                  and imap[p][2] != files[p][2])[:50]}
    out["index"]["equals_tree"] = not (out["index"]["missing"] or out["index"]["extra"] or out["index"]["differs"]
                                       or index["conflicts"])

    # Source inventory files are commit content
    mismatched = [rel for rel in mine["files"] if rel not in tree_map or files.get(rel, (None, None))[1]
                  != tree_map[rel][1]]
    out["source_inventory"]["every_file_is_commit_content"] = not mismatched
    out["source_inventory"]["not_commit_content"] = mismatched[:50]

    # The adoption record of amendment 001
    adoption_raw = read_all(wt + "/" + ADOPTION_001)
    containing = trees.get(posixpath.dirname(ADOPTION_001))
    out["adoption_record"] = {"relative": ADOPTION_001, "tree_entry": tree_map.get(ADOPTION_001),
                              "worktree_blob": blob_oid(adoption_raw),
                              "worktree_sha256": hashlib.sha256(adoption_raw).hexdigest(),
                              "worktree_size_bytes": len(adoption_raw),
                              "worktree_mode": mode_text(os.lstat(wt + "/" + ADOPTION_001)),
                              "containing_tree": containing,
                              "equals_blob_at_C": tree_map.get(ADOPTION_001, (None, None))[1] == blob_oid(adoption_raw),
                              "in_source_inventory": ADOPTION_001 in mine["files"]}
    try:
        adoption = json.loads(adoption_raw)
        out["adoption_record"]["content_summary"] = {k: adoption.get(k) for k in ("schema", "amendment", "decision",
                                                                                   "state", "design_revision")
                                                     if k in adoption}
        out["adoption_record"]["top_level_keys"] = sorted(adoption)
    except ValueError as exc:
        out["adoption_record"]["parse_error"] = str(exc)
    out["elapsed_s"] = round(time.time() - t0, 3)
    out["process_events"] = EVENTS
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    summary = {"source_digest_mine": out["source_inventory"]["digest_mine"],
               "source_bytes_identical": out["source_inventory"]["bytes_identical"],
               "source_problems": len(problems), "head_equals_C": out["head"]["equals_C"],
               "tree_equals_director_tree": out["commit"]["tree_equals_director_tree"],
               "worktree_equals_tree": out["worktree"]["equals_tree"], "index_equals_tree": out["index"]["equals_tree"],
               "cache_tree_root_equals_tree": out["index"]["cache_tree_root_equals_tree"],
               "adoption_equals_blob_at_C": out["adoption_record"]["equals_blob_at_C"],
               "elapsed_s": out["elapsed_s"], "process_events": EVENTS}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
