"""Independent proofs omit executed work without changing their finite domain."""
from contextlib import ExitStack
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.reach_conformance import _Bounds, _Cell
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.reach_reference import (
    MAX_CACHE, Interval, ReferenceError, _Arithmetic, _PoseArithmetic, build_reference,
)
from reach_agent_support import source_case


def point(value, kind=Interval):
    return kind(F(value), F(value))


def previous_add(arithmetic, first, last):
    first, last = arithmetic.interval(first), arithmetic.interval(last)
    arithmetic.tick()
    arithmetic.guard(first.lo, first.hi, last.lo, last.hi)
    if first.lo == first.hi == 0:
        return last
    if last.lo == last.hi == 0:
        return first
    if first.lo == first.hi and last.lo == last.hi:
        value = arithmetic.exact(first.lo, last.lo, "add")
        return arithmetic.grid(value, value)
    return arithmetic.grid(arithmetic.exact(first.lo, last.lo, "add"),
                           arithmetic.exact(first.hi, last.hi, "add"))


def previous_sub(arithmetic, first, last):
    return previous_add(arithmetic, first, arithmetic.neg(last))


def full_planar_rotation(pose, quaternion, vector):
    """The prior scalar/Z Hamilton expansion, including its bounded caches."""
    a = pose.a
    vector = pose.vector(vector)
    a.tick()
    a.guard(*(endpoint for values in (quaternion, vector)
              for part in values for endpoint in (part.lo, part.hi)))
    if pose._zero(vector):
        return vector
    if (quaternion[0].lo == quaternion[0].hi and abs(quaternion[0].lo) == 1
            and pose._zero(quaternion[1:])):
        return vector
    key = pose._key("rotate", tuple(quaternion), vector)
    cached = a.lookup(key)
    if cached is not None:
        return cached
    if not pose._zero((quaternion[1], quaternion[2])):
        pure = (a.point(0), *vector)
        return a.remember(key, pose.multiply(
            pose.multiply(quaternion, pure), pose.conjugate(quaternion))[1:])
    factor_key = pose._key("scalar_z_rotation_factors", tuple(quaternion))
    factors = a.lookup(factor_key)
    if factors is None:
        ww, zz = a.mul(quaternion[0], quaternion[0]), a.mul(quaternion[3], quaternion[3])
        factors = (a.sub(ww, zz), a.mul(2, a.mul(quaternion[0], quaternion[3])), a.add(ww, zz))
        a.remember(factor_key, factors)
    diagonal, off_diagonal, axis_scale = factors
    x, y, z = vector
    return a.remember(key, (
        a.sub(a.mul(diagonal, x), a.mul(off_diagonal, y)),
        a.add(a.mul(off_diagonal, x), a.mul(diagonal, y)), a.mul(axis_scale, z)))


