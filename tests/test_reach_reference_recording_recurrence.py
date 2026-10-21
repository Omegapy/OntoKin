"""Recording angle updates retain independent outward source enclosures."""
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_reference import (
    Interval, MAX_CACHE, MAX_OPERAND_BITS, ReachReference, ReferenceError,
    _Arithmetic, _PoseArithmetic, build_reference,
)
from ontokin.scene import ExportOptions
from reach_agent_support import source_case


def arithmetic(*, bits=128, cap=MAX_OPERAND_BITS):
    return _PoseArithmetic(_Arithmetic(work=ReachExecutionWork(max_operand_bits=cap), bits=bits))


def point(value):
    value = F(value)
    return Interval(value, value)


def cursor_rows(ops):
    return {key: value for key, value in ops.a.cache.items()
            if key[:1] == ("reference_pose",) and key[3] == "recording_sincos"}


def direct(ops, coordinate):
    return ops.a.sincos(ops.a.div(coordinate, 2))


class IndependentRecordingAngleTests(unittest.TestCase):
    def test_accumulated_intervals_contain_finer_independent_direct_enclosures(self):
        for initial, step in ((F(-7), F(1, 8)), (F(1, 3), F(-1, 17))):
            ops, fine, context = arithmetic(), arithmetic(bits=256), object()
            for index in range(68):
                coordinate = point(initial + index * step)
                actual = ops._recording_sincos(coordinate, context=context, clock=F(index))
                expected = direct(fine, coordinate)
                with self.subTest(initial=initial, index=index):
                    for enclosed, tighter in zip(actual, expected):
                        self.assertLessEqual(enclosed.lo, tighter.lo)
                        self.assertGreaterEqual(enclosed.hi, tighter.hi)
                        self.assertLess(enclosed.hi - enclosed.lo, F(1, 1 << 100))
                self.assertLessEqual(len(ops.a.cache), MAX_CACHE)
            self.assertLessEqual(ops.a.work.operations, 100000)
            self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))

    def test_equal_exact_deltas_reuse_their_independent_series_and_reduce_work(self):
        ops, baseline, context = arithmetic(), arithmetic(), object()
        with patch.object(ops.a, "_series_sincos", wraps=ops.a._series_sincos) as series:
            for index in range(1, 17):
                coordinate = point(F(index, 8))
                ops._recording_sincos(coordinate, context=context, clock=F(index, 8))
                direct(baseline, coordinate)
        # The initial half-angle and every later exact delta/2 are 1/16.
        self.assertEqual(series.call_count, 1)
        self.assertLess(ops.a.work.operations, baseline.a.work.operations)
        self.assertEqual(next(iter(cursor_rows(ops).values()))[4], 15)

    def test_new_context_rewind_large_jump_and_step_bound_reseed_directly(self):
        ops, context = arithmetic(), object()
        ops._recording_sincos(point(F(1, 8)), context=context, clock=F(1))
        ops._recording_sincos(point(F(1, 4)), context=context, clock=F(2))
        self.assertEqual(next(iter(cursor_rows(ops).values()))[4], 1)
        fresh = object()
        coordinate = point(F(3, 8))
        self.assertEqual(ops._recording_sincos(coordinate, context=fresh, clock=F(3)), direct(arithmetic(), coordinate))
        self.assertEqual(len(cursor_rows(ops)), 2)
        self.assertEqual(ops._recording_sincos(coordinate, context=context, clock=F(1)), direct(arithmetic(), coordinate))
        coordinate = point(20)
        self.assertEqual(ops._recording_sincos(coordinate, context=context, clock=F(2)), direct(arithmetic(), coordinate))
        for index in range(1, 65):
            coordinate = point(20 + F(index, 8))
            ops._recording_sincos(coordinate, context=context, clock=F(index + 2))
        key = ops._key("recording_sincos", context)
        self.assertEqual(ops.a.cache[key][4], 64)
        coordinate = point(20 + F(65, 8))
        self.assertEqual(ops._recording_sincos(coordinate, context=context, clock=F(67)), direct(arithmetic(), coordinate))
        self.assertEqual(ops.a.cache[key][4], 0)

    def test_eviction_reseeds_without_an_additional_cache_or_budget(self):
        ops, context = arithmetic(), object()
        for index in (1, 2):
            ops._recording_sincos(point(F(index, 8)), context=context, clock=F(index))
        for index in range(MAX_CACHE + 1):
            ops.a.remember(("unrelated", index), F(index))
        self.assertFalse(cursor_rows(ops))
        self.assertEqual(len(ops.a.cache), MAX_CACHE)
        coordinate = point(F(3, 8))
        self.assertEqual(ops._recording_sincos(coordinate, context=context, clock=F(3)), direct(arithmetic(), coordinate))
        self.assertEqual(next(iter(cursor_rows(ops).values()))[4], 0)
        self.assertEqual(len(ops.a.cache), MAX_CACHE)
        self.assertEqual(ops.a.work.max_operations, 100000)

    def test_other_precisions_intervals_caps_and_large_delta_operands_remain_direct(self):
        cases = ((128, MAX_OPERAND_BITS, Interval(F(1, 8), F(1, 4))),
                 (32, MAX_OPERAND_BITS, point(F(1, 3))),
                 (256, MAX_OPERAND_BITS, point(F(1, 3))),
                 (128, MAX_OPERAND_BITS - 1, point(F(1, 3))),
                 (128, MAX_OPERAND_BITS, Interval(False, False)))
        for bits, cap, coordinate in cases:
            ops, expected = arithmetic(bits=bits, cap=cap), arithmetic(bits=bits, cap=cap)
            with self.subTest(bits=bits, cap=cap, coordinate=coordinate):
                self.assertEqual(ops._recording_sincos(coordinate, context=object(), clock=F(1)), direct(expected, coordinate))
                self.assertFalse(cursor_rows(ops))
        # These individual coordinates fit the old division/grid domain,
        # while their exact subtraction's prospective denominator does not.
        ops, context = arithmetic(), object()
        for index in (1, 3):
            coordinate = point(F(index, 1 << 17000))
            self.assertEqual(ops._recording_sincos(coordinate, context=context, clock=F(index)), direct(arithmetic(), coordinate))
        self.assertEqual(next(iter(cursor_rows(ops).values()))[4], 0)
        for callback_only in (True, False):
            budget = ReachExecutionWork()
            current = (_Arithmetic(check=budget.tick) if callback_only else
                       _Arithmetic(work=SimpleNamespace(tick=budget.tick, max_operand_bits=MAX_OPERAND_BITS)))
            ops, context = _PoseArithmetic(current), object()
            for index in (1, 2):
                coordinate = point(F(index, 8))
                self.assertEqual(ops._recording_sincos(coordinate, context=context, clock=F(index)), direct(arithmetic(), coordinate))
            self.assertFalse(cursor_rows(ops))

    def test_narrowing_inside_delta_preflight_retries_the_admissible_direct_path(self):
        ops, context = arithmetic(), object()
        ops._recording_sincos(point(F(1, 1 << 16000)), context=context, clock=F(1))
        coordinate, calls = point(F(3, 1 << 16001)), 0
        def narrow():
            nonlocal calls
            calls += 1
            if calls == 2:
                ops.a.work.max_operand_bits = 20000
        with patch.object(ops.a.work, "external_check", side_effect=narrow):
            actual = ops._recording_sincos(coordinate, context=context, clock=F(2))
        # The delta's prospective denominator is 32003 bits; the original
        # half-angle division needs only 16004 before its outward grid.
        self.assertEqual(actual, direct(arithmetic(cap=20000), coordinate))
        self.assertFalse(cursor_rows(ops))
        self.assertLessEqual(ops.a.work.operations, 100000)

    def test_callback_thrown_reference_error_is_not_retried_after_narrowing(self):
        ops, context = arithmetic(), object()
        ops._recording_sincos(point(F(1, 1 << 16000)), context=context, clock=F(1))
        before, calls = cursor_rows(ops), 0
        marker = ReferenceError("resource", "callback owns this rejection")
        def cancel():
            nonlocal calls
            calls += 1
            if calls == 2:
                ops.a.work.max_operand_bits = 20000
                raise marker
        with patch.object(ops.a.work, "external_check", side_effect=cancel):
            with self.assertRaises(ReferenceError) as caught:
                ops._recording_sincos(point(F(3, 1 << 16001)), context=context, clock=F(2))
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.a.work.callback_error, marker)
        self.assertEqual(calls, 2)
        self.assertEqual(cursor_rows(ops), before)

    def test_cap_changes_reenter_the_direct_proof_and_cannot_publish_a_narrower_cursor(self):
        ops, context = arithmetic(), object()
        ops._recording_sincos(point(F(1, 8)), context=context, clock=F(1))
        def narrow():
            ops.a.work.max_operand_bits = MAX_OPERAND_BITS - 1
        with patch.object(ops.a.work, "external_check", side_effect=narrow):
            actual = ops._recording_sincos(point(F(1, 4)), context=context, clock=F(2))
        self.assertEqual(actual, direct(arithmetic(cap=MAX_OPERAND_BITS - 1), point(F(1, 4))))
        self.assertFalse(cursor_rows(ops))
        ops, context = arithmetic(), object()
        ops._recording_sincos(point(F(1, 8)), context=context, clock=F(1))
        original = ops.a.remember
        def narrow_at_publication(key, value):
            if key[:1] == ("reference_pose",) and key[3] == "recording_sincos":
                ops.a.work.max_operand_bits = 64
            return original(key, value)
        with patch.object(ops.a, "remember", side_effect=narrow_at_publication):
            with self.assertRaises(ReferenceError) as caught:
                ops._recording_sincos(point(F(1, 4)), context=context, clock=F(2))
        self.assertEqual(caught.exception.code, "resource")
        self.assertTrue(all(key[2] == MAX_OPERAND_BITS for key in cursor_rows(ops)))
        with self.assertRaises(ReferenceError):
            ops._recording_sincos(point(F(1, 4)), context=context, clock=F(3))

    def test_cancellation_retains_exception_identity_and_never_advances_a_failed_cursor(self):
        for fail_at in (1, 6):
            ops, context = arithmetic(), object()
            ops._recording_sincos(point(F(1, 8)), context=context, clock=F(1))
            before = cursor_rows(ops)
            calls, marker = 0, RuntimeError("cancel independent recording angle")
            def cancel():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    raise marker
            with patch.object(ops.a.work, "external_check", side_effect=cancel):
                with self.assertRaises(RuntimeError) as caught:
                    ops._recording_sincos(point(F(1, 4)), context=context, clock=F(2))
            self.assertIs(caught.exception, marker)
            self.assertIs(ops.a.work.callback_error, marker)
            self.assertEqual(cursor_rows(ops), before)


