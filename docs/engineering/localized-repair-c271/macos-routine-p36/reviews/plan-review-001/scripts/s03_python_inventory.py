"""W3 plan review 001, s03: the Python installation inventory, recomputed by my own code.

The document is the one W3-OBSERVER section 5 defines (schema ontokin.current-host-readback-python-
inventory/0.2.0): both trees listed exhaustively without following a link, the interpreter selection
chain, and the transitive closure of every Mach-O image's non-system references with every link hop,
under section 6.3's Python rules. Its digest is the SHA-256 of its canonical JSON bytes. The script
then verifies the packages (section 5 item 6) against the macOS lock, and compares the result with
the frozen file part by part and byte for byte.

python3 -I -S -B s03_python_inventory.py --venv V --framework F --lock LOCK --expected FILE
    [--label NAME=PATH ...] --output OUT
"""
import argparse
import base64
import csv
import io
import os
import posixpath
import re
import stat
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3_common as common  # noqa: E402
sys.path.pop(0)

SCHEMA = "ontokin.current-host-readback-python-inventory/0.2.0"
PROCESS_IMAGE = "Resources/Python.app/Contents/MacOS/Python"
SYSTEM_PREFIXES = ("/usr/lib/", "/System/Library/")
CONTRACT_PINS = {"attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1",
                 "referencing": "0.37.0", "rpds-py": "2026.5.1", "typing_extensions": "4.16.0", "Pillow": "13.0.0"}

# <mach-o/loader.h>
REQ = 0x80000000
NAMES = {0x1: "LC_SEGMENT", 0x2: "LC_SYMTAB", 0x3: "LC_SYMSEG", 0x4: "LC_THREAD", 0x5: "LC_UNIXTHREAD",
         0x6: "LC_LOADFVMLIB", 0x7: "LC_IDFVMLIB", 0x8: "LC_IDENT", 0x9: "LC_FVMFILE", 0xA: "LC_PREPAGE",
         0xB: "LC_DYSYMTAB", 0xC: "LC_LOAD_DYLIB", 0xD: "LC_ID_DYLIB", 0xE: "LC_LOAD_DYLINKER",
         0xF: "LC_ID_DYLINKER", 0x10: "LC_PREBOUND_DYLIB", 0x11: "LC_ROUTINES", 0x12: "LC_SUB_FRAMEWORK",
         0x13: "LC_SUB_UMBRELLA", 0x14: "LC_SUB_CLIENT", 0x15: "LC_SUB_LIBRARY", 0x16: "LC_TWOLEVEL_HINTS",
         0x17: "LC_PREBIND_CKSUM", 0x18 | REQ: "LC_LOAD_WEAK_DYLIB", 0x19: "LC_SEGMENT_64",
         0x1A: "LC_ROUTINES_64", 0x1B: "LC_UUID", 0x1C | REQ: "LC_RPATH", 0x1D: "LC_CODE_SIGNATURE",
         0x1E: "LC_SEGMENT_SPLIT_INFO", 0x1F | REQ: "LC_REEXPORT_DYLIB", 0x20: "LC_LAZY_LOAD_DYLIB",
         0x21: "LC_ENCRYPTION_INFO", 0x22: "LC_DYLD_INFO", 0x22 | REQ: "LC_DYLD_INFO_ONLY",
         0x23 | REQ: "LC_LOAD_UPWARD_DYLIB", 0x24: "LC_VERSION_MIN_MACOSX", 0x25: "LC_VERSION_MIN_IPHONEOS",
         0x26: "LC_FUNCTION_STARTS", 0x27: "LC_DYLD_ENVIRONMENT", 0x28 | REQ: "LC_MAIN",
         0x29: "LC_DATA_IN_CODE", 0x2A: "LC_SOURCE_VERSION", 0x2B: "LC_DYLIB_CODE_SIGN_DRS",
         0x2C: "LC_ENCRYPTION_INFO_64", 0x2D: "LC_LINKER_OPTION", 0x2E: "LC_LINKER_OPTIMIZATION_HINT",
         0x2F: "LC_VERSION_MIN_TVOS", 0x30: "LC_VERSION_MIN_WATCHOS", 0x31: "LC_NOTE", 0x32: "LC_BUILD_VERSION",
         0x33 | REQ: "LC_DYLD_EXPORTS_TRIE", 0x34 | REQ: "LC_DYLD_CHAINED_FIXUPS", 0x35 | REQ: "LC_FILESET_ENTRY",
         0x36: "LC_ATOM_INFO"}
