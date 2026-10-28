"""Test fixture preconditions separately from source/Agent runtime acceptance."""
from __future__ import annotations

import copy
from fractions import Fraction as F
import unittest

from ontokin.bundle import load_bundle
from reach_fixture_support import source_unit_identity


class ReachEvidenceIdentityTests(unittest.TestCase):
    def setUp(self):
        # These transport-only inputs do not claim to be executable .ok scenes.
        self.program = load_bundle({
            "schema_version": "ontokin.bundle/0.1",
            "entry": {"filename": "entry.ok", "source": "// exact entry\n"},
            "modules": [{"package_id": "fixture." + name, "version": "0.1.0",
                         "filename": name + ".ok", "source": "// caf\u00e9 " + name + "\r\n"}
                        for name in ("parts", "exterior", "assets")],
        })
        self.rows = [{"source_id": unit.source_id, "source_revision": unit.revision,
                      "filename": unit.filename, "source": unit.text}
                     for unit in self.program.units]

    def test_entry_and_dependency_identities_match_the_immutable_manifest(self):
        actual = [source_unit_identity(self.program, row) for row in self.rows]
        self.assertEqual(actual, self.program.manifest()["units"])
        self.assertIsNone(actual[0]["package_id"])
        self.assertIsNone(actual[0]["version"])
        self.assertEqual([row["package_id"] for row in actual[1:]],
                         ["fixture.assets", "fixture.exterior", "fixture.parts"])

    def test_diagnostic_source_does_not_supply_package_metadata(self):
        source = self.program.sources[self.rows[1]["source_id"]]
        with self.assertRaises(AttributeError):
            _ = source.package_id
        with self.assertRaises(AttributeError):
            _ = source.version
        self.assertEqual(source_unit_identity(self.program, self.rows[1])["package_id"], "fixture.assets")

    def test_unknown_source_id_cannot_borrow_another_units_bytes(self):
        row = {**self.rows[1], "source_id": "package:fixture.unknown@0.1.0"}
        with self.assertRaisesRegex(AssertionError, "absent from the bundle"):
            source_unit_identity(self.program, row)

    def test_returned_revision_is_verified_independently_of_returned_bytes(self):
        row = {**self.rows[1], "source_revision": "sha256:" + "0" * 64}
        with self.assertRaisesRegex(AssertionError, "revision differs"):
            source_unit_identity(self.program, row)

    def test_returned_filename_cannot_relabel_correct_source_bytes(self):
        row = {**self.rows[1], "filename": "other.ok"}
        with self.assertRaisesRegex(AssertionError, "filename differs"):
            source_unit_identity(self.program, row)

    def test_line_endings_remain_exact(self):
        row = {**self.rows[1], "source": self.rows[1]["source"].replace("\r\n", "\n")}
        with self.assertRaisesRegex(AssertionError, "source bytes differ"):
            source_unit_identity(self.program, row)

    def test_unicode_normalization_is_not_silent_source_equivalence(self):
        row = {**self.rows[1], "source": self.rows[1]["source"].replace("\u00e9", "e\u0301")}
        with self.assertRaisesRegex(AssertionError, "source bytes differ"):
            source_unit_identity(self.program, row)

    def test_evidence_check_mutates_neither_source_nor_response(self):
        payload, revision = self.program.to_payload(), self.program.program_revision
        before = copy.deepcopy(self.rows)
        for row in self.rows:
            identity = source_unit_identity(self.program, row)
            identity["filename"] = "caller mutation"
        self.assertEqual(self.rows, before)
        self.assertEqual(self.program.to_payload(), payload)
        self.assertEqual(self.program.program_revision, revision)


class ReachHandoffFixtureTests(unittest.TestCase):
    # Binary64 targets for the positive branch at (0, 1) with unit links:
    # correctly rounded pi/6 and 2*pi/3. Explicit bits avoid computing pi/6
    # from an already rounded host pi constant. Admission remains tested by
    # the separate complete source/reference cohorts.
    TARGETS = (float.fromhex("0x1.0c152382d7366p-1"),
               float.fromhex("0x1.0c152382d7366p+1"))

    def test_original_three_second_variant_has_no_rounding_witness(self):
        for target in self.TARGETS:
            ideal = F(target) * F(1, 2) / 3
            self.assertEqual(F(float(ideal)), ideal)
            self.assertEqual(ideal.denominator & (ideal.denominator - 1), 0)

    def test_five_second_variant_has_exact_nonzero_errors_on_both_coordinates(self):
        errors = (-F(1, 360287970189639680), -F(1, 90071992547409920))
        for target, expected_error in zip(self.TARGETS, errors):
            ideal = F(target) * F(1, 2) / 5
            rounded = F(float(ideal))
            self.assertNotEqual(rounded, ideal)
            self.assertEqual(rounded - ideal, expected_error)
            self.assertEqual(ideal.denominator % 5, 0)

    def test_replacement_slopes_retain_the_ideal_and_actual_start_distinction(self):
        replacement = (float.fromhex("0x1.921fb54442d18p+0"),
                       -float.fromhex("0x1.921fb54442d18p+0"))
        for first_target, second_target in zip(self.TARGETS, replacement):
            ideal = F(first_target) / 10
            actual = F(float(ideal))
            ideal_slope, actual_slope = F(second_target) - ideal, F(second_target) - actual
            self.assertNotEqual(ideal_slope, actual_slope)
            self.assertEqual(ideal_slope - actual_slope, actual - ideal)
            self.assertEqual(ideal + ideal_slope, F(second_target))
            self.assertEqual(actual + actual_slope, F(second_target))


if __name__ == "__main__":
    unittest.main()
