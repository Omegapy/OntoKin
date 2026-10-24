"""Shared exact planar coefficients retain independent centers and live guards."""
from contextlib import nullcontext
from fractions import Fraction as F
from types import MethodType
import unittest
from unittest.mock import patch

import ontokin.reach_reference_center as centered
from ontokin.reach_reference import MAX_CACHE, ReferenceError
from ontokin.reach_reference_center import (
    _CenteredCoefficients, _CenteredPose, _ChangedDomain, _Guard, _coefficients, _offset,
)
from test_reach_centered_identity_offsets import moving_p11
from test_reach_reference_centered_recording import (
    G, R, ZERO, admitted_carriers, hamilton, harness, point,
)
from test_reach_reference_source_batch import prefix
from test_reach_reference_world_recording import reference_case


def entries(reference):
    return {key: value for key, value in reference.a.cache.items()
            if key[:1] == ("reference_centered_coefficients",)}


def project(reference, plan, batch, rotation, vector, axis, source, *, radius=R):
    guard = _Guard(reference, plan, batch)
    parent = guard.pose(_CenteredPose(ZERO, rotation, F(0), radius, axis))
    return _offset(parent, guard.vector(vector), guard, coefficient_source=source)


class CenteredCoefficientKernelTests(unittest.TestCase):
    def test_cold_and_shared_coefficients_match_full_hamilton_products_on_every_axis(self):
        for axis in range(3):
            for scalar, active in ((F(3, 4), F(1, 2)), (F(-3, 4), F(1, 2)),
                                   (F(1), G), (F(0), F(-1)), (F(2) - G, -G)):
                reference, plan, batch = harness()
                source = object(), "independent source orientation"
                rotation = [F(0)] * 4
                rotation[0], rotation[axis + 1] = scalar, active
                rotation = tuple(rotation)
                for vector in ((F(-1, 4), F(1, 2), F(1, 4)),
                               (F(1, 8), F(-3, 8), F(1, 2)),
                               tuple(F(int(index == axis)) for index in range(3)), ZERO):
                    actual, uncertain = project(reference, plan, batch, rotation, vector, axis, source)
                    conjugate = (rotation[0], *(-value for value in rotation[1:]))
                    exact = hamilton(hamilton(rotation, (F(0), *vector)), conjugate)[1:]
                    expected = tuple(vector[index] if index == axis else
                                     F((value.numerator << 128) // value.denominator, 1 << 128)
                                     for index, value in enumerate(exact))
                    with self.subTest(axis=axis, scalar=scalar, active=active, vector=vector):
                        self.assertEqual(actual, expected)
                        self.assertEqual(uncertain, any(value for index, value in enumerate(vector)
                                                       if index != axis))
                self.assertEqual(len(entries(reference)), 1)
                self.assertEqual(reference.a.work.max_operations, 100000)

    def test_two_nonaxial_offsets_save_actual_work_including_the_first_lookup_and_write(self):
        outcomes = []
        for shared in (False, True):
            reference, plan, batch = harness()
            source = (object(), "paired source") if shared else None
            rotation = (F(3, 4), F(0), F(0), F(-1, 2))
            values = [project(reference, plan, batch, rotation, vector, 2, source)
                      for vector in ((F(1, 4), F(-1, 2), F(1, 4)),
                                     (F(-1, 8), F(3, 8), F(1, 2)))]
            outcomes.append((values, reference.a.work.operations))
            self.assertEqual(reference.a.work.operations, sum(reference.a.work.counts.values()))
            self.assertEqual(len(entries(reference)), int(shared))
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertEqual(outcomes[0][1] - outcomes[1][1], 2)

    def test_one_source_replaces_its_operands_and_actual_lru_eviction_forces_a_miss(self):
        reference, plan, batch = harness()
        source = object(), "same source at several clocks"
        observed = []
        for scalar, active in ((F(3, 4), F(1, 2)), (F(3, 4), F(1, 2)),
                               (F(-3, 4), F(1, 2)), (F(-3, 4), F(1, 2))):
            before = reference.a.work.operations
            actual = _coefficients(scalar, active, _Guard(reference, plan, batch), source)
            observed.append(reference.a.work.operations - before)
            self.assertEqual(actual, (scalar * scalar - active * active, 2 * scalar * active))
            self.assertEqual(len(entries(reference)), 1)
        self.assertEqual(observed, [7, 1, 7, 1])
        key = next(iter(entries(reference)))
        for index in range(MAX_CACHE):
            reference.a.remember(("coefficient eviction", index), F(index))
        self.assertNotIn(key, reference.a.cache)
        before = reference.a.work.operations
        _coefficients(F(-3, 4), F(1, 2), _Guard(reference, plan, batch), source)
        self.assertEqual(reference.a.work.operations - before, 7)
        self.assertEqual(len(reference.a.cache), MAX_CACHE)

    def test_nonadmitted_sources_and_foreign_arithmetic_keep_the_five_original_operations(self):
        expected = (F(5, 16), F(-3, 4))
        for method in (None, "exact", "guard", "tick", "_sync_cache_operand_limit"):
            reference, plan, batch = harness()
            guard, calls = _Guard(reference, plan, batch), []
            if method is not None:
                original = getattr(reference.a, method)
                def dispatch(owner, *args, **kwargs):
                    calls.append(args)
                    return original(*args, **kwargs)
                setattr(reference.a, method, MethodType(dispatch, reference.a))
            source = None if method is None else (object(), "custom arithmetic")
            with self.subTest(method=method), patch.object(_Guard, "lookup",
                    side_effect=AssertionError("the original formula has no memo lookup")):
                self.assertEqual(_coefficients(F(3, 4), F(-1, 2), guard, source), expected)
            self.assertEqual(reference.a.work.operations, 5)
            self.assertFalse(entries(reference))
            if method == "exact":
                self.assertEqual(calls, [(F(3, 4), F(3, 4), "mul"),
                                        (F(-1, 2), F(-1, 2), "mul"),
                                        (F(9, 16), F(1, 4), "sub"),
                                        (F(3, 4), F(-1, 2), "mul"),
                                        (F(-3, 8), 2, "mul")])
            elif method == "_sync_cache_operand_limit":
                self.assertFalse(calls)

    def test_a_narrow_original_prospective_guard_runs_before_optional_domain_rejection(self):
        reference, plan, batch = harness()
        guard = _Guard(reference, plan, batch)
        scalar = F((1 << 127) - 1, 1 << 128)
        reference.a.work.max_operand_bits = 200
        with self.assertRaises(ReferenceError) as caught:
            _coefficients(scalar, F(1, 2), guard, (object(), "narrow original calculation"))
        self.assertEqual(caught.exception.code, "resource")
        self.assertIn("intermediate operand", str(caught.exception))
        self.assertEqual(reference.a.work.operations, 1)
        self.assertFalse(entries(reference))

    def test_foreign_cache_mapping_keeps_the_original_formula_without_lookup(self):
        class ForeignCache(dict):
            def get(self, *args):
                raise AssertionError("foreign cache lookup")
        reference, plan, batch = harness()
        reference.a.cache = ForeignCache()
        self.assertEqual(_coefficients(F(3, 4), F(1, 2), _Guard(reference, plan, batch),
                                      (object(), "foreign cache")), (F(5, 16), F(3, 4)))
        self.assertEqual(reference.a.work.operations, 5)
        self.assertFalse(reference.a.cache)

    def test_lookup_dispatch_replacement_executes_the_original_formula_without_foreign_sync(self):
        for method in ("exact", "guard", "tick", "_sync_cache_operand_limit"):
            armed, changed, dispatched = [False], [], []
            def check():
                if armed[0] and not changed:
                    changed.append(True)
                    setattr(reference.a, method, MethodType(dispatch, reference.a))
            reference, plan, batch = harness(check)
            source = object(), "warm source"
            first = _coefficients(F(3, 4), F(1, 2), _Guard(reference, plan, batch), source)
            original = getattr(reference.a, method)
            def dispatch(owner, *args, **kwargs):
                dispatched.append(args)
                if method == "_sync_cache_operand_limit":
                    self.fail("lookup admission invoked the newly installed cache synchronizer")
                return original(*args, **kwargs)
            guard, before = _Guard(reference, plan, batch), reference.a.work.operations
            armed[0] = True
            with self.subTest(method=method):
                self.assertEqual(_coefficients(F(3, 4), F(1, 2), guard, source), first)
                self.assertEqual(reference.a.work.operations - before, 6)
                self.assertEqual(bool(dispatched), method != "_sync_cache_operand_limit")

    def test_initial_and_lookup_guard_dispatch_replacement_preserve_the_original_sentinel(self):
        for method in ("exact", "checked"):
            for after_lookup in (False, True):
                armed, calls = [False], []
                marker = ReferenceError("resource", "original custom guard sentinel")
                def dispatch(owner, *args, **kwargs):
                    raise marker
                def check():
                    if armed[0]:
                        calls.append(True)
                        self.assertEqual(len(calls), 1)
                        setattr(guard, method, MethodType(dispatch, guard))
                reference, plan, batch = harness(check)
                source = object(), "custom guard"
                _coefficients(F(3, 4), F(1, 2), _Guard(reference, plan, batch), source)
                retained = next(iter(entries(reference).values()))
                guard, before = _Guard(reference, plan, batch), reference.a.work.operations
                if after_lookup:
                    armed[0] = True
                else:
                    setattr(guard, method, MethodType(dispatch, guard))
                with self.subTest(method=method, after_lookup=after_lookup), \
                        self.assertRaises(ReferenceError) as caught:
                    _coefficients(F(3, 4), F(1, 2), guard, source)
                self.assertIs(caught.exception, marker)
                self.assertEqual(reference.a.work.operations - before, int(after_lookup))
                self.assertIs(next(iter(entries(reference).values())), retained)

    def test_foreign_guard_descriptor_is_called_only_at_the_original_operation(self):
        reference, plan, batch = harness()
        guard, calls = _Guard(reference, plan, batch), []
        marker = RuntimeError("original exact descriptor")
        def descriptor(owner):
            calls.append(True)
            raise marker
        with patch.object(_Guard, "exact", property(descriptor)), self.assertRaises(RuntimeError) as caught:
            _coefficients(F(3, 4), F(1, 2), guard, (object(), "foreign descriptor"))
        self.assertIs(caught.exception, marker)
        self.assertEqual(calls, [True])
        self.assertEqual(reference.a.work.operations, 0)

    def test_second_square_dispatch_change_preserves_the_previously_bound_outer_operation(self):
        for admitted in (False, True):
            calls = []
            marker = RuntimeError("custom Guard exact first used by the cross product")
            def dispatch(owner, *args):
                raise marker
            def check():
                calls.append(True)
                if len(calls) == 2 + int(admitted):
                    guard.exact = MethodType(dispatch, guard)
            reference, plan, batch = harness(check)
            guard = _Guard(reference, plan, batch)
            source = (object(), "outer binding") if admitted else None
            with self.subTest(admitted=admitted), self.assertRaises(RuntimeError) as caught:
                _coefficients(F(3, 4), F(1, 2), guard, source)
            self.assertIs(caught.exception, marker)
            # The outer subtraction bound before both squares still runs;
            # custom dispatch is first invoked at the cross-product stage.
            self.assertEqual(reference.a.work.operations, 3 + int(admitted))
            self.assertEqual(len(calls), 3 + int(admitted))
            self.assertFalse(entries(reference))

    def test_temporary_dispatch_change_cannot_publish_restored_native_receipts(self):
        armed, calls, dispatched = [False], [], []
        def check():
            if not armed[0]:
                return
            calls.append(True)
            if len(calls) == 2:
                reference.a.exact = MethodType(dispatch, reference.a)
            elif len(calls) == 3:
                reference.a.exact = original
        reference, plan, batch = harness(check)
        original = reference.a.exact
        def dispatch(owner, *args):
            dispatched.append(args)
            return original(*args)
        guard = _Guard(reference, plan, batch)
        armed[0] = True
        self.assertEqual(_coefficients(F(3, 4), F(1, 2), guard, (object(), "temporary dispatch")),
                         (F(5, 16), F(3, 4)))
        self.assertEqual(dispatched, [(F(1, 2), F(1, 2), "mul")])
        self.assertEqual(len(calls), 6)
        self.assertFalse(entries(reference))

    def test_remember_callback_cannot_invoke_a_foreign_synchronizer_or_publish_a_value(self):
        calls = []
        def check():
            calls.append(True)
            if len(calls) == 7:
                reference.a._sync_cache_operand_limit = lambda: self.fail("foreign cache synchronization")
        reference, plan, batch = harness(check)
        self.assertEqual(_coefficients(F(3, 4), F(1, 2), _Guard(reference, plan, batch),
                                      (object(), "miss with changed remember")),
                         (F(5, 16), F(3, 4)))
        self.assertEqual(len(calls), 7)
        self.assertFalse(entries(reference))

    def test_changed_cached_shapes_or_fraction_leaves_are_rejected_before_reuse(self):
        for change in ("foreign", "scalar", "diagonal", "denominator", "seal"):
            reference, plan, batch = harness()
            source = object(), "sealed arithmetic"
            _coefficients(F(3, 4), F(1, 2), _Guard(reference, plan, batch), source)
            key, value = next(iter(entries(reference).items()))
            if change == "foreign":
                reference.a.cache[key] = (value.scalar, value.active, value.diagonal, value.cross)
            elif change in ("scalar", "diagonal"):
                object.__setattr__(getattr(value, change), "_numerator", 7)
            elif change == "denominator":
                object.__setattr__(value.cross, "_denominator", 0)
            else:
                object.__setattr__(value, "seal", ())
            with self.subTest(change=change), self.assertRaises(ReferenceError) as caught:
                _coefficients(F(3, 4), F(1, 2), _Guard(reference, plan, batch), source)
            self.assertEqual(caught.exception.code, "identity")

    def test_cold_remember_callback_cannot_mutate_a_retained_fraction_leaf(self):
        for field in ("scalar", "active", "diagonal", "cross"):
            for member in ("_numerator", "_denominator"):
                calls = []
                def check():
                    calls.append(True)
                    if len(calls) == 7:
                        value = next(value for value, kind, _, _ in guard.records
                                     if kind is _CenteredCoefficients)
                        operand = getattr(value, field)
                        object.__setattr__(operand, member, getattr(operand, member) + 1)
                    elif len(calls) > 7:
                        self.fail("a mutated cold receipt reached a later callback")
                reference, plan, batch = harness(check)
                guard = _Guard(reference, plan, batch)
                scalar, active = F(3, 4), F(1, 2)
                with self.subTest(field=field, member=member), self.assertRaises(ReferenceError) as caught:
                    _coefficients(scalar, active, guard, (object(), "cold receipt mutation"))
                self.assertEqual(caught.exception.code, "identity")
                self.assertEqual(len(calls), 7)
                self.assertEqual(reference.a.work.operations, 7)
                self.assertEqual((scalar, active), (F(3, 4), F(1, 2)))
                self.assertFalse(entries(reference))

    def test_every_cold_and_warm_offset_callback_preserves_cancellation_and_live_guards(self):
        rotation, vector = (F(3, 4), F(0), F(0), F(1, 2)), (F(1, 4), F(-1, 2), F(1, 4))
        for warm in (False, True):
            reference, plan, batch = harness()
            source = object(), "callback source"
            if warm:
                project(reference, plan, batch, rotation, vector, 2, source)
            before = reference.a.work.operations
            project(reference, plan, batch, rotation, vector, 2, source)
            count = reference.a.work.operations - before
            for fail_at in range(1, count + 1):
                for mutation in ("cancel", "cap", "precision", "operand", "cache_owner"):
                    armed, calls, saved = [False], [], []
                    marker = RuntimeError("cancel shared centered coefficient")
                    def check():
                        if not armed[0]:
                            return
                        calls.append(True)
                        if len(calls) == fail_at:
                            if mutation == "cancel":
                                raise marker
                            if mutation == "cap":
                                reference.a.work.max_operand_bits = 32767
                            elif mutation == "precision":
                                reference.a.scale = 1 << 127
                            elif mutation == "cache_owner":
                                reference.a.cache = dict(reference.a.cache)
                            else:
                                operand = guard.leaves[0][0]
                                saved.append((operand, operand.numerator))
                                object.__setattr__(operand, "_numerator", operand.numerator + 1)
                        else:
                            self.assertLess(len(calls), fail_at)
                    reference, plan, batch = harness(check)
                    source = object(), "callback source"
                    if warm:
                        project(reference, plan, batch, rotation, vector, 2, source)
                    guard = _Guard(reference, plan, batch)
                    parent = guard.pose(_CenteredPose(ZERO, rotation, F(0), R, 2))
                    frozen_vector = guard.vector(vector)
                    armed[0] = True
                    expected = RuntimeError if mutation == "cancel" else (
                        ReferenceError if mutation in ("operand", "cache_owner") else _ChangedDomain)
                    try:
                        with self.subTest(warm=warm, fail_at=fail_at, mutation=mutation), \
                                self.assertRaises(expected) as caught:
                            _offset(parent, frozen_vector, guard, coefficient_source=source)
                        if mutation == "cancel":
                            self.assertIs(caught.exception, marker)
                            self.assertIs(reference.a.work.callback_error, marker)
                        self.assertEqual(len(calls), fail_at)
                    finally:
                        for operand, numerator in saved:
                            object.__setattr__(operand, "_numerator", numerator)

    def test_hit_receipt_remains_live_during_the_remaining_offset_operations(self):
        armed, calls = [False], []
        def check():
            if armed[0]:
                calls.append(True)
                if len(calls) == 2:
                    object.__setattr__(cached.cross, "_numerator", cached.cross.numerator + 1)
                elif len(calls) > 2:
                    self.fail("a mutated shared coefficient reached a later callback")
        reference, plan, batch = harness(check)
        source = object(), "live shared result"
        rotation, vector = (F(3, 4), F(0), F(0), F(1, 2)), (F(1, 4), F(-1, 2), F(1, 4))
        project(reference, plan, batch, rotation, vector, 2, source)
        cached = next(iter(entries(reference).values()))
        armed[0] = True
        with self.assertRaises(ReferenceError) as caught:
            project(reference, plan, batch, rotation, vector, 2, source)
        self.assertEqual(caught.exception.code, "identity")
        self.assertEqual(len(calls), 2)


class CenteredCoefficientSourceTests(unittest.TestCase):
    def test_plan_selects_repeated_nonaxial_children_and_leaves_unique_sources_unmemoized(self):
        for case in ("P09", "P11"):
            reference, _ = reference_case(case, F(1, 2))
            context = object()
            carriers = moving_p11(reference) if case == "P11" else admitted_carriers(reference, case)
            with self.subTest(case=case), reference.recording_source_batch(context):
                self.assertIsNotNone(reference._recording_centered_poses(carriers, F(1, 8),
                                                                       recording_context=context))
                plan = reference._recording_phase_plan
                selected = {node.path: recipe.coefficient_source
                            for node, recipe in zip(plan.nodes, plan.centered)
                            if recipe.coefficient_source is not None}
                if case == "P09":
                    self.assertFalse(selected)
                    self.assertFalse(entries(reference))
                else:
                    eyes = {path: source for path, source in selected.items() if "eyes[" in path}
                    self.assertEqual(len(eyes), 3)
                    self.assertEqual(set(eyes.values()), {"rig.head.frame"})
                    self.assertTrue(any(node.path.startswith("rig.arms[") and
                                        recipe.coefficient_source is None
                                        for node, recipe in zip(plan.nodes, plan.centered)))

    def test_a_different_source_seed_between_two_eyes_declines_distant_reuse(self):
        reference, _ = reference_case("P11", F(1, 2))
        eyes = tuple(path for path in reference.model.objects if "rig.head.eyes[" in path)
        arms = tuple(path for path in moving_p11(reference) if path.endswith(".forearm"))
        self.assertEqual(len(eyes), 3)
        self.assertEqual(len(arms), 2)
        context, carriers = object(), (eyes[0], arms[0], eyes[1], arms[1])
        with reference.recording_source_batch(context):
            self.assertIsNotNone(reference._recording_centered_poses(carriers, F(1, 8),
                                                                   recording_context=context))
            plan = reference._recording_phase_plan
            selected = {node.path: recipe.coefficient_source
                        for node, recipe in zip(plan.nodes, plan.centered)
                        if recipe.coefficient_source is not None}
            self.assertFalse(any("eyes[" in path for path in selected))
            self.assertFalse(any(key[-1] == "rig.head.frame" for key in entries(reference)))

    def test_complete_mixed_source_evaluations_save_work_under_native_cache_pressure(self):
        for churn in (0, 32, MAX_CACHE):
            outcomes = []
            for shared in (False, True):
                scope = nullcontext() if shared else patch.object(centered, "_coefficient_domain", return_value=False)
                with scope:
                    reference, _ = reference_case("P11", F(1, 2))
                    context, carriers, values = object(), moving_p11(reference), []
                    with reference.recording_source_batch(context) as batch:
                        for index in range(8):
                            for item in range(MAX_CACHE if index == 0 and churn else churn):
                                reference.a.remember(("actual coefficient pressure", index, item), F(item))
                            value = reference._recording_centered_poses(carriers, F(index + 1, 128),
                                                                        recording_context=context)
                            self.assertIsNotNone(value)
                            values.append(value)
                            self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
                            self.assertTrue(all(key not in batch.cursors for key in entries(reference)))
                    outcomes.append((values, reference.a.work.operations))
                    self.assertEqual(reference.a.work.operations, sum(reference.a.work.counts.values()))
                    self.assertEqual(reference.a.work.max_operations, 100000)
                    self.assertEqual(reference.a.work.max_cache_entries, 256)
                self.assertIsNone(reference._recording_batch)
            with self.subTest(churn=churn):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])
            print(f"P11 complete mixed centered sources, cache churn={churn}: "
                  f"original={outcomes[0][1]}, shared={outcomes[1][1]}")

    def test_source_prefix_bytes_complete_validation_and_work_remain_compatible(self):
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for shared in (False, True):
                scope = nullcontext() if shared else patch.object(centered, "_coefficient_domain", return_value=False)
                with scope:
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                if case == "P11":
                    self.assertLess(outcomes[1][2], outcomes[0][2])
                else:
                    self.assertLessEqual(outcomes[1][2], outcomes[0][2])
            print(f"{case} exact coefficient source prefix: "
                  f"original={outcomes[0][2]}, shared={outcomes[1][2]}")

    def test_live_source_recipe_marker_mutation_rejects_the_whole_batch(self):
        reference, _ = reference_case("P11", F(1, 2))
        original_check, original_offset = reference.a.work.external_check, centered._offset
        armed, changed, owned = [], [], {}
        def check():
            original_check()
            if armed and not changed:
                changed.append(True)
                object.__setattr__(armed[0], "coefficient_source", "changed source marker")
            elif changed:
                self.fail("the mutated source recipe reached a later callback")
        def offset(parent, vector, guard, **kwargs):
            if kwargs.get("coefficient_source") is not None and not armed:
                recipe = next(value for value, kind, _, _ in guard.records
                              if kind is centered._CenteredNode)
                armed.append(recipe)
            return original_offset(parent, vector, guard, **kwargs)
        reference.a.work.external_check = check
        context, carriers = object(), moving_p11(reference)
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context) as batch:
                self.assertIsNotNone(reference._recording_centered_poses(carriers, F(1, 8),
                                                                       recording_context=context))
                owned.update(batch.cursors)
                with patch.object(centered, "_offset", offset):
                    reference._recording_centered_poses(carriers, F(3, 16), recording_context=context)
        self.assertEqual(caught.exception.code, "identity")
        self.assertEqual(changed, [True])
        self.assertTrue(all(reference.a.cache.get(key) is not value for key, value in owned.items()))
        self.assertIsNone(reference._recording_batch)

    def test_final_source_rejection_discards_owned_cursors_without_treating_arithmetic_as_poses(self):
        reference, _ = reference_case("P11", F(1, 2))
        context, carriers, owned = object(), moving_p11(reference), {}
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context) as batch:
                previous = reference._recording_centered_poses(carriers, F(1, 8), recording_context=context)
                self.assertIsNotNone(previous)
                owned.update(batch.cursors)
                self.assertTrue(entries(reference))
                self.assertTrue(all(key not in owned for key in entries(reference)))
                state = reference._state_at(F(1, 8), "after")
                state.ideal_positions["rig"] = tuple(map(point, (F(1, 8), F(5, 4), 0)))
        self.assertEqual(caught.exception.code, "identity")
        self.assertTrue(owned)
        self.assertTrue(all(reference.a.cache.get(key) is not value for key, value in owned.items()))
        self.assertIsNone(reference._recording_batch)
        self.assertTrue(all(type(value) is _CenteredCoefficients for value in entries(reference).values()))
        fresh_context = object()
        with reference.recording_source_batch(fresh_context):
            fresh = reference._recording_centered_poses(carriers, F(1, 8), recording_context=fresh_context)
            self.assertIsNotNone(fresh)
            for path, value in fresh.items():
                self.assertEqual(value.position, (previous[path].position[0] + F(1, 8),
                                                 *previous[path].position[1:]))
                self.assertEqual(value.orientation, previous[path].orientation)


if __name__ == "__main__":
    unittest.main()
