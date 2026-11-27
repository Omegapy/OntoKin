"""W2 (freeze 001): the configuration against the provider's own read-only checks, in this process, starting nothing.

Usage (from env -i with the declared five, so that the HOST checks see what R1's unit process will be):
  <worktree>/.venv/bin/python -I -S -B w2f_validate.py WORKTREE CONFIG CONFIG_SHA256 OUTPUT

It loads the provider of commit B from WORKTREE and runs, on the configuration, the parts of _selection that
read files only: the digest and the closed schema, the contract and amendment-adoption bindings, the evidence
root's path form, HOST's Git binding (by bytes), _verify_host (state, environment record, Python inventory
recomputed and compared, runtime with its receipt, Git, both inspection receipts, labels, starts and claims),
the source inventory with every bound file, _cross_bindings, _verify_dependencies and _verify_methods.

Not run, because each starts Git or needs the driver's workspace: _verify_source's Git reads (rev-parse,
status, ls-files), derive_workspace_binding and the cohort's manifest. tools.check_local.git_read is replaced
by a sentinel that raises; the record shows that _verify_source reached it after every file binding passed.

An audit hook refuses every process creation and every open() for writing other than OUTPUT. It writes only
OUTPUT (absent).
"""
import sys

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
import json
import os
from pathlib import Path

worktree, config_path, config_sha256, output = sys.argv[1:5]
if os.path.lexists(output):
    sys.stderr.write("refused: output exists\n")
    raise SystemExit(2)
PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system",
                  "os.startfile"}
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
events = []


def hook(event, args):
    if event in PROCESS_EVENTS:
        events.append({"event": event, "refused": True})
        raise PermissionError("author validation starts no process: " + event)
    if event == "open" and len(args) >= 3:
        path, mode, flags = args[0], args[1], args[2]
        if isinstance(path, int):  # os.fdopen of a descriptor whose own open was checked here
            return
        writes = (isinstance(flags, int) and flags & WRITE_FLAGS) or (isinstance(mode, str) and any(c in mode for c in "wax+"))
        if writes and os.fspath(path) != output:
            events.append({"event": "open-for-write", "path": str(path), "refused": True})
            raise PermissionError("author validation writes nothing but its output")


sys.addaudithook(hook)
sys.path.insert(0, worktree)
from prototypes.static_tray_v01 import current_host_readback_v02 as v02  # noqa: E402
from prototypes.static_tray_v01 import current_host_observation_v02 as observation  # noqa: E402
from tools import check_local  # noqa: E402

rows = []


def step(name, function):
    try:
        value = function()
        rows.append({"check": name, "passed": True})
        return value
    except Exception as exc:  # recorded, never repaired
        rows.append({"check": name, "passed": False, "error": type(exc).__name__,
                     "reason": getattr(exc, "reason", str(exc)), "code": getattr(exc, "code", None)})
        return None


class GitNotStarted(OSError):
    pass


requested_git = []


def sentinel_git_read(root, *args, timeout=10):
    requested_git.append([str(root), *args])
    raise GitNotStarted("author validation: the provider's Git read is not started here")


root = Path(worktree)
path = Path(config_path)
config, actual = step("read config, digest", lambda: v02._read(path, 1024 * 1024, category="SELECTION")) or (None, None)
step("digest equals the supplied one", lambda: v02._require(actual["sha256"] == config_sha256, "SELECTION", "digest"))
step("closed config/0.2.0 schema", lambda: v02._schema(config, "config", v02.CONFIG_KEYS))
step("contract", lambda: v02._require(config["contract"] == v02.CONTRACT, "SCHEMA", "contract"))
step("source keys and root", lambda: (v02._keys(config["source"], ("root", "commit", "tree", "inventory")),
                                       v02._require(config["source"]["root"] == str(root), "SOURCE", "root")))
step("configuration outside the source", lambda: v02._require(not path.is_relative_to(root), "SELECTION", "inside"))
step("contract source bound", lambda: (v02._binding_shape(config["contract_source"], descriptor=True),
                                        v02._require(config["contract_source"]["path"] == str(root / v02.CONTRACT_PATH), "SOURCE", "path"),
                                        v02._bound(root / v02.CONTRACT_PATH, v02._plain(config["contract_source"]), category="SOURCE")))
