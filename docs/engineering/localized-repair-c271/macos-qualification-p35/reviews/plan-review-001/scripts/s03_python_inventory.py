"""W3 plan review 001, script s03: the Python inventory recomputed from W3-OBSERVER section 5.

Standard library only; the observer is not imported. My own tree walk, link resolver, Mach-O
load-command reader, closure and package check build the document
ontokin.current-host-readback-python-inventory/0.2.0 = {schema, framework: {root, entries},
venv: {root, entries}, selection, closure}. Its digest is the SHA-256 of its canonical bytes
(sorted keys, compact separators, ASCII). The shapes of the selection and closure records follow
section 5 and the field names the observer records, so that the digest is comparable; every value
comes from this script's own reads. Starts nothing (audit hook); writes only its absent output.

Usage:
  python -I -S -B s03_python_inventory.py --venv V --framework F --frozen FROZEN.json --lock LOCK --output OUT.json
"""
import argparse
import base64
import csv
import hashlib
import io
import json
import os
import posixpath
import re
import stat
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

SCHEMA = "ontokin.current-host-readback-python-inventory/0.2.0"
PROCESS_IMAGE = "Resources/Python.app/Contents/MacOS/Python"
SYSTEM_PREFIXES = ("/usr/lib/", "/System/Library/")
PINS = {"attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1", "referencing": "0.37.0",
        "rpds-py": "2026.5.1", "typing_extensions": "4.16.0", "Pillow": "13.0.0"}
REQ = 0x80000000
# <mach-o/loader.h>
LC_NAMES = {0x1: "LC_SEGMENT", 0x2: "LC_SYMTAB", 0x3: "LC_SYMSEG", 0x4: "LC_THREAD", 0x5: "LC_UNIXTHREAD",
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
            0x33 | REQ: "LC_DYLD_EXPORTS_TRIE", 0x34 | REQ: "LC_DYLD_CHAINED_FIXUPS",
            0x35 | REQ: "LC_FILESET_ENTRY", 0x36: "LC_ATOM_INFO"}
FILETYPES = {1: "MH_OBJECT", 2: "MH_EXECUTE", 3: "MH_FVMLIB", 4: "MH_CORE", 5: "MH_PRELOAD", 6: "MH_DYLIB",
             7: "MH_DYLINKER", 8: "MH_BUNDLE", 9: "MH_DYLIB_STUB", 10: "MH_DSYM", 11: "MH_KEXT_BUNDLE",
             12: "MH_FILESET"}
NODE_LIST = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
             "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
             "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
             "LC_DYLD_EXPORTS_TRIE"}
PYTHON_LIST = NODE_LIST | {"LC_ID_DYLIB", "LC_RPATH"}
STRING_AT = {"LC_ID_DYLIB": 8, "LC_LOAD_DYLIB": 8, "LC_LOAD_WEAK_DYLIB": 8, "LC_REEXPORT_DYLIB": 8,
             "LC_LOAD_UPWARD_DYLIB": 8, "LC_LAZY_LOAD_DYLIB": 8, "LC_RPATH": 8, "LC_LOAD_DYLINKER": 8,
             "LC_ID_DYLINKER": 8, "LC_DYLD_ENVIRONMENT": 8}
SINGLE = {"LC_LOAD_DYLINKER", "LC_MAIN", "LC_UUID", "LC_SYMTAB", "LC_DYSYMTAB", "LC_CODE_SIGNATURE",
          "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE", "LC_FUNCTION_STARTS",
          "LC_DATA_IN_CODE", "LC_SOURCE_VERSION", "LC_ID_DYLIB"}
RULE_PROBLEMS = []


def mode_text(info):
    return "0o%03o" % stat.S_IMODE(info.st_mode)


def hash_file(path, prefix=0):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        assert stat.S_ISREG(before.st_mode), path
        digest, length, head = hashlib.sha256(), 0, b""
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            if len(head) < prefix:
                head += block[:prefix - len(head)]
            digest.update(block)
            length += len(block)
        after = os.fstat(fd)
        assert (before.st_size, before.st_mtime_ns, before.st_ino) == (after.st_size, after.st_mtime_ns,
                                                                         after.st_ino) == (length, before.st_mtime_ns,
                                                                                           before.st_ino), path
        return {"sha256": digest.hexdigest(), "size_bytes": length, "mode": mode_text(before)}, head
    finally:
        os.close(fd)


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


