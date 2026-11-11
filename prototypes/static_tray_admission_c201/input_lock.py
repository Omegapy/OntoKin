"""C201 input-binding validation only; no launcher or native authorization.

The trusted context is supplied by independent sealing/review infrastructure,
never reconstructed from the candidate lock. This component checks bindings;
it does not discover every dynamic dependency, authenticate reviewers, observe
Git itself, persist the trusted context, or implement the future coordinator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

from .ledger import JOURNAL, MARKER
from .schedule import (PROTOCOL_SHA256, SCHEDULE_ID, SCHEDULE_SHA256, SLOTS,
                       canonical, exact, expected_schedule, validate_schedule)


SCHEMA = "ontokin.c201.executable-input-lock/0.1"
APPROVAL_SCHEMA = "ontokin.c201.input-binding-approval/0.1"
RECEIPT_SCHEMA = "ontokin.c201.input-gate-receipt/0.1"
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_INPUTS = 100000
MAX_FILE_BYTES = 8 * 1024 * 1024 * 1024
MAX_TOTAL_INPUT_BYTES = 16 * 1024 * 1024 * 1024
PROTOCOL_PATH = "docs/engineering/static-tray-admission-c201/ADMISSION.json"
PROTOCOL_REVIEW_PATH = "docs/engineering/static-tray-admission-c201/evidence/protocol-review/REVIEW.json"
PROTOCOL_REVIEW_SHA256 = "80a7076a608b541e7031dc499e3fcefa23d923ab2e4c9b946623ecb54538f37e"
ADMISSION_ROLES = {
    "admission_lock": "prototypes/static_tray_admission_c201/input_lock.py",
    "admission_schedule": "prototypes/static_tray_admission_c201/schedule.py",
    "admission_ledger": "prototypes/static_tray_admission_c201/ledger.py",
    "admission_coordinator": "prototypes/static_tray_admission_c201/coordinator.py",
    "admission_transaction": "prototypes/static_tray_admission_c201/transaction.py",
    "admission_format_check": "prototypes/static_tray_admission_c201/format_check.py",
    "admission_node_probe": "prototypes/static_tray_admission_c201/readback.mjs",
}
HOST_ROLES = ("python_executable", "python_stdlib", "blender_executable",
              "blender_distribution", "dynamic_loader", "shared_libraries",
              "node_executable", "node_packages", "node_loader")
GATES = ("implementation_review", "cpu_controls", "current_host")
STAGES = ("construction", "receiving", "node")
NATIVE_FLAGS = ("-b", "--factory-startup", "--disable-autoexec", "--threads", "2",
                "--python-exit-code", "1", "--python-use-system-env")
NODE_FLAGS = ("--no-addons", "--max-old-space-size=256")
NODE_ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                    "TZ": "UTC", "UV_THREADPOOL_SIZE": "2"}
NATIVE_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TZ": "UTC",
    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2", "PYTHONSAFEPATH": "1",
    "LIBGL_ALWAYS_SOFTWARE": "1", "LP_NUM_THREADS": "2",
}


class InputLockError(ValueError):
    """A rejected binding, with a stable category for CPU rejection controls."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _require(condition, code, message):
    if not condition:
        raise InputLockError(code, message)


def _keys(value, names, code="SCHEMA"):
    _require(type(value) is dict and value.keys() == set(names), code,
             "Missing, extra, or wrong-type fields")


def _digest(value, length=64):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def _text(value):
    return type(value) is str and 0 < len(value) <= 4096 and not any(c in value for c in "\x00\r\n")


def _absolute(value):
    _require(_text(value) and value.startswith("/") and not value.startswith("//")
             and str(PurePosixPath(value)) == value
             and ".." not in PurePosixPath(value).parts, "PATH", "Expected normalized absolute path")
    return Path(value)


def _relative(value):
    _require(_text(value) and not value.startswith("/") and value not in (".", "..")
             and str(PurePosixPath(value)) == value and ".." not in PurePosixPath(value).parts,
             "PATH", "Expected normalized relative input path")
    return value


