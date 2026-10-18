"""Actual Agent/0.3 source repair, bounded mesh reads and durable effects.

The frozen source bundle supplies every surface. Mesh checks use independent
vector arithmetic and decoded glTF accessors, never the production mesh reader.
These are Agent/0.3 workflow checks, not the complete M01--M12 release evidence.
"""

from contextlib import contextmanager
import base64
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch as instrument

from ontokin.agent_protocol import ProtocolError
from ontokin.bundle import ProgramBundle, SourceUnit, load_bundle
from ontokin.program_agent import ProgramAgentService
from ontokin.json_limits import measure_json
from tests.test_construction import RELEASE_SOURCE
from tests.test_export import DecodedGLB
from tests.test_surface_export import (DEFAULT_PALETTE, DEFAULT_SECTIONS, cross,
                                     mesh_content, single_source, surface_members)
from tests.test_surface_source import bundle as studio_bundle


PROTOCOL = "ontokin.agent/0.3"
DESTINATION = "ontokin.glb/0.3"
PROJECT = "native-surface-agent"
FIRST = ["surface-studio", "studio", "first"]
SECOND = ["surface-studio", "studio", "second"]
PALETTE_OVERRIDE = '''
        palette = keyed<SurfaceMaterial> {
            "clay": surface_material(rgba(0.6, 0.3, 0.2, 1), 0, 0.8),
            "paint": surface_material(rgba(0.8, 0.15, 0.05, 0.75), 0.7, 0.25)
        };
    '''


def source_program(text):
    return ProgramBundle(SourceUnit("entry", "native-agent.ok", text.encode("utf-8")))


def geometry_payload(page):
    return {name: page[name] for name in
            ("positions_m", "normals", "triangles", "source_triangle_ordinals", "region_keys")}


class _FinishGate(ProgramAgentService):
    """Pause after real native computation, immediately before its transaction."""

    def __init__(self, directory):
        self.ready = threading.Event()
        self.release = threading.Event()
        self.prepared = None
        self.errors = []
        super().__init__(directory, protocol=PROTOCOL)

    def _finish(self, task):
        self.prepared = {"response": copy.deepcopy(task.response),
                         "run": copy.deepcopy(task.run), "accept": task.accept,
                         "artifact": task.artifact,
                         "program": None if task.source is None else task.source.to_payload()}
        self.ready.set()
        if not self.release.wait(10):
            raise TimeoutError("The native surface test did not release the transaction")
        super()._finish(task)

    def work(self):
        try:
            if not self.work_next():
                raise AssertionError("No native surface request was claimed")
        except BaseException as error:
            self.errors.append(error)
            self.ready.set()


class SurfaceAgentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-surface-agent-")
        self.path = Path(self.temporary.name)
        self.service = ProgramAgentService(self.path, protocol=PROTOCOL)
        self.original = studio_bundle()
        self.sequence = 0

    def tearDown(self):
        self.service.close()
        self.temporary.cleanup()

    def request(self, operation, **fields):
        self.sequence += 1
        return {"schema_version": PROTOCOL, "project_id": PROJECT,
                "request_id": f"surface-{self.sequence}", "operation": operation, **fields}

    def send(self, operation, **fields):
        response = self.service.handle(self.request(operation, **fields))
        self.assertEqual(response["operation"], operation, response)
        return response

    def assert_success(self, response):
        self.assertEqual(response["schema_version"], PROTOCOL, response)
        self.assertEqual(response["status"], "succeeded", response)
        self.assertIsNone(response["protocol_error"], response)
        self.assertNotIn("source_revision", response)
        self.assertNotIn("accepted_revision", response)

    def assert_code(self, response, code):
        self.assertIn(response["status"], ("rejected", "failed"), response)
        codes = [diagnostic["code"] for diagnostic in response["diagnostics"]]
        if response["protocol_error"]:
            codes.append(response["protocol_error"]["code"])
        self.assertIn(code, codes, response)

    def create(self, program=None, level="represented", **fields):
        program = self.original if program is None else program
        response = self.send("create", bundle=program.to_payload(),
                             expected_program_revision=None, requested_level=level, **fields)
        self.assert_success(response)
        self.assertEqual(response["program_revision"], program.program_revision)
        self.assertEqual(response["accepted_program_revision"], program.program_revision)
        return response

    def inspect(self, revision, path, fields=None, **extra):
        response = self.send("inspect", program_revision=revision, selector={"path": path},
                             fields=fields or ["identity", "source", "geometry", "support"], limit=1, **extra)
        self.assert_success(response)
        self.assertEqual(response["result"]["total"], 1)
        return response["result"]["items"][0]

    def page(self, revision, element_id=FIRST, count=256, **fields):
        response = self.send("surface.mesh_page", program_revision=revision,
                             element_id=element_id, count=count, **fields)
        self.assert_success(response)
        page = response["result"]
        self.assertEqual(page["schema_version"], "ontokin.surface-mesh-page/0.1")
        self.assertEqual(page["program_revision"], revision)
        self.assertEqual(page["element_id"], element_id)
        self.assertEqual(page["profile"], "surface-0.1")
        self.assertEqual(page["coordinate_system"], "carrier_local_after_placement/0.1")
        self.assertEqual(page["ordering"], "native_triangle_ordinal/0.1")
        self.assertRegex(page["geometry_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(page["implementation"], self.service.implementation)
        self.assertIsNone(response["requested_level"])
        self.assertEqual(response["achieved_level"], "constructed")
        self.assertIsNone(response["run_id"])
        size = page["returned_triangles"]
        self.assertLessEqual(size, count)
        self.assertEqual(len(page["positions_m"]), 3 * size)
        self.assertEqual(len(page["normals"]), 3 * size)
        self.assertEqual(page["triangles"], [[3*i, 3*i+1, 3*i+2] for i in range(size)])
        self.assertEqual(len(page["source_triangle_ordinals"]), size)
        self.assertEqual(page["source_triangle_ordinals"], sorted(set(page["source_triangle_ordinals"])))
        self.assertEqual(len(page["region_keys"]), size)
        self.assertEqual(response["truncated"], response["next_cursor"] is not None)
        return response

    def collect(self, revision, element_id=FIRST, counts=(7, 1, 256), **fields):
        cursor = None
        result = {name: [] for name in ("positions_m", "normals", "source_triangle_ordinals", "region_keys")}
        offset = 0
        pages = []
        while True:
            response = self.page(revision, element_id, counts[len(pages) % len(counts)], cursor=cursor, **fields)
            page = response["result"]
            self.assertEqual(page["offset"], offset)
            if pages:
                for name in ("geometry_sha256", "total_triangles", "filtered_triangles"):
                    self.assertEqual(page[name], pages[0][name])
            pages.append(page)
            for name in result:
                result[name].extend(page[name])
            offset += page["returned_triangles"]
            cursor = response["next_cursor"]
            if cursor is None:
                break
            self.assertGreater(page["returned_triangles"], 0)
            self.assertLess(len(pages), 100, "Mesh pagination failed to terminate")
        self.assertEqual(offset, pages[0]["filtered_triangles"])
        return result, pages

    def source_patch(self, program, old, new, *, element_id=SECOND, source_id="entry"):
        source = program.sources[source_id]
        start = source.raw.index(old.encode("utf-8"))
        return {"source_id": source_id, "source_revision": source.revision,
                "element_id": element_id, "start_byte": start,
                "end_byte": start + len(old.encode("utf-8")),
                "expected_text": old, "replacement": new}

    def palette_patch(self, program, replacement=PALETTE_OVERRIDE):
        item = self.inspect(program.program_revision, "second.palette", ["source"])
        target = item["source"]["initializer_target"]
        self.assertTrue(target["available"])
        self.assertEqual(target["element_id"], SECOND)
        self.assertEqual(target["rendered_path"], "palette")
        self.assertIsNone(target["assignment_span"])
        span = target["span"]
        position = span["end_byte"] - 1
        self.assertEqual(program.entry.raw[position:position+1], b"}")
        return {"source_id": "entry", "source_revision": program.entry.revision,
                "element_id": SECOND, "start_byte": position, "end_byte": position,
                "expected_text": "", "replacement": replacement}

    def expected_candidate(self, program, patches):
        payload = program.to_payload()
        raw = program.entry.raw
        for patch in sorted(patches, key=lambda item: item["start_byte"], reverse=True):
            self.assertEqual(patch["source_id"], "entry")
            raw = raw[:patch["start_byte"]] + patch["replacement"].encode("utf-8") + raw[patch["end_byte"]:]
        payload["entry"]["source"] = raw.decode("utf-8")
        return load_bundle(payload)

    def effect_counts(self):
        with self.service._store.connection() as db:
            return {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                    for table in ("runs", "artifacts")}

    def artifact(self, exported, accepted):
        data = bytearray()
        offset = 0
        while offset is not None:
            response = self.send("artifact", artifact_id=exported["result"]["artifact_id"], offset=offset, max_bytes=4096)
            self.assert_success(response)
            self.assertEqual(response["program_revision"], exported["program_revision"])
            self.assertEqual(response["accepted_program_revision"], accepted)
            part = response["result"]
            self.assertEqual(part["offset"], len(data))
            self.assertEqual(part["artifact_provenance"]["program_revision"], exported["program_revision"])
            data.extend(base64.b64decode(part["data_base64"], validate=True))
            offset = part["next_offset"]
        self.assertEqual("sha256:" + hashlib.sha256(data).hexdigest(), exported["result"]["sha256"])
        decoded = DecodedGLB(bytes(data))
        self.assertEqual(decoded.document["extras"]["ontokin"]["program"]["revision"], exported["program_revision"])
        return decoded

    def assert_page_export(self, page, decoded, path):
        """Compare independent destination accessors with complete binary64 pages."""
        groups = mesh_content(decoded, path)
        self.assertEqual(set(groups), set(page["region_keys"]))
        for key, group in groups.items():
            ordinals = [index for index, region in enumerate(page["region_keys"]) if region == key]
            self.assertEqual(len(group["faces"]), len(ordinals))
            for (positions, normals), ordinal in zip(group["faces"], ordinals):
                for actual, expected in zip(positions, page["positions_m"][3*ordinal:3*ordinal+3]):
                    for coordinate, source in zip(actual, expected):
                        self.assertAlmostEqual(coordinate, source, delta=1e-5)
                for actual, expected in zip(normals, page["normals"][3*ordinal:3*ordinal+3]):
                    for coordinate, source in zip(actual, expected):
                        self.assertAlmostEqual(coordinate, source, delta=1e-6)

    @contextmanager
    def prepared(self, requests):
        workers = [_FinishGate(self.path) for _ in requests]
        threads = []
        try:
            for request in requests:
                self.assertEqual(self.service.submit(request)["status"], "queued")
            for worker in workers:
                thread = threading.Thread(target=worker.work, daemon=True)
                threads.append(thread)
                thread.start()
                self.assertTrue(worker.ready.wait(10), "Native computation did not reach its commit boundary")
                self.assertEqual(worker.errors, [])
                self.assert_success(worker.prepared["response"])
            yield workers, threads
        finally:
            for worker in workers:
                worker.release.set()
            for thread in threads:
                thread.join(10)
            for worker in workers:
                worker.close()

    def release(self, worker, thread):
        worker.release.set()
        thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(worker.errors, [])

    def test_frozen_source_identity_and_bounded_json_safe_surface_summary(self):
        revision = self.create()["program_revision"]
        item = self.inspect(revision, "first")
        self.assertEqual(item["element_id"], FIRST)
        self.assertEqual(item["source"]["program_revision"], revision)
        self.assertEqual(item["source"]["source_revision"], self.original.entry.revision)
        self.assertEqual(item["source"]["definition_span"]["source_revision"], self.original.modules[0].revision)
        self.assertEqual(item["support"]["profile"], "surface-0.1")
        self.assertEqual(item["support"]["named_destination"], DESTINATION)
        geometry = item["geometry"]
        summary = geometry["surface"]
        self.assertEqual(summary["schema_version"], "ontokin.surface-summary/0.1")
        self.assertEqual(summary["profile"], "surface-0.1")
        self.assertEqual(summary["section_keys"], ["foot", "neck", "tip"])
        self.assertEqual(summary["stations_m"], [0, 1, 1.5])
        self.assertEqual(summary["palette_keys"], ["clay", "paint"])
        self.assertEqual((summary["facets"], summary["caps"], summary["triangle_count"], summary["vertex_count"]), (16, "flat", 96, 288))
        self.assertEqual(summary["regions"], [{"key": key, "material_key": key, "triangle_count": 48}
                                              for key in ("clay", "paint")])
        self.assertEqual(summary["local_visual_placement"], {"frame": "carrier_self_frame",
                         "position_m": [0, 0, .1], "orientation_wxyz": [1, 0, 0, 0]})
        self.assertEqual(summary["physical_participation"], "none")
        self.assertEqual(summary["motion_authority"], "carrier_evaluated_world_pose")
        encoded = json.dumps(geometry, allow_nan=False)
        for derived in ('"positions_m"', '"normals"', '"triangles"', '"indices"'):
            self.assertNotIn(derived, encoded)
        self.assertLess(len(encoded), 15000)
        self.assertEqual(self.service.read_program(PROJECT, revision).to_payload(), self.original.to_payload())
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})

    def test_mesh_pages_are_complete_triangles_in_native_order_and_local_coordinates(self):
        revision = self.create()["program_revision"]
        full, pages = self.collect(revision)
        self.assertEqual([page["returned_triangles"] for page in pages], [7, 1, 88])
        self.assertEqual(full["source_triangle_ordinals"], list(range(96)))
        self.assertEqual(full["region_keys"], ["clay"]*32 + ["paint"]*32 + ["clay"]*16 + ["paint"]*16)
        self.assertEqual(len(full["positions_m"]), 288)
        expected_first = [(0.5, 0, .1), (.5*math.cos(math.pi/8), .35*math.sin(math.pi/8), .1), (.45, 0, 1.1)]
        for actual, expected in zip(full["positions_m"][:3], expected_first):
            for value, target in zip(actual, expected):
                self.assertAlmostEqual(value, target, delta=1e-10)
        for index in range(96):
            a, b, c = full["positions_m"][index*3:index*3+3]
            face_normal = cross([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])
            magnitude = math.sqrt(sum(value*value for value in face_normal))
            self.assertGreater(magnitude, 0)
            for normal in full["normals"][index*3:index*3+3]:
                self.assertAlmostEqual(sum(value*value for value in normal), 1, delta=1e-12)
                for actual, expected in zip(normal, face_normal):
                    self.assertAlmostEqual(actual, expected/magnitude, delta=1e-12)
            if index < 64:
                mean = [sum(point[k] for point in (a, b, c))/3 for k in range(3)]
                center_x = .15*(mean[2]-.1) if index < 32 else .15
                self.assertGreater(face_normal[0]*(mean[0]-center_x) + face_normal[1]*mean[1], 0)
            if index >= 64:
                self.assertEqual(full["normals"][index*3], [0, 0, -1 if index < 80 else 1])
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})

    def test_region_filter_preserves_disjoint_source_ordinals(self):
        revision = self.create()["program_revision"]
        full, _ = self.collect(revision)
        for region, expected in (("clay", list(range(32)) + list(range(64, 80))),
                                 ("paint", list(range(32, 64)) + list(range(80, 96)))):
            with self.subTest(region=region):
                filtered, pages = self.collect(revision, counts=(1, 19, 256), region=region)
                self.assertEqual(filtered["source_triangle_ordinals"], expected)
                self.assertEqual(pages[0]["total_triangles"], 96)
                self.assertEqual(pages[0]["filtered_triangles"], 48)
                self.assertEqual(filtered["region_keys"], [region]*48)
                self.assertEqual(filtered["positions_m"], [point for ordinal in expected for point in full["positions_m"][3*ordinal:3*ordinal+3]])

    def test_unused_region_is_empty_and_unknown_region_or_non_occurrence_rejects(self):
        palette = {**DEFAULT_PALETTE, "unused": {"rgba": [1, 1, 0, 1], "metallic": 0, "roughness": .6}}
        program = source_program(single_source(palette=palette))
        revision = self.create(program)["program_revision"]
        identity = ["native-export", "demo", "shell"]
        response = self.page(revision, identity, 1, region="unused")
        page = response["result"]
        self.assertEqual((page["total_triangles"], page["filtered_triangles"], page["returned_triangles"]), (64, 0, 0))
        self.assertFalse(response["truncated"])
        self.assertIn("unused", self.inspect(revision, "shell")["geometry"]["surface"]["palette_keys"])
        missing = self.send("surface.mesh_page", program_revision=revision, element_id=identity, count=1, region="unknown")
        self.assert_code(missing, "OKL-E-SURFACE-REGION")
        for target in (identity + ["rings"], ["sources", "entry"], ["native-export", "demo", "missing"]):
            response = self.send("surface.mesh_page", program_revision=revision, element_id=target, count=1)
            self.assert_code(response, "OKL-E-REVISION")

    def test_cursor_binds_exact_revision_project_occurrence_filter_and_signature(self):
        revision = self.create()["program_revision"]
        first = self.page(revision, count=1)
        cursor = first["next_cursor"]
        patches = [self.source_patch(self.original, "0.48[m]", "0.52[m]")]
        edited = self.send("edit", expected_program_revision=revision, patches=patches, requested_level="represented")
        self.assert_success(edited)
        current = edited["program_revision"]
        for fields in ({"program_revision": current}, {"element_id": SECOND}, {"region": "paint"},
                       {"cursor": ("A" if cursor[0] != "A" else "B") + cursor[1:]}):
            with self.subTest(fields=fields):
                request = dict(program_revision=revision, element_id=FIRST, count=19, cursor=cursor)
                request.update(fields)
                self.assert_code(self.send("surface.mesh_page", **request), "OKL-E-REVISION")
        other = self.request("create", bundle=self.original.to_payload(), expected_program_revision=None, requested_level="represented")
        other["project_id"] = "other-surface-project"
        self.assert_success(self.service.handle(other))
        cross_project = self.request("surface.mesh_page", program_revision=revision, element_id=FIRST, count=1, cursor=cursor)
        cross_project["project_id"] = other["project_id"]
        self.assert_code(self.service.handle(cross_project), "OKL-E-REVISION")
        # An immutable snapshot that was accepted remains readable after repair.
        old = self.page(revision, count=19, cursor=cursor)
        self.assertEqual(old["result"]["source_triangle_ordinals"], list(range(1, 20)))
        self.assertEqual(old["accepted_program_revision"], current)

    def test_comment_only_revision_invalidates_cursor_without_mutating_geometry(self):
        revision = self.create()["program_revision"]
        before = self.page(revision, count=7)
        patch = self.source_patch(self.original, 'duration = 2[s];', '// café 😀\n    duration = 2[s];',
                                  element_id=["sources", "entry"])
        edited = self.send("edit", expected_program_revision=revision, patches=[patch], requested_level="represented")
        self.assert_success(edited)
        current = edited["program_revision"]
        self.assertNotEqual(current, revision)
        after = self.page(current, count=7)
        self.assertEqual(geometry_payload(before["result"]), geometry_payload(after["result"]))
        stale = self.send("surface.mesh_page", program_revision=current, element_id=FIRST, count=7, cursor=before["next_cursor"])
        self.assert_code(stale, "OKL-E-REVISION")

    def test_invalid_candidate_then_atomic_section_and_material_repair_preserves_sibling(self):
        revision = self.create(level="evaluated")["program_revision"]
        first = self.page(revision)["result"]
        second = self.page(revision, SECOND)["result"]
        old_export = self.send("export", program_revision=revision, destination=DESTINATION, options={"helpers": False})
        self.assert_success(old_export)
        invalid = [self.source_patch(self.original, "0.48[m]", "0.52[m]"),
                   self.palette_patch(self.original, PALETTE_OVERRIDE.replace("0.7, 0.25", "1.1, 0.25"))]
        expected_invalid = self.expected_candidate(self.original, invalid)
        bad = self.send("edit", expected_program_revision=revision, patches=invalid, requested_level="evaluated")
        self.assert_code(bad, "OKL-E-SURFACE-MATERIAL")
        self.assertEqual(bad["program_revision"], expected_invalid.program_revision)
        self.assertEqual(bad["accepted_program_revision"], revision)
        self.assertEqual(self.service.read_program(PROJECT, bad["program_revision"]).to_payload(), expected_invalid.to_payload())
        diagnostic = next(item for item in bad["diagnostics"] if item["code"] == "OKL-E-SURFACE-MATERIAL")
        self.assertEqual(diagnostic["schema_version"], "ontokin.diagnostic/0.2")
        self.assertEqual(diagnostic["program_revision"], expected_invalid.program_revision)
        self.assertEqual(diagnostic["source_revision"], expected_invalid.entry.revision)
        self.assertEqual(diagnostic["primary"]["source_id"], "entry")
        source_only = self.send("inspect", program_revision=bad["program_revision"],
                                selector={"kind": "source", "source_id": "entry"},
                                fields=["source", "state"], limit=1)
        self.assert_success(source_only)
        self.assertFalse(source_only["result"]["index_complete"])
        self.assertFalse(source_only["result"]["items"][0]["state"]["available"])
        self.assertEqual(source_only["result"]["items"][0]["source"]["source_revision"], expected_invalid.entry.revision)
        for operation, fields in (("surface.mesh_page", {"element_id": SECOND, "count": 1}),
                                  ("evaluate", {"run_id": None, "until_seconds": "1"}),
                                  ("export", {"destination": DESTINATION})):
            self.assert_code(self.send(operation, program_revision=bad["program_revision"], **fields), "OKL-E-REVISION")
        repaired_patches = [self.source_patch(self.original, "0.48[m]", "0.52[m]"), self.palette_patch(self.original)]
        expected = self.expected_candidate(self.original, repaired_patches)
        repaired = self.send("edit", expected_program_revision=revision, patches=repaired_patches,
                             requested_level="delivered", destination=DESTINATION, options={"helpers": False})
        self.assert_success(repaired)
        self.assertEqual(repaired["achieved_level"], "delivered")
        self.assertEqual(repaired["program_revision"], expected.program_revision)
        current = repaired["program_revision"]
        self.assertEqual(self.service.read_program(PROJECT, current).to_payload(), expected.to_payload())
        self.assertEqual(self.service.read_unit(PROJECT, current, self.original.modules[0].source_id).raw, self.original.modules[0].raw)
        self.assertIn(self.original.modules[0].revision, self.service.read_unit(PROJECT, current, "entry").text)
        old_span = self.inspect(revision, "first", ["source"])["source"]["span"]
        self.assertEqual(expected.entry.raw[old_span["start_byte"]:old_span["end_byte"]],
                         self.original.entry.raw[old_span["start_byte"]:old_span["end_byte"]])
        self.assertEqual(geometry_payload(self.page(current)["result"]), geometry_payload(first))
        changed = self.page(current, SECOND)["result"]
        self.assertNotEqual(changed["positions_m"], second["positions_m"])
        self.assertEqual(changed["source_triangle_ordinals"], second["source_triangle_ordinals"])
        middle = [point for point in changed["positions_m"] if abs(point[2] - .8) < 1e-12]
        self.assertAlmostEqual(max(point[0] for point in middle), .72, delta=1e-10)
        old_decoded = self.artifact(old_export, current)
        new_decoded = self.artifact(repaired, current)
        self.assert_page_export(first, old_decoded, "first")
        self.assert_page_export(changed, new_decoded, "second")
        self.assertEqual(mesh_content(old_decoded, "first"), mesh_content(new_decoded, "first"))
        new_second = mesh_content(new_decoded, "second")
        self.assertEqual(new_second["paint"]["pbr"], {"baseColorFactor": [.8, .15, .05, .75],
                                                       "metallicFactor": .7, "roughnessFactor": .25})
        self.assertEqual(new_second["clay"]["pbr"], mesh_content(old_decoded, "second")["clay"]["pbr"])
        for time in (0, 1, 2):
            self.assertEqual(old_decoded.node_pose("first", time), new_decoded.node_pose("first", time))

    def test_isolated_occurrence_palette_repair_changes_pbr_and_digest_but_not_triangles(self):
        revision = self.create()["program_revision"]
        first = self.page(revision)["result"]
        second = self.page(revision, SECOND)["result"]
        cursor = self.page(revision, SECOND, 1)["next_cursor"]
        patches = [self.palette_patch(self.original)]
        repaired = self.send("edit", expected_program_revision=revision, patches=patches,
                             requested_level="delivered", destination=DESTINATION, options={"helpers": False})
        self.assert_success(repaired)
        current = repaired["program_revision"]
        new_first = self.page(current)["result"]
        new_second = self.page(current, SECOND)["result"]
        self.assertEqual(geometry_payload(second), geometry_payload(new_second))
        self.assertEqual(first["geometry_sha256"], new_first["geometry_sha256"])
        self.assertEqual(geometry_payload(first), geometry_payload(new_first))
        self.assertNotEqual(second["geometry_sha256"], new_second["geometry_sha256"])
        stale = self.send("surface.mesh_page", program_revision=current, element_id=SECOND, count=1, cursor=cursor)
        self.assert_code(stale, "OKL-E-REVISION")
        decoded = self.artifact(repaired, current)
        self.assertEqual(mesh_content(decoded, "second")["paint"]["pbr"],
                         {"baseColorFactor": [.8, .15, .05, .75], "metallicFactor": .7, "roughnessFactor": .25})
        self.assertEqual(mesh_content(decoded, "first")["paint"]["pbr"],
                         {"baseColorFactor": [.1, .4, .8, 1], "metallicFactor": .2, "roughnessFactor": .4})
        self.assertEqual(self.service.read_unit(PROJECT, current, self.original.modules[0].source_id).raw,
                         self.original.modules[0].raw)

    def test_utf8_preconditions_and_occurrence_scope_cannot_write_library(self):
        payload = self.original.to_payload()
        payload["entry"]["source"] += "\n// café 😀\n"
        program = load_bundle(payload)
        revision = self.create(program)["program_revision"]
        position = program.entry.raw.index("é".encode("utf-8")) + 1
        split = {"source_id": "entry", "source_revision": program.entry.revision,
                 "element_id": ["sources", "entry"], "start_byte": position, "end_byte": position,
                 "expected_text": "", "replacement": "x"}
        response = self.send("edit", expected_program_revision=revision, patches=[split], requested_level="represented")
        self.assert_code(response, "OKL-E-REVISION")
        self.assertEqual(response["diagnostics"][0]["primary"]["source_id"], "entry")
        library = self.source_patch(program, "0.5[m]", "0.9[m]", source_id=program.modules[0].source_id)
        radius = self.source_patch(program, "0.48[m]", "0.52[m]")
        rejected = self.send("edit", expected_program_revision=revision, patches=[radius, library], requested_level="represented")
        self.assert_code(rejected, "OKL-E-REVISION")
        self.assertEqual(self.service.accepted_revision(PROJECT), revision)
        self.assertEqual(self.service.read_program(PROJECT, revision).to_payload(), program.to_payload())

    def test_section_insertion_reordering_and_removal_preserve_authored_keys(self):
        revision = self.create()["program_revision"]
        old = self.page(revision, SECOND, 7)
        item = self.inspect(revision, "second.rings", ["source", "values"])
        span = item["source"]["initializer_target"]["assignment_span"]
        original_text = self.original.entry.raw[span["start_byte"]:span["end_byte"]].decode("utf-8")
        lines = original_text.splitlines()
        insert_line = '            "between": loft_section(0.4[m], vec3(0.1[m], 0[m], 0[m]), 0.55[m], 0.4[m], "clay"),'
        inserted_text = "\n".join(lines[:2] + [insert_line] + lines[2:])
        previous = self.original
        inserted_geometry = None
        variants = [(inserted_text, ["foot", "between", "middle", "tip"], 128),
                    ("\n".join([lines[0], lines[3]+",", lines[1], insert_line, lines[2].rstrip(","), lines[-1]]),
                     ["foot", "between", "middle", "tip"], 128),
                    (original_text, ["foot", "middle", "tip"], 96)]
        current_text = original_text
        for text, keys, count in variants:
            with self.subTest(keys=keys, text=text):
                patch = self.source_patch(previous, current_text, text)
                changed = self.send("edit", expected_program_revision=previous.program_revision,
                                    patches=[patch], requested_level="constructed")
                self.assert_success(changed)
                current = changed["program_revision"]
                summary = self.inspect(current, "second")["geometry"]["surface"]
                self.assertEqual(summary["section_keys"], keys)
                self.assertEqual((summary["triangle_count"], summary["vertex_count"]), (count, count*3))
                page = self.page(current, SECOND)["result"]
                if count == 128:
                    if inserted_geometry is None:
                        inserted_geometry = geometry_payload(page)
                    else:
                        self.assertEqual(geometry_payload(page), inserted_geometry)
                authored = self.inspect(current, "second.rings", ["values"])["values"]["rings"]["value"]
                self.assertEqual({item["key"] for item in authored}, set(keys))
                self.assertEqual(self.service.read_unit(PROJECT, current, previous.modules[0].source_id).raw, previous.modules[0].raw)
                previous = self.service.read_program(PROJECT, current)
                current_text = text
        # Exact restored UTF-8 bytes restore the content-addressed identity.
        self.assertEqual(previous.program_revision, revision)
        self.assertEqual(geometry_payload(self.page(revision, SECOND, 7)["result"]), geometry_payload(old["result"]))

    def test_mesh_pages_do_not_advance_runs_and_world_motion_remains_revision_bound(self):
        revision = self.create()["program_revision"]
        unavailable = self.inspect(revision, "first", ["state"])
        self.assertFalse(unavailable["state"]["available"])
        run = self.send("evaluate", program_revision=revision, run_id=None, until_seconds="1")
        self.assert_success(run)
        before = self.service.get_run(PROJECT, run["run_id"])
        local = self.page(revision)["result"]
        self.assertEqual(local["positions_m"][0], [.5, 0, .1])
        self.assertEqual(self.service.get_run(PROJECT, run["run_id"]), before)
        state = self.inspect(revision, "first", ["state"], run_id=run["run_id"], time={"seconds": "1", "side": "after"})["state"]
        self.assertEqual(state["program_revision"], revision)
        self.assertEqual(state["position_m"], [-2, .5, 0])
        changed = self.send("edit", expected_program_revision=revision,
                            patches=[self.source_patch(self.original, "0.48[m]", "0.52[m]")], requested_level="represented")
        self.assert_success(changed)
        invalid = self.send("evaluate", program_revision=changed["program_revision"], run_id=run["run_id"], until_seconds="2")
        self.assert_code(invalid, "OKL-E-SAMPLE")
        self.assertEqual(self.service.get_run(PROJECT, run["run_id"]), before)

    def test_generated_native_mesh_keeps_physical_release_and_local_placement_semantics(self):
        text = RELEASE_SOURCE.replace('ontokin "0.2";', 'ontokin "0.3";').replace(
            'profile "construction-0.1";', 'profile "surface-0.1";')
        text = text.replace("geometry = sphere(self.radius);", surface_members(
            placement="pose(self.frame, vec3(0[m], 0[m], 0.1[m]), axis_angle(vec3(1, 0, 0), 90[deg]))"))
        program = source_program(text)
        revision = self.create(program)["program_revision"]
        first_path = 'rig.balls["one"]'
        second_path = 'rig.balls["two"]'
        item = self.inspect(revision, first_path, ["source", "geometry"])
        self.assertEqual(item["source"]["generated"]["input_key"], "one")
        self.assertEqual(item["source"]["writable_spans"], [])
        page = self.page(revision, item["element_id"])["result"]
        self.assertEqual(page["positions_m"][0], [.5, 0, .1])
        for ordinal, expected in ((32, [0, 1, 0]), (48, [0, -1, 0])):
            for actual, target in zip(page["normals"][3*ordinal], expected):
                self.assertAlmostEqual(actual, target, delta=1e-12)
        run = self.send("evaluate", program_revision=revision, run_id=None, until_seconds="2")
        self.assert_success(run)
        for time in ("0", "1", "1.5", "2"):
            for path, released in ((first_path, True), (second_path, False)):
                state = self.inspect(revision, path, ["state"], run_id=run["run_id"],
                                     time={"seconds": time, "side": "after"})["state"]
                seconds = float(time)
                expected = [seconds+.5, 2-5*max(0, seconds-1)**2 if released else 2, 0]
                for actual, target in zip(state["position_m"], expected):
                    self.assertAlmostEqual(actual, target, delta=1e-10)
        exported = self.send("export", program_revision=revision, destination=DESTINATION, options={"helpers": False})
        self.assert_success(exported)
        decoded = self.artifact(exported, revision)
        self.assert_page_export(page, decoded, first_path)
        _, node = decoded.source_node(first_path)
        self.assertEqual(node["extras"]["ontokin"]["physical"]["kind"], "sphere_body")
        self.assertEqual(node["extras"]["ontokin"]["surface"]["physical_participation"], "none")
        for actual, target in zip(decoded.node_pose(first_path, 2)["translation"], [2.5, -3, 0]):
            self.assertAlmostEqual(actual, target, delta=1e-5)

    def test_mesh_generation_observes_real_cancellation_and_request_work_limit(self):
        from ontokin import program_surface
        revision = self.create()["program_revision"]
        original_execute = self.service._execute
        native_mesh = program_surface.build_surface_mesh
        execution = {}
        def capture_check(task, check):
            execution["check"] = check
            return original_execute(task, check)
        self.service._execute = capture_check
        for termination in ("cancel", "operations"):
            with self.subTest(termination=termination):
                request = self.request("surface.mesh_page", program_revision=revision, element_id=FIRST, count=7)
                visits = []
                def build(*args, check, **kwargs):
                    def checkpoint():
                        visits.append(True)
                        if len(visits) == 5:
                            if termination == "cancel":
                                self.assert_success(self.send("cancel", target_request_id=request["request_id"]))
                                execution["check"].last_poll = 0
                            else:
                                execution["check"].operations = execution["check"].limits["max_operations"]
                        check()
                    return native_mesh(*args, check=checkpoint, **kwargs)
                with instrument("ontokin.program_surface.build_surface_mesh", side_effect=build):
                    response = self.service.handle(request)
                self.assertEqual(len(visits), 5, "Termination must interrupt the real mesh builder")
                if termination == "cancel":
                    self.assertEqual(response["status"], "cancelled", response)
                else:
                    self.assert_code(response, "OKL-E-RESOURCE")
                self.assertIsNone(response["next_cursor"])
                self.assertIsNone(response["run_id"])
                for name in ("positions_m", "normals", "triangles", "source_triangle_ordinals"):
                    self.assertNotIn(name, response["result"] or {})
                self.assertEqual(response["accepted_program_revision"], revision)
                self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})
        self.service._execute = original_execute
        self.page(revision, count=1)

    def test_failed_delivery_retains_valid_candidate_without_accepting_or_paging_it(self):
        revision = self.create()["program_revision"]
        patches = [self.source_patch(self.original, "0.48[m]", "0.52[m]")]
        expected = self.expected_candidate(self.original, patches)
        with instrument("ontokin.gltf.MAX_GLB_BYTES", 100):
            failed = self.send("edit", expected_program_revision=revision, patches=patches,
                               requested_level="delivered", destination=DESTINATION)
        self.assert_code(failed, "OKL-E-RESOURCE")
        self.assertEqual(failed["program_revision"], expected.program_revision)
        self.assertEqual(failed["accepted_program_revision"], revision)
        self.assertNotEqual(failed["achieved_level"], "delivered")
        self.assertEqual(self.effect_counts()["artifacts"], 0)
        validated = self.send("validate", program_revision=expected.program_revision, requested_level="constructed")
        self.assert_success(validated)
        self.assertEqual(validated["accepted_program_revision"], revision)
        for operation, fields in (("surface.mesh_page", {"element_id": SECOND, "count": 1}),
                                  ("evaluate", {"run_id": None, "until_seconds": "1"}),
                                  ("export", {"destination": DESTINATION})):
            self.assert_code(self.send(operation, program_revision=expected.program_revision, **fields), "OKL-E-REVISION")
        self.assertEqual(self.service.accepted_revision(PROJECT), revision)

    def test_mesh_result_budgets_fail_explicitly_without_run_or_head_effects(self):
        revision = self.create()["program_revision"]
        for budget in ({"max_result_items": 1}, {"max_value_entries": 1}, {"max_operations": 1}):
            with self.subTest(budget=budget):
                response = self.send("surface.mesh_page", program_revision=revision, element_id=FIRST, count=7, budgets=budget)
                codes = [diagnostic["code"] for diagnostic in response["diagnostics"]]
                if response["protocol_error"]:
                    codes.append(response["protocol_error"]["code"])
                self.assertTrue(set(codes) & {"OKA-E-RESOURCE", "OKL-E-RESOURCE"}, response)
                self.assertIn(response["status"], ("rejected", "failed"), response)
                if response["result"] is not None:
                    self.assertIsNone(response["result"]["run_state"])
                    for field in ("positions_m", "normals", "triangles", "source_triangle_ordinals"):
                        self.assertNotIn(field, response["result"])
                self.assertIsNone(response["next_cursor"])
                self.assertEqual(response["accepted_program_revision"], revision)
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})
        self.page(revision, count=1)

    def test_frozen_large_mesh_still_returns_only_256_complete_triangles(self):
        sections = [(f"s{i}", i*.001, 0, 0, .001, .001, "blue") for i in range(64)]
        program = source_program(single_source(sections, facets=64))
        revision = self.create(program)["program_revision"]
        page = self.page(revision, ["native-export", "demo", "shell"], count=256)
        self.assertEqual(page["result"]["total_triangles"], 8192)
        self.assertEqual(page["result"]["returned_triangles"], 256)
        self.assertEqual(len(page["result"]["positions_m"]), 768)
        self.assertTrue(page["truncated"])

    def test_mesh_value_budget_includes_the_complete_final_envelope(self):
        revision = self.create()["program_revision"]
        complete = self.page(revision, count=256)
        entries = measure_json(complete)["entries"]
        result_entries = measure_json(complete["result"])["entries"]
        self.assertLess(result_entries, entries)
        for limit in (result_entries - 4, result_entries, entries - 1):
            with self.subTest(limit=limit):
                request = self.request("surface.mesh_page", program_revision=revision,
                                       element_id=FIRST, count=256, budgets={"max_value_entries": limit})
                failed = self.service.handle(request)
                self.assert_code(failed, "OKA-E-RESOURCE")
                self.assertFalse(failed["protocol_error"]["details"]["effects_committed"])
                self.assertIsNone(failed["result"])
                self.assertIsNone(failed["next_cursor"])
                self.assertEqual(self.service.handle(request), failed)
                self.assertEqual(failed["accepted_program_revision"], revision)
        exact = self.send("surface.mesh_page", program_revision=revision, element_id=FIRST,
                          count=256, budgets={"max_value_entries": entries})
        self.assert_success(exact)
        self.assertEqual(measure_json(exact)["entries"], entries)
        self.assertEqual(geometry_payload(exact["result"]), geometry_payload(complete["result"]))
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})

    def test_discovery_value_budget_counts_metadata_and_keeps_a_bounded_failure_receipt(self):
        revision = self.create()["program_revision"]
        fields = {"profile": "surface-0.1", "limit": 1, "filter": {"name": "LoftSection"}}
        complete = self.send("discover", **fields)
        self.assert_success(complete)
        self.assertEqual(complete["result"]["total"], 1)
        entries = measure_json(complete)["entries"]
        for limit in (1, entries - 1):
            with self.subTest(limit=limit):
                failed = self.send("discover", **fields, budgets={"max_value_entries": limit})
                self.assert_code(failed, "OKA-E-RESOURCE")
                self.assertFalse(failed["protocol_error"]["details"]["effects_committed"])
                self.assertIsNone(failed["result"])
                self.assertEqual(failed["accepted_program_revision"], revision)
                measure_json(failed)  # An impossibly small success budget still gets a typed failure.
        exact = self.send("discover", **fields, budgets={"max_value_entries": entries})
        self.assert_success(exact)
        self.assertEqual(exact["result"], complete["result"])
        self.assertEqual(measure_json(exact)["entries"], entries)
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})

    def test_lowered_final_delivery_budget_rolls_back_head_run_and_artifact(self):
        revision = self.create()["program_revision"]
        created = self.request("create", bundle=self.original.to_payload(),
                               expected_program_revision=None, requested_level="constructed")
        created["project_id"] = "budget-baseline"
        self.assert_success(self.service.handle(created))
        fields = {"expected_program_revision": revision,
                  "patches": [self.source_patch(self.original, "0.48[m]", "0.52[m]")],
                  "requested_level": "delivered", "destination": DESTINATION,
                  "options": {"end": "0.25", "fps": 8, "helpers": False}}
        baseline_request = self.request("edit", **fields)
        baseline_request["project_id"] = "budget-baseline"
        baseline = self.service.handle(baseline_request)
        self.assert_success(baseline)
        limit = measure_json(baseline)["entries"] - 1
        previous_effects = self.effect_counts()
        execute = self.service._execute
        prepared = []
        def observe(task, check):
            execute(task, check)
            prepared.append((task.accept, task.run is not None, task.artifact is not None))
        with instrument.object(self.service, "_execute", side_effect=observe):
            failed = self.send("edit", **fields, budgets={"max_value_entries": limit})
        self.assertEqual(prepared, [(True, True, True)], "Real delivery must finish before final publication rejects")
        self.assert_code(failed, "OKA-E-RESOURCE")
        self.assertFalse(failed["protocol_error"]["details"]["effects_committed"])
        self.assertEqual(failed["accepted_program_revision"], revision)
        self.assertEqual(failed["program_revision"], baseline["program_revision"])
        self.assertEqual(self.service.accepted_revision(PROJECT), revision)
        self.assertEqual(self.effect_counts(), previous_effects)
        self.assertIsNone(failed["run_id"])
        self.assertIsNone(failed["result"])
        self.assert_code(self.send("surface.mesh_page", program_revision=failed["program_revision"],
                                  element_id=SECOND, count=1), "OKL-E-REVISION")
        repaired = self.send("edit", **fields)
        self.assert_success(repaired)
        self.assertEqual(repaired["program_revision"], baseline["program_revision"])

    def test_native_surface_errors_return_exact_candidate_sources_without_acceptance(self):
        invalid = [
            (single_source(DEFAULT_SECTIONS[:1]), "OKL-E-SURFACE-SECTION"),
            (single_source([(f"s{i}", i*.01, 0, 0, .5, .5, "blue") for i in range(65)]), "OKL-E-SURFACE-SECTION"),
            (single_source([DEFAULT_SECTIONS[0], ("top", 0, 0, 0, .5, .5, "blue")]), "OKL-E-SURFACE-STATION"),
            (single_source([DEFAULT_SECTIONS[0], ("top", .000999, 0, 0, .5, .5, "blue")]), "OKL-E-SURFACE-STATION"),
            (single_source([("bottom", 0, 0, 0, 0, .5, "blue"), DEFAULT_SECTIONS[1]]), "OKL-E-SURFACE-RADIUS"),
            (single_source([("bottom", 0, 0, 0, 100.000001, .5, "blue"), DEFAULT_SECTIONS[1]]), "OKL-E-SURFACE-RADIUS"),
            (single_source().replace("vec3(0[m], 0[m], 0[m])", "vec3(0[m], 0[m], 1[m])", 1), "OKL-E-SURFACE-CENTER"),
            (single_source([("bottom", 0, 0, 0, .5, .5, "absent"), DEFAULT_SECTIONS[1]]), "OKL-E-SURFACE-REGION"),
            (single_source(palette={**DEFAULT_PALETTE, **{f"p{i}": DEFAULT_PALETTE["blue"] for i in range(16)}}), "OKL-E-SURFACE-MATERIAL"),
            (single_source(palette={"blue": {"rgba": [1, 1, 1, 1], "metallic": 1.1, "roughness": .4}}), "OKL-E-SURFACE-MATERIAL"),
            (single_source(facets=9), "OKL-E-SURFACE-FACETS"),
            (single_source(facets=68), "OKL-E-SURFACE-FACETS"),
            (single_source(caps="rounded"), "OKL-E-SURFACE-CAPS"),
            (single_source(placement="pose(world, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0))"), "OKL-E-SURFACE-PLACEMENT"),
        ]
        revision = self.create()["program_revision"]
        for index, (text, code) in enumerate(invalid):
            with self.subTest(code=code, index=index):
                program = source_program(text)
                request = self.request("create", bundle=program.to_payload(), expected_program_revision=None, requested_level="constructed")
                request["project_id"] = f"invalid-native-{index}"
                response = self.service.handle(request)
                self.assert_code(response, code)
                self.assertEqual(response["program_revision"], program.program_revision)
                self.assertIsNone(response["accepted_program_revision"])
                diagnostic = next(item for item in response["diagnostics"] if item["code"] == code)
                self.assertEqual(diagnostic["program_revision"], program.program_revision)
                self.assertEqual(diagnostic["source_revision"], program.entry.revision)
                self.assertEqual(diagnostic["primary"]["source_id"], "entry")
                self.assertEqual(self.service.read_program(request["project_id"], program.program_revision).entry.raw, text.encode("utf-8"))
        self.assertEqual(self.service.accepted_revision(PROJECT), revision)
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})

    def test_competing_surface_repairs_commit_one_head_and_keep_losing_candidate(self):
        revision = self.create()["program_revision"]
        requests = [self.request("edit", expected_program_revision=revision,
                                patches=[self.source_patch(self.original, "0.48[m]", value)], requested_level="evaluated")
                    for value in ("0.52[m]", "0.55[m]")]
        with self.prepared(requests) as (workers, threads):
            candidates = [load_bundle(worker.prepared["program"]) for worker in workers]
            self.assertTrue(all(worker.prepared["accept"] for worker in workers))
            self.release(workers[0], threads[0])
            self.release(workers[1], threads[1])
        winning = self.service.handle(requests[0])
        self.assert_success(winning)
        losing = self.service.handle(requests[1])
        self.assert_code(losing, "OKL-E-REVISION")
        self.assertEqual(self.service.accepted_revision(PROJECT), candidates[0].program_revision)
        self.assertEqual(losing["program_revision"], candidates[1].program_revision)
        self.assertEqual(self.service.read_program(PROJECT, candidates[1].program_revision).to_payload(), candidates[1].to_payload())
        self.assert_code(self.send("surface.mesh_page", program_revision=candidates[1].program_revision, element_id=SECOND, count=1), "OKL-E-REVISION")
        # Completed validation evidence may be retained for the losing candidate;
        # it must never be exposed as an ordinary accepted-program run.
        self.assertEqual(self.effect_counts(), {"runs": 2, "artifacts": 0})
        self.assertFalse(self.service.get_run(PROJECT, winning["run_id"])["candidate_only"])
        self.assertTrue(self.service.get_run(PROJECT, losing["run_id"])["candidate_only"])

    def test_cancellation_after_native_delivery_computation_commits_no_new_effects(self):
        revision = self.create()["program_revision"]
        request = self.request("edit", expected_program_revision=revision,
                               patches=[self.source_patch(self.original, "0.48[m]", "0.52[m]")],
                               requested_level="delivered", destination=DESTINATION, options={"helpers": False})
        with self.prepared([request]) as (workers, threads):
            prepared = workers[0].prepared
            self.assertTrue(prepared["accept"])
            self.assertIsNotNone(prepared["artifact"])
            self.assertIsNotNone(prepared["run"])
            cancel = self.send("cancel", target_request_id=request["request_id"])
            self.assert_success(cancel)
            self.release(workers[0], threads[0])
        response = self.service.handle(request)
        self.assertEqual(response["status"], "cancelled", response)
        self.assertEqual(response["accepted_program_revision"], revision)
        self.assertIsNone(response["result"])
        self.assertIsNone(response["run_id"])
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})
        candidate = load_bundle(prepared["program"])
        self.assertEqual(self.service.read_program(PROJECT, candidate.program_revision).to_payload(), candidate.to_payload())
        self.assert_code(self.send("surface.mesh_page", program_revision=candidate.program_revision, element_id=SECOND, count=1), "OKL-E-REVISION")

    def test_oversized_completed_native_response_rolls_back_head_run_and_artifact(self):
        revision = self.create()["program_revision"]
        original_execute = self.service._execute
        prepared = {}
        def oversized(task, check):
            original_execute(task, check)
            self.assert_success(task.response)
            prepared["program"] = task.source
            self.assertIsNotNone(task.artifact)
            task.response["result"]["oversized_probe"] = "x" * (4 * 1024 * 1024)
        self.service._execute = oversized
        response = self.send("edit", expected_program_revision=revision,
                             patches=[self.source_patch(self.original, "0.48[m]", "0.52[m]")],
                             requested_level="delivered", destination=DESTINATION)
        self.assert_code(response, "OKA-E-RESOURCE")
        self.assertFalse(response["protocol_error"]["details"]["effects_committed"])
        self.assertEqual(self.service.accepted_revision(PROJECT), revision)
        self.assertEqual(self.effect_counts(), {"runs": 0, "artifacts": 0})
        self.assertEqual(self.service.read_program(PROJECT, prepared["program"].program_revision).to_payload(), prepared["program"].to_payload())

    def test_queued_restart_exact_retry_and_stale_edits_do_not_replay_effects(self):
        request = self.request("create", bundle=self.original.to_payload(), expected_program_revision=None, requested_level="represented")
        self.assertEqual(self.service.submit(request)["status"], "queued")
        self.service.close()
        self.service = ProgramAgentService(self.path, protocol=PROTOCOL)
        created = self.service.handle(request)
        self.assert_success(created)
        revision = created["program_revision"]
        page_request = self.request("surface.mesh_page", program_revision=revision, element_id=FIRST, count=1)
        first_page = self.service.handle(page_request)
        self.assert_success(first_page)
        patch = self.source_patch(self.original, "0.48[m]", "0.52[m]")
        edit_request = self.request("edit", expected_program_revision=revision, patches=[patch], requested_level="represented")
        changed = self.service.handle(edit_request)
        self.assert_success(changed)
        self.service.close()
        self.service = ProgramAgentService(self.path, protocol=PROTOCOL)
        self.assertEqual(self.service.handle({key: request[key] for key in reversed(request)}), created)
        self.assertEqual(self.service.handle(page_request), first_page)
        self.assertEqual(self.service.handle(edit_request), changed)
        self.assert_code(self.service.handle({**page_request, "count": 2}), "OKL-E-REQUEST-ID")
        self.assert_code(self.send("edit", expected_program_revision=revision, patches=[patch], requested_level="represented"), "OKL-E-REVISION")
        continuation = self.page(revision, count=7, cursor=first_page["next_cursor"])
        self.assertEqual(continuation["result"]["source_triangle_ordinals"], list(range(1, 8)))
        self.assertEqual(continuation["accepted_program_revision"], changed["program_revision"])
        self.assertEqual(self.service.accepted_revision(PROJECT), changed["program_revision"])
        self.assertFalse(self.service.work_next())


if __name__ == "__main__":
    unittest.main()