def walk(root, tree, images, problems):
    entries, pending = {}, [""]
    while pending:
        rel_dir = pending.pop()
        directory = root + "/" + rel_dir if rel_dir else root
        for name in sorted(os.listdir(directory)):
            rel = rel_dir + "/" + name if rel_dir else name
            path = root + "/" + rel
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                entries[rel] = {"kind": "symlink", "target": os.readlink(path)}
            elif stat.S_ISDIR(info.st_mode):
                entries[rel] = {"kind": "directory", "mode": mode_text(info)}
                pending.append(rel)
            elif stat.S_ISREG(info.st_mode):
                binding, head = hash_file(path, prefix=4)
                entries[rel] = {"kind": "file", **binding}
                kind = magic_kind(head)
                if kind == "macho64":
                    images[path] = (tree, binding)
                elif kind is not None:
                    problems.append({"path": path, "problem": "Mach-O kind " + kind})
            else:
                problems.append({"path": path, "problem": "special file"})
    return entries


def chain(path):
    pending = [p for p in path.split("/") if p]
    resolved, hops = "/", []
    while pending:
        name = pending.pop(0)
        if name == ".":
            continue
        if name == "..":
            resolved = posixpath.dirname(resolved)
            continue
        candidate = posixpath.join(resolved, name)
        try:
            info = os.lstat(candidate)
        except FileNotFoundError:
            return {"state": "absent", "path": candidate, "hops": hops}
        if stat.S_ISLNK(info.st_mode):
            target = os.readlink(candidate)
            hops.append({"path": candidate, "target": target})
            if target.startswith("/"):
                resolved = "/"
            pending = [p for p in target.split("/") if p] + pending
            continue
        if pending and not stat.S_ISDIR(info.st_mode):
            return {"state": "absent", "path": candidate + "/" + "/".join(pending), "hops": hops}
        resolved = candidate
    info = os.lstat(resolved)
    state = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "other"
    return {"state": state, "path": resolved, "hops": hops}


def load_commands(path, expected):
    binding, _ = hash_file(path)
    assert binding == expected, ("changed", path)
    with open(path, "rb") as f:
        header = f.read(32)
        magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _ = struct.unpack("<8I", header)
        table = f.read(sizeofcmds)
    assert magic == 0xFEEDFACF and len(table) == sizeofcmds, path
    commands, offset = [], 0
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", table, offset)
        body = table[offset:offset + size]
        name = LC_NAMES.get(cmd)
        row = {"cmd": cmd, "name": name, "size": size}
        if name in STRING_AT:
            at = struct.unpack_from("<I", body, STRING_AT[name])[0]
            row["path"] = body[at:body.index(b"\0", at)].decode("ascii")
        commands.append(row)
        offset += size
    assert offset == sizeofcmds, path
    return {"cputype": cputype, "cpusubtype": cpusubtype, "filetype": FILETYPES.get(filetype, "0x%08x" % filetype),
            "flags": flags, "commands": commands}


def at_kind(raw):
    for prefix in ("@rpath/", "@loader_path/", "@executable_path/"):
        if raw.startswith(prefix) and len(raw) > len(prefix):
            return prefix[:-1]
    return None


