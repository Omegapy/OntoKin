"""C093 controls for the separately versioned native parent-site oracle.

The three stream hashes below come from the C092 independent source-only
expectation cf5dee14622c9b9caad5403680fc8cb875361807b007fb526f412dc523ed1694,
which was frozen before artifact inspection. No exporter, producer geometry
constructor, GLB artifact or native observation supplies these fixture streams.
These focused controls do not claim the full native destination gate.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct
from types import SimpleNamespace
import unittest

from tools import verify_torque_native_dense_c093 as native


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "docs/language-design/torque-v0.1/freeze"
KEY = "helper:carrier.tip.frame:joint_parent_site"
METADATA = {
    "kind": "visual_helper", "helper_kind": "joint_parent_site",
    "physical_participation": "none", "related_element_id": ["torque-cases", "demo", "hold"],
    "joint_path": "hold", "frame_path": "carrier.tip.frame",
    "meaning": "Parent site marker remains after release; it does not indicate an active constraint.",
}
MATERIAL = {"baseColorFactor": [.9, .65, .08, 1.], "metallicFactor": 0., "roughnessFactor": .7}
STREAM_HASHES = {
    "position": "62c682cbbf2db85a4f82d1f1a6d9cd524a7544d9a86106c00027ef032ec1fff5",
    "normal": "4440ad4677832768190825f99fef268a9a3acb04c428da5018768cc4360d5f0b",
    "indices": "7e6e9309203119ae4a5c2a1fdbedba53557a4ef238f3a7d6711d8a7ab198324f",
}


def independent_sphere_streams():
    """Explicit source construction, independently fixed by the frozen hashes."""
    normals = [(0., 1., 0.)]
    for band in range(1, 6):
        theta = math.pi * band / 6
        for longitude in range(12):
            phi = 2 * math.pi * longitude / 12
            normals.append((math.sin(theta) * math.cos(phi), math.cos(theta),
                            math.sin(theta) * math.sin(phi)))
    normals.append((0., -1., 0.))
    positions = [(0.025 * x, 0.025 * y, 0.025 * z) for x, y, z in normals]
    indices = []
    for longitude in range(12):
        indices.extend((0, 1 + (longitude + 1) % 12, 1 + longitude))
    for band in range(4):
        upper, lower = 1 + band * 12, 1 + (band + 1) * 12
        for longitude in range(12):
            following = (longitude + 1) % 12
            indices.extend((upper + longitude, upper + following, lower + longitude,
                            upper + following, lower + following, lower + longitude))
    for longitude in range(12):
        indices.extend((49 + longitude, 49 + (longitude + 1) % 12, 61))
    return [x for point in positions for x in point], [x for point in normals for x in point], indices


def fixture(*, positions=None, normals=None, indices=None, material=None):
    default_positions, default_normals, default_indices = independent_sphere_streams()
    positions = default_positions if positions is None else positions
    normals = default_normals if normals is None else normals
    indices = default_indices if indices is None else indices
    material = copy.deepcopy(MATERIAL if material is None else material)
    position_bytes = struct.pack("<" + "f" * len(positions), *positions)
    normal_bytes = struct.pack("<" + "f" * len(normals), *normals)
    index_bytes = struct.pack("<" + "H" * len(indices), *indices)
    binary = position_bytes + normal_bytes + index_bytes
    document = {
        "nodes": [{"name": "[visual helper] hold parent site", "mesh": 0,
                   "extras": {"ontokin": copy.deepcopy(METADATA)}}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1},
                                      "indices": 2, "material": 0, "mode": 4}]}],
        "materials": [{"pbrMetallicRoughness": material}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len(position_bytes)},
            {"buffer": 0, "byteOffset": len(position_bytes), "byteLength": len(normal_bytes)},
            {"buffer": 0, "byteOffset": len(position_bytes) + len(normal_bytes), "byteLength": len(index_bytes)}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(positions) // 3, "type": "VEC3"},
            {"bufferView": 1, "componentType": 5126, "count": len(normals) // 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": len(indices), "type": "SCALAR"}],
    }
    decoded_positions = list(struct.unpack("<" + "f" * len(positions), position_bytes))
    decoded_normals = list(struct.unpack("<" + "f" * len(normals), normal_bytes))
    inventory = {"images": [], "meshes": [{
        "carrier": KEY, "association": {"meshes": 0, "primitives": 0},
        "attributes": {"position": {"values": decoded_positions, "normalized": False},
                       "normal": {"values": decoded_normals, "normalized": False}},
        "indices": list(indices),
        "materials": [{"color": material["baseColorFactor"][:3], "opacity": material["baseColorFactor"][3],
                       "metalness": material["metallicFactor"], "roughness": material["roughnessFactor"],
                       "texture": "baseColorTexture" in material}]}]}
    return document, binary, inventory


class TorqueNativeParentSiteC093Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ontokin.texture_bundle import load_texture_file_manifest
        from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
        from ontokin.construction import compile_construction
        table = json.loads((FROZEN / "delivery-cases.json").read_bytes())
        cls.case = next(row for row in table["cases"] if row["id"] == "delivery-p28-release-then-torque")
        bundle = load_texture_file_manifest(FROZEN / cls.case["file_manifest"])
        if bundle.program_revision != "sha256:192424a2eb5c207a5e85989b7a466842947466218ebe6d0684b3d5ee041b92cc":
            raise AssertionError("Frozen p28 source changed")
        ledger = SharedExecutionBudget(HostPolicy(**cls.case["host_policy"]))
        admit_entry_budget(bundle.entry, ledger, profile="torque-0.1")
        cls.source_model = compile_construction(bundle, execution_budget=ledger).model
        cls.joint = cls.source_model.joints["hold"]
        if not (cls.joint.kind == "grip" and cls.joint.axis is None and cls.joint.parent == "carrier.tip"
                and cls.joint.child == "ball.origin" and list(cls.joint.element_id) == METADATA["related_element_id"]):
            raise AssertionError("Frozen source connection changed")

    def model(self):
        # Isolate this helper occurrence without pretending the synthetic
        # component fixture is a complete source program/native artifact.
        return SimpleNamespace(objects={}, sites={}, texture_assets={}, joints={"hold": self.joint})

    def check(self, values=None, model=None):
        document, binary, inventory = fixture() if values is None else values
        return native.geometry(self.model() if model is None else model,
                               document, binary, inventory, native.OfflineWork())

    def test_independent_fixture_matches_frozen_source_streams(self):
        positions, normals, indices = independent_sphere_streams()
        self.assertEqual((len(positions) // 3, len(normals) // 3, len(indices) // 3), (62, 62, 120))
        for name, fmt, values in (("position", "f", positions), ("normal", "f", normals), ("indices", "H", indices)):
            with self.subTest(stream=name):
                packed = struct.pack("<" + fmt * len(values), *values)
                self.assertEqual(hashlib.sha256(packed).hexdigest(), STREAM_HASHES[name])

    def test_documented_parent_site_marker_passes_complete_geometry_comparison(self):
        source, report = self.check()
        self.assertEqual(set(source), {KEY})
        self.assertEqual(source[KEY]["frame"], "carrier.tip.frame")
        self.assertEqual(source[KEY]["element_id"], ["torque-cases", "demo", "hold"])
        self.assertEqual(source[KEY]["source_vertices"], 62)
        self.assertEqual(len(source[KEY]["corners"]), 8)
        self.assertEqual(source[KEY]["sites"], [])
        self.assertEqual((report["primitive_count"], report["source_bound_joint_parent_site_markers"]), (1, 1))
        self.assertEqual(report["status"], "passed")

    def test_unsupported_and_malformed_helper_kinds_refuse(self):
        for kind in ("joint", "joint_parent_sites", "joint_parent_site ", "unknown", "", None, 17, []):
            with self.subTest(kind=kind):
                values = fixture()
                values[0]["nodes"][0]["extras"]["ontokin"]["helper_kind"] = kind
                with self.assertRaisesRegex(AssertionError, "Unknown requested helper"):
                    self.check(values)

    def test_source_identity_frame_and_release_meaning_refuse_mutations(self):
        mutations = {
            "frame_path": "ball.origin.frame",
            "related_element_id": ["torque-cases", "demo", "other"],
            "physical_participation": "dynamic_body",
            "meaning": "This marker indicates an active grip.",
        }
        for field, bad in mutations.items():
            with self.subTest(field=field):
                values = fixture()
                values[0]["nodes"][0]["extras"]["ontokin"][field] = bad
                with self.assertRaisesRegex(AssertionError, "Parent-site helper source identity/frame/meaning"):
                    self.check(values)
        values = fixture()
        values[0]["nodes"][0]["name"] = "[visual helper] ball child site"
        with self.assertRaisesRegex(AssertionError, "Parent-site helper source name"):
            self.check(values)

    def test_unknown_joint_missing_metadata_and_duplicate_occurrence_refuse(self):
        for variant in ("unknown_joint", "missing_meaning", "extra_authority", "duplicate"):
            with self.subTest(variant=variant):
                values = fixture()
                node = values[0]["nodes"][0]
                metadata = node["extras"]["ontokin"]
                if variant == "unknown_joint":
                    metadata["joint_path"] = "missing"
                elif variant == "missing_meaning":
                    del metadata["meaning"]
                elif variant == "extra_authority":
                    metadata["active_constraint"] = True
                else:
                    values[0]["nodes"].append(copy.deepcopy(node))
                with self.assertRaises(AssertionError):
                    self.check(values)

    def test_source_geometry_refuses_wrong_radius_normal_topology_and_axis_geometry(self):
        for mutation in ("radius", "normal", "winding", "axis_geometry"):
            with self.subTest(mutation=mutation):
                positions, normals, indices = independent_sphere_streams()
                if mutation == "radius":
                    positions = [2 * value for value in positions]
                elif mutation == "normal":
                    normals[1] = -normals[1]
                elif mutation == "winding":
                    indices[1], indices[2] = indices[2], indices[1]
                else:
                    positions.extend((0., .09, 0., .006, .09, 0., 0., -.09, 0.))
                    normals.extend((1., 0., 0.) * 3)
                    indices.extend((62, 63, 64))
                # The synthetic decoded native values agree with the bad
                # artifact. Refusal must therefore come from the source oracle.
                values = fixture(positions=positions, normals=normals, indices=indices)
                with self.assertRaisesRegex(AssertionError, "Canonical source/native"):
                    self.check(values)

    def test_source_gold_pbr_refuses_agreeing_native_material_mutations(self):
        for field, bad in (("baseColorFactor", [0., .65, .08, 1.]), ("metallicFactor", .5),
                           ("roughnessFactor", .2), ("baseColorTexture", {"index": 0})):
            with self.subTest(field=field):
                material = copy.deepcopy(MATERIAL)
                material[field] = bad
                with self.assertRaisesRegex(AssertionError, "Independent source parent-site helper PBR values"):
                    self.check(fixture(material=material))

    def test_actual_native_stream_and_material_divergence_refuses(self):
        for mutation in ("position", "normal", "normalization", "index", "material"):
            with self.subTest(mutation=mutation):
                values = fixture()
                loaded = values[2]["meshes"][0]
                if mutation in ("position", "normal"):
                    loaded["attributes"][mutation]["values"][0] += .01
                elif mutation == "normalization":
                    loaded["attributes"]["normal"]["normalized"] = True
                elif mutation == "index":
                    loaded["indices"][1], loaded["indices"][2] = loaded["indices"][2], loaded["indices"][1]
                else:
                    loaded["materials"][0]["color"][0] = 0.
                with self.assertRaises(AssertionError):
                    self.check(values)

    def test_marker_requires_triangle_position_and_normal_attributes(self):
        for mutation in ("missing_normal", "unexpected_uv", "line_mode"):
            with self.subTest(mutation=mutation):
                values = fixture()
                primitive = values[0]["meshes"][0]["primitives"][0]
                if mutation == "missing_normal":
                    del primitive["attributes"]["NORMAL"]
                elif mutation == "unexpected_uv":
                    primitive["attributes"]["TEXCOORD_0"] = 0
                else:
                    primitive["mode"] = 1
                with self.assertRaisesRegex(AssertionError, "Parent-site helper triangle attributes"):
                    self.check(values)

    def test_grip_source_cannot_give_marker_an_axis(self):
        model = self.model()
        model.joints = {"hold": SimpleNamespace(kind="grip", axis=(0., 0., 1.), parent=self.joint.parent,
                                               element_id=self.joint.element_id)}
        with self.assertRaisesRegex(AssertionError, "Grip parent-site marker has no axis bar"):
            self.check(model=model)

    def test_independent_parent_frame_stops_after_release_and_child_transform_refuses(self):
        from ontokin.reach_reference import build_reference
        work = native.OfflineWork()
        reference = build_reference(self.source_model, end=Fraction(3), check=work.tick, mode="recording")
        source, _ = self.check()
        marker = source[KEY]
        arithmetic = native.Directed(work)
        tolerance = self.case["options"]["position_tolerance_m"]
        self.assertEqual(tolerance, .001)
        for text in ("0", "1/2", "1", "3/2", "2", "3"):
            time = Fraction(text)
            expected_x = min(time, Fraction(1))
            for side in ("before", "after"):
                with self.subTest(time=text, side=side):
                    pose = reference.recording_pose_enclosures([marker["frame"]], time, side)[marker["frame"]]
                    for cell, expected in zip(pose.position, (expected_x, Fraction(0), Fraction(0))):
                        self.assertLessEqual(cell.lo, expected)
                        self.assertGreaterEqual(cell.hi, expected)
                    for cell, expected in zip(pose.orientation, (Fraction(1), Fraction(0), Fraction(0), Fraction(0))):
                        self.assertLessEqual(cell.lo, expected)
                        self.assertGreaterEqual(cell.hi, expected)
                    matrix = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., float(expected_x), 0., 0., 1.]
                    ideal = arithmetic.matrix(pose.orientation)
                    position = tuple(map(arithmetic.cell, pose.position))
                    bound = max(arithmetic.discrepancy(matrix, ideal, corner, position, marker["local_quantization"])
                                for corner in marker["corners"])
                    self.assertLessEqual(bound, tolerance)
                    if time > 1:
                        matrix[12] = float(time)  # Released ball keeps the incoming x velocity.
                        wrong = arithmetic.discrepancy(matrix, ideal, (0., 0., 0.), position)
                        self.assertGreater(wrong, tolerance)


if __name__ == "__main__":
    unittest.main()
