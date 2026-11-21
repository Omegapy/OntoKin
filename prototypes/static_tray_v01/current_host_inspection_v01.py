"""Author unapproved P06 host records from a separately approved static plan.

This is the bounded Linux/glibc inspection interface accepted in C271 P07. It
does not install anything, approve its own inputs, qualify a host, or run a
checker. Importing this module performs no project import or process operation.
Operational invocation is PYTHON -I -S -B THIS_FILE --plan PATH
--plan-sha256 EXTERNAL_DIGEST [--observe].

Concrete nested plan contracts (all objects have closed keys):

* author.source_commands: five {argv, environment, timeout_ms} records.
* author runtime document: {schema, executable, interpreter, files, aliases,
  startup_files, extension_files, loader_inputs, environment}. executable is a
  descriptor; other named files use the P06 alias/file maps. loader_inputs is a
  list of paths. All loaded file-backed Python modules must be in the bound
  source inventory or the runtime file map. environment is the clean launcher
  environment, exactly ENVIRONMENT. No site initialization is admitted.
* metadata document: {schema, lock, packages}; each package is {name, version,
  distribution_root, metadata_files}. metadata_files maps relative filenames
  to bindings, includes METADATA, and exactly inventories that dist-info root.
* resolution.images: {file, metadata, resolved_needed} rows; file is a descriptor,
  metadata is the exact read_elf_metadata result, resolved_needed maps each
  DT_NEEDED name to a predeclared named file. needed_edges rows are
  {image, soname, resolved_path}, using canonical resolved image paths.
* loader_inputs: present {path, state:"file", binding, includes} or absent
  {path, state:"absent", parent}. includes is the exact list of config include
  files; it is empty for binary/cache/empty-preload inputs.
* search_directories: {path, device, inode, mode, entries}; entries maps every
  immediate name to {kind, device, inode, mode, target}. target is null except
  for a symlink. glibc-hwcaps descendants must be inventoried too.
* inspector_commands: {script, interpreter, commands, rtld_candidates}; script
  and interpreter are descriptors, commands is a nonempty list of descriptors,
  and each loader candidate is {path, state:"file", binding} or
  {path, state:"absent", parent}. Exact script branches and any opaque loader
  cache interpretation are the independent review's responsibility. rationale
  is a descriptor of that nonempty review, never a tool-generated approval.
* ignored_kernel_rows is [] or ["linux-vdso.so.1"] (x86-64) or
  ["linux-vdso.so.1"] (AArch64). No other non-file ldd row is accepted.
* evidence.outputs is {reserved, preflight, node_version, shared_libraries,
  host, result, completion}; each command value has intent, started,
  supervisor_outcome:{raw, committed}, stdout, stderr, inspection, postflight,
  failure. Paths are derived by output_paths; no arbitrary output is accepted.
* outer_capture: {authority, log}; both are descriptors of existing, separately
  selected harness authority and its already-open log. The log descriptor binds
  its initial prefix (at most document_bytes); later append-only growth up to
  stage_bytes is permitted under the same guarded inode/mode. Authority is immutable. The
  tool never writes either, and their contents never authorize execution.

Every unsupported rule is a refusal. A finite declared map is checked against
files and ELF metadata; it is not a general dynamic loader or shell emulator.
Native execution, kernel integrity and independent review honesty are explicit
trust boundaries. Focused mocked tests cannot establish those properties.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from datetime import datetime, timezone
import errno
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import sys
import time
from types import MappingProxyType
import uuid


ROOT = Path(__file__).resolve().parents[2]
ENTRY_POINT = "prototypes/static_tray_v01/current_host_inspection_v01.py"
PREFIX = "ontokin.current-host-readback-"
VERSION = "/0.1.0"
CONTRACT = "ontokin.current-host-readback/0.1.0"
PLAN_SCHEMA = PREFIX + "inspection-plan" + VERSION
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
               "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
NODE = {"sha256": "acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa",
        "size_bytes": 126951512, "mode": "0o755"}
NODE_VERSION = "v24.22.1"
NODE_ARCHIVE_SHA256 = "100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5"
NODE_ARCHIVE_BYTES = 45186132
P06_SCHEMA_PATH = "docs/engineering/localized-repair-c271/current-host-p06/SCHEMA.json"
P06_SCHEMA_BINDING = {"sha256": "41d90fed8fa5ff072f1ae620071e3bb54aebc81e02768260fb3c63cfd78591fa",
                      "size_bytes": 57550, "mode": "0o644"}
LIMITS = {"direct_starts": 2, "command_ms": 5000, "active_work_ms": 3000,
          "cleanup_ms": 2000, "log_bytes": 4 * 1024 * 1024,
          "inspection_bytes": 8 * 1024 * 1024, "host_bytes": 8 * 1024 * 1024,
          "document_bytes": 16 * 1024 * 1024, "stage_bytes": 64 * 1024 * 1024,
          "stage_entries": 2048, "static_ms": 60000, "publication_ms": 30000}
PLAN_KEYS = "schema contract source author runtime dependencies host_static environment commands evidence limits".split()
AUTHOR_KEYS = "entry_point source_descriptor python_descriptor python_version runtime_inventory metadata_inventory git_descriptor source_commands".split()
ROLE_SCALARS = "node python ldd inspector_interpreter elf_interpreter".split()
ROLE_LISTS = "loader_configuration shared_libraries inspector_runtime".split()
PROCESS_KEYS = "argv cwd environment label start_monotonic pid process_group returncode observed_log_bytes retained_log_bytes cleanup handles_closed error end_monotonic".split()
ATTEMPT_KEYS = "schema plan command_id expected_argv expected_direct_starts actual_direct_starts observed_direct_starts start_count_state state preflight start supervisor_process supervisor_failure postflight artifacts evidence_finalized failure".split()
COMMAND_IDS = ("node_version", "shared_libraries")
LABELS = {"node_version": "host-node-version", "shared_libraries": "host-shared-libraries"}
SOURCE_TREES = ("ontokin", "tests", "prototypes/static_tray_v01", "tools/static_tray_reader_v01")
SOURCE_OPTIONAL = ("prototypes/__init__.py", "tools/__init__.py", "tests/__init__.py")
SOURCE_FILES = (
    "tools/check_local.py", "tools/prepare_current_host_readback.py", "tools/storage_identity.py",
    "tools/force-agent-verification-requirements.txt", "tools/native-reader-verification-linux-cp312.lock", "pyproject.toml",
    "docs/engineering/static-tray-mapping-c198/CONTROLS.json",
    "docs/engineering/static-tray-qualification-c199/EXTERNAL-INPUTS.json",
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.md",
    "docs/engineering/localized-repair-c271/current-host-p05/CONTRACT.json",
    "docs/engineering/localized-repair-c271/current-host-p05/ADOPTION.json",
    "docs/engineering/localized-repair-c271/current-host-p05/mapping/MAP-EVIDENCE.zip")


class HostInspectionError(RuntimeError):
    """Distinct from supervisor.Stop; original exception/receipt remain attached."""

    def __init__(self, category, reason, *, cause=None, process_record=None, state="REJECTED", details=None):
        self.code = category if category.startswith("CHI-") else "CHI-" + category
        self.reason, self.state = reason, state
        self.cause, self.process_record = cause, process_record
        self.supervisor_exception = None
        self.details = details or {}
        self.refusal_record = {"schema": PREFIX + "inspection-refusal" + VERSION,
                               "error": self.as_dict(), "evidence_finalized": False}
        super().__init__(reason)

    def as_dict(self):
        return {"code": self.code, "reason": self.reason, "state": self.state,
                "cause": _failure(self.cause), "details": self.details}


def _failure(exc):
    if exc is None:
        return None
    if hasattr(exc, "as_dict"):
        return exc.as_dict()
    return {"type": type(exc).__name__, "reason": str(exc)}


def _require(condition, category, reason, **kwargs):
    if not condition:
        raise HostInspectionError(category, reason, **kwargs)


def _keys(value, expected, category="PLAN"):
    _require(type(value) is dict and set(value) == set(expected), category,
             "Missing or unknown object keys; expected " + ", ".join(sorted(expected)))


def _canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                          allow_nan=False).encode("ascii")
    except (TypeError, ValueError, RecursionError) as exc:
        raise HostInspectionError("EVIDENCE", "Cannot serialize bounded canonical evidence", cause=exc) from exc


def _digest(value, category="PLAN"):
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             category, "Expected an external lowercase SHA-256 digest")
    return value


def _absolute(value, category="PATH", *, links=False):
    _require(isinstance(value, (str, Path)), category, "Expected an absolute path")
    text = str(value)
    path = Path(text)
    _require(bool(text) and len(text) <= 4096 and len(path.parts) <= 128 and "\0" not in text and path.is_absolute() and str(path) == text
             and ".." not in path.parts and not text.startswith("//"), category,
             "Expected a normalized absolute path")
    if not links:
        for item in (path, *path.parents):
            _require(not item.is_symlink(), category, "Symlink path component: " + str(item))
    return path


def _relative(value, category="PLAN"):
    _require(type(value) is str and value and "\0" not in value and "\\" not in value,
             category, "Invalid relative input name")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and str(path) == value and ".." not in path.parts
             and str(path) != ".", category, "Unsafe relative input name")
    return path


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _binding_shape(value, category="PLAN", *, descriptor=False):
    _keys(value, ["sha256", "size_bytes", "mode"] + (["path"] if descriptor else []), category)
    _digest(value["sha256"], category)
    _require(type(value["size_bytes"]) is int and value["size_bytes"] >= 0, category, "Invalid file byte count")
    _require(type(value["mode"]) is str and re.fullmatch(r"0o[0-7]{3,4}", value["mode"]) is not None,
             category, "Invalid file mode")
    if descriptor:
        _absolute(value["path"], category)


def _binding(value):
    return {key: value[key] for key in ("sha256", "size_bytes", "mode")}


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


class _Deadline:
    def __init__(self, milliseconds, category="PLAN"):
        self.deadline = time.monotonic() + milliseconds / 1000
        self.category = category

    def __call__(self):
        _require(time.monotonic() < self.deadline, self.category, "Bounded outer allowance exhausted", state="TIMEOUT")


def _read_file(path, maximum, *, category="PLAN", private=True, check=lambda: None, keep=True):
    path = _absolute(path, category)
    fd = None
    try:
        check()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        before = os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode) and (not private or before.st_nlink == 1),
                 category, "Expected a private regular file: " + str(path))
        _require(before.st_size <= maximum, category, "Input byte allowance exceeded")
        digest, chunks, length = hashlib.sha256(), [], 0
        while True:
            check()
            block = os.read(fd, min(1024 * 1024, maximum - length + 1))
            if not block:
                break
            length += len(block)
            _require(length <= maximum, category, "Input grew beyond its byte allowance")
            digest.update(block)
            if keep:
                chunks.append(block)
        after, named = os.fstat(fd), path.lstat()
        _require(_identity(before) == _identity(after) == _identity(named) and length == before.st_size,
                 category, "Input changed while being read: " + str(path))
        return (b"".join(chunks) if keep else None), {
            "sha256": digest.hexdigest(), "size_bytes": length, "mode": oct(stat.S_IMODE(before.st_mode))}
    except HostInspectionError:
        raise
    except OSError as exc:
        raise HostInspectionError(category, "Cannot authenticate input: " + str(path), cause=exc) from exc
    finally:
        if fd is not None:
            os.close(fd)


def _bound(path, expected, *, category="PLAN", private=True, check=lambda: None):
    _binding_shape(expected, category)
    _, actual = _read_file(path, expected["size_bytes"], category=category, private=private, check=check, keep=False)
    _require(actual == expected, category, "Bound file identity differs: " + str(path))
    return actual


def _decode(raw, category="PLAN"):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, category, "Duplicate JSON member: " + key)
            result[key] = value
        return result
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=lambda text: (_ for _ in ()).throw(ValueError(text)))
        _require(_canonical(value) == raw, category, "JSON must use the frozen canonical serialization")
        return value
    except HostInspectionError as exc:
        if exc.code != "CHI-" + category:
            raise HostInspectionError(category, "Invalid bounded JSON value", cause=exc) from exc
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise HostInspectionError(category, "Invalid bounded JSON", cause=exc) from exc


def _document(descriptor, maximum=16 * 1024 * 1024, *, category="PLAN", check=lambda: None):
    _binding_shape(descriptor, category, descriptor=True)
    raw, actual = _read_file(descriptor["path"], maximum, category=category, check=check)
    _require(actual == _binding(descriptor), category, "Document identity differs")
    return _decode(raw, category)


def _describe(path, *, check=lambda: None, maximum=16 * 1024 * 1024):
    _, value = _read_file(path, maximum, category="EVIDENCE", check=check, keep=False)
    return {"path": str(path), **value}


def _freeze(value):
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


class ValidatedPlan:
    """Immutable plan and observed validation identity; cannot grant approval."""
    __slots__ = ("_value", "_descriptor", "_source_reads", "_git_state", "_helpers", "_runtime", "_metadata", "_sealed")

    def __init__(self, value, descriptor, source_reads, git_state, helpers, runtime, metadata):
        object.__setattr__(self, "_value", _freeze(value))
        object.__setattr__(self, "_descriptor", _freeze(descriptor))
        object.__setattr__(self, "_source_reads", _freeze(source_reads))
        object.__setattr__(self, "_git_state", _freeze(git_state))
        object.__setattr__(self, "_helpers", helpers)
        object.__setattr__(self, "_runtime", _freeze(runtime))
        object.__setattr__(self, "_metadata", _freeze(metadata))
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name, value):
        raise AttributeError("Validated inspection plans are immutable")

    @property
    def plan(self):
        return self._value

    @property
    def descriptor(self):
        return self._descriptor


def output_paths(attempt_root):
    """The sole admitted output topology; this pure function creates nothing."""
    root = _absolute(attempt_root)
    result = {key: str(root / (key + ".json")) for key in ("reserved", "preflight", "result", "completion")}
    result["host"] = str(root / "HOST.json")
    for name in COMMAND_IDS:
        stage, label = root / name, LABELS[name]
        result[name] = {key: str(stage / (key + ".json"))
                        for key in ("intent", "started", "inspection", "postflight", "failure")}
        result[name].update(stdout=str(stage / (label + ".stdout.log")),
                            stderr=str(stage / (label + ".stderr.log")),
                            supervisor_outcome={"raw": str(stage / (label + ".process.json")),
                                                "committed": str(stage / "supervisor-outcome.json")})
    return result


def _strings(value, category, *, nonempty=False):
    _require(type(value) is list and (not nonempty or value) and all(type(item) is str and item for item in value)
             and len(set(value)) == len(value), category, "Expected a unique finite string list")
    return value


def _plan_shape(plan):
    _keys(plan, PLAN_KEYS)
    _require(plan["schema"] == PLAN_SCHEMA and plan["contract"] == CONTRACT, "PLAN", "Unsupported executable inspection plan")
    _require(plan["environment"] == ENVIRONMENT and _canonical(plan["limits"]) == _canonical(LIMITS), "PLAN", "Fixed environment or limits differ")
    _keys(plan["source"], "root commit tree inventory".split())
    root = _absolute(plan["source"]["root"], "SOURCE")
    _require(root == ROOT, "SOURCE", "Inspection module belongs to another checkout")
    for key in ("commit", "tree"):
        _require(type(plan["source"][key]) is str and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", plan["source"][key]),
                 "SOURCE", "Invalid source commit/tree")
    _binding_shape(plan["source"]["inventory"], "PLAN", descriptor=True)
    author = plan["author"]
    _keys(author, AUTHOR_KEYS)
    _require(author["entry_point"] == str(root / ENTRY_POINT), "SOURCE", "Entry point is not this canonical module")
    for key in ("source_descriptor", "python_descriptor", "runtime_inventory", "metadata_inventory", "git_descriptor"):
        _binding_shape(author[key], "PLAN", descriptor=True)
    _require(author["source_descriptor"]["path"] == author["entry_point"], "SOURCE", "Author source descriptor differs")
    _require(type(author["python_version"]) is str and re.fullmatch(r"\d+\.\d+\.\d+", author["python_version"]),
             "INSPECTOR", "Invalid Python version")
    _keys(plan["runtime"], "executable version candidate source_archive install_receipt".split(), "RUNTIME")
    runtime = plan["runtime"]
    _binding_shape(runtime["candidate"], "PLAN")
    node = _absolute(runtime["executable"], "RUNTIME")
    _require(runtime["version"] == NODE_VERSION and _canonical(runtime["candidate"]) == _canonical(NODE), "RUNTIME", "Selected Node identity differs")
    _require(not node.is_relative_to(root), "RUNTIME", "Runtime must be outside source")
    _binding_shape(runtime["source_archive"], "RUNTIME", descriptor=True)
    _require(runtime["source_archive"]["sha256"] == NODE_ARCHIVE_SHA256
             and runtime["source_archive"]["size_bytes"] == NODE_ARCHIVE_BYTES, "RUNTIME", "Preserved Node archive differs")
    _binding_shape(runtime["install_receipt"], "RUNTIME", descriptor=True)
    _keys(plan["dependencies"], "root inventory install_receipt".split(), "RUNTIME")
    dependencies = _absolute(plan["dependencies"]["root"], "RUNTIME")
    _require(not dependencies.is_relative_to(root) and not node.is_relative_to(dependencies)
             and not dependencies.is_relative_to(node.parent.parent), "RUNTIME", "Source/runtime/dependency roots overlap")
    for key in ("inventory", "install_receipt"):
        _binding_shape(plan["dependencies"][key], "RUNTIME", descriptor=True)
    _keys(plan["host_static"], "platform files aliases roles resolution path_guards".split(), "LOADER")
    _keys(plan["host_static"]["resolution"], "profile images needed_edges loader_inputs search_directories inspector_commands ignored_kernel_rows rationale".split(), "LOADER")
    _require(plan["host_static"]["resolution"]["profile"] == "linux-glibc-declared-closure-v1", "UNSUPPORTED", "Unsupported closure profile")
    _keys(plan["evidence"], "parent attempt_root ancestor_identities outputs outer_capture".split(), "PATH")
    evidence = plan["evidence"]
    parent, attempt = (_absolute(evidence[key], "PATH") for key in ("parent", "attempt_root"))
    _require(attempt.parent == parent and attempt != parent, "PATH", "Attempt must be a direct child of approved evidence parent")
    for protected in (root, dependencies, node.parent.parent):
        _require(not parent.is_relative_to(protected) and not protected.is_relative_to(parent), "PATH", "Evidence overlaps protected input root")
    expected_outputs = output_paths(attempt)
    _keys(evidence["outputs"], expected_outputs, "PLAN")
    for name in COMMAND_IDS:
        _keys(evidence["outputs"][name], expected_outputs[name], "PLAN")
        _keys(evidence["outputs"][name]["supervisor_outcome"], ("raw", "committed"), "PLAN")
    _require(evidence["outputs"] == expected_outputs, "PATH", "Evidence paths differ from fixed topology")
    _keys(evidence["outer_capture"], ("authority", "log"), "PATH")
    for descriptor in evidence["outer_capture"].values():
        _binding_shape(descriptor, "PATH", descriptor=True)
    _require(type(plan["commands"]) is list and len(plan["commands"]) == 2, "PLAN", "Exactly two ordered commands are required")
    for command, name in zip(plan["commands"], COMMAND_IDS):
        _keys(command, "id argv cwd label timeout_ms active_work_ms cleanup_ms expected_direct_starts stdout_predicate stderr_predicate".split())
        expected = {"id": name, "argv": [str(node), "--version"] if name == "node_version" else ["/usr/bin/ldd", str(node)],
                    "cwd": str(attempt / name), "label": LABELS[name], "timeout_ms": 5000,
                    "active_work_ms": 3000, "cleanup_ms": 2000, "expected_direct_starts": 1,
                    "stdout_predicate": "v24.22.1\n" if name == "node_version" else "linux-glibc-declared-closure-v1",
                    "stderr_predicate": ""}
        _require(command == expected and all(type(command[k]) is int for k in
                 ("timeout_ms", "active_work_ms", "cleanup_ms", "expected_direct_starts")), "PLAN", "Command differs from frozen fixed command")


def _path_row(path):
    path = _absolute(path, "PATH", links=True)
    info = path.lstat()
    kind = "symlink" if stat.S_ISLNK(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "file" if stat.S_ISREG(info.st_mode) else "special"
    _require(kind != "special", "PATH", "Special file in path guard")
    return {"path": str(path), "kind": kind, "device": info.st_dev, "inode": info.st_ino,
            "mode": oct(stat.S_IMODE(info.st_mode)), "target": os.readlink(path) if kind == "symlink" else None}


def _ancestors(path):
    path = _absolute(path)
    rows = []
    for item in (path, *path.parents):
        row = _path_row(item)
        _require(row["kind"] == "directory", "PATH", "Evidence ancestor is not an actual directory")
        rows.append(row)
    return sorted(rows, key=lambda row: row["path"])


def _existing_chain(path):
    """Include every named component and every explicit symlink target hop."""
    pending, seen, links = [_absolute(path, links=True)], set(), 0
    while pending:
        current = pending.pop()
        for item in reversed((current, *current.parents)):
            text = str(item)
            if text in seen:
                continue
            seen.add(text)
            if item.is_symlink():
                links += 1
                _require(links <= 40, "PATH", "Excessive or circular alias chain")
                target = os.readlink(item)
                _require(".." not in PurePosixPath(target).parts, "UNSUPPORTED",
                         "Parent-traversal symlink targets require a separately reviewed traversal model")
                raw = Path(target) if os.path.isabs(target) else item.parent / target
                # Lexical normalization is only for following an already bound
                # alias target; externally supplied paths are never normalized.
                pending.append(Path(os.path.normpath(str(raw))))
                pending.append(item.resolve(strict=True))
    return seen


def _check_guards(rows, required, *, check=lambda: None):
    _require(type(rows) is list and len(rows) <= 32768, "PATH", "Invalid finite path guard inventory")
    present, absent = {}, {}
    for row in rows:
        check()
        _require(type(row) is dict and "path" in row, "PATH", "Invalid path guard")
        path = _absolute(row["path"], links=True)
        _require(str(path) not in present and str(path) not in absent, "PATH", "Duplicate path guard")
        if "kind" in row:
            _keys(row, "path kind device inode mode target".split(), "PATH")
            _require(type(row["device"]) is int and row["device"] >= 0 and type(row["inode"]) is int
                     and row["inode"] > 0, "PATH", "Invalid path inode identity")
            _require(_path_row(path) == row, "PATH", "Path guard changed: " + str(path))
            present[str(path)] = row
        else:
            _keys(row, "path parent parent_device parent_inode".split(), "PATH")
            parent = _absolute(row["parent"])
            _require(path.parent == parent and not path.exists() and not path.is_symlink(), "PATH", "Required absence changed")
            info = parent.lstat()
            _require(stat.S_ISDIR(info.st_mode) and type(row["parent_device"]) is int
                     and type(row["parent_inode"]) is int and (info.st_dev, info.st_ino) ==
                     (row["parent_device"], row["parent_inode"]), "PATH", "Absent path parent identity changed")
            absent[str(path)] = row
    necessary = set()
    for path in required:
        check()
        if str(path) in absent:
            necessary.update(_existing_chain(Path(path).parent))
        else:
            necessary.update(_existing_chain(path))
    _require(necessary <= set(present), "PATH", "Significant ancestor or alias hop is unbound")
    return {"present": present, "absent": absent}


def _check_log_prefix(descriptor, *, check=lambda: None):
    """Authenticate a bounded initial prefix while allowing its owner to append."""
    _binding_shape(descriptor, "PATH", descriptor=True)
    _require(descriptor["size_bytes"] <= LIMITS["document_bytes"], "PATH", "Outer log prefix exceeds its finite allowance")
    path, fd = _absolute(descriptor["path"]), None
    try:
        check()
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        before = os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and descriptor["size_bytes"] <= before.st_size <= LIMITS["stage_bytes"]
                 and oct(stat.S_IMODE(before.st_mode)) == descriptor["mode"], "PATH", "Outer log identity or initial extent differs")
        remaining, digest = descriptor["size_bytes"], hashlib.sha256()
        while remaining:
            check()
            block = os.read(fd, min(1024 * 1024, remaining))
            _require(bool(block), "PATH", "Outer log initial prefix was truncated")
            remaining -= len(block)
            digest.update(block)
        after, named = os.fstat(fd), path.lstat()
        _require(_identity(before)[:4] == _identity(after)[:4] == _identity(named)[:4]
                 and before.st_size <= after.st_size <= named.st_size <= LIMITS["stage_bytes"]
                 and digest.hexdigest() == descriptor["sha256"], "PATH", "Outer log prefix or inode changed")
        check()
        return {"identity": list(_identity(named)[:4]), "resolved": str(path), "append_prefix": _binding(descriptor)}
    except HostInspectionError:
        raise
    except OSError as exc:
        raise HostInspectionError("PATH", "Cannot authenticate caller-owned log prefix", cause=exc) from exc
    finally:
        if fd is not None:
            os.close(fd)


def _check_evidence(plan, *, fresh=True, check=lambda: None):
    evidence = plan["evidence"]
    parent = _absolute(evidence["parent"])
    _require(parent.is_dir() and _ancestors(parent) == evidence["ancestor_identities"], "PATH", "Evidence ancestor identity differs")
    attempt = _absolute(evidence["attempt_root"])
    if fresh:
        _require(not attempt.exists() and not attempt.is_symlink(), "PATH", "Attempt already exists; reconciliation is required")
    for key, descriptor in evidence["outer_capture"].items():
        path = _absolute(descriptor["path"])
        _require(not path.is_relative_to(attempt), "PATH", "Outer capture cannot be inside the future attempt")
        if key == "log":
            _check_log_prefix(descriptor, check=check)
        else:
            _bound(path, _binding(descriptor), category="PATH", check=check)


def _alias(path):
    path = _absolute(path, "LOADER", links=True)
    return {"resolved_path": str(path.resolve(strict=True)), "symlink": path.is_symlink(),
            "link_target": os.readlink(path) if path.is_symlink() else None}


def _check_alias_files(files, aliases, named, *, check=lambda: None, category="LOADER"):
    _require(type(files) is dict and type(aliases) is dict and set(aliases) == set(named), category,
             "Named alias inventory differs")
    resolved = set()
    for name, expected in aliases.items():
        check()
        _keys(expected, "resolved_path symlink link_target".split(), category)
        _require(type(expected["symlink"]) is bool and (expected["link_target"] is None or type(expected["link_target"]) is str),
                 category, "Invalid alias shape")
        _require(_alias(name) == expected, category, "Bound alias changed: " + name)
        resolved.add(expected["resolved_path"])
    _require(set(files) == resolved, category, "Complete resolved file set differs")
    for path, binding in files.items():
        _bound(path, binding, category=category, private=False, check=check)


def _platform():
    info = os.uname()
    libc = os.confstr("CS_GNU_LIBC_VERSION")
    _require(type(libc) is str and libc.startswith("glibc "), "UNSUPPORTED", "Only identified Linux/glibc is supported")
    # This one kernel pseudo-file has a meaningful bounded read but st_size=0.
    path = Path("/proc/sys/kernel/random/boot_id")
    with path.open("rb") as stream:
        raw = stream.read(129)
    _require(re.fullmatch(rb"[0-9a-f-]{36}\n?", raw) is not None, "UNSUPPORTED", "Unrecognized kernel boot identity")
    return {"system": info.sysname, "release": info.release, "machine": info.machine,
            "libc": ["glibc", libc.split(" ", 1)[1]], "boot_id": raw.decode("ascii").strip()}


def _check_host_static(plan, *, check=lambda: None):
    host = plan["host_static"]
    _keys(host["platform"], "system release machine libc boot_id".split(), "UNSUPPORTED")
    _require(host["platform"]["system"] == "Linux" and host["platform"]["machine"] in ("x86_64", "aarch64")
             and type(host["platform"]["libc"]) is list and len(host["platform"]["libc"]) == 2
             and host["platform"]["libc"][0] == "glibc", "UNSUPPORTED", "Unsupported platform/architecture/libc")
    _require(host["platform"] == _platform(), "LOADER", "Current platform or boot differs")
    _keys(host["roles"], ROLE_SCALARS + ROLE_LISTS, "LOADER")
    roles = host["roles"]
    _require(roles["node"] == plan["runtime"]["executable"] and roles["python"] == plan["author"]["python_descriptor"]["path"]
             and roles["ldd"] == "/usr/bin/ldd", "INSPECTOR", "Executable role differs")
    named = list(roles[key] for key in ROLE_SCALARS)
    for key in ROLE_LISTS:
        named.extend(_strings(roles[key], "LOADER", nonempty=True))
    for path in named:
        _absolute(path, "UNSUPPORTED", links=True)
        _require(not any(char.isspace() for char in path), "UNSUPPORTED", "Whitespace paths cannot satisfy both P06 consumers")
    _require(roles["elf_interpreter"] not in roles["shared_libraries"], "LOADER", "Interpreter must have its separate role")
    for key in ("python", "ldd", "inspector_interpreter"):
        named_path = roles[key]
        _require(named_path in host["aliases"], "INSPECTOR", "Inspector alias is missing")
        resolved = host["aliases"][named_path]["resolved_path"]
        _require(resolved in host["files"], "INSPECTOR", "Inspector file binding is missing")
        _bound(roles[key] if key == "ldd" else resolved, host["files"][resolved],
               category="INSPECTOR", private=key == "ldd", check=check)
    _check_alias_files(host["files"], host["aliases"], set(named), check=check)
    _require(host["files"].get(roles["node"]) == NODE, "RUNTIME", "Exact Node is missing from host file roles")
    _bound(roles["node"], NODE, category="RUNTIME", check=check)
    _check_inspector_script(roles["ldd"], roles["inspector_interpreter"], check=check)


def _check_inspector_script(path, interpreter, *, check=lambda: None):
    ldd, _ = _read_file(path, 1024 * 1024, category="INSPECTOR", check=check)
    _require(ldd.split(b"\n", 1)[0] == ("#!" + interpreter).encode("ascii"),
             "INSPECTOR", "ldd must have the exact direct bound shebang")


def read_elf_metadata(path, *, check=lambda: None, require_interpreter=False):
    """Bounded ELF64 little-endian metadata, without executing an image.

    Shared objects may have no PT_INTERP; callers require exactly one for the
    selected Node and ordinary command executables. Unknown loader-affecting
    dynamic tags and nonliteral search tokens are refused conservatively.
    """
    path = _absolute(path, "LOADER")
    fd = None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        before = os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode) and before.st_size <= 512 * 1024 * 1024,
                 "UNSUPPORTED", "Unsafe or oversized ELF file")
        def read(offset, size):
            check()
            _require(type(offset) is int and type(size) is int and offset >= 0 and 0 <= size <= 16 * 1024 * 1024
                     and offset + size <= before.st_size, "UNSUPPORTED", "ELF range escapes its file/bound")
            raw = os.pread(fd, size, offset)
            _require(len(raw) == size, "UNSUPPORTED", "Truncated ELF range")
            return raw
        head = read(0, 64)
        _require(head[:4] == b"\x7fELF" and head[4:7] == b"\x02\x01\x01" and head[7] in (0, 3),
                 "UNSUPPORTED", "Only reviewed ELF64 little-endian System V/Linux images are supported")
        elf_type, machine, version = struct.unpack_from("<HHI", head, 16)
        _require(elf_type in (2, 3) and machine in (62, 183) and version == 1, "UNSUPPORTED", "Unsupported ELF type or architecture")
        offset = struct.unpack_from("<Q", head, 32)[0]
        header_size, entry_size, count = struct.unpack_from("<HHH", head, 52)
        _require(header_size == 64 and entry_size == 56 and 0 < count <= 256, "UNSUPPORTED", "Unsupported ELF program table")
        table = read(offset, entry_size * count)
        segments, interpreters, dynamic, dynamic_locations = [], [], [], []
        for index in range(count):
            kind, flags, fileoff, virtual, physical, filesz, memsz, alignment = struct.unpack_from("<IIQQQQQQ", table, index * entry_size)
            _require(fileoff + filesz <= before.st_size and filesz <= memsz and
                     (alignment in (0, 1) or alignment & (alignment - 1) == 0), "UNSUPPORTED", "Invalid ELF segment bounds/alignment")
            if kind == 1:
                _require(alignment in (0, 1) or fileoff % alignment == virtual % alignment,
                         "UNSUPPORTED", "ELF PT_LOAD file/virtual alignment is incongruent")
                segments.append((virtual, fileoff, filesz))
            elif kind == 3:
                _require(1 < filesz <= 4096, "UNSUPPORTED", "Invalid ELF interpreter length")
                raw = read(fileoff, filesz)
                _require(raw[-1:] == b"\0" and b"\0" not in raw[:-1], "UNSUPPORTED", "Invalid ELF interpreter string")
                interpreter = raw[:-1].decode("ascii")
                _absolute(interpreter, "UNSUPPORTED", links=True)
                interpreters.append(interpreter)
            elif kind == 2:
                _require(filesz and filesz % 16 == 0 and filesz <= 65536, "UNSUPPORTED", "Invalid dynamic table size")
                dynamic.append(read(fileoff, filesz))
                dynamic_locations.append((fileoff, virtual, filesz))
        _require(len(interpreters) <= 1 and len(dynamic) == 1 and segments, "UNSUPPORTED", "Missing/duplicate dynamic or interpreter table")
        _require(not require_interpreter or len(interpreters) == 1, "UNSUPPORTED", "Executable requires one ELF interpreter")
        for fileoff, virtual, size in dynamic_locations:
            mapped = [load_off + virtual - load_virtual for load_virtual, load_off, load_size in segments
                      if load_virtual <= virtual and virtual + size <= load_virtual + load_size]
            _require(len(set(mapped)) == 1 and mapped[0] == fileoff, "UNSUPPORTED", "Dynamic table file/virtual mapping disagrees")
        entries, ended = [], False
        for index in range(0, len(dynamic[0]), 16):
            tag, value = struct.unpack_from("<qQ", dynamic[0], index)
            if tag == 0:
                ended = True
                break
            entries.append((tag, value))
        _require(ended, "UNSUPPORTED", "Unterminated dynamic table")
        # Relocation, hash, symbol and initialization metadata do not select
        # another image. Audit/filter/auxiliary and other unknown tags can.
        ordinary = set(range(1, 31)) | {32, 33, 34, 35, 36, 37, 0x6FFFFEF5, 0x6FFFFFF0,
                    0x6FFFFFF9, 0x6FFFFFFA, 0x6FFFFFFB, 0x6FFFFFFC, 0x6FFFFFFD, 0x6FFFFFFE, 0x6FFFFFFF}
        _require(all(tag in ordinary for tag, _ in entries), "UNSUPPORTED", "Unreviewed ELF dynamic loader feature")
        # DT_FLAGS: ORIGIN and loader-side binding modes need separate review.
        flags = [value for tag, value in entries if tag == 30]
        flags1 = [value for tag, value in entries if tag == 0x6FFFFFFB]
        _require(len(flags) <= 1 and len(flags1) <= 1 and all(value & ~8 == 0 for value in flags)
                 and all(value & ~(1 | 0x08000000) == 0 for value in flags1), "UNSUPPORTED", "Unsupported dynamic flags")
        def single(tag, *, required=False):
            found = [value for key, value in entries if key == tag]
            _require(len(found) <= 1 and (not required or len(found) == 1), "UNSUPPORTED", "Duplicate/missing dynamic metadata")
            return found[0] if found else None
        straddr, strsize = single(5, required=True), single(10, required=True)
        _require(0 < strsize <= 4 * 1024 * 1024, "UNSUPPORTED", "Dynamic string table exceeds bound")
        mappings = [fileoff + straddr - virtual for virtual, fileoff, size in segments
                    if virtual <= straddr and straddr + strsize <= virtual + size]
        _require(len(set(mappings)) == 1, "UNSUPPORTED", "Ambiguous/unmapped ELF string table")
        strings = read(mappings[0], strsize)
        def string(position):
            _require(0 <= position < len(strings), "UNSUPPORTED", "ELF string offset escapes table")
            end = strings.find(b"\0", position)
            _require(position < end <= position + 4096, "UNSUPPORTED", "Invalid dynamic string")
            return strings[position:end].decode("ascii")
        needed = [string(value) for tag, value in entries if tag == 1]
        _require(len(needed) <= 256 and len(needed) == len(set(needed)) and
                 all(re.fullmatch(r"[^/\s\x00]+", name) for name in needed), "UNSUPPORTED", "Duplicate or unsupported DT_NEEDED name")
        paths = {}
        for name, tag in (("rpath", 15), ("runpath", 29)):
            position = single(tag)
            paths[name] = [] if position is None else string(position).split(":")
            _require(len(paths[name]) == len(set(paths[name])), "UNSUPPORTED", "Duplicate search path")
            for item in paths[name]:
                _require("$" not in item and not any(char.isspace() for char in item), "UNSUPPORTED", "Unreviewed loader token expansion")
                _absolute(item, "UNSUPPORTED", links=True)
        _require(not (paths["rpath"] and paths["runpath"]), "UNSUPPORTED", "Conflicting legacy and modern search paths")
        soname = single(14)
        result = {"class": 64, "endian": "little", "machine": machine, "type": elf_type,
                  "interpreter": interpreters[0] if interpreters else None, "needed": needed,
                  "soname": string(soname) if soname is not None else None, **paths}
        _require(_identity(before) == _identity(os.fstat(fd)) == _identity(path.lstat()), "LOADER", "ELF changed during inspection")
        check()
        return result
    except HostInspectionError:
        raise
    except (OSError, UnicodeError, struct.error, ValueError) as exc:
        raise HostInspectionError("UNSUPPORTED", "Cannot parse bounded ELF metadata", cause=exc) from exc
    finally:
        if fd is not None:
            os.close(fd)


def _directory_entries(path, *, check=lambda: None):
    path = _absolute(path, "LOADER", links=True)
    info = path.lstat()
    _require(stat.S_ISDIR(info.st_mode), "LOADER", "Search directory is not a real directory")
    entries = {}
    with os.scandir(path) as iterator:
        for entry in iterator:
            check()
            _require(len(entries) < 32768, "UNSUPPORTED", "Search directory is too large for finite inspection")
            row = _path_row(path / entry.name)
            entries[entry.name] = {key: row[key] for key in ("kind", "device", "inode", "mode", "target")}
    _require(_identity(info) == _identity(path.lstat()), "LOADER", "Search directory changed during enumeration")
    return {"path": str(path), "device": info.st_dev, "inode": info.st_ino,
            "mode": oct(stat.S_IMODE(info.st_mode)), "entries": entries}


def _bounded_include(pattern, *, check=lambda: None):
    """A finite config include: literal directory and one basename pattern.

    Wildcard directory traversal and recursive globbing are unsupported. Using
    scandir directly avoids glob's internal whole-directory list allocation.
    """
    parent, basename = os.path.split(pattern)
    _require(parent.startswith("/") and basename and not any(char in parent for char in "*?[")
             and "**" not in basename and ".." not in PurePosixPath(pattern).parts,
             "UNSUPPORTED", "Unsupported recursive/wildcard-directory loader include")
    directory = _absolute(parent, "LOADER")
    before = directory.lstat()
    _require(stat.S_ISDIR(before.st_mode), "LOADER", "Include parent is not a directory")
    found = []
    with os.scandir(directory) as entries:
        for index, entry in enumerate(entries):
            check()
            _require(index < 2048, "UNSUPPORTED", "Loader include directory exceeds finite entry bound")
            if fnmatch.fnmatchcase(entry.name, basename):
                found.append(str(directory / entry.name))
    _require(_identity(before) == _identity(directory.lstat()), "LOADER", "Include directory changed during enumeration")
    return sorted(found)


def _check_loader_inputs(inputs, searches, *, check=lambda: None):
    _require(type(inputs) is list and inputs, "LOADER", "Missing loader input inventory")
    rows, required = {}, []
    for row in inputs:
        _require(type(row) is dict and row.get("state") in ("file", "absent"), "LOADER", "Invalid loader input state")
        path = _absolute(row.get("path"), "LOADER")
        _require(str(path) not in rows, "LOADER", "Duplicate loader input")
        rows[str(path)] = row
        required.append(str(path))
        if row["state"] == "absent":
            _keys(row, ("path", "state", "parent"), "LOADER")
            _require(str(path.parent) == row["parent"] and path.parent.is_dir() and not path.exists() and not path.is_symlink(),
                     "LOADER", "Required loader absence differs")
        else:
            _keys(row, ("path", "state", "binding", "includes"), "LOADER")
            _bound(path, row["binding"], private=False, category="LOADER", check=check)
            _strings(row["includes"], "LOADER")
    for required_path in ("/etc/ld.so.cache", "/etc/ld.so.conf", "/etc/ld.so.preload"):
        _require(required_path in rows, "LOADER", "Required loader configuration presence/absence is unbound")
    preload = rows["/etc/ld.so.preload"]
    _require(preload["state"] == "absent" or preload["binding"]["size_bytes"] == 0,
             "UNSUPPORTED", "Nonempty global preload is unsupported")
    for name, row in rows.items():
        if row["state"] == "absent":
            continue
        if name == "/etc/ld.so.cache" or name == "/etc/ld.so.preload":
            _require(not row["includes"], "LOADER", "Binary cache/preload cannot declare configuration includes")
            continue
        raw, _ = _read_file(name, 1024 * 1024, category="LOADER", private=False, check=check)
        included = []
        try:
            lines = raw.decode("utf-8").splitlines()
        except UnicodeError as exc:
            raise HostInspectionError("UNSUPPORTED", "Unrecognized loader configuration encoding", cause=exc) from exc
        for original in lines:
            line = original.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("include "):
                pattern = line[8:].strip()
                _require(pattern.startswith("/") and ".." not in PurePosixPath(pattern).parts and "$" not in pattern
                         and not any(char.isspace() for char in pattern), "UNSUPPORTED", "Unreviewed loader include rule")
                _require(os.path.dirname(pattern) in searches, "LOADER", "Configuration include directory entries are unbound")
                matched = _bounded_include(pattern, check=check)
                for item in matched:
                    _require(item in rows and rows[item]["state"] == "file", "LOADER", "Loader include selects an unbound file")
                included.extend(matched)
            else:
                _absolute(line, "UNSUPPORTED", links=True)
                _require(line in searches, "LOADER", "Loader configuration selects an unbound search directory")
        _require(sorted(included) == sorted(row["includes"]) and len(included) == len(set(included)),
                 "LOADER", "Recursive loader include inventory differs")
    return required


def _check_resolution(plan, author_runtime, *, check=lambda: None):
    host, resolution = plan["host_static"], plan["host_static"]["resolution"]
    _binding_shape(resolution["rationale"], "LOADER", descriptor=True)
    review, _ = _read_file(resolution["rationale"]["path"], LIMITS["document_bytes"], category="LOADER", check=check)
    _require(review and hashlib.sha256(review).hexdigest() == resolution["rationale"]["sha256"], "LOADER", "Static resolution review differs")
    _bound(resolution["rationale"]["path"], _binding(resolution["rationale"]), category="LOADER", check=check)
    searches = {}
    _require(type(resolution["search_directories"]) is list and resolution["search_directories"], "LOADER", "Missing finite search directories")
    for row in resolution["search_directories"]:
        _keys(row, "path device inode mode entries".split(), "LOADER")
        _require(row["path"] not in searches and _directory_entries(row["path"], check=check) == row,
                 "LOADER", "Search directory identity or complete entries differ")
        searches[row["path"]] = row
    for name, row in searches.items():
        for entry, info in row["entries"].items():
            if entry == "glibc-hwcaps" or "/glibc-hwcaps" in name:
                if info["kind"] == "directory":
                    _require(str(Path(name) / entry) in searches, "UNSUPPORTED", "Unbound hwcaps alternative")
    required = _check_loader_inputs(resolution["loader_inputs"], searches, check=check)
    present_inputs = {row["path"]: row["binding"] for row in resolution["loader_inputs"] if row["state"] == "file"}
    _require(set(present_inputs) == set(host["roles"]["loader_configuration"]), "LOADER", "Loader configuration roles are missing or extra")
    for name, binding in present_inputs.items():
        _require(name in host["aliases"] and host["files"].get(host["aliases"][name]["resolved_path"]) == binding,
                 "LOADER", "Present loader configuration is absent from host file closure")
    inspector = resolution["inspector_commands"]
    _keys(inspector, "script interpreter commands rtld_candidates".split(), "INSPECTOR")
    for key, role in (("script", "ldd"), ("interpreter", "inspector_interpreter")):
        _binding_shape(inspector[key], "INSPECTOR", descriptor=True)
        _require(inspector[key]["path"] == host["aliases"][host["roles"][role]]["resolved_path"], "INSPECTOR", "Inspector role descriptor differs")
        _bound(inspector[key]["path"], _binding(inspector[key]), category="INSPECTOR", private=key == "script", check=check)
    _require(type(inspector["commands"]) is list and inspector["commands"], "INSPECTOR", "Missing reviewed inspector commands")
    command_paths = []
    for descriptor in inspector["commands"]:
        _binding_shape(descriptor, "INSPECTOR", descriptor=True)
        _bound(descriptor["path"], _binding(descriptor), category="INSPECTOR", private=False, check=check)
        _require(descriptor["path"] not in command_paths, "INSPECTOR", "Duplicate inspector command")
        command_paths.append(descriptor["path"])
    _require(type(inspector["rtld_candidates"]) is list and inspector["rtld_candidates"], "INSPECTOR", "Missing reviewed RTLD candidates")
    loader_candidates, present_loaders = [], []
    for row in inspector["rtld_candidates"]:
        _require(type(row) is dict and row.get("state") in ("file", "absent"), "INSPECTOR", "Invalid inspector candidate")
        path = _absolute(row.get("path"), "INSPECTOR", links=True)
        _require(str(path) not in loader_candidates, "INSPECTOR", "Duplicate RTLD candidate")
        loader_candidates.append(str(path))
        required.append(str(path))
        if row["state"] == "file":
            _keys(row, ("path", "state", "binding"), "INSPECTOR")
            _bound(path.resolve(strict=True), row["binding"], category="INSPECTOR", private=False, check=check)
            _require(str(path) in host["aliases"] and
                     host["files"].get(str(path.resolve(strict=True))) == row["binding"],
                     "LOADER", "Present RTLD candidate is missing from host roles/files")
            present_loaders.append(str(path))
        else:
            _keys(row, ("path", "state", "parent"), "INSPECTOR")
            _require(row["parent"] == str(path.parent) and path.parent.is_dir() and not path.exists()
                     and not path.is_symlink(), "INSPECTOR", "RTLD candidate absence differs")
    script, _ = _read_file(inspector["script"]["path"], 1024 * 1024, category="INSPECTOR", check=check)
    matches = re.findall(rb'^RTLDLIST=["\']([^"\'\n]+)["\']$', script, flags=re.MULTILINE)
    _require(len(matches) == 1 and matches[0].decode("ascii").split() == loader_candidates,
             "UNSUPPORTED", "Inspector RTLDLIST is not the exact reviewed literal list")
    _require(resolution["ignored_kernel_rows"] in ([], ["linux-vdso.so.1"]), "UNSUPPORTED", "Unsupported kernel-only output rows")
    _require(type(resolution["images"]) is list and 0 < len(resolution["images"]) <= 512, "LOADER", "Missing/excessive ELF image inventory")
    images, edges = {}, []
    for row in resolution["images"]:
        _keys(row, ("file", "metadata", "resolved_needed"), "LOADER")
        descriptor = row["file"]
        _binding_shape(descriptor, "LOADER", descriptor=True)
        path = descriptor["path"]
        _require(path not in images and host["files"].get(path) == _binding(descriptor), "LOADER", "ELF image missing/duplicate in host files")
        _bound(path, _binding(descriptor), category="LOADER", private=False, check=check)
        actual = read_elf_metadata(path, check=check)
        _require(row["metadata"] == actual, "LOADER", "Declared ELF metadata differs")
        machine = 62 if host["platform"]["machine"] == "x86_64" else 183
        _require(actual["machine"] == machine, "UNSUPPORTED", "ELF architecture does not match host")
        _require(type(row["resolved_needed"]) is dict and set(row["resolved_needed"]) == set(actual["needed"]),
                 "LOADER", "DT_NEEDED resolution map is incomplete or extra")
        _require(set(actual["rpath"] + actual["runpath"]) <= set(searches), "LOADER", "ELF search path is unbound")
        for soname, target in row["resolved_needed"].items():
            _require(target in host["aliases"], "LOADER", "Needed edge selects an unbound alias")
            edges.append({"image": path, "soname": soname, "resolved_path": host["aliases"][target]["resolved_path"]})
        images[path] = row
    _require(type(resolution["needed_edges"]) is list and sorted(resolution["needed_edges"], key=_canonical) == sorted(edges, key=_canonical),
             "LOADER", "Complete transitive needed-edge inventory differs")
    for edge in edges:
        _require(edge["resolved_path"] in images, "LOADER", "Unbound transitive ELF dependency")
    executable_roots = [host["roles"][key] for key in ("node", "python", "inspector_interpreter")] + command_paths + [plan["author"]["git_descriptor"]["path"]]
    all_roots = executable_roots + author_runtime["extension_files"] + present_loaders + [host["roles"]["elf_interpreter"]]
    for path in all_roots:
        resolved = str(Path(path).resolve(strict=True))
        _require(resolved in images, "LOADER", "Executable/extension ELF closure is missing")
        interpreter = images[resolved]["metadata"]["interpreter"]
        if path in executable_roots and path not in loader_candidates:
            _require(interpreter is not None, "UNSUPPORTED", "Static executable is unsupported")
        if interpreter is not None:
            _require(interpreter in host["aliases"] and host["aliases"][interpreter]["resolved_path"] in images,
                     "LOADER", "Image interpreter is outside declared closure")
    node_meta = images[host["roles"]["node"]]["metadata"]
    _require(node_meta["interpreter"] == host["roles"]["elf_interpreter"], "LOADER", "Selected Node interpreter differs")
    node_edges = images[host["roles"]["node"]]["resolved_needed"]
    # ldd prints the finite transitive Node closure, not Python's unrelated
    # extension or the inspector's additional shared inputs.
    seen, pending, mapping = set(), [host["roles"]["node"]], {}
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        for soname, name in images[path]["resolved_needed"].items():
            _require(soname not in mapping or mapping[soname] == name, "LOADER", "Conflicting SONAME resolution")
            mapping[soname] = name
            pending.append(host["aliases"][name]["resolved_path"])
    interpreter = host["roles"]["elf_interpreter"]
    # A DT_NEEDED loader row is emitted as the separate interpreter line.
    mapping = {name: path for name, path in mapping.items() if path != interpreter
               and host["aliases"][path]["resolved_path"] != host["aliases"][interpreter]["resolved_path"]}
    _require(set(mapping.values()) == set(host["roles"]["shared_libraries"]) and len(mapping.values()) == len(set(mapping.values())),
             "LOADER", "Node transitive shared-library roles differ")
    return {"libraries": mapping, "interpreter": interpreter,
            "vdso": resolution["ignored_kernel_rows"]}, required + list(searches) + command_paths


def parse_ldd_output(stdout, stderr, expected_resolution):
    """Parse every raw line; return observations without granting new authority."""
    _keys(expected_resolution, ("libraries", "interpreter", "vdso"), "OUTPUT")
    _require(type(expected_resolution["libraries"]) is dict and expected_resolution["libraries"], "OUTPUT", "Expected closure is empty")
    _require(type(expected_resolution["vdso"]) is list and expected_resolution["vdso"] in ([], ["linux-vdso.so.1"]),
             "OUTPUT", "Expected kernel-row inventory is invalid")
    _absolute(expected_resolution["interpreter"], "OUTPUT", links=True)
    for name, path in expected_resolution["libraries"].items():
        _require(type(name) is str and re.fullmatch(r"[^/\s\x00]+", name), "OUTPUT", "Invalid expected SONAME")
        _absolute(path, "OUTPUT", links=True)
    _require(type(stdout) in (str, bytes) and type(stderr) in (str, bytes), "OUTPUT", "Streams must be text or bytes")
    try:
        output = stdout.decode("utf-8", errors="strict") if isinstance(stdout, bytes) else stdout
        error = stderr.decode("utf-8", errors="strict") if isinstance(stderr, bytes) else stderr
        total = len(output.encode("utf-8")) + len(error.encode("utf-8"))
    except UnicodeError as exc:
        raise HostInspectionError("OUTPUT", "Inspection output is not strict UTF-8", cause=exc) from exc
    _require(0 < total <= LIMITS["log_bytes"] and not error and "not found" not in output
             and "not found" not in error and "\0" not in output, "OUTPUT", "Empty, excessive or unresolved inspection output")
    _require("\r" not in output and output.endswith("\n"), "OUTPUT", "Expected LF-terminated glibc output")
    libraries, interpreter, vdso, addresses = {}, None, None, []
    for line in output[:-1].split("\n"):
        row = line.strip(" \t")
        _require(bool(row), "OUTPUT", "Blank ldd output row")
        shared = re.fullmatch(r"([^/\s]+) => (/[^\s]+) \(0x([0-9a-fA-F]+)\)", row)
        loader = re.fullmatch(r"(/[^\s]+) \(0x([0-9a-fA-F]+)\)", row)
        kernel = re.fullmatch(r"([^/\s]+) \(0x([0-9a-fA-F]+)\)", row)
        if shared:
            name, path, address = shared.groups()
            _absolute(path, "OUTPUT", links=True)
            _require(name not in libraries and path not in libraries.values(), "OUTPUT", "Duplicate SONAME or library path")
            libraries[name] = path
        elif loader:
            path, address = loader.groups()
            _absolute(path, "OUTPUT", links=True)
            _require(interpreter is None, "OUTPUT", "Duplicate interpreter row")
            interpreter = path
        elif kernel:
            name, address = kernel.groups()
            _require(vdso is None and name in expected_resolution["vdso"], "OUTPUT", "Unknown or duplicate kernel row")
            vdso = name
        else:
            raise HostInspectionError("OUTPUT", "Unknown or malformed ldd output row")
        _require(len(address) <= 16, "OUTPUT", "Out-of-range loader address")
        addresses.append(int(address, 16))
    _require(libraries == expected_resolution["libraries"] and interpreter == expected_resolution["interpreter"]
             and interpreter not in libraries.values(), "OUTPUT", "Observed closure differs from approved finite map")
    return {"libraries": libraries, "interpreter": interpreter, "vdso": vdso, "addresses": addresses}


def _walk_bounded(root, maximum, *, check=lambda: None, category="PATH"):
    """Stream entries with one global cap; never enumerate through os.walk."""
    pending, count = [Path(root)], 0
    while pending:
        check()
        directory = pending.pop()
        before = directory.lstat()
        _require(stat.S_ISDIR(before.st_mode), category, "Traversal root is not a directory")
        with os.scandir(directory) as entries:
            for entry in entries:
                check()
                count += 1
                _require(count <= maximum, category, "Finite filesystem entry allowance exceeded")
                path = directory / entry.name
                info = path.lstat()
                _require(not stat.S_ISLNK(info.st_mode) and (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)),
                         category, "Linked/special entry is outside bounded inventory")
                is_directory = stat.S_ISDIR(info.st_mode)
                yield path, info, is_directory
                if is_directory:
                    pending.append(path)
        _require(_identity(before) == _identity(directory.lstat()), category, "Directory changed while traversed")


def _source_paths(root, *, check=lambda: None):
    found = set()
    for name in SOURCE_TREES:
        directory = _absolute(root / name, "SOURCE")
        _require(directory.is_dir(), "SOURCE", "Required source tree is missing")
        for path, info, is_directory in _walk_bounded(directory, 32768, check=check, category="SOURCE"):
            _require(path.name != "__pycache__", "SOURCE", "Unbound source bytecode directory")
            if not is_directory:
                _require(path.suffix not in (".pyc", ".pyo"), "SOURCE", "Source bytecode is unbound")
                found.add(path.relative_to(root).as_posix())
                _require(len(found) <= 32768, "SOURCE", "Execution source inventory exceeds finite entry bound")
    for name in SOURCE_FILES:
        _require((root / name).is_file(), "SOURCE", "Required execution source is missing")
        found.add(name)
    found.update(name for name in SOURCE_OPTIONAL if (root / name).exists())
    return sorted(found)


def _check_source_files(plan, *, check=lambda: None):
    root = Path(plan["source"]["root"])
    _bound(plan["author"]["entry_point"], _binding(plan["author"]["source_descriptor"]), category="SOURCE", check=check)
    inventory = _document(plan["source"]["inventory"], category="SOURCE", check=check)
    _keys(inventory, ("schema", "files"), "SOURCE")
    _require(inventory["schema"] == PREFIX + "source" + VERSION and type(inventory["files"]) is dict
             and set(inventory["files"]) == set(_source_paths(root, check=check)), "SOURCE", "Complete execution source inventory differs")
    _require(inventory["files"].get(ENTRY_POINT) == _binding(plan["author"]["source_descriptor"]), "SOURCE", "Entry point is not bound by source inventory")
    for name, binding in inventory["files"].items():
        _relative(name, "SOURCE")
        _bound(root / name, binding, category="SOURCE", check=check)
    return inventory


def _git_environment(root):
    return ENVIRONMENT | {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "GIT_ATTR_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1",
            "GIT_CEILING_DIRECTORIES": str(Path(root).parent)}


def source_commands(source):
    root = source["root"]
    args = [["rev-parse", "--show-toplevel"], ["rev-parse", "--verify", "HEAD^{commit}"],
            ["rev-parse", "--verify", source["commit"] + "^{tree}"],
            ["status", "--porcelain=v1", "--untracked-files=no"], ["ls-files", "--others", "--exclude-standard", "-z"]]
    return [{"argv": ["git", "-c", "core.fsmonitor=false", "-C", root, *row],
             "environment": _git_environment(root), "timeout_ms": 5000} for row in args]


def _git_state(root):
    """Read-only ref/index witnesses for later zero-extra-process rechecks."""
    git = _absolute(Path(root) / ".git", "SOURCE")
    _require(git.is_dir(), "UNSUPPORTED", "This inspector requires an ordinary bound .git directory")
    head, binding = _read_file(git / "HEAD", 4096, category="SOURCE")
    names = ["HEAD", "index", "packed-refs"]
    if head.startswith(b"ref: "):
        try:
            ref = head[5:].decode("ascii").strip()
        except UnicodeError as exc:
            raise HostInspectionError("SOURCE", "Invalid symbolic HEAD", cause=exc) from exc
        _relative(ref, "SOURCE")
        _require(ref.startswith("refs/"), "SOURCE", "HEAD ref is outside ref namespace")
        names.append(ref)
    else:
        _require(re.fullmatch(rb"[0-9a-f]{40}(?:[0-9a-f]{24})?\n?", head), "SOURCE", "Invalid detached HEAD")
    result = {}
    for name in names:
        path = git / name
        _absolute(path, "SOURCE")
        if path.exists():
            _, actual = _read_file(path, 16 * 1024 * 1024, category="SOURCE", keep=False)
            result[name] = {"binding": actual, "inode": list(_identity(path.lstat()))}
        else:
            result[name] = {"absent": True}
    return result


def _load_helpers(plan, inventory):
    """Only called after authenticating every project import's source bytes."""
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from prototypes.static_tray_v01 import current_host_readback_v01 as provider
    from prototypes.static_tray_v01 import supervisor
    from tools import check_local
    from tools import prepare_current_host_readback as preparer
    _require(tuple(provider.SOURCE_TREES) == SOURCE_TREES and tuple(provider.SOURCE_FILES) == SOURCE_FILES
             and tuple(provider.SOURCE_OPTIONAL) == SOURCE_OPTIONAL and provider.ROOT == ROOT,
             "SOURCE", "Bound provider source inventory contract differs")
    for module in (provider, supervisor, check_local, preparer):
        path = Path(module.__file__).resolve()
        _require(path.is_relative_to(ROOT) and path.relative_to(ROOT).as_posix() in inventory["files"],
                 "SOURCE", "Loaded helper belongs to an unbound checkout")
        _bound(path, inventory["files"][path.relative_to(ROOT).as_posix()], category="SOURCE")
    return (provider, supervisor, check_local, preparer.rename_without_replacement, preparer)


