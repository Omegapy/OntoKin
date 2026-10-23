"""Independent source plans retain cells, live receipts and bounded cursors."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import ReachExecutionWork as Work
from ontokin.reach_reference import MAX_CACHE, ReferenceError, _Arithmetic, _PoseArithmetic
from ontokin.reach_reference_plan import MAX_CURSORS, MAX_NODES
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_world_recording import reference_case


def cursor_values(reference):
    return {key: value for key, value in reference.a.cache.items()
            if key[:1] == ("reference_pose",) and
            key[3] in {"recording_body_orientation", "recording_sincos"}}


def stationary_values(reference):
    return {key: value for key, value in reference.a.cache.items()
            if key[:1] == ("reference_recording_stationary_pose",)}


def ordinary():
    return patch("ontokin.reach_reference_plan.recording_phase_poses", return_value=None)


class IndependentPhasePlanTests(unittest.TestCase):
    def assert_old_cursors(self, reference, before):
        current = cursor_values(reference)
        self.assertTrue(before)
        self.assertTrue(set(current).issubset(before))
        for key, value in current.items():
            self.assertEqual(value, before[key])
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)

    def test_cold_and_advanced_cells_equal_the_complete_original_walk(self):
        for case in ("P01", "P05", "P09", "P11", "P16", "L03"):
            outcomes = []
            for planned in (False, True):
                reference, _ = reference_case(case, F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                with nullcontext() if planned else ordinary():
                    values = [reference.recording_pose_enclosures(carriers, time, recording_context=context)
                              for time in (F(1, 16), F(1, 8), F(3, 16), F(1, 4), F(5, 16))]
                if planned:
                    self.assertIsNotNone(reference._recording_phase_plan, case)
                    self.assertLessEqual(len(reference._recording_phase_plan.nodes), MAX_NODES)
                outcomes.append(values)
            with self.subTest(case=case):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_actual_source_prefix_glb_bytes_and_validation_are_identical(self):
        for case in ("P05", "P09", "P11", "L03"):
            outcomes = []
            for planned in (False, True):
                compiler = compile_construction(source_case(case))
                with nullcontext() if planned else ordinary():
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            print(f"{case} phase-plan prefix: ordinary={outcomes[0][2]}, planned={outcomes[1][2]}")

    def test_repeated_phase_formulas_reduce_measured_work_with_identical_cells(self):
        # A two-key prefix also pays plan construction and may not amortize
        # it. Measure the intended repeated phase workload independently;
        # the complete recording probes retain every real startup cost.
        for case in ("P05", "P09", "P11", "L03"):
            outcomes = []
            for planned in (False, True):
                reference, _ = reference_case(case, F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                start = reference.a.work.operations
                with nullcontext() if planned else ordinary():
                    values = [reference.recording_pose_enclosures(carriers, F(index, 128),
                                                                  recording_context=context)
                              for index in range(32)]
                outcomes.append((values, reference.a.work.operations - start))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])
            print(f"{case} 32 independent phase keys: ordinary={outcomes[0][1]}, planned={outcomes[1][1]}")

    def test_reused_plan_rechecks_each_unique_actual_source_receipt(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
        plan = reference._recording_phase_plan
        self.assertIsNotNone(plan)
        self.assertEqual(len(plan.receipts), len({id(receipt) for receipt in plan.receipts}))
        batches, admit = [], reference._recording_admit_receipts
        def observe(receipts):
            batches.append(receipts)
            return admit(receipts)
        with patch.object(reference, "_recording_capture", side_effect=AssertionError("unchanged source recipes")), \
                patch.object(reference, "_recording_admit_receipts", side_effect=observe):
            reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
        self.assertIs(reference._recording_phase_plan, plan)
        self.assertEqual(batches, [plan.receipts])

    def test_stationary_complete_poses_use_only_the_original_bounded_cache(self):
        outcomes = []
        for planned in (False, True):
            reference, _ = reference_case("P11", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            values = []
            with nullcontext() if planned else ordinary():
                for index in range(52):
                    if index == 26:
                        for item in range(MAX_CACHE):
                            reference.a.remember(("stationary-pose-test-eviction", item), F(item))
                        self.assertFalse(stationary_values(reference))
                        self.assertFalse(cursor_values(reference))
                    values.append(reference.recording_pose_enclosures(
                        carriers, F(index, 128), recording_context=context))
                    self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
                    if planned:
                        plan = reference._recording_phase_plan
                        static = {node.path for node in plan.nodes if node.stationary}
                        memo = {key: value for key, value in stationary_values(reference).items()
                                if key[3] is plan.cache_identity}
                        self.assertTrue(memo)
                        self.assertTrue(any(node.kind == "hinge" and node.stationary for node in plan.nodes))
                        self.assertTrue(all(key[4] in static for key in memo))
                        self.assertTrue(all(not node.stationary for node in plan.nodes
                                            if node.kind == "hinge" and node.body.coordinate_rate))
            outcomes.append(values)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_stationary_lookup_keeps_callback_identity_and_live_operand_admission(self):
        for cancel in (False, True):
            reference, _ = reference_case("P11", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
            self.assertTrue(stationary_values(reference))
            lookup, changed = reference.a.lookup, []
            marker = RuntimeError("stationary memo callback")
            def inspect(key):
                if not changed and key[:1] == ("reference_recording_stationary_pose",):
                    def callback():
                        changed.append(True)
                        reference.a.work.max_operand_bits = 32767
                        reference.a.work.external_check = None
                        if cancel:
                            raise marker
                    reference.a.work.external_check = callback
                return lookup(key)
            with self.subTest(cancel=cancel), patch.object(reference.a, "lookup", side_effect=inspect):
                if cancel:
                    with self.assertRaises(RuntimeError) as caught:
                        reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
                    self.assertIs(caught.exception, marker)
                    self.assertIs(reference.a.work.callback_error, marker)
                else:
                    actual = reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
                    expected, _ = reference_case("P11", F(1, 2))
                    expected.a.work.max_operand_bits = 32767
                    with ordinary():
                        fresh = expected.recording_pose_enclosures(carriers, F(1, 4), recording_context=object())
                    self.assertEqual(actual, fresh)
                    self.assertFalse(stationary_values(reference))
                    self.assertFalse(cursor_values(reference))
            self.assertEqual(changed, [True])

    def test_y_axis_head_with_nonzero_origin_keeps_the_ordinary_local_compositions(self):
        reference, _ = reference_case("P11", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        observed, hinge = [], reference.p.hinge
        def observe(axis, coordinate, rate, **kwargs):
            if axis[1]:
                observed.append((axis, kwargs))
            return hinge(axis, coordinate, rate, **kwargs)
        with patch.object(reference.p, "hinge", side_effect=observe):
            for time in (F(1, 8), F(1, 4)):
                reference.recording_pose_enclosures(carriers, time, recording_context=context)
        plan = reference._recording_phase_plan
        head = next(node for node in plan.nodes if node.kind == "hinge" and node.axis[1])
        self.assertFalse(head.body.zero_origin)
        self.assertNotEqual(head.local.position, (0, 0, 0))
        self.assertTrue(observed)
        self.assertTrue(any(options["recording_context"] is not None for _, options in observed))
        self.assertTrue(any(key[3] == "recording_sincos" for key in cursor_values(reference)))

    def test_phase_state_side_and_selection_replace_the_single_plan(self):
        reference, _ = reference_case("L03", F(3))
        context, carriers = object(), tuple(reference.model.objects)
        previous = None
        for time, side, selected in ((F(15, 8), "after", carriers),
                                     (F(2), "before", carriers),
                                     (F(2), "after", carriers),
                                     (F(17, 8), "after", carriers[:1])):
            reference.recording_pose_enclosures(selected, time, side, recording_context=context)
            plan = reference._recording_phase_plan
            self.assertIsNotNone(plan)
            self.assertIsNot(plan, previous)
            self.assertEqual(plan.context[-1], side)
            self.assertEqual(plan.targets, tuple(path + ".frame" for path in selected))
            previous = plan

    def test_source_anchor_attachment_and_topology_mutations_rebuild_fresh_formulas(self):
        for change in ("position", "attachment", "incoming"):
            outcomes = []
            for planned in (False, True):
                reference, _ = reference_case("P09", F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                with nullcontext() if planned else ordinary():
                    reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                    previous = reference._recording_phase_plan
                    state = reference._state_at(F(1, 4), "after")
                    if change == "position":
                        state.ideal_positions["rig"] = reference.p.vector((F(1, 8), 0, 0))
                    elif change == "attachment":
                        relation = reference.model.actions["reach"].reach.elbow
                        site = reference.model.sites[reference.model.joints[relation].parent]
                        site.pose = replace(site.pose, position=(F(9, 8), 0, 0))
                    else:
                        follow = next(iter(reference.model.follows.values()))
                        follow.parent = "world"
                        # The original graph memo assumes immutable private
                        # topology. Invalidate it for this deliberate probe;
                        # the planned reader must detect the edit itself.
                        if not planned:
                            reference._incoming_graph_identity = object()
                    outcomes.append(reference.recording_pose_enclosures(carriers, F(1, 4),
                                                                          recording_context=context))
                if planned:
                    self.assertIsNot(reference._recording_phase_plan, previous)
            with self.subTest(change=change):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_late_angle_source_mutation_publishes_no_body_or_angle_cursor(self):
        reference, _ = reference_case("P11", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
        before, remember, changed = cursor_values(reference), reference.a.remember, []
        plan = reference._recording_phase_plan
        head = next(node for node in plan.nodes if node.kind == "hinge" and node.axis[1])
        joint = reference.model.joints[head.relation]
        def publish(key, value, **kwargs):
            if key[:1] == ("reference_pose",) and key[3] == "recording_sincos":
                def mutate():
                    changed.append(True)
                    joint.axis = (1., 0., 0.)
                    reference.a.work.external_check = None
                reference.a.work.external_check = mutate
            return remember(key, value, **kwargs)
        with patch.object(reference.a, "remember", side_effect=publish), self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
        self.assertEqual(changed, [True])
        self.assertEqual(caught.exception.code, "identity")
        self.assert_old_cursors(reference, before)

    def test_callback_exceptions_keep_identity_at_body_and_angle_staging(self):
        for kind, case in (("recording_body_orientation", "P09"), ("recording_sincos", "P11")):
            for marker in (RuntimeError("stop pending cursor"), ReferenceError("resource", "caller marker")):
                reference, _ = reference_case(case, F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                before, remember, armed = cursor_values(reference), reference.a.remember, []
                def publish(key, value, **kwargs):
                    if key[:1] == ("reference_pose",) and key[3] == kind:
                        def cancel():
                            armed.append(True)
                            reference.a.work.max_operand_bits = 64
                            raise marker
                        reference.a.work.external_check = cancel
                    return remember(key, value, **kwargs)
                with self.subTest(kind=kind, marker=type(marker).__name__), \
                        patch.object(reference.a, "remember", side_effect=publish), \
                        self.assertRaises(type(marker)) as caught:
                    reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
                self.assertEqual(armed, [True])
                self.assertIs(caught.exception, marker)
                self.assertIs(reference.a.work.callback_error, marker)
                self.assert_old_cursors(reference, before)

    def test_narrowed_pending_domain_uses_the_complete_ordinary_current_domain(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
        remember, narrowed = reference.a.remember, []
        def publish(key, value, **kwargs):
            if not narrowed and key[:1] == ("reference_pose",) and key[3] == "recording_body_orientation":
                def narrow():
                    narrowed.append(True)
                    reference.a.work.max_operand_bits = 32767
                    reference.a.work.external_check = None
                reference.a.work.external_check = narrow
            return remember(key, value, **kwargs)
        with patch.object(reference.a, "remember", side_effect=publish):
            actual = reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
        expected, _ = reference_case("P09", F(1, 2))
        expected.a.work.max_operand_bits = 32767
        with ordinary():
            values = expected.recording_pose_enclosures(carriers, F(1, 4), recording_context=object())
        self.assertEqual(narrowed, [True])
        self.assertEqual(actual, values)
        self.assertFalse(cursor_values(reference))

    def test_eviction_has_no_hidden_numeric_cursor_and_reseeds_exact_original_cells(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        for time in (F(1, 16), F(1, 8)):
            reference.recording_pose_enclosures(carriers, time, recording_context=context)
        plan = reference._recording_phase_plan
        for index in range(MAX_CACHE):
            reference.a.remember(("phase-plan-test-eviction", index), F(index))
        self.assertFalse(cursor_values(reference))
        actual = reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
        self.assertIs(reference._recording_phase_plan, plan)
        expected, _ = reference_case("P09", F(1, 2))
        with ordinary():
            values = expected.recording_pose_enclosures(carriers, F(1, 4), recording_context=object())
        self.assertEqual(actual, values)
        self.assertTrue(all(value[-1] == 0 for value in cursor_values(reference).values()))
        self.assertLessEqual(len(cursor_values(reference)), MAX_CURSORS)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)

    def test_reentrant_same_context_cannot_overwrite_the_nested_completed_cursors(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
        remember, nested = reference.a.remember, []
        def publish(key, value, **kwargs):
            if not nested and key[:1] == ("reference_pose",) and key[3] == "recording_body_orientation":
                nested.append(None)
                with patch.object(reference.a, "remember", side_effect=remember):
                    nested[0] = reference.recording_pose_enclosures(carriers, F(3, 8), recording_context=context)
            return remember(key, value, **kwargs)
        with patch.object(reference.a, "remember", side_effect=publish), self.assertRaises(ReferenceError) as caught:
            reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
        self.assertEqual(caught.exception.code, "identity")
        self.assertTrue(nested[0])
        self.assertTrue(all(value[3] == F(3, 8) for key, value in cursor_values(reference).items()
                            if key[3] == "recording_body_orientation"))

    def test_reseed_after_64_steps_retains_exact_cold_seed_cells(self):
        reference, _ = reference_case("P09", F(1, 2))
        carriers, context = tuple(reference.model.objects), object()
        for index in range(66):
            actual = reference.recording_pose_enclosures(carriers, F(index, 256), recording_context=context)
        self.assertTrue(all(value[-1] == 0 for value in cursor_values(reference).values()))
        expected, _ = reference_case("P09", F(1, 2))
        with ordinary():
            cold = expected.recording_pose_enclosures(carriers, F(65, 256), recording_context=object())
        self.assertEqual(actual, cold)
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        self.assertEqual(reference.a.work.operations, sum(reference.a.work.counts.values()))

    def test_observations_and_dynamic_roots_do_not_enter_phase_plan_arithmetic(self):
        reference, _ = reference_case("P09", F(1, 2))
        with patch("ontokin.reach_reference_plan.recording_phase_poses", side_effect=AssertionError("recording only")):
            reference.pose_enclosure("rig.tool", F(1, 8))
            reference.recording_pose_enclosures(("rig.tool",), F(1, 8))
        reference, _ = reference_case("P16", F(3))
        with patch("ontokin.reach_reference_plan._build", side_effect=AssertionError("unsupported dynamic root")):
            reference.recording_pose_enclosures(tuple(reference.model.objects), F(9, 4), recording_context=object())
        self.assertIsNone(reference._recording_phase_plan)

    def test_replaced_whole_model_or_source_maps_rebuild_between_requests(self):
        for replaced in ("model", "objects", "sites", "joints", "follows", "actions"):
            reference, _ = reference_case("P09", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
            previous = reference._recording_phase_plan
            if replaced == "model":
                reference.model = deepcopy(reference.model)
            else:
                setattr(reference.model, replaced, deepcopy(getattr(reference.model, replaced)))
            with self.subTest(replaced=replaced):
                reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
                self.assertIsNot(reference._recording_phase_plan, previous)
                self.assertTrue(reference._recording_phase_plan.owned_by(reference))

    def test_model_or_map_replacement_during_arithmetic_rejects_all_pending_cursors(self):
        for replaced in ("model", "objects", "sites", "joints", "follows", "actions"):
            reference, _ = reference_case("P09", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
            before, remember, changed = cursor_values(reference), reference.a.remember, []
            def publish(key, value, **kwargs):
                if not changed and key[:1] == ("reference_pose",) and key[3] == "recording_body_orientation":
                    changed.append(True)
                    if replaced == "model":
                        reference.model = deepcopy(reference.model)
                    else:
                        setattr(reference.model, replaced, deepcopy(getattr(reference.model, replaced)))
                return remember(key, value, **kwargs)
            with self.subTest(replaced=replaced), patch.object(reference.a, "remember", side_effect=publish), \
                    self.assertRaises(ReferenceError) as caught:
                reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(changed, [True])
            self.assert_old_cursors(reference, before)

    def test_replaced_arithmetic_owner_cannot_publish_pending_results(self):
        for replaced in ("arithmetic", "pose_arithmetic", "pose_owner"):
            reference, _ = reference_case("P09", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
            original_a, original_p = reference.a, reference.p
            before, remember, changed = cursor_values(reference), reference.a.remember, []
            replacement = _Arithmetic(work=Work())
            def publish(key, value, **kwargs):
                if not changed and key[:1] == ("reference_pose",) and key[3] == "recording_body_orientation":
                    changed.append(True)
                    if replaced == "arithmetic":
                        reference.a = replacement
                    elif replaced == "pose_arithmetic":
                        reference.p = _PoseArithmetic(original_a)
                    else:
                        reference.p.a = replacement
                return remember(key, value, **kwargs)
            with self.subTest(replaced=replaced), patch.object(original_a, "remember", side_effect=publish), \
                    self.assertRaises(ReferenceError) as caught:
                reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
            self.assertEqual(caught.exception.code, "identity")
            self.assertEqual(changed, [True])
            self.assertEqual(replacement.work.operations, 0)
            reference.a, reference.p = original_a, original_p
            original_p.a = original_a
            self.assert_old_cursors(reference, before)

    def test_prescribed_translation_uses_captured_source_during_a_restored_mutation(self):
        outcomes = []
        for mutate in (False, True):
            reference, _ = reference_case("P05", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
            translation = reference._prescribed_root_translation
            action = reference.model.actions["travel"]
            original_vector, changed = action.vector, []
            def observe(*args, **kwargs):
                def change():
                    changed.append(True)
                    action.vector = (8., 0., 0.)
                    reference.a.work.external_check = None
                if mutate:
                    reference.a.work.external_check = change
                try:
                    return translation(*args, **kwargs)
                finally:
                    action.vector = original_vector
                    reference.a.work.external_check = None
            with patch.object(reference, "_prescribed_root_translation", side_effect=observe):
                outcomes.append(reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context))
            self.assertEqual(bool(changed), mutate)
            self.assertIsNotNone(reference._recording_phase_plan)
        self.assertEqual(outcomes[0], outcomes[1])


if __name__ == "__main__":
    unittest.main()
