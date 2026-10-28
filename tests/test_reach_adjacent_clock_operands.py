"""Adjacent independent clocks retain exact operands and original failures."""
from contextlib import ExitStack, nullcontext
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_reference_source_batch import prefix


def original(arithmetic, left, right, raw_left, raw_right):
    """The complete original interval setup, in its original operation order."""
    stored_left, stored_right = arithmetic.value(raw_left), arithmetic.value(raw_right)
    width, stored_width = arithmetic.sub(right, left), arithmetic.sub(stored_right, stored_left)
    shift = max(abs(arithmetic.sub(left, stored_left)), abs(arithmetic.sub(right, stored_right)))
    return stored_left, stored_right, width, stored_width, shift


def prepared(*, check=None, cap=32768, bounds_type=reader._Bounds, work_type=Work):
    work = work_type(check=check, max_operand_bits=cap)
    arithmetic = bounds_type(work, cache_intermediates=False)
    clocks = reader._AdjacentClockOperands(arithmetic)
    left, middle, right = F(0), F(1, 10), F(1, 5)
    clocks.calculate(0, left, middle, 0., .1)
    return clocks, arithmetic, work, middle, right


def ordinary_clocks():
    return patch.object(reader._AdjacentClockOperands, "reuse", return_value=None)


class AdjacentClockOperandTests(unittest.TestCase):
    def assert_receipt_error(self, caught):
        self.assertEqual(caught.exception.diagnostic.details["export_code"],
                         "OKE-E-INDEPENDENT-VALIDATION")

    def test_complete_cold_and_warm_values_equal_the_original_with_two_operations_saved(self):
        clocks, arithmetic, work, middle, right = prepared()
        self.assertEqual(work.operations, 6)
        before, counts = work.operations, dict(work.counts)
        actual = clocks.calculate(1, middle, right, .1, .2)
        control = Work()
        expected = original(reader._Bounds(control), middle, right, .1, .2)
        self.assertEqual(actual, expected)
        self.assertEqual(work.operations - before, 4)
        self.assertEqual(control.operations, 6)
        self.assertEqual(work.counts["independent_bound_decode"] - counts["independent_bound_decode"], 1)
        self.assertEqual(work.counts["independent_exact_sub"] - counts["independent_exact_sub"], 3)
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertEqual(len(work._cache), 0)

    def test_nondyadic_extreme_and_exact_clocks_preserve_all_interval_operands(self):
        for middle, raw_middle in ((F(1, 10), .1), (F(1, 3), 1/3),
                                   (F(1, 1 << 1074), float.fromhex("0x0.0000000000001p-1022")),
                                   (F((1 << 1023) - 1), float.fromhex("0x1p+1023")),
                                   (F(3, 8), .375), (F(-1, 7), -1/7)):
            with self.subTest(middle=middle):
                arithmetic = reader._Bounds(Work())
                clocks = reader._AdjacentClockOperands(arithmetic)
                clocks.calculate(0, F(0), middle, 0., raw_middle)
                right, raw_right = middle + 1, raw_middle
                self.assertEqual(clocks.calculate(1, middle, right, raw_middle, raw_right),
                                 original(reader._Bounds(), middle, right, raw_middle, raw_right))

    def test_only_one_preceding_endpoint_is_retained_without_touching_the_existing_cache(self):
        clocks, arithmetic, work, middle, _ = prepared()
        work._cache[("untouched",)] = (F(7),)
        previous = tuple(work._cache.items())
        for index in range(1, 40):
            right = F(index + 1, 10)
            clocks.calculate(index, middle, right, float(middle), float(right))
            self.assertIs(clocks.previous.authored, right)
            self.assertEqual(clocks.previous.index, index)
            self.assertEqual(tuple(work._cache.items()), previous)
            middle = right
        self.assertEqual(work.max_cache_entries, 256)
        self.assertEqual(work.max_operand_bits, 32768)
        self.assertEqual(work.max_operations, 100000)

    def test_nonadjacent_replaced_authored_and_changed_raw_inputs_take_the_whole_original_path(self):
        for change in ("index", "authored", "raw"):
            clocks, arithmetic, work, middle, right = prepared()
            key, raw = 1, .1
            if change == "index":
                key = 2
            elif change == "authored":
                middle = F(middle.numerator, middle.denominator)
            else:
                raw = math.nextafter(raw, 1.)
            before = work.operations
            self.assertEqual(clocks.calculate(key, middle, right, raw, .2),
                             original(reader._Bounds(), middle, right, raw, .2))
            self.assertEqual(work.operations - before, 6)

    def test_signed_zero_raw_identity_is_not_collapsed_by_numeric_equality(self):
        work = Work()
        clocks = reader._AdjacentClockOperands(reader._Bounds(work))
        middle, right = F(0), F(1)
        clocks.calculate(0, F(-1), middle, -1., 0.)
        before = work.operations
        self.assertEqual(clocks.calculate(1, middle, right, -0., 1.),
                         original(reader._Bounds(), middle, right, -0., 1.))
        self.assertEqual(work.operations - before, 6)

    def test_mutated_completed_fields_before_entry_decline_without_reusing_them(self):
        for target, field, changed in (("stored", "_numerator", 17),
                                        ("stored", "_denominator", 0),
                                        ("difference", "_numerator", True),
                                        ("difference", "_denominator", -1)):
            clocks, arithmetic, work, middle, right = prepared()
            object.__setattr__(getattr(clocks.previous, target), field, changed)
            before = work.operations
            with self.subTest(target=target, field=field):
                self.assertEqual(clocks.calculate(1, middle, right, .1, .2),
                                 original(reader._Bounds(), middle, right, .1, .2))
                self.assertEqual(work.operations - before, 6)

    def test_foreign_native_subclasses_and_wide_authored_inputs_keep_original_operations(self):
        class ForeignBounds(reader._Bounds):
            pass
        class ForeignWork(Work):
            pass
        for bounds_type, work_type in ((ForeignBounds, Work), (reader._Bounds, ForeignWork)):
            clocks, arithmetic, work, middle, right = prepared(bounds_type=bounds_type, work_type=work_type)
            before = work.operations
            self.assertEqual(clocks.calculate(1, middle, right, .1, .2),
                             original(reader._Bounds(), middle, right, .1, .2))
            self.assertEqual(work.operations - before, 6)
            self.assertIsNone(clocks.previous)
        work = Work()
        clocks = reader._AdjacentClockOperands(reader._Bounds(work))
        middle, right = F(1, 1 << 2048), F(1)
        clocks.calculate(0, F(0), middle, 0., 0.)
        before = work.operations
        self.assertEqual(clocks.calculate(1, middle, right, 0., 1.),
                         original(reader._Bounds(), middle, right, 0., 1.))
        self.assertEqual(work.operations - before, 6)
        self.assertIsNone(clocks.previous)

    def test_invalid_raw_values_retain_the_original_diagnostic_and_callback_count(self):
        for value in (True, "0.1", float("inf"), float("nan")):
            observed = []
            for enabled in (False, True):
                clocks, arithmetic, work, middle, right = prepared()
                before = work.operations
                with self.assertRaises(OntoKinError) as caught:
                    if enabled:
                        clocks.calculate(1, middle, right, value, .2)
                    else:
                        original(arithmetic, middle, right, value, .2)
                observed.append((caught.exception.diagnostic.details, work.operations - before))
            self.assertEqual(observed[0], observed[1])

    def test_narrow_initial_and_later_caps_keep_the_complete_original_path(self):
        for initially_narrow in (False, True):
            clocks, arithmetic, work, middle, right = prepared(cap=128 if initially_narrow else 32768)
            work.max_operand_bits = 128
            before = work.operations
            self.assertEqual(clocks.calculate(1, middle, right, .1, .2),
                             original(reader._Bounds(Work(max_operand_bits=128)), middle, right, .1, .2))
            self.assertEqual(work.operations - before, 6)
            self.assertIsNone(clocks.previous)

    def test_changed_work_callback_or_arithmetic_before_entry_cannot_reuse_an_old_owner(self):
        for change in ("work", "external", "arithmetic"):
            clocks, arithmetic, work, middle, right = prepared()
            if change == "work":
                work = arithmetic.work = Work()
            elif change == "external":
                work.external_check = lambda: None
            else:
                clocks.arithmetic = reader._Bounds(work)
            before = work.operations
            self.assertEqual(clocks.calculate(1, middle, right, .1, .2),
                             original(reader._Bounds(), middle, right, .1, .2))
            self.assertEqual(work.operations - before, 6)

    def test_initial_custom_decode_and_subtraction_preserve_the_original_sentinel(self):
        for name in ("value", "sub", "op", "bits", "tick"):
            clocks, arithmetic, work, middle, right = prepared()
            marker = RuntimeError("custom adjacent operand dispatch")
            def fail(*args):
                raise marker
            with patch.object(arithmetic, name, fail), self.assertRaises(RuntimeError) as caught:
                clocks.calculate(1, middle, right, .1, .2)
            self.assertIs(caught.exception, marker)
            self.assertIsNone(clocks.previous)

    def test_dispatch_replaced_by_a_surviving_callback_executes_the_original_fallback(self):
        for target_name, name in (("instance", "sub"), ("class", "sub"), ("instance", "op"),
                                  ("instance", "bits"), ("instance", "tick"),
                                  ("work", "charge"), ("work", "guard_bits"), ("module", "_tick")):
            state, marker = {"armed": False, "calls": 0}, RuntimeError("replaced adjacent dispatch")
            with ExitStack() as patches:
                def fail(*args, **kwargs):
                    raise marker
                def check():
                    if state["armed"]:
                        state["calls"] += 1
                        if state["calls"] == 3:
                            target = {"instance": arithmetic, "class": reader._Bounds,
                                      "work": work, "module": reader}[target_name]
                            patches.enter_context(patch.object(target, name, fail))
                clocks, arithmetic, work, middle, right = prepared(check=check)
                state["armed"] = True
                with self.subTest(target=target_name, name=name), self.assertRaises(RuntimeError) as caught:
                    clocks.calculate(1, middle, right, .1, .2)
                self.assertIs(caught.exception, marker)
                self.assertGreaterEqual(state["calls"], 3)
                self.assertIsNone(clocks.previous)

    def test_every_surviving_cold_and_warm_callback_preserves_cancellation_identity(self):
        for warm, count in ((False, 6), (True, 4)):
            for fail_at in range(1, count + 1):
                state, marker = {"armed": False, "calls": 0}, RuntimeError("adjacent clock cancellation")
                def check():
                    if state["armed"]:
                        state["calls"] += 1
                        if state["calls"] == fail_at:
                            raise marker
                clocks, arithmetic, work, middle, right = prepared(check=check)
                if not warm:
                    clocks.previous = None
                state["armed"] = True
                with self.subTest(warm=warm, fail_at=fail_at), self.assertRaises(RuntimeError) as caught:
                    clocks.calculate(1, middle, right, .1, .2)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(state["calls"], fail_at)
                self.assertIsNone(clocks.previous)

    def test_callback_mutation_of_borrowed_decode_is_an_explicit_receipt_failure(self):
        state = {"armed": False}
        def check():
            if state["armed"]:
                object.__setattr__(saved.stored, "_numerator", saved.stored.numerator + 1)
        clocks, arithmetic, work, middle, right = prepared(check=check)
        saved, before = clocks.previous, work.operations
        state["armed"] = True
        with self.assertRaises(OntoKinError) as caught:
            clocks.calculate(1, middle, right, .1, .2)
        self.assert_receipt_error(caught)
        self.assertEqual(work.operations - before, 1)

    def test_callback_mutation_of_previous_difference_keeps_the_original_left_subtraction(self):
        state = {"armed": False, "calls": 0}
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 1:
                    object.__setattr__(saved.difference, "_numerator", saved.difference.numerator + 1)
        clocks, arithmetic, work, middle, right = prepared(check=check)
        saved, before = clocks.previous, work.operations
        state["armed"] = True
        self.assertEqual(clocks.calculate(1, middle, right, .1, .2),
                         original(reader._Bounds(), middle, right, .1, .2))
        self.assertEqual(work.operations - before, 5)
        self.assertEqual(state["calls"], 5)

    def test_changed_authored_fraction_during_callback_cannot_supply_the_old_difference(self):
        state = {"armed": False, "calls": 0}
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 1:
                    object.__setattr__(middle, "_numerator", 3)
        clocks, arithmetic, work, middle, _ = prepared(check=check)
        right, before = F(2, 5), work.operations
        state["armed"] = True
        actual = clocks.calculate(1, middle, right, .1, .4)
        self.assertEqual(actual, original(reader._Bounds(), middle, right, .1, .4))
        self.assertEqual(work.operations - before, 5)
        self.assertIsNone(clocks.previous)

    def test_callback_owner_or_external_replacement_rejects_the_borrowed_receipt(self):
        for change in ("work", "external", "arithmetic"):
            state = {"armed": False}
            def check():
                if state["armed"]:
                    if change == "work":
                        arithmetic.work = Work()
                    elif change == "external":
                        work.external_check = lambda: None
                    else:
                        clocks.arithmetic = reader._Bounds(work)
            clocks, arithmetic, work, middle, right = prepared(check=check)
            state["armed"] = True
            with self.subTest(change=change), self.assertRaises(OntoKinError) as caught:
                clocks.calculate(1, middle, right, .1, .2)
            self.assert_receipt_error(caught)
            self.assertIsNone(clocks.previous)

    def test_original_callback_exception_precedes_a_changed_receipt_failure(self):
        state, marker = {"armed": False}, RuntimeError("cancel after changing borrowed field")
        def check():
            if state["armed"]:
                object.__setattr__(saved.stored, "_numerator", 123)
                raise marker
        clocks, arithmetic, work, middle, right = prepared(check=check)
        saved = clocks.previous
        state["armed"] = True
        with self.assertRaises(RuntimeError) as caught:
            clocks.calculate(1, middle, right, .1, .2)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)

    def test_temporary_narrow_cap_does_not_guard_borrowed_values_before_the_original_operation(self):
        state = {"armed": False, "calls": 0}
        def check():
            if state["armed"]:
                state["calls"] += 1
                if state["calls"] == 2:
                    work.max_operand_bits = 16
                elif state["calls"] == 3:
                    work.max_operand_bits = 32768
        clocks, arithmetic, work, middle, right = prepared(check=check)
        state["armed"] = True
        self.assertEqual(clocks.calculate(1, middle, right, .1, .2),
                         original(reader._Bounds(), middle, right, .1, .2))
        self.assertEqual(state["calls"], 4)
        self.assertEqual(work.max_operand_bits, 32768)
        self.assertIsNone(clocks.previous)

    def test_narrowed_original_left_subtraction_keeps_its_prospective_guard_and_callback_order(self):
        for cancelled in (False, True):
            state, marker = {"armed": False, "calls": 0}, RuntimeError("original subtraction callback")
            def check():
                if state["armed"]:
                    state["calls"] += 1
                    if state["calls"] == 3:
                        work.max_operand_bits = 1076
                    elif state["calls"] == 4 and cancelled:
                        raise marker
            work = Work(check=check)
            clocks = reader._AdjacentClockOperands(reader._Bounds(work))
            middle, right = F(1), F(2)
            tiny = float.fromhex("0x0.0000000000001p-1022")
            clocks.calculate(0, F(0), middle, 0., tiny)
            state["armed"] = True
            with self.assertRaises(RuntimeError if cancelled else ReachAdmissionError) as caught:
                clocks.calculate(1, middle, right, tiny, 0.)
            self.assertEqual(state["calls"], 4)
            if cancelled:
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
            else:
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                self.assertEqual(caught.exception.details["consumed"], 1077)
            self.assertIsNone(clocks.previous)

    def test_reentrant_calculation_keeps_its_completed_receipt_and_cannot_be_overwritten(self):
        state = {"armed": False, "nested": False, "done": False}
        def check():
            if state["armed"] and not state["nested"] and not state["done"]:
                state["nested"] = True
                clocks.calculate(7, F(7, 10), F(4, 5), .7, .8)
                state["nested"], state["done"] = False, True
        clocks, arithmetic, work, middle, right = prepared(check=check)
        state["armed"] = True
        self.assertEqual(clocks.calculate(1, middle, right, .1, .2),
                         original(reader._Bounds(), middle, right, .1, .2))
        self.assertTrue(state["done"])
        self.assertEqual(clocks.previous.index, 7)
        self.assertEqual(clocks.previous.authored, F(4, 5))

    def test_absolute_shift_is_fresh_and_does_not_expose_the_borrowed_signed_result(self):
        clocks, arithmetic, work, middle, _ = prepared()
        saved = clocks.previous
        result = clocks.calculate(1, middle, F(1, 4), .1, .25)
        expected = F(result[-1].numerator, result[-1].denominator)
        self.assertGreater(expected, 0)
        self.assertIsNot(result[-1], saved.difference)
        object.__setattr__(saved.difference, "_numerator", saved.difference.numerator + 1)
        self.assertEqual(result[-1], expected)

    def test_original_request_operation_cap_is_never_reset_or_replaced(self):
        clocks, arithmetic, work, middle, right = prepared()
        work.max_operations = work.operations + 3
        with self.assertRaises(ReachAdmissionError) as caught:
            clocks.calculate(1, middle, right, .1, .2)
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], 9)
        self.assertEqual(caught.exception.details["consumed"], 10)
        self.assertEqual(work.operations, 9)
        self.assertIsNone(clocks.previous)

    def test_a_new_comparison_attempt_starts_cold_on_the_same_remaining_work(self):
        clocks, arithmetic, work, middle, right = prepared()
        replacement = reader._AdjacentClockOperands(arithmetic)
        before = work.operations
        self.assertEqual(replacement.calculate(1, middle, right, .1, .2),
                         original(reader._Bounds(), middle, right, .1, .2))
        self.assertEqual(work.operations - before, 6)
        self.assertIsNot(replacement.previous, clocks.previous)

    def test_an_existing_foreign_observer_is_never_replaced(self):
        clocks, arithmetic, work, middle, right = prepared()
        calls = []
        observer = lambda: calls.append(work.operations)
        work._source_after_charge = observer
        before = work.operations
        clocks.calculate(1, middle, right, .1, .2)
        self.assertIs(work._source_after_charge, observer)
        self.assertEqual(calls, list(range(before + 1, before + 5)))

    def test_original_prefix_bytes_and_entire_reports_match_with_positive_total_saving(self):
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for enabled in (False, True):
                with nullcontext() if enabled else ordinary_clocks():
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                self.assertEqual(compiler.reach_work.max_cache_entries, 256)
                self.assertEqual(compiler.reach_work.operations, sum(compiler.reach_work.counts.values()))
                outcomes.append((result.data, result.report, compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLess(outcomes[1][2], outcomes[0][2])
            print(f"{case} adjacent clocks complete prefix: original={outcomes[0][2]}, reused={outcomes[1][2]}")


if __name__ == "__main__":
    unittest.main()
