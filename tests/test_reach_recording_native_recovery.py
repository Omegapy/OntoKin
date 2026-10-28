"""Recovered native recording preserves current carrier and live-domain proofs."""
import copy
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_export
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import PhaseBound, phase_bounds
from ontokin.reach_recording_fast import (
    Binary64RecordingOps, _UnsupportedPlanar, recording_float_excess,
    sample_bounded_frames,
)
from test_reach_recording_sampler import simulator


class RecoveredNativeRecordingTests(unittest.TestCase):
    def test_sufficient_lift_sign_matches_exact_products_including_underflow(self):
        tiny = math.ldexp(1.0, -1074)
        pairs = (
            ((0.0, -0.0, 0.6, 0.8), (0.0, 0.0, 0.8, 0.6)),
            ((0.0, 0.0, -0.6, -0.8), (0.0, 0.0, 0.8, 0.6)),
            ((tiny, 0.0, 0.0, 0.0), (tiny, 0.0, 0.0, 0.0)),
            ((-tiny, 0.0, 0.0, 0.0), (tiny, 0.0, 0.0, 0.0)),
            ((1.0, 0.0, 0.0, 0.0), (0.0, -0.0, 1.0, 0.0)),
        )
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                expected = sum((F(a) * F(b) for a, b in zip(left, right)), F(0))
                work = ReachExecutionWork()
                with patch.object(reach_export, "_exact", side_effect=AssertionError("No product is needed")):
                    actual, _ = reach_export._recording_lift_relation(left, right, work=work)
                self.assertEqual(actual, (expected > 0) - (expected < 0))
                self.assertEqual(work.counts["recording_hemisphere_domain"], 1)
                self.assertEqual(work.operations, sum(work.counts.values()))

    def test_strict_lift_margin_keeps_exact_fallback_for_small_or_mixed_pairs(self):
        pairs = (
            ((0.0, 0.0, 0.5, 0.5), (0.0, 0.0, 0.5, 0.5)),
            ((0.0, 0.0, -0.5, -0.5), (0.0, 0.0, 0.5, 0.5)),
            ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0)),
            ((2.0**-8, 0.0, 0.0, 0.0), (2.0**-8, 0.0, 0.0, 0.0)),
            ((2.0**-8, 0.0, 0.0, 0.0), (2.0**-7, 0.0, 0.0, 0.0)),
            ((0.5, 0.5, 0.0, 0.0), (0.5, -0.5, 0.0, 0.0)),
            ((0.5, 0.5, 0.0, 0.0), (0.5, -0.25, 0.0, 0.0)),
        )
        for index, (left, right) in enumerate(pairs):
            with self.subTest(index=index):
                expected = sum((F(a) * F(b) for a, b in zip(left, right)), F(0))
                work = ReachExecutionWork()
                actual, separated = reach_export._recording_lift_relation(
                    left, right, work=work, require_margin=True)
                self.assertEqual(actual, (expected > 0) - (expected < 0))
                self.assertEqual(separated, abs(expected) > F(1, 1 << 16))
                if index >= 3:
                    self.assertEqual(work.counts["recording_exact_mul"], 4)
                    self.assertEqual(work.counts["recording_exact_add"], 4)
                else:
                    self.assertNotIn("recording_exact_mul", work.counts)

    def test_lift_admission_narrowing_and_cancellation_cannot_use_sign_shortcut(self):
        vector = (0.0, 0.0, 0.6, 0.8)
        for narrow in (False, True):
            work = ReachExecutionWork()
            marker = RuntimeError("cancel current lift admission")
            work.external_check = (lambda: setattr(work, "max_operand_bits", 128) if narrow
                                   else (_ for _ in ()).throw(marker))
            with self.assertRaises(ReachAdmissionError if narrow else RuntimeError) as caught:
                reach_export._recording_lift_relation(vector, vector, work=work)
            if narrow:
                self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
            else:
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
        for invalid in ((False, 0.0, 0.0, 1.0), (float("nan"), 0.0, 0.0, 1.0), (0.0, 1.0)):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                reach_export._recording_lift_relation(invalid, vector, work=ReachExecutionWork())

    def test_completed_endpoint_enclosure_rechecks_its_live_cache_domain(self):
        bound = PhaseBound(trig_count=2, product_count=8, max_position_l1_m=F(7),
                           path_offset_l1_m=F(3), position_error_m=F(1, 2**48),
                           rotation_error_rad=F(1, 2**49))
        for narrow in (False, True):
            work = ReachExecutionWork()
            previous = recording_float_excess(bound, work=work, include_cell_radii=False)
            key = next(key for key, value in work._cache.items() if value is previous)
            marker = RuntimeError("cancel completed native enclosure")
            charge = work.charge
            def interrupt(kind="checkpoint", amount=1):
                if kind == "cache_promote":
                    work.external_check = (lambda: setattr(work, "max_operand_bits", 128) if narrow
                                           else (_ for _ in ()).throw(marker))
                return charge(kind, amount)
            with patch.object(work, "charge", side_effect=interrupt):
                with self.assertRaises(_UnsupportedPlanar if narrow else RuntimeError) as caught:
                    recording_float_excess(bound, work=work, include_cell_radii=False)
            if narrow:
                self.assertEqual(tuple(work._cache.items()), ())
                self.assertEqual(work._cache_operand_bits, 128)
                self.assertEqual(work.counts["cache_operand_scope_reset"], 1)
            else:
                self.assertIs(work._cache[key], previous)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)

    def test_native_enclosures_cover_current_complete_carrier_recurrence(self):
        for case in ("P09", "P16"):
            with self.subTest(case=case):
                candidate, baseline = simulator(case), simulator(case)
                contexts = (object(), object())
                proofs = []
                paths = ("rig.arm.upper.frame", "rig.arm.forearm.frame", "rig.tool.frame")
                for sim in (candidate, baseline):
                    sim.advance(F(0), "after")
                    proofs.append(phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True))
                moving = candidate.recording_moving_frames(candidate.state, paths)
                before = copy.deepcopy(candidate.state)
                for sim, context, proof in zip((candidate, baseline), contexts, proofs):
                    sim.recording_frames(F(0), sim.state, paths, moving_frames=moving,
                        recording_context=context, recording_angular_proof=proof["recording_angular_proof"])
                source_cache = candidate._pose_cache
                for time in (F(1, 16), F(1, 8), F(1, 4), F(1, 2)):
                    actual = sample_bounded_frames(candidate, time, candidate.state, paths,
                        context=contexts[0], moving_frames=moving, phase_bounds=proofs[0]["frames"],
                        phase_interval=(F(0), F(2)),
                        recording_angular_proof=proofs[0]["recording_angular_proof"])
                    reference = baseline.recording_frames(time, baseline.state, paths,
                        moving_frames=moving, recording_context=contexts[1],
                        recording_angular_proof=proofs[1]["recording_angular_proof"])
                    for path in paths:
                        expected, value = reference[path], actual.frames[path]
                        excess = actual.excess_by_frame[path]
                        self.assertLessEqual(sum((abs(F(a) - F(b)) for a, b in
                            zip(value.position, expected.position)), F(0)), excess.position_m)
                        quaternion_error = min(max(abs(F(a) - sign * F(b)) for a, b in
                            zip(value.orientation, expected.orientation)) for sign in (1, -1))
                        self.assertLessEqual(quaternion_error, excess.quaternion_component)
                self.assertEqual(candidate.state, before)
                self.assertIs(candidate._pose_cache, source_cache)
                self.assertLessEqual(len(candidate.work._cache), 256)
                self.assertGreater(baseline.work.counts.get("recording_body_direct_seed", 0), 0)
                self.assertGreater(baseline.work.counts.get("recording_rotation_step", 0), 0)

    def test_native_graph_cannot_mix_current_private_carrier_cursor_operands(self):
        sim = simulator("P16")
        sim.advance(F(0), "after")
        proof = phase_bounds(sim, F(0), F(2), sim.state, recording_proof=True)["recording_angular_proof"]
        native = Binary64RecordingOps(sim.pose_ops)
        with self.assertRaises(ValueError):
            sim._resolve_kinematics(F(1, 4), sim.state, selected_frames=("rig.frame",),
                pose_only=True, recording_only=True, recording_context=object(),
                recording_pose_ops=native, recording_angular_proof=proof)
        with self.assertRaises(ValueError):
            sim._resolve_kinematics(F(1, 4), sim.state, recording_pose_ops=native)


if __name__ == "__main__":
    unittest.main()
