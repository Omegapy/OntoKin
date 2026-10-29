#!/usr/bin/env python3
"""Derive C067 source and arithmetic evidence without importing OntoKin."""

import argparse
import ast
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def function(tree, name):
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name == name)


def down(a, b):
    # This is the selected mathematical schedule, not a product helper
    return math.nextafter(a + b, 0.0)


def lower(point):
    require(type(point) is tuple and len(point) == 3, "Invalid witness shape")
    require(all(type(v) is float and math.isfinite(v) for v in point), "Invalid witness values")
    x, y, z = (abs(v) for v in point)
    result = down(down(x, y), z)
    require(math.isfinite(result) and result >= 0, "Invalid downward result")
    require(Fraction(result) <= sum(map(Fraction, (x, y, z))), "Lower bound violated")
    return result


def upper(point):
    x, y, z = map(abs, point)
    return math.nextafter(math.nextafter(x + y, math.inf) + z, math.inf)


def trace(points, seed=None, visited=None):
    """An abstract native arithmetic trace, with no geometry or work object."""
    radius = Fraction(0)
    floor = 0.0
    components = None
    bound = None if seed is None else lower(points[seed])
    pending = seed is not None
    folds, seams, excluded, states, recognitions = [], [], [], [], []
    for index, point in enumerate(points[:visited]):
        magnitudes = tuple(map(abs, point))
        u = upper(point)
        if u > floor and magnitudes != components:
            skip = False
            if pending:
                seams.append(index)
                skip = u < bound
            if skip:
                excluded.append(index)
            else:
                folds.append(index)
                candidate = sum(map(Fraction, magnitudes))
                if candidate > radius:
                    radius = candidate
                    floor = math.nextafter(float(radius), -math.inf)
                if candidate == radius:
                    components = magnitudes
        # The selected schedule funds one identity comparison while pending
        if pending:
            recognitions.append(index)
            if point is points[seed]:
                pending = False
        states.append((radius, floor, components))
    return {"radius": str(radius), "folds": folds, "seams": seams,
            "excluded": excluded, "states": states, "recognitions": recognitions}


def brief(value):
    return {key: item for key, item in value.items() if key != "states"}


