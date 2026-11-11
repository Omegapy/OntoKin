"""Strict route-neutral boundary for OK-MAP-STATIC-TRAY-001/0.1.0.

This producer-side validator is not the independent delivered-geometry reader.
Each arithmetic operation rounds separately through an exact Fraction result.
"""

from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from .errors import CONTRACT, PROFILE, TrayError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs/engineering/static-tray-mapping-c198/canonical-record.schema.json"
SCHEMA_SHA256 = "1d06f6be7841719f624a0137bf584704abbf156e6abf99870a21b3abe5e2b08c"
PARTS = ("back", "base", "front", "left-wall", "payload", "right-wall")
IDENTITY = (1.0, 0.0, 0.0, 0.0)
ROTATIONS = (IDENTITY, (0., 1., 0., 0.), (0., 0., 1., 0.), (0., 0., 0., 1.)) + tuple(
    (.5, x, y, z) for x in (.5, -.5) for y in (.5, -.5) for z in (.5, -.5))
CONSTANTS = {
    "schema_version": "ontokin.static-tray.record/0.1.0", "profile": PROFILE,
    "contract": CONTRACT, "template_id": "static-tray-six-box/0.1.0",
    "length_unit": "m", "frame": "ontokin-world-rh-y-up",
    "numeric_encoding": "binary64-be-hex/1", "material_set": "static-tray-materials/0.1.0"}
PARAMETER_KEYS = ("payload-width", "payload-height", "payload-depth", "clearance",
                  "wall-thickness", "base-thickness", "headroom")
BOUNDS = ((.01, 1.), (.01, .5), (.01, 1.), (.001, .05), (.001, .025), (.001, .025), (.001, .1))


def f64(value):
    value = float(value)
    if not math.isfinite(value):
        raise TrayError("NUMERIC", "A finite binary64 value is required.")
    return 0.0 if value == 0 else value


def bits(value):
    return struct.pack(">d", f64(value)).hex()


def number(value):
    if not isinstance(value, str) or re.fullmatch("[0-9a-f]{16}", value) is None:
        raise TrayError("RECORD", "Expected sixteen lowercase binary64 hex digits.", stage="record")
    result = struct.unpack(">d", bytes.fromhex(value))[0]
    if not math.isfinite(result) or value == "8000000000000000":
        raise TrayError("RECORD", "Nonfinite or negative-zero bits are not canonical.", stage="record")
    return result


def op(a, operator, b):
    a, b = Fraction(f64(a)), Fraction(f64(b))
    return f64({"+": lambda: a + b, "*": lambda: a * b, "/": lambda: a / b}[operator]())


def geometry_values(parameters):
    px, py, pz, c, t, b, h = parameters
    width, depth = op(px, "+", op(2, "*", c)), op(pz, "+", op(2, "*", c))
    height = op(py, "+", h)
    outer_x, outer_z = op(width, "+", op(2, "*", t)), op(depth, "+", op(2, "*", t))
    half_y, wall_x, wall_z = op(height, "/", 2), op(op(width, "+", t), "/", 2), op(op(depth, "+", t), "/", 2)
    return {
        "base": ((outer_x, b, outer_z), (0., f64(-op(b, "/", 2)), 0.)),
        "front": ((outer_x, height, t), (0., half_y, wall_z)),
        "back": ((outer_x, height, t), (0., half_y, f64(-wall_z))),
        "left-wall": ((t, height, depth), (f64(-wall_x), half_y, 0.)),
        "right-wall": ((t, height, depth), (wall_x, half_y, 0.)),
        "payload": ((px, py, pz), (0., op(py, "/", 2), 0.))}


def json_bytes(value):
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                          allow_nan=False).encode("ascii")
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise TrayError("RECORD", "Canonical JSON must contain finite ASCII data.", stage="record") from exc
    return data


def strict_json(data, *, limit=32768):
    if not isinstance(data, bytes) or len(data) > limit:
        raise TrayError("RESOURCE", "JSON byte allowance exceeded.", stage="record")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise TrayError("RECORD", "Duplicate JSON object member.", stage="record", pointer=key)
            result[key] = value
        return result
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, TrayError):
            raise
        raise TrayError("RECORD", "Invalid bounded UTF-8 JSON.", stage="record") from exc


def _schema_findings(value, schema, whole, pointer=""):
    """Apply every keyword present in the frozen finite schema, failing closed."""
    if schema is False:
        return [{"pointer": pointer, "code": "OTRAY-E-RECORD", "reason": "Additional item forbidden"}]
    if schema is True:
        return []
    allowed = {"$schema", "$id", "$comment", "$defs", "title", "description", "$ref", "type", "const", "enum", "allOf", "not", "pattern", "properties", "required", "additionalProperties", "items", "prefixItems", "minItems", "maxItems"}
    if set(schema) - allowed:
        raise TrayError("BINDING", "Unsupported schema keyword in locked boundary.", stage="record")
    result = []
    def fail(reason):
        result.append({"pointer": pointer, "code": "OTRAY-E-RECORD", "reason": reason})
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise TrayError("BINDING", "Only internal schema references are admitted.")
        target = whole
        for key in ref[2:].split("/"):
            target = target[key]
        result.extend(_schema_findings(value, target, whole, pointer))
    for child in schema.get("allOf", []):
        result.extend(_schema_findings(value, child, whole, pointer))
    if "not" in schema and not _schema_findings(value, schema["not"], whole, pointer):
        fail("Forbidden value or encoding")
    typ = schema.get("type")
    valid_type = {"object": type(value) is dict, "array": type(value) is list,
                  "string": type(value) is str, "integer": type(value) is int}.get(typ, True)
    if not valid_type:
        fail("Wrong JSON type")
        return result
    if "const" in schema and (value != schema["const"] or isinstance(value, bool) != isinstance(schema["const"], bool)):
        fail("Constant differs")
    if "enum" in schema and value not in schema["enum"]:
        fail("Value outside fixed enumeration")
    if isinstance(value, str) and "pattern" in schema and re.search(schema["pattern"], value) is None:
        fail("Encoding pattern differs")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                fail("Missing member " + key)
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False and set(value) - set(props):
            fail("Unknown members " + repr(sorted(set(value) - set(props))))
        for key, child in props.items():
            if key in value:
                result.extend(_schema_findings(value[key], child, whole, pointer + "/" + key))
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", 32768):
            fail("Wrong array length")
        prefix = schema.get("prefixItems", [])
        for i, item in enumerate(value):
            child = prefix[i] if i < len(prefix) else schema.get("items", True)
            result.extend(_schema_findings(item, child, whole, pointer + "/" + str(i)))
    return result


