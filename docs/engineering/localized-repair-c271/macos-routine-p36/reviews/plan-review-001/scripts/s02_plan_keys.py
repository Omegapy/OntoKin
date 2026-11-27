"""W3 plan review 001, s02: every key of observation plan 001 against the actual state.

My constants are written from CONTRACT.md sections 3, 4 and 7, AMENDMENT-001 and W3-OBSERVER.md
sections 1 to 3 and 5 to 7. The 15 LIMITS values, which the schema names but does not list, are
written from my reading of the observer's source; s02 also extracts the observer's constant
assignments with ast.literal_eval (a static read: no observer code runs) and compares both.

python3 -I -S -B s02_plan_keys.py --plan P --mh-plan P --launch L --environment-file E --observer-source O
    --worktree W --mp-plan-sums S --mp-receipt-sums S --mp-exact-plan-sums S --mr-tooling-readme R
    --mh-tooling-sums S --commit B --tree T [--label NAME=PATH ...] --output OUT
"""
import argparse
import ast
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w3_common as common  # noqa: E402
sys.path.pop(0)

PLAN_SCHEMA = "ontokin.current-host-readback-observation-plan/0.2.0"
CONTRACT = "ontokin.current-host-readback/0.2.0"
PROFILE = "darwin-arm64-v1"
EXECUTOR = "macos-arm64-local"
TOP_KEYS = {"schema", "contract", "profile", "executor", "environment", "platform", "os", "source", "observer",
            "python", "runtime", "dependencies", "git", "commands", "evidence", "failure_capture", "limits"}
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
GIT_EXTRA = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
             "GIT_ATTR_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"}
LIMITS = {"command_ms": 5000, "active_work_ms": 3000, "cleanup_ms": 2000, "log_bytes": 4194304,
          "document_bytes": 16777216, "host_bytes": 8388608, "inspection_bytes": 8388608, "static_ms": 60000,
          "publication_ms": 30000, "tree_entries": 65536, "tree_file_bytes": 536870912, "plist_bytes": 65536,
          "macho_commands": 4096, "macho_command_bytes": 4194304, "link_hops": 40}
NODE_VERSION = "v24.22.1"
NODE_ARCHIVE = "node-v24.22.1-darwin-arm64.tar.gz"
NODE_ARCHIVE_PIN = "89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7"
NODE_CHECKSUM_FILE = {"url": "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt",
                      "sha256": "fdfbffc969c0f604beff0124d409b33a43b53f5c681d6220f80023e0d6df9dc4", "size_bytes": 3171}
NODE_MEMBER = "node-v24.22.1-darwin-arm64/bin/node"
DEP_ARCHIVE_PIN = "b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9"
EXTERNAL_INPUTS = "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json"
EXTERNAL_INPUTS_PIN = "21fd6bad8738ed51d4ced8036a0fcde5dd046823f55f71de52b9b81df659ccd5"
ENTRY_POINT = "prototypes/static_tray_v01/current_host_observation_v02.py"
SYSTEM_VERSION = "/System/Library/CoreServices/SystemVersion.plist"
CRYPTEX_CONVENTIONAL = "/System/Cryptexes/OS/System/Library/CoreServices/SystemVersion.plist"
GIT_DISPATCHER = "/usr/bin/git"
N34M_GIT = {"path": "/Library/Developer/CommandLineTools/usr/bin/git",
            "sha256": "be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae", "size_bytes": 7604272}
FAILURE_CAPTURE_REL = "docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md"
FAILURE_CAPTURE_PIN = "f387fb3ec0ed306366f6d3f22820ec344f1ac843008775475258c5de9634c99c"
INSTALL_PLAN_KEYS = {"schema", "contract", "purpose", "source_root", "archive", "destination", "root_mode", "files",
                     "directories", "members", "node_source", "report"}
RESULT_BASE = {"schema", "contract", "design_revision", "amendments", "purpose", "passed", "state", "apply_requested",
               "execution_counts", "operations", "pins", "labels", "preparer_source"}
RESULT_KEYS = {"ALREADY_PRESENT_EXACT": RESULT_BASE | {"archive", "before"},
               "INSTALLED_EXACT": RESULT_BASE | {"archive", "before", "after", "publication"}}
DEPENDENCY_VERSIONS = {"validator/package/package.json": "2.0.0-dev.3.10", "indexer-view/three/package.json": "0.186.1"}
SYSTEM_LINKS = {"/tmp": "/private/tmp", "/var": "/private/var", "/etc": "/private/etc"}
UNRESOLVED = re.compile(r"(?i)\b(todo|tbd|fixme|xxx)\b|[*?\[\]{}~`$]")
NODE_COMMANDS = {"LC_SEGMENT_64", "LC_SYMTAB", "LC_DYSYMTAB", "LC_LOAD_DYLINKER", "LC_UUID", "LC_BUILD_VERSION",
                 "LC_SOURCE_VERSION", "LC_MAIN", "LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_FUNCTION_STARTS",
                 "LC_DATA_IN_CODE", "LC_CODE_SIGNATURE", "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS",
                 "LC_DYLD_EXPORTS_TRIE"}


def binding_of(row):
    return {"sha256": row["sha256"], "size_bytes": row["size_bytes"], "mode": row["mode"]}


def rehash(path):
    _, binding, _, info = common.read_bytes(path, keep=False)
    return binding, info


def canonical_check(path, allow_absent=False):
    """Contract section 7: only /tmp, /var and /etc may be linked, and only as the first component."""
    parts = [] if path == "/" else path.split("/")[1:]
    current, system, problem = "", None, None
    if not (path.startswith("/") and posixpath.normpath(path) == path and not path.startswith("//")):
        return False, "not normalized"
    for index, name in enumerate(parts):
        current += "/" + name
        last = index == len(parts) - 1
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            if last and allow_absent:
                break
            return False, "missing component " + current
        if stat.S_ISLNK(info.st_mode):
            if index == 0 and not last and current in SYSTEM_LINKS:
                system = current
                continue
            return False, "linked component " + current
        if not last and not stat.S_ISDIR(info.st_mode):
            return False, "ancestor not a directory " + current
    expected = SYSTEM_LINKS[system] + path[len(system):] if system else path
    if os.path.realpath(path) != expected:
        return False, "realpath differs"
    return expected == path, problem


def resolve(path):
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
            target = os.readlink(candidate)
            hops.append({"path": candidate, "target": target})
            if target.startswith("/"):
                current = "/"
            pending = [p for p in target.split("/") if p] + pending
            continue
        current = candidate
    info = os.lstat(current)
    return {"state": "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode)
            else "other", "path": current, "hops": hops}


def strict_plan(raw, problems):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                problems.append("duplicate member " + key)
            result[key] = value
        return result

    def floats(text):
        problems.append("float " + text)
        return float(text)

    def constant(text):
        problems.append("constant " + text)
        return None
    return json.loads(raw.decode("ascii"), object_pairs_hook=pairs, parse_float=floats, parse_constant=constant)