step("amendment adoption bound", lambda: (v02._binding_shape(config["amendment_adoption"], descriptor=True),
                                           v02._require(config["amendment_adoption"]["path"] == str(root / v02.AMENDMENT_ADOPTION_PATH), "SOURCE", "path"),
                                           v02._bound(root / v02.AMENDMENT_ADOPTION_PATH, v02._plain(config["amendment_adoption"]), category="SOURCE")))
evidence = step("evidence root path form (absolute, normalized, no linked component)",
                lambda: v02._absolute(config["evidence_root"], category="EVIDENCE"))
evidence_state = {"exists_now": bool(evidence and evidence.exists()), "is_dir_now": bool(evidence and evidence.is_dir()),
                  "outside_source": bool(evidence and not evidence.is_relative_to(root))}
step("parent is null (an original selection)", lambda: v02._verify_parent(config))
git = step("HOST's Git binding, by bytes (no Git start)", lambda: v02._host_git(config))
original_git_read = check_local.git_read
check_local.git_read = sentinel_git_read
source_outcome = {}
try:
    v02._verify_source(config["source"], git=git, derived=False, own_root=True)
    source_outcome = {"reached_git_reads": False}
except v02.CurrentHostBindingError as exc:
    cause = exc.cause or {}
    source_outcome = {"code": exc.code, "reason": exc.reason, "cause": cause,
                      "stopped_at_the_git_sentinel": exc.reason == "Bounded source Git inspection failed"
                      and cause.get("type") == "GitNotStarted"}
finally:
    check_local.git_read = original_git_read
rows.append({"check": "_verify_source up to its first Git read (bind_git by bytes, the source inventory, every file binding)",
             "passed": bool(source_outcome.get("stopped_at_the_git_sentinel")), "outcome": source_outcome,
             "git_reads_not_started": requested_git})
bound = check_local._GIT_STATE
host = step("_verify_host (state, environment, Python inventory, runtime, Git, inspections, labels, starts, claims)",
            lambda: v02._verify_host(config))
inventory = step("source inventory document", lambda: v02._document(config["source"]["inventory"], 16 * 1024 * 1024, category="SOURCE"))
step("_cross_bindings", lambda: v02._cross_bindings(config, host, inventory))
dependencies = step("_verify_dependencies", lambda: v02._verify_dependencies(config))
methods = step("_verify_methods (bodies, discovery, baseline map)", lambda: v02._verify_methods(config))
discovery = step("discovery document", lambda: v02._document(methods["discovery"], 8 * 1024 * 1024, category="SOURCE"))
summary = {"method_ids": len(discovery["method_ids"]) if discovery else None,
           "contains_the_seven": bool(discovery) and all(item in discovery["method_ids"] for item in v02.METHOD_IDS),
           "labels": v02._labels(host) if host else None,
           "git_state_after_binding": bound}
document = {"schema": "ontokin.c271.p36-w2-freeze-config-validation/1", "config": {"path": str(path), "sha256": config_sha256},
            "interpreter": {"executable": sys.executable, "version": sys.version, "flags": {
                "dont_write_bytecode": sys.flags.dont_write_bytecode, "isolated": sys.flags.isolated, "no_site": sys.flags.no_site}},
            "checks": rows, "evidence_root": evidence_state, "summary": summary, "audit_events": events,
            "all_passed": all(row["passed"] for row in rows) and not events,
            "not_run": ["_verify_source's Git reads (rev-parse --show-toplevel, rev-parse HEAD^{commit}, rev-parse <B>^{tree}, "
                        "status --porcelain=v1 --untracked-files=no, ls-files --others --exclude-standard -z)",
                        "derive_workspace_binding and the derived selection (need the driver's workspace)",
                        "setup_cpu_cohort, the manifest, jobs and every start"]}
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    stream.write(json.dumps(document, indent=1, sort_keys=True, default=str) + "\n")
print(json.dumps({"all_passed": document["all_passed"], "failed": [row["check"] for row in rows if not row["passed"]],
                  "events": len(events), "evidence_root": evidence_state, "method_ids": summary["method_ids"]}))
