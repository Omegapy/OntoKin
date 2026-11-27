"""W3 plan review 001, script s02: every key of observation plan 001 against the actual state.

Standard library only; nothing of the project is imported. Starts nothing (an audit hook
refuses every process-creation event). Follows no link when hashing. Writes only its one
absent output file. Every path is an argument or a path relative to an argument.

The expected constants are written here from the adopted contract (sections 3, 7 and 10),
W3-OBSERVER section 2 and, for LIMITS, which the schema names without listing, from the
observer's source (the LIMITS mapping). They are not imported.

Usage:
  python -I -S -B s02_plan_keys.py --worktree WT --local LOCAL --plan-dir W2DIR --output OUT.json
"""
import argparse
import ctypes
import hashlib
import json
import os
import plistlib
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

LIBSYSTEM = "/usr/lib/libSystem.B.dylib"
PLAN_SCHEMA = "ontokin.current-host-readback-observation-plan/0.2.0"
CONTRACT = "ontokin.current-host-readback/0.2.0"
PROFILE = "darwin-arm64-v1"
EXECUTOR = "macos-arm64-local"
ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
GIT_EXTRA = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
             "GIT_ATTR_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"}
LIMITS = {"command_ms": 5000, "active_work_ms": 3000, "cleanup_ms": 2000, "log_bytes": 4194304,
          "document_bytes": 16777216, "host_bytes": 8388608, "inspection_bytes": 8388608, "static_ms": 60000,
          "publication_ms": 30000, "tree_entries": 65536, "tree_file_bytes": 536870912, "plist_bytes": 65536,
          "macho_commands": 4096, "macho_command_bytes": 4194304, "link_hops": 40}
PLAN_KEYS = {"schema", "contract", "profile", "executor", "environment", "platform", "os", "source", "observer",
             "python", "runtime", "dependencies", "git", "commands", "evidence", "failure_capture", "limits"}
COMMAND_KEYS = {"id", "kind", "argv", "cwd", "label", "environment", "timeout_ms", "active_work_ms", "cleanup_ms",
                "expected_direct_starts", "stdout_predicate", "stderr_predicate"}
NODE_VERSION = "v24.22.1"
NODE_ARCHIVE = "node-v24.22.1-darwin-arm64.tar.gz"
NODE_ARCHIVE_SHA256 = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
NODE_CHECKSUM_FILE = {"url": "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt",
                      "sha256": "fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4",
                      "size_bytes": 3171}
NODE_MEMBER = "node-v24.22.1-darwin-arm64/bin/node"
DEP_ARCHIVE_SHA256 = "b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9"
EXTERNAL_INPUTS = "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json"
EXTERNAL_SHA256 = "21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5"
ENTRY_POINT = "prototypes/static_tray_v01/current_host_observation_v02.py"
N34M_OBSERVER_SHA256 = "471a954703a1a7974638e500051a6ac538bf81dfb2a01a3944bf441e96622788"
N34M_GIT = {"path": "/Library/Developer/CommandLineTools/usr/bin/git",
            "sha256": "be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae", "size_bytes": 7604272}
FROZEN_PYTHON_INVENTORY = "c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633"
SYSTEM_VERSION = "/System/Library/CoreServices/SystemVersion.plist"
CRYPTEX_CONVENTIONAL = "/System/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist"
UNRESOLVED = re.compile(r"(?i)\b(todo|tbd|fixme|xxx)\b|[*?\[\]{}~`$]")
LABELS = {"git_version": "host-git-version", "node_version": "host-node-version"}
ADOPTION_001 = "docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json"

CHECKS = []


def check(cid, key, text, passed, **detail):
    CHECKS.append({"id": cid, "key": key, "check": text, "passed": bool(passed), "detail": detail})
    return bool(passed)


def mode_text(st):
    return "0o%03o" % stat.S_IMODE(st.st_mode)


def rehash(path):
    """SHA-256, size, mode, link count and identity of one regular file, never through a link."""
    named = os.lstat(path)
    if stat.S_ISLNK(named.st_mode):
        return {"error": "symlink"}
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            return {"error": "not a regular file"}
        digest, length = hashlib.sha256(), 0
        while True:
            block = os.read(fd, 1 << 20)
            if not block:
                break
            digest.update(block)
            length += len(block)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    ident = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    return {"sha256": digest.hexdigest(), "size_bytes": length, "mode": mode_text(before),
            "nlink": before.st_nlink, "dev": before.st_dev, "ino": before.st_ino,
            "stable": ident(before) == ident(after) == ident(os.lstat(path)) and length == before.st_size}


def read_bytes(path):
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


def strict_json(raw, *, floats=True):
    """Duplicate members and nonfinite constants refuse; floats refuse only where P07 forbids them (the plan)."""
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError("duplicate member " + k)
            out[k] = v
        return out

    def no_float(text):
        raise ValueError("float " + text)

    def no_const(text):
        raise ValueError("constant " + text)
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_float=None if floats else no_float,
                      parse_constant=no_const)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def canonical_ascii(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("ascii")


SYSTEM_LINKS = {"/tmp", "/var", "/etc"}


def canonical_state(path, allow_absent=False):
    """My own reading of contract section 7: normalized absolute, no linked component, realpath equal."""
    if not (type(path) is str and path.startswith("/") and not path.startswith("//") and "\0" not in path
            and (path == "/" or not path.endswith("/")) and posixpath.normpath(path) == path):
        return {"canonical": False, "reason": "not a normalized absolute path"}
    parts = [] if path == "/" else path.split("/")[1:]
    current = ""
    for index, name in enumerate(parts):
        current += "/" + name
        last = index == len(parts) - 1
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            if last and allow_absent:
                return {"canonical": os.path.realpath(path) == path, "reason": "last component absent",
                        "absent": True}
            return {"canonical": False, "reason": "missing component " + current}
        if stat.S_ISLNK(info.st_mode):
            return {"canonical": False, "reason": "linked component " + current,
                    "system_link": current in SYSTEM_LINKS}
        if not last and not stat.S_ISDIR(info.st_mode):
            return {"canonical": False, "reason": "ancestor is not a directory " + current}
    return {"canonical": os.path.realpath(path) == path, "reason": "all components lstat-checked", "absent": False}


def resolve_chain(path):
    """Component-by-component resolution with every link hop, as the kernel does it."""
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


def libsystem():
    return ctypes.CDLL(LIBSYSTEM, use_errno=True)


def sysctl_raw(name):
    lib = libsystem()
    f = lib.sysctlbyname
    f.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
    f.restype = ctypes.c_int
    size = ctypes.c_size_t(0)
    if f(name.encode("ascii"), None, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), "sysctlbyname size " + name)
    buf = ctypes.create_string_buffer(size.value)
    if f(name.encode("ascii"), buf, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), "sysctlbyname read " + name)
    return buf.raw[:size.value]


def cstring(raw):
    return raw.split(b"\0", 1)[0].decode("ascii", "replace")


