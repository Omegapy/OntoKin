"""Synthetic supplied-byte attacks against the two-leaf regression allowance."""
from copy import deepcopy
import unittest

from tools.compare_keyed_merge_predecessor import compare_glb, packed_exact
from tools.keyed_merge_adversaries import repack_preserving_member_order
from tools.texture_reference import ReferenceError


class PredecessorComparison(unittest.TestCase):
    def setUp(self):
        self.old_basis = {"source": {"name": "synthetic unit-test basis", "implementation_sha256": "sha256:" + "1" * 64,
                                     "derivation_sha256": "sha256:" + "2" * 64},
                          "destination": {"implementation_sha256": "sha256:" + "3" * 64,
                                          "derivation_sha256": "sha256:" + "4" * 64}}
        self.new_basis = deepcopy(self.old_basis)
        self.new_basis["source"]["implementation_sha256"] = "sha256:" + "5" * 64
        self.new_basis["destination"]["implementation_sha256"] = "sha256:" + "6" * 64
        self.old_document = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": 4}],
            "extras": {"ontokin": {"target_contract": "ontokin.glb/0.16",
                "program": {"revision": "same-source", "manifest": {"first": 1, "second": 2}},
                "reach_quantization": {"source_numeric_bound_basis": deepcopy(self.old_basis["source"]),
                                        "destination_numeric_bound_basis": deepcopy(self.old_basis["destination"])},
                "provenance": [{"origin": "a"}, {"origin": "b"}]}}}
        self.new_document = deepcopy(self.old_document)
        self.new_document["extras"]["ontokin"]["reach_quantization"] = {
            "source_numeric_bound_basis": deepcopy(self.new_basis["source"]),
            "destination_numeric_bound_basis": deepcopy(self.new_basis["destination"])}
        self.binary = b"\x00\x01\x02\x03"
        self.previous = packed_exact(self.old_document, self.binary)

    def compare(self, document, binary=None):
        return compare_glb(self.previous, packed_exact(document, self.binary if binary is None else binary),
                           self.old_basis, self.new_basis, target="ontokin.glb/0.16")

    def test_exact_and_independently_bound_fingerprints_are_distinguished(self):
        exact = compare_glb(self.previous, self.previous, self.old_basis, self.old_basis, target="ontokin.glb/0.16")
        self.assertEqual(exact["comparison"], "exact")
        changed = self.compare(self.new_document)
        self.assertEqual(changed["comparison"], "fingerprint_only")
        self.assertEqual(len(changed["permitted_json_differences"]), 2)

    def test_hostile_encoder_retains_unrelated_native_member_order(self):
        document = deepcopy(self.new_document)
        document["extras"]["ontokin"]["program"]["manifest"] = {"second": 2, "first": 1}
        raw = packed_exact(document, self.binary)
        self.assertEqual(repack_preserving_member_order(deepcopy(document), self.binary), raw)
        document["extras"]["ontokin"]["provenance"].reverse()
        changed = repack_preserving_member_order(document, self.binary)
        self.assertNotEqual(raw, changed)
        document["extras"]["ontokin"]["provenance"].reverse()
        self.assertEqual(repack_preserving_member_order(document, self.binary), raw)

    def test_unknown_metadata_and_provenance_order_are_never_suppressed(self):
        for mutation in ("unknown", "provenance", "source", "derivation"):
            document = deepcopy(self.new_document)
            meta = document["extras"]["ontokin"]
            if mutation == "unknown":
                meta["unknown"] = "must remain exact"
            elif mutation == "provenance":
                meta["provenance"].reverse()
            elif mutation == "source":
                meta["program"]["revision"] = "another-source"
            else:
                meta["reach_quantization"]["source_numeric_bound_basis"]["derivation_sha256"] = "sha256:" + "0" * 64
            with self.subTest(mutation=mutation), self.assertRaises(ReferenceError):
                self.compare(document)

    def test_member_order_bin_and_unbound_fingerprint_are_rejected(self):
        reordered = deepcopy(self.new_document)
        reordered["extras"]["ontokin"]["program"]["manifest"] = {"second": 2, "first": 1}
        with self.assertRaises(ReferenceError):
            self.compare(reordered)
        with self.assertRaises(ReferenceError):
            self.compare(self.new_document, b"\x00\x01\x02\x04")
        forged = deepcopy(self.new_document)
        forged["extras"]["ontokin"]["reach_quantization"]["destination_numeric_bound_basis"]["implementation_sha256"] = "sha256:" + "0" * 64
        with self.assertRaises(ReferenceError):
            self.compare(forged)


if __name__ == "__main__":
    unittest.main()
