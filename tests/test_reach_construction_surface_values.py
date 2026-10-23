"""Repeated surface leaves preserve occurrence reads, values and source origins."""
from dataclasses import replace
import copy
import json
import unittest
from unittest.mock import patch

from ontokin.construction import ConstructionCompiler, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.syntax import Node
from ontokin.validator import Context
from ontokin.values import INT, LENGTH, REAL, STRING, Value, quantity_type
from test_construction import bundle
from test_reach_construction_parameters import (
    binary, build as frozen_build, context as frozen_context, member,
)


SOURCE = '''ontokin "0.6";
module SurfaceReuse @ "surface-reuse";
profile "planar-reach-0.1";
class Segment @ "segment" {
    public param length @ "length": Length = 1[m];
    public param width @ "width": Length = 0.08[m];
    public param red @ "red": Real = 0.16;
    public param metallic @ "metallic": Real = 0.25;
    public param roughness @ "roughness": Real = 0.4;
    public param region @ "region": String = "shell";
    public derive palette @ "palette": Keyed<SurfaceMaterial> = keyed<SurfaceMaterial> {
        "shell": surface_material(rgba(self.red, 0.38, 0.68, 1), self.metallic, self.roughness)
    };
    public derive sections @ "sections": Keyed<LoftSection> = keyed<LoftSection> {
        "base": loft_section(0[m], vec3(0[m], 0[m], 0[m]), self.width, self.width * 0.75, self.region),
        "end": loft_section(self.length, vec3(0[m], 0[m], 0[m]), self.width * 0.65, self.width * 0.5, self.region)
    };
    geometry = loft(self.sections, self.palette, 16, "flat");
    physical = no_body();
}
scene Demo @ "demo" {
    duration = 3[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object first @ "first": Segment {}
    object second @ "second": Segment {}
}
'''


def build():
    return compile_construction(bundle(SOURCE), level="constructed")


def expression(compiler, name, path="first"):
    cls = compiler.instances[path].cls
    return cls.defaults[name][0], Context(path, cls.name, cls.name)


