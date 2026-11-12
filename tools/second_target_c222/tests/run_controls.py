#!/usr/bin/env python3
"""CPU-only author controls; requires the preserved finite input package."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest


sys.dont_write_bytecode = True
CHECKER = Path(__file__).absolute().parents[1] / "check_observations.py"
SPEC = importlib.util.spec_from_file_location("c222_author_checker", CHECKER)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
PACKAGE_ROOT = None


def fixture(package_root):
    """Decode fixture arrays independently of the checker's geometry helpers."""
    base = Path(package_root) / "agent-results/namespace-repair/run-01/inputs"
    raw = (base / "after.glb").read_bytes()
    json_size = struct.unpack_from("<I", raw, 12)[0]
    glb = json.loads(raw[20:20 + json_size])
    binary = raw[28 + json_size:]
    semantic = json.loads((base / "after.semantic.json").read_text())
    by_node = {row["geometry_binding"]["node"]: row for row in semantic["objects"]}

    def accessor(index, format_string):
        spec = glb["accessors"][index]
        view = glb["bufferViews"][spec["bufferView"]]
        offset = view.get("byteOffset", 0) + spec.get("byteOffset", 0)
        width = struct.calcsize(format_string)
        return [list(struct.unpack_from(format_string, binary, offset + i * width)) for i in range(spec["count"])]

    parts = []
    for node_index, node in enumerate(glb["nodes"]):
        if "mesh" not in node:
            continue
        source = by_node[node_index]
        surfaces = []
        for primitive_index, primitive in enumerate(glb["meshes"][node["mesh"]]["primitives"]):
            source_indices = [v[0] for v in accessor(primitive["indices"], "<H")]
            indices = []
            for i in range(0, len(source_indices), 3):
                a, b, c = source_indices[i:i + 3]
                indices.extend((a, c, b))
            surfaces.append({"gltf_primitive": primitive_index, "material_index": primitive["material"],
                             "positions": accessor(primitive["attributes"]["POSITION"], "<3f"),
                             "normals": accessor(primitive["attributes"]["NORMAL"], "<3f"), "indices": indices})
        parts.append({"gltf_node": node_index, "gltf_mesh": node["mesh"], "element_id": source["element_id"],
                      "source_path": source["path"], "native_node_id": "synthetic-node-" + str(node_index),
                      "display_name": "Synthetic " + str(node_index), "surfaces": surfaces})
    return {"schema": checker.SCHEMA, "declared_origin": "synthetic",
            "accepted_program_revision": checker.c221.ACCEPTED_REVISION,
            "glb_sha256": checker.c221.digest(raw), "coordinate_system": copy.deepcopy(checker.COORDINATE_SYSTEM),
            "parts": parts}


class ObservationControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = checker._load_authority(PACKAGE_ROOT)
        cls.original = fixture(PACKAGE_ROOT)
        cls.passing = checker.validate_observations(cls.original, cls.authority)

    def setUp(self):
        self.value = copy.deepcopy(self.original)

    def surface(self):
        return self.value["parts"][0]["surfaces"][0]

    def refused(self, code, value=None):
        with self.assertRaises(checker.CheckError) as raised:
            checker.validate_observations(self.value if value is None else value, self.authority)
        self.assertEqual(code, raised.exception.code)

    def test_full_inventory_and_exact_corner_keys(self):
        report = self.passing
        self.assertEqual(report["structure"]["parts"], 18)
        self.assertEqual(report["structure"]["triangles"], 7800)
        mapping = report["correspondence"]["corner_map"]
        self.assertEqual(len(mapping), 23400)
        self.assertEqual(len({tuple(row[:4]) for row in mapping}), 23400)
        for row in mapping:
            self.assertEqual(row[1], row[6])
            self.assertEqual(row[2], row[7])
            self.assertEqual(row[8], (0, 2, 1)[row[3]])

    def test_names_and_normals_cannot_change_mapping(self):
        for part in self.value["parts"]:
            part["display_name"] = "same arbitrary name"
            for surface in part["surfaces"]:
                surface["normals"] = [[0.123, 0.456, 0.789] for _ in surface["normals"]]
        result = checker.validate_observations(self.value, self.authority)
        self.assertEqual(result["correspondence"], self.passing["correspondence"])

    def test_signed_zero_only(self):
        changed = 0
        for part in self.value["parts"]:
            for surface in part["surfaces"]:
                for position in surface["positions"]:
                    for axis in range(3):
                        if position[axis] == 0:
                            position[axis] = -0.0
                            changed += 1
        self.assertGreater(changed, 0)
        self.assertEqual(checker.validate_observations(self.value, self.authority)["correspondence"],
                         self.passing["correspondence"])

    def test_cyclic_order_and_vertex_reindexing(self):
        surface = self.surface()
        old_count = len(surface["positions"])
        surface["positions"].reverse()
        surface["normals"].reverse()
        surface["indices"] = [old_count - 1 - i for i in surface["indices"]]
        surface["indices"] = [value for i in range(0, len(surface["indices"]), 3)
                              for value in surface["indices"][i + 1:i + 3] + surface["indices"][i:i + 1]]
        result = checker.validate_observations(self.value, self.authority)
        self.assertEqual(result["structure"]["corners"], 23400)

    def test_part_reordering_is_irrelevant(self):
        self.value["parts"].reverse()
        self.assertEqual(checker.validate_observations(self.value, self.authority)["correspondence"],
                         self.passing["correspondence"])

    def test_swapped_identity_rejected(self):
        self.value["parts"][0]["element_id"], self.value["parts"][1]["element_id"] = (
            self.value["parts"][1]["element_id"], self.value["parts"][0]["element_id"])
        self.refused("IDENTITY")

    def test_duplicate_node_and_native_label_rejected(self):
        self.value["parts"][1]["gltf_node"] = self.value["parts"][0]["gltf_node"]
        self.refused("IDENTITY")
        self.value = copy.deepcopy(self.original)
        self.value["parts"][1]["native_node_id"] = self.value["parts"][0]["native_node_id"]
        self.refused("IDENTITY")

    def test_missing_and_extra_parts_rejected(self):
        self.value["parts"].pop()
        self.refused("COUNT")
        self.value["parts"].extend(copy.deepcopy(self.original["parts"][-2:]))
        self.refused("COUNT")

    def test_unit_basis_winding_claims_rejected(self):
        for key, value in (("position_unit", "cm"), ("basis", "blender-z-up"), ("winding", "unchanged")):
            with self.subTest(key=key):
                bad = copy.deepcopy(self.original)
                bad["coordinate_system"][key] = value
                self.refused("COORDINATES", bad)

    def test_wrong_raw_winding_rejected(self):
        indices = self.surface()["indices"]
        indices[1], indices[2] = indices[2], indices[1]
        self.refused("MISSING_CORRESPONDENCE")

    def test_actual_scale_and_axis_changes_rejected(self):
        for change in (lambda p: [v * 100 for v in p], lambda p: [p[0], p[2], -p[1]]):
            self.value = copy.deepcopy(self.original)
            self.surface()["positions"] = [change(p) for p in self.surface()["positions"]]
            self.refused("MISSING_CORRESPONDENCE")

    def test_small_position_change_has_no_tolerance(self):
        self.surface()["positions"][0][0] += 1e-12
        self.refused("MISSING_CORRESPONDENCE")

    def test_duplicate_triangle_rejected(self):
        # Choose a shared-vertex triangle so this isolates correspondence;
        # duplicating the first box face also creates an unused vertex.
        changed = False
        for part in self.value["parts"]:
            for surface in part["surfaces"]:
                indices = surface["indices"]
                for offset in range(3, len(indices), 3):
                    if set(indices[:offset] + indices[offset + 3:]) == set(indices):
                        indices[offset:offset + 3] = indices[:3]
                        changed = True
                        break
                if changed:
                    break
            if changed:
                break
        self.assertTrue(changed)
        self.refused("DUPLICATE_CORRESPONDENCE")

    def test_truncated_indices_and_normals_rejected(self):
        self.surface()["indices"].pop()
        self.refused("COUNT")
        self.value = copy.deepcopy(self.original)
        self.surface()["normals"].pop()
        self.refused("COUNT")

    def test_unused_geometry_rejected(self):
        self.surface()["positions"].append([9, 9, 9])
        self.surface()["normals"].append([0, 1, 0])
        self.refused("EXTRA_GEOMETRY")

    def test_wrong_primitive_material_and_mesh_rejected(self):
        for field, code in (("gltf_primitive", "IDENTITY"), ("material_index", "MATERIAL_BINDING")):
            self.value = copy.deepcopy(self.original)
            self.surface()[field] = 999
            self.refused(code)
        self.value = copy.deepcopy(self.original)
        self.value["parts"][0]["gltf_mesh"] = 999
        self.refused("IDENTITY")

    def test_boolean_indices_and_nonfinite_vectors_rejected(self):
        self.surface()["indices"][0] = True
        self.refused("INDEX")
        for array in ("positions", "normals"):
            for bad in (float("nan"), float("inf"), True):
                self.value = copy.deepcopy(self.original)
                self.surface()[array][0][0] = bad
                self.refused("FINITE")

    def test_schema_and_stale_source_rejected(self):
        self.value["extra"] = 1
        self.refused("SCHEMA")
        for key in ("accepted_program_revision", "glb_sha256"):
            self.value = copy.deepcopy(self.original)
            self.value[key] = "stale"
            self.refused("IDENTITY")

    def test_normals_cannot_disambiguate_source_candidates(self):
        source = copy.deepcopy(self.authority["parts"][0]["surfaces"][0]["triangles"])
        duplicate = copy.deepcopy(source[0])
        duplicate["index"] = 9999
        duplicate["normals"] = [[1, 0, 0]] * 3
        source[0]["normals"] = [[0, 1, 0]] * 3
        source.append(duplicate)
        with self.assertRaises(checker.CheckError) as raised:
            checker._match_surface(source, self.surface())
        self.assertEqual(raised.exception.code, "AMBIGUOUS_CORRESPONDENCE")

    def test_degenerate_corner_rotation_rejected(self):
        triangle = {"index": 0, "vertices": [0, 1, 2], "positions": [(0, 0, 0)] * 3,
                    "keys": [(0, 0, 0, i) for i in range(3)]}
        surface = {"positions": [[0, 0, 0]] * 3, "indices": [0, 2, 1]}
        with self.assertRaises(checker.CheckError) as raised:
            checker._match_surface([triangle], surface)
        self.assertEqual(raised.exception.code, "AMBIGUOUS_CORRESPONDENCE")

    def test_public_cli_api_agree_and_output_is_cpu_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.json"
            path.write_text(json.dumps(self.value))
            api = checker.check_observations(PACKAGE_ROOT, path)
            run = subprocess.run([sys.executable, "-IB", str(CHECKER), "--package-root", str(PACKAGE_ROOT),
                                  "--observations", str(path)], capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout), api)
            self.assertEqual(api["result"], "PASS_CPU_CORRESPONDENCE")
            self.assertFalse(api["limits"]["native_receiving_evidence"])
            self.assertFalse(api["limits"]["target_execution_authorized"])

    def test_public_malformed_json_and_unsafe_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            for raw in (b'{"schema":1,"schema":2}', b'{', b'NaN', b'\xff'):
                path.write_bytes(raw)
                with self.assertRaises(checker.CheckError):
                    checker.check_observations(PACKAGE_ROOT, path)
            target = Path(tmp) / "link.json"
            target.symlink_to(path)
            with self.assertRaises(checker.CheckError) as raised:
                checker.check_observations(PACKAGE_ROOT, target)
            self.assertEqual(raised.exception.stage, "observation_read")

    def test_empty_package_cannot_admit_forged_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observations.json"
            path.write_text(json.dumps(self.value))
            with self.assertRaises(checker.CheckError) as raised:
                checker.check_observations(tmp, path)
            self.assertEqual(raised.exception.stage, "authority_admission")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    args, test_args = parser.parse_known_args()
    PACKAGE_ROOT = Path(args.package_root)
    unittest.main(argv=[sys.argv[0], *test_args], verbosity=2)
