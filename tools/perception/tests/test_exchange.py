import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

import numpy as np

from tools.perception.geometry import inspect_point
from tools.perception.observation import import_observation, load_observation, read_arrays


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "solve.npz"
        self.output = self.root / "observation"
        cameras = np.tile(np.eye(4), (2, 1, 1))
        cameras[1, 0, 3] = 1
        depth = np.full((2, 3, 5), 2.0, dtype="f2")
        depth[1, 1, 1] = 2.125
        k = np.array([[2., 0, 2], [0, 3, 1], [0, 0, 1]])
        np.savez(self.source, c2w=cameras, K=np.tile(k, (2, 1, 1)), depth=depth, depth_conf=np.ones_like(depth))

    def test_point_cross_view_and_digest(self):
        manifest = import_observation("solv3r", self.source, self.output, source_kind="synthetic")
        self.assertEqual(manifest["source"]["sha256"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(load_observation(self.output)[0], manifest)
        point = inspect_point(self.output, 0, 2, 1, target_view=1)
        self.assertEqual(point["world_xyz"], [0., 0., -2.])
        self.assertEqual(point["projection"]["nearest_pixel_uv"], [1, 1])
        self.assertEqual(point["projection"]["observed_minus_predicted_depth"], 0.125)
        with self.assertRaisesRegex(ValueError, "outside"):
            inspect_point(self.output, 0, -1, 0)

    def test_preserve_existing_and_refuse_corruption(self):
        import_observation("solv3r", self.source, self.output)
        with self.assertRaisesRegex(ValueError, "new output"):
            import_observation("solv3r", self.source, self.output)
        with (self.output / "arrays.npz").open("ab") as file:
            file.write(b"damage")
        with self.assertRaisesRegex(ValueError, "digest"):
            load_observation(self.output)

    def test_refuse_wrong_inventory(self):
        import_observation("solv3r", self.source, self.output)
        path = self.output / "manifest.json"
        manifest = json.loads(path.read_bytes())
        del manifest["arrays"]["depth_valid"]
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "inventory"):
            load_observation(self.output)

    def test_refuse_forged_size_before_allocation(self):
        header = io.BytesIO()
        np.lib.format.write_array_header_1_0(header, dict(descr="<f8", shape=(100_000_000,), fortran_order=False))
        with ZipFile(self.source, "w") as file:
            file.writestr("depth.npy", header.getvalue())
        with self.assertRaisesRegex(ValueError, "length"):
            read_arrays(self.source, ("depth",))

    def test_refuse_object_data_and_incomplete_export(self):
        np.savez(self.source, depth=np.array([object()]))
        with self.assertRaisesRegex(ValueError, "dtype"):
            read_arrays(self.source, ("depth",))
        with self.assertRaisesRegex(ValueError, "Missing"):
            import_observation("solv3r", self.source, self.output)
        self.assertFalse(self.output.exists())
