"""Pure source/evidence checks; no Agent store or hosted service is opened."""
from __future__ import annotations

import contextlib
import copy
from fractions import Fraction
import io
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ontokin import force_conformance as force
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate
from tools.build_force_demo import fixture_bundle
from tools.force_oracles import oracle_for, sample_requests


class ForceReleaseContractTests(unittest.TestCase):
    def test_preserves_published_baseline_additive_cohort_and_all_twelve_roles(self):
        mapping = force.load_manifest()
        self.assertEqual(mapping["regression_baseline_commit"], "f901b1ac3b09fcb20842285f12d407dc919f9632")
        self.assertEqual(len(mapping["regression_required_test_ids"]), 753)
        self.assertEqual(mapping["additional_branch_cohort"]["commit"], "f05684d42c9ab8112efa2b137f5274fd70bd6754")
        self.assertEqual(len(mapping["additional_branch_cohort"]["test_ids"]), 5)
        self.assertEqual(mapping["python_matrix"], ["3.11", "3.12", "3.13"])
        self.assertEqual({name for case in mapping["cases"] for name in case["source_case_ids"]}, set(force.SOURCE_IDS))
        generic_delivery_guard = "test_force_agent.ForceAgentTests.test_planned_delivery_rejects_without_artifact_or_accepted_candidate"
        self.assertIn(generic_delivery_guard, mapping["regression_required_test_ids"])
        agent_gate = next(case for case in mapping["cases"] if case["id"] == "F09")
        self.assertIn(generic_delivery_guard, agent_gate["required_tests"])
        with patch("sqlite3.connect", side_effect=AssertionError("Discovery must not open an Agent store")):
            discovered = set(force.surface.discover_test_ids())
        required = {name for case in mapping["cases"] for name in case["required_tests"]}
        self.assertEqual(required - discovered, set(), "Every mapped literal must resolve to a current executable test")

    def test_additional_destination_cohort_cannot_disappear_from_discovery(self):
        auditor = force.Auditor.__new__(force.Auditor)
        auditor.mapping = force.load_manifest()
        auditor.role = lambda name: {version: {} for version in force.PYTHONS}
        with patch.object(force.surface, "discover_test_ids", return_value=auditor.mapping["regression_required_test_ids"]):
            with self.assertRaisesRegex(force.EvidenceError, "destination oracle regression"):
                auditor.compatibility()

    def test_inventory_covers_executed_scripts_grammar_pins_and_nested_tests(self):
        for name in ("tools/force-agent-verification-requirements.txt", "tools/evidence/check.py",
                     "tests/validation/test_nested.py", "docs/language-design/force-v0.1/syntax.ebnf",
                     "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py",
                     "docs/maintenance/reorganization-2026-10-17/source-map.json",
                     "docs/product/OK-PRD-001-product-requirements.md"):
            self.assertTrue(force.eligible_path(name), name)
        for name in ("GOAL.md", "STATUS.md", "docs/engineering/new-release-evidence/audit.json",
                     "tools/node_modules/example/index.js", "ontokin/__pycache__/module.py"):
            self.assertFalse(force.eligible_path(name), name)
        self.assertEqual(len(force.verification_pins()), 6)
        self.assertEqual(force.verification_pins()["typing-extensions"], "4.16.0")

    def test_empty_audit_stays_pending_and_cannot_claim_goal(self):
        result = force.audit_release()
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["summary"]["pending"], 12)
        self.assertFalse(result["summary"]["full_force_release_complete"])
        self.assertFalse(result["full_product_conformance_certified"])
        self.assertFalse(result["executed_external_tools"])


