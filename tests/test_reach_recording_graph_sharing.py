"""Same-clock carrier aliases retain complete independent source witnesses."""
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_phase
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import RecordingAngularFrame, _AxialRate, phase_bounds
from ontokin.reach_recording_fast import sample_bounded_frames, sample_certified_frames, RecordingRoundingAmbiguity
from test_reach_recording_sampler import simulator


def frozen(value):
    if value is None:
        return ("none",)
    if type(value) is str:
        return ("string", value)
    if type(value) is tuple:
        return ("tuple", tuple(frozen(part) for part in value))
    if type(value) is float:
        return ("binary64", value.hex())
    if type(value) is F:
        return ("rational", value.numerator, value.denominator)
    return ("integer", value)


def records(prefix="arm", offset=0.0):
    zero, unit = frozen((0.0, 0.0, 0.0)), frozen((1.0, 0.0, 0.0, 0.0))
    root = RecordingAngularFrame(_AxialRate(None, F(0)), None,
        ("root", "rig", frozen("kinematic"), zero, zero, unit,
         frozen(None), frozen(F(0)), None, None), 0)
    site = RecordingAngularFrame(_AxialRate(None, F(0)), "rig.frame",
        ("site", prefix + ".mount", frozen("rig"),
         (frozen((0.0, offset, 0.0)), unit)), 0)
    law = (frozen(prefix + ".reach"), frozen("reach_planar"), frozen(prefix),
           frozen(F(2)), frozen(None), frozen(None),
           frozen((prefix + ".shoulder", prefix + ".elbow")), frozen("running"),
           frozen((0.0, 0.0)), frozen((F(0), F(0))),
           frozen((0.25, 0.75)), frozen(F(0)), frozen(F(0)), frozen(F(0)), frozen(None))
    joint = RecordingAngularFrame(_AxialRate(2, F(1, 8)), prefix + ".mount.frame",
        ("joint", prefix + ".shoulder", frozen("hinge"), frozen(prefix + ".mount"),
         frozen(prefix + ".upper.base"), frozen((0.0, 0.0, 1.0)),
         frozen((-3.0, 3.0)), frozen(prefix + ".upper"), (zero, unit), law,
         frozen(0.0), frozen(F(0))), 1)
    return root, site, joint


def recipe(chain):
    parent = None
    work = ReachExecutionWork()
    for record in chain:
        parent = reach_phase._recording_orientation_recipe(record, parent, work=work)
    return parent


def prepared_many():
    sim = simulator("P23")
    sim.advance(F(0), "after")
    names = ("first", *(f"part-{index:02}" for index in range(1, 9)))
    paths = tuple(f'rig.arms["{name}"].{part}.frame'
                  for name in names for part in ("upper", "forearm"))
    phase = phase_bounds(sim, F(0), F(2), sim.state,
                         selected_frames=paths, recording_proof=True)
    return sim, paths, phase


def sample(sim, paths, phase, *, time=F(1, 8), context=None):
    return sample_bounded_frames(sim, time, sim.state, paths,
        context=context or object(), moving_frames=sim.recording_moving_frames(sim.state, paths),
        phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
        recording_angular_proof=phase["recording_angular_proof"])


