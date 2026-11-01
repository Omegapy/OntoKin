"""Independent C085 workflow reader adversaries; no product runtime oracle."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.compare_keyed_zip_predecessor import compare_glb, packed_exact
from tools.texture_reference import ReferenceError, bundle_identity, digest, sha
from tools.verify_keyed_zip_agent_evidence import inspect_source_pages, replay_edit


class SourcePageEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="ontokin-c085-reader-")
        self.root = Path(self.directory.name)
        (self.root / "agent/retrieved-sources").mkdir(parents=True)
        self.payload = {"schema_version": "ontokin.bundle/0.2",
            "entry": {"filename": "main.ok", "source": "// Original UTF-8 entry: café\n"},
            "modules": [{"package_id": "fixture.library", "version": "1.0.0",
                         "filename": "library.ok", "source": "// Original pinned library\n"}], "assets": []}
        self.revision = bundle_identity(self.payload)[0]
        self.pages, records = [], []
        for offset, (source_id, unit) in enumerate((
                ("entry", self.payload["entry"]),
                ("package:fixture.library@1.0.0", self.payload["modules"][0]))):
            raw = unit["source"].encode("utf-8")
            request = {"operation": "inspect", "request_id": f"source-{offset}",
                "program_revision": self.revision, "selector": {"kind": "source"},
                "fields": ["identity", "source"], "limit": 1}
            if offset:
                request["cursor"] = "actual-previous-source-cursor"
            self.pages.append({"request": request, "response": {
                "program_revision": self.revision, "truncated": offset == 0,
                "next_cursor": "actual-previous-source-cursor" if offset == 0 else None,
                "result": {"offset": offset, "total": 2, "next_offset": 1 if offset == 0 else None,
                    "truncated": offset == 0, "items": [{"kind": "source", "element_id": ["sources", source_id]}],
                    "source_units": [{"source_id": source_id, "source_revision": digest(raw),
                        "filename": unit["filename"], "source": unit["source"]}]}}})
            path = f"agent/retrieved-sources/unit-{offset:02}.ok"
            (self.root / path).write_bytes(raw)
            records.append({"source_id": source_id, "filename": unit["filename"],
                "source_revision": digest(raw), "program_revision": self.revision,
                "offset": offset, "bytes": len(raw), "sha256": sha(raw), "path": path,
                "request_id": request["request_id"]})
        (self.root / "agent/retrieved-sources.json").write_text(json.dumps(records))

    def tearDown(self):
        self.directory.cleanup()

    def test_exact_complete_source_units_have_distinct_original_identities(self):
        result = inspect_source_pages(self.root, self.pages, self.payload)
        self.assertEqual(len(result), 2)
        self.assertEqual([row["source_id"] for row in result], ["entry", "package:fixture.library@1.0.0"])
        self.assertEqual(result[0]["bytes"], len(self.payload["entry"]["source"].encode("utf-8")))

    def test_forged_source_bytes_filename_digest_and_saved_file_are_rejected(self):
        for field, value in (("source", "changed"), ("filename", "another.ok"),
                             ("source_revision", "sha256:" + "0" * 64)):
            pages = deepcopy(self.pages)
            pages[0]["response"]["result"]["source_units"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ReferenceError):
                inspect_source_pages(self.root, pages, self.payload)
        (self.root / "agent/retrieved-sources/unit-00.ok").write_bytes(b"forged retained bytes")
        with self.assertRaises(ReferenceError):
            inspect_source_pages(self.root, self.pages, self.payload)

    def test_cursor_chain_cardinality_and_terminal_completeness_are_not_trusted(self):
        mutations = []
        pages = deepcopy(self.pages); pages[1]["request"]["cursor"] = "unissued"; mutations.append(pages)
        pages = deepcopy(self.pages); pages[0]["response"]["next_cursor"] = None; mutations.append(pages)
        pages = deepcopy(self.pages); pages[1]["response"]["truncated"] = True; mutations.append(pages)
        pages = deepcopy(self.pages); pages[0]["response"]["result"]["offset"] = 1; mutations.append(pages)
        mutations.append(deepcopy(self.pages[:1]))
        for number, pages in enumerate(mutations):
            with self.subTest(number=number), self.assertRaises(ReferenceError):
                inspect_source_pages(self.root, pages, self.payload)


class AtomicEditReaderTests(unittest.TestCase):
    def setUp(self):
        self.source = "// café\nleft_width = 1[m];\nwarm_finish = false;\n"
        self.payload = {"schema_version": "ontokin.bundle/0.2",
            "entry": {"filename": "main.ok", "source": self.source}, "modules": [], "assets": []}
        raw = self.source.encode("utf-8")
        self.request = {"expected_program_revision": bundle_identity(self.payload)[0], "patches": []}
        for original, replacement in (("left_width = 1[m];", "left_width = 1.5[m];"),
                                       ("warm_finish = false;", "warm_finish = true;")):
            offset = raw.index(original.encode())
            self.request["patches"].append({"source_id": "entry", "element_id": ["sources", "entry"],
                "source_revision": digest(raw), "start_byte": offset, "end_byte": offset + len(original),
                "expected_text": original, "replacement": replacement})

    def test_two_original_utf8_preconditions_apply_as_one_candidate(self):
        result = replay_edit(self.payload, self.request)
        self.assertEqual(result["entry"]["source"], self.source.replace("1[m]", "1.5[m]").replace("false", "true"))
        self.assertEqual(self.payload["entry"]["source"], self.source)

    def test_character_offset_or_recomputed_second_precondition_cannot_pass(self):
        changed = deepcopy(self.request)
        changed["patches"][0]["start_byte"] -= 1
        with self.assertRaises(ReferenceError):
            replay_edit(self.payload, changed)
        changed = deepcopy(self.request)
        changed["patches"][1]["start_byte"] += 2
        changed["patches"][1]["end_byte"] += 2
        with self.assertRaises(ReferenceError):
            replay_edit(self.payload, changed)


class PredecessorCompleteByteTests(unittest.TestCase):
    def setUp(self):
        self.old_basis = {"source": {"name": "synthetic independent test basis",
            "implementation_sha256": "sha256:" + "1" * 64, "derivation_sha256": "sha256:" + "2" * 64},
            "destination": {"implementation_sha256": "sha256:" + "3" * 64,
                            "derivation_sha256": "sha256:" + "4" * 64}}
        self.new_basis = deepcopy(self.old_basis)
        self.new_basis["source"]["implementation_sha256"] = "sha256:" + "5" * 64
        self.new_basis["destination"]["implementation_sha256"] = "sha256:" + "6" * 64
        self.old = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 4}], "extras": {"ontokin": {
            "target_contract": "ontokin.glb/0.17", "program": {"revision": "same-source",
                "manifest": {"first": 1, "second": 2}}, "provenance": [{"origin": "a"}, {"origin": "b"}],
            "reach_quantization": {"source_numeric_bound_basis": deepcopy(self.old_basis["source"]),
                "destination_numeric_bound_basis": deepcopy(self.old_basis["destination"])}}}}
        self.new = deepcopy(self.old)
        self.new["extras"]["ontokin"]["reach_quantization"] = {
            "source_numeric_bound_basis": deepcopy(self.new_basis["source"]),
            "destination_numeric_bound_basis": deepcopy(self.new_basis["destination"])}
        self.binary = b"\x00\x01\x02\x03"
        self.previous = packed_exact(self.old, self.binary)

    def compare(self, document, binary=None):
        return compare_glb(self.previous, packed_exact(document, self.binary if binary is None else binary),
            self.old_basis, self.new_basis, target="ontokin.glb/0.17")

    def test_exact_and_only_independently_bound_numeric_leaf_changes(self):
        exact = compare_glb(self.previous, self.previous, self.old_basis, self.old_basis, target="ontokin.glb/0.17")
        self.assertEqual(exact["comparison"], "exact")
        changed = self.compare(self.new)
        self.assertEqual(changed["comparison"], "fingerprint_only")
        self.assertEqual(len(changed["permitted_json_differences"]), 2)

    def test_unknown_metadata_provenance_source_and_derivation_changes_refuse(self):
        for mutation in ("unknown", "provenance", "source", "derivation"):
            document = deepcopy(self.new); meta = document["extras"]["ontokin"]
            if mutation == "unknown": meta["unknown"] = "preserve me"
            elif mutation == "provenance": meta["provenance"].reverse()
            elif mutation == "source": meta["program"]["revision"] = "another-source"
            else: meta["reach_quantization"]["source_numeric_bound_basis"]["derivation_sha256"] = "sha256:" + "0" * 64
            with self.subTest(mutation=mutation), self.assertRaises(ReferenceError):
                self.compare(document)

    def test_member_order_complete_bin_and_unbound_fingerprint_refuse(self):
        reordered = deepcopy(self.new)
        reordered["extras"]["ontokin"]["program"]["manifest"] = {"second": 2, "first": 1}
        with self.assertRaises(ReferenceError): self.compare(reordered)
        with self.assertRaises(ReferenceError): self.compare(self.new, b"\x00\x01\x02\x04")
        forged = deepcopy(self.new)
        forged["extras"]["ontokin"]["reach_quantization"]["destination_numeric_bound_basis"]["implementation_sha256"] = "sha256:" + "0" * 64
        with self.assertRaises(ReferenceError): self.compare(forged)


if __name__ == "__main__":
    unittest.main()
