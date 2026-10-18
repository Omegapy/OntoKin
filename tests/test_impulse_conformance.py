"""Adversarial checks for actual impulse execution and evidence acceptance."""
from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
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


if __name__=="__main__":
    unittest.main()
