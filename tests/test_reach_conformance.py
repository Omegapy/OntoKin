"""Independent reader arithmetic and hostile-claim checks, before full GLBs.

These focused probes do not substitute for the adopted actual-byte hostile
artifacts, source/native/browser roles, or complete release acceptance.
"""
from fractions import Fraction as F
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ontokin.diagnostics import OntoKinError
from ontokin.reach_conformance import (
    _Bounds, _integer, _assert_projection, check_complete_inequalities, clock_cell_contains,
    rational_clock, verify_retained_clocks, _vertex_extrema, _CertificateBatch, _stored_arc,
    _aligned_reference, _Cell,
)
from ontokin.reach_numeric import ReachAdmissionError, ReachExecutionWork


def ratio(value):
    value = F(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def algebra_record():
    """Exact binary fractions derived directly from the adopted inequalities."""
    width, arc, shift = F(1, 128), F(1, 256), F(1, 1 << 24)
    endpoint, source = F(1, 1 << 30), F(1, 1 << 40)
    destination_position = F(1, 1 << 35)
    destination_rotation = arc * arc + F(1, 1 << 44)
    difference = endpoint + width * width / 32 + arc * arc / 8
    rotation = 4 * difference + source + destination_rotation + shift
    carrier = endpoint + width * width / 8 + source + destination_position + 2 * shift
    values = {
        "landmark_radius_m": 2, "local_vertex_error_bound_m": F(1, 1 << 30),
        "angular_speed_bound_rad_per_s": 1, "carrier_acceleration_bound_m_per_s2": 1,
        "enclosing_angular_speed_bound_rad_per_s": 1,
        "enclosing_carrier_acceleration_bound_m_per_s2": 1,
        "enclosing_carrier_speed_bound_m_per_s": 2,
        "max_endpoint_time_shift_s": shift, "max_endpoint_position_error_m": endpoint,
        "max_endpoint_unit_quaternion_error": endpoint, "stored_quaternion_arc_upper_rad": arc,
        "source_numeric_position_bound_m": source, "source_numeric_rotation_bound_rad": source,
        "destination_numeric_position_bound_m": destination_position,
        "destination_numeric_rotation_bound_rad": destination_rotation,
        "unit_quaternion_difference_bound": difference,
        "ideal_rotation_bound_rad": width * width / 4,
        "ideal_position_bound_m": width * width / 8,
        "total_rotation_bound_rad": rotation, "carrier_position_bound_m": carrier,
        "total_position_bound_m": carrier + 2 * rotation + F(1, 1 << 30),
    }
    result = {name: float(value) for name, value in values.items()}
    assert all(F(result[name]) == value for name, value in values.items())
    return {"h_authored_seconds": ratio(width), "h_stored_seconds": ratio(width), **result}


class ReachIndependentClockTests(unittest.TestCase):
    def test_direct_rounding_is_decided_by_exact_cells(self):
        source = 1 + F(1, 1 << 24) + F(1, 1 << 80)
        self.assertTrue(clock_cell_contains(source, 0x3f800001))
        self.assertFalse(clock_cell_contains(source, 0x3f800000))
        self.assertTrue(clock_cell_contains(F(1, 1 << 150), 0))
        self.assertFalse(clock_cell_contains(F(1, 1 << 150), 1))
        self.assertTrue(clock_cell_contains(F(3, 1 << 150), 2))
        self.assertFalse(clock_cell_contains(F(3, 1 << 150), 1))
        self.assertFalse(clock_cell_contains(0, 0x80000000))

    def test_overflow_midpoint_belongs_to_infinity(self):
        maximum = F((1 << 24) - 1) * (1 << 104)
        midpoint = maximum + (1 << 103)
        self.assertTrue(clock_cell_contains(midpoint - 1, 0x7f7fffff))
        self.assertFalse(clock_cell_contains(midpoint, 0x7f7fffff))
        self.assertFalse(clock_cell_contains(midpoint, 0x7f800000))

    def test_canonical_clock_records_reject_ambiguous_or_unreduced_values(self):
        for bad in ({"numerator": "01", "denominator": "2"},
                    {"numerator": "-0", "denominator": "1"},
                    {"numerator": "1", "denominator": "0"},
                    {"numerator": "2", "denominator": "4"},
                    {"numerator": "0", "denominator": "2"},
                    {"numerator": "1", "denominator": "1", "approximate": 1}):
            with self.subTest(value=bad), self.assertRaises(OntoKinError):
                rational_clock(bad)
        self.assertEqual(rational_clock(ratio(F(7, 31))), F(7, 31))
        with self.assertRaises(OntoKinError):
            _integer("9" * 9866)

    def test_consistent_double_rounding_labels_cannot_disguise_wrong_accessor(self):
        source = 1 + F(1, 1 << 24) + F(1, 1 << 80)
        authored = [ratio(0), ratio(source), ratio(2)]
        clocks = [0., 1., 2.]
        decoded = SimpleNamespace(document={"animations": [{"samplers": [{"input": 0}]}]},
                                  clock=lambda index: clocks)
        retained = [{"authored_seconds": time, "stored_seconds": stored,
                     "stored_binary32_bits": bits, "semantic_boundary": semantic}
                    for time, stored, bits, semantic in zip(authored, clocks,
                        ("00000000", "3f800000", "40000000"), (True, False, True))]
        with self.assertRaises(OntoKinError) as failed:
            verify_retained_clocks(decoded, {"retained_keys": retained}, authored,
                (F(0), F(2)), F(2), time_tolerance=1e-6, work=ReachExecutionWork())
        self.assertEqual(failed.exception.diagnostic.details["export_code"], "OKE-E-CLOCK-ROUNDING")


class ReachIndependentBoundTests(unittest.TestCase):
    def test_reference_sign_choice_preserves_antipodes_and_ambiguous_upper_bounds(self):
        arithmetic = _Bounds(ReachExecutionWork())
        for raw in ((0., 0., .6, .8), (.5, -.5, .5, -.5)):
            expected = arithmetic.normalize(raw)
            for sign in (-1, 1):
                actual = tuple(sign * value for value in raw)
                aligned = _aligned_reference(actual, expected, arithmetic)
                self.assertEqual(aligned, expected if sign == 1 else tuple(_Cell(-v.hi, -v.lo) for v in expected))
        uncertain = (_Cell(F(-1), F(1)),) * 4
        self.assertIs(_aligned_reference((1., 0., 0., 0.), uncertain, arithmetic), uncertain)
        # A wide/ambiguous source interval is still measured; choosing a sign
        # cannot silently convert it into zero rotational error.
        self.assertGreater(arithmetic.difference(arithmetic.normalize((1., 0., 0., 0.)), uncertain), F(1))

    def test_certificate_batch_checks_later_member_minima_and_changed_payloads(self):
        record, width = algebra_record(), F(1, 128)
        for name in ("landmark_radius_m", "max_endpoint_time_shift_s", "max_endpoint_position_error_m",
                     "max_endpoint_unit_quaternion_error", "stored_quaternion_arc_upper_rad",
                     "source_numeric_position_bound_m", "source_numeric_rotation_bound_rad"):
            with self.subTest(minimum=name):
                batch = _CertificateBatch(_Bounds(ReachExecutionWork()), .001, .001)
                batch.add(record, width, width, {name: F(record[name])}, F(0))
                batch.add(dict(record), width, width, {name: F(record[name]) + F(1, 1 << 100)}, F(0))
                with self.assertRaises(OntoKinError):
                    batch.flush()
        for name in ("unit_quaternion_difference_bound", "ideal_rotation_bound_rad", "ideal_position_bound_m",
                     "total_rotation_bound_rad", "carrier_position_bound_m", "total_position_bound_m"):
            with self.subTest(quantity=name):
                batch = _CertificateBatch(_Bounds(ReachExecutionWork()), .001, .001)
                batch.add(record, width, width, {}, F(0))
                batch.add({**record, name: math.nextafter(record[name], 0.)}, width, width, {}, F(0))
                with self.assertRaises(OntoKinError):
                    batch.flush()

    def test_certificate_batch_checks_maximum_widths_and_destination_magnitude(self):
        record, width = algebra_record(), F(1, 128)
        for authored, stored, magnitude in ((F(1), width, F(0)), (width, F(1), F(0)),
                                            (width, width, F(1 << 401))):
            with self.subTest(authored=authored, stored=stored, magnitude=magnitude):
                batch = _CertificateBatch(_Bounds(ReachExecutionWork()), .001, .001)
                batch.add(record, width, width, {}, F(0))
                batch.add(record, authored, stored, {}, magnitude)
                with self.assertRaises(OntoKinError):
                    batch.flush()

    def test_certificate_batch_is_bounded_and_keeps_complete_results(self):
        record, width = algebra_record(), F(1, 128)
        work = ReachExecutionWork()
        batch = _CertificateBatch(_Bounds(work), .001, .001)
        for index in range(70):
            item = {**record, "max_endpoint_time_shift_s": record["max_endpoint_time_shift_s"] * index / 70}
            batch.add(item, width, width, {}, F(0))
            self.assertLessEqual(len(batch.groups), 64)
        batch.flush()
        self.assertEqual(batch.max_position, F(record["total_position_bound_m"]))
        self.assertEqual(batch.max_rotation, F(record["total_rotation_bound_rad"]))
        self.assertEqual(work.counts["independent_certificate_member"], 70)
        self.assertEqual(work.counts["independent_certificate_group_check"], 70)
        for invalid in (True, float("nan"), float("inf"), -1.):
            with self.subTest(invalid=invalid), self.assertRaises(OntoKinError):
                batch.add({**record, "landmark_radius_m": invalid}, width, width, {}, F(0))

    def test_stored_arc_cache_cannot_hide_changed_endpoint_sign(self):
        arithmetic = _Bounds(ReachExecutionWork())
        first, last = (0., 0., 0., 1.), (0., 0., 0., -1.)
        normalized = arithmetic.normalize(first)
        _stored_arc(first, first, normalized, normalized, arithmetic)
        with self.assertRaises(OntoKinError):
            _stored_arc(first, last, normalized, arithmetic.normalize(last), arithmetic)

    def test_geometry_extrema_preserve_exact_radius_and_conversion_errors(self):
        from ontokin.geometry import sphere_mesh, box_mesh
        from ontokin.scene import float32
        tiny = math.ldexp(1., -150)
        seam = math.ldexp(1., -126)
        points = [
            (0., -0., tiny), (-tiny, 3 * tiny, -3 * tiny),
            (math.nextafter(tiny, 0.), math.nextafter(tiny, math.inf), -tiny),
            (seam, math.nextafter(seam, 0.), math.nextafter(seam, math.inf)),
            (1. + 2. ** -24, -1. - 2. ** -24, math.nextafter(1. + 2. ** -24, math.inf)),
            (1., 2. ** -54, 2. ** -54), (1., 2. ** -53, 2. ** -54),
            (F(1, 10), F(-1, 7), F(1, 3)),
            *box_mesh((.1, 2., 3.)).positions, *sphere_mesh(.3).positions,
        ]
        stored = [tuple(float32(value) for value in point) for point in points]
        expected_radius = max(sum((abs(F(value)) for value in point), F(0)) for point in points)
        axis_errors = [max(abs(F(point[axis]) - F(actual[axis]))
                           for point, actual in zip(points, stored)) for axis in range(3)]
        work = ReachExecutionWork()
        radius, error = _vertex_extrema(points, stored, work=work)
        self.assertEqual(radius, expected_radius)
        self.assertEqual(error, _Bounds().norm(axis_errors))
        self.assertEqual(work.counts["independent_geometry_point"], len(points))

    def test_geometry_radius_screen_cannot_hide_a_sub_ulp_larger_point(self):
        from ontokin.scene import float32
        points = [(1., 2. ** -54, 2. ** -54), (1., 2. ** -53, 2. ** -54)]
        stored = [tuple(float32(value) for value in point) for point in points]
        radius, _ = _vertex_extrema(points, stored, work=ReachExecutionWork())
        self.assertEqual(radius, F(1) + F(3, 1 << 54))

    def test_geometry_screen_retains_each_actual_vertex_and_cancellation_check(self):
        points = [(1., 0., 0.)] + [(0., 0., 0.)] * 30
        stored = list(points)
        stored[-1] = (0., 0., .001)
        with self.assertRaises(OntoKinError):
            _vertex_extrema(points, stored, work=ReachExecutionWork())
        checks = 0
        interruption = RuntimeError("original geometry cancellation")
        def check():
            nonlocal checks
            checks += 1
            if checks == 20:
                raise interruption
        with self.assertRaises(RuntimeError) as caught:
            _vertex_extrema(points, points, work=ReachExecutionWork(check=check))
        self.assertIs(caught.exception, interruption)

    def test_immutable_counts_and_boolean_controls_preserve_their_types(self):
        for actual, expected in ((True, 1), (False, 0), (1., 1), (1, True), (0, False), (True, 1.)):
            with self.subTest(actual=actual, expected=expected), self.assertRaises(OntoKinError):
                _assert_projection(actual, expected, arithmetic=_Bounds(ReachExecutionWork()), allowances={})

    def test_every_dependent_bound_is_binding(self):
        record = algebra_record()
        checked = check_complete_inequalities(record, position_tolerance=.001,
                                             rotation_tolerance=.001, work=ReachExecutionWork())
        self.assertEqual(checked["position_bound_m"], F(record["total_position_bound_m"]))
        for name in ("unit_quaternion_difference_bound", "ideal_rotation_bound_rad", "ideal_position_bound_m",
                     "total_rotation_bound_rad", "carrier_position_bound_m", "total_position_bound_m"):
            changed = {**record, name: math.nextafter(record[name], 0.)}
            with self.subTest(quantity=name), self.assertRaises(OntoKinError):
                check_complete_inequalities(changed, position_tolerance=.001,
                                            rotation_tolerance=.001, work=ReachExecutionWork())

    def test_both_authored_and_stored_quarter_plans_are_checked(self):
        for name in ("h_authored_seconds", "h_stored_seconds"):
            changed = {**algebra_record(), name: ratio(1)}
            with self.subTest(clock=name), self.assertRaises(OntoKinError):
                check_complete_inequalities(changed, position_tolerance=.001,
                                            rotation_tolerance=.001, work=ReachExecutionWork())

    def test_lowered_operand_limit_precedes_large_multiplication(self):
        first, last = F(1 << 40), F(1 << 40)
        work = ReachExecutionWork(max_operand_bits=64)
        with patch.object(F, "__mul__", side_effect=AssertionError("allocated a forbidden product")):
            with self.assertRaises(ReachAdmissionError):
                _Bounds(work).mul(first, last)

    def test_post_square_root_cancellation_preserves_original_exception(self):
        interruption, returned = RuntimeError("original cancellation"), False
        def check():
            if returned:
                raise interruption
        original = math.isqrt
        def finish(value):
            nonlocal returned
            answer = original(value)
            returned = True
            return answer
        with patch("ontokin.reach_conformance.math.isqrt", side_effect=finish):
            with self.assertRaises(RuntimeError) as caught:
                _Bounds(ReachExecutionWork(check=check)).root(F(2))
        self.assertIs(caught.exception, interruption)

    def test_quaternion_input_is_bounded_before_materialization(self):
        visited = []
        def components():
            for index in range(100):
                visited.append(index)
                if index > 4:
                    self.fail("reader consumed beyond the first invalid component")
                yield 1
        with self.assertRaises(OntoKinError):
            _Bounds(ReachExecutionWork()).normalize(components())
        self.assertEqual(visited, [0, 1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
