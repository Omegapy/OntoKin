"""Intra-certificate reuse preserves exact claims, dispatch and request work.

The control below is the complete algebra at checkpoint 025, copied without
changing its arithmetic or expression order. It is a test control, not a new
numerical oracle or a relaxation of the frozen source/acceptance corpus.
"""
from contextlib import nullcontext
from fractions import Fraction
from types import FunctionType
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.construction import ConstructionBudget, REACH_PROFILE
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_conformance import algebra_record, ratio
from test_reach_reference_source_batch import prefix


F = Fraction
WIDTH = F(1, 128)
_CERTIFICATE_FOUR = reader._CERTIFICATE_FOUR
_CERTIFICATE_EIGHT = reader._CERTIFICATE_EIGHT
_CERTIFICATE_THIRTY_TWO = reader._CERTIFICATE_THIRTY_TWO
ARC_LIMIT = reader.ARC_LIMIT
_error = reader._error


def original_complete(ha, hs, quantities, position_tolerance, rotation_tolerance, arithmetic, model):
    """Checkpoint 025's exact calculation, including original binding order."""
    q = quantities.__getitem__
    add, mul, div, square = arithmetic.add, arithmetic.mul, arithmetic.div, arithmetic.square
    four, eight, thirty_two = _CERTIFICATE_FOUR, _CERTIFICATE_EIGHT, _CERTIFICATE_THIRTY_TWO
    def require(name, minimum):
        actual = q(name)
        if arithmetic.compare(actual, minimum) < 0:
            _error("OKE-E-CERTIFICATE", "A reported bound understates the required exact sum.",
                   model=model, details={"quantity": name})
        return actual
    radius, vertex = q("landmark_radius_m"), q("local_vertex_error_bound_m")
    angular, acceleration = q("angular_speed_bound_rad_per_s"), q("carrier_acceleration_bound_m_per_s2")
    envelope_angular = q("enclosing_angular_speed_bound_rad_per_s")
    envelope_acceleration = q("enclosing_carrier_acceleration_bound_m_per_s2")
    speed, shift = q("enclosing_carrier_speed_bound_m_per_s"), q("max_endpoint_time_shift_s")
    position_quarter, rotation_quarter = div(position_tolerance, four), div(rotation_tolerance, four)
    for width, a, w in ((ha, acceleration, angular), (hs, envelope_acceleration, envelope_angular)):
        angle, width_squared = mul(w, width), square(width)
        rotation, chord = div(square(angle), four), div(mul(a, width_squared), eight)
        if (arithmetic.compare(angle, ARC_LIMIT) > 0 or arithmetic.compare(rotation, rotation_quarter) > 0
                or arithmetic.compare(add(chord, mul(radius, rotation)), position_quarter) > 0):
            _error("OKE-E-CERTIFICATE", "The supplied key interval violates the mandatory quarter-allocation plan.", model=model)
    arc = q("stored_quaternion_arc_upper_rad")
    if arc > ARC_LIMIT:
        _error("OKE-E-CERTIFICATE", "The supplied stored quaternion arc exceeds the proved local range.", model=model)
    angular_width_squared, width_squared = square(mul(angular, ha)), square(ha)
    difference = require("unit_quaternion_difference_bound", arithmetic.total((
        q("max_endpoint_unit_quaternion_error"), div(angular_width_squared, thirty_two), div(square(arc), eight))))
    if difference > Fraction(1, 2):
        _error("OKE-E-CERTIFICATE", "The supplied quaternion comparison exceeds its proved local range.", model=model)
    require("ideal_rotation_bound_rad", div(angular_width_squared, four))
    chord = div(mul(acceleration, width_squared), eight)
    require("ideal_position_bound_m", chord)
    rotation = require("total_rotation_bound_rad", arithmetic.total((mul(four, difference),
        q("source_numeric_rotation_bound_rad"), q("destination_numeric_rotation_bound_rad"),
        mul(envelope_angular, shift))))
    carrier = require("carrier_position_bound_m", arithmetic.total((q("max_endpoint_position_error_m"),
        chord, q("source_numeric_position_bound_m"), q("destination_numeric_position_bound_m"), mul(speed, shift))))
    total = require("total_position_bound_m", arithmetic.total((carrier, mul(radius, rotation), vertex)))
    if carrier > position_tolerance or total > position_tolerance or rotation > rotation_tolerance:
        _error("OKE-E-NUMERIC-BOUND", "The complete independently checked bound exceeds the requested tolerance.", model=model)
    return {"position_bound_m": total, "rotation_bound_rad": rotation}


