"""HOST review 001, script 02: the Python installation inventory recomputed with my own code.

It rebuilds ontokin.current-host-readback-python-inventory/0.2.0 from W3-OBSERVER section 5
(both trees exhaustively without following links, the selection chain and the Mach-O closure
with its link hops), compares its canonical bytes with the frozen inventory that HOST binds,
verifies the seven packages and their RECORD rows, and compares HOST's python facts.
Usage: python3 -I -S -B w3h_02_python.py --venv V --framework F --frozen INV --host HOST
       --lock LOCK --out OUT [--label PATH=LABEL ...]
"""
import argparse
import base64
import csv
import io
import os
import posixpath
import re
import stat
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()

SCHEMA = "ontokin.current-host-readback-python-inventory/0.2.0"
SYSTEM = ("/usr/lib/", "/System/Library/")
PROCESS_IMAGE = "Resources/Python.app/Contents/MacOS/Python"
NODE_LIST = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
             "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
             "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
             "LC_DYLD_EXPORTS_TRIE"}
PYTHON_LIST = NODE_LIST | {"LC_ID_DYLIB", "LC_RPATH"}
PYTHON_TYPES = {"MH_EXECUTE", "MH_DYLIB", "MH_BUNDLE"}
SINGLE = {"LC_LOAD_DYLINKER", "LC_MAIN", "LC_UUID", "LC_SYMTAB", "LC_DYSYMTAB", "LC_CODE_SIGNATURE",
          "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE", "LC_FUNCTION_STARTS",
          "LC_DATA_IN_CODE", "LC_SOURCE_VERSION", "LC_ID_DYLIB"}

PROBLEMS = []


def problem(text):
    PROBLEMS.append(text)


def walk(root, tag, images):
    entries, stack = {}, [""]
    while stack:
        rel = stack.pop()
        directory = root + "/" + rel if rel else root
        before = os.lstat(directory)
        for name in sorted(os.listdir(directory)):
            if name in (".", "..") or "/" in name or "\0" in name or not name.isprintable():
                problem("unsupported name in " + directory)
            r = rel + "/" + name if rel else name
            path = root + "/" + r
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                entries[r] = {"kind": "symlink", "target": os.readlink(path)}
            elif stat.S_ISDIR(info.st_mode):
                entries[r] = {"kind": "directory", "mode": C.mode_text(info.st_mode)}
                stack.append(r)
            elif stat.S_ISREG(info.st_mode):
                _, facts, head = C.read_bytes(path, keep=False, prefix=4)
                entries[r] = {"kind": "file", **C.binding(facts)}
                kind = C.magic_kind(head)
                if kind is not None:
                    if kind != "macho64":
                        problem("non-thin or non-64-bit Mach-O in a Python tree: " + path)
                    images[path] = (tag, C.binding(facts))
            else:
                problem("special file: " + path)
        after = os.lstat(directory)
        if (before.st_mtime_ns, before.st_ctime_ns, before.st_ino) != (after.st_mtime_ns, after.st_ctime_ns,
                                                                        after.st_ino):
            problem("directory changed while listed: " + directory)
    return entries


def parse_pyvenv(raw):
    values = {}
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key in values:
            problem("duplicate pyvenv.cfg key")
        values[key] = value
    return values


