"""Independent source contracts beyond the published validation corpus.

These examples exercise LANG-003/005/007/008/009/010/011 directly. Expected
results are source assertions or stable diagnostic codes, not model internals.
"""

import unittest

from ontokin.diagnostics import OntoKinError, Source
from ontokin.syntax import parse
from ontokin.validator import validate


def program(definitions="", scene="", *, settings=None):
    if settings is None:
        settings = """
            duration = 1[s];
            gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
        """
    return f'''ontokin "0.1";
module Contract @ "contract";
profile "core-0.1";
{definitions}
scene Demo @ "demo" {{ {settings} {scene} }}
'''


class ValidatorEdgeTests(unittest.TestCase):
    def accept(self, source, *, level="represented"):
        return validate(parse(source), level=level)

    def reject(self, source, code, *, category=None, level="represented"):
        with self.assertRaises(OntoKinError) as caught:
            self.accept(source, level=level)
        self.assertEqual(caught.exception.code, code)
        if category is not None:
            self.assertEqual(caught.exception.diagnostic.category, category)
        return caught.exception.diagnostic

    def test_unused_branches_are_typed_but_not_evaluated(self):
        self.accept(program(scene='''
            assert (if true then 2.0 else 1.0 / 0.0) == 2.0, "unused divide";
            assert true or (1.0 / 0.0 > 0), "short circuit";
            assert not (false and (1.0 / 0.0 > 0)), "short circuit";
        '''))
        for expression in ['if true then 2.0 else "wrong"',
                           'true or 4', 'false and "wrong"']:
            with self.subTest(expression=expression):
                self.reject(program(scene=f'assert {expression}, "bad branch";'),
                            "OKL-E-TYPE")

    def test_scene_fields_validate_unused_branch_units(self):
        source = program(settings='''
            duration = if true then 1[s] else 2[m];
            gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
        ''')
        self.reject(source, "OKL-E-UNIT")

    def test_unused_callable_has_a_checked_return_type(self):
        self.reject(program('''
            fn broken @ "broken"() -> Length { return "wrong"; }
        '''), "OKL-E-UNIT")

    def test_unused_class_initializers_are_type_checked(self):
        self.reject(program('''
            class Unused @ "unused" {
                public part child @ "child": Object { role = 1; }
            }
        '''), "OKL-E-TYPE")

    def test_private_members_keep_their_declaring_scope(self):
        base = '''
            class Base @ "base" {
                private param secret @ "secret": Int = 7;
                public method read @ "read"() -> Int { return self.secret; }
            }
        '''
        self.accept(program(base + 'class Child @ "child" extends Base {}', '''
            object value @ "value": Child {}
            assert value.read() == 7, "inherited method retains lexical access";
        '''))
        self.reject(program(base + '''
            class Child @ "child" extends Base {
                public method steal @ "steal"() -> Int { return self.secret; }
            }
        '''), "OKL-E-ACCESS")
        self.reject(program(base, '''
            object value @ "value": Base {}
            assert value.secret == 7, "private member";
        '''), "OKL-E-ACCESS")
        self.reject(program(base + '''
            class Child @ "child" extends Base { override secret = 8; }
        '''), "OKL-E-OVERRIDE")

    def test_nominal_upcast_dispatches_to_the_instance_override(self):
        self.accept(program('''
            class Base @ "base" {
                public method answer @ "answer"() -> Int { return 1; }
            }
            class Child @ "child" extends Base {
                public override method answer @ "answer"() -> Int { return 2; }
            }
            fn read @ "read"(item: Ref<Base>) -> Int { return item.answer(); }
        ''', '''
            object child @ "child": Child {}
            assert read(child) == 2, "nominal upcast preserves virtual dispatch";
        '''))
        self.reject(program('''
            class A @ "a" { public param n @ "n": Int = 1; }
            class B @ "b" { public param n @ "n": Int = 1; }
            fn read @ "read"(item: Ref<A>) -> Int { return item.n; }
        ''', '''
            object value @ "value": B {}
            assert read(value) == 1, "structural similarity is not an upcast";
        '''), "OKL-E-TYPE")

    def test_override_retains_parameter_names_and_member_keys(self):
        base = '''
            class Base @ "base" {
                public method f @ "f"(input: Int) -> Int { return input; }
            }
        '''
        for method in [
            'public override method f @ "f"(other: Int) -> Int { return other; }',
            'public override method f @ "new-f"(input: Int) -> Int { return input; }',
        ]:
            with self.subTest(method=method):
                self.reject(program(base + f'class Child @ "child" extends Base {{ {method} }}'),
                            "OKL-E-OVERRIDE")

    def test_explicit_inherited_builtin_defaults_require_override(self):
        base = 'class Base @ "base" { geometry = sphere(1[m]); }'
        self.reject(program(base + '''
            class Child @ "child" extends Base { geometry = empty(); }
        '''), "OKL-E-OVERRIDE")
        self.accept(program(base + '''
            class Child @ "child" extends Base { override geometry = empty(); }
        ''', 'object value @ "value": Child {}'))

    def test_outer_override_wins_and_part_rhs_uses_owner_scope(self):
        self.accept(program('''
            class Leaf @ "leaf" { public param n @ "n": Int = 1; }
            class Inner @ "inner" {
                public param n @ "n": Int = 2;
                public part leaf @ "leaf": Leaf { n = self.n; }
            }
            class Outer @ "outer" {
                public part inner @ "inner": Inner { n = 3; leaf.n = 4; }
            }
        ''', '''
            object first @ "first": Outer { inner.leaf.n = 5; }
            object second @ "second": Inner { n = 8; }
            assert first.inner.leaf.n == 5, "outermost explicit assignment wins";
            assert second.leaf.n == 8, "part RHS resolves self to the owner";
        '''))

    def test_same_scope_duplicate_assignments_are_errors(self):
        definitions = 'class Item @ "item" { public param n @ "n": Int = 1; }'
        self.reject(program(definitions, 'object value @ "value": Item { n = 2; n = 2; }'),
                    "OKL-E-NAME")
        self.reject(program('class Item @ "item" { geometry = empty(); geometry = empty(); }'),
                    "OKL-E-NAME")
        self.reject(program(scene='duration = 1[s];'), "OKL-E-NAME")

    def test_derived_values_and_nested_builtin_fields_are_readonly(self):
        definitions = '''
            class Leaf @ "leaf" { public derive n @ "n": Int = 1; }
            class Group @ "group" { public part leaf @ "leaf": Leaf {} }
        '''
        self.reject(program(definitions, 'object value @ "value": Leaf { n = 2; }'),
                    "OKL-E-READONLY")
        self.reject(program(definitions, 'object value @ "value": Group { leaf.motion = static; }'),
                    "OKL-E-NAME")

    def test_distinct_dependency_cycles_have_distinct_diagnostics(self):
        cases = [
            ('class A @ "a" extends B {} class B @ "b" extends A {}', '',
             "OKL-E-INHERITANCE-CYCLE"),
            ('class A @ "a" { public part again @ "again": A {} }', '',
             "OKL-E-RECURSIVE-COMPOSITION"),
            ('''class A @ "a" {
                public derive x @ "x": Int = self.y;
                public derive y @ "y": Int = self.x;
            }''', 'object value @ "value": A {}', "OKL-E-DEPENDENCY-CYCLE"),
            ('fn f @ "f"() -> Int { return g(); } fn g @ "g"() -> Int { return f(); }', '',
             "OKL-E-DEPENDENCY-CYCLE"),
        ]
        for definitions, scene, code in cases:
            with self.subTest(code=code, definitions=definitions):
                self.reject(program(definitions, scene), code)

    def test_class_expressions_cannot_capture_scene_names(self):
        self.reject(program('''
            class Item @ "item" { public derive label @ "label": String = external.role; }
        ''', 'object external @ "external": Object {}'), "OKL-E-NAME")

    def test_unit_errors_and_unsupported_dimensions_are_distinct(self):
        self.reject(program('class A @ "a" { public param x @ "x": Length = 1[furlong]; }'),
                    "OKL-E-UNIT", category="invalid")
        self.reject(program('class A @ "a" { public param x @ "x": Quantity[m^16*m] = 1[m^16*m]; }'),
                    "OKL-E-CAPABILITY-UNSUPPORTED", category="unsupported")
        self.reject(program(scene='assert 1[m^16] * 1[m] == 1[m], "unsupported dimension";'),
                    "OKL-E-CAPABILITY-UNSUPPORTED", category="unsupported")

    def test_unit_diagnostic_identifies_the_definition_and_exact_source(self):
        source = program('''
            // A UTF-8 comment before the error: café Ω
            class Item @ "item" {
                public param radius @ "radius": Length = 1[kg];
            }
        ''')
        diagnostic = self.reject(source, "OKL-E-UNIT").to_dict(Source(source, "unit.ok"))
        location = diagnostic["primary"]
        self.assertEqual(location["element_id"], ["contract", "definitions", "item", "radius"])
        self.assertEqual(source.encode("utf-8")[location["start_byte"]:location["end_byte"]], b"1[kg]")
        self.assertEqual(location["file"], "unit.ok")
        self.assertTrue(diagnostic["repair"]["summary"])

    def test_integer_boundaries_and_explicit_rounding(self):
        self.accept(program(scene='''
            assert -9223372036854775808 < 0, "minimum Int is legal";
            assert real(9007199254740993) == 9007199254740992.0, "explicit rounded conversion";
            assert 7 / 2 == 3.5, "integer division produces a Real quotient";
        '''))
        self.reject(program(scene='assert 9223372036854775808 > 0, "overflow";'),
                    "OKL-E-NUMERIC")
        self.reject(program(scene='assert abs(-9223372036854775808) > 0, "overflow";'),
                    "OKL-E-NUMERIC")
        self.reject(program(scene='assert 9007199254740993 == 9007199254740992.0, "lossy implicit widening";'),
                    "OKL-E-TYPE")

    def test_oversized_numeric_tokens_receive_structured_diagnostics(self):
        huge_integer = "9" * 5000
        self.reject(program(scene=f'assert {huge_integer} > 0, "outside Int range";'),
                    "OKL-E-NUMERIC")
        self.reject(program(f'''class Item @ "item" {{
            public param value @ "value": Quantity[m^{huge_integer}] = 1[m];
        }}'''), "OKL-E-CAPABILITY-UNSUPPORTED", category="unsupported")

    def test_scene_fields_and_namespace_are_checked(self):
        self.reject(program(settings='duration = 1[s];'), "OKL-E-NAME")
        self.reject(program(scene='unknown_field = 1;'), "OKL-E-NAME")
        self.reject(program(scene='''
            object item @ "item": Object {}
            action item @ "motion" = move(item, vector(world, 1[m/s], 0[m/s], 0[m/s]), 1[s]);
        '''), "OKL-E-NAME")


if __name__ == "__main__":
    unittest.main()
