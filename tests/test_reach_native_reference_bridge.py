"""Verification bridge clocks must preserve the independent source clock."""
from fractions import Fraction
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from tools.build_reach_native_reference import extra_samples, observation_time


class ReachNativeReferenceBridgeTests(unittest.TestCase):
    def test_binary_destination_clock_does_not_replace_exact_source_boundary(self):
        sample = {"time_seconds": .1, "side": "after"}
        self.assertEqual(observation_time(sample), Fraction(.1))
        sample["source_time_seconds"] = "1/10"
        self.assertEqual(observation_time(sample), Fraction(1, 10))
        self.assertNotEqual(observation_time(sample), Fraction(.1))

    def test_invalid_observation_side_and_nonfinite_clock_are_rejected(self):
        for sample in ({"time_seconds": 0, "side": "during"},
                       {"time_seconds": float("nan"), "side": "after"},
                       {"time_seconds": -.1, "side": "after"},
                       {"time_seconds": 0, "source_time_seconds": .1, "side": "after"}):
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                observation_time(sample)

    def test_frozen_fixture_requires_its_actual_program_revision_and_prefix(self):
        root = Path(__file__).resolve().parents[1]
        corpus = json.loads((root / "docs/language-design/planar-reach-v0.1/acceptance.json").read_text())
        case = next(row for row in corpus["source_cases"] if row["id"] == "P01")
        reference = SimpleNamespace(end=Fraction(1, 4), boundaries=(Fraction(0), Fraction(1, 4)))
        with self.assertRaisesRegex(ValueError, "source revision differ"):
            extra_samples("P01", "sha256:" + "0" * 64, reference)
        samples, provenance, neighbors = extra_samples("P01", case["program_revision"], reference)
        self.assertGreater(provenance["fixed_samples_in_prefix"], 0)
        self.assertGreater(provenance["fixed_samples_outside_prefix"], 0)
        self.assertEqual(neighbors, 2)
        self.assertEqual([observation_time(row) for row in samples[-2:]],
                         [Fraction(1, 1000000), Fraction(1, 4) - Fraction(1, 1000000)])
        self.assertTrue(all(Fraction(0) <= observation_time(row) <= reference.end for row in samples))


if __name__ == "__main__":
    unittest.main()
