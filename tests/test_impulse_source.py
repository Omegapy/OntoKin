"""Adopted source impulses: real pinned programs and exact source lowering."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.construction import ConstructionCompiler, compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.linker import link_program
from ontokin.syntax import Node, Token, lex
from ontokin.syntax02 import RESERVED_02, parse_source_unit


ROOT = Path(__file__).resolve().parents[1] / "docs/language-design/impulse-v0.1"
ACCEPTANCE = json.loads((ROOT / "acceptance.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in ACCEPTANCE["source_cases"]}


def fixture(case_id: str) -> ProgramBundle:
    return load_file_manifest(ROOT / CASES[case_id]["file_manifest"])


def with_entry(bundle: ProgramBundle, text: str) -> ProgramBundle:
    return ProgramBundle(replace(bundle.entry, raw=text.encode("utf-8")), bundle.modules)


def walk_nodes(value):
    if isinstance(value, (Node, Token)):
        yield value
        if isinstance(value, Node):
            for item in value.data.values():
                yield from walk_nodes(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_nodes(item)


class ImpulseSourceTests(unittest.TestCase):
    def test_all_positive_adopted_programs_lower_native_source_occurrences(self):
        for case_id, case in CASES.items():
            if case["kind"] != "positive":
                continue
            with self.subTest(case=case_id):
                bundle = fixture(case_id)
                self.assertEqual(bundle.program_revision, case["program_revision"])
                compiler = compile_construction(bundle)
                model = compiler.model
                self.assertEqual(model.profile, "impulse-0.1")
                self.assertEqual(model.program_revision, bundle.program_revision)
                events = [event for block in model.events for event in block.events
                          if event.kind == "impulse"]
                expected = case["source_impulse_statements"]
                self.assertEqual(len(events), len(expected))
                for event, statement in zip(events, expected):
                    self.assertIn(event.target, model.objects)
                    self.assertEqual(event.target, statement["target_path_spelling"])
                    self.assertEqual(event.impulse.sequence_index, statement["sequence_index"])
                    self.assertEqual(event.impulse.source, statement["source_location"])
                    self.assertEqual(bundle.entry.raw[event.span.start:event.span.end].decode("utf-8"),
                                     statement["expected_text"])
                    self.assertEqual(model.objects[event.target].geometry["kind"], "placed")
                    self.assertEqual(model.objects[event.target].geometry["surface"]["kind"], "loft")
                    self.assertEqual(model.objects[event.target].physical["kind"], "sphere_body")
                    self.assertEqual(len(event.impulse.impulse_world_n_s), 3)
                    self.assertEqual(len(event.impulse.point_self_m), 3)

    def test_adopted_elaboration_and_profile_negatives_keep_exact_codes(self):
        for case_id, case in CASES.items():
            if case["kind"] != "negative" or case["expected"]["phase_group"] == "event_admission":
                continue
            with self.subTest(case=case_id):
                bundle = fixture(case_id)
                with self.assertRaises(OntoKinError) as raised:
                    compile_construction(bundle)
                error = raised.exception
                self.assertEqual(error.code, case["expected"]["diagnostic_code"])
                source_id = error.diagnostic.node.source_id
                source = bundle.sources[source_id]
                source.raw[error.diagnostic.node.start:error.diagnostic.node.end].decode("utf-8")
                json.dumps(error.diagnostic.to_dict(source), allow_nan=False)

    def test_contextual_word_remains_an_identifier_outside_event_start(self):
        text = '''ontokin "0.4"; module impulse @ "impulse"; profile "impulse-0.1";
public class Body @ "body" {
    public param impulse @ "impulse": Real = 2;
    physical = sphere_body(0.5[m], 2[kg]);
}
scene Demo @ "demo" {
    duration = 2[s];
    gravity = vector(world, 0[m/s^2], 0[m/s^2], 0[m/s^2]);
    object ball @ "ball": Body { motion = dynamic; }
    object carrier @ "carrier": Body { }
    action impulse @ "impulse" = move(carrier, vector(world, 1[m/s], 0[m/s], 0[m/s]), 2[s]);
    at 0[s] sequence { start impulse; }
    at 1[s] sequence {
        stop impulse;
        impulse ball using vector(world, 0[N*s], 2[N*s], 0[N*s]) at point(ball.frame, 0[m], 0[m], 0[m]);
    }
}'''
        tokens = lex(text, reserved=RESERVED_02)
        self.assertTrue(all(token.kind == "IDENT" for token in tokens
                            if token.value == "impulse" and token.kind != "STRING"))
        compiler = compile_construction(ProgramBundle(SourceUnit("entry", "context.ok", text.encode())))
        self.assertIn("impulse", compiler.model.actions)
        self.assertEqual(compiler.model.events[1].events[1].impulse.sequence_index, 1)

    def test_point_frame_alias_resolves_to_the_actual_target(self):
        bundle = fixture("P01")
        text = bundle.entry.text.replace(
            'scene Demo @ "demo" {',
            'public fn axes @ "axes"(body: Ref<Object>) -> FrameRef { return body.frame; }\n'
            'scene Demo @ "demo" {').replace("point(ball.frame,", "point(axes(ball),")
        compiler = compile_construction(with_entry(bundle, text))
        event = compiler.model.events[0].events[0]
        self.assertEqual(event.target, "ball")
        self.assertEqual(event.impulse.point_self_m, (0.0, 0.0, 0.0))

    def test_nonobject_target_is_a_type_error(self):
        bundle = fixture("P01")
        text = bundle.entry.text.replace("impulse ball using", "impulse ball.origin using")
        with self.assertRaises(OntoKinError) as raised:
            compile_construction(with_entry(bundle, text))
        self.assertEqual(raised.exception.code, "OKL-E-TYPE")
        self.assertIn("IMP-001", raised.exception.diagnostic.rule_ids)

    def test_occurrence_target_keeps_literal_key_grammar(self):
        bundle = fixture("P08")
        text = bundle.entry.text.replace('impulse rack.props["first"]',
                                         'impulse rack.props["fir" + "st"]')
        with self.assertRaises(OntoKinError) as raised:
            parse_source_unit(with_entry(bundle, text).entry)
        self.assertEqual(raised.exception.code, "OKL-E-SYNTAX")

    def test_unicode_prefix_preserves_every_payload_and_statement_span(self):
        bundle = fixture("P04")
        changed = with_entry(bundle, "// café 雪\r\n" + bundle.entry.text)
        ast = parse_source_unit(changed.entry)
        for node in walk_nodes(ast):
            self.assertEqual(node.source_id, "entry")
            self.assertLessEqual(node.end, len(changed.entry.raw))
            changed.entry.raw[node.start:node.end].decode("utf-8")
        compiler = compile_construction(changed)
        event = compiler.model.events[-1].events[-1]
        self.assertEqual(event.impulse.source["source_revision"], changed.entry.revision)
        self.assertEqual(event.impulse.sequence_index, 1)
        self.assertEqual(event.impulse.source["start_byte"], event.span.start)
        self.assertTrue(changed.entry.raw[event.span.start:event.span.end].startswith(b"impulse ball "))

    def test_mixed_closure_preserves_declaring_profiles(self):
        compiler = compile_construction(fixture("P02"))
        self.assertEqual({source: module.ast.profile for source, module in compiler.linked.modules.items()},
                         CASES["P02"]["expected"]["declared_profiles"])
        event = compiler.model.events[0].events[0]
        self.assertEqual(event.impulse.impulse_world_n_s, (0.0, 2.0, 0.0))
        self.assertEqual(event.impulse.point_self_m, (0.5, 0.0, 0.0))

    def test_older_transitive_bridge_cannot_import_new_profile(self):
        original = fixture("P01")
        dependency = next(unit for unit in original.modules if unit.package_id == "fixture.impulse-parts")
        bridge_text = ('ontokin "0.2"; module Bridge @ "bridge"; profile "construction-0.1";\n'
                       'import bodies @ "bodies" from "fixture.impulse-parts" version "1.0.0" '
                       f'digest "{dependency.revision}";')
        bridge = SourceUnit("package:test.bridge@1.0.0", "bridge.ok", bridge_text.encode(),
                            "test.bridge", "1.0.0")
        entry = ('ontokin "0.4"; module Demo @ "demo"; profile "impulse-0.1";\n'
                 f'import bridge @ "bridge" from "test.bridge" version "1.0.0" digest "{bridge.revision}";\n'
                 'scene Test @ "test" { duration = 1[s]; }')
        bundle = ProgramBundle(SourceUnit("entry", "main.ok", entry.encode()), (*original.modules, bridge))
        with self.assertRaises(OntoKinError) as raised:
            link_program(bundle)
        self.assertEqual(raised.exception.code, "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertEqual(raised.exception.diagnostic.node.source_id, bridge.source_id)
        self.assertEqual(raised.exception.diagnostic.rule_ids, ["IMP-001"])

    def test_old_entry_bindings_do_not_gain_impulse_syntax(self):
        text = ('ontokin "VERSION"; module Demo @ "demo"; profile "PROFILE"; '
                'scene Test @ "test" { duration=1[s]; at 0[s] sequence { '
                'impulse ball using vector(world, 0[N*s], 1[N*s], 0[N*s]) '
                'at point(ball.frame, 0[m], 0[m], 0[m]); } }')
        for version, profile in (("0.2", "construction-0.1"), ("0.3", "surface-0.1")):
            with self.subTest(version=version):
                unit = SourceUnit("entry", "old.ok", text.replace("VERSION", version).replace("PROFILE", profile).encode())
                with self.assertRaises(OntoKinError) as raised:
                    parse_source_unit(unit)
                self.assertEqual(raised.exception.code, "OKL-E-SYNTAX")

    def test_new_profile_budget_reports_the_selected_binding(self):
        with self.assertRaises(OntoKinError) as raised:
            compile_construction(fixture("P01"), budgets={"max_value_entries": 1})
        self.assertEqual(raised.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(raised.exception.diagnostic.details["profile"], "impulse-0.1")

    def test_callback_failure_inside_impulse_lowering_is_unchanged(self):
        original = ConstructionCompiler.impulse_values
        errors = (OntoKinError("OKL-E-RESOURCE", "caller stopped", details={"caller": True}),
                  RecursionError("caller interrupted with its own exception"))
        for cancellation in errors:
            with self.subTest(exception=type(cancellation).__name__):
                entered = False

                def operands(compiler, event, context):
                    nonlocal entered
                    entered = True
                    return original(compiler, event, context)

                def check():
                    if entered:
                        raise cancellation

                with patch.object(ConstructionCompiler, "impulse_values", operands):
                    with self.assertRaises(type(cancellation)) as raised:
                        compile_construction(fixture("P01"), check=check)
                self.assertIs(raised.exception, cancellation)
                if isinstance(cancellation, OntoKinError):
                    self.assertIsNone(cancellation.diagnostic.rule_ids)
                    self.assertIsNone(cancellation.diagnostic.element_id)
                    self.assertEqual(cancellation.diagnostic.details, {"caller": True})


if __name__ == "__main__":
    unittest.main()
