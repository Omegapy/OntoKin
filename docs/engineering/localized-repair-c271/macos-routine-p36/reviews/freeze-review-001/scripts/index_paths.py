"""List the paths of a Git index file (read only), and those outside the driver's copied set.

Usage: python3 -I -S -B index_paths.py INDEX OUT.json FREEZE   (FREEZE supplies the path labels)
Reads Git's index bytes directly; starts no Git. Supports index versions 2, 3 and 4 with SHA-1 names.
"""
import json, os, struct, sys

SOURCE_DIRS = ("ontokin", "tests", "tools", "docs", "examples", "fixtures", "schemas", "prototypes", "packaging",
               ".github", ".agents", "TRDs")
ROOT_FILES = ("pyproject.toml", "README.md", "AGENTS.md", "GOAL.md", "STATUS.md", "CHATGPT-START-HERE.md", "ROLE.md",
              "LOCAL-START-HERE.md", "CLAUDE.md", "LICENSE", "LICENSE-CODE", "LICENSE-DOCS", "LICENSING.md", "NOTICE",
              ".gitignore", ".gitattributes", ".lfsconfig")


def entries(raw):
    assert raw[:4] == b"DIRC", "not an index"
    version, count = struct.unpack(">II", raw[4:12])
    assert version in (2, 3, 4), version
    offset, previous, out = 12, b"", []
    for _ in range(count):
        start = offset
        fields = struct.unpack(">IIIIIIIIII", raw[offset:offset + 40])
        mode = fields[6]
        size = fields[9]
        offset += 40
        oid = raw[offset:offset + 20].hex()
        offset += 20
        (flags,) = struct.unpack(">H", raw[offset:offset + 2])
        offset += 2
        if version >= 3 and flags & 0x4000:
            offset += 2
        if version == 4:
            strip, shift = 0, 0
            # varint as Git's offset encoding
            byte = raw[offset]; offset += 1
            strip = byte & 0x7F
            while byte & 0x80:
                byte = raw[offset]; offset += 1
                strip = ((strip + 1) << 7) | (byte & 0x7F)
            end = raw.index(b"\0", offset)
            name = previous[:len(previous) - strip] + raw[offset:end]
            offset = end + 1
        else:
            end = raw.index(b"\0", offset)
            name = raw[offset:end]
            length = end - start
            offset = start + ((length + 8) & ~7)
        previous = name
        out.append({"path": name.decode("utf-8"), "mode": oct(mode), "size": size, "oid": oid,
                    "stage": (flags >> 12) & 3})
    return version, count, out


def main():
    index, destination = sys.argv[1], sys.argv[2]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from labels import labeller
    label = labeller(sys.argv[3])
    raw = open(index, "rb").read()
    version, count, rows = entries(raw)
    outside = [row for row in rows
               if row["path"].split("/")[0] not in SOURCE_DIRS and row["path"] not in ROOT_FILES]
    result = {"index": label(index), "version": version, "count": count, "parsed": len(rows),
              "total_tracked_bytes": sum(row["size"] for row in rows),
              "outside_driver_copy": outside,
              "symlinks": [row["path"] for row in rows if row["mode"] == oct(0o120000)]}
    with open(destination, "x") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(json.dumps({k: result[k] for k in ("version", "count", "parsed", "total_tracked_bytes")}))
    print(json.dumps(outside, indent=1))


main()
