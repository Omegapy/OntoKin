"""Independent finite C082 readers; no production parser or runtime imports.

The expected values are the published preimplementation inputs. The reusable
GLB/PNG readers below are structural byte readers from the preceding independent
verifier, not compiler/export helpers. This module neither executes source nor
uses a candidate artifact to generate expected source answers.
"""
from __future__ import annotations

import base64
from collections import Counter
import copy
import math
import json
from pathlib import Path
import re
import struct

from tools.texture_reference import (GLB, ReferenceError, SAMPLER, bundle_identity,
    canonical, decode_png, digest, exact_uv, f32, file_payload, loads, ordinary_path,
    repack_glb, require, sha)

ROOT = Path(__file__).resolve().parents[1]
FREEZE_COMMIT = "e1054f43efdd6099df395e978221dfad19523d69"
FREEZE_SHA256 = "537571b07f8f0192180fb5f15bb9537d16f13e4f5796c6e9bee10b4ed93d959b"
TARGET = "ontokin.glb/0.15"
PROFILE = "keyed-reduction-0.1"
PROTOCOL = "ontokin.agent/0.15"
STORE_SCHEMA = "ontokin.keyed-reduction-program-agent-store/0.1"
DELIVERED_CASES = {"panel-task", "panel-task-repaired", "panel-identity", "panel-task-higher-budget"}
SOURCE_IMPLEMENTATION = (
    "ontokin/reach_numeric.py", "ontokin/reach_kinematics.py", "ontokin/reach_pose.py",
    "ontokin/reach_phase.py", "ontokin/reach_runtime.py", "ontokin/reach_export.py",
    "ontokin/reach_recording_fast.py", "ontokin/reach_recording_capture.py", "ontokin/reach_transfer_bounds.py")
SOURCE_DERIVATION = (
    "docs/engineering/reach-numeric-kernel.md", "docs/engineering/reach-source-kernel.md",
    "docs/engineering/reach-coaxial-phase-bounds.md", "docs/engineering/reach-carrier-rotation-cursors.md",
    "docs/engineering/reach-recording-certified-planar.md", "docs/engineering/reach-deferred-phase-locations.md",
    "docs/engineering/reach-planning-reuse.md", "docs/engineering/reach-release-cell-envelope.md")


def load_fixtures(root=ROOT / "examples/keyed-reduction"):
    root = Path(root).resolve()
    repository = root.parent.parent
    freeze_raw = ordinary_path(repository, "docs/language-design/keyed-reduction-v0.1/INPUT-FREEZE.json").read_bytes()
    require(sha(freeze_raw) == FREEZE_SHA256, "Published C082 input freeze changed")
    freeze = loads(freeze_raw)
    names, size = set(), 0
    for entry in freeze["files"]:
        require(entry["path"] not in names, "Duplicate frozen path")
        raw = ordinary_path(repository, entry["path"]).read_bytes()
        require(len(raw) == entry["bytes"] and sha(raw) == entry["sha256"], "Frozen bytes changed: " + entry["path"])
        names.add(entry["path"]); size += len(raw)
    require(len(names) == freeze["file_count"] and size == freeze["total_bytes"],
            "Published freeze inventory is incomplete")
    expected = loads(ordinary_path(root, "expected.json").read_bytes())
    cases = {item["name"]: item for item in expected["cases"]}
    require(len(expected["cases"]) == len(cases) == expected["case_count"] and
            set(item["expected_outcome"] for item in cases.values()) <= {"valid", "invalid"},
            "C082 source corpus inventory differs")
    require({c["name"] for c in cases.values() if c["expected_stage"] == "delivered" and c["expected_outcome"] == "valid"} == DELIVERED_CASES,
            "Frozen delivered-stage scope differs")
    workflows = loads(ordinary_path(root, "workflows.json").read_bytes())
    acceptance = loads(ordinary_path(repository, "docs/language-design/keyed-reduction-v0.1/acceptance.json").read_bytes())
    require(acceptance["corpus"] == "examples/keyed-reduction/expected.json" and
            acceptance["cases"] == [{"id": c["id"], "name": c["name"],
                "groups": c["tags"], "outcome": c["expected_outcome"]} for c in expected["cases"]],
            "Frozen acceptance and source inventories differ")
    require(acceptance["workflows"] == "examples/keyed-reduction/workflows.json" and
            len(workflows["workflows"]) == 10 and
            {w["id"] for w in workflows["workflows"]} == {f"A{i:02d}" for i in range(1, 11)},
            "Frozen Agent inventory differs")
    result = {"root": root, "repository": repository, "freeze": freeze, "expected": expected,
              "cases": cases, "workflows": workflows, "acceptance": acceptance}
    for case in cases.values():
        require(bundle_identity(case_payload(result, case)) == (case["program_revision"], case["canonical_manifest"]),
                "Frozen program identity cannot be independently reproduced: " + case["name"])
        if case["expected_outcome"] == "valid":
            control = case["explicit_c081_control"]
            require(bundle_identity(case_payload(result, case, control=True)) == (control["program_revision"], control["canonical_manifest"]),
                    "Frozen explicit control identity differs: " + case["name"])
    return result


def case_payload(fixtures, case, *, control=False):
    manifest = case["explicit_c081_control"]["file_manifest"] if control else case["file_manifest"]
    return file_payload(fixtures["root"], manifest)


def canonical_probe_type(display):
    # These two documented presentation aliases occur in the frozen corpus.
    # No dimensional or generic leaf type is otherwise weakened or stripped.
    return {"Keyed<Quantity[m^2]>": "Keyed<Area>", "Quantity[m^2]": "Area",
            "Keyed<Point3>": "Keyed<Point3<Length>>", "Point3": "Point3<Length>"}.get(display, display)


def delivered_by_revision(fixtures):
    selected = [case for case in fixtures["cases"].values()
                if case["expected_outcome"] == "valid" and case["expected_stage"] == "delivered"]
    require(len(selected) == 4 and {c["name"] for c in selected} == DELIVERED_CASES,
            "Delivered named source inventory is incomplete")
    result = {}
    for case in selected:
        previous = result.get(case["program_revision"])
        if previous is not None:
            # C082 deliberately names the same exact panel bundle twice. Bind
            # the alias to independently equal inputs and answers before using
            # either name to verify an artifact retrieved only by revision.
            require(case_payload(fixtures, case) == case_payload(fixtures, previous) and
                    case_payload(fixtures, case, control=True) == case_payload(fixtures, previous, control=True) and
                    case["expected"] == previous["expected"] and
                    case["host_policy"] == previous["host_policy"],
                    "Delivered revision aliases disagree on frozen inputs or answers")
        else:
            result[case["program_revision"]] = case
    return result


