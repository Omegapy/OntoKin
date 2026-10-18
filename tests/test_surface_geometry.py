"""Independent analytic and rejection tests for the prospective surface-0.1 mesh.

These directly test the geometry kernel. They do not claim the language parser,
agent service, exported GLB or browser already implement surface-0.1.
"""

import math
import unittest
from dataclasses import replace

from prototypes.surface_v01.mesh import (
    LoftSection, SurfaceMaterial, SurfaceError, triangulate_loft,
)


def s(key="base", z=0.0, rx=0.5, ry=0.5, region="blue", cx=0.0, cy=0.0):
    return LoftSection(key, z, (cx, cy, 0.0), rx, ry, region)


def m(key="blue", rgba=(0.1, 0.4, 0.8, 1.0), metallic=0.2, roughness=0.4):
    return SurfaceMaterial(key, rgba, metallic, roughness)


def cylinder():
    return triangulate_loft((s("z-base"), s("a-top", 2)), (m(),), 16, "flat")


def signed_triangle_volume(mesh):
    total = 0.0
    for region in mesh.regions:
        for i in range(0, len(region.indices), 3):
            ia, ib, ic = region.indices[i:i+3]
            a, b, c = (mesh.positions[j] for j in (ia, ib, ic))
            total += (
                a[0] * (b[1]*c[2] - b[2]*c[1])
                + a[1] * (b[2]*c[0] - b[0]*c[2])
                + a[2] * (b[0]*c[1] - b[1]*c[0])
            ) / 6.0
    return total


