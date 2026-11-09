"""Synthetic fixtures for the pinned evidence checker. These do not execute a neural model."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from tools.perception.observation import digest, import_observation


spec = importlib.util.spec_from_file_location("verify_capture", Path(__file__).with_name("verify-capture.py"))
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

LOG = """[1/1] /fixture/ontokin_test.mp4
>>> video transcoding done (encoder: libx264): /fixture/output/ontokin_test_30fps.mp4
  [bbox] track 3: length=3 frame_range=[2,5] / total=9
  === Step 2: Static Camera ===
  [sam] saved -> /fixture/output/ontokin_test_sam3d_feat_static.pt  (shape=(4, 3072))
  [gen] T=4, range=[2,5], seed=0, cfg=1.0
=== Done | ok=1 failed=0 ===
"""


class SyntheticControls(unittest.TestCase):
    def setUp(self):
        self.make_fixture(use_stretch=False)

    def make_fixture(self, *, use_stretch):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.job = Path(self.temp.name)
        if use_stretch:
            kit = Path(__file__).resolve().parents[1]
            self.video = kit / "capture/stretch_slow_static_1280x720_25fps.mp4"
        else:
            self.video = self.job / "fixture.mp4"
            self.video.write_bytes(b"synthetic identity fixture only")
        raw = self.job / "raw" / "model.npz"
        raw.parent.mkdir()
        np.savez(raw, trans=np.zeros((4, 3)), poses=np.zeros((4, 52, 3)), betas=np.zeros((1, 16)),
                 mocap_framerate=30, num_frames=4)
        capture = digest(self.video)
        import_observation("flowhmr", raw, self.job / "observation",
                           capture="sha256:" + capture, checkpoint="sha256:" + checker.CHECKPOINT)
        self.receipt = {
            "schema": "ontokin.perception_worker/1", "adapter": "flowhmr", "status": "complete",
            "revision": checker.REVISION, "python": "/fixture/python", "timeout_s": 180,
            "capture": {"kind": "video", "sha256": capture},
            "checkpoint": {"sha256": checker.CHECKPOINT, "path": "/fixture/model.ckpt"},
            "command": ["/fixture/python", "run_v2m_demo_generation.py", "/fixture/ontokin_test.mp4",
                        "--ckpt", "/fixture/model.ckpt", "--static_camera"],
            "raw_npz": "raw/model.npz", "raw_sha256": digest(raw), "observation": "observation", "sample_count": 4,
        }
        (self.job / "worker.log").write_text(LOG)

    def check(self, *, stretch=False):
        (self.job / "worker.json").write_text(json.dumps(self.receipt))
        verify = checker.verify_stretch if stretch else checker.verify
        return verify(self.job, self.video)

    def test_consistent_fixture(self):
        report = self.check()
        self.assertEqual(report["track_range_30hz_inclusive"], [2, 5])
        self.assertEqual(report["exported_samples"], 4)
        self.assertFalse(report["contact_scores_present"])

    def test_project_rejects_otherwise_consistent_other_video(self):
        self.check()
        with self.assertRaisesRegex(ValueError, "bundled fixed-camera stretch"):
            self.check(stretch=True)

    def test_project_rejects_wrong_full_transcode_count(self):
        self.make_fixture(use_stretch=True)
        self.check()
        with self.assertRaisesRegex(ValueError, "300 analysis frames"):
            self.check(stretch=True)

    def test_project_allows_shorter_track_within_300_frame_timeline(self):
        self.make_fixture(use_stretch=True)
        (self.job / "worker.log").write_text(LOG.replace("total=9", "total=300"))
        report = self.check(stretch=True)
        self.assertEqual(report["transcoded_frames"], 300)
        self.assertEqual(report["track_range_30hz_inclusive"], [2, 5])

    def test_receipt_with_another_jobs_log(self):
        (self.job / "worker.log").write_text(LOG.replace("ontokin_test", "ontokin_other"))
        with self.assertRaisesRegex(ValueError, "reserved video alias"):
            self.check()

    def test_missing_track(self):
        (self.job / "worker.log").write_text(LOG.replace("[bbox] track", "[bbox] WARN no_tracks"))
        with self.assertRaisesRegex(ValueError, "No person track"):
            self.check()

    def test_cached_features(self):
        (self.job / "worker.log").write_text(LOG.replace("[sam] saved ->", "[sam] skip (exists):"))
        with self.assertRaisesRegex(ValueError, "reused"):
            self.check()

    def test_displaced_track_with_correct_length(self):
        (self.job / "worker.log").write_text(LOG.replace("range=[2,5], seed", "range=[1,4], seed"))
        with self.assertRaisesRegex(ValueError, "disagree"):
            self.check()

    def test_wrong_conditioning_count(self):
        (self.job / "worker.log").write_text(LOG.replace("4, 3072", "3, 3072"))
        with self.assertRaisesRegex(ValueError, "disagree"):
            self.check()

    def test_changed_input(self):
        self.video.write_bytes(b"changed identity")
        with self.assertRaisesRegex(ValueError, "Video hash"):
            self.check()

    def test_tampered_observation_fps(self):
        target = self.job / "observation" / "manifest.json"
        manifest = json.loads(target.read_text())
        manifest["observation"]["fps"] = 24
        target.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "fresh decode"):
            self.check()

    def test_failed_worker(self):
        self.receipt["status"] = "failed"
        with self.assertRaisesRegex(ValueError, "did not complete"):
            self.check()


if __name__ == "__main__":
    unittest.main(verbosity=2)
