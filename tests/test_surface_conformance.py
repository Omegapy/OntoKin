"""Acceptance-runner evidence checks, with actual source workflow witnesses.

Synthetic CI/report envelopes below exercise the retained-record checker only;
they are never represented as actual remote CI or external browser execution.
The bounded studio witness uses the real Agent/0.3 edit/export/artifact APIs.
"""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ontokin import surface_conformance as conformance


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    return {"path": path.name, "sha256": conformance.file_identity(path)}


def passed_execution(names):
    return {"unique_required": len(names), "tests_run": len(names), "elapsed_seconds": 0,
            "outcomes": {"passed": len(names)}, "loader_errors": [], "fixture_errors": [],
            "unexpected_test_records": [],
            "tests": [{"test_id": name, "status": "passed", "elapsed_seconds": 0, "failures": []} for name in names]}


class SurfaceConformanceMappingTests(unittest.TestCase):
    def test_mapping_keeps_frozen_acceptance_limits_cases_and_inherited_test_ids(self):
        manifest = conformance.load_manifest()
        acceptance = conformance._json_file(conformance.FIXTURES / "acceptance.json")
        self.assertEqual([c["id"] for c in manifest["cases"]], [f"M{i:02}" for i in range(1,13)])
        self.assertEqual(manifest["limits"], acceptance["limits"])
        self.assertEqual(manifest["tolerance"], acceptance["tolerance"])
        discovered = set(conformance.discover_test_ids())
        required = {n for c in manifest["cases"] for n in c["required_tests"]}
        self.assertTrue(required <= discovered, required-discovered)
        self.assertEqual(len(manifest["regression_required_test_ids"]), 439)
        self.assertTrue(set(manifest["regression_required_test_ids"]) <= discovered)
        self.assertEqual(len(manifest["mandatory_native_fixtures"]), 22)
        self.assertEqual(manifest["mandatory_browser_fixtures"], ["palette-repaired", "composition-ordinary", "composition-generated", "rotated-release"])
        self.assertEqual(manifest["mandatory_browser_captures"], [{"view":"front","time_seconds":0}, {"view":"side","time_seconds":0}, {"view":"front","time_seconds":1.5}])
        self.assertIn("regression", manifest["cases"][-1]["external_gates"])
        self.assertIn("ci", manifest["cases"][-1]["external_gates"])

    def test_current_and_ci_inventory_share_all_executed_source_inputs(self):
        paths={record["path"] for record in conformance.evidence_inventory()}
        self.assertTrue({"prototypes/surface_v01/mesh.py","prototypes/surface_v01/glb.py",
                         "examples/visual/viewer.js","examples/visual/viewer.html",
                         "examples/visual/01-independent-parts.ok"} <= paths)
        for path in paths:
            self.assertTrue(conformance._inventory_path(path),path)
        for generated in ("examples/visual/viewer.bundle.js","examples/visual/demo-data.js",
                          "examples/visual/demo-data/copied.ok","examples/visual/01-independent-parts.export.json",
                          "validation/surface/workflow.json","tools/node_modules/package/index.js"):
            self.assertFalse(conformance._inventory_path(generated),generated)

    def test_changed_mapping_cannot_silently_remove_evidence_or_relax_limits(self):
        original = conformance.load_manifest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for edit in (lambda m: m["cases"][0].update(external_gates=[]),
                         lambda m: m["limits"].update(max_glb_bytes=999999999),
                         lambda m: m["mandatory_native_fixtures"].remove("rotated-release")):
                altered = copy.deepcopy(original); edit(altered)
                write_json(root / "conformance.json", altered)
                with self.assertRaisesRegex(ValueError, "reviewed conformance mapping bytes changed"):
                    conformance.load_manifest(root)

    def test_actual_selected_source_methods_execute_once_and_missing_destination_stays_pending(self):
        report = conformance.run_conformance(case_ids=["M01"])
        execution = report["test_execution"]
        self.assertEqual(execution["tests_run"], 2)
        self.assertEqual(execution["outcomes"], {"passed": 2})
        self.assertEqual(report["cases"][0]["status"], "pending")
        self.assertEqual(report["summary"], {"total":1,"passed":0,"failed":0,"pending":1,
                                           "all_adopted_cases_selected":False,"full_gate_complete":False})
        self.assertEqual(report["unselected_case_ids"], [f"M{i:02}" for i in range(2,13)])
        self.assertFalse(report["full_product_conformance_certified"])
        self.assertFalse(report["external_evidence"]["executed_external_tools"])
        self.assertNotIn("assertions", execution)
        json.dumps(report, allow_nan=False)

    def test_shared_methods_are_deduplicated_and_skips_cannot_become_case_passes(self):
        captured = []
        def run(names):
            captured.extend(names)
            result = passed_execution(names)
            result["tests"][0]["status"] = "skipped"
            result["tests"][0]["failures"] = ["required check unavailable"]
            result["outcomes"] = {"passed":len(names)-1,"skipped":1}
            return result
        with patch.object(conformance, "_run_tests", side_effect=run):
            report = conformance.run_conformance(case_ids=["M01","M03"])
        self.assertEqual(len(captured), len(set(captured)))
        self.assertEqual(len(captured), 4)
        self.assertFalse(report["summary"]["full_gate_complete"])
        self.assertTrue(any("skipped" in reason for case in report["cases"] for reason in case["pending_reasons"]))

    def test_failed_test_and_changed_input_bytes_are_reported_separately(self):
        def failed(names):
            result = passed_execution(names)
            result["tests"][0].update(status="failed", failures=["actual failed assertion"])
            result["outcomes"] = {"passed":len(names)-1,"failed":1}
            return result
        with patch.object(conformance, "_run_tests", side_effect=failed), \
             patch.object(conformance, "evidence_inventory", side_effect=[[],[{"path":"changed","sha256":"sha256:"+"0"*64}]]):
            report = conformance.run_conformance(case_ids=["M10"])
        self.assertEqual(report["cases"][0]["status"], "failed")
        self.assertFalse(report["evidence_stable_during_run"])
        self.assertTrue(report["run_issues"])

    def test_cli_pending_is_explicit_and_allow_pending_never_hides_a_failure(self):
        pending = {"summary":{"total":12,"passed":1,"failed":0,"pending":11,"full_gate_complete":False},"run_issues":[]}
        with patch.object(conformance, "run_conformance", return_value=pending), redirect_stdout(io.StringIO()):
            self.assertEqual(conformance.main([]), 2)
            self.assertEqual(conformance.main(["--allow-pending"]), 0)
            self.assertFalse(pending["summary"]["full_gate_complete"])
            pending["summary"]["failed"] = 1
            self.assertEqual(conformance.main(["--allow-pending"]), 1)
            pending["summary"]["failed"] = 0
            pending["run_issues"] = ["inputs changed"]
            self.assertEqual(conformance.main(["--allow-pending"]), 1)

    def test_absent_stale_malformed_or_partial_external_manifests_remain_pending(self):
        implementation = conformance.implementation_identity()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.json"
            values = [None,
                      {"schema_version":"ontokin.surface-release-evidence/0.1","implementation":{"source_code_sha256":"sha256:"+"0"*64}},
                      {"schema_version":"ontokin.surface-release-evidence/0.1","implementation":implementation}]
            for value in values:
                if value is not None:
                    write_json(path,value)
                report = conformance.verify_external_evidence(None if value is None else path, evidence_root=Path(directory))
                self.assertEqual([g["status"] for g in report["gates"]], ["pending"]*5)
                self.assertTrue(all(g["issues"] and not g["executed_external_tools"] for g in report["gates"]))
            path.write_text('{"schema_version":"a","schema_version":"b"}')
            report = conformance.verify_external_evidence(path, evidence_root=Path(directory))
            self.assertTrue(all(g["status"] == "pending" for g in report["gates"]))

    def test_evidence_path_hash_traversal_and_symlink_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); safe = root / "evidence"; safe.mkdir()
            outside = root / "outside.json"; outside.write_text('{}')
            local = safe / "local.json"; local.write_text('{}')
            good = {"path":"local.json","sha256":conformance.file_identity(local)}
            self.assertEqual(conformance._identified(good,safe),local)
            (safe / "escaped.json").symlink_to(outside)
            for record in ({**good,"sha256":"sha256:"+"0"*64}, {**good,"path":"../outside.json"},
                           {**good,"path":"escaped.json"}, {**good,"path":"./local.json"}):
                with self.assertRaises((ValueError,OSError)):
                    conformance._identified(record,safe)

    def test_independent_oracles_keep_native_cap_order_and_occurrence_palettes_separate(self):
        values=conformance._expected_fixtures()
        before=values["studio-original"]["oracle"]["shapes"]
        after=values["palette-repaired"]["oracle"]["shapes"]
        self.assertEqual(before[0]["materials"],after[0]["materials"])
        self.assertNotEqual(before[1]["materials"],after[1]["materials"])
        triangles=conformance._analytic_triangles(before[0])
        self.assertEqual([t[0] for t in triangles[64:80]],["clay"]*16)
        self.assertEqual([t[0] for t in triangles[80:96]],["paint"]*16)
        self.assertEqual([t[2] for t in triangles[64:80]],[[0.0,0.0,-1.0]]*16)
        self.assertEqual([t[2] for t in triangles[80:96]],[[0.0,0.0,1.0]]*16)

    def test_selected_case_ids_must_be_nonempty_and_adopted(self):
        for ids in ([], ["M00"], ["M13"], ["M01","C20"]):
            with self.assertRaises(ValueError):
                conformance.run_conformance(case_ids=ids)


class SurfaceConformanceRegressionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.implementation = {"name":"unit-test-retained-report","version":"test","source_code_sha256":"sha256:"+"1"*64}
        self.names = ["test_old.Case.test_kept", "test_new.Case.test_added"]
        self.inventory = [{"path":"tests/test_old.py","sha256":"sha256:"+"2"*64}]
        self.manifest = {"regression_required_test_ids":[self.names[0]]}
        self.report = {"schema_version":"ontokin.unittest-execution/0.1","executed":True,"implementation":self.implementation,
                       "evidence_stable_during_run":True,"evidence_files":self.inventory,
                       "evidence_inventory_sha256":conformance.inventory_identity(self.inventory),
                       "expected_test_ids":self.names,"test_execution":passed_execution(self.names),
                       "summary":{"total":2,"passed":2,"all_passed":True}}

    def test_complete_current_discovery_and_frozen_floor_are_both_required(self):
        with patch.object(conformance,"discover_test_ids",return_value=self.names):
            self.assertEqual(conformance._verify_full_suite(self.report,self.implementation,self.inventory,self.manifest),2)
        # A self-consistent smaller report cannot hide deletion of an older test.
        shortened = copy.deepcopy(self.report)
        shortened.update(expected_test_ids=[self.names[1]],test_execution=passed_execution([self.names[1]]),
                         summary={"total":1,"passed":1,"all_passed":True})
        with patch.object(conformance,"discover_test_ids",return_value=[self.names[1]]), \
             self.assertRaisesRegex(ValueError,"inherited frozen"):
            conformance._verify_full_suite(shortened,self.implementation,self.inventory,self.manifest)

    def test_skips_missing_methods_duplicate_results_and_stale_inventory_are_not_passes(self):
        edits = [lambda r:r.update(expected_test_ids=self.names[:1]),
                 lambda r:r["test_execution"]["tests"].pop(),
                 lambda r:r["test_execution"]["tests"].append(copy.deepcopy(r["test_execution"]["tests"][0])),
                 lambda r:r["test_execution"]["tests"][0].update(status="skipped"),
                 lambda r:r["test_execution"].update(fixture_errors=[{"failure":"setUpClass failed"}]),
                 lambda r:r.update(evidence_inventory_sha256="sha256:"+"0"*64),
                 lambda r:r.update(evidence_stable_during_run=False)]
        for edit in edits:
            with self.subTest(edit=edit):
                report = copy.deepcopy(self.report);edit(report)
                with patch.object(conformance,"discover_test_ids",return_value=self.names), self.assertRaises(ValueError):
                    conformance._verify_full_suite(report,self.implementation,self.inventory,self.manifest)

    def test_ci_commit_proof_reads_actual_git_tree_and_required_job_roles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/"ontokin").mkdir();source=root/"ontokin/source.py";source.write_text('value = 1\n')
            def git(*args):
                return subprocess.run(["git",*args],cwd=root,text=True,capture_output=True,check=True).stdout.strip()
            git("init","-q");git("config","user.name","Conformance fixture");git("config","user.email","fixture@example.invalid")
            git("add","ontokin/source.py");git("commit","-qm","fixed local test input")
            commit=git("rev-parse","HEAD")
            inventory=[{"path":"ontokin/source.py","sha256":conformance.file_identity(source)}]
            ci={"schema_version":"ontokin.surface-ci/0.1","implementation":self.implementation,
                "evidence_inventory_sha256":conformance.inventory_identity(inventory),"implementation_commit":commit,
                "workflow_run":{"id":42,"head_sha":commit,"status":"completed","conclusion":"success",
                                "html_url":"https://github.com/Omegapy/OntoKin/actions/runs/42"},
                "jobs":[{"id":i+1,"run_id":42,"name":"synthetic reader test "+v,"status":"completed","conclusion":"success",
                         "role":"python","python_version":v}for i,v in enumerate(("3.11","3.12","3.13"))]+
                       [{"id":4,"run_id":42,"name":"synthetic reader test visual","status":"completed","conclusion":"success",
                         "role":"visual","python_version":None}]}
            path=root/"ci.json";record=write_json(path,ci)
            with patch.object(conformance,"ROOT",root):
                result=conformance._verify_ci(record,root,self.implementation,inventory)
                self.assertEqual(result["implementation_commit"],commit)
                for edit in (lambda c:c["jobs"].pop(),lambda c:c["jobs"][0].update(conclusion="skipped"),
                             lambda c:c["jobs"][0].update(run_id=99),lambda c:c["workflow_run"].update(head_sha="0"*40),
                             lambda c:c["jobs"][0].update(python_version="3.13")):
                    changed=copy.deepcopy(ci);edit(changed);record=write_json(path,changed)
                    with self.assertRaises(ValueError):
                        conformance._verify_ci(record,root,self.implementation,inventory)
                source.write_text('value = 2\n')
                changed_inventory=[{"path":"ontokin/source.py","sha256":conformance.file_identity(source)}]
                ci["evidence_inventory_sha256"]=conformance.inventory_identity(changed_inventory)
                record=write_json(path,ci)
                with self.assertRaisesRegex(ValueError,"CI commit tree differs"):
                    conformance._verify_ci(record,root,self.implementation,changed_inventory)
                source.write_text('value = 1\n')
                extra=root/"ontokin/removed.py";extra.write_text("previous = True\n")
                git("add","ontokin/removed.py");git("commit","-qm","extra committed runtime input")
                ci["implementation_commit"]=git("rev-parse","HEAD")
                ci["workflow_run"]["head_sha"]=ci["implementation_commit"]
                ci["evidence_inventory_sha256"]=conformance.inventory_identity(inventory)
                extra.unlink()
                record=write_json(path,ci)
                with self.assertRaisesRegex(ValueError,"input path set differs"):
                    conformance._verify_ci(record,root,self.implementation,inventory)


class SurfaceConformanceWorkflowEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.build_surface_agent_demo import Workflow
        from tools.build_surface_demo import fixture_cases
        cls.temporary = tempfile.TemporaryDirectory(prefix="ontokin-conformance-source-witness-")
        cls.root = Path(cls.temporary.name)
        cls.output = cls.root / "original"
        workflow = Workflow(cls.output)
        _, bundle, oracle = next(fixture_cases())
        try:
            workflow.studio(bundle, oracle)
        except BaseException as error:
            workflow.finish(error)
            raise
        cls.report = workflow.finish()
        # This private reader witness exercises M07/M08 source records only.
        # Public run_conformance always loads the hashed complete 22-fixture map.
        cls.manifest = copy.deepcopy(conformance.load_manifest())
        cls.manifest["mandatory_native_fixtures"] = ["studio-original","radius-repaired","palette-repaired","inserted","reordered","removed"]
        cls.manifest["mandatory_workflow_checks"] = ["M07-radius-repair","M07-palette-repair","M08-topology-edits"]
        cls.record = {"path":"workflow.json","sha256":conformance.file_identity(cls.output/"workflow.json")}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def verify(self,root,record):
        context={}
        result=conformance._verify_workflow(record,root,self.report["implementation"],self.manifest,context)
        self.assertIn("workflow",context)
        return result

    def test_actual_source_workflow_replays_patches_snapshots_pages_and_retrieved_artifacts(self):
        result=self.verify(self.output,self.record)
        self.assertEqual(result["retrieved_artifacts"],6)
        self.assertGreater(result["exchanges"],100)
        self.assertEqual(result["snapshots"],6)  # removed returns an earlier exact revision
        self.assertEqual(result["accepted_revisions"],5)

    def changed(self,label,edit):
        root=self.root/label;shutil.copytree(self.output,root)
        report=json.loads((root/"workflow.json").read_text())
        edit(root,report)
        record=write_json(root/"workflow.json",report)
        return root,record

    def test_rehashed_accepted_candidate_claim_and_missing_mesh_pages_are_rejected(self):
        def accept_invalid(root,report):
            invalid=next(s for s in report["snapshots"] if not s["accepted_once"])
            invalid["accepted_once"]=True
        def remove_page(root,report):
            item=next(x for x in report["exchanges"] if x["operation"]=="surface.mesh_page" and
                      json.loads((root/x["response_file"]).read_text())["status"]=="succeeded")
            report["exchanges"].remove(item)
            for check in report["checks"]:
                check["evidence_request_ids"]=[i for i in check["evidence_request_ids"] if i != item["request_id"]]
        for label,edit in (("accepted-invalid",accept_invalid),("missing-page",remove_page)):
            root,record=self.changed(label,edit)
            with self.subTest(label=label),self.assertRaises((ValueError,KeyError)):
                self.verify(root,record)

    def test_rehashed_artifact_chunk_and_triangle_coordinates_cannot_forge_source_delivery(self):
        def alter_response(root,report,operation,edit):
            item=next(x for x in report["exchanges"] if x["operation"]==operation and
                      json.loads((root/x["response_file"]).read_text())["status"]=="succeeded")
            path=root/item["response_file"];response=json.loads(path.read_text());edit(response["result"])
            write_json(path,response);item["response_sha256"]=conformance.file_identity(path)
        edits=[("bad-chunk",lambda r,m:alter_response(r,m,"artifact",lambda p:p.update(data_base64="YQ=="))),
               ("bad-point",lambda r,m:alter_response(r,m,"surface.mesh_page",lambda p:p["positions_m"][0].__setitem__(0,50.0)))]
        for label,edit in edits:
            root,record=self.changed(label,edit)
            with self.subTest(label=label),self.assertRaises(ValueError):
                self.verify(root,record)

    def test_raw_source_and_relabelled_revision_tampering_break_provenance(self):
        def change_raw(root,report):
            file=root/report["snapshots"][0]["units"][0]["file"]
            file.write_bytes(file.read_bytes()+b'\n// changed\n')
        def wrong_revision(root,report):
            report["artifacts"][1]["program_revision"]=report["artifacts"][0]["program_revision"]
        for label,edit in (("raw-source",change_raw),("wrong-revision",wrong_revision)):
            root,record=self.changed(label,edit)
            with self.subTest(label=label),self.assertRaises(ValueError):
                self.verify(root,record)


class SurfaceConformanceNativeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import math
        from ontokin.construction import compile_construction
        from ontokin.gltf import export_glb
        cls.temporary=tempfile.TemporaryDirectory(prefix="ontokin-conformance-native-witness-")
        cls.root=Path(cls.temporary.name)
        expected=conformance._expected_fixtures()["cylinder"]
        cls.program=expected["program"];cls.shape=expected["oracle"]["shapes"][0]
        compiled=compile_construction(cls.program,level="evaluated")
        exported=export_glb(compiled.model,target_contract="ontokin.glb/0.3")
        (cls.root/"scene.glb").write_bytes(exported.data)
        cls.document,cls.binary=conformance._glb(cls.root/"scene.glb")
        primitive=cls.document["meshes"][0]["primitives"][0]
        positions=conformance._accessor(cls.document,cls.binary,primitive["attributes"]["POSITION"])
        normals=conformance._accessor(cls.document,cls.binary,primitive["attributes"]["NORMAL"])
        indices=conformance._accessor(cls.document,cls.binary,primitive["indices"])
        triangles=conformance._analytic_triangles(cls.shape)
        # This is a synthetic retained-record shape for testing the independent
        # Python binary reader; it does not claim a Khronos/Three.js execution.
        error=max(abs(positions[index][axis]-point[axis]) for i,(_,points,_) in enumerate(triangles)
                  for index,point in zip(indices[3*i:3*i+3],points)for axis in range(3))
        cls.record={"path":"shell","triangles":64,"vertices":192,"ordered_keys":["z-base","a-top"],
                    "local_placement_applied_once":True,"max_local_float32_error_m":error,
                    "max_float32_normal_length_error":max(abs(math.hypot(*n)-1)for n in normals),
                    "positions_sha256":conformance.digest(cls.binary),"topology_sha256":conformance.digest(cls.binary),
                    "regions":[{"region":"blue","triangles":64,"material_index":primitive["material"],
                                **cls.shape["materials"]["blue"]}]}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def verify(self,document=None,binary=None,record=None):
        conformance._verify_geometry(document or self.document,self.binary if binary is None else binary,
                                     self.shape,record or self.record,self.program.program_revision,self.program)

    def test_real_native_glb_matches_independent_source_points_normals_winding_and_pbr(self):
        self.verify()
        triangles=conformance._analytic_triangles(self.shape)
        self.assertEqual(len(triangles),64)
        self.assertTrue(all(p[2]==0 for _,points,_ in triangles[32:48]for p in points))
        self.assertTrue(all(p[2]==2 for _,points,_ in triangles[48:64]for p in points))

    def test_changed_real_bin_vertices_normals_and_winding_are_detected(self):
        import struct
        primitive=self.document["meshes"][0]["primitives"][0]
        for semantic in ("POSITION","NORMAL"):
            with self.subTest(semantic=semantic):
                accessor=self.document["accessors"][primitive["attributes"][semantic]]
                view=self.document["bufferViews"][accessor["bufferView"]]
                offset=view.get("byteOffset",0)+accessor.get("byteOffset",0)
                changed=bytearray(self.binary);struct.pack_into("<f",changed,offset,50.)
                with self.assertRaises(ValueError):self.verify(binary=changed)
        accessor=self.document["accessors"][primitive["indices"]]
        view=self.document["bufferViews"][accessor["bufferView"]]
        offset=view.get("byteOffset",0)+accessor.get("byteOffset",0)
        code={5123:"H",5125:"I"}[accessor["componentType"]]
        changed=bytearray(self.binary);a,b=struct.unpack_from("<"+code*2,changed,offset)
        struct.pack_into("<"+code*2,changed,offset,b,a)
        with self.assertRaises(ValueError):self.verify(binary=changed)

    def test_material_source_mapping_and_weak_tolerance_claims_are_rejected(self):
        for edit in (lambda d:d["materials"][0]["pbrMetallicRoughness"].update(metallicFactor=.99),
                     lambda d:d["materials"][0]["extras"]["ontokin"].update(source_region_key="other"),
                     lambda d:d["nodes"][0]["extras"]["ontokin"]["source_mapping"]["definition"].update(start_byte=999999)):
            changed=copy.deepcopy(self.document);edit(changed)
            with self.assertRaises(ValueError):self.verify(document=changed)
        changed=copy.deepcopy(self.record);changed["max_local_float32_error_m"]=.01
        with self.assertRaises(ValueError):self.verify(record=changed)

    def test_native_destination_cannot_pass_without_the_actual_workflow_link(self):
        result=conformance._gate("destination",lambda:conformance._verify_destination({},self.root,{},conformance.load_manifest(),{}))
        self.assertEqual(result["status"],"pending")
        self.assertIn("verified source workflow",result["issues"][0])

    def test_destination_link_rejects_relabelled_lookalike_program_and_changed_artifact(self):
        path=self.root/"scene.glb";sha=conformance.file_identity(path);size=path.stat().st_size
        revision=self.program.program_revision
        delivered={"project_id":"synthetic-link-witness","program_revision":revision,"artifact_sha256":sha,"byte_length":size}
        context={"workflow":{"artifacts":{"cylinder":delivered},
                             "snapshots":{("synthetic-link-witness",revision):(self.program,True)}}}
        conformance._verify_delivery_link("cylinder",self.program,sha,size,context)
        for edit in (lambda d:d.update(artifact_sha256="sha256:"+"0"*64),lambda d:d.update(byte_length=size+4)):
            changed=copy.deepcopy(context);edit(changed["workflow"]["artifacts"]["cylinder"])
            with self.assertRaisesRegex(ValueError,"artifact retrieved"):
                conformance._verify_delivery_link("cylinder",self.program,sha,size,changed)
        lookalike=conformance.ProgramBundle(conformance.SourceUnit("entry",self.program.entry.filename,
                            self.program.entry.raw+b"\n// geometry-identical different source revision\n"),self.program.modules)
        with self.assertRaisesRegex(ValueError,"accepted workflow snapshot"):
            conformance._verify_delivery_link("cylinder",lookalike,sha,size,context)
        context["workflow"]["snapshots"][("synthetic-link-witness",revision)]=(self.program,False)
        with self.assertRaisesRegex(ValueError,"accepted workflow snapshot"):
            conformance._verify_delivery_link("cylinder",self.program,sha,size,context)

    def test_release_motion_oracle_uses_independent_gravity_after_the_fixed_release(self):
        fixture=conformance._expected_fixtures()["rotated-release"]["oracle"]
        falling=next(s for s in fixture["shapes"]if s["path"]=="rig.falling")
        held=next(s for s in fixture["shapes"]if s["path"]=="rig.held")
        self.assertEqual(conformance._expected_pose(falling,.5)["position_m"],[.5,2.5,0.])
        self.assertEqual(conformance._expected_pose(falling,1.5)["position_m"],[1.5,1.25,0.])
        self.assertEqual(conformance._expected_pose(falling,2)["position_m"],[2.,-2.5,0.])
        self.assertNotEqual(conformance._expected_pose(falling,2)["position_m"],conformance._expected_pose(held,2)["position_m"])
        self.assertNotEqual(falling["local_rotation_wxyz"],falling["motion"]["rotation_wxyz"])