def selection(venv, framework, fw, ve):
    short = posixpath.basename(framework)
    name = "python" + short
    expected = framework + "/bin/" + name
    launcher = venv + "/bin/python"
    chain = C.resolve_chain(launcher)
    if not (chain["state"] == "file" and chain["path"] == expected):
        problem("venv python does not select the framework launcher")
    raw, facts, _ = C.read_bytes(venv + "/pyvenv.cfg")
    if C.binding(facts) != {k: ve["pyvenv.cfg"][k] for k in ("sha256", "size_bytes", "mode")}:
        problem("pyvenv.cfg changed")
    cfg = parse_pyvenv(raw)
    if cfg.get("include-system-site-packages") != "false" or not re.fullmatch(re.escape(short) + r"\.\d+",
                                                                              cfg.get("version", "")):
        problem("pyvenv.cfg values")
    home = C.resolve_chain(cfg["home"])
    home_launcher = C.resolve_chain(cfg["home"].rstrip("/") + "/" + name)
    if home["state"] != "directory" or home_launcher["state"] != "file" or home_launcher["path"] != expected:
        problem("pyvenv.cfg home")
    executable = None
    if "executable" in cfg:
        executable = C.resolve_chain(cfg["executable"])
        if executable["state"] != "file" or executable["path"] != expected:
            problem("pyvenv.cfg executable")
    if fw.get(PROCESS_IMAGE, {}).get("kind") != "file":
        problem("process image missing")
    return {"launcher": launcher, "launcher_chain": chain, "pyvenv_cfg": cfg, "home_chain": home,
            "home_launcher_chain": home_launcher, "executable_chain": executable,
            "process_image": framework + "/" + PROCESS_IMAGE, "version_directory": short}


def image_rules(path, bnd):
    _, facts, head = C.read_bytes(path, keep=False, prefix=65536)
    if C.binding(facts) != bnd:
        problem("image changed after its binding: " + path)
    ncmds, sizeofcmds = __import__("struct").unpack_from("<II", head, 16)
    if 32 + sizeofcmds > len(head):
        raw, _, _ = C.read_bytes(path, keep=True)
        head = raw[:32 + sizeofcmds]
    summary = C.parse_thin(head, facts["size_bytes"])
    if summary["cputype"] != "0x0100000c" or summary["cpusubtype"] != "0x00000000":
        problem("cpu type or subtype: " + path)
    if summary["filetype"] not in PYTHON_TYPES:
        problem("file type: " + path)
    ident, rpaths, refs, names, counts = None, [], [], [], {}
    for row in summary["commands"]:
        name = row["name"]
        names.append(name)
        if name is not None:
            counts[name] = counts.get(name, 0) + 1
        if name not in PYTHON_LIST:
            problem("command outside the Python list in " + path + ": " + str(name))
        if name == "LC_LOAD_DYLINKER" and row["path"] != "/usr/lib/dyld":
            problem("dylinker: " + path)
        if name == "LC_ID_DYLIB":
            ident = row["path"]
        elif name == "LC_RPATH":
            raw = row["path"]
            if raw.startswith("@"):
                if not (raw.startswith(("@loader_path/", "@executable_path/")) or raw in ("@loader_path",
                                                                                           "@executable_path")):
                    problem("rpath form: " + path)
            elif posixpath.normpath(raw) != raw or raw.startswith("//"):
                problem("rpath not normalized: " + path)
            rpaths.append(raw)
        elif name in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB"):
            raw = row["path"]
            if raw.startswith("@"):
                if at_kind(raw) is None:
                    problem("unsupported @ reference: " + path)
            elif posixpath.normpath(raw) != raw or raw.startswith("//") or not raw.startswith("/"):
                problem("reference not normalized absolute: " + path)
            refs.append({"command": name, "path": raw})
    if any(counts.get(n, 0) > 1 for n in SINGLE):
        problem("duplicated single command: " + path)
    if summary["filetype"] == "MH_EXECUTE":
        if counts.get("LC_LOAD_DYLINKER") != 1 or counts.get("LC_MAIN") != 1:
            problem("executable structure: " + path)
    elif "LC_MAIN" in counts or "LC_LOAD_DYLINKER" in counts:
        problem("non-executable carries LC_MAIN or dylinker: " + path)
    if summary["filetype"] == "MH_DYLIB" and counts.get("LC_ID_DYLIB") != 1:
        problem("dylib without one LC_ID_DYLIB: " + path)
    return {"filetype": summary["filetype"], "id": ident, "rpaths": rpaths, "references": refs, "commands": names}


def at_kind(raw):
    for prefix in ("@rpath/", "@loader_path/", "@executable_path/"):
        if raw.startswith(prefix) and len(raw) > len(prefix):
            return prefix[:-1]
    return None


def inside(path, root):
    return path == root or path.startswith(root + "/")


