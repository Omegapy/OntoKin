"""The adopted pure map, frozen source outcomes, and bounded provenance flow."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import SourceUnit
from ontokin.construction import ConstructionCompiler, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.profile_capabilities import KEYED_TRANSFORM_PROFILE, TEXTURE_PROFILE
from ontokin.texture_bundle import TextureBundle, load_texture_file_manifest
from ontokin.validator import Context


FIXTURES = Path(__file__).resolve().parents[1] / "examples/keyed-transform"
CASES = json.loads((FIXTURES / "expected.json").read_bytes())["cases"]
BY_NAME = {case["name"]: case for case in CASES}


def compile_bundle(bundle, *, policy=None, caller_caps=None, check=None, budgets=None):
    ledger = SharedExecutionBudget(policy, caller_caps=caller_caps)
    if check is not None:
        ledger.check = lambda: check(ledger)
    profile = (TEXTURE_PROFILE if 'profile "textured-surfaces-0.1";' in bundle.entry.text
               else KEYED_TRANSFORM_PROFILE)
    admit_entry_budget(bundle.entry, ledger, profile=profile)
    return compile_construction(bundle, execution_budget=ledger, budgets=budgets)


def compile_case(name, **kwargs):
    case = BY_NAME[name]
    bundle = load_texture_file_manifest(FIXTURES / case["file_manifest"])
    return compile_bundle(bundle, policy=HostPolicy(**case["host_policy"]), **kwargs)


def program(expression, *, typ="Int", before="", members="", imports=""):
    return f'''ontokin "0.14";
module Core @ "core";
profile "keyed-transform-0.1";
{imports}
{before}
public class Shape @ "shape-class" {{
 {members}
 public derive result @ "result": Keyed<{typ}> = {expression};
 geometry = if len(self.result) >= 0 then box(vec3(1[m], 1[m], 1[m])) else empty();
 physical = no_body();
}}
scene Demo @ "demo" {{
 duration = 1[s];
 gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
 object shape @ "shape": Shape {{}}
}}
'''


def compile_text(text, *, modules=(), **kwargs):
    return compile_bundle(TextureBundle(SourceUnit("entry", "main.ok", text.encode()), modules), **kwargs)


def context(compiler):
    cls = compiler.instances["shape"].cls
    return Context("shape", cls.name, cls.name)


class KeyedTransformCoreTests(unittest.TestCase):
    def test_all_97_predetermined_represented_outcomes_and_values(self):
        self.assertEqual(len(CASES), 97)
        for case in CASES:
            with self.subTest(case=case["id"], name=case["name"]):
                if case["expected_code"]:
                    with self.assertRaises(OntoKinError) as caught:
                        compile_case(case["name"])
                    self.assertEqual(caught.exception.code, case["expected_code"])
                    continue
                compiler = compile_case(case["name"])
                self.assertEqual(compiler.bundle.program_revision, case["program_revision"])
                self.assertEqual(compiler.bundle.manifest(), case["canonical_manifest"])
                probe = case.get("probe")
                if probe:
                    value = compiler.field(probe["object_path"], probe["member"])
                    spelling = probe["type"].replace("Quantity[m^2]", "Area").replace("<Point3>", "<Point3<Length>>")
                    self.assertEqual(str(value.type), spelling)
                    self.assertEqual([key for key, _ in value.value.entries], probe["keys"])
                    for key, expected in probe.get("scalar_values", {}).items():
                        actual = value.value.lookup(key).value
                        if type(expected) in (int, float):
                            self.assertAlmostEqual(actual, expected, places=12)
                        else:
                            self.assertEqual(actual, expected)

    def test_empty_maps_never_enter_a_dynamic_iteration(self):
        for name in ("empty-length", "empty-domain-body", "empty-local-zero-branch"):
            with self.subTest(name=name):
                stages = []
                compile_case(name, check=lambda ledger: stages.append(ledger.stage))
                self.assertNotIn("keyed_transform_iteration", stages)

    def test_input_helper_runs_once_and_keys_visit_canonical_order(self):
        text = program('map_keyed<Int>(supply(), (k, v) -> v + 1)', before='''
public fn supply @ "supply"() -> Keyed<Int> {
 return keyed<Int>{"z": 8, "A": 1, "a.b": 3};
}''')
        calls, selected = [], []
        original = ConstructionCompiler.expression
        def observed(compiler, node, ctx):
            if not ctx.abstract and node.kind == "call" and node.callee.kind == "name" and node.callee.name == "supply":
                calls.append(node)
            if not ctx.abstract and node.kind == "binary" and node.left.kind == "name" and node.left.name == "v":
                selected.append(ctx.locals["k"].value)
            return original(compiler, node, ctx)
        with patch.object(ConstructionCompiler, "expression", observed):
            compiler = compile_text(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(selected, ["A", "a.b", "z"])
        self.assertEqual(dict((key, value.value) for key, value in compiler.field("shape", "result").value.entries),
                         {"A": 2, "a.b": 4, "z": 9})

    def test_binders_cannot_hide_inherited_constructors_types_or_class_fields(self):
        for spelling in ("surface_material", "loft_section", "planar_point", "polygon_vertex",
                         "polygon_ring", "polygon_section", "framed_polygon_section", "polygon_pocket",
                         "planar_uv", "LoftSection", "PolygonRing", "TextureBinding", "geometry", "frame"):
            with self.subTest(spelling=spelling):
                text = program(f'map_keyed<Int>(keyed<Int>{{"a": 1}}, ({spelling}, v) -> v)')
                with self.assertRaises(OntoKinError) as caught:
                    compile_text(text)
                self.assertEqual(caught.exception.code, "OKL-E-NAME")
                node = caught.exception.diagnostic.node
                self.assertEqual(text.encode()[node.start:node.end], spelling.encode())

    def test_chains_keep_original_entries_and_detached_source_locations(self):
        text = program('map_keyed<Int>(self.first, (k2, v2) -> v2 + 1)', members='''
public param original @ "original": Keyed<Int> = keyed<Int>{"a": 2};
public derive first @ "first": Keyed<Int> = map_keyed<Int>(self.original, (k1, v1) -> v1 * 3);''')
        compiler = compile_text(text)
        value = compiler.field("shape", "result")
        aggregate = compiler.transform_provenance(value)
        leaf = compiler.transform_provenance(value.value.lookup("a"))
        self.assertEqual(len(aggregate), 2)
        self.assertTrue(all("key" not in row and "input_entry" not in row for row in aggregate))
        self.assertEqual([row["key"] for row in leaf], ["a", "a"])
        self.assertEqual(leaf[0]["input_entry"], leaf[1]["input_entry"])
        raw = text.encode()
        origin = leaf[0]["input_entry"]
        self.assertEqual(raw[origin["start_byte"]:origin["end_byte"]], b'"a": 2')
        bodies = [raw[row["body"]["start_byte"]:row["body"]["end_byte"]] for row in leaf]
        self.assertEqual(bodies, [b"v1 * 3", b"v2 + 1"])
        self.assertEqual(compiler.transform_provenance(compiler.field("shape", "original")), [])
        aggregate[0]["expression"]["start_byte"] = -1
        leaf[0]["input_entry"]["start_byte"] = -1
        self.assertGreaterEqual(compiler.transform_provenance(value)[0]["expression"]["start_byte"], 0)
        self.assertGreaterEqual(compiler.transform_provenance(value.value.lookup("a"))[0]["input_entry"]["start_byte"], 0)

    def test_nested_selected_leaf_keeps_inner_and_outer_keys(self):
        text = program('''map_keyed<Int>(keyed<Int>{"left": 1}, (outer_key, outer_value) ->
map_keyed<Int>(keyed<Int>{"right": 2}, (inner_key, inner_value) -> inner_value + outer_value)["right"])''')
        compiler = compile_text(text)
        value = compiler.field("shape", "result")
        leaf = value.value.lookup("left")
        self.assertEqual(leaf.value, 3)
        records = compiler.transform_provenance(leaf)
        self.assertEqual([row["key"] for row in records], ["right", "left"])
        self.assertTrue(all("key" not in row for row in compiler.transform_provenance(value)))

    def test_pure_helper_and_guarded_cache_preserve_transformed_leaf(self):
        text = program('keyed<Int>{"answer": pick(self.mapped)}', before='''
public fn pick @ "pick"(items: Keyed<Int>) -> Int { return items["left"] + 1; }
''', members='''
public derive mapped @ "mapped": Keyed<Int> = map_keyed<Int>(keyed<Int>{"left": 3}, (k, v) -> v * 2);
''')
        compiler = compile_text(text)
        result = compiler.field("shape", "result")
        self.assertEqual(result.value.lookup("answer").value, 7)
        self.assertEqual([row["key"] for row in compiler.transform_provenance(result.value.lookup("answer"))], ["left"])
        self.assertIs(result, compiler.field("shape", "result"))
        self.assertEqual(compiler.transform_provenance(result.value.lookup("answer")),
                         compiler.transform_provenance(compiler.field("shape", "result").value.lookup("answer")))

    def test_generated_occurrences_expose_actual_input_transform(self):
        compiler = compile_case("nested-own-final-input")
        path = 'rig.families["first"].leaves["nested"]'
        generated = compiler.model.occurrence_provenance[path]["generated"]
        self.assertEqual(generated["key"], "nested")
        self.assertEqual(generated["input_transforms"][0]["key"], "nested")
        self.assertEqual(generated["input_entry"], generated["input_transforms"][0]["input_entry"])
        self.assertEqual(compiler.field(path, "size").value, 0.5)

    def test_parameter_cache_replay_does_not_reuse_another_occurrences_provenance(self):
        text = '''ontokin "0.14";
module ParameterFlow @ "parameter-flow";
profile "keyed-transform-0.1";
public class Shape @ "shape" {
 public param width @ "width": Length = 0.5[m];
 public derive expanded @ "expanded": Length = self.width * 2;
 geometry = box(vec3(self.expanded, 1[m], 1[m]));
 physical = no_body();
}
scene Demo @ "demo" {
 duration = 1[s];
 gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
 object plain @ "plain": Shape {}
 object mapped @ "mapped": Shape {
  width = map_keyed<Length>(keyed<Length>{"input": 0.5[m]}, (k, v) -> v)["input"];
 }
}
'''
        compiler = compile_text(text)
        node = compiler.instances["plain"].cls.members["expanded"].node.value
        cls = compiler.instances["plain"].cls.name
        self.assertIn(("construction_parameters", id(node)), compiler.reach_work._cache)
        with patch.object(compiler, "_parameter_copy", wraps=compiler._parameter_copy) as copied:
            plain = compiler.expression(node, Context("plain", cls, cls))
            self.assertGreater(copied.call_count, 0)
        with patch.object(compiler, "_parameter_copy", wraps=compiler._parameter_copy) as copied:
            mapped = compiler.expression(node, Context("mapped", cls, cls))
            self.assertEqual(copied.call_count, 0)
        self.assertEqual(plain.value, mapped.value)
        self.assertEqual(compiler.transform_provenance(plain), [])
        self.assertEqual([row["key"] for row in compiler.transform_provenance(mapped)], ["input"])
        self.assertEqual(compiler.transform_provenance(compiler.field("plain", "width")), [])

    def test_repeated_direct_maps_pay_again_without_result_memoization(self):
        compiler = compile_case("singleton-length")
        node = compiler.instances["shape"].cls.members["result"].node.value
        previous = compiler.budget.report()
        values = []
        for _ in range(2):
            values.append(compiler.expression(node, context(compiler)))
            current = compiler.budget.report()
            self.assertGreater(current["operations"], previous["operations"])
            self.assertGreater(current["value_entries"], previous["value_entries"])
            previous = current
        self.assertIsNot(values[0], values[1])
        self.assertEqual(values[0], values[1])
        self.assertNotIn(("construction_parameters", id(node)), compiler.reach_work._cache)
        self.assertNotIn(("construction_constant", id(node), False), compiler.reach_work._cache)

    def test_actual_iteration_cancel_keeps_exception_identity_and_restores_stage(self):
        for failure in (RuntimeError("stop"), RecursionError("callback recursion"),
                        OntoKinError("OKL-E-UNIT", "callback identity")):
            with self.subTest(exception=type(failure).__name__):
                ledgers = []
                def cancel(ledger):
                    if ledger.stage == "keyed_transform_iteration":
                        ledgers.append(ledger)
                        raise failure
                with self.assertRaises(type(failure)) as caught:
                    compile_case("singleton-length", check=cancel)
                self.assertIs(caught.exception, failure)
                self.assertIs(ledgers[0].callback_error, failure)
                self.assertEqual(ledgers[0].stage, "execution")

    def test_caller_operation_cap_exhausts_the_same_ledger_during_map(self):
        visits = []
        compile_case("maximum-256", check=lambda ledger: visits.append(ledger.operations)
                     if ledger.stage == "keyed_transform_iteration" else None)
        self.assertEqual(len(visits), 256)
        cap = visits[8]
        partial = []
        with self.assertRaises(OntoKinError) as caught:
            compile_case("maximum-256", caller_caps={"max_operations": cap},
                         check=lambda ledger: partial.append(ledger.operations)
                         if ledger.stage == "keyed_transform_iteration" else None)
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
        self.assertGreater(len(partial), 0)
        self.assertLess(len(partial), 256)

    def test_value_materialization_limit_is_not_reset_by_map(self):
        with self.assertRaises(OntoKinError) as caught:
            compile_case("maximum-256", budgets={"max_value_entries": 100})
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(caught.exception.diagnostic.details["budget"], "max_value_entries")

    def test_imported_older_lazy_semantics_are_not_rewritten_by_new_caller(self):
        old = '''ontokin "0.13";
module Older @ "older";
profile "textured-surfaces-0.1";
public fn choose @ "choose"(v: Real, zero: Real) -> Real {
 return if true then v else v / zero;
}
'''
        unit = SourceUnit("package:older@1.0.0", "older.ok", old.encode(), "older", "1.0.0")
        imports = f'import older @ "older-import" from "older" version "1.0.0" digest "{unit.revision}";'
        text = program('map_keyed<Real>(keyed<Real>{"a": 1.0}, (k, v) -> older.choose(v, 0.0))',
                       typ="Real", imports=imports)
        with self.assertRaises(OntoKinError) as caught:
            compile_text(text, modules=(unit,))
        self.assertEqual(caught.exception.code, "OKL-E-NUMERIC")
        self.assertEqual(caught.exception.diagnostic.node.source_id, unit.source_id)
        new = program('map_keyed<Real>(keyed<Real>{"a": 1.0}, (k, v) -> choose(v, 0.0))', typ="Real",
                      before='public fn choose @ "choose"(v: Real, zero: Real) -> Real { return if true then v else v / zero; }')
        self.assertEqual(compile_text(new).field("shape", "result").value.lookup("a").value, 1.0)


if __name__ == "__main__":
    unittest.main()
