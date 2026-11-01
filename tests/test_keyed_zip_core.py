"""Frozen pairing outcomes, original source origins and real work checkpoints."""

import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.construction import ConstructionCompiler, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.profile_capabilities import KEYED_MERGE_PROFILE, KEYED_ZIP_PROFILE
from ontokin.texture_bundle import load_texture_file_manifest
from tools.keyed_zip_reference import load_fixtures


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-zip"
CASES = load_fixtures(FIXTURES)["expected"]["cases"]
FREEZE_SHA256 = "4914fd1696bc0c441736684289a4c4422c9db30ba99091dfbbbf8d1eb1c8a2a9"


def compile_case(case, *, check=None, caller_caps=None):
    if isinstance(case, str):
        case = next(row for row in CASES if row["name"] == case)
    bundle = load_texture_file_manifest(FIXTURES / case["file_manifest"])
    ledger = SharedExecutionBudget(HostPolicy(**case["host_policy"]), caller_caps=caller_caps)
    if check is not None:
        ledger.check = lambda: check(ledger)
    profile = (KEYED_MERGE_PROFILE if bundle.entry.raw.lstrip().startswith(b'ontokin "0.17";')
               else KEYED_ZIP_PROFILE)
    admit_entry_budget(bundle.entry, ledger, profile=profile)
    level = "constructed" if case["expected_stage"] == "constructed" else "represented"
    return compile_construction(bundle, level=level, execution_budget=ledger)


def location(value):
    if value is None:
        return None
    return {key: value[key] for key in ("source_id", "source_revision", "start_byte", "end_byte")}


def normalized(records):
    return [{**row, **{key: location(row[key]) for key in
                       ("expression", "left", "right", "body", "left_entry", "right_entry")}}
            for row in records]


