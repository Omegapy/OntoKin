"""Source lowering against the independently frozen .22 corpus."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest
from fractions import Fraction
from types import SimpleNamespace

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.program_diagnostics import diagnostic_dict
from ontokin.texture_bundle import load_texture_file_manifest
from ontokin.torque_source import source_intervals


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "docs/language-design/torque-v0.1/freeze"
AMENDMENT = ROOT / "docs/language-design/torque-amendments/c091-grouped-expression-span"


def document(path):
    return json.loads(path.read_bytes())


def compile_frozen(filename, *, check=None):
    program = load_texture_file_manifest(FROZEN / filename)
    ledger = SharedExecutionBudget(check=check)
    profile = "keyed-membership-0.1" if 'profile "keyed-membership-0.1";' in program.entry.text else "torque-0.1"
    admit_entry_budget(program.entry, ledger, profile=profile)
    return program, ledger, compile_construction(program, execution_budget=ledger)


def effective_expectation(case):
    expected = copy.deepcopy(case["expected"])
    if case["id"] != "n28-torque-child-before-duration-type":
        return expected
    amendment = document(AMENDMENT / "AMENDMENT.json")
    publication = document(AMENDMENT / "PUBLICATION.json")
    # The original packet stays byte-identical. The separately adopted and
    # independently reviewed replacement is the only effective overlay.
    if hashlib.sha256((FROZEN / "refusal-cases.json").read_bytes()).hexdigest() != amendment["original_table"]["sha256"]:
        raise AssertionError("Original refusal table changed")
    if not publication or not (AMENDMENT / "ADOPTION.md").is_file():
        raise AssertionError("Amendment publication authority is absent")
    if expected["primary_source"] != amendment["original"]:
        raise AssertionError("Amendment no longer addresses the exact original field")
    expected["primary_source"] = amendment["replacement"]
    return expected


class TorqueSourceTests(unittest.TestCase):
    def assert_diagnostic(self, error, program, expected):
        actual = diagnostic_dict(error.diagnostic, program)
        for field in ("code", "message", "phase"):
            if field in expected:
                self.assertEqual(actual[field], expected[field], field)
        primary = actual["primary"]
        for field, value in expected["primary_source"].items():
            if field != "text":
                self.assertEqual(primary[field], value, field)
        span = expected["primary_source"]
        unit = program.sources[span["source_id"]]
        self.assertEqual(unit.raw[primary["start_byte"]:primary["end_byte"]].decode(), span["text"])
        for field, value in expected.get("required_details", {}).items():
            self.assertEqual(actual["details"][field], value, field)
        if "required_related" in expected:
            self.assertEqual(len(actual["related"]), 1)
            related = actual["related"][0]
            self.assertEqual(related["source_id"], primary["source_id"])
            self.assertLess(related["start_byte"], primary["start_byte"])
            earlier = unit.raw[related["start_byte"]:related["end_byte"]].decode()
            self.assertIn('torque ball @ "same"', earlier)

    def test_complete_source_records_match_all_frozen_positive_cases(self):
        cases = document(FROZEN / "state-expectations.json")["cases"]
        self.assertEqual(len(cases), 31)
        for case in cases:
            with self.subTest(case=case["case"]):
                program, ledger, compiler = compile_frozen(case["case"] + ".files.json")
                self.assertEqual(program.program_revision, case["program_revision"])
                actual = source_intervals(compiler, case["target_path"], compiler.budget)
                self.assertEqual(actual, case["source_records"])
                for path in compiler.model.objects:
                    if path != case["target_path"]:
                        # Complete empty occurrence histories never borrow a
                        # carrier's authored intervals through following.
                        own = source_intervals(compiler, path, compiler.budget)
                        self.assertTrue(all(row["target_path"] == path for row in own))

    def test_source_refusals_preserve_order_diagnostic_and_original_spans(self):
        cases = document(FROZEN / "refusal-cases.json")["cases"]
        selected = [case for case in cases if case["expected"]["phase"] not in ("admission", "evaluation")]
        self.assertEqual(len(selected), 18)
        for case in selected:
            with self.subTest(case=case["id"]):
                program = load_texture_file_manifest(FROZEN / case["file_manifest"])
                self.assertEqual(program.program_revision, case["identity"]["program_revision"])
                try:
                    compile_frozen(case["file_manifest"])
                except OntoKinError as error:
                    self.assert_diagnostic(error, program, effective_expectation(case))
                else:
                    self.fail("Frozen source refusal was accepted")

    def test_contextual_names_imported_helpers_and_event_scope(self):
        for case in document(FROZEN / "language-cases.json")["cases"]:
            with self.subTest(case=case["id"]):
                program = load_texture_file_manifest(FROZEN / case["file_manifest"])
                self.assertEqual(program.program_revision, case["identity"]["program_revision"])
                try:
                    _, _, compiler = compile_frozen(case["file_manifest"])
                except OntoKinError as error:
                    self.assertEqual(case["expected"]["compile"], "refused")
                    self.assert_diagnostic(error, program, case["expected"])
                else:
                    self.assertEqual(case["expected"]["compile"], "accepted")
                    self.assertEqual(compiler.model.profile, "torque-0.1")

    def test_source_stage_callback_keeps_original_exception_and_restores_stage(self):
        program = load_texture_file_manifest(FROZEN / "p01-spin-up.files.json")
        sentinel = RuntimeError("original source callback")
        visited = []
        ledger = SharedExecutionBudget()
        admit_entry_budget(program.entry, ledger, profile="torque-0.1")
        ledger.stage = "source-test-owner"
        def callback():
            if ledger.stage == "torque_source":
                visited.append((id(ledger), ledger.started, ledger.operations))
                raise sentinel
        ledger.check = callback
        with self.assertRaises(RuntimeError) as caught:
            compile_construction(program, execution_budget=ledger)
        self.assertIs(caught.exception, sentinel)
        self.assertIs(ledger.callback_error, sentinel)
        self.assertEqual(len(visited), 1)
        self.assertEqual(ledger.stage, "source-test-owner")

    def test_empty_projection_is_charged_and_callback_exception_restores_owner_stage(self):
        _, ledger, compiler = compile_frozen("p01-spin-up.files.json")
        empty = next(path for path in compiler.model.objects if path != "ball")
        old = ledger.operations
        self.assertEqual(source_intervals(compiler, empty, compiler.budget), [])
        self.assertEqual(ledger.operations, old + 1)
        sentinel = RuntimeError("original empty projection callback")
        ledger.stage = "projection-test-owner"
        def callback():
            if ledger.stage == "torque_projection":
                raise sentinel
        ledger.check = callback
        with self.assertRaises(RuntimeError) as caught:
            source_intervals(compiler, empty, compiler.budget)
        self.assertIs(caught.exception, sentinel)
        self.assertEqual(ledger.stage, "projection-test-owner")

    def test_projection_cannot_replace_original_context(self):
        program, ledger, compiler = compile_frozen("p01-spin-up.files.json")
        other = SharedExecutionBudget()
        admit_entry_budget(program.entry, other, profile="torque-0.1")
        with self.assertRaises(OntoKinError) as caught:
            source_intervals(compiler, "ball", SimpleNamespace(execution_budget=other))
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-RESOURCE")
        self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")

    def test_projection_rejects_source_mutation_by_original_callback(self):
        for selected in (1, 2):
            with self.subTest(header_or_record_tick=selected):
                _, ledger, compiler = compile_frozen("p01-spin-up.files.json")
                event = next(event for block in compiler.model.events for event in block.events if event.kind == "torque")
                visits = []
                ledger.stage = "mutation-test-owner"
                def callback():
                    if ledger.stage == "torque_projection":
                        visits.append(ledger.operations)
                        if len(visits) == selected:
                            event.torque.source["source_revision"] = "sha256:"+"0"*64
                ledger.check = callback
                with self.assertRaises(ValueError):
                    source_intervals(compiler, "ball", compiler.budget)
                self.assertEqual(len(visits), selected)
                self.assertEqual(ledger.stage, "mutation-test-owner")
                self.assertIsNone(ledger.callback_error)

    def test_source_completion_addition_is_charged_to_original_work(self):
        _, ledger, compiler = compile_frozen("p01-spin-up.files.json")
        work = compiler.reach_work
        before, counts = ledger.operations, dict(work.counts)
        records = source_intervals(compiler, "ball", compiler.budget)
        self.assertEqual(ledger.operations - before, 1 + 2 * len(records))
        self.assertEqual(work.counts.get("exact_add", 0) - counts.get("exact_add", 0), len(records))
        self.assertIsNone(work._source_after_charge)

    def test_oversize_native_source_clock_refuses_before_callback_or_addition(self):
        from ontokin.reach_numeric import MAX_OPERAND_BITS
        _, ledger, compiler = compile_frozen("p01-spin-up.files.json")
        block = next(block for block in compiler.model.events if any(event.kind == "torque" for event in block.events))
        block.time = Fraction(1 << MAX_OPERAND_BITS)
        visits = []
        ledger.check = lambda: visits.append(ledger.operations)
        before = ledger.operations
        with self.assertRaises(ValueError):
            source_intervals(compiler, "ball", compiler.budget)
        self.assertEqual(ledger.operations, before)
        self.assertEqual(visits, [])

    def test_source_callback_cannot_reset_counter_or_replace_numeric_context(self):
        for selected in (1, 2, 3):
            with self.subTest(header_record_or_addition=selected):
                _, ledger, compiler = compile_frozen("p01-spin-up.files.json")
                visited = []
                ledger.stage = "source-counter-owner"
                def callback():
                    if ledger.stage == "torque_projection":
                        visited.append(ledger.operations)
                        if len(visited) == selected:
                            ledger.operations = 0
                ledger.check = callback
                with self.assertRaises(OntoKinError) as caught:
                    source_intervals(compiler, "ball", compiler.budget)
                self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                self.assertEqual(len(visited), selected)
                self.assertEqual(ledger.stage, "source-counter-owner")
                self.assertIsNone(compiler.reach_work._source_after_charge)

    def test_native_fraction_slots_and_span_tokens_cannot_mutate_in_place(self):
        for selected in (1, 2, 3):
            for changed in ("clock-numerator", "clock-denominator", "duration-numerator", "duration-denominator",
                            "event-source", "event-start", "event-end", "block-start"):
                with self.subTest(tick=selected, changed=changed):
                    _, ledger, compiler = compile_frozen("p01-spin-up.files.json")
                    block = next(block for block in compiler.model.events if any(event.kind == "torque" for event in block.events))
                    event = next(event for event in block.events if event.kind == "torque")
                    visits = []
                    def callback():
                        if ledger.stage != "torque_projection":
                            return
                        visits.append(ledger.operations)
                        if len(visits) != selected:
                            return
                        if changed.startswith("clock-"):
                            field = "_" + changed.removeprefix("clock-")
                            object.__setattr__(block.time, field, getattr(block.time, field) + 1)
                        elif changed.startswith("duration-"):
                            field = "_" + changed.removeprefix("duration-")
                            object.__setattr__(event.torque.duration, field, getattr(event.torque.duration, field) + 1)
                        elif changed == "event-source":
                            event.span.source_id = "changed-source"
                        elif changed == "event-start":
                            event.span.start += 1
                        elif changed == "event-end":
                            event.span.end += 1
                        else:
                            block.span.start += 1
                    ledger.check = callback
                    with self.assertRaises((ValueError, OntoKinError)):
                        source_intervals(compiler, "ball", compiler.budget)
                    self.assertEqual(len(visits), selected)
                    self.assertIsNone(compiler.reach_work._source_after_charge)

    def test_foreign_equal_context_values_refuse_without_foreign_methods(self):
        for selected in (1, 2, 3):
            for field in ("external_check", "ledger_started", "work_started", "max_operand_bits",
                          "max_cache_entries", "max_operations", "max_elapsed_ms", "limits_owner",
                          "limits_value", "work_operations", "work_count", "event_kind", "module_key",
                          "element_id", "context_hook"):
                with self.subTest(callback=selected, field=field):
                    _, ledger, compiler = compile_frozen("p04-overlap.files.json")
                    work = compiler.reach_work
                    event = next(event for block in compiler.model.events for event in block.events if event.kind == "torque")
                    original_guard = ledger._torque_context_guard
                    original_observer = work._source_after_charge
                    foreign_calls, visits = [], []
                    class Foreign:
                        def __eq__(self, other):
                            foreign_calls.append("equality")
                            return True
                        def __ne__(self, other):
                            foreign_calls.append("inequality")
                            return False
                        def __call__(self):
                            foreign_calls.append("callback")
                            return ledger.tick()
                        def __add__(self, other):
                            foreign_calls.append("addition")
                            return 1
                    foreign = Foreign()
                    def callback():
                        if ledger.stage != "torque_projection":
                            return
                        visits.append(ledger.operations)
                        if len(visits) != selected:
                            return
                        if field == "external_check": work.external_check = foreign
                        elif field == "ledger_started": ledger.started = foreign
                        elif field == "work_started": work.started = foreign
                        elif field == "limits_owner": ledger._limits = dict(ledger._limits)
                        elif field == "limits_value": ledger._limits["max_operations"] = foreign
                        elif field == "work_operations": work.operations = foreign
                        elif field == "work_count": work.counts["exact_add"] = foreign
                        elif field == "event_kind": event.kind = foreign
                        elif field == "module_key": compiler.model.module_key = foreign
                        elif field == "element_id": compiler.model.objects["ball"].element_id = foreign
                        elif field == "context_hook": ledger._torque_context_guard = None
                        else: setattr(work, field, foreign)
                    ledger.check = callback
                    with self.assertRaises((OntoKinError, ValueError)):
                        source_intervals(compiler, "ball", compiler.budget)
                    self.assertEqual(len(visits), selected)
                    self.assertEqual(foreign_calls, [])
                    self.assertIs(ledger.check, callback)
                    self.assertIs(ledger._torque_context_guard, original_guard)
                    self.assertIs(work._source_after_charge, original_observer)

    def test_source_guard_chains_native_parent_and_preserves_original_exception(self):
        _, ledger, compiler = compile_frozen("p01-spin-up.files.json")
        seen, original = [], ledger._torque_context_guard
        def parent():
            self.assertIs(ledger._torque_context_guard, parent)
            seen.append("native-parent")
        ledger._torque_context_guard = parent
        before = ledger.operations
        records = source_intervals(compiler, "ball", compiler.budget)
        self.assertEqual(ledger.operations-before, 1+2*len(records))
        self.assertTrue(seen)
        self.assertIs(ledger._torque_context_guard, parent)
        sentinel = RuntimeError("original callback before source context refusal")
        def callback():
            if ledger.stage == "torque_projection":
                ledger._torque_context_guard = None
                raise sentinel
        ledger.check = callback
        with self.assertRaises(RuntimeError) as caught:
            source_intervals(compiler, "ball", compiler.budget)
        self.assertIs(caught.exception, sentinel)
        self.assertIs(ledger.callback_error, sentinel)
        self.assertIs(ledger._torque_context_guard, parent)
        self.assertIsNone(compiler.reach_work._source_after_charge)
        ledger._torque_context_guard = original

    def test_source_structural_callbacks_cannot_reset_native_numerical_receipt(self):
        for selected in (1, 2, 3, 4, 5):
            for changed in ("operations", "counts-clear", "counts-replace"):
                with self.subTest(callback=selected, changed=changed):
                    _, ledger, compiler = compile_frozen("p04-overlap.files.json")
                    work = compiler.reach_work
                    self.assertGreater(work.operations, 0)
                    self.assertTrue(work.counts)
                    visits = []
                    original_guard = ledger._torque_context_guard
                    original_observer = work._source_after_charge
                    def callback():
                        if ledger.stage != "torque_projection":
                            return
                        visits.append(ledger.operations)
                        if len(visits) != selected:
                            return
                        if changed == "operations": work.operations = 0
                        elif changed == "counts-clear": work.counts.clear()
                        else: work.counts = dict(work.counts)
                    ledger.check = callback
                    with self.assertRaises(OntoKinError) as caught:
                        source_intervals(compiler, "ball", compiler.budget)
                    self.assertEqual(caught.exception.diagnostic.details["budget_reason"], "execution_context_required")
                    self.assertEqual(len(visits), selected)
                    self.assertIs(ledger.check, callback)
                    self.assertIs(ledger._torque_context_guard, original_guard)
                    self.assertIs(work._source_after_charge, original_observer)


if __name__ == "__main__":
    unittest.main()
