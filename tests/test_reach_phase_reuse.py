"""Pure source phase reuse preserves exact proof inputs and original work."""
import copy
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_phase import _CACHE_DOMAIN, joint_phase, phase_bounds
from ontokin.reach_pose import AXIS_ERROR, EXPOSED_ROTATION_ERROR, PRODUCT_ERROR, VECTOR_ERROR
from test_reach_phase import simulator, source


@contextmanager
def uncached_phases(work):
    """Force the same pure equations to execute, retaining lookup charges."""
    original = work.lookup

    def lookup(key):
        if key[0] == _CACHE_DOMAIN:
            work.charge("cache_lookup")
            return None
        return original(key)

    with patch.object(work, "lookup", lookup):
        yield


class ReachPhaseReuseTests(unittest.TestCase):
    def test_translated_recurrence_preserves_original_uniform_formula_exactly(self):
        sim = simulator(source("P01"))
        sim.advance(F(0), "after")
        baseline = phase_bounds(sim, F(0), F(2))
        incoming = sim._incoming(sim.state)
        roots = [path for path in sim.model.objects if path not in incoming]
        state = copy.deepcopy(sim.state)
        for path in roots:
            state.positions[path] = (-100.0, 2.0, 3.0)
            state.ideal_positions[path] = (F(-100), F(2), F(3))
        actual = phase_bounds(sim, F(0), F(2), state)
        for path, bound in actual["frames"].items():
            if path == "world":
                continue
            previous = baseline["frames"][path]
            self.assertEqual(bound.max_position_l1_m - previous.max_position_l1_m, F(105))
            self.assertEqual(bound.position_error_m - previous.position_error_m, F(105, 1 << 53))
            self.assertEqual(replace(bound, max_position_l1_m=previous.max_position_l1_m,
                                     position_error_m=previous.position_error_m), previous)
            rotation = (bound.anchor_rotation_error_rad + bound.coordinate_angle_error_rad
                        + bound.trig_count * AXIS_ERROR + bound.product_count * PRODUCT_ERROR)
            position = (bound.anchor_position_error_m + bound.path_offset_l1_m * rotation
                        + bound.vector_round_count * VECTOR_ERROR
                        + bound.max_position_l1_m / (1 << 53) + F(3, 1 << 1075))
            self.assertEqual(bound.rotation_error_rad, rotation + EXPOSED_ROTATION_ERROR)
            self.assertEqual(bound.position_error_m, position)

    def test_complete_phase_values_equal_forced_exact_recomputation(self):
        for name, start, end in (("P01", F(0), F(2)), ("L01", F(0), F(1, 2)),
                                 ("L02", F(1, 2), F(3, 2)), ("P16", F(2), F(3))):
            with self.subTest(case=name):
                cached = simulator(source(name))
                cached.advance(start, "after")
                actual = cached.phase_bounds(start, end)
                plain = simulator(source(name))
                with uncached_phases(plain.work):
                    plain.advance(start, "after")
                    expected = plain.phase_bounds(start, end)
                self.assertEqual(actual, expected)
                self.assertLess(cached.work.operations, plain.work.operations)

    def test_translated_and_differently_anchored_paths_do_not_borrow_bounds(self):
        sim = simulator(source("P01"))
        sim.advance(F(0), "after")
        baseline = phase_bounds(sim, F(0), F(2))
        incoming = sim._incoming(sim.state)
        root = next(path for path in sim.model.objects if path not in incoming)
        for change in ("translation", "ideal_position", "rotation_error"):
            with self.subTest(change=change):
                state = copy.deepcopy(sim.state)
                if change == "translation":
                    state.positions[root] = (1.0, 0.0, 0.0)
                    state.ideal_positions[root] = (F(1), F(0), F(0))
                elif change == "ideal_position":
                    state.ideal_positions[root] = (F(1, 1000), F(0), F(0))
                else:
                    state.root_rotation_errors[root] = F(1, 1000)
                actual = phase_bounds(sim, F(0), F(2), state)
                with uncached_phases(sim.work):
                    expected = phase_bounds(sim, F(0), F(2), state)
                self.assertEqual(actual, expected)
                self.assertNotEqual(actual, baseline)

        dynamic = simulator(source("P16"))
        dynamic.advance(F(2), "after")
        baseline = phase_bounds(dynamic, F(2), F(3))
        state = copy.deepcopy(dynamic.state)
        previous = state.dynamic_errors["payload"]
        state.dynamic_errors["payload"] = replace(previous,
            velocity_m_per_s=previous.velocity_m_per_s + F(1, 1000),
            angular_velocity_rad_per_s=previous.angular_velocity_rad_per_s + F(1, 1000))
        actual = phase_bounds(dynamic, F(2), F(3), state)
        with uncached_phases(dynamic.work):
            expected = phase_bounds(dynamic, F(2), F(3), state)
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, baseline)

    def test_joint_key_retains_actual_ideal_target_clock_duration_and_status(self):
        sim = simulator(source("P01"))
        sim.advance(F(0), "after")
        action = sim.model.actions["reach"]
        elbow = action.reach.elbow
        base = joint_phase(sim, elbow, F(0), F(1, 2), sim.state)
        for change in ("actual", "ideal", "target", "duration", "elapsed", "paused", "endpoint"):
            with self.subTest(change=change):
                state = copy.deepcopy(sim.state)
                runtime = state.actions["reach"]
                end, duration = F(1, 2), action.duration
                if change == "actual":
                    runtime.initial = (runtime.initial[0], 0.125)
                elif change == "ideal":
                    runtime.ideal_initial = (runtime.ideal_initial[0], F(1, 8))
                elif change == "target":
                    runtime.solution = replace(runtime.solution,
                        target_rad=(runtime.solution.target_rad[0], 1.0))
                elif change == "duration":
                    duration *= 2
                elif change == "elapsed":
                    runtime.elapsed = F(1, 8)
                elif change == "paused":
                    runtime.status = "paused"
                else:
                    end = F(1)
                with patch.object(action, "duration", duration):
                    actual = joint_phase(sim, elbow, F(0), end, state)
                    with uncached_phases(sim.work):
                        expected = joint_phase(sim, elbow, F(0), end, state)
                self.assertEqual(actual, expected)
                self.assertNotEqual(actual, base)

        for invalid in (False, F(1 << sim.work.max_operand_bits)):
            state = copy.deepcopy(sim.state)
            runtime = state.actions["reach"]
            runtime.ideal_initial = (runtime.ideal_initial[0], invalid)
            with self.assertRaises(ReachAdmissionError):
                joint_phase(sim, elbow, F(0), F(1, 2), state)

    def test_warm_reuse_keeps_fresh_maps_bounded_storage_and_cancellation(self):
        sim = simulator(source("L01"))
        sim.advance(F(0), "after")
        before = sim.work.operations
        first = phase_bounds(sim, F(0), F(1, 2))
        cold = sim.work.operations - before
        before = sim.work.operations
        again = phase_bounds(sim, F(0), F(1, 2))
        warm = sim.work.operations - before
        self.assertEqual(first, again)
        self.assertGreater(warm, 0)
        self.assertLess(warm, cold)
        self.assertIsNot(first["frames"], again["frames"])
        bound = next(value for path, value in first["frames"].items() if path != "world")
        with self.assertRaises(FrozenInstanceError):
            bound.velocity_error_m_per_s = F(0)
        first["frames"].clear()
        self.assertTrue(again["frames"])

        for index in range(sim.work.max_cache_entries + 1):
            sim.work.remember(("phase_reuse_test", index), index)
        self.assertEqual(len(sim.work._cache), sim.work.max_cache_entries)
        self.assertEqual(phase_bounds(sim, F(0), F(1, 2)), again)
        self.assertLessEqual(len(sim.work._cache), 256)
        with self.assertRaisesRegex(ValueError, "authored boundary"):
            phase_bounds(sim, F(0), F(1))

        marker = RuntimeError("cancel warm phase proof")
        with patch.object(sim.work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                phase_bounds(sim, F(0), F(1, 2))
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
