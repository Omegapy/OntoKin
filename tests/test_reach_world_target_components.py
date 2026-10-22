"""Translated observed points reuse only identical original scalar operands."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import float_bits
from ontokin.reach_runtime import _WorldTargetComponents
from test_reach_relative_observations import prepared


def component_key(key):
    return len(key) > 2 and key[0] == "reach_world_target_point" and key[2] == "translated_components"


def ordinary(simulator, base, payload):
    ops = simulator.pose_ops
    position, target = ops._vector(base.exact_position), ops._vector(payload.target_m)
    rotation = ops._rotation(base.rotation)
    offset = ops.rotate(rotation, target)
    return ops._vector_projection(ops._rounded_vector(ops._add_exact_vectors(position, offset)))


def target(simulator, base, payload):
    return simulator._world_target(payload, F(0), simulator.state, {payload.base_frame: base})


def bits(position):
    return tuple(map(float_bits, position))


class ReachWorldTargetComponentTests(unittest.TestCase):
    def test_32_translated_points_match_original_kernels_with_less_shared_work(self):
        for axis in ((0, 0, 1), (1, 0, 0), (1, 1, 1)):
            with self.subTest(axis=axis):
                costs, outputs = [], []
                for reuse in (True, False):
                    simulator = prepared()
                    payload = simulator.model.actions["reach"].reach
                    rotation = simulator.pose_ops.axis_rotation(axis, F(2, 7))
                    base = simulator.pose_ops.make(position=(F(2, 7), F(0), F(-3, 5)), orientation=rotation)
                    before = simulator.work.operations
                    values = []
                    for index in range(32):
                        moved = replace(base, exact_position=(base.exact_position[0], F(index, 4), base.exact_position[2]))
                        point = target(simulator, moved, payload).position if reuse else ordinary(simulator, moved, payload)
                        values.append(bits(point))
                    costs.append(simulator.work.operations - before)
                    outputs.append(values)
                    self.assertLessEqual(len(simulator.work._cache), simulator.work.max_cache_entries)
                    self.assertEqual(simulator.work.operations, sum(simulator.work.counts.values()))
                self.assertEqual(outputs[0], outputs[1])
                self.assertLess(costs[0], costs[1])

    def test_unchanged_grid_component_keeps_its_original_binary64_projection(self):
        simulator = prepared()
        payload = replace(simulator.model.actions["reach"].reach, target_m=(0.0, 0.0, 0.0))
        base = simulator.pose_ops.make(position=(F(1), F(0), F(0)))
        first = target(simulator, base, payload)
        moved = replace(base, exact_position=(F(1) + F(1, 1 << 100), F(0), F(0)))
        before = simulator.work.counts.get("binary64_round", 0)
        with patch.object(simulator.pose_ops, "rotate", side_effect=AssertionError("unchanged rotated target")):
            changed = target(simulator, moved, payload)
        self.assertEqual(simulator.work.counts.get("binary64_round", 0), before)
        self.assertEqual(bits(changed.position), bits(first.position))
        self.assertEqual(bits(changed.position), bits(ordinary(simulator, moved, payload)))
        retained = [value for key, value in simulator.work._cache.items() if component_key(key)]
        self.assertEqual(len(retained), 1)
        self.assertIs(type(retained[0]), _WorldTargetComponents)
        self.assertEqual(retained[0].position, moved.exact_position)

    def test_complete_target_and_rotation_operands_select_distinct_templates(self):
        simulator = prepared()
        payload = simulator.model.actions["reach"].reach
        base = simulator.pose_ops.make(position=(F(2), F(3), F(5)))
        first = target(simulator, base, payload)
        variants = (
            (base, replace(payload, target_m=(2.0, -1.0, 0.5))),
            (replace(base, rotation=simulator.pose_ops.axis_rotation((1, 0, 0), F(1, 5))), payload),
            (replace(base, rotation=replace(base.rotation, error_rad=F(1, 256))), payload),
        )
        for current, request in variants:
            actual = target(simulator, current, request)
            self.assertEqual(bits(actual.position), bits(ordinary(simulator, current, request)))
            self.assertIsNot(actual, first)
            self.assertIs(target(simulator, current, request), actual)

    def test_newly_narrowed_domain_does_not_guard_an_unused_old_translation(self):
        for stage in ("components", "publication"):
            with self.subTest(stage=stage):
                simulator = prepared()
                # Binary64 zero has a 1075-bit decode preflight. Use ordinary
                # nonzero targets so this 128-bit test isolates the unused
                # old translation, which still requires 201 bits.
                payload = replace(simulator.model.actions["reach"].reach,
                                  target_m=(1.0, 1.0, 1.0))
                base = simulator.pose_ops.make(position=(F(1 << 200), F(0), F(0)))
                target(simulator, base, payload)
                moved = replace(base, exact_position=(F(1), F(0), F(0)))
                expected = ordinary(simulator, moved, payload)
                changed = False
                original_charge, original_remember = simulator.work.charge, simulator.work.remember

                def charge(kind="checkpoint", amount=1):
                    nonlocal changed
                    if stage == "components" and kind == "source_world_target_components" and not changed:
                        changed = True
                        simulator.work.max_operand_bits = 128
                    return original_charge(kind, amount)

                def remember(key, value):
                    nonlocal changed
                    if stage == "publication" and component_key(key) and not changed:
                        changed = True
                        simulator.work.max_operand_bits = 128
                    return original_remember(key, value)

                previous = copy.deepcopy(simulator.state)
                with patch.object(simulator.work, "charge", charge), patch.object(simulator.work, "remember", remember):
                    result = target(simulator, moved, payload)
                self.assertTrue(changed)
                self.assertEqual(simulator.work.max_operand_bits, 128)
                self.assertEqual(bits(result.position), bits(expected))
                self.assertEqual(simulator.state, previous)

    def test_cancelled_components_or_replacement_keeps_completed_point_and_state(self):
        for stage in ("components", "publication"):
            with self.subTest(stage=stage):
                simulator = prepared()
                payload = simulator.model.actions["reach"].reach
                base = simulator.pose_ops.make(position=(F(1), F(0), F(0)))
                first = target(simulator, base, payload)
                moved = replace(base, exact_position=(F(1), F(2), F(0)))
                retained = {key: value for key, value in simulator.work._cache.items() if component_key(key)}
                previous = copy.deepcopy(simulator.state)
                marker = RuntimeError("cancel translated point " + stage)
                original_charge, original_remember = simulator.work.charge, simulator.work.remember

                def charge(kind="checkpoint", amount=1):
                    if stage == "components" and kind == "source_world_target_components":
                        with patch.object(simulator.work, "external_check", side_effect=marker):
                            return original_charge(kind, amount)
                    return original_charge(kind, amount)

                def remember(key, value):
                    if stage == "publication" and component_key(key):
                        with patch.object(simulator.work, "external_check", side_effect=marker):
                            return original_remember(key, value)
                    return original_remember(key, value)

                with patch.object(simulator.work, "charge", charge), patch.object(simulator.work, "remember", remember):
                    with self.assertRaises(RuntimeError) as caught:
                        target(simulator, moved, payload)
                self.assertIs(caught.exception, marker)
                self.assertIs(simulator.work.callback_error, marker)
                self.assertEqual(simulator.state, previous)
                for key, value in retained.items():
                    self.assertIs(simulator.work._cache[key], value)
                self.assertIs(target(simulator, base, payload), first)
                retried = target(simulator, moved, payload)
                self.assertEqual(bits(retried.position), bits(ordinary(simulator, moved, payload)))

    def test_eviction_keeps_values_exact_without_growing_the_cache(self):
        outputs = []
        for capacity in (1, 8, 256):
            simulator = prepared(capacity=capacity)
            payload = simulator.model.actions["reach"].reach
            base = simulator.pose_ops.make(orientation=simulator.pose_ops.axis_rotation((0, 0, 1), F(1, 3)))
            values = []
            for index in range(8):
                moved = replace(base, exact_position=(F(0), F(index), F(0)))
                actual = target(simulator, moved, payload)
                values.append(bits(actual.position))
                self.assertEqual(bits(actual.position), bits(ordinary(simulator, moved, payload)))
                self.assertLessEqual(len(simulator.work._cache), capacity)
            outputs.append(values)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])


if __name__ == "__main__":
    unittest.main()
