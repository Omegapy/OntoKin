"""C201 source/transaction compatibility, with no process-launch entry point.

This component consumes pinned bindings and on-disk stage evidence. The caller
still owns authenticated process observations, the one-use ledger, native
readiness, deadlines around children, Node checks and D01/D03 progression.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
import fcntl
import hashlib
import math
import os
from pathlib import Path
import stat
import time
import uuid

from . import input_lock
from .schedule import SLOTS, canonical, exact
from ..static_tray_v01.errors import PROFILE, TrayError
from ..static_tray_v01.lock import independent_modules
from ..static_tray_v01.receive_check import compare
from ..static_tray_v01.sources import lower_source
from ..static_tray_v01.store import seal_candidate, verify_candidate
from ..static_tray_v01.supervisor import Clock, LIMITS, Stop, inventory


RECEIPT_SCHEMA = "ontokin.c201.transaction-receipt/0.1"
PROCESS_SCHEMA = "ontokin.c201.process-observation/0.1"
SOURCE_SCHEMA = "ontokin.c201.prepared-source/0.1"
MARKER = ".c201-transaction-reserved.json"
_BINDING_TOKEN = object()
ARTIFACTS = ("raw.glb", "final.glb", "scene.blend")
EQUALITY_FILES = ("canonical-input.json", "raw.glb", "final.glb")
BUILD_FILES = {"canonical-input.json", "source-provenance.json", "job.json",
               "raw.glb", "final.glb", "scene.blend", "native-result.json",
               "construction.stdout.log", "construction.stderr.log",
               "native-startup.json", "construction.process.json"}
BUILD_ADDED = {"independent-audit.json", "equality-checks.json", "process-observation.json"}
RECEIVE_FILES = {"job.json", "observations.json", "review.png",
                 "receiving.stdout.log", "receiving.stderr.log", "receiving.process.json"}
RECEIVE_ADDED = {"receiving-check.json", "process-observation.json"}


class TransactionError(Stop):
    """A component rejection or an explicitly uncertain post-commit outcome."""

    def __init__(self, code, reason, state="REJECTED"):
        super().__init__("C201-" + code, reason, state)


def _require(condition, code, message):
    if not condition:
        raise TransactionError(code, message)


def _boundary(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except TransactionError:
            raise
        except (input_lock.InputLockError, TrayError, Stop) as exc:
            raise TransactionError("BINDING", str(exc), getattr(exc, "state", "REJECTED")) from exc
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
            raise TransactionError("BINDING", "Unsafe, missing or malformed transaction input: " + str(exc)) from exc
    return checked


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _read(path, limit=LIMITS["result_bytes"]):
    return input_lock._regular(Path(path), limit=limit, keep=True)


def _json(path):
    return input_lock._json(_read(path))


def _identity(path):
    return input_lock._directory(Path(path))


def _write(path, value, *, binary=False):
    path = Path(path)
    data = value if binary else canonical(value)
    _require(type(data) is bytes and len(data) <= LIMITS["output_bytes"], "RESOURCE", "Write exceeds allowance")
    parent = input_lock._directory_fd(path.parent)
    descriptor = None
    try:
        descriptor = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)


def _pointer(store):
    """Exact bytes, including absence; revision equality alone is insufficient."""
    parent = input_lock._directory_fd(store)
    try:
        try:
            os.stat("state.json", dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return None
    finally:
        os.close(parent)
    return _read(Path(store) / "state.json", 32768)


def _files(path, expected):
    _identity(path)
    rows = inventory(path)
    _require(set(rows) == set(expected), "CLOSURE", "Transaction file inventory is incomplete or has extra files")
    for name in rows:
        _read(Path(path) / name, LIMITS["output_bytes"])
    return rows


def _sealed(path, digest, expected):
    _files(path, set(expected) | {"closure.json"})
    raw = _read(Path(path) / "closure.json")
    _require(_sha(raw) == digest, "CLOSURE", "Retained closure manifest differs")
    manifest = verify_candidate(path)
    _require(manifest.get("schema") == "ontokin.static-tray.candidate/0.1.0"
             and set(manifest) == {"schema", "files"}, "CLOSURE", "Unexpected sealed closure schema")
    _require(stat.S_IMODE((Path(path) / "closure.json").stat().st_mode) == 0o444,
             "CLOSURE", "Closure manifest is not sealed")
    return raw


@dataclass(frozen=True)
class AcceptedTransaction:
    """Restorable transaction evidence, never a schedule-completion capability."""
    slot: str
    receipt_sha256: str
    state_bytes: bytes
    native_start_authorized: bool = field(default=False, init=False)
    native_readiness: bool = field(default=False, init=False)
    admission_completed: bool = field(default=False, init=False)


@dataclass(frozen=True)
class PreparedTransaction:
    """Immutable prepared bytes; accepted source always names an actual closure."""
    slot: str
    route: str
    source_identity: str
    canonical_bytes: bytes
    source_files: tuple[tuple[str, bytes], ...]
    source_path: str
    prior: tuple[AcceptedTransaction, ...]
    reservation_bytes: bytes
    _session: object = field(repr=False, compare=False)
    _clock: object = field(repr=False, compare=False)
    native_start_authorized: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ConstructedTransaction:
    prepared: PreparedTransaction
    closure_sha256: str
    audit_sha256: str
    receiving_end: float
    _session: object = field(repr=False, compare=False)


class TransactionBindings:
    """In-memory snapshot from C205; crash recovery cannot invent a fresh run."""

    def __init__(self, lock_bytes, approval_bytes, context, validation, *, _token=None):
        _require(_token is _BINDING_TOKEN and type(validation) is input_lock.ValidationResult
                 and validation.purpose == context.purpose
                 and context.purpose in ("fixture-only", "production-inputs"), "BINDING",
                 "Only the validated factory may construct this component session")
        self._creation_token = _token
        self._lock_bytes = lock_bytes
        self._approval_bytes = approval_bytes
        self._context = context
        self.validation = validation
        lock = self._lock()
        self._identities = {p: _identity(p) for p in (
            context.repository_root, context.authority_path, *lock["stores"].values(),
            *lock["environments"].values())}
        self._outputs = {p: _identity(p) for rows in lock["outputs"].values() for p in rows.values()}
        self._prepared = {}
        self._constructed = {}
        self._terminal = set()

    def _lock(self):
        return input_lock._json(self._lock_bytes)

    def _revalidate(self):
        _session(self)
        lock, context = self._lock(), self._context
        _require(_sha(self._lock_bytes) == context.lock_sha256
                 and _sha(self._approval_bytes) == context.approval_sha256,
                 "BINDING", "Session binding identity differs")
        for path, identity in self._identities.items():
            _require(_identity(path) == identity, "PATH", "A bound directory was replaced")
        for row in (*lock["inputs"].values(), *lock["gate_receipts"].values()):
            root = context.repository_root if row["root"] == "repository" else context.host_root
            input_lock._regular(Path(root) / row["path"], limit=input_lock.MAX_FILE_BYTES, binding=row)
        return lock


@_boundary
def bind_transactions(lock_path, approval_path, *, context):
    """Validate and retain exact inputs without granting native authorization."""
    validation = input_lock.validate_input_lock(lock_path, approval_path, context=context)
    lock_raw = _read(lock_path, input_lock.MAX_JSON_BYTES)
    approval_raw = _read(approval_path, input_lock.MAX_JSON_BYTES)
    _require(_sha(lock_raw) == validation.lock_sha256 and _sha(approval_raw) == validation.approval_sha256,
             "BINDING", "Lock or approval changed after validation")
    return TransactionBindings(lock_raw, approval_raw, context, validation, _token=_BINDING_TOKEN)


def _session(value):
    _require(type(value) is TransactionBindings, "BINDING", "Validated transaction bindings are required")
    _require(value._creation_token is _BINDING_TOKEN
             and type(value.validation) is input_lock.ValidationResult
             and value.validation.purpose == value._context.purpose
             and value._context.purpose in ("fixture-only", "production-inputs"),
             "BINDING", "This component requires a validated session")
    return value


def _slot(name):
    rows = [s for s in SLOTS if s.name == name]
    _require(type(name) is str and len(rows) == 1, "REFERENCE", "Unknown C201 slot")
    return rows[0]


def _source_names(route):
    return {"source.json", "main.ok", "tray.ok"} if route == "ontokin" else {"source.json", "main.py", "tray.py"}


def _source_files(path, route):
    _files(path, _source_names(route))
    return {name: _read(Path(path) / name, 32768) for name in sorted(_source_names(route))}


def _build_names(route):
    return BUILD_FILES | {"source/" + n for n in _source_names(route)}


def _process(session, slot, stage, value, directory):
    lock = session._lock()
    keys = {"schema", "purpose", "slot", "stage", "input_lock_sha256", "command",
            "process_id", "started_monotonic", "completed_monotonic", "returncode",
            "handles_closed", "cleanup", "supervisor_record_sha256"}
    _require(type(value) is dict and value.keys() == keys, "PROCESS", "Incomplete process observation")
    _require(value["schema"] == PROCESS_SCHEMA and value["purpose"] == session.validation.purpose
             and value["slot"] == slot and value["stage"] == stage
             and value["input_lock_sha256"] == session.validation.lock_sha256
             and exact(value["command"], lock["commands"][slot][stage]),
             "PROCESS", "Unrelated process observation")
    _require(type(value["process_id"]) is int and value["process_id"] > 0
             and type(value["returncode"]) is int and value["returncode"] == 0
             and value["handles_closed"] is True, "PROCESS", "Process did not complete with closed handles")
    cleanup = value["cleanup"]
    _require(type(cleanup) is dict and cleanup.keys() == {"passed", "process_group_absent", "reaped"}
             and all(v is True for v in cleanup.values()), "CLEANUP", "Cleanup is failed, incomplete or unknown")
    for key in ("started_monotonic", "completed_monotonic"):
        _require(type(value[key]) in (int, float) and math.isfinite(value[key]) and value[key] >= 0,
                 "PROCESS", "Invalid process time observation")
    elapsed = value["completed_monotonic"] - value["started_monotonic"]
    _require(0 <= elapsed <= LIMITS[stage + "_ms"] / 1000, "PROCESS", "Observed stage allowance was exceeded")
    raw = _read(Path(directory) / (stage + ".process.json"))
    _require(_sha(raw) == value["supervisor_record_sha256"], "PROCESS", "Supervisor receipt binding differs")
    observed = input_lock._json(raw)
    required = {"argv", "cwd", "environment", "label", "start_monotonic", "pid", "process_group",
                "returncode", "observed_log_bytes", "retained_log_bytes", "cleanup", "handles_closed",
                "error", "end_monotonic"}
    _require(type(observed) is dict and observed.keys() == required, "PROCESS", "Incomplete supervisor receipt")
    command = lock["commands"][slot][stage]
    _require(exact(observed["argv"], command["argv"]) and exact(observed["environment"], command["environment"])
             and observed["cwd"] == command["cwd"] == command["output"] == lock["outputs"][slot][stage]
             and observed["label"] == stage
             and type(observed["pid"]) is int and observed["pid"] == value["process_id"]
             and type(observed["process_group"]) is int and observed["process_group"] == observed["pid"]
             and type(observed["returncode"]) is int and observed["returncode"] == value["returncode"]
             and observed["handles_closed"] is True and observed["error"] is None
             and type(observed["start_monotonic"]) in (int, float)
             and type(observed["end_monotonic"]) in (int, float)
             and observed["start_monotonic"] == value["started_monotonic"]
             and observed["end_monotonic"] == value["completed_monotonic"],
             "PROCESS", "Supervisor receipt is unrelated to the slot/stage observation")
    cleanup = observed["cleanup"]
    _require(type(cleanup) is dict and cleanup.keys() == {"passed", "elapsed_ms", "process_group_absent", "reaped"}
             and all(cleanup[k] is True for k in ("passed", "process_group_absent", "reaped"))
             and type(cleanup["elapsed_ms"]) in (int, float) and math.isfinite(cleanup["elapsed_ms"])
             and 0 <= cleanup["elapsed_ms"] <= LIMITS["cleanup_ms"], "CLEANUP", "Underlying cleanup receipt failed")
    log_size = sum(len(_read(Path(directory) / (stage + suffix), LIMITS["log_bytes"]))
                   for suffix in (".stdout.log", ".stderr.log"))
    _require(type(observed["observed_log_bytes"]) is int and type(observed["retained_log_bytes"]) is int
             and observed["observed_log_bytes"] == observed["retained_log_bytes"] == log_size
             and log_size <= LIMITS["log_bytes"], "PROCESS", "Retained process logs differ from receipt")
    return canonical(value)


def _provenance(prepared):
    return {"schema": SOURCE_SCHEMA, "purpose": prepared._session.validation.purpose,
            "slot": prepared.slot, "route": prepared.route,
            "input_lock_sha256": prepared._session.validation.lock_sha256,
            "source_identity": prepared.source_identity, "source_path": prepared.source_path,
            "references": _slot(prepared.slot).references()}


def _construction_job(prepared):
    session = prepared._session
    stage = Path(session._lock()["outputs"][prepared.slot]["construction"])
    settings = Path(session._context.repository_root) / "prototypes/static_tray_v01/export-settings.json"
    return {"output_directory": str(stage), "record_path": str(stage / "canonical-input.json"),
            "record_sha256": _sha(prepared.canonical_bytes), "settings_path": str(settings),
            "settings_sha256": _sha(_read(settings))}


def _receiving_job(prepared, candidate):
    session = prepared._session
    stage = Path(session._lock()["outputs"][prepared.slot]["receiving"])
    settings = Path(session._context.repository_root) / "prototypes/static_tray_v01/import-settings.json"
    return {"output_directory": str(stage), "candidate": str(candidate),
            "input_sha256": {n: _sha(_read(candidate / n, LIMITS["output_bytes"])) for n in ("scene.blend", "final.glb")},
            "settings_path": str(settings), "settings_sha256": _sha(_read(settings)),
            "expected_world_bounds": independent_modules({})["expected"].expected_bounds("Q01")}


def _native_receipt(prepared, directory, audit):
    session = prepared._session
    native = _json(Path(directory) / "native-result.json")
    startup_raw = _read(Path(directory) / "native-startup.json")
    startup = input_lock._json(startup_raw)
    job = _construction_job(prepared)
    settings = _json(job["settings_path"])
    settings["filepath"] = str(Path(job["output_directory"]) / "raw.glb")
    policy = {"exporter_sha256": "82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e",
              "operator_context": "EXEC_DEFAULT", "operator_property_count": len(settings),
              "debug": {"debug": False, "debug_python": False, "debug_value": 0},
              "requested_log_level": -1, "resolved_log_level": 20, "action_filter": False,
              "action_filter_policy": "initialize-empty-properties-before-explicit-false",
              "omitted_operator_properties": []}
    python = startup.get("python_startup")
    _require(type(python) is dict and python.keys() == {"flags", "dont_write_bytecode", "sys_path", "executable",
                "prefix", "base_prefix", "python_version"}, "RECEIPT", "Incomplete embedded startup receipt")
    required_flags = {"isolated": 0, "ignore_environment": 0, "no_user_site": 1, "safe_path": True,
                      "hash_randomization": 0, "dont_write_bytecode": 1}
    _require(type(python["flags"]) is dict and all(exact(python["flags"].get(k), v) for k, v in required_flags.items())
             and python["dont_write_bytecode"] is True and type(python["sys_path"]) is list
             and all(type(v) is str for v in python["sys_path"])
             and all(type(python[k]) is str and python[k] for k in ("executable", "prefix", "base_prefix", "python_version")),
             "RECEIPT", "Embedded startup policy differs")
    expected_startup = {"schema": "ontokin.static-tray.native-startup/0.1.0", "phase": "BEFORE_EXPORT",
                        "delivery_state": "NOT_EXPORTED", "blender_version": [4, 5, 3], "build_hash": "67807e1800cc",
                        "python_startup": python, "operator_settings": settings, "exporter_policy": policy,
                        "action_filter_initialization": {"action_count": 0, "scene_count": 1, "filter_count": 0, "active_index": 0},
                        "record_sha256": job["record_sha256"], "settings_sha256": job["settings_sha256"]}
    _require(exact(startup, expected_startup), "RECEIPT", "Native startup/settings/exporter receipt differs")
    exporter = {**policy, "logging_observed": {"logger_level": 20, "error_logger_level": 40},
                "action_filter_properties_removed": True, "startup_receipt_sha256": _sha(startup_raw)}
    artifacts = {n: {"sha256": _sha(_read(Path(directory) / n, LIMITS["output_bytes"])),
                     "size_bytes": (Path(directory) / n).stat().st_size} for n in ARTIFACTS}
    expected_native = {"schema": "ontokin.static-tray.native/0.1.0", "passed": True,
                       "blender_version": [4, 5, 3], "build_hash": "67807e1800cc", "python_version": python["python_version"],
                       "python_startup": python, "threads": 2, "operator_settings": settings, "exporter_policy": exporter,
                       "objects": sorted(audit["nodes"]), "record_sha256": job["record_sha256"], "physics_world": False,
                       "artifacts": artifacts}
    _require(exact(native, expected_native), "RECEIPT", "Native result, startup hash or artifact receipt differs")
    return native


def _receipt_paths(session, slot):
    store = Path(session._lock()["stores"][slot])
    return store, store / "objects" / slot, store / "objects" / (slot + "-receiving"), store / "objects" / (slot + "-receipt")


def _accepted(session, handle):
    _require(type(handle) is AcceptedTransaction, "REFERENCE", "A retained transaction handle is required")
    slot = _slot(handle.slot)
    store, candidate, receiving, receipt_dir = _receipt_paths(session, slot.name)
    state_raw = _pointer(store)
    _require(state_raw is not None and state_raw == handle.state_bytes,
             "POINTER", "Accepted pointer differs from retained exact bytes")
    state = input_lock._json(state_raw)
    receipt_raw = _read(receipt_dir / "transaction.json")
    _require(_sha(receipt_raw) == handle.receipt_sha256, "RECEIPT", "Accepted transaction receipt changed")
    receipt = input_lock._json(receipt_raw)
    expected_state = {"schema": "ontokin.c201.accepted-pointer/0.1", "slot": slot.name,
                      "revision": "sha256:" + handle.receipt_sha256,
                      "receipt": "objects/" + slot.name + "-receipt",
                      "receipt_sha256": handle.receipt_sha256,
                      "receipt_closure_sha256": state.get("receipt_closure_sha256"),
                      "candidate": "objects/" + slot.name,
                      "closure_sha256": receipt.get("closure_sha256"),
                      "receiving_candidate": "objects/" + slot.name + "-receiving",
                      "receiving_closure_sha256": receipt.get("receiving_closure_sha256"),
                      "input_lock_sha256": session.validation.lock_sha256}
    _require(exact(state, expected_state) and state_raw == canonical(state), "POINTER", "Accepted pointer is unrelated or noncanonical")
    _sealed(receipt_dir, state["receipt_closure_sha256"], {"transaction.json"})
    _require(receipt.get("schema") == RECEIPT_SCHEMA and receipt.get("purpose") == session.validation.purpose
             and receipt.get("slot") == slot.name and receipt.get("route") == slot.route
             and exact(receipt.get("references"), slot.references())
             and receipt.get("input_lock_sha256") == session.validation.lock_sha256
             and receipt.get("state") == "TRANSACTION_ACCEPTED"
             and receipt.get("native_readiness") is False and receipt.get("admission_completed") is False,
             "RECEIPT", "Unrelated or incomplete accepted receipt")
    _sealed(candidate, receipt["closure_sha256"], _build_names(slot.route) | BUILD_ADDED)
    _sealed(receiving, receipt["receiving_closure_sha256"], RECEIVE_FILES | RECEIVE_ADDED)
    for stage, directory in (("construction", candidate), ("receiving", receiving)):
        _process(session, slot.name, stage, _json(directory / "process-observation.json"), directory)
    files = _source_files(candidate / "source", slot.route)
    _require({name: _sha(data) for name, data in files.items()} == receipt["source_sha256"],
             "SOURCE", "Accepted source/dependency closure differs")
    _require(_sha(_read(candidate / "canonical-input.json")) == receipt["canonical_sha256"],
             "SOURCE", "Accepted canonical bytes differ")
    _require(_json(candidate / "independent-audit.json").get("passed") is True
             and _json(receiving / "receiving-check.json").get("passed") is True,
             "RECEIPT", "Retained measurement validation did not pass")
    _require(_pointer(store) == state_raw, "POINTER", "Accepted pointer changed during validation")
    return receipt, candidate


def _prior(session, slot, accepted):
    expected = tuple(s.name for s in SLOTS[:SLOTS.index(slot)])
    _require(type(accepted) is tuple and all(type(h) is AcceptedTransaction for h in accepted)
             and tuple(h.slot for h in accepted) == expected,
             "REFERENCE", "Prior accepted transactions are missing, extra, reordered or duplicated")
    return {handle.slot: _accepted(session, handle) for handle in accepted}


def _prepared(value, *, constructed=False):
    _require(type(value) is PreparedTransaction, "BINDING", "An actual prepared transaction is required")
    session = _session(value._session)
    _require(session._prepared.get(value.slot) is value and value.slot not in session._terminal,
             "REPLAY", "Prepared transaction is foreign, already completed or stopped")
    if not constructed:
        _require(value.slot not in session._constructed, "REPLAY", "Construction is already sealed")
    session._revalidate()
    slot = _slot(value.slot)
    _prior(session, slot, value.prior)
    store = Path(session._lock()["stores"][slot.name])
    _require(_read(store / MARKER) == value.reservation_bytes, "REPLAY", "Reservation marker differs")
    _require(_pointer(store) is None, "POINTER", "Fresh slot store has an unexpected accepted pointer")
    return session, slot, store


@_boundary
def prepare_transaction(bindings, slot, *, route, references, accepted=()):
    """Materialize editable source only; ledger/Node/control gates remain external."""
    clock = Clock()
    session = _session(bindings)
    lock = session._revalidate()
    selected = _slot(slot)
    _require(route == selected.route and exact(references, selected.references()),
             "REFERENCE", "Route, predecessor, equality or regeneration reference differs")
    _require(slot not in session._prepared and slot not in session._terminal,
             "REPLAY", "Slot already prepared or stopped")
    priors = _prior(session, selected, accepted)
    store = Path(lock["stores"][slot])
    _require(not os.listdir(store), "POINTER", "C201 requires a new empty per-slot store")
    for stage, name in lock["outputs"][slot].items():
        _require(_identity(name) == session._outputs[name] and not os.listdir(name),
                 "PATH", "Bound stage output must retain its identity and be empty")
    protocol = _json(Path(session._context.repository_root) / input_lock.PROTOCOL_PATH)
    if selected.accepted_source_reference is None:
        source = Path(session._context.repository_root) / "fixtures/static_tray_v01/native/Q01" / route
    else:
        source = priors[selected.accepted_source_reference][1] / "source"
    files = _source_files(source, route)
    frozen = {Path(row["path"]).name: row for row in protocol["public_task"]["source_closures"][route]}
    _require(files.keys() == frozen.keys() and all(
        len(raw) == frozen[name]["size_bytes"] and _sha(raw) == frozen[name]["sha256"]
        for name, raw in files.items()), "SOURCE", "Source is not the frozen accepted Q01 closure")
    lowered = lower_source(route, source / "source.json", PROFILE,
                           check=lambda: clock.check(clock.started + LIMITS["construction_ms"] / 1000))
    _require(lowered.files == {n: raw for n, raw in files.items() if n != "source.json"},
             "SOURCE", "Source changed during lowering")
    _require(_source_files(source, route) == files, "SOURCE", "Source changed during preparation")
    _prior(session, selected, accepted)
    marker = canonical({"schema": "ontokin.c201.transaction-reservation/0.1", "slot": slot,
                        "purpose": session.validation.purpose, "input_lock_sha256": session.validation.lock_sha256,
                        "references": references})
    _write(store / MARKER, marker, binary=True)
    prepared = PreparedTransaction(slot, route, lowered.provenance["candidate_identity"],
                                   lowered.canonical_bytes, tuple(sorted(files.items())), str(source),
                                   accepted, marker, session, clock)
    session._prepared[slot] = prepared
    try:
        stage = Path(lock["outputs"][slot]["construction"])
        (stage / "source").mkdir()
        for name, raw in files.items():
            _write(stage / "source" / name, raw, binary=True)
        _write(stage / "canonical-input.json", lowered.canonical_bytes, binary=True)
        _write(stage / "source-provenance.json", _provenance(prepared))
        _write(stage / "job.json", _construction_job(prepared))
    except BaseException:
        session._terminal.add(slot)
        raise
    return prepared


@_boundary
def seal_construction(prepared, *, process):
    """Validate actual output, retain it, and prepare the receiver's exact job."""
    session, slot, store = _prepared(prepared)
    try:
        clock = prepared._clock
        construction_end = clock.started + LIMITS["construction_ms"] / 1000
        clock.check(construction_end)
        lock = session._lock()
        stage = Path(lock["outputs"][slot.name]["construction"])
        _require(_identity(stage) == session._outputs[str(stage)], "PATH", "Construction directory was replaced")
        _files(stage, _build_names(slot.route))
        _require(_source_files(stage / "source", slot.route) == dict(prepared.source_files)
                 and _read(stage / "canonical-input.json") == prepared.canonical_bytes,
                 "SOURCE", "Prepared source or canonical input changed")
        _require(_read(stage / "job.json") == canonical(_construction_job(prepared))
                 and _read(stage / "source-provenance.json") == canonical(_provenance(prepared)),
                 "RECEIPT", "Prepared job or provenance changed")
        process_raw = _process(session, slot.name, "construction", process, stage)
        native = _json(stage / "native-result.json")
        _require(native.get("passed") is True and native.get("record_sha256") == _sha(prepared.canonical_bytes)
                 and type(native.get("artifacts")) is dict and native["artifacts"].keys() == set(ARTIFACTS),
                 "RECEIPT", "Native receipt is incomplete or bound to unrelated source")
        for name in ARTIFACTS:
            data = _read(stage / name, LIMITS["glb_bytes"] if name.endswith(".glb") else LIMITS["output_bytes"])
            _require(exact(native["artifacts"][name], {"sha256": _sha(data), "size_bytes": len(data)}),
                     "RECEIPT", "Native artifact bytes differ from receipt")
        _require(_read(stage / "raw.glb", LIMITS["glb_bytes"]) == _read(stage / "final.glb", LIMITS["glb_bytes"]),
                 "EQUALITY", "Raw and final GLB must be identical")
        modules = independent_modules({})
        rules = _json(Path(session._context.repository_root) / "prototypes/static_tray_v01/delivery-rules.json")
        audit = modules["reader"].audit(stage / "final.glb", "Q01", None, rules)
        _require(audit.get("passed") is True, "GEOMETRY", "Independent GLB measurement failed")
        _native_receipt(prepared, stage, audit)
        priors = _prior(session, slot, prepared.prior)
        equality = []
        for reference in slot.equality_references:
            prior = priors[reference][1]
            hashes = {}
            for name in EQUALITY_FILES:
                a, b = _read(stage / name, LIMITS["glb_bytes"]), _read(prior / name, LIMITS["glb_bytes"])
                _require(a == b, "EQUALITY", "Exact paired or regenerated bytes differ: " + name)
                hashes[name] = _sha(a)
            equality.append({"reference": reference, "exact_files": hashes})
        _write(stage / "independent-audit.json", audit)
        _write(stage / "equality-checks.json", equality)
        _write(stage / "process-observation.json", process_raw, binary=True)
        _prepared(prepared)
        candidate, digest = seal_candidate(stage, store, slot.name)
        _sealed(candidate, digest, _build_names(slot.route) | BUILD_ADDED)
        receiving = Path(lock["outputs"][slot.name]["receiving"])
        _require(_identity(receiving) == session._outputs[str(receiving)] and not os.listdir(receiving),
                 "PATH", "Receiving directory changed or is not empty")
        _write(receiving / "job.json", _receiving_job(prepared, candidate))
        clock.check(construction_end)
        constructed = ConstructedTransaction(prepared, digest, _sha(canonical(audit)),
                                               clock.stage(LIMITS["receiving_ms"]), session)
        session._constructed[slot.name] = constructed
        return constructed
    except BaseException:
        session._terminal.add(slot.name)
        raise


