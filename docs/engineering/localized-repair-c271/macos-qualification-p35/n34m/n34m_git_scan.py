#!/usr/bin/env python3
"""N34-M: the version text embedded in a Git implementation's arm64 slice (worker W1, C271-P35).

A static read; Git is never started. It finds the fat slice of CPU_TYPE_ARM64, searches its bytes
for Apple's version pattern and for the "git version %s" format, and predicts the line that one
``--version`` start would print. It writes exactly one file, --output, by exclusive creation.

Run:  <venv>/bin/python -I -S -B n34m_git_scan.py --git PATH --output OUT.json
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys

GRAMMAR = re.compile(rb"git version [\x20-\x7e]{1,200}\n")  # the observer's GIT_VERSION_LINE, restated


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--git", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    data = open(args.git, "rb").read()
    result = {"schema": "n34m-git-scan-raw/1", "path": args.git, "sha256": hashlib.sha256(data).hexdigest(),
              "size_bytes": len(data)}
    if data[:4] != b"\xca\xfe\xba\xbe":
        result["error"] = "not a 32-bit fat file"
    else:
        count = struct.unpack_from(">I", data, 4)[0]
        slices = []
        for number in range(count):
            cputype, cpusubtype, offset, size, align = struct.unpack_from(">iiIII", data, 8 + 20 * number)
            slices.append({"cputype": "0x%08x" % (cputype & 0xFFFFFFFF), "cpusubtype": "0x%08x" % (cpusubtype & 0xFFFFFFFF),
                           "offset": offset, "size": size})
        result["slices"] = slices
        arm = [row for row in slices if row["cputype"] == "0x0100000c"]
        if arm:
            body = data[arm[0]["offset"]:arm[0]["offset"] + arm[0]["size"]]
            versions = sorted(set(match.group(0).decode("ascii")
                                  for match in re.finditer(rb"\d+\.\d+\.\d+ \(Apple Git-\d+\)", body)))
            formats = sorted(set(match.group(0).decode("ascii") for match in re.finditer(rb"git version %s", body)))
            result.update(arm64_embedded_versions=versions, arm64_formats=formats)
            if len(versions) == 1 and formats:
                predicted = ("git version " + versions[0] + "\n").encode("ascii")
                result["predicted_line"] = predicted.decode("ascii")
                result["predicted_line_matches_grammar"] = GRAMMAR.fullmatch(predicted) is not None
    result["note"] = "static prediction only; no Git start was made"
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
