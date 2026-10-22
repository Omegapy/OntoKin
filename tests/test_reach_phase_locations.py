"""Exact final bounds from deferred repeated source-path locations."""
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.construction import compile_construction
from ontokin.reach_export import recording_phase_bounds
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from test_reach_phase import source
from test_reach_phase_coaxial import pose
from test_reach_phase_mounts import PlanningSimulator, mounted_phases
from test_reach_phase_recording_proof import proof_chain


def placed_chain():
    simulator = proof_chain()
    simulator.model.sites["rig.base"].pose = pose((1.0, 2.0, 0.0))
    return simulator


class ReachPhaseLocationTests(unittest.TestCase):
    def test_complete_translated_mount_maps_equal_eager_bounds(self):
        for rotation_error in (F(0), F(1, 2**44)):
            outputs = []
            for defer in (True, False):
                simulator = mounted_phases(32, anchor_rotation=rotation_error)
                with patch.object(reach_phase, "_defer_phase_locations", return_value=defer):
                    outputs.append(reach_phase.phase_bounds(simulator, F(0), F(1)))
                self.assertEqual(simulator.work.operations, sum(simulator.work.counts.values()))
                self.assertLessEqual(len(simulator.work._cache), 256)
            self.assertEqual(outputs[0], outputs[1])
            for kind in ("objects", "frames"):
                self.assertTrue(all(type(bound) is reach_phase.PhaseBound for bound in outputs[0][kind].values()))
            for path, bound in outputs[0]["objects"].items():
                self.assertIs(bound, outputs[0]["frames"][path + ".frame"])

    def test_actual_p23_and_moving_release_paths_equal_the_eager_recurrence(self):
        cases = (("P23", F(0), F(2)), ("P23", F(2), F(3)),
                 ("P01", F(0), F(2)), ("L01", F(0), F(1, 2)),
                 ("L02", F(1, 2), F(3, 2)), ("P16", F(2), F(3)))
        for case, start, end in cases:
            with self.subTest(case=case, start=start):
                outputs, costs = [], []
                for defer in (True, False):
                    built = compile_construction(source(case))
                    simulator = PlanningSimulator(built.model, work=built.reach_work)
                    simulator.advance(start, "after")
                    state = copy.deepcopy(simulator.state)
                    before = built.budget.operations
                    with patch.object(reach_phase, "_defer_phase_locations", return_value=defer):
                        outputs.append(recording_phase_bounds(simulator, start, end, recording_proof=True))
                    costs.append(built.budget.operations - before)
                    self.assertEqual(state, simulator.state)
                    self.assertLessEqual(built.budget.operations, 100000)
                    self.assertLessEqual(len(simulator.work._cache), 256)
                self.assertEqual(outputs[0], outputs[1])
                if case == "P23":
                    self.assertGreater(costs[1] - costs[0], 1000)

    def test_coaxial_descriptors_and_witness_counts_match_complete_materialized_bounds(self):
        outputs = []
        for defer in (True, False):
            simulator = placed_chain()
            with patch.object(reach_phase, "_defer_phase_locations", return_value=defer):
                outputs.append(reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True))
            if defer:
                self.assertGreater(simulator.work.counts.get("phase_location_materialize", 0), 0)
        self.assertEqual(outputs[0], outputs[1])
        actual = outputs[0]
        self.assertEqual(len(reach_phase._BOUND_FIELDS), 18)
        proof = actual["recording_angular_proof"]
        self.assertEqual(proof.frames["second.frame"].rate.value, F(1))
        for path, record in proof.frames.items():
            self.assertEqual(record.trig_count, actual["frames"][path].trig_count)
            self.assertIsNot(record.token, outputs[1]["recording_angular_proof"].frames[path].token)
        self.assertEqual(actual["frames"]["second.frame"].angular_acceleration_upper_rad_per_s2, 0)

    def test_materialization_callback_narrowing_rechecks_the_complete_operands(self):
        simulator = mounted_phases(2, extent=F(1 << 200))
        original = simulator.work.charge

        def charge(kind="checkpoint", amount=1):
            if kind == "phase_location_materialize":
                simulator.work.max_operand_bits = 128
            return original(kind, amount)

        with patch.object(reach_phase, "_defer_phase_locations", return_value=True):
            with patch.object(simulator.work, "charge", charge):
                with self.assertRaises(ReachAdmissionError) as caught:
                    reach_phase.phase_bounds(simulator, F(0), F(1))
        self.assertEqual(caught.exception.reach_code, "reach_resource")
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_relative_recurrence_cap_change_restores_the_complete_parent(self):
        simulator = placed_chain()
        original = simulator.work.charge
        compositions = 0

        def charge(kind="checkpoint", amount=1):
            nonlocal compositions
            if kind == "phase_composition_operand_guard":
                compositions += 1
                if compositions == 2:
                    simulator.work.max_operand_bits = 128
            return original(kind, amount)

        state = copy.deepcopy(simulator.state)
        with patch.object(reach_phase, "_defer_phase_locations", return_value=True):
            with patch.object(simulator.work, "charge", charge):
                with self.assertRaises(ReachAdmissionError) as caught:
                    reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(compositions, 2)
        self.assertGreater(simulator.work.counts.get("phase_location_materialize", 0), 0)
        self.assertEqual(simulator.state, state)

    def test_callback_exception_with_the_private_control_type_remains_original(self):
        simulator = placed_chain()
        marker = reach_phase._PhaseLocationDomainChanged("cancel relative recurrence")
        original = simulator.work.charge

        def charge(kind="checkpoint", amount=1):
            if kind == "phase_composition_operand_guard":
                with patch.object(simulator.work, "external_check", side_effect=marker):
                    return original(kind, amount)
            return original(kind, amount)

        state = copy.deepcopy(simulator.state)
        with patch.object(reach_phase, "_defer_phase_locations", return_value=True):
            with patch.object(simulator.work, "charge", charge):
                with self.assertRaises(reach_phase._PhaseLocationDomainChanged) as caught:
                    reach_phase.phase_bounds(simulator, F(0), F(1))
        self.assertIs(caught.exception, marker)
        self.assertIs(simulator.work.callback_error, marker)
        self.assertEqual(simulator.state, state)

    def test_cancelled_materialization_propagates_and_retry_rebuilds_complete_maps(self):
        simulator = mounted_phases(2)
        state = copy.deepcopy(simulator.state)
        original = simulator.work.charge
        marker = RuntimeError("cancel exact phase location materialization")

        def charge(kind="checkpoint", amount=1):
            if kind == "phase_location_materialize":
                with patch.object(simulator.work, "external_check", side_effect=marker):
                    return original(kind, amount)
            return original(kind, amount)

        with patch.object(reach_phase, "_defer_phase_locations", return_value=True):
            with patch.object(simulator.work, "charge", charge):
                with self.assertRaises(RuntimeError) as caught:
                    reach_phase.phase_bounds(simulator, F(0), F(1))
            self.assertIs(caught.exception, marker)
            self.assertIs(simulator.work.callback_error, marker)
            self.assertEqual(simulator.state, state)
            actual = reach_phase.phase_bounds(simulator, F(0), F(1))
        with patch.object(reach_phase, "_defer_phase_locations", return_value=False):
            expected = reach_phase.phase_bounds(simulator, F(0), F(1))
        self.assertEqual(actual, expected)

    def test_warm_changed_mount_and_cache_eviction_rebuild_exact_locations(self):
        simulator = mounted_phases(2)
        with patch.object(reach_phase, "_defer_phase_locations", return_value=True):
            baseline = reach_phase.phase_bounds(simulator, F(0), F(1))
            simulator.model.follows["mount_1"].offset.position = (F(0), F(1, 7), F(0))
            simulator.state.root_rotation_errors["rig"] = F(1, 1024)
            changed = reach_phase.phase_bounds(simulator, F(0), F(1))
            simulator.work = ReachExecutionWork(max_cache_entries=1)
            evicted = reach_phase.phase_bounds(simulator, F(0), F(1))
        with patch.object(reach_phase, "_defer_phase_locations", return_value=False):
            expected = reach_phase.phase_bounds(simulator, F(0), F(1))
        self.assertNotEqual(changed, baseline)
        self.assertEqual(changed, expected)
        self.assertEqual(evicted, expected)
        self.assertLessEqual(len(simulator.work._cache), 1)

    def test_wider_operands_keep_the_ordinary_eager_recurrence(self):
        self.assertFalse(reach_phase._small_phase_location_operands(False))
        self.assertFalse(reach_phase._small_phase_location_operands(0.0))
        self.assertFalse(reach_phase._small_phase_location_operands(F(1 << 2100)))
        outputs = []
        for defer in (True, False):
            simulator = mounted_phases(2, extent=F(1 << 2100))
            with patch.object(reach_phase, "_defer_phase_locations", return_value=defer):
                outputs.append(reach_phase.phase_bounds(simulator, F(0), F(1)))
            self.assertNotIn("phase_location_materialize", simulator.work.counts)
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
