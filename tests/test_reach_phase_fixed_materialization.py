"""Fixed affine phase materialization retains the complete original formula."""
import copy
from dataclasses import replace
from fractions import Fraction as F
from types import MethodType
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.construction import compile_construction
from ontokin.reach_export import recording_phase_bounds
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork as Work
from test_reach_phase import source
from test_reach_phase_mounts import PlanningSimulator


def location():
    base = reach_phase.PhaseBound(max_position_l1_m=F(5, 7), path_offset_l1_m=F(2, 3),
        position_error_m=F(1, 1 << 80),
        rotation_error_rad=reach_phase.EXPOSED_ROTATION_ERROR + F(1, 1 << 50),
        trig_count=2, product_count=7, vector_round_count=8,
        carrier_speed_upper_m_per_s=F(2, 7),
        angular_velocity_error_rad_per_s=F(1, 1 << 64))
    return reach_phase._PhaseLocation(base, F(13, 7), F(5, 11))


def materialize(value, work=None, *, generic=False, arithmetic=None):
    work = Work() if work is None else work
    arithmetic = reach_phase.PhaseArithmetic(work) if arithmetic is None else arithmetic
    if generic:
        with patch.object(reach_phase, "_fixed_phase_location_values", return_value=None):
            return reach_phase._materialize_phase_location(value, arithmetic, work)
    return reach_phase._materialize_phase_location(value, arithmetic, work)


