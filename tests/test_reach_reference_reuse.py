"""Independent interval reuse retains exact meanings and shared work."""
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin.reach_reference import (
    Interval, MAX_CACHE, MAX_OPERAND_BITS, ReachReference, ReferenceError, _Arithmetic, _PoseArithmetic, build_reference,
)
from ontokin.construction import compile_construction
from reach_agent_support import source_case


class Work:
    def __init__(self):
        self.operations = 0
        self.cancel = None

    def tick(self):
        self.operations += 1
        if self.cancel is not None:
            raise self.cancel
        if self.operations > 100000:
            raise RuntimeError("shared work exhausted")


class IndependentPoseReuseTests(unittest.TestCase):
    def setUp(self):
        self.work = Work()
        self.a = _Arithmetic(work=self.work)
        self.p = _PoseArithmetic(self.a)

    def test_zero_vectors_and_scalar_quaternions_preserve_exact_answers(self):
        zero = self.p.vector((0, 0, 0))
        vector = self.p.vector((F(3, 7), -2, 5))
        self.assertEqual(self.p.cross(zero, vector), zero)
        self.assertEqual(self.p.add(zero, vector), vector)
        self.assertEqual(self.p.scale(vector, 0), zero)
        self.assertEqual(self.p.scale(vector, 1), vector)
        for scale, expected in ((7, 1), (-7, -1)):
            q = self.p.quaternion((scale, 0, 0, 0))
            self.assertEqual(q, self.p.vector((expected, 0, 0, 0)))
            self.assertEqual(self.p.rotate(q, vector), vector)
        with self.assertRaises(ReferenceError):
            self.p.quaternion((0, 0, 0, 0))

    def test_cached_composition_charges_and_preserves_callback_identity(self):
        parent = self.p.make(position=(1, 2, 3), omega=(0, 0, 2))
        local = self.p.make(position=(3, 0, 0))
        result = self.p.compose(parent, local)
        self.assertEqual(result.position, self.p.vector((4, 2, 3)))
        self.assertEqual(result.velocity, self.p.vector((0, 6, 0)))
        before = self.work.operations
        self.assertIs(self.p.compose(parent, local), result)
        self.assertGreater(self.work.operations, before)
        interruption = RuntimeError("cancel cached independent composition")
        self.work.cancel = interruption
        with self.assertRaises(RuntimeError) as caught:
            self.p.compose(parent, local)
        self.assertIs(caught.exception, interruption)

    def test_equal_poses_share_pure_results_but_changed_rates_do_not(self):
        parent = self.p.make(omega=(0, 0, 2))
        local = self.p.make(position=(3, 0, 0))
        result = self.p.compose(parent, local)
        self.assertIs(self.p.compose(self.p.make(omega=(0, 0, 2)), local), result)
        changed = self.p.compose(self.p.make(omega=(0, 0, -2)), local)
        self.assertEqual(changed.position, result.position)
        self.assertEqual(changed.velocity, self.p.vector((0, -6, 0)))
        self.assertNotEqual(changed.omega, result.omega)

    def test_cached_hinge_retains_rate_convention_and_charges_every_lookup(self):
        axis = (F(3, 5), F(4, 5), F(0))
        first = self.p.hinge(axis, F(1, 4), F(2))
        before = self.work.operations
        self.assertIs(self.p.hinge(axis, F(1, 4), F(2)), first)
        self.assertGreater(self.work.operations, before)
        changed = self.p.hinge(axis, F(1, 4), F(-2))
        self.assertEqual(changed.orientation, first.orientation)
        self.assertNotEqual(changed.omega, first.omega)
        nonunit = (F(3), F(4), F(0))
        actual = self.p.hinge(nonunit, F(1, 4), F(2))
        ideal = self.p.hinge(nonunit, F(1, 4), F(2), ideal=True)
        self.assertNotEqual(actual.omega, ideal.omega)
        marker = RuntimeError("cancel cached independent hinge")
        self.work.cancel = marker
        with self.assertRaises(RuntimeError) as caught:
            self.p.hinge(axis, F(1, 4), F(2))
        self.assertIs(caught.exception, marker)

    def test_planar_hamilton_algebra_retains_nonunit_meaning_and_interval_uncertainty(self):
        first, second = self.p.vector((2, 0, 0, 1)), self.p.vector((3, 0, 0, -4))
        self.assertEqual(self.p.multiply(first, second), self.p.vector((10, 0, 0, -5)))
        vector = self.p.vector((3, 4, 5))
        self.assertEqual(self.p.rotate(first, vector), self.p.vector((-7, 24, 25)))
        self.assertEqual(self.p.rotate(tuple(self.a.neg(value) for value in first), vector),
                         self.p.vector((-7, 24, 25)))
        # A component interval containing zero is not a zero operand. This
        # quaternion family includes q=(1,1,0,0), which maps (0,1,0) to (0,0,2)
        # under the same raw Hamilton product, not the unit-q identity result.
        uncertain = (self.a.point(1), Interval(F(-1), F(1)), self.a.point(0), self.a.point(0))
        rotated = self.p.rotate(uncertain, (0, 1, 0))
        self.assertTrue(all(value.contains(expected) for value, expected in zip(rotated, (0, 0, 2))))
        self.assertFalse(all(value.lo == value.hi for value in rotated))

    def test_saturated_cache_recomputes_pi_without_allocating_extra_capacity(self):
        expected = self.a.pi()
        for index in range(MAX_CACHE + 1):
            self.a.remember(("test", index), Interval(F(index), F(index)))
        self.assertEqual(len(self.a.cache), MAX_CACHE)
        self.assertEqual(self.a.pi(), expected)
        self.assertEqual(len(self.a.cache), MAX_CACHE)

    def test_sparse_exact_folds_preserve_guards_and_cancellation(self):
        self.assertEqual(self.a.exact_sum(0, F(3, 7), 0, F(-3, 7), 2), F(2))
        self.assertEqual(self.a.exact_product(1, F(3, 7), 1, F(7, 3), -2), F(-2))
        self.assertEqual(self.a.exact_sum(), F(0))
        self.assertEqual(self.a.exact_product(), F(1))
        # An early zero never hides an invalid later operand. Nontrivial
        # products still reject oversized prospective cross-products.
        with self.assertRaises(ReferenceError):
            self.a.exact_product(0, F(1 << MAX_OPERAND_BITS))
        with self.assertRaises(ReferenceError):
            self.a.exact_product(F(1 << 20000), F(1 << 20000))
        marker = RuntimeError("cancel exact zero/one fold")
        self.work.cancel = marker
        for method, values in ((self.a.exact_sum, (0, 0)), (self.a.exact_product, (1, 1))):
            with self.assertRaises(RuntimeError) as caught:
                method(*values)
            self.assertIs(caught.exception, marker)


