"""Actual source-to-byte regressions for explicit texture delivery and refusal."""
import copy
import json
from pathlib import Path
import struct
import unittest

from ontokin.budget_runtime import execute_pockets_export, execute_texture_export
from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import validate_export
from ontokin.profile_capabilities import TEXTURE_PROFILE
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions, TEXTURE_TARGET
from ontokin.texture_bundle import TextureBundle, load_texture_file_manifest


ROOT = Path(__file__).resolve().parents[1] / "examples/textured-surfaces"
OPTIONS = ExportOptions(fps=2, end="1", helpers=False)


def decode(data):
    size, kind = struct.unpack_from("<II", data, 12)
    assert kind == 0x4e4f534a
    document = json.loads(data[20:20+size])
    length, kind = struct.unpack_from("<II", data, 20+size)
    assert kind == 0x004e4942
    return document, data[28+size:28+size+length]


def encode(document, binary):
    raw = json.dumps(document, separators=(",", ":"), allow_nan=False).encode()
    raw += b" " * (-len(raw) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return (struct.pack("<III", 0x46546c67, 2, 28+len(raw)+len(binary))
            + struct.pack("<II", len(raw), 0x4e4f534a) + raw
            + struct.pack("<II", len(binary), 0x004e4942) + binary)


class TextureDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = load_texture_file_manifest(ROOT / "rgb-panel.files.json")
        cls.result = execute_texture_export(cls.program, options=OPTIONS)
        if cls.result.data is None:
            raise AssertionError(cls.result.report)
        cls.document, cls.binary = decode(cls.result.data)

    def validate(self, data, program=None):
        program = self.program if program is None else program
        ledger = SharedExecutionBudget()
        admit_entry_budget(program.entry, ledger, profile=TEXTURE_PROFILE)
        compiler = compile_construction(program, level="evaluated", execution_budget=ledger)
        return validate_export(data, compiler.model, options=OPTIONS,
            target_contract=TEXTURE_TARGET, work=ReachExecutionWork(execution_budget=ledger))

    def test_texture_bytes_follow_exact_unchanged_geometry_and_motion(self):
        old = execute_pockets_export(load_file_manifest(ROOT / "control-panel.files.json"), options=OPTIONS)
        self.assertIsNotNone(old.data, old.report)
        old_doc, old_bin = decode(old.data)
        length = old_doc["buffers"][0]["byteLength"]
        self.assertEqual(self.binary[:length], old_bin[:length])
        self.assertEqual(self.document["accessors"][:len(old_doc["accessors"])], old_doc["accessors"])
        self.assertEqual(self.document["bufferViews"][:len(old_doc["bufferViews"])], old_doc["bufferViews"])

    def test_embedded_image_is_the_exact_original_png_and_sampler_is_explicit(self):
        self.assertEqual(self.document["samplers"], [{"magFilter":9728,"minFilter":9728,"wrapS":33071,"wrapT":33071}])
        self.assertEqual(len(self.document["images"]), 1)
        view = self.document["bufferViews"][self.document["images"][0]["bufferView"]]
        self.assertEqual(self.binary[view["byteOffset"]:view["byteOffset"]+view["byteLength"]],
                         (ROOT / "assets/asymmetric-rgb.png").read_bytes())

    def test_hostile_texture_bytes_and_references_are_refused(self):
        for mutation in ("uv", "png", "sampler", "texture_reference", "factor", "missing_uv"):
            with self.subTest(mutation=mutation):
                doc, binary = copy.deepcopy(self.document), bytearray(self.binary)
                primitive = next(p for mesh in doc["meshes"] for p in mesh["primitives"] if "TEXCOORD_0" in p["attributes"])
                if mutation == "uv":
                    accessor = doc["accessors"][primitive["attributes"]["TEXCOORD_0"]]
                    view = doc["bufferViews"][accessor["bufferView"]]
                    binary[view["byteOffset"]] ^= 1
                elif mutation == "png":
                    view = doc["bufferViews"][doc["images"][0]["bufferView"]]
                    binary[view["byteOffset"]+16] ^= 1
                elif mutation == "sampler":
                    doc["samplers"][0]["wrapT"] = 10497
                elif mutation == "texture_reference":
                    doc["textures"][0]["source"] = True
                elif mutation == "factor":
                    doc["materials"][primitive["material"]]["pbrMetallicRoughness"]["baseColorFactor"][0] = .5
                else:
                    del primitive["attributes"]["TEXCOORD_0"]
                with self.assertRaises(OntoKinError) as caught:
                    self.validate(encode(doc, bytes(binary)))
                self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")

    def test_distinct_asset_ids_keep_separate_original_image_storage(self):
        program = load_texture_file_manifest(ROOT / "same-bytes-distinct-ids.files.json")
        result = execute_texture_export(program, options=OPTIONS)
        self.assertIsNotNone(result.data, result.report)
        document, binary = decode(result.data)
        self.assertEqual(len(document["images"]), 2)
        first, second = (image["bufferView"] for image in document["images"])
        self.assertNotEqual(first, second)
        document["bufferViews"][second]["byteOffset"] = document["bufferViews"][first]["byteOffset"]
        with self.assertRaises(OntoKinError) as caught:
            self.validate(encode(document, binary), program)
        self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")

    def test_unsupported_material_channels_and_extensions_cannot_change_rendering(self):
        for mutation in ("normal", "occlusion", "emissive", "double_sided", "unlit",
                         "metallic_roughness_map", "texture_transform"):
            with self.subTest(mutation=mutation):
                doc = copy.deepcopy(self.document)
                primitive = next(p for mesh in doc["meshes"] for p in mesh["primitives"]
                                 if "TEXCOORD_0" in p["attributes"])
                material = doc["materials"][primitive["material"]]
                if mutation == "normal":
                    material["normalTexture"] = {"index": 0, "texCoord": 0}
                elif mutation == "occlusion":
                    material["occlusionTexture"] = {"index": 0, "texCoord": 0}
                elif mutation == "emissive":
                    material["emissiveTexture"] = {"index": 0, "texCoord": 0}
                    material["emissiveFactor"] = [1, 1, 1]
                elif mutation == "double_sided":
                    material["doubleSided"] = True
                elif mutation == "unlit":
                    material["extensions"] = {"KHR_materials_unlit": {}}
                    doc["extensionsUsed"] = ["KHR_materials_unlit"]
                elif mutation == "metallic_roughness_map":
                    material["pbrMetallicRoughness"]["metallicRoughnessTexture"] = {"index": 0}
                else:
                    material["pbrMetallicRoughness"]["baseColorTexture"]["extensions"] = {
                        "KHR_texture_transform": {"offset": [.5, .25]}}
                    doc["extensionsUsed"] = ["KHR_texture_transform"]
                with self.assertRaises(OntoKinError) as caught:
                    self.validate(encode(doc, self.binary))
                self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")

    def test_untextured_regions_cannot_acquire_emission_or_changed_backfaces(self):
        for field, value in (("emissiveFactor", [1, 0, 0]), ("doubleSided", True)):
            with self.subTest(field=field):
                doc = copy.deepcopy(self.document)
                primitive = next(p for mesh in doc["meshes"] for p in mesh["primitives"]
                                 if "TEXCOORD_0" not in p["attributes"])
                doc["materials"][primitive["material"]][field] = value
                with self.assertRaises(OntoKinError) as caught:
                    self.validate(encode(doc, self.binary))
                self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")

    def test_morph_targets_and_mesh_or_node_weights_cannot_bypass_exact_base_geometry(self):
        for weight_owner in ("mesh", "node"):
            with self.subTest(weight_owner=weight_owner):
                doc = copy.deepcopy(self.document)
                node = next(node for node in doc["nodes"] if "mesh" in node)
                mesh = doc["meshes"][node["mesh"]]
                # Reuse valid existing accessor bytes as morph deltas.  This
                # leaves every base position/normal/index and UV byte exact,
                # while a conforming renderer would double those positions.
                for primitive in mesh["primitives"]:
                    primitive["targets"] = [{"POSITION": primitive["attributes"]["POSITION"]}]
                (mesh if weight_owner == "mesh" else node)["weights"] = [1]
                with self.assertRaises(OntoKinError) as caught:
                    self.validate(encode(doc, self.binary))
                self.assertEqual(caught.exception.diagnostic.details.get("export_code"), "OKE-E-TEXTURE")

    def test_older_destination_cannot_silently_drop_images(self):
        result = execute_pockets_export(self.program, options=OPTIONS)
        self.assertIsNone(result.data)

    def test_asset_bundle_cannot_be_accepted_under_an_earlier_source_profile(self):
        old = load_file_manifest(ROOT / "control-panel.files.json")
        wrong = TextureBundle(old.entry, old.modules, self.program.assets)
        result = execute_pockets_export(wrong, options=OPTIONS)
        self.assertIsNone(result.data)
        self.assertIn("OKL-E-ASSET-CLOSURE", [d["code"] for d in result.report["diagnostics"]])

    def test_failed_current_budget_returns_no_image_bearing_artifact(self):
        result = execute_texture_export(self.program, options=OPTIONS, caller_caps={"max_operations": 50})
        self.assertIsNone(result.data)
        self.assertNotEqual(result.report["outcome"], "valid")


if __name__ == "__main__":
    unittest.main()
