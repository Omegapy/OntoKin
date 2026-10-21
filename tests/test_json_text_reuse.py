"""Bounded repeated metadata text keeps the same wire and resource semantics."""
import copy
from fractions import Fraction
import json
import struct
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.gltf import _encode, read_glb
from ontokin.json_limits import JSONLimitError, measure_json
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.scene import BakedNode, BakedScene, ExportOptions, REACH_TARGET


def repeated_rows():
    row = {"left": 0, "right": 1, "carrier": {"path": "rig.arm.é中😀",
           "element_id": ["fixture", "demo", "rig", "arm"]},
           "clock": {"numerator": "1", "denominator": "26"},
           "description": "quotes \" and \\ and\ncontrols\u0000", "error": 1e-8}
    return [copy.deepcopy(row) for _ in range(48)]


class JSONTextReuseTests(unittest.TestCase):
    def test_repeated_nested_metadata_keeps_exact_limits_and_removes_actual_scans(self):
        value = repeated_rows()
        calls = 0
        def counted():
            nonlocal calls
            calls += 1
        expected = measure_json(value, check=counted)
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        self.assertEqual(expected["bytes"], len(encoded.encode("utf-8")))
        work = ReachExecutionWork()
        self.assertEqual(measure_json(value, check=work.tick, work=work), expected)
        start = work.operations
        self.assertEqual(measure_json(value, max_bytes=expected["bytes"],
                                      max_entries=expected["entries"], check=work.tick, work=work), expected)
        self.assertLess(work.operations - start, calls // 2)
        self.assertGreater(work.operations - start, 0)
        for limits in ({"max_bytes": expected["bytes"] - 1}, {"max_entries": expected["entries"] - 1}):
            with self.subTest(limits=limits), self.assertRaises(JSONLimitError):
                measure_json(value, check=work.tick, work=work, **limits)

    def test_changed_strings_and_numbers_are_checked_after_warming_the_cache(self):
        value, work = repeated_rows(), ReachExecutionWork()
        measure_json(value, check=work.tick, work=work)
        value[-1]["carrier"]["path"] = "changed é中😀\n"
        value[-1]["error"] = -0.0
        self.assertEqual(measure_json(value, check=work.tick, work=work), measure_json(value))
        for invalid in ("\ud800", float("nan"), float("inf"), 1 << 14001, object()):
            value[-1]["error"] = invalid
            with self.subTest(value=repr(invalid)[:50]), self.assertRaises(ValueError):
                measure_json(value, check=work.tick, work=work)

    def test_reuse_never_hides_cycles_depth_or_repeated_occurrences(self):
        row, work = repeated_rows()[0], ReachExecutionWork()
        value = [row] * 48
        expected = measure_json(value)
        self.assertEqual(measure_json(value, check=work.tick, work=work), expected)
        with self.assertRaises(JSONLimitError) as caught:
            measure_json(value, max_depth=3, check=work.tick, work=work)
        self.assertEqual(caught.exception.details["budget"], "json_depth")
        row["carrier"]["element_id"].append(row)
        with self.assertRaisesRegex(ValueError, "cyclic"):
            measure_json(value, check=work.tick, work=work)

    def test_long_strings_wide_schemas_and_small_cache_keep_exact_byte_counts(self):
        value = [{"key-" + str(index): ["😀\n" * 129, "x" * 128, str(index)]
                  for index in range(70)} for _ in range(3)]
        work = ReachExecutionWork(max_cache_entries=2)
        expected = measure_json(value)
        self.assertEqual(measure_json(value, check=work.tick, work=work), expected)
        self.assertEqual(measure_json(value, check=work.tick, work=work), expected)
        self.assertLessEqual(work.record()["cache_entries"], 2)

    def test_exactly_full_nested_merge_flushes_before_the_next_scalar(self):
        for left, right in ((1, 63), (31, 33), (32, 32)):
            value = [["left"] * left, ["right"] * right, "following", "scalar"]
            work = ReachExecutionWork()
            with self.subTest(left=left, right=right):
                expected = measure_json(value)
                for _ in range(2):
                    self.assertEqual(measure_json(value, check=work.tick, work=work), expected)
                for key in work._cache:
                    if key[0] == "bounded_json_text_batch_v1":
                        self.assertLessEqual(len(key[1]), 64)

    def test_cached_hits_keep_original_cancellation_and_request_budget(self):
        stopped = False
        interruption = RuntimeError("cancel this original request")
        def check():
            if stopped:
                raise interruption
        value, work = repeated_rows(), ReachExecutionWork(check=check)
        measure_json(value, check=work.tick, work=work)
        stopped = True
        with self.assertRaises(RuntimeError) as caught:
            measure_json(value, check=work.tick, work=work)
        self.assertIs(caught.exception, interruption)
        limited = ReachExecutionWork(max_operations=3)
        with self.assertRaises(ReachAdmissionError) as caught:
            measure_json(value, check=limited.tick, work=limited)
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], 3)
        self.assertEqual(caught.exception.details["consumed"], 4)


class GLBMetadataReuseTests(unittest.TestCase):
    def scene(self):
        node = BakedNode("rig", "rig.frame", None, (1., 1., 1., 1.), {"path": "rig"},
                         [(0., 0., 0.), (1., 0., 0.)], [(0., 0., 0., 1.)] * 2)
        return BakedScene("fixture", "demo", [Fraction(0), Fraction(1)], [0., 1.],
                          [Fraction(0), Fraction(1)], [node], {"records": repeated_rows()},
                          {"exporter": {"version": "test"}}, ExportOptions(helpers=False),
                          contract=REACH_TARGET, schema_version="0.6")

    def test_unchanged_glb_bytes_and_clocks_use_the_original_shared_work(self):
        expected, expected_error = _encode(self.scene())
        work = ReachExecutionWork()
        with patch("ontokin.reach_export._LocalArithmeticWork",
                   side_effect=AssertionError("authored clocks replenished arithmetic work")):
            data, error = _encode(self.scene(), check=work.tick, work=work)
        self.assertEqual((data, error), (expected, expected_error))
        decoded = read_glb(data, check=work.tick, work=work, target_contract=REACH_TARGET)
        self.assertEqual(decoded.document["extras"]["ontokin"]["records"], repeated_rows())
        clocks = decoded.document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]
        self.assertEqual(clocks, [{"numerator": "0", "denominator": "1"},
                                 {"numerator": "1", "denominator": "1"}])
        self.assertGreater(work.record()["counts"]["recording_decimal_result"], 0)

    def test_warm_reader_rejects_changed_invalid_metadata_bytes(self):
        work = ReachExecutionWork()
        data, _ = _encode(self.scene(), check=work.tick, work=work)
        decoded = read_glb(data, check=work.tick, work=work)
        changed = copy.deepcopy(decoded.document)
        changed["extras"]["ontokin"]["records"][-1]["carrier"]["path"] = "\ud800"
        text = json.dumps(changed, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
        text += b" " * (-len(text) % 4)
        binary = decoded.binary
        forged = (struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(binary)) +
                  struct.pack("<II", len(text), 0x4E4F534A) + text +
                  struct.pack("<II", len(binary), 0x004E4942) + binary)
        with self.assertRaises(OntoKinError) as caught:
            read_glb(forged, check=work.tick, work=work)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-GLB-STRUCTURE")


if __name__ == "__main__":
    unittest.main()