def _selected_git():
    return next((Path(parent) / "git" for parent in ENVIRONMENT["PATH"].split(":")
                 if (Path(parent) / "git").is_file() and os.access(Path(parent) / "git", os.X_OK)), None)


def _check_git(plan, helpers, *, check):
    expected = source_commands(plan["source"])
    _require(plan["author"]["source_commands"] == expected, "SOURCE", "Source-read command inventory differs")
    git = plan["author"]["git_descriptor"]
    selected = _selected_git()
    _require(selected is not None and str(selected.resolve(strict=True)) == git["path"], "INSPECTOR", "Fixed PATH selects another Git executable")
    host, named = plan["host_static"], str(selected)
    roles = {host["roles"][key] for key in ROLE_SCALARS}
    for key in ROLE_LISTS:
        roles.update(host["roles"][key])
    _require(named in roles and host["aliases"].get(named) == _alias(selected)
             and host["aliases"][named]["resolved_path"] == git["path"]
             and host["files"].get(git["path"]) == _binding(git),
             "INSPECTOR", "Named PATH Git alias is outside the admitted HOST role/file/guard closure")
    # _validate admitted every HOST alias and its complete guard chain before
    # entering here. Requiring the actual PATH name prevents a canonical-only
    # descriptor from omitting the alias through which the read will execute.
    _bound(git["path"], _binding(git), category="INSPECTOR", private=False, check=check)
    driver = helpers[2]
    _require(driver.git_environment(ROOT) == _git_environment(ROOT), "INSPECTOR", "Actual Git environment differs from approved clean launcher")
    outputs, evidence = [], []
    before = _git_state(ROOT)
    for row in expected:
        check()
        remaining = check.deadline - time.monotonic()
        _require(remaining > 0, "SOURCE", "No static allowance remains for a source read")
        try:
            result = driver.git_read(ROOT, *row["argv"][5:], timeout=min(5, remaining))
        except Exception as exc:
            raise HostInspectionError("SOURCE", "Bounded source Git read failed", cause=exc) from exc
        check()
        _require(type(result) is str and len(result.encode()) <= 1024 * 1024, "SOURCE", "Git result exceeds bounded source evidence")
        outputs.append(result)
        evidence.append({**row, "stdout": result, "completed": True})
    _require(outputs[:3] == [str(ROOT), plan["source"]["commit"], plan["source"]["tree"]]
             and not outputs[3] and not outputs[4], "SOURCE", "Source identity differs, or checkout has dirty/untracked inputs")
    _require(_git_state(ROOT) == before, "SOURCE", "Git identity changed across source reads")
    return evidence, before


