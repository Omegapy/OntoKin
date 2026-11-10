#!/usr/bin/env python3
"""Independent field/byte/native-sample checks around the frozen C190 bound."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c190_glb_difference import array, compare, decode

TIMES = (np.arange(481, dtype=float) / 240).astype("<f4").astype(float)
PARTS = {"base", "left_carriage", "left_shoe", "left_stop", "right_carriage", "right_shoe", "right_stop"}


def audit(raw_path, final_path, native_path):
    result = compare(raw_path, final_path, native_path)
    raw, raw_bin = decode(raw_path)
    final, final_bin = decode(final_path)
    native = json.loads(Path(native_path).read_text())
    assert len(native) == 481
    assert all(row["frame"] == i and row["time_s"] == i / 240 for i, row in enumerate(native))
    assert all(set(row["matrices_blender_m"]) == PARTS and set(row["bounds_gltf_mm"]) == PARTS for row in native)
    assert result["staticMeshesIdentical"] and result["materialsIdentical"] and result["geometryAccessorValuesIdentical"]
    assert result["maximumNativeSampleToFinalVertexDistanceMm"] <= .2
    assert result["maximumRecordedVertexDistanceMm"] <= .2
    assert result["maximumContinuousRawToFinalVertexDeviationBoundMm"] <= .2
    assert raw["nodes"] == final["nodes"] and raw["bufferViews"] == final["bufferViews"]
    assert len(raw_bin) == len(final_bin)
    expected_channels = [channel for channel in raw["animations"][0]["channels"]
        if not (channel["target"]["path"] == "rotation" and
                raw["nodes"][channel["target"]["node"]]["name"] in ("left_carriage", "right_carriage"))]
    assert final["animations"][0]["channels"] == expected_channels, "Unexpected final channel change"
    changed_outputs = set()
    allowed_byte_positions = set()
    x_proofs = {}
    for doc, blob in ((raw, raw_bin), (final, final_bin)):
        assert {node["name"] for node in doc["nodes"] if "mesh" in node} == PARTS
        for sampler in doc["animations"][0]["samplers"]:
            assert np.array_equal(array(doc, blob, sampler["input"])[:, 0], TIMES), "Not every track has 481 common keys"
    for channel in raw["animations"][0]["channels"]:
        name = raw["nodes"][channel["target"]["node"]]["name"]
        if channel["target"]["path"] != "translation":
            continue
        assert name in ("left_carriage", "right_carriage"), "Unexpected translated native node"
        sampler = raw["animations"][0]["samplers"][channel["sampler"]]
        output = sampler["output"]
        old_values, new_values = array(raw, raw_bin, output), array(final, final_bin, output)
        expected = np.array([[row["matrices_blender_m"][name][0][3],
                              row["matrices_blender_m"][name][2][3],
                             -row["matrices_blender_m"][name][1][3]] for row in native], dtype="<f4").astype(float)
        assert np.array_equal(old_values, expected), "Raw translation changed native samples: " + name
        assert np.array_equal(old_values[:, 0], new_values[:, 0]), "Final X changed"
        x_proofs[name] = {"native_samples": 481, "raw_native_xyz_float32_equal": True,
                         "raw_final_x_float32_equal": True}
        if not np.array_equal(old_values, new_values):
            changed_outputs.add(output)
        ac = raw["accessors"][output]
        view = raw["bufferViews"][ac["bufferView"]]
        start = view.get("byteOffset", 0) + ac.get("byteOffset", 0)
        stride = view.get("byteStride", 12)
        for row in range(ac["count"]):
            for component in (1, 2):
                allowed_byte_positions.update(range(start + row * stride + component * 4,
                                                   start + row * stride + component * 4 + 4))
    assert set(x_proofs) == {"left_carriage", "right_carriage"}
    byte_changes = [i for i, (old, new) in enumerate(zip(raw_bin, final_bin)) if old != new]
    assert set(byte_changes).issubset(allowed_byte_positions), "Unreported binary field changed"
    for change in result["logicalAccessorChanges"]:
        assert change["accessor"] in changed_outputs
        for row in change["values"]:
            assert row["before"][0] == row["after"][0]
    for change in result["jsonFieldChanges"]:
        path = change["path"]
        if path == "/animations/0/channels":
            continue
        segments = path.split("/")
        assert (len(segments) == 5 and segments[1] == "accessors" and
                int(segments[2]) in changed_outputs and segments[3] in ("min", "max") and
                segments[4] in ("1", "2")), "Unreported semantic JSON change: " + path
    result.update(version="C191-independent-mapping-audit-1", passed=True,
        native_time_sequence_exact=True, every_raw_final_sampler_has_common_481_keys=True,
        native_translation_proofs=x_proofs, changed_binary_byte_count=len(byte_changes),
        changed_binary_byte_positions=byte_changes, all_other_binary_bytes_identical=True,
        all_changes_limited_to_declared_projection=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("final", type=Path)
    parser.add_argument("native", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.raw, args.final, args.native)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"pass": result["passed"], "continuous_bound_mm": result["maximumContinuousRawToFinalVertexDeviationBoundMm"],
        "native_sample_bound_mm": result["maximumNativeSampleToFinalVertexDistanceMm"]}))