def xattr_names(path):
    lib = libsystem()
    lib.listxattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
    lib.listxattr.restype = ctypes.c_ssize_t
    lib.getxattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32,
                             ctypes.c_int]
    lib.getxattr.restype = ctypes.c_ssize_t
    raw = os.fsencode(path)
    n = lib.listxattr(raw, None, 0, 1)  # XATTR_NOFOLLOW
    if n < 0:
        return {"error": ctypes.get_errno()}
    names = []
    if n:
        buf = ctypes.create_string_buffer(n)
        n = lib.listxattr(raw, buf, n, 1)
        names = [x.decode("utf-8", "replace") for x in buf.raw[:n].split(b"\0") if x]
    out = {"names": names}
    if "com.apple.quarantine" in names:
        size = lib.getxattr(raw, b"com.apple.quarantine", None, 0, 0, 1)
        value = ctypes.create_string_buffer(max(size, 1))
        size = lib.getxattr(raw, b"com.apple.quarantine", value, size, 0, 1)
        out["quarantine_flags"] = value.raw[:max(size, 0)].split(b";")[0].decode("ascii", "replace")
    return out


def fs_info(path):
    lib = libsystem()
    lib.statfs.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
    lib.statfs.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(4096)
    if lib.statfs(os.fsencode(path), buf) != 0:
        return {"error": ctypes.get_errno()}
    raw = buf.raw
    return {"f_type": struct.unpack_from("<I", raw, 60)[0], "f_flags": "0x%08x" % struct.unpack_from("<I", raw, 64)[0],
            "f_fstypename": cstring(raw[72:88]), "f_mntonname": cstring(raw[88:1112])}


def walk_tree(root):
    """Exact entry map, links never followed: {rel: {kind, sha256, size_bytes, mode, nlink} | {kind, target}}."""
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
                h = rehash(path)
                entries[rel] = {"kind": "file", "sha256": h["sha256"], "size_bytes": h["size_bytes"],
                                "mode": h["mode"], "nlink": h["nlink"]}
            else:
                entries[rel] = {"kind": "special"}
    return entries


def binding_of(row):
    return {"sha256": row["sha256"], "size_bytes": row["size_bytes"], "mode": row["mode"]}


def shape_ok(value, descriptor):
    keys = {"sha256", "size_bytes", "mode"} | ({"path"} if descriptor else set())
    return (type(value) is dict and set(value) == keys and type(value["sha256"]) is str
            and re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is not None
            and re.fullmatch(r"(.)\1{63}", value["sha256"]) is None
            and type(value["size_bytes"]) is int and value["size_bytes"] >= 0
            and type(value["mode"]) is str and re.fullmatch(r"0o[0-7]{3,4}", value["mode"]) is not None)


def check_descriptor(cid, key, desc, *, private=False, expect_sha256=None):
    ok_shape = check(cid + "-shape", key, "descriptor shape {path, sha256, size_bytes, mode}", shape_ok(desc, True))
    if not ok_shape:
        return None
    canon = canonical_state(desc["path"])
    check(cid + "-canonical", key, "path is canonical (no linked component, realpath equal)", canon["canonical"],
          path=desc["path"], reason=canon["reason"])
    actual = rehash(desc["path"])
    check(cid + "-rehash", key, "path, SHA-256, size and mode equal the file's", "error" not in actual
          and binding_of(actual) == binding_of(desc) and actual["stable"],
          planned=binding_of(desc), actual={k: actual.get(k) for k in ("sha256", "size_bytes", "mode", "nlink")})
    if private:
        check(cid + "-private", key, "one link (private regular file)", actual.get("nlink") == 1,
              nlink=actual.get("nlink"))
    if expect_sha256 is not None:
        check(cid + "-expected", key, "SHA-256 equals the independently known value",
              desc["sha256"] == expect_sha256, expected=expect_sha256)
    return actual


