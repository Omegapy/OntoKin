"""Group-local decode receipts and fresh equality proofs keep original guards.

These are dedicated development controls for checkpoint 029's proposed field
scope. They compare each transformation with ordinary reader arithmetic and
leave all frozen source fixtures, request limits and release gates unchanged.
"""
from contextlib import ExitStack
from fractions import Fraction as F
import math
import struct
import sys
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.construction import ConstructionBudget, REACH_PROFILE
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_certificate_term_reuse import failure_signature, inputs
from test_reach_certificate_thresholds import MINIMUM_NAMES
from test_reach_conformance import algebra_record


DECODE_ADMISSION = "independent_certificate_decode_admission"
COMPARE_ADMISSION = "independent_certificate_compare_admission"
WIDTH = F(1, 128)


def decoded(values, *, work=None, optimized=True):
    work = Work() if work is None else work
    arithmetic = reader._Bounds(work)
    context = reader._CertificateFieldDecodes.create(arithmetic, values) if optimized else None
    calculate = arithmetic.value if context is None else context.value
    return tuple(calculate(value) for value in values), work, context


def comparisons(pairs, *, work=None, optimized=True):
    work = Work() if work is None else work
    arithmetic = reader._Bounds(work)
    context = reader._CertificateFieldComparisons.create(arithmetic) if optimized else None
    compare = arithmetic.compare if context is None else context.compare
    return tuple(compare(first, last) for first, last in pairs), work, context


def field_controls(*, decode=True, compare=True):
    scope = ExitStack()
    if not decode:
        scope.enter_context(patch.object(reader._CertificateFieldDecodes, "create", return_value=None))
    if not compare:
        scope.enter_context(patch.object(reader._CertificateFieldComparisons, "create", return_value=None))
    return scope


def complete_group(*, decode=True, compare=True, work=None, minimum_change=None, second_member=False):
    work = Work() if work is None else work
    arithmetic = reader._Bounds(work)
    record = algebra_record()
    minima = {name: F(record[name]) for name in MINIMUM_NAMES}
    if minimum_change is not None:
        name, amount = minimum_change
        minima[name] += amount
    with field_controls(decode=decode, compare=compare):
        batch = reader._CertificateBatch(arithmetic, .001, .001)
        batch.add(record, WIDTH, WIDTH, minima, F(0))
        if second_member:
            batch.add(dict(record), WIDTH, WIDTH, dict(minima), F(0))
        values = tuple(next(iter(batch.groups.values()))["quantities"].values())
        batch.flush()
    return (batch.max_position, batch.max_rotation), work, values


class NativeFieldTestCase(unittest.TestCase):
    def assert_accounted(self, work):
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertEqual(work.max_cache_entries, 256)
        self.assertEqual(work.record()["cache_entries"], 0)

    def native_decode(self, values=(1., 1., 1.), *, work=None):
        work = Work() if work is None else work
        arithmetic = reader._Bounds(work)
        context = reader._CertificateFieldDecodes.create(arithmetic, values)
        self.assertIsNotNone(context)
        return context, arithmetic, work

    def native_compare(self, *, work=None):
        work = Work() if work is None else work
        arithmetic = reader._Bounds(work)
        context = reader._CertificateFieldComparisons.create(arithmetic)
        self.assertIsNotNone(context)
        return context, arithmetic, work


