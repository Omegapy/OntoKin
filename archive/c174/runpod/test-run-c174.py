"""Exercise same-ZIP launch and failure handling with small offline stage fixtures."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent


class SingleArchiveLaunch(unittest.TestCase):
    def setUp(self):
        work = TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.top = Path(work.name)
        self.kit = self.top / "extracted kit"
        self.ws = self.top / "Pod workspace"
        self.archive = self.top / "handoff.zip"
        (self.kit / "runpod").mkdir(parents=True)
        (self.kit / "tools").mkdir()
        for name in ("verify_kit.py", "run-c174.sh"):
            shutil.copyfile(HERE / name, self.kit / "runpod" / name)
        shutil.copyfile(HERE.parent / "tools/verify_package.py", self.kit / "tools/verify_package.py")
        for subdir, name in (("ontokin", "python3.12"), ("flowhmr", "python")):
            directory = self.ws / "envs" / subdir / "bin"
            directory.mkdir(parents=True)
            (directory / name).symlink_to(sys.executable)
        (self.kit / "restore-main.sh").write_text('set -eu\nmkdir -- "$1"\n')
        (self.kit / "resume.sh").write_text(
            'set -eu\n'
            'test -d "$1"\ntest "$2" = "$ONTOKIN_WORKSPACE/FlowHMR"\n'
            'test "$3" = "$ONTOKIN_WORKSPACE/envs/flowhmr/bin/python"\n'
            'test "$4" = "$ONTOKIN_WORKSPACE/models/flowhmr_latest/flowhmr_latest.ckpt"\n'
            'mkdir -- "$5"\nexit "${MOCK_RESUME_EXIT:-0}"\n'
        )
        files = {}
        for f in self.kit.rglob("*"):
            if f.is_file():
                files[f.relative_to(self.kit).as_posix()] = {
                    "bytes": f.stat().st_size,
                    "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                }
        self.manifest = {"checkpoint": "C174", "files": files}
        (self.kit / "PACKAGE-MANIFEST.json").write_text(json.dumps(self.manifest))
        with ZipFile(self.archive, "w") as zipped:
            for f in self.kit.rglob("*"):
                if f.is_file():
                    zipped.write(f, f.relative_to(self.kit))

    def launch(self, expected, archive=None, worker_exit=0):
        cmd = ["bash", self.kit / "runpod/run-c174.sh", archive or self.archive]
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=20, env={
            **os.environ, "ONTOKIN_WORKSPACE": str(self.ws), "MOCK_RESUME_EXIT": str(worker_exit),
        })
        self.assertEqual(result.returncode, expected, msg=result.stderr)
        return result

    def job(self):
        job, = (self.ws / "jobs").iterdir()
        return job

    def check_refusal(self):
        self.launch(1)
        job = self.job()
        self.assertEqual((job / "package-check.exitcode").read_text().strip(), "1")
        self.assertFalse((job / "restored").exists())

    def test_same_archive_and_unique_job_on_retry(self):
        self.launch(0)
        self.launch(0)
        jobs = list((self.ws / "jobs").iterdir())
        self.assertEqual(len(jobs), 2)
        for job in jobs:
            self.assertFalse((job / "kit").exists())
            self.assertEqual((job / "resume.exitcode").read_text().strip(), "0")
            self.assertTrue((job / "output").is_dir())

    def test_resume_failure_is_recorded_and_returned(self):
        self.launch(17, worker_exit=17)
        self.assertEqual((self.job() / "resume.exitcode").read_text().strip(), "17")

    def test_changed_extracted_file_refused_before_restore(self):
        (self.kit / "restore-main.sh").write_text("exit 87\n")
        self.check_refusal()

    def test_extra_extracted_file_refused(self):
        (self.kit / "unexpected.py").write_text("print('fixture')\n")
        self.check_refusal()

    def test_extracted_symbolic_link_refused(self):
        (self.kit / "external-file").symlink_to(self.archive)
        self.check_refusal()

    def test_wrong_archive_refused(self):
        other = self.top / "other.zip"
        with ZipFile(other, "w") as zipped:
            zipped.writestr("PACKAGE-MANIFEST.json", '{"checkpoint":"C173","files":{}}')
        self.launch(1, archive=other)
        self.assertFalse((self.job() / "restored").exists())

    def test_archive_inside_extracted_tree_refused(self):
        misplaced = self.kit / "handoff.zip"
        shutil.copyfile(self.archive, misplaced)
        self.launch(2, archive=misplaced)
        self.assertFalse((self.ws / "jobs").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
