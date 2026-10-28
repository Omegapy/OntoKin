#!/usr/bin/env python3
"""Independently audit failed original P11/L03 recording diagnostics.

This program uses only Python's standard library. It never imports OntoKin,
executes source, resumes a failed request, or certifies the retained GLB.
Primitive GLB, rational, source-identity and certificate census routines derive
from checkpoint-033-census.py. Historical source IDs, operation counts and
failure-site expectations are deliberately absent from this auditor.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import struct
import subprocess
import sys
import traceback

MAX_FILE = 64 * 1024 * 1024
MAX_BITS = 32768
BASE = "docs/language-design/planar-reach-v0.1"
CHECKS = 0
CAPTURE_PATH = "tools/capture_reach_recording_work.py"
WRAPPER_NAMES = {"capture_validate_export", "capture_key_comparisons", "capture_recording_stage"}
WORK_LIMITS = {"max_operations": 100000, "max_elapsed_ms": 30000,
               "max_operand_bits": 32768, "max_cache_entries": 256}
BUDGET_LIMITS = {"max_objects": 1000, "max_operations": 100000,
                 "max_result_items": 1000, "max_elapsed_ms": 30000,
                 "max_value_entries": 100000}
CAPTURE_IDENTITIES = {
    "validate_export_restored", "key_comparisons_restored", "recording_stage_restored",
    "native_dispatch_preserved", "no_trace_hook", "no_profile_hook",
    "reader_owner_preserved", "reader_arguments_preserved", "reader_external_preserved",
    "reader_observer_restored", "same_callback_error_at_reader_exit",
    "external_callback_preserved", "native_callback_owner_preserved",
    "construction_check_preserved", "observer_restored_after_request",
    "callback_error_preserved", "key_reader_exception_identical",
    "work_limits_unchanged", "budget_limits_unchanged",
}
KEY_IDENTITIES = {
    "positional_arguments_preserved", "keyword_arguments_preserved", "work_owner_preserved",
    "source_owners_preserved", "source_check_preserved", "source_observer_restored",
    "external_preserved", "work_observer_preserved", "no_trace_hook", "no_profile_hook",
}
C033_READER_SOURCE_SHA256 = '91893ac4a26f898acb01c9c8277cbf0cab5c87071ce2f3fd600902521ab44892'

NUMERIC_KEYS = tuple(sorted((
    "landmark_radius_m", "local_vertex_error_bound_m",
    "angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
    "enclosing_carrier_speed_bound_m_per_s",
    "enclosing_carrier_acceleration_bound_m_per_s2",
    "enclosing_angular_speed_bound_rad_per_s", "max_endpoint_time_shift_s",
    "max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error",
    "stored_quaternion_arc_upper_rad", "source_numeric_position_bound_m",
    "source_numeric_rotation_bound_rad", "destination_numeric_position_bound_m",
    "destination_numeric_rotation_bound_rad", "unit_quaternion_difference_bound",
    "ideal_rotation_bound_rad", "ideal_position_bound_m", "carrier_position_bound_m",
    "total_position_bound_m", "total_rotation_bound_rad")))

ROW_KEYS = set(NUMERIC_KEYS) | {"left_key_index", "right_key_index", "carrier",
    "source_phase_indices", "h_authored_seconds", "h_stored_seconds"}

def require(condition, message):
    global CHECKS
    CHECKS += 1
    if not condition:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("Nonfinite JSON value: " + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode()

def relative(value):
    require(type(value) is str and value and "\\" not in value and "\0" not in value,
            "Evidence path must be a nonempty native relative string")
    path = PurePosixPath(value)
    require(not path.is_absolute() and str(path) == value
            and all(part not in ("", ".", "..") for part in path.parts),
            "Evidence path is not a canonical contained relative path")
    return path

class Inputs:
    def __init__(self):
        self.records = {}

    def read(self, path):
        path = Path(path).absolute()
        require(not any(item.is_symlink() for item in (path, *path.parents)),
                "Input path uses a symlink: " + str(path))
        before = path.stat()
        require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= MAX_FILE,
                "Input is not a bounded regular file: " + str(path))
        raw = path.read_bytes()
        after = path.stat()
        require(len(raw) == before.st_size == after.st_size
                and before.st_mtime_ns == after.st_mtime_ns,
                "Input changed while reading: " + str(path))
        receipt = {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}
        require(str(path) not in self.records or self.records[str(path)] == receipt,
                "Input changed between reads: " + str(path))
        self.records[str(path)] = receipt
        return raw

    def json(self, path):
        return decode(self.read(path))

    def stable_receipts(self):
        original = dict(self.records)
        for path in original:
            self.read(path)
        require(self.records == original, "Analysis input set or bytes changed")
        return [original[name] for name in sorted(original)]

def decimal(value):
    require(type(value) is str and len(value) <= 10000
            and re.fullmatch(r"0|-?[1-9][0-9]*", value) is not None,
            "Invalid bounded canonical decimal integer")
    negative = value.startswith("-")
    text = value[1:] if negative else value
    result = 0
    for start in range(0, len(text), 1000):
        chunk = text[start:start + 1000]
        result = result * 10 ** len(chunk) + int(chunk)
    require(result.bit_length() <= MAX_BITS, "Rational operand exceeds original bit cap")
    return -result if negative else result

def decimal_text(value):
    require(type(value) is int and value.bit_length() <= MAX_BITS,
            "Cannot serialize an unbounded integer")
    if not value:
        return "0"
    sign, remaining, pieces = ("-" if value < 0 else ""), abs(value), []
    while remaining:
        remaining, remainder = divmod(remaining, 10 ** 1000)
        pieces.append(remainder)
    return sign + str(pieces[-1]) + "".join(f"{item:01000d}" for item in reversed(pieces[:-1]))

def rational(record):
    require(type(record) is dict and set(record) == {"numerator", "denominator"},
            "Unexpected exact-rational fields")
    n, d = decimal(record["numerator"]), decimal(record["denominator"])
    require(d > 0, "Rational denominator is not positive")
    result = Fraction(n, d)
    require((result.numerator, result.denominator) == (n, d), "Rational is not reduced")
    return result

def ratio(value):
    return {"numerator": decimal_text(value.numerator),
            "denominator": decimal_text(value.denominator)}

def clock_text(value):
    require(type(value) is str and len(value) <= 1000,
            "Source clock is not a bounded exact string")
    result = Fraction(value)
    require(max(result.numerator.bit_length(), result.denominator.bit_length()) <= MAX_BITS,
            "Source clock exceeds original operand cap")
    return result

def number(value):
    require(type(value) in (int, float) and value >= 0
            and (type(value) is int or math.isfinite(value)),
            "Certificate number is not a finite nonnegative native scalar")
    result = Fraction(value)
    require(max(result.numerator.bit_length(), result.denominator.bit_length()) <= MAX_BITS,
            "Certificate scalar exceeds original operand cap")
    return result

def parse_glb(raw):
    require(20 <= len(raw) <= MAX_FILE, "Invalid bounded GLB size")
    magic, version, length = struct.unpack_from("<4sII", raw)
    require((magic, version, length) == (b"glTF", 2, len(raw)), "GLB header differs")
    position, chunks = 12, []
    while position < len(raw):
        require(position + 8 <= len(raw), "Truncated GLB chunk header")
        size, kind = struct.unpack_from("<II", raw, position)
        position += 8
        require(size % 4 == 0 and position + size <= len(raw), "Invalid GLB chunk extent")
        chunks.append((kind, raw[position:position + size]))
        position += size
    require([kind for kind, _ in chunks] == [0x4E4F534A, 0x004E4942],
            "Expected one JSON chunk and one embedded BIN chunk")
    document, binary = decode(chunks[0][1]), chunks[1][1]
    require(document.get("asset", {}).get("version") == "2.0", "Unexpected glTF version")
    buffers = document["buffers"]
    require(len(buffers) == 1 and "uri" not in buffers[0]
            and type(buffers[0]["byteLength"]) is int
            and 0 <= len(binary) - buffers[0]["byteLength"] <= 3,
            "Embedded buffer extent differs")
    return document, binary

def binary32(word):
    require(type(word) is int and 0 <= word <= 0xffffffff, "Invalid binary32 bits")
    exponent, mantissa = (word >> 23) & 255, word & 0x7fffff
    require(exponent != 255, "Nonfinite binary32 value")
    sign = -1 if word & 0x80000000 else 1
    if exponent == 0:
        return Fraction(sign * mantissa, 1 << 149)
    mantissa |= 1 << 23
    power = exponent - 150
    return Fraction(sign * (mantissa << power)) if power >= 0 else Fraction(sign * mantissa, 1 << -power)

def accessor(document, binary, index, kind, count=None):
    require(type(index) is int and 0 <= index < len(document["accessors"]),
            "Invalid accessor index")
    entry = document["accessors"][index]
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[kind]
    require(entry.get("componentType") == 5126 and entry.get("type") == kind
            and "sparse" not in entry and not entry.get("normalized", False),
            "Track accessor is not plain binary32 of the required shape")
    size = entry["count"]
    require(type(size) is int and 1 <= size <= 10000 and (count is None or size == count),
            "Track key count differs or exceeds cap")
    view_id = entry["bufferView"]
    require(type(view_id) is int and 0 <= view_id < len(document["bufferViews"]),
            "Invalid track buffer-view index")
    view = document["bufferViews"][view_id]
    stride, offset, start = view.get("byteStride", 4 * width), entry.get("byteOffset", 0), view.get("byteOffset", 0)
    require(view["buffer"] == 0 and all(type(value) is int and value >= 0
            for value in (stride, offset, start, view["byteLength"]))
            and stride >= 4 * width and stride % 4 == offset % 4 == start % 4 == 0,
            "Track buffer layout is invalid")
    require(offset + (size - 1) * stride + 4 * width <= view["byteLength"]
            and start + view["byteLength"] <= document["buffers"][0]["byteLength"],
            "Track extends outside its embedded view or buffer")
    words = tuple(tuple(struct.unpack_from("<" + "I" * width, binary,
                         start + offset + key * stride)) for key in range(size))
    values = tuple(tuple(binary32(word) for word in row) for row in words)
    layout = {"accessor": index, "buffer_view": view_id, "count": size,
              "components": width, "buffer_view_offset": start,
              "accessor_offset": offset, "byte_stride": stride,
              "logical_binary32_sha256": digest(b"".join(struct.pack("<" + "I" * width, *row) for row in words))}
    return values, words, layout

def rounded_clock(value, word):
    require(0 <= word <= 0x7f7fffff and value >= 0, "Clock is negative or nonfinite")
    center = binary32(word)
    low = Fraction(0) if word == 0 else (binary32(word - 1) + center) / 2
    following = Fraction(1 << 128) if word == 0x7f7fffff else binary32(word + 1)
    high = (center + following) / 2
    even = not word & 1
    return (value > low or even and value == low) and (value < high or even and value == high)

def source_receipts(repo, case, document, request, inputs):
    base = repo / BASE / ("draft2-supplements" if case.startswith("L") else "")
    manifest = inputs.json(base / (case.lower() + ".files.json"))
    records = [manifest["entry"], *manifest["modules"]]
    metadata = document["extras"]["ontokin"]
    program = metadata["program"]
    sources = program["sources"]
    require(type(sources) is dict and "entry" in sources, "GLB has no complete supplied source closure")
    named = {item["filename"]: item for item in sources.values()}
    require(len(named) == len(sources) == len(records), "Source filenames do not form an exact closure")
    result = []
    for item in records:
        path = base / relative(item["path"])
        raw = inputs.read(path)
        require(item["filename"] in named
                and named[item["filename"]]["source_revision"] == "sha256:" + digest(raw),
                "GLB source digest differs from the unchanged original fixture")
        result.append({"path": path.relative_to(repo).as_posix(), "filename": item["filename"],
                       "bytes": len(raw), "sha256": digest(raw)})
    corpus = inputs.json(base / "acceptance.json")
    expected = [item for item in corpus["source_cases"] if item["id"] == case]
    require(len(expected) == 1 and expected[0]["program_revision"] == request["program_revision"],
            "Request revision differs from the frozen original case")
    require(program["revision"] == request["program_revision"]
            == "sha256:" + digest(b"ontokin.bundle/0.1\0" + canonical(program["manifest"])),
            "GLB/request program revision differs")
    require(program["entry_source_id"] == program["manifest"]["entry_source_id"] == "entry"
            and program["manifest"]["schema_version"] == "ontokin.bundle/0.1",
            "Original source manifest identity differs")
    units = program["manifest"]["units"]
    require(len(units) == len(sources)
            and {unit["source_id"] for unit in units} == set(sources)
            and all(all(sources[unit["source_id"]].get(name) == value for name, value in unit.items())
                    for unit in units), "Program source mapping differs from its exact hashed manifest")
    return result

def census_bytes(repo, case, capture_dir, capture, request, inputs):
    expected_end = Fraction(request["options"]["end"])
    require(capture["artifact"]["path"] == "unvalidated-reader-input.glb",
            "Retained bytes must remain explicitly unvalidated")
    raw = inputs.read(capture_dir / "unvalidated-reader-input.glb")
    require(capture["artifact"]["bytes"] == len(raw) and capture["artifact"]["sha256"] == digest(raw),
            "Captured input byte identity differs")
    document, binary = parse_glb(raw)
    source = source_receipts(repo, case, document, request, inputs)
    metadata = document["extras"]["ontokin"]
    quantization = metadata["reach_quantization"]
    require(quantization["schema_version"] == "ontokin.reach-quantization/0.1",
            "Unexpected quantization schema")
    require(len(document["animations"]) == 1, "Expected exactly one original animation")
    animation = document["animations"][0]
    samplers = animation["samplers"]
    require(bool(samplers), "Animation contains no samplers")
    clocks, clock_words, layouts = None, None, []
    for index in sorted({sampler["input"] for sampler in samplers}):
        values, words, layout = accessor(document, binary, index, "SCALAR")
        axis = tuple(row[0] for row in values)
        bits = tuple(row[0] for row in words)
        if clocks is None:
            clocks, clock_words = axis, bits
        require((axis, bits) == (clocks, clock_words), "Samplers have different binary clock axes")
        layouts.append(layout)
    authored_records = animation["extras"]["ontokin"]["exact_times_seconds"]
    authored = tuple(rational(item) for item in authored_records)
    retained = quantization["retained_keys"]
    require(2 <= len(clocks) == len(authored) == len(retained) <= 256,
            "Decoded original key count differs")
    require(authored[0] == clocks[0] == 0 and authored[-1] == clocks[-1] == expected_end,
            "Original complete recording endpoints differ")
    require(all(left < right for left, right in zip(clocks, clocks[1:]))
            and all(left < right for left, right in zip(authored, authored[1:])),
            "Decoded clocks are not strictly increasing")
    boundaries = tuple(clock_text(item["source_seconds"]) for item in metadata["boundary_states"])
    require(2 <= len(boundaries) <= 10000 and boundaries[0] == 0 and boundaries[-1] == expected_end and all(a < b for a, b in zip(boundaries, boundaries[1:])),
            "Original source boundary inventory differs")
    require(tuple(clock_text(value) for value in animation["extras"]["ontokin"]["boundary_times_seconds"]) == boundaries,
            "Animation and source-state boundary labels disagree")
    clock_rows = []
    for index, (time, stored, word, record) in enumerate(zip(authored, clocks, clock_words, retained)):
        require(set(record) == {"authored_seconds", "stored_seconds", "stored_binary32_bits", "semantic_boundary"},
                "Retained clock field inventory differs")
        require(record["authored_seconds"] == authored_records[index]
                and number(record["stored_seconds"]) == stored
                and record["stored_binary32_bits"] == f"{word:08x}"
                and type(record["semantic_boundary"]) is bool
                and record["semantic_boundary"] == (time in boundaries)
                and rounded_clock(time, word), "Retained clock labels or nearest-even conversion differ from bytes")
        clock_rows.append({"index": index, "authored": ratio(time), "stored": ratio(stored),
                           "binary32_bits": f"{word:08x}", "shift": ratio(abs(time - stored)),
                           "semantic_boundary": time in boundaries})
    nodes = document["nodes"]
    require(0 < len(nodes) <= 64, "Actual original carrier inventory differs")
    require(document["scene"] == 0 and len(document["scenes"]) == 1
            and document["scenes"][0]["nodes"] == list(range(len(nodes)))
            and metadata["transform_policy"] == "all_nodes_are_roots_with_baked_world_poses",
            "Original carrier scene/root transform mapping differs")
    identities, carriers = {}, []
    for index, node in enumerate(nodes):
        info = node["extras"]["ontokin"]
        require(info["kind"] == "object" and node["name"] == info["path"]
                and info["path"] not in identities, "Carrier metadata is duplicated or not an original object")
        identity = {"path": info["path"], "element_id": info["element_id"]}
        occurrence = metadata["program"]["occurrences"][info["path"]]
        require(occurrence["path"] == identity["path"] and occurrence["element_id"] == identity["element_id"]
                and info["program_revision"] == metadata["program"]["revision"],
                "Carrier identity differs from the original source occurrence map")
        identities[info["path"]] = (index, identity)
        carriers.append({"node_index": index, "identity": identity,
                         "frame": info["path"] + ".frame", "tracks": {}})
    decoded_tracks = {}
    for channel in animation["channels"]:
        target = channel["target"]
        node, path, sampler_id = target["node"], target["path"], channel["sampler"]
        require(type(node) is int and 0 <= node < len(nodes) and path in ("translation", "rotation")
                and type(sampler_id) is int and 0 <= sampler_id < len(samplers)
                and (node, path) not in decoded_tracks, "Animation channel identity differs or repeats")
        sampler = samplers[sampler_id]
        require(sampler.get("interpolation", "LINEAR") == "LINEAR", "Original carrier track is not LINEAR")
        values, words, layout = accessor(document, binary, sampler["output"],
                                        "VEC3" if path == "translation" else "VEC4", len(authored))
        decoded_tracks[node, path] = (values, words)
        carriers[node]["tracks"][path] = {"sampler": sampler_id, **layout,
            "binary32_rows": [[f"{word:08x}" for word in row] for row in words],
            "exact_rows": [[ratio(value) for value in row] for row in values]}
    require(set(decoded_tracks) == {(node, path) for node in range(len(nodes)) for path in ("translation", "rotation")},
            "Every original carrier requires exactly two complete transform tracks")
    rows = {}
    for ordinal, record in enumerate(quantization["interval_certificates"]):
        require(type(record) is dict and set(record) == ROW_KEYS, "Certificate row field inventory differs")
        left, right, identity = record["left_key_index"], record["right_key_index"], record["carrier"]
        require(type(left) is int and type(right) is int and 0 <= left < len(authored) - 1 and right == left + 1,
                "Certificate has nonadjacent or invalid key indices")
        require(type(identity) is dict and identity.get("path") in identities
                and identity == identities[identity["path"]][1], "Certificate carrier differs from actual node identity")
        node = identities[identity["path"]][0]
        require((left, node) not in rows, "Duplicate carrier/interval certificate")
        ha, hs = authored[right] - authored[left], clocks[right] - clocks[left]
        require(rational(record["h_authored_seconds"]) == ha
                and rational(record["h_stored_seconds"]) == hs, "Certificate widths differ from actual clocks")
        low = max(Fraction(0), min(authored[left], clocks[left]))
        high = min(Fraction(expected_end), max(authored[right], clocks[right]))
        required = [index for index, (a, b) in enumerate(zip(boundaries, boundaries[1:]))
                    if max(a, low) < min(b, high)]
        selected = record["source_phase_indices"]
        require(type(selected) is list and len(selected) == len(set(selected))
                and all(type(value) is int and 0 <= value < len(boundaries) - 1 for value in selected)
                and set(required).issubset(selected)
                and all(max(low, boundaries[value]) <= min(high, boundaries[value + 1]) for value in selected),
                "Certificate phase selection differs from actual interval overlap")
        for name in NUMERIC_KEYS:
            number(record[name])
        rows[left, node] = {"input_ordinal": ordinal, "left_key_index": left, "right_key_index": right,
                           "node_index": node, "carrier": identity,
                           "h_authored_seconds": ratio(ha), "h_stored_seconds": ratio(hs),
                           "selected_source_phases": selected, "required_positive_overlap_phases": required,
                           "numeric_fields": {name: record[name] for name in NUMERIC_KEYS},
                           "canonical_row_sha256": digest(canonical(record))}
    require(len(rows) == (len(authored) - 1) * len(nodes)
            and set(rows) == {(key, node) for key in range(len(authored) - 1) for node in range(len(nodes))},
            "Certificate identities do not cover every actual interval/carrier exactly once")
    return {"artifact": {"bytes": len(raw), "sha256": digest(raw), "accepted": False},
        "original_source_files": source, "clock_count": len(authored), "carrier_count": len(nodes),
        "certificate_count": len(rows), "clock_accessors": layouts, "clocks": clock_rows,
        "source_boundaries": [ratio(value) for value in boundaries],
        "source_boundary_records": metadata["boundary_states"], "carriers": carriers,
        "certificates": [rows[key] for key in sorted(rows)],
        "decoded_numeric_fields_are_source_certified": False}, authored, boundaries, decoded_tracks


def same(first, last):
    """JSON value equality that does not conflate bool, int and float."""
    return canonical(first) == canonical(last)


def sha_text(value):
    require(type(value) is str, "Missing hash string")
    value = value.removeprefix("sha256:")
    require(re.fullmatch(r"[0-9a-f]{64}", value) is not None, "Invalid SHA-256")
    return value


def tree_hash(rows):
    root = {}
    for row in rows:
        parts = relative(row["path"]).parts
        cursor = root
        for part in parts[:-1]:
            require(part not in cursor or type(cursor[part]) is dict, "File/directory input collision")
            cursor = cursor.setdefault(part, {})
        require(parts[-1] not in cursor, "Repeated tracked input path")
        require(row["mode"] in ("100644", "100755") and
                re.fullmatch(r"[0-9a-f]{40}", row["git_blob"]) is not None,
                "Invalid input mode or blob identity")
        cursor[parts[-1]] = (row["mode"], row["git_blob"])

    def build(directory):
        chunks = []
        for name, value in sorted(directory.items(), key=lambda item:
                                 (item[0] + ("/" if type(item[1]) is dict else "")).encode()):
            if type(value) is dict:
                mode, identity = "40000", build(value)
            else:
                mode, identity = value
            chunks.append((mode + " " + name).encode() + b"\0" + bytes.fromhex(identity))
        raw = b"".join(chunks)
        return hashlib.sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    return build(root)


def verify_snapshot(repo, snapshot, inputs):
    require(snapshot.get("scope") == "materialized_tracked_bytes_with_explicit_omissions"
            and snapshot.get("complete_stock_harness") is False,
            "Evidence does not disclose its materialization scope")
    identity, present, omitted = snapshot["git"], snapshot["files"], snapshot["omitted"]
    require(type(present) is list and type(omitted) is list and present,
            "Missing materialized input inventory")
    require(identity["status"] == "" and type(identity["shallow"]) is bool
            and re.fullmatch(r"[0-9a-f]{40}", identity["commit"]) is not None
            and re.fullmatch(r"[0-9a-f]{40}", identity["tree"]) is not None,
            "Invalid executed Git identity")
    require(snapshot["materialized_count"] == len(present)
            and snapshot["tracked_count"] == len(present) + len(omitted)
            and snapshot["complete_checkout"] is (not omitted), "Input inventory counts differ")
    require(tree_hash(present + omitted) == identity["tree"],
            "Materialized and omitted input identities do not reconstruct the executed Git tree")
    commit = subprocess.check_output(["git", "-C", str(repo), "cat-file", "commit", identity["commit"]])
    require(hashlib.sha1(b"commit " + str(len(commit)).encode() + b"\0" + commit).hexdigest()
            == identity["commit"] and commit.splitlines()[0] == ("tree " + identity["tree"]).encode(),
            "Exact Git commit object does not bind the reconstructed tree")
    named = {}
    for row in present:
        path = repo / relative(row["path"])
        raw = inputs.read(path)
        require(type(row["bytes"]) is int and len(raw) == row["bytes"]
                and digest(raw) == sha_text(row["sha256"]), "Materialized input bytes differ: " + row["path"])
        require(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == row["git_blob"],
                "Materialized input Git blob differs: " + row["path"])
        require(bool(path.stat().st_mode & 0o111) == (row["mode"] == "100755"),
                "Materialized input mode differs: " + row["path"])
        named[row["path"]] = row
    runtime = {row["path"] for row in present + omitted if row["path"].startswith("ontokin/")}
    require(runtime <= set(named), "Runtime source closure has omitted tracked inputs")
    basis = {
        "reach-numeric-kernel.md", "reach-source-kernel.md", "reach-coaxial-phase-bounds.md",
        "reach-carrier-rotation-cursors.md", "reach-recording-certified-planar.md",
        "reach-deferred-phase-locations.md", "reach-planning-reuse.md",
        "reach-release-cell-envelope.md", "reach-destination-numerics.md",
    }
    require({"docs/engineering/" + name for name in basis} <= set(named)
            and "tools/reach_destination.mjs" in named,
            "Required numerical derivation/destination inputs are missing")
    return named, {"source_commit": identity["commit"], "source_tree": identity["tree"],
        "exact_commit_object_verified": True, "complete_tree_identity_reconstructed": True,
        "materialized_files_verified": len(present), "materialized_bytes_verified": sum(row["bytes"] for row in present),
        "runtime_files_verified": len(runtime), "omitted_tracked_files": len(omitted),
        "omitted_payload_bytes_verified": False, "complete_stock_harness": False,
        "source_history_is_shallow": identity["shallow"]}


def verify_modules(request, named):
    rows = request["loaded_modules"]
    require(type(rows) is list and rows, "No loaded-module evidence")
    modules = {}
    for row in rows:
        require(row["module"] not in modules and row["path"] in named,
                "Duplicate module or unbound loaded module path")
        expected = named[row["path"]]
        require(row["path"].endswith(".py") and row["bytes"] == expected["bytes"]
                and sha_text(row["sha256"]) == sha_text(expected["sha256"]),
                "Loaded module differs from materialized source")
        modules[row["module"]] = row
    require("ontokin" in modules and "ontokin.gltf" in modules and "ontokin.reach_conformance" in modules,
            "Required actual runtime imports are missing")
    return {name: modules[name] for name in sorted(modules) if name == "ontokin" or name.startswith("ontokin.")}


def wrapper_spans(repo, inputs):
    source = inputs.read(repo / CAPTURE_PATH)
    syntax = ast.parse(source)
    spans = {node.name: (node.lineno, node.end_lineno) for node in ast.walk(syntax)
             if isinstance(node, ast.FunctionDef) and node.name in WRAPPER_NAMES}
    require(set(spans) == WRAPPER_NAMES, "Declared wrapper function inventory differs")
    return spans


def normalize_frames(frames, repo, spans, *, remove_wrappers):
    require(type(frames) is list and frames, "Missing failure traceback frames")
    normalized, removed = [], []
    for frame in frames:
        require(type(frame) is dict and set(frame) == {"file", "line", "function"}
                and type(frame["file"]) is str and type(frame["function"]) is str
                and type(frame["line"]) is int and frame["line"] > 0, "Invalid traceback frame")
        path = Path(frame["file"])
        if path.is_absolute():
            resolved = path.resolve()
            name = resolved.relative_to(repo).as_posix() if resolved.is_relative_to(repo) else str(resolved)
        else:
            name = str(relative(frame["file"]))
        item = {**frame, "file": name}
        if remove_wrappers and name == CAPTURE_PATH and frame["function"] in WRAPPER_NAMES:
            low, high = spans[frame["function"]]
            require(low <= frame["line"] <= high, "Wrapper frame is outside the verified function body")
            removed.append(item)
        else:
            normalized.append(item)
    return normalized, removed


def normalize_graph(graph, repo, spans, *, remove_wrappers):
    require(type(graph) is list and 1 <= len(graph) < 16, "Invalid causal exception graph")
    result = []
    for row in graph:
        require(set(row) == {"type", "message", "frames", "cause", "context", "suppress_context"}
                and type(row["suppress_context"]) is bool,
                "Unexpected causal exception record fields")
        for link in (row["cause"], row["context"]):
            require(link is None or type(link) is int and 0 <= link < len(graph), "Invalid exception graph edge")
        frames, _ = normalize_frames(row["frames"], repo, spans, remove_wrappers=remove_wrappers)
        result.append({**row, "frames": frames})
    return result


def normalize_traceback_text(value, repo, spans):
    require(type(value) is str and value, "Missing formatted traceback")
    lines = value.splitlines(keepends=True)
    retained, removed, index = [], [], 0
    while index < len(lines):
        match = re.fullmatch(r'  File "([^"]+)", line ([0-9]+), in ([^\n]+)\n?', lines[index])
        if match:
            frame = {"file": match[1], "line": int(match[2]), "function": match[3]}
            _, omitted = normalize_frames([frame], repo, spans, remove_wrappers=True)
            if omitted:
                removed.extend(omitted)
                index += 1
                while index < len(lines) and lines[index].startswith("    "):
                    index += 1
                continue
        retained.append(lines[index])
        index += 1
    return "".join(retained), removed


def check_identities(record, required, label):
    require(type(record) is dict and required <= set(record) and all(value is True for value in record.values()),
            label + " identity/restoration checks are incomplete or false")


def verify_descriptor(inputs, path, descriptor):
    raw = inputs.read(path)
    require(type(descriptor["bytes"]) is int and descriptor["bytes"] == len(raw)
            and sha_text(descriptor["sha256"]) == digest(raw), "Member descriptor differs: " + str(path))
    return raw


def compare_requests(baseline_dir, capture_dir, inputs):
    baseline_report = inputs.json(baseline_dir / "report.json")
    capture_report = inputs.json(capture_dir / "diagnostic/report.json")
    capture = inputs.json(capture_dir / "capture.json")
    case = capture["case_id"]
    require(case in ("P11", "L03"), "This auditor only covers the bounded P11/L03 scope")
    baseline = inputs.json(baseline_dir / case / "request-result.json")
    wrapped = inputs.json(capture_dir / "diagnostic" / case / "request-result.json")
    inventories = [inputs.json(directory / name) for directory in (baseline_dir, capture_dir / "diagnostic")
                   for name in ("inputs-before.json", "inputs-after.json")]
    require(all(same(item, inventories[0]) for item in inventories), "Pair input inventories differ or are unstable")
    repo = Path(baseline_report["working_directory"]).resolve()
    require(str(repo) == baseline_report["working_directory"] == capture_report["working_directory"],
            "Pair working source directories differ")
    named, source = verify_snapshot(repo, inventories[0], inputs)
    for report, request in ((baseline_report, baseline), (capture_report, wrapped)):
        require(report["schema_version"] == "ontokin.reach-recording-diagnostic/0.1"
                and report["status"] == request["status"] == "failed" and report["inputs_stable"] is True
                and report["source_commit"] == source["source_commit"] and report["source_tree"] == source["source_tree"]
                and same(report["deliveries"], [request]) and report["complete_stock_harness"] is False
                and report["release_acceptance"] is False and report["complete_source_delivery_corpus"] is False
                and report["full_product_goal_completed"] is False, "Request/report does not retain a failed scoped execution")
    expected_options = {"end": "3" if case == "P11" else "4", "fps": 1.0, "helpers": False,
                        "position_tolerance_m": .001, "rotation_tolerance_rad": .001, "time_tolerance_s": .000001}
    for key in ("case_id", "source_files", "program_revision", "options", "max_operations", "source_manifest",
                "source_units", "after_construction", "operations", "work", "budget_limits", "work_limits", "diagnostic"):
        require(same(baseline[key], wrapped[key]), "Baseline/capture mismatch: " + key)
    require(baseline["case_id"] == case and same(baseline["options"], expected_options)
            and baseline["max_operations"] == 100000 and same(baseline["work_limits"], WORK_LIMITS)
            and same(baseline["budget_limits"], BUDGET_LIMITS), "Original settings or limits differ")
    require(baseline["operations"] == baseline["max_operations"] + 1
            and baseline["diagnostic"]["code"] == "OKL-E-RESOURCE"
            and baseline["diagnostic"]["details"]["budget"] == "max_operations"
            and baseline["diagnostic"]["details"]["consumed"] == baseline["operations"],
            "Observed failure is not the original operation-limit refusal")
    require(set(baseline["failure"]) == set(wrapped["failure"]) == {"type", "message", "frames"}
            and baseline["failure"]["type"] == wrapped["failure"]["type"]
            and baseline["failure"]["message"] == wrapped["failure"]["message"], "Failure type/message differ")
    baseline_modules, captured_modules = verify_modules(baseline, named), verify_modules(wrapped, named)
    require(same(baseline_modules, captured_modules), "Actual loaded OntoKin module identities differ")
    require(same(baseline_report["execution"], capture_report["execution"])
            and same(baseline_report["execution"], capture["execution"]), "Pair interpreter/platform differs")
    require(capture["schema_version"] == "ontokin.reach-recording-work-capture/0.1"
            and capture["status"] == "captured_failed_request" and capture["product_request_status"] == "failed"
            and capture["accepted_artifact"] is False and capture["release_acceptance"] is False
            and capture["complete_stock_harness"] is False and capture["reader_calls"] == 1
            and capture["observation_errors"] == [] and capture["inputs_stable"] is True
            and capture["source_commit"] == source["source_commit"] and capture["source_tree"] == source["source_tree"],
            "Capture did not preserve one complete failed diagnostic")
    check_identities(capture["identity_checks"], CAPTURE_IDENTITIES, "Capture")
    require(same(capture["work_limits"], WORK_LIMITS) and same(capture["budget_limits"], BUDGET_LIMITS)
            and same(capture["work_after_request"], baseline["work"])
            and capture["shared_operations_after_request"] == baseline["operations"]
            and same(capture["original_request"], {"case_id": case, **expected_options}),
            "Capture summary does not agree with original request")
    require(same(capture["callbacks"], {
        "external": {"module": "ontokin.construction", "qualname": "ConstructionBudget.tick",
                     "bound_owner_type": "ConstructionBudget"},
        "construction_check": None, "observer_at_reader_entry": None, "observer_after_request": None}),
        "Native external callback or observer state differs")
    require(Path(capture["driver"]["path"]).resolve() == repo / CAPTURE_PATH,
            "Capture driver is not the executed source-bound collector")
    verify_descriptor(inputs, repo / CAPTURE_PATH, capture["driver"])
    spans = wrapper_spans(repo, inputs)
    baseline_frames, removed_baseline = normalize_frames(baseline["failure"]["frames"], repo, spans, remove_wrappers=False)
    capture_frames, removed = normalize_frames(wrapped["failure"]["frames"], repo, spans, remove_wrappers=True)
    require(not removed_baseline and same(baseline_frames, capture_frames),
            "Underlying failure traceback differs after removing only verified named wrappers")
    require({frame["function"] for frame in removed} >= {"capture_validate_export", "capture_key_comparisons"},
            "Failed request did not traverse the declared reader/key wrappers")
    baseline_text, baseline_text_removed = normalize_traceback_text(baseline["traceback"], repo, spans)
    capture_text, capture_text_removed = normalize_traceback_text(wrapped["traceback"], repo, spans)
    require(not baseline_text_removed and baseline_text == capture_text
            and same(capture_text_removed, removed),
            "Formatted traceback differs beyond the verified named wrapper frame blocks")
    baseline_graph = normalize_graph(baseline["exception_graph"], repo, spans, remove_wrappers=False)
    capture_graph = normalize_graph(wrapped["exception_graph"], repo, spans, remove_wrappers=True)
    require(same(baseline_graph, capture_graph), "Causal exception graph or underlying frames differ")
    require(capture["exception"]["type"] == baseline["failure"]["type"]
            and capture["exception"]["message"] == baseline["failure"]["message"], "Retained original exception differs")
    byte_inputs = []
    for directory, request in ((baseline_dir, baseline), (capture_dir / "diagnostic", wrapped)):
        member = request["unvalidated_reader_input"]
        require(request["accepted_artifact"] is False and member["path"] == case + "/unvalidated-reader-input.glb",
                "Failed bytes have an accepted or unexpected identity")
        byte_inputs.append(verify_descriptor(inputs, directory / relative(member["path"]), member))
    require(capture["artifact"]["path"] == "unvalidated-reader-input.glb", "Unexpected live-capture member")
    byte_inputs.append(verify_descriptor(inputs, capture_dir / "unvalidated-reader-input.glb", capture["artifact"]))
    require(byte_inputs[0] == byte_inputs[1] == byte_inputs[2],
            "Uninstrumented postfailure and captured reader-input bytes differ")
    return repo, case, capture, baseline, wrapped, source, {
        "status": "passed", "product_request_status": "failed",
        "same_original_request_settings": True, "same_complete_work_maps": True,
        "same_final_cache_occupancy": True, "same_diagnostic_and_failure": True,
        "same_underlying_traceback": True, "same_formatted_traceback_after_named_wrapper_removal": True,
        "same_causal_exception_graph": True,
        "same_raw_reader_input_bytes": True, "raw_reader_input_bytes": len(byte_inputs[0]),
        "raw_reader_input_sha256": digest(byte_inputs[0]),
        "same_loaded_runtime_modules": True, "loaded_runtime_module_count": len(baseline_modules),
        "source": source, "removed_wrapper_frames": removed, "underlying_failure_frames": baseline_frames,
        "exception_graph": baseline_graph, "identity_checks": capture["identity_checks"],
        "diagnostic": baseline["diagnostic"], "original_options": expected_options,
        "elapsed_seconds": {"baseline": baseline["elapsed_seconds"], "capture": wrapped["elapsed_seconds"]},
        "elapsed_time_neutrality_claimed": False, "speedup_claimed": False,
    }


def work_valid(record):
    require(type(record) is dict and set(record) == {"operations", "counts", "cache_entries"}
            and type(record["operations"]) is int and record["operations"] >= 0
            and type(record["cache_entries"]) is int and 0 <= record["cache_entries"] <= 256
            and type(record["counts"]) is dict and len(record["counts"]) <= 512
            and all(type(name) is str and type(value) is int and value >= 0 for name, value in record["counts"].items())
            and sum(record["counts"].values()) == record["operations"], "Invalid complete reach work map")


def state(shared, work):
    require(type(shared) is int and shared >= 0, "Invalid shared operation count")
    work_valid(work)
    require(shared >= work["operations"], "Reach operation count exceeds shared count")
    return {"shared_operations": shared, "reach": work}


def diff(first, last):
    state(first["shared_operations"], first["reach"])
    state(last["shared_operations"], last["reach"])
    categories = {name: last["reach"]["counts"].get(name, 0) - first["reach"]["counts"].get(name, 0)
                  for name in set(first["reach"]["counts"]) | set(last["reach"]["counts"])}
    shared = last["shared_operations"] - first["shared_operations"]
    reach = last["reach"]["operations"] - first["reach"]["operations"]
    require(all(value >= 0 for value in categories.values()) and shared >= reach >= 0
            and sum(categories.values()) == reach, "Boundary work delta is not a monotone complete partition")
    categories = {name: categories[name] for name in sorted(categories) if categories[name]}
    return {"shared_operations": shared, "admitted_reach_operations": reach,
            "shared_minus_reach": shared - reach, "reach_category_delta": categories}


def reconcile_ledger(case, capture_dir, capture, request, census, authored, boundaries, tracks, inputs):
    ledger = inputs.json(capture_dir / "key-ledger.json")
    require(ledger["schema_version"] == "ontokin.source-endpoint-ledger/0.1" and ledger["case_id"] == case,
            "Unexpected ledger identity")
    require(tuple(rational(value) for value in ledger["source_boundaries"]) == boundaries,
            "Captured source boundary labels differ from supplied bytes")
    expected_geometry = [{"carrier": carrier["node_index"], "frame": carrier["frame"], "identity": carrier["identity"]}
                         for carrier in census["carriers"]]
    require(same(ledger["geometry"], expected_geometry), "Captured geometry/carrier identities differ from supplied bytes")
    track_rows = ledger["tracks"]
    require(len(track_rows) == census["carrier_count"] and len({row["carrier"] for row in track_rows}) == len(track_rows),
            "Captured track inventory is missing or duplicated")
    for row in track_rows:
        for path in ("translation", "rotation"):
            key = (row["carrier"], path)
            require(key in tracks, "Unknown captured carrier track")
            values, words = tracks[key]
            require(len(row[path]) == len(values) and all(type(value) in (int, float)
                    for vector in row[path] for value in vector), "Captured track length/type differs")
            require(tuple(tuple(Fraction(value) for value in vector) for vector in row[path]) == values,
                    "Captured track values differ from independently decoded binary32 values")
            require([[struct.pack("<f", value) for value in vector] for vector in row[path]]
                    == [[struct.pack("<I", word) for word in vector] for vector in words],
                    "Captured track bits, including zero signs, differ")
    keys = ledger["keys"]
    require(type(keys) is list and keys and len(keys) == capture["key_calls"]
            and len(keys) <= len(authored) and [row["index"] for row in keys] == list(range(len(keys))),
            "Observed keys are not one unreset original prefix")
    require([row["outcome"] for row in keys] == ["returned"] * (len(keys) - 1) + ["raised"],
            "Observed prefix lacks one terminal partial failed key")
    construction = state(request["after_construction"]["shared_operations"], request["after_construction"]["work"])
    reader_entry = state(capture["shared_operations_at_reader_entry"], capture["work_at_reader_entry"])
    final = state(request["operations"], request["work"])
    segments, totals, cursor_rows = [], Counter(), []
    previous = state(0, {"operations": 0, "counts": {}, "cache_entries": 0})

    def add(kind, end, **metadata):
        nonlocal previous
        delta = diff(previous, end)
        segments.append({"ordinal": len(segments), "kind": kind,
            "start_shared_operations": previous["shared_operations"], "end_shared_operations": end["shared_operations"],
            "start_reach_operations": previous["reach"]["operations"], "end_reach_operations": end["reach"]["operations"],
            **metadata, **delta})
        totals.update(delta["reach_category_delta"])
        previous = end
        return delta

    add("construction", construction)
    stages = ledger.get("producer_stages")
    require(type(stages) is list and stages, "No producer stage-boundary evidence")
    prior_stage = "construction_return"
    for ordinal, marker in enumerate(stages):
        require(marker["ordinal"] == ordinal and type(marker["name"]) is str and marker["outcome"] == "returned",
                "Invalid producer stage marker sequence")
        add("producer_between_markers", marker["entry"], after_marker=prior_stage, before_marker=marker["name"])
        marker_delta = add("producer_stage_marker", marker["exit"], marker=marker["name"])
        require(marker_delta["shared_operations"] == marker_delta["admitted_reach_operations"] == 1
                and marker_delta["reach_category_delta"] == {"recording_stage_" + marker["name"]: 1},
                "Original producer marker charge was changed or supplemented")
        prior_stage = marker["name"]
    add("producer_to_reader", reader_entry, after_marker=prior_stage)
    add("reader_setup", keys[0]["entry"])
    key_costs = []
    carriers = set(range(census["carrier_count"]))
    for ordinal, key in enumerate(keys):
        require(key["ordinal"] == ordinal + 1 and rational(key["time"]) == authored[ordinal]
                and key["geometry_count"] == len(carriers), "Captured key index/time/geometry differs")
        if ordinal:
            require(rational(key["previous_time"]) == authored[ordinal - 1]
                    and key["previous_available"] is True and set(key["previous_carriers"]) == carriers
                    and len(key["previous_carriers"]) == len(carriers), "Previous-key context differs")
            add("reader_between_keys", key["entry"], after_key=ordinal - 1, before_key=ordinal)
        else:
            require(key["previous_time"] is None and key["previous_available"] is False
                    and key["previous_carriers"] == [], "First key has unexpected predecessor")
        check_identities(key["identity_checks"], KEY_IDENTITIES, "Key")
        key_delta = add("reader_key", key["exit"], key_index=ordinal, authored_time=key["time"], outcome=key["outcome"])
        require(key_delta["shared_minus_reach"] == (1 if key["outcome"] == "raised" else 0),
                "Key delta does not preserve the observed final refused shared tick")
        key_costs.append({"index": ordinal, "authored_time": key["time"], "outcome": key["outcome"], **key_delta})
        if key["outcome"] == "returned":
            require(len(key["result_carriers"]) == len(carriers) and set(key["result_carriers"]) == carriers,
                    "Returned provisional key lacks its full carrier map")
        else:
            require(key["failure_type"] == request["failure"]["type"], "Partial key failure type differs")
        for boundary in ("entry", "exit"):
            observed = key[boundary]
            require(type(observed["source_cache_entries"]) is int and 0 <= observed["source_cache_entries"] <= 256
                    and sum(observed["source_cache_categories"].values()) == observed["source_cache_entries"],
                    "Reader-cache occupancy and namespace census differ")
            batch = observed["source_batch"]
            require(type(batch) is dict and batch["active"] is True and batch["prepared"] is False,
                    "Captured source batch was already finalized")
            for cursor in observed["source_cursors"]:
                value = cursor["value"]
                require(value["type"] == "_CenteredCursor" and type(value["steps"]) is int
                        and 0 <= value["steps"] <= 64, "Captured cursor exceeds its original update bound")
                rational(value["clock"])
                if ordinal == len(keys) - 1 or value["steps"] == 64:
                    cursor_rows.append({"key_index": ordinal, "boundary": boundary, "cursor_key": cursor["key"],
                                        "steps": value["steps"], "clock": value["clock"]})
    add("reader_unwind_and_exporter_tail", final)
    require(dict(totals) == request["work"]["counts"] and sum(row["shared_operations"] for row in segments) == request["operations"]
            and sum(row["admitted_reach_operations"] for row in segments) == request["work"]["operations"],
            "Disjoint segments fail to telescope to the entire executed request")
    reader_delta = diff(reader_entry, final)
    require(reader_delta["shared_minus_reach"] == 1, "Reader work has an unexplained non-reach charge")
    counts = request["work"]["counts"]
    traversed = counts.get("independent_interval_claim", 0)
    members = counts.get("independent_certificate_member", 0)
    require(type(traversed) is int and 0 <= traversed <= census["certificate_count"]
            and members == traversed, "Observed provisional interval counters differ")
    require(counts.get("independent_certificate_identity", 0) == census["certificate_count"],
            "Certificate identity census differs from actual reader accounting")
    admission = {name: counts.get(name, 0) for name in
                 ("independent_certificate_group_check", "independent_certificate_compare_admission",
                  "independent_certificate_term_admission")}
    return {"scope": "Complete operation ledger for the executed prefix only", "segments": segments,
        "segments_reconcile_exactly": True, "complete_reach_category_totals": dict(sorted(totals.items())),
        "final_shared_operations": request["operations"], "final_reach_operations": request["work"]["operations"],
        "shared_minus_reach_interpretation": "Unclassified construction work plus one observed refused shared tick; no construction category map exists.",
        "final_refused_shared_ticks": 1, "construction": diff(state(0, {"operations": 0, "counts": {}, "cache_entries": 0}), construction),
        "producer_after_construction": diff(construction, reader_entry), "reader": reader_delta,
        "stage_label_limit": "Markers identify existing source-code boundaries; a gap is not automatically one mathematical algorithm.",
        "key_costs": key_costs, "entered_keys": len(keys), "returned_provisional_keys": len(keys) - 1,
        "partial_key": {"index": keys[-1]["index"], "time": keys[-1]["time"]},
        "unvisited_key_indices": list(range(len(keys), len(authored))),
        "provisional_interval_rows_traversed": traversed,
        "interval_rows_not_yet_traversed": census["certificate_count"] - traversed,
        "final_admission_counter_observations": admission,
        "source_batch_finalized_at_refusal": False,
        "cursor_observations": cursor_rows,
        "cursor_observation_limit": "Actual retained fields only; a cursor at 64 updates is not by itself proof of the causal failure.",
        "complete_request_cost": None, "unexecuted_tail_cost": None, "optimization_savings": None,
        "tail_continued": False, "all_captured_tracks_match_supplied_bytes": True}


def audit_failure_locals(repo, case, capture_dir, capture, request, ledger, inputs):
    retained = inputs.json(capture_dir / "failure-locals.json")
    require(retained["schema_version"] == "ontokin.source-endpoint-failure-locals/0.1"
            and retained["case_id"] == case, "Retained failure-local identity differs")
    raw_graph = retained["exception_graph"]
    require(type(raw_graph) is list and 1 <= len(raw_graph) < 16,
            "Missing retained original exception objects")
    ids = {}
    for ordinal, item in enumerate(raw_graph):
        require(set(item) == {"error_object_id", "ordinal", "type", "message", "cause_object_id",
                             "context_object_id", "suppress_context", "frames"}
                and type(item["ordinal"]) is int and item["ordinal"] == ordinal
                and type(item["error_object_id"]) is int and item["error_object_id"] > 0
                and item["error_object_id"] not in ids,
                "Retained exception identity graph is malformed")
        ids[item["error_object_id"]] = ordinal
    graph = []
    for item in raw_graph:
        links = {}
        for name in ("cause", "context"):
            identity = item[name + "_object_id"]
            require(identity is None or type(identity) is int and identity in ids,
                    "Retained exception graph has an unbound edge")
            links[name] = None if identity is None else ids[identity]
        graph.append({name: item[name] for name in ("type", "message", "frames", "suppress_context")} | links)
    require(same(capture["exception"], raw_graph[0]),
            "Capture summary differs from its retained original exception object")
    spans = wrapper_spans(repo, inputs)
    normalized = normalize_graph(graph, repo, spans, remove_wrappers=True)
    baseline = normalize_graph(request["exception_graph"], repo, spans, remove_wrappers=False)
    require(same(normalized, baseline), "Retained object identities do not preserve the causal exception graph")
    known_frames = {canonical(frame) for item in normalized for frame in item["frames"]}
    selected, key_locals = [], []
    require(type(retained["frames"]) is list and retained["frames"], "No precleanup failure-local snapshot")
    for item in retained["frames"]:
        require(set(item) == {"file", "line", "function", "locals"} and type(item["locals"]) is dict,
                "Malformed selected failure-local record")
        location = {name: item[name] for name in ("file", "line", "function")}
        frames, removed = normalize_frames([location], repo, spans, remove_wrappers=False)
        require(not removed and canonical(frames[0]) in known_frames,
                "Selected failure locals do not belong to the observed underlying exception")
        selected.append({**frames[0], "locals": item["locals"]})
        if frames[0]["file"] == "ontokin/reach_conformance.py" and frames[0]["function"] == "_key_comparisons":
            key_locals.append(item["locals"])
    require(len(key_locals) == 1, "Missing unique failed key-local snapshot")
    key = key_locals[0]
    require(type(key["index"]) is int and key["index"] == ledger["partial_key"]["index"]
            and same(key["time"], ledger["partial_key"]["time"]),
            "Retained failure locals disagree with the partial key")
    scalar_names = {"kind", "index", "degree", "exponent", "clock", "time", "steps", "advance", "old_clock", "old_rate"}
    observations = []
    for frame in selected:
        fields = {name: value for name, value in frame["locals"].items() if name in scalar_names}
        node = frame["locals"].get("node")
        if type(node) is dict and type(node.get("path")) is str:
            fields["node_path"] = node["path"]
        if fields:
            observations.append({name: frame[name] for name in ("file", "line", "function")} | {"fields": fields})
    return {"same_retained_causal_exception_graph": True, "graph_object_count": len(raw_graph),
        "process_local_object_ids_are_cross_run_identities": False,
        "snapshot_boundary": retained["snapshot_boundary"], "selected_frames": selected,
        "observed_refusal_locals": observations, "partial_key": ledger["partial_key"],
        "partial_key_provisional_result_carriers": key.get("result_carriers"),
        "pending_carriers_are_unexecuted_cost_estimates": False,
        "failure_mechanism": "The original construction callback refused one shared tick before the reach category was charged.",
        "causal_optimization_or_complete_tail_cost_claimed": False}


def audit_command(path, case, mode, output_dir, repo, source, request, inputs):
    receipt = inputs.json(path)
    require(receipt["schema_version"] == "ontokin.actual-command/0.1"
            and receipt["case_id"] == case and receipt["mode"] == mode
            and receipt["source_commit"] == source["source_commit"]
            and receipt["cwd"] == str(repo) and receipt["output_dir"] == str(output_dir)
            and type(receipt["returncode"]) is int and receipt["returncode"] == 1
            and receipt["timed_out"] is False, "External command identity, real exit status, or output location differs")
    command = receipt["command"]
    require(type(command) is list and all(type(value) is str for value in command)
            and len(command) >= 7 and Path(command[0]).is_absolute() and command[1] == "-B",
            "External command is not the recorded standalone Python invocation")
    script = repo / ("tools/probe_reach_recording_work.py" if mode == "control" else CAPTURE_PATH)
    require(command[2] == str(script), "External command executed another script")
    report = inputs.json(output_dir / ("report.json" if mode == "control" else "diagnostic/report.json"))
    require(command[0] == report["execution"]["executable"]
            and same([command[0], *command[2:]], report["command"]),
            "External command executable or argv differs from the actual diagnostic report")
    if mode == "capture":
        captured = inputs.json(output_dir / "capture.json")
        require(same(captured["actual_driver_command"], report["command"]),
                "Capture driver argv differs from the actual diagnostic report")
    suffix = command[3:]
    require(len(suffix) % 2 == 0 and len(set(suffix[::2])) == len(suffix[::2]),
            "External command contains repeated or incomplete arguments")
    options = dict(zip(suffix[::2], suffix[1::2]))
    expected = {"--case": case, "--output-dir": str(output_dir)}
    if mode == "capture":
        expected["--repo"] = str(repo)
    require(same(options, expected), "External command did not use the exact original diagnostic invocation")
    start, end = datetime.fromisoformat(receipt["started_at"]), datetime.fromisoformat(receipt["finished_at"])
    require(start.tzinfo is not None and end.tzinfo is not None and end >= start
            and type(receipt["elapsed_seconds"]) in (int, float)
            and math.isfinite(receipt["elapsed_seconds"]) and receipt["elapsed_seconds"] >= 0,
            "External execution timing receipt is invalid")
    root = Path(receipt["evidence_root"])
    require(root.is_absolute() and root.resolve() == root and path.resolve().is_relative_to(root),
            "External command receipt is outside its declared evidence root")
    logs = {}
    for stream in ("stdout", "stderr"):
        descriptor = receipt[stream]
        raw = verify_descriptor(inputs, root / relative(descriptor["path"]), descriptor)
        logs[stream] = {"bytes": len(raw), "sha256": digest(raw), "path": descriptor["path"]}
        if stream == "stdout":
            lines = raw.decode("utf-8").splitlines()
            require(lines and lines[0] == f"{case}: failed ({request['operations']} shared operations)",
                    "External stdout does not retain the actual failed request status")
    return {"verified": True, "mode": mode, "command": command, "raw_returncode": receipt["returncode"],
            "timed_out": receipt["timed_out"], "started_at": receipt["started_at"],
            "finished_at": receipt["finished_at"], "elapsed_seconds": receipt["elapsed_seconds"],
            "stdout": logs["stdout"], "stderr": logs["stderr"]}


def compact_summary(case, comparison, census, ledger, failure):
    def top(counts):
        return [{"category": name, "operations": value}
                for name, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:12]]
    return {"case_id": case, "diagnostic_audit_status": "passed", "product_request_status": "failed",
        "accepted_artifact": False, "release_acceptance": False, "complete_stock_harness": False,
        "source_commit": comparison["source"]["source_commit"], "source_tree": comparison["source"]["source_tree"],
        "final_shared_operations": ledger["final_shared_operations"],
        "final_reach_operations": ledger["final_reach_operations"],
        "construction": ledger["construction"], "producer_after_construction": ledger["producer_after_construction"],
        "reader": ledger["reader"], "total_keys_in_supplied_bytes": census["clock_count"],
        "carrier_count": census["carrier_count"], "certificate_count": census["certificate_count"],
        "entered_keys": ledger["entered_keys"], "returned_provisional_keys": ledger["returned_provisional_keys"],
        "partial_key": ledger["partial_key"], "unvisited_keys": len(ledger["unvisited_key_indices"]),
        "provisional_interval_rows_traversed": ledger["provisional_interval_rows_traversed"],
        "interval_rows_not_yet_traversed": ledger["interval_rows_not_yet_traversed"],
        "source_batch_finalized_at_refusal": False,
        "top_request_categories": top(ledger["complete_reach_category_totals"]),
        "top_reader_categories": top(ledger["reader"]["reach_category_delta"]),
        "largest_observed_keys": sorted(ledger["key_costs"], key=lambda row: (-row["admitted_reach_operations"], row["index"]))[:5],
        "observed_refusal_locals": failure["observed_refusal_locals"],
        "complete_request_cost": None, "unexecuted_tail_cost": None, "optimization_savings": None,
        "elapsed_time_neutrality_claimed": False, "speedup_claimed": False,
        "interpretation": "Passing this audit validates diagnostic consistency and the executed-prefix census only. Both original product requests remain failed; retained bytes remain unvalidated."}


def write_json(directory, name, value):
    raw = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode() + b"\n"
    require(len(raw) <= MAX_FILE, "Analysis output exceeds its bounded file cap")
    with (directory / name).open("xb") as stream:
        stream.write(raw)
    return {"path": name, "bytes": len(raw), "sha256": digest(raw)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True, help="Uninstrumented probe output directory")
    parser.add_argument("--capture", type=Path, required=True, help="Instrumented capture output directory")
    parser.add_argument("--output-dir", type=Path, required=True, help="Fresh directory for independent audit outputs")
    parser.add_argument("--baseline-command", type=Path,
                        help="Actual command receipt; defaults to evidence-root/commands/CASE-control.json")
    parser.add_argument("--capture-command", type=Path,
                        help="Actual command receipt; defaults to evidence-root/commands/CASE-capture.json")
    args = parser.parse_args(argv)
    baseline_dir, capture_dir = args.baseline.absolute(), args.capture.absolute()
    output_dir = args.output_dir.absolute()
    require(not output_dir.exists() and not any(p.is_symlink() for p in (output_dir, *output_dir.parents)),
            "Audit output directory must be fresh and use no symlinks")
    require(output_dir.parent.is_dir(), "Audit output parent must already exist")
    output_dir.mkdir()
    inputs = Inputs()
    created = datetime.now(timezone.utc).isoformat()
    provenance = {"schema_version": "ontokin.reach-recording-independent-audit/0.1", "created_at": created,
        "scope": "Failed original P11/L03 request diagnostic; no product/source execution by this auditor",
        "accepted_artifact": False, "release_acceptance": False, "complete_stock_harness": False,
        "source_numeric_accuracy_certified": False, "retained_artifact_validity_certified": False,
        "product_request_status": "failed", "implementation": "Python standard library only",
        "primitive_reader_provenance": {"path": "docs/engineering/reach-recording-validation-2026-10-23/checkpoint-033-census.py",
                                        "sha256": C033_READER_SOURCE_SHA256,
                                        "method": "Primitive bounded rational, GLB/accessor and identity census routines adapted; no import or historical run expectations."},
        "execution": {"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
        "actual_audit_command": [sys.executable, *sys.argv]}
    try:
        own = inputs.read(Path(__file__).absolute())
        provenance["auditor"] = {"bytes": len(own), "sha256": digest(own)}
        repo, case, capture, baseline, wrapped, source, comparison = compare_requests(baseline_dir, capture_dir, inputs)
        census, authored, boundaries, tracks = census_bytes(repo, case, capture_dir, capture, baseline, inputs)
        ledger = reconcile_ledger(case, capture_dir, capture, baseline, census, authored, boundaries, tracks, inputs)
        failure = audit_failure_locals(repo, case, capture_dir, capture, baseline, ledger, inputs)
        commands = []
        for mode, directory, supplied in (("control", baseline_dir, args.baseline_command),
                                          ("capture", capture_dir, args.capture_command)):
            path = supplied.absolute() if supplied is not None else directory.parent.parent / "commands" / (case + "-" + mode + ".json")
            commands.append(audit_command(path, case, mode, directory, repo, source, baseline, inputs))
        receipts = inputs.stable_receipts()
        summary = compact_summary(case, comparison, census, ledger, failure)
        members = [write_json(output_dir, name, value) for name, value in (
            ("summary.json", summary), ("work-ledger.json", ledger), ("byte-census.json", census),
            ("failure-analysis.json", failure), ("input-receipts.json", {"all_inputs_stable": True, "files": receipts}))]
        write_json(output_dir, "audit.json", {**provenance, "status": "passed", "case_id": case,
            "assertions_checked": CHECKS, "comparison": comparison, "actual_command_receipts": commands,
            "members": members, "all_analysis_inputs_stable": True,
            "limitations": ["No source is evaluated and no failed request is resumed.",
                "Numeric certificate fields are decoded and structurally reconciled, not independently certified against source semantics.",
                "Materialized source bytes and the full Git tree identity are verified; omitted tracked payloads are explicitly unverified.",
                "Counter equality and retained identities support this pair's observation neutrality, not timing neutrality or future behavior.",
                "The partial failed key and unvisited tail provide no complete request cost or optimization savings.",
                "The original request failed; this audit is not a release or artifact acceptance."]})
        print(json.dumps({"status": "passed", "case_id": case, "product_request_status": "failed",
                          "release_acceptance": False, "output_dir": str(output_dir)}))
        return 0
    except Exception as error:
        record = {**provenance, "status": "failed", "assertions_checked": CHECKS,
                  "error_type": type(error).__name__, "error": str(error),
                  "traceback": traceback.format_exc(), "all_analysis_inputs_stable": False,
                  "input_receipts_so_far": [inputs.records[name] for name in sorted(inputs.records)]}
        if not (output_dir / "audit.json").exists():
            write_json(output_dir, "audit.json", record)
        print(json.dumps({"status": "failed", "error_type": type(error).__name__, "error": str(error),
                          "output_dir": str(output_dir)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