class IndependentGridArithmeticTests(unittest.TestCase):
    def test_dyadic_sums_and_differences_keep_every_previous_endpoint(self):
        values = [point(value) for value in (0, 1, -1, F(3, 4), F(-7, 16), F(1, 1 << 40))]
        values += [Interval(F(-3, 4), F(5, 8)), Interval(F(1, 16), F(17, 16))]
        for operation, previous in (("add", previous_add), ("sub", previous_sub)):
            for first in values:
                for last in values:
                    current, old = _Arithmetic(work=Work(), bits=32), _Arithmetic(work=Work(), bits=32)
                    with self.subTest(operation=operation, first=first, last=last):
                        self.assertEqual(getattr(current, operation)(first, last), previous(old, first, last))

    def test_aligned_endpoints_omit_the_grid_and_subtraction_omits_negation(self):
        for operation, previous in (("add", previous_add), ("sub", previous_sub)):
            current_work, old_work = Work(), Work()
            current, old = _Arithmetic(work=current_work, bits=32), _Arithmetic(work=old_work, bits=32)
            first, last = Interval(F(3, 8), F(7, 8)), Interval(F(1, 4), F(1, 2))
            expected = previous(old, first, last)
            with self.subTest(operation=operation), \
                 patch.object(current, "grid", side_effect=AssertionError("redundant grid allocation")), \
                 patch.object(current, "neg", side_effect=AssertionError("redundant negated interval")):
                self.assertEqual(getattr(current, operation)(first, last), expected)
            self.assertLess(current_work.operations, old_work.operations)

    def test_non_grid_results_still_use_the_original_outward_rounding(self):
        for first, last in ((point(F(1, 3)), point(F(1, 7))),
                            (point(F(1, 1 << 40)), point(F(3, 1 << 40)))):
            for operation, previous in (("add", previous_add), ("sub", previous_sub)):
                current = _Arithmetic(work=Work(), bits=32)
                with self.subTest(operation=operation, first=first, last=last), \
                     patch.object(current, "grid", wraps=current.grid) as grid:
                    actual = getattr(current, operation)(first, last)
                    self.assertEqual(actual, previous(_Arithmetic(work=Work(), bits=32), first, last))
                    grid.assert_called_once()

    def test_avoided_grid_keeps_the_original_operand_and_shift_limits(self):
        for limit, first, last in ((64, point(1 << 60), point(1)),
                                   (64, point(F(1, 1 << 40)), point(F(1, 1 << 40))),
                                   (64, point(1 << 80), point(0))):
            for operation, previous in (("add", previous_add), ("sub", previous_sub)):
                for query in (lambda a: getattr(a, operation)(first, last),
                              lambda a: previous(a, first, last)):
                    current = _Arithmetic(work=Work(max_operand_bits=limit), bits=8)
                    with self.subTest(operation=operation, limit=limit, first=first), \
                         self.assertRaises(ReferenceError) as caught:
                        query(current)
                    self.assertEqual(caught.exception.code, "resource")

    def test_later_endpoint_callback_readmits_the_first_exact_result(self):
        work = Work(max_operand_bits=256)
        arithmetic = _Arithmetic(work=work, bits=8)
        original = arithmetic.exact
        def narrow(first, last, kind):
            if first == F(1 << 81):
                work.max_operand_bits = 64
            return original(first, last, kind)
        with patch.object(arithmetic, "exact", side_effect=narrow), self.assertRaises(ReferenceError):
            arithmetic.add(Interval(F(1 << 80), F(1 << 81)), point(1))

    def test_cancelled_exact_arithmetic_retains_the_callers_exception(self):
        marker = RuntimeError("cancel exact dyadic proof")
        for operation in ("add", "sub"):
            work = Work(check=lambda: (_ for _ in ()).throw(marker))
            with self.subTest(operation=operation), self.assertRaises(RuntimeError) as caught:
                getattr(_Arithmetic(work=work, bits=8), operation)(point(3), point(2))
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)


