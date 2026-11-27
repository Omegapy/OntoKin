"""W2 of C271-P36 (gate MR, stage S4): author of observation plan 001 for M0 and M1 at commit B.

It loads the bound observer by its path (under -B, so no bytecode is written), takes every
value that the plan schema derives from the observer from the observer's own helpers, reads
the rest from the host, runs the observer's own static checks in this process, and writes
only absent files with exclusive creation. It starts no process: an audit hook refuses every
process-creation event of the runtime and every ctypes lookup of a process-creation function.

Subcommands (framework interpreter, -I -S -B):

  deps          the dependencies/0.2.0 inventory of the reader tree, written with write_new
  compare       this phase's inventories against MH's exact ones
  plan          build observation plan 001; --preview writes only its record, --write the plan
  observe-only  the loaded-module check that only observe makes, after the supervisor import
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import stat
import sys
import time

PROCESS_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn",
                            "os.fork", "os.forkpty", "pty.spawn", "os.startfile"))
LIBC_STARTS = re.compile(r"_?(fork|vfork|execv?[elp]*|posix_spawnp?|system|popen)")
REFUSED_EVENTS = []


def _audit(event, args):
    if event in PROCESS_EVENTS:
        REFUSED_EVENTS.append(event)
        raise RuntimeError("Process creation refused by the W2 audit hook: " + event)
    if event == "ctypes.dlsym" and len(args) > 1 and isinstance(args[1], str) and LIBC_STARTS.fullmatch(args[1]):
        REFUSED_EVENTS.append(event + ":" + args[1])
        raise RuntimeError("ctypes lookup of a process-creation function refused: " + args[1])


sys.addaudithook(_audit)

ATTEMPT_NAME = "observe-001"


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def load_observer(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("w2p_bound_observer_v02", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_record(path, value):
    raw = json.dumps(value, indent=1, sort_keys=True, ensure_ascii=True, default=repr).encode("ascii") + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    return {"path": path, "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def descriptor(ob, path, category="PLAN"):
    _, binding, _ = ob.read_file(path, ob.LIMITS["tree_file_bytes"], category=category)
    return ob._descriptor(path, binding)


def leaf_differences(old, new, path=""):
    rows = []
    if type(old) is dict and type(new) is dict:
        for key in sorted(set(old) | set(new)):
            where = path + "." + key if path else key
            if key not in new:
                rows.append({"path": where, "change": "removed"})
            elif key not in old:
                rows.append({"path": where, "change": "added", "new": new[key]})
            else:
                rows.extend(leaf_differences(old[key], new[key], where))
    elif type(old) is list and type(new) is list and len(old) == len(new):
        for index, (first, second) in enumerate(zip(old, new)):
            rows.extend(leaf_differences(first, second, path + "[" + str(index) + "]"))
    elif old != new:
        rows.append({"path": path, "change": "changed", "old": old, "new": new})
    return rows


def python_figures(inventory):
    figures = {}
    for tree in ("framework", "venv"):
        entries = inventory[tree]["entries"]
        files = [rel for rel, entry in entries.items() if entry["kind"] == "file"]
        figures[tree] = {"files": len(files),
                         "bytecode_files": sum(1 for rel in files if rel.endswith(".pyc")),
                         "pycache_directories": sum(1 for rel, entry in entries.items()
                                                    if entry["kind"] == "directory" and rel.split("/")[-1] == "__pycache__"),
                         "links": sum(1 for entry in entries.values() if entry["kind"] == "symlink"),
                         "directories": sum(1 for entry in entries.values() if entry["kind"] == "directory"),
                         "file_bytes": sum(entry["size_bytes"] for entry in entries.values() if entry["kind"] == "file")}
    closure = inventory["closure"]
    images = closure["images"]
    figures["closure"] = {"images": len(images), "external": len(closure["external"]), "links": len(closure["links"]),
                          "filetypes": {kind: sum(1 for row in images.values() if row["filetype"] == kind)
                                        for kind in sorted({row["filetype"] for row in images.values()})},
                          "rpath_entries": sum(len(row["rpaths"]) for row in images.values()),
                          "loader_path_references": sum(1 for row in images.values() for ref in row["references"]
                                                        if ref["raw"].startswith("@loader_path/")),
                          "system_references": sum(1 for row in images.values() for ref in row["references"]
                                                   if ref["kind"] == "system")}
    figures["selection_chain_hops"] = len(inventory["selection"]["launcher_chain"]["hops"])
    return figures


def mp_sums(paths):
    listed = {}
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                match = re.fullmatch(r"([0-9a-f]{64})\s+\*?(\S.*)", line.rstrip("\n"))
                if match:
                    listed.setdefault(os.path.basename(match[2]), set()).add(match[1])
    return listed


# ---------------------------------------------------------------------------
# deps
# ---------------------------------------------------------------------------

def run_deps(ob, args, record):
    root = ob.canonical_path(args.worktree)
    reader = ob.canonical_path(args.reader)
    historical = ob._historical_dependencies(root)
    entries = ob.tree_entries(reader, category="DEPENDENCY", refuse_ds_store=True, private=True, symlinks=False)
    files = {rel: ob._binding(entry) for rel, entry in entries.items() if entry["kind"] == "file"}
    directories = {rel: entry["mode"] for rel, entry in entries.items() if entry["kind"] == "directory"}
    plan_descriptor = descriptor(ob, args.reader_plan, "DEPENDENCY")
    reader_plan, _ = ob._document(plan_descriptor, ob.LIMITS["document_bytes"], "DEPENDENCY", canonical=False)
    archive = reader_plan["archive"]
    ob._binding_shape(archive, "DEPENDENCY", descriptor=True)
    rehash = ob._bound(archive["path"], archive, category="DEPENDENCY")
    necessary = {os.path.dirname(name) for name in files}
    necessary = {"/".join(name.split("/")[:index]) for name in necessary
                 for index in range(1, len(name.split("/")) + 1)} - {""}
    checks = {
        "paths_equal_c199_pins": set(files) == set(historical),
        "bytes_equal_c199_pins": all({"sha256": files[name]["sha256"], "size_bytes": files[name]["size_bytes"]}
                                     == historical[name] for name in historical if name in files),
        "directories_are_the_necessary_set": set(directories) == necessary,
        "archive_is_contract_pin": archive["sha256"] == ob.DEPENDENCY_ARCHIVE_SHA256,
        "archive_rehashed_equal": rehash == ob._binding(archive),
        "reader_plan_destination": reader_plan["destination"] == reader,
        "reader_plan_files": reader_plan["files"] == files,
        "reader_plan_directories": reader_plan["directories"] == directories,
        "reader_plan_root_mode": reader_plan["root_mode"] == ob._mode(os.lstat(reader)),
        "reader_plan_purpose": reader_plan["purpose"] == "retained-dependencies",
        "reader_plan_source_root": reader_plan["source_root"] == root,
        "files": len(files) == ob.DEPENDENCY_FILE_COUNT,
    }
    if not all(checks.values()):
        record["checks"] = checks
        raise RuntimeError("Dependency inventory checks failed: " + ", ".join(k for k, v in checks.items() if not v))
    inventory = {"schema": ob.DEPENDENCIES_SCHEMA, "files": files, "directories": directories, "archive": dict(archive)}
    record.update(checks=checks, reader_plan=plan_descriptor, archive=dict(archive),
                  files=len(files), directories=len(directories),
                  output=ob.write_new(args.output, inventory))


# ---------------------------------------------------------------------------
# compare
# ---------------------------------------------------------------------------

def _pair(ob, mine, theirs, category):
    raw_mine, raw_theirs = open(mine, "rb").read(), open(theirs, "rb").read()
    return (ob._loads(raw_mine, category), ob._loads(raw_theirs, category),
            {"mine": {"path": mine, "sha256": hashlib.sha256(raw_mine).hexdigest(), "size_bytes": len(raw_mine)},
             "mh": {"path": theirs, "sha256": hashlib.sha256(raw_theirs).hexdigest(), "size_bytes": len(raw_theirs)},
             "bytes_identical": raw_mine == raw_theirs})


def run_compare(ob, args, record):
    mine, mh, python = _pair(ob, args.mine_python, args.mh_python, "PYTHON")
    rows = ob.compare_inventory(mh, mine)
    python.update(compare_inventory_rows=rows, canonical_mine=ob._canonical(mine) == open(args.mine_python, "rb").read(),
                  figures_mine=python_figures(mine), figures_mh=python_figures(mh))
    for row in rows:
        if row["part"] in ("framework", "venv") and row["change"] == "changed":
            row["mh"] = mh[row["part"]]["entries"][row["path"]]
            row["mine"] = mine[row["part"]]["entries"][row["path"]]
    mine, mh, source = _pair(ob, args.mine_source, args.mh_source, "SOURCE")
    files_mine, files_mh = mine["files"], mh["files"]
    source.update(files_mine=len(files_mine), files_mh=len(files_mh),
                  bytes_mine=sum(row["size_bytes"] for row in files_mine.values()),
                  added=sorted(set(files_mine) - set(files_mh)), removed=sorted(set(files_mh) - set(files_mine)),
                  changed=[{"path": rel, "mh": files_mh[rel], "mine": files_mine[rel]} for rel in sorted(files_mine)
                           if rel in files_mh and files_mine[rel] != files_mh[rel]])
    mine, mh, deps = _pair(ob, args.mine_deps, args.mh_deps, "DEPENDENCY")
    deps["differences"] = leaf_differences(mh, mine)
    record.update(python=python, source=source, dependencies=deps)


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------

def build_plan(ob, args):
    root = ob.canonical_path(args.worktree)
    uname = os.uname()
    platform = {"system": uname.sysname, "release": uname.release, "machine": uname.machine,
                "proc_translated": ob.read_proc_translated(), "boot_session_uuid": ob.read_boot_session_uuid()}
    identity = ob.read_os_identity()
    system, cryptex = identity["system_version"], identity["cryptex"]
    os_plan = {"system_version": ob._descriptor(system["path"], system),
               "cryptex": ({"state": "present", "path": cryptex["path"], **ob._binding(cryptex)}
                           if cryptex["state"] == "present" else {"state": "absent", "path": cryptex["path"]})}
    framework = ob.canonical_path(args.framework)
    venv = ob.canonical_path(root + "/.venv")
    raw_cfg, _, _ = ob.read_file(venv + "/pyvenv.cfg", 65536, category="PYTHON", keep=True)
    cfg_version = ob._parse_pyvenv(raw_cfg)["version"]
    running = "%d.%d.%d" % sys.version_info[:3]
    if running != cfg_version or os.path.realpath(sys.base_prefix) != framework:
        raise RuntimeError("The authoring interpreter is not the planned framework interpreter")
    runtime_dir = ob.canonical_path(args.runtime)
    entries = ob.tree_entries(runtime_dir, category="RUNTIME", refuse_ds_store=True, private=True, symlinks=False)
    runtime = {"directory": runtime_dir, "version": ob.NODE_VERSION, "root_mode": ob._mode(os.lstat(runtime_dir)),
               "bin_mode": entries["bin"]["mode"], "executable": ob._binding(entries["bin/node"]),
               "node_source": ob._binding(entries[ob.NODE_SOURCE_NAME]), "archive": descriptor(ob, args.node_archive),
               "install": {"plan": descriptor(ob, args.node_plan), "result": descriptor(ob, args.node_result)}}
    dependencies = {"root": ob.canonical_path(args.reader), "inventory": descriptor(ob, args.deps_inventory),
                    "install": {"plan": descriptor(ob, args.reader_plan), "result": descriptor(ob, args.reader_result)}}
    parent = ob.canonical_path(args.evidence_parent)
    attempt = parent + "/" + ATTEMPT_NAME
    plan = {"schema": ob.PLAN_SCHEMA, "contract": ob.CONTRACT, "profile": ob.PROFILE, "executor": ob.EXECUTOR,
            "environment": dict(ob.ENVIRONMENT), "platform": platform, "os": os_plan,
            "source": {"root": root, "commit": args.commit, "tree": args.tree,
                       "inventory": descriptor(ob, args.source_inventory)},
            "observer": descriptor(ob, root + "/" + ob.ENTRY_POINT),
            "python": {"venv": venv, "framework": framework, "version": cfg_version,
                       "inventory": descriptor(ob, args.python_inventory)},
            "runtime": runtime, "dependencies": dependencies, "git": descriptor(ob, args.git, "GIT"),
            "evidence": {"parent": parent, "ancestors": ob._ancestors(parent), "attempt": attempt,
                         "outputs": ob.output_paths(attempt)},
            "failure_capture": {"procedure": descriptor(ob, args.failure_capture)}, "limits": dict(ob.LIMITS)}
    plan["commands"] = ob.expected_commands(plan)
    return plan, identity


def check_plan(ob, plan, args, record):
    check = ob._Deadline(ob.LIMITS["static_ms"])
    ob._resolved(plan)
    ob._plan_shape(plan, ob.Host())
    observer_path = plan["observer"]["path"]
    source = ob.check_source(plan, observer_path, check=check)
    runtime = ob.check_runtime(plan, check=check)
    dependencies = ob.check_dependencies(plan, check=check)
    git = ob.check_git_binding(plan["git"], check=check)
    ob._bound(plan["failure_capture"]["procedure"]["path"], plan["failure_capture"]["procedure"], category="PATH")
    expected, expected_raw = ob._document(plan["python"]["inventory"], 256 * 1024 * 1024, "PYTHON", check=check)
    actual = ob.python_inventory(plan["python"]["venv"], plan["python"]["framework"], check=check)
    differences = ob.compare_inventory(expected, actual)
    actual_raw = ob._canonical(actual)
    packages, records = ob.verify_packages(plan["python"]["venv"], actual["venv"]["entries"], source["pins"],
                                           actual["selection"]["version_directory"])
    ancestors_again = ob._ancestors(plan["evidence"]["parent"])
    parent_listing = sorted(os.listdir(plan["evidence"]["parent"]))
    git_bytes_kind = None
    _, _, head = ob.read_file(plan["git"]["path"], ob.LIMITS["tree_file_bytes"], category="GIT", prefix=4)
    git_bytes_kind = ob.macho_magic_kind(head)
    checks = {
        "resolved_and_plan_shape": True,
        "commands_equal_expected_commands": plan["commands"] == ob.expected_commands(plan),
        "outputs_equal_output_paths": plan["evidence"]["outputs"] == ob.output_paths(plan["evidence"]["attempt"]),
        "check_source": True, "source_head_is_commit": source["head"]["commit"] == plan["source"]["commit"],
        "check_runtime": True, "runtime_install_state": runtime["install"]["state"],
        "check_dependencies": True, "dependencies_install_state": dependencies["install"]["state"],
        "check_git_binding": True,
        "python_inventory_rows": len(differences),
        "python_inventory_canonical_bytes_equal": actual_raw == expected_raw,
        "python_inventory_digest": hashlib.sha256(actual_raw).hexdigest(),
        "verify_packages": packages,
        "attempt_absent": not os.path.lexists(plan["evidence"]["attempt"]),
        "evidence_parent_entries": parent_listing,
        "ancestors_equal_on_reread": ancestors_again == plan["evidence"]["ancestors"],
        "git_magic_kind": git_bytes_kind,
    }
    record["checks"] = checks
    record["observed"] = {
        "source_head": source["head"], "lock_pins": source["pins"],
        "runtime": {"macho": {key: runtime["macho"][key] for key in ("magic", "cputype", "cpusubtype", "filetype",
                                                                      "flags", "ncmds", "sizeofcmds")},
                    "command_names": [row["name"] for row in runtime["macho"]["commands"]],
                    "references": runtime["references"], "node_source_signature":
                        runtime["node_source"]["content"]["signature_check"],
                    "install": runtime["install"]},
        "dependencies": {"files": dependencies["files"], "install": dependencies["install"]},
        "git": git, "python_records": records}
    failed = [key for key in ("commands_equal_expected_commands", "outputs_equal_output_paths",
                              "source_head_is_commit", "python_inventory_canonical_bytes_equal", "attempt_absent",
                              "ancestors_equal_on_reread") if not checks[key]]
    if failed or differences or parent_listing:
        raise RuntimeError("Plan checks failed: " + ", ".join(failed) + (" python rows" if differences else "")
                           + (" evidence parent not empty" if parent_listing else ""))


def run_plan(ob, args, record):
    plan, identity = build_plan(ob, args)
    check_plan(ob, plan, args, record)
    raw = ob._canonical(plan)
    digest = hashlib.sha256(raw).hexdigest()
    record["plan_canonical"] = {"sha256": digest, "size_bytes": len(raw)}
    record["os_identity"] = identity
    record["platform"] = plan["platform"]
    if args.mp_sums:
        listed = mp_sums(args.mp_sums)
        record["mp_sums"] = {name: (plan_value["sha256"] in listed.get(os.path.basename(plan_value["path"]), set()))
                             for name, plan_value in (("node_plan", plan["runtime"]["install"]["plan"]),
                                                      ("node_result", plan["runtime"]["install"]["result"]),
                                                      ("reader_plan", plan["dependencies"]["install"]["plan"]),
                                                      ("reader_result", plan["dependencies"]["install"]["result"]))}
    if args.mh_plan:
        mh_raw = open(args.mh_plan, "rb").read()
        record["mh_plan"] = {"path": args.mh_plan, "sha256": hashlib.sha256(mh_raw).hexdigest(),
                             "size_bytes": len(mh_raw),
                             "differences": leaf_differences(ob._loads(mh_raw, "PLAN"), plan)}
    if args.preview:
        record["mode"] = "preview: nothing written apart from this record"
        return
    if args.expect_sha256 and args.expect_sha256 != digest:
        raise RuntimeError("The plan differs from the preview's digest; a fact changed between the two runs")
    path = ob.canonical_path(args.write, allow_absent=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        offset = 0
        while offset < len(raw):
            offset += os.write(fd, raw[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    validated = ob.validate_plan(path, digest)
    record["mode"] = "write"
    record["written"] = validated.descriptor
    record["validate_plan"] = "passed with the digest computed from the canonical bytes"


# ---------------------------------------------------------------------------
# observe-only
# ---------------------------------------------------------------------------

def run_observe_only(ob, args, record):
    root = ob.canonical_path(args.worktree)
    source, _ = ob._document(descriptor(ob, args.source_inventory), ob.LIMITS["document_bytes"], "SOURCE")
    python, _ = ob._document(descriptor(ob, args.python_inventory), 256 * 1024 * 1024, "PYTHON")
    caches = [root + "/prototypes/__pycache__", root + "/prototypes/static_tray_v01/__pycache__"]
    before = set(sys.modules)
    module = ob.load_darwin_supervisor(root, source)
    rows = ob.loaded_module_files()
    excluded = [row for row in rows if row["name"] == "__main__"]
    ob.check_loaded_modules([row for row in rows if row["name"] != "__main__"], python, root, source["files"])
    record.update(
        supervisor_module=module.__name__, run_process_file=module.run_process.__code__.co_filename,
        modules_added_by_import=sorted(set(sys.modules) - before),
        excluded_rows=excluded, checked_rows=len(rows) - len(excluded),
        bytecode_directories_after=[path for path in caches if os.path.lexists(path)],
        check_loaded_modules="passed for every loaded module apart from this script's __main__")


def main(argv=None):
    if not (sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode):
        raise SystemExit("Run under -I -S -B")
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("command", choices=("deps", "compare", "plan", "observe-only"))
    parser.add_argument("--observer", required=True)
    parser.add_argument("--record", required=True)
    for name in ("worktree", "reader", "reader-plan", "reader-result", "output", "mine-python", "mh-python",
                 "mine-source", "mh-source", "mine-deps", "mh-deps", "commit", "tree", "framework", "source-inventory",
                 "python-inventory", "deps-inventory", "runtime", "node-archive", "node-plan", "node-result", "git",
                 "evidence-parent", "failure-capture", "write", "expect-sha256", "mh-plan"):
        parser.add_argument("--" + name)
    parser.add_argument("--mp-sums", action="append", default=[])
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)
    record_fd_path = args.record
    if os.path.lexists(record_fd_path):
        raise SystemExit("The record path exists")
    began, clock = _utc(), time.monotonic()
    ob = load_observer(args.observer)
    record = {"schema": "ontokin.c271.p36-w2-author/1", "command": args.command, "pid": os.getpid(),
              "started_at_utc": began, "script": os.path.realpath(__file__),
              "script_sha256": _sha256_file(os.path.realpath(__file__)),
              "interpreter": {"executable": sys.executable, "version": sys.version, "flags": {
                  "isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                  "dont_write_bytecode": sys.flags.dont_write_bytecode, "safe_path": sys.flags.safe_path},
                  "base_prefix": sys.base_prefix},
              "observer": {"path": args.observer, "sha256": _sha256_file(args.observer)},
              "boot_before": ob.read_boot_session_uuid(), "argv": sys.argv[1:]}
    status = 0
    try:
        {"deps": run_deps, "compare": run_compare, "plan": run_plan, "observe-only": run_observe_only}[args.command](
            ob, args, record)
        record["outcome"] = "passed"
    except Exception as exc:  # recorded, then reported
        status = 1
        record["outcome"] = "failed"
        record["failure"] = {"type": type(exc).__name__, "reason": str(exc),
                             "details": getattr(exc, "details", None), "code": getattr(exc, "code", None)}
    record["boot_after"] = ob.read_boot_session_uuid()
    record["finished_at_utc"] = _utc()
    record["elapsed_s"] = round(time.monotonic() - clock, 3)
    record["refused_process_events"] = list(REFUSED_EVENTS)
    written = write_record(args.record, record)
    summary = {"command": args.command, "outcome": record["outcome"], "record": written,
               "boot_before": record["boot_before"], "boot_after": record["boot_after"]}
    for key in ("plan_canonical", "written", "output", "failure"):
        if key in record:
            summary[key] = record[key]
    sys.stdout.write(json.dumps(summary, sort_keys=True) + "\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
