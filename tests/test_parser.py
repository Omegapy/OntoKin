"""The published sources and independent lexical/grammar boundary checks."""

import unittest

from ontokin.diagnostics import OntoKinError, Source
from ontokin.fixtures import load_manifest, materialize
from ontokin.syntax import lex, parse


MINIMAL = '''ontokin "0.1";
module M @ "m";
profile "core-0.1";
scene S @ "s" {
    duration = 1[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
}
'''


class ParserTests(unittest.TestCase):
    def test_published_source_syntax(self):
        for case in load_manifest()["cases"]:
            with self.subTest(case=case["id"]):
                source = materialize(case)
                if case["expected"]["syntax"] == "accept":
                    self.assertEqual(parse(source).kind, "program")
                else:
                    with self.assertRaises(OntoKinError) as caught:
                        parse(source)
                    self.assertEqual(caught.exception.code, case["expected"]["diagnostic_code"])

    def test_exact_original_utf8_spans_and_crlf(self):
        source = '// café Ω\r\n' + MINIMAL.replace('duration = 1[s];', 'duration = 1[s]')
        with self.assertRaises(OntoKinError) as caught:
            parse(source)
        diagnostic = caught.exception.diagnostic.to_dict(Source(source, "unicode.ok"))
        span = diagnostic["primary"]
        self.assertEqual(source.encode()[span["start_byte"]:span["end_byte"]], b"gravity")
        self.assertTrue(diagnostic["source_revision"].startswith("sha256:"))
        self.assertEqual(span["file"], "unicode.ok")

    def test_comments_and_escaped_characters(self):
        source = MINIMAL.replace('scene S', '/* /* no nesting */ scene S')
        self.assertEqual(parse(source).scene.name, "S")
        tokens = lex('"// /* café \\" \\\\ \\n \\r \\t"')
        self.assertEqual(tokens[0].kind, "STRING")
        self.assertIn("café", tokens[0].value)

    def test_invalid_lexical_forms(self):
        for fragment in ['01', '.5', '0x20', '1_000', '1e+', '"\\u0041"',
                         '"unterminated', '/* never closed', '\ufeff', '\u00a0',
                         '"\x00"', '"\x85"']:
            with self.subTest(fragment=repr(fragment)):
                with self.assertRaises(OntoKinError) as caught:
                    lex(fragment)
                self.assertEqual(caught.exception.code, "OKL-E-LEXICAL")

    def test_grammar_requires_one_complete_scene(self):
        for suffix in [';', 'scene Extra @ "extra" {}', 'garbage']:
            with self.subTest(suffix=suffix), self.assertRaises(OntoKinError):
                parse(MINIMAL + suffix)

    def test_unary_minus_and_operator_precedence(self):
        source = MINIMAL.replace('1[s]', '-2[s] + 3[s] * 4')
        value = parse(source).scene.members[0].value
        self.assertEqual(value.op, "+")
        self.assertEqual(value.left.kind, "unary")
        self.assertEqual(value.right.op, "*")

    def test_chained_comparison_rejected(self):
        source = MINIMAL.replace('duration = 1[s];', 'assert 1 < 2 < 3, "bad"; duration = 1[s];')
        with self.assertRaises(OntoKinError) as caught:
            parse(source)
        self.assertEqual(caught.exception.code, "OKL-E-SYNTAX")

    def test_source_revision_changes_with_original_bytes(self):
        a = Source(MINIMAL)
        b = Source(MINIMAL.replace('\n', '\r\n'))
        self.assertNotEqual(a.revision, b.revision)
        self.assertEqual(parse(a.text).module_key, parse(b.text).module_key)


if __name__ == "__main__":
    unittest.main()
