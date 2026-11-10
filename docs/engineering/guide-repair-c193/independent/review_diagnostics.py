#!/usr/bin/env python3
"""Verify the frozen one-factor diagnostic matrix from retained native bytes."""
import argparse
import copy
import json
from pathlib import Path

from check_artifact import digest, require, verify_frozen
from c190_glb_difference import fields


def normalized(configuration):
    result = copy.deepcopy(configuration)
    for key in ("source_sha256", "canonical_input_sha256", "backend_binding"):
        result["scene_tags"].pop(key)
    for obj in result["objects"].values():
        for driver in obj["drivers"]:
            driver["variables"].sort(key=lambda v: v["name"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--retained-reuse", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "Refusing to overwrite evidence")
    root = args.diagnostics
    read = lambda directory, name: json.loads((root / directory / name).read_text())
    baseline = normalized(read("N0", "native-configuration.json"))
    expected_n1 = copy.deepcopy(baseline)
    expected_n1["objects"]["left_shoe"]["rigid_body"] = None
    expected_n1["world"]["body_collection"].remove("left_shoe")
    require(normalized(read("N1", "native-configuration.json")) == expected_n1,
            "N1 changed configuration beyond left shoe collision removal")
    expected_n2 = copy.deepcopy(baseline)
    for lane in ("left", "right"):
        expected_n2["objects"]["_" + lane + "_generic"]["constraint"]["solver_iterations"] = 400
    require(normalized(read("N2-postprocess-r1", "native-configuration.json")) == expected_n2,
            "N2 changed configuration beyond GENERIC override400")
    n3_diffs = fields(baseline, normalized(read("N3", "native-configuration.json")))
    expected_paths = {"/objects/_" + lane + "_generic/" + tail
        for lane in ("left", "right") for tail in ("location/0", "location/2", "matrix_world/0/3", "matrix_world/2/3")}
    require({d["path"] for d in n3_diffs} == expected_paths, "N3 changed configuration beyond guide origins")
    original_samples = json.loads((args.retained_reuse / "native-transforms.json").read_text())
    n0_samples = read("N0", "native-transforms.json")
    require(original_samples == n0_samples, "N0 failed exact witness reproduction")
    preservation = {}
    for name in ("native-result.json", "scene.blend", "backend.json", "canonical-input.json", "implementation/native_worker.py"):
        before, after = digest(root / "N2" / name), digest(root / "N2-postprocess-r1" / name)
        require(before == after, "N2 postprocessing changed native input/output: " + name)
        preservation[name] = before
    report = {"version": "C193-independent-diagnostic-controls-review-1", "passed": True,
        "inherited_preservation": verify_frozen(), "N0_retained_native_samples_identical": True,
        "N1_only_collider_removed": True, "N2_only_guide_iterations_changed": True,
        "N3_only_guide_origins_changed": True, "N3_config_differences": n3_diffs,
        "native_executions": 4, "postprocessing_native_executions": 0,
        "N2_original_failure": read("N2", "diagnostic-receipt.json"),
        "N2_postprocessing": read("N2-postprocess-r1", "postprocessing-receipt.json"),
        "N2_postprocessing_preserved_hashes": preservation,
        "right_lane_and_fixed_parts": {}, "backend_differences": {},
        "driver_order_note": "Sorted backend JSON reversed two named left-stop variable declarations. Names, targets and expression are identical; original failed validation and exact-byte postprocessing are both retained."}
    for label, directory in (("N1", "N1"), ("N2", "N2-postprocess-r1"), ("N3", "N3")):
        samples = read(directory, "native-transforms.json")
        same = {name: all(a["matrices_blender_m"][name] == b["matrices_blender_m"][name]
                          for a, b in zip(n0_samples, samples))
                for name in ("base", "left_stop", "right_carriage", "right_shoe", "right_stop")}
        require(all(same.values()), label + " changed an unrelated native trajectory")
        report["right_lane_and_fixed_parts"][label] = same
        report["backend_differences"][label] = fields(read("N0", "backend.json"), read(directory, "backend.json"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": True, "fresh_diagnostic_builds": 4, "evidence": str(args.out)}))


if __name__ == "__main__":
    main()