class ForceEvidenceInputTests(unittest.TestCase):
    def test_strict_json_rejects_duplicate_members_constants_and_overflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.json"
            for raw in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', '{"x":-1e999}'):
                path.write_text(raw)
                with self.assertRaises(force.EvidenceError):
                    force.json_file(path)
            path.write_text('{"x":1e-200}')
            self.assertEqual(force.json_file(path), {"x": 1e-200})

    def test_retained_paths_are_confined_and_hash_and_length_are_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "real.json"
            path.write_text("{}\n")
            record = force.file_record(path, root)
            self.assertEqual(force.identified(record, root), path)
            for name in ("../real.json", "/real.json", "a//real.json", "./real.json", "a\\real.json"):
                with self.assertRaises(force.EvidenceError):
                    force.relative_file(root, name)
            (root / "link.json").symlink_to(path)
            with self.assertRaises(force.EvidenceError):
                force.relative_file(root, "link.json")
            for changed in ({**record, "byte_length": 2}, {**record, "sha256": "sha256:" + "0" * 64}):
                with self.assertRaises(force.EvidenceError):
                    force.identified(changed, root)

    def test_external_argv_binds_the_captured_checkout_and_exact_role(self):
        cwd = "/retained/original-checkout"
        force.check_external_command("force-agent", ["python", cwd + "/tools/verify_force_agent_workflow.py",
                                                      "--workflow-dir", "/retained/workflow"], cwd=cwd)
        for argv in (["python", "/different/tools/verify_force_agent_workflow.py"],
                     ["python", "tools/verify_force_agent_workflow.py", "--help"],
                     ["sh", "wrapper.sh", "tools/verify_force_agent_workflow.py"]):
            with self.assertRaises(force.EvidenceError):
                force.check_external_command("force-agent", argv, cwd=cwd)
        with self.assertRaises(force.EvidenceError):
            force.check_external_command("agent-native", ["node", "tools/verify_force_native.mjs"], cwd=cwd)

    def test_new_output_modes_preserve_existing_identified_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "inventory.json"
            output.write_bytes(b"prior identified bytes\n")
            for mode in ("inventory", "template", "audit"):
                with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(force.main([mode, "--output", str(output)]), 1)
            self.assertEqual(output.read_bytes(), b"prior identified bytes\n")
            existing = Path(temporary) / "execution"
            existing.mkdir()
            with self.assertRaises(force.EvidenceError):
                force.execute_role("source", existing)

    def test_sealing_rejects_mutable_stores_before_writing_a_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root / "template.json"
            force.write_json(template, {"schema_version": force.EVIDENCE_SCHEMA, "roles": {}})
            (root / "agent.sqlite-wal").write_bytes(b"mutable")
            with self.assertRaisesRegex(force.EvidenceError, "mutable stores"):
                force.seal_evidence(template, root, root / "evidence.json")
            self.assertFalse((root / "evidence.json").exists())

    def test_literal_execution_inventory_rejects_skips_duplicates_and_nonfinite_duration(self):
        names = ["test_example.Example.test_one", "test_example.Example.test_two"]
        execution = {"unique_required": 2, "tests_run": 2, "loader_errors": [], "fixture_errors": [],
                     "unexpected_test_records": [], "outcomes": {"passed": 2},
                     "tests": [{"test_id": name, "status": "passed", "failures": [], "elapsed_seconds": .001} for name in names]}
        report = {"executed": True, "expected_test_ids": names, "test_execution": execution,
                  "summary": {"all_passed": True}}
        self.assertEqual(force.check_tests(report, names)["tests"], 2)
        for kind in ("skip", "duplicate", "nonfinite", "fixture"):
            changed = copy.deepcopy(report)
            if kind == "skip": changed["test_execution"]["tests"][0]["status"] = "skipped"
            if kind == "duplicate": changed["test_execution"]["tests"][1]["test_id"] = names[0]
            if kind == "nonfinite": changed["test_execution"]["tests"][0]["elapsed_seconds"] = math.inf
            if kind == "fixture": changed["test_execution"]["fixture_errors"] = ["failed setup"]
            with self.assertRaises(force.EvidenceError):
                force.check_tests(changed, names)

    def test_visual_outputs_cannot_contradict_their_passed_wrapper(self):
        report = {"schema_version": "ontokin.external-validation/0.1", "files": [{
            "validator": {"version": force.NODE_PINS["gltf-validator"], "errors": 0, "warnings": 0},
            "three_js": {"revision": "180", "loaded": True, "comparison": {
                "status": "passed", "failures": [], "sample_count": 7, "object_pose_comparisons": 14}}}]}
        force.check_visual_output("visual-format", report)
        for category in ("validator", "comparison", "browser", "failed-request"):
            changed = copy.deepcopy(report)
            if category == "validator": changed["files"][0]["validator"]["errors"] = 1
            if category == "comparison": changed["files"][0]["three_js"]["comparison"]["status"] = "failed"
            if category == "browser": changed = {"status": "passed", "page_errors": ["actual page error"]}
            if category == "failed-request": changed = {"status": "passed", "failed_requests": ["missing GLB asset"]}
            with self.assertRaises(force.EvidenceError):
                force.check_visual_output("visual-browser" if category in {"browser", "failed-request"} else "visual-format", changed)
        force.check_visual_output("surface", {"status": "pending", "summary": {"failed": 0, "pending": 3}})

    def test_visual_inventory_accepts_actual_driver_path_order_without_changing_named_bytes(self):
        from tools.check_local import inventory
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixtures = root / "docs/language-design/fixture"
            fixtures.mkdir(parents=True)
            (fixtures / "example.ok").write_text('ontokin "0.1";\n')
            (fixtures.with_suffix(".json")).write_text('{"frozen":true}\n')
            driver = inventory(root)
            current = force.evidence_inventory(root)
            self.assertNotEqual([row["path"] for row in driver["files"]],
                                [row["path"] for row in current])
            original = copy.deepcopy(driver)
            force.check_visual_source_inventory(driver["files"], current)
            force.check_visual_source_inventory(list(reversed(driver["files"])), current)
            self.assertEqual(driver, original)

    def test_visual_inventory_rejects_changed_missing_duplicate_or_renamed_inputs(self):
        records = [{"path": "ontokin/example.py", "sha256": "sha256:" + "a" * 64, "bytes": 17},
                   {"path": "tests/test_example.py", "sha256": "sha256:" + "b" * 64, "bytes": 23}]
        current = [{"path": row["path"], "sha256": row["sha256"], "byte_length": row["bytes"]}
                   for row in records]
        force.check_visual_source_inventory(records, current)
        for kind in ("hash", "length", "missing", "duplicate", "renamed", "extra"):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(records)
                if kind == "hash": changed[0]["sha256"] = "sha256:" + "c" * 64
                if kind == "length": changed[0]["bytes"] += 1
                if kind == "missing": changed.pop()
                if kind == "duplicate": changed.append(copy.deepcopy(changed[0]))
                if kind == "renamed": changed[0]["path"] = "ontokin/renamed.py"
                if kind == "extra": changed.append({**changed[0], "path": "ontokin/extra.py"})
                with self.assertRaisesRegex(force.EvidenceError, "omitted or changed"):
                    force.check_visual_source_inventory(changed, current)


