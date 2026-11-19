#!/usr/bin/env python3
"""Bounded raw GLB hinge claims; no source truth, comparison or file admission."""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import unicodedata

SCHEMA = "ontokin.c261.glb-hinge-observation/0.1"
MAX_GLB_BYTES = 4 * 1024 * 1024
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 32
MAX_OBJECTS = 128
MAX_HINGES = 128
MAX_SITES = 256
FIELDS = ("path", "element_id", "kind", "parent_site", "child_site",
          "axis", "limits", "initial")
IDENTITY_FIELDS = {"element_id", "definition_id", "declaration_definition_id",
                   "collection_id", "collection_definition_id"}
LIMITS = [
    "Untrusted artifact claims only; no source observation or field agreement",
    "No historical byte admission or accepted revision",
    "No site association, site poses, world alignment or motion qualification",
    "No complete source/glTF/C255 validity, native execution or model trial",
]


class Fault(ValueError):
    """Typed raw-observation refusal, with bounded input identity when available."""

    def __init__(self, code, detail, pointer=""):
        self.code, self.detail, self.pointer = code, detail, pointer
        self.artifactSha256, self.artifactBytes = None, None
        super().__init__(f"{code}: {pointer}: {detail}")


def _require(condition, detail, pointer="", code="MALFORMED"):
    if not condition:
        raise Fault(code, detail, pointer)


def _pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _text(value, pointer):
    _require(type(value) is str and bool(value), "nonempty text required", pointer)
    _require(len(value) <= 512, "text exceeds 512 scalar values", pointer, "RESOURCE_LIMIT")
    _require(all(unicodedata.category(c) not in ("Cc", "Cs") for c in value),
             "control or surrogate in text", pointer)
    return value


def _identity(value, pointer):
    _require(type(value) is list and bool(value), "identity array required", pointer)
    _require(len(value) <= MAX_DEPTH, "identity exceeds 32 components", pointer, "RESOURCE_LIMIT")
    return [_text(v, _pointer(pointer, i)) for i, v in enumerate(value)]


def _mapping(value, pointer):
    _require(type(value) is dict, "object required", pointer)
    return value


def _field(value, key, pointer):
    _mapping(value, pointer)
    _require(key in value, "missing field", _pointer(pointer, key))
    return value[key]


def _list(value, limit, pointer):
    _require(type(value) is list, "array required", pointer)
    _require(len(value) <= limit, "array count exceeds profile", pointer, "RESOURCE_LIMIT")
    return value


def _numeric_token(raw, integer=False):
    # Bounds precede int/float allocation; JSON has already checked number syntax
    _require(len(raw) <= 64, "number lexeme exceeds 64 characters", code="RESOURCE_LIMIT")
    pieces = re.split("[eE]", raw)
    exponent = int(pieces[1]) if len(pieces) == 2 else 0
    _require(-400 <= exponent <= 400, "explicit exponent outside [-400,400]", code="RESOURCE_LIMIT")
    mantissa = pieces[0].lstrip("-")
    whole = mantissa.split(".")[0]
    digits = mantissa.replace(".", "")
    first = next((i for i, digit in enumerate(digits) if digit != "0"), None)
    if first is not None:
        adjusted = len(whole) - first - 1 + exponent
        _require(-324 <= adjusted <= 308, "adjusted exponent outside [-324,308]", code="RESOURCE_LIMIT")
    value = int(raw) if integer else float(raw)
    _require(type(value) is int or math.isfinite(value), "nonfinite JSON number")
    return value


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _depth(text):
    # Reject excessive nesting before the recursive JSON decoder runs
    level, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            level += 1
            _require(level <= MAX_DEPTH, "JSON nesting exceeds 32", code="RESOURCE_LIMIT")
        elif char in "]}":
            level -= 1
            _require(level >= 0, "unbalanced JSON delimiters")


