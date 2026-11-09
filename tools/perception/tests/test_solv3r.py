"""Writer-shaped Solv3R fixtures, with geometry checked independently in source axes."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from tools.perception.geometry import inspect_point
from tools.perception.observation import import_observation
from tools.perception.solv3r import adapt


class Solv3RTests(unittest.TestCase):
    def setUp(self):
        work = TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.source = Path(work.name, "solve.npz")
        pose = np.repeat(np.eye(4, dtype=np.float32)[None], 2, axis=0)
        pose[1, :3] = [[0, 0, 1, 4], [0, 1, 0, 2], [-1, 0, 0, 6]]
        K = np.array([[4, 0, 1], [0, 2, 1], [0, 0, 1]], dtype=np.float32)
        self.raw = dict(c2w=pose, K=np.stack([K, K]), names=np.array(["b.jpg", "a.jpg"]),
                        depth=np.full((2, 3, 4), 2, dtype=np.float16),
                        depth_conf=np.full((2, 3, 4), 3, dtype=np.float16))

    def read(self, **options):
        np.savez_compressed(self.source, **self.raw)
        return adapt(self.source, **options)

    def test_reprojection_and_arrival_order(self):
        meta, arrays = self.read()
        self.assertEqual(meta["units"], "model_units")
        self.assertEqual(meta["view_names"], ["b.jpg", "a.jpg"])
        self.assertEqual(meta["sample_count"], 2)
        self.assertNotIn("timestamps_s", arrays)
        self.assertNotIn("camera_to_world_exit", arrays)
        # Source pixel (u=3,v=2), depth 2 -> [1,1,2] in the source camera.
        # Pose 1 maps that to [6,3,5]; canonical world flips y and z.
        world = arrays["camera_to_world"][1] @ [1, -1, -2, 1]
        np.testing.assert_allclose(world, [6, -3, -5, 1])
        np.testing.assert_array_equal(arrays["intrinsics_px"], self.raw["K"])
        np.testing.assert_array_equal(arrays["depth_confidence"], self.raw["depth_conf"])
        self.assertTrue(arrays["depth_valid"].all())

    def test_stream_exit_is_distinct_and_optional_names(self):
        del self.raw["names"]
        self.raw["c2w_exit"] = self.raw["c2w"].copy()
        self.raw["c2w_exit"][1, 2, 3] = 5
        meta, arrays = self.read(fps=4)
        self.assertNotIn("view_names", meta)
        self.assertEqual(arrays["camera_to_world"][1, 2, 3], -6)
        self.assertEqual(arrays["camera_to_world_exit"][1, 2, 3], -5)
        np.testing.assert_array_equal(arrays["timestamps_s"], [0, .25])

    def test_invalid_pixels_retain_mask_without_infinite_payload(self):
        self.raw["depth"][0, 0, 1] = np.inf
        self.raw["depth_conf"][0, 0, 2] = np.nan
        _, arrays = self.read()
        self.assertEqual(np.count_nonzero(~arrays["depth_valid"]), 2)
        for field in ("depth", "depth_confidence"):
            self.assertTrue(np.isfinite(arrays[field]).all())
            np.testing.assert_array_equal(arrays[field][0, 0, 1:3], [0, 0])

    def test_malformed_exports_fail(self):
        for field, invalid in (
            ("K", self.raw["K"][:1]),
            ("K", np.zeros_like(self.raw["K"])),
            ("c2w", np.zeros_like(self.raw["c2w"])),
            ("c2w_exit", np.stack([np.diag([-1., 1., 1., 1.])] * 2)),
            ("depth", np.empty((0, 1, 1))),
            ("depth", np.full_like(self.raw["depth"], -1)),
            ("depth_conf", np.empty((1, 3, 4))),
            ("names", np.array(["a"])),
            ("names", np.array([{}, {}], dtype=object)),
        ):
            with self.subTest(field=field):
                np.savez(self.source, **{**self.raw, field: invalid})
                with self.assertRaises(ValueError):
                    adapt(self.source)

    def test_missing_field_and_invalid_fps(self):
        for fps in (0, -1, float("inf"), float("nan")):
            with self.subTest(fps=fps), self.assertRaises(ValueError):
                self.read(fps=fps)
        del self.raw["depth_conf"]
        with self.assertRaises(ValueError):
            self.read()

    def bundle(self):
        np.savez_compressed(self.source, **self.raw)
        bundle = self.source.parent / "bundle"
        import_observation("solv3r", self.source, bundle)
        return bundle

    def test_camera_bottom_row_must_be_exact(self):
        self.raw["c2w"][1, 3, 0] = 1e-7
        self.raw["c2w"][1, 0, 3] = 1e7
        with self.assertRaisesRegex(ValueError, "affine"):
            self.read()

    def test_refuse_numeric_overflow(self):
        self.raw["K"] = self.raw["K"].astype(np.float64)
        self.raw["K"][0, 0, 0] = np.nextafter(0., 1.)
        with self.assertRaisesRegex(ValueError, "numeric range"):
            inspect_point(self.bundle(), 0, 2, 1)

    def test_refuse_mislabeled_units_frame_and_dimensions(self):
        bundle = self.bundle()
        manifest_path = bundle / "manifest.json"
        base = json.loads(manifest_path.read_text())
        for field, replacement in (("units", "m"), ("coordinate_system", "world"),
                                   ("sample_count", 100), ("resolution_hw", [3, 3])):
            with self.subTest(field=field):
                edited = {**base, "observation": {**base["observation"], field: replacement}}
                manifest_path.write_text(json.dumps(edited))
                with self.assertRaises(ValueError):
                    inspect_point(bundle, 0, 0, 0)

    def test_invalid_and_off_image_targets(self):
        self.raw["c2w"][1] = np.eye(4)
        self.raw["c2w"][1, 0, 3] = 0.5
        self.raw["depth"][1, 1, 0] = np.inf
        bundle = self.bundle()
        point = inspect_point(bundle, 0, 1, 1, target_view=1)
        self.assertEqual(point["projection"]["status"], "missing_target_depth")
        outside = inspect_point(bundle, 0, 0, 1, target_view=1)
        self.assertEqual(outside["projection"]["status"], "outside_image")

    def test_behind_camera(self):
        self.raw["c2w"][1] = np.diag([-1., 1., -1., 1.])
        result = inspect_point(self.bundle(), 0, 1, 1, target_view=1)
        self.assertEqual(result["projection"]["status"], "behind_camera")
