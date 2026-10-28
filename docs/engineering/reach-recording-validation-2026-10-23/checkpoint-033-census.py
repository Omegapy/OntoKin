#!/usr/bin/env python3
"""Independently census original P11/L03 captures; never import OntoKin.

This standard-library reader binds the actual failed stock/capture requests,
decodes every retained clock and carrier track, reconciles all certificate
identities and the observed key prefix, and explains the retained failure locals.
It does not evaluate source poses, certify an export, predict a pass, or measure
the unexecuted tail. Primitive GLB/clock checks extend checkpoint-029's separately
published byte-census method; no product parser or arithmetic is imported.
"""
from __future__ import annotations

import argparse
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


SOURCE = "a7af3ee6ad0a22869b3b26fc45ad4f42f0191c41"
TREE = "28c6b319686c19faba4d468634dfba52b18e037d"
MAX_FILE = 64 * 1024 * 1024
MAX_BITS = 32768
BASE = "docs/language-design/planar-reach-v0.1"
EXPECTED = {
    "P11": {"end": 3, "keys": 52, "carriers": 20, "certificates": 1020,
            "reach_operations": 93277, "boundaries": (0, 2, 3)},
    "L03": {"end": 4, "keys": 178, "carriers": 6, "certificates": 1062,
            "reach_operations": 95767, "boundaries": (0, 2, 3, 4)},
}
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
WORK_LIMITS = {"max_operations": 100000, "max_elapsed_ms": 30000,
               "max_operand_bits": 32768, "max_cache_entries": 256}
BUDGET_LIMITS = {"max_objects": 1000, "max_operations": 100000,
                 "max_result_items": 1000, "max_elapsed_ms": 30000,
                 "max_value_entries": 100000}
