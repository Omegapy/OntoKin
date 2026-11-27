"""The baseline comparator: OK-ENG-009 section 3 item 4 lists, attributions and the summaries side by side."""
import json
import os
import unittest

import w2_support as S

LOG = "unit_log_outcomes"


def comparison_case(version, tmp, workspace):
    """One class whose outcomes differ between a baseline and a candidate in every way item 4 names."""
    baseline = version == "baseline"

    class Case(unittest.TestCase):
        __module__, __qualname__ = "test_cmp", "Case"

        def test_a_pass(self):
            pass

        def test_b_fail_same(self):
            self.fail("same reason")

        def test_c_error_subtests_same(self):
            for number in (1, 2):
                with self.subTest(i=number):
                    raise ValueError("sub")

        @unittest.skip("skipped in both")
        def test_d_skip(self):
            pass

        def test_f_fixed(self):
            if baseline:
                self.fail("was failing")

        def test_g_reason_changes(self):
            self.fail("first reason" if baseline else "second reason")

        def test_h_subtests_change(self):
            for number in ((1, 2) if baseline else (1, 3)):
                with self.subTest(i=number):
                    raise ValueError("sub")

        def test_i_regresses(self):
            if not baseline:
                self.fail("now failing")

        def test_j_outcome_changes(self):
            if baseline:
                self.skipTest("was skipped")
            raise RuntimeError("now an error")

        def test_m_tmp_path(self):
            self.fail("cannot use " + tmp + "/tmp" + ("abcdefgh" if baseline else "zyxwvuts") + "/plan.json")

        def test_n_workspace_path(self):
            self.fail("bad path " + workspace + "/tests/x.py")

    def test_e_removed(self):
        pass

    def test_k_new_failing(self):
        self.fail("new test fails")

    def test_l_new_passing(self):
        pass
    if baseline:
        Case.test_e_removed = test_e_removed
    else:
        Case.test_k_new_failing = test_k_new_failing
        Case.test_l_new_passing = test_l_new_passing
    return Case


def readback_case(version):
    """Main's three skipped readback tests, and an ordinary run whose class fails at setup instead."""
    class Readback(unittest.TestCase):
        __module__, __qualname__ = "test_cmp", "Readback"

        def test_q01(self):
            self.skipTest("dependencies unavailable")

        def test_q03(self):
            self.skipTest("dependencies unavailable")

        def test_changed(self):
            self.skipTest("dependencies unavailable")

    if version == "candidate":
        def setUpClass(cls):
            raise RuntimeError("No approved current-host readback selection: ordinary run, not a qualification")
        Readback.setUpClass = classmethod(setUpClass)
    return Readback


class Plain(unittest.TestCase):
    __module__, __qualname__ = "test_probe", "Plain"

    def test_ok(self):
        pass


def ids(entries):
    return sorted(entry["id"].rsplit(".", 1)[-1] if entry["kind"] == "test" else entry["id"] for entry in entries)


def runs_of(test, cases, **options):
    """One driver run per version: {version: run}, each from S.unittest_log(cases[version])."""
    base = S.temp_dir(test)
    runs = {}
    for version, classes in cases.items():
        directory = os.path.join(base, version)
        os.makedirs(directory)
        runs[version] = S.driver_run(test, directory, S.unittest_log(*classes), **options.get(version, {}))
    return base, runs


def compare(base, baseline, candidate, name, *extra):
    output = os.path.join(base, name)
    code, stderr = S.run_tool(LOG, S.compare_argv(baseline, candidate, output, *extra))
    return code, S.read_json(output), stderr