def search_dir(raw, loader_dirs, exe_dir):
    if raw.startswith("@loader_path"):
        bases, suffix = sorted(loader_dirs), raw[len("@loader_path"):]
    elif raw.startswith("@executable_path"):
        bases, suffix = [exe_dir], raw[len("@executable_path"):]
    else:
        bases, suffix = [""], raw
    outs = [C.resolve_chain((base + suffix) if base else suffix) for base in bases]
    if len({(o["state"], o["path"]) for o in outs}) != 1:
        problem("rpath resolves differently through the image's spellings: " + raw)
    return {"raw": raw, **outs[0]}


def closure_pass(images, framework, venv, fw, ve, process_image, seed):
    known = dict(images)
    spell = {p: set(n) for p, n in seed.items()}
    used, queue = {}, sorted(images)
    out, external, links = {}, {}, {}
    entries = {"framework": fw, "venv": ve}
    while queue:
        path = queue.pop(0)
        if path in out:
            continue
        tree, bnd = known[path]
        rules = image_rules(path, bnd)
        spell.setdefault(path, set())
        used[path] = set(spell[path])
        loader_dirs = {posixpath.dirname(path)} | {posixpath.dirname(n) for n in spell[path]}
        exe_dir = posixpath.dirname(path if rules["filetype"] == "MH_EXECUTE" else process_image)
        rpaths = [search_dir(raw, loader_dirs, exe_dir) for raw in rules["rpaths"]]
        for row in rpaths:
            for hop in row["hops"]:
                links[(hop["path"], hop["target"])] = hop
        refs = []
        for ref in rules["references"]:
            raw = ref["path"]
            if not raw.startswith("@") and raw.startswith(SYSTEM):
                refs.append({"command": ref["command"], "raw": raw, "kind": "system"})
                continue
            candidates, kind = [], at_kind(raw)
            if kind == "@rpath":
                selected = None
                for row in rpaths:
                    cand = row["path"] + raw[len("@rpath"):]
                    outcome = (C.resolve_chain(cand) if row["state"] == "directory"
                               else {"state": "absent", "path": cand, "hops": []})
                    candidates.append({"rpath": row["raw"], "candidate": cand, "state": outcome["state"]})
                    if outcome["state"] != "absent":
                        selected = (cand, outcome)
                        break
                if selected is None:
                    problem("@rpath unresolved: " + raw)
                    continue
                spelling, outcome = selected
            elif kind == "@loader_path":
                outs = {}
                for base in sorted(loader_dirs):
                    s = base + raw[len("@loader_path"):]
                    outs[s] = C.resolve_chain(s)
                if len({(o["state"], o["path"]) for o in outs.values()}) != 1:
                    problem("@loader_path ambiguous: " + raw)
                spelling, outcome = sorted(outs.items())[0]
            elif kind == "@executable_path":
                spelling = exe_dir + raw[len("@executable_path"):]
                outcome = C.resolve_chain(spelling)
            else:
                spelling, outcome = raw, C.resolve_chain(raw)
            if outcome["state"] != "file":
                problem("reference not a bound regular file: " + raw)
                continue
            target = outcome["path"]
            if target.startswith(SYSTEM):
                problem("non-system reference resolves into the system tree: " + raw)
            for hop in outcome["hops"]:
                links[(hop["path"], hop["target"])] = hop
            if inside(target, framework) or inside(target, venv):
                owner = "framework" if inside(target, framework) else "venv"
                rel = target[len(framework if owner == "framework" else venv) + 1:]
                if entries[owner].get(rel, {}).get("kind") != "file" or target not in known:
                    problem("reference to an unbound or non-Mach-O tree file: " + target)
            elif target not in known:
                _, facts, head = C.read_bytes(target, keep=False, prefix=4)
                if C.magic_kind(head) != "macho64":
                    problem("external dependency not thin 64-bit Mach-O: " + target)
                known[target] = ("external", C.binding(facts))
                external[target] = C.binding(facts)
                queue.append(target)
            spell.setdefault(target, set()).add(spelling)
            row = {"command": ref["command"], "raw": raw, "kind": "bound", "path": target, "hops": outcome["hops"]}
            if candidates:
                row["candidates"] = candidates
            refs.append(row)
        out[path] = {"tree": tree, "filetype": rules["filetype"], "id": rules["id"], "commands": rules["commands"],
                     "rpaths": rpaths, "references": refs}
    for p, names in spell.items():
        if p in out and names - {p}:
            out[p]["spellings"] = sorted(names)
    return {"images": out, "external": external, "links": [links[k] for k in sorted(links)]}, used, spell


