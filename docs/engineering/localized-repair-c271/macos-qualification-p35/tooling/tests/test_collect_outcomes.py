"""Focused tests of collect_outcomes.py on synthetic test modules; children: the interpreter with -B, and
/usr/bin/true started by one synthetic control inside the collector."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import unittest

import mh_support as S

CONFIG_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG"
DIGEST_ENV = "ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256"
METHODS_SCHEMA = "ontokin.current-host-readback-methods/0.2.0"
PREFIX = "tests.test_static_tray_readback_v01."
CPU = ("test_q01_actual_synthetic_meshes_load_in_both_libraries",
       "test_q03_actual_synthetic_rotations_load_in_both_libraries",
       "test_three_rejects_changed_synthetic_reference")
SEAMS = ("test_result_write_failure_leaves_predecessor_gate_blocked",
         "test_host_alarm_cannot_interrupt_supervisor_cleanup",
         "test_success_finalization_uses_remaining_outer_alarm",
         "test_uncertain_marker_removal_recreates_pending")
# tools/check_local.py git_environment(root), apart from GIT_CEILING_DIRECTORIES, which names the root's parent.
DRIVER_GIT = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
              "GIT_ATTR_NOSYSTEM": "1", "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1",
              "GIT_NO_LAZY_FETCH": "1"}

SETUP_REFUSED = """import unittest
class ReadbackCPUControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raise RuntimeError("synthetic setup refusal: no approved selection")
    def test_q01_actual_synthetic_meshes_load_in_both_libraries(self): pass
    def test_q03_actual_synthetic_rotations_load_in_both_libraries(self): pass
    def test_three_rejects_changed_synthetic_reference(self): pass
class ReadbackCoordinatorSeams(unittest.TestCase):
    def test_result_write_failure_leaves_predecessor_gate_blocked(self): pass
    def test_host_alarm_cannot_interrupt_supervisor_cleanup(self): pass
    def test_success_finalization_uses_remaining_outer_alarm(self): pass
    def test_uncertain_marker_removal_recreates_pending(self): pass
