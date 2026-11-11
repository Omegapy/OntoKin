"""Local commit-object controls; no network or remote/ref mutation."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import import_git_commit as importer

HERE = Path(__file__).resolve().parent
REPO = Path("/workspace/scratch/801d9d641f68/ontokin")


class ExactCommitImportTests(unittest.TestCase):
    def test_unsigned_c198_original_offset_is_required(self):
        metadata, _ = importer.load_metadata(HERE / "c198-final-metadata.json")
        with self.assertRaisesRegex(ValueError, "timezone offsets"):
            importer.reconstruct(metadata, metadata["sha"])
        raw, report = importer.import_commit(REPO, metadata, metadata["sha"], author_offset="-0700", committer_offset="-0700")
        self.assertEqual(raw, (HERE / "c198-final-raw.commit").read_bytes())
        self.assertTrue(report["existing_bytes_equal"])
        self.assertEqual(report["author_offset"], "-0700")
        self.assertFalse(report["write_completed"])

    def test_signed_c198_merge_preserves_actual_folded_bytes(self):
        metadata, _ = importer.load_metadata(HERE / "c198-merge-metadata.json")
        raw, report = importer.import_commit(REPO, metadata, metadata["sha"])
        self.assertEqual(raw, (HERE / "c198-merge-raw.commit").read_bytes())
        self.assertIn(b"-----END PGP SIGNATURE-----\n \n\n", raw)
        self.assertTrue(report["github_signature_verified"])
        self.assertFalse(report["refs_updated"])

    def test_wrong_requested_sha_cannot_invoke_git(self):
        metadata, _ = importer.load_metadata(HERE / "c198-final-metadata.json")
        with patch.object(importer, "git") as git:
            with self.assertRaisesRegex(ValueError, "Requested SHA"):
                importer.import_commit(REPO, metadata, "1" * 40, write=True)
            git.assert_not_called()

    def test_changed_signature_cannot_invoke_git(self):
        metadata, _ = importer.load_metadata(HERE / "c198-merge-metadata.json")
        metadata["verification"]["signature"] = metadata["verification"]["signature"].replace("SIGNATURE", "S1GNATURE", 1)
        with patch.object(importer, "git") as git:
            with self.assertRaisesRegex(ValueError, "No unique exact"):
                importer.import_commit(REPO, metadata, metadata["sha"], write=True)
            git.assert_not_called()

    def fixture(self, tree):
        person = {"name": "Fixture", "email": "fixture@invalid", "date": "2026-11-11T00:00:00Z"}
        raw = ("tree " + tree + "\nauthor Fixture <fixture@invalid> 1794355200 +0000\ncommitter Fixture <fixture@invalid> 1794355200 +0000\n\nSynthetic local importer test\n").encode()
        metadata = {"sha": importer.oid(raw), "tree": {"sha": tree}, "parents": [], "author": person, "committer": person,
                    "message": "Synthetic local importer test", "verification": {"verified": False, "reason": "unsigned", "signature": None, "payload": None}}
        return raw, metadata

    def test_write_is_exact_and_leaves_all_refs_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "synthetic.git"
            subprocess.run(["git", "init", "--bare", "--quiet", "--template=", str(repo)], check=True, capture_output=True)
            tree = importer.git(repo, "hash-object", "-t", "tree", "-w", "--stdin", data=b"").stdout.decode().strip()
            raw, metadata = self.fixture(tree)
            refs_before = importer.git(repo, "for-each-ref", "--format=%(refname) %(objectname)").stdout
            head_before = (repo / "HEAD").read_bytes()
            reconstructed, report = importer.import_commit(repo, metadata, metadata["sha"], write=True)
            self.assertEqual(reconstructed, raw)
            self.assertTrue(report["write_completed"])
            self.assertFalse(report["already_present"])
            self.assertEqual(importer.git(repo, "cat-file", "commit", metadata["sha"]).stdout, raw)
            self.assertEqual(importer.git(repo, "for-each-ref", "--format=%(refname) %(objectname)").stdout, refs_before)
            self.assertEqual((repo / "HEAD").read_bytes(), head_before)

    def test_missing_tree_refuses_object_write(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "missing-tree.git"
            subprocess.run(["git", "init", "--bare", "--quiet", "--template=", str(repo)], check=True, capture_output=True)
            _, metadata = self.fixture("1" * 40)
            with self.assertRaisesRegex(ValueError, "Required direct tree"):
                importer.import_commit(repo, metadata, metadata["sha"], write=True)
            self.assertNotEqual(importer.git(repo, "cat-file", "-e", metadata["sha"], check=False).returncode, 0)

    def test_duplicate_metadata_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.json"
            path.write_bytes(b'{"sha":"one","sha":"two"}')
            with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
                importer.load_metadata(path)


if __name__ == "__main__":
    unittest.main()
