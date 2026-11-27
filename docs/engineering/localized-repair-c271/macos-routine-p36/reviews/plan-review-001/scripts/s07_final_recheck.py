"""W3 plan review 001, s07: the dependency inventory recomputed as a document, and the final rechecks.

1. The dependency inventory (ontokin.current-host-readback-dependencies/0.2.0) built by my own code from
   the installed reader tree and the retained C195 archive, compared byte for byte with the frozen file.
2. The plan file again: its digest, its canonical path, and the canonical paths of the three inventories.
3. W2's SHA256SUMS.txt again; the evidence parent still empty; the attempt and the capture paths absent;
   the boot, release and build unchanged.

python3 -I -S -B s07_final_recheck.py --plan P --w2 DIR --deps-root R --archive A --expected-deps FILE
    --evidence DIR --attempt PATH [--absent PATH ...] --expect-plan-sha256 H --expect-boot U
    [--label NAME=PATH ...] --output OUT
"""
import argparse
import hashlib
import os
import stat
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3_common as common  # noqa: E402
sys.path.pop(0)


def canonical(path):
    return os.path.realpath(path) == path and not any(
        stat.S_ISLNK(os.lstat(prefix).st_mode)
        for prefix in ["/".join(path.split("/")[:index]) for index in range(2, len(path.split("/")) + 1)])


def main():
    common.start()
    parser = argparse.ArgumentParser()
    for name in ("plan", "w2", "deps-root", "archive", "expected-deps", "evidence", "attempt", "expect-plan-sha256",
                 "expect-boot", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--absent", action="append", default=[])
    parser.add_argument("--label", action="append", default=[])
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    checks = common.Checks()
    out = {"schema": "w3.p36.plan-review-001.s07/1", "pid": os.getpid(), "at_epoch": time.time(),
           "boot_before": common.sysctl_text("kern.bootsessionuuid")}

    # 1. The dependency inventory as a document.
    files, directories, stack = {}, {}, [""]
    while stack:
        rel = stack.pop()
        directory = args.deps_root + "/" + rel if rel else args.deps_root
        for name in sorted(os.listdir(directory)):
            sub = rel + "/" + name if rel else name
            info = os.lstat(args.deps_root + "/" + sub)
            if stat.S_ISDIR(info.st_mode):
                directories[sub] = common.mode_text(info)
                stack.append(sub)
            elif stat.S_ISREG(info.st_mode):
                files[sub] = common.read_bytes(args.deps_root + "/" + sub, keep=False)[1]
            else:
                files[sub] = {"kind": "not a regular file"}
    archive_binding = common.read_bytes(args.archive, keep=False)[1]
    document = {"schema": "ontokin.current-host-readback-dependencies/0.2.0", "files": files,
                "directories": directories, "archive": {"path": args.archive, **archive_binding}}
    raw = common.canonical_json(document)
    expected_raw, expected_binding, _, _ = common.read_bytes(args.expected_deps)
    out["dependencies"] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "files": len(files),
                           "directories": len(directories), "expected": expected_binding,
                           "bytes_equal": raw == expected_raw}
    checks.add("R-01", raw == expected_raw, "the dependency inventory, built by my own code, is byte-identical to the "
               "frozen file", out["dependencies"])

    # 2. The plan file and the paths the observer canonicalizes.
    plan_raw, plan_binding, _, plan_info = common.read_bytes(args.plan)
    plan = common.strict_loads(plan_raw)
    paths = [args.plan, plan["source"]["inventory"]["path"], plan["python"]["inventory"]["path"],
             plan["dependencies"]["inventory"]["path"]]
    out["plan"] = {**plan_binding, "nlink": plan_info.st_nlink, "canonical_paths": {p: canonical(p) for p in paths}}
    checks.add("R-02", plan_binding["sha256"] == args.expect_plan_sha256 and all(canonical(p) for p in paths)
               and plan_info.st_nlink == 1,
               "the plan's SHA-256 is still the one this review records, and the plan and its three inventories are at "
               "canonical paths", out["plan"])
    for key in ("source", "python", "dependencies"):
        descriptor = plan[key]["inventory"]
        actual = common.read_bytes(descriptor["path"], keep=False)[1]
        checks.add("R-03-" + key, actual == {k: descriptor[k] for k in ("sha256", "size_bytes", "mode")},
                   key + " inventory still has the plan's binding", actual)

    # 3. W2's files, the evidence parent, the absent paths and the boot.
    sums_raw = common.read_bytes(args.w2 + "/SHA256SUMS.txt")[0].decode("ascii")
    mismatches, listed = [], set()
    for line in sums_raw.splitlines():
        digest, _, rel = line.partition("  ")
        listed.add(rel)
        if common.read_bytes(args.w2 + "/" + rel, keep=False)[1]["sha256"] != digest:
            mismatches.append(rel)
    present, stack = set(), [""]
    while stack:
        rel = stack.pop()
        for name in os.listdir(args.w2 + ("/" + rel if rel else "")):
            sub = rel + "/" + name if rel else name
            if stat.S_ISDIR(os.lstat(args.w2 + "/" + sub).st_mode):
                stack.append(sub)
            else:
                present.add(sub)
    checks.add("R-04", not mismatches and present == listed | {"SHA256SUMS.txt"},
               "W2's directory still holds exactly its listed files, each with its listed digest",
               {"listed": len(listed), "mismatches": mismatches, "unlisted": sorted(present - listed - {"SHA256SUMS.txt"})})
    entries = os.listdir(args.evidence)
    absent = {path: os.path.lexists(path) for path in [args.attempt] + args.absent}
    checks.add("R-05", entries == [] and not any(absent.values()),
               "the evidence parent is still empty; the attempt and every capture and record path are absent",
               {"entries": entries, "present": sorted(path for path, there in absent.items() if there)})
    now = {"boot": common.sysctl_text("kern.bootsessionuuid"), "release": common.sysctl_text("kern.osrelease"),
           "build": common.sysctl_text("kern.osversion")}
    checks.add("R-06", now["boot"] == args.expect_boot == out["boot_before"] and now["release"] == plan["platform"]["release"],
               "the boot and the release are unchanged", now)
    out["checks"] = checks.rows
    out["summary"] = checks.summary()
    out["refused_process_events"] = list(common.REFUSED_EVENTS)
    digest = common.write_output(args.output, out, labels)
    print(labels(str({"summary": out["summary"], "deps_sha256": out["dependencies"]["sha256"],
                      "plan_sha256": plan_binding["sha256"], "output_sha256": digest})))


if __name__ == "__main__":
    main()
