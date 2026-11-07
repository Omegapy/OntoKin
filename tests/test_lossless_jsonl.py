"""Exact handoff transcript restoration and fail-closed decoder checks."""
import contextlib
import gzip
import importlib.util
import io
import json
import lzma
from pathlib import Path
import tempfile
import unittest


_PATH = Path(__file__).resolve().parents[1] / "tools" / "pack_lossless_jsonl.py"
_SPEC = importlib.util.spec_from_file_location("lossless_jsonl", _PATH)
codec = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(codec)


class LosslessJSONLTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def make(self, raw, *, compressed=False):
        source = self.root / ("input.jsonl.gz" if compressed else "input.jsonl")
        source.write_bytes(gzip.compress(raw, mtime=0) if compressed else raw)
        packed, manifest = self.root / "output.xz", self.root / "manifest.json"
        with contextlib.redirect_stdout(io.StringIO()):
            codec.pack(source, packed, manifest)
        return packed, manifest

    def restore(self, packed, manifest, suffix=""):
        output, report = self.root / ("restored" + suffix), self.root / ("report" + suffix)
        with contextlib.redirect_stdout(io.StringIO()):
            codec.unpack(packed, output, manifest, report)
        return output, report

    def test_exact_unicode_whitespace_number_spellings_and_gzip(self):
        raw = (' { "value" : -0.000E+00, "s":"é😀é\\u0061\\/\\t" }\r\n'
               '{"value":1.234567890123456789012345678901234567890,"s":"é"}\n'
               '[true,false,null,0,1e-0003]\n\n').encode("utf-8")
        packed, manifest = self.make(raw, compressed=True)
        output, report = self.restore(packed, manifest)
        self.assertEqual(output.read_bytes(), raw)
        receipt = json.loads(report.read_bytes())
        self.assertEqual(receipt["status"], "passed")
        self.assertTrue(receipt["every_original_raw_byte_exact"])
        self.assertFalse(receipt["normalization_or_field_removal"])

    def test_empty_stream_and_packet_rollover(self):
        for index, raw in enumerate((b"", b'{"n":1}\n' * (codec.MAX_ROWS + 1))):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                old_root, self.root = self.root, Path(directory)
                try:
                    packed, manifest = self.make(raw)
                    output, _ = self.restore(packed, manifest)
                    self.assertEqual(output.read_bytes(), raw)
                    self.assertEqual(json.loads(manifest.read_bytes())["packets"], 0 if not raw else 2)
                finally:
                    self.root = old_root

    def test_decoder_refuses_structural_and_content_corruption(self):
        packed, manifest = self.make(b'{"id":1}\n{"id":2}\n')
        original_lines = lzma.decompress(packed.read_bytes()).splitlines(keepends=True)
        original_manifest = json.loads(manifest.read_bytes())
        mutations = {
            "duplicate_header_key": lambda rows: [rows[0].replace(b'"max_rows":1024', b'"max_rows":1024,"max_rows":1024'), *rows[1:]],
            "boolean_row_count": lambda rows: [rows[0], rows[1].replace(b'"rows":2', b'"rows":true'), *rows[2:]],
            "unknown_field": lambda rows: [rows[0], rows[1].replace(b'{"rows"', b'{"unknown":0,"rows"'), *rows[2:]],
            "missing_footer": lambda rows: rows[:-1],
            "trailing_packet": lambda rows: [*rows, rows[1]],
            "raw_value_changed": lambda rows: [rows[0], rows[1].replace(b'"1","2"', b'"1","3"'), *rows[2:]],
            "uneven_column": lambda rows: [rows[0], rows[1].replace(b'"1","2"', b'"1"'), *rows[2:]],
        }
        for index, (name, change) in enumerate(mutations.items()):
            with self.subTest(name=name):
                altered = self.root / (name + ".xz")
                altered.write_bytes(lzma.compress(b"".join(change(list(original_lines)))))
                record = {**original_manifest, "packed": {"name": altered.name, **codec.identity(altered)}}
                claim = self.root / (name + ".json")
                claim.write_text(json.dumps(record))
                with self.assertRaises((ValueError, KeyError)):
                    self.restore(altered, claim, str(index))
                self.assertFalse((self.root / ("report" + str(index))).exists())

    def test_packed_identity_and_fresh_destinations_are_required(self):
        packed, manifest = self.make(b'{"id":1}\n')
        output, _ = self.restore(packed, manifest)
        before = output.read_bytes()
        with self.assertRaises(FileExistsError):
            self.restore(packed, manifest)
        self.assertEqual(output.read_bytes(), before)
        packed.write_bytes(packed.read_bytes() + b"corrupt")
        with self.assertRaisesRegex(ValueError, "identity"):
            self.restore(packed, manifest, "corrupt")
        self.assertFalse((self.root / "restoredcorrupt").exists())

    def test_non_utf8_unrecognized_lexemes_and_oversize_line_refuse(self):
        for index, raw in enumerate((b'"\xff"\n', b'{"x":undefined}\n', b" " * (codec.MAX_LINE + 1))):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                old_root, self.root = self.root, Path(directory)
                try:
                    with self.assertRaises((ValueError, UnicodeDecodeError)):
                        self.make(raw)
                    self.assertFalse((self.root / "manifest.json").exists())
                finally:
                    self.root = old_root


if __name__ == "__main__":
    unittest.main()