def python_rules(path, parsed):
    """W3-OBSERVER section 6.3 (the implemented rules), evaluated here; problems are recorded, not raised."""
    def bad(rule):
        RULE_PROBLEMS.append({"path": path, "rule": rule})
    if parsed["cputype"] != 0x0100000C or parsed["cpusubtype"] != 0:
        bad("MACHO-CPU")
    if parsed["filetype"] not in ("MH_EXECUTE", "MH_DYLIB", "MH_BUNDLE"):
        bad("MACHO-FILETYPE")
    identity, rpaths, references, counts = None, [], [], {}
    for row in parsed["commands"]:
        name = row["name"]
        if name is not None:
            counts[name] = counts.get(name, 0) + 1
        if name in ("LC_DYLD_ENVIRONMENT", "LC_LOAD_UPWARD_DYLIB"):
            bad("MACHO-REFUSED-COMMAND")
        elif name not in PYTHON_LIST:
            bad("MACHO-COMMAND")
        if name == "LC_LOAD_DYLINKER" and row["path"] != "/usr/lib/dyld":
            bad("MACHO-DYLINKER")
        elif name == "LC_ID_DYLIB":
            identity = row["path"]
        elif name == "LC_RPATH":
            p = row["path"]
            if p.startswith("@"):
                if not (p.startswith(("@loader_path/", "@executable_path/")) or p in ("@loader_path",
                                                                                       "@executable_path")):
                    bad("MACHO-RPATH")
            elif not (p.startswith("/") and posixpath.normpath(p) == p and not p.startswith("//")):
                bad("MACHO-RPATH")
            rpaths.append(p)
        elif name in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB"):
            p = row["path"]
            if p.startswith("@"):
                if at_kind(p) is None:
                    bad("MACHO-AT-PATH")
            elif not (p.startswith("/") and posixpath.normpath(p) == p and not p.startswith("//")):
                bad("MACHO-DYLIB-PATH")
            references.append({"command": name, "path": p})
    if any(n in SINGLE and c > 1 for n, c in counts.items()):
        bad("MACHO-DUPLICATE")
    if parsed["filetype"] == "MH_EXECUTE":
        if counts.get("LC_LOAD_DYLINKER") != 1 or counts.get("LC_MAIN") != 1:
            bad("MACHO-STRUCTURE")
    elif "LC_MAIN" in counts or "LC_LOAD_DYLINKER" in counts:
        bad("MACHO-STRUCTURE")
    if parsed["filetype"] == "MH_DYLIB" and counts.get("LC_ID_DYLIB") != 1:
        bad("MACHO-STRUCTURE")
    return {"filetype": parsed["filetype"], "id": identity, "rpaths": rpaths, "references": references,
            "commands": [row["name"] for row in parsed["commands"]]}


def tree_of(path, framework, venv):
    for name, root in (("framework", framework), ("venv", venv)):
        if path == root or path.startswith(root + "/"):
            return name, path[len(root) + 1:]
    return None, None


def search_dir(raw, loader_dirs, executable_dir):
    if raw.startswith("@loader_path"):
        bases, suffix = sorted(loader_dirs), raw[len("@loader_path"):]
    elif raw.startswith("@executable_path"):
        bases, suffix = [executable_dir], raw[len("@executable_path"):]
    else:
        bases, suffix = [""], raw
    outcomes = [chain(base + suffix if base else suffix) for base in bases]
    if len({(o["state"], o["path"]) for o in outcomes}) != 1:
        RULE_PROBLEMS.append({"raw": raw, "rule": "MACHO-AT-AMBIGUOUS"})
    return {"raw": raw, **outcomes[0]}


def one_pass(images, framework, venv, entries, process_image, seed):
    known = dict(images)
    spellings = {p: set(n) for p, n in seed.items()}
    used, queue, out_images, external, links = {}, sorted(images), {}, {}, {}
    while queue:
        path = queue.pop(0)
        if path in out_images:
            continue
        tree, binding = known[path]
        rules = python_rules(path, load_commands(path, binding))
        spellings.setdefault(path, set())
        used[path] = set(spellings[path])
        loader_dirs = {posixpath.dirname(path)} | {posixpath.dirname(n) for n in spellings[path]}
        executable_dir = posixpath.dirname(path if rules["filetype"] == "MH_EXECUTE" else process_image)
        rpaths = [search_dir(raw, loader_dirs, executable_dir) for raw in rules["rpaths"]]
        for row in rpaths:
            for hop in row["hops"]:
                links[(hop["path"], hop["target"])] = hop
        references = []
        for ref in rules["references"]:
            raw = ref["path"]
            if not raw.startswith("@") and raw.startswith(SYSTEM_PREFIXES):
                references.append({"command": ref["command"], "raw": raw, "kind": "system"})
                continue
            kind, candidates = at_kind(raw), []
            if kind == "@rpath":
                selected = None
                for row in rpaths:
                    candidate = row["path"] + raw[len("@rpath"):]
                    outcome = chain(candidate) if row["state"] == "directory" else {"state": "absent",
                                                                                   "path": candidate, "hops": []}
                    candidates.append({"rpath": row["raw"], "candidate": candidate, "state": outcome["state"]})
                    if outcome["state"] != "absent":
                        selected = (candidate, outcome)
                        break
                if selected is None:
                    RULE_PROBLEMS.append({"path": path, "raw": raw, "rule": "MACHO-AT-UNRESOLVED"})
                    continue
                spelling, outcome = selected
            elif kind == "@loader_path":
                outcomes = {base + raw[len("@loader_path"):]: chain(base + raw[len("@loader_path"):])
                            for base in sorted(loader_dirs)}
                if len({(o["state"], o["path"]) for o in outcomes.values()}) != 1:
                    RULE_PROBLEMS.append({"path": path, "raw": raw, "rule": "MACHO-AT-AMBIGUOUS"})
                spelling, outcome = sorted(outcomes.items())[0]
            elif kind == "@executable_path":
                spelling = executable_dir + raw[len("@executable_path"):]
                outcome = chain(spelling)
            else:
                spelling, outcome = raw, chain(raw)
            if outcome["state"] != "file":
                RULE_PROBLEMS.append({"path": path, "raw": raw, "rule": "unresolved reference"})
                continue
            target = outcome["path"]
            if target.startswith(SYSTEM_PREFIXES):
                RULE_PROBLEMS.append({"path": path, "raw": raw, "rule": "MACHO-AT-PATH (into the system tree)"})
            for hop in outcome["hops"]:
                links[(hop["path"], hop["target"])] = hop
            owner, rel = tree_of(target, framework, venv)
            if owner is not None:
                if entries[owner].get(rel, {}).get("kind") != "file" or target not in known:
                    RULE_PROBLEMS.append({"path": path, "raw": raw, "rule": "tree target not an inventoried image"})
            elif target not in known:
                bound, head = hash_file(target, prefix=4)
                if magic_kind(head) != "macho64":
                    RULE_PROBLEMS.append({"path": target, "rule": "MACHO-DEPENDENCY-NOT-MACHO"})
                known[target] = ("external", bound)
                external[target] = bound
                queue.append(target)
            spellings.setdefault(target, set()).add(spelling)
            row = {"command": ref["command"], "raw": raw, "kind": "bound", "path": target, "hops": outcome["hops"]}
            if candidates:
                row["candidates"] = candidates
            references.append(row)
        out_images[path] = {"tree": tree, "filetype": rules["filetype"], "id": rules["id"],
                            "commands": rules["commands"], "rpaths": rpaths, "references": references}
    for path, names in spellings.items():
        if path in out_images and names - {path}:
            out_images[path]["spellings"] = sorted(names)
    return {"images": out_images, "external": external, "links": [links[k] for k in sorted(links)]}, used, spellings