def source_units(payload):
    return {"entry": payload["entry"], **{"package:" + u["package_id"] + "@" + u["version"]: u for u in payload["modules"]}}


def codes(value):
    if isinstance(value, dict):
        return sorted(set(([value["code"]] if isinstance(value.get("code"), str) else []) + [c for v in value.values() for c in codes(v)]))
    if isinstance(value, list):
        return sorted(set(c for v in value for c in codes(v)))
    return []


def walk(value, path=()):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, path + (key,))
    elif isinstance(value, list):
        for key, child in enumerate(value):
            yield from walk(child, path + (key,))


def check_location(location, units, *, allow_null=False):
    if location is None:
        require(allow_null, "Unexpected null source location")
        return None
    require(isinstance(location, dict), "Source location must be an object")
    key = location.get("source_id")
    require(key in units, "Source location refers to an absent unit")
    unit, start_key, end_key = units[key], "start_byte", "end_byte"
    if start_key not in location:
        start_key, end_key = "start", "end"
    start, end = location.get(start_key), location.get(end_key)
    raw = unit["source"].encode("utf-8")
    require(type(start) is int and type(end) is int and 0 <= start <= end <= len(raw), "Source location is out of range")
    # A source span must also terminate on UTF-8 boundaries.
    raw[:start].decode("utf-8"); raw[start:end].decode("utf-8"); raw[end:].decode("utf-8")
    if "source_revision" in location:
        require(location["source_revision"] == digest(raw), "Source span hash differs from original bytes")
    if "filename" in location:
        require(location["filename"] == unit["filename"], "Source span filename differs")
    return raw[start:end]


def same_location(actual, expected, units):
    check_location(actual, units)
    require(all(actual.get(k) == v for k, v in expected.items()), "Exact frozen source span differs")


def check_all_locations(value, units):
    count = 0
    for _, node in walk(value):
        if not isinstance(node, dict) or node.get("source_id") not in units:
            continue
        if ("start_byte" in node and "end_byte" in node) or ("start" in node and "end" in node):
            check_location(node, units); count += 1
        if "source_revision" in node:
            require(node["source_revision"] == digest(units[node["source_id"]]["source"].encode()), "Source revision lost byte binding")
    return count


def panel_transform(case, fixtures):
    return case["expected"].get("transform_provenance", fixtures["cases"]["panel-task"]["expected"]["transform_provenance"])


def check_transforms(records, units, *, expected=None, require_nonempty=True):
    require(isinstance(records, list) and (not require_nonempty or records), "Missing ordered map derivation records")
    count = 0
    for record in records:
        base_fields = {"expression", "body", "input", "input_element_type", "output_element_type"}
        require(isinstance(record, dict) and set(record) in (base_fields, base_fields | {"key", "input_entry"}),
                "Transform projection has an unadopted shape")
        expression = check_location(record["expression"], units)
        require(expression.startswith(b"map_keyed<"), "Derived expression does not identify the authored map")
        check_location(record["body"], units); check_location(record["input"], units)
        for name in ("body", "input"):
            location, outer = record[name], record["expression"]
            require(location["source_id"] == outer["source_id"] and
                    outer["start_byte"] <= location["start_byte"] < location["end_byte"] <= outer["end_byte"],
                    "Map body/input lies outside its exact expression")
        require(all(type(record[k]) is str and record[k] for k in ("input_element_type", "output_element_type")), "Missing map element types")
        if "key" in record:
            require(type(record["key"]) is str and record["key"].isascii() and record["key"], "Derived leaf lost its stable input key")
            raw_entry = check_location(record["input_entry"], units, allow_null=True)
            if raw_entry is not None:
                require(re.match(re.escape(canonical(record["key"])) + rb"\s*:", raw_entry) is not None,
                        "Derived leaf entry span identifies another original key")
        count += 1
    if expected is not None:
        record = records[-1]
        for part in ("expression", "body", "input"):
            same_location(record[part], expected[part], units)
        expected_input = expected.get("input_element_type") or ("Length" if expected["input_element_kind"] == "Quantity" else expected["input_element_kind"])
        require(record["input_element_type"] == expected_input and record["output_element_type"] == expected.get("output_element_type", "Length"), "Panel map element dimensions differ")
    return count



def _location_identity(value):
    return (value.get("source_id"), value.get("start_byte", value.get("start")),
            value.get("end_byte", value.get("end")))


def _source_tokens(raw):
    """Bounded byte-level delimiter reader; never evaluates OntoKin source."""
    require(len(raw) <= 1048576, "Independent source delimiter input exceeds its bound")
    tokens, index = [], 0
    while index < len(raw):
        byte, start = raw[index], index
        if byte in b" \t\r\n":
            index += 1
            continue
        if raw.startswith(b"//", index):
            end = raw.find(b"\n", index + 2)
            index = len(raw) if end < 0 else end
            continue
        if raw.startswith(b"/*", index):
            end = raw.find(b"*/", index + 2)
            require(end >= 0, "Unterminated source delimiter comment")
            index = end + 2
            continue
        if byte == 34:
            index += 1
            while index < len(raw) and raw[index] != 34:
                index += 2 if raw[index] == 92 else 1
            require(index < len(raw), "Unterminated source delimiter string")
            index += 1
        elif byte in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789":
            index += 1
            while index < len(raw) and raw[index] in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789":
                index += 1
        elif raw.startswith(b"->", index):
            index += 2
        else:
            index += 1
        tokens.append((raw[start:index], start, index))
        require(len(tokens) <= 262144, "Independent source token inventory exceeds its bound")
    return tokens


def _generic_type(tokens, name_index, name):
    require(tokens[name_index][0] == name and tokens[name_index + 1][0] == b"<",
            "Source expression lost its explicit type argument")
    depth, index = 1, name_index + 2
    while index < len(tokens) and depth:
        token = tokens[index][0]
        depth += (token == b"<") - (token == b">")
        require(depth <= 64 and token != b",", "Independent type delimiter bound/arity differs")
        index += 1
    require(depth == 0 and index > name_index + 3, "Unterminated/empty explicit source type")
    return b"".join(t[0] for t in tokens[name_index + 2:index - 1]).decode("ascii"), index


def _closing_delimiter(tokens, start):
    closes = {b"(": b")", b"[": b"]", b"{": b"}"}
    require(start < len(tokens) and tokens[start][0] in closes, "Missing source opening delimiter")
    stack = []
    for index in range(start, len(tokens)):
        token = tokens[index][0]
        if token in closes:
            stack.append(closes[token])
            require(len(stack) <= 128, "Independent source delimiter depth exceeds its bound")
        elif token in closes.values():
            require(stack and stack.pop() == token, "Mismatched source expression delimiter")
            if not stack:
                return index
    raise ReferenceError("Unterminated source expression delimiter")