def _check_launcher(environment):
    _require(environment == ENVIRONMENT and dict(os.environ) == ENVIRONMENT,
             "INSPECTOR", "Author requires the exact independently frozen clean launcher environment")
    _require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode
             and "site" not in sys.modules, "INSPECTOR", "Author must be launched with -I -S -B without site hooks")


def _check_author_runtime(plan, inventory, *, loaded=False, check=lambda: None):
    author = plan["author"]
    runtime = _document(author["runtime_inventory"], category="INSPECTOR", check=check)
    _keys(runtime, "schema executable interpreter files aliases startup_files extension_files loader_inputs environment".split(), "INSPECTOR")
    _require(runtime["schema"] == PREFIX + "author-runtime" + VERSION and runtime["executable"] == author["python_descriptor"],
             "INSPECTOR", "Author runtime identity/schema differs")
    _check_launcher(runtime["environment"])
    _require(str(Path(sys.executable).resolve()) == author["python_descriptor"]["path"]
             and ".".join(map(str, sys.version_info[:3])) == author["python_version"], "INSPECTOR", "Actual author Python differs")
    _require(type(runtime["files"]) is dict and runtime["files"].get(author["python_descriptor"]["path"]) ==
             _binding(author["python_descriptor"]), "INSPECTOR", "Python descriptor disagrees with its admitted runtime file binding")
    _bound(author["python_descriptor"]["path"], _binding(author["python_descriptor"]), category="INSPECTOR", private=False, check=check)
    for key in ("startup_files", "extension_files", "loader_inputs"):
        _strings(runtime[key], "INSPECTOR", nonempty=True)
    named = [author["python_descriptor"]["path"], runtime["interpreter"]] + runtime["startup_files"] + runtime["extension_files"] + runtime["loader_inputs"]
    _check_alias_files(runtime["files"], runtime["aliases"], set(named), category="INSPECTOR", check=check)
    _require(read_elf_metadata(author["python_descriptor"]["path"], check=check)["interpreter"] == runtime["interpreter"],
             "INSPECTOR", "Python interpreter binding differs")
    if loaded:
        source_files = {str(ROOT / name) for name in inventory["files"]}
        allowed = set(runtime["files"]) | source_files
        for module in tuple(sys.modules.values()):
            path = getattr(module, "__file__", None)
            if path is None:
                continue
            path = str(Path(path).resolve())
            _require(path in allowed, "INSPECTOR", "Loaded Python module is unbound: " + path)
            cached = getattr(module, "__cached__", None)
            if cached and Path(cached).exists():
                _require(str(Path(cached).resolve()) in runtime["files"], "INSPECTOR", "Possible imported bytecode cache is unbound")
    return runtime


