"""Exact texture bundle identities, immutable transfer, and confined files."""

from dataclasses import FrozenInstanceError
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ontokin.bundle import BundleError, SourceUnit, load_bundle
from ontokin.texture_bundle import (AssetUnit, TextureBundle, load_texture_bundle,
                                    load_texture_file_manifest, load_texture_file_manifest_transport)


FIXTURES = Path(__file__).resolve().parents[1] / "examples/textured-surfaces"
EXPECTED = json.loads((FIXTURES / "expected.json").read_text())
CASES = {case["name"]: case for case in EXPECTED["cases"]}


def inline(*assets):
    return {"schema_version": "ontokin.bundle/0.2",
            "entry": {"filename": "main.ok", "source": "unparsed source"},
            "modules": [], "assets": [asset.to_descriptor() for asset in assets]}


class TextureBundleTests(unittest.TestCase):
    def test_frozen_manifest_identity_and_original_byte_round_trip(self):
        for name in ("rgb-panel", "assembly", "generated", "same-bytes-distinct-ids",
                     "maximum-decoded-four", "older-user-function-png-asset"):
            with self.subTest(case=name):
                expected = CASES[name]
                sealed = load_texture_file_manifest(FIXTURES / expected["file_manifest"])
                self.assertEqual(sealed.program_revision, expected["program_revision"])
                self.assertEqual(sealed.manifest(), expected["canonical_manifest"])
                copied = load_texture_bundle(json.loads(json.dumps(sealed.to_payload())))
                self.assertEqual(copied, sealed)
                self.assertEqual([asset.raw for asset in copied.assets],
                                 [asset.raw for asset in sealed.assets])
        self.assertEqual(load_texture_file_manifest(FIXTURES / "reordered-assets.files.json"),
                         load_texture_file_manifest(FIXTURES / "same-bytes-distinct-ids.files.json"))

    def test_sealing_is_transport_only_and_legacy_loader_remains_strict(self):
        asset = AssetUnit("label", b"not a PNG")
        sealed = load_texture_bundle(inline(asset))
        self.assertEqual(sealed.assets, (asset,))
        self.assertEqual(asset.revision, asset.sha256)
        with self.assertRaises(BundleError):
            load_bundle(sealed.to_payload())
        old = load_bundle({"schema_version": "ontokin.bundle/0.1",
                           "entry": {"filename": "main.ok", "source": "unparsed source"},
                           "modules": []})
        with self.assertRaises(BundleError):
            load_texture_bundle(old.to_payload())
        self.assertNotEqual(TextureBundle(old.entry).program_revision, old.program_revision)

    def test_immutability_detached_accessors_order_and_distinct_named_content(self):
        a, b = AssetUnit("a", b"same"), AssetUnit("b", b"same")
        original = inline(b, a)
        sealed = load_texture_bundle(original)
        self.assertEqual(sealed.assets, (a, b))
        self.assertEqual(sealed.program_revision, load_texture_bundle(inline(a, b)).program_revision)
        original["assets"][0]["data_base64"] = ""
        exposed = sealed.to_payload()
        exposed["assets"][0]["asset_id"] = "changed"
        exposed_map = sealed.asset_map
        exposed_map.clear()
        self.assertEqual(set(sealed.asset_map), {"a", "b"})
        self.assertEqual(sealed.assets[0].raw, b"same")
        with self.assertRaises(FrozenInstanceError):
            sealed.assets[0].raw = b"changed"
        self.assertNotEqual(sealed.program_revision, load_texture_bundle(inline(a)).program_revision)
        renamed = TextureBundle(SourceUnit("entry", "renamed.ok", sealed.entry.raw), (), sealed.assets)
        self.assertNotEqual(renamed.program_revision, sealed.program_revision)

    def test_closed_shapes_id_digest_media_and_canonical_padding(self):
        asset = AssetUnit("label", b"f")
        bad = []
        for field, value in (("asset_id", "UPPER"), ("asset_id", "a/escape"),
                             ("sha256", asset.sha256.upper()), ("sha256", "sha256:" + "0" * 64),
                             ("media_type", "image/jpeg"), ("data_base64", "Zg"),
                             ("data_base64", "Zh=="), ("data_base64", "Zg==\n")):
            candidate = inline(asset)
            candidate["assets"][0][field] = value
            bad.append(candidate)
        bad.extend([inline(asset, asset), {**inline(asset), "extra": None}])
        missing = inline(asset)
        del missing["assets"][0]["sha256"]
        bad.append(missing)
        for candidate in bad:
            with self.subTest(candidate=candidate), self.assertRaises(BundleError) as rejected:
                load_texture_bundle(candidate)
            self.assertEqual(rejected.exception.code, "OKA-E-REQUEST")

    def test_base64_and_asset_count_bounds_precede_allocation(self):
        candidate = inline(AssetUnit("label", b""))
        candidate["assets"][0]["data_base64"] = "A" * 400001
        with patch("ontokin.texture_bundle.base64.b64decode") as decode:
            with self.assertRaises(BundleError) as rejected:
                load_texture_bundle(candidate)
        self.assertEqual(rejected.exception.code, "OKA-E-RESOURCE")
        decode.assert_not_called()
        with self.assertRaises(BundleError):
            load_texture_bundle(inline(*(AssetUnit("a" + str(i), b"") for i in range(5))))
        with self.assertRaises(BundleError):
            AssetUnit("label", b"x" * 300001)
        at_limit = load_texture_bundle(inline(*(AssetUnit("a" + str(i), b"x" * 300000)
                                               for i in range(4))))
        self.assertEqual(sum(len(asset.raw) for asset in at_limit.assets), 1200000)

    def _files(self, root):
        source, raw = b"exact original source", b"bounded raw image"
        (root / "entry.ok").write_bytes(source)
        (root / "image.png").write_bytes(raw)
        asset = AssetUnit("label", raw)
        descriptor = asset.to_descriptor()
        del descriptor["data_base64"]
        descriptor["path"] = "image.png"
        payload = {"schema_version": "ontokin.files/0.2",
                   "entry": {"filename": "main.ok", "path": "entry.ok"},
                   "modules": [], "assets": [descriptor]}
        manifest = root / "program.json"
        manifest.write_text(json.dumps(payload))
        return manifest, payload

    def test_manifest_and_every_declared_component_refuse_symlinks_and_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, payload = self._files(root)
            initial = load_texture_file_manifest(manifest)
            self.assertEqual(initial.assets[0].raw, b"bounded raw image")
            (root / "linked.png").symlink_to(root / "image.png")
            (root / "linked-dir").symlink_to(root, target_is_directory=True)
            (root / "linked-manifest.json").symlink_to(manifest)
            with self.assertRaises(BundleError):
                load_texture_file_manifest(root / "linked-manifest.json")
            for path in ("linked.png", "linked-dir/image.png", "../image.png", "./image.png",
                         "/image.png", "https://example.test/image.png", "C:escape.png"):
                payload["assets"][0]["path"] = path
                manifest.write_text(json.dumps(payload))
                with self.subTest(path=path), self.assertRaises(BundleError):
                    load_texture_file_manifest(manifest)
            payload["assets"][0]["path"] = "image.png"
            payload["entry"]["path"] = "linked-dir/entry.ok"
            manifest.write_text(json.dumps(payload))
            with self.assertRaises(BundleError):
                load_texture_file_manifest(manifest)

    def test_replacing_input_during_held_descriptor_read_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = self._files(root)
            ordinary_read = os.read
            replaced = False

            def read_and_replace(fd, size):
                nonlocal replaced
                data = ordinary_read(fd, size)
                if data == b"exact original source" and not replaced:
                    replacement = root / "replacement.ok"
                    replacement.write_bytes(data)
                    replacement.replace(root / "entry.ok")
                    replaced = True
                return data

            with patch("ontokin.texture_bundle.os.read", side_effect=read_and_replace):
                with self.assertRaises(BundleError) as rejected:
                    load_texture_file_manifest(manifest)
            self.assertTrue(replaced)
            self.assertEqual(rejected.exception.code, "OKA-E-REQUEST")

    def test_one_secure_manifest_read_returns_exact_transport_and_protected_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = self._files(root)
            bundle, raw, paths = load_texture_file_manifest_transport(manifest)
            self.assertEqual(raw, manifest.read_bytes())
            self.assertEqual(paths, ("entry.ok", "image.png"))
            self.assertIsInstance(paths, tuple)
            self.assertEqual(bundle, load_texture_file_manifest(manifest))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Named FIFOs are unavailable on this host")
    def test_fifo_manifest_is_rejected_before_any_potentially_blocking_open(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "manifest.fifo"
            os.mkfifo(fifo)
            ordinary_open = os.open

            def guarded_open(path, *args, **kwargs):
                if path == fifo.name:
                    self.fail("A nonregular manifest must be refused before opening it")
                return ordinary_open(path, *args, **kwargs)

            with patch("ontokin.texture_bundle.os.open", side_effect=guarded_open):
                with self.assertRaises(BundleError) as rejected:
                    load_texture_file_manifest_transport(fifo)
            self.assertEqual(rejected.exception.code, "OKA-E-REQUEST")

    def test_manifest_replacement_during_input_reads_cannot_change_protection_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, _ = self._files(root)
            raw = manifest.read_bytes()
            ordinary_read = os.read
            replaced = False

            def read_and_replace(fd, size):
                nonlocal replaced
                data = ordinary_read(fd, size)
                if data == b"exact original source" and not replaced:
                    replacement = root / "replacement.json"
                    replacement.write_bytes(raw)
                    replacement.replace(manifest)
                    replaced = True
                return data

            with patch("ontokin.texture_bundle.os.read", side_effect=read_and_replace):
                with self.assertRaises(BundleError) as rejected:
                    load_texture_file_manifest_transport(manifest)
            self.assertTrue(replaced)
            self.assertEqual(rejected.exception.code, "OKA-E-REQUEST")


if __name__ == "__main__":
    unittest.main()
