"""W2 of C271-P36 (gate MR, stage S4): a static reader of Git's files.

It never starts Git or any other process, and it writes exactly one absent output file.
It establishes, from the files of the worktree's Git directory and object store:

* HEAD: the worktree's .git file, its Git directory, the common directory, the ref and its commit;
* the commit object (its name recomputed from its bytes), its tree, parents, times and subject;
* every tree object of that commit, recursively, read from loose objects and the pack
  (pack index version 2, OFS_DELTA and REF_DELTA resolved, every object name recomputed);
* the worktree against that tree: every file and link by blob name and mode, apart from the
  root's .git file and .venv directory; missing, extra and changed paths, special files,
  multi-link files, .DS_Store, bytecode and empty directories;
* the worktree's index against the tree (version, checksum, stages, flags, TREE extension);
* the first-parent history from the commit back to a comparison commit, with the paths that
  each commit changed, and the tree difference between the two commits;
* named paths: their blob at the commit, and the worktree file's SHA-256, size and mode.

Usage, with the framework interpreter under -I -S -B:

    w2p_git_static.py --worktree W --commit B --tree T --compare-commit C --output OUT
                      [--path RELATIVE ...]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import stat
import struct
import sys
import time
import zlib

# ---------------------------------------------------------------------------
# No process creation: refuse every process-creation event of the runtime
# ---------------------------------------------------------------------------

PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn",
                            "os.fork", "os.forkpty", "pty.spawn", "os.startfile"))
LIBC_STARTS = re.compile(r"_?(fork|vfork|execv?[elp]*|posix_spawnp?|system|popen)")
REFUSED_EVENTS = []


def _audit(event, args):
    if event in PROCESS_EVENTS:
        REFUSED_EVENTS.append(event)
        raise RuntimeError("Process creation refused by the W2 audit hook: " + event)
    if event == "ctypes.dlsym" and len(args) > 1 and isinstance(args[1], str) and LIBC_STARTS.fullmatch(args[1]):
        REFUSED_EVENTS.append(event + ":" + args[1])
        raise RuntimeError("ctypes lookup of a process-creation function refused: " + args[1])


sys.addaudithook(_audit)


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _boot():
    import ctypes
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    function = libc.sysctlbyname
    function.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                         ctypes.c_size_t]
    function.restype = ctypes.c_int
    size = ctypes.c_size_t(64)
    buffer = ctypes.create_string_buffer(64)
    if function(b"kern.bootsessionuuid", buffer, ctypes.byref(size), None, 0) != 0:
        raise RuntimeError("sysctlbyname kern.bootsessionuuid failed")
    return buffer.raw[:size.value].rstrip(b"\0").decode("ascii")


# ---------------------------------------------------------------------------
# Object store: loose objects and version-2 pack indexes
# ---------------------------------------------------------------------------

TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}


def _object_name(kind, data):
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(data)).encode("ascii") + b"\0" + data).digest()


def _varint(buffer, index):
    value = shift = 0
    while True:
        byte = buffer[index]
        index += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, index


def apply_delta(base, delta):
    source_size, index = _varint(delta, 0)
    target_size, index = _varint(delta, index)
    if source_size != len(base):
        raise ValueError("Delta base size differs from its base")
    out = bytearray()
    length = len(delta)
    while index < length:
        op = delta[index]
        index += 1
        if op & 0x80:
            offset = size = 0
            for bit, shift in ((0x01, 0), (0x02, 8), (0x04, 16), (0x08, 24)):
                if op & bit:
                    offset |= delta[index] << shift
                    index += 1
            for bit, shift in ((0x10, 0), (0x20, 8), (0x40, 16)):
                if op & bit:
                    size |= delta[index] << shift
                    index += 1
            if size == 0:
                size = 0x10000
            if offset + size > len(base):
                raise ValueError("Delta copy escapes its base")
            out += base[offset:offset + size]
        elif op:
            out += delta[index:index + op]
            index += op
        else:
            raise ValueError("Delta opcode 0 is reserved")
    if len(out) != target_size:
        raise ValueError("Delta result size differs from its header")
    return bytes(out)


class Pack:
    def __init__(self, idx_path, pack_path, verify_pack):
        with open(idx_path, "rb") as handle:
            raw = handle.read()
        if raw[:4] != b"\xfftOc" or struct.unpack(">I", raw[4:8])[0] != 2:
            raise ValueError("Unsupported pack index: " + idx_path)
        fanout = struct.unpack(">256I", raw[8:8 + 1024])
        count = fanout[255]
        names_at = 8 + 1024
        crc_at = names_at + 20 * count
        offsets_at = crc_at + 4 * count
        large_at = offsets_at + 4 * count
        small = struct.unpack(">%dI" % count, raw[offsets_at:offsets_at + 4 * count])
        large_count = sum(1 for value in small if value & 0x80000000)
        large = struct.unpack(">%dQ" % large_count, raw[large_at:large_at + 8 * large_count]) if large_count else ()
        trailer_at = large_at + 8 * large_count
        if len(raw) != trailer_at + 40:
            raise ValueError("Pack index length differs from its layout")
        self.idx_path, self.pack_path = idx_path, pack_path
        self.pack_checksum = raw[trailer_at:trailer_at + 20]
        self.idx_checksum_valid = hashlib.sha1(raw[:-20]).digest() == raw[-20:]
        names = raw[names_at:crc_at]
        self.offsets = {}
        previous, ordered = b"", True
        for index in range(count):
            name = names[20 * index:20 * index + 20]
            if index and name <= previous:
                ordered = False
            previous = name
            value = small[index]
            if value & 0x80000000:
                value = large[value & 0x7FFFFFFF]
            self.offsets[name] = value
        fanout_ok = all(fanout[byte] == sum(1 for name in self.offsets if name[0] <= byte) for byte in (0, 127, 255))
        self.count, self.large_offsets, self.names_ordered, self.fanout_ok = count, large_count, ordered, fanout_ok
        self.handle = open(pack_path, "rb")
        header = self.handle.read(12)
        if header[:4] != b"PACK":
            raise ValueError("Not a pack file: " + pack_path)
        self.version, self.pack_objects = struct.unpack(">II", header[4:12])
        size = os.fstat(self.handle.fileno()).st_size
        self.handle.seek(size - 20)
        self.trailer = self.handle.read(20)
        self.trailer_matches_index = self.trailer == self.pack_checksum
        self.size_bytes = size
        self.content_checksum_valid = None
        if verify_pack:
            digest, remaining = hashlib.sha1(), size - 20
            self.handle.seek(0)
            while remaining:
                block = self.handle.read(min(8 * 1024 * 1024, remaining))
                if not block:
                    raise ValueError("Pack shorter than its size")
                digest.update(block)
                remaining -= len(block)
            self.content_checksum_valid = digest.digest() == self.trailer
        self.cache, self.cached_bytes = {}, 0

    def _remember(self, offset, value):
        if len(value[1]) > 4 * 1024 * 1024:
            return
        if self.cached_bytes > 256 * 1024 * 1024:
            self.cache, self.cached_bytes = {}, 0
        self.cache[offset] = value
        self.cached_bytes += len(value[1])

    def _header(self, offset):
        self.handle.seek(offset)
        head = self.handle.read(64)
        index = 0
        byte = head[index]
        index += 1
        kind = (byte >> 4) & 7
        size = byte & 15
        shift = 4
        while byte & 0x80:
            byte = head[index]
            index += 1
            size |= (byte & 0x7F) << shift
            shift += 7
        base = None
        if kind == 6:
            byte = head[index]
            index += 1
            relative = byte & 0x7F
            while byte & 0x80:
                byte = head[index]
                index += 1
                relative = ((relative + 1) << 7) | (byte & 0x7F)
            base = offset - relative
            if base <= 0:
                raise ValueError("OFS_DELTA base escapes the pack")
        elif kind == 7:
            base = head[index:index + 20]
            index += 20
        elif kind not in TYPES:
            raise ValueError("Unsupported pack object type %d" % kind)
        return kind, size, offset + index, base

    def _inflate(self, start, size):
        self.handle.seek(start)
        inflater, parts, total = zlib.decompressobj(), [], 0
        while not inflater.eof:
            block = self.handle.read(65536)
            if not block:
                raise ValueError("Truncated pack object")
            data = inflater.decompress(block)
            total += len(data)
            if total > size:
                raise ValueError("Pack object exceeds its header size")
            parts.append(data)
        data = b"".join(parts)
        if len(data) != size:
            raise ValueError("Pack object size differs from its header")
        return data

    def object_at(self, offset, store):
        chain, current = [], offset
        while True:
            if current in self.cache:
                kind, data = self.cache[current]
                break
            code, size, start, base = self._header(current)
            if code in TYPES:
                kind, data = TYPES[code], self._inflate(start, size)
                self._remember(current, (kind, data))
                break
            chain.append((current, self._inflate(start, size)))
            if code == 6:
                current = base
            else:
                kind, data = store.raw(base)
                break
        for position, delta in reversed(chain):
            data = apply_delta(data, delta)
            self._remember(position, (kind, data))
        return kind, data


class Store:
    def __init__(self, objects, verify_pack):
        self.objects = objects
        self.packs = []
        pack_dir = objects + "/pack"
        for name in sorted(os.listdir(pack_dir)):
            if name.endswith(".idx"):
                stem = name[:-4]
                self.packs.append(Pack(pack_dir + "/" + name, pack_dir + "/" + stem + ".pack", verify_pack))
        self.reads = {"loose": 0, "packed": 0}
        self.memo = {}

    def raw(self, name):
        if name in self.memo:
            return self.memo[name]
        hexname = name.hex()
        path = self.objects + "/" + hexname[:2] + "/" + hexname[2:]
        if os.path.lexists(path):
            with open(path, "rb") as handle:
                data = zlib.decompress(handle.read())
            header, _, body = data.partition(b"\0")
            kind, _, size = header.partition(b" ")
            kind = kind.decode("ascii")
            if int(size) != len(body):
                raise ValueError("Loose object size differs: " + hexname)
            self.reads["loose"] += 1
        else:
            for pack in self.packs:
                if name in pack.offsets:
                    kind, body = pack.object_at(pack.offsets[name], self)
                    self.reads["packed"] += 1
                    break
            else:
                raise KeyError("Object not found: " + hexname)
        if _object_name(kind, body) != name:
            raise ValueError("Object name does not recompute from its bytes: " + hexname)
        if kind in ("commit", "tree"):
            self.memo[name] = (kind, body)
        return kind, body

    def where(self, name):
        hexname = name.hex()
        if os.path.lexists(self.objects + "/" + hexname[:2] + "/" + hexname[2:]):
            return "loose"
        return "packed" if any(name in pack.offsets for pack in self.packs) else "absent"


def parse_commit(data):
    header, _, message = data.partition(b"\n\n")
    tree = re.search(rb"^tree ([0-9a-f]{40})$", header, re.M)
    parents = re.findall(rb"^parent ([0-9a-f]{40})$", header, re.M)
    committer = re.search(rb"^committer (.*) (\d+) ([+-]\d{4})$", header, re.M)
    author = re.search(rb"^author (.*) (\d+) ([+-]\d{4})$", header, re.M)
    return {"tree": tree.group(1).decode("ascii"), "parents": [value.decode("ascii") for value in parents],
            "committed_at_utc": datetime.fromtimestamp(int(committer.group(2)), timezone.utc).isoformat(),
            "authored_at_utc": datetime.fromtimestamp(int(author.group(2)), timezone.utc).isoformat(),
            "signed": b"\ngpgsig " in b"\n" + header or b"\ngpgsig-sha256 " in b"\n" + header,
            "subject": message.split(b"\n", 1)[0].decode("utf-8", "replace")}


def parse_tree(data):
    entries, index = [], 0
    while index < len(data):
        space = data.index(b" ", index)
        nul = data.index(b"\0", space)
        entries.append((data[index:space].decode("ascii"), data[space + 1:nul], data[nul + 1:nul + 21]))
        index = nul + 21
    return entries


def walk_tree(store, tree_hex):
    files, trees, stack = {}, {}, [(b"", bytes.fromhex(tree_hex))]
    while stack:
        prefix, name = stack.pop()
        kind, data = store.raw(name)
        if kind != "tree":
            raise ValueError("Expected a tree object: " + name.hex())
        trees[prefix.rstrip(b"/")] = name.hex()
        for mode, entry, sha in parse_tree(data):
            path = prefix + entry
            if mode == "40000":
                stack.append((path + b"/", sha))
            else:
                files[path] = (mode, sha.hex())
    return files, trees


# ---------------------------------------------------------------------------
# Worktree and index
# ---------------------------------------------------------------------------

def _blob_of_file(path, size):
    digest = hashlib.sha1(b"blob " + str(size).encode("ascii") + b"\0")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        total = 0
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            total += len(block)
            digest.update(block)
    finally:
        os.close(fd)
    if total != size:
        raise ValueError("File changed while hashed: " + os.fsdecode(path))
    return digest.hexdigest()


def walk_worktree(root):
    root_b = os.fsencode(root)
    files, directories, problems = {}, [], {"special": [], "ds_store": [], "bytecode": [], "multilink": [],
                                            "empty_directories": []}
    skipped, stack = [], [b""]
    while stack:
        relative = stack.pop()
        directory = root_b + b"/" + relative if relative else root_b
        with os.scandir(directory) as iterator:
            names = sorted(entry.name for entry in iterator)
        for name in names:
            rel = relative + b"/" + name if relative else name
            if not relative and name in (b".git", b".venv"):
                skipped.append(os.fsdecode(name))
                continue
            path = root_b + b"/" + rel
            info = os.lstat(path)
            if name == b".DS_Store":
                problems["ds_store"].append(os.fsdecode(rel))
            if name == b"__pycache__" or name.endswith((b".pyc", b".pyo")):
                problems["bytecode"].append(os.fsdecode(rel))
            if stat.S_ISLNK(info.st_mode):
                target = os.readlink(path)
                files[rel] = ("120000", _object_name("blob", target).hex())
            elif stat.S_ISDIR(info.st_mode):
                directories.append(rel)
                stack.append(rel)
            elif stat.S_ISREG(info.st_mode):
                mode = "100755" if info.st_mode & stat.S_IXUSR else "100644"
                files[rel] = (mode, _blob_of_file(path, info.st_size))
                if info.st_nlink != 1:
                    problems["multilink"].append(os.fsdecode(rel))
            else:
                problems["special"].append(os.fsdecode(rel))
    holding = set()
    for path in files:
        parts = path.split(b"/")
        for index in range(1, len(parts)):
            holding.add(b"/".join(parts[:index]))
    problems["empty_directories"] = sorted(os.fsdecode(path) for path in directories if path not in holding)
    return files, len(directories), skipped, problems


def parse_index(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    result = {"path": path, "size_bytes": len(raw), "checksum_valid": hashlib.sha1(raw[:-20]).digest() == raw[-20:]}
    if raw[:4] != b"DIRC":
        raise ValueError("Not an index file")
    version, count = struct.unpack(">II", raw[4:12])
    result.update(version=version, entries=count)
    index, entries, previous = 12, {}, b""
    staged = assume_valid = extended = skip_worktree = intent_to_add = 0
    for _ in range(count):
        start = index
        fields = struct.unpack(">10I", raw[index:index + 40])
        sha = raw[index + 40:index + 60]
        flags = struct.unpack(">H", raw[index + 60:index + 62])[0]
        index += 62
        extra = 0
        if version >= 3 and flags & 0x4000:
            extra = struct.unpack(">H", raw[index:index + 2])[0]
            index += 2
            extended += 1
            skip_worktree += 1 if extra & 0x4000 else 0
            intent_to_add += 1 if extra & 0x2000 else 0
        if version == 4:
            strip, index = _varint_index_v4(raw, index)
            nul = raw.index(b"\0", index)
            name = previous[:len(previous) - strip] + raw[index:nul]
            index = nul + 1
        else:
            nul = raw.index(b"\0", index)
            name = raw[index:nul]
            index = start + (((index - start) + len(name) + 8) // 8) * 8
        stage = (flags >> 12) & 3
        staged += 1 if stage else 0
        assume_valid += 1 if flags & 0x8000 else 0
        entries[(name, stage)] = ("%o" % fields[6], sha.hex(), fields[9])
        previous = name
    extensions, tree_root = [], None
    while index < len(raw) - 20:
        signature = raw[index:index + 4]
        size = struct.unpack(">I", raw[index + 4:index + 8])[0]
        data = raw[index + 8:index + 8 + size]
        extensions.append({"signature": signature.decode("ascii", "replace"), "size_bytes": size})
        if signature == b"TREE":
            nul = data.index(b"\0")
            line_end = data.index(b"\n", nul)
            entry_count, subtrees = data[nul + 1:line_end].split(b" ")
            root = {"path": data[:nul].decode("utf-8", "replace"), "entry_count": int(entry_count),
                    "subtrees": int(subtrees)}
            if int(entry_count) >= 0:
                root["tree"] = data[line_end + 1:line_end + 21].hex()
            tree_root = root
        index += 8 + size
    result.update(nonzero_stages=staged, assume_valid=assume_valid, extended_entries=extended,
                  skip_worktree=skip_worktree, intent_to_add=intent_to_add, extensions=extensions,
                  tree_extension_root=tree_root, consumed_exactly=index == len(raw) - 20)
    return result, entries


def _varint_index_v4(raw, index):
    byte = raw[index]
    index += 1
    value = byte & 0x7F
    while byte & 0x80:
        byte = raw[index]
        index += 1
        value = ((value + 1) << 7) | (byte & 0x7F)
    return value, index


# ---------------------------------------------------------------------------
# HEAD from the Git files
# ---------------------------------------------------------------------------

def _text(path, maximum=65536):
    with open(path, "rb") as handle:
        raw = handle.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("File too large: " + path)
    return raw.decode("utf-8")


def _sha256_binding(path):
    info = os.lstat(path)
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return {"sha256": digest.hexdigest(), "size_bytes": info.st_size, "mode": "0o%03o" % stat.S_IMODE(info.st_mode),
            "links": info.st_nlink}


def read_head(worktree):
    dotgit = worktree + "/.git"
    info = os.lstat(dotgit)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Expected a .git file in a linked worktree")
    text = _text(dotgit).strip()
    if not text.startswith("gitdir: "):
        raise ValueError("Unsupported .git file")
    gitdir = text[len("gitdir: "):]
    common_text = _text(gitdir + "/commondir").strip()
    common = os.path.normpath(os.path.join(gitdir, common_text))
    head_text = _text(gitdir + "/HEAD").strip()
    record = {"dotgit": {"path": dotgit, "text": text, **_sha256_binding(dotgit)}, "gitdir": gitdir,
              "commondir_text": common_text, "common_dir": common, "head_text": head_text,
              "backlink": _text(gitdir + "/gitdir").strip(),
              "per_worktree_refs": sorted(os.listdir(gitdir + "/refs")) if os.path.isdir(gitdir + "/refs") else None,
              "alternates_present": os.path.lexists(common + "/objects/info/alternates")}
    if not head_text.startswith("ref: "):
        raise ValueError("Detached HEAD is not expected here")
    ref = head_text[len("ref: "):]
    record["ref"] = ref
    loose = None
    for base in (gitdir, common):
        if os.path.lexists(base + "/" + ref):
            loose = {"path": base + "/" + ref, "commit": _text(base + "/" + ref).strip()}
            break
    packed = None
    if os.path.lexists(common + "/packed-refs"):
        for line in _text(common + "/packed-refs", 64 * 1024 * 1024).splitlines():
            parts = line.split(" ")
            if len(parts) == 2 and parts[1] == ref:
                packed = parts[0]
    record.update(loose_ref=loose, packed_ref=packed,
                  commit=loose["commit"] if loose else packed)
    return record


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def first_parent_history(store, start, stop, limit=500):
    rows, current = [], start
    for _ in range(limit):
        if current == stop:
            return rows, True
        kind, data = store.raw(bytes.fromhex(current))
        commit = parse_commit(data)
        rows.append({"commit": current, **commit})
        if not commit["parents"]:
            return rows, False
        current = commit["parents"][0]
    return rows, False


def tree_difference(old, new):
    added = sorted(path for path in new if path not in old)
    removed = sorted(path for path in old if path not in new)
    changed = sorted(path for path in new if path in old and new[path] != old[path])
    return added, removed, changed


def main(argv=None):
    if not (sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode):
        raise SystemExit("Run under -I -S -B")
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--compare-commit", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--no-pack-checksum", action="store_true")
    args = parser.parse_args(argv)
    began, monotonic = _utc(), time.monotonic()
    boot_before = _boot()
    out_fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    result = {"schema": "ontokin.c271.p36-w2-git-static/1", "script": os.path.realpath(__file__),
              "script_sha256": _sha256_binding(os.path.realpath(__file__))["sha256"], "pid": os.getpid(),
              "started_at_utc": began, "boot_before": boot_before, "starts": "none: no Git, no process"}
    head = read_head(args.worktree)
    result["head"] = head
    result["head_is_commit"] = head["commit"] == args.commit
    store = Store(head["common_dir"] + "/objects", verify_pack=not args.no_pack_checksum)
    result["packs"] = [{"index": pack.idx_path, "pack": pack.pack_path, "objects": pack.count,
                        "pack_header_objects": pack.pack_objects, "pack_version": pack.version,
                        "pack_size_bytes": pack.size_bytes, "large_offsets": pack.large_offsets,
                        "names_ordered": pack.names_ordered, "fanout_ok": pack.fanout_ok,
                        "index_checksum_valid": pack.idx_checksum_valid,
                        "trailer_matches_index": pack.trailer_matches_index,
                        "content_checksum_valid": pack.content_checksum_valid} for pack in store.packs]
    commit_name = bytes.fromhex(args.commit)
    _, commit_data = store.raw(commit_name)
    commit = parse_commit(commit_data)
    result["commit"] = {"name": args.commit, "location": store.where(commit_name), **commit,
                        "tree_is_expected": commit["tree"] == args.tree}
    tree_files, tree_dirs = walk_tree(store, commit["tree"])
    modes = {}
    for mode, _ in tree_files.values():
        modes[mode] = modes.get(mode, 0) + 1
    result["tree"] = {"name": commit["tree"], "trees": len(tree_dirs), "entries": len(tree_files), "modes": modes}
    work_files, work_dirs, skipped, problems = walk_worktree(args.worktree)
    missing = sorted(path for path in tree_files if path not in work_files)
    extra = sorted(path for path in work_files if path not in tree_files)
    changed = sorted(path for path in tree_files if path in work_files and tree_files[path] != work_files[path])
    result["worktree"] = {"root": args.worktree, "skipped_at_root": skipped, "files_and_links": len(work_files),
                          "links": sum(1 for mode, _ in work_files.values() if mode == "120000"),
                          "directories": work_dirs, "missing": [os.fsdecode(path) for path in missing],
                          "extra": [os.fsdecode(path) for path in extra],
                          "changed": [os.fsdecode(path) for path in changed], **problems,
                          "equals_tree": not missing and not extra and not changed}
    index_record, index_entries = parse_index(head["gitdir"] + "/index")
    stage0 = {name: value for (name, stage), value in index_entries.items() if stage == 0}
    index_vs_tree = {"missing": sorted(os.fsdecode(path) for path in tree_files if path not in stage0),
                     "extra": sorted(os.fsdecode(path) for path in stage0 if path not in tree_files),
                     "changed": sorted(os.fsdecode(path) for path in stage0 if path in tree_files
                                       and stage0[path][:2] != tree_files[path])}
    size_differs = 0
    for path, (_mode, _sha, size) in stage0.items():
        full = os.fsencode(args.worktree) + b"/" + path
        if os.path.lexists(full) and not os.path.islink(full) and os.lstat(full).st_size != size:
            size_differs += 1
    index_record["equals_tree"] = not any(index_vs_tree.values())
    index_record["versus_tree"] = index_vs_tree
    index_record["cached_size_differs_from_worktree"] = size_differs
    index_record["tree_extension_root_is_tree"] = bool(index_record["tree_extension_root"]) and \
        index_record["tree_extension_root"].get("tree") == commit["tree"]
    result["index"] = index_record
    history, reached = first_parent_history(store, args.commit, args.compare_commit)
    compare_name = bytes.fromhex(args.compare_commit)
    _, compare_data = store.raw(compare_name)
    compare = parse_commit(compare_data)
    compare_files, _ = walk_tree(store, compare["tree"])
    added, removed, changed_paths = tree_difference(compare_files, tree_files)
    rows = []
    for row in history:
        files_here, _ = walk_tree(store, row["tree"])
        parent_files, _ = walk_tree(store, store_parent_tree(store, row["parents"][0]))
        a, r, c = tree_difference(parent_files, files_here)
        rows.append({"commit": row["commit"], "parents": row["parents"], "subject": row["subject"],
                     "committed_at_utc": row["committed_at_utc"],
                     "added": [os.fsdecode(path) for path in a], "removed": [os.fsdecode(path) for path in r],
                     "changed": [os.fsdecode(path) for path in c]})
    result["comparison"] = {"commit": args.compare_commit, "tree": compare["tree"], "subject": compare["subject"],
                            "committed_at_utc": compare["committed_at_utc"],
                            "reached_by_first_parent": reached, "first_parent_commits": rows,
                            "tree_difference": {"added": [os.fsdecode(path) for path in added],
                                                "removed": [os.fsdecode(path) for path in removed],
                                                "changed": [os.fsdecode(path) for path in changed_paths]}}
    named = {}
    for rel in args.path:
        key = os.fsencode(rel)
        entry = tree_files.get(key)
        full = args.worktree + "/" + rel
        binding = _sha256_binding(full) if os.path.lexists(full) else None
        named[rel] = {"tree_entry": {"mode": entry[0], "blob": entry[1]} if entry else None,
                      "worktree": binding,
                      "worktree_blob": work_files.get(key, (None, None))[1],
                      "equals_blob": bool(entry) and work_files.get(key) == entry,
                      "at_comparison_commit": ({"mode": compare_files[key][0], "blob": compare_files[key][1]}
                                               if key in compare_files else None)}
    result["named_paths"] = named
    result["object_reads"] = dict(store.reads)
    result["boot_after"] = _boot()
    result["finished_at_utc"] = _utc()
    result["elapsed_s"] = round(time.monotonic() - monotonic, 3)
    result["refused_process_events"] = list(REFUSED_EVENTS)
    raw = json.dumps(result, indent=1, sort_keys=True).encode("utf-8") + b"\n"
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(out_fd, raw[offset:])
        os.fsync(out_fd)
    finally:
        os.close(out_fd)
    summary = {"head_is_commit": result["head_is_commit"], "tree_is_expected": result["commit"]["tree_is_expected"],
               "worktree_equals_tree": result["worktree"]["equals_tree"], "index_equals_tree": index_record["equals_tree"],
               "tree_entries": len(tree_files), "trees": len(tree_dirs), "reached_comparison": reached,
               "boot_before": boot_before, "boot_after": result["boot_after"], "elapsed_s": result["elapsed_s"],
               "output": args.output}
    sys.stdout.write(json.dumps(summary, sort_keys=True) + "\n")
    return 0


def store_parent_tree(store, parent):
    _, data = store.raw(bytes.fromhex(parent))
    return parse_commit(data)["tree"]


if __name__ == "__main__":
    raise SystemExit(main())