def _check_author_host_bindings(plan, runtime):
    """Carry every admitted author file into the unchanged P06 host lock."""
    host, roles = plan["host_static"], plan["host_static"]["roles"]
    runtime_roles = set(roles["inspector_runtime"])
    loader_roles = set(roles["loader_configuration"])
    ordinary = {runtime["interpreter"], *runtime["startup_files"], *runtime["extension_files"]}
    # The shared Node interpreter may also serve Python. Other author runtime
    # files belong to the inspector-runtime list; loader config uses its role.
    ordinary.discard(roles["elf_interpreter"])
    _require(ordinary <= runtime_roles and set(runtime["loader_inputs"]) <= runtime_roles | loader_roles,
             "INSPECTOR", "Admitted author runtime inputs are missing appropriate HOST roles")
    for name, alias in runtime["aliases"].items():
        _require(host["aliases"].get(name) == alias
                 and host["files"].get(alias["resolved_path"]) == runtime["files"][alias["resolved_path"]],
                 "INSPECTOR", "Author runtime alias/file binding is absent or different in HOST")


def _check_metadata(plan, helpers, *, check=lambda: None):
    metadata = _document(plan["author"]["metadata_inventory"], category="INSPECTOR", check=check)
    _keys(metadata, ("schema", "lock", "packages"), "INSPECTOR")
    _require(metadata["schema"] == PREFIX + "author-metadata" + VERSION, "INSPECTOR", "Metadata schema differs")
    _binding_shape(metadata["lock"], "INSPECTOR", descriptor=True)
    _require(metadata["lock"]["path"] == str(ROOT / "tools/native-reader-verification-linux-cp312.lock"), "INSPECTOR", "Package pin source differs")
    _bound(metadata["lock"]["path"], _binding(metadata["lock"]), category="INSPECTOR", check=check)
    try:
        pins = helpers[0]._python_pins(ROOT, check=check)
    except Exception as exc:
        raise HostInspectionError("INSPECTOR", "Cannot read unchanged Python pins", cause=exc) from exc
    _require(type(metadata["packages"]) is list and len(metadata["packages"]) == 7, "INSPECTOR", "Exactly seven metadata packages are required")
    observed, paths = {}, []
    for row in metadata["packages"]:
        _keys(row, "name version distribution_root metadata_files".split(), "INSPECTOR")
        _require(row["name"] not in observed and pins.get(row["name"]) == row["version"], "INSPECTOR", "Metadata pin differs or duplicates")
        root = _absolute(row["distribution_root"], "INSPECTOR")
        _require(root.is_dir() and root.name.endswith(".dist-info"), "INSPECTOR", "Unsupported distribution metadata layout")
        files = row["metadata_files"]
        _require(type(files) is dict and "METADATA" in files and 0 < len(files) <= 2048, "INSPECTOR", "Missing metadata file inventory")
        actual, directories = set(), set()
        for path, info, is_directory in _walk_bounded(root, 2048, check=check, category="INSPECTOR"):
            if is_directory:
                directories.add(path.relative_to(root).as_posix())
            else:
                _require(path.suffix not in (".py", ".pyc", ".pth", ".so"), "INSPECTOR", "Executable input is not distribution metadata")
                actual.add(path.relative_to(root).as_posix())
        _require(actual == set(files), "INSPECTOR", "Metadata inventory has missing or extra files")
        necessary = {str(parent) for name in files for parent in PurePosixPath(name).parents if str(parent) != "."}
        _require(directories == necessary, "INSPECTOR", "Metadata directory inventory has missing or extra entries")
        for name, binding in files.items():
            _relative(name, "INSPECTOR")
            _bound(root / name, binding, category="INSPECTOR", check=check)
            paths.append(str(root / name))
        raw, _ = _read_file(root / "METADATA", 4 * 1024 * 1024, category="INSPECTOR", check=check)
        try:
            header = raw.decode("utf-8").split("\n\n", 1)[0]
        except UnicodeError as exc:
            raise HostInspectionError("INSPECTOR", "Invalid metadata UTF-8", cause=exc) from exc
        names = re.findall(r"^Name: ([^\r\n]+)$", header, flags=re.MULTILINE)
        versions = re.findall(r"^Version: ([^\r\n]+)$", header, flags=re.MULTILINE)
        normalized = lambda name: re.sub(r"[-_.]+", "-", name).lower()
        _require(len(names) == len(versions) == 1 and normalized(names[0]) == normalized(row["name"])
                 and versions[0] == row["version"], "INSPECTOR", "Actual distribution metadata disagrees with pin")
        observed[row["name"]] = row["version"]
    _require(observed == pins, "INSPECTOR", "Exact package pin set differs")
    return {"packages": observed, "paths": paths}


