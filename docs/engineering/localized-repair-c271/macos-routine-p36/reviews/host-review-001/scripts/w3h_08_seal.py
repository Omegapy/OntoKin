"""HOST review 001, script 08: the seal. It writes SHA256SUMS.txt only if every check passes.

1. HOST-REVIEW-001.json parses strictly (no duplicate member), its verdict is one of the three, its
   HOST digest equals the file now, and every output digest it cites equals the output file.
2. The privacy scan: every file in OUT is searched for the owner's account name, the words of the
   account's full name, the home directory, the volume's mount point and name, the parent directory's
   machine path, the package prefix and HOST's CoreFoundation value. All are derived at run time and
   never written; only counts per file and term class are reported.
3. SHA256SUMS.txt lists every file in OUT except itself, in `shasum -a 256` form, written with O_EXCL.
Usage: python3 -I -S -B w3h_08_seal.py --dir OUT --host H --plan P --out OUT/outputs/h08-seal-run1.json
"""
import argparse
import os
import pwd
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()


def main():
    ap = argparse.ArgumentParser()
    for name in ("--dir", "--host", "--plan", "--out"):
        ap.add_argument(name, required=True)
    args = ap.parse_args()
    ck = C.Checks()
    started = time.time()
    record = C.strict_loads(C.read_bytes(os.path.join(args.dir, "HOST-REVIEW-001.json"))[0])
    _, hf, _ = C.read_bytes(args.host, keep=False)
    ck.add("Z01", record["verdict"] in ("ACCEPT", "ACCEPT_WITH_NONMANDATORY_FINDINGS",
                                        "REJECT_WITH_MANDATORY_FINDINGS")
           and record["host"]["sha256"] == hf["sha256"] and record["mandatory_findings"] == []
           and all(f["mandatory"] is False for f in record["findings"])
           and all(set(f) == {"id", "mandatory", "location", "statement", "required_change"} for f in record["findings"]),
           "the JSON record parses strictly; its verdict is allowed; its HOST digest equals the file now; every "
           "finding has id, mandatory, location, statement and required_change", findings=len(record["findings"]))
    cited = {}
    for name, row in record["checks"].items():
        path = os.path.join(args.dir, row["output"])
        cited[name] = C.read_bytes(path, keep=False)[1]["sha256"] == row["sha256"]
    ck.add("Z02", all(cited.values()), "every output digest the record cites equals the output file", rows=cited)
    # the private terms, derived now and never written
    user = pwd.getpwuid(os.getuid())
    plan = C.strict_loads(C.read_bytes(args.plan)[0])
    host = C.strict_loads(C.read_bytes(args.host)[0])
    root_dev = os.lstat("/").st_dev
    mounts = [row["path"] for row in plan["evidence"]["ancestors"] if row["device"] != root_dev]
    mount = min(mounts, key=len) if mounts else None
    parent = posixpath_parent = os.path.dirname(plan["source"]["root"].rstrip("/"))
    parent = os.path.dirname(posixpath_parent)
    framework = plan["python"]["framework"]
    prefix = framework.split("/Cellar/", 1)[0]
    terms = {"account name": [user.pw_name], "home directory": [user.pw_dir],
             "full-name words": [w for w in re.split(r"[\s,]+", user.pw_gecos or "") if len(w) >= 3],
             "volume mount point": [mount] if mount else [],
             "volume name": [os.path.basename(mount)] if mount else [],
             "parent directory path": [parent], "package prefix": [prefix],
             "CoreFoundation value": [host["environment"]["cf_user_text_encoding"] or ""]}
    terms = {k: [t for t in v if t] for k, v in terms.items()}
    hits, scanned = {}, 0
    for dirpath, dirnames, filenames in os.walk(args.dir):
        for name in filenames:
            path = os.path.join(dirpath, name)
            if name == "SHA256SUMS.txt":
                continue
            text = C.read_bytes(path)[0].decode("utf-8", "replace")
            scanned += 1
            for cls, values in terms.items():
                count = sum(len(re.findall(re.escape(v), text, flags=re.I if cls == "full-name words" else 0))
                            for v in values)
                if count:
                    hits.setdefault(os.path.relpath(path, args.dir), {})[cls] = count
    ck.add("Z03", not hits and all(terms[k] for k in ("account name", "home directory", "volume mount point",
                                                      "parent directory path", "package prefix",
                                                      "CoreFoundation value")),
           "no private term occurs in any file of OUT (terms derived at run time; counts only)",
           files_scanned=scanned, term_classes={k: len(v) for k, v in terms.items()}, hits=hits)
    out = {"script": "w3h_08_seal.py", "process": C.process_identity(), "started_epoch": started,
           "ended_epoch": time.time(), "checks": ck.rows, "summary": ck.summary(), "audit_events": C.EVENTS}
    if ck.summary()["failed"]:
        print("NOT SEALED", ck.summary(), {k: v for k, v in hits.items()})
        return 1
    digest = C.write_new(args.out, out)
    rows = []
    for dirpath, dirnames, filenames in os.walk(args.dir):
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, args.dir)
            if rel == "SHA256SUMS.txt":
                continue
            rows.append((rel, C.read_bytes(path, keep=False)[1]["sha256"]))
    raw = "".join("%s  %s\n" % (sha, rel) for rel, sha in sorted(rows)).encode("ascii")
    fd = os.open(os.path.join(args.dir, "SHA256SUMS.txt"), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    print("SEALED", digest, ck.summary(), "files listed:", len(rows), "sums:", C.sha256(raw))
    return 0


if __name__ == "__main__":
    sys.exit(main())
