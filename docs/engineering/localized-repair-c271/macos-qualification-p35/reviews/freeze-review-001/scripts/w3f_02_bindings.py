"""W3 freeze review 001, script 02: recompute every binding of FREEZE-001.json independently.

For each binding, host fact, configuration descriptor, environment file and preparation source it
records: lstat kind, SHA-256, size, mode, link count, canonical form and on-disk spelling of every
component. It also compares the tool bindings with authoring/TOOLING-SHA256SUMS.txt at C.
Reads only; writes one record into OUT/records.
"""
import hashlib
import json
import os
import stat
import sys

FREEZE = sys.argv[1]
OUT = sys.argv[2]
WT = "<worktree>"
TOOLSUMS = WT + "/docs/engineering/localized-repair-c271/macos-qualification-p35/authoring/TOOLING-SHA256SUMS.txt"


def sha256_file(path):
    h = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        while True:
            b = os.read(fd, 1 << 20)
            if not b:
                break
            h.update(b)
    finally:
        os.close(fd)
    return h.hexdigest()


def spelled(path):
    cur = "/"
    bad = []
    for part in [p for p in path.split("/") if p]:
        try:
            names = os.listdir(cur)
        except OSError as exc:
            bad.append(("unlistable", cur, str(exc)))
            return bad
        if part not in names:
            alt = [n for n in names if n.lower() == part.lower()]
            bad.append(("not-in-listing", cur, part, alt))
        cur = os.path.join(cur, part)
    return bad


def observe(path):
    o = {"path": path}
    try:
        st = os.lstat(path)
    except OSError as exc:
        o["error"] = str(exc)
        return o
    m = st.st_mode
    o["kind"] = ("file" if stat.S_ISREG(m) else "directory" if stat.S_ISDIR(m)
                 else "symlink" if stat.S_ISLNK(m) else "special")
    o["mode"] = "0o%03o" % stat.S_IMODE(m)
    o["nlink"] = st.st_nlink
    o["size_bytes"] = st.st_size
    o["uid"] = st.st_uid
    if stat.S_ISREG(m):
        o["sha256"] = sha256_file(path)
    o["canonical"] = os.path.realpath(path) == path and os.path.normpath(path) == path
    o["spelling_problems"] = spelled(path)
    return o


with open(FREEZE, "rb") as f:
    fz = json.loads(f.read())

results = []
problems = []
for b in fz["bindings"]:
    o = observe(b["path"])
    diff = []
    if "error" in o:
        diff.append("absent: " + o["error"])
    else:
        if o["kind"] != b["kind"]:
            diff.append("kind %s != %s" % (o["kind"], b["kind"]))
        for k in ("sha256", "size_bytes", "mode"):
            if k in b and o.get(k) != b[k]:
                diff.append("%s %r != %r" % (k, o.get(k), b[k]))
        if b.get("nlink_one") and o["nlink"] != 1:
            diff.append("nlink %d" % o["nlink"])
        if not b.get("nlink_one"):
            diff.append("NOTE nlink_one not set (nlink %d)" % o["nlink"])
        if not o["canonical"]:
            diff.append("not canonical")
        if o["spelling_problems"]:
            diff.append("spelling %r" % (o["spelling_problems"],))
        extra = set(b) - {"id", "kind", "mode", "nlink_one", "path", "role", "sha256", "size_bytes"}
        if extra:
            diff.append("NOTE extra keys %s" % sorted(extra))
    results.append({"id": b["id"], "role": b.get("role"), "path": b["path"], "frozen": {k: b.get(k) for k in ("kind", "sha256", "size_bytes", "mode", "nlink_one")}, "observed": o, "diff": diff})
    if [d for d in diff if not d.startswith("NOTE")]:
        problems.append((b["id"], diff))

# Duplicates and id/path uniqueness
ids = [b["id"] for b in fz["bindings"]]
paths = [b["path"] for b in fz["bindings"]]
dups = {"ids": sorted({i for i in ids if ids.count(i) > 1}), "paths": sorted({p for p in paths if paths.count(p) > 1})}

