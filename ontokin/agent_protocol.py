"""Strict, bounded JSON envelopes for the local ontokin.agent/0.1 service.

This is the concrete protocol validator, not a general JSON Schema engine.
The independently checked public schemas live beside the language contracts.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

SCHEMA_VERSION = "ontokin.agent/0.1"
MAX_REQUEST_BYTES = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_BUDGETS = {"max_objects": 1000, "max_operations": 100000,
               "max_result_items": 1000, "max_elapsed_ms": 30000}
LEVELS = ("represented", "constructed", "evaluated", "delivered")
TERMINAL = {"succeeded", "rejected", "failed", "cancelled", "unknown_outcome"}
FIELDS = {"identity", "source", "values", "geometry", "matter", "relations", "actions", "state", "support"}
KINDS = {"object", "property", "site", "joint", "follow", "action", "class", "function", "scene", "module"}
COMMON = {"schema_version", "project_id", "request_id", "operation"}
OPERATIONS = {
    "discover": ({"profile", "limit"}, {"filter", "cursor"}),
    "create": ({"filename", "source", "expected_revision", "requested_level"}, {"budgets", "destination", "options"}),
    "edit": ({"expected_revision", "patches", "requested_level"}, {"budgets", "destination", "options"}),
    "validate": ({"source_revision", "requested_level"}, {"budgets", "destination", "options"}),
    "inspect": ({"source_revision", "selector", "fields", "limit"}, {"run_id", "time", "frame", "cursor", "budgets"}),
    "evaluate": ({"source_revision", "run_id", "until_seconds"}, {"budgets"}),
    "reset": ({"source_revision"}, {"budgets"}),
    "status": ({"target_request_id"}, set()),
    "cancel": ({"target_request_id"}, set()),
    "export": ({"source_revision", "destination"}, {"options", "budgets"}),
    "artifact": ({"artifact_id"}, {"offset", "max_bytes"}),
}


class ProtocolError(Exception):
    def __init__(self, code: str, message: str, **details: Any):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


def _bad(message: str, **details: Any) -> None:
    raise ProtocolError("OKA-E-REQUEST", message, **details)


def _text(value: Any, name: str, *, empty: bool = False, limit: int | None = None) -> None:
    if not isinstance(value, str) or (not empty and not value):
        _bad(f"{name} must be a {'possibly empty' if empty else 'nonempty'} UTF-8 string.")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        _bad(f"{name} must encode as valid UTF-8.")
    if limit is not None and size > limit:
        _bad(f"{name} exceeds its byte limit.", limit=limit)


def _integer(value: Any, name: str, minimum: int, maximum: int | None = None) -> None:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        _bad(f"{name} must be an integer in the permitted range.", minimum=minimum, maximum=maximum)


def _object(value: Any, name: str, allowed: set[str], required: set[str] | None = None) -> None:
    if not isinstance(value, dict) or set(value) - allowed or (required or set()) - set(value):
        _bad(f"{name} has missing or unknown fields.", allowed=sorted(allowed), required=sorted(required or ()))


def _ids(value: Any, name: str) -> None:
    if not isinstance(value, list) or not value or len(value) > 128:
        _bad(f"{name} must be a nonempty bounded key path.")
    for item in value:
        _text(item, name, limit=200)


def _seconds(value: Any, name: str) -> None:
    _text(value, name, limit=1024)
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is None:
        _bad(f"{name} must be a nonnegative exact decimal seconds string.")


def _options(value: Any) -> None:
    names = {"fps", "end", "position_tolerance_m", "rotation_tolerance_rad", "time_tolerance_s", "helpers"}
    _object(value, "options", names)
    for name, item in value.items():
        if name == "end":
            _seconds(item, "options.end")
        elif name == "helpers":
            if type(item) is not bool:
                _bad("options.helpers must be Boolean.")
        else:
            try:
                valid = type(item) in (int, float) and math.isfinite(item) and item > 0 and (name != "fps" or item <= 10000)
            except OverflowError:
                valid = False
            if not valid:
                _bad(f"options.{name} must be finite and positive within the destination limits.")


def canonical_request(value: Any) -> tuple[dict, str]:
    """Ignore object-member order, preserving every value and array order."""
    try:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        if len(payload.encode("utf-8")) > MAX_REQUEST_BYTES:
            raise ProtocolError("OKA-E-RESOURCE", "The request exceeds the 4 MiB protocol limit.")
        clean = json.loads(payload)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("OKA-E-REQUEST", "The request must contain finite JSON values and valid UTF-8 strings.") from exc
    if not isinstance(clean, dict):
        _bad("A request must be a JSON object.")
    return clean, payload


def validate_request(request: dict) -> None:
    operation = request.get("operation")
    if request.get("schema_version") != SCHEMA_VERSION or not isinstance(operation, str) or operation not in OPERATIONS:
        _bad("Unknown protocol schema or operation.", schema_version=SCHEMA_VERSION, operations=sorted(OPERATIONS))
    required, optional = OPERATIONS[operation]
    _object(request, "request", COMMON | required | optional, COMMON | required)
    for name in ("project_id", "request_id"):
        _text(request[name], name, limit=200)
    for name in ("filename", "source_revision", "target_request_id", "artifact_id", "profile", "frame"):
        if name in request:
            _text(request[name], name, limit=1024)
    for name in ("run_id", "cursor"):
        if request.get(name) is not None:
            _text(request[name], name, limit=32768 if name == "cursor" else 200)
    if "requested_level" in request and request["requested_level"] not in LEVELS:
        _bad("Unknown requested output level.", levels=list(LEVELS))
    if "expected_revision" in request:
        if operation == "create" and request["expected_revision"] is not None:
            _bad("Create requires expected_revision:null.")
        if operation == "edit":
            _text(request["expected_revision"], "expected_revision", limit=1024)
    if "source" in request:
        _text(request["source"], "source", empty=True, limit=MAX_SOURCE_BYTES)
    if "limit" in request:
        _integer(request["limit"], "limit", 1, 1000)
    if "budgets" in request:
        _object(request["budgets"], "budgets", set(MAX_BUDGETS))
        for name, value in request["budgets"].items():
            _integer(value, name, 1, MAX_BUDGETS[name])
    if "until_seconds" in request:
        _seconds(request["until_seconds"], "until_seconds")
    if request.get("time") is not None:
        _object(request["time"], "time", {"seconds", "side"}, {"seconds", "side"})
        _seconds(request["time"]["seconds"], "time.seconds")
        if request["time"]["side"] not in ("before", "after"):
            _bad("time.side must be before or after.")
    if "selector" in request:
        selector = request["selector"]
        _object(selector, "selector", {"element_id", "kind", "path", "class_name", "role", "relation"})
        for name, value in selector.items():
            if name == "element_id" or (name == "relation" and isinstance(value, list)):
                _ids(value, "selector." + name)
            else:
                _text(value, "selector." + name, empty=name == "role", limit=1024)
                if name == "kind" and value not in KINDS:
                    _bad("Unknown selector.kind.")
    if "fields" in request:
        value = request["fields"]
        if not isinstance(value, list) or not value or not all(isinstance(x, str) and x in FIELDS for x in value) or len(set(value)) != len(value):
            _bad("fields must be a nonempty array of distinct supported field groups.", fields=sorted(FIELDS))
    if "patches" in request:
        patches = request["patches"]
        if not isinstance(patches, list) or not 1 <= len(patches) <= 1000:
            _bad("patches must contain 1 through 1,000 patches.")
        names = {"element_id", "start_byte", "end_byte", "expected_text", "replacement"}
        for patch in patches:
            _object(patch, "patch", names, names)
            _ids(patch["element_id"], "patch.element_id")
            for name in ("start_byte", "end_byte"):
                _integer(patch[name], "patch." + name, 0)
            for name in ("expected_text", "replacement"):
                _text(patch[name], "patch." + name, empty=True, limit=MAX_SOURCE_BYTES)
    if "filter" in request:
        filter_ = request["filter"]
        if isinstance(filter_, str):
            _text(filter_, "filter", limit=1024)
        else:
            _object(filter_, "filter", {"kind", "name", "capability"})
            for name, value in filter_.items():
                _text(value, "filter." + name, limit=1024)
    if "destination" in request and request["destination"] != "ontokin.glb/0.1":
        _bad("The available explicit destination is ontokin.glb/0.1.")
    if "options" in request:
        _options(request["options"])
    if operation in {"create", "edit", "validate"} and ("destination" in request or "options" in request) and request["requested_level"] != "delivered":
        _bad("Destination settings require requested_level:delivered.")
    if "options" in request and "destination" not in request:
        _bad("Export options require an explicit destination contract.")
    if "offset" in request:
        _integer(request["offset"], "offset", 0)
    if "max_bytes" in request:
        _integer(request["max_bytes"], "max_bytes", 1, 65536)


def envelope(request: Any, status: str, accepted: str | None = None) -> dict:
    request = request if isinstance(request, dict) else {}
    operation = request.get("operation")
    operation = operation if isinstance(operation, str) and operation in OPERATIONS else None
    requested = request.get("requested_level")
    if requested not in LEVELS:
        requested = "evaluated" if operation == "evaluate" else "delivered" if operation == "export" else None
    def usable(value, limit):
        try:
            return value if isinstance(value, str) and value and len(value.encode("utf-8")) <= limit else None
        except UnicodeError:
            return None
    return {"schema_version": SCHEMA_VERSION,
            "project_id": usable(request.get("project_id"), 200),
            "request_id": usable(request.get("request_id"), 200),
            "operation": operation, "status": status,
            "source_revision": usable(request.get("source_revision"), 1024), "accepted_revision": accepted,
            "requested_level": requested, "achieved_level": None, "run_id": None,
            "diagnostics": [], "result": None, "progress": None,
            "next_cursor": None, "truncated": False, "protocol_error": None}
