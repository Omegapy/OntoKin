"""Adversarial arithmetic obligations of the recorded reach contract."""
from fractions import Fraction
import math
import struct
import unittest

from ontokin.diagnostics import OntoKinError
from ontokin.reach_export import (MotionBound, ReachPhase, complete_interval_bounds,
    controlled_destination_sample, destination_numeric_bounds, direct_binary32,
    enclosing_phases, normalized_component, planning_inequalities, quaternion_arc_upper)


class ReachClockTests(unittest.TestCase):
    def test_direct_rounding_preserves_term_lost_by_binary64(self):
        exact = 1 + Fraction(1, 1 << 24) + Fraction(1, 1 << 80)
        result, bits = direct_binary32(exact)
        self.assertEqual(bits, "3f800001")
        double = struct.unpack("<I", struct.pack("<f", float(exact)))[0]
        self.assertEqual(double, 0x3f800000)
        self.assertEqual(result, 1 + 2**-23)

    def test_ties_at_zero_subnormal_boundary_and_overflow(self):
        self.assertEqual(direct_binary32(Fraction(1, 1 << 150))[1], "00000000")
        self.assertEqual(direct_binary32(Fraction(3, 1 << 150))[1], "00000002")
        self.assertEqual(direct_binary32(Fraction((1 << 24) - 1, 1 << 150))[1], "00800000")
        maximum = Fraction((1 << 24) - 1) * (1 << 104)
        self.assertEqual(direct_binary32(maximum + (1 << 103) - 1)[1], "7f7fffff")
        with self.assertRaises(OntoKinError):
            direct_binary32(maximum + (1 << 103))

    def test_nonbinary_semantic_boundaries_keep_fixed_bits(self):
        for clock, bits in ((Fraction(4503599807514481, 9007199254740992), "3f000000"),
                            (Fraction(6755399531127737, 4503599627370496), "3fc00000"),
                            (Fraction(27021597764222977, 9007199254740992), "40400000")):
            self.assertEqual(direct_binary32(clock)[1], bits)

    def test_neighboring_positive_width_phase_is_not_lost(self):
        pause = Fraction(4503599807514481, 9007199254740992)
        still = MotionBound(Fraction(0), Fraction(0), Fraction(0))
        phases = (ReachPhase(Fraction(0), pause, {"arm": still}),
                  ReachPhase(pause, Fraction(3, 2), {"arm": still}))
        self.assertEqual(enclosing_phases(phases, pause, Fraction(1), Fraction(1, 2),
                                         Fraction(1), prefix_end=Fraction(3, 2)), (0, 1))
        self.assertEqual(pause - Fraction(1, 2), Fraction(180143985, 9007199254740992))


class ReachDestinationArithmeticTests(unittest.TestCase):
    def test_normalization_rounds_extreme_finite_ratios(self):
        for component, norm in ((Fraction(3), Fraction(25)), (Fraction(-4), Fraction(25)),
                                (Fraction(1, 1 << 1074), Fraction(1))):
            result = normalized_component(component, norm)
            if norm == 25:
                self.assertEqual(result, float(component / 5))
            else:
                self.assertEqual(result, math.ulp(0.0))

    def test_coherent_lift_and_zero_are_explicit_failures(self):
        with self.assertRaises(OntoKinError):
            quaternion_arc_upper((0, 0, 0, 1), (0, 0, 0, -1))
        with self.assertRaises(OntoKinError):
            quaternion_arc_upper((0, 0, 0, 0), (0, 0, 0, 1))

    def test_exact_translation_and_coincident_rotation(self):
        position, rotation = controlled_destination_sample((0, 1, 2), (3, 4, 5),
            (0, 0, 0, 1), (0, 0, 0, 1), Fraction(1, 3))
        self.assertEqual(position, (1., 2., 3.))
        self.assertEqual(rotation, (0., 0., 0., 1.))

    def test_destination_approximation_is_charged_even_with_exact_endpoints(self):
        position, rotation = destination_numeric_bounds(Fraction(1, 100), 10, 2, 0)
        self.assertGreater(rotation, Fraction(1, 10000))
        self.assertGreater(position, 0)
        bound = MotionBound(Fraction(1), Fraction(1), Fraction(1))
        result = complete_interval_bounds(width=Fraction(1, 100), bound=bound, enclosing=bound,
            radius=2, vertex_error=0, endpoint_position_error=0, endpoint_quaternion_error=0,
            stored_arc=Fraction(1, 100), time_shift=0, source_position_error=0,
            source_rotation_error=0, destination_position_error=position,
            destination_rotation_error=rotation)
        self.assertGreater(result['total_rotation_bound_rad'], rotation)
        self.assertGreater(result['total_position_bound_m'], 2 * result['total_rotation_bound_rad'])
        self.assertTrue(planning_inequalities(Fraction(1, 100), bound, 2, Fraction(1, 1000), Fraction(1, 1000)))


if __name__ == '__main__':
    unittest.main()