FILE_TYPES = {1: "MH_OBJECT", 2: "MH_EXECUTE", 3: "MH_FVMLIB", 4: "MH_CORE", 5: "MH_PRELOAD", 6: "MH_DYLIB",
              7: "MH_DYLINKER", 8: "MH_BUNDLE", 9: "MH_DYLIB_STUB", 10: "MH_DSYM", 11: "MH_KEXT_BUNDLE",
              12: "MH_FILESET"}
# Contract section 7's closed list of 16, plus section 4's two additions for the Python side.
NODE_LIST = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
             "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
             "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
             "LC_DYLD_EXPORTS_TRIE"}
PYTHON_LIST = NODE_LIST | {"LC_ID_DYLIB", "LC_RPATH"}
ONCE = {"LC_LOAD_DYLINKER", "LC_MAIN", "LC_UUID", "LC_SYMTAB", "LC_DYSYMTAB", "LC_CODE_SIGNATURE",
        "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE", "LC_FUNCTION_STARTS",
        "LC_DATA_IN_CODE", "LC_SOURCE_VERSION", "LC_ID_DYLIB"}
DYLIB_KINDS = {"LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_ID_DYLIB", "LC_REEXPORT_DYLIB", "LC_LOAD_UPWARD_DYLIB",
               "LC_LAZY_LOAD_DYLIB"}
LINKEDIT = {"LC_CODE_SIGNATURE", "LC_SEGMENT_SPLIT_INFO", "LC_FUNCTION_STARTS", "LC_DATA_IN_CODE",
            "LC_DYLIB_CODE_SIGN_DRS", "LC_LINKER_OPTIMIZATION_HINT", "LC_DYLD_EXPORTS_TRIE",
            "LC_DYLD_CHAINED_FIXUPS", "LC_ATOM_INFO"}


class Refused(Exception):
    pass


