"""Captured stationary-source proofs retain actual laws and reader admission."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_reference_plan as plans
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_reference import MAX_CACHE, ReferenceError
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_reference_phase_plan import cursor_values
from test_reach_reference_source_batch import normalized_cursors
from test_reach_reference_world_recording import reference_case


def original_stationarity():
    return patch.object(plans, "recording_stationary_frames", return_value=None)


def seed(reference, context, time=F(1, 16)):
    carriers = tuple(reference.model.objects)
    reference.recording_pose_enclosures(carriers, time, recording_context=context)
    return carriers


class IndependentStationaryBatchTests(unittest.TestCase):
    def test_complete_stationary_sets_and_pose_cells_match_with_less_work(self):
        for case in ("P05", "P09", "P11", "L03"):
            outcomes = []
            for captured in (False, True):
                reference, _ = reference_case(case, F(1, 2))
                context, observations, query_cost = object(), [], 0
                with nullcontext() if captured else original_stationarity():
                    with reference.recording_source_batch(context) as batch:
                        carriers = seed(reference, context, F(0))
                        for index in range(1, 20):
                            first, last = F(index - 1, 128), F(index, 128)
                            start = reference.a.work.operations
                            stationary = reference.recording_stationary_frames(carriers, first, last)
                            query_cost += reference.a.work.operations - start
                            poses = reference.recording_pose_enclosures(carriers, last,
                                                                       recording_context=context)
                            observations.append((stationary, poses, normalized_cursors(reference)))
                        self.assertLessEqual(len(batch.receipts), plans.MAX_BATCH_RECEIPTS)
                        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
                outcomes.append((observations, query_cost))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])
            print(f"{case} 19 stationary queries: original={outcomes[0][1]}, captured={outcomes[1][1]}")

    def test_actual_source_prefix_bytes_and_validation_remain_identical(self):
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for captured in (False, True):
                compiler = compile_construction(source_case(case))
                with nullcontext() if captured else original_stationarity():
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=4, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                self.assertEqual(compiler.reach_work.max_operand_bits, 32768)
                self.assertEqual(compiler.reach_work.max_cache_entries, 256)
                outcomes.append((result.data, result.report["validation"], compiler.budget.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLess(outcomes[1][2], outcomes[0][2])
            print(f"{case} stationary source prefix: original={outcomes[0][2]}, captured={outcomes[1][2]}")

    def test_full_then_pruned_pose_plans_keep_stationary_proofs_after_numeric_eviction(self):
        for case in ("P09", "L03"):
            outcomes = []
            for captured in (False, True):
                reference, _ = reference_case(case, F(1, 2))
                context, observations, query_costs = object(), [], []
                with nullcontext() if captured else original_stationarity():
                    with reference.recording_source_batch(context) as batch:
                        carriers = seed(reference, context, F(0))
                        full = reference._recording_phase_plan
                        with original_stationarity():
                            expected = reference.recording_stationary_frames(carriers, F(0), F(1, 128))
                        moving = tuple(carrier for carrier in carriers if carrier + ".frame" not in expected)
                        self.assertTrue(moving)
                        self.assertLess(len(moving), len(carriers))
                        for index in range(1, 20):
                            if index == 4:
                                for item in range(MAX_CACHE):
                                    reference.a.remember(("pruned-stationarity-eviction", item), F(item))
                                self.assertFalse(cursor_values(reference))
                            first, last = F(index - 1, 128), F(index, 128)
                            start = reference.a.work.operations
                            stationary = reference.recording_stationary_frames(carriers, first, last)
                            query_costs.append(reference.a.work.operations - start)
                            self.assertEqual(stationary, expected)
                            poses = reference.recording_pose_enclosures(moving, last, recording_context=context)
                            pruned = reference._recording_phase_plan
                            self.assertIsNot(pruned, full)
                            self.assertTrue(set(expected) - {node.path for node in pruned.nodes})
                            self.assertEqual(len(batch.plans), 2)
                            observations.append((stationary, poses, normalized_cursors(reference)))
                outcomes.append((observations, query_costs))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertTrue(all(cost > 1 for cost in outcomes[0][1]))
                self.assertEqual(outcomes[1][1], [1] * 19)
            print(f"{case} full/pruned stationary queries: original={sum(outcomes[0][1])}, "
                  f"captured={sum(outcomes[1][1])}")

    def test_actual_multikey_prefix_uses_registered_full_plan_and_keeps_bytes(self):
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for captured in (False, True):
                compiler = compile_construction(source_case(case))
                helper, queries = plans.recording_stationary_frames, []
                def observe(*args):
                    result = helper(*args) if captured else None
                    queries.append(result)
                    return result
                with patch.object(plans, "recording_stationary_frames", side_effect=observe):
                    result = export_glb(compiler.model,
                        options=ExportOptions(end=F(1, 4), fps=32, helpers=False),
                        target_contract="ontokin.glb/0.6", work=compiler.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertGreaterEqual(len(queries), 8)
                if captured:
                    self.assertGreaterEqual(sum(value is not None for value in queries), 8)
                outcomes.append((result.data, result.report["validation"], compiler.budget.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLess(outcomes[1][2], outcomes[0][2])
            print(f"{case} multikey stationary prefix: original={outcomes[0][2]}, captured={outcomes[1][2]}")

    def test_previous_plan_registration_state_context_and_native_type_are_required(self):
        for change in ("unregistered", "state", "context", "foreign"):
            reference, _ = reference_case("P09", F(1, 2))
            context = object()
            with self.subTest(change=change), reference.recording_source_batch(context) as batch:
                carriers = seed(reference, context, F(0))
                full = reference._recording_phase_plan
                with original_stationarity():
                    expected = reference.recording_stationary_frames(carriers, F(0), F(1, 16))
                moving = tuple(carrier for carrier in carriers if carrier + ".frame" not in expected)
                reference.recording_pose_enclosures(moving, F(1, 16), recording_context=context)
                registered, state, previous_context = batch.plans[full.cache_identity], full.state, full.context
                try:
                    if change == "unregistered":
                        del batch.plans[full.cache_identity]
                    elif change == "state":
                        object.__setattr__(full, "state", deepcopy(state))
                    elif change == "context":
                        object.__setattr__(full, "context", (object(), *previous_context[1:]))
                    else:
                        batch.plans[full.cache_identity] = (object(), registered[1])
                    with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
                        actual = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
                    self.assertTrue(incoming.called)
                    self.assertEqual(actual, expected)
                finally:
                    batch.plans[full.cache_identity] = registered
                    object.__setattr__(full, "state", state)
                    object.__setattr__(full, "context", previous_context)

    def test_previous_plan_owner_and_source_mutation_cannot_publish_reused_proofs(self):
        for change in ("owner", "source"):
            with self.subTest(change=change):
                reference, _ = reference_case("P09", F(1, 2))
                context = object()
                with self.assertRaises(ReferenceError) as caught:
                    with reference.recording_source_batch(context):
                        carriers = seed(reference, context, F(0))
                        full = reference._recording_phase_plan
                        with original_stationarity():
                            stationary = reference.recording_stationary_frames(carriers, F(0), F(1, 16))
                        moving = tuple(carrier for carrier in carriers if carrier + ".frame" not in stationary)
                        reference.recording_pose_enclosures(moving, F(1, 16), recording_context=context)
                        self.assertNotIn("rig.column.frame", {node.path for node in reference._recording_phase_plan.nodes})
                        if change == "owner":
                            object.__setattr__(full, "owners", (object(), *full.owners[1:]))
                        else:
                            offset = reference.model.follows["rig.column_mount"].offset
                            object.__setattr__(offset, "position", (F(1), *offset.position[1:]))
                        reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
                self.assertEqual(caught.exception.code, "identity")
                self.assertIsNone(reference._recording_batch)
                self.assertFalse(cursor_values(reference))

    def test_zero_ideal_rate_does_not_prove_a_changing_actual_coordinate_stationary(self):
        reference, _ = reference_case("P09", F(1, 2))
        state = reference._state_at(F(1, 8), "after")
        active = state.actions["reach"]
        self.assertNotEqual(tuple(active.initial), tuple(active.targets))
        active.ideal_initial = tuple(active.targets)
        context = object()
        with reference.recording_source_batch(context):
            carriers = seed(reference, context)
            plan = reference._recording_phase_plan
            rejected = [node for node in plan.nodes if node.kind == "hinge"
                        and node.stationary and node.source_stationary is False]
            self.assertTrue(rejected)
            actual = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            with original_stationarity():
                expected = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertEqual(actual, expected)
            self.assertTrue(all(node.path not in actual for node in rejected))

    def test_actual_anchor_and_coordinate_changes_are_rejected_at_final_admission(self):
        for change in ("position", "orientation", "coordinate", "initial"):
            with self.subTest(change=change):
                reference, _ = reference_case("P11", F(1, 2))
                context = object()
                state = reference._state_at(F(1, 8), "after")
                relation = reference.model.actions["reach"].reach.shoulder
                if change == "coordinate":
                    # An explicit unclaimed variant exercises the stored
                    # actual coordinate receipt. In the original P11 this
                    # same stationary hinge has a running zero-rate owner.
                    state.claims.pop((relation, "coordinate"), None)
                with self.assertRaises(ReferenceError) as caught:
                    with reference.recording_source_batch(context):
                        carriers = seed(reference, context)
                        if change in ("position", "orientation"):
                            root = next(node.path.removesuffix(".frame")
                                        for node in reference._recording_phase_plan.nodes
                                        if node.kind == "root" and node.source_stationary)
                            if change == "position":
                                state.positions[root] = reference.p.vector((F(1, 8), 0, 0))
                            else:
                                state.orientations[root] = reference.p.vector((0, 0, 0, 1))
                        else:
                            node = next(node for node in reference._recording_phase_plan.nodes
                                        if node.relation == relation)
                            self.assertTrue(node.source_stationary)
                            if change == "coordinate":
                                self.assertNotIn((relation, "coordinate"), state.claims)
                                state.coordinates[relation] += F(1, 8)
                            else:
                                # Keep the ideal zero-rate law and replace
                                # only its actual initial source operand.
                                self.assertEqual(state.claims[relation, "coordinate"], "reach")
                                state.actions["reach"].initial = (F(1, 8), F(0))
                        reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
                self.assertEqual(caught.exception.code, "identity")
                self.assertIsNone(reference._recording_batch)
                self.assertFalse(cursor_values(reference))

    def test_entry_callback_keeps_cancellation_identity_and_current_cap(self):
        for cancel in (False, True):
            reference, _ = reference_case("P09", F(1, 2))
            context, marker, seen = object(), RuntimeError("stationary entry cancellation"), []
            scope = reference.recording_source_batch(context)
            with self.subTest(cancel=cancel), self.assertRaises(RuntimeError if cancel else plans._SourceBatchRestart) as caught:
                with scope:
                    carriers = seed(reference, context)
                    def callback():
                        reference.a.work.external_check = None
                        seen.append(True)
                        if cancel:
                            raise marker
                        reference.a.work.max_operand_bits = 32767
                    reference.a.work.external_check = callback
                    with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
                        actual = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
                        self.assertTrue(incoming.called)
                    with original_stationarity():
                        expected = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
                    self.assertEqual(actual, expected)
            self.assertEqual(seen, [True])
            if cancel:
                self.assertIs(caught.exception, marker)
                self.assertIs(reference.a.work.callback_error, marker)
            else:
                self.assertIs(caught.exception, scope.restart)
            self.assertFalse(cursor_values(reference))

    def test_owner_replacement_during_entry_cannot_borrow_a_source_plan(self):
        for owner in ("model", "objects", "_after"):
            reference, _ = reference_case("P09", F(1, 2))
            context = object()
            with self.subTest(owner=owner), self.assertRaises(ReferenceError) as caught:
                with reference.recording_source_batch(context):
                    carriers = seed(reference, context)
                    def callback():
                        reference.a.work.external_check = None
                        if owner == "model":
                            reference.model = deepcopy(reference.model)
                        elif owner == "objects":
                            reference.model.objects = dict(reference.model.objects)
                        else:
                            reference._after = list(reference._after)
                    reference.a.work.external_check = callback
                    reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertEqual(caught.exception.code, "identity")

    def test_phase_boundaries_sides_unregistered_plans_and_prepared_batches_keep_original_walk(self):
        reference, _ = reference_case("L03", F(3))
        context = object()
        with reference.recording_source_batch(context) as batch:
            carriers = seed(reference, context, F(15, 8))
            for first, last, side in ((F(15, 8), F(2), "after"), (F(15, 8), F(2), "before")):
                actual = reference.recording_stationary_frames(carriers, first, last, side)
                with original_stationarity():
                    expected = reference.recording_stationary_frames(carriers, first, last, side)
                self.assertEqual(actual, expected)
            batch.prepare_admission()
            with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
                reference.recording_stationary_frames(carriers, F(7, 4), F(15, 8))
            self.assertTrue(incoming.called)
        # An ideal plan created before source batching has no captured actual
        # stationarity operands. Reusing its ideal pose recipes remains valid,
        # while stationary endpoint decisions keep the complete source walk.
        reference, _ = reference_case("P09", F(1, 2))
        context = object()
        carriers = seed(reference, context)
        self.assertTrue(all(node.source_stationary is None for node in reference._recording_phase_plan.nodes))
        with reference.recording_source_batch(context):
            reference.recording_pose_enclosures(carriers, F(1, 8), recording_context=context)
            with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
                reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertTrue(incoming.called)

    def test_foreign_shapes_unknown_carriers_and_wide_clocks_keep_original_order(self):
        class Name(str):
            pass
        reference, _ = reference_case("P09", F(1, 2))
        context = object()
        with reference.recording_source_batch(context):
            carriers = seed(reference, context)
            for selected, first, last in (([Name(carriers[0])], F(1, 16), F(1, 8)),
                                           (carriers, 0, F(1, 8)),
                                           (carriers, F(1, 1 << 1025), F(1, 8))):
                self.assertIsNone(plans.recording_stationary_frames(reference, selected, first, last, "after"))
                actual = reference.recording_stationary_frames(selected, first, last)
                with original_stationarity():
                    expected = reference.recording_stationary_frames(selected, first, last)
                self.assertEqual(actual, expected)
            with self.assertRaises(ReferenceError) as caught:
                reference.recording_stationary_frames(("missing",), F(-1), F(1, 8))
            self.assertEqual(caught.exception.code, "identity")
            saved = reference._recording_phase_plan
            reference._recording_phase_plan = object()
            with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
                reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertTrue(incoming.called)
            reference._recording_phase_plan = saved

    def test_unavailable_actual_receipt_declines_only_stationarity_reuse(self):
        reference, _ = reference_case("P09", F(1, 2))
        state = reference._state_at(F(1, 8), "after")
        state.positions["rig"] = list(state.positions["rig"])
        context = object()
        with reference.recording_source_batch(context):
            carriers = seed(reference, context)
            self.assertIsNotNone(reference._recording_phase_plan)
            root = next(node for node in reference._recording_phase_plan.nodes if node.path == "rig.frame")
            self.assertIsNone(root.source_stationary)
            with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
                actual = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertTrue(incoming.called)
            with original_stationarity():
                expected = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertEqual(actual, expected)

    def test_reentrant_other_context_cannot_lend_its_unregistered_plan(self):
        reference, _ = reference_case("P09", F(1, 2))
        context, nested = object(), []
        with reference.recording_source_batch(context):
            carriers = seed(reference, context)
            def callback():
                reference.a.work.external_check = None
                nested.append(reference.recording_pose_enclosures(
                    carriers, F(3, 32), recording_context=object()))
            reference.a.work.external_check = callback
            with patch.object(reference, "_incoming", wraps=reference._incoming) as incoming:
                actual = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertTrue(nested)
            self.assertTrue(incoming.called)
            with original_stationarity():
                expected = reference.recording_stationary_frames(carriers, F(1, 16), F(1, 8))
            self.assertEqual(actual, expected)

    def test_eviction_and_reseed_cursors_remain_the_same_with_stationarity_queries(self):
        outcomes = []
        for captured in (False, True):
            reference, _ = reference_case("P09", F(1, 2))
            context, observations = object(), []
            with nullcontext() if captured else original_stationarity():
                with reference.recording_source_batch(context):
                    carriers = seed(reference, context, F(0))
                    for index in range(1, 68):
                        if index == 2:
                            for item in range(MAX_CACHE):
                                reference.a.remember(("stationary-batch-eviction", item), F(item))
                            self.assertFalse(cursor_values(reference))
                        first, last = F(index - 1, 256), F(index, 256)
                        stationary = reference.recording_stationary_frames(carriers, first, last)
                        values = reference.recording_pose_enclosures(carriers, last, recording_context=context)
                        cursors = normalized_cursors(reference)
                        if index in (2, 67):
                            self.assertTrue(cursors)
                            self.assertTrue(all(value[-1] == 0 for value in cursors.values()))
                        observations.append((stationary, values, cursors))
                        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
            outcomes.append(observations)
        self.assertEqual(outcomes[0], outcomes[1])


if __name__ == "__main__":
    unittest.main()
