"""Read retained C060 bytes and derive C071's singleton-phase screen.

This standalone helper imports no product modules and executes no product code.
It does not certify the numerical claims in the retained unvalidated GLBs.
"""
from __future__ import annotations

import argparse
import ast
from bisect import bisect_right
from collections import Counter
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile


BASELINE_COMMIT = "ff71faa05503245b553621ba390cad080276e732"
BASELINE_TREE = "a124d1acfa4e7c5f6c140e592d594036a2eed2ca"
EXPORT = "ontokin/reach_export.py"
NUMERIC = "ontokin/reach_numeric.py"
HISTORY = "docs/engineering/reach-recording-validation-2026-10-28-c060"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def unique_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON object key: " + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def rational(value):
    return Fraction(int(value["numerator"]), int(value["denominator"]))


def inspect_case(case, archive, members, directory):
    name = case + "/capture/unvalidated-reader-input.glb"
    raw = archive.read(name)
    identity = members[name]
    require(len(raw) == identity["bytes"] and sha256(raw) == identity["sha256"],
            case + " retained GLB identity differs")
    magic, version, size = struct.unpack_from("<4sII", raw)
    require(magic == b"glTF" and version == 2 and size == len(raw), "GLB header")
    json_size, json_type = struct.unpack_from("<II", raw, 12)
    require(json_type == 0x4E4F534A, "GLB JSON chunk type")
    document = unique_json(raw[20:20 + json_size])
    binary_header = 20 + json_size
    binary_size, binary_type = struct.unpack_from("<II", raw, binary_header)
    require(binary_type == 0x004E4942 and binary_header + 8 + binary_size == len(raw),
            "GLB binary chunk type and length")
    binary = raw[binary_header + 8:]
    metadata = document["extras"]["ontokin"]
    quantization = metadata["reach_quantization"]
    boundaries = [Fraction(row["source_seconds"]) for row in metadata["boundary_states"]]
    require(boundaries == sorted(set(boundaries)), "source boundary order")
    keys = quantization["retained_keys"]
    authored = [rational(row["authored_seconds"]) for row in keys]
    input_accessors = sorted({sampler["input"] for animation in document["animations"]
                              for sampler in animation["samplers"]})
    arrays = []
    for accessor_index in input_accessors:
        accessor = document["accessors"][accessor_index]
        require(accessor["componentType"] == 5126 and accessor["type"] == "SCALAR",
                "clock accessor scalar binary32")
        view = document["bufferViews"][accessor["bufferView"]]
        require(view.get("buffer", 0) == 0 and "sparse" not in accessor, "clock buffer")
        view_offset = view.get("byteOffset", 0)
        accessor_offset = accessor.get("byteOffset", 0)
        stride = view.get("byteStride", 4)
        count = accessor["count"]
        require(count == len(keys) and count >= 2 and stride >= 4, "clock count/stride")
        require(accessor_offset + (count - 1) * stride + 4 <= view["byteLength"],
                "clock accessor in view")
        require(view_offset + view["byteLength"] <= len(binary), "clock view in buffer")
        values = [struct.unpack_from("<f", binary, view_offset + accessor_offset + i * stride)[0]
                  for i in range(count)]
        require(all(struct.pack("<f", value).hex() ==
                    bytes.fromhex(keys[i]["stored_binary32_bits"])[::-1].hex()
                    for i, value in enumerate(values)), "retained clock bits")
        arrays.append(values)
    require(arrays and all(values == arrays[0] for values in arrays), "one shared clock")
    stored = list(map(Fraction, arrays[0]))
    require(all(Fraction(row["stored_seconds"]) == value for row, value in zip(keys, stored)),
            "retained JSON clocks match binary accessor")
    require(authored == sorted(set(authored)) and stored == sorted(set(stored)),
            "strict authored/stored clock order")
    require(set(boundaries) <= set(authored), "every source boundary retained")
    for boundary in boundaries:
        require(Fraction(struct.unpack("<f", struct.pack("<f", float(boundary)))[0]) == boundary,
                "boundary exactly representable in binary32")
        index = authored.index(boundary)
        require(stored[index] == boundary and keys[index]["semantic_boundary"] is True,
                "semantic boundary stored exactly")
    groups = {}
    intervals_by_phase = Counter()
    selected_by_interval = []
    for index, (left, right) in enumerate(zip(authored, authored[1:])):
        source_index = bisect_right(boundaries, left) - 1
        require(boundaries[source_index] <= left < right <= boundaries[source_index + 1],
                "authored interval lies within one source phase")
        low = max(Fraction(0), min(left, stored[index]))
        high = min(authored[-1], max(right, stored[index + 1]))
        selected = tuple(i for i, (start, end) in enumerate(zip(boundaries, boundaries[1:]))
                         if max(low, start) < min(high, end))
        require(selected == (source_index,), "enclosing phase set is source singleton")
        groups.setdefault((source_index, selected), []).append(index)
        intervals_by_phase[str(source_index)] += 1
        selected_by_interval.append(selected)
    rows = quantization["interval_certificates"]
    carriers = {row["carrier"]["path"] for row in rows}
    identities = set()
    for row in rows:
        index = row["left_key_index"]
        require(row["right_key_index"] == index + 1 and
                tuple(row["source_phase_indices"]) == selected_by_interval[index],
                "certificate phase claim matches exact recomputation")
        identities.add((index, row["carrier"]["path"]))
    require(len(identities) == len(rows) == (len(authored) - 1) * len(carriers),
            "complete unique interval/carrier identity census")
    summary_path = directory / "evidence" / case / "summary.json"
    summary_raw = summary_path.read_bytes()
    summary = unique_json(summary_raw)
    counters = summary["producer_after_construction"]["reach_category_delta"]
    visits = counters["recording_certificate_group"]
    calculations = counters["destination_bound"]
    require(visits == len(groups) * len(carriers), "retained group counter reconciliation")
    return {
        "case": case,
        "member": name,
        "member_bytes": len(raw),
        "member_sha256": sha256(raw),
        "summary_sha256": sha256(summary_raw),
        "boundaries": [str(value) for value in boundaries],
        "actual_binary_clock_accessors": input_accessors,
        "keys": len(keys),
        "intervals_by_phase": dict(intervals_by_phase),
        "carriers": len(carriers),
        "certificate_rows": len(rows),
        "groups": len(groups),
        "all_selected_equal_source_singleton": True,
        "group_visits": visits,
        "baseline_group_calculations": calculations,
        "baseline_group_hits": visits - calculations,
        "new_projected_key_equivalence_hits": 0,
        "bound_speed_recoverable_as": "enclosing.speed",
        "exact_numerical_inputs_reconstructed": False,
        "ordered_lru_events_reconstructed": False,
    }


