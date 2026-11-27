"""HOST review 001, script h03: the source inventory, HEAD, commit C's tree, the index and the worktree,
read from the files alone. No Git is started.

Run as: <worktree>/.venv/bin/python -I -S -B h03_source_and_head.py --host H --output OUT
"""
import argparse
import hashlib
import importlib.util
import json
import os
import stat
import struct
import zlib

HERE = os.path.dirname(os.path.realpath(__file__))
_spec = importlib.util.spec_from_file_location("h_common", HERE + "/h_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

# The source set, as W3-OBSERVER Q9 defines it (the 0.1.0 trees and files plus the 0.2.0 roles).
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
CHECKS = []


def check(cid, what, ok, **details):
    CHECKS.append({"id": cid, "what": what, "passed": bool(ok), **({"details": details} if details else {})})


def source_inventory(root):
    found, problems = set(), []
    for tree in SOURCE_TREES:
        for base, dirs, files in os.walk(root + "/" + tree, followlinks=False):
            for name in dirs + files:
                path = os.path.join(base, name)
                rel = os.path.relpath(path, root)
                info = os.lstat(path)
                if name in ("__pycache__", ".DS_Store") or name.endswith((".pyc", ".pyo")):
                    problems.append(rel)
                if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                    problems.append("not a plain file or directory: " + rel)
                elif stat.S_ISREG(info.st_mode):
                    found.add(rel)
    for rel in SOURCE_FILES:
        info = os.lstat(root + "/" + rel)
        if not stat.S_ISREG(info.st_mode):
            problems.append("role is not a regular file: " + rel)
        found.add(rel)
    found.update(rel for rel in SOURCE_OPTIONAL if os.path.lexists(root + "/" + rel))
    files = {}
    for rel in sorted(found):
        _, facts, _ = C.read_bound(root + "/" + rel)
        files[rel] = C.binding(facts)
        if facts["nlink"] != 1:
            problems.append("more than one link: " + rel)
    return {"schema": "ontokin.current-host-readback-source/0.2.0", "files": files}, problems


class Objects:
    """Loose objects and version-2 pack indexes, with OFS_DELTA and REF_DELTA resolution."""

    def __init__(self, directory):
        self.directory, self.packs = directory, []
        for name in sorted(os.listdir(directory + "/pack")):
            if name.endswith(".idx"):
                raw = C.read_bound(directory + "/pack/" + name, keep=True)[0]
                if raw[:4] != b"\xfftOc" or struct.unpack(">I", raw[4:8])[0] != 2:
                    raise ValueError("unsupported pack index " + name)
                fanout = struct.unpack(">256I", raw[8:1032])
                count = fanout[255]
                self.packs.append({"raw": raw, "fanout": fanout, "count": count, "shas": 1032,
                                   "offsets": 1032 + 24 * count, "large": 1032 + 28 * count,
                                   "pack": directory + "/pack/" + name[:-4] + ".pack"})
        self.loose = self.packed = 0

    def _find(self, pack, key):
        raw, first = pack["raw"], key[0]
        low, high = (pack["fanout"][first - 1] if first else 0), pack["fanout"][first]
        while low < high:
            mid = (low + high) // 2
            sha = raw[pack["shas"] + 20 * mid:pack["shas"] + 20 * mid + 20]
            if sha < key:
                low = mid + 1
            elif sha > key:
                high = mid
            else:
                offset = struct.unpack(">I", raw[pack["offsets"] + 4 * mid:pack["offsets"] + 4 * mid + 4])[0]
                if offset & 0x80000000:
                    index = offset & 0x7FFFFFFF
                    offset = struct.unpack(">Q", raw[pack["large"] + 8 * index:pack["large"] + 8 * index + 8])[0]
                return offset
        return None

    @staticmethod
    def _inflate(stream, position):
        stream.seek(position)
        engine, parts = zlib.decompressobj(), []
        while not engine.eof:
            chunk = stream.read(1 << 16)
            if not chunk:
                raise ValueError("truncated pack entry")
            parts.append(engine.decompress(chunk))
        return b"".join(parts)

    @staticmethod
    def _delta(base, delta):
        index = 0

        def varint():
            nonlocal index
            value = shift = 0
            while True:
                byte = delta[index]
                index += 1
                value |= (byte & 0x7F) << shift
                shift += 7
                if not byte & 0x80:
                    return value
        if varint() != len(base):
            raise ValueError("delta base size differs")
        size, out = varint(), bytearray()
        while index < len(delta):
            op = delta[index]
            index += 1
            if op & 0x80:
                offset = length = 0
                for bit in range(4):
                    if op & (1 << bit):
                        offset |= delta[index] << (8 * bit)
                        index += 1
                for bit in range(3):
                    if op & (1 << (4 + bit)):
                        length |= delta[index] << (8 * bit)
                        index += 1
                out += base[offset:offset + (length or 0x10000)]
            elif op:
                out += delta[index:index + op]
                index += op
            else:
                raise ValueError("reserved delta opcode")
        if len(out) != size:
            raise ValueError("delta result size differs")
        return bytes(out)

    def _entry(self, stream, offset):
        stream.seek(offset)
        byte = stream.read(1)[0]
        kind = (byte >> 4) & 7
        while byte & 0x80:
            byte = stream.read(1)[0]
        if kind in (1, 2, 3, 4):
            return {1: "commit", 2: "tree", 3: "blob", 4: "tag"}[kind], self._inflate(stream, stream.tell())
        if kind == 6:
            byte = stream.read(1)[0]
            distance = byte & 0x7F
            while byte & 0x80:
                byte = stream.read(1)[0]
                distance = ((distance + 1) << 7) | (byte & 0x7F)
            position = stream.tell()
            base_kind, base = self._entry(stream, offset - distance)
            return base_kind, self._delta(base, self._inflate(stream, position))
        if kind == 7:
            base_sha = stream.read(20).hex()
            position = stream.tell()
            base_kind, base = self.read(base_sha)
            return base_kind, self._delta(base, self._inflate(stream, position))
        raise ValueError("unsupported pack entry type %d" % kind)

    def read(self, sha):
        loose = self.directory + "/" + sha[:2] + "/" + sha[2:]
        if os.path.lexists(loose):
            data = zlib.decompress(C.read_bound(loose, keep=True)[0])
            header, _, body = data.partition(b"\0")
            kind = header.split(b" ")[0].decode()
            self.loose += 1
        else:
            key = bytes.fromhex(sha)
            for pack in self.packs:
                offset = self._find(pack, key)
                if offset is not None:
                    with open(pack["pack"], "rb") as stream:
                        kind, body = self._entry(stream, offset)
                    self.packed += 1
                    break
            else:
                raise KeyError(sha)
        if hashlib.sha1(kind.encode() + b" " + str(len(body)).encode() + b"\0" + body).hexdigest() != sha:
            raise ValueError("object digest differs: " + sha)
        return kind, body


def tree_entries(objects, sha, prefix=""):
    kind, body = objects.read(sha)
    if kind != "tree":
        raise ValueError("not a tree: " + sha)
    index = 0
    while index < len(body):
        space = body.index(b" ", index)
        nul = body.index(b"\0", space)
        mode, name = body[index:space].decode(), body[space + 1:nul].decode("utf-8", "surrogateescape")
        child = body[nul + 1:nul + 21].hex()
        index = nul + 21
        if mode == "40000":
            yield from tree_entries(objects, child, prefix + name + "/")
        else:
            yield prefix + name, int(mode, 8), child


def parse_index(raw):
    if raw[:4] != b"DIRC":
        raise ValueError("not an index")
    version, count = struct.unpack(">II", raw[4:12])
    offset, previous, entries, stages = 12, b"", {}, 0
    for _ in range(count):
        fields = struct.unpack(">10I", raw[offset:offset + 40])
        sha = raw[offset + 40:offset + 60].hex()
        flags = struct.unpack(">H", raw[offset + 60:offset + 62])[0]
        position = offset + 62 + (2 if version >= 3 and flags & 0x4000 else 0)
        if version == 4:
            byte = raw[position]
            position += 1
            strip = byte & 0x7F
            while byte & 0x80:
                byte = raw[position]
                position += 1
                strip = ((strip + 1) << 7) | (byte & 0x7F)
            end = raw.index(b"\0", position)
            name = previous[:len(previous) - strip] + raw[position:end]
            offset = end + 1
        else:
            end = raw.index(b"\0", position)
            name = raw[position:end]
            fixed = position - offset
            offset += ((fixed + len(name) + 8) // 8) * 8
        previous = name
        stage = (flags >> 12) & 3
        stages += stage != 0
        entries[name.decode("utf-8", "surrogateescape")] = {
            "mode": fields[6], "sha": sha, "size": fields[9], "mtime": (fields[2], fields[3]), "stage": stage}
    return version, entries, stages


def blob_sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = {"script": "h03_source_and_head.py", "process": C.process_facts()}
    host = json.loads(C.read_bound(args.host, keep=True)[0])
    source = host["source"]
    root = source["root"]

    # The source inventory, recomputed.
    frozen_raw, frozen_facts, _ = C.read_bound(source["inventory"]["path"], keep=True)
    doc, problems = source_inventory(root)
    raw = C.canonical(doc)
    out["source_inventory"] = {"files": len(doc["files"]), "sha256": C.sha256_bytes(raw), "size_bytes": len(raw),
                               "problems": problems}
    check("S1", "the recomputed source inventory is byte-identical to the frozen one, digest 95abd300...",
          raw == frozen_raw and C.sha256_bytes(raw) == source["inventory"]["sha256"], files=len(doc["files"]))
    check("S2", "no bytecode, .DS_Store, link or special file in the source trees, and every source file has one link",
          not problems, problems=problems[:20])
    check("S3", "the observer and the macOS lock are bound by the source inventory as HOST records them",
          doc["files"]["prototypes/static_tray_v01/current_host_observation_v02.py"]
          == {k: host["observer"][k] for k in ("sha256", "size_bytes", "mode")}
          and doc["files"]["tools/native-reader-verification-macos-arm64-cp312.lock"]
          == {k: host["python"]["lock"][k] for k in ("sha256", "size_bytes", "mode")})

    # HEAD from the Git files, statically.
    files = {}

    def read(path):
        data, facts, _ = C.read_bound(path, keep=True)
        files[path] = C.binding(facts)
        return data
    dotgit = read(root + "/.git").decode().strip()
    gitdir = os.path.normpath(os.path.join(root, dotgit[len("gitdir: "):])) if dotgit.startswith("gitdir: ") else None
    common = os.path.normpath(os.path.join(gitdir, read(gitdir + "/commondir").decode().strip()))
    head_text = read(gitdir + "/HEAD").decode().strip()
    ref = head_text[len("ref: "):] if head_text.startswith("ref: ") else None
    commit = None
    for base in (gitdir, common):
        if ref and os.path.lexists(base + "/" + ref):
            commit = read(base + "/" + ref).decode().strip()
            break
    head = {"gitdir": gitdir, "common_dir": common, "ref": ref, "commit": commit,
            "files": {p: files[p] for p in sorted(files)}}
    out["head"] = head
    check("H1", "HOST.source.head equals HEAD read from the Git files (gitdir, common dir, ref, commit, file bindings)",
          head == source["head"], recomputed=head)
    check("H2", "gitdir and common dir have no linked component", not C.linked_components(gitdir)
          and not C.linked_components(common))

    # Commit C and its tree, from the object store.
    objects = Objects(common + "/objects")
    kind, body = objects.read(commit)
    lines = body.split(b"\n\n", 1)[0].decode("utf-8", "replace").splitlines()
    tree = [line.split(" ", 1)[1] for line in lines if line.startswith("tree ")]
    parents = [line.split(" ", 1)[1] for line in lines if line.startswith("parent ")]
    committed = [line.rsplit(" ", 2)[-2] for line in lines if line.startswith("committer ")]
    out["commit"] = {"sha": commit, "kind": kind, "tree": tree, "parents": parents,
                     "committer_epoch_s": committed}
    check("T1", "commit C is a commit object whose tree is HOST.source.tree (ea10cd94...)",
          kind == "commit" and tree == [source["tree"]] and commit == source["commit"])
    tracked = {path: (mode, sha) for path, mode, sha in tree_entries(objects, tree[0])}
    out["tree"] = {"entries": len(tracked), "objects_read": {"loose": objects.loose, "packed": objects.packed}}

    # The index against the tree, and the worktree against the index.
    index_raw, index_facts, _ = C.read_bound(gitdir + "/index", keep=True)
    version, entries, stages = parse_index(index_raw)
    out["index"] = {"version": version, "entries": len(entries), "conflict_stages": stages,
                    "mtime_ns": index_facts["mtime_ns"], "sha256": index_facts["sha256"]}
    differ = sorted(set(tracked) ^ set(entries)) + sorted(p for p in set(tracked) & set(entries)
                                                          if (entries[p]["mode"], entries[p]["sha"]) != tracked[p])
    check("T2", "the index equals commit C's tree exactly (paths, modes, blobs) and has no conflict stage",
          not differ and not stages, differ=differ[:20])
    modified, newest = [], (0, None)
    for path, entry in sorted(entries.items()):
        full = root + "/" + path
        try:
            info = os.lstat(full)
        except FileNotFoundError:
            modified.append(path + " (missing)")
            continue
        if info.st_mtime_ns > newest[0]:
            newest = (info.st_mtime_ns, path)
        mode = entry["mode"]
        if stat.S_ISLNK(mode):
            data = os.readlink(full).encode() if stat.S_ISLNK(info.st_mode) else None
        elif stat.S_IFMT(mode) == 0o160000:
            continue
        else:
            data = C.read_bound(full, keep=True)[0] if stat.S_ISREG(info.st_mode) else None
            if data is not None and bool(info.st_mode & 0o100) != (mode & 0o777 == 0o755):
                modified.append(path + " (mode)")
        if data is None or blob_sha(data) != entry["sha"]:
            modified.append(path)
    out["worktree"] = {"tracked_checked": len(entries), "modified": modified[:50],
                       "newest_tracked_mtime_ns": newest[0], "newest_tracked_path": newest[1]}
    check("T3", "every tracked worktree file equals its index blob (content and executable bit)", not modified,
          modified=modified[:20])
    untracked, special = [], []
    for base, dirs, names in os.walk(root, followlinks=False):
        rel_base = os.path.relpath(base, root)
        if rel_base == ".":
            dirs[:] = [d for d in dirs if d != ".venv"]
        for name in dirs + names:
            rel = os.path.normpath(os.path.join(rel_base, name))
            full = os.path.join(base, name)
            if name in ("__pycache__", ".DS_Store") or name.endswith((".pyc", ".pyo")):
                special.append(rel)
            if name in dirs and not os.path.islink(full):
                continue
            if rel != ".git" and rel not in entries:
                untracked.append(rel)
    out["worktree"]["untracked_outside_venv"] = untracked[:50]
    out["worktree"]["bytecode_or_ds_store"] = special[:50]
    check("T4", "no untracked file outside .venv, and no bytecode or .DS_Store anywhere outside .venv",
          not untracked and not special, untracked=untracked[:20], special=special[:20])
    check("T5", "no tracked file is newer than the index file", newest[0] <= index_facts["mtime_ns"],
          newest=newest, index_mtime_ns=index_facts["mtime_ns"])
    out["checks"] = CHECKS
    out["failed"] = [c["id"] for c in CHECKS if not c["passed"]]
    out["refused_events"] = C.REFUSED_EVENTS
    C.write_new(args.output, out)
    print(json.dumps({"failed": out["failed"], "checks": len(CHECKS), "source": out["source_inventory"]["sha256"],
                      "tree_entries": out["tree"]["entries"], "index": out["index"]["entries"]}))


if __name__ == "__main__":
    main()
