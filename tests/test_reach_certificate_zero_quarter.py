"""Exact-zero stored-quarter identity against unchanged checkpoint-026 algebra.

The literal control isolates five proposed zero-operation omissions from the
already accepted authored-term reuse. These are dedicated local controls;
original source fixtures, resource limits and release gates remain unchanged.
"""
from fractions import Fraction
import sys
from types import FunctionType
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.construction import ConstructionBudget, REACH_PROFILE
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_certificate_term_reuse import evaluate, failure_signature, inputs, original_complete


F = Fraction
COEFFICIENTS = (
    "angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
    "enclosing_angular_speed_bound_rad_per_s", "enclosing_carrier_acceleration_bound_m_per_s2",
)
ZERO_NAMES = ("angle", "angle_squared", "rotation", "product", "chord")


def _checkpoint026_complete(ha, hs, quantities, position_tolerance, rotation_tolerance, arithmetic, model):
    """Pure exact algebra after all supplied fields and widths are decoded."""
    q = quantities.__getitem__
    add, mul, div, square = arithmetic.add, arithmetic.mul, arithmetic.div, arithmetic.square
    # These intrinsic rational coefficients need no repeated external-value
    # decoding. Every actual operation still charges and guards both operands,
    # including the coefficient, immediately after its cancellation callback.
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
    terms = _CertificateTermReuse.create(arithmetic, quantities,
        (ha, hs, angular, acceleration, four, eight, position_tolerance,
         rotation_tolerance, position_quarter, rotation_quarter))
    for index, (width, a, w) in enumerate(((ha, acceleration, angular), (hs, envelope_acceleration, envelope_angular))):
        if index == 0 and terms is not None:
            angle = terms.calculate("angle", mul, w, width)
            width_squared = terms.calculate("width_squared", square, width)
            angle_squared = terms.calculate("angle_squared", square, angle)
            rotation = terms.calculate("rotation", div, angle_squared, four)
            product = terms.calculate("product", mul, a, width_squared)
            chord = terms.calculate("chord", div, product, eight)
        else:
            angle, width_squared = mul(w, width), square(width)
            rotation, chord = div(square(angle), four), div(mul(a, width_squared), eight)
        if (arithmetic.compare(angle, ARC_LIMIT) > 0 or arithmetic.compare(rotation, rotation_quarter) > 0
                or arithmetic.compare(add(chord, mul(radius, rotation)), position_quarter) > 0):
            _error("OKE-E-CERTIFICATE", "The supplied key interval violates the mandatory quarter-allocation plan.", model=model)
    arc = q("stored_quaternion_arc_upper_rad")
    if arc > ARC_LIMIT:
        _error("OKE-E-CERTIFICATE", "The supplied stored quaternion arc exceeds the proved local range.", model=model)
    borrowed = terms.borrow("angle", "angle_squared", "width_squared") if terms is not None else None
    if borrowed is None:
        angular_width_squared, width_squared = square(mul(angular, ha)), square(ha)
    else:
        _, angular_width_squared, width_squared = borrowed
    difference = require("unit_quaternion_difference_bound", arithmetic.total((
        q("max_endpoint_unit_quaternion_error"), div(angular_width_squared, thirty_two), div(square(arc), eight))))
    if difference > Fraction(1, 2):
        _error("OKE-E-CERTIFICATE", "The supplied quaternion comparison exceeds its proved local range.", model=model)
    borrowed = terms.borrow("rotation") if terms is not None else None
    require("ideal_rotation_bound_rad", div(angular_width_squared, four) if borrowed is None else borrowed[0])
    borrowed = terms.borrow("product", "chord") if terms is not None else None
    chord = div(mul(acceleration, width_squared), eight) if borrowed is None else borrowed[1]
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


# Verbatim checkpoint 026 function body, apart from its definition name.
# Resolve its globals in the original product module just as that source did.
checkpoint026_complete_inequality_values = FunctionType(
    _checkpoint026_complete.__code__, reader.__dict__, "checkpoint026_complete_inequality_values")


