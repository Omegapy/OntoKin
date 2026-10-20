"""Controlled ordinary targets and explicit-frame inspection in source 0.6."""
from __future__ import annotations

from fractions import Fraction as Q
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.evaluator import evaluate_prefix, inspect_in_frame
from ontokin.reach_runtime import ReachSimulator


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"


class ReachObservationTests(unittest.TestCase):
    def test_ordinary_prefix_targets_use_controlled_arithmetic(self):
        built = compile_construction(load_file_manifest(DATA / "p16.files.json"))
        with patch("ontokin.evaluator._affine", side_effect=AssertionError("legacy affine target")), \
             patch("ontokin.evaluator._advance_orientation", side_effect=AssertionError("legacy spin target")):
            prefix = evaluate_prefix(built.model, Q(1, 4), work=built.reach_work)
        self.assertIsNone(prefix["failure"])
        actions = prefix["last_valid_state"]["actions"]
        self.assertEqual(tuple(actions["travel"]["target_value"]["value"]), (1.5, 0.0, 0.0))
        rotation = actions["turn"]["target_value"]["value"]
        self.assertAlmostEqual(rotation[0], math.cos(0.375), delta=2e-15)
        self.assertEqual(tuple(rotation[1:3]), (0.0, 0.0))
        self.assertAlmostEqual(rotation[3], math.sin(0.375), delta=2e-15)

    def test_nonworld_inspection_rotates_world_velocity_without_subtracting_carrier_motion(self):
        built = compile_construction(load_file_manifest(DATA / "p16.files.json"))
        sim = ReachSimulator(built.model, work=built.reach_work)
        sample = sim.advance(Q(1, 4), "after")
        value = inspect_in_frame(sample, "rig", "rig.frame", work=built.reach_work)
        self.assertEqual(value["position_m"], [0.0, 0.0, 0.0])
        self.assertEqual(value["orientation_wxyz"], [1.0, 0.0, 0.0, 0.0])
        self.assertAlmostEqual(value["velocity_m_per_s"][0], 0.5 * math.cos(0.0625), delta=2e-15)
        self.assertAlmostEqual(value["velocity_m_per_s"][1], -0.5 * math.sin(0.0625), delta=2e-15)
        self.assertEqual(value["angular_velocity_rad_per_s"], [0.0, 0.0, 0.25])
        self.assertEqual(value["velocity_measured_in"], "world")
        self.assertEqual(value["velocity_expressed_in"], "rig.frame")
        world = inspect_in_frame(sample, "rig", work=built.reach_work)
        for key in ("position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s"):
            self.assertEqual(world[key], sample["objects"]["rig"][key])


if __name__ == "__main__":
    unittest.main()
