"""W3 plan review 001, s04: the source inventory of B, and Git's files read without starting Git.

1. The source inventory (ontokin.current-host-readback-source/0.2.0): the observer's source set
   (its four trees, sixteen roles and three optional files, as its source states them), recomputed,
   compared byte for byte with the frozen file.
2. HEAD from the worktree's Git files; commit B and its tree from the object store (loose objects and
   the pack, deltas applied, every object name recomputed from its bytes); the worktree compared with
   the tree; the index parsed and compared with the tree; the first-parent chain from B back to MH's
   commit C, and the tree difference C..B; the Git blob ids of named files at B and at C.

python3 -I -S -B s04_source_and_git.py --worktree W --commit B --tree T --mh-commit C --expected FILE
    [--named REL ...] [--label NAME=PATH ...] --output OUT
"""
import argparse
import hashlib
import mmap
import os
import posixpath
import stat
import struct
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3_common as common  # noqa: E402
sys.path.pop(0)

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


class Refused(Exception):
    pass


# ---------------------------------------------------------------------------
# 1. Source inventory
# ---------------------------------------------------------------------------

def source_inventory(root, problems):
    found = set()
    for tree in SOURCE_TREES:
        stack = [""]
        base = root + "/" + tree
        while stack:
            rel = stack.pop()
            directory = base + "/" + rel if rel else base
            for name in sorted(os.listdir(directory)):
                sub = rel + "/" + name if rel else name
                path = base + "/" + sub
                info = os.lstat(path)
                if name == ".DS_Store":
                    problems.append({"rule": "DS_STORE", "path": path})
                if name == "__pycache__":
                    problems.append({"rule": "PYCACHE", "path": path})
                if stat.S_ISLNK(info.st_mode):
                    problems.append({"rule": "SYMLINK", "path": path})
                elif stat.S_ISDIR(info.st_mode):
                    stack.append(sub)
                elif stat.S_ISREG(info.st_mode):
                    if name.endswith((".pyc", ".pyo")):
                        problems.append({"rule": "BYTECODE", "path": path})
                    found.add(tree + "/" + sub)
                else:
                    problems.append({"rule": "SPECIAL", "path": path})
    for rel in SOURCE_FILES:
        path = root + "/" + rel
        if os.path.realpath(path) != path or not os.path.isfile(path) or os.path.islink(path):
            problems.append({"rule": "ROLE", "path": rel})
        found.add(rel)
    found.update(rel for rel in SOURCE_OPTIONAL if os.path.lexists(root + "/" + rel))
    files, multi = {}, []
    for rel in sorted(found):
        _, binding, _, info = common.read_bytes(root + "/" + rel, keep=False)
        if info.st_nlink != 1:
            multi.append(rel)
        files[rel] = binding
    return {"schema": "ontokin.current-host-readback-source/0.2.0", "files": files}, multi


# ---------------------------------------------------------------------------
# 2. Git object store, read without Git
# ---------------------------------------------------------------------------

def object_name(kind, data):
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


