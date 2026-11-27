"""The readback evidence reader on synthetic provider records of a qualifying driver run."""
import json
import os
import unittest

import w2_support as S

TOOL = "readback_evidence"


class Reader(unittest.TestCase):
    preserved = True

    def setUp(self):
        self.run_paths = S.make_driver_run(self, preserved=self.preserved)
        self.count = 0

    def read(self, *, command="run", **options):
        self.count += 1
        output = os.path.join(self.run_paths["base"], "reading-%d.json" % self.count)
        code, stderr = S.run_tool(TOOL, S.reader_argv(self.run_paths, output, command=command, **options))
        return code, S.read_json(output), stderr

    def assertFails(self, *names, command="run", **options):
        code, document, stderr = self.read(command=command, **options)
        self.assertEqual((code, document["passed"]), (1, False), stderr)
        for name in names:
            self.assertIn(name, document["failed_checks"])
        return document

    def cohort(self, *parts):
        return os.path.join(self.run_paths["cohort"], *parts)

    def new_audit(self):
        path = os.path.join(self.run_paths["base"], "audit-%d.json" % self.count)
        digest = S.write(path, json.dumps(S.audit_record(self.run_paths["cohort"])))
        return {"audit": path, "audit_sha256": digest}


class ConsistentRecords(Reader):
    def test_a_consistent_qualifying_run_passes_every_check(self):
        code, document, stderr = self.read()
        self.assertEqual(code, 0, stderr)
        self.assertTrue(document["passed"], document["failed_checks"])
        self.assertEqual(document["starts"]["established"], 3)
        self.assertEqual([row["case"] for row in document["starts"]["rows"]],
                         ["Q01-positive", "Q03-positive", "Q01-changed-reference"])
        self.assertEqual(document["cohort"]["route"], "preserved")
        self.assertGreater(len(document["checks"]), 120)
        self.assertEqual(document["driver_run"]["derived"]["config_path"], self.run_paths["selection"])
        self.assertEqual(document["numerical_audit"]["expected_tool_sha256"], S.AUDIT_TOOL_SHA256)

    def test_the_cohort_command_reads_the_same_cohort_without_a_summary(self):
        code, document, stderr = self.read(command="cohort")
        self.assertEqual(code, 0, stderr)
        self.assertIsNone(document["driver_run"])
        self.assertNotIn("cohort_setup_names_the_derived_selection", document["checks"])


class KeptInPlace(Reader):
    preserved = False

    def test_a_root_named_by_the_override_is_read_in_place(self):
        code, document, stderr = self.read()
        self.assertEqual(code, 0, stderr)
        self.assertEqual(document["cohort"]["route"], "kept_in_place")
        self.assertEqual(document["cohort"]["original_root"], self.run_paths["cohort"])


class Starts(Reader):
    def test_a_missing_started_record_leaves_the_start_unestablished(self):
        os.remove(self.cohort("provider-ledgers", "Q03-positive", "started.json"))
        document = self.assertFails("case_Q03_positive_start_established_by_a_positive_pid",
                                    "exactly_three_starts_established", "cohort_holds_exactly_the_expected_files",
                                    "preservation_lists_exactly_the_retained_files")
        self.assertEqual(document["starts"]["established"], 2)

    def test_a_start_without_a_positive_pid_is_not_established(self):
        S.rewrite_json(self.cohort("provider-ledgers", "Q01-positive", "started.json"),
                       lambda value: value["process"].update(pid=0))
        self.assertFails("case_Q01_positive_start_established_by_a_positive_pid", "exactly_three_starts_established")


class Attempts(Reader):
    def test_a_negative_case_that_exits_zero_fails(self):
        S.rewrite_json(self.cohort("provider-ledgers", "Q01-changed-reference", "result.json"),
                       lambda value: value["process"].update(returncode=0))
        self.assertFails("case_Q01_changed_reference_receipt_exit_status",
                         "case_Q01_changed_reference_cohort_descriptor_binds_the_result",
                         "case_Q01_changed_reference_supervisor_receipt_file_equals_the_ledger")

    def test_a_provider_failure_or_a_changed_postflight_fails(self):
        S.rewrite_json(self.cohort("provider-ledgers", "Q01-positive", "result.json"),
                       lambda value: value.update(provider_failure={"code": "CH-EVIDENCE"},
                                                  postflight=dict(value["postflight"], config_sha256="0" * 64)))
        self.assertFails("case_Q01_positive_result_no_provider_failure",
                         "case_Q01_positive_result_preflight_equals_postflight")

    def test_a_finalization_marker_or_an_extra_stage_file_fails(self):
        S.write(self.cohort("provider-ledgers", "Q01-positive", "finalization.failed.json"), b"{}")
        S.write(self.cohort("Q03-positive", "extra.txt"), b"extra")
        self.assertFails("no_finalization_failure_marker", "cohort_holds_exactly_the_expected_files",
                         "case_Q03_positive_artifacts_after_are_the_retained_bytes")

    def test_a_link_inside_the_cohort_fails(self):
        os.symlink(self.cohort("Q01-positive", "job.json"), self.cohort("Q01-positive", "link.json"))
        self.assertFails("cohort_no_link_or_special_file")

    def test_the_original_temporary_root_must_be_gone(self):
        os.makedirs(self.run_paths["original"])
        self.assertFails("original_root_absent_now")

    def test_a_job_that_binds_other_input_bytes_fails(self):
        S.rewrite_json(self.cohort("Q03-positive", "job.json"), lambda value: value.update(artifact_sha256="9" * 64))
        self.assertFails("case_Q03_positive_job_binds_its_inputs_and_manifest",
                         "case_Q03_positive_preflight_binds_the_job_inputs_and_selection")