"""
ALL_PASS = SETUP_REFUSED.replace('        raise RuntimeError("synthetic setup refusal: no approved selection")\n',
                                 "        cls.ready = True\n")
MIXED = """import unittest
class ReadbackCPUControls(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        raise RuntimeError("synthetic teardown error")
    def test_q01_actual_synthetic_meshes_load_in_both_libraries(self): pass
    def test_q03_actual_synthetic_rotations_load_in_both_libraries(self): self.fail("synthetic failure")
    def test_three_rejects_changed_synthetic_reference(self): raise ValueError("synthetic error")
class ReadbackCoordinatorSeams(unittest.TestCase):
    def test_result_write_failure_leaves_predecessor_gate_blocked(self): self.skipTest("synthetic skip")
    @unittest.expectedFailure
    def test_host_alarm_cannot_interrupt_supervisor_cleanup(self): self.fail("expected")
    @unittest.expectedFailure
    def test_success_finalization_uses_remaining_outer_alarm(self): pass
    def test_uncertain_marker_removal_recreates_pending(self):
        for index in range(3):
            with self.subTest(index=index):
                self.assertNotEqual(index, 1)
"""
INTERRUPTED = ALL_PASS.replace("    def test_q03_actual_synthetic_rotations_load_in_both_libraries(self): pass\n",
                               "    def test_q03_actual_synthetic_rotations_load_in_both_libraries(self):\n"
                               "        import os, signal\n        os.kill(os.getpid(), signal.SIGINT)\n")
SUBTEST_SKIP = ALL_PASS.replace("    def test_uncertain_marker_removal_recreates_pending(self): pass\n",
                                "    def test_uncertain_marker_removal_recreates_pending(self):\n"
                                "        with self.subTest(index=1):\n"
                                "            self.skipTest('synthetic subtest skip')\n")
UNPLANNED = ALL_PASS.replace("    def test_uncertain_marker_removal_recreates_pending(self): pass\n",
                             "    def test_uncertain_marker_removal_recreates_pending(self):\n"
                             "        class Inner(unittest.TestCase):\n"
                             "            def test_inner(self): pass\n"
                             "        Inner('test_inner').run(self._outcome.result)\n")
CONTROLS = """import subprocess, unittest
class SupervisorProcessControls(unittest.TestCase):
    def test_mc37_synthetic_one_child(self):
        completed = subprocess.run(["/usr/bin/true"], env={"MH_VALUE_NAME": "value-never-" + "written"})
        self.assertEqual(completed.returncode, 0)
    def test_not_selected(self):
        raise AssertionError("a control that was not named ran")
"""
CONTROL = "tests.test_current_host_readback_controls_v02.SupervisorProcessControls.test_mc37_synthetic_one_child"


def bodies_of(text):
    """Per Class.test_method: the SHA-256 of the AST dump of its body, as the provider's ORIGINAL_BODIES is computed."""
    rows = {}
    for group in ast.parse(text).body:
        if isinstance(group, ast.ClassDef):
            for node in group.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                    dump = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
                    rows[group.name + "." + node.name] = hashlib.sha256(dump.encode()).hexdigest()
    return rows


class CollectorWorld:
    """A synthetic root with the cohort module, a HOST that names this interpreter, a methods document and a
    frozen environment."""

    def __init__(self, test, cohort_text, *, launcher=None, controls_text=None, bodies=None):
        self.test, self.base = test, S.resolved_temp(test)
        self.root = self.base + "/root"
        self.module = S.write(self.root + "/tests/test_static_tray_readback_v01.py", cohort_text)
        self.controls = None
        if controls_text is not None:
            self.controls = S.write(self.root + "/tests/test_current_host_readback_controls_v02.py", controls_text)
        launcher = S.PYTHON if launcher is None else launcher
        host = {"schema": "ontokin.current-host-readback-host/0.2.0",
                "python": {"launcher": launcher, "venv": os.path.dirname(os.path.dirname(launcher)),
                           "interpreter": {"implementation": sys.implementation.name,
                                           "version": platform.python_version(), "build_string": sys.version,
                                           "process_image": S.process_image()}}}
        self.host = S.write(self.base + "/selection/HOST.json", json.dumps(host).encode(), 0o644)
        methods = {"schema": METHODS_SCHEMA, "source_test": "tests/test_static_tray_readback_v01.py",
                   "original_bodies": bodies_of(cohort_text) if bodies is None else bodies,
                   "discovery": {"path": "/synthetic", "sha256": "d" * 64, "size_bytes": 1, "mode": "0o644"}}
        self.methods = S.write(self.base + "/selection/methods.json", S.canonical(methods), 0o644)
        config = {"schema": "ontokin.current-host-readback-config/0.2.0", "host": S.descriptor(self.host),
                  "methods": S.descriptor(self.methods)}
        self.config = S.write(self.base + "/selection/config.json", S.canonical(config), 0o600)
        self.digest = S.sha256_file(self.config)

    def environment(self, *, selection=True, **extra):
        environment = S.child_environment(PYTHONNOUSERSITE="1")
        if selection:
            environment.update({CONFIG_ENV: self.config, DIGEST_ENV: self.digest})
        environment.update(extra)
        return environment

    def run(self, command, *, environment, frozen=None, flags=("-B",), extra_args=(), module_sha256=True,
            tool_path=None):
        frozen = environment if frozen is None else frozen
        index = len(os.listdir(self.base))
        env_file, env_digest = S.frozen_environment(self.base + "/environment-%d.json" % index, frozen)
        output = self.base + "/outcomes-%d" % index
        args = [command, "--root", self.root, "--environment", env_file, "--environment-sha256", env_digest,
                "--output-dir", output, *extra_args]
        if module_sha256 and "--module-sha256" not in extra_args:
            args += ["--module-sha256", S.sha256_file(self.module if command == "cohort" else self.controls)]
        completed = S.run_tool("collect_outcomes.py", *args, flags=flags, env=environment, cwd=self.root,
                               tool_path=tool_path)
        record = S.read_json(output + "/outcomes.json") if os.path.isfile(output + "/outcomes.json") else None
        return completed, record, output


def by_raw(record):
    return {row["raw_id"]: row for row in record["tests"]}


class CohortTests(unittest.TestCase):
    def test_setup_error_is_kept_and_the_three_cpu_methods_are_not_run(self):
        world = CollectorWorld(self, SETUP_REFUSED)
        completed, record, _ = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "COMPLETED_WITH_OTHER_OUTCOMES")
        rows = by_raw(record)
        for name in CPU:
            self.assertEqual(rows[PREFIX + "ReadbackCPUControls." + name]["outcome"], "not_run")
        for name in SEAMS:
            row = rows[PREFIX + "ReadbackCoordinatorSeams." + name]
            self.assertEqual(row["outcome"], "pass")
            self.assertEqual(row["alias_id"], "test_static_tray_readback_v01.ReadbackCoordinatorSeams." + name)
            self.assertTrue(row["identity"]["joined"])
            self.assertIsNotNone(row["elapsed_s"])
        self.assertEqual(len(record["class_level_events"]), 1)
        event = record["class_level_events"][0]
        self.assertEqual(event["test"], "setUpClass (tests.test_static_tray_readback_v01.ReadbackCPUControls)")
        self.assertEqual(event["kind"], "error")
        self.assertIn("synthetic setup refusal", event["traceback"])
        required = {row["id"]: row["outcome"] for row in record["required_methods"]}
        self.assertEqual(required["test_static_tray_readback_v01.ReadbackCPUControls." + CPU[0]], "not_run")
        self.assertEqual(record["process_events"], [])
        self.assertEqual(record["unittest"]["tests_run"], 4)
        self.assertEqual(record["selection"]["checks"]["process_image"], True)
        self.assertIsNotNone(record["environment"]["admitted_cf_user_text_encoding"],
                             "macOS adds __CF_USER_TEXT_ENCODING to this interpreter; its value is recorded")
        journal = Path(record["journal"]["path"]).read_text().splitlines()
        self.assertEqual(len(journal), record["journal"]["lines"])
        self.assertIn("MH-OUTCOMES", completed.stderr.decode())
        self.assertIn("Ran 4 tests", completed.stderr.decode())

    def test_every_outcome_kind_is_recorded_raw(self):
        world = CollectorWorld(self, MIXED)
        completed, record, _ = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 1)
        rows = by_raw(record)
        cpu = {name: rows[PREFIX + "ReadbackCPUControls." + name]["outcome"] for name in CPU}
        seams = {name: rows[PREFIX + "ReadbackCoordinatorSeams." + name]["outcome"] for name in SEAMS}
        self.assertEqual(list(cpu.values()), ["pass", "fail", "error"])
        self.assertEqual(list(seams.values()), ["skip", "expected_failure", "unexpected_success", "fail"])
        subtests = [event for event in rows[PREFIX + "ReadbackCoordinatorSeams." + SEAMS[3]]["events"]]
        self.assertEqual([event["kind"] for event in subtests], ["subtest_pass", "subtest_failure", "subtest_pass"])
        self.assertIn("synthetic failure", rows[PREFIX + "ReadbackCPUControls." + CPU[1]]["events"][0]["traceback"])
        self.assertEqual([event["test"] for event in record["class_level_events"]],
                         ["tearDownClass (tests.test_static_tray_readback_v01.ReadbackCPUControls)"])
        decorated = rows[PREFIX + "ReadbackCoordinatorSeams." + SEAMS[1]]
        self.assertIsNone(decorated["alias_id"], "a decorated method does not join the declared alias")
        self.assertEqual(record["unittest"]["expected_failures"], 1)
        self.assertEqual(record["unittest"]["unexpected_successes"], 1)

    def test_all_seven_pass_gives_exit_zero(self):
        world = CollectorWorld(self, ALL_PASS)
        completed, record, _ = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "ALL_PASSED")
        self.assertEqual({row["outcome"] for row in record["required_methods"]}, {"pass"})
        self.assertTrue(record["module_unchanged"])
        self.assertTrue(all(row["equal"] for row in record["original_bodies"].values()))
        self.assertEqual(len(record["original_bodies"]), 7)
        self.assertEqual(record["unplanned_events"], [])
        self.assertIsNone(record["own_main_admitted"], "this copy of the collector lies outside the root")

    def test_an_interruption_is_unknown_and_keeps_the_journal(self):
        world = CollectorWorld(self, INTERRUPTED)
        completed, record, output = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(record["state"], "UNKNOWN")
        rows = by_raw(record)
        self.assertEqual(rows[PREFIX + "ReadbackCPUControls." + CPU[1]]["outcome"], "interrupted")
        self.assertEqual(rows[PREFIX + "ReadbackCPUControls." + CPU[2]]["outcome"], "not_run")
        self.assertEqual(record["interrupted"]["type"], "KeyboardInterrupt")
        self.assertTrue(os.path.getsize(output + "/journal.jsonl") > 0)

    def test_an_environment_other_than_the_frozen_one_refuses_before_any_test(self):
        world = CollectorWorld(self, ALL_PASS)
        environment = world.environment()
        completed, record, _ = world.run("cohort", environment=dict(environment, EXTRA_NAME="x"), frozen=environment)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(record["state"], "REFUSED")
        self.assertEqual(record["refusal"]["details"]["extra"], ["EXTRA_NAME"])
        self.assertNotIn("tests", record)

    def test_a_driver_removed_name_in_the_frozen_environment_refuses(self):
        world = CollectorWorld(self, ALL_PASS)
        environment = world.environment(DYLD_PRINT_LIBRARIES="1")
        completed, record, _ = world.run("cohort", environment=environment)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(record["refusal"]["details"]["names"], ["DYLD_PRINT_LIBRARIES"])

    def test_a_host_launcher_that_is_not_this_process_refuses(self):
        world = CollectorWorld(self, ALL_PASS, launcher="/nonexistent/.venv/bin/python")
        completed, record, _ = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(record["refusal"]["rule"], "PROVIDER-PRECONDITION")
        self.assertFalse(record["refusal"]["details"]["checks"]["executable_is_host_launcher"])

    def test_a_cohort_without_selection_refuses(self):
        world = CollectorWorld(self, ALL_PASS)
        completed, record, _ = world.run("cohort", environment=world.environment(selection=False))
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(record["refusal"]["rule"], "SELECTION")

    def test_an_isolated_launch_refuses(self):
        world = CollectorWorld(self, ALL_PASS)
        completed, record, _ = world.run("cohort", environment=world.environment(), flags=("-I", "-B"))
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(record["refusal"]["rule"], "PYTHON")