def leaves(value, path="plan"):
    if isinstance(value, dict):
        for key in sorted(value):
            yield from leaves(value[key], path + "." + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, path + "[" + str(index) + "]")
    else:
        yield path, value


def walk_tree(root):
    """{relative path: lstat} for every entry below root, never following a link."""
    rows, stack = {}, [""]
    while stack:
        rel = stack.pop()
        directory = root + "/" + rel if rel else root
        for name in sorted(os.listdir(directory)):
            sub = rel + "/" + name if rel else name
            info = os.lstat(root + "/" + sub)
            rows[sub] = info
            if stat.S_ISDIR(info.st_mode):
                stack.append(sub)
    return rows


def output_paths(attempt):
    out = {key: attempt + "/" + key + ".json" for key in ("reserved", "preflight", "result", "completion", "failure")}
    out["host"] = attempt + "/HOST.json"
    for name, label in (("git_version", "host-git-version"), ("node_version", "host-node-version")):
        stage = attempt + "/" + name
        out[name] = {"stage": stage, "intent": stage + "/intent.json", "started": stage + "/started.json",
                     "inspection": stage + "/inspection.json", "postflight": stage + "/postflight.json",
                     "failure": stage + "/failure.json", "stdout": stage + "/" + label + ".stdout.log",
                     "stderr": stage + "/" + label + ".stderr.log", "process": stage + "/" + label + ".process.json"}
    return out


def expected_commands(plan):
    attempt = plan["evidence"]["attempt"]
    common_fields = {"timeout_ms": 5000, "active_work_ms": 3000, "cleanup_ms": 2000, "expected_direct_starts": 1,
                     "stderr_predicate": ""}
    return [{"id": "git_version", "kind": "other", "argv": [plan["git"]["path"], "--version"],
             "cwd": attempt + "/git_version", "label": "host-git-version", "environment": {**ENVIRONMENT, **GIT_EXTRA},
             "stdout_predicate": "git-version-line-v1", **common_fields},
            {"id": "node_version", "kind": "node", "argv": [plan["runtime"]["directory"] + "/bin/node", "--version"],
             "cwd": attempt + "/node_version", "label": "host-node-version", "environment": dict(ENVIRONMENT),
             "stdout_predicate": "v24.22.1\n", **common_fields}]


def inside(path, root):
    return path == root or path.startswith(root.rstrip("/") + "/")


def constant_value(node, known):
    """A small static evaluator for constant assignments: literals, names already found, + and * on
    constants, dict unpacking and MappingProxyType(...). Anything else is not evaluated."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in known:
            return known[node.id]
        raise ValueError("unknown name " + node.id)
    if isinstance(node, (ast.Tuple, ast.List)):
        values = [constant_value(item, known) for item in node.elts]
        return tuple(values) if isinstance(node, ast.Tuple) else values
    if isinstance(node, ast.Dict):
        result = {}
        for key, value in zip(node.keys, node.values):
            if key is None:
                result.update(constant_value(value, known))
            else:
                result[constant_value(key, known)] = constant_value(value, known)
        return result
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mult)):
        left, right = constant_value(node.left, known), constant_value(node.right, known)
        return left + right if isinstance(node.op, ast.Add) else left * right
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "MappingProxyType" and len(node.args) == 1:
        return constant_value(node.args[0], known)
    raise ValueError("not a constant expression")


def observer_constants(path):
    """The observer's module-level constant assignments, evaluated statically (no observer code runs)."""
    tree = ast.parse(open(path, "rb").read().decode("utf-8"))
    wanted = {"ENVIRONMENT", "LIMITS", "NODE_VERSION", "NODE_ARCHIVE_SHA256", "DEPENDENCY_ARCHIVE_SHA256",
              "EXTERNAL_SHA256", "CONTRACT", "PROFILE", "EXECUTOR", "NODE_CHECKSUM_FILE", "NODE_MEMBER",
              "COMMAND_IDS", "LABELS", "GIT_STDOUT_PREDICATE", "SYSTEM_VERSION_PATH", "CRYPTEX_SYSTEM_VERSION_PATH",
              "GIT_DISPATCHER", "ENTRY_POINT", "PLAN_SCHEMA", "GIT_ENVIRONMENT", "PREFIX", "VERSION",
              "NODE_ARCHIVE", "NODE_VERSION_STDOUT"}
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name not in wanted:
                continue
            try:
                found[name] = constant_value(node.value, found)
            except (ValueError, TypeError):
                found[name] = "not evaluated"
    if isinstance(found.get("NODE_VERSION_STDOUT"), bytes):
        found["NODE_VERSION_STDOUT"] = found["NODE_VERSION_STDOUT"].decode("ascii")
    return found


def macho_node(data):
    """W3-OBSERVER section 6.2, by my own parser: returns facts and the list of rule failures."""
    failures = []
    if data[:4] != b"\xcf\xfa\xed\xfe":
        return {"magic": data[:4].hex()}, ["not thin MH_MAGIC_64"]
    _, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags, _ = struct.unpack_from("<8I", data, 0)
    if cputype != 0x0100000C or cpusubtype != 0:
        failures.append("cpu")
    if filetype != 2:
        failures.append("filetype")
    if not (0 < ncmds <= 4096 and 0 < sizeofcmds <= 4194304 and 32 + sizeofcmds <= len(data)):
        failures.append("table")
    names = {0x19: "LC_SEGMENT_64", 0x2: "LC_SYMTAB", 0xB: "LC_DYSYMTAB", 0xE: "LC_LOAD_DYLINKER", 0x1B: "LC_UUID",
             0x32: "LC_BUILD_VERSION", 0x2A: "LC_SOURCE_VERSION", 0x80000028: "LC_MAIN", 0xC: "LC_LOAD_DYLIB",
             0x80000018: "LC_LOAD_WEAK_DYLIB", 0x26: "LC_FUNCTION_STARTS", 0x29: "LC_DATA_IN_CODE",
             0x1D: "LC_CODE_SIGNATURE", 0x80000022: "LC_DYLD_INFO_ONLY", 0x80000034: "LC_DYLD_CHAINED_FIXUPS",
             0x80000033: "LC_DYLD_EXPORTS_TRIE", 0x8000001C: "LC_RPATH", 0x27: "LC_DYLD_ENVIRONMENT",
             0x80000023: "LC_LOAD_UPWARD_DYLIB", 0x8000001F: "LC_REEXPORT_DYLIB", 0xD: "LC_ID_DYLIB"}
    commands, dylibs, dylinker, offset = [], [], [], 32
    for _ in range(ncmds):
        cmd, size = struct.unpack_from("<II", data, offset)
        if size < 8 or size % 8 or offset + size > 32 + sizeofcmds:
            failures.append("command size")
            break
        name = names.get(cmd, "0x%08x" % cmd)
        commands.append(name)
        body = data[offset:offset + size]
        if name in ("LC_LOAD_DYLIB", "LC_LOAD_WEAK_DYLIB", "LC_LOAD_DYLINKER"):
            field = struct.unpack_from("<I", body, 8)[0]
            text = body[field:body.index(b"\0", field)].decode("ascii")
            (dylinker if name == "LC_LOAD_DYLINKER" else dylibs).append(text)
        offset += size
    if offset != 32 + sizeofcmds:
        failures.append("sizes do not add up")
    for name in commands:
        if name not in NODE_COMMANDS:
            failures.append("command outside the closed list: " + name)
    counts = {name: commands.count(name) for name in set(commands)}
    once = {"LC_LOAD_DYLINKER", "LC_MAIN", "LC_UUID", "LC_SYMTAB", "LC_DYSYMTAB", "LC_CODE_SIGNATURE",
            "LC_DYLD_INFO_ONLY", "LC_DYLD_CHAINED_FIXUPS", "LC_DYLD_EXPORTS_TRIE", "LC_FUNCTION_STARTS",
            "LC_DATA_IN_CODE", "LC_SOURCE_VERSION", "LC_ID_DYLIB"}
    failures += ["duplicate " + name for name, count in counts.items() if count > 1 and name in once]
    if counts.get("LC_LOAD_DYLINKER") != 1 or counts.get("LC_MAIN") != 1 or dylinker != ["/usr/lib/dyld"]:
        failures.append("dylinker or main")
    for path in dylibs:
        if path.startswith("@") or not path.startswith(("/usr/lib/", "/System/Library/")) or \
                posixpath.normpath(path) != path:
            failures.append("dylib path " + path)
    return {"cputype": "0x%08x" % cputype, "cpusubtype": "0x%08x" % cpusubtype, "filetype": filetype,
            "flags": "0x%08x" % flags, "ncmds": ncmds, "commands": commands, "counts": counts, "dylibs": dylibs,
            "dylinker": dylinker}, failures