def validate_record(record):
    raw = json_bytes(record)
    if len(raw) > 32768:
        raise TrayError("RESOURCE", "Canonical record exceeds 32768 bytes.", stage="record")
    schema_raw = SCHEMA_PATH.read_bytes()
    if hashlib.sha256(schema_raw).hexdigest() != SCHEMA_SHA256:
        raise TrayError("BINDING", "Frozen C198 schema bytes changed.", stage="record")
    schema = json.loads(schema_raw)
    errors = _schema_findings(record, schema, schema)
    if errors:
        errors.sort(key=lambda x: (x["pointer"], x["code"], x["reason"]))
        raise TrayError("RECORD", "Record does not satisfy the frozen structural boundary.", stage="record", findings=errors)
    errors = []
    for tray in record["trays"]:
        sid = "/".join(tray["id"])
        p = tray["parameters"]
        values = [*(number(v) for v in p["payload_size_m"]), *(number(p[k]) for k in (
            "horizontal_clearance_m", "wall_thickness_m", "base_thickness_m", "headroom_m"))]
        for key, value, (low, high) in zip(PARAMETER_KEYS, values, BOUNDS):
            if not low <= value <= high:
                errors.append({"semantic_id": sid, "code": "OTRAY-E-RANGE", "field": key,
                               "actual": bits(value), "minimum": bits(low), "maximum": bits(high)})
        for i, v in enumerate(tray["root_pose"]["translation_m"]):
            if not -10 <= number(v) <= 10:
                errors.append({"semantic_id": sid, "code": "OTRAY-E-RANGE", "field": "root_translation/" + str(i)})
        if any(not low <= value <= high for value, (low, high) in zip(values, BOUNDS)):
            continue
        expected = geometry_values(values)
        for part in tray["parts"]:
            sizes, offset = expected[part["key"]]
            for field, actual, wanted in [("geometry/size_m", part["geometry"]["size_m"], sizes),
                                           ("following/offset/translation_m", part["following"]["offset"]["translation_m"], offset)]:
                if actual != [bits(v) for v in wanted]:
                    errors.append({"semantic_id": "/".join(part["id"]), "code": "OTRAY-E-SHAPE",
                                   "field": field, "actual": actual, "expected": [bits(v) for v in wanted]})
    if errors:
        errors.sort(key=lambda x: (x["semantic_id"], x["code"], x["field"]))
        raise TrayError(errors[0]["code"], "Finite record semantics failed.", findings=errors)
    return record


def canonical_bytes(record):
    validate_record(record)
    return json_bytes(record)


def decode_record(data):
    record = strict_json(data)
    validate_record(record)
    if json_bytes(record) != data:
        raise TrayError("RECORD", "Record file is not exact canonical JSON.", stage="record")
    return record


def record_identity(data):
    return "sha256:" + hashlib.sha256(b"ontokin.static-tray.record/0.1.0\0" + data).hexdigest()


def record_from_values(sets):
    """Producer convenience; OntoKin lowering instead reads actual compiled boxes."""
    trays = []
    for side in ("left", "right"):
        item = sets[side]
        values = [*item["payload_m"], item["clearance_m"], item["wall_m"], item["base_m"], item["headroom_m"]]
        sid = ["equipment-tray", "pair", side]
        geometry = geometry_values(values)
        tray = {"id": sid, "owner_id": sid[:2], "role": "tray-root", "geometry": "empty",
                "physical": "no_body", "motion": "prescribed", "collision": "disabled",
                "root_pose": {"reference": "world", "translation_m": [bits(v) for v in item["translation_m"]],
                              "rotation_wxyz": [bits(v) for v in item["rotation_wxyz"]]},
                "parameters": {"payload_size_m": [bits(v) for v in values[:3]],
                               **dict(zip(("horizontal_clearance_m", "wall_thickness_m", "base_thickness_m", "headroom_m"), [bits(v) for v in values[3:]]))}, "parts": []}
        for key in PARTS:
            size, offset = geometry[key]
            tray["parts"].append({"id": sid + [key], "owner_id": sid, "key": key,
                "role": "payload-proxy" if key == "payload" else key,
                "geometry": {"type": "box", "size_m": [bits(v) for v in size]},
                "physical": "no_body", "motion": "prescribed", "collision": "disabled",
                "material": "payload" if key == "payload" else "tray",
                "following": {"id": sid + ["follow-" + key], "parent_id": sid,
                              "offset": {"reference": "parent-frame", "translation_m": [bits(v) for v in offset],
                                         "rotation_wxyz": [bits(v) for v in IDENTITY]}}})
        trays.append(tray)
    return {**CONSTANTS, "trays": trays}
