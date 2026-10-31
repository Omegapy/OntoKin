"""Shared .11 routing, carrier authority, and actual binary32 reader checks."""
import hashlib
from pathlib import Path
import unittest

from ontokin.budget_runtime import execute_framed_loft_export, execute_ring_loft_export
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import read_glb
from ontokin.profile_capabilities import FRAMED_LOFT_PROFILE
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions, FRAMED_LOFT_TARGET
from tests import test_ring_loft_integration as inherited_reader


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/framed-polygon-lofts"


def bundle(raw, *, modules=()):
    return ProgramBundle(SourceUnit("entry", "shape.ok", raw), modules)


class FramedLoftIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = bundle((FIXTURES / "identity-solid.ok").read_bytes())
        cls.exported = execute_framed_loft_export(cls.program,
            options=ExportOptions(fps=2, end="1", helpers=False))
        if cls.exported.data is None:
            raise AssertionError(cls.exported.report)

    def read(self, data):
        ledger = SharedExecutionBudget()
        admit_entry_budget(self.program.entry, ledger, profile=FRAMED_LOFT_PROFILE)
        return read_glb(data, target_contract=FRAMED_LOFT_TARGET,
                        work=ReachExecutionWork(execution_budget=ledger))

    def changed_triangle(self, points, normal):
        # This inherited independent byte-layout helper changes supplied bytes;
        # it never invokes the framed triangulator or its predicates.
        return inherited_reader.RingLoftIntegrationTests.changed_triangle(self, points, normal)

    def test_reader_preserves_exact_thin_face_orientation_for_011(self):
        points = ((2.**-80, 0., 0.), (1., 3., 0.), (15., 45., 0.))
        self.read(self.changed_triangle(points, (0., 0., -1.)))

    def test_reader_cannot_use_rounded_scaled_cross_to_accept_inward_normal(self):
        points = ((2.**-80, 0., 0.), (1., 3., 0.), (15., 45., 0.))
        with self.assertRaisesRegex(OntoKinError, "outward"):
            self.read(self.changed_triangle(points, (0., 0., 1.)))

    def test_reader_rejects_exactly_collinear_binary32_face(self):
        points = ((0., 0., 0.), (1., 3., 0.), (15., 45., 0.))
        with self.assertRaisesRegex(OntoKinError, "degenerate"):
            self.read(self.changed_triangle(points, (0., 0., 1.)))

    def test_reader_requires_matching_destination_and_current_admission(self):
        for kwargs in ({}, {"target_contract": FRAMED_LOFT_TARGET}):
            with self.subTest(kwargs=kwargs), self.assertRaises(OntoKinError):
                read_glb(self.exported.data, **kwargs)
        meta = self.read(self.exported.data).document["extras"]["ontokin"]
        self.assertEqual(meta["target_contract"], FRAMED_LOFT_TARGET)
        self.assertEqual(meta["framed_polygon_loft_profile"]["section_transform_rule"],
                         "exact-rational-quaternion-single-round")
        self.assertNotIn("local_station_axis", meta["framed_polygon_loft_profile"])

    def test_prebuilt_geometry_cannot_be_borrowed_from_another_carrier(self):
        raw = (FIXTURES / "cross-owner-section-escape.ok").read_bytes()
        raw = raw.replace(b"sections = shape.sections;", b"geometry = shape.geometry;")
        result = execute_framed_loft_export(bundle(raw))
        self.assertIsNone(result.data)
        self.assertIn("OKL-E-FRAMED-LOFT-FRAME", [d["code"] for d in result.report["diagnostics"]])

    def test_outer_placement_cannot_conceal_foreign_geometry_ownership(self):
        raw = (FIXTURES / "cross-owner-section-escape.ok").read_bytes()
        raw = raw.replace(b"sections = shape.sections;",
            b"geometry = placed(shape.geometry, pose(thief.frame, vec3(0[m], 0[m], 0[m]), quat(1, 0, 0, 0)));")
        result = execute_framed_loft_export(bundle(raw))
        self.assertIsNone(result.data)
        codes = [d["code"] for d in result.report["diagnostics"]]
        self.assertTrue(set(codes) & {"OKL-E-FRAMED-LOFT-FRAME", "OKL-E-SURFACE-PLACEMENT"}, result.report)

    def test_owning_frame_survives_nested_free_function_calls(self):
        raw = (FIXTURES / "function-section-and-geometry.ok").read_bytes()
        raw = raw.replace(b"return framed_polygon_section(order, frame, rings);",
                          b"return inner_section(order, frame, rings);")
        extra = b'''public fn inner_section @ "inner-section"(order: Int, frame: Pose, rings: Keyed<PolygonRing>) -> FramedPolygonSection {
    return framed_polygon_section(order, frame, rings);
}
'''
        raw = raw.replace(b"public class Shape", extra + b"public class Shape", 1)
        result = execute_framed_loft_export(bundle(raw),
            options=ExportOptions(fps=2, end="1", helpers=False))
        self.assertIsNotNone(result.data, result.report)

    def test_earlier_module_cannot_import_even_unused_011_definitions(self):
        library = (FIXTURES / "parts.ok").read_bytes()
        digest = hashlib.sha256(library).hexdigest()
        raw = (FIXTURES / "identity-solid-legacy.ok").read_bytes()
        addition = (f'import framed @ "framed" from "fixture.framed-loft-parts" version "1.0.0" '
                    f'digest "sha256:{digest}";\n').encode()
        raw = raw.replace(b"public class Shape", addition + b"public class Shape", 1)
        module = SourceUnit("package:fixture.framed-loft-parts@1.0.0", "parts.ok", library,
                            "fixture.framed-loft-parts", "1.0.0")
        result = execute_ring_loft_export(bundle(raw, modules=(module,)))
        self.assertIsNone(result.data)
        self.assertIn("OKL-E-CAPABILITY-UNSUPPORTED", [d["code"] for d in result.report["diagnostics"]])
        self.assertTrue(any(d.get("details", {}).get("dependency_profile") == FRAMED_LOFT_PROFILE
                            for d in result.report["diagnostics"]), result.report)

    def test_new_constructor_is_unavailable_under_earlier_source_binding(self):
        result = execute_ring_loft_export(bundle((FIXTURES / "earlier-version-rejection.ok").read_bytes()))
        self.assertIsNone(result.data)
        self.assertTrue(result.report.get("diagnostics"), result.report)


if __name__ == "__main__":
    unittest.main()