# Preserve the original function's module-global resolution too: controls
# observe the current constants and helpers, just as checkpoint 025 did.
baseline_complete_inequality_values = FunctionType(
    original_complete.__code__, reader.__dict__, "baseline_complete_inequality_values")
original_complete = baseline_complete_inequality_values


def inputs(*, ha=WIDTH, hs=WIDTH, changes=None, position=F(.001), rotation=F(.001)):
    record = algebra_record()
    quantities = {name: F(value) for name, value in record.items() if not name.startswith("h_")}
    quantities.update(changes or {})
    return [F(ha), F(hs), quantities, F(position), F(rotation)]


def evaluate(calculation=None, *, work=None, arithmetic=None, operands=None, **kwargs):
    work = Work() if work is None else work
    arithmetic = reader._Bounds(work) if arithmetic is None else arithmetic
    values = inputs(**kwargs) if operands is None else operands
    result = (reader._complete_inequality_values if calculation is None else calculation)(
        *values, arithmetic, None)
    return result, work


def failure_signature(error):
    if isinstance(error, OntoKinError):
        return type(error), error.diagnostic.code, error.diagnostic.message, error.diagnostic.details
    if isinstance(error, ReachAdmissionError):
        return type(error), error.reach_code, str(error), error.details
    return type(error), str(error)