class CertificateFieldDecodeTests(NativeFieldTestCase):
    def test_completed_native_duplicates_save_work_after_the_real_admission(self):
        values = (1., 1., 1., .5, .5, .5)
        expected, control, _ = decoded(values, optimized=False)
        actual, candidate, context = decoded(values)
        self.assertIsNotNone(context)
        self.assertEqual(actual, expected)
        self.assertEqual(candidate.counts["independent_bound_decode"], 2)
        self.assertEqual(candidate.counts[DECODE_ADMISSION], 1)
        self.assertEqual(control.operations - candidate.operations, 3)
        self.assertEqual(len({id(value) for value in actual}), len(values))
        self.assert_accounted(candidate)

    def test_signed_zero_and_integer_float_identity_are_separate_receipts(self):
        values = (0., -0., 0., -0., 1, 1., 1, 1., 0, 0)
        actual, work, context = decoded(values)
        self.assertIsNotNone(context)
        self.assertEqual(actual, tuple(F(value) for value in values))
        self.assertEqual(work.counts["independent_bound_decode"], 5)
        self.assertEqual(work.counts[DECODE_ADMISSION], 1)
        self.assertEqual(work.operations, 6)
        self.assertNotEqual(struct.pack(">d", values[0]), struct.pack(">d", values[1]))
        self.assert_accounted(work)

    def test_adjacent_binary64_values_do_not_borrow_each_others_result(self):
        adjacent = float.fromhex("0x1.0000000000001p+0")
        values = (1., adjacent, 1., adjacent)
        actual, work, _ = decoded(values)
        self.assertEqual(actual, (F(1), F(adjacent), F(1), F(adjacent)))
        self.assertNotEqual(actual[0], actual[1])
        self.assertEqual(work.counts["independent_bound_decode"], 2)
        self.assertEqual(work.counts[DECODE_ADMISSION], 1)

    def test_subnormal_and_largest_finite_binary64_keep_exact_fields(self):
        small = float.fromhex("0x0.0000000000001p-1022")
        large = float.fromhex("0x1.fffffffffffffp+1023")
        actual, work, context = decoded((small, large, small, large))
        self.assertIsNotNone(context)
        self.assertEqual(actual, (F(1, 1 << 1074), F(large), F(small), F(large)))
        self.assertEqual(actual[0].denominator.bit_length(), 1075)
        self.assertEqual(work.counts["independent_bound_decode"], 2)
        self.assertEqual(work.counts[DECODE_ADMISSION], 1)

    def test_native_integer_boundary_and_wider_fallback_keep_exact_results(self):
        for bits in (2048, 2049):
            value = (1 << bits) - 1
            values = (value, value, value)
            expected, control, _ = decoded(values, optimized=False)
            actual, candidate, _ = decoded(values)
            with self.subTest(bits=bits):
                self.assertEqual(actual, expected)
                if bits == 2048:
                    self.assertLess(candidate.operations, control.operations)
                else:
                    self.assertEqual(candidate.counts, control.counts)

    def test_invalid_input_domains_decline_without_decoding_or_foreign_calls(self):
        class ForeignFloat(float):
            pass
        class ForeignInteger(int):
            pass
        invalid = (True, F(1), ForeignInteger(1), ForeignFloat(1), -1, -1.,
                   float("nan"), float("inf"), float("-inf"), object())
        for value in invalid:
            work = Work()
            with self.subTest(value_type=type(value).__name__, value=repr(value)):
                self.assertIsNone(reader._CertificateFieldDecodes.create(reader._Bounds(work), (value, value)))
                self.assertEqual(work.operations, 0)
        for values in ([], [1., 1.], (), (1.,) * 22):
            with self.subTest(shape=type(values).__name__, length=len(values)):
                self.assertIsNone(reader._CertificateFieldDecodes.create(reader._Bounds(Work()), values))

    def test_changed_completed_fraction_is_not_used_as_a_decode_receipt(self):
        for field, changed in (("_numerator", 7), ("_denominator", 3), ("_denominator", 0)):
            context, _, work = self.native_decode()
            earlier = context.value(1.)
            object.__setattr__(earlier, field, changed)
            before = work.counts.get("independent_bound_decode", 0)
            with self.subTest(field=field, changed=changed):
                fresh = context.value(1.)
                self.assertEqual(fresh, F(1))
                self.assertIsNot(fresh, earlier)
                self.assertEqual(work.counts["independent_bound_decode"], before + 1)

    def test_returned_reuse_objects_do_not_alias_completed_or_later_results(self):
        context, _, work = self.native_decode((1.,) * 4)
        earlier = context.value(1.)
        borrowed = context.value(1.)
        object.__setattr__(borrowed, "_numerator", 9)
        later = context.value(1.)
        self.assertEqual(earlier, 1)
        self.assertEqual(later, 1)
        self.assertIsNot(earlier, borrowed)
        self.assertIsNot(later, borrowed)
        self.assertIsNot(later, earlier)
        self.assertEqual(work.counts["independent_bound_decode"], 1)
        self.assertEqual(work.counts[DECODE_ADMISSION], 1)

    def test_replaced_or_malformed_receipt_cannot_forge_a_completed_decode(self):
        for alteration in ("fields", "result", "input", "self_consistent", "malformed"):
            context, _, work = self.native_decode()
            completed = context.value(1.)
            key = (float, struct.pack(">d", 1.))
            replacement = {
                "fields": (1., completed, (9, 1)),
                "result": (1., F(9), (1, 1)),
                "input": (2., completed, (1, 1)),
                "self_consistent": (1., F(9), (9, 1)),
                "malformed": [1., completed, (1, 1)],
            }[alteration]
            context.results[key] = replacement
            with self.subTest(alteration=alteration):
                self.assertEqual(context.value(1.), 1)
                self.assertEqual(work.counts["independent_bound_decode"], 2)
                self.assertNotIn(DECODE_ADMISSION, work.counts)

    def test_out_of_order_value_declines_instead_of_matching_a_different_slot(self):
        context, _, work = self.native_decode((1., 2., 1., 2.))
        self.assertEqual(context.value(1.), 1)
        self.assertEqual(context.value(1.), 1)
        self.assertEqual(work.counts["independent_bound_decode"], 2)
        self.assertNotIn(DECODE_ADMISSION, work.counts)

    def test_distinct_contexts_never_reuse_a_preceding_groups_decode(self):
        work, values = Work(), (1., 1., 1.)
        for group in range(2):
            context, _, _ = self.native_decode(values, work=work)
            self.assertEqual(context.value(1.), 1)
            self.assertEqual(work.counts["independent_bound_decode"], group + 1)
            self.assertEqual(context.value(1.), 1)
            self.assertEqual(context.value(1.), 1)
        self.assertEqual(work.counts[DECODE_ADMISSION], 2)
        self.assert_accounted(work)

    def test_failed_admission_retains_the_original_reach_budget_error(self):
        work = Work(max_operations=1)
        context, _, _ = self.native_decode(work=work)
        self.assertEqual(context.value(1.), 1)
        with self.assertRaises(ReachAdmissionError) as caught:
            context.value(1.)
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], 1)
        self.assertEqual(caught.exception.details["consumed"], 2)
        self.assertEqual(work.operations, 1)
        self.assertNotIn(DECODE_ADMISSION, work.counts)

    def test_shared_native_budget_refusal_escapes_before_reach_increment(self):
        budget = ConstructionBudget({"max_operations": 1})
        budget.profile = REACH_PROFILE
        callback = budget.tick
        work = Work(check=callback)
        context, _, _ = self.native_decode(work=work)
        self.assertEqual(context.value(1.), 1)
        with self.assertRaises(OntoKinError) as caught:
            context.value(1.)
        self.assertIs(work.callback_error, caught.exception)
        self.assertIs(work.external_check, callback)
        self.assertEqual(budget.operations, 2)
        self.assertEqual(work.operations, 1)
        self.assertEqual(caught.exception.diagnostic.details["consumed"], 2)

    def test_changed_work_owner_forces_an_actual_decode_on_the_current_owner(self):
        context, arithmetic, old_work = self.native_decode()
        self.assertEqual(context.value(1.), 1)
        new_work = Work()
        arithmetic.work = new_work
        self.assertEqual(context.value(1.), 1)
        self.assertEqual(old_work.operations, 1)
        self.assertEqual(new_work.counts, {"independent_bound_decode": 1})

    def test_transient_foreign_decoder_restoring_dispatch_cannot_seal_its_result(self):
        context, _, work = self.native_decode()
        original, calls = reader._Bounds.value, []
        def foreign(owner, value):
            reader._Bounds.value = original
            calls.append(value)
            owner.tick("foreign_decode")
            return F(9)
        try:
            reader._Bounds.value = foreign
            first = context.value(1.)
            second = context.value(1.)
        finally:
            reader._Bounds.value = original
        self.assertEqual(first, 9)
        self.assertEqual(second, 1)
        self.assertEqual(calls, [1.])
        self.assertEqual(work.counts["independent_bound_decode"], 1)
        self.assertNotIn(DECODE_ADMISSION, work.counts)


