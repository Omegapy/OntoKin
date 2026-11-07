"""Durable Agent/0.7 requests under current, independently supplied host policy.

The service owns authorization and persistence. A request owns its clock,
counter and temporary compiler. Earlier Agent services keep their old routes.
"""
from __future__ import annotations

import base64
import copy
from functools import partial
import hashlib
import json
import math
import time

from .agent import AgentService, _Cancelled
from .agent_protocol import ProtocolError
from .agent_runtime import _Interrupt
from .agent_store import dumps
from .bundle import load_bundle
from .budget_program_runtime import BudgetProgramRuntime
from .budget_protocol import BudgetProtocol, SCHEMA_VERSION
from .diagnostics import OntoKinError
from .execution_budget import (DEFAULT_LIMITS, HostPolicy, SharedExecutionBudget,
                               admit_entry_budget, budget_error)
from .json_limits import JSONLimitError, measure_json
from .profile_capabilities import BUDGET_PROFILE
from .program_agent import ProgramAgentService
from .program_store import ProgramStore


class _HostInterrupt(BaseException):
    def __init__(self, error, task):
        self.error, self.task = error, task


class BudgetProgramStore(ProgramStore):
    """Acceptance identity evidence shares the source publication transaction."""

    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or BudgetProtocol())
        with self.transaction() as db:
            db.execute("CREATE TABLE IF NOT EXISTS acceptance_identities ("
                       "project_id TEXT NOT NULL, revision TEXT NOT NULL, "
                       "implementation TEXT NOT NULL, identities TEXT NOT NULL, "
                       "PRIMARY KEY(project_id, revision))")


class _BudgetCheck:
    """The callback carries a single immutable-policy request context."""

    def __init__(self, service, task):
        self.service, self.task, self.request = service, task, task.request
        self.policy = service.host_policy
        self.last_poll = 0.0
        self.program_revision = None
        self.entry_revision = None
        self._last_clock = None
        self._clock_failed = False
        self._host_clock = time.monotonic if service._clock is None else service._clock
        caps = {key: value for key, value in self.request.get("budgets", {}).items()
                if key in DEFAULT_LIMITS}
        self.execution_budget = SharedExecutionBudget(
            self.policy, caps, check=self._poll, clock=self._read_clock)

    def _read_clock(self):
        # Failure transport uses the last established time. Recalling a broken
        # host clock would hide its original exception and strand the request.
        if self._clock_failed:
            return 0.0 if self._last_clock is None else self._last_clock
        try:
            value = self._host_clock()
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or self._last_clock is not None and value < self._last_clock):
                raise ValueError("The trusted clock must return finite monotonic seconds.")
        except BaseException as error:
            self._clock_failed = True
            if hasattr(self, "execution_budget"):
                self.execution_budget.budget_reason = "host_clock_failed"
            raise _HostInterrupt(error, self.task) from None
        self._last_clock = value
        return value

    @property
    def operations(self):
        return self.execution_budget.operations

    @property
    def started(self):
        return self.execution_budget.started

    @property
    def limits(self):
        return {**self.service._protocol.MAX_BUDGETS, **self.execution_budget.limits}

    def _poll(self):
        if self.service._host_check is not None:
            try:
                self.service._host_check()
            except BaseException as error:
                raise _HostInterrupt(error, self.task) from None
        now = time.monotonic()
        if now - self.last_poll >= .005 or self.service._store.closed:
            self.last_poll = now
            with self.service._store.connection() as db:
                row = self.service._store.request(db, self.request["project_id"],
                                                  self.request["request_id"])
            if (self.service._store.closed or row is None or row["state"] != "running"
                    or row["owner"] != self.service._store.owner or row["cancel_requested"]):
                raise _Cancelled()

    def __call__(self):
        self.execution_budget.tick()

    def admit(self, source):
        ledger = self.execution_budget
        if ledger.resolved is None:
            self.program_revision = source.program_revision
            self.entry_revision = source.entry.revision
            admit_entry_budget(source.entry, ledger, profile=self.service._profile)
        elif (source.program_revision != self.program_revision
              or source.entry.revision != self.entry_revision):
            budget_error("execution_context_required",
                         "One Agent request cannot replace its admitted source bundle.")
        ledger.checkpoint()

    def report(self, status):
        ledger = self.execution_budget
        return {**ledger.report(status=status),
                "started_monotonic_seconds": ledger.started,
                "deadline_monotonic_seconds": ledger.started + ledger.limits["max_elapsed_ms"] / 1000,
                "implementation": self.service.implementation,
                "program_revision": self.program_revision,
                "entry_revision": self.entry_revision,
                "request_id": self.request["request_id"],
                "provisional": ledger.resolved is None}


