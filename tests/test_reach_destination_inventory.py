"""Literal release inventory and honest actual-artifact intake boundaries."""
import copy
from fractions import Fraction
import math
from pathlib import Path
import tempfile
import unittest

from tools.reach_delivery_inventory import (ROOT, SOURCE_CASES, AGENT_CASES, SOURCE_BROWSER, AGENT_BROWSER,
    checked_member, check_settings, descriptor, endpoint, frozen_cases, relative_name,
    selected_cases, settings, source_files)
from tools.verify_reach_destinations import producer_rows, source_kind


class ReachDestinationInventoryTests(unittest.TestCase):
    def test_literal_full_corpora_and_browser_subsets(self):
        self.assertEqual(set(SOURCE_CASES), {f"P{n:02d}" for n in range(1, 24)} |
                         {"P25", "P26", "L01", "L02", "L03"})
        self.assertEqual(len(SOURCE_CASES), 28)
        self.assertEqual(set(AGENT_CASES), {"P01", "P11", "P13", "P20", "P16", "P17", "L01", "L02", "L03", "L04"})
        self.assertEqual(len(AGENT_CASES), 10)
        self.assertEqual(set(SOURCE_BROWSER), {"P01", "P11", "P20", "P16", "P18", "P19", "L01", "L02", "L03"})
        self.assertEqual(set(AGENT_BROWSER), set(AGENT_CASES) - {"L04"})

    def test_every_required_artifact_has_unchanged_frozen_source_and_explicit_horizon(self):
        frozen = frozen_cases()
        for case_id in set(SOURCE_CASES) | set(AGENT_CASES):
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, frozen)
                self.assertTrue((ROOT / source_files(case_id)).is_file())
                self.assertEqual(check_settings(case_id, settings(case_id)), settings(case_id))
        for case_id, expected in {"P14": 4, "P16": 4, "P17": 2, "P26": 60,
                                  "L01": 4, "L02": 2, "L03": 4, "L04": Fraction(1, 4)}.items():
            self.assertEqual(Fraction(endpoint(case_id)), expected)

    def test_truncated_or_failed_horizons_and_weaker_tolerances_cannot_enter_the_corpus(self):
        for case_id, wrong_end in (("P01", "0.25"), ("P17", "4"), ("L04", "2")):
            with self.subTest(case_id=case_id), self.assertRaises(ValueError):
                check_settings(case_id, {**settings(case_id), "end": wrong_end})
        for name in ("position_tolerance_m", "rotation_tolerance_rad", "time_tolerance_s"):
            wrong = settings("P01")
            wrong[name] = math.nextafter(wrong[name], math.inf)
            with self.subTest(tolerance=name), self.assertRaises(ValueError):
                check_settings("P01", wrong)
        tighter = {**settings("P01"), "position_tolerance_m": .0001}
        self.assertEqual(check_settings("P01", tighter)["position_tolerance_m"], .0001)
        with self.assertRaises(ValueError):
            check_settings("P01", {**settings("P01"), "helpers": True})
        missing_fps = settings("P01")
        del missing_fps["fps"]
        with self.assertRaises(ValueError):
            check_settings("P01", missing_fps)

    def test_case_filter_is_explicit_and_cannot_hide_duplicates_or_add_unpromised_glbs(self):
        self.assertEqual(selected_cases("source_component", []), SOURCE_CASES)
        self.assertEqual(selected_cases("agent_retrieved_artifact", ["L04"]), ("L04",))
        for kind, selected in (("source_component", ["P24"]), ("source_component", ["L04"]),
                               ("source_component", ["P01", "P01"]), ("agent_retrieved_artifact", ["P18"])):
            with self.subTest(kind=kind, selected=selected), self.assertRaises(ValueError):
                selected_cases(kind, selected)

    def test_normalized_member_paths_and_hashes_are_required(self):
        for name in ("/absolute", "../escape", "./file", "dir//file", "dir/../file", ".", "", "dir\\file"):
            with self.subTest(path=name), self.assertRaises(ValueError):
                relative_name(name)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = root / "scene.glb"
            member.write_bytes(b"actual supplied bytes")
            record = descriptor(member, relative_to=root)
            self.assertEqual(checked_member(root, record), member)
            member.write_bytes(b"changed bytes")
            with self.assertRaises(ValueError):
                checked_member(root, record)
            linked = root / "alias.glb"
            linked.symlink_to(member)
            with self.assertRaises(ValueError):
                checked_member(root, {**record, "path": "alias.glb"})

    def test_agent_intake_requires_actual_identities_and_fixed_source_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "retrieved.glb"
            artifact.write_bytes(b"intake fixture only; the separate native parser validates GLB bytes")
            row = {"case_id": "L04", "source_files": source_files("L04"),
                   "program_revision": frozen_cases()["L04"]["program_revision"],
                   "options": settings("L04"), "project_id": "project", "run_id": "fresh-run", "artifact_id": "artifact",
                   "artifact": descriptor(artifact, relative_to=root)}
            producer = {"schema_version": "ontokin.reach-agent-delivery-workflow/0.1", "deliveries": [row]}
            kind = source_kind(producer)
            self.assertEqual(producer_rows(producer, kind, ("L04",), root)[0][2], artifact)
            for key in ("project_id", "run_id", "artifact_id"):
                changed = copy.deepcopy(producer)
                del changed["deliveries"][0][key]
                with self.subTest(missing=key), self.assertRaises(ValueError):
                    producer_rows(changed, kind, ("L04",), root)
            changed = copy.deepcopy(producer)
            changed["deliveries"][0]["program_revision"] = "sha256:" + "0" * 64
            with self.assertRaises(ValueError):
                producer_rows(changed, kind, ("L04",), root)


if __name__ == "__main__":
    unittest.main()
