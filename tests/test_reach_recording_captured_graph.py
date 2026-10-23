"""Complete frozen native graphs retain live final source and cache admission."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import struct
from types import MappingProxyType
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.reach_numeric import ReachAdmissionError
from ontokin.reach_phase import phase_bounds
from test_reach_recording_sampler import simulator


def prepared(count=17, *, distinct=False):
    sim = simulator("P23")
    sim.advance(F(0), "after")
    names = ("first", *(f"part-{index:02}" for index in range(1, count)))
    paths = tuple(f'rig.arms["{name}"].forearm.frame' for name in names)
    if distinct:
        joint = sim.model.joints[paths[-1].removesuffix(".forearm.frame") + ".elbow"]
        child = sim.model.sites[joint.child]
        child.pose = replace(child.pose, rotation=(0.0, 0.0, 0.0, 1.0))
    phase = phase_bounds(sim, F(0), F(2), sim.state,
                         selected_frames=paths, recording_proof=True)
    moving = sim.recording_moving_frames(sim.state, paths)
    return sim, paths, phase, moving, object()


def sample(prepared, time=F(1, 8)):
    sim, paths, phase, moving, context = prepared
    return fast.sample_bounded_frames(sim, time, sim.state, paths, context=context,
        moving_frames=moving, phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
        recording_angular_proof=phase["recording_angular_proof"])


def body_cache(work):
    return {key: value for key, value in work._cache.items()
            if len(key) > 2 and key[1:3] == ("recording_rotation_cursor", "certified_binary64_body")}


def bits(result):
    return tuple((path, struct.pack("<7d", *pose.position, *pose.orientation))
                 for path, pose in result.frames.items()), result.excess_by_frame


def graph_entry(work):
    return next((key, value) for key, value in work._cache.items() if type(value) is capture._Graph)


class ReachRecordingCapturedGraphTests(unittest.TestCase):
    def test_cold_and_warm_complete_graphs_preserve_all_bits_and_enclosures(self):
        results = []
        for enabled in (False, True):
            fixture = prepared(distinct=True)
            sim = fixture[0]
            original, before = deepcopy(sim.state), sim.work.operations
            mode = nullcontext() if enabled else patch.object(capture, "sample_captured_carriers", return_value=None)
            with mode:
                values = [bits(sample(fixture, time)) for time in (F(1, 8), F(1, 4), F(3, 8))]
            results.append((values, sim.work.operations - before))
            self.assertEqual(sim.state, original)
            self.assertLessEqual(len(sim.work._cache), 256)
            self.assertEqual(sim.work.max_operations, 100000)
            self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
        self.assertEqual(results[0][0], results[1][0])
        self.assertLess(results[1][1], results[0][1])

    def test_warm_capture_checks_every_actual_source_record_once(self):
        fixture = prepared()
        sample(fixture)
        sim, paths = fixture[:2]
        graph = graph_entry(sim.work)[1]
        with patch.object(capture, "_current_recording_angular_witness",
                          wraps=capture._current_recording_angular_witness) as checked, \
                patch.object(fast, "_planar_paths", side_effect=AssertionError("captured graph has no live prepass")), \
                patch.object(sim, "_resolve_kinematics", side_effect=AssertionError("captured inputs supply every node")):
            value = sample(fixture, F(1, 4))
        receipts = [(call.args[2], call.args[3]) for call in checked.call_args_list]
        self.assertEqual(len(receipts), len(graph.nodes))
        self.assertEqual(len(receipts), len(set(receipts)))
        self.assertEqual(set(value.frames), set(paths))
        for path in paths:
            prefix = path.removesuffix(".forearm.frame")
            self.assertIn(("joint", prefix + ".elbow"), receipts)
            self.assertIn(("joint", prefix + ".shoulder"), receipts)
        self.assertIn(("root", "rig"), receipts)

    def test_final_receipt_rejects_static_source_claim_identity_and_topology_changes(self):
        for kind in ("root", "static_leaf", "static_law", "moving_law", "claim", "identity",
                     "typed_identity", "joint_parent", "unused_edge", "typed_unused_edge",
                     "new_edge", "grip", "state"):
            with self.subTest(kind=kind):
                fixture = prepared()
                sample(fixture)
                sim, paths = fixture[:2]
                before = body_cache(sim.work)
                prefix = paths[-1].removesuffix(".forearm.frame")
                elbow = sim.model.joints[prefix + ".elbow"]
                claimant = sim.state.claims[(prefix + ".elbow", "coordinate")]
                changed = []
                def mutate():
                    if changed:
                        return
                    changed.append(True)
                    if kind == "root":
                        sim.state.positions["rig"] = (0.125, 0.0, 0.0)
                    elif kind == "static_leaf":
                        site = sim.model.sites[elbow.parent]
                        site.pose = replace(site.pose, position=(1.25, 0.0, 0.0))
                    elif kind in {"static_law", "moving_law"}:
                        active = sim.state.actions[claimant]
                        index = 0 if kind == "static_law" else 1
                        active.initial = tuple(value + 0.125 if slot == index else value
                                               for slot, value in enumerate(active.initial))
                    elif kind == "claim":
                        del sim.state.claims[(prefix + ".elbow", "coordinate")]
                    elif kind == "identity":
                        stem = paths[-1][:-6]
                        sim.model.objects[stem] = replace(sim.model.objects[stem])
                    elif kind == "typed_identity":
                        class Name(str):
                            pass
                        current = sim.model.objects[paths[-1][:-6]]
                        current.element_id = tuple(Name(part) for part in current.element_id)
                    elif kind == "joint_parent":
                        elbow.parent = sim.model.joints[prefix + ".shoulder"].parent
                    elif kind == "unused_edge":
                        unused = sim.model.joints['rig.arms["part-31"].elbow']
                        unused.parent = elbow.parent
                    elif kind == "typed_unused_edge":
                        class Name(str):
                            pass
                        unused = sim.model.joints['rig.arms["part-31"].elbow']
                        unused.parent = Name(unused.parent)
                    elif kind == "new_edge":
                        sim.model.follows["injected"] = replace(next(iter(sim.model.follows.values())), path="injected")
                    elif kind == "grip":
                        sim.state.active_grips.add("changed grip activity")
                    else:
                        sim.state = deepcopy(sim.state)
                original = sim.work.remember_batch
                def publish(entries, *, admission):
                    sim.work.external_check = mutate
                    return original(entries, admission=admission)
                with patch.object(sim.work, "remember_batch", side_effect=publish):
                    with self.assertRaises(ReachAdmissionError) as caught:
                        sample(fixture, F(1, 4))
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertTrue(changed)
                self.assertEqual(body_cache(sim.work), before)

    def test_temporary_source_replacements_cannot_enter_cold_parent_calculations(self):
        expected = None
        for mutate in (False, True):
            fixture = prepared()
            sample(fixture)
            sim, paths = fixture[:2]
            key, _ = graph_entry(sim.work)
            # Evict numerical results through the ordinary bounded API while
            # retaining the structural input graph. Its value contains no pose.
            for index in range(256):
                sim.work.remember(("captured eviction", index), object())
                sim.work.lookup(key)
            prefix = paths[-1].removesuffix(".forearm.frame")
            joint = sim.model.joints[prefix + ".elbow"]
            site = sim.model.sites[joint.parent]
            claimant = sim.state.claims[(prefix + ".elbow", "coordinate")]
            active = sim.state.actions[claimant]
            original_position, original_pose, original_initial = sim.state.positions["rig"], site.pose, active.initial
            changed, restored = [], []
            charge = sim.work.charge
            def charged(kind="checkpoint", amount=1):
                if mutate and kind == "recording_float_domain" and not changed:
                    changed.append(True)
                    sim.state.positions["rig"] = (0.5, 0.0, 0.0)
                    site.pose = replace(site.pose, position=(2.0, 0.0, 0.0))
                    active.initial = (0.25, 0.75)
                if changed and kind == "recording_angular_witness_guard" and not restored:
                    restored.append(True)
                    sim.state.positions["rig"], site.pose, active.initial = original_position, original_pose, original_initial
                return charge(kind, amount)
            with patch.object(sim.work, "charge", side_effect=charged):
                result = bits(sample(fixture, F(1, 4)))
            if mutate:
                self.assertTrue(changed and restored)
                self.assertEqual(result, expected)
            else:
                expected = result

    def test_proof_backing_map_changes_are_bound_at_final_admission(self):
        for restore in (False, True):
            with self.subTest(restore=restore):
                fixture = prepared()
                sim, paths, phase = fixture[:3]
                proof = phase["recording_angular_proof"]
                records = dict(proof.frames)
                phase["recording_angular_proof"] = replace(proof, frames=MappingProxyType(records))
                sample(fixture)
                saved = records[paths[-1]]
                before = body_cache(sim.work)
                charge, changed = sim.work.charge, []
                def charged(kind="checkpoint", amount=1):
                    if kind == "recording_body_shared_orientation" and not changed:
                        changed.append(True)
                        records[paths[-1]] = replace(saved, rate=replace(saved.rate, value=F(999)))
                    if restore and kind == "recording_angular_witness_guard":
                        records[paths[-1]] = saved
                    return charge(kind, amount)
                with patch.object(sim.work, "charge", side_effect=charged):
                    if restore:
                        result = sample(fixture, F(1, 4))
                        self.assertEqual(len(result.frames), len(paths))
                    else:
                        with self.assertRaises(ReachAdmissionError) as caught:
                            sample(fixture, F(1, 4))
                        self.assertEqual(caught.exception.reach_code, "reach_domain")
                        self.assertEqual(body_cache(sim.work), before)
                self.assertTrue(changed)

    def test_cancellation_and_narrow_caps_never_publish_a_partial_cursor_group(self):
        for final in ("recording_body_cursor_stage", "recording_body_shared_orientation",
                      "recording_captured_topology_guard", "cache_batch_domain", "cache_promote"):
            for cancel in (False, True):
                with self.subTest(final=final, cancel=cancel):
                    fixture = prepared(distinct=True)
                    sample(fixture)
                    sim = fixture[0]
                    before = body_cache(sim.work)
                    self.assertEqual(len(before), 2)
                    marker = ReachAdmissionError("reach_resource", "original captured cancellation")
                    charge, armed, hit = sim.work.charge, [], []
                    publish = sim.work.remember_batch
                    def charged(kind="checkpoint", amount=1):
                        if kind == final and (final != "cache_promote" or armed) and not hit:
                            hit.append(True)
                            def reject():
                                sim.work.max_operand_bits = 128
                                if cancel:
                                    raise marker
                            sim.work.external_check = reject
                        return charge(kind, amount)
                    def publishing(entries, *, admission):
                        armed.append(True)
                        return publish(entries, admission=admission)
                    with patch.object(sim.work, "charge", side_effect=charged), \
                            patch.object(sim.work, "remember_batch", side_effect=publishing):
                        with self.assertRaises(ReachAdmissionError if cancel else fast.RecordingRoundingAmbiguity) as caught:
                            sample(fixture, F(1, 4))
                    self.assertTrue(hit)
                    if cancel:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(sim.work.callback_error, marker)
                        self.assertEqual(body_cache(sim.work), before)
                    else:
                        self.assertTrue(all(key in before and before[key] is value
                                            for key, value in body_cache(sim.work).items()))

    def test_restored_cap_and_changed_capacity_keep_existing_complete_cursors(self):
        for change in ("restore_operand", "capacity"):
            with self.subTest(change=change):
                fixture = prepared(distinct=True)
                sample(fixture)
                sim = fixture[0]
                before, events = body_cache(sim.work), []
                publish, charge = sim.work.remember_batch, sim.work.charge
                armed = []
                def charged(kind="checkpoint", amount=1):
                    if armed and kind == "cache_insert" and not events:
                        events.append(kind)
                        if change == "restore_operand":
                            sim.work.max_operand_bits = 128
                        else:
                            sim.work.max_cache_entries = 1
                    elif armed and kind == "cache_operand_scope_reset" and change == "restore_operand":
                        events.append(kind)
                        sim.work.max_operand_bits = 32768
                    return charge(kind, amount)
                def publishing(entries, *, admission):
                    self.assertEqual(len(entries), 2)
                    armed.append(True)
                    return publish(entries, admission=admission)
                with patch.object(sim.work, "charge", side_effect=charged), \
                        patch.object(sim.work, "remember_batch", side_effect=publishing):
                    result = sample(fixture, F(1, 4))
                self.assertTrue(events)
                self.assertEqual(len(result.frames), len(fixture[1]))
                self.assertEqual(body_cache(sim.work), before)

    def test_reentrant_sampling_keeps_the_inner_complete_cursor_group(self):
        fixture = prepared(distinct=True)
        sample(fixture)
        sim, paths = fixture[:2]
        charge, inside, retained = sim.work.charge, [], []
        def charged(kind="checkpoint", amount=1):
            if kind == "recording_body_shared_orientation" and not inside:
                inside.append(True)
                inner = sample(fixture, F(3, 8))
                self.assertEqual(len(inner.frames), len(paths))
                retained.append(body_cache(sim.work))
            return charge(kind, amount)
        with patch.object(sim.work, "charge", side_effect=charged):
            outer = sample(fixture, F(1, 4))
        self.assertEqual(len(outer.frames), len(paths))
        self.assertEqual(len(retained), 1)
        self.assertEqual(body_cache(sim.work), retained[0])
        self.assertLessEqual(len(sim.work._cache), 256)

    def test_structural_graph_holds_inputs_and_all_numeric_results_use_the_lru(self):
        fixture = prepared()
        sample(fixture)
        sim = fixture[0]
        _, graph = graph_entry(sim.work)
        self.assertIsInstance(graph.nodes, MappingProxyType)
        self.assertTrue(any(len(key) > 1 and key[1] == "captured_constant_parent"
                            and type(value) is fast._FloatPose for key, value in sim.work._cache.items()))
        for node in graph.nodes.values():
            pending = list(node.operands)
            while pending:
                value = pending.pop()
                self.assertNotIsInstance(value, (fast._FloatPose, fast._FloatRotation))
                if type(value) is tuple:
                    pending.extend(value)
        self.assertLessEqual(len(sim.work._cache), sim.work.max_cache_entries)

    def test_mixed_and_strict_diagnostic_paths_retain_the_existing_sampler(self):
        fixture = prepared()
        sim, paths, phase, moving, context = fixture
        mixed = (paths[0].replace(".forearm.frame", ".upper.frame"), *paths[1:])
        with patch.object(capture, "_Publication", side_effect=AssertionError("mixed capture must decline")):
            result = fast.sample_bounded_frames(sim, F(1, 8), sim.state, mixed, context=context,
                moving_frames=moving, phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                recording_angular_proof=phase["recording_angular_proof"])
        self.assertEqual(set(result.frames), set(mixed))
        with patch.object(capture, "sample_captured_carriers", side_effect=AssertionError("strict diagnostic is separate")):
            try:
                fast.sample_certified_frames(sim, F(1, 4), sim.state, paths, context=object(),
                    moving_frames=moving, phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                    recording_angular_proof=phase["recording_angular_proof"])
            except fast.RecordingRoundingAmbiguity:
                pass


if __name__ == "__main__":
    unittest.main()
