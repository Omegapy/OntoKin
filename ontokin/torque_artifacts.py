"""Bounded retained-byte integrity proofs for explicit Agent/0.22 reads.

Every request reads and admits current source, metadata and the entire current
SQLite blob. Equal immutable byte strings have the same SHA-256 digest: one
bounded successful proof can therefore avoid hashing the same bytes again.
This is content equality, not a database-version or authorization cache.
"""
from __future__ import annotations

import base64
import hashlib
import json
from threading import Lock
from typing import NamedTuple
from weakref import WeakKeyDictionary

from .agent_protocol import ProtocolError


class _VerifiedBytes(NamedTuple):
    project: str
    artifact_id: str
    data: bytes
    digest: str


_VERIFIED_ARTIFACTS = WeakKeyDictionary()
_VERIFIED_ARTIFACT_LOCK = Lock()


def verified_artifact(service):
    """Observe the proof published by this module for one service instance."""
    with _VERIFIED_ARTIFACT_LOCK:
        return _VERIFIED_ARTIFACTS.get(service)


def clear_verified_artifact(service):
    with _VERIFIED_ARTIFACT_LOCK:
        _VERIFIED_ARTIFACTS.pop(service, None)


def _publish_verified_artifact(service, proof):
    # The property on the service is observation-only. Constructing or replacing
    # a tuple on that instance cannot establish a verified proof's provenance.
    # No callbacks or SQLite transactions run while this native lock is held.
    # close() first fences the store, then clears under this same lock, so an
    # in-flight read cannot republish a proof after close() has completed.
    with _VERIFIED_ARTIFACT_LOCK:
        if not service._store.closed:
            _VERIFIED_ARTIFACTS[service] = proof


def read_retained_artifact(service, task):
    request, check = task.request, task.execution_check
    with service._store.connection() as db:
        row = db.execute("SELECT source_revision,length(data) AS total FROM artifacts WHERE project_id=? AND id=?",
                         (request["project_id"], request["artifact_id"])).fetchone()
    if row is None:
        raise ProtocolError("OKA-E-ARTIFACT", "The artifact is absent from this project.")
    task.source = service.read_program(request["project_id"], row["source_revision"])
    task.response["program_revision"] = task.source.program_revision
    check.admit(task.source)
    if row["total"] > 64 * 1024 * 1024:
        raise ProtocolError("OKA-E-RESOURCE", "The retained artifact exceeds the fixed byte limit.")
    with service._store.connection() as db:
        stored = db.execute("SELECT source_revision,data,report,sha256 FROM artifacts WHERE project_id=? AND id=?",
                            (request["project_id"], request["artifact_id"])).fetchone()
    if stored is None or stored["source_revision"] != row["source_revision"]:
        raise ProtocolError("OKA-E-STORE-INTEGRITY", "Artifact provenance does not match its retained source and implementation.")
    data, report = bytes(stored["data"]), json.loads(stored["report"])
    if len(data) > 64 * 1024 * 1024:
        raise ProtocolError("OKA-E-RESOURCE", "The retained artifact exceeds the fixed byte limit.")
    if (report.get("program_revision") != task.source.program_revision
            or report.get("implementation_identity") != service.implementation):
        raise ProtocolError("OKA-E-STORE-INTEGRITY", "Artifact provenance does not match its retained source and implementation.")

    # Capture the immutable previous proof before any original callback. A
    # hit still rereads and compares *every* byte, including bytes outside the
    # requested slice. Metadata is never reused; a changed digest is checked
    # against the proof below and a changed blob takes the original hash path.
    previous = service._verified_artifact
    # A tuple has no mutable instance dictionary or writable slots, including
    # through object.__setattr__. Capture its exact native values before any
    # integrity callback rather than rereading fields afterward.
    proof = tuple(previous) if type(previous) is _VerifiedBytes else None
    equal = (proof is not None and type(proof[0]) is str and type(proof[1]) is str
             and type(proof[2]) is bytes and type(proof[3]) is str
             and proof[0] == request["project_id"] and proof[1] == request["artifact_id"]
             and proof[2] == data)
    ledger = check.execution_budget
    ledger.stage = "artifact_integrity"
    digest = None if equal else hashlib.sha256()
    for start in range(0, len(data), 65536):
        size = min(65536, len(data) - start)
        # Preserve every original structural charge and callback, even when
        # whole-byte equality already establishes the content's digest.
        ledger.tick(amount=max(1, (size + 63) // 64))
        if digest is not None:
            digest.update(data[start:start + 65536])
    actual = proof[3] if equal else digest.hexdigest()
    if "sha256:" + actual != stored["sha256"] or "artifact:" + actual != request["artifact_id"]:
        raise ProtocolError("OKA-E-STORE-INTEGRITY", "The retained artifact bytes do not match their identity.")
    if not equal:
        # Exactly one entry, bounded by the same fixed 64 MiB artifact cap.
        _publish_verified_artifact(service, _VerifiedBytes(request["project_id"], request["artifact_id"], data, actual))

    offset = request.get("offset", 0)
    if offset > len(data):
        raise ProtocolError("OKA-E-ARTIFACT", "Artifact offset is beyond the byte length.", total_bytes=len(data))
    chunk = data[offset:offset + request.get("max_bytes", 65536)]
    next_offset = offset + len(chunk) if offset + len(chunk) < len(data) else None
    ledger.tick(amount=max(1, (len(chunk) + 63) // 64))
    task.response.update(status="succeeded", truncated=next_offset is not None,
        result={"artifact_id": request["artifact_id"], "offset": offset, "total_bytes": len(data),
                "data_base64": base64.b64encode(chunk).decode("ascii"), "next_offset": next_offset,
                "mime_type": "model/gltf-binary", "sha256": stored["sha256"],
                "program_revision": task.source.program_revision,
                "artifact_provenance": {"exporter": report["exporter"],
                    "source_code_sha256": "sha256:" + report["source_code_sha256"],
                    "program_revision": task.source.program_revision},
                "validation": "Exact retained bytes verified by SHA-256; producer validation is historical.",
                "producer_request_id": report["producer_request_id"]})