def inventory(venv, framework):
    images = {}
    fw = walk(framework, "framework", images)
    ve = walk(venv, "venv", images)
    sel = selection(venv, framework, fw, ve)
    seed, passes = {p: {p} for p in images}, 0
    for passes in range(1, 9):
        closure, used, final = closure_pass(images, framework, venv, fw, ve, sel["process_image"], seed)
        if all(used.get(p) == names for p, names in final.items()):
            break
        seed = {p: set(n) for p, n in final.items()}
    else:
        problem("closure did not stabilize")
    doc = {"schema": SCHEMA, "framework": {"root": framework, "entries": fw}, "venv": {"root": venv, "entries": ve},
           "selection": sel, "closure": closure}
    return doc, passes


def lock_pins(raw):
    pins = {}
    for line in raw.decode("ascii").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("--hash="):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)==([^\s\\]+)", line)
        if match:
            pins[match[1]] = match[2]
    return pins


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def packages(venv, ve, pins, short):
    site = "lib/python" + short + "/site-packages"
    wanted = {norm(n): (n, v) for n, v in pins.items()}
    dist = sorted(r for r, e in ve.items() if e["kind"] == "directory" and posixpath.dirname(r) == site
                  and r.endswith((".dist-info", ".egg-info")))
    found, records, owned = {}, {}, {}
    for directory in dist:
        if not directory.endswith(".dist-info"):
            problem("egg-info present")
            continue
        raw, _, _ = C.read_bytes(venv + "/" + directory + "/METADATA")
        header = raw.decode("utf-8").split("\n\n", 1)[0]
        names = re.findall(r"^Name: ([^\r\n]+)$", header, flags=re.M)
        versions = re.findall(r"^Version: ([^\r\n]+)$", header, flags=re.M)
        if len(names) != 1 or len(versions) != 1:
            problem("METADATA header: " + directory)
            continue
        key = norm(names[0].strip())
        if key not in wanted or versions[0].strip() != wanted[key][1] or key in found:
            problem("unexpected package or version: " + directory)
            continue
        raw, facts, _ = C.read_bytes(venv + "/" + directory + "/RECORD")
        hashed = unhashed = 0
        for row in csv.reader(io.StringIO(raw.decode("utf-8"), newline="")):
            if not row:
                continue
            if len(row) != 3:
                problem("RECORD row width: " + directory)
                continue
            name, digest, size = row
            rel = posixpath.normpath(site + "/" + name)
            entry = ve.get(rel)
            if entry is None or entry["kind"] != "file" or rel.startswith("../") or rel in owned:
                problem("RECORD row names a missing, unsafe or doubly owned file: " + rel)
                continue
            if digest:
                algorithm, _, value = digest.partition("=")
                expected = base64.urlsafe_b64encode(bytes.fromhex(entry["sha256"])).rstrip(b"=").decode("ascii")
                if algorithm != "sha256" or value != expected or size != str(entry["size_bytes"]):
                    problem("RECORD digest or size differs: " + rel)
                hashed += 1
            else:
                if size != "" or not (rel == directory + "/RECORD" or (rel.endswith(".pyc") and "/__pycache__/" in
                                                                       "/" + rel)):
                    problem("unhashed RECORD row: " + rel)
                unhashed += 1
            owned[rel] = key
        if owned.get(directory + "/RECORD") != key:
            problem("RECORD does not list itself: " + directory)
        found[key] = wanted[key][0]
        records[wanted[key][0]] = {"dist_info": directory, "record": C.binding(facts), "hashed_rows": hashed,
                                   "unhashed_rows": unhashed}
    unowned = [r for r, e in ve.items() if e["kind"] == "file" and inside(r, site) and r not in owned]
    if unowned:
        problem("unowned files under site-packages: %d" % len(unowned))
    pk = {wanted[k][0]: wanted[k][1] for k in found}
    if pk != pins:
        problem("installed packages differ from the pins")
    return pk, records, len(unowned)


