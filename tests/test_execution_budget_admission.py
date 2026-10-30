"""C073 admission, literal grammar, authority and shared-ledger boundaries."""
from dataclasses import FrozenInstanceError
import unittest

from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import (DEFAULT_LIMITS, MAX_HEADER_BYTES, MAX_LIMIT,
    HostPolicy, SharedExecutionBudget, admit_entry_budget)
from ontokin.linker import link_program
from ontokin.syntax import lex
from ontokin.syntax02 import RESERVED_02, parse_source_unit


HEADER = ('ontokin "0.7";\nmodule Workshop @"workshop";\n'
          'profile "planar-reach-budget-0.1";\n')
BODY = 'scene World @"world" {}\n'
LARGE = HostPolicy(400000, 80000)


def unit(declaration="", *, suffix=BODY, prefix=""):
    return SourceUnit("entry", "workshop.ok", (prefix + HEADER + declaration + suffix).encode())


def admit(source=None, *, policy=LARGE, caps=None, clock=None, check=None):
    ledger = SharedExecutionBudget(policy, caps, check=check, clock=clock)
    admit_entry_budget(unit() if source is None else source, ledger)
    return ledger


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


class ExecutionBudgetAdmissionTests(unittest.TestCase):
    def assert_reason(self, reason, callback):
        with self.assertRaises(OntoKinError) as caught:
            callback()
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-RESOURCE")
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], reason)
        return caught.exception

    def test_EB01_omission_retains_language_defaults_on_large_host(self):
        ledger = admit()
        self.assertEqual(ledger.limits, dict(DEFAULT_LIMITS))
        self.assertEqual(ledger.resolved.host_ceilings, LARGE.ceilings)
        for declaration, expected in [
            ("execution { max_operations = 200000; }", {"max_operations": 200000, "max_elapsed_ms": 30000}),
            ("execution { max_elapsed = 60[s]; }", {"max_operations": 100000, "max_elapsed_ms": 60000}),
        ]:
            with self.subTest(declaration=declaration):
                self.assertEqual(admit(unit(declaration)).limits, expected)

    def test_EB02_EB03_EB04_exact_authorized_example_requests(self):
        for operations, seconds in [(200000, 60), (400000, 75), (400000, 80)]:
            with self.subTest(seconds=seconds):
                source = unit(f"execution {{ max_operations = {operations}; max_elapsed = {seconds}[s]; }}")
                ledger = admit(source)
                self.assertEqual(ledger.limits, {"max_operations": operations, "max_elapsed_ms": seconds * 1000})
                self.assertEqual(parse_source_unit(source).execution.request, ledger.limits)
                self.assertEqual(ledger.admitted_entry_revision, source.revision)

    def test_EB05_source_cannot_authorize_larger_host_ceiling(self):
        source = unit("execution { max_operations = 400000; max_elapsed = 80[s]; }")
        ledger = SharedExecutionBudget()
        self.assert_reason("host_ceiling_exceeded", lambda: admit_entry_budget(source, ledger))
        self.assertIsNone(ledger.resolved)
        self.assertIsNone(ledger.admitted_entry_revision)
        self.assertEqual(ledger.report()["effective"], None)
        self.assertEqual(ledger.report()["source_request"]["max_operations"], 400000)

    def test_EB06_invalid_operation_literals_and_fields(self):
        declarations = [f"execution {{ max_operations = {value}; }}" for value in
            ["0", "-1", "+1", "true", "false", "null", "NaN", "Infinity", "1e5", "1.0",
             "100000 + 1", "len(keyed<Int>{})", "request", "1_000", "01", "9" * 200,
             str(MAX_LIMIT + 1)]]
        declarations += ["execution { max_unknown = 100; }",
                         "execution { max_operations = 100; max_operations = 200; }",
                         "execution { max_elapsed = 60[s]; max_elapsed = 70[s]; }"]
        for declaration in declarations:
            with self.subTest(declaration=declaration[:90]):
                self.assert_reason("invalid_declaration", lambda: admit(unit(declaration)))

    def test_EB06_invalid_host_values_and_unknown_caller_fields(self):
        for value in [False, True, None, 0, -1, 1.5, float("inf"), float("nan"), MAX_LIMIT + 1, "400000"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    HostPolicy(max_operations=value)
                with self.assertRaises(ValueError):
                    HostPolicy(max_elapsed_ms=value)
                self.assert_reason("invalid_declaration", lambda: SharedExecutionBudget(caller_caps={"max_operations": value}))
        self.assert_reason("invalid_declaration", lambda: SharedExecutionBudget(caller_caps={"trusted": True}))
        with self.assertRaises(TypeError):
            SharedExecutionBudget(policy={"max_operations": 400000})

    def test_EB07_exact_seconds_without_rounding(self):
        for literal, expected in [("0.5", 500), ("0.001", 1), ("0.5000", 500), ("1.001000", 1001)]:
            with self.subTest(literal=literal):
                ledger = admit(unit(f"execution {{ max_elapsed = {literal}[s]; }}"), clock=Clock())
                self.assertEqual(ledger.limits["max_elapsed_ms"], expected)
        for literal in ["0", "0.0001", "1.00001", "0.000", "1e1", "-1", ".5"]:
            with self.subTest(literal=literal):
                self.assert_reason("invalid_declaration", lambda: admit(unit(f"execution {{ max_elapsed = {literal}[s]; }}")))
        for unit_name in ["ms", "m", "s*s", "s^1"]:
            with self.subTest(unit_name=unit_name):
                self.assert_reason("invalid_declaration", lambda: admit(unit(f"execution {{ max_elapsed = 1[{unit_name}]; }}")))

    def test_EB08_empty_repeated_and_misplaced_declarations(self):
        for declaration in ["execution {}", "execution { max_operations = 200000; } execution { max_elapsed = 60[s]; }",
                            'execution { max_operations = 200000; } requires "late";']:
            with self.subTest(declaration=declaration):
                self.assert_reason("invalid_declaration", lambda: admit(unit(declaration)))
                self.assert_reason("invalid_declaration", lambda: parse_source_unit(unit(declaration)))
        self.assert_reason("invalid_declaration", lambda: parse_source_unit(unit(suffix=BODY + "execution { max_operations = 200000; }")))
        misplaced = unit('public class Part @"part" {} execution { max_operations = 200000; }')
        self.assert_reason("invalid_declaration", lambda: parse_source_unit(misplaced))

    def test_EB08_imported_declaration_is_rejected_even_when_smaller(self):
        imported = SourceUnit("package:demo.parts@1.0.0", "parts.ok",
            (HEADER + "execution { max_operations = 1000; }").encode(), "demo.parts", "1.0.0")
        self.assert_reason("invalid_declaration", lambda: parse_source_unit(imported))

    def test_EB09_fake_comment_and_string_declarations_do_not_grant_authority(self):
        source = unit('requires "execution { max_operations = 400000; }";\n',
                      prefix='// execution { max_operations = 400000; }\n'
                             '/* execution { max_elapsed = 80[s]; } */\n')
        self.assertEqual(admit(source).limits, dict(DEFAULT_LIMITS))

    def test_EB09_prefix_comments_are_bounded_and_paid(self):
        source = unit(prefix="/*" + "x" * MAX_HEADER_BYTES + "*/")
        ledger = SharedExecutionBudget(LARGE)
        self.assert_reason("invalid_declaration", lambda: admit_entry_budget(source, ledger))
        self.assertEqual(ledger.operations, MAX_HEADER_BYTES // 64)
        self.assertIsNone(ledger.resolved)
        self.assertEqual(ledger.budget_reason, "invalid_declaration")

    def test_EB09_body_is_not_lexed_to_discover_authority(self):
        source = unit(suffix='scene World @"world" { /*' + 'x' * (MAX_HEADER_BYTES + 1))
        ledger = admit(source)
        self.assertEqual(ledger.limits, dict(DEFAULT_LIMITS))
        self.assertLess(ledger.operations, 30)
        with self.assertRaises(OntoKinError):
            parse_source_unit(source)

    def test_EB09_oversized_prefix_tokens_reject_before_conversion(self):
        for text in ['ontokin "' + "x" * 10000 + '";',
                     'ontokin "0.7"; module ' + "x" * 10000,
                     HEADER + "execution { max_operations = " + "9" * 10000]:
            with self.subTest(start=text[:50]):
                ledger = SharedExecutionBudget(LARGE)
                self.assert_reason("invalid_declaration", lambda: admit_entry_budget(SourceUnit("entry", "x.ok", text.encode()), ledger))
                self.assertLess(ledger.operations, 50)

    def test_EB09_utf8_prefix_charges_bytes_and_preserves_error_span(self):
        prefix = "/*" + "\U0001f680" * 80 + "*/\n"
        plain = admit()
        unicode_ledger = admit(unit(prefix=prefix))
        header_bytes = len((HEADER + "scene").encode())
        expected_extra = ((header_bytes + len(prefix.encode()) + 63) // 64
                          - (header_bytes + 63) // 64)
        self.assertEqual(unicode_ledger.operations - plain.operations, expected_extra)
        source = unit("execution { unknown = 200000; }", prefix=prefix)
        error = self.assert_reason("invalid_declaration", lambda: admit(source))
        self.assertEqual(error.diagnostic.node.start, source.raw.index(b"unknown"))

    def test_EB09_prefix_uses_the_full_parser_identifier_rule(self):
        source = SourceUnit("entry", "bad.ok", unit().raw.replace(b"module Workshop", b"module scene"))
        ledger = SharedExecutionBudget(LARGE)
        self.assert_reason("invalid_declaration", lambda: admit_entry_budget(source, ledger))
        self.assertIsNone(ledger.resolved)

    def test_EB10_exact_operation_boundary_and_next_charge(self):
        ledger = admit(unit("execution { max_operations = 200000; }"))
        admission_work = ledger.operations
        self.assertGreater(admission_work, 0)
        ledger.tick(amount=200000 - admission_work)
        self.assertEqual(ledger.operations, 200000)
        ledger.checkpoint()
        self.assert_reason("operation_budget_exhausted", ledger.tick)
        self.assertEqual(ledger.operations, 200001)

    def test_EB10_promotion_preserves_consumed_header_work(self):
        source = unit("execution { max_operations = 1; }")
        ledger = SharedExecutionBudget(LARGE)
        self.assert_reason("operation_budget_exhausted", lambda: admit_entry_budget(source, ledger))
        self.assertGreater(ledger.operations, 1)
        self.assertEqual(ledger.limits["max_operations"], 1)

    def test_EB11_selected_deadlines_keep_original_start_and_inclusive_boundary(self):
        for seconds in (60, 75, 80):
            with self.subTest(seconds=seconds):
                clock = Clock()
                ledger = admit(unit(f"execution {{ max_elapsed = {seconds}[s]; }}"), clock=clock)
                self.assertEqual(ledger.started, 0)
                clock.value = seconds
                ledger.checkpoint()
                clock.value = seconds + 0.001
                self.assert_reason("execution_deadline_exceeded", ledger.checkpoint)

    def test_EB11_promotion_does_not_restart_clock(self):
        clock = Clock()
        def elapsed_header():
            clock.value = 0.2
        ledger = SharedExecutionBudget(LARGE, clock=clock, check=elapsed_header)
        source = unit("execution { max_elapsed = 0.1[s]; }")
        self.assert_reason("execution_deadline_exceeded", lambda: admit_entry_budget(source, ledger))
        self.assertEqual(ledger.started, 0)
        self.assertEqual(ledger.report()["elapsed_ms"], 200)

    def test_EB11_provisional_deadline_applies_before_authorization(self):
        clock = Clock()
        def slow_header():
            clock.value = 30.001
        ledger = SharedExecutionBudget(LARGE, clock=clock, check=slow_header)
        self.assert_reason("execution_deadline_exceeded", lambda: admit_entry_budget(unit("execution { max_elapsed = 80[s]; }"), ledger))
        self.assertIsNone(ledger.resolved)

    def test_EB12_no_second_promotion_or_mutable_authority(self):
        source = unit("execution { max_operations = 200000; }")
        ledger = admit(source)
        spent = ledger.operations
        with self.assertRaises(ValueError):
            admit_entry_budget(source, ledger)
        self.assertEqual(ledger.operations, spent)
        with self.assertRaises(TypeError):
            ledger.resolved.effective["max_operations"] = 400000
        with self.assertRaises(FrozenInstanceError):
            ledger.policy.max_operations = 800000
        detached = ledger.limits
        detached["max_operations"] = 999999
        self.assertEqual(ledger.limits["max_operations"], 200000)

    def test_EB17_explicit_caller_reductions_and_conflict(self):
        source = unit("execution { max_operations = 400000; max_elapsed = 80[s]; }")
        ledger = admit(source, policy=HostPolicy(200000, 60000),
                       caps={"max_operations": 200000, "max_elapsed_ms": 60000})
        self.assertEqual(ledger.limits, {"max_operations": 200000, "max_elapsed_ms": 60000})
        self.assertEqual(ledger.resolved.source_request["max_operations"], 400000)
        self.assert_reason("request_cap_exceeds_source", lambda: admit(caps={"max_operations": 200000}))

    def test_EB19_callback_identity_and_order(self):
        marker = OntoKinError("OKL-E-SYNTAX", "Caller interruption")
        def cancel():
            raise marker
        ledger = SharedExecutionBudget(check=cancel)
        with self.assertRaises(OntoKinError) as caught:
            admit_entry_budget(unit(), ledger)
        self.assertIs(caught.exception, marker)
        self.assertIs(ledger.callback_error, marker)
        self.assertEqual(ledger.operations, 0)
        self.assertIsNone(ledger.budget_reason)

    def test_EB21_legacy_lexer_and_parser_do_not_accept_new_declaration(self):
        self.assertEqual(lex("execution", reserved=RESERVED_02)[0].kind, "IDENT")
        old = unit().text.replace('"0.7"', '"0.6"').replace('"planar-reach-budget-0.1"', '"planar-reach-0.1"')
        parsed = parse_source_unit(SourceUnit("entry", "old.ok", old.encode()))
        self.assertNotIn("execution", parsed.data)
        with self.assertRaises(OntoKinError):
            parse_source_unit(SourceUnit("entry", "old.ok", old.replace(BODY, "execution { max_operations = 400000; }" + BODY).encode()))

    def test_EB22_explicit_import_compatibility(self):
        for version, profile in [("0.2", "construction-0.1"), ("0.3", "surface-0.1"),
                ("0.4", "impulse-0.1"), ("0.5", "force-0.1"),
                ("0.6", "planar-reach-0.1"), ("0.7", "planar-reach-budget-0.1")]:
            with self.subTest(profile=profile):
                imported = SourceUnit("package:demo.parts@1.0.0", "parts.ok",
                    f'ontokin "{version}"; module Parts @"parts"; profile "{profile}";'.encode(),
                    "demo.parts", "1.0.0")
                declaration = f'import Parts @"parts" from "demo.parts" version "1.0.0" digest "{imported.revision}";'
                linked = link_program(ProgramBundle(unit(declaration), (imported,)))
                self.assertEqual(linked.entry.ast.profile, "planar-reach-budget-0.1")
                self.assertEqual(linked.modules[imported.source_id].ast.profile, profile)
        old_entry = unit(declaration).text.replace('"0.7"', '"0.6"').replace('"planar-reach-budget-0.1"', '"planar-reach-0.1"')
        with self.assertRaises(OntoKinError) as caught:
            link_program(ProgramBundle(SourceUnit("entry", "old.ok", old_entry.encode()), (imported,)))
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-CAPABILITY-UNSUPPORTED")

    def test_EB25_host_below_defaults_requires_explicit_lower_request(self):
        host = HostPolicy(50000, 10000)
        self.assert_reason("host_ceiling_exceeded", lambda: admit(policy=host))
        source = unit("execution { max_operations = 50000; max_elapsed = 10[s]; }")
        self.assertEqual(admit(source, policy=host).limits, host.ceilings)
        self.assertEqual(admit(policy=host, caps=host.ceilings).limits, host.ceilings)

    def test_EB26_receipt_is_bounded_and_unresolved_fields_are_null(self):
        ledger = SharedExecutionBudget(LARGE)
        report = ledger.report(status="failed")
        self.assertIsNone(report["source_request"])
        self.assertIsNone(report["effective"])
        self.assertEqual(report["stage"], "header_admission")
        self.assertEqual(report["defaults"], dict(DEFAULT_LIMITS))
        self.assertEqual(report["host_ceilings"], LARGE.ceilings)
        self.assertEqual(HostPolicy(400000, 80000).policy_id, LARGE.policy_id)


if __name__ == "__main__":
    unittest.main()
