#!/usr/bin/env python3
"""Derive a C064 census from verified, retained C061 evidence only.

No OntoKin import, product evaluation, instrumentation, or failed-tail replay
occurs. The caller supplies the complete repository root. JSON is written to
stdout; this script does not write to the repository or extract archive files.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import struct
import zipfile


ARCHIVE_SHA256 = "417bc250d0028671ffd62c328b67f345d26f2cbce03eec453aeb25644a598f43"
C061_PATH = "docs/engineering/reach-recording-validation-2026-10-28-c061"
C060_PATH = "docs/engineering/reach-recording-validation-2026-10-28-c060"
SOURCE_ROOT = "docs/language-design/planar-reach-v0.1/"
SOURCE_INPUTS = (
    SOURCE_ROOT + "sources/p11-complete-segmented-character.ok",
    SOURCE_ROOT + "draft2-supplements/sources/l03-completed-action-new-owner.ok",
    SOURCE_ROOT + "libraries/reach-assets.ok",
    SOURCE_ROOT + "libraries/reach-parts.ok",
    SOURCE_ROOT + "libraries/reach-exterior.ok",
    "ontokin/reach_reference.py",
    "ontokin/reach_reference_plan.py",
    "ontokin/reach_reference_center.py",
    "ontokin/reach_conformance.py",
    "ontokin/geometry.py",
    "ontokin/scene.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def identity(raw):
    return {"bytes": len(raw), "sha256": digest(raw)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def safe_relative(path):
    value = PurePosixPath(path)
    require(not value.is_absolute() and ".." not in value.parts, "Unsafe archive path: " + path)
    return str(value)


def glb_document(raw):
    require(len(raw) >= 20, "Truncated retained GLB")
    magic, version, length = struct.unpack_from("<4sII", raw)
    require(magic == b"glTF" and version == 2 and length == len(raw), "Retained GLB header differs")
    size, kind = struct.unpack_from("<II", raw, 12)
    require(kind == 0x4E4F534A and 20 + size <= len(raw), "Retained GLB JSON chunk differs")
    return json.loads(raw[20:20 + size])


def geometry_census(document):
    occurrences, groups = [], {}
    for carrier, node in enumerate(document["nodes"]):
        metadata = node["extras"]["ontokin"]
        geometry = metadata["geometry"]
        row = {"carrier": carrier, "path": metadata["path"], "kind": geometry["kind"],
               "metadata_kind": metadata["kind"], "mesh_index": node.get("mesh"),
               "position_accessor": None, "position_count": 0, "primitive_count": 0}
        if "mesh" in node:
            primitives = document["meshes"][node["mesh"]]["primitives"]
            position = primitives[0]["attributes"]["POSITION"]
            accessor = document["accessors"][position]
            require(accessor["type"] == "VEC3", "Position accessor is not VEC3")
            require(all(p["attributes"]["POSITION"] == position for p in primitives),
                    "Retained material primitives do not share the expected position accessor")
            row.update(position_accessor=position, position_count=accessor["count"],
                       primitive_count=len(primitives))
        occurrences.append(row)
        group = groups.setdefault(canonical(geometry), {
            "geometry_descriptor_from_retained_bytes": geometry, "occurrence_paths": [],
            "vertices_per_occurrence": row["position_count"]})
        require(group["vertices_per_occurrence"] == row["position_count"],
                "Identical retained geometry descriptors have different position counts")
        group["occurrence_paths"].append(row["path"])
    return {
        "carrier_count": len(occurrences),
        "mesh_count": len(document["meshes"]),
        "occurrence_vertex_count": sum(row["position_count"] for row in occurrences),
        "occurrences": occurrences,
        "descriptor_groups": list(groups.values()),
        "limitations": [
            "These counts describe retained unvalidated reader-input bytes, not an accepted GLB.",
            "Material primitives sharing a position accessor are counted once per occurrence.",
            "Descriptors corroborate pinned source; retained metadata alone does not authorize source reuse.",
            "Source float64 vertex arrays and the scalar extrema witness sequence were not captured.",
        ],
    }


def plan_census(key_ledger):
    unique = {}
    for key in key_ledger["keys"]:
        for boundary in ("entry", "exit"):
            for plan in key.get(boundary, {}).get("source_batch", {}).get("plans", []):
                token = canonical(plan["cache_identity"])
                if token not in unique:
                    unique[token] = {"retained_plan": plan, "first_observed_key": key["index"],
                                     "first_observed_boundary": boundary,
                                     "last_observed_key": key["index"], "snapshot_occurrences": 0}
                value = unique[token]
                require(value["retained_plan"] == plan, "A retained plan identity has differing snapshot fields")
                value["last_observed_key"] = key["index"]
                value["snapshot_occurrences"] += 1
    for value in unique.values():
        plan = value["retained_plan"]
        value["target_count"] = len(plan["targets"])
        value["node_path_count"] = len(plan["node_paths"])
    return {
        "source_boundaries": key_ledger["source_boundaries"],
        "unique_plans": list(unique.values()),
        "captured_plan_fields": ["cache_identity", "context", "targets", "remaining",
                                 "registered_time", "node_paths"],
        "uncaptured_plan_fields": ["full plan.nodes", "node.stationary", "all body.identity_relative values",
                                   "all centered local vectors and radius recipes"],
        "opaque_identity_note": "Opaque context and cache IDs identify objects in the retained process only.",
    }


def derive(repository):
    root = repository.resolve()
    directory = root / C061_PATH
    manifest_raw = (directory / "evidence-manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    parts, part_identities = [], []
    for item in manifest["parts"]:
        path = safe_relative(item["path"])
        raw = (directory / path).read_bytes()
        require(len(raw) == item["bytes"] and digest(raw) == item["sha256"], "Archive part differs: " + path)
        parts.append(raw)
        part_identities.append({"path": C061_PATH + "/" + path, **identity(raw)})
    archive_raw = b"".join(parts)
    require(len(archive_raw) == manifest["archive"]["bytes"], "Archive length differs")
    require(digest(archive_raw) == manifest["archive"]["sha256"] == ARCHIVE_SHA256,
            "Archive identity differs from the retained C061 source")
    archive = zipfile.ZipFile(io.BytesIO(archive_raw))
    members = {item["path"]: item for item in manifest["members"]}
    require(len(members) == len(manifest["members"]), "Duplicate manifest member")
    require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate archive member")
    require(set(archive.namelist()) == set(members), "Archive member inventory differs")
    used = {}

    def read_member(path):
        safe_relative(path)
        raw = archive.read(path)
        expected = members[path]
        require(len(raw) == expected["bytes"] and digest(raw) == expected["sha256"],
                "Retained member differs: " + path)
        used[path] = identity(raw)
        return raw

    def member_json(path):
        return json.loads(read_member(path))

    source_identities = {}
    for path in SOURCE_INPUTS:
        raw = (root / path).read_bytes()
        archived = read_member("source/" + path)
        require(raw == archived, "Current source differs from frozen C061 input: " + path)
        source_identities[path] = identity(raw)

    decision_raw = (directory / "decision.json").read_bytes()
    decision = json.loads(decision_raw)
    cases, comparison_inputs = {}, {}
    for case in ("P11", "L03"):
        prefix = "evidence/round-001/" + case + "/"
        capture = member_json(prefix + "capture/capture.json")
        keys = member_json(prefix + "capture/key-ledger.json")
        setup = member_json(prefix + "audit-001/reader-setup-analysis.json")
        ledger = member_json(prefix + "audit-001/work-ledger.json")
        document = glb_document(read_member(prefix + "capture/unvalidated-reader-input.glb"))
        prior_path = C060_PATH + "/evidence/" + case + "/work-ledger.json"
        prior_raw = (root / prior_path).read_bytes()
        prior = json.loads(prior_raw)
        comparison_inputs[prior_path] = identity(prior_raw)
        for field in ("complete_reach_category_totals", "key_costs"):
            require(prior[field] == ledger[field], "C060/C061 ledger disagreement: " + case + " " + field)
        require([(s["kind"], s["shared_operations"]) for s in prior["segments"]] ==
                [(s["kind"], s["shared_operations"]) for s in ledger["segments"]],
                "C060/C061 segment cost disagreement: " + case)
        for field in ("observed_costs_by_label", "disjoint_stage_ledger"):
            require(setup[field] == decision["cases"][case][field], "C061 published setup disagreement: " + case)
        count = len(document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"])
        carriers = len(document["nodes"])
        rows = (count - 1) * carriers
        certificates = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
        require(rows == len(certificates), "Retained certificate census differs")
        require(len(keys["keys"]) == ledger["entered_keys"], "Entered key counts differ")
        require(count - ledger["entered_keys"] == len(ledger["unvisited_key_indices"]), "Unvisited key count differs")
        require(rows == ledger["provisional_interval_rows_traversed"] + ledger["interval_rows_not_yet_traversed"],
                "Interval row frontier differs")
        setup_segment = next(s for s in ledger["segments"] if s["kind"] == "reader_setup")
        reader_entry = capture["shared_operations_at_reader_entry"]
        require(reader_entry == setup_segment["start_shared_operations"], "Reader-entry counts differ")
        cap = capture["work_limits"]["max_operations"]
        require(cap == 100000, "Original operation cap differs")
        geometry = next(s for s in setup["disjoint_stage_ledger"] if s.get("label") == "reader._geometry_bounds")
        cases[case] = {
            "executed_source_commit": capture["source_commit"],
            "executed_source_tree": capture["source_tree"],
            "original_work_limits": capture["work_limits"],
            "product_status": capture["product_request_status"],
            "reader_entry_shared_operations": reader_entry,
            "whole_reader_budget_if_producer_unchanged": cap - reader_entry,
            "setup_shared_operations": setup_segment["shared_operations"],
            "first_key_entry_shared_operations": setup_segment["end_shared_operations"],
            "after_setup_budget_if_setup_unchanged": cap - setup_segment["end_shared_operations"],
            "original_key_count": count,
            "carrier_count": carriers,
            "interval_carrier_row_count": rows,
            "entered_keys_including_partial": ledger["entered_keys"],
            "returned_provisional_keys": ledger["returned_provisional_keys"],
            "wholly_unvisited_keys": len(ledger["unvisited_key_indices"]),
            "rows_not_yet_traversed": ledger["interval_rows_not_yet_traversed"],
            "selected_future_ticks_if_current_gates_unchanged":
                len(ledger["unvisited_key_indices"]) * carriers + 3 * ledger["interval_rows_not_yet_traversed"],
            "full_key_plus_three_row_gate_subtotal_if_unchanged": count * carriers + 3 * rows,
            "geometry_stage_shared_operations": geometry["shared_operations"],
            "geometry_stage_categories": geometry["reach_category_delta"],
            "geometry_census": geometry_census(document),
            "plan_census": plan_census(keys),
            "complete_request_cost": None,
            "measured_optimization_saving": None,
            "release_acceptance": False,
        }
    archive.close()
    return {
        "schema_version": "ontokin.c064-retained-evidence-derivation/0.1",
        "scope": "Offline census and arithmetic from retained failed-request evidence; no product execution",
        "source_checkpoint": "C061",
        "source_execution_commit": manifest["source_commit"],
        "source_execution_tree": manifest["source_tree"],
        "archive": {"name": manifest["archive"]["name"], **identity(archive_raw)},
        "input_files": {
            C061_PATH + "/evidence-manifest.json": identity(manifest_raw),
            C061_PATH + "/decision.json": identity(decision_raw),
            **comparison_inputs,
        },
        "verified_archive_parts": part_identities,
        "verified_used_members": used,
        "current_source_matches_frozen_inputs": source_identities,
        "cases": cases,
        "cost_claim_boundary": [
            "A positive net saving over the complete request can justify a scoped experiment without proving completion below 100000.",
            "Such a premise must bound added work, all future effects, fallbacks and cache consequences; prefix savings alone are insufficient.",
            "The reader budgets are completion conditions with the producer unchanged, not minimum savings for development admission.",
            "No source-plan flags or source float64 vertices absent from the capture are inferred as observed measurements.",
        ],
        "product_requests_executed": 0,
        "runtime_modules_imported": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    args = parser.parse_args()
    print(json.dumps(derive(args.repository), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