def _top_level_commas(tokens, start, end):
    commas, index = [], start
    while index < end:
        token = tokens[index][0]
        if token in (b"(", b"[", b"{"):
            index = _closing_delimiter(tokens, index)
            require(index < end, "Source child expression crosses its enclosing boundary")
        elif token in (b")", b"]", b"}"):
            raise ReferenceError("Unmatched source child delimiter")
        elif token == b",":
            commas.append(index)
        index += 1
    return commas


def _declared_keyed_types(name, units, *, function=False):
    """Read only explicit annotations, without type inference or execution."""
    candidates = set()
    for unit in units.values():
        tokens = _source_tokens(unit["source"].encode("utf-8"))
        for index, token in enumerate(tokens):
            if token[0] != name:
                continue
            cursor = index + 1
            if cursor < len(tokens) and tokens[cursor][0] == b"@":
                cursor += 2  # declaration's authored stable string key
            if function:
                if index == 0 or tokens[index - 1][0] != b"fn" or cursor >= len(tokens) or tokens[cursor][0] != b"(":
                    continue
                cursor = _closing_delimiter(tokens, cursor) + 1
                if cursor >= len(tokens) or tokens[cursor][0] != b"->":
                    continue
            elif cursor >= len(tokens) or tokens[cursor][0] != b":":
                continue
            cursor += 1
            if cursor + 1 < len(tokens) and tokens[cursor][0] == b"Keyed" and tokens[cursor + 1][0] == b"<":
                leaf, _ = _generic_type(tokens, cursor, b"Keyed")
                candidates.add(canonical_probe_type(leaf))
    return candidates


