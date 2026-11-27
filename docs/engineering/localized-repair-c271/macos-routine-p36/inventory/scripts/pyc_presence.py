"""W1 (C271-P36) cached-bytecode presence and freshness check. Reads files only; imports nothing it checks.

Run only as: python3 -I -S -B pyc_presence.py ROOT LABEL OUTFILE [--exclude NAME ...]

For every .py file under ROOT (not following directory links; excluded top-level names skipped), it
reports whether __pycache__/<stem>.cpython-312.pyc (and .opt-1, .opt-2) exists, and for the opt-level ''
file whether its 16-byte header matches the source as the import system would check it:
  flags == 0 (timestamp): header mtime == int(source st_mtime) & 0xFFFFFFFF and header size == st_size & 0xFFFFFFFF;
  flags & 1 (hash-based): recorded as hash-based; checked-source (flags & 2) noted, not recomputed.
The magic number is compared with the one in the first readable .pyc of the tree, and reported.
Output: JSON summary plus every module without a fresh opt-level '' file. Paths are relative to ROOT.
"""
from __future__ import annotations

import json
import os
import struct
import sys

TAG = "cpython-312"


def main():
    root, label, outfile, *rest = sys.argv[1:]
    excludes = set()
    while rest:
        flag, value, *rest = rest
        if flag != "--exclude":
            raise SystemExit("unknown option " + flag)
        excludes.add(value)
    sources, missing, stale, hashed, magic_seen, opt1_missing, opt2_missing = 0, [], [], [], {}, 0, 0
    links = []
    for parent, dirnames, filenames in os.walk(root, followlinks=False):
        rel_parent = os.path.relpath(parent, root)
        if rel_parent == ".":
            dirnames[:] = [d for d in dirnames if d not in excludes]
        for d in list(dirnames):
            if os.path.islink(os.path.join(parent, d)):
                links.append(os.path.normpath(os.path.join(rel_parent, d)))
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__" and not os.path.islink(os.path.join(parent, d)))
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            path = os.path.join(parent, name)
            if os.path.islink(path):
                links.append(os.path.normpath(os.path.join(rel_parent, name)))
                continue
            sources += 1
            stem = name[:-3]
            cache = os.path.join(parent, "__pycache__")
            pyc = os.path.join(cache, f"{stem}.{TAG}.pyc")
            rel = os.path.normpath(os.path.join(rel_parent, name))
            if not os.path.exists(os.path.join(cache, f"{stem}.{TAG}.opt-1.pyc")):
                opt1_missing += 1
            if not os.path.exists(os.path.join(cache, f"{stem}.{TAG}.opt-2.pyc")):
                opt2_missing += 1
            if not os.path.isfile(pyc):
                missing.append(rel)
                continue
            st = os.stat(path)
            with open(pyc, "rb") as stream:
                header = stream.read(16)
            if len(header) < 16:
                stale.append({"source": rel, "reason": "short header"})
                continue
            magic = header[:4].hex()
            magic_seen[magic] = magic_seen.get(magic, 0) + 1
            flags, = struct.unpack("<I", header[4:8])
            if flags & 1:
                hashed.append({"source": rel, "check_source": bool(flags & 2)})
                continue
            mtime, size = struct.unpack("<II", header[8:16])
            if mtime != (int(st.st_mtime) & 0xFFFFFFFF) or size != (st.st_size & 0xFFFFFFFF):
                stale.append({"source": rel, "header_mtime": mtime, "source_mtime": int(st.st_mtime),
                              "header_size": size, "source_size": st.st_size})
    out = {"label": label, "sources": sources, "missing_opt0": len(missing), "stale_opt0": len(stale),
           "hash_based": len(hashed), "opt1_missing": opt1_missing, "opt2_missing": opt2_missing,
           "magic_numbers": magic_seen, "excluded_top_level": sorted(excludes), "skipped_links": links,
           "missing_opt0_files": missing, "stale_opt0_files": stale, "hash_based_files": hashed}
    with open(outfile, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")
    print(json.dumps({k: v for k, v in out.items() if not k.endswith("_files")}, indent=1))


if __name__ == "__main__":
    main()
