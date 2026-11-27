"""W2 of C271-P36 (gate MR, stage S4): the last start of the stage.

1. Hygiene scan. The notes and the scripts may be copied into a public repository, so they
   must hold no machine path and no account name. The forbidden strings are derived at run
   time, never written here: the account's login name and home directory (from the password
   database), every --forbid-path argument, the volume name and the next component of each
   such path on an external volume, the last component of each --forbid-word-of path, and
   the generic prefixes of external volumes, home directories and the optional-software tree
   (built at run time, so that this file can scan itself).
2. SHA256SUMS.txt: the SHA-256 of every regular file under --dir except SHA256SUMS.txt itself,
   one "<hex>  <relative path>" line each, sorted by path, written with exclusive creation and
   then read back and verified.

It starts no process and prints its result on stdout only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import re
import sys

PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn",
                            "os.fork", "os.forkpty", "pty.spawn", "os.startfile"))
REFUSED_EVENTS = []


def _audit(event, args):
    if event in PROCESS_EVENTS:
        REFUSED_EVENTS.append(event)
        raise RuntimeError("Process creation refused by the W2 audit hook: " + event)


sys.addaudithook(_audit)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def main(argv=None):
    if not (sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode):
        raise SystemExit("Run under -I -S -B")
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--dir", required=True)
    parser.add_argument("--scan", action="append", default=[])
    parser.add_argument("--forbid-path", action="append", default=[])
    parser.add_argument("--forbid-word-of", action="append", default=[])
    args = parser.parse_args(argv)
    account = pwd.getpwuid(os.getuid())
    paths = [account.pw_dir] + list(args.forbid_path)
    words = {account.pw_name}
    for path in args.forbid_path:
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 3 and parts[0] == "Volumes":
            words.update(parts[1:3])
    for path in args.forbid_word_of:
        words.add(os.path.basename(path.rstrip("/")))
    generic = tuple("/" + name + "/" for name in ("Volumes", "Users", "opt"))
    absolute = re.compile(r"(?<![A-Za-z0-9_.>-])(?:" + "|".join(re.escape(value) for value in generic) + ")")
    findings = []
    for path in args.scan:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for number, line in enumerate(text.splitlines(), 1):
            lowered = line.lower()
            for value in paths:
                if value and value in line:
                    findings.append({"file": os.path.basename(path), "line": number, "kind": "machine path"})
            if absolute.search(line):
                findings.append({"file": os.path.basename(path), "line": number, "kind": "absolute machine path"})
            for value in words:
                if value and re.search(r"(?<![A-Za-z0-9])" + re.escape(value.lower()) + r"(?![A-Za-z0-9])", lowered):
                    findings.append({"file": os.path.basename(path), "line": number, "kind": "account or machine word"})
    if findings:
        sys.stdout.write(json.dumps({"scan": "failed", "findings": findings, "sums": "not written"}) + "\n")
        return 1
    root = os.path.realpath(args.dir)
    rows = []
    for current, directories, files in os.walk(root):
        directories.sort()
        for name in sorted(files):
            full = os.path.join(current, name)
            rel = os.path.relpath(full, root)
            if rel == "SHA256SUMS.txt" or os.path.islink(full) or not os.path.isfile(full):
                continue
            rows.append((rel, _sha256(full)))
    rows.sort()
    raw = "".join(digest + "  " + rel + "\n" for rel, digest in rows).encode("utf-8")
    target = os.path.join(root, "SHA256SUMS.txt")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    mismatches = []
    with open(target, "r", encoding="utf-8") as handle:
        for line in handle:
            digest, rel = line.rstrip("\n").split("  ", 1)
            if _sha256(os.path.join(root, rel)) != digest:
                mismatches.append(rel)
    sys.stdout.write(json.dumps({"scan": "passed", "scanned": [os.path.basename(path) for path in args.scan],
                                 "forbidden_strings": len(paths) + len(words) + len(generic),
                                 "sums": {"files": len(rows), "sha256": _sha256(target), "size_bytes": len(raw),
                                          "mismatches": mismatches},
                                 "pid": os.getpid(), "refused_process_events": REFUSED_EVENTS}, sort_keys=True) + "\n")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
