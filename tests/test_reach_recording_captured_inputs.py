"""Copied source inputs remove exact identities without weakening admission."""
from contextlib import ExitStack
from dataclasses import replace
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_recording_capture as capture
from ontokin import reach_recording_fast as fast
from ontokin.construction import compile_construction
from ontokin.gltf import export_glb
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_pose import ReachPoseOps
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recording_captured_graph import bits
from test_reach_recording_captured_roots import begin, cursors, prepared


def native(*, cap=MAX_OPERAND_BITS):
    work = ReachExecutionWork(max_operand_bits=cap)
    return fast.Binary64RecordingOps(ReachPoseOps(work),
        constant_hinges=frozenset({"hinge:fixed"}), cartesian_axes=True)


def clock(elapsed=F(0), since=F(0), *, running=True):
    return capture._RootLaw(None, (), elapsed, since, running)


def ordinary_elapsed(law, time, ops):
    if not law.running:
        ops.work.guard(law.elapsed)
        return law.elapsed
    op = ops.source_ops._op
    return op(law.elapsed, op(time, law.running_since, "sub"), "add")


def arguments():
    return dict(context=object(), path="hinge:fixed", max_steps=10000)


def rotation_bits(value):
    return fast.Binary64RecordingOps._rotation_bits(value)


class ReachCapturedInputTests(unittest.TestCase):
    def test_exact_clock_identities_preserve_values_and_only_remove_identity_arithmetic(self):
        cases = ((F(0), F(0), F(3, 8), True, 0),
                 (F(1, 8), F(0), F(3, 8), True, 1),
                 (F(0), F(1, 8), F(3, 8), True, 1),
                 (F(1, 8), F(1, 4), F(3, 8), True, 2),
                 (F(1, 8), F(1, 4), F(-3, 8), True, 2),
                 (F(1, 8), F(1, 4), F(3, 8), False, 0))
        for elapsed, since, time, running, count in cases:
            with self.subTest(elapsed=elapsed, since=since, time=time, running=running):
                actual, original = native(), native()
                law = clock(elapsed, since, running=running)
                self.assertEqual(capture._elapsed(law, time, actual), ordinary_elapsed(law, time, original))
                self.assertEqual(actual.work.operations, count)
                self.assertEqual(actual.work.operations, sum(actual.work.counts.values()))
                self.assertEqual(actual.work.max_operand_bits, MAX_OPERAND_BITS)

    def test_large_or_narrow_clock_keeps_the_original_prospective_failure(self):
        cases = ((MAX_OPERAND_BITS, F(0), F(1 << (MAX_OPERAND_BITS - 1))),
                 (MAX_OPERAND_BITS, F(1 << (MAX_OPERAND_BITS - 1)), F(0)),
                 (8, F(0), F(127)), (8, F(127), F(0)))
        for cap, elapsed, time in cases:
            with self.subTest(cap=cap, elapsed_bits=elapsed.numerator.bit_length()):
                failures = []
                for evaluate in (ordinary_elapsed, capture._elapsed):
                    ops = native(cap=cap)
                    with self.assertRaises(ReachAdmissionError) as caught:
                        evaluate(clock(elapsed), time, ops)
                    failures.append((caught.exception.reach_code, caught.exception.details, ops.work.counts))
                self.assertEqual(*failures)
                self.assertEqual(failures[0][1]["budget"], "numeric_operand_bits")

    def test_subtraction_callback_narrowing_retains_the_following_zero_add_guard(self):
        failures = []
        for evaluate in (ordinary_elapsed, capture._elapsed):
            ops, callbacks = native(), []
            def narrow():
                callbacks.append(True)
                ops.work.max_operand_bits = 10
            ops.work.external_check = narrow
            # 127 - (-127/2) passes the original 10-bit prospective check.
            # Its 381/2 result makes the subsequent zero-add require 11 bits.
            with self.assertRaises(ReachAdmissionError) as caught:
                evaluate(clock(F(0), F(-127, 2)), F(127), ops)
            failures.append((caught.exception.details, ops.work.counts, len(callbacks)))
        self.assertEqual(*failures)
        self.assertEqual(failures[0][0]["consumed"], 11)
        self.assertEqual(failures[0][1], {"exact_sub": 1, "exact_add": 1})

    def test_remaining_clock_callback_preserves_exception_identity(self):
        ops = native()
        marker = RuntimeError("cancel remaining captured clock subtraction")
        def cancel():
            raise marker
        ops.work.external_check = cancel
        with self.assertRaises(RuntimeError) as caught:
            capture._elapsed(clock(F(0), F(1, 8)), F(3, 8), ops)
        self.assertIs(caught.exception, marker)
        self.assertIs(ops.work.callback_error, marker)

    def test_all_small_clock_operands_are_detached_before_the_first_callback(self):
        ops = native()
        law, time = clock(F(1, 8), F(1, 4)), F(3, 8)
        leaves = (law.elapsed, law.running_since, time)
        saved = [(value.numerator, value.denominator) for value in leaves]
        calls = []
        def mutate_then_restore():
            calls.append(True)
            for value, (numerator, denominator) in zip(leaves, saved):
                object.__setattr__(value, "_numerator", 99 if len(calls) == 1 else numerator)
                object.__setattr__(value, "_denominator", 1 if len(calls) == 1 else denominator)
        ops.work.external_check = mutate_then_restore
        try:
            self.assertEqual(capture._elapsed(law, time, ops), F(1, 4))
        finally:
            for value, (numerator, denominator) in zip(leaves, saved):
                object.__setattr__(value, "_numerator", numerator)
                object.__setattr__(value, "_denominator", denominator)
        self.assertEqual(len(calls), 2)

    def test_captured_root_clocks_are_copies_and_final_live_changes_still_reject(self):
        times = (F(1, 8), F(1, 4))
        outcomes = []
        for mutation in ("none", "temporary", "persistent"):
            fixture = prepared("P16", F(0), F(2))
            sim = fixture[0]
            for name in ("travel", "turn"):
                sim.state.actions[name].elapsed = F(0)
                sim.state.actions[name].running_since = F(0)
            phase = begin(fixture, times)
            root = phase.phase.graph.nodes["rig.frame"]
            originals = []
            for law, name in zip(root.operands[2:4], ("travel", "turn")):
                active = sim.state.actions[name]
                self.assertIsNot(law.elapsed, active.elapsed)
                self.assertIsNot(law.running_since, active.running_since)
                originals.extend((active.elapsed, active.running_since))
            if mutation != "none":
                for value in originals:
                    object.__setattr__(value, "_numerator", 17)
            try:
                values = [bits(phase.sample(time)) for time in times]
                if mutation == "persistent":
                    with self.assertRaises(ReachAdmissionError):
                        phase.finish()
                    self.assertFalse(cursors(sim.work))
                else:
                    for value in originals:
                        object.__setattr__(value, "_numerator", 0)
                    phase.finish()
                    outcomes.append(values)
            finally:
                for value in originals:
                    object.__setattr__(value, "_numerator", 0)
        self.assertEqual(*outcomes)

    def test_original_p16_phases_preserve_native_bits_allowances_and_bounded_work(self):
        for start, end in ((F(0), F(2)), (F(2), F(3))):
            with self.subTest(start=start):
                times = tuple(start + (end - start) * F(index, 16) for index in range(1, 16))
                outcomes = []
                for enabled in (False, True):
                    fixture = prepared("P16", start, end)
                    sim = fixture[0]
                    before = sim.work.operations
                    with ExitStack() as stack:
                        if not enabled:
                            stack.enter_context(patch.object(capture, "_elapsed", ordinary_elapsed))
                            stack.enter_context(patch.object(fast.Binary64RecordingOps,
                                "capture_constant_hinge", return_value=None))
                        phase = begin(fixture, times)
                        self.assertIsNotNone(phase)
                        values = [bits(phase.sample(time)) for time in times]
                        phase.finish()
                    outcomes.append((values, sim.work.operations - before))
                    self.assertLessEqual(len(sim.work._cache), 256)
                    self.assertEqual(sim.work.operations, sum(sim.work.counts.values()))
                    self.assertEqual(sim.work.max_operations, 100000)
                self.assertEqual(outcomes[0][0], outcomes[1][0])
                self.assertLess(outcomes[1][1], outcomes[0][1])

    def test_only_unclaimed_fixed_hinges_get_copied_constant_inputs(self):
        for start, end in ((F(0), F(2)), (F(2), F(3))):
            fixture = prepared("P16", start, end)
            phase = begin(fixture, (start + (end - start) / 4, start + (end - start) / 2))
            hinges = [node for node in phase.phase.graph.nodes.values()
                      if node.kind == "joint" and node.operands[0] == "hinge"]
            self.assertEqual(len(hinges), 2)
            for node in hinges:
                if start == 0:
                    self.assertIsNotNone(node.operands[3])
                    self.assertIsNone(node.constant_hinge)
                else:
                    self.assertIsNone(node.operands[3])
                    self.assertIsInstance(node.constant_hinge, fast._CapturedConstantHinge)
                    joint = fixture[0].model.joints[node.path]
                    self.assertIsNot(node.operands[2], fixture[0].model.sites[joint.child].pose)

    def test_one_shot_capture_callback_errors_are_not_structural_fallback(self):
        for kind in (TypeError, KeyError, AttributeError, IndexError):
            with self.subTest(kind=kind.__name__):
                fixture = prepared("P16", F(2), F(3))
                sim = fixture[0]
                marker, reached = kind("original fixed-input capture refusal"), []
                original = fast.Binary64RecordingOps.capture_constant_hinge
                def checked(ops, *args):
                    if not reached:
                        reached.append(True)
                        previous = ops.work.external_check
                        def refuse_once():
                            ops.work.external_check = previous
                            raise marker
                        ops.work.external_check = refuse_once
                    return original(ops, *args)
                with patch.object(fast.Binary64RecordingOps, "capture_constant_hinge", checked):
                    with self.assertRaises(kind) as caught:
                        begin(fixture, (F(17, 8), F(9, 4)))
                self.assertTrue(reached)
                self.assertIs(caught.exception, marker)
                self.assertIs(sim.work.callback_error, marker)
                self.assertFalse(cursors(sim.work))

    def test_fixed_kernel_matches_all_cartesian_axes_native_types_and_zero_signs(self):
        axes = ((0.0, -0.0, 1.0), (0, 0, -2), (F(1), F(0), F(0)), (0.0, -1.0, 0.0))
        for axis in axes:
            for coordinate in (0.0, -0.0, 1, F(-1, 8), 0.25):
                with self.subTest(axis=axis, coordinate=coordinate):
                    ops, args = native(), arguments()
                    inputs = ops.capture_constant_hinge(axis, coordinate)
                    self.assertIsNotNone(inputs)
                    original = ops.recording_axis_rotation(axis, coordinate, **args)
                    actual = ops.recording_captured_constant_rotation(inputs, **args)
                    self.assertEqual(rotation_bits(actual), rotation_bits(original))
                    self.assertLessEqual(len(ops.work._cache), 256)

    def test_warm_fixed_input_path_does_not_decode_or_construct_an_unused_cursor_key(self):
        ops, args = native(), arguments()
        inputs = ops.capture_constant_hinge((0.0, 0.0, 1.0), 0.25)
        expected = ops.recording_captured_constant_rotation(inputs, **args)
        before = dict(ops.work.counts)
        with patch.object(ops.source_ops, "_recording_vector", side_effect=AssertionError("fixed source vector")), \
             patch.object(fast, "rational", side_effect=AssertionError("fixed source coordinate")), \
             patch.object(ops, "_recording_cursor_key", side_effect=AssertionError("unused fixed cursor")):
            actual = ops.recording_captured_constant_rotation(inputs, **args)
        self.assertEqual(rotation_bits(actual), rotation_bits(expected))
        for name in ("exact_decode", "binary64_decode", "pose_vector_domain", "recording_rotation_cursor_domain"):
            self.assertEqual(ops.work.counts.get(name, 0), before.get(name, 0))
        self.assertEqual(ops.work.counts["cache_lookup"] - before["cache_lookup"], 1)
        self.assertEqual(ops.work.counts["cache_promote"] - before.get("cache_promote", 0), 1)

    def test_axis_projection_eviction_still_calls_the_original_source_kernel(self):
        ops, args = native(), arguments()
        inputs = ops.capture_constant_hinge((0.0, 0.0, 1.0), 0.25)
        expected = ops.recording_captured_constant_rotation(inputs, **args)
        key = next(key for key in ops.work._cache if key[:2] == (fast.METHOD, "axis_projection"))
        del ops.work._cache[key]
        with patch.object(ops.source_ops, "axis_rotation", wraps=ops.source_ops.axis_rotation) as original:
            actual = ops.recording_captured_constant_rotation(inputs, **args)
        self.assertEqual(original.call_count, 1)
        self.assertEqual(rotation_bits(actual), rotation_bits(expected))
        self.assertIn(key, ops.work._cache)
        self.assertLessEqual(len(ops.work._cache), 256)

    def test_constant_capture_detaches_source_fraction_owners_before_callbacks(self):
        ops = native()
        axis, coordinate = (F(0), F(0), F(1)), F(1, 4)
        changed = []
        def mutate():
            if not changed:
                changed.append(True)
                object.__setattr__(axis[2], "_numerator", -1)
                object.__setattr__(coordinate, "_numerator", 3)
        ops.work.external_check = mutate
        try:
            inputs = ops.capture_constant_hinge(axis, coordinate)
            self.assertEqual(inputs.axis, (F(0), F(0), F(1)))
            self.assertEqual(inputs.coordinate, F(1, 4))
            self.assertIsNot(inputs.axis[2], axis[2])
            self.assertIsNot(inputs.coordinate, coordinate)
        finally:
            object.__setattr__(axis[2], "_numerator", 1)
            object.__setattr__(coordinate, "_numerator", 1)
        self.assertTrue(changed)

    def test_transient_descriptor_mutation_cannot_change_the_detached_kernel_operands(self):
        ops, args = native(), arguments()
        inputs = ops.capture_constant_hinge((0.0, 0.0, 1.0), F(1, 4))
        expected = ops.recording_captured_constant_rotation(inputs, **args)
        callbacks = []
        def mutate_then_restore():
            callbacks.append(True)
            if len(callbacks) == 2:
                object.__setattr__(inputs.coordinate, "_numerator", 3)
                object.__setattr__(inputs.axis[2], "_numerator", -1)
            elif len(callbacks) == 3:
                object.__setattr__(inputs.coordinate, "_numerator", 1)
                object.__setattr__(inputs.axis[2], "_numerator", 1)
        ops.work.external_check = mutate_then_restore
        try:
            actual = ops.recording_captured_constant_rotation(inputs, **args)
        finally:
            object.__setattr__(inputs.coordinate, "_numerator", 1)
            object.__setattr__(inputs.axis[2], "_numerator", 1)
        self.assertEqual(len(callbacks), 3)
        self.assertEqual(rotation_bits(actual), rotation_bits(expected))

    def test_changed_descriptor_owner_or_seal_cannot_reuse_a_completed_rotation(self):
        for change in ("source", "work", "axis", "coordinate", "seal"):
            with self.subTest(change=change):
                ops, args = native(), arguments()
                inputs = ops.capture_constant_hinge((0.0, 0.0, 1.0), 0.25)
                ops.recording_captured_constant_rotation(inputs, **args)
                if change == "source":
                    inputs = replace(inputs, source_ops=object())
                elif change == "work":
                    inputs = replace(inputs, work=object())
                elif change == "axis":
                    object.__setattr__(inputs.axis[2], "_numerator", -1)
                elif change == "coordinate":
                    object.__setattr__(inputs.coordinate, "_numerator", 3)
                else:
                    inputs = replace(inputs, seal=inputs.seal[:-1] + ((1, True),))
                with self.assertRaises(fast._UnsupportedPlanar):
                    ops.recording_captured_constant_rotation(inputs, **args)

    def test_unsupported_constant_inputs_and_cursor_domains_keep_ordinary_rejection(self):
        class ForeignTuple(tuple):
            pass
        ops = native()
        for axis, coordinate in (([0.0, 0.0, 1.0], 0.25),
                                 (ForeignTuple((0, 0, 1)), F(1, 4)),
                                 ((0, 0, True), F(1, 4)),
                                 ((0, 0, 1), float("inf")),
                                 ((0, 0, 1), F(1 << 1024)),
                                 ((0, 1, 1), F(1, 4))):
            self.assertIsNone(ops.capture_constant_hinge(axis, coordinate))
        inputs = ops.capture_constant_hinge((0, 0, 1), F(1, 4))
        for changes in ({"context": None}, {"path": ""}, {"path": 1}, {"max_steps": True}, {"max_steps": 0}):
            with self.assertRaises(ReachAdmissionError) as caught:
                ops.recording_captured_constant_rotation(inputs, **(arguments() | changes))
            self.assertEqual(caught.exception.reach_code, "reach_domain")

    def test_persistent_fixed_source_changes_reject_the_complete_phase(self):
        for change in ("axis", "coordinate", "claim", "child"):
            with self.subTest(change=change):
                fixture = prepared("P16", F(2), F(3))
                sim = fixture[0]
                times = (F(17, 8), F(9, 4))
                phase = begin(fixture, times)
                node = next(node for node in phase.phase.graph.nodes.values() if node.constant_hinge is not None)
                phase.sample(times[0])
                joint = sim.model.joints[node.path]
                if change == "axis":
                    joint.axis = (0.0, 0.0, -1.0)
                elif change == "coordinate":
                    sim.state.coordinates[node.path] += 0.125
                elif change == "claim":
                    sim.state.claims[node.path, "coordinate"] = "reach"
                else:
                    child = sim.model.sites[joint.child]
                    child.pose = replace(child.pose, position=(0.125, 0.0, 0.0))
                phase.sample(times[1])
                with self.assertRaises(ReachAdmissionError):
                    phase.finish()
                self.assertFalse(cursors(sim.work))

    def test_constant_kernel_callback_cancel_or_cap_change_cannot_publish_phase_cursors(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                fixture = prepared("P16", F(2), F(3))
                sim = fixture[0]
                phase = begin(fixture, (F(17, 8), F(9, 4)))
                ops = phase.phase.ops
                original = ops.recording_captured_constant_rotation
                marker, reached = RuntimeError("cancel captured fixed hinge"), []
                def checked(inputs, **kwargs):
                    if not reached:
                        reached.append(True)
                        def callback():
                            if cancel:
                                raise marker
                            sim.work.max_operand_bits = 128
                        sim.work.external_check = callback
                    return original(inputs, **kwargs)
                with patch.object(ops, "recording_captured_constant_rotation", side_effect=checked):
                    with self.assertRaises(RuntimeError if cancel else fast.RecordingRoundingAmbiguity) as caught:
                        phase.sample(F(17, 8))
                self.assertTrue(reached)
                if cancel:
                    self.assertIs(caught.exception, marker)
                    self.assertIs(sim.work.callback_error, marker)
                self.assertFalse(cursors(sim.work))

    def test_complete_p16_prefix_bytes_and_validation_report_match_original_clock_path(self):
        outcomes = []
        for enabled in (False, True):
            built = compile_construction(source_case("P16"), level="constructed")
            options = ExportOptions(end=F(1, 4), fps=1, helpers=False)
            with ExitStack() as stack:
                if not enabled:
                    stack.enter_context(patch.object(capture, "_elapsed", ordinary_elapsed))
                    stack.enter_context(patch.object(fast.Binary64RecordingOps,
                        "capture_constant_hinge", return_value=None))
                result = export_glb(built.model, options=options,
                    target_contract="ontokin.glb/0.6", work=built.reach_work)
            self.assertEqual(result.report["validation"]["status"], "passed")
            self.assertLessEqual(built.budget.operations, 100000)
            outcomes.append((result.data, result.report["validation"]))
        self.assertEqual(*outcomes)


if __name__ == "__main__":
    unittest.main()
