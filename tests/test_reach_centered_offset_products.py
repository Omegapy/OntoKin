"""Same-key product reuse preserves exact projections and hostile boundaries.

The disabled controls retain existing coefficient sharing. Source-level cost
comparisons include preparation; the kernel controls isolate the single paired
projection and compare it with an independent four-component Hamilton oracle.
"""
from contextlib import nullcontext
from dataclasses import dataclass, field, replace
from fractions import Fraction as F
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import patch

import ontokin.reach_reference_center as centered
from ontokin.reach_reference import MAX_CACHE, ReferenceError, _RecordingBodyRate
from ontokin.reach_reference_center import _CenteredNode, _CenteredPose, _Guard
from ontokin.reach_reference_plan import _LocalPose, _Node, _RootTranslation
from test_reach_centered_coefficients import entries
from test_reach_centered_identity_offsets import moving_p11
from test_reach_reference_centered_recording import R, UNIT, ZERO, hamilton, harness, point
from test_reach_reference_source_batch import prefix
from test_reach_reference_world_recording import reference_case


def enabled_products(enabled):
    return nullcontext() if enabled else patch.object(centered, "_product_native", return_value=False)


def plane_vector(axis, first=F(1, 4), second=F(1, 8), axial=F(3, 32)):
    result = [F(0)] * 3
    for index, value in zip(((axis + 1) % 3, (axis + 2) % 3, axis),
                            (first, second, axial)):
        result[index] = value
    return tuple(result)


def rotation_for(axis, scalar=F(3, 4), active=F(1, 2)):
    result = [F(0)] * 4
    result[0], result[axis + 1] = scalar, active
    return tuple(result)


