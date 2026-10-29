#!/usr/bin/env python3
"""Bind source and derive C068's explicit eager-prefix cost; import no product."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def definition(tree, name, parent=None):
    nodes = tree.body
    if parent is not None:
        nodes = next(node for node in nodes if isinstance(node, ast.ClassDef) and node.name == parent).body
    return next(node for node in nodes if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name)


def derive(root):
    here = Path(__file__).resolve().parent
    binding = json.loads((here / "source-binding.json").read_text())
    sources = {}
    for item in binding["inputs"]:
        raw = (root / item["path"]).read_bytes()
        assert len(raw) == item["bytes"] and digest(raw) == item["sha256"] and blob(raw) == item["git_blob"], item["path"]
        sources[item["path"]] = raw.decode("utf-8")
    conformance = sources["ontokin/reach_conformance.py"]
    tree = ast.parse(conformance)
    cold = definition(tree, "_vertex_extrema_uncached")
    text = ast.get_source_segment(conformance, cold)
    assert "for point, stored in zip(source_positions, stored_positions):" in text
    assert text.index('_tick(work, "independent_geometry_point")') < text.index("tuple(float32(value) for value in point)")
    assert text.index("tuple(float32(value) for value in point)") < text.index("all(type(value) is float for value in point)")
    assert "arithmetic.total(arithmetic.value(value) for value in (x, y, z))" in text
    assert "for value in stored" not in text
    wrapper = ast.get_source_segment(conformance, definition(tree, "_vertex_extrema"))
    assert wrapper.index("proof = work.lookup(key)") < wrapper.index("radius, vertex_error = direct()")
    geometry = ast.get_source_segment(conformance, definition(tree, "_geometry_bounds"))
    assert geometry.index('decoded.accessor(primitive["attributes"]["POSITION"])') < geometry.index("_vertex_extrema(source_positions, stored_positions, work=work)")
    gate = ast.get_source_segment(conformance, definition(tree, "_certificate_term_native"))
    assert 'function.__globals__.get(name, _TERM_ABSENT)' in gate
    assert 'function.__builtins__.get(name, _TERM_ABSENT)' in gate
    tick = ast.get_source_segment(conformance, definition(tree, "_tick"))
    assert "work.charge(kind)" in tick
    total = ast.get_source_segment(conformance, definition(tree, "total", "_Bounds"))
    assert "result = self.add(result, value)" in total and "type(values) is not tuple" in total
    value = ast.get_source_segment(conformance, definition(tree, "value", "_Bounds"))
    assert 'self.tick("independent_bound_decode")' in value
    op = ast.get_source_segment(conformance, definition(tree, "op", "_Bounds"))
    assert 'self.tick("independent_exact_" + operation)' in op
    gltf = sources["ontokin/gltf.py"]
    gt = ast.parse(gltf)
    accessor = ast.get_source_segment(gltf, definition(gt, "accessor", "DecodedGLB"))
    assert "return self._cache[index]" in accessor and "result = []" in accessor
    assert "result.append(format_.unpack_from(self.binary, offset + row * stride))" in accessor
    reader = ast.get_source_segment(gltf, definition(gt, "read_glb"))
    assert "decoded.accessor(" in reader
    numeric = sources["ontokin/reach_numeric.py"]
    nt = ast.parse(numeric)
    charge = ast.get_source_segment(numeric, definition(nt, "charge", "ReachExecutionWork"))
    assert 'self.counts[kind] = self.counts.get(kind, 0) + 1' in charge
    assert charge.index("self.external_check()") < charge.index("self.operations += 1") < charge.index("observer()")
    construction = sources["ontokin/construction.py"]
    construction_tree = ast.parse(construction)
    work_calls = [node for node in ast.walk(construction_tree)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                  and node.func.id == "ReachExecutionWork"]
    assert any(any(keyword.arg == "check" and ast.unparse(keyword.value) == "budget.tick"
                   for keyword in call.keywords) for call in work_calls)
    driver = sources["tools/build_reach_source_artifacts.py"]
    assert "work=compiler.reach_work" in driver

    seed = 133
    seams = []
    for j in range(seed):
        pairs = seed - j + 1
        gross = 6 * (seed - j)
        entry_checks = 6 * pairs
        seam_checks = entry_checks - 3
        assert entry_checks - gross == 6
        assert seam_checks - gross == 3
        seams.append({"j": j, "pairs": pairs, "gross_ceiling": gross,
                      "entry_leaf_checks": entry_checks, "credited_seam_leaf_checks": seam_checks,
                      "best_residual_before_other_cost": gross - seam_checks})
    locations = []
    for path, name, parent in [
        ("ontokin/reach_conformance.py", "validate_reach_export", None),
        ("ontokin/gltf.py", "read_glb", None),
        ("ontokin/gltf.py", "accessor", "DecodedGLB"),
        ("ontokin/scene.py", "_source_primitive_mesh", None),
        ("ontokin/geometry.py", "sphere_mesh", None),
        ("ontokin/reach_conformance.py", "_geometry_bounds", None),
        ("ontokin/reach_conformance.py", "_vertex_extrema", None),
        ("ontokin/reach_conformance.py", "_vertex_extrema_uncached", None),
        ("ontokin/reach_numeric.py", "charge", "ReachExecutionWork"),
        ("ontokin/construction.py", "tick", "ConstructionBudget"),
        ("ontokin/reach_conformance.py", "_certificate_term_native", None),
    ]:
        node = definition(ast.parse(sources[path]), name, parent)
        locations.append({"path": path, "definition": (parent + "." if parent else "") + name,
                          "first_line": node.lineno, "last_line": node.end_lineno})
    return {
        "schema_version": "ontokin.c068-static-derivation/0.1",
        "source_commit": binding["source_commit"], "source_tree": binding["source_tree"],
        "source_bindings_verified": len(binding["inputs"]),
        "source_binding_sha256": digest((here / "source-binding.json").read_bytes()),
        "definitions": locations, "source_order_assertions": "passed",
        "seed_index": seed, "checked_candidate_seams": len(seams), "seams": seams,
        "entry_0": {"gross_ceiling": 798, "leaf_checks": 804, "deficit": 6},
        "seam_0": {"gross_ceiling": 798, "credited_leaf_checks": 801, "deficit": 3},
        "scope": "Completed matched-native distinct per-occurrence eager prefix leaf-check schedule only",
        "universal_admission_lower_bound": False,
        "producer_receipt_implemented": False, "proposal_adopted": False,
        "positive_complete_request_premise": False,
        "product_imports_executed": 0, "product_requests_executed": 0,
        "product_suites_executed": 0, "native_trigonometric_evaluations": 0,
        "generated_meshes": 0, "release_acceptance": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(derive(args.root), indent=2))


if __name__ == "__main__":
    main()
