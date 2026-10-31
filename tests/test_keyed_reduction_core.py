"""Frozen reduction results and observable sequential construction behavior."""
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import SourceUnit
from ontokin.construction import ConstructionCompiler, ConstructionBudget, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import HostPolicy, SharedExecutionBudget, admit_entry_budget
from ontokin.profile_capabilities import KEYED_REDUCTION_PROFILE, KEYED_TRANSFORM_PROFILE
from ontokin.texture_bundle import TextureBundle, load_texture_file_manifest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/keyed-reduction"
CASES = json.loads((FIXTURES / "expected.json").read_bytes())["cases"]


def compile_bundle(bundle, *, policy=None, caller_caps=None, check=None, budgets=None):
    ledger = SharedExecutionBudget(policy, caller_caps=caller_caps)
    if check is not None:
        ledger.check = lambda: check(ledger)
    profile = (KEYED_TRANSFORM_PROFILE if 'profile "keyed-transform-0.1";' in bundle.entry.text
               else KEYED_REDUCTION_PROFILE)
    admit_entry_budget(bundle.entry, ledger, profile=profile)
    return compile_construction(bundle, execution_budget=ledger, budgets=budgets)


def compile_case(name, **kwargs):
    case = next(c for c in CASES if c["name"] == name)
    bundle = load_texture_file_manifest(FIXTURES / case["file_manifest"])
    return compile_bundle(bundle, policy=HostPolicy(**case["host_policy"]), **kwargs)


def program(expression, *, typ="Int", before="", members="", geometry=None):
    if geometry is None:
        geometry = 'if self.result >= 0 then box(vec3(1[m], 1[m], 1[m])) else empty()'
    return f'''ontokin "0.15";
module Core @ "core";
profile "keyed-reduction-0.1";
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


def compile_text(text, **kwargs):
    return compile_bundle(TextureBundle(SourceUnit("entry", "main.ok", text.encode()), ()), **kwargs)


class KeyedReductionCoreTests(unittest.TestCase):
    def test_frozen_inputs_and_all_expected_source_outcomes(self):
        freeze_path = ROOT / "docs/language-design/keyed-reduction-v0.1/INPUT-FREEZE.json"
        self.assertEqual(hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
                         "537571b07f8f0192180fb5f15bb9537d16f13e4f5796c6e9bee10b4ed93d959b")
        for record in json.loads(freeze_path.read_bytes())["files"]:
            data = (ROOT / record["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"], record["path"])
        for case in CASES:
            with self.subTest(case=case["name"]):
                if case["expected_outcome"] == "invalid":
                    with self.assertRaises(OntoKinError) as caught:
                        compile_case(case["name"])
                    self.assertEqual(caught.exception.code, case["expected_code"])
                    continue
                compiler = compile_case(case["name"])
                probe = case.get("probe")
                if probe:
                    actual = compiler.field(probe["object_path"], probe["member"])
                    if "scalar_value" in probe:
                        self.assertEqual(actual.value, probe["scalar_value"])
                    reductions = compiler.reduction_provenance(actual)
                    locations = {(r["expression"]["source_id"], r["expression"]["start_byte"],
                                  r["expression"]["end_byte"]) for r in reductions}
                    for expected in probe["required_reduction_expressions"]:
                        self.assertIn((expected["source_id"], expected["start_byte"], expected["end_byte"]), locations)
                    self.assertEqual(bool(reductions), probe["reduction_required"])

    def test_input_seed_order_body_count_and_every_required_copy(self):
        expression = ConstructionCompiler.expression
        charge = ConstructionBudget.charge_value
        for entries, expected in [('"z": 2, "A": 1', [("A", 10, 1), ("z", 11, 2)]), ("", [])]:
            with self.subTest(entries=entries):
                scope, evaluations, copies = [], [], []
                def observed(compiler, node, ctx):
                    root = node.kind == "reduce_keyed" and not ctx.abstract
                    if root:
                        scope.append(node)
                    try:
                        if scope and not ctx.abstract:
                            active = scope[-1]
                            for label in ("input", "seed", "body"):
                                if node is getattr(active, label):
                                    if label == "body":
                                        evaluations.append((label, ctx.locals[active.key_name].value,
                                            ctx.locals[active.accumulator_name].value,
                                            ctx.locals[active.value_name].value))
                                    else:
                                        evaluations.append((label,))
                        return expression(compiler, node, ctx)
                    finally:
                        if root:
                            scope.pop()
                def charged(budget, value, node=None):
                    if scope:
                        active = scope[-1]
                        labels = [("initial", active.seed), ("key", active.key_node),
                                  ("value", active.value_node), ("accumulator", active.accumulator_node),
                                  ("next", active.body), ("final", active)]
                        for label, origin in labels:
                            if node is origin:
                                copies.append((label, value))
                    return charge(budget, value, node)
                with patch.object(ConstructionCompiler, "expression", observed), patch.object(ConstructionBudget, "charge_value", charged):
                    compiler = compile_text(program(f'reduce_keyed<Int>(keyed<Int>{{{entries}}}, 10, (acc, k, v) -> acc + v)'))
                self.assertEqual(evaluations, [("input",), ("seed",)] + [("body", *row) for row in expected])
                self.assertEqual([name for name, _ in copies], ["initial"] + [name for _ in expected for name in ("key", "value", "accumulator", "next")] + ["final"])
                self.assertEqual(len({id(value) for _, value in copies}), len(copies))
                self.assertEqual(compiler.field("shape", "result").value, 13 if expected else 10)

    def test_nonkeyed_input_refuses_before_dynamic_seed(self):
        expression = ConstructionCompiler.expression
        seed_calls = []
        def observed(compiler, node, ctx):
            if not ctx.abstract and node.kind == "binary" and node.op == "/":
                seed_calls.append(node)
            return expression(compiler, node, ctx)
        with patch.object(ConstructionCompiler, "expression", observed):
            with self.assertRaises(OntoKinError) as caught:
                compile_text(program('reduce_keyed<Real>(42, 1.0 / 0.0, (acc, k, v) -> acc)', typ="Real"))
        self.assertEqual(caught.exception.code, "OKL-E-TYPE")
        self.assertEqual(seed_calls, [])

    def test_map_leaf_retains_discarded_input_reduction_for_generated_occurrence(self):
        text = program('0', members='''
 public parts children @ "children": Child for (child_key, child_value) in
 map_keyed<Length>(keyed<Length>{"x": reduce_keyed<Length>(keyed<Length>{"a": 1[m]}, 0[m], (acc, k, v) -> acc + v)}, (mk, mv) -> 1[m])
 { size = child_value; }
