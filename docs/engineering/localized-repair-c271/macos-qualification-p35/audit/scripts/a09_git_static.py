"""W4 audit 001, a09: the worktree, commit C and the two exports, from the Git files with this auditor's
own reader. No Git is started (an audit hook refuses every process creation).

Usage: a09_git_static.py WORKTREE COMMIT TREE BASELINE_COMMIT EXPORT_C EXPORT_BASELINE OUTPUT

  - HEAD of the worktree (its .git file, gitdir, HEAD, the ref in the common directory);
  - commit C and the baseline commit read from the object store (loose objects and pack v2 with
    OFS/REF deltas); their trees;
  - the worktree's index: every entry against the file's own Git blob hash and mode, its stage and
    flags; the tree hash computed from the index against C's tree;
  - the worktree walked: tracked set against the index, untracked files outside .venv, bytecode and
    .DS_Store outside .venv;
  - each extracted export directory: its tree hash computed from its files, against the commit's tree.
"""
import hashlib
import json
import os
import stat
import struct
import sys
import zlib


def _refuse(event, args):
    if event in ("subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn",
                 "os.system", "os.startfile"):
        raise PermissionError("this audit script starts no process: " + event)


sys.addaudithook(_refuse)


class Store:
    def __init__(self, objects):
        self.objects = objects
        self.packs = []
        pack_dir = os.path.join(objects, "pack")
        for name in sorted(os.listdir(pack_dir)):
            if name.endswith(".idx"):
                self.packs.append(self._load_index(os.path.join(pack_dir, name)))

    def _load_index(self, path):
        data = open(path, "rb").read()
        assert data[:4] == b"\xfftOc" and struct.unpack(">I", data[4:8])[0] == 2, "pack index v2"
        fanout = struct.unpack(">256I", data[8:8 + 1024])
        count = fanout[-1]
        names_at = 8 + 1024
        offsets_at = names_at + 20 * count + 4 * count
        large_at = offsets_at + 4 * count
        table = {}
        for i in range(count):
            name = data[names_at + 20 * i: names_at + 20 * i + 20].hex()
            offset = struct.unpack(">I", data[offsets_at + 4 * i: offsets_at + 4 * i + 4])[0]
            if offset & 0x80000000:
                index = offset & 0x7FFFFFFF
                offset = struct.unpack(">Q", data[large_at + 8 * index: large_at + 8 * index + 8])[0]
            table[name] = offset
        pack = open(path[:-4] + ".pack", "rb").read()
        assert pack[:4] == b"PACK", "pack header"
        return {"table": table, "pack": pack, "by_offset": {v: k for k, v in table.items()}}

    def read(self, name):
        loose = os.path.join(self.objects, name[:2], name[2:])
        if os.path.exists(loose):
            raw = zlib.decompress(open(loose, "rb").read())
            header, _, body = raw.partition(b"\0")
            kind, size = header.decode().split(" ")
            assert int(size) == len(body)
            return kind, body
        for pack in self.packs:
            if name in pack["table"]:
                return self._read_packed(pack, pack["table"][name])
        raise KeyError(name)

    def _read_packed(self, pack, offset):
        data = pack["pack"]
        byte = data[offset]
        kind = (byte >> 4) & 7
        size = byte & 15
        shift, position = 4, offset + 1
        while byte & 0x80:
            byte = data[position]
            size |= (byte & 0x7F) << shift
            shift += 7
            position += 1
        if kind in (1, 2, 3, 4):
            body = self._inflate(data, position, size)
            return {1: "commit", 2: "tree", 3: "blob", 4: "tag"}[kind], body
        if kind == 6:
            byte = data[position]
            back = byte & 0x7F
            position += 1
            while byte & 0x80:
                byte = data[position]
                back = ((back + 1) << 7) | (byte & 0x7F)
                position += 1
            base_kind, base = self._read_packed(pack, offset - back)
        elif kind == 7:
            base_name = data[position: position + 20].hex()
            position += 20
            base_kind, base = self.read(base_name)
        else:
            raise ValueError("pack object type %d" % kind)
        delta = self._inflate(data, position, size)
        return base_kind, self._apply(base, delta)

    @staticmethod
    def _inflate(data, position, size):
        decompressor = zlib.decompressobj()
        out = b""
        view = memoryview(data)
        chunk = 1 << 16
        while not decompressor.eof:
            if position >= len(data):
                raise ValueError("truncated zlib stream in pack")
            out += decompressor.decompress(view[position:position + chunk])
            position += chunk
        assert len(out) == size, "inflated size"
        return out

    @staticmethod
    def _apply(base, delta):
        def varint(position):
            value, shift = 0, 0
            while True:
                byte = delta[position]
                position += 1
                value |= (byte & 0x7F) << shift
                shift += 7
                if not byte & 0x80:
                    return value, position
        source_size, position = varint(0)
        target_size, position = varint(position)
        assert source_size == len(base)
        out = bytearray()
        while position < len(delta):
            op = delta[position]
            position += 1
            if op & 0x80:
                offset = size = 0
                for i in range(4):
                    if op & (1 << i):
                        offset |= delta[position] << (8 * i)
                        position += 1
                for i in range(3):
                    if op & (0x10 << i):
                        size |= delta[position] << (8 * i)
                        position += 1
                size = size or 0x10000
                out += base[offset: offset + size]
            elif op:
                out += delta[position: position + op]
                position += op
            else:
                raise ValueError("delta op 0")
        assert len(out) == target_size
        return bytes(out)