class ItemFourLists(unittest.TestCase):
    def setUp(self):
        base = S.temp_dir(self)
        self.tmp = os.path.join(base, "tmp-a")
        self.runs = {}
        for version in ("baseline", "candidate"):
            directory = os.path.join(base, version)
            os.makedirs(directory)
            text = S.unittest_log(comparison_case(version, self.tmp, directory + "/workspace"))
            self.runs[version] = S.driver_run(self, directory, text, documents="failed" if version == "baseline" else "passed")
        self.base = base

    def compare(self, *extra, name="comparison.json", candidate=None):
        return compare(self.base, self.runs["baseline"], candidate or self.runs["candidate"], name, *extra)

    def test_every_category_is_listed_and_nothing_is_exempt(self):
        code, document, stderr = self.compare("--baseline-tmpdir", self.tmp, "--candidate-tmpdir", self.tmp)
        self.assertEqual((code, document["state"]), (1, "COMPARED"), stderr)
        self.assertEqual(document["unchanged"], {"passed": 1, "failure": 3, "error": 1, "skipped": 1,
                                                 "expected_failure": 0, "unexpected_success": 0})
        self.assertEqual(ids(document["unchanged_not_passing"]),
                         ["test_b_fail_same", "test_c_error_subtests_same", "test_m_tmp_path", "test_n_workspace_path"])
        self.assertEqual(ids(document["unchanged_skipped"]), ["test_d_skip"])
        # TR-04: skipped in the baseline and an error now is newly not passing as well as a different outcome
        self.assertEqual(ids(document["new_not_passing"]), ["test_i_regresses", "test_j_outcome_changes",
                                                            "test_k_new_failing"])
        self.assertEqual(ids(document["no_longer_failing"]), ["test_f_fixed"])
        self.assertEqual(ids(document["different_outcome"]), ["test_j_outcome_changes"])
        self.assertEqual(ids(document["different_reason"]), ["test_g_reason_changes"])
        self.assertEqual(ids(document["different_subtests"]), ["test_h_subtests_change"])
        self.assertEqual(ids(document["added_ids"]), ["test_k_new_failing", "test_l_new_passing"])
        self.assertEqual(ids(document["removed_ids"]), ["test_e_removed"])
        self.assertEqual(document["exempt"], [])
        self.assertFalse(document["identical_item_4_lists"])
        entry = document["different_outcome"][0]
        self.assertEqual((entry["baseline"]["outcome"], entry["candidate"]["outcome"]), ("skipped", "error"))
        self.assertEqual(document["tests"], {"baseline": 12, "candidate": 13})

    def test_the_declared_normalization_replaces_only_the_runs_own_paths(self):
        code, document, _ = self.compare()
        self.assertIn("test_m_tmp_path", ids(document["different_reason"]))
        self.assertNotIn("test_n_workspace_path", ids(document["different_reason"]))
        code, document, _ = self.compare("--baseline-tmpdir", self.tmp, "--candidate-tmpdir", self.tmp, name="n.json")
        entry = [row for row in document["unchanged_not_passing"] if row["id"].endswith("test_m_tmp_path")][0]
        self.assertEqual(entry["candidate"]["reasons"], ["AssertionError: cannot use <tmp>/*/plan.json"])
        self.assertNotEqual(entry["baseline"]["raw_reasons"], entry["candidate"]["raw_reasons"])
        # TR-06: every masked temporary name is recorded per entry
        self.assertEqual((entry["baseline"]["masked_temporary_names"], entry["candidate"]["masked_temporary_names"]),
                         (["tmpabcdefgh"], ["tmpzyxwvuts"]))
        entry = [row for row in document["unchanged_not_passing"] if row["id"].endswith("test_n_workspace_path")][0]
        self.assertEqual(entry["baseline"]["reasons"], ["AssertionError: bad path <workspace>/tests/x.py"])
        self.assertEqual(entry["baseline"]["masked_temporary_names"], [])
        labels = document["normalization"]["candidate"]["temporary_directory_labels"]
        self.assertIn("<tmp>", labels)
        self.assertLessEqual(set(labels), {"<tmp>", "<tmp:resolved>", "<tmp:alias>"})
        self.assertEqual(document["normalization"]["candidate"]["path_labels"],
                         ["<python>", "<workspace>", "<source>", "<output>"])

    def test_steps_reports_pending_cases_and_not_executed_steps_side_by_side(self):
        code, document, _ = self.compare()
        summaries = document["summaries"]
        self.assertEqual(summaries["steps_different"], [["documents", "failed", "passed"]])
        self.assertEqual(summaries["steps_equal"], ["unit-tests", "surface"])
        self.assertEqual(summaries["reports_different"], [])
        surface = [row for row in summaries["steps"] if row["id"] == "surface"][0]
        self.assertTrue(surface["report_outcomes_equal"])
        self.assertTrue(summaries["pending_external_cases"]["equal"])
        self.assertTrue(summaries["not_executed_steps"]["equal"])
        self.assertTrue(document["logs"]["candidate"]["driver_reading_matches_summary"])

    def test_different_pending_cases_are_shown_on_each_side(self):
        directory = os.path.join(self.base, "candidate-pending")
        os.makedirs(directory)
        text = S.unittest_log(comparison_case("candidate", self.tmp, directory + "/workspace"))
        pending = [{"step": "surface", "report": "reports/surface.json", "id": "M01", "reasons": ["external"]},
                   {"step": "surface", "report": "reports/surface.json", "id": "M02", "reasons": ["external"]}]
        candidate = S.driver_run(self, directory, text, pending=pending)
        code, document, _ = self.compare(candidate=candidate, name="pending.json")
        cases = document["summaries"]["pending_external_cases"]
        self.assertFalse(cases["equal"])
        self.assertEqual([row["id"] for row in cases["only_candidate"]], ["M02"])
        surface = [row for row in document["summaries"]["steps"] if row["id"] == "surface"][0]
        self.assertFalse(surface["report_outcomes_equal"])

    def test_identical_runs_compare_as_identical(self):
        output = os.path.join(self.base, "same.json")
        code, stderr = S.run_tool(LOG, S.compare_argv(self.runs["baseline"], self.runs["baseline"], output))
        document = S.read_json(output)
        self.assertEqual(code, 0, stderr)
        self.assertTrue(document["identical_item_4_lists"])
        self.assertEqual(document["unchanged"]["failure"], 5)
        self.assertEqual(document["summaries"]["steps_different"], [])
        self.assertEqual(document["summaries"]["reports_different"], [])


