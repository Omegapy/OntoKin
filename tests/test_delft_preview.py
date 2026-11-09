"""Check the display derivative against identifiable binary PLY vertices."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

from ontokin.external_gltf import preflight_splat_glb


SCRIPT = Path(__file__).resolve().parents[1] / "examples/splat-composite/delft_preview.py"
spec = importlib.util.spec_from_file_location("delft_preview", SCRIPT)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class DelftPreviewTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.source = Path(tmp.name) / "test.ply"
        self.output = Path(tmp.name) / "test.glb"
        header = ["ply", "format binary_little_endian 1.0", "element vertex 6"]
        header.extend("property float " + name for name in preview.FIELDS)
        blob = bytearray(("\n".join(header) + "\nend_header\n").encode("ascii"))
        for i in range(6):
            floats = [i, 0, -i, 0, 0, 0, i / 2, -1, 2, *([1.0] * 45),
                      math.log(3), math.log(2), 0, -math.log(2), 0, 0, 0, -4]
            blob.extend(struct.pack("<62f", *floats))
        self.source.write_bytes(blob)
        self.digest = hashlib.sha256(blob).hexdigest()

    def test_preserves_coordinates_and_converts_encoded_attributes(self):
        report = preview.convert(self.source, self.output, 2, [0.5, -1, -6, 4.5, 1, 0],
                                 expected_sha=self.digest)
        self.assertEqual(report["eligibleSplats"], 4)
        checked = preflight_splat_glb(self.output, report["glbSha256"])
        self.assertEqual(checked["scene_splat_count"], 2)
        blob = self.output.read_bytes()
        (size,) = struct.unpack_from("<I", blob, 12)
        doc = json.loads(blob[20:20+size])
        accessors = doc["accessors"]
        self.assertEqual([a["byteOffset"] for a in accessors], [0, 12, 28, 40, 44])
        self.assertEqual(doc["bufferViews"][0]["byteStride"], 56)
        self.assertEqual(doc["asset"]["extras"]["sourceSha256"], self.digest)
        for n, i in enumerate([2, 4]):
            actual = struct.unpack_from("<14f", blob, 28 + size + n * 56)
            for observed, expected in zip(actual, [i, 0, -i, 0, 0, -1, 0, 2, 1, 0.5, 0.75, i / 2, -1, 2]):
                self.assertAlmostEqual(observed, expected)
        self.assertEqual(preview.convert(self.source, self.output, 2, [0.5, -1, -6, 4.5, 1, 0],
                                         expected_sha=self.digest), report)

    def test_rejects_wrong_source_and_empty_crop(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            preview.convert(self.source, self.output)
        with self.assertRaisesRegex(ValueError, "no splats"):
            preview.convert(self.source, self.output, 1, [20, 20, 20, 21, 21, 21], expected_sha=self.digest)
        self.assertFalse(self.output.exists())
