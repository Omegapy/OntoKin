"""Independent verifier rejection tests; these do not execute OntoKin source.

The tiny synthetic GLB below exercises byte addressing/mutation only. It is not
substituted for the actual supplied-artifact corpus required by acceptance.
"""
from __future__ import annotations

import base64
import copy
from pathlib import Path
import shutil
import struct
from types import SimpleNamespace

import tempfile
import unittest

from tools.keyed_transform_reference import (FREEZE_SHA256, GLB, PROFILE, TARGET,
    ReferenceError, canonical_probe_type, case_payload, check_all_locations, check_inspection, delivered_by_revision,
    check_transforms, digest, json_differences, load_fixtures, normalized_document,
    repack_glb, sha, source_units)
from tools.keyed_transform_adversaries import MUTATIONS, build_mutations
from tools.keyed_transform_destination_expectations import expectations
from tools.verify_keyed_transform_agent_evidence import terminal_refusals

ROOT = Path(__file__).resolve().parents[1]




def location(source, fragment):
    raw, sought = source.encode(), fragment.encode()
    start = raw.index(sought)
    return {"source_id": "entry", "source_revision": digest(raw), "filename": "main.ok",
            "start_byte": start, "end_byte": start + len(sought)}


def singleton_inspections(fixtures):
    case = fixtures["cases"]["singleton-length"]
    payload = case_payload(fixtures, case)
    text = payload["entry"]["source"]
    start = text.index("map_keyed<")
    transform = {"expression": location(text, text[start:text.index(";", start)]),
        "input": location(text, 'keyed<Length> {"only": 0.25[m]}'), "body": location(text, "v * 2"),
        "input_element_type": "Length", "output_element_type": "Length"}
    value = {"type": "Keyed<Length>", "value": [{"key": "only", "value": {"type": "Length", "value": .5}}],
             "status": "resolved", "stale": False}
    control = {"program_revision": case["explicit_c080_control"]["program_revision"],
               "items": [{"path": "shape", "values": {"result": copy.deepcopy(value)}}]}
    value["derived_transforms"] = [transform]
    value["value"][0]["value"]["derived_transforms"] = [{**copy.deepcopy(transform), "key":"only",
        "input_entry":location(text, '"only": 0.25[m]')}]
    actual = {"program_revision": case["program_revision"], "items": [{"path": "shape", "values": {"result": value}}]}
    return case, actual, control, transform, source_units(payload)












