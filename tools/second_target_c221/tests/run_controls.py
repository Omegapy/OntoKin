#!/usr/bin/env python3
"""CPU-only author controls for the finite C221 authority-binding checker."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest


CHECKER_PATH = Path(__file__).absolute().parents[1] / "check_bindings.py"
SPEC = importlib.util.spec_from_file_location("c221_checker", CHECKER_PATH)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class Controls(unittest.TestCase):
    package_root = None

    @classmethod
    def setUpClass(cls):
        cls.bindings, cls.part_map = checker.load_authority()
        cls.inputs = {path: (cls.package_root / path).read_bytes() for path in checker.INPUT_PATHS}
        cls.bundle = json.loads(cls.inputs[checker.INPUT_PATHS[1]])
        cls.semantic = json.loads(cls.inputs[checker.INPUT_PATHS[2]])
        cls.glb, cls.binary = checker.decode_glb(cls.inputs[checker.INPUT_PATHS[0]])
        cls.manifest, cls.sources = checker._source_manifest(cls.bundle)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-c221-controls-")
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def package_copy(self):
        root = self.root / "package"
        root.mkdir()
        for path in checker.INPUT_PATHS:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.inputs[path])
            target.chmod(0o644)
        return root

    def join(self, *, part_map=None, semantic=None, glb=None, binary=None, sources=None):
        return checker._check_parts(part_map or self.part_map, semantic or self.semantic,
                                    glb or self.glb, self.binary if binary is None else binary,
                                    sources or self.sources)

    def test_exact_admission_and_cli_api_equality(self):
        report = checker.check_package(self.package_root)
        self.assertEqual(report["result"], "PASS_CPU_AUTHORITY_BINDING")
        self.assertEqual(report["checked"], {
            "source_units": 2, "parts": 18, "source_span_occurrences": 52,
            "distinct_source_spans": 16, "instance_triangles": 7800,
            "instance_corners": 23400, "geometry_accessor_uses": 54,
        })
        result = subprocess.run([sys.executable, str(CHECKER_PATH), "--package-root", str(self.package_root)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), report)
        self.assertFalse(report["limits"]["target_execution_authorized"])
        self.assertFalse(report["limits"]["numeric_geometry_material_pose_validation"])

    def test_same_length_changed_input_refused(self):
        root = self.package_copy()
        path = root / checker.INPUT_PATHS[0]
        raw = bytearray(path.read_bytes())
        raw[-1] ^= 1
        path.write_bytes(raw)
        with self.assertRaisesRegex(checker.CheckError, "SHA-256"):
            checker.check_package(root)

    def test_missing_and_truncated_input_refused(self):
        for operation in ("missing", "truncated"):
            with self.subTest(operation=operation):
                root = self.package_copy()
                path = root / checker.INPUT_PATHS[1]
                if operation == "missing":
                    path.unlink()
                else:
                    path.write_bytes(path.read_bytes()[:-1])
                with self.assertRaises(checker.CheckError):
                    checker.check_package(root)
                shutil.rmtree(root)

    def test_mode_change_refused(self):
        root = self.package_copy()
        (root / checker.INPUT_PATHS[1]).chmod(0o755)
        with self.assertRaisesRegex(checker.CheckError, "mode differs"):
            checker.check_package(root)

    def test_symlink_leaf_and_ancestor_refused(self):
        for kind in ("leaf", "ancestor"):
            with self.subTest(kind=kind):
                root = self.package_copy()
                original = root / checker.INPUT_PATHS[0]
                if kind == "leaf":
                    outside = self.root / "exact-glb"
                    original.rename(outside)
                    original.symlink_to(outside)
                else:
                    original = original.parent
                    outside = self.root / "exact-inputs"
                    original.rename(outside)
                    original.symlink_to(outside, target_is_directory=True)
                with self.assertRaises(checker.CheckError):
                    checker.check_package(root)
                shutil.rmtree(root)

    def test_root_symlink_and_traversal_refused(self):
        linked = self.root / "linked-root"
        linked.symlink_to(self.package_root, target_is_directory=True)
        with self.assertRaises(checker.CheckError):
            checker.check_package(linked)
        with self.assertRaises(checker.CheckError):
            checker.check_package(str(self.package_root) + "/../c220")

    def test_relative_path_attacks_refused(self):
        with checker.SafeRoot(self.root) as root:
            for path in ("../outside", "/absolute", "a//b", "a/./b", "a/../b", "a\\b", "a\x00b"):
                with self.subTest(path=repr(path)), self.assertRaises(checker.CheckError):
                    root.read(path, 1, "0" * 64, 0o644)

    def test_fifo_refused_without_hanging(self):
        root = self.package_copy()
        target = root / checker.INPUT_PATHS[0]
        target.unlink()
        os.mkfifo(target, 0o644)
        result = subprocess.run([sys.executable, str(CHECKER_PATH), "--package-root", str(root)],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "FILE")

    def test_forged_authority_documents_refused(self):
        for name in checker.AUTHORITY_PINS:
            with self.subTest(name=name):
                repository = self.root / name
                target = repository / "tools/second_target_c221/check_bindings.py"
                target.parent.mkdir(parents=True)
                shutil.copy2(CHECKER_PATH, target)
                authority = repository / checker.AUTHORITY_DIRECTORY
                authority.mkdir(parents=True)
                source = CHECKER_PATH.parents[2] / checker.AUTHORITY_DIRECTORY
                for original in checker.AUTHORITY_PINS:
                    shutil.copy2(source / original, authority / original)
                changed = authority / name
                raw = bytearray(changed.read_bytes())
                raw[-2] ^= 1
                changed.write_bytes(raw)
                result = subprocess.run([sys.executable, str(target), "--package-root", str(self.package_root)],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["error"]["code"], "HASH")

    def test_json_rejects_duplicates_nonfinite_invalid_utf8_and_truncation(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'"\xff"', b'{"a":'):
            with self.subTest(raw=raw), self.assertRaises(checker.CheckError):
                checker.strict_json(raw, "control")

    def test_program_revision_reconstructed_from_source_bytes(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["entry"]["source"] = bundle["entry"]["source"].replace("0.75[m]", "0.76[m]")
        with self.assertRaisesRegex(checker.CheckError, "program revision"):
            checker._source_manifest(bundle)

    def test_missing_part_refused(self):
        mapping = copy.deepcopy(self.part_map)
        mapping["entries"].pop()
        with self.assertRaises(checker.CheckError):
            self.join(part_map=mapping)

    def test_duplicate_identity_and_node_refused(self):
        for field in ("elementId", "sourcePath", "glbNode"):
            with self.subTest(field=field):
                mapping = copy.deepcopy(self.part_map)
                mapping["entries"][1][field] = mapping["entries"][0][field]
                with self.assertRaises(checker.CheckError):
                    self.join(part_map=mapping)

    def test_swapped_part_identities_refused(self):
        semantic = copy.deepcopy(self.semantic)
        semantic["objects"][0]["element_id"], semantic["objects"][1]["element_id"] = (
            semantic["objects"][1]["element_id"], semantic["objects"][0]["element_id"])
        with self.assertRaises(checker.CheckError):
            self.join(semantic=semantic)

    def test_changed_span_or_keyed_occurrence_refused(self):
        for kind in ("span", "key", "revision"):
            with self.subTest(kind=kind):
                mapping = copy.deepcopy(self.part_map)
                provenance = mapping["entries"][1]["sourceProvenance"]
                if kind == "span":
                    provenance["declaration"]["start_byte"] += 1
                elif kind == "key":
                    provenance["generated"]["key"] = "unrelated"
                else:
                    provenance["declaration"]["source_revision"] = "sha256:" + "0" * 64
                with self.assertRaises(checker.CheckError):
                    self.join(part_map=mapping)

    def test_span_bounds_and_utf8_boundaries_refused(self):
        source = {"unit": {"raw": "aéz".encode(), "source_revision": "sha256:test", "filename": "test.ok"}}
        for start, end in ((0, 9), (1, 1), (2, 3), (True, 3)):
            with self.subTest(start=start, end=end), self.assertRaises(checker.CheckError):
                checker._check_spans({"source_id": "unit", "source_revision": "sha256:test",
                                      "filename": "test.ok", "start_byte": start, "end_byte": end}, source, set())

    def test_descriptive_names_do_not_select_identity(self):
        mapping, semantic, glb = [copy.deepcopy(value) for value in (self.part_map, self.semantic, self.glb)]
        for entry in mapping["entries"]:
            entry["godotNativeNode"] = "same arbitrary display name"
            entry["blenderComparisonObject"] = "same arbitrary display name"
        for obj in semantic["objects"]:
            obj["name"] = "same arbitrary display name"
        for node in glb["nodes"]:
            node["name"] = "same arbitrary display name"
        self.assertEqual(self.join(part_map=mapping, semantic=semantic, glb=glb)["parts"], 18)

    def test_glb_header_and_chunks_refused(self):
        original = self.inputs[checker.INPUT_PATHS[0]]
        variants = [original[:8], original[:-1], b"bad!" + original[4:]]
        raw = bytearray(original)
        struct.pack_into("<I", raw, 12, len(raw))
        variants.append(bytes(raw))
        raw = bytearray(original)
        struct.pack_into("<I", raw, 16, 0x004E4942)
        variants.append(bytes(raw))
        for raw in variants:
            with self.subTest(length=len(raw)), self.assertRaises(checker.CheckError):
                checker.decode_glb(raw)

    def test_accessor_bounds_types_and_byte_hash_refused(self):
        for kind in ("extent", "bool-index", "swapped", "bytes"):
            with self.subTest(kind=kind):
                glb = copy.deepcopy(self.glb)
                binary = self.binary
                if kind == "extent":
                    glb["accessors"][1]["count"] = 1000000
                elif kind == "bool-index":
                    glb["meshes"][0]["primitives"][0]["attributes"]["POSITION"] = True
                elif kind == "swapped":
                    glb["meshes"][0]["primitives"][0]["attributes"]["POSITION"] = 2
                else:
                    raw = bytearray(binary)
                    raw[484] ^= 1
                    binary = bytes(raw)
                with self.assertRaises(checker.CheckError):
                    self.join(glb=glb, binary=binary)

    def test_structural_seam_rejects_wrong_inventory_and_nonacceptance(self):
        inputs = dict(self.inputs)
        inputs.pop(checker.INPUT_PATHS[-1])
        with self.assertRaises(checker.CheckError):
            checker.validate_structure(self.bindings, self.part_map, inputs)
        result = checker.validate_structure(self.bindings, self.part_map, self.inputs)
        self.assertEqual(result["source_units"], 2)
        self.assertNotIn("result", result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    Controls.package_root = args.package_root
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"schema": "ontokin.c221.author-controls/0.1", "tests": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors),
              "skipped": len(result.skipped), "passed": result.wasSuccessful(),
              "target_starts": 0, "source_evaluations": 0,
              "scope": "Public file admission and explicitly private structural negative controls",
              "python": sys.version, "platform": sys.platform}
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
