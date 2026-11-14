#!/usr/bin/env python3
"""Finite package-dependent author controls; no native application starts."""

from __future__ import annotations

import argparse
import copy
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
import unittest
from unittest import mock


sys.dont_write_bytecode = True
CHECKER = Path(__file__).absolute().parents[1] / "check_materials.py"
SPEC = importlib.util.spec_from_file_location("c234_author_checker", CHECKER)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
PACKAGE_ROOT = None


def fixtures(package_root):
    """Construct observations from source bytes without checker decode helpers."""
    inputs = Path(package_root) / "agent-results/namespace-repair/run-01/inputs"
    raw = (inputs / "after.glb").read_bytes()
    length = struct.unpack_from("<I", raw, 12)[0]
    source = json.loads(raw[20:20 + length])
    binary = raw[28 + length:]
    semantic = json.loads((inputs / "after.semantic.json").read_text())
    objects = {row["geometry_binding"]["node"]: row for row in semantic["objects"]}

    def accessor(index, format_string):
        spec = source["accessors"][index]
        view = source["bufferViews"][spec["bufferView"]]
        offset = view.get("byteOffset", 0) + spec.get("byteOffset", 0)
        width = struct.calcsize(format_string)
        return [list(struct.unpack_from(format_string, binary, offset + i * width)) for i in range(spec["count"])]

    def encoded_color(value):
        return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055

    geometry_parts, material_parts = [], []
    for index, node in enumerate(source["nodes"]):
        if "mesh" not in node:
            continue
        meaning = objects[index]
        common = {"gltf_node": index, "gltf_mesh": node["mesh"], "element_id": meaning["element_id"],
                  "source_path": meaning["path"], "native_node_id": "author-node-" + str(index)}
        surfaces, material_surfaces = [], []
        for number, primitive in enumerate(source["meshes"][node["mesh"]]["primitives"]):
            original_indices = [value[0] for value in accessor(primitive["indices"], "<H")]
            reversed_indices = []
            for offset in range(0, len(original_indices), 3):
                a, b, c = original_indices[offset:offset + 3]
                reversed_indices.extend((a, c, b))
            surfaces.append({"gltf_primitive": number, "material_index": primitive["material"],
                             "positions": accessor(primitive["attributes"]["POSITION"], "<3f"),
                             "normals": accessor(primitive["attributes"]["NORMAL"], "<3f"), "indices": reversed_indices})
            material = source["materials"][primitive["material"]]
            pbr = material["pbrMetallicRoughness"]
            rgba = pbr["baseColorFactor"]
            material_surfaces.append({"gltf_primitive": number, "material_index": primitive["material"],
                "native_material_id": "author-material-copy-" + str(index),
                "raw": {"albedo_storage": "srgb-rgb-linear-alpha", "albedo_rgb": [encoded_color(v) for v in rgba[:3]],
                        "alpha": rgba[3], "metallic": pbr["metallicFactor"], "roughness": pbr["roughnessFactor"],
                        "cull_mode": "disabled" if material.get("doubleSided", False) else "back",
                        "transparency_mode": "disabled"}})
        geometry_parts.append({**common, "display_name": "Author synthetic fixture", "surfaces": surfaces})
        material_parts.append({**common, "surfaces": material_surfaces})
    identity = {"declared_origin": "synthetic", "accepted_program_revision": semantic["binding"]["accepted_program_revision"],
                "glb_sha256": hashlib.sha256(raw).hexdigest()}
    geometry = {"schema": "ontokin.c222.geometry-observations/0.1", **identity,
                "coordinate_system": {"position_unit": "m", "basis": "gltf-rh-y-up-identity", "winding": "godot-clockwise-reverse-once"},
                "parts": geometry_parts}
    geometry_bytes = json.dumps(geometry, sort_keys=True, separators=(",", ":")).encode()
    material = {"schema": "ontokin.c234.material-observations/0.1", **identity,
                "geometry_observation": {"bytes": len(geometry_bytes), "sha256": hashlib.sha256(geometry_bytes).hexdigest()},
                "parts": material_parts}
    return geometry_bytes, material


class MaterialControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="ontokin-c234-author-")
        cls.root = Path(cls.directory.name)
        cls.geometry_path = cls.root / "geometry.json"
        cls.material_path = cls.root / "material.json"
        cls.geometry_raw, cls.original = fixtures(PACKAGE_ROOT)
        cls.geometry_path.write_bytes(cls.geometry_raw)
        cls.material_path.write_text(json.dumps(cls.original))
        cls.passing = checker.check_materials(PACKAGE_ROOT, cls.geometry_path, cls.material_path)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.value = copy.deepcopy(self.original)
        self.geometry_path.write_bytes(self.geometry_raw)

    def raw(self):
        return self.value["parts"][0]["surfaces"][0]["raw"]

    def run_value(self):
        self.material_path.write_text(json.dumps(self.value))
        return checker.check_materials(PACKAGE_ROOT, self.geometry_path, self.material_path)

    def refused(self, stage=None, code=None):
        with self.assertRaises(checker.CheckError) as caught:
            self.run_value()
        error = caught.exception
        self.assertEqual(error.report["result"], "FAIL_CLOSED")
        if stage:
            self.assertEqual(error.stage, stage)
        if code:
            self.assertEqual(error.code, code)
        self.assertIs(error.report["limits"]["target_execution_authorized"], False)
        return error.report

    def test_complete_material_inventory_and_limits(self):
        result = self.passing
        self.assertEqual(result["result"], "PASS_CPU_MATERIALS")
        self.assertEqual(result["admission"]["result"], "PASS_CPU_AUTHORITY_BINDING")
        self.assertEqual(result["geometry"]["structure"]["corners"], 23400)
        self.assertEqual(result["structure"]["parts"], 18)
        self.assertEqual(result["structure"]["source_materials"], 2)
        self.assertEqual(result["comparison"]["numeric_components_compared"], 108)
        self.assertEqual(result["comparison"]["exact_mode_checks"], 36)
        self.assertEqual(result["comparison"]["failed_associations"], 0)
        self.assertFalse(result["limits"]["native_receiving_evidence"])
        for key in ("target_starts", "native_version_starts", "source_evaluations", "exports", "imports", "renders", "scene_writes"):
            self.assertEqual(result["limits"][key], 0)

    def test_raw_values_and_normalized_values_are_separate(self):
        for row in self.passing["comparison"]["rows"]:
            self.assertNotEqual(row["raw"]["albedo_rgb"], row["normalized"]["linear_rgba"][:3])
            self.assertEqual(row["raw"]["alpha"], row["normalized"]["linear_rgba"][3])
            self.assertTrue(all(row["checks"].values()))
            self.assertEqual(row["source"]["alpha_mode"], "OPAQUE")
            self.assertIs(row["source"]["double_sided"], False)

    def test_part_order_and_native_labels_do_not_establish_provenance(self):
        self.value["parts"].reverse()
        self.value["declared_origin"] = "unattested-native"
        report = self.run_value()
        self.assertEqual(report["comparison"], self.passing["comparison"])
        self.assertFalse(report["limits"]["native_mapping_attested"])

    def test_missing_duplicate_and_extra_parts(self):
        for change in (lambda a: a.pop(), lambda a: a.append(copy.deepcopy(a[0])), lambda a: a.__setitem__(1, copy.deepcopy(a[0]))):
            with self.subTest(change=str(change)):
                self.value = copy.deepcopy(self.original)
                change(self.value["parts"])
                self.refused("material_structure")

    def test_swapped_source_part_fields(self):
        for key in ("gltf_node", "gltf_mesh", "element_id", "source_path", "native_node_id"):
            with self.subTest(key=key):
                self.value = copy.deepcopy(self.original)
                first, second = self.value["parts"][:2]
                first[key], second[key] = second[key], first[key]
                self.refused("material_structure")

    def test_missing_duplicate_and_wrong_material_associations(self):
        for modification in ("missing", "duplicate", "material", "primitive"):
            with self.subTest(modification=modification):
                self.value = copy.deepcopy(self.original)
                surfaces = self.value["parts"][0]["surfaces"]
                if modification == "missing":
                    surfaces.clear()
                elif modification == "duplicate":
                    surfaces.append(copy.deepcopy(surfaces[0]))
                elif modification == "material":
                    surfaces[0]["material_index"] = 1
                else:
                    surfaces[0]["gltf_primitive"] = 1
                self.refused("material_structure")

    def test_indices_and_geometry_size_are_typed(self):
        for value in (True, 0.0, "0", -1):
            for location in ("node", "mesh", "primitive", "material", "bytes"):
                with self.subTest(value=value, location=location):
                    self.value = copy.deepcopy(self.original)
                    part = self.value["parts"][0]
                    if location == "bytes":
                        self.value["geometry_observation"]["bytes"] = value
                    elif location in ("node", "mesh"):
                        part["gltf_" + location] = value
                    else:
                        part["surfaces"][0]["gltf_primitive" if location == "primitive" else "material_index"] = value
                    self.refused("material_structure")

    def test_geometry_hash_size_and_label_are_bound(self):
        for kind in ("sha256", "bytes", "native_node_id"):
            self.value = copy.deepcopy(self.original)
            if kind == "sha256":
                self.value["geometry_observation"][kind] = "0" * 64
            elif kind == "bytes":
                self.value["geometry_observation"][kind] += 1
            else:
                self.value["parts"][0][kind] += "-swapped"
            self.refused("material_structure", "GEOMETRY_BINDING")

    def test_fresh_geometry_is_checked_before_materials(self):
        geometry = json.loads(self.geometry_raw)
        geometry["parts"][0]["surfaces"][0]["positions"][0][0] += 1
        self.geometry_path.write_text(json.dumps(geometry))
        report = self.refused("geometry_correspondence")
        self.assertEqual(report["admission"]["result"], "PASS_CPU_AUTHORITY_BINDING")
        self.assertEqual(report["structure"]["result"], "NOT_RUN")

    def test_geometry_replacement_between_check_and_read_fails(self):
        original = checker.c222.check_observations

        def replaced(*args):
            result = original(*args)
            geometry = json.loads(self.geometry_raw)
            geometry["parts"][0]["display_name"] += " changed"
            self.geometry_path.write_text(json.dumps(geometry))
            return result

        with mock.patch.object(checker.c222, "check_observations", side_effect=replaced):
            self.refused("geometry_correspondence", "GEOMETRY_CHANGED")

    def test_missing_extra_and_malformed_raw_fields(self):
        for key in tuple(self.raw()):
            self.value = copy.deepcopy(self.original)
            del self.raw()[key]
            self.refused("material_structure", "SCHEMA")
        self.value = copy.deepcopy(self.original)
        self.raw()["extra"] = 1
        self.refused("material_structure", "SCHEMA")
        self.value = copy.deepcopy(self.original)
        self.raw()["albedo_rgb"] = [0.1, 0.2]
        self.refused("material_structure", "PARAMETER")

    def test_nonfinite_boolean_and_out_of_range_parameters(self):
        for bad in (float("nan"), float("inf"), -float("inf"), True, None, "0.7", -0.1, 1.1):
            with self.subTest(value=bad):
                self.value = copy.deepcopy(self.original)
                self.raw()["roughness"] = bad
                self.refused("material_structure")

    def test_unknown_color_and_modes_fail_structure(self):
        for key, value in (("albedo_storage", "linear-rgb-linear-alpha"), ("albedo_storage", "guess"),
                           ("cull_mode", "default"), ("transparency_mode", "unknown")):
            self.value = copy.deepcopy(self.original)
            self.raw()[key] = value
            self.refused("material_structure")

    def test_linear_and_double_encoded_rgb_fail_comparison(self):
        self.raw()["albedo_rgb"] = [0.45, 0.45, 0.5]
        self.refused("material_comparison", "MATERIAL_COMPARISON")
        self.value = copy.deepcopy(self.original)
        self.raw()["albedo_rgb"] = [1.055 * v ** (1 / 2.4) - 0.055 for v in self.raw()["albedo_rgb"]]
        self.refused("material_comparison", "MATERIAL_COMPARISON")

    def test_alpha_remains_linear_near_opaque_boundary(self):
        self.raw()["alpha"] = 1 - 0.000001
        report = self.run_value()
        first = report["comparison"]["rows"][0]
        self.assertEqual(first["normalized"]["linear_rgba"][3], self.raw()["alpha"])
        self.assertTrue(first["checks"]["alpha"])
        self.assertGreater(abs(checker._srgb_to_linear(self.raw()["alpha"]) - 1), 0.000002)

    def test_wrong_parameters_retain_full_failed_comparison(self):
        for key, value in (("alpha", 0.5), ("metallic", 0.1), ("roughness", 0.9)):
            self.value = copy.deepcopy(self.original)
            self.raw()[key] = value
            report = self.refused("material_comparison")
            self.assertEqual(len(report["comparison"]["rows"]), 18)
            self.assertEqual(report["comparison"]["failed_associations"], 1)
            self.assertFalse(report["comparison"]["rows"][0]["checks"][key])

    def test_culling_and_opacity_modes_are_exact(self):
        for key, value in (("cull_mode", "front"), ("cull_mode", "disabled"),
                           ("transparency_mode", "alpha"), ("transparency_mode", "alpha-scissor")):
            self.value = copy.deepcopy(self.original)
            self.raw()[key] = value
            self.refused("material_comparison")

    def test_exact_tolerance_boundary_and_adjacent_values(self):
        for value, passes in ((0.000002, True), (math.nextafter(0.000002, 0.0), True), (math.nextafter(0.000002, math.inf), False)):
            with self.subTest(value=value):
                self.value = copy.deepcopy(self.original)
                self.raw()["metallic"] = value
                if passes:
                    self.assertEqual(self.run_value()["result"], "PASS_CPU_MATERIALS")
                else:
                    self.refused("material_comparison")

    def test_shared_native_resource_consistency_and_copies(self):
        for part in self.value["parts"]:
            surface = part["surfaces"][0]
            surface["native_material_id"] = "shared-" + str(surface["material_index"])
        self.assertEqual(self.run_value()["structure"]["declared_native_resources"], 2)
        self.raw()["roughness"] += 0.000001
        self.refused("material_structure", "RESOURCE_BINDING")
        self.value = copy.deepcopy(self.original)
        for part in self.value["parts"]:
            part["surfaces"][0]["native_material_id"] = "same-for-both-source-materials"
        self.refused("material_structure", "RESOURCE_BINDING")

    def test_initial_admission_refuses_changed_locked_bytes(self):
        with tempfile.TemporaryDirectory(prefix="c234-author-changed-") as temporary:
            root = Path(temporary)
            bindings, _ = checker.c221.load_authority()
            for item in bindings["items"]:
                destination = root / item["packagePath"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(Path(PACKAGE_ROOT) / item["packagePath"], destination)
                destination.chmod(item["mode"])
            glb = root / bindings["items"][0]["packagePath"]
            modified = bytearray(glb.read_bytes())
            modified[-1] ^= 1
            glb.write_bytes(modified)
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_materials(root, self.geometry_path, self.material_path)
            self.assertEqual(caught.exception.stage, "authority_admission")
            self.assertEqual(caught.exception.report["geometry"]["result"], "NOT_RUN")

    def test_bad_json_and_forged_report_fail_closed(self):
        for raw in (b'{"schema":1,"schema":2}', b'\xff', b'{', json.dumps(self.passing).encode()):
            self.material_path.write_bytes(raw)
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_materials(PACKAGE_ROOT, self.geometry_path, self.material_path)
            self.assertEqual(caught.exception.stage, "material_structure")

    def test_safe_read_missing_symlink_fifo_and_size(self):
        self.material_path.write_text(json.dumps(self.value))
        for name in ("missing", "link", "fifo", "empty", "large"):
            path = self.root / name
            if name == "link":
                path.symlink_to(self.material_path)
            elif name == "fifo":
                os.mkfifo(path)
            elif name == "empty":
                path.write_bytes(b"")
            elif name == "large":
                path.write_bytes(b" " * (checker.MAX_MATERIAL_OBSERVATION_BYTES + 1))
            with self.assertRaises(checker.CheckError) as caught:
                checker.check_materials(PACKAGE_ROOT, self.geometry_path, path)
            self.assertEqual(caught.exception.stage, "material_read")

    def test_piecewise_transfer_and_alpha_internal_seam(self):
        for value in (0.0, 0.04045, math.nextafter(0.04045, math.inf), 0.5, 1.0):
            expected = value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            self.assertEqual(checker._srgb_to_linear(value), expected)
        raw = copy.deepcopy(self.raw())
        raw["alpha"] = 0.4
        self.assertEqual(checker._normalize_raw(raw)["linear_rgba"][3], 0.4)

    def test_cli_success_and_failure_stage_accounting(self):
        self.material_path.write_text(json.dumps(self.value))
        command = [sys.executable, "-IB", str(CHECKER), "--package-root", str(PACKAGE_ROOT),
                   "--geometry-observations", str(self.geometry_path), "--material-observations", str(self.material_path)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["result"], "PASS_CPU_MATERIALS")
        self.raw()["roughness"] = 0.9
        self.material_path.write_text(json.dumps(self.value))
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)["error"]["stage"], "material_comparison")


def main(argv=None):
    global PACKAGE_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    args = parser.parse_args(argv)
    PACKAGE_ROOT = Path(args.package_root).absolute()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MaterialControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
