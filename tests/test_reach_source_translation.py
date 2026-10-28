"""Exact source-node reuse preserves grid ties, rates, histories, and domains."""
import copy
from dataclasses import replace
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ontokin.construction import compile_construction
from ontokin.model import Pose
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import BITS, PoseValue, ReachPoseOps, ZERO
from ontokin.reach_runtime import ReachSimulator
from test_reach_phase import source
from test_reach_phase_mounts import PlanningSimulator


def numerical_simulator():
    simulator = object.__new__(ReachSimulator)
    simulator.work = ReachExecutionWork()
    simulator.pose_ops = ReachPoseOps(simulator.work)
    simulator.model = SimpleNamespace(objects=dict.fromkeys(range(257)), sites={}, program_revision="source")
    return simulator


def build_node(simulator, signature):
    ops = simulator.pose_ops
    if len(signature) == 2:
        parent, local = signature
        return ops.compose(parent, simulator._constant_pose(local))
    if signature[0] == "follow":
        _, parent, local = signature
        return ops.compose(parent, simulator._constant_pose(local))
    _, parent, kind, axis, coordinate, slope, local = signature
    relative = (ops.hinge_pose(axis, coordinate, slope) if kind == "hinge" else
                ops.make(position=ops.scale(axis, F(coordinate)), velocity=ops.scale(axis, slope)))
    return ops.compose(ops.compose(parent, relative), simulator._constant_pose(local, inverse=True))


def slot(simulator, signature, path="object"):
    return simulator._pose_slot(path, signature, lambda: build_node(simulator, signature))


