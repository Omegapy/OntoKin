"""Adversarial tests of the parser-free C085 evidence readers.

All examples come from separately frozen source inputs or explicit synthetic
receipts. These tests import no compiler/runtime and produce no release proof.
"""
from copy import deepcopy
import json
import unittest

from tools.keyed_zip_reference import (
    ReferenceError, case_payload, check_zip_leaf_provenance, check_zips,
    diagnostic_anchor, enriched_zip_records, load_fixtures, panel_sources,
    paired_panel_merges, primary_panel_entry, sha, source_units, zip_source_shape)
from tools.verify_keyed_zip import check_execution_trace, requires_execution_trace


class IndependentZipReaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = load_fixtures()

    def source(self, name):
        case = self.fixtures["cases"][name]
        return case, source_units(case_payload(self.fixtures, case))

    def test_published_amendments_are_detached_from_original_bytes(self):
        fixtures = self.fixtures
        original = (fixtures["root"] / "expected.json").read_bytes()
        self.assertEqual(sha(original), fixtures["original_expected_sha256"])
        self.assertEqual(json.loads(original), fixtures["original_expected"])
        self.assertNotEqual(fixtures["expected"], fixtures["original_expected"])
        self.assertEqual(sha((json.dumps(fixtures["expected"], indent=2)+"\n").encode()),
                         fixtures["effective_expected_sha256"])
        changes = []
        def compare(left, right, path=()):
            if isinstance(left, dict):
                self.assertEqual(left.keys(), right.keys())
                for key in left:
                    compare(left[key], right[key], path+(key,))
            elif isinstance(left, list):
                self.assertEqual(len(left), len(right))
                for index, (a, b) in enumerate(zip(left, right)):
                    compare(a, b, path+(index,))
            elif left != right:
                changes.append((path, left, right))
        compare(fixtures["original_expected"], fixtures["expected"])
        self.assertEqual(len(changes), 44)
        self.assertEqual({p[-1] for p, _, _ in changes}, {"start_byte", "end_byte"})
        self.assertTrue(all(b-a == (-1 if p[-1] == "start_byte" else 1) for p, a, b in changes))

    def test_all_valid_source_triples_binders_and_spans_are_recoverable(self):
        count = 0
        for case in self.fixtures["cases"].values():
            if case["expected_outcome"] != "valid":
                continue
            units = source_units(case_payload(self.fixtures, case))
            for record in case["source_zip_records"]:
                with self.subTest(case=case["name"], expression=record["expression"]):
                    shape = zip_source_shape(record["expression"], units)
                    self.assertEqual(shape["parts"], {part:record[part] for part in ("left", "right", "body")})
                    for part in ("left_element_type", "right_element_type", "output_element_type"):
                        self.assertEqual(shape[part], record[part])
                    check_zips(enriched_zip_records([record], units), units,
                               expected=[record], exact=True, aggregate=True)
                    count += 1
        self.assertGreaterEqual(count, 160)

    def test_exact_ten_fields_and_five_location_fields_are_closed(self):
        case, units = self.source("singleton-add")
        wanted = [case["expected"]["paired_entry_zip_records_exact"]["a"]]
        baseline = enriched_zip_records(wanted, units)
        check_zips(baseline, units, expected=wanted, exact=True)
        mutations = []
        for field in ("key", "left_entry", "right_entry", "output_element_type"):
            value = deepcopy(baseline); del value[0][field]; mutations.append(value)
        value = deepcopy(baseline); value[0]["ordinal"] = 1; mutations.append(value)
        value = deepcopy(baseline); value[0]["left"]["unadopted"] = True; mutations.append(value)
        value = deepcopy(baseline); del value[0]["right"]["filename"]; mutations.append(value)
        value = deepcopy(baseline); value[0]["right"]["filename"] = "other.ok"; mutations.append(value)
        value = deepcopy(baseline); value[0]["key"] = "b"; mutations.append(value)
        value = deepcopy(baseline); value[0]["output_element_type"] = "Real"; mutations.append(value)
        value = deepcopy(baseline); value[0]["left"], value[0]["right"] = value[0]["right"], value[0]["left"]; mutations.append(value)
        value = deepcopy(baseline); value[0]["left_entry"], value[0]["right_entry"] = value[0]["right_entry"], value[0]["left_entry"]; mutations.append(value)
        mutations.append(baseline + deepcopy(baseline))
        for index, value in enumerate(mutations):
            with self.subTest(mutation=index), self.assertRaises(ReferenceError):
                check_zips(value, units, expected=wanted, exact=True)

    def test_complete_original_entry_not_key_token_or_partial_value(self):
        case, units = self.source("singleton-add")
        records = enriched_zip_records([case["expected"]["paired_entry_zip_records_exact"]["a"]], units)
        for end in (records[0]["left_entry"]["start_byte"]+3, records[0]["left_entry"]["end_byte"]-1):
            value = deepcopy(records); value[0]["left_entry"]["end_byte"] = end
            with self.subTest(end=end), self.assertRaises(ReferenceError):
                check_zips(value, units)

    def test_aggregate_cannot_invent_contributors(self):
        case, units = self.source("singleton-add")
        aggregate = enriched_zip_records(case["expected"]["aggregate_zip_records_exact"], units)
        paired = enriched_zip_records([case["expected"]["paired_entry_zip_records_exact"]["a"]], units)[0]
        for changes in ({"key":"a"}, {"left_entry":paired["left_entry"]},
                        {"key":"a", "left_entry":paired["left_entry"], "right_entry":paired["right_entry"]}):
            value = deepcopy(aggregate); value[0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ReferenceError):
                check_zips(value, units, aggregate=True)

    def test_nested_public_projection_is_aggregate_then_private_exact_order(self):
        case, units = self.source("nested-left-zip")
        expected = case["expected"]
        aggregate = enriched_zip_records(expected["aggregate_zip_records_exact"], units)
        entries = []
        for key, private in expected["stored_leaf_zips_exact"].items():
            combined = []
            for record in aggregate+enriched_zip_records(private, units):
                if record not in combined:
                    combined.append(record)
            entries.append({"key":key, "value":{"derived_zips":combined}})
        value = {"derived_zips":aggregate, "value":entries}
        self.assertEqual(check_zip_leaf_provenance(value, units, expected), 2)
        private_only = deepcopy(value)
        private_only["value"][0]["value"]["derived_zips"] = enriched_zip_records(expected["stored_leaf_zips_exact"]["a"], units)
        with self.assertRaises(ReferenceError):
            check_zip_leaf_provenance(private_only, units, expected)
        reversed_projection = deepcopy(value)
        records = reversed_projection["value"][0]["value"]["derived_zips"]
        records[0], records[2] = records[2], records[0]
        with self.assertRaises(ReferenceError):
            check_zip_leaf_provenance(reversed_projection, units, expected)

    def test_grouped_lambda_body_keeps_amended_parentheses(self):
        case, units = self.source("zip-inside-zip-body")
        grouped = next(record for record in case["source_zip_records"]
                       if units[record["expression"]["source_id"]]["source"].encode()[record["expression"]["start_byte"]:][:1] == b"(")
        records = enriched_zip_records([grouped], units)
        records[0]["expression"]["start_byte"] += 1
        records[0]["expression"]["end_byte"] -= 1
        with self.assertRaises(ReferenceError):
            check_zips(records, units, expected=[grouped], exact=True)

    def test_panel_inherited_order_is_whole_inputs_then_selected_leaves(self):
        case, units = self.source("panel-task")
        sources = panel_sources(case, self.fixtures)
        names = {sources[role]["record"]["expression"]["source_id"]:role for role in ("dimensions", "finishes")}
        pairs = lambda values:[(names[x["expression"]["source_id"]], x["input_side"]) for x in values]
        self.assertEqual(pairs(paired_panel_merges(sources)), [
            ("dimensions","both"),("finishes","both"),("dimensions","right"),
            ("dimensions","left"),("finishes","left"),("finishes","right")])
        self.assertEqual(pairs(paired_panel_merges(sources, key="left", stored_leaf=True)), [
            ("dimensions","both"),("finishes","both"),("dimensions","right"),("finishes","left")])
        actual = primary_panel_entry(case, self.fixtures, "left")
        control = primary_panel_entry(case, self.fixtures, "left", control=True)
        self.assertEqual(actual["source_id"], "package:fixture.pair-dimensions@1.0.0")
        self.assertEqual(control["source_id"], "package:fixture.pair-panels@1.0.0")
        # Frozen locators carry four coordinates; the canonical manifest
        # supplies the fifth runtime field, whose exact comparison is required.
        enriched = {**actual, "filename":units[actual["source_id"]]["filename"]}
        self.assertEqual(set(enriched), {"source_id","source_revision","filename","start_byte","end_byte"})

    @staticmethod
    def diagnostic(case, units):
        def location(value):
            return {**value, "file":units[value["source_id"]]["filename"], "element_id":None}
        return {"code":case["expected_code"], "primary":location(case["diagnostic_anchor"]),
                "related":[location(value) for value in case.get("diagnostic_related", [])],
                **{field:case["diagnostic_"+field] for field in ("category","phase","rule_ids","details")}}

    def test_missing_side_diagnostic_is_exact_and_asymmetric(self):
        for name in ("left-empty-right-one", "right-empty-left-one", "grouped-missing-left"):
            case, units = self.source(name)
            baseline = self.diagnostic(case, units)
            diagnostic_anchor({"diagnostics":[baseline]}, case, units)
            mutations = []
            value = deepcopy(baseline); value["details"]["missing_side"] = "left" if value["details"]["missing_side"] == "right" else "right"; mutations.append(value)
            value = deepcopy(baseline); value["primary"], value["related"][0] = value["related"][0], value["primary"]; mutations.append(value)
            value = deepcopy(baseline); value["primary"]["end_byte"] += 1; mutations.append(value)
            value = deepcopy(baseline); value["related"] = []; mutations.append(value)
            value = deepcopy(baseline); value["phase"] = "type"; mutations.append(value)
            value = deepcopy(baseline); value["details"]["ordinal"] = 0; mutations.append(value)
            for index, value in enumerate(mutations):
                with self.subTest(case=name, mutation=index), self.assertRaises(ReferenceError):
                    diagnostic_anchor({"diagnostics":[value]}, case, units)

    def singleton_trace(self):
        case, units = self.source("singleton-add")
        origin = enriched_zip_records(case["source_zip_records"], units)[0]
        private = {"a":enriched_zip_records([case["expected"]["paired_entry_zip_records_exact"]["a"]], units)}
        local = {"key":{"type":"String","known":False}, "lv":{"type":"Int","known":False}, "rv":{"type":"Int","known":False}}
        events = ["evaluate_left","admit_left","evaluate_right","admit_right"]
        budget = {"consumed_operations":20, "host_ceilings":case["host_policy"], "effective":case["host_policy"]}
        invocation = {**{p:origin[p] for p in ("expression","left","right","body")}, "self_path":"shape",
            "left_input_evaluations":1,"right_input_evaluations":1,"left_input_admissions":1,"right_input_admissions":1,
            "left_dynamic_divisions":0,"right_dynamic_divisions":0,"left_map_visits":[],"right_map_visits":[],
            "dynamic_input_order":["left","right"],"admission_order":["left","right"],"input_events":events,
            "left_keys":["a"],"right_keys":["a"],"output_keys":["a"],"keyset_keys":["a"],"iteration_keys":["a"],"body_keys":["a"],
            "left_type":"Keyed<Int>","right_type":"Keyed<Int>","output_type":"Keyed<Int>",
            "abstract_body_checks":[{"locals":local,"effective_locals":deepcopy(local),"mask_observed":False,"body_evaluations_started":0}],
            "operations_before":1,"operations_after":10,"value_entries_before":0,"value_entries_after":10,
            "checkpoints":[{"stage":"keyed_zip_keyset","key":"a","consumed_operations":3,"value_entries":1},
                           {"stage":"keyed_zip_iteration","key":"a","consumed_operations":5,"value_entries":2}],
            "timeline":[{"event":e} for e in events]+[{"event":"keyed_zip_keyset","key":"a"},
                {"event":"keyed_zip_iteration","key":"a"},{"event":"body","key":"a"}],
            "aggregate_zip_records":[origin],"stored_leaf_zip_records":private,
            "snapshot_ledger":{"operations_before":10,"operations_after":10,"value_entries_before":10,"value_entries_after":10}}
        trace = {"schema_version":"ontokin.c085-zip-execution-observation/0.1","case":case["name"],
            "program_revision":case["program_revision"],"profile":"keyed-zip-0.1","requested_level":"represented",
            "public_api":"KeyedZipProgramRuntime.validate_revision","invocations":[invocation],"execution_budget":budget}
        return case, units, trace, budget

    def test_trace_rejects_reordered_inputs_keyset_body_and_ledger_mutation(self):
        case, units, baseline, budget = self.singleton_trace()
        self.assertTrue(requires_execution_trace(case))
        check_execution_trace(baseline, case, units, budget)
        mutations = []
        value = deepcopy(baseline); value["invocations"][0]["input_events"][1:3] = ["evaluate_right","admit_left"]; mutations.append(value)
        value = deepcopy(baseline); value["invocations"][0]["timeline"][4], value["invocations"][0]["timeline"][6] = value["invocations"][0]["timeline"][6], value["invocations"][0]["timeline"][4]; mutations.append(value)
        value = deepcopy(baseline); value["invocations"][0]["checkpoints"][0]["key"] = "invented"; mutations.append(value)
        value = deepcopy(baseline); value["invocations"][0]["snapshot_ledger"]["operations_after"] += 1; mutations.append(value)
        value = deepcopy(baseline); value["invocations"][0]["stored_leaf_zip_records"]["a"][0]["right_entry"]["filename"] = "forged.ok"; mutations.append(value)
        value = deepcopy(baseline); value["invocations"][0]["abstract_body_checks"][0]["effective_locals"]["lv"]["known"] = True; mutations.append(value)
        for index, value in enumerate(mutations):
            with self.subTest(mutation=index), self.assertRaises(ReferenceError):
                check_execution_trace(value, case, units, budget)

    def test_recursive_abstract_recheck_requires_observed_masking(self):
        case, units, trace, budget = self.singleton_trace()
        local = deepcopy(trace["invocations"][0]["abstract_body_checks"][0]["locals"])
        concrete = {k:{**v,"known":True} for k,v in local.items()}
        trace["invocations"][0]["abstract_body_checks"].append({"locals":concrete,"effective_locals":local,
            "mask_observed":True,"body_evaluations_started":1})
        check_execution_trace(trace, case, units, budget)
        trace["invocations"][0]["abstract_body_checks"][-1]["mask_observed"] = False
        with self.assertRaises(ReferenceError):
            check_execution_trace(trace, case, units, budget)


if __name__ == "__main__":
    unittest.main()
