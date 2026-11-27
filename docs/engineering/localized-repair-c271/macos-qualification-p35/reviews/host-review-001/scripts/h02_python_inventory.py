"""HOST review 001, script h02: the Python installation inventory, recomputed from W3-OBSERVER section 5.

Run as: <worktree>/.venv/bin/python -I -S -B h02_python_inventory.py --host H --output OUT
It walks both trees without following a link, recomputes the selection chain and the Mach-O closure
with this review's own reader and resolver, serializes the document canonically and compares its bytes
and digest with the frozen inventory and with HOST. It also recomputes the packages and RECORD counts,
the interpreter facts of a process launched as the observer was, and lists every LC_RPATH entry (N-06).
"""
import argparse
import base64
import csv
import ctypes
import importlib.util
import io
import json
import os
import posixpath
import re
import stat
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))
_spec = importlib.util.spec_from_file_location("h_common", HERE + "/h_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

SCHEMA = "ontokin.current-host-readback-python-inventory/0.2.0"
SYSTEM = ("/usr/lib/", "/System/Library/")
AT = ("@rpath/", "@loader_path/", "@executable_path/")
PROCESS_IMAGE = "Resources/Python.app/Contents/MacOS/Python"
PY_FILE_TYPES = {"MH_EXECUTE", "MH_DYLIB", "MH_BUNDLE"}
NODE_ALLOWED = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
                "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
                "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
                "LC_DYLD_EXPORTS_TRIE"}
PY_ALLOWED = NODE_ALLOWED | {"LC_ID_DYLIB", "LC_RPATH"}
SINGLE = {"LC_LOAD_DYLINKER", "LC_MAIN", "LC_UUID", "LC_SYMTAB", "LC_DYSYMTAB", "LC_CODE_SIGNATURE",
          "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE", "LC_FUNCTION_STARTS",
          "LC_DATA_IN_CODE", "LC_SOURCE_VERSION", "LC_ID_DYLIB"}
PINS = {"attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1", "referencing": "0.37.0",
        "rpds-py": "2026.5.1", "typing_extensions": "4.16.0", "Pillow": "13.0.0"}
FLAGS = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
         "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated", "dev_mode",
         "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
CHECKS = []
PROBLEMS = []


def check(cid, what, ok, **details):
    CHECKS.append({"id": cid, "what": what, "passed": bool(ok), **({"details": details} if details else {})})


