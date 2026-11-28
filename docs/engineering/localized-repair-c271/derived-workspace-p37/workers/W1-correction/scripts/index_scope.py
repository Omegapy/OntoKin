"""Read-only: list a Git index's entries and classify them against the driver's copied set.

Usage: python3 -I -S -B index_scope.py <check_local.py> <index file> <output json>
It parses the driver's constants with ast (no import) and the index file directly (no Git start).
"""
import ast
import hashlib
import json
import struct
import sys


def constants(path):
    tree = ast.parse(open(path, "rb").read())
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ("SOURCE_DIRS", "ROOT_FILES", "IGNORED"):
                found[name] = ast.literal_eval(node.value)
    return found


def entries(path):
    raw = open(path, "rb").read()
    signature, version, count = struct.unpack(">4sLL", raw[:12])
    assert signature == b"DIRC", signature
    assert version in (2, 3), version
    offset, rows = 12, []
    for _ in range(count):
        start = offset
        mode = struct.unpack(">L", raw[offset + 24:offset + 28])[0]
        oid = raw[offset + 40:offset + 60].hex()
        flags = struct.unpack(">H", raw[offset + 60:offset + 62])[0]
        offset += 62
        if version == 3 and flags & 0x4000:
            offset += 2
        end = raw.index(b"\0", offset)
        name = raw[offset:end].decode("utf-8", "surrogateescape")
        stage = (flags >> 12) & 0x3
        length = end - start
        offset = start + ((length + 8) // 8) * 8
        rows.append({"path": name, "mode": oct(mode), "oid": oid, "stage": stage})
    return version, count, rows, hashlib.sha256(raw).hexdigest()


def main():
    source, index, output = sys.argv[1:4]
    c = constants(source)
    dirs, files, ignored_names = c["SOURCE_DIRS"], c["ROOT_FILES"], c["IGNORED"]

    def ignored(name):
        return name in ignored_names or name == ".env" or name.startswith(".env.") or name.endswith((".pyc", ".pyo"))

    def copied(name):
        parts = name.split("/")
        return (parts[0] in dirs or name in files) and not any(ignored(part) for part in parts)

    folded_dirs = {d.casefold(): d for d in dirs}
    folded_files = {f.casefold(): f for f in files}
    version, count, rows, digest = entries(index)
    outside = [row for row in rows if not copied(row["path"])]
    case_variants = [row["path"] for row in rows
                     if (row["path"].split("/")[0] not in dirs and row["path"].split("/")[0].casefold() in folded_dirs)
                     or (row["path"] not in files and row["path"].casefold() in folded_files)]
    with_ignored = [row["path"] for row in rows if any(ignored(part) for part in row["path"].split("/"))]
    special_inside = [row for row in rows if copied(row["path"]) and row["mode"] not in ("0o100644", "0o100755")]
    folded = {}
    for row in rows:
        folded.setdefault(row["path"].casefold(), []).append(row["path"])
    collisions = [names for names in folded.values() if len(names) > 1]
    unusual = [row["path"] for row in rows
               if any(ch in row["path"] for ch in ' "\\') or any(ord(ch) < 0x20 or ord(ch) >= 0x7f for ch in row["path"])]
    report = {"index_sha256": digest, "index_version": version, "entries": count,
              "stages_other_than_zero": [row["path"] for row in rows if row["stage"]],
              "outside_copied_set": outside, "outside_count": len(outside),
              "case_variants_of_copied_roots": case_variants,
              "with_an_ignored_component": with_ignored,
              "inside_copied_set_not_regular_files": special_inside,
              "case_insensitive_collisions": collisions,
              "names_git_may_quote": unusual,
              "modes": sorted({row["mode"] for row in rows})}
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=1, sort_keys=True)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("index_version", "entries", "outside_count", "modes")}))
    print("outside:", [(row["path"], row["mode"]) for row in outside])
    print("case variants:", case_variants[:20], "ignored components:", with_ignored[:20])
    print("inside, not regular:", special_inside[:20], "collisions:", collisions[:20], "unusual:", unusual[:40])


if __name__ == "__main__":
    main()
