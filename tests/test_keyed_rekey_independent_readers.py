"""Independent-reader rejection tests; no candidate compiler/runtime imports."""
from __future__ import annotations
import copy
import unittest

from tools.keyed_rekey_reference import (
    FREEZE_COMMIT, FREEZE_SHA256, PROFILE, ReferenceError, load_fixtures,
    case_payload, source_units, check_rekeys, input_lineage,
)
from tools.keyed_rekey_delivery_reference import (
    expected_source_projection, panel_sources, panel_zip_records,
)
from tools.verify_keyed_rekey import check_execution_trace


class IndependentRekeyReaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixtures()

    def test_all_authored_valid_rekey_records_have_original_source_roles(self):
        count = 0
        for case in self.fixtures["core_cases"].values():
            if case["expected_outcome"] != "valid":
                continue
            units = source_units(case_payload(self.fixtures, case))
            for record in case["source_rekey_records"]:
                check_rekeys([record], units, aggregate=True)
                count += 1
        self.assertEqual(count, 120)

    def test_published_point3_overlay_preserves_original_expectations(self):
        original = {case["name"]: case for case in self.fixtures["original_expected"]["cases"]}
        for name in ("leaf-point3-empty", "leaf-point3-identity", "leaf-point3-renamed"):
            self.assertEqual(original[name]["source_rekey_records"][0]["element_type"], "Point3")
            self.assertEqual(self.fixtures["core_cases"][name]["source_rekey_records"][0]["element_type"], "Point3<Length>")
        self.assertNotEqual(self.fixtures["original_expected_sha256"], self.fixtures["effective_expected_sha256"])

    def test_selected_origins_reject_identity_fields_swaps_and_shifted_spans(self):
        case = self.fixtures["core_cases"]["nested-rekey"]
        units = source_units(case_payload(self.fixtures, case))
        wanted = case["expected"]["exact_public_selected_rekey_records"]["c"]
        check_rekeys(wanted, units, expected=wanted, exact=True)
        alternatives = []
        wrong = copy.deepcopy(wanted); wrong[-1]["element_id"] = ["invented"]; alternatives.append(wrong)
        wrong = copy.deepcopy(wanted); wrong[-1]["old_key"], wrong[-1]["new_key"] = wrong[-1]["new_key"], wrong[-1]["old_key"]; alternatives.append(wrong)
        wrong = copy.deepcopy(wanted); wrong[-1]["input_entry"]["start_byte"] += 1; alternatives.append(wrong)
        wrong = copy.deepcopy(wanted); wrong[-1]["body"]["start_byte"] += 1; alternatives.append(wrong)
        wrong = copy.deepcopy(wanted); wrong[0], wrong[1] = wrong[1], wrong[0]; alternatives.append(wrong)
        wrong = copy.deepcopy(wanted); wrong[0]["new_key"] = "invented"; alternatives.append(wrong)
        for wrong in alternatives:
            with self.subTest(wrong=wrong):
                with self.assertRaises(ReferenceError):
                    check_rekeys(wrong, units, expected=wanted, exact=True)

    def test_generated_key_identity_and_original_zip_key_are_separate(self):
        case = self.fixtures["agent_cases"]["panel-task-repaired"]
        projection = expected_source_projection(case, self.fixtures)
        occurrence = projection["occurrences"]['first.panels["front.left"]']
        self.assertEqual(occurrence["element_id"], ["panel-task", "demo", "first", "panels", "front.left"])
        self.assertNotIn('first.panels["left"]', projection["occurrences"])
        selected = occurrence["generated"]["input_rekeys"][-1]
        self.assertEqual((selected["old_key"], selected["new_key"]), ("left", "front.left"))
        self.assertEqual(selected["input_entry"]["source_id"], "package:fixture.rekey-catalog@1.0.0")
        self.assertEqual(occurrence["generated"]["input_zips"][-1]["key"], "left")
        self.assertEqual(projection["occurrences"]['sibling.panels["left"]']["generated"]["input_rekeys"][-1]["new_key"], "left")

    def test_control_primary_entries_resolve_only_selected_literal_branches(self):
        case = self.fixtures["agent_cases"]["panel-task-repaired"]
        projection = expected_source_projection(case, self.fixtures, control=True)
        first = projection["occurrences"]['first.panels["front.left"]']["generated"]["input_entry"]
        sibling = projection["occurrences"]['sibling.panels["left"]']["generated"]["input_entry"]
        units = source_units(case_payload(self.fixtures, case, control=True))
        for value, expected in ((first, b'"front.left":"left"'), (sibling, b'"left":"left"')):
            raw = units[value["source_id"]]["source"].encode()
            self.assertEqual(raw[value["start_byte"]:value["end_byte"]], expected)

    def empty_trace(self):
        case = self.fixtures["core_cases"]["empty"]
        origin = case["source_rekey_records"][0]
        binders = case["source_rekey_binders"][0]
        locals_ = {name: {"type": typ, "known": False} for name, typ in zip(binders["names"], binders["types"])}
        policy = {"max_operations": 100000, "max_elapsed_ms": 30000}
        budget = {"consumed_operations": 10, "effective": policy, "host_ceilings": policy}
        record = {key: copy.deepcopy(origin[key]) for key in ("expression", "input", "body")}
        record.update(self_path="shape", input_evaluations=1, input_admissions=1, input_keys=[], input_type="Keyed<Int>",
            body_keys=[], output_keys=[], output_type="Keyed<Int>", operations_before=0, operations_after=10,
            value_entries_before=0, value_entries_after=1,
            abstract_body_checks=[{"input_evaluations_started": 0, "input_admissions_completed": 0,
                "body_evaluations_started": 0, "locals": locals_, "effective_locals": locals_, "mask_observed": False}],
            timeline=[{"event": "abstract_body"}, {"event": "evaluate_input"}, {"event": "admit_input"},
                      {"event": "keyed_rekey_publication", "key": None}],
            checkpoints=[{"stage": "keyed_rekey_publication", "key": None, "consumed_operations": 9, "value_entries": 0}],
            aggregate_rekey_records=[copy.deepcopy(origin)], stored_leaf_rekey_records={},
            snapshot_ledger={"operations_before": 10, "operations_after": 10, "value_entries_before": 1, "value_entries_after": 1})
        trace = {"schema_version": "ontokin.c086-rekey-execution-observation/0.1", **input_lineage(self.fixtures),
            "case": case["name"], "program_revision": case["program_revision"], "profile": PROFILE,
            "public_api": "KeyedRekeyProgramRuntime.validate_revision", "requested_level": "represented",
            "invocations": [record], "execution_budget": budget}
        return trace, case, source_units(case_payload(self.fixtures, case)), budget

    def test_empty_trace_requires_real_publication_and_unchanged_private_observation(self):
        trace, case, units, budget = self.empty_trace()
        # Synthetic reader input only: this is not a product execution/pass.
        check_execution_trace(trace, case, units, budget, self.fixtures)
        for change in ("omit_publication", "repeat_input", "charge_snapshot", "known_local", "body_before_admission"):
            wrong = copy.deepcopy(trace); record = wrong["invocations"][0]
            if change == "omit_publication":
                record["timeline"].pop(); record["checkpoints"].clear()
            elif change == "repeat_input":
                record["input_evaluations"] = 2
            elif change == "charge_snapshot":
                record["snapshot_ledger"]["operations_after"] += 1
            elif change == "known_local":
                record["abstract_body_checks"][0]["effective_locals"]["payload"]["known"] = True
            else:
                record["timeline"].insert(2, {"event": "body", "key": "invented"})
            with self.subTest(change=change):
                with self.assertRaises(ReferenceError):
                    check_execution_trace(wrong, case, units, budget, self.fixtures)


if __name__ == "__main__":
    unittest.main()