class IndependentTaylorTailTests(unittest.TestCase):
    def test_adaptive_midpoint_tails_enclose_direct_factorial_series(self):
        def independent_series(value, offset):
            # Direct powers/factorials provide a separate finite Taylor sum;
            # the next absolute term encloses its alternating remainder.
            count = 60
            total = sum(((-1) ** index * value ** (2 * index + offset)
                         / math.factorial(2 * index + offset) for index in range(count)), F(0))
            tail = abs(value) ** (2 * count + offset) / math.factorial(2 * count + offset)
            return total - tail, total + tail

        for precision in (128, 256):
            for interval in (Interval(F(-1), F(-1)), Interval(F(-1, 64), F(1, 32)),
                             Interval(F(0), F(0)), Interval(F(1, 1024), F(1, 1024)),
                             Interval(F(1), F(1))):
                with self.subTest(precision=precision, interval=interval):
                    arithmetic = _Arithmetic(work=Work(), bits=precision)
                    sine, cosine = arithmetic._series_sincos(interval)
                    for point in (interval.lo, (interval.lo + interval.hi) / 2, interval.hi):
                        for enclosed, offset in ((sine, 1), (cosine, 0)):
                            low, high = independent_series(point, offset)
                            self.assertLessEqual(enclosed.lo, low)
                            self.assertGreaterEqual(enclosed.hi, high)
        counts = []
        for point in (F(1, 1024), F(1)):
            work = Work()
            _Arithmetic(work=work)._series_sincos(point)
            counts.append(work.operations)
        self.assertGreater(counts[0], 0)
        self.assertLess(counts[0], counts[1])