def _document(raw):
    _require(type(raw) is bytes, "raw must be bytes")
    _require(len(raw) <= MAX_GLB_BYTES, "GLB exceeds 4 MiB", code="RESOURCE_LIMIT")
    _require(len(raw) >= 28, "truncated GLB")
    _require(struct.unpack_from("<III", raw) == (0x46546C67, 2, len(raw)), "GLB2 header or length")
    offset, chunks = 12, []
    for expected in (0x4E4F534A, 0x004E4942):
        _require(offset + 8 <= len(raw), "truncated chunk header")
        length, kind = struct.unpack_from("<II", raw, offset)
        _require(kind == expected and length % 4 == 0 and offset + 8 + length <= len(raw),
                 "one aligned JSON chunk then BIN chunk required")
        chunks.append((offset + 8, length))
        offset += 8 + length
    _require(offset == len(raw), "extra chunks or trailing bytes")
    start, length = chunks[0]
    _require(length <= MAX_JSON_BYTES, "JSON exceeds 2 MiB", code="RESOURCE_LIMIT")
    text = raw[start:start + length].decode("utf-8")
    _depth(text)
    def nonfinite(token):
        raise Fault("MALFORMED", "nonfinite JSON constant")
    document = json.loads(text, object_pairs_hook=_unique,
                          parse_int=lambda token: _numeric_token(token, True),
                          parse_float=_numeric_token, parse_constant=nonfinite)
    _require(_field(_field(document, "asset", ""), "version", "/asset") == "2.0",
             "glTF asset version must be 2.0", "/asset/version")
    return document


def _claim_tree(value, pointer):
    """Bound retained provenance claims; do not validate them against source."""
    if type(value) is dict:
        for key, item in value.items():
            _text(key, pointer)
            child = _pointer(pointer, key)
            if key in IDENTITY_FIELDS and not (key == "declaration_definition_id" and item is None):
                _identity(item, child)
            else:
                _claim_tree(item, child)
        if "start_byte" in value or "end_byte" in value:
            low, high = value.get("start_byte"), value.get("end_byte")
            _require(type(low) is int and type(high) is int and 0 <= low <= high,
                     "source byte span requires ordered nonnegative integers", pointer)
            _require(high <= 65536, "source span exceeds 65536 bytes", pointer, "RESOURCE_LIMIT")
    elif type(value) is list:
        for index, item in enumerate(value):
            _claim_tree(item, _pointer(pointer, index))
    elif type(value) is str:
        _text(value, pointer)


def _objects(document, program):
    node_pointer = "/nodes"
    nodes = _list(_field(document, "nodes", ""), MAX_OBJECTS, node_pointer)
    op = "/extras/ontokin/program/occurrences"
    occurrences = _mapping(_field(program, "occurrences", "/extras/ontokin/program"), op)
    _require(len(occurrences) <= MAX_OBJECTS, "occurrence count exceeds 128", op, "RESOURCE_LIMIT")
    records, ids, paths = [], set(), set()
    for index, node in enumerate(nodes):
        base = f"/nodes/{index}/extras/ontokin"
        meta = _mapping(_field(_field(node, "extras", f"/nodes/{index}"), "ontokin",
                               f"/nodes/{index}/extras"), base)
        _require(_field(meta, "kind", base) == "object", "object node required", base + "/kind")
        claims = {key: _field(meta, key, base) for key in
                  ("path", "element_id", "class_name", "program_revision", "source_mapping")}
        path = _text(claims["path"], base + "/path")
        oid = tuple(_identity(claims["element_id"], base + "/element_id"))
        _require(path not in paths and oid not in ids, "duplicate object identity or path", base)
        paths.add(path); ids.add(oid)
        for key in ("class_name", "program_revision"):
            _text(claims[key], base + "/" + key)
        _mapping(claims["source_mapping"], base + "/source_mapping")
        _require(path in occurrences, "node path has no program occurrence claim", base + "/path")
        occurrence = _mapping(occurrences[path], _pointer(op, path))
        _claim_tree(claims, base)
        _claim_tree(occurrence, _pointer(op, path))
        claims["program_occurrence"] = occurrence
        origins = {key: base + "/" + key for key in claims if key != "program_occurrence"}
        origins["program_occurrence"] = _pointer(op, path)
        records.append({"node": index, "claims": claims, "origins": origins})
    _require(paths == set(occurrences), "node and occurrence path sets differ", op)
    return records


def _number(value, pointer):
    _require(type(value) in (int, float) and math.isfinite(value), "finite JSON number required", pointer)
    return value


