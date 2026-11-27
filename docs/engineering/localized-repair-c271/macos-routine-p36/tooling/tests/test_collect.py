"""The unit-log outcome collector on logs that this interpreter's own unittest runner writes."""
import json
import os
import unittest

import w2_support as S

LOG = "unit_log_outcomes"


def by_id(document):
    return {row["id"]: row for row in document["tests"] + document["fixtures"]}


class EveryOutcomeKind(unittest.TestCase):
    def setUp(self):
        self.text = S.unittest_log(S.Outcomes, S.TearDownError)
        self.code, self.document, self.stderr, _ = S.collect(self, self.text)
        self.rows = by_id(self.document)

    def outcome(self, method, cls="Outcomes"):
        return self.rows["test_synth.%s.%s" % (cls, method)]

    def test_the_log_is_read_completely_and_its_counts_equal_its_footer(self):
        self.assertEqual(self.code, 0, self.stderr)
        self.assertEqual(self.document["state"], "PARSED")
        self.assertTrue(all(self.document["checks"].values()), self.document["checks"])
        footer = self.document["footer"]
        self.assertEqual(footer["ran"], self.document["counts"]["tests_started"])
        self.assertEqual(footer["ran"], len(self.document["tests"]))
        for key in ("failures", "errors", "skipped", "expected failures", "unexpected successes"):
            self.assertEqual(footer["counts"][key], self.document["counts"][key], key)
        self.assertEqual(self.document["listing"]["entries"], footer["counts"]["failures"] + footer["counts"]["errors"])

    def test_each_outcome_kind_has_its_own_value(self):
        expected = {"test_pass": "passed", "test_fail": "failure", "test_error": "error",
                    "test_skip_decorated": "skipped", "test_skip_in_body": "skipped",
                    "test_expected_failure": "expected_failure", "test_unexpected_success": "unexpected_success",
                    "test_subtests": "error", "test_subtest_skip": "skipped", "test_docstring_pass": "passed",
                    "test_docstring_fail": "failure", "test_docstring_subtests": "failure",
                    "test_multiline_reason": "failure", "test_chained": "error"}
        for method, outcome in expected.items():
            with self.subTest(method=method):
                self.assertEqual(self.outcome(method)["outcome"], outcome)
        self.assertEqual(self.outcome("test_fail_then_teardown_error", "TearDownError")["outcome"], "error")

    def test_raw_ids_are_unittests_own(self):
        for raw_id in self.rows:
            self.assertRegex(raw_id, r"^test_synth\.[A-Za-z]+\.test_[a-z_]+$")
        self.assertEqual(self.outcome("test_pass")["description"], "test_pass (test_synth.Outcomes.test_pass)")

    def test_first_line_of_each_reason(self):
        self.assertEqual(self.outcome("test_fail")["reasons"], ["AssertionError: 1 != 2"])
        self.assertEqual(self.outcome("test_error")["reasons"], ["ValueError: broken value"])
        self.assertEqual(self.outcome("test_multiline_reason")["reasons"],
                         ["AssertionError: Lists differ: [1, 2, 3] != [1, 2, 4]"])
        self.assertGreater(self.outcome("test_multiline_reason")["runs"][0]["events"][0]["reason_lines"], 5)
        chained = self.outcome("test_chained")
        self.assertEqual(chained["reasons"], ["RuntimeError: outer failure"])
        self.assertEqual(chained["runs"][0]["events"][0]["chain_first_lines"],
                         ["KeyError: 'k'", "RuntimeError: outer failure"])
        self.assertEqual(self.outcome("test_docstring_fail")["reasons"], ["AssertionError: failed with a docstring"])

    def test_skip_reasons_are_decoded(self):
        self.assertEqual(self.outcome("test_skip_decorated")["skip_reasons"], ["not today"])
        self.assertEqual(self.outcome("test_skip_in_body")["skip_reasons"], ["it's \"quoted\"\nand on two lines"])

    def test_failing_and_skipped_subtests(self):
        subtests = self.outcome("test_subtests")
        self.assertEqual([(row["subtest"], row["status"], row["reason_first_line"]) for row in subtests["failing_subtests"]],
                         [("(i=1)", "FAIL", "AssertionError: 1 != 0"), ("(i=2)", "ERROR", "KeyError: 'missing key'")])
        self.assertEqual(subtests["runs"][0]["events"], [])
        skipped = self.outcome("test_subtest_skip")
        self.assertEqual(skipped["skipped_subtests"], [{"subtest": "(case='a')", "skip_reason": "subtest skipped"}])
        docstring = self.outcome("test_docstring_subtests")
        self.assertEqual(docstring["docline"], "Docstring with subtests.")
        self.assertEqual([row["subtest"] for row in docstring["failing_subtests"]], ["[message] (n=2)"])

    def test_a_test_with_several_events_keeps_them_all(self):
        row = self.outcome("test_fail_then_teardown_error", "TearDownError")
        self.assertEqual([event["status"] for event in row["runs"][0]["events"]], ["FAIL", "ERROR"])
        self.assertEqual(row["reasons"], ["AssertionError: first the failure", "OSError: teardown broke"])

    def test_docstring_lines_are_part_of_the_description_not_the_id(self):
        row = self.outcome("test_docstring_pass")
        self.assertEqual(row["docline"], "First docstring line.")
        self.assertEqual(row["id"], "test_synth.Outcomes.test_docstring_pass")

    def test_the_drivers_own_reading_is_recorded(self):
        reading = self.document["driver_reading"]
        self.assertEqual(reading["tests_run"], self.document["footer"]["ran"])
        self.assertEqual(reading["skipped"], self.document["footer"]["counts"]["skipped"])
        self.assertEqual(reading["expected_failures"], self.document["footer"]["counts"]["expected failures"])

    def test_expectations_state_a_frozen_outcome_for_an_exact_id(self):
        code, document, _, _ = S.collect(self, self.text, "--expect", "test_synth.Outcomes.test_pass=passed",
                                         "--expect", "test_synth.Outcomes.test_fail=passed",
                                         "--expect", "test_synth.Outcomes.test_absent=passed")
        self.assertEqual(code, 1)
        self.assertEqual([(row["observed"], row["met"]) for row in document["expectations"]],
                         [("passed", True), ("failure", False), ("missing", False)])
        code, document, _, _ = S.collect(self, self.text, "--expect", "test_synth.Outcomes.test_pass=passed")
        self.assertEqual((code, document["expectations_met"]), (0, True))