def figures(doc):
    out = {}
    for tree in ("framework", "venv"):
        e = doc[tree]["entries"].values()
        files = [x for x in doc[tree]["entries"].items() if x[1]["kind"] == "file"]
        out[tree] = {"files": len(files), "bytecode_files": sum(1 for r, _ in files if r.endswith(".pyc")),
                     "symlinks": sum(1 for x in e if x["kind"] == "symlink"),
                     "directories": sum(1 for x in e if x["kind"] == "directory"),
                     "file_bytes": sum(x["size_bytes"] for _, x in files)}
    images = doc["closure"]["images"]
    by = {}
    for row in images.values():
        by.setdefault(row["tree"], {}).setdefault(row["filetype"], 0)
        by[row["tree"]][row["filetype"]] += 1
    refs = [r for row in images.values() for r in row["references"]]
    rp = [r for row in images.values() for r in row["rpaths"]]
    out["images"] = {"total": len(images), "by_tree_and_type": by, "external": len(doc["closure"]["external"])}
    out["closure"] = {"link_hops": len(doc["closure"]["links"]), "rpath_entries": len(rp),
                      "rpath_states": {s: sum(1 for r in rp if r["state"] == s) for s in sorted({r["state"] for r in rp})},
                      "references": len(refs), "system": sum(1 for r in refs if r["kind"] == "system"),
                      "bound_absolute": sum(1 for r in refs if r["kind"] == "bound" and not r["raw"].startswith("@")),
                      "loader_path": sum(1 for r in refs if r["raw"].startswith("@loader_path/")),
                      "rpath_refs": sum(1 for r in refs if r["raw"].startswith("@rpath/")),
                      "executable_path_refs": sum(1 for r in refs if r["raw"].startswith("@executable_path/")),
                      "images_with_spellings": sum(1 for row in images.values() if "spellings" in row)}
    sel = doc["selection"]
    out["selection_hops"] = {k: len(sel[k]["hops"]) for k in ("launcher_chain", "home_chain", "home_launcher_chain")}
    out["selection_hops"]["executable_chain"] = None if sel["executable_chain"] is None else len(
        sel["executable_chain"]["hops"])
    return out


def leaf_diff(a, b, limit=60):
    la, lb = dict(C.json_pointer_leaves(a)), dict(C.json_pointer_leaves(b))
    keys = sorted(set(la) | set(lb))
    rows = [{"pointer": k, "frozen": la.get(k, "<absent>"), "recomputed": lb.get(k, "<absent>")}
            for k in keys if la.get(k, "<absent>") != lb.get(k, "<absent>")]
    return len(rows), rows[:limit]