class CertificateFieldComparisonTests(NativeFieldTestCase):
    def test_each_fresh_equal_pair_is_proved_after_one_actual_admission(self):
        pairs = ((F(7, 31), F(7, 31)), (F(0), F(0)), (F(11, 47), F(11, 47)))
        expected, control, _ = comparisons(pairs, optimized=False)
        actual, candidate, context = comparisons(pairs)
        self.assertIsNotNone(context)
        self.assertEqual(actual, expected)
        self.assertEqual(actual, (0, 0, 0))
        self.assertEqual(candidate.counts, {COMPARE_ADMISSION: 1})
        self.assertEqual(control.operations - candidate.operations, 2)
        self.assert_accounted(candidate)

    def test_unequal_numerators_and_denominators_retain_ordinary_comparison(self):
        pairs = ((F(1, 2), F(1, 3)), (F(2, 7), F(3, 7)),
                 (F(9, 13), F(8, 13)), (F(-1, 3), F(1, 3)))
        expected, control, _ = comparisons(pairs, optimized=False)
        actual, candidate, _ = comparisons(pairs)
        self.assertEqual(actual, expected)
        self.assertEqual(candidate.counts, control.counts)
        self.assertNotIn(COMPARE_ADMISSION, candidate.counts)

    def test_a_fresh_changed_minimum_cannot_inherit_an_earlier_success(self):
        context, _, work = self.native_compare()
        actual, minimum = F(1, 2), F(1, 2)
        self.assertEqual(context.compare(actual, minimum), 0)
        object.__setattr__(minimum, "_numerator", 3)
        self.assertEqual(context.compare(actual, minimum), -1)
        self.assertEqual(work.counts["independent_exact_compare"], 1)
        self.assertEqual(work.counts[COMPARE_ADMISSION], 1)

    def test_a_fresh_changed_reported_value_cannot_inherit_an_earlier_success(self):
        context, _, work = self.native_compare()
        actual, minimum = F(1, 2), F(1, 2)
        self.assertEqual(context.compare(actual, minimum), 0)
        object.__setattr__(actual, "_denominator", 4)
        self.assertEqual(context.compare(actual, minimum), -1)
        self.assertEqual(work.counts["independent_exact_compare"], 1)

    def test_native_noncanonical_equal_fields_keep_the_ordinary_relation(self):
        a, b = F(1, 2), F(1, 2)
        for value in (a, b):
            object.__setattr__(value, "_numerator", 2)
            object.__setattr__(value, "_denominator", 4)
        actual, _, _ = comparisons(((a, b),))
        self.assertEqual(actual, (reader._Bounds(Work()).compare(a, b),))

    def test_foreign_or_non_fraction_operands_retain_original_decoding(self):
        class ForeignFraction(F):
            pass
        pairs = ((1, 1), (.5, .5), (ForeignFraction(1, 2), ForeignFraction(1, 2)))
        expected, control, _ = comparisons(pairs, optimized=False)
        actual, candidate, _ = comparisons(pairs)
        self.assertEqual(actual, expected)
        self.assertEqual(candidate.counts, control.counts)
        self.assertNotIn(COMPARE_ADMISSION, candidate.counts)

    def test_equal_large_operands_still_require_the_original_cross_product_guard(self):
        a = F((1 << 16384) - 1, (1 << 16385) - 1)
        b = F(a.numerator, a.denominator)
        outcomes = []
        for optimized in (False, True):
            work = Work()
            with self.assertRaises(ReachAdmissionError) as caught:
                comparisons(((a, b),), work=work, optimized=optimized)
            outcomes.append((failure_signature(caught.exception), work.operations, work.counts))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0][0][-1]["consumed"], 32769)
        self.assertEqual(outcomes[0][1], 1)

    def test_live_narrowing_keeps_operand_then_prospective_failure_order(self):
        for cap, expected_charges in ((80, 0), (81, 1)):
            outcomes = []
            for optimized in (False, True):
                work = Work()
                arithmetic = reader._Bounds(work)
                context = reader._CertificateFieldComparisons.create(arithmetic) if optimized else None
                work.max_operand_bits = cap
                compare = arithmetic.compare if context is None else context.compare
                with self.assertRaises(ReachAdmissionError) as caught:
                    compare(F(1, 1 << 80), F(1, 1 << 80))
                outcomes.append((failure_signature(caught.exception), work.operations, work.counts))
            with self.subTest(cap=cap):
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][1], expected_charges)

    def test_original_operand_guard_wins_before_an_exhausted_work_budget(self):
        context, _, work = self.native_compare(work=Work(max_operations=1))
        work.operations, work.counts = 1, {"prior": 1}
        huge = F(1 << 32768)
        with self.assertRaises(ReachAdmissionError) as caught:
            context.compare(huge, F(huge))
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["consumed"], 32769)
        self.assertEqual(work.operations, 1)

    def test_actual_comparison_admission_can_exhaust_the_native_budget(self):
        context, _, work = self.native_compare(work=Work(max_operations=1))
        work.charge("prior")
        with self.assertRaises(ReachAdmissionError) as caught:
            context.compare(F(1, 3), F(1, 3))
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["consumed"], 2)
        self.assertNotIn(COMPARE_ADMISSION, work.counts)
        self.assertEqual(work.operations, 1)

    def test_comparison_contexts_do_not_share_admission_or_claim_state(self):
        work = Work()
        for index in range(2):
            context, _, _ = self.native_compare(work=work)
            self.assertEqual(context.compare(F(1, 3), F(1, 3)), 0)
            self.assertEqual(work.counts[COMPARE_ADMISSION], index + 1)
        self.assertEqual(work.operations, 2)


