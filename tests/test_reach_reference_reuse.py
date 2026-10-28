"""Independent interval reuse retains exact meanings and shared work."""
from fractions import Fraction as F
from dataclasses import replace
import math
import unittest
from unittest.mock import patch

from ontokin.reach_reference import (
    Interval, MAX_CACHE, MAX_OPERAND_BITS, ZERO, ReachReference, ReferenceError, _Arithmetic, _PoseArithmetic, build_reference,
)
from ontokin.construction import compile_construction
from ontokin.model import ReachSourceLocation
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

    def test_fixed_constants_share_only_bounded_immutable_charged_results(self):
        zero, identity = self.p.vector(ZERO), self.p.identity()
        self.assertEqual(identity.position, self.p.vector((0, 0, 0)))
        self.assertEqual(identity.orientation, self.p.vector((1, 0, 0, 0)))
        self.assertEqual(identity.velocity, zero)
        self.assertEqual(identity.omega, zero)
        before = self.work.operations
        self.assertIs(self.p.vector(ZERO), zero)
        self.assertIs(self.p.identity(), identity)
        self.assertGreater(self.work.operations, before)
        for index in range(MAX_CACHE + 1):
            self.a.remember(("evict_fixed_constant", index), F(index))
        self.assertEqual(len(self.a.cache), MAX_CACHE)
        self.assertEqual(self.p.identity(), identity)
        self.assertEqual(self.p.vector(ZERO), zero)
        self.assertEqual(len(self.a.cache), MAX_CACHE)
        # A different tuple takes ordinary numeric admission, even if its
        # leading coordinates coincide with the fixed zero vector.
        with self.assertRaises(ReferenceError):
            self.p.vector((F(0), F(0), F(1 << MAX_OPERAND_BITS)))
        marker = RuntimeError("cancel fixed independent constant")
        self.work.cancel = marker
        for query in (lambda: self.p.vector(ZERO), self.p.identity):
            with self.assertRaises(RuntimeError) as caught:
                query()
            self.assertIs(caught.exception, marker)

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

    def test_zero_rate_composition_omits_derivatives_but_keeps_uncertain_rates(self):
        # q=(1,1,1,1)/2 maps (x,y,z) to (z,x,y), exactly.
        parent = self.p.make(position=(1, 2, 3), orientation=(F(1, 2),) * 4)
        local = self.p.make(position=(4, 5, 6))
        with patch.object(self.p, "cross", side_effect=AssertionError("zero derivative was recomputed")), \
             patch.object(self.p, "rotate", wraps=self.p.rotate) as rotate:
            value = self.p.compose(parent, local)
        self.assertEqual(rotate.call_count, 1)
        self.assertEqual(value.position, self.p.vector((7, 6, 8)))
        self.assertEqual(value.orientation, parent.orientation)
        self.assertEqual(value.velocity, self.p.vector((0, 0, 0)))
        self.assertEqual(value.omega, self.p.vector((0, 0, 0)))
        uncertain = self.p.make(omega=(Interval(F(-1), F(1)), 0, 0))
        moving = self.p.compose(parent, uncertain)
        self.assertTrue(all(component.contains(expected) for component, expected in zip(moving.omega, (0, 1, 0))))
        self.assertTrue(any(component.magnitude for component in moving.omega))
        marker = RuntimeError("cancel repeated zero-rate composition")
        self.work.cancel = marker
        with self.assertRaises(RuntimeError) as caught:
            self.p.compose(parent, local)
        self.assertIs(caught.exception, marker)

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

    def test_planar_rotation_factors_retain_exact_enclosures_for_distinct_vectors(self):
        for orientation in ((2, 0, 0, 1), (F(3, 7), 0, 0, F(2, 11)),
                (Interval(F(1), F(1) + F(1, 1 << 130)), 0, 0,
                 Interval(F(1, 2), F(1, 2) + F(1, 1 << 130)))):
            q = self.p.vector(orientation)
            self.p.rotate(q, (1, 2, 3))
            cold_work = Work()
            cold = _PoseArithmetic(_Arithmetic(work=cold_work))
            cold_q, vector = cold.vector(orientation), (F(4, 7), F(-3, 11), 5)
            before = cold_work.operations
            expected = cold.rotate(cold_q, vector)
            complete_cost = cold_work.operations - before
            before = self.work.operations
            actual = self.p.rotate(q, vector)
            reused_cost = self.work.operations - before
            with self.subTest(orientation=orientation):
                self.assertEqual(actual, expected)
                self.assertGreater(reused_cost, 0)
                self.assertLess(reused_cost, complete_cost)
        self.assertLessEqual(len(self.a.cache), MAX_CACHE)

    def test_planar_rotation_factor_reuse_keeps_changed_inputs_guards_and_eviction(self):
        q = self.p.vector((2, 0, 0, 1))
        expected = self.p.rotate(q, (3, 4, 5))
        changed = self.p.rotate(self.p.vector((2, 0, 0, -1)), (3, 4, 5))
        self.assertNotEqual(changed, expected)
        for index in range(MAX_CACHE + 1):
            self.a.remember(("evict_planar_factors", index), F(index))
        self.assertEqual(self.p.rotate(q, (3, 4, 5)), expected)
        self.assertLessEqual(len(self.a.cache), MAX_CACHE)
        huge = F(1 << MAX_OPERAND_BITS)
        invalid = (q[0], q[1], q[2], Interval(huge, huge))
        with self.assertRaises(ReferenceError):
            self.p.rotate(invalid, (3, 4, 5))
        marker = RuntimeError("cancel independent planar factor reuse")
        self.work.cancel = marker
        with self.assertRaises(RuntimeError) as caught:
            self.p.rotate(q, (4, 5, 6))
        self.assertIs(caught.exception, marker)

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
    def test_reused_bound_algebra_matches_uncached_lifecycle_and_dynamic_rates(self):
        original_lookup = _Arithmetic.lookup

        def without_bound_reuse(arithmetic, key):
            if key[0] in {"source_bound_constant", "source_bound_compose"}:
                arithmetic.tick()
                return None
            return original_lookup(arithmetic, key)

        def phases(name, end, carrier, queries):
            compiler = compile_construction(source_case(name))
            reference = build_reference(compiler.model, end=end, work=compiler.reach_work)
            results = [reference.point_phase(carrier, time, side) for time, side in queries]
            self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
            return results, compiler.reach_work.operations

        cases = (("P01", F(3), "rig.arm.forearm.tip.frame",
                  ((F(1), "after"), (F(2), "before"), (F(2), "after"))),
                 ("P16", F(5, 2), "payload.frame",
                  ((F(2), "before"), (F(2), "after"), (F(5, 2), "after"))))
        for case in cases:
            with self.subTest(case=case[0]):
                reused, used = phases(*case)
                with patch.object(_Arithmetic, "lookup", new=without_bound_reuse):
                    uncached, previously_used = phases(*case)
                self.assertEqual(reused, uncached)
                self.assertLess(used, previously_used)
                # The cache cannot turn a completed action or a released
                # force-driven root into its incoming moving-arm bound.
                if case[0] == "P01":
                    self.assertGreater(reused[1].angular_speed, reused[2].angular_speed)
                else:
                    self.assertNotEqual(reused[0].acceleration, reused[1].acceleration)

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

    def test_recording_batch_builds_one_graph_and_retains_individual_pose_meaning(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        selected = ["rig", "rig.arm.forearm.tip.frame", "world"]
        with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
            values = reference.recording_pose_enclosures(selected, F(1, 4))
        self.assertEqual(incoming.call_count, 1)
        self.assertEqual(set(values), {"rig.frame", "rig.arm.forearm.tip.frame", "world"})
        for carrier, pose in values.items():
            full = reference.pose_enclosure(carrier, F(1, 4))
            self.assertEqual(pose, reference.recording_pose_enclosure(carrier, F(1, 4)))
            self.assertEqual((pose.position, pose.orientation), (full.position, full.orientation))
            self.assertFalse(hasattr(pose, "velocity"))
            self.assertFalse(hasattr(pose, "omega"))
        state = reference._state_at(F(1, 4), "after")
        cached = reference._poses[(id(state), F(1, 4), True, True)][1]
        self.assertNotIn("rig.tool.frame", cached)
        values.clear()
        repeated = reference.recording_pose_enclosures(selected, F(1, 4))
        self.assertEqual(set(repeated), {"rig.frame", "rig.arm.forearm.tip.frame", "world"})

    def test_recording_batch_bounds_selection_and_preserves_callback_and_side_guards(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        for carriers, side in ((["missing"], "after"), ([None], "after"),
                               (["world"], "left"), ("world", "after"),
                               (["world"] * (2 + len(reference.model.objects) + len(reference.model.sites)), "after")):
            with self.subTest(carriers=carriers, side=side), self.assertRaises(ReferenceError):
                reference.recording_pose_enclosures(carriers, F(1, 4), side)
        self.assertEqual(reference.recording_pose_enclosures([], F(1, 4)), {})
        reference.recording_pose_enclosures(["world"], F(1, 4))
        marker = RuntimeError("cancel cached independent batch")
        with patch.object(reference.a, "check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reference.recording_pose_enclosures(["world"], F(1, 4))
        self.assertIs(caught.exception, marker)


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


class IndependentObservationReuseTests(unittest.TestCase):
    def test_complete_p24_observations_match_recomputation_and_keep_action_identity(self):
        def sample(recompute):
            compiler = compile_construction(source_case("P24"))
            reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
            if recompute:
                def coordinate(path, time, state, observations):
                    value, rate = reference._coordinate(path, time, state)
                    return value, rate, float(value), reference.a.round64(rate)
                reference._joint_observation = coordinate
                reference._world_target = lambda base, target: reference.p.compose(base, reference.p.make(target))
            before = compiler.reach_work.operations
            with patch.object(reference, "_coordinate", wraps=reference._coordinate) as coordinate:
                value = reference.sample(F(1, 4))
            return reference, value, compiler.reach_work.operations - before, coordinate.call_count

        reference, reused, used, coordinate_count = sample(False)
        _, original, recomputed, original_coordinate_count = sample(True)
        self.assertEqual(reused, original)
        self.assertLess(used, recomputed)
        self.assertLess(coordinate_count, original_coordinate_count)
        self.assertEqual(len(reused["reaches"]), 128)
        active = reused["reaches"]["reach"]["current"]["value"]
        pending = reused["reaches"]["pending_001"]["current"]["value"]
        sibling = reused["reaches"]["pending_002"]["current"]["value"]
        self.assertEqual(active["lifecycle"], "running")
        self.assertEqual(pending["lifecycle"], "pending")
        self.assertIsNone(pending["resolved_joint_targets_rad"])
        self.assertNotEqual(active["claimed_joint_ids"], pending["claimed_joint_ids"])
        self.assertEqual(active["joint_coordinates_rad"], pending["joint_coordinates_rad"])
        self.assertEqual(active["joint_rates_rad_per_s"], pending["joint_rates_rad_per_s"])
        pending["joint_coordinates_rad"][0] = 99
        pending["tip_pose_world"]["position_m"][0] = 99
        self.assertNotEqual(pending["joint_coordinates_rad"], sibling["joint_coordinates_rad"])
        repeated = reference.sample(F(1, 4))["reaches"]["pending_001"]["current"]["value"]
        self.assertEqual(repeated, original["reaches"]["pending_001"]["current"]["value"])
        incoming = reference.sample(F(0), "before")["reaches"]["reach"]["current"]["value"]
        self.assertEqual(incoming["lifecycle"], "pending")
        self.assertNotEqual(incoming["joint_coordinates_rad"], active["joint_coordinates_rad"])

    def test_observation_operands_remain_bounded_distinct_and_cancellable(self):
        compiler = compile_construction(source_case("P01"))
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        state = reference._state_at(F(1, 4), "after")
        action = reference.model.actions["reach"]
        observations = {("occupied", index): None for index in range(MAX_CACHE)}
        first = reference._joint_observation(action.reach.elbow, F(1, 4), state, observations)
        self.assertEqual(len(observations), MAX_CACHE)
        earlier = reference._joint_observation(action.reach.elbow, F(0),
            reference._state_at(F(0), "before"), {})
        self.assertNotEqual(first, earlier)
        base = reference.p.identity()
        target = reference._world_target(base, (1, 2, 3))
        self.assertIs(reference._world_target(base, (1, 2, 3)), target)
        self.assertNotEqual(reference._world_target(base, (1, 2, 4)).position, target.position)
        self.assertNotEqual(reference._world_target(reference.p.make((1, 0, 0)), (1, 2, 3)).position,
                            target.position)
        marker = RuntimeError("cancel reused independent observation")
        with patch.object(reference.a, "check", side_effect=marker):
            for query in (
                lambda: reference._world_target(base, (1, 2, 3)),
                lambda: reference._joint_observation(action.reach.elbow, F(1, 4), state,
                                                     {action.reach.elbow: first}),
            ):
                with self.assertRaises(RuntimeError) as caught:
                    query()
                self.assertIs(caught.exception, marker)


class IndependentDescriptionReuseTests(unittest.TestCase):
    def test_p24_locations_keep_all_action_identities_fresh_rows_and_complete_weight(self):
        from ontokin.reach_reference import _plain
        compiler = compile_construction(source_case("P24"))
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        original_weight = reference._reach_history_weight
        descriptions = {path: reference._description(path, {"own_action": path})
                        for path, action in reference.model.actions.items()
                        if action.kind == "reach_planar"}
        self.assertEqual(len(descriptions), 128)
        self.assertEqual(len({tuple(value["element_id"]) for value in descriptions.values()}), 128)
        for path, value in descriptions.items():
            payload = reference.model.actions[path].reach
            self.assertEqual(value["source_location"], _plain(payload.source_location, reference.a))
            self.assertEqual(value["current"]["value"], {"own_action": path})
        first = descriptions["reach"]["source_location"]
        sibling = descriptions["pending_001"]["source_location"]
        saved = dict(sibling)
        first["start_byte"] = -1
        self.assertEqual(sibling, saved)
        self.assertEqual(reference._description("pending_001", {})["source_location"], saved)
        with patch.object(reference, "_source_location", side_effect=lambda value: _plain(value, reference.a)):
            self.assertEqual(reference._maximum_reach_weight(), original_weight)

    def test_location_reuse_keeps_complete_keys_guards_fallbacks_cap_and_cancellation(self):
        reference = object.__new__(ReachReference)
        work = Work()
        reference.a = _Arithmetic(work=work)
        source = ReachSourceLocation("entry", "sha256:" + "1" * 64, 17, 29)
        expected = {"source_id": source.source_id, "source_revision": source.source_revision,
                    "start_byte": 17, "end_byte": 29}
        self.assertEqual(reference._source_location(source), expected)
        before = work.operations
        with patch("ontokin.reach_reference._plain", side_effect=AssertionError("repeated traversal")):
            self.assertEqual(reference._source_location(source), expected)
        self.assertGreater(work.operations, before)
        for name, value in (("source_id", "library"), ("source_revision", "sha256:" + "2" * 64),
                            ("start_byte", 18), ("end_byte", 30)):
            self.assertEqual(reference._source_location(replace(source, **{name: value})),
                             {**expected, name: value})
        with self.assertRaises(ReferenceError):
            reference._source_location(replace(source, start_byte=1 << MAX_OPERAND_BITS))
        # A frozen dataclass can still be given a mutable field by an invalid
        # direct caller. It must use the original fresh recursive conversion.
        mutable = replace(source, source_id=["entry"])
        first = reference._source_location(mutable)
        mutable.source_id.append("changed")
        self.assertEqual(first["source_id"], ["entry"])
        self.assertEqual(reference._source_location(mutable)["source_id"], ["entry", "changed"])
        with self.assertRaises(ReferenceError):
            reference._source_location(object())
        for index in range(MAX_CACHE + 1):
            reference.a.remember(("evict_location", index), index)
        self.assertEqual(reference._source_location(source), expected)
        self.assertEqual(len(reference.a.cache), MAX_CACHE)
        marker = RuntimeError("cancel immutable source projection")
        work.cancel = marker
        with self.assertRaises(RuntimeError) as caught:
            reference._source_location(source)
        self.assertIs(caught.exception, marker)


class IndependentObservationModeTests(unittest.TestCase):
    def test_unrequested_projection_work_is_deferred_with_original_guards_on_demand(self):
        compiler = compile_construction(source_case("P01"))
        projection_error = ReferenceError("resource", "complete reach projection guard")
        geometry_error = ReferenceError("unsupported", "captured geometry projection guard")
        with patch.object(ReachReference, "_maximum_reach_weight", side_effect=projection_error), \
             patch.object(ReachReference, "_capture_geometry", side_effect=geometry_error):
            reference = build_reference(compiler.model, end=F(1, 4), mode="observation", work=compiler.reach_work)
            pose = reference.pose_enclosure("rig.arm.forearm.tip.frame", F(1, 4))
            phase = reference.point_phase("rig.arm.forearm.tip.frame", F(1, 4))
            self.assertTrue(any(value.magnitude for value in pose.velocity))
            self.assertGreater(phase.source_numeric_velocity_error, 0)
            with self.assertRaises(ReferenceError) as caught:
                reference.sample(F(1, 4))
            self.assertIs(caught.exception, projection_error)
            with self.assertRaises(ReferenceError) as caught:
                reference.geometry_expectations
            self.assertIs(caught.exception, geometry_error)
            self.assertIsNone(reference._reach_history_weight)
            self.assertIsNone(reference._geometry)
        reference.sample(F(1, 4))
        self.assertIsNotNone(reference._reach_history_weight)
        returned = reference.geometry_expectations
        returned[0]["geometry"].clear()
        self.assertTrue(reference.geometry_expectations[0]["geometry"])

    def test_p24_single_observation_does_not_claim_complete_recording_capacity(self):
        compiler = compile_construction(source_case("P24"))
        with self.assertRaises(ReferenceError) as caught:
            build_reference(compiler.model, end=F(3), work=compiler.reach_work)
        self.assertEqual(caught.exception.code, "resource")
        self.assertEqual(caught.exception.details["budget"], "boundary_state_records")
        self.assertGreater(caught.exception.details["consumed"], 100000)
        compiler = compile_construction(source_case("P24"))
        reference = build_reference(compiler.model, end=F(3), mode="observation", work=compiler.reach_work)
        self.assertEqual(reference.mode, "observation")
        self.assertEqual(reference.boundaries, (F(0), F(2), F(3)))
        sample = reference.sample(F(3))
        self.assertEqual(len(sample["reaches"]), 128)
        self.assertEqual(sample["reaches"]["reach"]["current"]["value"]["lifecycle"], "completed")
        self.assertEqual(sample["reaches"]["pending_127"]["current"]["value"]["lifecycle"], "pending")
        self.assertEqual(len(reference._after), 3)
        with self.assertRaises(ReferenceError) as caught:
            reference.boundary_states()
        self.assertEqual(caught.exception.code, "unsupported")
        self.assertLessEqual(compiler.budget.operations, 100000)

    def test_observation_and_recording_modes_preserve_full_release_and_force_equations(self):
        results = []
        for mode in ("recording", "observation"):
            compiler = compile_construction(source_case("P16"))
            reference = build_reference(compiler.model, end=F(3), mode=mode, work=compiler.reach_work)
            results.append([(reference.pose_enclosure("payload.frame", time, side),
                             reference.point_phase("payload.frame", time, side))
                            for time, side in ((F(2), "before"), (F(2), "after"), (F(3), "after"))])
        self.assertEqual(results[0], results[1])
        self.assertNotEqual(results[1][0], results[1][-1])

    def test_observation_mode_keeps_incoming_failures_state_cap_and_mode_admission(self):
        compiler = compile_construction(source_case("L04"))
        reference = build_reference(compiler.model, end=F(1, 2), end_side="before",
                                    mode="observation", work=compiler.reach_work)
        self.assertTrue(reference.sample(F(1, 2), "before")["reaches"])
        for query in (
            lambda: reference.sample(F(1, 2), "after"),
            lambda: reference.recording_pose_enclosures(["world"], F(1, 2), "after"),
            reference.boundary_states,
        ):
            with self.assertRaises(ReferenceError) as caught:
                query()
            self.assertEqual(caught.exception.code, "unsupported")
        self.assertIsNone(reference._after[-1])
        compiler = compile_construction(source_case("L04"))
        with self.assertRaises(ReferenceError) as caught:
            build_reference(compiler.model, end=F(1, 2), mode="observation", work=compiler.reach_work)
        self.assertEqual(caught.exception.code, "source_admission")
        compiler = compile_construction(source_case("P01"))
        with patch("ontokin.reach_reference.MAX_BOUNDARIES", 1):
            with self.assertRaises(ReferenceError) as caught:
                build_reference(compiler.model, end=F(1, 4), mode="observation", work=compiler.reach_work)
        self.assertEqual(caught.exception.code, "resource")
        self.assertIn("boundary cap", str(caught.exception))
        for mode in (None, "", "observations", True):
            compiler = compile_construction(source_case("P01"))
            with self.subTest(mode=mode), self.assertRaises(ReferenceError) as caught:
                build_reference(compiler.model, end=F(0), mode=mode, work=compiler.reach_work)
            self.assertEqual(caught.exception.code, "unsupported")


if __name__ == "__main__":
    unittest.main()
