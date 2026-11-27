"""Compare two commits' trees by reading Git's object files directly (read only; starts no Git).

Usage: python3 -I -S -B git_tree_diff.py GITDIR COMMIT_A COMMIT_B OUT.json [PREFIX ...]
Reads loose objects with zlib and packed objects through the pack index (version 2), resolving
OFS_DELTA and REF_DELTA chains. Writes the paths whose blob or mode differ, and those only in one tree.
"""
import hashlib, json, mmap, os, struct, sys, zlib

gitdir = sys.argv[1]
commit_a, commit_b, destination = sys.argv[2:5]
prefixes = tuple(sys.argv[5:])
packdir = os.path.join(gitdir, "objects", "pack")
packs = []
for name in sorted(os.listdir(packdir)):
    if name.endswith(".idx"):
        raw = open(os.path.join(packdir, name), "rb").read()
        assert raw[:4] == b"\377tOc" and struct.unpack(">I", raw[4:8])[0] == 2
        fanout = struct.unpack(">256I", raw[8:8 + 1024])
        count = fanout[-1]
        names_at = 8 + 1024
        crc_at = names_at + 20 * count
        offsets_at = crc_at + 4 * count
        large_at = offsets_at + 4 * count
        fh = open(os.path.join(packdir, name[:-4] + ".pack"), "rb")
        data = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        packs.append({"idx": raw, "fanout": fanout, "count": count, "names_at": names_at,
                      "offsets_at": offsets_at, "large_at": large_at, "data": data})


def pack_lookup(oid):
    key = bytes.fromhex(oid)
    for pack in packs:
        lo = pack["fanout"][key[0] - 1] if key[0] else 0
        hi = pack["fanout"][key[0]]
        raw = pack["idx"]
        while lo < hi:
            mid = (lo + hi) // 2
            here = raw[pack["names_at"] + 20 * mid:pack["names_at"] + 20 * mid + 20]
            if here < key:
                lo = mid + 1
            elif here > key:
                hi = mid
            else:
                (offset,) = struct.unpack(">I", raw[pack["offsets_at"] + 4 * mid:pack["offsets_at"] + 4 * mid + 4])
                if offset & 0x80000000:
                    index = offset & 0x7FFFFFFF
                    (offset,) = struct.unpack(">Q", raw[pack["large_at"] + 8 * index:pack["large_at"] + 8 * index + 8])
                return pack, offset
    return None


def inflate(data, start):
    decompressor = zlib.decompressobj()
    out, position = [], start
    while not decompressor.eof:
        chunk = data[position:position + 65536]
        if not chunk:
            break
        out.append(decompressor.decompress(chunk))
        position += len(chunk)
    return b"".join(out)


TYPES = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}


def apply_delta(base, delta):
    def varint(position):
        value, shift = 0, 0
        while True:
            byte = delta[position]; position += 1
            value |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                return value, position
    source_size, position = varint(0)
    target_size, position = varint(position)
    assert source_size == len(base)
    out = bytearray()
    while position < len(delta):
        command = delta[position]; position += 1
        if command & 0x80:
            offset = size = 0
            for bit in range(4):
                if command & (1 << bit):
                    offset |= delta[position] << (8 * bit); position += 1
            for bit in range(3):
                if command & (1 << (4 + bit)):
                    size |= delta[position] << (8 * bit); position += 1
            if size == 0:
                size = 0x10000
            out += base[offset:offset + size]
        elif command:
            out += delta[position:position + command]; position += command
        else:
            raise ValueError("delta command 0")
    assert len(out) == target_size
    return bytes(out)


def read_packed(pack, offset):
    data = pack["data"]
    byte = data[offset]; position = offset + 1
    kind = (byte >> 4) & 7
    while byte & 0x80:
        byte = data[position]; position += 1
    if kind in TYPES:
        return TYPES[kind], inflate(data, position)
    if kind == 6:
        byte = data[position]; position += 1
        distance = byte & 0x7F
        while byte & 0x80:
            byte = data[position]; position += 1
            distance = ((distance + 1) << 7) | (byte & 0x7F)
        base_kind, base = read_packed(pack, offset - distance)
        return base_kind, apply_delta(base, inflate(data, position))
    if kind == 7:
        base_oid = bytes(data[position:position + 20]).hex(); position += 20
        base_kind, base = read_object(base_oid)
        return base_kind, apply_delta(base, inflate(data, position))
    raise ValueError("unknown pack type %d" % kind)


def read_object(oid):
    path = os.path.join(gitdir, "objects", oid[:2], oid[2:])
    if os.path.exists(path):
        raw = zlib.decompress(open(path, "rb").read())
        header, body = raw.split(b"\0", 1)
        kind = header.split(b" ")[0].decode()
    else:
        found = pack_lookup(oid)
        if found is None:
            raise KeyError(oid)
        kind, body = read_packed(*found)
    check = hashlib.sha1(kind.encode() + b" " + str(len(body)).encode() + b"\0" + body).hexdigest()
    assert check == oid, (oid, check)
    return kind, body


def tree_of(commit):
    kind, body = read_object(commit)
    assert kind == "commit"
    return body.split(b"\n", 1)[0].split(b" ")[1].decode()


def walk(tree, prefix=""):
    kind, body = read_object(tree)
    assert kind == "tree"
    position = 0
    while position < len(body):
        space = body.index(b" ", position)
        nul = body.index(b"\0", space)
        mode, name = body[position:space].decode(), body[space + 1:nul].decode()
        oid = body[nul + 1:nul + 21].hex()
        position = nul + 21
        path = prefix + name
        if mode == "40000":
            if not prefixes or any(p.startswith(path + "/") or path.startswith(p.rstrip("/")) for p in prefixes):
                yield from walk(oid, path + "/")
        else:
            if not prefixes or any(path.startswith(p) for p in prefixes):
                yield path, (mode, oid)


tree_a, tree_b = tree_of(commit_a), tree_of(commit_b)
a = dict(walk(tree_a))
b = dict(walk(tree_b))
result = {"commit_a": commit_a, "tree_a": tree_a, "commit_b": commit_b, "tree_b": tree_b, "prefixes": list(prefixes),
          "files_a": len(a), "files_b": len(b),
          "changed": sorted(p for p in a.keys() & b.keys() if a[p] != b[p]),
          "only_a": sorted(a.keys() - b.keys()), "only_b": sorted(b.keys() - a.keys())}
with open(destination, "x") as fh:
    json.dump(result, fh, indent=1)
    fh.write("\n")
print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 60 else v[:60] + ["...%d" % len(v)]) for k, v in result.items()}, indent=1))
