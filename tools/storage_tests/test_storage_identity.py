"""Offline storage tests only: local Git/LFS fixtures, no product imports."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import check_local, prepare_lfs_archives, run_reach_source_corpus
from tools.storage_identity import (StorageContext, StorageIdentityError, archive_path,
                                    blob_id, configure_offline_filters, git,
                                    parse_pointer, pointer_bytes, prepare_offline_workspace)


class StorageIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontokin-storage-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / "source"
        self.root.mkdir()
        git(self.root, "init", "--quiet", "--template=")
        git(self.root, "config", "user.name", "Local storage fixture")
        git(self.root, "config", "user.email", "storage@example.invalid")
        self.name = "docs/engineering/storage-fixture/payload.zip"
        self.path = self.root / self.name
        self.path.parent.mkdir(parents=True)
        self.payload = b"PK\x03\x04\x00" + bytes(range(256)) * 37

    def commit(self):
        git(self.root, "add", "--", ".")
        git(self.root, "commit", "--quiet", "-m", "Storage fixture")

    def lfs_fixture(self):
        if not shutil.which("git-lfs"):
            self.fail("Storage tests require the explicitly prepared git-lfs client")
        configure_offline_filters(self.root)
        (self.root / ".gitattributes").write_text("docs/engineering/**/*.zip filter=lfs diff=lfs merge=lfs -text\n")
        self.path.write_bytes(self.payload)
        self.commit()
        self.pointer = git(self.root, "show", "HEAD:" + self.name)
        self.assertNotEqual(self.pointer, self.payload)
        return StorageContext(self.root)

    def test_ordinary_blob_stays_strict_and_pointer_looking_text_stays_ordinary(self):
        pointer = pointer_bytes(hashlib.sha256(self.payload).hexdigest(), len(self.payload))
        self.path.write_bytes(pointer)
        self.commit()
        context = StorageContext(self.root)
        self.assertEqual(context.verify_file(self.name)["kind"], "git-blob")
        self.path.write_bytes(pointer + b"changed")
        with self.assertRaisesRegex(StorageIdentityError, "Ordinary tracked input differs"):
            context.verify_file(self.name)

    def test_valid_pointer_has_separate_git_and_hydrated_payload_identities(self):
        context = self.lfs_fixture()
        binding = context.verify_file(self.name)
        self.assertEqual(binding["kind"], "git-lfs")
        self.assertTrue(binding["hydrated"])
        self.assertEqual(binding["git_object"]["oid"], blob_id(self.pointer))
        self.assertEqual(binding["payload"]["raw_git_blob"], blob_id(self.payload))
        self.assertNotEqual(binding["git_object"]["oid"], binding["payload"]["raw_git_blob"])
        self.assertEqual(binding["pointer"]["oid"], "sha256:" + hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(binding["pointer"]["size"], len(self.payload))
        self.assertEqual(git(self.root, "status", "--porcelain"), b"")

    def test_unhydrated_missing_and_corrupt_payloads_fail(self):
        context = self.lfs_fixture()
        self.path.write_bytes(self.pointer)
        with self.assertRaisesRegex(StorageIdentityError, "not hydrated"):
            context.verify_file(self.name)
        self.path.write_bytes(b"!" + self.payload[1:])
        with self.assertRaisesRegex(StorageIdentityError, "SHA-256 and size"):
            context.verify_file(self.name)
        self.path.write_bytes(self.payload[:-1])
        with self.assertRaisesRegex(StorageIdentityError, "SHA-256 and size"):
            context.verify_file(self.name)
        self.path.unlink()
        with self.assertRaisesRegex(StorageIdentityError, "Missing"):
            context.verify_file(self.name)

    def test_pointer_parser_rejects_noncanonical_or_unsupported_fields(self):
        valid = pointer_bytes("a" * 64, 19)
        invalid = [valid.replace(b"/v1", b"/v2"), valid.replace(b"sha256:", b"sha1:"),
                   valid.replace(b"a", b"A", 1), valid.replace(b"size 19", b"size 019"),
                   valid.replace(b"size 19", b"size -1"), valid.replace(b"size 19", b"size 1.9"),
                   valid.replace(b"\n", b"\r\n"), valid[:-1], valid + b"extra data\n",
                   valid.replace(b"size 19", b"size 9223372036854775808"), b"x" * 1025]
        for raw in invalid:
            with self.subTest(raw=raw[:60]), self.assertRaises(StorageIdentityError):
                parse_pointer(raw)
        self.assertEqual(parse_pointer(valid)["size"], 19)

    def test_archive_scope_excludes_part_manifests_and_normative_files(self):
        for name in ("docs/engineering/a.zip", "docs/engineering/deeper/a.zip.part001",
                     "docs/engineering/a.tar.xz", "docs/engineering/a.tar.gz"):
            self.assertTrue(archive_path(name), name)
        for name in ("docs/engineering/a.zip.parts.json", "docs/engineering/a.zip.part1",
                     "docs/language-design/a.zip", "docs/engineering/a.py", "assets/a.blend"):
            self.assertFalse(archive_path(name), name)
        (self.root / ".gitattributes").write_text("*.json filter=lfs\n")
        (self.path.parent / "payload.json").write_text("{}")
        self.commit()
        with self.assertRaisesRegex(StorageIdentityError, "outside the bounded"):
            StorageContext(self.root)

    def test_only_committed_or_index_attributes_select_lfs(self):
        self.lfs_fixture()
        (self.root / ".git/info").mkdir(exist_ok=True)
        (self.root / ".git/info/attributes").write_text("*.zip -filter\n")
        (self.root / ".gitattributes").write_text("*.zip -filter\n")
        ambient = self.directory / "ambient-config"
        ambient.write_text("[core]\n attributesFile = /not/authoritative\n")
        with patch.dict(os.environ, {"GIT_DIR": "/invalid", "GIT_INDEX_FILE": "/invalid",
                                     "GIT_CONFIG_GLOBAL": str(ambient), "GIT_CONFIG_COUNT": "1",
                                     "GIT_CONFIG_KEY_0": "core.attributesFile", "GIT_CONFIG_VALUE_0": "/invalid"}):
            self.assertEqual(StorageContext(self.root).verify_file(self.name)["kind"], "git-lfs")
            self.assertEqual(StorageContext(self.root, None).verify_file(self.name)["kind"], "git-lfs")

    def test_lfs_attribute_without_conversion_is_rejected(self):
        self.path.write_bytes(self.payload)
        self.commit()
        (self.root / ".gitattributes").write_text("*.zip filter=lfs\n")
        git(self.root, "add", ".gitattributes")
        git(self.root, "commit", "--quiet", "-m", "Incomplete tracking fixture")
        with self.assertRaisesRegex(StorageIdentityError, "ordinary blob"):
            StorageContext(self.root).verify_file(self.name)

    def test_local_runner_copies_hydration_into_private_clean_workspace_without_source_config(self):
        self.lfs_fixture()
        git(self.root, "config", "credential.helper", "source-only-credential-helper")
        git(self.root, "config", "remote.origin.url", "https://example.invalid/no-network")
        before = (self.root / ".git/index").read_bytes()
        output = self.directory / "evidence"
        with patch.object(check_local, "build_plan", return_value=[]), redirect_stdout(io.StringIO()):
            code = check_local.run(self.root, output, False, 10)
        summary = json.loads((output / "summary.json").read_text())
        self.assertEqual(code, 0, summary)
        workspace = output / "workspace"
        self.assertEqual(summary["workspace_git"]["tracked_worktree_status"], "")
        self.assertTrue(summary["source_unchanged"])
        self.assertEqual((workspace / ".gitattributes").read_bytes(), (self.root / ".gitattributes").read_bytes())
        self.assertEqual((workspace / self.name).read_bytes(), self.payload)
        self.assertEqual((self.root / ".git/index").read_bytes(), before)
        configuration = (workspace / ".git/config").read_text()
        self.assertNotIn("source-only", configuration)
        self.assertNotIn("example.invalid", configuration)
        self.assertNotIn("credential", configuration)
        self.assertEqual(git(workspace, "remote"), b"")
        self.assertEqual(list((workspace / ".git/hooks").glob("*")), [])
        oid = hashlib.sha256(self.payload).hexdigest()
        cached = workspace / ".git/lfs/objects" / oid[:2] / oid[2:4] / oid
        self.assertEqual(cached.read_bytes(), self.payload)
        self.assertFalse(cached.samefile(workspace / self.name))
        self.assertFalse(summary["workspace_storage"]["network_transfers"])
        self.assertEqual(summary["workspace_storage"]["lfs_files"][0]["git_object"]["oid"], blob_id(self.pointer))

    def test_missing_payload_blocks_workspace_before_any_steps(self):
        self.lfs_fixture()
        self.path.write_bytes(self.pointer)
        output = self.directory / "evidence"
        with patch.object(check_local, "build_plan", return_value=[]), redirect_stdout(io.StringIO()):
            code = check_local.run(self.root, output, False, 10)
        summary = json.loads((output / "summary.json").read_text())
        self.assertEqual(code, 1)
        self.assertEqual(summary["steps"], [])
        self.assertIn("not hydrated", summary["error"])

    def test_corpus_snapshot_preserves_payload_fields_and_adds_pointer_binding(self):
        self.lfs_fixture()
        with patch.object(run_reach_source_corpus, "ROOT", self.root):
            report = run_reach_source_corpus._snapshot()
        row = next(item for item in report["inputs"] if item["path"] == self.name)
        self.assertEqual(row["git_blob_sha1"], blob_id(self.payload))
        self.assertEqual(row["sha256"], hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(row["storage_binding"]["git_object"]["oid"], blob_id(self.pointer))
        self.assertEqual(report["git_status"], "")
        self.assertEqual(report["storage_identity"]["lfs_files"], 1)

    def test_corpus_ordinary_snapshot_preserves_fields_and_runtime_error_on_changed_blob(self):
        self.path.write_bytes(self.payload)
        self.commit()
        with patch.object(run_reach_source_corpus, "ROOT", self.root):
            report = run_reach_source_corpus._snapshot()
            row = next(item for item in report["inputs"] if item["path"] == self.name)
            self.assertEqual(set(row), {"path", "bytes", "sha256", "git_blob_sha1", "index_mode", "tracked"})
            self.assertNotIn("storage_identity", report)
            self.path.write_bytes(self.payload + b"changed")
            with self.assertRaisesRegex(RuntimeError, "Ordinary tracked input differs"):
                run_reach_source_corpus._snapshot()

    def test_plan_has_exact_paths_and_proposed_pointers_without_repository_mutation(self):
        self.path.write_bytes(self.payload)
        manifest = self.path.parent / "payload.zip.parts.json"
        manifest.write_text('{"retained":true}\n')
        self.commit()
        index_before = (self.root / ".git/index").read_bytes()
        config_before = (self.root / ".git/config").read_bytes()
        output = self.directory / "plan"
        report = prepare_lfs_archives.prepare(self.root, output)
        self.assertEqual(report["archive_count"], 1)
        self.assertEqual(report["files"][0]["path"], self.name)
        pointer = pointer_bytes(hashlib.sha256(self.payload).hexdigest(), len(self.payload))
        self.assertEqual(report["files"][0]["proposed_pointer_git_blob"], blob_id(pointer))
        self.assertEqual((output / "archive-paths.nul").read_bytes(), self.name.encode() + b"\0")
        self.assertFalse((self.root / ".gitattributes").exists())
        self.assertEqual((self.root / ".git/index").read_bytes(), index_before)
        self.assertEqual((self.root / ".git/config").read_bytes(), config_before)
        self.assertFalse(report["repository_mutated"])
        self.assertFalse(report["network_transfers"])
        (self.root / ".gitattributes").write_bytes((output / "gitattributes.proposed").read_bytes())
        configure_offline_filters(self.root)
        git(self.root, "add", ".gitattributes")
        git(self.root, "add", "--renormalize", "--pathspec-from-file=" + str(output / "archive-paths.nul"), "--pathspec-file-nul")
        git(self.root, "commit", "--quiet", "-m", "Local-only migration fixture")
        migrated = StorageContext(self.root)
        self.assertEqual(migrated.verify_file(self.name)["kind"], "git-lfs")
        self.assertEqual(migrated.verify_file(manifest.relative_to(self.root).as_posix())["kind"], "git-blob")
        self.assertEqual(git(self.root, "rev-parse", "HEAD^{}~1").decode().strip(), report["source"]["commit"])
        verified = prepare_lfs_archives.verify_plan(self.root, output / "plan.json", self.directory / "verified")
        self.assertEqual(verified["status"], "passed")
        self.assertEqual(verified["archive_count"], 1)
        self.assertFalse(verified["remote_availability_established_by_this_command"])
        manifest.write_text('{"retained":false}\n')
        self.commit()
        with self.assertRaisesRegex(StorageIdentityError, "outside the planned"):
            prepare_lfs_archives.verify_plan(self.root, output / "plan.json", self.directory / "wrong-conversion")

    def test_plan_rejects_dirty_source_and_existing_configuration(self):
        self.path.write_bytes(self.payload)
        self.commit()
        self.path.write_bytes(self.payload + b"changed")
        with self.assertRaisesRegex(StorageIdentityError, "clean identified"):
            prepare_lfs_archives.prepare(self.root, self.directory / "dirty-plan")
        self.path.write_bytes(self.payload)
        (self.root / ".gitattributes").write_text("*.txt text\n")
        self.commit()
        with self.assertRaisesRegex(StorageIdentityError, "existing attributes"):
            prepare_lfs_archives.prepare(self.root, self.directory / "existing-plan")

    def test_migration_rejects_an_unrelated_gitlink(self):
        self.path.write_bytes(self.payload)
        self.commit()
        output = self.directory / "plan"
        plan = prepare_lfs_archives.prepare(self.root, output)
        (self.root / ".gitattributes").write_bytes((output / "gitattributes.proposed").read_bytes())
        configure_offline_filters(self.root)
        git(self.root, "add", ".gitattributes")
        git(self.root, "add", "--renormalize", "--pathspec-from-file=" + str(output / "archive-paths.nul"), "--pathspec-file-nul")
        (self.root / "unexpected-submodule").mkdir()
        git(self.root, "update-index", "--add", "--cacheinfo", "160000," + plan["source"]["commit"] + ",unexpected-submodule")
        git(self.root, "commit", "--quiet", "-m", "Invalid migration with gitlink")
        self.assertEqual(git(self.root, "status", "--porcelain"), b"")
        with self.assertRaisesRegex(StorageIdentityError, "Unsupported Git tree entry"):
            prepare_lfs_archives.verify_plan(self.root, output / "plan.json", self.directory / "invalid-gitlink")

    def test_planner_accepts_only_the_exact_empty_bootstrap(self):
        self.path.write_bytes(self.payload)
        (self.root / ".gitattributes").write_text(prepare_lfs_archives.BOOTSTRAP_ATTRIBUTES)
        self.commit()
        self.assertEqual(StorageContext(self.root).lfs_paths, ())
        plan = prepare_lfs_archives.prepare(self.root, self.directory / "bootstrap-plan")
        self.assertEqual(plan["archive_count"], 1)
        self.assertEqual(plan["files"][0]["original_git_blob"], blob_id(self.payload))
        nested = self.path.parent / ".gitattributes"
        nested.write_text("*.zip -filter\n")
        self.commit()
        with self.assertRaisesRegex(StorageIdentityError, "existing attributes"):
            prepare_lfs_archives.prepare(self.root, self.directory / "nested-attributes-plan")

    def recorded_starts(self):
        """Record every subprocess.run command line, then run it unchanged."""
        commands, run = [], subprocess.run
        def record(command, *args, **kwargs):
            commands.append(list(command))
            return run(command, *args, **kwargs)
        return commands, patch("tools.storage_identity.subprocess.run", side_effect=record)

    def test_callers_that_inject_no_resolver_still_start_git_by_name(self):
        """No LFS client needed. Starts Git by name, as before, in this throwaway repository."""
        (self.root / ".gitattributes").write_text(prepare_lfs_archives.BOOTSTRAP_ATTRIBUTES)
        self.path.write_bytes(self.payload)
        self.commit()
        commands, recording = self.recorded_starts()
        with recording:
            self.assertEqual(StorageContext(self.root).lfs_paths, ())
            self.assertEqual(prepare_offline_workspace(self.root)["lfs_files"], [])
            self.assertEqual(prepare_lfs_archives.prepare(self.root, self.directory / "plan")["archive_count"], 1)
            with patch.object(run_reach_source_corpus, "ROOT", self.root):
                self.assertEqual(run_reach_source_corpus._snapshot()["git_status"], "")
        prefix = ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
                  "-c", "core.attributesFile=" + os.devnull, "-C"]
        self.assertGreater(len(commands), 10)
        self.assertEqual([command for command in commands if command[:8] != prefix], [])

    def test_injected_resolver_names_the_git_of_every_start(self):
        """No LFS client needed. Starts the Git that PATH names, by its absolute path."""
        (self.root / ".gitattributes").write_text(prepare_lfs_archives.BOOTSTRAP_ATTRIBUTES)
        self.path.write_bytes(self.payload)
        self.commit()
        executable = shutil.which("git")
        self.assertTrue(executable and os.path.isabs(executable), executable)
        resolved = []
        def resolver():
            resolved.append(executable)
            return executable
        commands, recording = self.recorded_starts()
        with recording:
            self.assertEqual(prepare_offline_workspace(self.root, git_executable=resolver)["lfs_files"], [])
        self.assertGreaterEqual(len(commands), 7)
        self.assertEqual(len(resolved), len(commands))
        self.assertEqual([command for command in commands if command[0] != executable], [])

    def test_lfs_branch_starts_git_by_name_by_default_and_through_an_injected_resolver(self):
        """No LFS client needed: a /bin/sh stand-in answers only the version query. Starts Git by name,
        then by the resolver's absolute path, in this throwaway repository."""
        (self.root / ".gitattributes").write_text("docs/engineering/**/*.zip filter=lfs diff=lfs merge=lfs -text\n")
        self.path.write_bytes(pointer_bytes(hashlib.sha256(self.payload).hexdigest(), len(self.payload)))
        self.commit()  # No filter is configured, so Git stores the pointer text itself.
        self.path.write_bytes(self.payload)  # The hydrated payload, as a copied workspace holds it.
        stand_in = self.directory / "lfs-stand-in" / "git-lfs"
        stand_in.parent.mkdir()
        stand_in.write_text("#!/bin/sh\necho 'git-lfs/3.8.1 (synthetic stand-in)'\n")
        stand_in.chmod(0o755)
        executable = shutil.which("git")
        resolved = []
        def resolver():
            resolved.append(executable)
            return executable
        searched = {"PATH": str(stand_in.parent) + os.pathsep + os.environ.get("PATH", "")}
        for injected in (None, resolver):
            with self.subTest(resolver=injected is not None):
                commands, recording = self.recorded_starts()
                with patch.dict(os.environ, searched), recording:
                    report = prepare_offline_workspace(self.root, git_executable=injected)
                self.assertEqual([binding["path"] for binding in report["lfs_files"]], [self.name])
                self.assertEqual(report["client"]["executable"], str(stand_in.resolve()))
                starts = [command for command in commands if command[0] != str(stand_in.resolve())]
                self.assertIn(["config", "--local", "filter.lfs.required", "true"], [command[-4:] for command in starts])
                self.assertEqual({command[0] for command in starts}, {"git" if injected is None else executable})
                self.assertEqual(len(resolved), 0 if injected is None else len(starts))

    def test_a_refusing_resolver_starts_nothing(self):
        """Starts no process. A refusal propagates; an absent Git keeps the storage error."""
        class Refusal(ValueError):
            pass
        def refusing():
            raise Refusal("synthetic binding refusal")
        def absent():
            raise FileNotFoundError(2, "No git executable was found on PATH", "git")
        with patch("tools.storage_identity.subprocess.run") as start:
            with self.assertRaisesRegex(Refusal, "synthetic binding refusal"):
                StorageContext(self.root, git_executable=refusing)
            with self.assertRaisesRegex(StorageIdentityError, "No git executable was found on PATH"):
                git(self.root, "rev-parse", "HEAD", git_executable=absent)
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
