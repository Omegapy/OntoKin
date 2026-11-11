"""C201 readback job and retained-result bindings, with no process launcher.

This component verifies supplied observations against an actual accepted closure.
It cannot authenticate their producer, execute the probe, advance the ledger, or
grant native readiness, family admission, or authority to start the next slot.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import wraps
import hashlib
import math
import os
from pathlib import Path

from . import input_lock, transaction as tx
from .schedule import PROTOCOL_SHA256, SCHEDULE_SHA256, canonical, exact


JOB_SCHEMA = "ontokin.c201.readback-job/0.1"
PROBE_SCHEMA = "ontokin.c201.readback-probe/0.1"
SCOPE = "Khronos format and Three.js CPU import observations; no browser, GPU, render or simulation claim"
NAMING = "Three.js sanitizes Object3D.name; original names and semantic IDs remain checked without normalization"
LIMITS = {"outer_ms": 30000, "child_work_ms": 28000, "cleanup_ms": 2000,
          "glb_bytes": 8388608, "result_bytes": 4194304, "log_bytes": 4194304}
CHECKS = {
    "khronos": {"version": "2.0.0-dev.3.10", "format": "glb", "uri": "final.glb",
                "writeTimestamp": False, "maxIssues": 1000, "allowed_errors": 0,
                "allowed_warnings": 0, "ignoredIssues": [], "external_resources": "rejected"},
    "three": {"version": "0.186.1", "revision": "186", "position_tolerance_m": 0.000005,
              "matrix_tolerance": 0.000001, "node_count": 14, "mesh_count": 12,
              "animation_count": 0, "scene_count": 1, "camera_count": 0,
              "external_resources": "rejected", "textures": "rejected",
              "unsupported_objects": "rejected", "naming": NAMING},
}
OUTPUTS = {"job": "job.json", "probe": "probe.json", "process": "node.process.json",
           "stdout": "node.stdout.log", "stderr": "node.stderr.log"}
_TOKEN = object()


class ReadbackError(tx.TransactionError):
    """A rejected binding or an unknown interrupted observation check."""

    def __init__(self, code, reason, state="REJECTED"):
        super().__init__("READBACK-" + code, reason, state)


def _require(condition, code, reason):
    if not condition:
        raise ReadbackError(code, reason)


def _boundary(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ReadbackError:
            raise
        except (tx.TransactionError, tx.Stop, tx.TrayError) as exc:
            raise ReadbackError("BINDING", str(exc), getattr(exc, "state", "REJECTED")) from exc
        except (input_lock.InputLockError, OSError, ValueError, TypeError, KeyError,
                AttributeError, OverflowError, RecursionError) as exc:
            raise ReadbackError("BINDING", "Missing, changed or malformed readback input: " + str(exc)) from exc
    return checked


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _read(path, maximum=LIMITS["result_bytes"]):
    return input_lock._regular(Path(path), limit=maximum, keep=True)


def _number(value):
    _require(type(value) in (int, float) and math.isfinite(value), "MEASUREMENT", "Nonfinite or nonnumeric measurement")
    return value


def _equal(actual, expected):
    """JSON numeric equality permits 1/1.0, but never bool/numeric substitution."""
    if type(expected) in (int, float):
        return type(actual) in (int, float) and math.isfinite(actual) and actual == expected
    if type(expected) is list:
        return type(actual) is list and len(actual) == len(expected) and all(_equal(a, b) for a, b in zip(actual, expected))
    if type(expected) is dict:
        return type(actual) is dict and actual.keys() == expected.keys() and all(_equal(actual[k], v) for k, v in expected.items())
    return type(actual) is type(expected) and actual == expected


@dataclass(frozen=True)
class PreparedReadback:
    slot: str
    job_bytes: bytes
    accepted: tx.AcceptedTransaction
    _owner: object = field(repr=False, compare=False)
    node_start_authorized: bool = field(default=False, init=False)
    native_start_authorized: bool = field(default=False, init=False)
    native_readiness: bool = field(default=False, init=False)
    admission_completed: bool = field(default=False, init=False)
    next_slot_authorized: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ReadbackEvidence:
    """Binding consistency only; these are not authenticated execution receipts."""
    slot: str
    purpose: str
    accepted_revision: str
    accepted_pointer_sha256: str
    job_sha256: str
    probe_sha256: str
    process_observation_sha256: str
    output_bindings: tuple[tuple[str, int, str], ...]
    measurement_count: int
    state: str = field(default="BINDINGS_VERIFIED", init=False)
    authenticated_execution: bool = field(default=False, init=False)
    node_start_authorized: bool = field(default=False, init=False)
    native_start_authorized: bool = field(default=False, init=False)
    native_readiness: bool = field(default=False, init=False)
    admission_completed: bool = field(default=False, init=False)
    next_slot_authorized: bool = field(default=False, init=False)


class ReadbackBindings:
    """One in-memory component session; durable invocation control is external."""

    def __init__(self, transactions, *, _token=None):
        _require(_token is _TOKEN, "BINDING", "Use the validated binding factory")
        self._token = _token
        self._transactions = transactions
        self._prepared = {}
        self._terminal = set()
        self._stopped = False


def _owner(value):
    _require(type(value) is ReadbackBindings and value._token is _TOKEN,
             "BINDING", "Validated readback bindings are required")
    tx._session(value._transactions)
    return value


@_boundary
def bind_readbacks(transactions):
    """Retain a validated transaction context without reserving or starting work."""
    tx._session(transactions)._revalidate()
    return ReadbackBindings(transactions, _token=_TOKEN)


def _job(owner, slot, accepted):
    session = owner._transactions
    lock = session._revalidate()
    selected = tx._slot(slot)
    _require(type(accepted) is tx.AcceptedTransaction and accepted.slot == slot,
             "REFERENCE", "Readback must name its exact accepted C201 slot")
    receipt, candidate = tx._accepted(session, accepted)
    state = input_lock._json(accepted.state_bytes)
    stage = Path(lock["outputs"][slot]["node"])
    _require(tx._identity(stage) == session._outputs[str(stage)], "PATH", "Node stage directory was replaced")
    artifact = _read(candidate / "final.glb", LIMITS["glb_bytes"])
    audit_raw = _read(candidate / "independent-audit.json")
    audit = input_lock._json(audit_raw)
    _require(audit.get("passed") is True and audit.get("case") == "Q01"
             and audit.get("artifact_sha256") == _sha(artifact), "AUDIT", "Passed audit does not bind the actual accepted GLB")
    job = {"schema": JOB_SCHEMA, "purpose": session.validation.purpose,
           "slot": slot, "route": selected.route, "case": "Q01", "scope": SCOPE,
           "source": lock["source"], "protocol_sha256": PROTOCOL_SHA256,
           "schedule_sha256": SCHEDULE_SHA256,
           "input_lock_sha256": session.validation.lock_sha256,
           "approval_sha256": session.validation.approval_sha256,
           "accepted_revision": state["revision"], "accepted_pointer_sha256": _sha(accepted.state_bytes),
           "transaction_receipt_sha256": accepted.receipt_sha256,
           "construction_closure_sha256": receipt["closure_sha256"],
           "receiving_closure_sha256": receipt["receiving_closure_sha256"],
           "accepted_source_identity": receipt["source_identity"],
           "artifact": {"path": str(candidate / "final.glb"), "size_bytes": len(artifact), "sha256": _sha(artifact)},
           "audit": {"path": str(candidate / "independent-audit.json"), "size_bytes": len(audit_raw), "sha256": _sha(audit_raw)},
           "command": lock["commands"][slot]["node"],
           "outputs": {role: str(stage / name) for role, name in OUTPUTS.items()},
           "checks": input_lock._json(canonical(CHECKS)), "limits": dict(LIMITS),
           "node_start_authorized": False, "native_readiness": False,
           "admission_completed": False, "next_slot_authorized": False}
    return job, audit


@_boundary
def prepare_readback(bindings, slot, *, accepted):
    """Write one exact job in the bound empty stage; do not reserve a process."""
    owner = _owner(bindings)
    _require(not owner._stopped and slot not in owner._prepared,
             "REPLAY", "This binding session is stopped or this slot already has a job")
    job, _ = _job(owner, slot, accepted)
    stage = Path(job["outputs"]["job"]).parent
    _require(not os.listdir(stage), "OUTPUT", "Node stage must be empty before job preparation")
    raw = canonical(job)
    _require(len(raw) <= LIMITS["result_bytes"], "RESOURCE", "Job exceeds its byte allowance")
    prepared = PreparedReadback(slot, raw, accepted, owner)
    owner._prepared[slot] = prepared
    try:
        tx._write(stage / OUTPUTS["job"], raw, binary=True)
        _require(_read(stage / OUTPUTS["job"]) == raw, "JOB", "Written job readback differs")
        _require(canonical(_job(owner, slot, accepted)[0]) == raw, "JOB", "Accepted inputs changed during preparation")
    except BaseException:
        owner._stopped = True
        owner._terminal.add(slot)
        raise
    return prepared


def _prepared(value):
    _require(type(value) is PreparedReadback, "BINDING", "An actual prepared readback is required")
    owner = _owner(value._owner)
    _require(owner._prepared.get(value.slot) is value, "REPLAY", "Foreign or reconstructed readback handle")
    job, audit = _job(owner, value.slot, value.accepted)
    _require(canonical(job) == value.job_bytes and _read(job["outputs"]["job"]) == value.job_bytes,
             "JOB", "Job or its accepted input bindings changed")
    return owner, job, audit


@_boundary
def inspect_readback_job(prepared):
    """Revalidate and return a fresh job object, including after a stopped check."""
    return _prepared(prepared)[1]


def _outputs(job):
    stage = Path(job["outputs"]["job"]).parent
    _require(set(os.listdir(stage)) == set(OUTPUTS.values()), "OUTPUT", "Missing or extra readback outputs")
    result = {}
    for role, path in job["outputs"].items():
        maximum = LIMITS["log_bytes"] if role in ("stdout", "stderr") else LIMITS["result_bytes"]
        result[role] = _read(path, maximum)
    _require(len(result["stdout"]) + len(result["stderr"]) <= LIMITS["log_bytes"],
             "RESOURCE", "Combined Node logs exceed the fixed allowance")
    return result


def _process(owner, job, raw, observation, log_size):
    keys = {"schema", "purpose", "slot", "stage", "input_lock_sha256", "command", "process_id",
            "started_monotonic", "completed_monotonic", "returncode", "handles_closed", "cleanup",
            "supervisor_record_sha256", "requested_limits", "effective_limits"}
    _require(type(observation) is dict and observation.keys() == keys, "PROCESS", "Incomplete Node observation")
    expected = {"schema": tx.PROCESS_SCHEMA, "purpose": job["purpose"], "slot": job["slot"],
                "stage": "node", "input_lock_sha256": job["input_lock_sha256"],
                "command": job["command"], "returncode": 0, "handles_closed": True,
                "cleanup": {"passed": True, "process_group_absent": True, "reaped": True},
                "supervisor_record_sha256": _sha(raw), "requested_limits": LIMITS, "effective_limits": LIMITS}
    _require(all(exact(observation[k], v) for k, v in expected.items()), "PROCESS", "Failed, unknown or unrelated Node observation")
    _require(type(observation["process_id"]) is int and observation["process_id"] > 0,
             "PROCESS", "Missing actual process identity observation")
    start, end = (_number(observation[k]) for k in ("started_monotonic", "completed_monotonic"))
    _require(0 <= start <= end and (end - start) * 1000 <= LIMITS["outer_ms"],
             "PROCESS", "Observed Node outer allowance was exceeded")
    record = input_lock._json(raw)
    record_keys = {"argv", "cwd", "environment", "label", "start_monotonic", "pid", "process_group",
                   "returncode", "observed_log_bytes", "retained_log_bytes", "cleanup", "handles_closed",
                   "error", "end_monotonic"}
    _require(type(record) is dict and record.keys() == record_keys, "PROCESS", "Incomplete supervisor receipt")
    command = job["command"]
    expected_record = {"argv": command["argv"], "cwd": command["cwd"], "environment": command["environment"],
                       "label": "node", "pid": observation["process_id"], "process_group": observation["process_id"],
                       "returncode": 0, "observed_log_bytes": log_size, "retained_log_bytes": log_size,
                       "handles_closed": True, "error": None}
    _require(all(exact(record[k], v) for k, v in expected_record.items())
             and command["cwd"] == command["output"] == str(Path(job["outputs"]["job"]).parent)
             and _number(record["start_monotonic"]) == start and _number(record["end_monotonic"]) == end,
             "PROCESS", "Supervisor command, directory, logs, process or timing differs")
    cleanup = record["cleanup"]
    _require(type(cleanup) is dict and cleanup.keys() == {"passed", "elapsed_ms", "process_group_absent", "reaped"}
             and all(cleanup[k] is True for k in ("passed", "process_group_absent", "reaped")),
             "CLEANUP", "Supervisor cleanup is failed or unknown")
    _require(_number(cleanup["elapsed_ms"]) == 0,
             "CLEANUP", "Passing qualified supervisor receipts have no termination cleanup")
    _require((end - start) * 1000 <= LIMITS["child_work_ms"],
             "PROCESS", "Passing supervisor duration exceeds the child-work allowance")
    return canonical(observation)


def _khronos(value):
    _require(type(value) is dict and value.keys() == {"version", "passed", "report"}
             and value["version"] == CHECKS["khronos"]["version"] and value["passed"] is True,
             "KHRONOS", "Missing or failed Khronos check")
    report = value["report"]
    _require(type(report) is dict and report.get("validatorVersion") == value["version"]
             and report.get("uri") == "final.glb", "KHRONOS", "Unrelated Khronos report")
    issues = report.get("issues")
    _require(type(issues) is dict and issues.keys() == {"numErrors", "numWarnings", "numInfos", "numHints", "messages", "truncated"},
             "KHRONOS", "Incomplete Khronos issue inventory")
    _require(all(type(issues[k]) is int and issues[k] >= 0 for k in ("numErrors", "numWarnings", "numInfos", "numHints"))
             and issues["numErrors"] == issues["numWarnings"] == 0 and issues["truncated"] is False,
             "KHRONOS", "Khronos error, warning or truncated report")
    messages = issues["messages"]
    _require(type(messages) is list and len(messages) <= CHECKS["khronos"]["maxIssues"]
             and all(type(m) is dict and type(m.get("severity")) is int and m["severity"] in (2, 3) for m in messages)
             and sum(m["severity"] == 2 for m in messages) == issues["numInfos"]
             and sum(m["severity"] == 3 for m in messages) == issues["numHints"],
             "KHRONOS", "Khronos messages contradict issue counts")


def _three(value, audit):
    keys = {"version", "revision", "passed", "node_count", "mesh_count", "animations", "scenes", "cameras",
            "findings", "measurements", "nodes", "position_tolerance_m", "matrix_tolerance", "naming",
            "unsupported_objects", "textures", "external_resources"}
    _require(type(value) is dict and value.keys() == keys, "THREE", "Incomplete Three.js observations")
    expected = {"version": "0.186.1", "revision": "186", "passed": True, "node_count": 14,
                "mesh_count": 12, "animations": 0, "scenes": 1, "cameras": 0, "findings": [],
                "position_tolerance_m": 0.000005, "matrix_tolerance": 0.000001, "naming": NAMING,
                "unsupported_objects": [], "textures": [], "external_resources": []}
    _require(all(exact(value[k], v) for k, v in expected.items()), "THREE", "Failed, unsupported or wrong-count Three.js check")
    nodes, reference = value["nodes"], audit["nodes"]
    _require(type(nodes) is dict and type(reference) is dict and nodes.keys() == reference.keys() and len(nodes) == 14,
             "THREE", "Actual imported node inventory differs")
    measurements = []

    def near(name, label, actual, expected, threshold):
        difference = abs(_number(actual) - _number(expected))
        _require(difference <= threshold, "MEASUREMENT", name + ": " + label + " exceeds the frozen allowance")
        measurements.append({"semantic_id": name, "field": label, "actual": actual, "expected": expected,
                             "difference": difference, "threshold": threshold, "passed": True})

    meshes = 0
    for name in sorted(nodes):
        actual, ref = nodes[name], reference[name]
        common = {"original_name", "importer_name", "extras", "world_matrix", "children", "parent"}
        mesh = "world_vertices" in ref
        required = common | ({"positions", "normals", "world_vertices", "indices", "material", "world_bounds"} if mesh else set())
        _require(type(actual) is dict and actual.keys() == required and actual["original_name"] == name
                 and type(actual["importer_name"]) is str and bool(actual["importer_name"])
                 and _equal(actual["extras"], ref["extras"])
                 and exact(actual["children"], sorted(ref["children"]))
                 and actual["parent"] == (None if ref["extras"]["role"] == "tray-root" else "/".join(ref["extras"]["owner_id"])),
                 "THREE", "Imported identity, hierarchy, geometry kind or material role differs")
        matrix = actual["world_matrix"]
        _require(type(matrix) is list and len(matrix) == 4 and all(type(row) is list and len(row) == 4 for row in matrix),
                 "MEASUREMENT", "Malformed imported matrix")
        for i in range(4):
            for j in range(4):
                near(name, f"matrix_{i}_{j}", matrix[i][j], ref["world_matrix"][i][j], 0.000005 if j == 3 and i < 3 else 0.000001)
        if not mesh:
            continue
        meshes += 1
        count = len(ref["world_vertices"])
        _require(1 <= count <= 4096 and all(type(actual[k]) is list and len(actual[k]) == count
                 and all(type(row) is list and len(row) == 3 for row in actual[k])
                 for k in ("positions", "normals", "world_vertices")), "THREE", "Missing or malformed imported geometry")
        for i in range(count):
            p = [_number(v) for v in actual["positions"][i]]
            transformed = [sum(matrix[axis][j] * p[j] for j in range(3)) + matrix[axis][3] for axis in range(3)]
            for axis in range(3):
                _require(abs(_number(actual["world_vertices"][i][axis]) - transformed[axis]) <= 0.000005,
                         "MEASUREMENT", "Local positions contradict retained world vertices")
                near(name, f"world_vertex_{i}_{axis}", actual["world_vertices"][i][axis], ref["world_vertices"][i][axis], 0.000005)
                near(name, f"normal_{i}_{axis}", actual["normals"][i][axis], ref["normals"][i][axis], 0.000001)
        _require(exact(actual["indices"], ref["indices"]) and len(actual["indices"]) == 36
                 and _equal(actual["material"], ref["material"]), "THREE", "Imported triangle indices or material differ")
        bounds = [[operation(row[axis] for row in actual["world_vertices"]) for axis in range(3)] for operation in (min, max)]
        wanted = [[operation(row[axis] for row in ref["world_vertices"]) for axis in range(3)] for operation in (min, max)]
        _require(_equal(actual["world_bounds"], bounds), "MEASUREMENT", "Declared bounds differ from actual observed vertices")
        for axis in range(3):
            near(name, f"world_min_{axis}", bounds[0][axis], wanted[0][axis], 0.000005)
            near(name, f"world_max_{axis}", bounds[1][axis], wanted[1][axis], 0.000005)
            near(name, f"world_size_{axis}", bounds[1][axis] - bounds[0][axis], wanted[1][axis] - wanted[0][axis], 0.000005)
    _require(meshes == 12 and _equal(value["measurements"], measurements), "MEASUREMENT",
             "Missing, extra, reordered or contradictory required measurements")
    return len(measurements)


def _probe(job, job_bytes, raw, audit):
    value = input_lock._json(raw)
    _require(type(value) is dict, "RESULT", "Probe result must be an object")
    if value.get("state") == "UNKNOWN":
        raise ReadbackError("RESULT", "Readback result is explicitly unknown", "UNKNOWN")
    keys = {"schema", "purpose", "state", "passed", "job_sha256", "slot", "route", "case", "source",
            "protocol_sha256", "schedule_sha256", "input_lock_sha256", "accepted_revision",
            "accepted_pointer_sha256", "transaction_receipt_sha256", "artifact_sha256", "audit_sha256",
            "checks", "limits", "node", "native_starts", "exports", "input_preserved", "scope", "khronos", "three"}
    _require(value.keys() == keys, "RESULT", "Missing or extra probe result fields")
    bound = {k: job[k] for k in ("purpose", "slot", "route", "case", "source", "protocol_sha256",
             "schedule_sha256", "input_lock_sha256", "accepted_revision", "accepted_pointer_sha256",
             "transaction_receipt_sha256", "checks", "limits", "scope")}
    bound.update(schema=PROBE_SCHEMA, state="PASSED", passed=True, job_sha256=_sha(job_bytes),
                 artifact_sha256=job["artifact"]["sha256"], audit_sha256=job["audit"]["sha256"],
                 node="v24.22.1", native_starts=0, exports=0, input_preserved=True)
    _require(all(exact(value[k], v) for k, v in bound.items()), "RESULT", "Failed or unrelated probe result")
    _khronos(value["khronos"])
    return _three(value["three"], audit)


@_boundary
def verify_readback_result(prepared, *, process):
    """Check immutable accepted inputs and retained observations; never advance.

    Any failed/unknown attempt stops this in-memory session. The unchanged job
    and partial outputs remain available. Durable cross-restart stopping and
    authenticated process provenance remain the future coordinator's duty.
    """
    _require(type(prepared) is PreparedReadback, "BINDING", "An actual prepared readback is required")
    owner = _owner(prepared._owner)
    _require(owner._prepared.get(prepared.slot) is prepared and not owner._stopped
             and prepared.slot not in owner._terminal, "REPLAY", "Foreign, completed or stopped readback")
    owner._terminal.add(prepared.slot)
    try:
        _, job, audit = _prepared(prepared)
        outputs = _outputs(job)
        observed = _process(owner, job, outputs["process"], process, len(outputs["stdout"]) + len(outputs["stderr"]))
        count = _probe(job, prepared.job_bytes, outputs["probe"], audit)
        _prepared(prepared)
        _require(outputs == _outputs(job), "OUTPUT", "Readback output bytes changed during verification")
        return ReadbackEvidence(prepared.slot, job["purpose"], job["accepted_revision"],
                                job["accepted_pointer_sha256"], _sha(prepared.job_bytes), _sha(outputs["probe"]),
                                _sha(observed), tuple((OUTPUTS[k], len(v), _sha(v)) for k, v in sorted(outputs.items())), count)
    except BaseException as exc:
        owner._stopped = True
        if not isinstance(exc, Exception):
            raise ReadbackError("INTERRUPTED", "Readback observation check was interrupted; do not retry", "UNKNOWN") from exc
        raise