class ClassAndModuleLevelEvents(unittest.TestCase):
    def test_fixture_errors_skips_and_import_failures_are_records_of_their_own(self):
        text = S.unittest_log(S.SetUpClassError, S.TearDownClassError, S.SetUpClassSkip,
                              import_failure="test_synth_missing_module_w2", module_setup_error=True)
        code, document, stderr, _ = S.collect(self, text)
        self.assertEqual(code, 0, stderr)
        rows = by_id(document)
        self.assertEqual(rows["setUpClass (test_synth.SetUpClassError)"]["outcome"], "error")
        self.assertEqual(rows["setUpClass (test_synth.SetUpClassError)"]["reasons"], ["RuntimeError: class setup broke"])
        self.assertEqual(rows["tearDownClass (test_synth.TearDownClassError)"]["reasons"],
                         ["RuntimeError: class teardown broke"])
        self.assertEqual(rows["setUpClass (test_synth.SetUpClassSkip)"]["outcome"], "skipped")
        self.assertEqual(rows["setUpClass (test_synth.SetUpClassSkip)"]["skip_reasons"], ["the whole class is skipped"])
        self.assertEqual(rows["setUpModule (test_synth_module)"]["reasons"], ["RuntimeError: module setup broke"])
        failed = rows["unittest.loader._FailedTest.test_synth_missing_module_w2"]
        self.assertEqual((failed["outcome"], failed["special"]), ("error", "failed_import_or_load"))
        self.assertTrue(failed["reasons"][0].startswith("ImportError: Failed to import test module: "))
        # the tests of a class whose setup failed never start, so they have no record
        self.assertNotIn("test_synth.SetUpClassError.test_never_runs", rows)
        self.assertNotIn("test_synth_module.ModuleFixtureCase.test_not_run_after_module_setup", rows)
        self.assertEqual(rows["test_synth.TearDownClassError.test_runs"]["outcome"], "passed")
        self.assertEqual(document["counts"]["fixture_ids"], 4)