def reduction_source_shape(location, units):
    """Read exact input/seed/body spans and explicit types from frozen bytes.

    This finite provenance reader splits source delimiters and annotations. It
    does not evaluate expressions or resolve general overloads. Input types
    are checked for explicit keyed/map syntax and unambiguous declared keyed
    names/helper returns; the frozen corpus uses only those forms.
    """
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Reduction expression span includes non-expression boundary bytes")
    accumulator, opening = _generic_type(tokens, 0, b"reduce_keyed")
    closing = _closing_delimiter(tokens, opening)
    require(closing == len(tokens) - 1 and tokens[opening][0] == b"(",
            "Reduction expression span is not the complete authored call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 2, "Reduction source does not have exact input/seed/binder-body arguments")
    first, second = commas
    binder_start = second + 1
    binder_end = _closing_delimiter(tokens, binder_start)
    require(tokens[binder_start][0] == b"(" and binder_end + 2 < closing and tokens[binder_end + 1][0] == b"->",
            "Reduction source lost its binder/body delimiter")
    binders = [t[0] for t in tokens[binder_start + 1:binder_end]]
    require(len(binders) == 5 and binders[1] == binders[3] == b"," and
            all(re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", binders[i]) for i in (0, 2, 4)),
            "Reduction source does not have its exact three binders")
    ranges = {"input": (opening + 1, first), "seed": (first + 1, second), "body": (binder_end + 2, closing)}
    base = location.get("start_byte", location.get("start"))
    source_id = location["source_id"]
    parts = {}
    for name, (start, end) in ranges.items():
        require(start < end, "Reduction source has an empty " + name + " expression")
        parts[name] = {"source_id": source_id, "source_revision": digest(units[source_id]["source"].encode("utf-8")),
                       "start_byte": base + tokens[start][1], "end_byte": base + tokens[end - 1][2]}
    input_tokens = tokens[opening + 1:first]
    input_type = None
    if input_tokens[0][0] in (b"keyed", b"map_keyed"):
        input_type, _ = _generic_type(input_tokens, 0, input_tokens[0][0])
    else:
        names = [t[0] for t in input_tokens]
        if len(names) == 1 or len(names) == 3 and names[:2] == [b"self", b"."]:
            types = _declared_keyed_types(names[-1], {source_id: units[source_id]})
        elif b"(" in names:
            opening_call = names.index(b"(")
            prefix = names[:opening_call]
            types = (_declared_keyed_types(prefix[-1], units, function=True)
                     if len(prefix) == 1 or len(prefix) == 3 and prefix[1] == b"." else set())
        else:
            types = set()
        if len(types) == 1:
            input_type = next(iter(types))
    return {"parts": parts, "accumulator_type": canonical_probe_type(accumulator),
            "input_element_type": None if input_type is None else canonical_probe_type(input_type)}


def check_reductions(records, units, *, expected=None, require_nonempty=True):
    """Bind every aggregate derivation to original source without writable IDs."""
    require(isinstance(records, list) and (records or not require_nonempty),
            "Missing ordered reduction derivation records")
    fields = {"expression", "input", "seed", "body", "input_element_type", "accumulator_type"}
    seen = set()
    for index, record in enumerate(records):
        require(isinstance(record, dict) and set(record) == fields,
                "Reduction projection has an unadopted shape or invented identity")
        expression = check_location(record["expression"], units)
        require(expression.startswith(b"reduce_keyed<"), "Derived expression is not the authored reduction")
        outer = record["expression"]
        for name in ("input", "seed", "body"):
            child = record[name]
            check_location(child, units)
            require(child["source_id"] == outer["source_id"] and
                    outer["start_byte"] <= child["start_byte"] < child["end_byte"] <= outer["end_byte"],
                    "Reduction input/seed/body lies outside its exact expression")
        require(all(type(record[k]) is str and record[k] for k in ("input_element_type", "accumulator_type")),
                "Missing reduction input/accumulator types")
        authored = reduction_source_shape(outer, units)
        for name in ("input", "seed", "body"):
            same_location(record[name], authored["parts"][name], units)
        require(canonical_probe_type(record["accumulator_type"]) == authored["accumulator_type"],
                "Reduction accumulator type differs from its explicit source type")
        if authored["input_element_type"] is not None:
            require(canonical_probe_type(record["input_element_type"]) == authored["input_element_type"],
                    "Reduction input element type differs from its explicit source annotation")
        identity = tuple(_location_identity(record[name]) for name in ("expression", "input", "seed", "body")) + (
            record["input_element_type"], record["accumulator_type"])
        require(identity not in seen, "Duplicate reduction source derivation")
        seen.add(identity)
        # A nested selected reduction completes before its enclosing fold.
        for earlier in records[:index]:
            a, b = earlier["expression"], outer
            require(not (a["source_id"] == b["source_id"] and
                    a["start_byte"] < b["start_byte"] and b["end_byte"] <= a["end_byte"]),
                    "Nested reduction provenance is not in evaluation order")
    if expected is not None:
        matches = [record for record in records
                   if _location_identity(record["expression"]) == _location_identity(expected["expression"])]
        require(len(matches) == 1, "Frozen reduction expression is absent or duplicated")
        current = matches[0]
        for name in ("expression", "input", "seed", "body"):
            same_location(current[name], expected[name], units)
        wanted_input = expected.get("input_element_type", "Length")
        wanted_acc = expected.get("accumulator_type", "Length")
        require(current["input_element_type"] == wanted_input and current["accumulator_type"] == wanted_acc,
                "Frozen reduction dimensions differ")
    return len(records)


def require_expression_origins(records, expected, units, label):
    for wanted in expected:
        check_location(wanted, units)
        matches = [record for record in records
                   if _location_identity(record["expression"]) == _location_identity(wanted)]
        require(matches, "Actual value lost a required " + label + " expression")
        for match in matches:
            same_location(match["expression"], wanted, units)


def inspect_member(items, object_path, name):
    matches = [item["values"][name] for item in items if name in item.get("values", {}) and
               (item.get("path") in (object_path, object_path + "." + name) or item.get("name") == name)]
    require(matches and all(item == matches[0] for item in matches),
            "Requested public member is absent/ambiguous: " + object_path + "." + name)
    return matches[0]


def semantic_value(value, units):
    if isinstance(value, list):
        return [semantic_value(child, units) for child in value]
    if not isinstance(value, dict):
        return value
    location = value.get("source_id") in units and (("start" in value and "end" in value)
        or ("start_byte" in value and "end_byte" in value))
    result = {}
    for name, child in value.items():
        if name in ("derived_transforms", "derived_reductions", "input_entry"):
            continue
        if location and name in ("source_revision", "filename", "start", "end", "start_byte", "end_byte"):
            continue
        result[name] = semantic_value(child, units)
    return result


def check_panel_values(items, case, fixtures, units, *, control=False):
    """Check each occurrence's exact aggregate and keyed widths from source math."""
    expected, checks = case["expected"], 0
    for owner, wanted in expected["aggregate_lengths_m"].items():
        value = inspect_member(items, owner, "aggregate")
        require(value["type"] == "Length" and value["value"] == wanted,
                "Panel aggregate differs from independently frozen sequential math")
        require(value.get("status") == "resolved" and not value.get("stale"), "Panel aggregate is stale/unresolved")
        if not control:
            check_reductions(value.get("derived_reductions"), units, expected=expected["reduction_provenance"])
            transforms = value.get("derived_transforms", [])
            check_transforms(transforms, units, expected=expected["map_input_provenance"])
        checks += 1
    for owner, widths in expected["widths_m"].items():
        value = inspect_member(items, owner, "widths")
        require(value["type"] == "Keyed<Length>" and
                {entry["key"]: entry["value"]["value"] for entry in value["value"]} == widths,
                "Panel widths differ from independently frozen source math")
        require([entry["key"] for entry in value["value"]] == sorted(widths),
                "Panel width keys/order differ")
        if not control:
            check_keyed_leaf_provenance(value, units, expected=panel_transform(case, fixtures))
            check_reductions(value.get("derived_reductions"), units, expected=expected["reduction_provenance"])
            for entry in value["value"]:
                check_reductions(entry["value"].get("derived_reductions"), units,
                                 expected=expected["reduction_provenance"])
        checks += len(widths)
    return checks

def check_keyed_leaf_provenance(value, units, *, expected=None):
    """Require the adopted output-leaf projection, not aggregate-only labels."""
    aggregate = value.get("derived_transforms")
    check_transforms(aggregate, units, expected=expected)
    checked = 0
    for entry in value["value"]:
        records = entry["value"].get("derived_transforms")
        check_transforms(records, units)
        current = records[-1]
        require(current.get("key") == entry["key"] and "input_entry" in current,
                "Output leaf lost its original stable key/entry projection")
        require(current["input_entry"] is not None, "Frozen literal input leaf lost its known original entry span")
        require(all(current[field] == aggregate[-1][field] for field in
                    ("expression", "body", "input", "input_element_type", "output_element_type")),
                "Output leaf is not bound to its aggregate's final source map")
        if expected is not None:
            same_location(current["input_entry"], expected["original_key_entries"][entry["key"]], units)
        checked += 1
    return checked


def check_generated_shapes(items, case, units, *, control=False):
    """Bind the two frozen sphere-generation cases to their source math."""
    expected = case["expected"]
    objects = [item for item in items if item.get("kind") == "object"]
    generated = {item["path"]: item for item in objects if "generated" in item.get("source", {})}
    require(len({item["path"] for item in objects}) == len(objects),
            "Generated shape inspection repeats an object")
    require(set(generated) == set(expected["radii_m"]), "Generated occurrence path set differs")
    require(sorted(item["source"]["generated"]["input_key"] for item in generated.values()) == expected["generated_keys"],
            "Generated occurrence keys differ from frozen source keys")
    required = []
    if not control:
        # Each of these frozen source files has one reduction statement. Read
        # its original UTF-8 expression bytes, without asking the candidate
        # compiler to supply either locations or expected values.
        for identity, unit in units.items():
            raw = unit["source"].encode("utf-8")
            for match in re.finditer(rb"reduce_keyed<[^;]+", raw):
                end = match.start() + len(match.group().rstrip())
                required.append({"source_id": identity, "source_revision": digest(raw),
                                 "start_byte": match.start(), "end_byte": end})
        require(len(required) == 1, "Frozen generated-shape reduction source is ambiguous")
    for path, radius in expected["radii_m"].items():
        item = generated[path]
        geometry = item.get("geometry", {})
        require(geometry.get("available") is True and
                geometry.get("description") == {"kind": "sphere", "radius": radius} and
                geometry.get("representation") == "authored_analytic_geometry",
                "Generated sphere geometry differs from independently frozen radius")
        value = inspect_member(items, path, "size")
        require(value["type"] == "Length" and value["value"] == radius and
                value.get("status") == "resolved" and not value.get("stale"),
                "Generated typed radius differs from independently frozen source math")
        if not control:
            for records in (value.get("derived_reductions"), item["source"]["generated"].get("input_reductions")):
                check_reductions(records, units)
                require_expression_origins(records, required, units, "generated-shape reduction")
    return len(expected["radii_m"])


def expected_occurrences(case):
    expected = case["expected"]
    nodes = {}
    for owner, origin, velocity in (("first", [-8, 0, 0], [0, .5, 0]), ("sibling", [2, 0, 0], [0, 0, 0])):
        nodes[owner] = {"path": owner, "element_id": ["panel-task", "demo", owner], "owner": None,
                        "origin": origin, "velocity": velocity, "empty": True, "bindings": {}, "triangle_count": 0, "materials": {}}
    for panel in expected["panels"] + [expected["marker"]]:
        poses = panel["poses"]
        origin = poses[0]["position_m"]
        velocity = [end - start for start, end in zip(origin, poses[-1]["position_m"])]
        is_panel = "input_key" in panel
        nodes[panel["path"]] = {**copy.deepcopy(panel), "origin": origin, "velocity": velocity, "empty": False,
            "element_id": panel.get("element_id", ["panel-task", "demo", "marker"]),
            "owner": panel.get("owner"), "bindings": {"top": {"asset_id": "label", "mapping": expected["mapping"]}} if is_panel else {}}
    return nodes


def check_inspection(actual, control, case, fixtures):
    """Compare public aggregates with frozen math and independently authored .14 controls."""
    payload, baseline = case_payload(fixtures, case), case_payload(fixtures, case, control=True)
    units, old_units = source_units(payload), source_units(baseline)
    require(actual.get("program_revision") == case["program_revision"], "Inspection names another program")
    require(control.get("program_revision") == case["explicit_c081_control"]["program_revision"],
            "Control inspection names another source")
    require(actual.get("ok") is not False and control.get("ok") is not False and
            not any(code.startswith(("OKL-E-", "OKE-E-")) for code in codes(actual) + codes(control)), "Inspection failed")
    a_items, b_items = actual.get("items", []), control.get("items", [])
    require(a_items and b_items, "Public inspection retained no source records")
    location_count = check_all_locations(actual, units) + check_all_locations(control, old_units)
    transform_count, reduction_count = 0, 0
    for _, node in walk(actual):
        if isinstance(node, dict):
            if "derived_transforms" in node:
                transform_count += check_transforms(node["derived_transforms"], units)
            if "derived_reductions" in node:
                reduction_count += check_reductions(node["derived_reductions"], units)
            if "input_reductions" in node:
                reduction_count += check_reductions(node["input_reductions"], units)
    for _, node in walk(control):
        if isinstance(node, dict):
            require("derived_reductions" not in node and "input_reductions" not in node,
                    "Legacy .14 projection acquired .15 reduction fields")
            if "derived_transforms" in node:
                check_transforms(node["derived_transforms"], old_units)
    probes = 0
    if "probe" in case:
        probe = case["probe"]
        av = inspect_member(a_items, probe["object_path"], probe["member"])
        bv = inspect_member(b_items, probe["object_path"], probe["member"])
        require(av.get("status") == bv.get("status") == "resolved" and not av.get("stale") and not bv.get("stale"),
                "Aggregate probe is not currently resolved")
        require(av["type"] == bv["type"] and canonical_probe_type(av["type"]) == canonical_probe_type(probe["type"]),
                "Aggregate output type/dimension differs")
        require(av.get("frame") == bv.get("frame") and av.get("canonical_unit") == bv.get("canonical_unit"),
                "Aggregate frame or canonical unit differs from explicit control")
        require(semantic_value(av["value"], units) == semantic_value(bv["value"], old_units),
                "Complete typed aggregate differs from the separately authored explicit control")
        if "scalar_value" in probe:
            wanted, got = probe["scalar_value"], av["value"]
            require(got == wanted and (type(got) is type(wanted) or type(got) in (int, float) and type(wanted) in (int, float)),
                    "Independent scalar aggregate answer differs")
            probes += 1
        reductions, transforms = av.get("derived_reductions", []), av.get("derived_transforms", [])
        if probe["reduction_required"]:
            check_reductions(reductions, units)
        else:
            require(not reductions, "Ordinary older function acquired intrinsic reduction provenance")
        require_expression_origins(reductions, probe["required_reduction_expressions"], units, "reduction")
        require_expression_origins(transforms, probe["required_transform_expressions"], units, "map")
        require(not any(name in av for name in ("key", "iteration", "ordinal", "element_id")),
                "Aggregate acquired a new editable or iteration identity")
        dependency_paths = {record["path"] for record in av.get("dependencies", []) if "path" in record}
        expectations = case.get("expected") or {}
        require(set(expectations.get("observed_dependencies_include", [])) <= dependency_paths,
                "Aggregate lost an actual earlier dependency read")
        require(not set(expectations.get("observed_dependencies_exclude", [])) & dependency_paths,
                "Aggregate invented an unselected dynamic dependency")
        for dependency in av.get("dependencies", []):
            require(dependency["program_revision"] == case["program_revision"], "Dependency names a stale source revision")
    if "widths_m" in (case.get("expected") or {}):
        probes += check_panel_values(a_items, case, fixtures, units)
        probes += check_panel_values(b_items, case, fixtures, old_units, control=True)
    if "radii_m" in (case.get("expected") or {}):
        probes += check_generated_shapes(a_items, case, units)
        probes += check_generated_shapes(b_items, case, old_units, control=True)
    require(probes or "probe" in case, "Valid source has no independently checked aggregate probe")
    return {"status": "passed", "typed_probe": case.get("probe", {}).get("type"), "scalar_checks": probes,
            "source_locations": location_count, "derived_transform_records": transform_count,
            "derived_reduction_records": reduction_count,
            "control_program_revision": case["explicit_c081_control"]["program_revision"]}


def implementation_basis(repository):
    def aggregate(paths):
        chunks = []
        for path in paths:
            raw = ordinary_path(repository, path).read_bytes()
            require(len(raw) <= 262144, "Numeric identity component exceeds its finite bound")
            chunks.append(path.encode() + b"\0" + sha(raw).encode() + b"\n")
        return digest(b"".join(chunks))
    return {"source": {"name": "OntoKin controlled source poses", "version": "0.2",
        "implementation_sha256": aggregate(SOURCE_IMPLEMENTATION),
        "method": "ontokin.source-pose-projective-dyadic/0.2", "derivation_sha256": aggregate(SOURCE_DERIVATION)},
        "destination": {"implementation_sha256": digest(ordinary_path(repository, "tools/reach_destination.mjs").read_bytes()),
                        "derivation_sha256": digest(ordinary_path(repository, "docs/engineering/reach-destination-numerics.md").read_bytes())}}


def check_program_metadata(glb, case, fixtures, *, control=False):
    payload = case_payload(fixtures, case, control=control)
    revision, manifest = bundle_identity(payload)
    units = source_units(payload)
    meta = glb.document["extras"]["ontokin"]
    require(meta.get("target_contract") == ("ontokin.glb/0.14" if control else TARGET) and
            meta.get("schema_version") == ("0.14" if control else "0.15") and
            meta.get("profile") == ("keyed-transform-0.1" if control else PROFILE), "GLB source/target contract mismatch")
    require(meta["source"]["uri"] == payload["entry"]["filename"] == "main.ok" and meta["source"]["entry_source_id"] == "entry" and
            meta["source"]["entry_revision"] == digest(units["entry"]["source"].encode()), "GLB source locator identity differs")
    program = meta["program"]
    require(program["revision"] == revision and program["manifest"] == manifest and program["entry_source_id"] == "entry", "GLB immutable program manifest differs")
    require(set(program["sources"]) == set(units), "GLB source unit set differs")
    for identity, unit in units.items():
        actual = program["sources"][identity]
        match = re.search(r'\bmodule\s+(\w+)\s*@\s*"([^"]+)"', unit["source"])
        require(match is not None, "Frozen source lacks literal module identity")
        expected = {"source_id": identity, "source_revision": digest(unit["source"].encode()), "filename": unit["filename"],
                    "package_id": unit.get("package_id"), "version": unit.get("version"), "module_name": match[1], "module_key": match[2]}
        require(actual == expected, "GLB source unit metadata differs")
    wanted_nodes = expected_occurrences(case)
    require(set(program["occurrences"]) == set(wanted_nodes) == set(glb.objects()), "GLB occurrence/path inventory differs")
    require(set(program["collections"]) == {"first.panels", "sibling.panels"}, "GLB generated collection inventory differs")
    transformed = panel_transform(case, fixtures)
    for owner in ("first", "sibling"):
        collection = program["collections"][owner + ".panels"]
        require(collection["owner_path"] == owner and collection["ordered_keys"] == ["left", "right"] and
                collection["element_id"] == ["panel-task", "demo", owner, "panels"], "Generated collection key/owner identity differs")
        require(set(collection["entries"]) == {"left", "right"}, "Generated entry set differs")
        for key, entry in collection["entries"].items():
            path = owner + '.panels["' + key + '"]'
            require(entry == {"path": path, "element_id": wanted_nodes[path]["element_id"]}, "Generated entry stable identity differs")
    for path, wanted in wanted_nodes.items():
        occurrence = program["occurrences"][path]
        require(occurrence["path"] == path and occurrence["element_id"] == wanted["element_id"] and
                occurrence["owner_path"] == wanted["owner"], "Ordinary/generated occurrence identity differs")
        node = glb.document["nodes"][glb.objects()[path]]
        identity = node["extras"]["ontokin"]
        require(identity["source_mapping"] == occurrence and identity["element_id"] == wanted["element_id"] and
                identity["program_revision"] == revision, "Native node lost its exact source mapping")
        generated = occurrence.get("generated")
        if "input_key" in wanted:
            key = wanted["input_key"]
            require(generated and generated["key"] == key and generated["collection_path"] == wanted["owner"] + ".panels" and
                    generated["unique_declaration_span"] is False, "Generated key provenance differs")
            if not control:
                same_location(generated["input_entry"], transformed["original_key_entries"][key], units)
                check_transforms(generated.get("input_transforms"), units, expected=transformed)
                check_reductions(generated.get("input_reductions"), units,
                                 expected=case["expected"]["reduction_provenance"])
            else:
                require("input_reductions" not in generated, "Legacy .14 generated occurrence acquired .15 provenance")
                check_transforms(generated.get("input_transforms"), units)
        else:
            require(generated is None, "Ordinary occurrence is mislabelled generated")
    count = check_all_locations(glb.document, units)
    basis = implementation_basis(fixtures["repository"])
    quantization = meta["reach_quantization"]
    require(quantization["source_numeric_bound_basis"] == basis["source"], "GLB source numeric identity is not the supplied source implementation")
    for name, value in basis["destination"].items():
        require(quantization["destination_numeric_bound_basis"][name] == value, "GLB destination numeric identity differs")
    require(quantization["position_tolerance_m"] <= .001 and quantization["rotation_tolerance_rad"] <= .001 and
            quantization["time_tolerance_s"] <= 1e-6, "Inherited recording tolerances were widened")
    return {"program_revision": revision, "source_locations": count, "generated_occurrences": 4, "ordinary_occurrences": 3}


def near(actual, expected, tolerance, message):
    require(len(actual) == len(expected) and all(math.isfinite(a) and abs(a-b) <= tolerance for a, b in zip(actual, expected)), message)


def check_geometry(glb, case):
    report, used_materials, used_textures, used_images = [], set(), set(), set()
    for path, wanted in expected_occurrences(case).items():
        primitives = glb.primitives(path)
        if wanted["empty"]:
            require(not primitives, "Empty source carrier acquired native geometry")
            continue
        require(len(primitives) == 3, "Rectangular extrusion lost its three material regions")
        corners = {struct.pack("<3f", *point) for point in wanted["raw_corner_set_m"]}
        actual_corners, counts, volume, area = set(), Counter(), 0., 0.
        center = [(a+b)/2 for a,b in zip(*wanted["local_bounds_m"])]
        for primitive in primitives:
            require(primitive.get("mode", 4) == 4 and set(primitive["attributes"]) in ({"POSITION", "NORMAL"}, {"POSITION", "NORMAL", "TEXCOORD_0"}), "Native primitive mode/stream set differs")
            region = primitive["extras"]["ontokin"]["region_key"]
            require(region in wanted["materials"], "Unknown material region")
            positions = glb.accessor(primitive["attributes"]["POSITION"])
            normals = glb.accessor(primitive["attributes"]["NORMAL"])
            indices = glb.accessor(primitive["indices"])
            require(len(positions) == len(normals) and len(indices) % 3 == 0 and indices, "Native geometry cardinality differs")
            require(all(type(i) is int and 0 <= i < len(positions) for i in indices), "Native triangle index is out of range")
            selected = set(indices)
            for i in selected:
                encoded = struct.pack("<3f", *positions[i]); actual_corners.add(encoded)
                require(encoded in corners, "Native vertex is absent from the independent source prism")
                require(abs(sum(n*n for n in normals[i])-1) <= 1e-6, "Native normal is not unit length")
            for offset in range(0, len(indices), 3):
                a,b,c = [positions[i] for i in indices[offset:offset+3]]
                ab, ac = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
                cross = [ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0]]
                magnitude = math.sqrt(sum(x*x for x in cross))
                require(magnitude > 0 and sum(cross[i]*((a[i]+b[i]+c[i])/3-center[i]) for i in range(3)) > 0, "Triangle is degenerate or inward wound")
                for i in indices[offset:offset+3]:
                    near(normals[i], [v/magnitude for v in cross], 1e-6, "Face normal disagrees with triangle winding")
                area += magnitude/2
                volume += sum(a[i] * [b[1]*c[2]-b[2]*c[1], b[2]*c[0]-b[0]*c[2], b[0]*c[1]-b[1]*c[0]][i] for i in range(3))/6
            counts[region] += len(indices)//3
            material_index = primitive["material"]; used_materials.add(material_index)
            material = glb.reference("materials", material_index)
            identity = material["extras"]["ontokin"]
            require(identity["occurrence_path"] == path and identity["source_region_key"] == region, "Material occurrence/region identity differs")
            pbr, wanted_material = material["pbrMetallicRoughness"], wanted["materials"][region]
            require(pbr["baseColorFactor"] == wanted_material["color"] and pbr["metallicFactor"] == wanted_material["metallic"] and
                    pbr["roughnessFactor"] == wanted_material["roughness"] and material.get("alphaMode", "OPAQUE") == "OPAQUE" and
                    not material.get("doubleSided", False), "Native linear material/opacity differs")
            binding = wanted["bindings"].get(region)
            if not binding:
                require("baseColorTexture" not in pbr and "TEXCOORD_0" not in primitive["attributes"], "Untextured region acquired texture coordinates/image")
                continue
            require(set(primitive["attributes"]) == {"POSITION", "NORMAL", "TEXCOORD_0"}, "Textured region lost its UV stream")
            texture_info = pbr["baseColorTexture"]
            require(texture_info.get("texCoord", 0) == 0, "Native texture selects another UV set")
            texture_index = texture_info["index"]; used_textures.add(texture_index)
            texture = glb.reference("textures", texture_index); used_images.add(texture["source"])
            require(glb.reference("samplers", texture["sampler"]) == SAMPLER, "Native sampler is not nearest/clamp")
            image = glb.reference("images", texture["source"])
            require(image["extras"]["ontokin"]["asset_id"] == binding["asset_id"], "Texture references another source image")
            uvs = glb.accessor(primitive["attributes"]["TEXCOORD_0"])
            require(len(uvs) == len(positions), "UV row count differs from geometry")
            for i, uv in enumerate(uvs):
                expected = exact_uv(positions[i], binding["mapping"]) if i in selected else (0.,0.)
                require(struct.pack("<2f", *uv) == struct.pack("<2f", *expected), "Native UV differs from exact rational source affine map")
        require(actual_corners == corners and dict(counts) == wanted["region_triangle_counts"], "Independent complete corner/region triangle inventory differs")
        require(abs(volume-wanted["volume_m3"]) <= 1e-12 and abs(area-wanted["surface_area_m2"]) <= 1e-12, "Independent closed-prism volume/area differs")
        report.append({"path": path, "triangles": sum(counts.values()), "corners": len(corners), "volume_m3": volume, "surface_area_m2": area})
    require(used_materials == set(range(len(glb.document["materials"]))) and used_textures == set(range(len(glb.document.get("textures", [])))) and
            used_images == set(range(len(glb.document.get("images", [])))), "Dangling material/texture/image resource")
    return report


def check_images(glb, payload):
    assets = {a["asset_id"]: base64.b64decode(a["data_base64"], validate=True) for a in payload["assets"]}
    require(len(glb.document["images"]) == len(assets) == 1, "Panel task has exactly one native image")
    report = []
    for image in glb.document["images"]:
        identity = image["extras"]["ontokin"]; name = identity["asset_id"]
        require(name in assets and image.get("name") == name and image["mimeType"] == "image/png" and "uri" not in image,
                "Embedded image identity/transport differs")
        raw = glb.view_bytes(image["bufferView"])
        require(raw == assets[name] and identity["sha256"] == digest(raw) and identity["byte_length"] == len(raw), "Embedded PNG bytes/digest differ from exact source attachment")
        png = decode_png(raw)
        report.append({"asset_id": name, "sha256": sha(raw), "bytes": len(raw), "width": png["width"], "height": png["height"], "decoded_sha256": png["decoded_sha256"]})
    return report


def check_motion(glb, case):
    nodes = expected_occurrences(case)
    require(len(glb.document["animations"]) == 1, "Missing unique recorded animation")
    streams = glb.animation_streams()
    require(set(streams) == {(path, kind) for path in nodes for kind in ("translation", "rotation")}, "Recorded pose stream inventory differs")
    observations = []
    for time in (0., .25, .5, .75, 1.):
        for path, node in nodes.items():
            pose = glb.pose(path, time)
            near(pose["translation"], [x + time*v for x,v in zip(node["origin"], node["velocity"])], .001, "Independent recorded rigid translation differs")
            near(pose["rotation"], [0,0,0,1], .001, "Independent recorded orientation differs")
        observations.append({"time_seconds": time, "objects": len(nodes)})
    return observations


def _node_metadata_path(path):
    return len(path) == 4 and path[0] in ("nodes", "materials", "images") and type(path[1]) is int and path[2:] == ("extras", "ontokin")


def _mapping_tail(path):
    if len(path) >= 5 and path[:1] == ("nodes",) and type(path[1]) is int and path[2:5] == ("extras", "ontokin", "source_mapping"):
        return path[5:]
    if len(path) >= 5 and path[:4] == ("extras", "ontokin", "program", "occurrences") and type(path[4]) is str:
        return path[5:]
    return None


def _source_location_path(path):
    tail = _mapping_tail(path)
    if tail in (("declaration",), ("definition",), ("generated", "input"), ("generated", "input_entry")):
        return True
    if len(path) == 6 and path[:4] == ("extras", "ontokin", "program", "collections") and path[5] in ("declaration", "input"):
        return True
    if len(path) >= 5 and path[0] == "nodes" and type(path[1]) is int and path[2:4] == ("extras", "ontokin"):
        tail = path[4:]
        if tail in (("geometry",), ("surface", "source_location")):
            return True
        if len(tail) in (4, 5) and tail[:2] == ("geometry", "texture_bindings") and type(tail[2]) is int and tail[3] == 1:
            return len(tail) == 4 or tail[4] == "mapping"
    return False


def _source_unit_path(path):
    return len(path) == 5 and path[:4] == ("extras", "ontokin", "program", "sources")


def normalized_document(glb, payload, *, control=False):
    """Normalize only independently verified, explicitly source-derived fields.

    Each changed JSON path is recorded. All other data, including all unknown
    metadata, remains in the exact comparison. Broad removal of extras or all
    source records is deliberately forbidden.
    """
    units = source_units(payload)
    revision, manifest = bundle_identity(payload)
    changes = []
    profile = "keyed-transform-0.1" if control else PROFILE
    source_hashes = {digest(u["source"].encode()): key for key, u in units.items()}
    def visit(value, path=(), parent=None):
        if isinstance(value, list):
            return [visit(v, path+(i,), value) for i,v in enumerate(value)]
        if not isinstance(value, dict):
            return value
        output = {}
        is_location = value.get("source_id") in units and (("start_byte" in value and "end_byte" in value) or ("start" in value and "end" in value))
        if is_location:
            check_location(value, units)
        for key, child in value.items():
            current, replacement, reason = path+(key,), child, None
            if key == "input_reductions" and _mapping_tail(path) == ("generated",):
                require(not control, "Legacy .14 stream acquired reduction provenance")
                check_reductions(child, units)
                changes.append({"path": list(current), "kind": "adopted_reduction_derivation", "value_sha256": sha(canonical(child))})
                continue
            if key == "input_transforms" and _mapping_tail(path) == ("generated",):
                check_transforms(child, units)
                changes.append({"path": list(current), "kind": "adopted_map_derivation", "value_sha256": sha(canonical(child))})
                continue
            if key == "manifest" and path == ("extras", "ontokin", "program"):
                require(child == manifest, "Unexpected manifest while normalizing")
                replacement, reason = "<independently_bound_program_manifest>", "program_manifest"
            elif child == revision and ((key == "program_revision" and _node_metadata_path(path)) or
                    (key == "revision" and path == ("extras", "ontokin", "program"))):
                replacement, reason = "<independently_bound_program_revision>", "program_revision"
            elif key in ("source_revision", "entry_revision") and child in source_hashes and (
                    _source_location_path(path) or _source_unit_path(path) or
                    (key == "entry_revision" and path == ("extras", "ontokin", "source"))):
                replacement, reason = "<source_revision:"+source_hashes[child]+">", "source_revision"
            elif key == "filename" and value.get("source_id") in units and (_source_location_path(path) or _source_unit_path(path)):
                require(child == units[value["source_id"]]["filename"], "Unknown source filename normalization")
                replacement, reason = "<filename:"+value["source_id"]+">", "source_filename"
            elif is_location and _source_location_path(path) and key in ("start_byte", "end_byte", "start", "end"):
                replacement, reason = "<validated_source_byte_offset>", "source_location"
            elif current in (("extras", "ontokin", "target_contract"), ("animations", 0, "extras", "ontokin", "target_contract")):
                require(child == ("ontokin.glb/0.14" if control else TARGET), "Unexpected target")
                replacement, reason = "<explicit_profile_target>", "adopted_target"
            elif current == ("extras", "ontokin", "schema_version"):
                require(child == ("0.14" if control else "0.15"), "Unexpected source schema")
                replacement, reason = "<explicit_profile_schema>", "adopted_schema"
            elif current in (("extras", "ontokin", "profile"), ("extras", "ontokin", "reach_profile", "source_profile")):
                require(child == profile, "Unexpected profile binding")
                replacement, reason = "<explicit_source_profile>", "adopted_profile"
            if reason is not None:
                changes.append({"path": list(current), "kind": reason, "value_sha256": sha(canonical(child))})
                output[key] = replacement
            else:
                output[key] = visit(child, current, value)
        return output
    return visit(glb.document), changes


def json_differences(a, b, path=()):
    if type(a) is not type(b):
        return [{"path": list(path), "actual": a, "control": b}]
    if isinstance(a, dict):
        result = []
        for key in sorted(set(a) | set(b)):
            if key not in a or key not in b:
                result.append({"path": list(path+(key,)), "actual": a.get(key), "control": b.get(key)})
            else:
                result.extend(json_differences(a[key], b[key], path+(key,)))
        return result
    if isinstance(a, list):
        if len(a) != len(b):
            return [{"path": list(path), "actual_length": len(a), "control_length": len(b)}]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in json_differences(x,y,path+(i,))]
    return [] if a == b else [{"path": list(path), "actual": a, "control": b}]