class IndependentSparsePlanarTests(unittest.TestCase):
    def test_exact_axis_offsets_match_the_complete_nonunit_hamilton_expansion(self):
        orientations = ((2, 0, 0, 1), (F(3, 7), 0, 0, F(-2, 11)),
                        (Interval(F(1), F(1) + F(1, 1 << 130)), 0, 0,
                         Interval(F(1, 2), F(1, 2) + F(1, 1 << 130))))
        for q in orientations:
            for v in ((1, 0, 0), (0, 1, 0), (F(-3, 7), 0, 0), (0, F(5, 11), 0)):
                work, old_work = Work(), Work()
                pose, old = _PoseArithmetic(_Arithmetic(work=work)), _PoseArithmetic(_Arithmetic(work=old_work))
                quaternion, old_quaternion = pose.vector(q), old.vector(q)
                with self.subTest(quaternion=q, vector=v):
                    self.assertEqual(pose.rotate(quaternion, v), full_planar_rotation(old, old_quaternion, v))
                    self.assertLess(work.operations, old_work.operations)

    def test_uncertain_zero_and_nonplanar_vectors_keep_the_complete_formula(self):
        for q, v in (((2, 0, 0, 1), (1, Interval(F(-1, 8), F(1, 8)), 0)),
                     ((2, 0, 0, 1), (1, 0, Interval(F(0), F(1, 8)))),
                     ((1, Interval(F(-1, 8), F(1, 8)), 0, 1), (1, 0, 0)),
                     ((2, 0, 0, 1), (0, 0, 1))):
            pose, old = _PoseArithmetic(_Arithmetic(work=Work())), _PoseArithmetic(_Arithmetic(work=Work()))
            with self.subTest(quaternion=q, vector=v):
                self.assertEqual(pose.rotate(pose.vector(q), v), full_planar_rotation(old, old.vector(q), v))

    def test_factor_reuse_and_eviction_keep_changed_offset_and_antipode_correct(self):
        work = Work()
        pose = _PoseArithmetic(_Arithmetic(work=work))
        quaternion = pose.vector((2, 0, 0, 1))
        first = pose.rotate(quaternion, (1, 0, 0))
        self.assertEqual(first, pose.vector((3, 4, 0)))
        self.assertEqual(pose.rotate(quaternion, (0, 1, 0)), pose.vector((-4, 3, 0)))
        self.assertEqual(pose.rotate(pose.vector((-2, 0, 0, -1)), (1, 0, 0)), first)
        self.assertNotEqual(pose.rotate(pose.vector((2, 0, 0, -1)), (1, 0, 0)), first)
        for index in range(MAX_CACHE + 1):
            pose.a.remember(("evict", index), index)
        self.assertEqual(pose.rotate(quaternion, (1, 0, 0)), first)
        self.assertLessEqual(len(pose.a.cache), MAX_CACHE)

    def test_factor_lookup_narrowing_cannot_hide_a_wide_source_operand(self):
        work = Work(max_operand_bits=256)
        pose = _PoseArithmetic(_Arithmetic(work=work, bits=8))
        quaternion = (point(F(1, 1 << 80)), point(0), point(0), point(0))
        original = pose.a.lookup
        def narrow(key):
            if key[3] == "scalar_z_rotation_factors":
                work.max_operand_bits = 64
            return original(key)
        with patch.object(pose.a, "lookup", side_effect=narrow), self.assertRaises(ReferenceError) as caught:
            pose.rotate(quaternion, (1, 0, 0))
        self.assertEqual(caught.exception.code, "resource")

    def test_cancelled_warm_rotation_does_not_publish_or_reorder_results(self):
        work = Work()
        pose = _PoseArithmetic(_Arithmetic(work=work))
        quaternion = pose.vector((2, 0, 0, 1))
        pose.rotate(quaternion, (1, 0, 0))
        before = tuple(pose.a.cache.items())
        marker = RuntimeError("cancel independent sparse rotation")
        work.external_check = lambda: (_ for _ in ()).throw(marker)
        with self.assertRaises(RuntimeError) as caught:
            pose.rotate(quaternion, (1, 0, 0))
        self.assertIs(caught.exception, marker)
        self.assertEqual(tuple(pose.a.cache.items()), before)

    def test_actual_source_histories_samples_and_recording_enclosures_are_exact(self):
        for case, end, time in (("P07", F(3), F(1, 4)), ("L02", F(2), F(3, 2))):
            results, operations = [], []
            for previous in (False, True):
                with ExitStack() as stack:
                    if previous:
                        stack.enter_context(patch.object(_Arithmetic, "add", previous_add))
                        stack.enter_context(patch.object(_Arithmetic, "sub", previous_sub))
                        stack.enter_context(patch.object(_PoseArithmetic, "rotate", full_planar_rotation))
                    compiler = compile_construction(source_case(case))
                    reference = build_reference(compiler.model, end=end, work=compiler.reach_work)
                    carriers = tuple(path + ".frame" for path in reference.model.objects)
                    results.append((reference.boundary_states(),
                                    reference.recording_pose_enclosures(carriers, time), reference.sample(time)))
                    operations.append(compiler.budget.operations)
            with self.subTest(case=case):
                self.assertEqual(results[0], results[1])
                self.assertLess(operations[0], operations[1])


