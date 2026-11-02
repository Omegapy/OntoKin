#!/usr/bin/env python3
"""Emit C088 browser answers from frozen source/expectation/PNG bytes only.

No produced GLB, source producer output, or product module is read or imported.
The complete input inventory and pinned C087 delimiter/PNG utilities are checked
before deriving all twenty-one native roles.
"""
from __future__ import annotations

import argparse
import base64
from itertools import product
from pathlib import Path
import struct
import sys

import verify_membership_glb as R


TIMES = [0, .25, .5, .75, 1]


def vector_key(vector):
    return struct.pack("<" + "f" * len(vector), *vector).hex()


def expectations(frozen):
    cases = {}
    for role in frozen["delivery"]["native_roles"]:
        case = frozen["cases"][role["role"]]
        source = R.original_sources(case, frozen)
        projection = R.expected_projection(case, source)
        R.require(role["full_numerical_times_seconds"] == TIMES and role["capture_times_seconds"] == [0, 1],
                  "Exact frozen numerical/capture times")
        assets = {}
        for asset in source["payload"]["assets"]:
            raw = base64.b64decode(asset["data_base64"], validate=True)
            png = R.T.decode_png(raw)
            width, height, channels = png["width"], png["height"], png["channels"]
            R.require(channels in (3, 4), "Original RGB/RGBA PNG")
            rgba = png["pixels"] if channels == 4 else b"".join(png["pixels"][i:i+3] + b"\xff"
                                                                for i in range(0, len(png["pixels"]), 3))
            expected = frozen["expected"]["texture"]
            R.require((R.sha(raw), len(raw), width, height) ==
                      (expected["sha256"], expected["bytes"], expected["width"], expected["height"]),
                      "Exact original label PNG identity")
            coordinates = sorted({(0, 0), (width-1, 0), (0, height-1), (width-1, height-1),
                                  (width//2, height//2)})
            assets[asset["asset_id"]] = {
                "asset_id": asset["asset_id"], "png_sha256": R.sha(raw), "png_bytes": len(raw),
                "png_base64": base64.b64encode(raw).decode(), "width": width, "height": height,
                "rgba_sha256": R.sha(rgba), "rgba_base64": base64.b64encode(rgba).decode(),
                "sampler": expected["sampler"],
                "pixel_probes": [{"xy": [x, y], "uv": [(x+.5)/width, (y+.5)/height],
                                  "rgba": list(rgba[(y*width+x)*4:(y*width+x+1)*4])}
                                 for x, y in coordinates]}
        R.require(set(assets) == {"label"}, "Exact source asset closure")
        nodes = {}
        for path, occurrence in projection["occurrences"].items():
            empty = path in ("first", "sibling")
            geometry_path = path + '.panels["' + ("front.left" if path == "first" else "back.left") + '"]' if empty else path
            wanted = case["geometry"][geometry_path]
            positions = wanted["translation_samples_m"]
            R.require(len(positions) == len(TIMES) and wanted["quaternion_wxyz"] == [1, 0, 0, 0],
                      "Frozen identity orientation and five motion samples")
            origin = positions[0]
            velocity = [b-a for a, b in zip(positions[0], positions[-1])]
            R.require(positions == [[o + t*v for o, v in zip(origin, velocity)] for t in TIMES],
                      "Exact source constant-velocity motion")
            points, materials, bindings, counts = [], {}, {}, {}
            if path == "marker":
                R.require(wanted["box_size_m"] == [.5, .5, .5], "Independent marker dimensions")
                points = list(product(*[(-v/2, v/2) for v in wanted["box_size_m"]]))
                materials = {"box": {"baseColorFactor": [.5, .5, .5, 1],
                                      "metallicFactor": 0, "roughnessFactor": .7}}
                counts = {"box": 12}
            elif not empty:
                owner = path.split(".", 1)[0]
                key = occurrence["generated"]["key"].split(".", 1)[1]
                width = case[owner + "_selected"][key]
                points = list(product((0, width), (0, 2), (0, .25)))
                R.require(wanted["corners_m"] == [list(p) for p in points]
                          and (wanted["width_m"], wanted["height_m"], wanted["depth_m"], wanted["triangles"])
                          == (width, 2, .25, 12), "Frozen prism agrees with selected source width")
                R.require(wanted["top_uv_formula"] == ["0.5*x", "1-0.5*y"]
                          and wanted["texture_sha256"] == assets["label"]["png_sha256"], "Exact original UV and image binding")
                R.require(wanted["metallic"] == 0 and wanted["roughness"] == .7
                          and wanted["cap_color"] == [1, 1, 1, 1]
                          and wanted["side_color"] == ([.8, .25, .1, 1] if key == "middle" else [.25, .5, .75, 1]),
                          "Independent source PBR factors")
                materials = {region: {"baseColorFactor": wanted["side_color"] if region == "side" else wanted["cap_color"],
                                      "metallicFactor": 0, "roughnessFactor": .7}
                             for region in ("bottom", "side", "top")}
                bindings = {"top": {"asset_id": "label", "mapping": {"u": "0.5*x", "v": "1-0.5*y"},
                                     "uv_by_position": {vector_key(p): vector_key((.5*p[0], 1-.5*p[1])) for p in points}}}
                counts = {"bottom": 2, "side": 8, "top": 2}
            nodes[path] = {"element_id": occurrence["element_id"], "empty": empty,
                           "origin": origin, "velocity": velocity,
                           "position_samples_m": {format(t, "g"): p for t, p in zip(TIMES, positions)},
                           "quaternion_xyzw": [0, 0, 0, 1], "raw_corner_set_m": points,
                           "position_keys": sorted(vector_key(p) for p in points),
                           "triangle_count": sum(counts.values()), "region_triangle_counts": counts,
                           "materials": materials, "bindings": bindings}
        R.require(len(nodes) == 9 and sum(n["triangle_count"] for n in nodes.values()) == 84,
                  "Complete native object and triangle inventory")
        cases[case["id"]] = {
            "name": case["id"], "program_revision": source["revision"],
            "target_contract": R.TARGETS[case["mode"]], "source_profile": R.PROFILES[case["mode"]],
            "schema_version": "0.21" if case["mode"] == "source" else "0.20",
            "times_seconds": TIMES, "capture_times_seconds": [0, 1],
            "nodes": nodes, "assets": assets, "used_asset_ids": ["label"],
            "color_cpu_reference_absolute_tolerance": 1e-12,
            "source_family": "frozen sparse override rectangular panels and independent moving marker"}
    R.require(len(cases) == 21, "All twenty-one source roles")
    return {"schema_version": "ontokin.c088-independent-browser-inputs/1",
            "input_manifest_sha256": R.INPUT_SHA, "input_inventory_sha256": frozen["input_inventory_sha256"],
            "specification_sha256": R.SPEC_SHA, "candidate_observations_used": False,
            "expected_answers_source": "Exact adopted source/expectation/PNG bytes and independent prism/UV/motion arithmetic; no GLB or product import.",
            "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--reference-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    R.require(not args.output.exists(), "Browser expectation output must be fresh")
    references = R.import_references(args.reference_checkout.resolve())
    frozen = R.load_frozen(args.inputs.resolve())
    result = expectations(frozen)
    result["reference_utilities"] = references
    result["helper_sha256"] = R.sha(Path(__file__).read_bytes())
    result["reader_sha256"] = R.sha(Path(R.__file__).read_bytes())
    result["product_modules_imported"] = [name for name in sys.modules if name == "ontokin" or name.startswith("ontokin.")]
    R.require(not result["product_modules_imported"], "No product modules imported")
    R.save(args.output, result)
    print(R.canonical({"cases": len(result["cases"]), "output": str(args.output),
                       "sha256": R.sha(args.output.read_bytes())}).decode())


if __name__ == "__main__":
    main()
