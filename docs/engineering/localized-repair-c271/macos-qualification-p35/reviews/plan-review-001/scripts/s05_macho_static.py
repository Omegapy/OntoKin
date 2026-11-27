"""W3 plan review 001, script s05: static Mach-O facts of the bound Git (N-07) and of bin/node.

Standard library only; starts nothing (audit hook); never executes either file. Reads the fat
header and each slice's load commands of the developer tools' Git, finds the version text and
the "git version %s" format in each slice, and evaluates the predicted line against the
git-version-line-v1 grammar. Parses bin/node's header and load commands against W3-OBSERVER
section 6.2 (the implemented Node rules), and looks for the version text v24.22.1 in it.

Usage:
  python -I -S -B s05_macho_static.py --git GIT --node NODE --output OUT.json
"""
import argparse
import hashlib
import json
import os
import posixpath
import re
import struct
import sys
import time

REFUSED = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty")
EVENTS = []


def _hook(event, args):
    if event in REFUSED:
        EVENTS.append(event)
        raise RuntimeError("process creation refused: " + event)


sys.addaudithook(_hook)

REQ = 0x80000000
NAMES = {0x2: "LC_SYMTAB", 0xB: "LC_DYSYMTAB", 0xC: "LC_LOAD_DYLIB", 0xD: "LC_ID_DYLIB", 0xE: "LC_LOAD_DYLINKER",
         0x18 | REQ: "LC_LOAD_WEAK_DYLIB", 0x19: "LC_SEGMENT_64", 0x1B: "LC_UUID", 0x1C | REQ: "LC_RPATH",
         0x1D: "LC_CODE_SIGNATURE", 0x1E: "LC_SEGMENT_SPLIT_INFO", 0x1F | REQ: "LC_REEXPORT_DYLIB",
         0x20: "LC_LAZY_LOAD_DYLIB", 0x21: "LC_ENCRYPTION_INFO", 0x22: "LC_DYLD_INFO", 0x22 | REQ: "LC_DYLD_INFO_ONLY",
         0x23 | REQ: "LC_LOAD_UPWARD_DYLIB", 0x24: "LC_VERSION_MIN_MACOSX", 0x26: "LC_FUNCTION_STARTS",
         0x27: "LC_DYLD_ENVIRONMENT", 0x28 | REQ: "LC_MAIN", 0x29: "LC_DATA_IN_CODE", 0x2A: "LC_SOURCE_VERSION",
         0x2B: "LC_DYLIB_CODE_SIGN_DRS", 0x2C: "LC_ENCRYPTION_INFO_64", 0x2D: "LC_LINKER_OPTION",
         0x2E: "LC_LINKER_OPTIMIZATION_HINT", 0x31: "LC_NOTE", 0x32: "LC_BUILD_VERSION",
         0x33 | REQ: "LC_DYLD_EXPORTS_TRIE", 0x34 | REQ: "LC_DYLD_CHAINED_FIXUPS", 0x36: "LC_ATOM_INFO"}
CPU = {7: "CPU_TYPE_X86", 0x01000007: "CPU_TYPE_X86_64", 12: "CPU_TYPE_ARM", 0x0100000C: "CPU_TYPE_ARM64"}
NODE_LIST = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
             "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
             "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
             "LC_DYLD_EXPORTS_TRIE"}
NODE_REFUSED = {"LC_RPATH", "LC_DYLD_ENVIRONMENT", "LC_LOAD_UPWARD_DYLIB", "LC_REEXPORT_DYLIB"}
SINGLE = {"LC_LOAD_DYLINKER", "LC_MAIN", "LC_UUID", "LC_SYMTAB", "LC_DYSYMTAB", "LC_CODE_SIGNATURE",
          "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE", "LC_FUNCTION_STARTS",
          "LC_DATA_IN_CODE", "LC_SOURCE_VERSION", "LC_ID_DYLIB"}


