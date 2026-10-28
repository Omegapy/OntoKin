"""Whole pure phase nodes retain source laws, complete bounds and live guards."""
import copy
from contextlib import contextmanager
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_export import reach_prefix_plan, recording_phase_bounds
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.scene import ExportOptions
from test_reach_phase import source
from test_reach_phase_mounts import PlanningSimulator
from test_reach_phase_reuse import uncached_phases


def node_key(key):
    return len(key) > 3 and key[:3] == (reach_phase._CACHE_DOMAIN, MAX_OPERAND_BITS, "source_node")


@contextmanager
def node_mode(enabled):
    # Force small fixtures through the same optional path, while retaining the
    # production full-domain requirement after every callback.
    with patch.object(reach_phase, "_reuse_phase_nodes",
                      lambda model, work: enabled and work.max_operand_bits == MAX_OPERAND_BITS):
        yield


def prepared(case="P01", start=F(0), *, capacity=None):
    built = compile_construction(source(case))
    work = built.reach_work if capacity is None else ReachExecutionWork(max_cache_entries=capacity)
    simulator = PlanningSimulator(built.model, work=work)
    simulator.advance(start, "after")
    return built, simulator


class ReachPhaseNodeReuseTests(unittest.TestCase):
    def test_complete_phase_maps_and_recording_witnesses_equal_original_node_dags(self):
        cases = (("P23", F(0), F(2)), ("P23", F(2), F(3)),
                 ("P01", F(0), F(2)), ("P05", F(0), F(1)),
                 ("L01", F(0), F(1, 2)), ("L02", F(1, 2), F(3, 2)),
                 ("P16", F(2), F(3)))
        for case, start, end in cases:
            with self.subTest(case=case, start=start):
                outputs, costs = [], []
                for enabled in (True, False):
                    built, simulator = prepared(case, start)
                    previous = copy.deepcopy(simulator.state)
                    before = built.budget.operations
                    with node_mode(enabled):
                        outputs.append(recording_phase_bounds(simulator, start, end, recording_proof=True))
                    costs.append(built.budget.operations - before)
                    self.assertEqual(simulator.state, previous)
                    self.assertLessEqual(built.budget.operations, 100000)
                    self.assertLessEqual(len(simulator.work._cache), 256)
                    self.assertEqual(simulator.work.operations, sum(simulator.work.counts.values()))
                self.assertEqual(outputs[0], outputs[1])
                if case == "P23":
                    self.assertGreater(costs[1] - costs[0], 500)
                for path, record in outputs[0][1].frames.items():
                    self.assertIsNot(record.token, outputs[1][1].frames[path].token)

    def test_complete_p23_prefix_and_small_glb_are_exactly_unchanged(self):
        plans, costs = [], []
        for enabled in (True, False):
            built = compile_construction(source("P23"))
            with node_mode(enabled):
                plan = reach_prefix_plan(built.model, F(3), work=built.reach_work)
            plans.append((plan.boundaries, plan.phases, plan.phase_states,
                          plan.final_state, plan.boundary_records))
            costs.append(built.budget.operations)
            self.assertLessEqual(built.budget.operations, 100000)
        self.assertEqual(plans[0], plans[1])
        self.assertGreater(costs[1] - costs[0], 1000)

        artifacts = []
        for enabled in (True, False):
            built = compile_construction(source("P01"))
            with node_mode(enabled):
                result = export_glb(built.model,
                    options=ExportOptions(end=F(1, 4), fps=1, helpers=True),
                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            artifacts.append(result.data)
        self.assertEqual(artifacts[0], artifacts[1])

    def test_warm_keys_bind_all_actual_parent_local_axis_and_scalar_inputs(self):
        for change in ("axis", "child_position", "child_rotation", "duration",
                       "actual_initial", "ideal_initial", "target", "parent_position", "parent_error"):
            with self.subTest(change=change):
                _, simulator = prepared()
                action = simulator.model.actions["reach"]
                runtime = simulator.state.actions["reach"]
                elbow = simulator.model.joints[action.reach.elbow]
                site = simulator.model.sites[elbow.child]
                with node_mode(True):
                    baseline = reach_phase.phase_bounds(simulator, F(0), F(1, 2), recording_proof=True)
                    if change == "axis":
                        elbow.axis = (1.0, 0.0, 0.0)
                    elif change == "child_position":
                        site.pose = replace(site.pose, position=(0.25, 0.0, 0.0))
                    elif change == "child_rotation":
                        site.pose = replace(site.pose, rotation=(0.0, 1.0, 0.0, 0.0))
                    elif change == "duration":
                        action.duration = F(4)
                    elif change == "actual_initial":
                        runtime.initial = (0.125, runtime.initial[1])
                    elif change == "ideal_initial":
                        runtime.ideal_initial = (F(1, 8), runtime.ideal_initial[1])
                    elif change == "target":
                        runtime.solution = replace(runtime.solution, target_rad=(0.125, 1.0))
                    else:
                        incoming = simulator._incoming(simulator.state)
                        root = next(path for path in simulator.model.objects if path not in incoming)
                        if change == "parent_position":
                            simulator.state.positions[root] = (1.0, 2.0, 3.0)
                            simulator.state.ideal_positions[root] = (F(1), F(2), F(3))
                        else:
                            simulator.state.root_rotation_errors[root] = F(1, 1024)
                    actual = reach_phase.phase_bounds(simulator, F(0), F(1, 2), recording_proof=True)
                with node_mode(False), uncached_phases(simulator.work):
                    expected = reach_phase.phase_bounds(simulator, F(0), F(1, 2), recording_proof=True)
                self.assertEqual(actual, expected)
                self.assertNotEqual(actual, baseline)

    def test_template_results_have_complete_intermediates_and_no_deferred_numeric_values(self):
        _, simulator = prepared()
        with node_mode(True):
            first = reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True)
            second = reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True)
        retained = [value for key, value in simulator.work._cache.items() if node_key(key)]
        self.assertTrue(retained)
        self.assertGreater(simulator.work.counts.get("phase_node_reuse", 0), 0)
        self.assertEqual(first, second)
        self.assertIsNot(first["frames"], second["frames"])
        self.assertEqual(len(reach_phase._BOUND_FIELDS), 18)
        for bounds in retained:
            self.assertIn(len(bounds), (1, 2))
            self.assertTrue(all(type(bound) is reach_phase.PhaseBound for bound in bounds))
        for path, bound in second["objects"].items():
            self.assertIs(bound, second["frames"][path + ".frame"])
        for path, record in second["recording_angular_proof"].frames.items():
            self.assertEqual(record.trig_count, second["frames"][path].trig_count)
            self.assertIsNot(record.token, first["recording_angular_proof"].frames[path].token)

    def test_callback_source_replacement_cannot_poison_an_earlier_numeric_key(self):
        _, simulator = prepared()
        joint = simulator.model.joints[simulator.model.actions["reach"].reach.elbow]
        previous_axis = joint.axis
        changed = False
        original = simulator.work.lookup

        def lookup(key):
            nonlocal changed
            if (node_key(key) and key[3] == "hinge" and key[8].ideal_slope and not changed):
                changed = True
                joint.axis = (1.0, 0.0, 0.0)
            return original(key)

        with node_mode(True), patch.object(simulator.work, "lookup", lookup):
            first = reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True)
        self.assertTrue(changed)
        child_frame = simulator.model.sites[joint.child].owner + ".frame"
        self.assertNotIn(child_frame, first["recording_angular_proof"].frames)
        for axis in ((1.0, 0.0, 0.0), previous_axis):
            joint.axis = axis
            with node_mode(True):
                actual = reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True)
            with node_mode(False), uncached_phases(simulator.work):
                expected = reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True)
            self.assertEqual(actual, expected)

    def test_narrowed_lookup_and_publication_replay_original_complete_operands(self):
        for stage in ("reuse", "publication"):
            with self.subTest(stage=stage):
                _, simulator = prepared()
                with node_mode(True):
                    if stage == "reuse":
                        reach_phase.phase_bounds(simulator, F(0), F(1))
                    previous = copy.deepcopy(simulator.state)
                    original_charge, original_remember = simulator.work.charge, simulator.work.remember
                    changed = False

                    def charge(kind="checkpoint", amount=1):
                        nonlocal changed
                        if stage == "reuse" and kind == "phase_node_reuse" and not changed:
                            changed = True
                            simulator.work.max_operand_bits = 128
                        return original_charge(kind, amount)

                    def remember(key, value):
                        nonlocal changed
                        if stage == "publication" and node_key(key) and not changed:
                            changed = True
                            simulator.work.max_operand_bits = 128
                        return original_remember(key, value)

                    with patch.object(simulator.work, "charge", charge), \
                            patch.object(simulator.work, "remember", remember):
                        with self.assertRaises(ReachAdmissionError) as caught:
                            reach_phase.phase_bounds(simulator, F(0), F(1))
                    self.assertTrue(changed)
                    self.assertEqual(caught.exception.reach_code, "reach_resource")
                    self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
                    self.assertEqual(simulator.state, previous)

    def test_cancelled_lookup_or_publication_never_replaces_a_completed_template(self):
        for warm in (False, True):
            with self.subTest(warm=warm):
                _, simulator = prepared()
                with node_mode(True):
                    if warm:
                        reach_phase.phase_bounds(simulator, F(0), F(1))
                    retained = {key: value for key, value in simulator.work._cache.items() if node_key(key)}
                    previous = copy.deepcopy(simulator.state)
                    operation = "lookup" if warm else "remember"
                    original = getattr(simulator.work, operation)
                    marker = RuntimeError("cancel complete phase node " + operation)

                    def checked(key, *args):
                        if node_key(key):
                            with patch.object(simulator.work, "external_check", side_effect=marker):
                                return original(key, *args)
                        return original(key, *args)

                    with patch.object(simulator.work, operation, checked):
                        with self.assertRaises(RuntimeError) as caught:
                            reach_phase.phase_bounds(simulator, F(0), F(1))
                    self.assertIs(caught.exception, marker)
                    self.assertIs(simulator.work.callback_error, marker)
                    self.assertEqual(simulator.state, previous)
                    for key, value in retained.items():
                        self.assertIs(simulator.work._cache[key], value)
                    if not warm:
                        self.assertFalse(any(node_key(key) for key in simulator.work._cache))
                    actual = reach_phase.phase_bounds(simulator, F(0), F(1))
                with node_mode(False), uncached_phases(simulator.work):
                    expected = reach_phase.phase_bounds(simulator, F(0), F(1))
                self.assertEqual(actual, expected)

    def test_boolean_or_wide_source_operands_keep_original_fallbacks(self):
        for field in ("axis", "position"):
            outcomes = []
            for enabled in (True, False):
                _, simulator = prepared()
                with node_mode(True):
                    reach_phase.phase_bounds(simulator, F(0), F(1))
                joint = simulator.model.joints[simulator.model.actions["reach"].reach.elbow]
                if field == "axis":
                    joint.axis = (False, 0.0, 1.0)
                else:
                    site = simulator.model.sites[joint.child]
                    site.pose = replace(site.pose, position=(False, 0.0, 0.0))
                with node_mode(enabled):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        reach_phase.phase_bounds(simulator, F(0), F(1))
                outcomes.append((caught.exception.reach_code, caught.exception.details))
            self.assertEqual(outcomes[0], outcomes[1])

        results = []
        for enabled in (True, False):
            _, simulator = prepared()
            incoming = simulator._incoming(simulator.state)
            root = next(path for path in simulator.model.objects if path not in incoming)
            simulator.state.positions[root] = (F(1 << 2300), F(0), F(0))
            simulator.state.ideal_positions[root] = (F(1 << 2300), F(0), F(0))
            with node_mode(enabled):
                results.append(reach_phase.phase_bounds(simulator, F(0), F(1)))
            self.assertFalse(any(node_key(key) for key in simulator.work._cache))
        self.assertEqual(results[0], results[1])

    def test_small_capacity_evicts_templates_without_retaining_an_extra_numeric_store(self):
        outputs = []
        for capacity in (1, 8, 256):
            with self.subTest(capacity=capacity):
                _, simulator = prepared(capacity=capacity)
                original = simulator.work.remember

                def remember(key, value):
                    original(key, value)
                    self.assertLessEqual(len(simulator.work._cache), capacity)

                with node_mode(True), patch.object(simulator.work, "remember", remember):
                    outputs.append(reach_phase.phase_bounds(simulator, F(0), F(1), recording_proof=True))
                self.assertLessEqual(len(simulator.work._cache), capacity)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])


if __name__ == "__main__":
    unittest.main()
