"""A natural static handoff keeps exact poses and discards incoming rates."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, float_bits
from ontokin.reach_pose import RotationValue
from ontokin.reach_runtime import ReachSimulator
from test_reach_phase import changed, source


def prepared(case, *, bundle=None):
    built = compile_construction(source(case) if bundle is None else bundle)
    return ReachSimulator(built.model, work=built.reach_work)


class ReachTerminalStaticGraphTests(unittest.TestCase):
    def test_complete_source_graph_and_allowances_match_ordinary_reconstruction(self):
        for case, time in (("P01", F(2)), ("P13", F(2)), ("P14", F(3)), ("P18", F(2)), ("P23", F(2))):
            with self.subTest(case=case):
                actual, expected = prepared(case), prepared(case)
                self.assertEqual(actual.advance(time, "before"), expected.advance(time, "before"))
                incoming = actual._kinematics(time, actual.state)
                incoming_values = {path: (value.exact_position, value.rotation, value.exact_velocity,
                                         value.exact_omega, value.position_error_m)
                                   for path, value in incoming[1].items()}
                start, reference_start = actual.work.operations, expected.work.operations
                result = actual.advance(time, "after")
                used = actual.work.counts.get("source_terminal_static_node", 0)
                with patch.object(expected, "_terminal_static_kinematics", return_value=None):
                    reference = expected.advance(time, "after")
                self.assertGreater(used, 0)
                self.assertEqual(result, reference)
                outgoing = actual._kinematics(time, actual.state)
                reconstructed = expected._kinematics(time, expected.state)
                self.assertEqual(outgoing, reconstructed)
                for path, value in outgoing[1].items():
                    self.assertEqual((value.exact_position, value.rotation, value.position_error_m),
                                     (incoming_values[path][0], incoming_values[path][1], incoming_values[path][4]))
                    self.assertEqual(value.velocity, (0.0, 0.0, 0.0))
                    self.assertEqual(value.omega, (0.0, 0.0, 0.0))
                    self.assertEqual(tuple(float_bits(component) for field in ("position", "orientation", "velocity", "omega")
                                           for component in getattr(value, field)),
                                     tuple(float_bits(component) for field in ("position", "orientation", "velocity", "omega")
                                           for component in getattr(reconstructed[1][path], field)))
                self.assertTrue(any(any(values[3]) for values in incoming_values.values()))
                self.assertEqual(incoming_values, {
                    path: (value.exact_position, value.rotation, value.exact_velocity,
                           value.exact_omega, value.position_error_m)
                    for path, value in incoming[1].items()})
                if case == "P23":
                    self.assertLess(actual.work.operations - start, expected.work.operations - reference_start)
                self.assertLessEqual(len(actual._pose_cache), 1)
                self.assertLessEqual(len(actual.work._cache), actual.work.max_cache_entries)
                self.assertIsNone(actual._terminal_pose_context)

    def test_changed_final_coordinate_or_root_pose_uses_fresh_arithmetic(self):
        for change in ("coordinate", "root_position", "root_orientation", "mode"):
            with self.subTest(change=change):
                actual, expected = prepared("P01"), prepared("P01")
                actual.advance(F(2), "before")
                expected.advance(F(2), "before")

                def perturb(simulator, original):
                    def validate(time, staged, incoming):
                        if change == "coordinate":
                            joint = simulator.model.actions["reach"].reach.elbow
                            staged.coordinates[joint] = math.nextafter(staged.coordinates[joint], math.inf)
                        else:
                            topology = simulator._incoming(staged)
                            root = next(path for path in simulator.model.objects if path not in topology)
                            if change == "root_position":
                                x, y, z = staged.positions[root]
                                staged.positions[root] = (x + 1.0, y, z)
                            elif change == "root_orientation":
                                staged.orientations[root] = (0.0, 0.0, 0.0, 1.0)
                            else:
                                staged.modes[root] = "fixed"
                        return original(time, staged, incoming)
                    return validate

                with patch.object(actual, "_validate_staged", side_effect=perturb(actual, actual._validate_staged)):
                    result = actual.advance(F(2), "after")
                with patch.object(expected, "_validate_staged", side_effect=perturb(expected, expected._validate_staged)), \
                        patch.object(expected, "_terminal_static_kinematics", return_value=None):
                    reference = expected.advance(F(2), "after")
                self.assertEqual(result, reference)
                self.assertEqual(actual._kinematics(F(2), actual.state), expected._kinematics(F(2), expected.state))
                self.assertEqual(actual.work.counts.get("source_terminal_static_node", 0), 0)

    def test_source_events_ordinary_completions_and_dynamics_do_not_reuse(self):
        for case in ("P11", "P16"):
            with self.subTest(case=case):
                actual, expected = prepared(case), prepared(case)
                actual.advance(F(2), "before")
                expected.advance(F(2), "before")
                result = actual.advance(F(2), "after")
                with patch.object(expected, "_terminal_static_kinematics", return_value=None):
                    reference = expected.advance(F(2), "after")
                self.assertEqual(result, reference)
                self.assertEqual(actual.work.counts.get("source_terminal_static_node", 0), 0)
        released = changed(source("P16"), 'at 2[s] sequence { release', 'at 1[s] sequence { release')
        simulator = prepared("P16", bundle=released)
        simulator.advance(F(2), "before")
        self.assertTrue(simulator.state.dynamic)
        simulator.advance(F(2), "after")
        self.assertEqual(simulator.work.counts.get("source_terminal_static_node", 0), 0)
        # A separate action still owns a coordinate after the reach completes.
        moving = changed(source("P11"), 'rig.look_to(30[deg], 2[s])', 'rig.look_to(30[deg], 3[s])')
        simulator = prepared("P11", bundle=moving)
        simulator.advance(F(2), "after")
        self.assertTrue(simulator.state.claims)
        self.assertEqual(simulator.work.counts.get("source_terminal_static_node", 0), 0)

    def test_cancelled_node_or_final_guard_rolls_back_the_whole_boundary(self):
        for stage in ("source_terminal_static_node", "source_terminal_static_final_guard"):
            with self.subTest(stage=stage):
                simulator = prepared("P01")
                before = simulator.advance(F(2), "before")
                state, index = simulator.state, simulator.event_index
                saved = copy.deepcopy(state)
                marker = RuntimeError("cancel complete static handoff")
                original_charge, original_check = simulator.work.charge, simulator.work.external_check
                current = [None]

                def charge(kind="checkpoint", amount=1):
                    current[0] = kind
                    return original_charge(kind, amount)

                def check():
                    if current[0] == stage:
                        raise marker
                    if original_check is not None:
                        original_check()

                with patch.object(simulator.work, "charge", side_effect=charge), \
                        patch.object(simulator.work, "external_check", side_effect=check):
                    with self.assertRaises(RuntimeError) as caught:
                        simulator.advance(F(2), "after")
                self.assertIs(caught.exception, marker)
                self.assertIs(simulator.work.callback_error, marker)
                self.assertIs(simulator.state, state)
                self.assertEqual(simulator.state, saved)
                self.assertEqual(simulator.event_index, index)
                self.assertEqual(simulator._pose_cache, {})
                self.assertIsNone(simulator._terminal_pose_context)
                self.assertIsNone(simulator._pending_reach_output)
                self.assertEqual(simulator.snapshot(F(2), "before"), before)

    def test_lowered_live_operand_domain_falls_back_before_graph_publication(self):
        for stage in ("source_terminal_static_context", "source_terminal_static_node", "source_terminal_static_final_guard"):
            with self.subTest(stage=stage):
                simulator = prepared("P01")
                simulator.advance(F(2), "before")
                state = simulator.state
                original = simulator.work.charge
                narrowed = False
                fallback = []
                terminal = simulator._terminal_static_kinematics

                def charge(kind="checkpoint", amount=1):
                    nonlocal narrowed
                    result = original(kind, amount)
                    if kind == stage and not narrowed:
                        simulator.work.max_operand_bits = 8
                        narrowed = True
                    return result

                def observed(*args):
                    result = terminal(*args)
                    fallback.append(result is None)
                    return result

                with patch.object(simulator.work, "charge", side_effect=charge), \
                        patch.object(simulator, "_terminal_static_kinematics", side_effect=observed):
                    with self.assertRaises((OntoKinError, ReachAdmissionError)) as caught:
                        simulator.advance(F(2), "after")
                self.assertTrue(narrowed)
                self.assertEqual(fallback, [True])
                error = caught.exception
                details = error.details if isinstance(error, ReachAdmissionError) else error.diagnostic.details
                self.assertEqual(details["budget"], "numeric_operand_bits")
                self.assertIs(simulator.state, state)
                self.assertEqual(simulator._pose_cache, {})
                self.assertIsNone(simulator._terminal_pose_context)

    def test_final_callback_coordinate_change_rejects_the_completed_graph(self):
        simulator = prepared("P01")
        simulator.advance(F(2), "before")
        original = simulator.work.charge
        returned = []
        terminal = simulator._terminal_static_kinematics
        changed_coordinate = False

        def charge(kind="checkpoint", amount=1):
            nonlocal changed_coordinate
            result = original(kind, amount)
            if kind == "source_terminal_static_final_guard" and not changed_coordinate:
                state = simulator._terminal_pose_context.staged_state
                path = simulator.model.actions["reach"].reach.elbow
                state.coordinates[path] = math.nextafter(state.coordinates[path], math.inf)
                changed_coordinate = True
            return result

        def observed(*args):
            result = terminal(*args)
            returned.append(result)
            return result

        with patch.object(simulator.work, "charge", side_effect=charge), \
                patch.object(simulator, "_terminal_static_kinematics", side_effect=observed):
            simulator.advance(F(2), "after")
        self.assertTrue(changed_coordinate)
        self.assertEqual(returned, [None])
        actual = simulator._kinematics(F(2), simulator.state)
        simulator._invalidate()
        self.assertEqual(actual, simulator._kinematics(F(2), simulator.state))

    def test_incoming_node_types_and_complete_map_are_rechecked(self):
        for change in ("position_boolean", "rate_boolean", "quaternion_shape", "foreign_ops", "missing"):
            with self.subTest(change=change):
                simulator = prepared("P01")
                simulator.advance(F(2), "before")
                original = simulator._validate_staged
                terminal = simulator._terminal_static_kinematics
                returned = []

                def validate(*args):
                    frames = simulator._terminal_pose_context.frames
                    value = frames["world"]
                    if change == "missing":
                        del frames["world"]
                    elif change == "position_boolean":
                        frames["world"] = replace(value, exact_position=(False, F(0), F(0)))
                    elif change == "rate_boolean":
                        frames["world"] = replace(value, exact_velocity=(False, F(0), F(0)))
                    elif change == "quaternion_shape":
                        frames["world"] = replace(value, rotation=RotationValue((F(1), F(0), F(0))))
                    else:
                        frames["world"] = replace(value, _ops=object())
                    return original(*args)

                def observed(*args):
                    result = terminal(*args)
                    returned.append(result)
                    return result

                with patch.object(simulator, "_validate_staged", side_effect=validate), \
                        patch.object(simulator, "_terminal_static_kinematics", side_effect=observed):
                    simulator.advance(F(2), "after")
                self.assertEqual(returned, [None])
                actual = simulator._kinematics(F(2), simulator.state)
                simulator._invalidate()
                self.assertEqual(actual, simulator._kinematics(F(2), simulator.state))


if __name__ == "__main__":
    unittest.main()
