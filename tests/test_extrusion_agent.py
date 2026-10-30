"""Actual .8 source repair, bounded inspection and independently decoded delivery."""
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
from ontokin.budget_agent import BudgetAgentService
from ontokin.budget_runtime import execute_budgeted_export, execute_extrusion_export
from ontokin.bundle import ProgramBundle, SourceUnit, load_bundle
from ontokin.execution_budget import HostPolicy
from ontokin.extrusion_agent import ExtrusionAgentService
from ontokin.extrusion_protocol import ExtrusionProtocol
from ontokin.program_bindings import PROGRAM_BINDINGS, PROFILE_BINDINGS
from ontokin.scene import ExportOptions
from tests.test_export import DecodedGLB


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/polygon-extrusions"
PROTOCOL, PROFILE, TARGET = "ontokin.agent/0.8", "polygon-extrusion-0.1", "ontokin.glb/0.8"
SHAPE = ["extrusion-case", "demo", "shape"]
FIRST = ["extrusion-assembly", "demo", "first"]
SIBLING = ["extrusion-assembly", "demo", "sibling"]
OPTIONS = {"fps": 2, "end": "1", "helpers": False}


def source(name="concave-bracket", *, text=None):
    path = FIXTURES / "corrected" / (name + ".ok")
    if not path.is_file():
        path = FIXTURES / (name + ".ok")
    text = path.read_text() if text is None else text
    modules = []
    if 'from "fixture.extrusion-parts"' in text:
        modules.append({"package_id": "fixture.extrusion-parts", "version": "1.0.0",
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
        material = decoded.document["materials"][primitive["material"]]
        key = primitive["extras"]["ontokin"]["region_key"]
        regions[key] = len(indices) // 3
        for start in range(0, len(indices), 3):
            ia, ib, ic = indices[start:start+3]
            a, b, c = (positions[i] for i in (ia, ib, ic))
            normal = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
            assert sum(normal[i]*normals[ia][i] for i in range(3)) > 0
            total += sum(a[i]*cross(b,c)[i] for i in range(3)) / 6
            triangles += 1
    return total, triangles, regions


class ExtrusionAgentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c075-agent-")
        self.service = ExtrusionAgentService(self.directory.name)
        self.serial = 0

    def tearDown(self):
        self.service.close()
        self.directory.cleanup()

    def request(self, operation, **fields):
        self.serial += 1
        return {"schema_version": PROTOCOL, "project_id": "extrusions",
                "request_id": f"polygon-{self.serial}", "operation": operation, **fields}

    def send(self, operation, **fields):
        return self.service.handle(self.request(operation, **fields))

    def success(self, response):
        self.assertEqual(response["schema_version"], PROTOCOL, response)
        self.assertEqual(response["status"], "succeeded", response)
        return response

    def failure(self, response, code=None):
        self.assertIn(response["status"], ("rejected", "failed"), response)
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
            return {"accepted": self.service.accepted_revision("extrusions"),
                    "runs": [tuple(row) for row in db.execute("SELECT id,source_revision,descriptor,version FROM runs ORDER BY id")],
                    "artifacts": [tuple(row) for row in db.execute("SELECT id,data,sha256 FROM artifacts ORDER BY id")]}

    def test_explicit_discovery_names_source_types_limits_schemas_and_store(self):
        response = self.success(self.send("discover", profile=PROFILE, limit=1000))
        result = response["result"]
        self.assertEqual(result["language_version"], "0.8")
        self.assertEqual(result["source_header"], 'ontokin "0.8"; module Example @ "example"; profile "polygon-extrusion-0.1";')
        names = {item["name"] for item in result["items"]}
        self.assertTrue({"PlanarPoint", "PolygonVertex", "planar_point", "polygon_vertex", "extrude"} <= names)
        interface = result["polygon_extrusion_interface"]
        self.assertEqual(interface["defaults"], {"max_operations": 100000, "max_elapsed_ms": 30000})
        self.assertEqual(interface["polygon_limits"]["max_vertices"], 64)
        self.assertEqual(self.service.database_path.name, "extrusion-program-agent.sqlite3")
        self.assertEqual(self.service._store.schema_version, "ontokin.extrusion-program-agent-store/0.1")
        for key in ("request_schema", "response_schema", "adoption"):
            self.assertTrue((ROOT / interface[key]).is_file())
        self.assertNotIn(PROTOCOL, PROGRAM_BINDINGS)
        self.assertNotIn(PROFILE, PROFILE_BINDINGS)

    def test_discovery_links_actual_public_source_without_accepting_it(self):
        program = source()
        response = self.success(self.send("discover", profile=PROFILE, limit=1000, bundle=program.to_payload()))
        self.assertEqual(response["result"]["program_context"]["program_revision"], program.program_revision)
        self.assertIsNone(self.service.accepted_revision("extrusions"))
        self.assertEqual(response["execution_budget"]["source_request"]["max_operations"], 100000)

    def test_polygon_summary_exposes_stable_keys_order_materials_and_no_matter(self):
        program = self.create()
        response = self.success(self.send("inspect", program_revision=program.program_revision,
            selector={"path": "shape"}, fields=["identity", "geometry", "support"], limit=1))
        item = response["result"]["items"][0]
        summary = item["geometry"]["surface"]
        self.assertEqual(summary["schema_version"], "ontokin.polygon-extrusion-summary/0.1")
        self.assertEqual(summary["family"], "polygon_extrusion")
        self.assertEqual(summary["vertex_keys"], ["v0", "v1", "v2", "v3", "v4", "v5"])
        self.assertEqual(summary["orders"], [0, 10, 20, 30, 40, 50])
        self.assertEqual(summary["points_m"][3], [1., 1.])
        self.assertEqual(summary["depth_m"], .25)
        self.assertEqual(summary["triangle_count"], 20)
        self.assertEqual(summary["vertex_count"], 60)
        self.assertEqual({r["key"]: r["triangle_count"] for r in summary["regions"]}, {"bottom":4,"side":12,"top":4})
        self.assertEqual(summary["physical_participation"], "none")
        self.assertEqual(item["support"]["named_destination"], TARGET)

    def test_mesh_pages_cover_all_triangles_and_region_filters(self):
        program = self.create()
        page = self.page(program, count=7)
        all_ordinals = list(page["result"]["source_triangle_ordinals"])
        while page["next_cursor"]:
            page = self.page(program, count=5, cursor=page["next_cursor"])
            all_ordinals += page["result"]["source_triangle_ordinals"]
        self.assertEqual(all_ordinals, list(range(20)))
        side = self.page(program, region="side")["result"]
        self.assertEqual(side["returned_triangles"], 12)
        self.assertEqual(set(side["region_keys"]), {"side"})
        self.assertEqual(len(side["positions_m"]), 36)
        self.failure(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=SHAPE, count=3, budgets={"max_result_items": 2}), "OKL-E-RESOURCE")

    def test_declaration_reordering_preserves_local_mesh_but_changes_revision(self):
        first = self.create()
        before = self.page(first)["result"]
        after_text = (FIXTURES / "reordered-bracket.ok").read_text()
        result = self.success(self.send("edit", expected_program_revision=first.program_revision,
            requested_level="constructed", patches=[exact_patch(first, first.entry.text, after_text)]))
        after = source(text=after_text)
        self.assertEqual(result["accepted_program_revision"], after.program_revision)
        current = self.page(after)["result"]
        self.assertNotEqual(first.program_revision, after.program_revision)
        self.assertEqual(geometry(before), geometry(current))
        self.assertEqual(before["geometry_sha256"], current["geometry_sha256"])

    def test_keyed_vertex_repair_preserves_sibling_and_library(self):
        program = self.create(source("assembly"))
        before_first = self.page(program, FIRST)["result"]
        before_sibling = self.page(program, SIBLING)["result"]
        old = 'polygon_vertex(30, planar_point(1[m], 1[m]), "side")'
        new = 'polygon_vertex(30, planar_point(1.5[m], 1[m]), "side")'
        response = self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program, old, new)]))
        repaired = source("assembly", text=program.entry.text.replace(old, new))
        self.assertEqual(response["accepted_program_revision"], repaired.program_revision)
        saved = self.service.read_program("extrusions", repaired.program_revision)
        self.assertEqual(saved.modules[0].raw, program.modules[0].raw)
        self.assertEqual(geometry(self.page(repaired, SIBLING)["result"]), geometry(before_sibling))
        changed = self.page(repaired, FIRST)["result"]
        self.assertNotEqual(geometry(changed), geometry(before_first))
        self.assertEqual(changed["element_id"], before_first["element_id"])

    def test_invalid_crossing_candidate_rolls_back_source_run_and_artifact(self):
        program = self.create()
        self.success(self.send("evaluate", program_revision=program.program_revision, run_id=None, until_seconds="0.5"))
        self.export(program)
        before = self.retained()
        bad = (FIXTURES / "crossing.ok").read_text()
        result = self.failure(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="delivered", destination=TARGET, options=OPTIONS,
            patches=[exact_patch(program, program.entry.text, bad)]), "OKL-E-EXTRUSION-TOPOLOGY")
        self.assertEqual(self.retained(), before)
        self.assertNotEqual(result["achieved_level"], "delivered")
        self.assertNotIn("artifact_id", result.get("result") or {})

    def test_stale_source_preconditions_and_nominal_identity_reject_atomically(self):
        program = self.create()
        edit = exact_patch(program, '0.25[m]', '0.5[m]')
        before = self.retained()
        for modified in ({**edit,"expected_text":"wrong"}, {**edit,"source_revision":"sha256:"+"0"*64},
                         {**edit,"element_id":SHAPE}):
            self.failure(self.send("edit", expected_program_revision=program.program_revision,
                requested_level="constructed", patches=[modified]))
            self.assertEqual(before, self.retained())
        self.failure(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program,'class Shape @ "shape"','class Shape @ "different"')]), "OKL-E-ID")
        self.assertEqual(before, self.retained())

    def test_cursor_cannot_change_revision_or_region(self):
        program = self.create()
        paged = self.page(program, count=2)
        self.failure(self.send("surface.mesh_page", program_revision=program.program_revision,
            element_id=SHAPE, count=2, cursor=paged["next_cursor"], region="top"))
        self.success(self.send("edit", expected_program_revision=program.program_revision,
            requested_level="constructed", patches=[exact_patch(program,"0.25[m]","0.5[m]")]))
        revised = source(text=program.entry.text.replace("0.25[m]","0.5[m]"))
        self.failure(self.send("surface.mesh_page", program_revision=revised.program_revision,
            element_id=SHAPE, count=2, cursor=paged["next_cursor"]))

    def test_export_retrieve_has_analytic_volume_regions_and_recorded_motion(self):
        program = self.create()
        exported = self.export(program)
        decoded = DecodedGLB(self.retrieve(exported))
        volume, triangles, regions = decoded_volume(decoded,"shape")
        self.assertAlmostEqual(volume, 1.25, places=12)
        self.assertEqual(triangles, 20)
        self.assertEqual(regions, {"bottom":4,"side":12,"top":4})
        for when in (0., .25, .5, .75, 1.):
            translation = decoded.node_pose("shape", when)["translation"]
            self.assertAlmostEqual(translation[0],0.,places=7)
            self.assertAlmostEqual(translation[1],when*.5,places=7)
            self.assertAlmostEqual(translation[2],0.,places=7)
        self.assertEqual(exported["result"]["destination"], TARGET)
        self.assertGreater(exported["execution_budget"]["consumed_operations"],
            exported["result"]["report"]["execution_budget_at_export"]["consumed_operations"])

    def test_binary32_collapse_never_publishes_an_artifact(self):
        program = self.create(source("binary32-collapse"))
        before = self.retained()
        response = self.failure(self.send("export", program_revision=program.program_revision,
                                          destination=TARGET, options=OPTIONS))
        self.assertNotEqual(response["achieved_level"], "delivered")
        after = self.retained()
        self.assertEqual(after["accepted"], before["accepted"])
        self.assertEqual(after["artifacts"], before["artifacts"])
        self.assertEqual(len(after["runs"]), 1)
        descriptor = json.loads(after["runs"][0][2])
        self.assertEqual(descriptor["program_revision"], program.program_revision)
        self.assertEqual(descriptor["valid_until_seconds"], "1")
        self.assertFalse(descriptor["candidate_only"])
        self.assertNotIn("artifact_id", response.get("result") or {})

    def test_retry_returns_original_receipt_without_new_execution(self):
        program = self.create()
        request = self.request("export", program_revision=program.program_revision, destination=TARGET, options=OPTIONS)
        response = self.success(self.service.handle(request))
        before = self.retained()
        with patch.object(self.service, "_execute", side_effect=AssertionError("replayed")):
            self.assertEqual(self.service.handle(copy.deepcopy(request)), response)
        changed = copy.deepcopy(request); changed["options"]["fps"] = 3
        self.failure(self.service.handle(changed), "OKL-E-REQUEST-ID")
        self.assertEqual(before,self.retained())

    def test_saved_artifacts_and_runs_require_current_host_authority(self):
        self.service.host_policy = HostPolicy(400000,80000)
        text = source().entry.text.replace('profile "polygon-extrusion-0.1";',
            'profile "polygon-extrusion-0.1";\nexecution { max_operations = 200000; max_elapsed = 60[s]; }')
        program = self.create(source(text=text)); exported = self.export(program)
        run = self.success(self.send("evaluate", program_revision=program.program_revision, run_id=None, until_seconds="0.5"))
        before=self.retained();self.service.host_policy=HostPolicy()
        for operation,fields in (("artifact",{"artifact_id":exported["result"]["artifact_id"],"max_bytes":64}),
            ("evaluate",{"program_revision":program.program_revision,"run_id":run["run_id"],"until_seconds":"1"})):
            response=self.failure(self.send(operation,**fields),"OKL-E-RESOURCE")
            self.assertEqual(response["execution_budget"]["budget_reason"],"host_ceiling_exceeded")
        self.assertEqual(before,self.retained())
        reduced=self.success(self.send("artifact",artifact_id=exported["result"]["artifact_id"],max_bytes=64,
            budgets={"max_operations":100000,"max_elapsed_ms":30000}))
        self.assertEqual(base64.b64decode(reduced["result"]["data_base64"])[:4],b"glTF")

    def test_omitted_limits_stay_defaults_on_larger_host_and_caps_only_reduce(self):
        self.service.host_policy=HostPolicy(400000,80000)
        program=self.create()
        response=self.success(self.send("validate",program_revision=program.program_revision,requested_level="constructed"))
        self.assertEqual(response["execution_budget"]["effective"],{"max_operations":100000,"max_elapsed_ms":30000})
        bad=self.failure(self.send("validate",program_revision=program.program_revision,requested_level="constructed",budgets={"max_operations":100001}),"OKL-E-RESOURCE")
        self.assertEqual(bad["execution_budget"]["budget_reason"],"request_cap_exceeds_source")

    def test_budget_exhaustion_and_publication_failure_are_atomic(self):
        program=self.create();before=self.retained()
        self.failure(self.send("validate",program_revision=program.program_revision,requested_level="constructed",budgets={"max_operations":5}),"OKL-E-RESOURCE")
        state={"late":False}
        self.service._clock=lambda: 31. if state["late"] else 0.
        original=self.service._execute
        def expire_after_export(task,check):
            result=original(task,check)
            state["late"]=True
            return result
        with patch.object(self.service,"_execute",side_effect=expire_after_export):
            response=self.failure(self.send("export",program_revision=program.program_revision,destination=TARGET,options=OPTIONS),"OKL-E-RESOURCE")
        self.assertNotEqual(response["achieved_level"],"delivered")
        self.assertNotIn("artifact_id",response.get("result") or {})
        self.assertEqual(before,self.retained())

    def test_reset_status_and_queued_cancellation_execute(self):
        program=self.create()
        self.success(self.send("reset",program_revision=program.program_revision))
        request=self.request("validate",program_revision=program.program_revision,requested_level="evaluated")
        self.assertEqual(self.service.submit(request)["status"],"queued")
        self.success(self.send("cancel",target_request_id=request["request_id"]))
        self.assertEqual(self.service.handle(request)["status"],"cancelled")
        status=self.success(self.send("status",target_request_id=request["request_id"]))
        self.assertEqual(status["result"]["target_status"],"cancelled")

    def test_older_binding_and_destination_are_rejected_without_registry_changes(self):
        with self.assertRaises(ProtocolError):
            BudgetAgentService(self.directory.name,protocol=PROTOCOL)
        request=self.request("discover",profile=PROFILE,limit=10)
        request["schema_version"]="ontokin.agent/0.7"
        self.failure(self.service.handle(request),"OKA-E-REQUEST")
        program=self.create()
        self.failure(self.send("export",program_revision=program.program_revision,destination="ontokin.glb/0.7",options=OPTIONS),"OKA-E-REQUEST")
        old=source(text=source().entry.text.replace('"0.8"','"0.7"',1).replace(PROFILE,'planar-reach-budget-0.1',1))
        self.failure(self.send("create",bundle=old.to_payload(),expected_program_revision=program.program_revision,requested_level="constructed"))

    def test_inherited_loft_keeps_summary_and_has_explicit_mesh_profile(self):
        from tests.test_surface_export import single_source
        text=single_source().replace('"0.3"','"0.8"',1).replace('surface-0.1',PROFILE,1)
        program=self.create(source(text=text))
        response=self.success(self.send("inspect",program_revision=program.program_revision,selector={"path":"shell"},fields=["identity","geometry"],limit=1))
        item=response["result"]["items"][0]
        self.assertEqual(item["geometry"]["surface"]["schema_version"],"ontokin.surface-summary/0.1")
        self.page(program,item["element_id"])

    def test_direct_export_and_cli_use_explicit_08_binding(self):
        program=source("rectangle")
        direct=execute_extrusion_export(program,options=ExportOptions(fps=2,end="1",helpers=False))
        self.assertIsNotNone(direct.data,direct.report)
        self.assertEqual(direct.report["target_contract"],TARGET)
        self.assertEqual(direct.report["language_version"],"0.8")
        self.assertIsNone(execute_budgeted_export(program).data)
        path=Path(self.directory.name)/"rectangle.glb"
        result=subprocess.run([sys.executable,"-m","ontokin","export",str(FIXTURES/"rectangle.ok"),"--target",TARGET,
            "--output",str(path),"--fps","2","--end","1","--no-helpers"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        volume,triangles,_=decoded_volume(DecodedGLB(path.read_bytes()),"shape")
        self.assertAlmostEqual(volume,1.,places=12);self.assertEqual(triangles,12)

    def test_cli_agent_discovery_and_host_policy_injection_rejection(self):
        request=self.request("discover",profile=PROFILE,limit=1000)
        path=Path(self.directory.name)/"request.json";path.write_text(json.dumps(request))
        result=subprocess.run([sys.executable,"-m","ontokin","agent","--protocol",PROTOCOL,"--store",str(Path(self.directory.name)/"cli"),"--request",str(path),"--wait"],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"]["language_version"],"0.8")
        request=self.request("discover",profile=PROFILE,limit=10,host_policy={"max_operations":400000})
        self.failure(self.service.handle(request),"OKA-E-REQUEST")

    def test_separate_services_do_not_share_acceptance_in_one_directory(self):
        from tests.test_budget_agent_lifecycle import DEFAULT_TEXT
        program = self.create()
        with BudgetAgentService(self.directory.name) as old:
            self.assertIsNone(old.accepted_revision("extrusions"))
            old_program = ProgramBundle(SourceUnit("entry", "old.ok", DEFAULT_TEXT.encode()))
            response = old.handle({"schema_version":"ontokin.agent/0.7","project_id":"extrusions",
                "request_id":"polygon-1","operation":"create","bundle":old_program.to_payload(),
                "expected_program_revision":None,"requested_level":"constructed"})
            self.assertEqual(response["status"],"succeeded",response)
            self.assertEqual(old.accepted_revision("extrusions"),old_program.program_revision)
            self.assertNotEqual(old.database_path,self.service.database_path)
        self.assertEqual(self.service.accepted_revision("extrusions"),program.program_revision)

    def test_host_cancellation_inside_polygon_construction_keeps_identity_and_receipt(self):
        from ontokin import extrusion
        from ontokin.diagnostics import OntoKinError
        marker=OntoKinError("OKL-E-EXTRUSION-NUMERIC","trusted caller interrupt")
        state={"armed":False,"calls":0}
        def check():
            state["calls"]+=1
            if state["armed"]:
                raise marker
        self.service._host_check=check
        original=extrusion.triangulate_extrusion
        def arm(*args,**kwargs):
            state["armed"]=True
            return original(*args,**kwargs)
        request=self.request("create",bundle=source().to_payload(),expected_program_revision=None,
                             requested_level="constructed")
        with patch.object(extrusion,"triangulate_extrusion",side_effect=arm):
            with self.assertRaises(OntoKinError) as caught:
                self.service.handle(request)
        self.assertIs(caught.exception,marker)
        self.assertGreater(state["calls"],1)
        calls=state["calls"]
        response=self.service.handle(request)
        self.assertEqual(response["status"],"cancelled",response)
        self.assertEqual(state["calls"],calls)
        self.assertEqual(self.retained(),{"accepted":None,"runs":[],"artifacts":[]})

    def test_budget_reducing_polygon_source_repair_uses_candidate_authority(self):
        self.service.host_policy=HostPolicy(400000,80000)
        text=source().entry.text.replace('profile "polygon-extrusion-0.1";',
            'profile "polygon-extrusion-0.1";\nexecution { max_operations = 200000; max_elapsed = 60[s]; }')
        program=self.create(source(text=text))
        self.service.host_policy=HostPolicy()
        response=self.success(self.send("edit",expected_program_revision=program.program_revision,
            requested_level="constructed",patches=[exact_patch(program,"200000","100000"),
                                                     exact_patch(program,"60[s]","30[s]")]))
        repaired=source(text=text.replace("200000","100000").replace("60[s]","30[s]"))
        self.assertEqual(response["accepted_program_revision"],repaired.program_revision)
        self.assertEqual(response["execution_budget"]["source_request"],{"max_operations":100000,"max_elapsed_ms":30000})
        self.assertEqual(self.page(repaired)["result"]["total_triangles"],20)