def expected_offset(rotation, vector, axis):
    conjugate = (rotation[0], *(-value for value in rotation[1:]))
    exact = hamilton(hamilton(rotation, (F(0), *vector)), conjugate)[1:]
    return tuple(vector[index] if index == axis else
                 F((value.numerator << 128) // value.denominator, 1 << 128)
                 for index, value in enumerate(exact))


class Pair:
    """Two actual guards share one session; every callback remains the Work callback."""
    def __init__(self, axis=2, *, first=F(1, 4), scalar=F(3, 4), active=F(1, 2), clock=None):
        self.axis, self.action, self.callbacks = axis, None, 0
        self.reference, self.plan, self.batch = harness(self.check)
        self.rotation = rotation_for(axis, scalar, active)
        self.vectors = (plane_vector(axis, first, F(1, 8)),
                        plane_vector(axis, first, F(-1, 8)))
        self.clock = F(1, 8) if clock is None else clock
        self.pair = (1, axis, 0, 1)
        self.plan.cache_identity = object()
        self.plan.context = (object(), object(), 0, "after")
        self.plan.state = object()
        self.source = self.plan.cache_identity, "fixture.rotor"
        self.plan.nodes = tuple(_Node(path, "site", "fixture.rotor", _LocalPose(vector, UNIT), None)
                                for path, vector in zip(("fixture.north", "fixture.south"), self.vectors))
        self.plan.centered = tuple(_CenteredNode(vector, F(0), coefficient_source=self.source[1],
                                  product_pair=self.pair, product_owner=(node.path, node.kind, node.parent))
                                   for node, vector in zip(self.plan.nodes, self.vectors))
        self.session = centered._ProductSession(self.reference, self.plan, self.clock, self.batch)
        self.guard = None

    def check(self):
        self.callbacks += 1
        if self.action is not None:
            self.action(self)

    def project(self, index, *, selected=True, vector=None):
        self.guard = _Guard(self.reference, self.plan, self.batch, product_session=self.session)
        parent = self.guard.pose(_CenteredPose(ZERO, self.rotation, F(0), R, self.axis))
        self.frozen_vector = self.guard.vector(self.vectors[index] if vector is None else vector)
        return centered._offset(parent, self.frozen_vector, self.guard,
                                coefficient_source=self.source, product_session=self.session,
                                product_pair=self.pair if selected else None,
                                product_index=index if selected else None)

    def renew(self, clock):
        self.session.close()
        self.clock = clock
        self.session = centered._ProductSession(self.reference, self.plan, clock, self.batch)

    def close(self):
        self.session.close()


@dataclass(frozen=True)
class SourcePlan:
    """A small source graph for preparation tests, without imported case names."""
    nodes: tuple
    context: tuple = field(default_factory=lambda: (object(), object(), 0, "after"))
    cache_identity: object = field(default_factory=object)
    receipts: tuple = ()
    centered: object = None

    def admit_owners(self, reference):
        pass


def source_plan(axis=2, *, extra_pair=False):
    rotation = rotation_for(axis)
    root_body = SimpleNamespace(moving=False, witness=(None, None, None, tuple(map(point, UNIT)), None))
    body = _RecordingBodyRate(axis, F(0), False, ("independent test source",), "spindle",
                              lambda clock: tuple(map(point, rotation)), ())
    nodes = [_Node("hub", "root", None, _RootTranslation(tuple(map(point, ZERO))), root_body),
             _Node("spindle", "hinge", "hub", _LocalPose(ZERO, UNIT), body)]
    vectors = [plane_vector(axis), plane_vector(axis, second=F(-1, 8))]
    if extra_pair:
        vectors.extend((plane_vector(axis, F(3, 8), F(1, 16)),
                        plane_vector(axis, F(3, 8), F(-1, 16))))
    nodes.extend(_Node(f"projection.{index}", "site", "spindle", _LocalPose(vector, UNIT), None)
                 for index, vector in enumerate(vectors))
    return SourcePlan(tuple(nodes))


def source_harness():
    reference, _, batch = harness()
    reference._recording_body_domain = lambda: True
    batch.check_cursors = lambda: None
    batch.record_cursors = lambda values: None
    batch.discard_cursors = lambda: None
    return reference, batch


class CenteredOffsetProductKernelTests(unittest.TestCase):
    def test_all_axes_match_hamilton_oracle_and_save_one_complete_pair_operation(self):
        for axis in range(3):
            for scalar, active in ((F(3, 4), F(1, 2)), (F(-3, 4), F(1, 2)),
                                   (F(3, 4), F(-1, 2)), (F(1) - F(1, 1 << 128), F(1, 4))):
                outcomes = []
                for enabled in (False, True):
                    with enabled_products(enabled):
                        pair = Pair(axis, scalar=scalar, active=active)
                        try:
                            values = [pair.project(index) for index in (0, 1)]
                            for index, (value, uncertain) in enumerate(values):
                                self.assertEqual(value, expected_offset(pair.rotation, pair.vectors[index], axis))
                                self.assertTrue(uncertain)
                            outcomes.append((values, pair.reference.a.work.operations))
                            self.assertEqual(len(entries(pair.reference)), 1)
                            self.assertEqual(pair.reference.a.work.operations,
                                             sum(pair.reference.a.work.counts.values()))
                        finally:
                            pair.close()
                        self.assertIsNone(pair.reference.a._recording_product_after_tick)
                with self.subTest(axis=axis, scalar=scalar, active=active):
                    self.assertEqual(outcomes[0][0], outcomes[1][0])
                    self.assertEqual(outcomes[0][1] - outcomes[1][1], 1)

    def test_scalar_shortcuts_do_not_publish_or_claim_two_saved_multiplications(self):
        cases = [(value, F(3, 4), F(1, 2)) for value in (F(0), F(1), F(-1))]
        cases += [(F(1, 4), F(1, 2), F(1, 2)), (F(1, 4), F(3, 4), F(0))]
        for first, scalar, active in cases:
            outcomes = []
            for enabled in (False, True):
                with enabled_products(enabled):
                    pair = Pair(first=first, scalar=scalar, active=active)
                    try:
                        values = [pair.project(index) for index in (0, 1)]
                        outcomes.append((values, pair.reference.a.work.operations))
                        self.assertTrue(all(entry.products is None for entry in entries(pair.reference).values()))
                    finally:
                        pair.close()
            with self.subTest(first=first, scalar=scalar, active=active):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_stale_evaluation_tokens_decline_even_at_an_identical_clock(self):
        for clock in (F(1, 8), F(1, 4)):
            pair = Pair()
            try:
                pair.project(0)
                retained = next(iter(entries(pair.reference).values()))
                self.assertIsNotNone(retained.products)
                old_token = retained.products.token
                pair.renew(clock)
                before = pair.reference.a.work.operations
                actual, _ = pair.project(1)
                self.assertEqual(actual, expected_offset(pair.rotation, pair.vectors[1], pair.axis))
                self.assertEqual(pair.reference.a.work.operations - before, 9)
                self.assertIs(next(iter(entries(pair.reference).values())), retained)
                self.assertIs(retained.products.token, old_token)
            finally:
                pair.close()

    def test_nonselected_coefficient_hits_preserve_the_selected_payload(self):
        pair = Pair()
        try:
            pair.project(0)
            retained = next(iter(entries(pair.reference).values()))
            payload = retained.products
            self.assertIsNotNone(payload)
            different = plane_vector(pair.axis, second=F(1, 16))
            actual, _ = pair.project(0, selected=False, vector=different)
            self.assertEqual(actual, expected_offset(pair.rotation, different, pair.axis))
            self.assertIs(next(iter(entries(pair.reference).values())), retained)
            self.assertIs(retained.products, payload)
            before = pair.reference.a.work.operations
            pair.project(1)
            self.assertEqual(pair.reference.a.work.operations - before, 7)
        finally:
            pair.close()

    def test_expanded_receipt_uses_one_existing_slot_under_full_cache_pressure(self):
        pair = Pair()
        try:
            for index in range(MAX_CACHE):
                pair.reference.a.remember(("unrelated numeric value", index), F(index))
            pair.project(0)
            self.assertEqual(len(pair.reference.a.cache), MAX_CACHE)
            key, retained = next(iter(entries(pair.reference).items()))
            self.assertIsNotNone(retained.products)
            pair.project(1)
            self.assertEqual(len(pair.reference.a.cache), MAX_CACHE)
            self.assertIs(pair.reference.a.cache[key], retained)
        finally:
            pair.close()

    def test_every_actual_paired_callback_preserves_exception_identity_and_hook_cleanup(self):
        probe = Pair()
        try:
            probe.project(0)
            probe.project(1)
            count = probe.callbacks
        finally:
            probe.close()
        for fail_at in range(1, count + 1):
            for marker in (RuntimeError("original product caller"), ReferenceError("resource", "original product caller")):
                pair = Pair()
                def fail(current):
                    if current.callbacks == fail_at:
                        raise marker
                pair.action = fail
                try:
                    with self.subTest(fail_at=fail_at, error=type(marker).__name__), \
                            self.assertRaises(type(marker)) as caught:
                        pair.project(0)
                        pair.project(1)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(pair.reference.a.work.callback_error, marker)
                    self.assertEqual(pair.callbacks, fail_at)
                finally:
                    pair.close()
                self.assertIsNone(pair.reference.a._recording_product_after_tick)
                self.assertIsNone(pair.reference.a._recording_after_tick)

    def test_a_self_restoring_foreign_guard_cannot_reenable_the_second_product_skip(self):
        pair = Pair()
        calls = []
        try:
            pair.project(0)
            start, before = pair.callbacks, pair.reference.a.work.operations
            def install(current):
                if current.callbacks == start + 2:
                    original = current.guard.exact
                    def foreign(owner, *args):
                        calls.append(args)
                        owner.exact = original
                        return original(*args)
                    current.guard.exact = MethodType(foreign, current.guard)
            pair.action = install
            actual, _ = pair.project(1)
            self.assertEqual(actual, expected_offset(pair.rotation, pair.vectors[1], pair.axis))
            self.assertEqual(len(calls), 1)
            # The first skip preceded the departure; the second must execute.
            self.assertEqual(pair.reference.a.work.operations - before, 8)
        finally:
            pair.close()

    def test_foreign_session_reuse_cannot_override_the_latched_second_product_fallback(self):
        for scope in ("class", "instance"):
            pair, calls, installed = Pair(), [], []
            try:
                pair.project(0)
                start, before = pair.callbacks, pair.reference.a.work.operations
                def foreign(*args):
                    calls.append(args)
                    return True
                def install(current):
                    if current.callbacks == start + 2:
                        target = centered._ProductSession if scope == "class" else current.session
                        mutation = patch.object(target, "reuse", foreign)
                        mutation.start()
                        installed.append(mutation)
                pair.action = install
                actual, _ = pair.project(1)
                with self.subTest(scope=scope):
                    self.assertEqual(len(installed), 1)
                    self.assertFalse(calls)
                    self.assertEqual(actual, expected_offset(pair.rotation, pair.vectors[1], pair.axis))
                    # The first skip completed while native. An override
                    # returning True cannot authorize the second skip.
                    self.assertEqual(pair.reference.a.work.operations - before, 8)
                    self.assertIsNone(pair.reference.a.work.callback_error)
            finally:
                for mutation in reversed(installed):
                    mutation.stop()
                pair.close()

    def test_outer_floor_binding_precedes_the_first_product_callback(self):
        pair = Pair()
        marker, calls = RuntimeError("new floor is used only by the second expression"), []
        def change(current):
            if current.callbacks == 8:
                def foreign(owner, value):
                    calls.append(value)
                    raise marker
                current.guard.floor = MethodType(foreign, current.guard)
        pair.action = change
        try:
            with self.assertRaises(RuntimeError) as caught:
                pair.project(0)
            self.assertIs(caught.exception, marker)
            self.assertEqual(len(calls), 1)
            # Seven coefficient charges; four first-expression charges; three
            # second-expression charges before its newly bound floor raises.
            self.assertEqual(pair.reference.a.work.operations, 14)
            self.assertTrue(all(entry.products is None for entry in entries(pair.reference).values()))
        finally:
            pair.close()

    def test_publication_declines_evicted_or_replaced_slots_without_resurrection(self):
        probe = Pair()
        try:
            probe.project(0)
            publication = probe.callbacks
        finally:
            probe.close()
        for mutation in ("evict", "replace"):
            pair, changed = Pair(), []
            def intervene(current):
                if current.callbacks == publication:
                    key, old = next(iter(entries(current.reference).items()))
                    nested = replace(old)
                    changed.append((key, old, nested))
                    if mutation == "evict":
                        del current.reference.a.cache[key]
                    else:
                        current.reference.a.cache[key] = nested
            pair.action = intervene
            try:
                actual, _ = pair.project(0)
                self.assertEqual(actual, expected_offset(pair.rotation, pair.vectors[0], pair.axis))
                self.assertEqual(len(changed), 1)
                key, old, nested = changed[0]
                if mutation == "evict":
                    self.assertNotIn(key, pair.reference.a.cache)
                else:
                    self.assertIs(pair.reference.a.cache[key], nested)
                    self.assertIsNone(nested.products)
                before = pair.reference.a.work.operations
                actual, _ = pair.project(1)
                self.assertEqual(actual, expected_offset(pair.rotation, pair.vectors[1], pair.axis))
                self.assertGreaterEqual(pair.reference.a.work.operations - before, 9)
                self.assertIsNot(pair.reference.a.cache[key], old)
            finally:
                pair.close()

    def test_payload_field_and_rational_mutations_are_rejected_before_reuse(self):
        for field_name in ("operand", "first", "last", "clock", "seal"):
            pair = Pair()
            try:
                pair.project(0)
                payload = next(iter(entries(pair.reference).values())).products
                self.assertIsNotNone(payload)
                if field_name == "seal":
                    object.__setattr__(payload, "seal", ())
                elif field_name == "clock":
                    object.__setattr__(payload, "clock", (payload.clock[0] + 1, payload.clock[1]))
                else:
                    value = getattr(payload, field_name)
                    object.__setattr__(value, "_numerator", value.numerator + 1)
                with self.subTest(field=field_name), self.assertRaises(ReferenceError) as caught:
                    pair.project(1)
                self.assertEqual(caught.exception.code, "identity")
            finally:
                pair.close()

    def test_publication_watches_the_actual_detached_donor_operand(self):
        probe = Pair()
        try:
            probe.project(0)
            publication = probe.callbacks
        finally:
            probe.close()
        pair = Pair()
        def mutate(current):
            if current.callbacks == publication:
                value = current.frozen_vector[(current.axis + 1) % 3]
                object.__setattr__(value, "_numerator", value.numerator + 1)
        pair.action = mutate
        try:
            with self.assertRaises(ReferenceError) as caught:
                pair.project(0)
            self.assertEqual(caught.exception.code, "identity")
            self.assertTrue(all(entry.products is None for entry in entries(pair.reference).values()))
        finally:
            pair.close()

    def test_initial_narrow_domain_keeps_the_original_arithmetic_and_cost(self):
        outcomes = []
        for enabled in (False, True):
            with enabled_products(enabled):
                pair = Pair()
                pair.reference.a.work.max_operand_bits = 32767
                try:
                    with self.assertRaises(centered._ChangedDomain):
                        pair.project(0)
                    outcomes.append(pair.reference.a.work.operations)
                    self.assertFalse(entries(pair.reference))
                finally:
                    pair.close()
        self.assertEqual(outcomes, [0, 0])

    def test_live_narrowing_preserves_the_original_product_operand_refusal(self):
        pair = Pair()
        def narrow(current):
            # The cold coefficient receipt has completed; this is the first
            # original diagonal-times-vector operation, not a new boundary.
            if current.callbacks == 8:
                current.reference.a.work.max_operand_bits = 4
        pair.action = narrow
        try:
            with self.assertRaises(ReferenceError) as caught:
                pair.project(0)
            self.assertEqual(caught.exception.code, "resource")
            self.assertIn("operand limit", str(caught.exception))
            self.assertEqual(pair.reference.a.work.operations, 8)
            self.assertIsNone(pair.reference.a.work.callback_error)
            self.assertTrue(all(entry.products is None for entry in entries(pair.reference).values()))
        finally:
            pair.close()

    def test_cache_marker_departure_is_latched_even_when_the_cap_never_changes(self):
        pair = Pair()
        changes = []
        try:
            pair.project(0)
            start, before = pair.callbacks, pair.reference.a.work.operations
            def change(current):
                if current.callbacks == start + 2:
                    current.reference.a._cache_operand_limit = 32767
                    changes.append("departed")
                elif current.callbacks == start + 3:
                    current.reference.a._cache_operand_limit = 32768
                    changes.append("restored")
            pair.action = change
            actual, _ = pair.project(1)
            self.assertEqual(actual, expected_offset(pair.rotation, pair.vectors[1], pair.axis))
            self.assertEqual(changes, ["departed", "restored"])
            self.assertEqual(pair.reference.a.work.max_operand_bits, 32768)
            self.assertEqual(pair.reference.a.work.operations - before, 8)
        finally:
            pair.close()

    def test_selected_source_owner_and_recipe_mutations_cannot_borrow_a_receipt(self):
        for change in ("path", "parent", "stationary", "recipe_vector"):
            pair = Pair()
            try:
                pair.project(0)
                node = pair.plan.nodes[1]
                if change == "recipe_vector":
                    object.__setattr__(pair.plan.centered[1], "vector", plane_vector(pair.axis))
                elif change == "stationary":
                    object.__setattr__(node, "stationary", True)
                else:
                    object.__setattr__(node, change, "different.source")
                with self.subTest(change=change), self.assertRaises(ReferenceError) as caught:
                    pair.project(1)
                self.assertEqual(caught.exception.code, "identity")
            finally:
                pair.close()

    def test_product_observer_does_not_replace_the_existing_captured_oracle_hook(self):
        reference, _, _ = harness()
        seen = []
        marker = RuntimeError("existing oracle observer")
        replacement = lambda: seen.append("replacement")
        def caller():
            seen.append("caller")
            reference.a._recording_product_after_tick = replacement
        def old_observer():
            seen.append("old")
            raise marker
        reference.a.work.external_check = caller
        reference.a._recording_after_tick = old_observer
        reference.a._recording_product_after_tick = lambda: seen.append("product")
        with self.assertRaises(RuntimeError) as caught:
            reference.a.tick()
        self.assertIs(caught.exception, marker)
        self.assertEqual(seen[0], "caller")
        self.assertCountEqual(seen, ["caller", "product", "old"])
        self.assertIs(reference.a._recording_after_tick, old_observer)
        self.assertIs(reference.a._recording_product_after_tick, replacement)
        self.assertEqual(reference.a.work.operations, 1)

    def test_product_hook_cleanup_preserves_a_new_nested_owner(self):
        pair = Pair()
        try:
            pair.project(0)
            own_hook = pair.reference.a._recording_product_after_tick
            self.assertIsNotNone(own_hook)
            nested_hook = lambda: None
            pair.reference.a._recording_product_after_tick = nested_hook
            pair.close()
            self.assertIs(pair.reference.a._recording_product_after_tick, nested_hook)
        finally:
            pair.reference.a._recording_product_after_tick = None
            pair.close()

    def test_cleanup_does_not_invoke_a_callback_installed_hook_descriptor(self):
        pair = Pair()
        marker, touched, installed = RuntimeError("original callback before cleanup"), [], []
        try:
            pair.project(0)
            def descriptor(arithmetic):
                touched.append(True)
                raise AssertionError("cleanup bound a foreign hook descriptor")
            def fail(current):
                mutation = patch.object(type(current.reference.a), "_recording_product_after_tick",
                                        property(descriptor), create=True)
                mutation.start()
                installed.append(mutation)
                raise marker
            pair.action = fail
            with self.assertRaises(RuntimeError) as caught:
                pair.project(1)
            self.assertIs(caught.exception, marker)
            self.assertIs(pair.reference.a.work.callback_error, marker)
            pair.close()
            self.assertFalse(touched)
        finally:
            for mutation in reversed(installed):
                mutation.stop()
            pair.close()
        self.assertIsNone(pair.reference.a._recording_product_after_tick)

    def test_product_observer_never_binds_callback_installed_owner_descriptors(self):
        class ReferenceOwner:
            pass
        for field_name in ("cache", "check", "work", "reference_a"):
            pair, installed, touched = Pair(), [], []
            if field_name == "reference_a":
                # Give this ordinary data owner its own mutable class so the
                # callback can install a descriptor without affecting peers.
                reference = ReferenceOwner()
                reference.__dict__.update(pair.reference.__dict__)
                pair.close()
                pair.reference = reference
                pair.session = centered._ProductSession(reference, pair.plan, pair.clock, pair.batch)
            arithmetic, work = pair.reference.a, pair.reference.a.work
            marker = RuntimeError("foreign owner descriptor at an extra observer read")
            def descriptor(owner):
                touched.append(True)
                raise marker
            target, name = ((type(pair.reference), "a") if field_name == "reference_a"
                            else (type(arithmetic), field_name))
            try:
                pair.project(0)
                self.assertTrue(pair.session.valid)
                before = work.operations
                def install(current):
                    mutation = patch.object(target, name, property(descriptor), create=True)
                    mutation.start()
                    installed.append(mutation)
                pair.action = install
                # tick has already bound its original check before the
                # callback changes the class. No original cache/work/owner
                # read remains here; only the additional observer runs.
                with self.subTest(field=field_name):
                    arithmetic.tick()
                    self.assertEqual(len(installed), 1)
                    self.assertEqual(work.operations - before, 1)
                    self.assertFalse(pair.session.valid)
                    self.assertFalse(touched)
                    pair.close()
                    self.assertFalse(touched)
            finally:
                for mutation in reversed(installed):
                    mutation.stop()
                pair.close()
            self.assertIsNone(arithmetic._recording_product_after_tick)

    def test_plan_identity_swaps_are_latched_before_a_recipient_can_reuse_products(self):
        for field_name in ("cache_identity", "context", "state", "nodes", "centered"):
            for restore in (False, True):
                pair, changes = Pair(), []
                try:
                    pair.project(0)
                    saved = getattr(pair.plan, field_name)
                    replacement = tuple(list(saved)) if type(saved) is tuple else object()
                    self.assertIsNot(replacement, saved)
                    if type(saved) is tuple:
                        self.assertEqual(replacement, saved)
                    def replace_owner(current):
                        if not changes:
                            setattr(current.plan, field_name, replacement)
                            changes.append(True)
                    pair.action = replace_owner
                    # A real existing callback exposes the departure. Restore
                    # it before the next guard to distinguish a latched owner
                    # check from merely inspecting the eventual recipient.
                    pair.reference.a.tick()
                    if restore:
                        setattr(pair.plan, field_name, saved)
                    with self.subTest(field=field_name, restored=restore), \
                            self.assertRaises(ReferenceError) as caught:
                        pair.project(1)
                    self.assertEqual(caught.exception.code, "identity")
                    self.assertEqual(changes, [True])
                    self.assertIsNone(pair.reference.a.work.callback_error)
                finally:
                    pair.close()


class CenteredOffsetProductSourceTests(unittest.TestCase):
    def test_generic_preparation_selects_only_one_mirrored_pair_per_complete_plan(self):
        for axis in range(3):
            reference, batch = source_harness()
            plan = centered.prepare(source_plan(axis, extra_pair=True), reference, batch)
            selected = [(index, node, recipe) for index, (node, recipe) in
                        enumerate(zip(plan.nodes, plan.centered)) if recipe.product_pair is not None]
            with self.subTest(axis=axis):
                self.assertEqual(len(selected), 2)
                (first_index, first, donor), (last_index, last, recipient) = selected
                self.assertLess(first_index, last_index)
                self.assertEqual(donor.product_pair, recipient.product_pair)
                self.assertEqual(donor.product_pair[1:], (axis, first_index, last_index))
                self.assertEqual(first.parent, last.parent)
                self.assertFalse(first.stationary or last.stationary)
                self.assertEqual(donor.coefficient_source, recipient.coefficient_source)
                self.assertEqual(donor.product_owner, (first.path, first.kind, first.parent))
                self.assertEqual(recipient.product_owner, (last.path, last.kind, last.parent))
                self.assertEqual(donor.vector[(axis + 1) % 3], recipient.vector[(axis + 1) % 3])
                self.assertEqual(donor.vector[(axis + 2) % 3], -recipient.vector[(axis + 2) % 3])
                self.assertEqual(donor.vector[axis], recipient.vector[axis])

    def test_stationary_and_nonmirrored_sources_are_not_selected(self):
        for change in ("stationary_donor", "stationary_recipient", "first", "second", "axial"):
            reference, batch = source_harness()
            plan, nodes = source_plan(), list(source_plan().nodes)
            if change.startswith("stationary"):
                index = 2 if change == "stationary_donor" else 3
                nodes[index] = replace(nodes[index], stationary=True)
            else:
                vector = list(nodes[3].local.position)
                index = {"first": 0, "second": 1, "axial": 2}[change]
                vector[index] += F(1, 32)
                nodes[3] = replace(nodes[3], local=replace(nodes[3].local, position=tuple(vector)))
            prepared = centered.prepare(replace(plan, nodes=tuple(nodes)), reference, batch)
            with self.subTest(change=change):
                self.assertIs(type(prepared.centered), tuple)
                self.assertFalse(any(recipe.product_pair is not None for recipe in prepared.centered))

    def test_an_intervening_orientation_seed_prevents_pair_selection(self):
        reference, batch = source_harness()
        plan = source_plan()
        seed = replace(plan.nodes[1], path="another.spindle",
                       body=replace(plan.nodes[1].body, path="another.spindle"))
        nodes = (*plan.nodes[:3], seed, plan.nodes[3])
        prepared = centered.prepare(replace(plan, nodes=nodes), reference, batch)
        self.assertIs(type(prepared.centered), tuple)
        self.assertFalse(any(recipe.product_pair is not None for recipe in prepared.centered))

    def test_two_separate_source_segments_still_select_only_one_pair_per_plan(self):
        reference, batch = source_harness()
        plan = source_plan()
        second_seed = replace(plan.nodes[1], path="second.spindle",
                              body=replace(plan.nodes[1].body, path="second.spindle"))
        later = tuple(replace(node, path="second." + node.path, parent="second.spindle")
                      for node in plan.nodes[2:])
        prepared = centered.prepare(replace(plan, nodes=(*plan.nodes, second_seed, *later)), reference, batch)
        self.assertIs(type(prepared.centered), tuple)
        selected = [recipe for recipe in prepared.centered if recipe.product_pair is not None]
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0].product_pair, selected[1].product_pair)

    def test_complete_preparation_and_evaluation_cost_saves_one_per_eligible_key(self):
        for axis in range(3):
            outcomes = []
            for enabled in (False, True):
                with enabled_products(enabled):
                    reference, batch = source_harness()
                    plan = centered.prepare(source_plan(axis), reference, batch)
                    values = [centered.evaluate(plan, reference, F(index + 1, 128), batch)
                              for index in range(4)]
                    self.assertTrue(all(value is not None for value in values))
                    self.assertIsNone(reference.a._recording_product_after_tick)
                    outcomes.append((values, reference.a.work.operations))
            with self.subTest(axis=axis):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertEqual(outcomes[0][1] - outcomes[1][1], 4)

    def test_actual_p11_preparation_and_complete_keys_preserve_all_values_and_save_work(self):
        outcomes = []
        for enabled in (False, True):
            with enabled_products(enabled):
                reference, _ = reference_case("P11", F(1, 2))
                context, values = object(), []
                carriers = moving_p11(reference)
                before = reference.a.work.operations
                with reference.recording_source_batch(context):
                    for index in range(8):
                        value = reference._recording_centered_poses(carriers, F(index + 1, 128),
                                                                   recording_context=context)
                        self.assertIsNotNone(value)
                        values.append(value)
                        self.assertIsNone(reference.a._recording_product_after_tick)
                        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
                outcomes.append((values, reference.a.work.operations - before))
                self.assertEqual(reference.a.work.operations, sum(reference.a.work.counts.values()))
                self.assertIsNone(reference._recording_batch)
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])
        print(f"P11 complete preparation and eight keys: original={outcomes[0][1]}, reused={outcomes[1][1]}")

    def test_complete_p11_and_l03_prefix_bytes_and_validation_are_unchanged(self):
        for case in ("P11", "L03"):
            outcomes = []
            for enabled in (False, True):
                with enabled_products(enabled):
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.operations, sum(compiler.reach_work.counts.values()))
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                self.assertEqual(compiler.reach_work.max_elapsed_ms, 30000)
                self.assertEqual(compiler.reach_work.max_operand_bits, 32768)
                outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                if case == "P11":
                    self.assertLess(outcomes[1][2], outcomes[0][2])
                else:
                    self.assertLessEqual(outcomes[1][2], outcomes[0][2])
            print(f"{case} complete unchanged prefix: original={outcomes[0][2]}, reused={outcomes[1][2]}")


if __name__ == "__main__":
    unittest.main()
