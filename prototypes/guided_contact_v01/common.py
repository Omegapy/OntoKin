"""Small standard-library support for the adopted C191 boundary."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import time


CONTRACT = Path(__file__).resolve().parents[2] / "docs/language-design/guided-contact-v0.1"
CONTRACT_MANIFEST_SHA256 = "bc85696002d641122322313cf5167f84eb1ae377599930112e3afd0f054b0137"
AMENDMENTS = {"amendments/C191-A1.md": "c05699cdeec319b8f594c771cba7ef1ec8e7d7a4eb267569873171b8839d791e"}
LEVELS = ("represented", "constructed", "evaluated", "exported", "destination_validated")
PARTS = ("base", "left_carriage", "left_shoe", "left_stop",
         "right_carriage", "right_shoe", "right_stop")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf8")


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result

    def constant(value):
        raise ValueError("Nonfinite JSON value: " + value)
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def load_contract():
    raw = (CONTRACT / "CONTRACT-FILES.json").read_bytes()
    if sha256(raw) != CONTRACT_MANIFEST_SHA256:
        raise RuntimeError("C191 contract manifest differs from adopted bytes")
    manifest = strict_json(raw)
    content = {}
    for item in manifest["files"]:
        data = (CONTRACT / item["path"]).read_bytes()
        if len(data) != item["bytes"] or sha256(data) != item["sha256"]:
            raise RuntimeError("C191 adopted contract file changed: " + item["path"])
        content[item["path"]] = data
    closure = list(manifest["files"])
    for path, expected_hash in AMENDMENTS.items():
        data = (CONTRACT / path).read_bytes()
        if sha256(data) != expected_hash:
            raise RuntimeError("C191 adopted amendment changed: " + path)
        closure.append({"path": path, "bytes": len(data), "sha256": expected_hash})
    return {
        "manifest": manifest,
        "dependency_closure": closure,
        "backend": strict_json(content["backend.json"]),
        "backend_sha256": sha256(content["backend.json"]),
        "source_schema": strict_json(content["source.schema.json"]),
        "native_schema": strict_json(content["native-result.schema.json"]),
        "output_schema": strict_json(content["output.schema.json"]),
        "diagnostics": {r["code"]: r for r in strict_json(content["diagnostics.json"])["codes"]},
    }


class Failure(Exception):
    def __init__(self, code, message, span=None):
        super().__init__(message)
        self.code = code if code.startswith("C191_") else "C191_" + code
        self.message = message
        self.span = span


class Budget:
    def __init__(self, host_operations=100000, host_elapsed_ms=30000, cancel_file=None):
        self.started = time.monotonic()
        self.host_operations = host_operations
        self.host_elapsed_ms = host_elapsed_ms
        self.max_operations = host_operations
        self.max_elapsed_ms = host_elapsed_ms
        self.requested_operations = None
        self.requested_elapsed_ms = None
        self.components = Counter()
        self.cancel_file = Path(cancel_file) if cancel_file else None
        self.anchor = None
        self.cancellation_requested_ns = None
        self.cancellation_completion_ms = None
        self.native_elapsed_ms = 0.0
        self.native_result_bytes = 0
        self.native_log_bytes = 0
        self.staged_output_bytes = 0

    @property
    def operations(self):
        return sum(self.components.values())

    @property
    def elapsed_ms(self):
        return (time.monotonic() - self.started) * 1000

    def charge(self, component, amount=1):
        self.components[component] += amount
        self.check()

    def check(self):
        if self.cancel_file and self.cancel_file.exists():
            self.cancellation_requested_ns = self.cancel_file.stat().st_mtime_ns
            raise Failure("E_CANCELLED", "Cancellation requested", self.anchor)
        if self.operations > self.max_operations:
            raise Failure("E_RESOURCE_LIMIT", "Operation ceiling exhausted", self.anchor)
        if self.elapsed_ms >= self.max_elapsed_ms:
            raise Failure("E_TIMEOUT", "Attempt elapsed deadline exhausted", self.anchor)

    def authorize(self, operations, elapsed_ms, operation_span, elapsed_span):
        # Invalid fractional requests are located in source diagnostics. They
        # are not represented as an admitted integer budget in the envelope.
        self.requested_operations = operations if type(operations) is int else None
        self.requested_elapsed_ms = elapsed_ms if type(elapsed_ms) is int else None
        if (type(operations) is not int or operations < 1 or operations > 1000000
                or operations > self.host_operations):
            raise Failure("E_BUDGET", "Source operation request exceeds the authorized ceiling", operation_span)
        if (type(elapsed_ms) is not int or elapsed_ms < 1 or elapsed_ms > 80000
                or elapsed_ms > self.host_elapsed_ms):
            raise Failure("E_BUDGET", "Source elapsed request exceeds the authorized ceiling", elapsed_span)
        self.max_operations = operations
        self.max_elapsed_ms = elapsed_ms
        self.check()

    def cost(self):
        return {
            "requested_operations": self.requested_operations,
            "requested_elapsed_ms": self.requested_elapsed_ms,
            "host_operations_ceiling": self.host_operations,
            "host_elapsed_ms_ceiling": self.host_elapsed_ms,
            "operations_consumed": self.operations,
            "operation_components": dict(sorted(self.components.items())),
            "elapsed_ms": self.elapsed_ms,
            "native_elapsed_ms": self.native_elapsed_ms,
            "cancellation_completion_ms": self.cancellation_completion_ms,
            "native_result_bytes": self.native_result_bytes,
            "native_log_bytes": self.native_log_bytes,
            "staged_output_bytes": self.staged_output_bytes,
        }


def schema_check(value, schema, *, root=None, budget=None, path="$"):
    """Validate only the exact JSON-Schema vocabulary used by the frozen files.

    This deliberately has no external-reference loader or dependency on a schema
    package. Unknown schema keywords are not encountered in the sealed inputs.
    """
    root = schema if root is None else root
    if budget:
        budget.charge("schema_values")
    if "$ref" in schema:
        target = root
        for key in schema["$ref"].removeprefix("#/").split("/"):
            target = target[key]
        return schema_check(value, target, root=root, budget=budget, path=path)
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                schema_check(value, branch, root=root, budget=budget, path=path)
                return
            except ValueError:
                pass
        raise ValueError(path + ": no allowed type")
    kind = ("null" if value is None else "boolean" if type(value) is bool else
            "integer" if type(value) is int else "number" if type(value) is float else
            "string" if isinstance(value, str) else "array" if isinstance(value, list) else
            "object" if isinstance(value, dict) else "invalid")
    allowed = schema.get("type")
    if allowed:
        allowed = [allowed] if isinstance(allowed, str) else allowed
        if kind not in allowed and not (kind == "integer" and "number" in allowed):
            raise ValueError(path + ": unexpected type " + kind)
    if kind in ("integer", "number") and not math.isfinite(value):
        raise ValueError(path + ": nonfinite number")
    if "const" in schema and (value != schema["const"] or
            (type(value) is bool) != (type(schema["const"]) is bool)):
        raise ValueError(path + ": differs from frozen constant")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(path + ": unexpected enum")
    if kind in ("integer", "number"):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(path + ": below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(path + ": above maximum")
    if kind == "string" and "pattern" in schema:
        import re
        if not re.search(schema["pattern"], value):
            raise ValueError(path + ": pattern mismatch")
    if kind == "object":
        props = schema.get("properties", {})
        if set(schema.get("required", ())) - set(value):
            raise ValueError(path + ": missing required field")
        for key, item in value.items():
            rule = props.get(key, schema.get("additionalProperties", True))
            if rule is False:
                raise ValueError(path + ": unknown field " + key)
            if isinstance(rule, dict):
                schema_check(item, rule, root=root, budget=budget, path=path + "." + key)
    if kind == "array":
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", math.inf):
            raise ValueError(path + ": wrong array length")
        prefix = schema.get("prefixItems", [])
        for index, item in enumerate(value):
            rule = prefix[index] if index < len(prefix) else schema.get("items", True)
            if rule is False:
                raise ValueError(path + ": unexpected array item")
            if isinstance(rule, dict):
                schema_check(item, rule, root=root, budget=budget, path=f"{path}[{index}]")
