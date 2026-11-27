"""W3 plan review 001, s01: W2's files and digests, the evidence parent, absent paths, MH's exact files.

python3 -I -S -B s01_files.py --w2 DIR --mh-w2 DIR --evidence DIR --attempt PATH [--absent PATH ...]
    [--label NAME=PATH ...] --output OUT
"""
import argparse
import os
import stat
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # my own helper only; -I keeps it off by default
import w3_common as common  # noqa: E402
sys.path.pop(0)


def listing(root):
    """Every entry below root, links never followed: {relative path: kind}."""
    rows = {}
    stack = [""]
    while stack:
        rel = stack.pop()
        directory = os.path.join(root, rel) if rel else root
        for name in sorted(os.listdir(directory)):
            sub = rel + "/" + name if rel else name
            info = os.lstat(os.path.join(root, sub))
            if stat.S_ISLNK(info.st_mode):
                rows[sub] = "symlink"
            elif stat.S_ISDIR(info.st_mode):
                rows[sub] = "directory"
                stack.append(sub)
            elif stat.S_ISREG(info.st_mode):
                rows[sub] = "file"
            else:
                rows[sub] = "special"
    return rows


def main():
    common.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("--w2", required=True)
    parser.add_argument("--mh-w2", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--absent", action="append", default=[])
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    checks = common.Checks()
    out = {"schema": "w3.p36.plan-review-001.s01/1", "started_at_epoch": time.time(), "pid": os.getpid()}
    out["boot_before"] = common.sysctl_text("kern.bootsessionuuid")

    # 1. W2's SHA256SUMS.txt against the files, and no other file.
    raw, binding, _, _ = common.read_bytes(os.path.join(args.w2, "SHA256SUMS.txt"))
    out["w2_sums_file"] = binding
    listed = {}
    for line in raw.decode("ascii").splitlines():
        digest, _, rel = line.partition("  ")
        listed[rel] = digest
    rows = []
    for rel, digest in sorted(listed.items()):
        _, actual, _, info = common.read_bytes(os.path.join(args.w2, rel), keep=False)
        rows.append({"path": rel, "listed": digest, "actual": actual["sha256"], "size_bytes": actual["size_bytes"],
                     "mode": actual["mode"], "nlink": info.st_nlink, "equal": digest == actual["sha256"]})
    present = listing(args.w2)
    files = sorted(rel for rel, kind in present.items() if kind == "file")
    others = sorted(rel for rel, kind in present.items() if kind not in ("file", "directory"))
    out["w2_files"] = rows
    checks.add("F-01", all(row["equal"] for row in rows), "every digest listed in W2's SHA256SUMS.txt equals its file",
               {"listed": len(rows), "mismatches": [row["path"] for row in rows if not row["equal"]]})
    checks.add("F-02", set(files) == set(listed) | {"SHA256SUMS.txt"} and not others,
               "W2's directory holds exactly the listed files and SHA256SUMS.txt, and no link or special file",
               {"files": len(files), "unlisted": sorted(set(files) - set(listed) - {"SHA256SUMS.txt"}),
                "missing": sorted(set(listed) - set(files)), "others": others})

    # 2. W2's plan and inventories against MH's exact files (bytes).
    compare = {}
    for name in ("observation-plan-001.json", "source-inventory-001.json", "python-inventory-001.json",
                 "dependencies-inventory-001.json"):
        mine, mine_binding, _, _ = common.read_bytes(os.path.join(args.w2, name))
        theirs, theirs_binding, _, _ = common.read_bytes(os.path.join(args.mh_w2, name))
        compare[name] = {"w2": mine_binding, "mh": theirs_binding, "bytes_equal": mine == theirs}
    out["mh_comparison"] = compare
    for index, name in enumerate(("source-inventory-001.json", "python-inventory-001.json",
                                  "dependencies-inventory-001.json"), 3):
        checks.add("F-%02d" % index, compare[name]["bytes_equal"], name + " is byte-identical to MH's exact file",
                   {"w2": compare[name]["w2"]["sha256"], "mh": compare[name]["mh"]["sha256"]})
    checks.add("F-06", not compare["observation-plan-001.json"]["bytes_equal"]
               and compare["observation-plan-001.json"]["mh"]["sha256"] ==
               "b8cd6449aba958373f68715158402ed2e0e233e08213f3521bbc3d80cfe4c152",
               "MH's exact plan is the reviewed b8cd6449... file, and W2's plan differs from it (section 4 compares)",
               {"w2": compare["observation-plan-001.json"]["w2"], "mh": compare["observation-plan-001.json"]["mh"]})

    # 3. The evidence parent: an existing directory, empty; the attempt and the capture paths absent.
    info = os.lstat(args.evidence)
    entries = sorted(os.listdir(args.evidence))
    out["evidence_parent"] = {"device": info.st_dev, "inode": info.st_ino, "mode": common.mode_text(info),
                              "is_directory": stat.S_ISDIR(info.st_mode), "entries": entries}
    checks.add("F-07", stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and entries == [],
               "the evidence parent exists as a directory and is empty", out["evidence_parent"])
    checks.add("F-08", not os.path.lexists(args.attempt), "the attempt is absent", {"attempt": args.attempt})
    absent = {path: os.path.lexists(path) for path in args.absent}
    checks.add("F-09", not any(absent.values()), "every capture and command-record path is absent",
               {"paths": sorted(absent), "present": sorted(path for path, there in absent.items() if there)})

    out["boot_after"] = common.sysctl_text("kern.bootsessionuuid")
    out["checks"] = checks.rows
    out["summary"] = checks.summary()
    out["refused_process_events"] = list(common.REFUSED_EVENTS)
    digest = common.write_output(args.output, out, labels)
    print(labels(str({"summary": out["summary"], "boot": out["boot_before"], "output_sha256": digest})))


if __name__ == "__main__":
    main()
