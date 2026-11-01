"""Independent finite C085 readers; no production parser or runtime imports.

Derived from the unchanged C084 independent reader. The C085 changes add a
separate triple/binder delimiter reader, exact ten-field paired provenance,
the independently authored dimension/material panel and .18/.17 comparison.
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
FREEZE_COMMIT = "92b1ee60a2b9439878b7124981d2896be858937f"
FREEZE_SHA256 = "4914fd1696bc0c441736684289a4c4422c9db30ba99091dfbbbf8d1eb1c8a2a9"
TARGET = "ontokin.glb/0.18"
PROFILE = "keyed-zip-0.1"
PROTOCOL = "ontokin.agent/0.18"
STORE_SCHEMA = "ontokin.keyed-zip-program-agent-store/0.1"
DELIVERED_CASES = {"panel-task", "panel-task-repaired", "panel-identity", "panel-task-higher-budget", "panel-task-restored"}
AMENDMENTS = (
    {"id":"AMENDMENT-C085-001","commit":"b03ca75f3138ea9a94e4734eaf2c44b6c327d52c",
     "sha256":"9341d6712c9decd88ab71921a665102d0685585d102c668b1b91dec2545cd613",
     "adoption_sha256":"d994f5dff35d3bb2712859c339f9b690bcc455903d4199b351515d9cd2b147e3"},
    {"id":"AMENDMENT-C085-002","commit":"c4c756b430c6d2137986b1b780db6810300cbf71",
     "sha256":"9542c94d94e08f9c96336842b4784ede10325d46204784df9a7f1fda71f4c7ec",
     "adoption_sha256":"9a20697685aaacdf3a2bfb934be25977183033650d3a74f3e07bc371733dec23"},
)
SOURCE_IMPLEMENTATION = (
    "ontokin/reach_numeric.py", "ontokin/reach_kinematics.py", "ontokin/reach_pose.py",
    "ontokin/reach_phase.py", "ontokin/reach_runtime.py", "ontokin/reach_export.py",
    "ontokin/reach_recording_fast.py", "ontokin/reach_recording_capture.py", "ontokin/reach_transfer_bounds.py")
SOURCE_DERIVATION = (
    "docs/engineering/reach-numeric-kernel.md", "docs/engineering/reach-source-kernel.md",
    "docs/engineering/reach-coaxial-phase-bounds.md", "docs/engineering/reach-carrier-rotation-cursors.md",
    "docs/engineering/reach-recording-certified-planar.md", "docs/engineering/reach-deferred-phase-locations.md",
    "docs/engineering/reach-planning-reuse.md", "docs/engineering/reach-release-cell-envelope.md")


def load_fixtures(root=ROOT / "examples/keyed-zip"):
    root = Path(root).resolve()
    repository = root.parent.parent
    freeze_raw = ordinary_path(repository, "docs/language-design/keyed-zip-v0.1/INPUT-FREEZE.json").read_bytes()
    require(sha(freeze_raw) == FREEZE_SHA256, "Published C085 input freeze changed")
    freeze = loads(freeze_raw)
    names, size = set(), 0
    for entry in freeze["files"]:
        require(entry["path"] not in names, "Duplicate frozen path")
        path = ordinary_path(repository, entry["path"])
        raw = path.read_bytes()
        require(len(raw) == entry["size"] and sha(raw) == entry["sha256"], "Frozen bytes changed: " + entry["path"])
        require(entry["mode"] == ("100755" if path.stat().st_mode & 0o111 else "100644"), "Frozen mode changed: " + entry["path"])
        names.add(entry["path"]); size += len(raw)
    require(len(names) == freeze["file_count"] and size == freeze["total_bytes"],
            "Published freeze inventory is incomplete")
    expected_raw = ordinary_path(root, "expected.json").read_bytes()
    original_expected = loads(expected_raw)
    amendments = []
    for identity in AMENDMENTS:
        prefix = "docs/language-design/keyed-zip-v0.1/" + identity["id"]
        raw = ordinary_path(repository, prefix + ".json").read_bytes()
        adoption_raw = ordinary_path(repository, prefix + "-ADOPTION.json").read_bytes()
        require(sha(raw) == identity["sha256"] and sha(adoption_raw) == identity["adoption_sha256"],
                "Published independently reviewed amendment/adoption changed")
        amendment, adoption = loads(raw), loads(adoption_raw)
        require(amendment["frozen_input_commit"] == FREEZE_COMMIT and
                amendment["frozen_manifest_sha256"] == FREEZE_SHA256 and adoption["state"] == "adopted" and
                adoption["amendment_sha256"] == identity["sha256"], "Amendment adoption/freeze binding differs")
        amendments.append(amendment)
    comparison, correction = amendments
    require(sha(ordinary_path(repository, comparison["original_allowance_path"]).read_bytes()) == comparison["original_allowance_sha256"],
            "Original frozen comparison allowance changed")
    require(sha(expected_raw) == correction["original_expected_sha256"], "Original expected input bytes changed")
    expected = copy.deepcopy(original_expected)
    replaced = set()
    for change in correction["changes"]:
        pointer = change["json_pointer"]
        require(pointer not in replaced and change["operation"] == "replace", "Duplicate/unadopted expectation correction")
        replaced.add(pointer)
        parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
        parent = expected
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        before, after = change["before"], change["after"]
        require(parent[key] == before and set(before) == set(after) == {"source_id","source_revision","start_byte","end_byte"},
                "Expectation correction precondition/field set differs")
        require(after == dict(before, start_byte=before["start_byte"]-1, end_byte=before["end_byte"]+1),
                "Grouped-span amendment changed more than the enclosing parenthesis pair")
        case = expected["cases"][int(parts[1])]
        require(case["name"] == change["case"] and before["source_id"] == "entry", "Correction case/source differs")
        raw = file_payload(root, case["file_manifest"])["entry"]["source"].encode("utf-8")
        left, right = after["start_byte"], after["end_byte"]
        require(digest(raw) == before["source_revision"] and raw[left:left+1] == b"(" and raw[right-1:right] == b")" and
                raw[:left].rstrip().endswith(b"->") and raw[right:].lstrip().startswith(b"["),
                "Corrected grouping does not match original source bytes")
        tokens = _source_tokens(raw[left:right])
        require(_closing_delimiter(tokens, 0) == len(tokens)-1, "Corrected parentheses do not enclose one complete original expression")
        parent[key] = copy.deepcopy(after)
    effective_sha = sha((json.dumps(expected, indent=2) + "\n").encode("utf-8"))
    require(len(replaced) == 22 and effective_sha == correction["effective_expected_sha256"], "Effective expectation identity differs")
    cases = {item["name"]: item for item in expected["cases"]}
    require(len(expected["cases"]) == len(cases) == expected["case_count"] and
            set(item["expected_outcome"] for item in cases.values()) <= {"valid", "invalid"},
            "C085 source corpus inventory differs")
    require({c["name"] for c in cases.values() if c["expected_stage"] == "delivered" and c["expected_outcome"] == "valid"} == DELIVERED_CASES,
            "Frozen delivered-stage scope differs")
    workflows = loads(ordinary_path(root, "workflows.json").read_bytes())
    acceptance = loads(ordinary_path(repository, "docs/language-design/keyed-zip-v0.1/acceptance.json").read_bytes())
    require(acceptance["corpus"] == "examples/keyed-zip/expected.json" and
            acceptance["cases"] == [{"id": c["id"], "name": c["name"],
                "groups": c["tags"], "outcome": c["expected_outcome"]} for c in expected["cases"]],
            "Frozen acceptance and source inventories differ")
    require(acceptance["workflows"] == "examples/keyed-zip/workflows.json" and
            len(workflows["workflows"]) == 10 and
            {w["id"] for w in workflows["workflows"]} == {f"A{i:02d}" for i in range(1, 11)},
            "Frozen Agent inventory differs")
    result = {"root": root, "repository": repository, "freeze": freeze, "expected": expected,
              "original_expected": original_expected, "original_expected_sha256": sha(expected_raw),
              "effective_expected_sha256": effective_sha, "amendments": copy.deepcopy(list(AMENDMENTS)),
              "comparison_amendment": comparison,
              "cases": cases, "workflows": workflows, "acceptance": acceptance}
    for case in cases.values():
        require(bundle_identity(case_payload(result, case)) == (case["program_revision"], case["canonical_manifest"]),
                "Frozen program identity cannot be independently reproduced: " + case["name"])
        if case["expected_outcome"] == "valid":
            control = case["explicit_c084_control"]
            require(bundle_identity(case_payload(result, case, control=True)) == (control["program_revision"], control["canonical_manifest"]),
                    "Frozen explicit control identity differs: " + case["name"])
    require(sum(len(bundle["named_source_cases"]) for bundle in comparison["bundles"]) == 5 and len(comparison["bundles"]) == 3,
            "Primary-origin amendment bundle inventory differs")
    for bundle in comparison["bundles"]:
        require(len(bundle["occurrences"]) == 4, "Primary-origin amendment occurrence inventory differs")
        for name in bundle["named_source_cases"]:
            case = cases[name]
            require(case["program_revision"] == bundle["actual_program_revision"] and
                    case["explicit_c084_control"]["program_revision"] == bundle["control_program_revision"],
                    "Primary-origin amendment names another original source/control pair")
            for occurrence in bundle["occurrences"]:
                for is_control, side in ((False, "actual"), (True, "control")):
                    units = source_units(case_payload(result, case, control=is_control))
                    location = primary_panel_entry(case, result, occurrence["key"], control=is_control)
                    merge_location(occurrence[side + "_location"], location, units)
    return result


def case_payload(fixtures, case, *, control=False):
    manifest = case["explicit_c084_control"]["file_manifest"] if control else case["file_manifest"]
    return file_payload(fixtures["root"], manifest)


def canonical_probe_type(display):
    # These two documented presentation aliases occur in the frozen corpus.
    # No dimensional or generic leaf type is otherwise weakened or stripped.
    return {"Keyed<Quantity[m]>": "Keyed<Length>", "Quantity[m]": "Length",
            "Keyed<Quantity[m^2]>": "Keyed<Area>", "Quantity[m^2]": "Area",
            "Keyed<Point3>": "Keyed<Point3<Length>>", "Point3": "Point3<Length>"}.get(display, display)


def delivered_by_revision(fixtures):
    selected = [case for case in fixtures["cases"].values()
                if case["expected_outcome"] == "valid" and case["expected_stage"] == "delivered"]
    require(len(selected) == 5 and {c["name"] for c in selected} == DELIVERED_CASES,
            "Delivered named source inventory is incomplete")
    result = {}
    for case in selected:
        previous = result.get(case["program_revision"])
        if previous is not None:
            # C084 deliberately names the same exact base panel bundle three times. Bind
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
    if "file" in location:
        require(location["file"] == unit["filename"], "Source span file differs")
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


def original_keyed_entries(units):
    """Recover complete keyed-entry spans from original token delimiters."""
    result={}
    for source_id,unit in units.items():
        raw=unit["source"].encode("utf-8");tokens=_source_tokens(raw)
        for i,token in enumerate(tokens[:-1]):
            if token[0]!=b"keyed" or tokens[i+1][0]!=b"<":
                continue
            types,opening=_type_arguments(tokens,i,b"keyed")
            require(len(types)==1 and tokens[opening][0]==b"{", "Malformed original keyed literal")
            closing=_closing_delimiter(tokens,opening)
            boundaries=[opening]+_top_level_commas(tokens,opening+1,closing)+[closing]
            for left,right in zip(boundaries,boundaries[1:]):
                start=left+1
                if start==right:
                    continue
                require(start+2<right and tokens[start][0].startswith(b'"') and tokens[start+1][0]==b":",
                        "Malformed original keyed entry")
                key=loads(tokens[start][0])
                location={"source_id":source_id,"source_revision":digest(raw),
                          "start_byte":tokens[start][1],"end_byte":tokens[right-1][2]}
                result[_location_identity(location)]={"key":key,"location":location}
    return result


def panel_sources(case, fixtures, *, control=False):
    """Read independent dimension/finish merges and both original contributors."""
    units=source_units(case_payload(fixtures,case,control=control))
    entries=original_keyed_entries(units)
    sources={}
    for role,source_id,element_type in (
            ("dimensions","package:fixture.pair-dimensions@1.0.0","Length"),
            ("finishes","package:fixture.pair-finishes@1.0.0","SurfaceMaterial")):
        locations=intrinsic_locations({source_id:units[source_id]},b"merge_keyed")
        require(len(locations)==1,"Panel attribute library merge inventory differs")
        expression=locations[0];shape=merge_source_shape(expression,units)
        require(shape["element_type"]==element_type,"Panel attribute type differs")
        origin={"expression":expression,**shape["parts"],"element_type":element_type,"input_side":"both"}
        contributors={}
        for side in ("left","right"):
            operand=origin[side]
            matches=[entry for entry in entries.values() if entry["location"]["source_id"]==source_id and
                     operand["start_byte"]<=entry["location"]["start_byte"]<entry["location"]["end_byte"]<=operand["end_byte"]]
            require(len(matches)==1,"Each independent attribute merge operand has exactly one original keyed entry")
            item=matches[0];contributors[item["key"]]={"entry":item["location"],"side":side}
        require(set(contributors)=={"left","right"},"Panel attribute merge lost exact stable keys")
        sources[role]={"record":origin,"contributors":contributors}
    if not control:
        require(len(case["expected"]["zip_provenance"])==1,"Panel has exactly one authored zip expression")
        sources["zip"]=case["expected"]["zip_provenance"][0]
        check_zips(enriched_zip_records([sources["zip"]],units),units,aggregate=True)
    return sources


def panel_zip_records(sources, key=None):
    record=copy.deepcopy(sources["zip"])
    if key is not None:
        record.update(key=key,left_entry=sources["dimensions"]["contributors"][key]["entry"],
                      right_entry=sources["finishes"]["contributors"][key]["entry"])
    return [record]


def panel_merge_records(sources, *, key=None, aggregate=True):
    result=[]
    if aggregate:
        result=[sources[role]["record"] for role in ("dimensions","finishes")]
    if key is not None:
        result += [with_merge_side(sources[role]["record"],sources[role]["contributors"][key]["side"])
                   for role in ("dimensions","finishes")]
    return result


def panel_reduction(case, fixtures, *, control=False):
    units = source_units(case_payload(fixtures, case, control=control))
    records = intrinsic_locations(units, b"reduce_keyed")
    require(len(records) == 1, "Frozen panel has an ambiguous selection reduction")
    shape = reduction_source_shape(records[0], units)
    return {"expression": records[0], **shape["parts"], "input_element_type": "Length", "accumulator_type": "Length"}


def check_transforms(records, units, *, expected=None, require_nonempty=True):
    require(isinstance(records, list) and (not require_nonempty or records), "Missing ordered map derivation records")
    count = 0
    for record in records:
        base_fields = {"expression", "body", "input", "input_element_type", "output_element_type"}
        require(isinstance(record, dict) and set(record) in (base_fields, base_fields | {"key", "input_entry"}),
                "Transform projection has an unadopted shape")
        expression = check_location(record["expression"], units)
        require(b"map_keyed" in expression, "Derived expression does not identify the authored map")
        check_location(record["body"], units); check_location(record["input"], units)
        for name in ("body", "input"):
            location, outer = record[name], record["expression"]
            require(location["source_id"] == outer["source_id"] and
                    outer["start_byte"] <= location["start_byte"] < location["end_byte"] <= outer["end_byte"],
                    "Map body/input lies outside its exact expression")
        require(all(type(record[k]) is str and record[k] for k in ("input_element_type", "output_element_type")), "Missing map element types")
        authored = intrinsic_source_shape(record["expression"], units, b"map_keyed")
        for part in ("input", "body"):
            same_location(record[part], authored["parts"][part], units)
        require(canonical_probe_type(record["output_element_type"]) == authored["element_type"],
                "Map output type differs from its explicit source type")
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


def _type_arguments(tokens, name_index, name):
    """Read generic separators independently of expression commas."""
    require(tokens[name_index][0] == name and tokens[name_index + 1][0] == b"<",
            "Source expression lost explicit generic arguments")
    depth, start, values, cursor = 1, name_index + 2, [], name_index + 2
    while cursor < len(tokens):
        token = tokens[cursor][0]
        if token == b"<":
            depth += 1
            require(depth <= 64, "Independent generic depth exceeds its bound")
        elif token == b">":
            depth -= 1
            if depth == 0:
                require(start < cursor, "Empty explicit type argument")
                values.append(b"".join(t[0] for t in tokens[start:cursor]).decode("ascii"))
                return values, cursor + 1
        elif token == b"," and depth == 1:
            require(start < cursor, "Empty explicit type argument")
            values.append(b"".join(t[0] for t in tokens[start:cursor]).decode("ascii"))
            start = cursor + 1
        cursor += 1
    raise ReferenceError("Unterminated explicit generic arguments")


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
        if (token in (b"zip_keyed", b"map_keyed", b"reduce_keyed", b"filter_keyed", b"merge_keyed", b"keyed")
                and index + 1 < end and tokens[index + 1][0] == b"<"):
            _, after = _type_arguments(tokens, index, token)
            require(after < end, "Source type arguments cross expression boundary")
            index = after - 1
        elif token in (b"(", b"[", b"{"):
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


def intrinsic_locations(units, operation):
    """Inventory authored generic calls without running the product parser."""
    locations = []
    for source_id, unit in units.items():
        raw = unit["source"].encode("utf-8")
        tokens = _source_tokens(raw)
        for index, token in enumerate(tokens[:-1]):
            if token[0] != operation or tokens[index + 1][0] != b"<":
                continue
            types, opening = _type_arguments(tokens, index, operation)
            require(len(types) == (3 if operation == b"zip_keyed" else 1),
                    "Intrinsic generic arity differs")
            if opening >= len(tokens) or tokens[opening][0] != b"(":
                continue
            closing = _closing_delimiter(tokens, opening)
            locations.append({"source_id": source_id, "source_revision": digest(raw),
                              "start_byte": token[1], "end_byte": tokens[closing][2]})
    return locations


def intrinsic_source_shape(location, units, operation=b"filter_keyed"):
    """Read exact map/filter argument spans and explicit type delimiters."""
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Intrinsic source span includes non-expression boundary bytes")
    start, stop = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == stop - 1:
        start += 1; stop -= 1
    element_type, opening = _generic_type(tokens, start, operation)
    closing = _closing_delimiter(tokens, opening)
    require(closing == stop - 1 and tokens[opening][0] == b"(",
            "Intrinsic source span is not the complete authored call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 1, "Intrinsic source lost its exact two arguments")
    comma = commas[0]
    binder_start = comma + 1
    binder_end = _closing_delimiter(tokens, binder_start)
    require(tokens[binder_start][0] == b"(" and binder_end + 2 < closing and tokens[binder_end + 1][0] == b"->",
            "Intrinsic source lost its binder/body delimiter")
    binders = [t[0] for t in tokens[binder_start + 1:binder_end]]
    require(len(binders) == 3 and binders[1] == b"," and
            all(re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", binders[i]) for i in (0, 2)),
            "Intrinsic source does not have its exact two binders")
    name = "predicate" if operation == b"filter_keyed" else "body"
    ranges = {"input": (opening + 1, comma), name: (binder_end + 2, closing)}
    base, source_id = location.get("start_byte", location.get("start")), location["source_id"]
    parts = {}
    for part, (start, end) in ranges.items():
        require(start < end, "Intrinsic source has an empty " + part)
        parts[part] = {"source_id": source_id, "source_revision": digest(units[source_id]["source"].encode("utf-8")),
                       "start_byte": base + tokens[start][1], "end_byte": base + tokens[end - 1][2]}
    return {"parts": parts, "element_type": canonical_probe_type(element_type)}


def filter_source_shape(location, units):
    unit = units[location["source_id"]]
    require(location.get("source_revision") == digest(unit["source"].encode("utf-8")),
            "Filter expression lost original source revision binding")
    pairs = (("0.16", "keyed-filter-0.1"), ("0.17", "keyed-merge-0.1"), ("0.18", "keyed-zip-0.1"))
    require(any(re.search(r'\bontokin\s+"' + re.escape(version) + r'"\s*;', unit["source"]) and
                re.search(r'\bprofile\s+"' + re.escape(profile) + r'"\s*;', unit["source"])
                for version, profile in pairs), "Filter origin has an incompatible declaring-unit contract")
    return intrinsic_source_shape(location, units)

def check_filters(records, units, *, expected=None, require_nonempty=True):
    """Validate closed read-only records and original UTF-8 expression identity."""
    require(isinstance(records, list) and (records or not require_nonempty), "Missing ordered filter derivation records")
    fields = {"expression", "input", "predicate", "element_type"}
    seen = set()
    for index, record in enumerate(records):
        require(isinstance(record, dict) and set(record) == fields,
                "Filter projection has an unadopted shape or invented identity")
        authored = filter_source_shape(record["expression"], units)
        for part in ("input", "predicate"):
            same_location(record[part], authored["parts"][part], units)
        require(record["element_type"] == authored["element_type"],
                "Filter element type differs from its canonical resolved explicit source type")
        identity = _location_identity(record["expression"])
        require(identity not in seen, "Duplicate filter source derivation")
        seen.add(identity)
        for earlier in records[:index]:
            a, b = earlier["expression"], record["expression"]
            require(not (a["source_id"] == b["source_id"] and
                    a["start_byte"] < b["start_byte"] and b["end_byte"] <= a["end_byte"]),
                    "Nested filter provenance is not in evaluation order")
    if expected is not None:
        wanted_records = expected if isinstance(expected, list) else [expected]
        for wanted in wanted_records:
            matches = [record for record in records if _location_identity(record["expression"]) == _location_identity(wanted["expression"])]
            require(len(matches) == 1, "Frozen filter expression absent or duplicated")
            for name in ("expression", "input", "predicate"):
                same_location(matches[0][name], wanted[name], units)
            require(matches[0]["element_type"] == wanted["element_type"], "Frozen filter type differs")
    return len(records)


def require_filter_order(records, expected, units):
    check_filters(records, units, require_nonempty=bool(expected))
    require([_location_identity(record["expression"]) for record in records] ==
            [_location_identity(location) for location in expected],
            "Filter derivations differ from frozen actual evaluation order")
    require_expression_origins(records, expected, units, "filter")


def diagnostic_anchor(receipt, case, units):
    """Check adopted new token diagnostics and inherited containment anchors."""
    wanted = case.get("diagnostic_anchor")
    candidates = [node for _, node in walk(receipt)
                  if isinstance(node, dict) and node.get("code") == case["expected_code"]]
    require(candidates, "Expected diagnostic has no raw source record")
    if wanted is None:
        return None
    check_location(wanted, units)
    matches = []
    for candidate in candidates:
        primary = candidate.get("primary")
        if not isinstance(primary, dict):
            continue
        check_location(primary, units)
        if case.get("diagnostic_anchor_mode") == "contains_token":
            selected = (primary.get("source_id") == wanted["source_id"] and
                        primary.get("source_revision") == wanted["source_revision"] and
                        primary["start_byte"] <= wanted["start_byte"] < wanted["end_byte"] <= primary["end_byte"])
        else:
            selected = all(primary.get(key) == value for key, value in wanted.items())
        if selected:
            matches.append(candidate)
    require(matches, "Refusal primary span differs from its frozen exact/containment contract")
    current = matches[0]
    if case.get("diagnostic_anchor_mode") == "exact_token":
        for field in ("category", "phase", "rule_ids", "details"):
            require(current.get(field) == case["diagnostic_" + field], "New merge diagnostic " + field + " differs")
        related = current.get("related")
        expected_related = case.get("diagnostic_related", [])
        require(isinstance(related, list) and len(related) == len(expected_related),
                "New merge diagnostic related-location cardinality differs")
        for actual, expected in zip(related, expected_related):
            check_location(actual, units)
            require(all(actual.get(key) == value for key, value in expected.items()),
                    "New merge diagnostic related first-token span differs")
        for location in [current["primary"], *related]:
            require(set(location) == {"source_id", "source_revision", "file", "start_byte", "end_byte", "element_id"}
                    and location["file"] == units[location["source_id"]]["filename"],
                    "New merge diagnostic changed the inherited .2 source-location shape")
    return {"mode": case.get("diagnostic_anchor_mode", "exact_token"), "primary": current["primary"],
            "related": current.get("related", []), "details": current.get("details", {}),
            "category": current.get("category"), "phase": current.get("phase"), "rule_ids": current.get("rule_ids")}

def nominal_definition_id(locator, units):
    """Resolve a frozen source-qualified locator to inherited .2 nominal identity.

    OK-LANG-002 section 3.3 separates source ID/version from the stable nominal
    package/module/key ID. Neither form may be silently used in place of the
    other: bind the exact unit pin and authored declaration before translating.
    """
    require(isinstance(locator, list) and len(locator) == 4 and locator[2] == "definitions" and locator[0] in units,
            "Frozen called-definition locator has no exact source unit")
    unit = units[locator[0]]
    raw = unit["source"].encode("utf-8")
    module = re.search(rb'\bmodule\s+[A-Za-z_][A-Za-z_0-9]*\s*@\s*("(?:[^"\\]|\\.)*")', raw)
    require(module is not None and loads(module[1]) == locator[1], "Called-definition locator names another module key")
    declaration = re.search(rb'\bfn\s+[A-Za-z_][A-Za-z_0-9]*\s*@\s*' + re.escape(canonical(locator[3])) + rb'\s*\(', raw)
    require(declaration is not None, "Called-definition locator names an absent authored function key")
    if locator[0] == "entry":
        require(unit.get("package_id") is None and unit.get("version") is None, "Entry definition acquired a package pin")
        prefix = ["entry"]
    else:
        require(locator[0] == "package:" + unit["package_id"] + "@" + unit["version"], "Called-definition source pin differs")
        prefix = ["package", unit["package_id"]]
    return tuple(prefix + locator[1:])


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
    start, stop = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == stop - 1:
        start += 1; stop -= 1
    accumulator, opening = _generic_type(tokens, start, b"reduce_keyed")
    closing = _closing_delimiter(tokens, opening)
    require(closing == stop - 1 and tokens[opening][0] == b"(",
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
    if input_tokens[0][0] == b"zip_keyed":
        types, _ = _type_arguments(input_tokens, 0, b"zip_keyed")
        require(len(types) == 3, "Reduction input zip lost exact type arity")
        input_type = types[2]
    elif input_tokens[0][0] in (b"keyed", b"map_keyed", b"filter_keyed", b"merge_keyed"):
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
        if name in ("derived_transforms", "derived_reductions", "derived_filters", "derived_merges", "derived_zips", "input_entry"):
            continue
        if location and name in ("source_revision", "filename", "start", "end", "start_byte", "end_byte"):
            continue
        result[name] = semantic_value(child, units)
    return result


def check_keyed_membership(value, keys, *, scalars=None):
    require(type(value.get("type")) is str and value["type"].startswith("Keyed<") and isinstance(value.get("value"), list),
            "Expected a typed keyed inspection value")
    entries = value["value"]
    actual = [entry.get("key") for entry in entries]
    require(actual == sorted(keys) and len(actual) == len(set(actual)), "Exact surviving key membership/order differs")
    require(all(type(key) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", key) for key in actual),
            "Surviving stable key violates inherited identity grammar")
    leaf_type = canonical_probe_type(value["type"][6:-1])
    for entry in entries:
        require(set(entry) == {"key", "value"} and isinstance(entry["value"], dict), "Keyed entry projection has an invented identity")
        require(canonical_probe_type(entry["value"]["type"]) == leaf_type, "Surviving leaf type differs from its keyed type")
        if scalars is not None:
            got, wanted = entry["value"]["value"], scalars[entry["key"]]
            require(got == wanted and (type(got) is type(wanted) or
                    leaf_type not in ("Int", "Bool", "String") and type(got) in (int, float) and type(wanted) in (int, float)),
                    "Surviving scalar leaf value differs")
    return len(entries)


def no_filter_origins(value):
    require(not any(isinstance(node, dict) and ("derived_filters" in node or "input_filters" in node)
                    for _, node in walk(value)), "Shared original/plain value was contaminated by filter provenance")


def merge_location(actual, expected, units):
    """Every runtime merge location has exactly the adopted five fields."""
    enriched = {**expected, "filename": units[expected["source_id"]]["filename"]}
    require(set(enriched) == {"source_id", "source_revision", "filename", "start_byte", "end_byte"},
            "Independent merge location has an unexpected authored shape")
    check_location(actual, units)
    require(actual == enriched, "Merge provenance location differs from its complete original source expression")


def merge_source_shape(location, units):
    """Split two original operands, preserving complete grouping parentheses."""
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Merge expression span includes whitespace/comment boundary bytes")
    start, end = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == end - 1:
        start += 1; end -= 1
    element_type, opening = _generic_type(tokens, start, b"merge_keyed")
    closing = _closing_delimiter(tokens, opening)
    require(closing == end - 1, "Merge source span is not a complete grouped call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 1, "Merge source does not contain its exact two operands")
    unit = units[location["source_id"]]
    require(any(re.search(r'\bontokin\s+"' + re.escape(version) + r'"\s*;', unit["source"]) and
                re.search(r'\bprofile\s+"' + re.escape(profile) + r'"\s*;', unit["source"])
                for version, profile in (("0.17", "keyed-merge-0.1"), ("0.18", "keyed-zip-0.1"))),
            "Intrinsic merge provenance belongs to another declaring-unit version")
    base = location["start_byte"]
    parts = {}
    for name, (first, stop) in {"left": (opening + 1, commas[0]), "right": (commas[0] + 1, closing)}.items():
        require(first < stop, "Merge source contains an empty operand")
        parts[name] = {"source_id": location["source_id"], "source_revision": digest(unit["source"].encode()),
                       "start_byte": base + tokens[first][1], "end_byte": base + tokens[stop - 1][2]}
    return {"parts": parts, "element_type": canonical_probe_type(element_type)}


def check_merges(records, units, *, expected=None, require_nonempty=True, exact=False):
    require(isinstance(records, list) and (records or not require_nonempty), "Missing ordered merge derivation records")
    fields = {"expression", "left", "right", "element_type", "input_side"}
    seen = set()
    for record in records:
        require(isinstance(record, dict) and set(record) == fields,
                "Merge projection contains unadopted fields or invented identity")
        authored = merge_source_shape(record["expression"], units)
        for part in ("expression", "left", "right"):
            wanted = record[part] if part == "expression" else authored["parts"][part]
            merge_location(record[part], wanted, units)
        require(record["element_type"] == authored["element_type"], "Merge element type differs from its canonical explicit source type")
        require(record["input_side"] in ("both", "left", "right"), "Merge input side is outside the adopted vocabulary")
        identity = canonical(record)
        require(identity not in seen, "Duplicate exact merge provenance record")
        seen.add(identity)
    if expected is not None:
        enriched = [{**wanted, **{part: {**wanted[part], "filename": units[wanted[part]["source_id"]]["filename"]}
                                 for part in ("expression", "left", "right")}} for wanted in expected]
        if exact:
            require(records == enriched, "Exact merge provenance sequence or contribution sides differ")
        else:
            require(all(record in records for record in enriched), "Required authored merge record is absent")
    return len(records)


def require_merge_order(records, expected, units):
    check_merges(records, units, require_nonempty=bool(expected))
    order = []
    for record in records:
        identity = _location_identity(record["expression"])
        if identity not in order:
            order.append(identity)
    require(order == [_location_identity(location) for location in expected],
            "Merge derivations differ from frozen actual evaluation order")


def no_merge_origins(value):
    require(not any(isinstance(node, dict) and ("derived_merges" in node or "input_merges" in node)
                    for _, node in walk(value)), "Shared original/plain value was contaminated by merge provenance")


def with_merge_side(record, side):
    return {**record, "input_side": side}


ZIP_FIELDS = {"expression", "left", "right", "body", "left_element_type",
              "right_element_type", "output_element_type", "key", "left_entry", "right_entry"}
ZIP_LOCATIONS = ("expression", "left", "right", "body", "left_entry", "right_entry")


def zip_source_shape(location, units):
    """Read a full original triple/binder call, without parsing or executing DSL."""
    raw = check_location(location, units)
    tokens = _source_tokens(raw)
    require(tokens and tokens[0][1] == 0 and tokens[-1][2] == len(raw),
            "Zip source span has non-expression boundary bytes")
    start, stop = 0, len(tokens)
    while tokens[start][0] == b"(" and _closing_delimiter(tokens, start) == stop - 1:
        start += 1; stop -= 1
    types, opening = _type_arguments(tokens, start, b"zip_keyed")
    require(len(types) == 3 and tokens[opening][0] == b"(", "Zip lost exactly T,U,V or call delimiter")
    closing = _closing_delimiter(tokens, opening)
    require(closing == stop - 1, "Zip source does not span its complete call")
    commas = _top_level_commas(tokens, opening + 1, closing)
    require(len(commas) == 2, "Zip does not contain exact left/right/binder-body arguments")
    first, second = commas
    binder_start = second + 1
    binder_end = _closing_delimiter(tokens, binder_start)
    require(tokens[binder_start][0] == b"(" and binder_end + 2 < closing and tokens[binder_end + 1][0] == b"->",
            "Zip lost binder/body delimiter")
    binders = [t[0] for t in tokens[binder_start + 1:binder_end]]
    require(len(binders) == 5 and binders[1] == binders[3] == b"," and
            all(re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", binders[i]) for i in (0,2,4)) and
            len({binders[i] for i in (0,2,4)}) == 3, "Zip does not have three distinct named binders")
    unit = units[location["source_id"]]
    require(re.search(r'\bontokin\s+"0\.18"\s*;', unit["source"]) and
            re.search(r'\bprofile\s+"keyed-zip-0\.1"\s*;', unit["source"]),
            "Zip provenance belongs to another declaring-unit contract")
    parts = {}
    for name, (left, right) in {"left":(opening+1,first),"right":(first+1,second),"body":(binder_end+2,closing)}.items():
        require(left < right, "Zip has an empty operand or body")
        parts[name] = {"source_id":location["source_id"], "source_revision":digest(unit["source"].encode()),
                       "start_byte":location["start_byte"]+tokens[left][1],
                       "end_byte":location["start_byte"]+tokens[right-1][2]}
    return {"parts":parts, "left_element_type":canonical_probe_type(types[0]),
            "right_element_type":canonical_probe_type(types[1]), "output_element_type":canonical_probe_type(types[2]),
            "binders":[binders[i].decode('ascii') for i in (0,2,4)]}


def enriched_zip_records(records, units):
    result=[]
    for record in records:
        current=copy.deepcopy(record)
        for field in ZIP_LOCATIONS:
            value=current[field]
            if value is not None:
                current[field] = {**value,"filename":units[value["source_id"]]["filename"]}
        result.append(current)
    return result


def check_zips(records, units, *, expected=None, require_nonempty=True, exact=False, aggregate=False):
    """Require exact original five-field locations and ten-field zip records."""
    require(isinstance(records,list) and (records or not require_nonempty), "Missing ordered zip provenance")
    seen=set()
    original_entries=original_keyed_entries(units) if any(isinstance(r,dict) and r.get("key") is not None for r in records) else {}
    for record in records:
        require(isinstance(record,dict) and set(record)==ZIP_FIELDS, "Zip record has missing or unadopted fields")
        shape=zip_source_shape(record["expression"],units)
        for part in ("expression","left","right","body"):
            wanted=record[part] if part=="expression" else shape["parts"][part]
            merge_location(record[part],wanted,units)
        for part in ("left_element_type","right_element_type","output_element_type"):
            require(record[part]==shape[part], "Zip exact canonical boundary type differs from authored explicit type")
        key=record["key"]
        require(key is None or type(key) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}",key),
                "Zip paired key violates the original stable-key grammar")
        if key is None or aggregate:
            require(key is None and record["left_entry"] is None and record["right_entry"] is None,
                    "Keyed aggregate invented a paired contributor")
        else:
            for field in ("left_entry","right_entry"):
                entry=record[field]
                if entry is None:
                    continue
                merge_location(entry,entry,units)
                raw=check_location(entry,units)
                tokens=_source_tokens(raw)
                require(tokens and tokens[0][1]==0 and tokens[-1][2]==len(raw) and
                        tokens[0][0]==canonical(key) and len(tokens)>=3 and tokens[1][0]==b":" and tokens[-1][0]!=b",",
                        "Zip contributor is not the full original matching keyed entry")
                original=original_entries.get(_location_identity(entry))
                require(original is not None and original["key"]==key,
                        "Zip contributor span abbreviates or crosses the complete original keyed entry")
        identity=canonical(record)
        require(identity not in seen, "Duplicate exact zip provenance record")
        seen.add(identity)
    if expected is not None:
        wanted=enriched_zip_records(expected,units)
        require(records==wanted if exact else all(record in records for record in wanted),
                "Exact frozen zip provenance sequence or original pair differs")
    return len(records)


def require_zip_order(records, expected, units):
    check_zips(records,units,require_nonempty=bool(expected))
    order=[]
    for record in records:
        identity=_location_identity(record["expression"])
        if identity not in order:
            order.append(identity)
    require(order==[_location_identity(location) for location in expected],
            "Zip origin order differs from independently authored actual evaluation order")


def no_zip_origins(value):
    require(not any(isinstance(node,dict) and ("derived_zips" in node or "input_zips" in node)
                    for _,node in walk(value)), "Original/plain/.17 value acquired zip provenance")


def check_zip_leaf_provenance(value, units, expected):
    """Check normalized collection and exact retained leaf contributors separately."""
    aggregate=value.get("derived_zips",[])
    check_zips(aggregate,units,require_nonempty=bool(aggregate),aggregate=True)
    if "aggregate_zip_records_exact" in expected:
        wanted=expected["aggregate_zip_records_exact"]
        check_zips(aggregate,units,expected=wanted,exact=True,require_nonempty=bool(wanted),aggregate=True)
    count=0
    for entry in value["value"]:
        key, leaf=entry["key"],entry["value"]
        records=leaf.get("derived_zips",[])
        check_zips(records,units,require_nonempty=bool(records))
        wanted=expected.get("stored_leaf_zips_exact",{}).get(key)
        if wanted is None and key in expected.get("paired_entry_zip_records_exact",{}):
            wanted=[expected["paired_entry_zip_records_exact"][key]]
        if wanted is not None:
            check_zips(records,units,expected=wanted,exact=True,require_nonempty=bool(wanted))
        count+=1
    return count


def check_keyed_leaf_provenance(value, units, *, expected=None, required=None, require_leaf=True, entry_sides=None):
    records = value.get("derived_merges", [])
    check_merges(records, units, expected=expected)
    required = required if required is not None else [record["expression"] for record in records]
    checked = 0
    for entry in value["value"]:
        leaf_records = entry["value"].get("derived_merges", [])
        if require_leaf:
            check_merges(leaf_records, units)
            require_expression_origins(leaf_records, required, units, "contributing-entry merge")
        elif leaf_records:
            check_merges(leaf_records, units)
        if entry_sides is not None:
            require(expected and len(expected) == 1, "Explicit entry-side fixture must have exactly one merge")
            check_merges(leaf_records, units, expected=[with_merge_side(expected[0], entry_sides[entry["key"]])], exact=True)
        checked += 1
    return checked

def paired_panel_merges(sources, *, control=False, key=None, stored_leaf=False):
    """Derive inherited order from fixed source reads, never artifact metadata."""
    dims,finish=sources["dimensions"],sources["finishes"]
    if control:
        if stored_leaf:
            return [finish["record"],with_merge_side(finish["record"],finish["contributors"][key]["side"])]
        return [finish["record"]]+[with_merge_side(finish["record"],finish["contributors"][k]["side"]) for k in ("left","right")]
    if stored_leaf:
        return panel_merge_records(sources,key=key,aggregate=False)
    # Left and right aggregate admission, then the width condition and selected
    # material body reads for each canonical pair. Existing merge records are
    # not subject to the new zip-family aggregate normalization.
    return panel_merge_records(sources)+[record for k in ("left","right")
                                        for record in panel_merge_records(sources,key=k,aggregate=False)]


def primary_panel_entry(case, fixtures, key, *, control=False):
    sources=panel_sources(case,fixtures,control=control)
    if not control:
        return sources["dimensions"]["contributors"][key]["entry"]
    units=source_units(case_payload(fixtures,case,control=True))
    source_id="package:fixture.pair-panels@1.0.0";raw=units[source_id]["source"].encode()
    match=re.search(rb'public\s+derive\s+paired\b[^=]*=\s*(keyed<SurfaceMaterial>[^;]+);',raw)
    require(match is not None,"Explicit control lost independently authored paired literal")
    entries=[entry for entry in original_keyed_entries(units).values() if entry["key"]==key and
             entry["location"]["source_id"]==source_id and
             match.start(1)<=entry["location"]["start_byte"]<entry["location"]["end_byte"]<=match.end(1)]
    require(len(entries)==1,"Control primary entry is ambiguous or absent")
    return entries[0]["location"]


def check_panel_values(items, case, fixtures, units, *, control=False):
    """Read independent dimensions, finishes, exact paired colors and provenance."""
    expected,checks=case["expected"],0
    sources=panel_sources(case,fixtures,control=control)
    for owner,wanted in expected["selected_total_m"].items():
        value=inspect_member(items,owner,"selected_total")
        require(value["type"]=="Length" and value["value"]==wanted and value.get("status")=="resolved" and not value.get("stale"),
                "Panel total differs from frozen independent dimensions")
        check_reductions(value.get("derived_reductions"),units,expected=panel_reduction(case,fixtures,control=control))
        dimension=sources["dimensions"]
        reduction_merges=[dimension["record"]]+[with_merge_side(dimension["record"],dimension["contributors"][key]["side"]) for key in ("left","right")]
        check_merges(value.get("derived_merges"),units,expected=reduction_merges,exact=True)
        no_zip_origins(value)
        checks+=1
    for owner,widths in expected["widths_m"].items():
        dimensions=inspect_member(items,owner,"dimensions")
        require(dimensions["type"]=="Keyed<Length>","Panel dimensions have another type")
        checks+=check_keyed_membership(dimensions,sorted(widths),scalars=widths)
        check_merges(dimensions.get("derived_merges"),units,expected=[sources["dimensions"]["record"]],exact=True)
        for entry in dimensions["value"]:
            key=entry["key"];origin=sources["dimensions"]
            check_merges(entry["value"].get("derived_merges"),units,
                         expected=[with_merge_side(origin["record"],origin["contributors"][key]["side"])],exact=True)
        no_zip_origins(dimensions)
        finishes=inspect_member(items,owner,"finishes")
        paired=inspect_member(items,owner,"paired")
        for value in (finishes,paired):
            require(value["type"]=="Keyed<SurfaceMaterial>","Paired panel materials have another type")
            checks+=check_keyed_membership(value,sorted(widths))
            for entry in value["value"]:
                key=entry["key"];panel=next(p for p in expected["panels"]if p["owner"]==owner and p["input_key"]==key)
                mat=panel["materials"]["side"]
                require(entry["value"]["value"]==[mat["color"],mat["metallic"],mat["roughness"]],
                        "Pair correspondence changed independently authored material factors")
        no_zip_origins(finishes)
        check_merges(finishes.get("derived_merges"),units,expected=[sources["finishes"]["record"]],exact=True)
        check_merges(paired.get("derived_merges"),units,expected=paired_panel_merges(sources,control=control),exact=True)
        for entry in paired["value"]:
            key=entry["key"]
            check_merges(entry["value"].get("derived_merges"),units,
                         expected=paired_panel_merges(sources,control=control,key=key,stored_leaf=True),exact=True)
            if not control:
                check_zips(entry["value"].get("derived_zips"),units,expected=panel_zip_records(sources,key),exact=True)
        if control:
            no_zip_origins(paired)
        else:
            check_zips(paired.get("derived_zips"),units,expected=panel_zip_records(sources),exact=True,aggregate=True)
        for member in ("mounts","left_width","warm_finish"):
            no_zip_origins(inspect_member(items,owner,member))
    return checks

def check_generated_shapes(items, control_items, case, units, old_units):
    """Check generated identities, immutable values and exact selected origins."""
    expected=case.get("expected") or {}
    objects={i["path"]:i for i in items if i.get("kind")=="object"}
    controls={i["path"]:i for i in control_items if i.get("kind")=="object"}
    require(len(objects)==sum(i.get("kind")=="object"for i in items),"Repeated source occurrence")
    generated={p:i for p,i in objects.items()if i.get("source",{}).get("generated")}
    old_generated={p:i for p,i in controls.items()if i.get("source",{}).get("generated")}
    wanted_paths=expected["generated_paths"]
    require(set(generated)==set(old_generated)==set(wanted_paths),"Generated occurrence membership differs")
    count=0
    for path in wanted_paths:
        item,previous=generated[path],old_generated[path]
        source=item["source"]["generated"];key=path.rsplit('["',1)[1][:-2]
        radius=case["probe"]["scalar_values"][key]
        require(item.get("element_id")==previous.get("element_id") and source.get("input_key")==key and
                source.get("unique_declaration_span")is False,"Generated key/occurrence identity differs")
        raw=check_location(source.get("input_entry_span"),units)
        require(re.match(re.escape(canonical(key))+rb"\s*:",raw)is not None,"Generated original primary entry key differs")
        value=inspect_member(items,path,"size");prior=inspect_member(control_items,path,"size")
        require(value["type"]==prior["type"]=="Length" and value["value"]==prior["value"]==radius,
                "Generated sphere size differs from independently authored source")
        require(value.get("status")=="resolved" and not value.get("stale"),"Generated size is stale")
        require(item.get("geometry",{}).get("description")=={"kind":"sphere","radius":radius} and
                item.get("geometry",{}).get("representation")=="authored_analytic_geometry","Generated source sphere differs")
        records=source.get("input_zips",[])
        check_zips(records,units)
        require_expression_origins(records,case["probe"]["required_zip_expressions"],units,"generated zip")
        if path in expected.get("generated_input_zips_exact",{}):
            wanted=expected["generated_input_zips_exact"][path]
            check_zips(records,units,expected=wanted,exact=True,require_nonempty=bool(wanted))
        if "required_aggregate_map_key"in expected:
            maps=source.get("input_transforms",[])
            check_transforms(maps,units)
            keys={record.get("key")for record in maps}
            require(expected["required_aggregate_map_key"]in keys and expected["forbidden_relabelled_map_key"]not in keys,
                    "Unrelated aggregate map acquired the generated zip key")
        no_zip_origins(previous)
        count+=1
    return count


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
    """Compare complete public typed values to independent .17 source controls."""
    payload,baseline=case_payload(fixtures,case),case_payload(fixtures,case,control=True)
    units,old_units=source_units(payload),source_units(baseline)
    require(actual.get("program_revision")==case["program_revision"],"Inspection names another actual source")
    require(control.get("program_revision")==case["explicit_c084_control"]["program_revision"],"Control inspection names another source")
    require(actual.get("ok")is not False and control.get("ok")is not False and
            not any(c.startswith(("OKL-E-","OKE-E-"))for c in codes(actual)+codes(control)),"Source inspection failed")
    a_items,b_items=actual.get("items",[]),control.get("items",[])
    require(a_items and b_items,"Inspection retained no object records")
    locations=check_all_locations(actual,units)+check_all_locations(control,old_units)
    counts={name:0 for name in ("transform","reduction","filter","merge","zip")}
    for projection,source,is_control in ((actual,units,False),(control,old_units,True)):
        for _,node in walk(projection):
            if not isinstance(node,dict):
                continue
            if is_control:
                require("derived_zips"not in node and "input_zips"not in node,"Explicit .17 projection acquired .18 zip fields")
            for name,reader in (("transforms",check_transforms),("reductions",check_reductions),
                                ("filters",check_filters),("merges",check_merges),("zips",check_zips)):
                for field in ("derived_"+name,"input_"+name):
                    if field in node:
                        number=reader(node[field],source)
                        if not is_control:
                            counts[name[:-1]]+=number
            if isinstance(node.get("type"),str) and node["type"].startswith("Keyed<") and "derived_zips"in node:
                check_zips(node["derived_zips"],source,aggregate=True)
    probes=0;expectations=case.get("expected")or{};probe=case.get("probe")
    if probe:
        av=inspect_member(a_items,probe["object_path"],probe["member"])
        bv=inspect_member(b_items,probe["object_path"],probe["member"])
        require(av.get("status")==bv.get("status")=="resolved" and not av.get("stale")and not bv.get("stale"),"Typed probe unresolved/stale")
        require(av["type"]==bv["type"] and canonical_probe_type(av["type"])==canonical_probe_type(probe["type"]),"Exact output type/dimension differs")
        require(av.get("frame")==bv.get("frame")and av.get("canonical_unit")==bv.get("canonical_unit"),"Output frame/unit differs")
        require(semantic_value(av["value"],units)==semantic_value(bv["value"],old_units),"Complete typed output differs from independent .17 control")
        if "keys"in probe:
            probes+=check_keyed_membership(av,probe["keys"],scalars=probe.get("scalar_values"))+1
            probes+=check_zip_leaf_provenance(av,units,expectations)
        if "scalar_value"in probe:
            wanted,got=probe["scalar_value"],av["value"]
            require(got==wanted and (type(got)is type(wanted)or type(got)in(int,float)and type(wanted)in(int,float)),"Independent scalar answer differs")
            probes+=1
        records=av.get("derived_zips",[])
        required={_location_identity(x)for x in probe["required_zip_expressions"]}
        selected=[r for r in case.get("source_zip_records",[])if _location_identity(r["expression"])in required]
        check_zips(records,units,expected=selected,require_nonempty=probe["zip_required"])
        require_zip_order(records,probe["required_zip_expression_order"],units)
        if "derived_zips_exact"in expectations:
            wanted=expectations["derived_zips_exact"]
            check_zips(records,units,expected=wanted,exact=True,require_nonempty=bool(wanted))
        for name,singular,label in (("reductions","reduction","reduction"),("transforms","transform","map"),
                                    ("filters","filter","filter"),("merges","merge","merge")):
            inherited=av.get("derived_"+name,[]);wanted=probe["required_"+singular+"_expressions"]
            require_expression_origins(inherited,wanted,units,label)
            require({_location_identity(r["expression"])for r in inherited}=={_location_identity(x)for x in wanted},
                    "Unexpected or missing inherited "+label+" origin")
        require(not any(name in av for name in ("key","iteration","ordinal","element_id")),"Typed result gained editable/iteration identity")
        paths={r["path"]for r in av.get("dependencies",[])if "path"in r}
        require(set(expectations.get("observed_dependencies_include",[]))<=paths,"Zip lost earlier actual dependency")
        require(not set(expectations.get("observed_dependencies_exclude",[]))&paths,"Zip invented unselected dynamic dependency")
        if expectations.get("unselected_generated_dynamic_reads_absent"):
            require(not any('.leaves['in path for path in paths),"Unselected generated branch became a dynamic read")
        called={tuple(r["element_id"])for r in av.get("dependencies",[])if r.get("relationship")=="called_definition"}
        require({nominal_definition_id(x,units)for x in expectations.get("called_definition_ids_include",[])}<=called,"Imported helper dependency lost")
        for dependency in av.get("dependencies",[]):
            require(dependency["program_revision"]==case["program_revision"],"Dependency names stale source")
        for member,wanted in expectations.get("unchanged_properties",{}).items():
            original=inspect_member(a_items,probe["object_path"],member)
            previous=inspect_member(b_items,probe["object_path"],member)
            require(original["type"]==previous["type"]and semantic_value(original["value"],units)==semantic_value(previous["value"],old_units),"Aliased input changed")
            probes+=check_keyed_membership(original,wanted["keys"],scalars=wanted["scalar_values"])
            no_zip_origins(original)
    if "widths_m"in expectations:
        probes+=check_panel_values(a_items,case,fixtures,units)
        probes+=check_panel_values(b_items,case,fixtures,old_units,control=True)
    if "generated_paths"in expectations:
        probes+=check_generated_shapes(a_items,b_items,case,units,old_units)
    require(probes or probe,"Valid source has no independently checked typed probe")
    return {"status":"passed","typed_probe":(probe or{}).get("type"),"typed_checks":probes,
            "source_locations":locations,**{"derived_"+name+"_records":count for name,count in counts.items()},
            "control_program_revision":case["explicit_c084_control"]["program_revision"]}


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
    payload=case_payload(fixtures,case,control=control)
    revision,manifest=bundle_identity(payload);units=source_units(payload)
    meta=glb.document["extras"]["ontokin"]
    require(meta.get("target_contract")==("ontokin.glb/0.17"if control else TARGET)and
            meta.get("schema_version")==("0.17"if control else"0.18")and
            meta.get("profile")==("keyed-merge-0.1"if control else PROFILE),"GLB source/target contract mismatch")
    require(meta["source"]["uri"]==payload["entry"]["filename"]=="main.ok"and meta["source"]["entry_source_id"]=="entry"and
            meta["source"]["entry_revision"]==digest(units["entry"]["source"].encode()),"GLB entry source locator differs")
    program=meta["program"]
    require(program["revision"]==revision and program["manifest"]==manifest and program["entry_source_id"]=="entry","GLB immutable source manifest differs")
    require(set(program["sources"])==set(units),"GLB source-unit inventory differs")
    for identity,unit in units.items():
        match=re.search(r'\bmodule\s+(\w+)\s*@\s*"([^"]+)"',unit["source"])
        require(match is not None,"Frozen source lacks literal module identity")
        wanted={"source_id":identity,"source_revision":digest(unit["source"].encode()),"filename":unit["filename"],
                "package_id":unit.get("package_id"),"version":unit.get("version"),"module_name":match[1],"module_key":match[2]}
        require(program["sources"][identity]==wanted,"GLB module identity differs")
    wanted_nodes=expected_occurrences(case)
    require(set(program["occurrences"])==set(wanted_nodes)==set(glb.objects()),"GLB occurrence inventory differs")
    require(set(program["collections"])=={"first.panels","sibling.panels"},"GLB collection inventory differs")
    sources=panel_sources(case,fixtures,control=control)
    for owner in ("first","sibling"):
        collection=program["collections"][owner+".panels"];keys=sorted(case["expected"]["widths_m"][owner])
        require(collection["owner_path"]==owner and collection["ordered_keys"]==keys and
                collection["element_id"]==["panel-task","demo",owner,"panels"],"Generated collection identity differs")
        require(set(collection["entries"])==set(keys),"Generated collection keyset differs")
        for key,entry in collection["entries"].items():
            path=owner+'.panels["'+key+'"]'
            require(entry=={"path":path,"element_id":wanted_nodes[path]["element_id"]},"Generated stable entry identity differs")
    for path,wanted in wanted_nodes.items():
        occurrence=program["occurrences"][path]
        require(occurrence["path"]==path and occurrence["element_id"]==wanted["element_id"]and
                occurrence["owner_path"]==wanted["owner"],"Occurrence source identity differs")
        node=glb.document["nodes"][glb.objects()[path]];identity=node["extras"]["ontokin"]
        require(identity["source_mapping"]==occurrence and identity["element_id"]==wanted["element_id"]and
                identity["program_revision"]==revision,"Native node/program occurrence projections differ")
        generated=occurrence.get("generated")
        if "input_key"not in wanted:
            require(generated is None,"Ordinary occurrence is mislabeled generated")
            continue
        key=wanted["input_key"]
        require(generated and generated["key"]==key and generated["collection_path"]==wanted["owner"]+".panels"and
                generated["unique_declaration_span"]is False,"Generated paired identity differs")
        merge_location(generated["input_entry"],primary_panel_entry(case,fixtures,key,control=control),units)
        if control:
            no_zip_origins(generated)
        else:
            check_zips(generated.get("input_zips"),units,expected=panel_zip_records(sources)+panel_zip_records(sources,key),exact=True)
        check_merges(generated.get("input_merges"),units,expected=paired_panel_merges(sources,control=control),exact=True)
        require(not any(field in generated for field in ("input_filters","input_transforms","input_reductions")),
                "Panel paired input acquired an unselected inherited operation")
    count=check_all_locations(glb.document,units)
    basis=implementation_basis(fixtures["repository"]);quantization=meta["reach_quantization"]
    require(quantization["source_numeric_bound_basis"]==basis["source"],"GLB source numeric identity differs from actual supplied sourcecut")
    for name,value in basis["destination"].items():
        require(quantization["destination_numeric_bound_basis"][name]==value,"Destination numeric identity differs")
    require(quantization["position_tolerance_m"]<=.001 and quantization["rotation_tolerance_rad"]<=.001 and
            quantization["time_tolerance_s"]<=1e-6,"Recording tolerances widened")
    require(len(wanted_nodes)==case["expected"]["object_count"],"Frozen complete object count differs")
    return {"program_revision":revision,"source_locations":count,"generated_occurrences":4,"ordinary_occurrences":3}


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
    profile = "keyed-merge-0.1" if control else PROFILE
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
            if key == "input_zips" and _mapping_tail(path) == ("generated",):
                require(not control, "Explicit .17 stream acquired zip provenance")
                check_zips(child, units)
                changes.append({"path": list(current), "kind": "adopted_zip_derivation", "value_sha256": sha(canonical(child))})
                continue
            if key == "input_merges" and _mapping_tail(path) == ("generated",):
                check_merges(child, units)
                changes.append({"path": list(current), "kind": "adopted_merge_derivation", "value_sha256": sha(canonical(child))})
                continue
            if key == "input_filters" and _mapping_tail(path) == ("generated",):
                require(not control, "Explicit literal control acquired unselected filter provenance")
                check_filters(child, units)
                changes.append({"path": list(current), "kind": "adopted_filter_derivation", "value_sha256": sha(canonical(child))})
                continue
            if key == "input_reductions" and _mapping_tail(path) == ("generated",):
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
                require(child == ("ontokin.glb/0.17" if control else TARGET), "Unexpected target")
                replacement, reason = "<explicit_profile_target>", "adopted_target"
            elif current == ("extras", "ontokin", "schema_version"):
                require(child == ("0.17" if control else "0.18"), "Unexpected source schema")
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
    require(glb.binary == old.binary, "Complete BIN chunk differs from explicit .17 source control")
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
    glb, old = GLB(raw, target=TARGET), GLB(control, target="ontokin.glb/0.17")
    source = check_program_metadata(glb, case, fixtures)
    baseline = check_program_metadata(old, case, fixtures, control=True)
    geometry = check_geometry(glb, case)
    images = check_images(glb, case_payload(fixtures, case))
    motion = check_motion(glb, case)
    identity = check_identity(glb, old, case, fixtures)
    return {"case": case["name"], "status": "passed", "sha256": sha(raw), "bytes": len(raw), "source": source,
            "control_source": baseline, "geometry": geometry, "images": images, "motion": motion, "identity": identity}
