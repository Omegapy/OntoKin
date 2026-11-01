"""Frozen disjoint-union outcomes and observable source construction behavior."""

import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import SourceUnit
from ontokin.construction import ConstructionCompiler, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.profile_capabilities import KEYED_FILTER_PROFILE, KEYED_MERGE_PROFILE
from ontokin.texture_bundle import TextureBundle, load_texture_file_manifest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-merge"
CASES = json.loads((FIXTURES / "expected.json").read_bytes())["cases"]
FREEZE_SHA256 = "5f45a5c3f0231440ec34199a4bf977fc5abb694dfdf5c600380f7e2299609d48"


def compile_bundle(bundle, *, policy=None, caller_caps=None, check=None, level="represented"):
    ledger = SharedExecutionBudget(policy, caller_caps=caller_caps)
    if check is not None:
        ledger.check = lambda: check(ledger)
    profile = (KEYED_FILTER_PROFILE if bundle.entry.raw.lstrip().startswith(b'ontokin "0.16";')
               else KEYED_MERGE_PROFILE)
    admit_entry_budget(bundle.entry, ledger, profile=profile)
    return compile_construction(bundle, level=level, execution_budget=ledger)


def compile_case(name, **kwargs):
    case = next(case for case in CASES if case["name"] == name)
    bundle = load_texture_file_manifest(FIXTURES / case["file_manifest"])
    level = "constructed" if case["expected_stage"] == "constructed" else "represented"
    return compile_bundle(bundle, policy=HostPolicy(**case["host_policy"]), level=level, **kwargs)


def compile_text(text, **kwargs):
    return compile_bundle(TextureBundle(SourceUnit("entry", "main.ok", text.encode()), ()), **kwargs)


def program(expression, *, typ="Keyed<Int>", members="", before=""):
    return f'''ontokin "0.17";
module Core @ "core";
profile "keyed-merge-0.1";
{before}
public class Shape @ "shape-class" {{
 {members}
 public derive result @ "result": {typ} = {expression};
 geometry = if len(self.result) >= 0 then box(vec3(1[m], 1[m], 1[m])) else empty();
 physical = no_body();
}}
scene Demo @ "demo" {{
 duration = 1[s];
 gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
 object shape @ "shape": Shape {{}}
}}
'''


def location(record):
    return {key: record[key] for key in ("source_id", "source_revision", "start_byte", "end_byte")}


def normalized(records):
    return [{**record, **{name: location(record[name]) for name in ("expression", "left", "right")}}
            for record in records]


