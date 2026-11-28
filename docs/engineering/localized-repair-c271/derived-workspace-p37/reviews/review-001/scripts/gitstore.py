"""Read-only access to a Git object store and index files, without starting Git (W3, C271-P37 S7).

Loose objects (zlib) and version-2 pack files with their version-2 index files are read; offset and
reference deltas are applied. Index files of versions 2 to 4 are parsed. Nothing here writes.
"""
import hashlib
import mmap
import os
import struct
import zlib


class Store:
    def __init__(self, objects_dir):
        self.objects = objects_dir
        self.packs = []
        pack_dir = os.path.join(objects_dir, "pack")
        for name in sorted(os.listdir(pack_dir)) if os.path.isdir(pack_dir) else []:
            if name.endswith(".idx"):
                self.packs.append(Pack(os.path.join(pack_dir, name), os.path.join(pack_dir, name[:-4] + ".pack")))
        self.cache = {}

    def read(self, oid):
        """(kind, data) of an object, verified against its name."""
        if oid in self.cache:
            return self.cache[oid]
        path = os.path.join(self.objects, oid[:2], oid[2:])
        if os.path.exists(path):
            with open(path, "rb") as stream:
                raw = zlib.decompress(stream.read())
            header, _, data = raw.partition(b"\0")
            kind, size = header.split(b" ")
            kind = kind.decode()
            if int(size) != len(data):
                raise ValueError("loose object size differs: " + oid)
        else:
            for pack in self.packs:
                found = pack.read(oid, self)
                if found is not None:
                    kind, data = found
                    break
            else:
                raise KeyError(oid)
        check = hashlib.sha1(kind.encode() + b" " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if check != oid:
            raise ValueError("object digest differs: " + oid)
        result = (kind, data)
        if kind != "blob":
            self.cache[oid] = result
        return result

    def commit(self, oid):
        kind, data = self.read(oid)
        if kind != "commit":
            raise ValueError("not a commit: " + oid)
        headers, _, message = data.partition(b"\n\n")
        fields = {"parents": []}
        for line in headers.split(b"\n"):
            key, _, value = line.partition(b" ")
            if key == b"tree":
                fields["tree"] = value.decode()
            elif key == b"parent":
                fields["parents"].append(value.decode())
        fields["message_first_line"] = message.split(b"\n", 1)[0].decode("utf-8", "replace")
        return fields

    def tree(self, oid):
        kind, data = self.read(oid)
        if kind != "tree":
            raise ValueError("not a tree: " + oid)
        entries, position = [], 0
        while position < len(data):
            space = data.index(b" ", position)
            mode = data[position:space].decode()
            nul = data.index(b"\0", space)
            name = data[space + 1:nul].decode("utf-8", "surrogateescape")
            entry_oid = data[nul + 1:nul + 21].hex()
            entries.append((mode, name, entry_oid))
            position = nul + 21
        return entries

    def flatten(self, oid, prefix=""):
        """path -> (mode, oid) for every non-tree entry under a tree."""
        rows = {}
        for mode, name, entry_oid in self.tree(oid):
            path = prefix + name
            if mode == "40000":
                rows.update(self.flatten(entry_oid, path + "/"))
            else:
                rows[path] = (mode, entry_oid)
        return rows

    def changed(self, left, right, prefix=""):
        """Paths whose entries differ between two trees, descending only into differing subtrees."""
        a = {name: (mode, oid) for mode, name, oid in self.tree(left)} if left else {}
        b = {name: (mode, oid) for mode, name, oid in self.tree(right)} if right else {}
        rows = []
        for name in sorted(set(a) | set(b)):
            ea, eb = a.get(name), b.get(name)
            if ea == eb:
                continue
            path = prefix + name
            tree_a = ea[1] if ea and ea[0] == "40000" else None
            tree_b = eb[1] if eb and eb[0] == "40000" else None
            if tree_a or tree_b:
                rows.extend(self.changed(tree_a, tree_b, path + "/"))
                if ea and not tree_a:
                    rows.append((path, ea, None))
                if eb and not tree_b:
                    rows.append((path, None, eb))
            else:
                rows.append((path, ea, eb))
        return rows


class Pack:
    TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}

    def __init__(self, idx_path, pack_path):
        with open(idx_path, "rb") as stream:
            raw = stream.read()
        if raw[:4] != b"\xfftOc" or struct.unpack(">I", raw[4:8])[0] != 2:
            raise ValueError("unsupported pack index: " + idx_path)
        fanout = struct.unpack(">256I", raw[8:8 + 1024])
        count = fanout[255]
        names_at = 8 + 1024
        self.names = [raw[names_at + 20 * i:names_at + 20 * i + 20] for i in range(count)]
        offsets_at = names_at + 20 * count + 4 * count
        small = struct.unpack(">%dI" % count, raw[offsets_at:offsets_at + 4 * count])
        large_at = offsets_at + 4 * count
        self.offsets = {}
        for i, value in enumerate(small):
            if value & 0x80000000:
                index = value & 0x7FFFFFFF
                value = struct.unpack(">Q", raw[large_at + 8 * index:large_at + 8 * index + 8])[0]
            self.offsets[self.names[i].hex()] = value
        self.pack_path = pack_path
        self._data = None

    @property
    def data(self):
        if self._data is None:
            stream = open(self.pack_path, "rb")
            self._data = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
            stream.close()
        return self._data

    def read(self, oid, store):
        offset = self.offsets.get(oid)
        if offset is None:
            return None
        return self.at(offset, store)

    def at(self, offset, store):
        data = self.data
        byte = data[offset]
        kind = (byte >> 4) & 7
        size = byte & 15
        shift, position = 4, offset + 1
        while byte & 0x80:
            byte = data[position]
            position += 1
            size |= (byte & 0x7F) << shift
            shift += 7
        if kind in self.TYPES:
            return self.TYPES[kind], self.inflate(position, size)
        if kind == 6:
            byte = data[position]
            position += 1
            base = byte & 0x7F
            while byte & 0x80:
                byte = data[position]
                position += 1
                base = ((base + 1) << 7) | (byte & 0x7F)
            base_kind, base_data = self.at(offset - base, store)
        elif kind == 7:
            base_oid = data[position:position + 20].hex()
            position += 20
            base_kind, base_data = store.read(base_oid)
        else:
            raise ValueError("unsupported pack entry type %d" % kind)
        return base_kind, apply_delta(base_data, self.inflate(position, size))

    def inflate(self, position, size):
        decompressor = zlib.decompressobj()
        out = bytearray()
        while not decompressor.eof:
            piece = self.data[position:position + 65536]
            if not piece:
                break
            out += decompressor.decompress(piece)
            position += 65536
        if len(out) != size:
            raise ValueError("pack entry size differs")
        return bytes(out)