def closure(images, framework, venv, entries, process_image):
    seed = {p: {p} for p in images}
    for passes in range(1, 9):
        result, used, final = one_pass(images, framework, venv, entries, process_image, seed)
        if all(used.get(p) == n for p, n in final.items()):
            return result, passes
        seed = {p: set(n) for p, n in final.items()}
    raise RuntimeError("spellings did not stabilize")


def selection(venv, framework, fw_entries, venv_entries):
    short = posixpath.basename(framework)
    launcher_name = "python" + short
    expected = framework + "/bin/" + launcher_name
    launcher = venv + "/bin/python"
    launcher_chain = chain(launcher)
    cfg = {}
    with open(venv + "/pyvenv.cfg", "rb") as f:
        for line in f.read().decode("utf-8").splitlines():
            if line.strip():
                k, v = (s.strip() for s in line.split("=", 1))
                cfg[k] = v
    home = chain(cfg["home"])
    home_launcher = chain(cfg["home"].rstrip("/") + "/" + launcher_name)
    executable = chain(cfg["executable"]) if "executable" in cfg else None
    checks = {
        "framework launcher and process image are inventoried files":
            fw_entries.get("bin/" + launcher_name, {}).get("kind") == "file"
            and fw_entries.get(PROCESS_IMAGE, {}).get("kind") == "file",
        "venv bin/python is a link and pyvenv.cfg a file":
            venv_entries.get("bin/python", {}).get("kind") == "symlink"
            and venv_entries.get("pyvenv.cfg", {}).get("kind") == "file",
        "bin/python resolves, hop by hop, to the framework launcher":
            launcher_chain["state"] == "file" and launcher_chain["path"] == expected,
        "include-system-site-packages is false": cfg.get("include-system-site-packages") == "false",
        "pyvenv.cfg version is 3.12.x": re.fullmatch(re.escape(short) + r"\.\d+", cfg.get("version", "")) is not None,
        "home is a directory whose python3.12 resolves to the launcher":
            home["state"] == "directory" and home_launcher["state"] == "file" and home_launcher["path"] == expected,
        "executable resolves to the launcher":
            executable is None or (executable["state"] == "file" and executable["path"] == expected)}
    record = {"launcher": launcher, "launcher_chain": launcher_chain, "pyvenv_cfg": cfg, "home_chain": home,
              "home_launcher_chain": home_launcher, "executable_chain": executable,
              "process_image": framework + "/" + PROCESS_IMAGE, "version_directory": short}
    return record, checks


