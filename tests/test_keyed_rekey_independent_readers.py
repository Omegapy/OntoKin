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

    def test_published_unicode_overlay_preserves_historical_input_and_semantics(self):
        historical = load_fixtures(through_amendment="AMENDMENT-C086-001")
        current = self.fixtures
        name = "output-key-unicode"
        old_raw = case_payload(historical, name)["entry"]["source"].encode()
        new_raw = case_payload(current, name)["entry"]["source"].encode()
        self.assertEqual(new_raw, old_raw[:219] + '"café"'.encode() + old_raw[230:])
        self.assertEqual(old_raw[219:230], b'"caf\\u00e9"')
        self.assertEqual(current["original_expected"], historical["original_expected"])
        self.assertEqual(historical["input_roots"], {})
        self.assertEqual(set(current["input_roots"]), {name})
        self.assertEqual(len(historical["amendments"]), 1)
        self.assertEqual(len(current["amendments"]), 2)
        old_case, new_case = historical["cases"][name], current["cases"][name]
        for field in ("code", "category", "phase", "rule_ids", "message", "details"):
            self.assertEqual(old_case["expected_diagnostic"][field], new_case["expected_diagnostic"][field])
        for case_name in set(current["core_cases"]) - {name}:
            self.assertEqual(current["cases"][case_name], historical["cases"][case_name])
        with self.assertRaises(ReferenceError):
            load_fixtures(through_amendment="unpublished")

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


    def test_later_abstract_checks_keep_preinput_gate_and_exact_timeline_counters(self):
        trace, unused_case, unused_units, budget = self.empty_trace()
        case = self.fixtures["core_cases"]["reordered-output"]
        origin = case["source_rekey_records"][0]
        trace.update(case=case["name"], program_revision=case["program_revision"])
        current = trace["invocations"][0]
        current.update({key: copy.deepcopy(origin[key]) for key in ("expression", "input", "body")})
        keys = case["expected"]["body_key_order"]
        current.update(input_keys=keys, body_keys=keys, output_keys=case["expected"]["output_key_order"],
                       aggregate_rekey_records=[copy.deepcopy(origin)],
                       stored_leaf_rekey_records={key: [copy.deepcopy(value)] for key, value in
                                                 case["expected"]["root_selected_rekey_records"].items()})
        current["timeline"] = [{"event": "abstract_body"}, {"event": "evaluate_input"}, {"event": "admit_input"}]
        current["checkpoints"] = []
        first = current["abstract_body_checks"][0]
        for index, key in enumerate(keys):
            for event in ("keyed_rekey_iteration", "body", "keyed_rekey_key_validation", "keyed_rekey_collision"):
                current["timeline"].append({"event": event, "key": key})
                if event.startswith("keyed_rekey_"):
                    current["checkpoints"].append({"stage": event, "key": key,
                        "consumed_operations": len(current["checkpoints"]) + 1, "value_entries": 0})
                if event == "body":
                    check = copy.deepcopy(first)
                    check["effective_locals"] = copy.deepcopy(first["effective_locals"])
                    check.update(input_evaluations_started=1, input_admissions_completed=1,
                                 body_evaluations_started=index + 1, mask_observed=True)
                    for value in check["locals"].values():
                        value["known"] = True
                    current["abstract_body_checks"].append(check)
                    current["timeline"].append({"event": "abstract_body"})
        current["timeline"].append({"event": "keyed_rekey_publication", "key": None})
        current["checkpoints"].append({"stage": "keyed_rekey_publication", "key": None,
                                      "consumed_operations": 9, "value_entries": 0})
        units = source_units(case_payload(self.fixtures, case))
        # Synthetic reader input only: supplemental checks are not claimed product observations.
        check_execution_trace(trace, case, units, budget, self.fixtures)
        for mutation in ("no_preinput_check", "wrong_counter", "missing_mask", "drop_local", "unmatched_event"):
            wrong = copy.deepcopy(trace); observed = wrong["invocations"][0]
            if mutation == "no_preinput_check":
                observed["abstract_body_checks"].pop(0); observed["timeline"].pop(0)
            elif mutation == "wrong_counter":
                observed["abstract_body_checks"][1]["body_evaluations_started"] += 1
            elif mutation == "missing_mask":
                observed["abstract_body_checks"][1]["mask_observed"] = False
            elif mutation == "drop_local":
                observed["abstract_body_checks"][1]["locals"]["captured"] = {"type": "Int", "known": True}
            else:
                observed["timeline"].append({"event": "abstract_body"})
            with self.subTest(mutation=mutation):
                with self.assertRaises(ReferenceError):
                    check_execution_trace(wrong, case, units, budget, self.fixtures)

    def test_original_payload_entry_requires_the_source_bound_rename_chain(self):
        from tools.keyed_rekey_source_reference import original_keyed_entries, original_entry_matches_current_key
        case = self.fixtures["core_cases"]["rekey-then-map"]
        units = source_units(case_payload(self.fixtures, case))
        entry = next(row["location"] for row in original_keyed_entries(units).values() if row["key"] == "a")
        entry = {**entry, "filename": "main.ok"}
        selected = copy.deepcopy(case["source_rekey_records"][0])
        selected.update(old_key="a", new_key="ns.a", input_entry=entry)
        operand = selected["expression"]
        original_entry_matches_current_key(entry, "ns.a", units, operand, [selected])
        for mutation in ("missing", "wrong_old", "wrong_new", "unrelated_operand", "abbreviated_entry"):
            records, location, argument = [copy.deepcopy(selected)], copy.deepcopy(entry), copy.deepcopy(operand)
            if mutation == "missing": records = []
            elif mutation == "wrong_old": records[0]["old_key"] = "other"
            elif mutation == "wrong_new": records[0]["new_key"] = "other"
            elif mutation == "unrelated_operand": argument = copy.deepcopy(selected["body"])
            else: location["end_byte"] -= 1
            with self.subTest(mutation=mutation):
                with self.assertRaises(ReferenceError):
                    original_entry_matches_current_key(location, "ns.a", units, argument, records)

    def test_result_selection_and_dependency_ids_come_from_original_declarations(self):
        from tools.keyed_rekey_source_reference import result_rekey_expression, core_member_source_identity
        case = self.fixtures["core_cases"]["captured-rekey-inside-body"]
        units = source_units(case_payload(self.fixtures, case))
        resolved = result_rekey_expression(case, units)
        self.assertEqual(resolved["start_byte"], 278)
        self.assertNotEqual(resolved, case["source_rekey_records"][0]["expression"])
        dependency_case = self.fixtures["core_cases"]["explicit-namespace-map"]
        dependency_units = source_units(case_payload(self.fixtures, dependency_case))
        self.assertEqual(core_member_source_identity(dependency_units, "shape", "items"),
                         ["probe", "demo", "shape", "items"])
        with self.assertRaises(ReferenceError):
            core_member_source_identity(dependency_units, "shape", "not_declared")

    def test_inherited_public_span_keeps_its_exact_file_envelope(self):
        from tools.keyed_rekey_source_reference import exact_public_location
        case = self.fixtures["core_cases"]["singleton"]
        units = source_units(case_payload(self.fixtures, case))
        expected = case["source_rekey_records"][0]["input"]
        actual = {("file" if key == "filename" else key): value for key, value in expected.items()}
        exact_public_location(actual, expected, units)
        for wrong in ({**actual, "extra": "invented"}, {**actual, "file": "other.ok"},
                      {**actual, "start_byte": actual["start_byte"] + 1}, expected):
            with self.subTest(wrong=wrong):
                with self.assertRaises(ReferenceError):
                    exact_public_location(wrong, expected, units)

    def test_empty_literal_control_has_source_derived_empty_keyset(self):
        from tools.keyed_rekey_source_reference import literal_control_keys
        case = self.fixtures["core_cases"]["empty-captured-zero-not-evaluated"]
        units = source_units(case_payload(self.fixtures, case, control=True))
        self.assertEqual(literal_control_keys(units), [])

    def test_atomic_edit_replay_requires_original_utf8_preconditions(self):
        from tools.verify_keyed_rekey_agent_evidence import replay_edit, normalized
        from tools.keyed_rekey_reference import bundle_identity, digest
        before = case_payload(self.fixtures, "panel-task")
        after = case_payload(self.fixtures, "panel-task-repaired")
        spec = self.fixtures["workflows"]["workflows"][0]["expected"]["repair_patches"][0]
        raw = before["entry"]["source"].encode(); target = spec["expected_text"].encode(); offset = raw.index(target)
        request = {"expected_program_revision": bundle_identity(before)[0], "patches": [{"source_id": "entry",
            "element_id": ["sources", "entry"], "source_revision": digest(raw), "start_byte": offset,
            "end_byte": offset + len(target), **spec}]}
        self.assertEqual(replay_edit(before, request), normalized(after))
        for change in ("source_revision", "expected_text", "overlap"):
            wrong = copy.deepcopy(request)
            if change == "source_revision":
                wrong["patches"][0]["source_revision"] = "sha256:" + "0" * 64
            elif change == "expected_text":
                wrong["patches"][0]["expected_text"] += " "
            else:
                wrong["patches"].append(copy.deepcopy(wrong["patches"][0]))
            with self.subTest(change=change):
                with self.assertRaises(ReferenceError):
                    replay_edit(before, wrong)


if __name__ == "__main__":
    unittest.main()
