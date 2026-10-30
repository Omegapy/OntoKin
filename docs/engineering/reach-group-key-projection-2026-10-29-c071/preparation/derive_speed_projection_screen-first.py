"""Read retained C060 bytes and derive C071's singleton-phase screen.

This standalone helper imports no product modules and executes no product code.
It does not certify the numerical claims in the retained unvalidated GLBs.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def rational(value):
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def inspect_case(case, archive, members, directory):
    name = case + "/capture/unvalidated-reader-input.glb"
    raw = archive.read(name)
    identity = members[name]
    require(len(raw) == identity["bytes"] and sha256(raw) == identity["sha256"],
            case + " retained GLB identity differs")
    magic, version, size = struct.unpack_from("<4sII", raw)
    require(magic == b"glTF" and version == 2 and size == len(raw), "GLB header")
    json_size, json_type = struct.unpack_from("<II", raw, 12)
    require(json_type == 0x4E4F534A, "GLB JSON chunk type")
    document = json.loads(raw[20:20 + json_size])
    binary_header = 20 + json_size
    binary_size, binary_type = struct.unpack_from("<II", raw, binary_header)
    require(binary_type == 0x004E4942 and binary_header + 8 + binary_size == len(raw),
            "GLB binary chunk type and length")
    binary = raw[binary_header + 8:]
    metadata = document["extras"]["ontokin"]
    quantization = metadata["reach_quantization"]
    boundaries = [Fraction(row["source_seconds"]) for row in metadata["boundary_states"]]
    require(boundaries == sorted(set(boundaries)), "source boundary order")
    keys = quantization["retained_keys"]
    authored = [rational(row["authored_seconds"]) for row in keys]
    input_accessors = sorted({sampler["input"] for animation in document["animations"]
                              for sampler in animation["samplers"]})
    arrays = []
    for accessor_index in input_accessors:
        accessor = document["accessors"][accessor_index]
        require(accessor["componentType"] == 5126 and accessor["type"] == "SCALAR",
                "clock accessor scalar binary32")
        view = document["bufferViews"][accessor["bufferView"]]
        require(view.get("buffer", 0) == 0 and "sparse" not in accessor, "clock buffer")
        view_offset = view.get("byteOffset", 0)
        accessor_offset = accessor.get("byteOffset", 0)
        stride = view.get("byteStride", 4)
        count = accessor["count"]
        require(count == len(keys) and count >= 2 and stride >= 4, "clock count/stride")
        require(accessor_offset + (count - 1) * stride + 4 <= view["byteLength"],
                "clock accessor in view")
        require(view_offset + view["byteLength"] <= len(binary), "clock view in buffer")
        values = [struct.unpack_from("<f", binary, view_offset + accessor_offset + i * stride)[0]
                  for i in range(count)]
        require(all(struct.pack("<f", value).hex() ==
                    bytes.fromhex(keys[i]["stored_binary32_bits"])[::-1].hex()
                    for i, value in enumerate(values)), "retained clock bits")
        arrays.append(values)
    require(arrays and all(values == arrays[0] for values in arrays), "one shared clock")
    stored = list(map(Fraction, arrays[0]))
    require(all(Fraction(row["stored_seconds"]) == value for row, value in zip(keys, stored)),
            "retained JSON clocks match binary accessor")
    require(authored == sorted(set(authored)) and stored == sorted(set(stored)),
            "strict authored/stored clock order")
    require(set(boundaries) <= set(authored), "every source boundary retained")
    for boundary in boundaries:
        require(Fraction(struct.unpack("<f", struct.pack("<f", float(boundary)))[0]) == boundary,
                "boundary exactly representable in binary32")
        index = authored.index(boundary)
        require(stored[index] == boundary and keys[index]["semantic_boundary"] is True,
                "semantic boundary stored exactly")
    groups = {}
    intervals_by_phase = Counter()
    selected_by_interval = []
    for index, (left, right) in enumerate(zip(authored, authored[1:])):
        source_index = bisect_right(boundaries, left) - 1
        require(boundaries[source_index] <= left < right <= boundaries[source_index + 1],
                "authored interval lies within one source phase")
        low = max(Fraction(0), min(left, stored[index]))
        high = min(authored[-1], max(right, stored[index + 1]))
        selected = tuple(i for i, (start, end) in enumerate(zip(boundaries, boundaries[1:]))
                         if max(low, start) < min(high, end))
        require(selected == (source_index,), "enclosing phase set is source singleton")
        groups.setdefault((source_index, selected), []).append(index)
        intervals_by_phase[str(source_index)] += 1
        selected_by_interval.append(selected)
    rows = quantization["interval_certificates"]
    carriers = {row["carrier"]["path"] for row in rows}
    identities = set()
    for row in rows:
        index = row["left_key_index"]
        require(row["right_key_index"] == index + 1 and
                tuple(row["source_phase_indices"]) == selected_by_interval[index],
                "certificate phase claim matches exact recomputation")
        identities.add((index, row["carrier"]["path"]))
    require(len(identities) == len(rows) == (len(authored) - 1) * len(carriers),
            "complete unique interval/carrier identity census")
    summary_path = directory / "evidence" / case / "summary.json"
    summary_raw = summary_path.read_bytes()
    summary = json.loads(summary_raw)
    counters = summary["producer_after_construction"]["reach_category_delta"]
    visits = counters["recording_certificate_group"]
    calculations = counters["destination_bound"]
    require(visits == len(groups) * len(carriers), "retained group counter reconciliation")
    return {
        "case": case,
        "member": name,
        "member_bytes": len(raw),
        "member_sha256": sha256(raw),
        "summary_sha256": sha256(summary_raw),
        "boundaries": [str(value) for value in boundaries],
        "actual_binary_clock_accessors": input_accessors,
        "keys": len(keys),
        "intervals_by_phase": dict(intervals_by_phase),
        "carriers": len(carriers),
        "certificate_rows": len(rows),
        "groups": len(groups),
        "all_selected_equal_source_singleton": True,
        "group_visits": visits,
        "baseline_group_calculations": calculations,
        "baseline_group_hits": visits - calculations,
        "new_projected_key_equivalence_hits": 0,
        "bound_speed_recoverable_as": "enclosing.speed",
        "exact_numerical_inputs_reconstructed": False,
        "ordered_lru_events_reconstructed": False,
    }


def derive(repository):
    directory = repository / "docs/engineering/reach-recording-validation-2026-10-28-c060"
    parts_raw = (directory / "evidence.zip.parts.json").read_bytes()
    manifest = json.loads(parts_raw)
    chunks = []
    offset = 0
    for part in manifest["parts"]:
        raw = (directory / part["path"]).read_bytes()
        require(part["offset"] == offset and len(raw) == part["bytes"] and
                sha256(raw) == part["sha256"], "ordered archive part identity")
        chunks.append(raw)
        offset += len(raw)
    raw = b"".join(chunks)
    require(len(raw) == manifest["bytes"] and sha256(raw) == manifest["sha256"],
            "assembled archive identity")
    members_raw = (directory / "evidence.members.json").read_bytes()
    members = {item["path"]: item for item in json.loads(members_raw)["members"]}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        cases = [inspect_case(case, archive, members, directory) for case in ("P11", "L03")]
    return {
        "schema_version": "ontokin.c071-retained-speed-projection-screen/0.1",
        "status": "passed",
        "archive_bytes": len(raw),
        "archive_sha256": sha256(raw),
        "parts_manifest_sha256": sha256(parts_raw),
        "members_manifest_sha256": sha256(members_raw),
        "archive_parts_verified": len(chunks),
        "selected_glb_members_verified": 2,
        "cases": cases,
        "scope": "Static retained-byte census plus native singleton key injectivity",
        "product_imports_executed": 0,
        "product_requests_executed": 0,
        "historical_auditor_rerun": False,
        "numerical_claims_certified": False,
        "original_product_requests_remain_failed": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(derive(arguments.repository), indent=2, sort_keys=True))
