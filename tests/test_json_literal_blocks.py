"""Exact literal JSON blocks preserve byte, occurrence and failure bounds."""
import copy
import json
import unittest
from unittest.mock import patch

from ontokin.json_limits import JSONLimitError, measure_json
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def rows():
    return [{"carrier": {"path": "rig.arm", "element_id": ["fixture", "demo", "rig"]},
             "clock": {"numerator": str(index), "denominator": "104"},
             "error": 1e-8, "active": True} for index in range(96)]


class JSONLiteralBlockTests(unittest.TestCase):
    def test_plain_metadata_keeps_wire_counts_and_reduces_work_without_new_cache(self):
        value = rows()
        expected = measure_json(value)
        self.assertEqual(expected["bytes"], len(json.dumps(value, ensure_ascii=False,
            allow_nan=False, separators=(",", ":")).encode()))
        ordinary = Work()
        with patch("ontokin.json_limits._literal_text_size", return_value=None):
            self.assertEqual(measure_json(value, check=ordinary.tick, work=ordinary), expected)
        work = Work()
        self.assertEqual(measure_json(value, check=work.tick, work=work), expected)
        self.assertLess(work.operations, ordinary.operations)
        self.assertGreater(work.counts.get("json_text_literal_return", 0), 0)
        self.assertEqual(len(work._cache), 0)
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.max_cache_entries, 256)

    def test_all_ascii_characters_and_unicode_keep_exact_encoding(self):
        values = [[chr(n) * 128 for n in range(128)],
                  ["", " ", "/", "~", "\x7f"] * 40,
                  ["é", "中", "😀", "\u2028", "\u2029"] * 40,
                  [["plain"] * 31, ["tail"] * 33, "later", "values"]]
        for value in values:
            with self.subTest(first=repr(value[0])[:20]):
                expected = measure_json(value)
                work = Work(max_cache_entries=2)
                for _ in range(2):
                    self.assertEqual(measure_json(value, check=work.tick, work=work), expected)
                self.assertLessEqual(len(work._cache), 2)

    def test_exact_byte_entry_depth_boundaries_and_shared_occurrences(self):
        shared = rows()[0]
        value = [shared] * 40
        expected = measure_json(value)
        work = Work()
        self.assertEqual(measure_json(value, max_bytes=expected["bytes"],
            max_entries=expected["entries"], check=work.tick, work=work), expected)
        for limits in ({"max_bytes": expected["bytes"]-1},
                       {"max_entries": expected["entries"]-1}, {"max_depth": 3}):
            with self.subTest(limits=limits), self.assertRaises(JSONLimitError):
                measure_json(value, check=work.tick, work=work, **limits)
        shared["carrier"]["element_id"].append(shared)
        with self.assertRaisesRegex(ValueError, "cyclic"):
            measure_json(value, check=work.tick, work=work)

    def test_changed_values_after_plain_block_cannot_borrow_a_prior_admission(self):
        value = rows()
        work = Work()
        measure_json(value, check=work.tick, work=work)
        for changed in ("quote\"", "slash\\", "line\n", "é中😀", "x" * 129):
            value[-1]["carrier"]["path"] = changed
            self.assertEqual(measure_json(value, check=work.tick, work=work), measure_json(value))
        for invalid in ("\ud800", float("inf"), float("nan"), 1 << 14001, object()):
            value[-1]["error"] = invalid
            with self.subTest(kind=type(invalid).__name__), self.assertRaises(ValueError):
                measure_json(value, check=work.tick, work=work)

    def test_cancellation_brackets_literal_scan_and_preserves_exception_identity(self):
        value = ["plain-" + str(i) for i in range(64)]
        for stage in ("json_text_batch_domain", "json_text_literal_return"):
            work = Work()
            before = copy.deepcopy(work._cache)
            marker = RuntimeError("cancel literal JSON block")
            original = work.charge
            def charged(kind="checkpoint", amount=1):
                if kind == stage:
                    work.external_check = lambda: (_ for _ in ()).throw(marker)
                return original(kind, amount)
            with self.subTest(stage=stage), patch.object(work, "charge", charged):
                with self.assertRaises(RuntimeError) as caught:
                    measure_json(value, check=work.tick, work=work)
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertEqual(work._cache, before)

    def test_shared_request_operation_limit_is_never_replenished(self):
        work = Work(max_operations=1)
        with self.assertRaises(ReachAdmissionError) as caught:
            measure_json(["literal"] * 64, check=work.tick, work=work)
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], 1)
        self.assertEqual(caught.exception.details["consumed"], 2)
        self.assertEqual(len(work._cache), 0)


if __name__ == "__main__":
    unittest.main()
