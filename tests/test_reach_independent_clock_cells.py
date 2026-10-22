"""Exact independent clock cells, including live limits and cancellation."""
from fractions import Fraction as F
import struct
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work


def ordinary(value, bits, *, work=None):
    """Select the unchanged rational midpoint calculation."""
    with patch.object(reader, "_integer_clock_cell_contains", return_value=None):
        return reader.clock_cell_contains(value, bits, work=work)


def cell_edges(bits):
    """Use native binary32 decoding, independently of the new integer grid."""
    def decoded(value):
        return F(struct.unpack("<f", struct.pack("<I", value))[0])
    center = decoded(bits)
    lower = F(0) if bits == 0 else (decoded(bits - 1) + center) / 2
    next_value = F(1 << 128) if bits == 0x7f7fffff else decoded(bits + 1)
    return lower, center, (center + next_value) / 2


class ReachIndependentClockCellTests(unittest.TestCase):
    def test_every_exponent_transition_keeps_the_exact_adjacent_cells(self):
        patterns = {0, 1, 2, 0x7f7fffff}
        for exponent in range(1, 255):
            transition = exponent << 23
            patterns.update((transition - 1, transition, transition + 1))
        for bits in sorted(patterns):
            lower, center, upper = cell_edges(bits)
            step = (upper - lower) / 8
            probes = ((lower - step, False), (lower, not bits & 1),
                      (lower + step, True), (center, True),
                      (upper - step, True), (upper, not bits & 1),
                      (upper + step, False))
            for value, expected in probes:
                with self.subTest(bits=hex(bits), value=value):
                    self.assertIs(reader.clock_cell_contains(value, bits), expected)
                    self.assertIs(ordinary(value, bits), expected)

    def test_subnormal_normal_and_overflow_ties_keep_even_parity(self):
        cases = ((F(1, 1 << 150), 0, True),
                 (F(1, 1 << 150), 1, False),
                 (F(3, 1 << 150), 1, False),
                 (F(3, 1 << 150), 2, True),
                 (F((1 << 24) - 1, 1 << 150), 0x007fffff, False),
                 (F((1 << 24) - 1, 1 << 150), 0x00800000, True))
        for value, bits, expected in cases:
            with self.subTest(bits=hex(bits), value=value):
                self.assertIs(reader.clock_cell_contains(value, bits), expected)
        _, _, overflow = cell_edges(0x7f7fffff)
        self.assertTrue(reader.clock_cell_contains(overflow - 1, 0x7f7fffff))
        self.assertFalse(reader.clock_cell_contains(overflow, 0x7f7fffff))
        self.assertFalse(reader.clock_cell_contains(overflow, 0x7f800000))

    def test_source_rational_is_not_first_rounded_through_binary64(self):
        source = F(1) + F(1, 1 << 24) + F(1, 1 << 80)
        self.assertTrue(reader.clock_cell_contains(source, 0x3f800001))
        self.assertFalse(reader.clock_cell_contains(source, 0x3f800000))
        self.assertTrue(ordinary(source, 0x3f800001))
        self.assertFalse(ordinary(source, 0x3f800000))

    def test_largest_fast_source_and_larger_sources_keep_original_results(self):
        cases = ((F((1 << 1023) + 1, 1 << 1023), 0x3f800000, False),
                 (F((1 << 1024) + 1, 1 << 1024), 0x3f800000, True),
                 (float.fromhex("0x1p-1074"), 0, True),
                 (F(1 << 20000), 0x7f7fffff, True))
        for value, bits, fallback in cases:
            with self.subTest(bits=hex(bits), value_type=type(value), fallback=fallback):
                work = Work()
                result = reader.clock_cell_contains(value, bits, work=work)
                self.assertIs(result, ordinary(value, bits, work=Work()))
                self.assertEqual(work.counts.get("independent_exact_div", 0), 1 if bits == 0 and fallback else 2 if fallback else 0)
                self.assertEqual(work.operations, sum(work.counts.values()))
                self.assertFalse(work._cache)

    def test_invalid_bits_and_negative_sources_retain_admission_order(self):
        for bits in (False, True, -1, 0x80000000, 0x7f800000,
                     0x7fc00000, 0x100000000, "1", 1.0, None):
            with self.subTest(bits=bits):
                current, previous = Work(), Work()
                self.assertFalse(reader.clock_cell_contains(F(1), bits, work=current))
                self.assertFalse(ordinary(F(1), bits, work=previous))
                self.assertEqual(current.counts, previous.counts)
                self.assertEqual(current.operations, 2)
        for value in (-1, F(-1, 3), -0.5):
            self.assertFalse(reader.clock_cell_contains(value, 0))
            self.assertFalse(ordinary(value, 0))
        for value in (-0.0, 0.0, 0, F(0)):
            self.assertTrue(reader.clock_cell_contains(value, 0))

    def test_invalid_source_values_keep_the_original_errors(self):
        for value in (False, True, None, "0", (), [],
                      float("nan"), float("inf"), -float("inf")):
            for bits in (0, False):
                with self.subTest(value=value, bits=bits):
                    current, previous = Work(), Work()
                    with self.assertRaises(OntoKinError) as actual:
                        reader.clock_cell_contains(value, bits, work=current)
                    with self.assertRaises(OntoKinError) as expected:
                        ordinary(value, bits, work=previous)
                    self.assertEqual(str(actual.exception), str(expected.exception))
                    self.assertEqual(current.counts, previous.counts)
                    self.assertEqual(current.operations, 2)

    def test_only_removed_midpoint_divisions_and_decodes_reduce_work(self):
        for value, bits, additions, fast_cost, old_cost in (
                (F(0), 0, 1, 5, 7),
                (F(1), 0x3f800000, 2, 6, 10),
                (cell_edges(0x7f7fffff)[1], 0x7f7fffff, 2, 6, 10)):
            with self.subTest(bits=hex(bits)):
                current, previous = Work(), Work()
                self.assertIs(reader.clock_cell_contains(value, bits, work=current),
                              ordinary(value, bits, work=previous))
                self.assertEqual(current.counts, {"independent_clock_cell": 1,
                    "independent_bound_decode": 1, "independent_exact_add": additions,
                    "independent_exact_compare": 2})
                self.assertEqual(current.operations, fast_cost)
                self.assertEqual(previous.operations, old_cost)
                self.assertEqual(current.operations, sum(current.counts.values()))
                self.assertFalse(current._cache)

    def test_narrow_initial_caps_use_the_unchanged_rational_calculation(self):
        for cap in (16, 128, 32767):
            with self.subTest(cap=cap):
                current, previous = Work(max_operand_bits=cap), Work(max_operand_bits=cap)
                if cap == 16:
                    with self.assertRaises(ReachAdmissionError) as actual:
                        reader.clock_cell_contains(F(1), 0x3f800000, work=current)
                    with self.assertRaises(ReachAdmissionError) as expected:
                        ordinary(F(1), 0x3f800000, work=previous)
                    self.assertEqual(actual.exception.details, expected.exception.details)
                else:
                    self.assertIs(reader.clock_cell_contains(F(1), 0x3f800000, work=current),
                                  ordinary(F(1), 0x3f800000, work=previous))
                self.assertEqual(current.counts, previous.counts)

    def test_narrowing_each_new_arithmetic_checkpoint_uses_current_domain(self):
        # Calls 1 and 2 admit the cell and source. Calls 3 through 6 are the
        # two actual midpoint sums and two actual integer comparisons.
        for checkpoint in range(3, 7):
            with self.subTest(checkpoint=checkpoint):
                calls = 0
                work = Work()
                def narrow():
                    nonlocal calls
                    calls += 1
                    if calls == checkpoint:
                        work.max_operand_bits = 128
                work.external_check = narrow
                self.assertTrue(reader.clock_cell_contains(F(1), 0x3f800000, work=work))
                self.assertEqual(work.max_operand_bits, 128)
                self.assertEqual(work.counts["independent_exact_div"], 2)
                self.assertEqual(work.operations, sum(work.counts.values()))
                self.assertFalse(work._cache)

    def test_insufficient_live_caps_fail_in_the_original_arithmetic(self):
        with self.assertRaises(ReachAdmissionError) as expected:
            ordinary(F(1), 0x3f800000, work=Work(max_operand_bits=16))
        for checkpoint in range(3, 7):
            with self.subTest(checkpoint=checkpoint):
                calls = 0
                work = Work()
                def narrow():
                    nonlocal calls
                    calls += 1
                    if calls == checkpoint:
                        work.max_operand_bits = 16
                work.external_check = narrow
                with self.assertRaises(ReachAdmissionError) as actual:
                    reader.clock_cell_contains(F(1), 0x3f800000, work=work)
                self.assertEqual(actual.exception.details, expected.exception.details)
                self.assertEqual(work.max_operand_bits, 16)
                self.assertFalse(work._cache)

    def test_changed_domain_fallback_propagates_the_first_original_failure(self):
        work = Work()
        calls, failures = 0, []
        original_resource = work.resource
        def change_domain():
            nonlocal calls
            calls += 1
            if calls == 3:
                work.max_operand_bits = 128
            elif calls == 4:
                work.max_operand_bits = 16
            elif calls == 5:
                work.max_operand_bits = 32768
        def resource(budget, limit, consumed):
            try:
                return original_resource(budget, limit, consumed)
            except ReachAdmissionError as error:
                failures.append(error)
                raise
        work.external_check = change_domain
        with patch.object(work, "resource", resource):
            with self.assertRaises(ReachAdmissionError) as actual:
                reader.clock_cell_contains(F(1), 0x3f800000, work=work)
        self.assertEqual(len(failures), 1)
        self.assertIs(actual.exception, failures[0])
        self.assertEqual(calls, 4)
        self.assertEqual(work.max_operand_bits, 16)
        self.assertFalse(work._cache)

    def test_cancellation_at_every_new_charge_preserves_exception_and_cache(self):
        for checkpoint in range(3, 7):
            for exception_type in (RuntimeError, ReachAdmissionError):
                with self.subTest(checkpoint=checkpoint, exception_type=exception_type):
                    marker = (ReachAdmissionError("reach_resource", "callback-owned failure")
                              if exception_type is ReachAdmissionError else RuntimeError("cancel clock cell"))
                    work = Work()
                    work.remember(("existing",), (F(3, 5),))
                    cache, operations = tuple(work._cache.items()), work.operations
                    calls = 0
                    def cancel():
                        nonlocal calls
                        calls += 1
                        if calls == checkpoint:
                            raise marker
                    work.external_check = cancel
                    with self.assertRaises(exception_type) as actual:
                        reader.clock_cell_contains(F(1), 0x3f800000, work=work)
                    self.assertIs(actual.exception, marker)
                    self.assertIs(work.callback_error, marker)
                    self.assertEqual(tuple(work._cache.items()), cache)
                    self.assertEqual(work.operations - operations, checkpoint - 1)
                    self.assertEqual(work.operations, sum(work.counts.values()))

    def test_the_original_shared_operation_limit_still_stops_the_last_compare(self):
        work = Work(max_operations=5)
        with self.assertRaises(ReachAdmissionError) as actual:
            reader.clock_cell_contains(F(1), 0x3f800000, work=work)
        self.assertEqual(actual.exception.details["budget"], "max_operations")
        self.assertEqual(actual.exception.details["limit"], 5)
        self.assertEqual(actual.exception.details["consumed"], 6)
        self.assertEqual(work.operations, 5)
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertFalse(work._cache)


if __name__ == "__main__":
    unittest.main()
