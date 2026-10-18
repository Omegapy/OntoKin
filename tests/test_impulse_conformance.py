"""Adversarial checks for actual impulse execution and evidence acceptance."""
from __future__ import annotations

import copy
from contextlib import redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import impulse_conformance as gate
from ontokin.diagnostics import OntoKinError


class ImpulseConformanceReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = gate.load_manifest()
        cls.cases = {c["id"]:c for c in cls.contract["acceptance"]["source_cases"]}

    def test_all_frozen_sources_hashes_and_spans_are_loaded(self):
        self.assertEqual(40,len(self.cases))
        for case in self.cases.values():
            with self.subTest(case=case["id"]):
                self.assertEqual(case["program_revision"],gate.fixture_bundle(case).program_revision)

    def test_changed_acceptance_is_rejected_even_with_pass_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)
            data=copy.deepcopy(self.contract["acceptance"])
            data["status"]="passed"
            (path/"acceptance.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"adopted impulse expectations changed"):
                gate.load_manifest(path)

    def test_source_revision_and_statement_span_are_not_self_asserted(self):
        case=copy.deepcopy(self.cases["P01"])
        case["source_impulse_statements"][0]["source_location"]["end_byte"]-=1
        with self.assertRaisesRegex(ValueError,"exact source span"):
            gate.fixture_bundle(case)
        case=copy.deepcopy(self.cases["P01"])
        case["program_revision"]="sha256:"+"0"*64
        with self.assertRaisesRegex(ValueError,"Fixture bytes"):
            gate.fixture_bundle(case)

    def test_exact_decimal_boundary_and_side_cannot_be_relabelled(self):
        expected=self.cases["P15"]["expected"]["samples"][-1]
        actual={"time_seconds":"0.1","side":"after","objects":{}}
        with self.assertRaisesRegex(ValueError,"exact requested timestamp"):
            gate.compare_sample(actual,expected)
        actual["time_seconds"]=expected["time_seconds"]
        actual["side"]="before"
        with self.assertRaisesRegex(ValueError,"boundary side"):
            gate.compare_sample(actual,expected)

    def test_high_spin_orientation_does_not_pass_from_regular_sample_alias(self):
        expected=self.cases["P11"]["expected"]["samples"][1]
        actual={"time_seconds":expected["time_seconds"],"side":expected["side"],"objects":copy.deepcopy(expected["objects"])}
        gate.compare_sample(actual,expected)
        actual["objects"]["ball"]["orientation_wxyz"]=[1,0,0,0]
        with self.assertRaisesRegex(ValueError,"Orientation geodesic error"):
            gate.compare_sample(actual,expected)

    def test_extreme_cancellation_zero_cannot_hide_inside_relative_tolerance(self):
        expected=self.cases["P12"]["expected"]["samples"][-1]
        actual={"time_seconds":"2","side":"after","objects":copy.deepcopy(expected["objects"])}
        gate.compare_sample(actual,expected,exact_extreme=True)
        actual["objects"]["ball"]["position_m"][0]=1e292
        with self.assertRaisesRegex(ValueError,"position_m"):
            gate.compare_sample(actual,expected,exact_extreme=True)

    def test_positive_case_requires_actual_compiler_execution(self):
        with patch.object(gate,"compile_construction",side_effect=OntoKinError("OKL-E-CAPABILITY-UNSUPPORTED","disabled")) as compile_mock:
            result=gate.execute_source_case(self.cases["P01"])
        compile_mock.assert_called_once()
        self.assertTrue(result["executed"])
        self.assertEqual("failed",result["status"])
        self.assertNotIn("samples",result)

    def test_native_positive_result_retains_json_physical_state(self):
        result=gate.execute_source_case(self.cases["P02"])
        self.assertEqual("passed",result["status"],result["issues"])
        json.dumps(result,allow_nan=False)
        self.assertNotIn("geometry",result["samples"][0]["objects"]["ball"])
        self.assertIn("impulses",result["samples"][1]["objects"]["ball"])

    def test_runtime_negative_cannot_pass_from_early_same_code_rejection(self):
        with patch.object(gate,"compile_construction",side_effect=OntoKinError("OKL-E-MOTION-MODE","too early")):
            result=gate.execute_source_case(self.cases["N06"])
        self.assertEqual("failed",result["status"])
        self.assertTrue(any("before its required runtime" in e for e in result["issues"]))

    def test_application_diagnostic_needs_exact_time_target_span_and_index(self):
        case=self.cases["N15"]
        bundle=gate.fixture_bundle(case)
        event=case["source_impulse_statements"][0]
        location=event["source_location"]
        node=SimpleNamespace(source_id="entry",start=location["start_byte"],end=location["end_byte"])
        error=OntoKinError("OKL-E-NUMERIC","synthetic shape probe",node,category="numerical_failure",phase="transition",
                           time=Fraction(1),side="after",element_id=["impulse-demo","demo","ball"],details={"sequence_index":0})
        gate._error_check(error,case,bundle)
        error.diagnostic.time=Fraction(2)
        with self.assertRaisesRegex(ValueError,"actual event time"):
            gate._error_check(error,case,bundle)

    def test_absent_and_stale_external_records_remain_pending(self):
        result=gate.verify_external_evidence()
        self.assertEqual(list(gate.GATES),[g["id"] for g in result["gates"]])
        self.assertTrue(all(g["status"]=="pending" for g in result["gates"]))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"evidence.json"
            path.write_text(json.dumps({"schema_version":"ontokin.impulse-release-evidence/0.1","implementation":{}}))
            stale=gate.verify_external_evidence(path)
            self.assertTrue(all(g["status"]=="pending" for g in stale["gates"]))

    def test_inventory_contains_adopted_sources_and_new_profile_schemas(self):
        paths={r["path"] for r in gate.evidence_inventory()}
        self.assertIn("docs/language-design/impulse-v0.1/adoption.json",paths)
        self.assertIn("docs/language-design/impulse-v0.1/grammar.ebnf",paths)
        self.assertIn("docs/language-design/impulse-v0.1/sources/p11-high-spin-low-fps.ok",paths)
        self.assertIn("ontokin/impulse_conformance.py",paths)
        self.assertIn("examples/visual/viewer.js",paths)
        self.assertTrue(gate._inventory_path("docs/language-design/agent-v0.4/request.schema.json"))
        self.assertFalse(gate._inventory_path("docs/language-design/impulse-v0.1/evidence/report.json"))

    def test_required_execution_records_are_exact_not_count_only(self):
        name="test_x.Y.test_z"
        record={"unique_required":1,"tests_run":1,"tests":[{"test_id":name,"status":"passed","failures":[]}],
                "outcomes":{"passed":1},"loader_errors":[],"fixture_errors":[],"unexpected_test_records":[]}
        self.assertTrue(gate._execution_passes(record,[name]))
        record["tests"][0]["test_id"]="test_x.Y.test_other"
        self.assertFalse(gate._execution_passes(record,[name]))
        record["tests"]=[]
        self.assertFalse(gate._execution_passes(record,[name]))


def _execution(names):
    """Synthetic private-reader input, never an actual release execution claim."""
    return {"unique_required":len(names),"tests_run":len(names),
            "tests":[{"test_id":n,"status":"passed","failures":[]} for n in names],
            "outcomes":{"passed":len(names)},"loader_errors":[],"fixture_errors":[],"unexpected_test_records":[]}


class ImpulseWorkflowEvidenceTests(unittest.TestCase):
    """Real source/service exchanges; A03 complements below are test-shape data."""
    @classmethod
    def setUpClass(cls):
        from tools.build_impulse_agent_demo import build
        cls.directory=tempfile.TemporaryDirectory()
        cls.base=Path(cls.directory.name)/"real-workflow"
        with redirect_stdout(io.StringIO()):
            cls.report=build(cls.base)
        cls.contract=gate.load_manifest()

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/"retained"
        shutil.copytree(self.base,self.root,ignore=shutil.ignore_patterns("service-store"))
        self.report=copy.deepcopy(type(self).report)

    def audit(self, execution="synthetic-shape"):
        path=self.root/"workflow.json"
        path.write_text(json.dumps(self.report,allow_nan=False))
        tests=_execution(gate._A03_TESTS) if execution=="synthetic-shape" else execution
        context={}
        result=gate._verify_workflow({"path":"workflow.json","sha256":gate.file_identity(path)},self.root,
            self.report["implementation"],self.contract,context,tests)
        return result,context

    def replace_exchange_json(self, exchange, kind, mutation):
        path=self.root/exchange[kind+"_file"]
        value=json.loads(path.read_text())
        mutation(value)
        path.write_text(json.dumps(value,allow_nan=False))
        exchange[kind+"_sha256"]=gate.file_identity(path)

    def test_complete_actual_workflow_requires_all_sources_states_and_retrieved_bytes(self):
        result,_=self.audit()
        self.assertEqual((16,9,308,306),(result["positive_fixtures"],result["retrieved_artifacts"],
                         result["exchange_attempts"],result["unique_requests"]))
        self.assertEqual("partial",result["A03_basis"]["workflow_status"])

    def test_pass_labels_cannot_replace_actual_scoped_source_repairs(self):
        fixture=next(f for f in self.report["fixtures"] if f["fixture"]=="P09")
        fixture["edit_request_ids"]=[]
        with self.assertRaisesRegex(ValueError,"single actual scoped source patch"):
            self.audit()

    def test_writable_repair_scope_requires_exact_program_source_and_file_identity(self):
        fixture=next(f for f in self.report["fixtures"] if f["fixture"]=="P09")
        exchange=next(e for e in self.report["exchanges"] if e["request_id"] in fixture["inspect_request_ids"]
                      and "source" in json.loads((self.root/e["request_file"]).read_text()).get("fields",[]))
        path=self.root/exchange["response_file"]
        original=json.loads(path.read_text())
        for owner,field,value in (("source","program_revision","sha256:"+"0"*64),
            ("source","source_id","package:fixture.surface-parts@1.0.0"),
            ("source","source_revision","sha256:"+"0"*64),
            ("span","source_id","package:fixture.surface-parts@1.0.0"),
            ("span","source_revision","sha256:"+"0"*64),("span","file","other.ok")):
            response=copy.deepcopy(original)
            source=response["result"]["items"][0]["source"]
            target=source if owner=="source" else source["writable_spans"][0]
            target[field]=value
            path.write_text(json.dumps(response,allow_nan=False))
            exchange["response_sha256"]=gate.file_identity(path)
            with self.subTest(owner=owner,field=field),self.assertRaisesRegex(ValueError,"exact-source writable occurrence"):
                self.audit()

    def test_historical_scope_read_after_edit_cannot_authorize_the_earlier_patch(self):
        fixture=next(f for f in self.report["fixtures"] if f["fixture"]=="P09")
        scope=next(e for e in self.report["exchanges"] if e["request_id"] in fixture["inspect_request_ids"]
                   and "source" in json.loads((self.root/e["request_file"]).read_text()).get("fields",[]))
        edit=next(e for e in self.report["exchanges"] if e["request_id"]==fixture["accepted_request_id"])
        scope["sequence"],edit["sequence"]=edit["sequence"],scope["sequence"]
        self.report["exchanges"].sort(key=lambda e:e["sequence"])
        # A historical inspection is otherwise valid with the newer accepted
        # head. It cannot retroactively establish scope for that earlier edit.
        self.replace_exchange_json(scope,"response",lambda r:r.update(accepted_program_revision=fixture["program_revision"]))
        with self.assertRaisesRegex(ValueError,"inspection before its patch"):
            self.audit()

    def test_retained_history_cannot_invent_a_locally_consistent_staged_velocity(self):
        fixture=next(f for f in self.report["fixtures"] if f["fixture"]=="P05")
        exchange=next(e for e in self.report["exchanges"] if e["request_id"]==fixture["inspect_request_ids"][1])
        def mutate(response):
            record=response["result"]["items"][0]["state"]["impulses"]["last_applications"][0]
            for name in ("linear_velocity_before_world_m_per_s","linear_velocity_after_world_m_per_s"):
                record[name][0]=43
        self.replace_exchange_json(exchange,"response",mutate)
        with self.assertRaisesRegex(ValueError,"Retained staged incoming linear velocity"):
            self.audit()

    def test_evaluation_only_impulse_record_uses_its_actual_application_pose(self):
        fixture=next(f for f in self.report["fixtures"] if f["fixture"]=="P05")
        exchange=next(e for e in self.report["exchanges"] if e["request_id"]==fixture["inspect_request_ids"][1])
        original=json.loads((self.root/exchange["response_file"]).read_text())
        for field in ("lever_arm_world_m","application_point_world_m"):
            response=copy.deepcopy(original)
            response["result"]["items"][0]["state"]["impulses"]["last_applications"][0][field][0]=43
            path=self.root/exchange["response_file"]
            path.write_text(json.dumps(response,allow_nan=False))
            exchange["response_sha256"]=gate.file_identity(path)
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"Retained application-time world"):
                self.audit()

    def test_later_retained_copy_cannot_change_an_already_checked_application(self):
        fixture=next(f for f in self.report["fixtures"] if f["fixture"]=="P05")
        exchange=next(e for e in self.report["exchanges"] if e["request_id"]==fixture["inspect_request_ids"][-1])
        self.replace_exchange_json(exchange,"response",lambda r:r["result"]["items"][0]["state"]["impulses"]["last_applications"][0]
                                   ["application_point_world_m"].__setitem__(0,43))
        with self.assertRaisesRegex(ValueError,"history copy changed"):
            self.audit()

    def test_nonworld_inspection_requires_complete_inherited_velocity_and_orientation_conversion(self):
        check=next(c for c in self.report["checks"] if c["id"]=="A05")
        exchange=next(e for e in self.report["exchanges"] if e["request_id"] in check["evidence_request_ids"]
                      and json.loads((self.root/e["request_file"]).read_text()).get("frame")=="ball.frame")
        path=self.root/exchange["response_file"]
        original=json.loads(path.read_text())
        for field,value in (("orientation_wxyz",[0,1,0,0]),("velocity_m_per_s",[43,0,0]),
                            ("angular_velocity_rad_per_s",[43,0,0]),("velocity_measured_in","ball.frame")):
            response=copy.deepcopy(original)
            response["result"]["items"][0]["state"][field]=value
            path.write_text(json.dumps(response,allow_nan=False))
            exchange["response_sha256"]=gate.file_identity(path)
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"A05|Orientation geodesic error"):
                self.audit()

    def test_rejected_snapshot_cannot_be_relabelled_as_accepted_once(self):
        next(s for s in self.report["snapshots"] if not s["accepted_once"])["accepted_once"]=True
        with self.assertRaisesRegex(ValueError,"accepted_once was inferred"):
            self.audit()

    def test_identical_retry_attempt_cannot_be_omitted_from_passed_ledger(self):
        a02=next(c for c in self.report["checks"] if c["id"]=="A02")
        remove=a02["details"]["retry_sequences"][1]
        self.report["exchanges"]=[e for e in self.report["exchanges"] if e["sequence"]!=remove]
        with self.assertRaisesRegex(ValueError,"identical failed-admission retry"):
            self.audit()

    def test_missing_retrieval_chunk_fails_even_after_rehashing_the_report(self):
        self.report["artifacts"][0]["retrieval_request_ids"].pop(0)
        with self.assertRaisesRegex(ValueError,"Artifact chunks"):
            self.audit()

    def test_rehashed_extreme_readback_still_uses_exact_frozen_cancellation(self):
        fixture=next(f for f in self.report["fixtures"] if f["fixture"]=="P12")
        identity=fixture["inspect_request_ids"][-1]
        exchange=next(e for e in self.report["exchanges"] if e["request_id"]==identity)
        self.replace_exchange_json(exchange,"response",lambda r:r["result"]["items"][0]["state"]["position_m"].__setitem__(0,1e292))
        with self.assertRaisesRegex(ValueError,"position_m"):
            self.audit()

    def test_malformed_selected_protocol_request_is_a_controlled_audit_failure(self):
        exchange=next(e for e in self.report["exchanges"] if e["operation"]=="inspect")
        self.replace_exchange_json(exchange,"request",lambda r:r.update(impulse=[0,1,0]))
        with self.assertRaisesRegex(ValueError,"selected Agent/0.4 protocol"):
            self.audit()

    def test_public_mesh_capability_cannot_be_relabelled_as_entry_profile(self):
        exchange=next(e for e in self.report["exchanges"] if e["operation"]=="surface.mesh_page")
        self.replace_exchange_json(exchange,"response",lambda r:r["result"].update(profile="impulse-0.1"))
        with self.assertRaisesRegex(ValueError,"inherited capability"):
            self.audit()

    def test_real_workflow_remains_partial_without_actual_a03_test_complements(self):
        with self.assertRaisesRegex(ValueError,"A03 remains partial"):
            self.audit(execution=None)


class ImpulseDestinationEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=gate.load_manifest()
        cls.case=next(c for c in cls.contract["acceptance"]["source_cases"] if c["id"]=="P02")
        cls.program=gate.fixture_bundle(cls.case)

    def boundary_fixture(self):
        model=gate.compile_construction(self.program,level="constructed").model
        values=gate.evaluate(model,[{"time_seconds":t,"side":"after"} for t in ("0","1","2")])["samples"]
        samples={(Fraction(v["time_seconds"]),v["side"]):v for v in values}
        metadata={"impulse_profile":{"source_impulses":"instantaneous_world_momentum_at_target_self_point",
                                      "continuous_external_torques":"absent"},
            "boundary_states":[{"source_seconds":v["time_seconds"],"joint_states_after":v["joints"],"action_states_after":v["actions"],
                "pose_authorities_after":{p:s["pose_authority"] for p,s in v["objects"].items()},
                "impulse_states_after":{p:s["impulses"] for p,s in v["objects"].items()}} for v in values]}
        return copy.deepcopy(metadata),samples

    def test_retained_impulse_is_checked_at_original_application_pose(self):
        metadata,samples=self.boundary_fixture()
        record={"status":"passed","boundary_count":3,"retained_application_comparisons":2}
        self.assertEqual(2,gate._verify_impulse_boundaries(metadata,self.case,self.program,samples,record))
        state=samples[(Fraction(2),"after")]["objects"]["ball"]
        self.assertNotEqual([1,0,0,0],state["orientation_wxyz"])
        self.assertEqual([.5,0.,0.],state["impulses"]["last_applications"][0]["lever_arm_world_m"])

    def test_missing_changed_and_truncated_boundary_history_are_rejected(self):
        original,samples=self.boundary_fixture()
        record={"status":"passed","boundary_count":3,"retained_application_comparisons":2}
        for kind in ("missing","changed","truncated"):
            metadata=copy.deepcopy(original)
            state=metadata["boundary_states"][2]["impulse_states_after"]
            if kind=="missing": state.pop("ball")
            elif kind=="changed": state["ball"]["last_applications"][0]["source_location"]["start_byte"]+=1
            else: state["ball"]["last_applications"]=[]
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,"complete source impulse projection"):
                gate._verify_impulse_boundaries(metadata,self.case,self.program,samples,record)

    @staticmethod
    def clock_fixture(times):
        """Minimal synthetic accessor data for the clock reader, not a source GLB."""
        document={"nodes":[{"extras":{"ontokin":{"path":"ball"}}}],"scenes":[{"nodes":[0]}],
                  "buffers":[{}],"bufferViews":[],"accessors":[]}
        raw=bytearray()
        def accessor(values,width):
            start=len(raw)
            for value in values:
                raw.extend(struct.pack("<"+"f"*width,*([value] if width==1 else value)))
            document["bufferViews"].append({"buffer":0,"byteOffset":start,"byteLength":len(raw)-start})
            document["accessors"].append({"bufferView":len(document["bufferViews"])-1,"componentType":5126,
                "count":len(values),"type":{1:"SCALAR",3:"VEC3",4:"VEC4"}[width]})
            return len(document["accessors"])-1
        clock=accessor(times,1)
        poses=[gate._expected_pose("P11","ball",t) for t in times]
        position=accessor([p["position_m"] for p in poses],3)
        rotation=accessor([[*p["orientation_wxyz"][1:],p["orientation_wxyz"][0]] for p in poses],4)
        document["buffers"][0]["byteLength"]=len(raw)
        document["animations"]=[{"samplers":[{"input":clock,"output":position},{"input":clock,"output":rotation}],
            "channels":[{"sampler":0,"target":{"node":0,"path":"translation"}},
                        {"sampler":1,"target":{"node":0,"path":"rotation"}}]}]
        return document,bytes(raw)

    def test_actual_decoded_clock_guard_rejects_full_turn_alias(self):
        document,binary=self.clock_fixture([i/32 for i in range(65)])
        times,tracks=gate._read_tracks(document,binary,"P11")
        actual=gate._track_pose(times,tracks,"ball",Fraction(5,4))
        _,error=gate.legacy._pose_error(actual,gate._expected_pose("P11","ball",Fraction(5,4)),xyzw=True)
        self.assertLess(error,1e-6)
        document,binary=self.clock_fixture([0,1,2])
        with self.assertRaisesRegex(ValueError,"aliases the conservative authored impulse spin"):
            gate._read_tracks(document,binary,"P11")

    def test_quarter_time_exposes_wrong_coarse_rotation_despite_valid_endpoints(self):
        pose=gate._expected_pose("P11","ball",Fraction(5,4))
        a,b=(gate._expected_pose("P11","ball",t)["orientation_wxyz"] for t in (1,2))
        coarse=gate._slerp(a,b,.25)
        with self.assertRaisesRegex(ValueError,"Orientation geodesic error"):
            gate._orientation(coarse,pose["orientation_wxyz"],.001)

    def test_changed_intermediate_key_cannot_hide_between_fixed_quarter_samples(self):
        document,binary=self.clock_fixture([i/32 for i in range(65)])
        times,tracks=gate._read_tracks(document,binary,"P11")
        gate._verify_decoded_motion(times,tracks,"P11",{"position_m":.001,"rotation_rad":.001})
        tracks[("ball","rotation")][33]=[0,0,0,1]
        # The changed key is outside every fixed quarter-second observation.
        for seconds in gate._TIMES:
            actual=gate._track_pose(times,tracks,"ball",seconds)
            _,error=gate.legacy._pose_error(actual,gate._expected_pose("P11","ball",seconds),xyzw=True)
            self.assertLess(error,.001)
        with self.assertRaisesRegex(ValueError,"decoded key/interval source rotation"):
            gate._verify_decoded_motion(times,tracks,"P11",{"position_m":.001,"rotation_rad":.001})

    def test_three_js_dense_readback_requires_every_actual_interpolation_probe(self):
        document,binary=self.clock_fixture([i/32 for i in range(65)])
        times,tracks=gate._read_tracks(document,binary,"P11")
        samples=[]
        for seconds in gate._motion_probe_times(times):
            pose=gate._track_pose(times,tracks,"ball",seconds)
            p,q=gate.legacy._pose_error(pose,gate._expected_pose("P11","ball",seconds),xyzw=True)
            samples.append({"time_seconds":seconds,"objects":{"ball":{**pose,
                "independent":{"position_error_m":p,"rotation_error_rad":q}}}})
        three={"decoded_clock_samples":samples,"decoded_clock_pose_comparisons":len(samples)}
        # Actual Three.js readback retains small float32 quaternion norm error;
        # independent source orientation comparison still normalizes its axes.
        samples[133]["objects"]["ball"]["orientation_xyzw"]=[v*(1+5e-8) for v in samples[133]["objects"]["ball"]["orientation_xyzw"]]
        gate._verify_decoded_motion(times,tracks,"P11",{"position_m":.001,"rotation_rad":.001},three=three)
        three["decoded_clock_samples"]=samples[:1]+samples[2:]
        three["decoded_clock_pose_comparisons"]-=1
        with self.assertRaisesRegex(ValueError,"omitted or relabelled an actual decoded-key"):
            gate._verify_decoded_motion(times,tracks,"P11",{"position_m":.001,"rotation_rad":.001},three=three)
        three["decoded_clock_samples"]=samples
        three["decoded_clock_pose_comparisons"]+=1
        samples[133]["objects"]["ball"]["position_m"][0]=43
        with self.assertRaisesRegex(ValueError,"Independent source-driven world position"):
            gate._verify_decoded_motion(times,tracks,"P11",{"position_m":.001,"rotation_rad":.001},three=three)
        samples[133]["objects"]["ball"]["position_m"][0]=0
        samples[133]["objects"]["ball"]["orientation_xyzw"]=[0,0,0,2]
        with self.assertRaisesRegex(ValueError,"decoded float32 unit-quaternion tolerance"):
            gate._verify_decoded_motion(times,tracks,"P11",{"position_m":.001,"rotation_rad":.001},three=three)

    def test_delivery_link_rejects_a_lookalike_with_different_retrieved_hash(self):
        context={"workflow":{"artifacts":{"P02":{"project_id":"synthetic-reader","program_revision":self.program.program_revision,
                 "artifact_sha256":"sha256:"+"1"*64,"byte_length":123}},
                 "snapshots":{("synthetic-reader",self.program.program_revision):(self.program,True)}}}
        gate.surface._verify_delivery_link("P02",self.program,"sha256:"+"1"*64,123,context)
        with self.assertRaisesRegex(ValueError,"artifact retrieved from the source workflow"):
            gate.surface._verify_delivery_link("P02",self.program,"sha256:"+"2"*64,123,context)

    def test_camera_union_requires_actual_y_up_source_geometry(self):
        low,high=gate._camera_bounds("P02")
        camera={"position_m":[0,2,10],"orientation_xyzw":[0,0,0,1],"target_m":[(a+b)/2 for a,b in zip(low,high)],
                "up":[0,1,0],"fov_degrees":35,"aspect":1100/750,"near_m":.01,"far_m":100,
                "bounds_min_m":low,"bounds_max_m":high,"fit_sample_times_seconds":[i/4 for i in range(9)],
                "fit_policy":"union_of_actual_geometry_over_quarter_seconds/0.1"}
        gate._verify_camera(camera,"P02")
        camera["up"]=[0,0,1]
        with self.assertRaisesRegex(ValueError,"Y-up"):
            gate._verify_camera(camera,"P02")
        camera["up"]=[0,1,0];camera["bounds_max_m"]=[100,100,100]
        with self.assertRaisesRegex(ValueError,"union upper bounds"):
            gate._verify_camera(camera,"P02")