D18 = "test_current_host_readback_driver.CurrentHostDriverBindingTests.test_failed_prelaunch"
FROZEN = {"id": D18, "form": "raw", "source": "D-18 (synthetic)", "outcome": "error", "occurrences": 1,
          "events": [{"status": "FAIL", "reason_first_line": "AssertionError: own reason as frozen"}],
          "failing_subtests": [{"subtest": "(fail_after=False)", "status": "ERROR",
                                "reason_first_line": "TypeError: subtest reason as frozen"}],
          "skipped_subtests": []}


def d18_case(version):
    """D-18's first test as W3 describes it (an erroring subtest and its own failure), and its variants."""
    class Driver(unittest.TestCase):
        __module__, __qualname__ = "test_current_host_readback_driver", "CurrentHostDriverBindingTests"

        def test_failed_prelaunch(self):
            if version == "passing":
                return
            subtests = (False, True) if version in ("added-subtest", "pr5-worse") else (False,)
            for fail_after in subtests:
                with self.subTest(fail_after=fail_after):
                    reason = "subtest reason " + ("changed" if version in ("changed-subtest-reason", "pr5-worse")
                                                  else "as frozen")
                    if version == "changed-outcome":
                        self.fail(reason)
                    raise TypeError(reason)
            if version != "removed-event":
                self.fail("own reason as frozen")

    if version == "added-event":
        def tearDown(self):
            raise OSError("teardown broke")
        Driver.tearDown = tearDown
    return Driver


