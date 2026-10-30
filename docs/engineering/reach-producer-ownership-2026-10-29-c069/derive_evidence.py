#!/usr/bin/env python3
"""Check C069 bound source and declared design arithmetic without product imports."""

import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def definition(tree, name, owner=None):
    nodes = tree.body
    if owner:
        nodes = next(n for n in nodes if isinstance(n, ast.ClassDef) and n.name == owner).body
    return next(n for n in nodes if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)


def main():
    binding = json.loads((HERE / "source-binding.json").read_text())
    sources, trees, verified = {}, {}, []
    for item in binding["sources"]:
        raw = (ROOT / item["path"]).read_bytes()
        assert len(raw) == item["size"] and git_blob(raw) == item["sha"], item["path"]
        sources[item["path"]] = raw.decode()
        if item["path"].endswith(".py"):
            trees[item["path"]] = ast.parse(raw, filename=item["path"])
        verified.append({**item, "sha256": digest(raw)})

    checks = []

    def require(name, value):
        assert value, name
        checks.append(name)

    def segment(path, name, owner=None):
        return ast.get_source_segment(sources[path], definition(trees[path], name, owner))

    driver = trees["tools/build_reach_source_artifacts.py"]
    calls = [n for n in ast.walk(driver) if isinstance(n, ast.Call)]
    compile_calls = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == "compile_construction"]
    require("original_driver_omits_custom_compile_check", len(compile_calls) == 1 and
            not any(k.arg == "check" for k in compile_calls[0].keywords))
    export_calls = [n for n in calls if isinstance(n.func, ast.Name) and n.func.id == "export_glb"]
    require("original_export_reuses_compiler_work", len(export_calls) == 1 and
            any(k.arg == "work" and ast.unparse(k.value) == "compiler.reach_work" for k in export_calls[0].keywords))

    construction = segment("ontokin/construction.py", "__init__", "ConstructionCompiler")
    require("construction_uses_native_budget_callback", "check=budget.tick" in construction)
    budget = segment("ontokin/construction.py", "__init__", "ConstructionBudget")
    require("construction_retains_nested_check", "self.check = check" in budget)
    decoder = segment("ontokin/gltf.py", "DecodedGLB")
    accessor = segment("ontokin/gltf.py", "accessor", "DecodedGLB")
    require("accessor_hit_returns_cached_list", "if index in self._cache:\n            return self._cache[index]" in accessor)
    require("decoder_miss_publishes_same_list", "result = []" in accessor and "result.append(format_.unpack_from" in accessor and
            "self._cache[index] = result\n        return result" in accessor)
    require("decoder_no_generation_or_mutation_wrapper", "generation" not in decoder and "epoch" not in decoder and
            {n.name for n in definition(trees["ontokin/gltf.py"], "DecodedGLB").body if isinstance(n, ast.FunctionDef)} == {"clock", "accessor"})
    require("clock_cache_separate_projection", 'self._clocks[index] = [row[0] for row in self.accessor(index)]' in decoder)
    reader = segment("ontokin/gltf.py", "read_glb")
    require("read_glb_eager_decode_before_geometry", reader.index('for index, accessor in enumerate(document["accessors"]):') <
            reader.index("values = decoded.accessor(index)") < reader.index('for mesh in document.get("meshes", []):'))
    require("read_glb_reuses_cached_positions", "positions, normals = decoded.accessor(position_id), decoded.accessor(normal_id)" in reader)
    validate = segment("ontokin/reach_conformance.py", "validate_reach_export")
    ordered = ["decoded = read_glb", "verify_numeric_bases(", "program = program_metadata", "reference = build_reference",
               "boundary_records = reference.boundary_states", "quantization = _verify_metadata", "authored, times, shift = verify_retained_clocks",
               "geometry, meshes = _geometry_bounds"]
    offsets = [validate.index(x) for x in ordered]
    require("actual_intervening_stage_order", offsets == sorted(offsets))
    geometry = segment("ontokin/reach_conformance.py", "_geometry_bounds")
    ordered_geometry = ['source_positions = () if mesh is None else mesh.positions',
                        'stored_positions = decoded.accessor(primitive["attributes"]["POSITION"])',
                        'if len(stored_positions) != len(source_positions):',
                        'normals = decoded.accessor(primitive["attributes"]["NORMAL"])',
                        'radius, vertex_error = _vertex_extrema']
    offsets = [geometry.index(x) for x in ordered_geometry]
    require("actual_source_position_topology_extrema_order", offsets == sorted(offsets))
    wrapper = segment("ontokin/reach_conformance.py", "_vertex_extrema")
    require("wrapper_charged_lookup_precedes_cold_result", wrapper.index("proof = work.lookup(key)") < wrapper.index("radius, vertex_error = direct()"))
    require("proof_snapshot_is_after_cold_result", wrapper.index("radius, vertex_error = direct()") < wrapper.index("snapshot = []") < wrapper.index("work.remember(key, proof)"))
    cold = segment("ontokin/reach_conformance.py", "_vertex_extrema_uncached")
    require("cold_zip_and_tick_precede_conversion", cold.index("for point, stored in zip(") < cold.index('_tick(work, "independent_geometry_point")') <
            cold.index("tuple(float32(value) for value in point)"))
    require("cold_exact_sum_is_generator", "arithmetic.total(arithmetic.value(value) for value in (x, y, z))" in cold)
    charge = segment("ontokin/reach_numeric.py", "charge", "ReachExecutionWork")
    require("charge_callback_precedes_count_increment", charge.index("self.external_check()") < charge.index("self.operations += 1"))
    require("charge_observer_after_counts", charge.index("self.counts[kind] = self.counts.get(kind, 0) + 1") < charge.index("observer()"))
    work_class = definition(trees["ontokin/reach_numeric.py"], "ReachExecutionWork")
    generation_methods = []
    for method in work_class.body:
        if not isinstance(method, ast.FunctionDef):
            continue
        for node in ast.walk(method):
            if isinstance(node, ast.AugAssign) and ast.unparse(node.target) == "self._cache_generation":
                generation_methods.append(method.name)
    generation_owners = sorted(set(generation_methods))
    require("generation_is_numerical_cache_bookkeeping", generation_owners == ["_sync_cache_operand_limit", "lookup", "remember", "remember_batch"])
    require("numerical_work_has_no_decoder_owner", "DecodedGLB" not in sources["ontokin/reach_numeric.py"] and
            "stored_positions" not in sources["ontokin/reach_numeric.py"])
    primitive = segment("ontokin/scene.py", "_source_primitive_mesh")
    require("primitive_hit_returns_cached_object", "if cached is not None:\n            return cached" in primitive)
    require("primitive_independent_namespace_is_callsite_input", 'namespace="reach_independent_source"' in geometry)
    runtime = segment("ontokin/program_runtime.py", "_compile")
    require("agent_nested_callback_differs", "check=budget.tick" in runtime)
    agent_export = segment("ontokin/program_agent.py", "_export", "ProgramAgentService")
    require("agent_retains_delivery_callback", "check=delivery_check" in agent_export and "compiler.reach_work" in agent_export)

    quantities_node = definition(trees["ontokin/reach_export.py"], "_certificate_quantities")
    assignment_names = ("eq", "chord", "arc")
    angular_counts = {}
    angular_inputs = set()
    for name in assignment_names:
        statement = next(n for n in quantities_node.body if isinstance(n, ast.Assign) and
                         any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
        angular_counts[name] = sum(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_exact"
                                   for n in ast.walk(statement.value))
        angular_inputs.update(n.id for n in ast.walk(statement.value) if isinstance(n, ast.Name))
    require("different_angular_target_has_nine_exact_calls", angular_counts == {"eq": 1, "chord": 4, "arc": 4})
    require("angular_region_has_no_position_radius_input", not ({"ep", "nsp", "radius", "vertex_error", "magnitude", "enclosing", "shift"} & angular_inputs))
    quantities = ast.get_source_segment(sources["ontokin/reach_export.py"], quantities_node)
    require("positional_add_precedes_angular_region", quantities.index('ep = _exact(ep, nsp, "add", work)') < quantities.index('eq = _exact(eq, nsr, "add", work)'))
    export_source = sources["ontokin/reach_export.py"]
    require("existing_group_key_is_broader", '("certificate_group", bound, enclosing, radius, vertex_error, nsp, nsr,' in export_source and
            "proof_width, proof_shift, ep, eq, magnitude)" in export_source)

    funding = json.loads((HERE / "funding.json").read_text())
    require("declared_subject_has_24_unique_slots", len(funding["subject_fields"]) == 24 and
            len({x["name"] for x in funding["subject_fields"]}) == 24 and
            [x["slot"] for x in funding["subject_fields"]] == list(range(24)))
    require("declared_seed_has_four_unique_slots", len(funding["seed_fields"]) == 4 and
            len({x["name"] for x in funding["seed_fields"]}) == 4)
    costs = funding["declared_layout_counts"]
    require("declared_layout_arithmetic_only", costs["subject_initialization_only"] == 1 + 24 and
            costs["seed_initialization_only"] == 1 + 4 and costs["illustrative_subject_read_predicate_once"] == 2 * 24 and
            costs["whole_cost"] is None and costs["adopted_units"] is False)
    require("missing_authority_is_explicit", funding["root_resolved"] is False and funding["list_interval_resolved"] is False and
            funding["positive_complete_request_premise"] is False and funding["unknown_cost_is_zero"] is False)

    definition_requests = [
        ("tools/build_reach_source_artifacts.py", "build", None),
        ("ontokin/construction.py", "ConstructionBudget", None),
        ("ontokin/construction.py", "__init__", "ConstructionCompiler"),
        ("ontokin/construction.py", "compile_construction", None),
        ("ontokin/gltf.py", "DecodedGLB", None),
        ("ontokin/gltf.py", "read_glb", None),
        ("ontokin/gltf.py", "export_glb", None),
        ("ontokin/gltf.py", "_export_glb", None),
        ("ontokin/gltf.py", "validate_export", None),
        ("ontokin/reach_conformance.py", "validate_reach_export", None),
        ("ontokin/reach_conformance.py", "verify_retained_clocks", None),
        ("ontokin/reach_conformance.py", "_geometry_bounds", None),
        ("ontokin/reach_conformance.py", "_vertex_extrema", None),
        ("ontokin/reach_conformance.py", "_vertex_extrema_uncached", None),
        ("ontokin/reach_numeric.py", "charge", "ReachExecutionWork"),
        ("ontokin/reach_numeric.py", "lookup", "ReachExecutionWork"),
        ("ontokin/reach_numeric.py", "remember", "ReachExecutionWork"),
        ("ontokin/reach_numeric.py", "remember_batch", "ReachExecutionWork"),
        ("ontokin/reach_numeric.py", "_sync_cache_operand_limit", "ReachExecutionWork"),
        ("ontokin/scene.py", "_source_primitive_mesh", None),
        ("ontokin/scene.py", "_source_surface_mesh", None),
        ("ontokin/geometry.py", "Mesh", None),
        ("ontokin/geometry.py", "sphere_mesh", None),
        ("ontokin/program_runtime.py", "_compile", None),
        ("ontokin/program_agent.py", "_export", "ProgramAgentService"),
        ("ontokin/reach_export.py", "_certificate_quantities", None),
        ("ontokin/reach_export.py", "_reuse", None),
        ("ontokin/reach_export.py", "_exact", None),
    ]
    definitions = []
    for path, name, owner in definition_requests:
        node = definition(trees[path], name, owner)
        raw = ast.get_source_segment(sources[path], node).encode()
        definitions.append({"path": path, "name": name, "owner": owner, "first_line": node.lineno,
                            "last_line": node.end_lineno, "source_segment_sha256": digest(raw)})
    mutations = [
        {"transition": "same_length_list_item_or_slice_write", "calls_decoder": False, "calls_numerical_cache": False},
        {"transition": "list_truncation_or_mutator", "calls_decoder": False, "calls_numerical_cache": False},
        {"transition": "decoder_cache_replacement", "calls_decoder": False, "calls_numerical_cache": False},
        {"transition": "decoder_document_binary_check_rebinding", "calls_decoder": False, "calls_numerical_cache": False},
        {"transition": "native_numerical_cache_promotion_insert_reset", "calls_decoder": False, "calls_numerical_cache": True},
        {"transition": "host_work_field_or_dispatch_rebinding", "calls_decoder": False, "calls_numerical_cache": False},
    ]
    result = {"schema_version": "ontokin.c069-static-derivation/0.1", "status": "passed",
              "baseline_commit": binding["baseline_commit"], "baseline_tree": binding["baseline_tree"],
              "source_bindings": verified, "definitions": definitions, "checks": checks, "check_count": len(checks),
              "numerical_generation_owner_methods": generation_owners,
              "declared_mutation_matrix": mutations, "mutation_matrix_is_executed_test": False,
              "subject_fields": 24, "seed_fields": 4, "conditional_layout_counts": costs,
              "next_target_angular_exact_calls": angular_counts, "next_target_exact_call_total": sum(angular_counts.values()),
              "actual_duplicate_incidence": None, "complete_request_saving": None,
              "native_stock_mutation_observed": False, "universal_receipt_impossibility_proved": False,
              "source_only": True, "product_imports_executed": 0, "product_requests_executed": 0,
              "runtime_suites_executed": 0, "native_trigonometric_evaluations": 0, "generated_meshes": 0}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