def _varint(data, position):
    value, shift = 0, 0
    while True:
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return value, position


def apply_delta(base, delta):
    source_size, position = _varint(delta, 0)
    target_size, position = _varint(delta, position)
    if source_size != len(base):
        raise ValueError("delta base size differs")
    out = bytearray()
    while position < len(delta):
        op = delta[position]
        position += 1
        if op & 0x80:
            offset = size = 0
            for bit in range(4):
                if op & (1 << bit):
                    offset |= delta[position] << (8 * bit)
                    position += 1
            for bit in range(3):
                if op & (1 << (4 + bit)):
                    size |= delta[position] << (8 * bit)
                    position += 1
            if size == 0:
                size = 0x10000
            out += base[offset:offset + size]
        elif op:
            out += delta[position:position + op]
            position += op
        else:
            raise ValueError("reserved delta opcode")
    if len(out) != target_size:
        raise ValueError("delta target size differs")
    return bytes(out)


def blob_id(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def read_index(path):
    """(version, entries) of a Git index file: entries[path] = dict(stat fields, mode, oid, stage, flags)."""
    with open(path, "rb") as stream:
        raw = stream.read()
    if raw[:4] != b"DIRC":
        raise ValueError("not an index file")
    version, count = struct.unpack(">II", raw[4:12])
    if version not in (2, 3, 4):
        raise ValueError("unsupported index version")
    if hashlib.sha1(raw[:-20]).digest() != raw[-20:]:
        raise ValueError("index checksum differs")
    offset, previous, entries = 12, b"", {}
    for _ in range(count):
        fields = struct.unpack(">10I", raw[offset:offset + 40])
        oid = raw[offset + 40:offset + 60].hex()
        (flags,) = struct.unpack(">H", raw[offset + 60:offset + 62])
        extended = 0
        position = offset + 62
        if flags & 0x4000:
            (extended,) = struct.unpack(">H", raw[position:position + 2])
            position += 2
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
            offset += (end - offset + 8) // 8 * 8
        previous = name
        ctime_s, ctime_ns, mtime_s, mtime_ns, dev, ino, mode, uid, gid, size = fields
        entries[name.decode("utf-8", "surrogateescape")] = {
            "ctime": (ctime_s, ctime_ns), "mtime": (mtime_s, mtime_ns), "dev": dev, "ino": ino, "mode": mode,
            "uid": uid, "gid": gid, "size": size, "oid": oid, "stage": (flags >> 12) & 3,
            "assume_valid": bool(flags & 0x8000), "skip_worktree": bool(extended & 0x4000),
            "intent_to_add": bool(extended & 0x2000)}
    return version, entries
