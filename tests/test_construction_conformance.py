"""Prove that the C gate uses execution and rejects stale/incomplete evidence."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

from ontokin.bundle import load_bundle
from ontokin.construction_conformance import (DEFAULT_FIXTURES, ROOT, _run_tests,
                                              file_identity, implementation_identity,
                                              load_manifest, run_conformance,
                                              verify_external_evidence)
from tools.build_construction_demo import build


class ConstructionConformanceTests(unittest.TestCase):
    def test_manifest_matches_adopted_requirements_and_has_no_observed_pass_claims(self):
        manifest = load_manifest()
        contract = (ROOT / "docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md").read_text()
        adopted = {case: (title.strip(), expectation.strip())
                   for case, title, expectation in re.findall(r"^\| (C\d\d) \| ([^|]+) \| ([^|]+) \|$", contract, re.M)}
        self.assertEqual(set(adopted), {case["id"] for case in manifest["cases"]})
        self.assertEqual({rule for case in manifest["cases"] for rule in case["requirements"]},
                         {f"CON-{number:03}" for number in range(1, 16)})
        for case in manifest["cases"]:
            self.assertEqual((case["title"], case["expected"]), adopted[case["id"]])
            self.assertNotIn("status", case)
            self.assertEqual(case["unbound_requirements"], [])
        self.assertEqual(manifest["cases"][-1]["external_gates"], ["identified_visual_delivery"])
        self.assertFalse(manifest["full_product_conformance_certified"])

    def test_shared_real_requirements_execute_once_and_partial_selection_is_disclosed(self):
        manifest = load_manifest()
        selected = {"C02", "C03"}
        required = {name for case in manifest["cases"] if case["id"] in selected
                    for name in case["required_tests"]}
        self.assertGreater(sum(len(case["required_tests"]) for case in manifest["cases"] if case["id"] in selected),
                           len(required), "The fixture must actually share a test between two cases")
        report = run_conformance(case_ids=["C02", "C03", "C02"])
        self.assertEqual(report["summary"], {"total": 2, "passed": 2, "failed": 0, "pending": 0,
                                             "all_adopted_cases_selected": False, "case_gate_complete": False})
        measured = report["test_execution"]
        self.assertEqual(measured["tests_run"], len(required))
        self.assertEqual(measured["unique_required"], len(required))
        self.assertEqual({test["test_id"] for test in measured["tests"]}, required)
        self.assertTrue(all(test["status"] == "passed" for test in measured["tests"]))
        self.assertNotIn("assertions", measured)
        self.assertTrue(report["evidence_stable_during_run"])
        self.assertEqual(report["external_evidence"]["status"], "pending")
        self.assertFalse(report["external_evidence"]["executed_external_tools"])

    def test_failed_subtests_skips_and_class_errors_never_become_passed_methods(self):
        source = '''import unittest
class Measurements(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(2 + 2, 4)
    def test_subtest_failure(self):
        with self.subTest(observation='deliberate mismatch'):
            self.assertEqual(2 + 2, 5)
    def test_subtest_skip(self):
        with self.subTest(observation='unavailable check'):
            self.skipTest('deliberate skipped acceptance check')
class FixtureFailure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raise RuntimeError('deliberate fixture setup failure')
    def test_unreached(self):
        raise AssertionError('setup must prevent this body')
'''
        with tempfile.TemporaryDirectory(prefix="ontokin-conformance-methods-") as directory:
            module = "test_conformance_measurement_probe"
            (Path(directory) / (module + ".py")).write_text(source, encoding="utf-8")
            sys.path.insert(0, directory)
            try:
                names = [module + ".Measurements." + name for name in
                         ("test_pass", "test_subtest_failure", "test_subtest_skip")]
                names.append(module + ".FixtureFailure.test_unreached")
                result = _run_tests(names)
            finally:
                sys.path.remove(directory)
                sys.modules.pop(module, None)
        records = {record["test_id"].split(".")[-1]: record for record in result["tests"]}
        self.assertEqual(records["test_pass"]["status"], "passed")
        self.assertEqual(records["test_subtest_failure"]["status"], "failed")
        self.assertEqual(records["test_subtest_skip"]["status"], "skipped")
        self.assertEqual(records["test_unreached"]["status"], "not_run")
        self.assertEqual(result["tests_run"], 3)
        self.assertEqual(len(result["fixture_errors"]), 1)
        self.assertIn("deliberate fixture setup failure", result["fixture_errors"][0]["failure"])


class ConstructionExternalEvidenceTests(unittest.TestCase):
    """Temporary verification-input fixtures are not external execution evidence.

