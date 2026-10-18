"""Exact byte, transport, and candidate identity oracles for program bundles."""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from ontokin.bundle import (BundleError, MAX_SOURCE_BYTES, ProgramBundle, SourceUnit,
                            load_bundle, load_file_manifest)


FIXTURES = Path(__file__).resolve().parents[1] / "docs/language-design/construction-v0.1"
RACK_REVISION = "sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082"


def payload(source="", modules=()):
    return {"schema_version": "ontokin.bundle/0.1", "entry": {"filename": "main.ok", "source": source},
            "modules": list(modules)}


def module(package, source="", *, version="1.0.0", filename="library.ok"):
    return {"package_id": package, "version": version, "filename": filename, "source": source}


class BundleTests(unittest.TestCase):
    def test_frozen_golden_pin_and_exact_file_inline_round_trip(self):
        root = FIXTURES / "01-keyed-rack"
        inline = load_bundle(json.loads((root / "program.bundle.json").read_text()))
        files = load_file_manifest(root / "program.files.json")
        self.assertEqual(inline, files)
        self.assertEqual(files.program_revision, RACK_REVISION)
        self.assertEqual(load_bundle(json.loads(json.dumps(files.to_payload(), ensure_ascii=False))), files)
        for unit in files.units:
            self.assertEqual(unit.raw, (root / unit.filename).read_bytes())
            self.assertEqual(unit.revision, "sha256:" + hashlib.sha256(unit.raw).hexdigest())
        self.assertIn(files.modules[0].revision, files.entry.text)
        self.assertNotEqual(files.program_revision, files.entry.revision)

    def test_candidate_hash_is_defined_before_parsing_and_survives_exact_utf8(self):
        text = '\ufeffontokin "0.2";\r\n// café 雪\r\nclass unfinished {'
        value = load_bundle(payload(text))
        self.assertEqual(value.entry.raw, text.encode("utf-8"))
        self.assertEqual(load_bundle(value.to_payload()).program_revision, value.program_revision)
        self.assertNotEqual(load_bundle(payload(text.replace("\r\n", "\n"))).program_revision,
                            value.program_revision)

    def test_hash_order_and_every_declared_identity_input(self):
        initial = payload("entry", [module("example.b", "B"), module("example.a", "A")])
        bundle = load_bundle(initial)
        reordered = {key: initial[key] for key in reversed(initial)}
        reordered["modules"] = list(reversed(initial["modules"]))
        self.assertEqual(load_bundle(reordered).program_revision, bundle.program_revision)
        variants = []
        for field, replacement in [("filename", "renamed.ok"), ("source", "A\n"),
                                   ("version", "1.0.1"), ("package_id", "example.renamed")]:
            variant = copy.deepcopy(initial)
            variant["modules"][1][field] = replacement
            variants.append(variant)
        changed_entry = copy.deepcopy(initial)
        changed_entry["entry"]["filename"] = "entry-renamed.ok"
        variants.append(changed_entry)
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertNotEqual(load_bundle(variant).program_revision, bundle.program_revision)

    def test_snapshot_does_not_share_mutable_source_or_payload(self):
        request = payload("exact")
        bundle = load_bundle(request)
        request["entry"]["source"] = "changed"
        exposed = bundle.to_payload()
        exposed["entry"]["source"] = "also changed"
        source = bundle.sources["entry"]
        source.text = "not the sealed text"
        source.filename = "different.ok"
        self.assertEqual(bundle.entry.text, "exact")
        self.assertEqual(bundle.sources["entry"].text, "exact")
        self.assertEqual(bundle.sources["entry"].filename, "main.ok")
        with self.assertRaises(FrozenInstanceError):
            bundle.entry.raw = b"changed"
        with self.assertRaises(BundleError):
            SourceUnit("wrong", "main.ok", b"")

    def test_source_id_ambiguity_and_conflicting_versions_are_distinct(self):
        duplicate = module("example.a", "A")
        with self.assertRaises(BundleError) as rejected:
            load_bundle(payload("", [duplicate, copy.deepcopy(duplicate)]))
        self.assertEqual(rejected.exception.code, "OKA-E-REQUEST")
        candidate = load_bundle(payload("", [duplicate, module("example.a", "B", version="2.0.0")]))
        self.assertEqual(len(candidate.source_registry), 3)
        self.assertEqual(len(candidate.program_revision), 71)

    def test_closed_transport_shapes_unicode_and_pin_domains(self):
        bad = [None, [], {}, {**payload(), "extra": 1}]
        for field, value in [("entry", []), ("modules", {}), ("schema_version", "other")]:
            bad.append({**payload(), field: value})
        for text in [None, 1, {}, "\ud800"]:
            bad.append(payload(text))
        for package in ["A", "a..b", "a/b", "a-", "1abc", "a\n"]:
            bad.append(payload("", [module(package)]))
        for version in ["1.0", "01.0.0", "1.0.0-alpha", "1.0.0+build", "2147483648.0.0", "1.0.0\n"]:
            bad.append(payload("", [module("example.a", version=version)]))
        for value in bad:
            with self.subTest(value=repr(value)[:150]):
                with self.assertRaises(BundleError) as rejected:
                    load_bundle(value)
                self.assertFalse(hasattr(rejected.exception, "diagnostic"))
        self.assertEqual(load_bundle(payload("", [module("a.b-c_d", version="2147483647.0.1")]))
                         .modules[0].version, "2147483647.0.1")

    def test_aggregate_source_module_and_filename_boundaries(self):
        half = "é" * (MAX_SOURCE_BYTES // 4)
        at_limit = load_bundle(payload(half, [module("example.a", half)]))
        self.assertEqual(sum(len(unit.raw) for unit in at_limit.units), MAX_SOURCE_BYTES)
        with self.assertRaises(BundleError) as rejected:
            load_bundle(payload(half + "x", [module("example.a", half)]))
        self.assertEqual(rejected.exception.code, "OKA-E-RESOURCE")
        self.assertEqual(len(load_bundle(payload("", [module("p" + str(i)) for i in range(16)])).modules), 16)
        with self.assertRaises(BundleError):
            load_bundle(payload("", [module("p" + str(i)) for i in range(17)]))
        self.assertEqual(SourceUnit("entry", "é" * 512, b"").filename, "é" * 512)
        with self.assertRaises(BundleError):
            SourceUnit("entry", "é" * 513, b"")

    def test_file_manifest_preserves_bytes_and_ignores_transport_location(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sub").mkdir()
            raw = '// café\r\nontokin "0.2";\r\n'.encode("utf-8")
            (root / "first.ok").write_bytes(raw)
            (root / "sub/second.ok").write_bytes(raw)
            manifest = {"schema_version": "ontokin.files/0.1", "entry": {"filename": "stable.ok", "path": "first.ok"}, "modules": []}
            path = root / "program.json"
            path.write_text(json.dumps(manifest))
            first = load_file_manifest(path)
            manifest["entry"]["path"] = "sub/second.ok"
            path.write_text(json.dumps(manifest))
            second = load_file_manifest(path)
            self.assertEqual(first, second)
            self.assertEqual(first.entry.raw, raw)

    def test_file_path_validation_rejects_escape_symlink_and_nonregular(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            confined = root / "confined"
            confined.mkdir()
            (confined / "ok.ok").write_text("exact")
            (root / "outside.ok").write_bytes(b"\xff")
            (confined / "escape.ok").symlink_to(root / "outside.ok")
            manifest_path = confined / "program.json"
            for name in ["../outside.ok", "./ok.ok", "a/../ok.ok", "/outside.ok", "a\\ok.ok", "a//b.ok",
                         "ok.ok/", "escape.ok", "missing.ok"]:
                manifest_path.write_text(json.dumps({"schema_version": "ontokin.files/0.1",
                    "entry": {"filename": "source.ok", "path": name}, "modules": []}))
                with self.subTest(path=name), self.assertRaises(BundleError):
                    load_file_manifest(manifest_path)
            with self.assertRaises(BundleError):
                load_file_manifest(confined)
            if hasattr(os, "mkfifo"):
                fifo = confined / "pipe.json"
                os.mkfifo(fifo)
                with self.assertRaises(BundleError):
                    load_file_manifest(fifo)

    def test_manifest_json_and_source_bytes_fail_as_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "program.json"
            malformed = [b'{}', b'\xff', b'{"entry":1,"entry":2}', b'{"bad":NaN}', b'[' * 2000 + b']' * 2000]
            for raw in malformed:
                path.write_bytes(raw)
                with self.subTest(raw=raw[:40]), self.assertRaises(BundleError):
                    load_file_manifest(path)
            (root / "invalid.ok").write_bytes(b"\xff")
            path.write_text(json.dumps({"schema_version": "ontokin.files/0.1",
                "entry": {"filename": "invalid.ok", "path": "invalid.ok"}, "modules": []}))
            with self.assertRaises(BundleError) as rejected:
                load_file_manifest(path)
            self.assertFalse(hasattr(rejected.exception, "diagnostic"))


if __name__ == "__main__":
    unittest.main()