def lock_pins(raw):
    pins = {}
    for original in raw.decode("ascii").splitlines():
        line = original.strip()
        if not line or line.startswith("#") or line.startswith("--hash="):
            continue
        m = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s\\]+)(?:\s+--hash=sha256:[0-9a-f]{64})*(?:\s*\\)?", line)
        if m is None:
            raise ValueError("unsupported lock line: " + line)
        pins[m[1]] = m[2]
    return pins


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def packages(venv, venv_entries, pins, short):
    site = "lib/python" + short + "/site-packages"
    dist = sorted(r for r, e in venv_entries.items() if e["kind"] == "directory" and posixpath.dirname(r) == site
                  and r.endswith((".dist-info", ".egg-info")))
    wanted = {normalized(n): (n, v) for n, v in pins.items()}
    found, records, owned, problems = {}, {}, {}, []
    for d in dist:
        with open(venv + "/" + d + "/METADATA", "rb") as f:
            header = f.read().decode("utf-8").split("\n\n", 1)[0]
        names = re.findall(r"^Name: ([^\r\n]+)$", header, flags=re.MULTILINE)
        versions = re.findall(r"^Version: ([^\r\n]+)$", header, flags=re.MULTILINE)
        name, version = names[0].strip(), versions[0].strip()
        key = normalized(name)
        if key not in wanted or key in found or version != wanted[key][1] or len(names) != 1 or len(versions) != 1:
            problems.append({"dist_info": d, "problem": "unexpected package or version", "name": name,
                             "version": version})
        with open(venv + "/" + d + "/RECORD", "rb") as f:
            rows = list(csv.reader(io.StringIO(f.read().decode("utf-8"), newline="")))
        hashed = unhashed = 0
        for row in rows:
            if not row:
                continue
            rel = posixpath.normpath(site + "/" + row[0])
            entry = venv_entries.get(rel)
            if len(row) != 3 or entry is None or entry["kind"] != "file" or rel in owned:
                problems.append({"dist_info": d, "row": row[0], "problem": "row names no inventoried file once"})
                continue
            if row[1]:
                algorithm, _, value = row[1].partition("=")
                expected = base64.urlsafe_b64encode(bytes.fromhex(entry["sha256"])).rstrip(b"=").decode("ascii")
                if algorithm != "sha256" or value != expected or row[2] != str(entry["size_bytes"]):
                    problems.append({"dist_info": d, "row": row[0], "problem": "hash or size differs"})
                hashed += 1
            else:
                if not (row[2] == "" and (rel == d + "/RECORD" or (rel.endswith(".pyc") and "/__pycache__/" in
                                                                  "/" + rel))):
                    problems.append({"dist_info": d, "row": row[0], "problem": "unhashed row not admitted"})
                unhashed += 1
            owned[rel] = key
        found[wanted.get(key, (name,))[0]] = version
        records[wanted.get(key, (name,))[0]] = {"dist_info": d, "hashed_rows": hashed, "unhashed_rows": unhashed}
    unowned = sorted(r for r, e in venv_entries.items() if e["kind"] == "file" and r.startswith(site + "/")
                     and r not in owned)
    return {"packages": found, "records": records, "unowned": unowned, "problems": problems,
            "equals_pins": found == pins and not unowned and not problems}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def figures(entries):
    out = {"file": 0, "symlink": 0, "directory": 0, "bytecode": 0, "file_bytes": 0, "pycache_directories": 0}
    for rel, e in entries.items():
        out[e["kind"]] += 1
        if e["kind"] == "file":
            out["file_bytes"] += e["size_bytes"]
            if rel.endswith(".pyc"):
                out["bytecode"] += 1
        if e["kind"] == "directory" and posixpath.basename(rel) == "__pycache__":
            out["pycache_directories"] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venv", required=True)
    ap.add_argument("--framework", required=True)
    ap.add_argument("--frozen", required=True)
    ap.add_argument("--lock", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    t0 = time.time()
    venv, framework = a.venv, a.framework
    assert os.path.realpath(venv) == venv and os.path.realpath(framework) == framework
    images, problems = {}, []
    fw_entries = walk(framework, "framework", images, problems)
    venv_entries = walk(venv, "venv", images, problems)
    sel, sel_checks = selection(venv, framework, fw_entries, venv_entries)
    clo, passes = closure(images, framework, venv, {"framework": fw_entries, "venv": venv_entries},
                          sel["process_image"])
    mine = {"schema": SCHEMA, "framework": {"root": framework, "entries": fw_entries},
            "venv": {"root": venv, "entries": venv_entries}, "selection": sel, "closure": clo}
    mine_raw = canonical(mine)
    with open(a.frozen, "rb") as f:
        frozen_raw = f.read()
    frozen = json.loads(frozen_raw)
    parts = {
        "schema": frozen.get("schema") == mine["schema"],
        "framework.root": frozen["framework"]["root"] == framework,
        "framework.entries": frozen["framework"]["entries"] == fw_entries,
        "venv.root": frozen["venv"]["root"] == venv,
        "venv.entries": frozen["venv"]["entries"] == venv_entries,
        "selection": frozen["selection"] == sel,
        "closure.images": frozen["closure"]["images"] == clo["images"],
        "closure.external": frozen["closure"]["external"] == clo["external"],
        "closure.links": frozen["closure"]["links"] == clo["links"],
        "top-level keys": set(frozen) == set(mine)}
    differences = {}
    for tree, ent in (("framework", fw_entries), ("venv", venv_entries)):
        old = frozen[tree]["entries"]
        differences[tree] = {"missing": sorted(set(old) - set(ent))[:20], "added": sorted(set(ent) - set(old))[:20],
                             "changed": sorted(k for k in set(old) & set(ent) if old[k] != ent[k])[:20]}
    differences["images"] = sorted(k for k in set(frozen["closure"]["images"]) | set(clo["images"])
                                   if frozen["closure"]["images"].get(k) != clo["images"].get(k))[:20]
    with open(a.lock, "rb") as f:
        pins = lock_pins(f.read())
    pkg = packages(venv, venv_entries, pins, sel["version_directory"])
    image_types = {}
    for row in clo["images"].values():
        image_types[row["tree"] + ":" + row["filetype"]] = image_types.get(row["tree"] + ":" + row["filetype"], 0) + 1
    at_refs = sum(1 for row in clo["images"].values() for r in row["references"] if r["raw"].startswith("@"))
    out = {
        "script": os.path.basename(__file__), "argv": sys.argv, "pid": os.getpid(), "ppid": os.getppid(),
        "process_events": EVENTS, "elapsed_s": round(time.time() - t0, 3),
        "digest_mine": hashlib.sha256(mine_raw).hexdigest(), "canonical_bytes_mine": len(mine_raw),
        "digest_frozen_file": hashlib.sha256(frozen_raw).hexdigest(), "frozen_bytes": len(frozen_raw),
        "frozen_is_canonical": canonical(frozen) == frozen_raw, "bytes_identical": mine_raw == frozen_raw,
        "parts_equal": parts, "differences": differences, "walk_problems": problems, "rule_problems": RULE_PROBLEMS,
        "selection_checks": sel_checks, "closure_passes": passes,
        "figures": {"framework": figures(fw_entries), "venv": figures(venv_entries), "images": len(clo["images"]),
                    "images_by_tree_and_type": image_types, "external": len(clo["external"]),
                    "external_paths": sorted(clo["external"]), "closure_links": len(clo["links"]),
                    "selection_hops": len(sel["launcher_chain"]["hops"]), "at_references": at_refs,
                    "rpaths": sum(len(r["rpaths"]) for r in clo["images"].values()),
                    "spelled_images": sorted(p for p, r in clo["images"].items() if "spellings" in r)},
        "selection": {"launcher_chain": sel["launcher_chain"], "home_chain": sel["home_chain"],
                      "home_launcher_hops": len(sel["home_launcher_chain"]["hops"]),
                      "executable_hops": None if sel["executable_chain"] is None else len(sel["executable_chain"]["hops"]),
                      "pyvenv_cfg": {k: v for k, v in sel["pyvenv_cfg"].items() if k != "command"}},
        "lock_pins": pins, "lock_equals_contract_pins": pins == PINS, "packages": pkg}
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({k: out[k] for k in ("digest_mine", "digest_frozen_file", "bytes_identical", "parts_equal",
                                          "closure_passes", "elapsed_s", "process_events")}, indent=1))
    print(json.dumps({"rule_problems": len(RULE_PROBLEMS), "walk_problems": len(problems),
                      "selection_checks": all(sel_checks.values()), "packages_ok": pkg["equals_pins"],
                      "lock_equals_contract_pins": pins == PINS}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
