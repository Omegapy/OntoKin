"""Independent C083 reader rejection tests; no product execution or expected-output generation."""
from __future__ import annotations

import base64
import copy
import json
from pathlib import Path
import re
import shutil
import struct
import tempfile
from types import SimpleNamespace
import unittest

from tools.keyed_filter_reference import (FREEZE_SHA256, GLB, PROFILE, TARGET,
    ReferenceError, canonical_probe_type, case_payload, check_all_locations, check_inspection,
    check_filters, check_program_metadata, check_geometry, check_images, check_motion,
    check_raw_framing, compact_json_bytes, diagnostic_anchor, delivered_by_revision,
    digest, filter_source_shape, intrinsic_locations, json_differences, load_fixtures,
    normalized_document, panel_transform, panel_reduction, repack_glb, sha, source_units)
from tools.keyed_filter_reference import nominal_definition_id
from tools.keyed_filter_adversaries import MUTATIONS, build_mutations
from tools.keyed_filter_destination_expectations import expectations
from tools.verify_keyed_filter_agent_evidence import terminal_refusals
from tools.verify_keyed_filter import check_execution_trace

ROOT = Path(__file__).resolve().parents[1]


def location(source, fragment, source_id="entry"):
    raw, sought = source.encode(), fragment.encode()
    start = raw.index(sought)
    return {"source_id": source_id, "source_revision": digest(raw), "filename": "main.ok",
            "start_byte": start, "end_byte": start + len(sought)}