class Attributions(unittest.TestCase):
    """TR-01: an attribution states the complete not-passing record and matches only by exact equality."""

    def attribute(self, version, rows=None, *extra):
        base, runs = runs_of(self, {"baseline": [d18_case("passing")], "candidate": [d18_case(version)]})
        path, digest = S.attribution_file(base, "attributions.json", rows or [FROZEN])
        code, document, stderr = compare(base, runs["baseline"], runs["candidate"], "comparison.json",
                                         "--attributions", path, "--attributions-sha256", digest, *extra)
        self.assertEqual(document.get("state"), "COMPARED", stderr)
        return document["attributions"][0], document

    def test_tr01_an_exact_statement_of_a_two_part_record_matches(self):
        row, document = self.attribute("as-frozen")
        statement = {key: FROZEN[key] for key in ("outcome", "occurrences", "events", "failing_subtests",
                                                  "skipped_subtests")}
        self.assertEqual(row["observed"], statement)
        self.assertEqual((row["matches"], row["differences"]), (True, []))
        entry = [item for item in document["new_not_passing"] if item["id"] == D18][0]
        self.assertEqual(entry["attribution"], {"matches": True, "source": "D-18 (synthetic)"})
        self.assertEqual(document["exempt"], [])

    def test_tr01_a_changed_subtest_reason_does_not_match(self):
        row, _ = self.attribute("changed-subtest-reason")
        self.assertFalse(row["matches"])
        self.assertEqual([difference["field"] for difference in row["differences"]], ["failing_subtests[0]"])
        self.assertEqual(row["differences"][0]["observed"]["reason_first_line"], "TypeError: subtest reason changed")

    def test_tr01_an_added_subtest_does_not_match(self):
        row, _ = self.attribute("added-subtest")
        self.assertFalse(row["matches"])
        self.assertEqual([(item["field"], item["expected"]) for item in row["differences"]], [("failing_subtests[1]", None)])

    def test_tr01_an_added_own_event_does_not_match(self):
        row, _ = self.attribute("added-event")
        self.assertFalse(row["matches"])
        self.assertEqual(row["differences"], [{"field": "events[1]", "expected": None, "observed": {
            "status": "ERROR", "reason_first_line": "OSError: teardown broke"}}])

    def test_tr01_a_removed_own_event_does_not_match(self):
        row, _ = self.attribute("removed-event")
        self.assertFalse(row["matches"])
        self.assertEqual(row["differences"], [{"field": "events[0]", "expected": FROZEN["events"][0], "observed": None}])

    def test_tr01_a_changed_outcome_does_not_match(self):
        row, _ = self.attribute("changed-outcome")
        self.assertFalse(row["matches"])
        fields = [item["field"] for item in row["differences"]]
        self.assertEqual(fields, ["outcome", "failing_subtests[0]"])
        self.assertEqual((row["differences"][0]["expected"], row["differences"][0]["observed"]), ("error", "failure"))

    def test_tr01_probe_pr5_a_changed_subtest_reason_and_an_extra_erroring_subtest(self):
        row, _ = self.attribute("pr5-worse")
        self.assertFalse(row["matches"])
        self.assertEqual([item["field"] for item in row["differences"]], ["failing_subtests[0]", "failing_subtests[1]"])

    def test_tr01_an_absent_id_does_not_match(self):
        absent = dict(FROZEN, id=D18 + "_absent")
        row, _ = self.attribute("as-frozen", [absent])
        self.assertEqual((row["matches"], row["observed_outcome"]), (False, "missing"))
        self.assertEqual(row["differences"], [{"field": "id", "expected": "present", "observed": "missing"}])

    def test_tr01_the_declared_form_applies_to_the_whole_record(self):
        def case(component):
            class Paths(unittest.TestCase):
                __module__, __qualname__ = "test_cmp", "Paths"

                def test_reads_a_plan(self):
                    self.fail("cannot read " + tmp + "/" + component + "/plan.json")
            return Paths
        base = S.temp_dir(self)
        tmp = os.path.join(base, "tmp-b")
        base, runs = runs_of(self, {"baseline": [case("tmpabcd1234")], "candidate": [case("tmpzzzz9999")]})
        statement = {"id": "test_cmp.Paths.test_reads_a_plan", "outcome": "failure", "occurrences": 1,
                     "events": [{"status": "FAIL", "reason_first_line": "AssertionError: cannot read <tmp>/*/plan.json"}],
                     "failing_subtests": [], "skipped_subtests": []}
        results = {}
        for form in ("normalized", "raw"):
            path, digest = S.attribution_file(base, form + ".json", [dict(statement, form=form)])
            code, document, stderr = compare(base, runs["baseline"], runs["candidate"], form + "-comparison.json",
                                             "--attributions", path, "--attributions-sha256", digest,
                                             "--baseline-tmpdir", tmp, "--candidate-tmpdir", tmp)
            results[form] = document["attributions"][0]
        self.assertEqual((results["normalized"]["matches"], results["raw"]["matches"]), (True, False))
        self.assertEqual(results["raw"]["observed"]["events"][0]["reason_first_line"],
                         "AssertionError: cannot read " + tmp + "/tmpzzzz9999/plan.json")

    def test_malformed_attributions_refuse(self):
        base, runs = runs_of(self, {"baseline": [d18_case("passing")], "candidate": [d18_case("as-frozen")]})
        documents = {
            "revision 1's single reason": {"schema": "ontokin.c271.p36-attributions/1", "attributions": [
                {"id": D18, "outcome": "error", "reason_first_line": "AssertionError: own reason as frozen"}]},
            "a statement without its subtests": {"schema": S.ATTRIBUTIONS_V2, "attributions": [
                {key: value for key, value in FROZEN.items() if key != "failing_subtests"}]},
            "an undeclared form": {"schema": S.ATTRIBUTIONS_V2, "attributions": [dict(FROZEN, form="loose")]},
            "an outcome named exempt": {"schema": S.ATTRIBUTIONS_V2, "attributions": [dict(FROZEN, outcome="exempt")]},
            "an ID twice": {"schema": S.ATTRIBUTIONS_V2, "attributions": [FROZEN, FROZEN]}}
        for name, value in documents.items():
            with self.subTest(document=name):
                path = os.path.join(base, name.replace(" ", "-").replace("'", "") + ".json")
                digest = S.write(path, json.dumps(value))
                code, document, _ = compare(base, runs["baseline"], runs["candidate"], "refused-" + os.path.basename(path),
                                            "--attributions", path, "--attributions-sha256", digest)
                self.assertEqual((code, document["refusal"]["rule"]), (2, "ATTRIBUTIONS"))
        code, document, _ = compare(base, runs["baseline"], runs["candidate"], "half.json", "--attributions", path)
        self.assertEqual((code, document["refusal"]["rule"]), (2, "USAGE"))


