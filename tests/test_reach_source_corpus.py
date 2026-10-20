"""Actual source checks against the unchanged adopted P/N/L reach corpus.

Each sample is a separate request: load exact source, compile, then replay to
one exact side with the SAME compiler work context. Expectations are read from
the frozen corpus, never calculated by the production solver or sampler.
This development cohort is not the complete reach release audit.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
from datetime import datetime, timezone
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import struct
import time
import unittest

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import evaluate_prefix
from ontokin.reach_runtime import ReachSimulator


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/language-design/planar-reach-v0.1"
SUPPLEMENT = DATA / "draft2-supplements"
MAP_PATH = ROOT / "docs/engineering/reach-source-acceptance-validation/source-case-map.json"
ORIGINAL = json.loads((DATA / "acceptance.json").read_text())
LIFECYCLE = json.loads((SUPPLEMENT / "acceptance.json").read_text())
PROFILE = json.loads((DATA / "profile-draft2.json").read_text())
CASE_MAP = json.loads(MAP_PATH.read_text())
CASES = {case["id"]: (DATA, case) for case in ORIGINAL["source_cases"]}
CASES.update({case["id"]: (SUPPLEMENT, case) for case in LIFECYCLE["source_cases"]})
MAPPING = {row["case_id"]: row for row in CASE_MAP["cases"]}
DIAGNOSTICS = {row["reach_code"]: row for row in PROFILE["diagnostics"]}
POSITION_TOLERANCE = PROFILE["numerical_meaning"]["source_position_residual_max_m"]
ANGLE_TOLERANCE = PROFILE["numerical_meaning"]["derived_pose_reference_angle_tolerance_rad"]
EXECUTION_RECORDS = []


def _sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _time(row):
    return Q(int(row["time"]["numerator"]), int(row["time"]["denominator"]))


def _inverse_point(frame, position):
    """Independent re-expression of observed world bytes, not an expectation."""
    w, x, y, z = frame["orientation_wxyz"]
    x, y, z = -x, -y, -z
    px, py, pz = [a - b for a, b in zip(position, frame["position_m"])]
    tx, ty, tz = 2 * (y * pz - z * py), 2 * (z * px - x * pz), 2 * (x * py - y * px)
    return [math.fsum((px, w * tx, y * tz, -z * ty)),
            math.fsum((py, w * ty, z * tx, -x * tz)),
            math.fsum((pz, w * tz, x * ty, -y * tx))]


class ReachSourceCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name, wanted in CASE_MAP["frozen_input_hashes"].items():
            if _sha((ROOT / name).read_bytes()) != wanted:
                raise AssertionError("Mapped frozen input changed: " + name)
        expected = {f"P{i:02}" for i in range(1, 27)} | {f"N{i:02}" for i in range(1, 16)} | {f"L{i:02}" for i in range(1, 5)}
        if set(CASES) != expected or set(MAPPING) != expected or len(CASE_MAP["cases"]) != 45:
            raise AssertionError("The literal mapping must contain all 45 frozen source cases exactly once.")
        actual = set(unittest.defaultTestLoader.getTestCaseNames(cls))
        wanted = {row["test_method"] for row in CASE_MAP["cases"]}
        if actual != wanted or len(wanted) != 45:
            raise AssertionError("The literal mapping and actual named source-case methods differ.")
        for case_id, (directory, source) in CASES.items():
            row = MAPPING[case_id]
            frozen_fields = {
                "fixture": str((directory / "acceptance.json").relative_to(ROOT)),
                "file_manifest": str((directory / source["file_manifest"]).relative_to(ROOT)),
                "program_revision": source["program_revision"],
                "source_revision": source["source_sha256"],
                "sample_side_count": len(source.get("expected", source).get("samples", [])),
            }
            for field, value in frozen_fields.items():
                if row.get(field) != value:
                    raise AssertionError(f"Mapped {case_id}.{field} differs from its frozen case entry.")
        if sum(len(c["expected"].get("samples", [])) for c in ORIGINAL["source_cases"]) != 308:
            raise AssertionError("The original sample-side inventory changed.")
        if sum(len(c["samples"]) for c in LIFECYCLE["source_cases"]) != 51:
            raise AssertionError("The lifecycle sample-side inventory changed.")

    def setUp(self):
        self.case_id = next(row["case_id"] for row in CASE_MAP["cases"] if row["test_method"] == self._testMethodName)
        self.record = {"case_id": self.case_id, "test_id": self.id(), "requests": [], "derivative_measurements": []}

    def tearDown(self):
        EXECUTION_RECORDS.append(self.record)

    def _bundle(self, case):
        directory, source = CASES[case]
        manifest = directory / source["file_manifest"]
        self.assertEqual(_sha(manifest.read_bytes()), source["file_manifest_sha256"])
        bundle = load_file_manifest(manifest)
        self.assertEqual(bundle.program_revision, source["program_revision"])
        self.assertEqual(bundle.entry.raw, (directory / source["entry_source"]).read_bytes())
        self.assertEqual(bundle.entry.revision, source["source_sha256"])
        units = (source["source_manifest"]["units"] if case.startswith("L") else source["source_units"])
        self.assertEqual(bundle.manifest()["units"], units)
        for unit in bundle.units:
            self.assertEqual(unit.revision, _sha(unit.raw))
        return bundle

    @contextmanager
    def _request(self, case, purpose):
        bundle = self._bundle(case)
        before = tuple((unit.source_id, unit.raw, unit.revision) for unit in bundle.units)
        row = {"purpose": purpose, "program_revision": bundle.program_revision,
               "started_utc": datetime.now(timezone.utc).isoformat(), "status": "started"}
        self.record["requests"].append(row)
        started = time.monotonic()
        compiler = None
        try:
            compiler = compile_construction(bundle)
            self.assertEqual(compiler.model.program_revision, bundle.program_revision)
            self.assertEqual(compiler.model.profile, "planar-reach-0.1")
            self.assertIsNotNone(compiler.reach_work)
            yield compiler, row
            row["status"] = "passed"
        except BaseException as error:
            row["status"] = "failed"
            row["exception_type"] = type(error).__name__
            row["exception"] = str(error)
            if isinstance(error, OntoKinError):
                row["diagnostic"] = {"code": error.code, "phase": error.diagnostic.phase,
                                     "category": error.diagnostic.category,
                                     "details": error.diagnostic.details}
            raise
        finally:
            row["elapsed_seconds"] = time.monotonic() - started
            if compiler is not None:
                row["construction_operations"] = compiler.budget.operations
                row["reach_operations"] = compiler.reach_work.operations
                row["reach_counters"] = dict(compiler.reach_work.counts)
            self.assertEqual(tuple((unit.source_id, unit.raw, unit.revision) for unit in bundle.units), before)

    def _simulator(self, compiler):
        simulator = ReachSimulator(compiler.model, work=compiler.reach_work)
        self.assertIs(simulator.work, compiler.reach_work)
        return simulator

    def _bits(self, actual, expected, trail):
        if expected is None:
            self.assertIsNone(actual, trail)
            return
        if isinstance(expected, list):
            self.assertIsInstance(actual, (list, tuple), trail)
            self.assertEqual(len(actual), len(expected), trail)
            for index, (a, e) in enumerate(zip(actual, expected)):
                self._bits(a, e, trail + f"[{index}]")
            return
        self.assertIsInstance(actual, (float, int), trail)
        self.assertFalse(isinstance(actual, bool), trail)
        self.assertTrue(math.isfinite(actual), trail)
        self.assertEqual(struct.pack(">d", actual), struct.pack(">d", expected),
                         f"{trail}: actual={actual!r}, expected={expected!r}")

    def _position(self, actual, expected, trail):
        self.assertEqual(len(actual), len(expected), trail)
        self.assertTrue(all(math.isfinite(v) for v in actual), trail)
        self.assertLessEqual(math.dist(actual, expected), POSITION_TOLERANCE, trail)

    def _orientation(self, actual, expected, trail):
        self.assertEqual(len(actual), 4, trail)
        self.assertTrue(all(math.isfinite(v) for v in actual), trail)
        self.assertLessEqual(abs(math.hypot(*actual) - 1), ANGLE_TOLERANCE, trail)
        # atan2 of quaternion chord lengths avoids acos cancellation near zero.
        # A sign change represents the same rotation; targets/coordinates still
        # require their separately specified canonical bits.
        a_norm, e_norm = math.hypot(*actual), math.hypot(*expected)
        a = [v / a_norm for v in actual]
        e = [v / e_norm for v in expected]
        minus, plus = math.dist(a, e), math.hypot(*(x + y for x, y in zip(a, e)))
        angle = 4 * math.atan2(min(minus, plus), max(minus, plus))
        self.assertLessEqual(angle, ANGLE_TOLERANCE, f"{trail}: angular error {angle!r} rad")

    def _residual(self, actual, expected, trail):
        if expected is None:
            self.assertIsNone(actual, trail)
        else:
            self.assertTrue(math.isfinite(actual), trail)
            self.assertGreaterEqual(actual, 0, trail)
            self.assertLessEqual(abs(actual - expected), POSITION_TOLERANCE, trail)

    def _derivative(self, actual, expected, trail):
        self.assertEqual(len(actual), len(expected), trail)
        self.assertTrue(all(math.isfinite(v) for v in actual), trail)
        self.record["derivative_measurements"].append({
            "field": trail, "actual": list(actual), "frozen_expected": list(expected),
            "absolute_component_errors": [abs(a - e) for a, e in zip(actual, expected)],
            "exact_binary64_equal": all(struct.pack(">d", a) == struct.pack(">d", e) for a, e in zip(actual, expected)),
            "acceptance_tolerance": None, "acceptance_status": "pending_explicit_derived_rate_tolerance",
        })

    def _sets(self, compiler, snapshot, expected):
        wanted_objects = expected["expected_object_paths"]
        wanted_visible = expected["expected_visible_paths"]
        self.assertEqual(sorted(compiler.model.objects), sorted(wanted_objects))
        self.assertEqual(sorted(snapshot["objects"]), sorted(wanted_objects))
        visible = sorted(path for path, obj in snapshot["objects"].items() if obj["geometry"]["kind"] != "empty")
        self.assertEqual(visible, sorted(wanted_visible))
        self.assertEqual(sorted(snapshot["actions"]), MAPPING[self.case_id]["all_action_paths"])
        reaches = (list(expected["samples"][0]["reaches"]) if self.case_id.startswith("L")
                   else expected["reach_action_paths"])
        self.assertEqual(sorted(snapshot["reaches"]), sorted(reaches))
        ids = [tuple(row["element_id"]) for row in snapshot["objects"].values()]
        self.assertEqual(len(ids), len(set(ids)))
        for path in wanted_visible:
            self.assertNotEqual(snapshot["objects"][path]["geometry"]["kind"], "empty")

    def _physical(self, compiler, snapshot, arm, expected, trail):
        forearm = snapshot["objects"][arm + ".forearm"]
        tip = snapshot["frames"][arm + ".forearm.tip.frame"]
        base = snapshot["frames"][arm + ".pivot.frame"]
        reach = next(row for row in snapshot["reaches"].values() if row["chain"]["shoulder"]["path"] == arm + ".shoulder")
        value = reach["current"]["value"]
        for key, actual in {
            "elbow_position_base_m": _inverse_point(base, forearm["position_m"]),
            "elbow_position_world_m": forearm["position_m"],
            "tip_position_base_m": value["tip_pose_base"]["position_m"],
            "tip_position_world_m": tip["position_m"],
        }.items():
            self._position(actual, expected[key], trail + "." + key)
        self._position(value["tip_pose_world"]["position_m"], expected["tip_position_world_m"], trail + ".projected_tip_world")
        self._orientation(forearm["orientation_wxyz"], expected["forearm_orientation_wxyz"], trail + ".forearm_orientation_wxyz")
        self._derivative(tip["velocity_m_per_s"], expected["tip_velocity_world_m_per_s"], trail + ".tip_velocity_world_m_per_s")
        self._derivative(forearm["angular_velocity_rad_per_s"], expected["forearm_omega_world_rad_per_s"], trail + ".forearm_omega_world_rad_per_s")

    def _original_sample(self, compiler, snapshot, expected, sample):
        trail = f"{self.case_id}@{snapshot['time_seconds']}/{snapshot['side']}"
        self._sets(compiler, snapshot, expected)
        value = snapshot["reaches"]["reach"]["current"]["value"]
        self.assertEqual(value["lifecycle"], sample["action_state"], trail)
        self.assertEqual(value["goal_outcome"], sample["goal_outcome"], trail)
        self.assertEqual(snapshot["actions"]["reach"]["status"], sample["action_state"], trail)
        self._bits(value["joint_coordinates_rad"], sample["joint_coordinates_rad"], trail + ".joint_coordinates_rad")
        self._bits(value["joint_rates_rad_per_s"], sample["joint_rates_rad_per_s"], trail + ".joint_rates_rad_per_s")
        resolved = expected["independent_solution"]["resolved_joint_targets_rad"] if sample["resolved_targets_visible"] else None
        self._bits(value["resolved_joint_targets_rad"], resolved, trail + ".resolved_joint_targets_rad")
        arm = expected["tracked_arm"]
        wanted_claims = [list(compiler.model.joints[arm + "." + coordinate].element_id) for coordinate in sample["claimed_coordinates"]]
        self.assertEqual(value["claimed_joint_ids"], wanted_claims, trail)
        for index, name in enumerate(("shoulder", "elbow")):
            joint = snapshot["joints"][arm + "." + name]
            self._bits(joint["coordinate"], sample["joint_coordinates_rad"][index], trail + "." + name)
            self._bits(joint["coordinate_rate"], sample["joint_rates_rad_per_s"][index], trail + "." + name + "_rate")
        self._residual(value["current_residual_m"], sample["current_goal_residual_m"], trail + ".current_residual_m")
        terminal = value["terminal_result"]
        if terminal is not None and terminal["outcome"] == "satisfied":
            self.assertLessEqual(terminal["position_residual_m"], POSITION_TOLERANCE, trail)
        self._physical(compiler, snapshot, arm, sample, trail)

    def _projection(self, actual, expected, trail=""):
        if trail.rsplit(".", 1)[-1] in {
            "joint_coordinates_rad", "resolved_joint_targets_rad", "start_coordinates_rad",
            "joint_rates_rad_per_s", "action_joint_rates_rad_per_s", "coordinates_m",
        }:
            self._bits(actual, expected, trail)
        elif isinstance(expected, dict):
            self.assertEqual(set(actual), set(expected), trail)
            for key, value in expected.items():
                self._projection(actual[key], value, trail + "." + key)
        elif isinstance(expected, list):
            if trail.endswith("orientation_wxyz"):
                self._orientation(actual, expected, trail)
            elif trail.endswith(("position_m", "current_world_target_m")):
                self._position(actual, expected, trail)
            else:
                self.assertEqual(len(actual), len(expected), trail)
                for index, value in enumerate(expected):
                    self._projection(actual[index], value, trail + f"[{index}]")
        elif isinstance(expected, float):
            if trail.endswith(("current_residual_m", "position_residual_m")):
                self._residual(actual, expected, trail)
            else:
                self._bits(actual, expected, trail)
        else:
            self.assertEqual(actual, expected, trail)

    def _error(self, error, code):
        expected = DIAGNOSTICS[code]
        self.assertEqual(error.code, expected["envelope_code"])
        self.assertEqual(error.diagnostic.details.get("reach_code"), code)
        self.assertEqual(error.diagnostic.category, expected["category"])
        self.assertIn(error.diagnostic.phase, expected["envelope_phases"])

    def _rollback(self, simulator, time, code):
        before = simulator.advance(time, "before")
        retained, index, boundaries = copy.deepcopy(simulator.state), simulator.event_index, list(simulator.boundaries)
        with self.assertRaises(OntoKinError) as caught:
            simulator.advance(time, "after")
        self._error(caught.exception, code)
        self.assertEqual(simulator.state, retained)
        self.assertEqual(simulator.event_index, index)
        self.assertEqual(simulator.boundaries, boundaries)
        self.assertEqual(simulator.snapshot(time, "before"), before)
        return before

    def _negative(self, case):
        expected = CASES[case][1]["expected"]
        if expected["failure_phase"] == "construction_or_typed_action_construction":
            bundle = self._bundle(case)
            with self.assertRaises(OntoKinError) as caught:
                compile_construction(bundle)
            self._error(caught.exception, expected["reach_code"])
            self.record["construction_failure"] = {"phase": caught.exception.diagnostic.phase,
                "code": caught.exception.code, "reach_code": expected["reach_code"]}
            self.assertEqual(bundle.program_revision, CASES[case][1]["program_revision"])
            return
        self.assertEqual(expected["failure_phase"], "admission")
        with self._request(case, "admission rejection and whole-boundary rollback") as (compiler, row):
            simulator = self._simulator(compiler)
            before = self._rollback(simulator, Q(0), expected["reach_code"])
            self._sets(compiler, before, expected)
            self.assertEqual(simulator.state.claims, {})
            self.assertTrue(all(action.status == "pending" for action in simulator.state.actions.values()))

    def _positive(self, case):
        expected = CASES[case][1]["expected"]
        peaks = []
        for index, sample in enumerate(expected["samples"]):
            with self.subTest(case=case, sample=index, time=str(_time(sample)), side=sample["side"]):
                with self._request(case, f"sample {index}: {_time(sample)}/{sample['side']}") as (compiler, row):
                    snapshot = self._simulator(compiler).advance(_time(sample), sample["side"])
                    self.assertEqual(Q(snapshot["time_seconds"]), _time(sample))
                    self.assertEqual(snapshot["side"], sample["side"])
                    self._original_sample(compiler, snapshot, expected, sample)
                    peaks.append(sum(v["current"]["value"]["lifecycle"] in {"running", "paused"} for v in snapshot["reaches"].values()))
        self.assertEqual(max(peaks, default=-1), expected["peak_active_reaches"])
        if case == "P11":
            self._character(expected)
        if case == "P16":
            self._release(expected)
        if case == "P17":
            self._failed_prefix(case, expected["full_horizon_failure"]["reach_code"], Q(3), Q(2), Q(4))

    def _character(self, expected):
        with self._request("P11", "independent right arm and head at t=2") as (compiler, row):
            snapshot = self._simulator(compiler).advance(Q(2), "after")
            current = snapshot["reaches"]["other_arm"]["current"]["value"]
            wanted = expected["other_goals"]["right_arm"]
            self._bits(current["resolved_joint_targets_rad"], wanted["resolved_joint_targets_rad"], "P11.other_arm.targets")
            self._bits(current["joint_coordinates_rad"], wanted["resolved_joint_targets_rad"], "P11.other_arm.coordinates")
            self.assertEqual(current["goal_outcome"], "satisfied")
            self.assertLessEqual(current["current_residual_m"], POSITION_TOLERANCE)
            self._position(current["tip_pose_base"]["position_m"], wanted["tip_position_base_m"], "P11.other_arm.tip")
            look_joint = compiler.model.actions["look"].target
            self._bits(snapshot["joints"][look_joint]["coordinate"], expected["other_goals"]["head_yaw_at_2_seconds_rad"], "P11.head_yaw")

    def _release(self, expected):
        release = expected["release"]
        with self._request("P16", "incoming release and atomic completion at t=2") as (compiler, row):
            simulator = self._simulator(compiler)
            before = simulator.advance(Q(2), "before")
            self._original_sample(compiler, before, expected, release["incoming_state"])
            after = simulator.advance(Q(2), "after")
            records = simulator.incoming_releases_at(Q(2))
            self.assertEqual(len(records), 1)
            incoming = records[0]
            self.assertEqual(incoming["target"]["path"], "payload")
            self.assertEqual(incoming["program_revision"], CASES["P16"][1]["program_revision"])
            self.assertEqual(incoming["time_seconds"], "2")
            self.assertEqual(len(incoming["reach_contributors"]), 1)
            contribution = incoming["reach_contributors"][0]
            self._bits(contribution["joint_rates_rad_per_s"], release["incoming_state"]["joint_rates_rad_per_s"], "P16.incoming_joint_rates")
            self.assertTrue(all(contribution["joint_rates_rad_per_s"]))
            self._bits(incoming["incoming_linear_velocity_world_m_per_s"], before["objects"]["payload"]["velocity_m_per_s"], "P16.saved_velocity_identity")
            self._bits(incoming["incoming_angular_velocity_world_rad_per_s"], before["objects"]["payload"]["angular_velocity_rad_per_s"], "P16.saved_omega_identity")
            self._bits(after["objects"]["payload"]["velocity_m_per_s"], incoming["incoming_linear_velocity_world_m_per_s"], "P16.outgoing_velocity_identity")
            self._bits(after["objects"]["payload"]["angular_velocity_rad_per_s"], incoming["incoming_angular_velocity_world_rad_per_s"], "P16.outgoing_omega_identity")
            self._orientation(after["objects"]["payload"]["orientation_wxyz"], release["orientation_at_release_wxyz"], "P16.release_orientation")
            self._bits(after["reaches"]["reach"]["current"]["value"]["joint_rates_rad_per_s"], [0.0, 0.0], "P16.completed_rates")
            self.assertEqual(after["objects"]["payload"]["motion"], "dynamic")
            self._bits(after["objects"]["payload"]["own_mass_kg"], release["own_mass_kg"], "P16.own_mass")
            self._bits(after["objects"]["payload"]["forces"]["net_force_world_n"], release["world_force_n"], "P16.world_force")
        for endpoint in (3, 4):
            with self.subTest(release_time=endpoint):
                with self._request("P16", f"independent freed payload at t={endpoint}") as (compiler, row):
                    payload = self._simulator(compiler).advance(Q(endpoint), "after")["objects"]["payload"]
                    self._position(payload["position_m"], release[f"position_at_{endpoint}_seconds_m"], f"P16.payload@{endpoint}.position")
                    self._derivative(payload["velocity_m_per_s"], release[f"velocity_at_{endpoint}_seconds_m_per_s"], f"P16.payload@{endpoint}.velocity")
                    self._derivative(payload["angular_velocity_rad_per_s"], release["constant_free_omega_world_rad_per_s"], f"P16.payload@{endpoint}.omega")
                    self.assertEqual(payload["pose_authority"]["kind"], "free_sphere")
                    self.assertEqual(payload["forces"]["started_count"], 1)
                    self.assertEqual(payload["forces"]["completed_count"], 1)
                    self.assertEqual(payload["forces"]["last_change_time_seconds"], "3")
                    self._bits(payload["forces"]["net_force_world_n"], [0.0, 0.0, 0.0], "P16.completed_force")

    def _failed_prefix(self, case, code, failure_time, short_time, full_time):
        with self._request(case, "short requested prefix") as (compiler, row):
            result = evaluate_prefix(compiler.model, short_time, work=compiler.reach_work)
            self.assertIsNone(result["failure"])
            self.assertEqual(Q(result["valid_until_seconds"]), short_time)
            self.assertEqual(result["valid_until_side"], "after")
        with self._request(case, "full request retains exact valid incoming prefix") as (compiler, row):
            result = evaluate_prefix(compiler.model, full_time, work=compiler.reach_work)
            self.assertIsNotNone(result["failure"])
            self._error(result["failure"], code)
            self.assertEqual(Q(result["valid_until_seconds"]), failure_time)
            self.assertEqual(result["valid_until_side"], "before")
        with self._request(case, "failed handoff does not publish partial after-state") as (compiler, row):
            simulator = self._simulator(compiler)
            before = self._rollback(simulator, failure_time, code)
            if case == "L04":
                expected = CASES[case][1]["failure"]
                current = before["reaches"][expected["unchanged_prior_action"]]["current"]["value"]
                self.assertEqual(current["claimed_joint_ids"], expected["retained_claims"])
                self.assertEqual(set(simulator.state.claims.values()), {expected["unchanged_prior_action"]})
                self.assertEqual(simulator.state.actions[expected["pending_failed_action"]].status, "pending")
                self.assertEqual(simulator.incoming_releases_at(failure_time), [])

    def _lifecycle(self, case):
        expected = CASES[case][1]
        states = 0
        for index, sample in enumerate(expected["samples"]):
            with self.subTest(case=case, sample=index, time=sample["time_seconds"], side=sample["side"]):
                with self._request(case, f"sample {index}: {sample['time_seconds']}/{sample['side']}") as (compiler, row):
                    snapshot = self._simulator(compiler).advance(_time(sample), sample["side"])
                    self.assertEqual(Q(snapshot["time_seconds"]), _time(sample))
                    self.assertEqual(snapshot["side"], sample["side"])
                    self._sets(compiler, snapshot, expected)
                    self._projection(snapshot["reaches"], sample["reaches"], f"{case}@{sample['time_seconds']}/{sample['side']}")
                    # Frozen projections describe the current physical pair,
                    # even for pending/stopped actions while another action
                    # owns it. Check the independent joint-state output too.
                    for action_path, wanted_record in sample["reaches"].items():
                        wanted_current = wanted_record["current"]["value"]
                        for coordinate_index, name in enumerate(("shoulder", "elbow")):
                            wanted_joint = wanted_record["chain"][name]
                            joint = snapshot["joints"][wanted_joint["path"]]
                            trail = f"{case}@{sample['time_seconds']}/{sample['side']}.{action_path}.{name}"
                            self.assertEqual(joint["element_id"], wanted_joint["element_id"], trail)
                            self._bits(joint["coordinate"], wanted_current["joint_coordinates_rad"][coordinate_index], trail + ".coordinate")
                            self._bits(joint["coordinate_rate"], wanted_current["joint_rates_rad_per_s"][coordinate_index], trail + ".coordinate_rate")
                    self._physical(compiler, snapshot, "rig.arm", sample["physical"], f"{case}@{sample['time_seconds']}/{sample['side']}")
                    for reach in snapshot["reaches"].values():
                        terminal = reach["current"]["value"]["terminal_result"]
                        if terminal is not None and terminal["outcome"] == "satisfied":
                            self.assertLessEqual(terminal["position_residual_m"], POSITION_TOLERANCE)
                    states += len(snapshot["reaches"])
        self.assertEqual(states, expected["action_state_count"])
        if expected["failure"] is not None:
            failure = expected["failure"]
            self._failed_prefix(case, failure["reach_code"], Q(failure["time_seconds"]), Q(1, 4), Q(expected["scene_duration_seconds"]))

    def test_p01_bench_positive(self): self._positive("P01")
    def test_p02_bench_negative_branch(self): self._positive("P02")
    def test_p03_unequal_links(self): self._positive("P03")
    def test_p04_rotated_base(self): self._positive("P04")
    def test_p05_moving_base(self): self._positive("P05")
    def test_p06_outer_boundary(self): self._positive("P06")
    def test_p07_inner_boundary_positive(self): self._positive("P07")
    def test_p08_inner_boundary_negative(self): self._positive("P08")
    def test_p09_principal_shoulder_wrap(self): self._positive("P09")
    def test_p10_closed_elbow_limit(self): self._positive("P10")
    def test_p11_complete_segmented_character(self): self._positive("P11")
    def test_p12_keyed_one(self): self._positive("P12")
    def test_p13_keyed_five(self): self._positive("P13")
    def test_p14_pause_resume(self): self._positive("P14")
    def test_p15_stop_before_goal(self): self._positive("P15")
    def test_p16_incoming_release_and_force(self): self._positive("P16")
    def test_p17_valid_prefix_before_failed_goal(self): self._positive("P17")
    def test_p18_held_out_oblique(self): self._positive("P18")
    def test_p19_held_out_unequal(self): self._positive("P19")
    def test_p20_scoped_length_repair(self): self._positive("P20")
    def test_p21_minimum_link_lengths(self): self._positive("P21")
    def test_p22_maximum_link_and_target_lengths(self): self._positive("P22")
    def test_p23_maximum_chain_count(self): self._positive("P23")
    def test_p24_maximum_named_action_count(self): self._positive("P24")
    def test_p25_minimum_duration(self): self._positive("P25")
    def test_p26_maximum_duration(self): self._positive("P26")
    def test_n01_outside_outer_boundary(self): self._negative("N01")
    def test_n02_inside_inner_boundary(self): self._negative("N02")
    def test_n03_singular_origin(self): self._negative("N03")
    def test_n04_out_of_plane(self): self._negative("N04")
    def test_n05_different_target_frame(self): self._negative("N05")
    def test_n06_selected_branch_limit(self): self._negative("N06")
    def test_n07_length_one_over(self): self._negative("N07")
    def test_n08_branch_string_is_not_enum(self): self._negative("N08")
    def test_n09_partial_claim_conflict(self): self._negative("N09")
    def test_n10_wrong_end_site(self): self._negative("N10")
    def test_n11_chain_count_one_over(self): self._negative("N11")
    def test_n12_duration_below_minimum(self): self._negative("N12")
    def test_n13_named_action_count_one_over(self): self._negative("N13")
    def test_n14_duration_above_maximum(self): self._negative("N14")
    def test_n15_nonparallel_elbow_axis(self): self._negative("N15")
    def test_l01_both_moving_pause_resume(self): self._lifecycle("L01")
    def test_l02_stop_then_new_owner(self): self._lifecycle("L02")
    def test_l03_complete_then_new_owner(self): self._lifecycle("L03")
    def test_l04_failed_handoff_rollback(self): self._lifecycle("L04")


if __name__ == "__main__":
    unittest.main()
