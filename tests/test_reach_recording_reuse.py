"""Source-proved endpoint and current-interval supplied-claim reuse."""
from contextlib import nullcontext
import copy
from fractions import Fraction as F
import unittest
from unittest.mock import patch

from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import _Bounds, _IntervalCertificateClaims, _key_comparisons, _recording_vector, rational_clock
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork
from ontokin.reach_reference import MAX_CACHE, MAX_OPERAND_BITS, ReferenceError, build_reference
from reach_agent_support import source_case
from test_reach_conformance import ratio


def reference_case(name, end):
    compiler = compile_construction(source_case(name))
    return build_reference(compiler.model, end=end, work=compiler.reach_work), compiler.reach_work


class IndependentRecordingStationarityTests(unittest.TestCase):
    def test_source_ancestry_proof_keeps_moving_descendants_and_event_sides(self):
        reference, _ = reference_case("P01", F(3))
        carriers = ("world", "rig.frame", "rig.column.frame", "rig.arm.upper.frame",
                    "rig.arm.forearm.frame", "rig.arm.forearm.tip.frame", "rig.tool.frame")
        stationary = reference.recording_stationary_frames(carriers, F(1, 4), F(1, 2))
        self.assertEqual(stationary, frozenset(carriers[:4]))
        first = reference.recording_pose_enclosures(carriers, F(1, 4))
        last = reference.recording_pose_enclosures(carriers, F(1, 2))
        for carrier in stationary:
            self.assertEqual(first[carrier], last[carrier])
        self.assertNotEqual(first["rig.tool.frame"], last["rig.tool.frame"])
        self.assertEqual(reference.recording_stationary_frames(carriers, F(7, 4), F(2)), frozenset())
        self.assertEqual(reference.recording_stationary_frames(carriers, F(9, 4), F(5, 2)), frozenset(carriers))

    def test_paused_new_owner_and_dynamic_ancestors_are_distinct(self):
        carriers = ("rig.frame", "rig.arm.upper.frame", "rig.arm.forearm.tip.frame")
        paused, _ = reference_case("L01", F(2))
        self.assertEqual(paused.recording_stationary_frames(carriers, F(3, 4), F(5, 4)), frozenset(carriers))
        self.assertEqual(paused.recording_stationary_frames(carriers, F(5, 4), F(3, 2)), frozenset())
        self.assertEqual(paused.recording_stationary_frames(carriers, F(3, 2), F(7, 4)), frozenset(carriers[:1]))
        switched, _ = reference_case("L02", F(1))
        self.assertEqual(switched.recording_stationary_frames(carriers, F(1, 4), F(3, 4)), frozenset())
        released, _ = reference_case("P16", F(3))
        self.assertEqual(released.recording_stationary_frames(("world", "payload.frame"), F(9, 4), F(5, 2)),
                         frozenset(("world",)))
        self.assertEqual(released.recording_stationary_frames(("rig.frame",), F(1, 4), F(1, 2)), frozenset())

    def test_actual_and_ideal_coordinate_laws_must_both_be_stationary(self):
        reference, _ = reference_case("P01", F(1, 2))
        state = reference._state_at(F(1, 4), "after")
        active = state.actions["reach"]
        # An interrupted source can have distinct actual and ideal initial
        # coordinates. Zero ideal slope alone does not establish this proof.
        active.initial = (0.0, .125)
        active.ideal_initial = (F(0), F(0))
        active.targets = (0.0, 0.0)
        carrier = "rig.arm.forearm.frame"
        self.assertEqual(reference.recording_stationary_frames((carrier,), F(1, 4), F(1, 2)), frozenset())
        active.initial = (0.0, 0.0)
        self.assertEqual(reference.recording_stationary_frames((carrier,), F(1, 4), F(1, 2)), frozenset((carrier,)))
        huge = F(1 << MAX_OPERAND_BITS)
        active.initial = active.ideal_initial = active.targets = (F(0), huge)
        with self.assertRaises(ReferenceError) as caught:
            reference.recording_stationary_frames((carrier,), F(1, 4), F(1, 2))
        self.assertEqual(caught.exception.code, "resource")

    def test_stationarity_retains_selection_time_and_original_callback_guards(self):
        reference, work = reference_case("P01", F(1, 2))
        for carriers, first, last, side in ((["missing"], F(0), F(1, 4), "after"),
                (["world"], F(1, 4), F(0), "after"), (["world"], F(0), F(1), "after"),
                (["world"], F(0), F(1, 4), "left"), ("world", F(0), F(1, 4), "after")):
            with self.subTest(carriers=carriers, first=first, last=last, side=side), self.assertRaises(ReferenceError):
                reference.recording_stationary_frames(carriers, first, last, side)
        self.assertEqual(reference.recording_stationary_frames([], F(1, 4), F(1, 2)), frozenset())
        marker = RuntimeError("cancel source stationarity proof")
        with patch.object(work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                reference.recording_stationary_frames(["world"], F(1, 4), F(1, 2))
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)


