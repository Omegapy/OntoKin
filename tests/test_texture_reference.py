"""Independent reader controls; no OntoKin product import or generated oracle."""
from fractions import Fraction
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.texture_reference import (GLB, ReferenceError, decode_png, exact_uv,
    loads, ordinary_path, repack_glb)


class TextureReferenceTests(unittest.TestCase):
    def png(self, name):
        return (ROOT / "examples/textured-surfaces/assets" / (name + ".png")).read_bytes()

    def test_all_filter_predictors_reconstruct_the_independent_literal_pixels(self):
        expected = bytes([
            255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 0,
            0, 255, 255, 255, 0, 255, 128, 128, 128, 10, 11, 12,
            255, 255, 255, 0, 0, 0, 40, 80, 160, 255, 128, 0])
        for method in range(5):
            with self.subTest(method=method):
                result = decode_png(self.png("filter-" + str(method)))
                self.assertEqual(result["pixels"], expected)
                self.assertEqual(result["row_filters"], [method] * 3)

    def test_complete_one_stream_crc_and_opaque_admission_are_distinct_guards(self):
        for name in ("bad-zlib-checksum", "second-zlib-stream", "decoded-one-extra",
                     "decoded-one-short", "trailing-png-byte", "nonopaque-alpha", "idat-65"):
            with self.subTest(name=name):
                with self.assertRaises(ReferenceError) as caught:
                    decode_png(self.png(name))
                self.assertEqual(caught.exception.code, "OKL-E-PNG")

    def test_crc_damage_to_otherwise_valid_image_cannot_pass_decoder(self):
        raw = bytearray(self.png("asymmetric-rgb")); raw[32] ^= 1
        with self.assertRaisesRegex(ReferenceError, "CRC"):
            decode_png(bytes(raw))

    def test_exact_binary64_rational_affine_sum_is_not_intermediate_arithmetic(self):
        mapping = {"origin_m": [-.2, 0, 0], "u_per_m": [1, 0, 0],
                   "v_per_m": [0, 1, 0], "offset": [-.3, 0]}
        expected = Fraction.from_float(.1) - Fraction.from_float(-.2) + Fraction.from_float(-.3)
        self.assertEqual(expected, Fraction(1, 2 ** 55))
        value = exact_uv((.1, 0., .25), mapping)[0]
        self.assertEqual(value, 2 ** -55)
        self.assertNotEqual(value, (.1 - -.2) + -.3)
        self.assertEqual(struct.pack("<f", value), b"\0\0\0$")

    def test_json_duplicate_keys_nonfinite_literals_and_overflow_are_refused(self):
        for raw in (b'{"index":0,"index":1}', b'{"value":NaN}', b'{"value":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(ReferenceError):
                loads(raw)

    @staticmethod
    def supplied_accessor(raw=struct.pack("<2f", .125, .75), **overrides):
        accessor = {"bufferView": 0, "componentType": 5126, "count": 1, "type": "VEC2", **overrides}
        document = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(raw)}],
                    "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(raw)}],
                    "accessors": [accessor], "nodes": [],
                    "extras": {"ontokin": {"target_contract": "ontokin.glb/0.13",
                        "profile": "textured-surfaces-0.1", "schema_version": "0.13"}}}
        return GLB(repack_glb(document, raw))

    def test_reader_uses_actual_supplied_vec2_bytes(self):
        decoded = self.supplied_accessor()
        self.assertEqual(decoded.accessor(0), [(.125, .75)])
        self.assertEqual(decoded.accessor_bytes(0), struct.pack("<2f", .125, .75))

    def test_accessor_shape_boolean_references_and_nonfinite_bytes_are_refused(self):
        with self.assertRaises(ReferenceError):
            self.supplied_accessor().accessor(True)
        for changes in ({"count": 2}, {"normalized": True}, {"byteOffset": 2}, {"type": "VEC4"}):
            with self.subTest(changes=changes), self.assertRaises(ReferenceError):
                self.supplied_accessor(**changes).accessor(0)
        with self.assertRaisesRegex(ReferenceError, "Nonfinite"):
            self.supplied_accessor(struct.pack("<2f", float("nan"), .75)).accessor(0)

    def test_evidence_paths_cannot_escape_or_follow_a_final_symlink(self):
        with tempfile.TemporaryDirectory(prefix="c080-reference-") as directory:
            root = Path(directory); (root / "input.bin").write_bytes(b"frozen")
            (root / "link.bin").symlink_to("input.bin")
            self.assertEqual(ordinary_path(root, "input.bin").read_bytes(), b"frozen")
            for name in ("../input.bin", "link.bin", "/tmp/other", "./input.bin"):
                with self.subTest(name=name), self.assertRaises(ReferenceError):
                    ordinary_path(root, name)


if __name__ == "__main__":
    unittest.main()
