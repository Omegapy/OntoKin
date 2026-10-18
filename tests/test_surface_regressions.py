"""Regression checks for OK-LANG-003-C1, not an end-to-end language gate."""

import math
import unittest
from dataclasses import replace
from fractions import Fraction

from prototypes.surface_v01.mesh import (
    LoftSection, SurfaceError, SurfaceMaterial, triangulate_loft,
)


def sections(low=0.0, high=1.0):
    return (LoftSection("base", low, (0, 0, 0), .5, .5, "blue"),
            LoftSection("top", high, (0, 0, 0), .5, .5, "blue"))


def materials():
    return (SurfaceMaterial("blue", (.1, .4, .8, 1), .2, .4),)


class SurfaceSnapshotAndBoundaryTests(unittest.TestCase):
    def rejected(self, code, rings=None, palette=None, **kwargs):
        with self.assertRaises(SurfaceError) as caught:
            triangulate_loft(sections() if rings is None else rings,
                             materials() if palette is None else palette,
                             16, "flat", **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_returned_material_does_not_alias_mutable_color(self):
        color = [.1, .4, .8, 1]
        palette = [SurfaceMaterial("blue", color, .2, .4)]
        result = triangulate_loft(sections(), palette, 16, "flat")
        color[0] = 1
        palette.clear()
        self.assertEqual(result.regions[0].material.rgba, (.1, .4, .8, 1.0))
        self.assertIsInstance(result.regions[0].material.rgba, tuple)
        self.assertTrue(all(type(x) is float for x in result.regions[0].material.rgba))

    def test_callbacks_cannot_mutate_validated_section_or_palette(self):
        center, color = [0, 0, 0], [.1, .4, .8, 1]
        rings = [replace(sections()[0], center_m=center), sections()[1]]
        palette = [SurfaceMaterial("blue", color, .2, .4)]
        reference = triangulate_loft(rings, palette, 16, "flat")
        def mutate():
            center[0] = 200.0
            color[0] = 1.0
        actual = triangulate_loft(rings, palette, 16, "flat", check=mutate)
        self.assertEqual(actual, reference)

    def test_numeric_gap_rejects_values_outside_representation_allowance(self):
        for a, b in ((0, .001 - 5e-13), (0, math.nextafter(.001, 0)),
                     (1, math.nextafter(1.001, 0))):
            with self.subTest(a=a, b=b):
                error = self.rejected("OKL-E-SURFACE-STATION", sections(a, b))
                self.assertIn("representation_allowance_m", error.details)

    def test_numeric_gap_accepts_declared_quantized_boundary(self):
        for a, b in ((0, .001), (1, 1.001), (-100, -99.999), (99.999, 100)):
            with self.subTest(a=a, b=b):
                result = triangulate_loft(sections(a, b), materials(), 16, "flat")
                self.assertEqual(result.triangle_count, 64)

    def test_gap_decisions_match_independent_rational_oracle(self):
        # Decimal inputs are converted to canonical floats before this boundary.
        for a in (-100.0, -1.0, 0.0, 1.0, 99.999):
            middle = a + .001
            values = [middle]
            for direction in (-math.inf, math.inf):
                b = middle
                for _ in range(3):
                    b = math.nextafter(b, direction)
                    values.append(b)
            for b in values:
                if abs(b) > 100:
                    continue
                difference = Fraction.from_float(b) - Fraction.from_float(a)
                allowance = (Fraction.from_float(math.ulp(a))
                             + Fraction.from_float(math.ulp(b))) / 2
                expected = b > a and difference + allowance >= Fraction(1, 1000)
                with self.subTest(a=a, b=b, expected=expected):
                    try:
                        triangulate_loft(sections(a, b), materials(), 16, "flat")
                        actual = True
                    except SurfaceError as error:
                        self.assertEqual(error.code, "OKL-E-SURFACE-STATION")
                        actual = False
                    self.assertEqual(actual, expected)

    def test_equal_stations_and_signed_zero_remain_invalid(self):
        for a, b in ((0., -0.), (-0., 0.), (1., 1.)):
            self.rejected("OKL-E-SURFACE-STATION", sections(a, b))

    def test_bad_key_diagnostic_does_not_call_unknown_object(self):
        class UntrustedKey:
            def __str__(self):
                raise AssertionError("Validation must not call this conversion")
        self.rejected("OKL-E-SURFACE-SECTION",
                      (replace(sections()[0], key=UntrustedKey()), sections()[1]))

    def test_nonfinite_and_non_numeric_inputs_have_typed_errors(self):
        for value in (math.nan, math.inf, -math.inf, True, "1", 10**1000):
            with self.subTest(value_type=type(value).__name__):
                self.rejected("OKL-E-SURFACE-RADIUS",
                              (replace(sections()[0], radius_x_m=value), sections()[1]))
        self.rejected("OKL-E-SURFACE-MATERIAL", palette={})

    def test_actual_minimum_and_maximum_geometry_counts(self):
        for count, facets, radius, expected in ((2, 8, .001, 96), (64, 64, 100, 24576)):
            rings = tuple(LoftSection(f"s{i}", i * .01, (0, 0, 0),
                                      radius, radius, "blue") for i in range(count))
            result = triangulate_loft(rings, materials(), facets, "flat",
                                      max_vertices=expected)
            self.assertEqual(len(result.positions), expected)
            with self.assertRaises(SurfaceError) as caught:
                triangulate_loft(rings, materials(), facets, "flat", max_vertices=expected-1)
            self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")

    def test_remaining_budget_charged_for_repeated_occurrences(self):
        rings = tuple(LoftSection(f"s{i}", i*.01, (0,0,0), .1, .1, "blue")
                      for i in range(64))
        remaining = 250000
        for _ in range(10):
            result = triangulate_loft(rings, materials(), 64, "flat", max_vertices=remaining)
            remaining -= len(result.positions)
        self.assertEqual(remaining, 4240)
        with self.assertRaises(SurfaceError) as caught:
            triangulate_loft(rings, materials(), 64, "flat", max_vertices=remaining)
        self.assertEqual(caught.exception.code, "OKL-E-RESOURCE")
        self.assertEqual(caught.exception.details["required"], 24576)

    def test_unused_palette_has_no_empty_region_and_repeated_region_is_one_group(self):
        rings = tuple(LoftSection(f"s{i}", i, (0,0,0), .5, .5, name)
                      for i, name in enumerate(("blue", "red", "blue", "red")))
        red = SurfaceMaterial("red", (1,0,0,.5), .8, .1)
        unused = SurfaceMaterial("unused", (0,1,0,1), 0, 1)
        result = triangulate_loft(rings, (red, unused, materials()[0]), 16, "flat")
        self.assertEqual([g.key for g in result.regions], ["blue", "red"])
        self.assertEqual({g.key:len(g.indices)//3 for g in result.regions}, {"blue":80,"red":48})
        self.assertEqual(sorted(i for g in result.regions for i in g.indices),
                         list(range(len(result.positions))))

    def test_cancellation_during_finalization_returns_no_mesh(self):
        class Cancelled(Exception):
            pass
        # Count the documented pre-generation, ring and face-loop checkpoints.
        generation_visits = 1 + 2 + 16 + 2*16
        visits = 0
        def cancel():
            nonlocal visits
            visits += 1
            if visits > generation_visits:
                raise Cancelled()
        with self.assertRaises(Cancelled):
            triangulate_loft(sections(), materials(), 16, "flat", check=cancel)
        self.assertEqual(visits, generation_visits + 1)


if __name__ == "__main__":
    unittest.main()
