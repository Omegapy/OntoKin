"""Complete-reader source admission preserves cells, callbacks and finite work."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_conformance
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb
from ontokin.reach_reference import MAX_CACHE, ReachReference, ReferenceError
from ontokin.reach_reference_plan import _SourceBatchRestart
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_phase_plan import cursor_values
from test_reach_reference_world_recording import reference_case


def no_batch(reference, context):
    return nullcontext(None)


def normalized_cursors(reference):
    # Context objects deliberately differ between independent runs. Every
    # numerical cursor member, source witness and carrier identity must match.
    return {(key[3], key[4][1]): value for key, value in cursor_values(reference).items()}


def prefix(case="P09"):
    compiler = compile_construction(source_case(case))
    result = export_glb(compiler.model, options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
    return result, compiler


class IndependentSourceBatchTests(unittest.TestCase):
    def setUp(self):
        # Keep the original cell-identity, angle-cursor and callback cohort
        # exercising the legacy fallback. The independently validated nonzero
        # child-origin path has its own explicit containment/receipt cohort.
        context = patch("ontokin.reach_reference_plan._identity_child_origin", return_value=False)
        context.start()
        self.addCleanup(context.stop)

    def test_complete_source_batches_reduce_work_and_retain_exact_cells(self):
        for case in ("P05", "P09", "P11", "L03"):
            outcomes = []
            for batched in (False, True):
                reference, _ = reference_case(case, F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                start = reference.a.work.operations
                scope = reference.recording_source_batch(context) if batched else nullcontext(None)
                with scope:
                    values = [reference.recording_pose_enclosures(
                        carriers, F(index, 128), recording_context=context) for index in range(32)]
                outcomes.append((values, reference.a.work.operations - start))
                self.assertIsNone(reference._recording_batch)
                self.assertEqual(reference.a.work.operations, sum(reference.a.work.counts.values()))
                self.assertEqual(reference.a.work.max_operations, 100000)
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])
            print(f"{case} 32 independent source-batch keys: ordinary={outcomes[0][1]}, batched={outcomes[1][1]}")

    def test_actual_source_prefix_bytes_and_reports_are_identical(self):
        for case in ("P05", "P09", "P11", "L03"):
            outcomes = []
            for batched in (False, True):
                scope = nullcontext() if batched else patch.object(ReachReference, "recording_source_batch", no_batch)
                with scope:
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
            print(f"{case} source-batch prefix: ordinary={outcomes[0][2]}, batched={outcomes[1][2]}")

    def test_per_key_cache_cursors_eviction_and_64_step_reseeding_are_unchanged(self):
        for case, count in (("P09", 68), ("P11", 52)):
            outcomes = []
            for batched in (False, True):
                reference, _ = reference_case(case, F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                scope = reference.recording_source_batch(context) if batched else nullcontext(None)
                observations = []
                with scope as batch:
                    for index in range(count):
                        # P09 exercises the original 64-step ceiling; P11
                        # also loses every cursor through actual cache writes.
                        if case == "P11" and index == 26:
                            for item in range(MAX_CACHE):
                                reference.a.remember(("source-batch-eviction", item), F(item))
                            self.assertFalse(cursor_values(reference))
                        values = reference.recording_pose_enclosures(
                            carriers, F(index, 256), recording_context=context)
                        cursors = normalized_cursors(reference)
                        observations.append((values, cursors))
                        if case == "P09" and index == 65 or case == "P11" and index == 26:
                            self.assertTrue(cursors)
                            self.assertTrue(all(value[-1] == 0 for value in cursors.values()))
                        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
                        if batch is not None:
                            self.assertTrue(all(reference.a.cache.get(key) is value
                                                for key, value in batch.cursors.items()))
                            self.assertLessEqual(len(batch.cursors), MAX_CACHE)
                outcomes.append(observations)
            with self.subTest(case=case):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_unique_actual_receipts_are_admitted_after_the_complete_reader(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        reference.recording_pose_enclosures(carriers, F(1, 16), recording_context=context)
        plan = reference._recording_phase_plan
        admitted, original = [], reference._recording_admit_receipts
        def observe(receipts):
            admitted.append(tuple(receipts))
            return original(receipts)
        with patch.object(reference, "_recording_admit_receipts", side_effect=observe), \
                patch.object(reference, "_recording_capture", side_effect=AssertionError("unchanged captured plan")):
            with reference.recording_source_batch(context) as batch:
                for time in (F(1, 8), F(3, 16), F(1, 4)):
                    reference.recording_pose_enclosures(carriers, time, recording_context=context)
                    self.assertFalse(admitted)
                self.assertEqual(len(batch.receipts), len({id(receipt) for receipt in batch.receipts}))
            self.assertEqual(admitted, [plan.receipts])

    def test_final_source_change_discards_only_still_owned_new_cursors(self):
        reference, _ = reference_case("P09", F(1, 2))
        carriers = tuple(reference.model.objects)
        reference.recording_pose_enclosures(carriers, F(1, 16), recording_context=object())
        before, context = cursor_values(reference), object()
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context):
                reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
                state = reference._state_at(F(1, 4), "after")
                state.ideal_positions["rig"] = reference.p.vector((F(1, 8), 0, 0))
        self.assertEqual(caught.exception.code, "identity")
        self.assertIsNone(reference._recording_batch)
        current = cursor_values(reference)
        self.assertTrue(set(current).issubset(before))
        self.assertTrue(all(value is before[key] for key, value in current.items()))

    def test_equal_owner_and_phase_history_replacements_cannot_borrow_captured_source(self):
        for changed in ("model", "objects", "sites", "joints", "follows", "actions",
                        "boundaries", "_before", "_after", "state_slot", "precision"):
            reference, _ = reference_case("P09", F(1, 2))
            carriers, context = tuple(reference.model.objects), object()
            with self.subTest(changed=changed), self.assertRaises(ReferenceError) as caught:
                with reference.recording_source_batch(context):
                    reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                    if changed == "model":
                        reference.model = deepcopy(reference.model)
                    elif changed in ("objects", "sites", "joints", "follows", "actions"):
                        setattr(reference.model, changed, deepcopy(getattr(reference.model, changed)))
                    elif changed == "boundaries":
                        reference.boundaries = tuple(list(reference.boundaries))
                    elif changed in ("_before", "_after"):
                        setattr(reference, changed, list(getattr(reference, changed)))
                    elif changed == "state_slot":
                        state = reference._state_at(F(1, 8), "after")
                        index = next(index for index, item in enumerate(reference._after) if item is state)
                        reference._after[index] = deepcopy(state)
                    else:
                        reference.a.bits = 256
            self.assertEqual(caught.exception.code, "identity")
            self.assertFalse(cursor_values(reference))
            self.assertIsNone(reference._recording_batch)

    def test_transient_prescribed_source_mutation_cannot_enter_captured_equations(self):
        outcomes = []
        for mutate in (False, True):
            reference, _ = reference_case("P05", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            with reference.recording_source_batch(context):
                reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                translation = reference._prescribed_root_translation
                action, changed = reference.model.actions["travel"], []
                original_vector = action.vector
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
                    outcomes.append(reference.recording_pose_enclosures(
                        carriers, F(1, 4), recording_context=context))
                self.assertEqual(bool(changed), mutate)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_callback_errors_from_body_angle_and_final_precharge_keep_identity(self):
        for stage in ("body", "angle", "final"):
            for marker in (RuntimeError("source batch callback"), ReferenceError("resource", "source batch callback")):
                reference, _ = reference_case("P11" if stage == "angle" else "P09", F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                def fail():
                    reference.a.work.external_check = None
                    raise marker
                with self.subTest(stage=stage, marker=type(marker).__name__), \
                        self.assertRaises(type(marker)) as caught:
                    with reference.recording_source_batch(context) as batch:
                        reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                        if stage == "final":
                            reference.a.work.external_check = fail
                            batch.prepare_admission()
                        else:
                            remember = reference.a.remember
                            target = "recording_sincos" if stage == "angle" else "recording_body_orientation"
                            def publish(key, value, **kwargs):
                                if key[:1] == ("reference_pose",) and key[3] == target:
                                    reference.a.work.external_check = fail
                                return remember(key, value, **kwargs)
                            with patch.object(reference.a, "remember", side_effect=publish):
                                reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
                self.assertIs(caught.exception, marker)
                self.assertIs(reference.a.work.callback_error, marker)
                self.assertFalse(cursor_values(reference))
                self.assertIsNone(reference._recording_batch)

    def test_reentrant_reader_keeps_its_completed_cursor_when_outer_batch_rejects(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        remember, nested = reference.a.remember, []
        def publish(key, value, **kwargs):
            if not nested and key[:1] == ("reference_pose",) and key[3] == "recording_body_orientation":
                nested.append(None)
                with patch.object(reference.a, "remember", side_effect=remember):
                    nested[0] = reference.recording_pose_enclosures(carriers, F(3, 8), recording_context=context)
            return remember(key, value, **kwargs)
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context):
                reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                with patch.object(reference.a, "remember", side_effect=publish):
                    reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context)
        self.assertEqual(caught.exception.code, "identity")
        self.assertTrue(nested[0])
        self.assertTrue(cursor_values(reference))
        self.assertTrue(all(value[3] == F(3, 8) for key, value in cursor_values(reference).items()
                            if key[3] == "recording_body_orientation"))

    def test_optional_capture_bounds_fall_back_without_retaining_extra_history(self):
        for constant, maximum in (("MAX_BATCH_PLANS", 1), ("MAX_BATCH_RECEIPTS", 1)):
            outcomes = []
            for batched in (False, True):
                reference, _ = reference_case("P09", F(1, 2))
                context, carriers = object(), tuple(reference.model.objects)
                values = []
                scope = reference.recording_source_batch(context) if batched else nullcontext(None)
                with patch("ontokin.reach_reference_plan." + constant, maximum), scope as batch:
                    for index, selected in enumerate((carriers, tuple(reversed(carriers)), carriers), 1):
                        values.append(reference.recording_pose_enclosures(
                            selected, F(index, 8), recording_context=context))
                    if batch is not None:
                        self.assertLessEqual(len(batch.plans), maximum if constant == "MAX_BATCH_PLANS" else 16)
                        self.assertLessEqual(len(batch.receipts), maximum if constant == "MAX_BATCH_RECEIPTS" else 1024)
                outcomes.append(values)
            with self.subTest(constant=constant):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_source_change_and_narrowing_reject_identity_without_domain_restart(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, carriers = object(), tuple(reference.model.objects)
        with self.assertRaises(ReferenceError) as caught:
            with reference.recording_source_batch(context) as batch:
                reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
                reference._state_at(F(1, 8), "after").ideal_positions["rig"] = reference.p.vector((1, 0, 0))
                reference.a.work.max_operand_bits = 32767
        self.assertEqual(caught.exception.code, "identity")
        self.assertIsNone(batch.restart)
        self.assertFalse(cursor_values(reference))

    def test_later_optional_plan_refusal_keeps_the_complete_original_walker(self):
        outcomes = []
        for batched in (False, True):
            reference, _ = reference_case("P09", F(1, 2))
            context, carriers = object(), tuple(reference.model.objects)
            values = []
            scope = reference.recording_source_batch(context) if batched else nullcontext(None)
            with scope as batch:
                values.append(reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context))
                with patch("ontokin.reach_reference_plan.MAX_TARGETS", 1):
                    values.append(reference.recording_pose_enclosures(carriers, F(1, 4), recording_context=context))
                if batch is not None:
                    self.assertTrue(batch.plans)
                    self.assertFalse(batch.cursors)
                values.append(reference.recording_pose_enclosures(carriers, F(3, 8), recording_context=context))
            outcomes.append(values)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_narrow_initial_cap_and_dynamic_source_keep_original_per_key_paths(self):
        for case, end, time, cap in (("P09", F(1, 2), F(1, 8), 32767),
                                     ("P16", F(3), F(9, 4), 32768)):
            outcomes = []
            for batched in (False, True):
                reference, _ = reference_case(case, end)
                reference.a.work.max_operand_bits = cap
                context, carriers = object(), tuple(reference.model.objects)
                scope = reference.recording_source_batch(context) if batched else nullcontext(None)
                with scope as batch:
                    outcomes.append(reference.recording_pose_enclosures(carriers, time, recording_context=context))
                    if batch is not None:
                        self.assertFalse(batch.plans)
                        self.assertFalse(batch.cursors)
            with self.subTest(case=case):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_mutable_or_foreign_boundary_axes_keep_original_per_key_admission(self):
        for shape in ("list", "float"):
            outcomes = []
            for batched in (False, True):
                reference, _ = reference_case("P09", F(1, 2))
                reference.boundaries = (list(reference.boundaries) if shape == "list" else
                                        tuple(float(time) for time in reference.boundaries))
                context, carriers = object(), tuple(reference.model.objects)
                scope = reference.recording_source_batch(context) if batched else nullcontext(None)
                with scope as batch:
                    outcomes.append([reference.recording_pose_enclosures(
                        carriers, time, recording_context=context) for time in (F(1, 8), F(1, 4))])
                    if batch is not None:
                        self.assertFalse(batch.active)
                        self.assertFalse(batch.plans)
                        self.assertFalse(batch.cursors)
            with self.subTest(shape=shape):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_foreign_or_mismatched_history_lists_keep_original_per_key_admission(self):
        class History(list):
            pass
        for history in ("_before", "_after"):
            for change in ("subclass", "extra_state"):
                outcomes = []
                for batched in (False, True):
                    reference, _ = reference_case("P09", F(1, 2))
                    original = getattr(reference, history)
                    replacement = History(original) if change == "subclass" else [*original, original[-1]]
                    setattr(reference, history, replacement)
                    context, carriers = object(), tuple(reference.model.objects)
                    scope = reference.recording_source_batch(context) if batched else nullcontext(None)
                    with scope as batch:
                        outcomes.append([reference.recording_pose_enclosures(
                            carriers, time, recording_context=context) for time in (F(1, 8), F(1, 4))])
                        if batch is not None:
                            self.assertFalse(batch.active)
                            self.assertFalse(batch.plans)
                            self.assertFalse(batch.cursors)
                with self.subTest(history=history, change=change):
                    self.assertEqual(outcomes[0], outcomes[1])


class IndependentSourceBatchTerminalTests(unittest.TestCase):
    def terminal_callback(self, action):
        """Arm an actual Work callback at the last outward report conversion."""
        owners, fired = [], []
        original_batch = ReachReference.recording_source_batch
        original_tick = reach_conformance._Bounds.tick
        rounds = []
        def batch(reference, context):
            owners.append(reference)
            return original_batch(reference, context)
        def tick(arithmetic, kind="independent_bound_arithmetic"):
            if kind == "independent_report_rounding":
                rounds.append(True)
                if len(rounds) == 3:
                    reference = owners[-1]
                    def callback():
                        reference.a.work.external_check = None
                        fired.append(True)
                        action(reference)
                    reference.a.work.external_check = callback
            return original_tick(arithmetic, kind)
        return owners, fired, rounds, patch.object(ReachReference, "recording_source_batch", batch), \
            patch.object(reach_conformance._Bounds, "tick", tick)

    def test_report_rounding_source_mutation_is_rejected_before_passed_return(self):
        def mutate(reference):
            state = reference._state_at(F(1, 8), "after")
            state.ideal_positions["rig"] = reference.p.vector((1, 0, 0))
        owners, fired, rounds, capture, callback = self.terminal_callback(mutate)
        with capture, callback, self.assertRaises(OntoKinError) as caught:
            prefix()
        self.assertEqual(caught.exception.diagnostic.code, "OKL-E-CAPABILITY-UNSUPPORTED")
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-INDEPENDENT-VALIDATION")
        self.assertEqual(caught.exception.diagnostic.details["reference_code"], "identity")
        self.assertEqual(fired, [True])
        self.assertEqual(len(rounds), 3)
        self.assertFalse(cursor_values(owners[0]))

    def test_final_cap_change_replays_all_endpoints_and_report_on_the_same_budget(self):
        with patch.object(ReachReference, "recording_source_batch", no_batch):
            expected, _ = prefix()
        def narrow(reference):
            reference.a.work.max_operand_bits = 32767
        owners, fired, rounds, capture, callback = self.terminal_callback(narrow)
        original, keys = reach_conformance._key_comparisons, []
        def compare(*args, **kwargs):
            keys.append((args[4], kwargs.get("recording_context")))
            return original(*args, **kwargs)
        with capture, callback, patch.object(reach_conformance, "_key_comparisons", side_effect=compare):
            actual, compiler = prefix()
        self.assertEqual(actual.data, expected.data)
        self.assertEqual(actual.report["validation"], expected.report["validation"])
        count = actual.report["validation"]["sample_count"]
        self.assertEqual([index for index, _ in keys], list(range(count)) * 2)
        self.assertIsNot(keys[0][1], keys[count][1])
        self.assertEqual(len(owners), 1)
        self.assertIs(owners[0].a.work, compiler.reach_work)
        self.assertEqual(compiler.reach_work.max_operations, 100000)
        self.assertEqual(compiler.reach_work.max_operand_bits, 32767)
        self.assertEqual(compiler.reach_work.operations, sum(compiler.reach_work.counts.values()))
        self.assertEqual(fired, [True])
        self.assertEqual(len(rounds), 6)
        self.assertFalse(cursor_values(owners[0]))

    def test_callback_private_restart_exception_is_never_retried(self):
        marker = _SourceBatchRestart("original caller callback")
        def fail(reference):
            raise marker
        owners, fired, rounds, capture, callback = self.terminal_callback(fail)
        original, keys = reach_conformance._key_comparisons, []
        def compare(*args, **kwargs):
            keys.append(args[4])
            return original(*args, **kwargs)
        with capture, callback, patch.object(reach_conformance, "_key_comparisons", side_effect=compare), \
                self.assertRaises(_SourceBatchRestart) as caught:
            prefix()
        self.assertIs(caught.exception, marker)
        self.assertIs(owners[0].a.work.callback_error, marker)
        self.assertEqual(keys, list(range(len(keys))))
        self.assertEqual(fired, [True])
        self.assertEqual(len(rounds), 3)
        self.assertFalse(cursor_values(owners[0]))

    def test_original_terminal_arithmetic_failure_is_not_retried_after_narrowing(self):
        marker = RuntimeError("original report comparison failure")
        def narrow(reference):
            reference.a.work.max_operand_bits = 32767
        owners, fired, rounds, capture, callback = self.terminal_callback(narrow)
        original, failures = reach_conformance._Bounds.compare, []
        def compare(arithmetic, *args, **kwargs):
            if fired:
                failures.append(True)
                # A subsequent callback could broaden the allowance; the
                # failed original operation must never get that second try.
                arithmetic.work.external_check = lambda: setattr(arithmetic.work, "max_operand_bits", 32768)
                raise marker
            return original(arithmetic, *args, **kwargs)
        with capture, callback, patch.object(reach_conformance._Bounds, "compare", compare), \
                self.assertRaises(RuntimeError) as caught:
            prefix()
        self.assertIs(caught.exception, marker)
        self.assertEqual(failures, [True])
        self.assertEqual(len(rounds), 3)
        self.assertIsNone(owners[0]._recording_batch)
        self.assertFalse(cursor_values(owners[0]))


if __name__ == "__main__":
    unittest.main()
