"""Targeted CPU controls for inherited origin provenance and C218 boundaries; never loads Blender or its importer."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import canonical, descriptor, read_json, verify_installed, write_json
from origin_guard import classify_modules, inventory, snapshot_modules


class OriginControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="c217-origin-")
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "io_scene_gltf2"
        self.files = {"__init__.py": b"# synthetic package\n", "blender/__init__.py": b"# synthetic package\n",
                      "blender/com/node.py": b"SYNTHETIC = True\n"}
        for name, raw in self.files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.build = {"importer_root": str(self.root), "importer_python_files": [
            {"path": str(self.root / name), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            for name, raw in sorted(self.files.items())]}
        self.modules = {}
        for name, filename in (("io_scene_gltf2", "__init__.py"), ("io_scene_gltf2.blender", "blender/__init__.py"),
                               ("io_scene_gltf2.blender.com.node", "blender/com/node.py")):
            spec = importlib.util.spec_from_file_location(name, self.root / filename)
            self.modules[name] = importlib.util.module_from_spec(spec)
        parent_names = ("io_scene_gltf2", "io_scene_gltf2.blender")
        previous = {name: sys.modules.get(name) for name in parent_names}
        def restore_parents():
            for name, value in previous.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value
        self.addCleanup(restore_parents)
        for name in parent_names:
            sys.modules[name] = self.modules[name]
        name = "io_scene_gltf2.blender.com"
        loader = importlib.machinery.NamespaceLoader(name, [str(self.root / "blender/com")], importlib.machinery.PathFinder)
        spec = importlib.machinery.ModuleSpec(name, loader, is_package=True)
        spec.submodule_search_locations = [str(self.root / "blender/com")]
        module = importlib.util.module_from_spec(spec)
        module.__file__ = None
        self.modules[name] = module
        self.rows = snapshot_modules(self.modules)

    def tearDown(self):
        self.temporary.cleanup()

    def row(self, name="io_scene_gltf2.blender.com"):
        return next(row for row in self.rows if row["module"] == name)

    def reject_field(self, field, value, *, name="io_scene_gltf2.blender.com"):
        original = copy.deepcopy(self.rows)
        self.row(name)[field] = {"available": True, "value": value}
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)
        self.rows = original

    def test_pinned_source_and_namespace_accept(self):
        result = classify_modules(self.rows, self.build)
        self.assertEqual(len(result), 4)
        self.assertEqual(sum(row["kind"] == "namespace-package" for row in result), 1)
        self.assertTrue(all(row["cachedFileExists"] is False for row in result))

    def test_namespace_missing_file_differs_from_missing_source_file(self):
        del self.modules["io_scene_gltf2.blender.com"].__file__
        self.assertEqual(len(classify_modules(snapshot_modules(self.modules), self.build)), 4)
        del self.modules["io_scene_gltf2"].__file__
        with self.assertRaises(RuntimeError):
            classify_modules(snapshot_modules(self.modules), self.build)

    def test_source_origin_name_and_loader_conflicts(self):
        name = "io_scene_gltf2.blender.com.node"
        for field, value in (("specOrigin", str(self.root / "__init__.py")), ("specName", "io_scene_gltf2.wrong"),
                             ("moduleName", "io_scene_gltf2.wrong"), ("specHasLocation", False),
                             ("moduleLoaderClass", "custom.Loader"), ("specLoaderClass", "custom.Loader")):
            with self.subTest(field=field):
                self.reject_field(field, value, name=name)

    def test_namespace_missing_or_concrete_metadata_rejected(self):
        for field, value in (("specOrigin", "namespace"), ("file", str(self.root / "__init__.py")),
                             ("cached", str(self.base / "missing.pyc")), ("specCached", str(self.base / "missing.pyc")),
                             ("specHasLocation", True), ("moduleLoaderClass", None), ("specLoaderClass", None)):
            with self.subTest(field=field):
                self.reject_field(field, value)
        self.row()["specOrigin"] = {"available": False, "reason": "attribute-unavailable"}
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)

    def test_namespace_mixed_empty_duplicate_escaped_and_conflicting_locations(self):
        good = str(self.root / "blender/com")
        for locations in ([], [str(self.base)], [good, str(self.base)], [good, good], [str(self.root / "blender")],
                          [str(self.root / "blender/com/../com")], ["blender/com"]):
            for field in ("moduleSearchLocations", "specSearchLocations"):
                with self.subTest(locations=locations, field=field):
                    self.reject_field(field, locations)

    def test_namespace_symlink_alias_rejected(self):
        alias = self.base / "alias"
        alias.symlink_to(self.root / "blender/com", target_is_directory=True)
        self.reject_field("moduleSearchLocations", [str(alias)])

    def test_loader_objects_must_be_identical(self):
        self.row()["loaderObjectsIdentical"] = False
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)

    def test_source_bytes_drift_rejected(self):
        (self.root / "blender/com/node.py").write_bytes(b"changed\n")
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)

    def test_source_cache_absence_mismatch_and_existing_code_rejected(self):
        name = "io_scene_gltf2.blender.com.node"
        cached = self.row(name)["cached"]["value"]
        for field, value in (("cached", None), ("specCached", None), ("cached", str(self.base / "alien.pyc")),
                             ("specCached", str(self.base / "alien.pyc"))):
            with self.subTest(field=field, value=value):
                self.reject_field(field, value, name=name)
        self.row(name)["cached"] = self.row(name)["specCached"] = {"available": True, "value": str(self.base / "alien.pyc")}
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)
        self.rows = snapshot_modules(self.modules)
        cache = Path(cached)
        cache.parent.mkdir()
        cache.write_bytes(b"not valid pyc but still forbidden")
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)

    def test_only_explicit_private_cache_prefix_is_accepted(self):
        name = "io_scene_gltf2.blender.com.node"
        source = self.root / "blender/com/node.py"
        private = self.base / "private-cache"
        private.mkdir()
        default = self.row(name)["cached"]["value"]
        redirected = str(private / str(source.parent).lstrip("/") / Path(default).name)
        self.row(name)["cached"] = self.row(name)["specCached"] = {"available": True, "value": redirected}
        self.assertEqual(len(classify_modules(self.rows, self.build, (None, str(private)))), 4)
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build, (None,))

    def test_added_initializer_and_pinned_name_conflict_rejected(self):
        (self.root / "blender/com/__init__.py").write_bytes(b"unbound")
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)
        (self.root / "blender/com/__init__.py").unlink()
        path = self.root / "blender/com.py"
        path.write_bytes(b"collision")
        self.build["importer_python_files"].append({"path": str(path), "bytes": 9, "sha256": hashlib.sha256(b"collision").hexdigest()})
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)

    def test_unpinned_and_duplicate_module_names_rejected(self):
        self.rows.append(copy.deepcopy(self.rows[-1]))
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)
        self.rows = snapshot_modules(self.modules)
        self.row()["module"] = "io_scene_gltf2.unknown"
        self.row("io_scene_gltf2.unknown")["moduleName"]["value"] = "io_scene_gltf2.unknown"
        self.row("io_scene_gltf2.unknown")["specName"]["value"] = "io_scene_gltf2.unknown"
        with self.assertRaises(RuntimeError):
            classify_modules(self.rows, self.build)

    def test_raw_snapshot_retained_before_rejection(self):
        tree = ast.parse((HERE / "capture.py").read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "cache_receipt")
        fake_sys = types.SimpleNamespace(modules=self.modules, pycache_prefix=None, dont_write_bytecode=True,
                                        flags=types.SimpleNamespace(no_user_site=1, ignore_environment=0, isolated=0))
        namespace = {"sys": fake_sys, "Path": Path, "INITIAL_PYCACHE_PREFIX": None, "INITIAL_DONT_WRITE_BYTECODE": True,
                     "snapshot_modules": snapshot_modules, "classify_modules": classify_modules,
                     "write_json": write_json, "canonical": canonical, "descriptor": descriptor}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(HERE / "capture.py"), "exec"), namespace)
        self.modules["io_scene_gltf2.blender.com"].__path__ = [str(self.base)]
        with self.assertRaises(RuntimeError):
            namespace["cache_receipt"](self.base, self.build, "import", "control-rejection")
        raw = read_json(self.base / "import-importer-raw-control-rejection.json")
        self.assertEqual(len(raw["modules"]), 4)
        self.assertEqual(raw["modules"], snapshot_modules(self.modules))

    def test_static_installed_inventory_matches_preserved_build(self):
        build = read_json(HERE / "build_bindings.json")
        verify_installed(build)
        _, concrete, _, namespaces = inventory(build)
        self.assertEqual(len(concrete), 117)
        self.assertIn("io_scene_gltf2.blender.com", namespaces)
        self.assertEqual(str(namespaces["io_scene_gltf2.blender.com"]), build["importer_root"] + "/blender/com")

    def test_driver_has_one_reopen_and_no_import_or_save_route(self):
        tree = ast.parse((HERE / "capture.py").read_text())
        calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
        self.assertEqual(calls.count("open_mainfile"), 1)
        self.assertNotIn("save_as_mainfile", calls)
        self.assertNotIn("gltf", calls)
        self.assertNotIn("addon_enable", calls)
        driver = (HERE / "run.py").read_text()
        self.assertIn('"maxNativeStarts": 1', driver)
        self.assertIn('choices=("reopen",)', driver)
        self.assertNotIn('"maxNativeStarts": 2', driver)


if __name__ == "__main__":
    unittest.main(verbosity=2)