class CertificateNativeFieldGateTests(NativeFieldTestCase):
    def assert_declined(self, arithmetic):
        self.assertIsNone(reader._CertificateFieldDecodes.create(arithmetic, (1., 1., 1.)))
        self.assertIsNone(reader._CertificateFieldComparisons.create(arithmetic))

    def test_only_the_exact_full_live_operand_domain_admits_omissions(self):
        for limit in (1, 2048, 32767, 32768, 32769):
            work = Work()
            work.max_operand_bits = limit
            arithmetic = reader._Bounds(work)
            with self.subTest(limit=limit):
                if limit == 32768:
                    self.assertIsNotNone(reader._CertificateFieldDecodes.create(arithmetic, (1.,) * 3))
                    self.assertIsNotNone(reader._CertificateFieldComparisons.create(arithmetic))
                else:
                    self.assert_declined(arithmetic)
                self.assertEqual(work.operations, 0)

    def test_native_shared_request_budget_gets_all_real_charges(self):
        for transform, payload in ((decoded, (1., 1., 1.)),
                                   (comparisons, ((F(1, 3), F(1, 3)),) * 3)):
            outcomes = []
            for optimized in (False, True):
                budget = ConstructionBudget()
                budget.profile = REACH_PROFILE
                callback = budget.tick
                work = Work(check=callback)
                result, _, _ = transform(payload, work=work, optimized=optimized)
                self.assertIs(work.external_check, callback)
                self.assertIsNone(work._source_after_charge)
                self.assertEqual(work.operations, budget.operations)
                self.assert_accounted(work)
                outcomes.append((result, work.operations, budget.operations))
            with self.subTest(transform=transform.__name__):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])
                self.assertLess(outcomes[1][2], outcomes[0][2])

    def test_absent_owner_preserves_native_results(self):
        arithmetic = reader._Bounds(None)
        decode = reader._CertificateFieldDecodes.create(arithmetic, (1.,) * 3)
        compare = reader._CertificateFieldComparisons.create(arithmetic)
        self.assertIsNotNone(decode)
        self.assertIsNotNone(compare)
        self.assertEqual(tuple(decode.value(1.) for _ in range(3)), (F(1),) * 3)
        self.assertEqual(compare.compare(F(5, 7), F(5, 7)), 0)

    def test_custom_callbacks_and_existing_observers_keep_original_events(self):
        for transform, payload in ((decoded, (1., 1., 1.)),
                                   (comparisons, ((F(1, 3), F(1, 3)),) * 3)):
            outcomes = []
            for optimized in (False, True):
                work, before, after = Work(), [], []
                def callback():
                    before.append(work.operations)
                def observer():
                    after.append(work.operations)
                work.external_check, work._source_after_charge = callback, observer
                result, _, context = transform(payload, work=work, optimized=optimized)
                self.assertIsNone(context)
                self.assertIs(work.external_check, callback)
                self.assertIs(work._source_after_charge, observer)
                self.assertEqual(before, list(range(work.operations)))
                self.assertEqual(after, list(range(1, work.operations + 1)))
                outcomes.append((result, work.counts, before, after))
            with self.subTest(transform=transform.__name__):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_nested_construction_check_cannot_be_hidden_by_native_tick_identity(self):
        for transform, payload in ((decoded, (1.,) * 3),
                                   (comparisons, ((F(2, 5), F(2, 5)),) * 3)):
            calls = []
            budget = ConstructionBudget(check=lambda: calls.append(True))
            budget.profile = REACH_PROFILE
            work = Work(check=budget.tick)
            _, _, context = transform(payload, work=work)
            self.assertIsNone(context)
            self.assertEqual(len(calls), budget.operations)
            self.assertEqual(work.operations, budget.operations)
            self.assertNotIn(DECODE_ADMISSION, work.counts)
            self.assertNotIn(COMPARE_ADMISSION, work.counts)

    def test_changed_callback_between_operations_keeps_exception_identity(self):
        for kind in ("decode", "compare"):
            marker = RuntimeError("original field fallback callback")
            calls = []
            def stop():
                calls.append(True)
                raise marker
            if kind == "decode":
                context, _, work = self.native_decode()
                context.value(1.)
                operation = lambda: context.value(1.)
            else:
                context, _, work = self.native_compare()
                operation = lambda: context.compare(F(1, 3), F(1, 3))
            before = work.operations
            work.external_check = stop
            with self.subTest(kind=kind), self.assertRaises(RuntimeError) as caught:
                operation()
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertIs(work.external_check, stop)
            self.assertEqual(calls, [True])
            self.assertEqual(work.operations, before)

    def test_changed_after_charge_observer_forces_ordinary_operations(self):
        for kind in ("decode", "compare"):
            observations = []
            if kind == "decode":
                context, _, work = self.native_decode()
                context.value(1.)
                operation = lambda: context.value(1.)
                category = "independent_bound_decode"
            else:
                context, _, work = self.native_compare()
                operation = lambda: context.compare(F(1, 3), F(1, 3))
                category = "independent_exact_compare"
            def observer():
                observations.append(work.operations)
            before = work.operations
            work._source_after_charge = observer
            operation()
            self.assertIs(work._source_after_charge, observer)
            self.assertEqual(observations, [before + 1])
            self.assertEqual(work.operations, before + 1)
            self.assertIn(category, work.counts)
            self.assertNotIn(DECODE_ADMISSION, work.counts)
            self.assertNotIn(COMPARE_ADMISSION, work.counts)

    def test_trace_and_profile_hooks_decline_without_replacing_the_hooks(self):
        for kind, getter, setter in (("trace", sys.gettrace, sys.settrace),
                                     ("profile", sys.getprofile, sys.setprofile)):
            saved, events = getter(), []
            def hook(frame, event, arg):
                if event == "call":
                    events.append(frame.f_code.co_name)
                return hook
            work = Work()
            try:
                setter(hook)
                self.assert_declined(reader._Bounds(work))
                self.assertIs(getter(), hook)
            finally:
                setter(saved)
            with self.subTest(hook=kind):
                self.assertTrue(events)
                self.assertEqual(work.operations, 0)

    def test_math_finiteness_and_bit_encoder_attributes_are_explicitly_pinned(self):
        for module, name in ((math, "isfinite"), (struct, "pack")):
            original, calls = getattr(module, name), []
            def foreign(*args, **kwargs):
                calls.append((args, kwargs))
                return original(*args, **kwargs)
            arithmetic = reader._Bounds(Work())
            with self.subTest(attribute=name), patch.object(module, name, foreign):
                self.assert_declined(arithmetic)
            self.assertEqual(calls, [])

    def test_raw_field_reader_identity_is_pinned_before_invocation(self):
        calls = []
        def foreign(record):
            calls.append(record)
            raise AssertionError("Optional field admission called a foreign raw reader")
        with patch.object(reader, "_certificate_raw_fields", foreign):
            self.assert_declined(reader._Bounds(Work()))
        self.assertEqual(calls, [])

    def test_raw_field_reader_code_and_default_state_are_pinned(self):
        original = reader._certificate_raw_fields
        code, defaults, kwdefaults = original.__code__, original.__defaults__, original.__kwdefaults__
        def foreign(record):
            raise AssertionError("Changed raw reader must not execute during optional admission")
        for change in ("code", "defaults", "kwdefaults"):
            try:
                if change == "code":
                    original.__code__ = foreign.__code__
                elif change == "defaults":
                    original.__defaults__ = (None,)
                else:
                    original.__kwdefaults__ = {"foreign": object()}
                with self.subTest(change=change):
                    self.assert_declined(reader._Bounds(Work()))
            finally:
                original.__code__, original.__defaults__, original.__kwdefaults__ = code, defaults, kwdefaults

    def test_raw_field_reader_global_key_binding_is_pinned(self):
        keys = reader._NUMERIC_CERTIFICATE_KEYS
        replacement = tuple(list(keys))
        self.assertIsNot(keys, replacement)
        with patch.object(reader, "_NUMERIC_CERTIFICATE_KEYS", replacement):
            self.assert_declined(reader._Bounds(Work()))

    def test_foreign_fraction_properties_are_not_read_during_optional_admission(self):
        for name in ("numerator", "denominator"):
            calls = []
            def foreign(value):
                calls.append(True)
                raise AssertionError("Optional admission read a foreign Fraction property")
            arithmetic = reader._Bounds(Work())
            with self.subTest(property=name), patch.object(F, name, property(foreign)):
                self.assert_declined(arithmetic)
            self.assertEqual(calls, [])

    def test_foreign_arithmetic_work_descriptor_declines_before_property_access(self):
        marker, calls = RuntimeError("foreign work descriptor"), []
        def foreign(arithmetic):
            calls.append(True)
            raise marker
        arithmetic = reader._Bounds(Work())
        with patch.object(reader._Bounds, "work", property(foreign), create=True):
            self.assert_declined(arithmetic)
        self.assertEqual(calls, [])

    def test_foreign_comparison_operand_descriptor_matches_original_failure_order(self):
        marker = RuntimeError("original comparison numerator property")
        outcomes = []
        for optimized in (False, True):
            work, calls = Work(), []
            arithmetic, a, b = reader._Bounds(work), F(1, 3), F(1, 3)
            context = reader._CertificateFieldComparisons.create(arithmetic) if optimized else None
            compare = arithmetic.compare if context is None else context.compare
            def foreign(value):
                calls.append(True)
                raise marker
            with patch.object(F, "numerator", property(foreign)), self.assertRaises(RuntimeError) as caught:
                compare(a, b)
            self.assertIs(caught.exception, marker)
            outcomes.append((len(calls), work.operations, work.counts))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[1], (1, 0, {}))

    def test_foreign_exact_comparison_does_not_disappear_after_admission(self):
        context, _, work = self.native_compare()
        self.assertEqual(context.compare(F(1, 3), F(1, 3)), 0)
        original, calls = reader._Bounds.compare, []
        def foreign(owner, first, last):
            calls.append((first, last))
            return original(owner, first, last)
        with patch.object(reader._Bounds, "compare", foreign):
            self.assertEqual(context.compare(F(1, 3), F(1, 3)), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(work.counts["independent_exact_compare"], 1)

    def test_category_metadata_limit_is_separate_from_numerical_cache_capacity(self):
        for size, admitted in ((289, True), (513, False)):
            work = Work()
            work.counts = {f"prior_{index}": 0 for index in range(size)}
            arithmetic = reader._Bounds(work)
            with self.subTest(categories=size):
                if admitted:
                    self.assertIsNotNone(reader._CertificateFieldDecodes.create(arithmetic, (1.,) * 3))
                    self.assertIsNotNone(reader._CertificateFieldComparisons.create(arithmetic))
                else:
                    self.assert_declined(arithmetic)
                self.assertEqual(work.max_cache_entries, 256)
                self.assertEqual(work.record()["cache_entries"], 0)


    def test_late_trace_cannot_replace_slots_between_optional_filter_checks(self):
        import inspect
        context, arithmetic, work = self.native_compare()
        actual, minimum = F(1, 2), F(1, 3)
        function = reader._CertificateFieldComparisons.compare
        lines, first = inspect.getsourcelines(function)
        target = first + next(index for index, line in enumerate(lines)
                              if 'rn, rd = _FIELD_SLOT_READ' in line)
        original, saved_hook, mutations = F._numerator, sys.gettrace(), []
        marker = RuntimeError("a tracing hook reached an optional slot read")
        def foreign(value):
            raise marker
        def hook(frame, event, arg):
            if frame.f_code is function.__code__ and event == "line" and frame.f_lineno == target:
                mutations.append(True)
                F._numerator = property(foreign)
            return hook
        try:
            sys.settrace(hook)
            self.assertEqual(context.compare(actual, minimum), 1)
            self.assertIs(sys.gettrace(), hook)
        finally:
            sys.settrace(saved_hook)
            F._numerator = original
        self.assertEqual(mutations, [])
        self.assertEqual(work.counts, {"independent_exact_compare": 1})

    def test_late_profile_keeps_the_original_operand_property_exception(self):
        context, arithmetic, work = self.native_compare()
        actual, minimum = F(1, 2), F(1, 3)
        original, saved_hook, calls = F._numerator, sys.getprofile(), []
        marker = RuntimeError("original late-profile operand failure")
        def foreign(value):
            calls.append("field")
            raise marker
        def hook(frame, event, arg):
            if frame.f_code is reader._CertificateFieldComparisons.compare.__code__ and event == "call":
                F._numerator = property(foreign)
        try:
            sys.setprofile(hook)
            with self.assertRaises(RuntimeError) as caught:
                context.compare(actual, minimum)
            self.assertIs(caught.exception, marker)
            self.assertIs(sys.getprofile(), hook)
        finally:
            sys.setprofile(saved_hook)
            F._numerator = original
        self.assertEqual(calls, ["field"])
        self.assertEqual(work.counts, {})

    def test_unequal_filter_preserves_foreign_public_and_slot_property_calls(self):
        for name in ("numerator", "_numerator"):
            marker = RuntimeError("original unequal operand property")
            outcomes = []
            for optimized in (False, True):
                context, arithmetic, work = self.native_compare()
                actual, minimum, calls = F(1, 2), F(1, 3), []
                def foreign(value):
                    calls.append("field")
                    raise marker
                with patch.object(F, name, property(foreign)):
                    with self.assertRaises(RuntimeError) as caught:
                        (context.compare if optimized else arithmetic.compare)(actual, minimum)
                self.assertIs(caught.exception, marker)
                outcomes.append((calls, work.counts))
            with self.subTest(property=name):
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1], (["field"], {}))

    def test_unequal_filter_preserves_foreign_attribute_access_sequence(self):
        outcomes = []
        for optimized in (False, True):
            context, arithmetic, work = self.native_compare()
            actual, minimum, calls = F(1, 2), F(1, 3), []
            def foreign(value, name):
                calls.append(name)
                return object.__getattribute__(value, name)
            with patch.object(F, "__getattribute__", foreign):
                result = (context.compare if optimized else arithmetic.compare)(actual, minimum)
            outcomes.append((result, calls, work.counts))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[1][0], 1)
        self.assertEqual(outcomes[1][2], {"independent_exact_compare": 1})

    def test_unequal_filter_does_not_call_replaced_module_readers_or_object(self):
        context, _, work = self.native_compare()
        actual, minimum = F(1, 2), F(1, 3)
        marker = RuntimeError("an optional reader must not run")
        with patch.object(reader, "_certificate_fraction_fields", side_effect=marker) as fields, \
             patch.object(reader, "_certificate_raw_fields", side_effect=marker) as raw, \
             patch.object(reader, "object", create=True) as foreign_object:
            foreign_object.__getattribute__ = lambda *args: (_ for _ in ()).throw(marker)
            self.assertEqual(context.compare(actual, minimum), 1)
            fields.assert_not_called()
            raw.assert_not_called()
        self.assertEqual(work.counts, {"independent_exact_compare": 1})


