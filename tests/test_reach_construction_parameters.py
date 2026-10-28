"""Repeated scalar formulas keep occurrence reads and exact native results."""
from dataclasses import replace
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
from ontokin.values import INT, LENGTH, Type, Value, quantity_type


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"


def build(case="P01"):
    return compile_construction(load_file_manifest(DATA / (case.lower() + ".files.json")),
                                level="constructed")


def number(text):
    return Node("number", 0, len(text), {"text": text}, "entry")


def member(name):
    return Node("member", 0, 1, {"target": Node("name", 0, 1, {"name": "self"}, "entry"),
                               "name": name}, "entry")


def binary(op, left, right):
    return Node("binary", 0, 1, {"op": op, "left": left, "right": right}, "entry")


def call(name, *args):
    return Node("call", 0, 1, {"callee": Node("name", 0, 1, {"name": name}, "entry"),
                              "args": list(args)}, "entry")


def context(compiler, path="rig.arm.upper"):
    cls = compiler.instances[path].cls
    return Context(path, cls.name, cls.name)


def parameter_keys(compiler):
    return {key for key in compiler.reach_work._cache if key[0] == "construction_parameters"}


class ReachConstructionParameterTests(unittest.TestCase):
    def test_p23_complete_models_dependencies_meshes_and_logical_values_match(self):
        actual = build("P23")
        with patch.object(ConstructionCompiler, "_parameter_plan", return_value=None):
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

    def test_complete_p01_artifact_matches_ordinary_construction(self):
        def artifact():
            compiler = build()
            return export_glb(compiler.model,
                options=ExportOptions(end=Fraction(3), fps=1, helpers=False),
                target_contract="ontokin.glb/0.6", work=compiler.reach_work).data
        actual = artifact()
        with patch.object(ConstructionCompiler, "_parameter_plan", return_value=None):
            expected = artifact()
        self.assertEqual(actual, expected)

    def test_warm_result_replays_reads_and_returns_a_fresh_wrapper(self):
        compiler = build()
        ctx = context(compiler)
        node = binary("*", member("width"), number("0.75"))
        first = compiler.expression(node, ctx)
        self.assertIn(("construction_parameters", id(node)), parameter_keys(compiler))
        reads = []
        original = compiler.member
        def observed(value, name, current, source):
            reads.append((name, current.self_path))
            return original(value, name, current, source)
        with patch.object(compiler, "member", side_effect=observed):
            again = compiler.expression(node, ctx)
        self.assertEqual(again, first)
        self.assertIsNot(again, first)
        self.assertEqual(reads, [("width", ctx.self_path)])

    def test_changed_value_and_native_type_use_ordinary_arithmetic(self):
        compiler = build()
        ctx = context(compiler)
        node = binary("*", member("width"), number("0.75"))
        first = compiler.expression(node, ctx)
        compiler.memo[(ctx.self_path, "width")] = Value(quantity_type(LENGTH), .125)
        actual = compiler.expression(node, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            expected = compiler.expression(node, ctx)
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, first)
        compiler.memo[(ctx.self_path, "width")] = Value(Type("String"), "different")
        with self.assertRaises(OntoKinError) as actual:
            compiler.expression(node, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.expression(node, ctx)
        self.assertEqual(actual.exception.code, expected.exception.code)
        self.assertEqual(actual.exception.diagnostic.message, expected.exception.diagnostic.message)

    def test_first_changed_parameter_falls_back_before_later_read(self):
        compiler = build()
        ctx = context(compiler)
        node = binary("+", binary("/", number("1"), member("width")),
                      binary("/", number("1"), member("length")))
        compiler.expression(node, ctx)
        compiler.memo[(ctx.self_path, "width")] = Value(quantity_type(LENGTH), 0.)
        original = compiler.member
        seen = []
        def observed(value, name, current, source):
            seen.append(name)
            if name == "length":
                raise AssertionError("Read past the earlier division-by-zero failure")
            return original(value, name, current, source)
        with patch.object(compiler, "member", side_effect=observed):
            with self.assertRaises(OntoKinError) as actual:
                compiler.expression(node, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.expression(node, ctx)
        self.assertEqual(actual.exception.code, expected.exception.code)
        self.assertNotIn("length", seen)

    def test_every_occurrence_retains_its_dependency_route(self):
        compiler = build()
        node = binary("*", member("width"), number("0.75"))
        for path in ("rig.arm.upper", "rig.arm.forearm"):
            ctx = context(compiler, path)
            parent = (path, "test-result")
            compiler.pending.append(parent)
            try:
                compiler.expression(node, ctx)
            finally:
                compiler.pending.pop()
            self.assertIn((path, "width"), compiler.dependencies[parent])

    def test_warm_parameter_replays_dependency_cycle_and_shape_guards(self):
        compiler = build()
        ctx = context(compiler)
        node = binary("*", member("width"), number("0.75"))
        compiler.expression(node, ctx)
        key = (ctx.self_path, "width")
        saved = compiler.memo.pop(key)
        compiler.pending.append(key)
        try:
            with self.assertRaises(OntoKinError) as raised:
                compiler.expression(node, ctx)
            self.assertEqual(raised.exception.code, "OKL-E-DEPENDENCY-CYCLE")
        finally:
            compiler.pending.pop()
            compiler.memo[key] = saved
        compiler.generated_dependencies[key] = {"rig.forbidden_collection"}
        compiler._shape_stack.append(ctx.self_path)
        try:
            with self.assertRaises(OntoKinError) as raised:
                compiler.expression(node, ctx)
            self.assertEqual(raised.exception.code, "OKL-E-DEPENDENCY-CYCLE")
            self.assertEqual(raised.exception.diagnostic.details["generated_dependency"],
                             "rig.forbidden_collection")
        finally:
            compiler._shape_stack.pop()

    def test_revoked_access_and_shadowed_constructor_remain_visible(self):
        compiler = build()
        ctx = context(compiler)
        node = call("min", member("width"), member("length"))
        compiler.expression(node, ctx)
        with self.assertRaises(OntoKinError) as raised:
            compiler.expression(node, replace(ctx, locals={"min": Value(INT, 7)}))
        self.assertEqual(raised.exception.code, "OKL-E-TYPE")
        declaration = compiler.instances[ctx.self_path].cls.members["width"].node
        old = declaration.data["visibility"]
        declaration.data["visibility"] = "private"
        try:
            with self.assertRaises(OntoKinError) as raised:
                compiler.expression(node, replace(ctx, lexical_class=None))
            self.assertEqual(raised.exception.code, "OKL-E-ACCESS")
        finally:
            declaration.data["visibility"] = old

    def test_mutable_derived_and_short_circuit_inputs_are_not_retained(self):
        compiler = build()
        ctx = context(compiler)
        nodes = [call("min", member("sections"), member("sections")),
                 binary("and", Node("bool", 0, 1, {"value": False}, "entry"),
                        binary("==", member("width"), member("length"))),
                 Node("conditional", 0, 1, {
                     "condition": Node("bool", 0, 1, {"value": True}, "entry"),
                     "then": member("width"), "otherwise": member("length")}, "entry")]
        for node in nodes:
            try:
                compiler.expression(node, ctx)
            except OntoKinError:
                pass
            self.assertNotIn(("construction_parameters", id(node)), parameter_keys(compiler))

    def test_eviction_and_lowered_budget_preserve_results_and_limits(self):
        compiler = build()
        ctx = context(compiler)
        compiler.reach_work._cache.clear()
        compiler.reach_work.max_cache_entries = 2
        nodes = [binary("*", member("width"), number(value)) for value in ("0.5", "0.75", "0.25")]
        first = compiler.expression(nodes[0], ctx)
        for node in (*nodes[1:], nodes[0]):
            actual = compiler.expression(node, ctx)
            self.assertLessEqual(len(compiler.reach_work._cache), 2)
        self.assertEqual(actual, first)
        compiler.budget.limits["max_operations"] = compiler.budget.operations
        before = tuple(compiler.reach_work._cache.items())
        with self.assertRaises(OntoKinError) as raised:
            compiler.expression(nodes[0], ctx)
        self.assertEqual(raised.exception.diagnostic.details["budget"], "max_operations")
        self.assertEqual(tuple(compiler.reach_work._cache.items()), before)
        self.assertEqual(compiler._expression_depth, 0)
        self.assertIsNone(compiler._parameter_capture)

    def test_cancellation_on_warm_reads_preserves_exception_identity(self):
        for cancel_at in range(1, 6):
            compiler = build()
            ctx = context(compiler)
            node = call("min", member("width"), member("length"))
            compiler.expression(node, ctx)
            marker, calls = RuntimeError("cancel repeated parameter expression"), 0
            def check():
                nonlocal calls
                calls += 1
                if calls == cancel_at:
                    raise marker
            compiler.budget.check = check
            with self.assertRaises(RuntimeError) as raised:
                compiler.expression(node, ctx)
            self.assertIs(raised.exception, marker)
            self.assertEqual(compiler._expression_depth, 0)
            self.assertIsNone(compiler._parameter_capture)

    def test_cancelled_first_publication_retains_no_parameter_result(self):
        compiler = build()
        ctx = context(compiler)
        node = binary("*", member("width"), number("0.75"))
        before = tuple(compiler.reach_work._cache.items())
        marker = RuntimeError("cancel parameter result publication")
        original = compiler.reach_work.charge
        def charged(kind="checkpoint", amount=1):
            if kind == "cache_insert":
                compiler.budget.check = lambda: (_ for _ in ()).throw(marker)
            return original(kind, amount)
        with patch.object(compiler.reach_work, "charge", side_effect=charged):
            with self.assertRaises(RuntimeError) as raised:
                compiler.expression(node, ctx)
        self.assertIs(raised.exception, marker)
        self.assertEqual(tuple(compiler.reach_work._cache.items()), before)
        self.assertEqual(compiler._expression_depth, 0)
        self.assertIsNone(compiler._parameter_capture)

    def test_warm_expression_cannot_bypass_nested_depth_limit(self):
        compiler = build()
        ctx = context(compiler)
        node = binary("*", member("width"), number("0.75"))
        compiler.expression(node, ctx)
        nested = node
        for _ in range(126):
            nested = Node("unary", 0, 1, {"op": "-", "value": nested}, "entry")
        with self.assertRaises(OntoKinError) as actual:
            compiler.expression(nested, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.expression(nested, ctx)
        self.assertEqual(actual.exception.code, expected.exception.code)
        self.assertEqual(actual.exception.diagnostic.message, expected.exception.diagnostic.message)


if __name__ == "__main__":
    unittest.main()
