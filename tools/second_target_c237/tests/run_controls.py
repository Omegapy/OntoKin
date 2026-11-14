#!/usr/bin/env python3
"""Finite C237 author controls against retained inputs; no native/source starts."""
from __future__ import annotations

import argparse
import ast
import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
CHECKER = Path(__file__).absolute().parents[1] / "check_semantics.py"
SPEC = importlib.util.spec_from_file_location("c237_author_checker", CHECKER)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
PACKAGE_ROOT = None
EVIDENCE = None
RECORDS = []
SAVED = set()
INPUT = "agent-results/namespace-repair/run-01/inputs/"
FILE_KINDS = {"program_bundle": "after.program.bundle.json", "glb": "after.glb",
              "semantic_sidecar": "after.semantic.json", "source_normal_payload": "source-payload.json"}


def fixture(package_root):
    inputs = Path(package_root) / INPUT
    semantic = json.loads((inputs / "after.semantic.json").read_bytes())
    parts = [{"sourceNode": row["geometry_binding"]["node"], "sourceMesh": row["geometry_binding"]["mesh"],
              "elementId": row["element_id"], "definitionId": row["definition_id"],
              "sourcePath": row["path"], "destinationLabel": "synthetic-" + row["path"]} for row in semantic["objects"]]
    features = []
    for row in semantic["features"]:
        name = row["feature"]
        if name == "source_closure":
            provenance, capability = "retained_external", "retained_source"
        elif name in ("action_execution", "live_physics", "source_reconstruction"):
            provenance, capability = "unsupported", "unsupported"
        elif name in ("primitive_geometry", "numeric_precision"):
            provenance, capability = "observer_copied", "approximated_representation"
        elif name == "world_motion":
            provenance, capability = "observer_copied", "baked_playback"
        else:
            provenance, capability = "observer_copied", "descriptive_metadata"
        features.append({**row, "provenance": provenance, "capability": capability})
    return {"schema": "ontokin.second-target.c237.observations/0.1",
            "producer": {"kind": "synthetic", "name": "C237 author source-byte fixture"},
            "programRevision": semantic["binding"]["accepted_program_revision"],
            "parts": parts, "semantics": semantic, "features": features,
            "retainedFiles": [{"kind": kind, "base64": base64.b64encode((inputs / name).read_bytes()).decode("ascii")} for kind, name in FILE_KINDS.items()],
            "capabilities": {"liveFollowing": False, "liveHinges": False, "actionExecution": False,
                             "livePhysics": False, "sourceReconstruction": False, "rigidBodyCount": 0,
                             "controllerCount": 0, "representedBodyMassKg": 0.0,
                             "motionAuthority": "OntoKin reference evaluator; destination receives baked playback only"}}


def record(label, report):
    categories = sorted({r["category"] for r in report.get("losses", [])})
    error = report.get("error", {}).get("code")
    RECORDS.append({"case": label, "result": report["result"], "resultClass": report["resultClass"],
                    "passed": report["passed"], "errorCode": error, "lossCategories": categories,
                    "observation": report.get("observation"), "counts": report.get("counts"),
                    "nativeAttestation": report["limits"]["native_attestation"]})
    category = report["resultClass"] + "-" + (error or "+".join(categories) or "complete")
    if EVIDENCE is not None and category not in SAVED:
        SAVED.add(category)
        (EVIDENCE / (category + ".json")).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")


class SemanticControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="ontokin-c237-author-")
        cls.root = Path(cls.directory.name)
        cls.path = cls.root / "observations.json"
        cls.original = fixture(PACKAGE_ROOT)
        cls.path.write_text(json.dumps(cls.original))
        cls.passing = checker.check_semantics(PACKAGE_ROOT, cls.path)
        record("baseline", cls.passing)
        if EVIDENCE is not None:
            (EVIDENCE / "synthetic-observations.json").write_bytes(cls.path.read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def setUp(self):
        self.value = copy.deepcopy(self.original)

    def run_value(self, label=""):
        self.path.write_text(json.dumps(self.value))
        result = checker.check_semantics(PACKAGE_ROOT, self.path)
        record(self._testMethodName + ":" + label, result)
        return result

    def refused(self, code=None, label=""):
        result = self.run_value(label)
        self.assertEqual(result["resultClass"], "structural_refusal", result.get("error"))
        self.assertIs(result["passed"], False)
        if code:
            self.assertEqual(result["error"]["code"], code)
        return result

    def lost(self, category, label=""):
        result = self.run_value(label)
        self.assertEqual(result["resultClass"], "measured_loss", result.get("error"))
        self.assertIs(result["passed"], False)
        self.assertIn(category, [r["category"] for r in result["losses"]])
        return result

    def retained(self, kind):
        return next(r for r in self.value["retainedFiles"] if r["kind"] == kind)

    def feature(self, name):
        return next(r for r in self.value["features"] if r["feature"] == name)

    def package_copy(self, name):
        root = self.root / name
        root.mkdir()
        for path in checker.authority.INPUT_PATHS:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(PACKAGE_ROOT) / path, target)
            target.chmod(0o644)
        return root

    def test_complete_inventory_and_original_semantics(self):
        result = self.passing
        self.assertTrue(result["passed"], result.get("error"))
        self.assertEqual(result["result"], "PASS_CPU_SEMANTIC_RETENTION")
        self.assertEqual(result["authority"]["result"], "PASS_CPU_AUTHORITY_BINDING")
        self.assertEqual(result["counts"], {"parts": 18, "features": 14, "retainedFiles": 4, "sourceUnits": 2,
                                          "objects": 18, "sites": 34, "follows": 8, "joints": 8,
                                          "actions": 2, "events": 1, "collections": 2})
        self.assertEqual(result["semanticComparison"]["expected"], self.original["semantics"])
        self.assertEqual(result["semanticComparison"]["observed"], self.original["semantics"])
        self.assertEqual(result["requiredFeatures"], ["dimensions_units_frames", "stable_identities"])
        self.assertEqual(len(result["partComparisons"]), 18)
        self.assertEqual(len(result["featureComparisons"]), 14)
        self.assertEqual(result["losses"], [])

    def test_source_units_and_raw_retention_are_inspected(self):
        units = self.passing["sourceUnitInspection"]
        self.assertTrue(units["equal"])
        self.assertEqual([r["bytes"] for r in units["observed"]["units"]], [1708, 1911])
        self.assertEqual(units["observed"]["program_revision"], self.original["programRevision"])
        self.assertEqual(units["observed"]["units"][1]["package_id"], "example.hinges")
        self.assertEqual(units["observed"]["units"][1]["version"], "1.0.0")
        for row in self.passing["retentionComparisons"]:
            raw = (Path(PACKAGE_ROOT) / INPUT / FILE_KINDS[row["kind"]]).read_bytes()
            self.assertEqual(row["observed"], {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
            self.assertTrue(row["bytesEqual"])

    def test_full_feature_raw_rows_and_unsupported_limits(self):
        rows = {r["feature"]: r for r in self.passing["featureComparisons"]}
        for expected in self.original["features"]:
            row = rows[expected["feature"]]
            self.assertEqual(row["observed"], expected)
            self.assertFalse(row["provenanceAttested"])
            self.assertTrue(row["sourceTreatmentEqual"])
        for key in ("native_attestation", "destination_mapping_attestation", "source_execution", "native_execution", "aggregate_execution", "full_r07_acceptance"):
            self.assertIs(self.passing["limits"][key], False)
        self.assertEqual(self.passing["capabilities"]["observed"]["representedBodyMassKg"], 0.0)
        self.assertIn("Declaration-derived", self.passing["capabilities"]["representedMassBasis"])

    def test_keyed_order_and_duplicate_cosmetic_labels(self):
        for key in ("parts", "features", "retainedFiles"):
            self.value[key].reverse()
        for part in self.value["parts"]:
            part["destinationLabel"] = "same cosmetic label"
        self.assertTrue(self.run_value()["passed"])

    def test_consistent_destination_and_all_supported_origins_are_unattested(self):
        self.value["producer"]["kind"] = "declared_destination"
        for origin in ("imported_native", "independently_derived", "observer_copied", "retained_external"):
            with self.subTest(origin=origin):
                self.feature("stable_identities")["provenance"] = origin
                result = self.run_value(origin)
                self.assertTrue(result["passed"])
                self.assertFalse(result["limits"]["native_attestation"])
        self.assertEqual(self.feature("live_physics")["provenance"], "unsupported")

    def test_provenance_capability_contradictions(self):
        for name, key, value in (("ownership", "provenance", "imported_native"),
                                 ("following", "capability", "live_follow"),
                                 ("hinge_constraints", "capability", "live_joint"),
                                 ("action_execution", "provenance", "observer_copied"),
                                 ("source_closure", "provenance", "independently_derived"),
                                 ("materials", "provenance", "verified_by_assertion")):
            with self.subTest(feature=name, key=key):
                self.value = copy.deepcopy(self.original)
                self.feature(name)[key] = value
                self.refused("PROVENANCE", name + ":" + key)

    def test_all_original_feature_reasons_and_required_flags(self):
        for original in self.original["features"]:
            for key in ("reason", "required"):
                with self.subTest(feature=original["feature"], key=key):
                    self.value = copy.deepcopy(self.original)
                    row = self.feature(original["feature"])
                    row[key] = not row[key] if key == "required" else row[key] + " altered"
                    self.lost("source_feature_treatment", original["feature"] + ":" + key)

    def test_all_original_feature_treatments(self):
        for original in self.original["features"]:
            with self.subTest(feature=original["feature"]):
                self.value = copy.deepcopy(self.original)
                row = self.feature(original["feature"])
                row["treatment"] = "preserved" if row["treatment"] != "preserved" else "approximated"
                if original["treatment"] == "unsupported":
                    self.refused("CAPABILITY", original["feature"])
                else:
                    self.lost("source_feature_treatment", original["feature"])

    def test_missing_duplicate_extra_and_unknown_keyed_records(self):
        for key in ("parts", "features", "retainedFiles"):
            for operation in ("missing", "extra", "duplicate", "unknown"):
                with self.subTest(key=key, operation=operation):
                    self.value = copy.deepcopy(self.original)
                    rows = self.value[key]
                    if operation == "missing": rows.pop()
                    elif operation == "extra": rows.append(copy.deepcopy(rows[0]))
                    elif operation == "duplicate": rows[1] = copy.deepcopy(rows[0])
                    elif key == "parts": rows[0]["sourceNode"] = 999
                    elif key == "features": rows[0]["feature"] = "unknown"
                    else: rows[0]["kind"] = "unknown"
                    self.refused(label=key + ":" + operation)

    def test_swapped_and_stale_part_identity_cannot_be_repaired_by_labels(self):
        for key in ("sourceNode", "sourceMesh", "elementId", "definitionId", "sourcePath"):
            with self.subTest(key=key):
                self.value = copy.deepcopy(self.original)
                row = self.value["parts"][0]
                row[key] = 99 if key in ("sourceNode", "sourceMesh") else (["wrong"] if key.endswith("Id") else "wrong")
                row["destinationLabel"] = self.original["parts"][0]["destinationLabel"]
                self.refused("IDENTITY", key)
        self.value = copy.deepcopy(self.original)
        self.value["parts"][0]["elementId"], self.value["parts"][1]["elementId"] = self.value["parts"][1]["elementId"], self.value["parts"][0]["elementId"]
        self.refused("IDENTITY", "swapped")
        self.value = copy.deepcopy(self.original)
        self.value["programRevision"] = "sha256:" + "0" * 64
        self.refused("IDENTITY", "revision")

    def test_boolean_integer_and_float_identity_confusion(self):
        for key, value in (("sourceNode", False), ("sourceNode", 0.0), ("sourceMesh", False), ("sourceMesh", 0.0), ("elementId", [False])):
            with self.subTest(key=key, value=value):
                self.value = copy.deepcopy(self.original)
                self.value["parts"][0][key] = value
                self.refused("IDENTITY", key + ":" + repr(value))

    def test_boolean_and_integer_source_types_remain_distinct(self):
        changes = [(('objects', 0, 'geometry_binding', 'node'), False),
                   (('objects', 0, 'placement', 'authored'), 1),
                   (('scene', 'gravity_m_per_s2', 0), False),
                   (('scene', 'gravity_m_per_s2', 0), 0)]
        for path, value in changes:
            with self.subTest(path=path):
                self.value = copy.deepcopy(self.original)
                target = self.value["semantics"]
                for key in path[:-1]: target = target[key]
                target[path[-1]] = value
                self.refused("TYPE", repr(path))
        self.value = copy.deepcopy(self.original)
        self.feature("stable_identities")["required"] = 1
        self.refused("TYPE", "required-bool")

    def test_semantic_field_values_and_source_provenance_are_compared(self):
        changes = [(('objects', 0, 'geometry', 'size', 0), 0.2),
                   (('objects', 0, 'placement', 'position_m', 0), -0.75),
                   (('objects', 0, 'motion', 'initial_velocity_m_per_s', 0), 0.25),
                   (('objects', 0, 'provenance', 'declaration', 'start_byte'), 903),
                   (('objects', 0, 'collision'), 'enabled'),
                   (('objects', 0, 'physical', 'kind'), 'rigid_body'),
                   (('coordinates', 'up'), '+Z'),
                   (('scene', 'motion_authority'), 'invented live authority')]
        for path, value in changes:
            with self.subTest(path=path):
                self.value = copy.deepcopy(self.original)
                target = self.value["semantics"]
                for key in path[:-1]: target = target[key]
                target[path[-1]] = value
                result = self.lost("semantic_value", repr(path))
                self.assertTrue(result["semanticComparison"]["mismatches"])
                self.assertEqual(result["semanticComparison"]["observed"], self.value["semantics"])

    def test_owner_follow_joint_site_action_event_and_collection_changes(self):
        cases = [(('sites', 0, 'owner'), 'other.owner'),
                 (('sites', 0, 'pose', 'position_m', 0), -0.2),
                 (('follows', 0, 'parent_frame'), 'other.frame'),
                 (('follows', 0, 'offset', 'position_m', 1), -0.5),
                 (('joints', 0, 'child_site'), 'other.site'),
                 (('joints', 0, 'axis_in_parent_site', 2), -1.0),
                 (('joints', 0, 'limits_rad', 1), 0.5),
                 (('joints', 0, 'initial_rad'), 0.25),
                 (('actions', 0, 'target'), 'other.action'),
                 (('events', 0, 'events', 0, 'target'), 'other.event'),
                 (('collections', 'first.fingers', 'owner_path'), 'second')]
        owned = next(i for i, r in enumerate(self.original['semantics']['objects']) if isinstance(r['owner'], dict))
        cases.append((('objects', owned, 'owner', 'path'), 'invented.owner'))
        cases.append((('objects', owned, 'owner', 'element_id', 2), 'second'))
        for path, value in cases:
            with self.subTest(path=path):
                self.value = copy.deepcopy(self.original)
                target = self.value["semantics"]
                for key in path[:-1]: target = target[key]
                target[path[-1]] = value
                self.lost("semantic_value", repr(path))

    def test_missing_semantic_lists_unknown_fields_and_source_order(self):
        for key in ("objects", "sites", "follows", "joints", "actions", "events", "features"):
            with self.subTest(key=key):
                self.value = copy.deepcopy(self.original)
                self.value["semantics"][key].pop()
                self.refused("COUNT", key)
        self.value = copy.deepcopy(self.original)
        self.value["semantics"]["scene"]["invented_mass"] = 1.0
        self.refused("SHAPE", "extra-field")
        self.value = copy.deepcopy(self.original)
        self.value["semantics"]["collections"]["first.fingers"]["ordered_keys"].reverse()
        self.lost("semantic_value", "source-order")

    def test_signed_zero_is_representation_loss_only(self):
        self.value["semantics"]["scene"]["gravity_m_per_s2"][0] = -0.0
        result = self.lost("semantic_value")
        self.assertNotEqual(result["semanticComparison"]["expectedCanonicalSha256"], result["semanticComparison"]["observedCanonicalSha256"])
        self.assertFalse(result["limits"]["geometry_material_normal_pose_accuracy"])

    def test_live_capabilities_mass_and_motion_authority_are_refused(self):
        replacements = {"liveFollowing": True, "liveHinges": True, "actionExecution": True,
                        "livePhysics": True, "sourceReconstruction": True, "rigidBodyCount": 1,
                        "controllerCount": 1, "representedBodyMassKg": 1.0, "motionAuthority": "native live physics"}
        for key, value in replacements.items():
            with self.subTest(key=key):
                self.value = copy.deepcopy(self.original)
                self.value["capabilities"][key] = value
                self.refused("CAPABILITY", key)
        for key, value in (("representedBodyMassKg", 0), ("representedBodyMassKg", False), ("rigidBodyCount", False)):
            self.value = copy.deepcopy(self.original)
            self.value["capabilities"][key] = value
            self.refused("CAPABILITY", key + ":typed")

    def test_each_retained_file_same_length_corruption_is_measured(self):
        for kind in FILE_KINDS:
            with self.subTest(kind=kind):
                self.value = copy.deepcopy(self.original)
                row = self.retained(kind)
                raw = bytearray(base64.b64decode(row["base64"]))
                raw[-1] ^= 1
                row["base64"] = base64.b64encode(raw).decode("ascii")
                self.lost("retained_bytes", kind)

    def test_empty_retained_bytes_and_malformed_bundle_are_measured(self):
        for kind in FILE_KINDS:
            with self.subTest(kind=kind):
                self.value = copy.deepcopy(self.original)
                self.retained(kind)["base64"] = ""
                result = self.lost("retained_bytes", kind)
                self.assertEqual(next(r for r in result["retentionComparisons"] if r["kind"] == kind)["status"], "absent")
        for raw in (b'{', b'\xff', b'{"entry":{},"entry":{}}'):
            self.value = copy.deepcopy(self.original)
            self.retained("program_bundle")["base64"] = base64.b64encode(raw).decode("ascii")
            result = self.lost("retained_source_units", repr(raw))
            self.assertIsNotNone(result["sourceUnitInspection"]["error"])

    def test_embedded_source_dependency_and_version_changes_are_inspected(self):
        for field in ("entry_source", "dependency_source", "package_id", "version", "filename", "schema_version"):
            with self.subTest(field=field):
                self.value = copy.deepcopy(self.original)
                row = self.retained("program_bundle")
                bundle = json.loads(base64.b64decode(row["base64"]))
                if field == "entry_source": bundle["entry"]["source"] += "\n"
                elif field == "dependency_source": bundle["modules"][0]["source"] += "\n"
                elif field == "schema_version": bundle[field] = "ontokin.bundle/9.9"
                else: bundle["modules"][0][field] += "-changed"
                row["base64"] = base64.b64encode(json.dumps(bundle).encode()).decode("ascii")
                result = self.lost("retained_source_units", field)
                self.assertIsNotNone(result["sourceUnitInspection"]["observed"])

    def test_reserialized_json_fails_raw_retention_even_when_semantics_equal(self):
        for kind in ("program_bundle", "semantic_sidecar", "source_normal_payload"):
            with self.subTest(kind=kind):
                self.value = copy.deepcopy(self.original)
                row = self.retained(kind)
                decoded = json.loads(base64.b64decode(row["base64"]))
                row["base64"] = base64.b64encode(json.dumps(decoded, sort_keys=True, separators=(",", ":")).encode()).decode("ascii")
                result = self.lost("retained_bytes", kind)
                self.assertTrue(result["semanticComparison"]["equal"])
                if kind == "program_bundle": self.assertTrue(result["sourceUnitInspection"]["equal"])

    def test_stale_bundle_glb_pair_and_forged_hash_claim(self):
        bundle, glb = self.retained("program_bundle"), self.retained("glb")
        bundle["base64"], glb["base64"] = glb["base64"], bundle["base64"]
        self.lost("retained_bytes", "swapped-pair")
        self.value = copy.deepcopy(self.original)
        row = self.retained("glb")
        row["base64"] = ""
        row["sha256"] = hashlib.sha256((Path(PACKAGE_ROOT) / INPUT / "after.glb").read_bytes()).hexdigest()
        self.refused("SHAPE", "forged-hash")

    def test_malformed_and_noncanonical_base64_is_refused(self):
        for encoded in ("!", "Zg", "Zh==", "Zg==\n", "é", "===="):
            with self.subTest(encoded=encoded):
                self.value = copy.deepcopy(self.original)
                self.retained("glb")["base64"] = encoded
                self.refused("ENCODING", repr(encoded))

    def test_unknown_missing_and_forged_observation_fields(self):
        for key in self.original:
            with self.subTest(key=key):
                self.value = copy.deepcopy(self.original)
                del self.value[key]
                self.refused("SHAPE", key)
        self.value = copy.deepcopy(self.original)
        self.value["verified"] = True
        self.refused("SHAPE", "unknown-root")
        self.value = copy.deepcopy(self.passing)
        self.refused("SHAPE", "old-report")

    def test_invalid_json_duplicate_nonfinite_surrogate_and_encoding(self):
        for raw in (b'{', b'\xff', b'{"schema":1,"schema":2}', b'{"v":NaN}', b'{"v":Infinity}',
                    b'{"v":1e400}', b'{"v":"\\ud800"}', b'\xef\xbb\xbf{}'):
            with self.subTest(raw=raw):
                self.path.write_bytes(raw)
                report = checker.check_semantics(PACKAGE_ROOT, self.path)
                record(self._testMethodName + ":" + repr(raw), report)
                self.assertEqual(report["resultClass"], "structural_refusal")
                self.assertEqual(report["error"]["code"], "JSON")

    def test_depth_value_count_and_string_size_bounds(self):
        nested = 0
        for _ in range(70): nested = [nested]
        for label, value, code in (("deep", nested, "DEPTH"), ("values", [None] * 100001, "SIZE"),
                                   ("string", "a" * (1024 * 1024 + 1), "SIZE")):
            with self.subTest(label=label):
                self.value = copy.deepcopy(self.original)
                self.value["producer"]["name"] = value
                self.refused(code, label)

    def test_missing_empty_oversized_directory_fifo_and_symlink_files(self):
        self.path.write_text(json.dumps(self.value))
        for name in ("missing", "empty", "large", "directory", "fifo", "symlink"):
            with self.subTest(name=name):
                path = self.root / ("unsafe-" + name)
                if name == "empty": path.write_bytes(b"")
                elif name == "large": path.write_bytes(b" " * (4 * 1024 * 1024 + 1))
                elif name == "directory": path.mkdir()
                elif name == "fifo": os.mkfifo(path)
                elif name == "symlink": path.symlink_to(self.path)
                report = checker.check_semantics(PACKAGE_ROOT, path)
                record(self._testMethodName + ":" + name, report)
                self.assertEqual(report["resultClass"], "structural_refusal")
        link = self.root / "parent-link"
        link.symlink_to(self.root, target_is_directory=True)
        for path in (link / self.path.name, self.root / "sub" / ".." / self.path.name):
            report = checker.check_semantics(PACKAGE_ROOT, path)
            record(self._testMethodName + ":ancestor-or-traversal", report)
            self.assertEqual(report["resultClass"], "structural_refusal")

    def test_descriptor_change_and_path_replacement_are_refused(self):
        for action in ("mtime", "replace"):
            with self.subTest(action=action):
                self.path.write_text(json.dumps(self.value))
                target_inode = self.path.stat().st_ino
                real_read = os.read
                changed = False
                def read(fd, count):
                    nonlocal changed
                    raw = real_read(fd, count)
                    if not changed and os.fstat(fd).st_ino == target_inode:
                        changed = True
                        if action == "mtime":
                            before = self.path.stat()
                            os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
                        else:
                            replacement = self.root / "replacement.json"
                            replacement.write_bytes(self.path.read_bytes())
                            os.replace(replacement, self.path)
                    return raw
                with mock.patch.object(checker.os, "read", side_effect=read):
                    report = checker.check_semantics(PACKAGE_ROOT, self.path)
                record(self._testMethodName + ":" + action, report)
                self.assertTrue(changed)
                self.assertEqual(report["error"]["code"], "CHANGED")

    def test_fresh_admission_every_invocation_and_no_report_substitution(self):
        with mock.patch.object(checker.authority, "check_package", wraps=checker.authority.check_package) as admission:
            self.assertTrue(self.run_value("first")["passed"])
            self.assertTrue(self.run_value("second")["passed"])
            self.assertEqual(admission.call_count, 2)
        self.value = copy.deepcopy(self.passing)
        self.refused("SHAPE", "cached-pass-is-not-input")

    def test_original_package_corruption_and_postadmission_change_are_refused(self):
        self.path.write_text(json.dumps(self.value))
        root = self.package_copy("corrupt-package")
        path = root / INPUT / "after.glb"
        raw = bytearray(path.read_bytes()); raw[-1] ^= 1; path.write_bytes(raw)
        report = checker.check_semantics(root, self.path)
        record(self._testMethodName + ":corrupt-authority", report)
        self.assertEqual(report["error"]["code"], "HASH")
        root = self.package_copy("postadmission-package")
        real_admission = checker.authority.check_package
        def change(package):
            result = real_admission(package)
            path = root / INPUT / "after.semantic.json"
            raw = bytearray(path.read_bytes()); raw[-1] ^= 1; path.write_bytes(raw)
            return result
        with mock.patch.object(checker.authority, "check_package", side_effect=change):
            report = checker.check_semantics(root, self.path)
        record(self._testMethodName + ":post-admission-change", report)
        self.assertEqual(report["error"]["code"], "HASH")

    def test_original_input_bytes_are_not_written_and_runtime_is_not_imported(self):
        self.path.write_text(json.dumps(self.value))
        before = {p: hashlib.sha256((Path(PACKAGE_ROOT) / p).read_bytes()).hexdigest() for p in checker.authority.INPUT_PATHS}
        with mock.patch("subprocess.run", side_effect=AssertionError("No child process permitted by checker")), mock.patch("os.system", side_effect=AssertionError("No shell permitted")):
            report = checker.check_semantics(PACKAGE_ROOT, self.path)
        self.assertTrue(report["passed"], report.get("error"))
        after = {p: hashlib.sha256((Path(PACKAGE_ROOT) / p).read_bytes()).hexdigest() for p in before}
        self.assertEqual(before, after)
        tree = ast.parse(CHECKER.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom): imports.append(node.module or "")
        self.assertFalse(any(name.startswith("ontokin") or name in ("subprocess", "bpy") for name in imports))

    def test_raw_observation_hash_is_exact_not_canonical(self):
        raw = json.dumps(self.value, indent=1).encode("utf-8") + b"\n"
        self.path.write_bytes(raw)
        report = checker.check_semantics(PACKAGE_ROOT, self.path)
        record(self._testMethodName, report)
        self.assertTrue(report["passed"])
        self.assertEqual(report["observation"]["bytes"], len(raw))
        self.assertEqual(report["observation"]["sha256"], hashlib.sha256(raw).hexdigest())

    def test_cli_pass_loss_refusal_and_no_side_effects(self):
        command = [sys.executable, str(CHECKER), "--package-root", str(PACKAGE_ROOT), "--observations", str(self.path)]
        for expected, mutation in ((0, "none"), (1, "semantic"), (2, "schema")):
            with self.subTest(mutation=mutation):
                self.value = copy.deepcopy(self.original)
                if mutation == "semantic": self.value["semantics"]["coordinates"]["up"] = "+Z"
                elif mutation == "schema": self.value["unknown"] = 1
                self.path.write_text(json.dumps(self.value))
                before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(result.stderr, "")
                report = json.loads(result.stdout)
                record(self._testMethodName + ":" + mutation, report)
                after = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
                self.assertEqual(before, after)
        result = subprocess.run([sys.executable, str(CHECKER), "--unknown"], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "ARGUMENT")
        self.assertEqual(result.stderr, "")


def main(argv=None):
    global PACKAGE_ROOT, EVIDENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--evidence-directory")
    args = parser.parse_args(argv)
    PACKAGE_ROOT = Path(args.package_root).absolute()
    if args.evidence_directory:
        EVIDENCE = Path(args.evidence_directory).absolute()
        EVIDENCE.mkdir(parents=True, exist_ok=False)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SemanticControls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if EVIDENCE is not None:
        summary = {"schema": "ontokin.c237.author-controls/0.1", "methodsRun": result.testsRun,
                   "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
                   "successful": result.wasSuccessful(), "observedCalls": len(RECORDS), "cases": RECORDS,
                   "nativeStarts": 0, "sourceEvaluations": 0, "aggregateRuns": 0}
        (EVIDENCE / "controls.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
