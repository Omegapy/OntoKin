"""Completed independent source arcs retain only a bounded error envelope."""
from contextlib import nullcontext
from copy import deepcopy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recurring_endpoint_claims import replace_document


RAW = ((0., 0., 0., 1.), (0., 0., 2. ** -10, 1.), (0., 0., 2. ** -9, 1.))
ERROR = F(1, 1 << 16)
SPEED, WIDTH, LIMIT = F(1), F(1, 64), .02


def endpoint(raw, error=ERROR):
    return {"quaternion_error": F(error), "normalized": None, "_normalized_cap": None,
            "_proof_cap": 32768, "_quaternion_operand": raw}


def arc(first, last, start, finish, arithmetic, *, speed=SPEED, width=WIDTH,
        limit=LIMIT, source_path_valid=True):
    return reader._certified_stored_arc(first, last, start, finish, speed, width,
                                       limit, arithmetic, source_path_valid=source_path_valid)


def seed(work=None):
    arithmetic = reader._Bounds(work or Work(), cache_intermediates=False)
    first, last = endpoint(RAW[0]), endpoint(RAW[1])
    bound = arc(RAW[0], RAW[1], first, last, arithmetic)
    return arithmetic, last, bound


class IndependentArcReceiptTests(unittest.TestCase):
    def test_lower_current_errors_reuse_a_conservative_independent_envelope(self):
        arithmetic, first, old_bound = seed(Work(max_cache_entries=2))
        saved = deepcopy(first)
        last = endpoint(RAW[2], ERROR / 2)
        cold = arc(RAW[1], RAW[2], endpoint(RAW[1]), endpoint(RAW[2], ERROR / 2),
                   reader._Bounds(Work()))
        before = arithmetic.work.operations
        with patch.object(arithmetic, "normalize", side_effect=AssertionError("proved source arc")), \
             patch.object(arithmetic, "square", side_effect=AssertionError("completed arc envelope")):
            bound = arc(RAW[1], RAW[2], first, last, arithmetic)
        cost = arithmetic.work.operations - before
        cold_work = Work()
        arc(RAW[1], RAW[2], endpoint(RAW[1]), endpoint(RAW[2], ERROR / 2), reader._Bounds(cold_work))
        self.assertEqual(bound, old_bound)
        self.assertGreaterEqual(bound, cold)
        self.assertLessEqual(bound, F(LIMIT))
        self.assertLess(cost, cold_work.operations)
        self.assertEqual(last["_source_arc_receipt"], first["_source_arc_receipt"])
        self.assertEqual(first, saved)
        self.assertEqual(arithmetic.work.max_operations, 100000)
        self.assertLessEqual(arithmetic.work.record()["cache_entries"], 2)

    def test_changed_speed_width_or_larger_current_error_recomputes_the_proof(self):
        for change in ("speed", "width", "error"):
            arithmetic, first, old_bound = seed()
            kwargs = {"speed": SPEED * 2} if change == "speed" else (
                     {"width": WIDTH * 2} if change == "width" else {})
            error = ERROR * 2 if change == "error" else ERROR
            last = endpoint(RAW[2], error)
            with self.subTest(change=change):
                bound = arc(RAW[1], RAW[2], first, last, arithmetic, **kwargs)
                direct = arc(RAW[1], RAW[2], endpoint(RAW[1]), endpoint(RAW[2], error),
                             reader._Bounds(Work()), **kwargs)
                self.assertEqual(bound, direct)
                self.assertGreater(bound, old_bound)

    def test_a_tighter_actual_claim_does_not_inherit_a_larger_prior_bound(self):
        arithmetic, first, old_bound = seed()
        fresh = arc(RAW[1], RAW[2], endpoint(RAW[1]), endpoint(RAW[2], 0), reader._Bounds(Work()))
        limit = (fresh + old_bound) / 2
        last = endpoint(RAW[2], 0)
        self.assertLess(fresh, limit)
        self.assertLess(limit, old_bound)
        self.assertEqual(arc(RAW[1], RAW[2], first, last, arithmetic, limit=limit), fresh)
        self.assertEqual(last["_source_arc_receipt"][4], limit)

    def test_every_actual_sign_is_checked_and_mixed_signs_keep_the_exact_fallback(self):
        arithmetic, first, _ = seed()
        negative = tuple(-value for value in RAW[2])
        last = endpoint(negative, ERROR / 2)
        with self.assertRaises(OntoKinError) as caught:
            arc(RAW[1], negative, first, last, arithmetic)
        self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-QUATERNION-LIFT")
        self.assertNotIn("_source_arc_receipt", last)
        mixed = (0., 0., -RAW[2][2], 1.)
        last = endpoint(mixed, ERROR / 2)
        direct = arc(RAW[1], mixed, endpoint(RAW[1]), endpoint(mixed, ERROR / 2), reader._Bounds(Work()))
        with patch.object(arithmetic, "value", wraps=arithmetic.value) as decode:
            self.assertEqual(arc(RAW[1], mixed, first, last, arithmetic), direct)
        self.assertEqual([call.args[0] for call in decode.call_args_list[:8]], [*RAW[1], *mixed])

    def test_changed_endpoint_proof_or_unretained_source_path_cannot_borrow_a_receipt(self):
        for change in ("cap", "operand", "boundary"):
            arithmetic, first, _ = seed()
            last = endpoint(RAW[2], ERROR / 2)
            if change == "cap":
                last["_proof_cap"] = 128
            elif change == "operand":
                last["_quaternion_operand"] = RAW[0]
            kwargs = {"source_path_valid": False} if change == "boundary" else {}
            with self.subTest(change=change), \
                 patch.object(reader, "_previous_source_arc", wraps=reader._previous_source_arc) as previous:
                bound = arc(RAW[1], RAW[2], first, last, arithmetic, **kwargs)
            direct = arc(RAW[1], RAW[2], endpoint(RAW[1]), endpoint(RAW[2], ERROR / 2),
                         reader._Bounds(Work()), **kwargs)
            self.assertEqual(bound, direct)
            self.assertNotIn("_source_arc_receipt", last)
            if change == "boundary":
                previous.assert_not_called()
                self.assertIsNotNone(first["normalized"])
                self.assertIsNotNone(last["normalized"])

    def test_invalid_current_values_are_admitted_before_receipt_access(self):
        for invalid in ((False, *RAW[2][1:]), (float("nan"), *RAW[2][1:]),
                        (float("inf"), *RAW[2][1:]), RAW[2][:3], (1 << 32768, *RAW[2][1:])):
            arithmetic, first, _ = seed()
            with self.subTest(value_type=type(invalid[0])), \
                 patch.object(reader, "_previous_source_arc", side_effect=AssertionError("fresh admission first")), \
                 self.assertRaises((OntoKinError, ReachAdmissionError)):
                arc(RAW[1], invalid, first, endpoint(invalid), arithmetic)

    def test_cap_narrowing_at_each_reuse_step_keeps_the_original_normalization_guard(self):
        baseline = Work()
        baseline.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as direct:
            arc(RAW[1], RAW[2], endpoint(RAW[1]), endpoint(RAW[2], ERROR / 2), reader._Bounds(baseline))
        checkpoints = (("independent_source_arc_reuse", 1), ("independent_stored_lift_sign", 1),
                       ("independent_exact_add", 1), ("independent_exact_compare", 1),
                       ("independent_exact_compare", 2))
        for checkpoint, occurrence in checkpoints:
            arithmetic, first, _ = seed()
            last = endpoint(RAW[2], ERROR / 2)
            charge, seen = arithmetic.work.charge, 0
            def narrow(kind="checkpoint", amount=1):
                nonlocal seen
                if kind == checkpoint:
                    seen += 1
                    if seen == occurrence:
                        arithmetic.work.max_operand_bits = 128
                return charge(kind, amount)
            with self.subTest(checkpoint=checkpoint, occurrence=occurrence), \
                 patch.object(arithmetic.work, "charge", narrow), self.assertRaises(ReachAdmissionError) as caught:
                arc(RAW[1], RAW[2], first, last, arithmetic, limit=.025)
            self.assertEqual(caught.exception.details["limit"], 128)
            self.assertEqual(caught.exception.details["consumed"], direct.exception.details["consumed"])
            self.assertNotIn("_source_arc_receipt", last)

    def test_each_reuse_callback_can_cancel_without_publishing_a_receipt(self):
        for checkpoint, occurrence in (("independent_source_arc_reuse", 1), ("independent_stored_lift_sign", 1),
                                       ("independent_exact_add", 1), ("independent_exact_compare", 1),
                                       ("independent_exact_compare", 2)):
            arithmetic, first, _ = seed()
            last = endpoint(RAW[2], ERROR / 2)
            saved = deepcopy((first, last))
            marker = RuntimeError("cancel source arc receipt")
            charge, seen = arithmetic.work.charge, 0
            def cancel(kind="checkpoint", amount=1):
                nonlocal seen
                if kind == checkpoint:
                    seen += 1
                    if seen == occurrence:
                        def fail():
                            raise marker
                        arithmetic.work.external_check = fail
                return charge(kind, amount)
            with self.subTest(checkpoint=checkpoint, occurrence=occurrence), \
                 patch.object(arithmetic.work, "charge", cancel), self.assertRaises(RuntimeError) as caught:
                arc(RAW[1], RAW[2], first, last, arithmetic, limit=.025)
            self.assertIs(caught.exception, marker)
            self.assertIs(arithmetic.work.callback_error, marker)
            self.assertEqual((first, last), saved)

    def test_cold_receipt_is_not_published_after_the_claim_comparison_narrows_the_cap(self):
        arithmetic = reader._Bounds(Work())
        first, last = endpoint(RAW[0]), endpoint(RAW[1])
        compare = arithmetic.compare
        def narrow(a, b):
            result = compare(a, b)
            if type(b) is float and b == LIMIT:
                arithmetic.work.max_operand_bits = 128
            return result
        with patch.object(arithmetic, "compare", narrow), self.assertRaises(ReachAdmissionError) as caught:
            arc(RAW[0], RAW[1], first, last, arithmetic)
        self.assertEqual(caught.exception.details["limit"], 128)
        self.assertEqual(caught.exception.details["consumed"], 193)
        self.assertNotIn("_source_arc_receipt", last)


class IndependentArcReceiptCompleteGlbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = compile_construction(source_case("P01"))
        cls.options = ExportOptions(end=F(1, 4), fps=32, helpers=False)
        cls.result = export_glb(cls.built.model, options=cls.options,
                               target_contract="ontokin.glb/0.6", work=cls.built.reach_work)
        cls.decoded = read_glb(cls.result.data, target_contract="ontokin.glb/0.6")

    def test_actual_source_and_bytes_keep_the_result_with_lower_work(self):
        outcomes, costs, hits = [], [], []
        original = reader._previous_source_arc
        def observe(*args):
            receipt = original(*args)
            if receipt is not None:
                hits.append(receipt)
            return receipt
        for enabled in (False, True):
            work = Work(max_cache_entries=256)
            selection = (patch.object(reader, "_previous_source_arc", observe) if enabled else
                         patch.object(reader, "_previous_source_arc", return_value=None))
            with selection:
                outcomes.append(reader.validate_reach_export(self.result.data, self.built.model,
                                                             options=self.options, work=work))
            costs.append(work.operations)
            self.assertEqual(work.max_operations, 100000)
            self.assertLessEqual(work.record()["cache_entries"], 256)
        self.assertTrue(hits)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertLess(costs[1], costs[0])

    def test_a_changed_actual_arc_claim_still_fails_the_complete_checker(self):
        document = deepcopy(self.decoded.document)
        records = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
        selected = max(records, key=lambda row: (row["left_key_index"], row["stored_quaternion_arc_upper_rad"]))
        self.assertGreater(selected["stored_quaternion_arc_upper_rad"], 0)
        selected["stored_quaternion_arc_upper_rad"] = 0.
        changed = replace_document(document, self.decoded.binary)
        outcomes = []
        for enabled in (False, True):
            selection = nullcontext() if enabled else patch.object(reader, "_previous_source_arc", return_value=None)
            with selection, self.assertRaises(OntoKinError) as caught:
                reader.validate_reach_export(changed, self.built.model, options=self.options, work=Work())
            outcomes.append(caught.exception.diagnostic.details)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[0]["export_code"], "OKE-E-CERTIFICATE")
        self.assertEqual(outcomes[0]["quantity"], "stored_quaternion_arc_upper_rad")


if __name__ == "__main__":
    unittest.main()