class Store:
    TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}

    def __init__(self, objects):
        self.objects = objects
        alternates = objects + "/info/alternates"
        self.alternates = os.path.lexists(alternates)
        self.packs, self.index = [], {}
        self.stats = {"loose_reads": 0, "packed_reads": 0, "delta_ofs": 0, "delta_ref": 0}
        self.cache = {}
        pack_dir = objects + "/pack"
        for name in sorted(os.listdir(pack_dir)):
            if name.endswith(".idx"):
                self._open_pack(pack_dir + "/" + name)

    def _open_pack(self, idx_path):
        idx, _, _, _ = common.read_bytes(idx_path)
        if idx[:4] != b"\xfftOc" or struct.unpack(">I", idx[4:8])[0] != 2:
            raise Refused("unsupported pack index: " + idx_path)
        if hashlib.sha1(idx[:-20]).digest() != idx[-20:]:
            raise Refused("pack index checksum: " + idx_path)
        fanout = struct.unpack(">256I", idx[8:8 + 1024])
        count = fanout[255]
        names_at = 8 + 1024
        crc_at = names_at + 20 * count
        off_at = crc_at + 4 * count
        large_at = off_at + 4 * count
        pack_checksum = idx[-40:-20]
        offsets = struct.unpack(">%dI" % count, idx[off_at:off_at + 4 * count])
        large_count = sum(1 for value in offsets if value & 0x80000000)
        large = struct.unpack(">%dQ" % large_count, idx[large_at:large_at + 8 * large_count]) if large_count else ()
        pack_path = idx_path[:-4] + ".pack"
        fd = os.open(pack_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        size = os.fstat(fd).st_size
        data = mmap.mmap(fd, 0, prot=mmap.PROT_READ)
        os.close(fd)
        if data[:4] != b"PACK" or struct.unpack(">I", data[4:8])[0] not in (2, 3):
            raise Refused("unsupported pack: " + pack_path)
        pack_count = struct.unpack(">I", data[8:12])[0]
        trailer = data[size - 20:size]
        digest = hashlib.sha1()
        for start in range(0, size - 20, 1 << 24):
            digest.update(data[start:min(start + (1 << 24), size - 20)])
        number = len(self.packs)
        self.packs.append({"path": pack_path, "data": data, "size": size, "objects": count,
                           "pack_header_objects": pack_count, "trailer_equals_index": trailer == pack_checksum,
                           "content_sha1_equals_trailer": digest.digest() == trailer,
                           "index_checksum_valid": True, "large_offsets": large_count})
        previous = b""
        for position in range(count):
            name = idx[names_at + 20 * position:names_at + 20 * position + 20]
            if name <= previous:
                raise Refused("pack index names not sorted")
            previous = name
            value = offsets[position]
            offset = large[value & 0x7FFFFFFF] if value & 0x80000000 else value
            self.index[name.hex()] = (number, offset)

    def _packed(self, number, offset, depth=0):
        key = (number, offset)
        if key in self.cache:
            return self.cache[key]
        if depth > 100:
            raise Refused("delta chain too deep")
        data = self.packs[number]["data"]
        position = offset
        byte = data[position]
        position += 1
        kind, size, shift = (byte >> 4) & 7, byte & 15, 4
        while byte & 0x80:
            byte = data[position]
            position += 1
            size |= (byte & 0x7F) << shift
            shift += 7
        base = None
        if kind == 6:
            byte = data[position]
            position += 1
            distance = byte & 0x7F
            while byte & 0x80:
                byte = data[position]
                position += 1
                distance = ((distance + 1) << 7) | (byte & 0x7F)
            base = ("ofs", offset - distance)
        elif kind == 7:
            base = ("ref", bytes(data[position:position + 20]).hex())
            position += 20
        decompressor, chunks, total = zlib.decompressobj(), [], 0
        while not decompressor.eof:
            block = decompressor.decompress(data[position:position + 65536])
            position += 65536
            chunks.append(block)
            total += len(block)
            if position > self.packs[number]["size"] + 65536:
                raise Refused("truncated pack object")
        body = b"".join(chunks)
        if len(body) != size:
            raise Refused("pack object size")
        if base is None:
            result = (self.TYPES[kind], body)
        else:
            if base[0] == "ofs":
                self.stats["delta_ofs"] += 1
                base_kind, base_body = self._packed(number, base[1], depth + 1)
            else:
                self.stats["delta_ref"] += 1
                base_kind, base_body = self.read(base[1], depth + 1)
            result = (base_kind, apply_delta(base_body, body))
        if result[0] in ("tree", "commit"):
            self.cache[key] = result
        return result

    def has(self, name):
        return name in self.index or os.path.lexists(self.objects + "/" + name[:2] + "/" + name[2:])

    def read(self, name, depth=0):
        loose = self.objects + "/" + name[:2] + "/" + name[2:]
        if os.path.lexists(loose):
            raw, _, _, _ = common.read_bytes(loose)
            data = zlib.decompress(raw)
            header, _, body = data.partition(b"\0")
            kind, _, size = header.decode("ascii").partition(" ")
            if int(size) != len(body):
                raise Refused("loose object size: " + name)
            self.stats["loose_reads"] += 1
            where = "loose"
        elif name in self.index:
            kind, body = self._packed(*self.index[name], depth=depth)
            self.stats["packed_reads"] += 1
            where = "packed"
        else:
            raise Refused("object not found: " + name)
        if object_name(kind, body) != name:
            raise Refused("object name does not recompute: " + name)
        if depth == 0:
            self.last_where = where
        return kind, body


def apply_delta(base, delta):
    position = 0

    def varint():
        nonlocal position
        result, shift = 0, 0
        while True:
            byte = delta[position]
            position += 1
            result |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                return result
    source_size, target_size = varint(), varint()
    if source_size != len(base):
        raise Refused("delta base size")
    out = bytearray()
    while position < len(delta):
        command = delta[position]
        position += 1
        if command & 0x80:
            offset = size = 0
            for bit in range(4):
                if command & (1 << bit):
                    offset |= delta[position] << (8 * bit)
                    position += 1
            for bit in range(3):
                if command & (0x10 << bit):
                    size |= delta[position] << (8 * bit)
                    position += 1
            size = size or 0x10000
            out += base[offset:offset + size]
        elif command:
            out += delta[position:position + command]
            position += command
        else:
            raise Refused("reserved delta command")
    if len(out) != target_size:
        raise Refused("delta target size")
    return bytes(out)


def parse_commit(body):
    text = body.decode("utf-8", "replace")
    header, _, message = text.partition("\n\n")
    tree, parents, committer, signed = None, [], None, False
    for line in header.split("\n"):
        if line.startswith("tree "):
            tree = line[5:]
        elif line.startswith("parent "):
            parents.append(line[7:])
        elif line.startswith("committer "):
            committer = line.rsplit(" ", 2)[-2:]
        elif line.startswith("gpgsig"):
            signed = True
    return {"tree": tree, "parents": parents, "committer_time": committer, "signed": signed,
            "subject": message.split("\n", 1)[0]}


def parse_tree(body):
    rows, position = [], 0
    while position < len(body):
        space = body.index(b" ", position)
        nul = body.index(b"\0", space)
        mode = body[position:space].decode("ascii")
        name = body[space + 1:nul].decode("utf-8", "surrogateescape")
        rows.append((mode, name, body[nul + 1:nul + 21].hex()))
        position = nul + 21
    return rows


def flatten(store, tree, prefix="", out=None, counts=None):
    if out is None:
        out, counts = {}, {"trees": 0}
    kind, body = store.read(tree)
    if kind != "tree":
        raise Refused("not a tree: " + tree)
    counts["trees"] += 1
    for mode, name, name_id in parse_tree(body):
        path = prefix + name
        if mode == "40000":
            flatten(store, name_id, path + "/", out, counts)
        else:
            out[path] = (mode, name_id)
    return out, counts


def blob_id(data):
    return object_name("blob", data)


def compare_worktree(root, flat, problems):
    """Every worktree entry, except .git and .venv at its root, against the tree."""
    seen, changed, extra, directories, special = set(), [], [], 0, []
    stack = [""]
    tracked_dirs = {posixpath.dirname(path) for path in flat}
    tracked_dirs = {"/".join(path.split("/")[:index]) for path in tracked_dirs
                    for index in range(1, len(path.split("/")) + 1) if path}
    untracked_dirs = []
    while stack:
        rel = stack.pop()
        directory = root + "/" + rel if rel else root
        for name in sorted(os.listdir(directory)):
            sub = rel + "/" + name if rel else name
            if not rel and name in (".git", ".venv"):
                continue
            path = root + "/" + sub
            info = os.lstat(path)
            if name == ".DS_Store" or name == "__pycache__" or name.endswith((".pyc", ".pyo")):
                problems.append({"rule": "HYGIENE", "path": sub})
            if stat.S_ISDIR(info.st_mode):
                directories += 1
                if sub not in tracked_dirs:
                    untracked_dirs.append(sub)
                stack.append(sub)
                continue
            if stat.S_ISLNK(info.st_mode):
                mode, data = "120000", os.fsencode(os.readlink(path))
            elif stat.S_ISREG(info.st_mode):
                if info.st_nlink != 1:
                    problems.append({"rule": "MULTI-LINK", "path": sub})
                data, _, _, _ = common.read_bytes(path)
                mode = "100755" if info.st_mode & stat.S_IXUSR else "100644"
            else:
                special.append(sub)
                continue
            seen.add(sub)
            if sub not in flat:
                extra.append(sub)
            elif flat[sub] != (mode, blob_id(data)):
                changed.append(sub)
    missing = sorted(set(flat) - seen)
    return {"entries": len(seen), "links": sum(1 for path in seen if flat.get(path, ("",))[0] == "120000"),
            "directories": directories, "missing": missing[:50], "missing_count": len(missing),
            "extra": extra[:50], "extra_count": len(extra), "changed": changed[:50], "changed_count": len(changed),
            "special": special, "untracked_directories": untracked_dirs[:50]}


def parse_index(path):
    raw, binding, _, _ = common.read_bytes(path)
    if raw[:4] != b"DIRC":
        raise Refused("index signature")
    version, count = struct.unpack(">II", raw[4:12])
    checksum_valid = hashlib.sha1(raw[:-20]).digest() == raw[-20:]
    entries, position, previous = {}, 12, b""
    flags_seen = {"stage": 0, "assume_valid": 0, "extended": 0, "skip_worktree": 0, "intent_to_add": 0}
    for _ in range(count):
        start = position
        fields = struct.unpack(">10I", raw[position:position + 40])
        name = raw[position + 40:position + 60].hex()
        flags = struct.unpack(">H", raw[position + 60:position + 62])[0]
        position += 62
        extended = 0
        if flags & 0x4000:
            flags_seen["extended"] += 1
            if version >= 3:
                extended = struct.unpack(">H", raw[position:position + 2])[0]
                position += 2
        if flags & 0x8000:
            flags_seen["assume_valid"] += 1
        if (flags >> 12) & 3:
            flags_seen["stage"] += 1
        if extended & 0x4000:
            flags_seen["skip_worktree"] += 1
        if extended & 0x2000:
            flags_seen["intent_to_add"] += 1
        if version == 4:
            strip, shift = 0, 0
            while True:
                byte = raw[position]
                position += 1
                strip |= (byte & 0x7F) << shift
                shift += 7
                if not byte & 0x80:
                    break
            nul = raw.index(b"\0", position)
            path_bytes = previous[:len(previous) - strip] + raw[position:nul]
            position = nul + 1
        else:
            nul = raw.index(b"\0", position)
            path_bytes = raw[position:nul]
            length = nul - start + 1
            position = start + ((length + 7) // 8) * 8
        previous = path_bytes
        mode = fields[6]
        entries[path_bytes.decode("utf-8", "surrogateescape")] = ("%o" % mode, name, fields[9])
    extensions = {}
    tree_root = None
    while position < len(raw) - 20:
        signature = raw[position:position + 4].decode("latin-1")
        size = struct.unpack(">I", raw[position + 4:position + 8])[0]
        data = raw[position + 8:position + 8 + size]
        extensions[signature] = size
        if signature == "TREE":
            nul = data.index(b"\0")
            newline = data.index(b"\n", nul)
            count_text, subtrees = data[nul + 1:newline].decode("ascii").split(" ")
            root_count = int(count_text)
            tree_root = {"path": data[:nul].decode(), "entry_count": root_count, "subtrees": int(subtrees),
                         "tree": data[newline + 1:newline + 21].hex() if root_count >= 0 else None}
        position += 8 + size
    return {"binding": binding, "version": version, "count": count, "checksum_valid": checksum_valid,
            "flags": flags_seen, "extensions": extensions, "tree_root": tree_root}, entries


def main():
    common.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--mh-commit", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--named", action="append", default=[])
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    root = args.worktree
    began = time.monotonic()
    out = {"schema": "w3.p36.plan-review-001.s04/1", "pid": os.getpid(),
           "boot_before": common.sysctl_text("kern.bootsessionuuid")}
    checks = common.Checks()

    # 1. Source inventory.
    problems = []
    inventory, multi = source_inventory(root, problems)
    raw = common.canonical_json(inventory)
    expected_raw, expected_binding, _, _ = common.read_bytes(args.expected)
    expected = common.strict_loads(expected_raw)
    out["source_inventory"] = {
        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "files": len(inventory["files"]),
        "file_bytes": sum(row["size_bytes"] for row in inventory["files"].values()),
        "expected": expected_binding, "bytes_equal": raw == expected_raw,
        "missing": sorted(set(expected["files"]) - set(inventory["files"])),
        "added": sorted(set(inventory["files"]) - set(expected["files"])),
        "changed": sorted(rel for rel in set(expected["files"]) & set(inventory["files"])
                          if expected["files"][rel] != inventory["files"][rel]),
        "problems": problems, "multi_link_files": multi,
        "supervisor_files_in_set": all(rel in inventory["files"] for rel in (
            "prototypes/__init__.py", "prototypes/static_tray_v01/__init__.py",
            "prototypes/static_tray_v01/supervisor.py", "prototypes/static_tray_v01/supervisor_darwin_v01.py")),
        "observer_binding": inventory["files"].get("prototypes/static_tray_v01/current_host_observation_v02.py")}
    checks.add("G-01", raw == expected_raw and not problems and not multi,
               "the source inventory recomputes byte-identically, with no link, .DS_Store, bytecode or multi-link file",
               {"sha256": out["source_inventory"]["sha256"], "files": len(inventory["files"])})

    # 2. HEAD from the Git files.
    dotgit = root + "/.git"
    info = os.lstat(dotgit)
    text, _, _, _ = common.read_bytes(dotgit)
    gitdir = text.decode().strip()[len("gitdir: "):]
    common_raw, _, _, _ = common.read_bytes(gitdir + "/commondir")
    common_dir = posixpath.normpath(gitdir + "/" + common_raw.decode().strip())
    head_raw, _, _, _ = common.read_bytes(gitdir + "/HEAD")
    head = head_raw.decode().strip()
    ref = head[5:] if head.startswith("ref: ") else None
    backlink, _, _, _ = common.read_bytes(gitdir + "/gitdir")
    per_worktree_ref = os.path.lexists(gitdir + "/" + ref) if ref else None
    loose_ref = common_dir + "/" + ref if ref else None
    loose_value = common.read_bytes(loose_ref)[0].decode().strip() if ref and os.path.lexists(loose_ref) else None
    packed_entries = []
    if os.path.lexists(common_dir + "/packed-refs"):
        packed_raw, _, _, _ = common.read_bytes(common_dir + "/packed-refs")
        packed_entries = [line.split(" ")[0] for line in packed_raw.decode().splitlines()
                          if line.endswith(" " + ref)] if ref else []
    out["head"] = {"dotgit_is_file": stat.S_ISREG(info.st_mode), "gitdir": gitdir,
                   "gitdir_canonical": os.path.realpath(gitdir) == gitdir, "common_dir": common_dir,
                   "common_dir_canonical": os.path.realpath(common_dir) == common_dir, "head": head, "ref": ref,
                   "per_worktree_ref_present": per_worktree_ref, "loose_ref_value": loose_value,
                   "packed_refs_entries": packed_entries,
                   "backlink": backlink.decode().strip(), "backlink_names_worktree": backlink.decode().strip() == dotgit}
    checks.add("G-02", loose_value == args.commit and not per_worktree_ref and not packed_entries
               and out["head"]["gitdir_canonical"] and out["head"]["common_dir_canonical"]
               and out["head"]["backlink_names_worktree"],
               "HEAD resolves to B through the common directory's loose ref only; the Git directories are canonical "
               "and the backlink names the worktree's .git", out["head"])

    # 3. Commit B and its tree.
    store = Store(common_dir + "/objects")
    out["store"] = {"alternates": store.alternates,
                    "packs": [{key: value for key, value in pack.items() if key != "data"} for pack in store.packs]}
    kind, body = store.read(args.commit)
    commit = parse_commit(body)
    commit["stored"] = store.last_where
    out["commit"] = commit
    checks.add("G-03", kind == "commit" and commit["tree"] == args.tree and not store.alternates
               and all(pack["trailer_equals_index"] and pack["content_sha1_equals_trailer"] for pack in store.packs),
               "commit B's name recomputes from its bytes and it names tree T; the pack verifies; no alternates",
               {"tree": commit["tree"], "parents": commit["parents"], "stored": commit["stored"]})
    flat, counts = flatten(store, args.tree)
    modes = {}
    for mode, _ in flat.values():
        modes[mode] = modes.get(mode, 0) + 1
    missing_objects = sorted(path for path, (mode, name) in flat.items() if mode != "160000" and not store.has(name))
    out["tree"] = {"trees": counts["trees"], "entries": len(flat), "modes": modes,
                   "blobs_missing_from_store": missing_objects[:20]}

    # 4. The worktree against the tree.
    hygiene = []
    worktree = compare_worktree(root, flat, hygiene)
    worktree["hygiene"] = hygiene
    out["worktree"] = worktree
    checks.add("G-04", worktree["missing_count"] == 0 and worktree["extra_count"] == 0
               and worktree["changed_count"] == 0 and not worktree["special"] and not hygiene
               and not worktree["untracked_directories"],
               "apart from .git and .venv at its root, the worktree equals tree T exactly: nothing missing, extra or "
               "changed, no special, multi-link, bytecode or .DS_Store entry, no untracked directory",
               {key: worktree[key] for key in ("entries", "links", "directories", "missing_count", "extra_count",
                                                "changed_count")})

    # 5. The index.
    index, index_entries = parse_index(gitdir + "/index")
    differing = sorted(path for path in set(index_entries) | set(flat)
                       if path not in index_entries or path not in flat
                       or (index_entries[path][0], index_entries[path][1]) != flat[path])
    size_mismatch = []
    for path, (mode, name, size) in index_entries.items():
        if mode == "100644" or mode == "100755":
            actual = os.lstat(root + "/" + path).st_size
            if actual & 0xFFFFFFFF != size:
                size_mismatch.append(path)
    index["differs_from_tree"] = differing[:50]
    index["size_mismatch"] = size_mismatch[:50]
    out["index"] = index
    checks.add("G-05", index["checksum_valid"] and not differing and not size_mismatch
               and not any(index["flags"][key] for key in ("stage", "assume_valid", "skip_worktree", "intent_to_add"))
               and index["tree_root"] is not None and index["tree_root"]["tree"] == args.tree,
               "the index has a valid checksum, equals the tree by path, mode and blob, its cached sizes equal the "
               "files, it has no conflict stage, assume-valid, skip-worktree or intent-to-add entry, and its TREE root "
               "is T", {"count": index["count"], "version": index["version"], "flags": index["flags"],
                        "extensions": index["extensions"], "tree_root": index["tree_root"]})

    # 6. From C to B: the first-parent chain and the tree difference.
    chain, current = [], args.commit
    for _ in range(20):
        if current == args.mh_commit:
            break
        kind, body = store.read(current)
        parsed = parse_commit(body)
        chain.append({"commit": current, "parents": parsed["parents"], "subject": parsed["subject"],
                      "committer_time": parsed["committer_time"]})
        current = parsed["parents"][0]
    reached = current == args.mh_commit
    kind, body = store.read(args.mh_commit)
    mh_tree = parse_commit(body)["tree"]
    mh_flat, _ = flatten(store, mh_tree)
    added = sorted(set(flat) - set(mh_flat))
    removed = sorted(set(mh_flat) - set(flat))
    changed = sorted(path for path in set(flat) & set(mh_flat) if flat[path] != mh_flat[path])
    touched = added + removed + changed
    source_set = set(inventory["files"])

    def in_source(path):
        return path in source_set or any(path.startswith(tree + "/") for tree in SOURCE_TREES) or \
            path in SOURCE_FILES or path in SOURCE_OPTIONAL
    groups = {}
    for path in touched:
        key = ("docs/engineering/localized-repair-c271/macos-qualification-p35/"
               if path.startswith("docs/engineering/localized-repair-c271/macos-qualification-p35/") else
               "docs/engineering/localized-repair-c271/macos-routine-p36/"
               if path.startswith("docs/engineering/localized-repair-c271/macos-routine-p36/") else path)
        groups[key] = groups.get(key, 0) + 1
    out["c_to_b"] = {"chain": chain, "reached_c": reached, "c_tree": mh_tree, "added": len(added),
                     "removed": len(removed), "changed": len(changed), "outside_docs": [p for p in touched
                                                                                      if not p.startswith("docs/")],
                     "in_source_set": [p for p in touched if in_source(p)], "groups": groups,
                     "changed_paths": changed}
    checks.add("G-06", reached and not out["c_to_b"]["outside_docs"] and not out["c_to_b"]["in_source_set"],
               "B reaches MH's commit C by first parents, and every path that changes from C to B lies under docs/ and "
               "outside the observer's source set", {"commits": [row["commit"][:8] for row in chain],
                                                       "added": len(added), "removed": len(removed),
                                                       "changed": len(changed)})

    # 7. Named files: blob at B and at C, and the worktree bytes.
    named = {}
    for rel in args.named:
        data, binding, _, info = common.read_bytes(root + "/" + rel)
        named[rel] = {"blob_at_b": flat.get(rel, (None, None))[1], "blob_at_c": mh_flat.get(rel, (None, None))[1],
                      "mode_at_b": flat.get(rel, (None, None))[0], "worktree_blob": blob_id(data),
                      "nlink": info.st_nlink, **binding}
    out["named"] = named
    checks.add("G-07", all(row["blob_at_b"] == row["worktree_blob"] == row["blob_at_c"] for row in named.values()),
               "each named file's worktree bytes are its blob at B, which is its blob at C",
               {rel: row["blob_at_b"] for rel, row in named.items()})

    out["store"]["stats"] = store.stats
    out["elapsed_s"] = round(time.monotonic() - began, 3)
    out["boot_after"] = common.sysctl_text("kern.bootsessionuuid")
    out["checks"] = checks.rows
    out["summary"] = checks.summary()
    out["refused_process_events"] = list(common.REFUSED_EVENTS)
    digest = common.write_output(args.output, out, labels)
    print(labels(str({"summary": out["summary"], "source_sha256": out["source_inventory"]["sha256"],
                      "elapsed_s": out["elapsed_s"], "output_sha256": digest})))


if __name__ == "__main__":
    main()