class InterleavedOutput(unittest.TestCase):
    def test_output_between_start_and_status_or_glued_to_runner_lines_does_not_break_it(self):
        text = S.unittest_log(S.Interleaved, S.GluedStart, S.Outcomes, trailing="flushed at exit\n")
        code, document, stderr, _ = S.collect(self, text)
        self.assertEqual(code, 0, stderr)
        rows = by_id(document)
        for method in ("test_full_lines_between_start_and_status", "test_partial_line_glued_before_status",
                       "test_warning_like_lines", "test_noise_with_dots_and_parentheses",
                       "test_fake_footer_in_output"):
            with self.subTest(method=method):
                self.assertEqual(rows["test_synth.Interleaved." + method]["outcome"], "passed")
        self.assertEqual(rows["test_synth.Interleaved.test_partial_then_fail"]["reasons"],
                         ["AssertionError: failure after partial noise"])
        self.assertEqual(rows["test_synth.Interleaved.test_reason_with_a_foreign_header"]["reasons"],
                         ["AssertionError: text"])
        self.assertEqual(rows["test_synth.GluedStart.test_after_glued_noise"]["outcome"], "passed")
        self.assertGreater(document["noise"]["lines"], 8)
        self.assertEqual(document["footer"]["trailing_text"]["bytes"], len("flushed at exit\n"))
        self.assertEqual(document["footer"]["earlier_footer_patterns"], 1)

    def test_a_printed_status_right_after_a_start_is_refused_not_misread(self):
        class PrintsAStatus(unittest.TestCase):
            __module__, __qualname__ = "test_synth", "PrintsAStatus"

            def test_prints_fail_then_passes(self):
                S.Noise.write("FAIL\n")
        code, document, _, _ = S.collect(self, S.unittest_log(PrintsAStatus))
        self.assertEqual((code, document["state"]), (2, "REFUSED"))
        self.assertEqual(document["refusal"]["rule"], "PARSE")

    def assertAmbiguous(self, text):
        code, document, _, _ = S.collect(self, text)
        self.assertEqual((code, document["state"]), (2, "REFUSED"), document.get("tests"))
        attempts = document["refusal"]["details"]["attempts"]
        self.assertEqual({row["rule"] for row in attempts}, {"AMBIGUOUS"})
        return attempts[0]["details"]

    def test_tr05_two_candidates_after_a_start_refuse_even_when_they_agree(self):
        for method, statuses in (("test_noise_ending_like_a_status", ["ok", "ok"]),
                                 ("test_noise_ending_with_another_status", ["ERROR", "ok"])):
            with self.subTest(method=method):
                details = self.assertAmbiguous(S.unittest_log(extra_tests=[S.TwoCandidates(method)]))
                self.assertEqual(details["candidate_statuses"], statuses)

    def test_tr05_probe_pr3_printed_imitations_that_keep_every_count_are_refused(self):
        # PR-3: a skipped and a passing test whose printed imitations would swap their outcomes
        self.assertEqual(self.assertAmbiguous(S.unittest_log(S.Swap))["candidate_statuses"], ["ok", "skipped"])
        # PR-3b: an imitation that would replace the recorded skip reason
        self.assertEqual(self.assertAmbiguous(S.unittest_log(S.SkipReason))["candidate_statuses"],
                         ["skipped", "skipped"])

    def test_statuses_with_different_values_after_a_start_refuse_as_ambiguous(self):
        description = "test_x (test_synth.Case.test_x)"
        text = (description + " ... \nFAIL\nok\n\n" + S.SEPARATOR2 + "\nRan 1 test in 0.001s\n\nOK\n")
        code, document, _, _ = S.collect(self, text)
        self.assertEqual(code, 2)
        attempts = document["refusal"]["details"]["attempts"]
        self.assertEqual(attempts[0]["rule"], "AMBIGUOUS")

    def test_a_listing_split_that_is_not_unique_is_refused(self):
        class ForgesAHeader(unittest.TestCase):
            __module__, __qualname__ = "test_synth", "ForgesAHeader"

            def test_a_error(self):
                raise ValueError("real error")

            def test_b_fail(self):
                self.fail("forged\n" + S.SEPARATOR1 + "\nERROR: test_a_error (test_synth.ForgesAHeader.test_a_error)\n"
                          + S.SEPARATOR2 + "\nforged")
        code, document, _, _ = S.collect(self, S.unittest_log(ForgesAHeader))
        self.assertEqual(code, 2)
        self.assertEqual(document["refusal"]["details"]["attempts"][0]["rule"], "LISTING")

    def test_duplicate_ids_are_one_record_with_every_occurrence(self):
        class Twice(unittest.TestCase):
            __module__, __qualname__ = "test_synth", "Twice"

            def test_once_or_twice(self):
                pass
        code, document, stderr, _ = S.collect(self, S.unittest_log(Twice, duplicate=Twice))
        self.assertEqual(code, 0, stderr)
        row = by_id(document)["test_synth.Twice.test_once_or_twice"]
        self.assertEqual((row["occurrences"], len(row["runs"]), document["counts"]["duplicate_test_ids"]), (2, 2, 1))


