"""W2, observation plan 001 (gate MH, C271-P35): a static read of the worktree's Git state.

No Git is started and no process is created: an audit hook refuses every
process-creation event. HEAD, the ref, the commit, its trees and the index are
read from the Git directory's files. Every object's name is recomputed from its
bytes. The worktree's files (all but `.git` and `.venv` at its root) are
compared with commit C's tree by Git blob name, and the index with the same
tree. One absent output file is created exclusively and fsynced.

Launch (standard library only):
    <worktree>/.venv/bin/python -I -S -B w2_git_static.py --worktree W --commit C
        --tree T --source-inventory S --adoption-record REL --output O

Exit: 0 when every check holds, 1 when a difference is found, 2 on a refusal.
"""
import argparse
import hashlib
import json
import os
import posixpath
import stat
import struct
import sys
import time
import unicodedata
import zlib

REFUSED_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork",
                            "os.forkpty", "os.startfile", "pty.spawn"))
EVENTS = []


def _hook(event, args):
    if event in REFUSED_EVENTS:
        EVENTS.append(event)
        raise RuntimeError("process creation refused by the W2 audit hook: " + event)


sys.addaudithook(_hook)

TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}
CHUNK = 1024 * 1024


class Refusal(Exception):
    pass


def _require(condition, reason):
    if not condition:
        raise Refusal(reason)


def _read(path, limit=None):
    with open(path, "rb") as handle:
        data = handle.read() if limit is None else handle.read(limit + 1)
    _require(limit is None or len(data) <= limit, "file exceeds its allowance: " + path)
    return data


def apply_delta(base, delta):
    pos = 0

    def varint():
        nonlocal pos
        result = shift = 0
        while True:
            byte = delta[pos]
            pos += 1
            result |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                return result
    source_size, target_size = varint(), varint()
    _require(source_size == len(base), "delta base size differs")
    out = bytearray()
    while pos < len(delta):
        op = delta[pos]
        pos += 1
        if op & 0x80:
            offset = size = 0
            for index in range(4):
                if op & (1 << index):
                    offset |= delta[pos] << (8 * index)
                    pos += 1
            for index in range(3):
                if op & (1 << (4 + index)):
                    size |= delta[pos] << (8 * index)
                    pos += 1
            if size == 0:
                size = 0x10000
            _require(offset + size <= len(base), "delta copy outside its base")
            out += base[offset:offset + size]
        else:
            _require(op != 0, "delta opcode 0")
            out += delta[pos:pos + op]
            pos += op
    _require(len(out) == target_size, "delta result size differs")
    return bytes(out)


