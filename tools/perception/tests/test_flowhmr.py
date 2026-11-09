import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools.perception.flowhmr import adapt


class FlowHMRTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "motion.npz"
        pose = np.arange(312, dtype=np.float32).reshape(2, 52, 3) / 100
        self.fields = {
            "poses": pose,
            "trans": np.array([[1, 2, 3], [-2, 3, 4]], dtype=np.float32),
            "betas": np.zeros((1, 16), dtype=np.float32),
            "mocap_framerate": 30, "num_frames": 2, "gender": "neutral",
        }

    def read(self, **fields):
        np.savez(self.path, **(self.fields | fields))
        return adapt(self.path)

    def test_current_export_with_optional_signals(self):
        scores = np.array([[0.12, 0.4, 0.3, 1.04], [0.8, -0.03, 0.8, 0.5]])
        pelvis = np.ones((2, 3))
        meta, arrays = self.read(Rh=self.fields["poses"][:, 0], pelvis_world=pelvis, foot_contacts=scores)
        self.assertEqual(meta["sample_count"], 2)
        self.assertEqual(meta["units"], "m")
        self.assertEqual(meta["fps"], 30)
        np.testing.assert_array_equal(arrays["timestamps_s"], [0, 1 / 30])
        np.testing.assert_array_equal(arrays["root_translation"], self.fields["trans"])
        np.testing.assert_array_equal(arrays["joint_rotvec"], self.fields["poses"])
        np.testing.assert_array_equal(arrays["foot_contact_scores"], scores)
        np.testing.assert_array_equal(arrays["internal_pelvis_world"], pelvis)
        self.assertIn("internal_frame", meta)

    def test_published_demo_layout(self):
        meta, arrays = self.read(poses=self.fields["poses"].reshape(2, 156))
        np.testing.assert_array_equal(arrays["joint_rotvec"], self.fields["poses"])
        self.assertNotIn("foot_contact_scores", arrays)
        self.assertNotIn("internal_frame", meta)

    def test_missing_or_conflicting_timebase(self):
        np.savez(self.path, **self.fields)
        with self.assertRaisesRegex(ValueError, "conflicts"):
            adapt(self.path, fps=60)
        del self.fields["mocap_framerate"]
        with self.assertRaisesRegex(ValueError, "frame rate"):
            self.read()
        meta, arrays = adapt(self.path, fps=25)
        self.assertEqual(meta["fps"], 25)
        np.testing.assert_array_equal(arrays["timestamps_s"], [0, 0.04])

    def test_reject_bad_motion(self):
        for key, value in [
            ("num_frames", 1), ("num_frames", 2.5), ("mocap_framerate", 0),
            ("poses", np.zeros((2, 72))), ("betas", np.zeros(16)),
            ("trans", np.full((2, 3), np.nan)), ("trans", np.empty((0, 3))),
            ("Rh", np.zeros((2, 3))), ("foot_contacts", np.ones((3, 4))),
            ("local_joints_positions", np.ones((2, 22, 3))),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.read(**{key: value})