class Probes(unittest.TestCase):
    """W3's probes PR-6 to PR-8 of review 001, kept as tests."""

    def test_tr06_probe_pr6_a_non_random_name_below_the_temporary_directory_is_not_masked(self):
        tmp = "/synthetic-tmp/T"

        def case(component):
            class Paths(unittest.TestCase):
                __module__, __qualname__ = "test_probe", "Paths"

                def test_reads_a_plan(self):
                    self.fail("cannot read " + tmp + "/" + component + "/plan.json")
            return Paths
        base, runs = runs_of(self, {"baseline": [case("tmpabcd1234")], "candidate": [case("a-differently-named-directory")]})
        code, document, _ = compare(base, runs["baseline"], runs["candidate"], "pr6.json",
                                    "--baseline-tmpdir", tmp, "--candidate-tmpdir", tmp)
        self.assertEqual(ids(document["different_reason"]), ["test_reads_a_plan"])
        entry = document["different_reason"][0]
        self.assertEqual((entry["baseline"]["reasons"], entry["candidate"]["reasons"]),
                         (["AssertionError: cannot read <tmp>/*/plan.json"],
                          ["AssertionError: cannot read <tmp>/a-differently-named-directory/plan.json"]))
        self.assertEqual(document["unchanged_not_passing"], [])

    def test_tr06_a_run_path_is_replaced_only_at_component_boundaries(self):
        def case(workspace):
            class Sibling(unittest.TestCase):
                __module__, __qualname__ = "test_probe", "Sibling"

                def test_names_a_sibling(self):
                    self.fail("see " + workspace + "2/x.py and " + workspace + "/tests/x.py")
            return Sibling
        base = S.temp_dir(self)
        runs = {}
        for version in ("baseline", "candidate"):
            directory = os.path.join(base, version)
            os.makedirs(directory)
            runs[version] = S.driver_run(self, directory, S.unittest_log(case(directory + "/workspace")))
        code, document, _ = compare(base, runs["baseline"], runs["candidate"], "boundary.json")
        entry = document["unchanged_not_passing"][0]
        # the sibling workspace2 is not the workspace: only its parent, the output directory, is replaced
        self.assertEqual(entry["baseline"]["reasons"],
                         ["AssertionError: see <output>/workspace2/x.py and <workspace>/tests/x.py"])
        self.assertEqual(entry["candidate"]["reasons"], entry["baseline"]["reasons"])

    def test_tr03_probe_pr7_a_report_summary_that_differs_with_equal_statuses(self):
        base, runs = runs_of(self, {"baseline": [Plain], "candidate": [Plain]},
                             candidate={"surface_summary": {"total": 12, "pending": 0, "passed": 11}})
        code, document, stderr = compare(base, runs["baseline"], runs["candidate"], "pr7.json")
        self.assertEqual(code, 1, stderr)
        summaries = document["summaries"]
        self.assertEqual(summaries["steps_different"], [])
        self.assertEqual([(row["step"], row["report"]) for row in summaries["reports_different"]],
                         [("surface", "reports/surface.json")])
        row = summaries["reports_different"][0]
        self.assertEqual((row["baseline_outcomes"]["summary"]["total"], row["candidate_outcomes"]["summary"]["passed"]),
                         (12, 11))
        self.assertTrue(document["identical_item_4_lists"])

    def test_tr04_probe_pr8_a_skipped_baseline_test_that_errors_is_newly_not_passing(self):
        def case(version):
            class Readback(unittest.TestCase):
                __module__, __qualname__ = "test_probe", "Readback"

                def test_q01(self):
                    if version == "baseline":
                        self.skipTest("dependencies unavailable")
                    raise RuntimeError("now an error")
            return Readback
        base, runs = runs_of(self, {"baseline": [case("baseline")], "candidate": [case("candidate")]})
        code, document, _ = compare(base, runs["baseline"], runs["candidate"], "pr8.json")
        self.assertEqual(ids(document["new_not_passing"]), ["test_q01"])
        self.assertEqual(ids(document["different_outcome"]), ["test_q01"])
        self.assertEqual(document["new_not_passing"][0]["baseline"]["outcome"], "skipped")

    def test_tr04_an_expected_failure_that_now_fails_is_newly_not_passing(self):
        def case(version):
            class Expected(unittest.TestCase):
                __module__, __qualname__ = "test_probe", "Expected"

                def test_x(self):
                    raise RuntimeError("broken")
            if version == "baseline":
                Expected.test_x = unittest.expectedFailure(Expected.test_x)
            return Expected
        base, runs = runs_of(self, {"baseline": [case("baseline")], "candidate": [case("candidate")]})
        code, document, _ = compare(base, runs["baseline"], runs["candidate"], "expected.json")
        self.assertEqual(ids(document["new_not_passing"]), ["test_x"])
        self.assertEqual(document["new_not_passing"][0]["baseline"]["outcome"], "expected_failure")