def _check_installation(descriptor, plan, purpose, helpers, *, check=lambda: None):
    """Receipt binds the existing preparer's exact plan and actual final report.

    Closed receipt shape: {schema, plan, report}; plan/report are descriptors.
    This separate immutable index does not change or repair the preparer report.
    """
    receipt = _document(descriptor, category="RUNTIME", check=check)
    _keys(receipt, ("schema", "plan", "report"), "RUNTIME")
    _require(receipt["schema"] == PREFIX + "inspection-installation" + VERSION, "RUNTIME", "Unsupported installation receipt index")
    selected = _document(receipt["plan"], category="RUNTIME", check=check)
    report = _document(receipt["report"], category="RUNTIME", check=check)
    try:
        helpers[4]._plan_shape(selected)
    except Exception as exc:
        raise HostInspectionError("RUNTIME", "Invalid bound existing installation plan", cause=exc) from exc
    _require(selected["purpose"] == purpose and selected["source"] == plan["source"]
             and selected["report"] == receipt["report"]["path"], "RUNTIME", "Installation source, purpose or report binding differs")
    _require(report.get("schema") == PREFIX + "install-result" + VERSION and report.get("passed") is True
             and report.get("state") in ("INSTALLED_EXACT", "ALREADY_PRESENT_EXACT")
             and report.get("execution_counts") == {"node": 0, "ldd": 0, "checkers": 0},
             "RUNTIME", "Installation report is not an actual complete exact outcome")
    expected_keys = "schema passed apply_requested execution_counts operations state archive before".split()
    if report["state"] == "INSTALLED_EXACT":
        expected_keys.append("after")
        _require(report["apply_requested"] is True and report["after"].get("state") == "complete_exact", "RUNTIME", "Installation was not applied and verified")
    else:
        _require(report["before"].get("state") == "complete_exact", "RUNTIME", "Existing installation was not verified exact")
    _keys(report, expected_keys, "RUNTIME")
    _require(type(report["operations"]) is list and report["archive"] == {
        "members": len(selected["members"]), "expanded_bytes": sum(row["size_bytes"] for row in selected["members"].values())},
        "RUNTIME", "Installation report member inventory differs")
    destination = _absolute(selected["destination"], "RUNTIME")
    if purpose == "selected-node":
        _require(str(destination / "bin/node") == plan["runtime"]["executable"] and selected["archive"] == plan["runtime"]["source_archive"]
                 and set(selected["files"]) == {"bin/node", "SOURCE.json"} and selected["files"]["bin/node"] == NODE,
                 "RUNTIME", "Selected runtime installation provenance differs")
    else:
        _require(str(destination) == plan["dependencies"]["root"], "RUNTIME", "Dependency installation destination differs")
        inventory = _document(plan["dependencies"]["inventory"], category="RUNTIME", check=check)
        _require(selected["files"] == inventory["files"] and selected["directories"] == inventory["directories"]
                 and selected["archive"] == inventory["archive"], "RUNTIME", "Dependency install/inventory differs")
    _bound(selected["archive"]["path"], _binding(selected["archive"]), category="RUNTIME", check=check)
    _check_installed_tree(destination, selected["files"], selected["directories"], check=check)
    _require(oct(stat.S_IMODE(destination.stat().st_mode)) == selected["root_mode"], "RUNTIME", "Installed root mode differs")
    return [receipt["plan"]["path"], receipt["report"]["path"], str(destination / "SOURCE.json")] if purpose == "selected-node" else [receipt["plan"]["path"], receipt["report"]["path"]]


def _check_installed_tree(root, files, directories, *, check=lambda: None):
    """The existing exact-tree predicate with checked, bounded enumeration."""
    actual_files, actual_directories = set(), set()
    for path, info, directory in _walk_bounded(root, LIMITS["stage_entries"], check=check, category="RUNTIME"):
        (actual_directories if directory else actual_files).add(path.relative_to(root).as_posix())
    _require(actual_files == set(files) and actual_directories == set(directories), "RUNTIME", "Complete installed tree differs")
    necessary = {str(parent) for name in files for parent in _relative(name, "RUNTIME").parents if str(parent) != "."}
    _require(set(directories) == necessary, "RUNTIME", "Installed directory inventory is not exact")
    for name, mode in directories.items():
        check()
        _require(oct(stat.S_IMODE((Path(root) / name).stat().st_mode)) == mode, "RUNTIME", "Installed directory mode differs")
    for name, binding in files.items():
        _bound(Path(root) / name, binding, category="RUNTIME", check=check)
    check()


def _check_runtime_dependencies(plan, helpers, *, check=lambda: None):
    runtime = plan["runtime"]
    _bound(runtime["executable"], NODE, category="RUNTIME", check=check)
    _bound(runtime["source_archive"]["path"], _binding(runtime["source_archive"]), category="RUNTIME", check=check)
    paths = _check_installation(runtime["install_receipt"], plan, "selected-node", helpers, check=check)
    paths += _check_installation(plan["dependencies"]["install_receipt"], plan, "retained-dependencies", helpers, check=check)
    try:
        provider, root = helpers[0], Path(plan["dependencies"]["root"])
        inventory = _document(plan["dependencies"]["inventory"], 1024 * 1024, category="RUNTIME", check=check)
        _keys(inventory, "schema files directories archive".split(), "RUNTIME")
        _require(inventory["schema"] == PREFIX + "dependencies" + VERSION, "RUNTIME", "Dependency inventory schema differs")
        historical = provider.dependency_inventory(plan["source"]["root"])
        _require(set(inventory["files"]) == set(historical), "RUNTIME", "Exact retained dependency path set differs")
        for name, expected in historical.items():
            _binding_shape(inventory["files"][name], "RUNTIME")
            _require({key: inventory["files"][name][key] for key in ("sha256", "size_bytes")} == expected,
                     "RUNTIME", "Retained dependency bytes differ from their immutable historical pin")
        _binding_shape(inventory["archive"], "RUNTIME", descriptor=True)
        _require(inventory["archive"]["sha256"] == provider.ARCHIVE_SHA256, "RUNTIME", "Retained dependency archive differs")
        _bound(inventory["archive"]["path"], _binding(inventory["archive"]), category="RUNTIME", check=check)
        _check_installed_tree(root, inventory["files"], inventory["directories"], check=check)
        for name, version in (("validator/package/package.json", "2.0.0-dev.3.10"), ("indexer-view/three/package.json", "0.186.1")):
            package, _ = provider._read(root / name, 32768, check=check, category="DEPENDENCY")
            _require(package.get("version") == version, "RUNTIME", "Retained dependency package version differs")
    except Exception as exc:
        raise HostInspectionError("RUNTIME", "Exact retained dependency inventory differs", cause=exc) from exc
    return paths


def _required_paths(plan, author_runtime, metadata, extra):
    paths = [plan["source"]["root"], plan["source"]["inventory"]["path"], plan["author"]["entry_point"],
             plan["dependencies"]["root"], plan["evidence"]["parent"]]
    for key in ("source_descriptor", "python_descriptor", "runtime_inventory", "metadata_inventory", "git_descriptor"):
        paths.append(plan["author"][key]["path"])
    for group, fields in (("runtime", ("source_archive", "install_receipt")), ("dependencies", ("inventory", "install_receipt"))):
        paths.extend(plan[group][key]["path"] for key in fields)
    paths.extend(plan["host_static"]["aliases"])
    paths.extend(author_runtime["aliases"])
    paths.extend(metadata["paths"])
    paths.extend(row["path"] for row in plan["evidence"]["outer_capture"].values())
    paths.extend(extra)
    return paths


def _validate(plan_path, expected_plan_sha256, *, fresh, git_reads=True):
    check = _Deadline(LIMITS["static_ms"])
    _digest(expected_plan_sha256)
    path = _absolute(plan_path, "PLAN")
    raw, binding = _read_file(path, LIMITS["document_bytes"], category="PLAN", check=check)
    _require(binding["sha256"] == expected_plan_sha256, "PLAN", "Plan differs from independently supplied expected digest")
    plan = _decode(raw)
    _plan_shape(plan)
    inventory = _check_source_files(plan, check=check)
    author_runtime = _check_author_runtime(plan, inventory, check=check)
    helpers = _load_helpers(plan, inventory)
    author_runtime = _check_author_runtime(plan, inventory, loaded=True, check=check)
    metadata = _check_metadata(plan, helpers, check=check)
    extra = _check_runtime_dependencies(plan, helpers, check=check)
    _check_host_static(plan, check=check)
    _check_author_host_bindings(plan, author_runtime)
    expected_resolution, closure_paths = _check_resolution(plan, author_runtime, check=check)
    extra += closure_paths + [str(path), plan["host_static"]["resolution"]["rationale"]["path"]]
    _check_guards(plan["host_static"]["path_guards"], _required_paths(plan, author_runtime, metadata, extra), check=check)
    _check_evidence(plan, fresh=fresh, check=check)
    _p06_definitions()
    # Git is itself executable code. Its entire declared loader/alias/file
    # closure above must be admitted before any of these five process reads.
    source_reads, git_state = _check_git(plan, helpers, check=check) if git_reads else ([], _git_state(ROOT))
    _bound(path, binding, category="PLAN", check=check)
    check()
    metadata["expected_resolution"] = expected_resolution
    metadata["extra_paths"] = extra
    metadata["input_snapshot"] = _input_snapshot(plan, inventory, author_runtime, metadata, extra, check=check)
    check()
    return ValidatedPlan(plan, {"path": str(path), **binding}, source_reads, git_state, helpers, author_runtime, metadata)


def validate_inspection_plan(plan_path, expected_plan_sha256):
    """Authenticate the external plan and static inputs; never create evidence."""
    try:
        return _validate(plan_path, expected_plan_sha256, fresh=True)
    except HostInspectionError:
        raise
    except Exception as exc:
        raise HostInspectionError("PLAN", "Static inspection validation failed", cause=exc) from exc


def _recheck(validated, *, check=lambda: None, fresh=False):
    """Rehash all admitted inputs; no additional source Git processes."""
    plan = _thaw(validated.plan)
    try:
        _bound(validated.descriptor["path"], _binding(validated.descriptor), check=check)
        inventory = _check_source_files(plan, check=check)
        _require(_git_state(ROOT) == _thaw(validated._git_state), "SOURCE", "Source ref/index witness changed")
        runtime = _check_author_runtime(plan, inventory, loaded=True, check=check)
        metadata = _check_metadata(plan, validated._helpers, check=check)
        extra = _check_runtime_dependencies(plan, validated._helpers, check=check)
        _check_host_static(plan, check=check)
        _check_author_host_bindings(plan, runtime)
        resolution, closure_paths = _check_resolution(plan, runtime, check=check)
        _require(resolution == _thaw(validated._metadata)["expected_resolution"], "LOADER", "Observed static resolution map changed")
        _check_guards(plan["host_static"]["path_guards"], _required_paths(plan, runtime, metadata,
                      extra + closure_paths + [validated.descriptor["path"], plan["host_static"]["resolution"]["rationale"]["path"]]), check=check)
        _require(_ancestors(plan["evidence"]["parent"]) == plan["evidence"]["ancestor_identities"], "PATH", "Evidence ancestor changed")
        _check_evidence(plan, fresh=fresh, check=check)
        check()
    except Exception as exc:
        if isinstance(exc, HostInspectionError) and exc.code == "CHI-DRIFT":
            raise
        raise HostInspectionError("DRIFT", "An admitted input changed before/after the command", cause=exc,
                                  state=getattr(exc, "state", "REJECTED")) from exc
    return {"passed": True, "plan": _thaw(validated.descriptor), "source_commit": plan["source"]["commit"],
            "boot_id": plan["host_static"]["platform"]["boot_id"]}


def _input_snapshot(plan, inventory, runtime, metadata, extra, *, check=lambda: None):
    paths = {str(ROOT / name) for name in inventory["files"]}
    paths.update(plan["host_static"]["files"])
    paths.update(runtime["files"])
    paths.update(_required_paths(plan, runtime, metadata, extra))
    paths.add(str(ROOT / P06_SCHEMA_PATH))
    result = {}
    log = plan["evidence"]["outer_capture"]["log"]
    for name in sorted(paths):
        check()
        path = _absolute(name, links=True)
        if name == log["path"]:
            result[name] = _check_log_prefix(log, check=check)
            continue
        try:
            result[name] = {"identity": list(_identity(path.lstat())), "resolved": str(path.resolve(strict=True))}
        except FileNotFoundError:
            result[name] = {"absent": True}
    return result


