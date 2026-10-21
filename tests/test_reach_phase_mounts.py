"""Exact phase recurrence reuse across independently translated rigid mounts."""
from dataclasses import replace
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.construction import compile_construction
from ontokin.reach_export import recording_phase_bounds
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_runtime import ReachSimulator
from test_reach_phase import source


def mounted_phases(count=32, *, extent=F(1, 4), anchor_rotation=F(0)):
    """A complete small source topology with distinct local translations."""
    work = ReachExecutionWork()
    children = tuple("mount_" + str(index) for index in range(1, count + 1))
    follows = {path: SimpleNamespace(child=path, parent="rig.frame",
        offset=SimpleNamespace(position=(F(0), extent * index, F(0)), rotation=(0., 0., 0., 1.)))
        for index, path in enumerate(children, 1)}
    model = SimpleNamespace(duration=F(1), objects=dict.fromkeys(("rig", *children)),
        events=(), actions={}, follows=follows, joints={}, sites={})
    state = SimpleNamespace(positions={"rig": (F(3), F(-2), F(0))},
        ideal_positions={"rig": (F(3), F(-2), F(0))}, root_rotation_errors={"rig": anchor_rotation},
        actions={}, claims={}, forces={}, modes={"rig": "prescribed"})
    return SimpleNamespace(model=model, state=state, work=work, pose_ops=SimpleNamespace(),
        _incoming=lambda state: {path: ("follow", path) for path in children})


def mount_key(key):
    return len(key) > 2 and key[0] == reach_phase._CACHE_DOMAIN and key[2] == "composition_translation_recurrence"


class PlanningSimulator(ReachSimulator):
    """Use the same complete source validation as the recording prefix."""
    def _check_object_pose(self, pose):
        self.pose_ops.ensure_finite(pose)

    def snapshot(self, time, side):
        self._kinematics(time, self.state)
        return {}


class ReachPhaseMountTests(unittest.TestCase):
    def test_distinct_mounts_keep_every_exact_bound_and_share_the_full_recurrence(self):
        for rotation in (F(0), F(1, 1 << 45)):
            with self.subTest(anchor_rotation=rotation):
                current = mounted_phases(anchor_rotation=rotation)
                previous = mounted_phases(anchor_rotation=rotation)
                actual = reach_phase.phase_bounds(current, F(0), F(1))
                with patch.object(reach_phase, "_local_translation_independent", return_value=False):
                    expected = reach_phase.phase_bounds(previous, F(0), F(1))
                self.assertEqual(actual, expected)
                self.assertEqual(len(actual["objects"]), 33)
                self.assertGreater(previous.work.operations - current.work.operations, 1000)
                self.assertLess(current.work.counts["phase_path_counts"], previous.work.counts["phase_path_counts"])
                self.assertEqual(current.work.operations, sum(current.work.counts.values()))
                self.assertLessEqual(len(current.work._cache), current.work.max_cache_entries)

    def test_actual_source_carriers_match_the_previous_recurrence_including_32_arms(self):
        for case, start, end in (("P23", F(0), F(2)), ("P01", F(0), F(2)),
                                 ("L01", F(0), F(1, 2)), ("L02", F(1, 2), F(3, 2)),
                                 ("P16", F(2), F(3))):
            with self.subTest(case=case):
                outputs, costs = [], []
                for reuse in (True, False):
                    built = compile_construction(source(case))
                    simulator = PlanningSimulator(built.model, work=built.reach_work)
                    simulator.advance(start, "after")
                    before = built.budget.operations
                    if reuse:
                        result = recording_phase_bounds(simulator, start, end)
                    else:
                        with patch.object(reach_phase, "_local_translation_independent", return_value=False):
                            result = recording_phase_bounds(simulator, start, end)
                    outputs.append(result)
                    costs.append(built.budget.operations - before)
                    self.assertLessEqual(built.budget.operations, 100000)
                    self.assertLessEqual(len(simulator.work._cache), 256)
                self.assertEqual(outputs[0], outputs[1])
                if case == "P23":
                    self.assertEqual(len(built.model.actions), 32)
                    self.assertGreater(costs[1] - costs[0], 1000)

    def test_any_nonzero_angular_bound_retains_the_complete_offset_recurrence(self):
        zero = reach_phase.PhaseBound()
        self.assertTrue(reach_phase._local_translation_independent(zero))
        for field in ("angular_speed_upper_rad_per_s", "angular_acceleration_upper_rad_per_s2",
                      "actual_angular_speed_upper_rad_per_s", "angular_velocity_error_rad_per_s"):
            for value in (F(1, 1 << 200), False, 0):
                with self.subTest(field=field, value=value):
                    self.assertFalse(reach_phase._local_translation_independent(replace(zero, **{field: value})))

    def test_hot_results_revalidate_original_spatial_operands_after_callback_cap_change(self):
        simulator = mounted_phases(1, extent=F(1 << 2300))
        reach_phase.phase_bounds(simulator, F(0), F(1))
        original = simulator.work.charge

        def charge(kind="checkpoint", amount=1):
            if kind == "phase_composition_extent_identity":
                simulator.work.max_operand_bits = 2048
            original(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            with self.assertRaises(ReachAdmissionError) as caught:
                reach_phase.phase_bounds(simulator, F(0), F(1))
        self.assertEqual(caught.exception.reach_code, "reach_resource")
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_cancelled_hot_lookup_and_replacement_preserve_the_original_result(self):
        for operation in ("lookup", "remember"):
            with self.subTest(operation=operation):
                simulator = mounted_phases(2)
                baseline = reach_phase.phase_bounds(simulator, F(0), F(1))
                retained = {key: value for key, value in simulator.work._cache.items() if mount_key(key)}
                self.assertTrue(retained)
                original = getattr(simulator.work, operation)
                marker = RuntimeError("cancel translated mount " + operation)

                def checked(key, *args):
                    if mount_key(key):
                        with patch.object(simulator.work, "external_check", side_effect=marker):
                            return original(key, *args)
                    return original(key, *args)

                with patch.object(simulator.work, operation, checked):
                    with self.assertRaises(RuntimeError) as caught:
                        reach_phase.phase_bounds(simulator, F(0), F(1))
                self.assertIs(caught.exception, marker)
                self.assertIs(simulator.work.callback_error, marker)
                for key, value in retained.items():
                    self.assertIs(simulator.work._cache[key], value)
                self.assertEqual(reach_phase.phase_bounds(simulator, F(0), F(1)), baseline)

    def test_eviction_and_changed_root_allowance_recompute_fresh_exact_bounds(self):
        simulator = mounted_phases(2)
        baseline = reach_phase.phase_bounds(simulator, F(0), F(1))
        simulator.state.root_rotation_errors["rig"] = F(1, 1024)
        actual = reach_phase.phase_bounds(simulator, F(0), F(1))
        with patch.object(reach_phase, "_local_translation_independent", return_value=False):
            expected = reach_phase.phase_bounds(simulator, F(0), F(1))
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, baseline)
        for index in range(simulator.work.max_cache_entries + 1):
            simulator.work.remember(("mount_test_eviction", index), index)
        self.assertEqual(len(simulator.work._cache), 256)
        self.assertEqual(reach_phase.phase_bounds(simulator, F(0), F(1)), actual)
        self.assertLessEqual(len(simulator.work._cache), 256)


if __name__ == "__main__":
    unittest.main()