class IndependentRecordingEndpointReuseTests(unittest.TestCase):
    def test_finite_float_endpoint_guard_honors_a_narrower_request_limit(self):
        work = ReachExecutionWork()
        arithmetic = _Bounds(work)
        point = (0., 1., float(F(1, 1 << 100)))
        self.assertEqual(_recording_vector(point, 3, arithmetic), point)
        work.max_operand_bits = 64
        self.assertEqual(_recording_vector((0., 1., 2.), 3, arithmetic), (0., 1., 2.))
        with self.assertRaises(ReachAdmissionError):
            _recording_vector(point, 3, arithmetic)
        self.assertGreater(work.counts["independent_bound_decode"], 0)

    def endpoint_run(self, reuse):
        reference, work = reference_case("P01", F(3))
        carriers = tuple(path + ".frame" for path in reference.model.objects)
        geometry = {index: {"frame": carrier} for index, carrier in enumerate(carriers)}
        values = reference.recording_pose_enclosures(carriers, F(9, 4))
        tracks = {}
        for index, carrier in enumerate(carriers):
            value = values[carrier]
            position = tuple(float((part.lo + part.hi) / 2) for part in value.position)
            rotation = tuple(float((part.lo + part.hi) / 2) for part in value.orientation)
            rotation = (*rotation[1:], rotation[0])
            tracks[index] = {"translation": [position, position], "rotation": [rotation, rotation]}
        arithmetic = _Bounds(work)
        previous = _key_comparisons(reference, geometry, tracks, F(9, 4), 0, arithmetic)
        # Exercise the intended large-graph situation: unrelated pure work
        # evicts numeric entries, while the required prior endpoint remains.
        for index in range(MAX_CACHE + 1):
            reference.a.remember(("unrelated", index), F(index))
            work.remember(("unrelated", index), F(index))
        start = work.operations
        context = nullcontext() if reuse else patch.object(reference, "recording_stationary_frames", return_value=frozenset())
        with context:
            following = _key_comparisons(reference, geometry, tracks, F(5, 2), 1, arithmetic,
                                         previous=previous, previous_time=F(9, 4))
        self.assertEqual(following, previous)
        self.assertIsNot(following, previous)
        self.assertTrue(all(following[key] is not previous[key] for key in previous))
        self.assertLessEqual(len(reference.a.cache), MAX_CACHE)
        self.assertLessEqual(work.record()["cache_entries"], 256)
        return following, work.operations - start

    def test_unchanged_supplied_endpoints_retain_exact_results_without_numeric_cache_growth(self):
        reused, used = self.endpoint_run(True)
        recomputed, original_cost = self.endpoint_run(False)
        self.assertEqual(reused, recomputed)
        self.assertGreater(used, 0)
        self.assertLess(used, original_cost)

    def test_changed_stored_values_and_moving_ideal_are_always_compared(self):
        reference, work = reference_case("P01", F(1, 2))
        geometry = {0: {"frame": "rig.frame"}, 1: {"frame": "rig.arm.forearm.frame"}}
        tracks = {index: {"translation": [(0., 0., 0.)] * 2, "rotation": [(0., 0., 0., 1.)] * 2}
                  for index in geometry}
        arithmetic = _Bounds(work)
        previous = _key_comparisons(reference, geometry, tracks, F(1, 4), 0, arithmetic)
        with patch.object(reference, "recording_pose_enclosures", wraps=reference.recording_pose_enclosures) as evaluate:
            following = _key_comparisons(reference, geometry, tracks, F(1, 2), 1, arithmetic,
                                         previous=previous, previous_time=F(1, 4))
        self.assertEqual(evaluate.call_args.args[0], ("rig.arm.forearm.frame",))
        self.assertEqual(following[0], previous[0])
        self.assertNotEqual(following[1]["quaternion_error"], previous[1]["quaternion_error"])
        tracks[0]["translation"][1] = (.001, 0., 0.)
        changed = _key_comparisons(reference, geometry, tracks, F(1, 2), 1, arithmetic,
                                   previous=previous, previous_time=F(1, 4))
        self.assertGreater(changed[0]["position_error"], previous[0]["position_error"])
        tracks[0]["translation"][1] = (False, 0., 0.)
        with self.assertRaises(OntoKinError):
            _key_comparisons(reference, geometry, tracks, F(1, 2), 1, arithmetic,
                             previous=previous, previous_time=F(1, 4))


