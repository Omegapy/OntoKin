"""CPU corruption and one-attempt controls; never starts or imports Blender."""

from __future__ import annotations

import ast
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common
import run


class ReopenControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="c218-reopen-control-")
        self.base = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_scene_lock_rejects_same_length_corruption(self):
        scene = self.base / "fixture.blend"
        scene.write_bytes(b"scene authority")
        binding = common.descriptor(scene.read_bytes())
        with mock.patch.object(common, "SCENE_DESCRIPTOR", binding):
            self.assertEqual(common.verify_scene(scene), scene)
            scene.write_bytes(b"scene authoritx")
            with self.assertRaisesRegex(RuntimeError, "bytes differ"):
                common.verify_scene(scene)

    def test_scene_lock_rejects_symlink_even_matching_bytes(self):
        target = self.base / "target.blend"
        target.write_bytes(b"scene authority")
        link = self.base / "link.blend"
        link.symlink_to(target)
        with mock.patch.object(common, "SCENE_DESCRIPTOR", common.descriptor(target.read_bytes())):
            with self.assertRaisesRegex(RuntimeError, "nonsymlink"):
                common.verify_scene(link)

    def test_relative_bindings_refuse_escape_and_git_metadata(self):
        for name in ("../escape", "/absolute", ".git/HEAD", "a/../escape", ".", "", "a//b"):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                common.safe_relative(name)
        self.assertEqual(common.safe_relative("prior/import-details.json"), Path("prior/import-details.json"))

    def test_command_is_reopen_only_and_disables_scripts(self):
        command = run.native_command(self.base, "reopen", "/usr/bin/blender")
        self.assertIn("--disable-autoexec", command)
        self.assertEqual(command[command.index("--threads") + 1], "2")
        self.assertEqual(command[-1], "reopen")
        for phase in ("import", "retry", "", None):
            with self.subTest(phase=phase), self.assertRaises(RuntimeError):
                run.native_command(self.base, phase, "/usr/bin/blender")

    def test_mutated_plan_cannot_expand_start_budget(self):
        plan = {"schema": "ontokin.c218.native-reopen-plan/0.1", "maxNativeStarts": 2,
                "commands": {"reopen": []}}
        common.write_json(self.base / "plan.json", plan)
        with self.assertRaisesRegex(RuntimeError, "one reopen"):
            common.verify_run(self.base, HERE)

    def test_mutated_plan_cannot_add_import_route(self):
        plan = {"schema": "ontokin.c218.native-reopen-plan/0.1", "maxNativeStarts": 1,
                "commands": {"reopen": [], "import": []}}
        common.write_json(self.base / "plan.json", plan)
        with self.assertRaisesRegex(RuntimeError, "one reopen"):
            common.verify_run(self.base, HERE)

    def approval(self, plan):
        review = self.base / "independent-review.json"
        review.write_bytes(b'{"decision":"TEST_ONLY_NO_NATIVE"}\n')
        path = self.base / "approval.json"
        approval = {"schema": "ontokin.c218.native-reopen-approval/0.1",
                    "decision": "APPROVE_NATIVE_START", "phase": "reopen",
                    "sourceRevision": plan["sourceRevision"], "planSha256": common.digest(common.canonical(plan)),
                    "maxNativeStarts": 1, "integrator": "synthetic-test-only",
                    "independentReview": {"path": str(review), "file": common.descriptor(review.read_bytes())}}
        common.write_json(path, approval)
        return path, review

    def test_approval_refuses_changed_plan_or_review(self):
        plan = {"sourceRevision": "a" * 40}
        approval, review = self.approval(plan)
        run.approval_record(self.base, plan, "reopen", approval)
        with self.assertRaisesRegex(RuntimeError, "different source or plan"):
            run.approval_record(self.base, {**plan, "changed": True}, "reopen", approval)
        review.write_bytes(b'{"decision":"CHANGED"}\n')
        with self.assertRaisesRegex(RuntimeError, "review bytes differ"):
            run.approval_record(self.base, plan, "reopen", approval)

    def launch_fixture(self):
        plan = {"sourceRevision": "a" * 40, "maxNativeStarts": 1, "maximumSecondsPerStart": 240,
                "commands": {"reopen": run.native_command(self.base, "reopen", "/nonexecuted/blender")},
                "environmentOverrides": common.REOPEN_ENVIRONMENT,
                "isolatedBlenderDirectories": common.ISOLATED_DIRECTORIES}
        build = {"executable": {"path": "/nonexecuted/blender"}, "importer_root": str(self.base / "importer")}
        return plan, build

    def test_unknown_reservation_blocks_process_creation(self):
        plan, build = self.launch_fixture()
        approval, _ = self.approval(plan)
        common.write_json(self.base / "reopen-reservation.json", {"outcome": "UNKNOWN"})
        with mock.patch.object(run, "verify_run", return_value=(plan, build)), \
             mock.patch.object(run, "git", side_effect=lambda *args: "a" * 40 if args[0] == "rev-parse" else ""), \
             mock.patch.object(run.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(RuntimeError, "one unreserved reopen"):
                run.launch(self.base, "reopen", approval)
            spawn.assert_not_called()

    def test_failed_spawn_consumes_reservation_and_keeps_unknown_receipt(self):
        plan, build = self.launch_fixture()
        approval, _ = self.approval(plan)
        with mock.patch.object(run, "verify_run", return_value=(plan, build)), \
             mock.patch.object(run, "git", side_effect=lambda *args: "a" * 40 if args[0] == "rev-parse" else ""), \
             mock.patch.object(run.subprocess, "Popen", side_effect=OSError("synthetic spawn failure")) as spawn:
            with self.assertRaisesRegex(OSError, "synthetic spawn failure"):
                run.launch(self.base, "reopen", approval)
            self.assertEqual(spawn.call_count, 1)
            receipt = common.read_json(self.base / "reopen-process.json")
            self.assertEqual(receipt["outcome"], "LAUNCH_FAILED_NO_PROCESS_OBSERVED")
            self.assertIsNone(receipt["pid"])
            self.assertTrue((self.base / "reopen-reservation.json").is_file())
            with self.assertRaisesRegex(RuntimeError, "one unreserved reopen"):
                run.launch(self.base, "reopen", approval)
            self.assertEqual(spawn.call_count, 1)

    def test_capture_has_no_product_repair_or_save_operators(self):
        tree = ast.parse((HERE / "capture.py").read_text())
        operators = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name.startswith("bpy.ops."):
                    operators.append(name)
        self.assertEqual(sorted(operators), ["bpy.ops.render.render", "bpy.ops.wm.open_mainfile"])
        opened = next(node for node in ast.walk(tree) if isinstance(node, ast.Call)
                      and ast.unparse(node.func) == "bpy.ops.wm.open_mainfile")
        keywords = {item.arg: ast.literal_eval(item.value) for item in opened.keywords
                    if item.arg in ("load_ui", "use_scripts")}
        self.assertEqual(keywords, {"load_ui": False, "use_scripts": False})
        forbidden = {"normals_split_custom_set", "normals_split_custom_set_from_vertices", "from_pydata", "clear_geometry"}
        self.assertFalse(any(isinstance(node, ast.Attribute) and node.attr in forbidden for node in ast.walk(tree)))

    def test_post_spawn_receipt_failure_stops_owned_process_group(self):
        plan, build = self.launch_fixture()
        approval, _ = self.approval(plan)

        class FakeProcess:
            pid = 918273
            returncode = None

            def poll(self):
                return self.returncode

            def wait(self, timeout):
                self.returncode = -9
                return self.returncode

        process = FakeProcess()
        writer = run.write_json

        def fail_launched(path, value, **kwargs):
            if Path(path).name == "reopen-launched.json":
                raise OSError("synthetic launched receipt failure")
            return writer(path, value, **kwargs)

        with mock.patch.object(run, "verify_run", return_value=(plan, build)), \
             mock.patch.object(run, "git", side_effect=lambda *args: "a" * 40 if args[0] == "rev-parse" else ""), \
             mock.patch.object(run.subprocess, "Popen", return_value=process) as spawn, \
             mock.patch.object(run, "write_json", side_effect=fail_launched), \
             mock.patch.object(run.os, "killpg") as kill, \
             mock.patch.object(run, "group_exists", return_value=False):
            with self.assertRaisesRegex(OSError, "launched receipt failure"):
                run.launch(self.base, "reopen", approval)
            spawn.assert_called_once()
            kill.assert_called_once_with(process.pid, run.signal.SIGKILL)
        receipt = common.read_json(self.base / "reopen-process.json")
        self.assertEqual(receipt["outcome"], "FAILED_EXCEPTION_PROCESS_STOPPED")
        self.assertEqual(receipt["exceptionCleanupSignal"], "SIGKILL")
        self.assertEqual(receipt["returncode"], -9)
        self.assertIs(receipt["groupStillExists"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
