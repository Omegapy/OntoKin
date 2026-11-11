"""Child-free C200 compatibility controls; no Blender process is started.

Normal discovery runs the worker boundary controls. Direct execution with
--pinned-exporter additionally executes the exact installed exporter's Python
callback and complete execute method with native/downstream work replaced by
in-process observations. Neither cohort qualifies native geometry or delivery.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import ExitStack
import hashlib
import json
import logging
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "prototypes/static_tray_v01/worker.py"
SETTINGS = ROOT / "prototypes/static_tray_v01/export-settings.json"
PINNED_SHA256 = "82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e"
PINNED_DEBUG_SHA256 = "a0112a1488ce1520f6554f1c337494845ab0aea9b683a73b0b747505d6a2fa94"
HELPERS = {"digest", "write_json", "assert_operator", "exporter_compatibility",
           "prepare_inactive_action_filter", "export_with_startup_receipt"}


def worker_helpers(bpy, addon):
    tree = ast.parse(WORKER.read_bytes(), filename=str(WORKER))
    selected = [node for node in tree.body if
                (isinstance(node, ast.FunctionDef) and node.name in HELPERS) or
                (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
                 t.id in {"PINNED_EXPORTER_SHA256", "FILTER_PROPERTIES"} for t in node.targets))]
    namespace = {"bpy":bpy, "sys":SimpleNamespace(modules={"io_scene_gltf2":addon}),
                 "hashlib":hashlib, "json":json, "logging":logging, "Path":Path}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(WORKER), "exec"), namespace)
    return namespace


def fake_bpy():
    class Scene:
        pass
    scene = Scene()
    context = SimpleNamespace(scene=scene, space_data=None,
                              preferences=SimpleNamespace(addons={}))
    return SimpleNamespace(types=SimpleNamespace(Scene=Scene), context=context,
                           data=SimpleNamespace(scenes=[scene], actions=[]),
                           app=SimpleNamespace(debug=False, debug_python=False, debug_value=0,
                                               version=(4,5,3), build_hash=b"67807e1800cc"),
                           props=SimpleNamespace(CollectionProperty=lambda **kw:[], IntProperty=lambda:0),
                           ops=SimpleNamespace(export_scene=SimpleNamespace()))


class WorkerExporterCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="static-tray-c200-cpu-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.settings = json.loads(SETTINGS.read_bytes())
        self.settings["filepath"] = str(self.out / "raw.glb")
        self.bpy = fake_bpy()
        self.addon = SimpleNamespace(__file__="/cpu-control/pinned/__init__.py",
                                     GLTF2_filter_action=type("GLTF2_filter_action", (), {}),
                                     set_debug_log=lambda:logging.INFO)
        self.worker = worker_helpers(self.bpy, self.addon)
        actual_digest = self.worker["digest"]
        self.worker["digest"] = lambda path: PINNED_SHA256 if str(path)==self.addon.__file__ else actual_digest(path)
        self.calls = []
        self.callback_enabled = True
        self.export_error = None
        self.export_status = {"FINISHED"}
        self.logger_level = logging.INFO
        self.startup = {"flags":{"isolated":0, "ignore_environment":0, "no_user_site":1,
                                 "safe_path":True, "hash_randomization":0, "dont_write_bytecode":1},
                        "origin":"synthetic CPU startup observation"}
        self.job = {"record_sha256":"cpu-record", "settings_sha256":"cpu-settings"}
        properties = [SimpleNamespace(identifier=name) for name in ["rna_type", *self.settings]]
        owner = self
        class Operator:
            def get_rna_type(self):
                return SimpleNamespace(properties=properties)
            def __call__(self, *args, **kwargs):
                # Receipt ordering is inspected at the operation boundary.
                owner.calls.append((args, kwargs, json.loads((owner.out/"native-startup.json").read_bytes())))
                if owner.callback_enabled:
                    owner.bpy.data.scenes[0].gltf_action_filter.clear()
                    del owner.bpy.types.Scene.gltf_action_filter
                    del owner.bpy.types.Scene.gltf_action_filter_active
                if owner.export_error:
                    raise owner.export_error
                logging.getLogger("glTFImporter").setLevel(owner.logger_level)
                logging.getLogger("glTFImporter_errors").setLevel(logging.ERROR)
                return owner.export_status
        self.bpy.ops.export_scene.gltf = Operator()
        for name in ("glTFImporter", "glTFImporter_errors"):
            logger = logging.getLogger(name)
            self.addCleanup(logger.setLevel, logger.level)

    def run_export(self):
        return self.worker["export_with_startup_receipt"](self.settings, self.startup, self.job, self.out)

    def test_full_explicit_inventory_and_measured_receipt_precede_export(self):
        result = self.run_export()
        self.assertEqual(len(self.settings), 108)
        self.assertEqual(len(self.calls), 1)
        args, settings, before = self.calls[0]
        self.assertEqual(args, ("EXEC_DEFAULT",))
        self.assertEqual(settings, self.settings)
        self.assertIs(settings["export_action_filter"], False)
        self.assertEqual(settings["export_loglevel"], -1)
        self.assertEqual(before["python_startup"], self.startup)
        self.assertEqual(before["operator_settings"], settings)
        self.assertEqual(before["delivery_state"], "NOT_EXPORTED")
        self.assertNotIn("passed", before)
        self.assertEqual(before["exporter_policy"]["omitted_operator_properties"], [])
        self.assertEqual(before["action_filter_initialization"],
                         {"action_count":0, "scene_count":1, "filter_count":0, "active_index":0})
        self.assertEqual(result["logging_observed"], {"logger_level":20, "error_logger_level":40})
        self.assertTrue(result["action_filter_properties_removed"])
        self.assertEqual(result["startup_receipt_sha256"],
                         hashlib.sha256((self.out/"native-startup.json").read_bytes()).hexdigest())

    def test_export_failure_retains_startup_without_delivery_success(self):
        self.export_error = RuntimeError("injected export failure")
        with self.assertRaisesRegex(RuntimeError, "injected export failure"):
            self.run_export()
        receipt = json.loads((self.out/"native-startup.json").read_bytes())
        self.assertEqual(receipt["phase"], "BEFORE_EXPORT")
        self.assertEqual(receipt["record_sha256"], "cpu-record")
        self.assertEqual(receipt["settings_sha256"], "cpu-settings")
        self.assertEqual(receipt["python_startup"], self.startup)
        self.assertFalse((self.out/"native-result.json").exists())
        self.assertEqual(len(self.calls), 1)

    def test_missing_or_extra_operator_property_is_rejected(self):
        old = self.settings.pop("export_action_filter")
        with self.assertRaisesRegex(RuntimeError, "property coverage"):
            self.run_export()
        self.settings["export_action_filter"] = old
        self.settings["unexpected_property"] = False
        with self.assertRaisesRegex(RuntimeError, "property coverage"):
            self.run_export()
        self.assertEqual(self.calls, [])

    def test_positive_log_level_and_active_filter_are_rejected(self):
        for key, value in (("export_loglevel",20), ("export_action_filter",True),
                           ("export_animations",True), ("will_save_settings",True)):
            with self.subTest(setting=key):
                original = self.settings[key]
                self.settings[key] = value
                with self.assertRaisesRegex(RuntimeError, "compatibility settings"):
                    self.run_export()
                self.settings[key] = original
        self.assertEqual(self.calls, [])

    def test_changed_debug_state_cannot_select_suppression_or_profiling(self):
        for key, value in (("debug_value",1), ("debug_value",102),
                           ("debug",True), ("debug_python",True)):
            with self.subTest(debug=key, value=value):
                old = getattr(self.bpy.app, key)
                setattr(self.bpy.app, key, value)
                with self.assertRaisesRegex(RuntimeError, "debug state"):
                    self.run_export()
                setattr(self.bpy.app, key, old)
        self.assertEqual(self.calls, [])

    def test_changed_source_or_logging_resolution_is_rejected(self):
        digest = self.worker["digest"]
        self.worker["digest"] = lambda path:"unreviewed"
        with self.assertRaisesRegex(RuntimeError, "implementation differs"):
            self.run_export()
        self.worker["digest"] = digest
        self.addon.set_debug_log = lambda:logging.WARNING
        with self.assertRaisesRegex(RuntimeError, "effective logging"):
            self.run_export()
        self.assertEqual(self.calls, [])

    def test_preexisting_filter_state_is_preserved_and_rejected(self):
        original = ["unexpected prior item"]
        self.bpy.types.Scene.gltf_action_filter = original
        with self.assertRaisesRegex(RuntimeError, "preexisting action-filter"):
            self.run_export()
        self.assertEqual(self.bpy.context.scene.gltf_action_filter, original)
        self.assertEqual(self.calls, [])

    def test_actions_and_multiple_scenes_are_rejected_before_preparation(self):
        self.bpy.data.actions.append(object())
        with self.assertRaisesRegex(RuntimeError, "single action-free"):
            self.run_export()
        self.bpy.data.actions.clear()
        self.bpy.data.scenes.append(self.bpy.types.Scene())
        with self.assertRaisesRegex(RuntimeError, "single action-free"):
            self.run_export()
        self.assertEqual(self.calls, [])
        self.assertFalse(hasattr(self.bpy.types.Scene, "gltf_action_filter"))

    def test_callback_failure_cannot_be_treated_as_success(self):
        self.callback_enabled = False
        with self.assertRaisesRegex(RuntimeError, "callback did not remove"):
            self.run_export()
        self.assertEqual(len(self.calls), 1)
        self.assertTrue((self.out/"native-startup.json").is_file())
        self.assertFalse((self.out/"native-result.json").exists())

    def test_cancelled_operator_and_wrong_actual_logging_are_rejected(self):
        self.export_status = {"CANCELLED"}
        with self.assertRaisesRegex(RuntimeError, "did not finish"):
            self.run_export()
        self.assertEqual(len(self.calls), 1)
        self.export_status = {"FINISHED"}
        self.logger_level = logging.WARNING
        with self.assertRaisesRegex(RuntimeError, "Actual exporter logger levels"):
            self.run_export()
        self.assertEqual(len(self.calls), 2)
        self.assertFalse((self.out/"native-result.json").exists())


def pinned_source_suite(source_path):
    """Add opt-in controls of exact installed source without loading bpy."""
    source = Path(source_path).resolve()
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINNED_SHA256:
        raise ValueError("Pinned installed exporter source hash differs")
    tree = ast.parse(raw, filename=str(source))
    base = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name=="ExportGLTF2_Base")
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and
                 n.name in {"on_export_action_filter_changed", "set_debug_log"}]
    functions += [n for n in base.body if isinstance(n, ast.FunctionDef) and n.name=="execute"]
    debug_path = source.parent / "io/com/debug.py"
    debug_raw = debug_path.read_bytes()
    if hashlib.sha256(debug_raw).hexdigest() != PINNED_DEBUG_SHA256:
        raise ValueError("Pinned installed exporter logging source hash differs")

    class PinnedExporterSourceControls(unittest.TestCase):
        def setUp(self):
            self.bpy = fake_bpy()
            self.globals = {"__package__":"c200_pinned_exporter", "bpy":self.bpy,
                            "GLTF2_filter_action":type("GLTF2_filter_action", (), {}),
                            "is_draco_available":lambda:False}
            exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), "exec"), self.globals)
            self.captures = []
            self.hooks = []
            self.debug_module = ModuleType("c200_pinned_exporter.io.com.debug")
            exec(compile(debug_raw, str(debug_path), "exec"), self.debug_module.__dict__)
            self.modules = {}
            for name in ("c200_pinned_exporter", "c200_pinned_exporter.io", "c200_pinned_exporter.io.com",
                         "c200_pinned_exporter.io.exp", "c200_pinned_exporter.io.exp.user_extensions",
                         "c200_pinned_exporter.io.com.path", "c200_pinned_exporter.blender",
                         "c200_pinned_exporter.blender.exp", "c200_pinned_exporter.blender.exp.export"):
                self.modules[name] = ModuleType(name)
                self.modules[name].__path__ = []
            self.modules[self.debug_module.__name__] = self.debug_module
            self.modules["c200_pinned_exporter.io.exp.user_extensions"].export_user_extensions = lambda *args:self.hooks.append(args[0])
            self.modules["c200_pinned_exporter.io.com.path"].path_to_uri = lambda value:value
            def save(context, settings):
                self.captures.append(settings)
                return {"FINISHED"}
            self.modules["c200_pinned_exporter.blender.exp.export"].save = save
            self.modules["c200_pinned_exporter.blender.exp"].export = self.modules["c200_pinned_exporter.blender.exp.export"]
            self.stack = ExitStack()
            self.addCleanup(self.stack.close)
            self.stack.enter_context(patch.dict(sys.modules, self.modules))
            for name in ("glTFImporter", "glTFImporter_errors"):
                logger = logging.getLogger(name)
                self.addCleanup(logger.setLevel, logger.level)
                handlers = list(logger.handlers)
                self.addCleanup(lambda logger=logger, handlers=handlers:setattr(logger,"handlers",handlers))

        def operator(self, loglevel=-1):
            values = json.loads(SETTINGS.read_bytes())
            values["filepath"] = "/cpu-control/raw.glb"
            values["export_loglevel"] = loglevel
            return SimpleNamespace(**values, check=lambda context:None,
                                   report=lambda *args:self.fail("Unexpected exporter report"))

        def test_exact_source_defaults_bind_both_repair_decisions(self):
            # Annotated Blender properties carry their factory call in annotation.
            properties = {n.target.id:n.annotation for n in base.body if isinstance(n, ast.AnnAssign)
                          and isinstance(n.target, ast.Name)}
            logging_defaults = {kw.arg:kw.value for kw in properties["export_loglevel"].keywords}
            filter_defaults = {kw.arg:kw.value for kw in properties["export_action_filter"].keywords}
            self.assertEqual(ast.literal_eval(logging_defaults["default"]), -1)
            self.assertIs(ast.literal_eval(filter_defaults["default"]), False)
            self.assertEqual(filter_defaults["update"].id, "on_export_action_filter_changed")

        def test_complete_pinned_execute_uses_info_logging_with_negative_sentinel(self):
            # Exercise both selected compression-library availability branches.
            for draco_available in (False, True):
                with self.subTest(draco_available=draco_available):
                    self.globals["is_draco_available"] = lambda:draco_available
                    status = self.globals["execute"](self.operator(), self.bpy.context)
                    self.assertEqual(status, {"FINISHED"})
                    settings = self.captures[-1]
                    self.assertEqual(settings["gltf_loglevel"], -1)
                    self.assertEqual(settings["loglevel"], logging.INFO)
                    self.assertEqual(settings["log"].logger.level, logging.INFO)
                    self.assertEqual(settings["log"].error_logger.level, logging.ERROR)
                    self.assertIs(settings["gltf_animations"], False)
                    self.assertIs(settings["gltf_draco_mesh_compression"], False)
            self.assertEqual(self.hooks, ["pre_export_hook", "post_export_hook"] * 2)

        def test_complete_pinned_execute_reproduces_original_positive_level_failure(self):
            with self.assertRaisesRegex(KeyError, "loglevel"):
                self.globals["execute"](self.operator(20), self.bpy.context)
            self.assertEqual(self.captures, [])
            self.assertEqual(self.hooks, [])

        def test_original_false_callback_failure_and_reviewed_initialization(self):
            callback = self.globals["on_export_action_filter_changed"]
            operator = self.operator()
            with self.assertRaises(AttributeError):
                callback(operator, self.bpy.context)
            addon = SimpleNamespace(GLTF2_filter_action=self.globals["GLTF2_filter_action"])
            worker = worker_helpers(self.bpy, addon)
            observed = worker["prepare_inactive_action_filter"](addon)
            self.assertEqual(observed["filter_count"], 0)
            callback(operator, self.bpy.context)
            for name in ("gltf_action_filter", "gltf_action_filter_active"):
                self.assertFalse(hasattr(self.bpy.types.Scene, name))
                self.assertFalse(hasattr(self.bpy.context.scene, name))
            self.assertIs(operator.export_action_filter, False)

        def test_exact_debug_mapping_exposes_why_zero_is_required(self):
            for debug, level in ((0,20), (1,30), (2,40), (3,50), (4,10), (102,20)):
                with self.subTest(debug=debug):
                    self.bpy.app.debug_value = debug
                    self.assertEqual(self.globals["set_debug_log"](), level)

    return unittest.defaultTestLoader.loadTestsFromTestCase(PinnedExporterSourceControls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned-exporter", type=Path)
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(WorkerExporterCompatibilityTests)
    if args.pinned_exporter:
        suite.addTests(pinned_source_suite(args.pinned_exporter))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