class Pack:
    def __init__(self, idx_path, pack_path):
        data = _read(idx_path)
        _require(data[:4] == b"\xfftOc" and struct.unpack(">I", data[4:8])[0] == 2, "unsupported pack index")
        _require(hashlib.sha1(data[:-20]).digest() == data[-20:], "pack index checksum differs: " + idx_path)
        self.fanout = struct.unpack(">256I", data[8:1032])
        count = self.fanout[255]
        base = 1032
        self.names = data[base:base + 20 * count]
        offsets = base + 24 * count
        self.offsets = data[offsets:offsets + 4 * count]
        self.large = data[offsets + 4 * count:len(data) - 40]
        self.count = count
        self.idx_path, self.pack_path = idx_path, pack_path
        self.handle = open(pack_path, "rb")
        header = self.handle.read(12)
        _require(header[:4] == b"PACK" and struct.unpack(">I", header[4:8])[0] in (2, 3), "unsupported pack")
        _require(struct.unpack(">I", header[8:12])[0] == count, "pack object count differs from its index")
        _require(data[-40:-20] == self._pack_trailer(), "pack checksum named by the index differs from the pack's")
        self.cache = {}

    def _pack_trailer(self):
        self.handle.seek(-20, os.SEEK_END)
        return self.handle.read(20)

    def find(self, name):
        first = name[0]
        low = self.fanout[first - 1] if first else 0
        high = self.fanout[first]
        while low < high:
            middle = (low + high) // 2
            candidate = self.names[20 * middle:20 * middle + 20]
            if candidate < name:
                low = middle + 1
            elif candidate > name:
                high = middle
            else:
                offset = struct.unpack(">I", self.offsets[4 * middle:4 * middle + 4])[0]
                if offset & 0x80000000:
                    index = offset & 0x7FFFFFFF
                    offset = struct.unpack(">Q", self.large[8 * index:8 * index + 8])[0]
                return offset
        return None

    def _inflate(self, offset, size):
        self.handle.seek(offset)
        stream = zlib.decompressobj()
        parts = []
        while not stream.eof:
            chunk = self.handle.read(65536)
            _require(bool(chunk), "truncated pack object")
            parts.append(stream.decompress(chunk))
        data = b"".join(parts)
        _require(len(data) == size, "inflated pack object size differs")
        return data

    def read_at(self, offset, store, depth=0):
        _require(depth < 4096, "delta chain too deep")
        if offset in self.cache:
            return self.cache[offset]
        self.handle.seek(offset)
        head = self.handle.read(40)
        pos = 0
        byte = head[pos]
        pos += 1
        kind, size, shift = (byte >> 4) & 7, byte & 15, 4
        while byte & 0x80:
            byte = head[pos]
            pos += 1
            size |= (byte & 0x7F) << shift
            shift += 7
        if kind in TYPES:
            result = (TYPES[kind], self._inflate(offset + pos, size))
        elif kind == 6:
            byte = head[pos]
            pos += 1
            distance = byte & 0x7F
            while byte & 0x80:
                byte = head[pos]
                pos += 1
                distance = ((distance + 1) << 7) | (byte & 0x7F)
            base_kind, base = self.read_at(offset - distance, store, depth + 1)
            result = (base_kind, apply_delta(base, self._inflate(offset + pos, size)))
        elif kind == 7:
            base_name = head[pos:pos + 20].hex()
            pos += 20
            base_kind, base, _ = store.read(base_name, verify=True)
            result = (base_kind, apply_delta(base, self._inflate(offset + pos, size)))
        else:
            raise Refusal("unsupported pack object type %d" % kind)
        if len(result[1]) <= 4 * 1024 * 1024:
            self.cache[offset] = result
        return result


class Store:
    def __init__(self, objects):
        self.objects = objects
        self.alternates = os.path.lexists(objects + "/info/alternates")
        _require(not self.alternates, "object alternates are not supported by this reader")
        pack_dir = objects + "/pack"
        self.packs = [Pack(pack_dir + "/" + name, pack_dir + "/" + name[:-4] + ".pack")
                      for name in sorted(os.listdir(pack_dir)) if name.endswith(".idx")]
        self.reads = {"loose": 0, "pack": 0}

    def read(self, name, verify=True):
        path = self.objects + "/" + name[:2] + "/" + name[2:]
        if os.path.lexists(path):
            raw = zlib.decompress(_read(path))
            header, _, body = raw.partition(b"\0")
            kind, size = header.decode("ascii").split(" ")
            _require(int(size) == len(body), "loose object size differs: " + name)
            where = "loose"
        else:
            for pack in self.packs:
                offset = pack.find(bytes.fromhex(name))
                if offset is not None:
                    kind, body = pack.read_at(offset, self)
                    where = "pack"
                    break
            else:
                raise Refusal("object not found: " + name)
        if verify:
            actual = hashlib.sha1(kind.encode("ascii") + b" " + str(len(body)).encode("ascii") + b"\0" + body)
            _require(actual.hexdigest() == name, "object name differs from its bytes: " + name)
        self.reads[where] += 1
        return kind, body, where


def parse_tree(body):
    entries, pos = [], 0
    while pos < len(body):
        space = body.index(b" ", pos)
        mode = body[pos:space].decode("ascii")
        nul = body.index(b"\0", space)
        name = body[space + 1:nul].decode("utf-8")
        entries.append((mode, name, body[nul + 1:nul + 21].hex()))
        pos = nul + 21
    return entries


def walk_tree(store, name, prefix, files, trees):
    kind, body, _ = store.read(name)
    _require(kind == "tree", "expected a tree: " + name)
    trees[prefix or "."] = name
    for mode, entry, oid in parse_tree(body):
        path = prefix + "/" + entry if prefix else entry
        if mode in ("40000", "040000"):
            walk_tree(store, oid, path, files, trees)
        else:
            _require(mode in ("100644", "100755", "120000", "160000"), "unexpected tree entry mode: " + mode)
            files[path] = (mode, oid)


