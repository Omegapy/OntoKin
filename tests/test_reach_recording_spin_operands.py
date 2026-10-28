"""Completed spin operands retain original arithmetic and current admission."""
from contextlib import ExitStack
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_numeric import (MAX_OPERAND_BITS, ReachAdmissionError,
                                   ReachExecutionWork, float_bits)
from ontokin.reach_pose import ReachPoseOps, RotationValue, UNIT
from ontokin.reach_recording_fast import Binary64RecordingOps, _UnsupportedPlanar


def native_ops():
    return Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()))


def spin_key(key):
    return "certified_binary64_spin" in key


def rotation_bits(value):
    return float_bits(value.w), float_bits(value.z), value.zero_w, value.zero_z


def cache_identity(work):
    return tuple((key, id(value)) for key, value in work._cache.items())


def prepare(initial=UNIT, *, horizon=F(3), max_steps=10000, warm=True):
    native = native_ops()
    omega = (0.0, 0.0, 0.25)
    plan = native.source_ops.spin_plan(omega, horizon)
    arguments = dict(context=object(), path="prescribed:root", max_steps=max_steps,
                     phase_plan=plan)
    if warm:
        for time in (F(1, 8), F(1, 4)):
            native.recording_advance_orientation(initial, omega, time, **arguments)
    return native, omega, arguments


