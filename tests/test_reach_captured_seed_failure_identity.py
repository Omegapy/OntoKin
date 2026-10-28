"""Captured seeds preserve source failures and successful domain replay."""
from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path
import sys
from types import MappingProxyType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin import reach_recording_fast as fast
from ontokin.reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, ReachExecutionWork
from ontokin.reach_phase import RecordingAngularFrame, RecordingAngularProof, _AxialRate
from ontokin.reach_pose import ReachPoseOps, UNIT


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
    raise AssertionError(type(value))


def captured_proof(*, world=False):
    if world:
        frame = "world"
        record = RecordingAngularFrame(_AxialRate(None, F(0)), None, ("world",), 0)
    else:
        frame = "rig.frame"
        zero = frozen((0.0, 0.0, 0.0))
        unit = frozen((1.0, 0.0, 0.0, 0.0))
        # Match the ordinary constant-root witness used by the repository's
        # recording graph-sharing fixtures.
        record = RecordingAngularFrame(_AxialRate(None, F(0)), None,
            ("root", "rig", frozen("kinematic"), zero, zero, unit,
             frozen(None), frozen(F(0)), None, None), 0)
    return RecordingAngularProof(F(0), F(2), "seed-failure-review",
        MappingProxyType({frame: record})), frame


def sample_with_cap_callback(mode, *, restore_after_failure=False):
    """Keep the real source kernels; intercept only their ordinary callback."""
    proof, frame = captured_proof(world=mode == "successful_direct")
    state = SimpleNamespace(inside=False, narrowed=False, pending=None)
    errors, call_caps, events = [], [], []
    marker = ReachAdmissionError("reach_resource", "callback's original refusal",
        budget="numeric_operand_bits", limit=128, consumed=1075)

    def check():
        if state.pending in ("narrow", "raise"):
            work.max_operand_bits = 128
            state.narrowed = True
            events.append(state.pending)
            if state.pending == "raise":
                state.pending = None
                raise marker
        elif state.pending == "restore":
            work.max_operand_bits = MAX_OPERAND_BITS
            events.append("restore")
        state.pending = None

    work = ReachExecutionWork(check)
    ops = ReachPoseOps(work)
    original_charge = work.charge
    original_direct = fast._captured_recording_orientation_direct

    def charge(kind="checkpoint", amount=1):
        if not state.narrowed:
            if state.inside and kind == "binary64_decode" and mode in ("source_guard", "callback"):
                state.pending = "raise" if mode == "callback" else "narrow"
            elif state.inside and kind == "recording_body_seed_frame" and mode == "successful_direct":
                state.pending = "narrow"
            elif not state.inside and kind == "cache_lookup" and mode == "optional_lookup":
                state.pending = "narrow"
        elif state.inside and errors and restore_after_failure and work.max_operand_bits == 128:
            state.pending = "restore"
        return original_charge(kind, amount)

    def direct(*args, **kwargs):
        call_caps.append(work.max_operand_bits)
        state.inside = True
        try:
            return original_direct(*args, **kwargs)
        except ReachAdmissionError as error:
            errors.append(error)
            raise
        finally:
            state.inside = False

    result, error = None, None
    with patch.object(work, "charge", side_effect=charge), patch.object(
            fast, "_captured_recording_orientation_direct", side_effect=direct):
        try:
            result = fast.captured_recording_orientation(ops, proof, frame, F(1, 4))
        except ReachAdmissionError as raised:
            error = raised
    return SimpleNamespace(result=result, error=error, source_errors=errors,
        call_caps=call_caps, events=events, work=work, marker=marker)


class CapturedSeedFailureIdentityTests(unittest.TestCase):
    def assert_source_guard(self, outcome):
        self.assertEqual(len(outcome.source_errors), 1)
        original = outcome.source_errors[0]
        self.assertIs(outcome.error, original)
        self.assertEqual(original.details["budget"], "numeric_operand_bits")
        self.assertEqual(original.details["limit"], 128)
        self.assertEqual(original.details["consumed"], 1075)
        self.assertIsNone(outcome.work.callback_error)
        self.assertIsNone(outcome.result)
        self.assertFalse(any(key[0] == "recording_captured_direct_seed_v1"
                             for key in outcome.work._cache))
        self.assertEqual(outcome.work.max_operations, 100000)

    def test_original_source_guard_is_never_retried_or_replaced(self):
        for restore in (False, True):
            with self.subTest(later_callback_would_restore=restore):
                outcome = sample_with_cap_callback("source_guard", restore_after_failure=restore)
                self.assert_source_guard(outcome)
                self.assertEqual(outcome.call_caps, [MAX_OPERAND_BITS])
                self.assertEqual(outcome.events, ["narrow"])
                self.assertEqual(outcome.work.max_operand_bits, 128)

    def test_callback_exception_retains_identity_without_retry(self):
        outcome = sample_with_cap_callback("callback", restore_after_failure=True)
        self.assertIs(outcome.error, outcome.marker)
        self.assertIs(outcome.work.callback_error, outcome.marker)
        self.assertEqual(outcome.source_errors, [outcome.marker])
        self.assertEqual(outcome.call_caps, [MAX_OPERAND_BITS])
        self.assertEqual(outcome.events, ["raise"])
        self.assertIsNone(outcome.result)

    def test_successful_direct_result_still_replays_in_changed_domain(self):
        # A world rotation can complete under 128 bits. Its first successful
        # calculation crosses the cap change and must be admitted once again.
        outcome = sample_with_cap_callback("successful_direct")
        self.assertIsNone(outcome.error)
        self.assertEqual(outcome.source_errors, [])
        self.assertEqual(outcome.call_caps, [MAX_OPERAND_BITS, 128])
        self.assertEqual(outcome.events, ["narrow"])
        self.assertEqual(outcome.result.components, UNIT)
        self.assertEqual(outcome.work.max_operand_bits, 128)
        self.assertIsNone(outcome.work.callback_error)

    def test_optional_lookup_cap_change_precedes_single_current_domain_seed(self):
        # A declined optional lookup is not a failed source calculation. It
        # still restarts domain admission, then executes the original source
        # once under 128 bits and propagates that source's actual refusal.
        outcome = sample_with_cap_callback("optional_lookup")
        self.assert_source_guard(outcome)
        self.assertEqual(outcome.call_caps, [128])
        self.assertEqual(outcome.events, ["narrow"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
