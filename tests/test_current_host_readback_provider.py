"""Isolated provider safety checks; no Node, ldd, qualification or library import.

Independent P06 controls have their own frozen oracle and raw receipts. These
regressions exercise bounded file/selection/install/clock primitives with tiny
non-runtime fixtures and retain the original method body preservation checks.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from prototypes.static_tray_v01 import current_host_readback_v01 as provider
from prototypes.static_tray_v01.supervisor import Clock, Stop
from tools import prepare_current_host_readback as preparer


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def binding(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "mode": oct(path.stat().st_mode & 0o7777)}


def descriptor(path):
    return {"path": str(path), **binding(path)}


class ProviderSelectionAndFiles(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="current-host-primitives-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def file(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_provider_error_is_never_supervisor_stop(self):
        error = provider.CurrentHostBindingError("SELECTION", "unavailable")
        self.assertIsInstance(error, RuntimeError)
        self.assertNotIsInstance(error, Stop)
        self.assertFalse(error.refusal_record["evidence_finalized"])
        self.assertEqual(error.refusal_record["authorized_evidence_destination"], "unavailable")

    def test_missing_selection_never_starts_process(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(provider.supervisor, "run_process") as process:
            with self.assertRaises(provider.CurrentHostBindingError) as caught:
                provider.selection_from_environment()
            self.assertEqual(caught.exception.code, "CH-SELECTION")
            process.assert_not_called()

    def test_partial_and_malformed_selection_fail_visibly(self):
        for values in ({provider.CONFIG_ENV: str(self.root / "config.json")},
                       {provider.DIGEST_ENV: "a" * 64},
                       {provider.CONFIG_ENV: str(self.root / "config.json"), provider.DIGEST_ENV: "A" * 64}):
            with self.subTest(values=sorted(values)), patch.dict(os.environ, values, clear=True):
                with self.assertRaises(provider.CurrentHostBindingError) as caught:
                    provider.selection_from_environment()
                self.assertEqual(caught.exception.code, "CH-SELECTION")

    def test_external_digest_is_checked_before_config_schema(self):
        path = self.file("config.json", canonical({"schema": "unapproved"}))
        with self.assertRaises(provider.CurrentHostBindingError) as caught:
            provider.validate_selection(path, "0" * 64, provider.ROOT)
        self.assertEqual(caught.exception.code, "CH-SELECTION")

    def test_unknown_or_extra_config_fields_are_not_accepted(self):
        for value in ({"schema": "old"}, {key: None for key in provider.CONFIG_KEYS} | {"extra": "execute"}):
            path = self.file("config.json", canonical(value))
            with self.assertRaises(provider.CurrentHostBindingError) as caught:
                provider.validate_selection(path, hashlib.sha256(path.read_bytes()).hexdigest(), provider.ROOT)
            self.assertEqual(caught.exception.code, "CH-SCHEMA")

    def test_duplicate_json_members_are_rejected(self):
        path = self.file("duplicate.json", b'{"path":1,"path":2}')
        with self.assertRaisesRegex(provider.CurrentHostBindingError, "Duplicate"):
            provider._read(path, 1024)

    def test_json_byte_limit_is_applied_before_parse(self):
        path = self.file("large.json", b" " * 33)
        with self.assertRaises(provider.CurrentHostBindingError):
            provider._read(path, 32)

    def test_descriptor_unknown_key_is_rejected(self):
        path = self.file("bound.json", b"{}")
        with self.assertRaises(provider.CurrentHostBindingError):
            provider._document(descriptor(path) | {"execute": True}, 1024)

    def test_file_mode_changes_are_rejected(self):
        path = self.file("data", b"bounded file")
        expected = binding(path)
        path.chmod(0o700 if expected["mode"] != "0o700" else 0o600)
        with self.assertRaises(provider.CurrentHostBindingError):
            provider._bound(path, expected)

    def test_hardlinked_file_is_rejected(self):
        path = self.file("data", b"bounded file")
        os.link(path, self.root / "alias")
        with self.assertRaises(provider.CurrentHostBindingError):
            provider.file_binding(path)

    def test_symlink_component_and_nonregular_file_are_rejected(self):
        real = self.root / "real"
        real.mkdir()
        (real / "data").write_bytes(b"data")
        (self.root / "alias").symlink_to(real, target_is_directory=True)
        os.mkfifo(self.root / "fifo")
        for path in (self.root / "alias/data", self.root / "fifo"):
            with self.subTest(path=path.name), self.assertRaises(provider.CurrentHostBindingError):
                provider.file_binding(path)

    def test_file_replacement_during_hashing_is_rejected(self):
        path = self.file("data", b"a" * 1048577)
        count = 0
        def check():
            nonlocal count
            count += 1
            if count == 3:
                replacement = self.root / "replacement"
                replacement.write_bytes(path.read_bytes())
                replacement.replace(path)
        with self.assertRaises(provider.CurrentHostBindingError):
            provider.file_binding(path, check=check)

    def test_own_clock_stop_is_wrapped_with_metadata(self):
        original = Stop("OTRAY-E-RESOURCE", "fixed timeout", "TIMEOUT")
        def check():
            raise original
        with self.assertRaises(provider.CurrentHostBindingError) as caught:
            provider._tick(check)
        self.assertEqual(caught.exception.code, "CH-CLOCK")
        self.assertEqual(caught.exception.cause, original.as_dict())
        self.assertIs(caught.exception.__cause__, original)

    def test_wrong_source_root_refuses_before_inventory_read(self):
        with self.assertRaises(provider.CurrentHostBindingError) as caught:
            provider._verify_source({"root": str(self.root), "commit": "a" * 40, "tree": "b" * 40, "inventory": {}})
        self.assertEqual(caught.exception.code, "CH-SOURCE")

    def test_incomplete_source_inventory_is_rejected(self):
        path = self.file("source.json", canonical({"schema": provider.PREFIX + "source" + provider.VERSION, "files": {}}))
        with self.assertRaises(provider.CurrentHostBindingError) as caught:
            provider._verify_source({"root": str(provider.ROOT), "commit": "a" * 40, "tree": "b" * 40, "inventory": descriptor(path)})
        self.assertEqual(caught.exception.code, "CH-SOURCE")

    def test_original_seven_methods_and_both_helpers_preserve_bodies(self):
        source = provider.ROOT / "tests/test_static_tray_readback_v01.py"
        found = {}
        for group in ast.parse(source.read_text()).body:
            if isinstance(group, ast.ClassDef):
                for node in group.body:
                    name = group.name + "." + getattr(node, "name", "")
                    if isinstance(node, ast.FunctionDef) and name in provider.ORIGINAL_BODIES:
                        raw = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False).encode()
                        found[name] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(found, provider.ORIGINAL_BODIES)
        self.assertEqual(len(provider.METHOD_IDS), 7)

    def test_launch_rejects_unbound_digest_without_supervisor_call(self):
        path = self.file("selection.json", b"{}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with patch.dict(os.environ, {provider.CONFIG_ENV: str(path), provider.DIGEST_ENV: digest}), \
                patch.object(provider.supervisor, "run_process") as process:
            with self.assertRaises(provider.CurrentHostBindingError) as caught:
                provider.guarded_run_process(["node", "--job", str(self.root / "job.json")], stage=self.root,
                                             label="synthetic-readback", clock=Clock(total_ms=30000), stage_end=0)
            self.assertEqual(caught.exception.code, "CH-LAUNCH")
            process.assert_not_called()

    def test_failed_original_setup_has_machine_refusal_without_skip(self):
        class Subject:
            pass
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(provider.CurrentHostBindingError) as caught:
                provider.setup_cpu_cohort(Subject)
        self.assertEqual(caught.exception.code, "CH-SELECTION")
        self.assertEqual(caught.exception.refusal_record["actual_checker_starts"], 0)
        self.assertFalse(caught.exception.refusal_record["evidence_finalized"])
        self.assertIsNone(Subject.root)


class SafeArchiveInstallation(unittest.TestCase):
    """Two inert files; these tests do not install the retained runtime or readers."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="current-host-install-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.payloads = {"readme.txt": b"inert fixture\n", "nested/data.bin": bytes(range(16))}
        self.archive = self.root / "fixture.tar"
        self.write_archive()

    def write_archive(self, *, mutation=None):
        with tarfile.open(self.archive, "w", format=tarfile.USTAR_FORMAT) as archive:
            for index, (name, data) in enumerate(self.payloads.items()):
                info = tarfile.TarInfo(name)
                info.mode, info.size, info.mtime = 0o644, len(data), 0
                if index == 0:
                    if mutation == "absolute": info.name = "/outside-fixture"
                    if mutation == "traversal": info.name = "../outside-fixture"
                    if mutation == "symlink": info.type, info.linkname, info.size = tarfile.SYMTYPE, "../outside-fixture", 0
                    if mutation == "hardlink": info.type, info.linkname, info.size = tarfile.LNKTYPE, "nested/data.bin", 0
                    if mutation == "fifo": info.type, info.size = tarfile.FIFOTYPE, 0
                    if mutation == "mode": info.mode = 0o777
                archive.addfile(info, io.BytesIO(data) if info.isfile() else None)
                if index == 0 and mutation == "duplicate": archive.addfile(info, io.BytesIO(data))

    def plan(self, *, report="result.json"):
        files = {name: {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data), "mode": "0o644"}
                 for name, data in self.payloads.items()}
        return {"schema": preparer.SCHEMA, "purpose": "isolated-control", "source": None,
                "archive": descriptor(self.archive), "destination": str(self.root / "installed"), "root_mode": "0o755",
                "files": files, "directories": {"nested": "0o755"},
                "members": {name: {"kind": "file", **row, "target": name} for name, row in files.items()},
                "report": str(self.root / report)}

    def test_dry_run_has_no_destination(self):
        report = preparer.install_plan(self.plan())
        self.assertEqual(report["state"], "DRY_RUN_READY")
        self.assertFalse((self.root / "installed").exists())
        self.assertEqual(report["execution_counts"], {"node": 0, "ldd": 0, "checkers": 0})

    def test_absent_install_is_exact_and_reuse_does_not_replace(self):
        result = preparer.install_plan(self.plan(), apply=True)
        self.assertEqual(result["state"], "INSTALLED_EXACT")
        path = self.root / "installed/readme.txt"
        before = (path.stat().st_ino, path.read_bytes(), path.stat().st_mode)
        reused = preparer.install_plan(self.plan(report="reuse.json"), apply=True)
        self.assertEqual(reused["state"], "ALREADY_PRESENT_EXACT")
        self.assertEqual(before, (path.stat().st_ino, path.read_bytes(), path.stat().st_mode))

    def test_unsafe_archive_variants_refuse_before_install(self):
        for mutation in ("absolute", "traversal", "duplicate", "symlink", "hardlink", "fifo", "mode"):
            with self.subTest(mutation=mutation):
                self.write_archive(mutation=mutation)
                with self.assertRaises(provider.CurrentHostBindingError) as caught:
                    preparer.install_plan(self.plan(report=mutation + ".json"), apply=True)
                self.assertEqual(caught.exception.code, "CH-INSTALL")
                self.assertFalse((self.root / "installed").exists())

    def test_existing_partial_extra_changed_or_symlink_tree_is_preserved(self):
        destination = self.root / "installed"
        destination.mkdir()
        sentinel = destination / "sentinel"
        sentinel.write_bytes(b"another writer")
        before = (sentinel.stat().st_ino, sentinel.read_bytes())
        with self.assertRaises(provider.CurrentHostBindingError):
            preparer.install_plan(self.plan(), apply=True)
        self.assertEqual(before, (sentinel.stat().st_ino, sentinel.read_bytes()))
        self.assertEqual(sorted(p.name for p in destination.iterdir()), ["sentinel"])

    def test_publication_race_never_deletes_other_writer(self):
        sentinel = self.root / "installed/other"
        def race(source, destination):
            Path(destination).mkdir()
            sentinel.write_bytes(b"racing writer")
            raise FileExistsError(errno.EEXIST, "controlled race", str(destination))
        with patch.object(preparer, "rename_without_replacement", side_effect=race) as publish:
            with self.assertRaises(provider.CurrentHostBindingError) as caught:
                preparer.install_plan(self.plan(), apply=True)
        self.assertEqual(caught.exception.code, "CH-INSTALL")
        self.assertEqual(publish.call_count, 1)
        self.assertEqual(sentinel.read_bytes(), b"racing writer")
        self.assertEqual(list(self.root.glob(".current-host-stage-*")), [])

    def test_uncertain_publication_is_unknown_and_keeps_destination(self):
        real_rename = preparer.rename_without_replacement
        def lost_reply(source, destination):
            real_rename(source, destination)
            raise OSError(errno.EIO, "controlled lost reply")
        with patch.object(preparer, "rename_without_replacement", side_effect=lost_reply):
            with self.assertRaises(provider.CurrentHostBindingError) as caught:
                preparer.install_plan(self.plan(), apply=True)
        self.assertEqual(caught.exception.state, "UNKNOWN")
        self.assertEqual((self.root / "installed/readme.txt").read_bytes(), self.payloads["readme.txt"])

    def test_cli_refuses_control_plan_as_operational_install(self):
        path = self.root / "plan.json"
        path.write_bytes(canonical(self.plan()))
        with patch("sys.stderr", io.StringIO()):
            result = preparer.main(["--plan", str(path), "--plan-sha256", hashlib.sha256(path.read_bytes()).hexdigest(), "--apply"])
        self.assertEqual(result, 1)
        self.assertFalse((self.root / "installed").exists())


if __name__ == "__main__":
    unittest.main()
