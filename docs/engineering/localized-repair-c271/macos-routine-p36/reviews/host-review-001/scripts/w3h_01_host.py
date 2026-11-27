"""HOST review 001, script 01: HOST's bytes, closed shape and every binding I can recompute statically.

Reads HOST, the plan, the review record of the plan and the observer's source (parsed with ast,
never imported), and recomputes: the descriptors, the platform through sysctlbyname, the OS
identity and cryptex hop, the environment record and the CoreFoundation value's parts, the runtime
layout, bin/node's binding and Mach-O header and load commands with my own parser,
NODE-SOURCE.json, both install receipts under the receipt rule, the reader tree and its inventory
document, the C195 archive, the Git binding with N-07's embedded-version comparison, the
inspection descriptors, the starts, the labels and the claims.
Usage: python3 -I -S -B w3h_01_host.py --host H --plan P --review R --out OUT [--label PATH=LABEL ...]
"""
import argparse
import ast
import ctypes
import datetime
import os
import plistlib
import posixpath
import pwd
import re
import stat
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3h_common as C  # noqa: E402

C.install_hook()


# ---------------------------------------------------------------------------
# The observer's module-level constants, evaluated from its AST (no import, no execution)
# ---------------------------------------------------------------------------

# (the AST evaluator of the observer's constants is w3h_common.observer_constants)
# ---------------------------------------------------------------------------
# sysctlbyname
# ---------------------------------------------------------------------------

def sysctl_raw(name):
    libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    fn = libc.sysctlbyname
    fn.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p,
                   ctypes.c_size_t]
    fn.restype = ctypes.c_int
    size = ctypes.c_size_t(0)
    if fn(name.encode("ascii"), None, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), name)
    buf = ctypes.create_string_buffer(size.value)
    if fn(name.encode("ascii"), buf, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), name)
    return buf.raw[:size.value]


def utc(epoch):
    return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).isoformat()


def keys_are(value, expected):
    return isinstance(value, dict) and set(value) == set(expected)


def plist_fields(raw):
    value = plistlib.loads(raw)
    return {"product_name": value.get("ProductName"), "product_version": value.get("ProductVersion"),
            "product_build_version": value.get("ProductBuildVersion"),
            "product_version_extra": value.get("ProductVersionExtra")}


def canonical_ascii(value):
    import json
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("ascii")


def os_label_shape(value):
    def fields(row):
        return (isinstance(row.get("product_version"), str) and row["product_version"]
                and isinstance(row.get("product_build_version"), str) and row["product_build_version"]
                and (row.get("product_version_extra") is None or isinstance(row["product_version_extra"], str)))
    base = {"product_version", "product_build_version", "product_version_extra"}
    if not (isinstance(value, dict) and set(value) == base | {"cryptex"} and fields(value)):
        return False
    cx = value["cryptex"]
    return cx == {"state": "absent"} or (isinstance(cx, dict) and cx.get("state") == "present"
                                         and set(cx) == base | {"state"} and fields(cx))