class ReachFixedPhaseMaterializationTests(unittest.TestCase):
    def test_both_original_p23_phase_maps_and_source_proofs_match_the_generic_formula(self):
        for start, end in ((F(0), F(2)), (F(2), F(3))):
            outputs, costs = [], []
            for generic in (True, False):
                built = compile_construction(source("P23"))
                simulator = PlanningSimulator(built.model, work=built.reach_work)
                simulator.advance(start, "after")
                state = copy.deepcopy(simulator.state)
                before = built.budget.operations
                if generic:
                    with patch.object(reach_phase, "_fixed_phase_location_values", return_value=None):
                        output = recording_phase_bounds(simulator, start, end, recording_proof=True)
                else:
                    output = recording_phase_bounds(simulator, start, end, recording_proof=True)
                outputs.append(output)
                costs.append(built.budget.operations - before)
                self.assertEqual(state, simulator.state)
                self.assertGreater(built.reach_work.counts.get("phase_location_materialize", 0), 0)
                self.assertEqual(built.reach_work.operations, sum(built.reach_work.counts.values()))
                self.assertLessEqual(len(built.reach_work._cache), 256)
                self.assertLessEqual(built.budget.operations, 100000)
            with self.subTest(start=start, end=end):
                self.assertEqual(outputs[0], outputs[1])
                self.assertGreater(costs[0] - costs[1], 500)

    def test_exact_zero_signed_nondyadic_and_boundary_widths_match_all_fields(self):
        ordinary = location()
        large = F((1 << 2047) - 1, (1 << 2047) + 1)
        cases = [ordinary,
            reach_phase._PhaseLocation(reach_phase.PhaseBound(), F(0), F(0)),
            replace(ordinary, extent=F(-11, 13), offset=F(0)),
            replace(ordinary, relative=replace(ordinary.relative, position_error_m=F(0)),
                    extent=F(0), offset=F(-7, 19)),
            reach_phase._PhaseLocation(reach_phase.PhaseBound(
                max_position_l1_m=large, path_offset_l1_m=large,
                position_error_m=large, rotation_error_rad=large), large, large)]
        for value in cases:
            with self.subTest(value=value):
                before = copy.deepcopy(value)
                work = Work()
                self.assertEqual(materialize(value, work), materialize(value, generic=True))
                self.assertEqual(value, before)
                self.assertEqual(work.counts.get("phase_location_materialize"), 1)
                self.assertNotIn("phase_sum_domain", work.counts)
                self.assertNotIn("phase_product_domain", work.counts)
                self.assertEqual(work.operations, 8)

    def test_initial_narrow_domain_preserves_admitted_zero_identity_cases(self):
        # Adding exact zero through the generic identity path is admitted at
        # this cap although an unnecessary unreduced addition would be wider.
        value = reach_phase._PhaseLocation(reach_phase.PhaseBound(
            max_position_l1_m=F((1 << 127) - 1),
            rotation_error_rad=reach_phase.EXPOSED_ROTATION_ERROR), F(0), F(1))
        work = Work(max_operand_bits=128)
        expected = materialize(value, Work(max_operand_bits=128), generic=True)
        self.assertEqual(materialize(value, work), expected)
        self.assertGreater(work.counts.get("phase_sum_domain", 0), 0)
        self.assertEqual(work.max_operand_bits, 128)

    def test_wide_or_nonnative_spatial_inputs_keep_the_generic_path(self):
        value = location()
        for changed in (replace(value, extent=F(1 << 2048)),
                        replace(value, extent=0),
                        replace(value, relative=replace(value.relative, path_offset_l1_m=0))):
            with self.subTest(changed=changed):
                work = Work()
                self.assertEqual(materialize(changed, work), materialize(changed, generic=True))
                self.assertGreater(work.counts.get("phase_sum_domain", 0), 0)
        existing = value.relative
        work = Work()
        self.assertIs(materialize(existing, work), existing)
        self.assertEqual(work.operations, 0)

    def test_each_mid_dag_cap_change_is_latched_even_when_fallback_restores_the_cap(self):
        for operation in range(1, 8):
            calls = 0
            def check():
                nonlocal calls
                calls += 1
                if calls == operation + 1:
                    work.max_operand_bits = 128
                elif calls == operation + 2:
                    work.max_operand_bits = MAX_OPERAND_BITS
            work = Work(check=check)
            with self.subTest(operation=operation):
                self.assertEqual(materialize(location(), work), materialize(location(), generic=True))
                self.assertEqual(work.max_operand_bits, MAX_OPERAND_BITS)
                self.assertGreater(work.counts.get("phase_sum_domain", 0), 0)
                self.assertGreater(work.counts.get("phase_product_domain", 0), 0)

    def test_changed_native_method_dispatch_runs_the_current_generic_formula(self):
        native = reach_phase.PhaseArithmetic.add
        calls = dispatched = 0
        def changed(arithmetic, *values):
            nonlocal dispatched
            dispatched += 1
            reach_phase.PhaseArithmetic.add = native
            return native(arithmetic, *values)
        def check():
            nonlocal calls
            calls += 1
            if calls == 2:
                reach_phase.PhaseArithmetic.add = changed
        work = Work(check=check)
        with patch.object(reach_phase.PhaseArithmetic, "add", native):
            actual = materialize(location(), work)
        self.assertEqual(actual, materialize(location(), generic=True))
        self.assertEqual(dispatched, 1)
        self.assertGreater(work.counts.get("phase_sum_domain", 0), 0)

    def test_changed_exact_dispatch_cannot_publish_a_partially_native_result(self):
        native = reach_phase.exact
        calls = dispatched = 0
        def changed(left, right, operation, work):
            nonlocal dispatched
            dispatched += 1
            reach_phase.exact = native
            return native(left, right, operation, work)
        def check():
            nonlocal calls
            calls += 1
            if calls == 2:
                reach_phase.exact = changed
        work = Work(check=check)
        with patch.object(reach_phase, "exact", native):
            actual = materialize(location(), work)
        self.assertEqual(actual, materialize(location(), generic=True))
        self.assertEqual(dispatched, 1)
        self.assertGreater(work.counts.get("phase_sum_domain", 0), 0)

    def test_custom_arithmetic_dispatch_is_not_bypassed_initially(self):
        class Custom(reach_phase.PhaseArithmetic):
            def add(self, *values):
                self.called += 1
                return super().add(*values)
        work = Work()
        custom = Custom(work)
        custom.called = 0
        expected = materialize(location(), generic=True)
        self.assertEqual(materialize(location(), work, arithmetic=custom), expected)
        self.assertGreater(custom.called, 0)
        work = Work()
        ordinary = reach_phase.PhaseArithmetic(work)
        called = []
        def instance_add(arithmetic, *values):
            called.append(values)
            return reach_phase.PhaseArithmetic.add(arithmetic, *values)
        ordinary.add = MethodType(instance_add, ordinary)
        self.assertEqual(materialize(location(), work, arithmetic=ordinary), expected)
        self.assertTrue(called)

    def test_changed_fraction_or_bound_field_abandons_the_original_spatial_receipt(self):
        for mutation in ("fraction", "wide_fraction", "bound", "bool_numerator", "bool_denominator"):
            value = replace(location(), extent=F(1)) if mutation.startswith("bool_") else location()
            calls = 0
            def check():
                nonlocal calls
                calls += 1
                if calls == 2:
                    if mutation == "bound":
                        object.__setattr__(value.relative, "position_error_m", F(3, 16))
                    elif mutation.startswith("bool_"):
                        object.__setattr__(value.extent, "_" + mutation.removeprefix("bool_"), True)
                    else:
                        numerator = (value.extent.numerator + 2 if mutation == "fraction" else 1 << 2100)
                        object.__setattr__(value.extent, "_numerator", numerator)
            work = Work(check=check)
            with self.subTest(mutation=mutation):
                actual = materialize(value, work)
                self.assertEqual(actual, materialize(value, generic=True))
                self.assertGreater(work.counts.get("phase_sum_domain", 0), 0)

    def test_changed_work_owner_is_rejected_without_charging_a_fresh_request(self):
        calls = 0
        other = Work()
        def check():
            nonlocal calls
            calls += 1
            if calls == 2:
                arithmetic.work = other
        work = Work(check=check)
        arithmetic = reach_phase.PhaseArithmetic(work)
        with self.assertRaises(ReachAdmissionError) as caught:
            materialize(location(), work, arithmetic=arithmetic)
        self.assertEqual(caught.exception.reach_code, "reach_domain")
        self.assertIn("work context", str(caught.exception))
        self.assertEqual(other.operations, 0)
        self.assertEqual(len(work._cache), 0)

    def test_all_callbacks_preserve_exception_identity_and_publish_no_partial_value(self):
        for stop in range(1, 9):
            markers = (RuntimeError("cancel materialization"), ReachAdmissionError(
                "reach_resource", "callback numerical limit", budget="numeric_operand_bits",
                limit=128, consumed=129))
            for marker in markers:
                calls = 0
                def check():
                    nonlocal calls
                    calls += 1
                    if calls == stop:
                        raise marker
                value = location()
                before = copy.deepcopy(value)
                work = Work(check=check)
                with self.subTest(stop=stop, exception=type(marker).__name__):
                    with self.assertRaises(type(marker)) as caught:
                        materialize(value, work)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(work.callback_error, marker)
                    self.assertEqual(value, before)
                    self.assertEqual(work.operations, stop - 1)
                    self.assertEqual(len(work._cache), 0)

    def test_the_original_budget_and_numeric_cache_remain_owned_by_the_same_work(self):
        work = Work(max_operations=7)
        with self.assertRaises(ReachAdmissionError) as caught:
            materialize(location(), work)
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], 7)
        self.assertEqual(caught.exception.details["consumed"], 8)
        self.assertEqual(work.operations, 7)
        self.assertEqual(work.max_operations, 7)
        work = Work(max_cache_entries=1)
        work.remember(("existing_numeric_value",), F(17, 23))
        before = list(work._cache.items())
        self.assertEqual(materialize(location(), work), materialize(location(), generic=True))
        self.assertEqual(list(work._cache.items()), before)
        self.assertEqual(work.max_cache_entries, 1)


if __name__ == "__main__":
    unittest.main()
