import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from tools.perception.articulation import articulate
from tools.perception.observation import import_observation


class KneeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.pose = np.zeros((25, 52, 3))
        self.pose[:, 4, 0] = np.linspace(0.1, 1.3, 25)

    def observe(self):
        source = self.root / "human.npz"
        np.savez(source, trans=np.zeros((25, 3)), poses=self.pose, betas=np.zeros((1, 16)), mocap_framerate=24)
        result = self.root / "observed"
        import_observation("flowhmr", source, result, source_kind="synthetic")
        return result

    def test_linear_hinge_and_amplitude(self):
        self.pose[10:, 4, 0] -= 2*np.pi  # Same rotations across a representation seam
        out = self.root / "output"
        result = articulate(self.observe(), out, max_error_deg=0.01, max_phases=1)
        self.assertEqual(result["phases"], 1)
        self.assertLess(result["held_out"]["max_error_deg"], 0.001)
        self.assertLess(result["counterfactual"]["max_error_deg"], 0.001)
        self.assertFalse(set(result["knot_frames"]) & set(result["held_out_frames"]))
        self.assertEqual((out / "knee.glb").read_bytes()[:4], b"glTF")
        self.assertIn("validation", json.loads((out / "export.json").read_bytes()))

    def test_heldout_orientation_is_independent(self):
        self.pose[3, 4] = [0., 0.85, 0.]
        with self.assertRaisesRegex(ValueError, "held-out maximum"):
            articulate(self.observe(), self.root / "output", max_error_deg=2)
        self.assertFalse((self.root / "output").exists())

    def test_refuses_stationary_and_invalid_budget(self):
        obs = self.observe()
        with self.assertRaisesRegex(ValueError, "stationary"):
            articulate(obs, self.root / "output", joint="right_knee")
        with self.assertRaisesRegex(ValueError, "phase limit"):
            articulate(obs, self.root / "output", max_phases=33)
