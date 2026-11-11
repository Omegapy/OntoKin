"""C209 exact readback entry bindings; no Node launcher or import interceptor.

The independently sealed input graph is declarative evidence. This component
checks its named relationships and actual files, not the completeness of parsed
JavaScript imports or the behavior of a future Node loader.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
import os
from pathlib import Path, PurePosixPath
import posixpath

from . import input_lock, readback_binding as rb, transaction as tx
from .schedule import canonical


JOB_SCHEMA = "ontokin.c201.readback-job/0.2"
ENTRIES_SCHEMA = "ontokin.c201.readback-entries/0.1"
HELPER_PATH = "prototypes/static_tray_admission_c201/readback_entries.py"
BASE_HELPER_PATH = "prototypes/static_tray_admission_c201/readback_binding.py"
PACKAGE_NAMES = {"validator": "gltf-validator", "three": "three"}
PACKAGE_VERSIONS = {"validator": "2.0.0-dev.3.10", "three": "0.186.1"}
ENTRY_PATHS = {"validator_entry": ("validator", "index.js"),
               "three_entry": ("three", "build/three.webgpu.js"),
               "gltf_loader_entry": ("three", "examples/jsm/loaders/GLTFLoader.js")}
_TOKEN = object()


class EntryBindingError(rb.ReadbackError):
    """Rejected or unknown entry binding, never a process execution result."""

    def __init__(self, code, reason, state="REJECTED"):
        super().__init__("ENTRY-" + code, reason, state)


def _require(condition, code, reason):
    if not condition:
        raise EntryBindingError(code, reason)


def _boundary(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except EntryBindingError:
            raise
        except (rb.ReadbackError, tx.TransactionError, tx.Stop, tx.TrayError) as exc:
            raise EntryBindingError("BINDING", str(exc), getattr(exc, "state", "REJECTED")) from exc
        except (input_lock.InputLockError, OSError, ValueError, TypeError, KeyError,
                AttributeError, OverflowError, RecursionError) as exc:
            raise EntryBindingError("BINDING", "Missing, changed or malformed entry input: " + str(exc)) from exc
    return checked


def _path(session, row):
    root = session._context.repository_root if row["root"] == "repository" else session._context.host_root
    return Path(root) / row["path"]


def _row(session, lock, name):
    _require(name in lock["inputs"], "MISSING", "Required named input is absent")
    row = lock["inputs"][name]
    path = _path(session, row)
    input_lock._regular(path, limit=input_lock.MAX_FILE_BYTES, binding=row)
    return {"input": name, "path": str(path), "size_bytes": row["size_bytes"],
            "sha256": row["sha256"], "mode": row["mode"]}


def _reached(graph, starts):
    visited, pending = set(), list(starts)
    while pending:
        name = pending.pop()
        if name not in visited:
            visited.add(name)
            pending.extend(graph[name])
    return visited


def _metadata(raw, package):
    data = input_lock._json(raw)
    _require(type(data) is dict and data.get("name") == PACKAGE_NAMES[package]
             and data.get("version") == PACKAGE_VERSIONS[package],
             "PACKAGE", "Package name or retained version differs")
    if package == "validator":
        _require(data.get("main") == "index.js" and data.get("type", "commonjs") == "commonjs"
                 and "exports" not in data,
                 "SELECTOR", "Validator requires its exact unambiguous CommonJS main selector")
    else:
        exports = data.get("exports")
        _require(data.get("type") == "module" and type(exports) is dict
                 and exports.get("./webgpu") == "./build/three.webgpu.js"
                 and exports.get("./examples/jsm/*") == "./examples/jsm/*",
                 "SELECTOR", "Three.js retained webgpu and loader export selectors differ")
    return data


def _entries(session):
    lock = session._revalidate()
    context, validation = session._context, session.validation
    _require(lock["source"]["commit"] == context.source_commit == validation.source_commit
             and lock["source"]["tree"] == context.source_tree == validation.source_tree
             and context.lock_sha256 == validation.lock_sha256
             and context.approval_sha256 == validation.approval_sha256
             and input_lock.closure_digest(lock) == context.closure_sha256,
             "BINDING", "Retained source, validation or independently sealed closure differs")
    roles, graph = lock["roles"], lock["dependencies"]
    package_inputs = set(roles["node_packages"])
    metadata = {name: [] for name in PACKAGE_NAMES}
    for name in sorted(package_inputs):
        row = lock["inputs"][name]
        if PurePosixPath(row["path"]).name != "package.json":
            continue
        raw = input_lock._regular(_path(session, row), limit=32768, binding=row, keep=True)
        data = input_lock._json(raw)
        _require(type(data) is dict, "PACKAGE", "Package metadata must be an object")
        for package, expected in PACKAGE_NAMES.items():
            if data.get("name") == expected:
                metadata[package].append((name, _metadata(raw, package)))
    _require(all(len(rows) == 1 for rows in metadata.values()),
             "PACKAGE", "Exactly one metadata file for each required package is required")
    named, packages = {}, {}
    for package, rows in metadata.items():
        key, data = rows[0]
        binding = lock["inputs"][key]
        root = PurePosixPath(binding["path"]).parent
        _require(str(root) != ".", "PATH", "Each package needs a separate normalized root")
        named[package + "_package"] = _row(session, lock, key)
        packages[package] = {"name": data["name"], "version": data["version"],
                             "root": str(Path(session._context.host_root) / root), "metadata": key}
    roots = [Path(p["root"]) for p in packages.values()]
    _require(roots[0] != roots[1] and roots[0] not in roots[1].parents
             and roots[1] not in roots[0].parents, "PATH", "Package roots overlap")
    for role, (package, suffix) in ENTRY_PATHS.items():
        root = PurePosixPath(lock["inputs"][packages[package]["metadata"]]["path"]).parent
        key = "host:" + str(root / suffix)
        _require(key in package_inputs, "ROLE", "Named executable entry is not a node_packages input")
        named[role] = _row(session, lock, key)
    for role, lock_role in (("module_loader", "node_loader"), ("probe", "admission_node_probe"),
                            ("wrapper", "admission_format_check")):
        named[role] = _row(session, lock, roles[lock_role][0])
    named["binding_helper"] = _row(session, lock, "repository:" + HELPER_PATH)
    base_helper = "repository:" + BASE_HELPER_PATH
    _row(session, lock, base_helper)
    for key, module_file in (("repository:" + HELPER_PATH, __file__), (base_helper, rb.__file__)):
        actual = input_lock._regular(Path(module_file), limit=input_lock.MAX_FILE_BYTES, keep=True)
        _require(lock["inputs"][key]["sha256"] == rb._sha(actual),
                 "HELPER", "Bound helper bytes differ from this checked component source")
    _require(len({row["input"] for row in named.values()}) == len(named)
             and len({row["path"] for row in named.values()}) == len(named),
             "ROLE", "Named executable and metadata roles must be distinct")
    for role in ("python_executable", "python_stdlib", "blender_executable", "blender_distribution",
                 "dynamic_loader", "shared_libraries", "node_executable", "node_loader"):
        _require(not package_inputs.intersection(roles[role]), "ROLE", "Package inputs alias another host role")
    direct = {
        "probe": ("validator_package", "validator_entry", "three_package", "three_entry", "gltf_loader_entry"),
        "module_loader": ("three_entry", "three_package"),
        "validator_entry": ("validator_package",), "three_entry": ("three_package",),
        "gltf_loader_entry": ("three_entry", "three_package"),
    }
    for origin, required in direct.items():
        _require({named[role]["input"] for role in required} <= set(graph[named[origin]["input"]]),
                 "GRAPH", "Named import or metadata lacks its required direct dependency")
    wrapper_reached = _reached(graph, [named["wrapper"]["input"]])
    _require({row["input"] for row in named.values()} | {base_helper, roles["node_executable"][0]}
             <= wrapper_reached, "GRAPH", "Wrapper does not transitively bind every checker role and helper")
    node_names = _reached(graph, [named["probe"]["input"], named["module_loader"]["input"]])
    permitted = package_inputs | {named["probe"]["input"], named["module_loader"]["input"]}
    _require(node_names <= permitted, "GRAPH", "Node module graph escapes the selected package/probe/loader roles")
    for name in node_names.intersection(package_inputs):
        path = _path(session, lock["inputs"][name])
        _require(any(root in path.parents for root in roots), "PATH", "Node package dependency escapes both package roots")
    packages["three"]["revision"] = rb.CHECKS["three"]["revision"]
    return {"schema": ENTRIES_SCHEMA, "closure_sha256": session._context.closure_sha256,
            "named": named, "packages": packages,
            "graph": {name: sorted(graph[name]) for name in sorted(node_names)},
            "files": {name: _row(session, lock, name) for name in sorted(node_names)},
            "ambient_imports": False, "node_resolution_authorized": False}


@dataclass(frozen=True)
class PreparedEntryReadback:
    slot: str
    job_bytes: bytes
    accepted: tx.AcceptedTransaction
    _owner: object = field(repr=False, compare=False)
    authenticated_execution: bool = field(default=False, init=False)
    node_start_authorized: bool = field(default=False, init=False)
    native_start_authorized: bool = field(default=False, init=False)
    native_readiness: bool = field(default=False, init=False)
    admission_completed: bool = field(default=False, init=False)
    next_slot_authorized: bool = field(default=False, init=False)


class EntryReadbackBindings:
    def __init__(self, transactions, base, *, _token=None):
        _require(_token is _TOKEN, "BINDING", "Use the validated entry-binding factory")
        self._token, self._transactions, self._base = _token, transactions, base
        self._prepared, self._attempted, self._stopped = {}, set(), False


def _owner(value):
    _require(type(value) is EntryReadbackBindings and value._token is _TOKEN,
             "BINDING", "Validated entry-readback bindings are required")
    tx._session(value._transactions)
    _require(rb._owner(value._base)._transactions is value._transactions,
             "BINDING", "C208 accepted-source context differs")
    return value


@_boundary
def bind_entry_readbacks(transactions):
    """Bind exact package roles to an existing transaction session; start nothing."""
    session = tx._session(transactions)
    _entries(session)
    return EntryReadbackBindings(session, rb.bind_readbacks(session), _token=_TOKEN)


def _job(owner, slot, accepted):
    job, _ = rb._job(owner._base, slot, accepted)
    job["schema"] = JOB_SCHEMA
    job["dependency_entries"] = _entries(owner._transactions)
    job["native_start_authorized"] = False
    job["authenticated_execution"] = False
    return job


@_boundary
def prepare_entry_readback(bindings, slot, *, accepted):
    """Write one explicitly selected job/0.2; failure stops this binding session."""
    owner = _owner(bindings)
    _require(not owner._stopped and slot not in owner._attempted,
             "REPLAY", "Stopped binding session or previously attempted slot")
    owner._attempted.add(slot)
    try:
        job = _job(owner, slot, accepted)
        stage = Path(job["outputs"]["job"]).parent
        _require(not os.listdir(stage), "OUTPUT", "Node output stage is not empty")
        raw = canonical(job)
        _require(len(raw) <= rb.LIMITS["result_bytes"], "RESOURCE", "Extended job exceeds its byte allowance")
        prepared = PreparedEntryReadback(slot, raw, accepted, owner)
        tx._write(stage / rb.OUTPUTS["job"], raw, binary=True)
        _require(rb._read(stage / rb.OUTPUTS["job"]) == raw
                 and canonical(_job(owner, slot, accepted)) == raw,
                 "JOB", "Extended job or input bindings changed during preparation")
        owner._prepared[slot] = prepared
        return prepared
    except BaseException as exc:
        owner._stopped = True
        if not isinstance(exc, Exception):
            raise EntryBindingError("INTERRUPTED", "Entry preparation outcome is unknown; do not retry", "UNKNOWN") from exc
        raise


@_boundary
def inspect_entry_readback_job(prepared):
    """Return a new object after exact accepted-source, job and dependency checks."""
    _require(type(prepared) is PreparedEntryReadback, "BINDING", "An actual job/0.2 handle is required")
    owner = _owner(prepared._owner)
    _require(owner._prepared.get(prepared.slot) is prepared, "REPLAY", "Foreign or reconstructed prepared handle")
    job = _job(owner, prepared.slot, prepared.accepted)
    _require(canonical(job) == prepared.job_bytes
             and rb._read(job["outputs"]["job"]) == prepared.job_bytes,
             "JOB", "Extended job or accepted dependency binding changed")
    return job


@_boundary
def resolve_entry_import(prepared, *, importer, specifier):
    """Check one declared CPU mapping; never ask Node or search ambient paths.

    The importer is a bound input key. Only exact absolute paths, explicit
    relative file paths and the retained bare ``three`` alias are considered.
    Every returned target must be a declared direct edge in the sealed graph.
    """
    entries = inspect_entry_readback_job(prepared)["dependency_entries"]
    files, graph = entries["files"], entries["graph"]
    _require(type(importer) is str and importer in files, "IMPORT", "Importer is outside the checked Node graph")
    _require(type(specifier) is str and 0 < len(specifier) <= 4096
             and not any(c in specifier for c in ("\x00", "\r", "\n", "\\", "%", "?", "#")),
             "IMPORT", "Malformed, encoded or ambiguous import specifier")
    if specifier == "three":
        target = entries["named"]["three_entry"]["input"]
    elif specifier.startswith("/"):
        input_lock._absolute(specifier)
        matches = [name for name, row in files.items() if row["path"] == specifier]
        _require(len(matches) == 1, "IMPORT", "Absolute import is not one exact bound input")
        target = matches[0]
    elif specifier.startswith(("./", "../")):
        _require("//" not in specifier and not specifier.endswith("/"), "IMPORT", "Ambiguous relative import")
        path = posixpath.normpath(posixpath.join(posixpath.dirname(files[importer]["path"]), specifier))
        roots = [Path(p["root"]) for p in entries["packages"].values()]
        importer_roots = [root for root in roots if root in Path(files[importer]["path"]).parents]
        _require(len(importer_roots) == 1 and importer_roots[0] in Path(path).parents,
                 "IMPORT", "Relative import escapes its exact package root")
        matches = [name for name, row in files.items() if row["path"] == path]
        _require(len(matches) == 1, "IMPORT", "Relative import is not one exact bound file")
        target = matches[0]
    else:
        raise EntryBindingError("IMPORT", "Ambient, builtin, URL or undeclared bare import is forbidden")
    _require(target in graph[importer], "IMPORT", "Import has no declared direct dependency edge")
    return dict(files[target])
