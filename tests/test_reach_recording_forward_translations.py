"""Captured forward leaves preserve the original native sequence and receipts."""
from contextlib import nullcontext
from dataclasses import replace
from fractions import Fraction as F
import struct
import unittest
from unittest.mock import patch

from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.model import Pose
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import RecordingAngularFrame, _AxialRate
from ontokin.reach_pose import ReachPoseOps
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recording_captured_graph import bits
from test_reach_recording_captured_roots import begin, cursors, prepared


def native(**settings):
    return fast.Binary64RecordingOps(ReachPoseOps(ReachExecutionWork()),
                                    cartesian_axes=True, **settings)


def record(local, kind="site"):
    pose = tuple(("tuple", tuple(("binary64", value.hex()) for value in vector))
                 for vector in (local.position, local.rotation))
    names = (("string", "source"),) if kind == "site" else (
        ("string", "source.frame"), ("string", "child"))
    return RecordingAngularFrame(_AxialRate(None, F(0)), "source.frame",
                                 (kind, "leaf", *names, pose), 0)


def parent(axis=2, *, identity=False, depth=7):
    rotation = (fast._FloatRotation(1.0, -0.0, False, True, axis) if identity else
                fast._FloatRotation(0.8, 0.6, False, False, axis))
    return fast._FloatPose((0.125, -0.25, 0.0), rotation, (False, False, True), depth)


def ordinary(ops, base, local):
    return ops.compose_recording_fast(base, ops.recording_constant_pose(local,
        build=lambda value, inverse=False: (ops.source_ops.inverse_pose(value) if inverse
                                           else ops.source_ops.constant_pose(value))))


def pose_bits(value):
    return (struct.pack("<3d", *value.position), fast.Binary64RecordingOps._rotation_bits(value.rotation),
            value.zeros, value.depth)


def live_leaf(simulator, node):
    return (simulator.model.sites[node.path].pose if node.kind == "site"
            else simulator.model.follows[node.path].offset)