def _promote(session, prepared, state, clock):
    """Full-pointer conditional commit, with uncertainty retained after replace."""
    store = Path(session._lock()["stores"][prepared.slot])
    parent = input_lock._directory_fd(store)
    guard = None
    temp = ".c201-state-" + uuid.uuid4().hex
    replaced = False
    replacement_attempted = False
    try:
        guard = os.open(".promotion-lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK,
                        0o600, dir_fd=parent)
        info = os.fstat(guard)
        _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "PATH", "Unsafe promotion guard")
        deadline = clock.stage(LIMITS["promotion_ms"])
        while True:
            clock.check(deadline)
            try:
                fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(0.01)
        _require(_identity(store) == session._identities[str(store)], "PATH", "Store identity changed")
        _require(_pointer(store) is None, "POINTER", "Exact empty predecessor changed before promotion")
        _prior(session, _slot(prepared.slot), prepared.prior)
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical(state))
            stream.flush()
            os.fsync(stream.fileno())
        clock.check(deadline)
        _require(_pointer(store) is None, "POINTER", "Accepted pointer changed before commit")
        replacement_attempted = True
        os.replace(temp, "state.json", src_dir_fd=parent, dst_dir_fd=parent)
        replaced = True
        os.fsync(parent)
        observed = _pointer(store)
        _require(observed == canonical(state), "POINTER", "Promoted pointer readback differs")
        clock.check(deadline)
        return observed
    except BaseException as exc:
        observed_raw = None
        observation_failed = False
        try:
            observed_raw = _pointer(store)
        except BaseException:
            observation_failed = True
        if replaced or (replacement_attempted and (observed_raw is not None or observation_failed)):
            error = TransactionError("PROMOTION", "Pointer was replaced; outcome requires read-only reconciliation", "UNKNOWN")
            error.intended_state = state
            try:
                error.observed_state = input_lock._json(observed_raw) if observed_raw is not None else None
            except BaseException:
                error.observed_state = None
            raise error from exc
        raise
    finally:
        try:
            os.unlink(temp, dir_fd=parent)
        except FileNotFoundError:
            pass
        if guard is not None:
            os.close(guard)
        os.close(parent)


