"""Explicit Agent/0.13 transport for immutable source and image attachments."""
from __future__ import annotations

import json
import re

from . import program_protocol as legacy
from .agent_protocol import (FIELDS, LEVELS, ProtocolError, _bad, _integer,
                             _object, _options, _seconds, _text)
from .budget_protocol import BudgetProtocol
from .bundle import BundleError
from .json_limits import JSONLimitError, bounded_dumps
from .program_bindings import ProgramBinding
from .profile_capabilities import TEXTURE_PROFILE
from .texture_bundle import load_texture_bundle


SCHEMA_VERSION = "ontokin.agent/0.13"
MAX_REQUEST_BYTES = 8_388_608
ASSET_ID_RE = re.compile(r"[a-z][a-z0-9._-]{0,63}\Z", re.ASCII)
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.13", TEXTURE_PROFILE,
    "ontokin.glb/0.13", "texture-program-agent.sqlite3",
    "ontokin.texture-program-agent-store/0.1", True, True)
OPERATIONS = {name: (set(required), set(optional))
              for name, (required, optional) in BudgetProtocol.OPERATIONS.items()}
OPERATIONS["edit"][1].add("asset_changes")
OPERATIONS["inspect"][1].add("asset_slice")


def asset_selector(selector):
    """Recognize the reserved attachment namespace before ordinary inspection."""
    if not isinstance(selector, dict):
        return False
    identity = selector.get("element_id")
    return (selector.get("kind") == "texture_asset"
            or isinstance(identity, list) and bool(identity) and identity[0] == "assets")


def asset_id(value, name="asset_id"):
    if not isinstance(value, str) or ASSET_ID_RE.fullmatch(value) is None:
        _bad(name + " requires a lowercase ASCII asset ID of at most 64 characters.")


def load_asset_descriptor(value):
    """Check attachment transport only, without PNG parsing or execution."""
    try:
        return load_texture_bundle({"schema_version": "ontokin.bundle/0.2",
            "entry": {"filename": "<asset-shape>", "source": ""},
            "modules": [], "assets": [value]}).assets[0]
    except BundleError as exc:
        raise ProtocolError(exc.code, str(exc), **exc.details) from exc


def canonical_request(value):
    try:
        payload = bounded_dumps(value, max_bytes=MAX_REQUEST_BYTES)
        clean = json.loads(payload)
    except JSONLimitError as exc:
        raise ProtocolError("OKA-E-RESOURCE", "The request exceeds the Agent/0.13 JSON transport.",
                            **exc.details) from exc
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("OKA-E-REQUEST", "The request requires finite JSON and UTF-8 scalar strings.") from exc
    if not isinstance(clean, dict):
        _bad("A request must be a JSON object.")
    return clean, payload


