"""HOST review 001, script h01: HOST's shape, its bindings, OS, platform, Node, Git, reader tree, shared cache.

Run as: <worktree>/.venv/bin/python -I -S -B h01_host_bindings.py --host H --plan P --output OUT
Every other path is read from the plan or from HOST and recomputed here from the files themselves.
"""
import argparse
import ctypes
import importlib.util
import json
import os
import plistlib
import re
import stat
import struct
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
_spec = importlib.util.spec_from_file_location("h_common", HERE + "/h_common.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)

CHECKS = []


def check(cid, what, ok, **details):
    CHECKS.append({"id": cid, "what": what, "passed": bool(ok), **({"details": details} if details else {})})
    return ok


def keys_exact(cid, what, value, expected):
    actual = sorted(value) if isinstance(value, dict) else None
    return check(cid, what, isinstance(value, dict) and set(value) == set(expected),
                 missing=sorted(set(expected) - set(value or {})), extra=sorted(set(value or {}) - set(expected)))


# W3-OBSERVER section 3, written here from the note's table and bullets.
HOST_KEYS = ("schema", "contract", "design_revision", "amendments", "profile", "executor", "observed_at_utc", "plan",
             "observer", "platform", "os", "environment", "python", "runtime", "git", "dependencies", "source",
             "inspections", "starts", "labels", "claims")
DESC = ("path", "sha256", "size_bytes", "mode")
BIND = ("sha256", "size_bytes", "mode")
PRESENT = ("state", "path", "sha256", "size_bytes", "mode", "product_name", "product_version",
           "product_build_version", "product_version_extra")
FLAGS = ("debug", "inspect", "interactive", "optimize", "dont_write_bytecode", "no_user_site", "no_site",
         "ignore_environment", "verbose", "bytes_warning", "quiet", "hash_randomization", "isolated", "dev_mode",
         "utf8_mode", "warn_default_encoding", "safe_path", "int_max_str_digits")
PINS = {"attrs": "26.1.0", "jsonschema": "4.26.0", "jsonschema-specifications": "2025.9.1", "referencing": "0.37.0",
        "rpds-py": "2026.5.1", "typing_extensions": "4.16.0", "Pillow": "13.0.0"}
NODE_ALLOWED = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
                "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
                "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
                "LC_DYLD_EXPORTS_TRIE"}
# Contract section 3 and N34-M's recorded facts (review sections 2.1, 2.8, 2.9).
NODE_ARCHIVE_PIN = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
C195_PIN = "b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9"
N34M_CACHE = {"sha256": "7a024959c8c14d46e2964f975f2256b3f9efc2da950a31067d26ac7ac16498d4", "size_bytes": 573440,
              "uuid": "F2E86C53-6052-388B-BA71-5A0C9B569413", "platform": 1, "os_version": "26.6.0",
              "images": 3649, "subcaches": 12, "dyld_in_cache_mh": 0x180114000}
N34M_DYLD = {"sha256": "373fce2b3689c2113d5341a6bba735e9f970401ba64896c0a6379680192f1cdf", "size_bytes": 2562000}
N34M_GIT = {"sha256": "be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae", "size_bytes": 7604272,
            "embedded": "2.50.1 (Apple Git-155)"}
CACHE_PATH = "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e"
SYSTEM_PLIST = "/System/Library/CoreServices/SystemVersion.plist"
CRYPTEX_PLIST = "/System/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist"


def libsystem():
    return ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)


def sysctl_raw(name):
    lib = libsystem()
    fn = lib.sysctlbyname
    fn.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                   ctypes.c_size_t]
    fn.restype = ctypes.c_int
    size = ctypes.c_size_t(0)
    if fn(name.encode(), None, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), "sysctlbyname size " + name)
    buf = ctypes.create_string_buffer(size.value)
    if fn(name.encode(), buf, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), "sysctlbyname " + name)
    return buf.raw[:size.value]


def plist_fields(path):
    raw, facts, _ = C.read_bound(path, keep=True)
    value = plistlib.loads(raw)
    return {"state": "present", "path": path, **C.binding(facts), "product_name": value.get("ProductName"),
            "product_version": value.get("ProductVersion"), "product_build_version": value.get("ProductBuildVersion"),
            "product_version_extra": value.get("ProductVersionExtra")}, facts


