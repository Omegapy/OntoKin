"""Native complete carriers retain independent errors, guards and source state."""
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
from types import MappingProxyType
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_conformance import validate_reach_export
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import phase_bounds
from ontokin.reach_pose import ReachPoseOps, RotationValue, UNIT
from ontokin.reach_recording_fast import (
    Binary64RecordingOps, MAX_FLOAT_ROTATION_STEPS, RecordingRoundingAmbiguity,
    _FloatPose, _FloatRotation, _UnsupportedPlanar,
    sample_bounded_frames, sample_certified_frames,
)
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_pose import independent_oracle
from test_reach_recording_sampler import simulator


def arguments(**changes):
    return dict(phase_start=F(0), phase_end=F(4), context=object(),
                path="carrier:arm", proof_token=object(), max_steps=10000) | changes


def native_ops(**work_options):
    return Binary64RecordingOps(ReachPoseOps(ReachExecutionWork(**work_options)), body_cursors=True)


def quaternion_error(left, right):
    return min(max(abs(F(a) - sign * F(b)) for a, b in zip(left, right)) for sign in (1, -1))


class ReachRecordingNativeBodyTests(unittest.TestCase):
    def test_complete_cursor_matches_independent_intervals_through_reseeds_and_reversed_clocks(self):
        native, oracle = native_ops(), independent_oracle()
        args, rate, seeds = arguments(), F(7, 4), []
        times = [F(index, 64) for index in range(1, 131)] + [F(1, 2), F(1, 2), F(11, 4)]
        for time in times:
            def seed():
                seeds.append(time)
                return native.source_ops.axis_rotation((0, 0, 1), rate * time)
            value = native.recording_body_orientation(seed, 2, rate, time, **args)
            sine, cosine = oracle.Context(192, oracle.Budget()).sincos_point(rate * time / 2)
            distance = min(max(max(abs(sign * F(actual) - interval.lo),
                                   abs(sign * F(actual) - interval.hi))
                               for actual, interval in ((value.w, cosine), (value.z, sine)))
                           for sign in (1, -1))
            self.assertLessEqual(distance, F(1, 2**41))
            self.assertFalse(value.zero_w or value.zero_z)
        self.assertEqual(seeds, [times[0], times[MAX_FLOAT_ROTATION_STEPS]])
        self.assertGreater(native.work.counts.get("recording_float_body_increment_reuse", 0), 100)
        self.assertEqual(native.work.operations, sum(native.work.counts.values()))
        self.assertLessEqual(len(native.work._cache), 256)

    def test_zero_rate_reuses_its_private_seed_and_every_cursor_identity_remains_bound(self):
        native, args, seeds = native_ops(), arguments(), []
        def seed():
            seeds.append(None)
            return RotationValue((F(1), F(0), F(0), F(1)))
        first = native.recording_body_orientation(seed, None, F(0), F(1), **args)
        with patch.object(native, "_axis_rotation", side_effect=AssertionError("zero ideal increment")), \
                patch.object(native, "_product", side_effect=AssertionError("zero ideal product")):
            for time in (F(2), F(2), F(1, 2)):
                self.assertIs(native.recording_body_orientation(seed, None, F(0), time, **args), first)
        self.assertEqual(len(seeds), 1)
        for changes in ({"context": object()}, {"path": "carrier:other"}, {"proof_token": object()},
                        {"phase_start": F(1, 4)}, {"phase_end": F(3)}, {"max_steps": 126}):
            before = len(seeds)
            native.recording_body_orientation(seed, None, F(0), F(1), **(args | changes))
            self.assertEqual(len(seeds), before + 1)
        for axis, rate in ((2, F(0)), (2, F(1))):
            before = len(seeds)
            native.recording_body_orientation(seed, axis, rate, F(1), **args)
            self.assertEqual(len(seeds), before + 1)
        self.assertLessEqual(len(native.work._cache), 256)

    def test_smaller_step_limit_and_shared_lru_eviction_force_independent_seeds(self):
        native, args, seeds = native_ops(max_cache_entries=3), arguments(max_steps=2), []
        def seed():
            seeds.append(None)
            return RotationValue(UNIT)
        for time in (F(0), F(1), F(2)):
            native.recording_body_orientation(seed, None, F(0), time, **args)
        self.assertEqual(len(seeds), 2)
        for index in range(4):
            native.work.remember(("unrelated", index), F(index))
        native.recording_body_orientation(seed, None, F(0), F(3), **args)
        self.assertEqual(len(seeds), 3)
        self.assertLessEqual(len(native.work._cache), 3)

    def test_malformed_current_inputs_and_public_seeds_cannot_use_a_warm_cursor(self):
        native, args = native_ops(), arguments()
        seed = lambda: RotationValue(UNIT)
        native.recording_body_orientation(seed, 2, F(1), F(0), **args)
        for axis, rate, time, changes in (
                (False, F(1), F(0), {}), (0, F(1), F(0), {}), (None, F(1), F(0), {}),
                (2, False, F(0), {}), (2, float("nan"), F(0), {}),
                (2, F(1), F(-1), {}), (2, F(1), F(5), {}),
                (2, F(1), F(0), {"proof_token": 1}),
                (2, F(1), F(0), {"max_steps": 10001}),
                (2, F(1 << 32768), F(0), {})):
            with self.subTest(axis=axis, time=time, changes=changes):
                with self.assertRaises((ReachAdmissionError, _UnsupportedPlanar)):
                    native.recording_body_orientation(seed, axis, rate, time, **(args | changes))
        for public in ((1.0, 0.0, 0.0, 0.0), _FloatRotation(1.0, 0.0, False, False)):
            with self.assertRaises(_UnsupportedPlanar):
                native.recording_body_orientation(lambda: public, 2, F(1), F(0), **arguments())
        with self.assertRaises(ValueError):
            Binary64RecordingOps(native.source_ops, body_cursors=1)

    def test_each_warm_callback_keeps_cap_scope_and_cancellation_identity(self):
        for checkpoint in ("cache_promote", "recording_float_body_increment_reuse",
                           "recording_float_mul", "cache_insert"):
            for narrow in (False, True):
                with self.subTest(checkpoint=checkpoint, narrow=narrow):
                    native, args = native_ops(), arguments()
                    for time in (F(0), F(1, 8)):
                        native.recording_body_orientation(
                            lambda: native.source_ops.axis_rotation((0, 0, 1), time),
                            2, F(1), time, **args)
                    key = next(key for key in native.work._cache if "certified_binary64_body" in key)
                    previous, charge = native.work._cache[key], native.work.charge
                    marker, seen = RuntimeError("cancel native complete carrier"), []
                    def interrupt(kind="checkpoint", amount=1):
                        if kind == checkpoint:
                            seen.append(kind)
                            native.work.external_check = (
                                lambda: setattr(native.work, "max_operand_bits", 128) if narrow
                                else (_ for _ in ()).throw(marker))
                        return charge(kind, amount)
                    with patch.object(native.work, "charge", side_effect=interrupt):
                        with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                            native.recording_body_orientation(
                                lambda: RotationValue(UNIT), 2, F(1), F(1, 4), **args)
                    self.assertTrue(seen)
                    if not narrow:
                        self.assertIs(caught.exception, marker)
                        self.assertIs(native.work.callback_error, marker)
                        self.assertIs(native.work._cache[key], previous)
                    elif key in native.work._cache:
                        self.assertIs(native.work._cache[key], previous)

    def test_zero_child_origin_preserves_position_flags_and_both_composition_depths(self):
        native = native_ops()
        old = _FloatRotation(0.8, 0.6, False, False)
        rotation = _FloatRotation(0.6, 0.8, False, False)
        parent = _FloatPose((1.0, 0.0, -0.0), old, (False, True, False), 62)
        with patch.object(native.source_ops, "_vector_projection", side_effect=AssertionError("same origin")):
            value = native.recording_parent_origin(parent, rotation)
        self.assertIs(value.position, parent.position)
        self.assertIs(value.zeros, parent.zeros)
        self.assertIs(value.rotation, rotation)
        self.assertEqual(value.depth, 64)
        for invalid in (replace(parent, depth=63), replace(parent, depth=True),
                        replace(parent, position=(float("nan"), 0.0, 0.0)),
                        replace(parent, position=(False, 0.0, 0.0)),
                        replace(parent, zeros=(False, 0, False))):
            with self.assertRaises(_UnsupportedPlanar):
                native.recording_parent_origin(invalid, rotation)
        native.work.max_operand_bits = 128
        with self.assertRaises(_UnsupportedPlanar):
            native.recording_parent_origin(parent, rotation)

    def test_runtime_seeds_private_complete_ancestry_without_source_or_parent_cursors(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        phase = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame")
        moving = sim.recording_moving_frames(sim.state, paths)
        source = sim._kinematics(F(1, 16), sim.state)
        before, source_cache = deepcopy(sim.state), sim._pose_cache
        original, seeds, context = Binary64RecordingOps.recording_body_orientation, [], object()
        def observed(ops, build, *args, **keywords):
            def checked_seed():
                with patch.object(sim.pose_ops, "recording_body_orientation", side_effect=AssertionError("source cursor seed")), \
                        patch.object(sim.pose_ops, "recording_axis_rotation", side_effect=AssertionError("hinge cursor seed")), \
                        patch.object(sim.pose_ops, "recording_advance_orientation", side_effect=AssertionError("ancestor cursor seed")):
                    seed = build()
                self.assertIs(type(seed), RotationValue)
                self.assertIsNone(seed.frozen_projection)
                seeds.append(seed)
                return seed
            return original(ops, checked_seed, *args, **keywords)
        with patch.object(Binary64RecordingOps, "recording_body_orientation", observed):
            for time in (F(1, 8), F(1, 4), F(3, 8), F(1, 2)):
                sample_bounded_frames(sim, time, sim.state, paths, context=context,
                    moving_frames=moving, phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                    recording_angular_proof=phase["recording_angular_proof"])
        self.assertGreaterEqual(len(seeds), 2)
        self.assertGreater(sim.work.counts.get("recording_float_body_increment_reuse", 0), 0)
        self.assertEqual(sim.state, before)
        self.assertIs(sim._pose_cache, source_cache)
        self.assertIs(sim._kinematics(F(1, 16), sim.state)[1], source[1])
        with patch.object(Binary64RecordingOps, "recording_body_orientation", side_effect=AssertionError("source native cursor")):
            sim._kinematics(F(3, 4), sim.state)
        self.assertLessEqual(len(sim.work._cache), 256)

    def test_stale_missing_and_nonzero_child_proofs_retain_local_native_sampling(self):
        for condition in ("root", "initial", "child_offset", "missing", "trig_count"):
            with self.subTest(condition=condition):
                sim = simulator("P16")
                sim.advance(F(0), "after")
                if condition == "child_offset":
                    old = sim.model.sites["rig.arm.upper.base"]
                    sim.model.sites["rig.arm.upper.base"] = replace(old,
                        pose=replace(old.pose, position=(0.125, 0.0, 0.0)))
                phase = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)
                proof = phase["recording_angular_proof"]
                if condition == "root":
                    sim.state.orientations["rig"] = (0.0, 0.0, 0.0, 1.0)
                elif condition == "initial":
                    active = sim.state.actions[sim.state.claims[("rig.arm.shoulder", "coordinate")]]
                    active.initial = (active.initial[0] + 0.125, active.initial[1])
                elif condition in ("missing", "trig_count"):
                    records = dict(proof.frames)
                    name = "rig.arm.upper.frame"
                    if condition == "missing":
                        del records[name]
                    else:
                        records[name] = replace(records[name], trig_count=0)
                    proof = replace(proof, frames=MappingProxyType(records))
                native = Binary64RecordingOps(sim.pose_ops, affine_coordinates=True, body_cursors=True)
                with patch.object(native, "recording_body_orientation", side_effect=AssertionError("ineligible native body")):
                    _, frames = sim._resolve_kinematics(F(1, 4), sim.state,
                        selected_frames=("rig.arm.upper.frame",), pose_only=True, recording_only=True,
                        recording_context=object(), recording_pose_ops=native, recording_angular_proof=proof)
                self.assertIs(type(frames["rig.arm.upper.frame"]), _FloatPose)
                self.assertGreater(sim.work.counts.get("recording_affine_clock_domain", 0), 0)

    def test_native_carrier_and_parent_offsets_stay_inside_current_source_enclosures(self):
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame",
                 "rig.tool.frame", "payload.frame")
        for start, end in ((F(0), F(2)), (F(2), F(3)), (F(3), F(4))):
            with self.subTest(start=start):
                candidate, reference = simulator("P16"), simulator("P16")
                phases, contexts = [], (object(), object())
                for sim in (candidate, reference):
                    sim.advance(start, "after")
                    phases.append(phase_bounds(sim, start, end, sim.state, recording_proof=True))
                moving = candidate.recording_moving_frames(candidate.state, paths)
                before = deepcopy(candidate.state)
                for fraction in (F(1, 8), F(1, 4), F(3, 4), F(1, 2)):
                    time = start + fraction * (end - start)
                    actual = sample_bounded_frames(candidate, time, candidate.state, paths,
                        context=contexts[0], moving_frames=moving, phase_bounds=phases[0]["frames"],
                        phase_interval=(start, end), recording_angular_proof=phases[0]["recording_angular_proof"])
                    expected = reference.recording_frames(time, reference.state, paths,
                        moving_frames=moving, recording_context=contexts[1],
                        recording_angular_proof=phases[1]["recording_angular_proof"])
                    for path in paths:
                        value, target, excess = actual.frames[path], expected[path], actual.excess_by_frame[path]
                        self.assertLessEqual(sum(abs(F(a) - F(b)) for a, b in zip(value.position, target.position)),
                                             excess.position_m)
                        self.assertLessEqual(quaternion_error(value.orientation, target.orientation),
                                             excess.quaternion_component)
                self.assertEqual(candidate.state, before)
                if start == 0:
                    self.assertGreater(candidate.work.counts.get("recording_float_body_direct_seed", 0), 0)
                else:
                    # The completed local hinges retain ordinary native
                    # factors even while the rig or released payload moves.
                    self.assertEqual(candidate.work.counts.get("recording_float_body_direct_seed", 0), 0)
                self.assertLessEqual(len(candidate.work._cache), 256)

    def test_current_hinge_selection_rebuilds_through_completion_and_release(self):
        sim = simulator("P16")
        original = sim._resolve_kinematics
        for start, end, paths, expected in (
                (F(0), F(2), ("rig.arm.upper.frame", "rig.arm.forearm.frame"), True),
                (F(2), F(3), ("rig.arm.upper.frame", "rig.arm.forearm.frame"), False),
                (F(3), F(4), ("payload.frame",), False)):
            with self.subTest(start=start):
                sim.advance(start, "after")
                phase = phase_bounds(sim, start, end, sim.state, recording_proof=True)
                moving, observed = sim.recording_moving_frames(sim.state, paths), []
                def checked(*args, **keywords):
                    native = keywords.get("recording_pose_ops")
                    if native is not None:
                        observed.append(native)
                        self.assertIs(native.recording_body_cursors, expected)
                        self.assertEqual(bool(native.recording_body_hinges), expected)
                        if not expected:
                            self.assertIsNone(keywords.get("recording_angular_proof"))
                    return original(*args, **keywords)
                with patch.object(sim, "_resolve_kinematics", side_effect=checked):
                    sample_bounded_frames(sim, start + (end - start) / 4, sim.state, paths,
                        context=object(), moving_frames=moving, phase_bounds=phase["frames"],
                        phase_interval=(start, end), recording_angular_proof=phase["recording_angular_proof"])
                self.assertTrue(observed)
                self.assertLessEqual(len(sim.work._cache), 256)

    def test_a_constant_local_hinge_retains_its_factor_when_another_hinge_varies(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        active = sim.state.actions[sim.state.claims[("rig.arm.shoulder", "coordinate")]]
        active.solution = replace(active.solution,
            target_rad=(active.initial[0], active.solution.target_rad[1]))
        phase = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame")
        moving, seen = sim.recording_moving_frames(sim.state, paths), []
        original = Binary64RecordingOps.recording_body_orientation
        def observed(native, *args, **keywords):
            seen.append(keywords["path"])
            self.assertEqual(native.recording_body_hinges, frozenset({"rig.arm.elbow"}))
            return original(native, *args, **keywords)
        with patch.object(Binary64RecordingOps, "recording_body_orientation", observed):
            actual = sample_bounded_frames(sim, F(1, 4), sim.state, paths,
                context=object(), moving_frames=moving, phase_bounds=phase["frames"],
                phase_interval=(F(0), F(2)), recording_angular_proof=phase["recording_angular_proof"])
        expected = sim.recording_frames(F(1, 4), sim.state, paths,
            moving_frames=moving, recording_context=object())
        self.assertEqual(seen, ["carrier:rig.arm.forearm"])
        for path in paths:
            value, target, excess = actual.frames[path], expected[path], actual.excess_by_frame[path]
            self.assertLessEqual(sum(abs(F(a) - F(b)) for a, b in zip(value.position, target.position)),
                                 excess.position_m)
            self.assertLessEqual(quaternion_error(value.orientation, target.orientation),
                                 excess.quaternion_component)

    def test_strict_cell_diagnostic_does_not_enable_native_complete_cursors(self):
        sim = simulator("P09")
        sim.advance(F(0), "after")
        phase = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)
        paths, observed = ("rig.arm.upper.frame", "rig.arm.forearm.frame"), []
        moving, original = sim.recording_moving_frames(sim.state, paths), sim._resolve_kinematics
        def checked(*args, **keywords):
            native = keywords.get("recording_pose_ops")
            if native is not None:
                observed.append(native)
                self.assertIs(native.recording_body_cursors, False)
                self.assertIsNone(keywords.get("recording_angular_proof"))
            return original(*args, **keywords)
        with patch.object(sim, "_resolve_kinematics", side_effect=checked), \
                patch.object(Binary64RecordingOps, "recording_body_orientation", side_effect=AssertionError("strict body")):
            try:
                sample_certified_frames(sim, F(1, 4), sim.state, paths, context=object(),
                    moving_frames=moving, phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                    recording_angular_proof=phase["recording_angular_proof"])
            except RecordingRoundingAmbiguity:
                # The diagnostic is allowed to request its ordinary phase
                # replay when exact equality of stored cells is unresolved.
                pass
        self.assertTrue(observed)

    def test_complete_carriers_avoid_actual_local_sampling_work(self):
        paths = ("rig.frame", "rig.arm.upper.frame", "rig.arm.forearm.frame",
                 "rig.arm.forearm.tip.frame", "rig.tool.frame", "payload.frame")
        costs, counters = [], []
        original = Binary64RecordingOps.__init__
        def local_only(ops, *args, **keywords):
            return original(ops, *args, **(keywords | {"body_cursors": False}))
        for enabled in (False, True):
            sim = simulator("P16")
            sim.advance(F(0), "after")
            phase = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)
            context, moving = object(), sim.recording_moving_frames(sim.state, paths)
            before = sim.work.operations
            with ExitStack() as stack:
                if not enabled:
                    stack.enter_context(patch.object(Binary64RecordingOps, "__init__", local_only))
                for index in range(1, 91):
                    sample_bounded_frames(sim, F(index, 91), sim.state, paths, context=context,
                        moving_frames=moving, phase_bounds=phase["frames"], phase_interval=(F(0), F(2)),
                        recording_angular_proof=phase["recording_angular_proof"])
            costs.append(sim.work.operations - before)
            counters.append(dict(sim.work.counts))
            self.assertLessEqual(len(sim.work._cache), 256)
        self.assertLess(costs[1], costs[0])
        self.assertLess(counters[1].get("recording_affine_clock_domain", 0),
                        counters[0].get("recording_affine_clock_domain", 0))
        self.assertGreater(counters[1].get("recording_float_body_increment_reuse", 0), 0)

    def test_complete_production_glbs_pass_independent_reader_without_writer_sampling(self):
        for case, end in (("P01", F(3)), ("P09", F(1, 4)), ("P16", F(1, 4))):
            with self.subTest(case=case):
                built = compile_construction(source_case(case))
                options = ExportOptions(end=end, fps=1, helpers=False)
                result = export_glb(built.model, options=options,
                    target_contract="ontokin.glb/0.6", work=built.reach_work)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertGreater(built.reach_work.counts.get("recording_float_body_direct_seed", 0), 0)
                self.assertGreater(built.reach_work.counts.get("recording_float_body_increment_reuse", 0), 0)
                self.assertLessEqual(built.budget.operations, 100000)
                work = ReachExecutionWork()
                with patch.object(Binary64RecordingOps, "recording_body_orientation", side_effect=AssertionError("writer native body")), \
                        patch.object(ReachPoseOps, "axis_rotation", side_effect=AssertionError("writer axis")), \
                        patch.object(ReachPoseOps, "recording_body_orientation", side_effect=AssertionError("writer body")), \
                        patch.object(ReachSimulator, "_resolve_kinematics", side_effect=AssertionError("writer graph")):
                    checked = validate_reach_export(result.data, built.model, options=options, work=work)
                self.assertEqual(checked["status"], "passed")
                self.assertLessEqual(work.operations, 100000)
                decoded = read_glb(result.data)
                metadata = decoded.document["extras"]["ontokin"]
                certificates = metadata["reach_quantization"]["interval_certificates"]
                times = decoded.document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]
                self.assertEqual(len(certificates), (len(times) - 1) * len(decoded.document["nodes"]))


if __name__ == "__main__":
    unittest.main()
