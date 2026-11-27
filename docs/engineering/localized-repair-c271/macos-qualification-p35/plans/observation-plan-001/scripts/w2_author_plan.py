"""W2, observation plan 001 (gate MH, C271-P35): author the dependency inventory and the plan.

The observer is loaded by its path (``-I`` puts no script directory on sys.path)
and its own helpers produce every value that the plan schema derives from them:
canonical_path, read_file, read_os_identity, read_boot_session_uuid,
read_proc_translated, git_head, source_inventory, python_inventory,
tree_entries, _historical_dependencies, _ancestors, output_paths,
expected_commands, LIMITS, ENVIRONMENT and write_new. The observer's own static
checks then run on the plan in this process: _resolved, _plan_shape,
check_source, check_runtime, check_git_binding, the Python inventory comparison
and verify_packages, and, once the dependency inventory exists,
check_dependencies; after the plan is written, validate_plan. What this
process cannot check for the observer (its launcher, its environment and its
loaded modules) is left to the observer's `static` command.

No process is created: an audit hook refuses every process-creation event.
`preview` writes nothing and prints its facts. `write` creates, each exclusively
and only if absent: the dependency inventory, the plan and the facts record.
In `preview`, the dependency inventory does not exist yet, so _plan_shape runs
on a copy whose inventory path names the existing source inventory (only that
rule's path check is affected), and check_dependencies is not run.

Launch: <worktree>/.venv/bin/python -I -S -B w2_author_plan.py MODE --args...
Exit: 0 when every check holds, 1 when a check fails, 2 on a refusal.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import posixpath
import stat
import sys
import time

REFUSED_EVENTS = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork",
                            "os.forkpty", "os.startfile", "pty.spawn"))
EVENTS = []


def _hook(event, args):
    if event in REFUSED_EVENTS:
        EVENTS.append(event)
        raise RuntimeError("process creation refused by the W2 audit hook: " + event)


sys.addaudithook(_hook)


class CheckFailed(Exception):
    pass


CHECKS = []


def check(name, condition, **detail):
    CHECKS.append({"check": name, "passed": bool(condition), **({"detail": detail} if detail else {})})
    if not condition:
        raise CheckFailed(name + ": " + json.dumps(detail, sort_keys=True, default=str))


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_observer(path):
    spec = importlib.util.spec_from_file_location("current_host_observation_v02", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sums(path):
    rows = {}
    with open(path, "r", encoding="ascii") as handle:
        for line in handle:
            if line.strip():
                digest, name = line.rstrip("\n").split("  ", 1)
                rows[name] = digest
    return rows


def current_umask():
    value = os.umask(0o022)
    os.umask(value)
    return value


ARGUMENTS = ("worktree", "framework", "runtime-plan", "runtime-result", "reader-plan", "reader-result", "git",
             "evidence-parent", "attempt", "source-inventory", "python-inventory", "dependencies-inventory", "plan",
             "facts", "commit", "tree", "expect-python-inventory-sha256", "expect-git-sha256", "expect-git-size",
             "mp-outcome", "mp-plan-sums", "mp-receipt-sums", "local-plan-sums", "tooling-sums", "failure-capture")


def main(argv):
    parser = argparse.ArgumentParser(prog="w2_author_plan")
    parser.add_argument("mode", choices=("preview", "write"))
    for name in ARGUMENTS:
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    started = time.time()
    if not (sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.flags.dont_write_bytecode == 1):
        sys.stderr.write("refused: run under -I -S -B\n")
        return 2
    for path in (args.dependencies_inventory, args.plan, args.facts):
        if os.path.lexists(path):
            sys.stderr.write("refused: an output exists: " + path + "\n")
            return 2
    facts = {"schema": "ontokin.c271.p35-w2-plan-author-facts/1", "mode": args.mode, "started_at_utc": utc()}
    passed = False
    try:
        obs, plan, dependency_inventory, extra = build(args)
        facts.update(extra)
        if args.mode == "write":
            written = obs.write_new(args.dependencies_inventory, dependency_inventory)
            check("dependency inventory written with the planned descriptor",
                  written == plan["dependencies"]["inventory"], written=written)
            facts["dependency_inventory_descriptor"] = written
            prechecks(obs, plan, args, facts, shape_plan=plan)
            deps = obs.check_dependencies(plan)
            check("check_dependencies accepts the plan", deps["files"] == 24 and deps["install"]["state"]
                  == "INSTALLED_EXACT", files=deps["files"])
            facts["check_dependencies"] = {"files": deps["files"], "install_state": deps["install"]["state"]}
            descriptor = obs.write_new(args.plan, plan)
            validated = obs.validate_plan(args.plan, descriptor["sha256"])
            check("validate_plan accepts the written plan with its digest",
                  validated.descriptor == descriptor and validated.plan == plan, descriptor=descriptor)
            facts["plan_descriptor"] = descriptor
        else:
            shape_plan = copy.deepcopy(plan)
            shape_plan["dependencies"]["inventory"]["path"] = args.source_inventory
            prechecks(obs, plan, args, facts, shape_plan=shape_plan)
            facts["plan_preview"] = plan
            facts["plan_preview_canonical_sha256"] = hashlib.sha256(obs._canonical(plan)).hexdigest()
        end_boot = obs.read_boot_session_uuid()
        facts["boot_session_uuid_at_end"] = end_boot
        check("the boot did not change during authoring", end_boot == plan["platform"]["boot_session_uuid"])
        passed = True
    except CheckFailed as exc:
        facts["failure"] = str(exc)
    except Exception as exc:  # an observer refusal or an unexpected error is recorded, never hidden
        facts["failure"] = exc.as_dict() if hasattr(exc, "as_dict") else {"type": type(exc).__name__,
                                                                          "reason": str(exc)}
    facts.update(checks=CHECKS, passed=passed, refused_process_events=EVENTS, finished_at_utc=utc(),
                 elapsed_s=round(time.time() - started, 3),
                 process={"pid": os.getpid(), "argv": sys.argv, "orig_argv": getattr(sys, "orig_argv", None),
                          "executable": sys.executable, "cwd": os.getcwd(),
                          "flags": {"isolated": sys.flags.isolated, "no_site": sys.flags.no_site,
                                    "dont_write_bytecode": sys.flags.dont_write_bytecode},
                          "script_sha256": hashlib.sha256(open(os.path.realpath(__file__), "rb").read()).hexdigest()})
    data = (json.dumps(facts, sort_keys=True, indent=1, ensure_ascii=True, default=str) + "\n").encode("ascii")
    if args.mode == "write":
        fd = os.open(args.facts, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        sys.stdout.write(json.dumps({"facts": args.facts, "facts_sha256": hashlib.sha256(data).hexdigest(),
                                     "passed": passed, "plan": facts.get("plan_descriptor"),
                                     "dependency_inventory": facts.get("dependency_inventory_descriptor"),
                                     "failure": facts.get("failure")}, sort_keys=True) + "\n")
    else:
        sys.stdout.write(data.decode("ascii"))
    return 0 if passed else 1


def prechecks(obs, plan, args, facts, *, shape_plan):
    obs._resolved(plan)
    obs._plan_shape(shape_plan, obs.Host())
    check("plan rules (_resolved and _plan_shape) accept the plan", True,
          shape_plan_substituted=shape_plan is not plan)
    observer_path = plan["observer"]["path"]
    source = obs.check_source(plan, observer_path)
    check("check_source accepts the plan", source["head"]["commit"] == args.commit
          and source["pins"] == dict(obs.PYTHON_PINS))
    runtime = obs.check_runtime(plan)
    check("check_runtime accepts the plan", runtime["install"]["state"] == "INSTALLED_EXACT"
          and runtime["binding"] == plan["runtime"]["executable"])
    facts["runtime_macho"] = {key: runtime["macho"][key] for key in ("magic", "cputype", "cpusubtype", "filetype",
                                                                      "flags", "ncmds", "sizeofcmds")}
    facts["runtime_references"] = runtime["references"]
    facts["runtime_signature_check"] = runtime["node_source"]["content"]["signature_check"]
    facts["runtime_install"] = {key: runtime["install"][key] for key in ("purpose", "state")}
    check("check_git_binding accepts the plan's Git", obs.check_git_binding(plan["git"]) == plan["git"])
    check("expected_commands equals the plan's commands", plan["commands"] == obs.expected_commands(plan))
    check("output_paths equals the plan's outputs", plan["evidence"]["outputs"]
          == obs.output_paths(plan["evidence"]["attempt"]))
    check("the evidence ancestors are the observer's reading", obs._ancestors(plan["evidence"]["parent"])
          == plan["evidence"]["ancestors"])
    check("the attempt is still absent", not os.path.lexists(plan["evidence"]["attempt"]))


def build(args):
    root = args.worktree
    observer_path = root + "/prototypes/static_tray_v01/current_host_observation_v02.py"
    obs = load_observer(observer_path)
    extra = {}
    check("observer entry point constant", obs.ENTRY_POINT == "prototypes/static_tray_v01/current_host_observation_v02.py")
    rf = obs.read_file

    def binding(path, maximum=obs.LIMITS["tree_file_bytes"], private=False):
        return rf(path, maximum, category="W2", private=private)[1]

    def descriptor(path, maximum=obs.LIMITS["tree_file_bytes"], private=False):
        check("canonical path " + path, obs.canonical_path(path) == path)
        return {"path": path, **binding(path, maximum, private)}

    # Platform and boot (P07 section 2: the actual release and boot).
    uname = os.uname()
    platform = {"system": uname.sysname, "release": uname.release, "machine": uname.machine,
                "proc_translated": obs.read_proc_translated(), "boot_session_uuid": obs.read_boot_session_uuid()}
    check("platform native Darwin arm64", platform["system"] == "Darwin" and platform["machine"] == "arm64"
          and platform["proc_translated"] == 0, platform=platform)
    extra["uname_version"] = uname.version

    # OS identity: the system file and the cryptex copy, by the observer's own reader.
    identity = obs.read_os_identity()
    system, cryptex = identity["system_version"], identity["cryptex"]
    check("system SystemVersion.plist path", system["path"] == obs.SYSTEM_VERSION_PATH)
    os_plan = {"system_version": {key: system[key] for key in ("path", "sha256", "size_bytes", "mode")}}
    if cryptex["state"] == "present":
        os_plan["cryptex"] = {key: cryptex[key] for key in ("state", "path", "sha256", "size_bytes", "mode")}
        check("cryptex copy path is canonical", obs.canonical_path(cryptex["path"]) == cryptex["path"])
    else:
        os_plan["cryptex"] = {"state": "absent", "path": cryptex["path"]}
    extra["os_identity"] = identity

    # Source: root, commit and tree, and the source inventory written by the observer's command.
    check("worktree root is canonical", obs.canonical_path(root) == root)
    head = obs.git_head(root)
    check("HEAD is the planned commit (observer's static reader)", head["commit"] == args.commit, head=head)
    extra["git_head"] = head
    source_raw = open(args.source_inventory, "rb").read()
    source_doc = obs._decode(source_raw, "W2")
    check("source inventory schema", source_doc.get("schema") == obs.SOURCE_SCHEMA)
    recomputed = obs.source_inventory(root)
    check("source inventory equals a fresh computation", recomputed == source_doc, files=len(recomputed["files"]))
    source_descriptor = descriptor(args.source_inventory)
    check("source inventory descriptor equals its bytes",
          source_descriptor["sha256"] == hashlib.sha256(source_raw).hexdigest())
    observer_descriptor = descriptor(observer_path)
    check("observer bound by the source inventory", source_doc["files"][obs.ENTRY_POINT]
          == {key: observer_descriptor[key] for key in ("sha256", "size_bytes", "mode")})
    extra["source_inventory_figures"] = {"files": len(source_doc["files"]),
                                         "bytes": sum(row["size_bytes"] for row in source_doc["files"].values())}

    # Python: the venv, the canonical framework, the version and the frozen inventory.
    venv = root + "/.venv"
    framework = obs.canonical_path(args.framework)
    check("framework path is canonical", framework == args.framework)
    version = "%d.%d.%d" % sys.version_info[:3]
    cfg = obs._parse_pyvenv(open(venv + "/pyvenv.cfg", "rb").read())
    check("pyvenv.cfg version equals this interpreter's", cfg.get("version") == version, cfg_version=cfg.get("version"))
    check("framework version directory", posixpath.basename(framework) == "3.12" and version.startswith("3.12."))
    python_raw = open(args.python_inventory, "rb").read()
    python_doc = obs._decode(python_raw, "W2")
    python_descriptor = descriptor(args.python_inventory, maximum=256 * 1024 * 1024)
    check("Python inventory digest equals MP's after-snapshot and N34-M's",
          python_descriptor["sha256"] == args.expect_python_inventory_sha256, actual=python_descriptor["sha256"])
    fresh = obs.python_inventory(venv, framework)
    differences = obs.compare_inventory(python_doc, fresh)
    check("a fresh Python inventory equals the frozen one", not differences and obs._canonical(fresh) == python_raw,
          differences=differences[:20])
    pins = obs.read_lock_pins(open(root + "/" + obs.MACOS_LOCK, "rb").read())
    packages, records = obs.verify_packages(venv, fresh["venv"]["entries"], pins, fresh["selection"]["version_directory"])
    check("the seven pinned packages verify", packages == dict(obs.PYTHON_PINS), packages=packages)
    count = {}
    for tree in ("framework", "venv"):
        rows = python_doc[tree]["entries"]
        count[tree] = {kind: sum(1 for row in rows.values() if row["kind"] == kind)
                       for kind in ("file", "symlink", "directory")}
        count[tree]["bytecode"] = sum(1 for rel, row in rows.items() if row["kind"] == "file" and rel.endswith(".pyc"))
        count[tree]["file_bytes"] = sum(row["size_bytes"] for row in rows.values() if row["kind"] == "file")
    closure = python_doc["closure"]
    extra["python_inventory_figures"] = {
        "trees": count, "images": len(closure.get("images", {})), "external": len(closure.get("external", {})),
        "closure_links": len(closure.get("links", [])), "canonical_bytes": len(python_raw),
        "selection_hops": len(python_doc["selection"]["launcher_chain"]["hops"]),
        "records": {name: {k: v for k, v in row.items() if k != "record"} for name, row in records.items()}}
    python = {"venv": venv, "framework": framework, "version": version, "inventory": python_descriptor}

    # Runtime: the prepared Node tree, its archive, and MP's exact apply plan and receipt.
    node_plan = json.loads(open(args.runtime_plan, "rb").read())
    directory = node_plan["destination"]
    check("runtime directory is canonical", obs.canonical_path(directory) == directory, directory=directory)
    tree = obs.tree_entries(directory, category="W2", refuse_ds_store=True, private=True, symlinks=False,
                            file_maximum=256 * 1024 * 1024)
    check("runtime layout is exactly bin/, bin/node, NODE-SOURCE.json",
          {rel: row["kind"] for rel, row in tree.items()} == dict(obs.RUNTIME_LAYOUT), entries=sorted(tree))
    root_mode = obs._mode(os.lstat(directory))
    executable = obs._binding(tree["bin/node"])
    node_source = obs._binding(tree[obs.NODE_SOURCE_NAME])
    archive = dict(node_plan["archive"])
    check("Node archive descriptor equals its file and the pin", binding(archive["path"], 64 * 1024 * 1024)
          == obs._binding(archive) and archive["sha256"] == obs.NODE_ARCHIVE_SHA256, archive=archive)
    check("Node archive is retained with mode 0o444", archive["mode"] == "0o444")
    check("Node install plan names this tree", node_plan["root_mode"] == root_mode
          and node_plan["directories"] == {"bin": tree["bin"]["mode"]}
          and node_plan["files"] == {"bin/node": executable, obs.NODE_SOURCE_NAME: node_source}
          and node_plan["source_root"] == root and node_plan["report"] == args.runtime_result
          and node_plan["purpose"] == "selected-node")
    outcome = json.load(open(args.mp_outcome))["prepared"]
    check("bin/node and NODE-SOURCE.json equal MP's outcome record", executable == outcome["node_runtime"]["bin_node"]
          and node_source["sha256"] == outcome["node_runtime"]["node_source_sha256"])
    node_result = json.load(open(args.runtime_result))
    check("Node receipt is INSTALLED_EXACT with passed true", node_result.get("state") == "INSTALLED_EXACT"
          and node_result.get("passed") is True)
    runtime = {"directory": directory, "version": obs.NODE_VERSION, "root_mode": root_mode,
               "bin_mode": tree["bin"]["mode"], "executable": executable, "node_source": node_source,
               "archive": archive,
               "install": {"plan": descriptor(args.runtime_plan, 64 * 1024 * 1024),
                           "result": descriptor(args.runtime_result, 64 * 1024 * 1024)}}

    # Dependencies: the 24-file reader tree, its inventory document, and MP's plan and receipt.
    reader_plan = json.loads(open(args.reader_plan, "rb").read())
    deps_root = reader_plan["destination"]
    check("reader tree root is canonical", obs.canonical_path(deps_root) == deps_root, root=deps_root)
    deps_tree = obs.tree_entries(deps_root, category="W2", refuse_ds_store=True, private=True, symlinks=False)
    deps_files = {rel: obs._binding(row) for rel, row in deps_tree.items() if row["kind"] == "file"}
    deps_dirs = {rel: row["mode"] for rel, row in deps_tree.items() if row["kind"] == "directory"}
    historical = obs._historical_dependencies(root)
    check("the 24 reader files equal their C199 pins", set(deps_files) == set(historical) and all(
        {"sha256": deps_files[name]["sha256"], "size_bytes": deps_files[name]["size_bytes"]} == row
        for name, row in historical.items()), files=len(deps_files))
    necessary = {posixpath.dirname(name) for name in deps_files}
    necessary = {"/".join(name.split("/")[:index]) for name in necessary
                 for index in range(1, len(name.split("/")) + 1)} - {""}
    check("reader directories are exactly the necessary ones", set(deps_dirs) == necessary, directories=len(deps_dirs))
    deps_archive = dict(reader_plan["archive"])
    check("C195 archive path is canonical", obs.canonical_path(deps_archive["path"]) == deps_archive["path"],
          path=deps_archive["path"])
    check("C195 archive descriptor equals its file and the pin", binding(deps_archive["path"], 64 * 1024 * 1024)
          == obs._binding(deps_archive) and deps_archive["sha256"] == obs.DEPENDENCY_ARCHIVE_SHA256,
          archive=deps_archive)
    check("reader install plan names this tree", reader_plan["files"] == deps_files
          and reader_plan["directories"] == deps_dirs and reader_plan["root_mode"] == obs._mode(os.lstat(deps_root))
          and reader_plan["source_root"] == root and reader_plan["report"] == args.reader_result
          and reader_plan["purpose"] == "retained-dependencies" and reader_plan["node_source"] is None)
    check("reader tree figures equal MP's outcome record", len(deps_files) == outcome["reader_tree"]["files"]
          and len(deps_dirs) == outcome["reader_tree"]["directories"])
    reader_result = json.load(open(args.reader_result))
    check("reader receipt is INSTALLED_EXACT with passed true", reader_result.get("state") == "INSTALLED_EXACT"
          and reader_result.get("passed") is True)
    dependency_inventory = {"schema": obs.DEPENDENCIES_SCHEMA, "files": deps_files, "directories": deps_dirs,
                            "archive": deps_archive}
    inventory_raw = obs._canonical(dependency_inventory)
    check("dependency inventory path is canonical and absent", not os.path.lexists(args.dependencies_inventory)
          and obs.canonical_path(args.dependencies_inventory, allow_absent=True) == args.dependencies_inventory)
    dependencies = {"root": deps_root,
                    "inventory": {"path": args.dependencies_inventory,
                                  "sha256": hashlib.sha256(inventory_raw).hexdigest(),
                                  "size_bytes": len(inventory_raw), "mode": "0o%03o" % (0o644 & ~current_umask())},
                    "install": {"plan": descriptor(args.reader_plan, 64 * 1024 * 1024),
                                "result": descriptor(args.reader_result, 64 * 1024 * 1024)}}

    # MP's recorded digests of the exact plans and receipts.
    mp_plans, mp_receipts, local_plans = sums(args.mp_plan_sums), sums(args.mp_receipt_sums), sums(args.local_plan_sums)
    for path, recorded in ((args.runtime_plan, mp_plans), (args.reader_plan, mp_plans),
                           (args.runtime_plan, local_plans), (args.reader_plan, local_plans),
                           (args.runtime_result, mp_receipts), (args.reader_result, mp_receipts)):
        name = posixpath.basename(path)
        check("recorded digest of " + name, recorded.get(name) == binding(path, 64 * 1024 * 1024)["sha256"],
              recorded=recorded.get(name))

    # Git: the developer tools' Git that N34-M read, never the dispatcher.
    git_binding = binding(args.git, 64 * 1024 * 1024)
    check("Git equals the file N34-M read", git_binding["sha256"] == args.expect_git_sha256
          and git_binding["size_bytes"] == int(args.expect_git_size), actual=git_binding)
    check("Git path is not a link and is canonical", not os.path.islink(args.git)
          and obs.canonical_path(args.git) == args.git)
    git = {"path": args.git, **git_binding}
    extra["git_magic_kind"] = obs.macho_magic_kind(rf(args.git, 64 * 1024 * 1024, category="W2", prefix=4)[2])

    # Evidence: the existing empty parent, its ancestors, the absent attempt and the fixed outputs.
    parent = obs.canonical_path(args.evidence_parent)
    check("evidence parent is canonical, a directory and empty", parent == args.evidence_parent
          and stat.S_ISDIR(os.lstat(parent).st_mode) and os.listdir(parent) == [])
    attempt = args.attempt
    check("attempt is an absent direct child of the parent", posixpath.dirname(attempt) == parent
          and not os.path.lexists(attempt) and obs.canonical_path(attempt, allow_absent=True) == attempt)
    evidence = {"parent": parent, "ancestors": obs._ancestors(parent), "attempt": attempt,
                "outputs": obs.output_paths(attempt)}

    # Failure capture: the reviewed procedure at commit C.
    procedure = descriptor(args.failure_capture)
    check("FAILURE-CAPTURE.md equals the reviewed tooling digest",
          sums(args.tooling_sums).get("FAILURE-CAPTURE.md") == procedure["sha256"])

    plan = {"schema": obs.PLAN_SCHEMA, "contract": obs.CONTRACT, "profile": obs.PROFILE, "executor": obs.EXECUTOR,
            "environment": dict(obs.ENVIRONMENT), "platform": platform, "os": os_plan,
            "source": {"root": root, "commit": args.commit, "tree": args.tree, "inventory": source_descriptor},
            "observer": observer_descriptor, "python": python, "runtime": runtime, "dependencies": dependencies,
            "git": git, "commands": [], "evidence": evidence, "failure_capture": {"procedure": procedure},
            "limits": dict(obs.LIMITS)}
    plan["commands"] = obs.expected_commands(plan)
    extra["dependency_inventory_planned"] = dict(dependencies["inventory"])
    extra["umask"] = "0o%03o" % current_umask()
    return obs, plan, dependency_inventory, extra


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
