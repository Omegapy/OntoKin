"""Large exact translations require an independently proved identity parent."""
from contextlib import nullcontext
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.reach_reference import Interval, MAX_CACHE, ReachReference, ReferenceError
from ontokin.reach_reference_center import (
    _CenteredNode, _CenteredPose, _ChangedDomain, _Guard, _offset,
)
import test_reach_reference_centered_recording as centered_tests
from test_reach_reference_centered_recording import (
    G, R, UNIT, ZERO, harness, point,
)
from test_reach_reference_source_batch import prefix
from test_reach_reference_world_recording import reference_case


LEFT = 'rig.arms["left"]'


def mount(reference, child=LEFT):
    return next(follow for follow in reference.model.follows.values() if follow.child == child)


def moving_p11(reference):
    # These are the actual changing carriers after the first ordinary key.
    # All their source ancestors are still selected by the independent plan.
    return tuple(path for path in reference.model.objects
                 if path.startswith("rig.head") or path.startswith("rig.arms[") and path.endswith(".forearm"))


class CenteredIdentityOffsetTests(unittest.TestCase):
    def test_large_identity_offset_is_exact_and_retains_the_parent_position_radius(self):
        reference, plan, batch = harness()
        for vector in ((F(64), F(0), F(0)), (F(-16), F(32), F(-16)),
                       (F(1) + G, F(0), F(0))):
            guard = _Guard(reference, plan, batch)
            parent = _CenteredPose(ZERO, UNIT, 4 * R, F(0), None)
            frozen = guard.pose(parent)
            result, uncertain = _offset(frozen, guard.vector(vector), guard, identity_only=True)
            self.assertEqual(result, vector)
            self.assertFalse(uncertain)
            self.assertEqual(frozen.position_radius, 4 * R)

    def test_identity_center_with_radius_negative_identity_and_nonidentity_are_rejected(self):
        for rotation, radius, axis in ((UNIT, R, None),
                                       ((F(-1), F(0), F(0), F(0)), F(0), None),
                                       ((F(0), F(0), F(0), F(1)), F(0), 2)):
            reference, plan, batch = harness()
            guard = _Guard(reference, plan, batch)
            parent = guard.pose(_CenteredPose(ZERO, rotation, F(0), radius, axis))
            with self.subTest(rotation=rotation, radius=radius), self.assertRaises(_ChangedDomain):
                _offset(parent, (F(1) + G, F(0), F(0)), guard, identity_only=True)

    def test_actual_p11_pending_carriers_activate_and_enclose_finer_source_observations(self):
        reference, _ = reference_case("P11", F(1, 2))
        finer, _ = reference_case("P11", F(1, 2), bits=256)
        context, carriers = object(), moving_p11(reference)
        self.assertEqual(len(carriers), 6)
        with reference.recording_source_batch(context):
            # The nonidentity static leg rotations remain outside this domain.
            self.assertIsNone(reference._recording_centered_poses(tuple(reference.model.objects), F(0),
                                                                  recording_context=context))
            for index in range(12):
                clock = F(index, 64)
                actual = reference._recording_centered_poses(carriers, clock, recording_context=context)
                self.assertIsNotNone(actual)
                prepared = reference._recording_phase_plan
                large = {node.path for node, recipe in zip(prepared.nodes, prepared.centered)
                         if recipe.identity_offset}
                self.assertEqual(large, {LEFT + ".frame", 'rig.arms["right"].frame'})
                if index not in (0, 1, 5, 11):
                    continue
                expected = finer.recording_pose_enclosures(carriers, clock)
                ordinary = reference.recording_pose_enclosures(carriers, clock, recording_context=context)
                for carrier, pose in actual.items():
                    with self.subTest(index=index, carrier=carrier):
                        self.assertTrue(all(type(cell) is Interval for cell in ordinary[carrier].position))
                        if carrier == "rig.head.frame":
                            # The unchanged independent source identity is
                            # rootY=5/4, neckY=1, inverse baseY=1/4, hingeY.
                            self.assertEqual(pose.position, (F(0), F(5, 2), F(0)))
                            self.assertEqual(pose.position_radius, 0)
                            self.assertTrue(all(cell.contains(value) for cell, value
                                                in zip(expected[carrier].position, pose.position)))
                        else:
                            centered_tests.CenteredKernelTests.assert_ball_contains(self, pose.position,
                                pose.position_radius, expected[carrier].position)
                        centered_tests.CenteredKernelTests.assert_ball_contains(self, pose.orientation,
                            pose.orientation_radius, expected[carrier].orientation)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        self.assertEqual(reference.a.work.max_operations, 100000)

    def test_source_prefix_bytes_reports_and_actual_endpoint_activation(self):
        outcomes = []
        for enabled in (False, True):
            scope = nullcontext() if enabled else patch.object(ReachReference, "_recording_centered_poses", return_value=None)
            with scope:
                result, compiler = prefix("P11")
            self.assertEqual(result.report["validation"]["status"], "passed")
            outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations,
                             compiler.reach_work.counts.get("independent_centered_endpoint_domain", 0)))
        self.assertEqual(outcomes[0][:2], outcomes[1][:2])
        self.assertEqual(outcomes[0][3], 0)
        self.assertGreater(outcomes[1][3], 0)
        self.assertLess(outcomes[1][2], outcomes[0][2])
        print(f"P11 exact-identity offset prefix: ordinary={outcomes[0][2]}, centered={outcomes[1][2]}")

    def test_exact_parent_local_l1_boundary_and_nongrid_offsets_keep_original_fallback(self):
        for vector, admitted in (((F(1) + G, F(0), F(0)), True),
                                 ((F(-16), F(32), F(-16)), True),
                                 ((F(64), F(0), F(0)), True),
                                 ((F(64), G, F(0)), False),
                                 ((F(4, 3), F(0), F(0)), False)):
            reference, _ = reference_case("P11", F(1, 2))
            follow = mount(reference)
            follow.offset = replace(follow.offset, position=vector)
            context, work = object(), reference.a.work
            with self.subTest(vector=vector), reference.recording_source_batch(context):
                actual = reference._recording_centered_poses((LEFT,), F(1, 8), recording_context=context)
                self.assertEqual(actual is not None, admitted)
                ordinary = reference.recording_pose_enclosures((LEFT,), F(1, 8), recording_context=context)
                self.assertTrue(all(type(cell) is Interval for cell in ordinary[LEFT + ".frame"].position))
                if admitted:
                    expected = (vector[0], vector[1] + F(5, 4), vector[2])
                    self.assertEqual(actual[LEFT + ".frame"].position, expected)
                    self.assertEqual(actual[LEFT + ".frame"].position_radius, 0)
                    self.assertTrue(all(cell.contains(value) for cell, value
                                        in zip(ordinary[LEFT + ".frame"].position, expected)))
                self.assertIs(reference.a.work, work)

    def test_unchanged_total_extent_accepts_192_and_rejects_192_plus_one_grid_step(self):
        for tip, admitted in ((G, True), (2 * G, False)):
            reference, _ = reference_case("P11", F(1, 2))
            state = reference._state_at(F(1, 8), "after")
            state.ideal_positions["rig"] = tuple(map(point, (F(64), 0, 0)))
            follow = mount(reference)
            follow.offset = replace(follow.offset, position=(F(64), F(0), F(0)))
            pivot = reference.model.sites[LEFT + ".pivot"]
            pivot.pose = replace(pivot.pose, position=(F(64) - G, F(0), F(0)))
            site = reference.model.sites[LEFT + ".upper.hinge_tip"]
            site.pose = replace(site.pose, position=(tip, F(0), F(0)))
            context, target = object(), site.path + ".frame"
            with self.subTest(tip=tip), reference.recording_source_batch(context):
                actual = reference._recording_centered_poses((target,), F(1, 8), recording_context=context)
                self.assertEqual(actual is not None, admitted)
                ordinary = reference.recording_pose_enclosures((target,), F(1, 8), recording_context=context)
                exact = F(192) if admitted else F(192) + G
                self.assertTrue(ordinary[target].position[0].contains(exact))
                if admitted:
                    self.assertEqual(actual[target].position, (exact, F(0), F(0)))
                    self.assertEqual(actual[target].position_radius, 0)

    def test_extent_arithmetic_latches_narrowing_and_preserves_callback_cancellation(self):
        for cancel in (False, True):
            reference, _ = reference_case("P11", F(1, 2))
            follow = mount(reference)
            follow.offset = replace(follow.offset, position=(F(-16), F(32), F(-16)))
            original, original_check = _Guard.exact, reference.a.work.external_check
            armed, fired = [], []
            marker = RuntimeError("cancel the new source-extent addition")
            def exact(guard, first, last, operation):
                if operation == "add" and first == F(5, 4) and last == 64:
                    armed.append(True)
                return original(guard, first, last, operation)
            def check():
                original_check()
                if armed and not fired:
                    fired.append(True)
                    if cancel:
                        raise marker
                    reference.a.work.max_operand_bits -= 1
                elif fired:
                    # This later restoration must not revive the optional
                    # attempt; its first departure already invalidated it.
                    reference.a.work.max_operand_bits = 32768
                    fired.append(False)
            reference.a.work.external_check = check
            context, before = object(), reference.a.work.operations
            with self.subTest(cancel=cancel):
                if cancel:
                    with self.assertRaises(RuntimeError) as caught:
                        with reference.recording_source_batch(context), patch.object(_Guard, "exact", exact):
                            reference._recording_centered_poses((LEFT,), F(1, 8), recording_context=context)
                    self.assertIs(caught.exception, marker)
                else:
                    with reference.recording_source_batch(context), patch.object(_Guard, "exact", exact):
                        self.assertIsNone(reference._recording_centered_poses((LEFT,), F(1, 8),
                                                                              recording_context=context))
                    self.assertEqual(reference.a.work.max_operand_bits, 32767)
                    reference.a.work.max_operand_bits = 32768
                self.assertEqual(fired, [True])
                self.assertGreater(reference.a.work.operations, before)
                self.assertEqual(reference.a.work.max_operations, 100000)

    def test_identity_hinge_lineage_and_stationary_nonzero_parent_are_distinguished(self):
        for angle, admitted in ((F(0), True), (F(1, 8), False)):
            reference, _ = reference_case("P11", F(1, 2))
            state = reference._state_at(F(1, 8), "after")
            joint = next(joint for joint in reference.model.joints.values()
                         if reference.model.sites[joint.child].owner == LEFT + ".upper")
            # A constant active coordinate is stationary, but an identity
            # requires both independent affine endpoints to be exactly zero.
            owner = state.claims[joint.path, "coordinate"]
            active = state.actions[owner]
            active.initial = (angle, active.initial[1])
            active.ideal_initial = (angle, active.ideal_initial[1])
            active.targets = (angle, active.targets[1])
            site = reference.model.sites[LEFT + ".upper.hinge_tip"]
            site.pose = replace(site.pose, position=(F(1) + G, F(0), F(0)))
            context, target = object(), site.path + ".frame"
            with self.subTest(angle=angle), reference.recording_source_batch(context):
                actual = reference._recording_centered_poses((target,), F(1, 8), recording_context=context)
                self.assertEqual(actual is not None, admitted)
                ordinary = reference.recording_pose_enclosures((target,), F(1, 8), recording_context=context)
                self.assertTrue(ordinary)
                if admitted:
                    self.assertEqual(actual[target].orientation, UNIT)
                    self.assertEqual(actual[target].orientation_radius, 0)

    def test_moving_and_paused_nonzero_hinges_do_not_admit_large_eye_offsets(self):
        for paused in (False, True):
            reference, _ = reference_case("P11", F(1, 2))
            state = reference._state_at(F(1, 8), "after")
            joint = next(joint for joint in reference.model.joints.values()
                         if reference.model.sites[joint.child].owner == "rig.head")
            owner = state.claims[joint.path, "coordinate"]
            if paused:
                state.actions[owner].status = "paused"
                state.actions[owner].elapsed = F(1, 8)
            follow = next(follow for follow in reference.model.follows.values()
                          if follow.child.startswith("rig.head.eyes"))
            follow.offset = replace(follow.offset, position=(F(1) + G, F(0), F(0)))
            context = object()
            with self.subTest(paused=paused), reference.recording_source_batch(context):
                self.assertIsNone(reference._recording_centered_poses((follow.child,), F(1, 8),
                                                                      recording_context=context))
                self.assertTrue(reference.recording_pose_enclosures((follow.child,), F(1, 8),
                                                                    recording_context=context))

    def test_cancelling_source_rates_do_not_establish_identity_lineage(self):
        reference, _ = reference_case("P09", F(1, 2))
        state = reference._state_at(F(1, 8), "after")
        # A deliberate unit-fixture change to the captured independent law:
        # both source coordinates move, while their world rates cancel.
        active = state.actions["reach"]
        active.ideal_initial = (F(0), F(0))
        active.targets = (F(1), F(-1))
        follow = mount(reference, "rig.tool")
        follow.offset = replace(follow.offset, position=(F(1) + G, F(0), F(0)))
        context = object()
        with reference.recording_source_batch(context):
            self.assertIsNone(reference._recording_centered_poses(("rig.tool",), F(1, 8),
                                                                  recording_context=context))
            node = next(node for node in reference._recording_phase_plan.nodes
                        if node.path == "rig.arm.forearm.frame")
            self.assertEqual(node.body.rate, 0)
            self.assertTrue(node.body.moving)
            self.assertFalse(node.body.identity_relative)
            self.assertTrue(reference.recording_pose_enclosures(("rig.tool",), F(1, 8),
                                                                recording_context=context))

    def test_changed_typed_recipe_flag_rejects_without_borrowing_a_stationary_result(self):
        for changed in (0, True, 2):
            reference, _ = reference_case("P11", F(1, 2))
            context = object()
            with self.subTest(changed=changed), self.assertRaises(ReferenceError) as caught:
                with reference.recording_source_batch(context):
                    self.assertIsNotNone(reference._recording_centered_poses((LEFT,), F(1, 8),
                                                                           recording_context=context))
                    plan = reference._recording_phase_plan
                    recipe = next(recipe for node, recipe in zip(plan.nodes, plan.centered)
                                  if node.path == LEFT + ".frame")
                    self.assertEqual(recipe.identity_offset, 1)
                    object.__setattr__(recipe, "identity_offset", changed)
                    reference._recording_centered_poses((LEFT,), F(1, 4), recording_context=context)
            self.assertEqual(caught.exception.code, "identity")
            self.assertFalse(any(key[0] == "reference_centered_stationary_pose" for key in reference.a.cache))

    def test_parent_radius_and_center_mutation_after_freezing_cannot_hide_in_a_warm_cache(self):
        for changed in ("radius", "center"):
            reference, _ = reference_case("P11", F(1, 2))
            context, armed, fired = object(), [], []
            original = _Guard.pose
            original_check = reference.a.work.external_check
            def freeze(guard, value):
                result = original(guard, value)
                if any(type(record) is _CenteredNode and record.identity_offset == 1
                       for record, *_ in guard.records):
                    armed.append(value)
                return result
            def mutate():
                original_check()
                if armed and not fired:
                    pose = armed.pop()
                    fired.append(pose)
                    if changed == "radius":
                        object.__setattr__(pose, "orientation_radius", R)
                    else:
                        object.__setattr__(pose.orientation[0], "_numerator", 2)
            with self.subTest(changed=changed), self.assertRaises(ReferenceError) as caught:
                with reference.recording_source_batch(context):
                    self.assertIsNotNone(reference._recording_centered_poses((LEFT,), F(1, 8),
                                                                           recording_context=context))
                    reference.a.work.external_check = mutate
                    # New guards capture this callback before any pose is
                    # frozen. The mutation occurs at the child's next tick.
                    with patch.object(_Guard, "pose", freeze):
                        reference._recording_centered_poses((LEFT,), F(1, 4), recording_context=context)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(len(fired), 1)
            self.assertIsNone(reference._recording_batch)

    def test_warm_stationary_identity_offsets_still_require_final_live_source_admission(self):
        reference, _ = reference_case("P11", F(1, 2))
        context, saved = object(), {}
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context) as batch:
                first = reference._recording_centered_poses((LEFT,), F(1, 8), recording_context=context)
                last = reference._recording_centered_poses((LEFT,), F(1, 4), recording_context=context)
                self.assertEqual(first, last)
                self.assertTrue(batch.cursors)
                saved.update(batch.cursors)
                follow = mount(reference)
                follow.offset = replace(follow.offset, position=(F(-1, 2), F(3, 4), F(0)))
        self.assertEqual(caught.exception.code, "identity")
        self.assertTrue(all(reference.a.cache.get(key) is not value for key, value in saved.items()))
        self.assertIsNone(reference._recording_batch)


if __name__ == "__main__":
    unittest.main()
