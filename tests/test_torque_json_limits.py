"""Differential checks against the unchanged inherited JSON preflight."""
from __future__ import annotations

import copy
import json
import math
import unittest

from ontokin.json_limits import measure_json
from ontokin.torque_json_limits import measure_response_json


class Sentinel(BaseException):
    pass


class TorqueJSONLimitTests(unittest.TestCase):
    def observe(self, function, value, *, callback=None, **limits):
        calls = []
        def check():
            calls.append(len(calls) + 1)
            if callback is not None:
                callback(len(calls))
        try:
            result = function(value, check=check, **limits)
            return ("return", result, calls)
        except BaseException as error:
            return ("raise", type(error), str(error), getattr(error, "details", None), calls)

    def compare(self, value, **limits):
        expected = self.observe(measure_json, copy.deepcopy(value), **limits)
        actual = self.observe(measure_response_json, copy.deepcopy(value), **limits)
        self.assertEqual(actual, expected)
        return expected

    def test_all_controls_unicode_scalars_and_surrogates(self):
        characters = [chr(value) for value in range(128)] + [
            "\u0080", "\u07ff", "\u0800", "\ud7ff", "\ue000", "\uffff", "\U00010000", "\U0010ffff",
            "\ud800", "\udfff"]
        for character in characters:
            with self.subTest(codepoint=ord(character)):
                value = {"key" + character: "prefix" + character + "suffix", "nested": [character, True, None]}
                control = self.compare(value)
                if control[0] == "return":
                    self.assertEqual(control[1]["bytes"], len(json.dumps(value, ensure_ascii=False,
                        allow_nan=False, separators=(",", ":")).encode("utf-8")))
                # Includes failures before a character, within a UTF-8 scalar,
                # within a six-byte escape and immediately after a callback.
                for limit in range(0, 100):
                    self.compare(value, max_bytes=limit)

    def test_exact_callback_boundaries_and_first_overflow_counts(self):
        for length in (0, 1, 2, 1023, 1024, 1025, 2047, 2048, 2049, 8193):
            base = "a" * length
            variants = [base]
            for index in (0, 1, 1023, 1024, 1025):
                if index < length:
                    for character in ('"', "\\", "\x00", "\n", "\u0800", "\ud800"):
                        variants.append(base[:index] + character + base[index + 1:])
            for value in variants:
                with self.subTest(length=length, special=value.count("a") != length):
                    self.compare(value)
                    for limit in (0, 1, 2, 3, 1024, 1025, 1026, 1027, 2048, 2049, 2050,
                                  max(0, length - 1), length, length + 1, length + 2, length + 3):
                        self.compare(value, max_bytes=limit)

    def test_logical_entries_depth_cycles_and_exact_native_types(self):
        shared = {"a": [1, 2, 3]}
        cycle = []
        cycle.append(cycle)
        nested = 0
        for _ in range(130):
            nested = [nested]
        class ForeignList(list):
            pass
        class ForeignString(str):
            pass
        values = [None, True, False, 0, -1, 0.0, -0.0, 1e300, math.inf, math.nan,
                  1 << 14001, [shared, shared], cycle, nested, ForeignList([1]), ForeignString("a"),
                  {1: "wrong-key"}, (1, "value", {"key": "v"}), ["a"] * 260]
        for value in values:
            self.compare(value)
            for entries in (0, 1, 2, 3, 127, 128, 129, 260, 261):
                self.compare(value, max_entries=entries)
            for depth in (0, 1, 2, 127, 128, 129, 130, 131):
                self.compare(value, max_depth=depth)

    def test_original_callback_exception_object_survives_each_boundary(self):
        value = {"first": "a" * 3073, "second": ["b"] * 200}
        for selected in (1, 2, 3, 4, 5, 6, 7, 8, 50, 128, 200):
            sentinel = Sentinel("same original callback")
            counts = []
            for function in (measure_json, measure_response_json):
                count = [0]
                def callback():
                    count[0] += 1
                    if count[0] == selected:
                        raise sentinel
                with self.assertRaises(Sentinel) as caught:
                    function(value, check=callback)
                self.assertIs(caught.exception, sentinel)
                counts.append(count[0])
            self.assertEqual(counts, [selected, selected])

    def test_callback_container_mutations_keep_original_walk_and_refusals(self):
        for mutation in ("future-value", "new-key", "cycle", "append", "invalid-native"):
            outcomes = []
            for function in (measure_json, measure_response_json):
                value = {"current": "a" * 2049, "future": ["b", "c"]}
                fired = []
                def callback(index):
                    if fired:
                        return
                    fired.append(index)
                    if mutation == "future-value":
                        value["future"] = "\u0800" * 130
                    elif mutation == "new-key":
                        value["added"] = True
                    elif mutation == "cycle":
                        value["future"] = value
                    elif mutation == "append":
                        value["future"].append("z" * 2049)
                    else:
                        value["future"] = object()
                outcomes.append(self.observe(function, value, callback=callback))
            self.assertEqual(outcomes[0], outcomes[1], mutation)


if __name__ == "__main__":
    unittest.main()
