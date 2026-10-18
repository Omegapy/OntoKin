"""Run frozen geometry inputs through the kernel, not just oracle formulas.

The source compiler, agent operations and GLB/0.3 release gates are still open.
Float32 checks here encode components only; they are not destination evidence.
"""

import collections
import json
import math
from pathlib import Path
import struct
import unittest
from dataclasses import replace

from prototypes.surface_v01.mesh import (
    LoftSection, SurfaceError, SurfaceMaterial, triangulate_loft,
)

FIXTURES = Path(__file__).resolve().parents[1] / "docs/language-design/surface-v0.1"


def build_sections(spec):
    names = spec.get("region_keys", spec.get("section_regions"))
    columns = [spec["keys"], spec["stations_m"], spec["centers_xy_m"],
               spec["radii_xy_m"], names]
    if any(len(column) != len(columns[0]) for column in columns):
        raise ValueError("Fixture section columns must have matching lengths")
    return tuple(LoftSection(key, station, (center[0], center[1], 0), rxry[0], rxry[1], name)
                 for key, station, center, rxry, name in zip(*columns))


def default_palette(rings):
    return tuple(SurfaceMaterial(name, (.1, .4, .8, 1), .2, .4)
                 for name in sorted({ring.region for ring in rings}))


def triangle_vertices(mesh):
    for group in mesh.regions:
        for i in range(0, len(group.indices), 3):
            yield tuple(mesh.positions[j] for j in group.indices[i:i+3])