class IndependentRecordingContextTests(unittest.TestCase):
    def test_stationary_source_hinges_keep_their_direct_cache_across_clocks(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(1, 2), work=compiler.reach_work)
        context = object()
        with patch.object(reference.p, "hinge", wraps=reference.p.hinge) as hinge:
            for time in (F(1, 8), F(1, 4), F(3, 8)):
                reference.recording_pose_enclosures(("rig.arm.forearm.tip.frame",), time,
                                                    recording_context=context)
        stationary = [call for call in hinge.call_args_list if call.args[1] == 0]
        moving = [call for call in hinge.call_args_list if call.args[1] != 0]
        self.assertEqual(len(stationary), 3)
        self.assertEqual(len(moving), 3)
        self.assertTrue(all(call.kwargs["recording_context"] is None for call in stationary))
        self.assertTrue(all(call.kwargs["recording_context"] is not None for call in moving))

    def test_source_phase_side_and_pass_isolation_leave_full_source_evidence_direct(self):
        compiler = compile_construction(source_case("L02"))
        reference = build_reference(compiler.model, end=F(3, 4), work=compiler.reach_work)
        carriers, context = ("rig.arm.forearm.tip.frame",), object()
        histories = reference.boundary_states()
        observed = []
        original = reference.p._recording_sincos
        def capture(coordinate, *, context, clock):
            observed.append((clock, context[0][0]))
            return original(coordinate, context=context, clock=clock)
        with patch.object(reference.p, "_recording_sincos", side_effect=capture):
            for time, side in ((F(1, 4), "after"), (F(3, 8), "after"),
                               (F(1, 2), "before"), (F(1, 2), "after"), (F(5, 8), "after")):
                reference.recording_pose_enclosures(carriers, time, side, recording_context=context)
        scopes = {(time, scope[-1]): scope for time, scope in observed}
        self.assertEqual(scopes[F(1, 4), "after"], scopes[F(3, 8), "after"])
        self.assertNotEqual(scopes[F(1, 2), "before"], scopes[F(1, 2), "after"])
        self.assertEqual(scopes[F(1, 2), "after"], scopes[F(5, 8), "after"])
        self.assertNotEqual(scopes[F(1, 4), "after"], scopes[F(1, 2), "before"])
        with patch.object(reference.p, "_recording_sincos", side_effect=AssertionError("recording-only cursor")):
            default = reference.recording_pose_enclosures(carriers, F(5, 8))
            complete = reference.pose_enclosure(carriers[0], F(5, 8))
            self.assertEqual(default[carriers[0]].position, complete.position)
            self.assertEqual(default[carriers[0]].orientation, complete.orientation)
            self.assertEqual(reference.boundary_states(), histories)
        fresh = reference.recording_pose_enclosures(carriers, F(5, 8), recording_context=object())
        self.assertEqual(fresh, default)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        self.assertLessEqual(len(reference._poses), MAX_CACHE)
        self.assertLessEqual(compiler.budget.operations, 100000)
        with self.assertRaises(ValueError):
            reference.recording_pose_enclosures(carriers, F(1, 4), ideal=False, recording_context=context)
        with self.assertRaises(ValueError):
            reference.recording_pose_enclosures(carriers, F(1, 4), recording_context={})

    def test_actual_reader_creates_a_fresh_context_without_changing_recording_bytes(self):
        original, outputs, contexts = ReachReference.recording_pose_enclosures, [], []
        for use_recurrence in (True, False):
            observed = []
            def capture(reference, carriers, time, side="after", *, ideal=True, recording_context=None):
                if recording_context is not None:
                    observed.append(recording_context)
                return original(reference, carriers, time, side, ideal=ideal,
                                recording_context=recording_context if use_recurrence else None)
            compiler = compile_construction(source_case("P01"))
            with patch.object(ReachReference, "recording_pose_enclosures", new=capture):
                result = export_glb(compiler.model,
                    options=ExportOptions(end=F(1, 4), fps=1, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertGreater(len(observed), 1)
            self.assertTrue(all(type(value) is object and value is observed[0] for value in observed))
            self.assertLessEqual(compiler.budget.operations, 100000)
            contexts.append(observed[0])
            outputs.append(result.data)
        self.assertIsNot(contexts[0], contexts[1])
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
