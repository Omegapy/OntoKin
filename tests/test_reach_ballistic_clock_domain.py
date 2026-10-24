"""Ballistic width proofs retain the original clock domain and fallback order."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import fields
from fractions import Fraction as F
import struct
import unittest
from unittest.mock import patch

from ontokin import reach_recording_fast as fast
from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_runtime import ReachSimulator
from ontokin.reach_transfer_bounds import _OwnerRef
from test_reach_recording_dynamic import law
from test_reach_recording_sampler import DATA


ZERO = (0.0, 0.0, 0.0)


def original_range():
    """Retain both original comparisons without changing any work charge."""
    return patch.object(fast, "_ballistic_clock_in_range", return_value=False)


def prepared(*, horizon=F(2), position=(0.25, -0.0, 0.0),
             velocity=(0.5, -0.25, 0.0), acceleration=(0.125, 0.5, 0.0),
             work_type=Work, ops_type=fast.Binary64RecordingOps):
    ops = ops_type(ReachPoseOps(work_type()))
    proved = law(ops, position, velocity, acceleration, horizon)
    return ops, proved


def result_bits(result):
    values, zeros = result
    return struct.pack("<3d", *values), zeros


def changed_counts(work, before):
    return {name: value - before.get(name, 0) for name, value in work.counts.items()
            if value != before.get(name, 0)}


class ReachBallisticClockDomainTests(unittest.TestCase):
    def assert_source_state_values_equal(self, left, right):
        """Compare complete state values and the explicit source-owner layout.

        CellAnchor.lineage deliberately retains each request's model, work,
        tables and source objects by identity. Its literal source values and
        shared native method receipts still have to match exactly.
        """
        self.assertIs(type(left), type(right))
        for field in fields(left):
            if field.name != "dynamic_cells":
                self.assertEqual(getattr(left, field.name), getattr(right, field.name), field.name)
        self.assertEqual(left.dynamic_cells.keys(), right.dynamic_cells.keys())
        self.assertTrue(left.dynamic_cells)

        def separate_owner(first, second):
            self.assertIs(type(first), _OwnerRef)
            self.assertIs(type(second), _OwnerRef)
            self.assertEqual(len(first), 1)
            self.assertEqual(len(second), 1)
            self.assertIs(type(first[0]), type(second[0]))
            if first[0] is None:
                self.assertIs(second[0], None)
            else:
                self.assertIsNot(first, second)
                self.assertIsNot(first[0], second[0])

        for path, first in left.dynamic_cells.items():
            second = right.dynamic_cells[path]
            self.assertIs(type(first), type(second))
            for field in fields(first):
                if field.name != "lineage":
                    self.assertEqual(getattr(first, field.name), getattr(second, field.name), field.name)
            self.assertEqual(len(first.lineage), 2)
            self.assertEqual(len(second.lineage), 2)
            left_header, left_tables = first.lineage
            right_header, right_tables = second.lineage
            self.assertEqual(len(left_header), 5)
            self.assertEqual(len(right_header), 5)
            for old, new in zip(left_header[:3], right_header[:3]):
                separate_owner(old, new)
            self.assertEqual(left_header[3:], right_header[3:])
            self.assertEqual(len(left_tables), len(right_tables))
            for old_table, new_table in zip(left_tables, right_tables):
                self.assertEqual(len(old_table), 3)
                self.assertEqual(len(new_table), 3)
                self.assertEqual(old_table[0], new_table[0])
                separate_owner(old_table[1], new_table[1])
                self.assertEqual(len(old_table[2]), len(new_table[2]))
                for old_row, new_row in zip(old_table[2], new_table[2]):
                    self.assertEqual(len(old_row), 4)
                    self.assertEqual(len(new_row), 4)
                    self.assertEqual(old_row[0], new_row[0])
                    separate_owner(old_row[1], new_row[1])
                    self.assertEqual(len(old_row[2]), len(new_row[2]))
                    for old, new in zip(old_row[2], new_row[2]):
                        separate_owner(old, new)
                    self.assertEqual(old_row[3], new_row[3])

    def test_strict_interior_widths_preserve_results_and_remove_only_two_comparisons(self):
        for elapsed in (F(1, 7), F(1, 2), F(1), F(1, 1 << 249), F(1 << 249),
                        F((1 << 1023) - 1, (1 << 1023) + 1)):
            outcomes = []
            for enabled in (False, True):
                ops, proved = prepared(horizon=F(1 << 250), velocity=ZERO, acceleration=ZERO)
                before, calls = dict(ops.work.counts), []
                ops.work.external_check = lambda: calls.append(ops.work.operations)
                with nullcontext() if enabled else original_range():
                    result = ops._ballistic_position(proved, elapsed)
                counts = changed_counts(ops.work, before)
                self.assertEqual(sum(counts.values()), len(calls))
                outcomes.append((result_bits(result), counts, len(calls)))
            with self.subTest(elapsed=elapsed):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertEqual(outcomes[0][1].pop("exact_compare"), 3)
                self.assertEqual(outcomes[1][1].pop("exact_compare"), 1)
                self.assertEqual(outcomes[0][1], outcomes[1][1])
                self.assertEqual(outcomes[0][2] - outcomes[1][2], 2)

    def test_inclusive_edges_and_unproved_interior_shapes_keep_both_original_comparisons(self):
        for elapsed in (F(1, 1 << 250), F(1 << 250), F(3, 1 << 251), F(1 << 251, 3)):
            outcomes = []
            for enabled in (False, True):
                ops, proved = prepared(horizon=F(1 << 250), velocity=ZERO, acceleration=ZERO)
                before = dict(ops.work.counts)
                with nullcontext() if enabled else original_range():
                    result = ops._ballistic_position(proved, elapsed)
                outcomes.append((result_bits(result), changed_counts(ops.work, before)))
            with self.subTest(elapsed=elapsed):
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][1]["exact_compare"], 3)

    def test_width_proof_is_sufficient_against_independent_exact_boundary_values(self):
        ops, _ = prepared()
        lower, upper = F(1, 1 << 250), F(1 << 250)
        values = {F(0), F(-1), lower, upper}
        for base in (lower, upper):
            for scale in (F(1, 2), F(1) - F(1, 1 << 80), F(1),
                          F(1) + F(1, 1 << 80), F(2)):
                values.add(base * scale)
        for numerator in ((1 << 1023) - 1, (1 << 1023) + 1):
            for shift in (-251, -250, -249, 0, 249, 250, 251):
                denominator = (1 << (1023 + shift)) + 1
                values.add(F(numerator, denominator))
        before = ops.work.operations
        accepted = [value for value in values if fast._ballistic_clock_in_range(ops, value)]
        self.assertTrue(accepted)
        self.assertTrue(all(lower < value < upper for value in accepted))
        self.assertEqual(ops.work.operations, before)
        self.assertFalse(fast._ballistic_clock_in_range(ops, lower))
        self.assertFalse(fast._ballistic_clock_in_range(ops, upper))

    def test_original_horizon_and_negative_or_tiny_clock_rejections_remain_ordered(self):
        for horizon, elapsed, comparisons in (
                (F(1), F(-1), 0), (F(1), F(3, 2), 1),
                (F(1), F(1, 1 << 251), 2), (F(1), F(1, 1 << 1024), 0)):
            outcomes = []
            for enabled in (False, True):
                ops, proved = prepared(horizon=horizon)
                before = dict(ops.work.counts)
                with nullcontext() if enabled else original_range():
                    with self.assertRaises(fast._UnsupportedPlanar) as caught:
                        ops._ballistic_position(proved, elapsed)
                counts = changed_counts(ops.work, before)
                self.assertNotIn("recording_float_mul", counts)
                outcomes.append((str(caught.exception), counts))
            with self.subTest(horizon=horizon, elapsed=elapsed):
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][1].get("exact_compare", 0), comparisons)

    def test_exact_zero_keeps_original_signed_anchor_bits_without_entering_the_proof(self):
        ops, proved = prepared(position=(-0.0, 0.0, -0.0), velocity=(-0.25, 0.0, 0.0),
                               acceleration=ZERO)
        with patch.object(fast, "_ballistic_clock_in_range", side_effect=AssertionError("zero is direct")):
            actual = ops._ballistic_position(proved, F(0))
        self.assertEqual(result_bits(actual), (struct.pack("<3d", -0.0, 0.0, 0.0),
                                              (False, True, True)))

    def test_native_arithmetic_and_signed_zero_coefficients_are_unchanged(self):
        for position, velocity, acceleration in (
                ((0.25, -0.5, 0.75), (0.5, -0.25, 1.0), (0.125, -0.5, 0.25)),
                ((-0.0, 0.0, -0.0), (-0.0, -0.0, 0.0), ZERO),
                ((1.0, -1.0, 0.0), (float(1 << 249), -float(1 << 249), 0.0),
                 (-float(1 << 250), float(1 << 250), 0.0))):
            outcomes = []
            for enabled in (False, True):
                ops, proved = prepared(position=position, velocity=velocity, acceleration=acceleration)
                with nullcontext() if enabled else original_range():
                    results = tuple(result_bits(ops._ballistic_position(proved, elapsed))
                                    for elapsed in (F(1, 7), F(1, 2), F(1)))
                outcomes.append(results)
            self.assertEqual(outcomes[0], outcomes[1])

    def test_non_native_or_malformed_fields_decline_without_foreign_numeric_dispatch(self):
        class ForeignInt(int):
            def bit_length(self):
                raise AssertionError("foreign integer method")
        class ForeignFraction(F):
            pass
        ops, _ = prepared()
        for field, replacement in (("_numerator", True), ("_numerator", ForeignInt(1)),
                                   ("_denominator", False), ("_denominator", ForeignInt(2)),
                                   ("_numerator", -1), ("_denominator", 0), ("_denominator", -2)):
            value = F(2, 5)
            object.__setattr__(value, field, replacement)
            with self.subTest(field=field, replacement_type=type(replacement).__name__):
                self.assertFalse(fast._ballistic_clock_in_range(ops, value))
        for value in (False, 0.5, 1, ForeignFraction(1, 2), F(1 << 1024, (1 << 1024) + 1)):
            self.assertFalse(fast._ballistic_clock_in_range(ops, value))

    def test_changed_or_mutated_literal_bounds_keep_original_rejection(self):
        for field, replacement in (("_MIN_BALLISTIC_ELAPSED", F(3, 4)),
                                   ("_MAX_BALLISTIC_ELAPSED", F(1, 4))):
            for mutate in (False, True):
                outcomes = []
                for enabled in (False, True):
                    ops, proved = prepared()
                    bound = getattr(fast, field)
                    saved = bound.numerator, bound.denominator
                    before = dict(ops.work.counts)
                    try:
                        if mutate:
                            object.__setattr__(bound, "_numerator", replacement.numerator)
                            object.__setattr__(bound, "_denominator", replacement.denominator)
                        with nullcontext() if mutate else patch.object(fast, field, replacement):
                            with nullcontext() if enabled else original_range():
                                with self.assertRaises(fast._UnsupportedPlanar) as caught:
                                    ops._ballistic_position(proved, F(1, 2))
                        outcomes.append((str(caught.exception), changed_counts(ops.work, before)))
                    finally:
                        if mutate:
                            object.__setattr__(bound, "_numerator", saved[0])
                            object.__setattr__(bound, "_denominator", saved[1])
                self.assertEqual(outcomes[0], outcomes[1])

    def test_custom_comparison_dispatch_runs_at_the_original_lower_bound(self):
        for name in ("_checked_compare", "compare"):
            for enabled in (False, True):
                ops, proved = prepared()
                original = getattr(fast, name)
                marker, seen = RuntimeError("original range dispatch"), []
                def custom(left, right, work):
                    seen.append(right)
                    if right is fast._MIN_BALLISTIC_ELAPSED:
                        raise marker
                    return original(left, right, work)
                with patch.object(fast, name, custom):
                    with nullcontext() if enabled else original_range():
                        with self.assertRaises(RuntimeError) as caught:
                            ops._ballistic_position(proved, F(1, 2))
                self.assertIs(caught.exception, marker)
                self.assertEqual(len(seen), 2)
                self.assertIs(seen[0], proved.horizon)
                self.assertIs(seen[1], fast._MIN_BALLISTIC_ELAPSED)

    def test_custom_work_method_dispatch_retains_original_calls_and_exceptions(self):
        for method in ("charge", "guard", "guard_bits"):
            for class_override in (False, True):
                outcomes = []
                for enabled in (False, True):
                    ops, proved = prepared()
                    work = ops.work
                    original = getattr(Work if class_override else work, method)
                    previous_compares = work.counts.get("exact_compare", 0)
                    marker, calls = RuntimeError("custom comparison work"), []
                    def custom(*args, **kwargs):
                        values = args[1:] if class_override else args
                        calls.append(values[0] if method == "charge" else method)
                        count = work.counts.get("exact_compare", 0) - previous_compares
                        if (method == "charge" and values[0] == "exact_compare" and count == 1
                                or method != "charge" and count == 2):
                            raise marker
                        return original(*args, **kwargs)
                    before = dict(work.counts)
                    with patch.object(Work if class_override else work, method, custom):
                        with nullcontext() if enabled else original_range():
                            with self.assertRaises(RuntimeError) as caught:
                                ops._ballistic_position(proved, F(1, 2))
                    self.assertIs(caught.exception, marker)
                    outcomes.append((calls, changed_counts(work, before)))
                with self.subTest(method=method, class_override=class_override):
                    self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_work_and_ops_subclasses_keep_the_original_three_comparisons(self):
        class ForeignWork(Work):
            pass
        class ForeignOps(fast.Binary64RecordingOps):
            pass
        for settings in ({"work_type": ForeignWork}, {"ops_type": ForeignOps}):
            ops, proved = prepared(**settings)
            before = dict(ops.work.counts)
            self.assertFalse(fast._ballistic_clock_in_range(ops, F(1, 2)))
            ops._ballistic_position(proved, F(1, 2))
            self.assertEqual(changed_counts(ops.work, before)["exact_compare"], 3)

    def test_changed_fraction_comparison_or_field_descriptor_keeps_original_dispatch(self):
        for field in ("__lt__", "numerator"):
            outcomes = []
            for enabled in (False, True):
                ops, proved = prepared()
                original, calls = vars(F)[field], []
                def less(value, other):
                    calls.append("less")
                    return original(value, other)
                def numerator(value):
                    calls.append("numerator")
                    return original.__get__(value, F)
                replacement = less if field == "__lt__" else property(numerator)
                before = dict(ops.work.counts)
                with patch.object(F, field, replacement):
                    with nullcontext() if enabled else original_range():
                        result = ops._ballistic_position(proved, F(1, 2))
                outcomes.append((result_bits(result), calls, changed_counts(ops.work, before)))
            with self.subTest(field=field):
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][2]["exact_compare"], 3)

    def test_fallback_binds_comparison_before_a_custom_work_descriptor(self):
        for enabled in (False, True):
            ops, proved = prepared()
            original = fast._checked_compare
            marker, wrong = RuntimeError("already bound comparison"), RuntimeError("late comparison")
            state = {"armed": False, "reads": 0}
            def late(*args):
                raise wrong
            def compare(left, right, work):
                if right is proved.horizon:
                    result = original(left, right, work)
                    state["armed"] = True
                    return result
                raise marker
            def work(value):
                if state["armed"]:
                    state["reads"] += 1
                    fast._checked_compare = late
                return object.__getattribute__(value, "__dict__")["work"]
            with patch.object(fast, "_checked_compare", compare), \
                 patch.object(fast.Binary64RecordingOps, "work", property(work), create=True):
                with nullcontext() if enabled else original_range():
                    with self.assertRaises(RuntimeError) as caught:
                        ops._ballistic_position(proved, F(1, 2))
            self.assertIs(caught.exception, marker)
            self.assertEqual(state["reads"], 1)

    def test_horizon_callback_mutation_is_seen_at_the_actual_range_admission_point(self):
        for replacement, saving in ((F(3, 7), 2), (F(1, 1 << 251), 0),
                                    (F((1 << 1100) + 1, (1 << 1100) + 3), 0)):
            outcomes = []
            for enabled in (False, True):
                ops, proved = prepared()
                elapsed, calls = F(1, 2), []
                def mutate():
                    calls.append(ops.work.operations)
                    if len(calls) == 2:
                        object.__setattr__(elapsed, "_numerator", replacement.numerator)
                        object.__setattr__(elapsed, "_denominator", replacement.denominator)
                ops.work.external_check = mutate
                with nullcontext() if enabled else original_range():
                    if replacement < F(1, 1 << 250):
                        with self.assertRaises(fast._UnsupportedPlanar) as caught:
                            ops._ballistic_position(proved, elapsed)
                        result = str(caught.exception)
                    else:
                        result = result_bits(ops._ballistic_position(proved, elapsed))
                outcomes.append((result, len(calls)))
            self.assertEqual(outcomes[0][0], outcomes[1][0])
            self.assertEqual(outcomes[0][1] - outcomes[1][1], saving)

    def test_horizon_callback_can_replace_comparison_before_its_original_range_call(self):
        for enabled in (False, True):
            ops, proved = prepared()
            original, marker = fast._checked_compare, RuntimeError("callback installed comparison")
            calls = []
            def changed(*args):
                raise marker
            def callback():
                calls.append(ops.work.operations)
                if len(calls) == 2:
                    fast._checked_compare = changed
            ops.work.external_check = callback
            with patch.object(fast, "_checked_compare", original):
                with nullcontext() if enabled else original_range():
                    with self.assertRaises(RuntimeError) as caught:
                        ops._ballistic_position(proved, F(1, 2))
            self.assertIs(caught.exception, marker)
            self.assertEqual(len(calls), 2)

    def test_initial_or_horizon_narrowing_keeps_the_original_domain_failure(self):
        for cap in (128, 1275, 32767):
            for during_horizon in (False, True):
                outcomes = []
                for enabled in (False, True):
                    ops, proved = prepared()
                    calls = []
                    def callback():
                        calls.append(ops.work.operations)
                        if during_horizon and len(calls) == 2:
                            ops.work.max_operand_bits = cap
                    ops.work.external_check = callback
                    if not during_horizon:
                        ops.work.max_operand_bits = cap
                    before = dict(ops.work.counts)
                    with nullcontext() if enabled else original_range():
                        with self.assertRaises(fast._UnsupportedPlanar) as caught:
                            ops._ballistic_position(proved, F(1, 2))
                    outcomes.append((str(caught.exception), changed_counts(ops.work, before), len(calls)))
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][2], 2 if during_horizon else 1)

    def test_replaced_narrow_work_keeps_lower_compare_callback_before_prospective_guard(self):
        for cap, widen in ((128, False), (128, True), (251, False), (251, True)):
            outcomes = []
            for enabled in (False, True):
                ops, proved = prepared()
                old, replacement = ops.work, Work(max_operand_bits=cap)
                old_calls, new_calls = [], []
                def replace_owner():
                    old_calls.append(old.operations)
                    if len(old_calls) == 2:
                        ops.work = replacement
                def callback():
                    new_calls.append(replacement.operations)
                    if widen and len(new_calls) == 1:
                        replacement.max_operand_bits = 32768
                old.external_check, replacement.external_check = replace_owner, callback
                with nullcontext() if enabled else original_range():
                    if widen:
                        outcome = result_bits(ops._ballistic_position(proved, F(1, 2)))
                    else:
                        with self.assertRaises(ReachAdmissionError) as caught:
                            ops._ballistic_position(proved, F(1, 2))
                        outcome = caught.exception.reach_code, caught.exception.details
                        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                        self.assertEqual(caught.exception.details["consumed"], 251 if cap == 128 else 252)
                outcomes.append((outcome, len(old_calls), len(new_calls), dict(replacement.counts)))
            with self.subTest(cap=cap, widen=widen):
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][1], 2)
                self.assertEqual(outcomes[1][3]["exact_compare"], 2 if widen else 1)

    def test_every_surviving_callback_keeps_cancellation_identity(self):
        ops, proved = prepared()
        before = ops.work.operations
        ops._ballistic_position(proved, F(1, 2))
        operations = ops.work.operations - before
        for stop in range(1, operations + 1):
            ops, proved = prepared()
            start, calls = ops.work.operations, []
            marker = RuntimeError("cancel ballistic sample")
            def cancel():
                calls.append(ops.work.operations)
                if len(calls) == stop:
                    raise marker
            ops.work.external_check = cancel
            with self.assertRaises(RuntimeError) as caught:
                ops._ballistic_position(proved, F(1, 2))
            self.assertIs(caught.exception, marker)
            self.assertIs(ops.work.callback_error, marker)
            self.assertEqual(len(calls), stop)
            self.assertEqual(ops.work.operations - start, stop - 1)

    def test_existing_observer_is_preserved_at_every_surviving_charge(self):
        ops, proved = prepared()
        calls, observed = [], []
        def callback():
            calls.append(ops.work.operations)
        def observer():
            observed.append(ops.work.operations)
        ops.work.external_check, ops.work._source_after_charge = callback, observer
        before = ops.work.operations
        ops._ballistic_position(proved, F(1, 2))
        self.assertEqual(len(calls), ops.work.operations - before)
        self.assertEqual(observed, [value + 1 for value in calls])
        self.assertIs(ops.work.external_check, callback)
        self.assertIs(ops.work._source_after_charge, observer)

    def test_original_remaining_operation_budget_is_not_reset(self):
        ops, proved = prepared()
        before = ops.work.operations
        ops.work.max_operations = before + 4
        with self.assertRaises(ReachAdmissionError) as caught:
            ops._ballistic_position(proved, F(1, 2))
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["limit"], before + 4)
        self.assertEqual(caught.exception.details["consumed"], before + 5)
        self.assertEqual(ops.work.operations, before + 4)

    def test_no_numeric_cache_entry_lookup_eviction_or_capacity_is_added(self):
        ops, proved = prepared()
        for index in range(256):
            ops.work.remember(("existing", index), F(index, 257))
        before, counts = tuple(ops.work._cache.items()), dict(ops.work.counts)
        for elapsed in (F(1, 7), F(1, 3), F(1, 2)):
            ops._ballistic_position(proved, elapsed)
        after = tuple(ops.work._cache.items())
        self.assertEqual([key for key, _ in before], [key for key, _ in after])
        self.assertTrue(all(old is new for (_, old), (_, new) in zip(before, after)))
        self.assertFalse(any(name.startswith("cache_") for name in changed_counts(ops.work, counts)))
        self.assertEqual((ops.work.max_operations, ops.work.max_elapsed_ms,
                          ops.work.max_operand_bits, ops.work.max_cache_entries),
                         (100000, 30000, 32768, 256))

    def test_original_p16_release_and_coast_sampler_outputs_match_with_total_setup_saving(self):
        paths = ("payload.frame", "payload.origin.frame", "rig.arm.forearm.frame")
        for start, end in ((F(2), F(3)), (F(3), F(4))):
            outcomes = []
            for enabled in (False, True):
                callbacks = []
                with nullcontext() if enabled else original_range():
                    compiler = compile_construction(load_file_manifest(DATA / "p16.files.json"),
                        level="constructed", check=lambda: callbacks.append(None))
                    sim = ReachSimulator(compiler.model, work=compiler.reach_work)
                    construction = compiler.budget.operations
                    sim.advance(start, "after")
                    bounds = sim.phase_bounds(start, end)["frames"]
                    moving = sim.recording_moving_frames(sim.state, paths)
                    context = object()
                    sim.recording_frames(start, sim.state, paths, moving_frames=moving,
                                         recording_context=context)
                    before = deepcopy(sim.state)
                    for cell in before.dynamic_cells.values():
                        self.assertIs(cell.lineage[0][0][0], sim.model)
                        self.assertIs(cell.lineage[0][1][0], sim.work)
                        self.assertIs(cell.lineage[0][2][0], sim.pose_ops)
                    samples = []
                    for part in (F(1, 7), F(1, 3), F(3, 4)):
                        actual = fast.sample_bounded_frames(sim, start + (end - start) * part,
                            sim.state, paths, context=context, moving_frames=moving,
                            phase_bounds=bounds, phase_interval=(start, end))
                        bits = tuple((path, struct.pack("<7d", *actual.frames[path].position,
                                                       *actual.frames[path].orientation)) for path in paths)
                        samples.append((actual, bits))
                    self.assertEqual(sim.state, before)
                self.assertLessEqual(compiler.budget.operations, 100000)
                self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                self.assertEqual((sim.work.max_operations, sim.work.max_elapsed_ms,
                                  sim.work.max_operand_bits, sim.work.max_cache_entries),
                                 (100000, 30000, 32768, 256))
                outcomes.append((samples, compiler.budget.operations, sim.work.operations,
                                 len(callbacks), dict(sim.work.counts), construction, before))
            with self.subTest(phase=(start, end)):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertEqual(outcomes[0][5], outcomes[1][5])
                self.assert_source_state_values_equal(outcomes[0][6], outcomes[1][6])
                saved = outcomes[0][1] - outcomes[1][1]
                self.assertGreater(saved, 0)
                self.assertEqual(outcomes[0][2] - outcomes[1][2], saved)
                self.assertEqual(outcomes[0][3] - outcomes[1][3], saved)
                old_counts, new_counts = outcomes[0][4], outcomes[1][4]
                self.assertEqual(old_counts.pop("exact_compare") - new_counts.pop("exact_compare"), saved)
                self.assertEqual(old_counts, new_counts)
                self.assertEqual(saved, 2 * new_counts["recording_ballistic_clock_domain"])
            print(f"P16 ballistic sampler phase {start}-{end}, including construction and phase setup: "
                  f"original={outcomes[0][1]}, candidate={outcomes[1][1]}, "
                  f"numeric={outcomes[0][2]}->{outcomes[1][2]}, callbacks={outcomes[0][3]}->{outcomes[1][3]}")


if __name__ == "__main__":
    unittest.main()
