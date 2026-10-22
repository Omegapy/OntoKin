"""Constant folding preserves complete constructed models and request limits."""
from fractions import Fraction
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import ConstructionCompiler, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb
from ontokin.scene import ExportOptions
from ontokin.syntax import Node
from ontokin.validator import Context
from ontokin.values import INT, Value


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"


def build(case="P01"):
    return compile_construction(load_file_manifest(DATA / (case.lower() + ".files.json")),
                                level="constructed")


def number(text):
    return Node("number", 0, len(text), {"text": text}, "entry")


def vector(a="1", b="2", c="3"):
    return Node("call", 0, 1, {"callee": Node("name", 0, 1, {"name": "vec3"}, "entry"),
                               "args": [number(a), number(b), number(c)]}, "entry")


class ReachConstructionConstantTests(unittest.TestCase):
    def test_p23_complete_model_provenance_and_logical_values_equal_uncached(self):
        actual = build("P23")
        with patch.object(ConstructionCompiler, "_constant_names", return_value=None):
            expected = build("P23")
        self.assertEqual(actual.model, expected.model)
        self.assertEqual(actual.surface_meshes, expected.surface_meshes)
        self.assertEqual(actual.dependencies, expected.dependencies)
        self.assertEqual(actual.call_dependencies, expected.call_dependencies)
        self.assertEqual(actual.generated_dependencies, expected.generated_dependencies)
        self.assertEqual(actual.budget.value_entries, expected.budget.value_entries)
        self.assertEqual(actual.budget.limits, expected.budget.limits)
        self.assertLess(actual.budget.operations, expected.budget.operations)
        self.assertLessEqual(len(actual.reach_work._cache), 256)

    def test_complete_p01_output_is_byte_identical_to_uncached_construction(self):
        def artifact():
            compiler = build()
            return export_glb(compiler.model, options=ExportOptions(end=Fraction(3), fps=1, helpers=False),
                              target_contract="ontokin.glb/0.6", work=compiler.reach_work).data
        actual = artifact()
        with patch.object(ConstructionCompiler, "_constant_names", return_value=None):
            expected = artifact()
        self.assertEqual(actual, expected)

    def test_context_shadowing_does_not_reuse_a_builtin_result(self):
        compiler, node = build(), vector()
        expected = compiler.expression(node, Context())
        again = compiler.expression(node, Context())
        self.assertEqual(again, expected)
        self.assertIsNot(again, expected)
        with self.assertRaises(OntoKinError) as raised:
            compiler.expression(node, Context(locals={"vec3": Value(INT, 7)}))
        self.assertEqual(raised.exception.code, "OKL-E-TYPE")
        self.assertEqual(compiler.expression(node, Context()), expected)

    def test_abstract_and_concrete_values_have_separate_cache_entries(self):
        compiler, node = build(), vector()
        abstract = compiler.expression(node, Context(abstract=True))
        concrete = compiler.expression(node, Context())
        self.assertFalse(abstract.known)
        self.assertTrue(concrete.known)
        self.assertEqual(abstract.type, concrete.type)
        self.assertFalse(compiler.expression(node, Context(abstract=True)).known)

    def test_two_entry_eviction_recomputes_exact_values(self):
        compiler = build()
        compiler.reach_work._cache.clear()
        compiler.reach_work.max_cache_entries = 2
        first, second, third = vector(), vector("4"), vector("5")
        wanted = compiler.expression(first, Context())
        for node in (second, third, first):
            actual = compiler.expression(node, Context())
            self.assertLessEqual(len(compiler.reach_work._cache), 2)
        self.assertEqual(actual, wanted)
        self.assertGreater(compiler.reach_work.counts.get("cache_evict", 0), 0)

    def test_lowered_work_budget_fails_before_a_warm_result(self):
        compiler, node = build(), vector()
        compiler.expression(node, Context())
        compiler.budget.limits["max_operations"] = compiler.budget.operations
        before = tuple(compiler.reach_work._cache.items())
        with self.assertRaises(OntoKinError) as raised:
            compiler.expression(node, Context())
        self.assertEqual(raised.exception.diagnostic.details["budget"], "max_operations")
        self.assertEqual(tuple(compiler.reach_work._cache.items()), before)
        self.assertEqual(compiler._expression_depth, 0)

    def test_cancellation_on_each_warm_checkpoint_preserves_cache_and_depth(self):
        for cancel_at in range(1, 4):
            compiler, node = build(), vector()
            compiler.expression(node, Context())
            before = tuple(compiler.reach_work._cache.items())
            marker, calls = RuntimeError("cancel constant reuse"), 0
            def check():
                nonlocal calls
                calls += 1
                if calls == cancel_at:
                    raise marker
            compiler.budget.check = check
            with self.assertRaises(RuntimeError) as raised:
                compiler.expression(node, Context())
            self.assertIs(raised.exception, marker)
            self.assertEqual(tuple(compiler.reach_work._cache.items()), before)
            self.assertEqual(compiler._expression_depth, 0)

    def test_distinct_source_nodes_and_request_scopes_do_not_share_values(self):
        first, second = build(), build()
        one, two = vector("1"), vector("9")
        a = first.expression(one, Context())
        b = first.expression(two, Context())
        self.assertNotEqual(a, b)
        self.assertEqual(second.expression(one, Context()), a)
        self.assertIsNot(first.reach_work._cache, second.reach_work._cache)

    def test_warm_constant_cannot_bypass_nested_expression_depth_limit(self):
        compiler = build()
        node = Node("call", 0, 1, {
            "callee": Node("name", 0, 1, {"name": "abs"}, "entry"),
            "args": [number("1")]}, "entry")
        compiler.expression(node, Context())
        nested = node
        for _ in range(126):
            nested = Node("unary", 0, 1, {"op": "-", "value": nested}, "entry")
        self.assertEqual(compiler.expression(nested, Context()).value, 1)
        nested = Node("unary", 0, 1, {"op": "-", "value": nested}, "entry")
        with patch.object(ConstructionCompiler, "_constant_names", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.expression(nested, Context())
        self.assertEqual(expected.exception.code, "OKL-E-RESOURCE")
        with self.assertRaises(OntoKinError) as actual:
            compiler.expression(nested, Context())
        self.assertEqual(actual.exception.code, expected.exception.code)
        self.assertEqual(actual.exception.diagnostic.message, expected.exception.diagnostic.message)
        self.assertEqual(compiler._expression_depth, 0)


if __name__ == "__main__":
    unittest.main()