@_boundary
def complete_transaction(constructed, *, process):
    """Validate receiver measurements/cleanup, seal receipts, then conditionally commit.

    The returned transaction acceptance does not certify Node, D01/D03, image
    review, true process provenance, native readiness or admission completion.
    """
    _require(type(constructed) is ConstructedTransaction, "BINDING", "A sealed construction is required")
    prepared = constructed.prepared
    session, slot, store = _prepared(prepared, constructed=True)
    _require(constructed._session is session and session._constructed.get(slot.name) is constructed,
             "REPLAY", "Construction handle is foreign or stale")
    clock = prepared._clock
    _require(type(clock) is Clock, "BINDING", "The original bounded supervisor Clock is required")
    promoted = False
    try:
        clock.check(constructed.receiving_end)
        lock = session._lock()
        _, candidate, _, _ = _receipt_paths(session, slot.name)
        _sealed(candidate, constructed.closure_sha256, _build_names(slot.route) | BUILD_ADDED)
        audit_raw = _read(candidate / "independent-audit.json")
        _require(_sha(audit_raw) == constructed.audit_sha256, "RECEIPT", "Independent audit changed")
        receiving = Path(lock["outputs"][slot.name]["receiving"])
        _require(_identity(receiving) == session._outputs[str(receiving)], "PATH", "Receiving directory was replaced")
        _files(receiving, RECEIVE_FILES)
        _require(_read(receiving / "job.json") == canonical(_receiving_job(prepared, candidate)),
                 "RECEIPT", "Receiving job or settings binding changed")
        process_raw = _process(session, slot.name, "receiving", process, receiving)
        observations = _json(receiving / "observations.json")
        inputs = {n: _sha(_read(candidate / n, LIMITS["output_bytes"])) for n in ("scene.blend", "final.glb")}
        _require(exact(observations.get("input_sha256"), inputs), "RECEIPT", "Receiver observed unrelated candidate bytes")
        measured = compare(observations, input_lock._json(audit_raw))
        _require(measured.get("passed") is True, "RECEIVING", "Receiving measurements failed")
        _write(receiving / "receiving-check.json", measured)
        _write(receiving / "process-observation.json", process_raw, binary=True)
        _prepared(prepared, constructed=True)
        receiving_candidate, receiving_digest = seal_candidate(receiving, store, slot.name + "-receiving")
        _sealed(receiving_candidate, receiving_digest, RECEIVE_FILES | RECEIVE_ADDED)
        _sealed(candidate, constructed.closure_sha256, _build_names(slot.route) | BUILD_ADDED)
        receipt = {"schema": RECEIPT_SCHEMA, "purpose": session.validation.purpose,
                   "state": "TRANSACTION_ACCEPTED", "slot": slot.name, "route": slot.route,
                   "references": slot.references(), "input_lock_sha256": session.validation.lock_sha256,
                   "source_identity": prepared.source_identity,
                   "source_sha256": {n: _sha(raw) for n, raw in prepared.source_files},
                   "canonical_sha256": _sha(prepared.canonical_bytes),
                   "closure_sha256": constructed.closure_sha256,
                   "receiving_closure_sha256": receiving_digest,
                   "native_readiness": False, "admission_completed": False,
                   "pending_gates": ["actual-delivery-node", "schedule-controls", "visual-review", "native-admission"]}
        receipt_raw = canonical(receipt)
        receipt_stage = store / (".receipt-" + slot.name)
        receipt_stage.mkdir()
        _write(receipt_stage / "transaction.json", receipt_raw, binary=True)
        _, receipt_digest = seal_candidate(receipt_stage, store, slot.name + "-receipt")
        state = {"schema": "ontokin.c201.accepted-pointer/0.1", "slot": slot.name,
                 "revision": "sha256:" + _sha(receipt_raw), "receipt": "objects/" + slot.name + "-receipt",
                 "receipt_sha256": _sha(receipt_raw), "receipt_closure_sha256": receipt_digest,
                 "candidate": "objects/" + slot.name, "closure_sha256": constructed.closure_sha256,
                 "receiving_candidate": "objects/" + slot.name + "-receiving",
                 "receiving_closure_sha256": receiving_digest, "input_lock_sha256": session.validation.lock_sha256}
        clock.check(constructed.receiving_end)
        state_bytes = _promote(session, prepared, state, clock)
        promoted = True
        handle = AcceptedTransaction(slot.name, _sha(receipt_raw), state_bytes)
        _accepted(session, handle)
        _prior(session, slot, prepared.prior)
        clock.check()
        return handle
    except BaseException as exc:
        committed = promoted
        if "state" in locals():
            try:
                committed = committed or _pointer(store) == canonical(state)
            except BaseException:
                committed = True
        if committed and not (isinstance(exc, TransactionError) and exc.state == "UNKNOWN"):
            error = TransactionError("FINALIZATION", "Post-promotion verification failed; no rollback or retry", "UNKNOWN")
            error.intended_state = state
            try:
                error.observed_state = input_lock._json(_pointer(store))
            except BaseException:
                error.observed_state = None
            raise error from exc
        raise
    finally:
        session._terminal.add(slot.name)


@_boundary
def inspect_accepted(bindings, accepted):
    """Read-only exact receipt/closure/pointer verification; never retries a stage."""
    session = _session(bindings)
    session._revalidate()
    receipt, _ = _accepted(session, accepted)
    return receipt
