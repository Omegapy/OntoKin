"""Local controls for the worker screen. No case performs capture inference."""

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import worker_preflight as probe


class FileControls(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.file = Path(self.work.name) / "sample"

    def test_missing(self):
        self.assertEqual(probe.inspect_file(self.file)["status"], "missing")

    def test_read_error_is_unknown(self):
        with patch.object(Path, "stat", side_effect=PermissionError):
            self.assertEqual(probe.inspect_file(self.file)["status"], "unknown")

    def test_empty_and_placeholder_refused(self):
        for payload in (b"", b"version https://git-lfs.github.com/spec/v1\noid sha256:example"):
            with self.subTest(payload=payload):
                self.file.write_bytes(payload)
                self.assertEqual(probe.inspect_file(self.file)["status"], "invalid")

    def test_content_hash_match_and_mismatch(self):
        self.file.write_bytes(b"fixture")
        expected = hashlib.sha256(b"fixture").hexdigest()
        self.assertEqual(probe.inspect_file(self.file, expected)["status"], "pass")
        self.assertEqual(probe.inspect_file(self.file, "0" * 64)["status"], "mismatch")


class WorkerControls(unittest.TestCase):
    def test_source_requires_clean_pinned_recursive_checkout(self):
        for head, dirty, rows, expected in (
            (probe.UPSTREAM, "", " abc dep\n xyz dep/sub\n", "pass"),
            ("other", "", " abc dep\n", "mismatch"),
            (probe.UPSTREAM, " M path", " abc dep\n", "mismatch"),
            (probe.UPSTREAM, "", "-abc dep\n", "mismatch"),
            (probe.UPSTREAM, "", " abc dep\n+xyz dep/sub\n", "mismatch"),
            (probe.UPSTREAM, "", "", "mismatch"),
        ):
            with self.subTest(head=head, dirty=dirty, rows=rows), patch.object(
                probe, "git", side_effect=[head, dirty, rows]
            ):
                self.assertEqual(probe.source(Path("."))["status"], expected)

    def test_unreadable_checkout_is_unknown(self):
        with patch.object(probe, "git", side_effect=subprocess.TimeoutExpired("git", 30)):
            self.assertEqual(probe.source(Path("."))["status"], "unknown")

    def test_unavailable_cuda_stays_unavailable(self):
        torch = SimpleNamespace(__version__="fixture", version=SimpleNamespace(cuda=None),
                                cuda=SimpleNamespace(is_available=lambda: False, device_count=lambda: 0))
        with patch.dict(sys.modules, {"torch": torch}):
            self.assertEqual(probe.cuda()["status"], "unavailable")

    def test_explicit_ffmpeg_takes_precedence_over_path(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "ffmpeg-custom"
            executable.write_text("#!/bin/sh\necho 'ffmpeg version fixture'\n")
            executable.chmod(0o700)
            with patch.dict(os.environ, {"FFMPEG": str(executable)}):
                self.assertEqual(probe.ffmpeg(Path(directory))["version"], "ffmpeg version fixture")
                executable.unlink()
                self.assertEqual(probe.ffmpeg(Path(directory))["status"], "missing")

    def test_screen_blocks_when_a_restricted_asset_or_cuda_is_unknown(self):
        good = {"status": "pass"}
        unknown = {"status": "unknown"}
        root = Path("/simulated-fixture")
        with patch.object(probe.platform, "system", return_value="Linux"), \
             patch.object(sys, "version_info", (3, 10, 0)), \
             patch.object(probe, "source", return_value=good), \
             patch.object(probe, "ffmpeg", return_value=good), \
             patch.object(probe, "dependencies", return_value=good), \
             patch.object(probe, "cuda", return_value=good) as cuda, \
             patch.object(probe, "inspect_file", return_value=good) as files:
            self.assertEqual(probe.screen(root, root / "weights")["decision"], "prerequisites_passed")
            cuda.return_value = unknown
            self.assertEqual(probe.screen(root, root / "weights")["decision"], "blocked")
            cuda.return_value = good
            files.side_effect = lambda path, *args: unknown if path == root / probe.RESTRICTED[-1] else good
            self.assertEqual(probe.screen(root, root / "weights")["decision"], "blocked")


class GeneratorLayoutControls(unittest.TestCase):
    """Small fixture bytes exercise actual path resolution and digest checks."""

    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        root = Path(work.name)
        self.release = root / "release"
        self.release.mkdir()
        self.blobs = root / "blobs"
        self.blobs.mkdir()
        self.weight = self.release / "flowhmr_latest.ckpt"
        self.config = self.release / "config.yml"
        self.config.write_bytes(b"release config")
        self.blob = self.blobs / "weights-blob"
        self.blob.write_bytes(b"fixture weights")
        constants = patch.multiple(probe,
            CHECKPOINT=hashlib.sha256(self.blob.read_bytes()).hexdigest(),
            CONFIG=hashlib.sha256(self.config.read_bytes()).hexdigest())
        constants.start()
        self.addCleanup(constants.stop)

    def test_regular_release_pair_passes(self):
        self.weight.write_bytes(self.blob.read_bytes())
        assets = probe.generator_assets(self.weight)
        self.assertEqual(assets["generator_checkpoint"]["status"], "pass")
        self.assertEqual(assets["generator_config.yml"]["status"], "pass")
        self.assertEqual(assets["generator_config.yml"]["path"], str(self.config))

    def test_config_beside_link_only_cannot_qualify(self):
        self.weight.symlink_to(self.blob)
        assets = probe.generator_assets(self.weight)
        self.assertEqual(assets["generator_checkpoint"]["status"], "pass")
        self.assertEqual(assets["generator_checkpoint"]["path"], str(self.blob))
        self.assertEqual(assets["generator_config.yml"], {
            "status": "missing", "path": str(self.blobs / "config.yml")})

    def test_wrong_config_beside_target_cannot_qualify(self):
        self.weight.symlink_to(self.blob)
        (self.blobs / "config.yml").write_bytes(b"different config")
        config = probe.generator_assets(self.weight)["generator_config.yml"]
        self.assertEqual(config["status"], "mismatch")
        self.assertEqual(config["path"], str(self.blobs / "config.yml"))

    def test_link_to_correctly_paired_target_passes(self):
        self.weight.symlink_to(self.blob)
        (self.blobs / "config.yml").symlink_to(self.config)
        assets = probe.generator_assets(self.weight)
        self.assertEqual(assets["generator_checkpoint"]["status"], "pass")
        self.assertEqual(assets["generator_config.yml"]["status"], "pass")
        self.assertEqual(assets["generator_config.yml"]["path"], str(self.blobs / "config.yml"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