class IndependentRecordingPoseTests(unittest.TestCase):
    def test_sparse_basis_matches_complete_exact_folds_for_moving_and_dynamic_carriers(self):
        def old_sum(arithmetic, *values):
            result = F(0)
            for value in values:
                result = arithmetic.exact(result, value, "add")
            return result

        def old_product(arithmetic, *values):
            result = F(1)
            for value in values:
                result = arithmetic.exact(result, value, "mul")
            return result

        def phase(name, time, carrier):
            compiler = compile_construction(source_case(name))
            reference = build_reference(compiler.model, end=time, work=compiler.reach_work)
            result = reference.point_phase(carrier, time)
            return result, compiler.reach_work.operations

        for name, time, carrier in (("P01", F(1), "rig.arm.forearm.tip.frame"),
                                    ("P16", F(5, 2), "payload.frame")):
            with self.subTest(case=name):
                optimized, used = phase(name, time, carrier)
                with patch.object(_Arithmetic, "exact_sum", new=old_sum), \
                     patch.object(_Arithmetic, "exact_product", new=old_product):
                    original, previously_used = phase(name, time, carrier)
                self.assertEqual(optimized, original)
                self.assertLess(used, previously_used)

    def test_full_pose_selection_resolves_only_requested_ancestry(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        world = reference.pose_enclosure("world", F(1, 4))
        state = reference._state_at(F(1, 4), "after")
        cached = reference._poses[(id(state), F(1, 4), True, False)][1]
        self.assertEqual(set(cached), {"world"})
        tip = reference.pose_enclosure("rig.arm.forearm.tip.frame", F(1, 4))
        self.assertTrue(any(component.magnitude for component in tip.velocity))
        self.assertIs(reference.pose_enclosure("world", F(1, 4)), world)
        full = reference._pose_map(F(1, 4), state, ideal=True)
        self.assertEqual(tip, full["rig.arm.forearm.tip.frame"])
        self.assertEqual(set(full), {"world", *(path + ".frame" for path in
            (*compiler.model.objects, *compiler.model.sites))})

    def test_recording_poses_preserve_full_enclosures_without_exposing_rates(self):
        for name, time, carrier in (("P01", F(1, 4), "rig.arm.forearm.tip.frame"),
                                    ("P16", F(5, 2), "payload.frame")):
            compiler = compile_construction(source_case(name))
            reference = build_reference(compiler.model, end=time, work=compiler.reach_work)
            for side in ("before", "after"):
                selected = reference.recording_pose_enclosure(carrier, time, side)
                self.assertFalse(hasattr(selected, "velocity"))
                self.assertFalse(hasattr(selected, "omega"))
                full = reference.pose_enclosure(carrier, time, side)
                self.assertEqual(selected.position, full.position)
                self.assertEqual(selected.orientation, full.orientation)
                self.assertTrue(any(value.magnitude for value in (*full.velocity, *full.omega)))
                # Full observations and point bounds still use the complete
                # derivative path after a pose-only cache entry exists.
                snapshot = reference.sample(time, side)
                self.assertIn("velocity_m_per_s", snapshot["objects"][carrier.split(".")[0]])

    def test_recording_selection_does_not_admit_unknown_carriers_or_sides(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        for carrier, side in (("missing.frame", "after"), ("world", "left")):
            with self.subTest(carrier=carrier, side=side), self.assertRaises(ReferenceError):
                reference.recording_pose_enclosure(carrier, F(1, 4), side)


class IndependentIncomingPrefixTests(unittest.TestCase):
    def test_incoming_state_reuse_does_not_mutate_previous_action_history(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(3), work=compiler.reach_work)
        self.assertIs(reference._before[1], reference._after[0])
        self.assertIsNot(reference._after[1], reference._before[1])
        running = reference.sample(F(2), "before")["reaches"]["reach"]["current"]["value"]
        completed = reference.sample(F(2), "after")["reaches"]["reach"]["current"]["value"]
        self.assertEqual(running["lifecycle"], "running")
        self.assertEqual(completed["lifecycle"], "completed")
        self.assertIsNone(running["terminal_result"])
        self.assertIsNotNone(completed["terminal_result"])
        # Mutating a returned projection cannot mutate either shared private
        # state or later independently returned records.
        running["lifecycle"] = "changed"
        repeated = reference.sample(F(2), "before")["reaches"]["reach"]["current"]["value"]
        self.assertEqual(repeated["lifecycle"], "running")

    def test_failed_final_transaction_is_never_staged_or_observed(self):
        for name, end in (("P17", F(3)), ("L04", F(1, 2))):
            compiler = compile_construction(source_case(name))
            original = ReachReference._event
            def reject_final(reference, event, index, time, *args):
                if time == end:
                    raise AssertionError("unrequested final transaction executed")
                return original(reference, event, index, time, *args)
            with patch.object(ReachReference, "_event", new=reject_final):
                reference = build_reference(compiler.model, end=end,
                    end_side="before", work=compiler.reach_work)
            incoming = reference.sample(end, "before")
            self.assertEqual(incoming["side"], "before")
            self.assertTrue(incoming["reaches"])
            queries = (
                lambda: reference.sample(end, "after"),
                lambda: reference.pose_enclosure("world", end, "after"),
                lambda: reference.recording_pose_enclosure("world", end, "after"),
                lambda: reference.point_phase("world", end, "after"),
                reference.boundary_states,
            )
            for query in queries:
                with self.assertRaises(ReferenceError) as caught:
                    query()
                self.assertEqual(caught.exception.code, "unsupported")
            # A later hidden query has not evaluated or populated the sentinel.
            self.assertIsNone(reference._after[-1])

    def test_default_after_still_requires_final_admission_and_side_is_validated(self):
        compiler = compile_construction(source_case("L04"))
        with self.assertRaises(ReferenceError) as caught:
            build_reference(compiler.model, end=F(1, 2), work=compiler.reach_work)
        self.assertEqual(caught.exception.code, "source_admission")
        for side in ("left", None, ""):
            compiler = compile_construction(source_case("P01"))
            with self.subTest(side=side), self.assertRaises(ReferenceError):
                build_reference(compiler.model, end=F(0), end_side=side, work=compiler.reach_work)


if __name__ == "__main__":
    unittest.main()