# Tool sums at C
toolsums = {}
with open(TOOLSUMS, "r", encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if line:
            d, n = line.split("  ", 1)
            toolsums[n] = d
tool_cmp = []
for b in fz["bindings"]:
    if b["id"].startswith("tool:"):
        name = b["id"][5:]
        keys = [k for k in toolsums if k.endswith("/" + name) or k == name]
        tool_cmp.append({"id": b["id"], "frozen": b["sha256"], "sums_keys": keys,
                         "sums": [toolsums[k] for k in keys],
                         "equal": any(toolsums[k] == b["sha256"] for k in keys)})

# Host facts
hf = []
for h in fz["host_facts"]:
    o = observe(h["path"])
    content = None
    try:
        with open(h["path"], "rb") as f:
            content = f.read()
    except OSError as exc:
        content = ("ERR " + str(exc)).encode()
    hf.append({"id": h["id"], "frozen": {k: h.get(k) for k in ("sha256", "size_bytes", "mode", "nlink_one")},
               "observed": o, "content_repr": repr(content), "uid": os.getuid()})

# HOST, completion, result, contract, adoption, wrapper, env files, configs
extra = {}
for key, spec in (("HOST", fz["host"]["HOST"]), ("completion", fz["host"]["completion"]),
                  ("result", fz["host"]["result"]), ("contract", fz["contract"]["source"]),
                  ("adoption", fz["contract"]["adoption_record"]), ("wrapper", fz["wrapper"])):
    o = observe(spec["path"])
    extra[key] = {"frozen": {k: spec.get(k) for k in ("sha256", "size_bytes", "mode", "state")}, "observed": o}
for name, env in fz["environments"].items():
    o = observe(env["path"])
    with open(env["path"], "rb") as f:
        raw = f.read()
    doc = json.loads(raw)
    extra["env:" + name] = {"frozen": {"sha256": env["sha256"], "size_bytes": env["size_bytes"]},
                            "observed": o, "doc_equals_freeze": doc.get("environment") == env["environment"],
                            "doc_keys": sorted(doc), "schema": doc.get("schema"),
                            "names_equal": sorted(env["environment"]) == env["names"]}

# completion state
with open(fz["host"]["completion"]["path"], "rb") as f:
    comp = json.loads(f.read())
extra["completion_doc_state"] = comp.get("state")
with open(fz["host"]["result"]["path"], "rb") as f:
    res = json.loads(f.read())
extra["result_doc_keys"] = sorted(res)
extra["result_doc_state"] = res.get("state")

report = {"bindings_count": len(fz["bindings"]), "problems": problems, "duplicates": dups,
          "tool_cmp": tool_cmp, "toolsums": toolsums, "host_facts": hf, "extra": extra, "results": results}
with open(os.path.join(OUT, "records", "02-bindings.json"), "x", encoding="utf-8") as f:
    json.dump(report, f, indent=1)
    f.write("\n")
print("bindings", len(fz["bindings"]), "problems", len(problems))
for p in problems:
    print("PROBLEM", p)
print("dups", dups)
for t in tool_cmp:
    print("TOOL", t["id"], t["equal"], t["sums_keys"])
print("host_facts", json.dumps(hf, indent=0))
for k, v in extra.items():
    if isinstance(v, dict) and "observed" in v:
        ob = v["observed"]
        print("EXTRA", k, {kk: ob.get(kk) for kk in ("kind", "sha256", "size_bytes", "mode", "nlink", "canonical")}, "frozen", v["frozen"],
              {kk: v[kk] for kk in v if kk not in ("observed", "frozen")})
    else:
        print("EXTRA", k, v)
print("NOTES:")
for r in results:
    notes = [d for d in r["diff"] if d.startswith("NOTE")]
    if notes:
        print(r["id"], notes)
print("INDEX:")
for r in results:
    print(r["id"], "|", r["frozen"]["kind"], r["frozen"]["mode"], r["frozen"]["size_bytes"], r["frozen"]["sha256"][:12] if r["frozen"]["sha256"] else None, "|", r["path"], "|", r["role"])