def receipt_rule(ck, prefix, install, *, purpose, source_root, destination, archive, files, directories,
                 root_mode, executable, consts):
    """My own statement of W3-OBSERVER section 3's receipt rule (decisions D-05, D-11)."""
    plan_raw, plan_facts, _ = C.read_bytes(install["plan"]["path"])
    res_raw, res_facts, _ = C.read_bytes(install["result"]["path"])
    ck.add(prefix + "-01", C.binding(plan_facts) == {k: install["plan"][k] for k in ("sha256", "size_bytes", "mode")}
           and C.binding(res_facts) == {k: install["result"][k] for k in ("sha256", "size_bytes", "mode")},
           "the install plan and result have the bound SHA-256, size and mode")
    plan, res = C.strict_loads(plan_raw), C.strict_loads(res_raw)
    plan_keys = ("schema", "contract", "purpose", "source_root", "archive", "destination", "root_mode", "files",
                 "directories", "members", "node_source", "report")
    members = plan.get("members")
    ck.add(prefix + "-02", keys_are(plan, plan_keys) and plan["schema"] == consts["INSTALL_SCHEMA"]
           and plan["contract"] == consts["CONTRACT"] and plan["purpose"] == purpose
           and plan["source_root"] == source_root and plan["destination"] == destination
           and plan["root_mode"] == root_mode and plan["files"] == files and plan["directories"] == directories
           and plan["archive"] == archive and plan["report"] == install["result"]["path"]
           and isinstance(members, dict) and members
           and all(isinstance(r, dict) and isinstance(r.get("size_bytes"), int) for r in members.values()),
           "install/0.2.0 plan: closed keys; purpose, source root, destination, root mode, files, directories, "
           "archive and report path as bound", members=len(members or {}))
    state = res.get("state")
    base = ("schema", "contract", "design_revision", "amendments", "purpose", "passed", "state", "apply_requested",
            "execution_counts", "operations", "pins", "labels", "preparer_source")
    extra = {"ALREADY_PRESENT_EXACT": ("archive", "before"),
             "INSTALLED_EXACT": ("archive", "before", "after", "publication")}.get(state)
    pins_all = {"origin": "adopted-contract", "node_archive_sha256": consts["NODE_ARCHIVE_SHA256"],
                "dependency_archive_sha256": consts["DEPENDENCY_ARCHIVE_SHA256"]}
    ck.add(prefix + "-03", extra is not None and res.get("passed") is True and keys_are(res, base + extra)
           and res["schema"] == consts["INSTALL_RESULT_SCHEMA"] and res["contract"] == consts["CONTRACT"]
           and res["design_revision"] == consts["DESIGN_REVISION"] and res["amendments"] == list(consts["AMENDMENTS"])
           and res["purpose"] == purpose and isinstance(res["apply_requested"], bool)
           and res["execution_counts"] == {"node": 0, "ldd": 0, "checkers": 0}
           and isinstance(res["operations"], list)
           and all(r.get("operation") in ("created_owned_stage", "removed_owned_stage") for r in res["operations"])
           and res["pins"] == pins_all,
           "install-result/0.2.0: a passed receipt with the closed keys of its state, this contract and revision, "
           "zero starts, owned-stage operations only and the adopted pins", state=state)
    want_pins = ({"origin": "adopted-contract", "node_archive_sha256": consts["NODE_ARCHIVE_SHA256"],
                  "node_executable": executable} if purpose == "selected-node" else
                 {"origin": "adopted-contract", "dependency_archive_sha256": consts["DEPENDENCY_ARCHIVE_SHA256"]})
    labels = res.get("labels", {})
    ck.add(prefix + "-04", keys_are(labels, ("executor", "contract", "profile", "design_revision", "amendments",
                                             "pins", "os"))
           and labels["executor"] == consts["EXECUTOR"] and labels["contract"] == consts["CONTRACT"]
           and labels["profile"] == consts["PROFILE"] and labels["design_revision"] == consts["DESIGN_REVISION"]
           and labels["amendments"] == list(consts["AMENDMENTS"]) and labels["pins"] == want_pins
           and os_label_shape(labels["os"]), "the receipt's labels, with the pins of its purpose and HOST's OS "
           "label shape")
    src = res.get("preparer_source", {})
    ck.add(prefix + "-05", keys_are(src, ("root", "files_at_start")) and src["root"] == source_root,
           "preparer_source names this checkout")
    if state == "INSTALLED_EXACT":
        ok = (res["apply_requested"] is True and res["before"] == {"state": "absent"}
              and keys_are(res["after"], ("state", "files", "directories")) and res["after"]["state"] ==
              "complete_exact" and res["publication"] == {"call": "renamex_np", "library": "/usr/lib/libSystem.B.dylib",
                                                          "flag": "RENAME_EXCL", "flag_value": 4})
    else:
        ok = keys_are(res.get("before"), ("state", "files", "directories")) and res["before"]["state"] == \
            "complete_exact"
    ck.add(prefix + "-06", ok, "readbacks and publication of the receipt's state")
    summary = res.get("archive", {})
    mdig = C.sha256(canonical_ascii(members)) if isinstance(members, dict) else None
    want = {"sha256", "size_bytes", "members", "expanded_bytes", "symlinks", "member_inventory_sha256",
            "extracted_members"} | ({"executable"} if purpose == "selected-node" else set())
    ck.add(prefix + "-07", isinstance(summary, dict) and set(summary) == want and summary["sha256"] ==
           archive["sha256"] and summary["size_bytes"] == archive["size_bytes"] and summary["members"] == len(members)
           and summary["expanded_bytes"] == sum(r["size_bytes"] for r in members.values())
           and summary["member_inventory_sha256"] == mdig, "the archive summary equals the plan (digest, size, "
           "member count, expanded bytes and the member-inventory digest)", member_inventory_sha256=mdig)
    if purpose == "selected-node":
        ex = summary.get("executable", {})
        ck.add(prefix + "-08", keys_are(ex, ("member", "path", "sha256", "size_bytes", "mode", "macho"))
               and ex["member"] == consts["NODE_MEMBER"] and ex["path"] == "bin/node"
               and {k: ex[k] for k in ("sha256", "size_bytes", "mode")} == executable
               and keys_are(ex["macho"], ("magic", "cputype", "cpusubtype", "filetype")),
               "the receipt's extracted executable is the pinned bin/node")
    a_raw, a_facts, _ = C.read_bytes(archive["path"], keep=False)
    ck.add(prefix + "-09", C.binding(a_facts) == {k: archive[k] for k in ("sha256", "size_bytes", "mode")},
           "the retained archive has its bound bytes now")
    return plan, res, mdig