class ReachSourceTranslationTests(unittest.TestCase):
    def test_a_pose_from_another_request_cannot_supply_a_translated_slot(self):
        sim = numerical_simulator()
        other = ReachPoseOps(ReachExecutionWork())
        signature = ("follow", other.make(), Pose())
        self.assertIsNone(sim._translated_source_slot(signature, Mock()))
        self.assertFalse(any(key[0] == "reach_source_translated_node" for key in sim.work._cache))

    def test_even_grid_translation_preserves_halfway_rounding_and_odd_shift_rebuilds(self):
        sim = numerical_simulator()
        local = Pose(position=(2.0 ** (-BITS - 1), 0.0, 0.0))
        values = []
        for grid_integer in (0, 2, 1, 3, -1, -3):
            parent = sim.pose_ops.make(position=(F(grid_integer, 1 << BITS), F(0), F(0)))
            signature = ("follow", parent, local)
            result = slot(sim, signature, "instance_" + str(grid_integer))
            self.assertEqual(result, build_node(sim, signature))
            values.append(result.exact_position[0])
        # The ordinary source first rounds the rotated half-grid local
        # offset, then adds it to the parent. Preserve both stages exactly.
        self.assertEqual(values, [F(index, 1 << BITS) for index in (0, 2, 1, 3, -1, -3)])
        self.assertEqual(sim.work.counts["source_relative_pose_reuse"], 4)

    def test_complete_joint_and_site_values_match_original_sequential_composition(self):
        for kind in ("hinge", "slider", "site"):
            with self.subTest(kind=kind):
                sim = numerical_simulator()
                rotation = sim.pose_ops.axis_rotation((1.0, 0.0, 0.0), F(1, 3))
                initial = sim.pose_ops.make(orientation=rotation,
                    velocity=(F(1, 7), F(2, 3), F(0)), omega=(F(0), F(1, 5), F(0)))
                local = Pose(position=(0.25, 0.5, -0.125), rotation=(0.5, 0.5, 0.5, 0.5))
                outputs = []
                for index in range(5):
                    parent = replace(initial, exact_position=(F(index, 4), F(-index, 2), F(index)), _projection={})
                    signature = ((parent, local) if kind == "site" else
                        ("joint", parent, kind, (0.0, 0.0, 1.0), 0.375, F(1, 3), local))
                    actual = slot(sim, signature, "instance_" + str(index))
                    expected = build_node(sim, signature)
                    self.assertEqual(actual, expected)
                    self.assertEqual((actual.position, actual.orientation, actual.velocity, actual.omega),
                                     (expected.position, expected.orientation, expected.velocity, expected.omega))
                    outputs.append(actual)
                self.assertGreater(sim.work.counts.get("source_relative_pose_reuse", 0), 0)
                self.assertNotEqual(outputs[0].position, outputs[-1].position)
                self.assertLessEqual(len(sim.work._cache), 256)

    def test_each_changed_local_or_parent_operand_requires_its_own_complete_build(self):
        sim = numerical_simulator()
        parent = sim.pose_ops.make()
        local = Pose(position=(0.25, 0.5, 0.0))
        baseline = ("joint", parent, "hinge", (0.0, 0.0, 1.0), 0.375, F(1, 3), local)
        slot(sim, baseline)
        variants = [
            (*baseline[:3], (1.0, 0.0, 0.0), *baseline[4:]),
            (*baseline[:4], 0.5, *baseline[5:]),
            (*baseline[:5], F(1, 4), local),
            (*baseline[:6], replace(local, position=(0.5, 0.5, 0.0))),
            (*baseline[:6], replace(local, rotation=(0.5, 0.5, 0.5, 0.5))),
        ]
        for field, value in (("exact_velocity", (F(1), F(0), F(0))),
                             ("exact_omega", (F(0), F(0), F(1))),
                             ("rotation", replace(parent.rotation, error_rad=F(1, 2048)))):
            variants.append(("joint", replace(parent, **{field: value}), *baseline[2:]))
        for signature in variants:
            with self.subTest(signature=signature):
                build = Mock(side_effect=lambda: build_node(sim, signature))
                actual = sim._pose_slot("object", signature, build)
                self.assertEqual(build.call_count, 1)
                self.assertEqual(actual, build_node(sim, signature))
        signature = ("joint", replace(parent, position_error_m=F(1, 1024)), *baseline[2:])
        build = Mock(side_effect=lambda: build_node(sim, signature))
        actual = sim._pose_slot("object", signature, build)
        self.assertEqual(build.call_count, 0)
        self.assertEqual(actual, build_node(sim, signature))

    def test_recording_identity_and_non_grid_parent_keep_the_original_build(self):
        sim = numerical_simulator()
        parent = sim.pose_ops.make(position=(F(1, 1 << (BITS + 1)), F(0), F(0)))
        signature = ("follow", parent, Pose())
        build = Mock(side_effect=lambda: build_node(sim, signature))
        self.assertEqual(sim._pose_slot("object", signature, build), build_node(sim, signature))
        self.assertEqual(build.call_count, 1)
        self.assertFalse(any(key[0] == "reach_source_translated_node" for key in sim.work._cache))
        parent = sim.pose_ops.make()
        signature = ("follow", parent, Pose())
        for path in (("recorded_transform", "object"), ("recording", "object")):
            with patch.object(sim, "_translated_source_slot", side_effect=AssertionError("source-only reuse")):
                self.assertEqual(slot(sim, signature, path), build_node(sim, signature))

    def test_warm_node_cannot_hide_boolean_coordinates_or_narrowed_live_operands(self):
        sim = numerical_simulator()
        parent = sim.pose_ops.make(position=(F(1 << 80), F(0), F(0)))
        signature = ("joint", parent, "hinge", (0.0, 0.0, 1.0), 0.0, F(0), Pose())
        slot(sim, signature)
        with self.assertRaises(ReachAdmissionError) as caught:
            slot(sim, (*signature[:4], False, *signature[5:]))
        self.assertEqual(caught.exception.reach_code, "reach_domain")
        original = sim.work.charge
        def charge(kind="checkpoint", amount=1):
            if kind == "source_relative_pose_reuse":
                sim.work.max_operand_bits = 64
            original(kind, amount)
        with patch.object(sim.work, "charge", charge):
            with self.assertRaises(ReachAdmissionError) as caught:
                slot(sim, signature)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_cancellation_never_publishes_an_incomplete_node_and_does_not_change_previous_pose(self):
        for warm in (False, True):
            with self.subTest(warm=warm):
                sim = numerical_simulator()
                parent = sim.pose_ops.make()
                signature = ("follow", parent, Pose(position=(0.25, 0.5, 0.0)))
                previous = slot(sim, signature) if warm else None
                original = sim.work.lookup if warm else sim.work.remember
                marker = RuntimeError("cancel translated source node")
                def operation(key, *args):
                    if key[0] == "reach_source_translated_node":
                        with patch.object(sim.work, "external_check", side_effect=marker):
                            return original(key, *args)
                    return original(key, *args)
                with patch.object(sim.work, "lookup" if warm else "remember", operation):
                    with self.assertRaises(RuntimeError) as caught:
                        slot(sim, signature)
                self.assertIs(caught.exception, marker)
                self.assertIs(sim.work.callback_error, marker)
                retained = [value for key, value in sim.work._cache.items() if key[0] == "reach_source_translated_node"]
                if warm:
                    self.assertEqual(len(retained), 1)
                    self.assertIs(retained[0][-1], previous)
                else:
                    self.assertFalse(retained)
                self.assertEqual(slot(sim, signature), build_node(sim, signature))

    def test_cold_build_and_remember_cannot_return_operands_above_a_changed_cap(self):
        for stage in ("build", "remember"):
            with self.subTest(stage=stage):
                sim = numerical_simulator()
                parent = sim.pose_ops.make(position=(F(1 << 200), F(0), F(0)))
                signature = ("follow", parent, Pose())
                original_remember = sim.work.remember

                def build():
                    result = build_node(sim, signature)
                    if stage == "build":
                        sim.work.max_operand_bits = 128
                    return result

                def remember(key, value):
                    if stage == "remember" and key[0] == "reach_source_translated_node":
                        def narrow():
                            sim.work.max_operand_bits = 128
                        with patch.object(sim.work, "external_check", narrow):
                            return original_remember(key, value)
                    return original_remember(key, value)

                with patch.object(sim.work, "remember", remember):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        sim._pose_slot("object", signature, build)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                self.assertFalse(any(key[0] == "reach_source_translated_node" for key in sim.work._cache))

    def test_actual_32_arm_initial_and_terminal_source_values_match_without_reuse(self):
        outputs, costs = [], []
        for reuse in (True, False):
            built = compile_construction(source("P23"))
            simulator = PlanningSimulator(built.model, work=built.reach_work)
            values = []
            def observe():
                for time in (F(0), F(2)):
                    simulator.advance(time, "after")
                    _, frames = simulator._kinematics(time, simulator.state)
                    values.append((dict(frames), copy.deepcopy(simulator._pending_reach_output[3]),
                                   copy.deepcopy(simulator.state.claims), dict(simulator.state.coordinates)))
            if reuse:
                observe()
            else:
                with patch.object(simulator, "_translated_source_slot", return_value=None):
                    observe()
            outputs.append(values)
            costs.append(built.budget.operations)
            self.assertLessEqual(costs[-1], 100000)
            self.assertLessEqual(len(simulator.work._cache), 256)
        self.assertEqual(outputs[0], outputs[1])
        self.assertGreater(costs[1] - costs[0], 1000)


if __name__ == "__main__":
    unittest.main()