class IndependentReaderMissDomainTests(unittest.TestCase):
    def test_equal_wide_endpoints_are_readmitted_after_a_narrowing_lookup(self):
        for warm, promotion in ((False, False), (True, False), (True, True)):
            work = Work(max_operand_bits=256)
            arithmetic = _Bounds(work)
            vector = (point(1 << 80, _Cell), point(0, _Cell), point(0, _Cell))
            if warm:
                self.assertEqual(arithmetic.difference(vector, vector), F(0))
            original = work.charge
            def narrow(kind="checkpoint", amount=1):
                if kind == ("cache_promote" if promotion else "cache_lookup"):
                    work.max_operand_bits = 64
                return original(kind, amount)
            with self.subTest(warm=warm, promotion=promotion):
                with patch.object(work, "charge", side_effect=narrow), \
                     self.assertRaises(ReachAdmissionError) as caught:
                    arithmetic.difference(vector, vector)
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                self.assertEqual(caught.exception.details["limit"], 64)
                self.assertEqual(work.counts["independent_cache_miss_domain"], 1)

    def test_changed_domain_rechecks_interval_comparison_extents_too(self):
        work = Work(max_operand_bits=256)
        arithmetic = _Bounds(work)
        value = point(F(1 << 30, (1 << 40) - 1), _Cell)
        original = work.lookup
        def narrow(key):
            work.max_operand_bits = 64
            return original(key)
        with patch.object(work, "lookup", side_effect=narrow), self.assertRaises(ReachAdmissionError):
            arithmetic.difference((value,) * 3, (value,) * 3)

    def test_valid_changed_domain_proves_again_and_never_borrows_a_wide_key(self):
        work = Work(max_operand_bits=256)
        arithmetic = _Bounds(work)
        vector = (point(2, _Cell), point(0, _Cell), point(0, _Cell))
        original = work.lookup
        def narrow(key):
            work.max_operand_bits = 64
            return original(key)
        with patch.object(work, "lookup", side_effect=narrow):
            self.assertEqual(arithmetic.difference(vector, vector), F(0))
        self.assertEqual(work.counts["independent_cache_miss_domain"], 1)
        before = work.operations
        self.assertEqual(arithmetic.difference(vector, vector), F(0))
        self.assertGreater(work.operations, before)
        self.assertTrue(any(key[1] == 64 for key in work._cache))

    def test_miss_domain_cancellation_preserves_exception_and_does_not_cache(self):
        work = Work(max_operand_bits=256)
        arithmetic = _Bounds(work)
        vector = (point(2, _Cell), point(0, _Cell), point(0, _Cell))
        marker = RuntimeError("cancel miss-domain readmission")
        original = work.charge
        def callback(kind="checkpoint", amount=1):
            if kind == "cache_lookup":
                work.max_operand_bits = 64
            if kind == "independent_cache_miss_domain":
                work.external_check = lambda: (_ for _ in ()).throw(marker)
            return original(kind, amount)
        with patch.object(work, "charge", side_effect=callback), self.assertRaises(RuntimeError) as caught:
            arithmetic.difference(vector, vector)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertFalse(work._cache)

    def test_exact_zero_norm_needs_no_radical_but_admits_every_component(self):
        work = Work(max_operand_bits=64)
        arithmetic = _Bounds(work)
        with patch.object(arithmetic, "root", side_effect=AssertionError("unneeded radical")):
            self.assertEqual(arithmetic.norm((F(0),) * 4), F(0))
        self.assertEqual(work.counts, {"independent_norm_domain": 1})
        with self.assertRaises(ReachAdmissionError):
            arithmetic.norm((F(0), F(0), F(1 << 80)))


if __name__ == "__main__":
    unittest.main()