class ReachRecordingSpinOperandTests(unittest.TestCase):
    def test_completed_operands_preserve_exact_native_bits_through_reseeding(self):
        initials = ((1.0, 0.0, 0.0, 0.125),
                    RotationValue((F(1), F(0), F(0), F(1, 8))),
                    RotationValue(UNIT, frozen_projection=(1.0, 0.0, 0.0, 0.0)))
        times = [F(index + 1, 64) for index in range(130)]
        times += [F(-2), F(-15, 8), F(-7, 4), F(-7, 4), F(2), F(0), F(1, 8)]
        for initial in initials:
            with self.subTest(initial=type(initial).__name__):
                actual, omega, actual_args = prepare(initial, warm=False)
                original, _, original_args = prepare(initial, warm=False)
                with patch.object(original, "_reusable_spin_plan", return_value=False):
                    for time in times:
                        a = actual.recording_advance_orientation(initial, omega, time, **actual_args)
                        b = original.recording_advance_orientation(initial, omega, time, **original_args)
                        self.assertEqual(rotation_bits(a), rotation_bits(b))
                self.assertLess(actual.work.operations, original.work.operations)
                for ops in (actual, original):
                    self.assertLessEqual(len(ops.work._cache), 256)
                    self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))

    def test_warm_spin_reuses_completed_normalization_velocity_and_stationarity(self):
        for initial in (UNIT, (1.0, 0.0, 0.0, 0.125), RotationValue(UNIT)):
            with self.subTest(initial=type(initial).__name__):
                native, omega, arguments = prepare(initial)
                counts = dict(native.work.counts)
                with ExitStack() as stack:
                    for name in ("_rotation", "_recording_vector", "_checked_spin_plan"):
                        stack.enter_context(patch.object(native.source_ops, name,
                            side_effect=AssertionError("completed fixed spin operand")))
                    result = native.recording_advance_orientation(initial, omega, F(3, 8), **arguments)
                self.assertTrue(result.w > 0)
                for name in ("orientation_stationary", "pose_rotation_reference", "pose_vector_domain"):
                    self.assertEqual(native.work.counts.get(name, 0), counts.get(name, 0))
                # The newly requested clock still receives its exact horizon
                # comparison. Its same-half delta needs no second ordering.
                self.assertEqual(native.work.counts["exact_compare"] - counts["exact_compare"], 1)
                self.assertEqual(native.work.counts["exact_sub"] - counts["exact_sub"], 1)

    def test_raw_keys_distinguish_native_types_and_both_binary64_zero_signs(self):
        native, omega, arguments = prepare(warm=False)
        initials = (UNIT, (1, 0, 0, 0), (1.0, 0.0, 0.0, 0.0),
                    (1.0, -0.0, 0.0, 0.0))
        vectors = (omega, (F(0), F(0), F(1, 4)), (0, 0, F(1, 4)),
                   (0.0, -0.0, 0.25))
        pairs = [(initial, omega) for initial in initials]
        pairs += [(UNIT, vector) for vector in vectors[1:]]
        for initial, vector in pairs:
            with patch.object(native.source_ops, "_checked_spin_plan",
                              wraps=native.source_ops._checked_spin_plan) as checked:
                native.recording_advance_orientation(initial, vector, F(1, 8), **arguments)
            self.assertGreater(checked.call_count, 0)
        keys = [key for key in native.work._cache if spin_key(key)]
        self.assertEqual(len(keys), len(pairs))
        self.assertTrue(all("immutable_operands_v1" in key for key in keys))

    def test_mutable_and_subclass_inputs_keep_original_decoding(self):
        class TupleSubclass(tuple):
            pass
        class RotationSubclass(RotationValue):
            pass
        native, omega, arguments = prepare()
        cases = ((list(UNIT), omega), (TupleSubclass(UNIT), omega),
                 (RotationSubclass(UNIT), omega), (UNIT, list(omega)),
                 (UNIT, TupleSubclass(omega)))
        for initial, vector in cases:
            with self.subTest(initial=type(initial).__name__, omega=type(vector).__name__):
                with patch.object(native.source_ops, "_rotation",
                                  wraps=native.source_ops._rotation) as rotation, \
                     patch.object(native.source_ops, "_recording_vector",
                                  wraps=native.source_ops._recording_vector) as velocity:
                    native.recording_advance_orientation(initial, vector, F(3, 8), **arguments)
                self.assertGreater(rotation.call_count, 0)
                self.assertGreater(velocity.call_count, 0)

    def test_boolean_or_nonfinite_aliases_cannot_use_completed_operands(self):
        native, omega, arguments = prepare()
        cases = (((True, F(0), F(0), F(0)), omega),
                 (UNIT, (False, 0.0, 0.25)),
                 ((float("inf"), 0.0, 0.0, 0.0), omega),
                 (UNIT, (0.0, float("nan"), 0.25)))
        for initial, vector in cases:
            with self.subTest(initial_type=type(initial[0]).__name__, omega_type=type(vector[0]).__name__):
                with self.assertRaises((ReachAdmissionError, _UnsupportedPlanar)):
                    native.recording_advance_orientation(initial, vector, F(3, 8), **arguments)

    def test_frozen_projection_and_plan_fields_cannot_alias_a_completed_raw_key(self):
        initial = RotationValue(UNIT, frozen_projection=(1.0, 0.0, 0.0, 0.0))
        native, omega, arguments = prepare(initial)
        marker = RuntimeError("cold spin must retain original plan admission")
        variants = ((replace(initial, frozen_projection=(1, 0, 0, 0)), arguments),
                    (replace(initial, frozen_projection=(1.0, -0.0, 0.0, 0.0)), arguments),
                    (replace(initial, frozen_projection=(0.5, 0.0, 0.0, 0.0)), arguments),
                    (initial, arguments | {"phase_plan": replace(arguments["phase_plan"],
                        argument_error_rad=arguments["phase_plan"].argument_error_rad * 2)}),
                    (initial, arguments | {"phase_plan": replace(arguments["phase_plan"],
                        precision_bits=True)}))
        for changed_initial, changed_args in variants:
            with self.subTest(initial=repr(changed_initial.frozen_projection),
                              precision=changed_args["phase_plan"].precision_bits):
                with patch.object(native.source_ops, "_checked_spin_plan", side_effect=marker):
                    with self.assertRaises(RuntimeError) as caught:
                        native.recording_advance_orientation(changed_initial, omega, F(3, 8), **changed_args)
                self.assertIs(caught.exception, marker)

    def test_stationary_and_zero_clock_keep_original_unused_plan_behavior(self):
        native = native_ops()
        arguments = dict(context=object(), path="prescribed:stationary", max_steps=10000,
                         phase_plan=object())
        for omega, time in (((0.0, 0.0, 0.25), F(0)), ((0.0, 0.0, 0.0), F(1))):
            with patch.object(native.source_ops, "_checked_spin_plan",
                              side_effect=AssertionError("unused stationary plan")):
                actual = native.recording_advance_orientation(UNIT, omega, time, **arguments)
            self.assertEqual(rotation_bits(actual), (float_bits(1.0), float_bits(0.0), False, True))
        self.assertFalse(any(spin_key(key) for key in native.work._cache))

    def test_every_current_clock_and_changed_horizon_retain_rejection(self):
        native, omega, arguments = prepare()
        key = next(key for key in native.work._cache if spin_key(key))
        previous = native.work._cache[key]
        for time, horizon in ((F(4), F(3)), (F(-4), F(3)), (F(3, 8), F(1, 4)),
                              (F(3, 8), F(-3))):
            with self.subTest(time=time, horizon=horizon), self.assertRaises(ReachAdmissionError):
                native.recording_advance_orientation(UNIT, omega, time,
                    **(arguments | {"phase_plan": replace(arguments["phase_plan"], max_elapsed_s=horizon)}))
            self.assertIs(native.work._cache[key], previous)

    def test_same_half_delta_keeps_original_prospective_comparison_limit(self):
        native, omega, arguments = prepare(warm=False)
        power = 1 << 15000
        # Each clock fits the absolute-horizon comparison. Subtracting their
        # unlike denominators fits the original exact subtraction, but its
        # result's comparison with this same H would exceed the unchanged cap.
        horizon = F(power + 1, power - 1)
        arguments["phase_plan"] = replace(arguments["phase_plan"], max_elapsed_s=horizon)
        native.recording_advance_orientation(UNIT, omega, F(power - 1, power), **arguments)
        key = next(key for key in native.work._cache if spin_key(key))
        previous = native.work._cache[key]
        with self.assertRaises(ReachAdmissionError) as caught:
            native.recording_advance_orientation(UNIT, omega, F(power - 3, power - 2), **arguments)
        self.assertEqual(caught.exception.details.get("budget"), "numeric_operand_bits")
        self.assertEqual(caught.exception.details.get("limit"), MAX_OPERAND_BITS)
        self.assertGreater(caught.exception.details.get("consumed", 0), MAX_OPERAND_BITS)
        self.assertIs(native.work._cache[key], previous)

    def test_source_change_during_lookup_cannot_reuse_a_completed_cursor(self):
        for change in ("initial", "projection", "plan"):
            with self.subTest(change=change):
                initial = RotationValue(UNIT, frozen_projection=(1.0, 0.0, 0.0, 0.0))
                native, omega, arguments = prepare(initial)
                key = next(key for key in native.work._cache if spin_key(key))
                previous, lookup = native.work._cache[key], native.work.lookup
                def intercept(current):
                    if spin_key(current):
                        def mutate():
                            native.work.external_check = None
                            if change == "initial":
                                object.__setattr__(initial, "components", (F(1), F(0), F(0), F(1, 8)))
                            elif change == "projection":
                                object.__setattr__(initial, "frozen_projection", (1.0, -0.0, 0.0, 0.0))
                            else:
                                object.__setattr__(arguments["phase_plan"], "maximum", F(1, 2))
                        native.work.external_check = mutate
                    return lookup(current)
                with patch.object(native.work, "lookup", side_effect=intercept):
                    with self.assertRaises(_UnsupportedPlanar):
                        native.recording_advance_orientation(initial, omega, F(3, 8), **arguments)
                self.assertIs(native.work._cache[key], previous)

    def test_cap_narrowing_and_restoration_drops_the_prior_completed_proof(self):
        native, omega, arguments = prepare()
        key = next(key for key in native.work._cache if spin_key(key))
        previous, lookup = native.work._cache[key], native.work.lookup
        changed = []
        def intercept(current):
            if spin_key(current) and not changed:
                def narrow_and_restore():
                    native.work.external_check = None
                    changed.append(True)
                    native.work.max_operand_bits = 128
                    lookup(("spin test narrow domain",))
                    native.work.max_operand_bits = MAX_OPERAND_BITS
                    lookup(("spin test restored domain",))
                native.work.external_check = narrow_and_restore
            return lookup(current)
        with patch.object(native.work, "lookup", side_effect=intercept), \
             patch.object(native.source_ops, "_checked_spin_plan",
                          wraps=native.source_ops._checked_spin_plan) as checked:
            native.recording_advance_orientation(UNIT, omega, F(3, 8), **arguments)
        self.assertEqual(changed, [True])
        self.assertGreater(checked.call_count, 0)
        self.assertIsNot(native.work._cache[key], previous)
        self.assertEqual(native.work._cache[key][2], 1)
        self.assertEqual(native.work.max_operand_bits, MAX_OPERAND_BITS)

    def test_all_publication_callbacks_recheck_current_complete_operands(self):
        for final in ("cache_insert", "cache_promote", "cache_evict"):
            with self.subTest(final=final):
                initial = RotationValue(UNIT)
                native, omega, arguments = prepare(initial, warm=final != "cache_evict")
                work, saved, changed = native.work, [], []
                remember, charge = work.remember, work.charge
                def publish(key, value, *, admission=None):
                    if not spin_key(key):
                        return remember(key, value, admission=admission)
                    self.assertIsNotNone(admission)
                    if final == "cache_evict":
                        for index in range(work.max_cache_entries - len(work._cache)):
                            remember(("spin publication filler", index), object())
                    saved.append((cache_identity(work), work._cache_generation))
                    def mutate():
                        work.external_check = None
                        changed.append(final)
                        object.__setattr__(initial, "error_rad", initial.error_rad + F(1, 100))
                    def charged(kind="checkpoint", amount=1):
                        if kind == final:
                            work.external_check = mutate
                        return charge(kind, amount)
                    def callback_free_admission():
                        with patch.object(work, "charge", side_effect=AssertionError("callback after admission")):
                            return admission()
                    try:
                        with patch.object(work, "charge", side_effect=charged):
                            return remember(key, value, admission=callback_free_admission)
                    finally:
                        work.external_check = None
                with patch.object(work, "remember", side_effect=publish):
                    with self.assertRaises(_UnsupportedPlanar):
                        native.recording_advance_orientation(initial, omega, F(3, 8), **arguments)
                self.assertEqual(changed, [final])
                self.assertEqual(len(saved), 1)
                self.assertEqual(cache_identity(work), saved[0][0])
                self.assertEqual(work._cache_generation, saved[0][1])
                self.assertLessEqual(len(work._cache), 256)

    def test_reentrant_publication_keeps_nested_cache_work_and_final_admission(self):
        for mutate in (False, True):
            with self.subTest(mutate=mutate):
                initial = RotationValue(UNIT)
                native, omega, arguments = prepare(initial)
                work = native.work
                key = next(key for key in work._cache if spin_key(key))
                previous, remember = work._cache[key], work.remember
                nested_key, nested_value = ("nested completed spin test",), object()
                def publish(current, value, *, admission=None):
                    if spin_key(current):
                        def reenter():
                            work.external_check = None
                            remember(nested_key, nested_value)
                            if mutate:
                                object.__setattr__(initial, "error_rad", F(1, 100))
                        work.external_check = reenter
                    return remember(current, value, admission=admission)
                with patch.object(work, "remember", side_effect=publish):
                    if mutate:
                        with self.assertRaises(_UnsupportedPlanar):
                            native.recording_advance_orientation(initial, omega, F(3, 8), **arguments)
                    else:
                        result = native.recording_advance_orientation(initial, omega, F(3, 8), **arguments)
                        self.assertGreater(result.w, 0)
                self.assertIs(work._cache[key], previous)
                self.assertIs(work._cache[nested_key], nested_value)

    def test_publication_cancellation_preserves_previous_cursor_and_error_identity(self):
        native, omega, arguments = prepare()
        work = native.work
        key = next(key for key in work._cache if spin_key(key))
        previous, remember = work._cache[key], work.remember
        marker = RuntimeError("cancel completed spin publication")
        def publish(current, value, *, admission=None):
            if spin_key(current):
                work.external_check = lambda: (_ for _ in ()).throw(marker)
            return remember(current, value, admission=admission)
        with patch.object(work, "remember", side_effect=publish):
            with self.assertRaises(RuntimeError) as caught:
                native.recording_advance_orientation(UNIT, omega, F(3, 8), **arguments)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertIs(work._cache[key], previous)


if __name__ == "__main__":
    unittest.main()
