"""W3 freeze review 001, script 11: a copy of s7/prepare-s7-001.sh whose evidence root is rewritten into OUT, and a check
of what it created against the freeze's 43 preparation entries (rewritten the same way).

  w3f_11_prep_copy.py FREEZE OUT make     writes OUT/prep-test/prepare-copy.sh and OUT/prep-test/evidence/
  w3f_11_prep_copy.py FREEZE OUT verify   compares OUT/prep-test/evidence with the rewritten entries
Also compares the original script's mkdir and cp lines with the freeze's entries, one for one.
"""
import hashlib
import json
import os
import re
import stat
import sys

FREEZE, OUT, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
E = "<local>/c271-p35/evidence"
T = os.path.join(OUT, "prep-test", "evidence")
with open(FREEZE, "rb") as f:
    fz = json.loads(f.read())
script_path = fz["preparation"]["script"]["path"]
with open(script_path, "rb") as f:
    script = f.read().decode("utf-8")
entries = fz["preparation"]["entries"]

# One-for-one comparison of the original script with the entries
mkdirs = re.findall(r"absent '([^']+)'; /bin/mkdir -m 0700 '([^']+)'", script)
cps = re.findall(r"absent '([^']+)'; /bin/cp -n '([^']+)' '([^']+)'", script)
lines = [l for l in script.split("\n") if l.strip()]
other = [l for l in lines if not (l.startswith("absent '") or l.startswith("#"))]
dirs = [e for e in entries if e["kind"] == "directory"]
files = [e for e in entries if e["kind"] == "file"]
report = {
    "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
    "mkdir_lines": len(mkdirs), "cp_lines": len(cps), "entries_dirs": len(dirs), "entries_files": len(files),
    "mkdir_absent_equals_target": all(a == b for a, b in mkdirs),
    "cp_absent_equals_target": all(a == c for a, b, c in cps),
    "mkdir_targets_equal_entries_in_order": [b for a, b in mkdirs] == [e["path"] for e in dirs],
    "cp_targets_equal_entries_in_order": [(b, c) for a, b, c in cps] == [(e["copied_from"], e["path"]) for e in files],
    "other_lines": other,
    "parents_created_before_children": all(
        os.path.dirname(e["path"]) == E or os.path.dirname(e["path"]) in [d["path"] for d in dirs[:i]]
        for i, e in enumerate(dirs)),
    "rm_mv_ln_chmod_absent": not re.search(r"\b(rm|mv|ln|chmod|chown|touch|tee)\b", "\n".join(other + [l for l in lines if l.startswith("absent")])),
}
if MODE == "make":
    os.makedirs(T, mode=0o755)
    copy = script.replace(E, T)
    assert E not in copy
    path = os.path.join(OUT, "prep-test", "prepare-copy.sh")
    with open(path, "x", encoding="utf-8") as f:
        f.write(copy)
    report["copy"] = {"path": "<OUT>/prep-test/prepare-copy.sh", "sha256": hashlib.sha256(copy.encode()).hexdigest()}
else:
    problems = []
    seen = set()
    for e in entries:
        p = e["path"].replace(E, T)
        seen.add(p)
        st = os.lstat(p)
        mode = "0o%03o" % stat.S_IMODE(st.st_mode)
        if e["kind"] == "directory":
            if not stat.S_ISDIR(st.st_mode) or mode != e["mode"] or sorted(os.listdir(p)) != sorted(e["entries"]):
                problems.append((p, "dir", mode, sorted(os.listdir(p))))
        else:
            with open(p, "rb") as f:
                d = hashlib.sha256(f.read()).hexdigest()
            if not stat.S_ISREG(st.st_mode) or mode != e["mode"] or d != e["sha256"] or st.st_size != e["size_bytes"] or st.st_nlink != 1:
                problems.append((p, "file", mode, d, st.st_size, st.st_nlink))
    created = set()
    for root, ds, fs in os.walk(T):
        for n in ds + fs:
            created.add(os.path.join(root, n))
    report["verify"] = {"problems": problems, "created": len(created), "extra": sorted(created - seen), "missing": sorted(seen - created)}
print(json.dumps(report, indent=1))
