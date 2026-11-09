"""Full file exchange through the FlowHMR adapter, fitting and core-0.1 replay."""

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from ontokin.evaluator import evaluate
from ontokin.syntax import parse
from ontokin.validator import validate
from tools.perception.observation import import_observation
from tools.perception.synthesis import synthesize


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.observation = self.root / "observation"
        self.output = self.root / "result"
        self.times = np.arange(20) / 10
        self.velocity = np.array([0.5, -0.25, 0.8])
        self.positions = [1.0, 2.0, -3.0] + self.times[:, None] * self.velocity

    def write(self):
        raw = self.root / "motion.npz"
        np.savez(raw, poses=np.zeros((20, 156)), trans=self.positions,
                 mocap_framerate=10, betas=np.zeros((1, 16)))
        return import_observation("flowhmr", raw, self.observation, source_kind="synthetic")

    def test_editable_action_and_speed_counterfactual(self):
        manifest = self.write()
        fit = synthesize(self.observation, self.output, start_frame=3, stop_frame=19)
        self.assertEqual(fit["source_sha256"], manifest["source"]["sha256"])
        self.assertEqual(fit["frames"], {"start": 3, "holdout_start": 15, "stop_exclusive": 19})
        np.testing.assert_allclose(fit["velocity_m_per_s"], self.velocity)
        self.assertLess(fit["held_out"]["max_position_error_m"], 1e-12)
        self.assertEqual(fit["held_out"]["frames"], 4)
        self.assertEqual((self.output / "root-motion.glb").read_bytes()[:4], b"glTF")
        for filename, pace in (("root-motion.ok", 1.0), ("faster.ok", 1.2)):
            program = (self.output / filename).read_text()
            scene = validate(parse(program), level="evaluated")
            at = evaluate(scene, ["1.25"])["samples"][0]["objects"]["root"]
            np.testing.assert_allclose(at["position_m"], self.positions[3] + 1.25 * pace * self.velocity)

    def test_heldout_deviation_refuses_without_writing(self):
        self.positions[-1, 2] += 0.1
        self.write()
        with self.assertRaisesRegex(ValueError, r"held-out maximum 0\.1 m"):
            synthesize(self.observation, self.output)
        self.assertFalse(self.output.exists())

    def test_stationary_track_and_invalid_windows(self):
        self.positions[:] = [0.0, 1.0, 2.0]
        self.write()
        for options in ({}, {"start_frame": 18}, {"start_frame": -1}, {"stop_frame": 21},
                        {"start_frame": 15, "stop_frame": 13}, {"max_error_m": float("nan")}):
            with self.subTest(options), self.assertRaises(ValueError):
                synthesize(self.observation, self.output, **options)
        self.assertFalse(self.output.exists())

    def test_refuses_unqualified_axes_and_existing_output(self):
        self.write()
        path = self.observation / "manifest.json"
        meta = json.loads(path.read_text())
        meta["observation"]["coordinate_system"] = "unknown"
        path.write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError, "world-space"):
            synthesize(self.observation, self.output)
        self.output.mkdir()
        with self.assertRaisesRegex(ValueError, "new synthesis output"):
            synthesize(self.observation, self.output)
        self.assertEqual(list(self.output.iterdir()), [])
