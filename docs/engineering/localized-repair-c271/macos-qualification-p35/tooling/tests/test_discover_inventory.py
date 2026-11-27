"""Focused tests of discover_inventory.py on synthetic roots; children: the interpreter with -B only.

Against an earlier collector (discovery schema /1, which takes no frozen environment), discover is
started without the environment arguments, so that each test of a fix fails on what the fix changes."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

import mh_support as S

CHECK_LOCAL = '''def build_plan(python):
    stages = []

    def add(stage_id, argv):
        if argv[0] == python:
            argv = [python, "-B", *argv[1:]]
        stages.append((stage_id, argv))
    add("unit-tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"])
    add("force-agent-tests", [python, "-m", "unittest", "discover", "-s", "tests", "-p", "x*.py"])
    return stages
'''
OTHER_CHECK_LOCAL = CHECK_LOCAL.replace('"discover", "-s", "tests", "-v"]', '"discover", "-s", "t"]')
OTHER_FLAGS_CHECK_LOCAL = CHECK_LOCAL.replace('[python, "-B", *argv[1:]]', '[python, "-B", "-X", "dev", *argv[1:]]')
ADDITIONS_SCHEMA = "ontokin.c271.p33-inventory-additions/1"
LEGACY = S.legacy("discover_inventory.py", 'runtime-discovery/1"')


def module(text):
    return "import unittest\n" + text


def make_root(base, name, modules, check_local=CHECK_LOCAL, extra=None):
    root = Path(base) / name
    S.write(root / "tools/check_local.py", check_local)
    for filename, text in modules.items():
        S.write(root / "tests" / filename, text)
    for rel, text in (extra or {}).items():
        S.write(root / rel, text)
    return str(root)


def discover(base, root, *, flags=("-B",), output=None, environment=None, frozen=None, tool_path=None):
    """One discover start under an exact frozen environment (the child environment unless given)."""
    environment = S.child_environment() if environment is None else environment
    output = output or base + "/out-%d.json" % len(os.listdir(base))
    args = ["discover", "--root", root]
    if not LEGACY:
        path, digest = S.frozen_environment(base + "/environment-%d.json" % len(os.listdir(base)),
                                            environment if frozen is None else frozen)
        args += ["--environment", path, "--environment-sha256", digest]
    completed = S.run_tool("discover_inventory.py", *args, "--output", output, flags=flags, env=environment,
                           tool_path=tool_path)
    return completed, output


class DiscoverTests(unittest.TestCase):
    def setUp(self):
        self.base = S.resolved_temp(self)
        self.marker = self.base + "/a-test-ran"

    def test_lists_ids_as_unittest_discovers_them_and_runs_no_test(self):
        marker = self.marker
        root = make_root(self.base, "root", {
            "test_alpha.py": module("class A(unittest.TestCase):\n"
                                    "    def test_one(self): open(%r, 'w').close()\n"
                                    "    def test_two(self): pass\n" % marker),
            "test_beta.py": module("from rootpkg.helper import VALUE\n"
                                   "class B(unittest.TestCase):\n    def test_three(self): pass\n"),
            "helper_not_a_test.py": module("class H(unittest.TestCase):\n    def test_hidden(self): pass\n")},
            extra={"rootpkg/__init__.py": "", "rootpkg/helper.py": "VALUE = 1\n"})
        completed, output = discover(self.base, root)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        record = S.read_json(output)
        self.assertEqual(record["ids_in_discovery_order"],
                         ["test_alpha.A.test_one", "test_alpha.A.test_two", "test_beta.B.test_three"])
        self.assertEqual(record["state"], "COMPLETE")
        self.assertEqual(record["process_events"], [])
        self.assertEqual(record["failed_imports"], [])
        self.assertEqual(record["unit_stage"]["argv_after_interpreter"],
                         ["-m", "unittest", "discover", "-s", "tests", "-v"])
        self.assertEqual(record["unit_stage"]["discovery"], {"start": "tests", "pattern": "test*.py", "top": None})
        self.assertEqual(record["sys_path_at_discovery"][0], root)
        self.assertEqual(record["sys_path_after_discovery"][:2], [root + "/tests", root])
        self.assertNotIn(str(S.TOOLING), record["sys_path_at_discovery"])
        self.assertEqual(record["tool"]["sha256"], S.sha256_file(S.TOOLING / "discover_inventory.py"))
        self.assertFalse(os.path.exists(marker), "a test method ran during discovery")
        self.assertEqual(record["invocation"]["python"]["flags"]["dont_write_bytecode"], 1)
        self.assertTrue(any(row["path"] == "tests/test_beta.py" for row in record["loaded_project_files"]))
        self.assertEqual(record["bytecode_present"], [])
        # TR-07: the -B flag is derived from build_plan's add(), not asserted.
        self.assertEqual(record["unit_stage"]["interpreter_flags_added_by_build_plan"], ["-B"])
        self.assertEqual(record["unit_stage"]["derived_from"], "build_plan.add, by its AST")
        self.assertIsNone(record["own_main_admitted"], "this copy of the collector lies outside the root")

    def test_import_failures_and_a_refused_process_start_are_findings(self):
        marker = self.marker
        root = make_root(self.base, "root", {
            "test_alpha.py": module("class A(unittest.TestCase):\n    def test_one(self): pass\n"),
            "test_broken.py": module("import module_that_does_not_exist\n"),
            "test_spawns.py": module("import subprocess\nsubprocess.run(['/bin/sh', '-c', 'echo > %s'],"
                                     " env={'MH_VALUE_NAME': 'value-never-written'})\n"
                                     "class C(unittest.TestCase):\n    def test_never(self): pass\n" % marker),
            "test_shadow.py": module("import discover_inventory\n")})
        completed, output = discover(self.base, root)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode())
        record = S.read_json(output)
        self.assertEqual(record["state"], "COMPLETE_WITH_FINDINGS")
        self.assertEqual(record["ids_in_discovery_order"], ["test_alpha.A.test_one"])
        self.assertEqual(sorted(row["name"] for row in record["failed_imports"]),
                         ["test_broken", "test_shadow", "test_spawns"])
        self.assertEqual(len(record["process_events"]), 1)
        event = record["process_events"][0]
        self.assertEqual((event["event"], event["blocked"], event["argv"][0]), ("subprocess.Popen", True, "/bin/sh"))
        self.assertFalse(os.path.exists(marker), "the refused start ran")
        # TR-06: a child's environment is recorded by its names and a digest, never its values.
        self.assertEqual(event["environment"]["names"], ["MH_VALUE_NAME"])
        self.assertFalse("value-never-written" in json.dumps(record["process_events"]), "a value was written")

    def test_the_unit_stage_argv_must_be_the_one_reproduced(self):
        root = make_root(self.base, "root", {"test_alpha.py": module("")}, check_local=OTHER_CHECK_LOCAL)
        completed, output = discover(self.base, root)
        self.assertEqual(completed.returncode, 2)
        record = S.read_json(output)
        self.assertEqual((record["state"], record["refusal"]["rule"]), ("REFUSED", "UNIT-STAGE"))

    def test_interpreter_flags_other_than_dash_b_in_build_plan_refuse(self):
        """TR-07: the flag comes from build_plan's add(), so a different flag set refuses."""
        root = make_root(self.base, "root", {"test_alpha.py": module("")}, check_local=OTHER_FLAGS_CHECK_LOCAL)
        completed, output = discover(self.base, root)
        self.assertEqual(completed.returncode, 2, completed.stderr.decode())
        record = S.read_json(output)
        self.assertEqual(record["refusal"]["rule"], "UNIT-STAGE")
        self.assertEqual(record["refusal"]["details"]["flags"], ["-B", "-X", "dev"])

    def test_an_isolated_launch_is_refused(self):
        root = make_root(self.base, "root", {"test_alpha.py": module("")})
        completed, output = discover(self.base, root, flags=("-I", "-S", "-B"))
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "PYTHON")

    def test_an_existing_output_is_never_replaced(self):
        root = make_root(self.base, "root", {"test_alpha.py": module("")})
        output = S.write(self.base + "/existing.json", b"keep")
        completed, _ = discover(self.base, root, output=output)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(Path(output).read_bytes(), b"keep")

    def test_a_symlinked_root_is_refused(self):
        root = make_root(self.base, "root", {"test_alpha.py": module("")})
        os.symlink(root, self.base + "/alias")
        completed, output = discover(self.base, self.base + "/alias")
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "ROOT")


class PlaceAndEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.base = S.resolved_temp(self)

    def test_it_runs_from_its_committed_place_inside_the_root(self):
        """TR-01: its own __main__ lies under the root; it is admitted by realpath and recorded."""
        root = make_root(self.base, "root", {"test_alpha.py": module(
            "class A(unittest.TestCase):\n    def test_one(self): pass\n")})
        copy = S.in_place(root, "discover_inventory.py")
        completed, output = discover(self.base, root, tool_path=copy)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        record = S.read_json(output)
        self.assertEqual(record["state"], "COMPLETE")
        self.assertEqual(record["ids_in_discovery_order"], ["test_alpha.A.test_one"])
        self.assertEqual(record["own_main_admitted"]["path"], copy)
        self.assertEqual(record["tool"]["path"], copy)
        self.assertNotIn(os.path.dirname(copy), record["sys_path_at_discovery"])

    def test_every_other_preloaded_root_module_still_refuses(self):
        root = make_root(self.base, "root", {"test_alpha.py": module("")},
                         extra={"sitecustomize.py": "LOADED_BEFORE_THE_TOOL = True\n"})
        environment = S.child_environment(PYTHONPATH=root)
        completed, output = discover(self.base, root, environment=environment)
        self.assertEqual(completed.returncode, 2, completed.stderr.decode()[-3000:])
        record = S.read_json(output)
        self.assertEqual(record["refusal"]["rule"], "PYTHON")
        self.assertEqual(record["refusal"]["details"]["modules"], ["sitecustomize"])

    def test_the_process_environment_must_be_exactly_the_frozen_one(self):
        """TR-06: an exact frozen environment, recorded by name; HOME is never part of one."""
        root = make_root(self.base, "root", {"test_alpha.py": module("")})
        environment = S.child_environment(MH_FROZEN_NAME="frozen-value-never-written")
        completed, output = discover(self.base, root, environment=environment)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode()[-3000:])
        record = S.read_json(output)
        self.assertIn("MH_FROZEN_NAME", record["environment"]["names"])
        self.assertFalse(b"frozen-value-never-written" in Path(output).read_bytes(), "a frozen value was written")
        completed, output = discover(self.base, root, environment=environment, frozen=S.child_environment())
        self.assertEqual(completed.returncode, 2)
        refusal = S.read_json(output)["refusal"]
        self.assertEqual((refusal["rule"], refusal["details"]["extra"]), ("ENVIRONMENT", ["MH_FROZEN_NAME"]))
        with_home = S.child_environment(HOME=self.base)
        completed, output = discover(self.base, root, environment=with_home)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(S.read_json(output)["refusal"]["reason"], "HOME is not part of a frozen environment")


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.base = S.resolved_temp(self)
        alpha = module("class A(unittest.TestCase):\n    def test_one(self): pass\n    def test_two(self): pass\n")
        beta = module("class B(unittest.TestCase):\n    def test_three(self): pass\n")
        gamma = module("class G(unittest.TestCase):\n    def test_four(self): pass\n")
        self.baseline = self.discovered(make_root(self.base, "baseline", {"test_alpha.py": alpha}))
        self.current = self.discovered(make_root(self.base, "current", {"test_alpha.py": alpha, "test_beta.py": beta}))
        self.unapproved = self.discovered(make_root(self.base, "unapproved", {"test_alpha.py": alpha,
                                                                              "test_beta.py": beta,
                                                                              "test_gamma.py": gamma}))

    def discovered(self, root):
        completed, output = discover(self.base, root, output=self.base + "/" + os.path.basename(root) + ".json")
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        return output

    def additions(self, added, name="additions.json", **overrides):
        document = {"schema": ADDITIONS_SCHEMA, "base_commit": "b" * 39 + "a", "candidate_commit": "c" * 39 + "a",
                    "base_count": 2, "candidate_count": 2 + len(added), "added_count": len(added), "removed_count": 0,
                    "added_by_module": {}, "failed_imports": [], "approval": "synthetic", "added": added,
                    "removed": []}
        for item in added:
            key = item.split(".")[0]
            document["added_by_module"][key] = document["added_by_module"].get(key, 0) + 1
        document.update(overrides)
        return S.write(self.base + "/" + name, json.dumps(document).encode())

    def arguments(self, current, additions, output, *, current_digest=None, baseline=None):
        baseline = baseline or self.baseline
        return ["compare", "--current", current, "--current-sha256", current_digest or S.sha256_file(current),
                "--baseline", baseline, "--baseline-sha256", S.sha256_file(baseline),
                "--additions", additions, "--additions-sha256", S.sha256_file(additions), "--output", output]

    def compare(self, current, additions, *, current_digest=None, name=None, baseline=None):
        output = self.base + "/" + (name or "comparison-%d.json" % len(os.listdir(self.base)))
        completed = S.run_tool("discover_inventory.py", *self.arguments(current, additions, output,
                                                                        current_digest=current_digest,
                                                                        baseline=baseline),
                               flags=("-I", "-S", "-B"))
        return completed, output

    def test_exact_match_of_baseline_plus_approved_additions(self):
        completed, output = self.compare(self.current, self.additions(["test_beta.B.test_three"]))
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        record = S.read_json(output)
        self.assertTrue(record["exact_match"])
        self.assertEqual((record["missing"], record["extra"], record["expected_count"]), ([], [], 3))
        self.assertTrue(all(record["consistency"].values()))
        self.assertEqual(record["inputs_clean"], {"current_clean": True, "baseline_clean": True})

    def test_missing_and_extra_ids_are_reported(self):
        additions = self.additions(["test_beta.B.test_three", "test_beta.B.test_absent"], name="additions-2.json")
        completed, output = self.compare(self.unapproved, additions)
        self.assertEqual(completed.returncode, 1)
        record = S.read_json(output)
        self.assertFalse(record["exact_match"])
        self.assertEqual(record["missing"], ["test_beta.B.test_absent"])
        self.assertEqual(record["extra"], ["test_gamma.G.test_four"])

    def test_an_inconsistent_additions_record_is_not_an_exact_match(self):
        additions = self.additions(["test_beta.B.test_three"], name="additions-3.json", base_count=5587)
        completed, output = self.compare(self.current, additions)
        self.assertEqual(completed.returncode, 1)
        record = S.read_json(output)
        self.assertEqual((record["missing"], record["extra"]), ([], []))
        self.assertFalse(record["consistency"]["baseline_count_matches_base_count"])

    def test_a_duplicate_inside_the_baseline_is_not_an_exact_match(self):
        """TR-07: counts and duplicates are recomputed from the IDs of both documents."""
        baseline = S.read_json(self.baseline)
        baseline["ids_in_discovery_order"].append(baseline["ids_in_discovery_order"][0])
        duplicated = S.write(self.base + "/baseline-duplicated.json", json.dumps(baseline).encode())
        completed, output = self.compare(self.current, self.additions(["test_beta.B.test_three"], name="additions-5.json"),
                                         baseline=duplicated)
        self.assertEqual(completed.returncode, 1, completed.stderr.decode())
        record = S.read_json(output)
        self.assertFalse(record["exact_match"])
        self.assertEqual(record["baseline"]["duplicates_recomputed"], ["test_alpha.A.test_one"])
        self.assertFalse(record["baseline"]["consistent"])
        self.assertFalse(record["inputs_clean"]["baseline_clean"])

    def test_a_digest_mismatch_refuses(self):
        completed, output = self.compare(self.current, self.additions(["test_beta.B.test_three"], name="additions-4.json"),
                                         current_digest="0" * 63 + "1")
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "DIGEST")

    def test_compare_refuses_a_start_without_dash_b(self):
        """TR-17, in this process with sys.flags as a start without -B shows them; nothing is started."""
        tool = S.load_module("mh_discover_under_test", str(S.TOOLING / "discover_inventory.py"))
        output = self.base + "/comparison-without-b.json"
        arguments = self.arguments(self.current, self.additions(["test_beta.B.test_three"], name="additions-6.json"),
                                   output)
        with mock.patch.object(sys, "flags", S.FlagsWithoutB()), contextlib.redirect_stderr(io.StringIO()):
            code = tool.main(arguments)
        self.assertEqual(code, 2)
        self.assertEqual(S.read_json(output)["refusal"]["rule"], "PYTHON")


if __name__ == "__main__":
    unittest.main()