class ReachRecordingGraphSharingTests(unittest.TestCase):
    def test_ordered_numeric_recipe_removes_only_names_and_outer_translations(self):
        original = records()
        self.assertEqual(recipe(original), recipe(records("other", 7.75)))
        root, site, joint = original
        for index in (2, 5, 6, 7, 8):
            witness = list(root.witness)
            witness[index] = ("different", witness[index])
            with self.subTest(root_field=index):
                self.assertNotEqual(recipe(original), recipe((replace(root, witness=tuple(witness)), site, joint)))
        for index in (2, 5, 6, 8, 10, 11):
            witness = list(joint.witness)
            witness[index] = ((witness[index][0], frozen((0.0, 0.0, 0.0, 1.0)))
                              if index == 8 else ("different", witness[index]))
            with self.subTest(joint_field=index):
                self.assertNotEqual(recipe(original), recipe((root, site, replace(joint, witness=tuple(witness)))))
        for index in (1, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14):
            law = list(joint.witness[9])
            law[index] = ("different", law[index])
            witness = (*joint.witness[:9], tuple(law), *joint.witness[10:])
            with self.subTest(law_field=index):
                self.assertNotEqual(recipe(original), recipe((root, site, replace(joint, witness=witness))))
        for changed in (replace(joint, trig_count=2), replace(joint, rate=_AxialRate(2, F(-1, 8)))):
            self.assertNotEqual(recipe(original), recipe((root, site, changed)))

    def test_reach_pair_selection_and_ordered_fixed_rotation_remain_distinct(self):
        root, site, shoulder = records()
        witness = list(shoulder.witness)
        witness[1] = "arm.elbow"
        elbow = replace(shoulder, witness=tuple(witness))
        self.assertNotEqual(recipe((root, site, shoulder)), recipe((root, site, elbow)))
        changed_site = replace(site, witness=(*site.witness[:3],
            (site.witness[3][0], frozen((0.0, 0.0, 0.0, 1.0)))))
        self.assertNotEqual(recipe((root, site, shoulder)), recipe((root, changed_site, shoulder)))
        unsupported = replace(shoulder, witness=("unrecognized",))
        self.assertIsNone(recipe((root, site, unsupported)))

    def test_live_domain_and_cancellation_are_checked_before_recipe_reuse(self):
        record = records()[0]
        for narrow in (False, True):
            work = ReachExecutionWork()
            marker = RuntimeError("cancel carrier recipe")
            def check():
                if narrow:
                    work.max_operand_bits = 128
                else:
                    raise marker
            work.external_check = check
            if narrow:
                self.assertIsNone(reach_phase._recording_orientation_recipe(record, None, work=work))
            else:
                with self.assertRaises(RuntimeError) as caught:
                    reach_phase._recording_orientation_recipe(record, None, work=work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
            self.assertFalse(work._cache)

    def test_actual_repeated_arms_keep_native_samples_and_reduce_shared_work(self):
        results = []
        for enabled in (False, True):
            sim, paths, phase = prepared_many()
            original = deepcopy(sim.state)
            before = sim.work.operations
            mode = nullcontext() if enabled else patch.object(reach_phase, "_recording_orientation_recipe", return_value=None)
            with mode:
                result = sample(sim, paths, phase)
            results.append((result.frames, result.excess_by_frame, sim.work.operations - before,
                            sim.work.counts.get("recording_body_shared_orientation", 0),
                            sim.work.counts.get("recording_float_body_direct_seed", 0)))
            self.assertEqual(sim.state, original)
            self.assertLessEqual(sim.work.operations, 100000)
            self.assertLessEqual(len(sim.work._cache), 256)
        self.assertEqual(results[0][:2], results[1][:2])
        self.assertLess(results[1][2], results[0][2])
        self.assertEqual(results[0][3], 0)
        self.assertGreater(results[1][3], 0)
        self.assertLess(results[1][4], results[0][4])

    def test_only_used_body_ancestry_is_witnessed(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        paths = ("rig.frame", "rig.arm.upper.frame", "rig.arm.forearm.frame",
                 "rig.arm.forearm.tip.frame", "rig.tool.frame", "payload.frame")
        phase = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)
        with patch.object(reach_phase, "current_recording_angular_witness",
                          wraps=reach_phase.current_recording_angular_witness) as witnessed:
            sample(sim, paths, phase)
        calls = [(call.args[2], call.args[3]) for call in witnessed.call_args_list]
        self.assertIn(("joint", "rig.arm.elbow"), calls)
        self.assertNotIn(("root", "payload"), calls)
        self.assertNotIn(("site", "rig.arm.forearm.tip"), calls)
        self.assertNotIn(("follow", "rig.tool"), calls)
        self.assertEqual(len(calls), len(set(calls)))

    def test_shared_receiver_final_checkpoint_keeps_cancellation_and_cache_order(self):
        sim, paths, phase = prepared_many()
        marker, snapshots = RuntimeError("cancel shared carrier"), []
        charge = sim.work.charge
        def charged(kind="checkpoint", amount=1):
            if kind == "recording_body_shared_orientation":
                snapshots.append(tuple(sim.work._cache.items()))
                sim.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(sim.work, "charge", side_effect=charged):
            with self.assertRaises(RuntimeError) as caught:
                sample(sim, paths, phase)
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(tuple(sim.work._cache.items()), snapshots[0])

    def test_shared_receiver_rejects_changed_source_after_the_last_callback(self):
        sim, paths, phase = prepared_many()
        original, snapshots = deepcopy(sim.state), []
        charge = sim.work.charge
        def changed():
            for runtime in sim.state.actions.values():
                if type(runtime.initial) is tuple and len(runtime.initial) == 2:
                    runtime.initial = (runtime.initial[0] + 0.125, runtime.initial[1])
        def charged(kind="checkpoint", amount=1):
            if kind == "recording_body_shared_orientation" and not snapshots:
                snapshots.append(tuple(sim.work._cache.items()))
                sim.work.external_check = changed
            return charge(kind, amount)
        try:
            with patch.object(sim.work, "charge", side_effect=charged):
                with self.assertRaises(ReachAdmissionError) as caught:
                    sample(sim, paths, phase)
            self.assertEqual(caught.exception.reach_code, "reach_domain")
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(tuple(sim.work._cache.items()), snapshots[0])
        finally:
            sim.state = original

    def test_strict_stored_cell_diagnostic_does_not_use_shared_body_recipes(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame")
        phase = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)
        with patch.object(reach_phase, "_recording_orientation_recipe",
                          side_effect=AssertionError("strict cells keep local factors")):
            try:
                sample_certified_frames(sim, F(1, 8), sim.state, paths, context=object(),
                    moving_frames=sim.recording_moving_frames(sim.state, paths),
                    phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                    recording_angular_proof=phase["recording_angular_proof"])
            except RecordingRoundingAmbiguity:
                pass


if __name__ == "__main__":
    unittest.main()
