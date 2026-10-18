"""Version-specific grammar and original UTF-8 source-location regressions."""

from __future__ import annotations

from pathlib import Path
import unittest

from ontokin.bundle import SourceUnit, load_file_manifest
from ontokin.diagnostics import OntoKinError
from ontokin.syntax import Node, Token, parse
from ontokin.syntax02 import PathStep, parse_source_unit
from ontokin.validator import validate


ROOT = Path(__file__).resolve().parents[1] / "docs/language-design/construction-v0.1"
HEADER = 'ontokin "0.2"; module Example @ "example"; profile "construction-0.1";\n'
SCENE = 'scene Demo @ "demo" { duration=1[s]; }'


def unit(text, *, dependency=False):
    if dependency:
        return SourceUnit("package:example.library@1.0.0", "library.ok", text.encode("utf-8"), "example.library", "1.0.0")
    return SourceUnit("entry", "main.ok", text.encode("utf-8"))


def nodes(value):
    if isinstance(value, (Node, Token)):
        yield value
        if isinstance(value, Node):
            for child in value.data.values():
                yield from nodes(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from nodes(child)


class Syntax02Tests(unittest.TestCase):
    def test_complete_fixtures_retain_every_source_origin(self):
        for folder in ["01-keyed-rack", "02-namespaces", "03-transitive"]:
            bundle = load_file_manifest(ROOT / folder / "program.files.json")
            for source in bundle.units:
                ast = parse_source_unit(source)
                with self.subTest(source=source.source_id, folder=folder):
                    for node in nodes(ast):
                        self.assertEqual(node.source_id, source.source_id)
                        self.assertGreaterEqual(node.start, 0)
                        self.assertLessEqual(node.end, len(source.raw))
                        source.raw[node.start:node.end].decode("utf-8")
                    self.assertEqual(ast.scene is not None, source.source_id == "entry")

    def test_key_steps_do_not_split_dotted_entry_names(self):
        text = HEADER + '''
class Rack @ "rack" {
    public parts pieces @ "pieces": imported.Marker for (key, item) in self.inputs { radius=item; }
}
scene Demo @ "demo" {
    object rig @ "rig": Rack { pieces["left.eye"].radius=0.3[m]; }
    at 0[s] sequence { release rig.pieces["left.eye"].hold using incoming; }
}
'''
        ast = parse_source_unit(unit(text))
        assignment = ast.scene.members[0].assignments[0]
        self.assertEqual([(p.kind, p.value) for p in assignment.path],
                         [("member", "pieces"), ("key", "left.eye"), ("member", "radius")])
        self.assertTrue(all(isinstance(p, PathStep) for p in assignment.path))
        release = ast.scene.members[1].events[0]
        self.assertEqual([(p.kind, p.value) for p in release.path],
                         [("member", "rig"), ("member", "pieces"), ("key", "left.eye"), ("member", "hold")])

    def test_expression_keys_can_be_computed_but_assignment_keys_are_literals(self):
        ast = parse_source_unit(unit(HEADER + '''
fn get @ "get"(values: Keyed<Length>, key: String) -> Length { return values[key]; }
''' + SCENE))
        result = ast.functions[0].result
        self.assertEqual(result.kind, "index")
        self.assertEqual(result.index.name, "key")
        for target in ['parts[variable].radius', 'parts[1].radius', 'parts["one"]()']:
            source = HEADER + 'scene Demo @ "demo" { object a @ "a": A { ' + target + '=1[m]; } }'
            with self.subTest(target=target), self.assertRaises(OntoKinError) as rejected:
                parse_source_unit(unit(source))
            self.assertEqual(rejected.exception.code, "OKL-E-SYNTAX")

    def test_keyed_empty_type_duplicate_entries_and_typed_body_bindings(self):
        ast = parse_source_unit(unit(HEADER + '''
class A @ "a" {
    public param inputs @ "inputs": Keyed<Length> = keyed<Length>{"x":1[m],"x":2[m]};
    public derive empty_values @ "empty": Keyed<Length> = keyed<Length>{};
    public parts pieces @ "pieces": external.Part for (key, value) in self.inputs { radius=value; }
}
''' + SCENE))
        literal = ast.classes[0].members[0].value
        self.assertEqual([entry.key for entry in literal.entries], ["x", "x"])
        self.assertEqual([entry.value.text for entry in literal.entries], ["1", "2"])
        self.assertEqual(literal.element_type.name, "Length")
        self.assertEqual(ast.classes[0].members[1].value.entries, [])
        generated = ast.classes[0].members[2]
        self.assertEqual((generated.key_name, generated.value_name), ("key", "value"))
        self.assertEqual(generated.class_name_parts, ("external", "Part"))

    def test_qualified_base_reference_types_calls_and_visibility(self):
        ast = parse_source_unit(unit(HEADER + '''
import lib @ "lib" from "example.library" version "1.0.0" digest "sha256:0000000000000000000000000000000000000000000000000000000000000000";
private class Hidden @ "hidden" extends lib.Base {}
class Visible @ "visible" {}
public fn preserve @ "preserve"(value: Ref<lib.Base>) -> Ref<lib.Base> { return lib.keep(value); }
''' + SCENE))
        self.assertEqual(ast.classes[0].base_parts, ("lib", "Base"))
        self.assertEqual([item.visibility for item in ast.classes], ["private", "public"])
        self.assertEqual(ast.functions[0].params[0].type.args[0].name_parts, ("lib", "Base"))
        self.assertEqual(ast.functions[0].result.callee.target.name, "lib")

    def test_utf8_crlf_primary_and_import_literal_spans(self):
        text = '// café 雪\r\n' + HEADER.replace("\n", "\r\n") + '''import lib @ "lib" from "example.library" version "1.0.0" digest "sha256:0000000000000000000000000000000000000000000000000000000000000000";\r\n''' + SCENE
        source = unit(text, dependency=True)
        ast = parse_source_unit(source)
        literal = ast.imports[0].package_node
        self.assertEqual(source.raw[literal.start:literal.end], b'"example.library"')
        self.assertEqual(literal.start, source.raw.index(b'"example.library"'))
        self.assertEqual(literal.source_id, source.source_id)
        broken = unit(text.replace('duration=1[s]', 'duration=1['), dependency=True)
        with self.assertRaises(OntoKinError) as rejected:
            parse_source_unit(broken)
        self.assertEqual(rejected.exception.diagnostic.node.source_id, broken.source_id)

    def test_old_keywords_and_old_path_ast_keep_their_meaning(self):
        for identifier in ["import", "from", "version", "digest", "parts", "for", "in", "keyed", "len", "Keyed"]:
            text = 'ontokin "0.1"; module Legacy @ "legacy"; profile "core-0.1"; ' + \
                f'fn {identifier} @ "fn"(value:Int)->Int{{ return value; }} ' + \
                'scene Demo @ "demo" { duration=1[s]; gravity=vector(world,0[m/s^2],0[m/s^2],0[m/s^2]); }'
            with self.subTest(identifier=identifier):
                ast = parse(text)
                validate(ast, level="represented")
                self.assertEqual(ast.functions[0].name, identifier)
                self.assertIsNone(ast.source_id)
                self.assertEqual(ast.scene.members[0].path, ["duration"])

    def test_role_is_linked_version_and_profile_are_explicit(self):
        self.assertIsNone(parse_source_unit(unit(HEADER)).scene)
        self.assertIsNotNone(parse_source_unit(unit(HEADER + SCENE, dependency=True)).scene)
        for text in [HEADER.replace('"0.2"', '"0.1"') + SCENE,
                     HEADER.replace('"construction-0.1"', '"core-0.1"') + SCENE]:
            with self.subTest(text=text), self.assertRaises(OntoKinError) as rejected:
                parse_source_unit(unit(text))
            self.assertEqual(rejected.exception.code, "OKL-E-CAPABILITY-UNSUPPORTED")
            self.assertEqual(rejected.exception.diagnostic.node.source_id, "entry")

    def test_bounded_nesting_and_caller_interrupt_are_not_host_failures(self):
        deep = HEADER + 'scene Demo @ "demo" { duration=' + '(' * 1500 + '1[s]' + ')' * 1500 + '; }'
        with self.assertRaises(OntoKinError) as rejected:
            parse_source_unit(unit(deep))
        self.assertEqual(rejected.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(rejected.exception.diagnostic.node.source_id, "entry")
        cancellation = OntoKinError("OKL-E-REVISION", "caller cancellation sentinel")
        def stop():
            raise cancellation
        with self.assertRaises(OntoKinError) as interrupted:
            parse_source_unit(unit(HEADER + SCENE), check=stop)
        self.assertIs(interrupted.exception, cancellation)
        self.assertIsNone(cancellation.diagnostic.node)


if __name__ == "__main__":
    unittest.main()