def blob_name_of_file(path, size):
    digest_sha1, digest_sha256, length = hashlib.sha1(b"blob %d\0" % size), hashlib.sha256(), 0
    with open(path, "rb") as handle:
        while True:
            block = handle.read(CHUNK)
            if not block:
                break
            length += len(block)
            digest_sha1.update(block)
            digest_sha256.update(block)
    _require(length == size, "file changed while it was read: " + path)
    return digest_sha1.hexdigest(), digest_sha256.hexdigest()


def worktree_listing(root, skipped_names):
    files, directories, special, skipped, stack = {}, [], [], [], [""]
    while stack:
        relative = stack.pop()
        directory = root + "/" + relative if relative else root
        with os.scandir(directory) as iterator:
            names = sorted(entry.name for entry in iterator)
        for name in names:
            rel = relative + "/" + name if relative else name
            if not relative and name in skipped_names:
                skipped.append(rel)
                continue
            path = root + "/" + rel
            info = os.lstat(path)
            if stat.S_ISDIR(info.st_mode):
                directories.append(rel)
                stack.append(rel)
            elif stat.S_ISREG(info.st_mode):
                blob, sha256 = blob_name_of_file(path, info.st_size)
                files[rel] = {"kind": "file", "blob": blob, "sha256": sha256, "size_bytes": info.st_size,
                              "mode": "0o%03o" % stat.S_IMODE(info.st_mode), "nlink": info.st_nlink,
                              "git_mode": "100755" if info.st_mode & stat.S_IXUSR else "100644"}
            elif stat.S_ISLNK(info.st_mode):
                target = os.fsencode(os.readlink(path))
                files[rel] = {"kind": "symlink", "blob": hashlib.sha1(b"blob %d\0" % len(target) + target).hexdigest(),
                              "git_mode": "120000"}
            else:
                special.append(rel)
    return files, sorted(directories), sorted(special), sorted(skipped)


def lfs_pointer(store, oid):
    kind, body, _ = store.read(oid)
    if kind != "blob" or not body.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        return None
    fields = dict(line.split(" ", 1) for line in body.decode("ascii").splitlines() if " " in line)
    oid_field = fields.get("oid", "")
    return {"sha256": oid_field[len("sha256:"):] if oid_field.startswith("sha256:") else None,
            "size_bytes": int(fields["size"]) if fields.get("size", "").isdigit() else None}


def offset_varint(data, pos):
    byte = data[pos]
    pos += 1
    value = byte & 0x7F
    while byte & 0x80:
        byte = data[pos]
        pos += 1
        value = ((value + 1) << 7) | (byte & 0x7F)
    return value, pos


def read_index(path):
    data = _read(path)
    _require(data[:4] == b"DIRC", "not an index file")
    version, count = struct.unpack(">II", data[4:12])
    _require(version in (2, 3, 4), "unsupported index version %d" % version)
    checksum_ok = hashlib.sha1(data[:-20]).digest() == data[-20:]
    pos, previous, entries = 12, b"", {}
    for _ in range(count):
        start = pos
        fields = struct.unpack(">10I", data[pos:pos + 40])
        oid = data[pos + 40:pos + 60].hex()
        flags = struct.unpack(">H", data[pos + 60:pos + 62])[0]
        pos += 62
        extended = 0
        if version >= 3 and flags & 0x4000:
            extended = struct.unpack(">H", data[pos:pos + 2])[0]
            pos += 2
        if version == 4:
            strip, pos = offset_varint(data, pos)
            nul = data.index(b"\0", pos)
            name = previous[:len(previous) - strip] + data[pos:nul]
            pos = nul + 1
        else:
            nul = data.index(b"\0", pos)
            name = data[pos:nul]
            pos = start + ((pos - start + len(name) + 8) & ~7)
        previous = name
        entries[name.decode("utf-8")] = {"mode": "%o" % fields[6], "oid": oid, "stage": (flags >> 12) & 3,
                                         "assume_valid": bool(flags & 0x8000), "extended": extended,
                                         "size": fields[9]}
    extensions, cache_tree_root = [], None
    while pos < len(data) - 20:
        signature = data[pos:pos + 4].decode("latin-1")
        size = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + size]
        extensions.append({"signature": signature, "size_bytes": size})
        if signature == "TREE" and body[:1] == b"\0":
            line_end = body.index(b"\n", 1)
            count_text = body[1:line_end].decode("ascii").split(" ")[0]
            if int(count_text) >= 0:
                cache_tree_root = {"entry_count": int(count_text), "tree": body[line_end + 1:line_end + 21].hex()}
            else:
                cache_tree_root = {"entry_count": int(count_text), "tree": None}
        pos += 8 + size
    return {"version": version, "entries_count": count, "checksum_ok": checksum_ok, "extensions": extensions,
            "cache_tree_root": cache_tree_root}, entries