class ForceGitInputTests(unittest.TestCase):
    def test_commit_blob_binding_ignores_ambient_git_and_replacement_refs_without_index_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            def command(*args):
                result = subprocess.run(["git", *args], cwd=root, env=force.git_environment(),
                                        capture_output=True, check=True)
                return result.stdout.decode().strip()
            command("init", "--quiet", "--template=")
            command("config", "user.name", "OntoKin evidence test")
            command("config", "user.email", "evidence-test@example.invalid")
            (root / "ontokin").mkdir()
            (root / "ontokin/probe.py").write_text("VALUE = 1\n")
            command("add", "ontokin/probe.py")
            command("commit", "--quiet", "-m", "Identified source")
            commit, tree = command("rev-parse", "HEAD"), command("rev-parse", "HEAD^{tree}")
            inputs = force.evidence_inventory(root)
            (root / "ontokin/probe.py").write_text("VALUE = 2\n")
            command("add", "ontokin/probe.py")
            command("commit", "--quiet", "-m", "Different source")
            alternate = command("rev-parse", "HEAD")
            command("replace", commit, alternate)
            (root / "ontokin/probe.py").write_text("VALUE = 1\n")
            index_before = (root / ".git/index").read_bytes()
            with patch.dict(os.environ, {"GIT_DIR": "/not/a/repository", "GIT_INDEX_FILE": "/not/an/index",
                                         "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.fsmonitor", "GIT_CONFIG_VALUE_0": "bad"}):
                result = force.verify_commit_inputs(commit, tree, inputs, root)
            self.assertEqual(result["commit"], commit)
            self.assertEqual((root / ".git/index").read_bytes(), index_before)
            with self.assertRaises(force.EvidenceError):
                force.verify_commit_inputs(alternate, tree, inputs, root)
            (root / "ontokin/untracked.py").write_text("VALUE = 3\n")
            with self.assertRaisesRegex(force.EvidenceError, "omits or adds"):
                force.verify_commit_inputs(commit, tree, force.evidence_inventory(root), root)