def read_all(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        chunks = []
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            chunks.append(block)
        return b"".join(chunks)
    finally:
        os.close(fd)


def version(v):
    return "%d.%d.%d" % (v >> 16, (v >> 8) & 0xFF, v & 0xFF)


def thin(data, base=0):
    magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _ = struct.unpack_from("<8I", data, base)
    assert magic == 0xFEEDFACF, hex(magic)
    commands, off = [], base + 32
    for i in range(ncmds):
        cmd, size = struct.unpack_from("<II", data, off)
        body = data[off:off + size]
        name = NAMES.get(cmd)
        row = {"index": i, "cmd": "0x%08x" % cmd, "name": name, "cmdsize": size}
        if name in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_ID_DYLIB", "LC_REEXPORT_DYLIB", "LC_LOAD_UPWARD_DYLIB",
                    "LC_LAZY_LOAD_DYLIB", "LC_RPATH", "LC_LOAD_DYLINKER", "LC_DYLD_ENVIRONMENT"):
            at = struct.unpack_from("<I", body, 8)[0]
            row["path"] = body[at:body.index(b"\0", at)].decode("ascii")
        if name == "LC_BUILD_VERSION":
            platform, minos, sdk, ntools = struct.unpack_from("<IIII", body, 8)
            row.update(platform=platform, minos=version(minos), sdk=version(sdk))
        if name == "LC_UUID":
            row["uuid"] = body[8:24].hex().upper()
        commands.append(row)
        off += size
    assert off == base + 32 + sizeofcmds
    return {"cputype": "0x%08x" % cputype, "cpu": CPU.get(cputype), "cpusubtype": "0x%08x" % cpusubtype,
            "filetype": filetype, "flags": "0x%08x" % flags, "ncmds": ncmds, "sizeofcmds": sizeofcmds,
            "commands": commands}


