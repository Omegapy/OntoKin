#!/usr/bin/env python3
"""Emit browser expectations solely from explicit frozen source/image inputs."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.texture_reference import (FREEZE_COMMIT, FREEZE_SHA256, CORRECTION_SHA256,
    case_payload, decode_png, expected_occurrences, exact_uv, f32, load_fixtures,
    raw_points, sha)


def expectations(fixtures):
    cases = {}
    for case in fixtures["expected"]["cases"]:
        if case["expected_outcome"] != "valid":
            continue
        payload = case_payload(fixtures, case)
        assets = {}
        for asset in payload["assets"]:
            raw = base64.b64decode(asset["data_base64"], validate=True)
            png = decode_png(raw)
            if png["channels"] == 3:
                rgba = b"".join(png["pixels"][i:i + 3] + b"\xff" for i in range(0, len(png["pixels"]), 3))
            else:
                rgba = png["pixels"]
            w, h = png["width"], png["height"]
            sample_points = sorted(set(((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, h // 2))))
            probes = [{"xy": [x, y], "uv": [(x + .5) / w, (y + .5) / h],
                       "rgba": list(rgba[(y * w + x) * 4:(y * w + x + 1) * 4])} for x, y in sample_points]
            assets[asset["asset_id"]] = {"asset_id": asset["asset_id"], "png_sha256": sha(raw),
                "width": w, "height": h, "rgba_sha256": sha(rgba), "pixel_probes": probes}
        nodes, candidates = expected_occurrences(case), raw_points(fixtures, case)
        for node in nodes.values():
            if node.get("empty"):
                node["position_keys"] = []
                node["triangle_count"] = 0
                continue
            node["triangle_count"] = {"extrusion": 12, "holes": 32, "pockets": 28,
                "ring_loft": 12, "framed_loft": 12, "loft": 4 * case.get("loft_facets", 4)}[case["family"]]
            placed = [(p[2] + 2, p[0] - 3, p[1] + 1) if case["name"] == "placed-mapping" else p for p in candidates]
            keys = [struct.pack("<3f", *position).hex() for position in placed]
            node["position_keys"] = sorted(set(keys))
            active = {}
            for region, binding in node["bindings"].items():
                # Frozen zero-emission palette keys still declare their assets,
                # but cannot create actual material/UV/image resources.
                if region not in {"bottom", "side", "top", "floor", "inner"}:
                    continue
                active[region] = {**binding, "uv_by_position": {
                    key: struct.pack("<2f", *exact_uv(point, binding["mapping"])).hex()
                    for key, point in zip(keys, candidates)}}
            node["bindings"] = active
        used = sorted({binding["asset_id"] for node in nodes.values() for binding in node["bindings"].values()})
        cases[case["name"]] = {"name": case["name"], "id": case["id"], "program_revision": case["program_revision"],
            "nodes": nodes, "assets": assets, "used_asset_ids": used,
            "material_factors": case["expected_material_factors"],
            "color_cpu_reference_absolute_tolerance": fixtures["expected"]["color_comparison_absolute_tolerance"],
            "source_family": case["family"]}
    return {"schema_version": "ontokin.c080-independent-browser-inputs/0.1",
        "original_input_commit": FREEZE_COMMIT, "original_manifest_sha256": FREEZE_SHA256,
        "input_corpus_version": fixtures["corpus_version"],
        "correction_manifest_sha256": fixtures.get("correction_manifest_sha256"),
        "correction_input_commit": fixtures.get("correction_input_commit"),
        "expected_answers_source": "Only frozen source, PNG bytes and exact rational affine maps; no runtime imports or produced GLB reads.",
        "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/textured-surfaces")
    parser.add_argument("--corrections", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new file")
    value = expectations(load_fixtures(args.fixtures, args.corrections))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"valid_source_cases": len(value["cases"]), "sha256": sha(args.output.read_bytes())}))


if __name__ == "__main__":
    main()