class ImpulseRegressionEvidenceTests(unittest.TestCase):
    def test_a03_test_names_or_pass_count_do_not_substitute_for_execution_records(self):
        for execution in (None,{"required_test_ids":list(gate._A03_TESTS),"passed":4},_execution(gate._A03_TESTS[:-1])):
            with self.subTest(execution=execution),self.assertRaisesRegex(ValueError,"A03 remains partial"):
                gate._require_a03_execution(execution)
        value=_execution(gate._A03_TESTS)
        gate._require_a03_execution(value)
        value["tests"].append(value["tests"][0])
        with self.assertRaisesRegex(ValueError,"A03 remains partial"):
            gate._require_a03_execution(value)

    def test_current_m12_requires_complete_exact_mapped_test_records(self):
        mapping=gate.surface.load_manifest()
        names=sorted({n for c in mapping["cases"] for n in c["required_tests"]})
        implementation=gate.implementation_identity();inventory=[]
        report={"schema_version":"ontokin.surface-conformance/0.1","executed":True,
            "implementation":implementation,"implementation_after_run":implementation,"evidence_stable_during_run":True,
            "run_issues":[],"evidence_files":inventory,"evidence_inventory_sha256":gate.surface.inventory_identity(inventory),
            "manifest":{"sha256":gate.surface.MAPPING_SHA256},"test_execution":_execution(names),
            "cases":[{**c,"status":"passed","pending_reasons":[]} for c in mapping["cases"]],
            "summary":{"full_gate_complete":True,"passed":12,"failed":0,"pending":0}}
        # This synthetic private reader record proves no actual M12 execution.
        gate._verify_surface_report(report,implementation,inventory,mapping)
        report["test_execution"]["tests"].pop()
        with self.assertRaisesRegex(ValueError,"mapped methods"):
            gate._verify_surface_report(report,implementation,inventory,mapping)

    def test_historical_or_partial_m12_cannot_close_new_profile_regression(self):
        mapping=gate.surface.load_manifest();implementation=gate.implementation_identity()
        report={"schema_version":"ontokin.surface-conformance/0.1","executed":True,"implementation":{},
            "implementation_after_run":implementation,"evidence_stable_during_run":True,"run_issues":[]}
        with self.assertRaisesRegex(ValueError,"Current M01-M12"):
            gate._verify_surface_report(report,implementation,[],mapping)

    def test_ci_uses_actual_git_blobs_and_requires_all_supported_job_roles(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            files={"ontokin/sample.py":b"pass\n","docs/language-design/impulse-v0.1/grammar.ebnf":b"program = 'source';\n"}
            for name,raw in files.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            def git(*args):
                return subprocess.run(["git",*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
            git("init","-q");git("add",".");git("-c","user.name=Reader Test","-c","user.email=reader@example.invalid","commit","-qm","Synthetic private reader fixture")
            commit=git("rev-parse","HEAD")
            inventory=[{"path":p,"sha256":gate.digest(raw)} for p,raw in sorted(files.items())]
            implementation={"name":"synthetic private reader fixture","source_code_sha256":"sha256:"+"0"*64,"version":"test"}
            ci={"schema_version":"ontokin.impulse-ci/0.1","implementation":implementation,
                "evidence_inventory_sha256":gate.surface.inventory_identity(inventory),"implementation_commit":commit,
                "workflow_run":{"id":1,"head_sha":commit,"status":"completed","conclusion":"success",
                                "html_url":"https://github.com/Omegapy/OntoKin/actions/runs/1"},
                "jobs":[{"id":i+1,"run_id":1,"name":"synthetic private reader role "+str(i),"status":"completed","conclusion":"success",
                         "role":"visual" if version is None else "python","python_version":version}
                        for i,version in enumerate(["3.11","3.12","3.13",None])]}
            path=root/"ci.json"
            def write():
                path.write_text(json.dumps(ci));return {"path":"ci.json","sha256":gate.file_identity(path)}
            with patch.object(gate,"ROOT",root):
                self.assertEqual(1,gate._verify_ci(write(),root,implementation,inventory)["visual_jobs"])
                ci["jobs"].pop()
                with self.assertRaisesRegex(ValueError,"Three supported Python"):
                    gate._verify_ci(write(),root,implementation,inventory)
                (root/"ontokin/sample.py").write_text("different bytes\n")
                changed=[{"path":r["path"],"sha256":gate.file_identity(root/r["path"])} for r in inventory]
                with self.assertRaisesRegex(ValueError,"did not contain current bytes"):
                    gate._verify_commit_inventory(commit,changed)
                (root/"ontokin/sample.py").unlink()
                with self.assertRaisesRegex(ValueError,"omitted, added or renamed"):
                    gate._verify_commit_inventory(commit,[r for r in changed if r["path"]!="ontokin/sample.py"])


if __name__=="__main__":
    unittest.main()