def signed_volume(mesh):
    terms = []
    for a, b, c in triangle_vertices(mesh):
        terms.append((a[0]*(b[1]*c[2]-b[2]*c[1])
                      + a[1]*(b[2]*c[0]-b[0]*c[2])
                      + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6)
    return math.fsum(terms)


class SurfaceManifestExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((FIXTURES / "acceptance.json").read_text("utf-8"))
        cls.cases = {case["id"]:case for case in cls.manifest["cases"]}
        cls.tolerances = cls.manifest["tolerance"]

    def cylinder(self):
        spec = self.cases["M01"]["inputs"][0]
        rings = build_sections(spec)
        return triangulate_loft(rings, default_palette(rings), spec["facets"], spec["caps"])

    def verify_mesh(self, mesh, expected, closed=True):
        self.assertEqual(mesh.triangle_count, expected["triangles"])
        self.assertEqual(len(mesh.positions), expected["vertices"])
        self.assertEqual(len(mesh.normals), len(mesh.positions))
        self.assertEqual(sorted(i for g in mesh.regions for i in g.indices),
                         list(range(len(mesh.positions))))
        self.assertTrue(all(math.isfinite(x) for p in mesh.positions for x in p))
        for normal in mesh.normals:
            self.assertLessEqual(abs(math.hypot(*normal)-1), self.tolerances["normal_unit_length"])
        # Flat corners are not index-welded. Match positions to verify closure.
        directions = collections.Counter()
        for a, b, c in triangle_vertices(mesh):
            u, v = tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3))
            cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
            self.assertGreater(math.hypot(*cross), 0)
            directions.update(((a,b), (b,c), (c,a)))
        if closed:
            for (a,b), count in directions.items():
                self.assertEqual(count, 1)
                self.assertEqual(directions[(b,a)], 1)
            self.assertGreater(signed_volume(mesh), 0)
        else:
            self.assertTrue(any(directions[(b,a)] == 0 for a,b in directions))
        for label in ("ordered_keys", "numeric_station_order"):
            if label in expected:
                self.assertEqual(list(mesh.section_keys), expected[label])
        if "bounds_m" in expected:
            actual = [[min(p[i] for p in mesh.positions) for i in range(3)],
                      [max(p[i] for p in mesh.positions) for i in range(3)]]
            for side in range(2):
                for axis in range(3):
                    self.assertAlmostEqual(actual[side][axis], expected["bounds_m"][side][axis],
                                           delta=self.tolerances["ring_coordinate_m"])
        if "volume_m3" in expected:
            self.assertAlmostEqual(signed_volume(mesh), expected["volume_m3"],
                                   delta=self.tolerances["volume_m3"])

    def test_m01_frozen_analytic_inputs_generate_expected_geometry(self):
        for spec in self.cases["M01"]["inputs"]:
            with self.subTest(name=spec["name"]):
                rings = tuple(reversed(build_sections(spec)))
                actual = triangulate_loft(rings, default_palette(rings), spec["facets"], spec["caps"])
                self.verify_mesh(actual, spec["expected"])

    def test_m02_frozen_offset_taper_has_closed_edges_and_regional_caps(self):
        case = self.cases["M02"]
        rings = build_sections(case["input"])
        actual = triangulate_loft(tuple(reversed(rings)), default_palette(rings),
                                  case["input"]["facets"], case["input"]["caps"])
        self.verify_mesh(actual, case["expected"])
        self.assertEqual({g.key:len(g.indices)//3 for g in actual.regions},
                         case["expected"]["triangles_per_region"])
        low, high = min(r.station_m for r in rings), max(r.station_m for r in rings)
        for group in actual.regions:
            for i in range(0, len(group.indices), 3):
                indices = group.indices[i:i+3]
                stations = {actual.positions[j][2] for j in indices}
                if stations == {low} or stations == {high}:
                    target = "lower_cap_normal" if stations == {low} else "upper_cap_normal"
                    for j in indices:
                        self.assertEqual(list(actual.normals[j]), case["expected"][target])

    def test_m03_measures_actual_polygon_sagitta_and_float32_components(self):
        mesh = self.cylinder()
        checks = self.cases["M03"]["checks"]
        radius = self.cases["M01"]["inputs"][0]["radii_xy_m"][0][0]
        a, b = mesh.positions[:2]
        midpoint = ((a[0]+b[0])/2, (a[1]+b[1])/2)
        actual_sagitta = radius - math.hypot(*midpoint)
        self.assertAlmostEqual(actual_sagitta, checks["sagitta_m"], delta=1e-12)
        self.assertLessEqual(actual_sagitta, checks["sagitta_max_m"])
        max_error = max(abs(struct.unpack("<f", struct.pack("<f", x))[0]-x)
                        for p in mesh.positions for x in p)
        self.assertLessEqual(max_error, checks["float32_local_axis_error_max_m"])

    def test_m04_actual_palette_factors_and_indices_follow_frozen_regions(self):
        case = self.cases["M04"]
        data = case["input"]
        # This fixture specifies materials/counts, not a full geometric recipe.
        rings = tuple(LoftSection(f"s{i}", z, (0,0,0), .5, .5, region)
                      for i, (z,region) in enumerate(zip(data["stations_m"], data["section_regions"])))
        palette = tuple(SurfaceMaterial(key, tuple(v["rgba"]), v["metallic"], v["roughness"])
                        for key,v in data["materials"].items())
        before = triangulate_loft(rings, palette, data["facets"], data["caps"])
        self.assertEqual({g.key:len(g.indices)//3 for g in before.regions},
                         case["expected"]["per_region_triangles"])
        for group in before.regions:
            expected = data["materials"][group.key]
            self.assertEqual(list(group.material.rgba), expected["rgba"])
            self.assertEqual(group.material.metallic, expected["metallic"])
            self.assertEqual(group.material.roughness, expected["roughness"])
        edited = tuple(replace(m, rgba=(1,0,0,1)) if m.key == "middle" else m for m in palette)
        after = triangulate_loft(rings, edited, data["facets"], data["caps"])
        self.assertEqual(before.positions, after.positions)
        self.assertEqual(before.normals, after.normals)
        for left,right in zip(before.regions, after.regions):
            self.assertEqual(left.indices, right.indices)
            if left.key != "middle":
                self.assertEqual(left.material, right.material)
            else:
                self.assertNotEqual(left.material, right.material)

    def test_m06_executes_all_declared_proportions_not_only_minimum_radii(self):
        for spec in self.cases["M06"]["variants"]:
            with self.subTest(spec=spec):
                # Stations were not prescribed in this count/proportion fixture.
                rings = tuple(LoftSection(f"s{i}", i*.01, (0,0,0), spec["rx_m"],
                                          spec["ry_m"], "plain") for i in range(spec["sections"]))
                actual = triangulate_loft(rings, default_palette(rings), spec["facets"], spec["caps"])
                self.verify_mesh(actual, {"triangles":spec["expected_triangles"],
                                          "vertices":spec["expected_vertices"]}, spec["caps"] == "flat")

    def test_m10_tracks_each_frozen_kernel_rejection_without_silent_skips(self):
        rings = build_sections(self.cases["M01"]["inputs"][0])
        palette = default_palette(rings)
        variants = {
            "only one section":{"rings":rings[:1]},
            "65 sections":{"rings":tuple(replace(rings[0], key=f"s{i}", station_m=i*.01) for i in range(65))},
            "duplicate stations 0 and 0":{"rings":(rings[0],replace(rings[1],station_m=0))},
            "station gap 0.000999m":{"rings":(rings[0],replace(rings[1],station_m=.000999))},
            "negative or zero radius":{"rings":(replace(rings[0],radius_x_m=0),rings[1])},
            "radius 100.000001m":{"rings":(replace(rings[0],radius_x_m=100.000001),rings[1])},
            "center Z 1m":{"rings":(replace(rings[0],center_m=(0,0,1)),rings[1])},
            "missing region palette key":{"rings":(replace(rings[0],region="missing"),rings[1])},
            "17 material entries":{"palette":tuple(replace(palette[0],key=f"m{i}") for i in range(17))},
            "metallic 1.1":{"palette":(replace(palette[0],metallic=1.1),)},
            "facets 9":{"facets":9}, "facets 68":{"facets":68},
            "caps rounded":{"caps":"rounded"},
            "251000 requested mesh vertices":{"max_vertices":251000},
        }
        deferred = {"placed in world not carrier frame"}
        self.assertEqual({name for name,code in self.cases["M10"]["negative"]}, set(variants)|deferred)
        for name, code in self.cases["M10"]["negative"]:
            if name in deferred:
                continue  # Explicitly outside this kernel; no native placement exists yet.
            kwargs = dict(variants[name])
            with self.subTest(name=name), self.assertRaises(SurfaceError) as caught:
                triangulate_loft(kwargs.pop("rings",rings), kwargs.pop("palette",palette),
                                 kwargs.pop("facets",16), kwargs.pop("caps","flat"), **kwargs)
            self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main()