def inside(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def p07_walk(value, where, problems):
    if value is None:
        problems.append({"path": where, "problem": "null"})
    elif type(value) is float:
        problems.append({"path": where, "problem": "float"})
    elif type(value) is dict:
        for k, v in value.items():
            if UNRESOLVED.search(k):
                problems.append({"path": where + "." + k, "problem": "key text (keys are not checked by the observer)"})
            p07_walk(v, where + "." + k, problems)
    elif type(value) is list:
        for i, v in enumerate(value):
            p07_walk(v, where + "[" + str(i) + "]", problems)
    elif type(value) is str:
        if UNRESOLVED.search(value):
            problems.append({"path": where, "problem": "unresolved or wildcard text", "value": value})
        if re.fullmatch(r"[0-9a-f]{40,64}", value) and re.fullmatch(r"(.)\1+", value):
            problems.append({"path": where, "problem": "one repeated digit"})


def collect_paths(value, where, out):
    if type(value) is dict:
        for k, v in value.items():
            collect_paths(v, where + "." + k, out)
    elif type(value) is list:
        for i, v in enumerate(value):
            collect_paths(v, where + "[" + str(i) + "]", out)
    elif type(value) is str and value.startswith("/"):
        out.append((where, value))


def install_rule(cid, key, install, *, purpose, source_root, destination, archive, files, directories, root_mode,
                 executable, node_source_content):
    """The receipt rule of W3-OBSERVER section 3 (decisions D-05 and D-11), written independently."""
    plan_raw = read_bytes(install["plan"]["path"])
    result_raw = read_bytes(install["result"]["path"])
    plan = strict_json(plan_raw)
    result = strict_json(result_raw)
    plan_keys = {"schema", "contract", "purpose", "source_root", "archive", "destination", "root_mode", "files",
                 "directories", "members", "node_source", "report"}
    check(cid + "-plan-keys", key, "install plan: the 12 closed keys of install/0.2.0", set(plan) == plan_keys,
          keys=sorted(plan))
    members = plan.get("members")
    check(cid + "-plan-values", key, "install plan: schema, contract, purpose, source root, destination, root mode, "
          "files, directories, archive and report equal the observation plan's", all((
              plan.get("schema") == "ontokin.current-host-readback-install/0.2.0", plan.get("contract") == CONTRACT,
              plan.get("purpose") == purpose, plan.get("source_root") == source_root,
              plan.get("destination") == destination, plan.get("root_mode") == root_mode,
              plan.get("files") == files, plan.get("directories") == directories, plan.get("archive") == archive,
              plan.get("report") == install["result"]["path"])),
          schema=plan.get("schema"), purpose=plan.get("purpose"), source_root=plan.get("source_root"),
          destination=plan.get("destination"), root_mode=plan.get("root_mode"), report=plan.get("report"),
          files_equal=plan.get("files") == files, directories_equal=plan.get("directories") == directories,
          archive_equal=plan.get("archive") == archive)
    check(cid + "-plan-members", key, "install plan: members is a non-empty map with integer sizes",
          type(members) is dict and members and all(type(r) is dict and type(r.get("size_bytes")) is int
                                                    for r in members.values()), members=len(members or {}))
    state = result.get("state")
    base = {"schema", "contract", "design_revision", "amendments", "purpose", "passed", "state", "apply_requested",
            "execution_counts", "operations", "pins", "labels", "preparer_source"}
    keys = base | {"archive", "before"} | ({"after", "publication"} if state == "INSTALLED_EXACT" else set())
    check(cid + "-result-state", key, "result: INSTALLED_EXACT or ALREADY_PRESENT_EXACT with passed true",
          state in ("INSTALLED_EXACT", "ALREADY_PRESENT_EXACT") and result.get("passed") is True, state=state)
    check(cid + "-result-keys", key, "result: the closed keys of its outcome", set(result) == keys,
          keys=sorted(result))
    check(cid + "-result-values", key, "result: contract, design revision 4, amendment 001, purpose, zero starts, "
          "operation rows and the adopted pins", all((
              result.get("schema") == "ontokin.current-host-readback-install-result/0.2.0",
              result.get("contract") == CONTRACT, result.get("design_revision") == 4,
              result.get("amendments") == ["P33-AMENDMENT-001"], result.get("purpose") == purpose,
              type(result.get("apply_requested")) is bool,
              result.get("execution_counts") == {"node": 0, "ldd": 0, "checkers": 0},
              type(result.get("operations")) is list and all(
                  type(r) is dict and r.get("operation") in ("created_owned_stage", "removed_owned_stage")
                  for r in result["operations"]),
              result.get("pins") == {"origin": "adopted-contract", "node_archive_sha256": NODE_ARCHIVE_SHA256,
                                     "dependency_archive_sha256": DEP_ARCHIVE_SHA256})))
    expected_pins = ({"origin": "adopted-contract", "node_archive_sha256": NODE_ARCHIVE_SHA256,
                      "node_executable": executable} if purpose == "selected-node" else
                     {"origin": "adopted-contract", "dependency_archive_sha256": DEP_ARCHIVE_SHA256})
    labels = result.get("labels") or {}
    os_label = labels.get("os")

    def fields(row):
        return (type(row) is dict and type(row.get("product_version")) is str and row["product_version"]
                and type(row.get("product_build_version")) is str and row["product_build_version"]
                and (row.get("product_version_extra") is None or type(row["product_version_extra"]) is str))
    os_ok = (type(os_label) is dict and set(os_label) == {"product_version", "product_build_version",
                                                           "product_version_extra", "cryptex"} and fields(os_label)
             and (os_label["cryptex"] == {"state": "absent"} or (
                 type(os_label["cryptex"]) is dict and os_label["cryptex"].get("state") == "present"
                 and set(os_label["cryptex"]) == {"state", "product_version", "product_build_version",
                                                  "product_version_extra"} and fields(os_label["cryptex"]))))
    check(cid + "-result-labels", key, "result labels: {executor, contract, profile, design_revision, amendments, "
          "pins, os} with the pins of its purpose and HOST's OS-label shape", all((
              set(labels) == {"executor", "contract", "profile", "design_revision", "amendments", "pins", "os"},
              labels.get("executor") == EXECUTOR, labels.get("contract") == CONTRACT,
              labels.get("profile") == PROFILE, labels.get("design_revision") == 4,
              labels.get("amendments") == ["P33-AMENDMENT-001"], labels.get("pins") == expected_pins, os_ok)),
          os_label=os_label)
    source = result.get("preparer_source")
    check(cid + "-result-source", key, "result preparer_source names this source root",
          type(source) is dict and set(source) == {"root", "files_at_start"} and source.get("root") == source_root
          and type(source.get("files_at_start")) is dict, root=(source or {}).get("root"))

    def readback(value, st):
        return type(value) is dict and value.get("state") == st and set(value) == (
            {"state"} if st == "absent" else {"state", "files", "directories"})
    if state == "INSTALLED_EXACT":
        check(cid + "-result-readbacks", key, "INSTALLED_EXACT: applied to an absent destination, read back exact, "
              "published by renamex_np RENAME_EXCL", result.get("apply_requested") is True
              and readback(result.get("before"), "absent") and readback(result.get("after"), "complete_exact")
              and result.get("publication") == {"call": "renamex_np", "library": LIBSYSTEM, "flag": "RENAME_EXCL",
                                                "flag_value": 4})
    else:
        check(cid + "-result-readbacks", key, "ALREADY_PRESENT_EXACT: before read back exact",
              readback(result.get("before"), "complete_exact"))
    summary = result.get("archive") or {}
    members_sha256 = hashlib.sha256(canonical_ascii(members)).hexdigest() if type(members) is dict else None
    summary_keys = {"sha256", "size_bytes", "members", "expanded_bytes", "symlinks", "member_inventory_sha256",
                    "extracted_members"} | ({"executable"} if purpose == "selected-node" else set())
    check(cid + "-archive-summary", key, "archive summary: keys, digest, size, member count, expanded bytes and "
          "member digest equal the plan's", set(summary) == summary_keys
          and summary.get("sha256") == archive["sha256"] and summary.get("size_bytes") == archive["size_bytes"]
          and summary.get("members") == len(members) and summary.get("expanded_bytes") == sum(
              r["size_bytes"] for r in members.values()) and summary.get("member_inventory_sha256") == members_sha256,
          members=len(members), expanded_bytes=sum(r["size_bytes"] for r in members.values()),
          member_inventory_sha256=members_sha256)
    if purpose == "selected-node":
        extracted = summary.get("executable") or {}
        check(cid + "-archive-executable", key, "archive summary's executable: the Node member, bin/node and Node's "
              "binding, with the four Mach-O keys", set(extracted) == {"member", "path", "sha256", "size_bytes",
                                                                       "mode", "macho"}
              and extracted.get("member") == NODE_MEMBER and extracted.get("path") == "bin/node"
              and binding_of(extracted) == executable and type(extracted.get("macho")) is dict
              and set(extracted["macho"]) == {"magic", "cputype", "cpusubtype", "filetype"})
        check(cid + "-node-source", key, "the plan's node_source is the signature check of NODE-SOURCE.json, whose "
              "member digest and archive size agree", plan.get("node_source") == {
                  "signature_check": node_source_content["signature_check"]}
              and members_sha256 == node_source_content["member_inventory_sha256"]
              and node_source_content["archive"]["size_bytes"] == archive["size_bytes"])
    else:
        check(cid + "-node-source", key, "a reader-tree plan carries no node_source", plan.get("node_source") is None)
    archive_actual = rehash(archive["path"])
    check(cid + "-archive-bytes", key, "the retained archive's bytes equal its descriptor",
          binding_of(archive_actual) == binding_of(archive), actual=binding_of(archive_actual))
    return {"plan_members": len(members), "members_sha256": members_sha256, "state": state,
            "operations": result.get("operations"), "files_at_start": sorted((source or {}).get("files_at_start") or {})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--local", required=True)
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    t0 = time.time()
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    wt, local, w2 = a.worktree, a.local, a.plan_dir
    plan_path = w2 + "/observation-plan-001.json"
    facts = {}

    # --- The plan's bytes: digest, canonical form, P07 section 2 ---------------------------------
    raw = read_bytes(plan_path)
    plan_sha256 = hashlib.sha256(raw).hexdigest()
    facts["plan_sha256"] = plan_sha256
    facts["plan_binding"] = {k: v for k, v in rehash(plan_path).items() if k in ("sha256", "size_bytes", "mode",
                                                                                   "nlink")}
    plan = strict_json(raw, floats=False)
    check("P-01", "plan", "the plan parses with no duplicate member, float or nonfinite constant", True)
    check("P-02", "plan", "canonical JSON: sorted keys, compact separators, ASCII, no trailing newline",
          canonical(plan) == raw)
    check("P-03", "plan", "plan path is canonical", canonical_state(plan_path)["canonical"])
    problems = []
    p07_walk(plan, "plan", problems)
    check("P-04", "plan", "P07 section 2: no null, float, TODO/TBD/FIXME/XXX, * ? [ ] { } ~ $ or backtick, and no "
          "digest of one repeated digit", not problems, problems=problems)
    check("P-05", "plan", "closed top-level keys", set(plan) == PLAN_KEYS, keys=sorted(plan))
    paths = []
    collect_paths(plan, "plan", paths)
    attempt = plan["evidence"]["attempt"]
    noncanonical = []
    for where, value in paths:
        if ".environment." in where:  # PATH and GIT_CONFIG_GLOBAL are values, not bound paths
            continue
        absent_ok = inside(value, attempt)
        if absent_ok and value != attempt:
            state = canonical_state(attempt, allow_absent=True)
            ok = state["canonical"] and posixpath.normpath(value) == value
        else:
            state = canonical_state(value, allow_absent=absent_ok)
            ok = state["canonical"]
        if not ok:
            noncanonical.append({"where": where, "value": value, "reason": state["reason"]})
    check("P-06", "plan", "every path in the plan equals its canonical form (paths under the absent attempt: the "
          "attempt is canonical with an absent last component)", not noncanonical, checked=len(paths),
          noncanonical=noncanonical)

    # --- schema, contract, profile, executor, environment, limits ---------------------------------
    check("K-01", "schema", "schema", plan["schema"] == PLAN_SCHEMA, value=plan["schema"])
    check("K-02", "contract", "contract", plan["contract"] == CONTRACT, value=plan["contract"])
    check("K-03", "profile", "profile", plan["profile"] == PROFILE, value=plan["profile"])
    check("K-04", "executor", "executor", plan["executor"] == EXECUTOR, value=plan["executor"])
    check("K-05", "environment", "exactly the five declared variables, string values", plan["environment"] == ENV
          and all(type(v) is str for v in plan["environment"].values()), value=plan["environment"])
    check("K-06", "limits", "exactly the fixed LIMITS", plan["limits"] == LIMITS, value=plan["limits"])

    # --- platform -----------------------------------------------------------------------------------
    uname = os.uname()
    boot = cstring(sysctl_raw("kern.bootsessionuuid"))
    translated_raw = sysctl_raw("sysctl.proc_translated")
    translated = struct.unpack("=i", translated_raw)[0] if len(translated_raw) == 4 else None
    osrelease = cstring(sysctl_raw("kern.osrelease"))
    osversion = cstring(sysctl_raw("kern.osversion"))
    boottime = struct.unpack("=qq", sysctl_raw("kern.boottime")[:16])
    facts["platform_observed"] = {"sysname": uname.sysname, "release": uname.release, "machine": uname.machine,
                                  "kern.osrelease": osrelease, "kern.osversion": osversion,
                                  "kern.bootsessionuuid": boot, "sysctl.proc_translated": translated,
                                  "kern.boottime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(boottime[0]))}
    platform = plan["platform"]
    check("K-07", "platform", "closed keys {system, release, machine, proc_translated, boot_session_uuid}",
          set(platform) == {"system", "release", "machine", "proc_translated", "boot_session_uuid"})
    check("K-08", "platform", "system Darwin, machine arm64 (os.uname)", platform["system"] == uname.sysname == "Darwin"
          and platform["machine"] == uname.machine == "arm64")
    check("K-09", "platform", "release equals os.uname().release and kern.osrelease",
          platform["release"] == uname.release == osrelease, planned=platform["release"], observed=uname.release)
    check("K-10", "platform", "proc_translated 0 (sysctl.proc_translated through sysctlbyname)",
          platform["proc_translated"] == translated == 0 and type(platform["proc_translated"]) is int)
    check("K-11", "platform", "boot_session_uuid equals this boot's kern.bootsessionuuid",
          platform["boot_session_uuid"] == boot, planned=platform["boot_session_uuid"], observed=boot)

    # --- os -------------------------------------------------------------------------------------------
    os_plan = plan["os"]
    check("K-12", "os", "closed keys {system_version, cryptex}", set(os_plan) == {"system_version", "cryptex"})
    sv = os_plan["system_version"]
    check("K-13", "os.system_version", "path is /System/Library/CoreServices/SystemVersion.plist",
          sv.get("path") == SYSTEM_VERSION)
    sv_actual = check_descriptor("K-14", "os.system_version", sv)
    sv_plist = plistlib.loads(read_bytes(SYSTEM_VERSION))
    chain = resolve_chain(CRYPTEX_CONVENTIONAL)
    cryptex = os_plan["cryptex"]
    check("K-15", "os.cryptex", "present, closed keys {state, path, sha256, size_bytes, mode}",
          cryptex.get("state") == "present" and set(cryptex) == {"state", "path", "sha256", "size_bytes", "mode"})
    check("K-16", "os.cryptex", "the conventional path resolves, through its recorded hop, to the plan's canonical "
          "path, a regular file", chain["state"] == "file" and chain["path"] == cryptex.get("path"), chain=chain)
    cx_actual = check_descriptor("K-17", "os.cryptex", {k: cryptex[k] for k in ("path", "sha256", "size_bytes",
                                                                                 "mode")})
    cx_plist = plistlib.loads(read_bytes(cryptex["path"]))
    facts["os_identity"] = {
        "system": {k: sv_plist.get(k) for k in ("ProductName", "ProductVersion", "ProductBuildVersion",
                                                 "ProductVersionExtra")},
        "cryptex": {k: cx_plist.get(k) for k in ("ProductName", "ProductVersion", "ProductBuildVersion",
                                                  "ProductVersionExtra")},
        "cryptex_chain": chain, "system_binding": binding_of(sv_actual), "cryptex_binding": binding_of(cx_actual)}
    check("K-18", "os", "both plists name macOS 26.6.2, build 25G83 = kern.osversion, no ProductVersionExtra",
          sv_plist.get("ProductVersion") == cx_plist.get("ProductVersion") == "26.6.2"
          and sv_plist.get("ProductBuildVersion") == cx_plist.get("ProductBuildVersion") == osversion
          and "ProductVersionExtra" not in sv_plist and "ProductVersionExtra" not in cx_plist)

    # --- source and observer ----------------------------------------------------------------------
    source = plan["source"]
    check("K-19", "source", "closed keys {root, commit, tree, inventory}",
          set(source) == {"root", "commit", "tree", "inventory"})
    check("K-20", "source.root", "root is the worktree, canonical", source["root"] == wt
          and canonical_state(wt)["canonical"])
    check("K-21", "source.commit", "commit is C", source["commit"] == a.commit, value=source["commit"])
    check("K-22", "source.tree", "tree is the Director's tree", source["tree"] == a.tree, value=source["tree"])
    check_descriptor("K-23", "source.inventory", source["inventory"])
    check("K-24", "source.inventory", "the source inventory is W2's file in its plan directory",
          source["inventory"]["path"] == w2 + "/source-inventory-001.json")
    obs = plan["observer"]
    check("K-25", "observer", "the entry point under the source root", obs.get("path") == wt + "/" + ENTRY_POINT)
    check_descriptor("K-26", "observer", obs, expect_sha256=N34M_OBSERVER_SHA256)

    # --- python -------------------------------------------------------------------------------------
    py = plan["python"]
    check("K-27", "python", "closed keys {venv, framework, version, inventory}",
          set(py) == {"venv", "framework", "version", "inventory"})
    check("K-28", "python.venv", "the source checkout's own .venv, canonical", py["venv"] == wt + "/.venv"
          and canonical_state(py["venv"])["canonical"])
    fw = py["framework"]
    check("K-29", "python.framework", "canonical .../Python.framework/Versions/3.12 (no linked component)",
          canonical_state(fw)["canonical"] and posixpath.basename(fw) == "3.12"
          and posixpath.basename(posixpath.dirname(fw)) == "Versions"
          and posixpath.basename(posixpath.dirname(posixpath.dirname(fw))) == "Python.framework",
          reason=canonical_state(fw)["reason"])
    cfg = {}
    for line in read_bytes(py["venv"] + "/pyvenv.cfg").decode("utf-8").splitlines():
        if line.strip():
            k, v = (s.strip() for s in line.split("=", 1))
            cfg[k] = v
    facts["pyvenv_cfg_keys"] = sorted(cfg)
    running = "%d.%d.%d" % sys.version_info[:3]
    check("K-30", "python.version", "3.12.13 = pyvenv.cfg's version = this interpreter's version (the same launcher)",
          py["version"] == cfg.get("version") == running == "3.12.13", planned=py["version"],
          cfg=cfg.get("version"), running=running)
    check("K-31", "python.version", "this script's interpreter is the planned launcher and framework",
          sys.executable == py["venv"] + "/bin/python" and os.path.realpath(sys.executable) == fw + "/bin/python3.12",
          executable=sys.executable)
    check_descriptor("K-32", "python.inventory", py["inventory"], expect_sha256=FROZEN_PYTHON_INVENTORY)
    check("K-33", "python.inventory", "the inventory is W2's file in its plan directory, canonical bytes",
          py["inventory"]["path"] == w2 + "/python-inventory-001.json"
          and canonical(strict_json(read_bytes(py["inventory"]["path"]))) == read_bytes(py["inventory"]["path"]))

    # --- runtime --------------------------------------------------------------------------------------
    rt = plan["runtime"]
    check("K-34", "runtime", "closed keys", set(rt) == {"directory", "version", "root_mode", "bin_mode", "executable",
                                                        "node_source", "archive", "install"})
    directory = rt["directory"]
    check("K-35", "runtime.directory", "canonical; MP's prepared tree", canonical_state(directory)["canonical"]
          and directory == local + "/c271-macos/node-v24.22.1-darwin-arm64")
    check("K-36", "runtime.version", "v24.22.1 (MC33)", rt["version"] == NODE_VERSION)
    tree = walk_tree(directory)
    check("K-37", "runtime", "exact layout {bin/, bin/node, NODE-SOURCE.json}, no link, no .DS_Store, one link each",
          {k: v["kind"] for k, v in tree.items()} == {"bin": "directory", "bin/node": "file",
                                                     "NODE-SOURCE.json": "file"}
          and all(v.get("nlink") == 1 for v in tree.values() if v["kind"] == "file"), entries=sorted(tree))
    root_mode = mode_text(os.lstat(directory))
    check("K-38", "runtime.root_mode", "root mode from lstat", rt["root_mode"] == root_mode == "0o755",
          observed=root_mode)
    check("K-39", "runtime.bin_mode", "bin mode from lstat", rt["bin_mode"] == tree["bin"]["mode"] == "0o755",
          observed=tree["bin"]["mode"])
    check("K-40", "runtime.executable", "bin/node's SHA-256, size and mode (binding shape)",
          shape_ok(rt["executable"], False) and binding_of(tree["bin/node"]) == rt["executable"],
          actual=binding_of(tree["bin/node"]))
    check("K-41", "runtime.executable", "equals MP's OUTCOME.json and N34-M (6f320694..., 122,545,856, 0o755)",
          rt["executable"] == {"sha256": "6f32069480ec14d52b6d7b1f3c7124cfbbc46203abf5ddf5c65b127435f3f329",
                               "size_bytes": 122545856, "mode": "0o755"})
    check("K-42", "runtime.node_source", "NODE-SOURCE.json's SHA-256, size and mode", shape_ok(rt["node_source"], False)
          and binding_of(tree["NODE-SOURCE.json"]) == rt["node_source"], actual=binding_of(tree["NODE-SOURCE.json"]))
    ns_raw = read_bytes(directory + "/NODE-SOURCE.json")
    ns = strict_json(ns_raw)
    check("K-43", "runtime.node_source", "NODE-SOURCE.json: canonical ASCII JSON with its seven keys, the pinned "
          "archive, checksum-file identity, a signature record and the extracted binding", all((
              canonical_ascii(ns) == ns_raw,
              set(ns) == {"schema", "contract", "archive", "checksum_file", "signature_check",
                          "member_inventory_sha256", "extracted"},
              ns.get("schema") == "ontokin.current-host-readback-node-source/0.2.0", ns.get("contract") == CONTRACT,
              ns.get("archive") == {"name": NODE_ARCHIVE, "sha256": NODE_ARCHIVE_SHA256,
                                    "size_bytes": rt["archive"]["size_bytes"]},
              ns.get("checksum_file") == NODE_CHECKSUM_FILE,
              set(ns.get("signature_check", {})) == {"status", "detail"}
              and ns["signature_check"]["status"] in ("not_performed", "verified", "failed")
              and ns["signature_check"]["detail"],
              ns.get("extracted") == {"member": NODE_MEMBER, "path": "bin/node", **rt["executable"]})),
          signature_status=ns.get("signature_check", {}).get("status"))
    arch = rt["archive"]
    check_descriptor("K-44", "runtime.archive", arch, expect_sha256=NODE_ARCHIVE_SHA256)
    check("K-45", "runtime.archive", "retained at MP's path with mode 0o444", arch["path"] == local
          + "/c271-p34/downloads/node/" + NODE_ARCHIVE and arch["mode"] == "0o444")
    check("K-46", "runtime.install", "closed keys {plan, result}", set(rt["install"]) == {"plan", "result"})
    check_descriptor("K-47", "runtime.install.plan", rt["install"]["plan"])
    check_descriptor("K-48", "runtime.install.result", rt["install"]["result"])
    check("K-49", "runtime.install", "MP's exact apply plan and receipt (not the portable or dry-run files)",
          rt["install"]["plan"]["path"] == local + "/c271-p34/plans/node-install-plan.json"
          and rt["install"]["result"]["path"] == local + "/c271-p34/receipts/node-install-result.json")
    facts["runtime_receipt"] = install_rule(
        "K-50", "runtime.install", rt["install"], purpose="selected-node", source_root=wt, destination=directory,
        archive=arch, files={"bin/node": rt["executable"], "NODE-SOURCE.json": rt["node_source"]},
        directories={"bin": rt["bin_mode"]}, root_mode=rt["root_mode"], executable=rt["executable"],
        node_source_content=ns)

    # --- dependencies ---------------------------------------------------------------------------------
    deps = plan["dependencies"]
    check("K-51", "dependencies", "closed keys {root, inventory, install}", set(deps) == {"root", "inventory",
                                                                                          "install"})
    droot = deps["root"]
    check("K-52", "dependencies.root", "canonical; MP's reader tree", canonical_state(droot)["canonical"]
          and droot == local + "/c271-macos/reader-c195")
    check_descriptor("K-53", "dependencies.inventory", deps["inventory"])
    inv_raw = read_bytes(deps["inventory"]["path"])
    inv = strict_json(inv_raw)
    check("K-54", "dependencies.inventory", "canonical dependencies/0.2.0 {schema, files, directories, archive}",
          canonical(inv) == inv_raw and set(inv) == {"schema", "files", "directories", "archive"}
          and inv["schema"] == "ontokin.current-host-readback-dependencies/0.2.0")
    ext_raw = read_bytes(wt + "/" + EXTERNAL_INPUTS)
    check("K-55", "dependencies.inventory", "EXTERNAL-INPUTS.json is the pinned C199 manifest",
          hashlib.sha256(ext_raw).hexdigest() == EXTERNAL_SHA256)
    ext = strict_json(ext_raw)
    prefix = ext["dependencies_root"] + "/"
    historical = {n[len(prefix):]: r for n, r in ext["files"].items() if n.startswith(prefix)}
    check("K-56", "dependencies.inventory", "the 24 names and their SHA-256 and sizes equal the C199 pins",
          len(historical) == 24 and set(inv["files"]) == set(historical) and all(
              {"sha256": inv["files"][n]["sha256"], "size_bytes": inv["files"][n]["size_bytes"]} == r
              for n, r in historical.items()) and all(shape_ok(r, False) for r in inv["files"].values()),
          files=len(inv["files"]))
    dtree = walk_tree(droot)
    dfiles = {k: binding_of(v) for k, v in dtree.items() if v["kind"] == "file"}
    ddirs = {k: v["mode"] for k, v in dtree.items() if v["kind"] == "directory"}
    check("K-57", "dependencies.inventory", "files and directory modes equal the installed reader tree; no link, "
          "no special file, no .DS_Store; every file has one link",
          dfiles == inv["files"] and ddirs == inv["directories"]
          and not any(v["kind"] in ("symlink", "special") for v in dtree.values())
          and not any(k.split("/")[-1] == ".DS_Store" for k in dtree)
          and all(v.get("nlink") == 1 for v in dtree.values() if v["kind"] == "file"),
          files=len(dfiles), directories=len(ddirs))
    necessary = {posixpath.dirname(n) for n in inv["files"]}
    necessary = {"/".join(n.split("/")[:i]) for n in necessary for i in range(1, len(n.split("/")) + 1)} - {""}
    check("K-58", "dependencies.inventory", "directories are exactly the necessary set", set(inv["directories"])
          == necessary, directories=sorted(inv["directories"]))
    darch = inv["archive"]
    check_descriptor("K-59", "dependencies.inventory.archive", darch, expect_sha256=DEP_ARCHIVE_SHA256)
    check("K-60", "dependencies.inventory.archive", "the committed C195 archive in the worktree",
          darch["path"] == wt + "/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz")
    versions = {}
    for name, expected in (("validator/package/package.json", "2.0.0-dev.3.10"),
                           ("indexer-view/three/package.json", "0.186.1")):
        versions[name] = strict_json(read_bytes(droot + "/" + name)).get("version")
    check("K-61", "dependencies", "validator 2.0.0-dev.3.10 and Three.js 0.186.1",
          versions == {"validator/package/package.json": "2.0.0-dev.3.10",
                       "indexer-view/three/package.json": "0.186.1"}, versions=versions)
    check("K-62", "dependencies.install", "closed keys {plan, result}", set(deps["install"]) == {"plan", "result"})
    check_descriptor("K-63", "dependencies.install.plan", deps["install"]["plan"])
    check_descriptor("K-64", "dependencies.install.result", deps["install"]["result"])
    check("K-65", "dependencies.install", "MP's exact reader apply plan and receipt",
          deps["install"]["plan"]["path"] == local + "/c271-p34/plans/reader-install-plan.json"
          and deps["install"]["result"]["path"] == local + "/c271-p34/receipts/reader-install-result.json")
    facts["reader_receipt"] = install_rule(
        "K-66", "dependencies.install", deps["install"], purpose="retained-dependencies", source_root=wt,
        destination=droot, archive=darch, files=inv["files"], directories=inv["directories"],
        root_mode=mode_text(os.lstat(droot)), executable=None, node_source_content=None)

    # --- git ----------------------------------------------------------------------------------------------
    git = plan["git"]
    check("K-67", "git", "descriptor is N34-M's file: path, SHA-256 and size", shape_ok(git, True)
          and {k: git[k] for k in ("path", "sha256", "size_bytes")} == N34M_GIT)
    check("K-68", "git", "not the /usr/bin/git dispatcher and not a link", git["path"] != "/usr/bin/git"
          and not stat.S_ISLNK(os.lstat(git["path"]).st_mode))
    git_actual = check_descriptor("K-69", "git", git)
    disp = os.stat("/usr/bin/git")
    disp_hash = rehash("/usr/bin/git")
    check("K-70", "git", "neither a hard link of the dispatcher nor the dispatcher's bytes",
          (disp.st_dev, disp.st_ino) != (git_actual["dev"], git_actual["ino"])
          and disp_hash["sha256"] != git_actual["sha256"], dispatcher=binding_of(disp_hash))

    # --- commands -----------------------------------------------------------------------------------------
    common = {"timeout_ms": 5000, "active_work_ms": 3000, "cleanup_ms": 2000, "expected_direct_starts": 1,
              "stderr_predicate": ""}
    mine = [{"id": "git_version", "kind": "other", "argv": [git["path"], "--version"], "cwd": attempt + "/git_version",
             "label": "host-git-version", "environment": {**ENV, **GIT_EXTRA},
             "stdout_predicate": "git-version-line-v1", **common},
            {"id": "node_version", "kind": "node", "argv": [directory + "/bin/node", "--version"],
             "cwd": attempt + "/node_version", "label": "host-node-version", "environment": dict(ENV),
             "stdout_predicate": "v24.22.1\n", **common}]
    check("K-71", "commands", "exactly two records with the closed keys", type(plan["commands"]) is list
          and len(plan["commands"]) == 2 and all(set(c) == COMMAND_KEYS for c in plan["commands"]))
    check("K-72", "commands", "equal, in order, the two commands of W3-OBSERVER section 2 built here",
          plan["commands"] == mine)

    # --- evidence -------------------------------------------------------------------------------------------
    ev = plan["evidence"]
    parent = ev["parent"]
    check("K-73", "evidence", "closed keys {parent, ancestors, attempt, outputs}",
          set(ev) == {"parent", "ancestors", "attempt", "outputs"})
    check("K-74", "evidence.parent", "canonical existing directory, empty", canonical_state(parent)["canonical"]
          and stat.S_ISDIR(os.lstat(parent).st_mode) and os.listdir(parent) == [],
          children=os.listdir(parent))
    rows, current = [], parent
    while True:
        info = os.lstat(current)
        rows.append({"path": current, "device": info.st_dev, "inode": info.st_ino, "mode": mode_text(info),
                     "is_dir": stat.S_ISDIR(info.st_mode), "is_link": stat.S_ISLNK(info.st_mode)})
        if current == "/":
            break
        current = posixpath.dirname(current)
    rows.sort(key=lambda r: r["path"])
    facts["ancestors_observed"] = rows
    check("K-75", "evidence.ancestors", "{path, device, inode, mode} of the parent and every ancestor, sorted by "
          "path, from my own lstat; none a link", [{k: r[k] for k in ("path", "device", "inode", "mode")}
                                                   for r in rows] == ev["ancestors"]
          and all(r["is_dir"] and not r["is_link"] for r in rows))
    check("K-76", "evidence.attempt", "an absent direct child of the parent, observe-001",
          posixpath.dirname(attempt) == parent and attempt == parent + "/observe-001"
          and not os.path.lexists(attempt))
    outputs = {k: attempt + "/" + k + ".json" for k in ("reserved", "preflight", "result", "completion", "failure")}
    outputs["host"] = attempt + "/HOST.json"
    for cid in ("git_version", "node_version"):
        stage_dir, label = attempt + "/" + cid, LABELS[cid]
        outputs[cid] = {"stage": stage_dir, "intent": stage_dir + "/intent.json", "started": stage_dir + "/started.json",
                        "inspection": stage_dir + "/inspection.json", "postflight": stage_dir + "/postflight.json",
                        "failure": stage_dir + "/failure.json", "stdout": stage_dir + "/" + label + ".stdout.log",
                        "stderr": stage_dir + "/" + label + ".stderr.log",
                        "process": stage_dir + "/" + label + ".process.json"}
    check("K-77", "evidence.outputs", "equal the fixed topology of W3-OBSERVER section 2 built here",
          ev["outputs"] == outputs)
    protected = [wt, py["venv"], fw, directory, droot, posixpath.dirname(git["path"])]
    check("K-78", "evidence", "the parent lies outside every bound root, and no bound root inside it",
          all(not inside(parent, p) and not inside(p, parent) for p in protected), protected=protected)
    check("K-79", "runtime/dependencies/framework", "the bound roots overlap neither the source root nor each other",
          all(not inside(x, wt) and not inside(wt, x) for x in (directory, droot, fw))
          and all(not inside(x, y) and not inside(y, x) for x, y in ((directory, droot), (directory, fw),
                                                                     (droot, fw))))

    # --- failure capture --------------------------------------------------------------------------------
    fc = plan["failure_capture"]
    check("K-80", "failure_capture", "closed keys {procedure}", set(fc) == {"procedure"})
    fc_actual = check_descriptor("K-81", "failure_capture.procedure", fc["procedure"])
    check("K-82", "failure_capture.procedure", "the MH tooling's FAILURE-CAPTURE.md, outside the attempt",
          fc["procedure"]["path"] == wt + "/docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/"
          "FAILURE-CAPTURE.md" and not inside(fc["procedure"]["path"], attempt))
    tooling_sums = wt + "/docs/engineering/localized-repair-c271/macos-qualification-p35/authoring/TOOLING-SHA256SUMS.txt"
    listed = None
    if os.path.lexists(tooling_sums):
        for line in read_bytes(tooling_sums).decode("ascii").splitlines():
            if line.strip() and line.split()[-1].lstrip("*").endswith("FAILURE-CAPTURE.md"):
                listed = line.split()[0]
    check("K-83", "failure_capture.procedure", "equals the reviewed tooling's recorded digest at C",
          listed == fc_actual.get("sha256"), listed=listed, exists=os.path.lexists(tooling_sums))

    # --- M0-LAUNCH.json -----------------------------------------------------------------------------------
    launch = strict_json(read_bytes(w2 + "/M0-LAUNCH.json"))
    cmd = launch["command"]
    observer_argv = [py["venv"] + "/bin/python", "-I", "-S", "-B", wt + "/" + ENTRY_POINT, "observe",
                     "--plan", plan_path, "--plan-sha256", plan_sha256]
    expected_argv = ["/usr/bin/env", "-i"] + [k + "=" + ENV[k] for k in ("PATH", "LANG", "LC_ALL", "TZ",
                                                                          "UV_THREADPOOL_SIZE")] + observer_argv
    check("L-01", "M0-LAUNCH", "argv: /usr/bin/env -i, exactly the five declared variables, the launcher with "
          "-I -S -B, the observer, observe, the plan's path and my computed digest", cmd["argv"] == expected_argv,
          argv=cmd["argv"])
    check("L-02", "M0-LAUNCH", "observer_process_argv is the argv after env", cmd["observer_process_argv"]
          == observer_argv)
    check("L-03", "M0-LAUNCH", "environment record equals the declared five", cmd["environment"] == ENV)
    check("L-04", "M0-LAUNCH", "environment_canonical_sha256 is the digest of the canonical environment",
          cmd["environment_canonical_sha256"] == hashlib.sha256(canonical(ENV)).hexdigest(),
          mine=hashlib.sha256(canonical(ENV)).hexdigest())
    check("L-05", "M0-LAUNCH", "cwd is the existing canonical evidence parent", cmd["cwd"] == parent)
    cap = cmd["capture"]
    check("L-06", "M0-LAUNCH", "capture paths: three fresh siblings of the attempt in the parent, never inside it "
          "(FC-K2), all absent now", set(cap) == {"stdout", "stderr", "exit_status"}
          and all(posixpath.dirname(p) == parent and not inside(p, attempt) and not os.path.lexists(p)
                  for p in cap.values()) and len(set(cap.values())) == 3, capture=cap)
    shell = cmd["shell_form"]
    expected_shell = ("cd " + parent + " && " + " ".join(expected_argv) + " > " + cap["stdout"] + " 2> "
                      + cap["stderr"] + "; echo $? > " + cap["exit_status"])
    check("L-07", "M0-LAUNCH", "shell form: the same argv, cwd and redirections (no quoting needed: no space or "
          "special character in any word)", shell == expected_shell and not any(
              set(w) & set(" '\"\\;&|<>()$`*?[]{}~!#") for w in expected_argv))
    bounded = launch["expected_starts"]["bounded"]
    check("L-08", "M0-LAUNCH", "expected starts are the plan's commands in order (plus order and through)",
          [{k: v for k, v in b.items() if k not in ("order", "through")} for b in bounded] == plan["commands"]
          and [b["order"] for b in bounded] == [1, 2] and launch["expected_starts"]["totals"] == {"node": 1,
                                                                                               "other": 1})
    exp = launch["expected_outputs"]
    check("L-09", "M0-LAUNCH", "all planned paths equal the plan's outputs", exp["all_planned_paths"] == ev["outputs"])
    planned_files = sorted([v for k, v in outputs.items() if type(v) is str]
                           + [v for c in ("git_version", "node_version") for k, v in outputs[c].items()
                              if k != "stage"])
    failure_files = sorted([outputs["failure"], outputs["git_version"]["failure"], outputs["node_version"]["failure"]])
    success = exp["success"]
    check("L-10", "M0-LAUNCH", "success: the planned files minus the three failure files, the three directories, "
          "and the HOST path", sorted(success["files"]) == sorted(set(planned_files) - set(failure_files))
          and sorted(success["files_absent_on_success"]) == failure_files
          and sorted(success["directories"]) == sorted([attempt, outputs["git_version"]["stage"],
                                                        outputs["node_version"]["stage"]])
          and success["host"]["path"] == outputs["host"] and success["exit_status"] == 0)
    check("L-11", "M0-LAUNCH", "plan descriptor in the launch record equals my reading",
          launch["plan"] == {"path": plan_path, "sha256": plan_sha256, "size_bytes": len(raw),
                             "mode": facts["plan_binding"]["mode"]})
    check("L-12", "M0-LAUNCH", "predicted Git line matches the git-version-line-v1 grammar",
          re.fullmatch(rb"git version [\x20-\x7e]{1,200}\n",
                       launch["expected_starts"]["predicted_stdout"]["git_version"].encode("ascii")) is not None,
          predicted=launch["expected_starts"]["predicted_stdout"])

    # --- the adoption record, the filesystem and extended attributes ------------------------------------
    adoption = rehash(wt + "/" + ADOPTION_001)
    facts["adoption_record"] = {"relative": ADOPTION_001, **binding_of(adoption), "nlink": adoption["nlink"]}
    facts["filesystems"] = {label: fs_info(path) for label, path in (
        ("worktree", wt), ("local", local), ("evidence_parent", parent), ("framework", fw),
        ("git", git["path"]), ("root", "/"))}
    facts["xattrs"] = {path: xattr_names(path) for path in (
        directory, directory + "/bin", directory + "/bin/node", directory + "/NODE-SOURCE.json", arch["path"],
        git["path"], droot, parent, plan_path, w2 + "/python-inventory-001.json", py["venv"] + "/bin/python",
        fw + "/bin/python3.12", fw + "/Resources/Python.app/Contents/MacOS/Python")}

    # --- digests of the documents read for this review --------------------------------------------------
    docs = ["docs/engineering/localized-repair-c271/macos-qualification-p35/MH-PLAN.md",
            "docs/engineering/localized-repair-c271/macos-implementation-p33/interfaces/W3-OBSERVER.md",
            "docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md",
            "docs/engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md",
            "docs/engineering/localized-repair-c271/macos-preparation-p34/OUTCOME.json",
            "docs/engineering/localized-repair-c271/macos-preparation-p34/CLOSING.json",
            "docs/engineering/localized-repair-c271/macos-preparation-p34/EXACT-RECEIPTS-SHA256SUMS.txt",
            "docs/engineering/localized-repair-c271/macos-qualification-p35/n34m/N34-M-DISPOSITION.json",
            "docs/engineering/localized-repair-c271/macos-qualification-p35/n34m/N34-M-REVIEW.md",
            "docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md",
            "docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/README.md",
            ENTRY_POINT, "prototypes/static_tray_v01/supervisor.py",
            "prototypes/static_tray_v01/supervisor_darwin_v01.py", EXTERNAL_INPUTS, ADOPTION_001]
    facts["documents_read"] = {"<worktree>/" + d: binding_of(rehash(wt + "/" + d)) for d in docs}
    w2_files = {}
    for rel, row in sorted(walk_tree(w2).items()):
        if row["kind"] == "file":
            w2_files["<local>/c271-p35/workers/W2-plan-001/" + rel] = binding_of(row)
    facts["files_under_review"] = w2_files
    mp = ["c271-p34/plans/node-install-plan.json", "c271-p34/plans/reader-install-plan.json",
          "c271-p34/receipts/node-install-result.json", "c271-p34/receipts/reader-install-result.json",
          "c271-p34/downloads/node/" + NODE_ARCHIVE, "c271-macos/node-v24.22.1-darwin-arm64/bin/node",
          "c271-macos/node-v24.22.1-darwin-arm64/NODE-SOURCE.json"]
    facts["mp_preparation"] = {"<local>/" + m: binding_of(rehash(local + "/" + m)) for m in mp}

    out = {"script": os.path.basename(__file__), "argv": sys.argv, "pid": os.getpid(), "ppid": os.getppid(),
           "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                     "dont_write_bytecode": sys.flags.dont_write_bytecode},
           "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
           "finished_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "elapsed_s": round(time.time() - t0, 3), "process_events": EVENTS,
           "checks": CHECKS, "passed": sum(c["passed"] for c in CHECKS), "failed": [c for c in CHECKS if not c["passed"]],
           "facts": facts}
    os.makedirs(os.path.dirname(a.output), exist_ok=True)
    fd = os.open(a.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        os.write(fd, (json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    print(json.dumps({"plan_sha256": plan_sha256, "checks": len(CHECKS), "passed": out["passed"],
                      "failed": [(c["id"], c["check"], c["detail"]) for c in out["failed"]],
                      "boot": boot, "elapsed_s": out["elapsed_s"], "process_events": EVENTS}, indent=1))
    return 0 if not out["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
