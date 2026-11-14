#!/usr/bin/env python3
"""Finite C236 author controls on retained package inputs; no native execution."""

from __future__ import annotations

import argparse
import copy
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


sys.dont_write_bytecode = True
CHECKER = Path(__file__).absolute().parents[1] / "check_poses.py"
SPEC = importlib.util.spec_from_file_location("c236_author_checker", CHECKER)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
PACKAGE_ROOT = None


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def independent_matrix(t, q, scale):
    """Construct controls with ordinary floating quaternion arithmetic."""
    magnitude = max(map(abs, q))
    a = [float(v/magnitude) for v in q]
    norm = math.sqrt(sum(v*v for v in a))
    w, x, y, z = [v/norm for v in a]
    return [(1-2*y*y-2*z*z)*scale[0], (2*x*y-2*w*z)*scale[1], (2*x*z+2*w*y)*scale[2], t[0],
            (2*x*y+2*w*z)*scale[0], (1-2*x*x-2*z*z)*scale[1], (2*y*z-2*w*x)*scale[2], t[1],
            (2*x*z-2*w*y)*scale[0], (2*y*z+2*w*x)*scale[1], (1-2*x*x-2*y*y)*scale[2], t[2],
            0, 0, 0, 1]


def fixtures(package_root):
    inputs = Path(package_root) / "agent-results/namespace-repair/run-01/inputs"
    reference = json.loads((inputs / "after.reference.json").read_text())
    semantic = json.loads((inputs / "after.semantic.json").read_text())
    glb = (inputs / "after.glb").read_bytes()
    parts = []
    for obj in sorted(semantic["objects"], key=lambda x: x["geometry_binding"]["node"]):
        samples = []
        for ref_sample in reference["samples"]:
            value = ref_sample["objects"][obj["path"]]
            t, q, scale = list(value["position_m"]), list(value["orientation_wxyz"]), [1, 1, 1]
            samples.append({"reference_time_seconds": ref_sample["time_seconds"],
                            "observed_time_seconds": float(ref_sample["time_seconds"]),
                            "translation_m": t, "rotation_wxyz": q, "scale": scale,
                            "world_matrix": independent_matrix(t, q, scale)})
        node = obj["geometry_binding"]["node"]
        parts.append({"gltf_node": node, "gltf_mesh": obj["geometry_binding"]["mesh"],
                      "element_id": obj["element_id"], "definition_id": obj["definition_id"],
                      "source_path": obj["path"], "native_node_id": "c236-author-node-" + str(node),
                      "samples": samples})
    return {"schema": "ontokin.c236.pose-observations/0.1", "declared_origin": "synthetic",
            "accepted_program_revision": reference["program_revision"], "glb_sha256": hashlib.sha256(glb).hexdigest(),
            "coordinate_system": {"position_unit": "m", "time_unit": "s", "basis": "gltf-rh-y-up-identity",
                                  "quaternion_order": "wxyz", "matrix_layout": "row-major-4x4"},
            "parts": parts}, reference


def decimal_angle_of_tangent(t):
    """Independent small-angle atan series, separate from cosine-ratio gate."""
    with localcontext() as context:
        context.prec = 100
        x = Decimal.from_float(t)
        power, total, sign = x, Decimal(0), 1
        for n in range(40):
            total += sign * power / (2*n + 1)
            power *= x*x
            sign = -sign
        return 2*total


class PoseControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="ontokin-c236-author-")
        cls.root = Path(cls.directory.name)
        cls.path = cls.root / "poses.json"
        cls.original, cls.reference = fixtures(PACKAGE_ROOT)
        cls.path.write_bytes(encode(cls.original))
        cls.passing = checker.check_poses(PACKAGE_ROOT, cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.observation = copy.deepcopy(self.original)

    def first(self):
        return self.observation["parts"][0]["samples"][0]

    def recompose(self, sample=None):
        sample = self.first() if sample is None else sample
        sample["world_matrix"] = independent_matrix(sample["translation_m"], sample["rotation_wxyz"], sample["scale"])

    def write(self):
        self.path.write_bytes(encode(self.observation))

    def run_value(self):
        self.write()
        return checker.check_poses(PACKAGE_ROOT, self.path)

    def refused(self, code=None, result="FAIL_CLOSED"):
        self.write()
        with self.assertRaises(checker.CheckError) as caught:
            checker.check_poses(PACKAGE_ROOT, self.path)
        report = caught.exception.report
        self.assertEqual(report["result"], result)
        if code:
            self.assertEqual(caught.exception.code, code)
        if result == "FAIL_CLOSED":
            self.assertEqual(report["comparison"]["result"], "NOT_RUN")
            self.assertFalse(report["limits"]["poses_compared"])
        else:
            self.assertEqual(len(report["comparison"]["rows"]), 126)
            self.assertTrue(report["limits"]["poses_compared"])
        return report

    def test_complete_original_source_oracle(self):
        report = self.passing
        self.assertEqual(report["result"], "PASS_CPU_POSES")
        self.assertEqual(report["structure"]["object_time_pairs"], 126)
        summary = report["comparison"]["summary"]
        self.assertEqual(summary["position_components"], 378)
        self.assertEqual(summary["scale_components"], 378)
        self.assertEqual(summary["passing_original_poses"], 126)
        self.assertEqual(summary["passing_scale_profiles"], 126)
        self.assertEqual(len(report["source"]["identity_map"]), 126)
        self.assertEqual(len(report["comparison"]["per_part"]), 18)
        self.assertTrue(all(r["object_time_pairs"] == 7 for r in report["comparison"]["per_part"]))
        self.assertTrue(all(r["object_time_pairs"] == 18 for r in report["comparison"]["per_time"]))
        expected = {(p["gltf_node"], s["reference_time_seconds"]): (p, s)
                    for p in self.original["parts"] for s in p["samples"]}
        for row in report["comparison"]["rows"]:
            p, s = expected[(row["gltf_node"], row["reference_time_seconds"])]
            source = next(r for r in self.reference["samples"] if r["time_seconds"] == row["reference_time_seconds"])["objects"][p["source_path"]]
            self.assertEqual(row["raw_translation_m"], s["translation_m"])
            self.assertEqual(row["raw_rotation_wxyz"], s["rotation_wxyz"])
            self.assertEqual(row["raw_world_matrix"], s["world_matrix"])
            self.assertEqual(row["raw_scale"], s["scale"])
            self.assertEqual(row["source_position_m"], source["position_m"])
            self.assertEqual(row["source_orientation_wxyz"], source["orientation_wxyz"])
            self.assertEqual(row["orientation_dot_ratio_squared_exact"], "1")
            self.assertEqual(len(row["matrix_consistency"]["signed_residuals_exact"]), 9)
        self.assertEqual(report["comparison"]["losses"], [])
        self.assertFalse(report["limits"]["native_receiving_evidence"])

    def test_observation_byte_binding_includes_whitespace(self):
        self.write()
        first = checker.check_poses(PACKAGE_ROOT, self.path)
        self.path.write_bytes(self.path.read_bytes() + b"\n")
        second = checker.check_poses(PACKAGE_ROOT, self.path)
        self.assertNotEqual(first["observation_sha256"], second["observation_sha256"])
        self.assertEqual(second["observation_bytes"], first["observation_bytes"] + 1)
        self.assertEqual(second["observation_sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_fresh_admission_cannot_be_replaced_by_old_pass(self):
        self.write()
        with mock.patch.object(checker.c221, "check_package", wraps=checker.c221.check_package) as admission:
            result = checker.check_poses(PACKAGE_ROOT, self.path)
        self.assertEqual(admission.call_count, 1)
        self.assertEqual(result["admission"]["result"], "PASS_CPU_AUTHORITY_BINDING")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_poses(tmp, self.path)
        self.assertEqual(caught.exception.stage, "authority_admission")
        self.assertEqual(caught.exception.report["source"]["result"], "NOT_RUN")

    def copy_package_inputs(self, root):
        for relative in checker.c221.INPUT_PATHS:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(PACKAGE_ROOT) / relative, target)
            target.chmod(0o644)

    def test_changed_original_reference_bytes_refused(self):
        self.write()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.copy_package_inputs(root)
            path = root / checker.c221.INPUT_PATHS[4]
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_poses(root, self.path)
        self.assertEqual(caught.exception.stage, "authority_admission")
        self.assertEqual(caught.exception.report["comparison"]["result"], "NOT_RUN")

    def test_changed_reference_after_initial_admission_refused(self):
        self.write()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.copy_package_inputs(root)
            original = checker.c221.check_package
            def change_after_admission(*args):
                result = original(*args)
                path = root / checker.c221.INPUT_PATHS[4]
                path.write_bytes(path.read_bytes() + b"\n")
                return result
            with mock.patch.object(checker.c221, "check_package", side_effect=change_after_admission):
                with self.assertRaises(checker.CheckError) as caught:
                    checker.check_poses(root, self.path)
        self.assertEqual(caught.exception.stage, "source_reference")
        self.assertEqual(caught.exception.report["structure"]["result"], "NOT_RUN")

    def test_wrong_schema_source_and_coordinate_claims(self):
        for field, value, code in (("schema", "other", "SCHEMA"), ("glb_sha256", "0"*64, "IDENTITY"),
                                   ("accepted_program_revision", "wrong", "IDENTITY"),
                                   ("coordinate_system", {"basis": "blender"}, "COORDINATES")):
            with self.subTest(field=field):
                self.observation = copy.deepcopy(self.original)
                self.observation[field] = value
                self.refused(code)

    def test_part_identity_swaps_rejected(self):
        for field in ("gltf_mesh", "source_path", "element_id", "definition_id"):
            with self.subTest(field=field):
                self.observation = copy.deepcopy(self.original)
                if field == "definition_id":
                    self.observation["parts"][0][field] = ["invented"]
                elif field == "gltf_mesh":
                    self.observation["parts"][0][field] = 999
                else:
                    self.observation["parts"][0][field] = copy.deepcopy(self.observation["parts"][1][field])
                self.refused("IDENTITY")

    def test_missing_extra_duplicate_parts_rejected(self):
        for mutation in ("missing", "extra", "duplicate"):
            with self.subTest(mutation=mutation):
                self.observation = copy.deepcopy(self.original)
                if mutation == "missing":
                    self.observation["parts"].pop()
                elif mutation == "extra":
                    self.observation["parts"].append(copy.deepcopy(self.observation["parts"][0]))
                else:
                    self.observation["parts"][1] = copy.deepcopy(self.observation["parts"][0])
                self.refused("IDENTITY" if mutation == "duplicate" else "COUNT")

    def test_native_labels_remain_unique_bounded_untrusted_text(self):
        for label in ("", "x"*4097, "nul\x00", 1, self.original["parts"][1]["native_node_id"]):
            with self.subTest(label=str(label)[:20]):
                self.observation = copy.deepcopy(self.original)
                self.observation["parts"][0]["native_node_id"] = label
                self.refused("NATIVE_LABEL")

    def test_missing_duplicate_mistyped_time_slots_rejected(self):
        for mode in ("missing", "duplicate", "unknown", "numeric"):
            with self.subTest(mode=mode):
                self.observation = copy.deepcopy(self.original)
                samples = self.observation["parts"][0]["samples"]
                if mode == "missing":
                    samples.pop()
                elif mode == "duplicate":
                    samples[1]["reference_time_seconds"] = samples[0]["reference_time_seconds"]
                else:
                    samples[0]["reference_time_seconds"] = "0.1" if mode == "unknown" else 0
                self.refused("COUNT" if mode == "missing" else "TIME_IDENTITY")

    def test_swapped_observed_times_are_measured_without_rematching(self):
        samples = self.observation["parts"][0]["samples"]
        samples[0]["observed_time_seconds"], samples[1]["observed_time_seconds"] = samples[1]["observed_time_seconds"], samples[0]["observed_time_seconds"]
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        failures = [r for r in result["comparison"]["rows"] if not r["time_pass"]]
        self.assertEqual(len(failures), 2)
        self.assertEqual({r["reference_time_seconds"] for r in failures}, {"0", "0.25"})

    def test_swapped_pose_values_keep_declared_source_identity(self):
        a, b = self.observation["parts"][0]["samples"][0], self.observation["parts"][1]["samples"][0]
        a["translation_m"], b["translation_m"] = b["translation_m"], a["translation_m"]
        self.recompose(a)
        self.recompose(b)
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        self.assertEqual(result["comparison"]["summary"]["failing_original_poses"], 2)

    def test_position_adjacent_values_follow_exact_original_limit(self):
        low = math.nextafter(0.001, 0.0)
        self.assertLess(Fraction(low), Fraction(1, 1000))
        self.first()["translation_m"][2] = low
        self.recompose()
        self.assertEqual(self.run_value()["result"], "PASS_CPU_POSES")
        self.first()["translation_m"][2] = math.nextafter(low, math.inf)
        self.recompose()
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        self.assertEqual(result["comparison"]["losses"][0]["failed_position_components"], ["z"])

    def test_position_metric_is_max_component_not_euclidean(self):
        small = math.nextafter(0.001, 0.0)
        sample = self.first()
        sample["translation_m"][1:] = [small, small]
        self.recompose()
        result = self.run_value()
        self.assertGreater(math.hypot(small, small), 0.001)
        self.assertEqual(result["result"], "PASS_CPU_POSES")

    def test_private_exact_position_and_time_boundaries(self):
        source = checker._read_source(PACKAGE_ROOT)
        _, rows = checker._validate_structure(copy.deepcopy(self.original), source)
        rows[0]["sample"]["translation_m"][2] = Fraction(1, 1000)
        rows[0]["sample"]["observed_time_seconds"] = Fraction(1, 1000000)
        equal = checker._compare(rows)
        self.assertEqual(equal["result"], "PASS_CPU_POSES")
        rows[0]["sample"]["translation_m"][2] += Fraction(1, 10**60)
        rows[0]["sample"]["observed_time_seconds"] += Fraction(1, 10**60)
        above = checker._compare(rows)
        self.assertEqual(above["result"], "FAIL_POSE_LIMIT")
        self.assertEqual(above["rows"][0]["failed_gates"], ["position", "time"])

    def test_time_adjacent_values_follow_exact_decimal_limit(self):
        value = 0.000001
        if Fraction(value) > Fraction(1, 1000000):
            value = math.nextafter(value, 0)
        self.first()["observed_time_seconds"] = value
        self.assertEqual(self.run_value()["result"], "PASS_CPU_POSES")
        self.first()["observed_time_seconds"] = math.nextafter(value, math.inf)
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        self.assertEqual(result["comparison"]["losses"][0]["failed_gates"], ["time"])

    def test_orientation_adjacent_boundary_uses_independent_atan_oracle(self):
        value = math.tan(0.0005)
        if decimal_angle_of_tangent(value) > Decimal("0.001"):
            low, high = math.nextafter(value, 0), value
        else:
            low, high = value, math.nextafter(value, math.inf)
        self.assertLess(decimal_angle_of_tangent(low), Decimal("0.001"))
        self.assertGreater(decimal_angle_of_tangent(high), Decimal("0.001"))
        self.first()["rotation_wxyz"] = [1, 0, 0, low]
        self.recompose()
        self.assertEqual(self.run_value()["result"], "PASS_CPU_POSES")
        self.first()["rotation_wxyz"] = [1, 0, 0, high]
        self.recompose()
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        self.assertEqual(result["comparison"]["losses"][0]["failed_gates"], ["orientation"])

    def test_quaternion_sign_equivalence_preserves_all_126_poses(self):
        for part in self.observation["parts"]:
            for sample in part["samples"]:
                sample["rotation_wxyz"] = [-v for v in sample["rotation_wxyz"]]
        result = self.run_value()
        self.assertEqual(result["comparison"]["summary"]["passing_original_poses"], 126)
        self.assertTrue(all(r["orientation_dot_ratio_squared_exact"] == "1" for r in result["comparison"]["rows"]))

    def test_finite_huge_and_subnormal_quaternion_rescalings(self):
        for scalar in (sys.float_info.max, math.ulp(0.0), -sys.float_info.max):
            with self.subTest(scalar=scalar):
                self.observation = copy.deepcopy(self.original)
                self.first()["rotation_wxyz"] = [scalar, 0, 0, 0]
                self.assertEqual(self.run_value()["result"], "PASS_CPU_POSES")

    def test_half_turn_orientation_failure_retains_measured_angle(self):
        self.first()["rotation_wxyz"] = [0, 1, 0, 0]
        self.recompose()
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        self.assertEqual(result["comparison"]["rows"][0]["orientation_error_rad"], math.pi)
        self.assertEqual(result["comparison"]["rows"][0]["orientation_dot_ratio_squared_exact"], "0")

    def test_near_unit_scale_is_separate_profile_failure(self):
        self.first()["scale"][0] = math.nextafter(1.0, 0.0)
        self.recompose()
        result = self.refused("SCALE_PROFILE", "FAIL_SCALE_PROFILE")
        self.assertEqual(result["comparison"]["original_pose_result"], "PASS_POSE_LIMITS")
        self.assertEqual(result["comparison"]["scale_profile_result"], "FAIL_UNIT_SCALE_PROFILE")
        self.assertEqual(result["comparison"]["losses"][0]["failed_gates"], ["unit_scale_profile"])
        self.assertEqual(result["comparison"]["rows"][0]["failed_scale_components"], ["x"])

    def test_pose_and_scale_losses_both_survive(self):
        self.first()["translation_m"][2] = 0.1
        self.first()["scale"][1] = 2
        self.recompose()
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        row = result["comparison"]["rows"][0]
        self.assertFalse(row["original_pose_pass"])
        self.assertFalse(row["unit_scale_profile_pass"])
        self.assertEqual(row["failed_gates"], ["position", "unit_scale_profile"])

    def test_zero_quaternion_nonpositive_scales_and_bad_vectors_refused(self):
        for key, value, code in (("rotation_wxyz", [0]*4, "ZERO_QUATERNION"),
                                 ("scale", [0, 1, 1], "SCALE_DOMAIN"), ("scale", [-1, 1, 1], "SCALE_DOMAIN"),
                                 ("translation_m", [True, 0, 0], "FINITE"), ("rotation_wxyz", [1, 0, 0], "VECTOR"),
                                 ("scale", [1, None, 1], "FINITE"), ("world_matrix", [1]*15, "VECTOR"),
                                 ("observed_time_seconds", False, "FINITE")):
            with self.subTest(key=key, value=value):
                self.observation = copy.deepcopy(self.original)
                self.first()[key] = value
                self.refused(code)

    def test_matrix_translation_cannot_disagree_with_raw_origin(self):
        self.first()["world_matrix"][3] += 0.01
        self.refused("MATRIX_TRANSLATION")

    def test_matrix_consistency_inclusive_boundary_and_next_float(self):
        limit = 2**-20
        self.first()["world_matrix"][1] = limit
        result = self.run_value()
        residual = result["comparison"]["rows"][0]["matrix_consistency"]
        self.assertEqual(residual["maximum_absolute_residual_exact"], "1/1048576")
        self.assertEqual(residual["signed_residuals_exact"][1], "1/1048576")
        self.first()["world_matrix"][1] = math.nextafter(limit, math.inf)
        self.refused("MATRIX_CONSISTENCY")

    def test_projective_singular_and_reflected_matrices_refused(self):
        for mode, code in (("projective", "MATRIX_AFFINE"), ("singular", "MATRIX_DETERMINANT"),
                           ("reflection", "MATRIX_DETERMINANT")):
            with self.subTest(mode=mode):
                self.observation = copy.deepcopy(self.original)
                if mode == "projective":
                    self.first()["world_matrix"][15] = 2
                else:
                    self.first()["world_matrix"][0] = 0 if mode == "singular" else -1
                self.refused(code)

    def test_independently_binary32_rounded_raw_fields_admitted(self):
        f32 = lambda value: struct.unpack("<f", struct.pack("<f", value))[0]
        for part in self.observation["parts"]:
            for sample in part["samples"]:
                sample["translation_m"] = list(map(f32, sample["translation_m"]))
                sample["rotation_wxyz"] = list(map(f32, sample["rotation_wxyz"]))
                sample["world_matrix"] = list(map(f32, sample["world_matrix"]))
        result = self.run_value()
        self.assertEqual(result["comparison"]["summary"]["passing_original_poses"], 126)
        self.assertTrue(any(Fraction(r["matrix_consistency"]["maximum_absolute_residual_exact"]) > 0
                            for r in result["comparison"]["rows"]))

    def test_origin_label_never_grants_native_acceptance(self):
        self.observation["declared_origin"] = "unattested-native"
        result = self.run_value()
        self.assertEqual(result["declared_origin"], "unattested-native")
        for name in ("native_receiving_evidence", "native_mapping_attested", "target_execution_authorized", "R07_complete"):
            self.assertFalse(result["limits"][name])
        self.observation["declared_origin"] = "attested"
        self.refused("ORIGIN")

    def test_exact_fields_and_numeric_indices(self):
        for mode in ("root_extra", "part_extra", "sample_extra", "missing", "bool_index", "float_index"):
            with self.subTest(mode=mode):
                self.observation = copy.deepcopy(self.original)
                if mode.endswith("extra"):
                    target = {"root_extra": self.observation, "part_extra": self.observation["parts"][0],
                              "sample_extra": self.first()}[mode]
                    target["extra"] = 1
                elif mode == "missing":
                    self.first().pop("world_matrix")
                else:
                    self.observation["parts"][0]["gltf_node"] = False if mode == "bool_index" else 0.0
                self.refused("INDEX" if mode.endswith("index") else "SCHEMA")

    def test_signed_zero_raw_fields_are_retained(self):
        self.first()["translation_m"][2] = -0.0
        self.first()["rotation_wxyz"][1] = -0.0
        self.first()["world_matrix"][11] = -0.0
        result = self.run_value()
        row = result["comparison"]["rows"][0]
        self.assertEqual(math.copysign(1, row["raw_translation_m"][2]), -1)
        self.assertEqual(math.copysign(1, row["raw_rotation_wxyz"][1]), -1)
        self.assertEqual(math.copysign(1, row["raw_world_matrix"][11]), -1)
        self.assertEqual(row["position_absolute_errors_exact"][2], "0")

    def test_malformed_duplicate_nonfinite_and_invalid_utf8_refused(self):
        for raw in (b'{"schema":1,"schema":2}', b'{"x":NaN}', b'{"x":1e999}', b'{"x":', b"\xff"):
            with self.subTest(raw=raw):
                self.path.write_bytes(raw)
                with self.assertRaises(checker.CheckError) as caught:
                    checker.check_poses(PACKAGE_ROOT, self.path)
                self.assertEqual(caught.exception.code, "JSON")
                self.assertEqual(caught.exception.report["comparison"]["result"], "NOT_RUN")

    def test_finite_file_size_and_regular_file_limits(self):
        for raw in (b"", b" "* (1024*1024 + 1)):
            with self.subTest(size=len(raw)):
                self.path.write_bytes(raw)
                with self.assertRaises(checker.CheckError) as caught:
                    checker.check_poses(PACKAGE_ROOT, self.path)
                self.assertEqual(caught.exception.code, "SIZE")
        with self.assertRaises(checker.CheckError) as caught:
            checker.check_poses(PACKAGE_ROOT, self.root)
        self.assertEqual(caught.exception.code, "FILE")

    def test_symlink_fifo_traversal_and_missing_paths_refused(self):
        self.write()
        link, fifo = self.root / "linked.json", self.root / "fifo"
        link.symlink_to(self.path)
        os.mkfifo(fifo)
        ancestor = self.root / "linked-dir"
        ancestor.symlink_to(self.root, target_is_directory=True)
        cases = (link, fifo, ancestor / self.path.name, self.root / "absent", self.root / ".." / self.root.name / self.path.name)
        for path in cases:
            with self.subTest(path=str(path)):
                with self.assertRaises(checker.CheckError) as caught:
                    checker.check_poses(PACKAGE_ROOT, path)
                self.assertIn(caught.exception.code, ("PATH", "FILE"))
                self.assertEqual(caught.exception.report["comparison"]["result"], "NOT_RUN")

    def test_changed_read_metadata_is_refused_by_file_guard(self):
        self.write()
        real_fstat = os.fstat
        calls = 0
        def changed(fd):
            nonlocal calls
            value = real_fstat(fd)
            calls += 1
            if calls == 2:
                names = ("st_dev", "st_ino", "st_size", "st_mode", "st_mtime_ns", "st_ctime_ns")
                data = {name: getattr(value, name) for name in names}
                data["st_mtime_ns"] += 1
                return SimpleNamespace(**data)
            return value
        with mock.patch.object(checker.os, "fstat", side_effect=changed):
            with self.assertRaises(checker.CheckError) as caught:
                checker._read_observation(self.path)
        self.assertEqual(caught.exception.code, "CHANGED")

    def test_every_failed_sample_retains_complete_accounting(self):
        for part in self.observation["parts"]:
            for sample in part["samples"]:
                sample["translation_m"][2] += 0.01
                self.recompose(sample)
        result = self.refused("POSE_COMPARISON", "FAIL_POSE_LIMIT")
        self.assertEqual(len(result["comparison"]["losses"]), 126)
        self.assertEqual(result["comparison"]["summary"]["failing_original_poses"], 126)
        self.assertTrue(all(row["failing_original_poses"] == 7 for row in result["comparison"]["per_part"]))
        self.assertTrue(all(row["failing_original_poses"] == 18 for row in result["comparison"]["per_time"]))

    def test_part_and_sample_order_cannot_change_comparison(self):
        self.observation["parts"].reverse()
        for part in self.observation["parts"]:
            part["samples"].reverse()
        result = self.run_value()
        self.assertEqual(result["comparison"], self.passing["comparison"])
        self.assertEqual(result["source"]["identity_map_sha256"], self.passing["source"]["identity_map_sha256"])

    def test_cli_pass_measured_failure_and_argument_failure(self):
        self.write()
        args = [sys.executable, "-IB", str(CHECKER), "--package-root", str(PACKAGE_ROOT), "--pose-observations", str(self.path)]
        good = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["result"], "PASS_CPU_POSES")
        self.first()["observed_time_seconds"] = 0.1
        self.write()
        bad = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(json.loads(bad.stdout)["result"], "FAIL_POSE_LIMIT")
        arguments = subprocess.run([sys.executable, "-IB", str(CHECKER)], capture_output=True, text=True)
        self.assertEqual(arguments.returncode, 2)


def main(argv=None):
    global PACKAGE_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True, type=Path)
    args = parser.parse_args(argv)
    PACKAGE_ROOT = args.package_root
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PoseControls))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