WRAPPERS = ("capture_validate_export", "capture_key_comparisons")
CAPTURE_IDENTITIES = {
    "validate_export_restored", "key_comparisons_restored", "native_dispatch_preserved",
    "no_trace_hook", "no_profile_hook", "reader_owner_preserved", "reader_arguments_preserved",
    "reader_external_preserved", "reader_observer_restored", "same_callback_error_at_reader_exit",
    "external_callback_preserved", "native_callback_owner_preserved", "construction_check_preserved",
    "observer_restored_after_request", "callback_error_preserved", "key_reader_exception_identical",
    "work_limits_unchanged", "budget_limits_unchanged",
}
KEY_IDENTITIES = {
    "positional_arguments_preserved", "keyword_arguments_preserved", "work_owner_preserved",
    "source_owners_preserved", "source_check_preserved", "source_observer_restored",
    "external_preserved", "work_observer_preserved", "no_trace_hook", "no_profile_hook",
}
CHECKS = 0


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
    expected = EXPECTED[case]
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
    require(len(clocks) == len(authored) == len(retained) == expected["keys"],
            "Decoded original key count differs")
    require(authored[0] == clocks[0] == 0 and authored[-1] == clocks[-1] == expected["end"],
            "Original complete recording endpoints differ")
    require(all(left < right for left, right in zip(clocks, clocks[1:]))
            and all(left < right for left, right in zip(authored, authored[1:])),
            "Decoded clocks are not strictly increasing")
    boundaries = tuple(clock_text(item["source_seconds"]) for item in metadata["boundary_states"])
    require(boundaries == tuple(Fraction(value) for value in expected["boundaries"]),
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
    require(len(nodes) == expected["carriers"], "Actual original carrier inventory differs")
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
        high = min(Fraction(expected["end"]), max(authored[right], clocks[right]))
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
    require(len(rows) == expected["certificates"] == (len(authored) - 1) * len(nodes)
            and set(rows) == {(key, node) for key in range(len(authored) - 1) for node in range(len(nodes))},
            "Certificate identities do not cover every actual interval/carrier exactly once")
    return {"artifact": {"bytes": len(raw), "sha256": digest(raw), "accepted": False},
        "original_source_files": source, "clock_count": len(authored), "carrier_count": len(nodes),
        "certificate_count": len(rows), "clock_accessors": layouts, "clocks": clock_rows,
        "source_boundaries": [ratio(value) for value in boundaries],
        "source_boundary_records": metadata["boundary_states"], "carriers": carriers,
        "certificates": [rows[key] for key in sorted(rows)],
        "decoded_numeric_fields_are_source_certified": False}, authored, boundaries, decoded_tracks


def work_valid(record):
    require(type(record) is dict and set(record) == {"operations", "counts", "cache_entries"}
            and type(record["operations"]) is int and record["operations"] >= 0
            and type(record["cache_entries"]) is int and 0 <= record["cache_entries"] <= 256
            and type(record["counts"]) is dict and 0 < len(record["counts"]) <= 512
            and all(type(name) is str and type(value) is int and value > 0 for name, value in record["counts"].items())
            and sum(record["counts"].values()) == record["operations"],
            "Complete reach work map is invalid or unreconciled")


def delta(first, last):
    work_valid(first)
    work_valid(last)
    result = {name: last["counts"].get(name, 0) - first["counts"].get(name, 0)
              for name in set(first["counts"]) | set(last["counts"])}
    require(all(value >= 0 for value in result.values()), "Work category count decreased")
    result = {name: result[name] for name in sorted(result) if result[name]}
    require(sum(result.values()) == last["operations"] - first["operations"],
            "Complete operation delta does not equal its category sum")
    return result


def traceback_frames(value):
    return [{"file": name, "line": int(line), "function": function.strip()}
            for name, line, function in re.findall(r'File "([^"]+)", line (\d+), in ([^\n]+)', value)]


def command_check(path, repo, case, output, capture, inputs):
    if path is None:
        return {"checked": False, "reason": "No external command receipt supplied; product statuses are checked separately"}
    command = inputs.json(path)
    require(command["schema_version"] == "ontokin.checkpoint033-command/0.1"
            and command["status"] == "failed" and command["returncode"] == 1
            and not command.get("timeout", False) and command["product_request_limits_modified"] is False,
            "Actual command does not retain its complete failed exit 1")
    require(Path(command["cwd"]).resolve() == repo, "Command cwd differs from the verified source checkout")
    argv = command["command"]
    require(type(argv) is list and "--case" in argv and argv[argv.index("--case") + 1] == case
            and "--output-dir" in argv and Path(argv[argv.index("--output-dir") + 1]).resolve() == output.resolve(),
            "Command case/output does not bind this evidence")
    expected_name = Path(capture["driver"]["path"]).name if capture else "build_reach_source_artifacts.py"
    require(len(argv) >= 2 and Path(argv[1]).name == expected_name, "Actual command invokes another driver")
    if capture:
        require("--repo" in argv and Path(argv[argv.index("--repo") + 1]).resolve() == Path(command["cwd"]).resolve(),
                "Capture command source path/cwd differs")
        require(argv[1:] == capture["actual_driver_command"][1:],
                "Capture's actual command differs from the external command receipt")
    else:
        require("--fps" in argv and Fraction(argv[argv.index("--fps") + 1]) == 1,
                "Stock command changes the original fps")
    streams = {}
    for name in ("stdout", "stderr"):
        member = command[name]
        raw = inputs.read(path.parent / relative(member["path"]))
        require(len(raw) == member["bytes"] and digest(raw) == member["sha256"], "Command stream hash differs")
        streams[name] = raw
    require(streams["stdout"].decode().splitlines()[0] == f"{case}: failed (100001 operations)",
            "Actual stdout does not retain the unchanged failed request")
    return {"checked": True, "returncode": command["returncode"], "status": command["status"],
            "command": argv, "elapsed_seconds": command["elapsed_seconds"],
            "started_at": command["started_at"], "finished_at": command["finished_at"],
            "environment": command["environment"]}


def verify_source(repo, before, inputs):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
    require(before["git"] == {"commit": SOURCE, "tree": TREE, "status": ""},
            "Evidence source is not the identified clean checkpoint032 cut")
    require((git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"),
             git("status", "--porcelain=v1", "--untracked-files=all")) == (SOURCE, TREE, ""),
            "Current source checkout differs from the executed clean cut")
    names = subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"]).decode().split("\0")
    rows = before["files"]
    require([row["path"] for row in rows] == sorted(name for name in names if name),
            "Complete tracked source inventory differs from actual Git index")
    for row in rows:
        raw = inputs.read(repo / relative(row["path"]))
        require(len(raw) == row["bytes"] and "sha256:" + digest(raw) == row["sha256"],
                "Tracked source bytes differ: " + row["path"])
    return {"source_sha": SOURCE, "source_tree": TREE, "files": len(rows),
            "bytes": sum(row["bytes"] for row in rows), "all_named_bytes_verified": True}


def compare_requests(repo, case, stock_dir, capture_dir, commands, inputs, source_before):
    stock_report = inputs.json(stock_dir / "report.json")
    wrapped_report = inputs.json(capture_dir / "stock/report.json")
    stock = inputs.json(stock_dir / case / "request-result.json")
    wrapped = inputs.json(capture_dir / "stock" / case / "request-result.json")
    capture = inputs.json(capture_dir / "capture.json")
    inventories = [inputs.json(directory / name) for directory in (stock_dir, capture_dir / "stock")
                   for name in ("inputs-before.json", "inputs-after.json")]
    require(all(item == inventories[0] for item in inventories), "Stock/capture complete input inventories differ")
    if source_before is not None:
        require(inventories[0] == source_before, "P11/L03 did not execute the same complete source cut")
    for report, request in ((stock_report, stock), (wrapped_report, wrapped)):
        require(report["status"] == request["status"] == "failed" and report["inputs_stable"] is True
                and report["source_commit"] == SOURCE and report["source_tree"] == TREE
                and report["selected_cases"] == [case] and report["deliveries"] == [request]
                and report["release_acceptance"] is False and report["complete_source_delivery_corpus"] is False,
                "Stock or capture report does not preserve actual failed bounded execution")
    expected_options = {"end": str(EXPECTED[case]["end"]), "fps": 1.0, "helpers": False,
        "position_tolerance_m": .001, "rotation_tolerance_rad": .001, "time_tolerance_s": .000001}
    for key in ("case_id", "source_files", "program_revision", "options", "max_operations", "source_manifest",
                "operations", "work", "failure", "diagnostic"):
        require(stock[key] == wrapped[key], "Stock/capture request differs: " + key)
    require(stock["case_id"] == case and stock["options"] == expected_options and stock["max_operations"] == 100000
            and stock["operations"] == 100001 and stock["work"]["operations"] == EXPECTED[case]["reach_operations"]
            and stock["work"]["cache_entries"] == 256, "Fresh original failed-control totals/settings differ")
    work_valid(stock["work"])
    require(stock["diagnostic"]["code"] == "OKL-E-RESOURCE", "Failure diagnostic is not the original resource refusal")
    require(capture["schema_version"] == "ontokin.source-endpoint-capture/0.1"
            and capture["case_id"] == case and capture["observation_errors"] == []
            and capture["status"] == "captured_failed_request" and capture["product_request_status"] == "failed"
            and capture["accepted_artifact"] is False and capture["release_acceptance"] is False
            and capture["source_commit"] == SOURCE and capture["source_tree"] == TREE
            and capture["inputs_stable"] is True and capture["reader_calls"] == 1,
            "Capture summary does not bind one actual failed unvalidated request")
    require(set(capture["identity_checks"]) == CAPTURE_IDENTITIES
            and all(value is True for value in capture["identity_checks"].values()),
            "Capture callback/owner/argument/dispatch/restoration checks are not all true")
    require(capture["callbacks"] == {
        "external": {"module": "ontokin.construction", "qualname": "ConstructionBudget.tick",
                     "bound_owner_type": "ConstructionBudget"},
        "construction_check": None, "observer_at_reader_entry": None, "observer_after_request": None},
        "Capture did not retain the unmodified native budget callback and absent observers")
    require(capture["stock_api_call"] == {"callable": "tools.build_reach_source_artifacts.build",
        "output": str(capture_dir / "stock"), "cases": [case], "fps": 1.0},
        "Capture did not invoke the unchanged stock builder with the original case/fps")
    require(capture["work_limits"] == WORK_LIMITS and capture["budget_limits"] == BUDGET_LIMITS,
            "Capture changed an original request limit")
    require(capture["original_request"] == {"case_id": case, **expected_options}
            and capture["work_after_request"] == stock["work"]
            and capture["shared_operations_after_request"] == stock["operations"],
            "Capture summary options or complete counters differ from stock")
    require(stock_report["execution"] == wrapped_report["execution"] == capture["execution"],
            "Stock/capture interpreter or platform differs")
    driver = inputs.read(Path(capture["driver"]["path"]))
    require(digest(driver) == capture["driver"]["sha256"] and len(driver) == capture["driver"]["bytes"],
            "Capture driver bytes changed after execution")
    stock_frames, wrapped_frames = traceback_frames(stock["traceback"]), traceback_frames(wrapped["traceback"])
    removed = [frame for frame in wrapped_frames if frame["file"] == capture["driver"]["path"]]
    require(len(removed) == 2 and [frame["function"] for frame in removed] == list(WRAPPERS),
            "Traceback contains an unexpected diagnostic wrapper or misses an approved boundary")
    require([frame for frame in wrapped_frames if frame not in removed] == stock_frames,
            "Underlying failure frames differ after removing only named driver wrapper frames")
    require(stock["traceback"].splitlines()[-1] == wrapped["traceback"].splitlines()[-1],
            "Final raw exception message differs")
    require(capture["exception"]["type"] == stock["failure"]["type"]
            and capture["exception"]["message"] == stock["failure"]["message"],
            "Captured exception identity/type/message differs")
    require(capture["exception"]["frames"] == wrapped_frames,
            "Retained exception frame graph differs from the full builder traceback")
    reader_categories = delta(capture["work_at_reader_entry"], capture["work_after_request"])
    reader_shared = capture["shared_operations_after_request"] - capture["shared_operations_at_reader_entry"]
    require(reader_shared == sum(reader_categories.values()) + 1,
            "Reader shared/reach delta does not preserve the final refused shared charge")
    command_rows = {"stock": command_check(commands[0], repo, case, stock_dir, None, inputs),
                    "capture": command_check(commands[1], repo, case, capture_dir, capture, inputs)}
    return capture, stock, inventories[0], {"status": "passed", "product_status": "failed",
        "source_sha": SOURCE, "source_tree": TREE, "inputs_identical_and_stable": True,
        "settings": expected_options, "shared_operations": stock["operations"], "reach_work": stock["work"],
        "complete_reach_category_maps_identical": True, "final_request_cache_occupancy_identical": True,
        "shared_minus_reach_operations": stock["operations"] - stock["work"]["operations"],
        "shared_minus_reach_interpretation": "Derived unclassified construction work, including the final refused shared charge; ConstructionBudget has no native category map.",
        "reader_entry_shared_operations": capture["shared_operations_at_reader_entry"],
        "reader_entry_reach_work": capture["work_at_reader_entry"],
        "reader_shared_operations": reader_shared, "reader_admitted_reach_categories": reader_categories,
        "final_refused_shared_charges": 1,
        "callback_and_dispatch_identity_checks": capture["identity_checks"], "callbacks": capture["callbacks"],
        "underlying_failure_frames": stock_frames, "removed_wrapper_frames": removed,
        "diagnostic": stock["diagnostic"], "failure": stock["failure"], "commands": command_rows,
        "elapsed_seconds": {"stock_request": stock["elapsed_seconds"], "capture_request": wrapped["elapsed_seconds"]},
        "elapsed_neutrality_claimed": False, "elapsed_speedup_claimed": False}


def record_fields(record):
    require(type(record) is dict, "Expected detached native object fields")
    return record["fields"] if set(record) == {"type", "fields"} else record


def failure_analysis(case, capture_dir, capture, last_key, census, tracks, inputs):
    failure = inputs.json(capture_dir / "failure-locals.json")
    require(failure["schema_version"] == "ontokin.source-endpoint-failure-locals/0.1"
            and failure["case_id"] == case and type(failure["frames"]) is list and failure["frames"],
            "Missing selected actual failure-frame locals")
    require(failure["exception_graph"] and failure["exception_graph"][0] == capture["exception"],
            "Failure locals are not bound to the retained original exception")
    graph_frames = capture["exception"]["frames"]
    require(all({name: frame[name] for name in ("file", "line", "function")} in graph_frames
                for frame in failure["frames"]), "Selected locals name a frame outside the original failure")
    def selected(function, filename):
        return [frame for frame in failure["frames"]
                if frame["function"] == function and Path(frame["file"]).name == filename]
    keys = selected("_key_comparisons", "reach_conformance.py")
    require(len(keys) == 1 and all(frame["locals"]["index"] == last_key["index"]
            and rational(frame["locals"]["time"]) == rational(last_key["time"])
            and frame["locals"]["previous_time"] == last_key["previous_time"] for frame in keys),
            "Failure frames do not bind the actual partially attempted key")
    key_local = keys[0]["locals"]
    carriers = {row["node_index"]: row for row in census["carriers"]}
    require(len(key_local["observed"]) == len(carriers)
            and {item["carrier"] for item in key_local["observed"]} == set(carriers),
            "Failed key did not observe every original carrier exactly once")
    for collection in (key_local["observed"], key_local["pending"]):
        for item in collection:
            carrier = item["carrier"]
            require(carrier in carriers and item["frame"] == carriers[carrier]["frame"],
                    "Failed-key frame/carrier mapping differs from the supplied GLB")
            for name, path in (("position", "translation"), ("quaternion", "rotation")):
                values, all_words = tracks[carrier, path]
                words = all_words[last_key["index"]]
                require(all(type(value) in (int, float) for value in item[name])
                        and tuple(Fraction(value) for value in item[name]) == values[last_key["index"]],
                        "Failed-key native pose values are not exactly the independently decoded binary32 values")
                require([struct.pack("<f", value).hex() for value in item[name]]
                        == [struct.pack("<I", word).hex() for word in words],
                        "Failed-key observed or pending pose differs from its original track bytes")
    partial = key_local["result_carriers"]
    pending = [item["carrier"] for item in key_local["pending"]]
    require(len(set(partial)) == len(partial) and len(set(pending)) == len(pending)
            and not set(partial).intersection(pending) and set(partial).union(pending) == set(carriers),
            "Partial endpoint results and pending centered endpoints do not partition the actual carriers")
    evaluations = selected("evaluate", "reach_reference_center.py")
    require(len(evaluations) == 1
            and rational(evaluations[0]["locals"]["time"]) == rational(last_key["time"]),
            "Failure lacks the original centered source evaluation frame at the actual key clock")
    result = {"observed_partial_key_index": last_key["index"], "observed_partial_key_time": last_key["time"],
              "selected_failure_frames": failure["frames"], "original_exception_graph": failure.get("exception_graph"),
              "provisional_endpoint_result_carriers_before_failure": partial,
              "pending_centered_endpoint_carriers_at_failure": pending,
              "observed_pose_carriers": [item["carrier"] for item in key_local["observed"]],
              "source_pose_certified": False}
    if case == "L03":
        frames = selected("_orientation", "reach_reference_center.py")
        require(frames, "L03 failure lacks the direct source orientation frame")
        local = frames[-1]["locals"]
        require(local["advance"] is False, "L03 did not fail through the direct reseed branch")
        node = record_fields(local["node"])
        body = record_fields(local.get("body", node.get("body")))
        require(rational(local["clock"]) == rational(last_key["time"])
                and node["path"] == body["path"] and local["axis"] == body["axis"],
                "Orientation failure does not bind its actual source node, clock and axis")
        previous = local["previous"]
        reasons, conditions = [], {}
        if previous is None:
            reasons.append("no_previous_cursor")
        else:
            previous = record_fields(previous)
            rate, clock = rational(local["rate"]), rational(local["clock"])
            old_rate, old_clock = rational(local["old_rate"]), rational(local["old_clock"])
            conditions = {"source_witness_equal": previous["witness"] == body["witness"],
                "axis_equal": previous["axis"] == local["axis"], "rate_equal": old_rate == rate,
                "clock_strictly_increases": old_clock < clock, "prior_steps_below_64": previous["steps"] < 64}
            require(type(previous["steps"]) is int and 0 <= previous["steps"] <= 64,
                    "Previous source cursor step count is invalid")
            reasons.extend(name for name, passed in conditions.items() if not passed)
            if all(conditions.values()) and "delta" in local:
                conditions["half_angle_delta_at_most_quarter"] = abs(rational(local["delta"])) <= Fraction(1, 4)
                if not conditions["half_angle_delta_at_most_quarter"]:
                    reasons.append("half_angle_delta_exceeds_quarter")
            require(rational(previous["clock"]) == old_clock and rational(previous["rate"]) == old_rate,
                    "Frozen previous cursor operands disagree with actual local operands")
        require(bool(reasons), "Captured local operands do not establish why direct reseeding occurred")
        series = selected("_series_integer", "reach_reference.py")
        coefficients = selected("_series_coefficients", "reach_reference.py")
        require(len(series) == len(coefficients) == 1, "Missing original reseed coefficient failure locals")
        operation, coefficient = series[0]["locals"], coefficients[0]["locals"]
        require(operation["kind"] == "div" and operation["a"] == coefficient["common"]
                and type(operation["b"]) is int and operation["b"] > 0
                and coefficient["odd"] == 2 * coefficient["index"] + 1,
                "Direct reseed failure is not the captured coefficient integer division")
        result.update(kind="observed_direct_orientation_reseed", source_node_path=node["path"],
                      reseed_gate_conditions=conditions, failed_reseed_gate_conditions=reasons,
                      prior_cursor_steps=None if previous is None else previous["steps"],
                      source_clock=local["clock"], previous_clock=local.get("old_clock"),
                      refused_integer_operation={**operation, "coefficient_index": coefficient["index"],
                          "odd_factorial_index": coefficient["odd"], "degree": coefficient["degree"],
                          "exponent": coefficient["exponent"], "performed": False,
                          "refusal_site": series[0]["line"]},
                      completed_source_frames_before_failure=evaluations[-1]["locals"].get("completed_frames"),
                      exact_reason_established_from_failure_locals=True,
                      optimization_selected=False)
    else:
        offsets = selected("_offset", "reach_reference_center.py")
        products = selected("product", "reach_reference_center.py")
        require(offsets and products, "P11 failure lacks its actual centered offset/product frames")
        local, evaluation = offsets[-1]["locals"], evaluations[-1]["locals"]
        node = record_fields(evaluation["node"])
        product = products[-1]["locals"]
        exacts = selected("exact", "reach_reference.py")
        require(len(exacts) == 1 and exacts[0]["locals"]["kind"] == "mul"
                and rational(exacts[0]["locals"]["a"]) == rational(product["first"])
                and rational(exacts[0]["locals"]["b"]) == rational(product["last"]),
                "Original refused exact multiplication differs from the actual offset product")
        matches = [name for name, first, last in (("diagonal_times_x", "diagonal", "x"),
                                                ("cross_times_y", "cross", "y"))
                   if rational(local[first]) == rational(product["first"])
                   and rational(local[last]) == rational(product["last"])]
        require(len(matches) == 1, "Offset locals do not uniquely identify the refused product on this source line")
        result.update(kind="observed_centered_offset_product", source_node_path=node["path"],
                      source_node_kind=node.get("kind"), source_parent_path=node.get("parent"),
                      offset_operands=local, product_operands=product,
                      exact_refused_product=matches[0], refused_operation_performed=False,
                      source_line=offsets[-1]["line"],
                      completed_source_frames_before_failure=evaluation.get("completed_frames"),
                      optimization_selected=False)
    return result


def reconcile_ledger(case, capture_dir, capture, census, authored, boundaries, tracks, inputs):
    ledger = inputs.json(capture_dir / "key-ledger.json")
    require(ledger["schema_version"] == "ontokin.source-endpoint-ledger/0.1"
            and ledger["case_id"] == case and type(ledger["keys"]) is list and ledger["keys"],
            "Missing actual key-entry/return/failure ledger")
    require(tuple(rational(value) for value in ledger["source_boundaries"]) == boundaries,
            "Captured source boundaries differ from the independently decoded input")
    expected_geometry = [{"carrier": carrier["node_index"], "frame": carrier["frame"], "identity": carrier["identity"]}
                         for carrier in census["carriers"]]
    require(ledger["geometry"] == expected_geometry, "Captured geometry/carrier frame mapping differs from bytes")
    keys = ledger["keys"]
    require(capture["key_calls"] == len(keys), "Capture key-call total differs from its native index ledger")
    require([key["index"] for key in keys] == list(range(len(keys))) and len(keys) <= len(authored),
            "Observed key calls are not one unreplayed original prefix")
    require([key["outcome"] for key in keys] == ["returned"] * (len(keys) - 1) + ["raised"],
            "Ledger does not end in exactly one partly attempted failed key")
    carriers = list(range(census["carrier_count"]))
    rows, previous_exit = [], None
    total_categories = Counter()
    before_first = {"shared_operations": keys[0]["entry"]["shared_operations"]
                    - capture["shared_operations_at_reader_entry"],
                    "reach_categories": delta(capture["work_at_reader_entry"], keys[0]["entry"]["reach"])}
    require(before_first["shared_operations"] == sum(before_first["reach_categories"].values()),
            "Reader work preceding the first key has unreconciled shared charges")
    reader_categories = Counter(before_first["reach_categories"])
    for ordinal, key in enumerate(keys):
        index = key["index"]
        require(key["ordinal"] == ordinal + 1 and rational(key["time"]) == authored[index]
                and key["geometry_count"] == len(carriers), "Captured key index/time/geometry differs")
        require((key["previous_time"] is None and key["previous_carriers"] == []
                 and key["previous_available"] is False) if index == 0 else
                (rational(key["previous_time"]) == authored[index - 1] and key["previous_available"] is True
                 and len(key["previous_carriers"]) == len(carriers) and set(key["previous_carriers"]) == set(carriers)),
                "Observed previous-key map differs from the independently decoded adjacent clock")
        require(set(key["identity_checks"]) == KEY_IDENTITIES
                and all(value is True for value in key["identity_checks"].values()),
                "A key wrapper changed argument/owner/callback identity")
        entry, end = key["entry"], key["exit"]
        categories = delta(entry["reach"], end["reach"])
        total_categories.update(categories)
        reader_categories.update(categories)
        shared = end["shared_operations"] - entry["shared_operations"]
        reach = end["reach"]["operations"] - entry["reach"]["operations"]
        require(shared == reach + (1 if key["outcome"] == "raised" else 0),
                "Source key shared/reach charges do not preserve the final refused charge")
        require(categories.get("independent_key_pose", 0) == len(carriers),
                "Observed key does not enter every supplied carrier's key-pose check")
        for state in (entry, end):
            require(type(state["source_cache_entries"]) is int and 0 <= state["source_cache_entries"] <= 256,
                    "Captured independent source cache exceeds its unchanged cap")
            require(sum(state["source_cache_categories"].values()) == state["source_cache_entries"],
                    "Source cache category inventory does not equal its actual occupancy")
            batch = state["source_batch"]
            require(batch is not None and batch["active"] is True and batch["prepared"] is False
                    and 0 <= batch["cursor_ledger_entries"] <= 256
                    and len(batch["plans"]) <= 16, "Original source batch was finalized or changed before refusal")
        between = None
        if previous_exit is not None:
            between = {"shared_operations": entry["shared_operations"] - previous_exit["shared_operations"],
                       "reach_categories": delta(previous_exit["reach"], entry["reach"])}
            require(between["shared_operations"] == sum(between["reach_categories"].values()),
                    "Inter-key work category accounting differs")
            reader_categories.update(between["reach_categories"])
        if key["outcome"] == "returned":
            require(len(key["result_carriers"]) == len(carriers) and set(key["result_carriers"]) == set(carriers),
                    "Returned key lacks complete carrier endpoint results")
        else:
            require(key["failure_type"] == capture["exception"]["type"],
                    "Final key exception type differs from the original failed request")
        source_phase = max(position for position, boundary in enumerate(boundaries) if boundary <= authored[index])
        rows.append({"index": index, "authored_time": key["time"], "stored_time": census["clocks"][index]["stored"],
            "semantic_boundary": authored[index] in boundaries,
            "source_after_phase_index": source_phase if source_phase < len(boundaries) - 1 else None,
            "terminal_boundary": authored[index] == boundaries[-1],
            "outcome": key["outcome"], "shared_operations": shared, "admitted_reach_operations": reach,
            "reach_category_delta": categories, "preceding_inter_key_work": between,
            "source_cache_at_entry": entry["source_cache_entries"], "source_cache_at_exit": end["source_cache_entries"]})
        previous_exit = end
    require(previous_exit["shared_operations"] == capture["shared_operations_after_request"]
            and previous_exit["reach"] == capture["work_after_request"],
            "Post-key request counters changed after the final refusal")
    require(dict(reader_categories) == delta(capture["work_at_reader_entry"], capture["work_after_request"]),
            "Pre-key, per-key and inter-key maps do not exactly partition all admitted reader work")
    completed = len(keys) - 1
    complete_intervals = max(0, completed - 1)
    counts = capture["work_after_request"]["counts"]
    required_counts = {"independent_retained_clock": len(authored), "independent_source_geometry": len(carriers),
        "independent_key_pose": len(keys) * len(carriers), "independent_interval_claim": complete_intervals * len(carriers),
        "independent_certificate_member": complete_intervals * len(carriers),
        "independent_certificate_identity": census["certificate_count"],
        "independent_certificate_group_check": 0, "independent_certificate_compare_admission": 0,
        "independent_certificate_term_admission": 0}
    require(all(counts.get(name, 0) == value for name, value in required_counts.items()),
            "Actual source/certificate counter stages differ from observed key prefix")
    track_snapshot = ledger["tracks"]
    require(len(track_snapshot) == len(carriers),
            "Captured track inventory is missing or incomplete")
    for item in track_snapshot:
        carrier = item["carrier"]
        require(carrier in carriers, "Captured track names an unknown carrier")
        for path in ("translation", "rotation"):
            supplied = item[path]
            values, words = tracks[carrier, path]
            require(len(supplied) == len(words), "Captured full track key count differs")
            require(all(type(value) in (int, float) for row in supplied for value in row)
                    and tuple(tuple(Fraction(value) for value in row) for row in supplied) == values,
                    "Captured native full-track values are not exactly the independently decoded binary32 values")
            actual_bits = [[struct.pack("<f", value).hex() for value in row] for row in supplied]
            expected_bits = [[struct.pack("<I", word).hex() for word in row] for row in words]
            require(actual_bits == expected_bits, "Captured original track values differ from binary32 bytes")
    require(len({item["carrier"] for item in track_snapshot}) == len(carriers),
            "Captured track repeats a carrier")
    failure = failure_analysis(case, capture_dir, capture, keys[-1], census, tracks, inputs)
    return {"observed_key_calls": len(keys), "completed_key_calls": completed,
        "completed_key_calls_remain_provisional_until_final_source_admission": True,
        "partial_final_key_index": keys[-1]["index"], "partial_final_key_time": keys[-1]["time"],
        "full_original_key_count": len(authored), "unvisited_key_indices": list(range(len(keys), len(authored))),
        "entered_key_pose_charges_are_completed_source_poses": False,
        "completed_interval_rows": complete_intervals * len(carriers),
        "completed_interval_rows_interpretation": "Provisional interval-claim/member traversal and addition only; final certificate comparison/flush and final source admission have not occurred.",
        "remaining_interval_rows": census["certificate_count"] - complete_intervals * len(carriers),
        "complete_counter_reconciliation": required_counts, "all_captured_tracks_match_original_bytes": True,
        "raw_observed_key_ledger": ledger,
        "raw_context_note": "Opaque identities are meaningful only within this request. source_batch.plans.registered_time is the plan's first registration time, not the current key clock.",
        "reader_work_before_first_key": before_first,
        "key_work_rows": rows, "all_key_category_delta_totals": dict(sorted(total_categories.items())),
        "failure": failure,
        "tail": {"kind": "remaining_obligations_not_a_measured_or_predicted_complete_cost",
            "unvisited_key_calls": len(authored) - len(keys), "partly_attempted_key_calls": 1,
            "interval_rows_not_yet_traversed": census["certificate_count"] - complete_intervals * len(carriers),
            "interval_rows_without_final_admission": census["certificate_count"],
            "final_certificate_comparison_flush_started": False, "final_source_admission_completed": False,
            "measured_complete_operations": None, "conditional_complete_operation_estimate": None,
            "reason_no_cost_estimate": "Unvisited source branch costs and the final certificate/source-admission work were not executed; captured entry counts cannot establish their total.",
            "continuation_assumptions": ["same original bytes and numerical domain", "no replay or further failure",
                "all remaining source and certificate obligations pass under the original callbacks and caps"]}}


def concise_summary(comparison, census, prefix):
    failure, last = prefix["failure"], prefix["key_work_rows"][-1]
    explanation = {"source_node_path": failure["source_node_path"], "kind": failure["kind"]}
    if "failed_reseed_gate_conditions" in failure:
        explanation.update(failed_advance_conditions=failure["failed_reseed_gate_conditions"],
                           evaluated_advance_conditions=failure["reseed_gate_conditions"],
                           prior_cursor_steps=failure["prior_cursor_steps"],
                           refused_integer_operation=failure["refused_integer_operation"])
    else:
        explanation.update(refused_product=failure["exact_refused_product"],
                           source_parent_path=failure["source_parent_path"])
    return {
        "observations": {"product_status": "failed", "stock_capture_neutrality": comparison["status"],
            "shared_operations": comparison["shared_operations"],
            "admitted_reach_operations": comparison["reach_work"]["operations"],
            "native_cache_entries": comparison["reach_work"]["cache_entries"],
            "original_keys": census["clock_count"], "original_carriers": census["carrier_count"],
            "original_interval_certificates": census["certificate_count"],
            "entered_key_calls": prefix["observed_key_calls"],
            "returned_provisional_key_calls": prefix["completed_key_calls"],
            "partly_attempted_final_key_index": prefix["partial_final_key_index"],
            "partly_attempted_final_key_time": prefix["partial_final_key_time"],
            "partial_key_shared_delta": last["shared_operations"],
            "partial_key_admitted_reach_delta": last["admitted_reach_operations"],
            "partial_key_provisional_result_carriers": failure["provisional_endpoint_result_carriers_before_failure"],
            "partial_key_pending_carriers": failure["pending_centered_endpoint_carriers_at_failure"]},
        "inferences_from_frozen_source_and_observed_locals": explanation,
        "derived_remaining_obligations": {"unvisited_key_calls": prefix["tail"]["unvisited_key_calls"],
            "provisionally_registered_interval_rows": prefix["completed_interval_rows"],
            "interval_rows_not_yet_registered": prefix["remaining_interval_rows"],
            "interval_rows_without_final_admission": census["certificate_count"],
            "final_source_and_certificate_admission_completed": False},
        "unmeasured": {"complete_request_cost": None, "optimization_savings": None,
            "future_success_under_original_caps": None},
        "interpretation": "Entered carrier charges are not completed source poses. Returned endpoints and interval members remain provisional; neither original request produced an accepted export."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--stock-p11", type=Path, required=True)
    parser.add_argument("--capture-p11", type=Path, required=True)
    parser.add_argument("--stock-l03", type=Path, required=True)
    parser.add_argument("--capture-l03", type=Path, required=True)
    for name in ("stock-p11", "capture-p11", "stock-l03", "capture-l03"):
        parser.add_argument("--" + name + "-command", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    repo, output, inputs = args.repo.resolve(), args.output.absolute(), Inputs()
    require(not output.exists() and not output.is_relative_to(repo), "Use a fresh analysis output outside the source checkout")
    require(output.parent.is_dir(), "Analysis output parent must already exist")
    require(not any(path.is_symlink() for path in (output, *output.parents)),
            "Analysis output must not traverse a symlink")
    record = {"schema_version": "ontokin.source-endpoint-census/0.1", "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        "execution": {"python": sys.version, "platform": platform.platform(), "executable": sys.executable},
        "source_sha": SOURCE, "source_tree": TREE, "imports_ontokin": False, "product_runtime_executed": False,
        "source_poses_independently_certified": False, "successful_export_claimed": False,
        "measured_full_cost_claimed": False, "measured_savings_claimed": False,
        "elapsed_neutrality_claimed": False, "release_acceptance": False, "full_product_goal_completed": False,
        "cases": {}}
    try:
        inputs.read(Path(__file__).resolve())
        common = None
        for case in ("P11", "L03"):
            name = case.lower()
            stock_dir, capture_dir = getattr(args, "stock_" + name).resolve(), getattr(args, "capture_" + name).resolve()
            commands = (getattr(args, "stock_" + name + "_command"), getattr(args, "capture_" + name + "_command"))
            capture, request, before, comparison = compare_requests(repo, case, stock_dir, capture_dir, commands, inputs, common)
            if common is None:
                common = before
                record["source_verification"] = verify_source(repo, before, inputs)
            census, authored, boundaries, tracks = census_bytes(repo, case, capture_dir, capture, request, inputs)
            prefix = reconcile_ledger(case, capture_dir, capture, census, authored, boundaries, tracks, inputs)
            record["cases"][case] = {"summary": concise_summary(comparison, census, prefix),
                                     "stock_capture_neutrality": comparison, "independent_input_census": census,
                                     "observed_source_prefix": prefix}
        record["status"] = "passed"
    except Exception as error:
        record.update(status="failed", failure={"type": type(error).__name__, "message": str(error)},
                      traceback=traceback.format_exc())
    try:
        record["inputs"] = inputs.stable_receipts()
        record["inputs_stable"] = True
    except Exception as error:
        record.update(status="failed", inputs_stable=False,
                      input_verification_failure={"type": type(error).__name__, "message": str(error)})
    record["evidence_checks"] = CHECKS
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    raw = (json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= MAX_FILE, "Generated census exceeds bounded output size")
    with output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"status": record["status"], "evidence_checks": record["evidence_checks"],
        "cases": {case: {"keys": item["independent_input_census"]["clock_count"],
            "carriers": item["independent_input_census"]["carrier_count"],
            "certificates": item["independent_input_census"]["certificate_count"],
            "partial_key_index": item["observed_source_prefix"]["partial_final_key_index"]}
            for case, item in record["cases"].items()}, "output_bytes": len(raw), "output_sha256": digest(raw)}), flush=True)
    return 0 if record["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