class ReachRecordingForwardTranslationTests(unittest.TestCase):
    def test_all_cartesian_axes_zero_signs_and_finite_offset_shapes_keep_exact_bits(self):
        positions = ((0.0, -0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                     (0.25, -0.75, 0.5), (float.fromhex("0x0.0000000000001p-1022"), 0.0, 0.0),
                     (float(2**500), 0.0, -0.0))
        for axis in range(3):
            for identity in (False, True):
                for position in positions:
                    with self.subTest(axis=axis, identity=identity, position=position):
                        ops, base = native(), parent(axis, identity=identity)
                        local = Pose(position=position, rotation=(1.0, -0.0, 0.0, -0.0))
                        expected = ordinary(ops, base, local)
                        actual = ops.recording_forward_translation(base, local, record(local))
                        self.assertIsNotNone(actual)
                        self.assertEqual(pose_bits(actual), pose_bits(expected))
                        self.assertEqual(actual.depth, base.depth + 1)
                        if identity:
                            self.assertEqual(actual.rotation.axis, 2)
                            self.assertFalse(actual.rotation.zero_w)
                        self.assertIsNone(ops.work._source_after_charge)

    def test_only_two_unused_domain_entries_disappear_and_native_operations_stay_ordered(self):
        results = []
        local, base = Pose(position=(0.25, -0.75, 0.5)), parent()
        for enabled in (False, True):
            ops, calls = native(), []
            # Read the charged sequence at the original callback; no arithmetic
            # helper or charge dispatch is replaced for this observation.
            def observe():
                calls.append(tuple(ops.work.counts.items()))
            ops.work.external_check = observe
            result = (ops.recording_forward_translation(base, local, record(local)) if enabled
                      else ordinary(ops, base, local))
            results.append((pose_bits(result), dict(ops.work.counts), calls))
            self.assertEqual(ops.work.operations, len(calls))
            self.assertEqual(ops.work.operations, sum(ops.work.counts.values()))
        self.assertEqual(results[0][0], results[1][0])
        original, actual = results[0][1], results[1][1]
        self.assertEqual(original.pop("recording_float_domain"), 3)
        self.assertEqual(actual.pop("recording_float_domain"), 1)
        self.assertEqual(original, actual)
        def arithmetic(sequence):
            return [tuple((name, count) for name, count in row if name != "recording_float_domain")
                    for row in sequence if any(name != "recording_float_domain" for name, _ in row)]
        # The final old product checkpoint duplicates the already complete
        # arithmetic receipt. Remove only that final redundant observation.
        self.assertEqual(arithmetic(results[0][2])[:-1], arithmetic(results[1][2]))

    def test_actual_original_numeric_cache_contents_and_capacity_are_unchanged(self):
        ops = native()
        for index in range(256):
            ops.work.remember(("forward-existing", index), F(index, 257))
        before = tuple(ops.work._cache.items())
        counts = dict(ops.work.counts)
        local = Pose(position=(0.25, -0.75, 0.5))
        for _ in range(3):
            self.assertIsNotNone(ops.recording_forward_translation(parent(), local, record(local, "follow")))
        after = tuple(ops.work._cache.items())
        self.assertEqual([key for key, _ in before], [key for key, _ in after])
        self.assertTrue(all(old is new for (_, old), (_, new) in zip(before, after)))
        self.assertEqual(ops.work.counts.get("cache_lookup", 0), counts.get("cache_lookup", 0))
        self.assertEqual(ops.work.counts.get("cache_insert", 0), counts.get("cache_insert", 0))
        self.assertEqual(ops.work.max_cache_entries, 256)
        self.assertEqual(ops.work.max_operand_bits, MAX_OPERAND_BITS)
        self.assertEqual(ops.work.max_operations, 100000)

    def test_literal_typed_source_witness_rejects_foreign_equality_and_inverse_shapes(self):
        ops, local = native(), Pose(position=(0.25, 0.0, 0.0))
        expected = record(local)
        class ForeignEqual:
            def __eq__(self, other):
                raise AssertionError("foreign source equality must not execute")
        for witness in (
            ("joint", *expected.witness[1:]),
            (ForeignEqual(), *expected.witness[1:]),
            (*expected.witness[:2], ("string", ForeignEqual()), expected.witness[-1]),
            (*expected.witness[:-1], (("tuple", (("binary64", ForeignEqual()),) * 3),
                                     expected.witness[-1][1])),
            (*expected.witness[:-1], (expected.witness[-1][0],
                                     ("tuple", (("integer", "1"),) * 4))),
        ):
            with self.subTest(witness_type=type(witness[0])):
                self.assertIsNone(ops.recording_forward_translation(parent(), local,
                    replace(expected, witness=witness)))
        for rotation in ((-1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)):
            changed = replace(local, rotation=rotation)
            self.assertIsNone(ops.recording_forward_translation(parent(), changed, record(changed)))
        for position in ((F(1, 4), 0.0, 0.0), (True, 0.0, 0.0), [0.25, 0.0, 0.0]):
            self.assertIsNone(ops.recording_forward_translation(parent(), replace(local, position=position), expected))
        self.assertEqual(ops.work.operations, 0)

    def test_unsupported_parent_depth_and_position_keep_the_existing_builder(self):
        local = Pose(position=(1.0, 0.0, 0.0))
        ops = native()
        maximum = ops.recording_forward_translation(parent(depth=63), local, record(local))
        self.assertEqual(maximum.depth, 64)
        self.assertEqual(pose_bits(maximum), pose_bits(ordinary(ops, parent(depth=63), local)))
        for base in (parent(depth=64), replace(parent(), depth=True),
                     replace(parent(), position=(float("inf"), 0.0, 0.0)),
                     replace(parent(), position=(float(2**501), 0.0, 0.0)),
                     replace(parent(), zeros=(1, False, False))):
            self.assertIsNone(ops.recording_forward_translation(base, local, record(local)))
        with self.assertRaises(fast._UnsupportedPlanar):
            ordinary(ops, parent(depth=64), local)

    def test_shared_arithmetic_narrow_caps_and_existing_observers_remain_ordinary(self):
        local, base = Pose(position=(1.0, 0.0, 0.0)), parent()
        shared = native(share_arithmetic=True)
        self.assertIsNone(shared.recording_forward_translation(base, local, record(local)))
        self.assertEqual(shared.work.operations, 0)
        ops = native()
        ops.work.max_operand_bits = 1074
        self.assertIsNone(ops.recording_forward_translation(base, local, record(local)))
        with self.assertRaises(fast._UnsupportedPlanar):
            ordinary(ops, base, local)
        ops, observed = native(), []
        observer = lambda: observed.append(True)
        ops.work._source_after_charge = observer
        self.assertIsNone(ops.recording_forward_translation(base, local, record(local)))
        ordinary(ops, base, local)
        self.assertEqual(len(observed), ops.work.operations)
        self.assertIs(ops.work._source_after_charge, observer)

    def test_initial_helper_dispatch_replacement_is_not_silently_bypassed(self):
        ops, local = native(), Pose(position=(1.0, 0.0, 0.0))
        marker = RuntimeError("original composition observer")
        def refuse(*args):
            raise marker
        with patch.object(ops, "compose_recording_fast", side_effect=refuse):
            self.assertIsNone(ops.recording_forward_translation(parent(), local, record(local)))
            with self.assertRaises(RuntimeError) as caught:
                ordinary(ops, parent(), local)
        self.assertIs(caught.exception, marker)
        self.assertIsNone(ops.work._source_after_charge)

    def test_warm_parent_leaf_and_record_mutations_reject_before_the_next_operation(self):
        for change in ("parent_position", "parent_rotation", "parent_flags", "local", "record"):
            with self.subTest(change=change):
                ops, base, local = native(), parent(), Pose(position=(0.25, -0.75, 0.5))
                source, calls = record(local), []
                self.assertIsNotNone(ops.recording_forward_translation(base, local, source))
                def mutate():
                    calls.append(True)
                    if len(calls) != 2:
                        return
                    if change == "parent_position":
                        object.__setattr__(base, "position", (17.0, 0.0, 0.0))
                    elif change == "parent_rotation":
                        object.__setattr__(base.rotation, "w", 0.0)
                    elif change == "parent_flags":
                        object.__setattr__(base.rotation, "zero_z", 0)
                    elif change == "local":
                        object.__setattr__(local, "position", (17.0, 0.0, 0.0))
                    else:
                        object.__setattr__(source, "witness", record(Pose()).witness)
                ops.work.external_check = mutate
                with self.assertRaises(fast._UnsupportedPlanar):
                    ops.recording_forward_translation(base, local, source)
                self.assertEqual(len(calls), 2)
                self.assertIsNone(ops.work._source_after_charge)

    def test_narrow_then_restore_cannot_hide_a_departure_between_native_callbacks(self):
        ops, base, local = native(), parent(), Pose(position=(0.25, -0.75, 0.5))
        source, calls = record(local), []
        ops.recording_forward_translation(base, local, source)
        def mutate_then_restore():
            calls.append(True)
            ops.work.max_operand_bits = 128 if len(calls) == 2 else MAX_OPERAND_BITS
        ops.work.external_check = mutate_then_restore
        try:
            with self.assertRaises(fast._UnsupportedPlanar):
                ops.recording_forward_translation(base, local, source)
            self.assertEqual(len(calls), 2)
            self.assertEqual(ops.work.max_operand_bits, 128)
            self.assertIsNone(ops.work._source_after_charge)
        finally:
            ops.work.max_operand_bits = MAX_OPERAND_BITS

    def test_owner_dispatch_and_observer_replacements_are_detected_and_not_erased(self):
        for change in ("work", "source", "source_work", "dispatch", "observer", "sharing", "selector"):
            with self.subTest(change=change):
                ops, local, calls = native(), Pose(position=(0.25, -0.75, 0.5)), []
                original_work, foreign = ops.work, lambda: None
                def mutate():
                    calls.append(True)
                    if len(calls) != 2:
                        return
                    if change == "work":
                        ops.work = ReachExecutionWork()
                    elif change == "source":
                        ops.source_ops = ReachPoseOps(original_work)
                    elif change == "source_work":
                        ops.source_ops.work = ReachExecutionWork()
                    elif change == "dispatch":
                        ops._native = foreign
                    elif change == "observer":
                        original_work._source_after_charge = foreign
                    elif change == "sharing":
                        ops.share_arithmetic = True
                    else:
                        ops.recording_cartesian_axes = False
                        ops._recording_cartesian_selector = False
                original_work.external_check = mutate
                with self.assertRaises(fast._UnsupportedPlanar):
                    ops.recording_forward_translation(parent(), local, record(local))
                self.assertEqual(len(calls), 2)
                self.assertIs(original_work._source_after_charge, foreign if change == "observer" else None)
                if change == "dispatch":
                    self.assertIs(ops._native, foreign)

    def test_original_remaining_callback_and_resource_exceptions_keep_identity(self):
        for marker in (RuntimeError("native callback"), TypeError("native callback"),
                       KeyError("native callback"), fast._UnsupportedPlanar("native callback"),
                       ReachAdmissionError("reach_resource", "native callback resource")):
            with self.subTest(marker=type(marker)):
                ops, local, calls = native(), Pose(position=(0.25, -0.75, 0.5)), []
                def refuse():
                    calls.append(True)
                    if len(calls) == 2:
                        raise marker
                ops.work.external_check = refuse
                with self.assertRaises(type(marker)) as caught:
                    ops.recording_forward_translation(parent(), local, record(local))
                self.assertIs(caught.exception, marker)
                self.assertIs(ops.work.callback_error, marker)
                self.assertEqual(len(calls), 2)
                self.assertIsNone(ops.work._source_after_charge)
        ops, local = native(), Pose(position=(0.25, -0.75, 0.5))
        ops.work.max_operations = 1
        with self.assertRaises(ReachAdmissionError) as caught:
            ops.recording_forward_translation(parent(), local, record(local))
        self.assertEqual(caught.exception.reach_code, "reach_resource")
        self.assertEqual(caught.exception.details["budget"], "max_operations")
        self.assertEqual(caught.exception.details["consumed"], 2)
        self.assertEqual(ops.work.operations, 1)
        self.assertIsNone(ops.work._source_after_charge)

    def test_original_p16_phase_bits_allowances_and_positive_work_gate(self):
        for start, end in ((F(0), F(2)), (F(2), F(3))):
            with self.subTest(start=start):
                times = tuple(start + (end - start) * F(index, 16) for index in range(1, 16))
                outcomes = []
                for enabled in (False, True):
                    fixture = prepared("P16", start, end)
                    sim = fixture[0]
                    before = sim.work.operations
                    mode = nullcontext() if enabled else patch.object(
                        fast.Binary64RecordingOps, "recording_forward_translation", return_value=None)
                    with mode:
                        phase = begin(fixture, times)
                        self.assertIsNotNone(phase)
                        values = [bits(phase.sample(time)) for time in times]
                        phase.finish()
                    outcomes.append((values, sim.work.operations - before))
                    self.assertEqual(sim.work.max_operations, 100000)
                    self.assertEqual(sim.work.max_operand_bits, MAX_OPERAND_BITS)
                    self.assertLessEqual(len(sim.work._cache), 256)
                    self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])
                print(f"P16 forward translations {start}..{end}: ordinary={outcomes[0][1]}, captured={outcomes[1][1]}")

    def test_live_forward_leaves_are_detached_before_sampling_and_temporary_edits_do_not_enter_math(self):
        times, outcomes = (F(1, 8), F(1, 4)), []
        for mutate in (False, True):
            fixture = prepared("P16", F(0), F(2))
            sim, phase = fixture[0], begin(fixture, times)
            nodes = [node for node in phase.phase.graph.nodes.values() if node.kind in {"site", "follow"}]
            self.assertTrue(nodes)
            saved = []
            for node in nodes:
                live = live_leaf(sim, node)
                self.assertIsNot(node.operands[0], live)
                saved.append((live, live.position, live.rotation))
                if mutate:
                    object.__setattr__(live, "position", (17.0, 0.0, 0.0))
                    object.__setattr__(live, "rotation", (0.0, 0.0, 0.0, 1.0))
            try:
                outcomes.append([bits(phase.sample(time)) for time in times])
            finally:
                for live, position, rotation in saved:
                    object.__setattr__(live, "position", position)
                    object.__setattr__(live, "rotation", rotation)
            phase.finish()
        self.assertEqual(*outcomes)

    def test_original_nonidentity_forward_leaf_cannot_be_promoted_by_a_transient_source_edit(self):
        times, outcomes = (F(1, 8), F(1, 4)), []
        for mutate in (False, True):
            fixture = prepared("P16", F(0), F(2))
            sim, phase = fixture[0], begin(fixture, times)
            nodes = [node for node in phase.phase.graph.nodes.values()
                     if node.kind in {"site", "follow"}
                     and node.operands[0].rotation != (1.0, 0.0, 0.0, 0.0)]
            self.assertTrue(nodes)
            saved = [(live_leaf(sim, node), live_leaf(sim, node).rotation) for node in nodes]
            if mutate:
                for live, _ in saved:
                    object.__setattr__(live, "rotation", (1.0, 0.0, 0.0, 0.0))
            try:
                outcomes.append([bits(phase.sample(time)) for time in times])
            finally:
                for live, rotation in saved:
                    object.__setattr__(live, "rotation", rotation)
            phase.finish()
        self.assertEqual(*outcomes)

    def test_persistent_source_pose_or_owner_change_rejects_the_whole_phase(self):
        for change in ("position", "rotation", "owner"):
            with self.subTest(change=change):
                fixture = prepared("P16", F(0), F(2))
                sim, phase = fixture[0], begin(fixture, (F(1, 8), F(1, 4)))
                node = next(node for node in phase.phase.graph.nodes.values() if node.kind == "site")
                phase.sample(F(1, 8))
                site = sim.model.sites[node.path]
                if change == "position":
                    site.pose = replace(site.pose, position=(17.0, 0.0, 0.0))
                elif change == "rotation":
                    site.pose = replace(site.pose, rotation=(0.0, 0.0, 0.0, 1.0))
                else:
                    site.owner = "payload"
                phase.sample(F(1, 4))
                with self.assertRaises(ReachAdmissionError) as caught:
                    phase.finish()
                self.assertEqual(caught.exception.reach_code, "reach_domain")
                self.assertFalse(cursors(sim.work))

    def test_phase_callback_marker_survives_a_simultaneous_arithmetic_owner_change(self):
        fixture = prepared("P16", F(0), F(2))
        sim, phase = fixture[0], begin(fixture, (F(1, 8), F(1, 4)))
        ops, marker, reached = phase.phase.ops, fast._UnsupportedPlanar("original callback refusal"), []
        original = ops.recording_forward_translation
        def enter(base, local, source):
            if not reached and fast._forward_source_inputs(local, source) is not None:
                reached.append(True)
                def refuse():
                    sim.work.external_check = None
                    ops.work = ReachExecutionWork()
                    raise marker
                sim.work.external_check = refuse
            return original(base, local, source)
        with patch.object(ops, "recording_forward_translation", side_effect=enter):
            with self.assertRaises(fast._UnsupportedPlanar) as caught:
                phase.sample(F(1, 8))
        self.assertIs(caught.exception, marker)
        self.assertIs(sim.work.callback_error, marker)
        self.assertEqual(reached, [True])
        self.assertIsNone(sim.work._source_after_charge)
        self.assertFalse(cursors(sim.work))

    def test_warm_phase_narrow_restore_stops_before_cursor_publication(self):
        fixture = prepared("P16", F(0), F(2))
        sim, phase = fixture[0], begin(fixture, (F(1, 8), F(1, 4)))
        phase.sample(F(1, 8))
        ops, calls, reached = phase.phase.ops, [], []
        original = ops.recording_forward_translation
        def enter(base, local, source):
            if (not reached and fast._forward_source_inputs(local, source) is not None
                    and any(local.position) and not base.rotation.zero_z):
                reached.append(True)
                def narrow_then_restore():
                    calls.append(True)
                    sim.work.max_operand_bits = 128 if len(calls) == 2 else MAX_OPERAND_BITS
                sim.work.external_check = narrow_then_restore
            return original(base, local, source)
        try:
            with patch.object(ops, "recording_forward_translation", side_effect=enter):
                with self.assertRaises(fast.RecordingRoundingAmbiguity):
                    phase.sample(F(1, 4))
            self.assertEqual(reached, [True])
            self.assertEqual(len(calls), 2)
            self.assertIsNone(sim.work._source_after_charge)
            self.assertFalse(cursors(sim.work))
        finally:
            sim.work.max_operand_bits = MAX_OPERAND_BITS

    def test_later_original_callback_on_replacement_native_work_keeps_identity(self):
        fixture = prepared("P16", F(0), F(2))
        sim, phase = fixture[0], begin(fixture, (F(1, 8), F(1, 4)))
        ops, marker, calls = phase.phase.ops, fast._UnsupportedPlanar("later original callback refusal"), []
        def later_refusal():
            calls.append("replacement")
            raise marker
        replacement = ReachExecutionWork(check=later_refusal)
        def replace_owner():
            calls.append("entry")
            sim.work.external_check = None
            ops.work = replacement
        # The entry phase-domain callback changes the owner. The next actual
        # ordinary root operation uses that work and raises the original error
        # before an optional source/owner proof can complete.
        sim.work.external_check = replace_owner
        with self.assertRaises(fast._UnsupportedPlanar) as caught:
            phase.sample(F(1, 8))
        self.assertIs(caught.exception, marker)
        self.assertIsNone(sim.work.callback_error)
        self.assertIs(replacement.callback_error, marker)
        self.assertEqual(calls, ["entry", "replacement"])
        self.assertIsNone(sim.work._source_after_charge)
        self.assertIsNone(replacement._source_after_charge)
        self.assertFalse(cursors(sim.work))

    def test_complete_actual_p16_prefix_bytes_full_validation_and_positive_saving(self):
        outcomes = []
        for enabled in (False, True):
            built = compile_construction(source_case("P16"), level="constructed")
            options = ExportOptions(end=F(1, 4), fps=1, helpers=False)
            mode = nullcontext() if enabled else patch.object(
                fast.Binary64RecordingOps, "recording_forward_translation", return_value=None)
            with mode:
                result = export_glb(built.model, options=options,
                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertLessEqual(built.budget.operations, 100000)
            outcomes.append((result.data, result.report["validation"], built.reach_work.operations))
        self.assertEqual(outcomes[0][:2], outcomes[1][:2])
        self.assertLess(outcomes[1][2], outcomes[0][2])
        print(f"P16 complete original prefix: ordinary={outcomes[0][2]}, captured={outcomes[1][2]}")


if __name__ == "__main__":
    unittest.main()