class CertificateTermReuseTests(unittest.TestCase):
    def assert_accounted(self, work):
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.max_cache_entries, 256)
        self.assertEqual(work.record()["cache_entries"], 0)

    def test_equal_quarters_save_complete_real_work_with_identical_results(self):
        expected, control = evaluate(original_complete)
        actual, candidate = evaluate()
        self.assertEqual(actual, expected)
        self.assertLess(candidate.operations, control.operations)
        self.assert_accounted(control)
        self.assert_accounted(candidate)
        print(f"certificate equal quarters: control={control.operations}, candidate={candidate.operations}, "
              f"saved={control.operations - candidate.operations}")

    def test_native_construction_callback_saves_work_in_both_shared_counters(self):
        outcomes = []
        for calculation in (original_complete, None):
            budget = ConstructionBudget()
            budget.profile = REACH_PROFILE
            callback = budget.tick
            work = Work(check=callback)
            result, _ = evaluate(calculation, work=work)
            outcomes.append((result, work.operations, budget.operations))
            self.assertEqual(work.operations, budget.operations)
            self.assertIs(work.external_check, callback)
            self.assertIsNone(budget.check)
            self.assertIsNone(work._source_after_charge)
            self.assert_accounted(work)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])
        self.assertLess(outcomes[1][2], outcomes[0][2])

    def test_native_work_category_inventory_is_independent_of_the_numerical_cache_cap(self):
        outcomes = []
        for calculation in (original_complete, None):
            budget = ConstructionBudget()
            budget.profile = REACH_PROFILE
            work = Work(check=budget.tick)
            work.counts = {f"previous_exact_work_category_{index}": 0 for index in range(289)}
            self.assertEqual(len(work.counts), 289)
            self.assertEqual(work.operations, 0)
            self.assertEqual(sum(work.counts.values()), 0)
            self.assertEqual(work.record()["cache_entries"], 0)
            result, _ = evaluate(calculation, work=work)
            outcomes.append((result, work.operations, budget.operations))
            self.assertGreater(len(work.counts), work.max_cache_entries)
            self.assertEqual(work.operations, budget.operations)
            self.assert_accounted(work)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])
        self.assertLess(outcomes[1][2], outcomes[0][2])

    def test_nested_construction_callback_keeps_the_complete_original_path(self):
        outcomes = []
        for calculation in (original_complete, None):
            checks = []
            budget = ConstructionBudget(check=lambda: checks.append(True))
            budget.profile = REACH_PROFILE
            callback = budget.tick
            work = Work(check=callback)
            result, _ = evaluate(calculation, work=work)
            outcomes.append((result, work.counts, budget.operations, len(checks)))
            self.assertIs(work.external_check, callback)
            self.assertEqual(len(checks), budget.operations)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_unequal_quarter_inputs_keep_the_exact_authored_and_stored_plans(self):
        cases = ({"hs": F(1, 256)}, {"hs": F(1, 64)},
                 {"changes": {"enclosing_angular_speed_bound_rad_per_s": F(1, 2)}},
                 {"changes": {"enclosing_carrier_acceleration_bound_m_per_s2": F(1, 2)}},
                 {"hs": F(1, 256), "changes": {
                     "enclosing_angular_speed_bound_rad_per_s": F(3, 4),
                     "enclosing_carrier_acceleration_bound_m_per_s2": F(3, 2)}})
        for arguments in cases:
            expected, control = evaluate(original_complete, **arguments)
            actual, candidate = evaluate(**arguments)
            with self.subTest(arguments=arguments):
                self.assertEqual(actual, expected)
                self.assertLess(candidate.operations, control.operations)
                self.assert_accounted(candidate)

    def test_larger_enclosing_angular_rate_retains_the_original_rotation_understatement(self):
        # The original record includes W_E=1 in its reported total. Raising
        # W_E without raising that claim must fail, even with a shorter gap.
        outcomes = []
        for calculation in (original_complete, None):
            with self.assertRaises(OntoKinError) as caught:
                evaluate(calculation, hs=F(1, 256), changes={
                    "enclosing_angular_speed_bound_rad_per_s": F(3, 2),
                    "enclosing_carrier_acceleration_bound_m_per_s2": F(3, 2)})
            outcomes.append(failure_signature(caught.exception))
            self.assertEqual(caught.exception.diagnostic.details["quantity"], "total_rotation_bound_rad")
        self.assertEqual(outcomes[0], outcomes[1])

    def test_zero_coefficients_and_distinct_equal_fractions_keep_exact_totals(self):
        for angular, acceleration in ((0, 0), (0, 1), (1, 0), (1, 1)):
            changed = {"angular_speed_bound_rad_per_s": F(angular),
                       "enclosing_angular_speed_bound_rad_per_s": F(angular),
                       "carrier_acceleration_bound_m_per_s2": F(acceleration),
                       "enclosing_carrier_acceleration_bound_m_per_s2": F(acceleration)}
            values = inputs(changes=changed)
            values[0], values[1] = F(1, 128), F(1, 128)
            self.assertIsNot(values[0], values[1])
            expected, control = evaluate(original_complete, operands=values)
            actual, candidate = evaluate(operands=values)
            with self.subTest(angular=angular, acceleration=acceleration):
                self.assertEqual(actual, expected)
                self.assertLess(candidate.operations, control.operations)
                self.assert_accounted(candidate)

    def test_changed_operands_between_calls_cannot_reuse_an_earlier_invocation(self):
        work = Work()
        cases = ({}, {"ha": F(1, 256)},
                 {"changes": {"angular_speed_bound_rad_per_s": F(1, 2)}},
                 {"changes": {"carrier_acceleration_bound_m_per_s2": F(1, 2)}},
                 {"position": F(1, 500), "rotation": F(1, 500)})
        for arguments in cases:
            expected, _ = evaluate(original_complete, **arguments)
            actual, _ = evaluate(work=work, **arguments)
            with self.subTest(arguments=arguments):
                self.assertEqual(actual, expected)
                self.assert_accounted(work)

    def test_explicitly_disabled_admission_is_the_complete_original_calculation(self):
        expected, control = evaluate(original_complete)
        with patch.object(reader, "_certificate_term_native", return_value=False):
            actual, candidate = evaluate()
        self.assertEqual(actual, expected)
        self.assertEqual(candidate.counts, control.counts)
        self.assertEqual(candidate.operations, control.operations)

    def test_every_reported_sum_keeps_its_original_first_rejection(self):
        record = algebra_record()
        names = ("unit_quaternion_difference_bound", "ideal_rotation_bound_rad",
                 "ideal_position_bound_m", "total_rotation_bound_rad",
                 "carrier_position_bound_m", "total_position_bound_m")
        for name in names:
            failures = []
            for calculation in (original_complete, None):
                with self.assertRaises(OntoKinError) as caught:
                    evaluate(calculation, changes={name: F(record[name]) - F(1, 1 << 100)})
                failures.append(failure_signature(caught.exception))
            with self.subTest(quantity=name):
                self.assertEqual(failures[0], failures[1])
                self.assertEqual(failures[1][-1]["quantity"], name)

    def test_quarter_and_final_boundary_failures_match_the_original_exact_checks(self):
        cases = (
            {"ha": F(1)}, {"hs": F(1)},
            {"changes": {"angular_speed_bound_rad_per_s": F(128)}},
            {"changes": {"enclosing_angular_speed_bound_rad_per_s": F(128)}},
            {"changes": {"stored_quaternion_arc_upper_rad": ARC_LIMIT + F(1, 1 << 100)}},
            {"changes": {"unit_quaternion_difference_bound": F(1, 2) + F(1, 1 << 100)}},
            {"position": F(1, 1 << 30)}, {"rotation": F(1, 1 << 30)},
        )
        for arguments in cases:
            outcomes = []
            for calculation in (original_complete, None):
                with self.assertRaises(OntoKinError) as caught:
                    evaluate(calculation, **arguments)
                outcomes.append(failure_signature(caught.exception))
            with self.subTest(arguments=arguments):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_exact_quarter_equality_and_one_rational_increment_remain_distinct(self):
        # With zero angular rate and radius, the position quarter is solely
        # A*h^2/8. All other terms below are exact zero or conservative claims.
        base = {name: F(0) for name in algebra_record() if not name.startswith("h_")}
        base.update({"carrier_acceleration_bound_m_per_s2": F(1),
                     "enclosing_carrier_acceleration_bound_m_per_s2": F(1),
                     "ideal_position_bound_m": F(1, 8),
                     "carrier_position_bound_m": F(1, 8),
                     "total_position_bound_m": F(1, 8)})
        for width, succeeds in ((F(1), True), (F(1) + F(1, 1 << 100), False)):
            outcomes = []
            for calculation in (original_complete, None):
                values = [width, F(1), dict(base), F(1, 2), F(1)]
                if succeeds:
                    outcome, _ = evaluate(calculation, operands=values)
                else:
                    with self.assertRaises(OntoKinError) as caught:
                        evaluate(calculation, operands=values)
                    outcome = failure_signature(caught.exception)
                outcomes.append(outcome)
            with self.subTest(width=width):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_public_width_decoding_rejects_malformed_or_nonpositive_clocks(self):
        bad = (ratio(0), ratio(-1), {"numerator": "2", "denominator": "4"},
               {"numerator": "01", "denominator": "2"},
               {"numerator": "1", "denominator": "0"},
               {"numerator": True, "denominator": "1"})
        for field in ("h_authored_seconds", "h_stored_seconds"):
            for clock in bad:
                with self.subTest(field=field, clock=clock), self.assertRaises(OntoKinError):
                    reader.check_complete_inequalities({**algebra_record(), field: clock},
                        position_tolerance=.001, rotation_tolerance=.001, work=Work())

    def test_narrow_initial_operand_caps_keep_original_error_order_and_details(self):
        for cap in (2, 16, 32, 64, 128, 1024, 32767):
            outcomes = []
            for calculation in (original_complete, None):
                work = Work(max_operand_bits=cap)
                try:
                    result, _ = evaluate(calculation, work=work)
                    outcome = ("passed", result)
                except (OntoKinError, ReachAdmissionError) as error:
                    outcome = ("failed", failure_signature(error))
                outcomes.append((outcome, work.counts, work.operations))
            with self.subTest(cap=cap):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_live_narrowing_before_intrinsic_division_keeps_the_original_guard(self):
        outcomes = []
        for calculation in (original_complete, None):
            work, calls = Work(), []
            def narrow():
                calls.append(True)
                work.max_operand_bits = 2 if len(calls) == 1 else 32768
            work.external_check = narrow
            values = inputs(ha=F(1), hs=F(1), position=F(1), rotation=F(1))
            with self.assertRaises(ReachAdmissionError) as caught:
                evaluate(calculation, work=work, operands=values)
            outcomes.append((failure_signature(caught.exception), len(calls), work.operations))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[1][1], 1)

    def test_every_actual_callback_preserves_cancellation_and_error_identity(self):
        calls = []
        baseline = Work(check=lambda: calls.append(True))
        evaluate(work=baseline)
        self.assertEqual(len(calls), baseline.operations)
        for fail_at in range(1, len(calls) + 1):
            work, seen = Work(), []
            marker = RuntimeError("original certificate term cancellation")
            def cancel():
                seen.append(True)
                if len(seen) == fail_at:
                    raise marker
            work.external_check = cancel
            with self.subTest(callback=fail_at), self.assertRaises(RuntimeError) as caught:
                evaluate(work=work)
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertIs(work.external_check, cancel)
            self.assertEqual(len(seen), fail_at)
            self.assertEqual(work.record()["cache_entries"], 0)

    def test_initial_foreign_arithmetic_keeps_original_operations_and_calls(self):
        for name in ("add", "mul", "div", "square", "op", "bits", "tick", "compare", "total"):
            outcomes = []
            original = getattr(reader._Bounds, name)
            for calculation in (original_complete, None):
                calls = []
                def foreign(owner, *args, **kwargs):
                    calls.append(args)
                    return original(owner, *args, **kwargs)
                with patch.object(reader._Bounds, name, foreign):
                    actual, work = evaluate(calculation)
                outcomes.append((actual, work.counts, calls))
            with self.subTest(method=name):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_initial_foreign_fraction_add_comparison_and_truth_keep_original_calls(self):
        for name in ("__add__", "__gt__", "__bool__"):
            original = getattr(F, name)
            outcomes = []
            for calculation in (original_complete, None):
                calls = []
                def foreign(*args, **kwargs):
                    calls.append(args)
                    return original(*args, **kwargs)
                # Construct the input outside the patch so the comparison
                # covers only the independently checked certificate algebra.
                values = inputs()
                work = Work()
                with patch.object(F, name, foreign):
                    actual, _ = evaluate(calculation, work=work, operands=values)
                outcomes.append((actual, work.counts, calls))
            with self.subTest(method=name):
                self.assertTrue(outcomes[0][2])
                self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_bits_descriptor_runs_only_at_the_original_guard(self):
        marker = RuntimeError("original bits descriptor")
        outcomes = []
        for calculation in (original_complete, None):
            called, checks = [], []
            work = Work(check=lambda: checks.append(True))
            def descriptor(owner):
                called.append(True)
                raise marker
            with patch.object(reader._Bounds, "bits", property(descriptor)), \
                    self.assertRaises(RuntimeError) as caught:
                evaluate(calculation, work=work)
            self.assertIs(caught.exception, marker)
            outcomes.append((len(called), len(checks), work.operations))
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[1], (1, 1, 1))

    def test_foreign_quantity_mapping_keeps_original_reads_and_no_extra_cache(self):
        outcomes = []
        for calculation in (original_complete, None):
            calls = []
            class Quantities(dict):
                def __getitem__(self, name):
                    calls.append(name)
                    return super().__getitem__(name)
            values = inputs()
            values[2] = Quantities(values[2])
            actual, work = evaluate(calculation, operands=values)
            outcomes.append((actual, calls, work.counts))
            self.assert_accounted(work)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_changed_field_helper_keyword_default_declines_before_any_added_dispatch(self):
        defaults = reader._certificate_fraction_fields.__kwdefaults__
        saved = defaults["bits"]
        marker = RuntimeError("foreign certificate field width comparison")
        calls = []
        class ForeignWidth:
            def compare(self, other):
                calls.append(other)
                raise marker
            __lt__ = __le__ = __gt__ = __ge__ = compare
        outcomes = []
        try:
            # Mutate the same dictionary: object identity alone cannot prove
            # the helper still has its original native keyword default.
            defaults["bits"] = ForeignWidth()
            self.assertIs(reader._certificate_fraction_fields.__kwdefaults__, defaults)
            for calculation in (original_complete, None):
                result, work = evaluate(calculation)
                outcomes.append((result, work.counts, work.operations))
        finally:
            defaults["bits"] = saved
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(calls, [])

    def test_mutated_authored_fraction_cannot_borrow_the_previous_exact_term(self):
        for field in ("angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2", "width"):
            values = inputs()
            operand = values[0] if field == "width" else values[2][field]
            old_numerator = operand.numerator
            work, changed = Work(), []
            def mutate():
                if not changed and work.counts.get("independent_exact_compare", 0) == 3:
                    changed.append(True)
                    object.__setattr__(operand, "_numerator", old_numerator * 2)
            work.external_check = mutate
            try:
                with self.subTest(field=field), self.assertRaises(OntoKinError):
                    evaluate(work=work, operands=values)
            finally:
                object.__setattr__(operand, "_numerator", old_numerator)
            self.assertTrue(changed)
            self.assertEqual(work.record()["cache_entries"], 0)

    def test_fresh_reported_field_read_cannot_be_replaced_by_an_earlier_claim(self):
        values, work, changed = inputs(), Work(), []
        def mutate():
            if not changed and work.counts.get("independent_exact_compare", 0) == 3:
                changed.append(True)
                values[2]["ideal_rotation_bound_rad"] = F(0)
        work.external_check = mutate
        with self.assertRaises(OntoKinError) as caught:
            evaluate(work=work, operands=values)
        self.assertEqual(caught.exception.diagnostic.details["quantity"], "ideal_rotation_bound_rad")
        self.assertTrue(changed)

    def test_transient_foreign_fraction_dispatch_cannot_certify_a_native_receipt(self):
        # The first authored angle is changed by a foreign multiply that
        # restores its dispatch before returning. The later original angle is
        # native and nonzero, so the deliberately zero ideal claim must fail.
        outcomes = []
        original_mul = F.__mul__
        for calculation in (original_complete, None):
            values = inputs(changes={"ideal_rotation_bound_rad": F(0)})
            work, installed, dispatched = Work(), [], []
            def foreign(first, last):
                F.__mul__ = original_mul
                dispatched.append((first, last))
                return F(0)
            def replace_once():
                if (not installed and work.counts.get("independent_exact_div", 0) == 2
                        and work.counts.get("independent_exact_mul", 0) == 0):
                    installed.append(True)
                    F.__mul__ = foreign
            work.external_check = replace_once
            try:
                with self.assertRaises(OntoKinError) as caught:
                    evaluate(calculation, work=work, operands=values)
                outcomes.append(failure_signature(caught.exception))
                self.assertEqual(caught.exception.diagnostic.details["quantity"], "ideal_rotation_bound_rad")
            finally:
                F.__mul__ = original_mul
            self.assertEqual(len(installed), 1)
            self.assertEqual(len(dispatched), 1)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_original_external_callback_and_foreign_after_charge_observer_are_preserved(self):
        callbacks, observations = [], []
        work = Work(check=lambda: callbacks.append(work.operations))
        def observer():
            observations.append(work.operations)
        work._source_after_charge = observer
        check = work.external_check
        expected, _ = evaluate(original_complete)
        actual, _ = evaluate(work=work)
        self.assertEqual(actual, expected)
        self.assertIs(work.external_check, check)
        self.assertIs(work._source_after_charge, observer)
        self.assertEqual(callbacks, list(range(work.operations)))
        self.assertEqual(observations, list(range(1, work.operations + 1)))
        self.assert_accounted(work)

    def test_reentrant_calls_keep_separate_operands_on_the_same_or_different_work(self):
        for shared in (False, True):
            work, calls, nested = Work(), [], []
            inner_values = inputs(ha=F(1, 256), hs=F(1, 512),
                                  changes={"angular_speed_bound_rad_per_s": F(1, 2)})
            def reenter():
                calls.append(True)
                if len(calls) == 3:
                    inner_work = work if shared else Work()
                    nested.append(evaluate(work=inner_work, operands=inner_values)[0])
            work.external_check = reenter
            actual, _ = evaluate(work=work)
            expected, _ = evaluate(original_complete)
            inner_expected, _ = evaluate(original_complete, operands=inner_values)
            with self.subTest(shared_work=shared):
                self.assertEqual(actual, expected)
                self.assertEqual(nested, [inner_expected])
                self.assertIs(work.external_check, reenter)
                self.assert_accounted(work)

    def test_failed_invocation_leaves_no_receipt_for_a_later_valid_request(self):
        work = Work()
        with self.assertRaises(OntoKinError):
            evaluate(work=work, changes={"ideal_position_bound_m": F(0)})
        expected, _ = evaluate(original_complete)
        actual, _ = evaluate(work=work)
        self.assertEqual(actual, expected)
        self.assert_accounted(work)

    def test_original_source_prefix_bytes_certificates_and_reports_are_identical(self):
        saved = []
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for control in (True, False):
                scope = (patch.object(reader, "_complete_inequality_values", original_complete)
                         if control else nullcontext())
                with scope:
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                self.assertEqual(compiler.reach_work.operations, sum(compiler.reach_work.counts.values()))
                self.assertLessEqual(compiler.reach_work.record()["cache_entries"], 256)
                outcomes.append((result.data, result.report, compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLessEqual(outcomes[1][2], outcomes[0][2])
                if case == "P09":
                    self.assertLess(outcomes[1][2], outcomes[0][2])
            saved.append(outcomes[0][2] - outcomes[1][2])
            print(f"{case} certificate term prefix: control={outcomes[0][2]}, "
                  f"candidate={outcomes[1][2]}, saved={saved[-1]}")
        self.assertGreater(sum(saved), 0)


if __name__ == "__main__":
    unittest.main()
