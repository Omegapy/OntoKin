import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.perception.ballistic import fit_ballistic
from tools.perception.observation import import_observation


class BallisticTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.t = np.linspace(0, 1.8, 20)
        self.velocity = np.array([0.7, 3.2, -0.25])
        self.line = np.array([2., 8., -4.]) + self.t[:, None] * self.velocity
        self.track = self.line.copy()
        self.track[:, 1] -= 4.1 * self.t ** 2

    def save(self, positions, frame="right_handed_y_up"):
        path = self.root / "capture.npz"
        np.savez(path, position_m=positions, timestamps_s=self.t + 79, coordinate_system=frame)
        observation = self.root / "observation"
        import_observation("metric-track", path, observation, source_kind="synthetic")
        return observation

    def test_recovers_gravity_in_existing_simulator(self):
        output = self.root / "action"
        fit = fit_ballistic(self.save(self.track), output)
        self.assertAlmostEqual(fit["gravity_y_m_per_s2"], -8.2)
        np.testing.assert_allclose(fit["initial_velocity_m_per_s"], self.velocity)
        self.assertEqual(fit["held_out"]["frames"], 5)
        self.assertLess(fit["held_out"]["max_position_error_m"], 1e-10)
        self.assertLess(fit["counterfactual"]["max_position_change_error_m"], 1e-10)
        self.assertTrue((output / "ballistic.glb").is_file())

    def test_refuses_changed_future(self):
        self.track[-1, 0] += 0.2
        with self.assertRaisesRegex(ValueError, "held-out maximum"):
            fit_ballistic(self.save(self.track), self.root / "action")
        self.assertFalse((self.root / "action").exists())

    def test_refuses_unidentified_gravity(self):
        with self.assertRaisesRegex(ValueError, "Constant velocity"):
            fit_ballistic(self.save(self.line), self.root / "action")

    def test_refuses_unqualified_frame(self):
        with self.assertRaisesRegex(ValueError, "right_handed_y_up"):
            self.save(self.track, "uncalibrated")