def _directory_fd(path):
    """Open every component without following a symbolic-link ancestor."""
    path = _absolute(str(path))
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _directory(path, *, empty=False):
    descriptor = _directory_fd(path)
    try:
        info = os.fstat(descriptor)
        _require(not empty or not os.listdir(descriptor), "PATH", "Output/store directory is not empty")
        return info.st_dev, info.st_ino
    finally:
        os.close(descriptor)


def _regular(path, *, limit, binding=None, keep=False):
    """Bounded nonblocking read of one unaliased regular file through held dirs."""
    path = _absolute(str(path))
    parent = _directory_fd(path.parent)
    descriptor = None
    try:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=parent)
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and before.st_size <= limit, "FILE", "Unsafe, aliased or overlarge file")
        if binding is not None:
            _require(before.st_size == binding["size_bytes"]
                     and stat.S_IMODE(before.st_mode) == binding["mode"],
                     "FILE", "Input size or mode differs")
        digest, chunks, size = hashlib.sha256(), [], 0
        while True:
            block = os.read(descriptor, min(1048576, limit + 1 - size))
            if not block:
                break
            size += len(block)
            _require(size <= limit, "FILE", "Input grew beyond its bound")
            digest.update(block)
            if keep:
                chunks.append(block)
        after = os.fstat(descriptor)
        final = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        identity = lambda i: (i.st_dev, i.st_ino, i.st_size, i.st_mtime_ns, i.st_ctime_ns,
                              i.st_nlink, stat.S_IMODE(i.st_mode))
        _require(identity(before) == identity(after) == identity(final) and size == before.st_size,
                 "FILE", "Input changed during verification")
        if binding is not None:
            _require(digest.hexdigest() == binding["sha256"], "FILE", "Input hash differs")
        return b"".join(chunks) if keep else digest.hexdigest()
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def _json(data):
    _require(type(data) is bytes and len(data) <= MAX_JSON_BYTES, "JSON", "JSON exceeds bound")

    def pairs(rows):
        result = {}
        for key, value in rows:
            _require(key not in result, "JSON", "Duplicate JSON field")
            result[key] = value
        return result

    def invalid(_):
        raise InputLockError("JSON", "Nonfinite JSON value")

    try:
        value = json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, InputLockError):
            raise
        raise InputLockError("JSON", "Invalid bounded JSON") from exc
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        _require(depth <= 32, "JSON", "JSON nesting exceeds bound")
        if type(item) is dict:
            stack.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            stack.extend((v, depth + 1) for v in item)
    return value


@dataclass(frozen=True)
class TrustedContext:
    """Independent sealed facts; its persistence/authentication is an external gate.

    All fields are immutable scalars or tuples. There is deliberately no
    from_lock constructor, approval producer, or automatic dependency scanner.
    """
    repository_root: str
    host_root: str
    source_commit: str
    source_tree: str
    lock_sha256: str
    approval_sha256: str
    closure_sha256: str
    launch_plan_sha256: str
    authority_path: str
    authority_device: int
    authority_inode: int
    producer: str
    reviewer: str
    purpose: str
    gate_issuers: tuple[str, str, str]


@dataclass(frozen=True)
class ValidationResult:
    """Snapshot of verified bindings, never a capability to start work."""
    lock_sha256: str
    approval_sha256: str
    source_commit: str
    source_tree: str
    purpose: str
    input_count: int
    authority_path: str
    authority_device: int
    authority_inode: int
    native_start_authorized: bool = field(default=False, init=False)
    native_readiness: bool = field(default=False, init=False)
    admission_completed: bool = field(default=False, init=False)


def closure_digest(lock):
    """Canonical binding subject; this calculation does not establish completeness."""
    return hashlib.sha256(canonical({k: lock[k] for k in ("source", "inputs", "roles", "dependencies")})).hexdigest()