class IndependentIntervalClaimTests(unittest.TestCase):
    def claims(self, work):
        return _IntervalCertificateClaims((F(0), F(1), F(2), F(3)), F(1, 2), F(1), [0], F(1, 2), F(1, 2), work)

    def record(self):
        return {"source_phase_indices": [0], "h_authored_seconds": ratio(F(1, 2)),
                "h_stored_seconds": ratio(F(1, 2))}

    def test_repeated_claims_reuse_only_validated_current_interval_inputs(self):
        work, record = ReachExecutionWork(), self.record()
        claims = self.claims(work)
        with patch("ontokin.reach_conformance.rational_clock", wraps=rational_clock) as parse:
            for _ in range(12):
                self.assertEqual(claims.check(copy.deepcopy(record)), (0,))
        self.assertEqual(parse.call_count, 2)
        self.assertEqual(work.counts["independent_interval_claim"], 12)
        # Exact endpoint-only contact is still permitted for the next phase.
        record["source_phase_indices"] = [0, 1]
        self.assertEqual(claims.check(record), (0, 1))
        # A different interval must validate its own widths and source spans.
        later = _IntervalCertificateClaims(claims.boundaries, F(2), F(3), [2], F(1), F(1), work)
        with self.assertRaises(OntoKinError):
            later.check(record)

    def test_later_carrier_cannot_change_phase_clock_shape_or_canonical_form(self):
        record, work = self.record(), ReachExecutionWork()
        claims = self.claims(work)
        claims.check(record)
        for selected in ([], [1], [0, 0], [0, 2], [False], (0,), [0, 1, 2, 0]):
            changed = {**record, "source_phase_indices": selected}
            with self.subTest(selected=selected), self.assertRaises(OntoKinError):
                claims.check(changed)
        for field in ("h_authored_seconds", "h_stored_seconds"):
            for value in ({"numerator": "2", "denominator": "4"},
                          {"numerator": "01", "denominator": "2"},
                          {"numerator": "1", "denominator": "0"},
                          {"numerator": True, "denominator": "2"},
                          {**ratio(F(1, 2)), "extra": 0}, ratio(F(1, 3))):
                changed = {**record, field: value}
                with self.subTest(field=field, value=value), self.assertRaises(OntoKinError):
                    claims.check(changed)
        self.assertEqual(claims.check(record), (0,))

    def test_warm_claims_preserve_operand_guard_and_cancellation_identity(self):
        work = ReachExecutionWork()
        width = F(1 << 80, 3)
        claims = _IntervalCertificateClaims((F(0), width), F(0), width, [0], width, width, work)
        record = {"source_phase_indices": [0], "h_authored_seconds": ratio(width), "h_stored_seconds": ratio(width)}
        claims.check(record)
        work.max_operand_bits = 64
        with self.assertRaises(ReachAdmissionError):
            claims.check(record)
        work.max_operand_bits = 32768
        marker = RuntimeError("cancel repeated interval claim")
        with patch.object(work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as caught:
                claims.check(record)
        self.assertIs(caught.exception, marker)
        self.assertIs(work.callback_error, marker)


if __name__ == "__main__":
    unittest.main()
