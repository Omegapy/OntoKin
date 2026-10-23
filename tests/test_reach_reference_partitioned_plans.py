"""A released source ancestry cannot disable unrelated prescribed interval plans."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_reference_plan as plans
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import Interval, MAX_CACHE, ReferenceError
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_phase import changed
from test_reach_reference_phase_plan import cursor_values, ordinary, stationary_values
from test_reach_reference_world_recording import reference_case


def original_dynamic_reader():
    """Preserve the preceding global dynamic-state refusal as a control."""
    original = plans.recording_phase_poses

    def read(reference, time, state, targets, context):
        if any(mode == "dynamic" for mode in state.modes.values()):
            return None
        return original(reference, time, state, targets, context)

    return patch.object(plans, "recording_phase_poses", side_effect=read)


def sample(reference, context, time=F(9, 4), carriers=None, side="after"):
    return reference.recording_pose_enclosures(
        tuple(reference.model.objects) if carriers is None else carriers,
        time, side, recording_context=context)


class IndependentPartitionedPlanTests(unittest.TestCase):
    def assert_limits(self, reference, batch):
        self.assertEqual(reference.a.work.max_operations, 100000)
        self.assertEqual(reference.a.work.max_operand_bits, 32768)
        self.assertEqual(reference.a.work.max_cache_entries, 256)
        self.assertEqual(reference.a.work.operations, sum(reference.a.work.counts.values()))
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        self.assertLessEqual(len(batch.plans), plans.MAX_BATCH_PLANS)
        self.assertLessEqual(len(batch.receipts), plans.MAX_BATCH_RECEIPTS)
        self.assertLessEqual(len(batch.cursors), MAX_CACHE)

    def test_original_release_sides_and_later_phases_keep_all_exact_cells(self):
        outcomes = []
        for partitioned in (False, True):
            reference, _ = reference_case("P16", F(4))
            context, values = object(), []
            with nullcontext() if partitioned else original_dynamic_reader():
                with reference.recording_source_batch(context) as batch:
                    for time, side in ((F(2), "before"), (F(2), "after"),
                                       (F(17, 8), "after"), (F(5, 2), "after"),
                                       (F(3), "before"), (F(3), "after"),
                                       (F(25, 8), "after"), (F(7, 2), "after"),
                                       (F(4), "after")):
                        result = sample(reference, context, time, side=side)
                        self.assertEqual(tuple(result), tuple(path + ".frame" for path in reference.model.objects))
                        values.append(result)
                        if partitioned and not (time == 2 and side == "before"):
                            plan = reference._recording_phase_plan
                            self.assertEqual(plan.remaining, ("payload.frame",))
                            self.assertNotIn("payload.frame", {node.path for node in plan.nodes})
                            self.assertTrue(all(key[4] != "payload.frame"
                                                for key in stationary_values(reference)))
                    self.assert_limits(reference, batch)
            outcomes.append(values)
            self.assertIsNone(reference._recording_batch)
            self.assertIsNone(reference.a._recording_after_tick)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_repeated_original_postrelease_keys_reduce_work_without_changing_cells(self):
        outcomes = []
        for partitioned in (False, True):
            reference, _ = reference_case("P16", F(3))
            context = object()
            start = reference.a.work.operations
            with nullcontext() if partitioned else original_dynamic_reader():
                with reference.recording_source_batch(context) as batch:
                    values = [sample(reference, context, F(9, 4) + F(index, 128))
                              for index in range(32)]
                    self.assert_limits(reference, batch)
            outcomes.append((values, reference.a.work.operations - start))
        self.assertEqual(outcomes[0][0], outcomes[1][0])
        self.assertLess(outcomes[1][1], outcomes[0][1])
        print(f"P16 32 original postrelease keys: ordinary={outcomes[0][1]}, partitioned={outcomes[1][1]}")

    def test_stationary_full_plan_and_dynamic_only_selection_keep_separate_source_roles(self):
        reference, _ = reference_case("P16", F(4))
        context, carriers = object(), tuple(reference.model.objects)
        with reference.recording_source_batch(context) as batch:
            sample(reference, context, F(49, 16))
            full = reference._recording_phase_plan
            with patch.object(plans, "recording_stationary_frames", return_value=None):
                expected = reference.recording_stationary_frames(carriers, F(49, 16), F(25, 8))
            self.assertNotIn("payload.frame", expected)
            self.assertEqual(expected, frozenset(path + ".frame" for path in carriers if path != "payload"))
            sample(reference, context, F(25, 8), ("payload",))
            pruned = reference._recording_phase_plan
            self.assertIsNot(pruned, full)
            self.assertEqual(pruned.remaining, ("payload.frame",))
            self.assertEqual(pruned.nodes, ())
            capture, dynamic_reads = reference._recording_capture, []
            def only_dynamic(read):
                def checked():
                    values = read()
                    # This is the original ordinary root admission. The
                    # registered prescribed graph must not be captured again.
                    self.assertEqual(values[:2], ("root", "payload"))
                    dynamic_reads.append(values[2])
                    return values
                return capture(checked)
            with patch.object(reference, "_recording_capture", side_effect=only_dynamic):
                for time in (F(51, 16), F(13, 4)):
                    sample(reference, context, time, ("payload",))
            self.assertEqual(dynamic_reads, ["dynamic", "dynamic"])
            with patch.object(reference, "_incoming", side_effect=AssertionError("registered source flags")):
                self.assertEqual(reference.recording_stationary_frames(carriers, F(25, 8), F(13, 4)), expected)
            self.assertEqual(len(batch.plans), 2)
            self.assert_limits(reference, batch)

    def test_original_cache_eviction_keeps_complete_values_and_no_second_pose_table(self):
        outcomes = []
        for partitioned in (False, True):
            reference, _ = reference_case("P16", F(3))
            context, values = object(), []
            with nullcontext() if partitioned else original_dynamic_reader():
                with reference.recording_source_batch(context) as batch:
                    for index in range(8):
                        if index == 4:
                            for item in range(MAX_CACHE):
                                reference.a.remember(("partition-eviction", item), F(item))
                            self.assertFalse(cursor_values(reference))
                        values.append(sample(reference, context, F(17, 8) + F(index, 64)))
                        self.assert_limits(reference, batch)
                        if partitioned:
                            plan = reference._recording_phase_plan
                            self.assertFalse(any(isinstance(value, dict) for value in vars(plan).values()))
            outcomes.append(values)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_original_64_step_body_reseed_remains_in_the_existing_cache(self):
        reference, _ = reference_case("P16", F(3))
        context = object()
        with reference.recording_source_batch(context) as batch:
            for index in range(66):
                result = sample(reference, context, F(2) + F(index, 512))
            self.assertTrue(cursor_values(reference))
            self.assertTrue(all(value[-1] == 0 for value in cursor_values(reference).values()))
            self.assert_limits(reference, batch)
        expected, _ = reference_case("P16", F(3))
        with ordinary():
            cold = sample(expected, object(), F(2) + F(65, 512))
        self.assertEqual(result, cold)

    def test_context_free_nested_centered_and_initial_narrow_domains_keep_original_paths(self):
        for kind in ("context_free", "nested", "centered", "narrow"):
            reference, _ = reference_case("P16", F(3))
            context, carriers = object(), tuple(reference.model.objects)
            if kind == "narrow":
                reference.a.work.max_operand_bits = 32767
            scope = nullcontext(None) if kind == "context_free" else reference.recording_source_batch(context)
            with self.subTest(kind=kind), scope as batch:
                with patch.object(plans, "_build", side_effect=AssertionError("original dynamic path")):
                    if kind == "centered":
                        self.assertIsNone(reference._recording_centered_poses(carriers, F(9, 4),
                                                                            recording_context=context))
                    else:
                        if kind == "nested":
                            batch.depth += 1
                        try:
                            result = sample(reference, context)
                        finally:
                            if kind == "nested":
                                batch.depth -= 1
                        self.assertEqual(len(result), len(carriers))
                if batch is not None:
                    self.assertFalse(batch.plans)

    def test_optional_node_cursor_target_and_batch_limits_do_not_return_partial_maps(self):
        expected, _ = reference_case("P16", F(3))
        with ordinary():
            result = sample(expected, object())
        for name, limit in (("MAX_TARGETS", 1), ("MAX_NODES", 1), ("MAX_CURSORS", 0),
                            ("MAX_BATCH_PLANS", 0), ("MAX_BATCH_RECEIPTS", 1)):
            reference, _ = reference_case("P16", F(3))
            context = object()
            with self.subTest(bound=name), patch.object(plans, name, limit):
                with reference.recording_source_batch(context) as batch:
                    self.assertEqual(sample(reference, context), result)
                    self.assertFalse(batch.plans)
                    self.assertFalse(batch.cursors)
            self.assertEqual(reference.a.work.max_operations, 100000)
            self.assertLessEqual(len(reference.a.cache), MAX_CACHE)

    def test_dynamic_site_and_follow_descendants_stay_in_the_ordinary_ancestry(self):
        outcomes = []
        for partitioned in (False, True):
            reference, _ = reference_case("P16", F(3))
            # A private source variant places an existing independent visual
            # carrier under the released payload. Both controls use exactly
            # this graph; the original fixture files are unchanged.
            reference.model.follows["rig.column_mount"].parent = "payload.origin.frame"
            reference._incoming_graph_identity = object()
            context = object()
            carriers = (*reference.model.objects, "payload.origin")
            with nullcontext() if partitioned else original_dynamic_reader():
                with reference.recording_source_batch(context) as batch:
                    values = [sample(reference, context, time, carriers)
                              for time in (F(9, 4), F(5, 2))]
                    if partitioned:
                        plan = reference._recording_phase_plan
                        self.assertEqual(set(plan.remaining),
                                         {"payload.frame", "payload.origin.frame", "rig.column.frame"})
                        self.assertTrue(set(plan.remaining).isdisjoint(node.path for node in plan.nodes))
                        self.assertTrue(any(receipt.values[0] == "partition_dynamic_site"
                                            for receipt in plan.receipts))
                    self.assert_limits(reference, batch)
            outcomes.append(values)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_unused_global_relation_changes_still_reject_the_complete_batch(self):
        reference, _ = reference_case("P16", F(3))
        context = object()
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context):
                sample(reference, context, carriers=("rig", "payload"))
                plan = reference._recording_phase_plan
                self.assertNotIn("rig.column.frame", {node.path for node in plan.nodes})
                reference.model.follows["rig.column_mount"].parent = "world"
        self.assertEqual(caught.exception.code, "identity")
        self.assertFalse(cursor_values(reference))

    def test_dynamic_classification_mode_and_site_owner_have_final_receipts(self):
        for change in ("mode", "site_owner"):
            reference, _ = reference_case("P16", F(3))
            context = object()
            with self.subTest(change=change), self.assertRaises(ReferenceError) as caught:
                with reference.recording_source_batch(context):
                    sample(reference, context, carriers=("rig", "payload.origin"))
                    if change == "mode":
                        reference._state_at(F(9, 4), "after").modes["payload"] = "prescribed"
                    else:
                        reference.model.sites["payload.origin"].owner = "rig"
            self.assertEqual(caught.exception.code, "identity")
            self.assertIsNone(reference._recording_batch)

    def test_transient_live_prescribed_fraction_cannot_enter_copied_plan_equations(self):
        outcomes = []
        for mutate in (False, True):
            reference, _ = reference_case("P16", F(3))
            context = object()
            active = reference._state_at(F(9, 4), "after").actions["travel"]
            active.ideal_initial = tuple(Interval(F(cell.lo.numerator, cell.lo.denominator),
                                                 F(cell.hi.numerator, cell.hi.denominator))
                                         for cell in active.ideal_initial)
            leaf = active.ideal_initial[0].lo
            original_numerator = leaf.numerator
            root, translation = reference._root_pose, reference._prescribed_root_translation
            changed_fields, restored = [], []

            def dynamic(*args, **kwargs):
                if mutate and args[0] == "payload":
                    def change():
                        reference.a.work.external_check = None
                        object.__setattr__(leaf, "_numerator", original_numerator + 1)
                        changed_fields.append(True)
                    reference.a.work.external_check = change
                return root(*args, **kwargs)

            def prescribed(*args, **kwargs):
                try:
                    return translation(*args, **kwargs)
                finally:
                    if mutate:
                        object.__setattr__(leaf, "_numerator", original_numerator)
                        restored.append(True)

            with reference.recording_source_batch(context):
                sample(reference, context)
                with patch.object(reference, "_root_pose", side_effect=dynamic), \
                        patch.object(reference, "_prescribed_root_translation", side_effect=prescribed):
                    outcomes.append(sample(reference, context, F(5, 2)))
            self.assertEqual(bool(changed_fields), mutate)
            self.assertEqual(bool(restored), mutate)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_declined_optional_plan_keeps_the_completed_dynamic_work(self):
        expected, _ = reference_case("P16", F(3))
        with ordinary():
            baseline = sample(expected, object())
        reference, _ = reference_case("P16", F(3))
        context, roots = object(), []
        root = reference._root_pose

        def observe(*args, **kwargs):
            roots.append(args[0])
            return root(*args, **kwargs)

        with reference.recording_source_batch(context), \
                patch.object(reference, "_root_pose", side_effect=observe), \
                patch.object(plans._Plan, "evaluate", return_value=None):
            self.assertEqual(sample(reference, context), baseline)
        self.assertEqual(roots.count("payload"), 1)
        self.assertIsNone(reference.a._recording_after_tick)

    def test_narrow_then_restored_cap_latches_fallback_without_repeating_dynamic_work(self):
        expected, _ = reference_case("P16", F(3))
        with ordinary():
            baseline = sample(expected, object())
        reference, _ = reference_case("P16", F(3))
        context, roots, callbacks = object(), [], []
        root, work = reference._root_pose, reference.a.work

        def observe(*args, **kwargs):
            if args[0] == "payload":
                roots.append(True)
                def change():
                    callbacks.append(True)
                    work.max_operand_bits = 32767 if len(callbacks) == 1 else 32768
                    if len(callbacks) == 2:
                        work.external_check = None
                work.external_check = change
            return root(*args, **kwargs)

        with reference.recording_source_batch(context), \
                patch.object(reference, "_root_pose", side_effect=observe), \
                patch.object(plans._Plan, "evaluate", side_effect=AssertionError("latched optional decline")):
            self.assertEqual(sample(reference, context), baseline)
        self.assertEqual(len(roots), 1)
        self.assertEqual(len(callbacks), 2)
        self.assertIs(reference.a.work, work)
        self.assertIsNone(reference.a._recording_after_tick)
        self.assertEqual(work.operations, sum(work.counts.values()))

    def test_original_dynamic_resource_failure_is_not_retried_after_optional_decline(self):
        reference, _ = reference_case("P16", F(3))
        context, failures, calls = object(), [], []
        root = reference._root_pose

        def observe(*args, **kwargs):
            if args[0] == "payload":
                calls.append(True)
                def narrow():
                    reference.a.work.max_operand_bits = 64
                    reference.a.work.external_check = None
                reference.a.work.external_check = narrow
            try:
                return root(*args, **kwargs)
            except ReferenceError as error:
                failures.append(error)
                raise

        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context), \
                    patch.object(reference, "_root_pose", side_effect=observe):
                sample(reference, context)
        self.assertEqual(caught.exception.code, "resource")
        self.assertIs(caught.exception, failures[0])
        self.assertEqual(calls, [True])
        self.assertIsNone(reference.a._recording_after_tick)

    def test_original_callback_exceptions_keep_exact_identity_and_scope_cleanup(self):
        for marker in (RuntimeError("partition callback"), TypeError("partition callback"),
                       KeyError("partition callback"), ReferenceError("resource", "partition callback")):
            reference, _ = reference_case("P16", F(3))
            context, calls = object(), []
            root = reference._root_pose

            def observe(*args, **kwargs):
                if args[0] == "payload":
                    def fail():
                        reference.a.work.external_check = None
                        calls.append(True)
                        raise marker
                    reference.a.work.external_check = fail
                return root(*args, **kwargs)

            with self.subTest(marker=type(marker)), self.assertRaises(type(marker)) as caught:
                with reference.recording_source_batch(context), \
                        patch.object(reference, "_root_pose", side_effect=observe):
                    sample(reference, context)
            self.assertIs(caught.exception, marker)
            self.assertIs(reference.a.work.callback_error, marker)
            self.assertEqual(calls, [True])
            self.assertIsNone(reference.a._recording_after_tick)
            self.assertIsNone(reference._recording_batch)

    def test_clock_precision_dispatch_and_observer_departures_reject_without_erasing_replacements(self):
        # The public reader copies its caller's Fraction before selecting the
        # source phase. Mutating that detached caller alias must not alter the
        # accepted sample or be mistaken for mutation of the consumed clock.
        outcomes = []
        for mutate_caller in (False, True):
            reference, _ = reference_case("P16", F(3))
            context, caller_clock, calls = object(), F(9, 4), []
            root = reference._root_pose
            def observe_caller(*args, **kwargs):
                if args[0] == "payload":
                    self.assertIsNot(args[1], caller_clock)
                    if mutate_caller:
                        def mutate():
                            reference.a.work.external_check = None
                            calls.append(True)
                            object.__setattr__(caller_clock, "_numerator", 10)
                        reference.a.work.external_check = mutate
                return root(*args, **kwargs)
            with reference.recording_source_batch(context), \
                    patch.object(reference, "_root_pose", side_effect=observe_caller):
                outcomes.append(sample(reference, context, caller_clock))
            self.assertEqual(calls, [True] if mutate_caller else [])
        self.assertEqual(*outcomes)

        for change in ("clock", "bits", "scale", "tick", "observer", "owner"):
            reference, _ = reference_case("P16", F(3))
            context, clock, calls = object(), F(9, 4), []
            root, foreign = reference._root_pose, lambda: None

            def observe(*args, **kwargs):
                if args[0] == "payload":
                    consumed_clock = args[1]
                    self.assertIsNot(consumed_clock, clock)
                    def mutate():
                        reference.a.work.external_check = None
                        calls.append(True)
                        if change == "clock":
                            object.__setattr__(consumed_clock, "_numerator", consumed_clock.numerator + 1)
                        elif change == "bits":
                            reference.a.bits = 256
                        elif change == "scale":
                            reference.a.scale = 1 << 256
                        elif change == "tick":
                            reference.a.tick = foreign
                        elif change == "observer":
                            reference.a._recording_after_tick = foreign
                        else:
                            reference.model.sites = deepcopy(reference.model.sites)
                    reference.a.work.external_check = mutate
                return root(*args, **kwargs)

            with self.subTest(change=change):
                with self.assertRaises(ReferenceError) as caught:
                    with reference.recording_source_batch(context), \
                            patch.object(reference, "_root_pose", side_effect=observe):
                        sample(reference, context, clock)
                self.assertEqual(caught.exception.code, "identity")
                self.assertEqual(calls, [True])
                if change == "observer":
                    self.assertIs(reference.a._recording_after_tick, foreign)
                else:
                    self.assertIsNone(reference.a._recording_after_tick)
                if change == "tick":
                    self.assertIs(reference.a.tick, foreign)

    def test_nested_reader_cursor_is_not_overwritten_or_deleted_by_the_outer_partition(self):
        reference, _ = reference_case("P16", F(3))
        context, nested = object(), []
        root = reference._root_pose

        def observe(*args, **kwargs):
            if not nested and args[0] == "payload":
                def reenter():
                    reference.a.work.external_check = None
                    nested.append(None)
                    nested[0] = sample(reference, context, F(11, 4))
                reference.a.work.external_check = reenter
            return root(*args, **kwargs)

        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context):
                sample(reference, context)
                with patch.object(reference, "_root_pose", side_effect=observe):
                    sample(reference, context, F(5, 2))
        self.assertEqual(caught.exception.code, "identity")
        self.assertTrue(nested[0])
        self.assertTrue(cursor_values(reference))
        self.assertTrue(all(value[3] == F(11, 4) for value in cursor_values(reference).values()))
        self.assertIsNone(reference.a._recording_after_tick)

    def test_source_change_retains_precedence_after_a_restored_cap_forces_fallback(self):
        reference, _ = reference_case("P16", F(3))
        context, callbacks = object(), []
        root = reference._root_pose

        def observe(*args, **kwargs):
            if args[0] == "payload":
                def change():
                    callbacks.append(True)
                    if len(callbacks) == 1:
                        reference.model.follows["rig.column_mount"].parent = "world"
                        reference.a.work.max_operand_bits = 32767
                    else:
                        reference.a.work.max_operand_bits = 32768
                        reference.a.work.external_check = None
                reference.a.work.external_check = change
            return root(*args, **kwargs)

        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context) as batch:
                with patch.object(reference, "_root_pose", side_effect=observe):
                    sample(reference, context)
        self.assertEqual(caught.exception.code, "identity")
        self.assertIsNone(batch.restart)
        self.assertEqual(len(callbacks), 2)
        self.assertIsNone(reference.a._recording_after_tick)

    def test_complete_supplied_byte_reader_matches_on_a_small_release_source_variant(self):
        # The original full P16 remains a separate unchanged-budget gate.
        # This explicit source variant reaches the same dynamic split in a
        # short artifact so both old and new complete readers fit that budget.
        bundle = changed(source_case("P16"), "at 2[s] sequence", "at 0.125[s] sequence")
        outcomes = []
        for partitioned in (False, True):
            compiler = compile_construction(bundle)
            observed = []
            original = plans._PartitionedPlan.evaluate_remaining

            def partial(partition, *args):
                result = original(partition, *args)
                observed.append(result is not None)
                return result

            with nullcontext() if partitioned else original_dynamic_reader():
                with patch.object(plans._PartitionedPlan, "evaluate_remaining", partial):
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertEqual(compiler.reach_work.max_operations, 100000)
            self.assertEqual(any(observed), partitioned)
            outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations))
        self.assertEqual(outcomes[0][:2], outcomes[1][:2])
        print(f"P16 early-release source variant: ordinary={outcomes[0][2]}, partitioned={outcomes[1][2]}")


if __name__ == "__main__":
    unittest.main()