def launch_plan_digest(lock):
    return hashlib.sha256(canonical({k: lock[k] for k in ("commands", "stores", "outputs", "environments")})).hexdigest()


def native_environment(root):
    """Exact inherited clean variables with an explicitly bound per-slot root."""
    root = _absolute(root)
    return {**NATIVE_ENVIRONMENT,
            **{key: str(root / name) for key, name in (
                ("HOME", "home"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache"),
                ("TMPDIR", "tmp"), ("BLENDER_USER_CONFIG", "blender-config"),
                ("BLENDER_USER_SCRIPTS", "blender-scripts"))}}


def _binding(value):
    _keys(value, ("root", "path", "size_bytes", "sha256", "mode"), "INPUT")
    _require(value["root"] in ("repository", "host"), "INPUT", "Unknown input root")
    _relative(value["path"])
    _require(type(value["size_bytes"]) is int and 0 <= value["size_bytes"] <= MAX_FILE_BYTES
             and _digest(value["sha256"]) and type(value["mode"]) is int
             and 0 <= value["mode"] <= 0o777, "INPUT", "Invalid exact file binding")


def _context(context):
    _require(type(context) is TrustedContext, "CONTEXT", "A separately trusted context is required")
    for field in ("source_commit", "source_tree"):
        _require(_digest(getattr(context, field), 40), "CONTEXT", "Invalid trusted Git identity")
    for field in ("lock_sha256", "approval_sha256", "closure_sha256", "launch_plan_sha256"):
        _require(_digest(getattr(context, field)), "CONTEXT", "Invalid trusted digest")
    _require(context.purpose in ("fixture-only", "production-inputs")
             and _text(context.producer) and _text(context.reviewer)
             and context.producer != context.reviewer, "CONTEXT", "Independent identities are required")
    _require(type(context.gate_issuers) is tuple and len(context.gate_issuers) == 3
             and all(_text(v) for v in context.gate_issuers)
             and context.gate_issuers[0] != context.producer,
             "CONTEXT", "Implementation review must be independently issued")
    for value in (context.authority_device, context.authority_inode):
        _require(type(value) is int and value >= 0, "CONTEXT", "Invalid trusted authority identity")
    for value in (context.repository_root, context.host_root, context.authority_path):
        _absolute(value)


def _check_disjoint(paths):
    for index, path in enumerate(paths):
        for other in paths[index + 1:]:
            _require(path != other and path not in other.parents and other not in path.parents,
                     "PATH", "Input, authority, store and stage-output roots must be disjoint")


def _validate(lock_path, approval_path, context):
    _context(context)
    raw = _regular(lock_path, limit=MAX_JSON_BYTES, keep=True)
    approval_raw = _regular(approval_path, limit=MAX_JSON_BYTES, keep=True)
    lock_hash, approval_hash = hashlib.sha256(raw).hexdigest(), hashlib.sha256(approval_raw).hexdigest()
    _require(lock_hash == context.lock_sha256 and approval_hash == context.approval_sha256,
             "DIGEST", "Candidate differs from independently reviewed exact bytes")
    lock, approval = _json(raw), _json(approval_raw)
    _keys(lock, ("schema", "purpose", "producer", "source", "protocol_sha256", "schedule",
                 "limits", "inputs", "roles", "dependencies", "commands", "stores", "outputs",
                 "authority", "host", "gate_receipts", "environments"))
    _require(lock["schema"] == SCHEMA and lock["purpose"] == context.purpose
             and lock["producer"] == context.producer, "SCHEMA", "Lock identity differs")
    _keys(lock["source"], ("commit", "tree", "files"), "SOURCE")
    _require(lock["source"]["commit"] == context.source_commit
             and lock["source"]["tree"] == context.source_tree,
             "SOURCE", "Source differs from independently observed committed revision")
    _require(lock["protocol_sha256"] == PROTOCOL_SHA256, "PROTOCOL", "Protocol identity differs")
    validate_schedule(lock["schedule"])
    repo, host = _absolute(context.repository_root), _absolute(context.host_root)
    _directory(repo)
    _directory(host)
    protocol_raw = _regular(repo / PROTOCOL_PATH, limit=MAX_JSON_BYTES, keep=True)
    _require(hashlib.sha256(protocol_raw).hexdigest() == PROTOCOL_SHA256,
             "PROTOCOL", "Approved protocol bytes differ")
    protocol = _json(protocol_raw)
    review_raw = _regular(repo / PROTOCOL_REVIEW_PATH, limit=MAX_JSON_BYTES, keep=True)
    _require(hashlib.sha256(review_raw).hexdigest() == PROTOCOL_REVIEW_SHA256,
             "PROTOCOL", "Independent protocol review bytes differ")
    review = _json(review_raw)
    _require(exact(lock["limits"], protocol["limits"]), "LIMITS", "Original limits must be exact")

    inputs = lock["inputs"]
    _require(type(inputs) is dict and 0 < len(inputs) <= MAX_INPUTS, "INPUT", "Invalid input inventory")
    for name, binding in inputs.items():
        _binding(binding)
        _require(name == binding["root"] + ":" + binding["path"], "INPUT", "Input key differs from path")
    _require(sum(row["size_bytes"] for row in inputs.values()) <= MAX_TOTAL_INPUT_BYTES,
             "INPUT", "Cumulative input inventory exceeds the validation bound")
    source_files = sorted(name for name, row in inputs.items() if row["root"] == "repository")
    _require(exact(lock["source"]["files"], source_files), "SOURCE", "Committed-source inventory differs")
    frozen = [*review["documentBindings"], *protocol["normative_bindings"],
              *protocol["qualified_role_bindings"].values(),
              *protocol["public_task"]["source_closures"]["ontokin"],
              *protocol["public_task"]["source_closures"]["direct-python"]]
    frozen.append({"path": PROTOCOL_REVIEW_PATH, "sha256": PROTOCOL_REVIEW_SHA256,
                   "size_bytes": len(review_raw)})
    for binding in frozen:
        actual = inputs.get("repository:" + binding["path"])
        _require(actual is not None and actual["sha256"] == binding["sha256"]
                 and actual["size_bytes"] == binding["size_bytes"],
                 "FROZEN", "Required protocol, source or qualified binding is missing or changed")
    fixed_roles = {name: row["path"] for name, row in protocol["qualified_role_bindings"].items()
                   if not name.startswith("historical_")}
    fixed_roles.update(ADMISSION_ROLES)
    _keys(lock["roles"], (*fixed_roles, *HOST_ROLES), "ROLE")
    for role, path in fixed_roles.items():
        _require(exact(lock["roles"][role], ["repository:" + path]), "ROLE", "Required role path differs")
    for role, references in lock["roles"].items():
        _require(type(references) is list and len(references) > 0
                 and all(type(v) is str and v in inputs for v in references)
                 and len(references) == len(set(references)), "ROLE", "Missing or duplicate role input")
        if role in HOST_ROLES:
            _require(all(inputs[v]["root"] == "host" for v in references), "ROLE", "Host role uses wrong root")
        if role.endswith("_executable"):
            _require(len(references) == 1 and inputs[references[0]]["mode"] & 0o111,
                     "ROLE", "Executable role must name one executable file")
        if role == "node_loader":
            _require(len(references) == 1, "ROLE", "Node loader role must name one file")
    dependencies = lock["dependencies"]
    _keys(dependencies, inputs, "DEPENDENCY")
    for name, references in dependencies.items():
        _require(type(references) is list and all(type(v) is str and v in inputs for v in references)
                 and len(references) == len(set(references)) and name not in references,
                 "DEPENDENCY", "Unresolved, duplicate or self dependency")
    reached = set()
    frontier = (["repository:" + row["path"] for row in frozen]
                + [name for refs in lock["roles"].values() for name in refs])
    while frontier:
        name = frontier.pop()
        if name not in reached:
            reached.add(name)
            frontier.extend(dependencies[name])
    _require(reached == inputs.keys(), "DEPENDENCY", "Unreachable extra input or missing closure member")
    _require(closure_digest(lock) == context.closure_sha256,
             "DEPENDENCY", "Dependency closure differs from independently sealed inventory")
    for binding in inputs.values():
        root = repo if binding["root"] == "repository" else host
        _regular(root / binding["path"], limit=binding["size_bytes"], binding=binding)

    _keys(lock["authority"], ("schedule_id", "path", "device", "inode"), "AUTHORITY")
    expected_authority = {"schedule_id": SCHEDULE_ID, "path": context.authority_path,
                          "device": context.authority_device, "inode": context.authority_inode}
    _require(exact(lock["authority"], expected_authority), "AUTHORITY", "Persistent authority differs")
    authority = _absolute(context.authority_path)
    _require(_directory(authority) == (context.authority_device, context.authority_inode),
             "AUTHORITY", "Persistent authority filesystem identity changed")
    authority_fd = _directory_fd(authority)
    try:
        for marker in (MARKER, JOURNAL):
            try:
                os.stat(marker, dir_fd=authority_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise InputLockError("REPLAY", "Existing invocation or journal prevents another invocation")
    finally:
        os.close(authority_fd)
    slots = tuple(slot.name for slot in SLOTS)
    _keys(lock["stores"], slots, "PATH")
    _keys(lock["outputs"], slots, "PATH")
    _keys(lock["environments"], slots, "PATH")
    _keys(lock["gate_receipts"], GATES, "APPROVAL")
    # The host namespace may be / because real loader/runtime files span roots.
    # Bind actual input files, not the namespace directory, against write roots.
    paths = [repo, authority]
    identities = {_directory(path) for path in paths}
    _require(len(identities) == len(paths), "PATH", "Root directory identities alias")
    for slot in slots:
        _keys(lock["outputs"][slot], STAGES, "PATH")
        for value in (lock["stores"][slot], lock["environments"][slot], *lock["outputs"][slot].values()):
            path = _absolute(value)
            identity = _directory(path, empty=True)
            _require(identity not in identities, "PATH", "Store/output directory identity aliases")
            identities.add(identity)
            paths.append(path)
    _check_disjoint(paths)
    for binding in (*inputs.values(), *lock["gate_receipts"].values()):
        _binding(binding)
        if binding["root"] == "host":
            file_path = host / binding["path"]
            _require(all(file_path != path and path not in file_path.parents for path in paths),
                     "PATH", "Host or gate input overlaps repository, authority or writable roots")
    _keys(lock["commands"], slots, "COMMAND")
    for slot in slots:
        _keys(lock["commands"][slot], STAGES, "COMMAND")
        for stage in STAGES:
            command = lock["commands"][slot][stage]
            _keys(command, ("argv", "environment", "cwd", "output"), "COMMAND")
            argv = command["argv"]
            _require(type(argv) is list and 2 <= len(argv) <= 128 and all(_text(v) for v in argv)
                     and not any("{" in v or "}" in v or "$" in v for v in argv),
                     "COMMAND", "Commands must be bounded expanded argument vectors")
            executable_role = "node_executable" if stage == "node" else "blender_executable"
            script_role = {"construction": "constructor", "receiving": "receiver",
                           "node": "admission_node_probe"}[stage]
            executable = inputs[lock["roles"][executable_role][0]]
            script = inputs[lock["roles"][script_role][0]]
            output = _absolute(lock["outputs"][slot][stage])
            if stage == "node":
                loader = inputs[lock["roles"]["node_loader"][0]]
                expected_argv = [str(host / executable["path"]), *NODE_FLAGS,
                                 "--experimental-loader", str(host / loader["path"]),
                                 str(repo / script["path"]), "--job", str(output / "job.json")]
                environment = NODE_ENVIRONMENT
            else:
                expected_argv = [str(host / executable["path"]), *NATIVE_FLAGS, "--python",
                                 str(repo / script["path"]), "--", "--job", str(output / "job.json")]
                environment = native_environment(lock["environments"][slot])
            _require(exact(argv, expected_argv), "COMMAND", "Expanded child command differs from fixed safe policy")
            _require(exact(command["environment"], environment)
                     and command["cwd"] == str(repo)
                     and command["output"] == lock["outputs"][slot][stage],
                     "COMMAND", "Clean environment, working directory or output differs")
    _require(launch_plan_digest(lock) == context.launch_plan_sha256,
             "COMMAND", "Launch plan differs from independent review")
    _keys(lock["host"], ("target", "mode"), "HOST")
    target = {k: v for k, v in protocol["intended_dependencies"].items()
              if k not in ("pin_source", "current_host_verified",
                           "complete_distribution_loader_shared_library_stdlib_environment_verification_required")}
    _require(exact(lock["host"]["target"], target)
             and lock["host"]["mode"] == ("fixture-only" if context.purpose == "fixture-only" else "current-host"),
             "HOST", "Host target or evidence classification differs")

    _keys(lock["gate_receipts"], GATES, "APPROVAL")
    for index, gate in enumerate(GATES):
        binding = lock["gate_receipts"][gate]
        _binding(binding)
        root = repo if binding["root"] == "repository" else host
        receipt = _json(_regular(root / binding["path"], limit=MAX_JSON_BYTES, binding=binding, keep=True))
        expected = {"schema": RECEIPT_SCHEMA, "gate": gate, "purpose": context.purpose,
                    "issuer": context.gate_issuers[index], "passed": True,
                    "source_commit": context.source_commit, "source_tree": context.source_tree,
                    "protocol_sha256": PROTOCOL_SHA256, "schedule_sha256": SCHEDULE_SHA256,
                    "closure_sha256": context.closure_sha256}
        _require(exact(receipt, expected), "APPROVAL", "Missing, stale or incomplete gate receipt")
    expected_approval = {
        "schema": APPROVAL_SCHEMA, "purpose": context.purpose,
        "decision": "FIXTURE_BINDINGS_ONLY" if context.purpose == "fixture-only" else "APPROVE_INPUT_BINDINGS_ONLY",
        "producer": context.producer, "reviewer": context.reviewer,
        "source_commit": context.source_commit, "source_tree": context.source_tree,
        "lock_sha256": lock_hash, "protocol_sha256": PROTOCOL_SHA256,
        "schedule_sha256": SCHEDULE_SHA256, "closure_sha256": context.closure_sha256,
        "launch_plan_sha256": context.launch_plan_sha256, "authority": expected_authority,
        "ceilings": expected_schedule()["ceilings"],
        "gate_receipts": {gate: lock["gate_receipts"][gate]["sha256"] for gate in GATES},
        "native_start_authorized": False,
    }
    _require(exact(approval, expected_approval), "APPROVAL", "Independent exact-input approval differs")
    return ValidationResult(lock_hash, approval_hash, context.source_commit, context.source_tree,
                            context.purpose, len(inputs), context.authority_path,
                            context.authority_device, context.authority_inode)


def validate_input_lock(lock_path, approval_path, *, context):
    """Validate actual current files without starting children or writing receipts.

    Callers must independently establish/persist TrustedContext, and later
    revalidate before use. A passing snapshot cannot close a mutation window,
    reserve a stage, grant readiness, or substitute for the ledger/coordinator.
    """
    try:
        return _validate(lock_path, approval_path, context)
    except InputLockError:
        raise
    except OSError as exc:
        raise InputLockError("FILESYSTEM", "Missing, unsafe or inaccessible bound path") from exc
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        raise InputLockError("SCHEMA", "Malformed input or schedule binding") from exc
