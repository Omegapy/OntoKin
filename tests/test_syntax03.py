"""Native surface syntax from actual .ok files; not GLB/0.3 acceptance."""
from pathlib import Path
import unittest

from ontokin.bundle import SourceUnit
from ontokin.diagnostics import OntoKinError
from ontokin.syntax02 import parse_source_unit


ROOT = Path(__file__).resolve().parents[1] / "docs/language-design/surface-v0.1"


def unit(text, *, source_id="entry"):
    return (SourceUnit(source_id, "surface.ok", text.encode("utf-8"),
                       "fixture.surface-parts", "1.0.0")
            if source_id.startswith("package:") else
            SourceUnit(source_id, "surface.ok", text.encode("utf-8")))


class NativeSurfaceSyntaxTests(unittest.TestCase):
    def test_actual_library_parses_with_section_and_palette_values(self):
        source = unit((ROOT / "01-surface-parts.ok").read_text(encoding="utf-8"),
                      source_id="package:fixture.surface-parts@1.0.0")
        ast = parse_source_unit(source)
        self.assertEqual((ast.version, ast.profile), ("0.3", "surface-0.1"))
        self.assertIsNone(ast.scene)
        members = ast.classes[0].members
        self.assertEqual([m.name if m.kind == "param" else m.path[0].value for m in members],
                         ["rings", "palette", "geometry", "physical"])
        self.assertEqual(members[0].type.args[0].name, "LoftSection")
        self.assertEqual([item.key for item in members[0].value.entries],
                         ["foot", "neck", "tip"])
        self.assertEqual(members[1].type.args[0].name, "SurfaceMaterial")
        self.assertEqual(members[2].value.callee.name, "placed")

    def test_complete_scene_parses_pinned_import_and_occurrence_override(self):
        ast = parse_source_unit(unit((ROOT / "02-studio.ok").read_text(encoding="utf-8")))
        self.assertEqual(ast.profile, "surface-0.1")
        self.assertEqual(ast.imports[0].package_id, "fixture.surface-parts")
        self.assertEqual(ast.imports[0].version, "1.0.0")
        objects = [m for m in ast.scene.members if m.kind == "object"]
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[1].assignments[1].path[0].value, "rings")
        self.assertEqual(objects[1].assignments[1].value.element_type.name, "LoftSection")

    def test_versioned_parser_keeps_byte_precise_source_spans(self):
        text = "// café 雪\r\n" + (ROOT / "01-surface-parts.ok").read_text(encoding="utf-8")
        source = unit(text)
        ast = parse_source_unit(source)
        def scan(v):
            from ontokin.syntax import Node, Token
            if isinstance(v, (Node, Token)):
                yield v
                if isinstance(v, Node):
                    for child in v.data.values():
                        yield from scan(child)
            elif isinstance(v, (tuple, list)):
                for child in v:
                    yield from scan(child)
        for node in scan(ast):
            self.assertEqual(node.source_id, source.source_id)
            self.assertGreaterEqual(node.start, 0)
            self.assertLessEqual(node.end, len(source.raw))
            source.raw[node.start:node.end].decode("utf-8")

    def test_surface_version_rejects_old_profile(self):
        text = 'ontokin "0.3"; module A @ "a"; profile "construction-0.1";'
        with self.assertRaises(OntoKinError) as e:
            parse_source_unit(unit(text))
        self.assertEqual(e.exception.code, "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertEqual(e.exception.diagnostic.node.source_id, "entry")

    def test_legacy_version_rejects_surface_profile(self):
        text = 'ontokin "0.2"; module A @ "a"; profile "surface-0.1";'
        with self.assertRaises(OntoKinError) as e:
            parse_source_unit(unit(text))
        self.assertEqual(e.exception.code, "OKL-E-CAPABILITY-UNSUPPORTED")

    def test_original_version_keeps_original_ast(self):
        text = 'ontokin "0.2"; module A @ "a"; profile "construction-0.1"; scene Demo @ "demo" { duration = 1[s]; }'
        ast = parse_source_unit(unit(text))
        self.assertEqual((ast.version, ast.profile), ("0.2", "construction-0.1"))

    def test_bad_surface_syntax_keeps_source_identity(self):
        text = 'ontokin "0.3"; module A @ "a"; profile "surface-0.1"; class C @ "c" { geometry = loft(; }'
        with self.assertRaises(OntoKinError) as e:
            parse_source_unit(unit(text))
        self.assertEqual(e.exception.code, "OKL-E-SYNTAX")
        self.assertEqual(e.exception.diagnostic.node.source_id, "entry")

    def test_cooperative_interrupt_is_not_diagnostic(self):
        class Cancelled(Exception):
            pass
        def cancel():
            raise Cancelled()
        with self.assertRaises(Cancelled):
            parse_source_unit(unit('ontokin "0.3"; module A @ "a"; profile "surface-0.1";'), check=cancel)


if __name__ == "__main__":
    unittest.main()
