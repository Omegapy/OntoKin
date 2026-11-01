"""Adversarial checks of the parser-free C084 readers, using frozen sources.

These are synthetic projection/receipt tests, not compiler execution evidence.
No production OntoKin module is imported and no expected fixture is rewritten.
"""
from copy import deepcopy
import unittest

from tools.keyed_merge_reference import (ReferenceError, case_payload, check_merges,
    check_panel_transforms, diagnostic_anchor, load_fixtures, merge_source_shape,
    panel_transform, source_units)
from tools.verify_keyed_merge import check_execution_trace, requires_execution_trace


class IndependentMergeReaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixtures()

    def source(self, name):
        case = self.fixtures["cases"][name]
        return case, source_units(case_payload(self.fixtures, case))

    @staticmethod
    def runtime_records(records, units):
        return [{**deepcopy(record), **{part: {**record[part], "filename": units[record[part]["source_id"]]["filename"]}
                                       for part in ("expression", "left", "right")}}
                for record in records]

    def test_all_valid_source_shapes_are_independently_recoverable(self):
        count = 0
        for case in self.fixtures["cases"].values():
            if case["expected_outcome"] != "valid":
                continue
            units = source_units(case_payload(self.fixtures, case))
            for record in case["source_merge_records"]:
                with self.subTest(case=case["name"], expression=record["expression"]):
                    actual = merge_source_shape(record["expression"], units)
                    self.assertEqual(actual["parts"], {part: record[part] for part in ("left", "right")})
                    self.assertEqual(actual["element_type"], record["element_type"])
                    check_merges(self.runtime_records([record], units), units, expected=[record], exact=True)
                    count += 1
        self.assertGreater(count, 79)

    def test_grouped_outer_expression_is_complete(self):
        case, units = self.source("nested-merge-indexed-scalar")
        outer = case["source_merge_records"][0]["expression"]
        raw = units[outer["source_id"]]["source"].encode()[outer["start_byte"]:outer["end_byte"]]
        self.assertTrue(raw.startswith(b"(merge_keyed<"))
        self.assertTrue(raw.endswith(b"))"))
        shortened = {**outer, "start_byte": outer["start_byte"] + 1, "end_byte": outer["end_byte"] - 1}
        records = self.runtime_records(case["expected"]["derived_merges_exact"], units)
        records[1]["expression"].update(shortened)
        with self.assertRaises(ReferenceError):
            check_merges(records, units, expected=case["expected"]["derived_merges_exact"], exact=True)

    def test_closed_record_locations_types_and_sides(self):
        case, units = self.source("singleton-pair")
        expected = case["source_merge_records"]
        baseline = self.runtime_records(expected, units)
        mutations = []
        value = deepcopy(baseline); value[0]["ordinal"] = 1; mutations.append(value)
        value = deepcopy(baseline); value[0]["left"]["unadopted"] = True; mutations.append(value)
        value = deepcopy(baseline); del value[0]["right"]["filename"]; mutations.append(value)
        value = deepcopy(baseline); value[0]["right"]["filename"] = "other.ok"; mutations.append(value)
        value = deepcopy(baseline); value[0]["input_side"] = "either"; mutations.append(value)
        value = deepcopy(baseline); value[0]["element_type"] = "Real"; mutations.append(value)
        value = deepcopy(baseline); value[0]["left"], value[0]["right"] = value[0]["right"], value[0]["left"]; mutations.append(value)
        mutations.append(baseline + deepcopy(baseline))
        for number, value in enumerate(mutations):
            with self.subTest(mutation=number), self.assertRaises(ReferenceError):
                check_merges(value, units, expected=expected, exact=True)

    def test_nested_aggregate_and_contribution_order_is_semantic(self):
        case, units = self.source("nested-merge-indexed-scalar")
        expected = case["expected"]["derived_merges_exact"]
        baseline = self.runtime_records(expected, units)
        check_merges(baseline, units, expected=expected, exact=True)
        reordered = deepcopy(baseline)
        reordered[0], reordered[2] = reordered[2], reordered[0]
        self.assertCountEqual(reordered, baseline)
        with self.assertRaises(ReferenceError):
            check_merges(reordered, units, expected=expected, exact=True)
        wrong_side = deepcopy(baseline); wrong_side[-1]["input_side"] = "right"
        with self.assertRaises(ReferenceError):
            check_merges(wrong_side, units, expected=expected, exact=True)

    def test_unrelated_aggregate_map_cannot_borrow_contributor_key(self):
        case, units = self.source("panel-task")
        maps = panel_transform(case, self.fixtures)
        records = []
        for source in maps:
            record = {name: deepcopy(source[name]) for name in (
                "expression", "input", "body", "input_element_type", "output_element_type")}
            for field in ("expression", "input", "body"):
                record[field]["filename"] = units[record[field]["source_id"]]["filename"]
            records.append(record)
        check_panel_transforms(records, maps, units, require_both=True)
        counterfeit = deepcopy(records)
        counterfeit[1].update(key="left", input_entry={**maps[0]["original_key_entries"]["left"], "filename": "panels.ok"})
        with self.assertRaises(ReferenceError):
            check_panel_transforms(counterfeit, maps, units, require_both=True)

    @staticmethod
    def diagnostic(case, units):
        def location(value):
            return {**value, "file": units[value["source_id"]]["filename"], "element_id": None}
        return {"code": case["expected_code"], "primary": location(case["diagnostic_anchor"]),
                "related": [location(value) for value in case.get("diagnostic_related", [])],
                **{field: case["diagnostic_" + field] for field in ("category", "phase", "rule_ids", "details")}}

    def test_new_collision_diagnostic_is_exact(self):
        case, units = self.source("collision-equal-values")
        baseline = self.diagnostic(case, units)
        diagnostic_anchor({"diagnostics": [baseline]}, case, units)
        for field, value in (("details", {"operation": "merge_keyed", "key": "another"}),
                             ("phase", "type"), ("related", []), ("category", "unsupported"),
                             ("rule_ids", ["LANG-003"])):
            changed = deepcopy(baseline); changed[field] = value
            with self.subTest(field=field), self.assertRaises(ReferenceError):
                diagnostic_anchor({"diagnostics": [changed]}, case, units)
        changed = deepcopy(baseline); changed["primary"]["end_byte"] += 1
        with self.assertRaises(ReferenceError):
            diagnostic_anchor({"diagnostics": [changed]}, case, units)

    def test_inherited_anchor_is_containment_not_new_token_contract(self):
        case = next(case for case in self.fixtures["cases"].values()
                    if case.get("diagnostic_anchor_mode") == "contains_token")
        units = source_units(case_payload(self.fixtures, case))
        location = {**case["diagnostic_anchor"], "file": units[case["diagnostic_anchor"]["source_id"]]["filename"],
                    "element_id": None}
        location["end_byte"] += 1
        diagnostic_anchor({"diagnostics": [{"code": case["expected_code"], "primary": location}]}, case, units)

    def test_trace_observation_rejects_reordered_admission_and_fabricated_keys(self):
        case, units = self.source("singleton-pair")
        origin, expected = case["source_merge_records"][0], case["expected"]
        right, output = expected["collision_key_order"], expected["materialization_key_order"]
        visits = [("keyed_merge_collision", key) for key in right] + [("keyed_merge_iteration", key) for key in output]
        budget = {"consumed_operations": 20, "host_ceilings": case["host_policy"], "effective": case["host_policy"]}
        invocation = {**{part: origin[part] for part in ("expression", "left", "right")}, "self_path": "shape",
            "left_input_evaluations": 1, "right_input_evaluations": 1,
            "left_input_admissions": 1, "right_input_admissions": 1,
            "dynamic_input_order": ["left", "right"], "admission_order": ["left", "right"],
            "input_events": ["evaluate_left", "admit_left", "evaluate_right", "admit_right"],
            "left_keys": sorted(set(output) - set(right)), "right_keys": right, "output_keys": output,
            "collision_keys": right, "materialization_keys": output,
            "left_type": case["probe"]["type"], "right_type": case["probe"]["type"], "output_type": case["probe"]["type"],
            "operations_before": 1, "operations_after": 10, "value_entries_before": 0, "value_entries_after": 10,
            "checkpoints": [{"stage": stage, "key": key, "consumed_operations": index + 3, "value_entries": index}
                            for index, (stage, key) in enumerate(visits)]}
        trace = {"schema_version": "ontokin.c084-merge-execution-observation/0.1", "case": case["name"],
                 "program_revision": case["program_revision"], "profile": "keyed-merge-0.1", "requested_level": "represented",
                 "public_api": "KeyedMergeProgramRuntime.validate_revision", "invocations": [invocation], "execution_budget": budget}
        self.assertTrue(requires_execution_trace(case))
        check_execution_trace(trace, case, units, budget)
        changed = deepcopy(trace); changed["invocations"][0]["input_events"] = ["evaluate_left", "evaluate_right", "admit_left", "admit_right"]
        with self.assertRaises(ReferenceError):
            check_execution_trace(changed, case, units, budget)
        changed = deepcopy(trace); changed["invocations"][0]["checkpoints"][0]["key"] = "invented"
        with self.assertRaises(ReferenceError):
            check_execution_trace(changed, case, units, budget)


if __name__ == "__main__":
    unittest.main()
