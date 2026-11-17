#!/usr/bin/env python3
"""Finite reader controls; C255 is an independent consumer, never a producer input."""
from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reader = load("c256_reader_under_test", HERE / "reader.py")
oracle = load("c255_independent_consumer", HERE.parent / "localized-repair-c255/oracle.py")
PROOF = REPO / reader.PROOF


def unpack(raw):
    size = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20+size])
    binary_size = struct.unpack_from("<I", raw, 20+size)[0]
    return document, bytearray(raw[28+size:28+size+binary_size])


def pack(document, binary):
    payload = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode()
    payload += b" " * (-len(payload) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 28+len(payload)+len(binary))
            + struct.pack("<II", len(payload), 0x4E4F534A) + payload
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


def byte_offset(document, accessor, index=0):
    a = document["accessors"][accessor]
    view = document["bufferViews"][a["bufferView"]]
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
    size = {5126: 4, 5123: 2, 5125: 4}[a["componentType"]] * width
    return view.get("byteOffset", 0) + a.get("byteOffset", 0) + index * view.get("byteStride", size)


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (PROOF / "before.glb").read_bytes()
        cls.doc, cls.bin = unpack(cls.raw)
        cls.sources = {"main.ok": (PROOF / "before.main.ok").read_bytes(),
                       "hinges.ok": (PROOF / "hinges.ok").read_bytes()}
        cls.corpus = oracle.load_corpus(REPO)

    def mutation(self, change):
        d, b = copy.deepcopy(self.doc), self.bin.copy()
        change(d, b)
        return pack(d, b)

    def reject(self, raw, code=None):
        with self.assertRaises(reader.Fault) as caught:
            reader.measure_glb(raw)
        if code:
            self.assertEqual(caught.exception.code, code)

    def check_frozen(self, observation, raw, endpoint):
        expected = oracle.expected_state(self.corpus, "V1", "start" if endpoint == "before" else "final")
        artifacts = {observation["artifact"]["name"]: raw}
        oracle.geometry_check(observation["geometry"], expected["semantic"], artifacts, observation["programRevision"])
        oracle.pose_check(observation["poses"], expected["poses"], "delivery", artifacts, observation["programRevision"])

    def test_both_endpoints_pass_unchanged_c255_subset_predicates(self):
        for endpoint in ("before", "after"):
            with self.subTest(endpoint=endpoint):
                result = reader.read_bound_endpoint(REPO, endpoint)
                self.assertTrue(result["historicalArtifactBound"])
                self.assertTrue(result["sourceAssociationVerified"])
                self.assertEqual(len(result["geometry"]), 18)
                self.assertEqual(len(result["poses"]), 126)
                self.assertEqual(len({tuple(x["id"]) for x in result["identityJoins"]}), 18)
                self.assertEqual(len({tuple(x["definitionId"]) for x in result["identityJoins"]}), 3)
                self.check_frozen(result, (PROOF / (endpoint+".glb")).read_bytes(), endpoint)

    def test_no_complete_semantic_or_trial_result_is_created(self):
        result = reader.measure_glb(self.raw)
        self.assertFalse(result["historicalArtifactBound"])
        self.assertFalse(result["sourceAssociationVerified"])
        self.assertFalse(result["semanticQualified"])
        self.assertFalse(result["completeC255Observation"])
        self.assertFalse(result["executionAllowed"])
        self.assertIsNone(result["realTrialSuccess"])
        self.assertNotIn("semantic", result)
        self.assertNotIn("decision", result)
        self.assertNotIn("rebuild", result)

    def test_source_association_does_not_claim_historical_artifact(self):
        result = reader.associate_glb(self.raw, self.sources)
        self.assertTrue(result["sourceAssociationVerified"])
        self.assertFalse(result["historicalArtifactBound"])

    def test_geometry_corruption_changes_measurement_and_fails_math(self):
        def alter(d, b):
            accessor = d["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
            offset = byte_offset(d, accessor)
            value = struct.unpack_from("<f", b, offset)[0]
            struct.pack_into("<f", b, offset, value+0.1)
        raw = self.mutation(alter)
        observed = reader.associate_glb(raw, self.sources)
        self.assertNotEqual(observed["geometry"][0]["vertices_m"], reader.measure_glb(self.raw)["geometry"][0]["vertices_m"])
        with self.assertRaises(oracle.Fault):
            self.check_frozen(observed, raw, "before")

    def test_translation_corruption_changes_measured_pose(self):
        def alter(d, b):
            out = d["animations"][0]["samplers"][0]["output"]
            offset = byte_offset(d, out, 15)
            struct.pack_into("<f", b, offset, 4.0)
        raw = self.mutation(alter)
        result = reader.associate_glb(raw, self.sources)
        pose = next(x for x in result["poses"] if x["id"] == ["keyed-rack", "demo", "first"] and x["time_s"] == 0.25)
        self.assertEqual(pose["position_m"][0], 4.0)
        self.assertEqual(pose["matrix"][3], 4.0)
        with self.assertRaises(oracle.Fault):
            self.check_frozen(result, raw, "before")

    def test_rotation_corruption_changes_measured_orientation(self):
        def alter(d, b):
            out = d["animations"][0]["samplers"][1]["output"]
            struct.pack_into("<ffff", b, byte_offset(d, out, 15), 0, 0, math.sin(0.1), math.cos(0.1))
        raw = self.mutation(alter)
        result = reader.associate_glb(raw, self.sources)
        pose = next(x for x in result["poses"] if x["id"] == ["keyed-rack", "demo", "first"] and x["time_s"] == 0.25)
        self.assertAlmostEqual(pose["rotation_wxyz"][3], math.sin(0.1), places=7)
        with self.assertRaises(oracle.Fault):
            self.check_frozen(result, raw, "before")

    def test_valid_time_change_changes_interpolation_without_expected_answers(self):
        raw = self.mutation(lambda d, b: struct.pack_into("<f", b, byte_offset(d, 0, 15), 0.255))
        original, modified = reader.measure_glb(self.raw), reader.measure_glb(raw)
        before = next(x for x in original["poses"] if x["id"] == ["keyed-rack", "demo", "first"] and x["time_s"] == 0.25)
        after = next(x for x in modified["poses"] if x["id"] == before["id"] and x["time_s"] == 0.25)
        self.assertNotEqual(before["position_m"], after["position_m"])
        origin = next(x for x in modified["measurementOrigins"]["poses"] if x["id"] == before["id"] and x["time_s"] == 0.25)
        self.assertEqual(origin["translation"]["sampleIndices"], [14, 15])
        self.assertGreater(origin["translation"]["alpha"], 0)
        self.assertLess(origin["translation"]["alpha"], 1)

    def test_nonincreasing_and_uncovered_time_tracks_refuse(self):
        for sample, value in ((15, 0.0), (120, 1.99), (0, 0.001)):
            with self.subTest(sample=sample):
                self.reject(self.mutation(lambda d, b: struct.pack_into("<f", b, byte_offset(d, 0, sample), value)))

    def test_node_defaults_are_replaced_by_animation(self):
        raw = self.mutation(lambda d, b: d["nodes"][0].update(translation=[100, 200, 300]))
        observed = reader.measure_glb(raw)
        self.assertEqual(observed["poses"][0]["position_m"], [-1, 0, 0])

    def test_metadata_dimensions_do_not_supply_meshes(self):
        raw = self.mutation(lambda d, b: d["nodes"][0]["extras"]["ontokin"]["geometry"].update(size=[999, 999, 999]))
        result = reader.measure_glb(raw)
        self.assertEqual(result["geometry"][0]["vertices_m"], reader.measure_glb(self.raw)["geometry"][0]["vertices_m"])

    def test_invalid_quaternions_are_refused_before_normalization(self):
        for q in ([0, 0, 0, 0], [0, 0, 0, 1.01], [0, 0, 0, float("nan")]):
            with self.subTest(q=q):
                self.reject(self.mutation(lambda d, b: struct.pack_into("<ffff", b,
                    byte_offset(d, d["animations"][0]["samplers"][1]["output"], 15), *q)))

    def test_sign_equivalent_quaternion_remains_same_rotation(self):
        def alter(d, b):
            out = d["animations"][0]["samplers"][1]["output"]
            struct.pack_into("<ffff", b, byte_offset(d, out, 15), 0, 0, 0, -1)
        raw = self.mutation(alter)
        self.check_frozen(reader.measure_glb(raw), raw, "before")

    def test_changed_full_id_and_definition_associations_refuse(self):
        def alter_id(d, b):
            m = d["nodes"][0]["extras"]["ontokin"]
            m["element_id"] = ["wrong", "demo", "first"]
            m["source_mapping"]["element_id"] = m["element_id"]
            d["extras"]["ontokin"]["program"]["occurrences"]["first"]["element_id"] = m["element_id"]
        def alter_definition(d, b):
            m = d["nodes"][0]["extras"]["ontokin"]
            m["source_mapping"]["definition_id"] = ["wrong"]
            d["extras"]["ontokin"]["program"]["occurrences"]["first"]["definition_id"] = ["wrong"]
        for change in (alter_id, alter_definition):
            with self.subTest(change=change.__name__):
                raw = self.mutation(change)
                self.assertFalse(reader.measure_glb(raw)["sourceAssociationVerified"])
                with self.assertRaises(reader.Fault):
                    reader.associate_glb(raw, self.sources)

    def test_source_spans_and_program_hash_are_checked(self):
        def span(d, b):
            for m in [d["nodes"][0]["extras"]["ontokin"]["source_mapping"],
                      d["extras"]["ontokin"]["program"]["occurrences"]["first"]]:
                m["declaration"]["start_byte"] += 1
        def revision(d, b):
            program = "sha256:"+"0"*64
            d["extras"]["ontokin"]["program"]["revision"] = program
            for node in d["nodes"]:
                node["extras"]["ontokin"]["program_revision"] = program
        for change in (span, revision):
            with self.subTest(change=change.__name__), self.assertRaises(reader.Fault):
                reader.associate_glb(self.mutation(change), self.sources)

    def test_duplicate_identity_refuses(self):
        def alter(d, b):
            original = d["nodes"][0]["extras"]["ontokin"]["element_id"]
            d["nodes"][1]["extras"]["ontokin"]["element_id"] = original
        self.reject(self.mutation(alter), "DUPLICATE_IDENTITY")

    def test_source_closure_changes_refuse(self):
        for change in ({"main.ok": self.sources["main.ok"]+b"\n", "hinges.ok": self.sources["hinges.ok"]},
                       {"main.ok": self.sources["main.ok"]}, {**self.sources, "extra.ok": b"x"}):
            with self.subTest(keys=list(change)), self.assertRaises(reader.Fault):
                reader.associate_glb(self.raw, change)

    def test_raw_origins_resolve_actual_binary_elements(self):
        result = reader.read_bound_endpoint(REPO, "before")
        for mesh, origin in zip(result["geometry"], result["measurementOrigins"]["geometry"]):
            p = origin["position"]
            first = list(struct.unpack_from("<fff", self.raw, p["glbByteOffset"]))
            self.assertEqual(mesh["vertices_m"][0], first)
            i = origin["indices"]
            fmt = "<H" if i["componentType"] == 5123 else "<I"
            self.assertEqual(mesh["triangles"][0][0], struct.unpack_from(fmt, self.raw, i["glbByteOffset"])[0])
        for origin in result["measurementOrigins"]["poses"]:
            for key in ("translation", "rotation"):
                track = origin[key]
                for n, index in enumerate(track["sampleIndices"]):
                    info = track["input"]
                    self.assertEqual(track["storedTimes_s"][n], struct.unpack_from("<f", self.raw,
                        info["glbByteOffset"]+index*info["byteStride"])[0])

    def test_historical_entry_refuses_mutation_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = root / reader.PROOF
            proof.mkdir(parents=True)
            for name in ("before.glb", "before.main.ok", "hinges.ok"):
                shutil.copyfile(PROOF/name, proof/name)
            self.assertTrue(reader.read_bound_endpoint(root, "before")["historicalArtifactBound"])
            (proof/"before.glb").write_bytes(self.raw[:-1]+bytes([self.raw[-1]^1]))
            with self.assertRaises(reader.Fault) as caught:
                reader.read_bound_endpoint(root, "before")
            self.assertEqual(caught.exception.code, "HISTORICAL_BINDING")
            (proof/"before.glb").unlink()
            (proof/"before.glb").symlink_to(PROOF/"before.glb")
            with self.assertRaises(reader.Fault):
                reader.read_bound_endpoint(root, "before")

    def test_headers_and_truncations_refuse(self):
        for raw in (b"", self.raw[:12], self.raw[:-1], b"BAD!"+self.raw[4:],
                    self.raw[:8]+struct.pack("<I", len(self.raw)+4)+self.raw[12:]):
            with self.subTest(length=len(raw)):
                self.reject(raw)

    def test_extra_and_misaligned_chunks_refuse(self):
        raw = bytearray(self.raw)
        struct.pack_into("<I", raw, 12, struct.unpack_from("<I", raw, 12)[0]-1)
        self.reject(bytes(raw), "GLB_CHUNK")
        raw = bytearray(self.raw+struct.pack("<II", 0, 42))
        struct.pack_into("<I", raw, 8, len(raw))
        self.reject(bytes(raw), "GLB_CHUNKS")

    def test_accessor_ranges_alignment_types_and_indices_refuse(self):
        changes = [lambda d, b: d["accessors"][1].update(byteOffset=2),
                   lambda d, b: d["accessors"][1].update(count=9999999),
                   lambda d, b: d["accessors"][1].update(componentType=True),
                   lambda d, b: d["accessors"][1].update(sparse={}),
                   lambda d, b: d["accessors"][1].update(normalized=True),
                   lambda d, b: d["bufferViews"][1].update(byteLength=8),
                   lambda d, b: struct.pack_into("<H", b, byte_offset(d, 3), 65535)]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.reject(self.mutation(change))

    def test_external_buffers_and_unsupported_transforms_refuse(self):
        changes = [lambda d, b: d["buffers"][0].update(uri="external.bin"),
                   lambda d, b: d["nodes"][0].update(children=[1]),
                   lambda d, b: d["nodes"][0].update(scale=[1, 1.001, 1]),
                   lambda d, b: d["nodes"][0].update(matrix=[1]*16),
                   lambda d, b: d.update(extensionsRequired=["EXT_unknown"]),
                   lambda d, b: d["animations"][0]["samplers"][0].update(interpolation="CUBICSPLINE")]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.reject(self.mutation(change))

    def test_scene_and_channel_ambiguities_refuse(self):
        changes = [lambda d, b: d["scenes"][0]["nodes"].pop(),
                   lambda d, b: d["scenes"][0]["nodes"].__setitem__(1, 0),
                   lambda d, b: d["animations"][0]["channels"].pop(),
                   lambda d, b: d["animations"][0]["channels"][1].update(target={"node": 0, "path": "translation"}),
                   lambda d, b: d["animations"][0]["channels"][0].update(target={"node": True, "path": "translation"})]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.reject(self.mutation(change))

    def test_nonfinite_binary_position_refuses(self):
        self.reject(self.mutation(lambda d, b: struct.pack_into("<f", b, byte_offset(d, 1), float("inf"))), "NONFINITE")

    def test_duplicate_json_keys_refuse(self):
        payload = json.dumps(self.doc, separators=(",", ":")).encode()
        payload = b'{"scene":0,' + payload[1:]
        payload += b" " * (-len(payload)%4)
        raw = (struct.pack("<III", 0x46546C67, 2, 28+len(payload)+len(self.bin))
               +struct.pack("<II", len(payload), 0x4E4F534A)+payload
               +struct.pack("<II", len(self.bin), 0x004E4942)+self.bin)
        self.reject(raw, "JSON_DUPLICATE")

    def test_malformed_objects_report_refusal_instead_of_attribute_error(self):
        changes = [lambda d, b: d.update(asset=[]),
                   lambda d, b: d["extras"].update(ontokin=[]),
                   lambda d, b: d["nodes"][0]["extras"].update(ontokin=[])]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                self.reject(self.mutation(change), "STRUCTURE")
        raw = self.mutation(lambda d, b: d["extras"]["ontokin"]["program"].update(manifest=[]))
        with self.assertRaises(reader.Fault) as caught:
            reader.associate_glb(raw, self.sources)
        self.assertEqual(caught.exception.code, "STRUCTURE")

    def test_oversized_integer_json_reports_explicit_refusal(self):
        payload = json.dumps(self.doc, separators=(",", ":")).encode()
        payload = b'{"enormous":'+b"9"*5000+b","+payload[1:]
        payload += b" " * (-len(payload)%4)
        raw = (struct.pack("<III", 0x46546C67, 2, 28+len(payload)+len(self.bin))
               +struct.pack("<II", len(payload), 0x4E4F534A)+payload
               +struct.pack("<II", len(self.bin), 0x004E4942)+self.bin)
        self.reject(raw, "STRUCTURE")

    def test_bounded_inputs_reject_size_before_hashing(self):
        with self.assertRaises(reader.Fault) as caught:
            reader.associate_glb(self.raw, {**self.sources, "main.ok": b"x"*4097})
        self.assertEqual(caught.exception.code, "SOURCE_SIZE")
        with tempfile.TemporaryDirectory() as directory:
            proof = Path(directory) / reader.PROOF
            proof.mkdir(parents=True)
            (proof / "before.glb").write_bytes(self.raw+b"x")
            with self.assertRaises(reader.Fault) as caught:
                reader.read_bound_endpoint(directory, "before")
            self.assertEqual(caught.exception.code, "HISTORICAL_SIZE")
        self.reject(b"x"*(reader.MAX_BYTES+1), "GLB_SIZE")

    def test_accessor_alias_amplification_has_cumulative_limit(self):
        d, b = copy.deepcopy(self.doc), self.bin.copy()
        times = b"".join(struct.pack("<f", 2*i/4095) for i in range(4096))
        translation = struct.pack("<fff", 0, 0, 0)*4096
        rotation = struct.pack("<ffff", 0, 0, 0, 1)*4096
        new_views = []
        for raw in (times, translation, rotation):
            new_views.append(len(d["bufferViews"]))
            d["bufferViews"].append({"buffer": 0, "byteOffset": len(b), "byteLength": len(raw)})
            b.extend(raw)
        d["accessors"][0] = {"bufferView": new_views[0], "componentType": 5126,
                               "count": 4096, "type": "SCALAR"}
        for index, sampler in enumerate(d["animations"][0]["samplers"]):
            sampler["input"] = 0
            sampler["output"] = len(d["accessors"])
            d["accessors"].append({"bufferView": new_views[1 if index%2 == 0 else 2],
                "componentType": 5126, "count": 4096, "type": "VEC3" if index%2 == 0 else "VEC4"})
        d["buffers"][0]["byteLength"] = len(b)
        self.reject(pack(d, b), "DECODE_LIMIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