class Bindings(unittest.TestCase):
    def setUp(self):
        self.base = S.temp_dir(self)
        self.runs = {}
        for version in ("baseline", "candidate"):
            directory = os.path.join(self.base, version)
            os.makedirs(directory)
            self.runs[version] = S.driver_run(self, directory, S.unittest_log(S.Outcomes))

    def run_compare(self, baseline, candidate, name):
        output = os.path.join(self.base, name)
        code, _ = S.run_tool(LOG, S.compare_argv(baseline, candidate, output))
        return code, S.read_json(output)

    def test_a_summary_that_names_another_log_refuses(self):
        other = dict(self.runs["candidate"])
        text = S.unittest_log(S.Outcomes, S.TearDownError)
        path = os.path.join(self.base, "other.log")
        other.update(log=path, log_sha256=S.write(path, text))
        code, document = self.run_compare(self.runs["baseline"], other, "binding.json")
        self.assertEqual((code, document["refusal"]["rule"]), (2, "BINDING"))

    def test_a_summary_or_log_with_another_digest_refuses(self):
        code, document = self.run_compare(self.runs["baseline"], dict(self.runs["candidate"], summary_sha256="1" * 64),
                                          "summary.json")
        self.assertEqual((code, document["refusal"]["rule"], document["refusal"]["details"]["role"]), (2, "DIGEST", "SUMMARY"))
        code, document = self.run_compare(dict(self.runs["baseline"], log_sha256="2" * 64), self.runs["candidate"], "log.json")
        self.assertEqual((code, document["refusal"]["details"]["role"]), (2, "LOG"))

    def test_an_unreadable_log_refuses_the_comparison(self):
        directory = os.path.join(self.base, "truncated")
        os.makedirs(directory)
        text = S.unittest_log(S.Outcomes)
        truncated = S.driver_run(self, directory, text[:len(text) // 2])
        code, document = self.run_compare(self.runs["baseline"], truncated, "truncated.json")
        self.assertEqual((code, document["refusal"]["rule"]), (2, "FOOTER"))


class SkipsAndOccurrences(unittest.TestCase):
    def test_a_different_skip_reason_and_a_repeated_id_are_listed(self):
        def case(reason):
            class Skips(unittest.TestCase):
                __module__, __qualname__ = "test_cmp", "Skips"

                def test_skip(self):
                    self.skipTest(reason)

                def test_twice(self):
                    pass
            return Skips
        base = S.temp_dir(self)
        runs = {}
        for version, reason in (("baseline", "first reason"), ("candidate", "second reason")):
            directory = os.path.join(base, version)
            os.makedirs(directory)
            cls = case(reason)
            text = S.unittest_log(cls, duplicate=cls if version == "candidate" else None)
            runs[version] = S.driver_run(self, directory, text)
        code, document, stderr = compare(base, runs["baseline"], runs["candidate"], "skips.json")
        self.assertEqual(code, 1, stderr)
        self.assertEqual(ids(document["different_skip_reason"]), ["test_skip"])
        self.assertEqual(ids(document["different_occurrences"]), ["test_skip", "test_twice"])
        self.assertEqual(document["unchanged"]["skipped"], 0)


class FixtureOutcomes(unittest.TestCase):
    def test_a_class_that_fails_at_setup_instead_of_skipping_is_visible(self):
        base, runs = runs_of(self, {"baseline": [readback_case("baseline"), S.Outcomes],
                                    "candidate": [readback_case("candidate"), S.Outcomes]})
        code, document, _ = compare(base, runs["baseline"], runs["candidate"], "fixture.json")
        self.assertEqual(code, 1)
        self.assertEqual(ids(document["removed_ids"]), ["test_changed", "test_q01", "test_q03"])
        self.assertEqual({entry["baseline"]["outcome"] for entry in document["removed_ids"]}, {"skipped"})
        self.assertEqual(ids(document["added_ids"]), ["setUpClass (test_cmp.Readback)"])
        self.assertEqual(ids(document["new_not_passing"]), ["setUpClass (test_cmp.Readback)"])
        self.assertEqual(document["new_not_passing"][0]["candidate"]["reasons"],
                         ["RuntimeError: No approved current-host readback selection: ordinary run, not a qualification"])
        self.assertEqual(document["no_longer_failing"], [])


if __name__ == "__main__":
    unittest.main()
