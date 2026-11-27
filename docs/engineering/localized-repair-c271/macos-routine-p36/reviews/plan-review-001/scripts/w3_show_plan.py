"""W3 plan review 001: read the observation plan's bytes, digest them, test the canonical form,
and print an indented copy for reading. Standard library only; reads only; writes only the
absent output path named by the second argument (exclusive creation).

Usage: python3 -I -S -B w3_show_plan.py PLAN OUTPUT
"""
import hashlib
import json
import os
import stat
import sys


def refuse_unless_flags():
    flags = sys.flags
    if not (flags.isolated and flags.no_site and flags.dont_write_bytecode):
        raise SystemExit("run me as python3 -I -S -B")


def main(argv):
    refuse_unless_flags()
    plan_path, output = argv[1], argv[2]
    info = os.lstat(plan_path)
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit("plan is not a regular file")
    with open(plan_path, "rb") as handle:
        raw = handle.read()
    again = os.lstat(plan_path)
    value = json.loads(raw.decode("utf-8"))
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                           allow_nan=False).encode("ascii")
    report = {
        "path_label": "the plan",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "st_size": info.st_size,
        "mode": "0o%03o" % stat.S_IMODE(info.st_mode),
        "nlink": info.st_nlink,
        "unchanged_during_read": (info.st_ino, info.st_size, info.st_mtime_ns) ==
                                 (again.st_ino, again.st_size, again.st_mtime_ns),
        "canonical_bytes_equal": canonical == raw,
        "top_level_keys": sorted(value),
    }
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps({"report": report, "plan": value}, indent=1, sort_keys=True))
        handle.write("\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv)