def magic_kind(head):
    m = head[:4]
    if m in (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"):
        return "fat"
    if m == b"\xcf\xfa\xed\xfe":
        return "macho64"
    if m in (b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce"):
        return "macho32"
    if m == b"\xfe\xed\xfa\xcf":
        return "macho64-be"
    return None


def walk(root, problems):
    """{relative path: entry} for every entry below root, never following a link."""
    entries, heads = {}, {}
    stack = [""]
    while stack:
        rel = stack.pop()
        directory = root + "/" + rel if rel else root
        before = os.lstat(directory)
        names = sorted(os.listdir(directory))
        for name in names:
            if name in (".", "..") or "/" in name or "\0" in name or not name.isprintable():
                problems.append({"rule": "NAME", "path": directory + "/" + repr(name)})
            sub = rel + "/" + name if rel else name
            path = root + "/" + sub
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                entries[sub] = {"kind": "symlink", "target": os.readlink(path)}
            elif stat.S_ISDIR(info.st_mode):
                entries[sub] = {"kind": "directory", "mode": common.mode_text(info)}
                stack.append(sub)
            elif stat.S_ISREG(info.st_mode):
                _, binding, head, _ = common.read_bytes(path, keep=False, prefix=4)
                entries[sub] = {"kind": "file", **binding}
                heads[path] = head
            else:
                problems.append({"rule": "SPECIAL", "path": path})
        after = os.lstat(directory)
        if (before.st_ino, before.st_mtime_ns, before.st_ctime_ns) != (after.st_ino, after.st_mtime_ns,
                                                                     after.st_ctime_ns):
            problems.append({"rule": "CHANGED-WHILE-LISTED", "path": directory})
    return entries, heads


def resolve(path):
    """Component by component, as the kernel resolves it; every link followed is recorded as a hop."""
    pending = [part for part in path.split("/") if part]
    current, hops = "/", []
    while pending:
        part = pending.pop(0)
        if part == ".":
            continue
        if part == "..":
            current = posixpath.dirname(current)
            continue
        candidate = posixpath.join(current, part)
        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            return {"state": "absent", "path": candidate, "hops": hops}
        if stat.S_ISLNK(info.st_mode):
            if len(hops) >= 40:
                raise Refused("link chain too long: " + path)
            target = os.readlink(candidate)
            hops.append({"path": candidate, "target": target})
            if target.startswith("/"):
                current = "/"
            pending = [p for p in target.split("/") if p] + pending
            continue
        if pending and not stat.S_ISDIR(info.st_mode):
            return {"state": "absent", "path": candidate + "/" + "/".join(pending), "hops": hops}
        current = candidate
    info = os.lstat(current)
    kind = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "other"
    return {"state": kind, "path": current, "hops": hops}


def normalized_absolute(path):
    return path.startswith("/") and not path.startswith("//") and posixpath.normpath(path) == path


def c_string(body, field, minimum):
    if len(body) < minimum:
        raise Refused("short command")
    offset = struct.unpack_from("<I", body, field)[0]
    if not minimum <= offset < len(body):
        raise Refused("string offset outside its command")
    end = body.find(b"\0", offset)
    if end <= offset:
        raise Refused("empty or unterminated string")
    raw = body[offset:end]
    if not all(0x20 <= b <= 0x7E for b in raw):
        raise Refused("string is not printable ASCII")
    return raw.decode("ascii")


def inside_file(offset, size, file_size):
    if offset + size > file_size:
        raise Refused("command data outside the file")


def parse_macho(data):
    """Header and every load command of a thin 64-bit little-endian arm64 image, with structural checks."""
    file_size = len(data)
    kind = magic_kind(data)
    if kind != "macho64":
        raise Refused("magic " + str(kind))
    if file_size < 32:
        raise Refused("truncated header")
    _, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _ = struct.unpack_from("<8I", data, 0)
    if cputype != 0x0100000C or cpusubtype != 0:
        raise Refused("cpu %#x/%#x" % (cputype, cpusubtype))
    if not (0 < ncmds <= 4096 and 0 < sizeofcmds <= 4 * 1024 * 1024 and 32 + sizeofcmds <= file_size):
        raise Refused("load command table")
    commands, offset, end = [], 32, 32 + sizeofcmds
    for _ in range(ncmds):
        if offset + 8 > end:
            raise Refused("command header outside the table")
        cmd, cmdsize = struct.unpack_from("<II", data, offset)
        if cmdsize < 8 or cmdsize % 8 or offset + cmdsize > end:
            raise Refused("command size")
        body = data[offset:offset + cmdsize]
        name = NAMES.get(cmd)
        row = {"name": name, "cmd": cmd}
        if name == "LC_SEGMENT_64":
            if len(body) < 72:
                raise Refused("short segment")
            segname = body[8:24].split(b"\0", 1)[0]
            if not all(0x20 <= b <= 0x7E for b in segname):
                raise Refused("segment name")
            fileoff, filesize = struct.unpack_from("<QQ", body, 40)
            nsects = struct.unpack_from("<I", body, 64)[0]
            if len(body) != 72 + 80 * nsects:
                raise Refused("segment size")
            inside_file(fileoff, filesize, file_size)
        elif name == "LC_SYMTAB":
            if len(body) != 24:
                raise Refused("symtab size")
            symoff, nsyms, stroff, strsize = struct.unpack_from("<IIII", body, 8)
            inside_file(symoff, nsyms * 16, file_size)
            inside_file(stroff, strsize, file_size)
        elif name == "LC_DYSYMTAB":
            if len(body) != 80:
                raise Refused("dysymtab size")
        elif name in ("LC_LOAD_DYLINKER", "LC_ID_DYLINKER", "LC_DYLD_ENVIRONMENT", "LC_RPATH"):
            row["path"] = c_string(body, 8, 12)
        elif name in DYLIB_KINDS:
            row["path"] = c_string(body, 8, 24)
        elif name == "LC_UUID":
            if len(body) != 24:
                raise Refused("uuid size")
        elif name == "LC_BUILD_VERSION":
            if len(body) < 24:
                raise Refused("short build version")
            ntools = struct.unpack_from("<I", body, 20)[0]
            if len(body) != 24 + 8 * ntools:
                raise Refused("build version size")
        elif name == "LC_SOURCE_VERSION":
            if len(body) != 16:
                raise Refused("source version size")
        elif name == "LC_MAIN":
            if len(body) != 24:
                raise Refused("main size")
            if struct.unpack_from("<Q", body, 8)[0] >= file_size:
                raise Refused("entry offset")
        elif name in LINKEDIT:
            if len(body) != 16:
                raise Refused(name + " size")
            dataoff, datasize = struct.unpack_from("<II", body, 8)
            inside_file(dataoff, datasize, file_size)
        elif name in ("LC_DYLD_INFO", "LC_DYLD_INFO_ONLY"):
            if len(body) != 48:
                raise Refused(name + " size")
            values = struct.unpack_from("<10I", body, 8)
            for index in range(0, 10, 2):
                inside_file(values[index], values[index + 1], file_size)
        commands.append(row)
        offset += cmdsize
    if offset != end:
        raise Refused("command sizes do not add up")
    return {"filetype": FILE_TYPES.get(filetype, "0x%08x" % filetype), "commands": commands, "flags": flags}


def at_kind(path):
    for prefix in ("@rpath/", "@loader_path/", "@executable_path/"):
        if path.startswith(prefix) and len(path) > len(prefix):
            return prefix[:-1]
    return None


def python_rules(summary):
    """Contract section 4 and W3-OBSERVER section 6.3."""
    if summary["filetype"] not in ("MH_EXECUTE", "MH_DYLIB", "MH_BUNDLE"):
        raise Refused("file type " + summary["filetype"])
    identity, rpaths, references, counts = None, [], [], {}
    for row in summary["commands"]:
        name = row["name"]
        if name in ("LC_DYLD_ENVIRONMENT", "LC_LOAD_UPWARD_DYLIB") or name not in PYTHON_LIST:
            raise Refused("command " + str(name or hex(row["cmd"])))
        counts[name] = counts.get(name, 0) + 1
        if name == "LC_LOAD_DYLINKER" and row["path"] != "/usr/lib/dyld":
            raise Refused("dylinker " + row["path"])
        if name == "LC_ID_DYLIB":
            identity = row["path"]
        elif name == "LC_RPATH":
            path = row["path"]
            if path.startswith("@"):
                if not (path in ("@loader_path", "@executable_path")
                        or path.startswith(("@loader_path/", "@executable_path/"))):
                    raise Refused("rpath " + path)
            elif not normalized_absolute(path):
                raise Refused("rpath " + path)
            rpaths.append(path)
        elif name in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB"):
            path = row["path"]
            if path.startswith("@"):
                if at_kind(path) is None:
                    raise Refused("@ reference " + path)
            elif not normalized_absolute(path):
                raise Refused("reference " + path)
            references.append({"command": name, "path": path})
    twice = sorted(name for name, count in counts.items() if count > 1 and name in ONCE)
    if twice:
        raise Refused("duplicated " + ",".join(twice))
    if summary["filetype"] == "MH_EXECUTE":
        if counts.get("LC_LOAD_DYLINKER") != 1 or counts.get("LC_MAIN") != 1:
            raise Refused("executable structure")
    elif "LC_MAIN" in counts or "LC_LOAD_DYLINKER" in counts:
        raise Refused("non-executable with LC_MAIN or a dylinker")
    if summary["filetype"] == "MH_DYLIB" and counts.get("LC_ID_DYLIB") != 1:
        raise Refused("dylib without one LC_ID_DYLIB")
    return {"filetype": summary["filetype"], "id": identity, "rpaths": rpaths, "references": references,
            "commands": [row["name"] for row in summary["commands"]]}


def inside(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def tree_of(path, framework, venv):
    if inside(path, framework):
        return "framework", path[len(framework) + 1:]
    if inside(path, venv):
        return "venv", path[len(venv) + 1:]
    return None, None


def search_directory(raw, loader_dirs, executable_dir):
    if raw.startswith("@loader_path"):
        bases, suffix = sorted(loader_dirs), raw[len("@loader_path"):]
    elif raw.startswith("@executable_path"):
        bases, suffix = [executable_dir], raw[len("@executable_path"):]
    else:
        bases, suffix = [""], raw
    outcomes = [resolve(base + suffix if base else suffix) for base in bases]
    if len({(row["state"], row["path"]) for row in outcomes}) != 1:
        raise Refused("@loader_path rpath ambiguous: " + raw)
    return {"raw": raw, **outcomes[0]}


def closure_pass(images, framework, venv, entries, process_image, seed, stats):
    known = dict(images)
    spellings = {path: set(names) for path, names in seed.items()}
    used, done, external, links = {}, {}, {}, {}
    queue = sorted(images)
    while queue:
        path = queue.pop(0)
        if path in done:
            continue
        tree, binding = known[path]
        data, actual, _, _ = common.read_bytes(path)
        if actual != binding:
            raise Refused("image changed after its listing: " + path)
        rules = python_rules(parse_macho(data))
        stats["parsed"] += 1
        spellings.setdefault(path, set())
        used[path] = set(spellings[path])
        loader_dirs = {posixpath.dirname(path)} | {posixpath.dirname(name) for name in spellings[path]}
        executable_dir = posixpath.dirname(path if rules["filetype"] == "MH_EXECUTE" else process_image)
        rpaths = [search_directory(raw, loader_dirs, executable_dir) for raw in rules["rpaths"]]
        for row in rpaths:
            for hop in row["hops"]:
                links[(hop["path"], hop["target"])] = hop
        references = []
        for reference in rules["references"]:
            raw = reference["path"]
            if not raw.startswith("@") and raw.startswith(SYSTEM_PREFIXES):
                references.append({"command": reference["command"], "raw": raw, "kind": "system"})
                continue
            candidates, kind = [], at_kind(raw)
            if kind == "@rpath":
                selected = None
                for row in rpaths:
                    candidate = row["path"] + raw[len("@rpath"):]
                    outcome = (resolve(candidate) if row["state"] == "directory"
                               else {"state": "absent", "path": candidate, "hops": []})
                    candidates.append({"rpath": row["raw"], "candidate": candidate, "state": outcome["state"]})
                    if outcome["state"] != "absent":
                        selected = (candidate, outcome)
                        break
                if selected is None:
                    raise Refused("@rpath unresolved: " + raw + " in " + path)
                spelling, outcome = selected
            elif kind == "@loader_path":
                outcomes = {base + raw[len("@loader_path"):]: resolve(base + raw[len("@loader_path"):])
                            for base in sorted(loader_dirs)}
                if len({(row["state"], row["path"]) for row in outcomes.values()}) != 1:
                    raise Refused("@loader_path ambiguous: " + raw + " in " + path)
                spelling, outcome = sorted(outcomes.items())[0]
            elif kind == "@executable_path":
                spelling = executable_dir + raw[len("@executable_path"):]
                outcome = resolve(spelling)
            else:
                spelling, outcome = raw, resolve(raw)
            if outcome["state"] != "file":
                raise Refused("reference not a file: " + raw + " in " + path)
            target = outcome["path"]
            if target.startswith(SYSTEM_PREFIXES):
                raise Refused("non-system reference into the system tree: " + raw)
            for hop in outcome["hops"]:
                links[(hop["path"], hop["target"])] = hop
            owner, rel = tree_of(target, framework, venv)
            if owner is not None:
                if entries[owner].get(rel, {}).get("kind") != "file" or target not in known:
                    raise Refused("reference to an unbound or non-Mach-O tree file: " + target)
            elif target not in known:
                _, bound, head, _ = common.read_bytes(target, keep=False, prefix=4)
                if magic_kind(head) != "macho64":
                    raise Refused("external dependency not thin arm64 Mach-O: " + target)
                known[target] = ("external", bound)
                external[target] = bound
                queue.append(target)
            spellings.setdefault(target, set()).add(spelling)
            row = {"command": reference["command"], "raw": raw, "kind": "bound", "path": target,
                   "hops": outcome["hops"]}
            if candidates:
                row["candidates"] = candidates
            references.append(row)
        done[path] = {"tree": tree, "filetype": rules["filetype"], "id": rules["id"], "commands": rules["commands"],
                      "rpaths": rpaths, "references": references}
    for path, names in spellings.items():
        if path in done and names - {path}:
            done[path]["spellings"] = sorted(names)
    return {"images": done, "external": external, "links": [links[key] for key in sorted(links)]}, used, spellings


def parse_pyvenv(raw):
    values = {}
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            raise Refused("pyvenv.cfg line without =")
        key, value = (part.strip() for part in line.split("=", 1))
        if not key or key in values:
            raise Refused("pyvenv.cfg key")
        values[key] = value
    return values


def selection_record(venv, framework, framework_entries, venv_entries):
    short = posixpath.basename(framework)
    if not (re.fullmatch(r"3\.\d+", short) and posixpath.basename(posixpath.dirname(framework)) == "Versions"
            and posixpath.basename(posixpath.dirname(posixpath.dirname(framework))) == "Python.framework"):
        raise Refused("not a Python.framework version directory")
    launcher_name = "python" + short
    expected = framework + "/bin/" + launcher_name
    if framework_entries.get("bin/" + launcher_name, {}).get("kind") != "file":
        raise Refused("framework launcher missing")
    if framework_entries.get(PROCESS_IMAGE, {}).get("kind") != "file":
        raise Refused("process image missing")
    if venv_entries.get("bin/python", {}).get("kind") != "symlink" or \
            venv_entries.get("pyvenv.cfg", {}).get("kind") != "file":
        raise Refused("venv bin/python link or pyvenv.cfg missing")
    chain = resolve(venv + "/bin/python")
    if chain["state"] != "file" or chain["path"] != expected:
        raise Refused("venv python does not select the framework launcher")
    raw, binding, _, _ = common.read_bytes(venv + "/pyvenv.cfg")
    entry = venv_entries["pyvenv.cfg"]
    if binding != {key: entry[key] for key in ("sha256", "size_bytes", "mode")}:
        raise Refused("pyvenv.cfg changed")
    cfg = parse_pyvenv(raw)
    if not {"home", "include-system-site-packages", "version"} <= set(cfg) or \
            cfg["include-system-site-packages"] != "false" or \
            re.fullmatch(re.escape(short) + r"\.\d+", cfg["version"]) is None:
        raise Refused("pyvenv.cfg content")
    home = resolve(cfg["home"])
    if home["state"] != "directory":
        raise Refused("home is not a directory")
    home_launcher = resolve(cfg["home"].rstrip("/") + "/" + launcher_name)
    if home_launcher["state"] != "file" or home_launcher["path"] != expected:
        raise Refused("home does not select the framework launcher")
    executable = None
    if "executable" in cfg:
        executable = resolve(cfg["executable"])
        if executable["state"] != "file" or executable["path"] != expected:
            raise Refused("executable does not select the framework launcher")
    return {"launcher": venv + "/bin/python", "launcher_chain": chain, "pyvenv_cfg": cfg, "home_chain": home,
            "home_launcher_chain": home_launcher, "executable_chain": executable,
            "process_image": framework + "/" + PROCESS_IMAGE, "version_directory": short}


def lock_pins(raw):
    pins = {}
    for original in raw.decode("ascii").splitlines():
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if re.fullmatch(r"--hash=sha256:[0-9a-f]{64}(?:\s*\\)?", line):
            if not pins:
                raise Refused("hash line before a requirement")
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s\\]+)(?:\s+--hash=sha256:[0-9a-f]{64})*(?:\s*\\)?", line)
        if match is None or match[1] in pins:
            raise Refused("lock line: " + line)
        pins[match[1]] = match[2]
    return pins


def normal_name(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def verify_packages(venv, venv_entries, pins, short):
    site = "lib/python" + short + "/site-packages"
    if venv_entries.get(site, {}).get("kind") != "directory":
        raise Refused("no site-packages")
    meta_dirs = sorted(rel for rel, entry in venv_entries.items() if entry["kind"] == "directory"
                       and posixpath.dirname(rel) == site and rel.endswith((".dist-info", ".egg-info")))
    if not all(rel.endswith(".dist-info") for rel in meta_dirs):
        raise Refused(".egg-info present")
    wanted = {normal_name(name): (name, version) for name, version in pins.items()}
    packages, records, owned = {}, {}, {}
    for directory in meta_dirs:
        raw, _, _, _ = common.read_bytes(venv + "/" + directory + "/METADATA")
        header = raw.decode("utf-8").split("\n\n", 1)[0]
        names = re.findall(r"^Name: ([^\r\n]+)$", header, flags=re.MULTILINE)
        versions = re.findall(r"^Version: ([^\r\n]+)$", header, flags=re.MULTILINE)
        if len(names) != 1 or len(versions) != 1:
            raise Refused("METADATA header: " + directory)
        name, version = names[0].strip(), versions[0].strip()
        key = normal_name(name)
        if key not in wanted or key in packages or version != wanted[key][1]:
            raise Refused("unexpected package or version: " + name + " " + version)
        raw, _, _, _ = common.read_bytes(venv + "/" + directory + "/RECORD")
        hashed = unhashed = 0
        for row in csv.reader(io.StringIO(raw.decode("utf-8"), newline="")):
            if not row:
                continue
            if len(row) != 3:
                raise Refused("RECORD row width")
            path_field, hash_field, size_field = row
            if not path_field or path_field.startswith("/") or "\\" in path_field:
                raise Refused("RECORD path")
            rel = posixpath.normpath(site + "/" + path_field)
            if rel == ".." or rel.startswith("../") or rel.startswith("/"):
                raise Refused("RECORD path leaves the venv")
            entry = venv_entries.get(rel)
            if entry is None or entry["kind"] != "file":
                raise Refused("RECORD names a missing file: " + rel)
            if rel in owned:
                raise Refused("file owned twice: " + rel)
            if hash_field:
                algorithm, _, value = hash_field.partition("=")
                expected = base64.urlsafe_b64encode(bytes.fromhex(entry["sha256"])).rstrip(b"=").decode("ascii")
                if algorithm != "sha256" or value != expected or size_field != str(entry["size_bytes"]):
                    raise Refused("RECORD row disagrees: " + rel)
                hashed += 1
            else:
                if size_field != "" or not (rel == directory + "/RECORD" or
                                            (rel.endswith(".pyc") and "/__pycache__/" in "/" + rel)):
                    raise Refused("unhashed RECORD row: " + rel)
                unhashed += 1
            owned[rel] = key
        if owned.get(directory + "/RECORD") != key:
            raise Refused("RECORD does not list itself")
        packages[wanted[key][0]] = version
        records[wanted[key][0]] = {"dist_info": directory, "hashed_rows": hashed, "unhashed_rows": unhashed}
    unowned = sorted(rel for rel, entry in venv_entries.items() if entry["kind"] == "file" and inside(rel, site)
                     and rel not in owned)
    if unowned:
        raise Refused("unowned files under site-packages: " + ", ".join(unowned[:10]))
    if packages != pins:
        raise Refused("installed packages differ from the pins")
    return packages, records


def tree_stats(entries):
    files = [rel for rel, entry in entries.items() if entry["kind"] == "file"]
    return {"files": len(files),
            "bytecode_files": sum(1 for rel in files if rel.endswith(".pyc")),
            "pycache_directories": sum(1 for rel, entry in entries.items() if entry["kind"] == "directory"
                                       and posixpath.basename(rel) == "__pycache__"),
            "symlinks": sum(1 for entry in entries.values() if entry["kind"] == "symlink"),
            "directories": sum(1 for entry in entries.values() if entry["kind"] == "directory"),
            "file_bytes": sum(entries[rel]["size_bytes"] for rel in files)}


def differences(expected, actual, limit=50):
    rows = []
    if expected.get("schema") != actual.get("schema"):
        rows.append(["schema"])
    for tree in ("framework", "venv"):
        old, new = expected.get(tree, {}), actual.get(tree, {})
        if old.get("root") != new.get("root"):
            rows.append([tree, "root"])
        a, b = old.get("entries", {}), new.get("entries", {})
        for key in sorted(set(a) | set(b)):
            if a.get(key) != b.get(key):
                rows.append([tree, key, "missing" if key not in b else "added" if key not in a else "changed"])
    for key in sorted(set(expected.get("selection", {})) | set(actual.get("selection", {}))):
        if expected.get("selection", {}).get(key) != actual.get("selection", {}).get(key):
            rows.append(["selection", key])
    for part in ("images", "external"):
        a, b = expected.get("closure", {}).get(part, {}), actual.get("closure", {}).get(part, {})
        for key in sorted(set(a) | set(b)):
            if a.get(key) != b.get(key):
                rows.append([part, key])
    if expected.get("closure", {}).get("links") != actual.get("closure", {}).get("links"):
        rows.append(["links"])
    return {"count": len(rows), "first": rows[:limit]}


def main():
    common.start()
    parser = argparse.ArgumentParser()
    parser.add_argument("--venv", required=True)
    parser.add_argument("--framework", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--label", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    began = time.monotonic()
    out = {"schema": "w3.p36.plan-review-001.s03/1", "pid": os.getpid(),
           "boot_before": common.sysctl_text("kern.bootsessionuuid")}
    problems = []
    venv, framework = args.venv, args.framework
    for name, path in (("venv", venv), ("framework", framework)):
        if os.path.realpath(path) != path:
            problems.append({"rule": "NOT-CANONICAL", "path": path})
    framework_entries, framework_heads = walk(framework, problems)
    venv_entries, venv_heads = walk(venv, problems)
    images = {}
    for tree, heads, entries in (("framework", framework_heads, framework_entries), ("venv", venv_heads, venv_entries)):
        root = framework if tree == "framework" else venv
        for path, head in heads.items():
            kind = magic_kind(head)
            if kind is None:
                continue
            if kind != "macho64":
                problems.append({"rule": "MACHO-" + kind.upper(), "path": path})
                continue
            entry = entries[path[len(root) + 1:]]
            images[path] = (tree, {key: entry[key] for key in ("sha256", "size_bytes", "mode")})
    selection = selection_record(venv, framework, framework_entries, venv_entries)
    stats = {"parsed": 0}
    seed = {path: {path} for path in images}
    entries = {"framework": framework_entries, "venv": venv_entries}
    passes = 0
    for passes in range(1, 9):
        closure, used, final = closure_pass(images, framework, venv, entries, selection["process_image"], seed, stats)
        if all(used.get(path) == names for path, names in final.items()):
            break
        seed = {path: set(names) for path, names in final.items()}
    else:
        raise Refused("spellings did not stabilize")
    inventory = {"schema": SCHEMA, "framework": {"root": framework, "entries": framework_entries},
                 "venv": {"root": venv, "entries": venv_entries}, "selection": selection, "closure": closure}
    raw = common.canonical_json(inventory)
    digest = __import__("hashlib").sha256(raw).hexdigest()
    expected_raw, expected_binding, _, _ = common.read_bytes(args.expected)
    expected = common.strict_loads(expected_raw)

    lock_raw, lock_binding, _, _ = common.read_bytes(args.lock)
    pins = lock_pins(lock_raw)
    packages, records = verify_packages(venv, venv_entries, pins, selection["version_directory"])

    images_by = {}
    for path, image in closure["images"].items():
        key = image["tree"] + ":" + image["filetype"]
        images_by[key] = images_by.get(key, 0) + 1
    references = [ref for image in closure["images"].values() for ref in image["references"]]
    out.update({
        "inventory_sha256": digest, "inventory_bytes": len(raw),
        "expected": {"binding": expected_binding, "bytes_equal": raw == expected_raw},
        "differences": differences(expected, inventory),
        "problems": problems,
        "framework": tree_stats(framework_entries), "venv": tree_stats(venv_entries),
        "images": {"total": len(closure["images"]), "by_tree_and_type": images_by, "parsed": stats["parsed"]},
        "external": {path: binding for path, binding in closure["external"].items()},
        "closure_links": closure["links"],
        "rpath_entries": sum(len(image["rpaths"]) for image in closure["images"].values()),
        "references": {"system": sum(1 for ref in references if ref["kind"] == "system"),
                       "bound": sum(1 for ref in references if ref["kind"] == "bound"),
                       "loader_path": sum(1 for ref in references if ref["raw"].startswith("@loader_path/")),
                       "rpath": sum(1 for ref in references if ref["raw"].startswith("@rpath/")),
                       "executable_path": sum(1 for ref in references if ref["raw"].startswith("@executable_path/")),
                       "absolute_bound": sum(1 for ref in references if ref["kind"] == "bound"
                                             and not ref["raw"].startswith("@"))},
        "spelled_images": sorted(path for path, image in closure["images"].items() if "spellings" in image),
        "closure_passes": passes,
        "selection": {"launcher_hops": len(selection["launcher_chain"]["hops"]),
                      "home_hops": len(selection["home_chain"]["hops"]),
                      "home_launcher_hops": len(selection["home_launcher_chain"]["hops"]),
                      "executable_chain": None if selection["executable_chain"] is None
                      else len(selection["executable_chain"]["hops"]),
                      "pyvenv_cfg_keys": sorted(selection["pyvenv_cfg"])},
        "lock": {"binding": lock_binding, "pins": pins, "equal_to_contract_pins": pins == CONTRACT_PINS},
        "packages": packages, "records": records,
        "elapsed_s": round(time.monotonic() - began, 3),
        "boot_after": common.sysctl_text("kern.bootsessionuuid"),
        "refused_process_events": list(common.REFUSED_EVENTS)})
    digest_out = common.write_output(args.output, out, labels)
    print(labels(str({"inventory_sha256": digest, "bytes_equal": raw == expected_raw,
                      "differences": out["differences"]["count"], "problems": len(problems),
                      "packages_ok": True, "pins_equal_contract": pins == CONTRACT_PINS,
                      "output_sha256": digest_out})))


if __name__ == "__main__":
    main()