def _observe(raw):
    document = _document(raw)
    base = "/extras/ontokin"
    meta = _mapping(_field(_field(document, "extras", ""), "ontokin", "/extras"), base)
    for key, expected in (("target_contract", "ontokin.glb/0.2"), ("schema_version", "0.2"),
                          ("profile", "construction-0.1")):
        _require(_field(meta, key, base) == expected, "unsupported artifact profile", base + "/" + key,
                 "UNSUPPORTED")
    program = _mapping(_field(meta, "program", base), base + "/program")
    for container, pointer in ((meta, base), (program, base + "/program")):
        _require("sites" not in container, "direct site table is outside this raw profile",
                 pointer + "/sites", "UNSUPPORTED")
    source = _mapping(_field(meta, "source", base), base + "/source")
    program_claims = {key: _field(program, key, base + "/program") for key in
                      ("revision", "entry_source_id", "manifest", "sources")}
    for key in ("revision", "entry_source_id"):
        _text(program_claims[key], base + "/program/" + key)
    _mapping(program_claims["manifest"], base + "/program/manifest")
    units = _mapping(program_claims["sources"], base + "/program/sources")
    _require(len(units) <= 2, "source claim count exceeds two-file closure", base + "/program/sources",
             "RESOURCE_LIMIT")
    source_claims = {"source": source, "program": program_claims}
    _claim_tree(source_claims, base)
    objects = _objects(document, program)
    joints = _list(_field(meta, "joints", base), MAX_HINGES, base + "/joints")
    records, ids, paths, sites = [], set(), set(), set()
    for index, row in enumerate(joints):
        pointer = base + f"/joints/{index}"
        _mapping(row, pointer)
        _require(set(row) == set(FIELDS), "joint fields must be exactly the eight contract fields", pointer)
        path = _text(row["path"], pointer + "/path")
        oid = tuple(_identity(row["element_id"], pointer + "/element_id"))
        _require(path not in paths and oid not in ids, "duplicate joint identity or path", pointer)
        paths.add(path); ids.add(oid)
        _require(row["kind"] == "hinge", "only hinge joint rows are supported", pointer + "/kind", "UNSUPPORTED")
        for key in ("parent_site", "child_site"):
            sites.add(_text(row[key], pointer + "/" + key))
        axis = _list(row["axis"], 3, pointer + "/axis")
        _require(len(axis) == 3, "three axis components required", pointer + "/axis")
        for i, value in enumerate(axis):
            _number(value, pointer + f"/axis/{i}")
        _require(sum(value in (-1, 1) for value in axis) == 1 and
                 sum(value == 0 for value in axis) == 2, "signed basis axis required", pointer + "/axis")
        limits = _list(row["limits"], 2, pointer + "/limits")
        _require(len(limits) == 2, "two ordered limits required", pointer + "/limits")
        low, high = [_number(value, pointer + f"/limits/{i}") for i, value in enumerate(limits)]
        initial = _number(row["initial"], pointer + "/initial")
        _require(low <= high and low <= initial <= high, "reversed limits or initial outside closed range", pointer)
        origins = {key: pointer + "/" + key for key in FIELDS}
        origins.update({"limitLow": pointer + "/limits/0", "limitHigh": pointer + "/limits/1"})
        records.append({"claims": row, "origins": origins})
    _require(len(sites) <= MAX_SITES, "referenced site paths exceed 256", base + "/joints", "RESOURCE_LIMIT")
    return {"schema": SCHEMA, "kind": "untrusted-artifact-hinges",
            "artifactSha256": hashlib.sha256(raw).hexdigest(), "artifactBytes": len(raw),
            "records": records, "objects": objects, "sourceClaims": source_claims,
            "sourceOrigins": {"source": base + "/source", "program": {
                key: base + "/program/" + key for key in program_claims}},
            "profileName": "construction-0.1", "historicalInputsBound": False,
            "sourceAgreementVerified": False, "completeC255Semantic": False,
            "executionAllowed": False, "directSiteTableObserved": False,
            "jointDefinitionOrSpanObserved": False, "limits": LIMITS.copy()}


def observe_glb_hinges(raw):
    """Return untrusted raw claims or raise Fault; never read a path or source."""
    try:
        return _observe(raw)
    except Fault as fault:
        if type(raw) is bytes:
            fault.artifactBytes = len(raw)
            if len(raw) <= MAX_GLB_BYTES:
                fault.artifactSha256 = hashlib.sha256(raw).hexdigest()
        raise
    except (UnicodeError, ValueError, TypeError, KeyError, IndexError, struct.error,
            OverflowError, RecursionError) as exc:
        fault = Fault("MALFORMED", type(exc).__name__)
        if type(raw) is bytes and len(raw) <= MAX_GLB_BYTES:
            fault.artifactBytes, fault.artifactSha256 = len(raw), hashlib.sha256(raw).hexdigest()
        raise fault from exc 