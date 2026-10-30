"""Explicit profile selection and exact supplied binary32 face orientation."""
import copy
from pathlib import Path
import struct
import unittest

from ontokin.budget_runtime import execute_holes_export, execute_ring_loft_export
from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.diagnostics import OntoKinError
from ontokin.execution_budget import SharedExecutionBudget, admit_entry_budget
from ontokin.gltf import read_glb
from ontokin.profile_capabilities import RING_LOFT_PROFILE
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.scene import ExportOptions, RING_LOFT_TARGET
from tests.test_export import DecodedGLB, encode_glb


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples/polygon-lofts"


def bundle(raw, filename="shape.ok"):
    return ProgramBundle(SourceUnit("entry", filename, raw), ())


class RingLoftIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = bundle((FIXTURES / "constant-solid.ok").read_bytes())
        cls.exported = execute_ring_loft_export(cls.program,
            options=ExportOptions(fps=2, end="1", helpers=False))
        if cls.exported.data is None:
            raise AssertionError(cls.exported.report)

    def read(self, data, **kwargs):
        ledger = SharedExecutionBudget()
        admit_entry_budget(self.program.entry, ledger, profile=RING_LOFT_PROFILE)
        return read_glb(data, target_contract=RING_LOFT_TARGET,
                        work=ReachExecutionWork(execution_budget=ledger), **kwargs)

    def changed_triangle(self, points, normal):
        """Mutate real exported attributes with independent byte-layout code.

        The format reader checks individual supplied triangles. Complete source
        equivalence/manifold checks belong to validate_export, not this helper.
        """
        decoded = DecodedGLB(self.exported.data)
        document = copy.deepcopy(decoded.document)
        binary = bytearray(decoded.binary)
        primitive = document["meshes"][0]["primitives"][0]
        indices = [row[0] for row in decoded.accessor(primitive["indices"])[:3]]
        for name, rows in (("POSITION", points), ("NORMAL", (normal,) * 3)):
            number = primitive["attributes"][name]
            accessor = document["accessors"][number]
            view = document["bufferViews"][accessor["bufferView"]]
            start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
            stride = view.get("byteStride", 12)
            for index, point in zip(indices, rows):
                struct.pack_into("<3f", binary, start + index * stride, *point)
            if name == "POSITION":
                values = [struct.unpack_from("<3f", binary, start + i * stride)
                          for i in range(accessor["count"])]
                accessor["min"] = [min(v[i] for v in values) for i in range(3)]
                accessor["max"] = [max(v[i] for v in values) for i in range(3)]
        return encode_glb(document, binary)

    def test_thin_binary32_face_with_exact_outward_normal_is_readable(self):
        # Exact Z cross is -42 * 2**-80; the previous scaled float cross
        # has the opposite sign. All three supplied vertices are binary32.
        points = ((2.**-80, 0., 0.), (1., 3., 0.), (15., 45., 0.))
        self.read(self.changed_triangle(points, (0., 0., -1.)))

    def test_scaled_float_sign_cannot_authorize_an_inward_normal(self):
        points = ((2.**-80, 0., 0.), (1., 3., 0.), (15., 45., 0.))
        with self.assertRaisesRegex(OntoKinError, "outward"):
            self.read(self.changed_triangle(points, (0., 0., 1.)))

    def test_exactly_collinear_supplied_face_is_rejected(self):
        points = ((0., 0., 0.), (1., 3., 0.), (15., 45., 0.))
        with self.assertRaisesRegex(OntoKinError, "degenerate"):
            self.read(self.changed_triangle(points, (0., 0., 1.)))

    def test_binary32_orientation_reversal_is_checked_after_conversion(self):
        u = 2.**-23
        points = ((1 + .49*u, 1 + .49*u, 0.),
                  (1 + 1.49*u, 1 + 1.51*u, 0.),
                  (1 + 1.51*u, 1 + 2.49*u, 0.))
        with self.assertRaisesRegex(OntoKinError, "outward"):
            self.read(self.changed_triangle(points, (0., 0., 1.)))

    def test_explicit_destination_and_admitted_work_are_required(self):
        with self.assertRaises(OntoKinError):
            read_glb(self.exported.data)
        with self.assertRaises(OntoKinError):
            read_glb(self.exported.data, target_contract=RING_LOFT_TARGET)
        decoded = self.read(self.exported.data)
        meta = decoded.document["extras"]["ontokin"]
        self.assertEqual(meta["target_contract"], RING_LOFT_TARGET)
        self.assertEqual(meta["polygon_loft_profile"]["surface_rule"], "fixed-diagonal-triangles")

    def test_station_type_and_dimension_have_their_frozen_distinct_diagnostics(self):
        for name, code in (("wrong-station-type", "OKL-E-TYPE"), ("wrong-station-unit", "OKL-E-UNIT")):
            with self.subTest(case=name):
                result = execute_ring_loft_export(bundle((FIXTURES / (name + ".ok")).read_bytes()))
                self.assertIsNone(result.data)
                self.assertIn(code, [d["code"] for d in result.report.get("diagnostics", [])])

    def test_earlier_source_rejects_the_new_constructor_under_its_own_binding(self):
        result = execute_holes_export(bundle((FIXTURES / "earlier-version-rejection.ok").read_bytes()))
        self.assertIsNone(result.data)
        self.assertTrue(result.report.get("diagnostics"), result.report)

    def test_inherited_polygon_families_keep_their_original_summaries(self):
        for folder, name, version, profile, family in (
            ("polygon-extrusions", "rectangle.ok", "0.8", "polygon-extrusion-0.1", "polygon_extrusion"),
            ("polygon-holes", "square-hole.ok", "0.9", "polygon-holes-0.1", "polygon_holes"),
        ):
            with self.subTest(family=family):
                raw = (ROOT / "examples" / folder / name).read_bytes()
                raw = raw.replace(('ontokin "' + version + '"').encode(), b'ontokin "0.10"', 1)
                raw = raw.replace(profile.encode(), RING_LOFT_PROFILE.encode(), 1)
                result = execute_ring_loft_export(bundle(raw), options=ExportOptions(fps=2, end="1", helpers=False))
                self.assertIsNotNone(result.data, result.report)
                decoded = DecodedGLB(result.data)
                surface = decoded.document["nodes"][0]["extras"]["ontokin"]["surface"]
                self.assertEqual(surface["family"], family)
                self.assertEqual(surface["profile"], profile)


if __name__ == "__main__":
    unittest.main()
