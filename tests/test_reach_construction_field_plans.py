"""Source field routes never stand in for occurrence values or validation."""
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
from ontokin.syntax02 import PathStep


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"
FIELDS = {"pose", "interface", "size"}


def build(case="P01"):
    return compile_construction(load_file_manifest(DATA / (case.lower() + ".files.json")),
                                level="constructed")


def site(names=("pose", "interface", "size")):
    rows = [Node("assign", 10 + index, 20 + index,
                 {"path": (PathStep("member", name, 10 + index, 20 + index),),
                  "value": Node("number", 30 + index, 31 + index, {"text": "1"}, "entry")}, "entry")
            for index, name in enumerate(names)]
    return Node("site", 0, 40, {"assignments": rows}, "entry")


def signature(error):
    d = error.diagnostic
    return error.code, d.message, d.phase, d.node.source_id, d.node.start, d.node.end


class ReachConstructionFieldPlanTests(unittest.TestCase):
    def test_original_p23_model_dependencies_and_logical_values_match(self):
        actual = build("P23")
        with patch.object(ConstructionCompiler, "_assignment_shape", return_value=None):
            expected = build("P23")
        self.assertEqual(actual.model, expected.model)
        self.assertEqual(actual.surface_meshes, expected.surface_meshes)
        for name in ("dependencies", "call_dependencies", "generated_dependencies"):
            self.assertEqual(getattr(actual, name), getattr(expected, name))
        self.assertEqual(actual.budget.value_entries, expected.budget.value_entries)
        self.assertEqual(actual.budget.limits, expected.budget.limits)
        self.assertLess(actual.budget.operations, expected.budget.operations)
        self.assertLessEqual(len(actual._assignment_syntax), 64)
        self.assertLessEqual(len(actual.reach_work._cache), 256)

    def test_complete_original_p01_bytes_match_original_field_validation(self):
        def artifact():
            compiler = build()
            return export_glb(compiler.model,
                options=ExportOptions(end=Fraction(3), fps=1, helpers=False),
                target_contract="ontokin.glb/0.6", work=compiler.reach_work).data
        actual = artifact()
        with patch.object(ConstructionCompiler, "_assignment_shape", return_value=None):
            expected = artifact()
        self.assertEqual(actual, expected)

    def test_warm_routing_returns_fresh_map_and_live_source_expressions(self):
        compiler, node = build(), site()
        first = compiler.assignments(node, FIELDS)
        start = compiler.budget.operations
        again = compiler.assignments(node, FIELDS)
        self.assertEqual(compiler.budget.operations - start, 1)
        self.assertEqual(first, again)
        self.assertIsNot(first, again)
        again.clear()
        replacement = Node("string", 30, 31, {"value": "changed"}, "entry")
        node.assignments[0].data["value"] = replacement
        current = compiler.assignments(node, FIELDS)
        self.assertIs(current["pose"], node.assignments[0])
        self.assertIs(current["pose"].value, replacement)

    def test_invalid_duplicate_unknown_and_missing_fields_keep_original_errors(self):
        compiler = build()
        for names in (("pose", "pose", "size"), ("pose", "unknown", "size"), ("pose", "size")):
            node = site(names)
            with self.subTest(names=names):
                with self.assertRaises(OntoKinError) as actual:
                    compiler.assignments(node, FIELDS)
                with patch.object(compiler, "_assignment_shape", return_value=None):
                    with self.assertRaises(OntoKinError) as expected:
                        compiler.assignments(node, FIELDS)
                self.assertEqual(signature(actual.exception), signature(expected.exception))

    def test_different_required_set_cannot_use_warm_route(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, {"pose", "size"})
        with patch.object(compiler, "_assignment_shape", return_value=None):
            with self.assertRaises(OntoKinError) as expected:
                compiler.assignments(node, {"pose", "size"})
        self.assertEqual(signature(actual.exception), signature(expected.exception))

    def test_reordered_and_replaced_source_rows_are_revalidated(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        node.assignments.reverse()
        start = compiler.budget.operations
        result = compiler.assignments(node, FIELDS)
        self.assertEqual(compiler.budget.operations - start, 3)
        self.assertEqual(list(result), ["size", "interface", "pose"])
        node.data["assignments"] = site(("pose", "pose", "size")).assignments
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, FIELDS)
        self.assertIn("assigned twice", actual.exception.diagnostic.message)

    def test_changed_native_path_field_cannot_hide_behind_owner_identity(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        object.__setattr__(node.assignments[0].path[0], "value", "bad")
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, FIELDS)
        self.assertIn("Allowed site fields", actual.exception.diagnostic.message)

    def test_direct_assignment_attribute_shadow_keeps_original_failure(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        node.assignments = site(("bad",)).assignments
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, FIELDS)
        self.assertIn("Allowed site fields", actual.exception.diagnostic.message)

    def test_direct_path_attribute_shadow_keeps_original_failure(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        node.assignments[0].path = (PathStep("member", "bad", 10, 20),)
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, FIELDS)
        self.assertIn("Allowed site fields", actual.exception.diagnostic.message)

    def test_callback_assignment_shadow_finishes_original_iterator_then_rejects_next_call(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        original, calls = list(node.assignments), []
        def callback():
            calls.append(None)
            if len(calls) == 1:
                node.assignments = site(("bad",)).assignments
        compiler.budget.check = callback
        result = compiler.assignments(node, FIELDS)
        self.assertEqual(list(result.values()), original)
        self.assertEqual(len(calls), 3)
        compiler.budget.check = None
        with self.assertRaises(OntoKinError):
            compiler.assignments(node, FIELDS)

    def test_callback_path_shadow_fails_before_later_restoring_callback(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        first, calls = node.assignments[0], []
        def callback():
            calls.append(None)
            first.path = (PathStep("member", "bad" if len(calls) == 1 else "pose", 10, 20),)
        compiler.budget.check = callback
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, FIELDS)
        self.assertEqual(len(calls), 1)
        self.assertIn("Allowed site fields", actual.exception.diagnostic.message)

    def test_callback_first_field_failure_precedes_a_restoring_second_callback(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        step, calls = node.assignments[0].path[0], []
        def callback():
            calls.append(None)
            object.__setattr__(step, "value", "bad" if len(calls) == 1 else "pose")
        compiler.budget.check = callback
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, FIELDS)
        self.assertEqual(len(calls), 1)
        self.assertIn("Allowed site fields", actual.exception.diagnostic.message)

    def test_callback_replacing_assignment_list_keeps_original_live_iterator(self):
        compiler, node = build(), site()
        original = list(node.assignments)
        compiler.assignments(node, FIELDS)
        calls = []
        def callback():
            calls.append(None)
            if len(calls) == 1:
                node.data["assignments"] = site(("bad",)).assignments
        compiler.budget.check = callback
        result = compiler.assignments(node, FIELDS)
        self.assertEqual(len(calls), 3)
        self.assertEqual(list(result.values()), original)
        self.assertEqual(node.assignments[0].path[0].value, "bad")

    def test_later_original_callback_can_repair_its_own_field(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        step, calls = node.assignments[1].path[0], []
        def callback():
            calls.append(None)
            object.__setattr__(step, "value", "bad" if len(calls) == 1 else "interface")
        compiler.budget.check = callback
        result = compiler.assignments(node, FIELDS)
        self.assertEqual(set(result), FIELDS)
        self.assertEqual(len(calls), 3)

    def test_original_callback_exception_identity_is_preserved(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        for cls in (RuntimeError, TypeError, KeyError, AttributeError):
            sentinel = cls("caller refusal")
            def callback():
                raise sentinel
            compiler.budget.check = callback
            with self.assertRaises(cls) as actual:
                compiler.assignments(node, FIELDS)
            self.assertIs(actual.exception, sentinel)
            self.assertIs(compiler.budget.callback_error, sentinel)

    def test_lowered_work_limit_retains_original_first_source_span(self):
        compiler, node = build(), site()
        compiler.assignments(node, FIELDS)
        compiler.budget.limits["max_operations"] = compiler.budget.operations
        with self.assertRaises(OntoKinError) as actual:
            compiler.assignments(node, FIELDS)
        d = actual.exception.diagnostic
        self.assertEqual(actual.exception.code, "OKL-E-RESOURCE")
        self.assertIs(d.node, node.assignments[0])

    def test_source_plan_table_is_bounded_and_legacy_path_is_unchanged(self):
        compiler = build()
        compiler._assignment_syntax.clear()
        retained = [site() for _ in range(70)]
        for node in retained:
            self.assertEqual(set(compiler.assignments(node, FIELDS)), FIELDS)
        self.assertEqual(len(compiler._assignment_syntax), 64)
        node = retained[-1]
        start = compiler.budget.operations
        compiler.assignments(node, FIELDS)
        self.assertEqual(compiler.budget.operations - start, 3)
        compiler.reach_work = None
        start = compiler.budget.operations
        compiler.assignments(retained[0], FIELDS)
        self.assertEqual(compiler.budget.operations - start, 3)

    def test_string_paths_and_unsupported_large_field_sets_keep_original_path(self):
        compiler, node = build(), site()
        for row in node.assignments:
            row.data["path"] = (row.path[0].value,)
        self.assertEqual(set(compiler.assignments(node, FIELDS)), FIELDS)
        self.assertNotIn(id(node), compiler._assignment_syntax)
        names = tuple("field" + str(n) for n in range(9))
        wide = site(names)
        self.assertEqual(set(compiler.assignments(wide, set(names))), set(names))
        self.assertNotIn(id(wide), compiler._assignment_syntax)


if __name__ == "__main__":
    unittest.main()