def _launch_check(validated, clock, stage_end):
    """Final identity check shares the original command allowance."""
    plan = _thaw(validated.plan)
    try:
        for name, expected in _thaw(validated._metadata)["input_snapshot"].items():
            clock.check(stage_end)
            path = _absolute(name, links=True)
            if expected.get("absent"):
                _require(not path.exists() and not path.is_symlink(), "DRIFT", "Required absence changed before launch")
            elif "append_prefix" in expected:
                actual = _check_log_prefix({"path": name, **expected["append_prefix"]}, check=lambda: clock.check(stage_end))
                _require(actual == expected, "DRIFT", "Caller log inode or prefix changed before launch")
            else:
                actual = {"identity": list(_identity(path.lstat())), "resolved": str(path.resolve(strict=True))}
                _require(actual == expected, "DRIFT", "Bound file/path changed immediately before launch")
        _require(_platform() == plan["host_static"]["platform"], "DRIFT", "Host reboot/platform drift before launch")
        _check_guards(plan["host_static"]["path_guards"], [], check=lambda: clock.check(stage_end))
        clock.check(stage_end)
    except HostInspectionError:
        raise
    except Exception as exc:
        if isinstance(exc, validated._helpers[1].Stop):
            raise HostInspectionError("PROCESS", "Command allowance expired before launch", cause=exc, state=exc.state) from exc
        raise HostInspectionError("DRIFT", "Final launch identity check failed", cause=exc) from exc


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _path_readback(path):
    """Best-effort bounded readback, never replacement or retry."""
    try:
        if not path.exists() and not path.is_symlink():
            return {"path": str(path), "state": "absent"}
        row = _path_row(path)
        if row["kind"] == "file":
            row["binding"] = _describe(path)
        return {"state": "observed", **row}
    except BaseException as exc:
        return {"path": str(path), "state": "UNKNOWN", "failure": _failure(exc)}


class _EvidenceStore:
    def __init__(self, validated, *, create=True):
        self.validated = validated
        self.plan = _thaw(validated.plan)
        self.root = Path(self.plan["evidence"]["attempt_root"])
        self.rename = validated._helpers[3]
        self.owned = {}
        self.publications = []
        self.allowed = set()
        def visit(value):
            if type(value) is str:
                self.allowed.add(value)
            elif type(value) is dict:
                for item in value.values():
                    visit(item)
        visit(self.plan["evidence"]["outputs"])
        if create:
            self.check_parent()
            self._mkdir(self.root)
            for name in COMMAND_IDS:
                self._mkdir(self.root / name)

    def check_parent(self):
        _require(_ancestors(self.root.parent) == self.plan["evidence"]["ancestor_identities"],
                 "EVIDENCE", "Evidence parent changed", state="UNKNOWN")
        for name, identity in self.owned.items():
            path = _absolute(name, "EVIDENCE")
            row = path.lstat()
            _require(stat.S_ISDIR(row.st_mode) and (row.st_dev, row.st_ino, stat.S_IMODE(row.st_mode)) == identity,
                     "EVIDENCE", "Owned evidence directory changed", state="UNKNOWN")

    def _fsync_directory(self, path):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _mkdir(self, path):
        self.check_parent()
        try:
            os.mkdir(path, 0o700)
        except FileExistsError as exc:
            raise HostInspectionError("PATH", "Evidence directory already exists; no replacement", cause=exc) from exc
        row = path.lstat()
        _require(stat.S_ISDIR(row.st_mode) and stat.S_IMODE(row.st_mode) == 0o700,
                 "EVIDENCE", "Private evidence directory mode differs", state="UNKNOWN")
        self.owned[str(path)] = (row.st_dev, row.st_ino, stat.S_IMODE(row.st_mode))
        self._fsync_directory(path)
        self._fsync_directory(path.parent)

    def budget(self, *, check=lambda: None):
        count, total = 0, 0
        for path, row, directory in _walk_bounded(self.root, LIMITS["stage_entries"], check=check, category="EVIDENCE"):
            _require(directory or row.st_nlink == 1, "EVIDENCE", "Hardlinked evidence entry", state="UNKNOWN")
            total += row.st_size if not directory else 0
            _require(total <= LIMITS["stage_bytes"], "EVIDENCE", "Evidence stage byte limit exceeded", state="UNKNOWN")

    def write(self, path, value, *, maximum=None, check=None):
        check = check or _Deadline(LIMITS["publication_ms"], "EVIDENCE")
        path = _absolute(path, "EVIDENCE")
        _require(str(path) in self.allowed and str(path.parent) in self.owned,
                 "EVIDENCE", "Unplanned evidence destination", state="UNKNOWN")
        raw = _canonical(value)
        _require(len(raw) <= (maximum or LIMITS["document_bytes"]), "OUTPUT", "Evidence serialization exceeds limit")
        temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
        expected = {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw), "mode": "0o600"}
        fd, owned = None, None
        intent = {"source": str(temporary), "destination": str(path), "intended_binding": expected,
                  "state": "INTENT", "retry": False}
        self.publications.append(intent)
        try:
            check()
            self.check_parent()
            self.budget(check=check)
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            opened = os.fstat(fd)
            owned = (opened.st_dev, opened.st_ino)
            offset = 0
            while offset < len(raw):
                check()
                written = os.write(fd, raw[offset:])
                _require(written > 0, "EVIDENCE", "Short evidence write", state="UNKNOWN")
                offset += written
            os.fsync(fd)
            os.close(fd)
            fd = None
            self.check_parent()
            info = temporary.lstat()
            _require((info.st_dev, info.st_ino) == owned and info.st_nlink == 1,
                     "EVIDENCE", "Owned temporary inode changed", state="UNKNOWN")
            _bound(temporary, expected, category="EVIDENCE", check=check)
            self.rename(temporary, path)
            self._fsync_directory(path.parent)
            self.check_parent()
            check()
            _bound(path, expected, category="EVIDENCE", check=check)
            self.budget(check=check)
            intent["state"] = "COMMITTED"
            return {"path": str(path), **expected}
        except BaseException as exc:
            intent.update(state="UNKNOWN", failure=_failure(exc), owned_temporary=list(owned) if owned else None,
                          source_after=_path_readback(temporary), destination_after=_path_readback(path))
            # Preserve owned temporary bytes for explicit recovery. No retry,
            # overwrite, or cleanup of a possibly renamed destination occurs.
            category = "PATH" if isinstance(exc, OSError) and exc.errno == errno.EEXIST and path.name in ("reserved.json", "preflight.json", "intent.json") else "EVIDENCE"
            raise HostInspectionError(category, "Atomic evidence publication failed; readback retained, no retry",
                                      cause=exc, state="UNKNOWN", details=dict(intent)) from exc
        finally:
            if fd is not None:
                os.close(fd)

    def retain_raw(self, path, *, maximum):
        _require(str(path) in self.allowed, "EVIDENCE", "Unplanned raw artifact")
        path = _absolute(path, "EVIDENCE")
        raw, binding = _read_file(path, maximum, category="EVIDENCE")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        self._fsync_directory(path.parent)
        _bound(path, binding, category="EVIDENCE")
        self.check_parent()
        return raw, {"path": str(path), **binding}


def _new_attempt(validated, command, preflight):
    return {"schema": PREFIX + "inspection-attempt" + VERSION, "plan": _thaw(validated.descriptor),
            "command_id": command["id"], "expected_argv": command["argv"], "expected_direct_starts": 1,
            "actual_direct_starts": None, "observed_direct_starts": 0, "start_count_state": "UNKNOWN", "state": "UNKNOWN",
            "preflight": preflight, "start": None, "supervisor_process": None, "supervisor_failure": None,
            "postflight": None, "artifacts": {}, "evidence_finalized": False, "failure": None}


def _count_observed(record, process):
    if type(process) is dict and type(process.get("pid")) is int and process["pid"] > 0:
        record.update(actual_direct_starts=1, observed_direct_starts=1, start_count_state="OBSERVED_ONE")


def _process_success(process, command, stdout, stderr, started, finished):
    _keys(process, PROCESS_KEYS, "PROCESS")
    _keys(process["cleanup"], ("passed", "process_group_absent", "reaped", "elapsed_ms"), "PROCESS")
    _require(process["argv"] == command["argv"] and process["cwd"] == command["cwd"]
             and process["environment"] == ENVIRONMENT and process["label"] == command["label"], "PROCESS", "Actual process command binding differs")
    _require(type(process["pid"]) is int and process["pid"] > 0 and type(process["process_group"]) is int
             and process["process_group"] == process["pid"] and type(process["returncode"]) is int
             and process["returncode"] == 0 and process["handles_closed"] is True and process["error"] is None,
             "PROCESS", "Missing, failed or unknown actual process outcome")
    cleanup = process["cleanup"]
    _require(all(cleanup[key] is True for key in ("passed", "process_group_absent", "reaped"))
             and _number(cleanup["elapsed_ms"]) and 0 <= cleanup["elapsed_ms"] <= 2000,
             "PROCESS", "Process cleanup failed or exceeded allowance")
    _require(_number(process["start_monotonic"]) and _number(process["end_monotonic"])
             and 0 <= process["end_monotonic"] - process["start_monotonic"] <= 5,
             "PROCESS", "Process interval exceeds five-second allowance")
    total = len(stdout) + len(stderr)
    _require(total <= LIMITS["log_bytes"] and type(process["observed_log_bytes"]) is int
             and type(process["retained_log_bytes"]) is int and process["observed_log_bytes"] ==
             process["retained_log_bytes"] == total, "OUTPUT", "Raw/retained/observed stream counts differ or exceed limit")
    try:
        start, end = (datetime.fromisoformat(value.replace("Z", "+00:00")) for value in (started, finished))
    except (TypeError, ValueError) as exc:
        raise HostInspectionError("PROCESS", "Invalid command wall timestamps", cause=exc) from exc
    _require(start.tzinfo is not None and end.tzinfo is not None and start <= end <= datetime.now(timezone.utc),
             "PROCESS", "Unzoned, unordered or future command timestamps")
    _require(0 <= (end - start).total_seconds() <= 5, "PROCESS", "Command wall interval exceeds its bounded allowance")


def _schema_check(value, schema, definitions):
    """Validate only the pinned P06 schema subset used by HOST/inspection."""
    if "$ref" in schema:
        return _schema_check(value, definitions[schema["$ref"].split("/")[-1]], definitions)
    if "oneOf" in schema:
        passes = 0
        for alternative in schema["oneOf"]:
            try:
                _schema_check(value, alternative, definitions)
                passes += 1
            except HostInspectionError:
                pass
        _require(passes == 1, "COMPAT", "P06 union shape differs")
        return
    if "const" in schema:
        _require(type(value) is type(schema["const"]) and value == schema["const"], "COMPAT", "P06 constant differs")
    types = {"object": lambda x: type(x) is dict, "array": lambda x: type(x) is list,
             "string": lambda x: type(x) is str, "integer": lambda x: type(x) is int,
             "number": _number, "null": lambda x: x is None, "boolean": lambda x: type(x) is bool}
    if "type" in schema:
        choices = schema["type"] if type(schema["type"]) is list else [schema["type"]]
        _require(any(types[name](value) for name in choices), "COMPAT", "P06 field type differs")
    if type(value) is dict:
        properties = schema.get("properties", {})
        _require(set(schema.get("required", [])) <= set(value), "COMPAT", "P06 required field is missing")
        if schema.get("additionalProperties") is False:
            _require(set(value) <= set(properties), "COMPAT", "P06 object has an unknown field")
        for key, item in value.items():
            item_schema = properties.get(key, schema.get("additionalProperties"))
            if type(item_schema) is dict:
                _schema_check(item, item_schema, definitions)
    elif type(value) is list:
        _require(len(value) >= schema.get("minItems", 0) and len(value) <= schema.get("maxItems", sys.maxsize), "COMPAT", "P06 array size differs")
        if schema.get("uniqueItems"):
            _require(len({_canonical(item) for item in value}) == len(value), "COMPAT", "P06 array has duplicates")
        for item in value:
            _schema_check(item, schema.get("items", {}), definitions)
    elif type(value) is str and "pattern" in schema:
        _require(re.search(schema["pattern"], value) is not None, "COMPAT", "P06 field pattern differs")
    elif _number(value):
        _require(value >= schema.get("minimum", -math.inf) and value <= schema.get("maximum", math.inf), "COMPAT", "P06 numeric bound differs")


def _p06_definitions():
    # The exact existing schema is not in P06's execution source inventory;
    # pin its reviewed bytes explicitly rather than silently trusting the file.
    raw, binding = _read_file(ROOT / P06_SCHEMA_PATH, 1024 * 1024, category="COMPAT")
    _require(binding == P06_SCHEMA_BINDING, "COMPAT", "Bound P06 schema changed")
    return json.loads(raw)["$defs"]


def _inspection(process, command, stdout, stderr, started, finished, expected_resolution):
    _process_success(process, command, stdout, stderr, started, finished)
    try:
        output, error = stdout.decode("utf-8"), stderr.decode("utf-8")
    except UnicodeError as exc:
        raise HostInspectionError("OUTPUT", "Inspection output is not strict UTF-8", cause=exc) from exc
    if command["id"] == "node_version":
        _require(output == NODE_VERSION + "\n" and error == "", "OUTPUT", "Version command output differs")
    else:
        parse_ldd_output(stdout, stderr, expected_resolution)
    result = {"schema": PREFIX + "inspection" + VERSION, "argv": command["argv"], "environment": dict(ENVIRONMENT),
              "timeout_ms": 5000, "started_at_utc": started, "finished_at_utc": finished,
              "process": process, "stdout": output, "stderr": error}
    _require(len(_canonical(result)) <= LIMITS["inspection_bytes"], "OUTPUT", "Inspection document exceeds limit")
    definitions = _p06_definitions()
    _schema_check(result, definitions["inspection"], definitions)
    return result


def _retain_outcome(store, paths, command, process, failure, started_record):
    artifacts, payload, faults, streams = {}, {}, [], {}
    for key, path, maximum in (("raw_process", paths["supervisor_outcome"]["raw"], LIMITS["document_bytes"]),
                               ("stdout", paths["stdout"], LIMITS["stage_bytes"]), ("stderr", paths["stderr"], LIMITS["stage_bytes"])):
        try:
            raw, descriptor = store.retain_raw(path, maximum=maximum)
            artifacts[key] = descriptor
            if key == "raw_process":
                try:
                    payload["decoded_raw_process"] = _decode(raw, "EVIDENCE")
                    _require(payload["decoded_raw_process"] == process, "EVIDENCE", "Raw supervisor receipt disagrees with returned process")
                except HostInspectionError as exc:
                    faults.append(exc)
            else:
                streams[key] = raw
        except Exception as exc:
            faults.append(HostInspectionError("PROCESS", "Supervisor artifact is missing or cannot be retained", cause=exc, state="UNKNOWN"))
            payload[key + "_unavailable"] = _failure(exc)
    payload.update(schema=PREFIX + "inspection-supervisor-outcome" + VERSION, plan=_thaw(store.validated.descriptor), command_id=command["id"],
                   process=process, supervisor_failure=_failure(failure), observed_start=started_record,
                   artifacts=artifacts, faults=[_failure(exc) for exc in faults])
    committed = store.write(paths["supervisor_outcome"]["committed"], payload)
    return committed, artifacts, streams, faults


