"""End-to-end native .ok surface model construction and strict profile isolation."""
from pathlib import Path
import hashlib
import unittest

from ontokin.bundle import ProgramBundle, SourceUnit
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError


ROOT = Path(__file__).resolve().parents[1] / "docs/language-design/surface-v0.1"


def bundle(library=None, entry=None):
    lib = (ROOT / "01-surface-parts.ok").read_bytes() if library is None else library
    main = (ROOT / "02-studio.ok").read_text("utf-8") if entry is None else entry
    expected_hash = "sha256:87fed50bdcb9b6274ec87981cc67028463c10b1cdce301060416c69586b428ce"
    actual_hash = "sha256:" + hashlib.sha256(lib).hexdigest()
    main = main.replace(expected_hash, actual_hash)
    return ProgramBundle(SourceUnit("entry", "02-studio.ok", main.encode("utf-8")),
                         (SourceUnit("package:fixture.surface-parts@1.0.0",
                                     "01-surface-parts.ok", lib,
                                     "fixture.surface-parts", "1.0.0"),))


class NativeSurfaceConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = bundle()
        cls.compiler = compile_construction(cls.source, level="evaluated")

    def test_source_creates_two_actual_independent_surface_meshes(self):
        meshes = self.compiler.surface_meshes
        self.assertEqual(set(meshes), {"first", "second"})
        self.assertEqual(self.compiler.model.profile, "surface-0.1")
        self.assertEqual(len(self.compiler.model.objects), 2)
        self.assertEqual(self.compiler.model.program_revision, self.source.program_revision)
        for name in ("first", "second"):
            mesh = meshes[name]["mesh"]
            self.assertEqual(mesh.triangle_count, 96)
            self.assertEqual(len(mesh.positions), 288)
            self.assertEqual(len(mesh.normals), 288)
            self.assertEqual(mesh.section_keys, ("foot", "neck", "tip") if name == "first"
                             else ("foot", "middle", "tip"))
            self.assertEqual(set(region.key for region in mesh.regions), {"clay", "paint"})
        self.assertEqual(self.compiler.model.objects["first"].physical["kind"], "no_body")
        self.assertEqual(self.compiler.model.objects["second"].physical["kind"], "no_body")

    def test_parameter_override_changes_one_occurrence_only(self):
        a = self.compiler.surface_meshes["first"]["mesh"]
        b = self.compiler.surface_meshes["second"]["mesh"]
        self.assertAlmostEqual(a.positions[0][0], 0.5)
        self.assertAlmostEqual(b.positions[0][0], 0.65)
        self.assertEqual(a.positions[0][2], 0.)
        self.assertEqual(b.positions[0][2], 0.)
        self.assertEqual(a.regions[0].material.metallic, 0.)
        self.assertEqual(self.compiler.surface_meshes["first"]["source_id"],
                         "package:fixture.surface-parts@1.0.0")

    def test_rigid_visual_offset_is_separate_from_world_object_placement(self):
        first = self.compiler.surface_meshes["first"]["local_pose"]
        second = self.compiler.surface_meshes["second"]["local_pose"]
        self.assertEqual(first.position, (0., 0., .1))
        self.assertEqual(second.position, (0., 0., .1))
        self.assertEqual(first.rotation, (1., 0., 0., 0.))
        self.assertNotEqual(self.compiler.model.objects["first"].placement.position,
                            self.compiler.model.objects["second"].placement.position)

    def test_invalid_facet_count_rejects_actual_compiled_source(self):
        text = (ROOT / "01-surface-parts.ok").read_text("utf-8")
        text = text.replace('self.palette, 16, "flat"', 'self.palette, 7, "flat"')
        with self.assertRaises(OntoKinError) as e:
            compile_construction(bundle(library=text.encode("utf-8")), level="evaluated")
        self.assertEqual(e.exception.code, "OKL-E-SURFACE-FACETS")

    def test_unknown_material_region_rejects_compiled_source(self):
        text = (ROOT / "01-surface-parts.ok").read_text("utf-8")
        text = text.replace('0.5[m], 0.35[m], "clay"', '0.5[m], 0.35[m], "missing"')
        with self.assertRaises(OntoKinError) as e:
            compile_construction(bundle(library=text.encode("utf-8")), level="evaluated")
        self.assertEqual(e.exception.code, "OKL-E-SURFACE-REGION")


if __name__ == "__main__":
    unittest.main()