def simple_inspections(fixtures, name="singleton-keep"):
    case = fixtures["cases"][name]
    probe = case["probe"]
    records = copy.deepcopy(case["source_filter_records"])
    value = {"type": probe["type"], "value": [{"key": key, "value": {"type": canonical_probe_type(probe["type"][6:-1]),
                "value": probe["scalar_values"][key]}} for key in probe["keys"]],
             "status": "resolved", "stale": False,
             "dependencies": [{"path": path, "program_revision": case["program_revision"]} for path in case.get("expected", {}).get("observed_dependencies_include", [])]}
    baseline = copy.deepcopy(value)
    baseline["dependencies"] = []
    control = {"program_revision": case["explicit_c082_control"]["program_revision"],
               "items": [{"kind": "object", "path": probe["object_path"], "values": {probe["member"]: baseline}}]}
    value["derived_filters"] = records
    for entry in value["value"]:
        entry["value"]["derived_filters"] = copy.deepcopy(records)
    actual = {"program_revision": case["program_revision"],
              "items": [{"kind": "object", "path": probe["object_path"], "values": {probe["member"]: value}}]}
    return case, actual, control, records, source_units(case_payload(fixtures, case))


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
        "extras":{"ontokin":{"target_contract":TARGET,"schema_version":"0.16","profile":PROFILE,"program":{"revision":fixtures["cases"]["panel-identity"]["program_revision"]}}},
        "nodes":[{"extras":{"ontokin":{"kind":"object","path":"carrier","source_mapping":{"generated":None}}}},
            {"mesh":0,"extras":{"ontokin":{"kind":"object","path":'first.panels["left"]',
            "source_mapping":{"generated":{"key":"left","input_filters":copy.deepcopy(fixtures["cases"]["panel-identity"]["expected"]["filter_provenance"])}}}}}],
        "meshes":[{"primitives":[{"attributes":{"POSITION":positions,"NORMAL":normals,"TEXCOORD_0":uvs},
            "indices":indices,"material":0,"extras":{"ontokin":{"region_key":"top"}}}]}],
        "materials":[{"pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],"baseColorTexture":{"index":0}}}],
        "textures":[{"source":0,"sampler":0}], "samplers":[{"magFilter":9728,"minFilter":9728,"wrapS":33071,"wrapT":33071}],
        "images":[{"bufferView":image_view,"mimeType":"image/png","extras":{"ontokin":{"asset_id":"label","sha256":digest(png)}}}],
        "animations":[{"samplers":[{"input":times,"output":translations}],"channels":[{"sampler":0,"target":{"node":0,"path":"translation"}}]}]}
    return repack_glb(document, bytes(binary))


class KeyedFilterReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixtures(ROOT / "examples/keyed-filter")

    def test_frozen_inventory_exact_sources_controls_and_native_membership(self):
        fixtures = self.fixtures
        self.assertEqual(sha((ROOT / "docs/language-design/keyed-filter-v0.1/INPUT-FREEZE.json").read_bytes()), FREEZE_SHA256)
        self.assertEqual(len(fixtures["cases"]), 141)
        self.assertEqual(sum(case["expected_outcome"] == "valid" for case in fixtures["cases"].values()), 75)
        self.assertEqual(len(delivered_by_revision(fixtures)), 4)
        result = expectations(fixtures)
        self.assertEqual(len(result["cases"]), 5)
        base = result["cases"]["panel-task"]["nodes"]
        repaired = result["cases"]["panel-task-repaired"]["nodes"]
        dropped = result["cases"]["panel-task-drop-all"]["nodes"]
        self.assertEqual((len(base), len(repaired), len(dropped)), (7, 6, 5))
        self.assertEqual([sum(node["triangle_count"] for node in group.values()) for group in (base, repaired, dropped)], [60, 48, 36])
        self.assertNotIn('first.panels["left"]', repaired)
        self.assertNotIn('first.panels["right"]', dropped)
        for path in ('first.panels["right"]', 'sibling.panels["left"]', 'sibling.panels["right"]', 'marker'):
            self.assertEqual(base[path], repaired[path])
        for path in ('sibling.panels["left"]', 'sibling.panels["right"]', 'marker'):
            self.assertEqual(base[path], dropped[path])
        corner = struct.pack("<3f", 2, 2, .25).hex()
        self.assertEqual(repaired['first.panels["right"]']["bindings"]["top"]["uv_by_position"][corner], struct.pack("<2f", 1, 0).hex())

    def test_all_frozen_valid_filter_records_bind_independently(self):
        count = 0
        for case in self.fixtures["cases"].values():
            if case["expected_outcome"] != "valid":
                continue
            units = source_units(case_payload(self.fixtures, case))
            for record in case["source_filter_records"] + case.get("expected", {}).get("filter_provenance", []):
                count += check_filters([record], units)
        self.assertGreater(count, 70)
        for name in ("panel-task", "panel-task-repaired", "panel-task-drop-all"):
            case = self.fixtures["cases"][name]
            self.assertEqual(panel_transform(case, self.fixtures)["input_element_type"], "Real")
            self.assertEqual(panel_reduction(case, self.fixtures)["accumulator_type"], "Length")

    def test_filter_record_refuses_retyping_offsets_missing_hash_and_writable_identity(self):
        case, _, _, records, units = simple_inspections(self.fixtures)
        self.assertEqual(check_filters(records, units), 1)
        for alter in (
            lambda record: record.update(element_type="Real"),
            lambda record: record.update(key="only"),
            lambda record: record["input"].update(start_byte=record["input"]["start_byte"] + 1),
            lambda record: record["predicate"].update(end_byte=record["predicate"]["end_byte"] - 1),
            lambda record: record["expression"].pop("source_revision"),
            lambda record: record["expression"].update(end_byte=record["expression"]["end_byte"] + 1),
        ):
            changed = copy.deepcopy(records)
            alter(changed[0])
            with self.subTest(changed=changed), self.assertRaises((ReferenceError, KeyError)):
                check_filters(changed, units)
        with self.assertRaisesRegex(ReferenceError, "Duplicate"):
            check_filters(records + records, units)

    def test_nested_filter_requires_inner_before_outer(self):
        case = self.fixtures["cases"]["nested-filter"]
        units = source_units(case_payload(self.fixtures, case))
        records = case["source_filter_records"]
        outer, inner = sorted(records, key=lambda r: r["expression"]["start_byte"])
        self.assertEqual(check_filters([inner, outer], units), 2)
        with self.assertRaisesRegex(ReferenceError, "evaluation order"):
            check_filters([outer, inner], units)

    def test_alias_type_canonicalization_is_exact_and_does_not_widen(self):
        self.assertEqual(canonical_probe_type("Quantity[m]"), "Length")
        self.assertEqual(canonical_probe_type("Point3"), "Point3<Length>")
        self.assertNotEqual(canonical_probe_type("Int"), canonical_probe_type("Real"))
        self.assertNotEqual(canonical_probe_type("Quantity[s]"), canonical_probe_type("Length"))
        for name in ("equivalent-quantity-alias", "leaf-point3"):
            case = self.fixtures["cases"][name]
            units = source_units(case_payload(self.fixtures, case))
            record = copy.deepcopy(case["source_filter_records"][0])
            self.assertEqual(check_filters([record], units), 1)
            record["element_type"] = "Quantity[m]" if name == "equivalent-quantity-alias" else "Point3"
            with self.assertRaisesRegex(ReferenceError, "canonical"):
                check_filters([record], units)

    def test_public_surviving_type_value_key_and_leaf_origin_are_all_required(self):
        case, actual, control, _, _ = simple_inspections(self.fixtures)
        self.assertEqual(check_inspection(actual, control, case, self.fixtures)["typed_checks"], 2)
        def target(value):
            return value["items"][0]["values"]["result"]
        for alter in (
            lambda value: target(value)["value"][0].update(key="renamed"),
            lambda value: target(value)["value"][0]["value"].update(value=3),
            lambda value: target(value)["value"][0]["value"].update(type="Real"),
            lambda value: target(value)["value"][0]["value"].pop("derived_filters"),
            lambda value: target(value).pop("derived_filters"),
            lambda value: target(value).update(element_id=["invented"]),
            lambda value: target(value).update(frame="different"),
        ):
            changed = copy.deepcopy(actual)
            alter(changed)
            with self.subTest(changed=changed), self.assertRaises(ReferenceError):
                check_inspection(changed, control, case, self.fixtures)

    def test_empty_output_still_requires_filter_origin(self):
        case, actual, control, _, _ = simple_inspections(self.fixtures, "singleton-drop")
        self.assertEqual(check_inspection(actual, control, case, self.fixtures)["typed_checks"], 1)
        actual["items"][0]["values"]["result"].pop("derived_filters")
        with self.assertRaisesRegex(ReferenceError, "filter"):
            check_inspection(actual, control, case, self.fixtures)

    def test_original_plain_property_cannot_acquire_condition_origins(self):
        case, actual, control, records, _ = simple_inspections(self.fixtures, "condition-retains-filter")
        original = copy.deepcopy(control["items"][0]["values"]["result"])
        actual["items"][0]["values"]["original"] = copy.deepcopy(original)
        control["items"][0]["values"]["original"] = copy.deepcopy(original)
        for entry in actual["items"][0]["values"]["result"]["value"]:
            entry["value"].pop("derived_filters")
        self.assertEqual(check_inspection(actual, control, case, self.fixtures)["status"], "passed")
        actual["items"][0]["values"]["original"]["value"][0]["value"]["derived_filters"] = records
        with self.assertRaisesRegex(ReferenceError, "contaminated"):
            check_inspection(actual, control, case, self.fixtures)

    def test_unselected_dependency_and_old_projection_fields_are_refused(self):
        case, actual, control, records, _ = simple_inspections(self.fixtures, "unselected-predicate-dependency")
        check_inspection(actual, control, case, self.fixtures)
        changed = copy.deepcopy(actual)
        changed["items"][0]["values"]["result"]["dependencies"].append({"path":"shape.threshold", "program_revision":case["program_revision"]})
        with self.assertRaisesRegex(ReferenceError, "unselected"):
            check_inspection(changed, control, case, self.fixtures)
        changed = copy.deepcopy(control)
        changed["items"][0]["values"]["result"]["derived_filters"] = []
        with self.assertRaisesRegex(ReferenceError, "Legacy"):
            check_inspection(actual, changed, case, self.fixtures)

    def test_generated_membership_leaf_value_and_original_entry_span_are_required(self):
        case, actual, control, records, units = simple_inspections(self.fixtures, "generated-mixed")
        source = units["entry"]["source"]
        item = {"kind": "object", "path": 'rig.leaves["z"]',
                "element_id": ["selection", "demo", "rig", "leaves", "z"],
                "source": {"generated": {"input_key": "z", "unique_declaration_span": False,
                    "input_entry_span": location(source, '"z": 0.5[m]'), "input_filters": records}},
                "geometry": {"description": {"kind": "sphere", "radius": .5}, "representation": "authored_analytic_geometry"},
                "values": {"size": {"type": "Length", "value": .5, "status": "resolved", "stale": False}}}
        actual["items"].append(item)
        old = copy.deepcopy(item)
        old["source"]["generated"].pop("input_filters")
        old_source = case_payload(self.fixtures, case, control=True)["entry"]["source"]
        old["source"]["generated"]["input_entry_span"] = location(old_source, '"z": 0.5[m]')
        control["items"].append(old)
        self.assertEqual(check_inspection(actual, control, case, self.fixtures)["status"], "passed")
        for alter in (
            lambda value: value["items"][1]["source"]["generated"].update(input_key="renamed"),
            lambda value: value["items"][1]["source"]["generated"].pop("input_filters"),
            lambda value: value["items"][1]["source"]["generated"].update(input_entry_span=location(source, '"a": 0.25[m]')),
            lambda value: value["items"][1]["geometry"]["description"].update(radius=.75),
            lambda value: value["items"][1]["values"]["size"].update(value=.75),
            lambda value: value["items"].pop(),
        ):
            changed = copy.deepcopy(actual)
            alter(changed)
            with self.subTest(changed=changed), self.assertRaises(ReferenceError):
                check_inspection(changed, control, case, self.fixtures)

    def test_diagnostic_primary_is_the_exact_frozen_expression_span(self):
        count = 0
        for case in self.fixtures["cases"].values():
            if "diagnostic_anchor" not in case:
                continue
            units = source_units(case_payload(self.fixtures, case))
            wanted = case["diagnostic_anchor"]
            primary = {**wanted, "file": "main.ok", "element_id": None}
            receipt = {"diagnostics": [{"code":case["expected_code"], "primary":primary}]}
            self.assertEqual(diagnostic_anchor(receipt, case, units)["end_byte"], primary["end_byte"])
            primary["start_byte"] += 1
            with self.assertRaisesRegex(ReferenceError, "primary span"):
                diagnostic_anchor(receipt, case, units)
            primary["start_byte"] -= 1
            primary["end_byte"] -= 1
            with self.assertRaisesRegex(ReferenceError, "primary span"):
                diagnostic_anchor(receipt, case, units)
            count += 1
        self.assertEqual(count, 9)

    def test_source_qualified_called_definition_binds_pin_module_and_nominal_key(self):
        case = self.fixtures["cases"]["imported-legacy-predicate"]
        units = source_units(case_payload(self.fixtures, case))
        locator = case["expected"]["called_definition_ids_include"][0]
        self.assertEqual(nominal_definition_id(locator, units), ("package", "fixture.legacy", "legacy", "definitions", "keep"))
        for index, value in ((0, "package:fixture.legacy@9.0.0"), (1, "other"), (3, "unknown")):
            changed = list(locator)
            changed[index] = value
            with self.assertRaises(ReferenceError):
                nominal_definition_id(changed, units)
        changed_units = copy.deepcopy(units)
        changed_units[locator[0]]["version"] = "9.0.0"
        with self.assertRaisesRegex(ReferenceError, "pin differs"):
            nominal_definition_id(locator, changed_units)

    def test_source_delimiter_reader_ignores_comments_strings_and_preserves_utf8(self):
        source = 'ontokin "0.16"; profile "keyed-filter-0.1"; // café filter_keyed<Int>(bad)\n"filter_keyed<Int>(ignored)"; filter_keyed<Int>(keyed<Int>{"a": 1}, (k, v) -> true)'
        units = {"entry":{"source":source, "filename":"main.ok"}}
        locations = intrinsic_locations(units, b"filter_keyed")
        self.assertEqual(len(locations), 1)
        shape = filter_source_shape(locations[0], units)
        raw = source.encode()
        predicate = shape["parts"]["predicate"]
        self.assertEqual(raw[predicate["start_byte"]:predicate["end_byte"]], b"true")
        self.assertEqual(shape["element_type"], "Int")

    def test_named_revision_alias_cannot_hide_different_membership(self):
        changed = copy.deepcopy(self.fixtures)
        changed["cases"]["panel-identity"]["expected"]["widths_m"]["first"].pop("left")
        with self.assertRaisesRegex(ReferenceError, "aliases disagree"):
            delivered_by_revision(changed)

    def test_freeze_rejects_changed_bytes_and_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repository = Path(tmp)
            for entry in self.fixtures["freeze"]["files"]:
                target = repository / entry["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / entry["path"], target)
            freeze = "docs/language-design/keyed-filter-v0.1/INPUT-FREEZE.json"
            shutil.copy2(ROOT / freeze, repository / freeze)
            source = repository / "examples/keyed-filter/sources/singleton-keep.ok"
            original = source.read_bytes()
            source.write_bytes(original + b"\n")
            with self.assertRaisesRegex(ReferenceError, "Frozen bytes changed"):
                load_fixtures(repository / "examples/keyed-filter")
            source.write_bytes(original)
            source.chmod(0o755)
            with self.assertRaisesRegex(ReferenceError, "Frozen mode changed"):
                load_fixtures(repository / "examples/keyed-filter")

    def test_twelve_mutations_retain_null_generated_ordinary_carriers(self):
        case = self.fixtures["cases"]["panel-identity"]
        raw = structural_glb(self.fixtures)
        first = build_mutations(raw, case)
        self.assertEqual([item["id"] for item in first], [f"H{i:02}" for i in range(1, 13)])
        self.assertEqual([item["mutation"] for item in first], list(MUTATIONS))
        self.assertEqual(len({item["sha256"] for item in first}), 12)
        self.assertEqual(first, build_mutations(raw, case))
        for item in first:
            self.assertEqual(item["base_sha256"], sha(raw))
            self.assertEqual(item["sha256"], sha(item["data"]))
            self.assertNotEqual(item["data"], raw)
        old = GLB(raw, target=TARGET)
        self.assertIsNone(old.document["nodes"][0]["extras"]["ontokin"]["source_mapping"]["generated"])
        self.assertEqual(GLB(first[0]["data"], target=TARGET).document, old.document)
        self.assertNotEqual(GLB(first[0]["data"], target=TARGET).binary, old.binary)
        with self.assertRaises(ReferenceError):
            GLB(first[-1]["data"], target=TARGET)
        altered = GLB(first[9]["data"], target=TARGET).document["nodes"][1]["extras"]["ontokin"]["source_mapping"]["generated"]["input_filters"]
        with self.assertRaisesRegex(ReferenceError, "element type"):
            check_filters(altered, source_units(case_payload(self.fixtures, case)))

    def test_normalization_preserves_unknown_json_and_checks_filter_bytes(self):
        case = self.fixtures["cases"]["panel-task"]
        payload = case_payload(self.fixtures, case)
        origin = case["expected"]["filter_provenance"]
        document = {"extras":{"ontokin":{"target_contract":TARGET, "schema_version":"0.16", "profile":PROFILE,
            "program":{"revision":case["program_revision"], "manifest":case["canonical_manifest"]}, "unknown":{"keep":1}}},
            "nodes":[{"extras":{"ontokin":{"program_revision":case["program_revision"],
                "source_mapping":{"generated":{"input_filters":copy.deepcopy(origin)}}}}}]}
        normalized, changes = normalized_document(SimpleNamespace(document=document), payload)
        self.assertEqual(normalized["extras"]["ontokin"]["unknown"], {"keep":1})
        self.assertNotIn("input_filters", normalized["nodes"][0]["extras"]["ontokin"]["source_mapping"]["generated"])
        self.assertTrue(any(item["kind"] == "adopted_filter_derivation" for item in changes))
        changed = copy.deepcopy(document)
        changed["extras"]["ontokin"]["unknown"]["keep"] = 2
        other, _ = normalized_document(SimpleNamespace(document=changed), payload)
        self.assertTrue(json_differences(normalized, other))
        changed = copy.deepcopy(document)
        changed["nodes"][0]["extras"]["ontokin"]["source_mapping"]["generated"]["input_filters"][0]["predicate"]["start_byte"] += 1
        with self.assertRaises(ReferenceError):
            normalized_document(SimpleNamespace(document=changed), payload)
        changed = copy.deepcopy(document)
        changed["extras"]["ontokin"]["unknown"]["program_revision"] = case["program_revision"]
        normalized, _ = normalized_document(SimpleNamespace(document=changed), payload)
        self.assertEqual(normalized["extras"]["ontokin"]["unknown"]["program_revision"], case["program_revision"])

    def test_raw_json_framing_and_member_order_are_not_semantic_only(self):
        raw = structural_glb(self.fixtures)
        self.assertTrue(check_raw_framing(GLB(raw, target=TARGET))["verified_framing"])
        self.assertEqual(json_differences({"a":1,"b":2}, {"b":2,"a":1}), [])
        self.assertNotEqual(compact_json_bytes({"a":1,"b":2}), compact_json_bytes({"b":2,"a":1}))
        malformed = bytearray(raw)
        struct.pack_into("<I", malformed, 8, len(raw) + 4)
        with self.assertRaises(ReferenceError):
            GLB(bytes(malformed), target=TARGET)

    def test_successful_status_diagnostics_are_not_new_refusals(self):
        refused = {"response":{"status":"rejected", "diagnostics":[{"code":"OKL-E-NAME"}]}}
        status = {"response":{"status":"succeeded", "result":{"target":refused["response"]}}}
        self.assertEqual(terminal_refusals([refused, status], "OKL-E-NAME"), [refused])

    def test_observed_traversal_requires_one_input_strict_bool_and_current_ledger(self):
        case = self.fixtures["cases"]["singleton-drop"]
        budget = {"consumed_operations": 20, "effective": case["host_policy"], "host_ceilings": case["host_policy"]}
        invocation = {**copy.deepcopy(case["source_filter_records"][0]), "self_path": "shape", "input_evaluations": 1,
            "static_predicate_checks": 1, "input_keys": ["only"], "predicate_keys": ["only"], "output_keys": [],
            "input_type": "Keyed<Length>", "output_type": "Keyed<Length>", "operations_before": 1, "operations_after": 10,
            "value_entries_before": 0, "value_entries_after": 10,
            "predicates": [{"key": "only", "key_type": "String", "value_type": "Length", "result_type": "Bool", "result": False,
                "operations_before": 4, "operations_after": 8, "value_entries_before": 5, "value_entries_after": 6}],
            "checkpoints": [{"stage": "keyed_filter_iteration", "consumed_operations": 2, "value_entries": 2}]}
        trace = {"schema_version": "ontokin.c083-filter-execution-observation/0.1", "case": case["name"], "program_revision": case["program_revision"],
            "profile": PROFILE, "requested_level": "represented", "public_api": "KeyedFilterProgramRuntime.validate_revision",
            "invocations": [invocation], "execution_budget": copy.deepcopy(budget)}
        units = source_units(case_payload(self.fixtures, case))
        self.assertEqual(check_execution_trace(trace, case, units, budget)["predicate_visits"], 1)
        for alter in (
            lambda value: value["invocations"][0].update(input_evaluations=2),
            lambda value: value["invocations"][0].update(predicate_keys=[]),
            lambda value: value["invocations"][0]["predicates"][0].update(result=0),
            lambda value: value["invocations"][0]["predicates"][0].update(result=True),
            lambda value: value["invocations"][0]["checkpoints"][0].update(consumed_operations=9),
            lambda value: value["execution_budget"].update(consumed_operations=19),
        ):
            changed = copy.deepcopy(trace)
            alter(changed)
            with self.subTest(changed=changed), self.assertRaises(ReferenceError):
                check_execution_trace(changed, case, units, budget)


if __name__ == "__main__":
    unittest.main()
