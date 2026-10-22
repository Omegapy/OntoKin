"""Complete IK reuse binds current canonical limits and reports current work."""
import copy
from dataclasses import replace
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_kinematics as ik
from ontokin.reach_numeric import (
    MAX_OPERAND_BITS, PI64_BITS, DyadicContext, ReachAdmissionError,
    ReachExecutionWork, bits_float,
)
from test_reach_relative_observations import prepared


PI = bits_float(PI64_BITS)
LENGTHS = (1.0, 1.0)
TARGET = (1.0, 1.0, 0.0)
LIMITS = ((-PI, PI), (-PI, PI))


def complete_key(key):
    return len(key) > 1 and key[0] == ik.METHOD and key[1] == "complete_admission"


def admit(work, *, lengths=LENGTHS, target=TARGET, branch="elbow_positive", limits=LIMITS):
    return ik.admit_planar(lengths, target, branch, limits, work=work)


def outcome(work, **arguments):
    try:
        return replace(admit(work, **arguments), work=())
    except ReachAdmissionError as error:
        return error.reach_code, str(error), error.details


class ReachCompleteAdmissionTests(unittest.TestCase):
    def test_32_admissions_retain_exact_proofs_and_count_only_current_work(self):
        costs, outputs = [], []
        original = ik._complete_admission_key
        for reuse in (True, False):
            work = ReachExecutionWork()
            values = []
            with patch.object(ik, "_complete_admission_key", original if reuse else lambda *args: None):
                for _ in range(32):
                    before = work.operations
                    result = admit(work)
                    self.assertEqual(dict(result.work)["operations"] + 1, work.operations - before)
                    values.append(replace(result, work=()))
            costs.append(work.operations)
            outputs.append(values)
            self.assertEqual(work.operations, sum(work.counts.values()))
            self.assertLessEqual(len(work._cache), work.max_cache_entries)
        self.assertEqual(outputs[0], outputs[1])
        self.assertLess(costs[0], costs[1])

    def test_warm_complete_proof_omits_only_completed_numeric_work(self):
        work = ReachExecutionWork()
        first = admit(work)
        before = work.operations
        with patch.object(ik, "rational", side_effect=AssertionError("completed binary64 decode")), \
                patch.object(ik, "_limits", side_effect=AssertionError("completed identical limits")):
            second = admit(work)
        self.assertEqual(replace(first, work=()), replace(second, work=()))
        self.assertIsNot(first, second)
        self.assertEqual(dict(second.work), {"series_terms": 0, "interval_operations": 0,
                                          "exact_operations": 9, "operations": 11})
        self.assertEqual(work.operations - before, 12)

    def test_every_geometry_limit_and_branch_operand_is_part_of_the_proof(self):
        variants = [
            {"lengths": (0.0, 1.0)}, {"lengths": (1.0, 0.0)},
            {"target": (9.0, 1.0, 0.0)}, {"target": (1.0, 9.0, 0.0)},
            {"target": (1.0, 1.0, 1.0)},
            {"limits": ((4.0, PI), (-PI, PI))},
            {"limits": ((-PI, -4.0), (-PI, PI))},
            {"limits": ((-PI, PI), (4.0, PI))},
            {"limits": ((-PI, PI), (-PI, 0.0))},
            {"branch": "elbow_negative"},
        ]
        for arguments in variants:
            with self.subTest(arguments=arguments):
                work = ReachExecutionWork()
                first = admit(work)
                actual = outcome(work, **arguments)
                with patch.object(ik, "_complete_admission_key", return_value=None):
                    expected = outcome(ReachExecutionWork(), **arguments)
                self.assertEqual(actual, expected)
                self.assertNotEqual(actual, replace(first, work=()))

    def test_changed_valid_limits_keep_the_existing_geometry_only_proof(self):
        work = ReachExecutionWork()
        first = admit(work)
        with patch.object(DyadicContext, "atan_small", side_effect=AssertionError("old solver proof lost")):
            second = admit(work, limits=((-PI, PI), (0.0, PI)))
        self.assertEqual(replace(first, work=()), replace(second, work=()))
        self.assertEqual(sum(complete_key(key) for key in work._cache), 2)

    def test_mutable_foreign_nonfinite_and_large_inputs_keep_original_outcomes(self):
        class ForeignFloat(float):
            pass

        variants = (
            {"target": [1.0, 1.0, 0.0]}, {"lengths": [1.0, 1.0]},
            {"limits": [list(row) for row in LIMITS]},
            {"target": (ForeignFloat(1.0), 1.0, 0.0)},
            {"target": (True, 1.0, 0.0)}, {"target": (math.nan, 1.0, 0.0)},
            {"target": (math.inf, 1.0, 0.0)}, {"target": (float.fromhex("0x1.fffffffffffffp+1023"), 1.0, 0.0)},
            {"lengths": (1 << 40000, 1)},
        )
        for index, arguments in enumerate(variants):
            with self.subTest(index=index):
                warm = ReachExecutionWork()
                admit(warm)
                actual = outcome(warm, **arguments)
                with patch.object(ik, "_complete_admission_key", return_value=None):
                    expected = outcome(ReachExecutionWork(), **arguments)
                self.assertEqual(actual, expected)

    def test_initial_callback_precedes_fresh_mutable_input_reads(self):
        target = list(TARGET)
        work = ReachExecutionWork()
        admit(work)
        changed = False

        def change():
            nonlocal changed
            if not changed:
                target[0] = 3.0
                changed = True

        work.external_check = change
        with self.assertRaises(ReachAdmissionError) as caught:
            admit(work, target=target)
        self.assertTrue(changed)
        self.assertEqual(caught.exception.reach_code, "reach_unreachable")

    def test_each_input_checkpoint_and_lookup_respect_a_newly_narrowed_domain(self):
        with patch.object(ik, "_complete_admission_key", return_value=None):
            expected = outcome(ReachExecutionWork(max_operand_bits=512))
        for narrow_at in range(11):
            with self.subTest(narrow_at=narrow_at):
                work = ReachExecutionWork()
                admit(work)
                seen = 0
                original_charge, original_lookup = work.charge, work.lookup

                def charge(kind="checkpoint", amount=1):
                    nonlocal seen
                    if kind == "planar_admission_input":
                        seen += 1
                        if seen == narrow_at:
                            work.max_operand_bits = 512
                    return original_charge(kind, amount)

                def lookup(key):
                    result = original_lookup(key)
                    if narrow_at == 10 and complete_key(key):
                        work.max_operand_bits = 512
                    return result

                if narrow_at == 0:
                    work.max_operand_bits = 512
                with patch.object(work, "charge", charge), patch.object(work, "lookup", lookup):
                    self.assertEqual(outcome(work), expected)
                self.assertEqual(work.max_operand_bits, 512)

    def test_narrow_then_widen_does_not_replace_the_original_decode_exception(self):
        work = ReachExecutionWork()
        admit(work)
        original_charge, original_rational = work.charge, ik.rational
        errors = []

        def charge(kind="checkpoint", amount=1):
            if kind == "planar_admission_input":
                work.max_operand_bits = 512
            return original_charge(kind, amount)

        def decode(value, meter):
            try:
                return original_rational(value, meter)
            except ReachAdmissionError as error:
                errors.append(error)
                work.max_operand_bits = MAX_OPERAND_BITS
                raise

        with patch.object(work, "charge", charge), patch.object(ik, "rational", decode):
            with self.assertRaises(ReachAdmissionError) as caught:
                admit(work)
        self.assertEqual(len(errors), 1)
        self.assertIs(caught.exception, errors[0])
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(work.max_operand_bits, MAX_OPERAND_BITS)

    def test_cancelled_input_or_lookup_keeps_completed_cache_and_exception_identity(self):
        for cancel_at in range(1, 12):
            with self.subTest(cancel_at=cancel_at):
                work = ReachExecutionWork()
                admit(work)
                before = tuple(work._cache.items())
                marker = RuntimeError("cancel complete admission")
                original_charge = work.charge
                seen = 0

                def charge(kind="checkpoint", amount=1):
                    nonlocal seen
                    if kind in ("planar_admission_input", "cache_lookup", "cache_promote"):
                        seen += 1
                        if seen == cancel_at:
                            with patch.object(work, "external_check", side_effect=marker):
                                return original_charge(kind, amount)
                    return original_charge(kind, amount)

                with patch.object(work, "charge", charge):
                    with self.assertRaises(RuntimeError) as caught:
                        admit(work)
                self.assertIs(caught.exception, marker)
                self.assertIs(work.callback_error, marker)
                self.assertEqual(tuple(work._cache.items()), before)

    def test_publication_cancellation_or_domain_change_never_retains_a_partial_receipt(self):
        for cancel in (True, False):
            with self.subTest(cancel=cancel):
                work = ReachExecutionWork()
                original_remember = work.remember
                marker = RuntimeError("cancel complete proof publication")

                def remember(key, value, **kwargs):
                    if complete_key(key):
                        if cancel:
                            with patch.object(work, "external_check", side_effect=marker):
                                return original_remember(key, value, **kwargs)
                        work.max_operand_bits = 512
                    return original_remember(key, value, **kwargs)

                with patch.object(work, "remember", remember):
                    if cancel:
                        with self.assertRaises(RuntimeError) as caught:
                            admit(work)
                        self.assertIs(caught.exception, marker)
                    else:
                        result = admit(work)
                        self.assertEqual(result.target_rad, (0.0, PI / 2))
                self.assertFalse(any(complete_key(key) for key in work._cache))

    def test_cache_capacity_and_lowered_request_budget_are_unchanged(self):
        for capacity in (1, 2, 256):
            with self.subTest(capacity=capacity):
                work = ReachExecutionWork(max_cache_entries=capacity)
                first = admit(work)
                for _ in range(3):
                    self.assertEqual(replace(admit(work), work=()), replace(first, work=()))
                    self.assertLessEqual(len(work._cache), capacity)
                previous = tuple(work._cache.items())
                work.max_operations = work.operations + 1
                with self.assertRaises(ReachAdmissionError) as caught:
                    admit(work)
                self.assertEqual(caught.exception.details["budget"], "max_operations")
                self.assertEqual(tuple(work._cache.items()), previous)

    def test_cancelled_warm_source_admission_rolls_back_the_complete_boundary(self):
        simulator = prepared()
        payload = simulator.model.actions["reach"].reach
        ik.admit_planar(payload.lengths_m, payload.target_m, payload.branch,
                        payload.limits_rad, work=simulator.work)
        previous = copy.deepcopy(simulator.state)
        marker = RuntimeError("cancel admitted boundary")
        original_charge = simulator.work.charge

        def charge(kind="checkpoint", amount=1):
            if kind == "planar_admission_input":
                with patch.object(simulator.work, "external_check", side_effect=marker):
                    return original_charge(kind, amount)
            return original_charge(kind, amount)

        with patch.object(simulator.work, "charge", charge):
            with self.assertRaises(RuntimeError) as caught:
                simulator._process_boundary(F(0))
        self.assertIs(caught.exception, marker)
        self.assertEqual(simulator.state, previous)
        self.assertEqual(simulator.state.claims, {})
        self.assertIsNone(simulator._pending_reach_output)


if __name__ == "__main__":
    unittest.main()
