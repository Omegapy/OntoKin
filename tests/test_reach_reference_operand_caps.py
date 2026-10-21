"""A live narrower work domain cannot inherit a broader independent proof."""
from copy import deepcopy
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_reference
from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.reach_reference import (
    Interval, MAX_CACHE, MAX_OPERAND_BITS, ReachReference, ReferenceError,
    _Action, _Arithmetic, _PoseArithmetic, build_reference,
)
from reach_agent_support import source_case


class TickOnly:
    def __init__(self):
        self.operations = 0

    def tick(self):
        self.operations += 1
        if self.operations > 100000:
            raise RuntimeError("shared work exhausted")


def arithmetic(limit=MAX_OPERAND_BITS, *, bits=8):
    work = TickOnly()
    work.max_operand_bits = limit
    return _Arithmetic(work=work, bits=bits)


class ReachReferenceOperandCapTests(unittest.TestCase):
    def resource(self, execute):
        with self.assertRaises(ReferenceError) as caught:
            execute()
        self.assertEqual(caught.exception.code, "resource")

    def test_effective_limit_preserves_tick_only_and_never_enlarges_module_domain(self):
        fallback = _Arithmetic(work=TickOnly(), bits=8)
        callback_only = _Arithmetic(check=lambda: None, bits=8)
        self.assertEqual(fallback.operand_limit, MAX_OPERAND_BITS)
        self.assertEqual(callback_only.operand_limit, MAX_OPERAND_BITS)
        self.assertEqual(fallback.exact(1 << 80, 1, "add"), F((1 << 80) + 1))
        current = arithmetic(64)
        self.resource(lambda: current.exact(1 << 80, 1, "add"))
        current.work.max_operand_bits = MAX_OPERAND_BITS * 2
        self.assertEqual(current.operand_limit, MAX_OPERAND_BITS)
        with patch.object(reach_reference, "MAX_OPERAND_BITS", 128):
            self.assertEqual(current.operand_limit, 128)
            self.assertEqual(fallback.operand_limit, 128)
        for limit in (0, -1, True, 64.0, None):
            current.work.max_operand_bits = limit
            with self.subTest(limit=limit):
                self.resource(lambda: current.point(0))

    def test_fraction_preflights_reject_before_the_actual_large_operation(self):
        cases = ((F(1, 1 << 40), F(1, 1 << 40), "add", "__add__"),
                 (F(1 << 40), F(1 << 40), "mul", "__mul__"),
                 (F(1, 1 << 40), F(1 << 40), "div", "__truediv__"))
        for first, last, operation, method in cases:
            current = arithmetic(64)
            with self.subTest(operation=operation), patch.object(F, method, side_effect=AssertionError("allocated")):
                self.resource(lambda: current.exact(first, last, operation))
            self.assertEqual(current.work.operations, 1)

    def test_precision_grid_radical_and_series_shifts_use_the_live_limit(self):
        self.resource(lambda: arithmetic(16, bits=16))
        current = arithmetic(16)
        self.resource(lambda: current.grid(F(1 << 9), F(1 << 9)))
        with patch.object(reach_reference.math, "isqrt", side_effect=AssertionError("allocated radical")):
            self.resource(lambda: current.sqrt(F(1)))
        self.resource(lambda: current._atan_small(F(0)))
        self.resource(lambda: current._series_sincos(F(0)))
        for first, last, operation in ((1, 16, "shift"), (1 << 9, 1 << 9, "mul"),
                                       (1 << 15, 1, "add")):
            self.resource(lambda: current._series_integer(first, last, operation))
        existing = arithmetic(bits=128)
        existing.work.max_operand_bits = 128
        # Even zero endpoints cannot use a previously allocated 129-bit grid.
        self.resource(lambda: existing.grid(F(0), F(0)))

    def test_omitted_interval_corners_still_check_all_old_prospective_widths(self):
        tiny = F(1, 1 << 80)
        cases = (("mul", Interval(tiny, F(1, 2)), Interval(F(1, 3), 1 + tiny)),
                 ("div", Interval(F(1, 3), F(1, 2) + tiny), Interval(F(1, 2), 1 + tiny)))
        for operation, first, last in cases:
            current = arithmetic(125)
            with self.subTest(operation=operation), patch.object(current, "exact", side_effect=AssertionError("selected corner")):
                self.resource(lambda: getattr(current, operation)(first, last))

    def test_zero_and_identity_shortcuts_guard_every_supplied_interval_endpoint(self):
        current = arithmetic(64)
        pose = _PoseArithmetic(current)
        zero, one = Interval(F(0), F(0)), Interval(F(1), F(1))
        huge = Interval(F(1 << 80), F(1 << 80))
        unit, invalid = (one, zero, zero, zero), (huge, zero, zero, zero)
        queries = (lambda: current.add(zero, huge), lambda: current.mul(zero, huge),
                   lambda: current.div(zero, huge), lambda: current.mul(one, huge),
                   lambda: pose.multiply(unit, invalid), lambda: pose.multiply(invalid, unit),
                   lambda: pose.rotate(invalid, (zero, zero, zero)), lambda: pose.conjugate(invalid))
        for index, query in enumerate(queries):
            with self.subTest(index=index):
                self.resource(query)

    def test_nested_normalization_and_trig_proofs_recompute_under_a_lower_cap(self):
        for operation in ("quaternion", "sincos"):
            current = arithmetic(bits=128)
            pose = _PoseArithmetic(current)
            query = (lambda: pose.quaternion((1, 1, 0, 0))) if operation == "quaternion" else (lambda: current.sincos(F(1, 2)))
            query()
            self.assertTrue(current.cache)
            current.work.max_operand_bits = 256
            with self.subTest(operation=operation):
                self.resource(query)
            self.assertEqual(current._cache_operand_limit, 256)
            self.assertLessEqual(len(current.cache), MAX_CACHE)

    def test_callback_narrowing_precedes_all_zero_unit_and_projection_shortcuts(self):
        zero, one = Interval(F(0), F(0)), Interval(F(1), F(1))
        huge = Interval(F(1 << 80), F(1 << 80))
        tiny = Interval(F(1, 1 << 80), F(1, 1 << 80))
        unit, zeros = (one, zero, zero, zero), (zero, zero, zero)
        huge_vector, huge_quaternion = (huge, zero, zero), (huge, zero, zero, zero)
        for query in (
            lambda a, p: a.add(zero, huge),
            lambda a, p: a.mul(zero, huge),
            lambda a, p: a.mul(one, huge),
            lambda a, p: a.div(zero, huge),
            lambda a, p: a.round64(huge),
            lambda a, p: a.sqrt(tiny),
            lambda a, p: p.add(zeros, huge_vector),
            lambda a, p: p.scale(huge_vector, one),
            lambda a, p: p.cross(zeros, huge_vector),
            lambda a, p: p.rotate(unit, huge_vector),
            lambda a, p: p.quaternion(huge_quaternion),
            lambda a, p: p.conjugate(huge_quaternion),
        ):
            current = arithmetic()
            original = current.check
            def narrow():
                current.work.max_operand_bits = 64
                original()
            current.check = narrow
            with self.subTest(query=query.__code__.co_firstlineno):
                self.resource(lambda: query(current, _PoseArithmetic(current)))

    def test_later_vector_decode_cannot_retain_an_earlier_wide_component(self):
        current = arithmetic()
        original = current.check
        calls = 0
        def narrow():
            nonlocal calls
            calls += 1
            if calls == 2:
                current.work.max_operand_bits = 64
            original()
        current.check = narrow
        self.resource(lambda: _PoseArithmetic(current).vector((F(1 << 80), F(0), F(0))))

    def test_later_component_arithmetic_readmits_all_retained_result_endpoints(self):
        zero, one, two = (Interval(F(value), F(value)) for value in (0, 1, 2))
        huge = Interval(F(1 << 80), F(1 << 80))
        medium = Interval(F(1 << 40), F(1 << 40))
        unit, zeros = (one, zero, zero, zero), (zero, zero, zero)
        for name, at, query in (
            ("add", 5, lambda p: p.add((huge, zero, zero), (one, zero, zero))),
            ("scale", 5, lambda p: p.scale((huge, zero, zero), two)),
            ("cross", 8, lambda p: p.cross((zero, medium, zero), (zero, zero, medium))),
            ("make", 1, lambda p: p.make(position=(huge, zero, zero), orientation=unit,
                                        velocity=(zero, F(0), zero), omega=zeros, normalized=True)),
        ):
            current = arithmetic()
            original = current.check
            calls = 0
            def narrow():
                nonlocal calls
                calls += 1
                if calls == at:
                    current.work.max_operand_bits = 64
                original()
            current.check = narrow
            with self.subTest(operation=name):
                self.resource(lambda: query(_PoseArithmetic(current)))
            self.assertGreaterEqual(current.work.operations, at)

    def test_integer_tables_cannot_reuse_a_wider_allocation_proof(self):
        current = arithmetic()
        factorials = current._series_factorials(31)
        current._series_coefficients(8, 10, factorials)
        current.work.max_operand_bits = 64
        self.resource(lambda: current._series_factorials(31))
        self.resource(lambda: current._series_coefficients(8, 10, factorials))
        self.assertEqual(current._cache_operand_limit, 64)

    def test_cap_changes_clear_the_same_bounded_cache_and_preserve_cancellation(self):
        current = arithmetic()
        pose = _PoseArithmetic(current)
        first = pose.identity()
        current.work.max_operand_bits = 64
        second = pose.identity()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        current.work.max_operand_bits = MAX_OPERAND_BITS
        third = pose.identity()
        self.assertEqual(first, third)
        self.assertIsNot(first, third)
        for index in range(MAX_CACHE + 2):
            current.remember(("padding", index), F(index))
        self.assertEqual(len(current.cache), MAX_CACHE)
        before = dict(current.cache)
        current.work.max_operand_bits = 64
        marker = RuntimeError("cancel changed-cap proof reset")
        for fail_at in (1, 2):
            calls = 0
            def cancel():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    raise marker
            with patch.object(current, "check", side_effect=cancel):
                with self.assertRaises(RuntimeError) as caught:
                    current.lookup(("padding", MAX_CACHE + 1))
            self.assertIs(caught.exception, marker)
            self.assertEqual(current.cache, before)

    def test_cap_change_at_insertion_cannot_publish_a_broader_quaternion_proof(self):
        current = arithmetic(bits=32)
        pose = _PoseArithmetic(current)
        original = current.remember
        def lower_at_final_proof(key, value):
            if key[:1] == ("reference_pose",) and key[3] == "quaternion":
                current.work.max_operand_bits = 64
            return original(key, value)
        with patch.object(current, "remember", side_effect=lower_at_final_proof):
            pose.quaternion((1, 1, 0, 0))
        # Its stored endpoints fit, but its original radical preflight did not.
        self.resource(lambda: pose.quaternion((1, 1, 0, 0)))

    def test_affine_and_per_sample_joint_reuse_do_not_hide_narrower_division(self):
        reference = object.__new__(ReachReference)
        reference.a = arithmetic(bits=8)
        action = SimpleNamespace(kind="tween", goal=F(1, 1 << 80), duration=F(1 << 80))
        active = _Action(status="running", initial=F(0), ideal_initial=F(0))
        reference.model = SimpleNamespace(actions={"action": action})
        state = SimpleNamespace(claims={("joint", "coordinate"): "action"}, actions={"action": active})
        reference._coordinate("joint", F(0), state, ideal=True)
        observations = {}
        reference._joint_observation("joint", F(0), state, observations)
        reference.a.work.max_operand_bits = 125
        for query in (lambda: reference._coordinate("joint", F(0), state, ideal=True),
                      lambda: reference._joint_observation("joint", F(0), state, observations)):
            with patch.object(reference.a, "exact", wraps=reference.a.exact) as exact:
                self.resource(query)
            self.assertEqual([call.args[2] for call in exact.call_args_list], ["sub", "div"])

    def test_outer_source_proofs_reenter_their_cold_paths_after_a_cap_change(self):
        carrier, time = "rig.arm.forearm.tip.frame", F(1, 8)
        for kind in ("pose", "phase", "point", "basis", "targets"):
            compiled = compile_construction(source_case("P01"))
            reference = build_reference(compiled.model, end=F(1, 4), work=compiled.reach_work)
            state = reference._state_at(time, "after")
            marker = RuntimeError("entered current-cap independent proof")
            if kind == "pose":
                query = lambda: reference._pose_map(time, state, ideal=True, selected=(carrier,))
                patched, member = reference, "_incoming"
            elif kind == "phase":
                query = lambda: reference.phases(carrier, F(0), F(1, 4))
                patched, member = reference, "_phase"
            elif kind == "point":
                query = lambda: reference.point_phase(carrier, time)
                patched, member = reference, "_phase"
            elif kind == "basis":
                query = lambda: reference._source_basis(carrier, F(0), F(1, 4), state)
                patched, member = reference, "_incoming"
            else:
                event = next(event for block in reference.model.events for event in block.events
                             if event.kind == "start" and reference.model.actions[event.target].kind == "reach_planar")
                query = lambda: reference._event(event, 0, F(0), deepcopy(reference._before[0]), {}, set(), [])
                patched, member = reach_reference, "_canonical_targets"
            query()
            reference.a.work.max_operand_bits = MAX_OPERAND_BITS - 1
            with self.subTest(kind=kind), patch.object(patched, member, side_effect=marker):
                with self.assertRaises(RuntimeError) as caught:
                    query()
            self.assertIs(caught.exception, marker)
            self.assertEqual(reference._numeric_cache_limit, MAX_OPERAND_BITS - 1)

    def test_unchanged_default_cap_preserves_values_and_every_operation_charge(self):
        def calculate(work):
            current = _Arithmetic(work=work, bits=32)
            pose = _PoseArithmetic(current)
            trig = current._series_sincos(F(1, 4))
            parent = pose.make(position=(1, 2, 3), orientation=(F(1, 2),) * 4, omega=(0, 0, 2))
            local = pose.make(position=(F(1, 3), 1, 0))
            first, second = pose.compose(parent, local), pose.compose(parent, local)
            return (trig, first, second), work.operations
        actual, actual_count = calculate(ReachExecutionWork())
        expected, expected_count = calculate(TickOnly())
        self.assertEqual(actual, expected)
        self.assertEqual(actual_count, expected_count)


if __name__ == "__main__":
    unittest.main()