def structural_glb(fixtures):
    binary, views, accessors = bytearray(), [], []
    def view(raw):
        binary.extend(b"\0" * (-len(binary) % 4))
        result = len(views)
        views.append({"buffer":0, "byteOffset":len(binary), "byteLength":len(raw)})
        binary.extend(raw)
        return result
    def accessor(raw, count, shape, component=5126):
        result = len(accessors)
        accessors.append({"bufferView":view(raw), "componentType":component, "count":count, "type":shape})
        return result
    positions = accessor(struct.pack("<9f",0,0,0,1,0,0,0,1,0),3,"VEC3")
    normals = accessor(struct.pack("<9f",*(0,0,1)*3),3,"VEC3")
    uvs = accessor(struct.pack("<6f",0,0,1,0,0,1),3,"VEC2")
    indices = accessor(struct.pack("<3H",0,1,2),3,"SCALAR",5123)
    times = accessor(struct.pack("<2f",0,1),2,"SCALAR")
    translations = accessor(struct.pack("<6f",0,0,0,1,0,0),2,"VEC3")
    png = base64.b64decode(case_payload(fixtures, fixtures["cases"]["panel-identity"])["assets"][0]["data_base64"])
    image_view = view(png)
    document = {"asset":{"version":"2.0"}, "buffers":[{"byteLength":len(binary)}], "bufferViews":views, "accessors":accessors,
        "extras":{"ontokin":{"target_contract":TARGET,"schema_version":"0.14","profile":PROFILE}},
        "nodes":[{"mesh":0,"extras":{"ontokin":{"kind":"object","path":'first.panels["left"]',
            "source_mapping":{"generated":{"key":"left"}}}}}],
        "meshes":[{"primitives":[{"attributes":{"POSITION":positions,"NORMAL":normals,"TEXCOORD_0":uvs},
            "indices":indices,"material":0,"extras":{"ontokin":{"region_key":"top"}}}]}],
        "materials":[{"pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"baseColorTexture":{"index":0}}}],
        "textures":[{"source":0,"sampler":0}], "samplers":[{"magFilter":9728,"minFilter":9728,"wrapS":33071,"wrapT":33071}],
        "images":[{"bufferView":image_view,"mimeType":"image/png","extras":{"ontokin":{"asset_id":"label","sha256":digest(png)}}}],
        "animations":[{"samplers":[{"input":times,"output":translations}],"channels":[{"sampler":0,"target":{"node":0,"path":"translation"}}]}]}
    return repack_glb(document, bytes(binary))



class KeyedTransformReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixtures(ROOT / "examples/keyed-transform")

    def test_successful_status_diagnostic_is_not_another_refused_operation(self):
        rejected = {"sequence":1,"response":{"status":"rejected","diagnostics":[{"code":"OKL-E-EXTRUSION-WINDING"}]}}
        status = {"sequence":2,"response":{"status":"succeeded","result":{"target":rejected["response"]}}}
        failed = {"sequence":3,"response":{"status":"failed","diagnostics":[{"code":"OKL-E-RESOURCE"}]}}
        self.assertEqual(terminal_refusals([rejected,status,failed],"OKL-E-EXTRUSION-WINDING"),[rejected])
        self.assertEqual(terminal_refusals([rejected,status,failed],"OKL-E-RESOURCE"),[failed])

    def test_published_freeze_and_source_only_native_expectations(self):
        fixtures = self.fixtures
        assert sha((ROOT / "docs/language-design/keyed-transform-v0.1/INPUT-FREEZE.json").read_bytes()) == FREEZE_SHA256
        assert len(fixtures["cases"]) == 97
        by_revision = delivered_by_revision(fixtures)
        high = fixtures["cases"]["panel-task-higher-budget"]
        denied = fixtures["cases"]["panel-task-ungranted-budget"]
        assert high["program_revision"] == denied["program_revision"]
        assert by_revision[high["program_revision"]]["name"] == high["name"]
        assert denied["expected_outcome"] == "invalid"
        assert canonical_probe_type("Keyed<Quantity[m^2]>") == canonical_probe_type("Keyed<Area>")
        assert canonical_probe_type("Keyed<Point3>") == canonical_probe_type("Keyed<Point3<Length>>")
        assert canonical_probe_type("Keyed<Quantity[m^3]>") == "Keyed<Quantity[m^3]>"
        expected = expectations(fixtures)
        assert len(expected["cases"]) == 4
        original = expected["cases"]["panel-task"]["nodes"]
        repaired = expected["cases"]["panel-task-repaired"]["nodes"]
        assert repaired['first.panels["left"]']["local_bounds_m"] == [[0,0,0],[1.5,2,.25]]
        assert repaired['first.panels["right"]']["local_bounds_m"] == [[0,0,0],[3,2,.25]]
        assert original['sibling.panels["right"]'] == repaired['sibling.panels["right"]']
        assert original["marker"] == repaired["marker"]
        assert sum(n["triangle_count"] for n in original.values()) == 60
        top = repaired['first.panels["right"]']["bindings"]["top"]
        key = struct.pack("<3f", 3, 2, .25).hex()
        assert top["uv_by_position"][key] == struct.pack("<2f", 1.5, 0).hex()

    def test_freeze_reader_refuses_changed_original_input(self):
        fixtures = self.fixtures
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        tmp_path = Path(directory.name)
        repository = tmp_path / "repository"
        for record in fixtures["freeze"]["files"]:
            target = repository / record["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / record["path"], target)
        freeze = "docs/language-design/keyed-transform-v0.1/INPUT-FREEZE.json"
        shutil.copyfile(ROOT / freeze, repository / freeze)
        source = repository / "examples/keyed-transform/sources/singleton-length.ok"
        source.write_bytes(source.read_bytes().replace(b"v * 2", b"v * 3"))
        with self.assertRaisesRegex(ReferenceError, "Frozen bytes changed"):
            load_fixtures(repository / "examples/keyed-transform")

    def test_public_typed_value_comparison_refuses_changed_answer_and_lost_keys(self):
        fixtures = self.fixtures
        case, actual, control, _, _ = singleton_inspections(fixtures)
        assert check_inspection(actual, control, case, fixtures)["scalar_checks"] == 1
        changed = copy.deepcopy(actual)
        changed["items"][0]["values"]["result"]["value"][0]["value"]["value"] = .75
        with self.assertRaisesRegex(ReferenceError, "typed leaf values|scalar answer"):
            check_inspection(changed, control, case, fixtures)
        changed = copy.deepcopy(actual)
        changed["items"][0]["values"]["result"]["value"][0]["key"] = "Only"
        with self.assertRaisesRegex(ReferenceError, "key cardinality/order/case"):
            check_inspection(changed, control, case, fixtures)
        changed = copy.deepcopy(actual)
        del changed["items"][0]["values"]["result"]["value"][0]["value"]["derived_transforms"]
        with self.assertRaisesRegex(ReferenceError, "Missing ordered map derivation"):
            check_inspection(changed, control, case, fixtures)

    def test_derivation_uses_original_key_span_and_null_only_when_unknown(self):
        fixtures = self.fixtures
        case, _, _, transform, units = singleton_inspections(fixtures)
        source = case_payload(fixtures, case)["entry"]["source"]
        leaf = {**transform, "key": "only", "input_entry": location(source, '"only": 0.25[m]')}
        assert check_transforms([leaf], units) == 1
        unknown = {**leaf, "input_entry": None}
        assert check_transforms([unknown], units) == 1
        with self.assertRaisesRegex(ReferenceError, "another original key"):
            check_transforms([{**leaf, "key": "Only"}], units)
        broken = copy.deepcopy(leaf)
        broken["body"] = location(source, "world")
        with self.assertRaisesRegex(ReferenceError, "outside its exact expression"):
            check_transforms([broken], units)
        broken = copy.deepcopy(leaf)
        broken["input_entry"]["source_revision"] = "sha256:" + "0"*64
        with self.assertRaisesRegex(ReferenceError, "hash differs"):
            check_transforms([broken], units)

    def test_identity_normalization_keeps_unknown_metadata_and_refuses_false_profile(self):
        fixtures = self.fixtures
        case = fixtures["cases"]["panel-identity"]
        payload = case_payload(fixtures, case)
        document = {"extras": {"ontokin": {"target_contract": TARGET, "schema_version": "0.14", "profile": PROFILE}},
                    "animations":[{"extras":{"ontokin":{"target_contract":TARGET}}}],
                    "vendor": {"geometry_tolerance": 1e-5, "opaque": [1,2,3]}}
        baseline, changed = SimpleNamespace(document=document), SimpleNamespace(document=copy.deepcopy(document))
        changed.document["vendor"]["geometry_tolerance"] = .5
        a, _ = normalized_document(baseline, payload)
        b, _ = normalized_document(changed, payload)
        assert json_differences(a,b) == [{"path":["vendor","geometry_tolerance"], "actual":1e-5, "control":.5}]
        changed.document["extras"]["ontokin"]["profile"] = "textured-surfaces-0.1"
        with self.assertRaisesRegex(ReferenceError, "Unexpected profile"):
            normalized_document(changed, payload)
        changed.document["extras"]["ontokin"]["profile"] = PROFILE
        changed.document["animations"][0]["extras"]["ontokin"]["target_contract"] = "ontokin.glb/0.13"
        with self.assertRaisesRegex(ReferenceError, "Unexpected target"):
            normalized_document(changed, payload)

    def test_supplied_byte_mutations_change_real_streams_and_are_repeatable(self):
        fixtures = self.fixtures
        raw = structural_glb(fixtures)
        first = build_mutations(raw, "panel-identity")
        assert first == build_mutations(raw, "panel-identity")
        assert len({m["sha256"] for m in first}) == len(MUTATIONS) == 12
        assert all(m["data"] != raw and m["base_sha256"] == sha(raw) and m["sha256"] == sha(m["data"]) for m in first)
        base = GLB(raw, target=TARGET)
        changed = {m["id"]: GLB(m["data"], target=TARGET) for m in first}
        assert changed["G01"].accessor(0)[0] == (.125,0.,0.)
        assert changed["G02"].accessor(1)[0] == (.125,0.,1.)
        assert changed["G03"].accessor(3) == [0,0,2]
        assert changed["G04"].accessor(2)[0] == (.125,0.)
        image = base.document["images"][0]["bufferView"]
        assert changed["G05"].view_bytes(image) != base.view_bytes(image)
        assert changed["G06"].document["images"][0]["extras"]["ontokin"]["sha256"] != digest(base.view_bytes(image))
        assert changed["G09"].accessor(5)[-1] == (1.125,0.,0.)
        assert changed["G10"].document["nodes"][0]["extras"]["ontokin"]["source_mapping"]["generated"]["key"] == "substituted"
        assert "NORMAL" not in changed["G12"].document["meshes"][0]["primitives"][0]["attributes"]


if __name__ == "__main__":
    unittest.main()