class KeyedZipCoreTests(unittest.TestCase):
    def test_published_inputs_are_unchanged(self):
        path = ROOT / "docs/language-design/keyed-zip-v0.1/INPUT-FREEZE.json"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), FREEZE_SHA256)
        rows = json.loads(path.read_bytes())["files"]
        self.assertEqual(len(rows), 856)
        for row in rows:
            self.assertEqual(hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest(),
                             row["sha256"], row["path"])

    def test_all_frozen_source_outcomes_and_original_diagnostics(self):
        self.assertEqual(len(CASES), 254)
        for case in CASES:
            with self.subTest(case=case["name"]):
                if case["expected_outcome"] == "invalid":
                    with self.assertRaises(OntoKinError) as caught:
                        compile_case(case)
                    error = caught.exception.diagnostic
                    self.assertEqual(error.code, case["expected_code"])
                    self.assertEqual(error.category, case["expected_protocol_outcome"])
                    anchor = case.get("diagnostic_anchor")
                    if anchor:
                        self.assertEqual(error.node.source_id, anchor["source_id"])
                        if case.get("diagnostic_anchor_mode") == "contains_token":
                            self.assertLessEqual(error.node.start, anchor["start_byte"])
                            self.assertGreaterEqual(error.node.end, anchor["end_byte"])
                        else:
                            self.assertEqual((error.node.start, error.node.end),
                                             (anchor["start_byte"], anchor["end_byte"]))
                    for field in ("details", "category", "phase", "rule_ids"):
                        if "diagnostic_" + field in case:
                            actual = getattr(error, field)
                            if field == "rule_ids" and actual is None:
                                from ontokin.bundle import SourceUnit
                                actual = error.to_dict(SourceUnit("entry", "main.ok", b"").to_source())[field]
                            self.assertEqual(actual, case["diagnostic_" + field])
                    if "diagnostic_related" in case:
                        self.assertEqual([(node.source_id, node.start, node.end) for node in error.related],
                                         [(row["source_id"], row["start_byte"], row["end_byte"])
                                          for row in case["diagnostic_related"]])
                    continue
                compiler = compile_case(case)
                probe = case.get("probe")
                if not probe:
                    continue
                value = compiler.field(probe["object_path"], probe["member"])
                self.assertEqual(str(value.type), probe["type"])
                if "keys" in probe:
                    self.assertEqual([key for key, _ in value.value.entries], probe["keys"])
                if "scalar_values" in probe:
                    self.assertEqual({key: leaf.value for key, leaf in value.value.entries}, probe["scalar_values"])
                if "scalar_value" in probe:
                    self.assertEqual(value.value, probe["scalar_value"])
                records = compiler.zip_provenance(value)
                self.assertEqual(bool(records), probe["zip_required"])
                order = []
                for row in records:
                    self.assertEqual(set(row), {"expression", "left", "right", "body",
                        "left_element_type", "right_element_type", "output_element_type",
                        "key", "left_entry", "right_entry"})
                    here = location(row["expression"])
                    if here not in order:
                        order.append(here)
                    frozen = next(item for item in case["source_zip_records"] if item["expression"] == here)
                    for field in ("expression", "left", "right", "body"):
                        self.assertEqual(location(row[field]), frozen[field])
                    for field in ("left_element_type", "right_element_type", "output_element_type"):
                        self.assertEqual(row[field], frozen[field])
                    if value.type.kind == "Keyed":
                        self.assertIsNone(row["key"])
                        self.assertIsNone(row["left_entry"])
                        self.assertIsNone(row["right_entry"])
                self.assertEqual(order, probe["required_zip_expression_order"])
                for kind in ("transform", "reduction", "filter", "merge"):
                    actual = [location(row["expression"]) for row in getattr(compiler, kind + "_provenance")(value)]
                    for expected in probe["required_" + kind + "_expressions"]:
                        self.assertIn(expected, actual)

    def test_exact_nested_aggregate_leaf_and_generated_origins(self):
        for case in CASES:
            expected = case.get("expected", {})
            if not any(key in expected for key in ("aggregate_zip_records_exact", "derived_zips_exact",
                                                  "stored_leaf_zips_exact", "generated_input_zips_exact")):
                continue
            with self.subTest(case=case["name"]):
                compiler = compile_case(case)
                probe = case.get("probe")
                if probe:
                    value = compiler.field(probe["object_path"], probe["member"])
                    name = "aggregate_zip_records_exact" if value.type.kind == "Keyed" else "derived_zips_exact"
                    if name in expected:
                        self.assertEqual(normalized(compiler.zip_provenance(value)), expected[name])
                    if value.type.kind == "Keyed" and "stored_leaf_zips_exact" in expected:
                        for key, frozen in expected["stored_leaf_zips_exact"].items():
                            leaf = value.value.lookup(key)
                            self.assertEqual(normalized(compiler.zip_provenance(leaf)), frozen)
                for path, frozen in expected.get("generated_input_zips_exact", {}).items():
                    actual = compiler.model.occurrence_provenance[path]["generated"]["input_zips"]
                    self.assertEqual(normalized(actual), frozen)

    def test_complete_admission_keyset_and_canonical_callback_order(self):
        admission = ConstructionCompiler._keyed_zip_input
        checkpoint = ConstructionCompiler._keyed_zip_checkpoint
        for name in ("both-empty", "singleton-add", "authored-entry-reordering", "maximum-256"):
            case = next(row for row in CASES if row["name"] == name)
            with self.subTest(case=name):
                admissions, events = [], []
                def observed_input(compiler, operand, token, ctx, element_type):
                    value = admission(compiler, operand, token, ctx, element_type)
                    if not ctx.abstract:
                        admissions.append(operand.start)
                    return value
                def observed_checkpoint(compiler, node, stage, key):
                    events.append((stage, key))
                    return checkpoint(compiler, node, stage, key)
                with patch.object(ConstructionCompiler, "_keyed_zip_input", observed_input), \
                        patch.object(ConstructionCompiler, "_keyed_zip_checkpoint", observed_checkpoint):
                    compile_case(case)
                source = case["source_zip_records"][0]
                self.assertEqual(admissions, [source["left"]["start_byte"], source["right"]["start_byte"]])
                self.assertEqual(events, [("keyed_zip_keyset", key) for key in case["expected"]["keyset_check_order"]]
                                 + [("keyed_zip_iteration", key) for key in case["expected"]["body_key_order"]])

    def test_actual_checkpoint_callback_preserves_original_exception(self):
        class CallbackFailure(Exception):
            pass
        for stage in ("keyed_zip_keyset", "keyed_zip_iteration"):
            sentinel = CallbackFailure(stage)
            visited = []
            def check(ledger):
                if ledger.stage == stage:
                    visited.append(stage)
                    raise sentinel
            with self.subTest(stage=stage), self.assertRaises(CallbackFailure) as caught:
                compile_case("singleton-add", check=check)
            self.assertIs(caught.exception, sentinel)
            self.assertTrue(visited)

    def test_caller_cap_never_grants_more_work(self):
        with self.assertRaises(OntoKinError) as caught:
            compile_case("maximum-256", caller_caps={"max_operations": 100})
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
        compiler = compile_case("maximum-256")
        self.assertEqual(len(compiler.field("shape", "result").value.entries), 256)

    def test_detached_aliases_and_public_locations(self):
        compiler = compile_case("input-alias-remains-unmodified")
        result = compiler.field("shape", "result")
        original = compiler.field("shape", "left_items")
        untouched = compiler.field("shape", "untouched")
        self.assertEqual(compiler.zip_provenance(original), [])
        self.assertEqual(compiler.zip_provenance(untouched), [])
        for key, leaf in result.value.entries:
            self.assertIsNot(leaf, original.value.lookup(key))
            self.assertEqual(compiler.zip_provenance(original.value.lookup(key)), [])
        projection = compiler.zip_provenance(result)
        projection[0]["left"]["start_byte"] = -1
        projection[0]["key"] = "invented"
        self.assertGreaterEqual(compiler.zip_provenance(result)[0]["left"]["start_byte"], 0)
        self.assertIsNone(compiler.zip_provenance(result)[0]["key"])


if __name__ == "__main__":
    unittest.main()