class SurfaceKernelTests(unittest.TestCase):
    def assertError(self, code, sections=None, materials=None, facets=16, caps="flat",
                    **kwargs):
        if sections is None:
            sections = (s(), s("top", 1))
        if materials is None:
            materials = (m(),)
        with self.assertRaises(SurfaceError) as caught:
            triangulate_loft(sections, materials, facets, caps, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_m01_circular_prism_independent_volume_bounds_and_normals(self):
        mesh = cylinder()
        self.assertEqual(mesh.section_keys, ("z-base", "a-top"))
        self.assertEqual(mesh.triangle_count, 64)
        self.assertEqual(len(mesh.positions), 192)
        self.assertEqual(len(mesh.normals), 192)
        self.assertEqual(min(p[0] for p in mesh.positions), -0.5)
        self.assertEqual(max(p[0] for p in mesh.positions), 0.5)
        self.assertEqual(min(p[1] for p in mesh.positions), -0.5)
        self.assertEqual(max(p[1] for p in mesh.positions), 0.5)
        self.assertEqual(min(p[2] for p in mesh.positions), 0)
        self.assertEqual(max(p[2] for p in mesh.positions), 2)
        oracle = 16 * 0.5**2 * math.sin(2 * math.pi / 16) * 2 / 2
        self.assertAlmostEqual(signed_triangle_volume(mesh), oracle, delta=1e-9)
        self.assertAlmostEqual(oracle, 1.5307337294603591, delta=1e-9)
        for normal in mesh.normals:
            self.assertAlmostEqual(math.sqrt(sum(v*v for v in normal)), 1, delta=1e-12)
        # At theta 0 the first side face points outward toward +X.
        self.assertGreater(mesh.normals[0][0], 0)

    def test_m01_elliptic_dimensions(self):
        mesh = triangulate_loft((s(rx=0.4, ry=0.2), s("top", 1, 0.4, 0.2)),
                                (m(),), 16, "flat")
        self.assertEqual(mesh.triangle_count, 64)
        self.assertAlmostEqual(min(p[0] for p in mesh.positions), -0.4)
        self.assertAlmostEqual(max(p[1] for p in mesh.positions), 0.2)
        self.assertAlmostEqual(max(p[2] for p in mesh.positions), 1)

    def test_m02_station_not_key_order_taper_and_regions(self):
        sections = (s("b-end", 2, 0.1, 0.1, "tip", 0.4, 0.15),
                    s("z-start", 0, 0.5, 0.3, "base"),
                    s("a-middle", 0.8, 0.4, 0.2, "middle", 0.25, 0.1))
        materials = (m("tip"), m("base"), m("middle"))
        mesh = triangulate_loft(sections, materials, 16, "flat")
        self.assertEqual(mesh.section_keys, ("z-start", "a-middle", "b-end"))
        self.assertEqual(mesh.triangle_count, 96)
        self.assertEqual(len(mesh.positions), 288)
        self.assertEqual({g.key: len(g.indices)//3 for g in mesh.regions},
                         {"base": 48, "middle": 32, "tip": 16})
        self.assertTrue(all(math.isfinite(x) for v in mesh.positions for x in v))
        self.assertTrue(all(math.isfinite(x) for v in mesh.normals for x in v))
        self.assertEqual(mesh.normals[-1], (0.0, 0.0, 1.0))

    def test_m03_angular_sagitta_is_analytically_bounded(self):
        radius, facets = 0.5, 16
        sagitta = radius * (1 - math.cos(math.pi / facets))
        self.assertAlmostEqual(sagitta, 0.009607359798384785, delta=1e-12)
        self.assertLess(sagitta, 0.01)
        mesh = cylinder()
        self.assertAlmostEqual(mesh.positions[0][0], radius, delta=1e-10)
        self.assertAlmostEqual(mesh.positions[1][0], radius * math.cos(2*math.pi/16),
                               delta=1e-10)

    def test_m04_palette_regions_have_real_triangle_indices(self):
        sections = (s("base", 0, region="base"), s("mid", 1, region="middle"),
                    s("end", 2, region="top"))
        palette = (m("base"), m("middle"), m("top"))
        first = triangulate_loft(sections, palette, 16, "flat")
        self.assertEqual({g.key: len(g.indices)//3 for g in first.regions},
                         {"base": 48, "middle": 32, "top": 16})
        self.assertEqual([g.key for g in first.regions], ["base", "middle", "top"])
        all_indices = sorted(index for g in first.regions for index in g.indices)
        self.assertEqual(all_indices, list(range(len(first.positions))))
        replacement = replace(palette[1], rgba=(1.0, 0.0, 0.0, 1.0))
        second = triangulate_loft(sections, (palette[0], replacement, palette[2]), 16, "flat")
        self.assertEqual(first.positions, second.positions)
        self.assertEqual(first.normals, second.normals)
        self.assertEqual([g.indices for g in first.regions],
                         [g.indices for g in second.regions])
        self.assertEqual(second.regions[1].material.rgba, (1.0, 0.0, 0.0, 1.0))
        self.assertEqual(second.regions[0].material, first.regions[0].material)

    def test_m06_held_out_counts_and_boundary_values(self):
        for n, segments, caps, expected in ((2,8,"flat",32), (3,12,"none",48),
                                            (11,32,"flat",704), (64,64,"flat",8192)):
            sections = tuple(s(f"k{i}", i*0.01, 0.001, 0.001) for i in range(n))
            mesh = triangulate_loft(sections, (m(),), segments, caps)
            self.assertEqual(mesh.triangle_count, expected)
            self.assertEqual(len(mesh.positions), 3*expected)
        tiny = triangulate_loft((s(rx=0.001, ry=0.001),
                                 s("top", 0.001, 0.001, 0.001)), (m(),), 8, "flat")
        self.assertEqual(tiny.triangle_count, 32)

    def test_m07_repair_only_new_geometry_and_immutable_inputs(self):
        sections = (s("base"), s("middle", 1, 0.48, 0.38), s("top", 2))
        first = triangulate_loft(sections, (m(),), 16, "flat")
        amended = (sections[0], replace(sections[1], radius_x_m=0.52), sections[2])
        second = triangulate_loft(amended, (m(),), 16, "flat")
        self.assertEqual(first.section_keys, second.section_keys)
        self.assertNotEqual(first.positions, second.positions)
        self.assertEqual(sections[1].radius_x_m, 0.48)
        self.assertEqual(first.regions[0].material, second.regions[0].material)

    def test_m08_source_order_permutation_keeps_numeric_mesh(self):
        sections = (s("tip", 2), s("base", 0), s("middle", 1))
        forward = triangulate_loft(sections, (m(),), 16, "flat")
        backward = triangulate_loft(tuple(reversed(sections)), (m(),), 16, "flat")
        self.assertEqual(forward, backward)
        self.assertEqual(forward.section_keys, ("base", "middle", "tip"))
        insertion = triangulate_loft(sections + (s("new", 0.5),), (m(),), 16, "flat")
        self.assertEqual(insertion.section_keys, ("base", "new", "middle", "tip"))
        self.assertEqual(insertion.triangle_count - forward.triangle_count, 32)

    def test_m10_station_radius_center_and_missing_region_rejections(self):
        self.assertError("OKL-E-SURFACE-STATION", (s(), s("other", 0)))
        self.assertError("OKL-E-SURFACE-STATION", (s(), s("other", 0.000999)))
        self.assertError("OKL-E-SURFACE-RADIUS", (s(rx=0), s("top", 1)))
        self.assertError("OKL-E-SURFACE-RADIUS", (s(ry=100.000001), s("top", 1)))
        self.assertError("OKL-E-SURFACE-CENTER",
                         (replace(s(), center_m=(0,0,1)), s("top", 1)))
        self.assertError("OKL-E-SURFACE-REGION",
                         (s(region="missing"), s("top", 1)))
        self.assertError("OKL-E-SURFACE-STATION", (s(z=math.inf), s("top", 1)))
        self.assertError("OKL-E-SURFACE-SECTION", (s(), s("base", 1)))

    def test_m10_resource_facets_materials_and_caps(self):
        self.assertError("OKL-E-SURFACE-SECTION", (s(),))
        self.assertError("OKL-E-SURFACE-SECTION",
                         tuple(s(f"s{i}", i*0.01) for i in range(65)))
        self.assertError("OKL-E-SURFACE-FACETS", facets=9)
        self.assertError("OKL-E-SURFACE-FACETS", facets=68)
        self.assertError("OKL-E-SURFACE-FACETS", facets=True)
        self.assertError("OKL-E-SURFACE-CAPS", caps="rounded")
        self.assertError("OKL-E-SURFACE-MATERIAL",
                         materials=tuple(m(f"material{i}") for i in range(17)))
        self.assertError("OKL-E-SURFACE-MATERIAL", materials=(m(metallic=1.1),))
        self.assertError("OKL-E-SURFACE-MATERIAL",
                         materials=(m(rgba=(0,0,math.nan,1)),))
        self.assertError("OKL-E-RESOURCE", max_vertices=191)

    def test_m10_cancel_is_propagated_without_partial_result(self):
        class Cancelled(Exception):
            pass
        visits = 0
        def cancel():
            nonlocal visits
            visits += 1
            if visits > 20:
                raise Cancelled()
        with self.assertRaises(Cancelled):
            triangulate_loft((s(), s("top", 1)), (m(),), 16, "flat", check=cancel)
        self.assertGreater(visits, 20)


if __name__ == "__main__":
    unittest.main()