def zero_inputs(*, ha=F(1, 104), hs=F(1, 128), changes=None, tight=False):
    """Fresh canonical zero coefficients and positive, deliberately unequal gaps."""
    values = inputs(ha=ha, hs=hs, changes={name: F(0) for name in COEFFICIENTS})
    q = values[2]
    if tight:
        q["unit_quaternion_difference_bound"] = (
            q["max_endpoint_unit_quaternion_error"] + q["stored_quaternion_arc_upper_rad"] ** 2 / 8)
        q["ideal_rotation_bound_rad"], q["ideal_position_bound_m"] = F(0), F(0)
        q["total_rotation_bound_rad"] = (4 * q["unit_quaternion_difference_bound"]
            + q["source_numeric_rotation_bound_rad"] + q["destination_numeric_rotation_bound_rad"])
        q["carrier_position_bound_m"] = (q["max_endpoint_position_error_m"]
            + q["source_numeric_position_bound_m"] + q["destination_numeric_position_bound_m"]
            + q["enclosing_carrier_speed_bound_m_per_s"] * q["max_endpoint_time_shift_s"])
        q["total_position_bound_m"] = (q["carrier_position_bound_m"]
            + q["landmark_radius_m"] * q["total_rotation_bound_rad"] + q["local_vertex_error_bound_m"])
    q.update(changes or {})
    return values


def zero_receipt(*, hs=F(1, 128)):
    """Produce six ordinary authored results before exercising optional zeroes."""
    values, work = zero_inputs(hs=hs), Work()
    ha, hs, quantities, position, rotation = values
    arithmetic = reader._Bounds(work)
    angular, acceleration, envelope_angular, envelope_acceleration = (
        quantities[name] for name in COEFFICIENTS)
    four, eight = reader._CERTIFICATE_FOUR, reader._CERTIFICATE_EIGHT
    position_quarter, rotation_quarter = arithmetic.div(position, four), arithmetic.div(rotation, four)
    terms = reader._CertificateTermReuse.create(arithmetic, quantities,
        (ha, hs, angular, acceleration, four, eight, position, rotation,
         position_quarter, rotation_quarter))
    if terms is None:
        raise AssertionError("The direct receipt probe requires original unobserved native dispatch")
    angle = terms.calculate("angle", arithmetic.mul, angular, ha)
    width_squared = terms.calculate("width_squared", arithmetic.square, ha)
    angle_squared = terms.calculate("angle_squared", arithmetic.square, angle)
    terms.calculate("rotation", arithmetic.div, angle_squared, four)
    product = terms.calculate("product", arithmetic.mul, acceleration, width_squared)
    terms.calculate("chord", arithmetic.div, product, eight)
    coefficients = (angular, acceleration, envelope_angular, envelope_acceleration)
    return terms, coefficients, values, work