def _run_command(validated, command, store, preflight):
    paths = store.plan["evidence"]["outputs"][command["id"]]
    record = _new_attempt(validated, command, preflight)
    process = failure = callback_failure = started_record = None
    entered, callback_count = False, 0
    callback_records = []
    contract_violation = None
    started = finished = None
    supervisor_elapsed_ms = None
    inspection_descriptor = final = None
    try:
        store.write(paths["intent"], record)
        _recheck(validated, check=_Deadline(LIMITS["static_ms"], "DRIFT"))
        clock = validated._helpers[1].Clock(total_ms=5000)
        stage_end = clock.started + 3
        _launch_check(validated, clock, stage_end)
        started = _utc()
        def on_started(actual):
            nonlocal callback_count, callback_failure, started_record
            callback_count += 1
            started_record = actual
            callback_records.append(_decode(_canonical(actual), "PROCESS"))
            _count_observed(record, actual)
            try:
                _require(callback_count == 1 and record["start_count_state"] == "OBSERVED_ONE"
                         and type(actual.get("process_group")) is int and actual["process_group"] == actual["pid"],
                         "PROCESS", "Invalid or repeated actual start callback")
                try:
                    clock.check(stage_end)
                except validated._helpers[1].Stop as exc:
                    raise HostInspectionError("PROCESS", "Command clock expired during actual start callback", cause=exc, state=exc.state) from exc
                record["start"] = store.write(paths["started"], {
                    "schema": PREFIX + "inspection-start" + VERSION, "plan": _thaw(validated.descriptor),
                    "command_id": command["id"], "process": actual, "observed_at_utc": _utc()},
                    check=lambda: clock.check(stage_end))
            except BaseException as exc:
                callback_failure = exc
                raise
        entered = True
        try:
            process = validated._helpers[1].run_process(command["argv"], stage=Path(command["cwd"]),
                      label=command["label"], clock=clock, stage_end=stage_end, env=dict(ENVIRONMENT),
                      on_started=on_started, cancel_after_ms=None)
        except BaseException as exc:
            failure = exc
            process = getattr(exc, "process_record", None)
        supervisor_elapsed_ms = clock.elapsed_ms()
        finished = _utc()
        _count_observed(record, process)
        pids = {row["pid"] for row in callback_records if type(row.get("pid")) is int and row["pid"] > 0}
        if not callback_records and type(process) is dict and type(process.get("pid")) is int and process["pid"] > 0:
            pids.add(process["pid"])
        if len(pids) > 1 or callback_count > 1:
            record.update(actual_direct_starts=None, observed_direct_starts=len(pids), start_count_state="INVALID_MULTIPLE_STARTS")
            contract_violation = {"callback_receipts": callback_records, "final_process": process,
                "observed_distinct_pids": sorted(pids), "observed_distinct_start_count": {"exact": len(pids), "observed_lower_bound": len(pids)},
                "observed_start_lower_bound": len(pids), "callback_count": callback_count,
                "total_direct_start_count_complete": False, "normal_count_projection_available": False}
            callback_failure = HostInspectionError("PROCESS", "Direct-start contract violation; normal count projection is unavailable",
                details={"contract_violation": contract_violation})
        record["supervisor_failure"] = _failure(failure)
        committed, artifacts, streams, faults = _retain_outcome(store, paths, command, process, failure, started_record)
        record["supervisor_process"], record["artifacts"] = committed, artifacts
        # Raw outcomes are committed before any postflight or output predicate.
        record["postflight"] = _recheck(validated, check=_Deadline(LIMITS["static_ms"], "DRIFT"))
        if callback_failure is not None:
            if isinstance(callback_failure, HostInspectionError):
                raise callback_failure
            raise HostInspectionError("EVIDENCE", "Actual start could not be durably recorded", cause=callback_failure, state="UNKNOWN")
        if faults:
            raise faults[0]
        if failure is not None:
            raise HostInspectionError("PROCESS", "Delegated supervisor did not complete successfully", cause=failure,
                                      process_record=process, state=getattr(failure, "state", "UNKNOWN"))
        _require(started_record is not None and type(process) is dict and
                 all(started_record.get(key) == process.get(key) for key in
                     ("pid", "process_group", "argv", "cwd", "environment", "label", "start_monotonic")),
                 "PROCESS", "Retained actual start and final process identity disagree")
        _require(record["start_count_state"] == "OBSERVED_ONE" and callback_count == 1,
                 "PROCESS", "No complete actual start evidence", state="UNKNOWN")
        _require(supervisor_elapsed_ms <= 5000, "PROCESS", "Supervisor returned beyond the original allowance", state="TIMEOUT")
        receipt = _inspection(process, command, streams["stdout"], streams["stderr"], started, finished,
                              _thaw(validated._metadata)["expected_resolution"])
        inspection_descriptor = store.write(paths["inspection"], receipt, maximum=LIMITS["inspection_bytes"])
        record["artifacts"]["inspection"] = inspection_descriptor
        record.update(state="COMPLETED", evidence_finalized=True)
        final = store.write(paths["postflight"], record)
    except BaseException as exc:
        if not entered:
            record.update(actual_direct_starts=0, observed_direct_starts=0, start_count_state="PROVEN_ZERO")
        if isinstance(exc, HostInspectionError):
            error = exc
        else:
            error = HostInspectionError("PROCESS" if entered else "EVIDENCE", "Inspection attempt failed",
                                        cause=exc, state=getattr(exc, "state", "UNKNOWN"))
        error.process_record = process
        error.supervisor_exception = failure
        if failure is not None:
            error.details = {**error.details, "supervisor_failure": _failure(failure)}
        if contract_violation is not None:
            error.details = {**error.details, "contract_violation": contract_violation}
        record.update(state=error.state, failure=error.as_dict(), evidence_finalized=False)
        if record["start_count_state"] == "UNKNOWN":
            record["state"] = "UNKNOWN"
        # Even a write/retention failure must attempt the postflight guard,
        # while the original failure/receipt stay attached and immutable.
        if entered and record["postflight"] is None:
            try:
                record["postflight"] = _recheck(validated, check=_Deadline(LIMITS["static_ms"], "DRIFT"))
            except BaseException as post:
                record["postflight"] = {"passed": False, "failure": _failure(post)}
        try:
            store.write(paths["failure"], {"schema": PREFIX + "inspection-failure" + VERSION,
                        "plan": _thaw(validated.descriptor), "command_id": command["id"],
                        "failure": error.as_dict(), "process": process, "observed_start": started_record,
                        "publications": store.publications})
            if record["start_count_state"] == "INVALID_MULTIPLE_STARTS":
                # The normal P07 0/1 sidecar has no valid representation for
                # this violation. Preserve it only as a distinct failed record.
                error.refusal_record = {"attempt": record, "descriptor": None, "evidence_finalized": True,
                                        "contract_violation": error.details["contract_violation"]}
                raise error
            record["evidence_finalized"] = True
            _require(not any(row["destination"] == paths["postflight"] for row in store.publications),
                     "EVIDENCE", "Final attempt publication already has an uncertain outcome; no retry", state="UNKNOWN")
            final = store.write(paths["postflight"], record)
            error.refusal_record = {"attempt": record, "descriptor": final, "evidence_finalized": True}
        except BaseException as evidence:
            if evidence is error and record["start_count_state"] == "INVALID_MULTIPLE_STARTS":
                raise
            record["evidence_finalized"] = False
            error = HostInspectionError("EVIDENCE", "Failure evidence finalization is uncertain", cause=evidence,
                                        process_record=process, state="UNKNOWN", details={"original_failure": error.as_dict()})
            if contract_violation is not None:
                error.details["contract_violation"] = contract_violation
            error.supervisor_exception = failure
            error.refusal_record = {"attempt": record, "descriptor": None, "evidence_finalized": False}
        raise error
    return record, final, inspection_descriptor


def _actual_counts(records):
    observed = sum(row["observed_direct_starts"] for row in records)
    exact = None if any(row["actual_direct_starts"] is None for row in records) else sum(row["actual_direct_starts"] for row in records)
    result = {"direct_starts": {"exact": exact, "observed_lower_bound": observed},
              "attempted_launches": {"exact": None if any(row["start_count_state"] in ("UNKNOWN", "INVALID_MULTIPLE_STARTS") for row in records)
                                     else sum(row["start_count_state"] == "OBSERVED_ONE" for row in records),
                                     "observed_lower_bound": sum(row["observed_direct_starts"] for row in records)},
              "checker_starts": {"exact": 0, "observed_lower_bound": 0}}
    for name in COMMAND_IDS:
        selected = [row for row in records if row["command_id"] == name]
        result[name] = {"exact": selected[0]["actual_direct_starts"] if selected else 0,
                        "observed_lower_bound": selected[0]["observed_direct_starts"] if selected else 0}
    return result


def _host(validated, inspections):
    plan, metadata = _thaw(validated.plan), _thaw(validated._metadata)
    host = {"schema": PREFIX + "host" + VERSION, "observed_at_utc": _utc(),
            "platform": plan["host_static"]["platform"],
            "python": {"executable": plan["author"]["python_descriptor"]["path"], "version": plan["author"]["python_version"],
                       "packages": metadata["packages"]},
            "runtime": {"executable": plan["runtime"]["executable"], "version": NODE_VERSION,
                        "candidate_sha256": NODE["sha256"], "candidate_size_bytes": NODE["size_bytes"],
                        "candidate_mode": NODE["mode"], "source_archive": plan["runtime"]["source_archive"]},
            "files": plan["host_static"]["files"], "aliases": plan["host_static"]["aliases"], "roles": plan["host_static"]["roles"],
            "environment": dict(ENVIRONMENT), "inspections": inspections}
    _validate_host_projection(host, validated)
    return host


def _validate_host_projection(host, validated):
    definitions = _p06_definitions()
    _schema_check(host, definitions["host"], definitions)
    plan = _thaw(validated.plan)
    _require(host["python"] == {"executable": plan["author"]["python_descriptor"]["path"],
             "version": plan["author"]["python_version"], "packages": _thaw(validated._metadata)["packages"]}
             and host["runtime"] == {"executable": plan["runtime"]["executable"], "version": NODE_VERSION,
             "candidate_sha256": NODE["sha256"], "candidate_size_bytes": NODE["size_bytes"], "candidate_mode": NODE["mode"],
             "source_archive": plan["runtime"]["source_archive"]}, "COMPAT", "Projected Python/runtime identity differs")
    for key in ("platform", "files", "aliases", "roles"):
        _require(host[key] == plan["host_static"][key], "COMPAT", "Projected host differs from admitted static fields")
    roles = host["roles"]
    named = set(roles[key] for key in ROLE_SCALARS)
    for key in ROLE_LISTS:
        named.update(roles[key])
    _require(set(host["aliases"]) == named and set(host["files"]) == {row["resolved_path"] for row in host["aliases"].values()},
             "COMPAT", "Projected role/alias/file sets disagree")
    try:
        observed = datetime.fromisoformat(host["observed_at_utc"].replace("Z", "+00:00"))
        _require(observed.tzinfo is not None and observed <= datetime.now(timezone.utc), "COMPAT", "Invalid host timestamp")
        for command in plan["commands"]:
            receipt = _document(host["inspections"][command["id"]], LIMITS["inspection_bytes"], category="COMPAT")
            _schema_check(receipt, definitions["inspection"], definitions)
            projected = _inspection(receipt["process"], command, receipt["stdout"].encode(), receipt["stderr"].encode(),
                                    receipt["started_at_utc"], receipt["finished_at_utc"], _thaw(validated._metadata)["expected_resolution"])
            _require(projected == receipt, "COMPAT", "Inspection envelope differs from exact command projection")
            _require(datetime.fromisoformat(receipt["finished_at_utc"].replace("Z", "+00:00")) <= observed,
                     "COMPAT", "Host predates its inspection receipts")
    except HostInspectionError:
        raise
    except (ValueError, TypeError) as exc:
        raise HostInspectionError("COMPAT", "Invalid projected host time", cause=exc) from exc


def inspect_host(plan_path, expected_plan_sha256, *, observe=False):
    """Static by default; success from observation is explicitly unapproved."""
    _require(type(observe) is bool, "PLAN", "observe must be an explicit boolean")
    validated = validate_inspection_plan(plan_path, expected_plan_sha256)
    plan = _thaw(validated.plan)
    result = {"schema": PREFIX + "inspection-result" + VERSION, "plan": _thaw(validated.descriptor),
              "mode": "observe" if observe else "static", "state": "STATIC_READY", "command_attempts": [],
              "actual_counts": _actual_counts([]), "artifacts": {"source_validation": _thaw(validated._source_reads)},
              "host": None, "evidence_finalized": False, "failures": []}
    if not observe:
        return result
    store, records = None, []
    try:
        store = _EvidenceStore(validated)
        outputs = plan["evidence"]["outputs"]
        result["artifacts"]["reserved"] = store.write(outputs["reserved"], {
            "schema": PREFIX + "inspection-reservation" + VERSION, "plan": _thaw(validated.descriptor),
            "attempt_root": plan["evidence"]["attempt_root"], "owned_directories": store.owned,
            "state": "RESERVED", "expected_direct_starts": 2, "checker_starts": 0})
        preflight = store.write(outputs["preflight"], {"schema": PREFIX + "inspection-preflight" + VERSION,
            "plan": _thaw(validated.descriptor), "source_reads": _thaw(validated._source_reads),
            "binding": _recheck(validated, check=_Deadline(LIMITS["static_ms"], "DRIFT"))})
        result["artifacts"]["preflight"] = preflight
        inspections = {}
        for command in plan["commands"]:
            try:
                record, descriptor, inspection = _run_command(validated, command, store, preflight)
            except HostInspectionError as exc:
                attempt = exc.refusal_record.get("attempt")
                if attempt is not None:
                    records.append(attempt)
                    result["command_attempts"].append(exc.refusal_record.get("descriptor"))
                raise
            records.append(record)
            result["command_attempts"].append(descriptor)
            inspections[command["id"]] = inspection
        publication = _Deadline(LIMITS["publication_ms"], "EVIDENCE")
        _recheck(validated, check=publication)
        host = _host(validated, inspections)
        result["host"] = store.write(outputs["host"], host, maximum=LIMITS["host_bytes"], check=publication)
        result["actual_counts"] = _actual_counts(records)
        _require(result["actual_counts"]["direct_starts"]["exact"] == 2, "PROCESS", "Preparation counts are incomplete")
        # This immutable result is explicitly pending until the final marker
        # binds it. A failed marker must not leave a durable success claim.
        result["state"] = "PENDING_COMPLETION"
        result_descriptor = store.write(outputs["result"], result, check=publication)
        completion = store.write(outputs["completion"], {
            "schema": PREFIX + "inspection-completion" + VERSION, "plan": _thaw(validated.descriptor),
            "state": "OBSERVED_UNAPPROVED", "result": result_descriptor, "host": result["host"],
            "command_attempts": result["command_attempts"], "actual_counts": result["actual_counts"],
            "evidence_finalized": True}, check=publication)
        result.update(state="OBSERVED_UNAPPROVED", evidence_finalized=True)
        result["artifacts"].update(result=result_descriptor, completion=completion)
        return result
    except BaseException as exc:
        error = exc if isinstance(exc, HostInspectionError) else HostInspectionError("EVIDENCE", "Inspection package failed", cause=exc, state="UNKNOWN")
        result.update(state=error.state, host=None, actual_counts=_actual_counts(records), evidence_finalized=False)
        result["failures"].append(error.as_dict())
        if store is not None:
            result["artifacts"]["publication_attempts"] = store.publications
            path = Path(plan["evidence"]["outputs"]["result"])
            if not path.exists() and not path.is_symlink() and not any(row["destination"] == str(path) for row in store.publications):
                try:
                    store.write(path, result)
                except BaseException as final:
                    result["failures"].append(_failure(final))
                    result["state"] = "UNKNOWN"
        error.refusal_record = result
        raise error


def _read_retained(path, *, maximum=16 * 1024 * 1024, check=lambda: None):
    path = _absolute(path, "EVIDENCE")
    if not path.exists():
        return None, None
    raw, binding = _read_file(path, maximum, category="EVIDENCE", check=check)
    descriptor = {"path": str(path), **binding}
    try:
        return _decode(raw, "EVIDENCE"), descriptor
    except HostInspectionError as exc:
        raise HostInspectionError("EVIDENCE", "Retained record is incomplete or malformed", cause=exc,
                                  state="UNKNOWN", details={"raw_descriptor": descriptor}) from exc


def _guard_receipt(validated):
    plan = _thaw(validated.plan)
    return {"passed": True, "plan": _thaw(validated.descriptor), "source_commit": plan["source"]["commit"],
            "boot_id": plan["host_static"]["platform"]["boot_id"]}


def _expected_source_reads(plan):
    outputs = [plan["source"]["root"], plan["source"]["commit"], plan["source"]["tree"], "", ""]
    return [{**command, "stdout": output, "completed": True}
            for command, output in zip(source_commands(plan["source"]), outputs)]