class ReachConstructionSurfaceValueTests(unittest.TestCase):
    def test_p23_exact_model_meshes_origins_and_values_match_without_surface_reuse(self):
        actual = frozen_build("P23")
        original = ConstructionCompiler._parameter_plan
        def scalar_only(compiler, node, depth=0):
            if (node.kind == "keyed" or node.kind == "name"
                    and node.name in {"loft_section", "surface_material"}
                    or node.kind == "call" and node.callee.kind == "name"
                    and node.callee.name in {"loft_section", "surface_material"}):
                return None
            return original(compiler, node, depth)
        with patch.object(ConstructionCompiler, "_parameter_plan", scalar_only):
            expected = frozen_build("P23")
        self.assertEqual(actual.model, expected.model)
        self.assertEqual(actual.surface_meshes, expected.surface_meshes)
        self.assertEqual(actual.dependencies, expected.dependencies)
        self.assertEqual(actual.call_dependencies, expected.call_dependencies)
        self.assertEqual(actual.generated_dependencies, expected.generated_dependencies)
        self.assertEqual(actual.budget.value_entries, expected.budget.value_entries)
        self.assertEqual(actual.budget.limits, expected.budget.limits)
        self.assertLess(actual.budget.operations, expected.budget.operations)
        self.assertLessEqual(len(actual.reach_work._cache), 256)
        print(json.dumps({"case_id": "P23", "constructed_operations": actual.budget.operations,
                          "without_surface_reuse_operations": expected.budget.operations,
                          "logical_value_entries": actual.budget.value_entries}))

    def test_warm_keyed_values_have_fresh_wrappers_payloads_and_origin_maps(self):
        compiler = build()
        node, ctx = expression(compiler, "palette")
        first = compiler.expression(node, ctx)
        second = compiler.expression(node, ctx)
        self.assertIn(("construction_parameters", id(node)), compiler.reach_work._cache)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first.value, second.value)
        self.assertIsNot(first.value.entries[0][1], second.value.entries[0][1])
        first_origins = compiler._keyed_origins[id(first.value)]
        second_origins = compiler._keyed_origins[id(second.value)]
        self.assertIsNot(first_origins, second_origins)
        first_origins.clear()
        self.assertIs(second_origins["shell"], node.entries[0])
        # Hostile mutation of a returned frozen wrapper must not reach either
        # another occurrence or the separately retained successful template.
        object.__setattr__(first.value.entries[0][1], "value", ("changed",))
        again = compiler.expression(node, ctx)
        self.assertEqual(again, second)
        self.assertIs(compiler._keyed_origins[id(again.value)]["shell"], node.entries[0])

    def test_changed_section_and_palette_parameters_recompute_exact_values(self):
        compiler = build()
        cases = (("sections", "width", Value(quantity_type(LENGTH), .12)),
                 ("sections", "length", Value(quantity_type(LENGTH), 1.5)),
                 ("sections", "region", Value(STRING, "trim")),
                 ("palette", "red", Value(REAL, .32)),
                 ("palette", "metallic", Value(REAL, .8)),
                 ("palette", "roughness", Value(REAL, .7)))
        for result_name, parameter, changed in cases:
            with self.subTest(parameter=parameter):
                node, ctx = expression(compiler, result_name)
                previous = compiler.expression(node, ctx)
                compiler.memo[(ctx.self_path, parameter)] = changed
                actual = compiler.expression(node, ctx)
                with patch.object(compiler, "_parameter_plan", return_value=None):
                    expected = compiler.expression(node, ctx)
                self.assertEqual(actual, expected)
                self.assertNotEqual(actual, previous)
        node, ctx = expression(compiler, "palette")
        compiler.memo[(ctx.self_path, "metallic")] = Value(REAL, 1.2)
        with self.assertRaises(OntoKinError) as actual:
            compiler.expression(node, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.expression(node, ctx)
        self.assertEqual(actual.exception.code, "OKL-E-SURFACE-MATERIAL")
        self.assertEqual(actual.exception.diagnostic.message, expected.exception.diagnostic.message)

    def test_early_changed_entry_fails_before_later_entry_parameter_reads(self):
        compiler = build()
        node, ctx = expression(compiler, "sections")
        compiler.expression(node, ctx)
        compiler.memo[(ctx.self_path, "width")] = Value(STRING, "wrong type")
        original, reads = compiler.member, []
        def observed(value, name, current, source):
            reads.append(name)
            if name == "length":
                raise AssertionError("Read a later entry before the first entry's type error")
            return original(value, name, current, source)
        with patch.object(compiler, "member", side_effect=observed):
            with self.assertRaises(OntoKinError) as actual:
                compiler.expression(node, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.expression(node, ctx)
        self.assertEqual(actual.exception.code, expected.exception.code)
        self.assertNotIn("length", reads)

    def test_occurrences_retain_dependency_routes_and_shadowed_names(self):
        compiler = build()
        node, first = expression(compiler, "sections")
        for path in ("first", "second"):
            _, ctx = expression(compiler, "sections", path)
            parent = (path, "test-sections")
            compiler.pending.append(parent)
            try:
                compiler.expression(node, ctx)
            finally:
                compiler.pending.pop()
            self.assertIn((path, "width"), compiler.dependencies[parent])
            self.assertIn((path, "length"), compiler.dependencies[parent])
            self.assertNotIn(("second" if path == "first" else "first", "width"),
                             compiler.dependencies[parent])
        for shadow in ("loft_section", "vec3"):
            with self.subTest(shadow=shadow):
                ctx = replace(first, locals={shadow: Value(INT, 1)})
                with self.assertRaises(OntoKinError) as actual:
                    compiler.expression(node, ctx)
                with patch.object(compiler, "_parameter_plan", return_value=None):
                    with self.assertRaises(OntoKinError) as expected:
                        compiler.expression(node, ctx)
                self.assertEqual(actual.exception.code, expected.exception.code)

    def test_invalid_keyed_inputs_keep_their_original_error_and_are_not_published(self):
        compiler = build()
        original, ctx = expression(compiler, "sections")
        for changed in ("duplicate", "invalid"):
            node = copy.deepcopy(original)
            node.entries[1].data["key"] = node.entries[0].key if changed == "duplicate" else "bad/key"
            with self.subTest(changed=changed):
                with self.assertRaises(OntoKinError) as actual:
                    compiler.expression(node, ctx)
                with patch.object(compiler, "_parameter_plan", return_value=None):
                    with self.assertRaises(OntoKinError) as expected:
                        compiler.expression(node, ctx)
                self.assertEqual(actual.exception.code, "OKL-E-ID")
                self.assertEqual(actual.exception.diagnostic.message, expected.exception.diagnostic.message)
                self.assertNotIn(("construction_parameters", id(node)), compiler.reach_work._cache)
                self.assertIsNone(compiler._parameter_capture)

    def test_changed_keys_and_entry_membership_cannot_reuse_an_old_keyed_value(self):
        compiler = build()
        original, ctx = expression(compiler, "palette")
        node = copy.deepcopy(original)
        first = compiler.expression(node, ctx)
        node.entries[0].data["key"] = "coat"
        actual = compiler.expression(node, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            expected = compiler.expression(node, ctx)
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, first)
        node.entries.append(copy.deepcopy(node.entries[0]))
        with self.assertRaises(OntoKinError) as actual:
            compiler.expression(node, ctx)
        with patch.object(compiler, "_parameter_plan", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.expression(node, ctx)
        self.assertEqual(actual.exception.code, "OKL-E-ID")
        self.assertEqual(actual.exception.diagnostic.message, expected.exception.diagnostic.message)

    def test_every_warm_keyed_value_is_logically_charged_and_cancellable(self):
        compiler = frozen_build()
        ctx = frozen_context(compiler)
        node = compiler.instances[ctx.self_path].cls.defaults["palette"][0]
        compiler.expression(node, ctx)
        before = compiler.budget.value_entries
        compiler.expression(node, ctx)
        logical_entries = compiler.budget.value_entries - before
        self.assertGreater(logical_entries, 0)
        compiler.budget.limits["max_value_entries"] = compiler.budget.value_entries + logical_entries - 1
        with self.assertRaises(OntoKinError) as raised:
            compiler.expression(node, ctx)
        self.assertEqual(raised.exception.diagnostic.details["budget"], "max_value_entries")
        compiler.budget.limits["max_value_entries"] = 100000
        marker = RuntimeError("cancel keyed logical unfolding")
        origins_before = dict(compiler._keyed_origins)
        with patch.object(compiler.budget, "charge_value", side_effect=marker):
            with self.assertRaises(RuntimeError) as raised:
                compiler.expression(node, ctx)
        self.assertIs(raised.exception, marker)
        self.assertEqual(compiler._keyed_origins, origins_before)
        self.assertEqual(compiler._expression_depth, 0)
        self.assertIsNone(compiler._parameter_capture)

    def test_tiny_cache_eviction_rebuilds_independent_surface_values(self):
        compiler = build()
        compiler.reach_work._cache.clear()
        compiler.reach_work.max_cache_entries = 1
        sections, ctx = expression(compiler, "sections")
        palette, _ = expression(compiler, "palette")
        expected = compiler.expression(sections, ctx)
        compiler.expression(palette, ctx)
        actual = compiler.expression(sections, ctx)
        self.assertEqual(actual, expected)
        self.assertIsNot(actual.value, expected.value)
        self.assertEqual(len(compiler.reach_work._cache), 1)

    def test_constant_subtrees_do_not_admit_short_circuit_parameter_expressions(self):
        compiler = build()
        _, ctx = expression(compiler, "sections")
        truth = lambda: Node("bool", 0, 1, {"value": True}, "entry")
        node = binary("==", binary("==", member("width"), member("width")),
                      binary("and", truth(), truth()))
        self.assertTrue(compiler.expression(node, ctx).value)
        self.assertNotIn(("construction_parameters", id(node)), compiler.reach_work._cache)


if __name__ == "__main__":
    unittest.main()
