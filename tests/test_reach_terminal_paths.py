"""Selected terminal dependencies preserve actual poses and boundary rollback."""
import copy
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_runtime import ReachSimulator

DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"


class ReachTerminalPathTests(unittest.TestCase):
    def test_terminal_pose_reuse_keeps_incoming_rates_and_fresh_outgoing_rates(self):
        built = compile_construction(load_file_manifest(DATA / "p01.files.json"))
        simulator = ReachSimulator(built.model, work=built.reach_work)
        simulator.advance(F(2), "before")
        action = built.model.actions["reach"]
        child = built.model.sites[built.model.joints[action.reach.elbow].child].owner
        incoming = simulator._kinematics(F(2), simulator.state)[0][child]
        terminal_pose = simulator._tip_base(action, F(2), simulator.state)
        self.assertNotEqual(incoming.omega, (0.0, 0.0, 0.0))
        simulator.advance(F(2), "after")
        outgoing = simulator._kinematics(F(2), simulator.state)
        self.assertEqual(outgoing[0][child].omega, (0.0, 0.0, 0.0))
        self.assertEqual(simulator.state.actions["reach"].terminal["tip_pose_base"],
                         simulator._pose_record(terminal_pose))
        self.assertIsNone(simulator._terminal_pose_context)
        simulator._invalidate()
        rebuilt = simulator._kinematics(F(2), simulator.state)
        self.assertEqual(outgoing, rebuilt)

    def test_clock_independent_graph_reuse_requires_no_dynamic_body_or_motion_claim(self):
        for case, stationary in (("p01", True), ("p16", False)):
            with self.subTest(case=case):
                built = compile_construction(load_file_manifest(DATA / (case + ".files.json")))
                simulator = ReachSimulator(built.model, work=built.reach_work)
                simulator.advance(F(2), "after")
                objects, frames = simulator._kinematics(F(2), simulator.state)
                later_objects, later_frames = simulator._kinematics(F(3), simulator.state)
                self.assertEqual(not simulator.state.dynamic and not simulator.state.claims, stationary)
                if stationary:
                    self.assertIs(later_objects, objects)
                    self.assertIs(later_frames, frames)
                else:
                    self.assertIsNot(later_objects, objects)
                    self.assertIsNot(later_frames, frames)

        built = compile_construction(load_file_manifest(DATA / "p01.files.json"))
        simulator = ReachSimulator(built.model, work=built.reach_work)
        simulator.advance(F(1, 2), "after")
        first = simulator._kinematics(F(1, 2), simulator.state)
        later = simulator._kinematics(F(1), simulator.state)
        self.assertTrue(simulator.state.claims)
        self.assertIsNot(first[0], later[0])
        tip_frame = built.model.actions["reach"].reach.tip + ".frame"
        self.assertNotEqual(first[1][tip_frame].position, later[1][tip_frame].position)

    def test_selected_terminal_pose_matches_complete_graph_without_poisoning_its_cache(self):
        for case in ("p01", "p11", "p16"):
            with self.subTest(case=case):
                built = compile_construction(load_file_manifest(DATA / (case + ".files.json")))
                simulator = ReachSimulator(built.model, work=built.reach_work)
                simulator.advance(F(1, 2), "after")
                action = built.model.actions["reach"]
                complete = simulator._tip_base(action, F(1, 2), simulator.state)
                expected = (complete.position, complete.orientation, complete.position_error_m,
                            complete.angular_error_rad)
                simulator._invalidate()
                selected = simulator._tip_base(action, F(1, 2), simulator.state, terminal=True)
                self.assertEqual((selected.position, selected.orientation, selected.position_error_m,
                                  selected.angular_error_rad), expected)
                self.assertEqual(simulator._pose_cache, {})
                objects, frames = simulator._kinematics(F(1, 2), simulator.state)
                self.assertEqual(set(objects), set(built.model.objects))
                self.assertEqual(set(frames), {"world"} | {path + ".frame" for path in built.model.objects}
                                 | {path + ".frame" for path in built.model.sites})

    def test_failure_after_complete_staged_validation_keeps_incoming_state_and_release(self):
        built = compile_construction(load_file_manifest(DATA / "p16.files.json"))
        simulator = ReachSimulator(built.model, work=built.reach_work)
        before = simulator.advance(F(2), "before")
        state, event_index = copy.deepcopy(simulator.state), simulator.event_index
        marker = RuntimeError("reject fully validated staged boundary")
        original = simulator._validate_staged
        def fail_after_validation(*args):
            original(*args)
            raise marker
        with patch.object(simulator, "_validate_staged", side_effect=fail_after_validation):
            with self.assertRaises(RuntimeError) as caught:
                simulator.advance(F(2), "after")
        self.assertIs(caught.exception, marker)
        self.assertIsNone(simulator._terminal_pose_context)
        self.assertEqual(simulator.state, state)
        self.assertEqual(simulator.event_index, event_index)
        self.assertEqual(simulator.incoming_releases_at(F(2)), [])
        self.assertEqual(simulator.snapshot(F(2), "before"), before)


if __name__ == "__main__":
    unittest.main()
