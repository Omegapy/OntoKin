#!/usr/bin/env python3
"""Authored C261 controls; independent review supplies a separate test author."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("c261_hinge_glb", HERE / "hinge_glb.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
PROOF = ROOT / "docs/engineering/semantic-export-c210/evidence/proof"
UNSET = object()


def decode(raw):
    length = struct.unpack_from("<I", raw, 12)[0]
    return json.loads(raw[20:20 + length]), raw[28 + length:]


def encode(document, binary=b"", text=None):
    text = json.dumps(document, ensure_ascii=False, separators=(",", ":")) if text is None else text
    data = text.encode("utf-8")
    data += b" " * (-len(data) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 28 + len(data) + len(binary)) +
            struct.pack("<II", len(data), 0x4E4F534A) + data +
            struct.pack("<II", len(binary), 0x004E4942) + binary)


class RawHingeControls(unittest.TestCase):
    def setUp(self):
        self.raw = (PROOF / "before.glb").read_bytes()
        self.document, self.binary = decode(self.raw)
        self.meta = self.document["extras"]["ontokin"]
        self.row = self.meta["joints"][0]

    def observe(self):
        return reader.observe_glb_hinges(encode(self.document, self.binary))

    def refusal(self, raw=UNSET, code=None):
        with self.assertRaises(reader.Fault) as found:
            reader.observe_glb_hinges(encode(self.document, self.binary) if raw is UNSET else raw)
        if code:
            self.assertEqual(found.exception.code, code)
        self.assertTrue(found.exception.detail)
        return found.exception

    def test_original_endpoints_and_pointers(self):
        for name in ("before", "after"):
            raw = (PROOF / (name + ".glb")).read_bytes()
            expected, _ = decode(raw)
            report = reader.observe_glb_hinges(raw)
            self.assertEqual(report["artifactSha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(len(report["records"]), 8)
            self.assertEqual(len(report["objects"]), 18)
            for index, record in enumerate(report["records"]):
                self.assertEqual(record["claims"], expected["extras"]["ontokin"]["joints"][index])
                for field in reader.FIELDS:
                    self.assertEqual(record["origins"][field], f"/extras/ontokin/joints/{index}/{field}")

    def test_no_authority_or_invented_site_fields(self):
        report = self.observe()
        for flag in ("historicalInputsBound", "sourceAgreementVerified", "completeC255Semantic",
                     "executionAllowed", "directSiteTableObserved", "jointDefinitionOrSpanObserved"):
            self.assertIs(report[flag], False)
        self.assertNotIn("definitionId", report["records"][0])
        self.assertNotIn("sites", report)

    def test_added_direct_site_table_refuses(self):
        for container in (self.meta, self.meta["program"]):
            container["sites"] = []
            self.refusal(code="UNSUPPORTED")
            del container["sites"]

    def test_changed_initial_limits_and_sign_are_raw_claims(self):
        self.row.update(initial=0.25, limits=[-2, 3], axis=[0, -1, 0])
        claim = self.observe()["records"][0]["claims"]
        self.assertEqual((claim["initial"], claim["limits"], claim["axis"]), (0.25, [-2, 3], [0, -1, 0]))

    def test_all_six_basis_axes(self):
        for component in range(3):
            for sign in (-1, 1):
                axis = [0, 0, 0]; axis[component] = sign
                self.row["axis"] = axis
                self.assertEqual(self.observe()["records"][0]["claims"]["axis"], axis)

    def test_closed_boundaries_and_zero_width(self):
        for low, high, initial in ((-2, 3, -2), (-2, 3, 3), (0.25, 0.25, 0.25)):
            self.row.update(limits=[low, high], initial=initial)
            self.assertEqual(self.observe()["records"][0]["claims"]["initial"], initial)

    def test_negative_zero_retained(self):
        self.row.update(initial=-0.0, axis=[-0.0, 0.0, 1.0])
        claim = self.observe()["records"][0]["claims"]
        self.assertEqual(math.copysign(1, claim["initial"]), -1)
        self.assertEqual(math.copysign(1, claim["axis"][0]), -1)

    def test_bad_axis_shapes_and_values(self):
        for value in ([0, 1], [0, 0, 0], [0, 0, 2], [0.6, 0.8, 0],
                      [True, 0, 0], ["0", 0, 1], [5e-324, 0, 1], None):
            with self.subTest(value=value):
                self.row["axis"] = value; self.refusal()

    def test_bad_limits_and_initial(self):
        for limits, initial in (([1, -1], 0), ([0, 1], -0.1), ([0, 1], 1.1),
                                ([0, True], 0), ([0, 1], True), ([0], 0), (None, 0)):
            with self.subTest(limits=limits, initial=initial):
                self.row.update(limits=limits, initial=initial); self.refusal()

    def test_duplicate_missing_and_extra_fields(self):
        original = copy.deepcopy(self.row)
        del self.row["initial"]; self.refusal()
        self.row.update(original); self.row["definition_id"] = ["invented"]; self.refusal()
        self.row.clear(); self.row.update(original)
        self.meta["joints"].append(copy.deepcopy(self.row)); self.refusal()

    def test_nonhinge_and_profile_refusals(self):
        self.row["kind"] = "fixed"; self.refusal(code="UNSUPPORTED")
        self.row["kind"] = "hinge"
        for field in ("target_contract", "schema_version", "profile"):
            prior = self.meta[field]; self.meta[field] = "different"
            self.refusal(code="UNSUPPORTED"); self.meta[field] = prior

    def test_row_and_node_reordering(self):
        self.meta["joints"].reverse(); self.document["nodes"].reverse()
        report = self.observe()
        self.assertEqual(report["records"][0]["claims"], self.meta["joints"][0])
        self.assertEqual(report["objects"][0]["claims"]["path"], self.document["nodes"][0]["extras"]["ontokin"]["path"])

    def test_endpoint_order_is_never_inferred(self):
        parent, child = self.row["parent_site"], self.row["child_site"]
        self.row["parent_site"], self.row["child_site"] = child, parent
        claims = self.observe()["records"][0]["claims"]
        self.assertEqual((claims["parent_site"], claims["child_site"]), (child, parent))

    def test_zero_one_128_rows_and_129_refusal(self):
        original = copy.deepcopy(self.row)
        for count in (0, 1, 128):
            self.meta["joints"] = [dict(copy.deepcopy(original), path=f"p{i}.hinge", element_id=["p", str(i)],
                                        parent_site=f"p{i}.a", child_site=f"p{i}.b") for i in range(count)]
            self.assertEqual(len(self.observe()["records"]), count)
        self.meta["joints"].append(dict(copy.deepcopy(original), path="extra", element_id=["extra"]))
        self.refusal(code="RESOURCE_LIMIT")

    def test_untrusted_stale_source_claims(self):
        self.meta["program"]["revision"] = "sha256:" + "0" * 64
        self.meta["source"]["entry_revision"] = "sha256:" + "1" * 64
        report = self.observe()
        self.assertEqual(report["sourceClaims"]["program"]["revision"], "sha256:" + "0" * 64)
        self.assertIs(report["sourceAgreementVerified"], False)

    def test_opaque_punctuation_keys_and_json_pointer_escaping(self):
        self.row["element_id"][-1] = "key.with_-punctuation"
        self.row["path"] = 'part["a.b"].new_name'
        self.assertEqual(self.observe()["records"][0]["claims"]["element_id"][-1], "key.with_-punctuation")
        old = self.document["nodes"][0]["extras"]["ontokin"]["path"]
        new = "a~b/c"
        self.document["nodes"][0]["extras"]["ontokin"]["path"] = new
        occurrences = self.meta["program"]["occurrences"]
        occurrences[new] = occurrences.pop(old)
        self.assertEqual(self.observe()["objects"][0]["origins"]["program_occurrence"],
                         "/extras/ontokin/program/occurrences/a~0b~1c")

    def test_object_duplicate_and_count_refusal(self):
        self.document["nodes"].append(copy.deepcopy(self.document["nodes"][0])); self.refusal()
        self.document["nodes"] = [self.document["nodes"][0]] * 129
        self.refusal(code="RESOURCE_LIMIT")

    def test_span_booleans_fractional_and_range_refuse(self):
        span = self.document["nodes"][0]["extras"]["ontokin"]["source_mapping"]["declaration"]
        for low, high in ((True, 10), (0, 10.0), (-1, 10), (11, 10), (0, 65537)):
            with self.subTest(low=low, high=high):
                span.update(start_byte=low, end_byte=high); self.refusal()

    def test_nested_identity_types_and_sparse_map_nonclaim(self):
        mapping = self.document["nodes"][0]["extras"]["ontokin"]["source_mapping"]
        prior = mapping["definition_id"]
        for value in (None, "wrong", True, []):
            mapping["definition_id"] = value; self.refusal()
        mapping["definition_id"] = prior
        mapping.clear()
        report = self.observe()
        self.assertEqual(report["objects"][0]["claims"]["source_mapping"], {})
        self.assertIs(report["sourceAgreementVerified"], False)

    def test_program_occurrence_refusal_uses_real_pointer(self):
        self.meta["program"]["occurrences"]["first"]["definition"]["start_byte"] = True
        fault = self.refusal()
        self.assertEqual(fault.pointer, "/extras/ontokin/program/occurrences/first/definition")

    def test_text_and_identity_limits(self):
        for value in ("", "a\x85b", "a\ud800b"):
            self.row["path"] = value
            text = json.dumps(self.document, ensure_ascii=True)
            self.refusal(encode(None, self.binary, text))
        self.row["path"] = "a" * 513; self.refusal(code="RESOURCE_LIMIT")
        self.row["path"] = "ok"; self.row["element_id"] = ["a"] * 33
        self.refusal(code="RESOURCE_LIMIT")

    def test_byte_only_input_and_refusal_identity(self):
        for raw in (None, "path.glb", bytearray(self.raw), memoryview(self.raw)):
            with self.subTest(kind=type(raw).__name__):
                self.refusal(raw)
        fault = self.refusal(b"bad")
        self.assertEqual((fault.artifactBytes, fault.artifactSha256), (3, hashlib.sha256(b"bad").hexdigest()))

    def test_truncated_wrong_header_and_extra_chunk(self):
        for raw in (self.raw[:-1], b"bad!" + self.raw[4:], self.raw[:12],
                    struct.pack("<III", 0x46546C67, 1, len(self.raw)) + self.raw[12:]):
            self.refusal(raw)
        appended = self.raw + struct.pack("<II", 0, 0x004E4942)
        appended = appended[:8] + struct.pack("<I", len(appended)) + appended[12:]
        self.refusal(appended)

    def test_chunk_alignment_order_and_utf8(self):
        for raw in (self.raw[:12] + struct.pack("<II", 1, 0x4E4F534A) + self.raw[20:],
                    self.raw[:16] + struct.pack("<I", 0x004E4942) + self.raw[20:],
                    self.raw[:20] + b"\xff" + self.raw[21:]):
            self.refusal(raw)

    def test_json_shape_duplicate_and_nonfinite(self):
        for text in ("[]", '{"asset":{},"asset":{}}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}'):
            self.refusal(encode(None, text=text))

    def test_numeric_lexeme_and_exponent_boundaries(self):
        text = json.dumps(self.document, separators=(",", ":"))
        for value in ("1" * 65, "1e401", "0e-401", "1e309", "1e-325", "1.7976931348623159e308"):
            candidate = text.replace('"initial":0.0', '"initial":' + value, 1)
            self.refusal(encode(None, self.binary, candidate))
        for value in ("0e400", "0e-400", "1e-324", "5e-324"):
            candidate = text.replace('"initial":0.0', '"initial":' + value, 1)
            report = reader.observe_glb_hinges(encode(None, self.binary, candidate))
            self.assertEqual(report["records"][0]["claims"]["initial"], float(value))

    def test_glb_json_and_depth_resource_limits(self):
        self.refusal(b"x" * (reader.MAX_GLB_BYTES + 1), code="RESOURCE_LIMIT")
        self.refusal(encode(None, text=" " * (reader.MAX_JSON_BYTES + 4)), code="RESOURCE_LIMIT")
        self.refusal(encode(None, text="[" * 33 + "0" + "]" * 33), code="RESOURCE_LIMIT")

    def test_unrelated_geometry_follow_motion_claims_do_not_supply_hinges(self):
        before = copy.deepcopy(self.row)
        self.meta["follows"] = ["not evaluated"]
        self.meta["motion_authority"] = "not evaluated"
        self.document["nodes"][0]["extras"]["ontokin"]["geometry"] = {"size": [10, 20, 30]}
        self.assertEqual(self.observe()["records"][0]["claims"], before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
