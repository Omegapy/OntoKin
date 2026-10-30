"""Actual matched-section repair, bounded inspection and durable .10 delivery."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ontokin.agent_protocol import ProtocolError
from ontokin.budget_runtime import execute_holes_export, execute_ring_loft_export
from ontokin.bundle import load_bundle
from ontokin.execution_budget import HostPolicy
from ontokin.holes_agent import HolesAgentService
from ontokin.ring_loft_agent import RingLoftAgentService
from ontokin.ring_loft_protocol import RingLoftProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.scene import ExportOptions
from tests.test_export import DecodedGLB


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/polygon-lofts"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text())
PROTOCOL, PROFILE, TARGET = "ontokin.agent/0.10", "polygon-loft-0.1", "ontokin.glb/0.10"
SHAPE = ["ring-loft-case", "demo", "shape"]
FIRST, SIBLING = ["ring-loft-assembly", "demo", "first"], ["ring-loft-assembly", "demo", "sibling"]
OPTIONS = {"fps": 2, "end": "1", "helpers": False}
EDIT_OLD = "polygon_section(20, 3[m]"
EDIT_NEW = "polygon_section(20, 4[m]"


def source(name="hollow-frustum", *, text=None):
    text = (FIXTURES / (name + ".ok")).read_text() if text is None else text
    modules = []
    if 'from "fixture.ring-loft-parts"' in text:
        modules.append({"package_id": "fixture.ring-loft-parts", "version": "1.0.0",
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


def decoded_volume(decoded, object_path):
    _, node = decoded.source_node(object_path)
    mesh = decoded.document["meshes"][node["mesh"]]
    total, triangles, regions = 0., 0, {}
    for primitive in mesh["primitives"]:
        positions = decoded.accessor(primitive["attributes"]["POSITION"])
        normals = decoded.accessor(primitive["attributes"]["NORMAL"])
        indices = [row[0] for row in decoded.accessor(primitive["indices"])]
        key = primitive["extras"]["ontokin"]["region_key"]
        regions[key] = len(indices) // 3
        for start in range(0, len(indices), 3):
            ia, ib, ic = indices[start:start+3]
            a, b, c = (positions[i] for i in (ia, ib, ic))
            face = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
            assert sum(face[i]*normals[ia][i] for i in range(3)) > 0
            total += sum(a[i]*cross(b, c)[i] for i in range(3)) / 6
            triangles += 1
    return total, triangles, regions


class RingLoftAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        paths = list((ROOT / "docs/language-design/agent-v0.10").glob("*.schema.json"))
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
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c077-agent-")
        self.service = RingLoftAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "ring-lofts",
                "request_id": f"lofts-{self.serial}", "operation": operation, **fields}

    def send(self, operation, **fields):
        request = self.request(operation, **fields)
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

    def create(self, program=None):
        program = source() if program is None else program
        self.success(self.send("create", bundle=program.to_payload(),
            expected_program_revision=None, requested_level="constructed"))
        return program

    def page(self, program, element=SHAPE, **fields):
        fields.setdefault("count", 256)
        result = self.success(self.send("surface.mesh_page", program_revision=program.program_revision,
                                      element_id=element, **fields))
        self.assertEqual(result["result"]["profile"], PROFILE)
        return result

    def export(self, program):
        return self.success(self.send("export", program_revision=program.program_revision,
                                      destination=TARGET, options=OPTIONS))

    def retrieve(self, exported, **fields):
        pieces, offset = [], 0
        for _ in range(200):
            response = self.success(self.send("artifact", artifact_id=exported["result"]["artifact_id"],
                                             offset=offset, max_bytes=256, **fields))
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
            return {"accepted": self.service.accepted_revision("ring-lofts"),
                    "runs": [tuple(row) for row in db.execute("SELECT id,source_revision,descriptor,version FROM runs ORDER BY id")],
                    "artifacts": [tuple(row) for row in db.execute("SELECT id,data,sha256 FROM artifacts ORDER BY id")]}

    def test_discovery_names_sections_limits_schemas_and_separate_store(self):
        response = self.success(self.send("discover", profile=PROFILE, limit=1000))
        result = response["result"]
        self.assertEqual(result["language_version"], "0.10")
        self.assertEqual(result["source_header"], 'ontokin "0.10"; module Example @ "example"; profile "polygon-loft-0.1";')
        names = {item["name"] for item in result["items"]}
        self.assertTrue({"PlanarPoint", "PolygonVertex", "PolygonRing", "PolygonSection", "polygon_ring", "polygon_section", "extrude", "extrude_rings", "loft_rings"} <= names)
        interface = result["polygon_loft_interface"]
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["ring_loft_limits"]["max_total_vertices"], 256)
        self.assertEqual(interface["ring_loft_limits"]["max_sections"], 8)
        self.assertEqual(interface["surface_rule"], "fixed-diagonal-triangles")
        self.assertEqual(self.service.database_path.name, "ring-loft-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.ring-loft-program-agent-store/0.1")
        for key in ("request_schema", "response_schema", "adoption"):
            self.assertTrue((ROOT / interface[key]).is_file())
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)

    def test_discovery_links_source_without_accepting_it(self):
        program = source()
        response = self.success(self.send("discover", profile=PROFILE, limit=1000, bundle=program.to_payload()))
        self.assertEqual(response["result"]["program_context"]["program_revision"], program.program_revision)
        self.assertIsNone(self.service.accepted_revision("ring-lofts"))
        self.assertEqual(response["execution_budget"]["source_request"]["max_operations"], 100000)

    def test_summary_exposes_sections_correspondence_and_material_ownership(self):
        program = self.create()
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "shape"}, fields=["identity", "geometry", "support"], limit=1))
        item = response["result"]["items"][0]
        summary = item["geometry"]["surface"]
        self.assertEqual(summary["schema_version"], "ontokin.polygon-loft-summary/0.1")
        self.assertEqual(summary["family"], "polygon_loft")
        self.assertEqual(summary["surface_rule"], "fixed-diagonal-triangles")
        self.assertEqual((summary["section_count"], summary["ring_count"], summary["hole_count"]), (2, 2, 1))
        self.assertEqual((summary["vertices_per_section"], summary["authored_vertex_count"]), (8, 16))
        self.assertEqual([section["key"] for section in summary["sections"]], ["s0", "s1"])
        self.assertEqual([section["order"] for section in summary["sections"]], [10, 20])
        self.assertEqual(summary["station_range_m"], [0., 3.])
        for section in summary["sections"]:
            self.assertEqual([ring["key"] for ring in section["rings"]], ["outer", "opening"])
            self.assertEqual([ring["order"] for ring in section["rings"]], [20, 40])
            self.assertEqual([ring["role"] for ring in section["rings"]], ["outer", "hole"])
            for ring in section["rings"]:
                self.assertEqual([v["key"] for v in ring["vertices"]], ["v0", "v1", "v2", "v3"])
                self.assertEqual([v["order"] for v in ring["vertices"]], [0, 10, 20, 30])
        self.assertEqual(summary["sections"][1]["rings"][1]["vertices"][0],
            {"key": "v0", "order": 0, "point_m": [-.5, .5], "side_region": "inner"})
        self.assertEqual((summary["cap_triangle_count"], summary["strip_triangle_count"]), (8, 16))
        self.assertEqual((summary["triangle_count"], summary["vertex_count"]), (32, 96))
        self.assertEqual((summary["palette_count"], summary["used_region_count"]), (4, 4))
        self.assertEqual({r["key"]: r["triangle_count"] for r in summary["regions"]},
                         {"bottom": 8, "inner": 8, "outer": 8, "top": 8})
        self.assertEqual(summary["physical_participation"], "none")
        self.assertEqual(item["support"]["named_destination"], TARGET)

    def test_mesh_pages_cover_all_triangles_and_inner_wall_filter(self):
        program = self.create()
        page = self.page(program, count=7)
        ordinals = list(page["result"]["source_triangle_ordinals"])
        while page["next_cursor"]:
            page = self.page(program, count=5, cursor=page["next_cursor"])
            ordinals += page["result"]["source_triangle_ordinals"]
        self.assertEqual(ordinals, list(range(32)))
        inner = self.page(program, region="inner")["result"]
        self.assertEqual(inner["returned_triangles"], 8)
        self.assertEqual(set(inner["region_keys"]), {"inner"})
        self.assertEqual(len(inner["positions_m"]), 24)
        self.failure(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=SHAPE, count=3, budgets={"max_result_items": 2}), "OKL-E-RESOURCE")

    def test_section_ring_and_vertex_declaration_reordering_preserves_mesh(self):
        first = self.create(source("two-holes"))
        before = self.page(first)["result"]
        text = (FIXTURES / "reordered-sections-rings-vertices.ok").read_text()
        result = self.success(self.send("edit", expected_program_revision=first.program_revision,
            requested_level="constructed", patches=[exact_patch(first, first.entry.text, text)]))
        after = source("two-holes", text=text)
        self.assertEqual(result["accepted_program_revision"], after.program_revision)
        current = self.page(after)["result"]
        self.assertNotEqual(first.program_revision, after.program_revision)
        self.assertEqual(geometry(before), geometry(current))
        self.assertEqual(before["geometry_sha256"], current["geometry_sha256"])

    def test_summary_counts_lower_strip_materials_and_unused_terminal_regions(self):
        for name in ("mixed-strip-materials", "terminal-regions-no-strip", "maximum-palette"):
            with self.subTest(case=name):
                program = source(name)
                project_id = "ring-lofts-" + name
                self.success(self.send("create", project_id=project_id, bundle=program.to_payload(),
                    expected_program_revision=None,
                    requested_level="constructed"))
                response = self.success(self.send("inspect", project_id=project_id,
                    program_revision=program.program_revision,
                    selector={"path": "shape"}, fields=["geometry"], limit=1))
                summary = response["result"]["items"][0]["geometry"]["surface"]
                expected = next(case["geometry"] for case in EXPECTED["cases"] if case["id"] == name)
                self.assertEqual({item["key"]: item["triangle_count"] for item in summary["regions"]},
                                 expected["region_triangle_counts"])
                self.assertEqual(summary["palette_count"], len(expected["palette"]))
                self.assertEqual(summary["used_region_count"], len(expected["region_triangle_counts"]))
                self.assertEqual(summary["triangle_count"], expected["triangle_count"])

    def test_valid_endpoint_sections_with_invalid_strips_reject_edits_atomically(self):
        program = self.create(source("constant-solid"))
        self.success(self.send("evaluate", program_revision=program.program_revision,
                               run_id=None, until_seconds="0.5"))
        self.export(program)
        before = self.retained()
        for name in ("strip-diagonal-pinch", "correspondence-edge-pinch", "swapped-hole-collision"):
            with self.subTest(case=name):
                text = (FIXTURES / (name + ".ok")).read_text()
                response = self.failure(self.send("edit", expected_program_revision=program.program_revision,
                    requested_level="delivered", destination=TARGET, options=OPTIONS,
                    patches=[exact_patch(program, program.entry.text, text)]), "OKL-E-RING-LOFT-TOPOLOGY")
                self.assertEqual(self.retained(), before)
                self.assertNotIn("artifact_id", response.get("result") or {})

    def test_changed_correspondence_has_section_diagnostic_and_preserves_acceptance(self):
        program = self.create()
        before = self.retained()
        text = (FIXTURES / "changed-ring-key.ok").read_text()
        response = self.failure(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, program.entry.text, text)]),
            "OKL-E-RING-LOFT-CORRESPONDENCE")
        diagnostic = next(item for item in response["diagnostics"]
                          if item["code"] == "OKL-E-RING-LOFT-CORRESPONDENCE")
        self.assertTrue(diagnostic.get("primary"), diagnostic)
        self.assertTrue(diagnostic.get("details"), diagnostic)
        self.assertEqual(before, self.retained())

    def test_authoritative_quarter_turn_is_the_triangle_defined_box(self):
        program = self.create(source("authoritative-quarter-turn"))
        decoded = DecodedGLB(self.retrieve(self.export(program)))
        volume, triangles, regions = decoded_volume(decoded, "shape")
        self.assertAlmostEqual(volume, 4., places=10)
        self.assertEqual(triangles, 12)
        self.assertEqual(regions, {"bottom": 2, "outer": 8, "top": 2})

    def test_inner_vertex_repair_preserves_sibling_library_and_occurrence(self):
        program = self.create(source("assembly"))
        before_first = self.page(program, FIRST)["result"]
        before_sibling = self.page(program, SIBLING)["result"]
        edit = EXPECTED["assembly"]["repair"]
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, edit["old"], edit["new"])]))
        repaired = source("assembly", text=program.entry.text.replace(edit["old"], edit["new"]))
        self.assertEqual(response["accepted_program_revision"], repaired.program_revision)
        saved = self.service.read_program("ring-lofts", repaired.program_revision)
        self.assertEqual(saved.modules[0].raw, program.modules[0].raw)
        self.assertEqual(geometry(self.page(repaired, SIBLING)["result"]), geometry(before_sibling))
        changed = self.page(repaired, FIRST)["result"]
        self.assertNotEqual(geometry(changed), geometry(before_first))
        self.assertEqual(changed["element_id"], before_first["element_id"])
        decoded = DecodedGLB(self.retrieve(self.export(repaired)))
        self.assertAlmostEqual(decoded_volume(decoded, "first")[0], 21.375, places=10)
        self.assertAlmostEqual(decoded_volume(decoded, "sibling")[0], 21., places=10)

    def test_touching_hole_edit_rolls_back_source_run_and_artifact(self):
        program = self.create(source("assembly"))
        self.success(self.send("evaluate", program_revision=program.program_revision, run_id=None, until_seconds="0.5"))
        self.export(program)
        before = self.retained()
        edit = EXPECTED["assembly"]["invalid_edit"]
        response = self.failure(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="delivered", destination=TARGET, options=OPTIONS,
            patches=[exact_patch(program, edit["old"], edit["new"])]), edit["diagnostic_code"])
        self.assertEqual(before, self.retained())
        self.assertNotEqual(response["achieved_level"], "delivered")
        self.assertNotIn("artifact_id", response.get("result") or {})

    def test_stale_file_preconditions_and_nominal_identity_reject_atomically(self):
        program = self.create()
        edit = exact_patch(program, EDIT_OLD, EDIT_NEW)
        before = self.retained()
        for modified in ({**edit, "expected_text": "wrong"},
                         {**edit, "source_revision": "sha256:" + "0"*64},
                         {**edit, "element_id": SHAPE}):
            self.failure(self.send("edit", expected_program_revision=program.program_revision,
                requested_level="constructed", patches=[modified]))
            self.assertEqual(before, self.retained())
        self.failure(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program,
                'class Shape @ "shape"', 'class Shape @ "different"')]), "OKL-E-ID")
        self.assertEqual(before, self.retained())

    def test_cursor_cannot_change_revision_or_region(self):
        program = self.create()
        paged = self.page(program, count=2)
        self.failure(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=SHAPE, count=2, cursor=paged["next_cursor"], region="inner"))
        self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, EDIT_OLD, EDIT_NEW)]))
        revised = source(text=program.entry.text.replace(EDIT_OLD, EDIT_NEW))
        self.failure(self.send("surface.mesh_page", program_revision=revised.program_revision,
            element_id=SHAPE, count=2, cursor=paged["next_cursor"]))

    def test_export_retrieval_preserves_analytic_volume_regions_and_motion(self):
        program = self.create()
        exported = self.export(program)
        decoded = DecodedGLB(self.retrieve(exported))
        volume, triangles, regions = decoded_volume(decoded, "shape")
        self.assertAlmostEqual(volume, 21., places=10)
        self.assertEqual(triangles, 32)
        self.assertEqual(regions, {"bottom": 8, "inner": 8, "outer": 8, "top": 8})
        for when in (0., .25, .5, .75, 1.):
            translation = decoded.node_pose("shape", when)["translation"]
            self.assertAlmostEqual(translation[0], 0., places=7)
            self.assertAlmostEqual(translation[1], when*.5, places=7)
            self.assertAlmostEqual(translation[2], 0., places=7)
        self.assertEqual(exported["result"]["destination"], TARGET)
        self.assertGreater(exported["execution_budget"]["consumed_operations"],
            exported["result"]["report"]["execution_budget_at_export"]["consumed_operations"])

    def test_binary32_touching_opening_never_publishes_an_artifact(self):
        program = self.create(source("binary32-boundary-clearance"))
        before = self.retained()
        response = self.failure(self.send("export", program_revision=program.program_revision,
                                          destination=TARGET, options=OPTIONS))
        after = self.retained()
        self.assertEqual(after["accepted"], before["accepted"])
        self.assertEqual(after["artifacts"], before["artifacts"])
        self.assertNotEqual(response["achieved_level"], "delivered")
        self.assertNotIn("artifact_id", response.get("result") or {})
        self.assertEqual(len(after["runs"]), 1)
        descriptor = json.loads(after["runs"][0][2])
        self.assertEqual(descriptor["program_revision"], program.program_revision)
        self.assertEqual(descriptor["valid_until_seconds"], "1")

    def test_durable_retry_returns_original_receipt_and_rejects_changed_payload(self):
        program = self.create()
        request = self.request("export", program_revision=program.program_revision,
                               destination=TARGET, options=OPTIONS)
        response = self.success(self.service.handle(request))
        before = self.retained()
        with patch.object(self.service, "_execute", side_effect=AssertionError("replayed")):
            self.assertEqual(self.service.handle(copy.deepcopy(request)), response)
        changed = copy.deepcopy(request)
        changed["options"]["fps"] = 3
        self.failure(self.service.handle(changed), "OKL-E-REQUEST-ID")
        self.assertEqual(before, self.retained())

    def test_saved_artifact_and_run_reauthorize_current_host_policy(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        text = source().entry.text.replace('profile "polygon-loft-0.1";',
            'profile "polygon-loft-0.1";\nexecution { max_operations = 200000; max_elapsed = 60[s]; }')
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

    def test_omitted_limits_remain_defaults_and_caller_caps_only_reduce(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        program = self.create()
        response = self.success(self.send("validate", program_revision=program.program_revision,
                                          requested_level="constructed"))
        self.assertEqual(response["execution_budget"]["effective"],
                         {"max_operations": 100000, "max_elapsed_ms": 30000})
        bad = self.failure(self.send("validate", program_revision=program.program_revision,
            requested_level="constructed", budgets={"max_operations": 100001}), "OKL-E-RESOURCE")
        self.assertEqual(bad["execution_budget"]["budget_reason"], "request_cap_exceeds_source")

    def test_budget_exhaustion_and_late_publication_failure_are_atomic(self):
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

    def test_reset_status_and_queued_cancellation_execute(self):
        program = self.create()
        self.success(self.send("reset", program_revision=program.program_revision))
        request = self.request("validate", program_revision=program.program_revision, requested_level="evaluated")
        queued = self.service.handle(request, wait=False)
        self.validators["response.schema.json"].validate(queued)
        self.success(self.send("cancel", target_request_id=request["request_id"]))
        status = self.success(self.send("status", target_request_id=request["request_id"]))
        self.assertEqual(status["result"]["target_status"], "cancelled")

    def test_older_binding_and_destination_are_rejected_without_registry_changes(self):
        with self.assertRaises(ProtocolError):
            RingLoftAgentService(self.directory.name, protocol="ontokin.agent/0.9")
        request = self.request("discover", profile=PROFILE, limit=10)
        request["schema_version"] = "ontokin.agent/0.9"
        self.failure(self.service.handle(request), "OKA-E-REQUEST")
        program = self.create()
        self.failure(self.send("export", program_revision=program.program_revision,
            destination="ontokin.glb/0.9", options=OPTIONS), "OKA-E-REQUEST")
        old = source(text=source().entry.text.replace('"0.10"', '"0.9"', 1)
                     .replace(PROFILE, 'polygon-holes-0.1', 1))
        self.failure(self.send("create", bundle=old.to_payload(),
            expected_program_revision=program.program_revision, requested_level="constructed"))

    def test_inherited_loft_keeps_summary_and_explicit_mesh_profile(self):
        from tests.test_surface_export import single_source
        text = single_source().replace('"0.3"', '"0.10"', 1).replace('surface-0.1', PROFILE, 1)
        program = self.create(source(text=text))
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "shell"}, fields=["identity", "geometry"], limit=1))
        item = response["result"]["items"][0]
        self.assertEqual(item["geometry"]["surface"]["schema_version"], "ontokin.surface-summary/0.1")
        self.page(program, item["element_id"])

    def test_inherited_simple_extrusion_keeps_its_summary_meaning(self):
        text = (ROOT / "examples/polygon-extrusions/rectangle.ok").read_text()
        text = text.replace('"0.8"', '"0.10"', 1).replace('polygon-extrusion-0.1', PROFILE, 1)
        program = self.create(source(text=text))
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "shape"}, fields=["identity", "geometry"], limit=1))
        item = response["result"]["items"][0]
        summary = item["geometry"]["surface"]
        self.assertEqual(summary["schema_version"], "ontokin.polygon-extrusion-summary/0.1")
        self.assertEqual(summary["profile"], "polygon-extrusion-0.1")
        self.assertEqual(summary["triangle_count"], 12)
        self.page(program, item["element_id"])
        self.assertAlmostEqual(decoded_volume(DecodedGLB(self.retrieve(self.export(program))), "shape")[0], 1.)

    def test_inherited_holes_and_pinned_09_library_keep_their_summary_meaning(self):
        from tests.test_holes_agent import source as old_source
        inherited = old_source("assembly")
        payload = inherited.to_payload()
        payload["entry"]["source"] = inherited.entry.text.replace('"0.9"', '"0.10"', 1).replace(
            "polygon-holes-0.1", PROFILE, 1)
        program = self.create(load_bundle(payload))
        self.assertEqual(program.modules[0].raw, inherited.modules[0].raw)
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "first"}, fields=["identity", "geometry"], limit=1))
        item = response["result"]["items"][0]
        summary = item["geometry"]["surface"]
        self.assertEqual(summary["schema_version"], "ontokin.polygon-holes-summary/0.1")
        self.assertEqual(summary["profile"], "polygon-holes-0.1")
        self.assertEqual(summary["triangle_count"], 32)
        self.page(program, item["element_id"])
        self.assertAlmostEqual(decoded_volume(DecodedGLB(self.retrieve(self.export(program))), "first")[0], 6.)

    def test_direct_export_and_cli_require_explicit_010_binding(self):
        program = source()
        direct = execute_ring_loft_export(program, options=ExportOptions(fps=2, end="1", helpers=False))
        self.assertIsNotNone(direct.data, direct.report)
        self.assertEqual(direct.report["target_contract"], TARGET)
        self.assertEqual(direct.report["language_version"], "0.10")
        self.assertIsNone(execute_holes_export(program).data)
        output = Path(self.directory.name) / "loft.glb"
        result = subprocess.run([sys.executable, "-m", "ontokin", "export", str(FIXTURES / "hollow-frustum.ok"),
            "--target", TARGET, "--output", str(output), "--fps", "2", "--end", "1", "--no-helpers"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        volume, triangles, _ = decoded_volume(DecodedGLB(output.read_bytes()), "shape")
        self.assertAlmostEqual(volume, 21., places=10)
        self.assertEqual(triangles, 32)

    def test_cli_agent_discovery_and_host_policy_injection_refusal(self):
        request = self.request("discover", profile=PROFILE, limit=1000)
        path = Path(self.directory.name) / "request.json"
        path.write_text(json.dumps(request))
        result = subprocess.run([sys.executable, "-m", "ontokin", "agent", "--protocol", PROTOCOL,
            "--store", str(Path(self.directory.name) / "cli"), "--request", str(path), "--wait"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"]["language_version"], "0.10")
        request = self.request("discover", profile=PROFILE, limit=10, host_policy={"max_operations": 400000})
        self.failure(self.service.handle(request), "OKA-E-REQUEST")

    def test_previous_service_has_separate_acceptance_in_same_directory(self):
        from tests.test_holes_agent import source as old_source
        program = self.create()
        with HolesAgentService(self.directory.name) as old:
            self.assertIsNone(old.accepted_revision("ring-lofts"))
            old_program = old_source()
            response = old.handle({"schema_version": "ontokin.agent/0.9", "project_id": "ring-lofts",
                "request_id": "rings-1", "operation": "create", "bundle": old_program.to_payload(),
                "expected_program_revision": None, "requested_level": "constructed"})
            self.assertEqual(response["status"], "succeeded", response)
            self.assertEqual(old.accepted_revision("ring-lofts"), old_program.program_revision)
            self.assertNotEqual(old.database_path, self.service.database_path)
        self.assertEqual(self.service.accepted_revision("ring-lofts"), program.program_revision)

    def test_host_cancellation_inside_ring_construction_preserves_identity_and_receipt(self):
        from ontokin import ring_loft
        from ontokin.diagnostics import OntoKinError
        marker = OntoKinError("OKL-E-RING-LOFT-NUMERIC", "trusted caller interrupt")
        state = {"armed": False, "calls": 0}
        def check():
            state["calls"] += 1
            if state["armed"]:
                raise marker
        self.service._host_check = check
        original = ring_loft.triangulate_ring_loft
        def arm(*args, **kwargs):
            state["armed"] = True
            return original(*args, **kwargs)
        request = self.request("create", bundle=source().to_payload(), expected_program_revision=None,
                               requested_level="constructed")
        with patch.object(ring_loft, "triangulate_ring_loft", side_effect=arm):
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

    def test_budget_reducing_ring_repair_uses_candidate_authority(self):
        self.service.host_policy = HostPolicy(400000, 80000)
        text = source().entry.text.replace('profile "polygon-loft-0.1";',
            'profile "polygon-loft-0.1";\nexecution { max_operations = 200000; max_elapsed = 60[s]; }')
        program = self.create(source(text=text))
        self.service.host_policy = HostPolicy()
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, "200000", "100000"),
                                                     exact_patch(program, "60[s]", "30[s]")]))
        repaired = source(text=text.replace("200000", "100000").replace("60[s]", "30[s]"))
        self.assertEqual(response["accepted_program_revision"], repaired.program_revision)
        self.assertEqual(response["execution_budget"]["source_request"],
                         {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(self.page(repaired)["result"]["total_triangles"], 32)

    def test_response_schema_rejects_malformed_section_summary(self):
        from jsonschema import ValidationError
        program = self.create()
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "shape"}, fields=["geometry"], limit=1))
        for change in ("role", "point", "count", "region", "station", "section_count", "rule"):
            bad = copy.deepcopy(response)
            summary = bad["result"]["items"][0]["geometry"]["surface"]
            ring = summary["sections"][0]["rings"][0]
            if change == "role":
                ring["role"] = "island"
            elif change == "point":
                ring["vertices"][0]["point_m"] = [0, 0, 0]
            elif change == "count":
                summary["authored_vertex_count"] = 257
            elif change == "region":
                ring["vertices"][0].pop("side_region")
            elif change == "station":
                summary["sections"][0]["station_m"] = -1
            elif change == "section_count":
                summary["section_count"] = 9
            else:
                summary["surface_rule"] = "linear-polygon-slices"
            with self.assertRaises(ValidationError):
                self.validators["response.schema.json"].validate(bad)

    def test_all_twelve_operations_execute_with_published_wire_shapes(self):
        operations = set()
        def perform(operation, *, queued=False, **fields):
            request = self.request(operation, **fields)
            self.validators["request.schema.json"].validate(request)
            RingLoftProtocol.validate_request(request)
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
        perform("create", bundle=program.to_payload(), expected_program_revision=None,
                requested_level="constructed")
        perform("validate", program_revision=program.program_revision, requested_level="constructed")
        perform("edit", expected_program_revision=program.program_revision, requested_level="constructed",
                patches=[exact_patch(program, EDIT_OLD, EDIT_NEW)])
        program = source(text=program.entry.text.replace(EDIT_OLD, EDIT_NEW))
        perform("inspect", program_revision=program.program_revision, selector={"path": "shape"},
                fields=["identity", "geometry", "support"], limit=1)
        perform("surface.mesh_page", program_revision=program.program_revision,
                element_id=SHAPE, region="inner", count=4)
        perform("evaluate", program_revision=program.program_revision, run_id=None, until_seconds="1")
        exported_request, exported = perform("export", program_revision=program.program_revision,
                                              destination=TARGET, options=OPTIONS)
        perform("artifact", artifact_id=exported["result"]["artifact_id"], offset=0, max_bytes=1024)
        perform("status", target_request_id=exported_request["request_id"])
        perform("reset", program_revision=program.program_revision)
        pending, _ = perform("validate", queued=True, program_revision=program.program_revision,
                             requested_level="evaluated")
        perform("cancel", target_request_id=pending["request_id"])
        self.assertEqual(operations, set(RingLoftProtocol.OPERATIONS))