class KeyedMergeCoreTests(unittest.TestCase):
    def test_published_freeze_and_all_source_outcomes(self):
        freeze = ROOT / "docs/language-design/keyed-merge-v0.1/INPUT-FREEZE.json"
        self.assertEqual(hashlib.sha256(freeze.read_bytes()).hexdigest(), FREEZE_SHA256)
        for entry in json.loads(freeze.read_bytes())["files"]:
            self.assertEqual(hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest(),
                             entry["sha256"], entry["path"])
        self.assertEqual(len(CASES), 144)
        for case in CASES:
            with self.subTest(case=case["name"]):
                if case["expected_outcome"] == "invalid":
                    with self.assertRaises(OntoKinError) as caught:
                        compile_case(case["name"])
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
                                actual = error.to_dict(SourceUnit("entry", "main.ok", b"").to_source())[field]
                            self.assertEqual(actual, case["diagnostic_" + field])
                    if "diagnostic_related" in case:
                        self.assertEqual([(node.source_id, node.start, node.end) for node in error.related],
                            [(item["source_id"], item["start_byte"], item["end_byte"])
                             for item in case["diagnostic_related"]])
                    continue
                compiler = compile_case(case["name"])
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
                records = compiler.merge_provenance(value)
                self.assertEqual(bool(records), probe["merge_required"])
                expression_order = []
                for record in records:
                    self.assertEqual(set(record), {"expression", "left", "right", "element_type", "input_side"})
                    self.assertIn(record["input_side"], {"both", "left", "right"})
                    here = location(record["expression"])
                    if here not in expression_order:
                        expression_order.append(here)
                    expected = next(item for item in case["source_merge_records"]
                                    if item["expression"] == here)
                    for field in ("expression", "left", "right"):
                        self.assertEqual(location(record[field]), expected[field])
                    self.assertEqual(record["element_type"], expected["element_type"])
                self.assertEqual(expression_order, probe.get("required_merge_expression_order", []))
                for kind in ("transform", "reduction", "filter"):
                    actual = [location(record["expression"])
                              for record in getattr(compiler, kind + "_provenance")(value)]
                    for expected in probe["required_" + kind + "_expressions"]:
                        self.assertIn(expected, actual)

    def test_actual_operand_admissions_and_key_order(self):
        admission = ConstructionCompiler._keyed_merge_input
        checkpoint = ConstructionCompiler._keyed_merge_checkpoint
        for name in ("both-empty", "empty-left", "empty-right", "mixed-membership", "maximum-256"):
            case = next(case for case in CASES if case["name"] == name)
            with self.subTest(case=name):
                admitted, stages = [], []
                def observed_admission(compiler, operand, token, ctx, element_type):
                    result = admission(compiler, operand, token, ctx, element_type)
                    if not ctx.abstract:
                        admitted.append(operand.start)
                    return result
                def observed_checkpoint(compiler, node, stage, key):
                    stages.append((stage, key))
                    return checkpoint(compiler, node, stage, key)
                with patch.object(ConstructionCompiler, "_keyed_merge_input", observed_admission), \
                        patch.object(ConstructionCompiler, "_keyed_merge_checkpoint", observed_checkpoint):
                    compile_case(name)
                record = case["source_merge_records"][0]
                self.assertEqual(admitted, [record["left"]["start_byte"], record["right"]["start_byte"]])
                self.assertEqual([key for stage, key in stages if stage == "keyed_merge_collision"],
                                 case["expected"]["collision_key_order"])
                self.assertEqual([key for stage, key in stages if stage == "keyed_merge_iteration"],
                                 case["expected"]["materialization_key_order"])

    def test_collision_finishes_admission_and_publishes_no_materialization(self):
        admission = ConstructionCompiler._keyed_merge_input
        checkpoint = ConstructionCompiler._keyed_merge_checkpoint
        admitted, stages = [], []
        def observed_admission(compiler, operand, token, ctx, element_type):
            result = admission(compiler, operand, token, ctx, element_type)
            if not ctx.abstract:
                admitted.append(operand.start)
            return result
        def observed_checkpoint(compiler, node, stage, key):
            stages.append((stage, key))
            return checkpoint(compiler, node, stage, key)
        with patch.object(ConstructionCompiler, "_keyed_merge_input", observed_admission), \
                patch.object(ConstructionCompiler, "_keyed_merge_checkpoint", observed_checkpoint):
            with self.assertRaises(OntoKinError) as caught:
                compile_case("collision-multiple-canonical")
        self.assertEqual(caught.exception.code, "OKL-E-ID")
        self.assertEqual(len(admitted), 2)
        self.assertEqual(stages, [("keyed_merge_collision", "A")])

    def test_detached_entries_do_not_change_source_or_sibling(self):
        text = program('merge_keyed<Int>(self.left, self.right)', members='''
 public derive left @ "left": Keyed<Int> = keyed<Int>{"a": 1};
 public derive right @ "right": Keyed<Int> = keyed<Int>{"b": 2};
 public derive unchanged @ "unchanged": Keyed<Int> = self.left;
''')
        compiler = compile_text(text)
        result = compiler.field("shape", "result")
        left = compiler.field("shape", "left")
        right = compiler.field("shape", "right")
        sibling = compiler.field("shape", "unchanged")
        originals = {**dict(left.value.entries), **dict(right.value.entries)}
        for key, leaf in result.value.entries:
            self.assertIsNot(leaf, originals[key])
            self.assertEqual(leaf.type, originals[key].type)
            self.assertEqual(leaf.value, originals[key].value)
            self.assertEqual(compiler.merge_provenance(originals[key]), [])
            self.assertEqual(compiler.merge_provenance(leaf)[-1]["input_side"], "left" if key == "a" else "right")
        self.assertEqual(compiler.merge_provenance(left), [])
        self.assertEqual(compiler.merge_provenance(right), [])
        self.assertEqual(compiler.merge_provenance(sibling), [])
        projection = compiler.merge_provenance(result)
        projection[0]["left"]["start_byte"] = -1
        projection[0]["input_side"] = "right"
        self.assertEqual(compiler.merge_provenance(result)[0]["input_side"], "both")
        self.assertGreaterEqual(compiler.merge_provenance(result)[0]["left"]["start_byte"], 0)

    def test_nested_aggregate_entry_generated_and_indexed_record_order(self):
        case = next(case for case in CASES if case["name"] == "nested-merge-generated-contributions")
        compiler = compile_case(case["name"])
        value = compiler.field("rig", "result")
        self.assertEqual(normalized(compiler.merge_provenance(value)), case["expected"]["aggregate_merges_exact"])
        for path, expected in case["expected"]["generated_input_merges_exact"].items():
            self.assertEqual(normalized(compiler.model.occurrence_provenance[path]["generated"]["input_merges"]), expected)
        case = next(case for case in CASES if case["name"] == "nested-merge-indexed-scalar")
        compiler = compile_case(case["name"])
        value = compiler.field("shape", "result")
        self.assertEqual(normalized(compiler.merge_provenance(value)), case["expected"]["derived_merges_exact"])

    def test_ignored_values_and_empty_results_keep_aggregate_origins(self):
        for name in ("map-constant-retains-merge", "reduce-constant-retains-merge", "drop-all-retains-merge",
                     "empty-map-retains-merge", "empty-reduce-retains-merge"):
            with self.subTest(case=name):
                compiler = compile_case(name)
                value = compiler.field("shape", "result")
                self.assertTrue(compiler.merge_provenance(value))
                if value.type.kind == "Keyed":
                    for _, leaf in value.value.entries:
                        self.assertTrue(compiler.merge_provenance(leaf))

    def test_generated_members_keep_other_operand_aggregate_maps(self):
        compiler = compile_case("panel-task-repaired")
        for collection in compiler.collections.values():
            if collection["name"] != "panels":
                continue
            aggregate = compiler.transform_provenance(collection["input_value"])
            expected = {tuple(location(record["expression"]).items()) for record in aggregate}
            self.assertEqual(len(expected), 2)
            for path in collection["entries"].values():
                actual = compiler.model.occurrence_provenance[path]["generated"]["input_transforms"]
                self.assertEqual({tuple(location(record["expression"]).items()) for record in actual}, expected)
                for record in actual:
                    if "key" in record:
                        self.assertEqual(record["key"], compiler.model.occurrence_provenance[path]["generated"]["key"])

    def test_downstream_transform_origins_do_not_invent_another_operand_key(self):
        left = 'map_keyed<Int>(keyed<Int>{"a": 1}, (ka, va) -> va)'
        right = 'map_keyed<Int>(keyed<Int>{"b": 2}, (kb, vb) -> vb)'
        merged = f'merge_keyed<Int>({left}, {right})'
        for expression in (f'map_keyed<Int>({merged}, (kc, vc) -> vc)',
                           f'filter_keyed<Int>({merged}, (kc, vc) -> true)'):
            with self.subTest(expression=expression):
                text = program(expression)
                compiler = compile_text(text)
                right_start = text.encode().index(right.encode())
                left_leaf = dict(compiler.field("shape", "result").value.entries)["a"]
                records = compiler.transform_provenance(left_leaf)
                unrelated = [record for record in records if record["expression"]["start_byte"] == right_start]
                self.assertTrue(unrelated)
                self.assertTrue(all("key" not in record for record in unrelated))

        # The condition reads the map while the chosen plain input has its own
        # unrelated key. Indexing must preserve that distinction as well.
        text = program(f'keyed<Int>{{"out": (if len({right}) > 0 then keyed<Int>{{"a": 1}} else keyed<Int>{{}})["a"]}}')
        compiler = compile_text(text)
        right_start = text.encode().index(right.encode())
        result = dict(compiler.field("shape", "result").value.entries)["out"]
        records = [record for record in compiler.transform_provenance(result)
                   if record["expression"]["start_byte"] == right_start]
        self.assertTrue(records)
        self.assertTrue(all("key" not in record for record in records))

    def test_generated_binding_keeps_aggregate_maps_through_reduction_and_filter_wrappers(self):
        source = (FIXTURES / "sources/generated-union.ok").read_text()
        source = source.replace('keyed<Length>{"a": 0.25[m]}',
            'map_keyed<Length>(keyed<Int>{"a": reduce_keyed<Int>(keyed<Int>{"r": 1}, 0, '
            '(acc, rk, rv) -> acc + rv)}, (mk, mv) -> mv * 0.25[m])')
        source = source.replace('keyed<Length>{"z": 0.5[m]}',
            'filter_keyed<Length>(map_keyed<Length>(keyed<Int>{"b": 2}, '
            '(mk, mv) -> mv * 0.25[m]), (fk, fv) -> false)')
        for ignores_value in (False, True):
            with self.subTest(ignores_value=ignores_value):
                text = source.replace("size = child_value;", "size = 0.25[m];") if ignores_value else source
                compiler = compile_text(text)
                generated = compiler.model.occurrence_provenance['rig.leaves["a"]']["generated"]
                self.assertEqual(len(generated["input_transforms"]), 2)
                self.assertEqual(len(generated["input_reductions"]), 1)
                self.assertEqual(len(generated["input_filters"]), 1)
                self.assertEqual([record["input_side"] for record in generated["input_merges"]], ["both", "left"])
                self.assertEqual(sum("key" in record for record in generated["input_transforms"]), 1)
                if not ignores_value:
                    size = compiler.field('rig.leaves["a"]', "size")
                    self.assertEqual(len(compiler.transform_provenance(size)), 2)
                    self.assertEqual(len(compiler.reduction_provenance(size)), 1)
                    self.assertEqual(len(compiler.filter_provenance(size)), 1)

    def test_actual_cancellation_stages_preserve_callback_identity(self):
        for stage in ("keyed_merge_collision", "keyed_merge_iteration"):
            for sentinel in (RuntimeError("cancel actual merge"), OntoKinError("OKL-E-TYPE", "callback identity")):
                with self.subTest(stage=stage, exception=type(sentinel).__name__):
                    reached = []
                    def cancel(ledger):
                        if ledger.stage == stage:
                            reached.append(stage)
                            raise sentinel
                    with self.assertRaises(type(sentinel)) as caught:
                        compile_case("mixed-membership", check=cancel)
                    self.assertIs(caught.exception, sentinel)
                    self.assertEqual(reached, [stage])

    def test_caller_cap_remains_cumulative(self):
        with self.assertRaises(OntoKinError) as caught:
            compile_case("maximum-256", caller_caps={"max_operations": 100})
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")


if __name__ == "__main__":
    unittest.main()
