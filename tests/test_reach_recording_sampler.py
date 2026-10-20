"""Recording samples preserve actual p/q without publishing fictitious rates."""
from __future__ import annotations

from fractions import Fraction as Q
from pathlib import Path
import unittest

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_runtime import ReachSimulator


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"
SUPPLEMENT = DATA / "draft2-supplements"


def simulator(case):
    root = SUPPLEMENT if case.startswith("L") else DATA
    built = compile_construction(load_file_manifest(root / (case.lower() + ".files.json")))
    return ReachSimulator(built.model, work=built.reach_work)


class ReachRecordingSamplerTests(unittest.TestCase):
    def assert_same_poses(self, sim, time, paths):
        # Both paths use the same already prepared whole-phase reduction plan.
        sim._invalidate()
        recorded = sim.recording_frames(time, sim.state, paths)
        _, complete = sim._kinematics(time, sim.state)
        self.assertEqual(set(recorded), set(paths))
        for path in paths:
            self.assertEqual(recorded[path].position, complete[path].position, path)
            self.assertEqual(recorded[path].orientation, complete[path].orientation, path)
            self.assertFalse(hasattr(recorded[path], "velocity"))
            self.assertFalse(hasattr(recorded[path], "omega"))
        return complete

    def test_moving_carrier_and_reach_match_complete_pose_without_losing_rates(self):
        sim = simulator("P16")
        sim.advance(Q(0), "after")
        sim.phase_bounds(Q(0), Q(2))
        complete = self.assert_same_poses(sim, Q(1, 3),
            ("rig.frame", "rig.arm.upper.frame", "rig.arm.forearm.tip.frame", "payload.frame"))
        self.assertTrue(any(complete["payload.frame"].velocity))
        self.assertTrue(any(complete["payload.frame"].omega))

    def test_new_owner_replaces_partial_cache_inputs(self):
        sim = simulator("L02")
        sim.advance(Q(0), "after")
        sim.phase_bounds(Q(0), Q(1, 2))
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame")
        first = self.assert_same_poses(sim, Q(1, 4), paths)
        first_pose = first[paths[-1]].position
        sim.advance(Q(1, 2), "after")
        sim.phase_bounds(Q(1, 2), Q(3, 2))
        second = self.assert_same_poses(sim, Q(3, 4), paths)
        self.assertNotEqual(first_pose, second[paths[-1]].position)
        self.assertTrue(any(second[paths[-1]].omega))

    def test_released_anchor_and_dynamic_samples_preserve_canonical_pose(self):
        sim = simulator("P16")
        sim.advance(Q(2), "after")
        anchor = sim.state.dynamic["payload"].state
        anchor_pose = (anchor.position, anchor.orientation)
        sim.phase_bounds(Q(2), Q(3))
        at_anchor = sim.recording_frames(Q(2), sim.state, ["payload.frame"])["payload.frame"]
        self.assertEqual((at_anchor.position, at_anchor.orientation), anchor_pose)
        complete = self.assert_same_poses(sim, Q(9, 4), ("payload.frame",))
        self.assertTrue(any(complete["payload.frame"].velocity))
        self.assertEqual((anchor.position, anchor.orientation), anchor_pose)

    def test_pose_only_default_carriers_execute_less_actual_work(self):
        costs, poses = {}, {}
        for mode in ("complete", "recording"):
            sim = simulator("P01")
            sim.advance(Q(0), "after")
            sim.phase_bounds(Q(0), Q(2))
            paths = tuple(path + ".frame" for path in sim.model.objects)
            baseline = sim.work.operations
            if mode == "recording":
                frames = sim.recording_frames(Q(1, 3), sim.state, paths)
            else:
                _, frames = sim._kinematics(Q(1, 3), sim.state)
            poses[mode] = {path: (frames[path].position, frames[path].orientation) for path in paths}
            costs[mode] = sim.work.operations - baseline
        self.assertEqual(poses["recording"], poses["complete"])
        self.assertLess(costs["recording"], costs["complete"])


if __name__ == "__main__":
    unittest.main()