class SurfaceConformanceBrowserEvidenceTests(unittest.TestCase):
    def test_browser_numeric_capture_and_visual_review_requirements_remain_independent(self):
        # A reduced private-reader fixture tests the report contract. Public
        # conformance always uses four fixed browser fixtures and 12 captures.
        import zlib,struct
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/"surface-viewer.html").write_text("synthetic browser reader unit fixture")
            manifest=copy.deepcopy(conformance.load_manifest());manifest["mandatory_browser_fixtures"]=["cylinder"]
            expected=conformance._expected_fixtures()["cylinder"]
            program=expected["program"];oracle=expected["oracle"]
            identity=conformance.implementation_identity();artifact="sha256:"+"7"*64
            source={"fixture":"cylinder","program_revision":program.program_revision,"artifact_sha256":artifact,
                    "provenance":{},"exporter_source_code_sha256":identity["source_code_sha256"][7:]}
            context={"destination":{"cylinder":{"program_revision":program.program_revision,"artifact_sha256":artifact,"provenance":{},"oracle":oracle}}}
            def objects(time):
                p=conformance._expected_pose(oracle["shapes"][0],time);w,x,y,z=p["orientation_wxyz"]
                return {"shell":{"position_m":p["position_m"],"orientation_xyzw":[x,y,z,w],"probes":[],
                                 "position_error_m":0.,"rotation_error_rad":0.}}
            def chunk(kind,data):
                return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data))
            captures=[];reviews=[]
            for i,item in enumerate(manifest["mandatory_browser_captures"]):
                raw=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",8,8,8,2,0,0,0))+chunk(b"tEXt",b"unit fixture\0"+bytes([65+i])*80)+chunk(b"IDAT",zlib.compress((b"\0"+bytes([i*40,0,0])*8)*8))+chunk(b"IEND",b"")
                file=root/f"capture-{i}.png";file.write_bytes(raw);sha=conformance.file_identity(file)
                captures.append({"fixture":"cylinder","file":file.name,"sha256":sha,"program_revision":program.program_revision,
                                 "artifact_sha256":artifact,"objects":objects(item["time_seconds"]),**item})
                reviews.append({"capture_sha256":sha,"status":"reviewed","reviewer":"synthetic reader fixture",
                                "observation":"Synthetic unit-test record; no actual browser execution is claimed."})
            times=[float(t)for t in conformance._json_file(conformance.FIXTURES/"compositions/expected.json")["sample_times_seconds"]]
            browser={"schema_version":"ontokin.surface-native-browser-validation/0.1","status":"passed",
                     "verifier_sha256":conformance.file_identity(conformance.ROOT/"tools/verify_surface_viewer.mjs"),
                     "tooling_lock_sha256":conformance.file_identity(conformance.ROOT/"tools/package-lock.json"),
                     "harness_sha256":conformance.file_identity(root/"surface-viewer.html"),"browser":"synthetic fixture",
                     "webgl":{"synthetic":True},"environment":{"synthetic":True},"page_errors":[],"console_errors":[],"failed_requests":[],"network_requests":[],
                     "source_fixtures":[source],"samples":[{"fixture":"cylinder","time_seconds":t,"objects":objects(t)}for t in times],
                     "captures":captures,"playback":[{"fixture":"cylinder","started_at_seconds":.5,"paused_at_seconds":.6,"stable_across_frames":True}],
                     "world_pose_comparisons":7}
            path=root/"browser.json";native={"browser":write_json(path,browser),"visual_reviews":reviews}
            self.assertEqual(conformance._verify_browser(native,root,identity,manifest,context)["reviewed_captures"],3)
            edits=[lambda b:b["captures"].pop(),lambda b:b["captures"][2]["objects"]["shell"]["position_m"].__setitem__(0,5),
                   lambda b:b["source_fixtures"][0].update(artifact_sha256="sha256:"+"0"*64),lambda b:b["samples"].pop(),
                   lambda b:b.update(world_pose_comparisons=999),lambda b:b["console_errors"].append("render failed")]
            for edit in edits:
                changed=copy.deepcopy(browser);edit(changed);native["browser"]=write_json(path,changed)
                with self.assertRaises(ValueError):conformance._verify_browser(native,root,identity,manifest,context)
            native["browser"]=write_json(path,browser);native["visual_reviews"]=reviews[:-1]
            with self.assertRaisesRegex(ValueError,"visual review"):
                conformance._verify_browser(native,root,identity,manifest,context)
            # Rehash both the report and review after corrupting the PNG. The
            # file parser, not a stale outer hash, must reject the fake capture.
            malformed=root/browser["captures"][0]["file"]
            malformed.write_bytes(b"\x89PNG\r\n\x1a\n"+b"truncated chunk"*20)
            changed=copy.deepcopy(browser);changed["captures"][0]["sha256"]=conformance.file_identity(malformed)
            native["browser"]=write_json(path,changed);native["visual_reviews"]=copy.deepcopy(reviews)
            native["visual_reviews"][0]["capture_sha256"]=changed["captures"][0]["sha256"]
            with self.assertRaisesRegex(ValueError,"PNG"):
                conformance._verify_browser(native,root,identity,manifest,context)


if __name__ == "__main__":
    unittest.main()
