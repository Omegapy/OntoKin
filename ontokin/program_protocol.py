"""Strict versioned agent contracts for immutable pinned source bundles.

Module-level calls retain Agent/0.2. A bound interface selects Agent/0.3
without changing process globals or another service instance's behavior.
"""
from __future__ import annotations

import json
import re

from . import agent_protocol as core
from .agent_protocol import ProtocolError, LEVELS, TERMINAL, FIELDS, _bad, _text, _integer, _object, _seconds, _options
from .json_limits import bounded_dumps, JSONLimitError, MAX_JSON_BYTES, MAX_JSON_ENTRIES

SCHEMA_VERSION = "ontokin.agent/0.2"
SURFACE_SCHEMA_VERSION = "ontokin.agent/0.3"
MAX_REQUEST_BYTES = MAX_JSON_BYTES
MAX_BUDGETS = {**core.MAX_BUDGETS, "max_value_entries": MAX_JSON_ENTRIES}
COMMON = core.COMMON
KINDS = core.KINDS | {"source", "import", "collection"}
OPERATIONS = {
    "discover": ({"profile", "limit"}, {"filter", "cursor", "bundle", "program_revision", "budgets"}),
    "create": ({"bundle", "expected_program_revision", "requested_level"}, {"budgets", "destination", "options"}),
    "edit": ({"expected_program_revision", "patches", "requested_level"}, {"module_changes", "budgets", "destination", "options"}),
    "validate": ({"program_revision", "requested_level"}, {"budgets", "destination", "options"}),
    "inspect": ({"program_revision", "selector", "fields", "limit"}, {"run_id", "time", "frame", "cursor", "budgets"}),
    "evaluate": ({"program_revision", "run_id", "until_seconds"}, {"budgets"}),
    "reset": ({"program_revision"}, {"budgets"}),
    "status": ({"target_request_id"}, set()),
    "cancel": ({"target_request_id"}, set()),
    "export": ({"program_revision", "destination"}, {"options", "budgets"}),
    "artifact": ({"artifact_id"}, {"offset", "max_bytes"}),
}
SURFACE_OPERATIONS = {**OPERATIONS, "surface.mesh_page": (
    {"program_revision", "element_id", "count"}, {"region", "cursor", "budgets"})}


class ProgramProtocol:
    def __init__(self, schema_version=SCHEMA_VERSION):
        if schema_version not in (SCHEMA_VERSION, SURFACE_SCHEMA_VERSION):
            raise ProtocolError("OKA-E-REQUEST", "Unknown program service binding.",
                                available_protocols=[SCHEMA_VERSION, SURFACE_SCHEMA_VERSION])
        self.SCHEMA_VERSION = schema_version
        self.MAX_BUDGETS = dict(MAX_BUDGETS)
        self.OPERATIONS = {name: (set(required), set(optional)) for name, (required, optional) in
                           (SURFACE_OPERATIONS if schema_version == SURFACE_SCHEMA_VERSION else OPERATIONS).items()}
        self.profile = "surface-0.1" if schema_version == SURFACE_SCHEMA_VERSION else "construction-0.1"
        self.destination = "ontokin.glb/0.3" if schema_version == SURFACE_SCHEMA_VERSION else "ontokin.glb/0.2"

    def canonical_request(self, value):
        return canonical_request(value)

    def validate_request(self, request):
        return validate_request(request, schema_version=self.SCHEMA_VERSION)

    def envelope(self, request, status, accepted=None):
        return envelope(request, status, accepted, schema_version=self.SCHEMA_VERSION)


def bind(schema_version=SCHEMA_VERSION):
    return ProgramProtocol(schema_version)


def _revision(value, name):
    _text(value, name, limit=71)
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        _bad(f"{name} must be an exact lowercase SHA-256 identity.")


def _ids(value, name):
    if not isinstance(value, list) or not 1 <= len(value) <= 256:
        _bad(f"{name} requires 1 through 256 identity segments.")
    for part in value:
        _text(part, name, limit=200)


def canonical_request(value):
    try:
        payload = bounded_dumps(value)
        clean = json.loads(payload)
    except JSONLimitError as exc:
        raise ProtocolError("OKA-E-RESOURCE", "The request exceeds the bounded JSON transport.", **exc.details) from exc
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("OKA-E-REQUEST", "The request must contain finite JSON with valid UTF-8 scalar strings.") from exc
    if not isinstance(clean, dict):
        _bad("A request must be a JSON object.")
    return clean, payload


def _module(value):
    from .bundle import load_bundle, BundleError
    try:
        load_bundle({"schema_version": "ontokin.bundle/0.1", "entry": {"filename": "<shape>", "source": ""}, "modules": [value]})
    except BundleError as exc:
        raise ProtocolError(exc.code, str(exc), **exc.details) from exc