def layout(keys=2, carriers=1):
    """A declared empty-carrier GLB layout, never represented as execution evidence."""
    counts = [(keys, "SCALAR", 4), (keys, "VEC3", 12), (keys, "VEC4", 16)]
    views, accessors, offset = [], [], 0
    for count, kind, width in counts:
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": count * width})
        accessors.append({"bufferView": len(views) - 1, "count": count, "type": kind, "componentType": 5126})
        offset += count * width
    nodes = [{"extras": {"ontokin": {"path": "empty" + str(i)}}} for i in range(carriers)]
    samplers = [{"input": 0, "output": output, "interpolation": "LINEAR"} for _ in nodes for output in (1, 2)]
    channels = [{"sampler": 2 * i + j, "target": {"node": i, "path": prop}}
                for i in range(carriers) for j, prop in enumerate(("translation", "rotation"))]
    document = {"buffers": [{"byteLength": offset}], "bufferViews": views, "accessors": accessors,
                "nodes": nodes, "scene": 0, "scenes": [{"nodes": list(range(carriers))}],
                "animations": [{"samplers": samplers, "channels": channels}]}
    return document, bytes(offset), {"empty" + str(i): {"path": "empty" + str(i)} for i in range(carriers)}


class ForceNativeAllocationTests(unittest.TestCase):
    def test_declared_keys_and_aggregate_poses_are_bounded_before_any_decode(self):
        document, binary, objects = layout()
        self.assertEqual(force.preflight_native_layout(document, binary, objects)["declared_components"], 16)
        for keys, carriers in ((10001, 1), (10000, 26)):
            document, binary, objects = layout(keys, carriers)
            with patch.object(force.surface, "_accessor", side_effect=AssertionError("decoded too early")) as decode:
                with self.assertRaisesRegex(force.EvidenceError, "allocation budget"):
                    force.preflight_native_layout(document, binary, objects)
                decode.assert_not_called()

    def test_aliasing_accessor_declarations_count_toward_total_allocation(self):
        document, binary, objects = layout()
        document["buffers"][0]["byteLength"] = 4_000_000
        document["bufferViews"].append({"buffer": 0, "byteOffset": 0, "byteLength": 4_000_000})
        document["accessors"] += [{"bufferView": 3, "count": 250000, "type": "VEC4", "componentType": 5126} for _ in range(5)]
        with self.assertRaisesRegex(force.EvidenceError, "aggregate decoded allocation"):
            force.preflight_native_layout(document, bytes(4_000_000), objects)

    def test_scene_matrix_and_nonfinite_json_cannot_bypass_recorded_transforms(self):
        for change in ("scene", "matrix", "nonfinite"):
            document, binary, objects = layout()
            if change == "scene": document["scenes"][0]["nodes"] = []
            if change == "matrix": document["nodes"][0]["matrix"] = [1, 0, 0, 0] * 4
            if change == "nonfinite": document["extra"] = {"overflow": math.inf}
            with self.assertRaises(force.EvidenceError):
                force.preflight_native_layout(document, binary, objects)

    def test_slerp_normalizes_binary32_endpoints_without_changing_rotation(self):
        left = [0., 0., 0., 1. + 2 ** -24]
        right = [0., 0., math.sin(.4) * (1 - 2 ** -24), math.cos(.4) * (1 - 2 ** -24)]
        for fraction in (0., .25, .5, 1.):
            actual = force.slerp_xyzw(left, right, fraction)
            force.orientation([actual[3], *actual[:3]], [math.cos(.4 * fraction), 0., 0., math.sin(.4 * fraction)])


class ForceNativeSourceOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {}
        keys = ("element_id", "position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s",
                "own_mass_kg", "pose_authority", "forces", "impulses")
        for name in ("P07", "P09", "P19", "held-out-oblique", "held-out-spin", "held-out-prefix"):
            bundle, oracle = fixture_bundle(name), oracle_for(name)
            model = compile_construction(bundle).model
            requests = [{"time": Fraction(row["time_seconds"]), "side": row["side"]} for row in sample_requests(name)]
            snapshots = evaluate(model, requests)["samples"]
            observations = [{**sample, "objects": {target: {key: obj[key] for key in keys}
                for target, obj in sample["objects"].items()}} for sample in snapshots]
            cls.cases[name] = (force.NativeSourceOracle(name, bundle, oracle),
                              {shape["path"]: shape for shape in oracle["shapes"] + oracle["empty_objects"]}, observations)

    def test_actual_source_states_match_independent_heldout_and_boundary_projections(self):
        for name, (oracle, shapes, observations) in self.cases.items():
            for sample in observations:
                for target, obj in sample["objects"].items():
                    with self.subTest(case=name, time=sample["time_seconds"], side=sample["side"], target=target):
                        oracle.check(target, shapes[target], obj, Fraction(sample["time_seconds"]), sample["side"])

    def test_self_consistent_erased_heldout_history_cannot_pass(self):
        for case, field in (("held-out-oblique", "forces"), ("held-out-spin", "impulses"),
                            ("held-out-prefix", "pose_authority")):
            oracle, shapes, observations = self.cases[case]
            sample = observations[-1]
            obj = copy.deepcopy(sample["objects"]["ball"])
            obj[field] = {}
            with self.assertRaises((force.EvidenceError, KeyError, ValueError)):
                oracle.check("ball", shapes["ball"], obj, Fraction(sample["time_seconds"]), sample["side"])

    def test_rehashed_mass_velocity_and_impulse_source_spans_are_independent(self):
        oracle, shapes, observations = self.cases["held-out-spin"]
        sample = observations[-1]
        for field in ("mass", "velocity", "span"):
            obj = copy.deepcopy(sample["objects"]["ball"])
            if field == "mass": obj["own_mass_kg"] += 1
            if field == "velocity": obj["velocity_m_per_s"][0] += .25
            if field == "span": obj["impulses"]["last_applications"][0]["source_location"]["end_byte"] -= 1
            with self.assertRaises((force.EvidenceError, ValueError)):
                oracle.check("ball", shapes["ball"], obj, Fraction(sample["time_seconds"]), sample["side"])

    def test_raw_source_filenames_bind_individual_units_not_a_byte_multiset(self):
        bundle = fixture_bundle("P01")
        with tempfile.TemporaryDirectory() as temporary:
            paths = {}
            for index, unit in enumerate(bundle.units):
                path = Path(temporary) / unit.filename
                path.write_bytes(unit.raw)
                paths["source_" + str(index)] = path
            force.check_raw_source_units(bundle, paths)
            left, right = paths["source_1"], paths["source_2"]
            first, second = left.read_bytes(), right.read_bytes()
            left.write_bytes(second)
            right.write_bytes(first)
            with self.assertRaisesRegex(force.EvidenceError, "filename or role"):
                force.check_raw_source_units(bundle, paths)


class ForceSourceExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = force.execute_sources()

    def test_all_fifty_six_actual_source_cases_are_serializable_and_independently_reaudited(self):
        self.assertEqual(self.report["summary"], {"total": 56, "passed": 56, "failed": 0, "all_passed": True})
        serialized = json.loads(json.dumps(self.report, allow_nan=False))
        self.assertEqual(force.check_source_report(serialized)["source_cases"], 56)

    def test_rehashed_source_poses_interval_history_and_atomic_prefix_cannot_change(self):
        for case, change in (("P01", "position"), ("P01", "history"), ("S05", "prefix")):
            changed = copy.deepcopy(self.report)
            row = next(item for item in changed["cases"] if item["id"] == case)
            if change == "position": row["observations"][-1]["objects"]["ball"]["position_m"][0] += 1
            if change == "history": row["observations"][-1]["objects"]["ball"]["forces"]["completed_count"] += 1
            if change == "prefix": row["last_valid_state"]["time_seconds"] = "3"
            with self.assertRaises((force.EvidenceError, ValueError)):
                force.check_source_report(changed)

    def test_errata_apply_only_when_original_values_match(self):
        original = force.json_file
        def changed(path):
            value = original(path)
            if Path(path).name == "source-errata.json":
                value["sample_corrections"][0]["old"]["velocity_m_s"] = [999, 0, 0]
            return value
        with patch.object(force, "json_file", side_effect=changed):
            with self.assertRaisesRegex(force.EvidenceError, "old-value precondition"):
                force.SourceCorpus()

    def test_exact_source_clocks_keep_binary64_addition_and_subnormal_duration(self):
        exact_sum = Fraction.from_float(.1) + Fraction.from_float(.2)
        self.assertEqual(Fraction(force.clock(exact_sum)), exact_sum)
        self.assertNotEqual(force.clock(exact_sum), force.clock(Fraction.from_float(.3)))
        smallest = Fraction.from_float(math.nextafter(0., 1.))
        self.assertEqual(Fraction(force.clock(smallest)), smallest)
        failure = next(row for row in self.report["cases"] if row["id"] == "S05")
        self.assertEqual(failure["valid_until"], {"time_seconds": "0", "side": "after"})
        self.assertTrue(failure["observations"])


if __name__ == "__main__":
    unittest.main()
