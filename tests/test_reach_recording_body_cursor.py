"""Complete carrier cursors obey their source proof and existing error budget."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F
from types import MappingProxyType
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_conformance import validate_reach_export
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork, float_bits
from ontokin.reach_phase import phase_bounds
from ontokin.reach_pose import AXIS_ERROR, PRODUCT_ERROR, ReachPoseOps, RotationValue
from ontokin.reach_runtime import ReachSimulator
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_pose import independent_oracle
from test_reach_recording_sampler import simulator


def matrix(rotation):
    w, x, y, z = rotation.components
    n = w*w+x*x+y*y+z*z
    return ((1-2*(y*y+z*z)/n, 2*(x*y-w*z)/n, 2*(x*z+w*y)/n),
            (2*(x*y+w*z)/n, 1-2*(x*x+z*z)/n, 2*(y*z-w*x)/n),
            (2*(x*z-w*y)/n, 2*(y*z+w*x)/n, 1-2*(x*x+y*y)/n))


def arguments(**changes):
    result = dict(phase_start=F(0), phase_end=F(2), context=object(),
                  path="carrier", proof_token=object(), max_steps=10000)
    result.update(changes)
    return result


def phase(sim, start=F(0), end=F(2)):
    return phase_bounds(sim, start, end, sim.state,
                        recording_proof=True)["recording_angular_proof"]


class ReachRecordingBodyCursorTests(unittest.TestCase):
    def test_body_postmultiplication_matches_independent_matrix_enclosures(self):
        oracle = independent_oracle()
        for axis in range(3):
            ops = ReachPoseOps(ReachExecutionWork())
            rate, args = F(7, 4), arguments()
            unit = tuple(F(index == axis) for index in range(3))
            # This exact quarter-turn does not commute with every body axis.
            initial = ops._rotation((1, 1, 0, 0))
            times = [F(index, 32) for index in range(8, 25)]
            times += [times[-1], F(9, 16), F(1, 3)]
            for index, time in enumerate(times):
                def seed():
                    return ops.multiply(initial, ops.axis_rotation(unit, rate*time))
                actual = ops.recording_body_orientation(seed, axis, rate, time, **args)
                sine, cosine = oracle.Context(192, oracle.Budget()).sincos_point(rate*time)
                s, c = (sine.lo, sine.hi), (cosine.lo, cosine.hi)
                neg = lambda v: (-v[1], -v[0])
                zero, one = (F(0), F(0)), (F(1), F(1))
                expected = [[zero for _ in range(3)] for _ in range(3)]
                expected[axis][axis] = one
                first, second = (axis+1) % 3, (axis+2) % 3
                expected[first][first] = expected[second][second] = c
                expected[first][second], expected[second][first] = neg(s), s
                # Left multiplication by the initial exact Rx(pi/2).
                expected = (expected[0], [neg(v) for v in expected[2]], expected[1])
                allowance = AXIS_ERROR+4*PRODUCT_ERROR+index*(AXIS_ERROR+2*PRODUCT_ERROR)
                for actual_row, expected_row in zip(matrix(actual), expected):
                    for value, enclosure in zip(actual_row, expected_row):
                        self.assertLessEqual(value-allowance, enclosure[0])
                        self.assertGreaterEqual(value+allowance, enclosure[1])
            self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))
            self.assertLessEqual(len(ops.work._cache), 256)

    def test_repeated_complete_steps_reuse_one_increment_and_zero_rate_keeps_seed(self):
        ops = ReachPoseOps(ReachExecutionWork())
        args, seeds = arguments(), []
        current = F(0)
        def seed():
            seeds.append(current)
            return ops.axis_rotation((0, 0, 1), current)
        for current in (F(0), F(1, 8)):
            ops.recording_body_orientation(seed, 2, F(1), current, **args)
        with patch.object(ops, "axis_rotation", side_effect=AssertionError("recomputed increment")):
            current = F(1, 4)
            ops.recording_body_orientation(seed, 2, F(1), current, **args)
        self.assertEqual(seeds, [F(0)])
        self.assertEqual(ops.work.counts["recording_body_increment_reuse"], 1)
        fixed = RotationValue((F(1), F(1), F(0), F(0)))
        args = arguments()
        for current in (F(0), F(1, 3), F(1), F(2)):
            self.assertIs(ops.recording_body_orientation(lambda: fixed, None, F(0), current, **args), fixed)

    def test_new_proof_context_cap_ceiling_and_eviction_require_direct_seeds(self):
        ops = ReachPoseOps(ReachExecutionWork(max_cache_entries=3))
        args, seeds = arguments(max_steps=2), []
        current = F(0)
        def seed():
            seeds.append(current)
            return RotationValue((F(1), F(0), F(0), F(0)))
        for current in (F(0), F(1, 8), F(1, 4)):
            ops.recording_body_orientation(seed, None, F(0), current, **args)
        self.assertEqual(seeds, [F(0), F(1, 4)])
        for changes in ({"proof_token": object()}, {"context": object()}, {"phase_end": F(3)}):
            before = len(seeds)
            ops.recording_body_orientation(seed, None, F(0), current, **{**args, **changes})
            self.assertEqual(len(seeds), before+1)
        for index in range(3):
            ops.work.remember(("eviction", index), index)
        before = len(seeds)
        ops.recording_body_orientation(seed, None, F(0), current, **args)
        self.assertEqual(len(seeds), before+1)
        ops.work.max_operand_bits = 128
        for current in (F(1, 2), F(3, 4)):
            before = len(seeds)
            ops.recording_body_orientation(seed, None, F(0), current, **args)
            self.assertEqual(len(seeds), before+1)
        self.assertLessEqual(len(ops.work._cache), 3)

    def test_malformed_or_outside_phase_inputs_cannot_use_warm_cursor(self):
        ops, args = ReachPoseOps(ReachExecutionWork()), arguments()
        seed = lambda: RotationValue((F(1), F(0), F(0), F(0)))
        ops.recording_body_orientation(seed, 2, F(1), F(0), **args)
        for axis, rate, time, changes in (
                (True, F(1), F(0), {}), (None, F(1), F(0), {}),
                (2, False, F(0), {}), (2, float("nan"), F(0), {}),
                (2, F(1), F(-1, 8), {}), (2, F(1), F(3), {}),
                (2, F(1), F(0), {"proof_token": 1}),
                (2, F(1), F(0), {"max_steps": 10001})):
            with self.subTest(axis=axis, rate=rate, time=time, changes=changes):
                with self.assertRaises(ReachAdmissionError):
                    ops.recording_body_orientation(seed, axis, rate, time, **{**args, **changes})
        with self.assertRaises(ReachAdmissionError):
            ops.recording_body_orientation(lambda: (1., 0., 0., 0.), 2, F(1), F(0), **arguments())

    def test_cap_change_during_reuse_reexecutes_direct_source_preflights(self):
        cold = ReachPoseOps(ReachExecutionWork(max_operand_bits=128))
        with self.assertRaises(ReachAdmissionError) as expected:
            cold.axis_rotation((0, 0, 1), F(1, 4))
        for checkpoint in ("recording_body_increment_reuse", "quaternion_sparse_check", "cache_insert"):
            ops, args = ReachPoseOps(ReachExecutionWork()), arguments()
            current = F(0)
            def seed():
                return ops.axis_rotation((0, 0, 1), current)
            for current in (F(0), F(1, 8)):
                ops.recording_body_orientation(seed, 2, F(1), current, **args)
            charge = ops.work.charge
            observed = []
            def narrow(kind="checkpoint", amount=1):
                if kind == checkpoint:
                    observed.append(kind)
                    ops.work.external_check = lambda: setattr(ops.work, "max_operand_bits", 128)
                return charge(kind, amount)
            current = F(1, 4)
            with self.subTest(checkpoint=checkpoint), patch.object(ops.work, "charge", side_effect=narrow):
                with self.assertRaises(ReachAdmissionError) as actual:
                    ops.recording_body_orientation(seed, 2, F(1), current, **args)
            self.assertTrue(observed)
            self.assertEqual(actual.exception.details, expected.exception.details)

    def test_cancelled_increment_preserves_the_last_complete_cursor(self):
        ops, args = ReachPoseOps(ReachExecutionWork()), arguments()
        current = F(0)
        def seed():
            return ops.axis_rotation((0, 0, 1), current)
        for current in (F(0), F(1, 8)):
            ops.recording_body_orientation(seed, 2, F(1), current, **args)
        key = next(key for key in ops.work._cache if "recording_rotation_cursor" in key)
        saved = ops.work._cache[key]
        marker, charge = RuntimeError("cancel carrier increment"), ops.work.charge
        def cancel(kind="checkpoint", amount=1):
            if kind == "recording_body_increment_reuse":
                ops.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        current = F(1, 4)
        with patch.object(ops.work, "charge", side_effect=cancel), self.assertRaises(RuntimeError) as actual:
            ops.recording_body_orientation(seed, 2, F(1), current, **args)
        self.assertIs(actual.exception, marker)
        self.assertIs(ops.work.callback_error, marker)
        self.assertEqual(ops.work._cache[key], saved)

    def test_runtime_seeds_complete_private_ancestry_and_keeps_source_graph_direct(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        proof = phase(sim)
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame")
        source = sim._kinematics(F(1, 8), sim.state)
        source_cache = sim._pose_cache
        original = sim.pose_ops.recording_body_orientation
        seeds = []
        def observed(seed, *args, **kwargs):
            def checked_seed():
                with patch.object(sim.pose_ops, "recording_axis_rotation", side_effect=AssertionError("incremental seed")), \
                        patch.object(sim.pose_ops, "recording_advance_orientation", side_effect=AssertionError("incremental ancestor")):
                    value = seed()
                self.assertIs(type(value), RotationValue)
                self.assertIsNone(value.frozen_projection)
                seeds.append(value)
                return value
            return original(checked_seed, *args, **kwargs)
        context = object()
        with patch.object(sim.pose_ops, "recording_body_orientation", side_effect=observed):
            for time in (F(1, 4), F(3, 8), F(1, 2)):
                sim.recording_frames(time, sim.state, paths, recording_context=context,
                                     recording_angular_proof=proof)
        self.assertGreaterEqual(len(seeds), 2)
        self.assertGreater(sim.work.counts.get("recording_body_increment_reuse", 0), 0)
        self.assertIs(sim._pose_cache, source_cache)
        self.assertIs(sim._kinematics(F(1, 8), sim.state)[1], source[1])
        with patch.object(sim.pose_ops, "recording_body_orientation", side_effect=AssertionError("source cursor")):
            sim._kinematics(F(3, 4), sim.state)
            sim.recording_frames(F(3, 4), sim.state, paths)
        self.assertLessEqual(len(sim.work._cache), 256)

    def test_stale_root_and_joint_witnesses_fall_back_without_ancestor_authority(self):
        for changed in ("root", "initial", "ideal_initial", "status", "axis"):
            sim = simulator("P16")
            sim.advance(F(0), "after")
            proof, context = phase(sim), object()
            paths = ("rig.arm.forearm.frame",)
            sim.recording_frames(F(1, 8), sim.state, paths, recording_context=context,
                                 recording_angular_proof=proof)
            active = sim.state.actions[sim.state.claims[("rig.arm.shoulder", "coordinate")]]
            if changed == "root":
                sim.state.orientations["rig"] = (0., 0., 0., 1.)
            elif changed == "initial":
                active.initial = (active.initial[0]+0.125, active.initial[1])
            elif changed == "ideal_initial":
                active.ideal_initial = (active.ideal_initial[0]+F(1, 8), active.ideal_initial[1])
            elif changed == "status":
                active.status = "paused"
            else:
                old = sim.model.joints["rig.arm.shoulder"]
                sim.model.joints["rig.arm.shoulder"] = replace(old, axis=(0., 0., -1.))
            with self.subTest(changed=changed), patch.object(sim.pose_ops, "recording_body_orientation",
                    side_effect=AssertionError("stale complete law")):
                actual = sim.recording_frames(F(1, 4), sim.state, paths, recording_context=object(),
                                              recording_angular_proof=proof)
                expected = sim.recording_frames(F(1, 4), sim.state, paths, recording_context=object())
            self.assertEqual(actual, expected)

    def test_missing_proof_nonzero_child_offset_and_no_trig_count_use_existing_sampler(self):
        for condition in ("missing", "child_offset", "trig_count"):
            sim = simulator("P16")
            sim.advance(F(0), "after")
            if condition == "child_offset":
                old = sim.model.sites["rig.arm.upper.base"]
                sim.model.sites["rig.arm.upper.base"] = replace(old,
                    pose=replace(old.pose, position=(0.125, 0., 0.)))
            proof = phase(sim)
            if condition != "child_offset":
                records = dict(proof.frames)
                name = "rig.arm.upper.frame"
                if condition == "missing":
                    del records[name]
                else:
                    records[name] = replace(records[name], trig_count=0)
                proof = replace(proof, frames=MappingProxyType(records))
            with self.subTest(condition=condition), patch.object(sim.pose_ops, "recording_body_orientation",
                    side_effect=AssertionError("unsupported carrier law")):
                sim.recording_frames(F(1, 4), sim.state, ("rig.arm.upper.frame",),
                    recording_context=object(), recording_angular_proof=proof)

    def test_cancelled_runtime_cursor_leaves_source_state_and_full_graph_unchanged(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        proof, context = phase(sim), object()
        paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame")
        before = deepcopy(sim.state)
        source_cache = sim._pose_cache
        for time in (F(0), F(1, 8)):
            sim.recording_frames(time, sim.state, paths, recording_context=context,
                                 recording_angular_proof=proof)
        marker, charge = RuntimeError("cancel carrier graph"), sim.work.charge
        def cancel(kind="checkpoint", amount=1):
            if kind == "recording_body_increment_reuse":
                sim.work.external_check = lambda: (_ for _ in ()).throw(marker)
            return charge(kind, amount)
        with patch.object(sim.work, "charge", side_effect=cancel), self.assertRaises(RuntimeError) as actual:
            sim.recording_frames(F(1, 4), sim.state, paths, recording_context=context,
                                 recording_angular_proof=proof)
        self.assertIs(actual.exception, marker)
        self.assertEqual(sim.state, before)
        self.assertIs(sim._pose_cache, source_cache)

    def test_complete_glbs_pass_independent_analytic_byte_checks_with_writer_disabled(self):
        for case, end in (("P01", F(3)), ("P09", F(1, 4)), ("P16", F(1, 4))):
            built = compile_construction(source_case(case))
            options = ExportOptions(end=end, fps=1, helpers=False)
            result = export_glb(built.model, options=options,
                target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertGreater(built.reach_work.counts.get("recording_body_direct_seed", 0), 0)
            self.assertGreater(built.reach_work.counts.get("recording_rotation_step", 0), 0)
            self.assertLessEqual(built.budget.operations, 100000)
            independent_work = ReachExecutionWork()
            with self.subTest(case=case), \
                    patch.object(ReachPoseOps, "axis_rotation", side_effect=AssertionError("writer axis")), \
                    patch.object(ReachPoseOps, "recording_body_orientation", side_effect=AssertionError("writer cursor")), \
                    patch.object(ReachSimulator, "_resolve_kinematics", side_effect=AssertionError("writer graph")):
                checked = validate_reach_export(result.data, built.model, options=options, work=independent_work)
            self.assertEqual(checked["status"], "passed")
            self.assertLessEqual(independent_work.operations, 100000)
            decoded = read_glb(result.data)
            metadata = decoded.document["extras"]["ontokin"]
            certificates = metadata["reach_quantization"]["interval_certificates"]
            times = decoded.document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]
            self.assertEqual(len(certificates), (len(times)-1)*len(decoded.document["nodes"]))

    def test_prepopulated_projection_retains_signed_zero_only_for_equal_operands(self):
        ops = ReachPoseOps(ReachExecutionWork())
        untouched = replace(ops.make_recording((F(0), F(2), F(3))),
                            _projection={"position": (-0., 2., 3.)})
        self.assertEqual(float_bits(untouched.position[0]), float_bits(-0.))
        old = replace(ops.make_recording((F(0), F(2), F(3))),
                      _projection={"position": (-0., 2., 3.)})
        changed = replace(old, exact_position=(F(4), F(5), F(6)))
        self.assertEqual(changed.position, (4., 5., 6.))
        self.assertEqual(old.position, (0., 2., 3.))


if __name__ == "__main__":
    unittest.main()