def validate_request(request, *, schema_version=SCHEMA_VERSION):
    binding = bind(schema_version)
    operations = binding.OPERATIONS
    op = request.get("operation")
    if request.get("schema_version") != schema_version or not isinstance(op, str) or op not in operations:
        _bad("Unknown program protocol schema or operation.", schema_version=schema_version, operations=sorted(operations))
    required, optional = operations[op]
    _object(request, "request", COMMON | required | optional, COMMON | required)
    for name in ("project_id", "request_id", "target_request_id", "artifact_id"):
        if name in request:
            _text(request[name], name, limit=200)
    for name in ("program_revision", "expected_program_revision"):
        if name in request:
            if op == "create" and name == "expected_program_revision":
                if request[name] is not None:
                    _bad("Create requires expected_program_revision:null.")
            else:
                _revision(request[name], name)
    for name in ("run_id", "cursor"):
        if name in request and request[name] is not None:
            _text(request[name], name, limit=65536 if name == "cursor" else 200)
    for name in ("profile", "frame"):
        if name in request:
            _text(request[name], name, limit=32768)
    if "requested_level" in request and request["requested_level"] not in LEVELS:
        _bad("Unknown requested output level.", levels=list(LEVELS))
    if "bundle" in request:
        from .bundle import load_bundle, BundleError
        try:
            load_bundle(request["bundle"])
        except BundleError as exc:
            raise ProtocolError(exc.code, str(exc), **exc.details) from exc
    if op == "discover" and "bundle" in request and "program_revision" in request:
        _bad("Discovery context is a bundle or a retained program revision, not both.")
    if "limit" in request:
        _integer(request["limit"], "limit", 1, 1000)
    if op == "surface.mesh_page":
        _ids(request["element_id"], "element_id")
        _integer(request["count"], "count", 1, 256)
        if "region" in request:
            _text(request["region"], "region", limit=64)
    if "budgets" in request:
        _object(request["budgets"], "budgets", set(MAX_BUDGETS))
        for key, value in request["budgets"].items():
            _integer(value, "budgets." + key, 1, MAX_BUDGETS[key])
    if "until_seconds" in request:
        _seconds(request["until_seconds"], "until_seconds")
    if request.get("time") is not None:
        _object(request["time"], "time", {"seconds", "side"}, {"seconds", "side"})
        _seconds(request["time"]["seconds"], "time.seconds")
        if request["time"]["side"] not in ("before", "after"):
            _bad("time.side must be before or after.")
    if "selector" in request:
        _object(request["selector"], "selector", {"element_id", "kind", "path", "class_name", "role", "relation", "source_id"})
        for key, value in request["selector"].items():
            if key == "element_id" or key == "relation" and isinstance(value, list):
                _ids(value, "selector." + key)
            else:
                _text(value, "selector." + key, empty=key == "role", limit=32768)
                if key == "kind" and value not in KINDS:
                    _bad("Unknown selector.kind.")
    if "fields" in request:
        value = request["fields"]
        if not isinstance(value, list) or not value or any(not isinstance(x, str) or x not in FIELDS for x in value) or len(set(value)) != len(value):
            _bad("fields requires distinct supported field groups.", fields=sorted(FIELDS))
    if "patches" in request:
        patches = request["patches"]
        if not isinstance(patches, list) or len(patches) > 1000:
            _bad("patches must be an array of at most 1,000 records.")
        names = {"source_id", "source_revision", "element_id", "start_byte", "end_byte", "expected_text", "replacement"}
        for patch in patches:
            _object(patch, "patch", names, names)
            _text(patch["source_id"], "patch.source_id", limit=200)
            _revision(patch["source_revision"], "patch.source_revision")
            _ids(patch["element_id"], "patch.element_id")
            for key in ("start_byte", "end_byte"):
                _integer(patch[key], "patch." + key, 0, 2000000)
            for key in ("expected_text", "replacement"):
                _text(patch[key], "patch." + key, empty=True, limit=2000000)
    if "module_changes" in request:
        changes = request["module_changes"]
        if not isinstance(changes, list) or len(changes) > 32:
            _bad("module_changes must be an array of at most 32 records.")
        for change in changes:
            if not isinstance(change, dict) or change.get("operation") not in ("add", "remove", "replace"):
                _bad("A module change must explicitly add, remove, or replace.")
            mode = change["operation"]
            names = {"operation"} | ({"module"} if mode == "add" else {"source_id", "source_revision"}) | ({"module"} if mode == "replace" else set())
            _object(change, "module_change", names, names)
            if mode != "add":
                _text(change["source_id"], "module_change.source_id", limit=200)
                _revision(change["source_revision"], "module_change.source_revision")
            if mode != "remove":
                _module(change["module"])
    if op == "edit" and not request["patches"] and not request.get("module_changes"):
        _bad("An edit needs a source patch or an explicit module change.")
    if "filter" in request:
        if isinstance(request["filter"], str):
            _text(request["filter"], "filter", limit=1024)
        else:
            _object(request["filter"], "filter", {"kind", "name", "capability"})
            for key, value in request["filter"].items():
                _text(value, "filter." + key, limit=1024)
    if "destination" in request and request["destination"] != binding.destination:
        _bad("The program destination contract is " + binding.destination + ".")
    if "options" in request:
        _options(request["options"])
        if "destination" not in request:
            _bad("Export options require an explicit destination contract.")
    if op in {"create", "edit", "validate"} and ("destination" in request or "options" in request) and request["requested_level"] != "delivered":
        _bad("Destination settings require requested_level:delivered.")
    if "offset" in request:
        _integer(request["offset"], "offset", 0)
    if "max_bytes" in request:
        _integer(request["max_bytes"], "max_bytes", 1, 65536)


def envelope(request, status, accepted=None, *, schema_version=SCHEMA_VERSION):
    result = core.envelope(request, status, accepted)
    result["schema_version"] = schema_version
    result["program_revision"] = None
    if isinstance(request, dict):
        operation = request.get("operation")
        operations = SURFACE_OPERATIONS if schema_version == SURFACE_SCHEMA_VERSION else OPERATIONS
        result["operation"] = operation if isinstance(operation, str) and operation in operations else None
        revision = request.get("program_revision")
        if isinstance(revision, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", revision):
            result["program_revision"] = revision
    result["accepted_program_revision"] = result.pop("accepted_revision")
    result.pop("source_revision")
    return result