class Audit(Reader):
    def test_an_audit_by_another_harness_fails(self):
        self.assertFails("audit_tool_is_the_bound_harness", tool_sha256="b" * 64)

    def test_an_audit_of_other_bytes_fails(self):
        audit = self.new_audit()
        os.remove(self.cohort("Q01-positive", "probe.json"))
        S.write(self.cohort("Q01-positive", "probe.json"), b'{"passed": true}')
        self.assertFails("audit_Q01_positive_inputs_are_the_bytes_read_here",
                         "case_Q01_positive_artifacts_after_are_the_retained_bytes", **audit)

    def test_a_failed_audit_fails(self):
        path = os.path.join(self.run_paths["base"], "failed-audit.json")
        digest = S.write(path, json.dumps(S.audit_record(self.run_paths["cohort"], passed=False)))
        self.assertFails("audit_passed", "audit_Q01_positive_passed", audit=path, audit_sha256=digest)

    def test_an_audit_with_another_digest_refuses(self):
        code, document, _ = self.read(audit_sha256="c" * 64)
        self.assertEqual((code, document["refusal"]["rule"]), (2, "DIGEST"))
        code, document, _ = self.read(tool_sha256="XYZ")
        self.assertEqual((code, document["refusal"]["rule"]), (2, "USAGE"))


class DriverRun(Reader):
    def test_a_unit_step_given_another_selection_fails(self):
        def change(value):
            value["steps"][0]["environment_overrides"]["ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"] = "8" * 64
        digest = S.rewrite_json(self.run_paths["summary"], change)
        self.run_paths["summary_sha256"] = digest
        self.assertFails("unit_step_received_the_derived_selection")

    def test_an_ordinary_run_is_not_read_as_qualifying(self):
        def change(value):
            value["readback_selection"].update(run_kind="ordinary", status="absent")
        self.run_paths["summary_sha256"] = S.rewrite_json(self.run_paths["summary"], change)
        self.assertFails("summary_run_kind_qualifying_and_workspace_bound")

    def test_a_cohort_set_up_by_another_selection_fails(self):
        S.rewrite_json(self.cohort("setup.json"), lambda value: value.update(config_sha256="7" * 64))
        self.assertFails("cohort_setup_names_the_derived_selection", "manifest_names_the_setup_selection",
                         "preservation_lists_exactly_the_retained_files")

    def test_an_extra_file_in_the_readback_binding_fails(self):
        S.write(os.path.join(self.run_paths["output"], "readback-binding", "extra.json"), b"{}")
        self.assertFails("readback_binding_holds_exactly_four_files")

    def test_a_changed_original_selection_fails(self):
        os.remove(self.run_paths["original_config"])
        S.write(self.run_paths["original_config"], b'{"schema": "changed"}')
        self.assertFails("original_selection_file_unchanged")

    def test_a_changed_selection_file_fails(self):
        S.rewrite_json(self.run_paths["selection"], lambda value: value.update(evidence_root="/elsewhere"))
        self.assertFails("derived_selection_is_the_binding_file", "cohort_inside_the_evidence_root")

    def test_a_summary_with_another_digest_or_a_link_path_refuses(self):
        output = os.path.join(self.run_paths["base"], "refused.json")
        argv = S.reader_argv(dict(self.run_paths, summary_sha256="d" * 64), output)
        code, _ = S.run_tool(TOOL, argv)
        self.assertEqual((code, S.read_json(output)["refusal"]["rule"]), (2, "DIGEST"))
        link = os.path.join(self.run_paths["base"], "cohort-link")
        os.symlink(self.run_paths["cohort"], link)
        output = os.path.join(self.run_paths["base"], "refused-link.json")
        code, _ = S.run_tool(TOOL, S.reader_argv(dict(self.run_paths, cohort=link), output))
        self.assertEqual((code, S.read_json(output)["refusal"]["rule"]), (2, "COHORT"))


class DashBGuard(unittest.TestCase):
    def test_a_start_without_dash_b_refuses_before_any_other_import(self):
        module = S.tool(TOOL)

        class Flags:
            dont_write_bytecode = 0
        self.assertTrue(module._missing_dash_b(Flags))
        with self.assertRaises(module.Refusal):
            module.require_dash_b(Flags)
        source = (S.TOOLING / (TOOL + ".py")).read_text(encoding="utf-8")
        guard = source.index('if __name__ == "__main__" and _missing_dash_b():')
        self.assertLess(guard, source.index("import argparse"))
        self.assertEqual([line for line in source[:guard].splitlines() if line.startswith(("import ", "from "))],
                         ["import sys"])


if __name__ == "__main__":
    unittest.main()
