"""Producer-boundary checks; these do not certify filtering or its oracle."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import run_keyed_filter_acceptance as producer


class RecordingContext:
    def __init__(self, policy, profile):
        self.policy, self.profile = policy, profile
        self.execution_budget = SimpleNamespace(report=lambda **values: values)


class KeyedFilterProducerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = producer.load_fixtures(producer.ROOT / "examples/keyed-filter")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.driver = producer.Acceptance.__new__(producer.Acceptance)
        self.driver.fixtures = self.fixtures
        self.driver.output = Path(self.temporary.name)

    def payload(self, name):
        return producer.case_payload(self.fixtures, self.fixtures["cases"][name])

    def test_repair_exactly_reproduces_frozen_membership_change(self):
        before, after = self.payload("panel-task"), self.payload("panel-task-repaired")
        request = self.driver.repair_fields(before, after)
        self.assertEqual(request["expected_program_revision"],
                         self.fixtures["cases"]["panel-task"]["program_revision"])
        self.assertEqual(request["requested_level"], "constructed")
        self.assertEqual(len(request["patches"]), 1)
        change = request["patches"][0]
        raw = before["entry"]["source"].encode("utf-8")
        self.assertEqual(change["source_id"], "entry")
        self.assertEqual(change["element_id"], ["sources", "entry"])
        self.assertEqual(change["source_revision"], producer.digest(raw))
        self.assertEqual(raw[change["start_byte"]:change["end_byte"]],
                         b"minimum_width = 0[m];")
        patched = (raw[:change["start_byte"]] + change["replacement"].encode("utf-8")
                   + raw[change["end_byte"]:])
        self.assertEqual(patched, after["entry"]["source"].encode("utf-8"))
        self.assertEqual(before["modules"], after["modules"])
        self.assertEqual(before["assets"], after["assets"])
        self.assertEqual(producer.PANEL_ID[-1], "right")

    def test_repair_rejects_unrelated_entry_library_or_asset_changes(self):
        before, after = self.payload("panel-task"), self.payload("panel-task-repaired")
        for part in ("entry", "modules", "assets"):
            candidate = copy.deepcopy(after)
            if part == "entry":
                candidate[part]["source"] += "\n// unrelated change\n"
            elif part == "modules":
                candidate[part][0]["source"] += "\n// unrelated change\n"
            else:
                candidate[part][0]["data_base64"] = "AA=="
            with self.subTest(part=part), self.assertRaises(AssertionError):
                self.driver.repair_fields(before, candidate)

    def test_repair_refuses_missing_or_ambiguous_authored_scope(self):
        after = self.payload("panel-task-repaired")
        for repeated in (False, True):
            before = self.payload("panel-task")
            old = "minimum_width = 0[m];"
            if repeated:
                before["entry"]["source"] += "\n// " + old + "\n"
            else:
                before["entry"]["source"] = before["entry"]["source"].replace(old, "minimum_width = 1[m];")
            with self.subTest(repeated=repeated), self.assertRaises(AssertionError):
                self.driver.repair_fields(before, after)

    def test_constructed_refusal_is_requested_at_its_frozen_stage(self):
        case = self.fixtures["cases"]["invalid-resulting-geometry"]
        payload = self.payload(case["name"])
        source = SimpleNamespace(program_revision=case["program_revision"],
                                 entry=SimpleNamespace(raw=payload["entry"]["source"].encode()))
        calls = []
        runtime = SimpleNamespace(validate_revision=lambda source, **kwargs:
            calls.append(kwargs) or {"outcome": "invalid"})
        self.driver.Runtime = lambda: runtime
        self.driver.HostPolicy = lambda **policy: policy
        with patch.object(producer, "SourceContext", RecordingContext):
            self.driver.source_observation(source, case, "constructed")
        self.assertEqual(calls[0]["level"], "constructed")
        receipt = json.loads((self.driver.output / "constructed.receipt.json").read_bytes())
        self.assertEqual(receipt["requested_level"], "constructed")
        self.assertEqual(receipt["program_revision"], case["program_revision"])

    def test_older_importer_uses_actual_declaring_unit_binding(self):
        # This is a real unchanged .15 public call. Routing it to the .16
        # runtime would hide the intended import refusal behind entry admission.
        from ontokin.execution_budget import HostPolicy
        from ontokin.keyed_reduction_program_runtime import KeyedReductionProgramRuntime
        from ontokin.texture_bundle import load_texture_file_manifest
        case = self.fixtures["cases"]["older-importer-rejects-new-unit"]
        source = load_texture_file_manifest(self.fixtures["root"] / case["file_manifest"])
        self.driver.Runtime = lambda: self.fail("The .15 entry must use its own runtime")
        self.driver.ControlRuntime = KeyedReductionProgramRuntime
        self.driver.HostPolicy = HostPolicy
        result = self.driver.source_observation(source, case, "older-importer")
        self.assertNotEqual(result["outcome"], "valid")
        self.assertIn(case["expected_code"], producer.codes(result))
        receipt = json.loads((self.driver.output / "older-importer.receipt.json").read_bytes())
        self.assertEqual(receipt["profile"], "keyed-reduction-0.1")
        self.assertEqual(receipt["public_api"], "KeyedReductionProgramRuntime.validate_revision")

    def test_inspection_keeps_generated_siblings_and_refuses_incomplete_rows(self):
        case = self.fixtures["cases"]["equal-valued-plain-filtered-occurrences"]
        source = SimpleNamespace(program_revision=case["program_revision"])
        calls = []
        result = {"outcome": "valid", "items": [{"path": "first"}, {"path": "sibling"}]}
        runtime = SimpleNamespace(inspect_revision=lambda source, **kwargs:
            calls.append(kwargs) or result)
        self.driver.Runtime = lambda: runtime
        self.driver.HostPolicy = lambda **policy: policy
        with patch.object(producer, "SourceContext", RecordingContext):
            path = self.driver.inspect_source(source, case, "complete")
            self.assertEqual(calls[0]["selector"], {"kind": "object"})
            self.assertEqual(json.loads((self.driver.output / path).read_bytes()), result)
            result["truncated"] = True
            result["next_cursor"] = "actual-next-page"
            with self.assertRaises(AssertionError):
                self.driver.inspect_source(source, case, "incomplete")
        retained = json.loads((self.driver.output / "incomplete.inspection.json").read_bytes())
        self.assertTrue(retained["truncated"])

    def test_observer_preserves_callback_exception_and_restores_original_hooks(self):
        from ontokin.construction import ConstructionCompiler
        from ontokin.execution_budget import HostPolicy
        context = producer.SourceContext(HostPolicy(), producer.PROFILE)
        class HostCancellation(BaseException):
            pass
        sentinel = HostCancellation("the host's exact cancellation")
        def original_poll():
            raise sentinel
        context.execution_budget.check = original_poll
        original_expression = ConstructionCompiler.expression
        with self.assertRaises(HostCancellation) as raised:
            with producer.FilterExecutionObserver(context) as observer:
                context.execution_budget.tick()
        self.assertIs(raised.exception, sentinel)
        self.assertIs(context.execution_budget.callback_error, sentinel)
        self.assertIs(context.execution_budget.check, original_poll)
        self.assertIs(ConstructionCompiler.expression, original_expression)
        self.assertEqual(context.execution_budget.operations, 0)
        self.assertEqual(observer.invocations, [])


if __name__ == "__main__":
    unittest.main()