READBACK = "test_static_tray_readback_v01."
CPU = READBACK + "ReadbackCPUControls"
SEAMS = READBACK + "ReadbackCoordinatorSeams"
METHODS = [CPU + "." + name for name in ("test_q01_actual_synthetic_meshes_load_in_both_libraries",
                                         "test_q03_actual_synthetic_rotations_load_in_both_libraries",
                                         "test_three_rejects_changed_synthetic_reference")] + \
          [SEAMS + "." + name for name in ("test_result_write_failure_leaves_predecessor_gate_blocked",
                                           "test_host_alarm_cannot_interrupt_supervisor_cleanup",
                                           "test_success_finalization_uses_remaining_outer_alarm",
                                           "test_uncertain_marker_removal_recreates_pending")]


def readback_classes(teardown_error):
    """W3's probe PR-1: the seven readback methods pass; the CPU class's tearDownClass (the cohort accounting) may error."""
    class ReadbackCPUControls(unittest.TestCase):
        __module__, __qualname__ = "test_static_tray_readback_v01", "ReadbackCPUControls"

        def test_q01_actual_synthetic_meshes_load_in_both_libraries(self):
            pass

        def test_q03_actual_synthetic_rotations_load_in_both_libraries(self):
            pass

        def test_three_rejects_changed_synthetic_reference(self):
            pass

    class ReadbackCoordinatorSeams(unittest.TestCase):
        __module__, __qualname__ = "test_static_tray_readback_v01", "ReadbackCoordinatorSeams"

        def test_result_write_failure_leaves_predecessor_gate_blocked(self):
            pass

        def test_host_alarm_cannot_interrupt_supervisor_cleanup(self):
            pass

        def test_success_finalization_uses_remaining_outer_alarm(self):
            pass

        def test_uncertain_marker_removal_recreates_pending(self):
            pass

    if teardown_error:
        def tearDownClass(cls):
            raise RuntimeError("synthetic cohort accounting failure")
        ReadbackCPUControls.tearDownClass = classmethod(tearDownClass)
    return ReadbackCPUControls, ReadbackCoordinatorSeams


