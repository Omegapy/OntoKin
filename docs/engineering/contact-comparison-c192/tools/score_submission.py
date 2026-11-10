#!/usr/bin/env python3
"""Coordinator scoring of exact successful or rejected C192 build bytes.

This records failed mapping measurements without weakening the frozen checker.
The source-localization checks add evidence; no original numerical gate changes.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import time


def literal_design(path):
    tree = ast.parse(path.read_text())
    values = [ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "DESIGN"]
    assert len(values) == 1
    assert all(isinstance(n, ast.Assign) or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
               and isinstance(n.value.value, str)) for n in tree.body), "Unexpected executable source statement"
    return values[0]


def score(repo, build, case, out):
    scope = repo / "docs/engineering/contact-comparison-c192"
    sys.path.insert(0, str(scope / "shared"))
    from check_delivery import load
    checker, mapping_checker = load(repo)
    from c190_glb_difference import compare
    command = json.loads((build / "delivery.json").read_text())
    raw_files = list(build.rglob("raw.glb"))
    assert len(raw_files) == 1, "Expected one retained native result"
    artifact = raw_files[0].parent
    out.mkdir(parents=True, exist_ok=False)
    target = next(c for c in json.loads((scope / "frozen/targets.json").read_text())["cases"] if c["id"] == case)
    expected = copy.deepcopy(literal_design(scope / "starters/design.py"))
    expected["parts"]["left_stop"]["at_mm"][0] = target["left_stop_near_face_mm"]
    canonical = json.loads((artifact / "canonical-input.json").read_text())
    assert canonical == expected, "An unrelated design field changed"
    route = command["route"]
    source = artifact / ("source.ok" if route == "ok" else "source.py")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == command["source_sha256"]
    assert command["source_unchanged_during_build"]
    if route == "ok":
        starter = (scope / "starters/design.ok").read_text()
        exact = starter.replace("at = [380, 130, -220][mm];",
                                f"at = [{target['left_stop_near_face_mm']}, 130, -220][mm];")
        source_localized = source.read_text() == exact
    else:
        source_localized = literal_design(source) == expected
        old = ast.parse((scope / "starters/design.py").read_text())
        new = ast.parse(source.read_text())
        changed = []
        def differences(a, b, path=""):
            if type(a) is not type(b):
                changed.append(path)
            elif isinstance(a, ast.AST):
                for key in a._fields:
                    differences(getattr(a, key), getattr(b, key), path + "/" + key)
            elif isinstance(a, list):
                if len(a) != len(b): changed.append(path)
                else:
                    for i, (x, y) in enumerate(zip(a, b)): differences(x, y, path + "/" + str(i))
            elif a != b:
                changed.append(path)
        differences(old, new)
        source_localized = source_localized and len(changed) == 1 and changed[0].endswith("/value")
    assert source_localized, "Source edit is not one localized stop literal"
    playback = checker.measure(artifact / "final.glb", case)
    comparison = compare(artifact / "raw.glb", artifact / "final.glb", artifact / "native-transforms.json")
    try:
        mapping = mapping_checker.audit(artifact / "raw.glb", artifact / "final.glb", artifact / "native-transforms.json")
    except Exception as error:
        mapping = {"passed": False, "failure_type": type(error).__name__, "reason": str(error),
                   "limit_mm": 0.2, "full_comparison": "raw-final-comparison.json"}
    for name, value in (("playback.json", playback), ("mapping.json", mapping), ("raw-final-comparison.json", comparison)):
        (out / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    hashes = {name: hashlib.sha256((artifact / name).read_bytes()).hexdigest()
              for name in ("canonical-input.json", "native-transforms.json", "scene.blend", "raw.glb", "final.glb")}
    report = {"case": case, "route": route, "scored_unix_s": time.time(), "source_sha256": digest,
              "source_localization_pass": source_localized, "canonical_only_target_field_changed": True,
              "build_successful": command["successful"], "playback_pass": playback["pass"],
              "mapping_pass": mapping["passed"],
              "pass": command["successful"] and playback["pass"] and mapping["passed"],
              "maximum_native_to_final_mm": comparison["maximumNativeSampleToFinalVertexDistanceMm"],
              "maximum_continuous_raw_to_final_mm": comparison["maximumContinuousRawToFinalVertexDeviationBoundMm"],
              "mapping_limit_mm": 0.2, "artifact_directory": str(artifact), "hashes": hashes,
              "left_travel_mm": playback.get("parts", {}).get("left_carriage", {}).get("final_displacement_mm", [None])[0],
              "right_gap_mm": playback.get("gaps", {}).get("right", {}).get("final_mm"),
              "build_elapsed_s": command["elapsed_s"],
              "qualification": "Rejected outputs remain diagnostic evidence and are not accepted deliveries" if not command["successful"] else "Accepted build; destination validation is separate"}
    (out / "score.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--build", type=Path, required=True)
    p.add_argument("--case", choices=("edit", "reuse"), required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(score(a.repo.resolve(), a.build.resolve(), a.case, a.out.resolve()), sort_keys=True))