class TextureProtocol(BudgetProtocol):
    """Keep older bundle loaders and protocol registries unchanged."""

    SCHEMA_VERSION = SCHEMA_VERSION
    MAX_REQUEST_BYTES = MAX_REQUEST_BYTES
    definition = DEFINITION
    profile = TEXTURE_PROFILE
    destination = DEFINITION.destination
    OPERATIONS = OPERATIONS
    canonical_request = staticmethod(canonical_request)

    @classmethod
    def validate_request(cls, request):
        op = request.get("operation")
        if (request.get("schema_version") != cls.SCHEMA_VERSION
                or not isinstance(op, str) or op not in cls.OPERATIONS):
            _bad(f"Unknown Agent/{cls.definition.language_version} schema or operation.", operations=sorted(cls.OPERATIONS))
        required, optional = cls.OPERATIONS[op]
        _object(request, "request", legacy.COMMON | required | optional, legacy.COMMON | required)
        for name in ("project_id", "request_id", "target_request_id", "artifact_id"):
            if name in request:
                _text(request[name], name, limit=200)
        for name in ("program_revision", "expected_program_revision"):
            if name in request:
                if op == "create" and name == "expected_program_revision":
                    if request[name] is not None:
                        _bad("Create requires expected_program_revision:null.")
                else:
                    legacy._revision(request[name], name)
        for name in ("run_id", "cursor"):
            if name in request and request[name] is not None:
                _text(request[name], name, limit=65536 if name == "cursor" else 200)
        for name in ("profile", "frame"):
            if name in request:
                _text(request[name], name, limit=32768)
        if "requested_level" in request and request["requested_level"] not in LEVELS:
            _bad("Unknown requested output level.", levels=list(LEVELS))
        if "bundle" in request:
            try:
                load_texture_bundle(request["bundle"])
            except BundleError as exc:
                raise ProtocolError(exc.code, str(exc), **exc.details) from exc
        if op == "discover" and "bundle" in request and "program_revision" in request:
            _bad("Discovery accepts a bundle or a retained revision, not both.")
        if "limit" in request:
            _integer(request["limit"], "limit", 1, 1000)
        if op == "surface.mesh_page":
            legacy._ids(request["element_id"], "element_id")
            _integer(request["count"], "count", 1, 256)
            if "region" in request:
                _text(request["region"], "region", limit=64)
        if "budgets" in request:
            _object(request["budgets"], "budgets", set(cls.MAX_BUDGETS))
            for key, value in request["budgets"].items():
                _integer(value, "budgets." + key, 1, cls.MAX_BUDGETS[key])
        if "until_seconds" in request:
            _seconds(request["until_seconds"], "until_seconds")
        if request.get("time") is not None:
            _object(request["time"], "time", {"seconds", "side"}, {"seconds", "side"})
            _seconds(request["time"]["seconds"], "time.seconds")
            if request["time"]["side"] not in ("before", "after"):
                _bad("time.side must be before or after.")
        if "selector" in request:
            selector = request["selector"]
            _object(selector, "selector", {"element_id", "kind", "path", "class_name", "role", "relation", "source_id"})
            for key, value in selector.items():
                if key == "element_id" or key == "relation" and isinstance(value, list):
                    legacy._ids(value, "selector." + key)
                else:
                    _text(value, "selector." + key, empty=key == "role", limit=32768)
                    if key == "kind" and value not in legacy.KINDS | {"texture_asset"}:
                        _bad("Unknown selector.kind.")
        if "fields" in request:
            fields = request["fields"]
            if (not isinstance(fields, list) or not fields
                    or any(not isinstance(value, str) or value not in FIELDS for value in fields)
                    or len(set(fields)) != len(fields)):
                _bad("fields requires distinct supported field groups.", fields=sorted(FIELDS))
        if op == "inspect" and asset_selector(request["selector"]):
            selector = request["selector"]
            exact = set(selector) == {"element_id"} and len(selector["element_id"]) == 2
            if exact:
                asset_id(selector["element_id"][1], "selector asset ID")
            elif selector != {"kind": "texture_asset"}:
                _bad("Asset inspection requires the exact asset ID or texture_asset kind selector.")
            if set(request["fields"]) - {"identity", "source"}:
                _bad("Asset inspection supports identity and source fields only.")
            if "asset_slice" in request:
                if not exact or any(name in request for name in ("cursor", "run_id", "time", "frame")):
                    _bad("Asset slices require one exact asset ID and no cursor, run, time or frame.")
                _object(request["asset_slice"], "asset_slice", {"offset", "max_bytes"}, {"offset", "max_bytes"})
                _integer(request["asset_slice"]["offset"], "asset_slice.offset", 0)
                _integer(request["asset_slice"]["max_bytes"], "asset_slice.max_bytes", 1, 65536)
        elif "asset_slice" in request:
            _bad("asset_slice is only available for one exact attachment selector.")
        if "patches" in request:
            patches = request["patches"]
            if not isinstance(patches, list) or len(patches) > 1000:
                _bad("patches must contain at most 1,000 records.")
            names = {"source_id", "source_revision", "element_id", "start_byte", "end_byte", "expected_text", "replacement"}
            for patch in patches:
                _object(patch, "patch", names, names)
                _text(patch["source_id"], "patch.source_id", limit=200)
                legacy._revision(patch["source_revision"], "patch.source_revision")
                if patch["element_id"] != ["sources", patch["source_id"]]:
                    _bad(f"Agent/{cls.definition.language_version} patches require the exact source-file scope.")
                for key in ("start_byte", "end_byte"):
                    _integer(patch[key], "patch." + key, 0, 2000000)
                for key in ("expected_text", "replacement"):
                    _text(patch[key], "patch." + key, empty=True, limit=2000000)
        if "module_changes" in request:
            changes = request["module_changes"]
            if not isinstance(changes, list) or len(changes) > 32:
                _bad("module_changes must contain at most 32 records.")
            for change in changes:
                if not isinstance(change, dict) or change.get("operation") not in ("add", "remove", "replace"):
                    _bad("A module change must add, remove or replace.")
                mode = change["operation"]
                names = ({"operation"} | ({"module"} if mode == "add" else {"source_id", "source_revision"})
                         | ({"module"} if mode == "replace" else set()))
                _object(change, "module_change", names, names)
                if mode != "add":
                    _text(change["source_id"], "module_change.source_id", limit=200)
                    legacy._revision(change["source_revision"], "module_change.source_revision")
                if mode != "remove":
                    legacy._module(change["module"])
        if "asset_changes" in request:
            changes = request["asset_changes"]
            if not isinstance(changes, list) or len(changes) > 8:
                _bad("asset_changes must contain at most eight records.")
            for change in changes:
                if not isinstance(change, dict) or change.get("operation") not in ("add", "remove", "replace"):
                    _bad("An asset change must add, remove or replace.")
                mode = change["operation"]
                names = ({"operation"} | ({"asset"} if mode == "add" else {"asset_id", "expected_sha256"})
                         | ({"asset"} if mode == "replace" else set()))
                _object(change, "asset_change", names, names)
                if mode != "add":
                    asset_id(change["asset_id"])
                    legacy._revision(change["expected_sha256"], "asset_change.expected_sha256")
                if mode != "remove":
                    load_asset_descriptor(change["asset"])
        if op == "edit" and not (request["patches"] or request.get("module_changes") or request.get("asset_changes")):
            _bad("An edit requires a source patch, module change or asset change.")
        if "filter" in request:
            if isinstance(request["filter"], str):
                _text(request["filter"], "filter", limit=1024)
            else:
                _object(request["filter"], "filter", {"kind", "name", "capability"})
                for key, value in request["filter"].items():
                    _text(value, "filter." + key, limit=1024)
        if "destination" in request and request["destination"] != cls.destination:
            _bad(f"Agent/{cls.definition.language_version} requires the explicit " + cls.destination + " destination.")
        if "options" in request:
            _options(request["options"])
            if request["options"].get("time_tolerance_s", 1e-6) > 1e-6:
                _bad(f"Agent/{cls.definition.language_version} time_tolerance_s must be at most 1e-6.")
            if "destination" not in request:
                _bad("Export options require an explicit destination contract.")
        if (op in {"create", "edit", "validate"} and ("destination" in request or "options" in request)
                and request["requested_level"] != "delivered"):
            _bad("Destination settings require requested_level:delivered.")
        if "offset" in request:
            _integer(request["offset"], "offset", 0)
        if "max_bytes" in request:
            _integer(request["max_bytes"], "max_bytes", 1, 65536)
