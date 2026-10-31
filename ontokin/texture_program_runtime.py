"""Atomic source/asset candidates and bounded immutable attachment inspection."""
from __future__ import annotations

import base64

from . import program_runtime as runtime
from .agent_protocol import ProtocolError
from .agent_runtime import _Interrupt
from .budget_program_runtime import BudgetProgramRuntime, ExecutionProgramBudget
from .bundle import BundleError, ProgramBundle
from .diagnostics import OntoKinError
from .profile_capabilities import TEXTURE_PROFILE
from .texture_bundle import TextureBundle
from .texture_protocol import load_asset_descriptor


def _edit_error(message, *, category="conflict", **details):
    raise OntoKinError("OKL-E-REVISION", message, category=category, phase="edit", details=details)


class TextureProgramRuntime(BudgetProgramRuntime):
    profile = TEXTURE_PROFILE

    def apply_patches(self, source, patches, *, module_changes=None, asset_changes=None,
                      budgets=None, check=None):
        """Prepare all changes before admitting or publishing the one candidate."""
        try:
            budget = ExecutionProgramBudget(budgets, check, profile=self.profile)
            budget.execution_budget.stage = "edit_preparation"
            if not isinstance(source, TextureBundle):
                _edit_error("Texture edits require an immutable bundle/0.2.")
            # This inherited operation performs exact UTF-8 preconditions only.
            # Its temporary source-only value is never admitted or snapshotted.
            # Avoid its source-descriptor preparation encoding unused PNG data.
            source_units = ProgramBundle(source.entry, source.modules)
            patched = self._call(runtime.apply_patches, source_units, patches=patches,
                                 module_changes=module_changes, budgets=budgets, check=check)
            original = {asset.asset_id: asset for asset in source.assets}
            candidate, touched = dict(original), set()
            for change in asset_changes or []:
                budget.tick()
                mode = change["operation"]
                key = change["asset"]["asset_id"] if mode == "add" else change["asset_id"]
                if key in touched:
                    _edit_error("One candidate cannot touch the same asset ID twice.", asset_id=key)
                touched.add(key)
                old = original.get(key)
                if mode == "add":
                    if old is not None:
                        _edit_error("An asset addition requires an absent original ID.", asset_id=key)
                elif old is None or old.sha256 != change["expected_sha256"]:
                    _edit_error("The asset change requires its exact original digest.",
                                category="stale", asset_id=key)
                if mode == "remove":
                    del candidate[key]
                    continue
                descriptor = change["asset"]
                if descriptor["asset_id"] != key:
                    _edit_error("An asset replacement must retain the same stable ID.", asset_id=key)
                budget.execution_budget.tick(amount=max(1, (len(descriptor["data_base64"]) + 63) // 64))
                try:
                    candidate[key] = load_asset_descriptor(descriptor)
                except ProtocolError as exc:
                    raise OntoKinError("OKL-E-RESOURCE" if exc.code == "OKA-E-RESOURCE" else "OKL-E-REVISION",
                        str(exc), category="resource_limit" if exc.code == "OKA-E-RESOURCE" else "conflict",
                        phase="edit", details=exc.details) from exc
            try:
                result = TextureBundle(patched.entry, patched.modules, tuple(candidate.values()))
            except BundleError as exc:
                raise OntoKinError("OKL-E-RESOURCE" if exc.code == "OKA-E-RESOURCE" else "OKL-E-REVISION",
                    str(exc), category="resource_limit" if exc.code == "OKA-E-RESOURCE" else "conflict",
                    phase="edit", details=exc.details) from exc
            budget.tick()
            return result
        except _Interrupt as interrupted:
            raise interrupted.error from None

    def inspect_assets(self, source, *, selector, fields, limit, offset=0,
                       asset_slice=None, budgets=None, check=None):
        """Read retained bytes without claiming PNG or source semantic validity."""
        try:
            budget = ExecutionProgramBudget(budgets, check, profile=self.profile)
            check.admit(source)
            budget.execution_budget.stage = "asset_inspection"
            if limit > budget.limits["max_result_items"]:
                raise ProtocolError("OKA-E-RESOURCE", "Asset inspection exceeds the caller's item limit.")
            selected = []
            wanted = selector.get("element_id")
            for asset in source.assets:
                budget.tick()
                if wanted is None or wanted == ["assets", asset.asset_id]:
                    selected.append(asset)
            if wanted is not None and not selected:
                raise ProtocolError("OKL-E-REVISION", "The attachment is absent from this immutable revision.",
                                    element_id=wanted)
            items = []
            for asset in selected[offset:offset + limit]:
                budget.execution_budget.tick(amount=max(1, (len(asset.raw) + 63) // 64))
                record = {"element_id": ["assets", asset.asset_id], "kind": "texture_asset",
                          "name": asset.asset_id}
                if "identity" in fields:
                    record["identity"] = {"asset_id": asset.asset_id,
                                          "element_id": ["assets", asset.asset_id],
                                          "kind": "texture_asset"}
                if "source" in fields:
                    record["source"] = {"asset_id": asset.asset_id,
                        "program_revision": source.program_revision, "sha256": asset.sha256,
                        "media_type": asset.media_type, "total_bytes": len(asset.raw)}
                items.append(record)
            next_offset = offset + len(items) if offset + len(items) < len(selected) else None
            result = runtime._result(source, None, None, [], items=items, total=len(selected),
                offset=offset, next_offset=next_offset, truncated=next_offset is not None,
                index_complete=True, asset_semantics="immutable transport identity; PNG validity is not asserted")
            if asset_slice is not None:
                asset = selected[0]
                start, count = asset_slice["offset"], asset_slice["max_bytes"]
                if start > len(asset.raw):
                    raise ProtocolError("OKA-E-REQUEST", "The asset slice starts after the exact attachment length.",
                                        offset=start, total_bytes=len(asset.raw))
                end = min(len(asset.raw), start + count)
                budget.execution_budget.tick(amount=max(1, (end - start + 63) // 64))
                encoded = base64.b64encode(asset.raw[start:end]).decode("ascii")
                budget.tick()
                result.update(asset_id=asset.asset_id, element_id=["assets", asset.asset_id],
                    program_revision=source.program_revision, sha256=asset.sha256,
                    media_type=asset.media_type, total_bytes=len(asset.raw), offset=start,
                    returned_bytes=end - start, data_base64=encoded,
                    next_offset=end if end < len(asset.raw) else None, complete=end == len(asset.raw),
                    truncated=False)
            return budget.json(result)
        except _Interrupt as interrupted:
            raise interrupted.error from None
