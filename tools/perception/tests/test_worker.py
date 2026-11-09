"""Exercise dispatch with installed stand-in scripts and real subprocess groups."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

from tools.perception.worker import REVISIONS, run_worker


FLOW_SCRIPT = """import pathlib, shutil, sys
video = pathlib.Path(sys.argv[1])
out = pathlib.Path("output") / video.stem
assert out.is_dir() and not list(out.iterdir())
assert video.read_bytes() == b"video"
checkpoint = pathlib.Path(sys.argv[sys.argv.index("--ckpt") + 1])
print("stand-in capture", flush=True)
shutil.copyfile("capture.npz", out / (checkpoint.stem + ".npz"))
"""
SOLV_SCRIPT = """import pathlib, shutil, sys
media = pathlib.Path(sys.argv[sys.argv.index("--images") + 1])
out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])
assert media.is_dir() and pathlib.Path(sys.argv[sys.argv.index("--checkpoint") + 1]).is_file()
shutil.copyfile("solve.npz", out / "solve.npz")
"""


@unittest.skipUnless(os.name == "posix", "worker uses POSIX process groups")
class WorkerTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.checkout = self.base / "repo"
        self.checkout.mkdir()
        self.checkpoint = self.base / "weights.ckpt"
        self.checkpoint.write_bytes(b"stand-in")
        self.video = self.base / "clip.mp4"
        self.video.write_bytes(b"video")
        self.git("init", "-q")
        self.git("config", "user.email", "test@localhost")
        self.git("config", "user.name", "Worker Test")
        (self.checkout / "examples").mkdir()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.checkout), *args], text=True).strip()

    def install(self, adapter, code):
        file = "run_v2m_demo_generation.py" if adapter == "flowhmr" else "examples/offline.py"
        (self.checkout / file).write_text(code, encoding="utf-8")
        self.git("add", file)
        self.git("commit", "-qm", "Install stand-in")
        patcher = patch.dict(REVISIONS, {adapter: self.git("rev-parse", "HEAD")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_job(self, adapter="flowhmr", media=None, job="job", **options):
        return run_worker(adapter, media or self.video, self.base / job, checkout=self.checkout,
                          python=Path(sys.executable), checkpoint=self.checkpoint, **options)

    def test_flow_dispatch_and_isolation(self):
        self.install("flowhmr", FLOW_SCRIPT)
        np.savez(self.checkout / "capture.npz", poses=np.zeros((3, 52, 3)),
                 trans=np.zeros((3, 3)), betas=np.ones((1, 16)), mocap_framerate=30)
        a = self.run_job(static_camera=True)
        b = self.run_job(job="second")
        self.assertEqual(a["status"], "complete")
        self.assertEqual(a["sample_count"], 3)
        self.assertEqual(a["raw_npz"], "raw/weights.npz")
        self.assertIn("--static_camera", a["command"])
        self.assertNotIn("--static_camera", b["command"])
        self.assertNotEqual(a["command"][2], b["command"][2])
        self.assertEqual(list((self.checkout / "output").iterdir()), [])
        self.assertIn("stand-in capture", (self.base / "job/worker.log").read_text())
        manifest = json.loads((self.base / "job/observation/manifest.json").read_text())
        self.assertEqual(manifest["source"]["sha256"], a["raw_sha256"])
        self.assertEqual(manifest["source"]["capture"], "sha256:" + a["capture"]["sha256"])
        with self.assertRaises(FileExistsError):
            self.run_job()

    def test_solv3r_folder_dispatch(self):
        self.install("solv3r", SOLV_SCRIPT)
        frames = self.base / "images"
        frames.mkdir()
        for name in ("frame10.jpg", "frame2.png", "readme.txt", ".preview.png"):
            (frames / name).write_bytes(b"image")
        np.savez(self.checkout / "solve.npz", c2w=np.eye(4)[None], K=np.eye(3)[None],
                 depth=np.ones((1, 2, 3)), depth_conf=np.ones((1, 2, 3)))
        summary = self.run_job("solv3r", frames)
        self.assertEqual(summary["sample_count"], 1)
        self.assertEqual(summary["raw_npz"], "raw/solve.npz")
        self.assertEqual(set(summary["capture"]["files_sha256"]), {"frame10.jpg", "frame2.png"})
        self.assertEqual(summary["command"][1], "examples/offline.py")
        with self.assertRaisesRegex(ValueError, "static_camera"):
            self.run_job("solv3r", frames, job="other", static_camera=True)

    def test_cpu_dispatch_and_flow_refusal(self):
        self.install("solv3r", SOLV_SCRIPT)
        frames = self.base / "images"
        frames.mkdir()
        (frames / "frame.jpg").write_bytes(b"image")
        with patch("tools.perception.worker._run", side_effect=ValueError("dispatched")) as invoke:
            with self.assertRaisesRegex(ValueError, "dispatched"):
                self.run_job("solv3r", frames, device="cpu")
            command = invoke.call_args.args[0]
            self.assertEqual(Path(command[1]).name, "solv3r_cpu.py")
            self.assertEqual(command[command.index("--checkpoint") + 1], str(self.checkpoint))
        with self.assertRaisesRegex(ValueError, "CPU mode"):
            self.run_job("flowhmr", device="cpu", job="flow-cpu")

    def test_pinned_checkout_and_worker_failures(self):
        self.install("flowhmr", "import sys; print('failure'); sys.exit(3)")
        with self.assertRaisesRegex(ValueError, "status 3"):
            self.run_job()
        self.assertIn("failure", (self.base / "job/worker.log").read_text())
        self.assertEqual(json.loads((self.base / "job/worker.json").read_text())["status"], "failed")
        self.assertFalse((self.base / "job/observation").exists())
        with patch.dict(REVISIONS, {"flowhmr": "0" * 40}), self.assertRaisesRegex(ValueError, "revision"):
            self.run_job(job="wrong")
        (self.checkout / "run_v2m_demo_generation.py").write_text("print('changed')")
        with self.assertRaisesRegex(ValueError, "tracked changes"):
            self.run_job(job="dirty")

    def test_absent_export_is_not_success(self):
        self.install("flowhmr", "print('no output')")
        with self.assertRaisesRegex(ValueError, "without producing"):
            self.run_job()
        self.assertFalse((self.base / "job/observation").exists())

    def test_timeout(self):
        import fcntl

        # The child's lock is observable across PID namespaces. Its release
        # proves this particular descendant stopped holding the resource.
        lock = self.base / "child.lock"
        child = ("import fcntl, sys, time; "
                 "f = open(sys.argv[1], 'w'); fcntl.flock(f, fcntl.LOCK_EX); "
                 "print('child locked', flush=True); time.sleep(30)")
        code = ("import subprocess, sys, time\n"
                f"subprocess.Popen([sys.executable, '-c', {child!r}, {str(lock)!r}])\n"
                "time.sleep(30)\n")
        self.install("flowhmr", code)
        with self.assertRaisesRegex(ValueError, "exceeded"):
            self.run_job(timeout_s=1)
        self.assertIn("child locked", (self.base / "job/worker.log").read_text())
        deadline = time.monotonic() + 1
        with lock.open() as stream:
            while True:
                try:
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        self.fail("Timed-out worker's child still holds the lock")
                    time.sleep(0.025)
