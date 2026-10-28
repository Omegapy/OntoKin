"""Durable, revision-safe authoring and inspection for local AI-agent clients.

AgentService has no network listener or model dependency. Submit JSON requests,
run work_next() in a worker, and use status/cancel requests concurrently. handle()
is the synchronous convenience entry point. Native source is authoritative.
"""

from __future__ import annotations

import base64
import copy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import hmac
import json
from pathlib import Path
import time
import uuid

from . import agent_runtime as runtime
from . import agent_protocol as protocol
from . import __version__
from .agent_protocol import (MAX_BUDGETS, OPERATIONS, TERMINAL, ProtocolError,
                             canonical_request, envelope, validate_request)
from .agent_store import AgentStore, dumps
from .diagnostics import OntoKinError, Source


class _Cancelled(Exception):
    pass


@lru_cache(maxsize=1)
def implementation_identity() -> dict:
    """Pin one loaded process to a concrete package; restart after code updates."""
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return {"name": "ontokin-reference", "version": __version__,
            "source_code_sha256": "sha256:" + digest.hexdigest()}


@dataclass
class _Task:
    request: dict
    response: dict
    source: Source | None = None
    accept: bool = False
    run: dict | None = None
    run_version: int | None = None
    artifact: tuple[bytes, dict, str] | None = None
    publication_context: object | None = None


class _Check:
    """Cooperative work/deadline checks, with cancellation polled at most 5ms apart."""
    def __init__(self, service, request):
        self.service, self.request = service, request
        self.limits = {**service._protocol.MAX_BUDGETS, **request.get("budgets", {})}
        self.started, self.last_poll, self.operations = time.monotonic(), 0., 0

    def __call__(self):
        self.operations += 1
        now = time.monotonic()
        elapsed = (now - self.started) * 1000
        for name, consumed in (("max_operations", self.operations), ("max_elapsed_ms", elapsed)):
            if consumed > self.limits[name]:
                raise OntoKinError("OKL-E-RESOURCE", f"The request exhausted {name}.",
                                   category="resource_limit", phase="support",
                                   details={"budget": name, "limit": self.limits[name], "consumed": consumed,
                                            "request_terminated": True,
                                            "partial_results": "No uncommitted source, artifact or run advancement is available."})
        if now - self.last_poll >= .005 or self.service._store.closed:
            self.last_poll = now
            with self.service._store.connection() as db:
                row = self.service._store.request(db, self.request["project_id"], self.request["request_id"])
            if self.service._store.closed or row is None or row["state"] != "running" or row["owner"] != self.service._store.owner or row["cancel_requested"]:
                raise _Cancelled()


