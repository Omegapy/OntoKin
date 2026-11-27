"""W3 plan review 001, s05: the bound Git implementation, read statically (it is never started).

Reads the universal file's fat header and both slices, lists each slice's load commands, dylinker,
dylibs and rpaths, and finds the version format and version text in each slice, so that the version
line its arm64 slice would print can be compared with the plan's grammar git-version-line-v1.

python3 -I -S -B s05_git_static.py --git PATH [--label NAME=PATH ...] --output OUT
"""
import argparse
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3_common as common  # noqa: E402
sys.path.pop(0)

CPU = {0x01000007: "x86_64", 0x0100000C: "arm64"}
NAMES = {0x19: "LC_SEGMENT_64", 0x2: "LC_SYMTAB", 0xB: "LC_DYSYMTAB", 0xE: "LC_LOAD_DYLINKER", 0x1B: "LC_UUID",
         0x32: "LC_BUILD_VERSION", 0x2A: "LC_SOURCE_VERSION", 0x80000028: "LC_MAIN", 0xC: "LC_LOAD_DYLIB",
         0x80000018: "LC_LOAD_WEAK_DYLIB", 0x26: "LC_FUNCTION_STARTS", 0x29: "LC_DATA_IN_CODE",
         0x1D: "LC_CODE_SIGNATURE", 0x80000022: "LC_DYLD_INFO_ONLY", 0x80000034: "LC_DYLD_CHAINED_FIXUPS",
         0x80000033: "LC_DYLD_EXPORTS_TRIE", 0x8000001C: "LC_RPATH", 0x27: "LC_DYLD_ENVIRONMENT",
         0x80000023: "LC_LOAD_UPWARD_DYLIB", 0x8000001F: "LC_REEXPORT_DYLIB", 0xD: "LC_ID_DYLIB",
         0x24: "LC_VERSION_MIN_MACOSX", 0x2B: "LC_DYLIB_CODE_SIGN_DRS", 0x2E: "LC_LINKER_OPTIMIZATION_HINT"}


def version_text(value):
    return "%d.%d.%d" % (value >> 16, (value >> 8) & 0xFF, value & 0xFF)


def slice_facts(data):
    magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _ = struct.unpack_from("<8I", data, 0)
    commands, dylibs, dylinker, rpaths, build, offset = [], [], [], [], None, 32
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", data, offset)
        name = NAMES.get(cmd, "0x%08x" % cmd)
        commands.append(name)
        body = data[offset:offset + size]
        if name in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_LOAD_DYLINKER", "LC_RPATH"):
            field = struct.unpack_from("<I", body, 8)[0]
            text = body[field:body.index(b"\0", field)].decode("ascii")
            {"LC_LOAD_DYLINKER": dylinker, "LC_RPATH": rpaths}.get(name, dylibs).append(text)
        if name == "LC_BUILD_VERSION":
            platform, minos, sdk = struct.unpack_from("<III", body, 8)
            build = {"platform": platform, "minos": version_text(minos), "sdk": version_text(sdk)}
        offset += size
    formats = [match.start() for match in re.finditer(rb"git version %s\n", data)]
    versions = sorted(set(match.group(0).decode("ascii") for match in
                          re.finditer(rb"\b2\.\d+\.\d+ \(Apple Git-\d+\)", data)))
    return {"magic": "0x%08x" % magic, "cpu": CPU.get(cputype, hex(cputype)), "cpusubtype": cpusubtype,
            "filetype": filetype, "ncmds": ncmds, "flags": "0x%08x" % flags, "commands": commands,
            "unknown_commands": [name for name in commands if name.startswith("0x")], "dylinker": dylinker,
            "dylibs": dylibs, "rpaths": rpaths, "build": build, "version_format_count": len(formats),
            "version_texts": versions}


def main():
    common.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("--git", required=True)
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    data, binding, _, info = common.read_bytes(args.git)
    out = {"schema": "w3.p36.plan-review-001.s05/1", "pid": os.getpid(), "binding": binding, "nlink": info.st_nlink,
           "boot": common.sysctl_text("kern.bootsessionuuid")}
    magic, count = struct.unpack_from(">II", data, 0)
    out["fat_magic"] = "0x%08x" % magic
    slices = []
    for index in range(count):
        cputype, cpusubtype, offset, size, align = struct.unpack_from(">IIIII", data, 8 + 20 * index)
        facts = slice_facts(data[offset:offset + size])
        facts.update(fat_cputype=CPU.get(cputype, hex(cputype)), fat_cpusubtype=cpusubtype, offset=offset, size=size)
        slices.append(facts)
    out["slices"] = slices
    arm = [row for row in slices if row["cpu"] == "arm64"]
    texts = arm[0]["version_texts"] if arm else []
    predicted = ("git version " + texts[0] + "\n") if len(texts) == 1 else None
    out["predicted_line"] = predicted
    out["fits_grammar"] = predicted is not None and re.fullmatch(r"git version [\x20-\x7e]{1,200}\n", predicted) is not None
    out["arm64e_slice"] = any(row["cpu"] == "arm64" and row["cpusubtype"] & 0xFF == 2 for row in slices)
    out["refused_process_events"] = list(common.REFUSED_EVENTS)
    digest = common.write_output(args.output, out, labels)
    print(labels(str({"binding": binding, "slices": [(row["cpu"], row["cpusubtype"]) for row in slices],
                      "predicted": predicted, "fits": out["fits_grammar"], "output_sha256": digest})))


if __name__ == "__main__":
    main()
