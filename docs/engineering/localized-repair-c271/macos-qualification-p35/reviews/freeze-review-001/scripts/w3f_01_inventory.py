"""W3 freeze review 001, script 01: hash the freeze directory and map FREEZE-001.json.

Reads only. Writes only into OUT (the path given as argv[2]).
"""
import hashlib
import json
import os
import stat
import sys

FREEZE_DIR = sys.argv[1]
OUT = sys.argv[2]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


rows = []
for root, dirs, files in os.walk(FREEZE_DIR):
    dirs.sort()
    for d in dirs:
        p = os.path.join(root, d)
        st = os.lstat(p)
        rows.append({"path": os.path.relpath(p, FREEZE_DIR), "type": "dir",
                     "mode": oct(stat.S_IMODE(st.st_mode)), "nlink": st.st_nlink})
    for fn in sorted(files):
        p = os.path.join(root, fn)
        st = os.lstat(p)
        entry = {"path": os.path.relpath(p, FREEZE_DIR),
                 "type": "link" if stat.S_ISLNK(st.st_mode) else "file",
                 "mode": oct(stat.S_IMODE(st.st_mode)), "nlink": st.st_nlink,
                 "size": st.st_size}
        if stat.S_ISREG(st.st_mode):
            entry["sha256"] = sha256_file(p)
        rows.append(entry)

sums = {}
with open(os.path.join(FREEZE_DIR, "SHA256SUMS.txt"), "r", encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        digest, name = line.split("  ", 1)
        sums[name] = digest

files = {r["path"]: r for r in rows if r["type"] == "file"}
verify = {"listed": len(sums), "ok": 0, "bad": [], "missing": [], "unlisted": []}
for name, digest in sums.items():
    r = files.get(name)
    if r is None:
        verify["missing"].append(name)
    elif r["sha256"] != digest:
        verify["bad"].append(name)
    else:
        verify["ok"] += 1
for name in files:
    if name not in sums and name != "SHA256SUMS.txt":
        verify["unlisted"].append(name)

with open(os.path.join(FREEZE_DIR, "FREEZE-001.json"), "rb") as f:
    raw = f.read()
doc = json.loads(raw)
top = []
for k, v in doc.items():
    top.append({"key": k, "type": type(v).__name__,
                "len": len(v) if isinstance(v, (list, dict, str)) else None,
                "json_bytes": len(json.dumps(v, ensure_ascii=False))})

report = {
    "freeze_sha256": hashlib.sha256(raw).hexdigest(),
    "freeze_size": len(raw),
    "freeze_lines": raw.count(b"\n"),
    "freeze_endswith_newline": raw.endswith(b"\n"),
    "sha256sums_verify": verify,
    "files": rows,
    "top_level": top,
}
os.makedirs(os.path.join(OUT, "records"), exist_ok=True)
with open(os.path.join(OUT, "records", "01-inventory.json"), "x", encoding="utf-8") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)
    f.write("\n")
print(json.dumps({k: report[k] for k in ("freeze_sha256", "freeze_size", "freeze_lines",
                                          "freeze_endswith_newline", "sha256sums_verify")}, indent=1))
for t in top:
    print(t)
