#!/usr/bin/env python3
"""Audit raw C084 requests, replies, supplied slices and SQLite independently.

No OntoKin runtime module is imported. Successful edits are replayed as exact
UTF-8/attachment transactions, and every accepted identity is recomputed from
source/image bytes rather than taken from a receipt's claim.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import struct
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.keyed_merge_reference import (FREEZE_COMMIT, FREEZE_SHA256, PROTOCOL, STORE_SCHEMA, TARGET, GLB, bundle_identity,
    canonical, digest, exact_uv, expected_occurrences, file_payload, load_fixtures,
    loads, ordinary_path, require, sha)
from tools.keyed_merge_reference import codes, case_payload, check_transforms, check_reductions, check_panel_values, check_keyed_leaf_provenance, check_filters, check_all_locations, delivered_by_revision, panel_transform, walk, check_merges, diagnostic_anchor


def schema_validators(repository):
    """Resolve only local supplied schema files; no network schema retrieval."""
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    resources = {}
    for path in sorted((repository / "docs/language-design").rglob("*.schema.json")):
        schema = loads(path.read_bytes())
        if "$id" in schema:
            resources[schema["$id"]] = Resource.from_contents(schema)
    registry = Registry().with_resources(resources.items())
    result = {}
    for name in ("request.schema.json", "response.schema.json"):
        schema = loads(ordinary_path(repository, "docs/language-design/agent-v0.17/"+name).read_bytes())
        Draft202012Validator.check_schema(schema)
        result[name] = Draft202012Validator(schema, registry=registry)
    return result


def terminal_refusals(rows, code):
    """Historical target diagnostics in a successful status reply are not new refusals."""
    return [row for row in rows if (row.get("response") or {}).get("status") in ("failed", "rejected")
            and code in codes(row["response"])]


def normalized(payload):
    result = copy.deepcopy(payload)
    result["modules"].sort(key=lambda unit: (unit["package_id"], unit["version"]))
    result["assets"].sort(key=lambda unit: unit["asset_id"])
    return result


def source_units(payload):
    return {"entry": payload["entry"], **{
        "package:" + unit["package_id"] + "@" + unit["version"]: unit for unit in payload["modules"]}}


def replay_edit(before, request):
    """Apply independent original-byte preconditions, then one atomic candidate."""
    require(bundle_identity(before)[0] == request["expected_program_revision"], "Edit original revision differs")
    result = copy.deepcopy(before)
    original, units = source_units(before), source_units(result)
    patches = defaultdict(list)
    for patch in request["patches"]:
        key = patch["source_id"]
        require(key in original and patch["element_id"] == ["sources", key], "Edit source identity differs")
        raw = original[key]["source"].encode("utf-8")
        require(digest(raw) == patch["source_revision"], "Edit source digest precondition differs")
        start, end = patch["start_byte"], patch["end_byte"]
        require(type(start) is int and type(end) is int and 0 <= start <= end <= len(raw), "Edit UTF-8 byte range")
        require(raw[start:end] == patch["expected_text"].encode("utf-8"), "Edit original byte precondition differs")
        patches[key].append((start, end, patch["replacement"].encode("utf-8")))
    for key, changes in patches.items():
        changes.sort()
        require(all(a[1] <= b[0] for a, b in zip(changes, changes[1:])), "Overlapping accepted patch ranges")
        raw, end, pieces = original[key]["source"].encode("utf-8"), 0, []
        for start, stop, replacement in changes:
            pieces.extend((raw[end:start], replacement)); end = stop
        pieces.append(raw[end:])
        units[key]["source"] = b"".join(pieces).decode("utf-8", errors="strict")
    require(not request.get("module_changes"), "Finite C084 workflows must not silently add unprescribed module edits")
    assets = {asset["asset_id"]: asset for asset in result["assets"]}
    original_assets, touched = {asset["asset_id"]: asset for asset in before["assets"]}, set()
    for change in request.get("asset_changes", []):
        operation = change["operation"]
        key = change["asset"]["asset_id"] if operation == "add" else change["asset_id"]
        require(key not in touched, "An accepted candidate touched one asset ID twice")
        touched.add(key)
        if operation == "add":
            require(key not in original_assets, "Accepted addition overwrote an original attachment")
        else:
            require(key in original_assets and original_assets[key]["sha256"] == change["expected_sha256"], "Accepted asset digest precondition differs")
        if operation == "remove":
            del assets[key]
        else:
            require(change["asset"]["asset_id"] == key, "Accepted replacement changed stable ID")
            assets[key] = copy.deepcopy(change["asset"])
    result["assets"] = list(assets.values())
    bundle_identity(result)  # independently check attachment digests/base64
    return normalized(result)


def retained_keys(state):
    return {key: state[key] for key in ("accepted_program_revision", "accepted_payload_sha256", "assets")}


def inspect_asset(request, response, payload):
    result = response["result"]
    assets = {a["asset_id"]: a for a in payload["assets"]}
    revision = bundle_identity(payload)[0]
    for item in result.get("items", []):
        key = item["name"]
        require(key in assets and item["element_id"] == ["assets", key] and item["kind"] == "texture_asset", "Asset metadata identity differs")
        asset = assets[key]; raw = base64.b64decode(asset["data_base64"], validate=True)
        if "identity" in request["fields"]:
            require(item["identity"] == {"asset_id": key, "element_id": ["assets", key], "kind": "texture_asset"}, "Asset identity metadata differs")
        if "source" in request["fields"]:
            require(item["source"] == {"asset_id": key, "program_revision": revision,
                "sha256": digest(raw), "media_type": "image/png", "total_bytes": len(raw)}, "Asset source metadata differs")
    if "asset_slice" not in request:
        return {"metadata_items": len(result.get("items", []))}
    key = request["selector"]["element_id"][1]
    raw = base64.b64decode(assets[key]["data_base64"], validate=True)
    offset, count = request["asset_slice"]["offset"], request["asset_slice"]["max_bytes"]
    end = min(offset + count, len(raw))
    returned = base64.b64decode(result["data_base64"], validate=True)
    require(returned == raw[offset:end] and result["data_base64"] == base64.b64encode(returned).decode(), "Actual asset slice differs from exact original PNG bytes")
    for field, expected in {"asset_id": key, "element_id": ["assets", key], "program_revision": revision,
        "sha256": digest(raw), "media_type": "image/png", "total_bytes": len(raw), "offset": offset,
        "returned_bytes": end - offset, "next_offset": end if end < len(raw) else None,
        "complete": end == len(raw)}.items():
        require(type(result[field]) is type(expected) and result[field] == expected, "Actual asset slice metadata differs: " + field)
    require(response.get("next_cursor") is None and not response.get("truncated", False), "Raw asset slice acquired metadata cursor semantics")
    return {"asset_id": key, "offset": offset, "bytes": len(returned), "total_bytes": len(raw),
            "sha256": sha(returned), "complete": result["complete"]}


def inspect_surface(request, response, payload, case):
    result = response["result"]
    wanted = expected_occurrences(case)[result["path"]]
    require(result["program_revision"] == case["program_revision"] and result["element_id"] == request["element_id"], "Mesh page source/occurrence binding differs")
    require(result["texture_coordinate_system"] == "raw_unplaced_recipe_local_affine", "Mesh page texture coordinate convention differs")
    require(set(result["texture_bindings"]) == set(wanted["bindings"]), "Inspected regional texture inventory differs")
    assets, units = {a["asset_id"]: a for a in payload["assets"]}, source_units(payload)
    for key, expected in wanted["bindings"].items():
        actual = result["texture_bindings"][key]
        require(actual["asset_id"] == expected["asset_id"] and actual["sha256"] == assets[expected["asset_id"]]["sha256"], "Inspected region selects wrong image")
        require(all(actual[field] == value for field, value in expected["mapping"].items()), "Inspected authored affine map differs")
        require(actual["source_id"] in units, "Mapping provenance names absent source")
        raw = units[actual["source_id"]]["source"].encode()
        require(type(actual["start"]) is int and type(actual["end"]) is int and
                0 <= actual["start"] < actual["end"] <= len(raw), "Mapping source span is out of range")
        require(b"texture_binding" in raw[actual["start"]:actual["end"]], "Mapping provenance span omits authored binding")
    points, uvs = result["positions_m"], result["texcoords_0"]
    require(len(points) == len(uvs) == 3 * result["returned_triangles"], "Mesh page UV cardinality differs")
    corners = {tuple(point) for point in wanted["raw_corner_set_m"]}
    require(all(tuple(point) in corners for point in points), "Mesh page vertex differs from independently frozen prism corners")
    checked = 0
    for triangle, region in zip(result["triangles"], result["region_keys"]):
        binding = wanted["bindings"].get(region)
        for index in triangle:
            if binding is None:
                require(uvs[index] is None, "Untextured page corner acquired UV")
            else:
                expected = exact_uv(points[index], binding["mapping"])
                require(struct.pack("<2f", *uvs[index]) == struct.pack("<2f", *expected), "Inspected UV differs from independent authored map")
                checked += 1
    return {"path": result["path"], "triangles": result["returned_triangles"], "uv_rows": checked,
            "program_revision": result["program_revision"]}


def audit_workflows(results, fixtures, summary, rows, sources, requests, artifacts, runs, report):
    cases, coverage = fixtures["cases"], []
    by_id = {w["id"]: w for w in summary["workflows"]}
    for spec in fixtures["workflows"]["workflows"]:
        observed = rows[spec["id"]]
        require(observed and spec["id"] in by_id, "Frozen workflow omitted actual operations")
        descriptor = by_id[spec["id"]]
        require(descriptor["status"] == "observed_as_expected" and descriptor["name"] == spec["name"], "Actual frozen workflow failed")
        require(descriptor["first_exchange"] == observed[0]["sequence"] and descriptor["last_exchange"] == observed[-1]["sequence"], "Workflow boundaries do not match raw exchanges")
        require(set(spec["operations"]) <= {r["request"]["operation"] for r in observed}, "Frozen workflow operation coverage differs")
        coverage.append({"id": spec["id"], "raw_exchanges": len(observed), "status": "passed"})
    reopens = loads(ordinary_path(results, "agent/reopen-log.json").read_bytes())
    require(reopens == summary["reopens"] and {r["workflow"] for r in reopens} == {"A03", "A04", "A05", "A08"},
            "Explicit fresh-service reopen evidence is missing")
    for record in reopens:
        require(Path(record["store_path"]).name == "keyed-merge-program-agent.sqlite3",
                "Actual live Agent .17 service used another store filename")
        require(record["old_session_owner"] != record["new_session_owner"] and record["before"] == record["after"] and
                record["old_implementation"] == record["new_implementation"], "Reopen changed accepted state or reused a session")
        require(any(r["sequence"] == record["after_exchange"] for r in rows[record["workflow"]]), "Reopen has no exact raw exchange boundary")
        if record["workflow"] == "A05":
            require(record["old_host_policy"] == {"max_operations":400000, "max_elapsed_ms":80000} and
                    record["new_host_policy"] == {"max_operations":100000, "max_elapsed_ms":30000}, "Fresh service did not actually reduce current authority")
        if record["workflow"] == "A08":
            require("interruption" in record["store_path"].split("/"), "Publication reopen used another store")
    def successful(group, operation):
        return [r for r in rows[group] if r["request"]["operation"] == operation and (r.get("response") or {}).get("status") == "succeeded"]
    def refusals(group, code):
        return terminal_refusals(rows[group], code)
    def unchanged(row, *, all_effects=True):
        before, after = row["state_before"], row["state_after"]
        require(before == after if all_effects else retained_keys(before) == retained_keys(after), "Failed/cancelled workflow published a partial state")

    # A01: independently replay the exact add and removal, then bind old
    # membership/run/artifact observations to the earlier immutable revisions.
    edited = successful("A01", "edit")
    require(len(edited) == 2, "Optional-union workflow must accept exactly add then removal")
    add, remove = edited
    base_case, added_case, removed_case = (cases[name] for name in ("panel-task", "panel-task-repaired", "panel-task-removed"))
    before, after, restored = (case_payload(fixtures, case) for case in (base_case, added_case, removed_case))
    require(normalized(replay_edit(before, add["request"])) == normalized(after) and
            normalized(replay_edit(after, remove["request"])) == normalized(restored) == normalized(before),
            "Add/removal are not exactly the independently frozen two-occurrence candidates")
    require(before["modules"] == after["modules"] == restored["modules"] and
            before["assets"] == after["assets"] == restored["assets"], "Optional repair changed pinned library/PNG bytes")
    for edit, expected_text, replacement in ((add, "include_optional = false;", "include_optional = true;"),
                                              (remove, "include_optional = true;", "include_optional = false;")):
        patches = edit["request"]["patches"]
        require(len(patches) == 1 and patches[0]["source_id"] == "entry" and
                patches[0]["expected_text"] == expected_text and patches[0]["replacement"] == replacement,
                "Optional repair did not use the exact first-occurrence parameter precondition")
    base_revision, added_revision = base_case["program_revision"], added_case["program_revision"]
    revisions = {base_revision, added_revision}
    require(removed_case["program_revision"] == base_revision, "Source restoration failed exact immutable identity")
    for operation in ("inspect", "surface.mesh_page", "evaluate", "export"):
        operations = successful("A01", operation)
        require({row["request"].get("program_revision") for row in operations} == revisions,
                "Optional repair lacks actual before/added " + operation)
        require(any(row["sequence"] > remove["sequence"] and row["request"].get("program_revision") == base_revision
                    for row in operations), "Removal lacks actual restored-source " + operation)
    frozen_by_revision = delivered_by_revision(fixtures)
    for row in successful("A01", "inspect") + successful("A05", "inspect") + successful("A10", "inspect"):
        request, response = row["request"], row["response"]
        case = frozen_by_revision[request["program_revision"]]
        units = source_units(sources[(request["project_id"], request["program_revision"])])
        check_all_locations(response["result"], units)
        check_panel_values(response["result"].get("items", []), case, fixtures, units)
        for _, node in walk(response["result"]):
            if not isinstance(node, dict):
                continue
            for suffix, reader in (("transforms", check_transforms), ("reductions", check_reductions),
                                   ("filters", check_filters), ("merges", check_merges)):
                for field in ("derived_" + suffix, "input_" + suffix):
                    if field in node:
                        reader(node[field], units)
    exports = [artifact for artifact in summary["agent_artifacts"] if artifact["project_id"] == "c084-a01"]
    require({artifact["program_revision"] for artifact in exports} == revisions,
            "Optional repair lacks both immutable native artifact revisions")
    decoded = {artifact["program_revision"]: GLB(ordinary_path(results, artifact["glb"]).read_bytes(), target=TARGET) for artifact in exports}
    old, new = decoded[base_revision], decoded[added_revision]
    spec = fixtures["workflows"]["workflows"][0]["expected"]
    old_geometry, new_geometry = old.geometry_streams(), new.geometry_streams()
    for path in spec["surviving_unchanged_paths"]:
        require({key:value for key,value in old_geometry.items() if key[0] == path} ==
                {key:value for key,value in new_geometry.items() if key[0] == path}, "Optional repair changed unrelated native geometry")
    require(set(old.objects()) - set(new.objects()) == set(spec["removed_paths"]) and
            set(new.objects()) - set(old.objects()) == set(spec["added_paths"]), "Optional repair changed another occurrence membership")
    old_motion, new_motion = old.animation_streams(), new.animation_streams()
    for path in spec["unchanged_motion_paths"]:
        require({key:value for key,value in old_motion.items() if key[0] == path} ==
                {key:value for key,value in new_motion.items() if key[0] == path}, "Optional repair changed unrelated motion")
    for revision, transition, accepted in ((base_revision, add, added_revision), (added_revision, remove, base_revision)):
        evaluations = [row for row in successful("A01", "evaluate")
                       if row["request"]["program_revision"] == revision and row["sequence"] < transition["sequence"]]
        require(evaluations, "Retained old run has no actual preceding evaluation")
        original = evaluations[0]
        run_id = original["response"].get("run_id") or (original["response"].get("result") or {}).get("run_id")
        require(run_id and any(run["project_id"] == "c084-a01" and run["id"] == run_id and
                               run["source_revision"] == revision for run in runs), "Old run lost its durable original revision")
        pinned = [row for row in successful("A01", "inspect") if row["sequence"] > transition["sequence"] and
                  row["request"].get("run_id") == run_id and row["state_before"]["accepted_program_revision"] == accepted]
        require(pinned and all(row["request"]["program_revision"] == row["response"]["program_revision"] == revision and
                               row["state_after"]["accepted_program_revision"] == accepted for row in pinned),
                "Old run was not inspected under its original revision after accepted membership changed")
        originals = [row for row in successful("A01", "export")
                     if row["request"]["program_revision"] == revision and row["sequence"] < transition["sequence"]]
        ids = {row["response"]["result"]["artifact_id"] for row in originals}
        require(ids and any(row["sequence"] > transition["sequence"] and row["request"]["artifact_id"] in ids
                            and row["state_before"]["accepted_program_revision"] == accepted
                            for row in successful("A01", "artifact")), "Old artifact was not retrieved after membership changed")
        retained = [ordinary_path(results, artifact["glb"]).read_bytes() for artifact in exports
                    if artifact["program_revision"] == revision]
        require(len(retained) >= 2 and len(set(retained)) == 1, "Earlier complete artifact bytes changed on bounded re-retrieval")

    # A02/A03: inspect actual candidate retention and actual issued cursor reuse.
    invalid = refusals("A02", "OKL-E-NAME")
    stale_edits = refusals("A02", "OKL-E-REVISION")
    require(len(invalid) == len(stale_edits) == 1, "Rollback/stale-revision probes were not both exercised")
    unchanged(invalid[0]); unchanged(stale_edits[0])
    require(("c084-a02", cases["panel-task-invalid"]["program_revision"]) in sources, "Rejected candidate bytes were not retained")
    collisions = refusals("A02", "OKL-E-ID")
    require(len(collisions) == 1, "Rollback workflow omitted the colliding optional-input candidate")
    unchanged(collisions[0])
    collision_case = cases["panel-task-collision"]
    require(("c084-a02", collision_case["program_revision"]) in sources, "Rejected collision candidate bytes were not retained")
    diagnostic_anchor(collisions[0]["response"], collision_case, source_units(case_payload(fixtures, collision_case)))
    stale_cursor = refusals("A03", "OKL-E-REVISION")
    require({r["request"]["operation"] for r in stale_cursor} == {"inspect", "surface.mesh_page"} and len(stale_cursor) == 2,
            "Ordinary and native mesh stale cursors were not separately refused")
    for row in stale_cursor:
        unchanged(row)
        cursor = row["request"]["cursor"]
        issued = [r for r in successful("A03", row["request"]["operation"]) if r["response"].get("next_cursor") == cursor]
        require(issued and issued[0]["request"]["program_revision"] == cases["panel-task"]["program_revision"] and
                row["request"]["program_revision"] == cases["panel-task-repaired"]["program_revision"], "Stale cursor was not the real older-revision token")

    # A04: same request ID exact replay and different payload conflict.
    retries = [r for r in report["request_retries"] if r["project_id"] == "c084-a04"]
    require(len(retries) >= 2 and len(refusals("A04", "OKL-E-REQUEST-ID")) == 1, "Reopen workflow omitted exact create/export retry or changed-payload refusal")
    for row in refusals("A04", "OKL-E-REQUEST-ID"):
        unchanged(row)

    # A05: seven distinct fresh requests under reduced current host policy.
    reduced = refusals("A05", "OKL-E-RESOURCE")
    expected_operations = Counter({"validate":1, "inspect":2, "surface.mesh_page":1, "evaluate":1, "export":1, "artifact":1})
    require(Counter(r["request"]["operation"] for r in reduced) == expected_operations, "Reduced current host authority did not refuse every required operation")
    require(any("asset_slice" in r["request"] for r in reduced), "Reduced host policy did not cover exact asset retrieval")
    for row in reduced:
        unchanged(row)
        require(row["host_policy"] == {"max_operations":100000, "max_elapsed_ms":30000}, "Reduced operation retained earlier higher authority")
    require(successful("A05", "export") and all(r["host_policy"] == {"max_operations":400000, "max_elapsed_ms":80000} for r in successful("A05", "export")), "Higher source was never independently admitted under higher host authority")

    # A06: inherited item selector bound plus shared operation/value bounds.
    capped = [r for r in rows["A06"] if r["request"].get("budgets")]
    require(len(capped) >= 8, "Caller cap workflow omitted frozen bound attempts")
    json_refusals = []
    for row in capped:
        diagnostics = [node for _, node in walk(row["response"])
                       if isinstance(node, dict) and node.get("code") in ("OKA-E-RESOURCE", "OKL-E-RESOURCE")]
        json_bounds = [node for node in diagnostics
                       if node.get("details", {}).get("budget") in ("logical_json_entries", "encoded_json_bytes")]
        if json_bounds:
            require(row["request"]["budgets"].get("max_value_entries") == 1 and
                    row["response"]["status"] in ("failed", "rejected"),
                    "JSON exhaustion is not bound to the smallest supported caller result cap")
            for diagnostic in json_bounds:
                details = diagnostic["details"]
                require(details["budget"] == "logical_json_entries" and details["limit"] == 1 and
                        type(details["consumed"]) is int and details["consumed"] > 1,
                        "Actual JSON bound is not the exact lowered supported caller limit")
            json_refusals.append(row)
        else:
            wanted = "OKL-E-SAMPLE" if "max_result_items" in row["request"]["budgets"] else "OKL-E-RESOURCE"
            require(wanted in codes(row["response"]), "Caller cap reached the wrong failure contract")
        unchanged(row)
        require(not (row["response"].get("result") or {}).get("items"), "Exhausted caller budget exposed partial result items")
    require(json_refusals, "Frozen A06 lacks an actual JSON response-bound refusal distinct from typed-value copying")

    # A07: two independent interventions at genuine collision/copy stages.
    retained_barriers = loads(ordinary_path(results, "agent/cancellation-barriers.json").read_bytes())
    barriers = retained_barriers["barriers"] if isinstance(retained_barriers, dict) else retained_barriers
    required_stages = {"keyed_merge_collision", "keyed_merge_iteration"}
    require(isinstance(barriers, list) and len(barriers) == 2 and
            {barrier["stage"] for barrier in barriers} == required_stages and
            len({barrier["request_id"] for barrier in barriers}) == 2,
            "Cancellation must independently execute each adopted merge checkpoint stage")
    for barrier in barriers:
        require(barrier["actual_merge_checkpoint_reached"] is True and not barrier["worker_errors"] and barrier["checkpoints"],
                "Cancellation never reached actual admitted merge work")
        require(barrier["checkpoints"][-1]["stage"] == barrier["stage"], "Cancellation did not pause at the specified actual stage")
        cancelled = [row for row in rows["A07"] if row["request"]["request_id"] == barrier["request_id"] and
                     (row.get("response") or {}).get("status") == "cancelled"]
        require(cancelled and all(row["request"]["operation"] == "validate" for row in cancelled),
                "Cancellation lost its original validation request identity")
        for row in cancelled:
            unchanged(row)
            require(not {"OKL-E-TYPE", "OKL-E-ID"} & set(codes(row["response"])), "Cancellation callback became a type/collision error")
        previous_operations = -1
        for checkpoint in barrier["checkpoints"]:
            require(checkpoint["stage"] in required_stages and checkpoint["consumed_operations"] > previous_operations and
                    checkpoint["request_id"] == barrier["request_id"] and
                    checkpoint["program_revision"] == cases["maximum-256"]["program_revision"],
                    "Cancellation checkpoint was not actual current admitted merge work")
            previous_operations = checkpoint["consumed_operations"]

    # A08: actual prepared bytes, transactional rollback, truthful status and
    # successful new-ID retry. The same content-addressed bytes may then exist.
    publication = loads(ordinary_path(results, "agent/publication-interruption.json").read_bytes())
    require(publication["before"] == publication["after"] and len(publication["prepared_only"]) == 1, "Interrupted SQLite publication leaked effects")
    prepared = publication["prepared_only"][0]
    require(prepared["sqlite_transaction_active"] is True and "interruption" in prepared["store_path"].split("/"),
            "Fault was not inside the actual isolated SQLite publication transaction")
    raw = ordinary_path(results, prepared["glb"]).read_bytes()
    require(sha(raw) == prepared["sha256"] and len(raw) == prepared["bytes"] and GLB(raw, target=TARGET).document["extras"]["ontokin"]["program"]["revision"] == cases["panel-task"]["program_revision"], "Publication interruption did not preserve actual source-bound prepared bytes")
    interrupted = requests[("c084-a08", prepared["request_id"])]
    require(interrupted["state"] in ("unknown_outcome", "failed", "cancelled"), "Interrupted publication incorrectly claims success")
    require(publication["status_response"]["result"]["target_status"] == interrupted["state"], "Reopened status hid the true interrupted durable state")
    require(refusals("A08", "OKA-E-ARTIFACT"), "Uncommitted prepared artifact was not queried/refused before retry")
    retry_exports = successful("A08", "export")
    require(retry_exports and all(r["request"]["request_id"] != prepared["request_id"] for r in retry_exports), "Interrupted publication did not use a successful fresh-ID retry")
    if ("c084-a08", prepared["artifact_id"]) in artifacts:
        provenance = loads(artifacts[("c084-a08", prepared["artifact_id"])]["report"])
        require(provenance["producer_request_id"] != prepared["request_id"], "Interrupted transaction owns the later visible artifact")

    # A09: assemble real ordered PNG slices including exact empty EOF.
    slices = [r for r in successful("A09", "inspect") if "asset_slice" in r["request"]]
    require(slices, "Missing exact asset byte retrieval")
    offset, parts = 0, []
    for row in slices:
        require(row["request"]["asset_slice"]["offset"] == offset, "Actual asset slices are not contiguous")
        part = base64.b64decode(row["response"]["result"]["data_base64"], validate=True)
        parts.append(part); offset += len(part)
    source_png = base64.b64decode(case_payload(fixtures, cases["panel-task"])["assets"][0]["data_base64"], validate=True)
    require(b"".join(parts) == source_png and parts[-1] == b"" and slices[-1]["response"]["result"]["complete"], "Asset full-byte/EOF result differs")
    require(ordinary_path(results, "agent/retrieved-label.png").read_bytes() == source_png and len(refusals("A09", "OKA-E-REQUEST")) == 1, "Asset retrieval/past-EOF refusal differs")

    # A10's artifact is independently source/control/byte checked by the
    # companion reader; this audit binds the same actual request/store lineage.
    require(successful("A10", "export") and any(a["project_id"] == "c084-a10" and a["program_revision"] == cases["panel-identity"]["program_revision"] for a in summary["agent_artifacts"]), "Merge control workflow lacks its actual retrieved export")
    return coverage


def audit(results, fixtures):
    summary = loads(ordinary_path(results, "summary.json").read_bytes())
    require(summary["frozen_input_commit"] == FREEZE_COMMIT and summary["frozen_manifest_sha256"] == FREEZE_SHA256,
            "Raw audit requires the exact published C084 freeze")
    validators = schema_validators(fixtures["repository"])
    transcript = loads(ordinary_path(results, "agent/transcript.json").read_bytes())
    jsonl = [loads(line) for line in ordinary_path(results, "agent/transcript.jsonl").read_bytes().splitlines()]
    require(transcript == jsonl and transcript, "Raw transcript representations differ or are empty")
    require([row["sequence"] for row in transcript] == list(range(1, len(transcript) + 1)), "Raw exchanges lack exact order")
    for row in transcript:
        require(loads(ordinary_path(results, f"agent/exchange-{row['sequence']:04}.json").read_bytes()) == row,
                "Individual raw exchange differs from transcript")
    stores = [summary["store"], *summary.get("additional_stores", [])]
    require(len(stores) == 2 and stores[1].get("workflow") == "A08" and stores[0]["path"] != stores[1]["path"],
            "A08 publication must use a distinct retained isolated store")
    sources, requests, artifacts, projects, runs, database_records = {}, {}, {}, {}, [], []
    raw_snapshots = {}
    for store in stores:
        database = ordinary_path(results, store["path"])
        raw = database.read_bytes()
        require(sha(raw) == store["sha256"] and len(raw) == store["bytes"], "Retained SQLite identity differs")
        connection = sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            require([r[0] for r in connection.execute("PRAGMA integrity_check")] == ["ok"], "Retained SQLite integrity failure")
            require(connection.execute("SELECT value FROM metadata WHERE name='schema_version'").fetchone()[0] == STORE_SCHEMA,
                    "Wrong separate .17 store schema")
            store_projects = {r["id"]: r["accepted_revision"] for r in connection.execute("SELECT * FROM projects")}
            require(not set(store_projects) & set(projects), "A project crossed the isolated store boundary")
            if store.get("workflow") == "A08":
                require(set(store_projects) == {"c084-a08"}, "Publication store is not isolated to A08")
            projects.update(store_projects)
            for r in connection.execute("SELECT * FROM sources"):
                key = (r["project_id"], r["revision"])
                raw_snapshots[key] = bytes(r["raw"])
                sources[key] = loads(raw_snapshots[key])
            requests.update({(r["project_id"], r["id"]): dict(r) for r in connection.execute("SELECT * FROM requests ORDER BY sequence")})
            artifacts.update({(r["project_id"], r["id"]): dict(r) for r in connection.execute("SELECT * FROM artifacts")})
            runs.extend(dict(r) for r in connection.execute("SELECT * FROM runs"))
            database_records.append({"path": store["path"], "sha256": sha(raw), "bytes": len(raw), "projects": sorted(store_projects)})
        finally:
            connection.close()
    snapshots = {(s["project_id"], s["program_revision"]): s for s in summary["snapshots"]}
    require(len(snapshots) == len(summary["snapshots"]) and set(snapshots) == set(sources), "Extracted snapshot inventory differs from actual stores")
    for key, retained in snapshots.items():
        raw = ordinary_path(results, retained["path"]).read_bytes()
        require(raw == raw_snapshots[key] and len(raw) == retained["bytes"] and sha(raw) == retained["sha256"], "Extracted source snapshot differs from actual SQLite bytes")
    report = {"schema_version": "ontokin.c084-independent-agent-audit/0.1", "status": "running",
        "frozen_input_commit": FREEZE_COMMIT, "actual_git": summary["git"], "release_acceptance": False,
        "frozen_manifest_sha256": FREEZE_SHA256, "databases": database_records, "source_snapshots": [], "accepted_edits": [],
        "asset_inspections": [], "surface_pages": [], "artifact_slices": 0,
        "request_retries": [], "durable_payload_tombstones": [], "failures": []}
    for (project, revision), payload in sources.items():
        actual, manifest = bundle_identity(payload)
        require(actual == revision, "Durable source/image revision does not match actual bytes")
        report["source_snapshots"].append({"project_id": project, "program_revision": revision,
            "payload_sha256": sha(canonical(payload)), "source_units": len(manifest["units"]), "assets": manifest["assets"]})
    observed_keys = {(r["request"]["project_id"], r["request"]["request_id"]) for r in transcript}
    require(observed_keys == set(requests), "Every usable raw request identity must have exactly one durable row")
    frozen_cases = delivered_by_revision(fixtures)
    previous, seen, operation_counts, workflow_rows = {}, {}, defaultdict(int), defaultdict(list)
    for row in transcript:
        request = row["request"]; project, request_id, operation = request["project_id"], request["request_id"], request["operation"]
        key, stored = (project, request_id), requests[(project, request_id)]
        require(request["schema_version"] == PROTOCOL, "Wrong actual request contract")
        require(not row.get("request_schema_errors") and not row.get("response_schema_errors"), "Actual protocol schema failed producer validation")
        require(not list(validators["request.schema.json"].iter_errors(request)), "Independent actual request schema failure")
        if row.get("response") is not None:
            require(not list(validators["response.schema.json"].iter_errors(row["response"])), "Independent actual response schema failure")
        workflow_rows[row["workflow"]].append(row)
        operation_counts[operation] += 1
        if stored["payload"] is None:
            # Interrupted/expired work intentionally retains identity+digest,
            # clears replayable payload, and exposes unknown_outcome. Recover
            # the audit input only from independently retained raw exchanges.
            terminal = loads(stored["response"])
            require(stored["state"] == "unknown_outcome" and
                    (terminal.get("protocol_error") or {}).get("code") == "OKA-E-UNKNOWN-OUTCOME" and
                    (terminal.get("protocol_error") or {}).get("details", {}).get("replay_permitted") is False,
                    "Missing durable payload is not an explicit non-replayable tombstone")
            originals = [r["request"] for r in transcript if
                (r["request"]["project_id"], r["request"]["request_id"]) == key and
                sha(canonical(r["request"])) == stored["digest"]]
            require(originals and all(canonical(r) == canonical(originals[0]) for r in originals),
                    "Tombstone digest has no exact retained original request")
            original_request = originals[0]
            if not any(r["project_id"] == project and r["request_id"] == request_id for r in report["durable_payload_tombstones"]):
                report["durable_payload_tombstones"].append({"project_id": project, "request_id": request_id,
                    "digest": stored["digest"], "state": stored["state"], "replay_permitted": False,
                    "original_payload_evidence": "exact hash-matching raw request retained outside the durable tombstone"})
        else:
            original_request = loads(stored["payload"])
            require(sha(stored["payload"].encode()) == stored["digest"] and canonical(original_request).decode() == stored["payload"], "Durable request digest/canonical payload differs")
        before, after = row["state_before"], row["state_after"]
        for state in (before, after):
            revision = state["accepted_program_revision"]
            if revision is not None:
                payload = sources[(project, revision)]
                require(sha(canonical(payload)) == state["accepted_payload_sha256"], "State receipt accepted bytes differ from actual retained source")
                expected_assets = [{k: a[k] for k in ("asset_id", "sha256", "media_type")} |
                                   {"bytes": len(base64.b64decode(a["data_base64"], validate=True))} for a in payload["assets"]]
                require(state["assets"] == expected_assets, "State receipt accepted asset identities differ")
        if project in previous:
            require(previous[project]["accepted_program_revision"] == before["accepted_program_revision"] and
                    previous[project]["accepted_payload_sha256"] == before["accepted_payload_sha256"],
                    "Accepted state changed outside recorded authoring operation")
        previous[project] = after
        response = row.get("response")
        if response is None:
            require(row["workflow"] == "A08" and row.get("exception", {}).get("exception") == "PublicationInterruption", "Unexplained missing actual response")
            continue
        require(response["schema_version"] == PROTOCOL and response["request_id"] == request_id and response["project_id"] == project,
                "Raw response belongs to another request")
        changed_retry = canonical(request) != canonical(original_request)
        if changed_retry:
            require(response["status"] == "rejected" and "OKL-E-REQUEST-ID" in codes(response), "Changed request identity did not conflict")
            require(before == after, "Changed retry altered durable product state")
        elif key in seen and seen[key]["status"] not in ("queued", "running"):
            require(response == seen[key], "Identical terminal retry did not recover exact durable receipt")
            report["request_retries"].append({"project_id": project, "request_id": request_id, "exact_receipt_recovered": True})
        if not changed_retry:
            seen[key] = response
        success = response["status"] == "succeeded"
        if success and operation in ("create", "edit") and not changed_retry:
            candidate = normalized(request["bundle"]) if operation == "create" else replay_edit(sources[(project, request["expected_program_revision"])], request)
            revision = bundle_identity(candidate)[0]
            require(response["accepted_program_revision"] == revision == after["accepted_program_revision"], "Atomic accepted candidate revision differs")
            require(normalized(sources[(project, revision)]) == candidate, "Durable acceptance differs from exact independent source/asset candidate")
            if operation == "edit":
                report["accepted_edits"].append({"project_id": project, "request_id": request_id,
                    "program_revision": revision, "asset_operations": [a["operation"] for a in request.get("asset_changes", [])],
                    "source_patch_count": len(request["patches"])})
        elif operation in ("create", "edit") and response["status"] in ("failed", "rejected", "cancelled"):
            require(retained_keys(before) == retained_keys(after), "Failed candidate changed accepted source or image bytes")
        budget = response.get("execution_budget")
        if success and budget and key not in {(x["project_id"], x["request_id"]) for x in report["request_retries"]}:
            effective = budget.get("effective")
            if effective:
                for field in ("max_operations", "max_elapsed_ms"):
                    require(effective[field] <= row["host_policy"][field] and
                            effective[field] <= request.get("budgets", {}).get(field, effective[field]),
                            "Fresh successful request exceeded current host/caller authority")
        if not success:
            continue
        if operation == "inspect" and (request["selector"].get("kind") == "texture_asset" or request["selector"].get("element_id", [None])[0] == "assets"):
            observation = inspect_asset(request, response, sources[(project, request["program_revision"])])
            report["asset_inspections"].append({"project_id": project, "request_id": request_id, **observation})
        elif operation == "surface.mesh_page":
            revision = request["program_revision"]
            require(revision in frozen_cases, "Unprescribed mesh-page source identity")
            report["surface_pages"].append(inspect_surface(request, response, sources[(project, revision)], frozen_cases[revision]))
        elif operation == "artifact":
            result = response["result"]
            artifact = artifacts[(project, request["artifact_id"])]
            raw = bytes(artifact["data"]); offset = request.get("offset", 0); count = request["max_bytes"]
            require(base64.b64decode(result["data_base64"], validate=True) == raw[offset:offset + count], "Actual artifact slice differs from durable GLB bytes")
            require(result["sha256"] == digest(raw) and result["program_revision"] == artifact["source_revision"], "Actual artifact slice digest/source binding differs")
            report["artifact_slices"] += 1
    required_operations = {"discover", "create", "edit", "validate", "inspect", "surface.mesh_page", "evaluate", "export", "artifact", "status", "cancel", "reset"}
    require(set(operation_counts) == required_operations == set(summary["operation_inventory"]), "Raw evidence omits a documented operation")
    for project, revision in projects.items():
        require(project in previous and previous[project]["accepted_program_revision"] == revision, "Final SQLite accepted revision differs from raw history")
    for key, row in requests.items():
        response = loads(row["response"])
        require(response["status"] == row["state"] and row["state"] not in ("queued", "running"), "Raw store retains unterminated request")
        if key in seen and seen[key]["status"] not in ("queued", "running"):
            require(seen[key] == response, "SQLite terminal response differs from observed raw reply")
        else:
            observed = [r["response"]["result"]["target"] for r in transcript
                if (r.get("response") or {}).get("status") == "succeeded" and
                r["request"]["operation"] in ("status", "cancel") and
                (r["request"]["project_id"], r["request"]["target_request_id"]) == key]
            require(any(target == response for target in observed), "Unreturned request terminal state lacks an actual status reconciliation")
    for (project, artifact_id), artifact in artifacts.items():
        raw, provenance = bytes(artifact["data"]), loads(artifact["report"])
        require(digest(raw) == artifact["sha256"] and artifact_id == "artifact:" + sha(raw), "Durable GLB identity differs from actual bytes")
        require(GLB(raw, target=TARGET).document["extras"]["ontokin"]["program"]["revision"] == artifact["source_revision"], "Durable artifact source/asset revision differs")
        producer = requests[(project, provenance["producer_request_id"])]
        require(producer["operation"] == "export" and producer["state"] == "succeeded", "Artifact has no successful actual export request")
        matches = [a for a in summary["agent_artifacts"] if a["project_id"] == project and a["artifact_id"] == artifact_id]
        require(matches and all(ordinary_path(results, a["glb"]).read_bytes() == raw for a in matches), "Retrieved supplied GLB differs from durable actual bytes")
    report["workflows"] = audit_workflows(results, fixtures, summary, workflow_rows, sources, requests, artifacts, runs, report)
    report.update(status="passed", raw_exchanges=len(transcript), durable_request_identities=len(requests),
        durable_source_snapshots=len(sources), durable_artifacts=len(artifacts), durable_runs=len(runs),
        operation_counts=dict(sorted(operation_counts.items())), workflow_count=10,
        finished_utc=datetime.now(timezone.utc).isoformat())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/keyed-merge")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must name a new report")
    try:
        report = audit(args.results.resolve(), load_fixtures(args.fixtures))
    except Exception as error:
        report = {"schema_version": "ontokin.c084-independent-agent-audit/0.1", "status": "failed",
                  "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc(),
                  "release_acceptance": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "raw_exchanges", "durable_request_identities", "durable_artifacts", "reason") if key in report}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
