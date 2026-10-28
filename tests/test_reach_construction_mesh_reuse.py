"""Compiled occurrences retain their own placement, identity and limits."""
import copy
from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch

from ontokin.bundle import load_file_manifest
from ontokin.construction import _materialize_reach_surface, compile_construction
from ontokin.reach_numeric import ReachExecutionWork
from ontokin.surface import SurfaceError
from ontokin.surface_runtime import materialize_surface
from test_reach_source_mesh_reuse import recipe


ROOT = Path(__file__).resolve().parents[1]


def build(value, work, remaining=250000):
    return _materialize_reach_surface(value, max_vertices=remaining, work=work, check=work.tick)


class ReachConstructionMeshReuseTests(unittest.TestCase):
    def test_identical_triangles_share_only_immutable_data(self):
        value, work = recipe(), ReachExecutionWork()
        first = build(value, work)
        self.assertEqual(first, materialize_surface(value, max_vertices=250000))
        with patch("ontokin.construction.materialize_surface",
                   side_effect=AssertionError("reconstructed an identical loft")):
            second = build(copy.deepcopy(value), work)
        self.assertIs(first[0], second[0])
        self.assertEqual(first[1], second[1])
        self.assertIsNot(first[1], second[1])
        self.assertLessEqual(len(work._cache), work.max_cache_entries)

    def test_changed_recipe_and_remaining_occurrence_allowance_stay_visible(self):
        value, work = recipe(), ReachExecutionWork()
        mesh, _ = build(value, work)
        with self.assertRaises(SurfaceError) as raised:
            build(value, work, len(mesh.positions) - 1)
        self.assertEqual(raised.exception.details,
                         {"required": len(mesh.positions), "available": len(mesh.positions) - 1})
        for changed in ("radius", "material", "position"):
            other = copy.deepcopy(value)
            surface = other["surface"]
            if changed == "radius":
                surface["sections"] = (replace(surface["sections"][0], radius_x_m=.2),
                                       *surface["sections"][1:])
            elif changed == "material":
                surface["materials"] = (replace(surface["materials"][0], metallic=.7),
                                        *surface["materials"][1:])
            else:
                other["local_position"] = (.5, 0., 0.)
            with self.subTest(changed=changed):
                actual = build(other, work)
                self.assertEqual(actual, materialize_surface(other, max_vertices=250000))
                self.assertNotEqual(actual, (mesh, build(value, work)[1]))
        invalid = copy.deepcopy(value)
        invalid["surface"]["sections"] = (replace(value["surface"]["sections"][0], station_m=False),
                                            *value["surface"]["sections"][1:])
        with self.assertRaises(SurfaceError):
            build(invalid, work)

    def test_reuse_and_first_publication_preserve_cancellation(self):
        work = ReachExecutionWork()
        value = recipe()
        build(value, work)
        marker = RuntimeError("cancel compiled mesh reuse")
        with patch.object(work, "external_check", side_effect=marker):
            with self.assertRaises(RuntimeError) as raised:
                build(value, work)
        self.assertIs(raised.exception, marker)
        self.assertIs(work.callback_error, marker)
        fresh = ReachExecutionWork()

        def completed(*args, **kwargs):
            result = materialize_surface(*args, **kwargs)
            fresh.external_check = lambda: (_ for _ in ()).throw(marker)
            return result

        with patch("ontokin.construction.materialize_surface", side_effect=completed):
            with self.assertRaises(RuntimeError) as raised:
                build(value, fresh)
        self.assertIs(raised.exception, marker)
        self.assertEqual(len(fresh._cache), 0)

    def test_repeated_source_assets_keep_every_occurrence_and_exact_mesh(self):
        bundle = load_file_manifest(ROOT / "docs/language-design/planar-reach-v0.1/p23.files.json")
        compiler = compile_construction(bundle, level="constructed")
        meshes = compiler.surface_meshes
        self.assertEqual(len(meshes), 64)
        self.assertEqual(len({id(item["mesh"]) for item in meshes.values()}), 1)
        self.assertEqual(len({id(item["local_pose"]) for item in meshes.values()}), 64)
        for path, record in meshes.items():
            self.assertEqual(record["object_path"], path)
            self.assertEqual(record["element_id"], compiler.model.objects[path].element_id)
            self.assertEqual((record["mesh"], record["local_pose"]),
                             materialize_surface(compiler.model.objects[path].geometry,
                                                 max_vertices=250000))
        self.assertLessEqual(compiler.reach_work.record()["cache_entries"], 256)


if __name__ == "__main__":
    unittest.main()
