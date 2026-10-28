"""Same-traversal site reuse keeps complete source values and callback owners."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.model import ObjectModel, Pose, SceneModel, SiteModel
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, exact, float_bits
from ontokin.reach_pose import ReachPoseOps
from ontokin.reach_runtime import ReachSimulator, _ReachRunState, _SourceSiteIndex
from test_reach_phase import source
from test_reach_phase_mounts import PlanningSimulator


def harness(*, callback=None, capacity=256, position=(F(3), F(2), F(0))):
    work = ReachExecutionWork(check=callback, max_cache_entries=capacity)
    sim = object.__new__(ReachSimulator)
    sim.work, sim.pose_ops = work, ReachPoseOps(work)
    sim.model = SceneModel("module", "module", "scene", "scene", program_revision="source")
    sim.model.objects = {name: ObjectModel(name, name, "body", (name,))
                         for name in ("body", *("padding_" + str(index) for index in range(256)))}
    sim.state, sim.check = _ReachRunState(), None
    parent = sim.pose_ops.make(position=position, velocity=(F(1, 8), F(0), F(0)),
                               omega=(F(0), F(0), F(1, 4)))
    objects, frames = {"body": parent}, {"body.frame": parent}
    for name in ("first", "second"):
        path = "body." + name
        sim.model.sites[path] = SiteModel(path, ("body", name), "body",
            Pose("body.frame", (1.0, 0.0, 0.0)))
    index = _SourceSiteIndex.create(sim, sim.state, F(0), objects, frames)
    return sim, index, frames, parent


def site(index, name, *, build=None):
    current = index.model.sites["body." + name]
    parent = index.objects[current.owner]
    path = current.path + ".frame"
    local = current.pose
    if build is None:
        build = lambda: index.simulator._pose_slot(path, (parent, local),
            lambda: index.ops.compose(parent, index.simulator._constant_pose(local)))
    value = index.pose(path, current, parent, local, build)
    index.frames[path] = value
    return value


def public_bits(value):
    return tuple(tuple(float_bits(part) for part in getattr(value, field))
                 for field in ("position", "orientation", "velocity", "omega"))


class SourceChargeObserverTests(unittest.TestCase):
    def test_default_and_observed_charge_keep_callback_owner_counts_and_order(self):
        calls = []
        work = ReachExecutionWork()
        def check():
            self.assertIs(work.external_check, check)
            calls.append(("callback", work.operations))
        def observed():
            calls.append(("observer", work.operations))
        work.external_check = check
        work.charge("plain", 2)
        self.assertEqual(calls, [("callback", 0), ("callback", 1)])
        calls.clear()
        work._source_after_charge = observed
        work.charge("observed", 2)
        self.assertEqual(calls, [("callback", 2), ("observer", 3),
                                 ("callback", 3), ("observer", 4)])
        self.assertEqual(work.counts, {"plain": 2, "observed": 2})

    def test_callback_and_original_resource_failure_precede_the_observer(self):
        marker = RuntimeError("original caller failure")
        work = ReachExecutionWork(max_operations=1)
        observed = []
        work._source_after_charge = lambda: observed.append(work.operations)
        work.charge("first")
        with self.assertRaises(ReachAdmissionError) as caught:
            work.charge("exhausted")
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertIsNone(work.callback_error)
        self.assertEqual(observed, [1])
        def check():
            raise marker
        work.external_check = check
        with self.assertRaises(RuntimeError) as caught:
            work.charge("cancelled")
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(observed, [1])
        self.assertEqual(work.counts, {"first": 1})

    def test_each_amount_member_captures_its_observer_before_the_original_callback(self):
        calls = []
        work = ReachExecutionWork()
        def first():
            calls.append("first")
        def replacement():
            calls.append("replacement")
        def check():
            work._source_after_charge = replacement
        work.external_check, work._source_after_charge = check, first
        work.charge("many", 3)
        self.assertEqual(calls, ["first", "replacement", "replacement"])
        self.assertIs(work._source_after_charge, replacement)
        self.assertEqual(work.operations, 3)


class SourceSiteIndexTests(unittest.TestCase):
    def test_same_parent_site_preserves_all_numeric_fields_and_fresh_projection_ownership(self):
        sim, index, frames, parent = harness()
        first = site(index, "first")
        expected = public_bits(first)
        second = site(index, "second")
        self.assertEqual(second, first)
        self.assertEqual(public_bits(second), expected)
        self.assertIsNot(second, first)
        self.assertIsNot(second._projection, first._projection)
        self.assertIsNot(second._projection_domains, first._projection_domains)
        self.assertIsNot(second.rotation, first.rotation)
        self.assertEqual(sim.work.counts["source_site_reuse"], 1)
        self.assertLessEqual(len(sim.work._cache), 256)
        self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))

    def test_identity_site_still_composes_its_own_rounding_allowances(self):
        sim, index, _, parent = harness()
        for current in sim.model.sites.values():
            current.pose = Pose("body.frame")
        first, second = site(index, "first"), site(index, "second")
        self.assertEqual(first, second)
        self.assertGreater(second.position_error_m, parent.position_error_m)
        self.assertNotEqual(second, parent)
        self.assertEqual(sim.work.counts["source_site_reuse"], 1)

    def test_different_local_frame_position_rotation_and_signed_zero_keep_original_builds(self):
        variants = (Pose("other.frame", (1.0, 0.0, 0.0)),
                    Pose("body.frame", (2.0, 0.0, 0.0)),
                    Pose("body.frame", (1.0, -0.0, 0.0)),
                    Pose("body.frame", (1.0, 0.0, 0.0), (0.5, 0.5, 0.5, 0.5)))
        for local in variants:
            with self.subTest(local=local):
                sim, index, _, parent = harness()
                site(index, "first")
                sim.model.sites["body.second"].pose = local
                actual = site(index, "second")
                expected = sim.pose_ops.compose(parent, sim._constant_pose(local))
                self.assertEqual(actual, expected)
                self.assertNotIn("source_site_reuse", sim.work.counts)

    def test_equal_but_distinct_required_parent_cannot_use_another_parent_receipt(self):
        sim, index, frames, parent = harness()
        site(index, "first")
        other = replace(parent, _projection={}, _projection_domains={})
        index.objects["body"] = other
        frames["body.frame"] = other
        actual = site(index, "second")
        self.assertEqual(actual, sim.pose_ops.compose(other, sim._constant_pose(sim.model.sites["body.second"].pose)))
        self.assertNotIn("source_site_reuse", sim.work.counts)

    def test_malformed_local_values_and_wide_operands_retain_original_admission(self):
        sim, index, _, _ = harness()
        sim.model.sites["body.second"].pose = Pose("body.frame", (False, 0.0, 0.0))
        with self.assertRaises(ReachAdmissionError) as caught:
            site(index, "second")
        self.assertEqual(caught.exception.reach_code, "reach_domain")
        self.assertFalse(index.entries)
        sim, index, _, parent = harness(position=(F(1 << 600), F(0), F(0)))
        actual = site(index, "first")
        self.assertEqual(actual, sim.pose_ops.compose(parent, sim._constant_pose(sim.model.sites["body.first"].pose)))
        self.assertFalse(index.entries)
        sim.work.max_operand_bits = 64
        with self.assertRaises(ReachAdmissionError) as caught:
            site(index, "second")
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")

    def test_index_cap_and_foreign_or_small_domains_do_not_enlarge_numeric_storage(self):
        sim, index, frames, parent = harness(capacity=2)
        for ordinal in range(5):
            name = "extra_" + str(ordinal)
            path = "body." + name
            sim.model.sites[path] = SiteModel(path, ("body", name), "body",
                                             Pose("body.frame", (float(ordinal + 2), 0.0, 0.0)))
        # The fixed native specimen is complete before its traversal begins.
        index = _SourceSiteIndex.create(sim, sim.state, F(0), index.objects, frames)
        for name in ("first", "extra_0", "extra_1", "extra_2", "extra_3", "extra_4", "second"):
            site(index, name)
            self.assertLessEqual(len(index.entries), 2)
            self.assertLessEqual(len(sim.work._cache), 2)
        self.assertEqual(sim.work.counts["source_site_reuse"], 1)
        foreign = lambda: None
        sim.work._source_after_charge = foreign
        self.assertIsNone(_SourceSiteIndex.create(sim, sim.state, F(0), index.objects, frames))
        self.assertIs(sim.work._source_after_charge, foreign)
        sim.work._source_after_charge = None
        sim.model.objects = {"body": sim.model.objects["body"]}
        self.assertIsNone(_SourceSiteIndex.create(sim, sim.state, F(0), index.objects, frames))

    def test_cache_eviction_needs_the_live_required_frame_and_never_recovers_from_a_seal(self):
        for mutation in ("cache_only", "remove_frame", "equal_replacement"):
            with self.subTest(mutation=mutation):
                sim, index, frames, _ = harness()
                first = site(index, "first")
                sim.work._cache.clear()
                if mutation == "remove_frame":
                    del frames["body.first.frame"]
                elif mutation == "equal_replacement":
                    frames["body.first.frame"] = replace(first, _projection={}, _projection_domains={})
                if mutation == "cache_only":
                    self.assertEqual(site(index, "second"), first)
                else:
                    with self.assertRaises(ReachAdmissionError) as caught:
                        site(index, "second")
                    self.assertEqual(caught.exception.reach_code, "reach_domain")
                    self.assertNotIn("body.second.frame", frames)
                self.assertIsNone(sim.work._source_after_charge)

    def test_changed_private_parent_or_required_result_is_rejected_after_last_callback(self):
        for field in ("parent_position", "result_position", "result_rotation", "result_error", "result_rate"):
            for at in (1, 2):
                with self.subTest(field=field, callback=at):
                    armed, calls, altered = [False], [0], []
                    def check():
                        if armed[0]:
                            calls[0] += 1
                            if calls[0] == at:
                                value = {"parent_position": parent.exact_position[0],
                                    "result_position": first.exact_position[0],
                                    "result_rotation": first.rotation.components[0],
                                    "result_error": first.position_error_m,
                                    "result_rate": first.exact_velocity[0]}[field]
                                altered.append((value, value.numerator))
                                object.__setattr__(value, "_numerator", value.numerator + 1)
                    sim, index, frames, parent = harness(callback=check)
                    first = site(index, "first")
                    armed[0] = True
                    try:
                        with self.assertRaises(ReachAdmissionError) as caught:
                            site(index, "second")
                        self.assertEqual(caught.exception.reach_code, "reach_domain")
                        self.assertEqual(calls[0], at)
                        self.assertNotIn("body.second.frame", frames)
                        self.assertIsNone(sim.work._source_after_charge)
                    finally:
                        for value, numerator in altered:
                            object.__setattr__(value, "_numerator", numerator)

    def test_changed_source_owner_pose_and_revision_cannot_publish_a_duplicate(self):
        for mutation in ("pose", "owner", "source_record", "revision"):
            with self.subTest(mutation=mutation):
                armed = [False]
                def check():
                    if armed[0]:
                        self.assertIs(sim.work.external_check, check)
                        armed[0] = False
                        if mutation == "pose":
                            current.pose = replace(current.pose, position=(2.0, 0.0, 0.0))
                        elif mutation == "owner":
                            current.owner = "padding_0"
                        elif mutation == "source_record":
                            sim.model.sites[current.path] = replace(current)
                        else:
                            sim.model.program_revision = "changed"
                sim, index, frames, _ = harness(callback=check)
                first = site(index, "first")
                current = sim.model.sites["body.second"]
                armed[0] = True
                with self.assertRaises(ReachAdmissionError) as caught:
                    site(index, "second")
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertIs(frames["body.first.frame"], first)
                self.assertNotIn("body.second.frame", frames)

    def test_lazy_or_changed_representative_projection_maps_are_never_copied_to_the_target(self):
        sim, index, _, _ = harness()
        first = site(index, "first")
        expected = public_bits(first)
        first._projection["position"] = (999.0, 999.0, 999.0)
        second = site(index, "second")
        self.assertFalse(second._projection)
        self.assertFalse(second._projection_domains)
        self.assertEqual(public_bits(second), expected)
        self.assertEqual(sim.work.counts["source_site_reuse"], 1)

    def test_frozen_projection_and_equal_boolean_fraction_backing_cannot_match_a_result_seal(self):
        for mutation in ("frozen_projection", "boolean_backing"):
            with self.subTest(mutation=mutation):
                sim, index, frames, _ = harness()
                first = site(index, "first")
                if mutation == "frozen_projection":
                    owner, field = first.rotation, "frozen_projection"
                    old = owner.frozen_projection
                    changed = (0.0, 1.0, 0.0, 0.0)
                else:
                    owner, field = first.rotation.components[0], "_numerator"
                    old = owner.numerator
                    self.assertEqual(old, 1)
                    changed = True
                object.__setattr__(owner, field, changed)
                try:
                    with self.assertRaises(ReachAdmissionError) as caught:
                        site(index, "second")
                    self.assertEqual(caught.exception.reach_code, "reach_domain")
                    self.assertNotIn("body.second.frame", frames)
                finally:
                    object.__setattr__(owner, field, old)

    def test_work_callback_and_pose_arithmetic_owners_cannot_change_during_admission(self):
        for mutation in ("work", "ops_work", "external", "sim_check", "root_state"):
            with self.subTest(mutation=mutation):
                armed = [False]
                def check():
                    if armed[0]:
                        armed[0] = False
                        if mutation == "work":
                            sim.work = ReachExecutionWork()
                        elif mutation == "ops_work":
                            sim.pose_ops.work = ReachExecutionWork()
                        elif mutation == "external":
                            sim.work.external_check = lambda: None
                        elif mutation == "sim_check":
                            sim.check = lambda: None
                        else:
                            sim.state = _ReachRunState()
                sim, index, frames, _ = harness(callback=check)
                site(index, "first")
                armed[0] = True
                with self.assertRaises(ReachAdmissionError) as caught:
                    site(index, "second")
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertNotIn("body.second.frame", frames)
                self.assertIsNone(index.work._source_after_charge)

    def test_cap_narrow_restore_is_latched_without_replacing_the_original_builder(self):
        armed, calls = [False], [0]
        def check():
            if armed[0]:
                calls[0] += 1
                if calls[0] == 3:
                    sim.work.max_operand_bits = 32767
                elif calls[0] == 4:
                    sim.work.max_operand_bits = 32768
        sim, index, _, parent = harness(callback=check)
        armed[0] = True
        actual = site(index, "first")
        armed[0] = False
        self.assertGreater(calls[0], 4)
        self.assertEqual(sim.work.max_operand_bits, 32768)
        self.assertFalse(index.valid)
        self.assertFalse(index.entries)
        self.assertEqual(actual, sim.pose_ops.compose(parent, sim._constant_pose(sim.model.sites["body.first"].pose)))
        site(index, "second")
        self.assertNotIn("source_site_reuse", sim.work.counts)

    def test_original_operand_failure_and_callback_failures_keep_their_exact_exceptions(self):
        armed, calls, failures = [False], [0], []
        def check():
            if armed[0]:
                calls[0] += 1
                sim.work.max_operand_bits = 8 if calls[0] == 2 else 32768
        sim, index, frames, _ = harness(callback=check)
        def build():
            try:
                return exact(F(1 << 12), F(2), "mul", sim.work)
            except ReachAdmissionError as error:
                failures.append(error)
                raise
        armed[0] = True
        with self.assertRaises(ReachAdmissionError) as caught:
            site(index, "first", build=build)
        self.assertIs(caught.exception, failures[0])
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(calls[0], 2)
        self.assertIsNone(sim.work.callback_error)
        self.assertFalse(index.entries)
        self.assertNotIn("body.first.frame", frames)
        self.assertIsNone(sim.work._source_after_charge)
        for warm in (False, True):
            for marker in (RuntimeError("cancel"), ReachAdmissionError("reach_resource", "caller refusal")):
                armed = [False]
                def cancel():
                    if armed[0]:
                        raise marker
                sim, index, frames, _ = harness(callback=cancel)
                if warm:
                    site(index, "first")
                armed[0] = True
                with self.assertRaises(type(marker)) as caught:
                    site(index, "second" if warm else "first")
                self.assertIs(caught.exception, marker)
                self.assertIs(sim.work.callback_error, marker)
                self.assertIsNone(sim.work._source_after_charge)
                self.assertNotIn("body.second.frame", frames)

    def test_temporary_dispatch_change_stays_declined_and_actual_dispatch_failure_propagates(self):
        for fail in (False, True):
            armed, calls = [False], [0]
            original = ReachPoseOps._op
            marker = RuntimeError("changed arithmetic dispatch")
            def changed(ops, *args):
                if fail:
                    raise marker
                return original(ops, *args)
            def check():
                if armed[0]:
                    calls[0] += 1
                    if calls[0] == 2:
                        ReachPoseOps._op = changed
                    elif calls[0] == 3 and not fail:
                        ReachPoseOps._op = original
            sim, index, frames, _ = harness(callback=check)
            armed[0] = True
            try:
                if fail:
                    with self.assertRaises(RuntimeError) as caught:
                        site(index, "first")
                    self.assertIs(caught.exception, marker)
                    self.assertIsNone(sim.work.callback_error)
                    self.assertNotIn("body.first.frame", frames)
                else:
                    site(index, "first")
                    self.assertIs(ReachPoseOps._op, original)
                self.assertFalse(index.valid)
                self.assertFalse(index.entries)
                self.assertIsNone(sim.work._source_after_charge)
            finally:
                ReachPoseOps._op = original

    def test_reentrant_checks_keep_the_original_callback_and_foreign_observer_owner(self):
        armed, nested = [False], [False]
        def check():
            if armed[0] and not nested[0]:
                nested[0] = True
                sim.work.charge("nested")
        sim, index, frames, _ = harness(callback=check)
        armed[0] = True
        site(index, "first")
        self.assertTrue(nested[0])
        self.assertEqual(sim.work.counts["nested"], 1)
        self.assertIs(sim.work.external_check, check)
        self.assertIsNone(sim.work._source_after_charge)
        foreign = lambda: None
        armed = [False]
        def replace_hook():
            if armed[0]:
                sim.work._source_after_charge = foreign
        sim, index, frames, _ = harness(callback=replace_hook)
        armed[0] = True
        with self.assertRaises(ReachAdmissionError) as caught:
            site(index, "first")
        self.assertEqual(caught.exception.reach_code, "reach_domain")
        self.assertIs(sim.work._source_after_charge, foreign)
        self.assertIs(sim.work.external_check, replace_hook)
        self.assertFalse(index.entries)

    def test_actual_32_arm_full_source_graphs_preserve_complete_values_and_save_work(self):
        outputs, costs, reuses = [], [], []
        for enabled in (True, False):
            built = compile_construction(source("P23"))
            sim = PlanningSimulator(built.model, work=built.reach_work)
            observations = []
            def observe():
                for time in (F(0), F(2)):
                    sim.advance(time, "after")
                    objects, frames = sim._kinematics(time, sim.state)
                    observations.append((dict(objects), dict(frames),
                        copy.deepcopy(sim._pending_reach_output[3]), dict(sim.state.claims),
                        dict(sim.state.coordinates)))
            if enabled:
                observe()
            else:
                with patch.object(_SourceSiteIndex, "create", return_value=None):
                    observe()
            outputs.append(observations)
            costs.append(built.budget.operations)
            reuses.append(sim.work.counts.get("source_site_reuse", 0))
            self.assertLessEqual(len(sim.work._cache), 256)
            self.assertEqual(sim.work.max_operations, 100000)
            self.assertEqual(sim.work.max_operand_bits, 32768)
            self.assertEqual(sim.work.max_cache_entries, 256)
            self.assertIsNone(sim.work._source_after_charge)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(reuses, [480, 0])
        self.assertGreater(costs[1] - costs[0], 0)

    def test_partial_and_recording_resolvers_do_not_create_a_source_site_index(self):
        built = compile_construction(source("P01"))
        sim = PlanningSimulator(built.model, work=built.reach_work)
        target = next(iter(built.model.objects)) + ".frame"
        with patch.object(_SourceSiteIndex, "create", side_effect=AssertionError("full source only")):
            sim._resolve_kinematics(F(0), sim.state, selected_frames=(target,), pose_only=True)
            sim._resolve_kinematics(F(0), sim.state, selected_frames=(target,), pose_only=True, recording_only=True)
        self.assertNotIn("source_site_admission", sim.work.counts)


if __name__ == "__main__":
    unittest.main()
