"""Frozen filtering contracts and observable construction invariants."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import SourceUnit
from ontokin.construction import ConstructionCompiler, ConstructionBudget, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.profile_capabilities import KEYED_FILTER_PROFILE, KEYED_REDUCTION_PROFILE
from ontokin.texture_bundle import TextureBundle, load_texture_file_manifest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-filter"
CASES = json.loads((FIXTURES / "expected.json").read_bytes())["cases"]


def compile_bundle(bundle, *, policy=None, caller_caps=None, check=None, budgets=None):
    ledger = SharedExecutionBudget(policy, caller_caps=caller_caps)
    if check is not None:
        ledger.check = lambda: check(ledger)
    profile = (KEYED_REDUCTION_PROFILE if bundle.entry.raw.lstrip().startswith(b'ontokin "0.15";')
               else KEYED_FILTER_PROFILE)
    admit_entry_budget(bundle.entry, ledger, profile=profile)
    return compile_construction(bundle, execution_budget=ledger, budgets=budgets)


def compile_case(name, **kwargs):
    case = next(c for c in CASES if c["name"] == name)
    bundle = load_texture_file_manifest(FIXTURES / case["file_manifest"])
    return compile_bundle(bundle, policy=HostPolicy(**case["host_policy"]), **kwargs)


def compile_text(text, **kwargs):
    return compile_bundle(TextureBundle(SourceUnit("entry", "main.ok", text.encode()), ()), **kwargs)


def program(expression, *, typ="Keyed<Int>", members="", before="", geometry=None):
    geometry = geometry or 'if len(self.result) >= 0 then box(vec3(1[m], 1[m], 1[m])) else empty()'
    return f'''ontokin "0.16";
module Core @ "core";
profile "keyed-filter-0.1";
{before}
public class Shape @ "shape-class" {{
 {members}
 public derive result @ "result": {typ} = {expression};
 geometry = {geometry};
 physical = no_body();
}}
scene Demo @ "demo" {{
 duration = 1[s];
 gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
 object shape @ "shape": Shape {{}}
}}
'''


def location(record):
    return {k: record[k] for k in ("source_id", "source_revision", "start_byte", "end_byte")}


class KeyedFilterCoreTests(unittest.TestCase):
    def test_published_freeze_and_all_source_outcomes(self):
        path = ROOT / "docs/language-design/keyed-filter-v0.1/INPUT-FREEZE.json"
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         "cc01defc6296ce9c66c094607ecd054da84d38bd1c358d4b846f1baec65b3d3e")
        for record in json.loads(path.read_bytes())["files"]:
            self.assertEqual(hashlib.sha256((ROOT / record["path"]).read_bytes()).hexdigest(),
                             record["sha256"], record["path"])
        for case in CASES:
            with self.subTest(case=case["name"]):
                if case["expected_outcome"] == "invalid":
                    with self.assertRaises(OntoKinError) as caught:
                        compile_case(case["name"])
                    self.assertEqual(caught.exception.code, case["expected_code"])
                    if case.get("diagnostic_anchor"):
                        node, expected = caught.exception.diagnostic.node, case["diagnostic_anchor"]
                        self.assertEqual((node.source_id, node.start, node.end),
                            (expected["source_id"], expected["start_byte"], expected["end_byte"]))
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
                filters = compiler.filter_provenance(value)
                self.assertEqual(bool(filters), probe["filter_required"])
                self.assertEqual([location(r["expression"]) for r in filters],
                                 probe.get("required_filter_expression_order", []))
                expected_records = {tuple(location(r["expression"]).items()): r for r in case["source_filter_records"]}
                for record in filters:
                    self.assertEqual(set(record), {"expression", "input", "predicate", "element_type"})
                    expected = expected_records[tuple(location(record["expression"]).items())]
                    self.assertEqual(record["element_type"], expected["element_type"])
                    for name in ("expression", "input", "predicate"):
                        self.assertEqual(location(record[name]), expected[name])
                for kind in ("transform", "reduction"):
                    records = getattr(compiler, kind + "_provenance")(value)
                    actual = [location(r["expression"]) for r in records]
                    for expected in probe["required_" + kind + "_expressions"]:
                        self.assertIn(expected, actual)

    def test_input_once_predicate_order_and_detached_copies(self):
        expression = ConstructionCompiler.expression
        charge = ConstructionBudget.charge_value
        for entries, expected in [('"z": 2, "A": 1', [("A", 1), ("z", 2)]), ("", [])]:
            with self.subTest(entries=entries):
                scope, evaluations, copies = [], [], []
                def observed(compiler, node, ctx):
                    root = node.kind == "filter_keyed" and not ctx.abstract
                    if root:
                        scope.append(node)
                    try:
                        if scope and not ctx.abstract:
                            active = scope[-1]
                            if node is active.input:
                                evaluations.append(("input",))
                            elif node is active.predicate:
                                evaluations.append(("predicate", ctx.locals[active.key_name].value,
                                                    ctx.locals[active.value_name].value))
                        return expression(compiler, node, ctx)
                    finally:
                        if root:
                            scope.pop()
                def charged(budget, value, node=None):
                    if scope:
                        active = scope[-1]
                        for label, origin in (("key", active.key_node), ("value", active.value_node),
                                              ("kept", active.predicate), ("final", active)):
                            if node is origin:
                                copies.append((label, value))
                    return charge(budget, value, node)
                with patch.object(ConstructionCompiler, "expression", observed), patch.object(ConstructionBudget, "charge_value", charged):
                    compiler = compile_text(program(f'filter_keyed<Int>(keyed<Int>{{{entries}}}, (k, v) -> v >= 2)'))
                self.assertEqual(evaluations, [("input",)] + [("predicate", *row) for row in expected])
                self.assertEqual([name for name, _ in copies],
                                 ["key", "value", "key", "value", "kept", "final"] if expected else ["final"])
                self.assertEqual(len({id(value) for _, value in copies}), len(copies))
                self.assertEqual([key for key, _ in compiler.field("shape", "result").value.entries], ["z"] if expected else [])

    def test_bad_input_admission_precedes_actual_predicate(self):
        expression = ConstructionCompiler.expression
        calls = []
        def observed(compiler, node, ctx):
            if node.kind == "binary" and node.op == "/" and not ctx.abstract:
                calls.append(node)
            return expression(compiler, node, ctx)
        with patch.object(ConstructionCompiler, "expression", observed):
            with self.assertRaises(OntoKinError) as caught:
                compile_case("admission-before-predicate-domain")
        self.assertEqual(caught.exception.code, "OKL-E-TYPE")
        self.assertEqual(calls, [])

    def test_dropped_first_entry_does_not_skip_later_failure(self):
        expression, observed_keys = ConstructionCompiler.expression, []
        def observed(compiler, node, ctx):
            if not ctx.abstract and node.kind == "binary" and node.op == "<" and "k" in ctx.locals:
                observed_keys.append(ctx.locals["k"].value)
            return expression(compiler, node, ctx)
        with patch.object(ConstructionCompiler, "expression", observed):
            with self.assertRaises(OntoKinError) as caught:
                compile_case("later-domain-failure")
        self.assertEqual(caught.exception.code, "OKL-E-NUMERIC")
        self.assertEqual(observed_keys, ["a", "z"])

    def test_actual_dependencies_survive_empty_results_and_cache_replay(self):
        for case in CASES:
            expected = case.get("expected", {})
            if "observed_dependencies_include" not in expected:
                continue
            with self.subTest(case=case["name"]):
                compiler = compile_case(case["name"])
                probe = case["probe"]
                compiler.field(probe["object_path"], probe["member"])
                actual = {path + "." + name for path, name in
                          compiler.dependencies.get((probe["object_path"], probe["member"]), ())}
                for name in expected["observed_dependencies_include"]:
                    self.assertIn(name, actual)
                for name in expected.get("observed_dependencies_exclude", []):
                    self.assertNotIn(name, actual)

    def test_filter_provenance_does_not_mutate_original_or_equal_valued_sibling(self):
        compiler = compile_case("survivor-original-alias")
        original, filtered = compiler.field("shape", "original"), compiler.field("shape", "result")
        self.assertEqual(compiler.filter_provenance(original), [])
        self.assertEqual(compiler.filter_provenance(compiler.field("shape", "untouched")), [])
        self.assertIsNot(filtered.value, original.value)
        self.assertIsNot(filtered.value.lookup("b"), original.value.lookup("b"))
        self.assertEqual(compiler.filter_provenance(original.value.lookup("b")), [])
        self.assertTrue(compiler.filter_provenance(filtered.value.lookup("b")))
        compiler = compile_case("equal-valued-plain-filtered-occurrences")
        for key in ("a", "z"):
            selected = compiler.model.occurrence_provenance[f'selected.leaves["{key}"]']["generated"]
            plain = compiler.model.occurrence_provenance[f'plain.leaves["{key}"]']["generated"]
            self.assertTrue(selected["input_filters"])
            self.assertNotIn("input_filters", plain)
            self.assertEqual(compiler.filter_provenance(compiler.field(f'plain.leaves["{key}"]', "size")), [])

    def test_indexing_filtered_condition_does_not_taint_shared_plain_leaf(self):
        text = program('self.plain', before='''
public class Leaf @ "leaf" {
 public param size @ "size": Length = 1[m];
 geometry = sphere(self.size);
 physical = no_body();
}
''', members='''
 public param plain @ "plain": Keyed<Int> = keyed<Int>{"a": 1};
 public parts children @ "children": Leaf for (ck, cv) in keyed<Int>{"first": 1} {}
 public derive selected @ "selected": Keyed<Int> = if len(filter_keyed<Int>(
 keyed<Int>{"check": 1}, (fk, fv) -> self.children["first"].size > 0[m])) == 1
 then self.plain else self.plain;
 public derive indexed @ "indexed": Int = self.selected["a"];
 public derive untouched @ "untouched": Int = self.plain["a"];
''', geometry='if self.indexed == 1 then box(vec3(1[m], 1[m], 1[m])) else empty()')
        compiler = compile_text(text)
        selected = compiler.field("shape", "selected")
        plain = compiler.field("shape", "plain")
        self.assertIs(selected.value, plain.value)
        self.assertTrue(compiler._value_taints.get(id(selected)))
        self.assertTrue(compiler._value_taints.get(id(compiler.field("shape", "indexed"))))
        self.assertFalse(compiler._value_taints.get(id(plain.value.lookup("a"))))
        self.assertFalse(compiler._value_taints.get(id(compiler.field("shape", "untouched"))))

    def test_generated_condition_retains_filter_when_plain_payload_is_selected(self):
        compiler = compile_case("generated-condition-retains-filter")
        generated = [p["generated"] for p in compiler.model.occurrence_provenance.values() if p["generated"]]
        self.assertTrue(generated)
        for record in generated:
            self.assertTrue(record["input_filters"])
            self.assertIsNotNone(record["input_entry"])

    def test_downstream_discard_keeps_filter_origin(self):
        for name in ("map-constant-retains-filter", "reduce-constant-retains-filter",
                     "empty-map-retains-filter", "empty-reduce-retains-filter"):
            with self.subTest(case=name):
                compiler = compile_case(name)
                value = compiler.field("shape", "result")
                self.assertTrue(compiler.filter_provenance(value))
                if value.type.kind == "Keyed":
                    for _, leaf in value.value.entries:
                        self.assertTrue(compiler.filter_provenance(leaf))

    def test_actual_iteration_cancellation_keeps_callback_exception(self):
        sentinel = RuntimeError("cancel at actual filter iteration")
        stages = []
        def cancel(ledger):
            if ledger.stage == "keyed_filter_iteration":
                stages.append(ledger.stage)
                raise sentinel
        with self.assertRaises(RuntimeError) as caught:
            compile_case("singleton-keep", check=cancel)
        self.assertIs(caught.exception, sentinel)
        self.assertEqual(stages, ["keyed_filter_iteration"])

    def test_caller_operation_reduction_stays_cumulative(self):
        with self.assertRaises(OntoKinError) as caught:
            compile_case("maximum-256", caller_caps={"max_operations": 100})
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")


if __name__ == "__main__":
    unittest.main()
