#!/usr/bin/env python3
"""Check C066 source bindings and conditional algebra without running OntoKin."""

import argparse
import ast
import hashlib
import json
from pathlib import Path

from math_derivation import derive as derive_math


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def function(tree, name):
    return next(node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)


def derive(root):
    require(__debug__, "Exact rational assertion checks must remain enabled")
    folder = Path(__file__).resolve().parent
    binding = json.loads((folder / "source-binding.json").read_text())
    checked = []
    for row in binding["inputs"]:
        raw = (root / row["path"]).read_bytes()
        require(len(raw) == row["bytes"], "Source size changed: " + row["path"])
        require(hashlib.sha256(raw).hexdigest() == row["sha256"], "Source digest changed: " + row["path"])
        require(git_blob(raw) == row["git_blob"], "Source blob changed: " + row["path"])
        checked.append(row)

    geometry = ast.parse((root / "ontokin/geometry.py").read_text())
    constants = {node.targets[0].id: node.value.value for node in geometry.body
                 if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                 and isinstance(node.value, ast.Constant)}
    segments, rings = constants["SPHERE_SEGMENTS"], constants["SPHERE_RINGS"]
    require((segments, rings) == (32, 16), "Native sphere dimensions changed")
    sphere = function(geometry, "sphere_mesh")
    require([ast.unparse(v) for v in sphere.args.defaults] == ["SPHERE_SEGMENTS", "SPHERE_RINGS"],
            "Native sphere defaults changed")
    sphere_text = ast.unparse(sphere)
    require("range(1, rings)" in sphere_text and "radius * v" in sphere_text,
            "Native sphere generation structure changed")
    indices = [1 + (latitude - 1) * segments + longitude
               for latitude in (5, 11) for longitude in (4, 12, 20, 28)]
    require(indices == [133, 141, 149, 157, 325, 333, 341, 349], "Wrong selected indices")

    reader = ast.parse((root / "ontokin/reach_conformance.py").read_text())
    cold = function(reader, "_vertex_extrema_uncached")
    loop = next(node for node in cold.body if isinstance(node, ast.For))
    require(ast.unparse(loop.iter) == "zip(source_positions, stored_positions)", "Cold traversal changed")
    require("independent_geometry_point" in ast.unparse(loop.body[0]), "Point charge moved")
    require("float32(value)" in ast.unparse(loop.body[1]) and "OKE-E-GEOMETRY" in ast.unparse(loop.body[1]),
            "Original supplied-byte comparison moved")
    float_branch = loop.body[2]
    require(isinstance(float_branch, ast.If) and "type(value) is float" in ast.unparse(float_branch.test),
            "Float branch changed")
    candidate = next(node for node in ast.walk(float_branch)
                     if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "candidate" for t in node.targets))
    call = candidate.value
    require(isinstance(call, ast.Call) and ast.unparse(call.func) == "arithmetic.total"
            and len(call.args) == 1 and isinstance(call.args[0], ast.GeneratorExp), "Exact fold is no longer a generator")
    gen = call.args[0]
    require(ast.unparse(gen.elt) == "arithmetic.value(value)", "Candidate decode changed")
    require(isinstance(gen.generators[0].iter, ast.Tuple) and len(gen.generators[0].iter.elts) == 3,
            "Candidate component count changed")
    bounds = next(node for node in reader.body if isinstance(node, ast.ClassDef) and node.name == "_Bounds")
    total = function(bounds, "total")
    direct = function(total, "direct")
    require("result = self.add(result, value)" in ast.unparse(direct)
            and "type(values) is not tuple" in ast.unparse(total), "Direct total fold changed")
    require("independent_bound_decode" in ast.unparse(function(bounds, "value")), "Decode charge changed")
    require("independent_exact_" in ast.unparse(function(bounds, "op")), "Exact operation charge changed")
    require("float_errors =" in ast.unparse(float_branch.body[-1]), "Float error accumulation moved")
    require("return (radius, arithmetic.norm(errors))" in ast.unparse(cold)
            or "return (radius, arithmetic.norm(errors))" in ast.dump(cold)
            or ast.unparse(cold.body[-1]) == "return (radius, arithmetic.norm(errors))",
            "Final radius/error return changed")
    mathematics = derive_math()
    require(mathematics["conditional_actual_coordinate_theorem"]["selected_indices"] == indices,
            "Mathematical and source indices disagree")
    return {
        "schema_version": "ontokin.c066-source-derivation/0.1",
        "status": "passed",
        "baseline_commit": binding["baseline_commit"],
        "baseline_tree": binding["baseline_tree"],
        "source_inputs_verified": checked,
        "source_structure": {"sphere_vertices": 2 + (rings - 1) * segments,
            "selected_indices": indices, "excluded_witness_index": 1 + (3 - 1) * segments + 4,
            "candidate_decode_charges": 3, "candidate_add_charges": 3,
            "candidate_total_charges": 6, "original_conversion_before_fold": True,
            "original_component_error_after_fold": True,
            "candidate_line": candidate.lineno,
            "counts_are_static_not_product_measurements": True},
        "conditional_cost": {"baseline_exact_candidate_count": "unknown B",
            "retained_exact_candidate_count": "input-dependent K, at most 8 on a completed eligible scan",
            "selection_count_is_not_baseline_count": True,
            "minimum_proposed_screen_passes_through_first_selected": indices[0] + 1,
            "completed_scan_optimistic_net": "6*(B-K)-L-A-F",
            "complete_request_positive_premise_established": False,
            "prefix_interruptions_need_event_counts": True},
        "conditional_mathematics": mathematics,
        "product_modules_imported": False,
        "product_requests_executed": 0,
        "product_suites_executed": 0,
        "native_trigonometric_evaluations": 0,
        "generated_meshes": 0,
        "hosted_jobs_dispatched": 0,
        "new_runtime_speedup_claimed": False,
        "release_acceptance": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(derive(args.repository.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