class AgentService:
    # Version bindings share durability/fencing, never revision field meanings.
    _protocol = protocol
    _runtime = runtime
    _store_type = AgentStore
    _revision_key = "source_revision"
    _accepted_key = "accepted_revision"
    _expected_key = "expected_revision"
    _destination = "ontokin.glb/0.1"

    @staticmethod
    def _revision(source):
        return source.revision

    @staticmethod
    def _create_source(request):
        return Source(request["source"], request["filename"])

    def _edit_source(self, base, request, check):
        return self._runtime.apply_patches(base, request["patches"],
                                           budgets=request.get("budgets"), check=check)

    @staticmethod
    def _diagnostic(error, source, run_id=None):
        return error.diagnostic.to_dict(source, run_id)

    def _context_binding(self):
        return {}

    def _check_response(self, response):
        """A version binding may impose an additional encoded result limit."""

    def _check_task_response(self, task):
        """Check a proposed publication with its immutable request context."""
        self._check_response(task.response)

    def _bind_publication_context(self, task, *, accepted_revision, source_accepted_once):
        """Bind fresh versioned projections before a run is serialized.

        The default preserves all earlier bindings. The transaction has already
        fenced cancellation, source acceptance and competing run advancement.
        Implementations receive the prospective committed identities, not a
        store handle, and must leave historical descriptors and receipts alone.
        """

    def __init__(self, store_path: Path):
        self.implementation = copy.deepcopy(implementation_identity())
        self._store = self._store_type(Path(store_path), self.implementation)
        self.store_path = self._store.path
        self.database_path = self._store.database_path

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        self._store.close()

    def read_source(self, project_id: str, revision: str) -> Source:
        return self._store.read_source(project_id, revision)

    def get_run(self, project_id: str, run_id: str) -> dict:
        return self._store.read_run(project_id, run_id)[0]

    def accepted_revision(self, project_id: str) -> str | None:
        with self._store.connection() as db:
            return self._store.accepted(db, project_id)

    def _protocol_response(self, request, error: ProtocolError, *, accepted=None, status="rejected"):
        response = self._protocol.envelope(request, status, accepted)
        response["protocol_error"] = error.to_dict()
        return response

    def submit(self, request: dict) -> dict:
        """Retain a receipt before work; identical retries never re-enqueue effects."""
        if self._store.closed:
            return self._protocol_response(request, ProtocolError("OKA-E-CLOSED", "This service instance is closed."))
        original = request
        try:
            request, payload = self._protocol.canonical_request(request)
        except ProtocolError as exc:
            return self._protocol_response(original, exc)
        project, request_id = request.get("project_id"), request.get("request_id")
        usable_identity = all(isinstance(x, str) and x and len(x.encode("utf-8")) <= 200 for x in (project, request_id))
        if not usable_identity:
            return self._protocol_response(request, ProtocolError("OKA-E-REQUEST", "project_id and request_id must be nonempty bounded strings."))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        with self._store.transaction() as db:
            accepted = self._store.accepted(db, project)
            existing = self._store.request(db, project, request_id)
            if existing is not None:
                if existing["digest"] != digest:
                    return self._protocol_response(request, ProtocolError("OKL-E-REQUEST-ID", "This request identity already names a different canonical payload.",
                                                                        original_operation=existing["operation"]), accepted=accepted)
                return json.loads(existing["response"])
            try:
                self._protocol.validate_request(request)
            except ProtocolError as exc:
                response = self._protocol_response(request, exc, accepted=accepted)
                # Even a malformed operation with a usable identity cannot later be repurposed.
                self._store.record(db, {**request, "operation": str(request.get("operation", "invalid"))}, digest, payload, response)
                return response
            db.execute("INSERT OR IGNORE INTO projects (id) VALUES (?)", (project,))
            if request["operation"] in {"status", "cancel"}:
                db.execute("SAVEPOINT control_response")
                try:
                    response = self._control(db, request)
                    self._check_response(response)
                except ProtocolError as exc:
                    db.execute("ROLLBACK TO control_response")
                    response = self._protocol_response(request, exc, accepted=accepted)
                finally:
                    db.execute("RELEASE control_response")
            else:
                response = self._protocol.envelope(request, "queued", accepted)
                response["progress"] = {"phase": "queued", "cancellation_requested": False}
            self._store.record(db, request, digest, payload, response)
            return response

    def _control(self, db, request: dict) -> dict:
        project, target_id = request["project_id"], request["target_request_id"]
        accepted = self._store.accepted(db, project)
        target = self._store.request(db, project, target_id)
        response = self._protocol.envelope(request, "succeeded", accepted)
        if target is None:
            target_response = self._protocol.envelope({"project_id": project, "request_id": target_id}, "unknown_outcome", accepted)
            target_response["protocol_error"] = ProtocolError("OKA-E-UNKNOWN-OUTCOME", "No result or request identity is known in this store; reconcile before issuing effects.").to_dict()
            disposition = "unknown_identity"
        else:
            target_response = json.loads(target["response"])
            disposition = "observed"
            if request["operation"] == "cancel":
                if target["state"] == "queued":
                    target_response["status"] = "cancelled"
                    target_response["progress"] = {"phase": "cancelled_before_work", "cancellation_requested": True,
                                                   "partial_results": "No work began and no source or run was accepted."}
                    self._store.update_response(db, project, target_id, target_response)
                    db.execute("UPDATE requests SET cancel_requested=1 WHERE project_id=? AND id=?", (project, target_id))
                    disposition = "cancelled"
                elif target["state"] == "running":
                    db.execute("UPDATE requests SET cancel_requested=1 WHERE project_id=? AND id=?", (project, target_id))
                    target_response["progress"] = {**(target_response.get("progress") or {}), "cancellation_requested": True}
                    self._store.update_response(db, project, target_id, target_response)
                    disposition = "cancellation_requested"
                else:
                    disposition = "already_completed" if target["state"] != "unknown_outcome" else "unknown_outcome"
        response["result"] = {"target_request_id": target_id, "target_status": target_response["status"],
                              "disposition": disposition, "target": target_response}
        return response

    def handle(self, request: dict, wait: bool = True) -> dict:
        """Synchronous convenience; transport clients may submit and poll instead."""
        response = self.submit(request)
        if not wait or response["status"] in TERMINAL:
            return response
        project, request_id = response["project_id"], response["request_id"]
        while response["status"] not in TERMINAL:
            worked = self.work_next()
            with self._store.connection() as db:
                row = self._store.request(db, project, request_id)
                response = json.loads(row["response"])
            if not worked and response["status"] not in TERMINAL:
                # A different live worker owns this request; this call is a bounded poll.
                time.sleep(.01)
        return response

    def work_next(self) -> bool:
        if self._store.closed:
            return False
        with self._store.transaction() as db:
            self._store.recover(db)
            row = db.execute("SELECT * FROM requests WHERE state='queued' ORDER BY sequence LIMIT 1").fetchone()
            if row is None:
                return False
            request = json.loads(row["payload"])
            response = json.loads(row["response"])
            if row["engine"] != dumps(self.implementation):
                response[self._accepted_key] = self._store.accepted(db, row["project_id"])
                response.update(status="rejected",
                                protocol_error=ProtocolError("OKA-E-ENGINE", "Queued work was authored for a different implementation; reconcile before deliberately submitting new work.",
                                                             recorded_implementation=None if row["engine"] is None else json.loads(row["engine"]),
                                                             current_implementation=self.implementation, effects_committed=False).to_dict())
                self._store.update_response(db, row["project_id"], row["id"], response)
                return True
            response["status"] = "running"
            response["progress"] = {"phase": "working", "cancellation_requested": False}
            self._store.update_response(db, row["project_id"], row["id"], response)
            db.execute("UPDATE requests SET owner=? WHERE sequence=?", (self._store.owner, row["sequence"]))
        task = _Task(request, response)
        check = _Check(self, request)
        try:
            check()
            self._execute(task, check)
            check()
        except _Cancelled:
            task.accept, task.run, task.artifact = False, None, None
            task.response["status"] = "cancelled"
            task.response["progress"] = {"phase": "cancelled_before_commit", "cancellation_requested": True,
                                         "partial_results": "Only already-retained immutable source and previously committed runs are available."}
        except OntoKinError as exc:
            self._semantic_error(task, exc)
        except ProtocolError as exc:
            task.accept, task.run, task.artifact = False, None, None
            task.response.update(status="rejected", protocol_error=exc.to_dict())
        except (RecursionError, MemoryError) as exc:
            self._semantic_error(task, OntoKinError("OKL-E-RESOURCE", "The local operation exceeded a runtime resource limit.",
                                                   category="resource_limit", phase="support", details={"exception": type(exc).__name__}))
        except Exception as exc:
            # No effects have been committed. Preserve an explicit failure, never fake language diagnostics.
            task.accept, task.run, task.artifact = False, None, None
            task.response.update(status="failed", protocol_error=ProtocolError("OKA-E-INTERNAL", "The operation failed before commit.",
                                                                              exception=type(exc).__name__, reason=str(exc)).to_dict())
        self._finish(task)
        return True

    def _semantic_error(self, task: _Task, error: OntoKinError) -> None:
        task.accept, task.artifact = False, None
        # An exception outside a returned evaluator prefix did not commit a run.
        # A completed isolated validation run can still be useful when delivery
        # fails, but request-wide termination must discard computed advancement.
        terminated = bool((error.diagnostic.details or {}).get("request_terminated"))
        if terminated:
            task.run = None
        if task.run is not None:
            run = task.run
            run_id = run["run_id"]
            partial = "The completed isolated evaluation is retained for diagnosis; no source acceptance or artifact was committed."
        else:
            run_id = task.request.get("run_id")
            try:
                run = self.get_run(task.request["project_id"], run_id) if run_id else None
            except ProtocolError:
                run_id, run = None, None
            partial = "Only already-retained immutable source snapshots and any previously committed run descriptor are available."
        task.response["run_id"] = run_id
        task.response["result"] = {"outcome": error.diagnostic.category, "run_state": run,
                                   "requested_level": task.response["requested_level"],
                                   "achieved_level": task.response["achieved_level"],
                                   "delivery": "failed" if task.response["requested_level"] == "delivered" else "not_requested",
                                   "partial_results": partial}
        task.response["status"] = "failed" if error.diagnostic.category in {"numerical_failure", "resource_limit"} else "rejected"
        if task.source is not None:
            task.response[self._revision_key] = self._revision(task.source)
            task.response["diagnostics"].append(self._diagnostic(error, task.source, task.response.get("run_id")))
        else:
            task.response["protocol_error"] = ProtocolError(error.code, str(error)).to_dict()

    def _snapshot(self, task: _Task, source) -> None:
        with self._store.transaction() as db:
            self._store.snapshot(db, task.request["project_id"], source)
        task.source = self.read_source(task.request["project_id"], self._revision(source))
        task.response[self._revision_key] = self._revision(task.source)

    def _absorb(self, task: _Task, result: dict, *, origin: str | None = None) -> None:
        task.response["result"] = result
        task.response["diagnostics"] = result.get("diagnostics", [])
        task.response["achieved_level"] = result.get("achieved_level")
        task.response["status"] = ("succeeded" if result.get("outcome") == "valid" else
                                   "failed" if result.get("outcome") in {"resource_limit", "numerical_failure"} else "rejected")
        if result.get("run_state") is not None:
            run = copy.deepcopy(result["run_state"])
            run_id = run.get("run_id") or "run:" + uuid.uuid4().hex
            run.update(run_id=run_id, origin=origin or "ordinary",
                       implementation=copy.deepcopy(self.implementation),
                       candidate_only=not self._store.source_accepted_once(task.request["project_id"], self._revision(task.source)))
            task.run = run
            task.response["run_id"] = run_id
            result["run_state"] = run
            # Attach the service-issued run identity to real revision-bound diagnostics.
            for diagnostic in task.response["diagnostics"]:
                if diagnostic.get("time") is not None:
                    diagnostic["run_id"] = run_id
            if run.get("failure") and run["failure"].get("diagnostic"):
                run["failure"]["diagnostic"]["run_id"] = run_id

    def _validate(self, task: _Task, check: _Check) -> None:
        request = task.request
        level = request["requested_level"]
        explicit_delivery = level == "delivered" and request.get("destination") == self._destination
        result = self._runtime.validate_revision(task.source, level="evaluated" if explicit_delivery else level,
                                           budgets=request.get("budgets"), check=check)
        result["requested_level"] = level
        self._absorb(task, result, origin="validation")
        if explicit_delivery and result["outcome"] == "valid":
            self._export(task, check)
            task.response["achieved_level"] = "delivered"
            result["achieved_level"] = "delivered"

    def _identity_gate(self, before: Source, candidate: Source, check: _Check, budgets: dict | None) -> None:
        # Object occurrence identity must not silently change nominal definition.
        identity = {}
        for source in (before, candidate):
            inspected = self._runtime.inspect_revision(source, selector={"kind": "object"}, fields=["identity"],
                                                 limit=min(1000, (budgets or {}).get("max_result_items", 1000)),
                                                 budgets=budgets, check=check)
            if inspected["outcome"] != "valid" or inspected.get("truncated"):
                raise OntoKinError("OKL-E-RESOURCE", "The edit's identity comparison did not fit its complete object-result budget.",
                                   category="resource_limit", phase="edit")
            current = {tuple(item["element_id"]): item["identity"].get("definition_id") for item in inspected["items"]}
            if identity:
                changed = [key for key in identity.keys() & current.keys() if identity[key] != current[key]]
                if changed:
                    raise OntoKinError("OKL-E-ID", "Replacing an occurrence with a different class definition requires a new occurrence key.",
                                       category="invalid", phase="binding", rule_ids=["LANG-007"],
                                       details={"changed_occurrences": [list(key) for key in sorted(changed)]})
            identity = current

    def _execute(self, task: _Task, check: _Check) -> None:
        request, response = task.request, task.response
        operation, project = request["operation"], request["project_id"]
        budgets = request.get("budgets")
        if operation == "discover":
            self._discover(task, check)
            return
        if operation == "artifact":
            self._read_artifact(task)
            return
        if operation == "create":
            source = self._create_source(request)
            self._snapshot(task, source)
            if self.accepted_revision(project) is not None:
                raise OntoKinError("OKL-E-REVISION", "Create requires a project with no accepted revision.", category="stale", phase="edit")
            self._validate(task, check)
            task.accept = response["status"] == "succeeded"
            return
        if operation == "edit":
            base = self.read_source(project, request[self._expected_key])
            task.source = base
            response[self._revision_key] = self._revision(base)
            if self.accepted_revision(project) != self._revision(base):
                raise OntoKinError("OKL-E-REVISION", "The edit's expected revision is stale.", category="stale", phase="edit")
            candidate = self._edit_source(base, request, check)
            self._snapshot(task, candidate)
            self._validate(task, check)
            if response["status"] == "succeeded":
                self._identity_gate(base, candidate, check, budgets)
                task.accept = True
            return
        task.source = self.read_source(project, request[self._revision_key])
        if operation == "validate":
            self._validate(task, check)
        elif operation == "inspect":
            self._inspect(task, check)
        elif operation in {"evaluate", "reset", "export"}:
            if not self._store.source_accepted_once(project, self._revision(task.source)):
                raise OntoKinError("OKL-E-REVISION", "Ordinary runs and export require an accepted source snapshot; this candidate has never been accepted.",
                                   category="stale", phase="inspection", blocks=[])
            if operation == "export":
                result = self._runtime.validate_revision(task.source, level="evaluated", budgets=budgets, check=check)
                self._absorb(task, result, origin="validation")
                if response["status"] == "succeeded":
                    self._export(task, check)
                    response["achieved_level"] = "delivered"
                    result["requested_level"] = "delivered"
                    result["achieved_level"] = "delivered"
                return
            previous = None
            if operation == "evaluate" and request["run_id"] is not None:
                previous, task.run_version = self._store.read_run(project, request["run_id"])
                self._check_engine(previous)
                response["run_id"] = request["run_id"]
                if previous[self._revision_key] != self._revision(task.source) or previous.get("candidate_only"):
                    raise OntoKinError("OKL-E-SAMPLE", "The run belongs to another revision or is retained only for candidate diagnosis.",
                                       category="stale", phase="inspection", blocks=[])
            result = self._runtime.evaluate_revision(task.source, until="0" if operation == "reset" else request["until_seconds"],
                                               side="before" if operation == "reset" else "after", previous=previous,
                                               budgets=budgets, check=check)
            self._absorb(task, result, origin="reset" if operation == "reset" else (previous or {}).get("origin", "ordinary"))
        else:
            raise ProtocolError("OKA-E-REQUEST", "Unknown work operation.")

    def _cursor(self, context: dict, offset: int) -> str:
        data = dumps({"context": context, "offset": offset}).encode("utf-8")
        mac = hmac.new(self._store.cursor_secret, data, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac + data).decode("ascii").rstrip("=")

    def _offset(self, token: str | None, context: dict) -> int:
        if token is None:
            return 0
        try:
            raw = base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True)
            mac, data = raw[:32], raw[32:]
            if not hmac.compare_digest(mac, hmac.new(self._store.cursor_secret, data, hashlib.sha256).digest()):
                raise ValueError("signature")
            decoded = json.loads(data)
            if decoded["context"] != context or type(decoded["offset"]) is not int or decoded["offset"] < 0:
                raise ValueError("context")
            return decoded["offset"]
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            raise ProtocolError("OKL-E-REVISION", "The cursor is invalid or belongs to a different immutable inspection context.") from exc

    def _inspect(self, task: _Task, check: _Check) -> None:
        request = task.request
        run = self.get_run(request["project_id"], request["run_id"]) if request.get("run_id") else None
        if run is not None:
            self._check_engine(run)
        sample = request.get("time")
        if sample is None and run is not None:
            sample = {"seconds": run.get("valid_until_seconds"), "side": run.get("valid_until_side")}
        context = {"project_id": request["project_id"], self._revision_key: self._revision(task.source),
                   "run_id": request.get("run_id"), "time": sample, "frame": request.get("frame", "world"),
                   "selector": request["selector"], "fields": sorted(request["fields"]), **self._context_binding()}
        offset = self._offset(request.get("cursor"), context)
        result = self._runtime.inspect_revision(task.source, selector=request["selector"], fields=request["fields"], limit=request["limit"],
                                          offset=offset, run=run, time=None if sample is None else sample["seconds"],
                                          side="after" if sample is None else sample["side"], frame=context["frame"],
                                          budgets=request.get("budgets"), check=check)
        if "context" in result:
            result["sample_context"] = result["context"]
        self._absorb(task, result)
        task.response["run_id"] = request.get("run_id")
        task.response["truncated"] = result.get("truncated", False)
        if result.get("next_offset") is not None:
            task.response["next_cursor"] = self._cursor(context, result["next_offset"])

    def _check_engine(self, run: dict) -> None:
        if run.get("implementation") != self.implementation:
            raise ProtocolError("OKL-E-SAMPLE", "This run belongs to a different implementation and cannot be replayed by this engine.",
                                recorded_implementation=run.get("implementation"), current_implementation=self.implementation,
                                repair="Inspect the retained descriptor and deliberately reset the accepted source to create a new run.")

    def _export(self, task: _Task, check: _Check) -> None:
        from .gltf import export_glb
        from .scene import ExportOptions
        from .syntax import parse
        from .validator import validate
        check()
        model = validate(parse(task.source.text, task.source.filename), level="evaluated")
        artifact = export_glb(model, options=ExportOptions(**task.request.get("options", {})),
                              source_uri=task.source.filename, source_sha256=self._revision(task.source))
        check()
        artifact_id = "artifact:" + hashlib.sha256(artifact.data).hexdigest()
        task.artifact = (artifact.data, artifact.report, artifact_id)
        task.response["result"].update({"artifact_id": artifact_id, "report": artifact.report,
                                       self._revision_key: self._revision(task.source), "total_bytes": len(artifact.data),
                                       "sha256": "sha256:" + hashlib.sha256(artifact.data).hexdigest(),
                                       "mime_type": "model/gltf-binary", "destination": "ontokin.glb/0.1"})

    def _read_artifact(self, task: _Task) -> None:
        request = task.request
        with self._store.connection() as db:
            row = db.execute("SELECT source_revision,length(data) AS total,sha256,substr(data,?,?) AS chunk FROM artifacts WHERE project_id=? AND id=?",
                             (request.get("offset", 0) + 1, request.get("max_bytes", 65536), request["project_id"], request["artifact_id"])).fetchone()
        if row is None:
            raise ProtocolError("OKA-E-ARTIFACT", "The artifact identity is not present in this project.")
        offset, total = request.get("offset", 0), row["total"]
        if offset > total:
            raise ProtocolError("OKA-E-ARTIFACT", "Artifact offset is beyond the byte length.", total_bytes=total)
        chunk = bytes(row["chunk"])
        next_offset = offset + len(chunk) if offset + len(chunk) < total else None
        task.response.update(status="succeeded", truncated=next_offset is not None)
        task.response[self._revision_key] = row["source_revision"]
        task.response["result"] = {"artifact_id": request["artifact_id"], "offset": offset, "total_bytes": total,
                                   "data_base64": base64.b64encode(chunk).decode("ascii"), "next_offset": next_offset,
                                   "mime_type": "model/gltf-binary", "sha256": row["sha256"], self._revision_key: row["source_revision"]}

    def _discover(self, task: _Task, check=None) -> None:
        from .agent_catalog import catalog
        request = task.request
        if request["profile"] != "core-0.1":
            raise ProtocolError("OKL-E-CAPABILITY-UNSUPPORTED", "The requested semantic profile is unavailable.", available_profiles=["core-0.1"])
        context = {"project_id": request["project_id"], "operation": "discover", "catalog_revision": catalog()["revision"],
                   "profile": request["profile"], "filter": request.get("filter")}
        offset = self._offset(request.get("cursor"), context)
        result = catalog()
        items = result["items"]
        filter_ = request.get("filter")
        if isinstance(filter_, str):
            items = [item for item in items if filter_.lower() in dumps(item).lower()]
        elif isinstance(filter_, dict):
            if set(filter_) - {"kind", "name", "capability"}:
                raise ProtocolError("OKA-E-REQUEST", "Discovery filters support kind, name, or capability.")
            items = [item for item in items if all(item.get(key) == value for key, value in filter_.items())]
        total = len(items)
        result.update(items=items[offset:offset + request["limit"]], total=total, offset=offset)
        next_offset = offset + len(result["items"]) if offset + len(result["items"]) < total else None
        task.response.update(status="succeeded", result=result, truncated=next_offset is not None,
                             next_cursor=None if next_offset is None else self._cursor(context, next_offset))

    def _finish(self, task: _Task) -> None:
        try:
            self._commit_task(task)
        except ProtocolError as exc:
            # A result-limit failure rolls back the whole attempted transaction,
            # including acceptance, runs and artifacts, before retaining failure.
            task.accept, task.run, task.artifact = False, None, None
            task.response = self._protocol.envelope(task.request, "failed")
            if task.source is not None:
                task.response[self._revision_key] = self._revision(task.source)
            task.response["protocol_error"] = exc.to_dict()
            self._commit_task(task)

    def _commit_task(self, task: _Task) -> None:
        request, response = task.request, task.response
        self._check_task_response(task)
        project, request_id = request["project_id"], request["request_id"]
        with self._store.transaction() as db:
            row = self._store.request(db, project, request_id)
            if row["state"] != "running" or row["owner"] != self._store.owner:
                return  # Closed/dead worker has been fenced; it cannot commit late.
            accepted = self._store.accepted(db, project)
            response[self._accepted_key] = accepted
            if row["cancel_requested"]:
                task.accept, task.run, task.artifact = False, None, None
                response.update(status="cancelled", achieved_level=None, run_id=None, result=None,
                                progress={"phase": "cancelled_before_commit", "cancellation_requested": True,
                                          "partial_results": "No source acceptance, artifact, or run advancement was committed."})
            elif task.accept and accepted != request.get(self._expected_key):
                task.accept = False
                task.artifact = None
                error = OntoKinError("OKL-E-REVISION", "Another accepted edit advanced the project before this candidate could commit.",
                                     category="stale", phase="edit", details={self._expected_key: request.get(self._expected_key), self._accepted_key: accepted})
                response["status"] = "rejected"
                response["diagnostics"].append(self._diagnostic(error, task.source, response.get("run_id")))
                if response.get("result") is not None:
                    response["result"]["acceptance"] = "stale; source not accepted; any returned isolated validation run is retained for diagnosis"
            run_version = None
            if task.run is not None:
                run_id = task.run["run_id"]
                old = db.execute("SELECT version,descriptor FROM runs WHERE project_id=? AND id=?", (project, run_id)).fetchone()
                if old is not None and old["version"] != task.run_version:
                    task.run, task.accept, task.artifact = None, False, None
                    response.update(status="rejected", protocol_error=ProtocolError("OKL-E-SAMPLE", "Another worker advanced this run before commit; inspect its current interval.").to_dict())
                    response["achieved_level"] = None
                    response["result"] = {"run_state": json.loads(old["descriptor"]), "run_advance_committed": False}
                else:
                    task.run["candidate_only"] = not (task.accept or self._source_accepted_db(db, project, self._revision(task.source)))
                    run_version = 1 if old is None else old["version"] + 1
            if task.accept:
                response[self._accepted_key] = self._revision(task.source)
            source_accepted = task.source is not None and (
                task.accept or self._source_accepted_db(db, project, self._revision(task.source)))
            self._bind_publication_context(task, accepted_revision=response[self._accepted_key],
                                           source_accepted_once=bool(source_accepted))
            if task.run is not None:
                db.execute("INSERT INTO runs VALUES (?,?,?,?,?) ON CONFLICT(project_id,id) DO UPDATE SET descriptor=excluded.descriptor,version=excluded.version",
                           (project, task.run["run_id"], self._revision(task.source), dumps(task.run), run_version))
            if task.accept:
                db.execute("UPDATE projects SET accepted_revision=? WHERE id=?", (self._revision(task.source), project))
                db.execute("UPDATE sources SET accepted_once=1 WHERE project_id=? AND revision=?", (project, self._revision(task.source)))
            if task.artifact is not None and response["status"] == "succeeded":
                data, report, artifact_id = task.artifact
                db.execute("INSERT OR IGNORE INTO artifacts VALUES (?,?,?,?,?,?)",
                           (project, artifact_id, self._revision(task.source), data, dumps(report), "sha256:" + hashlib.sha256(data).hexdigest()))
            if response["status"] != "cancelled":
                response["progress"] = {"phase": "complete", "cancellation_requested": False,
                                        "implementation": self.implementation}
            if isinstance(response.get("result"), dict):
                response["result"]["implementation"] = self.implementation
            self._check_task_response(task)
            self._store.update_response(db, project, request_id, response)
            db.execute("UPDATE requests SET owner=NULL WHERE project_id=? AND id=?", (project, request_id))

    @staticmethod
    def _source_accepted_db(db, project, revision):
        row = db.execute("SELECT accepted_once FROM sources WHERE project_id=? AND revision=?", (project, revision)).fetchone()
        return bool(row and row[0])

    def expire_result(self, project_id: str, request_id: str) -> bool:
        """Explicit administrative retention action; keep an identity/digest tombstone."""
        with self._store.transaction() as db:
            row = self._store.request(db, project_id, request_id)
            if row is None or row["state"] not in TERMINAL or row["state"] == "unknown_outcome":
                return False
            self._store.unknown(db, row, "The terminal result was explicitly expired; its identity and digest remain and must not be replayed.")
            return True