def receipt_rule(install, *, source_root, destination, purpose, archive, files, directories, root_mode, executable):
    """W3-OBSERVER section 3's receipt rule, written by me. Returns (facts, failures)."""
    failures = []
    plan_raw, _, _, _ = common.read_bytes(install["plan"]["path"])
    result_raw, _, _, _ = common.read_bytes(install["result"]["path"])
    plan, result = common.strict_loads(plan_raw), common.strict_loads(result_raw)
    if set(plan) != INSTALL_PLAN_KEYS:
        failures.append("plan keys")
    members = plan.get("members")
    expect = {"schema": "ontokin.current-host-readback-install/0.2.0", "contract": CONTRACT, "purpose": purpose,
              "source_root": source_root, "destination": destination, "root_mode": root_mode, "files": files,
              "directories": directories, "archive": archive, "report": install["result"]["path"]}
    for key, value in expect.items():
        if plan.get(key) != value:
            failures.append("plan " + key)
    if not (isinstance(members, dict) and members and all(isinstance(row, dict) and type(row.get("size_bytes")) is int
                                                          for row in members.values())):
        failures.append("plan members")
    state = result.get("state")
    if state not in RESULT_KEYS or result.get("passed") is not True:
        failures.append("result state " + str(state))
        return {"state": state}, failures
    if set(result) != RESULT_KEYS[state]:
        failures.append("result keys")
    pins = {"origin": "adopted-contract", "node_archive_sha256": NODE_ARCHIVE_PIN,
            "dependency_archive_sha256": DEP_ARCHIVE_PIN}
    for key, value in {"schema": "ontokin.current-host-readback-install-result/0.2.0", "contract": CONTRACT,
                       "design_revision": 4, "amendments": ["P33-AMENDMENT-001"], "purpose": purpose,
                       "execution_counts": {"node": 0, "ldd": 0, "checkers": 0}, "pins": pins}.items():
        if result.get(key) != value:
            failures.append("result " + key)
    if type(result.get("apply_requested")) is not bool:
        failures.append("apply_requested")
    if not (isinstance(result.get("operations"), list) and all(
            isinstance(row, dict) and row.get("operation") in ("created_owned_stage", "removed_owned_stage")
            for row in result["operations"])):
        failures.append("operations")
    labels = result.get("labels", {})
    label_pins = ({"origin": "adopted-contract", "node_archive_sha256": NODE_ARCHIVE_PIN, "node_executable": executable}
                  if purpose == "selected-node" else
                  {"origin": "adopted-contract", "dependency_archive_sha256": DEP_ARCHIVE_PIN})
    if set(labels) != {"executor", "contract", "profile", "design_revision", "amendments", "pins", "os"} or \
            labels.get("executor") != EXECUTOR or labels.get("contract") != CONTRACT or \
            labels.get("profile") != PROFILE or labels.get("design_revision") != 4 or \
            labels.get("amendments") != ["P33-AMENDMENT-001"] or labels.get("pins") != label_pins:
        failures.append("labels")
    os_label = labels.get("os", {})
    fields = ("product_version", "product_build_version", "product_version_extra")

    def os_fields(row):
        return (isinstance(row.get("product_version"), str) and row["product_version"]
                and isinstance(row.get("product_build_version"), str) and row["product_build_version"]
                and (row.get("product_version_extra") is None or isinstance(row["product_version_extra"], str)))
    cryptex = os_label.get("cryptex") if isinstance(os_label, dict) else None
    if not (isinstance(os_label, dict) and set(os_label) == set(fields) | {"cryptex"} and os_fields(os_label) and
            (cryptex == {"state": "absent"} or (isinstance(cryptex, dict) and cryptex.get("state") == "present"
                                                 and set(cryptex) == set(fields) | {"state"} and os_fields(cryptex)))):
        failures.append("labels.os shape")
    source = result.get("preparer_source")
    if not (isinstance(source, dict) and set(source) == {"root", "files_at_start"} and source["root"] == source_root
            and isinstance(source["files_at_start"], dict)):
        failures.append("preparer_source")

    def readback(value, wanted):
        return isinstance(value, dict) and value.get("state") == wanted and set(value) == (
            {"state"} if wanted == "absent" else {"state", "files", "directories"})
    if state == "INSTALLED_EXACT":
        if not (result.get("apply_requested") is True and readback(result.get("before"), "absent")
                and readback(result.get("after"), "complete_exact")
                and result.get("publication") == {"call": "renamex_np", "library": "/usr/lib/libSystem.B.dylib",
                                                  "flag": "RENAME_EXCL", "flag_value": 4}):
            failures.append("installed readbacks or publication")
    elif not readback(result.get("before"), "complete_exact"):
        failures.append("already-present readback")
    summary = result.get("archive", {})
    members_digest = hashlib.sha256(json.dumps(members, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                                               allow_nan=False).encode("ascii")).hexdigest()
    keys = {"sha256", "size_bytes", "members", "expanded_bytes", "symlinks", "member_inventory_sha256",
            "extracted_members"} | ({"executable"} if purpose == "selected-node" else set())
    if not (isinstance(summary, dict) and set(summary) == keys and summary["sha256"] == archive["sha256"]
            and summary["size_bytes"] == archive["size_bytes"] and summary["members"] == len(members)
            and summary["expanded_bytes"] == sum(row["size_bytes"] for row in members.values())
            and summary["member_inventory_sha256"] == members_digest):
        failures.append("archive summary")
    if purpose == "selected-node":
        extracted = summary.get("executable", {})
        if not (isinstance(extracted, dict) and set(extracted) == {"member", "path", "sha256", "size_bytes", "mode",
                                                                   "macho"}
                and extracted["member"] == NODE_MEMBER and extracted["path"] == "bin/node"
                and binding_of(extracted) == executable and isinstance(extracted["macho"], dict)
                and set(extracted["macho"]) == {"magic", "cputype", "cpusubtype", "filetype"}):
            failures.append("extracted executable")
    archive_binding, _ = rehash(archive["path"])
    if archive_binding != binding_of(archive):
        failures.append("archive bytes")
    return {"state": state, "apply_requested": result.get("apply_requested"), "members": len(members),
            "member_inventory_sha256": members_digest, "plan_node_source": plan.get("node_source"),
            "operations": [row.get("operation") for row in result.get("operations", [])],
            "labels_os": os_label}, failures