def derive(repository):
    directory = repository / "docs/engineering/reach-recording-validation-2026-10-28-c060"
    parts_raw = (directory / "evidence.zip.parts.json").read_bytes()
    manifest = unique_json(parts_raw)
    chunks = []
    offset = 0
    for part in manifest["parts"]:
        raw = (directory / part["path"]).read_bytes()
        require(part["offset"] == offset and len(raw) == part["bytes"] and
                sha256(raw) == part["sha256"], "ordered archive part identity")
        chunks.append(raw)
        offset += len(raw)
    raw = b"".join(chunks)
    require(len(raw) == manifest["bytes"] and sha256(raw) == manifest["sha256"],
            "assembled archive identity")
    members_raw = (directory / "evidence.members.json").read_bytes()
    member_rows = unique_json(members_raw)["members"]
    members = {item["path"]: item for item in member_rows}
    require(len(members) == len(member_rows) == manifest["member_count"],
            "unique retained member manifest paths")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) == manifest["member_count"],
                "unique ZIP member names")
        require(set(names) == set(members), "ZIP member names match retained manifest")
        cases = [inspect_case(case, archive, members, directory) for case in ("P11", "L03")]
    return {
        "schema_version": "ontokin.c071-retained-speed-projection-screen/0.1",
        "status": "passed",
        "archive_bytes": len(raw),
        "archive_sha256": sha256(raw),
        "parts_manifest_sha256": sha256(parts_raw),
        "members_manifest_sha256": sha256(members_raw),
        "archive_parts_verified": len(chunks),
        "selected_glb_members_verified": 2,
        "cases": cases,
        "scope": "Static retained-byte census plus native singleton key injectivity",
        "product_imports_executed": 0,
        "product_requests_executed": 0,
        "historical_auditor_rerun": False,
        "numerical_claims_certified": False,
        "original_product_requests_remain_failed": True,
    }


