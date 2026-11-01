#!/usr/bin/env python3
"""Emit .17 browser expectations from the frozen source math and PNG bytes."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.keyed_merge_reference import (DELIVERED_CASES, FREEZE_COMMIT, FREEZE_SHA256,
    case_payload, decode_png, delivered_by_revision, exact_uv, expected_occurrences, load_fixtures, sha)


def expectations(fixtures):
    by_revision = delivered_by_revision(fixtures)
    cases = {}
    for name in sorted(DELIVERED_CASES):
        case = fixtures["cases"][name]
        payload = case_payload(fixtures, case)
        assets = {}
        for asset in payload["assets"]:
            raw = base64.b64decode(asset["data_base64"], validate=True)
            png = decode_png(raw)
            rgba = png["pixels"] if png["channels"] == 4 else b"".join(png["pixels"][i:i+3]+b"\xff" for i in range(0, len(png["pixels"]), 3))
            width, height = png["width"], png["height"]
            coordinates = sorted({(0,0), (width-1,0), (0,height-1), (width-1,height-1), (width//2,height//2)})
            assets[asset["asset_id"]] = {"asset_id": asset["asset_id"], "png_sha256": sha(raw), "width": width, "height": height,
                "rgba_sha256": sha(rgba), "pixel_probes": [{"xy": [x,y], "uv": [(x+.5)/width,(y+.5)/height],
                    "rgba": list(rgba[(y*width+x)*4:(y*width+x+1)*4])} for x,y in coordinates]}
        nodes = expected_occurrences(case)
        for node in nodes.values():
            points = node.get("raw_corner_set_m", [])
            node["position_keys"] = sorted(struct.pack("<3f", *p).hex() for p in points)
            for binding in node["bindings"].values():
                binding["uv_by_position"] = {struct.pack("<3f", *p).hex(): struct.pack("<2f", *exact_uv(p, binding["mapping"])).hex() for p in points}
            node["materials"] = {region: {"baseColorFactor": value["color"], "metallicFactor": value["metallic"],
                "roughnessFactor": value["roughness"]} for region, value in node["materials"].items()}
        cases[name] = {"name": name, "id": case["id"], "program_revision": case["program_revision"],
            "nodes": nodes, "assets": assets, "used_asset_ids": ["label"], "source_family": "independent rectangular extrusions",
            "target_contract": "ontokin.glb/0.17", "source_profile": "keyed-merge-0.1",
            "color_cpu_reference_absolute_tolerance": 1e-12}
    return {"schema_version": "ontokin.c084-independent-browser-inputs/0.1", "frozen_input_commit": FREEZE_COMMIT,
        "frozen_manifest_sha256": FREEZE_SHA256,
        "named_delivered_cases": len(cases), "unique_delivered_bundles": len(by_revision),
        "expected_answers_source": "Published source-only prism corners/materials/motion, exact original PNG bytes and exact rational affine maps; no produced GLB or runtime imports.",
        "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-merge")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new report file")
    result = expectations(load_fixtures(args.fixtures))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"delivered_source_cases": len(result["cases"]), "sha256": sha(args.output.read_bytes())}))


if __name__ == "__main__":
    main()