# Retain the exact native reader function for .22's callback-free clock proof.
# Earlier profiles do not use this binding or change any clock behavior.
_NATIVE_BUDGET_READ_CLOCK = _BudgetCheck._read_clock
_NATIVE_BUDGET_READ_CLOCK_AUTHORITY = (_BudgetCheck._read_clock.__code__,
    _BudgetCheck._read_clock.__defaults__, _BudgetCheck._read_clock.__kwdefaults__,
    _BudgetCheck._read_clock.__closure__, _BudgetCheck._read_clock.__globals__,
    _BudgetCheck._read_clock.__builtins__, (("type", type), ("int", int), ("float", float)),
    _BudgetCheck.__bases__, _BudgetCheck.__mro__)


class BudgetAgentService(ProgramAgentService):
    """Explicit local budget service; host configuration is never JSON authority."""

    store_type = BudgetProgramStore
    protocol_type = BudgetProtocol
    runtime_type = BudgetProgramRuntime

    @staticmethod
    def catalog(**kwargs):
        from .budget_agent_catalog import catalog
        return catalog(**kwargs)

    def __init__(self, store_path, *, host_policy=None, protocol=SCHEMA_VERSION,
                 max_running_requests=4, max_pending_requests=256, check=None, clock=None):
        if protocol != self.protocol_type.SCHEMA_VERSION:
            raise ProtocolError("OKA-E-REQUEST", type(self).__name__ + " requires " +
                                self.protocol_type.SCHEMA_VERSION + ".")
        self.host_policy = HostPolicy() if host_policy is None else host_policy
        for name, value in (("max_running_requests", max_running_requests),
                            ("max_pending_requests", max_pending_requests)):
            if type(value) is not int or not 1 <= value <= 10000:
                raise ValueError(name + " must be an integer from 1 through 10000.")
            setattr(self, name, value)
        if check is not None and not callable(check):
            raise TypeError("check must be a trusted callable.")
        if clock is not None and not callable(clock):
            raise TypeError("clock must be a trusted monotonic callable.")
        self._host_check, self._clock = check, clock
        self._protocol = self.protocol_type()
        self._profile = self._protocol.profile
        self._destination = self._protocol.destination
        self._runtime = self.runtime_type()
        self._store_type = partial(self.store_type, protocol=self._protocol)
        AgentService.__init__(self, store_path)

    @property
    def host_policy(self):
        return self._host_policy

    @host_policy.setter
    def host_policy(self, value):
        if not isinstance(value, HostPolicy):
            raise TypeError("host_policy must be a HostPolicy supplied by the trusted host.")
        self._host_policy = value

    def _admit_request(self, db, request):
        if request["operation"] not in {"status", "cancel"}:
            pending = db.execute("SELECT count(*) FROM requests WHERE state IN ('queued','running')").fetchone()[0]
            if pending >= self.max_pending_requests:
                raise ProtocolError("OKA-E-RESOURCE", "The independent service pending-request limit is full.",
                                    service_limit="max_pending_requests", limit=self.max_pending_requests,
                                    effects_committed=False)

    def _next_request(self, db):
        running = db.execute("SELECT count(*) FROM requests WHERE state='running'").fetchone()[0]
        if running >= self.max_running_requests:
            return None
        return super()._next_request(db)

    def _make_check(self, task):
        try:
            task.execution_check = _BudgetCheck(self, task)
        except _HostInterrupt:
            raise
        except BaseException as error:
            raise _HostInterrupt(error, task) from None
        return task.execution_check

    def work_next(self):
        try:
            return super().work_next()
        except _HostInterrupt as interrupted:
            # The host's exception is not a source diagnostic. Record that no
            # tentative effects survived, then propagate the same object.
            task = interrupted.task
            task.accept, task.run, task.artifact = False, None, None
            task.bounded_failure = True
            task.response.update(status="cancelled", achieved_level=None, run_id=None,
                                 result=None, progress={"phase": "host_cancelled",
                                                        "cancellation_requested": True})
            self._finish(task)
            raise interrupted.error from None

    def _snapshot(self, task, source):
        check = task.execution_check
        check.execution_budget.stage = "source_snapshot"
        for unit in source.units:
            check.execution_budget.tick(amount=max(1, (len(unit.raw) + 63) // 64))
        super()._snapshot(task, source)
        check.admit(task.source)

    def _context_binding(self):
        return {"implementation": self.implementation, "protocol": self._protocol.SCHEMA_VERSION,
                "entry_profile": self._profile}

    def _absorb(self, task, result, *, origin=None):
        super()._absorb(task, result, origin=origin)
        if result.get("outcome") == "resource_limit":
            task.run, task.artifact, task.accept = None, None, False
            result.pop("run_state", None)
            task.response["run_id"] = None
        from .reach_context import register_fresh
        task.publication_context = register_fresh(
            result, run=task.run, inspection_run_id=task.request.get("run_id"))

    def _bind_publication_context(self, task, *, accepted_revision, source_accepted_once):
        from .reach_context import bind_fresh
        bind_fresh(task.publication_context, result=task.response.get("result"), run=task.run,
                   accepted_revision=accepted_revision, source_accepted_once=source_accepted_once)

    def _validate(self, task, check):
        request = task.request
        if request["requested_level"] == "delivered" and request.get("destination") == self._destination:
            self._force_delivery(task, check)
        else:
            result = self._runtime.validate_revision(task.source, level=request["requested_level"],
                budgets=request.get("budgets"), check=check)
            self._absorb(task, result, origin="validation")
        if task.response["status"] == "succeeded":
            task.identity_map = self._runtime.identity_map(task.source,
                budgets=request.get("budgets"), check=check)

    def _force_delivery(self, task, check):
        compiler, result = self._runtime.prepare_delivery(task.source,
            until=task.request.get("options", {}).get("end"),
            budgets=task.request.get("budgets"), check=check)
        result["requested_level"] = "delivered"
        task.response["requested_level"] = "delivered"
        self._absorb(task, result, origin="validation")
        if result["outcome"] == "valid":
            self._export(task, check, compiler=compiler)
            task.response["achieved_level"] = result["achieved_level"] = "delivered"

    def _identity_gate(self, before, candidate, check, budgets):
        with self._store.connection() as db:
            row = db.execute("SELECT implementation,identities FROM acceptance_identities "
                             "WHERE project_id=? AND revision=?",
                             (check.request["project_id"], before.program_revision)).fetchone()
        if row is None or json.loads(row["implementation"]) != self.implementation:
            raise ProtocolError("OKA-E-ENGINE", "The accepted revision has no compatible complete identity descriptor.",
                                repair="Validate this accepted revision under current host authority before editing.",
                                effects_committed=False)
        previous = json.loads(row["identities"])
        check.execution_budget.stage = "identity_comparison"
        measure_json(previous, check=check)
        current = self._runtime.identity_map(candidate, budgets=budgets, check=check)
        old = {tuple(item["element_id"]): item["definition_id"] for item in previous}
        changed = []
        for item in current:
            check()
            key = tuple(item["element_id"])
            if key in old and old[key] != item["definition_id"]:
                changed.append(list(key))
        if changed:
            raise OntoKinError("OKL-E-ID", "An existing occurrence cannot change its nominal definition without a new key.",
                               category="invalid", phase="binding", rule_ids=["LANG-007"],
                               details={"changed_occurrences": changed})
        check.task.identity_map = current

    def _persist_task_metadata(self, db, task):
        identities = getattr(task, "identity_map", None)
        if (identities is not None and task.response["status"] == "succeeded"
                and (task.accept or self._source_accepted_db(db, task.request["project_id"],
                                                           task.source.program_revision))):
            db.execute("INSERT INTO acceptance_identities VALUES (?,?,?,?) "
                       "ON CONFLICT(project_id,revision) DO UPDATE SET implementation=excluded.implementation,identities=excluded.identities",
                       (task.request["project_id"], task.source.program_revision,
                        dumps(self.implementation), dumps(identities)))

    def _execute(self, task, check):
        operation = task.request["operation"]
        if operation == "discover":
            return self._discover(task, check)
        if operation == "artifact":
            return self._read_artifact(task)
        if operation not in {"create", "edit"}:
            task.source = self.read_program(task.request["project_id"], task.request["program_revision"])
            task.response["program_revision"] = task.source.program_revision
            check.admit(task.source)
        if operation == "export":
            if not self._store.source_accepted_once(task.request["project_id"], task.source.program_revision):
                raise OntoKinError("OKL-E-REVISION", "Export requires a previously accepted program.",
                                   category="stale", phase="inspection", blocks=[])
            return self._force_delivery(task, check)
        return super()._execute(task, check)

    def _export(self, task, check, *, compiler=None):
        from .gltf import export_glb
        from .scene import ExportOptions
        check.admit(task.source)
        if compiler is None:
            raise ProtocolError("OKA-E-INTERNAL", "Budget delivery requires its already evaluated request compiler.")
        ledger = check.execution_budget
        ledger.stage = "recording_export_readback"
        try:
            artifact = export_glb(compiler.model,
                options=ExportOptions(**task.request.get("options", {})),
                source_uri=task.source.entry.filename, source_sha256=task.source.entry.revision,
                target_contract=self._destination, work=compiler.reach_work,
                reach_plan=compiler.reach_delivery_plan)
        except _Interrupt as interrupted:
            raise interrupted.error from None
        ledger.checkpoint()
        digest = hashlib.sha256(artifact.data).hexdigest()
        artifact_id = "artifact:" + digest
        report = {**artifact.report, "implementation_identity": copy.deepcopy(self.implementation),
                  "producer_request_id": task.request["request_id"],
                  "execution_budget_at_export": check.report("export_verified_pending_publication")}
        task.artifact = (artifact.data, report, artifact_id)
        task.response["result"].update(artifact_id=artifact_id, report=report,
            program_revision=task.source.program_revision, total_bytes=len(artifact.data),
            sha256="sha256:" + digest, mime_type="model/gltf-binary", destination=self._destination)

    def _read_artifact(self, task):
        request, check = task.request, task.execution_check
        with self._store.connection() as db:
            row = db.execute("SELECT source_revision,length(data) AS total FROM artifacts WHERE project_id=? AND id=?",
                             (request["project_id"], request["artifact_id"])).fetchone()
        if row is None:
            raise ProtocolError("OKA-E-ARTIFACT", "The artifact is absent from this project.")
        task.source = self.read_program(request["project_id"], row["source_revision"])
        task.response["program_revision"] = task.source.program_revision
        check.admit(task.source)
        if row["total"] > 64 * 1024 * 1024:
            raise ProtocolError("OKA-E-RESOURCE", "The retained artifact exceeds the fixed byte limit.")
        with self._store.connection() as db:
            stored = db.execute("SELECT data,report,sha256 FROM artifacts WHERE project_id=? AND id=?",
                                (request["project_id"], request["artifact_id"])).fetchone()
        data, report = bytes(stored["data"]), json.loads(stored["report"])
        if (report.get("program_revision") != task.source.program_revision
                or report.get("implementation_identity") != self.implementation):
            raise ProtocolError("OKA-E-STORE-INTEGRITY", "Artifact provenance does not match its retained source and implementation.")
        ledger = check.execution_budget
        ledger.stage = "artifact_integrity"
        digest = hashlib.sha256()
        for start in range(0, len(data), 65536):
            chunk = data[start:start + 65536]
            ledger.tick(amount=max(1, (len(chunk) + 63) // 64))
            digest.update(chunk)
        actual = digest.hexdigest()
        if "sha256:" + actual != stored["sha256"] or "artifact:" + actual != request["artifact_id"]:
            raise ProtocolError("OKA-E-STORE-INTEGRITY", "The retained artifact bytes do not match their identity.")
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

    def _discover(self, task, check=None):
        request = task.request
        if request["profile"] != self._profile:
            raise ProtocolError("OKL-E-CAPABILITY-UNSUPPORTED", self._protocol.SCHEMA_VERSION +
                                " requires " + self._profile + ".")
        if request["limit"] > request.get("budgets", {}).get("max_result_items", 1000):
            raise ProtocolError("OKA-E-RESOURCE", "Discovery exceeds the requested item limit.")
        if "bundle" in request:
            task.source = self._create_source(request)
        elif "program_revision" in request:
            task.source = self.read_program(request["project_id"], request["program_revision"])
        linked = None
        if task.source is not None:
            from .linker import link_program
            task.response["program_revision"] = task.source.program_revision
            check.admit(task.source)
            linked = link_program(task.source, check=check)
        else:
            for key, value in check.execution_budget.caller_caps.items():
                if value > DEFAULT_LIMITS[key]:
                    budget_error("request_cap_exceeds_source", "Source-free discovery cannot enlarge default work.")
        result = self.catalog(policy=check.policy, linked_program=linked, check=check,
                         aggregate_limits=self.aggregate_limits())
        context = {"project_id": request["project_id"], "operation": "discover",
                   "catalog_revision": result["revision"],
                   "program_revision": None if task.source is None else task.source.program_revision,
                   "profile": self._profile, "filter": request.get("filter"), **self._context_binding()}
        offset = self._offset(request.get("cursor"), context)
        items, selected = result["items"], []
        filter_ = request.get("filter")
        for item in items:
            check()
            if (filter_ is None or isinstance(filter_, str) and filter_.lower() in dumps(item).lower()
                    or isinstance(filter_, dict) and all(item.get(k) == v for k, v in filter_.items())):
                selected.append(item)
        result.update(items=selected[offset:offset + request["limit"]], total=len(selected), offset=offset)
        next_offset = offset + len(result["items"]) if offset + len(result["items"]) < len(selected) else None
        task.response.update(status="succeeded", result=result, truncated=next_offset is not None,
                             next_cursor=None if next_offset is None else self._cursor(context, next_offset))

    def aggregate_limits(self):
        return {"max_running_requests": self.max_running_requests,
                "max_pending_requests": self.max_pending_requests,
                "scope": "Shared local database, checked by each admitting service's trusted limits",
                "memory_and_retention": "Configured independently by the embedding host"}

    def _semantic_error(self, task, error):
        if (error.diagnostic.details or {}).get("budget_reason"):
            task.run = None
            error.diagnostic.details["request_terminated"] = True
        return super()._semantic_error(task, error)

    def _check_task_response(self, task):
        check = getattr(task, "execution_check", None)
        if task.response["status"] == "cancelled":
            task.response.update(result=None, achieved_level=None, run_id=None)
        elif task.response["status"] in {"rejected", "failed"}:
            # A completed encoder result is still tentative until the source
            # and run fences commit. Do not return a nonexistent artifact as
            # delivered when a late edit conflict or identity check rejects it.
            result = task.response.get("result")
            if isinstance(result, dict):
                for key in ("artifact_id", "report", "total_bytes", "sha256", "mime_type",
                            "destination", "data_base64", "artifact_provenance", "producer_request_id"):
                    result.pop(key, None)
                if task.response.get("requested_level") == "delivered":
                    result["delivery"] = "failed"
            if task.response.get("achieved_level") == "delivered":
                run = task.run or (result.get("run_state") if isinstance(result, dict) else None)
                achieved = "evaluated" if isinstance(run, dict) and run.get("valid_until_seconds") is not None else None
                task.response["achieved_level"] = achieved
                if isinstance(result, dict):
                    result["achieved_level"] = achieved
        if check is not None:
            task.response["execution_budget"] = check.report(task.response["status"])
        # Failed transport is bounded but cannot consume another product grant.
        if task.response["status"] != "succeeded" or getattr(task, "bounded_failure", False):
            self._check_response(task.response)
            return
        ledger = check.execution_budget
        ledger.stage = "publication"
        try:
            measure_json(task.response,
                         max_entries=task.request.get("budgets", {}).get("max_value_entries", 100000),
                         check=ledger.tick)
            ledger.checkpoint()
            task.response["execution_budget"] = check.report(task.response["status"])
        except (OntoKinError, JSONLimitError) as error:
            details = (error.diagnostic.details if isinstance(error, OntoKinError) else error.details)
            raise ProtocolError("OKL-E-RESOURCE", "The complete result exceeded its shared request allowance; no effects committed.",
                                **details, effects_committed=False) from error

    def _finish(self, task):
        try:
            return super()._finish(task)
        except _Cancelled:
            task.accept, task.run, task.artifact = False, None, None
            task.bounded_failure = True
            task.response.update(status="cancelled", result=None, achieved_level=None, run_id=None)
            return super()._finish(task)
