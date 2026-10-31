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

from tools.keyed_reduction_reference import (FREEZE_SHA256, GLB, PROFILE, TARGET,
    ReferenceError, canonical_probe_type, case_payload, check_all_locations, check_inspection, delivered_by_revision,
    check_transforms, check_reductions, check_raw_framing, compact_json_bytes, require_expression_origins,
    digest, json_differences, load_fixtures, normalized_document, reduction_source_shape,
    repack_glb, sha, source_units)
from tools.keyed_reduction_adversaries import MUTATIONS, build_mutations
from tools.keyed_reduction_destination_expectations import expectations
from tools.verify_keyed_reduction_agent_evidence import terminal_refusals

ROOT = Path(__file__).resolve().parents[1]




def location(source, fragment):
    raw, sought = source.encode(), fragment.encode()
    start = raw.index(sought)
    return {"source_id": "entry", "source_revision": digest(raw), "filename": "main.ok",
            "start_byte": start, "end_byte": start + len(sought)}


def singleton_inspections(fixtures):
    case = fixtures["cases"]["singleton-length"]
    payload = case_payload(fixtures, case)
    source = payload["entry"]["source"]
    start = source.index("reduce_keyed<")
    origin = {"expression": location(source, source[start:source.index(";", start)]),
        "input": location(source, 'keyed<Length>{"only": 0.25[m]}'),
        "seed": location(source, "0.5[m]"), "body": location(source, "acc + v"),
        "input_element_type": "Length", "accumulator_type": "Length"}
    value = {"type": "Length", "value": .75, "status": "resolved", "stale": False,
             "dependencies": []}
    control = {"program_revision": case["explicit_c081_control"]["program_revision"],
               "items": [{"path": "shape", "values": {"result": copy.deepcopy(value)}}]}
    value["derived_reductions"] = [origin]
    actual = {"program_revision": case["program_revision"],
              "items": [{"path": "shape", "values": {"result": value}}]}
    return case, actual, control, origin, source_units(payload)


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
        "extras":{"ontokin":{"target_contract":TARGET,"schema_version":"0.15","profile":PROFILE}},
        "nodes":[{"mesh":0,"extras":{"ontokin":{"kind":"object","path":'first.panels["left"]',
            "source_mapping":{"generated":{"key":"left"}}}}}],
        "meshes":[{"primitives":[{"attributes":{"POSITION":positions,"NORMAL":normals,"TEXCOORD_0":uvs},
            "indices":indices,"material":0,"extras":{"ontokin":{"region_key":"top"}}}]}],
        "materials":[{"pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"baseColorTexture":{"index":0}}}],
        "textures":[{"source":0,"sampler":0}], "samplers":[{"magFilter":9728,"minFilter":9728,"wrapS":33071,"wrapT":33071}],
        "images":[{"bufferView":image_view,"mimeType":"image/png","extras":{"ontokin":{"asset_id":"label","sha256":digest(png)}}}],
        "animations":[{"samplers":[{"input":times,"output":translations}],"channels":[{"sampler":0,"target":{"node":0,"path":"translation"}}]}]}
    return repack_glb(document, bytes(binary))



class KeyedReductionReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixtures(ROOT / "examples/keyed-reduction")

    def test_successful_status_diagnostic_is_not_another_refused_operation(self):
        rejected = {"sequence":1,"response":{"status":"rejected","diagnostics":[{"code":"OKL-E-EXTRUSION-WINDING"}]}}
        status = {"sequence":2,"response":{"status":"succeeded","result":{"target":rejected["response"]}}}
        failed = {"sequence":3,"response":{"status":"failed","diagnostics":[{"code":"OKL-E-RESOURCE"}]}}
        self.assertEqual(terminal_refusals([rejected,status,failed],"OKL-E-EXTRUSION-WINDING"),[rejected])
        self.assertEqual(terminal_refusals([rejected,status,failed],"OKL-E-RESOURCE"),[failed])

    def test_published_freeze_and_source_only_native_expectations(self):
        fixtures = self.fixtures
        assert sha((ROOT / "docs/language-design/keyed-reduction-v0.1/INPUT-FREEZE.json").read_bytes()) == FREEZE_SHA256
        assert len(fixtures["cases"]) == 128
        by_revision = delivered_by_revision(fixtures)
        assert len(by_revision) == 3
        assert fixtures["cases"]["panel-task"]["program_revision"] == fixtures["cases"]["panel-identity"]["program_revision"]
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

    def test_revision_alias_refuses_conflicting_independent_answers(self):
        changed = copy.deepcopy(self.fixtures)
        changed["cases"]["panel-identity"]["expected"]["aggregate_lengths_m"]["first"] = 7
        with self.assertRaisesRegex(ReferenceError, "aliases disagree"):
            delivered_by_revision(changed)

    def test_generated_occurrence_key_radius_and_reduction_are_independently_checked(self):
        case = self.fixtures["cases"]["generated-shape-from-reduction"]
        source = case_payload(self.fixtures, case)["entry"]["source"]
        expression = 'reduce_keyed<Length>(self.sizes, 0[m], (acc, k, v) -> acc + v)'
        origin = {"expression": location(source, expression), "input": location(source, "self.sizes"),
                  "seed": location(source, "0[m]"), "body": location(source, "acc + v"),
                  "input_element_type": "Length", "accumulator_type": "Length"}
        item = {"kind": "object", "path": 'rig.leaves["sum"]',
                "source": {"generated": {"input_key": "sum"}},
                "geometry": {"available": True, "representation": "authored_analytic_geometry",
                             "description": {"kind": "sphere", "radius": .75}},
                "values": {"size": {"type": "Length", "value": .75, "status": "resolved", "stale": False}}}
        control = {"program_revision": case["explicit_c081_control"]["program_revision"], "items": [copy.deepcopy(item)]}
        item["source"]["generated"]["input_reductions"] = [origin]
        item["values"]["size"]["derived_reductions"] = [origin]
        actual = {"program_revision": case["program_revision"], "items": [item]}
        self.assertEqual(check_inspection(actual, control, case, self.fixtures)["scalar_checks"], 2)
        for label, alter in (
            ("keys differ", lambda x: x["source"]["generated"].update(input_key="invented")),
            ("sphere geometry", lambda x: x["geometry"]["description"].update(radius=7)),
            ("typed radius", lambda x: x["values"]["size"].update(value=7)),
            ("Missing ordered reduction", lambda x: x["source"]["generated"].pop("input_reductions")),
        ):
            changed = copy.deepcopy(actual)
            alter(changed["items"][0])
            with self.assertRaisesRegex(ReferenceError, label):
                check_inspection(changed, control, case, self.fixtures)

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
        freeze = "docs/language-design/keyed-reduction-v0.1/INPUT-FREEZE.json"
        shutil.copyfile(ROOT / freeze, repository / freeze)
        source = repository / "examples/keyed-reduction/sources/singleton-length.ok"
        source.write_bytes(source.read_bytes().replace(b"acc + v", b"acc - v"))
        with self.assertRaisesRegex(ReferenceError, "Frozen bytes changed"):
            load_fixtures(repository / "examples/keyed-reduction")

    def test_public_aggregate_comparison_refuses_changed_answer_frame_and_lost_origin(self):
        case, actual, control, _, _ = singleton_inspections(self.fixtures)
        assert check_inspection(actual, control, case, self.fixtures)["scalar_checks"] == 1
        changed = copy.deepcopy(actual)
        changed["items"][0]["values"]["result"]["value"] = 1.0
        with self.assertRaisesRegex(ReferenceError, "typed aggregate|scalar aggregate"):
            check_inspection(changed, control, case, self.fixtures)
        changed = copy.deepcopy(actual)
        changed["items"][0]["values"]["result"]["frame"] = "invented"
        with self.assertRaisesRegex(ReferenceError, "frame"):
            check_inspection(changed, control, case, self.fixtures)
        changed = copy.deepcopy(actual)
        del changed["items"][0]["values"]["result"]["derived_reductions"]
        with self.assertRaisesRegex(ReferenceError, "Missing ordered reduction"):
            check_inspection(changed, control, case, self.fixtures)
        changed = copy.deepcopy(actual)
        changed["items"][0]["values"]["result"]["element_id"] = ["iteration", 0]
        with self.assertRaisesRegex(ReferenceError, "new editable"):
            check_inspection(changed, control, case, self.fixtures)

    def test_reduction_span_types_and_no_iteration_identity(self):
        case, _, _, origin, units = singleton_inspections(self.fixtures)
        assert check_reductions([origin], units) == 1
        changed = copy.deepcopy(origin)
        changed["seed"] = location(units["entry"]["source"], "world")
        with self.assertRaisesRegex(ReferenceError, "outside its exact expression"):
            check_reductions([changed], units)
        with self.assertRaisesRegex(ReferenceError, "invented identity"):
            check_reductions([{**origin, "key": "only"}], units)
        with self.assertRaisesRegex(ReferenceError, "Duplicate"):
            check_reductions([origin, origin], units)
        changed = copy.deepcopy(origin)
        changed["seed"]["source_revision"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ReferenceError, "hash differs"):
            check_reductions([changed], units)
        with self.assertRaisesRegex(ReferenceError, "required reduction"):
            require_expression_origins([], case["probe"]["required_reduction_expressions"], units, "reduction")
        changed = copy.deepcopy(origin)
        changed["seed"] = changed["body"]
        with self.assertRaisesRegex(ReferenceError, "Exact frozen source span differs"):
            check_reductions([changed], units)
        for field in ("input_element_type", "accumulator_type"):
            changed = copy.deepcopy(origin)
            changed[field] = "Bool"
            with self.assertRaisesRegex(ReferenceError, "type differs from its explicit source"):
                check_reductions([changed], units)

    def test_independent_reduction_delimiters_cover_all_frozen_explicit_input_types(self):
        checked = 0
        for case in self.fixtures["cases"].values():
            if case["expected_outcome"] != "valid":
                continue
            units = source_units(case_payload(self.fixtures, case))
            origins = list(case.get("probe", {}).get("required_reduction_expressions", []))
            if "reduction_provenance" in case.get("expected", {}):
                origins.append(case["expected"]["reduction_provenance"]["expression"])
            for origin in origins:
                with self.subTest(case=case["name"], start=origin["start_byte"]):
                    shape = reduction_source_shape(origin, units)
                    self.assertIsNotNone(shape["input_element_type"])
                    self.assertTrue(shape["accumulator_type"])
                    checked += 1
        self.assertGreater(checked, 60)

    def test_source_delimiters_respect_comments_strings_and_nested_calls(self):
        source = ('reduce_keyed<String>(keyed<Int>{"a,)(/*": 1}, /* ) , */ "seed,)", '
                  '(acc, key, value) -> if true then "a,)(/*" else acc)')
        units = {"entry": {"source": source, "filename": "main.ok"}}
        shape = reduction_source_shape(location(source, source), units)
        self.assertEqual(shape["input_element_type"], "Int")
        self.assertEqual(shape["accumulator_type"], "String")
        self.assertEqual(shape["parts"]["input"], {k:v for k,v in location(source, 'keyed<Int>{"a,)(/*": 1}').items() if k!="filename"})
        self.assertEqual(shape["parts"]["seed"], {k:v for k,v in location(source, '"seed,)"').items() if k!="filename"})
        self.assertEqual(shape["parts"]["body"], {k:v for k,v in location(source, 'if true then "a,)(/*" else acc').items() if k!="filename"})

    def test_nested_reduction_requires_earlier_inner_derivation(self):
        source = 'reduce_keyed<Int>(keyed<Int>{}, reduce_keyed<Int>(keyed<Int>{}, 3, (a,k,v)->a), (b,l,w)->b)'
        inner = 'reduce_keyed<Int>(keyed<Int>{}, 3, (a,k,v)->a)'
        units = {"entry": {"source": source, "filename": "main.ok"}}
        inner_start = source.index(inner)
        def at(fragment, start=0):
            offset = source.index(fragment, start)
            return {"source_id":"entry", "source_revision":digest(source.encode()),
                    "start_byte":offset, "end_byte":offset+len(fragment)}
        older = {"expression":at(inner), "input":at("keyed<Int>{}",inner_start),
                 "seed":at("3"), "body":at("a", source.index("->a")+2),
                 "input_element_type":"Int", "accumulator_type":"Int"}
        current = {"expression":at(source), "input":at("keyed<Int>{}"), "seed":at(inner),
                   "body":at("b",source.index("->b")+2), "input_element_type":"Int", "accumulator_type":"Int"}
        assert check_reductions([older,current],units)==2
        with self.assertRaisesRegex(ReferenceError,"evaluation order"):
            check_reductions([current,older],units)

    def test_identity_normalization_keeps_unknown_metadata_and_refuses_false_profile(self):
        fixtures = self.fixtures
        case = fixtures["cases"]["panel-identity"]
        payload = case_payload(fixtures, case)
        document = {"extras": {"ontokin": {"target_contract": TARGET, "schema_version": "0.15", "profile": PROFILE}},
                    "animations":[{"extras":{"ontokin":{"target_contract":TARGET}}}],
                    "vendor": {"geometry_tolerance": 1e-5, "opaque": [1,2,3]}}
        baseline, changed = SimpleNamespace(document=document), SimpleNamespace(document=copy.deepcopy(document))
        changed.document["vendor"]["geometry_tolerance"] = .5
        a, _ = normalized_document(baseline, payload)
        b, _ = normalized_document(changed, payload)
        assert json_differences(a,b) == [{"path":["vendor","geometry_tolerance"], "actual":1e-5, "control":.5}]
        changed.document["extras"]["ontokin"]["profile"] = "keyed-transform-0.1"
        with self.assertRaisesRegex(ReferenceError, "Unexpected profile"):
            normalized_document(changed, payload)
        changed.document["extras"]["ontokin"]["profile"] = PROFILE
        changed.document["animations"][0]["extras"]["ontokin"]["target_contract"] = "ontokin.glb/0.14"
        with self.assertRaisesRegex(ReferenceError, "Unexpected target"):
            normalized_document(changed, payload)

    def test_unknown_origin_shaped_metadata_is_never_normalized_away(self):
        case, _, _, reduction, _ = singleton_inspections(self.fixtures)
        payload = case_payload(self.fixtures, case)
        document = {"extras":{"ontokin":{"target_contract":TARGET,"schema_version":"0.15","profile":PROFILE}},
            "vendor":{"derived_reductions":[reduction], "revision":case["program_revision"]}}
        normalized, changes = normalized_document(SimpleNamespace(document=document), payload)
        self.assertEqual(normalized["vendor"],document["vendor"])
        self.assertFalse(any(change["path"][0]=="vendor" for change in changes))

    def test_actual_dependency_inclusion_and_unselected_exclusion_are_checked(self):
        case, actual, control, _, _ = singleton_inspections(self.fixtures)
        case = copy.deepcopy(case)
        case["expected"] = {"observed_dependencies_include":["shape.dep"],
                            "observed_dependencies_exclude":["shape.unselected"]}
        with self.assertRaisesRegex(ReferenceError,"actual earlier dependency"):
            check_inspection(actual,control,case,self.fixtures)
        value=actual["items"][0]["values"]["result"]
        value["dependencies"]=[{"path":"shape.dep","program_revision":case["program_revision"]}]
        self.assertEqual(check_inspection(actual,control,case,self.fixtures)["scalar_checks"],1)
        value["dependencies"].append({"path":"shape.unselected","program_revision":case["program_revision"]})
        with self.assertRaisesRegex(ReferenceError,"unselected dynamic dependency"):
            check_inspection(actual,control,case,self.fixtures)

    def test_raw_json_whitespace_and_framing_cannot_hide_in_parsed_equality(self):
        raw=structural_glb(self.fixtures)
        glb=GLB(raw,target=TARGET)
        self.assertTrue(check_raw_framing(glb)["verified_framing"])
        text=b" " + compact_json_bytes(glb.document)
        text += b" " * (-len(text)%4)
        changed=(struct.pack("<III",0x46546c67,2,28+len(text)+len(glb.binary))+
                 struct.pack("<II",len(text),0x4e4f534a)+text+
                 struct.pack("<II",len(glb.binary),0x004e4942)+glb.binary)
        decoded=GLB(changed,target=TARGET)
        self.assertEqual(decoded.document,glb.document)
        with self.assertRaisesRegex(ReferenceError,"Raw GLB JSON"):
            check_raw_framing(decoded)

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