def derive(root):
    folder = Path(__file__).resolve().parent
    binding = json.loads((folder / "source-binding.json").read_text())
    for entry in binding["inputs"]:
        raw = (root / entry["path"]).read_bytes()
        require(len(raw) == entry["bytes"] and blob(raw) == entry["git_blob"]
                and hashlib.sha256(raw).hexdigest() == entry["sha256"], "Changed source: " + entry["path"])

    tree = ast.parse((root / "ontokin/reach_conformance.py").read_text())
    cold = function(tree, "_vertex_extrema_uncached")
    loops = [node for node in cold.body if isinstance(node, ast.For)]
    require(len(loops) == 1 and ast.unparse(loops[0].iter) == "zip(source_positions, stored_positions)", "Cold traversal changed")
    body = ast.unparse(cold)
    require(body.index("_tick(work, 'independent_geometry_point')") < body.index("tuple((float32(value) for value in point))"), "Point validation order changed")
    require("upper > radius_floor and (not repeated_maximum)" in body, "Original candidate screen changed")
    require("arithmetic.total((arithmetic.value(value) for value in (x, y, z)))" in body, "Three-value generator fold changed")
    require("return (radius, arithmetic.norm(errors))" in body, "Final result changed")
    total = ast.unparse(function(tree, "total"))
    require("type(values) is not tuple" in total and "self.add(result, value)" in total, "Generator folding changed")
    accessor = ast.unparse(function(ast.parse((root / "ontokin/gltf.py").read_text()), "accessor"))
    require("result = []" in accessor and "self._cache[index] = result" in accessor and "return result" in accessor, "Native accessor shape changed")

    mu = float.fromhex("0x0.0000000000001p-1022")
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    boundary_points = [(0., -0., 0.), (mu, 0., 0.), (mu, mu, mu),
                       (8., 8., 8.), (256., 256., 256.),
                       (maximum, maximum, maximum)]
    boundary = [{"point_hex": [v.hex() for v in p], "lower_hex": lower(p).hex(),
                 "lower_exact": str(Fraction(lower(p))),
                 "sum_exact": str(sum(Fraction(abs(v)) for v in p))}
                for p in boundary_points]
    require(lower(boundary_points[0]) == 0.0 and lower(boundary_points[1]) == 0.0, "Zero boundary changed")
    require(lower(boundary_points[-1]) == maximum, "Overflow downward rule changed")
    require(Fraction(lower((8., 8., 8.))) == 24 - Fraction(1, 2**48), "Small witness bound changed")
    require(Fraction(upper((1., 0., 0.))) == 1 + Fraction(1, 2**51), "Small witness upper changed")

    positive = tuple((float(i), 0., 0.) for i in range(1, 134)) + ((256., 256., 256.),) * 3
    base, candidate = trace(positive), trace(positive, seed=133)
    require(base["radius"] == candidate["radius"] == "768", "Complete positive trace differs")
    require(len(base["folds"]) == 134 and len(candidate["folds"]) == 1 and len(candidate["seams"]) == 134, "Positive event counts differ")
    require(len(candidate["recognitions"]) == 134, "Positive recognition count differs")
    require(base["states"][133:] == candidate["states"][133:], "Post-seed state differs")
    require(Fraction(lower(positive[133])) == 768 - Fraction(1, 2**43), "Positive lower bound differs")

    negative = ((1024., 0., 0.),) * 133 + ((1., 0., 0.),)
    negative_base, negative_candidate = trace(negative), trace(negative, seed=133)
    require(negative_base["radius"] == negative_candidate["radius"] == "1024", "Negative radius differs")
    require(len(negative_base["folds"]) == len(negative_candidate["folds"]) == 1, "Negative folds differ")
    require(len(negative_candidate["seams"]) == 1, "Negative added work differs")

    truncation = ((1., 0., 0.),) * 133 + ((8., 8., 8.),)
    truncated_base, truncated_candidate = trace(truncation, visited=1), trace(truncation, seed=133, visited=1)
    require(truncated_base["radius"] == "1" and truncated_candidate["radius"] == "0", "Truncation witness differs")
    restored_base, restored_candidate = trace(truncation), trace(truncation, seed=133)
    require(restored_base["radius"] == restored_candidate["radius"] == "24", "Complete witness differs")

    # Exact rational locations on both sides of a representable value check
    # the finite illustrative cases of the separately written dominance proof
    values = [Fraction(0), Fraction(mu), Fraction(1), Fraction(1) + Fraction(1, 2**54),
              Fraction(1) - Fraction(1, 2**55), Fraction(134), Fraction(768)]
    dominance_cases = 0
    for r in values:
        rounded = float(r)
        floor = math.nextafter(rounded, -math.inf)
        for low in [0., max(0., floor), rounded]:
            if Fraction(low) > r:
                continue
            for u in [0., max(0., floor), rounded, math.nextafter(rounded, math.inf)]:
                require(not (u > floor and u < low), "Visited-seed dominance violated")
                dominance_cases += 1

    return {
        "schema_version": "ontokin.c067-source-derivation/0.1",
        "source_commit": binding["source_commit"], "source_tree": binding["source_tree"],
        "source_bindings_verified": len(binding["inputs"]),
        "selected_seed_index": 133,
        "lower_schedule": "D(a,b)=nextafter(a+b,0.0); L=D(D(abs(qx),abs(qy)),abs(qz))",
        "source_structure": {"cold_zip": True, "native_accessor_returns_mutable_list": True,
                             "completed_float_fold_charge_calls": {"decode": 3, "add": 3}},
        "boundary_witnesses": boundary, "illustrative_dominance_cases": dominance_cases,
        "positive_abstract_trace": {"baseline": brief(base), "candidate": brief(candidate),
                                    "removed_folds": 133, "gross_removed_charges": 798,
                                    "added_seam_comparisons": 134,
                                    "optimistic_residual_before_all_setup_authority_recognition_fallback": 664,
                                    "added_identity_recognition_comparisons": 134,
                                    "optimistic_residual_after_selection_and_recognition_before_other_costs": 530,
                                    "post_seed_state_equal": True},
        "negative_abstract_trace": {"baseline": brief(negative_base), "candidate": brief(negative_candidate),
                                    "removed_folds": 0, "added_seam_comparisons": 1},
        "conditional_truncation_trace": {"baseline_radius": truncated_base["radius"],
                                          "candidate_radius": truncated_candidate["radius"],
                                          "complete_radius": restored_candidate["radius"],
                                          "not_an_observed_product_failure": True},
        "general_prefix_bound": {"maximum_removed_folds": 133, "maximum_gross_removed_charges": 798,
                                 "maximum_added_seam_comparisons_including_seed": 134,
                                 "maximum_pending_identity_recognitions": 134,
                                 "minimum_seam_comparisons_not_claimed": True},
        "product_imports": 0, "product_requests": 0, "runtime_suites": 0,
        "native_trigonometric_calls": 0, "generated_meshes": 0,
        "complete_request_saving_established": False,
        "boundary": "Abstract native binary64/rational witnesses and source inspection only; no production path or original recording evaluated"
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(derive(args.root.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
