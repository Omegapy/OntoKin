"""Exercise the two action commands on synthetic data without claiming a video capture."""
import csv
import json
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from tools.perception.observation import import_observation

EVALUATOR = runpy.run_path(str(Path(__file__).with_name("evaluate-stretch.py")))


class EvaluationControls(unittest.TestCase):
    def run_control(self, n, angular_speed):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        poses = np.zeros((n, 52, 3))
        times = np.arange(n) / 30
        poses[:, 4, 0] = angular_speed * times
        raw, observation = base / "synthetic.npz", base / "observation"
        np.savez(raw, trans=np.column_stack((times, times * 0, times * 0)),
                 poses=poses, betas=np.zeros((1, 16)), mocap_framerate=30)
        import_observation("flowhmr", raw, observation, source_kind="synthetic")
        out = base / "evaluation"
        out.mkdir()
        sources = EVALUATOR["read_frame_map"](11, 10 + n)
        result = EVALUATOR["evaluate_actions"](observation, out, 11, sources)
        self.assertEqual(result["status"], "fits_evaluated")
        with (out / "fit-frame-map.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([int(row["analysis_frame_30hz"]) for row in rows], list(range(11, 11 + n)))
        self.assertEqual([int(row["source_frame_25hz"]) for row in rows], sources)
        return result["actions"], out, rows

    def test_both_fits_and_held_groups(self):
        fits, out, rows = self.run_control(36, 1.)
        self.assertEqual([v["exit_code"] for v in fits.values()], [0, 0])
        self.assertEqual(fits["root"]["counterfactual"]["pace"], 1.2)
        self.assertEqual(fits["knee"]["counterfactual"]["amplitude"], 0.8)
        self.assertEqual(sum(r["root_split"] == "held" for r in rows), 8)
        groups = json.loads((out / "knee-source-groups.json").read_text())
        self.assertEqual(groups["all_held"]["frames"], 8)
        self.assertGreater(groups["source_repeated_in_fit"]["frames"], 0)
        self.assertGreater(groups["source_disjoint"]["frames"], 0)

    def test_short_track_still_runs_knee(self):
        fits, _, rows = self.run_control(24, 1.)
        self.assertEqual([v["exit_code"] for v in fits.values()], [1, 0])
        self.assertIn("valid half-open frame range", fits["root"]["reason"])
        self.assertTrue(all(r["root_split"] == "outside" for r in rows))

    def test_preexisting_output_is_an_execution_error(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            # The fitters check the existing output directories before loading a fixture.
            for name in ("root-action", "knee-action"):
                (out / name).mkdir()
            result = EVALUATOR["evaluate_actions"](out / "absent-observation", out, 0, [])
            self.assertEqual(result["status"], "execution_error")
            self.assertEqual([v["outcome"] for v in result["actions"].values()],
                             ["execution_error", "execution_error"])

    def test_stationary_knee_preserves_root(self):
        fits, out, _ = self.run_control(36, 0.)
        self.assertEqual([v["exit_code"] for v in fits.values()], [0, 1])
        self.assertIn("stationary knee", fits["knee"]["reason"])
        self.assertFalse((out / "knee-source-groups.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
