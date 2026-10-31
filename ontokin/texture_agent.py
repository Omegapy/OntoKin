"""Source and image attachment authoring under the durable request lifecycle."""
from __future__ import annotations

from .budget_agent import BudgetAgentService
from .texture_bundle import load_texture_bundle
from .texture_program_runtime import TextureProgramRuntime
from .texture_protocol import SCHEMA_VERSION, TextureProtocol, asset_selector
from .texture_store import TextureProgramStore


class TextureAgentService(BudgetAgentService):
    """Explicit Agent/0.13 with independent storage and current host authority."""

    protocol_type = TextureProtocol
    runtime_type = TextureProgramRuntime
    store_type = TextureProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .texture_agent_catalog import catalog
        return catalog(**kwargs)

    @staticmethod
    def _create_source(request):
        return load_texture_bundle(request["bundle"])

    def _edit_source(self, base, request, check):
        return self._runtime.apply_patches(base, request["patches"],
            module_changes=request.get("module_changes"), asset_changes=request.get("asset_changes"),
            budgets=request.get("budgets"), check=check)

    def _snapshot(self, task, source):
        ledger = task.execution_check.execution_budget
        ledger.stage = "asset_snapshot"
        for asset in source.assets:
            ledger.tick(amount=max(1, (len(asset.raw) + 63) // 64))
        super()._snapshot(task, source)

    def _inspect(self, task, check):
        request = task.request
        if not asset_selector(request["selector"]):
            return super()._inspect(task, check)
        context = {"project_id": request["project_id"], "operation": "inspect",
            "program_revision": task.source.program_revision,
            "selector": request["selector"], "fields": sorted(request["fields"]),
            "run_id": request.get("run_id"), "time": request.get("time"),
            "frame": request.get("frame"), **self._context_binding()}
        offset = self._offset(request.get("cursor"), context)
        result = self._runtime.inspect_assets(task.source, selector=request["selector"],
            fields=request["fields"], limit=request["limit"], offset=offset,
            asset_slice=request.get("asset_slice"), budgets=request.get("budgets"), check=check)
        self._absorb(task, result)
        task.response["truncated"] = result.get("truncated", False)
        if "asset_slice" not in request and result.get("next_offset") is not None:
            task.response["next_cursor"] = self._cursor(context, result["next_offset"])
