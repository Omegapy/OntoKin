"""Independent checks for the proposed pointwise source-rate audit.

Analytic interval examples establish the comparison rule without obtaining
expected values from the production solver. Source tests exercise the actual
compiled inspection and independent reference under one bounded context.
"""
from __future__ import annotations

import copy
from fractions import Fraction as F
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_reference import Interval, ReferenceError, build_reference
from ontokin.reach_runtime import ReachSimulator
from tools.reach_source_rates import (
    FROZEN_SCHEMA, RateAuditError, audit_source_rates, compare_rate_vector,
    execute_source_rate_audit, observation_from_snapshot,
)


DATA = Path(__file__).resolve().parents[1] / "docs/language-design/planar-reach-v0.1"
TIP = "rig.arm.forearm.tip.frame"


def exact(record):
    return F(int(record["numerator_hex"], 16), int(record["denominator_hex"], 16))


def point_box(*values):
    return tuple(Interval(F(value), F(value)) for value in values)


def bundle(name):
    directory = DATA / "draft2-supplements" if name.startswith("l") else DATA
    return load_file_manifest(directory / (name + ".files.json"))


class ReachRateDistanceTests(unittest.TestCase):
    def setUp(self):
        self.work = ReachExecutionWork()
        self.zero = point_box(0, 0, 0)

    def test_euclidean_ball_includes_exact_three_four_five_boundary(self):
        result = compare_rate_vector([3.0, 4.0, 0.0], self.zero, F(5), work=self.work)
        self.assertEqual(result["status"], "proved")
        self.assertEqual(exact(result["minimum_squared_error"]), 25)
        self.assertEqual(exact(result["maximum_squared_error"]), 25)
        self.assertGreater(self.work.operations, 0)

    def test_componentwise_allowance_cannot_replace_a_vector_norm(self):
        result = compare_rate_vector([1.0, 1.0, 1.0], self.zero, F(1), work=self.work)
        self.assertEqual(result["status"], "contradicted")
        self.assertEqual(exact(result["minimum_squared_error"]), 3)

    def test_mixed_endpoint_extrema_preserve_all_three_outcomes(self):
        # The farthest corner is (-3, 4, 0), neither all-low nor all-high.
        box = (Interval(F(-3), F(-2)), Interval(F(2), F(4)), Interval(F(0), F(0)))
        for allowance, status in ((5, "proved"), (3, "unresolved"), (2, "contradicted")):
            with self.subTest(allowance=allowance):
                result = compare_rate_vector([0.0, 0.0, 0.0], box, F(allowance), work=self.work)
                self.assertEqual(result["status"], status)
                self.assertEqual(exact(result["minimum_squared_error"]), 8)
                self.assertEqual(exact(result["maximum_squared_error"]), 25)

    def test_touching_allowance_and_midpoint_agreement_remain_unresolved(self):
        touching = (Interval(F(1), F(2)), *self.zero[1:])
        result = compare_rate_vector([0.0, 0.0, 0.0], touching, F(1), work=self.work)
        self.assertEqual(result["status"], "unresolved")
        box = (Interval(F(-1), F(1)),) * 3
        result = compare_rate_vector([0.0, 0.0, 0.0], box, F(1), work=self.work)
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual(exact(result["maximum_squared_error"]), 3)

    def test_subnormal_squared_distances_do_not_underflow(self):
        smallest = float.fromhex("0x0.0000000000001p-1022")
        result = compare_rate_vector([smallest, 0.0, -0.0], self.zero, F(smallest), work=self.work)
        self.assertEqual(result["status"], "proved")
        self.assertEqual(exact(result["maximum_squared_error"]), F(1, 1 << 2148))
        self.assertEqual(result["actual_binary64_hex"][2], "8000000000000000")
        result = compare_rate_vector([smallest, 0.0, -0.0], self.zero, F(0), work=self.work)
        self.assertEqual(result["status"], "contradicted")

    def test_frozen_preparation_values_are_measurements_only(self):
        result = compare_rate_vector([0.0, 0.0, -0.0], self.zero, F(0), work=self.work,
                                     frozen=[1000.0, 0.0, 0.0])
        self.assertEqual(result["status"], "proved")
        measurement = result["frozen_measurement"]
        self.assertEqual(measurement["acceptance_status"], "not_established")
        self.assertFalse(measurement["used_for_verdict"])
        self.assertFalse(measurement["exact_binary64_equal"])
        self.assertEqual(exact(measurement["actual_minus_frozen"][0]), -1000)
        self.assertEqual(exact(measurement["minimum_squared_distance_to_ideal_box"]), 1000000)
        zeros = compare_rate_vector([-0.0, 0.0, 0.0], self.zero, F(0), work=self.work,
                                    frozen=[0.0, 0.0, 0.0])["frozen_measurement"]
        self.assertFalse(zeros["exact_binary64_equal"])
        self.assertEqual(exact(zeros["actual_minus_frozen"][0]), 0)

    def test_invalid_binary64_vectors_and_inexact_allowances_are_rejected(self):
        vectors = ([True, 0.0, 0.0], [math.inf, 0.0, 0.0], [math.nan, 0.0, 0.0],
                   [0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [F(1, 2), 0.0, 0.0],
                   [(1 << 1024) - 1, 0.0, 0.0], [(1 << 54) + 1, 0.0, 0.0])
        for vector in vectors:
            with self.subTest(vector=vector):
                with self.assertRaises(RateAuditError):
                    compare_rate_vector(vector, self.zero, F(1), work=self.work)
        for allowance in (True, 1.0, F(-1)):
            with self.subTest(allowance=allowance):
                with self.assertRaises(RateAuditError):
                    compare_rate_vector([0.0] * 3, self.zero, allowance, work=self.work)
        bad_box = (Interval(0.0, 1.0), *self.zero[1:])
        with self.assertRaises(RateAuditError):
            compare_rate_vector([0.0] * 3, bad_box, F(1), work=self.work)

    def test_exact_operand_limits_precede_large_intermediate_allocation(self):
        work = ReachExecutionWork(max_operand_bits=128)
        with self.assertRaises(RateAuditError) as caught:
            compare_rate_vector([0.0] * 3, self.zero, F(1 << 100), work=work)
        self.assertEqual(caught.exception.code, "operand_limit")
        with self.assertRaises(RateAuditError) as caught:
            compare_rate_vector([0.0] * 3, self.zero, F(1 << 32768), work=self.work)
        self.assertEqual(caught.exception.code, "operand_limit")

    def test_work_is_not_reset_and_callback_exception_identity_is_retained(self):
        limited = ReachExecutionWork(max_operations=8)
        limited.charge(amount=7)
        with self.assertRaises(ReachAdmissionError) as caught:
            compare_rate_vector([0.0] * 3, self.zero, F(0), work=limited)
        self.assertEqual(caught.exception.reach_code, "reach_resource")
        self.assertEqual(limited.operations, 8)
        interruption = ReferenceError("test_cancellation", "retain this callback object")
        def check():
            raise interruption
        cancelled = ReachExecutionWork(check=check)
        with self.assertRaises(ReferenceError) as caught:
            compare_rate_vector([0.0] * 3, self.zero, F(0), work=cancelled)
        self.assertIs(caught.exception, interruption)
        self.assertIs(cancelled.callback_error, interruption)


class ReachSourceRateAuditTests(unittest.TestCase):
    def capture(self, *, time=F(1, 4), carriers=(TIP,)):
        compiler = compile_construction(bundle("p01"))
        snapshot = ReachSimulator(compiler.model, work=compiler.reach_work).advance(time, "after")
        observation = observation_from_snapshot(compiler.model, snapshot, carriers=carriers,
                                                work=compiler.reach_work)
        return compiler, observation

    def test_actual_reference_comparison_never_calls_production_expectation_generators(self):
        compiler, observation = self.capture()
        original = copy.deepcopy(observation)
        failure = AssertionError("A production expectation generator was called")
        with patch("ontokin.reach_runtime.ReachSimulator", side_effect=failure), \
             patch("ontokin.reach_kinematics.admit_planar", side_effect=failure), \
             patch("ontokin.reach_pose.ReachPoseOps", side_effect=failure):
            reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
            report = audit_source_rates(reference, observation, work=compiler.reach_work)
        self.assertEqual(report["status"], "proved")
        self.assertEqual(report["observation_provenance"], "supplied_identity_assertion")
        self.assertEqual(report["criterion_status"], "proposed_not_adopted")
        self.assertFalse(report["release_acceptance"])
        self.assertEqual(observation, original)
        self.assertEqual(len(report["results"]), 2)

    def test_changed_actual_velocity_is_contradicted_by_independent_reference(self):
        compiler, observation = self.capture()
        observation["carriers"][TIP]["velocity_m_per_s"][0] = 1000000.0
        reference = build_reference(compiler.model, end=F(1, 4), work=compiler.reach_work)
        report = audit_source_rates(reference, observation, work=compiler.reach_work)
        self.assertEqual(report["status"], "contradicted")
        self.assertEqual(report["results"][0]["status"], "contradicted")
        self.assertEqual(report["source_execution_role"], "pending")

    def test_stale_identity_fraction_packets_wrong_sides_and_new_work_are_rejected(self):
        compiler, observation = self.capture(time=F(0), carriers=("world",))
        reference = build_reference(compiler.model, end=F(0), work=compiler.reach_work)
        stale = copy.deepcopy(observation)
        stale["source"]["program_revision"] = "sha256:" + "0" * 64
        variants = [(stale, "source_identity")]
        wrong_source = copy.deepcopy(observation)
        source_id = next(iter(wrong_source["source"]["sources"]))
        wrong_source["source"]["sources"][source_id] = "sha256:" + "0" * 64
        variants.append((wrong_source, "source_identity"))
        for key, value, code in (("time_seconds", F(0), "clock"), ("side", "left", "side"),
                                 ("time_seconds", "1e1000000", "clock"),
                                 ("time_seconds", "1/0", "clock"),
                                 ("time_seconds", "1", "clock")):
            variant = copy.deepcopy(observation)
            variant[key] = value
            variants.append((variant, code))
        malformed = copy.deepcopy(observation)
        malformed["source"]["module_key"] = "\ud800"
        variants.append((malformed, "text"))
        for variant, code in variants:
            with self.subTest(code=code, clock=repr(variant["time_seconds"])):
                with self.assertRaises(RateAuditError) as caught:
                    audit_source_rates(reference, variant, work=compiler.reach_work)
                self.assertEqual(caught.exception.code, code)
        with self.assertRaises(RateAuditError) as caught:
            audit_source_rates(reference, observation, work=ReachExecutionWork())
        self.assertEqual(caught.exception.code, "work")

    def test_frozen_packet_requires_same_source_clock_side_and_carriers(self):
        compiler, observation = self.capture(time=F(0), carriers=("world",))
        reference = build_reference(compiler.model, end=F(0), work=compiler.reach_work)
        frozen = copy.deepcopy(observation)
        frozen["schema_version"] = FROZEN_SCHEMA
        frozen["side"] = "before"
        with self.assertRaises(RateAuditError) as caught:
            audit_source_rates(reference, observation, work=compiler.reach_work, frozen=frozen)
        self.assertEqual(caught.exception.code, "frozen_identity")

    def test_fresh_wrapper_records_actual_source_and_implementation_identities(self):
        report = execute_source_rate_audit(bundle("p01"), time=F(1, 4), side="after", carriers=[TIP])
        self.assertEqual(report["status"], "proved")
        self.assertEqual(report["observation_provenance"], "fresh_compile_and_source_snapshot_in_this_call")
        self.assertEqual(report["source"]["program_revision"], bundle("p01").program_revision)
        self.assertTrue(report["identified_inputs_stable_during_observation_and_reference"])
        self.assertTrue(report["compilation_preceded_hash_window"])
        self.assertEqual(report["request_operation_limit"], 100000)
        self.assertEqual(report["reach_work_operation_limit"], 100000)
        self.assertGreater(report["compilation_request_operations"], 0)
        self.assertGreater(report["request_operations"], report["compilation_request_operations"])
        self.assertLessEqual(report["request_operations"], 100000)
        self.assertLessEqual(report["reach_work_operations"], report["request_operations"])
        self.assertFalse(report["full_product_goal_completed"])
        for group in report["input_hashes"].values():
            self.assertRegex(group["sha256"], r"^sha256:[0-9a-f]{64}$")
            self.assertTrue(group["inputs"])
            self.assertTrue(all(row["bytes"] > 0 for row in group["inputs"]))

    def test_valid_incoming_failed_boundary_is_explicitly_reference_unavailable(self):
        report = execute_source_rate_audit(bundle("l04"), time=F(1, 2), side="before", carriers=["world"])
        self.assertEqual(report["status"], "unresolved")
        self.assertEqual(report["reason"], "reference_unavailable")
        self.assertEqual(report["reference_error"]["code"], "source_admission")
        self.assertEqual(exact(report["time"]), F(1, 2))
        self.assertEqual(report["side"], "before")
        self.assertFalse(report["release_acceptance"])

    def test_fresh_wrapper_does_not_translate_reference_typed_cancellation(self):
        interruption = ReferenceError("test_cancellation", "original callback exception")
        armed = False
        def check():
            if armed:
                raise interruption
        def cancel_during_reference(model, *, end, work):
            nonlocal armed
            armed = True
            work.tick()
        with patch("tools.reach_source_rates.build_reference", side_effect=cancel_during_reference):
            with self.assertRaises(ReferenceError) as caught:
                execute_source_rate_audit(bundle("p01"), time=0, side="after", carriers=["world"], check=check)
        self.assertIs(caught.exception, interruption)

    def test_fresh_wrapper_preserves_reference_owned_resource_failure(self):
        exhausted = ReferenceError("resource", "independent exact operand limit")
        with patch("tools.reach_source_rates.build_reference", side_effect=exhausted):
            with self.assertRaises(ReferenceError) as caught:
                execute_source_rate_audit(bundle("p01"), time=0, side="after", carriers=["world"])
        self.assertIs(caught.exception, exhausted)


if __name__ == "__main__":
    unittest.main()
