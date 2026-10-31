#!/usr/bin/env python3
"""Audit raw C080 requests, replies, supplied slices and SQLite independently.

No OntoKin runtime module is imported. Successful edits are replayed as exact
UTF-8/attachment transactions, and every accepted identity is recomputed from
source/image bytes rather than taken from a receipt's claim.
"""
from __future__ import annotations

import argparse
import base64
from collections import defaultdict
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
from tools.texture_reference import (FREEZE_COMMIT, PROTOCOL, GLB, bundle_identity,
    canonical, digest, exact_uv, expected_occurrences, file_payload, load_fixtures,
    loads, ordinary_path, require, sha)
from tools.verify_textures import codes


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
    require(not request.get("module_changes"), "Finite C080 workflows must not silently add unprescribed module edits")
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


def audit(results, fixtures):
    summary = loads(ordinary_path(results, "summary.json").read_bytes())
    require(summary.get("input_corpus_version", 1) == fixtures["corpus_version"] and
            summary.get("correction_manifest_sha256") == fixtures.get("correction_manifest_sha256"),
            "Raw audit requires explicit matching original/corrected corpus selection")
    transcript = loads(ordinary_path(results, "agent/transcript.json").read_bytes())
    jsonl = [loads(line) for line in ordinary_path(results, "agent/transcript.jsonl").read_bytes().splitlines()]
    require(transcript == jsonl and transcript, "Raw transcript representations differ or are empty")
    require([row["sequence"] for row in transcript] == list(range(1, len(transcript) + 1)), "Raw exchanges lack exact order")
    for row in transcript:
        require(loads(ordinary_path(results, f"agent/exchange-{row['sequence']:04}.json").read_bytes()) == row,
                "Individual raw exchange differs from transcript")
    database = ordinary_path(results, summary["store"]["path"])
    require(sha(database.read_bytes()) == summary["store"]["sha256"] and database.stat().st_size == summary["store"]["bytes"], "Retained SQLite identity differs")
    connection = sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        require([r[0] for r in connection.execute("PRAGMA integrity_check")] == ["ok"], "Retained SQLite integrity failure")
        require(connection.execute("SELECT value FROM metadata WHERE name='schema_version'").fetchone()[0] ==
                "ontokin.texture-program-agent-store/0.1", "Wrong separate .13 store schema")
        sources = {(r["project_id"], r["revision"]): loads(bytes(r["raw"])) for r in connection.execute("SELECT * FROM sources")}
        requests = {(r["project_id"], r["id"]): dict(r) for r in connection.execute("SELECT * FROM requests ORDER BY sequence")}
        artifacts = {(r["project_id"], r["id"]): dict(r) for r in connection.execute("SELECT * FROM artifacts")}
        projects = {r["id"]: r["accepted_revision"] for r in connection.execute("SELECT * FROM projects")}
        runs = [dict(r) for r in connection.execute("SELECT * FROM runs")]
    finally:
        connection.close()
    report = {"schema_version": "ontokin.c080-independent-agent-audit/0.1", "status": "running",
        "frozen_input_commit": FREEZE_COMMIT, "actual_git": summary["git"], "release_acceptance": False,
        "input_corpus_version": fixtures["corpus_version"], "correction_manifest_sha256": fixtures.get("correction_manifest_sha256"),
        "correction_input_commit": summary.get("correction_input_commit"),
        "database_sha256": sha(database.read_bytes()), "source_snapshots": [], "accepted_edits": [],
        "asset_inspections": [], "surface_pages": [], "artifact_slices": 0,
        "request_retries": [], "durable_payload_tombstones": [], "failures": []}
    for (project, revision), payload in sources.items():
        actual, manifest = bundle_identity(payload)
        require(actual == revision, "Durable source/image revision does not match actual bytes")
        report["source_snapshots"].append({"project_id": project, "program_revision": revision,
            "payload_sha256": sha(canonical(payload)), "source_units": len(manifest["units"]), "assets": manifest["assets"]})
    observed_keys = {(r["request"]["project_id"], r["request"]["request_id"]) for r in transcript}
    require(observed_keys == set(requests), "Every usable raw request identity must have exactly one durable row")
    frozen_cases = {c["program_revision"]: c for c in fixtures["cases"].values()}
    previous, seen, operation_counts, workflow_rows = {}, {}, defaultdict(int), defaultdict(list)
    for row in transcript:
        request = row["request"]; project, request_id, operation = request["project_id"], request["request_id"], request["operation"]
        key, stored = (project, request_id), requests[(project, request_id)]
        require(request["schema_version"] == PROTOCOL, "Wrong actual request contract")
        require(not row.get("response_schema_errors"), "Actual response schema failed producer validation")
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
            require(row["workflow"] == "A14" and row.get("exception", {}).get("exception") == "PublicationInterruption", "Unexplained missing actual response")
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
    require(set(operation_counts) == set(fixtures["workflows"]["required_operations"]), "Raw evidence omits a documented operation")
    for project, revision in projects.items():
        require(project in previous and previous[project]["accepted_program_revision"] == revision, "Final SQLite accepted revision differs from raw history")
    for key, row in requests.items():
        response = loads(row["response"])
        require(response["status"] == row["state"] and row["state"] not in ("queued", "running"), "Raw store retains unterminated request")
        if key in seen and seen[key]["status"] not in ("queued", "running"):
            require(seen[key] == response, "SQLite terminal response differs from observed raw reply")
        else:
            observed = [r["response"]["result"]["target"] for r in transcript
                if r.get("response", {}).get("status") == "succeeded" and
                r["request"]["operation"] in ("status", "cancel") and
                (r["request"]["project_id"], r["request"]["target_request_id"]) == key]
            require(any(target == response for target in observed), "Unreturned request terminal state lacks an actual status reconciliation")
    for (project, artifact_id), artifact in artifacts.items():
        raw, provenance = bytes(artifact["data"]), loads(artifact["report"])
        require(digest(raw) == artifact["sha256"] and artifact_id == "artifact:" + sha(raw), "Durable GLB identity differs from actual bytes")
        require(GLB(raw).document["extras"]["ontokin"]["program"]["revision"] == artifact["source_revision"], "Durable artifact source/asset revision differs")
        producer = requests[(project, provenance["producer_request_id"])]
        require(producer["operation"] == "export" and producer["state"] == "succeeded", "Artifact has no successful actual export request")
        matches = [a for a in summary["agent_artifacts"] if a["project_id"] == project and a["artifact_id"] == artifact_id]
        require(matches and all(ordinary_path(results, a["glb"]).read_bytes() == raw for a in matches), "Retrieved supplied GLB differs from durable actual bytes")
    for spec in fixtures["workflows"]["sequences"]:
        require(workflow_rows[spec["id"]], "Frozen workflow omitted actual operations")
        row = next(r for r in summary["workflows"] if r["id"] == spec["id"])
        require(row["status"] == "observed_as_expected", "Actual frozen workflow failed")
    a09 = [r for r in workflow_rows["A09"] if r["request"]["operation"] != "create"]
    require(len(a09) == 3 and all("OKL-E-RESOURCE" in codes(r["response"]) and retained_keys(r["state_before"]) == retained_keys(r["state_after"]) for r in a09), "Current host reauthorization was not actually refused")
    cancelled = [r for r in workflow_rows["A11"] if r.get("response", {}).get("status") == "cancelled" and r["request"]["operation"] == "export"]
    require(len(cancelled) == 1 and cancelled[0]["state_before"] == cancelled[0]["state_after"], "Actual in-progress export cancellation changed durable product state")
    barrier = loads(ordinary_path(results, "agent/cancellation-barrier.json").read_bytes())
    require(barrier["actual_export_checkpoint_reached"] is True and not barrier["worker_errors"], "Cancellation did not reach actual metered export")
    publication = loads(ordinary_path(results, "agent/publication-interruption.json").read_bytes())
    require(publication["before"] == publication["after"] and len(publication["prepared_only"]) == 1, "Interrupted publication leaked durable effects")
    prepared = publication["prepared_only"][0]
    require(sha(ordinary_path(results, "agent/interrupted-prepared-only.glb").read_bytes()) == prepared["sha256"], "Publication interruption did not preserve its actual prepared-byte evidence")
    require(("c080-a14", prepared["artifact_id"]) not in artifacts and requests[("c080-a14", prepared["request_id"])]["state"] != "succeeded", "Interrupted artifact was published successfully")
    for spec in fixtures["workflows"]["request_envelope_boundaries"]:
        observed = next(r for r in summary["envelope_boundaries"] if r["name"] == spec["name"])
        raw = ordinary_path(results, observed["request_file"]).read_bytes()
        require(len(raw) == spec["serialized_utf8_bytes"] == observed["bytes"] and sha(raw) == observed["sha256"], "Exact serialized envelope boundary differs")
        request = loads(raw)
        original = file_payload(fixtures["root"], fixtures["cases"]["rgb-panel"]["file_manifest"])
        prefix = original["entry"]["source"] + "\n//"
        require(request["bundle"]["entry"]["source"].startswith(prefix), "Envelope probe changed underlying source")
        suffix = request["bundle"]["entry"]["source"][len(prefix):]
        require(suffix == "\0" * suffix.count("\0") + " " * suffix.count(" ") and len(request["bundle"]["entry"]["source"].encode()) < 2000000, "Envelope padding does not isolate byte gate")
        response = observed["response"]
        if "expected_code" in spec:
            require(spec["expected_code"] in codes(response) and response.get("request_id") is None, "Oversized envelope reached product work")
        else:
            require(response.get("request_id") == request["request_id"], "Exact maximum envelope did not reach actual admission")
    require(len(summary["asset_slice_probes"]) == 16 and all(r["status"] == "observed_as_expected" for r in summary["asset_slice_probes"]), "Slice boundary coverage incomplete")
    report.update(status="passed", raw_exchanges=len(transcript), durable_request_identities=len(requests),
        durable_source_snapshots=len(sources), durable_artifacts=len(artifacts), durable_runs=len(runs),
        operation_counts=dict(sorted(operation_counts.items())), workflow_count=18, slice_boundary_probes=16,
        envelope_boundaries=2, finished_utc=datetime.now(timezone.utc).isoformat())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "examples/textured-surfaces")
    parser.add_argument("--corrections", type=Path, help="Explicitly select the separately frozen input corpus version 2")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must name a new report")
    try:
        report = audit(args.results.resolve(), load_fixtures(args.fixtures, args.corrections))
    except Exception as error:
        report = {"schema_version": "ontokin.c080-independent-agent-audit/0.1", "status": "failed",
                  "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc(),
                  "release_acceptance": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "raw_exchanges", "durable_request_identities", "durable_artifacts", "reason") if key in report}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