def main():
    common.start()
    parser = argparse.ArgumentParser()
    for name in ("plan", "mh-plan", "launch", "environment-file", "observer-source", "worktree", "mp-plan-sums",
                 "mp-receipt-sums", "mp-exact-plan-sums", "mr-tooling-readme", "mh-tooling-sums", "commit", "tree",
                 "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--label", action="append", default=[])
    args = parser.parse_args()
    labels = common.parse_labels(args.label)
    checks = common.Checks()
    began = time.monotonic()
    out = {"schema": "w3.p36.plan-review-001.s02/1", "pid": os.getpid(),
           "boot_before": common.sysctl_text("kern.bootsessionuuid")}

    # K-01 to K-05: form, keys, constants, environment, limits.
    raw, plan_binding, _, plan_info = common.read_bytes(args.plan)
    out["plan"] = {**plan_binding, "nlink": plan_info.st_nlink}
    problems = []
    plan = strict_plan(raw, problems)
    canonical = common.canonical_json(plan) == raw
    all_leaves = list(leaves(plan))
    nulls = [path for path, value in all_leaves if value is None]
    unresolved = [path for path, value in all_leaves if isinstance(value, str) and UNRESOLVED.search(value)]
    unresolved += [path for path, _ in all_leaves for part in re.split(r"[.\[\]]", path)
                   if part and UNRESOLVED.search(part)]
    placeholders = [path for path, value in all_leaves if isinstance(value, str) and re.fullmatch(r"(.)\1{63}", value)]
    checks.add("K-01", canonical and not problems and not nulls and not unresolved and not placeholders,
               "canonical JSON (sorted keys, compact, ASCII, no trailing newline); no duplicate member, float, "
               "non-finite constant or null; no TODO, TBD, FIXME, XXX, wildcard, shell character or backtick in any "
               "value or key; no one-digit digest", {"leaves": len(all_leaves), "problems": problems, "nulls": nulls,
                                                      "unresolved": unresolved, "placeholders": placeholders})
    checks.add("K-02", set(plan) == TOP_KEYS, "the 17 top-level keys are exactly the schema's", sorted(plan))
    checks.add("K-03", (plan["schema"], plan["contract"], plan["profile"], plan["executor"]) ==
               (PLAN_SCHEMA, CONTRACT, PROFILE, EXECUTOR), "schema, contract, profile and executor",
               [plan["schema"], plan["contract"], plan["profile"], plan["executor"]])
    checks.add("K-04", plan["environment"] == ENVIRONMENT, "environment is exactly the declared five", plan["environment"])
    constants = observer_constants(args.observer_source)
    out["observer_constants"] = constants
    checks.add("K-05", plan["limits"] == LIMITS == constants.get("LIMITS") and
               constants.get("ENVIRONMENT") == ENVIRONMENT and constants.get("CONTRACT") == CONTRACT and
               constants.get("PROFILE") == PROFILE and constants.get("EXECUTOR") == EXECUTOR and
               constants.get("NODE_VERSION") == NODE_VERSION and constants.get("NODE_ARCHIVE_SHA256") == NODE_ARCHIVE_PIN
               and constants.get("DEPENDENCY_ARCHIVE_SHA256") == DEP_ARCHIVE_PIN and
               constants.get("EXTERNAL_SHA256") == EXTERNAL_INPUTS_PIN and
               constants.get("NODE_CHECKSUM_FILE") == NODE_CHECKSUM_FILE and constants.get("NODE_MEMBER") == NODE_MEMBER
               and constants.get("PLAN_SCHEMA") == PLAN_SCHEMA
               and constants.get("GIT_ENVIRONMENT") == {**ENVIRONMENT, **GIT_EXTRA}
               and constants.get("COMMAND_IDS") == ("git_version", "node_version")
               and constants.get("LABELS") == {"git_version": "host-git-version", "node_version": "host-node-version"}
               and constants.get("GIT_STDOUT_PREDICATE") == "git-version-line-v1"
               and constants.get("NODE_VERSION_STDOUT") == "v24.22.1\n"
               and constants.get("SYSTEM_VERSION_PATH") == SYSTEM_VERSION
               and constants.get("CRYPTEX_SYSTEM_VERSION_PATH") == CRYPTEX_CONVENTIONAL
               and constants.get("GIT_DISPATCHER") == GIT_DISPATCHER and constants.get("ENTRY_POINT") == ENTRY_POINT
               and constants.get("NODE_ARCHIVE") == NODE_ARCHIVE,
               "the 15 limits equal my values and the observer's LIMITS; my other constants, written from the "
               "documents, equal the observer's (evaluated statically from its source)",
               {"limits": plan["limits"], "not_equal": sorted(
                   name for name, mine in (("LIMITS", LIMITS), ("ENVIRONMENT", ENVIRONMENT), ("PLAN_SCHEMA", PLAN_SCHEMA),
                                           ("GIT_ENVIRONMENT", {**ENVIRONMENT, **GIT_EXTRA}))
                   if constants.get(name) != mine)})

    # K-06 to K-08: platform, boot and OS identity.
    uname = os.uname()
    platform = plan["platform"]
    now = {"system": uname.sysname, "release": uname.release, "machine": uname.machine,
           "kern.osrelease": common.sysctl_text("kern.osrelease"), "kern.osversion": common.sysctl_text("kern.osversion"),
           "proc_translated": common.sysctl_int("sysctl.proc_translated"),
           "boot_session_uuid": common.sysctl_text("kern.bootsessionuuid")}
    out["platform_now"] = now
    checks.add("K-06", platform == {"system": "Darwin", "release": now["release"], "machine": "arm64",
                                    "proc_translated": 0, "boot_session_uuid": now["boot_session_uuid"]}
               and now["system"] == "Darwin" and now["machine"] == "arm64" and now["proc_translated"] == 0
               and now["release"] == now["kern.osrelease"],
               "platform: Darwin, the actual release, arm64, not translated, and this boot", {"plan": platform, "now": now})
    system = plan["os"]["system_version"]
    system_raw, system_binding, _, _ = common.read_bytes(SYSTEM_VERSION)
    plist = plistlib.loads(system_raw)
    out["os_now"] = {"product_name": plist.get("ProductName"), "product_version": plist.get("ProductVersion"),
                     "product_build_version": plist.get("ProductBuildVersion"),
                     "product_version_extra": plist.get("ProductVersionExtra"), "binding": system_binding}
    checks.add("K-07", system["path"] == SYSTEM_VERSION and canonical_check(SYSTEM_VERSION)[0]
               and binding_of(system) == system_binding and plist.get("ProductBuildVersion") == now["kern.osversion"],
               "os.system_version: the canonical SystemVersion.plist, rehashed, whose build equals kern.osversion",
               out["os_now"])
    cryptex = plan["os"]["cryptex"]
    chain = resolve(CRYPTEX_CONVENTIONAL)
    cryptex_binding, _ = rehash(chain["path"]) if chain["state"] == "file" else (None, None)
    cryptex_plist = plistlib.loads(common.read_bytes(chain["path"])[0]) if chain["state"] == "file" else {}
    out["cryptex_now"] = {"chain": chain, "binding": cryptex_binding,
                          "product_version": cryptex_plist.get("ProductVersion"),
                          "product_build_version": cryptex_plist.get("ProductBuildVersion")}
    checks.add("K-08", cryptex.get("state") == "present" and set(cryptex) == {"state", "path", "sha256", "size_bytes", "mode"}
               and chain["state"] == "file" and chain["path"] == cryptex["path"] and len(chain["hops"]) == 1
               and canonical_check(cryptex["path"])[0] and binding_of(cryptex) == cryptex_binding,
               "os.cryptex: present; the conventional name resolves by one hop to the plan's canonical path, rehashed",
               out["cryptex_now"])

    # K-09 to K-12: source, observer, Python.
    source = plan["source"]
    root = source["root"]
    checks.add("K-09", root == args.worktree and canonical_check(root)[0] and source["commit"] == args.commit
               and source["tree"] == args.tree and set(source) == {"root", "commit", "tree", "inventory"},
               "source.root is the canonical worktree; commit and tree are B and its tree (s04 reads them)",
               {"commit": source["commit"], "tree": source["tree"]})
    inventory_binding, inventory_info = rehash(source["inventory"]["path"])
    inventory = common.strict_loads(common.read_bytes(source["inventory"]["path"])[0])
    checks.add("K-10", binding_of(source["inventory"]) == inventory_binding and canonical_check(source["inventory"]["path"])[0]
               and set(inventory) == {"schema", "files"} and inventory["schema"] == "ontokin.current-host-readback-source/0.2.0",
               "source.inventory: canonical path, rehashed, schema source/0.2.0 (s04 recomputes it)", inventory_binding)
    observer = plan["observer"]
    observer_binding, _ = rehash(observer["path"])
    checks.add("K-11", observer["path"] == root + "/" + ENTRY_POINT and binding_of(observer) == observer_binding
               and inventory["files"].get(ENTRY_POINT) == observer_binding,
               "observer: the entry point under the root, rehashed, equal to the source inventory's entry", observer_binding)
    python = plan["python"]
    cfg_raw = common.read_bytes(python["venv"] + "/pyvenv.cfg")[0].decode()
    cfg_version = re.search(r"^version\s*=\s*(\S+)$", cfg_raw, flags=re.MULTILINE)
    py_binding, _ = rehash(python["inventory"]["path"])
    checks.add("K-12", python["venv"] == root + "/.venv" and canonical_check(python["venv"])[0]
               and canonical_check(python["framework"])[0]
               and re.fullmatch(r".*/Python\.framework/Versions/3\.12", python["framework"]) is not None
               and python["version"] == (cfg_version.group(1) if cfg_version else None)
               and python["version"] == "%d.%d.%d" % sys.version_info[:3]
               and binding_of(python["inventory"]) == py_binding and canonical_check(python["inventory"]["path"])[0]
               and set(python) == {"venv", "framework", "version", "inventory"},
               "python: the root's .venv, the canonical framework version directory, pyvenv.cfg's version (also mine), "
               "and the inventory rehashed (s03 recomputes it)",
               {"version": python["version"], "inventory": py_binding, "my_base_prefix_is_framework":
                os.path.realpath(sys.base_prefix) == python["framework"]})

    # K-13 to K-18: runtime.
    runtime = plan["runtime"]
    directory = runtime["directory"]
    tree = walk_tree(directory)
    layout = {rel: ("directory" if stat.S_ISDIR(info.st_mode) else "file" if stat.S_ISREG(info.st_mode) else "other")
              for rel, info in tree.items()}
    root_info = os.lstat(directory)
    checks.add("K-13", canonical_check(directory)[0] and layout == {"bin": "directory", "bin/node": "file",
                                                                    "NODE-SOURCE.json": "file"}
               and all(info.st_nlink == 1 for rel, info in tree.items() if stat.S_ISREG(info.st_mode))
               and common.mode_text(root_info) == runtime["root_mode"] == "0o755"
               and common.mode_text(tree["bin"]) == runtime["bin_mode"] == "0o755",
               "runtime.directory: canonical, exactly {bin/, bin/node, NODE-SOURCE.json}, single-link files, the modes",
               {"layout": layout, "root_mode": common.mode_text(root_info)})
    checks.add("K-14", runtime["version"] == NODE_VERSION, "runtime.version is v24.22.1", runtime["version"])
    node_raw, node_binding, _, _ = common.read_bytes(directory + "/bin/node")
    checks.add("K-15", binding_of(runtime["executable"]) == node_binding, "runtime.executable rehashed", node_binding)
    macho, macho_failures = macho_node(node_raw)
    out["node_macho"] = macho
    checks.add("K-16", not macho_failures, "bin/node meets W3-OBSERVER section 6.2 by my own parser: thin arm64, "
               "subtype 0, MH_EXECUTE, only the closed 16 commands, one /usr/lib/dyld and one LC_MAIN, system dylibs",
               {"failures": macho_failures, "dylibs": macho.get("dylibs"), "ncmds": macho.get("ncmds")})
    del node_raw
    source_raw, source_binding, _, _ = common.read_bytes(directory + "/NODE-SOURCE.json")
    content = common.strict_loads(source_raw)
    content_ok = (json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("ascii") == source_raw
                  and set(content) == {"schema", "contract", "archive", "checksum_file", "signature_check",
                                       "member_inventory_sha256", "extracted"}
                  and content["schema"] == "ontokin.current-host-readback-node-source/0.2.0"
                  and content["contract"] == CONTRACT
                  and content["archive"] == {"name": NODE_ARCHIVE, "sha256": NODE_ARCHIVE_PIN,
                                             "size_bytes": runtime["archive"]["size_bytes"]}
                  and content["checksum_file"] == NODE_CHECKSUM_FILE
                  and set(content["signature_check"]) == {"status", "detail"}
                  and content["signature_check"]["status"] in ("not_performed", "verified", "failed")
                  and re.fullmatch(r"[0-9a-f]{64}", content["member_inventory_sha256"]) is not None
                  and content["extracted"] == {"member": NODE_MEMBER, "path": "bin/node", **node_binding})
    checks.add("K-17", binding_of(runtime["node_source"]) == source_binding and content_ok,
               "runtime.node_source rehashed; NODE-SOURCE.json is canonical with its seven keys, the pinned archive, "
               "the checksum-file identity, a recorded signature status and the executable's binding",
               {"signature_status": content["signature_check"]["status"], "binding": source_binding})
    archive = runtime["archive"]
    archive_binding, archive_info = rehash(archive["path"])
    checks.add("K-18", canonical_check(archive["path"])[0] and binding_of(archive) == archive_binding
               and archive["sha256"] == NODE_ARCHIVE_PIN and archive_info.st_nlink == 1,
               "runtime.archive: canonical, rehashed, the contract's pin", archive_binding)
    sums = {}
    for name in ("mp_plan_sums", "mp_receipt_sums", "mp_exact_plan_sums", "mh_tooling_sums"):
        text = common.read_bytes(getattr(args, name))[0].decode()
        sums[name] = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in text.splitlines() if "  " in line}
    install_rows = {}
    for owner_name, owner in (("runtime", runtime["install"]), ("dependencies", plan["dependencies"]["install"])):
        for key in ("plan", "result"):
            descriptor = owner[key]
            actual, info = rehash(descriptor["path"])
            base = posixpath.basename(descriptor["path"])
            listed = (sums["mp_plan_sums"].get(base) if key == "plan" else sums["mp_receipt_sums"].get(base))
            listed_exact = (sums["mp_exact_plan_sums"].get(base) if key == "plan" else listed)
            install_rows[owner_name + "." + key] = {"binding": actual, "equal": binding_of(descriptor) == actual,
                                                    "listed": listed == actual["sha256"],
                                                    "listed_exact": listed_exact == actual["sha256"],
                                                    "canonical": canonical_check(descriptor["path"])[0]}
    out["install_descriptors"] = install_rows
    runtime_facts, runtime_failures = receipt_rule(
        runtime["install"], source_root=root, destination=directory, purpose="selected-node", archive=archive,
        files={"bin/node": binding_of(runtime["executable"]), "NODE-SOURCE.json": binding_of(runtime["node_source"])},
        directories={"bin": runtime["bin_mode"]}, root_mode=runtime["root_mode"],
        executable=binding_of(runtime["executable"]))
    planned_source_ok = (runtime_facts.get("plan_node_source") == {"signature_check": content["signature_check"]}
                         and runtime_facts.get("member_inventory_sha256") == content["member_inventory_sha256"])
    out["runtime_receipt"] = {"facts": runtime_facts, "failures": runtime_failures}
    checks.add("K-19", all(row["equal"] and row["listed"] and row["listed_exact"] and row["canonical"]
                           for name, row in install_rows.items() if name.startswith("runtime"))
               and not runtime_failures and planned_source_ok,
               "runtime.install: MP's exact plan and receipt, rehashed and listed in MP's sums; my receipt rule passes; "
               "the plan's node_source and member digest equal NODE-SOURCE.json's",
               {"state": runtime_facts.get("state"), "failures": runtime_failures})

    # K-20 to K-23: dependencies.
    deps = plan["dependencies"]
    deps_root = deps["root"]
    deps_tree = walk_tree(deps_root)
    files = {rel: info for rel, info in deps_tree.items() if stat.S_ISREG(info.st_mode)}
    dirs = {rel: common.mode_text(info) for rel, info in deps_tree.items() if stat.S_ISDIR(info.st_mode)}
    others = [rel for rel, info in deps_tree.items() if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))]
    installed = {rel: rehash(deps_root + "/" + rel)[0] for rel in files}
    dep_inv_raw, dep_inv_binding, _, _ = common.read_bytes(deps["inventory"]["path"])
    dep_inv = common.strict_loads(dep_inv_raw)
    external_raw, external_binding, _, _ = common.read_bytes(root + "/" + EXTERNAL_INPUTS)
    manifest = json.loads(external_raw)
    prefix = manifest["dependencies_root"] + "/"
    historical = {name[len(prefix):]: row for name, row in manifest["files"].items() if name.startswith(prefix)}
    necessary = {posixpath.dirname(name) for name in dep_inv.get("files", {})}
    necessary = {"/".join(name.split("/")[:index]) for name in necessary for index in range(1, len(name.split("/")) + 1)}
    necessary.discard("")
    dep_archive = dep_inv.get("archive", {})
    dep_archive_binding, _ = rehash(dep_archive["path"])
    versions = {name: json.loads(common.read_bytes(deps_root + "/" + name)[0]).get("version")
                for name in DEPENDENCY_VERSIONS}
    checks.add("K-20", canonical_check(deps_root)[0] and len(files) == 24 and len(dirs) == 13 and not others
               and ".DS_Store" not in {posixpath.basename(rel) for rel in deps_tree}
               and all(info.st_nlink == 1 for info in files.values()),
               "dependencies.root: canonical; 24 single-link files and 13 directories; no link, special file or .DS_Store",
               {"files": len(files), "directories": len(dirs), "others": others})
    checks.add("K-21", binding_of(deps["inventory"]) == dep_inv_binding and common.canonical_json(dep_inv) == dep_inv_raw
               and set(dep_inv) == {"schema", "files", "directories", "archive"}
               and dep_inv["schema"] == "ontokin.current-host-readback-dependencies/0.2.0"
               and {rel: binding_of(row) for rel, row in dep_inv["files"].items()} == installed
               and dep_inv["directories"] == dirs and set(dirs) == necessary
               and external_binding["sha256"] == EXTERNAL_INPUTS_PIN and len(historical) == 24
               and all({"sha256": dep_inv["files"][name]["sha256"], "size_bytes": dep_inv["files"][name]["size_bytes"]}
                       == row for name, row in historical.items())
               and dep_archive_binding == binding_of(dep_archive) and dep_archive["sha256"] == DEP_ARCHIVE_PIN
               and dep_archive["path"] == root + "/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz"
               and versions == DEPENDENCY_VERSIONS,
               "dependencies.inventory: rehashed, canonical, its four keys; files equal the installed tree and the C199 "
               "pins; directories exact and necessary; the archive is the contract's pin; validator and Three.js versions",
               {"binding": dep_inv_binding, "versions": versions, "archive": dep_archive_binding})
    deps_facts, deps_failures = receipt_rule(
        deps["install"], source_root=root, destination=deps_root, purpose="retained-dependencies", archive=dep_archive,
        files={rel: binding_of(row) for rel, row in dep_inv["files"].items()}, directories=dep_inv["directories"],
        root_mode=common.mode_text(os.lstat(deps_root)), executable=None)
    out["dependencies_receipt"] = {"facts": deps_facts, "failures": deps_failures}
    checks.add("K-22", all(row["equal"] and row["listed"] and row["listed_exact"] and row["canonical"]
                           for name, row in install_rows.items() if name.startswith("dependencies"))
               and not deps_failures and deps_facts.get("plan_node_source") is None,
               "dependencies.install: MP's exact plan and receipt, rehashed and listed; my receipt rule passes; the plan "
               "carries no node_source", {"state": deps_facts.get("state"), "failures": deps_failures})

    # K-23 to K-24: Git.
    git = plan["git"]
    git_info = os.lstat(git["path"])
    git_binding, _ = rehash(git["path"])
    dispatcher = os.stat(GIT_DISPATCHER)
    dispatcher_binding, _ = rehash(GIT_DISPATCHER)
    git_head = common.read_bytes(git["path"], keep=False, prefix=8)[2]
    out["git_now"] = {"binding": git_binding, "magic": git_head[:4].hex(),
                      "dispatcher_sha256": dispatcher_binding["sha256"]}
    checks.add("K-23", git["path"] != GIT_DISPATCHER and not stat.S_ISLNK(git_info.st_mode)
               and canonical_check(git["path"])[0] and binding_of(git) == git_binding
               and (dispatcher.st_dev, dispatcher.st_ino) != (git_info.st_dev, git_info.st_ino)
               and dispatcher_binding["sha256"] != git_binding["sha256"]
               and {"path": git["path"], "sha256": git["sha256"], "size_bytes": git["size_bytes"]} == N34M_GIT,
               "git: N34-M's file, rehashed; canonical, no link, not /usr/bin/git, not its hard link or its bytes",
               out["git_now"])

    # K-24: commands.
    checks.add("K-24", plan["commands"] == expected_commands(plan),
               "commands: exactly git_version then node_version as W3-OBSERVER section 2 states them",
               [command["id"] for command in plan["commands"]])

    # K-25 to K-29: evidence and failure capture.
    evidence = plan["evidence"]
    parent = evidence["parent"]
    rows, current = [], parent
    while True:
        info = os.lstat(current)
        rows.append({"path": current, "device": info.st_dev, "inode": info.st_ino, "mode": common.mode_text(info),
                     "is_link": stat.S_ISLNK(info.st_mode), "is_dir": stat.S_ISDIR(info.st_mode)})
        if current == "/":
            break
        current = posixpath.dirname(current)
    rows.sort(key=lambda row: row["path"])
    mine = [{key: row[key] for key in ("path", "device", "inode", "mode")} for row in rows]
    out["ancestors_now"] = rows
    checks.add("K-25", canonical_check(parent)[0] and os.listdir(parent) == [] and stat.S_ISDIR(os.lstat(parent).st_mode),
               "evidence.parent: canonical, a directory, empty", {"entries": os.listdir(parent)})
    checks.add("K-26", evidence["ancestors"] == mine and not any(row["is_link"] for row in rows)
               and all(row["is_dir"] for row in rows),
               "evidence.ancestors: my lstat walk, sorted by path, equal; no link", mine)
    checks.add("K-27", posixpath.dirname(evidence["attempt"]) == parent and evidence["attempt"] != parent
               and not os.path.lexists(evidence["attempt"]) and canonical_check(evidence["attempt"], True)[0]
               and evidence["outputs"] == output_paths(evidence["attempt"]),
               "evidence.attempt: an absent direct child; outputs exactly the fixed topology", evidence["attempt"])
    procedure = plan["failure_capture"]["procedure"]
    procedure_binding, _ = rehash(procedure["path"])
    readme = common.read_bytes(args.mr_tooling_readme)[0].decode()
    checks.add("K-28", procedure["path"] == root + "/" + FAILURE_CAPTURE_REL and binding_of(procedure) == procedure_binding
               and procedure["sha256"] == FAILURE_CAPTURE_PIN and sums["mh_tooling_sums"].get("FAILURE-CAPTURE.md")
               == FAILURE_CAPTURE_PIN and FAILURE_CAPTURE_PIN in readme and not inside(procedure["path"], evidence["attempt"])
               and canonical_check(procedure["path"])[0],
               "failure_capture.procedure: MH's procedure at its committed path, rehashed, equal to MH's tooling sums and "
               "MR's tooling README, outside the attempt", procedure_binding)
    roots = {"source": root, "venv": python["venv"], "framework": python["framework"], "runtime": directory,
             "dependencies": deps_root, "git": posixpath.dirname(git["path"])}
    overlaps = [name for name, value in roots.items() if inside(parent, value) or inside(value, parent)]
    pairwise = [(a, b) for a in ("runtime", "dependencies", "framework") for b in ("runtime", "dependencies", "framework")
                if a < b and (inside(roots[a], roots[b]) or inside(roots[b], roots[a]))]
    pairwise += [name for name in ("runtime", "dependencies", "framework")
                 if inside(roots[name], root) or inside(root, roots[name])]
    checks.add("K-29", not overlaps and not pairwise, "the parent overlaps no bound root, and the bound roots are disjoint",
               {"overlaps": overlaps, "pairwise": pairwise})

    # K-30: every path in the plan canonical.
    path_rows = []
    attempt_ok = canonical_check(evidence["attempt"], allow_absent=True)[0]
    for path, value in all_leaves:
        if isinstance(value, str) and value.startswith("/") and ".environment." not in path:
            if inside(value, evidence["attempt"]):
                ok, why = attempt_ok and posixpath.normpath(value) == value, "inside the absent attempt"
            else:
                ok, why = canonical_check(value)
            path_rows.append({"leaf": path, "ok": ok, "why": why})
    checks.add("K-30", all(row["ok"] for row in path_rows),
               "every absolute path in the plan is canonical: no linked component; paths in the absent attempt count "
               "with an absent last component", {"paths": len(path_rows),
                                                 "failing": [row for row in path_rows if not row["ok"]]})

    # K-31: leaf-by-leaf difference from MH's exact plan.
    mh_raw, mh_binding, _, _ = common.read_bytes(args.mh_plan)
    mh_plan = common.strict_loads(mh_raw)
    a, b = dict(leaves(plan)), dict(leaves(mh_plan))
    differing = sorted(key for key in set(a) | set(b) if a.get(key, "<absent>") != b.get(key, "<absent>"))
    allowed = {"plan.source.commit", "plan.source.tree", "plan.source.inventory.path", "plan.python.inventory.path",
               "plan.dependencies.inventory.path", "plan.evidence.parent", "plan.evidence.attempt",
               "plan.commands[0].cwd", "plan.commands[1].cwd", "plan.evidence.ancestors[5].path",
               "plan.evidence.ancestors[5].inode", "plan.evidence.ancestors[6].path", "plan.evidence.ancestors[6].inode"}
    unexplained = [key for key in differing if key not in allowed and not key.startswith("plan.evidence.outputs.")]
    out["mh_difference"] = {"mh_plan": mh_binding, "differing_leaves": len(differing), "unexplained": unexplained,
                            "keys": differing,
                            "values": {key: [b.get(key, "<absent>"), a.get(key, "<absent>")] for key in differing
                                       if not key.startswith("plan.evidence.outputs.")},
                            "outputs_leaves": sum(1 for key in differing if key.startswith("plan.evidence.outputs."))}
    checks.add("K-31", len(raw) == len(mh_raw) and not unexplained and set(a) == set(b),
               "against MH's exact plan: the same size and leaves; every differing leaf is the commit, tree, an inventory "
               "path, an evidence path, a command cwd, or the path and inode of the two new ancestors",
               {"differing": len(differing), "unexplained": unexplained})

    # K-32 to K-34: M0-LAUNCH.json and M0-ENVIRONMENT.json.
    launch_raw, launch_binding, _, _ = common.read_bytes(args.launch)
    launch = common.strict_loads(launch_raw)
    env_raw, env_binding, _, _ = common.read_bytes(args.environment_file)
    venv_python = python["venv"] + "/bin/python"
    words = ["PATH=/usr/bin:/bin", "LANG=C.UTF-8", "LC_ALL=C.UTF-8", "TZ=UTC", "UV_THREADPOOL_SIZE=2"]
    expected_argv = {mode: ["/usr/bin/env", "-i"] + words + [venv_python, "-I", "-S", "-B", observer["path"], mode,
                                                           "--plan", args.plan, "--plan-sha256"]
                     for mode in ("observe", "static")}
    launch_rows = {}
    for key, mode in (("observe", "observe"), ("static_before_observe", "static")):
        block = launch[key]
        capture = block["capture"]
        expected_capture = {name: parent + "/" + posixpath.basename(evidence["attempt"]) + "." + mode + "." + suffix
                            for name, suffix in (("stdout", "stdout.txt"), ("stderr", "stderr.txt"),
                                                 ("exit_status", "exit.txt"))}
        shell = ("cd " + parent + " && " + " ".join(expected_argv[mode]) + ' "$PLAN_SHA256" > ' +
                 expected_capture["stdout"] + " 2> " + expected_capture["stderr"] + "; echo $? > " +
                 expected_capture["exit_status"])
        safe = all(re.fullmatch(r"[A-Za-z0-9_./:=@+-]+", word) for word in expected_argv[mode] + [parent]
                   + list(expected_capture.values()))
        launch_rows[key] = {
            "argv": block["argv_without_digest"] == expected_argv[mode],
            "observer_argv": block["observer_process_argv_without_digest"] == expected_argv[mode][7:],
            "environment": block["environment"] == ENVIRONMENT, "cwd": block["cwd"] == parent,
            "capture": capture == expected_capture,
            "capture_absent": not any(os.path.lexists(path) for path in capture.values()),
            "capture_outside_attempt": not any(inside(path, evidence["attempt"]) for path in capture.values()),
            "shell_form": block["shell_form"] == shell, "words_need_no_quoting": safe,
            "plan_digest_not_in_block": plan_binding["sha256"] not in json.dumps(block),
            "capture_distinct_from_records": not (set(capture.values()) & {
                parent + "/observe-001.static.command-record.json", parent + "/observe-001.observe.command-record.json"})}
    expected_starts = [{**{key: value for key, value in command.items()}, "order": index + 1,
                        "through": "prototypes/static_tray_v01/supervisor_darwin_v01.py run_process"}
                       for index, command in enumerate(plan["commands"])]
    outputs = output_paths(evidence["attempt"])
    planned_files = sorted(value for key, value in outputs.items() if isinstance(value, str))
    planned_files += sorted(value for name in ("git_version", "node_version") for key, value in outputs[name].items()
                            if key != "stage")
    success = launch["expected_outputs"]["success"]
    failure_files = {outputs["failure"], outputs["git_version"]["failure"], outputs["node_version"]["failure"]}
    plan_digest_text = plan_binding["sha256"]
    launch_rows["record"] = {
        "expected_starts": launch["expected_starts"]["bounded"] == expected_starts,
        "totals": launch["expected_starts"]["totals"] == {"node": 1, "other": 1},
        "success_files": sorted(success["files"]) == sorted(set(planned_files) - failure_files),
        "absent_on_success": sorted(success["files_absent_on_success"]) == sorted(failure_files),
        "directories": sorted(success["directories"]) == sorted([evidence["attempt"], outputs["git_version"]["stage"],
                                                                 outputs["node_version"]["stage"]]),
        "host_path": success["host"]["path"] == outputs["host"],
        "plan_path_size_mode": launch["plan"]["path"] == args.plan and launch["plan"]["size_bytes"] == len(raw)
        and launch["plan"]["mode"] == plan_binding["mode"],
        "plan_digest_absent": plan_digest_text not in launch_raw.decode("ascii"),
        "predicted_git_fits_grammar": re.fullmatch(r"git version [\x20-\x7e]{1,200}\n",
                                                   launch["predicted_stdout"]["git_version"]) is not None,
        "predicted_node": launch["predicted_stdout"]["node_version"] == "v24.22.1\n",
        "environment_file": launch["environment_file"]["path"] == args.environment_file
        and launch["environment_file"]["sha256"] == env_binding["sha256"]
        and env_raw == common.canonical_json(ENVIRONMENT),
        "refused_process_events_empty": launch.get("refused_process_events") == []}
    out["launch"] = {"binding": launch_binding, "rows": launch_rows, "environment_file": env_binding}
    checks.add("K-32", all(all(row.values()) for name, row in launch_rows.items() if name != "record"),
               "M0-LAUNCH.json: both launches are exactly W3-OBSERVER section 1's, from env -i with the declared five, the "
               "digest left for one final argument; cwd the parent; capture paths fresh siblings outside the attempt; "
               "the shell forms have the same words, none needing quotes", launch_rows)
    checks.add("K-33", all(launch_rows["record"].values()),
               "M0-LAUNCH.json: the expected starts equal the plan's commands, totals 1 and 1; the success outputs equal "
               "the fixed topology without the three failure files; no plan digest in the record; predictions fit; "
               "M0-ENVIRONMENT.json is the canonical declared environment", launch_rows["record"])

    out["elapsed_s"] = round(time.monotonic() - began, 3)
    out["boot_after"] = common.sysctl_text("kern.bootsessionuuid")
    out["checks"] = checks.rows
    out["summary"] = checks.summary()
    out["refused_process_events"] = list(common.REFUSED_EVENTS)
    digest = common.write_output(args.output, out, labels)
    print(labels(str({"summary": out["summary"], "plan_sha256": plan_binding["sha256"], "output_sha256": digest})))


if __name__ == "__main__":
    main()
