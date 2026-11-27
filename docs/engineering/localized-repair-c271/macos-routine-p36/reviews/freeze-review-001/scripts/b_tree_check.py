"""Read B's loose commit and root tree objects, and the index's cache-tree root, from Git's files (read only).

Usage: python3 -I -S -B b_tree_check.py GITDIR WORKTREE_GITDIR COMMIT OUT.json
Starts no Git. Decompresses loose objects with zlib; parses the index's TREE extension root.
"""
import hashlib, json, struct, sys, zlib

gitdir, wtgit, commit, destination = sys.argv[1:5]


def loose(oid):
    raw = zlib.decompress(open(f"{gitdir}/objects/{oid[:2]}/{oid[2:]}", "rb").read())
    assert hashlib.sha1(raw).hexdigest() == oid, "object name differs from its bytes"
    header, body = raw.split(b"\0", 1)
    kind, size = header.split(b" ")
    assert int(size) == len(body)
    return kind.decode(), body


kind, body = loose(commit)
assert kind == "commit"
tree = body.split(b"\n", 1)[0].split(b" ")[1].decode()
kind, tbody = loose(tree)
assert kind == "tree"
entries, offset = [], 0
while offset < len(tbody):
    space = tbody.index(b" ", offset)
    nul = tbody.index(b"\0", space)
    mode, name = tbody[offset:space].decode(), tbody[space + 1:nul].decode()
    oid = tbody[nul + 1:nul + 21].hex()
    entries.append({"mode": mode, "name": name, "oid": oid})
    offset = nul + 21

raw = open(f"{wtgit}/index", "rb").read()
# Find the TREE extension after the entries: scan for b"TREE" followed by a size whose end fits the file.
version, count = struct.unpack(">II", raw[4:12])
position = raw.find(b"TREE", 12)
cache_root = None
while position != -1:
    (size,) = struct.unpack(">I", raw[position + 4:position + 8])
    data = raw[position + 8:position + 8 + size]
    if data[:1] == b"\0":
        line_end = data.index(b"\n")
        counts = data[1:line_end].decode()
        entry_count = int(counts.split(" ")[0])
        if entry_count >= 0:
            cache_root = {"entry_count": entry_count, "subtrees": int(counts.split(" ")[1]),
                          "oid": data[line_end + 1:line_end + 21].hex()}
            break
    position = raw.find(b"TREE", position + 4)
result = {"commit": commit, "tree": tree, "root_entries": entries,
          "claude_entry": [e for e in entries if e["name"] == ".claude"],
          "index_cache_tree_root": cache_root,
          "index_entry_count": count, "index_version": version}
with open(destination, "x") as fh:
    json.dump(result, fh, indent=1)
    fh.write("\n")
print(json.dumps({"tree": tree, "claude_entry": result["claude_entry"], "cache_root": cache_root,
                  "root_names": [e["name"] for e in entries]}, indent=1))