''', before='''public class Child @ "child" {
 public param size @ "size": Length = 1[m];
 geometry = sphere(self.size);
 physical = no_body();
}''')
        compiler = compile_text(text)
        generated = compiler.model.occurrence_provenance['shape.children["x"]']["generated"]
        self.assertEqual(len(generated["input_reductions"]), 1)
        self.assertTrue(generated["input_transforms"])

    def test_reduction_provenance_does_not_mutate_shared_keyed_payload(self):
        text = program('0', members='''
 public param plain @ "plain": Keyed<Int> = keyed<Int>{"x": 1};
 public derive chosen @ "chosen": Keyed<Int> = if reduce_keyed<Int>(keyed<Int>{"a": 1}, 0, (acc, k, v) -> acc + v) == 1 then self.plain else self.plain;
''')
        compiler = compile_text(text)
        chosen = compiler.field("shape", "chosen")
        plain = compiler.field("shape", "plain")
        self.assertTrue(compiler.reduction_provenance(chosen))
        self.assertEqual(compiler.reduction_provenance(plain), [])

    def test_generated_input_condition_retains_reduction_origin(self):
        text = program('0', members='''
 public param plain @ "plain": Keyed<Length> = keyed<Length>{"x": 1[m]};
 public parts children @ "children": Child for (child_key, child_value) in
 (if reduce_keyed<Int>(keyed<Int>{"a": 1}, 0, (acc, k, v) -> acc + v) == 1 then self.plain else self.plain)
 { size = child_value; }
''', before='''public class Child @ "child" {
 public param size @ "size": Length = 1[m];
 geometry = sphere(self.size);
 physical = no_body();
}''')
        compiler = compile_text(text)
        generated = compiler.model.occurrence_provenance['shape.children["x"]']["generated"]
        self.assertEqual(len(generated["input_reductions"]), 1)

    def test_actual_iteration_cancellation_preserves_exception_identity(self):
        sentinel = RuntimeError("cancel exactly in reduction iteration")
        stages = []
        def cancel(ledger):
            if ledger.stage == "keyed_reduction_iteration":
                stages.append(ledger.stage)
                raise sentinel
        with self.assertRaises(RuntimeError) as caught:
            compile_case("singleton-length", check=cancel)
        self.assertIs(caught.exception, sentinel)
        self.assertEqual(stages, ["keyed_reduction_iteration"])

    def test_current_caller_operation_cap_stays_cumulative(self):
        with self.assertRaises(OntoKinError) as caught:
            compile_case("maximum-256", caller_caps={"max_operations": 100})
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")


if __name__ == "__main__":
    unittest.main()
