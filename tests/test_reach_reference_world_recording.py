"""Complete ideal carrier cursors remain independently enclosed and bounded."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_conformance
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachExecutionWork as Work
from ontokin.reach_reference import (
    Interval, MAX_CACHE, ReachReference, ReferenceError, _Arithmetic, _PoseArithmetic, _Uncertain,
)
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recurring_endpoint_claims import replace_document


def point(value):
    value = F(value)
    return Interval(value, value)


def arithmetic(*, bits=128, cap=32768):
    return _PoseArithmetic(_Arithmetic(work=Work(max_operand_bits=cap), bits=bits))


def quaternion_at(ops, axis, rate, clock, initial=(F(1, 2),) * 4):
    sine, cosine = ops.a.sincos(point(rate * clock / 2))
    increment = [cosine, point(0), point(0), point(0)]
    increment[axis + 1] = sine
    return ops.multiply(tuple(map(point, initial)), tuple(increment))


def cursors(ops):
    return {key: value for key, value in ops.a.cache.items()
            if key[:1] == ("reference_pose",) and key[3] == "recording_body_orientation"}


def reference_case(case, end=F(2), *, bits=128):
    compiler = compile_construction(source_case(case))
    reference = ReachReference(compiler.model, end=end, arithmetic=_Arithmetic(work=compiler.reach_work, bits=bits))
    return reference, compiler


class IndependentWorldRotationTests(unittest.TestCase):
    def assert_encloses(self, actual, finer):
        for cell, expected in zip(actual, finer):
            self.assertLessEqual(cell.lo, expected.lo)
            self.assertGreaterEqual(cell.hi, expected.hi)

    def test_all_cartesian_right_products_enclose_finer_direct_source_rotations(self):
        for axis, rate in ((0, F(7, 5)), (1, F(-9, 7)), (2, F(11, 8))):
            ops, fine, context = arithmetic(), arithmetic(bits=256), object()
            for index in range(68):
                time = F(index, 128)
                actual = ops._recording_body_orientation(
                    lambda: quaternion_at(ops, axis, rate, time), axis=axis, rate=rate,
                    witness=("independent analytic unit seed",), context=context, clock=time)
                expected = quaternion_at(fine, axis, rate, time)
                with self.subTest(axis=axis, index=index):
                    self.assert_encloses(actual, expected)
                    self.assertTrue(all(cell.hi - cell.lo < F(1, 1 << 100) for cell in actual))
                self.assertLessEqual(len(ops.a.cache), MAX_CACHE)
            self.assertLessEqual(ops.a.work.operations, 100000)
            self.assertEqual(ops.a.work.operations, sum(ops.a.work.counts.values()))

    def test_zero_pairs_and_cancelled_signed_rates_need_no_interval_products(self):
        ops, context = arithmetic(), object()
        fixed = tuple(map(point, (1, 0, 0, 0)))
        for time in (F(0), F(1, 8), F(1, 4)):
            with patch.object(ops, "_recording_rotate_sincos", side_effect=AssertionError("zero angular rate")):
                self.assertIs(ops._recording_body_orientation(
                    lambda: fixed, axis=2, rate=F(0), witness=("opposing nonzero source hinges",),
                    context=context, clock=time), fixed)
        self.assertEqual(next(iter(cursors(ops).values()))[-1], 2)
        ops, context, calls = arithmetic(), object(), []
        original = ops._recording_rotate_sincos
        def observe(*args, **kwargs):
            calls.append(args)
            return original(*args, **kwargs)
        for time in (F(0), F(1, 8)):
            with patch.object(ops, "_recording_rotate_sincos", side_effect=observe):
                ops._recording_body_orientation(
                    lambda: quaternion_at(ops, 2, F(1), time, initial=(1, 0, 0, 0)),
                    axis=2, rate=F(1), witness=("Z",), context=context, clock=time)
        self.assertEqual(len(calls), 1)

    def test_restart_clock_context_witness_and_increment_limits_use_direct_seeds(self):
        ops, context, seeds = arithmetic(), object(), []
        def sample(time, *, witness=("first source curve",), selected=context, rate=F(1)):
            def direct():
                seeds.append((time, witness, selected))
                return quaternion_at(ops, 2, rate, time)
            return ops._recording_body_orientation(direct, axis=2, rate=rate, witness=witness,
                                                   context=selected, clock=time)
        for index in range(65):
            sample(F(index, 128))
        key = ops._key("recording_body_orientation", context)
        self.assertEqual(len(seeds), 1)
        self.assertEqual(ops.a.cache[key][-1], 64)
        sample(F(65, 128))
        self.assertEqual(len(seeds), 2)
        self.assertEqual(ops.a.cache[key][-1], 0)
        sample(F(1, 4))  # rewind
        sample(F(5, 16), witness=("changed source curve",))
        sample(F(3, 8), selected=object())
        sample(F(2), witness=("changed source curve",))  # half-increment > 1/4
        self.assertEqual(len(seeds), 6)

    def test_eviction_keeps_the_existing_256_entry_cache_and_reseeds(self):
        ops, context = arithmetic(), object()
        for time in (F(0), F(1, 8)):
            ops._recording_body_orientation(lambda: quaternion_at(ops, 2, F(1), time),
                axis=2, rate=F(1), witness=("curve",), context=context, clock=time)
        for index in range(MAX_CACHE + 1):
            ops.a.remember(("unrelated complete numeric value", index), F(index))
        self.assertFalse(cursors(ops))
        self.assertEqual(len(ops.a.cache), MAX_CACHE)
        time = F(1, 4)
        self.assertEqual(ops._recording_body_orientation(lambda: quaternion_at(ops, 2, F(1), time),
            axis=2, rate=F(1), witness=("curve",), context=context, clock=time),
            quaternion_at(arithmetic(), 2, F(1), time))
        self.assertEqual(next(iter(cursors(ops).values()))[-1], 0)
        self.assertEqual(len(ops.a.cache), MAX_CACHE)
        self.assertEqual(ops.a.work.max_operations, 100000)

    def test_other_precisions_caps_types_and_large_rates_keep_the_original_direct_path(self):
        cases = ((256, 32768, 2, F(1), F(1)), (128, 32767, 2, F(1), F(1)),
                 (128, 32768, True, F(1), F(1)), (128, 32768, 2, 1., F(1)),
                 (128, 32768, 2, F(1, 1 << 1100), F(1)),
                 (128, 32768, 2, F(1), F(1, 1 << 1100)))
        for bits, cap, axis, rate, time in cases:
            ops, calls, marker = arithmetic(bits=bits, cap=cap), [], object()
            def direct():
                calls.append(True)
                return marker
            with self.subTest(bits=bits, cap=cap, axis=axis, rate=rate, time=time):
                self.assertIs(ops._recording_body_orientation(direct, axis=axis, rate=rate,
                    witness=("curve",), context=object(), clock=time), marker)
                self.assertEqual(calls, [True])
                self.assertFalse(cursors(ops))

    def test_lookup_and_delta_callbacks_narrow_before_reusing_a_completed_orientation(self):
        for fail_at in (1, 2, 3, 4):
            ops, context = arithmetic(), object()
            old = tuple(map(point, (1, 0, 0, 0)))
            ops._recording_body_orientation(lambda: old, axis=2, rate=F(1), witness=("curve",),
                                            context=context, clock=F(0))
            calls, directs = 0, []
            fresh = tuple(map(point, (0, 0, 0, 1)))
            def narrow():
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    ops.a.work.max_operand_bits = 32767
            def direct():
                directs.append(True)
                return fresh
            with self.subTest(fail_at=fail_at), patch.object(ops.a.work, "external_check", side_effect=narrow):
                self.assertIs(ops._recording_body_orientation(direct, axis=2, rate=F(1),
                    witness=("curve",), context=context, clock=F(1, 8)), fresh)
            self.assertEqual(directs, [True])

    def test_cancellation_in_a_product_or_publication_keeps_the_cursor_and_exception_identity(self):
        for location in ("product", "publication"):
            for marker in (RuntimeError("cancel independent world update"),
                           ReferenceError("resource", "caller owns this refusal")):
                ops, context = arithmetic(), object()
                ops._recording_body_orientation(lambda: quaternion_at(ops, 2, F(1), F(0)),
                    axis=2, rate=F(1), witness=("curve",), context=context, clock=F(0))
                key = ops._key("recording_body_orientation", context)
                before = ops.a.cache[key]
                rotate, remember = ops._recording_rotate_sincos, ops.a.remember
                def cancelled():
                    raise marker
                def product(*args, **kwargs):
                    ops.a.work.external_check = cancelled
                    return rotate(*args, **kwargs)
                def publish(candidate, value, **kwargs):
                    if candidate == key:
                        ops.a.work.external_check = cancelled
                    return remember(candidate, value, **kwargs)
                context_manager = (patch.object(ops, "_recording_rotate_sincos", side_effect=product)
                                   if location == "product" else patch.object(ops.a, "remember", side_effect=publish))
                with self.subTest(location=location, marker=type(marker).__name__), context_manager, \
                        self.assertRaises(type(marker)) as caught:
                    ops._recording_body_orientation(lambda: quaternion_at(ops, 2, F(1), F(1, 8)),
                        axis=2, rate=F(1), witness=("curve",), context=context, clock=F(1, 8))
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.a.work.callback_error, marker)
                self.assertEqual(ops.a.cache[key], before)
                self.assertLessEqual(len(ops.a.cache), MAX_CACHE)

    def test_a_direct_interval_failure_is_not_retried_into_a_later_broader_domain(self):
        ops, context = arithmetic(), object()
        ops._recording_body_orientation(lambda: quaternion_at(ops, 2, F(1), F(0)),
            axis=2, rate=F(1), witness=("curve",), context=context, clock=F(0))
        key = ops._key("recording_body_orientation", context)
        previous = ops.a.cache[key]
        rotate, multiply = ops._recording_rotate_sincos, ops.a.mul
        armed, failures, broadened = False, [], []
        def change_domain():
            if armed:
                if failures:
                    broadened.append(True)
                    ops.a.work.max_operand_bits = 32768
                else:
                    ops.a.work.max_operand_bits = 64
        def enter_rotation(*values, **kwargs):
            nonlocal armed
            armed = True
            return rotate(*values, **kwargs)
        def observe_original(a, b):
            try:
                return multiply(a, b)
            except ReferenceError as error:
                failures.append(error)
                raise
        with patch.object(ops.a.work, "external_check", side_effect=change_domain), \
                patch.object(ops, "_recording_rotate_sincos", side_effect=enter_rotation), \
                patch.object(ops.a, "mul", side_effect=observe_original), self.assertRaises(ReferenceError) as caught:
            ops._recording_body_orientation(lambda: quaternion_at(ops, 2, F(1), F(1, 8)),
                axis=2, rate=F(1), witness=("curve",), context=context, clock=F(1, 8))
        self.assertTrue(armed)
        self.assertEqual(len(failures), 1)
        self.assertIs(caught.exception, failures[0])
        self.assertFalse(broadened)
        self.assertEqual(ops.a.cache[key], previous)


class IndependentWorldSourceTests(unittest.TestCase):
    def test_fixed_positive_scalar_recipes_omit_identity_work_after_fresh_admission(self):
        reference, _ = reference_case("P09", F(1))
        parent = (point(F(1, 2)),) * 4
        with patch.object(reference.p, "quaternion", side_effect=AssertionError("exact fixed identity")):
            for inverse in (False, True):
                self.assertIs(reference._recording_fixed_orientation(parent, (8., 0., 0., 0.),
                                                                     inverse=inverse), parent)
        negative = reference._recording_fixed_orientation(parent, (-8., 0., 0., 0.), inverse=True)
        self.assertEqual(negative, (point(F(-1, 2)),) * 4)
        reference.a.work.external_check = lambda: setattr(reference.a.work, "max_operand_bits", 64)
        with self.assertRaises(ReferenceError) as caught:
            reference._recording_fixed_orientation(parent, (2. ** -200, 0., 0., 0.))
        self.assertEqual(caught.exception.code, "resource")

    def test_stationary_affine_receipts_need_no_numeric_lookup_but_keep_duration_admission(self):
        reference, _ = reference_case("P07", F(1))
        state = reference._state_at(F(0), "after")
        relation = reference.model.actions["reach"].reach.shoulder
        active = state.actions["reach"]
        self.assertEqual(F(active.ideal_initial[0]), F(active.targets[0]))
        with patch.object(reference.a, "lookup", side_effect=AssertionError("exact zero affine slope")):
            rate, _, receipt = reference._recording_coordinate_recipe(relation, state)
        self.assertEqual(rate, 0)
        self.assertIsNotNone(receipt)
        reference.model.actions["reach"].duration = F(0)
        with self.assertRaises(_Uncertain):
            reference._recording_coordinate_recipe(relation, state)

    def test_p09_and_spinning_root_use_independent_signed_body_rates(self):
        for case, root_rate in (("P09", F(0)), ("P16", F(1, 4))):
            reference, _ = reference_case(case, F(1))
            state = reference._state_at(F(0), "after")
            action = reference.model.actions["reach"].reach
            shoulder = reference._coordinate(action.shoulder, F(1, 8), state, ideal=True)[1]
            elbow = reference._coordinate(action.elbow, F(1, 8), state, ideal=True)[1]
            observed, original = {}, reference.p._recording_body_orientation
            def observe(*args, **kwargs):
                observed[kwargs["context"][-1]] = kwargs
                return original(*args, **kwargs)
            # This spy exercises both signed body rates; the identity-carrier
            # tests separately cover omitting an identical parent's trajectory.
            with self.subTest(case=case), \
                    patch.object(reference, "_recording_identity_parent", return_value=None), \
                    patch.object(reference.p, "_recording_body_orientation", side_effect=observe):
                reference.recording_pose_enclosures(("rig.tool.frame",), F(1, 8), recording_context=object())
            self.assertEqual(observed["rig.arm.upper.frame"]["rate"], root_rate + shoulder)
            self.assertEqual(observed["rig.arm.forearm.frame"]["rate"], root_rate + shoulder + elbow)
            self.assertEqual(observed["rig.arm.forearm.frame"]["axis"], 2)

    def test_prescribed_root_cursor_keeps_world_translation_and_encloses_finer_spin(self):
        reference, compiler = reference_case("P05", F(1))
        finer = ReachReference(compiler.model, end=F(1), arithmetic=_Arithmetic(work=Work(), bits=256))
        context, carrier = object(), "rig.frame"
        spins, spin = [], reference.p.spin
        def observe(*args, **kwargs):
            spins.append(args)
            return spin(*args, **kwargs)
        with patch.object(reference.p, "spin", side_effect=observe):
            for index in range(1, 18):
                time = F(index, 32)
                actual = reference.recording_pose_enclosures((carrier,), time, recording_context=context)[carrier]
                expected = finer.recording_pose_enclosures((carrier,), time)[carrier]
                for current, direct in ((actual.position, expected.position),
                                        (actual.orientation, expected.orientation)):
                    for cell, enclosed in zip(current, direct):
                        self.assertLessEqual(cell.lo, enclosed.lo)
                        self.assertGreaterEqual(cell.hi, enclosed.hi)
                self.assertTrue(actual.position[0].contains(time / 2))
        self.assertEqual(len(spins), 1)
        selected = [value for key, value in cursors(reference.p).items() if key[-1][-1] == carrier]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0][-1], 16)
        with patch.object(reference.p, "_recording_body_orientation", side_effect=AssertionError("source root cursor")):
            source = reference.pose_enclosure(carrier, F(3, 4))
            ordinary = reference.recording_pose_enclosures((carrier,), F(3, 4))[carrier]
        self.assertEqual(source.orientation, ordinary.orientation)
        self.assertNotEqual(source.omega, (point(0),) * 3)

    def test_root_source_mutation_during_translation_rejects_before_cursor_publication(self):
        reference, compiler = reference_case("P05", F(1))
        finer = ReachReference(compiler.model, end=F(1), arithmetic=_Arithmetic(work=Work(), bits=256))
        context, carrier = object(), "rig.frame"
        reference.recording_pose_enclosures((carrier,), F(1, 8), recording_context=context)
        key = next(key for key in cursors(reference.p) if key[-1][-1] == carrier)
        previous = reference.a.cache[key]
        action = reference.model.actions["turn"]
        vector, changed = action.vector, []
        translation = reference._prescribed_root_translation
        def mutate():
            changed.append(True)
            action.vector = (0., 0., -.25)
            reference.a.work.external_check = None
        def observe(*args, **kwargs):
            reference.a.work.external_check = mutate
            return translation(*args, **kwargs)
        with patch.object(reference, "_prescribed_root_translation", side_effect=observe), \
                self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures((carrier,), F(1, 4), recording_context=context)
        self.assertEqual(changed, [True])
        self.assertEqual(caught.exception.code, "identity")
        self.assertEqual(reference.a.cache[key], previous)
        action.vector, reference.a.work.external_check = vector, None
        actual = reference.recording_pose_enclosures((carrier,), F(1, 4), recording_context=context)[carrier]
        expected = finer.recording_pose_enclosures((carrier,), F(1, 4))[carrier]
        for cell, enclosed in zip(actual.orientation, expected.orientation):
            self.assertLessEqual(cell.lo, enclosed.lo)
            self.assertGreaterEqual(cell.hi, enclosed.hi)

    def test_complete_positions_and_orientations_enclose_finer_direct_source_graphs(self):
        carriers = ("rig.frame", "rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.tool.frame")
        for case in ("P09", "P16"):
            reference, compiler = reference_case(case, F(1))
            finer = ReachReference(compiler.model, end=F(1), arithmetic=_Arithmetic(work=Work(), bits=256))
            context = object()
            for index in range(1, 17):
                time = F(index, 32)
                actual = reference.recording_pose_enclosures(carriers, time, recording_context=context)
                expected = finer.recording_pose_enclosures(carriers, time)
                for carrier in carriers:
                    with self.subTest(case=case, index=index, carrier=carrier):
                        for left, right in ((actual[carrier].position, expected[carrier].position),
                                            (actual[carrier].orientation, expected[carrier].orientation)):
                            for cell, enclosed in zip(left, right):
                                self.assertLessEqual(cell.lo, enclosed.lo)
                                self.assertGreaterEqual(cell.hi, enclosed.hi)
            self.assertTrue(cursors(reference.p))
            self.assertLessEqual(compiler.budget.operations, 100000)
            self.assertLessEqual(finer.a.work.operations, 100000)

    def test_source_axis_action_law_anchor_and_attachment_changes_force_fresh_seeds(self):
        for change in ("axis", "initial", "target", "duration", "elapsed", "attachment"):
            reference, _ = reference_case("P09", F(1))
            context, carrier = object(), "rig.arm.forearm.frame"
            for time in (F(1, 8), F(1, 4)):
                reference.recording_pose_enclosures((carrier,), time, recording_context=context)
            state = reference._state_at(F(1, 4), "after")
            active = state.actions["reach"]
            action = reference.model.actions["reach"]
            if change == "axis":
                reference.model.joints[action.reach.shoulder].axis = (0., 0., -1.)
            elif change == "initial":
                active.ideal_initial = (active.ideal_initial[0] + F(1, 8), active.ideal_initial[1])
            elif change == "target":
                active.targets = (active.targets[0] + .125, active.targets[1])
            elif change == "duration":
                action.duration += F(1, 8)
            elif change == "elapsed":
                active.elapsed += F(1, 32)  # unchanged rate, changed curve
            else:
                child = reference.model.sites[reference.model.joints[action.reach.elbow].child]
                child.pose = replace(child.pose, rotation=(0., 1., 0., 0.))
            # Reusing the SAME explicit clock also exercises the complete-map
            # cache barrier and the context-free seed's fresh source recipe.
            time = F(1, 4)
            with self.subTest(change=change):
                actual = reference.recording_pose_enclosures((carrier,), time, recording_context=context)[carrier]
                expected = reference._pose_map(time, state, ideal=True, pose_only=True,
                                               selected=(carrier,), recording_seed=True)[carrier]
                self.assertEqual(actual.orientation, expected.orientation)
                selected = [value for key, value in cursors(reference.p).items() if key[-1][-1] == carrier]
                self.assertEqual(len(selected), 1)
                self.assertEqual(selected[0][-1], 0)

    def test_source_capture_callback_binds_the_rate_and_seed_to_the_same_new_values(self):
        reference, compiler = reference_case("P09", F(1))
        finer = ReachReference(compiler.model, end=F(1), arithmetic=_Arithmetic(work=Work(), bits=256))
        carrier, context = "rig.arm.forearm.frame", object()
        relation = reference.model.actions["reach"].reach.elbow
        joint, old_axis = reference.model.joints[relation], reference.model.joints[relation].axis
        capture, changed = reference._recording_capture, []
        def observe(read):
            values = read()
            if not changed and values[0] == relation and len(values) == 8:
                def mutate():
                    changed.append(True)
                    joint.axis = (0., 0., -1.)
                    reference.a.work.external_check = None
                reference.a.work.external_check = mutate
            return capture(read)
        with patch.object(reference, "_recording_capture", side_effect=observe):
            actual = reference.recording_pose_enclosures((carrier,), F(1, 8), recording_context=context)[carrier]
        self.assertEqual(changed, [True])
        finer.model.joints[relation].axis = (0., 0., -1.)
        expected = finer.recording_pose_enclosures((carrier,), F(1, 8))[carrier]
        for cell, enclosed in zip(actual.orientation, expected.orientation):
            self.assertLessEqual(cell.lo, enclosed.lo)
            self.assertGreaterEqual(cell.hi, enclosed.hi)
        joint.axis = finer.model.joints[relation].axis = old_axis
        actual = reference.recording_pose_enclosures((carrier,), F(1, 4), recording_context=context)[carrier]
        expected = finer.recording_pose_enclosures((carrier,), F(1, 4))[carrier]
        for cell, enclosed in zip(actual.orientation, expected.orientation):
            self.assertLessEqual(cell.lo, enclosed.lo)
            self.assertGreaterEqual(cell.hi, enclosed.hi)
        selected = [value for key, value in cursors(reference.p).items() if key[-1][-1] == carrier]
        self.assertEqual(selected[0][-1], 0)

    def test_seed_arithmetic_uses_immutable_operands_if_a_callback_changes_and_restores_source(self):
        reference, compiler = reference_case("P09", F(1))
        finer = ReachReference(compiler.model, end=F(1), arithmetic=_Arithmetic(work=Work(), bits=256))
        carrier, context = "rig.arm.forearm.frame", object()
        joint = reference.model.joints[reference.model.actions["reach"].reach.elbow]
        old_axis, changed = joint.axis, []
        body_orientation = reference.p._recording_body_orientation
        def observe(direct, **kwargs):
            if kwargs["context"][-1] != carrier:
                return body_orientation(direct, **kwargs)
            def wrapped_direct():
                def mutate():
                    changed.append(True)
                    joint.axis = (0., 0., -1.)
                    reference.a.work.external_check = None
                reference.a.work.external_check = mutate
                try:
                    return direct()
                finally:
                    joint.axis = old_axis
                    reference.a.work.external_check = None
            return body_orientation(wrapped_direct, **kwargs)
        with patch.object(reference.p, "_recording_body_orientation", side_effect=observe):
            first = reference.recording_pose_enclosures((carrier,), F(1, 8), recording_context=context)[carrier]
        self.assertEqual(changed, [True])
        for time, actual in ((F(1, 8), first), (F(1, 4), reference.recording_pose_enclosures(
                (carrier,), F(1, 4), recording_context=context)[carrier])):
            expected = finer.recording_pose_enclosures((carrier,), time)[carrier]
            for cell, enclosed in zip(actual.orientation, expected.orientation):
                self.assertLessEqual(cell.lo, enclosed.lo)
                self.assertGreaterEqual(cell.hi, enclosed.hi)

    def test_changed_source_during_seed_or_final_publication_preserves_the_previous_cursor(self):
        for location in ("seed", "publication"):
            reference, compiler = reference_case("P09", F(1))
            finer = ReachReference(compiler.model, end=F(1), arithmetic=_Arithmetic(work=Work(), bits=256))
            carrier, context = "rig.arm.forearm.frame", object()
            reference.recording_pose_enclosures((carrier,), F(1, 8), recording_context=context)
            key = next(key for key in cursors(reference.p) if key[-1][-1] == carrier)
            previous = reference.a.cache[key]
            joint = reference.model.joints[reference.model.actions["reach"].reach.elbow]
            old_axis, changed = joint.axis, []
            def mutate():
                changed.append(True)
                joint.axis = (0., 0., -1.)
                reference.a.work.external_check = None
            body_orientation, remember = reference.p._recording_body_orientation, reference.a.remember
            def observe(direct, **kwargs):
                if kwargs["context"][-1] != carrier:
                    return body_orientation(direct, **kwargs)
                def wrapped_direct():
                    reference.a.work.external_check = mutate
                    return direct()
                return body_orientation(wrapped_direct, **kwargs)
            def publish(candidate, value, **kwargs):
                if candidate == key:
                    reference.a.work.external_check = mutate
                return remember(candidate, value, **kwargs)
            manager = (patch.object(reference.p, "_recording_body_orientation", side_effect=observe)
                       if location == "seed" else patch.object(reference.a, "remember", side_effect=publish))
            with self.subTest(location=location), manager, self.assertRaises(ReferenceError) as caught:
                # Same-clock reuse requires a new direct seed in both modes.
                reference.recording_pose_enclosures((carrier,), F(1, 8), recording_context=context)
            self.assertEqual(changed, [True])
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(reference.a.cache[key], previous)
            joint.axis, reference.a.work.external_check = old_axis, None
            actual = reference.recording_pose_enclosures((carrier,), F(1, 4), recording_context=context)[carrier]
            expected = finer.recording_pose_enclosures((carrier,), F(1, 4))[carrier]
            for cell, enclosed in zip(actual.orientation, expected.orientation):
                self.assertLessEqual(cell.lo, enclosed.lo)
                self.assertGreaterEqual(cell.hi, enclosed.hi)

    def test_original_affine_slope_failure_is_not_retried_after_a_callback_widens_the_cap(self):
        reference, _ = reference_case("P09", F(1))
        reference.a.cache.clear()
        recipe, exact = reference._recording_coordinate_recipe, reference.a.exact
        armed, failures, broadened = False, [], []
        def change_domain():
            if failures:
                broadened.append(True)
                reference.a.work.max_operand_bits = 32768
            else:
                reference.a.work.max_operand_bits = 1
        def enter_recipe(*args, **kwargs):
            nonlocal armed
            armed = True
            return recipe(*args, **kwargs)
        def observe_exact(first, last, kind):
            if armed and kind == "sub":
                reference.a.work.external_check = change_domain
            try:
                return exact(first, last, kind)
            except ReferenceError as error:
                failures.append(error)
                raise
        with patch.object(reference, "_recording_coordinate_recipe", side_effect=enter_recipe), \
                patch.object(reference.a, "exact", side_effect=observe_exact), \
                self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures(("rig.arm.forearm.frame",), F(1, 8), recording_context=object())
        self.assertTrue(armed)
        self.assertEqual(len(failures), 1)
        self.assertIs(caught.exception, failures[0])
        self.assertEqual(caught.exception.code, "resource")
        self.assertFalse(broadened)
        self.assertEqual(reference.a.work.max_operand_bits, 1)

    def test_unsupported_axes_offsets_and_fixed_rotations_keep_the_ordinary_graph(self):
        carrier = "rig.arm.forearm.frame"
        for change in ("noncoaxial", "nonunit", "child_offset", "oblique_attachment"):
            reference, _ = reference_case("P09", F(1))
            elbow = reference.model.joints[reference.model.actions["reach"].reach.elbow]
            child = reference.model.sites[elbow.child]
            if change == "noncoaxial":
                elbow.axis = (0., 1., 0.)
            elif change == "nonunit":
                elbow.axis = (0., 0., .5)
            elif change == "child_offset":
                child.pose = replace(child.pose, position=(.125, 0., 0.))
            else:
                child.pose = replace(child.pose, rotation=(1., 1., 1., 1.))
            observed, original = [], reference.p._recording_body_orientation
            def observe(*args, **kwargs):
                observed.append(kwargs["context"][-1])
                return original(*args, **kwargs)
            with self.subTest(change=change), patch.object(reference.p, "_recording_body_orientation", side_effect=observe):
                actual = reference.recording_pose_enclosures((carrier,), F(1, 8), recording_context=object())[carrier]
            self.assertNotIn(carrier, observed)
            state = reference._state_at(F(1, 8), "after")
            expected = reference._pose_map(F(1, 8), state, ideal=True, pose_only=True,
                                           selected=(carrier,), recording_seed=True)[carrier]
            self.assertEqual(actual.orientation, expected.orientation)
            self.assertEqual(actual.position, expected.position)

    def test_paused_and_dynamic_sources_do_not_acquire_a_world_cursor(self):
        reference, _ = reference_case("P09", F(1))
        state = reference._state_at(F(0), "after")
        state.actions["reach"].status = "paused"
        with patch.object(reference.p, "_recording_body_orientation", side_effect=AssertionError("paused world law")):
            reference.recording_pose_enclosures(("rig.tool.frame",), F(1, 4), recording_context=object())
        reference, _ = reference_case("P16", F(3))
        with patch.object(reference.p, "_recording_body_orientation", side_effect=AssertionError("dynamic world law")):
            reference.recording_pose_enclosures(("payload.frame",), F(9, 4), recording_context=object())

    def test_boundary_sides_and_changed_root_anchor_cannot_borrow_a_previous_cursor(self):
        reference, _ = reference_case("P16", F(1))
        context, carrier = object(), "rig.arm.forearm.frame"
        reference.recording_pose_enclosures((carrier,), F(7, 8), recording_context=context)
        for side in ("before", "after"):
            with self.subTest(side=side):
                reference.recording_pose_enclosures((carrier,), F(1), side, recording_context=context)
                selected = [value for key, value in cursors(reference.p).items()
                            if key[-1][-1] == carrier and key[-1][0][-1] == side and value[3] == 1]
                self.assertEqual(len(selected), 1)
                self.assertEqual(selected[0][-1], 0)
        reference, _ = reference_case("P16", F(1))
        state = reference._state_at(F(0), "after")
        state.actions["turn"].rotation_error = F(1, 1 << 80)
        with patch.object(reference.p, "_recording_body_orientation", side_effect=AssertionError("uncertain root anchor")):
            reference.recording_pose_enclosures((carrier,), F(1, 4), recording_context=object())

    def test_late_added_source_admission_rechecks_the_completed_pose_in_the_live_domain(self):
        reference, _ = reference_case("P09", F(1))
        original, armed = reference._recording_attached_body, []
        def narrow(parent, attachment, **kwargs):
            if parent is not None and parent.rate and attachment[0] == "site":
                armed.append(attachment)
                reference.a.work.external_check = lambda: setattr(reference.a.work, "max_operand_bits", 64)
            return original(parent, attachment, **kwargs)
        with patch.object(reference, "_recording_attached_body", side_effect=narrow), \
                self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures(("rig.tool.frame",), F(1, 4), recording_context=object())
        self.assertTrue(armed)
        self.assertEqual(caught.exception.code, "resource")
        self.assertEqual(reference.a.work.max_operand_bits, 64)

    def test_source_observations_never_borrow_recording_cursors_or_unused_rates(self):
        reference, _ = reference_case("P09", F(1))
        carrier = "rig.arm.forearm.frame"
        reference.recording_pose_enclosures((carrier,), F(1, 8), recording_context=object())
        with patch.object(reference.p, "_recording_body_orientation", side_effect=AssertionError("source cursor")):
            full = reference.pose_enclosure(carrier, F(1, 4))
            actual = reference.recording_pose_enclosures((carrier,), F(1, 4), ideal=False)[carrier]
            direct = reference.recording_pose_enclosures((carrier,), F(1, 4))[carrier]
        self.assertEqual(full.orientation, direct.orientation)
        self.assertNotEqual(full.omega, (point(0),) * 3)
        self.assertFalse(hasattr(actual, "omega"))
        self.assertFalse(hasattr(direct, "velocity"))

    def test_independent_world_source_walk_has_no_production_pose_or_derivative_oracle(self):
        reference, _ = reference_case("P09", F(1))
        context = object()
        unavailable = AssertionError("production oracle called by independent reader")
        with patch("ontokin.reach_phase.phase_bounds", side_effect=unavailable), \
                patch("ontokin.reach_pose.ReachPoseOps", side_effect=unavailable), \
                patch("ontokin.reach_runtime.ReachSimulator", side_effect=unavailable):
            for time in (F(1, 8), F(1, 4)):
                reference.recording_pose_enclosures(("rig.tool.frame",), time, recording_context=context)
        self.assertTrue(cursors(reference.p))

    def test_complete_glb_bytes_acceptance_and_hostile_claims_match_with_less_shared_work(self):
        for case in ("P07", "P09", "P05"):
            outcomes = []
            for optimized in (False, True):
                built = compile_construction(source_case(case))
                options = ExportOptions(end=F(1, 4), fps=24, helpers=False)
                mode = nullcontext() if optimized else patch.object(ReachReference, "_recording_body_domain", return_value=False)
                with mode:
                    result = export_glb(built.model, options=options,
                        target_contract="ontokin.glb/0.6", work=built.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(built.reach_work.max_operations, 100000)
                self.assertLessEqual(built.budget.operations, 100000)
                outcomes.append((result.data, result.report["validation"], built.budget.operations))
            self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            self.assertLess(outcomes[1][2], outcomes[0][2])
            decoded = read_glb(outcomes[1][0], target_contract="ontokin.glb/0.6")
            quantity = "max_endpoint_unit_quaternion_error"
            observed = []
            original_add = reach_conformance._CertificateBatch.add
            def observe(batch, record, width, stored_width, minima, magnitude):
                observed.append((deepcopy(record), dict(minima)))
                return original_add(batch, record, width, stored_width, minima, magnitude)
            def exact_orientation(quaternion, expected, limit, arithmetic, *, before_error=None):
                return reach_conformance._recording_orientation_comparison(
                    quaternion, expected, arithmetic, before_error=before_error)
            # A carrier is a provenance dictionary, not a frame-name string.
            # Select an actual interior record using the original independent
            # norm proof, so the forged claim is below a measured requirement
            # rather than merely below an optional sufficient enclosure.
            oracle_work = Work()
            with patch.object(ReachReference, "_recording_body_domain", return_value=False), \
                    patch.object(reach_conformance, "_recording_orientation_bound", exact_orientation), \
                    patch.object(reach_conformance._CertificateBatch, "add", observe):
                reach_conformance.validate_reach_export(outcomes[1][0], built.model,
                                                       options=options, work=oracle_work)
            self.assertEqual(oracle_work.max_operations, 100000)
            self.assertLessEqual(oracle_work.operations, 100000)
            candidates = [(record, minima[quantity]) for record, minima in observed
                          if record["left_key_index"] > 0 and minima[quantity] > 0]
            self.assertTrue(candidates, case)
            source, minimum = max(candidates, key=lambda pair: pair[1])
            self.assertGreater(minimum, 0)
            document = deepcopy(decoded.document)
            records = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
            selected = [record for record in records if record["carrier"] == source["carrier"]
                        and record["left_key_index"] == source["left_key_index"]]
            self.assertEqual(len(selected), 1)
            self.assertGreaterEqual(F(selected[0][quantity]), minimum)
            selected[0][quantity] = 0.
            self.assertLess(F(selected[0][quantity]), minimum)
            forged = replace_document(document, decoded.binary)
            self.assertEqual(read_glb(forged, target_contract="ontokin.glb/0.6").binary, decoded.binary)
            rejected = []
            for optimized in (False, True):
                mode = nullcontext() if optimized else patch.object(ReachReference, "_recording_body_domain", return_value=False)
                work = Work()
                with mode, self.assertRaises(OntoKinError) as caught:
                    reach_conformance.validate_reach_export(forged, built.model, options=options, work=work)
                rejected.append((caught.exception.diagnostic.details["export_code"],
                                 caught.exception.diagnostic.details.get("quantity")))
                self.assertLessEqual(work.operations, 100000)
            self.assertEqual(rejected[0], rejected[1])
            self.assertEqual(rejected[1][0], "OKE-E-CERTIFICATE")
            self.assertEqual(rejected[1][1], quantity)


if __name__ == "__main__":
    unittest.main()
