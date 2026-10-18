"""Durable versioned program service sharing the proven request lifecycle."""
from __future__ import annotations

import hashlib
import json
from functools import partial

from .agent import AgentService
from .agent_protocol import ProtocolError
from .agent_store import dumps
from .bundle import load_bundle
from .diagnostics import OntoKinError
from .json_limits import measure_json, JSONLimitError
from .program_diagnostics import diagnostic_dict
from .program_store import ProgramStore
from . import program_protocol, program_runtime


class ProgramAgentService(AgentService):
    _protocol = program_protocol
    _runtime = program_runtime
    _store_type = ProgramStore
    _revision_key = "program_revision"
    _accepted_key = "accepted_program_revision"
    _expected_key = "expected_program_revision"
    _destination = "ontokin.glb/0.2"

    def __init__(self, store_path, *, protocol=program_protocol.SCHEMA_VERSION):
        self._protocol = program_protocol.bind(protocol)
        self._profile = self._protocol.profile
        self._destination = self._protocol.destination
        self._runtime = program_runtime.ProgramRuntime(self._profile)
        self._store_type = partial(ProgramStore, protocol=self._protocol)
        super().__init__(store_path)

    @staticmethod
    def _revision(program):
        return program.program_revision

    @staticmethod
    def _create_source(request):
        return load_bundle(request["bundle"])

    def read_program(self, project_id, program_revision):
        return self.read_source(project_id, program_revision)

    def read_unit(self, project_id, program_revision, source_id):
        program = self.read_program(project_id, program_revision)
        if source_id not in program.sources:
            raise ProtocolError("OKL-E-REVISION", "The source ID is not in this immutable program.", source_id=source_id)
        return program.sources[source_id]

    def _edit_source(self, base, request, check):
        return self._runtime.apply_patches(base, request["patches"], module_changes=request.get("module_changes"),
                                            budgets=request.get("budgets"), check=check)

    @staticmethod
    def _diagnostic(error, program, run_id=None):
        return diagnostic_dict(error.diagnostic, program, run_id)

    def _read_artifact(self, task):
        super()._read_artifact(task)
        with self._store.connection() as db:
            row = db.execute("SELECT report FROM artifacts WHERE project_id=? AND id=?",
                             (task.request["project_id"], task.request["artifact_id"])).fetchone()
        report = json.loads(row["report"])
        task.response["result"]["artifact_provenance"] = {
            "exporter": report["exporter"], "source_code_sha256": "sha256:" + report["source_code_sha256"],
            "program_revision": report["program_revision"]}

    def _cursor(self, context, offset):
        token = super()._cursor(context, offset)
        if len(token.encode("utf-8")) > 65536:
            raise ProtocolError("OKA-E-RESOURCE", "The complete immutable query context cannot fit a bounded cursor.")
        return token

    def _context_binding(self):
        return {"implementation": self.implementation, "protocol": self._protocol.SCHEMA_VERSION}

    def _execute(self, task, check):
        if task.request["operation"] != "surface.mesh_page":
            return super()._execute(task, check)
        from .program_surface import prepare_surface_page
        request = task.request
        task.source = self.read_program(request["project_id"], request["program_revision"])
        task.response["program_revision"] = task.source.program_revision
        if not self._store.source_accepted_once(request["project_id"], task.source.program_revision):
            raise OntoKinError("OKL-E-REVISION", "Surface mesh pages require an accepted program snapshot; this candidate has never been accepted.",
                               category="stale", phase="inspection", blocks=[])
        query = prepare_surface_page(task.source, request["element_id"], region=request.get("region"),
                                     count=request["count"], budgets=request.get("budgets"), check=check)
        context = {"project_id": request["project_id"], "operation": "surface.mesh_page",
                   **query.binding(), **self._context_binding()}
        offset = self._offset(request.get("cursor"), context)
        try:
            result, next_offset = query.page(offset, request["count"])
        except program_runtime._Interrupt as exc:
            raise exc.error
        task.response.update(status="succeeded", achieved_level="constructed", run_id=None,
                             result=result, truncated=next_offset is not None,
                             next_cursor=None if next_offset is None else self._cursor(context, next_offset))

    def _check_response(self, response):
        try:
            measure_json(response)
        except JSONLimitError as exc:
            raise ProtocolError("OKA-E-RESOURCE", "The complete response exceeds the program JSON envelope limit; no new effects were committed.",
                                **exc.details, effects_committed=False,
                                repair="Request fewer fields/items or retrieve separate source units and artifact chunks.") from exc
        except (TypeError, ValueError, RecursionError) as exc:
            raise ProtocolError("OKA-E-INTERNAL", "The operation produced an invalid bounded JSON response.",
                                exception=type(exc).__name__, effects_committed=False) from exc

    def _check_task_response(self, task):
        self._check_response(task.response)
        limit = task.request.get("budgets", {}).get("max_value_entries")
        if self._profile != "surface-0.1" or limit is None or task.response["status"] != "succeeded":
            return
        # The final check runs inside the publication transaction after source
        # identity, cursor, implementation and progress metadata are present.
        # A smaller user budget cannot suppress the bounded failure receipt.
        try:
            measure_json(task.response, max_entries=limit)
        except JSONLimitError as exc:
            raise ProtocolError("OKA-E-RESOURCE", "The complete native response exceeds its requested value-entry budget; no new effects were committed.",
                                **exc.details, effects_committed=False,
                                repair="Request fewer triangles/fields or increase max_value_entries within the published limit.") from exc

    def _discover(self, task, check=None):
        from .construction_catalog import catalog
        from .linker import link_program
        request = task.request
        if request["profile"] != self._profile:
            raise ProtocolError("OKL-E-CAPABILITY-UNSUPPORTED", "This binding requires " + self._profile + ".", available_profiles=[self._profile])
        if request["limit"] > request.get("budgets", {}).get("max_result_items", 1000):
            raise ProtocolError("OKA-E-RESOURCE", "Discovery limit exceeds its requested result-item budget.")
        linked = None
        if "bundle" in request:
            task.source = load_bundle(request["bundle"])
        elif "program_revision" in request:
            task.source = self.read_program(request["project_id"], request["program_revision"])
        if task.source is not None:
            task.response["program_revision"] = task.source.program_revision
            linked = link_program(task.source, check=check)
            if linked.entry.ast.profile != self._profile:
                raise ProtocolError("OKL-E-CAPABILITY-UNSUPPORTED", "Discovery entry does not match this program binding.",
                                    required_profile=self._profile, actual_profile=linked.entry.ast.profile)
        result = catalog(linked_program=linked, check=check, profile=self._profile)
        context = {"project_id": request["project_id"], "operation": "discover", "catalog_revision": result["revision"],
                   "program_revision": None if task.source is None else task.source.program_revision,
                   "profile": request["profile"], "filter": request.get("filter"), **self._context_binding()}
        offset = self._offset(request.get("cursor"), context)
        items = result["items"]
        filter_ = request.get("filter")
        if isinstance(filter_, str):
            selected = []
            for item in items:
                if check is not None:
                    check()
                measure_json(item)
                if filter_.lower() in dumps(item).lower():
                    selected.append(item)
            items = selected
        elif isinstance(filter_, dict):
            items = [item for item in items if all(item.get(key) == value for key, value in filter_.items())]
        total = len(items)
        result.update(items=items[offset:offset + request["limit"]], total=total, offset=offset)
        next_offset = offset + len(result["items"]) if offset + len(result["items"]) < total else None
        task.response.update(status="succeeded", result=result, truncated=next_offset is not None,
                             next_cursor=None if next_offset is None else self._cursor(context, next_offset))

    def _export(self, task, check):
        from .gltf import export_glb
        from .scene import ExportOptions
        compiler = self._runtime.compile_program(task.source, budgets=task.request.get("budgets"), check=check)
        # Agent/0.2's frozen operation budget never counted internal GLB work.
        # The separately selected Agent/0.3 contract adds cooperative delivery
        # checks without retroactively rejecting formerly valid old requests.
        delivery_check = check if self._profile == "surface-0.1" else None
        artifact = export_glb(compiler.model, options=ExportOptions(**task.request.get("options", {})),
                              source_uri=task.source.entry.filename, source_sha256=task.source.entry.revision,
                              target_contract=self._destination, check=delivery_check)
        check()
        sha = hashlib.sha256(artifact.data).hexdigest()
        artifact_id = "artifact:" + sha
        task.artifact = (artifact.data, artifact.report, artifact_id)
        task.response["result"].update(artifact_id=artifact_id, report=artifact.report,
                                       program_revision=task.source.program_revision,
                                       total_bytes=len(artifact.data), sha256="sha256:" + sha,
                                       mime_type="model/gltf-binary", destination=self._destination)