class Expectations(unittest.TestCase):
    """TR-02: --expect states an absence, and an outcome holds only for exactly one occurrence (or a stated count)."""

    def expect(self, text, *rows):
        code, document, stderr, _ = S.collect(self, text, *[item for row in rows for item in ("--expect", row)])
        return code, document, stderr

    def test_tr02_probe_pr1_a_fixture_record_that_must_be_absent(self):
        rows = [raw_id + "=passed" for raw_id in METHODS]
        absent = ["%s (%s)=missing" % (kind, cls) for cls in (CPU, SEAMS) for kind in ("setUpClass", "tearDownClass")]
        code, document, stderr = self.expect(S.unittest_log(*readback_classes(True)), *rows, *absent)
        self.assertEqual(code, 1, stderr)
        self.assertFalse(document["expectations_met"])
        unmet = [row["id"] for row in document["expectations"] if not row["met"]]
        self.assertEqual(unmet, ["tearDownClass (%s)" % CPU])
        code, document, stderr = self.expect(S.unittest_log(*readback_classes(False)), *rows, *absent)
        self.assertEqual((code, document["expectations_met"]), (0, True), stderr)
        self.assertEqual({row["expected_occurrences"] for row in document["expectations"] if row["expected"] == "missing"},
                         {0})

    def test_tr02_probe_pr2_an_id_that_starts_twice_does_not_meet_a_single_expectation(self):
        _, seams = readback_classes(False)
        text = S.unittest_log(seams, duplicate=seams)
        code, document, _ = self.expect(text, METHODS[3] + "=passed")
        self.assertEqual(code, 1)
        self.assertEqual([(row["occurrences"], row["expected_occurrences"], row["met"]) for row in document["expectations"]],
                         [(2, 1, False)])
        code, document, _ = self.expect(text, METHODS[3] + "=passed*2")
        self.assertEqual((code, document["expectations"][0]["met"]), (0, True))

    def test_malformed_expectations_refuse(self):
        text = S.unittest_log(readback_classes(False)[1])
        for row in (METHODS[3] + "=absent", METHODS[3] + "=passed*0", METHODS[3] + "=missing*2", "=passed"):
            with self.subTest(row=row):
                code, document, _ = self.expect(text, row)
                self.assertEqual((code, document["refusal"]["rule"]), (2, "USAGE"))


class LoaderTests(unittest.TestCase):
    def test_tr08_probe_pr4_a_failed_import_inside_a_test_package_is_read(self):
        class Plain(unittest.TestCase):
            __module__, __qualname__ = "test_probe", "Plain"

            def test_ok(self):
                pass
        for name in ("test_flat_module", "package.test_inside_a_package"):
            with self.subTest(name=name):
                code, document, stderr, _ = S.collect(self, S.unittest_log(Plain, extra_tests=[S.failed_import(name)]))
                self.assertEqual((code, document["state"]), (0, "PARSED"), stderr)
                row = by_id(document)["unittest.loader._FailedTest." + name]
                self.assertEqual((row["outcome"], row["special"]), ("error", "failed_import_or_load"))
                self.assertEqual(row["reasons"], ["ImportError: Failed to import test module: " + name])
                self.assertEqual(row["description"], "%s (unittest.loader._FailedTest.%s)" % (name, name))


class DriverReading(unittest.TestCase):
    def test_tr11_the_drivers_reading_translates_line_ends_as_the_driver_does(self):
        text = S.unittest_log(S.Outcomes, trailing="printed at exit\rRan 9 tests in 1.000s\n")
        code, document, stderr, _ = S.collect(self, text)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(document["driver_reading"]["tests_run"], 9)
        self.assertEqual(S.driver_reading(text.encode("utf-8"))["tests_run"], 9)
        self.assertNotEqual(document["footer"]["ran"], 9)
        self.assertFalse(document["driver_reading"]["equals_footer"])
        code, document, _, _ = S.collect(self, S.unittest_log(S.Outcomes))
        self.assertTrue(document["driver_reading"]["equals_footer"])