def _reconcile_command(validated, command, preflight, *, check=lambda: None):
    paths = _thaw(validated.plan)["evidence"]["outputs"][command["id"]]
    known, descriptors, faults = {}, {}, []
    for key, path in (("intent", paths["intent"]), ("start", paths["started"]),
                      ("outcome", paths["supervisor_outcome"]["committed"]),
                      ("final", paths["postflight"]), ("failure", paths["failure"])):
        try:
            known[key], descriptors[key] = _read_retained(path, check=check)
        except HostInspectionError as exc:
            known[key], descriptors[key] = None, exc.details.get("raw_descriptor")
            faults.append(exc.as_dict())
    row = _new_attempt(validated, command, None)
    if known["intent"] is not None:
        _require(known["intent"] == _new_attempt(validated, command, preflight), "EVIDENCE", "Intent differs from the frozen command/preflight relation")
    if known["start"] is not None:
        start = known["start"]
        _keys(start, "schema plan command_id process observed_at_utc".split(), "EVIDENCE")
        _require(start["schema"] == PREFIX + "inspection-start" + VERSION and start["plan"] == _thaw(validated.descriptor)
                 and start["command_id"] == command["id"], "EVIDENCE", "Start record belongs to another plan/command")
        process = start["process"]
        _keys(process, set(PROCESS_KEYS) - {"end_monotonic"}, "EVIDENCE")
        _require(process["argv"] == command["argv"] and process["cwd"] == command["cwd"]
                 and process["label"] == command["label"] and process["environment"] == ENVIRONMENT
                 and type(process["pid"]) is int and process["pid"] > 0 and type(process["process_group"]) is int
                 and process["process_group"] == process["pid"]
                 and _number(process["start_monotonic"]) and process["returncode"] is None
                 and process["cleanup"] is None and process["handles_closed"] is False
                 and process["observed_log_bytes"] == process["retained_log_bytes"] == 0 and process["error"] is None,
                 "EVIDENCE", "Retained start is not the fixed command's actual callback")
        _count_observed(row, start["process"])
    if known["outcome"] is not None:
        outcome = known["outcome"]
        required = set("schema plan command_id process supervisor_failure observed_start artifacts faults".split())
        allowed = required | {"decoded_raw_process", "raw_process_unavailable", "stdout_unavailable", "stderr_unavailable"}
        _require(type(outcome) is dict and required <= set(outcome) <= allowed, "EVIDENCE", "Outcome has missing/unknown fields")
        _require(outcome.get("schema") == PREFIX + "inspection-supervisor-outcome" + VERSION
                 and outcome.get("plan") == _thaw(validated.descriptor)
                 and outcome.get("command_id") == command["id"], "EVIDENCE", "Outcome belongs to another plan/command")
        expected_artifacts = {"raw_process": paths["supervisor_outcome"]["raw"], "stdout": paths["stdout"], "stderr": paths["stderr"]}
        _require(type(outcome.get("artifacts")) is dict and set(outcome["artifacts"]) <= set(expected_artifacts),
                 "EVIDENCE", "Outcome has unknown artifact roles")
        for key, descriptor in outcome["artifacts"].items():
            _binding_shape(descriptor, "EVIDENCE", descriptor=True)
            _require(descriptor["path"] == expected_artifacts[key], "EVIDENCE", "Outcome references an unplanned artifact")
            _bound(descriptor["path"], _binding(descriptor), category="EVIDENCE", check=check)
        process = outcome.get("process")
        if known["start"] is None and type(process) is dict and process.get("pid") is not None:
            # Without an earlier actual callback, only a complete, correctly
            # linked final supervisor receipt can establish a positive count.
            _keys(process, PROCESS_KEYS, "EVIDENCE")
            _require(process["argv"] == command["argv"] and process["cwd"] == command["cwd"]
                     and process["label"] == command["label"] and process["environment"] == ENVIRONMENT
                     and type(process["pid"]) is int and process["pid"] > 0 and type(process["process_group"]) is int
                     and process["process_group"] == process["pid"] and _number(process["start_monotonic"])
                     and _number(process["end_monotonic"]) and process["start_monotonic"] <= process["end_monotonic"]
                     and (process["returncode"] is None or type(process["returncode"]) is int)
                     and type(process["handles_closed"]) is bool and type(process["observed_log_bytes"]) is int
                     and type(process["retained_log_bytes"]) is int
                     and process["observed_log_bytes"] >= process["retained_log_bytes"] >= 0,
                     "EVIDENCE", "Outcome-only process is not a complete fixed-command receipt")
            raw_process, raw_descriptor = _read_retained(paths["supervisor_outcome"]["raw"], check=check)
            _require(raw_descriptor is not None and outcome["artifacts"].get("raw_process") == raw_descriptor
                     and raw_process == process == outcome.get("decoded_raw_process"),
                     "EVIDENCE", "Outcome-only process lacks its exact raw supervisor relationship")
            _count_observed(row, process)
        if known["start"] is not None:
            _require(outcome["observed_start"] == known["start"]["process"], "EVIDENCE", "Committed callback differs from retained start")
            if type(outcome["process"]) is dict:
                _require(all(known["start"]["process"].get(key) == outcome["process"].get(key) for key in
                         ("pid", "process_group", "argv", "cwd", "environment", "label", "start_monotonic")),
                         "EVIDENCE", "Retained callback and final process identities disagree")
    if known["failure"] is not None:
        failed = known["failure"]
        _keys(failed, "schema plan command_id failure process observed_start publications".split(), "EVIDENCE")
        _require(failed["schema"] == PREFIX + "inspection-failure" + VERSION
                 and failed["plan"] == _thaw(validated.descriptor) and failed["command_id"] == command["id"],
                 "EVIDENCE", "Failure belongs to another plan/command")
    final = known["final"]
    if final is not None:
        _keys(final, ATTEMPT_KEYS, "EVIDENCE")
        _require(final["schema"] == PREFIX + "inspection-attempt" + VERSION
                 and final["plan"] == _thaw(validated.descriptor) and final["command_id"] == command["id"]
                 and final["expected_argv"] == command["argv"] and type(final["expected_direct_starts"]) is int
                 and final["expected_direct_starts"] == 1 and final["preflight"] == preflight
                 and final["start"] == descriptors["start"] and final["supervisor_process"] == descriptors["outcome"],
                 "EVIDENCE", "Final attempt identity differs")
        counts = (final["actual_direct_starts"], final["observed_direct_starts"], final["start_count_state"])
        _require((final["actual_direct_starts"] is None or type(final["actual_direct_starts"]) is int)
                 and type(final["observed_direct_starts"]) is int
                 and counts in ((0, 0, "PROVEN_ZERO"), (1, 1, "OBSERVED_ONE"), (None, 0, "UNKNOWN")),
                 "EVIDENCE", "Invalid retained exact/observed count relation")
        if known["failure"] is not None:
            _require(final["failure"] == known["failure"]["failure"], "EVIDENCE", "Final refusal and failure record disagree")
        if known["outcome"] is not None:
            _require(final["supervisor_failure"] == known["outcome"]["supervisor_failure"], "EVIDENCE", "Final supervisor failure differs")
            expected_artifacts = dict(known["outcome"]["artifacts"])
            if "inspection" in final["artifacts"]:
                expected_artifacts["inspection"] = final["artifacts"]["inspection"]
            _require(final["artifacts"] == expected_artifacts, "EVIDENCE", "Final and committed raw artifact descriptors disagree")
        if counts[2] == "PROVEN_ZERO":
            _require(row["observed_direct_starts"] == 0 and known["start"] is None and known["outcome"] is None
                     and known["failure"] is not None and final["failure"] is not None
                     and final["state"] != "COMPLETED", "EVIDENCE", "Zero-start refusal lacks its positive refusal evidence")
            row.update(actual_direct_starts=0, observed_direct_starts=0, start_count_state="PROVEN_ZERO")
        elif counts[2] == "OBSERVED_ONE":
            _require(row["observed_direct_starts"] == 1, "EVIDENCE", "Final count has no retained positive start/process evidence")
        else:
            _require(row["observed_direct_starts"] == 0, "EVIDENCE", "Retained lower bound contradicts actual start evidence")
        if final["state"] == "COMPLETED":
            _require(known["start"] is not None and known["outcome"] is not None
                     and final["start"] == descriptors["start"] and final["supervisor_process"] == descriptors["outcome"]
                     and final["evidence_finalized"] is True and final["failure"] is None
                     and final["supervisor_failure"] is None and known["outcome"].get("supervisor_failure") is None
                     and not known["outcome"].get("faults") and final["postflight"] == _guard_receipt(validated)
                     and known["failure"] is None and known["intent"] is not None and preflight is not None,
                     "EVIDENCE", "Completed sidecar lacks complete consistent evidence")
            actual_process = known["outcome"]["process"]
            _require(all(known["start"]["process"].get(key) == actual_process.get(key) for key in
                         ("pid", "process_group", "argv", "cwd", "environment", "label", "start_monotonic")),
                     "EVIDENCE", "Retained start/final identities disagree")
            raw_process, raw_descriptor = _read_retained(paths["supervisor_outcome"]["raw"], check=check)
            _require(raw_process == actual_process == known["outcome"].get("decoded_raw_process"),
                     "EVIDENCE", "Raw and committed process receipt differ")
            _require(known["outcome"]["artifacts"].get("raw_process") == raw_descriptor, "EVIDENCE", "Raw receipt descriptor differs")
            receipt, receipt_descriptor = _read_retained(paths["inspection"], maximum=LIMITS["inspection_bytes"], check=check)
            _require(final["artifacts"].get("inspection") == receipt_descriptor and receipt is not None
                     and receipt["process"] == actual_process, "EVIDENCE", "Inspection is not the retained actual process")
            stdout, stdout_binding = _read_file(paths["stdout"], LIMITS["log_bytes"], category="EVIDENCE", check=check)
            stderr, stderr_binding = _read_file(paths["stderr"], LIMITS["log_bytes"], category="EVIDENCE", check=check)
            _require(known["outcome"]["artifacts"].get("stdout") == {"path": paths["stdout"], **stdout_binding}
                     and known["outcome"]["artifacts"].get("stderr") == {"path": paths["stderr"], **stderr_binding}
                     and _inspection(actual_process, command, stdout, stderr, receipt["started_at_utc"], receipt["finished_at_utc"],
                                     _thaw(validated._metadata)["expected_resolution"]) == receipt,
                     "EVIDENCE", "Inspection does not project the actual retained streams and process")
        row["state"] = final["state"] if final["state"] != "COMPLETED" else "COMPLETED_AS_RECORDED"
    if faults or known["failure"] is not None or final is None:
        row["state"] = "UNKNOWN" if row["start_count_state"] == "UNKNOWN" or faults else "NO_START" if row["start_count_state"] == "PROVEN_ZERO" else "INCOMPLETE_OR_FAILED"
    return {"command_id": command["id"], "actual_direct_starts": row["actual_direct_starts"],
            "observed_direct_starts": row["observed_direct_starts"], "start_count_state": row["start_count_state"],
            "state": row["state"], "records": descriptors, "faults": faults}


def reconcile_attempt(plan_path, expected_plan_sha256, attempt_path):
    """Read retained evidence; no writes, process starts, retry, or promotion.

    No PID absence is treated as completion. This implementation reports only
    the retained record graph; current process-group liveness is unobserved.
    Marker presence cannot prove an earlier parent-directory fsync. Even a
    complete graph has durability_state=UNKNOWN and evidence_finalized=False.
    """
    try:
        validated = _validate(plan_path, expected_plan_sha256, fresh=False, git_reads=False)
        check = _Deadline(LIMITS["static_ms"], "EVIDENCE")
        plan = _thaw(validated.plan)
        root = _absolute(attempt_path, "EVIDENCE")
        _require(str(root) == plan["evidence"]["attempt_root"] and root.is_dir(), "EVIDENCE", "Reconciliation target is not the selected attempt")
        outputs = plan["evidence"]["outputs"]
        reservation, reserved_descriptor = _read_retained(outputs["reserved"], check=check)
        _keys(reservation, "schema plan attempt_root owned_directories state expected_direct_starts checker_starts".split(), "EVIDENCE")
        _require(reservation is not None and reservation.get("plan") == _thaw(validated.descriptor)
                 and reservation.get("attempt_root") == str(root) and reservation["schema"] == PREFIX + "inspection-reservation" + VERSION
                 and reservation["state"] == "RESERVED" and reservation["expected_direct_starts"] == 2 and reservation["checker_starts"] == 0
                 and set(reservation["owned_directories"]) == {str(root), *(str(root / name) for name in COMMAND_IDS)},
                 "EVIDENCE", "Missing or unrelated reservation")
        for name, expected in reservation.get("owned_directories", {}).items():
            path = _absolute(name, "EVIDENCE")
            _require(path == root or path.parent == root and path.name in COMMAND_IDS, "EVIDENCE", "Unplanned owned directory in reservation")
            row = path.lstat()
            _require(stat.S_ISDIR(row.st_mode) and [row.st_dev, row.st_ino, stat.S_IMODE(row.st_mode)] == expected,
                     "EVIDENCE", "Reserved directory identity differs")
        preflight, preflight_descriptor = _read_retained(outputs["preflight"], check=check)
        if preflight is not None:
            _keys(preflight, "schema plan source_reads binding".split(), "EVIDENCE")
            _require(preflight["schema"] == PREFIX + "inspection-preflight" + VERSION
                     and preflight["plan"] == _thaw(validated.descriptor)
                     and preflight["binding"] == _guard_receipt(validated)
                     and preflight["source_reads"] == _expected_source_reads(plan),
                     "EVIDENCE", "Preflight is not the exact plan/source/boot relation")
        commands = [_reconcile_command(validated, command, preflight_descriptor, check=check) for command in plan["commands"]]
        completion, completion_descriptor = _read_retained(outputs["completion"], check=check)
        state = "UNKNOWN"
        if completion is not None:
            _keys(completion, "schema plan state result host command_attempts actual_counts evidence_finalized".split(), "EVIDENCE")
            _require(completion["schema"] == PREFIX + "inspection-completion" + VERSION
                     and completion["plan"] == _thaw(validated.descriptor) and completion["state"] == "OBSERVED_UNAPPROVED"
                     and completion["evidence_finalized"] is True and all(row["state"] == "COMPLETED_AS_RECORDED" for row in commands),
                     "EVIDENCE", "Final marker is incomplete or disagrees with command evidence")
            _binding_shape(completion["result"], "EVIDENCE", descriptor=True)
            _binding_shape(completion["host"], "EVIDENCE", descriptor=True)
            _require(completion["result"]["path"] == outputs["result"] and completion["host"]["path"] == outputs["host"],
                     "EVIDENCE", "Completion refers to an unplanned result or HOST path")
            result = _document(completion["result"], category="EVIDENCE", check=check)
            host = _document(completion["host"], LIMITS["host_bytes"], category="EVIDENCE", check=check)
            _keys(result, "schema plan mode state command_attempts actual_counts artifacts host evidence_finalized failures".split(), "EVIDENCE")
            _require(type(completion["command_attempts"]) is list and len(completion["command_attempts"]) == 2
                     and result["schema"] == PREFIX + "inspection-result" + VERSION
                     and result["mode"] == "observe" and result["evidence_finalized"] is False and result["failures"] == []
                     and result["state"] == "PENDING_COMPLETION" and result["plan"] == completion["plan"]
                     and result["host"] == completion["host"] and result["command_attempts"] == completion["command_attempts"]
                     and completion["actual_counts"] == result["actual_counts"] == _actual_counts(commands)
                     and result["artifacts"] == {"source_validation": preflight["source_reads"],
                                                "reserved": reserved_descriptor, "preflight": preflight_descriptor},
                     "EVIDENCE", "Completion references or counts disagree")
            for command, descriptor in zip(plan["commands"], completion["command_attempts"]):
                _require(descriptor == next(row["records"]["final"] for row in commands if row["command_id"] == command["id"]),
                         "EVIDENCE", "Completion attempt descriptor differs")
            _validate_host_projection(host, validated)
            for command in plan["commands"]:
                path = outputs[command["id"]]["inspection"]
                _require(host["inspections"][command["id"]] == _describe(path, check=check, maximum=LIMITS["inspection_bytes"]),
                         "EVIDENCE", "HOST inspection link differs from the retained command inspection")
            required = {outputs[key] for key in ("reserved", "preflight", "host", "result", "completion")}
            for name in COMMAND_IDS:
                paths = outputs[name]
                required.update(paths[key] for key in ("intent", "started", "stdout", "stderr", "inspection", "postflight"))
                required.update(paths["supervisor_outcome"].values())
            actual, actual_directories = set(), set()
            for path, info, directory in _walk_bounded(root, LIMITS["stage_entries"], check=check, category="EVIDENCE"):
                (actual_directories if directory else actual).add(str(path))
            _require(actual == required and actual_directories == set(reservation["owned_directories"]) - {str(root)},
                     "EVIDENCE", "Completed evidence has missing/extra files or directories")
            state = "OBSERVED_UNAPPROVED_AS_RECORDED"
        check()
        return {"schema": PREFIX + "inspection-reconciliation" + VERSION, "plan": _thaw(validated.descriptor),
                "attempt_root": str(root), "state": state, "commands": commands, "actual_counts": _actual_counts(commands),
                "reserved": reserved_descriptor, "completion": completion_descriptor,
                "current_process_group_state": "NOT_OBSERVED", "writes": 0, "new_preparation_starts": 0,
                "source_git_reads": 0,
                "durability_state": "UNKNOWN", "evidence_finalized": False,
                "approved": False, "relaunch_permitted": False}
    except HostInspectionError as exc:
        raise HostInspectionError("EVIDENCE", "Read-only reconciliation remains unresolved", cause=exc, state="UNKNOWN",
                                  details=exc.details) from exc
    except Exception as exc:
        raise HostInspectionError("EVIDENCE", "Cannot reconcile the retained attempt", cause=exc, state="UNKNOWN") from exc


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise HostInspectionError("PLAN", "Invalid inspection arguments: " + message)


def main(argv=None):
    parser = _Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--observe", action="store_true")
    try:
        args = parser.parse_args(argv)
        result = inspect_host(args.plan, args.plan_sha256, observe=args.observe)
        print(_canonical(result).decode("ascii"))
        return 0
    except HostInspectionError as exc:
        result = {"passed": False, "error": exc.as_dict(), "refusal_record": exc.refusal_record}
        raw = _canonical(result)
        if len(raw) > LIMITS["document_bytes"]:
            raw = _canonical({"passed": False, "error": {"code": exc.code, "reason": exc.reason, "state": exc.state},
                              "evidence_finalized": False, "details": "Outer refusal exceeded its capture bound"})
        print(raw.decode("ascii"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
