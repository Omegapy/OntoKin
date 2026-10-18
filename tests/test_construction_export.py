"""Versioned construction delivery, independently read from GLB bytes."""

import copy
import hashlib
import json
import unittest

from ontokin.bundle import load_bundle
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, validate_export
from ontokin.scene import ExportOptions, rotation_error
from ontokin.syntax import parse
from ontokin.validator import validate
from tests.test_construction import RACK, RELEASE_SOURCE, bundle
from tests.test_export import DecodedGLB, encode_glb, simple_source


CONTRACT = "ontokin.glb/0.2"


class ConstructionExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sealed = load_bundle(json.loads((RACK / "program.bundle.json").read_text()))
        cls.compiler = compile_construction(cls.sealed, level="evaluated")
        cls.result = export_glb(cls.compiler.model, target_contract=CONTRACT,
                               source_uri="program.files.json", source_sha256=cls.sealed.entry.revision)
        cls.decoded = DecodedGLB(cls.result.data)

    def test_explicit_target_profile_and_complete_exact_source_map(self):
        report, document = self.result.report, self.decoded.document
        self.assertEqual(report["schema_version"], "ontokin.glb-report/0.2")
        self.assertEqual(report["target_contract"], CONTRACT)
        self.assertEqual(report["program_revision"], self.sealed.program_revision)
        self.assertEqual(report["scene"]["profile"], "construction-0.1")
        self.assertEqual(report["artifact"]["sha256"], "sha256:" + hashlib.sha256(self.result.data).hexdigest())
        metadata = document["extras"]["ontokin"]
        self.assertEqual(metadata["target_contract"], CONTRACT)
        self.assertEqual(metadata["program"], report["program"])
        self.assertEqual(metadata["program"]["manifest"], self.sealed.manifest())
        self.assertEqual(metadata["source"]["entry_revision"], self.sealed.entry.revision)
        self.assertNotEqual(metadata["source"]["entry_revision"], metadata["program"]["revision"])
        self.assertEqual(document["animations"][0]["extras"]["ontokin"]["target_contract"], CONTRACT)
        nodes = document["nodes"]
        self.assertEqual(document["scenes"][0]["nodes"], list(range(len(nodes))))
        self.assertTrue(all("children" not in node for node in nodes))
        for path, obj in self.compiler.model.objects.items():
            _, node = self.decoded.source_node(path)
            record = node["extras"]["ontokin"]
            self.assertEqual(record["element_id"], list(obj.element_id))
            self.assertEqual(record["source_mapping"], self.compiler.model.occurrence_provenance[path])
            self.assertEqual(record["program_revision"], self.sealed.program_revision)

    def test_independent_decode_matches_all126_frozen_poses_and_geometry(self):
        expected = json.loads((RACK / "expected.json").read_text())
        comparisons = 0
        for sample in expected["samples"]:
            t = float(sample["seconds"])
            for obj in sample["objects"]:
                actual = self.decoded.node_pose(obj["path"], t)
                self.assertLessEqual(max(abs(a - b) for a, b in zip(actual["translation"], obj["position_m"])), .001)
                w, x, y, z = obj["rotation_wxyz"]
                self.assertLessEqual(rotation_error(actual["rotation"], (x, y, z, w)), .001)
                comparisons += 1
        self.assertEqual(comparisons, 126)
        for obj in expected["objects"]:
            _, node = self.decoded.source_node(obj["path"])
            primitive = self.decoded.document["meshes"][node["mesh"]]["primitives"][0]
            positions = self.decoded.accessor(primitive["attributes"]["POSITION"])
            dimensions = [max(point[i] for point in positions) - min(point[i] for point in positions) for i in range(3)]
            geometry = obj["geometry"]
            wanted = geometry["size_m"] if geometry["kind"] == "box" else [2 * geometry["radius_m"]] * 3
            for actual, expected_dimension in zip(dimensions, wanted):
                self.assertAlmostEqual(actual, expected_dimension, delta=.001)

    def test_version_mismatch_and_ambiguous_source_hash_fail_closed(self):
        with self.assertRaises(OntoKinError):
            export_glb(self.compiler.model)
        core = validate(parse(simple_source()), level="evaluated")
        with self.assertRaises(OntoKinError):
            export_glb(core, target_contract=CONTRACT)
        with self.assertRaises(OntoKinError):
            export_glb(self.compiler.model, target_contract=CONTRACT,
                       source_sha256=self.sealed.program_revision)
        with self.assertRaises(OntoKinError):
            validate_export(self.result.data, self.compiler.model)

    def test_real_serialized_provenance_tampering_is_rejected(self):
        def bad_program(doc):
            doc["extras"]["ontokin"]["program"]["revision"] = "sha256:" + "0" * 64
        def bad_source(doc):
            doc["extras"]["ontokin"]["program"]["sources"]["entry"]["source_revision"] = "sha256:" + "0" * 64
        def bad_generated_key(doc):
            _, node = self.decoded.source_node('first.fingers["middle"]')
            index = self.decoded.document["nodes"].index(node)
            doc["nodes"][index]["extras"]["ontokin"]["source_mapping"]["generated"]["key"] = "upper"
        def bad_clip_contract(doc):
            doc["animations"][0]["extras"]["ontokin"]["target_contract"] = "ontokin.glb/0.1"
        for mutation in (bad_program, bad_source, bad_generated_key, bad_clip_contract):
            with self.subTest(mutation=mutation.__name__):
                document = copy.deepcopy(self.decoded.document)
                mutation(document)
                data = encode_glb(document, self.decoded.binary)
                with self.assertRaises(OntoKinError) as caught:
                    validate_export(data, self.compiler.model, target_contract=CONTRACT)
                self.assertEqual(caught.exception.diagnostic.details["target_contract"], CONTRACT)

    def test_dependency_revision_cannot_relabel_existing_artifact(self):
        payload = self.sealed.to_payload()
        payload["modules"][0]["source"] += "\n// A source revision changes even without changed numerical motion.\n"
        digest = "sha256:" + hashlib.sha256(payload["modules"][0]["source"].encode()).hexdigest()
        payload["entry"]["source"] = payload["entry"]["source"].replace(self.sealed.modules[0].revision, digest)
        changed = compile_construction(load_bundle(payload))
        self.assertEqual(set(changed.model.objects), set(self.compiler.model.objects))
        self.assertNotEqual(changed.model.program_revision, self.compiler.model.program_revision)
        with self.assertRaises(OntoKinError):
            validate_export(self.result.data, changed.model, target_contract=CONTRACT)

    def test_generated_release_is_world_baked_and_other_entry_remains_carried(self):
        compiler = compile_construction(bundle(RELEASE_SOURCE), level="evaluated")
        result = export_glb(compiler.model, target_contract=CONTRACT, options=ExportOptions(helpers=False))
        decoded = DecodedGLB(result.data)
        self.assertEqual(len(decoded.document["nodes"]), 3)
        for t in (.5, 1, 1.25, 1.5, 2):
            tau = max(0, t - 1)
            first = decoded.node_pose('rig.balls["one"]', t)["translation"]
            second = decoded.node_pose('rig.balls["two"]', t)["translation"]
            for actual, expected in zip(first, (t + .5, 2 - 5 * tau * tau, 0)):
                self.assertAlmostEqual(actual, expected, delta=.001)
            for actual, expected in zip(second, (t + .5, 2, 0)):
                self.assertAlmostEqual(actual, expected, delta=.001)


if __name__ == "__main__":
    unittest.main()