class Refusals(unittest.TestCase):
    def setUp(self):
        self.text = S.unittest_log(S.Outcomes)

    def assertRefused(self, text, rule, *, nested=False):
        code, document, _, _ = S.collect(self, text)
        self.assertEqual((code, document["state"], document["schema"]), (2, "REFUSED", "ontokin.c271.p36-tool-refusal/1"))
        observed = document["refusal"]["rule"]
        if nested:
            observed = {row["rule"] for row in document["refusal"]["details"].get("attempts", [])} or {observed}
            self.assertIn(rule, observed)
        else:
            self.assertEqual(observed, rule)
        return document

    def test_truncation_anywhere_refuses(self):
        footer = self.text.rindex("\nRan ")
        listing = self.text.index(S.SEPARATOR1)
        for cut in (footer, footer + 6, listing + 200, len(self.text) // 3, len(self.text) - 2):
            with self.subTest(cut=cut):
                code, document, _, _ = S.collect(self, self.text[:cut])
                self.assertEqual((code, document["state"]), (2, "REFUSED"))

    def test_a_missing_listing_entry_refuses(self):
        start = self.text.index(S.SEPARATOR1 + "\nFAIL: ")
        end = self.text.index(S.SEPARATOR1, start + 1)
        self.assertRefused(self.text[:start] + self.text[end:], "LISTING", nested=True)

    def test_footer_counts_that_differ_from_the_progress_refuse(self):
        line = self.text.splitlines()[-1]
        changed = line.replace("failures=", "failures=1", 1)
        self.assertNotEqual(changed, line)
        self.assertRefused(self.text.replace(line, changed), "COUNTS", nested=True)
        ran = [row for row in self.text.splitlines() if row.startswith("Ran ")][-1]
        number = int(ran.split()[1])
        self.assertRefused(self.text.replace(ran, ran.replace(str(number), str(number + 1), 1)), "COUNTS", nested=True)

    def test_a_result_word_that_does_not_fit_its_counts_refuses(self):
        line = self.text.splitlines()[-1]
        self.assertRefused(self.text.replace(line, line.replace("FAILED", "OK", 1)), "FOOTER")

    def test_a_log_that_is_not_unittest_output_refuses(self):
        self.assertRefused("no unittest here\n", "FOOTER")

    def test_digest_and_usage_refusals(self):
        directory = S.temp_dir(self)
        log = os.path.join(directory, "unit-tests.log")
        S.write(log, self.text)
        output = os.path.join(directory, "out.json")
        code, _ = S.run_tool(LOG, ["collect", "--log", log, "--log-sha256", "0" * 64, "--output", output])
        document = S.read_json(output)
        self.assertEqual((code, document["refusal"]["rule"]), (2, "DIGEST"))
        self.assertEqual(document["refusal"]["details"]["actual_sha256"], S.sha256(self.text))
        other = os.path.join(directory, "other.json")
        code, _ = S.run_tool(LOG, ["collect", "--log", log, "--log-sha256", "ABC", "--output", other])
        self.assertEqual((code, S.read_json(other)["refusal"]["rule"]), (2, "USAGE"))

    def test_an_existing_output_is_never_replaced(self):
        directory = S.temp_dir(self)
        log = os.path.join(directory, "unit-tests.log")
        digest = S.write(log, self.text)
        output = os.path.join(directory, "out.json")
        S.write(output, b"kept")
        code, stderr = S.run_tool(LOG, ["collect", "--log", log, "--log-sha256", digest, "--output", output])
        self.assertEqual(code, 2)
        self.assertIn('"rule": "OUTPUT"', stderr)
        with open(output, "rb") as stream:
            self.assertEqual(stream.read(), b"kept")

    def test_a_non_canonical_path_refuses(self):
        directory = S.temp_dir(self)
        log = os.path.join(directory, "unit-tests.log")
        digest = S.write(log, self.text)
        os.symlink(directory, os.path.join(directory, "link"))
        output = os.path.join(directory, "out.json")
        code, _ = S.run_tool(LOG, ["collect", "--log", os.path.join(directory, "link", "unit-tests.log"),
                                   "--log-sha256", digest, "--output", output])
        self.assertEqual((code, S.read_json(output)["refusal"]["rule"]), (2, "LOG"))


class InventoryJoin(unittest.TestCase):
    """The log against a runtime-discovery document (MC28): MH's schema, its IDs recomputed, every difference listed."""

    def setUp(self):
        self.text = S.unittest_log(S.Outcomes)
        _, document, _, _ = S.collect(self, self.text)
        self.ids = [raw_id for _, raw_id in sorted((run["order"], row["id"]) for row in document["tests"]
                                                    for run in row["runs"])]

    def join(self, ids, *, schema="ontokin.c271.p35-runtime-discovery/2", state="COMPLETE"):
        directory = S.temp_dir(self)
        path = os.path.join(directory, "discovery.json")
        digest = S.write(path, json.dumps({"schema": schema, "state": state, "count": 999,
                                           "ids_in_discovery_order": ids}))
        code, document, stderr, _ = S.collect(self, self.text, "--inventory", path, "--inventory-sha256", digest,
                                              directory=directory)
        return code, document, stderr

    def test_the_started_tests_equal_the_discovered_list(self):
        code, document, stderr = self.join(self.ids)
        self.assertEqual(code, 0, stderr)
        self.assertTrue(document["inventory"]["matches"])
        self.assertEqual(document["inventory"]["ids"], len(self.ids))

    def test_every_difference_is_listed(self):
        code, document, _ = self.join(self.ids[1:] + ["test_synth.Outcomes.test_never_started"])
        inventory = document["inventory"]
        self.assertEqual(code, 1)
        self.assertEqual(inventory["inventory_not_started"], ["test_synth.Outcomes.test_never_started"])
        self.assertEqual(inventory["started_not_in_inventory"], [self.ids[0]])
        code, document, _ = self.join(list(reversed(self.ids)))
        self.assertEqual((code, document["inventory"]["sequence_equal"]), (1, False))
        self.assertEqual(document["inventory"]["inventory_not_started"], [])
        code, document, _ = self.join(self.ids + self.ids[:1])
        self.assertEqual(document["inventory"]["recomputed_duplicates"], [self.ids[0]])
        self.assertEqual(document["inventory"]["started_a_different_number_of_times"], [self.ids[0]])

    def test_an_incomplete_or_foreign_document_refuses(self):
        for options in ({"state": "INCOMPLETE"}, {"schema": "ontokin.c271.p35-runtime-discovery/1"}):
            with self.subTest(**options):
                code, document, _ = self.join(self.ids, **options)
                self.assertEqual((code, document["refusal"]["rule"]), (2, "INVENTORY"))


class DashBGuard(unittest.TestCase):
    def test_a_start_without_dash_b_refuses_before_any_other_import(self):
        module = S.tool(LOG)

        class Flags:
            dont_write_bytecode = 0
        self.assertTrue(module._missing_dash_b(Flags))
        with self.assertRaises(module.Refusal) as caught:
            module.require_dash_b(Flags)
        self.assertEqual(caught.exception.rule, "PYTHON")
        self.assertFalse(module._missing_dash_b())
        source = (S.TOOLING / (LOG + ".py")).read_text(encoding="utf-8")
        guard, first_import = source.index('if __name__ == "__main__" and _missing_dash_b():'), source.index("import argparse")
        self.assertLess(guard, first_import)
        self.assertEqual([line for line in source[:guard].splitlines() if line.startswith(("import ", "from "))],
                         ["import sys"])


if __name__ == "__main__":
    unittest.main()