class RevisionTests(unittest.TestCase):
    """TR-01, TR-06 and TR-09."""

    def test_it_runs_from_its_committed_place_inside_the_root(self):
        """TR-01: its own __main__ lies under the root; it is admitted by realpath and recorded."""
        world = CollectorWorld(self, ALL_PASS)
        copy = S.in_place(world.root, "collect_outcomes.py")
        completed, record, _ = world.run("cohort", environment=world.environment(), tool_path=copy)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "ALL_PASSED")
        self.assertEqual(record["own_main_admitted"]["path"], copy)
        self.assertTrue(record["own_main_admitted"]["admitted"])
        self.assertNotIn(os.path.dirname(copy), record["sys_path_at_load"])

    def test_a_skip_inside_a_subtest_is_the_parents_skip(self):
        world = CollectorWorld(self, SUBTEST_SKIP)
        completed, record, _ = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        row = by_raw(record)[PREFIX + "ReadbackCoordinatorSeams." + SEAMS[3]]
        self.assertEqual(row["outcome"], "skip")
        self.assertIn("subtest_skip", [event["kind"] for event in row["events"]])
        self.assertEqual(record["unplanned_events"], [])
        self.assertEqual(record["state"], "COMPLETED_WITH_OTHER_OUTCOMES")

    def test_events_of_an_unplanned_test_are_kept_by_name(self):
        world = CollectorWorld(self, UNPLANNED)
        completed, record, _ = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        names = {event["test"] for event in record["unplanned_events"]}
        self.assertEqual(len(names), 1)
        self.assertTrue(next(iter(names)).endswith("<locals>.Inner.test_inner"))
        self.assertEqual(record["state"], "COMPLETED_WITH_OTHER_OUTCOMES")

    def test_the_module_digest_is_required_for_a_cohort_too(self):
        world = CollectorWorld(self, ALL_PASS)
        completed, record, _ = world.run("cohort", environment=world.environment(), module_sha256=False)
        self.assertEqual(completed.returncode, 2, completed.stderr.decode()[-3000:])
        self.assertIsNone(record)
        self.assertIn(b'"USAGE"', completed.stderr)

    def test_a_body_that_differs_from_the_frozen_original_bodies_is_not_all_passed(self):
        bodies = bodies_of(ALL_PASS)
        name = "ReadbackCoordinatorSeams." + SEAMS[0]
        bodies[name] = "0" * 63 + "1"
        world = CollectorWorld(self, ALL_PASS, bodies=bodies)
        completed, record, _ = world.run("cohort", environment=world.environment())
        self.assertEqual(completed.returncode, 1, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "COMPLETED_WITH_OTHER_OUTCOMES")
        self.assertFalse(record["original_bodies"][name]["equal"])
        self.assertEqual(sorted(key for key, row in record["original_bodies"].items() if not row["equal"]), [name])

    def test_git_names_are_refused_unless_they_are_exactly_the_drivers_own(self):
        world = CollectorWorld(self, ALL_PASS)
        completed, record, _ = world.run("cohort", environment=world.environment(GIT_DIR="/nonexistent"))
        self.assertEqual(completed.returncode, 2, completed.stderr.decode()[-3000:])
        self.assertEqual((record["refusal"]["rule"], record["refusal"]["details"]["names"]),
                         ("ENVIRONMENT", ["GIT_DIR"]))
        driver = dict(DRIVER_GIT, GIT_CEILING_DIRECTORIES=os.path.dirname(world.root))
        completed, record, _ = world.run("cohort", environment=world.environment(**driver))
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        self.assertEqual(record["state"], "ALL_PASSED")


