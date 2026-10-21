"""A constant source law remains constant while its action is running."""
from fractions import Fraction as F
import unittest

from ontokin.reach_numeric import ReachAdmissionError
from test_reach_recording_sampler import simulator


class ReachRecordingStationarityTests(unittest.TestCase):
    def test_zero_reach_coordinate_is_constant_for_the_complete_phase(self):
        sim = simulator('P01')
        sim.advance(F(0), 'after')
        sim.phase_bounds(F(0), F(2))
        paths = tuple(path + '.frame' for path in sim.model.objects)
        moving = sim.recording_moving_frames(sim.state, paths)
        self.assertNotIn('rig.arm.upper.frame', moving)
        self.assertIn('rig.arm.forearm.frame', moving)
        snapshots = [sim.recording_frames(t, sim.state, paths)
                     for t in (F(0), F(1, 7), F(1), F(2))]
        for path in paths:
            if path not in moving:
                self.assertTrue(all(row[path] == snapshots[0][path] for row in snapshots))
        self.assertNotEqual(snapshots[0]['rig.arm.forearm.frame'],
                            snapshots[-1]['rig.arm.forearm.frame'])

    def test_new_law_and_inherited_motion_are_not_mistaken_for_stationarity(self):
        sim = simulator('P05')
        sim.advance(F(0), 'after')
        paths = tuple(path + '.frame' for path in sim.model.objects)
        self.assertEqual(sim.recording_moving_frames(sim.state, paths), frozenset(paths))
        sim = simulator('L01')
        sim.advance(F(0), 'after')
        initial = sim.recording_moving_frames(sim.state, ('rig.arm.upper.frame',))
        sim.advance(F(1, 2), 'after')
        paused = sim.recording_moving_frames(sim.state, ('rig.arm.upper.frame',))
        sim.advance(F(3, 2), 'after')
        resumed = sim.recording_moving_frames(sim.state, ('rig.arm.upper.frame',))
        self.assertIn('rig.arm.upper.frame', initial)
        self.assertFalse(paused)
        self.assertEqual(resumed, initial)

    def test_boolean_equal_endpoint_is_rejected_before_constant_classification(self):
        sim = simulator('P01')
        sim.advance(F(0), 'after')
        claimant = next(path for path, action in sim.model.actions.items() if action.kind == 'reach_planar')
        runtime = sim.state.actions[claimant]
        runtime.initial = (False, runtime.initial[1])
        with self.assertRaises(ReachAdmissionError):
            sim.recording_moving_frames(sim.state, ('rig.arm.upper.frame',))


if __name__ == '__main__':
    unittest.main()