class CertificateNativeFieldIntegrationTests(NativeFieldTestCase):
    def test_each_transformation_independently_reduces_complete_group_work(self):
        expected, control, _ = complete_group(decode=False, compare=False)
        for decode, compare in ((True, False), (False, True), (True, True)):
            actual, candidate, quantities = complete_group(decode=decode, compare=compare)
            with self.subTest(decode=decode, compare=compare):
                self.assertEqual(actual, expected)
                self.assertLess(candidate.operations, control.operations)
                self.assertEqual(candidate.counts.get(DECODE_ADMISSION, 0), int(decode))
                self.assertEqual(candidate.counts.get(COMPARE_ADMISSION, 0), int(compare))
                self.assertEqual(len({id(value) for value in quantities}), len(quantities))
                self.assert_accounted(candidate)

    def test_flush_and_complete_inequality_requirements_share_one_comparison_admission(self):
        expected, control, _ = complete_group(decode=False, compare=False)
        actual, candidate, _ = complete_group(decode=False, compare=True)
        self.assertEqual(actual, expected)
        self.assertEqual(candidate.counts[COMPARE_ADMISSION], 1)
        self.assertGreater(control.counts["independent_exact_compare"] -
                           candidate.counts["independent_exact_compare"], len(MINIMUM_NAMES))
        self.assertEqual(candidate.counts["independent_exact_mul"], control.counts["independent_exact_mul"])
        self.assertEqual(candidate.counts["independent_exact_div"], control.counts["independent_exact_div"])

    def test_each_fresh_understated_source_requirement_keeps_its_original_rejection(self):
        for name in MINIMUM_NAMES:
            outcomes = []
            for enabled in (False, True):
                with self.assertRaises(OntoKinError) as caught:
                    complete_group(decode=enabled, compare=enabled, minimum_change=(name, F(1, 1 << 100)))
                outcomes.append(failure_signature(caught.exception))
            with self.subTest(quantity=name):
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][-1]["quantity"], name)

    def test_repeated_members_keep_fresh_checks_without_second_decode_or_admission(self):
        one, first, _ = complete_group()
        two, second, _ = complete_group(second_member=True)
        self.assertEqual(two, one)
        self.assertEqual(second.counts[DECODE_ADMISSION], 1)
        self.assertEqual(second.counts[COMPARE_ADMISSION], 1)
        self.assertEqual(second.counts["independent_bound_decode"], first.counts["independent_bound_decode"])
        self.assertEqual(second.counts["independent_certificate_member"], 2)

    def test_foreign_callback_replacing_decode_mid_group_keeps_each_later_dispatch(self):
        outcomes = []
        for enabled in (False, True):
            work, changed, calls = Work(), [], []
            arithmetic = reader._Bounds(work)
            original = arithmetic.value
            def foreign(value):
                calls.append(value)
                return original(value)
            def replace_once():
                if (not changed and work.counts.get("independent_certificate_group", 0) == 1
                        and work.counts.get("independent_bound_decode", 0) == 2):
                    changed.append(True)
                    arithmetic.value = foreign
            work.external_check = replace_once
            with field_controls(decode=enabled, compare=enabled):
                batch = reader._CertificateBatch(arithmetic, .001, .001)
                batch.add(algebra_record(), WIDTH, WIDTH, {}, F(0))
            quantities = tuple(next(iter(batch.groups.values()))["quantities"].values())
            self.assertEqual(changed, [True])
            self.assertEqual(len(calls), len(reader._NUMERIC_CERTIFICATE_KEYS) - 1)
            self.assertNotIn(DECODE_ADMISSION, work.counts)
            outcomes.append((quantities, calls, work.counts))
        self.assertEqual(outcomes[0], outcomes[1])

    def test_a_comparison_context_for_another_arithmetic_owner_is_ignored(self):
        values = inputs()
        expected_work, actual_work, other_work = Work(), Work(), Work()
        expected = reader._complete_inequality_values(*values, reader._Bounds(expected_work), None)
        context = reader._CertificateFieldComparisons.create(reader._Bounds(other_work))
        self.assertIsNotNone(context)
        actual = reader._complete_inequality_values(*inputs(), reader._Bounds(actual_work), None,
                                                   field_comparisons=context)
        self.assertEqual(actual, expected)
        self.assertEqual(actual_work.counts, expected_work.counts)
        self.assertEqual(other_work.operations, 0)


if __name__ == "__main__":
    unittest.main()
