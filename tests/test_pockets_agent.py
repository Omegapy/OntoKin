"""Exercise pocket source edits, actual protocol lifecycle and delivered floors."""
from __future__ import annotations

import base64
import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ontokin.agent_protocol import ProtocolError
from ontokin.budget_runtime import execute_extrusion_export, execute_framed_loft_export, execute_pockets_export
from ontokin.bundle import load_bundle
from ontokin.execution_budget import HostPolicy
from ontokin.framed_loft_agent import FramedLoftAgentService
from ontokin.pockets_agent import PocketsAgentService
from ontokin.pockets_protocol import PocketsProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.scene import ExportOptions
from tests.test_export import DecodedGLB


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/polygon-pockets"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text())
CASES = {case["id"]: case for case in EXPECTED["cases"]}
PROTOCOL, PROFILE, TARGET = "ontokin.agent/0.12", "polygon-pockets-0.1", "ontokin.glb/0.12"
PROJECT = "pockets"
SHAPE = ["pocket-case", "demo", "shape"]
FIRST, SIBLING = ["pocket-assembly", "demo", "first"], ["pocket-assembly", "demo", "sibling"]
OPTIONS = {"fps": 4, "end": "1", "helpers": False}
EDIT_OLD, EDIT_NEW = '}, 0.5[m], "floor")', '}, 0.75[m], "floor")'


def source(name="rectangular-pocket", *, text=None):
    text = (FIXTURES / (name + ".ok")).read_text() if text is None else text
    modules = []
    if 'from "fixture.pocket-parts"' in text:
        modules.append({"package_id": "fixture.pocket-parts", "version": "1.0.0",
                        "filename": "parts.ok", "source": (FIXTURES / "parts.ok").read_text()})
    return load_bundle({"schema_version": "ontokin.bundle/0.1",
        "entry": {"filename": name + ".ok", "source": text}, "modules": modules})


def exact_patch(program, before, after):
    raw = before.encode()
    offset = program.entry.raw.index(raw)
    return {"source_id": "entry", "source_revision": program.entry.revision,
        "element_id": ["sources", "entry"], "start_byte": offset,
        "end_byte": offset + len(raw), "expected_text": before, "replacement": after}


def geometry(page):
    return {key: page[key] for key in ("positions_m", "normals", "triangles", "region_keys")}


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def decoded_geometry(decoded, object_path):
    """Measure supplied position/index/normal streams without the pocket builder."""
    _, node = decoded.source_node(object_path)
    mesh = decoded.document["meshes"][node["mesh"]]
    volume, area, triangles, regions, streams = 0., 0., 0, {}, {}
    for primitive in mesh["primitives"]:
        positions = decoded.accessor(primitive["attributes"]["POSITION"])
        normals = decoded.accessor(primitive["attributes"]["NORMAL"])
        indices = [row[0] for row in decoded.accessor(primitive["indices"])]
        key = primitive["extras"]["ontokin"]["region_key"]
        regions[key] = len(indices) // 3
        streams[key] = {"positions": positions, "normals": normals, "indices": indices}
        for start in range(0, len(indices), 3):
            ia, ib, ic = indices[start:start+3]
            a, b, c = (positions[i] for i in (ia, ib, ic))
            face = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
            if sum(face[i]*normals[ia][i] for i in range(3)) <= 0:
                raise AssertionError("Delivered face normal does not point outward")
            volume += sum(a[i]*cross(b, c)[i] for i in range(3)) / 6
            area += math.sqrt(sum(v*v for v in face)) / 2
            triangles += 1
    return {"volume": volume, "area": area, "triangles": triangles,
            "regions": regions, "streams": streams}


class PocketsAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        paths = list((ROOT / "docs/language-design/agent-v0.12").glob("*.schema.json"))
        paths += [ROOT / "docs/language-design" / name for name in (
            "construction-v0.1/bundle.schema.json", "agent-v0.2/diagnostic.schema.json",
            "force-v0.1/forces.schema.json", "impulse-v0.1/impulses.schema.json",
            "planar-reach-v0.1/schema-drafts/reach-projection.schema.json",
            "planar-reach-v0.1/schema-drafts/reach-diagnostic.schema.json",
            "planar-reach-v0.1/schema-drafts/common.schema.json")]
        schemas = [json.loads(path.read_text()) for path in paths]
        registry = Registry().with_resources((item["$id"], Resource.from_contents(item)) for item in schemas)
        for item in schemas:
            Draft202012Validator.check_schema(item)
        cls.validators = {path.name: Draft202012Validator(item, registry=registry)
                          for path, item in zip(paths, schemas)}

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c079-agent-")
        self.service = PocketsAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": PROJECT,
                "request_id": f"pockets-{self.serial}", "operation": operation, **fields}

    def send(self, operation, **fields):
        request = self.request(operation, **fields)
        self.validators["request.schema.json"].validate(request)
        PocketsProtocol.validate_request(request)
        return self.service.handle(request)

    def success(self, response):
        self.assertEqual(response["schema_version"], PROTOCOL, response)
        self.assertEqual(response["status"], "succeeded", response)
        self.validators["response.schema.json"].validate(response)
        return response

    def failure(self, response, code=None):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        self.validators["response.schema.json"].validate(response)
        if code:
            codes = [d["code"] for d in response["diagnostics"]]
            if response["protocol_error"]:
                codes.append(response["protocol_error"]["code"])
            self.assertIn(code, codes, response)
        return response

    def create(self, program=None, *, project=PROJECT):
        program = source() if program is None else program
        self.success(self.send("create", project_id=project, bundle=program.to_payload(),
            expected_program_revision=None, requested_level="constructed"))
        return program

    def inspect(self, program, *, path="shape", project=PROJECT):
        return self.success(self.send("inspect", project_id=project,
            program_revision=program.program_revision, selector={"path": path},
            fields=["identity", "geometry", "support"], limit=1))

    def page(self, program, element=SHAPE, *, project=PROJECT, **fields):
        fields.setdefault("count", 256)
        result = self.success(self.send("surface.mesh_page", project_id=project,
            program_revision=program.program_revision, element_id=element, **fields))
        self.assertEqual(result["result"]["profile"], PROFILE)
        return result

    def export(self, program, *, project=PROJECT):
        return self.success(self.send("export", project_id=project,
            program_revision=program.program_revision, destination=TARGET, options=OPTIONS))

    def retrieve(self, exported, *, project=PROJECT, **fields):
        pieces, offset = [], 0
        for _ in range(200):
            response = self.success(self.send("artifact", project_id=project,
                artifact_id=exported["result"]["artifact_id"], offset=offset, max_bytes=2048, **fields))
            piece = response["result"]
            self.assertEqual(piece["offset"], offset)
            pieces.append(base64.b64decode(piece["data_base64"], validate=True))
            offset = piece["next_offset"]
            if offset is None:
                break
        else:
            self.fail("Artifact retrieval did not terminate")
        data = b"".join(pieces)
        self.assertEqual(len(data), exported["result"]["total_bytes"])
        self.assertEqual("sha256:" + hashlib.sha256(data).hexdigest(), exported["result"]["sha256"])
        return data

    def retained(self):
        with self.service._store.connection() as db:
            return {"accepted": self.service.accepted_revision(PROJECT),
                "runs": [tuple(row) for row in db.execute("SELECT id,source_revision,descriptor,version FROM runs ORDER BY id")],
                "artifacts": [tuple(row) for row in db.execute("SELECT id,data,sha256 FROM artifacts ORDER BY id")]}

    def test_discovery_names_constructors_limits_schemas_and_separate_store(self):
        response = self.success(self.send("discover", profile=PROFILE, limit=1000))
        result = response["result"]
        self.assertLessEqual(response["execution_budget"]["consumed_operations"], 100000)
        self.assertEqual(result["language_version"], "0.12")
        self.assertEqual(result["agent_contract"], PROTOCOL)
        self.assertEqual(result["delivery_targets"], [TARGET])
        self.assertEqual(result["source_header"], 'ontokin "0.12"; module Example @ "example"; profile "polygon-pockets-0.1";')
        names = {item["name"] for item in result["items"]}
        self.assertTrue({"PolygonPocket", "polygon_pocket", "extrude_pockets", "PlanarPoint",
            "PolygonVertex", "PolygonRing", "PolygonSection", "FramedPolygonSection",
            "extrude", "extrude_rings", "loft_rings", "loft_framed_rings"} <= names)
        interface = result["polygon_pockets_interface"]
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["polygon_pockets_limits"]["max_total_vertices"], 64)
        self.assertEqual(interface["polygon_pockets_limits"]["max_pockets"], 8)
        self.assertEqual(interface["polygon_pockets_limits"]["max_triangles"], 252)
        self.assertEqual(interface["pocket_floor_rule"], "exact-rational-subtract-single-binary64-round")
        self.assertEqual(set(interface["operations"]), {"discover", "create", "edit", "validate",
            "inspect", "evaluate", "reset", "status", "cancel", "export", "artifact", "surface.mesh_page"})
        from ontokin.framed_loft_agent_catalog import catalog as old_catalog, interface as old_interface
        previous = old_interface(self.service.host_policy, aggregate_limits=self.service.aggregate_limits())
        inherited = result["inherited_geometry_interfaces"][-1]
        self.assertEqual(inherited, {key: previous[key] for key in inherited})
        self.assertEqual(inherited["agent_contract"], "ontokin.agent/0.11")
        self.assertEqual(inherited["delivery_contract"], "ontokin.glb/0.11")
        self.assertNotIn("host_ceilings", inherited)
        for item in result["items"]:
            if item["kind"] == "protocol":
                self.assertEqual(item["name"], PROTOCOL)
                self.assertIn("PocketsAgentService", item["signature"])
            elif item["kind"] == "destination":
                self.assertEqual(item["name"], TARGET)
                self.assertEqual(item["capability"], TARGET)
        inherited_catalog = old_catalog(policy=self.service.host_policy,
                                        aggregate_limits=self.service.aggregate_limits())
        by_name = {(item["kind"], item["name"]): item for item in result["items"]}
        extended = {"Geometry", "Keyed", "placed", "geometry.surface", "surface.mesh_page",
                    "persistent_agent_editing_service"}
        for item in inherited_catalog["items"]:
            if item["kind"] not in {"protocol", "destination"} and item["name"] not in extended:
                self.assertEqual(by_name[(item["kind"], item["name"])], item)
            if item["name"] == "geometry.surface":
                self.assertEqual(by_name[(item["kind"], item["name"])]["summary_contracts"],
                                 item["summary_contracts"] + ["ontokin.polygon-pockets-summary/0.1"])
        for key in ("request_schema", "response_schema", "adoption"):
            self.assertTrue((ROOT / interface[key]).is_file())
        self.assertEqual(self.service.database_path.name, "pockets-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.pockets-program-agent-store/0.1")
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)

    def test_discovery_links_source_without_accepting_it(self):
        program = source()
        result = self.success(self.send("discover", profile=PROFILE, limit=1000, bundle=program.to_payload()))
        self.assertEqual(result["result"]["program_context"]["program_revision"], program.program_revision)
        self.assertIsNone(self.service.accepted_revision(PROJECT))
        self.assertEqual(result["execution_budget"]["source_request"]["max_operations"], 100000)

    def test_discovery_template_never_retains_caller_mutations_or_host_authority(self):
        first = self.success(self.send("discover", profile=PROFILE, limit=1000))
        first["result"]["items"][0]["description"] = "caller mutation"
        first["result"]["polygon_pockets_interface"]["host_ceilings"]["max_operations"] = 1
        policy = HostPolicy(400000, 80000)
        self.service.host_policy = policy
        self.service.max_pending_requests = 17
        second = self.success(self.send("discover", profile=PROFILE, limit=1000))
        current = second["result"]["polygon_pockets_interface"]
        self.assertNotEqual(second["result"]["items"][0]["description"], "caller mutation")
        self.assertEqual(current["host_ceilings"], policy.ceilings)
        self.assertEqual(current["policy_id"], policy.policy_id)
        self.assertEqual(current["aggregate_limits"]["max_pending_requests"], 17)
        self.assertIsNone(second["result"]["program_context"])
        self.assertEqual(current["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertLessEqual(second["execution_budget"]["consumed_operations"], 100000)
        retained = self.retained()
        limited = self.failure(self.send("discover", profile=PROFILE, limit=1000,
            budgets={"max_operations": 1000}), "OKL-E-RESOURCE")
        self.assertEqual(limited["execution_budget"]["budget_reason"], "operation_budget_exhausted")
        self.assertEqual(limited["result"], {
            "outcome": "resource_limit", "requested_level": None, "achieved_level": None,
            "run_state": None, "delivery": "not_requested",
            "implementation": limited["progress"]["implementation"],
            "partial_results": "Only already-retained immutable source snapshots and any previously committed run descriptor are available."})
        self.assertNotIn("items", limited["result"])
        self.assertNotIn("artifact_id", limited["result"])
        self.assertEqual(self.retained(), retained)
        self.assertIsNone(self.service.accepted_revision(PROJECT))

    def test_summary_exposes_boundaries_floors_counts_and_material_ownership(self):
        program = self.create()
        item = self.inspect(program)["result"]["items"][0]
        summary = item["geometry"]["surface"]
        expected = CASES["rectangular-pocket"]["geometry"]
        self.assertEqual(summary["schema_version"], "ontokin.polygon-pockets-summary/0.1")
        self.assertEqual(summary["profile"], PROFILE)
        self.assertEqual(summary["family"], "polygon_pockets")
        for name in ("height_m", "pocket_count", "authored_vertex_count", "logical_vertex_count",
                     "bottom_triangle_count", "top_triangle_count", "floor_triangle_count",
                     "wall_triangle_count", "triangle_count", "vertex_count"):
            self.assertEqual(summary[name], expected[name], name)
        self.assertEqual([v["key"] for v in summary["outer_vertices"]], ["v0", "v1", "v2", "v3"])
        pocket = summary["pockets"][0]
        self.assertEqual((pocket["key"], pocket["order"], pocket["depth_m"], pocket["floor_region"]),
                         ("recess", 20, .5, "floor"))
        self.assertEqual(pocket["floor_m"], 1.5)
        self.assertEqual(pocket["remaining_base_m"], 1.5)
        self.assertEqual(pocket["exact_remaining_base_m"], {"numerator": "3", "denominator": "2"})
        self.assertEqual(pocket["effective_depth_m"], {"numerator": "1", "denominator": "2"})
        self.assertEqual(pocket["vertices"][0],
            {"key": "v0", "order": 0, "point_m": [1., 1.], "side_region": "inner"})
        self.assertEqual({r["key"]: r["triangle_count"] for r in summary["regions"]},
                         expected["region_triangle_counts"])
        self.assertEqual((summary["palette_count"], summary["used_region_count"]), (5, 5))
        self.assertEqual(summary["physical_participation"], "none")
        self.assertEqual(item["support"]["named_destination"], TARGET)
        self.assertNotIn("sections", summary)

    def test_exact_floor_summary_matches_frozen_arithmetic_controls(self):
        for name in ("rounded-floor", "minimum-base", "above-minimum-base", "unequal-depths"):
            with self.subTest(case=name):
                program = self.create(source(name), project=name)
                summary = self.inspect(program, project=name)["result"]["items"][0]["geometry"]["surface"]
                expected = CASES[name]["geometry"]
                for actual, required in zip(summary["pockets"], expected["pockets"]):
                    for key in ("key", "depth_m", "floor_m", "remaining_base_m",
                                "exact_remaining_base_m", "effective_depth_m"):
                        self.assertEqual(actual[key], required[key], key)
                    exact = actual["exact_remaining_base_m"]
                    effective = actual["effective_depth_m"]
                    self.assertEqual(Fraction(int(exact["numerator"]), int(exact["denominator"])),
                                     Fraction(summary["height_m"]) - Fraction(actual["depth_m"]))
                    self.assertEqual(Fraction(int(effective["numerator"]), int(effective["denominator"])),
                                     Fraction(summary["height_m"]) - Fraction(actual["floor_m"]))

    def test_mesh_pages_cover_all_faces_and_select_actual_floor(self):
        program = self.create()
        page = self.page(program, count=5)
        ordinals = list(page["result"]["source_triangle_ordinals"])
        while page["next_cursor"]:
            page = self.page(program, count=7, cursor=page["next_cursor"])
            ordinals += page["result"]["source_triangle_ordinals"]
        self.assertEqual(ordinals, list(range(28)))
        floor = self.page(program, region="floor")["result"]
        self.assertEqual(floor["returned_triangles"], 2)
        self.assertEqual(set(floor["region_keys"]), {"floor"})
        self.assertEqual({p[2] for p in floor["positions_m"]}, {1.5})
        self.assertTrue(all(normal == [0., 0., 1.] for normal in floor["normals"]))
        self.failure(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=SHAPE, count=3, budgets={"max_result_items": 2}), "OKL-E-RESOURCE")

    def test_pocket_and_vertex_declaration_reordering_preserves_mesh(self):
        program = self.create(source("unequal-depths"))
        before = self.page(program)["result"]
        text = (FIXTURES / "declaration-reordering.ok").read_text()
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, program.entry.text, text)]))
        revised = source("unequal-depths", text=text)
        self.assertEqual(response["accepted_program_revision"], revised.program_revision)
        after = self.page(revised)["result"]
        self.assertEqual(geometry(before), geometry(after))
        self.assertEqual(before["geometry_sha256"], after["geometry_sha256"])

    def test_material_regions_and_zero_pocket_summary_keep_their_domains(self):
        for name in ("mixed-wall-materials", "maximum-palette", "zero-pockets", "pocket-key-outer"):
            with self.subTest(case=name):
                program = self.create(source(name), project=name)
                summary = self.inspect(program, project=name)["result"]["items"][0]["geometry"]["surface"]
                expected = CASES[name]["geometry"]
                self.assertEqual({r["key"]: r["triangle_count"] for r in summary["regions"]},
                                 expected["region_triangle_counts"])
                self.assertEqual(summary["palette_count"], len(expected["palette"]))
                self.assertEqual(summary["used_region_count"], len(expected["region_triangle_counts"]))
                self.assertEqual(summary["logical_vertex_count"], expected["logical_vertex_count"])
                self.assertEqual(summary["floor_triangle_count"], expected["floor_triangle_count"])

    def test_exported_control_has_floor_volume_area_materials_and_recorded_motion(self):
        program = self.create()
        exported = self.export(program)
        decoded = DecodedGLB(self.retrieve(exported))
        measured = decoded_geometry(decoded, "shape")
        self.assertAlmostEqual(measured["volume"], 23., places=10)
        self.assertAlmostEqual(measured["area"], 55., places=10)
        self.assertEqual(measured["triangles"], 28)
        self.assertEqual(measured["regions"], CASES["rectangular-pocket"]["geometry"]["region_triangle_counts"])
        floor = measured["streams"]["floor"]
        self.assertEqual({floor["positions"][i][2] for i in floor["indices"]}, {1.5})
        for when in EXPECTED["sample_times_seconds"]:
            position = decoded.node_pose("shape", when)["translation"]
            self.assertAlmostEqual(position[0], 0., places=7)
            self.assertAlmostEqual(position[1], when*.5, places=7)
            self.assertAlmostEqual(position[2], 0., places=7)
        self.assertEqual(exported["result"]["destination"], TARGET)
        self.assertGreater(exported["execution_budget"]["consumed_operations"],
            exported["result"]["report"]["execution_budget_at_export"]["consumed_operations"])

    def test_zero_pocket_delivery_preserves_exact_08_local_streams(self):
        for case in EXPECTED["legacy_equivalence"]:
            with self.subTest(case=case["case"]):
                program = self.create(source(case["case"]), project=case["case"])
                current = DecodedGLB(self.retrieve(self.export(program, project=case["case"]), project=case["case"]))
                legacy = source(case["source"][:-3])
                old = execute_extrusion_export(legacy, options=ExportOptions(fps=4, end="1", helpers=False))
                self.assertIsNotNone(old.data, old.report)
                self.assertEqual(decoded_geometry(current, "shape")["streams"],
                                 decoded_geometry(DecodedGLB(old.data), "shape")["streams"])

    def test_depth_repair_preserves_sibling_library_and_nominal_occurrence(self):
        program = self.create(source("assembly"))
        before_first = self.page(program, FIRST)["result"]
        before_sibling = self.page(program, SIBLING)["result"]
        edit = EXPECTED["assembly"]["repair"]
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, edit["old"], edit["new"])]))
        revised = source("assembly", text=program.entry.text.replace(edit["old"], edit["new"]))
        self.assertEqual(response["accepted_program_revision"], revised.program_revision)
        saved = self.service.read_program(PROJECT, revised.program_revision)
        self.assertEqual(saved.modules[0].raw, program.modules[0].raw)
        self.assertEqual(geometry(self.page(revised, SIBLING)["result"]), geometry(before_sibling))
        after = self.page(revised, FIRST)["result"]
        self.assertNotEqual(geometry(after), geometry(before_first))
        self.assertEqual(after["element_id"], before_first["element_id"])
        decoded = DecodedGLB(self.retrieve(self.export(revised)))
        self.assertAlmostEqual(decoded_geometry(decoded, "first")["volume"], 22.5, places=10)
        self.assertAlmostEqual(decoded_geometry(decoded, "sibling")["volume"], 23., places=10)

    def test_invalid_depth_and_topology_edits_preserve_source_runs_and_artifacts(self):
        program = self.create()
        self.success(self.send("evaluate", program_revision=program.program_revision, run_id=None, until_seconds="0.5"))
        self.export(program)
        before = self.retained()
        for name in ("depth-equals-height", "below-minimum-base", "pocket-touching-boundary",
                     "nested-pockets", "missing-floor-region", "counterclockwise-pocket"):
            with self.subTest(case=name):
                text = (FIXTURES / (name + ".ok")).read_text()
                response = self.failure(self.send("edit", expected_program_revision=program.program_revision,
                    requested_level="delivered", destination=TARGET, options=OPTIONS,
                    patches=[exact_patch(program, program.entry.text, text)]), CASES[name]["diagnostic_code"])
                self.assertEqual(self.retained(), before)
                self.assertNotEqual(response["achieved_level"], "delivered")
                self.assertNotIn("artifact_id", response.get("result") or {})
                self.assertTrue(response["diagnostics"][0].get("primary"))

    def test_stale_file_preconditions_and_nominal_identity_reject_atomically(self):
        program = self.create()
        edit = exact_patch(program, EDIT_OLD, EDIT_NEW)
        before = self.retained()
        for modified in ({**edit, "expected_text": "wrong"},
                         {**edit, "source_revision": "sha256:" + "0"*64},
                         {**edit, "element_id": SHAPE}):
            request = self.request("edit", expected_program_revision=program.program_revision,
                                  requested_level="constructed", patches=[modified])
            self.failure(self.service.handle(request))
            self.assertEqual(before, self.retained())
        self.failure(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program,
                'class Shape @ "shape"', 'class Shape @ "different"')]), "OKL-E-ID")
        self.assertEqual(before, self.retained())

    def test_cursor_cannot_change_revision_or_material_filter(self):
        program = self.create()
        first = self.page(program, count=2)
        self.failure(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=SHAPE, count=2, cursor=first["next_cursor"], region="floor"))
        self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, EDIT_OLD, EDIT_NEW)]))
        revised = source(text=program.entry.text.replace(EDIT_OLD, EDIT_NEW))
        self.failure(self.send("surface.mesh_page", program_revision=revised.program_revision,
            element_id=SHAPE, count=2, cursor=first["next_cursor"]))

    def test_delivered_floor_and_opening_collapse_never_publish_artifacts(self):
        self.service.host_policy = HostPolicy(**EXPECTED["maximum_host_policy"])
        for name in ("binary32-floor-collapse", "binary32-pocket-width-collapse", "binary32-boundary-clearance"):
            with self.subTest(case=name):
                program = self.create(source(name), project=name)
                before = self.retained()["artifacts"]
                response = self.failure(self.send("export", project_id=name,
                    program_revision=program.program_revision, destination=TARGET, options=OPTIONS))
                codes = {item["code"] for item in response["diagnostics"]}
                if response["protocol_error"]:
                    codes.add(response["protocol_error"]["code"])
                self.assertNotIn("OKL-E-RESOURCE", codes, response)
                export_codes = {item.get("details", {}).get("export_code")
                                for item in response["diagnostics"]}
                expected_code = ("OKE-E-GEOMETRY-PRECISION" if name == "binary32-floor-collapse"
                                 else "OKE-E-GLB-STRUCTURE")
                self.assertEqual(export_codes, {expected_code}, response)
                self.assertEqual(codes, {"OKL-E-NUMERIC"} if expected_code == "OKE-E-GEOMETRY-PRECISION"
                                 else {"OKL-E-CAPABILITY-UNSUPPORTED"}, response)
                self.assertIsNone(response["execution_budget"]["budget_reason"], response)
                if expected_code == "OKE-E-GLB-STRUCTURE":
                    self.assertIn("degenerate triangle", response["diagnostics"][0]["message"])
                self.assertEqual(self.retained()["artifacts"], before)
                self.assertNotEqual(response["achieved_level"], "delivered")
                self.assertNotIn("artifact_id", response.get("result") or {})

    def test_durable_retry_survives_reopen_and_refuses_changed_payload(self):
        program = self.create()
        request = self.request("export", program_revision=program.program_revision, destination=TARGET, options=OPTIONS)
        response = self.success(self.service.handle(request))
        before = self.retained()
        self.service.close()
        self.service = PocketsAgentService(self.directory.name)
        with patch.object(self.service, "_execute", side_effect=AssertionError("replayed")):
            self.assertEqual(self.service.handle(copy.deepcopy(request)), response)
        changed = copy.deepcopy(request)
        changed["options"]["fps"] = 3
        self.failure(self.service.handle(changed), "OKL-E-REQUEST-ID")
        self.assertEqual(before, self.retained())
        self.assertTrue(self.retrieve(response).startswith(b"glTF"))

    def test_saved_artifact_and_run_reauthorize_current_host_policy(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        text = source().entry.text.replace('profile "polygon-pockets-0.1";',
            'profile "polygon-pockets-0.1";\nexecution { max_operations = 200000; max_elapsed = 60[s]; }')
        program = self.create(source(text=text))
        exported = self.export(program)
        run = self.success(self.send("evaluate", program_revision=program.program_revision,
                                     run_id=None, until_seconds="0.5"))
        before = self.retained()
        self.service.host_policy = HostPolicy()
        for operation, fields in (
            ("artifact", {"artifact_id": exported["result"]["artifact_id"], "max_bytes": 64}),
            ("evaluate", {"program_revision": program.program_revision, "run_id": run["run_id"], "until_seconds": "1"})):
            response = self.failure(self.send(operation, **fields), "OKL-E-RESOURCE")
            self.assertEqual(response["execution_budget"]["budget_reason"], "host_ceiling_exceeded")
        self.assertEqual(before, self.retained())
        reduced = self.success(self.send("artifact", artifact_id=exported["result"]["artifact_id"],
            max_bytes=64, budgets={"max_operations": 100000, "max_elapsed_ms": 30000}))
        self.assertEqual(base64.b64decode(reduced["result"]["data_base64"])[:4], b"glTF")

    def test_omitted_limits_stay_default_and_caller_caps_only_reduce(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        program = self.create()
        response = self.success(self.send("validate", program_revision=program.program_revision,
                                          requested_level="constructed"))
        self.assertEqual(response["execution_budget"]["effective"],
                         {"max_operations": 100000, "max_elapsed_ms": 30000})
        bad = self.failure(self.send("validate", program_revision=program.program_revision,
            requested_level="constructed", budgets={"max_operations": 100001}), "OKL-E-RESOURCE")
        self.assertEqual(bad["execution_budget"]["budget_reason"], "request_cap_exceeds_source")

    def test_budget_failure_and_expiry_after_export_leave_no_tentative_effects(self):
        program = self.create()
        before = self.retained()
        self.failure(self.send("validate", program_revision=program.program_revision,
            requested_level="constructed", budgets={"max_operations": 5}), "OKL-E-RESOURCE")
        state = {"late": False}
        self.service._clock = lambda: 31. if state["late"] else 0.
        original = self.service._execute
        def expire_after_export(task, check):
            result = original(task, check)
            state["late"] = True
            return result
        with patch.object(self.service, "_execute", side_effect=expire_after_export):
            response = self.failure(self.send("export", program_revision=program.program_revision,
                destination=TARGET, options=OPTIONS), "OKL-E-RESOURCE")
        self.assertNotEqual(response["achieved_level"], "delivered")
        self.assertNotIn("artifact_id", response.get("result") or {})
        self.assertEqual(before, self.retained())

    def test_post_insert_publication_failure_rolls_back_artifact_and_run(self):
        program = self.create()
        before = self.retained()
        original = self.service._check_task_response
        checks = []
        def fail_after_insert(task):
            if task.request["operation"] == "export" and task.response["status"] == "succeeded":
                checks.append(task.artifact is not None)
                if len(checks) == 2:
                    raise ProtocolError("OKL-E-RESOURCE", "Injected failure before transaction commit")
            return original(task)
        with patch.object(self.service, "_check_task_response", side_effect=fail_after_insert):
            response = self.failure(self.send("export", program_revision=program.program_revision,
                destination=TARGET, options=OPTIONS), "OKL-E-RESOURCE")
        self.assertEqual(checks, [True, True])
        self.assertEqual(before, self.retained())
        self.assertNotIn("artifact_id", response.get("result") or {})

    def test_budget_reducing_depth_repair_uses_candidate_authority(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        text = source().entry.text.replace('profile "polygon-pockets-0.1";',
            'profile "polygon-pockets-0.1";\nexecution { max_operations = 200000; max_elapsed = 60[s]; }')
        program = self.create(source(text=text))
        self.service.host_policy = HostPolicy()
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, "200000", "100000"),
                exact_patch(program, "60[s]", "30[s]"), exact_patch(program, EDIT_OLD, EDIT_NEW)]))
        revised = source(text=text.replace("200000", "100000").replace("60[s]", "30[s]").replace(EDIT_OLD, EDIT_NEW))
        self.assertEqual(response["accepted_program_revision"], revised.program_revision)
        self.assertEqual(response["execution_budget"]["source_request"],
                         {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual({p[2] for p in self.page(revised, region="floor")["result"]["positions_m"]}, {1.25})

    def test_host_cancellation_inside_pocket_construction_preserves_exception_identity(self):
        from ontokin import pockets
        from ontokin.diagnostics import OntoKinError
        marker = OntoKinError("OKL-E-POCKETS-DEPTH", "trusted caller interrupt")
        state = {"armed": False, "calls": 0}
        def check():
            state["calls"] += 1
            if state["armed"]:
                raise marker
        self.service._host_check = check
        original = pockets.triangulate_pockets
        def arm(*args, **kwargs):
            state["armed"] = True
            return original(*args, **kwargs)
        request = self.request("create", bundle=source().to_payload(), expected_program_revision=None,
                               requested_level="constructed")
        with patch.object(pockets, "triangulate_pockets", side_effect=arm):
            with self.assertRaises(OntoKinError) as caught:
                self.service.handle(request)
        self.assertIs(caught.exception, marker)
        self.assertGreater(state["calls"], 1)
        calls = state["calls"]
        response = self.service.handle(request)
        self.assertEqual(response["status"], "cancelled", response)
        self.validators["response.schema.json"].validate(response)
        self.assertEqual(state["calls"], calls)
        self.assertEqual(self.retained(), {"accepted": None, "runs": [], "artifacts": []})

    def test_older_binding_and_destination_are_refused(self):
        with self.assertRaises(ProtocolError):
            PocketsAgentService(self.directory.name, protocol="ontokin.agent/0.11")
        request = self.request("discover", profile=PROFILE, limit=10)
        request["schema_version"] = "ontokin.agent/0.11"
        self.failure(self.service.handle(request), "OKA-E-REQUEST")
        program = self.create()
        request = self.request("export", program_revision=program.program_revision,
            destination="ontokin.glb/0.11", options=OPTIONS)
        self.failure(self.service.handle(request), "OKA-E-REQUEST")
        from tests.test_framed_loft_agent import source as old_source
        self.failure(self.send("create", project_id="older-entry", bundle=old_source().to_payload(),
            expected_program_revision=None, requested_level="constructed"))
        self.assertIsNone(self.service.accepted_revision("older-entry"))
        self.assertEqual(self.service.accepted_revision(PROJECT), program.program_revision)

    def test_previous_service_keeps_separate_acceptance_in_same_directory(self):
        from tests.test_framed_loft_agent import source as old_source
        program = self.create()
        with FramedLoftAgentService(self.directory.name) as old:
            self.assertIsNone(old.accepted_revision(PROJECT))
            inherited = old_source()
            response = old.handle({"schema_version": "ontokin.agent/0.11", "project_id": PROJECT,
                "request_id": "frames-1", "operation": "create", "bundle": inherited.to_payload(),
                "expected_program_revision": None, "requested_level": "constructed"})
            self.assertEqual(response["status"], "succeeded", response)
            self.assertEqual(old.accepted_revision(PROJECT), inherited.program_revision)
            self.assertNotEqual(old.database_path, self.service.database_path)
        self.assertEqual(self.service.accepted_revision(PROJECT), program.program_revision)

    def test_all_five_inherited_summary_definitions_remain_unchanged(self):
        previous = json.loads((ROOT / "docs/language-design/agent-v0.11/response.schema.json").read_text())
        current = json.loads((ROOT / "docs/language-design/agent-v0.12/response.schema.json").read_text())
        for name in ("surface_summary", "extrusion_summary", "holes_summary", "ring_loft_summary", "framed_loft_summary"):
            self.assertEqual(current["$defs"][name], previous["$defs"][name], name)

    def test_inherited_pinned_framed_definition_keeps_its_summary_and_mesh(self):
        from tests.test_framed_loft_agent import source as old_source
        inherited = old_source("assembly")
        payload = inherited.to_payload()
        payload["entry"]["source"] = inherited.entry.text.replace('"0.11"', '"0.12"', 1).replace(
            "framed-polygon-loft-0.1", PROFILE, 1)
        program = self.create(load_bundle(payload))
        self.assertEqual(program.modules[0].raw, inherited.modules[0].raw)
        item = self.inspect(program, path="first")["result"]["items"][0]
        summary = item["geometry"]["surface"]
        self.assertEqual(summary["schema_version"], "ontokin.framed-polygon-loft-summary/0.1")
        self.assertEqual(summary["profile"], "framed-polygon-loft-0.1")
        self.assertNotIn("pockets", summary)
        self.page(program, item["element_id"])
        self.assertAlmostEqual(decoded_geometry(DecodedGLB(self.retrieve(self.export(program))), "first")["volume"], 12., places=10)

    def test_free_function_construction_and_pocket_key_outer_are_admitted(self):
        for name in ("function-pocket-and-geometry", "pocket-key-outer"):
            with self.subTest(case=name):
                program = self.create(source(name), project=name)
                self.assertEqual(self.page(program, project=name)["result"]["total_triangles"], 28)
                measured = decoded_geometry(DecodedGLB(self.retrieve(self.export(program, project=name), project=name)), "shape")
                self.assertAlmostEqual(measured["volume"], CASES[name]["geometry"]["volume_m3"], places=10)

    def test_response_schema_rejects_malformed_pocket_summary(self):
        from jsonschema import ValidationError
        program = self.create()
        response = self.inspect(program)
        for change in ("pocket_count", "point", "vertex_count", "logical_count", "floor_region",
                       "depth", "base", "numerator", "denominator", "fraction_shape", "sections", "floor_count"):
            bad = copy.deepcopy(response)
            summary = bad["result"]["items"][0]["geometry"]["surface"]
            pocket = summary["pockets"][0]
            if change == "pocket_count":
                summary["pocket_count"] = 9
            elif change == "point":
                pocket["vertices"][0]["point_m"] = [0, 0, 0]
            elif change == "vertex_count":
                summary["authored_vertex_count"] = 65
            elif change == "logical_count":
                summary["logical_vertex_count"] = 129
            elif change == "floor_region":
                pocket.pop("floor_region")
            elif change == "depth":
                pocket["depth_m"] = 0
            elif change == "base":
                pocket["remaining_base_m"] = -1
            elif change == "numerator":
                pocket["exact_remaining_base_m"]["numerator"] = 3
            elif change == "denominator":
                pocket["effective_depth_m"]["denominator"] = "0"
            elif change == "fraction_shape":
                pocket["effective_depth_m"] = [1, 2]
            elif change == "sections":
                summary["sections"] = []
            else:
                summary["floor_triangle_count"] = -1
            with self.assertRaises(ValidationError):
                self.validators["response.schema.json"].validate(bad)

    def test_direct_export_and_cli_require_explicit_012_binding(self):
        program = source()
        direct = execute_pockets_export(program, options=ExportOptions(fps=4, end="1", helpers=False))
        self.assertIsNotNone(direct.data, direct.report)
        self.assertEqual(direct.report["target_contract"], TARGET)
        self.assertEqual(direct.report["language_version"], "0.12")
        self.assertIsNone(execute_framed_loft_export(program).data)
        output = Path(self.directory.name) / "pocket.glb"
        result = subprocess.run([sys.executable, "-m", "ontokin", "export", str(FIXTURES / "rectangular-pocket.ok"),
            "--target", TARGET, "--output", str(output), "--fps", "4", "--end", "1", "--no-helpers"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertAlmostEqual(decoded_geometry(DecodedGLB(output.read_bytes()), "shape")["volume"], 23., places=10)

    def test_cli_agent_discovery_and_host_policy_injection_refusal(self):
        request = self.request("discover", profile=PROFILE, limit=1000)
        path = Path(self.directory.name) / "request.json"
        path.write_text(json.dumps(request))
        result = subprocess.run([sys.executable, "-m", "ontokin", "agent", "--protocol", PROTOCOL,
            "--store", str(Path(self.directory.name) / "cli"), "--request", str(path), "--wait"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"]["language_version"], "0.12")
        request = self.request("discover", profile=PROFILE, limit=10, host_policy={"max_operations": 400000})
        self.failure(self.service.handle(request), "OKA-E-REQUEST")

    def test_all_twelve_operations_execute_with_published_wire_shapes(self):
        operations = set()
        def perform(operation, *, queued=False, **fields):
            request = self.request(operation, **fields)
            self.validators["request.schema.json"].validate(request)
            PocketsProtocol.validate_request(request)
            response = self.service.handle(request, wait=not queued)
            self.validators["response.schema.json"].validate(response)
            if queued:
                self.assertEqual(response["status"], "queued", response)
            else:
                self.success(response)
            operations.add(operation)
            return request, response
        perform("discover", profile=PROFILE, limit=1000)
        program = source()
        perform("create", bundle=program.to_payload(), expected_program_revision=None, requested_level="constructed")
        perform("validate", program_revision=program.program_revision, requested_level="constructed")
        perform("edit", expected_program_revision=program.program_revision, requested_level="constructed",
            patches=[exact_patch(program, EDIT_OLD, EDIT_NEW)])
        program = source(text=program.entry.text.replace(EDIT_OLD, EDIT_NEW))
        perform("inspect", program_revision=program.program_revision, selector={"path": "shape"},
                fields=["identity", "geometry", "support"], limit=1)
        perform("surface.mesh_page", program_revision=program.program_revision, element_id=SHAPE, region="floor", count=2)
        perform("evaluate", program_revision=program.program_revision, run_id=None, until_seconds="1")
        export_request, exported = perform("export", program_revision=program.program_revision, destination=TARGET, options=OPTIONS)
        perform("artifact", artifact_id=exported["result"]["artifact_id"], offset=0, max_bytes=1024)
        perform("status", target_request_id=export_request["request_id"])
        perform("reset", program_revision=program.program_revision)
        pending, _ = perform("validate", queued=True, program_revision=program.program_revision, requested_level="evaluated")
        perform("cancel", target_request_id=pending["request_id"])
        status = self.success(self.send("status", target_request_id=pending["request_id"]))
        self.assertEqual(status["result"]["target_status"], "cancelled")
        self.assertEqual(operations, set(PocketsProtocol.OPERATIONS))