def inside(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def walk(root):
    entries, images, pending = {}, {}, [""]
    while pending:
        rel = pending.pop()
        directory = root + "/" + rel if rel else root
        for name in sorted(os.listdir(directory)):
            r = rel + "/" + name if rel else name
            path = root + "/" + r
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                entries[r] = {"kind": "symlink", "target": os.readlink(path)}
            elif stat.S_ISDIR(info.st_mode):
                entries[r] = {"kind": "directory", "mode": C.mode_text(info.st_mode)}
                pending.append(r)
            elif stat.S_ISREG(info.st_mode):
                _, facts, head = C.read_bound(path, prefix=4)
                entries[r] = {"kind": "file", **C.binding(facts)}
                kind = C.magic_kind(head)
                if kind is not None:
                    if kind != "macho64":
                        PROBLEMS.append("non-thin or non-64-bit Mach-O in a tree: " + path)
                    images[path] = C.binding(facts)
            else:
                PROBLEMS.append("special file: " + path)
    return entries, images


def parse_cfg(raw):
    values = {}
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            key, value = (part.strip() for part in line.split("=", 1))
            values[key] = value
    return values


def selection(venv, framework):
    short = posixpath.basename(framework)
    name = "python" + short
    cfg = parse_cfg(C.read_bound(venv + "/pyvenv.cfg", keep=True)[0])
    result = {"launcher": venv + "/bin/python", "launcher_chain": C.resolve_chain(venv + "/bin/python"),
              "pyvenv_cfg": cfg, "home_chain": C.resolve_chain(cfg["home"]),
              "home_launcher_chain": C.resolve_chain(cfg["home"].rstrip("/") + "/" + name),
              "executable_chain": C.resolve_chain(cfg["executable"]) if "executable" in cfg else None,
              "process_image": framework + "/" + PROCESS_IMAGE, "version_directory": short}
    expected = framework + "/bin/" + name
    check("S1", "the venv's python, pyvenv.cfg's home and executable all select <framework>/bin/python3.12",
          result["launcher_chain"]["state"] == "file" and result["launcher_chain"]["path"] == expected
          and result["home_chain"]["state"] == "directory"
          and result["home_launcher_chain"]["state"] == "file" and result["home_launcher_chain"]["path"] == expected
          and (result["executable_chain"] is None or result["executable_chain"]["path"] == expected))
    check("S2", "include-system-site-packages is false and version is 3.12.x",
          cfg.get("include-system-site-packages") == "false" and re.fullmatch(r"3\.12\.\d+", cfg.get("version", "")))
    return result


def at_kind(path):
    for prefix in AT:
        if path.startswith(prefix) and len(path) > len(prefix):
            return prefix[:-1]
    return None


def image_rules(path, summary):
    names = [row["name"] for row in summary["commands"]]
    if summary["cputype"] != "0x0100000c" or summary["cpusubtype"] != "0x00000000":
        PROBLEMS.append("cpu type or subtype: " + path)
    if summary["filetype"] not in PY_FILE_TYPES:
        PROBLEMS.append("file type " + summary["filetype"] + ": " + path)
    for row in summary["commands"]:
        if row["name"] not in PY_ALLOWED:
            PROBLEMS.append("command outside the Python allow-list (%s): %s" % (row["name"] or row["cmd"], path))
        if row["name"] == "LC_LOAD_DYLINKER" and row["path"] != "/usr/lib/dyld":
            PROBLEMS.append("dylinker: " + path)
        if row["name"] == "LC_RPATH":
            raw = row["path"]
            if raw.startswith("@") and not (raw in ("@loader_path", "@executable_path")
                                            or raw.startswith(("@loader_path/", "@executable_path/"))):
                PROBLEMS.append("rpath form: " + path)
        if row["name"] in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB"):
            raw = row["path"]
            if raw.startswith("@") and at_kind(raw) is None:
                PROBLEMS.append("@ form: " + path)
            if not raw.startswith("@") and posixpath.normpath(raw) != raw:
                PROBLEMS.append("reference not normalized: " + path)
    for name in SINGLE:
        if names.count(name) > 1:
            PROBLEMS.append("duplicate " + name + ": " + path)
    if summary["filetype"] == "MH_EXECUTE":
        if names.count("LC_MAIN") != 1 or names.count("LC_LOAD_DYLINKER") != 1:
            PROBLEMS.append("executable structure: " + path)
    elif "LC_MAIN" in names or "LC_LOAD_DYLINKER" in names:
        PROBLEMS.append("non-executable carries LC_MAIN or a dylinker: " + path)
    if summary["filetype"] == "MH_DYLIB" and names.count("LC_ID_DYLIB") != 1:
        PROBLEMS.append("dylib without one LC_ID_DYLIB: " + path)
    ids = [row["path"] for row in summary["commands"] if row["name"] == "LC_ID_DYLIB"]
    return {"filetype": summary["filetype"], "id": ids[0] if ids else None,
            "rpaths": [row["path"] for row in summary["commands"] if row["name"] == "LC_RPATH"],
            "references": [{"command": row["name"], "path": row["path"]} for row in summary["commands"]
                           if row["name"] in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB")],
            "commands": names}


def search_dir(raw, loader_dirs, exe_dir):
    if raw.startswith("@loader_path"):
        bases, suffix = sorted(loader_dirs), raw[len("@loader_path"):]
    elif raw.startswith("@executable_path"):
        bases, suffix = [exe_dir], raw[len("@executable_path"):]
    else:
        bases, suffix = [""], raw
    outcomes = [C.resolve_chain(base + suffix if base else suffix) for base in bases]
    if len({(o["state"], o["path"]) for o in outcomes}) != 1:
        PROBLEMS.append("@loader_path rpath ambiguous: " + raw)
    return {"raw": raw, **outcomes[0]}


def one_pass(images, framework, venv, entries, process_image, seed, parsed):
    known = dict(images)
    spellings = {p: set(n) for p, n in seed.items()}
    used, queue, result, external, links = {}, sorted(images), {}, {}, {}
    while queue:
        path = queue.pop(0)
        if path in result:
            continue
        tree, bound = known[path]
        if path not in parsed:
            facts, summary, problems = C.read_thin_macho(path)
            if C.binding(facts) != bound:
                PROBLEMS.append("image changed after it was listed: " + path)
            PROBLEMS.extend(problems)
            parsed[path] = image_rules(path, summary)
        rules = parsed[path]
        spellings.setdefault(path, set())
        used[path] = set(spellings[path])
        loader_dirs = {posixpath.dirname(path)} | {posixpath.dirname(n) for n in spellings[path]}
        exe_dir = posixpath.dirname(path if rules["filetype"] == "MH_EXECUTE" else process_image)
        rpaths = [search_dir(raw, loader_dirs, exe_dir) for raw in rules["rpaths"]]
        for row in rpaths:
            for hop in row["hops"]:
                links[(hop["path"], hop["target"])] = hop
        references = []
        for ref in rules["references"]:
            raw = ref["path"]
            if not raw.startswith("@") and raw.startswith(SYSTEM):
                references.append({"command": ref["command"], "raw": raw, "kind": "system"})
                continue
            kind, candidates = at_kind(raw), []
            if kind == "@rpath":
                chosen = None
                for row in rpaths:
                    candidate = row["path"] + raw[len("@rpath"):]
                    outcome = C.resolve_chain(candidate) if row["state"] == "directory" else \
                        {"state": "absent", "path": candidate, "hops": []}
                    candidates.append({"rpath": row["raw"], "candidate": candidate, "state": outcome["state"]})
                    if outcome["state"] != "absent":
                        chosen = (candidate, outcome)
                        break
                if chosen is None:
                    PROBLEMS.append("@rpath unresolved: " + raw)
                    continue
                spelling, outcome = chosen
            elif kind == "@loader_path":
                outcomes = {base + raw[len("@loader_path"):]: C.resolve_chain(base + raw[len("@loader_path"):])
                            for base in sorted(loader_dirs)}
                if len({(o["state"], o["path"]) for o in outcomes.values()}) != 1:
                    PROBLEMS.append("@loader_path ambiguous: " + raw)
                spelling, outcome = sorted(outcomes.items())[0]
            elif kind == "@executable_path":
                spelling = exe_dir + raw[len("@executable_path"):]
                outcome = C.resolve_chain(spelling)
            else:
                spelling, outcome = raw, C.resolve_chain(raw)
            if outcome["state"] != "file":
                PROBLEMS.append("reference does not resolve to a file: " + raw + " in " + path)
                continue
            target = outcome["path"]
            if target.startswith(SYSTEM):
                PROBLEMS.append("non-system reference resolves into the system tree: " + raw)
            for hop in outcome["hops"]:
                links[(hop["path"], hop["target"])] = hop
            owner = "framework" if inside(target, framework) else "venv" if inside(target, venv) else None
            if owner is not None:
                rel = target[len(framework if owner == "framework" else venv) + 1:]
                if entries[owner].get(rel, {}).get("kind") != "file" or target not in known:
                    PROBLEMS.append("reference to an unbound or non-Mach-O tree path: " + target)
            elif target not in known:
                _, facts, head = C.read_bound(target, prefix=4)
                if C.magic_kind(head) != "macho64":
                    PROBLEMS.append("external dependency is not thin arm64 Mach-O: " + target)
                known[target] = ("external", C.binding(facts))
                external[target] = C.binding(facts)
                queue.append(target)
            spellings.setdefault(target, set()).add(spelling)
            row = {"command": ref["command"], "raw": raw, "kind": "bound", "path": target, "hops": outcome["hops"]}
            if candidates:
                row["candidates"] = candidates
            references.append(row)
        result[path] = {"tree": tree, "filetype": rules["filetype"], "id": rules["id"], "commands": rules["commands"],
                        "rpaths": rpaths, "references": references}
    for path, names in spellings.items():
        if path in result and names - {path}:
            result[path]["spellings"] = sorted(names)
    return {"images": result, "external": external, "links": [links[k] for k in sorted(links)]}, used, spellings


def closure(images, framework, venv, entries, process_image):
    seed, parsed = {p: {p} for p in images}, {}
    for passes in range(1, 9):
        value, used, final = one_pass(images, framework, venv, entries, process_image, seed, parsed)
        if all(used.get(p) == n for p, n in final.items()):
            return value, passes
        seed = {p: set(n) for p, n in final.items()}
    raise ValueError("spellings did not stabilize")


def inventory(venv, framework):
    fw_entries, fw_images = walk(framework)
    venv_entries, venv_images = walk(venv)
    images = {p: ("framework", b) for p, b in fw_images.items()}
    images.update({p: ("venv", b) for p, b in venv_images.items()})
    sel = selection(venv, framework)
    clo, passes = closure(images, framework, venv, {"framework": fw_entries, "venv": venv_entries},
                          sel["process_image"])
    doc = {"schema": SCHEMA, "framework": {"root": framework, "entries": fw_entries},
           "venv": {"root": venv, "entries": venv_entries}, "selection": sel, "closure": clo}
    return doc, passes


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def packages(venv, venv_entries):
    site = "lib/python3.12/site-packages"
    dirs = sorted(rel for rel, e in venv_entries.items() if e["kind"] == "directory"
                  and posixpath.dirname(rel) == site and rel.endswith((".dist-info", ".egg-info")))
    wanted = {norm(k): k for k in PINS}
    found, records, owned = {}, {}, {}
    for directory in dirs:
        meta = C.read_bound(venv + "/" + directory + "/METADATA", keep=True)[0].decode("utf-8").split("\n\n", 1)[0]
        name = re.findall(r"^Name: ([^\r\n]+)$", meta, flags=re.M)[0].strip()
        version = re.findall(r"^Version: ([^\r\n]+)$", meta, flags=re.M)[0].strip()
        key = norm(name)
        rows = list(csv.reader(io.StringIO(C.read_bound(venv + "/" + directory + "/RECORD", keep=True)[0]
                                           .decode("utf-8"), newline="")))
        hashed = unhashed = 0
        for row in rows:
            if not row:
                continue
            rel = posixpath.normpath(site + "/" + row[0])
            entry = venv_entries.get(rel)
            if entry is None or entry["kind"] != "file" or rel in owned:
                PROBLEMS.append("RECORD row names a missing or doubly owned file: " + rel)
                continue
            if row[1]:
                algorithm, _, value = row[1].partition("=")
                expected = base64.urlsafe_b64encode(bytes.fromhex(entry["sha256"])).rstrip(b"=").decode("ascii")
                if algorithm != "sha256" or value != expected or row[2] != str(entry["size_bytes"]):
                    PROBLEMS.append("RECORD row disagrees with the file: " + rel)
                hashed += 1
            else:
                if not (rel == directory + "/RECORD" or (rel.endswith(".pyc") and "/__pycache__/" in "/" + rel)):
                    PROBLEMS.append("unhashed row for a file that must be hashed: " + rel)
                unhashed += 1
            owned[rel] = key
        pin = wanted.get(key)
        if pin is None:
            PROBLEMS.append("unexpected package " + name)
            continue
        found[pin] = version
        records[pin] = {"dist_info": directory, "record": {k: venv_entries[directory + "/RECORD"][k]
                                                           for k in ("sha256", "size_bytes", "mode")},
                        "hashed_rows": hashed, "unhashed_rows": unhashed}
    unowned = sorted(rel for rel, e in venv_entries.items() if e["kind"] == "file" and inside(rel, site)
                     and rel not in owned)
    return found, records, unowned


def process_image():
    lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    fn = lib.proc_pidpath
    fn.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    fn.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(4096)
    length = fn(os.getpid(), buf, 4096)
    return os.fsdecode(buf.raw[:length])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = {"script": "h02_python_inventory.py", "process": C.process_facts()}
    host = json.loads(C.read_bound(args.host, keep=True)[0])
    py = host["python"]
    venv, framework = py["venv"], py["framework"]
    check("P0", "the venv and framework roots have no linked component", not C.linked_components(venv)
          and not C.linked_components(framework))
    frozen_raw, frozen_facts, _ = C.read_bound(py["inventory"]["path"], keep=True)
    frozen = json.loads(frozen_raw)
    started = time.monotonic()
    doc, passes = inventory(venv, framework)
    elapsed = time.monotonic() - started
    raw = C.canonical(doc)
    out["recomputed"] = {"sha256": C.sha256_bytes(raw), "size_bytes": len(raw), "elapsed_s": round(elapsed, 3),
                         "closure_passes": passes}
    out["frozen"] = {"path": py["inventory"]["path"], **C.binding(frozen_facts)}
    check("P1", "the frozen inventory file is canonical JSON", C.canonical(frozen) == frozen_raw)
    check("P2", "this review's recomputed inventory is byte-identical to the frozen one", raw == frozen_raw)
    check("P3", "its SHA-256 equals HOST.python.inventory_sha256 and the plan's frozen descriptor",
          C.sha256_bytes(raw) == py["inventory_sha256"] == py["inventory"]["sha256"] == host["labels"]["python_inventory_sha256"])
    diffs = []
    for tree in ("framework", "venv"):
        a, b = frozen[tree]["entries"], doc[tree]["entries"]
        for name in sorted(set(a) | set(b)):
            if a.get(name) != b.get(name):
                diffs.append({"part": tree, "path": name, "frozen": a.get(name), "now": b.get(name)})
    for part in ("images", "external"):
        a, b = frozen["closure"][part], doc["closure"][part]
        for name in sorted(set(a) | set(b)):
            if a.get(name) != b.get(name):
                diffs.append({"part": part, "path": name})
    if frozen["closure"]["links"] != doc["closure"]["links"]:
        diffs.append({"part": "links"})
    if frozen["selection"] != doc["selection"]:
        diffs.append({"part": "selection"})
    out["differences"] = diffs[:200]
    check("P4", "no tree entry, image, external dependency, link hop or selection key differs", not diffs,
          count=len(diffs))
    check("P5", "HOST.python.selection equals the recomputed selection", py["selection"] == doc["selection"])
    check("P6", "no rule problem in any image, tree entry or reference", not PROBLEMS, problems=PROBLEMS[:100])
    counts = {tree: {k: sum(1 for e in doc[tree]["entries"].values() if e["kind"] == k)
                     for k in ("file", "symlink", "directory")} for tree in ("framework", "venv")}
    bytecode = {tree: sum(1 for r, e in doc[tree]["entries"].items() if e["kind"] == "file" and r.endswith(".pyc"))
                for tree in ("framework", "venv")}
    images = doc["closure"]["images"]
    out["figures"] = {"entries": counts, "bytecode_files": bytecode, "images": len(images),
                      "images_by_tree": {t: sum(1 for v in images.values() if v["tree"] == t)
                                         for t in ("framework", "venv", "external")},
                      "external": len(doc["closure"]["external"]), "links": len(doc["closure"]["links"]),
                      "canonical_bytes": len(raw)}
    check("P7", "the process image is an inventoried framework file",
          doc["framework"]["entries"].get(PROCESS_IMAGE, {}).get("kind") == "file")

    # Packages and RECORD verification.
    found, records, unowned = packages(venv, doc["venv"]["entries"])
    check("P8", "exactly the seven pins are installed, at their versions, and HOST.python.packages equals them",
          found == PINS == py["packages"], found=found)
    check("P9", "HOST.python.records equals the recomputed RECORD verification", records == py["records"])
    check("P10", "every file under site-packages is owned by exactly one RECORD row", not unowned,
          unowned=unowned[:20])

    # The interpreter facts of this process, launched as the observer was (<venv>/bin/python -I -S -B).
    mine = {"implementation": sys.implementation.name, "version": "%d.%d.%d" % sys.version_info[:3],
            "build_string": sys.version, "flags": {name: getattr(sys.flags, name) for name in FLAGS},
            "executable": sys.executable, "base_executable": getattr(sys, "_base_executable", None),
            "prefix": sys.prefix, "base_prefix": sys.base_prefix, "path": list(sys.path),
            "process_image": process_image()}
    out["interpreter_of_this_process"] = mine
    check("P11", "HOST.python.interpreter equals the facts of a process launched as <venv>/bin/python -I -S -B",
          mine == py["interpreter"], differing=sorted(k for k in mine if mine[k] != py["interpreter"].get(k)))

    # N-06: every LC_RPATH entry, and every reference kind.
    rpaths, kinds = [], {}
    for path, row in sorted(images.items()):
        for entry in row["rpaths"]:
            rpaths.append({"image": path, "raw": entry["raw"], "state": entry["state"], "path": entry["path"]})
        for ref in row["references"]:
            label = ref["kind"] if not ref["raw"].startswith("@") else ref["raw"].split("/", 1)[0]
            kinds[label] = kinds.get(label, 0) + 1
    distinct = {}
    for row in rpaths:
        key = (row["raw"], row["state"], row["path"])
        distinct[key] = distinct.get(key, 0) + 1
    out["n06"] = {"entries": len(rpaths), "distinct": [{"raw": k[0], "state": k[1], "resolved": k[2], "images": v}
                                                       for k, v in sorted(distinct.items())],
                  "absent": [row for row in rpaths if row["state"] != "directory"],
                  "reference_kinds": kinds}
    check("P12", "N-06: no bound image has an @rpath or @executable_path reference, so no LC_RPATH entry is used",
          "@rpath" not in kinds and "@executable_path" not in kinds, kinds=kinds)
    check("P13", "N-06: the only absent rpath entry is recorded as absent at its first missing component",
          all(row["state"] == "absent" for row in out["n06"]["absent"]))
    out["checks"] = CHECKS
    out["failed"] = [c["id"] for c in CHECKS if not c["passed"]]
    out["refused_events"] = C.REFUSED_EVENTS
    C.write_new(args.output, out)
    print(json.dumps({"failed": out["failed"], "checks": len(CHECKS), "recomputed": out["recomputed"]}))


if __name__ == "__main__":
    main()