def main(argv):
    parser = argparse.ArgumentParser(prog="w2_git_static")
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--source-inventory", required=True)
    parser.add_argument("--adoption-record", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    started = time.time()
    _require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.flags.dont_write_bytecode == 1,
             "run under -I -S -B")
    root = os.path.realpath(args.worktree)
    _require(root == args.worktree, "the worktree path is not canonical")
    _require(not os.path.lexists(args.output), "the output exists")
    record = {"schema": "ontokin.c271.p35-w2-git-static/1", "refusals": [], "findings": []}

    # HEAD, statically.
    dotgit = _read(root + "/.git", 4096).decode("utf-8").strip()
    _require(dotgit.startswith("gitdir: "), "unsupported .git file")
    gitdir = dotgit[len("gitdir: "):]
    _require(os.path.realpath(gitdir) == gitdir, "gitdir is not canonical")
    common_rel = _read(gitdir + "/commondir", 4096).decode("utf-8").strip()
    common = os.path.realpath(posixpath.normpath(gitdir + "/" + common_rel))
    back = _read(gitdir + "/gitdir", 4096).decode("utf-8").strip()
    head_text = _read(gitdir + "/HEAD", 4096).decode("ascii").strip()
    _require(head_text.startswith("ref: refs/"), "HEAD is not a symbolic ref")
    ref = head_text[5:]
    sources = {}
    for label, base in (("worktree_gitdir", gitdir), ("common_dir", common)):
        path = base + "/" + ref
        sources[label] = _read(path, 4096).decode("ascii").strip() if os.path.lexists(path) else None
    packed = None
    if os.path.lexists(common + "/packed-refs"):
        for line in _read(common + "/packed-refs").decode("utf-8").splitlines():
            parts = line.split(" ")
            if len(parts) == 2 and parts[1] == ref:
                packed = parts[0]
    sources["packed_refs"] = packed
    resolved = sources["worktree_gitdir"] or sources["common_dir"] or packed
    record["head"] = {"dotgit": dotgit, "gitdir": gitdir, "commondir_text": common_rel, "common_dir": common,
                      "gitdir_backlink": back, "backlink_names_dotgit": back == root + "/.git",
                      "head": head_text, "ref": ref, "ref_sources": sources, "commit": resolved,
                      "equals_planned_commit": resolved == args.commit}
    if resolved != args.commit:
        record["findings"].append("HEAD does not resolve to the planned commit")

    # The commit and its tree, from the object store.
    store = Store(common + "/objects")
    kind, body, where = store.read(args.commit)
    _require(kind == "commit", "the planned commit is not a commit object")
    header = body.split(b"\n\n", 1)[0].decode("utf-8", "replace").splitlines()
    message = body.split(b"\n\n", 1)[1].decode("utf-8", "replace") if b"\n\n" in body else ""
    tree = [line[5:] for line in header if line.startswith("tree ")]
    parents = [line[7:] for line in header if line.startswith("parent ")]
    committer = [line for line in header if line.startswith("committer ")]
    stamp = committer[0].rsplit(" ", 2)[-2:] if committer else None
    record["commit"] = {"oid": args.commit, "storage": where, "name_recomputed": True, "tree": tree,
                        "parents": parents, "committer_time": {"epoch": int(stamp[0]), "offset": stamp[1]} if stamp else None,
                        "committer_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(stamp[0])))
                        if stamp else None, "signed": any(line.startswith("gpgsig") for line in header),
                        "subject": message.splitlines()[0] if message else None,
                        "tree_equals_planned_tree": tree == [args.tree]}
    if tree != [args.tree]:
        record["findings"].append("the commit's tree differs from the planned tree")
    tree_files, trees = {}, {}
    walk_tree(store, args.tree, "", tree_files, trees)
    lowered = {}
    for path in tree_files:
        lowered.setdefault(path.lower(), []).append(path)
    collisions = sorted(paths for paths in lowered.values() if len(paths) > 1)
    record["tree"] = {"oid": args.tree, "trees": len(trees), "entries": len(tree_files),
                      "by_mode": {mode: sum(1 for value in tree_files.values() if value[0] == mode)
                                  for mode in sorted({value[0] for value in tree_files.values()})},
                      "case_collisions": collisions,
                      "subtrees": {name: trees.get(name) for name in (
                          "ontokin", "tests", "prototypes", "prototypes/static_tray_v01", "tools",
                          "tools/static_tray_reader_v01", "docs/engineering/localized-repair-c271/macos-qualification-p35",
                          "docs/engineering/localized-repair-c271/macos-qualification-p35/tooling")}}

    # The worktree against the tree.
    files, directories, special, skipped = worktree_listing(root, (".git", ".venv"))
    normalized = {unicodedata.normalize("NFC", path): path for path in files}
    _require(len(normalized) == len(files), "two worktree paths normalize to one name")
    non_ascii = sorted(path for path in files if not path.isascii())
    missing = sorted(path for path in tree_files if path not in normalized)
    extra = sorted(normalized[path] for path in normalized if path not in tree_files)
    changed, mode_differs, lfs = [], [], []
    for path, (mode, oid) in sorted(tree_files.items()):
        if path not in normalized:
            continue
        entry = files[normalized[path]]
        if mode == "160000":
            changed.append({"path": path, "reason": "gitlink in the tree"})
            continue
        if entry["blob"] != oid:
            pointer = lfs_pointer(store, oid) if entry["kind"] == "file" else None
            if pointer and pointer["sha256"] == entry["sha256"] and pointer["size_bytes"] == entry["size_bytes"]:
                lfs.append(path)
            else:
                changed.append({"path": path, "reason": "blob differs", "tree": oid, "worktree": entry["blob"]})
        if entry["git_mode"] != mode:
            mode_differs.append({"path": path, "tree": mode, "worktree": entry["git_mode"]})
    tracked_dirs = {posixpath.dirname(path) for path in tree_files}
    tracked_dirs = {"/".join(path.split("/")[:index]) for path in tracked_dirs
                    for index in range(1, len(path.split("/")) + 1)} - {""}
    untracked_dirs = sorted(path for path in directories if unicodedata.normalize("NFC", path) not in tracked_dirs)
    ds_store = sorted(path for path in files if posixpath.basename(path) == ".DS_Store")
    bytecode = sorted(path for path in files if path.endswith((".pyc", ".pyo")) or "/__pycache__/" in "/" + path)
    record["worktree"] = {"root": root, "skipped": skipped, "files": sum(1 for v in files.values() if v["kind"] == "file"),
                          "symlinks": sum(1 for v in files.values() if v["kind"] == "symlink"),
                          "directories": len(directories), "special": special, "non_ascii_paths": len(non_ascii),
                          "ds_store": ds_store, "bytecode": bytecode, "multi_link_files": sorted(
                              path for path, value in files.items() if value.get("nlink", 1) != 1)}
    record["comparison"] = {"missing": missing, "extra": extra, "changed": changed, "mode_differs": mode_differs,
                            "lfs_pointers_matched": lfs, "directories_without_tracked_content": untracked_dirs,
                            "worktree_equals_tree": not (missing or extra or changed or mode_differs)}
    if not record["comparison"]["worktree_equals_tree"]:
        record["findings"].append("the worktree differs from the commit's tree")

    # The index against the tree.
    index_path = gitdir + "/index"
    index_info, index_entries = read_index(index_path)
    conflicts = sorted(path for path, entry in index_entries.items() if entry["stage"] != 0)
    flagged = sorted(path for path, entry in index_entries.items() if entry["extended"] or entry["assume_valid"])
    index_missing = sorted(path for path in tree_files if path not in index_entries)
    index_extra = sorted(path for path in index_entries if path not in tree_files)
    index_differs = sorted(path for path, (mode, oid) in tree_files.items() if path in index_entries
                           and (index_entries[path]["oid"] != oid or index_entries[path]["mode"] != mode))
    size_differs = sorted(path for path, entry in index_entries.items() if normalized.get(path)
                          and files[normalized[path]]["kind"] == "file"
                          and entry["size"] != files[normalized[path]]["size_bytes"] % (1 << 32)
                          and path not in lfs)
    index_info.update(path=index_path, conflicts=conflicts, flagged_entries=flagged, missing=index_missing,
                      extra=index_extra, differs=index_differs, cached_size_differs=size_differs,
                      cache_tree_root_equals_tree=(index_info["cache_tree_root"] or {}).get("tree") == args.tree,
                      index_equals_tree=not (index_missing or index_extra or index_differs or conflicts))
    record["index"] = index_info
    if not index_info["index_equals_tree"] or not index_info["checksum_ok"]:
        record["findings"].append("the index differs from the commit's tree")

    # The source inventory against the tree and the worktree.
    raw = _read(args.source_inventory)
    inventory = json.loads(raw.decode("utf-8"))
    rows = inventory["files"]
    not_in_tree = sorted(path for path in rows if path not in tree_files)
    blob_mismatch = sorted(path for path in rows if path in tree_files and path in files
                           and files[path]["blob"] != tree_files[path][1])
    binding_mismatch = sorted(path for path, binding in rows.items() if path not in files
                              or {"sha256": files[path]["sha256"], "size_bytes": files[path]["size_bytes"],
                                  "mode": files[path]["mode"]} != binding)
    record["source_inventory"] = {"path": args.source_inventory, "sha256": hashlib.sha256(raw).hexdigest(),
                                  "size_bytes": len(raw), "schema": inventory.get("schema"), "files": len(rows),
                                  "bytes": sum(row["size_bytes"] for row in rows.values()),
                                  "not_in_tree": not_in_tree, "blob_mismatch": blob_mismatch,
                                  "binding_mismatch": binding_mismatch,
                                  "every_file_is_commit_content": not (not_in_tree or blob_mismatch or binding_mismatch)}
    if not record["source_inventory"]["every_file_is_commit_content"]:
        record["findings"].append("the source inventory is not exactly the commit's content")

    # The amendment's adoption record, which lies outside the source set.
    rel = args.adoption_record
    entry = files.get(rel)
    record["adoption_record"] = {
        "path": root + "/" + rel, "relative": rel, "in_source_inventory": rel in rows,
        "worktree": {k: entry[k] for k in ("sha256", "size_bytes", "mode", "blob")} if entry else None,
        "tree": {"mode": tree_files[rel][0], "blob": tree_files[rel][1]} if rel in tree_files else None,
        "containing_tree": trees.get(posixpath.dirname(rel)),
        "worktree_equals_commit": bool(entry and rel in tree_files and entry["blob"] == tree_files[rel][1])}
    if not record["adoption_record"]["worktree_equals_commit"]:
        record["findings"].append("the adoption record differs from the commit's blob")

    record["store"] = {"objects": common + "/objects", "alternates": store.alternates, "reads": store.reads,
                       "packs": [{"index": pack.idx_path, "pack": pack.pack_path, "objects": pack.count}
                                 for pack in store.packs]}
    record["process"] = {"pid": os.getpid(), "argv": sys.argv, "orig_argv": getattr(sys, "orig_argv", None),
                         "executable": sys.executable, "version": sys.version,
                         "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                                   "dont_write_bytecode": sys.flags.dont_write_bytecode,
                                   "ignore_environment": sys.flags.ignore_environment},
                         "refused_process_events": EVENTS, "cwd": os.getcwd(),
                         "script_sha256": hashlib.sha256(_read(os.path.realpath(__file__))).hexdigest(),
                         "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                         "elapsed_s": round(time.time() - started, 3)}
    record["passed"] = not record["findings"]
    data = (json.dumps(record, sort_keys=True, indent=1, ensure_ascii=True) + "\n").encode("ascii")
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    directory = os.open(os.path.dirname(args.output), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    sys.stdout.write(json.dumps({"output": args.output, "sha256": hashlib.sha256(data).hexdigest(),
                                 "size_bytes": len(data), "passed": record["passed"],
                                 "findings": record["findings"]}, sort_keys=True) + "\n")
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Refusal as exc:
        sys.stderr.write(json.dumps({"refused": str(exc)}) + "\n")
        raise SystemExit(2)
