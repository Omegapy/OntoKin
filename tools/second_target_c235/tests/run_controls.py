#!/usr/bin/env python3
"""Finite package-dependent author controls; no source or native execution."""

from __future__ import annotations

import argparse
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


sys.dont_write_bytecode = True
CHECKER = Path(__file__).absolute().parents[1] / "check_normals.py"
SPEC = importlib.util.spec_from_file_location("c235_author_checker", CHECKER)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
PACKAGE_ROOT = None


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def fixtures(package_root):
    """Decode the original GLB without checker/source-payload helper calls."""
    inputs = Path(package_root) / "agent-results/namespace-repair/run-01/inputs"
    raw = (inputs / "after.glb").read_bytes()
    length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + length])
    binary = raw[28 + length:]
    semantic = json.loads((inputs / "after.semantic.json").read_text())
    objects = {row["geometry_binding"]["node"]: row for row in semantic["objects"]}

    def accessor(index, format_string):
        spec = document["accessors"][index]
        view = document["bufferViews"][spec["bufferView"]]
        offset = view.get("byteOffset", 0) + spec.get("byteOffset", 0)
        width = struct.calcsize(format_string)
        stride = view.get("byteStride", width)
        return [list(struct.unpack_from(format_string, binary, offset + i * stride)) for i in range(spec["count"])]

    parts, mapping, records, expected = [], [], [], []
    for node_number, node in enumerate(document["nodes"]):
        if "mesh" not in node:
            continue
        meaning = objects[node_number]
        mesh = node["mesh"]
        surfaces = []
        for number, primitive in enumerate(document["meshes"][mesh]["primitives"]):
            original_indices = [value[0] for value in accessor(primitive["indices"], "<H")]
            normals = accessor(primitive["attributes"]["NORMAL"], "<3f")
            raw_indices = []
            for offset in range(0, len(original_indices), 3):
                for raw_corner, source_corner in enumerate((0, 2, 1)):
                    vertex = original_indices[offset + source_corner]
                    raw_indices.append(vertex)
                    key = [node_number, number, offset // 3, raw_corner, vertex]
                    source_key = [node_number, mesh, number, offset // 3, source_corner]
                    mapping.append([*key, mesh, number, offset // 3, source_corner, vertex])
                    records.append({"key": key, "normal": list(normals[vertex])})
                    expected.append({"raw_key": key, "source_key": source_key, "source_vertex": vertex,
                                     "normal": list(normals[vertex]), "bits": struct.pack("<3f", *normals[vertex]).hex()})
            surfaces.append({"gltf_primitive": number, "material_index": primitive["material"],
                             "positions": accessor(primitive["attributes"]["POSITION"], "<3f"),
                             "normals": normals, "indices": raw_indices})
        parts.append({"gltf_node": node_number, "gltf_mesh": mesh, "element_id": meaning["element_id"],
                      "source_path": meaning["path"], "native_node_id": "c235-author-node-" + str(node_number),
                      "display_name": "Synthetic retained-source observation", "surfaces": surfaces})
    identity = {"declared_origin": "synthetic", "accepted_program_revision": semantic["binding"]["accepted_program_revision"],
                "glb_sha256": hashlib.sha256(raw).hexdigest()}
    geometry = {"schema": "ontokin.c222.geometry-observations/0.1", **identity,
                "coordinate_system": {"position_unit": "m", "basis": "gltf-rh-y-up-identity", "winding": "godot-clockwise-reverse-once"},
                "parts": parts}
    geometry_raw = encode(geometry)
    observation = {"schema": "ontokin.c235.normal-observations/0.1", **identity,
                   "normal_frame": "gltf-object-local-right-handed-y-up",
                   "geometry_observation": {"bytes": len(geometry_raw), "sha256": hashlib.sha256(geometry_raw).hexdigest(),
                                             "corner_map_sha256": hashlib.sha256(encode(mapping)).hexdigest()},
                   "records": records}
    return geometry, observation, mapping, expected


class NormalControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="ontokin-c235-author-")
        cls.root = Path(cls.directory.name)
        cls.geometry_path, cls.normal_path = cls.root / "geometry.json", cls.root / "normals.json"
        cls.geometry_original, cls.normal_original, cls.mapping, cls.expected = fixtures(PACKAGE_ROOT)
        cls.geometry_path.write_bytes(encode(cls.geometry_original))
        cls.normal_path.write_bytes(encode(cls.normal_original))
        cls.passing = checker.check_normals(PACKAGE_ROOT, cls.geometry_path, cls.normal_path)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.geometry = copy.deepcopy(self.geometry_original)
        self.observation = copy.deepcopy(self.normal_original)

    def write(self):
        self.geometry_path.write_bytes(encode(self.geometry))
        self.normal_path.write_bytes(encode(self.observation))

    def rebind(self, copies=True):
        raw = encode(self.geometry)
        self.observation["geometry_observation"]["bytes"] = len(raw)
        self.observation["geometry_observation"]["sha256"] = hashlib.sha256(raw).hexdigest()
        if copies:
            values = {(part["gltf_node"], surface["gltf_primitive"]): surface["normals"]
                      for part in self.geometry["parts"] for surface in part["surfaces"]}
            for record in self.observation["records"]:
                key = record["key"]
                record["normal"] = list(values[tuple(key[:2])][key[4]])

    def run_value(self):
        self.write()
        return checker.check_normals(PACKAGE_ROOT, self.geometry_path, self.normal_path)

    def refused(self, code=None, stage=None, measured=False):
        with self.assertRaises(checker.CheckError) as caught:
            self.run_value()
        error = caught.exception
        self.assertEqual(error.report["result"], "FAIL_STRICT_NORMAL_LIMIT" if measured else "FAIL_CLOSED")
        if code:
            self.assertEqual(error.code, code)
        if stage:
            self.assertEqual(error.stage, stage)
        self.assertFalse(error.report["limits"]["target_execution_authorized"])
        if not measured:
            self.assertEqual(error.report["comparison"]["result"], "NOT_RUN")
        return error.report

    def first_vector(self):
        return self.geometry["parts"][0]["surfaces"][0]["normals"][0]

    def test_complete_independent_corner_oracle(self):
        result = self.passing
        self.assertEqual(result["result"], "PASS_CPU_NORMALS")
        self.assertEqual(result["admission"]["result"], "PASS_CPU_AUTHORITY_BINDING")
        self.assertEqual(result["geometry"]["corner_map_sha256"], hashlib.sha256(encode(self.mapping)).hexdigest())
        comparison = result["comparison"]
        self.assertEqual(comparison["corners_compared"], 23400)
        self.assertEqual(comparison["numeric_components_compared"], 70200)
        self.assertEqual(comparison["exceeding_corners"], 0)
        self.assertEqual(comparison["maximum_absolute_error_exact"], "0")
        self.assertEqual(comparison["maximum_angular_error_degrees"], 0)
        for observed, expected in zip(comparison["rows"], self.expected, strict=True):
            self.assertEqual(observed["raw_key"], expected["raw_key"])
            self.assertEqual(observed["source_key"], expected["source_key"])
            self.assertEqual(observed["source_vertex"], expected["source_vertex"])
            self.assertEqual(observed["source_normal_f32le"], expected["bits"])
            self.assertEqual(observed["source_normal"], expected["normal"])
            self.assertEqual(observed["raw_normal"], expected["normal"])
            self.assertEqual(observed["component_pass"], [True, True, True])
        self.assertEqual(len(comparison["per_part"]), 18)
        self.assertEqual(sum(row["corners"] for row in comparison["per_part"]), 23400)
        self.assertEqual(sum(row["components"] for row in comparison["per_part"]), 70200)

    def test_no_native_or_other_comparison_claim(self):
        limits = self.passing["limits"]
        for key in ("target_starts", "native_version_starts", "source_evaluations", "exports", "imports", "renders", "scene_writes"):
            self.assertEqual(limits[key], 0)
        for key in ("native_receiving_evidence", "native_mapping_attested", "target_execution_authorized", "material_values_compared", "poses_compared"):
            self.assertIs(limits[key], False)
        self.assertIs(limits["normal_values_compared"], True)
        self.assertIsNone(self.passing["comparison"]["angular_limit"])

    def test_scaled_normal_fails_components_despite_zero_angle(self):
        vector = self.first_vector()
        vector[:] = [value * 2 for value in vector]
        self.rebind()
        report = self.refused("NORMAL_COMPARISON", "normal_comparison", measured=True)
        self.assertEqual(report["geometry"]["corner_map_sha256"], self.passing["geometry"]["corner_map_sha256"])
        self.assertNotEqual(report["geometry"]["observation_sha256"], self.passing["geometry"]["observation_sha256"])
        self.assertEqual(report["comparison"]["maximum_angular_error_degrees"], 0)
        node = self.geometry["parts"][0]["gltf_node"]
        count = sum(row["raw_key"][0] == node and row["raw_key"][4] == 0 for row in self.expected)
        self.assertEqual(report["comparison"]["exceeding_corners"], count)
        self.assertEqual(len(report["comparison"]["rows"]), 23400)

    def test_all_corners_fail_and_accounting_is_complete(self):
        for part in self.geometry["parts"]:
            for surface in part["surfaces"]:
                for vector in surface["normals"]:
                    vector[:] = [value * 2 for value in vector]
        self.rebind()
        report = self.refused("NORMAL_COMPARISON", measured=True)
        comparison = report["comparison"]
        self.assertEqual(comparison["exceeding_corners"], 23400)
        self.assertEqual(comparison["passing_corners"], 0)
        self.assertEqual(len(comparison["exceeding_corner_records"]), 23400)
        self.assertEqual(sum(row["exceeding_corners"] for row in comparison["per_part"]), 23400)
        self.assertEqual(sum(row["exceeding_components"] for row in comparison["per_part"]), comparison["exceeding_components"])

    def test_swapped_normal_values_do_not_select_correspondence(self):
        selected = None
        for part in self.geometry["parts"]:
            values = part["surfaces"][0]["normals"]
            index = next((i for i, v in enumerate(values) if v != values[0]), None)
            if index is not None:
                selected = (values, index)
                break
        self.assertIsNotNone(selected)
        values, index = selected
        values[0], values[index] = values[index], values[0]
        self.rebind()
        report = self.refused("NORMAL_COMPARISON", measured=True)
        self.assertEqual(report["geometry"]["corner_map_sha256"], self.passing["geometry"]["corner_map_sha256"])
        self.assertGreater(report["comparison"]["exceeding_corners"], 0)

    def test_raw_copy_cannot_hide_bad_geometry_normals(self):
        self.first_vector()[:] = [3.0, 2.0, 1.0]
        self.rebind(copies=False)
        self.refused("RAW_NORMAL_BINDING", "normal_structure")

    def test_record_order_is_not_identity(self):
        random.Random(235).shuffle(self.observation["records"])
        report = self.run_value()
        self.assertEqual(report["comparison"], self.passing["comparison"])

    def test_complete_key_inventory_required(self):
        for kind in ("missing", "extra", "duplicate", "unknown", "bool", "float"):
            with self.subTest(kind=kind):
                self.setUp()
                records = self.observation["records"]
                if kind == "missing":
                    records.pop()
                elif kind == "extra":
                    records.append(copy.deepcopy(records[0]))
                elif kind == "duplicate":
                    records[-1] = copy.deepcopy(records[0])
                elif kind == "unknown":
                    records[0]["key"][4] = 999999
                elif kind == "bool":
                    records[0]["key"][0] = True
                else:
                    records[0]["key"][0] = float(records[0]["key"][0])
                self.refused(stage="normal_structure")

    def test_swapped_keys_cannot_reassociate_raw_values(self):
        records = self.observation["records"]
        other = next(i for i, row in enumerate(records) if row["normal"] != records[0]["normal"])
        records[0]["key"], records[other]["key"] = records[other]["key"], records[0]["key"]
        self.refused("RAW_NORMAL_BINDING")

    def test_malformed_zero_and_mistyped_normals_refuse(self):
        for value in (None, [], [1, 2], [1, 2, 3, 4], [True, 0, 1], ["1", 0, 1], [0.0, -0.0, 0], [10 ** 400, 0, 1]):
            with self.subTest(value=str(value)[:30]):
                self.setUp()
                self.observation["records"][0]["normal"] = value
                self.refused(stage="normal_structure")

    def test_zero_geometry_normals_are_not_zero_loss(self):
        self.first_vector()[:] = [0.0, 0.0, 0.0]
        self.rebind()
        self.refused("ZERO_NORMAL", "normal_structure")

    def test_geometry_bindings_are_exact(self):
        for key, value in (("bytes", True), ("bytes", 1), ("sha256", "0" * 64), ("corner_map_sha256", "0" * 64)):
            with self.subTest(key=key, value=value):
                self.setUp()
                self.observation["geometry_observation"][key] = value
                self.refused(stage="normal_structure")

    def test_source_frame_origin_and_fields_cannot_be_replaced(self):
        for key, value in (("accepted_program_revision", "sha256:stale"), ("glb_sha256", "0" * 64),
                           ("normal_frame", "blender-world"), ("declared_origin", "native"),
                           ("declared_origin", "unattested-native"), ("schema", "ontokin.c235.normal-observations/9")):
            with self.subTest(key=key, value=value):
                self.setUp()
                self.observation[key] = value
                self.refused(stage="normal_structure")
        self.setUp()
        self.observation["source_key"] = [0, 0, 0, 0]
        self.refused("SCHEMA")

    def test_unattested_native_origin_cannot_grant_acceptance(self):
        self.geometry["declared_origin"] = self.observation["declared_origin"] = "unattested-native"
        self.rebind()
        report = self.run_value()
        self.assertEqual(report["declared_origin"], "unattested-native")
        self.assertFalse(report["limits"]["native_receiving_evidence"])
        self.assertFalse(report["limits"]["native_mapping_attested"])

    def test_exact_rational_boundary_and_adjacent_binary64(self):
        limit = Fraction(1, 500000)
        self.assertTrue(checker._within_tolerance(limit, 0))
        self.assertTrue(checker._within_tolerance(-limit, 0))
        self.assertFalse(checker._within_tolerance(limit + Fraction(1, 10 ** 40), 0))
        self.assertFalse(checker._within_tolerance(-limit - Fraction(1, 10 ** 40), 0))
        below = float(limit)
        self.assertLess(Fraction(below), limit)
        above = math.nextafter(below, math.inf)
        self.assertGreater(Fraction(above), limit)
        self.assertTrue(checker._within_tolerance(below, 0))
        self.assertFalse(checker._within_tolerance(above, 0))

    def test_public_adjacent_boundary_and_raw_preservation(self):
        axis = next(i for i, value in enumerate(self.first_vector()) if value == 0)
        self.first_vector()[axis] = float(Fraction(1, 500000))
        self.rebind()
        report = self.run_value()
        self.assertGreater(report["comparison"]["maximum_absolute_error"], 0)
        self.first_vector()[axis] = math.nextafter(self.first_vector()[axis], math.inf)
        self.rebind()
        failed = self.refused("NORMAL_COMPARISON", measured=True)
        rows = [row for row in failed["comparison"]["rows"] if not all(row["component_pass"])]
        self.assertTrue(rows)
        self.assertTrue(all(row["failed_components"] == ["xyz"[axis]] for row in rows))

    def test_magnitude_loss_survives_angle_normalization(self):
        self.first_vector()[:] = [value * 0.5 for value in self.first_vector()]
        self.rebind()
        report = self.refused("NORMAL_COMPARISON", measured=True)
        self.assertEqual(report["comparison"]["maximum_angular_error_degrees"], 0)
        self.assertGreater(report["comparison"]["maximum_absolute_error"], 0.1)

    def test_opposite_directions_report_180_degrees(self):
        self.first_vector()[:] = [-value for value in self.first_vector()]
        self.rebind()
        report = self.refused("NORMAL_COMPARISON", measured=True)
        self.assertEqual(report["comparison"]["maximum_angular_error_degrees"], 180)

    def test_subnormal_nonzero_direction_remains_measurable(self):
        original = list(self.first_vector())
        self.first_vector()[:] = [math.copysign(math.ulp(0.0), v) if v != 0 else 0.0 for v in original]
        self.rebind()
        report = self.refused("NORMAL_COMPARISON", measured=True)
        self.assertTrue(math.isfinite(report["comparison"]["maximum_angular_error_degrees"]))
        self.assertEqual(report["comparison"]["maximum_angular_error_degrees"], 0)

    def test_huge_vector_magnitude_overflow_is_explicit(self):
        self.first_vector()[:] = [sys.float_info.max] * 3
        self.rebind()
        report = self.refused("NORMAL_COMPARISON", measured=True)
        rows = [row for row in report["comparison"]["rows"] if row["raw_magnitude_overflow"]]
        self.assertTrue(rows)
        self.assertTrue(all(row["raw_magnitude"] is None for row in rows))
        self.assertTrue(all(math.isfinite(row["angular_error_degrees"]) for row in rows))
        json.dumps(report, allow_nan=False)

    def test_signed_zero_preserved_and_zero_error(self):
        axis = next(i for i, value in enumerate(self.first_vector()) if value == 0)
        self.first_vector()[axis] = -0.0
        self.rebind()
        report = self.run_value()
        changed = [row for row in report["comparison"]["rows"] if row["raw_key"][0] == self.geometry["parts"][0]["gltf_node"] and row["raw_key"][4] == 0]
        self.assertTrue(all(math.copysign(1.0, row["raw_normal"][axis]) == -1 for row in changed))
        self.assertEqual(report["comparison"]["maximum_absolute_error"], 0)

    def test_canonical_copy_equality_includes_numeric_type(self):
        first = self.observation["records"][0]["normal"]
        index = next(i for i, value in enumerate(first) if value == 0)
        first[index] = 0
        self.refused("RAW_NORMAL_BINDING")

    def test_known_angular_controls_are_diagnostic(self):
        for actual, expected, angle in (([1, 0, 0], [1, 0, 0], 0), ([0, 1, 0], [1, 0, 0], 90),
                                        ([-1, 0, 0], [1, 0, 0], 180), ([2, 0, 0], [1, 0, 0], 0)):
            self.assertEqual(checker._angle_degrees(actual, expected), angle)

    def test_fresh_admission_cannot_be_replaced_by_old_pass(self):
        self.write()
        with mock.patch.object(checker.c221, "check_package", wraps=checker.c221.check_package) as admission:
            report = checker.check_normals(PACKAGE_ROOT, self.geometry_path, self.normal_path)
            self.assertEqual(admission.call_count, 2)
            self.assertEqual(report["result"], "PASS_CPU_NORMALS")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_normals(tmp, self.geometry_path, self.normal_path)
            self.assertEqual(caught.exception.stage, "authority_admission")
            self.assertEqual(caught.exception.report["geometry"]["result"], "NOT_RUN")

    def test_modified_authority_bytes_refused(self):
        self.write()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in checker.c221.INPUT_PATHS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(PACKAGE_ROOT / relative, target)
                target.chmod(0o644)
            path = root / checker.c221.INPUT_PATHS[3]
            raw = bytearray(path.read_bytes())
            raw[-1] ^= 1
            path.write_bytes(raw)
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_normals(root, self.geometry_path, self.normal_path)
            self.assertEqual(caught.exception.stage, "authority_admission")

    def test_geometry_changed_between_check_and_reread_refused(self):
        self.write()
        original = checker.c222.check_observations

        def change_after_check(*args):
            report = original(*args)
            self.geometry_path.write_bytes(self.geometry_path.read_bytes() + b"\n")
            return report

        with mock.patch.object(checker.c222, "check_observations", side_effect=change_after_check):
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_normals(PACKAGE_ROOT, self.geometry_path, self.normal_path)
        self.assertEqual(caught.exception.code, "GEOMETRY_CHANGED")
        self.assertEqual(caught.exception.stage, "geometry_correspondence")

    def test_nonfinite_and_malformed_json_refuse(self):
        self.geometry_path.write_bytes(encode(self.geometry))
        for raw in (b'{"schema":1,"schema":2}', b'{', b'NaN', b'Infinity', b'\xff'):
            with self.subTest(raw=raw):
                self.normal_path.write_bytes(raw)
                with self.assertRaises(checker.CheckError) as caught:
                    checker.check_normals(PACKAGE_ROOT, self.geometry_path, self.normal_path)
                self.assertEqual(caught.exception.stage, "normal_structure")
                self.assertEqual(caught.exception.report["comparison"]["result"], "NOT_RUN")

    def test_geometry_malformed_normals_fail_before_comparison(self):
        self.geometry["parts"][0]["surfaces"][0]["normals"][0] = [1, 0]
        self.refused(stage="geometry_correspondence")

    def test_unsafe_and_nonregular_observations_refuse(self):
        self.write()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            symlink = root / "link.json"
            symlink.symlink_to(self.normal_path)
            fifo = root / "fifo"
            os.mkfifo(fifo)
            for path in (symlink, fifo, root / "missing"):
                with self.subTest(path=path.name):
                    with self.assertRaises(checker.CheckError) as caught:
                        checker.check_normals(PACKAGE_ROOT, self.geometry_path, path)
                    self.assertEqual(caught.exception.stage, "normal_read")
            with self.assertRaises(checker.CheckError):
                checker._read_normal_observation(str(root / ".." / "elsewhere"))

    def test_size_bounds_before_parsing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "oversized.json"
            with path.open("wb") as stream:
                stream.truncate(checker.MAX_NORMAL_OBSERVATION_BYTES + 1)
            with self.assertRaises(checker.CheckError) as caught:
                checker._read_normal_observation(path)
            self.assertEqual(caught.exception.code, "SIZE")

    def test_cli_reports_pass_and_complete_measured_failure(self):
        self.write()
        command = [sys.executable, "-IB", str(CHECKER), "--package-root", str(PACKAGE_ROOT),
                   "--geometry-observations", str(self.geometry_path), "--normal-observations", str(self.normal_path)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.passing)
        self.first_vector()[:] = [value * 2 for value in self.first_vector()]
        self.rebind()
        self.write()
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["result"], "FAIL_STRICT_NORMAL_LIMIT")
        self.assertEqual(len(report["comparison"]["rows"]), 23400)


def main(argv=None):
    global PACKAGE_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    PACKAGE_ROOT = Path(args.package_root).absolute()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NormalControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if args.report:
        report = {"schema": "ontokin.c235.author-controls/0.1", "tests": result.testsRun,
                  "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                  "passed": result.wasSuccessful(), "target_starts": 0, "source_evaluations": 0,
                  "python": sys.version, "platform": sys.platform,
                  "scope": "Finite CPU normal observation, complete independent raw/source corner oracle and strict loss controls"}
        Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
