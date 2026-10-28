"""Complete phase roots reuse exact work without borrowing source authority."""
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_reference import Interval, MAX_CACHE, ReachReference, ReferenceError
from test_reach_reference_world_recording import point, reference_case


def root_entries(reference):
    return {key: value for key, value in reference.a.cache.items()
            if key[:1] == ("source_phase_root_pair",)}


def root_state(reference, time=F(1, 4), *, dynamic=False):
    state = reference._state_at(time, "after")
    roots = {reference._ancestry(path + ".frame", state)[0] for path in reference.model.objects}
    return next(path for path in sorted(roots - {None})
                if (state.modes[path] == "dynamic") == dynamic), state


def original_pair(reference, path, time, state):
    return (reference._root_pose(path, time, state, ideal=False),
            reference._root_pose(path, time, state, ideal=True))


class IndependentPhaseRootTests(unittest.TestCase):
    def test_full_root_fields_equal_the_original_two_equations(self):
        for case, end, time, dynamic in (("P01", F(1), F(1, 4), False),
                ("P05", F(1), F(1, 4), False), ("P16", F(4), F(7, 2), True),
                ("L03", F(3), F(9, 4), False)):
            with self.subTest(case=case):
                reference, _ = reference_case(case, end)
                path, state = root_state(reference, time, dynamic=dynamic)
                expected = original_pair(reference, path, time, state)
                prior_roots = set(root_entries(reference))
                actual = reference._phase_root_poses(path, time, state)
                self.assertEqual(actual, expected)
                first = reference.a.work.operations
                with patch.object(reference, "_root_pose", side_effect=AssertionError("repeated root")):
                    self.assertEqual(reference._phase_root_poses(path, time, state), expected)
                self.assertLessEqual(reference.a.work.operations - first, 3)
                # Constructing a released dynamic source can already prove
                # earlier roots. This call adds its own complete pair.
                self.assertEqual(len(set(root_entries(reference)) - prior_roots), 1)

    def test_complete_phase_fields_match_original_root_and_distance_paths(self):
        for case in ("P01", "P05", "P16", "L03"):
            with self.subTest(case=case):
                reference, _ = reference_case(case, F(1, 2))
                original, _ = reference_case(case, F(1, 2))
                carriers = tuple(path + ".frame" for path in reference.model.objects)
                with patch.object(original, "_phase_root_poses",
                        side_effect=lambda path, time, state: original_pair(original, path, time, state)), \
                        patch.object(original, "_phase_root_distance", side_effect=original._distance):
                    expected = tuple(original.phases(path, F(0), F(1, 2)) for path in carriers)
                actual = tuple(reference.phases(path, F(0), F(1, 2)) for path in carriers)
                self.assertEqual(actual, expected)
                self.assertLess(reference.a.work.operations, original.a.work.operations)

    def test_actual_and_ideal_roots_with_different_inputs_are_never_coalesced(self):
        reference, _ = reference_case("P01", F(1, 2))
        path, state = root_state(reference)
        position = state.ideal_positions[path]
        state.ideal_positions[path] = (point(F(1, 8)), *position[1:])
        expected = original_pair(reference, path, F(1, 4), state)
        actual = reference._phase_root_poses(path, F(1, 4), state)
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual[0].position, actual[1].position)
        self.assertIsNot(actual[0], actual[1])

    def test_each_new_clock_and_source_operand_has_its_own_complete_value(self):
        reference, _ = reference_case("P05", F(1, 2))
        path, state = root_state(reference)
        for time in (F(1, 8), F(1, 4)):
            self.assertEqual(reference._phase_root_poses(path, time, state),
                             original_pair(reference, path, time, state))
        move = state.claims[(path, "translation")]
        action = reference.model.actions[move]
        reference.model.actions[move] = replace(action, vector=(F(3, 4), F(0), F(0)))
        self.assertEqual(reference._phase_root_poses(path, F(1, 4), state),
                         original_pair(reference, path, F(1, 4), state))
        self.assertEqual(len(root_entries(reference)), 3)

    def test_dynamic_force_and_anchor_changes_do_not_reuse_a_previous_root(self):
        reference, _ = reference_case("P16", F(4))
        path, state = root_state(reference, F(7, 2), dynamic=True)
        prior_roots = set(root_entries(reference))
        reference._phase_root_poses(path, F(7, 2), state)
        force = state.forces[path]
        force.acceleration = (F(1), F(2), F(3))
        expected = original_pair(reference, path, F(7, 2), state)
        actual = reference._phase_root_poses(path, F(7, 2), state)
        self.assertEqual(actual, expected)
        self.assertEqual(len(set(root_entries(reference)) - prior_roots), 2)

    def test_current_source_is_rechecked_after_a_warm_lookup(self):
        for field in ("position", "claim"):
            reference, _ = reference_case("P05", F(1, 2))
            path, state = root_state(reference)
            reference._phase_root_poses(path, F(1, 4), state)
            old = root_entries(reference)
            lookup = reference.a.lookup
            def changed(key):
                result = lookup(key)
                if key[:1] == ("source_phase_root_pair",):
                    if field == "position":
                        state.positions[path] = (point(9), point(0), point(0))
                    else:
                        state.claims.pop((path, "translation"))
                return result
            with self.subTest(field=field), patch.object(reference.a, "lookup", side_effect=changed), \
                    self.assertRaises(ReferenceError) as caught:
                reference._phase_root_poses(path, F(1, 4), state)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(root_entries(reference), old)

    def test_changed_source_at_publication_does_not_publish_a_pair(self):
        reference, _ = reference_case("P05", F(1, 2))
        path, state = root_state(reference)
        remember = reference.a.remember
        def changed(key, value, **kwargs):
            if key[:1] != ("source_phase_root_pair",):
                return remember(key, value, **kwargs)
            def mutate():
                state.positions[path] = (point(9), point(0), point(0))
            with patch.object(reference.a.work, "external_check", side_effect=mutate):
                return remember(key, value, **kwargs)
        with patch.object(reference.a, "remember", side_effect=changed), \
                self.assertRaises(ReferenceError) as caught:
            reference._phase_root_poses(path, F(1, 4), state)
        self.assertEqual(caught.exception.code, "identity")
        self.assertFalse(root_entries(reference))

    def test_transient_source_cell_mutation_cannot_change_captured_arithmetic(self):
        reference, _ = reference_case("P05", F(1, 2))
        path, state = root_state(reference)
        expected = original_pair(reference, path, F(1, 4), state)
        active = state.actions[state.claims[(path, "translation")]]
        cell = active.initial[0]
        saved = cell.lo, cell.hi
        scale, entered = reference.p.scale, False
        def transient(vector, scalar):
            nonlocal entered
            if entered:
                return scale(vector, scalar)
            entered = True
            calls = 0
            def check():
                nonlocal calls
                calls += 1
                value = F(9) if calls == 1 else saved[0]
                object.__setattr__(cell, "lo", value)
                object.__setattr__(cell, "hi", value if calls == 1 else saved[1])
            try:
                with patch.object(reference.a.work, "external_check", side_effect=check):
                    return scale(vector, scalar)
            finally:
                object.__setattr__(cell, "lo", saved[0])
                object.__setattr__(cell, "hi", saved[1])
        with patch.object(reference.p, "scale", side_effect=transient):
            actual = reference._phase_root_poses(path, F(1, 4), state)
        self.assertTrue(entered)
        self.assertEqual(actual, expected)
        self.assertEqual(next(iter(root_entries(reference).values())), expected)

    def test_cancellation_keeps_the_original_exception_and_publishes_no_pair(self):
        for stage in ("capture", "publication"):
            reference, _ = reference_case("P05", F(1, 2))
            path, state = root_state(reference)
            marker = RuntimeError("cancel independent phase root")
            remember = reference.a.remember
            def cancelled(key, value, **kwargs):
                if key[:1] == ("source_phase_root_pair",):
                    with patch.object(reference.a.work, "external_check", side_effect=marker):
                        return remember(key, value, **kwargs)
                return remember(key, value, **kwargs)
            with self.subTest(stage=stage), self.assertRaises(RuntimeError) as caught:
                if stage == "capture":
                    with patch.object(reference.a.work, "external_check", side_effect=marker):
                        reference._phase_root_poses(path, F(1, 4), state)
                else:
                    with patch.object(reference.a, "remember", side_effect=cancelled):
                        reference._phase_root_poses(path, F(1, 4), state)
            self.assertIs(caught.exception, marker)
            self.assertIs(reference.a.work.callback_error, marker)
            self.assertFalse(root_entries(reference))

    def test_reentrant_lookup_retains_only_completed_exact_pairs(self):
        reference, _ = reference_case("P05", F(1, 2))
        path, state = root_state(reference)
        expected = original_pair(reference, path, F(1, 4), state)
        lookup, entered = reference.a.lookup, False
        nested = []
        def reenter(key):
            nonlocal entered
            if key[:1] == ("source_phase_root_pair",) and not entered:
                entered = True
                nested.append(reference._phase_root_poses(path, F(1, 8), state))
            return lookup(key)
        with patch.object(reference.a, "lookup", side_effect=reenter):
            self.assertEqual(reference._phase_root_poses(path, F(1, 4), state), expected)
        self.assertEqual(nested, [original_pair(reference, path, F(1, 8), state)])
        self.assertEqual(len(root_entries(reference)), 2)

    def test_other_domains_keep_the_original_pair_calculations(self):
        for bits, cap, time in ((256, 32768, F(1, 4)), (128, 32767, F(1, 4)),
                               (128, 32768, .25)):
            reference, _ = reference_case("P05", F(1, 2), bits=bits)
            path, state = root_state(reference)
            reference.a.work.max_operand_bits = cap
            expected = original_pair(reference, path, time, state)
            with self.subTest(bits=bits, cap=cap, time=time), \
                    patch.object(reference, "_root_pose", wraps=reference._root_pose) as direct:
                self.assertEqual(reference._phase_root_poses(path, time, state), expected)
                self.assertEqual(direct.call_count, 2)
            self.assertFalse(root_entries(reference))

    def test_warm_lookup_narrowing_falls_back_to_original_root_calculation(self):
        reference, _ = reference_case("P05", F(1, 2))
        path, state = root_state(reference)
        reference._phase_root_poses(path, F(1, 4), state)
        lookup = reference.a.lookup
        def narrowed(key):
            result = lookup(key)
            if key[:1] == ("source_phase_root_pair",):
                reference.a.work.max_operand_bits = 32767
            return result
        with patch.object(reference.a, "lookup", side_effect=narrowed), \
                patch.object(reference, "_root_pose", wraps=reference._root_pose) as direct:
            actual = reference._phase_root_poses(path, F(1, 4), state)
        self.assertEqual(direct.call_count, 2)
        self.assertEqual(actual, original_pair(reference, path, F(1, 4), state))

    def test_eviction_keeps_the_existing_cache_bound_and_reconstructs(self):
        reference, _ = reference_case("P01", F(1, 2))
        path, state = root_state(reference)
        expected = reference._phase_root_poses(path, F(1, 4), state)
        for index in range(MAX_CACHE + 1):
            reference.a.remember(("unrelated completed arithmetic", index), F(index))
        self.assertFalse(root_entries(reference))
        self.assertEqual(len(reference.a.cache), MAX_CACHE)
        self.assertEqual(reference._phase_root_poses(path, F(1, 4), state), expected)
        self.assertEqual(len(reference.a.cache), MAX_CACHE)
        self.assertEqual(reference.a.work.max_operations, 100000)

    def test_point_distance_elision_does_not_erase_uncertain_cell_widths(self):
        reference, _ = reference_case("P01", F(1, 2))
        for values in ((point(0), point(0), point(0)),
                       (point(F(2, 3)), point(-4), point(F(1, 16)))):
            expected = reference._distance(values, values)
            before = reference.a.work.operations
            self.assertEqual(reference._phase_root_distance(values, values), expected)
            self.assertEqual(reference.a.work.operations - before, 1)
        uncertain = (Interval(F(-1, 8), F(1, 8)), point(0), point(0))
        self.assertEqual(reference._phase_root_distance(uncertain, uncertain),
                         reference._distance(uncertain, uncertain))
        self.assertGreater(reference._phase_root_distance(uncertain, uncertain), 0)

    def test_point_distance_checks_omitted_widths_before_cap_restoration(self):
        reference, _ = reference_case("P01", F(1, 2))
        value = point(F(1, (1 << 200) - 1))
        values, calls = (value, point(0), point(0)), 0
        def transient_cap():
            nonlocal calls
            calls += 1
            reference.a.work.max_operand_bits = 256 if calls == 1 else 32768
        with patch.object(reference.a.work, "external_check", side_effect=transient_cap), \
                self.assertRaises(ReferenceError) as caught:
            reference._phase_root_distance(values, values)
        self.assertEqual(caught.exception.code, "resource")
        self.assertEqual(calls, 1)

    def test_point_distance_rechecks_its_zero_premise_after_callback_mutation(self):
        for changed in (Interval(F(3), F(3)), Interval(F(-1, 8), F(1, 8))):
            with self.subTest(changed=changed):
                reference, _ = reference_case("P01", F(1, 2))
                first, last = ((point(0), point(0), point(0)) for _ in range(2))
                expected = reference._distance((changed, *first[1:]), last)
                called = False

                def mutate():
                    nonlocal called
                    if not called:
                        called = True
                        object.__setattr__(first[0], "lo", changed.lo)
                        object.__setattr__(first[0], "hi", changed.hi)

                with patch.object(reference.a.work, "external_check", side_effect=mutate), \
                        patch.object(reference, "_distance", wraps=reference._distance) as direct:
                    actual = reference._phase_root_distance(first, last)
                self.assertTrue(called)
                self.assertEqual(actual, expected)
                self.assertGreater(actual, 0)
                self.assertEqual(direct.call_count, 1)

    def test_point_distance_cancellation_keeps_exception_identity(self):
        reference, _ = reference_case("P01", F(1, 2))
        values = (point(0),) * 3
        marker = ReferenceError("resource", "caller cancelled phase distance")
        with patch.object(reference.a.work, "external_check", side_effect=marker), \
                self.assertRaises(ReferenceError) as caught:
            reference._phase_root_distance(values, values)
        self.assertIs(caught.exception, marker)
        self.assertIs(reference.a.work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
