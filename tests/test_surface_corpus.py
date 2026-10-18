"""Check that prospective source fixtures and frozen analytical oracles agree.

These checks audit contract inputs. They are not a substitute for compiling
surface-0.1 source or independently validating its future GLB/0.3 output.
"""

import hashlib
import json
import math
from pathlib import Path
import re
import unittest

FIXTURES=Path(__file__).resolve().parents[1]/"docs"/"language-design"/"surface-v0.1"


class SurfaceCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((FIXTURES/"acceptance.json").read_text("utf-8"))

    def test_adopted_cases_are_unique_and_prospective(self):
        cases=self.manifest["cases"]
        self.assertEqual([c["id"] for c in cases],[f"M{i:02}" for i in range(1,13)])
        self.assertEqual(self.manifest["status"],"adopted-unexecuted")
        self.assertEqual(self.manifest["schema"],"ontokin.acceptance/surface-0.1")
        self.assertEqual(len(set(c["id"] for c in cases)),12)

    def test_pinned_import_digest_matches_exact_library_bytes(self):
        dep=(FIXTURES/self.manifest["source_bundle"]["library"]).read_bytes()
        actual=hashlib.sha256(dep).hexdigest()
        self.assertEqual(actual,self.manifest["source_bundle"]["sha256"])
        entry=(FIXTURES/self.manifest["source_bundle"]["entry"]).read_text("utf-8")
        self.assertIn('digest "sha256:'+actual+'";',entry)
        self.assertIn('profile "surface-0.1";',entry)
        self.assertIn('ontokin "0.3";',entry)
        self.assertIn("loft(self.rings, self.palette",dep.decode("utf-8"))
        self.assertTrue(re.search(r'object\s+second',entry))

    def test_predeclared_m01_oracle_is_independent_geometry_formula(self):
        cylinder=self.manifest["cases"][0]["inputs"][0]
        facets=cylinder["facets"]
        radius=cylinder["radii_xy_m"][0][0]
        height=cylinder["stations_m"][1]-cylinder["stations_m"][0]
        expected=cylinder["expected"]
        self.assertEqual(expected["triangles"],2*len(cylinder["stations_m"])*facets)
        self.assertEqual(expected["vertices"],3*expected["triangles"])
        geometric_volume=facets*radius**2*math.sin(2*math.pi/facets)*height/2
        self.assertAlmostEqual(geometric_volume,expected["volume_m3"],delta=1e-9)
        self.assertAlmostEqual(math.pi*radius**2*height,
                               expected["ideal_circle_volume_m3"],delta=1e-9)
        self.assertAlmostEqual(radius*(1-math.cos(math.pi/facets)),
                               expected["radial_sagitta_m"],delta=1e-12)
        self.assertLess(geometric_volume,expected["ideal_circle_volume_m3"])

    def test_m06_holdouts_and_negative_codes_are_frozen(self):
        cases={case["id"]:case for case in self.manifest["cases"]}
        for v in cases["M06"]["variants"]:
            n=v["sections"]
            facets=v["facets"]
            tris=2*(n-1)*facets+(2*facets if v["caps"]=="flat" else 0)
            self.assertEqual(v["expected_triangles"],tris)
            self.assertEqual(v["expected_vertices"],3*tris)
        negatives=cases["M10"]["negative"]
        self.assertGreaterEqual(len(negatives),12)
        self.assertTrue(all(item[1].startswith("OKL-E-") for item in negatives))
        self.assertEqual(self.manifest["limits"]["max_aggregate_vertices"],250000)


if __name__=="__main__":
    unittest.main()
