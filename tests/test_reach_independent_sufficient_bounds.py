"""Independent sufficient inequalities keep exact fallbacks and hostile claims."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from fractions import Fraction as F
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin import reach_conformance as reader
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.gltf import export_glb, read_glb
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork as Work
from ontokin.reach_reference import ReachReference
from ontokin.scene import ExportOptions
from reach_agent_support import source_case
from test_reach_recurring_endpoint_claims import replace_document


def point(value):
    return reader._Cell(F(value), F(value))


def cells(values):
    return tuple(map(point, values))


def endpoint(error=0):
    return {"quaternion_error": F(error), "normalized": None, "_normalized_cap": None}


@contextmanager
def original_norm_proofs():
    """Select the retained exact comparators, without changing any limits."""
    def orientation(quaternion, expected, limit, arithmetic, *, before_error=None):
        return reader._recording_orientation_comparison(quaternion, expected, arithmetic, before_error=before_error)
    def position(actual, expected, limit, arithmetic):
        return arithmetic.difference(actual, expected)
    def arc(raw_first, raw_last, first, last, angular_speed, width, limit, arithmetic,
            *, source_path_valid=True):
        return reader._stored_arc(raw_first, raw_last, first["normalized"], last["normalized"], arithmetic)
    with ExitStack() as stack:
        # This control deliberately requests complete interval normalization.
        # The current sufficient/fallback checker runs outside this context.
        stack.enter_context(patch.object(ReachReference, "_recording_centered_poses", return_value=None))
        stack.enter_context(patch.object(reader, "_recording_orientation_bound", orientation))
        stack.enter_context(patch.object(reader, "_recording_position_bound", position))
        stack.enter_context(patch.object(reader, "_certified_stored_arc", arc))
        yield


class IndependentSufficientEndpointTests(unittest.TestCase):
    def test_factor_two_encloses_exact_normalized_error_without_a_root(self):
        source = cells((0, 0, F(3, 5), F(4, 5)))
        for raw in ((0., 0., .6, .8), (0., 0., .6 + 2. ** -24, .8),
                    (0., 0., -.6, -.8), (0., 0., .6, .8 - 2. ** -24)):
            with self.subTest(raw=raw):
                expected = reader._recording_orientation_comparison(raw, source, reader._Bounds(Work()))
                work = Work()
                arithmetic = reader._Bounds(work)
                with patch.object(arithmetic, "normalize", side_effect=AssertionError("unneeded normalized endpoint")), \
                     patch.object(arithmetic, "root", side_effect=AssertionError("unneeded endpoint root")):
                    normalized, error = reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
                self.assertIsNone(normalized)
                self.assertGreaterEqual(error, expected[1])
                self.assertLessEqual(error, F(1e-5))
                self.assertEqual(work.max_operations, 100000)

    def test_a_tighter_claim_keeps_the_exact_position_norm(self):
        work = Work()
        arithmetic = reader._Bounds(work)
        with patch.object(arithmetic, "norm", wraps=arithmetic.norm) as norm:
            self.assertEqual(reader._recording_position_bound((0., 0., 0.), cells((3, 4, 0)), 5., arithmetic), 5)
        self.assertEqual(norm.call_count, 1)
        self.assertEqual(reader._recording_position_bound((0., 0., 0.), cells((3, 4, 0)), 7., arithmetic), 7)

    def test_nonunit_raw_quaternion_uses_its_original_normalized_meaning(self):
        arithmetic = reader._Bounds(Work())
        with patch.object(arithmetic, "normalize", wraps=arithmetic.normalize) as normalize:
            result = reader._recording_orientation_bound((0., 0., 0., 2.), cells((0, 0, 0, 1)), 0., arithmetic)
        self.assertEqual(result, (cells((0, 0, 0, 1)), F(0)))
        self.assertEqual(normalize.call_count, 1)

    def test_zero_and_near_zero_raw_quaternions_keep_the_original_rejection(self):
        for raw in ((0., 0., 0., 0.), (0., 0., 0., 2. ** -200),
                    (0., 0., 0., math.ldexp(1., -1074))):
            outcomes = []
            for sufficient in (False, True):
                arithmetic = reader._Bounds(Work())
                with self.subTest(raw=raw, sufficient=sufficient), self.assertRaises(OntoKinError) as caught:
                    if sufficient:
                        reader._recording_orientation_bound(raw, cells((0, 0, 0, 1)), .5, arithmetic)
                    else:
                        reader._recording_orientation_comparison(raw, cells((0, 0, 0, 1)), arithmetic)
                outcomes.append(caught.exception.diagnostic.details["export_code"])
            self.assertEqual(outcomes, ["OKE-E-QUATERNION"] * 2)

    def test_wide_source_enclosures_never_become_exact_zero(self):
        source = (reader._Cell(F(-1), F(1)),) * 3 + (reader._Cell(F(0), F(1)),)
        arithmetic = reader._Bounds(Work())
        with patch.object(arithmetic, "normalize", wraps=arithmetic.normalize) as normalize:
            normalized, error = reader._recording_orientation_bound((0., 0., 0., 1.), source, .5, arithmetic)
        self.assertIsNotNone(normalized)
        self.assertGreater(error, 1)
        self.assertEqual(normalize.call_count, 1)

    def test_changed_claim_and_source_cells_cannot_borrow_a_sufficient_proof(self):
        raw = (0., 0., .6, .8 + 2. ** -24)
        source = cells((0, 0, F(3, 5), F(4, 5)))
        arithmetic = reader._Bounds(Work())
        self.assertIsNone(reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)[0])
        normalized, error = reader._recording_orientation_bound(raw, source, 0., arithmetic)
        self.assertIsNotNone(normalized)
        self.assertGreater(error, 0)
        opposite = tuple(reader._Cell(-value.hi, -value.lo) for value in source)
        self.assertEqual(reader._recording_orientation_bound(raw, source, 1e-5, arithmetic),
                         reader._recording_orientation_bound(raw, opposite, 1e-5, arithmetic))
        changed = (*source[:2], reader._Cell(F(1, 2), F(7, 10)), source[3])
        self.assertGreater(reader._recording_orientation_bound(raw, changed, 1e-5, arithmetic)[1], error)

    def test_invalid_shape_scalar_and_interval_are_rejected_before_lookup(self):
        raw, source = (0., 0., 0., 1.), cells((0, 0, 0, 1))
        work = Work()
        arithmetic = reader._Bounds(work)
        reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
        for actual, expected in ((raw[:3], source), ((False, *raw[1:]), source),
                ((float("nan"), *raw[1:]), source), (raw, source[:3]),
                (raw, (reader._Cell(F(1), F(0)), *source[1:])),
                (raw, (point(F(1 << 32768)), *source[1:]))):
            with self.subTest(actual=actual, expected_type=type(expected[0])), \
                 patch.object(work, "lookup", wraps=work.lookup) as lookup:
                with self.assertRaises((OntoKinError, ReachAdmissionError)):
                    reader._recording_orientation_bound(actual, expected, 1e-5, arithmetic)
                lookup.assert_not_called()

    def test_warm_sufficient_proof_keeps_original_narrow_root_domain(self):
        raw, source = (0., 0., 0., 1.), cells((0, 0, 0, 1))
        work = Work()
        arithmetic = reader._Bounds(work)
        reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
        work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as caught:
            reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
        self.assertEqual(caught.exception.details["consumed"], 193)

    def test_live_cap_changes_on_lookup_insert_or_position_keep_original_domain(self):
        raw, source = (0., 0., 0., 1.), cells((0, 0, 0, 1))
        for checkpoint in ("independent_sufficient_orientation_domain", "cache_lookup", "cache_insert", "position"):
            work = Work()
            arithmetic = reader._Bounds(work)
            charge = work.charge
            def charged(kind="checkpoint", amount=1):
                if kind == checkpoint:
                    work.max_operand_bits = 128
                return charge(kind, amount)
            before_error = lambda: charged("position")
            with self.subTest(checkpoint=checkpoint), patch.object(work, "charge", charged), \
                 self.assertRaises(ReachAdmissionError) as caught:
                reader._recording_orientation_bound(raw, source, 1e-5, arithmetic, before_error=before_error)
            self.assertEqual(caught.exception.details["consumed"], 193)

    def test_cancellation_on_warm_lookup_keeps_the_original_exception(self):
        raw, source = (0., 0., 0., 1.), cells((0, 0, 0, 1))
        work = Work()
        arithmetic = reader._Bounds(work)
        reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
        marker = RuntimeError("cancel sufficient endpoint lookup")
        lookup = work.lookup
        def cancelled(key):
            def fail():
                raise marker
            work.external_check = fail
            return lookup(key)
        with patch.object(work, "lookup", cancelled), self.assertRaises(RuntimeError) as caught:
            reader._recording_orientation_bound(raw, source, 1e-5, arithmetic)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)

    def test_sign_selection_checks_the_callback_current_cell_domain(self):
        source = (*cells((0, 0, 0)), reader._Cell(F(1) - F(1, 1 << 200), F(1)))
        for sufficient in (False, True):
            work = Work()
            arithmetic = reader._Bounds(work)
            charge = work.charge
            def charged(kind="checkpoint", amount=1):
                if kind == "independent_quaternion_sign":
                    work.max_operand_bits = 64
                return charge(kind, amount)
            with self.subTest(sufficient=sufficient), patch.object(work, "charge", charged), \
                 self.assertRaises(ReachAdmissionError) as caught:
                if sufficient:
                    reader._recording_orientation_bound((0., 0., 0., -1.), source, 1e-5, arithmetic)
                else:
                    reader._recording_orientation_comparison((0., 0., 0., -1.), source, arithmetic)
            self.assertEqual(caught.exception.details["limit"], 64)
            self.assertEqual(caught.exception.details["consumed"], 201)

    def test_stationary_endpoint_rechecks_a_tighter_adjacent_claim(self):
        epsilon = F(1, 1 << 40)
        orientation = (reader._Cell(F(1, 2) - epsilon, F(1, 2) + epsilon),) * 4
        pose = SimpleNamespace(position=cells((0, 0, 0)), orientation=orientation)
        reference = SimpleNamespace(
            recording_pose_enclosures=lambda carriers, time, side, recording_context=None: {"frame": pose},
            recording_stationary_frames=lambda carriers, first, last, side: frozenset(carriers))
        geometry = {0: {"frame": "frame"}}
        tracks = {0: {"translation": [(0.,) * 3] * 2, "rotation": [(.5,) * 4] * 2}}
        rows = {(0, 0): {"max_endpoint_position_error_m": 0., "max_endpoint_unit_quaternion_error": 1e-5},
                (1, 0): {"max_endpoint_position_error_m": 0., "max_endpoint_unit_quaternion_error": float(2 * epsilon)}}
        arithmetic = reader._Bounds(Work())
        previous = reader._key_comparisons(reference, geometry, tracks, F(0), 0, arithmetic, endpoint_rows=rows)
        self.assertEqual(previous[0]["quaternion_error"], 8 * epsilon)
        following = reader._key_comparisons(reference, geometry, tracks, F(1), 1, arithmetic,
                                           previous=previous, previous_time=F(0), endpoint_rows=rows)
        self.assertEqual(following[0]["quaternion_error"], 2 * epsilon)
        self.assertIsNotNone(following[0]["normalized"])
        arithmetic.work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError):
            reader._key_comparisons(reference, geometry, tracks, F(1), 1, arithmetic,
                                    previous=previous, previous_time=F(0), endpoint_rows=rows)

    def test_complete_sufficient_bounds_keep_the_existing_lru_limit(self):
        work = Work(max_cache_entries=2)
        arithmetic = reader._Bounds(work)
        source = cells((0, 0, 0, 1))
        for offset in (2. ** -24, 2. ** -23, 2. ** -22, 2. ** -24):
            raw = (0., 0., offset, 1.)
            self.assertEqual(reader._recording_orientation_bound(raw, source, 1e-5, arithmetic),
                             reader._recording_orientation_bound(raw, source, 1e-5, reader._Bounds(Work())))
            self.assertLessEqual(len(work._cache), 2)


class IndependentSufficientArcTests(unittest.TestCase):
    def test_identical_admitted_operands_have_zero_arc_across_independent_anchors(self):
        raw = (0., 0., .6, .8)
        arithmetic = reader._Bounds(Work())
        normalized, error = reader._recording_orientation_bound(
            raw, cells((0, 0, F(3, 5), F(4, 5))), 1e-5, arithmetic)
        proof = {"quaternion_error": error, "normalized": normalized,
                 "_proof_cap": 32768, "_quaternion_operand": raw, "_normalized_cap": None}
        with patch.object(arithmetic, "normalize", side_effect=AssertionError("identical completed endpoints")), \
             patch.object(arithmetic, "mul", side_effect=AssertionError("no dot or source-path product")):
            for source_path_valid in (False, True):
                self.assertEqual(reader._certified_stored_arc(raw, raw, dict(proof), dict(proof),
                    F(100), F(1), 0., arithmetic, source_path_valid=source_path_valid), 0)

    def test_identical_raw_values_cannot_borrow_a_different_or_stale_endpoint_proof(self):
        proved = (0., 0., 0., 1.)
        proof = {**endpoint(), "_proof_cap": 32768, "_quaternion_operand": proved}
        for raw in ((0.,) * 4, (0., 0., 0., 2. ** -200)):
            with self.subTest(raw=raw), self.assertRaises(OntoKinError) as caught:
                reader._certified_stored_arc(raw, raw, dict(proof), dict(proof), F(0), F(1), 0.,
                    reader._Bounds(Work()), source_path_valid=False)
            self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-QUATERNION")
        arithmetic = reader._Bounds(Work())
        charge = arithmetic.work.charge
        def narrow(kind="checkpoint", amount=1):
            if kind == "independent_sufficient_arc_domain":
                arithmetic.work.max_operand_bits = 128
            return charge(kind, amount)
        with patch.object(arithmetic.work, "charge", narrow), self.assertRaises(ReachAdmissionError) as caught:
            reader._certified_stored_arc(proved, proved, dict(proof), dict(proof), F(0), F(1), 0.,
                                         arithmetic, source_path_valid=False)
        self.assertEqual(caught.exception.details["consumed"], 193)

    def test_identical_endpoint_shortcut_keeps_cancellation_identity(self):
        raw = (0., 0., 0., 1.)
        proof = {**endpoint(), "_proof_cap": 32768, "_quaternion_operand": raw}
        marker = RuntimeError("cancel identical stored endpoints")
        def cancel():
            raise marker
        arithmetic = reader._Bounds(Work(check=cancel))
        with self.assertRaises(RuntimeError) as caught:
            reader._certified_stored_arc(raw, raw, dict(proof), dict(proof), F(0), F(1), 0., arithmetic)
        self.assertIs(caught.exception, marker)
        self.assertIs(arithmetic.work.callback_error, marker)

    def test_outgoing_boundary_anchor_keeps_the_actual_normalized_arc(self):
        first, last = (0., 0., 0., 1.), (0., 0., 2. ** -10, 1.)
        arithmetic = reader._Bounds(Work())
        start, finish = endpoint(), endpoint()
        # Zero error against two independently selected anchors and a zero
        # incoming speed do not prove continuity between those anchors.
        bound = reader._certified_stored_arc(first, last, start, finish, F(0), F(1), 0., arithmetic,
                                             source_path_valid=False)
        original = reader._Bounds(Work())
        expected = reader._stored_arc(first, last, original.normalize(first), original.normalize(last), original)
        self.assertEqual(bound, expected)
        self.assertGreater(bound, 0)
        self.assertIsNotNone(start["normalized"])
        self.assertIsNotNone(finish["normalized"])

    def test_independent_source_path_and_endpoint_errors_bound_actual_arc(self):
        first, last = (0., 0., 0., 1.), (0., 0., 2. ** -10, 1.)
        arithmetic = reader._Bounds(Work())
        start, finish = endpoint(), endpoint(F(1, 1 << 19))
        with patch.object(arithmetic, "normalize", side_effect=AssertionError("unneeded arc normalization")), \
             patch.object(arithmetic, "root", side_effect=AssertionError("unneeded arc root")):
            bound = reader._certified_stored_arc(first, last, start, finish, F(1), F(1, 64), .01, arithmetic)
        original = reader._Bounds(Work())
        direct = reader._stored_arc(first, last, original.normalize(first), original.normalize(last), original)
        self.assertGreaterEqual(bound, direct)
        self.assertLessEqual(bound, F(.01))
        self.assertIsNone(start["normalized"])

    def test_insufficient_source_path_bound_falls_back_to_actual_shorter_arc(self):
        raw = (0., 0., 0., 1.)
        first, last = endpoint(), endpoint()
        arithmetic = reader._Bounds(Work())
        self.assertEqual(reader._certified_stored_arc(raw, raw, first, last, F(4), F(1, 10), 0., arithmetic), 0)
        self.assertIsNotNone(first["normalized"])
        with patch.object(arithmetic, "normalize", side_effect=AssertionError("repeated lazy normalization")):
            self.assertEqual(reader._certified_stored_arc(raw, raw, first, last, F(4), F(1, 10), 0., arithmetic), 0)

    def test_negative_raw_dot_and_zero_dot_keep_the_actual_lift_rejections(self):
        first = (0., 0., 0., 1.)
        for last, speed in (((0., 0., 0., -1.), F(0)), ((1., 0., 0., 0.), F(4))):
            with self.subTest(last=last), self.assertRaises(OntoKinError) as caught:
                reader._certified_stored_arc(first, last, endpoint(), endpoint(), speed, F(1), .5,
                                             reader._Bounds(Work()))
            self.assertEqual(caught.exception.diagnostic.details["export_code"], "OKE-E-QUATERNION-LIFT")

    def test_warm_arc_rechecks_current_raw_sign_and_operand_cap(self):
        raw = (0., 0., 0., 1.)
        arithmetic = reader._Bounds(Work())
        first, last = endpoint(), endpoint()
        self.assertEqual(reader._certified_stored_arc(raw, raw, first, last, F(0), F(1), 0., arithmetic), 0)
        with self.assertRaises(OntoKinError):
            reader._certified_stored_arc(raw, (0., 0., 0., -1.), first, last, F(0), F(1), 0., arithmetic)
        arithmetic.work.max_operand_bits = 128
        with self.assertRaises(ReachAdmissionError) as caught:
            reader._certified_stored_arc(raw, raw, first, last, F(0), F(1), 0., arithmetic)
        self.assertEqual(caught.exception.details["consumed"], 193)


class IndependentSufficientCompleteGlbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = compile_construction(source_case("P01"))
        cls.options = ExportOptions(end=F(1, 4), fps=8, helpers=False)
        cls.result = export_glb(cls.built.model, options=cls.options,
                               target_contract="ontokin.glb/0.6", work=cls.built.reach_work)
        cls.decoded = read_glb(cls.result.data, target_contract="ontokin.glb/0.6")

    def test_complete_actual_glb_validation_matches_original_norm_proofs(self):
        outcomes, costs = [], []
        for sufficient in (False, True):
            work = Work()
            with ExitStack() as stack:
                if not sufficient:
                    stack.enter_context(original_norm_proofs())
                outcomes.append(reader.validate_reach_export(self.result.data, self.built.model,
                                                             options=self.options, work=work))
            costs.append(work.operations)
            self.assertEqual(work.max_operations, 100000)
            self.assertLessEqual(work.operations, 100000)
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertLess(costs[1], costs[0])

    def test_complete_checker_excludes_the_final_outgoing_anchor_from_source_paths(self):
        source_paths = []
        original = reader._certified_stored_arc
        def observe(*args, **kwargs):
            source_paths.append(kwargs["source_path_valid"])
            return original(*args, **kwargs)
        with patch.object(reader, "_certified_stored_arc", observe):
            reader.validate_reach_export(self.result.data, self.built.model, options=self.options, work=Work())
        self.assertTrue(source_paths)
        self.assertIn(True, source_paths)
        self.assertIs(source_paths[-1], False)

    def test_forged_exact_endpoint_and_arc_claims_fail_both_complete_checkers(self):
        observed = []
        original_add = reader._CertificateBatch.add
        def observe(batch, record, width, stored_width, minima, magnitude):
            observed.append((deepcopy(record), dict(minima)))
            return original_add(batch, record, width, stored_width, minima, magnitude)
        with original_norm_proofs(), patch.object(reader._CertificateBatch, "add", observe):
            reader.validate_reach_export(self.result.data, self.built.model, options=self.options, work=Work())
        for quantity in ("max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error",
                         "stored_quaternion_arc_upper_rad", "angular_speed_bound_rad_per_s"):
            source, minimum = max(((record, minima[quantity]) for record, minima in observed), key=lambda pair: pair[1])
            self.assertGreater(minimum, 0)
            document = deepcopy(self.decoded.document)
            records = document["extras"]["ontokin"]["reach_quantization"]["interval_certificates"]
            selected = next(record for record in records if record["left_key_index"] == source["left_key_index"]
                            and record["carrier"] == source["carrier"])
            selected[quantity] = 0.
            changed = replace_document(document, self.decoded.binary)
            outcomes = []
            for sufficient in (False, True):
                with self.subTest(quantity=quantity, sufficient=sufficient), ExitStack() as stack:
                    if not sufficient:
                        stack.enter_context(original_norm_proofs())
                    with self.assertRaises(OntoKinError) as caught:
                        reader.validate_reach_export(changed, self.built.model, options=self.options, work=Work())
                    outcomes.append(caught.exception.diagnostic.details)
            self.assertEqual(outcomes[0]["export_code"], "OKE-E-CERTIFICATE")
            self.assertEqual(outcomes[0]["quantity"], quantity)
            self.assertEqual(outcomes[0], outcomes[1])

    def test_complete_reader_cancellation_propagates_without_a_success_result(self):
        marker = RuntimeError("cancel sufficient supplied-byte validation")
        def cancel():
            raise marker
        work = Work(check=cancel)
        with self.assertRaises(RuntimeError) as caught:
            reader.validate_reach_export(self.result.data, self.built.model, options=self.options, work=work)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)
        self.assertEqual(work.operations, 0)


if __name__ == "__main__":
    unittest.main()
