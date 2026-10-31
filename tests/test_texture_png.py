"""Frozen independent PNG byte/pixel expectations and bounded admission work."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.surface import SurfaceError
from ontokin.texture_png import validate_png


FIXTURES = Path(__file__).resolve().parents[1] / "examples/textured-surfaces"
IMAGES = json.loads((FIXTURES / "expected.json").read_text())["images"]


class TexturePngTests(unittest.TestCase):
    def test_independently_frozen_complete_png_cohort(self):
        for name, expected in IMAGES.items():
            with self.subTest(image=name):
                raw = (FIXTURES / expected["path"]).read_bytes()
                if not expected["expected_png_valid"]:
                    with self.assertRaises(SurfaceError) as rejected:
                        validate_png(raw)
                    self.assertEqual(rejected.exception.code, "OKL-E-PNG")
                    continue
                info = validate_png(raw)
                self.assertEqual((info.width, info.height, info.channels),
                                 (expected["width"], expected["height"], expected["channels"]))
                self.assertEqual(info.decoded_bytes, expected["decoded_bytes"])
                self.assertEqual(info.pixel_sha256, expected["decoded_sha256"])

    def test_work_counts_original_blocks_chunks_rows_and_channel_bytes(self):
        raw = (FIXTURES / IMAGES["asymmetric-rgb"]["path"]).read_bytes()
        charges, checks = [], []
        validate_png(raw, charge=charges.append, check=lambda: checks.append(True))
        # Frozen PNG: 89 encoded bytes, 3 chunks, 3 rows, 4*3*3 samples.
        self.assertEqual(sum(charges), 2 + 3 + 3 + 36)
        self.assertTrue(all(type(amount) is int and amount > 0 for amount in charges))
        self.assertGreaterEqual(len(checks), 8)

    def test_no_decompression_before_encoded_work_authorization(self):
        raw = (FIXTURES / IMAGES["maximum-rgba"]["path"]).read_bytes()
        failure = RuntimeError("current caller cancelled")

        def refuse(_amount):
            raise failure

        with patch("ontokin.texture_png.zlib.decompressobj") as decoder:
            with self.assertRaises(RuntimeError) as rejected:
                validate_png(raw, charge=refuse)
        self.assertIs(rejected.exception, failure)
        decoder.assert_not_called()

    def test_cancellation_reaches_reconstruction_and_is_not_png_failure(self):
        raw = (FIXTURES / IMAGES["maximum-rgba"]["path"]).read_bytes()
        failure = RuntimeError("cancel reconstructed pixels")
        consumed = 0

        def charge(amount):
            nonlocal consumed
            consumed += amount
            if consumed >= 4096:
                raise failure

        with self.assertRaises(RuntimeError) as rejected:
            validate_png(raw, charge=charge)
        self.assertIs(rejected.exception, failure)
        self.assertLess(consumed, 4500)

    def test_no_pixel_validity_cache_hides_fresh_current_work(self):
        raw = (FIXTURES / IMAGES["asymmetric-rgb"]["path"]).read_bytes()
        first, second = [], []
        self.assertEqual(validate_png(raw, charge=first.append),
                         validate_png(raw, charge=second.append))
        self.assertEqual(first, second)
        self.assertEqual(sum(second), 44)


if __name__ == "__main__":
    unittest.main()
