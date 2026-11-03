#!/usr/bin/env python3
"""Compare every unchanged raw geometry, appearance and image stream.

This role compares actual accepted GLBs with the original frozen predecessor
archives and both C5 delivery pairs. It never treats a screenshot as stream
equality. Only the explicitly permitted program-revision scalar and relocated
accessor/image byte addresses are resolved; unknown fields remain in equality.
Complete source/history metadata is separately closed and proved by the byte
reader, not removed or normalized by this focused stream comparison.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import traceback
import zipfile


def sha(raw): return hashlib.sha256(raw).hexdigest()


def unpack(raw):
    assert len(raw) <= 64 * 1024 * 1024
    assert struct.unpack_from("<III", raw) == (0x46546C67, 2, len(raw))
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20 + size])
    binary_size, kind = struct.unpack_from("<II", raw, 20 + size)
    assert kind == 0x004E4942 and len(raw) == 28 + size + binary_size
    return document, raw[28 + size:]


def streams(raw):
    document, binary = unpack(raw)
    revision = document["extras"]["ontokin"]["program"]["revision"]
    changes = []
    def revision_scalar(value, path):
        value = copy.deepcopy(value)
        metadata = value.get("extras", {}).get("ontokin", {})
        if "program_revision" in metadata:
            assert metadata["program_revision"] == revision, path
            changes.append({"pointer": path + "/extras/ontokin/program_revision", "value": revision})
            metadata["program_revision"] = {"independently_identified_program_revision": True}
        return value
    def view(index):
        row = document["bufferViews"][index]
        assert row["buffer"] == 0 and "byteStride" not in row
        start, size = row.get("byteOffset", 0), row["byteLength"]
        assert 0 <= start <= start + size <= len(binary)
        return binary[start:start + size]
    def accessor(index):
        row = copy.deepcopy(document["accessors"][index])
        width = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[row["componentType"]]
        arity = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[row["type"]]
        data = view(row.pop("bufferView")); offset = row.pop("byteOffset", 0)
        size = row["count"] * width * arity
        assert 0 <= offset <= offset + size <= len(data)
        row["resolved_stream_bytes"] = data[offset:offset + size]
        return row
    nodes = {}
    for index, node in enumerate(document["nodes"]):
        metadata = node["extras"]["ontokin"]
        if metadata["kind"] != "object":
            assert metadata["kind"] == "visual_helper"
            continue
        path = metadata["path"]
        assert path not in nodes
        row = {"path": path, "element_id": metadata["element_id"], "mesh": None}
        if "mesh" in node:
            mesh = copy.deepcopy(document["meshes"][node["mesh"]])
            for pi, primitive in enumerate(mesh["primitives"]):
                primitive["attributes"] = {key: accessor(value) for key, value in primitive["attributes"].items()}
                primitive["indices"] = accessor(primitive["indices"])
                mi = primitive["material"]
                primitive["material"] = revision_scalar(document["materials"][mi], f"/materials/{mi}")
            row["mesh"] = mesh
        nodes[path] = row
    images = []
    for index, original in enumerate(document.get("images", [])):
        row = revision_scalar(original, f"/images/{index}")
        data = view(row.pop("bufferView"))
        assert sha(data) == row["extras"]["ontokin"]["sha256"].removeprefix("sha256:")
        assert len(data) == row["extras"]["ontokin"]["byte_length"]
        row["resolved_image_bytes"] = data
        images.append(row)
    return {"nodes": nodes, "images": images, "textures": document.get("textures", []),
            "samplers": document.get("samplers", [])}, changes


def receipts(value):
    if isinstance(value, bytes): return {"sha256": sha(value), "byte_length": len(value)}
    if isinstance(value, dict): return {key: receipts(child) for key, child in value.items()}
    if isinstance(value, list): return [receipts(child) for child in value]
    return value


def compare(left, right, label):
    first, first_changes = streams(left); second, second_changes = streams(right)
    assert first == second, label
    return {"pair": label, "status": "passed", "left_glb_sha256": sha(left),
        "right_glb_sha256": sha(right), "exact_resolved_streams": receipts(first),
        "permitted_program_revision_scalars": {"left": first_changes, "right": second_changes}}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--checkout", type=Path, required=True)
    p.add_argument("--accepted", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(); assert not args.output.exists()
    frozen = args.checkout / "docs/language-design/torque-v0.1/freeze"
    cases = json.loads((frozen / "delivery-cases.json").read_text())["cases"]
    accepted = {}; rows = []; absent = []
    for case in cases:
        folder = args.accepted / case["id"] / "original"
        result = json.loads((folder / "result.json").read_text())
        assert result["status"] == "passed", case["id"]
        raw = (folder / "scene.glb").read_bytes()
        assert sha(raw) == result["artifact"]["sha256"], case["id"]
        accepted[case["physics_case"]] = raw
        archive = frozen / case["predecessor_evidence_archive"]
        member = case["predecessor_case_path"] + "/original.glb"
        with zipfile.ZipFile(archive) as z:
            if member not in z.namelist():
                assert not case["actual_predecessor_artifact_available"], case["id"]
                absent.append({"case": case["id"], "archive": str(archive.relative_to(frozen)),
                    "archive_sha256": sha(archive.read_bytes()), "member": member,
                    "limitation": case["actual_predecessor_limitation"]})
                continue
            assert case["actual_predecessor_artifact_available"], case["id"]
            old = z.read(member)
        row = compare(old, raw, case["id"] + ": frozen predecessor versus .22")
        row.update(predecessor_archive=str(archive.relative_to(frozen)),
                   predecessor_archive_sha256=sha(archive.read_bytes()), predecessor_member=member)
        rows.append(row)
    for first, second in (("p01-spin-up", "p07-same-net-replacement"),
                          ("p19-torque-then-impulse", "p20-impulse-then-torque")):
        rows.append(compare(accepted[first], accepted[second], first + " versus " + second))
    assert len(absent) == 4 and len(rows) == 29
    result = {"schema_version": "ontokin.c091-exact-geometry-streams/1", "status": "passed",
        "harness_sha256": sha(Path(__file__).read_bytes()), "pairs": rows,
        "unpaired_predecessor_failures": absent,
        "scope": "Exact bytes and complete resolved geometry accessor/material/image/texture/sampler values. No unknown fields discarded. Source/history/pose changes remain the separate complete independent-reader obligation."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "passed", "pairs": len(rows), "unpaired": len(absent)}))


if __name__ == "__main__": main()