def blob_hash(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def tree_hash(entries):
    """entries: {path: (mode_octal_str, sha1hex)} -> root tree sha1."""
    root = {}
    for path, value in entries.items():
        parts = path.split("/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def build(node):
        items = []
        for name, value in node.items():
            if isinstance(value, dict):
                items.append((name + "/", b"40000 " + name.encode() + b"\0" + bytes.fromhex(build(value))))
            else:
                mode, sha = value
                items.append((name, mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(sha)))
        items.sort(key=lambda item: item[0].encode())
        body = b"".join(raw for _, raw in items)
        return hashlib.sha1(b"tree %d\0" % len(body) + body).hexdigest()

    return build(root)


def read_index(path):
    data = open(path, "rb").read()
    assert data[:4] == b"DIRC"
    version, count = struct.unpack(">II", data[4:12])
    position, entries, previous = 12, [], b""
    for _ in range(count):
        start = position
        fields = struct.unpack(">10I", data[position: position + 40])
        sha = data[position + 40: position + 60].hex()
        flags = struct.unpack(">H", data[position + 60: position + 62])[0]
        position += 62
        extended = 0
        if version >= 3 and flags & 0x4000:
            extended = struct.unpack(">H", data[position: position + 2])[0]
            position += 2
        if version == 4:
            strip, shift = 0, 0
            while True:
                byte = data[position]
                position += 1
                strip |= (byte & 0x7F) << shift
                shift += 7
                if not byte & 0x80:
                    break
            end = data.index(b"\0", position)
            name = previous[:len(previous) - strip] + data[position:end]
            position = end + 1
        else:
            end = data.index(b"\0", position)
            name = data[position:end]
            position = start + ((62 + (2 if extended or (version >= 3 and flags & 0x4000) else 0) + len(name) + 8) // 8) * 8
        previous = name
        entries.append({"path": name.decode(), "mode": "%o" % fields[6], "sha1": sha,
                        "stage": (flags >> 12) & 3, "assume_valid": bool(flags & 0x8000),
                        "skip_worktree": bool(extended & 0x4000), "intent_to_add": bool(extended & 0x2000),
                        "size": fields[9]})
    return version, entries


def main():
    worktree, commit, tree, baseline, export_c, export_baseline, output = sys.argv[1:8]
    report = {"schema": "w4-audit-001.a09-git-static/1"}
    pointer = open(os.path.join(worktree, ".git")).read().strip()
    gitdir = pointer.split("gitdir: ", 1)[1]
    head = open(os.path.join(gitdir, "HEAD")).read().strip()
    common = os.path.normpath(os.path.join(gitdir, open(os.path.join(gitdir, "commondir")).read().strip()))
    head_commit = None
    if head.startswith("ref: "):
        ref = head[5:]
        loose_ref = os.path.join(common, ref)
        if os.path.exists(loose_ref):
            head_commit = open(loose_ref).read().strip()
        else:
            for line in open(os.path.join(common, "packed-refs")):
                if line.strip().endswith(" " + ref):
                    head_commit = line.split()[0]
    else:
        head_commit = head
    report["head"] = {"ref": head, "commit": head_commit, "equals_C": head_commit == commit}
    store = Store(os.path.join(common, "objects"))
    commits = {}
    for name in (commit, baseline):
        kind, body = store.read(name)
        text = body.decode("utf-8", "replace")
        lines = text.split("\n")
        commits[name] = {"kind": kind, "tree": lines[0].split(" ")[1] if lines[0].startswith("tree ") else None,
                         "parents": [l.split(" ")[1] for l in lines if l.startswith("parent ")],
                         "hash_ok": hashlib.sha1(("%s %d\0" % (kind, len(body))).encode() + body).hexdigest() == name}
    report["commits"] = commits
    report["C_tree_equals_frozen"] = commits[commit]["tree"] == tree

    # The index against the worktree, and the tree hash from the index.
    version, entries = read_index(os.path.join(gitdir, "index"))
    problems = []
    mapping = {}
    for entry in entries:
        path = os.path.join(worktree, entry["path"])
        info = os.lstat(path) if os.path.lexists(path) else None
        if info is None:
            problems.append((entry["path"], "absent"))
            continue
        if stat.S_ISLNK(info.st_mode):
            data, mode = os.readlink(path).encode(), "120000"
        else:
            data = open(path, "rb").read()
            mode = "100755" if info.st_mode & 0o111 else "100644"
        if blob_hash(data) != entry["sha1"]:
            problems.append((entry["path"], "content differs from the index"))
        if mode != entry["mode"]:
            problems.append((entry["path"], "mode %s vs %s" % (mode, entry["mode"])))
        if entry["stage"] or entry["assume_valid"] or entry["skip_worktree"] or entry["intent_to_add"]:
            problems.append((entry["path"], "flags"))
        mapping[entry["path"]] = (entry["mode"], entry["sha1"])
    computed_tree = tree_hash(mapping)
    tracked = {entry["path"] for entry in entries}
    untracked, bytecode, ds_store = [], [], []
    for parent, directories, names in os.walk(worktree):
        rel_parent = os.path.relpath(parent, worktree)
        if rel_parent == ".":
            directories[:] = [d for d in directories if d != ".venv"]
        for name in directories + names:
            rel = os.path.normpath(os.path.join(rel_parent, name))
            if name == "__pycache__" or name.endswith((".pyc", ".pyo")):
                bytecode.append(rel)
            if name == ".DS_Store":
                ds_store.append(rel)
        for name in names:
            rel = os.path.normpath(os.path.join(rel_parent, name))
            if rel == ".git":
                continue
            if rel not in tracked:
                untracked.append(rel)
        for name in list(directories):
            full = os.path.join(parent, name)
            if os.path.islink(full):
                rel = os.path.normpath(os.path.join(rel_parent, name))
                if rel not in tracked:
                    untracked.append(rel)
    report["index"] = {"version": version, "entries": len(entries), "problems": problems[:50], "problem_count": len(problems),
                       "tree_from_index": computed_tree, "tree_from_index_equals_C": computed_tree == tree,
                       "untracked_outside_venv": untracked[:50], "untracked_count": len(untracked),
                       "bytecode_outside_venv": bytecode[:50], "ds_store": ds_store}

    # The extracted exports against the commits' trees.
    def directory_tree(root):
        entries, others = {}, []
        for parent, directories, names in os.walk(root):
            for name in list(directories):
                full = os.path.join(parent, name)
                if os.path.islink(full):
                    directories.remove(name)
                    names.append(name)
            for name in names:
                full = os.path.join(parent, name)
                rel = os.path.relpath(full, root)
                info = os.lstat(full)
                if stat.S_ISLNK(info.st_mode):
                    entries[rel] = ("120000", blob_hash(os.readlink(full).encode()))
                elif stat.S_ISREG(info.st_mode):
                    entries[rel] = ("100755" if info.st_mode & 0o111 else "100644", blob_hash(open(full, "rb").read()))
                else:
                    others.append(rel)
        return entries, others
    exports = {}
    for name, root in ((commit, export_c), (baseline, export_baseline)):
        entries_export, others = directory_tree(root)
        computed = tree_hash(entries_export)
        exports[name] = {"root": root, "files": len(entries_export), "others": others,
                         "tree_computed": computed, "tree_of_commit": commits[name]["tree"],
                         "equal": computed == commits[name]["tree"]}
    report["exports"] = exports
    report["export_C_equals_index_set"] = sorted(directory_tree(export_c)[0]) == sorted(mapping)
    data = json.dumps(report, indent=1, sort_keys=True).encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps(report, indent=1)[:6000])


main()
