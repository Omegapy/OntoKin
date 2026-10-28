"""Across-container text blocks retain exact wire and request semantics."""
import json
from fractions import Fraction
import unittest
from unittest.mock import patch

from ontokin import json_limits
from ontokin.json_limits import JSONLimitError, measure_json
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def nested_rows():
    return [{"carrier": {"path": "rig.arm", "identity": ["fixture", "rig", "arm"]},
             "clock": {"numerator": str(index), "denominator": "104"},
             "bounds": {"position": 0.0001, "rotation": 0.0002}, "phase": [0]}
            for index in range(97)]


class JSONTraversalBlockTests(unittest.TestCase):
    def assert_wire(self, value, **limits):
        expected = measure_json(value)
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False,
                             separators=(",", ":")).encode("utf-8")
        self.assertEqual(expected["bytes"], len(encoded))
        work = Work()
        self.assertEqual(measure_json(value, work=work, check=work.tick, **limits), expected)
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertLessEqual(len(work._cache), 256)
        return expected, work

    def test_nested_short_text_fills_bounded_blocks_without_early_level_flushes(self):
        value, blocks = nested_rows(), []
        original = json_limits._literal_text_size
        def observed(pending):
            blocks.append(tuple(pending))
            return original(pending)
        with patch.object(json_limits, "_literal_text_size", observed):
            expected, work = self.assert_wire(value)
        self.assertGreater(len(blocks), 1)
        self.assertTrue(all(len(block) == 64 for block in blocks[:-1]))
        self.assertTrue(all(5 <= len(block) <= 64 for block in blocks))
        # No container or its values are cached by the traversal-local buffer.
        self.assertEqual(work._cache, {})
        self.assert_wire(value, max_bytes=expected["bytes"], max_entries=expected["entries"])
        for limits in ({"max_bytes": expected["bytes"] - 1},
                       {"max_entries": expected["entries"] - 1}, {"max_depth": 3}):
            with self.subTest(limits=limits), self.assertRaises(JSONLimitError):
                self.assert_wire(value, **limits)

    def test_long_strings_and_empty_containers_keep_exact_partial_blocks(self):
        values = [
            [["short"] * 31, (), {"empty": []}, ["tail"] * 33, "é😀" * 129],
            [{"quoted\"": ["x", "\\", "\n", "\u0000"]}, [[], (), {}]] * 20,
            ["😀" * 128, {"tail": "x" * 129}, ["literal"] * 63, "last"],
        ]
        for value in values:
            with self.subTest(value=repr(value)[:60]):
                self.assert_wire(value)

    def test_shared_occurrences_and_changed_cached_text_remain_fresh(self):
        shared = {"path": "é中😀", "clock": {"n": "1", "d": "104"},
                  "labels": ["escaped\n", "quoted\"", "slash\\"]}
        value, work = [shared] * 48, Work(max_cache_entries=2)
        for replacement in ("é中😀", "changed\n", "literal", "long" * 129):
            shared["path"] = replacement
            self.assertEqual(measure_json(value, work=work, check=work.tick), measure_json(value))
            self.assertLessEqual(len(work._cache), 2)
        shared["labels"].append(shared)
        with self.assertRaisesRegex(ValueError, "cyclic"):
            measure_json(value, work=work, check=work.tick)

    def test_nested_measurement_uses_its_own_pending_block(self):
        value, nested = nested_rows(), []
        work = Work()
        original = work.charge
        def charged(kind="checkpoint", amount=1):
            if kind == "json_text_batch_domain" and not nested:
                nested.append(None)
                nested_work = Work()
                inner = [{"inner": ["é", "escaped\n", "x"]}] * 41
                nested[0] = measure_json(inner, work=nested_work, check=nested_work.tick)
                self.assertEqual(nested[0], measure_json(inner))
            return original(kind, amount)
        with patch.object(work, "charge", charged):
            self.assertEqual(measure_json(value, work=work, check=work.tick), measure_json(value))
        self.assertEqual(len(nested), 1)

    def test_escaped_blocks_preserve_existing_numeric_cache_values_and_order(self):
        value = nested_rows()
        for index, row in enumerate(value):
            row["carrier"]["path"] = 'rig.arms["left"].part-' + str(index)
            row["carrier"]["identity"].append("é中😀\n")
        expected = measure_json(value)
        for capacity in (1, 2, 256):
            work = Work(max_cache_entries=capacity)
            for index in range(capacity):
                work.remember(("original_numeric", index), Fraction(index + 1, 7))
            before = tuple(work._cache.items())
            generation = work._cache_generation
            cache_counts = {name: work.counts.get(name, 0) for name in
                            ("cache_lookup", "cache_promote", "cache_insert", "cache_evict")}
            with self.subTest(capacity=capacity), \
                    patch.object(work, "lookup", side_effect=AssertionError("JSON read the numeric cache")), \
                    patch.object(work, "remember", side_effect=AssertionError("JSON wrote the numeric cache")):
                for _ in range(2):
                    self.assertEqual(measure_json(value, work=work, check=work.tick), expected)
            after = tuple(work._cache.items())
            self.assertEqual(after, before)
            self.assertTrue(all(old is new for (_, old), (_, new) in zip(before, after)))
            self.assertEqual(work._cache_generation, generation)
            self.assertEqual({name: work.counts.get(name, 0) for name in cache_counts}, cache_counts)
            self.assertGreater(work.counts.get("json_text_block_encode", 0), 0)
            self.assertEqual(work.counts["json_text_block_encode"],
                             work.counts["json_text_block_encode_return"])
            self.assertEqual(work.operations, sum(work.counts.values()))

    def test_cross_container_blocks_preserve_cancellation_identity_and_shared_budget(self):
        value = nested_rows()
        for stage in ("json_text_batch_domain", "json_text_literal_return"):
            work, marker = Work(), RuntimeError("cancel a cross-container JSON block")
            original = work.charge
            def charged(kind="checkpoint", amount=1):
                if kind == stage:
                    work.external_check = lambda: (_ for _ in ()).throw(marker)
                return original(kind, amount)
            with self.subTest(stage=stage), patch.object(work, "charge", charged):
                with self.assertRaises(RuntimeError) as caught:
                    measure_json(value, work=work, check=work.tick)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
        limited = Work(max_operations=1)
        with self.assertRaises(ReachAdmissionError) as caught:
            measure_json(value, work=limited, check=limited.tick)
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], 1)
        self.assertEqual(caught.exception.details["consumed"], 2)


if __name__ == "__main__":
    unittest.main()