def main():
    ap = argparse.ArgumentParser()
    for name in ("--host", "--plan", "--review", "--disposition", "--launch", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--label", action="append", default=[])
    args = ap.parse_args()
    lab = C.Labeler([tuple(item.split("=", 1)) for item in args.label])
    ck = C.Checks()
    started = time.time()

    host_raw, host_facts, _ = C.read_bytes(args.host)
    host = C.strict_loads(host_raw)
    plan_raw, plan_facts, _ = C.read_bytes(args.plan)
    plan = C.strict_loads(plan_raw)
    review = C.strict_loads(C.read_bytes(args.review)[0])
    disposition = C.strict_loads(C.read_bytes(args.disposition)[0])
    launch = C.strict_loads(C.read_bytes(args.launch)[0])
    obs_path = plan["observer"]["path"]
    obs_raw, obs_facts, _ = C.read_bytes(obs_path)
    K = C.observer_constants(obs_raw.decode("utf-8"))
    needed = ("CONTRACT", "DESIGN_REVISION", "AMENDMENTS", "PROFILE", "EXECUTOR", "HOST_SCHEMA", "RUN_KIND",
              "ENVIRONMENT", "GIT_ENVIRONMENT", "CF_NAME", "LIMITS", "CLAIMS", "NODE_VERSION", "NODE_ARCHIVE",
              "NODE_ARCHIVE_SHA256", "NODE_CHECKSUM_FILE", "NODE_MEMBER", "NODE_SOURCE_SCHEMA", "INSTALL_SCHEMA",
              "INSTALL_RESULT_SCHEMA", "DEPENDENCY_ARCHIVE_SHA256", "DEPENDENCIES_SCHEMA", "EXTERNAL_INPUTS",
              "EXTERNAL_SHA256", "DEPENDENCY_VERSIONS", "FLAG_NAMES", "SYSTEM_VERSION_PATH",
              "CRYPTEX_SYSTEM_VERSION_PATH", "MACOS_LOCK", "PLAN_SCHEMA", "ENTRY_POINT", "GIT_DISPATCHER")
    ck.add("K00", all(n in K for n in needed), "the observer's constants evaluate statically from its AST",
           missing=[n for n in needed if n not in K])

    # --- A. bytes and identity ------------------------------------------------
    ck.add("A01", host_facts["sha256"] == "858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666",
           "HOST's SHA-256 from its bytes equals the value in the brief", sha256=host_facts["sha256"])
    ck.add("A02", host_facts["size_bytes"] == 18420 and host_facts["mode"] == "0o600" and host_facts["nlink"] == 1,
           "HOST is 18,420 bytes, mode 0o600, one link", size=host_facts["size_bytes"], mode=host_facts["mode"])
    ck.add("A03", C.canonical(host) == host_raw, "HOST is canonical JSON (sorted, compact, ASCII) with no duplicate "
           "member")
    plan_digest = review["plan"]["sha256"]
    ck.add("A04", plan_facts["sha256"] == plan_digest == disposition["plan_digest_for_s5"]["value"]
           == "cc1c2defd73d8d1ade22a8c772308c0e3d2fad3262a83c946c1733aecf429d5e" and C.canonical(plan) == plan_raw,
           "the plan's bytes have the review record's digest, which the disposition carries to S5")

    # --- B. closed shape ------------------------------------------------------
    top = ("schema", "contract", "design_revision", "amendments", "profile", "executor", "observed_at_utc", "plan",
           "observer", "platform", "os", "environment", "python", "runtime", "git", "dependencies", "source",
           "inspections", "starts", "labels", "claims")
    shape = [
        ("", host, top),
        ("/platform", host["platform"], ("system", "release", "version", "machine", "proc_translated",
                                          "boot_session_uuid")),
        ("/os", host["os"], ("system_version", "cryptex")),
        ("/os/system_version", host["os"]["system_version"], ("state", "path", "sha256", "size_bytes", "mode",
                                                              "product_name", "product_version",
                                                              "product_build_version", "product_version_extra")),
        ("/os/cryptex", host["os"]["cryptex"], ("state", "path", "sha256", "size_bytes", "mode", "product_name",
                                                "product_version", "product_build_version", "product_version_extra",
                                                "link_path", "hops")),
        ("/environment", host["environment"], ("declared", "cf_user_text_encoding")),
        ("/python", host["python"], ("launcher", "venv", "framework", "interpreter", "selection", "inventory",
                                     "inventory_sha256", "packages", "records", "lock")),
        ("/python/interpreter", host["python"]["interpreter"], ("implementation", "version", "build_string", "flags",
                                                                "executable", "base_executable", "prefix",
                                                                "base_prefix", "path", "process_image")),
        ("/python/interpreter/flags", host["python"]["interpreter"]["flags"], K["FLAG_NAMES"]),
        ("/python/selection", host["python"]["selection"], ("launcher", "launcher_chain", "pyvenv_cfg", "home_chain",
                                                            "home_launcher_chain", "executable_chain",
                                                            "process_image", "version_directory")),
        ("/python/inventory", host["python"]["inventory"], ("path", "sha256", "size_bytes", "mode")),
        ("/python/lock", host["python"]["lock"], ("path", "sha256", "size_bytes", "mode")),
        ("/runtime", host["runtime"], ("directory", "executable", "version", "binding", "archive", "node_source",
                                       "layout", "macho", "install")),
        ("/runtime/binding", host["runtime"]["binding"], ("sha256", "size_bytes", "mode")),
        ("/runtime/archive", host["runtime"]["archive"], ("path", "sha256", "size_bytes", "mode")),
        ("/runtime/node_source", host["runtime"]["node_source"], ("path", "sha256", "size_bytes", "mode", "content")),
        ("/runtime/layout", host["runtime"]["layout"], ("root_mode", "bin_mode", "entries")),
        ("/runtime/macho", host["runtime"]["macho"], ("magic", "cputype", "cpusubtype", "filetype", "flags", "ncmds",
                                                      "sizeofcmds", "commands")),
        ("/runtime/install", host["runtime"]["install"], ("plan", "result", "purpose", "state")),
        ("/git", host["git"], ("path", "sha256", "size_bytes", "mode", "version")),
        ("/dependencies", host["dependencies"], ("root", "inventory", "archive", "files", "install")),
        ("/dependencies/install", host["dependencies"]["install"], ("plan", "result", "purpose", "state")),
        ("/source", host["source"], ("root", "commit", "tree", "tree_check", "inventory", "head")),
        ("/source/head", host["source"]["head"], ("gitdir", "common_dir", "ref", "commit", "files")),
        ("/inspections", host["inspections"], ("git_version", "node_version")),
        ("/starts", host["starts"], ("node", "other")),
        ("/labels", host["labels"], ("executor", "contract", "design_revision", "amendments", "profile", "os", "node",
                                     "python_inventory_sha256", "git", "run_kind", "boundary")),
        ("/labels/os", host["labels"]["os"], ("product_version", "product_build_version", "product_version_extra",
                                              "cryptex")),
        ("/labels/os/cryptex", host["labels"]["os"]["cryptex"], ("state", "product_version", "product_build_version",
                                                                 "product_version_extra")),
        ("/labels/node", host["labels"]["node"], ("archive", "archive_sha256", "executable", "signature_check")),
        ("/labels/git", host["labels"]["git"], ("path", "sha256")),
        ("/claims", host["claims"], ("closure", "python", "boot", "status")),
    ]
    bad = [p for p, v, k in shape if not keys_are(v, k)]
    ck.add("B01", not bad, "every object of HOST has exactly W3-OBSERVER section 3's members", objects=len(shape),
           not_closed=bad)
    ck.add("B02", host["schema"] == K["HOST_SCHEMA"] == "ontokin.current-host-readback-host/0.2.0"
           and host["contract"] == K["CONTRACT"] and host["design_revision"] == K["DESIGN_REVISION"] == 4
           and host["amendments"] == list(K["AMENDMENTS"]) == ["P33-AMENDMENT-001"]
           and host["profile"] == K["PROFILE"] and host["executor"] == K["EXECUTOR"],
           "schema, contract, design revision 4, amendments, profile and executor")
    ck.add("B03", host["claims"] == K["CLAIMS"] and host["claims"]["status"].startswith("OBSERVED_UNAPPROVED:"),
           "the four claims are the observer's fixed texts; status OBSERVED_UNAPPROVED")
    ck.add("B04", host["starts"] == {"node": 1, "other": 1}, "/starts is {node: 1, other: 1}")

    # --- C. plan and observer descriptors ------------------------------------
    ck.add("C01", host["plan"] == C.descriptor(args.plan, plan_facts), "/plan is the plan file's descriptor")
    ck.add("C02", host["observer"] == plan["observer"] == C.descriptor(obs_path, obs_facts) and obs_facts["nlink"] == 1,
           "/observer equals the plan's observer and the file now")
    src_inv = C.strict_loads(C.read_bytes(plan["source"]["inventory"]["path"])[0])
    ck.add("C03", src_inv["files"].get(K["ENTRY_POINT"]) == C.binding(obs_facts),
           "the source inventory binds the observer with the same bytes")

    # --- D. platform -----------------------------------------------------------
    un = os.uname()
    boot = sysctl_raw("kern.bootsessionuuid").rstrip(b"\0").decode("ascii")
    translated = struct.unpack("=i", sysctl_raw("sysctl.proc_translated"))[0]
    osversion = sysctl_raw("kern.osversion").rstrip(b"\0").decode("ascii")
    bt = sysctl_raw("kern.boottime")
    boot_sec, boot_usec = struct.unpack_from("=qi", bt, 0)
    p, pp = host["platform"], plan["platform"]
    ck.add("D01", p["system"] == un.sysname == pp["system"] == "Darwin" and p["machine"] == un.machine ==
           pp["machine"] == "arm64", "Darwin and arm64, as os.uname() gives them now")
    ck.add("D02", p["release"] == un.release == pp["release"] and p["version"] == un.version,
           "release (as planned) and the kernel version string equal os.uname() now")
    ck.add("D03", p["proc_translated"] == translated == pp["proc_translated"] == 0,
           "sysctl.proc_translated is 0 (native), for this reader too")
    ck.add("D04", p["boot_session_uuid"] == boot == pp["boot_session_uuid"] == "C90010BA-4DA9-475D-BBAB-CF1A9C40175A",
           "kern.bootsessionuuid now is the plan's and HOST's boot", boottime_utc=utc(boot_sec + boot_usec / 1e6))
    ck.add("D05", osversion == host["os"]["system_version"]["product_build_version"],
           "kern.osversion equals the recorded build", kern_osversion=osversion)

    # --- E. OS identity -------------------------------------------------------
    sv = host["os"]["system_version"]
    sv_raw, sv_facts, _ = C.read_bytes(K["SYSTEM_VERSION_PATH"])
    ck.add("E01", sv["path"] == K["SYSTEM_VERSION_PATH"] and C.has_linked_component(sv["path"]) is None
           and C.binding(sv_facts) == {k: sv[k] for k in ("sha256", "size_bytes", "mode")}
           == {k: plan["os"]["system_version"][k] for k in ("sha256", "size_bytes", "mode")}
           and sv["state"] == "present" and plist_fields(sv_raw) == {k: sv[k] for k in ("product_name",
                                                                                      "product_version",
                                                                                      "product_build_version",
                                                                                      "product_version_extra")},
           "SystemVersion.plist: canonical, bound bytes, and its four fields", fields=plist_fields(sv_raw))
    cx = host["os"]["cryptex"]
    chain = C.resolve_chain(K["CRYPTEX_SYSTEM_VERSION_PATH"])
    cx_raw, cx_facts, _ = C.read_bytes(chain["path"])
    ck.add("E02", cx["link_path"] == K["CRYPTEX_SYSTEM_VERSION_PATH"] and chain["state"] == "file"
           and chain["path"] == cx["path"] == plan["os"]["cryptex"]["path"] and chain["hops"] == cx["hops"]
           and C.has_linked_component(cx["path"]) is None and cx["state"] == plan["os"]["cryptex"]["state"] == "present"
           and C.binding(cx_facts) == {k: cx[k] for k in ("sha256", "size_bytes", "mode")}
           == {k: plan["os"]["cryptex"][k] for k in ("sha256", "size_bytes", "mode")}
           and plist_fields(cx_raw) == {k: cx[k] for k in ("product_name", "product_version",
                                                         "product_build_version", "product_version_extra")},
           "the cryptex copy: my resolver gives the recorded single hop and canonical path; bytes and fields agree",
           hops=chain["hops"])
    label_os = {"product_version": sv["product_version"], "product_build_version": sv["product_build_version"],
                "product_version_extra": sv["product_version_extra"],
                "cryptex": {"state": "present", "product_version": cx["product_version"],
                            "product_build_version": cx["product_build_version"],
                            "product_version_extra": cx["product_version_extra"]}}
    ck.add("E03", host["labels"]["os"] == label_os and os_label_shape(label_os), "/labels/os is derived from /os")

    # --- F. environment -------------------------------------------------------
    env = host["environment"]
    menv_path = posixpath.join(posixpath.dirname(args.plan), "M0-ENVIRONMENT.json")
    menv_raw, menv_facts, _ = C.read_bytes(menv_path)
    ck.add("F01", env["declared"] == plan["environment"] == K["ENVIRONMENT"] == {
        "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
        and K["CF_NAME"] not in env["declared"], "/environment/declared is exactly the five declared variables")
    ck.add("F02", menv_raw == C.canonical(plan["environment"]) and menv_facts["sha256"] ==
           launch["environment_file"]["sha256"] == "0ed78f47b1929634d65b6407b8e8daf047aeb2daa6b5c194c24e91a7b91ebcf2",
           "M0-ENVIRONMENT.json is the canonical declared environment that the command records bind")
    cf = env["cf_user_text_encoding"]
    mine = os.environ.get(K["CF_NAME"])
    user = pwd.getpwuid(os.getuid())
    cf_file = os.path.join(user.pw_dir, ".CFUserTextEncoding")
    cf_raw, cf_facts, _ = C.read_bytes(cf_file)
    composed = "0x%X:%s" % (os.getuid(), cf_raw.decode("ascii").strip())
    ck.add("F03", isinstance(cf, str) and cf != "" and cf == mine,
           "HOST's CoreFoundation value is a non-empty string equal to this reviewer's process value now "
           "(compared, not printed)")
    ck.add("F04", cf == composed and cf_facts["sha256"] ==
           "bd605d2eae2bc28178ba94d69e189242f971d699c5846addae706d7e52bc69fd" and cf_facts["size_bytes"] == 7
           and cf_facts["mode"] == "0o400",
           "the value is 0x + the UID in hex + ':' + the content of <home>/.CFUserTextEncoding, whose bytes are those "
           "recorded under MH's HR-02", file_mtime_utc=utc(cf_facts["mtime_ns"] / 1e9))

    # --- G. runtime -----------------------------------------------------------
    rt, prt = host["runtime"], plan["runtime"]
    directory = prt["directory"]
    walk = {}
    for dirpath, dirnames, filenames in os.walk(directory):
        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            walk[os.path.relpath(path, directory)] = os.lstat(path)
    kinds = {r: ("directory" if stat.S_ISDIR(s.st_mode) else "file" if stat.S_ISREG(s.st_mode) else "other")
             for r, s in walk.items()}
    root_mode = C.mode_text(os.lstat(directory).st_mode)
    ck.add("G01", rt["directory"] == directory and kinds == {"bin": "directory", "bin/node": "file",
                                                             "NODE-SOURCE.json": "file"}
           and root_mode == prt["root_mode"] == rt["layout"]["root_mode"] == "0o755"
           and C.mode_text(walk["bin"].st_mode) == prt["bin_mode"] == rt["layout"]["bin_mode"] == "0o755"
           and rt["layout"]["entries"] == sorted(kinds), "the runtime directory holds exactly bin/, bin/node and "
           "NODE-SOURCE.json, with the planned modes")
    node_path = directory + "/bin/node"
    node_raw, node_facts, _ = C.read_bytes(node_path)
    nb = C.binding(node_facts)
    ck.add("G02", rt["executable"] == node_path and nb == rt["binding"] == prt["executable"]
           == host["labels"]["node"]["executable"] and node_facts["nlink"] == 1 and rt["version"] == prt["version"] ==
           K["NODE_VERSION"] == "v24.22.1", "bin/node: path, SHA-256, size, mode, one link; version v24.22.1",
           sha256=nb["sha256"], size=nb["size_bytes"])
    mine_macho = C.parse_thin(node_raw, len(node_raw))
    ck.add("G03", mine_macho == rt["macho"], "my parse of bin/node equals /runtime/macho field for field "
           "(header and all load commands)", ncmds=mine_macho["ncmds"], sizeofcmds=mine_macho["sizeofcmds"])
    names = [c["name"] for c in mine_macho["commands"]]
    allowed = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
               "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
               "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
               "LC_DYLD_EXPORTS_TRIE"}
    dylibs = [c["path"] for c in mine_macho["commands"] if c["name"] in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB")]
    sig = [c for c in mine_macho["commands"] if c["name"] == "LC_CODE_SIGNATURE"]
    ck.add("G04", mine_macho["magic"] == "MH_MAGIC_64" and mine_macho["cputype"] == "0x0100000c"
           and mine_macho["cpusubtype"] == "0x00000000" and mine_macho["filetype"] == "MH_EXECUTE"
           and all(n in allowed for n in names) and names.count("LC_LOAD_DYLINKER") == 1 and names.count("LC_MAIN") == 1
           and [c["path"] for c in mine_macho["commands"] if c["name"] == "LC_LOAD_DYLINKER"] == ["/usr/lib/dyld"]
           and all(d.startswith(("/usr/lib/", "/System/Library/")) and posixpath.normpath(d) == d for d in dylibs)
           and not any(d.startswith("@") for d in dylibs) and node_raw[:4] == b"\xcf\xfa\xed\xfe",
           "contract section 7's Node rules: thin arm64 MH_EXECUTE, the closed list, one dylinker /usr/lib/dyld, "
           "one LC_MAIN, system dylibs only, no @ path and no LC_RPATH", dylibs=dylibs,
           kinds=sorted(set(names)))
    ck.add("G05", len(sig) == 1 and sig[0]["dataoff"] + sig[0]["datasize"] == len(node_raw),
           "the code signature ends exactly at the end of the file")
    cf_cmd = mine_macho["commands"][14]
    ck.add("G06", cf_cmd["cmd"] == "0x0000000c" and cf_cmd["name"] == "LC_LOAD_DYLIB" and cf_cmd["path"] ==
           "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation",
           "D-16 still holds: command 14 is a plain LC_LOAD_DYLIB of CoreFoundation")
    ns_path = directory + "/NODE-SOURCE.json"
    ns_raw, ns_facts, _ = C.read_bytes(ns_path)
    ns = C.strict_loads(ns_raw)
    a = rt["archive"]
    _, arc_facts, _ = C.read_bytes(a["path"], keep=False)
    ck.add("G07", rt["node_source"] == {"path": ns_path, **C.binding(ns_facts), "content": ns}
           and C.binding(ns_facts) == prt["node_source"] and ns_facts["nlink"] == 1
           and canonical_ascii(ns) == ns_raw, "NODE-SOURCE.json: bound bytes, canonical, and /runtime/node_source "
           "carries its parsed content")
    ck.add("G08", keys_are(ns, ("schema", "contract", "archive", "checksum_file", "signature_check",
                                "member_inventory_sha256", "extracted"))
           and ns["schema"] == K["NODE_SOURCE_SCHEMA"] and ns["contract"] == K["CONTRACT"]
           and ns["archive"] == {"name": K["NODE_ARCHIVE"], "sha256": K["NODE_ARCHIVE_SHA256"],
                                 "size_bytes": arc_facts["size_bytes"]}
           and ns["checksum_file"] == K["NODE_CHECKSUM_FILE"]
           and ns["signature_check"]["status"] == "not_performed" == host["labels"]["node"]["signature_check"]
           and ns["extracted"] == {"member": K["NODE_MEMBER"], "path": "bin/node", **nb},
           "NODE-SOURCE.json's content: the pinned archive with its actual size, the checksum file, a recorded "
           "not_performed signature check, and the extracted bin/node binding")
    ck.add("G09", a == prt["archive"] == C.descriptor(a["path"], arc_facts) and a["sha256"] == K["NODE_ARCHIVE_SHA256"]
           and arc_facts["nlink"] == 1, "the retained Node archive: bound bytes and mode, SHA-256 equal to the pin")
    plan_n, res_n, mdig_n = receipt_rule(
        ck, "G10", prt["install"], purpose="selected-node", source_root=plan["source"]["root"], destination=directory,
        archive=prt["archive"], files={"bin/node": prt["executable"], "NODE-SOURCE.json": prt["node_source"]},
        directories={"bin": prt["bin_mode"]}, root_mode=prt["root_mode"], executable=prt["executable"], consts=K)
    ck.add("G11", plan_n["node_source"] == {"signature_check": ns["signature_check"]}
           and mdig_n == ns["member_inventory_sha256"] and ns["archive"]["size_bytes"] == prt["archive"]["size_bytes"],
           "NODE-SOURCE.json agrees with the install plan (signature check, member digest, archive size)")
    ck.add("G12", rt["install"] == {"plan": prt["install"]["plan"], "result": prt["install"]["result"],
                                    "purpose": "selected-node", "state": res_n["state"]}
           and res_n["state"] == "INSTALLED_EXACT", "/runtime/install records the plan, the receipt, the purpose and "
           "the state INSTALLED_EXACT")

    # --- H. dependencies (the reader tree) -----------------------------------
    dp, pdp = host["dependencies"], plan["dependencies"]
    root = pdp["root"]
    inv_raw, inv_facts, _ = C.read_bytes(pdp["inventory"]["path"])
    inv = C.strict_loads(inv_raw)
    files, dirs, extras = {}, {}, []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames:
            path = os.path.join(dirpath, name)
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                extras.append("link:" + name)
            dirs[os.path.relpath(path, root)] = C.mode_text(info.st_mode)
        for name in filenames:
            path = os.path.join(dirpath, name)
            if name == ".DS_Store":
                extras.append(".DS_Store")
            info = os.lstat(path)
            if not stat.S_ISREG(info.st_mode):
                extras.append("special:" + name)
                continue
            _, facts, _ = C.read_bytes(path, keep=False)
            if facts["nlink"] != 1:
                extras.append("multilink:" + name)
            files[os.path.relpath(path, root)] = C.binding(facts)
    arch = inv["archive"]
    _, dar_facts, _ = C.read_bytes(arch["path"], keep=False)
    rebuilt = {"schema": K["DEPENDENCIES_SCHEMA"], "files": files, "directories": dirs,
               "archive": C.descriptor(arch["path"], dar_facts)}
    ck.add("H01", C.canonical(rebuilt) == inv_raw and inv_facts["sha256"] ==
           "3545d5f920ac840804a9e25d28a87d623f96af71537fd3f020a0c1d743f82fb4" and not extras,
           "the reader tree recomputed now (24 files, their directories, the retained C195 archive) gives a document "
           "byte-identical to the frozen dependency inventory", files=len(files), directories=len(dirs),
           recomputed_sha256=C.sha256(C.canonical(rebuilt)), problems=extras)
    ext_raw, ext_facts, _ = C.read_bytes(plan["source"]["root"] + "/" + K["EXTERNAL_INPUTS"])
    ext = C.strict_loads(ext_raw)
    pre = ext["dependencies_root"] + "/"
    pins = {n[len(pre):]: r for n, r in ext["files"].items() if n.startswith(pre)}
    ck.add("H02", ext_facts["sha256"] == K["EXTERNAL_SHA256"] and len(pins) == 24
           and {n: {"sha256": b["sha256"], "size_bytes": b["size_bytes"]} for n, b in files.items()} == pins,
           "the 24 files equal C199's historical pins of EXTERNAL-INPUTS.json")
    necessary = set()
    for name in files:
        parts = name.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            necessary.add("/".join(parts[:i]))
    versions = {}
    for name, version in K["DEPENDENCY_VERSIONS"]:
        versions[name] = C.strict_loads(C.read_bytes(root + "/" + name)[0]).get("version")
    ck.add("H03", set(dirs) == necessary and versions == {n: v for n, v in K["DEPENDENCY_VERSIONS"]},
           "the directories are exactly the necessary ones; validator 2.0.0-dev.3.10 and Three.js 0.186.1",
           versions=versions)
    ck.add("H04", dp["root"] == root and dp["inventory"] == pdp["inventory"] == C.descriptor(pdp["inventory"]["path"],
                                                                                            inv_facts)
           and dp["archive"] == inv["archive"] == C.descriptor(arch["path"], dar_facts)
           and dar_facts["sha256"] == K["DEPENDENCY_ARCHIVE_SHA256"] and dp["files"] == len(files) == 24,
           "/dependencies: root, inventory descriptor, archive descriptor (the C195 pin) and 24 files")
    plan_d, res_d, _ = receipt_rule(
        ck, "H05", pdp["install"], purpose="retained-dependencies", source_root=plan["source"]["root"],
        destination=root, archive=inv["archive"], files={n: {k: b[k] for k in ("sha256", "size_bytes", "mode")}
                                                         for n, b in inv["files"].items()},
        directories=inv["directories"], root_mode=C.mode_text(os.lstat(root).st_mode), executable=None, consts=K)
    ck.add("H06", plan_d["node_source"] is None and dp["install"] == {
        "plan": pdp["install"]["plan"], "result": pdp["install"]["result"], "purpose": "retained-dependencies",
        "state": res_d["state"]} and res_d["state"] == "INSTALLED_EXACT",
        "/dependencies/install: plan, receipt, purpose, INSTALLED_EXACT, and no node_source in the reader plan")

    # --- I. Git ---------------------------------------------------------------
    g, pg = host["git"], plan["git"]
    git_raw, git_facts, _ = C.read_bytes(pg["path"])
    disp = os.stat(K["GIT_DISPATCHER"])
    _, disp_facts, _ = C.read_bytes(K["GIT_DISPATCHER"], keep=False)
    ck.add("I01", {k: g[k] for k in ("path", "sha256", "size_bytes", "mode")} == pg == C.descriptor(pg["path"],
                                                                                                    git_facts)
           and g["sha256"] == "be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae"
           and not stat.S_ISLNK(os.lstat(pg["path"]).st_mode) and C.has_linked_component(pg["path"]) is None,
           "/git: the plan's binding and the file now; N34-M's file; canonical, not a link")
    ck.add("I02", pg["path"] != K["GIT_DISPATCHER"] and (disp.st_dev, disp.st_ino) != (git_facts["dev"],
                                                                                      git_facts["ino"])
           and disp_facts["sha256"] != git_facts["sha256"],
           "not the /usr/bin/git dispatcher, nor its hard link, nor its bytes")
    slices = C.parse_fat(git_raw)
    arm = [s for s in slices if s["cputype"] == "0x0100000c"]
    ck.add("I03", [(s["cputype"], s["cpusubtype"]) for s in slices] == [("0x01000007", "0x00000003"),
                                                                      ("0x0100000c", "0x00000000")],
           "the bound Git is universal with an x86_64 slice (subtype 3) and an arm64 slice (subtype 0) and no arm64e "
           "slice, so this host runs its arm64 slice", slices=slices)
    sl = git_raw[arm[0]["offset"]:arm[0]["offset"] + arm[0]["size"]]
    thin = C.parse_thin(sl, len(sl))
    git_dylibs = [c["path"] for c in thin["commands"] if c["name"] in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB")]
    ck.add("I04", thin["filetype"] == "MH_EXECUTE" and not any(c["name"] == "LC_RPATH" for c in thin["commands"])
           and all(d.startswith(("/usr/lib/", "/System/Library/")) for d in git_dylibs),
           "N-07: the arm64 slice is an executable that links only system libraries and has no LC_RPATH",
           ncmds=thin["ncmds"], dylibs=git_dylibs)
    texts = sorted(set(m.decode("ascii") for m in re.findall(rb"\d+\.\d+\.\d+ \(Apple Git-\d+\)", sl)))
    counts = {t: sl.count(t.encode("ascii")) for t in texts}
    fmt = sl.count(b"git version %s\n")
    stdout_path = plan["evidence"]["outputs"]["git_version"]["stdout"]
    out_raw = C.read_bytes(stdout_path)[0]
    ck.add("I05", len(texts) == 1 and g["version"] == "git version " + texts[0] and fmt >= 1
           and out_raw == (g["version"] + "\n").encode("ascii"),
           "N-07: the recorded line is exactly 'git version ' + the one version text embedded in the arm64 slice; "
           "the retained stdout is that line with its newline", embedded=texts, occurrences=counts,
           format_occurrences=fmt)
    ck.add("I06", re.fullmatch(rb"git version [\x20-\x7e]{1,200}\n", out_raw) is not None
           and host["labels"]["git"] == {"path": g["path"], "sha256": g["sha256"]},
           "the line fits git-version-line-v1, and /labels/git is {path, sha256}")

    # --- J. source descriptors (HEAD and the tree are script 03's) -----------
    s, ps = host["source"], plan["source"]
    tree_check = "planned value; M0 starts no Git read, and the provider's bound Git reads verify it"
    sinv_raw, sinv_facts, _ = C.read_bytes(ps["inventory"]["path"])
    ck.add("J01", s["root"] == ps["root"] and s["commit"] == ps["commit"] ==
           "4ca781429c5411c67c0965bc69306b42c6cc74ad" and s["tree"] == ps["tree"] ==
           "0935162c72fd9d804681e920da6f6d6e9066ff28" and s["inventory"] == ps["inventory"] ==
           C.descriptor(ps["inventory"]["path"], sinv_facts) and s["tree_check"] == tree_check
           and tree_check.encode("ascii") in obs_raw and s["head"]["commit"] == ps["commit"],
           "/source: root, commit B, tree, the source inventory's descriptor, the observer's tree_check text, and "
           "HEAD's commit B")
    hp = host["python"]
    lock_path = ps["root"] + "/" + K["MACOS_LOCK"]
    _, lock_facts, _ = C.read_bytes(lock_path, keep=False)
    ck.add("J02", hp["lock"] == C.descriptor(lock_path, lock_facts) and src_inv["files"][K["MACOS_LOCK"]] ==
           C.binding(lock_facts), "/python/lock: the macOS lock in the worktree, as the source inventory binds it")

    # --- K. interpreter facts that this process can check --------------------
    it = host["python"]["interpreter"]
    pyf = host["python"]["framework"]
    ck.add("K01", it["implementation"] == "cpython" and it["version"] == plan["python"]["version"] == "3.12.13"
           and it["build_string"] == sys.version and it["prefix"] == it["base_prefix"] == pyf
           and it["base_executable"] == pyf + "/bin/python3.12" and it["executable"] == hp["launcher"]
           and it["process_image"] == pyf + "/Resources/Python.app/Contents/MacOS/Python"
           and it["path"] == [pyf + "/lib/python312.zip", pyf + "/lib/python3.12", pyf + "/lib/python3.12/lib-dynload"],
           "/python/interpreter: CPython 3.12.13 with this interpreter's build string, launched through the venv, "
           "prefix the framework, process image Python.app, and the isolated sys.path")
    fl = it["flags"]
    ck.add("K02", fl["isolated"] == 1 and fl["no_site"] == 1 and fl["dont_write_bytecode"] == 1
           and fl["ignore_environment"] == 1 and fl["no_user_site"] == 1 and fl["safe_path"] is True
           and fl["utf8_mode"] == 0, "/python/interpreter/flags: -I -S -B, safe_path, and utf8_mode 0 under "
           "LC_ALL=C.UTF-8")

    # --- L. inspections, starts and labels ------------------------------------
    outs = plan["evidence"]["outputs"]
    rows = {}
    for cid in ("git_version", "node_version"):
        _, f, _ = C.read_bytes(outs[cid]["inspection"], keep=False)
        rows[cid] = host["inspections"][cid] == C.descriptor(outs[cid]["inspection"], f)
    ck.add("L01", all(rows.values()), "/inspections are the two inspection receipts' descriptors, at the planned "
           "paths", rows=rows)
    lb = host["labels"]
    ck.add("L02", lb["executor"] == K["EXECUTOR"] and lb["contract"] == K["CONTRACT"] and lb["design_revision"] == 4
           and lb["amendments"] == ["P33-AMENDMENT-001"] and lb["profile"] == K["PROFILE"]
           and lb["node"] == {"archive": K["NODE_ARCHIVE"], "archive_sha256": K["NODE_ARCHIVE_SHA256"],
                              "executable": nb, "signature_check": "not_performed"}
           and lb["python_inventory_sha256"] == hp["inventory_sha256"] == plan["python"]["inventory"]["sha256"]
           and lb["run_kind"] == K["RUN_KIND"] == "host-observation" and lb["boundary"] == "real",
           "the labels: executor, contract with revision 4 and the amendment, profile, OS (E03), Node pins, the "
           "inventory digest, Git (I06), run kind host-observation, boundary real")
    insp = {cid: C.strict_loads(C.read_bytes(outs[cid]["inspection"])[0]) for cid in ("git_version", "node_version")}
    observed = datetime.datetime.fromisoformat(host["observed_at_utc"])
    finished = max(datetime.datetime.fromisoformat(insp[c]["finished_at_utc"]) for c in insp)
    rec = C.strict_loads(C.read_bytes(posixpath.join(posixpath.dirname(plan["evidence"]["attempt"]),
                                                     "observe-001.observe.command.json"))[0])
    t0, t1 = float(rec["start_epoch_s"]), float(rec["end_epoch_s"])
    ck.add("L03", observed > finished and t0 <= observed.timestamp() <= t1,
           "/observed_at_utc is later than both inspection receipts and inside observe's command window",
           observed=host["observed_at_utc"], last_inspection_end=finished.isoformat(), window=[utc(t0), utc(t1)])
    ck.add("L04", hp["venv"] == plan["python"]["venv"] == ps["root"] + "/.venv" and hp["framework"] ==
           plan["python"]["framework"] and hp["inventory"] == plan["python"]["inventory"],
           "/python: venv, framework and frozen inventory descriptor as planned")

    result = {"script": "w3h_01_host.py", "process": C.process_identity(), "started_epoch": started,
              "ended_epoch": time.time(), "host": {"sha256": host_facts["sha256"], "size_bytes": host_facts["size_bytes"],
                                                   "mode": host_facts["mode"], "nlink": host_facts["nlink"]},
              "checks": ck.rows, "summary": ck.summary(), "audit_events": C.EVENTS}
    print(C.write_new(args.out, lab.deep(result)), ck.summary())


if __name__ == "__main__":
    main()
