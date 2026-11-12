"""Independent corruptions and finite boundaries for semantic sidecars."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import unittest

from ontokin.bundle import load_bundle
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb
from ontokin.scene import ExportOptions
from ontokin.semantic_export import (SemanticExportError, build_semantic_manifest,
                                     canonical_bytes, verify_semantic_manifest)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/language-design/construction-v0.1/01-keyed-rack"


def decode(data):
    size = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20+size])
    offset = 20 + size
    binary_size = struct.unpack_from("<I", data, offset)[0]
    return document, data[offset+8:offset+8+binary_size]


def encode(document, binary):
    raw = json.dumps(document, separators=(",", ":")).encode()
    raw += b" " * (-len(raw) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 28+len(raw)+len(binary))
            + struct.pack("<I4s", len(raw), b"JSON") + raw
            + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


class SemanticExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads((FIXTURE / "program.bundle.json").read_text())
        cls.bundle = load_bundle(cls.payload)
        cls.model = compile_construction(cls.bundle, level="evaluated").model
        cls.artifact = export_glb(cls.model, target_contract="ontokin.glb/0.2", options=ExportOptions(helpers=False))
        cls.manifest = build_semantic_manifest(cls.bundle, cls.artifact.data,
                                               accepted_program_revision=cls.bundle.program_revision)

    def build(self, bundle=None, data=None, **kwargs):
        bundle = self.bundle if bundle is None else bundle
        return build_semantic_manifest(bundle, self.artifact.data if data is None else data,
                                       accepted_program_revision=bundle.program_revision, **kwargs)

    def verify(self, manifest, **kwargs):
        return verify_semantic_manifest(manifest, self.bundle, self.artifact.data,
                                        accepted_program_revision=self.bundle.program_revision, **kwargs)

    def test_complete_finite_inventory_bound_to_frozen_oracle(self):
        expected = json.loads((FIXTURE / "expected.json").read_text())
        self.assertEqual([len(self.manifest[key]) for key in ("objects", "sites", "joints", "follows", "actions")],
                         [18, 34, 8, 8, 2])
        actual = {item["path"]: item for item in self.manifest["objects"]}
        for row in expected["objects"]:
            record = actual[row["path"]]
            self.assertEqual(record["element_id"], row["element_id"])
            self.assertEqual(record["definition_id"], row["definition_id"])
            shape = record["geometry"]
            wanted = row["geometry"]
            self.assertEqual(shape["kind"], wanted["kind"])
            values = shape["size"] if shape["kind"] == "box" else [shape["radius"]]
            targets = wanted["size_m"] if wanted["kind"] == "box" else [wanted["radius_m"]]
            for value, target in zip(values, targets):
                self.assertAlmostEqual(value, target, delta=expected["comparison"]["geometry_dimension_tolerance_m"])
        self.assertEqual(self.manifest["binding"]["source_manifest"], self.bundle.manifest())
        self.assertEqual(self.manifest["binding"]["artifact"]["sha256"],
                         "sha256:" + hashlib.sha256(self.artifact.data).hexdigest())
        self.assertEqual(self.manifest["scene"]["delivered_interval_seconds"], ["0", "2"])

    def test_ownership_and_declared_connections_do_not_parent_glb_transforms(self):
        document, _ = decode(self.artifact.data)
        self.assertEqual(document["scenes"][0]["nodes"], list(range(18)))
        self.assertTrue(all("children" not in node for node in document["nodes"]))
        middle = next(x for x in self.manifest["objects"] if x["path"] == 'first.fingers["middle"]')
        self.assertEqual(middle["owner"]["path"], "first")
        self.assertEqual(middle["physical"], {"kind": "no_body"})
        self.assertFalse(middle["placement"]["authored"])
        self.assertEqual(self.manifest["follows"][0]["offset"]["frame"], "first.frame")
        self.assertFalse(self.manifest["validation"]["destination_execution"])

    def test_unknown_and_required_unimplemented_features_reject(self):
        for name in ("live_physics", "action_execution", "source_reconstruction", "unreal_import"):
            with self.subTest(feature=name), self.assertRaises(SemanticExportError) as caught:
                self.build(required_features=[name])
            self.assertEqual(caught.exception.code, "OKS-E-UNSUPPORTED")
            self.assertEqual(caught.exception.details["feature"], name)
        for values in ("stable_identities", ["stable_identities", "stable_identities"], [True]):
            with self.subTest(requirements=values), self.assertRaises(SemanticExportError):
                self.build(required_features=values)

    def test_stale_accepted_revision_rejects_before_artifact_use(self):
        with self.assertRaises(SemanticExportError) as caught:
            build_semantic_manifest(self.bundle, self.artifact.data, accepted_program_revision="sha256:" + "0"*64)
        self.assertEqual(caught.exception.code, "OKS-E-REVISION")

    def test_same_geometry_with_changed_source_revision_cannot_relabel_glb(self):
        payload = copy.deepcopy(self.payload)
        payload["entry"]["source"] += "\n// Changed revision, unchanged geometry.\n"
        with self.assertRaises(OntoKinError):
            self.build(load_bundle(payload))

    def test_changed_dependency_and_updated_pin_cannot_relabel_glb(self):
        payload = copy.deepcopy(self.payload)
        payload["modules"][0]["source"] += "\n// Exact dependency bytes changed.\n"
        new_hash = "sha256:" + hashlib.sha256(payload["modules"][0]["source"].encode()).hexdigest()
        payload["entry"]["source"] = payload["entry"]["source"].replace(self.bundle.modules[0].revision, new_hash)
        with self.assertRaises(OntoKinError):
            self.build(load_bundle(payload))

    def test_broken_sidecar_reference_and_changed_semantics_reject(self):
        for alteration in ("reference", "dimension", "site", "missing_object"):
            manifest = copy.deepcopy(self.manifest)
            if alteration == "reference":
                manifest["objects"][0]["geometry_binding"]["mesh"] = 123456
            elif alteration == "dimension":
                manifest["objects"][0]["geometry"]["size"][0] = 3
            elif alteration == "site":
                manifest["sites"][0]["pose"]["position_m"][0] = 3
            else:
                manifest["objects"].pop()
            with self.subTest(alteration=alteration), self.assertRaises(SemanticExportError) as caught:
                self.verify(manifest)
            self.assertEqual(caught.exception.code, "OKS-E-MISMATCH")

    def test_actual_broken_geometry_reference_and_binary_mutation_reject(self):
        document, binary = decode(self.artifact.data)
        corrupt = copy.deepcopy(document)
        corrupt["nodes"][0]["mesh"] = 123456
        with self.assertRaises(OntoKinError):
            self.build(data=encode(corrupt, binary))
        index = document["meshes"][document["nodes"][0]["mesh"]]["primitives"][0]["attributes"]["POSITION"]
        accessor = document["accessors"][index]
        view = document["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        corrupt_binary = bytearray(binary)
        value = struct.unpack_from("<f", corrupt_binary, offset)[0]
        struct.pack_into("<f", corrupt_binary, offset, value + .1)
        with self.assertRaises(OntoKinError):
            self.build(data=encode(document, bytes(corrupt_binary)))

    def test_real_prefix_export_cannot_silently_omit_source_interval(self):
        prefix = export_glb(self.model, target_contract="ontokin.glb/0.2", options=ExportOptions(helpers=False, end=".5"))
        with self.assertRaises(SemanticExportError) as caught:
            self.build(data=prefix.data)
        self.assertEqual(caught.exception.details["feature"], "partial_interval")
        self.assertEqual(caught.exception.details["delivered_end_seconds"], "0.5")

    def test_visual_helpers_are_explicitly_outside_selected_profile(self):
        artifact = export_glb(self.model, target_contract="ontokin.glb/0.2", options=ExportOptions(helpers=True))
        with self.assertRaises(SemanticExportError) as caught:
            self.build(data=artifact.data)
        self.assertEqual(caught.exception.details["feature"], "visual_helpers")

    def test_external_requirements_cannot_be_erased_from_manifest(self):
        with self.assertRaises(SemanticExportError) as caught:
            self.verify(self.manifest, required_features=["stable_identities"])
        self.assertEqual(caught.exception.code, "OKS-E-MISMATCH")
        with self.assertRaises(SemanticExportError) as caught:
            self.verify(self.manifest, required_features=["live_physics"])
        self.assertEqual(caught.exception.code, "OKS-E-UNSUPPORTED")

    def test_canonical_comparison_is_deterministic_and_rejects_unknown_fields(self):
        self.assertEqual(canonical_bytes(self.build()), canonical_bytes(self.manifest))
        reordered = dict(reversed(list(self.manifest.items())))
        self.assertEqual(canonical_bytes(reordered), canonical_bytes(self.manifest))
        reordered["invented_destination_success"] = True
        with self.assertRaises(SemanticExportError):
            self.verify(reordered)

    def test_callback_interrupt_propagates_without_mutating_inputs(self):
        class Interrupted(Exception):
            pass
        expected = Interrupted("stop")
        before = canonical_bytes(self.payload)
        def stop():
            raise expected
        with self.assertRaises(Interrupted) as caught:
            self.build(check=stop)
        self.assertIs(caught.exception, expected)
        self.assertEqual(before, canonical_bytes(self.payload))


if __name__ == "__main__":
    unittest.main()
