"""Relative observations share pure arithmetic, never source occurrence state."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.json_limits import measure_json
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, float_bits
from ontokin.reach_runtime import ReachSimulator
from reach_agent_support import source_case


def prepared(case="P01", *, capacity=None):
    built = compile_construction(source_case(case))
    work = built.reach_work if capacity is None else ReachExecutionWork(max_cache_entries=capacity)
    return ReachSimulator(built.model, work=work)


def ordinary_tip(ops, base, tip):
    rotation = ops.multiply(ops.inverse_rotation(base.rotation), tip.rotation)
    return ops.make(position=ops.relative_point(base, tip), orientation=rotation)


def exposed_bits(pose):
    return tuple(float_bits(value) for field in ("position", "orientation", "velocity", "omega")
                 for value in getattr(pose, field))


class ReachRelativeObservationTests(unittest.TestCase):
    def pair(self, simulator):
        ops = simulator.pose_ops
        base = ops.make(position=(F(3, 7), F(-2, 5), F(1, 9)),
                        orientation=ops.axis_rotation((0, 0, 1), F(2, 7)),
                        velocity=(F(1), F(2), F(3)), omega=(F(0), F(0), F(5, 7)))
        tip = ops.make(position=(F(9, 7), F(3, 5), F(1, 9)),
                       orientation=ops.axis_rotation((1, 0, 0), F(4, 9)),
                       velocity=(F(2), F(3), F(4)), omega=(F(0), F(2), F(0)))
        return base, tip

    def relative(self, simulator, base, tip):
        action = simulator.model.actions["reach"]
        frames = {action.reach.base_frame: base, action.reach.tip + ".frame": tip}
        simulator._derived_pose_cache.clear()
        with patch.object(simulator, "_kinematics", return_value=({}, frames)):
            return simulator._tip_base(action, F(0), simulator.state)

    def test_translated_relative_poses_keep_exact_private_values_and_bits(self):
        simulator = prepared()
        base, tip = self.pair(simulator)
        expected = ordinary_tip(simulator.pose_ops, base, tip)
        before = simulator.work.counts.get("quaternion_conjugate", 0)
        actual = self.relative(simulator, base, tip)
        self.assertEqual(simulator.work.counts["quaternion_conjugate"] - before, 3)
        self.assertEqual(actual, expected)
        self.assertEqual(actual.position_error_m, expected.position_error_m)
        self.assertEqual(actual.angular_error_rad, expected.angular_error_rad)
        self.assertEqual(exposed_bits(actual), exposed_bits(expected))
        for index in range(1, 33):
            offset = (F(index * 11), F(-index * 3), F(index))
            moved = [replace(value, exact_position=tuple(a + b for a, b in zip(value.exact_position, offset)))
                     for value in (base, tip)]
            before = simulator.work.counts.get("quaternion_conjugate", 0)
            reused = self.relative(simulator, *moved)
            self.assertIs(reused, actual)
            self.assertEqual(simulator.work.counts["quaternion_conjugate"], before)
            self.assertEqual(exposed_bits(reused), exposed_bits(expected))
        self.assertLessEqual(len(simulator.work._cache), simulator.work.max_cache_entries)

    def test_changed_relative_operands_and_allowances_cannot_borrow_a_result(self):
        simulator = prepared()
        base, tip = self.pair(simulator)
        actual = self.relative(simulator, base, tip)
        variants = [
            (replace(base, exact_position=(F(8, 7), *base.exact_position[1:])), tip),
            (base, replace(tip, rotation=simulator.pose_ops.axis_rotation((0, 1, 0), F(1, 3)))),
            (replace(base, rotation=replace(base.rotation, error_rad=base.rotation.error_rad + F(1, 1000))), tip),
            (base, replace(tip, rotation=replace(tip.rotation, error_rad=tip.rotation.error_rad + F(1, 2000)))),
            (simulator.pose_ops.materialize(base), simulator.pose_ops.materialize(tip)),
        ]
        for first, last in variants:
            with self.subTest(base=first.exact_position, allowance=last.angular_error_rad):
                expected = ordinary_tip(simulator.pose_ops, first, last)
                changed = self.relative(simulator, first, last)
                self.assertEqual(changed, expected)
                self.assertEqual(exposed_bits(changed), exposed_bits(expected))
                self.assertEqual(changed.position_error_m, expected.position_error_m)
                self.assertEqual(changed.angular_error_rad, expected.angular_error_rad)
                self.assertIsNot(changed, actual)

    def test_world_target_point_matches_complete_moving_pose_composition(self):
        simulator = prepared()
        base, _ = self.pair(simulator)
        payload = simulator.model.actions["reach"].reach
        variants = [(base, payload),
            (replace(base, exact_position=(F(-7, 9), *base.exact_position[1:])), payload),
            (replace(base, rotation=simulator.pose_ops.axis_rotation((1, 1, 1), F(2, 3))), payload),
            (base, replace(payload, target_m=(math.nextafter(1.0, math.inf), -2.0, 0.5))),
            (simulator.pose_ops.materialize(base), replace(payload, target_m=(-0.0, 0.0, 0.0)))]
        previous = None
        for current, request in variants:
            with self.subTest(position=current.exact_position, target=request.target_m):
                expected = simulator.pose_ops.compose(current, simulator.pose_ops.make(position=request.target_m))
                frames = {request.base_frame: current}
                with patch.object(simulator.pose_ops, "compose", side_effect=AssertionError("unused target pose")):
                    actual = simulator._world_target(request, F(0), simulator.state, frames)
                    repeated = simulator._world_target(request, F(0), simulator.state, frames)
                self.assertEqual(tuple(map(float_bits, actual.position)), tuple(map(float_bits, expected.position)))
                self.assertIs(actual, repeated)
                self.assertIsNot(actual, previous)
                previous = actual

    def test_current_target_scalar_domains_are_checked_even_after_reuse(self):
        simulator = prepared()
        payload = simulator.model.actions["reach"].reach
        base = simulator.pose_ops.make()
        frames = {payload.base_frame: base}
        simulator._world_target(payload, F(0), simulator.state, frames)
        for target in ((True, 1.0, 0.0), (1.0, 1.0), (math.nan, 1.0, 0.0), (math.inf, 1.0, 0.0)):
            with self.subTest(target=target):
                with self.assertRaises(ReachAdmissionError):
                    simulator._world_target(replace(payload, target_m=target), F(0), simulator.state, frames)
        for components in ((True, F(0), F(0), F(0)), (F(0), F(0), F(0), F(0))):
            with self.subTest(components=components):
                invalid = replace(base, rotation=replace(base.rotation, components=components))
                with self.assertRaises(ReachAdmissionError):
                    simulator._world_target(payload, F(0), simulator.state, {payload.base_frame: invalid})

    def test_lowered_live_domain_rechecks_warm_relative_and_target_proofs(self):
        for method in ("tip", "target"):
            for during_lookup in (False, True):
                with self.subTest(method=method, during_lookup=during_lookup):
                    simulator = prepared()
                    base, tip = self.pair(simulator)
                    payload = simulator.model.actions["reach"].reach
                    invoke = ((lambda: self.relative(simulator, base, tip)) if method == "tip" else
                              (lambda: simulator._world_target(payload, F(0), simulator.state,
                                                               {payload.base_frame: base})))
                    invoke()
                    original = simulator.work.lookup
                    prefix = "reach_relative_tip_pose" if method == "tip" else "reach_world_target_point"
                    changed = []
                    def lookup(key):
                        result = original(key)
                        if key[0] == prefix and not changed:
                            simulator.work.max_operand_bits = 128
                            changed.append(True)
                        return result
                    if not during_lookup:
                        simulator.work.max_operand_bits = 128
                    with patch.object(simulator.work, "lookup", side_effect=lookup if during_lookup else original):
                        with self.assertRaises(ReachAdmissionError) as caught:
                            invoke()
                    self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                    if during_lookup:
                        self.assertEqual(changed, [True])

    def test_cancellation_of_warm_numeric_lookup_keeps_state_unchanged(self):
        for method in ("tip", "target"):
            with self.subTest(method=method):
                simulator = prepared()
                base, tip = self.pair(simulator)
                payload = simulator.model.actions["reach"].reach
                invoke = ((lambda: self.relative(simulator, base, tip)) if method == "tip" else
                          (lambda: simulator._world_target(payload, F(0), simulator.state,
                                                           {payload.base_frame: base})))
                invoke()
                before = copy.deepcopy(simulator.state)
                original_check, original_lookup = simulator.work.external_check, simulator.work.lookup
                marker = RuntimeError("cancel shared physical arithmetic")
                armed = [False]
                prefix = "reach_relative_tip_pose" if method == "tip" else "reach_world_target_point"
                def lookup(key):
                    armed[0] = key[0] == prefix
                    try:
                        return original_lookup(key)
                    finally:
                        armed[0] = False
                def check():
                    if armed[0]:
                        raise marker
                    if original_check is not None:
                        original_check()
                with patch.object(simulator.work, "lookup", side_effect=lookup), \
                        patch.object(simulator.work, "external_check", side_effect=check):
                    with self.assertRaises(RuntimeError) as caught:
                        invoke()
                self.assertIs(caught.exception, marker)
                self.assertIs(simulator.work.callback_error, marker)
                self.assertEqual(simulator.state, before)

    def test_cancelled_target_observation_rolls_back_complete_boundary(self):
        simulator = prepared()
        before = simulator.advance(F(0), "before")
        state, index = simulator.state, simulator.event_index
        saved = copy.deepcopy(state)
        original_target, original_check = simulator._world_target, simulator.work.external_check
        marker = RuntimeError("cancel target during complete staged projection")
        armed = [False]
        def target(*arguments):
            armed[0] = True
            try:
                return original_target(*arguments)
            finally:
                armed[0] = False
        def check():
            if armed[0]:
                raise marker
            if original_check is not None:
                original_check()
        with patch.object(simulator, "_world_target", side_effect=target), \
                patch.object(simulator.work, "external_check", side_effect=check):
            with self.assertRaises(RuntimeError) as caught:
                simulator.advance(F(0), "after")
        self.assertIs(caught.exception, marker)
        self.assertIs(simulator.state, state)
        self.assertEqual(simulator.state, saved)
        self.assertEqual(simulator.event_index, index)
        self.assertEqual(simulator._derived_pose_cache, {})
        self.assertIsNone(simulator._pending_reach_output)
        self.assertIsNone(simulator._terminal_pose_context)
        self.assertEqual(simulator.snapshot(F(0), "before"), before)

    def test_complete_32_arm_occurrences_match_direct_equations_with_less_work(self):
        actual, expected = prepared("P23"), prepared("P23")
        def direct(action, time, state):
            payload = action.reach
            physical = tuple(expected._coordinate(joint, time, state)
                             for joint in (payload.shoulder, payload.elbow))
            _, frames = expected._kinematics(time, state)
            base, tip = frames[payload.base_frame], frames[payload.tip + ".frame"]
            relative = ordinary_tip(expected.pose_ops, base, tip)
            target = expected.pose_ops.compose(base, expected.pose_ops.make(position=payload.target_m))
            return physical, (relative.position, relative.orientation), (tip.position, tip.orientation), target.position
        start, old_start = actual.work.operations, expected.work.operations
        result = actual.advance(F(0), "after")
        with patch.object(expected, "_physical_observation", side_effect=direct):
            reference = expected.advance(F(0), "after")
        self.assertEqual(result, reference)
        self.assertEqual(measure_json(result), measure_json(reference))
        self.assertEqual(len(result["reaches"]), 32)
        self.assertEqual(len({tuple(value["element_id"]) for value in result["reaches"].values()}), 32)
        self.assertLess(actual.work.operations - start, expected.work.operations - old_start)
        self.assertLessEqual(len(actual.work._cache), actual.work.max_cache_entries)

    def test_small_cache_retains_exact_values_without_growth(self):
        simulator = prepared(capacity=1)
        base, tip = self.pair(simulator)
        payload = simulator.model.actions["reach"].reach
        for _ in range(3):
            actual = self.relative(simulator, base, tip)
            expected = ordinary_tip(simulator.pose_ops, base, tip)
            self.assertEqual(exposed_bits(actual), exposed_bits(expected))
            point = simulator._world_target(payload, F(0), simulator.state, {payload.base_frame: base})
            direct = simulator.pose_ops.compose(base, simulator.pose_ops.make(position=payload.target_m))
            self.assertEqual(tuple(map(float_bits, point.position)), tuple(map(float_bits, direct.position)))
            self.assertLessEqual(len(simulator.work._cache), 1)


if __name__ == "__main__":
    unittest.main()
