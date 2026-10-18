"""Actual impulse source-to-GLB delivery, independent poses and hostile bytes."""

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import evaluate, _records_per_sample
from ontokin.gltf import export_glb, validate_export
from ontokin.scene import ExportOptions, _angular_speed_bound, sampled_states
from tests.test_export import DecodedGLB, encode_glb
from tests.test_surface_export import mesh_content, change_accessor


FIXTURES = Path(__file__).resolve().parents[1] / "docs/language-design/impulse-v0.1"
ACCEPTANCE = json.loads((FIXTURES / "acceptance.json").read_text())
CASES = {case["id"]: case for case in ACCEPTANCE["source_cases"]}
CONTRACT = "ontokin.glb/0.4"


def compile_case(case_id, *, level="evaluated"):
    bundle = load_file_manifest(FIXTURES / CASES[case_id]["file_manifest"])
    return bundle, compile_construction(bundle, level=level)


def deliver(case_id, **options):
    bundle, compiler = compile_case(case_id)
    result = export_glb(compiler.model, target_contract=CONTRACT,
                        options=ExportOptions(helpers=False, **options))
    return bundle, compiler, result, DecodedGLB(result.data)


class ImpulseExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, cls.compiler, cls.result, cls.decoded = deliver("P02")

    def assertPose(self, decoded, path, sample):
        expected = sample["objects"][path]
        actual = decoded.node_pose(path, float(Fraction(sample["time_seconds"])))
        for got, wanted in zip(actual["translation"], expected["position_m"]):
            self.assertAlmostEqual(got, wanted, delta=.001)
        if "orientation_wxyz" in expected:
            w, x, y, z = expected["orientation_wxyz"]
            wanted = (x, y, z, w)
            norm = math.hypot(*actual["rotation"])
            actual_q = tuple(v / norm for v in actual["rotation"])
            chord = min(math.hypot(*(a - sign*b for a, b in zip(actual_q, wanted)))
                        for sign in (-1, 1))
            self.assertLessEqual(chord, .0005)

    def assertReject(self, document, binary=None):
        with self.assertRaises(OntoKinError) as caught:
            validate_export(encode_glb(document, self.decoded.binary if binary is None else binary),
                            self.compiler.model, target_contract=CONTRACT)
        self.assertEqual(caught.exception.diagnostic.details["target_contract"], CONTRACT)

    def test_all_required_source_fixtures_deliver_fixed_analytic_poses(self):
        for case in CASES.values():
            if not case["delivery_required"]:
                continue
            with self.subTest(case=case["id"]):
                options = case["expected"].get("export_options", {})
                bundle, compiler, result, decoded = deliver(case["id"], **options)
                self.assertEqual(result.report["outcome"], "valid")
                self.assertEqual(result.report["program_revision"], case["program_revision"])
                self.assertEqual(result.report["program"]["manifest"], bundle.manifest())
                self.assertEqual(result.report["artifact"]["sha256"], "sha256:" + hashlib.sha256(result.data).hexdigest())
                self.assertEqual(decoded.document["extras"]["ontokin"]["profile"], "impulse-0.1")
                self.assertEqual(result.report["geometry"]["surface_profile"]["name"], "surface-0.1")
                for sample in case["expected"]["samples"]:
                    for path in sample["objects"]:
                        self.assertPose(decoded, path, sample)
                self.assertTrue(all(node.get("children") is None for node in decoded.document["nodes"]))

    def test_rotated_application_uses_world_spin_composed_with_initial_orientation(self):
        _, _, _, decoded = deliver("P03")
        for seconds in (1, 1.25, 1.5, 1.75, 2):
            c, s = math.cos(2.5 * (seconds-1)), math.sin(2.5 * (seconds-1))
            scale = math.sqrt(.5)
            sample = {"time_seconds": str(seconds), "objects": {"ball": {
                "position_m": [0, seconds-1, 0],
                "orientation_wxyz": [scale*c, scale*s, scale*c, scale*s]}}}
            self.assertPose(decoded, "ball", sample)

    def test_every_boundary_retains_exact_complete_source_impulse_records(self):
        metadata = self.decoded.document["extras"]["ontokin"]
        records = metadata["boundary_states"]
        reference = evaluate(self.compiler.model, [record["source_seconds"] for record in records])["samples"]
        for record, state in zip(records, reference):
            self.assertEqual(record["impulse_states_after"], {
                path: obj["impulses"] for path, obj in state["objects"].items()})
        application = records[1]["impulse_states_after"]["ball"]["last_applications"][0]
        frozen = CASES["P02"]["source_impulse_statements"][0]
        self.assertEqual(application["source_location"], frozen["source_location"])
        self.assertEqual(application["target_element_id"], ["impulse-demo", "demo", "ball"])
        span = application["source_location"]
        self.assertEqual(self.bundle.entry.raw[span["start_byte"]:span["end_byte"]].decode(), frozen["expected_text"])
        self.assertEqual(metadata["impulse_profile"]["continuous_external_torques"], "absent")
        self.assertEqual(metadata["impulse_profile"]["source_impulses"], "instantaneous_world_momentum_at_target_self_point")

    def test_missing_changed_or_truncated_influence_metadata_is_rejected(self):
        for mode in ("missing", "empty", "changed", "identity", "assumption"):
            with self.subTest(mode=mode):
                document = copy.deepcopy(self.decoded.document)
                metadata = document["extras"]["ontokin"]
                state = metadata["boundary_states"][1]["impulse_states_after"]["ball"]
                if mode == "missing":
                    del metadata["boundary_states"][1]["impulse_states_after"]
                elif mode == "empty":
                    state["last_applications"] = []
                elif mode == "changed":
                    state["last_applications"][0]["angular_impulse_world_n_m_s"][2] = 0
                elif mode == "identity":
                    state["last_applications"][0]["source_location"]["source_revision"] = "sha256:" + "0"*64
                else:
                    metadata["impulse_profile"]["source_impulses"] = "absent"
                self.assertReject(document)

    def test_parameter_repairs_change_physics_and_preserve_all_visual_meshes(self):
        variants = [deliver(case) for case in ("P08", "P09", "P10")]
        for path in ('rack.props["first"]', 'rack.props["second"]'):
            initial = mesh_content(variants[0][3], path)
            for _, _, _, decoded in variants[1:]:
                self.assertEqual(mesh_content(decoded, path), initial)
        poses = [decoded.node_pose('rack.props["first"]', 2) for _, _, _, decoded in variants]
        self.assertNotEqual(poses[0], poses[1])
        self.assertNotEqual(poses[0]["rotation"], poses[2]["rotation"])
        for variant in variants[1:]:
            self.assertEqual(variant[3].node_pose('rack.props["second"]', 2),
                             variants[0][3].node_pose('rack.props["second"]', 2))

    def test_high_spin_raises_sampling_above_requested_one_fps(self):
        _, compiler, result, decoded = deliver("P11", fps=1, end="2")
        self.assertAlmostEqual(result.report["sampling"]["angular_speed_bound_rad_per_s"], 40)
        self.assertGreater(len(decoded.animation_times()), 100)
        for sample in CASES["P11"]["expected"]["samples"]:
            self.assertPose(decoded, "ball", sample)
        self.assertEqual(_angular_speed_bound(compiler.model), 40)

    def test_coarsened_high_spin_track_is_rejected_even_with_valid_endpoint_poses(self):
        _, compiler, result, decoded = deliver("P11", fps=1, end="2")
        document = copy.deepcopy(decoded.document)
        binary = bytearray(decoded.binary)
        animation = document["animations"][0]
        clock = animation["samplers"][0]["input"]
        for row, seconds in enumerate((0., 1., 2.)):
            change_accessor(binary, document, clock, row, [seconds])
        document["accessors"][clock]["count"] = 3
        document["accessors"][clock]["min"] = [0.]
        document["accessors"][clock]["max"] = [2.]
        for channel in animation["channels"]:
            output = animation["samplers"][channel["sampler"]]["output"]
            for row, seconds in enumerate((0., 1., 2.)):
                change_accessor(binary, document, output, row, decoded.node_pose("ball", seconds)[channel["target"]["path"]])
            document["accessors"][output]["count"] = 3
        animation["extras"]["ontokin"]["exact_times_seconds"] = ["0", "1", "2"]
        with self.assertRaises(OntoKinError) as caught:
            validate_export(encode_glb(document, binary), compiler.model, target_contract=CONTRACT)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-ROTATION-ALIAS")

    def test_zero_duration_and_binary64_impulse_boundaries_are_never_erased(self):
        for case in ("P05", "P13", "P14", "P15"):
            with self.subTest(case=case):
                _, _, result, decoded = deliver(case)
                expected = {item["event_time_seconds"] for item in CASES[case]["source_impulse_statements"]}
                self.assertTrue(expected.issubset(result.report["sampling"]["boundary_times_seconds"]))
                self.assertTrue(expected.issubset(decoded.document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]))

    def test_all_authored_impulses_contribute_even_when_spin_cancels(self):
        _, compiler = compile_case("P06")
        self.assertGreaterEqual(_angular_speed_bound(compiler.model), 10)

    def test_single_large_sample_rejects_before_private_simulator_allocation(self):
        with patch("ontokin.scene.MAX_OUTPUT_RECORDS", 1), patch("ontokin.scene._Simulator", side_effect=AssertionError("unbudgeted allocation")):
            with self.assertRaises(OntoKinError) as caught:
                list(sampled_states(self.compiler.model, ["1"], check=lambda: None))
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-STATE-BUDGET")

    def test_boundary_metadata_is_weighted_before_mesh_allocation(self):
        with patch("ontokin.scene.MAX_OUTPUT_RECORDS", _records_per_sample(self.compiler.model)), \
                patch("ontokin.scene._nodes", side_effect=AssertionError("unbudgeted mesh allocation")):
            with self.assertRaises(OntoKinError) as caught:
                export_glb(self.compiler.model, target_contract=CONTRACT)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-BOUNDARY-BUDGET")

    def test_bound_loop_observes_cancellation_without_wrapping_it(self):
        class Cancelled(Exception):
            pass
        interruption = Cancelled("cancel bound iteration")
        def cancel():
            raise interruption
        with self.assertRaises(Cancelled) as caught:
            _angular_speed_bound(self.compiler.model, check=cancel)
        self.assertIs(caught.exception, interruption)

    def test_finite_evaluation_does_not_claim_float32_delivery(self):
        _, compiler = compile_case("P12")
        with self.assertRaises(OntoKinError) as caught:
            export_glb(compiler.model, target_contract=CONTRACT)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-FLOAT32")

    def test_older_target_binding_cannot_export_new_semantics(self):
        for target in ("ontokin.glb/0.1", "ontokin.glb/0.2", "ontokin.glb/0.3"):
            with self.subTest(target=target), self.assertRaises(OntoKinError):
                export_glb(self.compiler.model, target_contract=target)


if __name__ == "__main__":
    unittest.main()