class CertificateZeroQuarterTests(unittest.TestCase):
    def assert_accounted(self, work):
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertEqual(work.max_cache_entries, 256)
        self.assertEqual(work.record()["cache_entries"], 0)

    def pair(self, *, factory=zero_inputs, work_factory=Work):
        outcomes = []
        for calculation in (checkpoint026_complete_inequality_values, None):
            values, work = factory(), work_factory()
            try:
                result, _ = evaluate(calculation, operands=values, work=work)
                outcome = ("passed", result)
            except (OntoKinError, ReachAdmissionError) as error:
                outcome = ("failed", failure_signature(error))
            outcomes.append((outcome, work))
            self.assert_accounted(work)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        return outcomes

    def test_unequal_width_zero_quarters_save_five_incremental_operations(self):
        widths = ((F(1, 104), F(1, 128)), (F(1, 28), F(1, 32)),
                  (F(1, 44), F(1, 64)), (F(1, 128), F(1, 128)),
                  (F(17, 199), F(19, 211)))
        for ha, hs in widths:
            outcomes = self.pair(factory=lambda: zero_inputs(ha=ha, hs=hs))
            (expected, control), (actual, candidate) = outcomes
            with self.subTest(ha=ha, hs=hs):
                self.assertEqual(expected[0], "passed")
                self.assertEqual(control.operations - candidate.operations, 5)
                self.assertEqual(control.counts["independent_exact_mul"] - candidate.counts["independent_exact_mul"], 3)
                self.assertEqual(control.counts["independent_exact_div"] - candidate.counts["independent_exact_div"], 2)
                self.assertEqual(candidate.counts["independent_exact_compare"], control.counts["independent_exact_compare"])
                self.assertEqual(candidate.counts["independent_exact_add"], control.counts["independent_exact_add"])
                self.assertEqual(candidate.counts["independent_certificate_term_admission"], 1)

    def test_maximum_native_stored_width_and_adjacent_fallback_keep_exact_results(self):
        for bits in (2048, 2049):
            # These adjacent odd integers are coprime, so reduction keeps
            # both supplied fields exactly at the intended admission boundary.
            stored = F((1 << bits) - 3, (1 << bits) - 1)
            self.assertEqual(stored.numerator.bit_length(), bits)
            self.assertEqual(stored.denominator.bit_length(), bits)
            (outcome, control), (_, candidate) = self.pair(factory=lambda: zero_inputs(hs=stored))
            with self.subTest(stored_field_bits=bits):
                self.assertEqual(outcome[0], "passed")
                if bits == 2048:
                    self.assertEqual(control.operations - candidate.operations, 5)
                    self.assertEqual(candidate.counts["independent_certificate_term_admission"], 1)
                    terms, coefficients, values, work = zero_receipt(hs=stored)
                    self.assertTrue(terms.zero_quarter(*coefficients))
                    self.assertEqual(terms.zero("angle", "mul", coefficients[2], values[1]), 0)
                    before = work.operations
                    actual_square = terms.arithmetic.square(values[1])
                    self.assertEqual(work.operations, before + 1)
                    self.assertEqual(actual_square.numerator.bit_length(), 4096)
                    self.assertEqual(actual_square.denominator.bit_length(), 4096)
                    self.assertEqual(actual_square, stored * stored)
                    self.assertEqual(terms.zero("product", "mul", coefficients[3], actual_square), 0)
                    self.assertEqual(work.operations, before + 1)
                    self.assert_accounted(work)
                else:
                    self.assertEqual(candidate.operations, control.operations)
                    self.assertEqual(candidate.counts, control.counts)
                    self.assertNotIn("independent_certificate_term_admission", candidate.counts)

    def test_saved_authored_work_is_not_counted_as_new_zero_savings(self):
        prior, old = evaluate(original_complete, operands=zero_inputs())
        expected, control = evaluate(checkpoint026_complete_inequality_values, operands=zero_inputs())
        actual, candidate = evaluate(operands=zero_inputs())
        self.assertEqual(prior, expected)
        self.assertEqual(actual, expected)
        self.assertEqual(old.operations - control.operations, 5)
        self.assertEqual(control.operations - candidate.operations, 5)
        self.assertEqual(old.operations - candidate.operations, 10)

    def test_any_nonzero_coefficient_keeps_the_complete_checkpoint026_path(self):
        # All 15 nonempty subsets include asymmetric angular/acceleration cases.
        for mask in range(1, 16):
            changes = {name: F(1, 2) for index, name in enumerate(COEFFICIENTS) if mask & (1 << index)}
            (expected, control), (_, candidate) = self.pair(factory=lambda: zero_inputs(changes=changes))
            with self.subTest(nonzero_mask=mask):
                self.assertEqual(expected[0], "passed")
                self.assertEqual(candidate.operations, control.operations)
                self.assertEqual(candidate.counts, control.counts)

    def test_native_shared_budget_counts_each_remaining_operation(self):
        outcomes = []
        for calculation in (checkpoint026_complete_inequality_values, None):
            budget = ConstructionBudget()
            budget.profile = REACH_PROFILE
            callback = budget.tick
            work = Work(check=callback)
            result, _ = evaluate(calculation, operands=zero_inputs(), work=work)
            self.assertIs(work.external_check, callback)
            self.assertIsNone(work._source_after_charge)
            self.assertEqual(work.operations, budget.operations)
            self.assert_accounted(work)
            outcomes.append((result, work.operations, budget.operations))
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertEqual(outcomes[0][1] - outcomes[1][1], 5)
        self.assertEqual(outcomes[0][2] - outcomes[1][2], 5)

    def test_absent_work_owner_preserves_exact_algebra(self):
        outcomes = []
        for calculation in (checkpoint026_complete_inequality_values, None):
            actual, _ = evaluate(calculation, operands=zero_inputs(), arithmetic=reader._Bounds(None))
            outcomes.append(actual)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_each_fresh_reported_sum_retains_its_understatement_rejection(self):
        names = ("unit_quaternion_difference_bound", "ideal_rotation_bound_rad", "ideal_position_bound_m",
                 "total_rotation_bound_rad", "carrier_position_bound_m", "total_position_bound_m")
        for name in names:
            def values():
                supplied = zero_inputs(tight=True)
                supplied[2][name] -= F(1, 1 << 100)
                return supplied
            (outcome, _), _ = self.pair(factory=values)
            with self.subTest(quantity=name):
                self.assertEqual(outcome[0], "failed")
                self.assertEqual(outcome[1][-1]["quantity"], name)

    def test_stored_arc_and_final_tolerances_remain_binding(self):
        for change in ("arc", "position", "rotation", "difference"):
            def values():
                supplied = zero_inputs(tight=True)
                if change == "arc":
                    supplied[2]["stored_quaternion_arc_upper_rad"] = reader.ARC_LIMIT + F(1, 1 << 100)
                elif change == "difference":
                    supplied[2]["unit_quaternion_difference_bound"] = F(1, 2) + F(1, 1 << 100)
                elif change == "position":
                    supplied[3] = F(1, 1 << 100)
                else:
                    supplied[4] = F(1, 1 << 100)
                return supplied
            (outcome, _), _ = self.pair(factory=values)
            with self.subTest(boundary=change):
                self.assertEqual(outcome[0], "failed")

    def test_zero_coefficients_do_not_hide_the_actual_stored_square_overflow(self):
        # Stored angle is zero, but its actual following square still has a
        # 32,770-bit prospective denominator and must refuse at the same point.
        (outcome, control), (_, candidate) = self.pair(factory=lambda: zero_inputs(hs=F(1, 1 << 16384)))
        self.assertEqual(outcome[0], "failed")
        self.assertEqual(outcome[1][-1]["budget"], "numeric_operand_bits")
        self.assertEqual(outcome[1][-1]["limit"], 32768)
        self.assertEqual(outcome[1][-1]["consumed"], 32770)
        self.assertEqual(control.counts, candidate.counts)
        self.assertNotIn("independent_certificate_term_admission", candidate.counts)

    def test_initial_narrow_domains_keep_original_failure_order_and_work(self):
        for cap in (2, 16, 64, 128, 1024, 32767):
            (outcome, control), (_, candidate) = self.pair(work_factory=lambda: Work(max_operand_bits=cap))
            with self.subTest(cap=cap):
                self.assertEqual(candidate.counts, control.counts)
                self.assertEqual(candidate.operations, control.operations)
                self.assertNotIn("independent_certificate_term_admission", candidate.counts)

    def test_custom_callbacks_and_observers_keep_all_original_events(self):
        outcomes = []
        for calculation in (checkpoint026_complete_inequality_values, None):
            before, after, work = [], [], Work()
            def callback():
                before.append(work.operations)
            def observer():
                after.append(work.operations)
            work.external_check, work._source_after_charge = callback, observer
            result, _ = evaluate(calculation, operands=zero_inputs(), work=work)
            self.assertIs(work.external_check, callback)
            self.assertIs(work._source_after_charge, observer)
            self.assertEqual(before, list(range(work.operations)))
            self.assertEqual(after, list(range(1, work.operations + 1)))
            outcomes.append((result, work.counts, before, after))
        self.assertEqual(outcomes[0], outcomes[1])

    def test_cancellation_at_each_original_callback_preserves_exception_identity(self):
        seen = []
        work = Work(check=lambda: seen.append(True))
        evaluate(checkpoint026_complete_inequality_values, operands=zero_inputs(), work=work)
        for fail_at in range(1, len(seen) + 1):
            marker = RuntimeError("original exact-zero control cancellation")
            outcomes = []
            for calculation in (checkpoint026_complete_inequality_values, None):
                calls, work = [], Work()
                def cancel():
                    calls.append(True)
                    if len(calls) == fail_at:
                        raise marker
                work.external_check = cancel
                with self.assertRaises(RuntimeError) as caught:
                    evaluate(calculation, operands=zero_inputs(), work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertIs(work.external_check, cancel)
                outcomes.append((len(calls), work.operations, work.counts))
            with self.subTest(callback=fail_at):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_nested_construction_cancellation_uses_the_original_exception(self):
        for fail_at in (3, 13, 14, 20):
            marker = RuntimeError("nested exact-zero cancellation")
            outcomes = []
            for calculation in (checkpoint026_complete_inequality_values, None):
                calls = []
                def cancel():
                    calls.append(True)
                    if len(calls) == fail_at:
                        raise marker
                budget = ConstructionBudget(check=cancel)
                budget.profile = REACH_PROFILE
                work = Work(check=budget.tick)
                callback = work.external_check
                with self.assertRaises(RuntimeError) as caught:
                    evaluate(calculation, operands=zero_inputs(), work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertIs(budget.callback_error, marker)
                self.assertIs(work.external_check, callback)
                outcomes.append((len(calls), work.operations, work.counts, budget.operations))
            with self.subTest(callback=fail_at):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_mutated_enclosing_coefficients_at_the_stored_boundary_keep_fallback(self):
        for name in COEFFICIENTS[2:]:
            outcomes = []
            for calculation in (checkpoint026_complete_inequality_values, None):
                values, changed, work = zero_inputs(), [], Work()
                coefficient = values[2][name]
                def mutate():
                    if not changed and work.counts.get("independent_exact_compare", 0) == 3:
                        changed.append(True)
                        object.__setattr__(coefficient, "_numerator", 128)
                work.external_check = mutate
                with self.assertRaises(OntoKinError) as caught:
                    evaluate(calculation, operands=values, work=work)
                self.assertTrue(changed)
                outcomes.append((failure_signature(caught.exception), work.counts))
            with self.subTest(field=name):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_trace_hook_retains_original_arithmetic_and_hook_ownership(self):
        previous, outcomes = sys.gettrace(), []
        try:
            for calculation in (checkpoint026_complete_inequality_values, None):
                events, values, work = [], zero_inputs(), Work()
                def trace(frame, event, arg):
                    if event == "call":
                        events.append(frame.f_code.co_name)
                    return trace
                sys.settrace(trace)
                try:
                    result, _ = evaluate(calculation, operands=values, work=work)
                    self.assertIs(sys.gettrace(), trace)
                finally:
                    sys.settrace(previous)
                self.assertTrue(events)
                self.assertNotIn("independent_certificate_term_admission", work.counts)
                outcomes.append((result, work.counts))
        finally:
            sys.settrace(previous)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_profile_hook_retains_original_arithmetic_and_hook_ownership(self):
        previous, outcomes = sys.getprofile(), []
        try:
            for calculation in (checkpoint026_complete_inequality_values, None):
                events, values, work = [], zero_inputs(), Work()
                def profile(frame, event, arg):
                    if event == "call":
                        events.append(frame.f_code.co_name)
                sys.setprofile(profile)
                try:
                    result, _ = evaluate(calculation, operands=values, work=work)
                    self.assertIs(sys.getprofile(), profile)
                finally:
                    sys.setprofile(previous)
                self.assertTrue(events)
                self.assertNotIn("independent_certificate_term_admission", work.counts)
                outcomes.append((result, work.counts))
        finally:
            sys.setprofile(previous)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_fraction_properties_do_not_add_earlier_reads(self):
        for name in ("numerator", "denominator"):
            original = getattr(F, name)
            outcomes = []
            for calculation in (checkpoint026_complete_inequality_values, None):
                calls, values, work = [], zero_inputs(), Work()
                def field(value):
                    calls.append(id(value))
                    return original.fget(value)
                with patch.object(F, name, property(field)):
                    result, _ = evaluate(calculation, operands=values, work=work)
                self.assertTrue(calls)
                self.assertNotIn("independent_certificate_term_admission", work.counts)
                outcomes.append((result, work.counts, len(calls)))
            with self.subTest(field=name):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_scalar_subclasses_keep_original_multiplication_calls(self):
        for name in ("stored_width", *COEFFICIENTS):
            outcomes = []
            for calculation in (checkpoint026_complete_inequality_values, None):
                calls = []
                class ForeignFraction(F):
                    def __mul__(self, other):
                        calls.append("mul")
                        return super().__mul__(other)
                    def __rmul__(self, other):
                        calls.append("rmul")
                        return super().__rmul__(other)
                values = zero_inputs()
                if name == "stored_width":
                    values[1] = ForeignFraction(1, 128)
                else:
                    values[2][name] = ForeignFraction(0)
                result, work = evaluate(calculation, operands=values)
                self.assertTrue(calls)
                self.assertNotIn("independent_certificate_term_admission", work.counts)
                outcomes.append((result, work.counts, calls))
            with self.subTest(field=name):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_bounds_dispatch_preserves_all_original_calls(self):
        for name in ("mul", "div", "square", "op", "bits", "tick", "compare"):
            original = getattr(reader._Bounds, name)
            outcomes = []
            for calculation in (checkpoint026_complete_inequality_values, None):
                calls = []
                def foreign(owner, *args, **kwargs):
                    calls.append(args)
                    return original(owner, *args, **kwargs)
                with patch.object(reader._Bounds, name, foreign):
                    result, work = evaluate(calculation, operands=zero_inputs())
                outcomes.append((result, work.counts, calls))
            with self.subTest(method=name):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_wider_counter_inventory_uses_the_unchanged_ordinary_path(self):
        def work_factory():
            work = Work()
            work.counts = {f"other_{index}": 0 for index in range(513)}
            return work
        (_, control), (_, candidate) = self.pair(work_factory=work_factory)
        self.assertEqual(control.counts, candidate.counts)
        self.assertNotIn("independent_certificate_term_admission", candidate.counts)

    def test_five_omissions_return_owned_zeroes_and_share_one_admission(self):
        terms, coefficients, values, work = zero_receipt()
        self.assertTrue(terms.zero_quarter(*coefficients))
        self.assertFalse(terms.admitted)
        before = work.operations
        angle = terms.zero("angle", "mul", coefficients[2], values[1])
        self.assertIsNotNone(angle)
        width_squared = terms.arithmetic.square(values[1])
        angle_squared = terms.zero("angle_squared", "mul", angle, angle)
        rotation = terms.zero("rotation", "div", angle_squared, reader._CERTIFICATE_FOUR)
        product = terms.zero("product", "mul", coefficients[3], width_squared)
        chord = terms.zero("chord", "div", product, reader._CERTIFICATE_EIGHT)
        zeroes = (angle, angle_squared, rotation, product, chord)
        self.assertTrue(all(type(value) is F and value == 0 for value in zeroes))
        self.assertEqual(len({id(value) for value in zeroes}), 5)
        self.assertEqual(width_squared, values[1] ** 2)
        self.assertNotEqual(width_squared, terms.results["width_squared"][2])
        for value in zeroes:
            self.assertTrue(all(value is not record[2] for record in terms.results.values()))
        self.assertEqual(work.operations - before, 2)  # One admission and the retained stored square.
        authored = terms.borrow("angle", "angle_squared", "width_squared")
        self.assertIsNotNone(authored)
        self.assertEqual(work.operations - before, 2)
        self.assertEqual(work.counts["independent_certificate_term_admission"], 1)
        object.__setattr__(angle, "_numerator", 1)
        fresh = terms.zero("angle", "mul", coefficients[2], values[1])
        self.assertEqual(fresh, 0)
        self.assertIsNot(fresh, angle)
        self.assertEqual(terms.results["angle"][2], 0)
        self.assert_accounted(work)

    def test_changed_enclosing_coefficient_cannot_reuse_a_zero_receipt(self):
        for index in (2, 3):
            terms, coefficients, values, work = zero_receipt()
            self.assertTrue(terms.zero_quarter(*coefficients))
            first = terms.zero("angle", "mul", coefficients[2], values[1])
            self.assertEqual(first, 0)
            object.__setattr__(coefficients[index], "_numerator", 1)
            before = work.operations
            self.assertIsNone(terms.zero("angle", "mul", coefficients[2], values[1]))
            self.assertEqual(work.operations, before)
            self.assertEqual(terms.arithmetic.mul(coefficients[index], values[1]), values[1])
            self.assertEqual(work.operations, before + 1)

    def test_noncanonical_zero_fields_and_foreign_integer_fields_decline(self):
        class ForeignInteger(int):
            pass
        for index in range(4):
            for field, bad in (("_denominator", 2), ("_numerator", False),
                               ("_numerator", ForeignInteger(0)), ("_denominator", ForeignInteger(1))):
                terms, coefficients, _, work = zero_receipt()
                object.__setattr__(coefficients[index], field, bad)
                before = work.operations
                with self.subTest(coefficient=index, field=field, value_type=type(bad).__name__):
                    self.assertFalse(terms.zero_quarter(*coefficients))
                    self.assertEqual(work.operations, before)

    def test_changed_owner_callback_and_observer_decline_without_foreign_calls(self):
        for change in ("owner", "callback", "observer", "operand_limit"):
            terms, coefficients, values, work = zero_receipt()
            self.assertTrue(terms.zero_quarter(*coefficients))
            calls = []
            def foreign():
                calls.append(True)
                raise AssertionError("Optional identity invoked foreign work")
            other = Work()
            if change == "owner":
                terms.arithmetic.work = other
            elif change == "callback":
                work.external_check = foreign
            elif change == "observer":
                work._source_after_charge = foreign
            else:
                work.max_operand_bits = 32767
            before = work.operations
            with self.subTest(change=change):
                self.assertIsNone(terms.zero("angle", "mul", coefficients[2], values[1]))
                self.assertEqual(work.operations, before)
                self.assertEqual(other.operations, 0)
                self.assertEqual(calls, [])

    def test_changed_fraction_dispatch_after_admission_declines_before_omission(self):
        terms, coefficients, values, work = zero_receipt()
        self.assertTrue(terms.zero_quarter(*coefficients))
        self.assertEqual(terms.zero("angle", "mul", coefficients[2], values[1]), 0)
        before, calls = work.operations, []
        original = F.__mul__
        def foreign(first, last):
            calls.append((first, last))
            return original(first, last)
        with patch.object(F, "__mul__", foreign):
            self.assertIsNone(terms.zero("product", "mul", coefficients[3], F(1, 1 << 200)))
        self.assertEqual(work.operations, before)
        self.assertEqual(calls, [])

    def test_live_narrowing_keeps_stored_angle_then_square_failure_order(self):
        for cap, expected_consumed, expected_mul in ((101, 102, 1), (150, 202, 2)):
            terms, coefficients, values, work = zero_receipt(hs=F(1, 1 << 100))
            self.assertTrue(terms.zero_quarter(*coefficients))
            work.max_operand_bits = cap
            before = work.counts["independent_exact_mul"]
            with self.subTest(cap=cap):
                self.assertIsNone(terms.zero("angle", "mul", coefficients[2], values[1]))
                with self.assertRaises(ReachAdmissionError) as caught:
                    terms.arithmetic.mul(coefficients[2], values[1])
                    terms.arithmetic.square(values[1])
                self.assertEqual(caught.exception.details["consumed"], expected_consumed)
                self.assertEqual(caught.exception.details["limit"], cap)
                self.assertEqual(work.counts["independent_exact_mul"] - before, expected_mul)

    def test_live_product_guard_uses_the_actual_stored_square(self):
        terms, coefficients, values, work = zero_receipt(hs=F(1, 1 << 100))
        self.assertTrue(terms.zero_quarter(*coefficients))
        self.assertEqual(terms.zero("angle", "mul", coefficients[2], values[1]), 0)
        stored_square = terms.arithmetic.square(values[1])
        self.assertEqual(stored_square.denominator.bit_length(), 201)
        self.assertNotEqual(stored_square, terms.results["width_squared"][2])
        work.max_operand_bits = 201
        before = work.operations
        self.assertIsNone(terms.zero("product", "mul", coefficients[3], stored_square))
        self.assertEqual(work.operations, before)
        with self.assertRaises(ReachAdmissionError) as caught:
            terms.arithmetic.mul(coefficients[3], stored_square)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["consumed"], 202)
        self.assertEqual(caught.exception.details["limit"], 201)

    def test_changed_owned_zero_cannot_supply_the_next_zero_square(self):
        terms, coefficients, values, work = zero_receipt()
        self.assertTrue(terms.zero_quarter(*coefficients))
        angle = terms.zero("angle", "mul", coefficients[2], values[1])
        self.assertEqual(angle, 0)
        object.__setattr__(angle, "_numerator", 1)
        before = work.operations
        self.assertIsNone(terms.zero("angle_squared", "mul", angle, angle))
        self.assertEqual(work.operations, before)
        self.assertEqual(terms.arithmetic.square(angle), 1)

    def test_changed_completed_authored_zero_cannot_certify_an_omission(self):
        for name in ZERO_NAMES:
            terms, coefficients, values, work = zero_receipt()
            self.assertTrue(terms.zero_quarter(*coefficients))
            saved = terms.results[name][2]
            object.__setattr__(saved, "_numerator", 1)
            before = work.operations
            operation = "div" if name in ("rotation", "chord") else "mul"
            last = reader._CERTIFICATE_FOUR if operation == "div" else values[1]
            if name == "angle_squared":
                last = F(0)
            with self.subTest(term=name):
                self.assertIsNone(terms.zero(name, operation, F(0), last))
                self.assertEqual(work.operations, before)
                self.assertFalse(terms.valid)

    def test_zero_division_identity_cannot_hide_a_zero_denominator(self):
        terms, coefficients, _, work = zero_receipt()
        self.assertTrue(terms.zero_quarter(*coefficients))
        before = work.operations
        self.assertIsNone(terms.zero("rotation", "div", F(0), F(0)))
        self.assertEqual(work.operations, before)
        with self.assertRaises(OntoKinError) as caught:
            terms.arithmetic.div(F(0), F(0))
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-CERTIFICATE")
        self.assertIn("denominator is zero", caught.exception.diagnostic.message)
        self.assertEqual(work.operations, before + 1)

    def test_native_operation_caps_bound_every_remaining_charge(self):
        _, completed = evaluate(operands=zero_inputs())
        for cap in sorted({1, 2, 3, 8, 13, 14, 20, completed.operations - 1, completed.operations}):
            work = Work(max_operations=cap)
            if cap < completed.operations:
                with self.subTest(cap=cap), self.assertRaises(ReachAdmissionError) as caught:
                    evaluate(operands=zero_inputs(), work=work)
                self.assertEqual(caught.exception.details["limit"], cap)
                self.assertEqual(caught.exception.details["consumed"], cap + 1)
                self.assertEqual(work.operations, cap)
            else:
                evaluate(operands=zero_inputs(), work=work)
                self.assertEqual(work.operations, completed.operations)
            self.assert_accounted(work)

    def test_shared_construction_caps_bound_each_remaining_charge(self):
        _, completed = evaluate(operands=zero_inputs())
        for cap in sorted({1, 2, 8, 13, 14, 20, completed.operations - 1, completed.operations}):
            budget = ConstructionBudget(budgets={"max_operations": cap})
            budget.profile = REACH_PROFILE
            work = Work(check=budget.tick)
            if cap < completed.operations:
                with self.subTest(cap=cap), self.assertRaises(OntoKinError) as caught:
                    evaluate(operands=zero_inputs(), work=work)
                self.assertEqual(caught.exception.diagnostic.details["limit"], cap)
                self.assertEqual(caught.exception.diagnostic.details["consumed"], cap + 1)
                self.assertEqual(work.operations, cap)
                self.assertEqual(budget.operations, cap + 1)
            else:
                evaluate(operands=zero_inputs(), work=work)
                self.assertEqual(work.operations, completed.operations)
                self.assertEqual(budget.operations, completed.operations)
            self.assert_accounted(work)

    def test_failed_invocation_cannot_supply_a_later_zero_or_nonzero_result(self):
        work = Work()
        values = zero_inputs(tight=True, changes={"total_position_bound_m": F(0)})
        with self.assertRaises(OntoKinError):
            evaluate(operands=values, work=work)
        before = work.operations
        changes = {"angular_speed_bound_rad_per_s": F(1, 2)}
        expected, control = evaluate(checkpoint026_complete_inequality_values, operands=zero_inputs(changes=changes))
        actual, _ = evaluate(operands=zero_inputs(changes=changes), work=work)
        self.assertEqual(actual, expected)
        self.assertEqual(work.operations - before, control.operations)
        self.assert_accounted(work)


if __name__ == "__main__":
    unittest.main()