def main():
    ap = argparse.ArgumentParser()
    for name in ("--venv", "--framework", "--frozen", "--host", "--lock", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--label", action="append", default=[])
    ap.add_argument("--tag", default="run1")
    args = ap.parse_args()
    lab = C.Labeler([tuple(item.split("=", 1)) for item in args.label])
    checks = C.Checks()
    started = time.time()
    doc, passes = inventory(args.venv, args.framework)
    mine = C.canonical(doc)
    digest = C.sha256(mine)
    frozen_raw, frozen_facts, _ = C.read_bytes(args.frozen)
    frozen = C.strict_loads(frozen_raw)
    checks.add("P01", C.canonical(frozen) == frozen_raw, "the frozen inventory file is canonical JSON with no "
               "duplicate member")
    checks.add("P02", mine == frozen_raw, "my recomputed inventory is byte-identical to the frozen file",
               recomputed_sha256=digest, recomputed_bytes=len(mine), frozen_sha256=frozen_facts["sha256"],
               frozen_bytes=frozen_facts["size_bytes"])
    count, rows = (0, []) if mine == frozen_raw else leaf_diff(frozen, doc)
    checks.add("P03", count == 0, "no leaf differs between the frozen and the recomputed inventory",
               differing_leaves=count, first=lab.deep(rows))
    checks.add("P04", not PROBLEMS, "my own rule checks found no problem (trees, selection, Mach-O rules, closure)",
               problems=lab.deep(PROBLEMS[:50]))
    host = C.strict_loads(C.read_bytes(args.host)[0])
    hp = host["python"]
    checks.add("P05", hp["inventory_sha256"] == digest and host["labels"]["python_inventory_sha256"] == digest,
               "HOST /python/inventory_sha256 and /labels/python_inventory_sha256 equal my digest")
    checks.add("P06", hp["inventory"] == C.descriptor(args.frozen, frozen_facts) and hp["inventory"]["sha256"] == digest,
               "HOST /python/inventory is the frozen file's descriptor (path, SHA-256, size, mode)")
    checks.add("P07", hp["selection"] == doc["selection"], "HOST /python/selection equals my selection chain")
    checks.add("P08", hp["venv"] == args.venv and hp["framework"] == args.framework
               and hp["launcher"] == args.venv + "/bin/python", "HOST /python/venv, /framework and /launcher")
    lock_raw, lock_facts, _ = C.read_bytes(args.lock)
    pins = lock_pins(lock_raw)
    contract_pins = {"attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1",
                     "referencing": "0.37.0", "rpds-py": "2026.5.1", "typing_extensions": "4.16.0",
                     "Pillow": "13.0.0"}
    checks.add("P09", pins == contract_pins, "the macOS lock pins exactly the contract's seven names and versions")
    checks.add("P10", hp["lock"] == C.descriptor(args.lock, lock_facts), "HOST /python/lock is the lock's descriptor")
    pk, records, unowned = packages(args.venv, doc["venv"]["entries"], pins, doc["selection"]["version_directory"])
    checks.add("P11", pk == pins and hp["packages"] == pk, "the seven packages are installed at their pins and equal "
               "HOST /python/packages", unowned_files=unowned)
    checks.add("P12", hp["records"] == records, "HOST /python/records equals my RECORD verification (dist-info, "
               "RECORD binding, hashed and unhashed rows)")
    rp = [{"image": lab.text(p), "raw": lab.text(r["raw"]), "state": r["state"], "path": lab.text(r["path"])}
          for p, row in sorted(doc["closure"]["images"].items()) for r in row["rpaths"]]
    used = [r for row in doc["closure"]["images"].values() for r in row["references"]
            if r["raw"].startswith(("@rpath/", "@executable_path/"))]
    checks.add("P13", not used, "N-06: no reference uses @rpath or @executable_path, so no LC_RPATH entry takes "
               "part in load-time resolution", rpath_entries=len(rp),
               not_directory=[r for r in rp if r["state"] != "directory"])
    image = os.path.realpath(sys.executable)
    checks.add("P14", image == args.framework + "/bin/python" + doc["selection"]["version_directory"]
               and sys.flags.dont_write_bytecode == 1 and sys.flags.isolated == 1 and sys.flags.no_site == 1,
               "this script runs on the bound framework interpreter, under -I -S -B",
               executable_resolves_to=lab.text(image))
    result = {"script": "w3h_02_python.py", "tag": args.tag, "process": C.process_identity(),
              "started_epoch": started, "ended_epoch": time.time(), "closure_passes": passes,
              "recomputed": {"sha256": digest, "canonical_bytes": len(mine)},
              "frozen": {"path": lab.text(args.frozen), **C.binding(frozen_facts), "nlink": frozen_facts["nlink"]},
              "figures": figures(doc), "rpath_entries_by_raw": sorted({(r["raw"], r["state"]) for r in rp}),
              "checks": checks.rows, "summary": checks.summary(), "audit_events": C.EVENTS}
    result["rpath_entries_by_raw"] = [list(x) for x in result["rpath_entries_by_raw"]]
    print(C.write_new(args.out, lab.deep(result)), checks.summary())


if __name__ == "__main__":
    main()