def source_derivation(repository, binding_path):
    binding_raw = binding_path.read_bytes()
    binding = unique_json(binding_raw)
    require(binding["baseline_commit"] == BASELINE_COMMIT and
            binding["baseline_tree"] == BASELINE_TREE, "C070 baseline identity")
    sources, trees, verified = {}, {}, []
    for item in binding["sources"]:
        path = item["path"]
        require(path not in sources, "duplicate source binding")
        raw = (repository / path).read_bytes()
        require(len(raw) == item["size"] and git_blob(raw) == item["sha"] and
                sha256(raw) == item["sha256"], "bound source identity: " + path)
        require(item["type"] == "blob" and item["mode"] in ("100644", "100755"),
                "bound regular source mode")
        require(bool((repository / path).stat().st_mode & 0o100) ==
                (item["mode"] == "100755"), "source executable mode: " + path)
        sources[path] = raw
        if path.endswith(".py"):
            trees[path] = ast.parse(raw, filename=path)
        verified.append(dict(item))
    checks = []

    def check(name, condition):
        require(condition, name)
        require(name not in checks, "duplicate check name")
        checks.append(name)

    def definition(path, name, owner=None):
        body = trees[path].body
        if owner is not None:
            owners = [n for n in body if isinstance(n, ast.ClassDef) and n.name == owner]
            require(len(owners) == 1, "unique definition owner " + owner)
            body = owners[0].body
        nodes = [n for n in body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name]
        require(len(nodes) == 1, "unique definition " + str(owner) + "." + name)
        return nodes[0]

    def text(path, name, owner=None):
        return ast.get_source_segment(sources[path].decode(), definition(path, name, owner))

    def assignments(node, target):
        return [n for n in ast.walk(node) if isinstance(n, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id == target for t in n.targets)]

    def one_assignment(node, target):
        nodes = assignments(node, target)
        require(len(nodes) == 1, "unique assignment " + target)
        return nodes[0]

    motion = definition(EXPORT, "MotionBound")
    fields = [n.target.id for n in motion.body if isinstance(n, ast.AnnAssign)]
    check("native_motion_bound_exact_three_fields", fields == ["speed", "acceleration", "angular_speed"])
    check("motion_bound_declared_frozen_dataclass", [ast.unparse(n) for n in motion.decorator_list] ==
          ["dataclass(frozen=True)"])
    group = definition(EXPORT, "interval_certificates")
    original_key = ast.unparse(one_assignment(group, "key").value)
    check("existing_complete_group_key_exact", original_key ==
          "('certificate_group', bound, enclosing, radius, vertex_error, nsp, nsr, proof_width, proof_shift, ep, eq, magnitude)")
    bound_assignments = assignments(group, "bound")
    check("source_bound_comes_from_source_phase_carrier", len(bound_assignments) == 2 and
          all(ast.unparse(n.value) == "phase.carriers[frame]" for n in bound_assignments))
    enclosing_assignments = assignments(group, "enclosing")
    enclosing_expression = "MotionBound(max((plan.phases[i].carriers[frame].speed for i in selected)), max((plan.phases[i].carriers[frame].acceleration for i in selected)), max((plan.phases[i].carriers[frame].angular_speed for i in selected)))"
    check("both_enclosing_bounds_are_componentwise_selected_maxima", len(enclosing_assignments) == 2 and
          all(ast.unparse(n.value) == enclosing_expression for n in enclosing_assignments))
    check("source_index_uses_authored_left_key", ast.unparse(one_assignment(group, "source_index").value) ==
          "min(bisect_right(plan.boundaries, left) - 1, len(plan.phases) - 1)")
    check("selected_comes_from_authored_and_stored_positive_overlap", ast.unparse(one_assignment(group, "selected").value) ==
          "enclosing_phases(plan.phases, left, right, s0, s1, prefix_end=exact[-1], work=work)")
    check("group_identity_keeps_source_index_and_selected", ast.unparse(one_assignment(group, "group_key").value) ==
          "(source_index, tuple(selected))")
    group_text = text(EXPORT, "interval_certificates")
    check("authored_interval_guard_precedes_selected_construction",
          group_text.index("if not phase.start <= left < right <= phase.end:") <
          group_text.index("selected = enclosing_phases("))
    check("numeric_selected_has_separate_container", ast.unparse(one_assignment(group, "numeric_selected").value) ==
          "set(selected)" and "numeric_selected.add(endpoint_index)" in group_text)
    check("proof_width_retains_source_acceleration_and_angular_speed", ast.unparse(one_assignment(group, "proof_width").value) ==
          "group['width'] if bound.acceleration or bound.angular_speed else Fraction(0)")
    check("proof_shift_retains_enclosing_speed_and_angular_speed", ast.unparse(one_assignment(group, "proof_shift").value) ==
          "group['shift'] if enclosing.speed or enclosing.angular_speed else Fraction(0)")
    check("existing_whole_group_reuse_wraps_calculation", "_reuse(work, key, lambda: _certificate_quantities(" in group_text)
    check("per_row_source_phase_indices_are_selected", '"source_phase_indices": list(selected)' in group_text)
    enclosing = definition(EXPORT, "enclosing_phases")
    check("enclosing_low_includes_both_authored_and_stored_start", ast.unparse(one_assignment(enclosing, "low").value) ==
          "max(Fraction(0), min(Fraction(authored_start), Fraction(stored_start)))")
    check("enclosing_high_includes_both_authored_and_stored_end", ast.unparse(one_assignment(enclosing, "high").value) ==
          "min(Fraction(prefix_end), max(Fraction(authored_end), Fraction(stored_end)))")
    check("enclosing_selection_uses_strict_positive_overlap", "if max(low, phase.start) < min(high, phase.end):" in
          text(EXPORT, "enclosing_phases"))
    timeline = text(EXPORT, "reach_timeline")
    check("timeline_binds_semantic_boundary_set", "semantic = set(plan.boundaries)" in timeline)
    check("timeline_generates_keys_within_each_phase", "authored.append(phase.start + (phase.end - phase.start) * index / steps)" in timeline)
    check("timeline_uses_direct_binary32_conversion", "stored, bits = direct_binary32(time, work=work, model=model)" in timeline)
    check("timeline_rejects_missing_semantic_boundaries", "if not semantic.issubset(exact):" in timeline)
    check("timeline_returns_same_authored_and_stored_sequences", 'return exact, [item["stored_seconds"] for item in retained], retained' in timeline)
    prefix = text(EXPORT, "reach_prefix_plan")
    check("prefix_records_and_boundaries_share_actual_time", "records.append(_boundary_record(time, before, after," in prefix and
          "times.append(time)" in prefix and "return ReachPrefixPlan(tuple(times), tuple(phases), tuple(states)," in prefix)
    check("prefix_carriers_construct_actual_motion_bounds", "carriers = {path: MotionBound(value.carrier_speed_upper_m_per_s," in prefix and
          "value.carrier_acceleration_upper_m_per_s2," in prefix and "value.angular_speed_upper_rad_per_s)" in prefix)
    quantities = definition(EXPORT, "_certificate_quantities")
    speed_reads = [n for n in ast.walk(quantities) if isinstance(n, ast.Attribute) and ast.unparse(n) == "bound.speed"]
    check("source_speed_read_occurs_once_in_quantity_calculation", len(speed_reads) == 1)
    rounded = one_assignment(quantities, "rounded_bound")
    check("source_speed_is_forwarded_into_temporary_motion_bound", ast.unparse(rounded.value) ==
          "MotionBound(bound.speed, q('carrier_acceleration_bound_m_per_s2'), q('angular_speed_bound_rad_per_s'))")
    rounded_destination = [n for n in ast.walk(quantities) if isinstance(n, ast.Assign) and
                           any(ast.unparse(t) == "quantities['destination_numeric_rotation_bound_rad']"
                               for t in n.targets)]
    check("source_speed_read_is_late_after_destination_bound_rounding", len(rounded_destination) == 1 and
          speed_reads[0].lineno > rounded_destination[0].end_lineno)
    interval = definition(EXPORT, "complete_interval_bounds")
    used_fields = sorted({ast.unparse(n) for n in ast.walk(interval) if isinstance(n, ast.Attribute) and
                         isinstance(n.value, ast.Name) and n.value.id in {"bound", "enclosing"}})
    check("numeric_interval_ignores_source_speed_and_keeps_enclosing_speed", used_fields ==
          ["bound.acceleration", "bound.angular_speed", "enclosing.angular_speed", "enclosing.speed"])
    check("quantity_output_does_not_expose_source_speed", not any(isinstance(n, ast.Constant) and
          isinstance(n.value, str) and n.value == "carrier_speed_bound_m_per_s" for n in ast.walk(quantities)))
    reuse = text(EXPORT, "_reuse")
    check("foreign_work_without_cache_uses_original_calculation", 'if not hasattr(work, "lookup") or not hasattr(work, "remember"):' in reuse)
    check("reuse_order_is_lookup_calculate_then_remember", reuse.index("result = work.lookup(key)") <
          reuse.index("result = calculate()") < reuse.index("work.remember(key, result)"))
    lookup = text(NUMERIC, "lookup", "ReachExecutionWork")
    check("lookup_and_promotion_have_existing_charges", 'self.charge("cache_lookup")' in lookup and 'self.charge("cache_promote")' in lookup)
    check("lookup_rechecks_domain_and_presence_before_return", lookup.index('self.charge("cache_promote")') <
          lookup.index("if self._sync_cache_operand_limit() or operand_bits != self.max_operand_bits:") <
          lookup.rindex("if key not in self._cache:") < lookup.index("return self._cache[key]"))
    remember = text(NUMERIC, "remember", "ReachExecutionWork")
    check("existing_insert_and_eviction_charges_retained", 'self.charge("cache_insert")' in remember and
          'self.charge("cache_evict")' in remember)
    check("publication_checks_current_cache_generation", "generation != self._cache_generation" in remember)
    sync = text(NUMERIC, "_sync_cache_operand_limit", "ReachExecutionWork")
    check("operand_domain_change_clears_cache", 'self.charge("cache_operand_scope_reset")' in sync and "self._cache.clear()" in sync)
    charge = text(NUMERIC, "charge", "ReachExecutionWork")
    ordered = ["observer = self._source_after_charge", "self.external_check()", "if self.operations >= self.max_operations:",
               "self.operations += 1", "self.counts[kind] =", "observer()"]
    positions = [charge.index(value) for value in ordered]
    check("original_callback_budget_counter_observer_order", positions == sorted(positions))
    check("unchanged_cache_capacity_maximum_is_256", "(max_operand_bits, MAX_OPERAND_BITS), (max_cache_entries, 256)" in sources[NUMERIC].decode())
    historical = unique_json(sources[HISTORY + "/evidence/inputs-before.json"])
    historical_runtime = [r for r in historical["files"] if r["path"].startswith("ontokin/") and r["path"].endswith(".py")]
    runtime_paths = sorted(p.relative_to(repository).as_posix() for p in (repository / "ontokin").glob("*.py"))
    check("historical_runtime_inventory_matches_all_65_current_files", len(historical_runtime) == 65 and
          len({r["path"] for r in historical_runtime}) == 65 and sorted(r["path"] for r in historical_runtime) == runtime_paths)
    for row in historical_runtime:
        raw = sources[row["path"]]
        require(len(raw) == row["bytes"] and "sha256:" + sha256(raw) == row["sha256"] and
                git_blob(raw) == row["git_blob"], "C060 runtime byte equality: " + row["path"])
    check("all_65_runtime_files_match_c060_bytes", True)
    destination = text(EXPORT, "destination_numeric_bounds")
    check("one_destination_bound_charge_per_completed_quantity_call", destination.count('_charge(work, "destination_bound")') == 1)
    calls = [{"path": path, "line": call.lineno} for path in runtime_paths for call in ast.walk(trees[path])
             if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "destination_numeric_bounds"]
    check("single_destination_bound_runtime_callsite_is_inside_quantities", len(calls) == 1 and calls[0]["path"] == EXPORT and
          quantities.lineno < calls[0]["line"] < quantities.end_lineno)
    screen = derive(repository)
    for case in screen["cases"]:
        name = case["case"]
        summary = unique_json(sources[HISTORY + "/evidence/" + name + "/summary.json"])
        ledger = unique_json(sources[HISTORY + "/evidence/" + name + "/work-ledger.json"])
        request = unique_json(sources[HISTORY + "/evidence/" + name + "/request-result.json"])
        spans = [s for s in ledger["segments"] if s.get("after_marker") == "certification" and s.get("before_marker") == "encoding"]
        check(name + "_single_completed_certification_span", len(spans) == 1 and spans[0]["shared_minus_reach"] == 0)
        counters = spans[0]["reach_category_delta"]
        check(name + "_retained_group_counters_agree", counters["recording_certificate_group"] == case["group_visits"] and
              counters["destination_bound"] == case["baseline_group_calculations"])
        check(name + "_all_actual_enclosing_phase_sets_are_source_singletons", case["all_selected_equal_source_singleton"] is True)
        check(name + "_failed_request_status_preserved", summary["product_request_status"] == "failed" and
              summary["accepted_artifact"] is False and summary["complete_stock_harness"] is False and
              summary["final_shared_operations"] == 100001 and request["accepted_artifact"] is False)
        check(name + "_raw_glb_identity_matches_actual_request", request["unvalidated_reader_input"]["bytes"] == case["member_bytes"] and
              request["unvalidated_reader_input"]["sha256"] == "sha256:" + case["member_sha256"])
    requests = [(EXPORT, name, None) for name in ["MotionBound", "ReachPhase", "ReachPrefixPlan", "_reuse", "_exact",
                "_certificate_quantities", "interval_certificates", "enclosing_phases", "reach_prefix_plan",
                "reach_timeline", "complete_interval_bounds", "destination_numeric_bounds", "direct_binary32"]]
    requests += [(NUMERIC, name, "ReachExecutionWork") for name in
                 ["__init__", "charge", "guard", "guard_bits", "lookup", "remember", "_sync_cache_operand_limit"]]
    definitions = []
    for path, name, owner in requests:
        node = definition(path, name, owner)
        definitions.append({"path": path, "name": name, "owner": owner, "first_line": node.lineno,
                            "last_line": node.end_lineno, "sha256": sha256(text(path, name, owner).encode())})
    return {
        "schema_version": "ontokin.c071-source-and-retained-byte-derivation/0.1",
        "status": "passed",
        "baseline_commit": BASELINE_COMMIT,
        "baseline_tree": BASELINE_TREE,
        "source_binding_file_sha256": sha256(binding_raw),
        "source_bindings": verified,
        "source_binding_count": len(verified),
        "definitions": definitions,
        "definition_count": len(definitions),
        "checks": checks,
        "check_count": len(checks),
        "runtime_files_equal_to_historical_c060": len(historical_runtime),
        "actual_destination_bound_callsites": calls,
        "existing_key_expression": original_key,
        "interval_used_motion_fields": used_fields,
        "retained_byte_screen": screen,
        "logical_scope": {
            "name": "native_singleton_enclosing_phase_key_injectivity",
            "premises": ["passive native MotionBound field semantics", "all fields except source speed retained",
                         "enclosing speed retained", "selected is exactly the source phase", "unchanged runtime source"],
            "recovery": "bound.speed = enclosing.speed",
            "conclusion": "equal projected keys imply equal existing keys for both retained cohorts",
            "new_group_equivalence_hits_P11": 0,
            "new_group_equivalence_hits_L03": 0,
            "optimistic_direct_operation_saving_before_new_costs": 0,
            "cache_isomorphism_condition": "passive unchanged dispatch and paths, injective disjoint key renaming",
            "exact_numerical_tuples_reconstructed": False,
            "ordered_lru_events_reconstructed": False,
            "generic_mixed_phase_incidence": None,
            "universal_no_saving_theorem": False,
            "authority_safe_schedule_established": False,
            "positive_complete_request_premise_established": False,
        },
        "source_only": True,
        "product_imports_executed": 0,
        "product_requests_executed": 0,
        "runtime_suites_executed": 0,
        "native_trigonometric_evaluations": 0,
        "generated_meshes": 0,
        "historical_auditor_rerun": False,
        "release_acceptance": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path, nargs="?", default=Path(__file__).resolve().parents[3])
    parser.add_argument("--binding", type=Path, default=Path(__file__).with_name("source-binding.json"))
    arguments = parser.parse_args()
    print(json.dumps(source_derivation(arguments.repository, arguments.binding), indent=2, sort_keys=True))
