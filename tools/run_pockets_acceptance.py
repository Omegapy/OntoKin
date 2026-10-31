#!/usr/bin/env python3
"""Run the frozen C079 corpus and the actual twelve-operation Agent/0.12 workflow.

Write evidence outside the checkout. Independent readers check supplied GLB
bytes against the published inputs; runtime results never define expectations.
This finite development check does not assert complete release acceptance.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.budget_runtime import execute_pockets_export, execute_framed_loft_export, execute_extrusion_export
from ontokin.execution_budget import HostPolicy
from ontokin.pockets_agent import PocketsAgentService
from ontokin.scene import ExportOptions
from tools.check_local import git_metadata, inventory
from tools.pockets_oracles import Decoded, LegacyDecoded, check_glb

FIXTURES = ROOT / "examples/polygon-pockets"
PROFILE = "polygon-pockets-0.1"
PROTOCOL = "ontokin.agent/0.12"
TARGET = "ontokin.glb/0.12"
PROJECT = "c079"
DEFAULT_LIMITS = {"max_operations": 100000, "max_elapsed_ms": 30000}
MAXIMUM_LIMITS = {"max_operations": 2000000, "max_elapsed_ms": 80000}
OPTIONS = {"fps": 4, "end": "1", "helpers": False}
FREEZE_SHA256 = "3759a77630119f2203863dd4c5c4b51872008964e93cbacc29ffeed31af9c4d1"
FREEZE_COMMIT = "0177d68abbfa1043b99c2ec633d7336cceb020ae"
ADOPTION_SHA256 = "f94abe4603d324c388689ba43fbffa7a5f89eefa30a84884b024fba6db860d49"
OPERATIONS = {
    "discover", "create", "edit", "validate", "inspect", "evaluate", "reset",
    "status", "cancel", "export", "artifact", "surface.mesh_page",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def source_bundle(name, library):
    modules = ()
    if name in {"assembly.ok", "assembly-repaired.ok", "assembly-invalid.ok", "generated.ok"}:
        modules = (SourceUnit(library["source_id"], library["filename"],
                              (FIXTURES / library["filename"]).read_bytes(),
                              library["package"], library["version"]),)
    return ProgramBundle(SourceUnit("entry", Path(name).name, (FIXTURES / name).read_bytes()), modules)


def exact_patch(source, old, new):
    encoded = old.encode("utf-8")
    if source.entry.raw.count(encoded) != 1:
        raise AssertionError("The frozen repair must identify exactly one byte occurrence")
    start = source.entry.raw.index(encoded)
    return {"source_id": "entry", "source_revision": source.entry.revision,
            "element_id": ["sources", "entry"], "start_byte": start,
            "end_byte": start + len(encoded), "expected_text": old, "replacement": new}


def triangle_content(decoded, path="shape"):
    return [(region, positions, normals, material["pbrMetallicRoughness"])
            for region, positions, normals, material in decoded.triangles(path)]


def legacy_geometry(geometry):
    """Keep frozen zero-pocket expectations for an actual older .8 export."""
    if geometry['pockets']:
        raise AssertionError('Only the empty-pockets identity is a legacy comparison')
    return copy.deepcopy(geometry)


def schema_validators(output):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource

    directory = ROOT / "docs/language-design"
    paths = sorted((directory / "agent-v0.12").glob("*.schema.json"))
    paths += [directory / name for name in (
        "construction-v0.1/bundle.schema.json", "agent-v0.2/diagnostic.schema.json",
        "force-v0.1/forces.schema.json", "impulse-v0.1/impulses.schema.json",
        "planar-reach-v0.1/schema-drafts/reach-projection.schema.json",
        "planar-reach-v0.1/schema-drafts/reach-diagnostic.schema.json",
        "planar-reach-v0.1/schema-drafts/common.schema.json")]
    schemas = [json.loads(path.read_bytes()) for path in paths]
    registry = Registry().with_resources((item["$id"], Resource.from_contents(item)) for item in schemas)
    for item in schemas:
        Draft202012Validator.check_schema(item)
    save(output / "schema-inventory.json", [
        {"path": path.relative_to(ROOT).as_posix(), "id": item["$id"],
         "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}
        for path, item in zip(paths, schemas)])
    return {path.name: Draft202012Validator(item, registry=registry)
            for path, item in zip(paths, schemas)}


class Acceptance:
    def __init__(self, output):
        self.output = output
        self.serial = 0
        self.transcript = []
        self.service = None
        self.temporary = None
        self.before = None
        self.summary = {
            "schema_version": "ontokin.pockets-acceptance/0.1", "status": "running",
            "started_utc": datetime.now(timezone.utc).isoformat(), "git": git_metadata(ROOT),
            "python": sys.version, "platform": platform.platform(),
            "command": [sys.executable, *sys.argv], "profile": PROFILE,
            "agent_contract": PROTOCOL, "target_contract": TARGET,
            "frozen_input_commit": FREEZE_COMMIT, "cases": [], "assertions": [],
            "artifacts": [], "legacy_artifacts": [], "legacy_equivalence": [],
            "schema_validated_exchanges": 0, "release_acceptance": False,
            "not_executed_here": ["Khronos validator", "Three.js/Chromium playback",
                                  "capture review", "complete inherited checks",
                                  "other Python interpreters", "Unreal import or live physics"],
        }

    def check(self, value, label):
        self.summary["assertions"].append({"label": label, "passed": bool(value)})
        if not value:
            raise AssertionError(label)

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": PROJECT,
                "request_id": f"c079-{self.serial}", "operation": operation, **fields}

    def call(self, payload, *, wait=True):
        self.validators["request.schema.json"].validate(payload)
        response = self.service.handle(payload, wait=wait)
        row = {"sequence": len(self.transcript) + 1, "request": copy.deepcopy(payload),
               "response": copy.deepcopy(response)}
        self.transcript.append(row)
        save(self.output / f"exchange-{len(self.transcript):03}.json", row)
        self.validators["response.schema.json"].validate(response)
        self.summary["schema_validated_exchanges"] += 1
        return response

    def success(self, payload):
        response = self.call(payload)
        self.check(response["status"] == "succeeded", payload["operation"] + " succeeded")
        return response

    def retained(self):
        with self.service._store.connection() as db:
            return {
                "accepted": self.service.accepted_revision(PROJECT),
                "runs": [tuple(row) for row in db.execute(
                    "SELECT id,source_revision,descriptor,version FROM runs WHERE project_id=? ORDER BY id", (PROJECT,))],
                "artifacts": [tuple(row) for row in db.execute(
                    "SELECT id,data,sha256 FROM artifacts WHERE project_id=? ORDER BY id", (PROJECT,))],
            }

    def state_receipt(self, name, state):
        save(self.output / name, {
            "accepted_program_revision": state["accepted"],
            "runs": [{"id": row[0], "program_revision": row[1],
                      "descriptor": json.loads(row[2]), "version": row[3]} for row in state["runs"]],
            "artifacts": [{"id": row[0], "bytes": len(row[1]), "sha256": sha(row[1]),
                           "stored_sha256": row[2]} for row in state["artifacts"]],
        })

    def artifact(self, name, data, source, nodes, *, legacy=False):
        (self.output / (name + ".glb")).write_bytes(data)
        decoder = LegacyDecoded if legacy else Decoded
        decoded = decoder(data)
        self.check(set(decoded.objects()) == set(nodes), name + " exact carrier inventory")
        verified = check_glb(data, nodes, source.program_revision, legacy=legacy,
                             sample_times=tuple(self.expected["sample_times_seconds"]))
        save(self.output / (name + ".oracle.json"), verified)
        self.check(verified["status"] == "passed", name + " independent geometry and playback check")
        self.check(decoded.document["extras"]["ontokin"]["program"]["revision"] == source.program_revision,
                   name + " source revision in supplied GLB")
        expected_schema = "ontokin.extrusion-destination-expected/0.1" if legacy else "ontokin.pockets-destination-expected/0.1"
        save(self.output / (name + ".expected.json"), {
            "schema_version": expected_schema, "case_id": name,
            "program_revision": source.program_revision,
            "duration_seconds": self.expected["duration_seconds"], "nodes": nodes})
        destination = "ontokin.glb/0.8" if legacy else TARGET
        self.summary["legacy_artifacts" if legacy else "artifacts"].append({
            "name": name, "path": name + ".glb", "bytes": len(data), "sha256": sha(data),
            "program_revision": source.program_revision, "target_contract": destination,
            "source_revision": source.entry.revision, "geometry": verified["geometry"],
            "native_poses": len(verified["observations"]),
        })
        return decoded

    def verify_freeze(self):
        raw = (FIXTURES / "acceptance-freeze.json").read_bytes()
        self.check(sha(raw) == FREEZE_SHA256, "Exact published C079 input freeze")
        frozen = json.loads(raw)
        self.check(frozen["frozen_before_implementation"] is True, "Input freeze precedes implementation")
        self.check(frozen["decision_sha256"] == ADOPTION_SHA256 and
                   sha((ROOT / frozen["decision_file"]).read_bytes()) == ADOPTION_SHA256,
                   "Exact published polygon-pockets adoption")
        for name, wanted in frozen["files"].items():
            data = (FIXTURES / name).read_bytes()
            self.check({"bytes": len(data), "sha256": sha(data)} == wanted, "Frozen input " + name)
        self.expected = json.loads((FIXTURES / "expected.json").read_bytes())
        outcomes = dict(Counter(case["expected_outcome"] for case in self.expected["cases"]))
        self.check(len(self.expected["cases"]) == frozen["case_count"] == 82 and
                   outcomes == frozen["outcome_counts"] == {
                       "valid": 27, "invalid": 50, "source_valid_delivery_rejected": 5},
                   "All 82 independently frozen outcomes retained")
        self.check(self.expected["maximum_host_policy"] == MAXIMUM_LIMITS, "Frozen maximum host authority")
        self.library = self.expected["assembly"]["library"]
        self.check(sha((FIXTURES / self.library["filename"]).read_bytes()) == self.library["sha256"],
                   "Exact independently pinned reusable library")
        self.summary["input_freeze"] = {"sha256": sha(raw), "case_count": 82,
                                         "outcome_counts": outcomes, "source_count": frozen["source_count"]}
        save(self.output / "input-freeze.json", frozen)

    def no_resource_substitution(self, report, label):
        diagnostics = report.get("diagnostics", [])
        self.check(report.get("outcome") != "resource_limit" and
                   not (report.get("execution_budget") or {}).get("budget_reason") and
                   (report.get("error") or {}).get("code") != "OKL-E-RESOURCE" and
                   all(d.get("code") != "OKL-E-RESOURCE" and d.get("category") != "resource_limit"
                       for d in diagnostics), label + " does not substitute a resource refusal")

    def run_sources(self):
        self.exports = {}
        by_id = {case["id"]: case for case in self.expected["cases"]}
        for case in self.expected["cases"]:
            source = source_bundle(case["source"], self.library)
            execute = execute_framed_loft_export if case["id"] == "earlier-version-rejection" else execute_pockets_export
            result = execute(source, policy=HostPolicy(**MAXIMUM_LIMITS), options=ExportOptions(**OPTIONS))
            save(self.output / (case["id"] + ".receipt.json"), result.report)
            budget = result.report.get("execution_budget") or {}
            record = {"id": case["id"], "source": case["source"],
                      "program_revision": source.program_revision,
                      "expected": case["expected_outcome"],
                      "actual": "delivered" if result.data is not None else "rejected",
                      "achieved_level": result.report.get("achieved_level"),
                      "operations": budget.get("consumed_operations"),
                      "elapsed_ms": budget.get("elapsed_ms"),
                      "diagnostic_codes": [d["code"] for d in result.report.get("diagnostics", [])]}
            self.summary["cases"].append(record)
            self.check(budget.get("source_request") == case.get("requested_execution_limits", DEFAULT_LIMITS),
                       case["id"] + " exact source request; host ceilings do not raise defaults")
            self.no_resource_substitution(result.report, case["id"])
            if case["expected_outcome"] == "valid":
                self.check(result.data is not None, case["id"] + " delivered")
                self.exports[case["id"]] = result.data
                self.artifact(case["id"], result.data, source, {"shape": {
                    "geometry": case["geometry"], "origin": [0, 0, 0],
                    "velocity": self.expected["motion_m_per_second"]}})
            else:
                self.check(result.data is None and bool(record["diagnostic_codes"]),
                           case["id"] + " rejected with diagnostics and no artifact")
                if case.get("diagnostic_code"):
                    self.check(case["diagnostic_code"] in record["diagnostic_codes"],
                               case["id"] + " exact frozen diagnostic")
                if case["expected_outcome"] == "source_valid_delivery_rejected":
                    self.check(result.report.get("achieved_level") == "evaluated",
                               case["id"] + " source constructed and evaluated before delivery refusal")
                    precision = any(
                        d.get("code") == "OKL-E-POCKETS-NUMERIC" or
                        d.get("details", {}).get("export_code") == "OKE-E-GEOMETRY-PRECISION" or
                        (d.get("details", {}).get("export_code") == "OKE-E-GLB-STRUCTURE" and
                         any(word in d.get("message", "").lower() for word in ("triangle", "normal", "winding")))
                        for d in result.report.get("diagnostics", []))
                    self.check(precision, case["id"] + " actual delivered-geometry precision refusal")
            record["status"] = "passed"

        for left, right in self.expected["ordering_equivalence"] + self.expected.get("geometry_equivalence", []):
            self.check(triangle_content(Decoded(self.exports[left])) == triangle_content(Decoded(self.exports[right])),
                       left + " / " + right + " decoded triangles, normals and materials are identical")

        for reference in self.expected["legacy_equivalence"]:
            case_id = reference["case"]
            source = source_bundle(reference["source"], self.library)
            result = execute_extrusion_export(source, options=ExportOptions(**OPTIONS))
            name = Path(reference["source"]).stem
            save(self.output / (name + ".receipt.json"), result.report)
            self.check(result.data is not None, name + " actual legacy .8 export")
            nodes = {"shape": {"geometry": legacy_geometry(by_id[case_id]["geometry"]),
                                "origin": [0, 0, 0], "velocity": self.expected["motion_m_per_second"]}}
            decoded = self.artifact(name, result.data, source, nodes, legacy=True)
            self.check(triangle_content(decoded) == triangle_content(Decoded(self.exports[case_id])),
                       case_id + " empty pockets equal actual .8 triangles, normals and materials")
            self.summary["legacy_equivalence"].append({
                "case": case_id, "reference": name, "status": "passed",
                "reference_program_revision": source.program_revision,
                "pockets_sha256": sha(self.exports[case_id]), "legacy_sha256": sha(result.data)})

        generated_spec = self.expected["generated"]
        generated = source_bundle(generated_spec["entry"], self.library)
        result = execute_pockets_export(generated, options=ExportOptions(**OPTIONS))
        save(self.output / "generated.receipt.json", result.report)
        self.check(result.data is not None, "Generated pinned reusable occurrences export")
        origin, path = generated_spec["root_placement_m"], generated_spec["object_path"]
        nodes = {path: {"geometry": None, "origin": origin, "velocity": self.expected["motion_m_per_second"]}}
        for item in generated_spec["parts"]:
            part_path = path + "." + generated_spec["parts_member"] + "[" + json.dumps(item["key"]) + "]"
            nodes[part_path] = {"geometry": item["geometry"],
                                "origin": [a+b for a,b in zip(origin, item["offset_m"])],
                                "velocity": self.expected["motion_m_per_second"]}
        self.artifact("generated", result.data, generated, nodes)

    def retrieve(self, exported, source):
        result = exported["result"]
        artifact_id, total = result["artifact_id"], result["total_bytes"]
        chunks, offset = [], 0
        self.check(type(total) is int and 0 < total <= 64 * 1024 * 1024, "Bounded nonempty artifact size")
        for _ in range((total + 1023) // 1024):
            response = self.success(self.request("artifact", artifact_id=artifact_id, offset=offset, max_bytes=1024))
            part = response["result"]
            chunk = base64.b64decode(part["data_base64"], validate=True)
            self.check(part["offset"] == offset and part["program_revision"] == source.program_revision and
                       part["artifact_id"] == artifact_id and part["sha256"] == result["sha256"] and
                       part["total_bytes"] == total and len(chunk) == min(1024, total - offset),
                       "Artifact chunk offset, length, identity and source binding")
            chunks.append(chunk)
            offset += len(chunk)
            self.check(part["next_offset"] == (offset if offset < total else None) and
                       response["truncated"] == (offset < total), "Artifact pagination makes exact bounded progress")
            if offset == total:
                break
        data = b"".join(chunks)
        self.check(len(data) == total and "sha256:" + sha(data) == result["sha256"] and
                   "artifact:" + sha(data) == artifact_id, "Retrieved complete artifact exact bytes and identities")
        with self.service._store.connection() as db:
            stored = db.execute("SELECT data,sha256,source_revision,report FROM artifacts WHERE project_id=? AND id=?",
                                (PROJECT, artifact_id)).fetchone()
        self.check(stored is not None and bytes(stored["data"]) == data and
                   stored["sha256"] == result["sha256"] and stored["source_revision"] == source.program_revision and
                   json.loads(stored["report"])["producer_request_id"] == exported["request_id"],
                   "Retrieved supplied bytes equal the durable SQLite artifact and producer receipt")
        self.summary.setdefault("artifact_retrievals", []).append({
            "artifact_id": artifact_id, "program_revision": source.program_revision,
            "chunks": len(chunks), "bytes": len(data), "sha256": sha(data), "sqlite_bytes_equal": True})
        return data

    def run_agent(self):
        self.temporary = Path(tempfile.mkdtemp(prefix="live-store-", dir=self.output))
        self.service = PocketsAgentService(self.temporary / "agent")
        spec = self.expected["assembly"]
        source = source_bundle(spec["entry"], self.library)
        repaired_source = ProgramBundle(SourceUnit("entry", source.entry.filename,
            (FIXTURES / spec["repaired_entry"]).read_bytes()), source.modules)
        first = [spec["module_id"], spec["scene_id"], "first"]
        sibling = [spec["module_id"], spec["scene_id"], "sibling"]
        discovery = self.success(self.request("discover", profile=PROFILE, limit=1000))
        self.check({"PolygonPocket", "polygon_pocket", "extrude_pockets", "loft_framed_rings"}
                   <= {item["name"] for item in discovery["result"]["items"]},
                   "Actual discovery contains new and inherited constructors")
        self.check(self.service.database_path.name == "pockets-program-agent.sqlite3",
                   "Separate Agent/0.12 durable database")
        self.success(self.request("create", bundle=source.to_payload(), expected_program_revision=None,
                                  requested_level="constructed"))
        validation = self.success(self.request("validate", program_revision=source.program_revision,
                                               requested_level="constructed"))
        self.check(validation["execution_budget"]["effective"] == DEFAULT_LIMITS,
                   "Ordinary composed program retains default execution limits")
        self.success(self.request("inspect", program_revision=source.program_revision,
                                  selector={"kind": "source"}, fields=["identity", "source"], limit=100))
        inspection = self.success(self.request("inspect", program_revision=source.program_revision,
                                  selector={"path": "first"}, fields=["identity", "geometry", "support"], limit=1))
        summary = inspection["result"]["items"][0]["geometry"]["surface"]
        self.check(summary["schema_version"] == "ontokin.polygon-pockets-summary/0.1" and
                   summary["profile"] == PROFILE and summary["family"] == "polygon_pockets" and
                   summary["physical_participation"] == "none" and
                   summary["motion_authority"] == "carrier_evaluated_world_pose",
                   "Actual .12 geometry inspection exposes visual blind-pocket semantics")
        vertices = lambda values: [{"key": v["key"], "order": v["order"],
                                   "point_m": v["point_m"], "region": v["side_region"]}
                                  for v in sorted(values, key=lambda v: v["order"])]
        self.check(vertices(summary["outer_vertices"]) == spec["first"]["outer_vertices"],
                   "Inspected outer boundary retains independently frozen source identities")
        self.check(len(summary["pockets"]) == len(spec["first"]["pockets"]),
                   "Inspected blind pocket count matches the independent input")
        for actual, wanted in zip(summary["pockets"], spec["first"]["pockets"]):
            self.check(vertices(actual["vertices"]) == wanted["vertices"] and all(actual[key] == wanted[key] for key in (
                "key", "order", "depth_m", "floor_region", "floor_m", "remaining_base_m",
                "exact_remaining_base_m", "effective_depth_m")),
                "Inspected authored depth, exact remaining base and single-rounded floor match independently")
        for key in ("height_m", "bottom_region", "top_region", "pocket_count", "authored_vertex_count",
                    "logical_vertex_count", "bottom_triangle_count", "top_triangle_count", "floor_triangle_count",
                    "wall_triangle_count", "triangle_count", "vertex_count"):
            self.check(summary[key] == spec["first"][key], "Inspection exact frozen field " + key)
        self.check({region["key"]: region["triangle_count"] for region in summary["regions"]} ==
                   spec["first"]["region_triangle_counts"], "Inspection frozen regional triangle counts")
        old_sibling = self.success(self.request("surface.mesh_page", program_revision=source.program_revision,
                                               element_id=sibling, count=256))["result"]
        page = self.success(self.request("surface.mesh_page", program_revision=source.program_revision,
                                         element_id=first, count=3))
        first_page, cursor = page["result"], page["next_cursor"]
        self.check(cursor is not None and first_page["returned_triangles"] == 3, "Bounded pocket mesh page yields cursor")
        continued = self.success(self.request("surface.mesh_page", program_revision=source.program_revision,
                                             element_id=first, count=3, cursor=cursor))
        self.check(continued["result"]["source_triangle_ordinals"] == [3, 4, 5],
                   "Same-query mesh cursor continues the exact triangle order")
        changed_filter = self.call(self.request("surface.mesh_page", program_revision=source.program_revision,
                                               element_id=first, count=3, cursor=cursor, region="floor"))
        self.check(changed_filter["status"] in ("failed", "rejected"), "Mesh cursor refuses a changed region filter")

        self.success(self.request("evaluate", program_revision=source.program_revision, run_id=None, until_seconds="0.5"))
        original_export = self.success(self.request("export", program_revision=source.program_revision,
                                                    destination=TARGET, options=OPTIONS))
        original_data = self.retrieve(original_export, source)
        def nodes(first_geometry):
            return {"first": {"geometry": first_geometry, "origin": spec["first_placement_m"],
                              "velocity": self.expected["motion_m_per_second"]},
                    "sibling": {"geometry": spec["sibling"], "origin": spec["sibling_placement_m"],
                                "velocity": spec["sibling_motion_m_per_second"]}}
        self.artifact("agent-original", original_data, source, nodes(spec["first"]))
        before = self.retained()
        self.state_receipt("before-invalid-edit.json", before)
        bad, repair = spec["invalid_edit"], spec["repair"]
        self.check(source.entry.raw.count(bad["old"].encode()) == 1 and
                   source.entry.raw.replace(bad["old"].encode(), bad["new"].encode(), 1) ==
                   (FIXTURES / spec["invalid_entry"]).read_bytes(), "Invalid edit is the exact frozen one-occurrence candidate")
        rejected = self.call(self.request("edit", expected_program_revision=source.program_revision,
            requested_level="delivered", destination=TARGET, options=OPTIONS,
            patches=[exact_patch(source, bad["old"], bad["new"])]))
        self.check(rejected["status"] in ("failed", "rejected") and
                   bad["diagnostic_code"] in [item["code"] for item in rejected.get("diagnostics", [])],
                   "Invalid penetrating-depth edit reaches its frozen depth diagnostic")
        self.no_resource_substitution(rejected, "Invalid pocket-depth edit")
        after = self.retained()
        self.state_receipt("after-invalid-edit.json", after)
        self.check(before == after and "artifact_id" not in (rejected.get("result") or {}),
                   "Invalid edit preserves accepted source, valid runs and exact stored artifacts")
        self.check(repair["old"] == "pocket_depth = 0.5[m];" and repair["new"] == "pocket_depth = 0.75[m];" and
                   source.entry.raw.replace(repair["old"].encode(), repair["new"].encode(), 1) == repaired_source.entry.raw,
                   "Repair changes only the frozen first-instance pocket depth from 0.5 to 0.75 meters")
        repaired = self.success(self.request("edit", expected_program_revision=source.program_revision,
            requested_level="constructed", patches=[exact_patch(source, repair["old"], repair["new"])]))
        self.check(repaired["accepted_program_revision"] == repaired_source.program_revision,
                   "Accepted repair is the exact frozen bundle with the original entry filename")
        stored = self.service.read_program(PROJECT, repaired_source.program_revision)
        self.check(stored.entry.raw == repaired_source.entry.raw and stored.modules == source.modules,
                   "Accepted source bytes and unchanged pinned module closure match the frozen repair")
        new_sibling = self.success(self.request("surface.mesh_page", program_revision=repaired_source.program_revision,
                                               element_id=sibling, count=256))["result"]
        new_first = self.success(self.request("surface.mesh_page", program_revision=repaired_source.program_revision,
                                             element_id=first, count=3))["result"]
        geometry_fields = ("positions_m", "normals", "triangles", "region_keys", "source_triangle_ordinals")
        self.check(all(old_sibling[field] == new_sibling[field] for field in geometry_fields),
                   "Sibling triangles, source ordinals, materials and normals remain exactly unchanged")
        self.check(new_first["element_id"] == first_page["element_id"] and
                   new_first["geometry_sha256"] != first_page["geometry_sha256"],
                   "First occurrence retains its identity and changes its geometry")
        stale = self.call(self.request("surface.mesh_page", program_revision=repaired_source.program_revision,
                                      element_id=first, count=3, cursor=cursor))
        self.check(stale["status"] in ("failed", "rejected"), "Prior-revision mesh cursor is rejected after repair")

        evaluation = self.request("evaluate", program_revision=repaired_source.program_revision, run_id=None, until_seconds="1")
        evaluated = self.success(evaluation)
        before_retry = self.retained()
        self.check(self.call(evaluation) == evaluated, "Identical evaluation retry returns the exact durable receipt")
        changed = copy.deepcopy(evaluation)
        changed["until_seconds"] = "0.5"
        mismatch = self.call(changed)
        self.check(mismatch["status"] == "rejected" and self.retained() == before_retry,
                   "Changed retry payload is refused without modifying durable product state")
        export_request = self.request("export", program_revision=repaired_source.program_revision,
                                      destination=TARGET, options=OPTIONS)
        exported = self.success(export_request)
        data = self.retrieve(exported, repaired_source)
        self.artifact("agent-repaired", data, repaired_source, nodes(spec["repaired_first"]))
        self.check(spec["repaired_first"]["volume_m3"] == 22.5 and spec["sibling"]["volume_m3"] == 23,
                   "Independent repaired/sibling controls remain 22.5 and 23 cubic meters")
        self.summary["agent_export_operations"] = exported["execution_budget"]["consumed_operations"]

        before_reopen = self.retained()
        self.state_receipt("before-reopen.json", before_reopen)
        store_directory = self.service.database_path.parent
        self.service.close()
        self.service = PocketsAgentService(store_directory)
        after_reopen = self.retained()
        self.state_receipt("after-reopen.json", after_reopen)
        self.check(after_reopen == before_reopen and
                   self.call(evaluation) == evaluated,
                   "Reopened service retains exact source, runs, artifacts and original evaluation receipt")
        self.summary["service_reopen"] = {"same_store": True, "retained_state_equal": True,
                                           "evaluation_receipt_equal": True}
        before_policy = self.retained()
        self.service.host_policy = HostPolicy(50000, 30000)
        for operation, fields in (
            ("artifact", {"artifact_id": exported["result"]["artifact_id"], "max_bytes": 1024}),
            ("evaluate", {"program_revision": repaired_source.program_revision,
                          "run_id": evaluated["run_id"], "until_seconds": "1"})):
            denied = self.call(self.request(operation, **fields))
            self.check(denied["status"] in ("failed", "rejected") and
                       denied["execution_budget"]["budget_reason"] == "host_ceiling_exceeded",
                       "New " + operation + " request reauthorizes retained data against current host policy")
        self.check(self.retained() == before_policy, "Current-policy refusals preserve accepted source, runs and artifacts")
        self.check(self.call(export_request) == exported, "Historical identical export retry retains its original receipt under lower policy")
        reduced = self.success(self.request("artifact", artifact_id=exported["result"]["artifact_id"],
            max_bytes=64, budgets={"max_operations": 50000, "max_elapsed_ms": 30000}))
        self.check(base64.b64decode(reduced["result"]["data_base64"], validate=True) == data[:64],
                   "Explicit caller reduction permits the same retained bytes within current host authority")
        self.service.host_policy = HostPolicy()
        self.success(self.request("reset", program_revision=repaired_source.program_revision))
        pending = self.request("validate", program_revision=repaired_source.program_revision, requested_level="constructed")
        queued = self.call(pending, wait=False)
        self.success(self.request("cancel", target_request_id=pending["request_id"]))
        status = self.success(self.request("status", target_request_id=pending["request_id"]))
        self.check(queued["status"] == "queued" and status["result"]["target_status"] == "cancelled",
                   "Queued cancellation retains an inspectable terminal result")
        self.check(self.service.accepted_revision(PROJECT) == repaired_source.program_revision,
                   "Reset, cancellation and policy changes preserve the accepted repaired program")
        self.audit_store()

    def audit_store(self):
        operations = sorted({row["request"]["operation"] for row in self.transcript})
        self.summary["operation_inventory"] = operations
        self.check(operations == sorted(OPERATIONS), "All twelve documented operations actually executed")
        with self.service._store.connection() as db:
            requests = [dict(row) for row in db.execute(
                "SELECT id,operation,state,digest,payload,response,cancel_requested FROM requests WHERE project_id=? ORDER BY sequence",
                (PROJECT,))]
            schema = db.execute("SELECT value FROM metadata WHERE name='schema_version'").fetchone()[0]
            artifacts = [{"id": row[0], "program_revision": row[1], "bytes": len(row[2]),
                          "stored_sha256": row[3], "sha256": sha(row[2])}
                         for row in db.execute("SELECT id,source_revision,data,sha256 FROM artifacts WHERE project_id=? ORDER BY id", (PROJECT,))]
            integrity = [row[0] for row in db.execute("PRAGMA integrity_check")]
        self.summary["durable_requests"] = len(requests)
        self.check({row["id"] for row in requests} == {row["request"]["request_id"] for row in self.transcript},
                   "Every unique actual request identity is retained exactly once")
        self.check(schema == "ontokin.pockets-program-agent-store/0.1" and integrity == ["ok"],
                   "Correct separate durable store schema and SQLite integrity")
        for row in requests:
            row["payload"] = json.loads(row["payload"])
            row["response"] = json.loads(row["response"])
            self.validators["request.schema.json"].validate(row["payload"])
            self.validators["response.schema.json"].validate(row["response"])
            matches = [item for item in self.transcript if item["request"]["request_id"] == row["id"]]
            self.check(row["payload"] == matches[0]["request"], "Durable original request payload " + row["id"])
            if row["state"] != "cancelled":
                self.check(any(row["response"] == item["response"] for item in matches),
                           "Durable terminal receipt equals an actual response " + row["id"])
        save(self.output / "store-inventory.json", {"schema_version": schema, "integrity_check": integrity,
                                                    "requests": requests, "artifacts": artifacts})

    def finish(self):
        errors = []
        database_backed_up = False
        if self.before is not None:
            try:
                after = inventory(ROOT)
                save(self.output / "source-after.json", after)
                self.check(self.before == after, "Complete source inventory unchanged during acceptance")
            except BaseException as error:
                errors.append({"stage": "source_inventory", "type": type(error).__name__, "message": str(error)})
        if self.service is not None:
            try:
                self.service.close()
                with sqlite3.connect(self.service.database_path) as src, sqlite3.connect(
                        self.output / self.service.database_path.name) as dst:
                    src.backup(dst)
                database_backed_up = True
            except BaseException as error:
                errors.append({"stage": "database_backup", "type": type(error).__name__, "message": str(error)})
        if self.temporary is not None:
            if database_backed_up:
                try:
                    shutil.rmtree(self.temporary)
                except OSError as error:
                    errors.append({"stage": "temporary_cleanup", "type": type(error).__name__, "message": str(error)})
            else:
                self.summary["retained_live_store"] = str(self.temporary)
        if errors:
            self.summary["status"] = "failed"
            self.summary["finalization_failures"] = errors
        (self.output / "protocol.jsonl").write_text(
            "".join(json.dumps(row, allow_nan=False) + "\n" for row in self.transcript), encoding="utf-8")
        self.summary["exchanges"] = len(self.transcript)
        self.summary.setdefault("operation_inventory", sorted({row["request"]["operation"] for row in self.transcript}))
        self.summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(self.output / "summary.json", self.summary)

    def run(self):
        try:
            self.before = inventory(ROOT)
            save(self.output / "source-before.json", self.before)
            self.verify_freeze()
            self.validators = schema_validators(self.output)
            self.run_sources()
            self.run_agent()
            self.summary["status"] = "passed"
        except BaseException as error:
            self.summary["status"] = "failed"
            self.summary["failure"] = {"type": type(error).__name__, "message": str(error)}
            (self.output / "failure.traceback").write_text(traceback.format_exc(), encoding="utf-8")
        finally:
            self.finish()
        print(json.dumps({key: self.summary.get(key) for key in (
            "status", "exchanges", "durable_requests", "schema_validated_exchanges",
            "agent_export_operations", "failure", "finalization_failures")}))
        return 0 if self.summary["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Acceptance evidence must be written outside the source checkout")
    output.mkdir(parents=True, exist_ok=False)
    return Acceptance(output).run()


if __name__ == "__main__":
    raise SystemExit(main())
