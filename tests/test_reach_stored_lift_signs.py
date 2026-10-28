"""Exact supplied-byte lift signs avoid only mathematically unnecessary work."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
import math
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_independent_sufficient_bounds import original_norm_proofs
from test_reach_recurring_endpoint_claims import replace_document


def endpoint(error=0):
    return {"quaternion_error": F(error), "normalized": None, "_normalized_cap": None}


def arc(first, last, arithmetic):
    return reader._certified_stored_arc(first, last, endpoint(), endpoint(F(1, 1 << 19)),
                                        F(1), F(1, 4), .2, arithmetic)


class IndependentStoredLiftSignTests(unittest.TestCase):
    def test_uniform_signs_match_the_exact_rational_dot_without_arithmetic(self):
        pairs = (
            ((0., -0., .5, .5), (-0., 0., .25, .75)),
            ((0., 0., -.5, .5), (0., 0., -.25, .75)),
            ((.5, -.5, .5, -.5), (-.5, .5, -.5, .5)),
            ((1., 0., -0., 0.), (0., 1., 0., -0.)),
            ((-0.,) * 4, (0.,) * 4),
            ((2. ** -200, 0., 0., 2. ** 128), (2. ** -200, 0., 0., 2. ** 128)),
        )
        for first, last in pairs:
            exact = sum((F(a) * F(b) for a, b in zip(first, last)), F(0))
            work = Work()
            arithmetic = reader._Bounds(work)
            first = reader._recording_vector(first, 4, arithmetic)
            last = reader._recording_vector(last, 4, arithmetic)
            with self.subTest(first=first, last=last), \
                 patch.object(arithmetic, "value", side_effect=AssertionError("no exact decoding")), \
                 patch.object(arithmetic, "mul", side_effect=AssertionError("no exact products")), \
                 patch.object(arithmetic, "add", side_effect=AssertionError("no exact sum")):
                result = reader._recording_uniform_lift_sign(first, last, arithmetic)
            self.assertEqual(result, (exact > 0) - (exact < 0))
            self.assertEqual(work.operations, 1)
            self.assertFalse(work._cache)

    def test_component_range_proves_the_original_small_exact_ratio_domain(self):
        smallest, largest = 2. ** -200, 2. ** 128
        for value in (smallest, math.nextafter(smallest, math.inf), .1,
                      math.nextafter(largest, 0.), largest):
            for sign in (-1., 1.):
                raw = (0., 0., sign * value, 1.)
                with self.subTest(value=value, sign=sign):
                    self.assertEqual(reader._recording_uniform_lift_sign(raw, raw, reader._Bounds(Work())), 1)
                    exact = F(sign * value)
                    self.assertLessEqual(exact.numerator.bit_length(), 129)
                    self.assertLessEqual(exact.denominator.bit_length(), 253)
                    self.assertTrue(reader._small_proof_values((exact,)))

    def test_mixed_signs_types_ranges_and_narrow_caps_keep_the_original_path(self):
        class FloatSubclass(float):
            pass
        first = (0., 0., .125, 1.)
        for last in ((0., 0., -.125, 1.), (0, 0., .125, 1.),
                     (False, 0., .125, 1.), (FloatSubclass(0.), 0., .125, 1.),
                     (0., 0., math.nextafter(2. ** -200, 0.), 1.),
                     (0., 0., math.nextafter(2. ** 128, math.inf), 1.),
                     (0., 0., float("inf"), 1.), (0., 0., float("nan"), 1.),
                     first[:3], list(first)):
            with self.subTest(last=last):
                self.assertIsNone(reader._recording_uniform_lift_sign(first, last, reader._Bounds(Work())))
        work = Work()
        work.max_operand_bits = 256
        self.assertIsNone(reader._recording_uniform_lift_sign(first, first, reader._Bounds(work)))

    def test_complete_sufficient_arc_is_exactly_unchanged_and_costs_less(self):
        first, last = (0., 0., 0., 1.), (0., 0., 2. ** -10, 1.)
        results, costs = [], []
        for shortcut in (False, True):
            work = Work()
            arithmetic = reader._Bounds(work)
            selection = (nullcontext() if shortcut else
                         patch.object(reader, "_recording_uniform_lift_sign", return_value=None))
            with selection, patch.object(arithmetic, "normalize", side_effect=AssertionError("unchanged sufficient arc")):
                results.append(arc(first, last, arithmetic))
            costs.append(work.operations)
            self.assertEqual(work.max_operations, 100000)
        self.assertEqual(results[0], results[1])
        self.assertLess(costs[1], costs[0])

    def test_mixed_sign_and_other_exact_domains_still_decode_actual_components(self):
        pairs = (
            ((0., 0., .0625, 1.), (0., 0., -.0625, 1.)),
            ((0, 0., 0., 1.), (0., 0., 2. ** -10, 1.)),
            ((0., 0., 2. ** -201, 1.), (0., 0., 2. ** -202, 1.)),
        )
        for first, last in pairs:
            arithmetic = reader._Bounds(Work())
            with patch.object(reader, "_recording_uniform_lift_sign", return_value=None):
                original = arc(first, last, reader._Bounds(Work()))
            with self.subTest(first=first, last=last), patch.object(arithmetic, "value", wraps=arithmetic.value) as decode:
                self.assertEqual(arc(first, last, arithmetic), original)
            actual = [call.args[0] for call in decode.call_args_list[:8]]
            self.assertEqual(actual, [*first, *last])
            self.assertTrue(all(type(a) is type(b) for a, b in zip(actual, (*first, *last))))

    def test_negative_lift_keeps_its_exact_diagnostic_without_dot_arithmetic(self):
        first, last = (.5,) * 4, (-.5,) * 4
        outcomes = []
        for shortcut in (False, True):
            arithmetic = reader._Bounds(Work())
            selection = (patch.object(arithmetic, "mul", side_effect=AssertionError("uniform negative sign"))
                         if shortcut else patch.object(reader, "_recording_uniform_lift_sign", return_value=None))
            with selection, self.assertRaises(OntoKinError) as caught:
                arc(first, last, arithmetic)
            outcomes.append(caught.exception.diagnostic)
        self.assertEqual(outcomes[0].details["export_code"], "OKE-E-QUATERNION-LIFT")
        self.assertEqual(outcomes[0], outcomes[1])

    def test_actual_invalid_values_are_rejected_before_any_sign_proof(self):
        first, last = (0., 0., 0., 1.), (0., 0., 2. ** -10, 1.)
        arithmetic = reader._Bounds(Work())
        arc(first, last, arithmetic)
        for invalid in ((False, *first[1:]), (float("nan"), *first[1:]),
                        (float("inf"), *first[1:]), first[:3], (1 << 32768, *first[1:])):
            with self.subTest(invalid_type=type(invalid[0])), \
                 patch.object(reader, "_recording_uniform_lift_sign", side_effect=AssertionError("fresh admission first")), \
                 self.assertRaises((OntoKinError, ReachAdmissionError)):
                arc(invalid, last, arithmetic)

    def test_helper_callback_narrowing_keeps_original_normalization_guard(self):
        work = Work()
        charge = work.charge
        def narrow(kind="checkpoint", amount=1):
            if kind == "independent_stored_lift_sign":
                work.max_operand_bits = 128
            return charge(kind, amount)
        with patch.object(work, "charge", narrow), self.assertRaises(ReachAdmissionError) as caught:
            arc((0., 0., 0., 1.), (0., 0., 2. ** -10, 1.), reader._Bounds(work))
        self.assertEqual(caught.exception.details["limit"], 128)
        self.assertEqual(caught.exception.details["consumed"], 193)

    def test_helper_cancellation_retains_identity_and_publishes_no_partial_proof(self):
        marker = RuntimeError("cancel independent stored lift sign")
        armed = False
        def check():
            if armed:
                raise marker
        work = Work(check=check)
        charge = work.charge
        def charged(kind="checkpoint", amount=1):
            nonlocal armed
            if kind == "independent_stored_lift_sign":
                armed = True
            return charge(kind, amount)
        with patch.object(work, "charge", charged), self.assertRaises(RuntimeError) as caught:
            arc((0., 0., 0., 1.), (0., 0., 2. ** -10, 1.), reader._Bounds(work))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertFalse(work._cache)


class IndependentStoredLiftCompleteGlbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = compile_construction(source_case("P01"))
        cls.options = ExportOptions(end=F(1, 4), fps=8, helpers=False)
        cls.result = export_glb(cls.built.model, options=cls.options,
                               target_contract="ontokin.glb/0.6", work=cls.built.reach_work)
        cls.decoded = read_glb(cls.result.data, target_contract="ontokin.glb/0.6")

    def test_complete_actual_glb_keeps_the_same_result_and_reduces_work(self):
        outcomes, costs = [], []
        for shortcut in (False, True):
            work = Work()
            selection = (nullcontext() if shortcut else
                         patch.object(reader, "_recording_uniform_lift_sign", return_value=None))
            with selection:
                outcomes.append(reader.validate_reach_export(self.result.data, self.built.model,
                                                             options=self.options, work=work))
            costs.append(work.operations)
            self.assertEqual(work.max_operations, 100000)
            self.assertLessEqual(work.operations, 100000)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertLess(costs[1], costs[0])

    def test_forged_actual_arc_claim_is_rejected_with_both_sign_proofs(self):
        observed = []
        add = reader._CertificateBatch.add
        def observe(batch, record, width, stored_width, minima, magnitude):
            observed.append((deepcopy(record), minima["stored_quaternion_arc_upper_rad"]))
            return add(batch, record, width, stored_width, minima, magnitude)
        with original_norm_proofs(), patch.object(reader._CertificateBatch, "add", observe):
            reader.validate_reach_export(self.result.data, self.built.model, options=self.options, work=Work())
        source, exact = max(observed, key=lambda row: row[1])
        self.assertGreater(exact, 0)
        document = deepcopy(self.decoded.document)
        records = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
        selected = next(record for record in records if record["left_key_index"] == source["left_key_index"]
                        and record["carrier"] == source["carrier"])
        selected["stored_quaternion_arc_upper_rad"] = 0.
        changed = replace_document(document, self.decoded.binary)
        outcomes = []
        for shortcut in (False, True):
            selection = (nullcontext() if shortcut else
                         patch.object(reader, "_recording_uniform_lift_sign", return_value=None))
            with selection, self.assertRaises(OntoKinError) as caught:
                reader.validate_reach_export(changed, self.built.model, options=self.options, work=Work())
            outcomes.append(caught.exception.diagnostic.details)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0]["export_code"], "OKE-E-CERTIFICATE")
        self.assertEqual(outcomes[0]["quantity"], "stored_quaternion_arc_upper_rad")


if __name__ == "__main__":
    unittest.main()
