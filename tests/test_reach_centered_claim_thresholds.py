"""Fresh centered inequalities may omit only a proved local comparison."""
from contextlib import ExitStack, nullcontext
from fractions import Fraction as F
import math
from types import MethodType, SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.diagnostics import OntoKinError
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from test_reach_centered_endpoint_proofs import pose, point
from test_reach_reference_source_batch import prefix


def exact_claims():
    """Keep the same centered proof, selecting only its original comparisons."""
    return patch.object(reader, "_centered_claim_sufficient", return_value=False)


def arithmetic(*, check=None, cap=32768):
    work = Work(check=check, max_operand_bits=cap)
    return reader._Bounds(work, cache_intermediates=False), work


def comparison(ideal, bounds, *, position=(0., 0., 0.), quaternion=(0., 0., 0., 1.),
               limits=(.001, .001), previous=None, completed=()):
    return reader._recording_centered_comparison(ideal, position, quaternion, limits, bounds,
                                                previous=previous, completed=completed)


class CenteredClaimThresholdTests(unittest.TestCase):
    def assert_independent_error(self, caught):
        self.assertEqual(caught.exception.diagnostic.details["export_code"],
                         "OKE-E-INDEPENDENT-VALIDATION")

    def test_normal_strict_boundaries_and_nondyadic_minima(self):
        bounds, work = arithmetic()
        cases = ((.5, F(3, 8), True), (1.5, F(7, 8), True),
                 (1.5, F(7, 5), False), (2., F(1, 3), True),
                 (2., F(3, 2), True), (2., 2-F(1, 1 << 100), True),
                 (2., F(2), False), (2., 2+F(1, 1 << 100), False),
                 (math.nextafter(2., 0.), F(1), False), (2., F(-1, 8), False))
        for claim, value, expected in cases:
            with self.subTest(claim=claim, value=value):
                actual = reader._centered_claim_sufficient(value, claim, bounds)
                self.assertIs(actual, expected)
                if actual:
                    self.assertLess(value, F(claim))
        self.assertEqual(work.operations, 0)

    def test_subnormal_minimum_largest_and_normal_transition(self):
        bounds, _ = arithmetic()
        smallest = float.fromhex("0x0.0000000000001p-1022")
        largest = float.fromhex("0x0.fffffffffffffp-1022")
        normal = float.fromhex("0x1p-1022")
        for claim, value in ((smallest, F(1, 1 << 1075)),
                             (largest, F(1, 1 << 1024)),
                             (normal, F(normal)-F(1, 1 << 1100))):
            with self.subTest(claim=claim):
                self.assertTrue(reader._centered_claim_sufficient(value, claim, bounds))
                self.assertLess(value, F(claim))
                self.assertFalse(reader._centered_claim_sufficient(F(claim), claim, bounds))
                self.assertTrue(reader._centered_claim_sufficient(F(0), claim, bounds))

    def test_largest_finite_binary64_retains_exact_equality_fallback(self):
        bounds, _ = arithmetic()
        claim = float.fromhex("0x1.fffffffffffffp+1023")
        self.assertTrue(reader._centered_claim_sufficient(F(1 << 1022), claim, bounds))
        self.assertFalse(reader._centered_claim_sufficient(F(claim), claim, bounds))
        self.assertFalse(reader._centered_claim_sufficient(F(1 << 1024), claim, bounds))

    def test_zero_signed_zero_nonfinite_and_foreign_claims_decline(self):
        bounds, work = arithmetic()
        class FloatSubclass(float):
            pass
        for claim in (0., -0., -1., float("nan"), float("inf"), float("-inf"),
                      True, False, 1, F(1), FloatSubclass(1.)):
            with self.subTest(claim=claim):
                self.assertFalse(reader._centered_claim_sufficient(F(0), claim, bounds))
        self.assertEqual(work.operations, 0)

    def test_native_fraction_field_boundary_is_2048_without_expanding_cap(self):
        bounds, work = arithmetic()
        for value in (F(1, (1 << 2047)+1), F((1 << 2047)+1, (1 << 2047)+3)):
            self.assertEqual(max(value.numerator.bit_length(), value.denominator.bit_length()), 2048)
            self.assertTrue(reader._centered_claim_sufficient(value, 4., bounds))
        for value in (F(1, 1 << 2048), F((1 << 2048)+1, (1 << 2048)+3)):
            self.assertEqual(max(value.numerator.bit_length(), value.denominator.bit_length()), 2049)
            self.assertFalse(reader._centered_claim_sufficient(value, 4., bounds))
        self.assertEqual(work.max_operand_bits, 32768)
        self.assertEqual(work.max_operations, 100000)

    def test_nonnative_and_malformed_fraction_fields_never_supply_a_proof(self):
        bounds, _ = arithmetic()
        class FractionSubclass(F):
            pass
        for value in (FractionSubclass(1, 8), 0, 0., True):
            self.assertFalse(reader._centered_claim_sufficient(value, 1., bounds))
        for field, changed in (("_numerator", True), ("_numerator", 0.),
                               ("_denominator", True), ("_denominator", 0),
                               ("_denominator", -1)):
            value = F(0, 1)
            with self.subTest(field=field, changed=changed):
                object.__setattr__(value, field, changed)
                self.assertFalse(reader._centered_claim_sufficient(value, 1., bounds))

    def test_narrow_or_nonnative_cap_declines_without_charging_or_recapturing(self):
        for cap in (512, 2048, 32767):
            bounds, work = arithmetic(cap=cap)
            self.assertFalse(reader._centered_claim_sufficient(F(0), 1., bounds))
            self.assertEqual(work.operations, 0)
            self.assertEqual(work.max_operand_bits, cap)
        bounds, work = arithmetic()
        work.max_operand_bits = 32768.
        self.assertFalse(reader._centered_claim_sufficient(F(0), 1., bounds))
        self.assertIs(type(work.max_operand_bits), float)

    def test_original_cross_product_failure_still_occurs_after_decline(self):
        value = F(1, 1 << 2047)
        bounds, work = arithmetic(cap=2048)
        self.assertFalse(reader._centered_claim_sufficient(value, 1., bounds))
        # Both scalars fit; the original prospective second product is 2049.
        with self.assertRaises(ReachAdmissionError) as caught:
            bounds.compare(value, 1.)
        self.assertEqual(caught.exception.details["budget"], "numeric_operand_bits")
        self.assertEqual(caught.exception.details["consumed"], 2049)
        self.assertEqual(work.counts.get("independent_bound_decode"), 1)
        self.assertEqual(work.counts.get("independent_exact_compare"), 1)

    def test_original_prospective_guard_keeps_preceding_callback_exception_identity(self):
        calls, marker = [0], RuntimeError("original comparison callback")
        def check():
            calls[0] += 1
            if calls[0] == 2:
                raise marker
        bounds, work = arithmetic(check=check, cap=2048)
        value = F(1, 1 << 2047)
        self.assertFalse(reader._centered_claim_sufficient(value, 1., bounds))
        with self.assertRaises(RuntimeError) as caught:
            bounds.compare(value, 1.)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(calls[0], 2)

    def test_sufficient_metadata_adds_no_operation_or_numeric_cache(self):
        bounds, work = arithmetic()
        for index in range(1, 17):
            value = F(index, 1 << 200)
            self.assertTrue(reader._centered_claim_sufficient(value, .001, bounds))
        self.assertEqual(work.operations, 0)
        self.assertEqual(work.counts, {})
        self.assertEqual(len(work._cache), 0)
        self.assertEqual(work.max_cache_entries, 256)
        self.assertTrue(reader._centered_claim_sufficient(F(0), .001, reader._Bounds()))

    def test_complete_numerical_proof_is_identical_with_exactly_four_operations_removed(self):
        radius = F(1, 1 << 104)
        ideal = pose((-radius, F(1, 8), F(-1, 4)), (1-radius, 0, 0, 0), pr=radius, qr=radius)
        results = []
        for enabled in (False, True):
            bounds, work = arithmetic()
            with nullcontext() if enabled else exact_claims():
                proof = comparison(ideal, bounds, position=(0., .125, -.25))
            self.assertIsNotNone(proof)
            self.assertEqual(proof["position_error"], 2*radius)
            self.assertEqual(proof["quaternion_error"], 4*radius)
            self.assertEqual(proof["magnitude"], F(3, 8))
            self.assertEqual(work.operations, sum(work.counts.values()))
            results.append((proof, work.operations, dict(work.counts)))
        self.assertEqual(results[0][0], results[1][0])
        self.assertEqual(results[0][1]-results[1][1], 4)
        for kind in ("independent_bound_decode", "independent_exact_compare"):
            self.assertEqual(results[0][2].get(kind, 0)-results[1][2].get(kind, 0), 2)
        for kind in set(results[0][2]) | set(results[1][2]):
            if kind not in ("independent_bound_decode", "independent_exact_compare"):
                self.assertEqual(results[0][2].get(kind, 0), results[1][2].get(kind, 0))

    def test_tight_valid_claim_and_exact_equality_keep_the_original_local_path(self):
        for error, claim in ((F(1, 8), .125), (F(5, 4), 1.5), (F(0), 0.)):
            outcomes = []
            for enabled in (False, True):
                bounds, work = arithmetic()
                with nullcontext() if enabled else exact_claims():
                    proof = comparison(pose((-error, 0, 0)), bounds, limits=(claim, 0.))
                outcomes.append((proof, dict(work.counts)))
            with self.subTest(error=error, claim=claim):
                self.assertIsNotNone(outcomes[1][0])
                self.assertEqual(outcomes[0], outcomes[1])
                self.assertEqual(outcomes[1][1].get("independent_exact_compare"), 2)

    def test_integer_fraction_and_invalid_claims_retain_original_outcomes(self):
        for claim in (1, F(1), True, float("nan"), float("inf"), -1.):
            outcomes = []
            for enabled in (False, True):
                bounds, work = arithmetic()
                with nullcontext() if enabled else exact_claims():
                    try:
                        result = comparison(pose(), bounds, limits=(claim, 0.))
                        outcomes.append(("result", result, dict(work.counts)))
                    except OntoKinError as error:
                        outcomes.append(("error", error.diagnostic.details["export_code"], dict(work.counts)))
            with self.subTest(claim=claim):
                self.assertEqual(outcomes[0], outcomes[1])

    def test_underreported_claim_still_requires_ordinary_independent_enclosures(self):
        bounds, work = arithmetic()
        reads = []
        centered = pose(qr=F(1, 1 << 104))
        ordinary = SimpleNamespace(position=tuple(map(point, (0, 0, 0))),
                                   orientation=tuple(map(point, (1, 0, 0, 0))))
        def enclosures(carriers, time, side, recording_context=None):
            reads.append((tuple(carriers), work.operations))
            return {carrier: ordinary for carrier in carriers}
        reference = SimpleNamespace(
            _recording_centered_poses=lambda carriers, *args, **kwargs: {carrier: centered for carrier in carriers},
            recording_pose_enclosures=enclosures,
            recording_stationary_frames=lambda *args, **kwargs: frozenset())
        rows = {(0, 0): {"max_endpoint_position_error_m": .001,
                         "max_endpoint_unit_quaternion_error": 0.}}
        result = reader._key_comparisons(reference, {0: {"frame": "carrier.frame"}},
            {0: {"translation": [(0., 0., 0.)], "rotation": [(0., 0., 0., 1.)]}},
            F(0), 0, bounds, endpoint_rows=rows, recording_context=object())
        self.assertEqual(len(reads), 1)
        self.assertGreater(reads[0][1], 0)
        self.assertEqual(result[0]["quaternion_error"], 0)
        self.assertNotIn("_centered_orientation_proof", result[0])
        self.assertIs(bounds.work, work)
        self.assertEqual(work.max_operations, 100000)

    def test_large_claim_cannot_omit_separate_quaternion_one_half_obligation(self):
        observed, original = [], reader._centered_claim_sufficient
        def observe(value, claim, bounds):
            observed.append(claim)
            return original(value, claim, bounds)
        bounds, _ = arithmetic()
        with patch.object(reader, "_centered_claim_sufficient", observe):
            result = comparison(pose(), bounds, quaternion=(0., 0., 0., 1.5), limits=(.001, 4.))
        self.assertIsNone(result)
        self.assertEqual(observed, [.001])

    def test_initial_custom_compare_executes_the_original_local_calls(self):
        bounds, work = arithmetic()
        calls, original = [], bounds.compare
        def compare(self, first, last):
            calls.append((first, last))
            return original(first, last)
        bounds.compare = MethodType(compare, bounds)
        result = comparison(pose(), bounds)
        self.assertIsNotNone(result)
        self.assertEqual(len(calls), 2)
        self.assertEqual(work.counts.get("independent_exact_compare"), 2)

    def test_initial_foreign_arithmetic_or_work_owner_cannot_borrow_native_proof(self):
        class ForeignBounds(reader._Bounds):
            pass
        class ForeignWork(Work):
            pass
        for bounds in (ForeignBounds(Work()), reader._Bounds(ForeignWork()),
                       SimpleNamespace(work=Work())):
            self.assertFalse(reader._centered_claim_sufficient(F(0), .001, bounds))

    def test_preceding_callback_dispatch_replacement_preserves_exact_sentinel(self):
        for target_name, method in (("instance", "compare"), ("class", "compare"),
                                   ("instance", "value"), ("instance", "tick"),
                                   ("instance", "bits"), ("work", "charge"),
                                   ("work", "guard_bits"), ("module", "_tick")):
            marker, changed = RuntimeError("changed native dispatch"), []
            with ExitStack() as patches:
                def fail(*args, **kwargs):
                    raise marker
                def check():
                    # The quaternion decode has completed. This surviving
                    # multiply callback precedes its optional claim proof.
                    if (not changed and work.counts.get("independent_centered_quaternion_sign", 0)
                            and work.counts.get("independent_bound_decode", 0)):
                        changed.append(True)
                        target = {"instance": bounds, "class": reader._Bounds,
                                  "work": work, "module": reader}[target_name]
                        patches.enter_context(patch.object(target, method, fail))
                bounds, work = arithmetic(check=check)
                with self.subTest(target=target_name, method=method), self.assertRaises(RuntimeError) as caught:
                    comparison(pose(), bounds)
                self.assertEqual(changed, [True])
                self.assertIs(caught.exception, marker)

    def test_every_surviving_callback_preserves_cancellation_identity(self):
        radius = F(1, 1 << 104)
        def run(check=None):
            bounds, work = arithmetic(check=check)
            ideal = pose((-radius, 0, 0), (1-radius, 0, 0, 0), pr=radius, qr=radius)
            return bounds, work, lambda: comparison(ideal, bounds)
        _, baseline, calculate = run()
        self.assertIsNotNone(calculate())
        for fail_at in range(1, baseline.operations+1):
            calls, marker = [0], RuntimeError("remaining centered callback")
            def check():
                calls[0] += 1
                if calls[0] == fail_at:
                    raise marker
            _, work, calculate = run(check)
            with self.subTest(fail_at=fail_at), self.assertRaises(RuntimeError) as caught:
                calculate()
            self.assertIs(caught.exception, marker)
            self.assertIs(work.callback_error, marker)
            self.assertEqual(calls[0], fail_at)

    def test_observed_cap_departure_cannot_restore_at_a_later_claim_callback(self):
        calls, restore = [0], []
        def check():
            calls[0] += 1
            if calls[0] == 2:
                work.max_operand_bits = 32767
            elif calls[0] > 2:
                restore.append(True)
                work.max_operand_bits = 32768
        bounds, work = arithmetic(check=check)
        self.assertIsNone(comparison(pose(), bounds))
        self.assertEqual(calls[0], 2)
        self.assertEqual(restore, [])
        self.assertEqual(work.max_operand_bits, 32767)

    def test_callback_mutated_native_source_fields_remain_receipt_failures(self):
        for field, changed in (("_numerator", True), ("_denominator", 0)):
            ideal = pose(pr=F(1, 1 << 104))
            def check():
                object.__setattr__(ideal.position_radius, field, changed)
            bounds, work = arithmetic(check=check)
            with self.subTest(field=field), self.assertRaises(OntoKinError) as caught:
                comparison(ideal, bounds)
            self.assert_independent_error(caught)
            self.assertEqual(work.operations, 1)

    def test_callback_owner_replacement_remains_an_independent_receipt_failure(self):
        def check():
            bounds.work = Work()
        bounds, work = arithmetic(check=check)
        with self.assertRaises(OntoKinError) as caught:
            comparison(pose(), bounds)
        self.assert_independent_error(caught)
        self.assertEqual(work.operations, 1)

    def test_existing_completed_receipts_reuse_without_new_claim_state(self):
        ideal = pose(position=(1, 2, 3))
        bounds, work = arithmetic()
        first = comparison(ideal, bounds, position=(1., 2., 3.))
        before = work.operations
        with patch.object(reader, "_centered_claim_sufficient", side_effect=AssertionError("completed receipt")):
            reused = comparison(ideal, bounds, position=(1., 2., 3.), previous=first, completed=(first,))
        self.assertEqual(first, reused)
        self.assertGreater(work.operations, before)
        self.assertEqual(work.counts.get("independent_centered_endpoint_reuse"), 2)
        self.assertEqual(len(work._cache), 0)

    def test_original_source_prefix_bytes_and_complete_reports_are_unchanged(self):
        for case in ("P09", "P11", "L03"):
            outcomes = []
            for enabled in (False, True):
                with nullcontext() if enabled else exact_claims():
                    result, compiler = prefix(case)
                self.assertEqual(result.report["validation"]["status"], "passed")
                self.assertEqual(compiler.reach_work.max_operations, 100000)
                self.assertEqual(compiler.reach_work.operations, sum(compiler.reach_work.counts.values()))
                outcomes.append((result.data, result.report["validation"], compiler.reach_work.operations))
            with self.subTest(case=case):
                self.assertEqual(outcomes[0][:2], outcomes[1][:2])
                self.assertLess(outcomes[1][2], outcomes[0][2])
            print(f"{case} local centered claims: exact={outcomes[0][2]}, sufficient={outcomes[1][2]}")


if __name__ == "__main__":
    unittest.main()
