"""Independent body cursors preserve the original inverse child translation."""
from contextlib import nullcontext
from dataclasses import replace
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import MAX_CACHE, ReferenceError, _PoseArithmetic
from ontokin.reach_reference_plan import _LocalPose, _SourceBatchRestart, _identity_child_origin
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_phase_plan import cursor_values
from test_reach_reference_world_recording import reference_case


HEAD = "rig.head.frame"


def head_joint(reference):
    return next(joint for joint in reference.model.joints.values()
                if reference.model.sites[joint.child].owner == "rig.head")


def head_carriers(reference):
    return tuple(path + ".frame" for path in reference.model.objects if path.startswith("rig.head"))


def head_cursors(reference):
    return {key: value for key, value in cursor_values(reference).items()
            if key[3] == "recording_body_orientation" and key[4][-1] == HEAD}


class IndependentChildOriginTests(unittest.TestCase):
    def assert_encloses(self, actual, finer):
        self.assertEqual(set(actual), set(finer))
        for carrier in actual:
            for field in ("position", "orientation"):
                for cell, expected in zip(getattr(actual[carrier], field), getattr(finer[carrier], field)):
                    with self.subTest(carrier=carrier, field=field):
                        self.assertLessEqual(cell.lo, expected.lo)
                        self.assertGreaterEqual(cell.hi, expected.hi)

    def assert_original_budget(self, reference):
        work = reference.a.work
        self.assertEqual(work.max_operations, 100000)
        self.assertEqual(work.max_operand_bits, 32768)
        self.assertEqual(work.operations, sum(work.counts.values()))
        self.assertLessEqual(work.operations, work.max_operations)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)

    def test_original_p11_head_and_all_eye_offsets_enclose_finer_source(self):
        reference, _ = reference_case("P11", F(1, 2))
        fine, _ = reference_case("P11", F(1, 2), bits=256)
        context, carriers = object(), head_carriers(reference)
        self.assertGreaterEqual(len(carriers), 4)
        child = reference.model.sites[head_joint(reference).child]
        self.assertEqual(child.pose.position, (0., -.25, 0.))
        advances, original = [], reference.p._recording_body_orientation
        def observe(*args, **kwargs):
            result = original(*args, **kwargs)
            if kwargs["context"][-1] == HEAD:
                advances.append(result[1])
            return result
        with patch.object(reference.p, "_recording_body_orientation", side_effect=observe), \
                reference.recording_source_batch(context):
            for index in range(1, 13):
                time = F(index, 32)
                actual = reference.recording_pose_enclosures(carriers, time, recording_context=context)
                expected = fine.recording_pose_enclosures(carriers, time)
                self.assert_encloses(actual, expected)
            self.assertTrue(head_cursors(reference))
            self.assertEqual(next(iter(head_cursors(reference).values()))[-1], 11)
        self.assertEqual(advances, [False] + [True] * 11)
        self.assert_original_budget(reference)

    def test_all_signed_cartesian_axes_keep_nonaxial_child_translations(self):
        for axis in range(3):
            for sign in (-1., 1.):
                reference, _ = reference_case("P11", F(1, 2))
                fine, _ = reference_case("P11", F(1, 2), bits=256)
                direction = tuple(sign if index == axis else 0. for index in range(3))
                for reader in (reference, fine):
                    joint = head_joint(reader)
                    joint.axis = direction
                    child = reader.model.sites[joint.child]
                    child.pose = replace(child.pose, position=(.125, -.25, .375))
                carriers, context = head_carriers(reference), object()
                with self.subTest(axis=axis, sign=sign), reference.recording_source_batch(context):
                    for time in (F(1, 16), F(1, 8), F(3, 16)):
                        actual = reference.recording_pose_enclosures(carriers, time, recording_context=context)
                        expected = fine.recording_pose_enclosures(carriers, time)
                        self.assert_encloses(actual, expected)
                    self.assertEqual(next(iter(head_cursors(reference).values()))[1], axis)
                self.assert_original_budget(reference)

    def test_nonidentity_child_rotation_retains_original_local_angle_path(self):
        outcomes = []
        for enabled in (False, True):
            reference, _ = reference_case("P11", F(1, 2))
            joint = head_joint(reference)
            child = reference.model.sites[joint.child]
            child.pose = replace(child.pose, rotation=(1., 0., 2. ** -40, 0.))
            context, carriers = object(), head_carriers(reference)
            control = nullcontext() if enabled else patch(
                "ontokin.reach_reference_plan._identity_child_origin", return_value=False)
            with control, reference.recording_source_batch(context):
                outcomes.append([reference.recording_pose_enclosures(carriers, time, recording_context=context)
                                 for time in (F(1, 8), F(1, 4))])
                self.assertFalse(head_cursors(reference))
                self.assertTrue(any(key[3] == "recording_sincos" for key in cursor_values(reference)))
        self.assertEqual(outcomes[0], outcomes[1])

    def test_optional_origin_admission_requires_native_finite_identity_components(self):
        class ForeignFloat(float):
            def __eq__(self, other):
                raise AssertionError("foreign equality must not execute")
        native = _LocalPose((.125, -.25, .375), (1., 0., 0., 0.))
        self.assertTrue(_identity_child_origin(SimpleNamespace(local=native)))
        for position, rotation in (((0, 0., 0.), native.rotation),
                                   ((F(1, 8), 0., 0.), native.rotation),
                                   ((float("inf"), 0., 0.), native.rotation),
                                   ((ForeignFloat(.125), 0., 0.), native.rotation),
                                   (native.position, (ForeignFloat(1.), 0., 0., 0.)),
                                   (native.position, (1., 0., 2. ** -80, 0.)),
                                   (native.position, (-1., 0., 0., 0.)),
                                   (native.position, [1., 0., 0., 0.])):
            with self.subTest(position=position, rotation=rotation):
                self.assertFalse(_identity_child_origin(SimpleNamespace(local=_LocalPose(position, rotation))))
        self.assertFalse(_identity_child_origin(SimpleNamespace(local=SimpleNamespace(
            position=native.position, rotation=native.rotation))))

    def test_direct_requests_and_unregistered_batches_keep_original_cells(self):
        for scope in ("direct", "unregistered"):
            outcomes = []
            for enabled in (False, True):
                reference, _ = reference_case("P11", F(1, 2))
                context, carriers = object(), head_carriers(reference)
                control = nullcontext() if enabled else patch(
                    "ontokin.reach_reference_plan._identity_child_origin", return_value=False)
                batch = reference.recording_source_batch(context) if scope == "unregistered" else nullcontext()
                with control, patch("ontokin.reach_reference_plan.MAX_BATCH_RECEIPTS", 1), batch:
                    outcomes.append([reference.recording_pose_enclosures(carriers, time, recording_context=context)
                                     for time in (F(1, 8), F(1, 4))])
                    self.assertFalse(head_cursors(reference))
            with self.subTest(scope=scope):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_persistent_child_axis_and_owner_changes_reject_new_cursors(self):
        for changed in ("position", "rotation", "axis", "sites_owner"):
            reference, _ = reference_case("P11", F(1, 2))
            context, carriers = object(), head_carriers(reference)
            joint = head_joint(reference)
            with self.subTest(changed=changed), self.assertRaises(ReferenceError) as caught:
                with reference.recording_source_batch(context):
                    reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                    reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
                    self.assertTrue(head_cursors(reference))
                    if changed == "position":
                        child = reference.model.sites[joint.child]
                        child.pose = replace(child.pose, position=(1., 0., 0.))
                    elif changed == "rotation":
                        child = reference.model.sites[joint.child]
                        child.pose = replace(child.pose, rotation=(0., 0., 1., 0.))
                    elif changed == "axis":
                        joint.axis = (0., -1., 0.)
                    else:
                        reference.model.sites = dict(reference.model.sites)
            self.assertEqual(caught.exception.code, "identity")
            self.assertFalse(cursor_values(reference))
            self.assertIsNone(reference._recording_batch)

    def test_transient_child_mutation_cannot_enter_captured_inverse_translation(self):
        outcomes = []
        for mutate in (False, True):
            reference, _ = reference_case("P11", F(1, 2))
            context, carriers = object(), head_carriers(reference)
            child = reference.model.sites[head_joint(reference).child]
            original_pose = child.pose
            position, constant, changed = original_pose.position, reference.p.constant, []
            def observe(pose):
                if not mutate or type(pose) is not _LocalPose or pose.position != position:
                    return constant(pose)
                original_check = reference.a.work.external_check
                def change():
                    changed.append(True)
                    child.pose = replace(original_pose, position=(8., 9., 10.))
                    reference.a.work.external_check = original_check
                    if original_check is not None:
                        original_check()
                reference.a.work.external_check = change
                try:
                    return constant(pose)
                finally:
                    child.pose = original_pose
                    reference.a.work.external_check = original_check
            with reference.recording_source_batch(context):
                reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                with patch.object(reference.p, "constant", side_effect=observe):
                    outcomes.append(reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context))
            self.assertEqual(bool(changed), mutate)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_head_cursor_cancellation_preserves_exception_identity_and_discards_batch(self):
        for marker in (RuntimeError("cancel head recurrence"), ReferenceError("resource", "caller cancellation")):
            reference, _ = reference_case("P11", F(1, 2))
            context, carriers = object(), head_carriers(reference)
            original, armed = reference.p._recording_body_orientation, []
            def fail():
                reference.a.work.external_check = None
                raise marker
            def observe(*args, **kwargs):
                if kwargs["context"][-1] == HEAD:
                    armed.append(True)
                    reference.a.work.external_check = fail
                return original(*args, **kwargs)
            with self.subTest(marker=type(marker).__name__), self.assertRaises(type(marker)) as caught:
                with reference.recording_source_batch(context):
                    reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                    with patch.object(reference.p, "_recording_body_orientation", side_effect=observe):
                        reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
            self.assertTrue(armed)
            self.assertIs(caught.exception, marker)
            self.assertIs(reference.a.work.callback_error, marker)
            self.assertFalse(cursor_values(reference))
            self.assertIsNone(reference._recording_batch)

    def test_narrowed_domain_requires_original_complete_reader_restart(self):
        for stage in ("body", "inverse_origin"):
            reference, _ = reference_case("P11", F(1, 2))
            context, carriers = object(), head_carriers(reference)
            original, constant, narrowed = reference.p._recording_body_orientation, reference.p.constant, []
            child_position = reference.model.sites[head_joint(reference).child].pose.position
            previous_check = reference.a.work.external_check
            def narrow():
                narrowed.append(True)
                reference.a.work.max_operand_bits = 32767
                reference.a.work.external_check = previous_check
                if previous_check is not None:
                    previous_check()
            def observe(*args, **kwargs):
                if stage == "body" and kwargs["context"][-1] == HEAD and not narrowed:
                    reference.a.work.external_check = narrow
                return original(*args, **kwargs)
            def observe_constant(pose):
                if (stage == "inverse_origin" and not narrowed and type(pose) is _LocalPose
                        and pose.position == child_position):
                    reference.a.work.external_check = narrow
                return constant(pose)
            with self.subTest(stage=stage), self.assertRaises(_SourceBatchRestart) as caught:
                with reference.recording_source_batch(context) as batch:
                    reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                    with patch.object(reference.p, "_recording_body_orientation", side_effect=observe), \
                            patch.object(reference.p, "constant", side_effect=observe_constant):
                        reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
            self.assertEqual(narrowed, [True])
            self.assertIs(caught.exception, batch.restart)
            self.assertEqual(reference.a.work.max_operand_bits, 32767)
            self.assertEqual(reference.a.work.operations, sum(reference.a.work.counts.values()))
            self.assertFalse(cursor_values(reference))

    def test_64_step_reseed_and_eviction_keep_original_finite_cache(self):
        for evict in (False, True):
            reference, _ = reference_case("P11", F(1, 2))
            fine, _ = reference_case("P11", F(1, 2), bits=256)
            context = object()
            with self.subTest(evict=evict), reference.recording_source_batch(context):
                for index in range(68 if not evict else 24):
                    if evict and index == 20:
                        for item in range(MAX_CACHE):
                            reference.a.remember(("child-origin-eviction", item), F(item))
                        self.assertFalse(head_cursors(reference))
                    time = F(index + 1, 256)
                    actual = reference.recording_pose_enclosures((HEAD,), time, recording_context=context)
                    if index in (0, 1, 20, 64, 65, 67):
                        self.assert_encloses(actual, fine.recording_pose_enclosures((HEAD,), time))
                    cursor = next(iter(head_cursors(reference).values()))
                    if index == 0 or (evict and index == 20) or (not evict and index == 65):
                        self.assertEqual(cursor[-1], 0)
                    if not evict and index == 64:
                        self.assertEqual(cursor[-1], 64)
                    self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
            self.assert_original_budget(reference)

    def test_actual_p11_prefix_uses_new_head_cursor_and_preserves_supplied_bytes(self):
        outcomes, advances = [], []
        original = _PoseArithmetic._recording_body_orientation
        def observe(ops, *args, **kwargs):
            result = original(ops, *args, **kwargs)
            if kwargs["context"][-1] == HEAD:
                advances.append(result[1])
            return result
        for enabled in (False, True):
            compiler = compile_construction(source_case("P11"))
            control = nullcontext() if enabled else patch(
                "ontokin.reach_reference_plan._identity_child_origin", return_value=False)
            before = len(advances)
            with control, patch.object(_PoseArithmetic, "_recording_body_orientation", observe):
                result = export_glb(compiler.model,
                    options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                    target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertEqual(compiler.reach_work.max_operations, 100000)
            self.assertEqual(compiler.reach_work.max_operand_bits, 32768)
            self.assertEqual(bool(advances[before:]), enabled)
            if enabled:
                self.assertIn(True, advances[before:])
            outcomes.append((result.data, compiler.reach_work.operations))
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        print(f"P11 independent child-origin prefix: previous={outcomes[0][1]}, candidate={outcomes[1][1]}")


if __name__ == "__main__":
    unittest.main()