The workflow, inspection reference and GLB below come from actual agent requests.
Synthetic external/browser report inputs exercise the retained-record checker;
they are not evidence of a browser, independent validator or visual review.
"""

    @classmethod
    def setUpClass(cls):
        cls.program = load_bundle(json.loads((DEFAULT_FIXTURES / "01-keyed-rack/program.bundle.json").read_text()))
        cls.template = tempfile.TemporaryDirectory(prefix="ontokin-evidence-template-")
        cls.addClassCleanup(cls.template.cleanup)
        cls.template_root = Path(cls.template.name)
        build(cls.template_root)
        cls.artifact = (cls.template_root / "keyed-rack.glb").read_bytes()
        oracle_path = cls.template_root / "docs/language-design/construction-v0.1/01-keyed-rack/expected.json"
        oracle_path.parent.mkdir(parents=True)
        shutil.copyfile(DEFAULT_FIXTURES / "01-keyed-rack/expected.json", oracle_path)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-external-gate-test-")
        self.root = Path(self.temporary.name)
        self.engine = implementation_identity()
        shutil.copytree(self.template_root, self.root, dirs_exist_ok=True)
        roles = {"source_bundle": "program.bundle.json", "artifact": "keyed-rack.glb",
                 "workflow": "workflow.json", "reference": "keyed-rack.reference.json",
                 "external_results": "external-results.json", "viewer_results": "viewer-results.json",
                 "capture": "capture.fixture"}
        reference = self.read("keyed-rack.reference.json")
        workflow = self.read("workflow.json")
        export = self.read("keyed-rack.export.json")
        artifact_sha = file_identity(self.root / "keyed-rack.glb")
        synthetic_note = "Synthetic checker input; no external execution or visual inspection is claimed."
        samples = []
        for sample in reference["samples"]:
            poses = {}
            for name, pose in sample["objects"].items():
                w, x, y, z = pose["orientation_wxyz"]
                poses[name] = {"position_m": pose["position_m"], "orientation_xyzw": [x, y, z, w]}
            samples.append({"time_seconds": float(sample["time_seconds"]), "objects": poses})
        geometry = []
        for item in reference["geometry"]:
            kind = item["geometry"]["kind"]
            size = item["geometry"]["size_m"] if kind == "box" else [2 * item["geometry"]["radius_m"]] * 3
            geometry.append({"path": item["path"], "kind": kind, "decoded_full_size_m": size,
                             "expected_full_size_m": size, "max_dimension_error_m": 0, "status": "passed"})
        self.write("external-results.json", {"schema_version": "ontokin.external-validation/0.1", "scope": synthetic_note,
            "files": [{"file": "keyed-rack.glb", "sha256": artifact_sha.removeprefix("sha256:"),
                       "program_revision": self.program.program_revision, "source_manifest": self.program.manifest(),
                       "geometry": geometry, "validator": {"version": "test-fixture", "errors": 0, "warnings": 0,
                                                             "infos": 0, "hints": 0, "messages": []},
                       "three_js": {"revision": "test-fixture", "loaded": True, "animation_count": 1,
                                    "duration_seconds": 2, "samples": samples,
                                    "comparison": {"status": "passed", "sample_count": 7, "object_pose_comparisons": 126,
                                                   "max_position_error_m": 0, "max_rotation_error_rad": 0,
                                                   "tolerances": reference["tolerances"], "failures": []}}}]})
        browser_samples = copy.deepcopy(samples)
        for sample, expected in zip(browser_samples, reference["samples"]):
            sample["displayed_time_seconds"] = sample["time_seconds"]
            for name, pose in sample["objects"].items():
                pose.update(expected_position_m=expected["objects"][name]["position_m"],
                            expected_orientation_wxyz=expected["objects"][name]["orientation_wxyz"],
                            position_error_m=0, rotation_error_rad=0, oracle_position_error_m=0, oracle_rotation_error_rad=0)
        self.write("capture.fixture", {"scope": synthetic_note})
        browser_files = {"source_bundle": "program.bundle.json", "entry_source": "main.ok", "library_source": "hinges.ok",
                         "glb": "keyed-rack.glb", "export_report": "keyed-rack.export.json", "reference": "keyed-rack.reference.json",
                         "workflow": "workflow.json", "oracle": "docs/language-design/construction-v0.1/01-keyed-rack/expected.json"}
        for name in ("viewer_html", "viewer_bundle", "viewer_builtin_data", "verifier", "tooling_lock"):
            browser_files[name] = name + ".fixture"
            self.write(browser_files[name], {"scope": synthetic_note, "role": name})
        self.write("viewer-results.json", {"schema_version": "ontokin.visual-validation/0.2", "status": "passed",
            "scope": synthetic_note, "program_revision": self.program.program_revision, "source_manifest": self.program.manifest(),
            "artifact_sha256": artifact_sha, "agent_implementation": self.engine,
            "exporter": export["exporter"], "exporter_source_code_sha256": export["source_code_sha256"],
            "tolerances": reference["tolerances"], "checks": ["Synthetic retained observation " + str(i) for i in range(8)],
            "samples": browser_samples, "pose_comparisons": 126, "page_errors": [], "console_errors": [],
            "network_requests": [], "failed_requests": [],
            "captures": [{"file": "capture.fixture", "sha256": file_identity(self.root / "capture.fixture"),
                          "program_revision": self.program.program_revision, "artifact_sha256": artifact_sha}],
            "provenance": {name: {"path": filename, "byte_length": (self.root / filename).stat().st_size,
                                  "sha256": file_identity(self.root / filename)} for name, filename in browser_files.items()}})
        self.evidence = {
            "schema_version": "ontokin.construction-external-gate/0.1",
            "implementation": self.engine, "program_revision": self.program.program_revision,
            "source_manifest": self.program.manifest(), "artifact_sha256": artifact_sha,
            "checks": {
                "workflow": {"status": "passed", "checks": len(workflow["checks"]), "operations": workflow["operation_count"]},
                "format": {"status": "passed", "errors": 0, "warnings": 0},
                "geometry": {"status": "passed", "objects": 18},
                "motion": {"status": "passed", "pose_comparisons": 126,
                           "max_position_error_m": 0, "max_rotation_error_rad": 0},
                "viewer": {"status": "passed", "checks": 8, "pose_comparisons": 126,
                           "capture_sha256": file_identity(self.root / roles["capture"]),
                           "visual_review": {"status": "reviewed", "reviewer": "unit-test fixture",
                                             "observation": "Synthetic gate input; no visual inspection is claimed."}},
            },
            "provenance": [{"role": role, "path": path, "sha256": file_identity(self.root / path)}
                           for role, path in sorted(roles.items())],
        }

    def read(self, filename):
        return json.loads((self.root / filename).read_text(encoding="utf-8"))

    def write(self, filename, value):
        (self.root / filename).write_text(json.dumps(value), encoding="utf-8")

    def rehash(self, filename):
        for record in self.evidence["provenance"]:
            if record["path"] == filename:
                record["sha256"] = file_identity(self.root / filename)

    def tearDown(self):
        self.temporary.cleanup()

    def verify(self, evidence=None):
        path = self.root / "gate.json"
        path.write_text(json.dumps(self.evidence if evidence is None else evidence), encoding="utf-8")
        return verify_external_evidence(path, implementation=self.engine,
                                        expected_program=self.program, root=self.root)

    def test_identity_verification_is_explicitly_distinct_from_external_tool_execution(self):
        absent = verify_external_evidence(None, implementation=self.engine, expected_program=self.program)
        self.assertEqual(absent["status"], "pending")
        verified = self.verify()
        self.assertEqual(verified["status"], "passed", verified)
        self.assertFalse(verified["executed_external_tools"])
        self.assertEqual(len(verified["verified_provenance"]), 7)
        self.assertTrue(all(record["matches"] for record in verified["verified_provenance"]))
        self.assertEqual(verified["crosschecked_reports"]["workflow_operations"], 22)
        self.assertEqual(verified["crosschecked_reports"]["pose_observations"]["viewer"]["pose_comparisons"], 126)

    def test_stale_identity_insufficient_counts_or_absent_visual_review_leave_gate_pending(self):
        mutations = [
            ("implementation", lambda value: value["implementation"].update(source_code_sha256="sha256:" + "0" * 64)),
            ("program", lambda value: value.update(program_revision="sha256:" + "0" * 64)),
            ("source map", lambda value: value["source_manifest"]["units"].reverse()),
            ("geometry count", lambda value: value["checks"]["geometry"].update(objects=17)),
            ("pose count", lambda value: value["checks"]["motion"].update(pose_comparisons=125)),
            ("browser count", lambda value: value["checks"]["viewer"].update(pose_comparisons=125)),
            ("numeric tolerance", lambda value: value["checks"]["motion"].update(max_position_error_m=.0011)),
            ("large numeric", lambda value: value["checks"]["motion"].update(max_rotation_error_rad=10 ** 400)),
            ("boolean count", lambda value: value["checks"]["format"].update(errors=False)),
            ("failed format", lambda value: value["checks"]["format"].update(status="failed")),
            ("missing review", lambda value: value["checks"]["viewer"].pop("visual_review")),
            ("capture identity", lambda value: value["checks"]["viewer"].update(capture_sha256="sha256:" + "0" * 64)),
        ]
        for label, mutate in mutations:
            with self.subTest(condition=label):
                evidence = copy.deepcopy(self.evidence)
                mutate(evidence)
                result = self.verify(evidence)
                self.assertEqual(result["status"], "pending", result)
                self.assertTrue(result["issues"])

    def test_rehashed_failed_or_contradictory_reports_cannot_be_overridden_by_passed_summary(self):
        cases = [
            ("workflow.json", lambda value: value.update(status="failed"), "actual workflow report failed"),
            ("workflow.json", lambda value: value["checks"][0].update(passed=False), "workflow checks contradict"),
            ("workflow.json", lambda value: value.update(operation_count=21), "operation count contradicts"),
            ("workflow.json", lambda value: value["operations"][-1]["response"]["result"].update(data_base64="AAAA"),
             "retrieved chunks do not reproduce"),
            ("keyed-rack.reference.json", lambda value: value["samples"][0]["objects"]["first"]["position_m"].__setitem__(0, 3),
             "differs from the independent formula"),
            ("external-results.json", lambda value: value["files"][0]["validator"].update(warnings=1), "Khronos report contains"),
            ("external-results.json", lambda value: value["files"][0]["three_js"]["comparison"].update(status="failed"),
             "Three.js comparison is unavailable, failed"),
            ("external-results.json", lambda value: value["files"][0]["three_js"]["comparison"].update(object_pose_comparisons=125),
             "pose comparison count contradicts"),
            ("external-results.json", lambda value: value["files"][0]["three_js"]["comparison"]["tolerances"].update(position_m=.1),
             "exceeds its declared tolerance"),
            ("external-results.json", lambda value: value["files"][0]["geometry"][0].update(status="failed"),
             "mesh dimensions contradict"),
            ("external-results.json", lambda value: value["files"][0]["three_js"]["samples"][0]["objects"]["first"]["position_m"].__setitem__(0, 3),
             "retained poses violate"),
            ("viewer-results.json", lambda value: value.update(status="failed"), "actual browser report failed"),
            ("viewer-results.json", lambda value: value["console_errors"].append("Actual browser failure"), "browser checks or error records"),
            ("viewer-results.json", lambda value: value.update(pose_comparisons=125), "pose comparison count contradicts"),
            ("viewer-results.json", lambda value: value["samples"][0]["objects"]["first"].update(position_error_m=.01),
             "disagrees with its retained observations"),
            ("viewer-results.json", lambda value: value["captures"][0].update(artifact_sha256="sha256:" + "0" * 64),
             "does not identify the reviewed capture"),
            ("viewer-results.json", lambda value: value["provenance"]["entry_source"].update(sha256="sha256:" + "0" * 64),
             "entry_source bytes changed"),
        ]
        for filename, mutate, issue in cases:
            with self.subTest(file=filename, expected_issue=issue):
                original = self.read(filename)
                changed = copy.deepcopy(original)
                mutate(changed)
                self.write(filename, changed)
                self.rehash(filename)
                result = self.verify()
                self.assertEqual(result["status"], "pending", result)
                self.assertTrue(all(item["matches"] for item in result["verified_provenance"]), result)
                self.assertTrue(any(issue in message for message in result["issues"]), result["issues"])
                self.write(filename, original)
                self.rehash(filename)

    def test_changed_browser_source_and_rendering_inputs_invalidate_the_retained_capture_context(self):
        for filename in ("main.ok", "hinges.ok", "viewer_bundle.fixture", "verifier.fixture"):
            with self.subTest(input=filename):
                path = self.root / filename
                original = path.read_bytes()
                path.write_bytes(original + b"\nChanged after capture\n")
                result = self.verify()
                self.assertEqual(result["status"], "pending", result)
                self.assertTrue(any("browser's retained" in issue for issue in result["issues"]), result["issues"])
                path.write_bytes(original)

    def test_actual_file_tampering_missing_roles_and_path_escape_cannot_close_gate(self):
        artifact = self.root / "keyed-rack.glb"
        artifact.write_bytes(self.artifact + b"changed")
        changed = self.verify()
        self.assertEqual(changed["status"], "pending")
        self.assertTrue(any("artifact" in issue for issue in changed["issues"]))
        artifact.write_bytes(self.artifact)
        for mode in ("missing", "escape", "duplicate"):
            with self.subTest(condition=mode):
                evidence = copy.deepcopy(self.evidence)
                if mode == "missing":
                    evidence["provenance"] = [record for record in evidence["provenance"] if record["role"] != "viewer_results"]
                elif mode == "escape":
                    evidence["provenance"][0]["path"] = "../outside"
                else:
                    evidence["provenance"].append(copy.deepcopy(evidence["provenance"][0]))
                self.assertEqual(self.verify(evidence)["status"], "pending")
        bundle_path = self.root / "program.bundle.json"
        payload = self.program.to_payload()
        payload["entry"]["source"] += "\n// Different candidate\n"
        bundle_path.write_text(json.dumps(payload), encoding="utf-8")
        evidence = copy.deepcopy(self.evidence)
        for record in evidence["provenance"]:
            if record["role"] == "source_bundle":
                record["sha256"] = file_identity(bundle_path)
        self.assertEqual(self.verify(evidence)["status"], "pending")


if __name__ == "__main__":
    unittest.main()