def strings_around(blob, needle, limit=8):
    found, start = [], 0
    while len(found) < limit:
        at = blob.find(needle, start)
        if at < 0:
            break
        left = blob.rfind(b"\0", 0, at) + 1
        right = blob.find(b"\0", at)
        found.append({"offset": at, "c_string": blob[left:right].decode("ascii", "replace")})
        start = at + 1
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--git", required=True)
    ap.add_argument("--node", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    t0 = time.time()
    out = {"script": os.path.basename(__file__), "argv": sys.argv, "pid": os.getpid(), "ppid": os.getppid()}

    git = read_all(a.git)
    out["git"] = {"path": a.git, "sha256": hashlib.sha256(git).hexdigest(), "size_bytes": len(git)}
    magic = struct.unpack_from(">I", git, 0)[0]
    out["git"]["magic"] = "0x%08x" % magic
    slices = []
    if magic in (0xCAFEBABE, 0xCAFEBABF):
        count = struct.unpack_from(">I", git, 4)[0]
        size = 20 if magic == 0xCAFEBABE else 32
        for i in range(count):
            if magic == 0xCAFEBABE:
                cputype, cpusubtype, offset, length, align = struct.unpack_from(">5I", git, 8 + size * i)
            else:
                cputype, cpusubtype, offset, length, align, _ = struct.unpack_from(">IIQQII", git, 8 + size * i)
            parsed = thin(git, offset)
            blob = git[offset:offset + length]
            dylibs = [c["path"] for c in parsed["commands"] if c["name"] in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB")]
            slices.append({
                "cputype": "0x%08x" % cputype, "cpu": CPU.get(cputype), "cpusubtype": "0x%08x" % cpusubtype,
                "offset": offset, "size": length, "align": align, "filetype": parsed["filetype"],
                "ncmds": parsed["ncmds"], "dylibs": dylibs,
                "rpaths": [c["path"] for c in parsed["commands"] if c["name"] == "LC_RPATH"],
                "dylinker": [c["path"] for c in parsed["commands"] if c["name"] == "LC_LOAD_DYLINKER"],
                "build_version": [{k: c[k] for k in ("platform", "minos", "sdk")} for c in parsed["commands"]
                                  if c["name"] == "LC_BUILD_VERSION"],
                "uuid": [c["uuid"] for c in parsed["commands"] if c["name"] == "LC_UUID"],
                "code_signature": any(c["name"] == "LC_CODE_SIGNATURE" for c in parsed["commands"]),
                "unknown_commands": [c["cmd"] for c in parsed["commands"] if c["name"] is None],
                "system_only_dylibs": all(d.startswith(("/usr/lib/", "/System/Library/")) for d in dylibs),
                "format_git_version": strings_around(blob, b"git version %s"),
                "version_text": strings_around(blob, b"(Apple Git-"),
                "env_names": {name: blob.find(name.encode() + b"\0") >= 0 for name in (
                    "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_SYSTEM", "GIT_ATTR_NOSYSTEM",
                    "GIT_TERMINAL_PROMPT", "GIT_OPTIONAL_LOCKS", "GIT_NO_REPLACE_OBJECTS", "HOME",
                    "XDG_CONFIG_HOME", "GIT_TRACE2", "GIT_EXEC_PATH")},
                "messages": {text: blob.find(text.encode()) >= 0 for text in (
                    "unable to access '%s': %s", "$HOME not set", "could not determine executable path")}})
    out["git"]["slices"] = slices
    arm = [s for s in slices if s["cpu"] == "CPU_TYPE_ARM64"]
    if arm:
        texts = sorted({row["c_string"] for row in arm[0]["version_text"]})
        out["git"]["arm64_version_texts"] = texts
        predicted = ("git version " + texts[0] + "\n") if len(texts) == 1 else None
        out["git"]["predicted_line"] = predicted
        out["git"]["predicted_matches_grammar"] = predicted is not None and re.fullmatch(
            rb"git version [\x20-\x7e]{1,200}\n", predicted.encode("ascii")) is not None
        out["git"]["predicted_equals_launch_record"] = predicted == "git version 2.50.1 (Apple Git-155)\n"
    out["git"]["slices_embed_the_same_version"] = len({tuple(sorted({r["c_string"] for r in s["version_text"]}))
                                                       for s in slices}) == 1

    node = read_all(a.node)
    parsed = thin(node, 0)
    names = [c["name"] for c in parsed["commands"]]
    counts = {}
    for n in names:
        counts[n] = counts.get(n, 0) + 1
    dylibs = [c for c in parsed["commands"] if c["name"] in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB")]
    rules = {
        "thin MH_MAGIC_64": struct.unpack_from("<I", node, 0)[0] == 0xFEEDFACF,
        "CPU_TYPE_ARM64, subtype exactly 0": parsed["cputype"] == "0x0100000c" and parsed["cpusubtype"] == "0x00000000",
        "MH_EXECUTE": parsed["filetype"] == 2,
        "no refused command": not (set(names) & NODE_REFUSED),
        "every command in the closed list of 16": all(n in NODE_LIST for n in names),
        "LC_LOAD_DYLINKER /usr/lib/dyld": [c["path"] for c in parsed["commands"]
                                           if c["name"] == "LC_LOAD_DYLINKER"] == ["/usr/lib/dyld"],
        "one LC_LOAD_DYLINKER and one LC_MAIN": counts.get("LC_LOAD_DYLINKER") == 1 and counts.get("LC_MAIN") == 1,
        "no duplicate single-instance command": not any(counts.get(n, 0) > 1 for n in SINGLE),
        "dylibs normalized absolute under /usr/lib/ or /System/Library/, no @": all(
            not c["path"].startswith("@") and c["path"].startswith("/") and not c["path"].startswith("//")
            and posixpath.normpath(c["path"]) == c["path"] and c["path"].startswith(("/usr/lib/", "/System/Library/"))
            for c in dylibs)}
    out["node"] = {"path": a.node, "sha256": hashlib.sha256(node).hexdigest(), "size_bytes": len(node),
                   "header": {k: parsed[k] for k in ("cputype", "cpusubtype", "filetype", "flags", "ncmds",
                                                     "sizeofcmds")},
                   "commands": [{k: c.get(k) for k in ("index", "name", "cmdsize", "path")} for c in parsed["commands"]],
                   "dylibs": [{"index": c["index"], "name": c["name"], "path": c["path"]} for c in dylibs],
                   "corefoundation": [{"index": c["index"], "name": c["name"]} for c in dylibs
                                      if c["path"].endswith("/CoreFoundation")],
                   "rules": rules, "rules_all_hold": all(rules.values()),
                   "version_text": strings_around(node, b"v24.22.1", limit=4)}
    out["elapsed_s"] = round(time.time() - t0, 3)
    out["process_events"] = EVENTS
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({"git_sha256": out["git"]["sha256"], "git_size": out["git"]["size_bytes"],
                      "slices": [(s["cpu"], s["cpusubtype"], s["dylibs"], s["rpaths"]) for s in slices],
                      "predicted": out["git"].get("predicted_line"),
                      "grammar": out["git"].get("predicted_matches_grammar"),
                      "node_rules_all_hold": out["node"]["rules_all_hold"],
                      "corefoundation": out["node"]["corefoundation"], "elapsed_s": out["elapsed_s"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