def compact_json_bytes(document):
    return json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def check_raw_framing(glb):
    """Verify every raw JSON/framing byte before a field-specific comparison."""
    raw, document = glb.data, glb.document
    text = compact_json_bytes(document)
    padded = text + b" " * (-len(text) % 4)
    json_size = struct.unpack_from("<I", raw, 12)[0]
    require(raw[20:20 + json_size] == padded,
            "Raw GLB JSON encoding/padding differs from the inherited compact UTF-8 stream")
    wanted = (struct.pack("<III", 0x46546c67, 2, len(raw)) +
              struct.pack("<II", len(padded), 0x4e4f534a) + padded +
              struct.pack("<II", len(glb.binary), 0x004e4942) + glb.binary)
    require(raw == wanted, "Complete raw GLB framing differs")
    return {"raw_json_sha256": sha(padded), "raw_json_bytes": len(padded),
            "raw_glb_sha256": sha(raw), "raw_glb_bytes": len(raw), "verified_framing": True}


def check_identity(glb, old, case, fixtures):
    framing, old_framing = check_raw_framing(glb), check_raw_framing(old)
    require(glb.binary == old.binary, "Complete BIN chunk differs from explicit .14 source control")
    for field in ("accessors", "bufferViews", "buffers"):
        require(glb.document[field] == old.document[field], "Complete accessor/buffer layout differs from explicit control: " + field)
    accessors = []
    for index in range(len(glb.document["accessors"])):
        require(glb.accessor(index) == old.accessor(index) and glb.accessor_bytes(index) == old.accessor_bytes(index), "Decoded accessor differs from explicit control")
        accessors.append({"index": index, "sha256": sha(glb.accessor_bytes(index)), "count": glb.document["accessors"][index]["count"]})
    require(glb.geometry_streams() == old.geometry_streams() and glb.animation_streams() == old.animation_streams(), "Occurrence-bound geometry/motion streams differ")
    new_json, new_changes = normalized_document(glb, case_payload(fixtures, case))
    old_json, old_changes = normalized_document(old, case_payload(fixtures, case, control=True), control=True)
    differences = json_differences(new_json, old_json)
    require(not differences, "Unpermitted control JSON differences: " + str(differences[:4]))
    new_bytes, old_bytes = compact_json_bytes(new_json), compact_json_bytes(old_json)
    require(new_bytes == old_bytes, "Unpermitted raw JSON member order or encoding difference")
    return {"complete_bin_sha256": sha(glb.binary), "complete_bin_bytes": len(glb.binary), "accessors": accessors,
        "actual_raw_framing": framing, "control_raw_framing": old_framing,
        "normalized_json_sha256": sha(new_bytes), "normalized_json_bytes": len(new_bytes),
        "actual_permitted_json_fields": new_changes, "control_permitted_json_fields": old_changes,
        "unpermitted_json_differences": [], "comparison": "full BIN, all accessor bytes, occurrence-bound streams, raw compact JSON/member order and complete framing after individually verified source/version/provenance deltas"}


def check_artifact(raw, case, fixtures, control):
    require(case["name"] in DELIVERED_CASES, "Artifact outside frozen delivered-stage scope")
    glb, old = GLB(raw, target=TARGET), GLB(control, target="ontokin.glb/0.14")
    source = check_program_metadata(glb, case, fixtures)
    baseline = check_program_metadata(old, case, fixtures, control=True)
    geometry = check_geometry(glb, case)
    images = check_images(glb, case_payload(fixtures, case))
    motion = check_motion(glb, case)
    identity = check_identity(glb, old, case, fixtures)
    return {"case": case["name"], "status": "passed", "sha256": sha(raw), "bytes": len(raw), "source": source,
            "control_source": baseline, "geometry": geometry, "images": images, "motion": motion, "identity": identity}