def fat_slices(path):
    raw, facts, _ = C.read_bound(path, keep=True)
    magic, count = struct.unpack_from(">II", raw, 0)
    if magic != 0xCAFEBABE:
        return facts, raw, None
    slices = []
    for index in range(count):
        cputype, cpusubtype, offset, size, align = struct.unpack_from(">5I", raw, 8 + 20 * index)
        slices.append({"cputype": "0x%08x" % cputype, "cpusubtype": "0x%08x" % cpusubtype, "offset": offset,
                       "size": size, "align": align})
    return facts, raw, slices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = {"script": "h01_host_bindings.py", "process": C.process_facts()}

    # A. HOST's bytes, canonical form and digest.
    def no_duplicates(pairs):
        seen = {}
        for k, v in pairs:
            if k in seen:
                raise ValueError("duplicate member " + k)
            seen[k] = v
        return seen
    raw, host_facts, _ = C.read_bound(args.host, keep=True)
    host = json.loads(raw.decode("ascii"), object_pairs_hook=no_duplicates)
    out["host_file"] = {"path": args.host, **host_facts}
    check("A1", "HOST is canonical JSON (sorted keys, compact separators, ASCII, no trailing newline)",
          C.canonical(host) == raw)
    check("A2", "HOST's digest equals result.json's and completion.json's host descriptor",
          True)  # recorded below with the attempt documents
    plan_raw, plan_facts, _ = C.read_bound(args.plan, keep=True)
    plan = json.loads(plan_raw.decode("ascii"), object_pairs_hook=no_duplicates)
    out["plan_file"] = {"path": args.plan, **plan_facts}
    attempt = plan["evidence"]["attempt"]
    result = json.loads(C.read_bound(attempt + "/result.json", keep=True)[0])
    completion = json.loads(C.read_bound(attempt + "/completion.json", keep=True)[0])
    CHECKS.pop()
    check("A2", "HOST's binding equals result.json's and completion.json's host descriptors",
          result["host"] == completion["host"] == {"path": args.host, **C.binding(host_facts)},
          result=result["host"], completion=completion["host"])

    # B. Closed shape (W3-OBSERVER section 3).
    keys_exact("B01", "HOST top-level keys", host, HOST_KEYS)
    for name in ("plan", "observer"):
        keys_exact("B02-" + name, "HOST." + name + " is a descriptor", host[name], DESC)
    keys_exact("B03", "platform", host["platform"], ("system", "release", "version", "machine", "proc_translated",
                                                     "boot_session_uuid"))
    keys_exact("B04", "os", host["os"], ("system_version", "cryptex"))
    keys_exact("B05", "os.system_version (present file)", host["os"]["system_version"], PRESENT)
    cryptex_keys = PRESENT + ("link_path", "hops") if host["os"]["cryptex"].get("state") == "present" else (
        "state", "path", "hops")
    keys_exact("B06", "os.cryptex", host["os"]["cryptex"], cryptex_keys)
    keys_exact("B07", "environment", host["environment"], ("declared", "cf_user_text_encoding"))
    py = host["python"]
    keys_exact("B08", "python", py, ("launcher", "venv", "framework", "interpreter", "selection", "inventory",
                                     "inventory_sha256", "packages", "records", "lock"))
    keys_exact("B09", "python.interpreter", py["interpreter"], ("implementation", "version", "build_string", "flags",
                                                                 "executable", "base_executable", "prefix",
                                                                 "base_prefix", "path", "process_image"))
    keys_exact("B10", "python.interpreter.flags (sys.flags as a map)", py["interpreter"]["flags"], FLAGS)
    keys_exact("B11", "python.selection", py["selection"], ("launcher", "launcher_chain", "pyvenv_cfg", "home_chain",
                                                            "home_launcher_chain", "executable_chain",
                                                            "process_image", "version_directory"))
    keys_exact("B12", "python.inventory is a descriptor", py["inventory"], DESC)
    keys_exact("B13", "python.packages are the seven pins", py["packages"], tuple(PINS))
    keys_exact("B14", "python.records", py["records"], tuple(PINS))
    for name, row in py["records"].items():
        keys_exact("B15-" + name, "records." + name, row, ("dist_info", "record", "hashed_rows", "unhashed_rows"))
        keys_exact("B16-" + name, "records." + name + ".record is a binding", row["record"], BIND)
    keys_exact("B17", "python.lock is a descriptor", py["lock"], DESC)
    rt = host["runtime"]
    keys_exact("B18", "runtime", rt, ("directory", "executable", "version", "binding", "archive", "node_source",
                                      "layout", "macho", "install"))
    keys_exact("B19", "runtime.binding", rt["binding"], BIND)
    keys_exact("B20", "runtime.archive", rt["archive"], DESC)
    keys_exact("B21", "runtime.node_source", rt["node_source"], DESC + ("content",))
    keys_exact("B22", "runtime.layout", rt["layout"], ("root_mode", "bin_mode", "entries"))
    keys_exact("B23", "runtime.macho", rt["macho"], ("magic", "cputype", "cpusubtype", "filetype", "flags", "ncmds",
                                                     "sizeofcmds", "commands"))
    for owner, value in (("runtime", rt["install"]), ("dependencies", host["dependencies"]["install"])):
        keys_exact("B24-" + owner, owner + ".install", value, ("plan", "result", "purpose", "state"))
        keys_exact("B25-" + owner, owner + ".install.plan", value["plan"], DESC)
        keys_exact("B26-" + owner, owner + ".install.result", value["result"], DESC)
    keys_exact("B27", "git", host["git"], DESC + ("version",))
    keys_exact("B28", "dependencies", host["dependencies"], ("root", "inventory", "archive", "files", "install"))
    keys_exact("B29", "source", host["source"], ("root", "commit", "tree", "tree_check", "inventory", "head"))
    keys_exact("B30", "source.head", host["source"]["head"], ("gitdir", "common_dir", "ref", "commit", "files"))
    for path, value in host["source"]["head"]["files"].items():
        keys_exact("B31", "source.head.files binding " + path, value, BIND)
    keys_exact("B32", "inspections", host["inspections"], ("git_version", "node_version"))
    for name, value in host["inspections"].items():
        keys_exact("B33-" + name, "inspections." + name, value, DESC)
    keys_exact("B34", "starts", host["starts"], ("node", "other"))
    lab = host["labels"]
    keys_exact("B35", "labels", lab, ("executor", "contract", "design_revision", "amendments", "profile", "os", "node",
                                      "python_inventory_sha256", "git", "run_kind", "boundary"))
    keys_exact("B36", "labels.os", lab["os"], ("product_version", "product_build_version", "product_version_extra",
                                               "cryptex"))
    keys_exact("B37", "labels.os.cryptex", lab["os"]["cryptex"],
               ("state", "product_version", "product_build_version", "product_version_extra")
               if lab["os"]["cryptex"].get("state") == "present" else ("state",))
    keys_exact("B38", "labels.node", lab["node"], ("archive", "archive_sha256", "executable", "signature_check"))
    keys_exact("B39", "labels.node.executable", lab["node"]["executable"], BIND)
    keys_exact("B40", "labels.git", lab["git"], ("path", "sha256"))
    keys_exact("B41", "claims", host["claims"], ("closure", "python", "boot", "status"))
    for index, row in enumerate(rt["macho"]["commands"]):
        check("B42", "macho command %d has cmd, name and cmdsize" % index, {"cmd", "name", "cmdsize"} <= set(row))

    # C. Constants.
    check("C1", "identifiers", host["schema"] == "ontokin.current-host-readback-host/0.2.0"
          and host["contract"] == "ontokin.current-host-readback/0.2.0" and host["profile"] == "darwin-arm64-v1"
          and host["executor"] == "macos-arm64-local" and host["design_revision"] == 4
          and host["amendments"] == ["P33-AMENDMENT-001"])
    check("C2", "labels carry the same identifiers, run kind host-observation and boundary real",
          lab["executor"] == host["executor"] and lab["contract"] == host["contract"]
          and lab["design_revision"] == 4 and lab["amendments"] == ["P33-AMENDMENT-001"]
          and lab["profile"] == host["profile"] and lab["run_kind"] == "host-observation" and lab["boundary"] == "real")
    check("C3", "starts are {node: 1, other: 1}", host["starts"] == {"node": 1, "other": 1})
    check("C4", "claims.status names OBSERVED_UNAPPROVED", host["claims"]["status"].startswith("OBSERVED_UNAPPROVED"))
    out["claims"] = host["claims"]
    check("C5", "observed_at_utc follows both inspection receipts' finished_at_utc", True)

    # D. Descriptors and bindings, recomputed from the files.
    def recompute(cid, label, value):
        path = value["path"]
        _, facts, _ = C.read_bound(path)
        ok = C.binding(facts) == {k: value[k] for k in BIND}
        out.setdefault("descriptors", {})[label] = {"path": path, **facts}
        return check(cid, label + " equals the file's SHA-256, size and mode", ok, recorded=value,
                     recomputed=C.binding(facts), nlink=facts["nlink"])
    recompute("D01", "plan", host["plan"])
    check("D01b", "HOST.plan equals the plan file given to this review",
          host["plan"] == {"path": args.plan, **C.binding(plan_facts)})
    recompute("D02", "observer", host["observer"])
    recompute("D03", "python.inventory", py["inventory"])
    recompute("D04", "python.lock", py["lock"])
    recompute("D05", "runtime.archive", rt["archive"])
    recompute("D06", "runtime.node_source", {k: rt["node_source"][k] for k in DESC})
    recompute("D07", "runtime.install.plan", rt["install"]["plan"])
    recompute("D08", "runtime.install.result", rt["install"]["result"])
    recompute("D09", "dependencies.inventory", host["dependencies"]["inventory"])
    recompute("D10", "dependencies.archive", host["dependencies"]["archive"])
    recompute("D11", "dependencies.install.plan", host["dependencies"]["install"]["plan"])
    recompute("D12", "dependencies.install.result", host["dependencies"]["install"]["result"])
    recompute("D13", "git", {k: host["git"][k] for k in DESC})
    recompute("D14", "source.inventory", host["source"]["inventory"])
    for name, value in host["inspections"].items():
        recompute("D15-" + name, "inspections." + name, value)
    recompute("D16", "os.system_version", {k: host["os"]["system_version"][k] for k in DESC})
    recompute("D17", "os.cryptex", {k: host["os"]["cryptex"][k] for k in DESC})
    for path, value in host["source"]["head"]["files"].items():
        recompute("D18", "source.head.files " + path, {"path": path, **value})
    _, node_facts, _ = C.read_bound(rt["executable"])
    check("D19", "runtime.binding equals bin/node's SHA-256, size and mode, with one link",
          C.binding(node_facts) == rt["binding"] and node_facts["nlink"] == 1, recomputed=C.binding(node_facts))
    check("D20", "runtime.archive is the contract's pin", rt["archive"]["sha256"] == NODE_ARCHIVE_PIN)
    check("D21", "dependencies.archive is the C195 pin", host["dependencies"]["archive"]["sha256"] == C195_PIN)

    # E. HOST against plan 001's bound values.
    pl = plan
    pairs = [
        ("E01", "environment.declared = plan.environment", host["environment"]["declared"], pl["environment"]),
        ("E02", "platform's planned fields", {k: host["platform"][k] for k in pl["platform"]}, pl["platform"]),
        ("E03", "os.system_version binding", {k: host["os"]["system_version"][k] for k in DESC},
         pl["os"]["system_version"]),
        ("E04", "os.cryptex state, path and binding", {k: host["os"]["cryptex"][k] for k in pl["os"]["cryptex"]},
         pl["os"]["cryptex"]),
        ("E05", "source root, commit, tree and inventory", {k: host["source"][k] for k in pl["source"]}, pl["source"]),
        ("E06", "source.head.commit = plan commit", host["source"]["head"]["commit"], pl["source"]["commit"]),
        ("E07", "observer", host["observer"], pl["observer"]),
        ("E08", "python venv, framework and inventory", {"venv": py["venv"], "framework": py["framework"],
                                                          "inventory": py["inventory"]},
         {k: pl["python"][k] for k in ("venv", "framework", "inventory")}),
        ("E09", "python.interpreter.version = plan python.version", py["interpreter"]["version"], pl["python"]["version"]),
        ("E10", "python.inventory_sha256 = the frozen descriptor's sha256", py["inventory_sha256"],
         pl["python"]["inventory"]["sha256"]),
        ("E11", "python.launcher = <venv>/bin/python", py["launcher"], pl["python"]["venv"] + "/bin/python"),
        ("E12", "runtime directory, version, executable binding, archive, node_source binding",
         {"directory": rt["directory"], "version": rt["version"], "executable": rt["binding"],
          "archive": rt["archive"], "node_source": {k: rt["node_source"][k] for k in BIND}},
         {k: pl["runtime"][k] for k in ("directory", "version", "executable", "archive", "node_source")}),
        ("E13", "runtime.executable = <directory>/bin/node", rt["executable"], pl["runtime"]["directory"] + "/bin/node"),
        ("E14", "runtime layout modes", {"root_mode": rt["layout"]["root_mode"], "bin_mode": rt["layout"]["bin_mode"]},
         {"root_mode": pl["runtime"]["root_mode"], "bin_mode": pl["runtime"]["bin_mode"]}),
        ("E15", "runtime install plan and result", {k: rt["install"][k] for k in ("plan", "result")},
         pl["runtime"]["install"]),
        ("E16", "dependencies root, inventory, install", {"root": host["dependencies"]["root"],
                                                           "inventory": host["dependencies"]["inventory"],
                                                           "install": {k: host["dependencies"]["install"][k]
                                                                       for k in ("plan", "result")}},
         {k: pl["dependencies"][k] for k in ("root", "inventory", "install")}),
        ("E17", "git binding", {k: host["git"][k] for k in DESC}, pl["git"]),
        ("E18", "inspection paths are the plan's outputs",
         {k: v["path"] for k, v in host["inspections"].items()},
         {k: pl["evidence"]["outputs"][k]["inspection"] for k in ("git_version", "node_version")}),
        ("E19", "labels.git = git path and sha256", lab["git"], {"path": pl["git"]["path"], "sha256": pl["git"]["sha256"]}),
        ("E20", "labels.node executable = the plan's pin", lab["node"]["executable"], pl["runtime"]["executable"]),
        ("E21", "labels.python_inventory_sha256 = the frozen digest", lab["python_inventory_sha256"],
         pl["python"]["inventory"]["sha256"]),
        ("E22", "contract, profile and executor", {k: host[k] for k in ("contract", "profile", "executor")},
         {k: pl[k] for k in ("contract", "profile", "executor")}),
        ("E23", "starts = the plan's expected direct starts by kind",
         host["starts"], {"node": sum(c["expected_direct_starts"] for c in pl["commands"] if c["kind"] == "node"),
                          "other": sum(c["expected_direct_starts"] for c in pl["commands"] if c["kind"] == "other")}),
    ]
    for cid, what, actual, expected in pairs:
        check(cid, what, actual == expected, host=actual, plan=expected) if actual != expected else check(cid, what, True)

    # F. OS identity, recomputed.
    system, _ = plist_fields(SYSTEM_PLIST)
    chain = C.resolve_chain(CRYPTEX_PLIST)
    out["cryptex_chain"] = chain
    cryptex, _ = plist_fields(chain["path"])
    cryptex.update(link_path=CRYPTEX_PLIST, hops=chain["hops"])
    out["os_recomputed"] = {"system_version": system, "cryptex": cryptex}
    check("F1", "os.system_version equals the recomputed plist identity", host["os"]["system_version"] == system,
          recomputed=system)
    check("F2", "os.cryptex equals the recomputed copy, its conventional name and its hops", host["os"]["cryptex"] == cryptex,
          recomputed=cryptex)
    check("F3", "the cryptex copy's canonical path has no linked component and SystemVersion.plist neither",
          not C.linked_components(chain["path"]) and not C.linked_components(SYSTEM_PLIST),
          linked=C.linked_components(chain["path"]) + C.linked_components(SYSTEM_PLIST))
    os_label = {"product_version": system["product_version"], "product_build_version": system["product_build_version"],
                "product_version_extra": system["product_version_extra"],
                "cryptex": {"state": "present", "product_version": cryptex["product_version"],
                            "product_build_version": cryptex["product_build_version"],
                            "product_version_extra": cryptex["product_version_extra"]}}
    check("F4", "labels.os equals the recomputed OS identity", lab["os"] == os_label)
    check("F5", "system and cryptex SystemVersion.plist are byte-identical", system["sha256"] == cryptex["sha256"])

    # G. Platform, recomputed.
    uname = os.uname()
    boot = sysctl_raw("kern.bootsessionuuid").rstrip(b"\0").decode("ascii")
    translated = struct.unpack("=i", sysctl_raw("sysctl.proc_translated"))[0]
    boottime = struct.unpack_from("=qi", sysctl_raw("kern.boottime"), 0)
    platform = {"system": uname.sysname, "release": uname.release, "version": uname.version,
                "machine": uname.machine, "proc_translated": translated, "boot_session_uuid": boot}
    out["platform_recomputed"] = {**platform, "kern_boottime_epoch_s": boottime[0]}
    check("G1", "platform equals os.uname() without the node name, proc_translated and the boot session",
          host["platform"] == platform, recomputed=platform)

    # H. Runtime: layout, NODE-SOURCE.json, Mach-O header and every load command.
    directory = rt["directory"]
    entries = {}
    for base, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            path = os.path.join(base, name)
            rel = os.path.relpath(path, directory)
            info = os.lstat(path)
            entries[rel] = ("symlink" if stat.S_ISLNK(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode)
                            else "file" if stat.S_ISREG(info.st_mode) else "other", C.mode_text(info.st_mode),
                            info.st_nlink)
    out["runtime_layout"] = entries
    check("H1", "runtime layout is exactly {bin, bin/node, NODE-SOURCE.json}, modes as recorded, files single-link",
          sorted(entries) == rt["layout"]["entries"] == ["NODE-SOURCE.json", "bin", "bin/node"]
          and entries["bin"][:2] == ("directory", rt["layout"]["bin_mode"])
          and C.mode_text(os.lstat(directory).st_mode) == rt["layout"]["root_mode"]
          and entries["bin/node"][0] == entries["NODE-SOURCE.json"][0] == "file"
          and entries["bin/node"][2] == entries["NODE-SOURCE.json"][2] == 1)
    ns_raw, ns_facts, _ = C.read_bound(directory + "/NODE-SOURCE.json", keep=True)
    ns = json.loads(ns_raw.decode("ascii"))
    check("H2", "runtime.node_source.content equals NODE-SOURCE.json, which is canonical",
          rt["node_source"]["content"] == ns and C.canonical(ns) == ns_raw)
    check("H3", "NODE-SOURCE.json describes bin/node and the pinned archive",
          ns["extracted"]["sha256"] == node_facts["sha256"] and ns["extracted"]["size_bytes"] == node_facts["size_bytes"]
          and ns["extracted"]["mode"] == node_facts["mode"] and ns["archive"]["sha256"] == NODE_ARCHIVE_PIN
          and ns["archive"]["size_bytes"] == rt["archive"]["size_bytes"])
    facts, summary, problems = C.read_thin_macho(rt["executable"])
    out["node_macho_recomputed"] = summary
    check("H4", "bin/node is parsed from the bound bytes", C.binding(facts) == rt["binding"])
    check("H5", "runtime.macho equals this review's own parse, field for field", summary == rt["macho"],
          differing=[i for i, (a, b) in enumerate(zip(summary["commands"], rt["macho"]["commands"])) if a != b])
    check("H6", "no structural problem found by this review's parser", not problems, problems=problems)
    names = [row["name"] for row in summary["commands"]]
    dylibs = [row for row in summary["commands"] if row["name"] in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB")]
    check("H7", "thin MH_MAGIC_64, CPU_TYPE_ARM64, CPU_SUBTYPE_ARM64_ALL, MH_EXECUTE",
          summary["cputype"] == "0x0100000c" and summary["cpusubtype"] == "0x00000000"
          and summary["filetype"] == "MH_EXECUTE")
    check("H8", "every command inside the 16-command allow-list; no LC_RPATH, LC_DYLD_ENVIRONMENT, upward or re-export",
          all(n in NODE_ALLOWED for n in names), kinds=sorted(set(names)))
    check("H9", "exactly one LC_LOAD_DYLINKER (/usr/lib/dyld) and one LC_MAIN",
          names.count("LC_LOAD_DYLINKER") == 1 and names.count("LC_MAIN") == 1
          and [r["path"] for r in summary["commands"] if r["name"] == "LC_LOAD_DYLINKER"] == ["/usr/lib/dyld"])
    check("H10", "every dylib path normalized, absolute, not @-relative, under /usr/lib/ or /System/Library/",
          all(not r["path"].startswith("@") and os.path.normpath(r["path"]) == r["path"]
              and r["path"].startswith(("/usr/lib/", "/System/Library/")) for r in dylibs),
          dylibs=[r["path"] for r in dylibs])
    cf = summary["commands"][14] if len(summary["commands"]) > 14 else None
    check("H11", "D-16: command 14 is a plain LC_LOAD_DYLIB (0x0000000c) of CoreFoundation, in HOST and in this parse",
          cf is not None and cf["cmd"] == "0x0000000c" and cf["name"] == "LC_LOAD_DYLIB"
          and cf["path"] == "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation"
          and rt["macho"]["commands"][14] == cf, row=cf)
    sig = [r for r in summary["commands"] if r["name"] == "LC_CODE_SIGNATURE"][0]
    check("H12", "the code signature's data ends at the end of the file (no trailing bytes)",
          sig["dataoff"] + sig["datasize"] == facts["size_bytes"])

    # I. Git: binding, fat header, slices, embedded version text (N-07).
    git_facts, git_raw, slices = fat_slices(host["git"]["path"])
    check("I1", "Git is N34-M's file (SHA-256 and size)", git_facts["sha256"] == N34M_GIT["sha256"]
          and git_facts["size_bytes"] == N34M_GIT["size_bytes"])
    check("I2", "Git is not a link and is canonical", not C.linked_components(host["git"]["path"]))
    disp = os.stat("/usr/bin/git")
    _, disp_facts, _ = C.read_bound("/usr/bin/git")
    check("I3", "Git is neither the /usr/bin/git dispatcher nor a hard link or copy of it",
          (disp.st_dev, disp.st_ino) != (git_facts["dev"], git_facts["ino"]) and disp_facts["sha256"] != git_facts["sha256"])
    slice_rows = []
    for row in slices or []:
        body = git_raw[row["offset"]:row["offset"] + row["size"]]
        summary_s, problems_s = C.parse_thin(body, len(body))
        texts = sorted(set(m.decode("ascii") for m in re.findall(rb"\d+\.\d+\.\d+ \(Apple Git-\d+\)", body)))
        fmt = body.count(b"git version %s\n")
        refs = [c["path"] for c in summary_s["commands"] if c["name"] in C.DYLIB_KINDS and c["name"] != "LC_ID_DYLIB"]
        build = [c for c in summary_s["commands"] if c["name"] == "LC_BUILD_VERSION"]
        slice_rows.append({**row, "filetype": summary_s["filetype"], "ncmds": summary_s["ncmds"],
                           "dylibs": refs, "rpaths": [c["path"] for c in summary_s["commands"] if c["name"] == "LC_RPATH"],
                           "dylinker": [c["path"] for c in summary_s["commands"] if c["name"] == "LC_LOAD_DYLINKER"],
                           "unknown_commands": [c["cmd"] for c in summary_s["commands"] if c["name"] is None],
                           "build": build, "problems": problems_s, "version_texts": texts,
                           "format_count": fmt})
    out["git_slices"] = slice_rows
    arm64 = [r for r in slice_rows if r["cputype"] == "0x0100000c"]
    check("I4", "Git is fat with an x86_64 and an arm64 slice; the arm64 slice has subtype 0 and no arm64e slice exists",
          slices is not None and sorted(r["cputype"] for r in slice_rows) == ["0x01000007", "0x0100000c"]
          and len(arm64) == 1 and arm64[0]["cpusubtype"] == "0x00000000")
    stdout_raw = C.read_bound(plan["evidence"]["outputs"]["git_version"]["stdout"], keep=True)[0]
    predicted = "git version " + (arm64[0]["version_texts"][0] if arm64 and len(arm64[0]["version_texts"]) == 1 else "?") + "\n"
    out["git_version_line"] = {"recorded_stdout": stdout_raw.decode("ascii"), "host_version": host["git"]["version"],
                               "predicted_from_arm64_slice": predicted}
    check("I5", "N-07: the arm64 slice embeds one version text and the format 'git version %s\\n'",
          arm64 and len(arm64[0]["version_texts"]) == 1 and arm64[0]["format_count"] >= 1)
    check("I6", "N-07: the recorded line equals 'git version ' + the embedded text, and HOST.git.version is it without the newline",
          stdout_raw.decode("ascii") == predicted and host["git"]["version"] + "\n" == predicted
          and arm64[0]["version_texts"][0] == N34M_GIT["embedded"])
    check("I7", "Git's arm64 slice links only system paths and carries no LC_RPATH",
          arm64 and all(p.startswith(("/usr/lib/", "/System/Library/")) for p in arm64[0]["dylibs"])
          and not arm64[0]["rpaths"])

    # J. Reader tree against the dependency inventory, the C199 pins and the receipts.
    dep_inv = json.loads(C.read_bound(host["dependencies"]["inventory"]["path"], keep=True)[0])
    root = host["dependencies"]["root"]
    files, dirs, other = {}, {}, []
    for base, dnames, fnames in os.walk(root, followlinks=False):
        for name in dnames + fnames:
            path = os.path.join(base, name)
            rel = os.path.relpath(path, root)
            info = os.lstat(path)
            if stat.S_ISDIR(info.st_mode):
                dirs[rel] = C.mode_text(info.st_mode)
            elif stat.S_ISREG(info.st_mode):
                _, f, _ = C.read_bound(path)
                files[rel] = C.binding(f)
                if f["nlink"] != 1:
                    other.append(rel + " has more than one link")
            else:
                other.append(rel)
            if name == ".DS_Store":
                other.append(rel)
    check("J1", "the reader tree holds exactly the inventory's 24 files and its directories, all private and unlinked",
          files == dep_inv["files"] and dirs == dep_inv["directories"] and not other and len(files) == 24,
          other=other, missing=sorted(set(dep_inv["files"]) - set(files)), added=sorted(set(files) - set(dep_inv["files"])))
    ext_path = plan["source"]["root"] + "/docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json"
    ext_raw, ext_facts, _ = C.read_bound(ext_path, keep=True)
    ext = json.loads(ext_raw)
    prefix = ext["dependencies_root"] + "/"
    pins = {k[len(prefix):]: v for k, v in ext["files"].items() if k.startswith(prefix)}
    check("J2", "every reader file equals its C199 pin (EXTERNAL-INPUTS.json, SHA-256 21fd6bad...)",
          ext_facts["sha256"] == "21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5"
          and set(pins) == set(files)
          and all({"sha256": files[k]["sha256"], "size_bytes": files[k]["size_bytes"]} == pins[k] for k in pins))
    versions = {}
    for rel in ("validator/package/package.json", "indexer-view/three/package.json"):
        versions[rel] = json.loads(C.read_bound(root + "/" + rel, keep=True)[0]).get("version")
    check("J3", "validator 2.0.0-dev.3.10 and Three.js 0.186.1",
          versions == {"validator/package/package.json": "2.0.0-dev.3.10", "indexer-view/three/package.json": "0.186.1"})
    check("J4", "dependencies.files = 24 and dependencies.archive = the inventory's archive",
          host["dependencies"]["files"] == 24 and host["dependencies"]["archive"] == dep_inv["archive"])
    for owner, value in (("runtime", rt["install"]), ("dependencies", host["dependencies"]["install"])):
        receipt = json.loads(C.read_bound(value["result"]["path"], keep=True)[0])
        plan_doc = json.loads(C.read_bound(value["plan"]["path"], keep=True)[0])
        check("J5-" + owner, owner + ": receipt INSTALLED_EXACT, passed, zero starts, purpose and report as recorded",
              receipt["state"] == value["state"] == "INSTALLED_EXACT" and receipt["passed"] is True
              and receipt["purpose"] == value["purpose"] == plan_doc["purpose"]
              and plan_doc["report"] == value["result"]["path"]
              and receipt["execution_counts"] == {"checkers": 0, "ldd": 0, "node": 0},
              purpose=value["purpose"])

    # K. Shared cache and dyld (N-03), statically.
    cache_raw, cache_facts, _ = C.read_bound(CACHE_PATH, keep=True)
    magic = cache_raw[:16].split(b"\0", 1)[0].decode("ascii")
    mapping_offset = struct.unpack_from("<I", cache_raw, 16)[0]
    uuid = cache_raw[88:104].hex().upper()
    uuid = "-".join((uuid[:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:]))
    platform_id = struct.unpack_from("<I", cache_raw, 216)[0]
    os_version = struct.unpack_from("<I", cache_raw, 364)[0]
    sub_count = struct.unpack_from("<I", cache_raw, 396)[0]
    images_offset, images_count = struct.unpack_from("<II", cache_raw, 448)
    dyld_mh = struct.unpack_from("<Q", cache_raw, 120)[0]
    paths = set()
    for index in range(images_count):
        address, mod_time, inode, path_offset, _pad = struct.unpack_from("<QQQII", cache_raw, images_offset + 32 * index)
        end = cache_raw.index(b"\0", path_offset)
        paths.add(cache_raw[path_offset:end].decode("utf-8"))
    node_refs = [r["path"] for r in dylibs]
    git_refs = sorted(set(p for r in arm64 for p in r["dylibs"]))
    wanted = sorted(set(node_refs + git_refs + ["/usr/lib/dyld"]))
    on_disk = {p: os.path.lexists(p) for p in wanted}
    out["shared_cache"] = {"path": CACHE_PATH, **C.binding(cache_facts), "magic": magic,
                           "mapping_offset": mapping_offset, "uuid": uuid, "platform": platform_id,
                           "os_version": C._ver3(os_version), "subcaches": sub_count, "images": images_count,
                           "dyld_in_cache_mh": "0x%x" % dyld_mh,
                           "membership": {p: p in paths for p in wanted}, "on_disk": on_disk}
    check("K1", "N-03: the main cache file is N34-M's (SHA-256, size, UUID, platform, osVersion, images, subcaches)",
          cache_facts["sha256"] == N34M_CACHE["sha256"] and cache_facts["size_bytes"] == N34M_CACHE["size_bytes"]
          and uuid == N34M_CACHE["uuid"] and platform_id == N34M_CACHE["platform"]
          and C._ver3(os_version) == N34M_CACHE["os_version"] and images_count == N34M_CACHE["images"]
          and sub_count == N34M_CACHE["subcaches"] and dyld_mh == N34M_CACHE["dyld_in_cache_mh"]
          and mapping_offset >= 456)
    check("K2", "N-03: Node's four and Git's five system references are cache images and absent from disk",
          all(p in paths for p in node_refs + git_refs) and not any(on_disk[p] for p in node_refs + git_refs))
    _, dyld_facts, _ = C.read_bound("/usr/lib/dyld")
    out["dyld_on_disk"] = C.binding(dyld_facts)
    check("K3", "N-03: /usr/lib/dyld is on disk, equal to N34-M's bytes, and also in the cache's image table",
          dyld_facts["sha256"] == N34M_DYLD["sha256"] and dyld_facts["size_bytes"] == N34M_DYLD["size_bytes"]
          and "/usr/lib/dyld" in paths)
    check("K4", "N-03: the cache's osVersion (major.minor.patch) and HOST's OS identity agree on 26.6",
          C._ver3(os_version).startswith("26.6.") and host["os"]["system_version"]["product_version"].startswith("26.6"))

    # C5 and A2 completed with the inspection receipts' times.
    ins = {k: json.loads(C.read_bound(v["path"], keep=True)[0]) for k, v in host["inspections"].items()}
    CHECKS[:] = [c for c in CHECKS if c["id"] != "C5"]
    check("C5", "observed_at_utc follows both inspection receipts' finished_at_utc",
          all(host["observed_at_utc"] > row["finished_at_utc"] for row in ins.values()),
          observed=host["observed_at_utc"], finished={k: v["finished_at_utc"] for k, v in ins.items()})

    out["checks"] = CHECKS
    out["failed"] = [c["id"] for c in CHECKS if not c["passed"]]
    out["refused_events"] = C.REFUSED_EVENTS
    out["host_sha256"] = host_facts["sha256"]
    C.write_new(args.output, out)
    print(json.dumps({"failed": out["failed"], "checks": len(CHECKS), "host_sha256": host_facts["sha256"]}))


if __name__ == "__main__":
    main()