class ControlTests(unittest.TestCase):
    def test_a_named_control_runs_alone_and_its_child_is_recorded(self):
        world = CollectorWorld(self, ALL_PASS, controls_text=CONTROLS)
        completed, record, _ = world.run("controls", environment=world.environment(selection=False),
                                         extra_args=("--test", CONTROL))
        S.count_tool_starts("/usr/bin/true", 1)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        self.assertEqual([row["raw_id"] for row in record["tests"]], [CONTROL])
        self.assertEqual(record["tests"][0]["outcome"], "pass")
        self.assertIsNone(record["tests"][0]["alias_id"])
        self.assertEqual([event["argv"] for event in record["process_events"]], [["/usr/bin/true"]])
        # TR-06: the child's environment by its names and a digest, never its values.
        self.assertEqual(record["process_events"][0]["environment"]["names"], ["MH_VALUE_NAME"])
        self.assertFalse("value-never-written" in json.dumps(record["process_events"]), "a value was written")

    def test_a_control_rerun_refuses_a_selection_and_another_module(self):
        world = CollectorWorld(self, ALL_PASS, controls_text=CONTROLS)
        completed, record, _ = world.run("controls", environment=world.environment(), extra_args=("--test", CONTROL))
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "SELECTION"))
        completed, record, _ = world.run("controls", environment=world.environment(selection=False),
                                         extra_args=("--test", "tests.test_static_tray_readback_v01.X.test_y"))
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "TARGET"))
        completed, record, _ = world.run("controls", environment=world.environment(selection=False),
                                         extra_args=("--test", CONTROL, "--module-sha256", "0" * 63 + "1"))
        self.assertEqual((completed.returncode, record["refusal"]["rule"]), (2, "TARGET"))


if __name__ == "__main__":
    unittest.main()
